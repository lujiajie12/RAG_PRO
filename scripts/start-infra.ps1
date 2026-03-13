[CmdletBinding()]
param(
    [switch]$Down,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $projectRoot "infra/docker/docker-compose.yml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "docker is not available in PATH."
}

if (-not (Test-Path $composeFile)) {
    throw "Compose file not found: $composeFile"
}

Set-Location $projectRoot

if ($Down) {
    & docker compose -f $composeFile down
    exit $LASTEXITCODE
}

& docker compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

& docker compose -f $composeFile ps

if ($Logs) {
    & docker compose -f $composeFile logs --tail 30
}
