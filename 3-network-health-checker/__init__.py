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
"""

__version__ = "1.0.0"
__author__ = "SysAdmin Portfolio"
