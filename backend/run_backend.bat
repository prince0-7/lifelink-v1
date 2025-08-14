@echo off
title LifeLink Backend Server
color 0A

echo LifeLink Backend Server
echo =======================
echo.

cd /d "%~dp0"

echo Checking MongoDB connection...
python test_mongo.py >nul 2>&1
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

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
