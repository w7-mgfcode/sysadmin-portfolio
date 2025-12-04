# SysAdmin Portfolio - System Administrator Toolkit

> **🇬🇧 English below** | **🇭🇺 Magyar verzió lent**

---

## 🇬🇧 English Version

### Overview

A comprehensive system administrator portfolio demonstrating professional skills in:

- **Network Monitoring** - ICMP ping, SNMP queries, port scanning (Python)
- **Infrastructure Management** - Docker, Prometheus, Grafana monitoring stack
- **Microsoft 365 Administration** - PowerShell automation with Graph API
- **Backup & Recovery** - Automated backup scripts with retention policies
- **Documentation** - Professional runbooks, diagrams, and procedures

### Portfolio Components

| Component | Description | Technologies |
|-----------|-------------|--------------|
| 🔧 SysAdmin Toolkit | System utilities and monitoring scripts | Python, Bash |
| 📊 Infra Monitoring | Complete monitoring stack | Docker, Prometheus, Grafana |
| 🌐 Network Health Checker | Network diagnostics and SNMP monitoring | Python, pysnmp, ping3 |
| 💼 M365 Admin Scripts | Microsoft 365 automation | PowerShell, Graph API |
| 💾 Backup Automation | Backup framework with retention | Python, Bash, Cron |
| 📚 Homelab Docs | Professional documentation | Markdown, Mermaid |

### Quick Start

```bash
# Clone the repository
git clone https://github.com/w7-mgfcode/sysadmin-portfolio.git
cd sysadmin-portfolio

# Setup Python virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run network health checker
python -m network_health_checker.cli --help

# Run SysAdmin toolkit
python -m toolkit health

# Start monitoring stack
cd 2-infra-monitoring && docker-compose up -d
```

### Features Showcase

#### 🌐 Network Health Checker
```bash
# Ping monitoring with batch processing
python -m network_health_checker.cli ping 8.8.8.8 --count 10

# Port scanning
python -m network_health_checker.cli scan 192.168.1.1 --ports 22,80,443

# DNS queries (all record types)
python -m network_health_checker.cli dns google.com

# SNMP device queries
python -m network_health_checker.cli snmp 192.168.1.1 --community public

# Subnet calculations
python -m network_health_checker.cli subnet 192.168.1.0/24
```

#### 🔧 SysAdmin Toolkit
```bash
# System health monitoring
python -m toolkit health
python -m toolkit processes --count 10 --sort cpu

# Log analysis
python -m toolkit logs /var/log/syslog

# Disk analysis
python -m toolkit large-files /var/log --min-size 100

# Service management
python -m toolkit services --state running
python -m toolkit check-services sshd nginx
```

#### 📊 Infrastructure Monitoring
```bash
# Start the monitoring stack
cd 2-infra-monitoring
docker-compose up -d

# Access:
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090
# - Alertmanager: http://localhost:9093
```

#### 💾 Backup Automation
```python
from backup_manager import BackupManager, BackupConfig, RetentionPolicy

config = BackupConfig(
    name="home-backup",
    source_path="/home/user",
    destination_path="/backups",
    retention_policy=RetentionPolicy(keep_daily=7, keep_weekly=4)
)

manager = BackupManager()
result = manager.create_backup(config)
```

#### 💼 M365 Admin Scripts
```powershell
# Connect to Microsoft 365
.\4-m365-admin-scripts\common\Connect-M365.ps1
Connect-M365Services

# Get users, groups, licenses
.\users\Get-M365Users.ps1 -ExportPath users.csv
.\groups\Get-M365Groups.ps1 -IncludeMembers
.\licenses\Get-M365Licenses.ps1
.\reports\Get-M365InactiveUsers.ps1 -DaysInactive 90
```

### Project Structure

```
sysadmin-portfolio/
├── 1-sysadmin-toolkit/              # System administration utilities
│   ├── toolkit/                     # Python package
│   │   ├── log_analyzer.py         # Syslog/auth.log parsing
│   │   ├── system_health.py        # CPU/memory/disk monitoring
│   │   ├── disk_analyzer.py        # Disk space analysis
│   │   ├── service_manager.py      # Systemd service management
│   │   └── cli.py                  # Typer CLI interface
│   └── scripts/                     # Bash scripts
│       ├── system-report.sh        # System report generator
│       └── log-cleanup.sh          # Log cleanup with retention
│
├── 2-infra-monitoring/              # Complete monitoring stack
│   ├── docker-compose.yml          # 6 services stack definition
│   ├── prometheus/                  # Prometheus config
│   │   ├── prometheus.yml          # Scrape configs
│   │   └── alerts/                 # 40+ alert rules
│   ├── grafana/                    # Grafana config
│   │   ├── provisioning/           # Auto-provisioning
│   │   └── dashboards/             # 3 pre-built dashboards
│   ├── alertmanager/               # Alert routing
│   └── blackbox/                   # Endpoint probes
│
├── network_health_checker/          # Network diagnostics (renamed from 3-)
│   ├── models.py                   # Pydantic v2 models
│   ├── config.py                   # Environment config
│   ├── network_tools/              # Network utilities
│   │   ├── ping_monitor.py         # ICMP ping (batch)
│   │   ├── port_scanner.py         # TCP port scanning
│   │   ├── dns_lookup.py           # DNS all record types
│   │   ├── subnet_calculator.py    # IP/subnet calculations
│   │   ├── snmp_query.py           # SNMP v2c (async)
│   │   └── network_info.py         # Local network info
│   └── cli.py                      # Typer CLI
│
├── 4-m365-admin-scripts/            # Microsoft 365 automation
│   ├── common/                      # Connection module
│   ├── users/                       # User management
│   ├── groups/                      # Group management
│   ├── licenses/                    # License reporting
│   └── reports/                     # Inactive users, etc.
│
├── 5-backup-automation/             # Backup framework
│   ├── backup_manager/              # Python package
│   │   ├── manager.py              # Backup creation
│   │   ├── retention.py            # Retention policies
│   │   └── verifier.py             # Integrity checks
│   ├── scripts/                     # Bash scripts
│   └── config/                      # Configuration examples
│
├── 6-homelab-docs/                  # Professional documentation
│   ├── architecture/                # Network diagrams
│   ├── inventory/                   # Server inventory
│   ├── runbooks/                    # Incident response
│   └── templates/                   # Change requests
│
├── tests/                           # 226+ unit tests
│   ├── test_network_health_checker/ # 118 tests
│   ├── test_sysadmin_toolkit/      # 90 tests
│   └── test_backup_automation/     # 18 tests
│
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Project configuration
└── README.md                        # This file
```

