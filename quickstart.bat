@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo Mercedes-Benz Stator Statusanzeige
echo Quickstart wird gestartet...
echo ========================================

echo.
py -m pip install Flask --index-url https://pypi.org/simple --disable-pip-version-check >nul 2>&1
if errorlevel 1 (
    python -m pip install Flask --index-url https://pypi.org/simple --disable-pip-version-check >nul 2>&1
)

echo Browser wird geoeffnet...
start http://127.0.0.1:5000

echo Anwendung startet...
py app.py
if errorlevel 1 (
    python app.py
)

pause
