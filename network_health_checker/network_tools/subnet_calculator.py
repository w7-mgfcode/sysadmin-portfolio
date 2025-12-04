"""
Subnet Calculator - IP és alhálózat számítások.

Ez a modul tartalmazza az IP cím és alhálózat számítási funkciókat,
CIDR notation támogatással.

Használat:
    >>> from network_tools.subnet_calculator import calculate_subnet
    >>> info = calculate_subnet("192.168.1.0/24")
    >>> print(f"Network: {info.network}, Hosts: {info.total_hosts}")
"""

import ipaddress
from typing import Iterator, List

from ..models import SubnetInfo


def calculate_subnet(cidr: str) -> SubnetInfo:
    """
    Alhálózat információk kiszámítása CIDR notation alapján.

    Args:
        cidr: CIDR formátumú hálózati cím (pl. "192.168.1.0/24")

    Returns:
        SubnetInfo objektum a számított értékekkel

    Raises:
        ValueError: Ha a CIDR formátum érvénytelen

    Example:
        >>> info = calculate_subnet("10.0.0.0/8")
        >>> print(f"Broadcast: {info.broadcast}")
        >>> print(f"Usable hosts: {info.total_hosts}")
    """
    try:
        # IPv4Network objektum létrehozása
        network = ipaddress.IPv4Network(cidr, strict=False)
    except ValueError as e:
        raise ValueError(f"Invalid CIDR notation: {cidr} - {e}")

    # Hostok számának kiszámítása
    # A hálózati és broadcast cím nem használható host-ként
    total_hosts = network.num_addresses - 2 if network.prefixlen < 31 else network.num_addresses

    # Első és utolsó host meghatározása
    hosts = list(network.hosts())
    first_host = str(hosts[0]) if hosts else str(network.network_address)
    last_host = str(hosts[-1]) if hosts else str(network.broadcast_address)

    return SubnetInfo(
        network=str(network.network_address),
        netmask=str(network.netmask),
        broadcast=str(network.broadcast_address),
        first_host=first_host,
        last_host=last_host,
        total_hosts=max(0, total_hosts),
        cidr=network.prefixlen,
    )


def ip_in_subnet(ip: str, cidr: str) -> bool:
    """
    Ellenőrzi, hogy egy IP cím egy adott alhálózatban van-e.

    Args:
        ip: Ellenőrizendő IP cím
        cidr: Alhálózat CIDR formátumban

    Returns:
        True ha az IP az alhálózatban van

    Example:
        >>> ip_in_subnet("192.168.1.100", "192.168.1.0/24")
        True
        >>> ip_in_subnet("10.0.0.1", "192.168.1.0/24")
        False
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        network = ipaddress.IPv4Network(cidr, strict=False)
        return ip_obj in network
    except ValueError:
        return False


def get_subnet_hosts(cidr: str, limit: int | None = None) -> List[str]:
    """
    Alhálózat összes használható host címének listázása.

    Args:
        cidr: Alhálózat CIDR formátumban
        limit: Maximum visszaadandó címek száma (opcionális)

    Returns:
        IP címek listája

    Note:
        Nagyobb alhálózatoknál (pl. /16) ez nagyon hosszú lista lehet!
        Használd a limit paramétert a memória védelméhez.

    Example:
        >>> hosts = get_subnet_hosts("192.168.1.0/30")
        >>> print(hosts)  # ['192.168.1.1', '192.168.1.2']
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        hosts = list(network.hosts())

        if limit:
            hosts = hosts[:limit]

        return [str(h) for h in hosts]
    except ValueError:
        return []


def iterate_subnet_hosts(cidr: str) -> Iterator[str]:
    """
    Alhálózat host címeinek iterálása.

    Generator függvény, ami egyenként adja vissza a host címeket.
    Memória-hatékony nagy alhálózatokhoz.

    Args:
        cidr: Alhálózat CIDR formátumban

    Yields:
        IP címek stringként

    Example:
        >>> for ip in iterate_subnet_hosts("192.168.1.0/28"):
        ...     print(f"Checking {ip}...")
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        for host in network.hosts():
            yield str(host)
    except ValueError:
        return


def netmask_to_cidr(netmask: str) -> int:
    """
    Alhálózati maszk konvertálása CIDR prefix hosszra.

    Args:
        netmask: Alhálózati maszk (pl. "255.255.255.0")

    Returns:
        CIDR prefix hossz (pl. 24)

    Example:
        >>> netmask_to_cidr("255.255.255.0")
        24
        >>> netmask_to_cidr("255.255.0.0")
        16
    """
    try:
        # IP cím objektumként értelmezve a maszk
        mask = ipaddress.IPv4Address(netmask)
        # Bináris reprezentáció 1-eseinek számlálása
        binary = bin(int(mask))
        return binary.count("1")
    except ValueError:
        raise ValueError(f"Invalid netmask: {netmask}")


def cidr_to_netmask(cidr: int) -> str:
    """
    CIDR prefix hossz konvertálása alhálózati maszkra.

    Args:
        cidr: CIDR prefix hossz (0-32)

    Returns:
        Alhálózati maszk string

    Example:
        >>> cidr_to_netmask(24)
        '255.255.255.0'
        >>> cidr_to_netmask(16)
        '255.255.0.0'
    """
    if not 0 <= cidr <= 32:
        raise ValueError(f"Invalid CIDR prefix: {cidr}. Must be 0-32.")

    # Hálózat létrehozása és maszk kinyerése
    network = ipaddress.IPv4Network(f"0.0.0.0/{cidr}")
    return str(network.netmask)


def split_subnet(cidr: str, new_prefix: int) -> List[SubnetInfo]:
    """
    Alhálózat felosztása kisebb alhálózatokra.

    Args:
        cidr: Eredeti alhálózat CIDR formátumban
        new_prefix: Új prefix hossz (nagyobb mint az eredeti)

    Returns:
        Felosztott alhálózatok listája

    Example:
        >>> subnets = split_subnet("192.168.0.0/24", 26)
        >>> for s in subnets:
        ...     print(f"{s.network}/{s.cidr}: {s.total_hosts} hosts")
    """
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)

        if new_prefix <= network.prefixlen:
            raise ValueError(f"New prefix must be larger than {network.prefixlen}")

        subnets = list(network.subnets(new_prefix=new_prefix))
        return [calculate_subnet(str(s)) for s in subnets]

    except ValueError as e:
        raise ValueError(f"Cannot split subnet: {e}")


def is_private_ip(ip: str) -> bool:
    """
    Ellenőrzi, hogy egy IP cím privát tartományban van-e.

    RFC 1918 privát tartományok:
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16

    Args:
        ip: Ellenőrizendő IP cím

    Returns:
        True ha privát IP

    Example:
        >>> is_private_ip("192.168.1.1")
        True
        >>> is_private_ip("8.8.8.8")
        False
    """
    try:
        ip_obj = ipaddress.IPv4Address(ip)
        return ip_obj.is_private
    except ValueError:
        return False


def is_valid_ip(ip: str) -> bool:
    """
    IP cím formátum validálása.

    Args:
        ip: Ellenőrizendő string

    Returns:
        True ha érvényes IPv4 cím
    """
    try:
        ipaddress.IPv4Address(ip)
        return True
    except ValueError:
        return False
