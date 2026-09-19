@echo off
REM NAVITAS YKİ paketleyici — proje kökünden çalıştır: tools\yki_paket\paketle.bat
set PY=O:\navitas-local-train\venv\Scripts\python.exe
cd /d %~dp0..\..
%PY% -m PyInstaller --noconfirm --clean --distpath dist --workpath build tools\yki_paket\YKS.spec
if errorlevel 1 exit /b 1
copy /y tools\yki_paket\YKS_baslat.bat dist\YKS\ >nul
copy /y tools\yki_paket\OKUBENI.txt dist\YKS\ >nul
echo PAKET: dist\YKS\
for /f %%h in ('git rev-parse HEAD') do set COMMIT=%%h
> dist\YKS\SURUM.txt echo NAVITAS YKS paketi · commit %COMMIT% · %date% %time%
echo SURUM: %COMMIT%
