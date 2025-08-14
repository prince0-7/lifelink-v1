@echo off
echo Starting Lifelink Backend Server...
cd /d "%~dp0"
set PYTHONPATH=%cd%;%PYTHONPATH%
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
