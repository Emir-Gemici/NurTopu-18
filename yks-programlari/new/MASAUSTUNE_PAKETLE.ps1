# NEDEN: dogrulanabilir, tekrarlanabilir Windows YKI paketi ve masaustu kisayolu.
$ErrorActionPreference = 'Stop'
$projectRoot = 'O:\navitas'
$pythonExe = 'O:\navitas-local-train\venv\Scripts\python.exe'
$buildRoot = Join-Path $projectRoot 'results\yki_exe_20260922'
$env:PYINSTALLER_CONFIG_DIR = Join-Path $buildRoot 'pyinstaller_cache'
Set-Location -LiteralPath $projectRoot
$buildProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-X','utf8','-B','-m','PyInstaller','--noconfirm','--distpath',(Join-Path $buildRoot 'dist'),'--workpath',(Join-Path $buildRoot 'build'),(Join-Path $buildRoot 'NAVITAS_YKI.spec')) -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $buildRoot 'build_stdout.log') -RedirectStandardError (Join-Path $buildRoot 'build_stderr.log') -Wait -PassThru
if ($buildProcess.ExitCode -ne 0) { throw "Paketleme basarisiz: $($buildProcess.ExitCode)" }
$package = Join-Path $buildRoot 'dist\NAVITAS_YKI'
foreach ($name in @('OKUBENI.txt','SURUM.json')) {
    Copy-Item -LiteralPath (Join-Path $buildRoot $name) -Destination (Join-Path $package $name)
}
$testProcess = Start-Process -FilePath (Join-Path $package 'NAVITAS_YKI.exe') -ArgumentList '--self-test' -WorkingDirectory $package -WindowStyle Hidden -Wait -PassThru
if ($testProcess.ExitCode -ne 0) { throw 'EXE bagimlilik/model testi basarisiz; results\launcher kaydini inceleyin.' }
$desktop = [Environment]::GetFolderPath('Desktop')
$destination = Join-Path $desktop ('NAVITAS_YKI_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
Copy-Item -LiteralPath $package -Destination $destination -Recurse
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'NAVITAS YKI.lnk'))
$shortcut.TargetPath = Join-Path $destination 'NAVITAS_YKI.exe'
$shortcut.WorkingDirectory = $destination
$shortcut.Description = 'NAVITAS YKI - radyo telemetri'
$shortcut.Save()
Write-Output ('EXE: ' + (Join-Path $destination 'NAVITAS_YKI.exe'))
Write-Output ('KISAYOL: ' + (Join-Path $desktop 'NAVITAS YKI.lnk'))
