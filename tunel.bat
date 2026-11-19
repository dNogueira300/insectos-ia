@echo off
REM Plan B de la demostracion: publica en internet el INSECTIA de esta laptop
REM con un Cloudflare Quick Tunnel. No hace falta cuenta ni tarjeta.
REM Uso: primero iniciar.bat (en otra ventana), luego este archivo.
cd /d "%~dp0"

where cloudflared >nul 2>nul
if errorlevel 1 (
    echo Falta cloudflared. Instalalo una vez con:
    echo     winget install --id Cloudflare.cloudflared
    echo y vuelve a abrir esta ventana.
    goto error
)

powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 http://127.0.0.1:8000/salud | Out-Null } catch { exit 1 }"
if errorlevel 1 (
    echo INSECTIA no responde en http://127.0.0.1:8000.
    echo Abre primero iniciar.bat y espera a que cargue el navegador.
    goto error
)

echo.
echo Abriendo el tunel. En unos segundos aparecera una direccion como
echo     https://palabras-al-azar.trycloudflare.com
echo Esa es la direccion publica: abrela en el celular o hazle un QR.
echo Cambia cada vez que se abre el tunel. Ctrl+C para cerrarlo.
echo.
cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8000
exit /b 0

:error
echo.
pause
exit /b 1
