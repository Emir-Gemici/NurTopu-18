# Deney: venv launcher -> ebeveyn python -> torun python;
# subprocess.run(timeout) kill() sonrasi kim sag kalir? (Windows, Python 3.13 venv)
import subprocess, sys, time

PY = sys.executable
EBEVEYN = (
    "import subprocess, sys, time\n"
    "c = subprocess.Popen([sys.executable, '-c', "
    "\"import time; print('TORUN_ISARETI', flush=True); time.sleep(60)\"], "
    "stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)\n"
    "print('EBEVEYN_ISARETI', flush=True)\n"
    "c.wait()\n"
)


def sag_kalanlar():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "
         "'TORUN_ISARETI|EBEVEYN_ISARETI' } | ForEach-Object { '{0} parent={1} "
         "exe={2}' -f $_.ProcessId, $_.ParentProcessId, $_.ExecutablePath }"],
        capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if l.strip()]


t0 = time.time()
try:
    subprocess.run([PY, "-c", EBEVEYN], capture_output=True, text=True, timeout=3)
    print("bitti (beklenmiyor)")
except subprocess.TimeoutExpired:
    print("TimeoutExpired after %.1f s" % (time.time() - t0))
kalan = sag_kalanlar()
print("run() dondu; sag kalanlar (%d):" % len(kalan))
for l in kalan:
    print("  ", l)
for l in kalan:
    subprocess.run(["taskkill", "/PID", l.split()[0], "/T", "/F"], capture_output=True)
print("temizlik sonrasi:", len(sag_kalanlar()))
