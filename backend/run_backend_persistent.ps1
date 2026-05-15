# LifeLink Backend Persistent Runner
# This script ensures the backend stays running

Write-Host "LifeLink Backend Persistent Runner" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Change to the script's directory
Set-Location $PSScriptRoot

# Set Python path
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

# Check if MongoDB is running
Write-Host "`nChecking MongoDB connection..." -ForegroundColor Yellow
& $Python -c "from test_backend import check_mongodb; import asyncio; raise SystemExit(0 if asyncio.run(check_mongodb()) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "MongoDB is not running! Please start MongoDB first." -ForegroundColor Red
    Write-Host "You can start MongoDB with: mongod" -ForegroundColor Yellow
    exit 1
}

# Kill any existing backend processes
Write-Host "`nChecking for existing backend processes..." -ForegroundColor Yellow
$existingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*main:*"
}
if ($existingProcesses) {
    Write-Host "Found existing backend processes. Stopping them..." -ForegroundColor Yellow
    $existingProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Start the backend
Write-Host "`nStarting LifeLink Backend..." -ForegroundColor Green
Write-Host "Backend will be available at: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server" -ForegroundColor Yellow

# Run uvicorn directly (not in background)
& $Python -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
