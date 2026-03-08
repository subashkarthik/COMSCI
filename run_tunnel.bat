@echo off
echo ===================================================
echo     WhatsApp Webhook Exposer (Pinggy)
echo ===================================================
echo.
echo Launching SSH Tunnel on Port 8000...
echo.
echo ===================================================
echo   IMPORTANT: When the URL appears below,
echo   copy the link that says "https://something.free.pinggy.link"
echo   
echo   Paste that URL into the Meta Developer Portal
echo   and make sure to add /webhook to the end!
echo ===================================================
echo.
ssh -p 443 -R0:localhost:8000 tcp@a.pinggy.io -o StrictHostKeyChecking=no
pause
