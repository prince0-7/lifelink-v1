@echo off
title LifeLink Backend Server
color 0A

echo LifeLink Backend Server
echo =======================
echo.

cd /d "%~dp0"

set PYTHON=python
if exist ".venv\Scripts\python.exe" set PYTHON=.venv\Scripts\python.exe

echo Checking MongoDB connection...
%PYTHON% -c "from test_backend import check_mongodb; import asyncio; raise SystemExit(0 if asyncio.run(check_mongodb()) else 1)" >nul 2>&1
if errorlevel 1 (
    echo MongoDB is not running! Please start MongoDB first.
    echo You can start MongoDB with: mongod
    pause
    exit /b 1
)

echo MongoDB is connected!
echo.
echo Starting LifeLink Backend...
echo Backend will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

%PYTHON% -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000

pause
