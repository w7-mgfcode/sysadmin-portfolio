"""
SysAdmin Toolkit - Rendszergazda eszköztár.

System administration utilities for log analysis, system health monitoring,
disk usage analysis, and service management.

Rendszergazda segédprogramok log elemzéshez, rendszer állapot monitorozáshoz,
lemezterület analízishez és szolgáltatás menedzsmenthez.
"""

from .models import (
    LogEntry,
    LogAnalysisResult,
    SystemHealth,
    DiskUsage,
    ProcessInfo,
    ServiceStatus,
)
from .log_analyzer import LogAnalyzer, parse_syslog, parse_auth_log, analyze_logs
from .system_health import (
    get_system_health,
    get_cpu_info,
    get_memory_info,
    get_disk_info,
    get_top_processes,
)
from .disk_analyzer import (
    analyze_directory,
    find_large_files,
    get_directory_sizes,
    get_filesystem_usage,
)
from .service_manager import (
    get_service_status,
    list_services,
    check_critical_services,
)

__all__ = [
    # Models
    "LogEntry",
    "LogAnalysisResult",
    "SystemHealth",
    "DiskUsage",
    "ProcessInfo",
    "ServiceStatus",
    # Log analyzer
    "LogAnalyzer",
    "parse_syslog",
    "parse_auth_log",
    "analyze_logs",
    # System health
    "get_system_health",
    "get_cpu_info",
    "get_memory_info",
    "get_disk_info",
    "get_top_processes",
    # Disk analyzer
    "analyze_directory",
    "find_large_files",
    "get_directory_sizes",
    "get_filesystem_usage",
    # Service manager
    "get_service_status",
    "list_services",
    "check_critical_services",
]

__version__ = "1.0.0"
