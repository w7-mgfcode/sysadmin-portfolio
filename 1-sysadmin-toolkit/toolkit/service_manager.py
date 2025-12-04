"""
Service Manager - Szolgáltatás kezelő.

Tools for querying and monitoring systemd services.

Eszközök systemd szolgáltatások lekérdezéséhez és monitorozásához.
"""

import subprocess
from typing import Optional

from .models import ServiceState, ServiceStatus


def _run_systemctl(args: list[str]) -> tuple[str, int]:
    """
    Systemctl parancs futtatása.

    Args:
        args: Parancs argumentumok.

    Returns:
        Tuple (stdout, return_code).
    """
    try:
        result = subprocess.run(
            ["systemctl"] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout, result.returncode
    except FileNotFoundError:
        return "", -1
    except subprocess.TimeoutExpired:
        return "", -2


def get_service_status(service_name: str) -> ServiceStatus:
    """
    Szolgáltatás státusz lekérdezése.

    Args:
        service_name: A szolgáltatás neve (pl. "nginx", "sshd").

    Returns:
        ServiceStatus objektum a szolgáltatás információival.

    Example:
        >>> status = get_service_status("nginx")
        >>> print(f"State: {status.state}")
        >>> print(f"Active: {status.is_active}")
    """
    # Alapértelmezett értékek
    state = ServiceState.UNKNOWN
    is_enabled = False
    is_active = False
    pid = None
    memory_bytes = None
    description = None
    load_state = None
    sub_state = None

    # is-enabled ellenőrzés
    stdout, rc = _run_systemctl(["is-enabled", service_name])
    if rc == 0:
        is_enabled = True

    # is-active ellenőrzés
    stdout, rc = _run_systemctl(["is-active", service_name])
    active_status = stdout.strip().lower()
    is_active = active_status == "active"

    # Állapot meghatározása
    if active_status == "active":
        state = ServiceState.RUNNING
    elif active_status == "inactive":
        state = ServiceState.INACTIVE
    elif active_status == "failed":
        state = ServiceState.FAILED
    else:
        state = ServiceState.STOPPED

    # Részletes információ lekérdezése
    stdout, rc = _run_systemctl([
        "show", service_name,
        "--property=MainPID,MemoryCurrent,Description,LoadState,SubState"
    ])

    if rc == 0:
        for line in stdout.strip().split("\n"):
            if "=" not in line:
                continue
            key, value = line.split("=", 1)

            if key == "MainPID" and value.isdigit():
                pid_val = int(value)
                if pid_val > 0:
                    pid = pid_val
            elif key == "MemoryCurrent" and value.isdigit():
                mem_val = int(value)
                # Reason: [not set] értéknél 18446744073709551615 jön vissza
                if mem_val < 2**62:
                    memory_bytes = mem_val
            elif key == "Description":
                description = value
            elif key == "LoadState":
                load_state = value
            elif key == "SubState":
                sub_state = value

    return ServiceStatus(
        name=service_name,
        state=state,
        is_enabled=is_enabled,
        is_active=is_active,
        pid=pid,
        memory_bytes=memory_bytes,
        description=description,
        load_state=load_state,
        sub_state=sub_state,
    )


def list_services(
    filter_state: Optional[ServiceState] = None,
    filter_enabled: Optional[bool] = None,
) -> list[ServiceStatus]:
    """
    Szolgáltatások listázása.

    Args:
        filter_state: Szűrés állapot alapján.
        filter_enabled: Szűrés enabled állapot alapján.

    Returns:
        ServiceStatus objektumok listája.
    """
    services = []

    # Összes service unit lekérdezése
    stdout, rc = _run_systemctl([
        "list-units", "--type=service", "--all", "--no-legend", "--plain"
    ])

    if rc != 0:
        return services

    for line in stdout.strip().split("\n"):
        if not line:
            continue

        parts = line.split()
        if len(parts) < 4:
            continue

        unit_name = parts[0]
        # Eltávolítjuk a .service kiterjesztést
        if unit_name.endswith(".service"):
            service_name = unit_name[:-8]
        else:
            service_name = unit_name

        # Részletes státusz lekérdezése
        status = get_service_status(service_name)

        # Szűrés alkalmazása
        if filter_state is not None and status.state != filter_state:
            continue
        if filter_enabled is not None and status.is_enabled != filter_enabled:
            continue

        services.append(status)

    return services


def check_critical_services(
    service_names: Optional[list[str]] = None,
) -> dict[str, ServiceStatus]:
    """
    Kritikus szolgáltatások állapotának ellenőrzése.

    Args:
        service_names: Ellenőrizendő szolgáltatások listája.
                      Ha None, alapértelmezett kritikus szolgáltatások.

    Returns:
        Dict ahol a kulcs a szolgáltatás neve, az érték a ServiceStatus.

    Example:
        >>> results = check_critical_services(["sshd", "nginx"])
        >>> for name, status in results.items():
        ...     if not status.is_active:
        ...         print(f"WARNING: {name} is not running!")
    """
    if service_names is None:
        # Alapértelmezett kritikus szolgáltatások Linux-on
        service_names = [
            "sshd",
            "systemd-journald",
            "systemd-networkd",
            "systemd-resolved",
            "cron",
            "rsyslog",
        ]

    results = {}
    for name in service_names:
        results[name] = get_service_status(name)

    return results


def get_failed_services() -> list[ServiceStatus]:
    """
    Hibás állapotú szolgáltatások lekérdezése.

    Returns:
        Hibás szolgáltatások listája.
    """
    return list_services(filter_state=ServiceState.FAILED)


def get_service_logs(
    service_name: str,
    lines: int = 50,
    since: Optional[str] = None,
) -> str:
    """
    Szolgáltatás naplóinak lekérdezése journalctl-lel.

    Args:
        service_name: A szolgáltatás neve.
        lines: Visszaadandó sorok száma.
        since: Kezdő időpont (pl. "1 hour ago", "today").

    Returns:
        A napló tartalma string-ként.
    """
    args = ["-u", service_name, "-n", str(lines), "--no-pager"]

    if since:
        args.extend(["--since", since])

    try:
        result = subprocess.run(
            ["journalctl"] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
