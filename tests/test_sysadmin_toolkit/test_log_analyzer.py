"""
Tests for log analyzer module.

Tesztek a log elemző modulhoz.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/1-sysadmin-toolkit")

from toolkit.log_analyzer import (
    LogAnalyzer,
    analyze_logs,
    parse_auth_log,
    parse_syslog,
)
from toolkit.models import LogEntry, LogLevel


# Sample log lines for testing / Teszt log sorok
SAMPLE_SYSLOG_LINES = [
    "Dec  4 10:30:15 server01 sshd[1234]: Accepted password for user1 from 192.168.1.100",
    "Dec  4 10:30:16 server01 nginx[5678]: worker process started",
    "Dec  4 10:30:17 server01 kernel: Out of memory: Kill process 9999",
    "Dec  4 10:30:18 server01 cron[100]: (root) CMD (/usr/bin/backup)",
    "Dec  4 10:30:19 server01 sshd[1235]: Failed password for invalid user admin from 10.0.0.1",
]

SAMPLE_AUTH_LOG_LINES = [
    "Dec  4 10:30:15 server01 sshd[1234]: Accepted password for user1 from 192.168.1.100",
    "Dec  4 10:30:16 server01 sshd[1235]: Failed password for root from 10.0.0.1",
    "Dec  4 10:30:17 server01 sshd[1236]: Failed password for invalid user admin from 10.0.0.2",
    "Dec  4 10:30:18 server01 sudo: pam_unix(sudo:session): session opened for user root",
    "Dec  4 10:30:19 server01 sshd[1237]: Invalid user test from 10.0.0.3",
]


class TestLogAnalyzer:
    """Tests for LogAnalyzer class."""

    def test_parse_syslog_line(self):
        """Test parsing a single syslog line."""
        analyzer = LogAnalyzer(year=2024)
        entry = analyzer.parse_syslog_line(SAMPLE_SYSLOG_LINES[0])

        assert entry is not None
        assert entry.hostname == "server01"
        assert entry.program == "sshd"
        assert entry.pid == 1234
        assert "Accepted password" in entry.message

    def test_parse_syslog_line_without_pid(self):
        """Test parsing syslog line without PID."""
        analyzer = LogAnalyzer(year=2024)
        entry = analyzer.parse_syslog_line(SAMPLE_SYSLOG_LINES[2])

        assert entry is not None
        assert entry.program == "kernel"
        assert entry.pid is None

    def test_parse_empty_line(self):
        """Test parsing empty line returns None."""
        analyzer = LogAnalyzer(year=2024)
        entry = analyzer.parse_syslog_line("")
        assert entry is None

    def test_parse_invalid_line(self):
        """Test parsing invalid line returns None."""
        analyzer = LogAnalyzer(year=2024)
        entry = analyzer.parse_syslog_line("This is not a valid syslog line")
        assert entry is None

    def test_detect_error_level(self):
        """Test error level detection."""
        analyzer = LogAnalyzer(year=2024)

        # Error keyword detection
        assert analyzer._detect_level("Connection failed") == LogLevel.ERROR
        assert analyzer._detect_level("Error occurred") == LogLevel.ERROR
        assert analyzer._detect_level("Warning: disk full") == LogLevel.WARNING
        assert analyzer._detect_level("Normal message") == LogLevel.INFO


class TestParseSyslog:
    """Tests for parse_syslog function."""

    def test_parse_syslog_file(self):
        """Test parsing entire syslog file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("\n".join(SAMPLE_SYSLOG_LINES))
            f.flush()

            entries = parse_syslog(f.name, year=2024)

            assert len(entries) == 5
            assert entries[0].program == "sshd"
            assert entries[1].program == "nginx"

    def test_parse_syslog_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_syslog("/nonexistent/file.log")


class TestParseAuthLog:
    """Tests for parse_auth_log function."""

    def test_parse_auth_log_file(self):
        """Test parsing auth.log file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("\n".join(SAMPLE_AUTH_LOG_LINES))
            f.flush()

            entries = parse_auth_log(f.name, year=2024)

            assert len(entries) == 5


class TestAnalyzeLogs:
    """Tests for analyze_logs function."""

    def test_analyze_logs(self):
        """Test log file analysis."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("\n".join(SAMPLE_SYSLOG_LINES))
            f.flush()

            result = analyze_logs(f.name, year=2024)

            assert result.total_entries == 5
            assert "sshd" in result.entries_by_program
            assert result.entries_by_program["sshd"] >= 1

    def test_analyze_auth_logs(self):
        """Test auth log analysis for login tracking."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("\n".join(SAMPLE_AUTH_LOG_LINES))
            f.flush()

            result = analyze_logs(f.name, year=2024)

            assert result.successful_logins >= 1
            assert result.failed_logins >= 1

    def test_analyze_empty_file(self):
        """Test analyzing empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("")
            f.flush()

            result = analyze_logs(f.name, year=2024)

            assert result.total_entries == 0


class TestLogAnalyzerIntegration:
    """Integration tests for log analyzer."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow."""
        # Create sample log content
        log_content = """Dec  4 10:30:15 server01 sshd[1234]: Accepted password for user1 from 192.168.1.100
Dec  4 10:30:16 server01 nginx[5678]: Error: connection refused
Dec  4 10:30:17 server01 kernel: Warning: disk usage high
Dec  4 10:30:18 server01 sshd[1235]: Failed password for root from 10.0.0.1
Dec  4 10:30:19 server01 cron[100]: INFO: job completed"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(log_content)
            f.flush()

            analyzer = LogAnalyzer(year=2024)
            entries = list(analyzer.parse_file(f.name))
            result = analyzer.analyze(entries)

            # Verify counts
            assert result.total_entries == 5
            assert result.error_count >= 1  # "Error: connection refused"
            assert result.warning_count >= 1  # "Warning: disk usage"

            # Verify program breakdown
            assert "sshd" in result.entries_by_program
            assert result.entries_by_program["sshd"] == 2

            # Verify time range
            assert result.time_range_start is not None
            assert result.time_range_end is not None
