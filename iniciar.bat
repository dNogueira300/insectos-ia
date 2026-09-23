@echo off
REM Arranque de un clic del prototipo de identificacion de insectos.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno virtual...
    py -3.12 -m venv .venv
    .venv\Scripts\python -m pip install --upgrade pip
    .venv\Scripts\python -m pip install -r backend\requirements.txt
)

REM Corrida que sirve el prototipo: la misma que CORRIDA_VIGENTE en backend\app.py.
set "MODELO_DIR=modelo\v4_convnext_t_288"

if not exist "%MODELO_DIR%\insectos.onnx" (
    echo.
    echo ERROR: falta %MODELO_DIR%\insectos.onnx
    echo Copia ahi insectos.onnx y etiquetas.json de la corrida ^(ver CLAUDE.md^).
    echo.
    pause
    exit /b 1
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
    )
)

echo Iniciando el servidor en http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn backend.app:app_produccion --factory --port 8000
