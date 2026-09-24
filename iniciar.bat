@echo off
REM Arranque de un clic del prototipo de identificacion de insectos.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    py -3.12 -m venv .venv
    .venv\Scripts\python -m pip install --upgrade pip
)

REM La .venv puede existir sin las dependencias del servidor (la de desarrollo, por ejemplo).
.venv\Scripts\python -c "import fastapi, uvicorn, onnxruntime, multipart" >nul 2>nul
if errorlevel 1 (
    echo Instalando las dependencias del servidor...
    .venv\Scripts\python -m pip install -r backend\requirements.txt
    if errorlevel 1 goto error
)

REM Corrida que sirve el prototipo: la misma que CORRIDA_VIGENTE en backend\app.py.
set "MODELO_DIR=modelo\v4_convnext_t_288"

for %%A in (insectos.onnx etiquetas.json) do (
    if not exist "%MODELO_DIR%\%%A" (
        echo.
        echo ERROR: falta %MODELO_DIR%\%%A
        echo Copia ahi insectos.onnx y etiquetas.json de la corrida ^(ver CLAUDE.md^).
        goto error
    )
)

REM frontend\dist no se versiona: en un clon nuevo hay que construirlo.
if not exist "frontend\dist\index.html" (
    where npm >nul 2>nul
    if errorlevel 1 (
        echo AVISO: falta frontend\dist y no se encontro npm. La API funcionara,
        echo pero sin interfaz web. Instala Node y ejecuta: cd frontend ^&^& npm install ^&^& npm run build
    ) else (
        echo Construyendo la interfaz web...
        pushd frontend
        call npm install
        call npm run build
        popd
        if not exist "frontend\dist\index.html" echo AVISO: no se pudo construir la interfaz web; la API funcionara sin ella.
    )
)

REM El navegador se abre recien cuando el servidor responde: cargar el modelo
REM tarda unos segundos y, si se abriera antes, la pagina daria error.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "for ($i = 0; $i -lt 120; $i++) { try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://127.0.0.1:8000/salud | Out-Null; Start-Process 'http://127.0.0.1:8000'; break } catch { Start-Sleep -Seconds 1 } }"

echo Iniciando el servidor en http://127.0.0.1:8000 ... ^(Ctrl+C para detenerlo^)
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000
if errorlevel 1 goto error
exit /b 0

:error
echo.
echo El prototipo no pudo arrancar. Revisa el mensaje de arriba.
pause
exit /b 1
