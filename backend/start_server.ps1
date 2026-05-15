Write-Host "Starting Lifelink Backend Server..." -ForegroundColor Green
Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
& $Python -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
