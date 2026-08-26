# EGITIM IZLEYICI — gece_v7a / v7b (ya da --log ile herhangi bir ultralytics logu)
# Kullanim:  powershell -NoExit -File scripts\egitim_izle.ps1
param([string]$Log = "")
$kok = "O:\navitas"
$host.UI.RawUI.WindowTitle = "NAVITAS egitim izleyici"
function SonLog {
    if ($Log) { return $Log }
    foreach ($ad in @("v7b", "v7a")) {
        $p = "$kok\results\gece_20260826\egitim_$ad.log"
        if (Test-Path $p) {
            $son = Get-Content $p -Tail 3 -ErrorAction SilentlyContinue
            if (-not ($son -match '^EXIT')) { return $p }
        }
    }
    return "$kok\results\gece_20260826\egitim_v7a.log"
}
while ($true) {
    $p = SonLog
    $ad = [IO.Path]::GetFileNameWithoutExtension($p) -replace '^egitim_', ''
    $raw = ""
    try {
        # yazan surec dosyayi acik tutuyor: paylasimli okuma (ReadWrite) sart
        $fs = New-Object IO.FileStream($p, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        $sr = New-Object IO.StreamReader($fs)
        $raw = $sr.ReadToEnd(); $sr.Close(); $fs.Close()
    } catch { $raw = "" }
    $parcalar = $raw -split "[`r`n]+" | Where-Object { $_ -match '\S' }
    $son = if ($parcalar.Count) { $parcalar[-1] } else { "" }
    $epoch = ""; $eta = ""; $hiz = ""
    if ($son -match '\s(\d+)/(\d+)\s') { $epoch = "epoch $($Matches[1])/$($Matches[2])" }
    if ($son -match '(\d+)/(\d+)\s+[\d\.]+it/s\s+[\d:]+<([\d:]+)') { $hiz = "it $($Matches[1])/$($Matches[2])"; $eta = "epoch ETA $($Matches[3])" }
    $csv = "$kok\codes\runs\segment\gece_${ad}_v35taban\results.csv"
    $biten = 0; $best = ""
    if (Test-Path $csv) {
        $rows = Import-Csv $csv
        $biten = $rows.Count
        if ($biten) {
            $b = $rows | Sort-Object { [double]$_.'metrics/mAP50-95(M)' } -Descending | Select-Object -First 1
            $best = "best epoch $($b.epoch) mAP50-95(M) $([math]::Round([double]$b.'metrics/mAP50-95(M)',4))"
        }
    }
    $durum = if ($raw -match 'EXIT (\d+)\s*$') { "BITTI (exit $($Matches[1]))" } else { "KOSUYOR" }
    $toplam = if ($son -match '\s\d+/(\d+)\s') { [int]$Matches[1] } else { 0 }
    $kalanTahmin = ""
    if ($biten -gt 0 -and $toplam -gt 0) {
        $ilk = (Get-Item $p).CreationTime; $simdi = Get-Date
        $gecen = ($simdi - $ilk).TotalMinutes
        if ($gecen -gt 0) { $dk = [math]::Round($gecen / $biten * ($toplam - $biten), 0); $kalanTahmin = "toplam ETA ~${dk} dk (erken durdurma olabilir)" }
    }
    Clear-Host
    Write-Host ("{0}  {1}  [{2}]" -f (Get-Date -Format 'HH:mm:ss'), $ad, $durum) -ForegroundColor Cyan
    Write-Host ("  {0}   {1}   {2}" -f $epoch, $hiz, $eta) -ForegroundColor Yellow
    Write-Host ("  biten epoch: {0}   {1}" -f $biten, $best) -ForegroundColor Green
    if ($kalanTahmin) { Write-Host ("  {0}" -f $kalanTahmin) -ForegroundColor Green }
    Write-Host ("  log: {0}" -f $p) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host ($son.Substring(0, [Math]::Min(150, $son.Length))) -ForegroundColor Gray
    $gpu = & nvidia-smi --query-gpu=temperature.gpu,memory.used,utilization.gpu --format=csv,noheader 2>$null
    if ($gpu) { Write-Host ("  GPU: {0}" -f $gpu) -ForegroundColor DarkGray }
    Start-Sleep -Seconds 5
}
