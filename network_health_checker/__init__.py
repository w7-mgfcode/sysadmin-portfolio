"""
Network Health Checker - Hálózati diagnosztikai eszközök.

Ez a modul tartalmazza a hálózati monitorozáshoz szükséges eszközöket:
- Ping monitor (ICMP)
- Port scanner (TCP)
- DNS lookup
- Subnet calculator
- SNMP query
- Network info

Használat:
    >>> from network_health_checker import ping_host
    >>> result = ping_host("8.8.8.8")
    >>> print(f"Status: {result.status}, Latency: {result.latency_ms}ms")

CLI használat:
    $ python -m network_health_checker ping 8.8.8.8
    $ python -m network_health_checker scan 192.168.1.1 -p 22,80,443
    $ python -m network_health_checker dns google.com -t MX
"""

__version__ = "1.0.0"
__author__ = "SysAdmin Portfolio"

# Models
from .models import (
    ConnectionInfo,
    DNSRecord,
    HostStatus,
    NetworkDevice,
    NetworkInterface,
    PingResult,
    PortScanResult,
    SNMPInterface,
    SubnetInfo,
)

# Network tools
from .network_tools import (
    # Ping
    is_host_reachable,
    ping_host,
    ping_hosts,
    # Port scanner
    scan_common_ports,
    scan_port,
    scan_ports,
    # DNS
    get_mx_records,
    get_nameservers,
    lookup_all_records,
    lookup_dns,
    reverse_lookup,
    # Subnet
    calculate_subnet,
    cidr_to_netmask,
    get_subnet_hosts,
    ip_in_subnet,
    is_private_ip,
    is_valid_ip,
    iterate_subnet_hosts,
    netmask_to_cidr,
    split_subnet,
    # Network info
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
    # SNMP (async)
    check_snmp_reachable,
    get_interface_stats,
    get_interfaces,
    get_system_info,
    snmp_get,
    snmp_get_bulk,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Models
    "HostStatus",
    "PingResult",
    "PortScanResult",
    "DNSRecord",
    "SubnetInfo",
    "SNMPInterface",
    "NetworkDevice",
    "NetworkInterface",
    "ConnectionInfo",
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
