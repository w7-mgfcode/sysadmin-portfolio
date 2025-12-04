"""
Tests for SysAdmin Toolkit models.

Tesztek a toolkit modellekhez.
"""

from datetime import datetime

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/1-sysadmin-toolkit")

from toolkit.models import (
    DirectorySize,
    DiskUsage,
    LargeFile,
    LogAnalysisResult,
    LogEntry,
    LogLevel,
    ProcessInfo,
    ServiceState,
    ServiceStatus,
    SystemHealth,
)


class TestLogEntry:
    """Tests for LogEntry model."""

    def test_create_log_entry(self):
        """Test creating a basic log entry."""
        entry = LogEntry(
            timestamp=datetime.now(),
            hostname="server01",
            program="sshd",
            message="Accepted password for user",
            level=LogLevel.INFO,
        )
        assert entry.hostname == "server01"
        assert entry.program == "sshd"
        assert entry.level == LogLevel.INFO

    def test_log_entry_with_pid(self):
        """Test log entry with PID."""
        entry = LogEntry(
            timestamp=datetime.now(),
            hostname="server01",
            program="nginx",
            pid=1234,
            message="worker process started",
        )
        assert entry.pid == 1234

    def test_log_entry_without_pid(self):
        """Test log entry without PID defaults to None."""
        entry = LogEntry(
            timestamp=datetime.now(),
            hostname="server01",
            program="kernel",
            message="kernel message",
        )
        assert entry.pid is None


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_all_log_levels_exist(self):
        """Test that all expected log levels are defined."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_level_from_string(self):
        """Test creating log level from string."""
        assert LogLevel("error") == LogLevel.ERROR


class TestLogAnalysisResult:
    """Tests for LogAnalysisResult model."""

    def test_empty_analysis_result(self):
        """Test creating empty analysis result."""
        result = LogAnalysisResult(total_entries=0)
        assert result.total_entries == 0
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_analysis_result_with_data(self):
        """Test analysis result with data."""
        result = LogAnalysisResult(
            total_entries=100,
            error_count=5,
            warning_count=10,
            entries_by_program={"sshd": 50, "nginx": 50},
            entries_by_level={"info": 85, "error": 5, "warning": 10},
            failed_logins=3,
            successful_logins=10,
        )
        assert result.total_entries == 100
        assert result.error_count == 5
        assert result.entries_by_program["sshd"] == 50


class TestSystemHealth:
    """Tests for SystemHealth model."""

    def test_create_system_health(self):
        """Test creating system health object."""
        health = SystemHealth(
            hostname="server01",
            uptime_seconds=86400.0,
            boot_time=datetime.now(),
            cpu_percent=25.5,
            cpu_count=4,
            load_avg_1m=0.5,
            load_avg_5m=0.6,
            load_avg_15m=0.7,
            memory_total_bytes=8589934592,
            memory_used_bytes=4294967296,
            memory_available_bytes=4294967296,
            memory_percent=50.0,
            swap_total_bytes=2147483648,
            swap_used_bytes=0,
            swap_percent=0.0,
            process_count=100,
            users_logged_in=2,
        )
        assert health.hostname == "server01"
        assert health.cpu_percent == 25.5
        assert health.memory_percent == 50.0


class TestDiskUsage:
    """Tests for DiskUsage model."""

    def test_create_disk_usage(self):
        """Test creating disk usage object."""
        disk = DiskUsage(
            device="/dev/sda1",
            mountpoint="/",
            fstype="ext4",
            total_bytes=107374182400,
            used_bytes=53687091200,
            free_bytes=53687091200,
            percent_used=50.0,
        )
        assert disk.device == "/dev/sda1"
        assert disk.percent_used == 50.0


class TestDirectorySize:
    """Tests for DirectorySize model."""

    def test_create_directory_size(self):
        """Test creating directory size object."""
        dir_size = DirectorySize(
            path="/var/log",
            size_bytes=1073741824,
            file_count=100,
            dir_count=10,
        )
        assert dir_size.path == "/var/log"
        assert dir_size.size_bytes == 1073741824


class TestLargeFile:
    """Tests for LargeFile model."""

    def test_create_large_file(self):
        """Test creating large file object."""
        large_file = LargeFile(
            path="/var/log/syslog",
            size_bytes=524288000,
            modified_time=datetime.now(),
            owner="root",
        )
        assert large_file.size_bytes == 524288000
        assert large_file.owner == "root"


class TestProcessInfo:
    """Tests for ProcessInfo model."""

    def test_create_process_info(self):
        """Test creating process info object."""
        proc = ProcessInfo(
            pid=1,
            name="systemd",
            username="root",
            status="running",
            cpu_percent=0.5,
            memory_percent=1.2,
            memory_rss_bytes=12582912,
            create_time=datetime.now(),
        )
        assert proc.pid == 1
        assert proc.name == "systemd"


class TestServiceStatus:
    """Tests for ServiceStatus model."""

    def test_create_service_status(self):
        """Test creating service status object."""
        status = ServiceStatus(
            name="nginx",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
            pid=1234,
            description="A high performance web server",
        )
        assert status.name == "nginx"
        assert status.state == ServiceState.RUNNING
        assert status.is_active is True

    def test_service_states(self):
        """Test all service states exist."""
        assert ServiceState.RUNNING.value == "running"
        assert ServiceState.STOPPED.value == "stopped"
        assert ServiceState.FAILED.value == "failed"
        assert ServiceState.INACTIVE.value == "inactive"
