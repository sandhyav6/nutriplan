<#
.SYNOPSIS
    Starts NutriPlan locally without Docker - one command, then the browser opens.

.DESCRIPTION
    1. Runs scripts\setup-local.ps1 automatically if the project is not set up yet.
    2. Makes sure the SQLite database folder is writable (falls back to backend\.data).
    3. Applies migrations and loads the food & recipe dataset (no-op when already done).
    4. Starts the backend in its own window and waits until /api/v1/health answers.
    5. Starts the frontend in its own window, waits for it, and opens the browser.

    -Production: builds the frontend and serves API + frontend from ONE backend process
    (the same single-origin setup as the Docker image) - no separate frontend window.

    Free ports are picked automatically (API from 8000, frontend from 5173) when the
    defaults are already in use. Close the server windows to stop NutriPlan.

.EXAMPLE
    .\start.cmd
    .\start.cmd -Production
    powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1 -Port 8080 -NoBrowser
#>
param([switch]$Production, [int]$Port = 0, [switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$envFile = Join-Path $backend '.env'

function Step($text) { Write-Host "`n==> $text" -ForegroundColor Cyan }

function Test-PortFree([int]$p) {
    -not (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)
}

function Get-FreePort([int]$start) {
    for ($p = $start; $p -lt $start + 50; $p++) {
        if (Test-PortFree $p) { return $p }
    }
    throw "No free port found between $start and $($start + 49)."
}

function Wait-Url([string]$url, [int]$seconds) {
    $deadline = (Get-Date).AddSeconds($seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Milliseconds 700
        }
    }
    return $false
}

function Write-Utf8NoBom([string]$path, [string]$text) {
    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding $false))
}

function Test-WritableFolder([string]$dir) {
    try {
        New-Item -ItemType Directory -Force $dir | Out-Null
        $probe = Join-Path $dir ('.nutriplan-write-test-' + [guid]::NewGuid().ToString('N'))
        [System.IO.File]::WriteAllText($probe, 'ok')
        Remove-Item -LiteralPath $probe -Force
        return $true
    } catch {
        return $false
    }
}

# --- 1. Setup on first run --------------------------------------------------------------
if (-not (Test-Path $python) -or -not (Test-Path $envFile) -or -not (Test-Path (Join-Path $frontend 'node_modules'))) {
    Step 'First run - setting up the project (this takes a few minutes once)'
    & (Join-Path $PSScriptRoot 'setup-local.ps1')
}

# --- 2. SQLite location must be writable --------------------------------------------------
$envText = [System.IO.File]::ReadAllText($envFile)
$match = [regex]::Match($envText, '(?m)^DATABASE_URL=sqlite:///(.+?)\s*$')
if ($match.Success) {
    $dbPath = $match.Groups[1].Value -replace '/', '\'
    if (-not [System.IO.Path]::IsPathRooted($dbPath)) { $dbPath = Join-Path $backend $dbPath }
    if (-not (Test-WritableFolder (Split-Path -Parent $dbPath))) {
        $fallback = Join-Path $backend '.data'
        if (-not (Test-WritableFolder $fallback)) { throw "Cannot write the database folder or $fallback." }
        Write-Warning "Cannot write '$(Split-Path -Parent $dbPath)'. Using $fallback instead and updating backend\.env."
        $base = 'sqlite:///' + ($fallback -replace '\\', '/')
        $envText = [regex]::Replace($envText, '(?m)^DATABASE_URL=sqlite:///.*$', "DATABASE_URL=$base/nutriplan.db")
        $envText = [regex]::Replace($envText, '(?m)^TEST_DATABASE_URL=sqlite:///.*$', "TEST_DATABASE_URL=$base/nutriplan_test.db")
        Write-Utf8NoBom $envFile $envText
    }
}

# --- 3. Database schema + dataset ---------------------------------------------------------
Step 'Preparing the database'
Push-Location $backend
try {
    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed - see the error above.' }
    & $python -m app.cli seed-catalogue
    if ($LASTEXITCODE -ne 0) { throw 'Loading the food dataset failed - see the error above.' }
} finally {
    Pop-Location
}

# --- 4. Backend -----------------------------------------------------------------------------
$apiPort = if ($Port -gt 0) { $Port } else { Get-FreePort 8000 }
if (-not (Test-PortFree $apiPort)) { throw "Port $apiPort is already in use. Choose another one with -Port." }
if ($apiPort -ne 8000 -and $Port -eq 0) { Write-Host "Port 8000 is busy - using $apiPort for the backend." }

$backendCmd = "`$Host.UI.RawUI.WindowTitle = 'NutriPlan backend (close to stop)'; Set-Location -LiteralPath '$backend'; "
if ($Production) {
    Step 'Building the frontend'
    Push-Location $frontend
    try {
        & npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed - see the error above.' }
    } finally {
        Pop-Location
    }
    $dist = Join-Path $frontend 'dist'
    $backendCmd += "`$env:FRONTEND_DIST_DIR = '$dist'; & '$python' -m uvicorn app.main:app --port $apiPort"
} else {
    $backendCmd += "& '$python' -m uvicorn app.main:app --reload --port $apiPort"
}

Step "Starting the backend on http://127.0.0.1:$apiPort"
Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', $backendCmd) | Out-Null
if (-not (Wait-Url "http://127.0.0.1:$apiPort/api/v1/health" 90)) {
    throw 'The backend did not start within 90 seconds - check the "NutriPlan backend" window for the error.'
}
Write-Host 'Backend is up.' -ForegroundColor Green

# --- 5. Frontend + browser ----------------------------------------------------------------
if ($Production) {
    $appUrl = "http://localhost:$apiPort"
} else {
    $webPort = Get-FreePort 5173
    $frontendCmd = "`$Host.UI.RawUI.WindowTitle = 'NutriPlan frontend (close to stop)'; Set-Location -LiteralPath '$frontend'; " +
        "`$env:VITE_API_PROXY_TARGET = 'http://127.0.0.1:$apiPort'; npm run dev -- --port $webPort --strictPort"
    Step "Starting the frontend on http://localhost:$webPort"
    Start-Process powershell -ArgumentList @('-NoExit', '-NoProfile', '-Command', $frontendCmd) | Out-Null
    $appUrl = "http://localhost:$webPort"
    if (-not (Wait-Url $appUrl 90)) {
        throw 'The frontend did not start within 90 seconds - check the "NutriPlan frontend" window for the error.'
    }
}

Write-Host "`nNutriPlan is running: $appUrl" -ForegroundColor Green
Write-Host "API docs:             http://127.0.0.1:$apiPort/docs"
Write-Host 'Close the NutriPlan server window(s) to stop.'
if (-not $NoBrowser) { Start-Process $appUrl }
