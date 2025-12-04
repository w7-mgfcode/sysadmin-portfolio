# Infra Monitoring Stack

## Áttekintés / Overview

Teljes körű infrastruktúra monitoring megoldás Docker Compose alapokon. A stack tartalmaz metrika gyűjtést, vizualizációt, riasztáskezelést és endpoint monitoring-ot.

Complete infrastructure monitoring solution based on Docker Compose. The stack includes metric collection, visualization, alert management, and endpoint monitoring.

## Architektúra / Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MONITORING STACK                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Grafana   │◄───│ Prometheus  │◄───│    Exporters        │ │
│  │   (3000)    │    │   (9090)    │    │                     │ │
│  └─────────────┘    └──────┬──────┘    │  - Node Exporter    │ │
│         │                  │           │    (9100)           │ │
│         │                  ▼           │  - cAdvisor         │ │
│         │           ┌─────────────┐    │    (8080)           │ │
│         └──────────►│Alertmanager │    │  - Blackbox         │ │
│                     │   (9093)    │    │    (9115)           │ │
│                     └─────────────┘    └─────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Komponensek / Components

| Szolgáltatás / Service | Port | Leírás / Description |
|------------------------|------|----------------------|
| Prometheus | 9090 | Metrika gyűjtés és tárolás / Metric collection and storage |
| Grafana | 3000 | Vizualizáció és dashboardok / Visualization and dashboards |
| Alertmanager | 9093 | Riasztás kezelés / Alert management |
| Node Exporter | 9100 | Host metrikák / Host metrics |
| Blackbox Exporter | 9115 | Endpoint monitoring (HTTP, ICMP, TCP) |
| cAdvisor | 8080 | Container metrikák / Container metrics |

## Gyors indítás / Quick Start

### Előfeltételek / Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+
- Linux host (Node Exporter és cAdvisor miatt / due to Node Exporter and cAdvisor)

### Indítás / Start

```bash
# A 2-infra-monitoring könyvtárban / In the 2-infra-monitoring directory
cd 2-infra-monitoring

# Stack indítása / Start the stack
docker-compose up -d

# Naplók megtekintése / View logs
docker-compose logs -f

# Szolgáltatás állapot / Service status
docker-compose ps
```

### Elérés / Access

- **Grafana**: http://localhost:3000
  - Alapértelmezett felhasználó / Default user: `admin`
  - Alapértelmezett jelszó / Default password: `admin`
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## Könyvtárstruktúra / Directory Structure

```
2-infra-monitoring/
├── docker-compose.yml          # Fő Docker Compose konfiguráció
├── README.md                   # Ez a dokumentum / This document
├── prometheus/
│   ├── prometheus.yml          # Prometheus konfiguráció
│   └── alerts/
│       └── alerts.yml          # Riasztási szabályok / Alert rules
├── alertmanager/
│   └── alertmanager.yml        # Alertmanager konfiguráció
├── blackbox/
│   └── blackbox.yml            # Blackbox Exporter konfiguráció
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── datasources.yml # Datasource konfiguráció
    │   └── dashboards/
    │       └── dashboards.yml  # Dashboard provider konfiguráció
    └── dashboards/
        ├── server-health.json  # Szerver egészség dashboard
        ├── docker-overview.json # Docker container dashboard
        └── network-overview.json # Hálózati monitoring dashboard
```

## Dashboardok / Dashboards

### Server Health / Szerver Egészség
- CPU használat és load average
- Memória használat és swap
- Lemez használat és I/O
- Hálózati forgalom és hibák

### Docker Overview / Docker Áttekintés
- Futó containerek száma
- Container CPU és memória használat
- Hálózati forgalom containerenként
- Filesystem I/O

### Network Overview / Hálózati Áttekintés
- HTTP endpoint státusz és válaszidő
- ICMP ping latency
- TCP port elérhetőség
- SSL tanúsítvány lejárat

## Riasztások / Alerts

### Host Alerts
| Alert | Súlyosság / Severity | Küszöb / Threshold |
|-------|---------------------|-------------------|
| HighCPUUsage | warning | >80% (5m) |
| CriticalCPUUsage | critical | >95% (2m) |
| HighMemoryUsage | warning | >80% (5m) |
| CriticalMemoryUsage | critical | >95% (2m) |
| LowDiskSpace | warning | <20% free |
| CriticalDiskSpace | critical | <10% free |

