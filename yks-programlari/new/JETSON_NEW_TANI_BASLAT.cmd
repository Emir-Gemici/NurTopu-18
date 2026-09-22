@echo off
REM Salt okunur Jetson tanisi. Sifre dosyaya yazilmaz. Internet gerekmez.
setlocal
cd /d "%~dp0\..\.."
set "JETSON_HOST=%~1"
if "%JETSON_HOST%"=="" set "JETSON_HOST=fe80::1%%22"
set "PYTHON=%NAVITAS_PYTHON%"
if "%PYTHON%"=="" if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
if "%PYTHON%"=="" set "PYTHON=py"
"%PYTHON%" -X utf8 -B scripts\jetson_tani_aktar.py --host "%JETSON_HOST%"
endlocal
