"""Curutucu ortak yardimcilar: kopruyu O:\\navitas\\scripts'ten SALT OKUNUR import eder."""
import sys
import threading
import time
from pathlib import Path

sys.dont_write_bytecode = True          # O:\navitas altina __pycache__ YAZMA
for _y in (r"O:\navitas\scripts", r"O:\navitas\codes", r"O:\navitas\comms"):
    if _y not in sys.path:
        sys.path.insert(0, _y)

import cv2          # noqa: E402
import numpy as np  # noqa: E402
import kamera_koprusu as kk  # noqa: E402

BOYUT = (320, 240)


def sahte_avi(dizin, ad="sahte.avi", n=30, boyut=BOYUT):
    yol = Path(dizin) / ad
    w = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, boyut)
    assert w.isOpened()
    for i in range(n):
        k = np.zeros((boyut[1], boyut[0], 3), np.uint8)
        k[:, :, 0] = (i * 8) % 256
        k[:, :, 1] = 255 - (i * 8) % 256
        k[:, :, 2] = 40
        cv2.putText(k, str(i), (20, boyut[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        w.write(k)
    w.release()
    return yol


def kopru(kaynak, port=0, loglar=None, **kw):
    loglar = [] if loglar is None else loglar

    def log(metin, kirmizi=False):
        loglar.append((time.monotonic(), kirmizi, metin))

    sunucu, uretici = kk.kopru_kur(str(kaynak), port=port, log_aralik_s=0, log=log, **kw)
    ip = threading.Thread(target=sunucu.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    ip.start()
    return sunucu, uretici, sunucu.server_address[1], loglar


def bekle(kosul, tavan_s=8.0, adim_s=0.05):
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis:
        if kosul():
            return True
        time.sleep(adim_s)
    return kosul()


def durum(port):
    import json
    import urllib.request
    with urllib.request.urlopen("http://127.0.0.1:%d/durum" % port, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))


def http_kod(port, yol):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, yol), timeout=8) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
