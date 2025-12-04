<#
.SYNOPSIS
    M365 csoportok lekérdezése / Get M365 groups

.DESCRIPTION
    Microsoft 365 csoportok listázása tagokkal.
    Lists Microsoft 365 groups with members.

.PARAMETER GroupName
    Csoport név szűrő / Group name filter

.PARAMETER IncludeMembers
    Tagok megjelenítése / Include members

.EXAMPLE
    .\Get-M365Groups.ps1

.EXAMPLE
    .\Get-M365Groups.ps1 -GroupName "Sales" -IncludeMembers

.NOTES
    Requires: Microsoft.Graph.Groups module
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$GroupName,

    [Parameter(Mandatory = $false)]
    [switch]$IncludeMembers
)

begin {
    # Import kapcsolat modul / Import connection module
    $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
    . (Join-Path (Split-Path $scriptPath) "common\Connect-M365.ps1")

    Write-Host "M365 csoportok lekérdezése / Getting M365 groups..." -ForegroundColor Cyan
}

process {
    try {
        # Kapcsolat ellenőrzése / Check connection
        if (-not (Test-M365Connection)) {
            Connect-M365Services -Scopes @("Group.Read.All", "GroupMember.Read.All") | Out-Null
        }

        # Csoportok lekérdezése / Get groups
        $getGroupParams = @{
            All = $true
            Property = @(
                'Id',
                'DisplayName',
                'Description',
                'GroupTypes',
                'Mail',
                'MailEnabled',
                'SecurityEnabled',
                'CreatedDateTime'
            )
        }

        if ($GroupName) {
            $getGroupParams.Filter = "startswith(displayName,'$GroupName')"
        }

        $groups = Get-MgGroup @getGroupParams

        Write-Host "Találatok: $($groups.Count) csoport / Found: $($groups.Count) groups" -ForegroundColor Green

        # Eredmények feldolgozása / Process results
        $results = foreach ($group in $groups) {
            $memberCount = 0
            $members = @()

            if ($IncludeMembers) {
                $groupMembers = Get-MgGroupMember -GroupId $group.Id -All
                $memberCount = $groupMembers.Count
                $members = $groupMembers | ForEach-Object {
                    Get-MgUser -UserId $_.Id -Property DisplayName, UserPrincipalName -ErrorAction SilentlyContinue |
                        Select-Object DisplayName, UserPrincipalName
                }
            }

            [PSCustomObject]@{
                DisplayName = $group.DisplayName
                Description = $group.Description
                Type = if ($group.GroupTypes -contains "Unified") { "Microsoft 365" } else { "Security/Distribution" }
                Mail = $group.Mail
                MailEnabled = $group.MailEnabled
                SecurityEnabled = $group.SecurityEnabled
                MemberCount = $memberCount
                Members = if ($members) { ($members.DisplayName -join '; ') } else { "" }
                Created = $group.CreatedDateTime
                Id = $group.Id
            }
        }

        # Megjelenítés / Display
        if ($IncludeMembers) {
            $results | Format-List
        }
        else {
            $results | Format-Table DisplayName, Type, Mail, SecurityEnabled, MemberCount, Created -AutoSize
        }

        # Statisztikák / Statistics
        $m365Groups = ($results | Where-Object { $_.Type -eq "Microsoft 365" }).Count
        $securityGroups = ($results | Where-Object { $_.SecurityEnabled }).Count

        Write-Host "`nStatisztikák / Statistics:" -ForegroundColor Cyan
        Write-Host "  Microsoft 365 csoportok / Microsoft 365 groups: $m365Groups" -ForegroundColor Green
        Write-Host "  Biztonsági csoportok / Security groups: $securityGroups" -ForegroundColor Green

        return $results
    }
    catch {
        Write-Error "Hiba a csoportok lekérdezése során / Error getting groups: $_"
        throw
    }
}

end {
    Write-Host "Kész / Done!" -ForegroundColor Green
}