### Container Alerts
| Alert | Súlyosság / Severity | Küszöb / Threshold |
|-------|---------------------|-------------------|
| ContainerDown | warning | not seen for 1m |
| ContainerHighCPU | warning | >80% (5m) |
| ContainerHighMemory | warning | >80% of limit (5m) |

### Service Alerts
| Alert | Súlyosság / Severity | Küszöb / Threshold |
|-------|---------------------|-------------------|
| PrometheusDown | critical | down for 1m |
| GrafanaDown | critical | down for 1m |
| AlertmanagerDown | critical | down for 1m |
| HTTPEndpointDown | critical | probe failed for 1m |

### Network Alerts
| Alert | Súlyosság / Severity | Küszöb / Threshold |
|-------|---------------------|-------------------|
| ICMPProbeFailed | warning | failed for 2m |
| TCPConnectionFailed | critical | failed for 1m |
| HighNetworkTraffic | warning | >100 Mbps (5m) |

## Konfiguráció / Configuration

### Környezeti változók / Environment Variables

Hozz létre egy `.env` fájlt a docker-compose.yml mellett:
Create a `.env` file next to docker-compose.yml:

```bash
# Grafana admin beállítások / Grafana admin settings
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_password_here
GRAFANA_ROOT_URL=http://localhost:3000

# SMTP beállítások az email értesítésekhez / SMTP settings for email notifications
SMTP_PASSWORD=smtp_password_here
```

### Új scrape target hozzáadása / Adding New Scrape Targets

Szerkeszd a `prometheus/prometheus.yml` fájlt:
Edit the `prometheus/prometheus.yml` file:

```yaml
scrape_configs:
  - job_name: "my-new-service"
    static_configs:
      - targets: ["service-host:port"]
```

### Új endpoint monitoring / Adding Endpoint Monitoring

HTTP endpoint hozzáadása / Add HTTP endpoint:

```yaml
# prometheus/prometheus.yml - blackbox-http job
static_configs:
  - targets:
      - https://example.com
```

### Alertmanager értesítések / Alertmanager Notifications

Email értesítésekhez állítsd be az SMTP szervert az `alertmanager/alertmanager.yml` fájlban.
For email notifications, configure the SMTP server in `alertmanager/alertmanager.yml`.

Slack integráció / Slack integration:

```yaml
receivers:
  - name: "slack-notifications"
    slack_configs:
      - api_url: "${SLACK_WEBHOOK_URL}"
        channel: "#alerts"
        send_resolved: true
```

## Karbantartás / Maintenance

### Prometheus adatok törlése / Clearing Prometheus Data

```bash
docker-compose stop prometheus
docker volume rm prometheus-data
docker-compose up -d prometheus
```

### Konfiguráció újratöltése / Reloading Configuration

```bash
# Prometheus
curl -X POST http://localhost:9090/-/reload

# Alertmanager
curl -X POST http://localhost:9093/-/reload
```

### Backup

```bash
# Grafana dashboardok és beállítások / Grafana dashboards and settings
docker cp grafana:/var/lib/grafana ./grafana-backup

# Prometheus adatok / Prometheus data
docker cp prometheus:/prometheus ./prometheus-backup
```

## Hibaelhárítás / Troubleshooting

### Container nem indul / Container Won't Start

```bash
# Ellenőrizd a naplókat / Check logs
docker-compose logs [service-name]

# Ellenőrizd az erőforrásokat / Check resources
docker stats
```

### Prometheus nem gyűjti a metrikákat / Prometheus Not Collecting Metrics

1. Ellenőrizd a targets státuszát / Check targets status: http://localhost:9090/targets
2. Ellenőrizd a scrape konfigurációt / Check scrape config
3. Ellenőrizd a hálózati kapcsolatot / Check network connectivity

### Grafana nem mutat adatokat / Grafana Shows No Data

1. Ellenőrizd a datasource kapcsolatot / Check datasource connection
2. Ellenőrizd az időintervallumot / Check time range
3. Prometheus targets állapota / Prometheus targets status

## Bővítési lehetőségek / Extension Options

- **Loki**: Log aggregáció / Log aggregation
- **Tempo**: Distributed tracing
- **Pushgateway**: Batch job metrikák / Batch job metrics
- **Thanos**: Long-term storage és HA

## Licenc / License

MIT License
