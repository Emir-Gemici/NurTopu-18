"""Seq uzayi: taze surecte protocol._seq 1'den baslar; KararYayinci'nin ILK cercevesi ne?"""
import sys
import time
from pathlib import Path
KOK = Path(r"O:\navitas")
for _y in (KOK / "comms", KOK / "codes"):
    sys.path.insert(0, str(_y))
from link import UDPLink
from protocol import FrameReader
from iha_sender import IhaSender, KararYayinci

dinle = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
link = UDPLink()
y = KararYayinci(IhaSender(link, {"yks": ("127.0.0.1", dinle.port)}),
                 wait_ack=False, repeat=1, interval=0.01).start()
y.karar(2, 0.9, [[0, 0], [10, 10]], 0.05)          # start() ile ayni anda karar
time.sleep(0.4)
y.stop()
r = FrameReader()
gelen = []
for _ in range(20):
    d, _a = dinle.recv()
    if d:
        gelen += [(m["type"], m["seq"]) for m in r.feed(d)]
print("taze surec, ilk cerceveler (type, seq):", gelen[:4])