### Project Statistics

| Metric | Count |
|--------|-------|
| Python Modules | 15+ |
| PowerShell Scripts | 5 |
| Bash Scripts | 4 |
| Docker Services | 6 |
| Unit Tests | 226+ |
| Grafana Dashboards | 3 |
| Alert Rules | 40+ |
| Lines of Code | 5000+ |

### Technologies Used

**Languages:**
- Python 3.12 (Pydantic v2, FastAPI patterns)
- PowerShell 7
- Bash

**Frameworks & Libraries:**
- **Python:** psutil, typer, rich, pydantic, pysnmp, dnspython, ping3
- **Monitoring:** Prometheus, Grafana, Alertmanager, Node Exporter, cAdvisor, Blackbox Exporter
- **M365:** Microsoft.Graph PowerShell SDK
- **Testing:** pytest, pytest-mock, pytest-asyncio

**Infrastructure:**
- Docker & Docker Compose
- Linux (Ubuntu 22.04)
- Git & GitHub workflows

### Requirements

- Python 3.9+
- Docker & Docker Compose v2.0+
- PowerShell 7+ (for M365 scripts)
- Linux host (for full functionality)

### License

MIT License - see [LICENSE](LICENSE) file

---

## 🇭🇺 Magyar Verzió

### Áttekintés

Átfogó rendszergazda portfólió, amely bemutatja a professzionális képességeket:

- **Hálózat Monitorozás** - ICMP ping, SNMP lekérdezések, port szkennelés (Python)
- **Infrastruktúra Menedzsment** - Docker, Prometheus, Grafana monitoring stack
- **Microsoft 365 Adminisztráció** - PowerShell automatizálás Graph API-val
- **Mentés és Helyreállítás** - Automatizált mentési scriptek megőrzési szabályokkal
- **Dokumentáció** - Professzionális runbook-ok, diagramok és eljárások

### Portfólió Komponensek

| Komponens | Leírás | Technológiák |
|-----------|--------|--------------|
| 🔧 SysAdmin Toolkit | Rendszer eszközök és monitorozó scriptek | Python, Bash |
| 📊 Infra Monitoring | Teljes monitorozási stack | Docker, Prometheus, Grafana |
| 🌐 Network Health Checker | Hálózati diagnosztika és SNMP | Python, pysnmp, ping3 |
| 💼 M365 Admin Scripts | Microsoft 365 automatizálás | PowerShell, Graph API |
| 💾 Backup Automation | Mentési keretrendszer megőrzéssel | Python, Bash, Cron |
| 📚 Homelab Docs | Professzionális dokumentáció | Markdown, Mermaid |

### Gyors Kezdés

```bash
# Repository klónozása
git clone https://github.com/w7-mgfcode/sysadmin-portfolio.git
cd sysadmin-portfolio

# Python virtuális környezet beállítása
python -m venv venv
source venv/bin/activate  # Linux/Mac
# vagy: venv\Scripts\activate  # Windows

# Függőségek telepítése
pip install -r requirements.txt

# Hálózati eszköz futtatása
python -m network_tools.cli --help
```

### Álláshirdetés Követelményei Lefedve

Ez a portfólió bemutatja a következő kompetenciákat:

- ✅ **Windows kliensek** rendszergazdai szintű ismerete
- ✅ **Microsoft 365** rendszergazdai szintű ismerete
- ✅ **TCP/IP** hálózati ismeretek
- ✅ **Mikrotik, Ubiquiti, Omada** eszközök (SNMP monitorozás)
- ✅ **Zabbix, Prometheus, Grafana** monitorozási rendszerek
- ✅ **Linux** operációs rendszer ismerete
- ✅ **SQL** ismeretek (log analízis, monitoring)
- ✅ **Python** scriptelési tapasztalat
- ✅ **Dokumentációk** készítése
- ✅ **Mentések** kezelése

### Követelmények

- Python 3.9+
- Docker & Docker Compose
- PowerShell 7+ (M365 scriptekhez)

### Licenc

MIT Licenc - lásd [LICENSE](LICENSE) fájl

---

## Author / Szerző

**Portfolio for:** Hansa Invest Zrt. - System Administrator Position

---

*🤖 Generated with [Claude Code](https://claude.com/claude-code)*
