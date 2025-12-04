"""
Network Info - Helyi hálózati információk.

Ez a modul tartalmazza a helyi rendszer hálózati információinak
lekérdezési funkcióit (interfészek, kapcsolatok, routing).

Használat:
    >>> from network_tools.network_info import get_local_interfaces
    >>> interfaces = get_local_interfaces()
    >>> for iface in interfaces:
    ...     print(f"{iface.name}: {iface.ipv4_address}")
"""

import socket
from typing import List, Optional

import psutil

from ..models import ConnectionInfo, NetworkInterface


def get_local_interfaces(include_loopback: bool = False) -> List[NetworkInterface]:
    """
    Helyi hálózati interfészek információinak lekérdezése.

    Visszaadja az összes aktív hálózati interfész adatait,
    beleértve az IP címeket és MAC címet.

    Args:
        include_loopback: Ha True, a loopback interfészt is visszaadja

    Returns:
        NetworkInterface objektumok listája

    Example:
        >>> interfaces = get_local_interfaces()
        >>> for iface in interfaces:
        ...     print(f"{iface.name}: {iface.ipv4_address}/{iface.ipv4_netmask}")
    """
    interfaces: List[NetworkInterface] = []

    # Interfész címek lekérése
    if_addrs = psutil.net_if_addrs()
    # Interfész statisztikák lekérése
    if_stats = psutil.net_if_stats()

    for name, addrs in if_addrs.items():
        # Loopback kihagyása ha nem kell
        if not include_loopback and name.lower() in ("lo", "loopback", "lo0"):
            continue

        # Adatok inicializálása
        ipv4_address: Optional[str] = None
        ipv4_netmask: Optional[str] = None
        ipv6_address: Optional[str] = None
        mac_address: Optional[str] = None

        for addr in addrs:
            if addr.family == socket.AF_INET:
                # IPv4 cím
                ipv4_address = addr.address
                ipv4_netmask = addr.netmask
            elif addr.family == socket.AF_INET6:
                # IPv6 cím (első nem link-local)
                if not addr.address.startswith("fe80:"):
                    ipv6_address = addr.address
            elif addr.family == psutil.AF_LINK:
                # MAC cím
                mac_address = addr.address

        # Interfész állapot
        is_up = False
        speed: Optional[int] = None
        mtu: Optional[int] = None

        if name in if_stats:
            stats = if_stats[name]
            is_up = stats.isup
            speed = stats.speed if stats.speed > 0 else None
            mtu = stats.mtu

        interfaces.append(
            NetworkInterface(
                name=name,
                ipv4_address=ipv4_address,
                ipv4_netmask=ipv4_netmask,
                ipv6_address=ipv6_address,
                mac_address=mac_address,
                is_up=is_up,
                speed_mbps=speed,
                mtu=mtu,
            )
        )

    return interfaces


def get_interface_by_name(name: str) -> Optional[NetworkInterface]:
    """
    Specifikus interfész információinak lekérdezése név alapján.

    Args:
        name: Interfész neve (pl. "eth0", "enp0s3")

    Returns:
        NetworkInterface vagy None ha nem létezik

    Example:
        >>> eth0 = get_interface_by_name("eth0")
        >>> if eth0:
        ...     print(f"IP: {eth0.ipv4_address}")
    """
    interfaces = get_local_interfaces(include_loopback=True)
    for iface in interfaces:
        if iface.name == name:
            return iface
    return None


def get_default_gateway() -> Optional[str]:
    """
    Alapértelmezett gateway IP címének lekérdezése.

    Returns:
        Gateway IP címe vagy None ha nem található

    Example:
        >>> gw = get_default_gateway()
        >>> print(f"Default gateway: {gw}")
    """
    # psutil nem ad direkt gateway infót, gateways() használata
    try:
        gateways = psutil.net_if_addrs()
        # Alternatív: netifaces library vagy socket route info
        # Itt egyszerűsített megoldás: próbáljuk kitalálni az első
        # nem-loopback interfész hálózatából

        for name, addrs in gateways.items():
            if name.lower() in ("lo", "loopback", "lo0"):
                continue
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address:
                    # Tipikus gateway: x.x.x.1 vagy x.x.x.254
                    parts = addr.address.split(".")
                    if len(parts) == 4:
                        # Próbáljuk meg a .1-es címet
                        gateway = f"{parts[0]}.{parts[1]}.{parts[2]}.1"
                        return gateway
    except Exception:
        pass

    return None


