# M365 Admin Scripts

## Áttekintés / Overview

PowerShell scriptek Microsoft 365 adminisztrációhoz Graph API használatával.

PowerShell scripts for Microsoft 365 administration using Graph API.

## Előfeltételek / Prerequisites

### PowerShell Modulok / PowerShell Modules

```powershell
# Microsoft Graph modulok telepítése / Install Microsoft Graph modules
Install-Module Microsoft.Graph -Scope CurrentUser

# Vagy csak a szükséges modulok / Or just required modules
Install-Module Microsoft.Graph.Users -Scope CurrentUser
Install-Module Microsoft.Graph.Groups -Scope CurrentUser
Install-Module Microsoft.Graph.Identity.DirectoryManagement -Scope CurrentUser
Install-Module Microsoft.Graph.Reports -Scope CurrentUser
```

### Jogosultságok / Permissions

Az alábbi Graph API jogosultságok szükségesek:
- `User.Read.All` - Felhasználók olvasása
- `Group.Read.All` - Csoportok olvasása
- `Directory.Read.All` - Könyvtár olvasása
- `Organization.Read.All` - Szervezet információk
- `AuditLog.Read.All` - Audit logok (riportokhoz)

## Scriptek / Scripts

### Kapcsolat / Connection

#### Connect-M365.ps1
Kapcsolódás Microsoft 365-höz Graph API-val.

```powershell
# Kapcsolat modul importálása / Import connection module
. .\common\Connect-M365.ps1

# Kapcsolódás / Connect
Connect-M365Services -TenantId "your-tenant-id"

# Kapcsolat ellenőrzése / Test connection
Test-M365Connection

# Kapcsolat bontása / Disconnect
Disconnect-M365Services
```

### Felhasználó Kezelés / User Management

#### Get-M365Users.ps1
Felhasználók listázása részletes információkkal.

```powershell
# Összes felhasználó / All users
.\users\Get-M365Users.ps1

# Szűrés névre / Filter by name
.\users\Get-M365Users.ps1 -Filter "startswith(displayName,'John')"

# Export CSV-be / Export to CSV
.\users\Get-M365Users.ps1 -ExportPath "C:\temp\users.csv"
```

**Kimeneti adatok / Output data:**
- Megjelenítési név / Display name
- UPN (felhasználónév)
- Email cím
- Munkakör / Job title
- Részleg / Department
- Iroda helyszín / Office location
- Mobiltelefon / Mobile phone
- Fiók állapot / Account status
- Létrehozás dátuma / Creation date
- Utolsó bejelentkezés / Last sign-in

### Csoport Kezelés / Group Management

#### Get-M365Groups.ps1
Csoportok listázása tagokkal.

```powershell
# Összes csoport / All groups
.\groups\Get-M365Groups.ps1

# Csoport keresése névvel / Search by name
.\groups\Get-M365Groups.ps1 -GroupName "Sales"

# Tagokkal együtt / Include members
.\groups\Get-M365Groups.ps1 -GroupName "IT" -IncludeMembers
```

**Információk / Information:**
- Csoport név / Group name
- Leírás / Description
- Csoport típus / Group type (M365, Security, Distribution)
- Email cím
- Tagok száma / Member count
- Tagok listája / Member list (ha kérjük)

### Licenc Kezelés / License Management

#### Get-M365Licenses.ps1
Licenc használat riport.

```powershell
# Licenc áttekintés / License overview
.\licenses\Get-M365Licenses.ps1

# Export CSV-be / Export to CSV
.\licenses\Get-M365Licenses.ps1 -ExportPath "C:\temp\licenses.csv"
```

**Riport tartalom / Report content:**
- Termék név / Product name
- Összes licenc / Total licenses
- Kiosztott licencek / Assigned licenses
- Elérhető licencek / Available licenses
- Kihasználtság % / Usage percentage
- Állapot / Status
- Figyelmeztetés alacsony készletnél / Warning for low availability

### Riportok / Reports

#### Get-M365InactiveUsers.ps1
Inaktív felhasználók riport.

```powershell
# 90 napja inaktív felhasználók / Users inactive for 90 days
.\reports\Get-M365InactiveUsers.ps1

# 30 napja inaktív / Inactive for 30 days
.\reports\Get-M365InactiveUsers.ps1 -DaysInactive 30

# Export / Export
.\reports\Get-M365InactiveUsers.ps1 -DaysInactive 90 -ExportPath "C:\temp\inactive.csv"
```

