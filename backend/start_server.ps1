Write-Host "Starting Lifelink Backend Server..." -ForegroundColor Green
Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