def get_active_connections(
    kind: str = "inet",
    include_listening: bool = True,
) -> List[ConnectionInfo]:
    """
    Aktív hálózati kapcsolatok lekérdezése.

    Visszaadja a rendszer aktív TCP/UDP kapcsolatait.

    Args:
        kind: Kapcsolat típus ("inet", "inet4", "inet6", "tcp", "udp", "all")
        include_listening: Ha True, a LISTEN állapotú kapcsolatokat is

    Returns:
        ConnectionInfo objektumok listája

    Example:
        >>> connections = get_active_connections("tcp")
        >>> for conn in connections:
        ...     print(f"{conn.local_address}:{conn.local_port} -> "
        ...           f"{conn.remote_address}:{conn.remote_port} [{conn.status}]")
    """
    connections: List[ConnectionInfo] = []

    try:
        net_connections = psutil.net_connections(kind=kind)

        for conn in net_connections:
            # LISTEN kapcsolatok szűrése ha kell
            if not include_listening and conn.status == "LISTEN":
                continue

            # Helyi cím és port
            local_address: Optional[str] = None
            local_port: Optional[int] = None
            if conn.laddr:
                local_address = conn.laddr.ip
                local_port = conn.laddr.port

            # Távoli cím és port
            remote_address: Optional[str] = None
            remote_port: Optional[int] = None
            if conn.raddr:
                remote_address = conn.raddr.ip
                remote_port = conn.raddr.port

            # Protokoll típus meghatározása
            if conn.type == socket.SOCK_STREAM:
                protocol = "tcp"
            elif conn.type == socket.SOCK_DGRAM:
                protocol = "udp"
            else:
                protocol = "unknown"

            # Process információ (ha elérhető)
            pid = conn.pid
            process_name: Optional[str] = None
            if pid:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            connections.append(
                ConnectionInfo(
                    protocol=protocol,
                    local_address=local_address,
                    local_port=local_port,
                    remote_address=remote_address,
                    remote_port=remote_port,
                    status=conn.status,
                    pid=pid,
                    process_name=process_name,
                )
            )

    except psutil.AccessDenied:
        # Néhány kapcsolathoz admin jog kell
        pass
    except Exception:
        pass

    return connections


def get_listening_ports() -> List[ConnectionInfo]:
    """
    Nyitott (LISTEN) portok lekérdezése.

    Visszaadja az összes portot, amin a rendszer kapcsolatra vár.

    Returns:
        ConnectionInfo objektumok listája

    Example:
        >>> listening = get_listening_ports()
        >>> for conn in listening:
        ...     print(f"Port {conn.local_port}: {conn.process_name or 'unknown'}")
    """
    all_connections = get_active_connections("all", include_listening=True)
    return [c for c in all_connections if c.status == "LISTEN"]


def get_interface_io_counters(interface: str | None = None) -> dict:
    """
    Hálózati I/O számlálók lekérdezése.

    Visszaadja az elküldött/fogadott byte-ok és csomagok számát.

    Args:
        interface: Specifikus interfész neve (None = összesített)

    Returns:
        Dictionary a számlálókkal

    Example:
        >>> counters = get_interface_io_counters("eth0")
        >>> print(f"Received: {counters['bytes_recv']} bytes")
    """
    try:
        if interface:
            counters = psutil.net_io_counters(pernic=True)
            if interface in counters:
                c = counters[interface]
                return {
                    "bytes_sent": c.bytes_sent,
                    "bytes_recv": c.bytes_recv,
                    "packets_sent": c.packets_sent,
                    "packets_recv": c.packets_recv,
                    "errin": c.errin,
                    "errout": c.errout,
                    "dropin": c.dropin,
                    "dropout": c.dropout,
                }
            return {}
        else:
            c = psutil.net_io_counters()
            return {
                "bytes_sent": c.bytes_sent,
                "bytes_recv": c.bytes_recv,
                "packets_sent": c.packets_sent,
                "packets_recv": c.packets_recv,
                "errin": c.errin,
                "errout": c.errout,
                "dropin": c.dropin,
                "dropout": c.dropout,
            }
    except Exception:
        return {}


def get_hostname() -> str:
    """
    Helyi hostname lekérdezése.

    Returns:
        A gép hostname-je
    """
    return socket.gethostname()


def get_fqdn() -> str:
    """
    Helyi FQDN (Fully Qualified Domain Name) lekérdezése.

    Returns:
        A gép teljes domain neve
    """
    return socket.getfqdn()


def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Hostname feloldása IP címre.

    Args:
        hostname: Feloldandó hostname

    Returns:
        IP cím vagy None ha nem sikerült

    Example:
        >>> ip = resolve_hostname("google.com")
        >>> print(f"Google IP: {ip}")
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def reverse_resolve(ip_address: str) -> Optional[str]:
    """
    IP cím feloldása hostname-re.

    Args:
        ip_address: Feloldandó IP cím

    Returns:
        Hostname vagy None ha nem sikerült

    Example:
        >>> name = reverse_resolve("8.8.8.8")
        >>> print(f"8.8.8.8 = {name}")
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except (socket.herror, socket.gaierror):
        return None
