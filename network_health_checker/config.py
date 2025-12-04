"""
Konfiguráció kezelés a Network Health Checker-hez.

Ez a modul tartalmazza a konfigurációs beállításokat, amelyeket
környezeti változókból vagy .env fájlból tölt be.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env fájl betöltése a projekt gyökeréből
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """
    Alkalmazás beállítások.

    A beállítások környezeti változókból töltődnek be,
    alapértelmezett értékekkel.

    Attributes:
        snmp_community: SNMP community string (alapért. "public")
        snmp_version: SNMP verzió (1, 2c, vagy 3)
        default_timeout: Alapértelmezett timeout másodpercben
        log_level: Naplózási szint
        mikrotik_host: Mikrotik eszköz címe
        ubiquiti_host: Ubiquiti eszköz címe
    """

    # SNMP beállítások
    snmp_community: str = Field(default="public", alias="SNMP_COMMUNITY")
    snmp_version: str = Field(default="2c", alias="SNMP_VERSION")
    snmp_port: int = Field(default=161, alias="SNMP_PORT")

    # Timeout beállítások
    default_timeout: float = Field(default=5.0, alias="DEFAULT_TIMEOUT")
    ping_timeout: float = Field(default=2.0, alias="PING_TIMEOUT")
    port_scan_timeout: float = Field(default=1.0, alias="PORT_SCAN_TIMEOUT")
    dns_timeout: float = Field(default=5.0, alias="DNS_TIMEOUT")

    # Hálózati eszközök
    mikrotik_host: Optional[str] = Field(default=None, alias="MIKROTIK_HOST")
    ubiquiti_host: Optional[str] = Field(default=None, alias="UBIQUITI_HOST")
    omada_host: Optional[str] = Field(default=None, alias="OMADA_HOST")

    # Naplózás
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Beállítások lekérése (cached).

    Az első hívás után cache-eli az eredményt a teljesítmény érdekében.

    Returns:
        Settings objektum a konfigurációval
    """
    return Settings()


# Gyakran használt szolgáltatás nevek és portok
COMMON_PORTS = {
    20: "ftp-data",
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    143: "imap",
    443: "https",
    445: "smb",
    993: "imaps",
    995: "pop3s",
    1433: "mssql",
    1521: "oracle",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8080: "http-proxy",
    8443: "https-alt",
    27017: "mongodb",
}


def get_service_name(port: int) -> Optional[str]:
    """
    Port számhoz tartozó szolgáltatás neve.

    Args:
        port: Port száma

    Returns:
        Szolgáltatás neve vagy None ha ismeretlen
    """
    return COMMON_PORTS.get(port)


# Standard MIB-2 OID-k
SNMP_OIDS = {
    # System csoport (1.3.6.1.2.1.1)
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
    # Interfaces csoport (1.3.6.1.2.1.2)
    "ifNumber": "1.3.6.1.2.1.2.1.0",
    "ifTable": "1.3.6.1.2.1.2.2",
    "ifIndex": "1.3.6.1.2.1.2.2.1.1",
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifType": "1.3.6.1.2.1.2.2.1.3",
    "ifMtu": "1.3.6.1.2.1.2.2.1.4",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifPhysAddress": "1.3.6.1.2.1.2.2.1.6",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
    "ifInOctets": "1.3.6.1.2.1.2.2.1.10",
    "ifOutOctets": "1.3.6.1.2.1.2.2.1.16",
}


# DNS rekord típusok
DNS_RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA", "PTR", "SRV"]
