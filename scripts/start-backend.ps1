[CmdletBinding()]
param(
    [string]$CondaEnv = "rag_pro",
    [switch]$InstallDeps,
    [switch]$UpgradeDb
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envFile = Join-Path $projectRoot ".env"
$requirementsFile = Join-Path $projectRoot "requirements.txt"
$backendEntry = Join-Path $projectRoot "backend/run.py"
$migrationsDir = Join-Path $projectRoot "backend/migrations"

function Test-CondaEnv {
    param([string]$Name)

    $condaCmd = Get-Command conda -ErrorAction SilentlyContinue
    if (-not $condaCmd) {
        return $false
    }

    try {
        $json = & conda env list --json | ConvertFrom-Json
        foreach ($envPath in $json.envs) {
            if ($envPath -match "[\\/]" + [Regex]::Escape($Name) + "$") {
                return $true
            }
        }
    }
    catch {
        return $false
    }

    return $false
}

function Invoke-ProjectPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    if ($script:useConda) {
        & conda run --no-capture-output -n $script:resolvedCondaEnv python @Arguments
    }
    else {
        & python @Arguments
    }
}

Set-Location $projectRoot

if (-not (Test-Path $envFile) -and (Test-Path (Join-Path $projectRoot ".env.example"))) {
    Copy-Item (Join-Path $projectRoot ".env.example") $envFile
    Write-Host "Created .env from .env.example" -ForegroundColor Yellow
}

$script:useConda = Test-CondaEnv -Name $CondaEnv
$script:resolvedCondaEnv = $CondaEnv

if ($script:useConda) {
    Write-Host "Using conda environment: $CondaEnv" -ForegroundColor Cyan
}
else {
    Write-Host "Conda env '$CondaEnv' not found. Falling back to current python." -ForegroundColor Yellow
}

if ($InstallDeps) {
    if (-not (Test-Path $requirementsFile)) {
        throw "requirements.txt not found: $requirementsFile"
    }
    Invoke-ProjectPython -Arguments @("-m", "pip", "install", "-r", $requirementsFile)
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if ($UpgradeDb) {
    if (-not (Test-Path $migrationsDir)) {
        throw "Migrations directory not found: $migrationsDir"
    }
    Invoke-ProjectPython -Arguments @("-m", "flask", "--app", "backend/run.py", "db", "upgrade", "-d", "backend/migrations")
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path $backendEntry)) {
    throw "Backend entry not found: $backendEntry"
}

Write-Host "Starting backend on http://localhost:5001" -ForegroundColor Green
Invoke-ProjectPython -Arguments @("backend/run.py")
exit $LASTEXITCODE
