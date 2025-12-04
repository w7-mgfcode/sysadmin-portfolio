# Homelab Documentation / Homelab Dokumentáció

## Áttekintés / Overview

Professzionális dokumentáció a homelab infrastruktúrához, beleértve architektúra diagramokat, leltárt, runbook-okat és sablonokat.

Professional documentation for homelab infrastructure including architecture diagrams, inventory, runbooks, and templates.

## Dokumentáció Struktúra / Documentation Structure

```
6-homelab-docs/
├── README.md                           # Ez a dokumentum / This document
├── architecture/
│   └── network-architecture.md        # Hálózati architektúra / Network architecture
├── inventory/
│   └── servers.md                     # Szerver leltár / Server inventory
├── runbooks/
│   └── incident-response.md           # Incidenskezelési runbook / Incident response
└── templates/
    └── change-request.md              # Változtatási kérelem sablon / Change request
```

## Architektúra / Architecture

### Hálózati Architektúra / Network Architecture

A `architecture/network-architecture.md` dokumentum tartalmazza:
- Hálózati topológia diagram (Mermaid)
- VLAN konfiguráció
- IP címtartományok
- Tűzfal szabályok
- DNS konfiguráció
- Port kiosztások

**Fő komponensek / Key components:**
- 5 VLAN (Servers, Management, Clients, IoT, Quarantine)
- Szegmentált hálózati zónák / Segmented network zones
- Firewall szabályok zónák között / Firewall rules between zones

## Leltár / Inventory

### Szerver Leltár / Server Inventory

A `inventory/servers.md` dokumentum tartalmazza:
- Fizikai szerverek listája / Physical servers list
- Virtuális gépek / Virtual machines
- Docker containerek / Docker containers
- Hálózati eszközök / Network devices
- Szolgáltatások és portok / Services and ports

**Nyomon követett információk / Tracked information:**
- IP címek / IP addresses
- Hardware specifikációk / Hardware specifications
- Szoftver verziók / Software versions
- Állapot és elérhetőség / Status and availability

## Runbook-ok / Runbooks

### Incidenskezelés / Incident Response

A `runbooks/incident-response.md` runbook tartalmazza:

**Súlyossági szintek / Severity levels:**
- P0 (Critical) - 15 perc válaszidő / 15 min response
- P1 (High) - 1 óra válaszidő / 1 hour response
- P2 (Medium) - 4 óra válaszidő / 4 hour response
- P3 (Low) - 1 nap válaszidő / 1 day response

**Minden szinthez / For each level:**
- Jellemző problémák / Typical problems
- Diagnosztikai parancsok / Diagnostic commands
- Helyreállítási lépések / Recovery steps
- Eszkalációs útvonal / Escalation path

**Kommunikációs sablonok / Communication templates:**
- Incidensnyitás / Incident opening
- Státusz frissítés / Status update
- Incidenzárás / Incident closing
- Post-mortem riport / Post-mortem report

## Sablonok / Templates

### Változtatási Kérelem / Change Request

A `templates/change-request.md` sablon tartalmazza:

**Szakaszok / Sections:**
1. Változtatás információk / Change information
2. Leírás és indoklás / Description and justification
3. Implementációs terv / Implementation plan
4. Ellenőrzési pontok / Verification points
5. Visszaállítási terv / Rollback plan
6. Kockázat értékelés / Risk assessment
7. Ütemezés / Scheduling
8. Kommunikáció / Communication
9. Jóváhagyás / Approval

**Használat / Usage:**
1. Másold le a sablont / Copy the template
2. Töltsd ki a mezőket / Fill in the fields
3. Kérj jóváhagyást / Request approval
4. Implementáld / Implement
5. Dokumentáld az eredményt / Document the result

## Használati Útmutató / Usage Guide

### Új Szerver Hozzáadása / Adding a New Server

1. **Dokumentáld a szervert / Document the server**
   - Frissítsd a `inventory/servers.md` fájlt
   - Add hozzá az IP címet, hardvert, OS-t

2. **Frissítsd a hálózati diagramot / Update network diagram**
   - Módosítsd az `architecture/network-architecture.md` fájlt
   - Adj hozzá új node-ot a Mermaid diagramhoz

3. **Konfiguráld a monitorozást / Configure monitoring**
   - Add hozzá a Prometheus target-hez
   - Készíts dashboard-ot Grafana-ban

### Incidens Kezelése / Handling an Incident

1. **Nyiss incidensriportot / Open incident report**
   - Használd a kommunikációs sablont
   - Azonosítsd a súlyossági szintet

2. **Kövesd a runbook-ot / Follow the runbook**
   - Nézd meg a `runbooks/incident-response.md` fájlt
   - Futtasd a diagnosztikai parancsokat

3. **Dokumentáld a megoldást / Document the solution**
   - Készíts post-mortem riportot
   - Frissítsd a runbook-ot ha szükséges

### Változtatás Kezdeményezése / Initiating a Change

1. **Töltsd ki a change request-et / Fill out change request**
   - Használd a `templates/change-request.md` sablont
   - Dokumentáld a változtatást részletesen

2. **Kérj jóváhagyást / Request approval**
   - Küldd el áttekintésre
   - Válaszolj a kérdésekre

3. **Implementáld / Implement**
   - Kövesd az implementációs tervet
   - Ellenőrizd minden lépésnél

4. **Zárás / Close**
   - Dokumentáld az eredményt
   - Frissítsd a leltárat ha szükséges

## Best Practices

### Dokumentáció Karbantartás / Documentation Maintenance

- **Rendszeres frissítés / Regular updates:** Minden változtatás után
- **Verziókezelés / Version control:** Git használata
- **Felülvizsgálat / Review:** Negyedévente
- **Pontosság / Accuracy:** Valós állapot tükrözése

### Diagram Karbantartás / Diagram Maintenance

- Használj Mermaid formátumot / Use Mermaid format
- Tartsd egyszerűnek / Keep it simple
- Frissítsd változtatások után / Update after changes
- Színkódolás konzisztens / Consistent color coding

### Runbook Karbantartás / Runbook Maintenance

- Teszteld a parancsokat / Test the commands
- Dokumentáld a változásokat / Document changes
- Add hozzá a tanulságokat / Add lessons learned
- Konkrét legyen / Be specific

## Referenciák / References

### Külső Dokumentáció / External Documentation

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Microsoft Graph API](https://docs.microsoft.com/graph/)
- [Docker Documentation](https://docs.docker.com/)

### Belső Dokumentáció / Internal Documentation

- [Monitoring Stack README](../2-infra-monitoring/README.md)
- [Network Health Checker](../network_health_checker/README.md)
- [SysAdmin Toolkit](../1-sysadmin-toolkit/README.md)
- [Backup Automation](../5-backup-automation/README.md)

## Licenc / License

MIT License