**Statisztikák / Statistics:**
- Inaktív aktív fiókok / Inactive enabled accounts
- Letiltott fiókok / Disabled accounts
- Soha nem bejelentkezett / Never signed in
- Ajánlások / Recommendations

## Könyvtárstruktúra / Directory Structure

```
4-m365-admin-scripts/
├── README.md              # Ez a dokumentum / This document
├── common/
│   └── Connect-M365.ps1   # Kapcsolat modul / Connection module
├── users/
│   └── Get-M365Users.ps1  # Felhasználók lekérdezése / Get users
├── groups/
│   └── Get-M365Groups.ps1 # Csoportok lekérdezése / Get groups
├── licenses/
│   └── Get-M365Licenses.ps1 # Licencek lekérdezése / Get licenses
└── reports/
    └── Get-M365InactiveUsers.ps1 # Inaktív felhasználók / Inactive users
```

## Használati Példák / Usage Examples

### Napi Ellenőrzés / Daily Check

```powershell
# 1. Kapcsolódás / Connect
. .\common\Connect-M365.ps1
Connect-M365Services

# 2. Licenc helyzet / License status
.\licenses\Get-M365Licenses.ps1

# 3. Új felhasználók / New users (last 7 days)
.\users\Get-M365Users.ps1 -Filter "createdDateTime ge $((Get-Date).AddDays(-7).ToString('yyyy-MM-dd'))"

# 4. Kapcsolat bontása / Disconnect
Disconnect-M365Services
```

### Havi Riport / Monthly Report

```powershell
# Kapcsolódás / Connect
Connect-M365Services

# Export könyvtár létrehozása / Create export directory
$exportDir = "C:\M365Reports\$(Get-Date -Format 'yyyy-MM')"
New-Item -Path $exportDir -ItemType Directory -Force

# Riportok generálása / Generate reports
.\users\Get-M365Users.ps1 -ExportPath "$exportDir\users.csv"
.\groups\Get-M365Groups.ps1 -ExportPath "$exportDir\groups.csv"
.\licenses\Get-M365Licenses.ps1 -ExportPath "$exportDir\licenses.csv"
.\reports\Get-M365InactiveUsers.ps1 -DaysInactive 90 -ExportPath "$exportDir\inactive.csv"

Write-Host "Riportok mentve: $exportDir" -ForegroundColor Green
```

### Licenc Auditálás / License Audit

```powershell
# 1. Licenc áttekintés / License overview
$licenses = .\licenses\Get-M365Licenses.ps1

# 2. Alacsony készlet figyelmeztetés / Low availability warning
$lowStock = $licenses | Where-Object { $_.AvailableLicenses -lt 5 -and $_.TotalLicenses -gt 0 }
if ($lowStock) {
    $lowStock | Format-Table ProductName, AvailableLicenses
    Write-Warning "Figyelem: Alacsony licenc készlet! / Warning: Low license stock!"
}

# 3. Kihasználatlan felhasználók / Unused users
$inactiveUsers = .\reports\Get-M365InactiveUsers.ps1 -DaysInactive 90
Write-Host "$($inactiveUsers.Count) felhasználó inaktív 90 napja"
```

## Biztonság / Security

### Kapcsolat Kezelés / Connection Management
- Graph API OAuth2 hitelesítés / OAuth2 authentication
- Munkamenet kezelés / Session management
- Automatikus token frissítés / Automatic token refresh

### Audit és Napló / Audit and Logging
- Minden művelet naplózva a Microsoft Audit Log-ban
- Sign-in activity tracking
- License change tracking

### Best Practices
- Mindig használj minimális jogosultságokat / Always use least privilege
- Kapcsolódj csak amikor szükséges / Connect only when needed
- Kapcsolat bontása használat után / Disconnect after use
- Érzékeny adatok exportálása biztonságosan / Export sensitive data securely

## Hibaelhárítás / Troubleshooting

### Kapcsolódási Hiba / Connection Error
```powershell
# Module ellenőrzés / Check module
Get-Module Microsoft.Graph -ListAvailable

# Újratelepítés / Reinstall
Install-Module Microsoft.Graph -Force -AllowClobber
```

### Jogosultság Hiba / Permission Error
```powershell
# Jelenlegi jogosultságok / Current permissions
(Get-MgContext).Scopes

# Újracsatlakozás több jogosultsággal / Reconnect with more scopes
Connect-M365Services -Scopes @("User.Read.All", "Group.Read.All", "Directory.Read.All")
```

## Licenc / License

MIT License
