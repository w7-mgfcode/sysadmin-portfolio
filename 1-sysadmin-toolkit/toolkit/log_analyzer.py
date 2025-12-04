"""
Log Analyzer - Rendszer log elemző.

Tools for parsing and analyzing system logs (syslog, auth.log, etc.).

Eszközök rendszer logok (syslog, auth.log, stb.) elemzéséhez.
"""

import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from .models import LogAnalysisResult, LogEntry, LogLevel


# Syslog formátum regex (RFC 3164)
# Példa: "Dec  4 10:30:15 hostname program[1234]: message"
SYSLOG_PATTERN = re.compile(
    r"^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<hostname>\S+)\s+"
    r"(?P<program>[\w\-\.\/]+)"
    r"(?:\[(?P<pid>\d+)\])?"
    r":\s*"
    r"(?P<message>.*)$"
)

# Auth log minták sikeres/sikertelen bejelentkezéshez
AUTH_SUCCESS_PATTERNS = [
    re.compile(r"Accepted\s+(?:password|publickey)\s+for\s+(\S+)\s+from\s+(\S+)"),
    re.compile(r"session opened for user\s+(\S+)"),
    re.compile(r"pam_unix\(.*:session\):\s+session opened for user\s+(\S+)"),
]

AUTH_FAILURE_PATTERNS = [
    re.compile(r"Failed\s+password\s+for\s+(?:invalid user\s+)?(\S+)\s+from\s+(\S+)"),
    re.compile(r"authentication failure.*user=(\S+)"),
    re.compile(r"pam_unix\(.*:auth\):\s+authentication failure"),
    re.compile(r"Invalid user\s+(\S+)\s+from\s+(\S+)"),
]

# Log szint felismerő minták
LEVEL_PATTERNS = {
    LogLevel.EMERGENCY: re.compile(r"\b(emerg|emergency)\b", re.IGNORECASE),
    LogLevel.ALERT: re.compile(r"\balert\b", re.IGNORECASE),
    LogLevel.CRITICAL: re.compile(r"\b(crit|critical)\b", re.IGNORECASE),
    LogLevel.ERROR: re.compile(r"\b(err|error|failed|failure)\b", re.IGNORECASE),
    LogLevel.WARNING: re.compile(r"\b(warn|warning)\b", re.IGNORECASE),
    LogLevel.NOTICE: re.compile(r"\bnotice\b", re.IGNORECASE),
    LogLevel.INFO: re.compile(r"\binfo\b", re.IGNORECASE),
    LogLevel.DEBUG: re.compile(r"\bdebug\b", re.IGNORECASE),
}


