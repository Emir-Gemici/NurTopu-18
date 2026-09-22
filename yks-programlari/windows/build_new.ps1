param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $candidate = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
    if (Test-Path $candidate) { $Python = $candidate } else { $Python = 'py' }
}
$env:NAVITAS_PROJECT_ROOT = $ProjectRoot
$spec = Join-Path $ProjectRoot 'yks-programlari\new\NAVITAS_YKI.spec'
$out = Join-Path $ProjectRoot 'yks-programlari\new\dist'
$work = Join-Path $ProjectRoot 'yks-programlari\new\build'
& $Python -X utf8 -B -m PyInstaller --noconfirm --distpath $out --workpath $work $spec
if ($LASTEXITCODE) { throw "NEW paketleme başarısız: $LASTEXITCODE" }
Write-Output (Join-Path $out 'NAVITAS_YKI\NAVITAS_YKI.exe')
