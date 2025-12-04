<#
.SYNOPSIS
    M365 felhasználók lekérdezése / Get M365 users

.DESCRIPTION
    Microsoft 365 felhasználók listázása részletes információkkal.
    Lists Microsoft 365 users with detailed information.

.PARAMETER Filter
    Szűrő kifejezés / Filter expression (OData)

.PARAMETER ExportPath
    Export CSV útvonala / CSV export path

.EXAMPLE
    .\Get-M365Users.ps1

.EXAMPLE
    .\Get-M365Users.ps1 -Filter "startswith(displayName,'John')"

.EXAMPLE
    .\Get-M365Users.ps1 -ExportPath "C:\temp\users.csv"

.NOTES
    Requires: Microsoft.Graph.Users module
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Filter,

    [Parameter(Mandatory = $false)]
    [string]$ExportPath
)

begin {
    # Import kapcsolat modul / Import connection module
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    . (Join-Path (Split-Path $scriptPath) "common\Connect-M365.ps1")

    Write-Host "M365 felhasználók lekérdezése / Getting M365 users..." -ForegroundColor Cyan
}

process {
    try {
        # Kapcsolat ellenőrzése / Check connection
        if (-not (Test-M365Connection)) {
            Write-Host "Kapcsolódás szükséges / Connection required..." -ForegroundColor Yellow
            Connect-M365Services -Scopes @("User.Read.All") | Out-Null
        }

        # Felhasználók lekérdezése / Get users
        $getUserParams = @{
            All = $true
            Property = @(
                'Id',
                'DisplayName',
                'UserPrincipalName',
                'Mail',
                'JobTitle',
                'Department',
                'OfficeLocation',
                'MobilePhone',
                'AccountEnabled',
                'CreatedDateTime',
                'SignInActivity'
            )
        }

        if ($Filter) {
            $getUserParams.Filter = $Filter
        }

        Write-Host "Lekérdezés futtatása / Running query..." -ForegroundColor Gray
        $users = Get-MgUser @getUserParams

        Write-Host "Találatok: $($users.Count) felhasználó / Found: $($users.Count) users" -ForegroundColor Green

        # Eredmények formázása / Format results
        $results = $users | Select-Object `
            DisplayName,
            UserPrincipalName,
            Mail,
            JobTitle,
            Department,
            OfficeLocation,
            MobilePhone,
            @{Name='Enabled'; Expression={$_.AccountEnabled}},
            @{Name='Created'; Expression={$_.CreatedDateTime}},
            @{Name='LastSignIn'; Expression={$_.SignInActivity.LastSignInDateTime}},
            Id

        # Megjelenítés / Display
        $results | Format-Table -AutoSize

        # Export ha kértük / Export if requested
        if ($ExportPath) {
            $results | Export-Csv -Path $ExportPath -NoTypeInformation -Encoding UTF8
            Write-Host "Exportálva: $ExportPath" -ForegroundColor Green
        }

        # Statisztikák / Statistics
        $enabledCount = ($users | Where-Object { $_.AccountEnabled }).Count
        $disabledCount = $users.Count - $enabledCount

        Write-Host "`nStatisztikák / Statistics:" -ForegroundColor Cyan
        Write-Host "  Aktív felhasználók / Active users: $enabledCount" -ForegroundColor Green
        Write-Host "  Inaktív felhasználók / Inactive users: $disabledCount" -ForegroundColor Yellow

        return $results
    }
    catch {
        Write-Error "Hiba a felhasználók lekérdezése során / Error getting users: $_"
        throw
    }
}

end {
    Write-Host "Kész / Done!" -ForegroundColor Green
}
