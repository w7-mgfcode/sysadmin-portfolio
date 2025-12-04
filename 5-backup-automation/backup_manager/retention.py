"""
Retention Manager - Megőrzési szabály kezelő.

Manages backup retention policies and cleanup.

Mentések megőrzési szabályainak kezelése és tisztítás.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import BackupMetadata, RetentionPolicy


class RetentionManager:
    """
    Retention manager osztály.

    Manages retention policies and determines which backups to keep or delete.
    """

    def __init__(self, policy: RetentionPolicy):
        """
        Inicializálja a retention managert.

        Args:
            policy: Megőrzési szabály konfiguráció.
        """
        self.policy = policy

    def apply_retention(
        self, backups: list[BackupMetadata], dry_run: bool = False
    ) -> tuple[list[BackupMetadata], list[BackupMetadata]]:
        """
        Megőrzési szabály alkalmazása.

        Args:
            backups: Mentések listája (legújabb elöl).
            dry_run: Csak szimulálás, nem töröl.

        Returns:
            Tuple (megőrzendő mentések, törlendő mentések).
        """
        if len(backups) <= self.policy.min_backups:
            return backups, []

        # Mentések kategorizálása időszakok szerint
        to_keep = set()
        now = datetime.now()

        # Daily backups (legutóbbi N nap)
        daily_cutoff = now - timedelta(days=self.policy.keep_daily)
        daily_backups = self._get_backups_in_range(backups, daily_cutoff, now)
        to_keep.update(daily_backups)

        # Weekly backups (egy hetente)
        weekly_cutoff = now - timedelta(weeks=self.policy.keep_weekly)
        weekly_backups = self._get_weekly_backups(
            backups, weekly_cutoff, daily_cutoff
        )
        to_keep.update(weekly_backups)

        # Monthly backups (egy havonta)
        monthly_cutoff = now - timedelta(days=30 * self.policy.keep_monthly)
        monthly_backups = self._get_monthly_backups(
            backups, monthly_cutoff, weekly_cutoff
        )
        to_keep.update(monthly_backups)

        # Yearly backups (egy évente)
        yearly_cutoff = now - timedelta(days=365 * self.policy.keep_yearly)
        yearly_backups = self._get_yearly_backups(
            backups, yearly_cutoff, monthly_cutoff
        )
        to_keep.update(yearly_backups)

        # Minimum backups biztosítása
        if len(to_keep) < self.policy.min_backups:
            # Legújabb backupok hozzáadása
            for backup in backups[: self.policy.min_backups]:
                to_keep.add(backup.backup_id)

        # Törlendők meghatározása
        to_keep_list = [b for b in backups if b.backup_id in to_keep]
        to_delete = [b for b in backups if b.backup_id not in to_keep]

        return to_keep_list, to_delete

    def _get_backups_in_range(
        self,
        backups: list[BackupMetadata],
        start: datetime,
        end: datetime,
    ) -> set[str]:
        """
        Mentések lekérdezése időintervallumban.

        Args:
            backups: Mentések listája.
            start: Kezdő időpont.
            end: Végző időpont.

        Returns:
            Backup ID-k halmaza.
        """
        return {
            b.backup_id
            for b in backups
            if start <= b.created_at <= end
        }

    def _get_weekly_backups(
        self,
        backups: list[BackupMetadata],
        start: datetime,
        end: datetime,
    ) -> set[str]:
        """
        Heti mentések kiválasztása (egy backup hetente).

        Args:
            backups: Mentések listája.
            start: Kezdő időpont.
            end: Végző időpont.

        Returns:
            Backup ID-k halmaza.
        """
        weekly_backups = {}  # week_number -> backup

        for backup in backups:
            if start <= backup.created_at <= end:
                # ISO week number
                week = backup.created_at.isocalendar()[1]
                year = backup.created_at.year

                key = (year, week)
                if key not in weekly_backups:
                    weekly_backups[key] = backup.backup_id

        return set(weekly_backups.values())

    def _get_monthly_backups(
        self,
        backups: list[BackupMetadata],
        start: datetime,
        end: datetime,
    ) -> set[str]:
        """
        Havi mentések kiválasztása (egy backup havonta).

        Args:
            backups: Mentések listája.
            start: Kezdő időpont.
            end: Végző időpont.

        Returns:
            Backup ID-k halmaza.
        """
        monthly_backups = {}  # (year, month) -> backup

        for backup in backups:
            if start <= backup.created_at <= end:
                key = (backup.created_at.year, backup.created_at.month)
                if key not in monthly_backups:
                    monthly_backups[key] = backup.backup_id

        return set(monthly_backups.values())

    def _get_yearly_backups(
        self,
        backups: list[BackupMetadata],
        start: datetime,
        end: datetime,
    ) -> set[str]:
        """
        Éves mentések kiválasztása (egy backup évente).

        Args:
            backups: Mentések listája.
            start: Kezdő időpont.
            end: Végző időpont.

        Returns:
            Backup ID-k halmaza.
        """
        yearly_backups = {}  # year -> backup

        for backup in backups:
            if start <= backup.created_at <= end:
                year = backup.created_at.year
                if year not in yearly_backups:
                    yearly_backups[year] = backup.backup_id

        return set(yearly_backups.values())

    def cleanup_old_backups(
        self,
        backup_dir: Path,
        config_name: Optional[str] = None,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """
        Régi mentések tisztítása.

        Args:
            backup_dir: Mentések könyvtára.
            config_name: Konfiguráció név szűréshez.
            dry_run: Csak szimulálás.

        Returns:
            Statisztika dict (kept, deleted, total_size_freed).
        """
        # Metadata fájlok keresése
        backups = []
        for metadata_file in backup_dir.rglob("*.json"):
            try:
                metadata = BackupMetadata.model_validate_json(
                    metadata_file.read_text()
                )
                if config_name is None or metadata.config_name == config_name:
                    backups.append((metadata, metadata_file))
            except Exception:
                continue

        # Rendezés dátum szerint (legújabb elöl)
        backups.sort(key=lambda x: x[0].created_at, reverse=True)
        backup_objects = [b[0] for b in backups]

        # Retention alkalmazása
        to_keep, to_delete = self.apply_retention(backup_objects, dry_run)

        # Törlés végrehajtása
        deleted_count = 0
        total_size_freed = 0

        if not dry_run:
            for metadata in to_delete:
                # Backup fájl és metadata törlése
                backup_file = self._find_backup_file(backup_dir, metadata.backup_id)
                if backup_file and backup_file.exists():
                    total_size_freed += backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_count += 1

                # Metadata fájl törlése
                metadata_file = backup_file.with_suffix(backup_file.suffix + ".json")
                if metadata_file.exists():
                    metadata_file.unlink()

        return {
            "kept": len(to_keep),
            "deleted": len(to_delete) if not dry_run else 0,
            "would_delete": len(to_delete) if dry_run else 0,
            "total_size_freed": total_size_freed,
        }

    def _find_backup_file(self, backup_dir: Path, backup_id: str) -> Optional[Path]:
        """
        Backup fájl keresése ID alapján.

        Args:
            backup_dir: Mentések könyvtára.
            backup_id: Backup azonosító.

        Returns:
            Backup fájl útvonala vagy None.
        """
        for metadata_file in backup_dir.rglob("*.json"):
            try:
                metadata = BackupMetadata.model_validate_json(
                    metadata_file.read_text()
                )
                if metadata.backup_id == backup_id:
                    # Metadata fájlból visszafejtjük a backup fájl nevét
                    backup_file = metadata_file.with_suffix("")
                    # .tar.gz vagy .tar kiterjesztés
                    if backup_file.suffix == ".tar":
                        return backup_file
                    elif backup_file.with_suffix("").suffix == ".tar":
                        return backup_file.with_suffix("")
                    return backup_file
            except Exception:
                continue
        return None
