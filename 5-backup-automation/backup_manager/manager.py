"""
Backup Manager - Mentés kezelő.

Main backup management functionality.

Fő mentés kezelési funkcionalitás.
"""

import hashlib
import json
import shutil
import socket
import subprocess
import tarfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    BackupConfig,
    BackupJob,
    BackupMetadata,
    BackupResult,
    BackupStatus,
    BackupType,
)


class BackupManager:
    """
    Backup manager osztály.

    Manages backup operations including creation, compression, and metadata.
    """

    def __init__(self, work_dir: Optional[Path] = None):
        """
        Inicializálja a backup managert.

        Args:
            work_dir: Munka könyvtár (alapértelmezett: /var/backups).
        """
        self.work_dir = Path(work_dir or "/var/backups")
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, config: BackupConfig) -> BackupResult:
        """
        Mentés létrehozása konfigurációból.

        Args:
            config: Mentés konfiguráció.

        Returns:
            BackupResult az eredménnyel.
        """
        # Job létrehozása
        job = BackupJob(
            job_id=str(uuid.uuid4()),
            config_name=config.name,
            backup_type=config.backup_type,
            started_at=datetime.now(),
            status=BackupStatus.RUNNING,
        )

        try:
            # Pre-backup script futtatása
            if config.pre_backup_script and config.pre_backup_script.exists():
                self._run_script(config.pre_backup_script)

            # Mentés fájl létrehozása
            backup_file = self._generate_backup_filename(config)
            job.backup_file = backup_file

            # Mentés típus alapján
            if config.backup_type == BackupType.FULL:
                self._create_full_backup(config, backup_file)
            elif config.backup_type == BackupType.INCREMENTAL:
                self._create_incremental_backup(config, backup_file)
            else:
                self._create_differential_backup(config, backup_file)

            # Metadata gyűjtése
            job.size_bytes = backup_file.stat().st_size
            job.files_count = self._count_files_in_archive(backup_file)
            job.finished_at = datetime.now()
            job.status = BackupStatus.COMPLETED

            # Duration számítása
            if job.finished_at:
                duration = (job.finished_at - job.started_at).total_seconds()
                job.duration_seconds = duration

            # Metadata mentése
            self._save_metadata(job, config)

            # Post-backup script futtatása
            if config.post_backup_script and config.post_backup_script.exists():
                self._run_script(config.post_backup_script)

            return BackupResult(
                success=True,
                job=job,
                message=f"Backup completed successfully: {backup_file}",
            )

        except Exception as e:
            job.status = BackupStatus.FAILED
            job.finished_at = datetime.now()
            job.error_message = str(e)

            return BackupResult(
                success=False,
                job=job,
                message=f"Backup failed: {e}",
            )

    def _create_full_backup(self, config: BackupConfig, output_file: Path) -> None:
        """
        Teljes mentés létrehozása.

        Args:
            config: Mentés konfiguráció.
            output_file: Kimeneti fájl útvonala.
        """
        mode = "w:gz" if config.compression else "w"

        with tarfile.open(output_file, mode) as tar:
            # Exclude patterns használata
            def filter_func(tarinfo):
                """Filter function for tarfile."""
                for pattern in config.exclude_patterns:
                    if Path(tarinfo.name).match(pattern):
                        return None
                return tarinfo

            tar.add(
                config.source_path,
                arcname=config.source_path.name,
                recursive=True,
                filter=filter_func,
            )

    def _create_incremental_backup(
        self, config: BackupConfig, output_file: Path
    ) -> None:
        """
        Inkrementális mentés létrehozása.

        Args:
            config: Mentés konfiguráció.
            output_file: Kimeneti fájl útvonala.
        """
        # Reason: Egyszerűsített implementáció - teljes mentést csinál
        # Valós implementációban timestamp alapú változás detektálás kéne
        self._create_full_backup(config, output_file)

    def _create_differential_backup(
        self, config: BackupConfig, output_file: Path
    ) -> None:
        """
        Differenciális mentés létrehozása.

        Args:
            config: Mentés konfiguráció.
            output_file: Kimeneti fájl útvonala.
        """
        # Reason: Egyszerűsített implementáció - teljes mentést csinál
        self._create_full_backup(config, output_file)

    def _generate_backup_filename(self, config: BackupConfig) -> Path:
        """
        Mentés fájlnév generálása.

        Args:
            config: Mentés konfiguráció.

        Returns:
            Generált fájl útvonala.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = ".tar.gz" if config.compression else ".tar"
        filename = f"{config.name}_{timestamp}{extension}"

        # Destination path használata
        backup_dir = config.destination_path
        backup_dir.mkdir(parents=True, exist_ok=True)

        return backup_dir / filename

    def _count_files_in_archive(self, archive_path: Path) -> int:
        """
        Fájlok számának meghatározása archívumban.

        Args:
            archive_path: Archívum útvonala.

        Returns:
            Fájlok száma.
        """
        try:
            with tarfile.open(archive_path, "r") as tar:
                return len([m for m in tar.getmembers() if m.isfile()])
        except Exception:
            return 0

    def _save_metadata(self, job: BackupJob, config: BackupConfig) -> None:
        """
        Metadata mentése JSON fájlba.

        Args:
            job: Mentési feladat.
            config: Konfiguráció.
        """
        if not job.backup_file:
            return

        metadata = BackupMetadata(
            backup_id=job.job_id,
            created_at=job.started_at,
            config_name=config.name,
            backup_type=config.backup_type,
            source_path=str(config.source_path),
            hostname=socket.gethostname(),
            size_bytes=job.size_bytes or 0,
            files_count=job.files_count or 0,
            compression=config.compression,
            encryption=config.encryption,
            checksum=self._calculate_checksum(job.backup_file),
        )

        metadata_file = job.backup_file.with_suffix(
            job.backup_file.suffix + ".json"
        )
        metadata_file.write_text(metadata.model_dump_json(indent=2))

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Fájl checksum számítása SHA256-tal.

        Args:
            file_path: Fájl útvonala.

        Returns:
            Hexadecimális checksum.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _run_script(self, script_path: Path) -> None:
        """
        Script futtatása.

        Args:
            script_path: Script útvonala.

        Raises:
            subprocess.CalledProcessError: Ha a script hibával tér vissza.
        """
        subprocess.run(
            [str(script_path)],
            check=True,
            capture_output=True,
            timeout=300,  # 5 perc timeout
        )

    def list_backups(self, config_name: Optional[str] = None) -> list[BackupMetadata]:
        """
        Mentések listázása.

        Args:
            config_name: Szűrés konfiguráció név alapján.

        Returns:
            BackupMetadata objektumok listája.
        """
        backups = []

        # Összes metadata fájl keresése
        for metadata_file in self.work_dir.rglob("*.json"):
            try:
                metadata = BackupMetadata.model_validate_json(
                    metadata_file.read_text()
                )
                if config_name is None or metadata.config_name == config_name:
                    backups.append(metadata)
            except Exception:
                continue

        # Rendezés dátum szerint (legújabb elöl)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    def restore_backup(
        self, backup_file: Path, restore_path: Path, overwrite: bool = False
    ) -> bool:
        """
        Mentés visszaállítása.

        Args:
            backup_file: Mentés fájl útvonala.
            restore_path: Visszaállítási útvonal.
            overwrite: Létező fájlok felülírása.

        Returns:
            Sikeres volt-e.
        """
        try:
            restore_path.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_file, "r") as tar:
                # Biztonság: path traversal védelem
                for member in tar.getmembers():
                    if member.name.startswith("/") or ".." in member.name:
                        raise ValueError(f"Unsafe path in archive: {member.name}")

                tar.extractall(path=restore_path)

            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
