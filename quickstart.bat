@echo off
cd /d "%~dp0"

echo ========================================
echo Motor Auftragssteuerung - Quickstart
echo ========================================
echo.

echo [1/3] Flask-Abhaengigkeiten...
py -m pip install Flask --index-url https://pypi.org/simple --disable-pip-version-check >nul 2>&1
echo       OK

echo [2/3] Frontend pruefen...
if not exist "frontend\node_modules" (
    echo       Installiere npm-Pakete...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)
echo       OK

echo [3/3] Starte Server...
echo.

:: Flask im Hintergrund starten
start "Flask Backend" /min cmd /c "cd /d "%~dp0" && py app.py"

:: Warten bis Flask bereit
timeout /t 3 /nobreak >nul

echo       Backend laeuft auf http://127.0.0.1:5000
echo       Frontend startet jetzt (Browser oeffnet automatisch)...
echo.
echo       Dieses Fenster offen lassen!
echo       Zum Beenden: Ctrl+C
echo.

:: Vite startet und oeffnet Browser selbst
cd /d "%~dp0frontend"
call npx vite --host 127.0.0.1 --port 5173 --open

pause
