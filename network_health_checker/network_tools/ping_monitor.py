"""
Ping Monitor - ICMP ping implementáció.

Ez a modul tartalmazza az ICMP ping funkciókat egyedi és
tömeges host ellenőrzéshez.

Használat:
    >>> from network_tools.ping_monitor import ping_host
    >>> result = ping_host("8.8.8.8")
    >>> print(f"Status: {result.status}, Latency: {result.latency_ms}ms")
"""

import socket
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import List

from ping3 import ping

from ..config import get_settings
from ..models import HostStatus, PingResult


def ping_host(
    host: str,
    timeout: float | None = None,
    count: int = 1,
    privileged: bool = False,
) -> PingResult:
    """
    Egyetlen host pingelése és strukturált eredmény visszaadása.

    ICMP echo request küldése a megadott host-nak és a válaszidő mérése.
    Támogatja a hostname feloldást és a többszöri ping átlagolását.

    Args:
        host: Cél hostname vagy IP cím
        timeout: Időtúllépés másodpercben (None = config default)
        count: Küldendő ping-ek száma (átlagoláshoz)
        privileged: Raw socket használata (admin jog szükséges)

    Returns:
        PingResult státusszal, latency-vel és metaadatokkal

    Example:
        >>> result = ping_host("google.com", timeout=2.0, count=3)
        >>> if result.status == HostStatus.UP:
        ...     print(f"Latency: {result.latency_ms:.2f}ms")
    """
    # Konfiguráció betöltése
    settings = get_settings()
    if timeout is None:
        timeout = settings.ping_timeout

    # Hostname feloldása IP címre
    try:
        ip_address = socket.gethostbyname(host)
    except socket.gaierror as e:
        return PingResult(
            host=host,
            status=HostStatus.ERROR,
            error_message=f"Could not resolve hostname: {host} - {e}",
            timestamp=datetime.now(),
        )

    # Ping műveletek végrehajtása
    latencies: List[float] = []
    last_error: str | None = None

    for _ in range(count):
        try:
            # FONTOS: ping3 None-t ad timeout esetén, False-t hiba esetén
            result = ping(ip_address, timeout=timeout, unit="ms")

            if result is not None and result is not False:
                latencies.append(float(result))
        except PermissionError:
            # Admin jog szükséges raw socket-hez
            return PingResult(
                host=host,
                ip_address=ip_address,
                status=HostStatus.ERROR,
                error_message="Permission denied. Try running with admin privileges.",
                timestamp=datetime.now(),
            )
        except Exception as e:
            last_error = str(e)

    # Eredmény összeállítása
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        return PingResult(
            host=host,
            ip_address=ip_address,
            status=HostStatus.UP,
            latency_ms=round(avg_latency, 2),
            timestamp=datetime.now(),
        )
    elif last_error:
        return PingResult(
            host=host,
            ip_address=ip_address,
            status=HostStatus.ERROR,
            error_message=last_error,
            timestamp=datetime.now(),
        )
    else:
        return PingResult(
            host=host,
            ip_address=ip_address,
            status=HostStatus.TIMEOUT,
            timestamp=datetime.now(),
        )


def ping_hosts(
    hosts: List[str],
    timeout: float | None = None,
    count: int = 1,
    max_workers: int = 10,
) -> List[PingResult]:
    """
    Több host párhuzamos pingelése.

    ProcessPoolExecutor-t használ a párhuzamos végrehajtáshoz,
    mivel a ping3 library nem thread-safe.

    Args:
        hosts: Pingelendő hostok listája
        timeout: Időtúllépés host-onként
        count: Ping-ek száma host-onként
        max_workers: Párhuzamos worker folyamatok száma

    Returns:
        PingResult lista minden host-hoz

    Example:
        >>> hosts = ["8.8.8.8", "1.1.1.1", "google.com"]
        >>> results = ping_hosts(hosts, timeout=2.0)
        >>> for r in results:
        ...     print(f"{r.host}: {r.status}")

    Note:
        KRITIKUS: A ping3 NEM thread-safe, ezért ProcessPoolExecutor-t
        használunk ThreadPoolExecutor helyett!
    """
    results: List[PingResult] = []

    # ProcessPoolExecutor használata threading helyett
    # Reason: A ping3 library belső állapota nem thread-safe
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Feladatok indítása
        future_to_host = {
            executor.submit(ping_host, host, timeout, count): host for host in hosts
        }

        # Eredmények gyűjtése ahogy elkészülnek
        for future in as_completed(future_to_host):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Ha valami nagyon elromlik, hibás eredményt adunk vissza
                host = future_to_host[future]
                results.append(
                    PingResult(
                        host=host,
                        status=HostStatus.ERROR,
                        error_message=f"Unexpected error: {e}",
                        timestamp=datetime.now(),
                    )
                )

    return results


def is_host_reachable(host: str, timeout: float = 2.0) -> bool:
    """
    Gyors ellenőrzés, hogy egy host elérhető-e.

    Egyszerűsített függvény ami csak bool-t ad vissza.

    Args:
        host: Ellenőrizendő host
        timeout: Időtúllépés másodpercben

    Returns:
        True ha a host válaszol, False egyébként
    """
    result = ping_host(host, timeout=timeout, count=1)
    return result.status == HostStatus.UP
