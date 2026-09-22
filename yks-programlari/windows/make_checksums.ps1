param([string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference = 'Stop'
foreach ($folder in @('demo','new')) {
    $dir = Join-Path $ProjectRoot "yks-programlari\$folder"
    $lines = Get-ChildItem $dir -File |
        Where-Object { $_.Name -notlike 'SHA256SUMS.txt' } |
        Sort-Object Name |
        ForEach-Object {
            $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
            "$hash  $($_.Name)"
        }
    $lines | Set-Content -Encoding utf8 (Join-Path $dir 'SHA256SUMS.txt')
}
