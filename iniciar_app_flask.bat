@echo off
setlocal

echo --------------------------------------
echo Iniciando entorno Flask...
echo --------------------------------------

REM Activar entorno virtual si existe
IF EXIST venv\Scripts\activate (
    call venv\Scripts\activate
    echo Entorno virtual activado.
) ELSE (
    echo [ADVERTENCIA] No se encontró el entorno virtual 'venv'.
    echo Asegúrate de crearlo con: python -m venv venv
)

REM Verificar que Flask esté instalado
pip show flask >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Flask no está instalado. Instálalo con:
    echo pip install flask
    pause
    exit /b
)

REM Iniciar el servidor Flask
echo Iniciando servidor...
start /B python web_app.py

REM Esperar unos segundos y abrir el navegador
timeout /t 3 >nul
start http://127.0.0.1:5000/login

echo Listo. Cerrando...
endlocal
