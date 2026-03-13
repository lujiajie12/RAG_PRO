[CmdletBinding()]
param(
    [switch]$InstallDeps,
    [int]$Port = 5173,
    [switch]$UseDistFallback
)

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontendRoot = Join-Path $projectRoot "frontend"
$packageJson = Join-Path $frontendRoot "package.json"
$nodeModules = Join-Path $frontendRoot "node_modules"
$distDir = Join-Path $frontendRoot "dist"
$fallbackServer = Join-Path $projectRoot "scripts/serve_frontend_dist.py"

function Get-NpmCommand {
    foreach ($name in @("npm.cmd", "npm")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) {
            return $cmd.Source
        }
    }

    $registryInstallPath = (Get-ItemProperty "HKLM:\SOFTWARE\Node.js" -ErrorAction SilentlyContinue).InstallPath
    if ($registryInstallPath) {
        $registryNpm = Join-Path $registryInstallPath "npm.cmd"
        if (Test-Path $registryNpm) {
            return $registryNpm
        }
    }

    foreach ($candidate in @(
        "C:\Program Files\nodejs\npm.cmd",
        "C:\Program Files (x86)\nodejs\npm.cmd",
        "F:\Program Files\nodejs\npm.cmd"
    )) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Test-PortInUse {
    param([int]$PortNumber)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $PortNumber)
        $listener.Start()
        return $false
    }
    catch {
        return $true
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

Set-Location $projectRoot

if (-not (Test-Path $packageJson)) {
    throw "Frontend package.json not found: $packageJson"
}

if (Test-PortInUse -PortNumber $Port) {
    throw "Frontend port $Port is already in use. Pass -Port with a different value."
}

$npmCommand = Get-NpmCommand

if ($npmCommand) {
    $npmDir = Split-Path -Parent $npmCommand
    if ($npmDir -and ($env:PATH -split ";") -notcontains $npmDir) {
        $env:PATH = "$npmDir;$env:PATH"
    }

    Set-Location $frontendRoot

    if ($InstallDeps -or -not (Test-Path $nodeModules)) {
        & $npmCommand install
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }

    Write-Host "Starting frontend dev server on http://localhost:$Port" -ForegroundColor Green
    & $npmCommand run dev -- --host 0.0.0.0 --port $Port
    exit $LASTEXITCODE
}

if ($UseDistFallback -or (Test-Path $distDir)) {
    if (-not (Test-Path $fallbackServer)) {
        throw "Fallback server script not found: $fallbackServer"
    }

    Write-Warning "npm/node not found in PATH. Falling back to serving frontend/dist."
    & python $fallbackServer --root $distDir --port $Port
    exit $LASTEXITCODE
}

throw "npm/node is not available in PATH, and frontend/dist fallback is unavailable."
