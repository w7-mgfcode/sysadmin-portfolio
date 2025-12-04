# Server Inventory / Szerver Leltár

## Áttekintés / Overview

Homelab szerverek és szolgáltatások leltára.
Inventory of homelab servers and services.

## Fizikai Szerverek / Physical Servers

| Név / Name | IP Cím | CPU | RAM | Lemez / Disk | OS | Szerep / Role |
|------------|--------|-----|-----|--------------|----|--------------|
| monitoring-server | 192.168.10.10 | 4 cores | 8 GB | 500 GB SSD | Ubuntu 22.04 LTS | Monitoring Stack |
| docker-host | 192.168.10.20 | 8 cores | 16 GB | 1 TB SSD | Ubuntu 22.04 LTS | Container Host |
| backup-server | 192.168.10.30 | 4 cores | 8 GB | 2 TB HDD | Ubuntu 22.04 LTS | Backup Storage |

## Virtuális Gépek / Virtual Machines

| Név / Name | Hoszt / Host | vCPU | vRAM | vDisk | OS | Állapot / Status |
|------------|--------------|------|------|-------|----|-----------------|
| jumpserver | docker-host | 2 | 4 GB | 50 GB | Ubuntu 22.04 | Running |
| dev-workstation | docker-host | 4 | 8 GB | 100 GB | Ubuntu 22.04 | Running |

## Docker Containerek / Docker Containers

### Monitoring Stack (monitoring-server)

| Container | Image | Port | Verzió / Version | Állapot / Status |
|-----------|-------|------|-----------------|-----------------|
| prometheus | prom/prometheus | 9090 | v2.47.0 | Running |
| grafana | grafana/grafana | 3000 | v10.1.0 | Running |
| alertmanager | prom/alertmanager | 9093 | v0.26.0 | Running |
| node-exporter | prom/node-exporter | 9100 | v1.6.1 | Running |
| blackbox-exporter | prom/blackbox-exporter | 9115 | v0.24.0 | Running |
| cadvisor | gcr.io/cadvisor/cadvisor | 8080 | v0.47.2 | Running |

### Application Stack (docker-host)

| Container | Image | Port | Leírás / Description |
|-----------|-------|------|---------------------|
| Example | - | - | Placeholder for applications |

## Hálózati Eszközök / Network Devices

| Eszköz / Device | IP Cím | Típus / Type | Modell / Model | Szerep / Role |
|----------------|--------|--------------|----------------|---------------|
| fw-01 | 192.168.1.1 | Firewall | Generic | Gateway/Firewall |
| sw-core-01 | 192.168.1.2 | Switch | Managed L3 | Core Switch |
| ap-office-01 | 192.168.1.10 | Access Point | Wireless | WiFi Coverage |

## Szolgáltatások / Services

### Kritikus Szolgáltatások / Critical Services

| Szolgáltatás / Service | Szerver / Server | Port | Monitorozva / Monitored |
|------------------------|------------------|------|------------------------|
| Prometheus | monitoring-server | 9090 | ✅ |
| Grafana | monitoring-server | 3000 | ✅ |
| SSH | All servers | 22 | ✅ |
| Docker | docker-host | 2376 | ✅ |

### Mentési Ütemezés / Backup Schedule

| Szerver / Server | Adat / Data | Gyakoriság / Frequency | Megőrzés / Retention |
|------------------|-------------|------------------------|---------------------|
| monitoring-server | /etc, /var/lib/grafana | Napi / Daily | 7 nap |
| docker-host | Docker volumes | Napi / Daily | 14 nap |
| backup-server | Config files | Heti / Weekly | 30 nap |

## Karbantartási Ablak / Maintenance Windows

| Nap / Day | Időpont / Time | Típus / Type | Leírás / Description |
|-----------|---------------|--------------|---------------------|
| Szerda / Wednesday | 02:00-04:00 | Tervezett / Scheduled | Rendszer frissítések / System updates |
| Vasárnap / Sunday | 03:00-05:00 | Mentés / Backup | Heti teljes mentés / Weekly full backup |

## Elérhetőségek / Access Points

### Web Interfészek / Web Interfaces

| Szolgáltatás / Service | URL | Hitelesítés / Auth |
|------------------------|-----|-------------------|
| Grafana | http://192.168.10.10:3000 | Username/Password |
| Prometheus | http://192.168.10.10:9090 | None (internal) |
| Alertmanager | http://192.168.10.10:9093 | None (internal) |

### SSH Hozzáférés / SSH Access

```bash
# Monitoring szerver / Monitoring server
ssh admin@192.168.10.10

# Docker host
ssh admin@192.168.10.20

# Jump server-en keresztül / Through jump server
ssh -J admin@192.168.20.20 admin@192.168.10.10
```

## Dokumentáció Frissítés / Documentation Updates

| Dátum / Date | Szerző / Author | Változás / Change |
|--------------|----------------|-------------------|
| 2025-12-04 | Claude Code | Kezdeti dokumentáció / Initial documentation |

## Kapcsolattartók / Contacts

| Szerep / Role | Név / Name | Elérhetőség / Contact |
|---------------|------------|----------------------|
| Rendszergazda / System Administrator | Portfolio Owner | portfolio@example.com |
| Mentés Felelős / Backup Responsible | Portfolio Owner | portfolio@example.com |
