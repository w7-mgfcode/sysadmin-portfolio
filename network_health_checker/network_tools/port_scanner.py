"""
Port Scanner - TCP port szkennelés.

Ez a modul tartalmazza a TCP port szkennelési funkciókat,
egyedi portok és port tartományok ellenőrzéséhez.

Használat:
    >>> from network_tools.port_scanner import scan_port, scan_ports
    >>> result = scan_port("example.com", 80)
    >>> print(f"Port 80 is {'open' if result.is_open else 'closed'}")
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from ..config import get_service_name, get_settings
from ..models import PortScanResult


def scan_port(
    host: str,
    port: int,
    timeout: float | None = None,
    grab_banner: bool = False,
) -> PortScanResult:
    """
    Egyetlen TCP port szkennelése.

    Megpróbál TCP kapcsolatot létesíteni a megadott host:port-ra.
    Opcionálisan megpróbálja lekérni a banner információt.

    Args:
        host: Cél hostname vagy IP cím
        port: Szkennelendő port száma
        timeout: Kapcsolódási időtúllépés másodpercben
        grab_banner: Ha True, megpróbálja lekérni a banner-t

    Returns:
        PortScanResult az eredményekkel

    Example:
        >>> result = scan_port("google.com", 443)
        >>> if result.is_open:
        ...     print(f"HTTPS port open, latency: {result.latency_ms}ms")
    """
    # Konfiguráció betöltése
    settings = get_settings()
    if timeout is None:
        timeout = settings.port_scan_timeout

    # Szolgáltatás neve a porthoz
    service_name = get_service_name(port)

    # Socket létrehozása és időtúllépés beállítása
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    banner: str | None = None
    latency_ms: float | None = None

    try:
        # Kapcsolódási idő mérése
        start_time = time.perf_counter()

        # Kapcsolódás a porthoz
        result = sock.connect_ex((host, port))
        end_time = time.perf_counter()

        latency_ms = round((end_time - start_time) * 1000, 2)

        if result == 0:
            # Port nyitva
            if grab_banner:
                banner = _grab_banner(sock, timeout)

            return PortScanResult(
                host=host,
                port=port,
                is_open=True,
                service_name=service_name,
                banner=banner,
                latency_ms=latency_ms,
            )
        else:
            # Port zárva vagy szűrve
            return PortScanResult(
                host=host,
                port=port,
                is_open=False,
                service_name=service_name,
            )

    except socket.timeout:
        # Időtúllépés - port szűrve vagy host nem elérhető
        return PortScanResult(
            host=host,
            port=port,
            is_open=False,
            service_name=service_name,
        )

    except socket.gaierror:
        # Hostname feloldási hiba
        return PortScanResult(
            host=host,
            port=port,
            is_open=False,
            service_name=service_name,
        )

    except Exception:
        # Egyéb hiba
        return PortScanResult(
            host=host,
            port=port,
            is_open=False,
            service_name=service_name,
        )

    finally:
        sock.close()


def _grab_banner(sock: socket.socket, timeout: float) -> str | None:
    """
    Banner információ lekérése nyitott portról.

    Args:
        sock: Nyitott socket kapcsolat
        timeout: Olvasási időtúllépés

    Returns:
        Banner szöveg vagy None
    """
    try:
        sock.settimeout(timeout)
        # Néhány szolgáltatásnak küldeni kell valamit
        sock.send(b"\r\n")
        banner = sock.recv(1024)
        return banner.decode("utf-8", errors="ignore").strip()
    except Exception:
        return None


def scan_ports(
    host: str,
    ports: List[int] | str,
    timeout: float | None = None,
    max_workers: int = 50,
    grab_banner: bool = False,
) -> List[PortScanResult]:
    """
    Több port párhuzamos szkennelése.

    ThreadPoolExecutor-t használ a gyors párhuzamos végrehajtáshoz.

    Args:
        host: Cél hostname vagy IP cím
        ports: Port lista vagy port range string (pl. "20-25,80,443")
        timeout: Időtúllépés portonként
        max_workers: Párhuzamos szálak száma
        grab_banner: Banner lekérés megkísérlése

    Returns:
        PortScanResult lista minden porthoz

    Example:
        >>> results = scan_ports("example.com", "22,80,443,8080")
        >>> open_ports = [r for r in results if r.is_open]
        >>> print(f"Found {len(open_ports)} open ports")
    """
    # Port lista feldolgozása
    port_list = _parse_ports(ports) if isinstance(ports, str) else ports

    results: List[PortScanResult] = []

    # ThreadPoolExecutor használata (socket műveletek thread-safe-ek)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Feladatok indítása
        future_to_port = {
            executor.submit(scan_port, host, port, timeout, grab_banner): port
            for port in port_list
        }

        # Eredmények gyűjtése
        for future in as_completed(future_to_port):
            try:
                result = future.result()
                results.append(result)
            except Exception:
                port = future_to_port[future]
                results.append(
                    PortScanResult(
                        host=host,
                        port=port,
                        is_open=False,
                    )
                )

    # Rendezés port szám szerint
    results.sort(key=lambda x: x.port)
    return results


def _parse_ports(ports_str: str) -> List[int]:
    """
    Port string feldolgozása listává.

    Támogatott formátumok:
    - Egyedi portok: "22,80,443"
    - Tartományok: "20-25"
    - Vegyes: "22,80-90,443"

    Args:
        ports_str: Port definíció string

    Returns:
        Port számok listája
    """
    port_list: List[int] = []

    for part in ports_str.split(","):
        part = part.strip()
        if "-" in part:
            # Port tartomány
            start, end = part.split("-", 1)
            port_list.extend(range(int(start), int(end) + 1))
        else:
            # Egyedi port
            port_list.append(int(part))

    return sorted(set(port_list))


def scan_common_ports(host: str, timeout: float | None = None) -> List[PortScanResult]:
    """
    Gyakori portok szkennelése.

    A leggyakrabban használt szolgáltatás portokat ellenőrzi.

    Args:
        host: Cél hostname vagy IP cím
        timeout: Időtúllépés portonként

    Returns:
        PortScanResult lista a gyakori portokhoz
    """
    common_ports = [
        21,  # FTP
        22,  # SSH
        23,  # Telnet
        25,  # SMTP
        53,  # DNS
        80,  # HTTP
        110,  # POP3
        143,  # IMAP
        443,  # HTTPS
        445,  # SMB
        993,  # IMAPS
        995,  # POP3S
        1433,  # MSSQL
        3306,  # MySQL
        3389,  # RDP
        5432,  # PostgreSQL
        8080,  # HTTP Proxy
    ]
    return scan_ports(host, common_ports, timeout)
