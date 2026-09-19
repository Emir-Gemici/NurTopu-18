Add-Type -AssemblyName System.Drawing
Add-Type @"
using System; using System.Runtime.InteropServices;
public class W3 { [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint f);
 public struct RECT { public int L, T, R, B; } }
"@
[W3]::SetProcessDPIAware() | Out-Null
$dir = "O:\navitas\results\telsiz_20260919\kanit_panel"; New-Item -ItemType Directory -Force $dir | Out-Null
$ids = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*yks_gui.py --tunel 127.0.0.1:14590*' } | Select-Object -ExpandProperty ProcessId
$p = $ids | ForEach-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue } | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
$hw = $p.MainWindowHandle; $bas = Get-Date
while (((Get-Date) - $bas).TotalSeconds -lt 240) {
  $r = New-Object W3+RECT; [W3]::GetWindowRect($hw, [ref]$r) | Out-Null; $w = $r.R - $r.L; $h = $r.B - $r.T
  $bmp = New-Object System.Drawing.Bitmap $w, $h; $g = [System.Drawing.Graphics]::FromImage($bmp); $hdc = $g.GetHdc()
  [W3]::PrintWindow($hw, $hdc, 2) | Out-Null; $g.ReleaseHdc($hdc)
  $x0 = [int]($w * 0.733); $y0 = [int]($h * 0.52); $cw = $w - $x0 - 5; $ch = [int]($h * 0.20)
  $crop = $bmp.Clone((New-Object System.Drawing.Rectangle $x0, $y0, $cw, $ch), $bmp.PixelFormat)
  $crop.Save("$dir\panel_$((Get-Date).ToString('HHmmss')).png"); $crop.Dispose(); $g.Dispose(); $bmp.Dispose()
  Start-Sleep -Seconds 4
}
"bitti: $((Get-ChildItem $dir).Count) goruntu"
