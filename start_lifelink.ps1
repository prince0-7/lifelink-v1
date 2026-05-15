# Starts the local LifeLink stack: MongoDB, backend API, and frontend UI.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$BackendPython = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host "Starting LifeLink local stack..." -ForegroundColor Cyan

$mongoService = Get-Service -Name MongoDB -ErrorAction SilentlyContinue
if ($mongoService) {
    if ($mongoService.Status -ne "Running") {
        Write-Host "Starting MongoDB service..." -ForegroundColor Yellow
        Start-Service -Name MongoDB
        Start-Sleep -Seconds 3
    }
} else {
    Write-Host "MongoDB service was not found. Install MongoDB Server or start mongod manually." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $BackendPython)) {
    Write-Host "Backend virtual environment not found at backend\.venv." -ForegroundColor Red
    Write-Host "Create it with: cd backend; python -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements-minimal.txt"
    exit 1
}

Write-Host "Checking MongoDB connection..." -ForegroundColor Yellow
Push-Location $Backend
& $BackendPython -c "from test_backend import test_mongodb; import asyncio; raise SystemExit(0 if asyncio.run(test_mongodb()) else 1)"
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    Write-Host "MongoDB is not reachable on localhost:27017." -ForegroundColor Red
    exit 1
}
Pop-Location

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Green
Start-Process -FilePath $BackendPython -ArgumentList "-m","uvicorn","main:socket_app","--reload","--host","0.0.0.0","--port","8000" -WorkingDirectory $Backend -WindowStyle Hidden

Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Green
Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev","--","--host","0.0.0.0" -WorkingDirectory $Frontend -WindowStyle Hidden

Start-Sleep -Seconds 4

Write-Host ""
Write-Host "LifeLink is running:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173"
Write-Host "  Backend:  http://localhost:8000"
Write-Host "  API Docs: http://localhost:8000/docs"
