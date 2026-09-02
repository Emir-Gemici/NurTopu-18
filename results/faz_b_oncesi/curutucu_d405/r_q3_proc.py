"""Q3d uctan uca: GERCEK seri_hub.py SURECI (CLI, calistir dongusu) derin ic ice satirda olur mu?"""
import subprocess
import sys
import time
from pathlib import Path
KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "comms")); sys.path.insert(0, str(KOK / "tests"))
from test_p2_seri_hat import SikKoprusu
from link import SerialLink
from protocol import encode, command

kopru = SikKoprusu()
proc = subprocess.Popen(
    [sys.executable, str(KOK / "comms" / "seri_hub.py"), "--port",
     f"socket://127.0.0.1:{kopru.port}", "--bind", "127.0.0.1:0", "--log-aralik", "0"],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
time.sleep(0.8)                                   # hub baglansin (kopru ucu 1)
yks = SerialLink(f"socket://127.0.0.1:{kopru.port}", 57600, timeout=0.05)   # kopru ucu 2
time.sleep(0.3)
print("hub sureci yasiyor mu (once):", proc.poll() is None)
yks.send(encode(command("ARM", "iha", seq=1)))   # saglikli cerceve
time.sleep(0.3)
yks.send(b"[" * 3000 + b"\n")                     # derin ic ice satir
try:
    rc = proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    rc = None
    proc.kill()
out, err = proc.communicate(timeout=5)
print("hub sureci cikis kodu:", rc, "(None = 10 s icinde olmedi)")
print("stdout:", out.strip()[-300:])
print("stderr son satirlar:")
for l in err.strip().splitlines()[-4:]:
    print("   ", l)
yks.close(); kopru.kapat()
