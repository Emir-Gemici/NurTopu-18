# T140 — yedek aktarimini TEMIZ durdurur (betik duzenlemeden ONCE zorunlu).
#
# NEDEN AYRI DOSYA: sureci komut satirindaki desenle suzerken, KOMUTUN KENDISI
# de o deseni icerdigi icin kendi kabugunu oldurur. Ustabasi bunu bir kez
# yasadi (11:0x, exit 255). Desen artik BU DOSYADA duruyor; cagiran komut
# satirinda gecmiyor.
#
# SIRA: once rclone (aktarim), sonra betigi kosan bash. Tersi olursa betik
# yeni bir rclone dogurabilir.
$ErrorActionPreference = 'SilentlyContinue'

$r = Get-Process rclone -ErrorAction SilentlyContinue
if ($r) { $r | Stop-Process -Force; "rclone oldurulda: " + ($r.Id -join ',') }
else { "rclone zaten yok" }

Start-Sleep -Seconds 2

$hedef = '*yedek_drive.sh*'
$b = Get-CimInstance Win32_Process -Filter "Name='bash.exe'" |
     Where-Object { $_.CommandLine -like $hedef }
if ($b) {
  foreach ($p in $b) { Stop-Process -Id $p.ProcessId -Force; "bash oldurulda: " + $p.ProcessId }
} else { "yedek betigi kosan bash yok" }

Start-Sleep -Seconds 2
if (Get-Process rclone -ErrorAction SilentlyContinue) { "UYARI: rclone HALA VAR" }
else { "dogrulama: rclone YOK" }
