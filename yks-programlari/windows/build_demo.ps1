param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $candidate = Join-Path $ProjectRoot 'venv\Scripts\python.exe'
    if (Test-Path $candidate) { $Python = $candidate } else { $Python = 'py' }
}
$spec = Join-Path $ProjectRoot 'tools\yki_paket\YKS.spec'
$out = Join-Path $ProjectRoot 'dist'
& $Python -X utf8 -B -m PyInstaller --noconfirm --distpath $out --workpath (Join-Path $ProjectRoot 'build\YKS') $spec
if ($LASTEXITCODE) { throw "Demo paketleme başarısız: $LASTEXITCODE" }
Write-Output (Join-Path $out 'YKS\YKS.exe')
