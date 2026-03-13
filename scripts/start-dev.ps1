[CmdletBinding()]
param(
    [string]$CondaEnv = "rag_pro",
    [switch]$InstallBackendDeps,
    [switch]$InstallFrontendDeps,
    [switch]$UpgradeDb,
    [switch]$SkipInfra,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$powerShellExe = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source

if (-not $powerShellExe) {
    throw "powershell.exe not found."
}

if (-not $SkipInfra) {
    & (Join-Path $PSScriptRoot "start-infra.ps1")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

$backendArgs = @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "start-backend.ps1"),
    "-CondaEnv", $CondaEnv
)
if ($InstallBackendDeps) {
    $backendArgs += "-InstallDeps"
}
if ($UpgradeDb) {
    $backendArgs += "-UpgradeDb"
}

$frontendArgs = @(
    "-NoExit",
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "start-frontend.ps1"),
    "-Port", $FrontendPort
)
if ($InstallFrontendDeps) {
    $frontendArgs += "-InstallDeps"
}

Start-Process -FilePath $powerShellExe -WorkingDirectory $projectRoot -ArgumentList $backendArgs | Out-Null
Start-Process -FilePath $powerShellExe -WorkingDirectory $projectRoot -ArgumentList $frontendArgs | Out-Null

Write-Host "Started backend and frontend in separate PowerShell windows." -ForegroundColor Green
if (-not $SkipInfra) {
    Write-Host "Infrastructure services were started with docker compose." -ForegroundColor Green
}
