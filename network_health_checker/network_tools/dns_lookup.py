"""
DNS Lookup - DNS lekérdezési eszközök.

Ez a modul tartalmazza a DNS lekérdezési funkciókat különböző
rekord típusokhoz (A, AAAA, MX, TXT, CNAME, NS, stb.).

Használat:
    >>> from network_tools.dns_lookup import lookup_dns
    >>> records = lookup_dns("google.com", "A")
    >>> for record in records:
    ...     print(f"IP: {record}")
"""

from typing import List, Optional

import dns.exception
import dns.resolver

from ..config import DNS_RECORD_TYPES, get_settings
from ..models import DNSRecord


def lookup_dns(
    domain: str,
    record_type: str = "A",
    timeout: float | None = None,
    nameserver: str | None = None,
) -> DNSRecord:
    """
    DNS rekord lekérdezése.

    Lekérdezi a megadott domain rekordját a megadott típussal.

    Args:
        domain: A lekérdezendő domain név
        record_type: Rekord típus (A, AAAA, MX, TXT, CNAME, NS, SOA, PTR, SRV)
        timeout: Lekérdezési időtúllépés másodpercben
        nameserver: Egyedi DNS szerver címe (opcionális)

    Returns:
        DNSRecord a lekérdezés eredményével

    Raises:
        ValueError: Ha a rekord típus érvénytelen

    Example:
        >>> result = lookup_dns("google.com", "MX")
        >>> for mx in result.values:
        ...     print(f"Mail server: {mx}")
    """
    # Rekord típus validálása
    record_type = record_type.upper()
    if record_type not in DNS_RECORD_TYPES:
        raise ValueError(f"Invalid record type: {record_type}. Valid types: {DNS_RECORD_TYPES}")

    # Konfiguráció betöltése
    settings = get_settings()
    if timeout is None:
        timeout = settings.dns_timeout

    # Resolver konfigurálása
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout
    resolver.lifetime = timeout

    # Egyedi nameserver beállítása ha meg van adva
    if nameserver:
        resolver.nameservers = [nameserver]

    try:
        # DNS lekérdezés végrehajtása
        answers = resolver.resolve(domain, record_type)

        # Eredmények feldolgozása
        values: List[str] = []
        ttl: Optional[int] = None

        for rdata in answers:
            # TTL mentése az első rekordból
            if ttl is None:
                ttl = answers.rrset.ttl

            # Érték formázása a rekord típus alapján
            if record_type == "MX":
                # MX rekordnál prioritás + mail szerver
                values.append(f"{rdata.preference} {rdata.exchange}")
            elif record_type == "SOA":
                # SOA rekord részletes formázása
                values.append(
                    f"mname={rdata.mname} rname={rdata.rname} "
                    f"serial={rdata.serial} refresh={rdata.refresh}"
                )
            elif record_type == "SRV":
                # SRV rekord formázása
                values.append(
                    f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
                )
            else:
                # Standard rekordok (A, AAAA, TXT, CNAME, NS, PTR)
                values.append(str(rdata))

        return DNSRecord(
            query=domain,
            record_type=record_type,
            values=values,
            ttl=ttl,
        )

    except dns.resolver.NXDOMAIN:
        # Domain nem létezik
        return DNSRecord(
            query=domain,
            record_type=record_type,
            values=[],
            ttl=None,
        )

    except dns.resolver.NoAnswer:
        # Nincs válasz a megadott rekord típusra
        return DNSRecord(
            query=domain,
            record_type=record_type,
            values=[],
            ttl=None,
        )

    except dns.resolver.NoNameservers:
        # Nem sikerült elérni a DNS szervert
        return DNSRecord(
            query=domain,
            record_type=record_type,
            values=[],
            ttl=None,
        )

    except dns.exception.Timeout:
        # Időtúllépés
        return DNSRecord(
            query=domain,
            record_type=record_type,
            values=[],
            ttl=None,
        )


def lookup_all_records(domain: str, timeout: float | None = None) -> List[DNSRecord]:
    """
    Összes gyakori DNS rekord típus lekérdezése.

    Lekérdezi az A, AAAA, MX, TXT, CNAME és NS rekordokat.

    Args:
        domain: A lekérdezendő domain
        timeout: Lekérdezési időtúllépés

    Returns:
        DNSRecord lista minden sikeres lekérdezéshez
    """
    record_types = ["A", "AAAA", "MX", "TXT", "CNAME", "NS"]
    results: List[DNSRecord] = []

    for record_type in record_types:
        result = lookup_dns(domain, record_type, timeout)
        # Csak azokat adjuk vissza ahol van eredmény
        if result.values:
            results.append(result)

    return results


def reverse_lookup(ip_address: str, timeout: float | None = None) -> DNSRecord:
    """
    Reverse DNS lookup (PTR rekord).

    IP címből domain név lekérdezése.

    Args:
        ip_address: IP cím (IPv4 vagy IPv6)
        timeout: Lekérdezési időtúllépés

    Returns:
        DNSRecord a PTR rekorddal

    Example:
        >>> result = reverse_lookup("8.8.8.8")
        >>> if result.values:
        ...     print(f"Hostname: {result.values[0]}")
    """
    # IP cím konvertálása reverse DNS formátumra
    try:
        reverse_name = dns.reversename.from_address(ip_address)
    except Exception:
        return DNSRecord(
            query=ip_address,
            record_type="PTR",
            values=[],
            ttl=None,
        )

    return lookup_dns(str(reverse_name), "PTR", timeout)


def get_nameservers(domain: str, timeout: float | None = None) -> List[str]:
    """
    Domain authoritative nameserver-einek lekérdezése.

    Args:
        domain: A lekérdezendő domain
        timeout: Lekérdezési időtúllépés

    Returns:
        Nameserver nevek listája
    """
    result = lookup_dns(domain, "NS", timeout)
    return result.values


def get_mx_records(domain: str, timeout: float | None = None) -> List[str]:
    """
    Domain mail szervereinek lekérdezése.

    Args:
        domain: A lekérdezendő domain
        timeout: Lekérdezési időtúllépés

    Returns:
        MX rekordok listája (prioritás + szerver)
    """
    result = lookup_dns(domain, "MX", timeout)
    return result.values
