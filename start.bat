@echo off
echo Starting NEXUS backend...
cd /d "%~dp0"
set PYTHONPATH=src
start "NEXUS Backend" py -3.11 -m uvicorn nexus.api.main:app --reload --port 8000
echo Backend starting on http://localhost:8000
echo.
echo Frontend: run "npm run dev" in nexus-frontend\ separately
echo Or open a new terminal and run: cd nexus-frontend ^&^& npm run dev
