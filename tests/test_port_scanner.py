"""
Port Scanner tesztek.

Tesztek a TCP port szkennelési funkciókhoz.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Projekt gyökér hozzáadása a path-hoz
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_health_checker.network_tools.port_scanner import (
    _parse_ports,
    scan_common_ports,
    scan_port,
    scan_ports,
)


class TestScanPort:
    """scan_port függvény tesztjei."""

    def test_open_port(self, mock_socket_open):
        """Nyitott port detektálása."""
        result = scan_port("192.168.1.1", 80, timeout=1.0)

        assert result.host == "192.168.1.1"
        assert result.port == 80
        assert result.is_open is True
        assert result.service_name == "http"
        assert result.latency_ms is not None

    def test_closed_port(self, mock_socket_closed):
        """Zárt port detektálása."""
        result = scan_port("192.168.1.1", 8888, timeout=1.0)

        assert result.is_open is False
        assert result.latency_ms is None

    def test_port_with_banner(self, mock_socket_with_banner):
        """Banner információ lekérése."""
        result = scan_port("192.168.1.1", 22, timeout=1.0, grab_banner=True)

        assert result.is_open is True
        assert result.banner == "SSH-2.0-OpenSSH_8.0"

    def test_timeout_handling(self, mock_socket_timeout):
        """Timeout kezelése zárt portként."""
        result = scan_port("192.168.1.1", 12345, timeout=0.5)

        assert result.is_open is False

    def test_hostname_resolution_error(self, mock_socket_gaierror):
        """Hostname feloldási hiba kezelése."""
        result = scan_port("invalid.host", 80)

        assert result.is_open is False

    def test_known_service_name(self, mock_socket_open):
        """Ismert port szolgáltatás neve."""
        result = scan_port("192.168.1.1", 443)

        assert result.service_name == "https"

    def test_unknown_service_name(self, mock_socket_open):
        """Ismeretlen port esetén None szolgáltatás."""
        result = scan_port("192.168.1.1", 54321)

        assert result.service_name is None


class TestScanPorts:
    """scan_ports függvény tesztjei."""

    def test_multiple_ports_list(self, mock_socket_mixed):
        """Több port szkennelése listából."""
        results = scan_ports("192.168.1.1", [22, 80, 443], timeout=1.0)

        assert len(results) == 3
        # Eredmények port szám szerint rendezve
        assert results[0].port <= results[1].port <= results[2].port

    def test_port_string_format(self, mock_socket_mixed):
        """Port string formátum feldolgozása."""
        results = scan_ports("192.168.1.1", "22,80,443")

        assert len(results) == 3

    def test_port_range_string(self, mock_socket_mixed):
        """Port tartomány string feldolgozása."""
        results = scan_ports("192.168.1.1", "20-22")

        assert len(results) == 3
        ports = [r.port for r in results]
        assert 20 in ports
        assert 21 in ports
        assert 22 in ports

    def test_mixed_port_string(self, mock_socket_mixed):
        """Vegyes port string (egyedi + tartomány)."""
        results = scan_ports("192.168.1.1", "22,80-82,443")

        assert len(results) == 5

    def test_returns_sorted_results(self, mock_socket_mixed):
        """Eredmények port szám szerint rendezettek."""
        results = scan_ports("192.168.1.1", "443,22,80")

        ports = [r.port for r in results]
        assert ports == sorted(ports)


class TestParsePorts:
    """_parse_ports belső függvény tesztjei."""

    def test_single_port(self):
        """Egyetlen port feldolgozása."""
        ports = _parse_ports("80")
        assert ports == [80]

    def test_multiple_ports(self):
        """Több port feldolgozása."""
        ports = _parse_ports("22,80,443")
        assert ports == [22, 80, 443]

    def test_port_range(self):
        """Port tartomány feldolgozása."""
        ports = _parse_ports("20-25")
        assert ports == [20, 21, 22, 23, 24, 25]

    def test_mixed_format(self):
        """Vegyes formátum feldolgozása."""
        ports = _parse_ports("22,80-82,443")
        assert ports == [22, 80, 81, 82, 443]

    def test_removes_duplicates(self):
        """Duplikátumok eltávolítása."""
        ports = _parse_ports("22,22,80")
        assert ports == [22, 80]

    def test_returns_sorted(self):
        """Rendezett lista visszaadása."""
        ports = _parse_ports("443,22,80")
        assert ports == [22, 80, 443]

    def test_with_spaces(self):
        """Szóközök kezelése."""
        ports = _parse_ports("22, 80, 443")
        assert ports == [22, 80, 443]


class TestScanCommonPorts:
    """scan_common_ports függvény tesztjei."""

    def test_scans_predefined_ports(self, mock_socket_mixed):
        """Előre definiált portok szkennelése."""
        results = scan_common_ports("192.168.1.1", timeout=1.0)

        # Tartalmazza a gyakori portokat
        ports = [r.port for r in results]
        assert 22 in ports  # SSH
        assert 80 in ports  # HTTP
        assert 443 in ports  # HTTPS

    def test_returns_correct_count(self, mock_socket_mixed):
        """Helyes számú eredmény."""
        results = scan_common_ports("192.168.1.1")

        # A COMMON_PORTS listában 17 port van
        assert len(results) == 17


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_socket_open():
    """Mock nyitott porthoz."""
    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        # connect_ex visszatér 0-val (success)
        mock_sock.connect_ex.return_value = 0
        yield mock_socket_class


@pytest.fixture
def mock_socket_closed():
    """Mock zárt porthoz."""
    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        # connect_ex visszatér nem 0-val (connection refused)
        mock_sock.connect_ex.return_value = 111  # ECONNREFUSED
        yield mock_socket_class


@pytest.fixture
def mock_socket_with_banner():
    """Mock banner-es porthoz."""
    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0
        # Banner válasz
        mock_sock.recv.return_value = b"SSH-2.0-OpenSSH_8.0\r\n"
        yield mock_socket_class


@pytest.fixture
def mock_socket_timeout():
    """Mock timeout-hoz."""
    import socket

    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect_ex.side_effect = socket.timeout()
        yield mock_socket_class


@pytest.fixture
def mock_socket_gaierror():
    """Mock hostname feloldási hibához."""
    import socket

    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock
        mock_sock.connect_ex.side_effect = socket.gaierror(8, "Name not resolved")
        yield mock_socket_class


@pytest.fixture
def mock_socket_mixed():
    """Mock vegyes eredményekhez (nyitott és zárt portok)."""
    with patch("network_health_checker.network_tools.port_scanner.socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        # Bizonyos portok nyitottak, mások zártak
        open_ports = {22, 80, 443}

        def connect_ex_side_effect(address):
            host, port = address
            return 0 if port in open_ports else 111

        mock_sock.connect_ex.side_effect = connect_ex_side_effect
        yield mock_socket_class
