"""
Pydantic models for backup automation.

Pydantic modellek a mentés automatizáláshoz.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BackupType(str, Enum):
    """Mentés típus enumeration."""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str, Enum):
    """Mentés státusz enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


class RetentionPolicy(BaseModel):
    """
    Megőrzési szabály konfiguráció.

    Retention policy configuration for backup cleanup.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    keep_daily: int = Field(default=7, description="Napi mentések megőrzése (napokban)")
    keep_weekly: int = Field(default=4, description="Heti mentések megőrzése (hetekben)")
    keep_monthly: int = Field(default=6, description="Havi mentések megőrzése (hónapokban)")
    keep_yearly: int = Field(default=1, description="Éves mentések megőrzése (években)")
    min_backups: int = Field(
        default=3, description="Minimum megőrzendő mentések száma"
    )

    @field_validator("keep_daily", "keep_weekly", "keep_monthly", "keep_yearly", "min_backups")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate that values are positive."""
        if v < 0:
            raise ValueError("Retention values must be positive")
        return v


class BackupConfig(BaseModel):
    """
    Mentés konfiguráció.

    Configuration for a backup job.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(description="Mentési feladat neve")
    source_path: Path = Field(description="Forrás útvonal")
    destination_path: Path = Field(description="Cél útvonal")
    backup_type: BackupType = Field(
        default=BackupType.FULL, description="Mentés típusa"
    )
    compression: bool = Field(default=True, description="Tömörítés engedélyezése")
    encryption: bool = Field(default=False, description="Titkosítás engedélyezése")
    retention_policy: RetentionPolicy = Field(
        default_factory=RetentionPolicy, description="Megőrzési szabály"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="Kizárandó mintázatok"
    )
    schedule_cron: Optional[str] = Field(
        default=None, description="Ütemezés cron formátumban"
    )
    enabled: bool = Field(default=True, description="Mentés engedélyezve")
    pre_backup_script: Optional[Path] = Field(
        default=None, description="Mentés előtti script"
    )
    post_backup_script: Optional[Path] = Field(
        default=None, description="Mentés utáni script"
    )
    notification_email: Optional[str] = Field(
        default=None, description="Értesítési email cím"
    )


class BackupJob(BaseModel):
    """
    Mentési feladat információ.

    Information about a backup job execution.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    job_id: str = Field(description="Feladat azonosító")
    config_name: str = Field(description="Konfiguráció neve")
    backup_type: BackupType = Field(description="Mentés típusa")
    started_at: datetime = Field(description="Indítás időpontja")
    finished_at: Optional[datetime] = Field(default=None, description="Befejezés időpontja")
    status: BackupStatus = Field(description="Állapot")
    backup_file: Optional[Path] = Field(default=None, description="Mentés fájl útvonala")
    size_bytes: Optional[int] = Field(default=None, description="Méret bájtban")
    files_count: Optional[int] = Field(default=None, description="Fájlok száma")
    error_message: Optional[str] = Field(default=None, description="Hibaüzenet")
    duration_seconds: Optional[float] = Field(
        default=None, description="Időtartam másodpercben"
    )

    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == BackupStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if job is completed successfully."""
        return self.status == BackupStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == BackupStatus.FAILED


class BackupResult(BaseModel):
    """
    Mentés eredmény.

    Result of a backup operation.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    success: bool = Field(description="Sikeres volt-e")
    job: BackupJob = Field(description="Mentési feladat")
    message: str = Field(description="Eredmény üzenet")
    warnings: list[str] = Field(default_factory=list, description="Figyelmeztetések")


class BackupMetadata(BaseModel):
    """
    Mentés metadata.

    Metadata stored with each backup.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    backup_id: str = Field(description="Mentés azonosító")
    created_at: datetime = Field(description="Létrehozás időpontja")
    config_name: str = Field(description="Konfiguráció neve")
    backup_type: BackupType = Field(description="Mentés típusa")
    source_path: str = Field(description="Forrás útvonal")
    hostname: str = Field(description="Host neve")
    size_bytes: int = Field(description="Méret bájtban")
    files_count: int = Field(description="Fájlok száma")
    compression: bool = Field(description="Tömörített-e")
    encryption: bool = Field(description="Titkosított-e")
    checksum: Optional[str] = Field(default=None, description="Ellenőrző összeg")
    parent_backup_id: Optional[str] = Field(
        default=None, description="Szülő mentés azonosító (inkrementális esetén)"
    )


class VerificationResult(BaseModel):
    """
    Ellenőrzési eredmény.

    Result of backup verification.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    backup_file: Path = Field(description="Mentés fájl")
    is_valid: bool = Field(description="Érvényes-e")
    can_extract: bool = Field(description="Kibontható-e")
    checksum_match: Optional[bool] = Field(
        default=None, description="Ellenőrző összeg egyezik-e"
    )
    size_bytes: int = Field(description="Méret bájtban")
    verified_at: datetime = Field(description="Ellenőrzés időpontja")
    errors: list[str] = Field(default_factory=list, description="Hibák")
