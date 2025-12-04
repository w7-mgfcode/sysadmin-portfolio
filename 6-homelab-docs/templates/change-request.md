# Change Request Template / Változtatási Kérelem Sablon

## Változtatás Információk / Change Information

**Változtatás ID / Change ID:** CHG-YYYYMMDD-XXX

**Beküldő / Submitter:** [Név / Name]

**Dátum / Date:** YYYY-MM-DD

**Prioritás / Priority:** [Low / Medium / High / Critical]

**Kategória / Category:** [Hardware / Software / Configuration / Network]

## Leírás / Description

### Változtatás Címe / Change Title
[Rövid, beszédes cím / Short, descriptive title]

### Változtatás Oka / Reason for Change
[Miért szükséges ez a változtatás? / Why is this change necessary?]

### Változtatás Hatása / Change Impact
[Milyen rendszerekre/felhasználókra van hatással? / What systems/users are affected?]

## Részletek / Details

### Jelenleg Állapot / Current State
[Mi a jelenlegi helyzet? / What is the current situation?]

### Tervezett Állapot / Desired State
[Mi lesz a változtatás után? / What will it be after the change?]

### Változtatás Típusa / Change Type
- [ ] Új funkció telepítése / New feature installation
- [ ] Konfiguráció módosítás / Configuration change
- [ ] Frissítés/patch / Update/patch
- [ ] Hardware csere / Hardware replacement
- [ ] Hálózati változtatás / Network change
- [ ] Egyéb / Other: ___________

## Implementációs Terv / Implementation Plan

### Előkészület / Preparation

1. [Előkészítő lépés 1 / Preparation step 1]
2. [Előkészítő lépés 2 / Preparation step 2]

### Végrehajtási Lépések / Implementation Steps

```bash
# 1. lépés / Step 1
[Command or action]

# 2. lépés / Step 2
[Command or action]

# 3. lépés / Step 3
[Command or action]
```

### Ellenőrzési Pontok / Verification Points

- [ ] [Ellenőrzési pont 1 / Verification 1]
- [ ] [Ellenőrzési pont 2 / Verification 2]
- [ ] [Ellenőrzési pont 3 / Verification 3]

### Visszaállítási Terv / Rollback Plan

Ha a változtatás sikertelen:
If the change fails:

```bash
# Visszaállítás lépései / Rollback steps
[Rollback commands]
```

## Kockázat Értékelés / Risk Assessment

### Kockázat Szint / Risk Level
- [ ] Alacsony / Low - Minimális hatás, könnyen visszaállítható
- [ ] Közepes / Medium - Korlátozott hatás, visszaállítható
- [ ] Magas / High - Jelentős hatás, komplex visszaállítás
- [ ] Kritikus / Critical - Teljes szolgáltatáskiesés lehetséges

### Azonosított Kockázatok / Identified Risks

1. [Kockázat 1 / Risk 1]
   - **Valószínűség / Probability:** [Low/Medium/High]
   - **Hatás / Impact:** [Low/Medium/High]
   - **Enyhítés / Mitigation:** [Mit teszünk ellene / What we do about it]

2. [Kockázat 2 / Risk 2]
   - **Valószínűség / Probability:** [Low/Medium/High]
   - **Hatás / Impact:** [Low/Medium/High]
   - **Enyhítés / Mitigation:** [Mit teszünk ellene / What we do about it]

## Ütemezés / Scheduling

### Javasolt Időpont / Proposed Date/Time
**Dátum / Date:** YYYY-MM-DD
**Időpont / Time:** HH:MM - HH:MM (időzóna / timezone)
**Időtartam / Duration:** X óra / hours

### Karbantartási Ablak / Maintenance Window
- [ ] Szabványos ablak / Standard window (Wednesday 02:00-04:00)
- [ ] Sürgősségi ablak / Emergency window (azonnal / immediate)
- [ ] Egyedi ablak / Custom window: ___________

### Értesítések / Notifications
- [ ] Felhasználók értesítése 24 órával előtte / Notify users 24h before
- [ ] Email értesítés / Email notification
- [ ] Dashboard banner

## Kommunikáció / Communication

### Érintett Felek / Stakeholders
| Szerep / Role | Név / Name | Értesítve / Notified |
|---------------|------------|---------------------|
| Rendszergazda / Admin | [Name] | [ ] Igen / Yes |
| Felhasználók / Users | All | [ ] Igen / Yes |

### Üzenet Sablon / Message Template

**Tárgy / Subject:** Tervezett karbantartás - [Változtatás címe]

**Üzenet / Message:**
```
Tisztelt Felhasználók / Dear Users,

Tervezett rendszerkarbantartást végzünk:
Scheduled system maintenance:

Időpont / Date: YYYY-MM-DD HH:MM
Időtartam / Duration: X óra / hours
Érintett szolgáltatások / Affected services: [List]

A karbantartás során az alábbi szolgáltatások nem lesznek elérhetők:
During maintenance, the following services will be unavailable:
- [Service 1]
- [Service 2]

Köszönjük a megértést!
Thank you for your understanding!
```

## Végrehajtás / Execution

### Pre-Change Checklist / Változtatás Előtti Ellenőrzés

- [ ] Változtatási terv áttekintve / Change plan reviewed
- [ ] Mentés elkészítve / Backup completed
- [ ] Tesztkörnyezetben validálva / Validated in test environment
- [ ] Rollback terv dokumentálva / Rollback plan documented
- [ ] Érintettek értesítve / Stakeholders notified
- [ ] Szükséges eszközök elérhetők / Required tools available

### Végrehajtás Napló / Execution Log

| Idő / Time | Művelet / Action | Eredmény / Result | Jegyzetek / Notes |
|------------|------------------|-------------------|-------------------|
| HH:MM | [Action] | [OK/FAIL] | [Notes] |

### Post-Change Checklist / Változtatás Utáni Ellenőrzés

- [ ] Változtatás sikeresen telepítve / Change successfully deployed
- [ ] Ellenőrzési pontok teljesítve / Verification points completed
- [ ] Szolgáltatások működnek / Services operational
- [ ] Monitoring adatok normálisak / Monitoring data normal
- [ ] Felhasználók értesítve befejezésről / Users notified of completion
- [ ] Dokumentáció frissítve / Documentation updated
- [ ] Change lezárva / Change closed

## Jóváhagyás / Approval

| Szerep / Role | Név / Name | Dátum / Date | Aláírás / Signature |
|---------------|------------|--------------|---------------------|
| Kérelmező / Requester | | | |
| Jóváhagyó / Approver | | | |
| Implementáló / Implementer | | | |

## Jegyzetek / Notes

[További megjegyzések / Additional notes]

---

**Létrehozva / Created:** YYYY-MM-DD
**Frissítve / Updated:** YYYY-MM-DD
**Állapot / Status:** [DRAFT / PENDING / APPROVED / IMPLEMENTED / CLOSED]
