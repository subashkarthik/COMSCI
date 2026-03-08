@echo off
echo ===================================================
echo     WhatsApp Vernacular Fact-Checker Startup
echo ===================================================
echo.

echo [1/2] Starting Backend Server (FastAPI)...
start cmd /k "cd backend && call python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Dashboard (React/Vite)...
start cmd /k "cd dashboard && call npm run dev"

echo.
echo Servers are launching in separate windows!
echo Please wait a few seconds, then open:
echo    http://localhost:5173
echo.
echo ===================================================
echo   Hackathon Ready. Press any key to exit this script.
echo ===================================================
pause >nul
