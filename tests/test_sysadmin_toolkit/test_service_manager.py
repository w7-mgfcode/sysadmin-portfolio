"""
Tests for service manager module.

Tesztek a szolgáltatás kezelő modulhoz.
"""

from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/1-sysadmin-toolkit")

from toolkit.service_manager import (
    check_critical_services,
    get_failed_services,
    get_service_logs,
    get_service_status,
    list_services,
)
from toolkit.models import ServiceState, ServiceStatus


class TestGetServiceStatus:
    """Tests for get_service_status function."""

    @patch("toolkit.service_manager._run_systemctl")
    def test_service_status_running(self, mock_run):
        """Test getting status of a running service."""
        # Setup mock responses
        mock_run.side_effect = [
            ("enabled", 0),  # is-enabled
            ("active", 0),  # is-active
            ("MainPID=1234\nDescription=Test Service\nLoadState=loaded\nSubState=running\n", 0),  # show
        ]

        status = get_service_status("test-service")

        assert isinstance(status, ServiceStatus)
        assert status.name == "test-service"
        assert status.state == ServiceState.RUNNING
        assert status.is_enabled is True
        assert status.is_active is True

    @patch("toolkit.service_manager._run_systemctl")
    def test_service_status_stopped(self, mock_run):
        """Test getting status of a stopped service."""
        mock_run.side_effect = [
            ("disabled", 1),  # is-enabled
            ("inactive", 3),  # is-active
            ("MainPID=0\nDescription=Test Service\n", 0),  # show
        ]

        status = get_service_status("test-service")

        assert status.state == ServiceState.INACTIVE
        assert status.is_enabled is False
        assert status.is_active is False

    @patch("toolkit.service_manager._run_systemctl")
    def test_service_status_failed(self, mock_run):
        """Test getting status of a failed service."""
        mock_run.side_effect = [
            ("enabled", 0),
            ("failed", 1),
            ("MainPID=0\n", 0),
        ]

        status = get_service_status("test-service")

        assert status.state == ServiceState.FAILED

    @patch("toolkit.service_manager._run_systemctl")
    def test_service_status_with_memory(self, mock_run):
        """Test getting service status with memory info."""
        mock_run.side_effect = [
            ("enabled", 0),
            ("active", 0),
            ("MainPID=1234\nMemoryCurrent=52428800\n", 0),
        ]

        status = get_service_status("test-service")

        assert status.pid == 1234
        assert status.memory_bytes == 52428800


class TestListServices:
    """Tests for list_services function."""

    @patch("toolkit.service_manager.get_service_status")
    @patch("toolkit.service_manager._run_systemctl")
    def test_list_services_returns_list(self, mock_run, mock_status):
        """Test that list_services returns a list."""
        mock_run.return_value = (
            "nginx.service loaded active running nginx server\n"
            "sshd.service loaded active running SSH daemon\n",
            0,
        )
        mock_status.return_value = ServiceStatus(
            name="test",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
        )

        services = list_services()
        assert isinstance(services, list)

    @patch("toolkit.service_manager.get_service_status")
    @patch("toolkit.service_manager._run_systemctl")
    def test_list_services_filter_by_state(self, mock_run, mock_status):
        """Test filtering by state."""
        mock_run.return_value = (
            "nginx.service loaded active running nginx\n",
            0,
        )
        mock_status.return_value = ServiceStatus(
            name="nginx",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
        )

        services = list_services(filter_state=ServiceState.RUNNING)
        assert all(s.state == ServiceState.RUNNING for s in services)

    @patch("toolkit.service_manager._run_systemctl")
    def test_list_services_empty_on_error(self, mock_run):
        """Test empty list on systemctl error."""
        mock_run.return_value = ("", 1)

        services = list_services()
        assert services == []


class TestCheckCriticalServices:
    """Tests for check_critical_services function."""

    @patch("toolkit.service_manager.get_service_status")
    def test_check_critical_services_returns_dict(self, mock_status):
        """Test that function returns a dictionary."""
        mock_status.return_value = ServiceStatus(
            name="test",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
        )

        results = check_critical_services(["sshd"])
        assert isinstance(results, dict)
        assert "sshd" in results

    @patch("toolkit.service_manager.get_service_status")
    def test_check_critical_services_custom_list(self, mock_status):
        """Test with custom service list."""
        mock_status.return_value = ServiceStatus(
            name="test",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
        )

        custom_services = ["nginx", "mysql", "redis"]
        results = check_critical_services(custom_services)

        assert len(results) == 3
        assert all(name in results for name in custom_services)

    @patch("toolkit.service_manager.get_service_status")
    def test_check_critical_services_default_list(self, mock_status):
        """Test with default service list."""
        mock_status.return_value = ServiceStatus(
            name="test",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
        )

        results = check_critical_services(None)
        # Should contain some default services
        assert len(results) > 0


class TestGetFailedServices:
    """Tests for get_failed_services function."""

    @patch("toolkit.service_manager.list_services")
    def test_get_failed_services(self, mock_list):
        """Test getting failed services."""
        mock_list.return_value = [
            ServiceStatus(
                name="failed1",
                state=ServiceState.FAILED,
                is_enabled=True,
                is_active=False,
            ),
        ]

        failed = get_failed_services()
        mock_list.assert_called_once_with(filter_state=ServiceState.FAILED)


class TestGetServiceLogs:
    """Tests for get_service_logs function."""

    @patch("toolkit.service_manager.subprocess.run")
    def test_get_service_logs_success(self, mock_run):
        """Test successful log retrieval."""
        mock_run.return_value = MagicMock(stdout="Log line 1\nLog line 2\n")

        logs = get_service_logs("nginx", lines=10)

        assert "Log line 1" in logs
        mock_run.assert_called_once()

    @patch("toolkit.service_manager.subprocess.run")
    def test_get_service_logs_with_since(self, mock_run):
        """Test log retrieval with since parameter."""
        mock_run.return_value = MagicMock(stdout="Recent logs")

        logs = get_service_logs("nginx", lines=50, since="1 hour ago")

        call_args = mock_run.call_args[0][0]
        assert "--since" in call_args
        assert "1 hour ago" in call_args

    @patch("toolkit.service_manager.subprocess.run")
    def test_get_service_logs_not_found(self, mock_run):
        """Test when journalctl is not found."""
        mock_run.side_effect = FileNotFoundError

        logs = get_service_logs("nginx")
        assert logs == ""


class TestServiceStatusModel:
    """Additional tests for ServiceStatus model integration."""

    def test_service_status_creation(self):
        """Test creating ServiceStatus with all fields."""
        status = ServiceStatus(
            name="nginx",
            state=ServiceState.RUNNING,
            is_enabled=True,
            is_active=True,
            pid=1234,
            memory_bytes=52428800,
            description="A high performance web server",
            load_state="loaded",
            sub_state="running",
        )

        assert status.name == "nginx"
        assert status.pid == 1234
        assert status.memory_bytes == 52428800

    def test_service_status_optional_fields(self):
        """Test ServiceStatus with optional fields as None."""
        status = ServiceStatus(
            name="test",
            state=ServiceState.STOPPED,
            is_enabled=False,
            is_active=False,
        )

        assert status.pid is None
        assert status.memory_bytes is None
        assert status.description is None
