"""
Tests for backup automation models.

Tesztek a backup automatizálás modellekhez.
"""

from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/5-backup-automation")

from backup_manager.models import (
    BackupConfig,
    BackupJob,
    BackupMetadata,
    BackupResult,
    BackupStatus,
    BackupType,
    RetentionPolicy,
    VerificationResult,
)


class TestRetentionPolicy:
    """Tests for RetentionPolicy model."""

    def test_default_retention_policy(self):
        """Test default retention policy values."""
        policy = RetentionPolicy()
        assert policy.keep_daily == 7
        assert policy.keep_weekly == 4
        assert policy.keep_monthly == 6
        assert policy.keep_yearly == 1
        assert policy.min_backups == 3

    def test_custom_retention_policy(self):
        """Test custom retention policy values."""
        policy = RetentionPolicy(
            keep_daily=14,
            keep_weekly=8,
            keep_monthly=12,
            keep_yearly=2,
            min_backups=5,
        )
        assert policy.keep_daily == 14
        assert policy.min_backups == 5

    def test_retention_policy_validation(self):
        """Test that negative values are rejected."""
        with pytest.raises(ValueError):
            RetentionPolicy(keep_daily=-1)


class TestBackupConfig:
    """Tests for BackupConfig model."""

    def test_create_backup_config(self):
        """Test creating backup configuration."""
        config = BackupConfig(
            name="test-backup",
            source_path=Path("/home/user"),
            destination_path=Path("/backups"),
        )
        assert config.name == "test-backup"
        assert config.backup_type == BackupType.FULL
        assert config.compression is True
        assert config.enabled is True

    def test_backup_config_with_exclusions(self):
        """Test backup config with exclude patterns."""
        config = BackupConfig(
            name="test",
            source_path=Path("/home"),
            destination_path=Path("/backups"),
            exclude_patterns=["*.log", "*.tmp", ".cache/*"],
        )
        assert len(config.exclude_patterns) == 3

    def test_backup_config_with_schedule(self):
        """Test backup config with cron schedule."""
        config = BackupConfig(
            name="test",
            source_path=Path("/home"),
            destination_path=Path("/backups"),
            schedule_cron="0 2 * * *",
        )
        assert config.schedule_cron == "0 2 * * *"


class TestBackupJob:
    """Tests for BackupJob model."""

    def test_create_backup_job(self):
        """Test creating backup job."""
        job = BackupJob(
            job_id="test-123",
            config_name="test-backup",
            backup_type=BackupType.FULL,
            started_at=datetime.now(),
            status=BackupStatus.RUNNING,
        )
        assert job.job_id == "test-123"
        assert job.is_running is True

    def test_backup_job_completed(self):
        """Test completed backup job."""
        job = BackupJob(
            job_id="test-123",
            config_name="test",
            backup_type=BackupType.FULL,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            status=BackupStatus.COMPLETED,
            backup_file=Path("/backups/test.tar.gz"),
            size_bytes=1024000,
        )
        assert job.is_completed is True
        assert job.size_bytes == 1024000

    def test_backup_job_failed(self):
        """Test failed backup job."""
        job = BackupJob(
            job_id="test-123",
            config_name="test",
            backup_type=BackupType.FULL,
            started_at=datetime.now(),
            finished_at=datetime.now(),
            status=BackupStatus.FAILED,
            error_message="Disk full",
        )
        assert job.is_failed is True
        assert job.error_message == "Disk full"


class TestBackupResult:
    """Tests for BackupResult model."""

    def test_successful_backup_result(self):
        """Test successful backup result."""
        job = BackupJob(
            job_id="test-123",
            config_name="test",
            backup_type=BackupType.FULL,
            started_at=datetime.now(),
            status=BackupStatus.COMPLETED,
        )
        result = BackupResult(
            success=True,
            job=job,
            message="Backup completed",
        )
        assert result.success is True
        assert "completed" in result.message.lower()

    def test_failed_backup_result(self):
        """Test failed backup result."""
        job = BackupJob(
            job_id="test-123",
            config_name="test",
            backup_type=BackupType.FULL,
            started_at=datetime.now(),
            status=BackupStatus.FAILED,
        )
        result = BackupResult(
            success=False,
            job=job,
            message="Backup failed",
            warnings=["Low disk space"],
        )
        assert result.success is False
        assert len(result.warnings) == 1


class TestBackupMetadata:
    """Tests for BackupMetadata model."""

    def test_create_backup_metadata(self):
        """Test creating backup metadata."""
        metadata = BackupMetadata(
            backup_id="backup-123",
            created_at=datetime.now(),
            config_name="test-backup",
            backup_type=BackupType.FULL,
            source_path="/home/user",
            hostname="server01",
            size_bytes=1024000,
            files_count=100,
            compression=True,
            encryption=False,
        )
        assert metadata.backup_id == "backup-123"
        assert metadata.compression is True


class TestVerificationResult:
    """Tests for VerificationResult model."""

    def test_valid_verification_result(self):
        """Test valid verification result."""
        result = VerificationResult(
            backup_file=Path("/backups/test.tar.gz"),
            is_valid=True,
            can_extract=True,
            checksum_match=True,
            size_bytes=1024000,
            verified_at=datetime.now(),
        )
        assert result.is_valid is True
        assert result.can_extract is True

    def test_invalid_verification_result(self):
        """Test invalid verification result."""
        result = VerificationResult(
            backup_file=Path("/backups/test.tar.gz"),
            is_valid=False,
            can_extract=False,
            size_bytes=0,
            verified_at=datetime.now(),
            errors=["Checksum mismatch", "Corrupt archive"],
        )
        assert result.is_valid is False
        assert len(result.errors) == 2
