"""
Backup Automation - Automatizált mentési rendszer.

Ez a modul tartalmazza a backup műveletekhez szükséges eszközöket:
- File/folder backup
- MySQL backup
- PostgreSQL backup
- Retention manager
- Restore test

Használat:
    >>> from backup_automation import FileBackup
    >>> backup = FileBackup(source="/data", dest="/backups")
    >>> result = backup.run()
    >>> print(f"Backup: {result.success}, Size: {result.backup_size_bytes}")
"""

__version__ = "1.0.0"
__author__ = "SysAdmin Portfolio"
