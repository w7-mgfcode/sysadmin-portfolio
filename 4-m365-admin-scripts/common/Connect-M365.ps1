<#
.SYNOPSIS
    Microsoft 365 kapcsolat modul / Microsoft 365 connection module

.DESCRIPTION
    Kapcsolódás Microsoft 365 szolgáltatásokhoz Graph API-val.
    Connects to Microsoft 365 services using Graph API.

.PARAMETER TenantId
    Tenant azonosító / Tenant ID

.PARAMETER Scopes
    Szükséges jogosultságok / Required scopes

.EXAMPLE
    . .\Connect-M365.ps1
    Connect-M365Services -TenantId "your-tenant-id"

.NOTES
    Requires: Microsoft.Graph PowerShell SDK
    Install-Module Microsoft.Graph -Scope CurrentUser
#>

function Connect-M365Services {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$TenantId,

        [Parameter(Mandatory = $false)]
        [string[]]$Scopes = @(
            "User.Read.All",
            "Group.Read.All",
            "Directory.Read.All",
            "Organization.Read.All"
        )
    )

    begin {
        Write-Host "M365 kapcsolódás indítása / Starting M365 connection..." -ForegroundColor Cyan
    }

    process {
        try {
            # Ellenőrizzük hogy telepítve van-e a Microsoft.Graph modul
            # Check if Microsoft.Graph module is installed
            if (-not (Get-Module -ListAvailable -Name Microsoft.Graph)) {
                throw "Microsoft.Graph modul nincs telepítve / Microsoft.Graph module not installed. Run: Install-Module Microsoft.Graph"
            }

            # Kapcsolódás / Connect
            $connectParams = @{
                Scopes = $Scopes
            }

            if ($TenantId) {
                $connectParams.TenantId = $TenantId
            }

            Connect-MgGraph @connectParams -NoWelcome

            # Kapcsolat ellenőrzése / Verify connection
            $context = Get-MgContext
            if ($context) {
                Write-Host "Sikeres kapcsolódás / Successfully connected" -ForegroundColor Green
                Write-Host "  Tenant ID: $($context.TenantId)" -ForegroundColor Gray
                Write-Host "  Account: $($context.Account)" -ForegroundColor Gray
                Write-Host "  Scopes: $($context.Scopes -join ', ')" -ForegroundColor Gray
                return $true
            }
            else {
                throw "Kapcsolódás sikertelen / Connection failed"
            }
        }
        catch {
            Write-Error "Hiba a kapcsolódás során / Error during connection: $_"
            return $false
        }
    }
}

function Disconnect-M365Services {
    [CmdletBinding()]
    param()

    try {
        Disconnect-MgGraph -ErrorAction SilentlyContinue
        Write-Host "Kapcsolat bontva / Disconnected" -ForegroundColor Green
    }
    catch {
        Write-Warning "Hiba a kapcsolat bontása során / Error during disconnect: $_"
    }
}

function Test-M365Connection {
    [CmdletBinding()]
    param()

    try {
        $context = Get-MgContext -ErrorAction Stop
        if ($context) {
            Write-Host "Kapcsolat aktív / Connection active" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Nincs aktív kapcsolat / No active connection" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "Nincs aktív kapcsolat / No active connection" -ForegroundColor Yellow
        return $false
    }
}

# Export functions
Export-ModuleMember -Function Connect-M365Services, Disconnect-M365Services, Test-M365Connection
