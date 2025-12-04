"""
System Health Checker - Rendszer egészség ellenőrző.

Tools for monitoring system health including CPU, memory, disk, and processes.

Eszközök a rendszer egészségének monitorozásához, beleértve a CPU-t,
memóriát, lemezt és folyamatokat.
"""

import socket
from datetime import datetime
from typing import Optional

import psutil

from .models import DiskUsage, ProcessInfo, SystemHealth


def get_cpu_info() -> dict:
    """
    CPU információk lekérdezése.

    Returns:
        CPU információkat tartalmazó dict.
    """
    cpu_freq = psutil.cpu_freq()
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_count": psutil.cpu_count(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_freq_mhz": cpu_freq.current if cpu_freq else None,
        "cpu_freq_min": cpu_freq.min if cpu_freq else None,
        "cpu_freq_max": cpu_freq.max if cpu_freq else None,
    }


def get_memory_info() -> dict:
    """
    Memória információk lekérdezése.

    Returns:
        Memória információkat tartalmazó dict.
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "memory_total_bytes": mem.total,
        "memory_used_bytes": mem.used,
        "memory_available_bytes": mem.available,
        "memory_percent": mem.percent,
        "memory_cached_bytes": getattr(mem, "cached", 0),
        "memory_buffers_bytes": getattr(mem, "buffers", 0),
        "swap_total_bytes": swap.total,
        "swap_used_bytes": swap.used,
        "swap_free_bytes": swap.free,
        "swap_percent": swap.percent,
    }


def get_disk_info(exclude_types: Optional[list[str]] = None) -> list[DiskUsage]:
    """
    Lemez partíciók információinak lekérdezése.

    Args:
        exclude_types: Kizárandó fájlrendszer típusok listája.
                      List of filesystem types to exclude.

    Returns:
        DiskUsage objektumok listája.
    """
    if exclude_types is None:
        exclude_types = ["tmpfs", "devtmpfs", "squashfs", "overlay"]

    disks = []
    for partition in psutil.disk_partitions(all=False):
        if partition.fstype in exclude_types:
            continue

        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append(
                DiskUsage(
                    device=partition.device,
                    mountpoint=partition.mountpoint,
                    fstype=partition.fstype,
                    total_bytes=usage.total,
                    used_bytes=usage.used,
                    free_bytes=usage.free,
                    percent_used=usage.percent,
                )
            )
        except (PermissionError, OSError):
            # Reason: Néhány mountpoint nem elérhető (pl. snap)
            continue

    return disks


def get_top_processes(
    count: int = 10, sort_by: str = "cpu"
) -> list[ProcessInfo]:
    """
    Top folyamatok lekérdezése erőforrás használat alapján.

    Args:
        count: Visszaadandó folyamatok száma.
        sort_by: Rendezési szempont ("cpu" vagy "memory").

    Returns:
        ProcessInfo objektumok listája.
    """
    processes = []

    for proc in psutil.process_iter(
        ["pid", "name", "username", "status", "cpu_percent", "memory_percent",
         "memory_info", "create_time", "cmdline"]
    ):
        try:
            pinfo = proc.info
            if pinfo.get("pid") is None:
                continue

            # cmdline összeállítása
            cmdline = pinfo.get("cmdline")
            cmdline_str = " ".join(cmdline) if cmdline else None

            # memory_info kezelése
            mem_info = pinfo.get("memory_info")
            rss = mem_info.rss if mem_info else 0

            # create_time konvertálása
            create_time = pinfo.get("create_time", 0)
            create_dt = datetime.fromtimestamp(create_time) if create_time else datetime.now()

            processes.append(
                ProcessInfo(
                    pid=pinfo["pid"],
                    name=pinfo.get("name", "unknown"),
                    username=pinfo.get("username", "unknown"),
                    status=pinfo.get("status", "unknown"),
                    cpu_percent=pinfo.get("cpu_percent", 0.0) or 0.0,
                    memory_percent=pinfo.get("memory_percent", 0.0) or 0.0,
                    memory_rss_bytes=rss,
                    create_time=create_dt,
                    cmdline=cmdline_str,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Rendezés
    if sort_by == "memory":
        processes.sort(key=lambda p: p.memory_percent, reverse=True)
    else:
        processes.sort(key=lambda p: p.cpu_percent, reverse=True)

    return processes[:count]


def get_system_health() -> SystemHealth:
    """
    Teljes rendszer egészségi állapot lekérdezése.

    Returns:
        SystemHealth objektum minden releváns információval.

    Example:
        >>> health = get_system_health()
        >>> print(f"CPU: {health.cpu_percent}%")
        >>> print(f"Memory: {health.memory_percent}%")
    """
    # Boot idő és uptime
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = (datetime.now() - boot_time).total_seconds()

    # Load average
    try:
        load_avg = psutil.getloadavg()
    except (AttributeError, OSError):
        # Reason: Windows-on nincs load average
        load_avg = (0.0, 0.0, 0.0)

    # CPU info
    cpu_info = get_cpu_info()

    # Memory info
    mem_info = get_memory_info()

    # Disk info
    disk_info = get_disk_info()

    # Bejelentkezett felhasználók
    try:
        users = len(psutil.users())
    except (AttributeError, RuntimeError):
        users = 0

    # Futó folyamatok száma
    process_count = len(psutil.pids())

    return SystemHealth(
        hostname=socket.gethostname(),
        uptime_seconds=uptime,
        boot_time=boot_time,
        cpu_percent=cpu_info["cpu_percent"],
        cpu_count=cpu_info["cpu_count"],
        cpu_freq_mhz=cpu_info.get("cpu_freq_mhz"),
        load_avg_1m=load_avg[0],
        load_avg_5m=load_avg[1],
        load_avg_15m=load_avg[2],
        memory_total_bytes=mem_info["memory_total_bytes"],
        memory_used_bytes=mem_info["memory_used_bytes"],
        memory_available_bytes=mem_info["memory_available_bytes"],
        memory_percent=mem_info["memory_percent"],
        swap_total_bytes=mem_info["swap_total_bytes"],
        swap_used_bytes=mem_info["swap_used_bytes"],
        swap_percent=mem_info["swap_percent"],
        disk_partitions=disk_info,
        process_count=process_count,
        users_logged_in=users,
    )
