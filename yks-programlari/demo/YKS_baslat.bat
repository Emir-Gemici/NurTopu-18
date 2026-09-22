@echo off
REM NAVITAS YKİ başlatıcı. Bu dosyanın yanındaki YKS.exe'yi çalıştırır.
REM Kullanım örnekleri (OKUBENI.txt):
REM   YKS_baslat.bat --demo
REM   YKS_baslat.bat --tunel 127.0.0.1:14590 --fda
REM   YKS_baslat.bat --serial COM5 --baud 57600 --fda
cd /d %~dp0
if "%~1"=="" (
  echo Argüman verilmedi; DEMO kipinde açılıyor. Saha için OKUBENI.txt'ye bak.
  YKS.exe --demo
) else (
  YKS.exe %*
)
if errorlevel 1 (
  echo.
  echo YKS hata ile kapandı. Yukarıdaki satırları ekip yazılımcısına gönder.
  pause
)
