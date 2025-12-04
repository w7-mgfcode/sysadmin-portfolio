<#
.SYNOPSIS
    M365 licencek lekérdezése / Get M365 licenses

.DESCRIPTION
    Microsoft 365 licenc használat riport.
    Microsoft 365 license usage report.

.PARAMETER ExportPath
    Export CSV útvonala / CSV export path

.EXAMPLE
    .\Get-M365Licenses.ps1

.EXAMPLE
    .\Get-M365Licenses.ps1 -ExportPath "C:\temp\licenses.csv"

.NOTES
    Requires: Microsoft.Graph.Identity.DirectoryManagement module
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ExportPath
)

begin {
    # Import kapcsolat modul / Import connection module
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    . (Join-Path (Split-Path $scriptPath) "common\Connect-M365.ps1")

    Write-Host "M365 licencek lekérdezése / Getting M365 licenses..." -ForegroundColor Cyan
}

process {
    try {
        # Kapcsolat ellenőrzése / Check connection
        if (-not (Test-M365Connection)) {
            Connect-M365Services -Scopes @("Organization.Read.All", "Directory.Read.All") | Out-Null
        }

        # Előfizetett SKU-k lekérdezése / Get subscribed SKUs
        $skus = Get-MgSubscribedSku -All

        Write-Host "Találatok: $($skus.Count) licenc típus / Found: $($skus.Count) license types" -ForegroundColor Green

        # Licenc nevek map / License name mapping
        $licenseNames = @{
            "ENTERPRISEPACK" = "Office 365 E3"
            "ENTERPRISEPREMIUM" = "Office 365 E5"
            "SPE_E3" = "Microsoft 365 E3"
            "SPE_E5" = "Microsoft 365 E5"
            "STANDARDPACK" = "Office 365 E1"
            "EXCHANGESTANDARD" = "Exchange Online Plan 1"
            "EXCHANGEENTERPRISE" = "Exchange Online Plan 2"
            "POWER_BI_PRO" = "Power BI Pro"
            "PROJECTPROFESSIONAL" = "Project Plan 3"
            "VISIOCLIENT" = "Visio Plan 2"
        }

        # Eredmények formázása / Format results
        $results = foreach ($sku in $skus) {
            $skuPart = $sku.SkuPartNumber
            $friendlyName = if ($licenseNames.ContainsKey($skuPart)) {
                $licenseNames[$skuPart]
            } else {
                $skuPart
            }

            $enabled = $sku.PrepaidUnits.Enabled
            $consumed = $sku.ConsumedUnits
            $available = $enabled - $consumed
            $usagePercent = if ($enabled -gt 0) {
                [math]::Round(($consumed / $enabled) * 100, 2)
            } else { 0 }

            [PSCustomObject]@{
                ProductName = $friendlyName
                SkuId = $sku.SkuId
                SkuPartNumber = $skuPart
                TotalLicenses = $enabled
                AssignedLicenses = $consumed
                AvailableLicenses = $available
                UsagePercent = $usagePercent
                Status = $sku.CapabilityStatus
            }
        }

        # Megjelenítés / Display
        $results | Sort-Object AssignedLicenses -Descending |
            Format-Table ProductName, TotalLicenses, AssignedLicenses, AvailableLicenses, UsagePercent, Status -AutoSize

        # Export ha kértük / Export if requested
        if ($ExportPath) {
            $results | Export-Csv -Path $ExportPath -NoTypeInformation -Encoding UTF8
            Write-Host "Exportálva: $ExportPath" -ForegroundColor Green
        }

        # Statisztikák / Statistics
        $totalLicenses = ($results | Measure-Object -Property TotalLicenses -Sum).Sum
        $assignedLicenses = ($results | Measure-Object -Property AssignedLicenses -Sum).Sum
        $availableLicenses = $totalLicenses - $assignedLicenses
        $overallUsage = if ($totalLicenses -gt 0) {
            [math]::Round(($assignedLicenses / $totalLicenses) * 100, 2)
        } else { 0 }

        Write-Host "`nÖsszesített statisztikák / Overall statistics:" -ForegroundColor Cyan
        Write-Host "  Összes licenc / Total licenses: $totalLicenses" -ForegroundColor White
        Write-Host "  Kiosztott / Assigned: $assignedLicenses" -ForegroundColor Green
        Write-Host "  Elérhető / Available: $availableLicenses" -ForegroundColor Yellow
        Write-Host "  Kihasználtság / Usage: $overallUsage%" -ForegroundColor $(if ($overallUsage -gt 90) { "Red" } elseif ($overallUsage -gt 75) { "Yellow" } else { "Green" })

        # Figyelmeztetések / Warnings
        $lowAvailability = $results | Where-Object { $_.AvailableLicenses -lt 5 -and $_.TotalLicenses -gt 0 }
        if ($lowAvailability) {
            Write-Host "`nFigyelmeztetés / Warning: Alacsony licenc készlet / Low license availability:" -ForegroundColor Yellow
            $lowAvailability | ForEach-Object {
                Write-Host "  $($_.ProductName): $($_.AvailableLicenses) elérhető" -ForegroundColor Yellow
            }
        }

        return $results
    }
    catch {
        Write-Error "Hiba a licencek lekérdezése során / Error getting licenses: $_"
        throw
    }
}

end {
    Write-Host "Kész / Done!" -ForegroundColor Green
}
