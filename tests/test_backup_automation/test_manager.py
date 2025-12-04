"""
Tests for backup manager.

Tesztek a backup managerhez.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0] + "/5-backup-automation")

from backup_manager.manager import BackupManager
from backup_manager.models import BackupConfig, BackupType, RetentionPolicy


class TestBackupManager:
    """Tests for BackupManager class."""

    def test_manager_initialization(self):
        """Test manager initialization with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BackupManager(work_dir=Path(tmpdir))
            assert manager.work_dir.exists()

    def test_create_backup_simple(self):
        """Test creating a simple backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source files
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()
            (source_dir / "test.txt").write_text("Hello World")

            # Create backup dir
            backup_dir = Path(tmpdir) / "backups"
            backup_dir.mkdir()

            # Configure backup
            config = BackupConfig(
                name="test-backup",
                source_path=source_dir,
                destination_path=backup_dir,
                backup_type=BackupType.FULL,
                compression=True,
            )

            # Create backup
            manager = BackupManager(work_dir=backup_dir)
            result = manager.create_backup(config)

            assert result.success is True
            assert result.job.backup_file is not None
            assert result.job.backup_file.exists()
            assert result.job.status.value == "completed"

    def test_list_backups_empty(self):
        """Test listing backups when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BackupManager(work_dir=Path(tmpdir))
            backups = manager.list_backups()
            assert len(backups) == 0

    def test_generate_backup_filename(self):
        """Test backup filename generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BackupConfig(
                name="test",
                source_path=Path("/tmp"),
                destination_path=Path(tmpdir),
                compression=True,
            )

            manager = BackupManager()
            filename = manager._generate_backup_filename(config)

            assert "test" in str(filename)
            assert filename.suffix == ".gz"
            assert filename.parent == Path(tmpdir)
