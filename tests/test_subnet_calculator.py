"""
Subnet Calculator tesztek.

Tesztek az IP és alhálózat számítási funkciókhoz.
"""

import sys
from pathlib import Path

import pytest

# Projekt gyökér hozzáadása a path-hoz
sys.path.insert(0, str(Path(__file__).parent.parent))

from network_health_checker.network_tools.subnet_calculator import (
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


class TestCalculateSubnet:
    """calculate_subnet függvény tesztjei."""

    def test_standard_class_c_network(self):
        """Standard /24 hálózat helyes számítása."""
        info = calculate_subnet("192.168.1.0/24")

        assert info.network == "192.168.1.0"
        assert info.netmask == "255.255.255.0"
        assert info.broadcast == "192.168.1.255"
        assert info.first_host == "192.168.1.1"
        assert info.last_host == "192.168.1.254"
        assert info.total_hosts == 254
        assert info.cidr == 24

    def test_small_subnet(self):
        """Kis /30 alhálózat (point-to-point link)."""
        info = calculate_subnet("10.0.0.0/30")

        assert info.network == "10.0.0.0"
        assert info.broadcast == "10.0.0.3"
        assert info.first_host == "10.0.0.1"
        assert info.last_host == "10.0.0.2"
        assert info.total_hosts == 2

    def test_large_network(self):
        """Nagy /8 hálózat."""
        info = calculate_subnet("10.0.0.0/8")

        assert info.network == "10.0.0.0"
        assert info.netmask == "255.0.0.0"
        assert info.total_hosts == 16777214  # 2^24 - 2

    def test_host_in_middle_of_subnet(self):
        """CIDR nem hálózati címmel (strict=False működik)."""
        info = calculate_subnet("192.168.1.100/24")

        # A network cím automatikusan normalizálódik
        assert info.network == "192.168.1.0"

    def test_invalid_cidr_raises_error(self):
        """Érvénytelen CIDR formátum hibát dob."""
        with pytest.raises(ValueError, match="Invalid CIDR"):
            calculate_subnet("invalid")

    def test_invalid_ip_raises_error(self):
        """Érvénytelen IP cím hibát dob."""
        with pytest.raises(ValueError, match="Invalid CIDR"):
            calculate_subnet("999.999.999.999/24")

    def test_slash_31_network(self):
        """/31 hálózat speciális eset (RFC 3021)."""
        info = calculate_subnet("10.0.0.0/31")

        # /31 esetén nincs broadcast, mindkét cím használható
        assert info.total_hosts == 2

    def test_slash_32_host_route(self):
        """/32 host route."""
        info = calculate_subnet("192.168.1.1/32")

        assert info.network == "192.168.1.1"
        assert info.total_hosts == 1


class TestIpInSubnet:
    """ip_in_subnet függvény tesztjei."""

    def test_ip_in_subnet_true(self):
        """IP benne van az alhálózatban."""
        assert ip_in_subnet("192.168.1.100", "192.168.1.0/24") is True

    def test_ip_not_in_subnet(self):
        """IP nincs benne az alhálózatban."""
        assert ip_in_subnet("192.168.2.100", "192.168.1.0/24") is False

    def test_network_address_in_subnet(self):
        """Hálózati cím benne van az alhálózatban."""
        assert ip_in_subnet("192.168.1.0", "192.168.1.0/24") is True

    def test_broadcast_address_in_subnet(self):
        """Broadcast cím benne van az alhálózatban."""
        assert ip_in_subnet("192.168.1.255", "192.168.1.0/24") is True

    def test_invalid_ip_returns_false(self):
        """Érvénytelen IP False-t ad vissza."""
        assert ip_in_subnet("invalid", "192.168.1.0/24") is False

    def test_invalid_cidr_returns_false(self):
        """Érvénytelen CIDR False-t ad vissza."""
        assert ip_in_subnet("192.168.1.100", "invalid") is False


class TestGetSubnetHosts:
    """get_subnet_hosts függvény tesztjei."""

    def test_small_subnet_all_hosts(self):
        """Kis alhálózat összes hostja."""
        hosts = get_subnet_hosts("192.168.1.0/30")

        assert len(hosts) == 2
        assert "192.168.1.1" in hosts
        assert "192.168.1.2" in hosts

    def test_with_limit(self):
        """Limitált host lista."""
        hosts = get_subnet_hosts("192.168.1.0/24", limit=10)

        assert len(hosts) == 10
        assert hosts[0] == "192.168.1.1"

    def test_invalid_cidr_returns_empty(self):
        """Érvénytelen CIDR üres listát ad."""
        hosts = get_subnet_hosts("invalid")

        assert hosts == []


class TestIterateSubnetHosts:
    """iterate_subnet_hosts függvény tesztjei."""

    def test_iterate_small_subnet(self):
        """Kis alhálózat iterálása."""
        hosts = list(iterate_subnet_hosts("192.168.1.0/30"))

        assert len(hosts) == 2
        assert hosts == ["192.168.1.1", "192.168.1.2"]

    def test_invalid_cidr_empty_generator(self):
        """Érvénytelen CIDR üres generátor."""
        hosts = list(iterate_subnet_hosts("invalid"))

        assert hosts == []


class TestNetmaskToCidr:
    """netmask_to_cidr függvény tesztjei."""

    def test_class_c_mask(self):
        """Class C maszk konvertálása."""
        assert netmask_to_cidr("255.255.255.0") == 24

    def test_class_b_mask(self):
        """Class B maszk konvertálása."""
        assert netmask_to_cidr("255.255.0.0") == 16

    def test_class_a_mask(self):
        """Class A maszk konvertálása."""
        assert netmask_to_cidr("255.0.0.0") == 8

    def test_small_subnet_mask(self):
        """/30 maszk konvertálása."""
        assert netmask_to_cidr("255.255.255.252") == 30

    def test_invalid_mask_raises_error(self):
        """Érvénytelen maszk hibát dob."""
        with pytest.raises(ValueError, match="Invalid netmask"):
            netmask_to_cidr("invalid")


class TestCidrToNetmask:
    """cidr_to_netmask függvény tesztjei."""

    def test_cidr_24(self):
        """/24 konvertálása."""
        assert cidr_to_netmask(24) == "255.255.255.0"

    def test_cidr_16(self):
        """/16 konvertálása."""
        assert cidr_to_netmask(16) == "255.255.0.0"

    def test_cidr_8(self):
        """/8 konvertálása."""
        assert cidr_to_netmask(8) == "255.0.0.0"

    def test_cidr_0(self):
        """/0 konvertálása (default route)."""
        assert cidr_to_netmask(0) == "0.0.0.0"

    def test_cidr_32(self):
        """/32 konvertálása (host route)."""
        assert cidr_to_netmask(32) == "255.255.255.255"

    def test_invalid_cidr_raises_error(self):
        """Érvénytelen CIDR érték hibát dob."""
        with pytest.raises(ValueError, match="Invalid CIDR prefix"):
            cidr_to_netmask(33)

        with pytest.raises(ValueError, match="Invalid CIDR prefix"):
            cidr_to_netmask(-1)


class TestSplitSubnet:
    """split_subnet függvény tesztjei."""

    def test_split_24_to_26(self):
        """/24 felosztása /26 alhálózatokra."""
        subnets = split_subnet("192.168.1.0/24", 26)

        assert len(subnets) == 4
        assert subnets[0].network == "192.168.1.0"
        assert subnets[0].cidr == 26
        assert subnets[1].network == "192.168.1.64"
        assert subnets[2].network == "192.168.1.128"
        assert subnets[3].network == "192.168.1.192"

    def test_split_24_to_25(self):
        """/24 felosztása két /25 alhálózatra."""
        subnets = split_subnet("192.168.1.0/24", 25)

        assert len(subnets) == 2
        assert subnets[0].total_hosts == 126
        assert subnets[1].total_hosts == 126

    def test_invalid_new_prefix_raises_error(self):
        """Kisebb prefix érték hibát dob."""
        with pytest.raises(ValueError, match="New prefix must be larger"):
            split_subnet("192.168.1.0/24", 20)


class TestIsPrivateIp:
    """is_private_ip függvény tesztjei."""

    def test_class_a_private(self):
        """10.x.x.x privát tartomány."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True

    def test_class_b_private(self):
        """172.16-31.x.x privát tartomány."""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True
        # 172.32.x.x már nem privát
        assert is_private_ip("172.32.0.1") is False

    def test_class_c_private(self):
        """192.168.x.x privát tartomány."""
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.255.255") is True

    def test_public_ip(self):
        """Publikus IP cím."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False

    def test_invalid_ip_returns_false(self):
        """Érvénytelen IP False-t ad vissza."""
        assert is_private_ip("invalid") is False


class TestIsValidIp:
    """is_valid_ip függvény tesztjei."""

    def test_valid_ip(self):
        """Érvényes IPv4 címek."""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("0.0.0.0") is True
        assert is_valid_ip("255.255.255.255") is True

    def test_invalid_ip(self):
        """Érvénytelen címek."""
        assert is_valid_ip("invalid") is False
        assert is_valid_ip("256.1.1.1") is False
        assert is_valid_ip("1.1.1") is False
        assert is_valid_ip("") is False
