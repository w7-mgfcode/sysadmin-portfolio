"""
Network Info tesztek.

Tesztek a helyi hálózati információk lekérdezéséhez.
"""

import socket
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Projekt gyökér hozzáadása a path-hoz
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_health_checker.network_tools.network_info import (
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


class TestGetLocalInterfaces:
    """get_local_interfaces függvény tesztjei."""

    def test_returns_list_of_interfaces(self, mock_psutil_interfaces):
        """Interfész lista visszaadása."""
        interfaces = get_local_interfaces()

        assert isinstance(interfaces, list)
        assert len(interfaces) > 0

    def test_interface_has_required_fields(self, mock_psutil_interfaces):
        """Interfész objektumoknak megvannak a szükséges mezői."""
        interfaces = get_local_interfaces()
        iface = interfaces[0]

        assert hasattr(iface, "name")
        assert hasattr(iface, "ipv4_address")
        assert hasattr(iface, "ipv4_netmask")
        assert hasattr(iface, "mac_address")
        assert hasattr(iface, "is_up")

    def test_excludes_loopback_by_default(self, mock_psutil_interfaces):
        """Loopback alapértelmezetten kizárva."""
        interfaces = get_local_interfaces(include_loopback=False)

        names = [i.name for i in interfaces]
        assert "lo" not in names

    def test_includes_loopback_when_requested(self, mock_psutil_interfaces_with_lo):
        """Loopback visszaadása ha kérik."""
        interfaces = get_local_interfaces(include_loopback=True)

        names = [i.name for i in interfaces]
        assert "lo" in names


class TestGetInterfaceByName:
    """get_interface_by_name függvény tesztjei."""

    def test_returns_correct_interface(self, mock_psutil_interfaces):
        """Helyes interfész visszaadása név alapján."""
        iface = get_interface_by_name("eth0")

        assert iface is not None
        assert iface.name == "eth0"

    def test_returns_none_for_nonexistent(self, mock_psutil_interfaces):
        """None visszaadása ha az interfész nem létezik."""
        iface = get_interface_by_name("nonexistent0")

        assert iface is None


class TestGetDefaultGateway:
    """get_default_gateway függvény tesztjei."""

    def test_returns_gateway_ip(self, mock_psutil_interfaces):
        """Gateway IP visszaadása."""
        gateway = get_default_gateway()

        # A mock alapján: 192.168.1.1
        assert gateway is not None
        assert gateway.endswith(".1")  # Tipikus gateway


class TestGetActiveConnections:
    """get_active_connections függvény tesztjei."""

    def test_returns_connection_list(self, mock_psutil_connections):
        """Kapcsolat lista visszaadása."""
        connections = get_active_connections()

        assert isinstance(connections, list)

    def test_connection_has_required_fields(self, mock_psutil_connections):
        """Kapcsolat objektumoknak megvannak a szükséges mezői."""
        connections = get_active_connections()

        if connections:
            conn = connections[0]
            assert hasattr(conn, "protocol")
            assert hasattr(conn, "local_address")
            assert hasattr(conn, "local_port")
            assert hasattr(conn, "status")

    def test_filters_listening_only(self, mock_psutil_connections):
        """LISTEN kapcsolatok szűrése."""
        all_conn = get_active_connections(include_listening=True)
        no_listen = get_active_connections(include_listening=False)

        listen_count_all = sum(1 for c in all_conn if c.status == "LISTEN")
        listen_count_filtered = sum(1 for c in no_listen if c.status == "LISTEN")

        # Szűrés után nincs LISTEN
        assert listen_count_filtered == 0


class TestGetListeningPorts:
    """get_listening_ports függvény tesztjei."""

    def test_returns_only_listening(self, mock_psutil_connections):
        """Csak LISTEN kapcsolatok visszaadása."""
        listening = get_listening_ports()

        for conn in listening:
            assert conn.status == "LISTEN"


class TestGetInterfaceIoCounters:
    """get_interface_io_counters függvény tesztjei."""

    def test_returns_counters_dict(self, mock_psutil_io_counters):
        """Számláló dictionary visszaadása."""
        counters = get_interface_io_counters()

        assert isinstance(counters, dict)
        assert "bytes_sent" in counters
        assert "bytes_recv" in counters

    def test_interface_specific_counters(self, mock_psutil_io_counters):
        """Specifikus interfész számlálói."""
        counters = get_interface_io_counters("eth0")

        assert isinstance(counters, dict)

    def test_nonexistent_interface_returns_empty(self, mock_psutil_io_counters):
        """Nem létező interfész üres dict-et ad."""
        counters = get_interface_io_counters("nonexistent0")

        assert counters == {}


class TestGetHostname:
    """get_hostname függvény tesztjei."""

    def test_returns_string(self, mock_socket_hostname):
        """String típusú hostname visszaadása."""
        hostname = get_hostname()

        assert isinstance(hostname, str)
        assert len(hostname) > 0


class TestGetFqdn:
    """get_fqdn függvény tesztjei."""

    def test_returns_fqdn(self, mock_socket_fqdn):
        """FQDN visszaadása."""
        fqdn = get_fqdn()

        assert isinstance(fqdn, str)


class TestResolveHostname:
    """resolve_hostname függvény tesztjei."""

    def test_resolves_valid_hostname(self, mock_socket_resolve):
        """Érvényes hostname feloldása."""
        ip = resolve_hostname("example.com")

        assert ip == "93.184.216.34"

    def test_returns_none_for_invalid(self, mock_socket_resolve_fail):
        """None visszaadása érvénytelen hostname-re."""
        ip = resolve_hostname("nonexistent.invalid")

        assert ip is None


class TestReverseResolve:
    """reverse_resolve függvény tesztjei."""

    def test_resolves_valid_ip(self, mock_socket_reverse):
        """Érvényes IP feloldása hostname-re."""
        hostname = reverse_resolve("8.8.8.8")

        assert hostname == "dns.google"

    def test_returns_none_for_invalid(self, mock_socket_reverse_fail):
        """None visszaadása ha nem sikerül a feloldás."""
        hostname = reverse_resolve("192.168.1.1")

        assert hostname is None


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_psutil_interfaces():
    """Mock psutil interfész lekérdezéshez."""
    with patch("network_health_checker.network_tools.network_info.psutil.net_if_addrs") as mock_addrs:
        with patch("network_health_checker.network_tools.network_info.psutil.net_if_stats") as mock_stats:
            # Mock interfész címek
            mock_addr_ipv4 = MagicMock()
            mock_addr_ipv4.family = socket.AF_INET
            mock_addr_ipv4.address = "192.168.1.100"
            mock_addr_ipv4.netmask = "255.255.255.0"

            mock_addr_mac = MagicMock()
            mock_addr_mac.family = 17  # AF_LINK
            mock_addr_mac.address = "00:11:22:33:44:55"

            mock_addrs.return_value = {"eth0": [mock_addr_ipv4, mock_addr_mac]}

            # Mock interfész státusz
            mock_stat = MagicMock()
            mock_stat.isup = True
            mock_stat.speed = 1000
            mock_stat.mtu = 1500
            mock_stats.return_value = {"eth0": mock_stat}

            yield mock_addrs


@pytest.fixture
def mock_psutil_interfaces_with_lo():
    """Mock psutil interfész lekérdezéshez loopback-kel."""
    with patch("network_health_checker.network_tools.network_info.psutil.net_if_addrs") as mock_addrs:
        with patch("network_health_checker.network_tools.network_info.psutil.net_if_stats") as mock_stats:
            mock_addr_eth = MagicMock()
            mock_addr_eth.family = socket.AF_INET
            mock_addr_eth.address = "192.168.1.100"
            mock_addr_eth.netmask = "255.255.255.0"

            mock_addr_lo = MagicMock()
            mock_addr_lo.family = socket.AF_INET
            mock_addr_lo.address = "127.0.0.1"
            mock_addr_lo.netmask = "255.0.0.0"

            mock_addrs.return_value = {
                "eth0": [mock_addr_eth],
                "lo": [mock_addr_lo],
            }

            mock_stat = MagicMock()
            mock_stat.isup = True
            mock_stat.speed = 1000
            mock_stat.mtu = 1500
            mock_stats.return_value = {
                "eth0": mock_stat,
                "lo": mock_stat,
            }

            yield mock_addrs


@pytest.fixture
def mock_psutil_connections():
    """Mock psutil kapcsolat lekérdezéshez."""
    with patch("network_health_checker.network_tools.network_info.psutil.net_connections") as mock_conn:
        with patch("network_health_checker.network_tools.network_info.psutil.Process"):
            # Mock kapcsolatok
            conn_listen = MagicMock()
            conn_listen.type = socket.SOCK_STREAM
            conn_listen.laddr = MagicMock(ip="0.0.0.0", port=80)
            conn_listen.raddr = None
            conn_listen.status = "LISTEN"
            conn_listen.pid = 1234

            conn_established = MagicMock()
            conn_established.type = socket.SOCK_STREAM
            conn_established.laddr = MagicMock(ip="192.168.1.100", port=54321)
            conn_established.raddr = MagicMock(ip="93.184.216.34", port=443)
            conn_established.status = "ESTABLISHED"
            conn_established.pid = 5678

            mock_conn.return_value = [conn_listen, conn_established]

            yield mock_conn


@pytest.fixture
def mock_psutil_io_counters():
    """Mock psutil I/O számláló lekérdezéshez."""
    with patch("network_health_checker.network_tools.network_info.psutil.net_io_counters") as mock_io:
        mock_counters = MagicMock()
        mock_counters.bytes_sent = 1000000
        mock_counters.bytes_recv = 2000000
        mock_counters.packets_sent = 1000
        mock_counters.packets_recv = 2000
        mock_counters.errin = 0
        mock_counters.errout = 0
        mock_counters.dropin = 0
        mock_counters.dropout = 0

        def side_effect(pernic=False):
            if pernic:
                return {"eth0": mock_counters}
            return mock_counters

        mock_io.side_effect = side_effect

        yield mock_io


@pytest.fixture
def mock_socket_hostname():
    """Mock socket hostname-hez."""
    with patch("network_health_checker.network_tools.network_info.socket.gethostname") as mock_hostname:
        mock_hostname.return_value = "testhost"
        yield mock_hostname


@pytest.fixture
def mock_socket_fqdn():
    """Mock socket FQDN-hez."""
    with patch("network_health_checker.network_tools.network_info.socket.getfqdn") as mock_fqdn:
        mock_fqdn.return_value = "testhost.example.com"
        yield mock_fqdn


@pytest.fixture
def mock_socket_resolve():
    """Mock socket hostname feloldáshoz."""
    with patch("network_health_checker.network_tools.network_info.socket.gethostbyname") as mock_resolve:
        mock_resolve.return_value = "93.184.216.34"
        yield mock_resolve


@pytest.fixture
def mock_socket_resolve_fail():
    """Mock sikertelen hostname feloldáshoz."""
    with patch("network_health_checker.network_tools.network_info.socket.gethostbyname") as mock_resolve:
        mock_resolve.side_effect = socket.gaierror(8, "Name not resolved")
        yield mock_resolve


@pytest.fixture
def mock_socket_reverse():
    """Mock reverse DNS lookup-hoz."""
    with patch("network_health_checker.network_tools.network_info.socket.gethostbyaddr") as mock_reverse:
        mock_reverse.return_value = ("dns.google", [], ["8.8.8.8"])
        yield mock_reverse


@pytest.fixture
def mock_socket_reverse_fail():
    """Mock sikertelen reverse lookup-hoz."""
    with patch("network_health_checker.network_tools.network_info.socket.gethostbyaddr") as mock_reverse:
        mock_reverse.side_effect = socket.herror(1, "Host not found")
        yield mock_reverse
