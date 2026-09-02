"""Hub'in UDP ucu SO_REUSEADDR ile acilir: ikinci hub ayni 127.0.0.1:PORT'a baglanabilir mi?"""
import sys
from pathlib import Path
KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "comms"))
from link import UDPLink

a = UDPLink(bind=("127.0.0.1", 0), timeout=0.2)
p = a.port
try:
    b = UDPLink(bind=("127.0.0.1", p), timeout=0.2)
    print(f"ikinci bind 127.0.0.1:{p} -> BASARILI (SO_REUSEADDR); b.port={b.port}")
except OSError as e:
    print("ikinci bind reddedildi:", e)
    sys.exit(0)
g = UDPLink()
for i in range(5):
    g.send(f"dg{i}".encode(), ("127.0.0.1", p))
import time; time.sleep(0.1)
def bosalt(l):
    out = []
    for _ in range(10):
        d, _a = l.recv()
        if not d:
            break
        out.append(d)
    return out
print("ilk soket aldi :", bosalt(a))
print("ikinci soket aldi:", bosalt(b))
