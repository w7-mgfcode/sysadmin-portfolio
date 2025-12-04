"""
DNS Lookup tesztek.

Tesztek a DNS lekérdezési funkciókhoz.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Projekt gyökér hozzáadása a path-hoz
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_health_checker.network_tools.dns_lookup import (
    get_mx_records,
    get_nameservers,
    lookup_all_records,
    lookup_dns,
    reverse_lookup,
)


class TestLookupDns:
    """lookup_dns függvény tesztjei."""

    def test_a_record_lookup_success(self, mock_dns_resolver):
        """Sikeres A rekord lekérdezés."""
        result = lookup_dns("example.com", "A")

        assert result.query == "example.com"
        assert result.record_type == "A"
        assert result.values == ["93.184.216.34"]
        assert result.ttl == 3600

    def test_mx_record_lookup_success(self, mock_dns_resolver_mx):
        """Sikeres MX rekord lekérdezés."""
        result = lookup_dns("example.com", "MX")

        assert result.query == "example.com"
        assert result.record_type == "MX"
        assert len(result.values) == 1
        # MX rekord formátum: "priority server"
        assert "10" in result.values[0]
        assert "mail.example.com" in result.values[0]

    def test_invalid_record_type_raises_error(self):
        """Érvénytelen rekord típus hibát dob."""
        with pytest.raises(ValueError, match="Invalid record type"):
            lookup_dns("example.com", "INVALID")

    def test_case_insensitive_record_type(self, mock_dns_resolver):
        """Rekord típus case-insensitive."""
        result = lookup_dns("example.com", "a")  # kisbetű

        assert result.record_type == "A"  # Nagybetűvé alakul

    def test_nonexistent_domain_returns_empty(self, mock_dns_nxdomain):
        """Nem létező domain üres eredményt ad."""
        result = lookup_dns("nonexistent.invalid", "A")

        assert result.values == []
        assert result.ttl is None

    def test_no_records_returns_empty(self, mock_dns_no_answer):
        """Ha nincs rekord, üres eredményt ad."""
        result = lookup_dns("example.com", "AAAA")

        assert result.values == []

    def test_timeout_returns_empty(self, mock_dns_timeout):
        """Timeout esetén üres eredményt ad."""
        result = lookup_dns("example.com", "A", timeout=0.1)

        assert result.values == []

    def test_custom_nameserver(self, mock_dns_resolver):
        """Egyedi nameserver használata."""
        result = lookup_dns("example.com", "A", nameserver="8.8.8.8")

        assert result.values == ["93.184.216.34"]


class TestLookupAllRecords:
    """lookup_all_records függvény tesztjei."""

    def test_returns_multiple_record_types(self, mock_dns_resolver):
        """Több rekord típust ad vissza."""
        results = lookup_all_records("example.com")

        # Legalább egy eredményt kapunk (A rekord)
        assert len(results) >= 1
        record_types = [r.record_type for r in results]
        assert "A" in record_types

    def test_excludes_empty_results(self, mock_dns_partial):
        """Üres eredmények nem szerepelnek."""
        results = lookup_all_records("example.com")

        # Minden visszaadott eredménynek van értéke
        for result in results:
            assert len(result.values) > 0


class TestReverseLookup:
    """reverse_lookup függvény tesztjei."""

    def test_reverse_lookup_success(self, mock_dns_ptr):
        """Sikeres reverse lookup."""
        result = reverse_lookup("8.8.8.8")

        assert result.record_type == "PTR"
        assert len(result.values) > 0

    def test_invalid_ip_returns_empty(self):
        """Érvénytelen IP üres eredményt ad."""
        result = reverse_lookup("invalid")

        assert result.values == []


class TestGetNameservers:
    """get_nameservers függvény tesztjei."""

    def test_returns_ns_list(self, mock_dns_ns):
        """NS rekordok listáját adja vissza."""
        ns_list = get_nameservers("example.com")

        assert isinstance(ns_list, list)
        assert len(ns_list) > 0
        assert "ns1.example.com." in ns_list


class TestGetMxRecords:
    """get_mx_records függvény tesztjei."""

    def test_returns_mx_list(self, mock_dns_resolver_mx):
        """MX rekordok listáját adja vissza."""
        mx_list = get_mx_records("example.com")

        assert isinstance(mx_list, list)
        assert len(mx_list) > 0


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_dns_resolver():
    """Mock a sikeres DNS A rekord lekérdezéshez."""
    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        # Mock resolver instance
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance

        # Mock answer
        mock_answer = MagicMock()
        mock_rdata = MagicMock()
        mock_rdata.__str__ = MagicMock(return_value="93.184.216.34")

        # rrset TTL
        mock_rrset = MagicMock()
        mock_rrset.ttl = 3600
        mock_answer.rrset = mock_rrset
        mock_answer.__iter__ = MagicMock(return_value=iter([mock_rdata]))

        resolver_instance.resolve.return_value = mock_answer

        yield mock_resolver


@pytest.fixture
def mock_dns_resolver_mx():
    """Mock MX rekord lekérdezéshez."""
    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance

        mock_answer = MagicMock()
        mock_rdata = MagicMock()
        mock_rdata.preference = 10
        mock_rdata.exchange = "mail.example.com."

        mock_rrset = MagicMock()
        mock_rrset.ttl = 3600
        mock_answer.rrset = mock_rrset
        mock_answer.__iter__ = MagicMock(return_value=iter([mock_rdata]))

        resolver_instance.resolve.return_value = mock_answer

        yield mock_resolver


@pytest.fixture
def mock_dns_nxdomain():
    """Mock NXDOMAIN válaszhoz."""
    import dns.resolver

    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        resolver_instance.resolve.side_effect = dns.resolver.NXDOMAIN()

        yield mock_resolver


@pytest.fixture
def mock_dns_no_answer():
    """Mock NoAnswer válaszhoz."""
    import dns.resolver

    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        resolver_instance.resolve.side_effect = dns.resolver.NoAnswer()

        yield mock_resolver


@pytest.fixture
def mock_dns_timeout():
    """Mock timeout-hoz."""
    import dns.exception

    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance
        resolver_instance.resolve.side_effect = dns.exception.Timeout()

        yield mock_resolver


@pytest.fixture
def mock_dns_partial():
    """Mock részleges eredményekhez."""
    import dns.resolver

    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance

        def resolve_side_effect(domain, record_type):
            if record_type == "A":
                mock_answer = MagicMock()
                mock_rdata = MagicMock()
                mock_rdata.__str__ = MagicMock(return_value="93.184.216.34")
                mock_rrset = MagicMock()
                mock_rrset.ttl = 3600
                mock_answer.rrset = mock_rrset
                mock_answer.__iter__ = MagicMock(return_value=iter([mock_rdata]))
                return mock_answer
            raise dns.resolver.NoAnswer()

        resolver_instance.resolve.side_effect = resolve_side_effect

        yield mock_resolver


@pytest.fixture
def mock_dns_ptr():
    """Mock PTR rekord lekérdezéshez."""
    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        with patch("network_health_checker.network_tools.dns_lookup.dns.reversename.from_address") as mock_reverse:
            mock_reverse.return_value = "8.8.8.8.in-addr.arpa."

            resolver_instance = MagicMock()
            mock_resolver.return_value = resolver_instance

            mock_answer = MagicMock()
            mock_rdata = MagicMock()
            mock_rdata.__str__ = MagicMock(return_value="dns.google.")

            mock_rrset = MagicMock()
            mock_rrset.ttl = 3600
            mock_answer.rrset = mock_rrset
            mock_answer.__iter__ = MagicMock(return_value=iter([mock_rdata]))

            resolver_instance.resolve.return_value = mock_answer

            yield mock_resolver


@pytest.fixture
def mock_dns_ns():
    """Mock NS rekord lekérdezéshez."""
    with patch("network_health_checker.network_tools.dns_lookup.dns.resolver.Resolver") as mock_resolver:
        resolver_instance = MagicMock()
        mock_resolver.return_value = resolver_instance

        mock_answer = MagicMock()
        mock_rdata1 = MagicMock()
        mock_rdata1.__str__ = MagicMock(return_value="ns1.example.com.")
        mock_rdata2 = MagicMock()
        mock_rdata2.__str__ = MagicMock(return_value="ns2.example.com.")

        mock_rrset = MagicMock()
        mock_rrset.ttl = 3600
        mock_answer.rrset = mock_rrset
        mock_answer.__iter__ = MagicMock(return_value=iter([mock_rdata1, mock_rdata2]))

        resolver_instance.resolve.return_value = mock_answer

        yield mock_resolver
