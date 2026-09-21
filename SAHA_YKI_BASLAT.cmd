@echo off
REM NAVITAS saha YKI acilisi (18 Eyl 2026 duzeni, D-494): once yer yonlendiricisi (COM7'nin TEK sahibi),
REM sonra yks_gui tunel+FDA kipinde. Mission Planner ONCEDEN COM7'den ayrilmis olmali; MP'ye UDP 14550 ile baglanilir.
REM Kullanim: SAHA_YKI_BASLAT.cmd [COMx]   (varsayilan COM7)
setlocal
set PY=O:\navitas-local-train\venv\Scripts\python.exe
set KOK=%~dp0
set PORT=%1
if "%PORT%"=="" set PORT=COM7
cd /d "%KOK%"
echo [1/2] yer yonlendiricisi: %PORT% ^<-^> MP udp 14550 + tunel udp 14590
start "NAVITAS yer yonlendiricisi (KAPATMA)" "%PY%" -u -B scripts\yer_yonlendirici.py --port %PORT% --baud 57600 --tunel 127.0.0.1:14590
timeout /t 4 /nobreak >nul
echo [2/2] YKI: tunel 127.0.0.1:14590, FDA kipi
start "NAVITAS YKI" "%PY%" -B comms\yks_gui.py --tunel 127.0.0.1:14590 --fda
echo.
echo Simdi Mission Planner: baglanti turu UDP, port 14550, Connect. YKI'de IHA yesil olmali.
echo Kapatirken once YKI penceresi, sonra yonlendirici penceresi kapatilir.
endlocal
