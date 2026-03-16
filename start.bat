@echo off
echo ===================================================
echo     WhatsApp Vernacular Fact-Checker Startup
echo ===================================================
echo.

echo [1/2] Starting Backend Server (FastAPI on port 8000)...
start cmd /k "cd /d d:\Hackathon_COMSCI\Whatsapp_FactChecker\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Dashboard (React/Vite on port 5173)...
start cmd /k "cd /d d:\Hackathon_COMSCI\Whatsapp_FactChecker\dashboard && npm run dev"

echo.
echo ===================================================
echo  Servers are launching in separate windows!
echo  Please wait a few seconds, then open:
echo    Dashboard:  http://localhost:5173
echo    API Docs:   http://localhost:8000/docs
echo.
echo  To expose for WhatsApp Webhook:
echo    Run 'run_tunnel.bat' separately
echo ===================================================
pause >nul
