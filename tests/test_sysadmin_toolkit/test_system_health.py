"""
Tests for system health module.

Tesztek a rendszer egészség modulhoz.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/1-sysadmin-toolkit")

from toolkit.system_health import (
    get_cpu_info,
    get_disk_info,
    get_memory_info,
    get_system_health,
    get_top_processes,
)
from toolkit.models import DiskUsage, ProcessInfo, SystemHealth


class TestGetCPUInfo:
    """Tests for get_cpu_info function."""

    def test_cpu_info_returns_dict(self):
        """Test that cpu_info returns a dictionary."""
        info = get_cpu_info()
        assert isinstance(info, dict)

    def test_cpu_info_has_required_keys(self):
        """Test that cpu_info has required keys."""
        info = get_cpu_info()
        assert "cpu_percent" in info
        assert "cpu_count" in info

    def test_cpu_percent_is_valid(self):
        """Test that CPU percent is between 0 and 100."""
        info = get_cpu_info()
        assert 0 <= info["cpu_percent"] <= 100

    def test_cpu_count_is_positive(self):
        """Test that CPU count is positive."""
        info = get_cpu_info()
        assert info["cpu_count"] > 0


class TestGetMemoryInfo:
    """Tests for get_memory_info function."""

    def test_memory_info_returns_dict(self):
        """Test that memory_info returns a dictionary."""
        info = get_memory_info()
        assert isinstance(info, dict)

    def test_memory_info_has_required_keys(self):
        """Test that memory_info has required keys."""
        info = get_memory_info()
        assert "memory_total_bytes" in info
        assert "memory_used_bytes" in info
        assert "memory_available_bytes" in info
        assert "memory_percent" in info
        assert "swap_total_bytes" in info

    def test_memory_total_is_positive(self):
        """Test that memory total is positive."""
        info = get_memory_info()
        assert info["memory_total_bytes"] > 0

    def test_memory_percent_is_valid(self):
        """Test that memory percent is between 0 and 100."""
        info = get_memory_info()
        assert 0 <= info["memory_percent"] <= 100


class TestGetDiskInfo:
    """Tests for get_disk_info function."""

    def test_disk_info_returns_list(self):
        """Test that disk_info returns a list."""
        disks = get_disk_info()
        assert isinstance(disks, list)

    def test_disk_info_items_are_disk_usage(self):
        """Test that disk_info items are DiskUsage objects."""
        disks = get_disk_info()
        if disks:  # May be empty in some environments
            assert isinstance(disks[0], DiskUsage)

    def test_disk_usage_has_valid_percent(self):
        """Test that disk usage percent is valid."""
        disks = get_disk_info()
        for disk in disks:
            assert 0 <= disk.percent_used <= 100

    def test_exclude_types_filter(self):
        """Test that exclude_types filters correctly."""
        disks_all = get_disk_info(exclude_types=[])
        disks_filtered = get_disk_info(exclude_types=["tmpfs", "devtmpfs"])
        # Filtered list should be same or smaller
        assert len(disks_filtered) <= len(disks_all)


class TestGetTopProcesses:
    """Tests for get_top_processes function."""

    def test_top_processes_returns_list(self):
        """Test that top_processes returns a list."""
        procs = get_top_processes()
        assert isinstance(procs, list)

    def test_top_processes_respects_count(self):
        """Test that top_processes respects count parameter."""
        procs = get_top_processes(count=5)
        assert len(procs) <= 5

    def test_top_processes_items_are_process_info(self):
        """Test that items are ProcessInfo objects."""
        procs = get_top_processes(count=1)
        if procs:
            assert isinstance(procs[0], ProcessInfo)

    def test_top_processes_sort_by_cpu(self):
        """Test sorting by CPU."""
        procs = get_top_processes(count=10, sort_by="cpu")
        if len(procs) > 1:
            # First should have >= CPU than second
            assert procs[0].cpu_percent >= procs[1].cpu_percent

    def test_top_processes_sort_by_memory(self):
        """Test sorting by memory."""
        procs = get_top_processes(count=10, sort_by="memory")
        if len(procs) > 1:
            # First should have >= memory than second
            assert procs[0].memory_percent >= procs[1].memory_percent


class TestGetSystemHealth:
    """Tests for get_system_health function."""

    def test_system_health_returns_object(self):
        """Test that system_health returns SystemHealth object."""
        health = get_system_health()
        assert isinstance(health, SystemHealth)

    def test_system_health_has_hostname(self):
        """Test that system health has hostname."""
        health = get_system_health()
        assert health.hostname is not None
        assert len(health.hostname) > 0

    def test_system_health_has_valid_uptime(self):
        """Test that uptime is positive."""
        health = get_system_health()
        assert health.uptime_seconds > 0

    def test_system_health_has_boot_time(self):
        """Test that boot_time is a valid datetime."""
        health = get_system_health()
        assert isinstance(health.boot_time, datetime)
        assert health.boot_time < datetime.now()

    def test_system_health_has_cpu_info(self):
        """Test that CPU info is valid."""
        health = get_system_health()
        assert 0 <= health.cpu_percent <= 100
        assert health.cpu_count > 0

    def test_system_health_has_memory_info(self):
        """Test that memory info is valid."""
        health = get_system_health()
        assert health.memory_total_bytes > 0
        assert 0 <= health.memory_percent <= 100

    def test_system_health_has_disk_info(self):
        """Test that disk info is present."""
        health = get_system_health()
        assert isinstance(health.disk_partitions, list)

    def test_system_health_has_process_count(self):
        """Test that process count is positive."""
        health = get_system_health()
        assert health.process_count > 0


class TestSystemHealthMocked:
    """Tests for system health with mocked psutil."""

    @patch("toolkit.system_health.psutil")
    @patch("toolkit.system_health.socket")
    def test_system_health_with_mocked_psutil(self, mock_socket, mock_psutil):
        """Test system health with mocked values."""
        # Setup mocks
        mock_socket.gethostname.return_value = "test-host"
        mock_psutil.boot_time.return_value = datetime.now().timestamp() - 86400
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.cpu_freq.return_value = MagicMock(current=2400.0)
        mock_psutil.getloadavg.return_value = (1.0, 1.5, 2.0)

        vm = MagicMock()
        vm.total = 8589934592
        vm.used = 4294967296
        vm.available = 4294967296
        vm.percent = 50.0
        mock_psutil.virtual_memory.return_value = vm

        swap = MagicMock()
        swap.total = 2147483648
        swap.used = 0
        swap.percent = 0.0
        mock_psutil.swap_memory.return_value = swap

        mock_psutil.disk_partitions.return_value = []
        mock_psutil.users.return_value = []
        mock_psutil.pids.return_value = [1, 2, 3]

        health = get_system_health()

        assert health.hostname == "test-host"
        assert health.cpu_percent == 50.0
        assert health.memory_percent == 50.0
