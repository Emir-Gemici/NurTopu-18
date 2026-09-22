@echo off
REM NEW gelistirme testi: yalniz loopback, telsiz/seri port ACMAZ.
setlocal
cd /d "%~dp0\..\.."
set "PYTHON=%NAVITAS_PYTHON%"
if "%PYTHON%"=="" if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"
if "%PYTHON%"=="" set "PYTHON=py"
"%PYTHON%" -X utf8 -B comms\yks_gui.py --bind 127.0.0.1:15991 --iha 127.0.0.1:15992 --ika 127.0.0.1:15993 --fda --sistem-gunlugu
endlocal
