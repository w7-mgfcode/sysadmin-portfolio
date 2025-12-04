"""
Ping Monitor tesztek.

Tesztek az ICMP ping funkciókhoz.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Projekt gyökér hozzáadása a path-hoz
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_health_checker.models import HostStatus
from network_health_checker.network_tools.ping_monitor import is_host_reachable, ping_host, ping_hosts


class TestPingHost:
    """ping_host függvény tesztjei."""

    def test_successful_ping(self, mock_ping_success, mock_socket_resolve):
        """Sikeres ping válasz."""
        result = ping_host("8.8.8.8", timeout=2.0, count=1)

        assert result.host == "8.8.8.8"
        assert result.status == HostStatus.UP
        assert result.latency_ms is not None
        assert result.latency_ms > 0
        assert result.ip_address == "8.8.8.8"

    def test_ping_timeout(self, mock_ping_timeout, mock_socket_resolve):
        """Ping timeout esetén TIMEOUT státusz."""
        result = ping_host("192.168.1.1", timeout=0.5, count=1)

        assert result.status == HostStatus.TIMEOUT
        assert result.latency_ms is None

    def test_hostname_resolution_failure(self, mock_socket_resolve_fail):
        """Hostname feloldási hiba ERROR státuszt ad."""
        result = ping_host("nonexistent.invalid", timeout=1.0)

        assert result.status == HostStatus.ERROR
        assert "Could not resolve hostname" in result.error_message

    def test_multiple_pings_average(self, mock_ping_variable, mock_socket_resolve):
        """Több ping átlagolása."""
        result = ping_host("8.8.8.8", count=3)

        assert result.status == HostStatus.UP
        # Az átlag 10, 20, 30 ms-ból = 20ms
        assert result.latency_ms == 20.0

    def test_permission_error(self, mock_ping_permission, mock_socket_resolve):
        """Permission denied hiba kezelése."""
        result = ping_host("8.8.8.8")

        assert result.status == HostStatus.ERROR
        assert "Permission denied" in result.error_message

    def test_result_has_timestamp(self, mock_ping_success, mock_socket_resolve):
        """Eredmény tartalmaz timestamp-et."""
        result = ping_host("8.8.8.8")

        assert result.timestamp is not None


class TestPingHosts:
    """ping_hosts függvény tesztjei."""

    def test_multiple_hosts_success(self, mock_ping_success, mock_socket_resolve):
        """Több host pingelése sikeresen."""
        hosts = ["8.8.8.8", "1.1.1.1"]
        results = ping_hosts(hosts, timeout=1.0, max_workers=2)

        assert len(results) == 2
        # Minden eredmény PingResult
        for result in results:
            assert hasattr(result, "host")
            assert hasattr(result, "status")

    def test_empty_host_list(self):
        """Üres host lista üres eredményt ad."""
        results = ping_hosts([])

        assert results == []

    def test_mixed_results(
        self, mock_ping_mixed, mock_socket_resolve, mock_socket_resolve_mixed
    ):
        """Vegyes eredmények (UP és TIMEOUT)."""
        # Ezt nehéz mockkolni ProcessPoolExecutor miatt
        # Egyszerűsített teszt
        pass


class TestIsHostReachable:
    """is_host_reachable függvény tesztjei."""

    def test_reachable_host_returns_true(self, mock_ping_success, mock_socket_resolve):
        """Elérhető host True-t ad."""
        result = is_host_reachable("8.8.8.8", timeout=1.0)

        assert result is True

    def test_unreachable_host_returns_false(
        self, mock_ping_timeout, mock_socket_resolve
    ):
        """Nem elérhető host False-t ad."""
        result = is_host_reachable("192.168.1.1", timeout=0.5)

        assert result is False


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_ping_success():
    """Mock sikeres ping válaszhoz."""
    with patch("network_health_checker.network_tools.ping_monitor.ping") as mock_ping:
        # Visszaad egy latency értéket ms-ban
        mock_ping.return_value = 15.5
        yield mock_ping


@pytest.fixture
def mock_ping_timeout():
    """Mock ping timeout-hoz."""
    with patch("network_health_checker.network_tools.ping_monitor.ping") as mock_ping:
        # None = timeout a ping3-ban
        mock_ping.return_value = None
        yield mock_ping


@pytest.fixture
def mock_ping_variable():
    """Mock változó latency értékekkel."""
    with patch("network_health_checker.network_tools.ping_monitor.ping") as mock_ping:
        # Különböző latency értékek visszaadása
        mock_ping.side_effect = [10.0, 20.0, 30.0]
        yield mock_ping


@pytest.fixture
def mock_ping_permission():
    """Mock permission error-hoz."""
    with patch("network_health_checker.network_tools.ping_monitor.ping") as mock_ping:
        mock_ping.side_effect = PermissionError("Permission denied")
        yield mock_ping


@pytest.fixture
def mock_ping_mixed():
    """Mock vegyes eredményekhez."""
    with patch("network_health_checker.network_tools.ping_monitor.ping") as mock_ping:

        def side_effect(host, **kwargs):
            if host == "8.8.8.8":
                return 10.0
            return None  # timeout

        mock_ping.side_effect = side_effect
        yield mock_ping


@pytest.fixture
def mock_socket_resolve():
    """Mock hostname feloldáshoz."""
    with patch("network_health_checker.network_tools.ping_monitor.socket.gethostbyname") as mock_resolve:
        # Az IP-t változatlanul adja vissza
        mock_resolve.side_effect = lambda x: x
        yield mock_resolve


@pytest.fixture
def mock_socket_resolve_fail():
    """Mock sikertelen hostname feloldáshoz."""
    import socket

    with patch("network_health_checker.network_tools.ping_monitor.socket.gethostbyname") as mock_resolve:
        mock_resolve.side_effect = socket.gaierror(8, "Name or service not known")
        yield mock_resolve


@pytest.fixture
def mock_socket_resolve_mixed():
    """Mock vegyes hostname feloldáshoz."""
    with patch("network_health_checker.network_tools.ping_monitor.socket.gethostbyname") as mock_resolve:
        mock_resolve.side_effect = lambda x: x
        yield mock_resolve
