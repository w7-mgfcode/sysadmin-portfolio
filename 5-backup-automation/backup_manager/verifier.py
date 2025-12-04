"""
Backup Verifier - Mentés ellenőrző.

Verifies backup integrity and completeness.

Mentés integritás és teljességének ellenőrzése.
"""

import hashlib
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from .models import BackupMetadata, VerificationResult


class BackupVerifier:
    """
    Backup verifier osztály.

    Verifies backup file integrity, extractability, and checksums.
    """

    def verify_backup(self, backup_file: Path) -> VerificationResult:
        """
        Mentés ellenőrzése.

        Args:
            backup_file: Mentés fájl útvonala.

        Returns:
            VerificationResult az eredménnyel.
        """
        errors = []
        is_valid = True
        can_extract = False
        checksum_match = None

        # Fájl létezés ellenőrzése
        if not backup_file.exists():
            errors.append("Backup file does not exist")
            return VerificationResult(
                backup_file=backup_file,
                is_valid=False,
                can_extract=False,
                size_bytes=0,
                verified_at=datetime.now(),
                errors=errors,
            )

        size_bytes = backup_file.stat().st_size

        # Ellenőrző összeg validálás
        metadata_file = backup_file.with_suffix(backup_file.suffix + ".json")
        if metadata_file.exists():
            try:
                metadata = BackupMetadata.model_validate_json(
                    metadata_file.read_text()
                )
                actual_checksum = self._calculate_checksum(backup_file)
                checksum_match = actual_checksum == metadata.checksum

                if not checksum_match:
                    errors.append(
                        f"Checksum mismatch: expected {metadata.checksum}, got {actual_checksum}"
                    )
                    is_valid = False
            except Exception as e:
                errors.append(f"Failed to verify checksum: {e}")

        # Tarfile integritás ellenőrzés
        try:
            with tarfile.open(backup_file, "r") as tar:
                # Fájllista olvasás
                members = tar.getmembers()
                if len(members) == 0:
                    errors.append("Archive is empty")
                    is_valid = False
        except tarfile.TarError as e:
            errors.append(f"Invalid tar archive: {e}")
            is_valid = False

        # Kibonthatóság tesztelése
        if is_valid:
            can_extract = self._test_extraction(backup_file)
            if not can_extract:
                errors.append("Failed to extract archive")
                is_valid = False

        return VerificationResult(
            backup_file=backup_file,
            is_valid=is_valid,
            can_extract=can_extract,
            checksum_match=checksum_match,
            size_bytes=size_bytes,
            verified_at=datetime.now(),
            errors=errors,
        )

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

    def _test_extraction(self, backup_file: Path) -> bool:
        """
        Kibonthatóság tesztelése temp könyvtárba.

        Args:
            backup_file: Mentés fájl útvonala.

        Returns:
            Sikeres volt-e.
        """
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                with tarfile.open(backup_file, "r") as tar:
                    # Biztonság: csak néhány fájlt bontunk ki tesztként
                    members = tar.getmembers()[:5]
                    tar.extractall(path=tmpdir, members=members)
            return True
        except Exception:
            return False

    def verify_all_backups(self, backup_dir: Path) -> dict[str, VerificationResult]:
        """
        Összes mentés ellenőrzése könyvtárban.

        Args:
            backup_dir: Mentések könyvtára.

        Returns:
            Dict backup_id -> VerificationResult.
        """
        results = {}

        # Tarfile keresése
        for backup_file in backup_dir.rglob("*.tar*"):
            if backup_file.suffix == ".json":
                continue

            try:
                result = self.verify_backup(backup_file)
                # Backup ID kinyerése metadata-ból
                metadata_file = backup_file.with_suffix(backup_file.suffix + ".json")
                if metadata_file.exists():
                    metadata = BackupMetadata.model_validate_json(
                        metadata_file.read_text()
                    )
                    results[metadata.backup_id] = result
                else:
                    results[str(backup_file)] = result
            except Exception as e:
                # Hiba esetén is adjunk vissza eredményt
                results[str(backup_file)] = VerificationResult(
                    backup_file=backup_file,
                    is_valid=False,
                    can_extract=False,
                    size_bytes=0,
                    verified_at=datetime.now(),
                    errors=[f"Verification failed: {e}"],
                )

        return results
