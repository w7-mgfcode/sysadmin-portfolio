# SysAdmin Toolkit

## Áttekintés / Overview

Python és Bash alapú rendszergazda eszköztár log elemzéshez, rendszer monitorozáshoz, lemezterület analízishez és szolgáltatás kezeléshez.

Python and Bash based system administration toolkit for log analysis, system monitoring, disk space analysis, and service management.

## Funkciók / Features

### Python Toolkit

- **Log Analyzer** - Syslog és auth.log elemzés
  - Syslog formátum parsing (RFC 3164)
  - Bejelentkezés statisztikák (sikeres/sikertelen)
  - Hibaüzenet aggregáció
  - Programonkénti bontás

- **System Health** - Rendszer állapot monitorozás
  - CPU használat és load average
  - Memória és swap monitorozás
  - Lemez partíciók állapota
  - Top folyamatok listázása

- **Disk Analyzer** - Lemezterület elemzés
  - Könyvtár méret analízis
  - Nagy fájlok keresése
  - Fájlrendszer használat

- **Service Manager** - Szolgáltatás kezelés
  - Systemd szolgáltatások státusza
  - Kritikus szolgáltatások ellenőrzése
  - Szolgáltatás naplók lekérdezése

### Bash Scripts

- **system-report.sh** - Átfogó rendszer riport generálása
- **log-cleanup.sh** - Log fájlok tisztítása retention policy alapján

## Telepítés / Installation

```bash
# Virtuális környezet aktiválása / Activate virtual environment
source venv/bin/activate

# Függőségek már telepítve vannak / Dependencies are already installed
# psutil, typer, rich, pydantic
```

## Használat / Usage

### CLI Interface

```bash
# A projekt gyökérből / From project root
cd 1-sysadmin-toolkit

# Rendszer állapot / System health
python -m toolkit health

# Top folyamatok / Top processes
python -m toolkit processes --count 10 --sort cpu

# Log elemzés / Log analysis
python -m toolkit logs /var/log/syslog

# Lemez használat / Disk usage
python -m toolkit disk /

# Nagy fájlok keresése / Find large files
python -m toolkit large-files /var/log --min-size 100 --count 20

# Könyvtár méretek / Directory sizes
python -m toolkit dir-sizes /home

# Szolgáltatások listázása / List services
python -m toolkit services --state running

# Szolgáltatás státusz / Service status
python -m toolkit service nginx

# Kritikus szolgáltatások ellenőrzése / Check critical services
python -m toolkit check-services sshd nginx mysql
```

### Bash Scripts

```bash
# Rendszer riport generálása / Generate system report
./scripts/system-report.sh /tmp/report.txt

# Log tisztítás előnézet / Log cleanup preview
./scripts/log-cleanup.sh --dry-run --days 30

# Log tisztítás végrehajtás / Execute log cleanup
./scripts/log-cleanup.sh --days 7 --size 500
```

### Python API

```python
from toolkit import (
    get_system_health,
    analyze_logs,
    find_large_files,
    check_critical_services,
)

# Rendszer egészség / System health
health = get_system_health()
print(f"CPU: {health.cpu_percent}%")
print(f"Memory: {health.memory_percent}%")

# Log elemzés / Log analysis
result = analyze_logs("/var/log/syslog")
print(f"Errors: {result.error_count}")
print(f"Failed logins: {result.failed_logins}")

# Nagy fájlok / Large files
files = find_large_files("/var/log", min_size_bytes=100*1024*1024)
for f in files:
    print(f"{f.path}: {f.size_bytes} bytes")

# Szolgáltatások / Services
services = check_critical_services(["nginx", "sshd"])
for name, status in services.items():
    print(f"{name}: {status.state.value}")
```

## Könyvtárstruktúra / Directory Structure

```
1-sysadmin-toolkit/
├── README.md                    # Ez a dokumentum / This document
├── toolkit/
│   ├── __init__.py             # Package exports
│   ├── __main__.py             # CLI entry point
│   ├── cli.py                  # Typer CLI commands
│   ├── models.py               # Pydantic models
│   ├── log_analyzer.py         # Log analysis tools
│   ├── system_health.py        # System monitoring
│   ├── disk_analyzer.py        # Disk space analysis
│   └── service_manager.py      # Systemd service management
└── scripts/
    ├── system-report.sh        # System report generator
    └── log-cleanup.sh          # Log cleanup script
```

## CLI Parancsok / CLI Commands

| Parancs / Command | Leírás / Description |
|-------------------|----------------------|
| `health` | Rendszer egészségi állapot / System health status |
| `processes` | Top folyamatok / Top processes |
| `logs` | Log fájl elemzés / Log file analysis |
| `disk` | Lemez használat / Disk usage |
| `large-files` | Nagy fájlok keresése / Find large files |
| `dir-sizes` | Könyvtár méretek / Directory sizes |
| `services` | Szolgáltatások listázása / List services |
| `service` | Szolgáltatás részletek / Service details |
| `check-services` | Kritikus szolgáltatások / Critical services check |

## Modellek / Models

### LogEntry
Log bejegyzés reprezentációja timestamp-el, host névvel, programmal és üzenettel.

### LogAnalysisResult
Elemzési eredmény hibaszámmal, warning számmal, bejelentkezési statisztikákkal.

### SystemHealth
Rendszer állapot CPU, memória, lemez és load információkkal.

### DiskUsage
Lemez partíció használati adatok.

### ProcessInfo
Folyamat információ CPU és memória használattal.

### ServiceStatus
Systemd szolgáltatás státusz.

## Tesztek / Tests

```bash
# Tesztek futtatása / Run tests
pytest tests/test_sysadmin_toolkit/ -v

# Coverage riport / Coverage report
pytest tests/test_sysadmin_toolkit/ --cov=toolkit
```

## Licenc / License

MIT License
