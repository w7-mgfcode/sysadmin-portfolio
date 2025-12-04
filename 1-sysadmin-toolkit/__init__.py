"""
SysAdmin Toolkit - Rendszergazda eszközök.

Ez a modul tartalmazza a rendszergazdai feladatokhoz szükséges eszközöket:
- System info riport generálás
- Disk usage monitoring és alertek
- User audit
- Service monitor
- Log analyzer

Használat:
    >>> from sysadmin_toolkit import get_system_info
    >>> info = get_system_info()
    >>> print(f"CPU: {info.cpu_percent}%, RAM: {info.memory_percent}%")
"""

__version__ = "1.0.0"
__author__ = "SysAdmin Portfolio"
