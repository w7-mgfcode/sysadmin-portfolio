"""
Pydantic models for SysAdmin Toolkit.

Pydantic modellek a rendszergazda eszköztárhoz.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    """Log szint enumeration."""

    DEBUG = "debug"
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    ALERT = "alert"
    EMERGENCY = "emergency"


class LogEntry(BaseModel):
    """
    Egy log bejegyzés reprezentációja.

    Represents a single log entry from system logs.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    timestamp: datetime = Field(description="Log bejegyzés időpontja")
    hostname: str = Field(description="Host neve")
    program: str = Field(description="Program vagy szolgáltatás neve")
    pid: Optional[int] = Field(default=None, description="Process ID")
    message: str = Field(description="Log üzenet tartalma")
    level: LogLevel = Field(default=LogLevel.INFO, description="Log szint")
    facility: Optional[str] = Field(default=None, description="Syslog facility")
    raw_line: Optional[str] = Field(default=None, description="Eredeti log sor")


class LogAnalysisResult(BaseModel):
    """
    Log elemzés eredménye.

    Contains statistics and insights from log analysis.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    total_entries: int = Field(description="Összes bejegyzés száma")
    error_count: int = Field(default=0, description="Hibák száma")
    warning_count: int = Field(default=0, description="Figyelmeztetések száma")
    entries_by_program: dict[str, int] = Field(
        default_factory=dict, description="Bejegyzések programonként"
    )
    entries_by_level: dict[str, int] = Field(
        default_factory=dict, description="Bejegyzések szintenként"
    )
    time_range_start: Optional[datetime] = Field(
        default=None, description="Legkorábbi bejegyzés"
    )
    time_range_end: Optional[datetime] = Field(
        default=None, description="Legutolsó bejegyzés"
    )
    top_error_messages: list[str] = Field(
        default_factory=list, description="Leggyakoribb hibaüzenetek"
    )
    failed_logins: int = Field(default=0, description="Sikertelen bejelentkezések száma")
    successful_logins: int = Field(
        default=0, description="Sikeres bejelentkezések száma"
    )


class SystemHealth(BaseModel):
    """
    Rendszer egészségi állapot.

    System health information including CPU, memory, disk, and load.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    hostname: str = Field(description="Rendszer neve")
    uptime_seconds: float = Field(description="Üzemidő másodpercben")
    boot_time: datetime = Field(description="Boot időpont")
    cpu_percent: float = Field(description="CPU használat százalékban")
    cpu_count: int = Field(description="CPU magok száma")
    cpu_freq_mhz: Optional[float] = Field(
        default=None, description="CPU frekvencia MHz-ben"
    )
    load_avg_1m: float = Field(description="Load average 1 perc")
    load_avg_5m: float = Field(description="Load average 5 perc")
    load_avg_15m: float = Field(description="Load average 15 perc")
    memory_total_bytes: int = Field(description="Összes memória")
    memory_used_bytes: int = Field(description="Használt memória")
    memory_available_bytes: int = Field(description="Elérhető memória")
    memory_percent: float = Field(description="Memória használat százalékban")
    swap_total_bytes: int = Field(description="Összes swap")
    swap_used_bytes: int = Field(description="Használt swap")
    swap_percent: float = Field(description="Swap használat százalékban")
    disk_partitions: list["DiskUsage"] = Field(
        default_factory=list, description="Lemez partíciók"
    )
    process_count: int = Field(description="Futó folyamatok száma")
    users_logged_in: int = Field(description="Bejelentkezett felhasználók")


class DiskUsage(BaseModel):
    """
    Lemez használat információ.

    Disk usage information for a partition or mount point.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    device: str = Field(description="Eszköz neve")
    mountpoint: str = Field(description="Mount pont")
    fstype: str = Field(description="Fájlrendszer típusa")
    total_bytes: int = Field(description="Összes méret")
    used_bytes: int = Field(description="Használt méret")
    free_bytes: int = Field(description="Szabad méret")
    percent_used: float = Field(description="Használat százalékban")


class DirectorySize(BaseModel):
    """
    Könyvtár méret információ.

    Directory size information.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    path: str = Field(description="Könyvtár útvonala")
    size_bytes: int = Field(description="Méret bájtokban")
    file_count: int = Field(default=0, description="Fájlok száma")
    dir_count: int = Field(default=0, description="Alkönyvtárak száma")


class LargeFile(BaseModel):
    """
    Nagy fájl információ.

    Information about a large file.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    path: str = Field(description="Fájl útvonala")
    size_bytes: int = Field(description="Méret bájtokban")
    modified_time: datetime = Field(description="Utolsó módosítás")
    owner: Optional[str] = Field(default=None, description="Tulajdonos")


class ProcessInfo(BaseModel):
    """
    Folyamat információ.

    Process information including resource usage.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    pid: int = Field(description="Process ID")
    name: str = Field(description="Folyamat neve")
    username: str = Field(description="Tulajdonos")
    status: str = Field(description="Folyamat státusza")
    cpu_percent: float = Field(description="CPU használat százalékban")
    memory_percent: float = Field(description="Memória használat százalékban")
    memory_rss_bytes: int = Field(description="RSS memória")
    create_time: datetime = Field(description="Létrehozás időpontja")
    cmdline: Optional[str] = Field(default=None, description="Parancssor")


class ServiceState(str, Enum):
    """Szolgáltatás állapot enumeration."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class ServiceStatus(BaseModel):
    """
    Szolgáltatás státusz.

    Service status information from systemd or init.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(description="Szolgáltatás neve")
    state: ServiceState = Field(description="Aktuális állapot")
    is_enabled: bool = Field(description="Indításkor elindul-e")
    is_active: bool = Field(description="Aktív-e")
    pid: Optional[int] = Field(default=None, description="Main PID")
    memory_bytes: Optional[int] = Field(
        default=None, description="Memória használat bájtban"
    )
    cpu_usage_seconds: Optional[float] = Field(
        default=None, description="CPU használat másodpercben"
    )
    uptime_seconds: Optional[float] = Field(
        default=None, description="Szolgáltatás uptime"
    )
    description: Optional[str] = Field(default=None, description="Szolgáltatás leírása")
    load_state: Optional[str] = Field(default=None, description="Load state")
    sub_state: Optional[str] = Field(default=None, description="Sub state")
