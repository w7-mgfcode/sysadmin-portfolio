"""
Network Tools - Hálózati eszközök gyűjteménye.

Tartalmazza az összes hálózati diagnosztikai és monitorozási eszközt.

Modulok:
    - ping_monitor: ICMP ping funkciók
    - port_scanner: TCP port szkennelés
    - dns_lookup: DNS lekérdezések
    - subnet_calculator: IP/subnet számítások
    - snmp_query: SNMP lekérdezések
    - network_info: Helyi hálózati információk
"""

# Ping monitor exports
from .ping_monitor import is_host_reachable, ping_host, ping_hosts

# Port scanner exports
from .port_scanner import scan_common_ports, scan_port, scan_ports

# DNS lookup exports
from .dns_lookup import (
    get_mx_records,
    get_nameservers,
    lookup_all_records,
    lookup_dns,
    reverse_lookup,
)

# Subnet calculator exports
from .subnet_calculator import (
    calculate_subnet,
    cidr_to_netmask,
    get_subnet_hosts,
    ip_in_subnet,
    is_private_ip,
    is_valid_ip,
    iterate_subnet_hosts,
    netmask_to_cidr,
    split_subnet,
)

# Network info exports
from .network_info import (
    get_active_connections,
    get_default_gateway,
    get_fqdn,
    get_hostname,
    get_interface_by_name,
    get_interface_io_counters,
    get_listening_ports,
    get_local_interfaces,
    resolve_hostname,
    reverse_resolve,
)

# SNMP exports (async functions)
from .snmp_query import (
    check_snmp_reachable,
    get_interface_stats,
    get_interfaces,
    get_system_info,
    snmp_get,
    snmp_get_bulk,
)

__all__ = [
    # Ping
    "ping_host",
    "ping_hosts",
    "is_host_reachable",
    # Port scanner
    "scan_port",
    "scan_ports",
    "scan_common_ports",
    # DNS
    "lookup_dns",
    "lookup_all_records",
    "reverse_lookup",
    "get_nameservers",
    "get_mx_records",
    # Subnet
    "calculate_subnet",
    "ip_in_subnet",
    "get_subnet_hosts",
    "iterate_subnet_hosts",
    "netmask_to_cidr",
    "cidr_to_netmask",
    "split_subnet",
    "is_private_ip",
    "is_valid_ip",
    # Network info
    "get_local_interfaces",
    "get_interface_by_name",
    "get_default_gateway",
    "get_active_connections",
    "get_listening_ports",
    "get_interface_io_counters",
    "get_hostname",
    "get_fqdn",
    "resolve_hostname",
    "reverse_resolve",
    # SNMP
    "snmp_get",
    "snmp_get_bulk",
    "get_system_info",
    "get_interfaces",
    "get_interface_stats",
    "check_snmp_reachable",
]
