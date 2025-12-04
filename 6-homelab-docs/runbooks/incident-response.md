# Incident Response Runbook / Incidenskezelési Runbook

## Áttekintés / Overview

Ez a runbook leírja az incidensek kezelési folyamatát.
This runbook describes the incident handling process.

## Súlyossági Szintek / Severity Levels

| Szint / Level | Név / Name | Leírás / Description | Válaszidő / Response Time |
|---------------|------------|---------------------|--------------------------|
| P0 | Critical | Teljes szolgáltatáskiesés / Complete service outage | 15 perc |
| P1 | High | Jelentős funkció nem elérhető / Major function unavailable | 1 óra |
| P2 | Medium | Korlátozott hatás / Limited impact | 4 óra |
| P3 | Low | Minimális hatás / Minimal impact | 1 nap |

## P0 - Critical Incident / Kritikus Incidens

### Jellemzők / Characteristics
- Prometheus nem elérhető / Prometheus unreachable
- Grafana teljes kiesés / Grafana complete outage
- Több szerver offline
- Hálózati kapcsolat megszakadás

### Válaszlépések / Response Steps

#### 1. Azonnali Értékelés / Immediate Assessment (0-5 perc)
```bash
# Szerverek elérhetőségének ellenőrzése / Check server reachability
ping 192.168.10.10  # Monitoring server
ping 192.168.10.20  # Docker host

# Szolgáltatások állapota / Service status
systemctl status prometheus
systemctl status grafana-server
docker ps

# Erőforrások ellenőrzése / Check resources
df -h
free -m
top -b -n 1 | head -20
```

#### 2. Szolgáltatás Újraindítás / Service Restart (5-10 perc)
```bash
# Prometheus újraindítása / Restart Prometheus
docker-compose -f /path/to/docker-compose.yml restart prometheus

# Grafana újraindítása / Restart Grafana
docker-compose restart grafana

# Állapot ellenőrzése / Check status
docker-compose ps
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

#### 3. Naplók Ellenőrzése / Log Review (10-15 perc)
```bash
# Docker container naplók / Docker container logs
docker-compose logs --tail=100 prometheus
docker-compose logs --tail=100 grafana

# Rendszer naplók / System logs
journalctl -u prometheus -n 100
tail -100 /var/log/syslog | grep -i error
```

#### 4. Eszkaláció / Escalation
Ha a probléma 15 percen belül nem oldódik meg:
- Értesítsd a backup rendszergazdát
- Készíts részletes incident riportot
- Dokumentáld a hibát és a végzett lépéseket

## P1 - High Severity / Magas Súlyosság

### Jellemzők / Characteristics
- Egy fő szolgáltatás nem elérhető
- Monitoring gaps (részleges adatvesztés)
- Container újraindulások

### Válaszlépések / Response Steps

#### 1. Probléma Azonosítás / Problem Identification
```bash
# Alert ellenőrzés / Check alerts
curl http://localhost:9093/api/v2/alerts

# Container státusz / Container status
docker ps -a
docker stats --no-stream

# Resource check
df -h
free -m
```

#### 2. Helyreállítás / Recovery
```bash
# Container restart
docker-compose restart <service-name>

# Konfiguráció reload / Reload configuration
curl -X POST http://localhost:9090/-/reload

# Log analízis / Log analysis
python -m toolkit logs /var/log/syslog
```

## P2 - Medium Severity / Közepes Súlyosság

### Jellemzők / Characteristics
- Nem kritikus alert
- Teljesítmény degradáció
- Nem esszenciális szolgáltatás hiba

### Válaszlépések / Response Steps

#### 1. Monitorozás / Monitoring
```bash
# Rendszer állapot / System health
python -m toolkit health

# Top folyamatok / Top processes
python -m toolkit processes --count 20

# Disk használat / Disk usage
python -m toolkit disk /
```

#### 2. Javítás Ütemezése / Schedule Fix
- Dokumentáld a hibát
- Tervezz javítást következő karbantartási ablakra
- Készíts változtatási tervet

## Kommunikációs Sablon / Communication Template

### Incidensnyitás / Incident Opening

```
INCIDENT ID: INC-YYYYMMDD-XXX
SEVERITY: [P0/P1/P2/P3]
START TIME: YYYY-MM-DD HH:MM:SS
AFFECTED SERVICE: [Service name]

DESCRIPTION / LEÍRÁS:
[Brief description in Hungarian and English]

IMPACT / HATÁS:
[Who/what is affected]

ACTIONS TAKEN / VÉGZETT LÉPÉSEK:
1. [First action]
2. [Second action]

STATUS: [INVESTIGATING / IDENTIFIED / RESOLVING / RESOLVED]
```

### Incidenzárás / Incident Closing

```
INCIDENT ID: INC-YYYYMMDD-XXX
RESOLUTION TIME: YYYY-MM-DD HH:MM:SS
DURATION: XX minutes

ROOT CAUSE / KIVÁLTÓ OK:
[Detailed root cause analysis]

RESOLUTION / MEGOLDÁS:
[What was done to fix]

PREVENTION / MEGELŐZÉS:
[How to prevent in future]

LESSONS LEARNED / TANULSÁGOK:
[Key takeaways]
```

## Eszkalációs Mátrix / Escalation Matrix

| Szint / Level | Idő / Time | Művelet / Action |
|---------------|-----------|------------------|
| 1 | 0-15 min | Elsődleges rendszergazda / Primary admin |
| 2 | 15-30 min | Backup rendszergazda / Backup admin |
| 3 | 30-60 min | Külső támogatás / External support |

## Post-Mortem Sablon / Post-Mortem Template

1. **Incident Összefoglaló / Summary**
   - Mi történt? / What happened?
   - Mikor? / When?
   - Mennyi ideig? / How long?

2. **Időrend / Timeline**
   - HH:MM - Esemény 1
   - HH:MM - Esemény 2

3. **Kiváltó Ok / Root Cause**
   - Miért történt? / Why did it happen?

4. **Hatás / Impact**
   - Kik érintettek? / Who was affected?
   - Milyen következmények? / What consequences?

5. **Megoldás / Resolution**
   - Mit tettünk? / What did we do?
   - Működött? / Did it work?

6. **Megelőzés / Prevention**
   - Hogyan előzhető meg? / How to prevent?
   - Milyen változtatások? / What changes needed?

7. **Tanulságok / Lessons Learned**
   - Mit tanultunk? / What did we learn?
   - Javítási lehetőségek / Improvement opportunities
