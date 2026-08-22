# T140 - yedek/bekci sureclerini YONET (durdur, tekille, durum).
#
# 🔴 UC KEZ OGRENILEN DERS (exit 255 x3): sureci komut satiri desenine gore
# suzerken, CAGIRAN KOMUTUN KENDISI de o deseni icerdigi icin kendi kabugunu
# oldurur. Ustabasi bunu uc kez yasadi. IKI KORUMA birden uygulanir:
#   1) Desenler yalniz BU DOSYADA gecer.
#   2) `-c` ile cagrilan bash'ler DISLANIR. Gercek arka plan islerimiz
#      `bash.exe <betik>` seklinde kosar; benim kabuk cagrilarim
#      `bash.exe -c "..."` seklindedir. Bu ayrim OZ-OLDURMEYI imkansiz kilar.
#
# NEDEN SADECE ASCII: PowerShell 5.1 BOM'suz .ps1'i ANSI okur; em-dash ve
# Turkce harfler ayristirma hatasi verir (bir kez oldu).
param([ValidateSet('durum','durdur','tekille')] [string]$Kip = 'durum')
$ErrorActionPreference = 'SilentlyContinue'

function Bul($desen) {
  @(Get-CimInstance Win32_Process -Filter "Name='bash.exe'" | Where-Object {
      $_.CommandLine -like $desen -and $_.CommandLine -notlike '* -c *'
    } | Sort-Object CreationDate)
}

$yedek = Bul '*yedek_drive.sh*'
$bekci = Bul '*yedek_bekcisi.sh*'
$rclone = @(Get-Process rclone -ErrorAction SilentlyContinue)

switch ($Kip) {
  'durum' {
    "yedek betigi : " + $yedek.Count + " ornek " + (($yedek | ForEach-Object { $_.ProcessId }) -join ',')
    "bekci        : " + $bekci.Count + " ornek " + (($bekci | ForEach-Object { $_.ProcessId }) -join ',')
    "rclone       : " + $rclone.Count + " ornek " + (($rclone | ForEach-Object { $_.Id }) -join ',')
  }
  'durdur' {
    if ($rclone) { $rclone | Stop-Process -Force; "rclone oldurulda" } else { "rclone yok" }
    Start-Sleep -Seconds 2
    foreach ($p in $yedek) { Stop-Process -Id $p.ProcessId -Force; "yedek bash oldurulda: " + $p.ProcessId }
    foreach ($p in $bekci) { Stop-Process -Id $p.ProcessId -Force; "bekci oldurulda: " + $p.ProcessId }
    Start-Sleep -Seconds 2
    if (Get-Process rclone -ErrorAction SilentlyContinue) { "UYARI: rclone HALA VAR" } else { "dogrulama: rclone YOK" }
  }
  'tekille' {
    foreach ($grup in @(,$yedek), @(,$bekci)) {
      $g = $grup[0]
      if ($g.Count -gt 1) {
        $kalan = $g[-1]
        foreach ($p in $g) {
          if ($p.ProcessId -ne $kalan.ProcessId) { Stop-Process -Id $p.ProcessId -Force; "fazla ornek oldurulda: " + $p.ProcessId }
        }
        "kalan: " + $kalan.ProcessId
      }
    }
    "tekilleme bitti"
  }
}
