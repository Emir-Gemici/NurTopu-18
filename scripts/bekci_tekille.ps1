# T140 - coklu bekci ornegini temizler, TEK ornek birakir.
#
# NEDEN AYRI DOSYA: sureci komut satiri desenine gore suzerken, KOMUTUN KENDISI
# de deseni icerdigi icin kendi kabugunu oldurur. Ustabasi bunu IKI KEZ yasadi
# (exit 255). Desen artik yalniz BU DOSYADA.
#
# NEDEN SADECE ASCII: PowerShell 5.1 .ps1 dosyalarini BOM yoksa ANSI okur;
# em-dash ve Turkce harfler ayristirma hatasi verir (bir kez oldu). Bu dosya
# ASCII tutulur.
$ErrorActionPreference = 'SilentlyContinue'
$desen = '*yedek_bekcisi*'
$hepsi = @(Get-CimInstance Win32_Process -Filter "Name='bash.exe'" |
           Where-Object { $_.CommandLine -like $desen } |
           Sort-Object CreationDate)
if ($hepsi.Count -le 1) {
  "bekci ornegi: " + $hepsi.Count + " - temizlik gerekmiyor"
  exit 0
}
$kalan = $hepsi[-1]
foreach ($p in $hepsi) {
  if ($p.ProcessId -ne $kalan.ProcessId) {
    Stop-Process -Id $p.ProcessId -Force
    "oldurulen bekci PID: " + $p.ProcessId
  }
}
"kalan bekci PID: " + $kalan.ProcessId
