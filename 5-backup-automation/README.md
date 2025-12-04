# Backup Automation

## Áttekintés / Overview

Automatizált mentési rendszer Python és Bash eszközökkel, retention policy-val, ellenőrzéssel és helyreállítással.

Automated backup system with Python and Bash tools, including retention policies, verification, and restoration.

## Funkciók / Features

### Python Backup Manager

- **Backup Creation** - Teljes, inkrementális, differenciális mentések
  - Tar/gzip tömörítés
  - Metadata tárolás JSON formátumban
  - SHA256 checksum generálás
  - Pre/post backup scriptek támogatása

- **Retention Management** - Automatikus mentés tisztítás
  - Napi mentések megőrzése (X nap)
  - Heti mentések megőrzése (X hét)
  - Havi mentések megőrzése (X hónap)
  - Éves mentések megőrzése (X év)
  - Minimum mentések számának biztosítása

- **Backup Verification** - Integritás ellenőrzés
  - Checksum validálás
  - Tarfile integritás ellenőrzés
  - Kibonthatóság tesztelés
  - Részletes hibajelentés

- **Restore** - Mentés visszaállítás
  - Biztonságos kibontás
  - Path traversal védelem

### Bash Scripts

- **backup-files.sh** - Könyvtár mentés tar/gzip-pel

## Telepítés / Installation

```bash
# Virtuális környezet aktiválása / Activate virtual environment
source venv/bin/activate

# Függőségek már telepítve vannak / Dependencies are already installed
```

## Használat / Usage

### Python API

```python
from pathlib import Path
from backup_manager import BackupManager, BackupConfig, RetentionPolicy, BackupVerifier

# Backup létrehozása / Create backup
config = BackupConfig(
    name="home-backup",
    source_path=Path("/home/user"),
    destination_path=Path("/backups"),
    compression=True,
    exclude_patterns=["*.log", "*.tmp", ".cache/*"],
    retention_policy=RetentionPolicy(
        keep_daily=7,
        keep_weekly=4,
        keep_monthly=6,
    ),
)

manager = BackupManager(work_dir=Path("/backups"))
result = manager.create_backup(config)

if result.success:
    print(f"Backup created: {result.job.backup_file}")
    print(f"Size: {result.job.size_bytes} bytes")
else:
    print(f"Backup failed: {result.message}")

# Mentések listázása / List backups
backups = manager.list_backups(config_name="home-backup")
for backup in backups:
    print(f"{backup.created_at}: {backup.size_bytes} bytes")

# Mentés ellenőrzése / Verify backup
verifier = BackupVerifier()
result = verifier.verify_backup(Path("/backups/home-backup_20250104.tar.gz"))

if result.is_valid:
    print("Backup is valid!")
else:
    print(f"Backup validation failed: {result.errors}")

# Mentés visszaállítása / Restore backup
manager.restore_backup(
    backup_file=Path("/backups/home-backup_20250104.tar.gz"),
    restore_path=Path("/restore"),
    overwrite=False,
)
```

### Bash Scripts

```bash
# Könyvtár mentése / Backup directory
./scripts/backup-files.sh /home/user /backups home-backup

# Eredmény / Result:
# - /backups/home-backup_hostname_20250104_120000.tar.gz
# - /backups/home-backup_hostname_20250104_120000.tar.gz.sha256
```

### Retention Policy

```python
from backup_manager import RetentionManager, RetentionPolicy

# Retention policy konfiguráció
policy = RetentionPolicy(
    keep_daily=7,      # Utolsó 7 nap minden mentése
    keep_weekly=4,     # 4 hét, hetente 1 mentés
    keep_monthly=6,    # 6 hónap, havonta 1 mentés
    keep_yearly=1,     # 1 év, évente 1 mentés
    min_backups=3,     # Minimum 3 mentés mindig megőrzésre
)

manager = RetentionManager(policy)

# Dry run (csak szimulálás)
stats = manager.cleanup_old_backups(
    backup_dir=Path("/backups"),
    config_name="home-backup",
    dry_run=True,
)

print(f"Would keep: {stats['kept']} backups")
print(f"Would delete: {stats['would_delete']} backups")

# Tényleges tisztítás / Actual cleanup
stats = manager.cleanup_old_backups(
    backup_dir=Path("/backups"),
    config_name="home-backup",
    dry_run=False,
)

print(f"Deleted: {stats['deleted']} backups")
print(f"Space freed: {stats['total_size_freed']} bytes")
```

## Könyvtárstruktúra / Directory Structure

```
5-backup-automation/
├── README.md                    # Ez a dokumentum / This document
├── backup_manager/
│   ├── __init__.py             # Package exports
│   ├── models.py               # Pydantic models
│   ├── manager.py              # Backup manager
│   ├── retention.py            # Retention manager
│   └── verifier.py             # Backup verifier
├── scripts/
│   └── backup-files.sh         # File backup script
└── config/
    └── backup-config.example.json  # Example configuration
```

## Modellek / Models

### BackupConfig
Mentés konfiguráció forrás, cél, típus, tömörítés, exclusion patterns-ekkel.

### BackupJob
Mentési feladat végrehajtási információ státusszal, időzítéssel, eredményekkel.

### BackupMetadata
Mentés metadata JSON formátumban: ID, dátum, méret, checksum, config név.

### BackupResult
Mentési művelet eredménye success flag-gel, job objektummal, üzenetekkel.

### RetentionPolicy
Megőrzési szabályok napi, heti, havi, éves mentésekre.

### VerificationResult
Ellenőrzési eredmény érvényesség, kibonthatóság, checksum állapottal.

## Cron Ütemezés / Cron Scheduling

```bash
# Napi mentés 2:00-kor / Daily backup at 2:00 AM
0 2 * * * /path/to/backup-files.sh /home/user /backups home-backup

# Heti tisztítás vasárnap 3:00-kor / Weekly cleanup Sunday at 3:00 AM
0 3 * * 0 python -m backup_manager cleanup --config home-backup
```

## Biztonsági Szempontok / Security Considerations

- **Path Traversal védelem** - Visszaállításnál ellenőrzés
- **Checksum validálás** - SHA256 integritás ellenőrzés
- **Permission handling** - Megfelelő jogosultságok beállítása
- **Script timeout** - Pre/post scriptek max 5 perc
- **Exclude patterns** - Érzékeny fájlok kizárása

## Tesztek / Tests

```bash
# Tesztek futtatása / Run tests
pytest tests/test_backup_automation/ -v

# 18 unit tests covering:
# - Models validation
# - Backup creation
# - Retention policy
# - Verification
```

## Licenc / License

MIT License
