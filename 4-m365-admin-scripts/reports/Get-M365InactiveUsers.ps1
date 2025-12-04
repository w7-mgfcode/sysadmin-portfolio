<#
.SYNOPSIS
    Inaktív M365 felhasználók riportja / M365 inactive users report

.DESCRIPTION
    Felhasználók akik X napja nem jelentkeztek be.
    Users who haven't signed in for X days.

.PARAMETER DaysInactive
    Inaktivitás napokban / Days of inactivity (default: 90)

.PARAMETER ExportPath
    Export CSV útvonala / CSV export path

.EXAMPLE
    .\Get-M365InactiveUsers.ps1 -DaysInactive 30

.EXAMPLE
    .\Get-M365InactiveUsers.ps1 -DaysInactive 90 -ExportPath "C:\temp\inactive.csv"

.NOTES
    Requires: Microsoft.Graph.Users, Microsoft.Graph.Reports modules
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [int]$DaysInactive = 90,

    [Parameter(Mandatory = $false)]
    [string]$ExportPath
)

begin {
    # Import kapcsolat modul / Import connection module
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    . (Join-Path (Split-Path $scriptPath) "common\Connect-M365.ps1")

    Write-Host "Inaktív felhasználók keresése ($DaysInactive nap) / Finding inactive users ($DaysInactive days)..." -ForegroundColor Cyan
}

process {
    try {
        # Kapcsolat ellenőrzése / Check connection
        if (-not (Test-M365Connection)) {
            Connect-M365Services -Scopes @("User.Read.All", "AuditLog.Read.All") | Out-Null
        }

        # Küszöb dátum / Threshold date
        $thresholdDate = (Get-Date).AddDays(-$DaysInactive)

        Write-Host "Küszöb dátum / Threshold date: $($thresholdDate.ToString('yyyy-MM-dd'))" -ForegroundColor Gray

        # Felhasználók lekérdezése / Get users
        $users = Get-MgUser -All -Property `
            Id, DisplayName, UserPrincipalName, Mail, Department, JobTitle, `
            AccountEnabled, CreatedDateTime, SignInActivity

        Write-Host "Összesen $($users.Count) felhasználó ellenőrzése / Checking $($users.Count) users..." -ForegroundColor Gray

        # Inaktív felhasználók szűrése / Filter inactive users
        $inactiveUsers = $users | Where-Object {
            $lastSignIn = $_.SignInActivity.LastSignInDateTime

            # Ha nincs bejelentkezési adat, vagy régebbi mint a küszöb
            # If no sign-in data or older than threshold
            (-not $lastSignIn) -or ($lastSignIn -lt $thresholdDate)
        }

        Write-Host "Találatok: $($inactiveUsers.Count) inaktív felhasználó / Found: $($inactiveUsers.Count) inactive users" -ForegroundColor Yellow

        # Eredmények formázása / Format results
        $results = $inactiveUsers | ForEach-Object {
            $daysSinceSignIn = if ($_.SignInActivity.LastSignInDateTime) {
                ((Get-Date) - $_.SignInActivity.LastSignInDateTime).Days
            } else {
                "Nincs adat / No data"
            }

            [PSCustomObject]@{
                DisplayName = $_.DisplayName
                UserPrincipalName = $_.UserPrincipalName
                Mail = $_.Mail
                Department = $_.Department
                JobTitle = $_.JobTitle
                AccountEnabled = $_.AccountEnabled
                LastSignIn = if ($_.SignInActivity.LastSignInDateTime) {
                    $_.SignInActivity.LastSignInDateTime.ToString('yyyy-MM-dd HH:mm')
                } else {
                    "Nincs / Never"
                }
                DaysSinceSignIn = $daysSinceSignIn
                Created = $_.CreatedDateTime.ToString('yyyy-MM-dd')
                Id = $_.Id
            }
        }

        # Megjelenítés / Display
        $results | Sort-Object DisplayName |
            Format-Table DisplayName, UserPrincipalName, Department, AccountEnabled, LastSignIn, DaysSinceSignIn -AutoSize

        # Export ha kértük / Export if requested
        if ($ExportPath) {
            $results | Export-Csv -Path $ExportPath -NoTypeInformation -Encoding UTF8
            Write-Host "Exportálva: $ExportPath" -ForegroundColor Green
        }

        # Statisztikák / Statistics
        $enabledInactive = ($results | Where-Object { $_.AccountEnabled }).Count
        $disabledInactive = $results.Count - $enabledInactive
        $neverSignedIn = ($results | Where-Object { $_.LastSignIn -eq "Nincs / Never" }).Count

        Write-Host "`nStatisztikák / Statistics:" -ForegroundColor Cyan
        Write-Host "  Aktív fiókok (inaktív) / Enabled accounts (inactive): $enabledInactive" -ForegroundColor Yellow
        Write-Host "  Letiltott fiókok / Disabled accounts: $disabledInactive" -ForegroundColor Gray
        Write-Host "  Soha nem jelentkezett be / Never signed in: $neverSignedIn" -ForegroundColor Red

        # Ajánlások / Recommendations
        if ($enabledInactive -gt 0) {
            Write-Host "`nAjánlás / Recommendation:" -ForegroundColor Cyan
            Write-Host "  $enabledInactive aktív fiók inaktív $DaysInactive napja." -ForegroundColor Yellow
            Write-Host "  Fontolja meg a fiókok felülvizsgálatát vagy letiltását." -ForegroundColor Yellow
            Write-Host "  $enabledInactive enabled accounts inactive for $DaysInactive days." -ForegroundColor Yellow
            Write-Host "  Consider reviewing or disabling these accounts." -ForegroundColor Yellow
        }

        return $results
    }
    catch {
        Write-Error "Hiba az inaktív felhasználók lekérdezése során / Error getting inactive users: $_"
        throw
    }
}

end {
    Write-Host "Kész / Done!" -ForegroundColor Green
}