class LogAnalyzer:
    """
    Log elemző osztály.

    Class for analyzing log files with various parsing strategies.
    """

    def __init__(self, year: Optional[int] = None):
        """
        Inicializálja a log elemzőt.

        Args:
            year: Az év a timestamp-ekhez (alapértelmezett: jelenlegi év).
                  Year for timestamps (default: current year).
        """
        self.year = year or datetime.now().year
        self._entries: list[LogEntry] = []

    def parse_syslog_line(self, line: str) -> Optional[LogEntry]:
        """
        Egy syslog sor elemzése.

        Args:
            line: A log sor.

        Returns:
            LogEntry vagy None ha nem sikerült elemezni.
        """
        line = line.strip()
        if not line:
            return None

        match = SYSLOG_PATTERN.match(line)
        if not match:
            return None

        groups = match.groupdict()

        # Timestamp konvertálása
        try:
            timestamp_str = f"{self.year} {groups['timestamp']}"
            timestamp = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
        except ValueError:
            return None

        # PID konvertálása
        pid = int(groups["pid"]) if groups.get("pid") else None

        # Log szint detektálása
        level = self._detect_level(groups["message"])

        return LogEntry(
            timestamp=timestamp,
            hostname=groups["hostname"],
            program=groups["program"],
            pid=pid,
            message=groups["message"],
            level=level,
            raw_line=line,
        )

    def _detect_level(self, message: str) -> LogLevel:
        """
        Log szint detektálása üzenet alapján.

        Args:
            message: A log üzenet.

        Returns:
            Detektált LogLevel.
        """
        for level, pattern in LEVEL_PATTERNS.items():
            if pattern.search(message):
                return level
        return LogLevel.INFO

    def parse_file(self, file_path: Path | str) -> Generator[LogEntry, None, None]:
        """
        Log fájl elemzése.

        Args:
            file_path: Log fájl útvonala.

        Yields:
            LogEntry objektumok.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Log fájl nem található: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                entry = self.parse_syslog_line(line)
                if entry:
                    yield entry

    def analyze(self, entries: list[LogEntry]) -> LogAnalysisResult:
        """
        Log bejegyzések elemzése és statisztika készítése.

        Args:
            entries: LogEntry lista.

        Returns:
            LogAnalysisResult a statisztikákkal.
        """
        if not entries:
            return LogAnalysisResult(total_entries=0)

        # Számlálók
        program_counter: Counter[str] = Counter()
        level_counter: Counter[str] = Counter()
        error_messages: Counter[str] = Counter()

        # Auth log elemzés
        failed_logins = 0
        successful_logins = 0

        timestamps = []

        for entry in entries:
            program_counter[entry.program] += 1
            level_counter[entry.level.value] += 1
            timestamps.append(entry.timestamp)

            # Hiba üzenetek gyűjtése
            if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.EMERGENCY):
                # Üzenet normalizálása (számok eltávolítása)
                normalized = re.sub(r"\d+", "N", entry.message[:100])
                error_messages[normalized] += 1

            # Auth log elemzés
            for pattern in AUTH_SUCCESS_PATTERNS:
                if pattern.search(entry.message):
                    successful_logins += 1
                    break

            for pattern in AUTH_FAILURE_PATTERNS:
                if pattern.search(entry.message):
                    failed_logins += 1
                    break

        # Top error üzenetek
        top_errors = [msg for msg, _ in error_messages.most_common(10)]

        return LogAnalysisResult(
            total_entries=len(entries),
            error_count=sum(
                level_counter.get(level.value, 0)
                for level in (LogLevel.ERROR, LogLevel.CRITICAL, LogLevel.EMERGENCY)
            ),
            warning_count=level_counter.get(LogLevel.WARNING.value, 0),
            entries_by_program=dict(program_counter),
            entries_by_level=dict(level_counter),
            time_range_start=min(timestamps) if timestamps else None,
            time_range_end=max(timestamps) if timestamps else None,
            top_error_messages=top_errors,
            failed_logins=failed_logins,
            successful_logins=successful_logins,
        )


def parse_syslog(
    file_path: Path | str, year: Optional[int] = None
) -> list[LogEntry]:
    """
    Syslog fájl elemzése.

    Args:
        file_path: A syslog fájl útvonala.
        year: Év a timestamp-ekhez.

    Returns:
        LogEntry lista.
    """
    analyzer = LogAnalyzer(year=year)
    return list(analyzer.parse_file(file_path))


def parse_auth_log(
    file_path: Path | str, year: Optional[int] = None
) -> list[LogEntry]:
    """
    Auth.log fájl elemzése.

    Args:
        file_path: Az auth.log fájl útvonala.
        year: Év a timestamp-ekhez.

    Returns:
        LogEntry lista.
    """
    # Reason: Az auth.log és syslog formátuma azonos
    return parse_syslog(file_path, year)


def analyze_logs(
    file_path: Path | str, year: Optional[int] = None
) -> LogAnalysisResult:
    """
    Log fájl elemzése és statisztika készítése.

    Args:
        file_path: A log fájl útvonala.
        year: Év a timestamp-ekhez.

    Returns:
        LogAnalysisResult a statisztikákkal.

    Example:
        >>> result = analyze_logs("/var/log/syslog")
        >>> print(f"Errors: {result.error_count}")
    """
    analyzer = LogAnalyzer(year=year)
    entries = list(analyzer.parse_file(file_path))
    return analyzer.analyze(entries)
