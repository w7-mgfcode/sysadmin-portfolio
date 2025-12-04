"""
Backup Manager - Mentés kezelő rendszer.

Automated backup system with retention policies, rotation, and verification.

Automatizált mentési rendszer megőrzési szabályokkal, rotációval és ellenőrzéssel.
"""

from .models import (
    BackupConfig,
    BackupJob,
    BackupResult,
    BackupStatus,
    BackupType,
    RetentionPolicy,
)
from .manager import BackupManager
from .retention import RetentionManager
from .verifier import BackupVerifier

__all__ = [
    # Models
    "BackupConfig",
    "BackupJob",
    "BackupResult",
    "BackupStatus",
    "BackupType",
    "RetentionPolicy",
    # Manager
    "BackupManager",
    "RetentionManager",
    "BackupVerifier",
]

__version__ = "1.0.0"
