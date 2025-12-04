"""
Pydantic adatmodellek a Network Health Checker-hez.

Ez a modul tartalmazza az összes adatstruktúrát, amelyeket a hálózati
eszközök használnak az eredmények tárolására és validálására.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HostStatus(str, Enum):
    """
    Host állapot enum.

    A ping és egyéb hálózati műveletek eredményének jelzésére szolgál.
    """

    UP = "up"
    DOWN = "down"
    TIMEOUT = "timeout"
    ERROR = "error"


class PingResult(BaseModel):
    """
    ICMP ping művelet eredménye.

    Tárolja a ping válaszidőt, státuszt és az esetleges hibaüzeneteket.
    A timestamp mező automatikusan kitöltődik a lekérdezés időpontjával.

    Attributes:
        host: A pinged host neve vagy címe
        ip_address: Feloldott IP cím (ha elérhető)
        status: A ping művelet eredménye
        latency_ms: Válaszidő milliszekundumban
        timestamp: A lekérdezés időpontja
        error_message: Hibaüzenet (ha volt hiba)
    """

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    host: str
    ip_address: Optional[str] = None
    status: HostStatus
    latency_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = None


class PortScanResult(BaseModel):
    """
    TCP port szkennelés eredménye.

    Tartalmazza a port állapotát, a futó szolgáltatás nevét (ha ismert),
    és az esetleges banner információkat.

    Attributes:
        host: A szkennelt host
        port: A szkennelt port száma
        is_open: True ha a port nyitott
        service_name: A szolgáltatás neve (ha ismert)
        banner: Banner információ (ha elérhető)
        latency_ms: Kapcsolódási idő milliszekundumban
    """

    host: str
    port: int
    is_open: bool
    service_name: Optional[str] = None
    banner: Optional[str] = None
    latency_ms: Optional[float] = None


class DNSRecord(BaseModel):
    """
    DNS lekérdezés eredménye.

    Támogatja az összes gyakori rekord típust: A, AAAA, MX, TXT, CNAME, NS.

    Attributes:
        query: Az eredeti lekérdezés
        record_type: A rekord típusa (A, AAAA, MX, stb.)
        values: A visszakapott értékek listája
        ttl: Time-to-live másodpercben
    """

    query: str
    record_type: str
    values: List[str]
    ttl: Optional[int] = None


class SubnetInfo(BaseModel):
    """
    Alhálózat számítás eredménye.

    CIDR notation alapján kiszámítja a hálózati címet, broadcast címet,
    és a használható host tartományt.

    Attributes:
        network: Hálózati cím
        netmask: Alhálózati maszk
        broadcast: Broadcast cím
        first_host: Első használható host cím
        last_host: Utolsó használható host cím
        total_hosts: Használható hostok száma
        cidr: CIDR prefix hossz
    """

    network: str
    netmask: str
    broadcast: str
    first_host: str
    last_host: str
    total_hosts: int
    cidr: int


class SNMPInterface(BaseModel):
    """
    SNMP interfész statisztikák.

    Hálózati eszközök (Mikrotik, Ubiquiti, stb.) interfészeinek
    forgalmi és állapot adatait tárolja.

    Attributes:
        index: Interfész index (ifIndex)
        name: Interfész neve (ifDescr)
        type: Interfész típusa (ifType)
        mtu: Maximum Transmission Unit
        speed: Interfész sebessége (bps)
        phys_address: Fizikai (MAC) cím
        oper_status: Operációs állapot (up/down)
        in_octets: Bejövő bájtok száma
        out_octets: Kimenő bájtok száma
    """

    index: int
    name: Optional[str] = None
    type: Optional[int] = None
    mtu: Optional[int] = None
    speed: Optional[int] = None
    phys_address: Optional[str] = None
    oper_status: Optional[str] = None
    in_octets: Optional[int] = None
    out_octets: Optional[int] = None


class NetworkDevice(BaseModel):
    """
    Hálózati eszköz információk SNMP-ből.

    A standard MIB-2 system csoport adatait és az eszköz
    összes interfészének statisztikáit tartalmazza.

    Attributes:
        host: Az eszköz címe
        sys_name: Rendszer neve (sysName)
        sys_descr: Rendszer leírása (sysDescr)
        sys_object_id: Rendszer object ID (sysObjectID)
        uptime_seconds: Üzemidő másodpercben
        sys_contact: Kapcsolattartó (sysContact)
        sys_location: Fizikai helyszín (sysLocation)
        interfaces: Interfészek listája
    """

    host: str
    sys_name: Optional[str] = None
    sys_descr: Optional[str] = None
    sys_object_id: Optional[str] = None
    uptime_seconds: Optional[int] = None
    sys_contact: Optional[str] = None
    sys_location: Optional[str] = None
    interfaces: List[SNMPInterface] = Field(default_factory=list)


class NetworkInterface(BaseModel):
    """
    Helyi hálózati interfész információk.

    A rendszer saját hálózati adaptereinek adatait tárolja.

    Attributes:
        name: Interfész neve (eth0, ens33, stb.)
        ipv4_address: IPv4 cím
        ipv4_netmask: IPv4 alhálózati maszk
        ipv6_address: IPv6 cím (ha van)
        mac_address: MAC cím
        is_up: True ha az interfész aktív
        speed_mbps: Interfész sebessége (Mbps)
        mtu: Maximum Transmission Unit
    """

    name: str
    ipv4_address: Optional[str] = None
    ipv4_netmask: Optional[str] = None
    ipv6_address: Optional[str] = None
    mac_address: Optional[str] = None
    is_up: bool = False
    speed_mbps: Optional[int] = None
    mtu: Optional[int] = None


class ConnectionInfo(BaseModel):
    """
    Aktív hálózati kapcsolat információk.

    Attributes:
        protocol: Protokoll típusa (tcp, udp)
        local_address: Helyi IP cím
        local_port: Helyi port
        remote_address: Távoli IP cím
        remote_port: Távoli port
        status: Kapcsolat állapota (ESTABLISHED, LISTEN, stb.)
        pid: A kapcsolatot birtokló folyamat PID-je
        process_name: A folyamat neve
    """

    protocol: str
    local_address: Optional[str] = None
    local_port: Optional[int] = None
    remote_address: Optional[str] = None
    remote_port: Optional[int] = None
    status: str
    pid: Optional[int] = None
    process_name: Optional[str] = None
