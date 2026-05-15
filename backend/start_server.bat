@echo off
echo Starting Lifelink Backend Server...
cd /d "%~dp0"
set PYTHONPATH=%cd%;%PYTHONPATH%
set PYTHON=python
if exist ".venv\Scripts\python.exe" set PYTHON=.venv\Scripts\python.exe
%PYTHON% -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
pause
