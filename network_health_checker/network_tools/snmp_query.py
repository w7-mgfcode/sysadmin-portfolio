"""
SNMP Query - SNMP lekérdezési eszközök.

Ez a modul tartalmazza az SNMP lekérdezési funkciókat hálózati
eszközök monitorozásához (Mikrotik, Ubiquiti, stb.).

Használat:
    >>> from network_tools.snmp_query import get_system_info
    >>> info = get_system_info("192.168.1.1")
    >>> print(f"Device: {info.sys_name}")
"""

from typing import Any, Dict, List, Optional

from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    bulk_cmd,
    get_cmd,
)

from ..config import SNMP_OIDS, get_settings
from ..models import NetworkDevice, SNMPInterface


async def snmp_get(
    host: str,
    oid: str,
    community: str | None = None,
    port: int | None = None,
    timeout: float | None = None,
) -> Optional[Any]:
    """
    Egyetlen SNMP OID lekérdezése.

    Args:
        host: Cél eszköz IP címe vagy hostname
        oid: Lekérdezendő OID (pl. "1.3.6.1.2.1.1.1.0")
        community: SNMP community string (None = config default)
        port: SNMP port (None = config default)
        timeout: Lekérdezési időtúllépés

    Returns:
        Az OID értéke vagy None hiba esetén

    Example:
        >>> value = await snmp_get("192.168.1.1", "1.3.6.1.2.1.1.5.0")
        >>> print(f"sysName: {value}")
    """
    # Konfiguráció betöltése
    settings = get_settings()
    if community is None:
        community = settings.snmp_community
    if port is None:
        port = settings.snmp_port
    if timeout is None:
        timeout = settings.default_timeout

    try:
        # SNMP GET végrehajtása
        iterator = get_cmd(
            SnmpEngine(),
            CommunityData(community),
            await UdpTransportTarget.create((host, port), timeout=timeout),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        error_indication, error_status, error_index, var_binds = await iterator

        if error_indication:
            # Hálózati vagy protokoll hiba
            return None

        if error_status:
            # SNMP hiba (pl. nincs ilyen OID)
            return None

        # Érték kinyerése
        for name, value in var_binds:
            return value.prettyPrint()

    except Exception:
        return None


async def snmp_get_bulk(
    host: str,
    oid: str,
    community: str | None = None,
    port: int | None = None,
    timeout: float | None = None,
    max_repetitions: int = 25,
) -> List[tuple]:
    """
    SNMP GETBULK lekérdezés táblázatos adatokhoz.

    Hatékonyabb mint az egyedi GET hívások sorozata,
    egyetlen kéréssel több értéket kér le.

    Args:
        host: Cél eszköz IP címe
        oid: Kezdő OID a táblázathoz
        community: SNMP community string
        port: SNMP port
        timeout: Lekérdezési időtúllépés
        max_repetitions: Maximum visszaadandó sorok száma

    Returns:
        Lista (oid, value) tuple-ökkel

    Example:
        >>> interfaces = await snmp_get_bulk("192.168.1.1", "1.3.6.1.2.1.2.2.1.2")
        >>> for oid, name in interfaces:
        ...     print(f"Interface: {name}")
    """
    # Konfiguráció betöltése
    settings = get_settings()
    if community is None:
        community = settings.snmp_community
    if port is None:
        port = settings.snmp_port
    if timeout is None:
        timeout = settings.default_timeout

    results: List[tuple] = []

    try:
        # SNMP GETBULK végrehajtása
        iterator = bulk_cmd(
            SnmpEngine(),
            CommunityData(community),
            await UdpTransportTarget.create((host, port), timeout=timeout),
            ContextData(),
            0,  # nonRepeaters
            max_repetitions,
            ObjectType(ObjectIdentity(oid)),
        )

        async for error_indication, error_status, error_index, var_binds in iterator:
            if error_indication or error_status:
                break

            for var_bind in var_binds:
                name, value = var_bind
                oid_str = str(name)
                # Ellenőrizzük, hogy még a kért OID alatt vagyunk-e
                if not oid_str.startswith(oid):
                    return results
                results.append((oid_str, value.prettyPrint()))

    except Exception:
        pass

    return results


async def get_system_info(
    host: str,
    community: str | None = None,
) -> Optional[NetworkDevice]:
    """
    Hálózati eszköz alapvető rendszer információinak lekérdezése.

    Standard MIB-2 system csoport értékeket kérdez le.

    Args:
        host: Cél eszköz IP címe
        community: SNMP community string

    Returns:
        NetworkDevice objektum vagy None hiba esetén

    Example:
        >>> device = await get_system_info("192.168.1.1")
        >>> if device:
        ...     print(f"Name: {device.sys_name}")
        ...     print(f"Uptime: {device.uptime_seconds}s")
    """
    try:
        # Párhuzamos lekérdezések az összes system OID-re
        sys_descr = await snmp_get(host, SNMP_OIDS["sysDescr"], community)
        sys_object_id = await snmp_get(host, SNMP_OIDS["sysObjectID"], community)
        sys_uptime = await snmp_get(host, SNMP_OIDS["sysUpTime"], community)
        sys_contact = await snmp_get(host, SNMP_OIDS["sysContact"], community)
        sys_name = await snmp_get(host, SNMP_OIDS["sysName"], community)
        sys_location = await snmp_get(host, SNMP_OIDS["sysLocation"], community)

        # Ha semmit nem kaptunk, az eszköz nem elérhető
        if all(v is None for v in [sys_descr, sys_name, sys_uptime]):
            return None

        # Uptime konvertálása másodpercre (SNMP timeticks = 1/100 sec)
        uptime_seconds: int | None = None
        if sys_uptime:
            try:
                # Az uptime stringből kinyerjük a számot
                uptime_ticks = int(sys_uptime)
                uptime_seconds = uptime_ticks // 100
            except (ValueError, TypeError):
                pass

        return NetworkDevice(
            host=host,
            sys_descr=sys_descr,
            sys_object_id=sys_object_id,
            sys_name=sys_name,
            sys_location=sys_location,
            sys_contact=sys_contact,
            uptime_seconds=uptime_seconds,
        )

    except Exception:
        return None


async def get_interfaces(
    host: str,
    community: str | None = None,
) -> List[SNMPInterface]:
    """
    Hálózati eszköz interfészeinek lekérdezése SNMP-n keresztül.

    IF-MIB táblázatból olvassa ki az interfész információkat.

    Args:
        host: Cél eszköz IP címe
        community: SNMP community string

    Returns:
        SNMPInterface objektumok listája

    Example:
        >>> interfaces = await get_interfaces("192.168.1.1")
        >>> for iface in interfaces:
        ...     print(f"{iface.name}: {iface.status}")
    """
    interfaces: List[SNMPInterface] = []

    try:
        # Interface index-ek lekérése
        indices = await snmp_get_bulk(host, SNMP_OIDS["ifIndex"], community)

        for oid, index_value in indices:
            try:
                if_index = int(index_value)
            except ValueError:
                continue

            # Interface adatok lekérdezése egyenként
            # (BULK használata index-enként nem praktikus)
            if_descr = await snmp_get(
                host, f"{SNMP_OIDS['ifDescr']}.{if_index}", community
            )
            if_type = await snmp_get(
                host, f"{SNMP_OIDS['ifType']}.{if_index}", community
            )
            if_mtu = await snmp_get(host, f"{SNMP_OIDS['ifMtu']}.{if_index}", community)
            if_speed = await snmp_get(
                host, f"{SNMP_OIDS['ifSpeed']}.{if_index}", community
            )
            if_phys = await snmp_get(
                host, f"{SNMP_OIDS['ifPhysAddress']}.{if_index}", community
            )
            if_oper = await snmp_get(
                host, f"{SNMP_OIDS['ifOperStatus']}.{if_index}", community
            )
            if_in_octets = await snmp_get(
                host, f"{SNMP_OIDS['ifInOctets']}.{if_index}", community
            )
            if_out_octets = await snmp_get(
                host, f"{SNMP_OIDS['ifOutOctets']}.{if_index}", community
            )

            # Operációs státusz konvertálása
            # 1=up, 2=down, 3=testing, 4=unknown, 5=dormant, 6=notPresent, 7=lowerLayerDown
            status_map = {
                "1": "up",
                "2": "down",
                "3": "testing",
                "4": "unknown",
                "5": "dormant",
                "6": "notPresent",
                "7": "lowerLayerDown",
            }
            oper_status = status_map.get(str(if_oper), "unknown") if if_oper else None

            interfaces.append(
                SNMPInterface(
                    index=if_index,
                    name=if_descr,
                    type=_safe_int(if_type),
                    mtu=_safe_int(if_mtu),
                    speed=_safe_int(if_speed),
                    phys_address=if_phys,
                    oper_status=oper_status,
                    in_octets=_safe_int(if_in_octets),
                    out_octets=_safe_int(if_out_octets),
                )
            )

    except Exception:
        pass

    return interfaces


def _safe_int(value: Any) -> Optional[int]:
    """
    Biztonságos integer konverzió.

    Args:
        value: Konvertálandó érték

    Returns:
        Integer vagy None ha nem konvertálható
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


async def get_interface_stats(
    host: str,
    community: str | None = None,
) -> Dict[str, Dict[str, int]]:
    """
    Interfész forgalmi statisztikák lekérdezése.

    Visszaadja az in/out octet számlálókat interfészenként.

    Args:
        host: Cél eszköz IP címe
        community: SNMP community string

    Returns:
        Dictionary {interface_name: {in_octets, out_octets}}

    Example:
        >>> stats = await get_interface_stats("192.168.1.1")
        >>> for name, data in stats.items():
        ...     print(f"{name}: IN={data['in_octets']}, OUT={data['out_octets']}")
    """
    stats: Dict[str, Dict[str, int]] = {}

    interfaces = await get_interfaces(host, community)
    for iface in interfaces:
        if iface.name:
            stats[iface.name] = {
                "in_octets": iface.in_octets or 0,
                "out_octets": iface.out_octets or 0,
            }

    return stats


async def check_snmp_reachable(
    host: str,
    community: str | None = None,
    timeout: float = 2.0,
) -> bool:
    """
    Ellenőrzi, hogy egy eszköz elérhető-e SNMP-n keresztül.

    Gyors ellenőrzés a sysDescr lekérdezésével.

    Args:
        host: Cél eszköz IP címe
        community: SNMP community string
        timeout: Lekérdezési időtúllépés

    Returns:
        True ha az eszköz válaszol SNMP-re
    """
    result = await snmp_get(host, SNMP_OIDS["sysDescr"], community, timeout=timeout)
    return result is not None
