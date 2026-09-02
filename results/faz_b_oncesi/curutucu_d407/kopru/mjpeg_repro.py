"""MJPEG cerceveleme + uzun kosum (300 kare) bellek/iplik olcumu."""
import gc
import socket
import sys
import tempfile
import threading
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ortak import kk, cv2, np, sahte_avi, kopru, bekle, durum, BOYUT  # noqa: E402

try:
    import psutil
    _proc = psutil.Process()
    def rss(): return _proc.memory_info().rss / 1e6
except Exception:
    def rss(): return float("nan")


def ham_akis_oku(port, n, zaman_asimi=10.0):
    """Ham soketle /video'yu oku, multipart cerceveyi KENDIMIZ ayristir; her sapmayi listele."""
    s = socket.create_connection(("127.0.0.1", port), timeout=zaman_asimi)
    s.sendall(b"GET /video HTTP/1.0\r\nHost: x\r\n\r\n")
    buf = b""
    while b"\r\n\r\n" not in buf:
        p = s.recv(65536)
        if not p:
            raise RuntimeError("baslik gelmeden kapandi: %r" % buf[:200])
        buf += p
    bas, buf = buf.split(b"\r\n\r\n", 1)
    satirlar = bas.decode("latin-1").split("\r\n")
    durum_satiri = satirlar[0]
    basliklar = {}
    for st in satirlar[1:]:
        k, _, v = st.partition(":")
        basliklar[k.strip().lower()] = v.strip()
    ct = basliklar.get("content-type", "")
    sapmalar = []
    if not durum_satiri.startswith("HTTP/1.0 200"):
        sapmalar.append("durum satiri: " + durum_satiri)
    if "multipart/x-mixed-replace" not in ct or "boundary=" not in ct:
        sapmalar.append("Content-Type: " + ct)
    sinir = ct.split("boundary=", 1)[1].strip().strip('"') if "boundary=" in ct else None
    on_ek = ("--" + sinir).encode() if sinir else b"--"
    kareler = 0
    boyutlar = set()
    siralar = []
    t0 = time.monotonic()

    def oku_kadar(gerek):
        nonlocal buf
        while len(buf) < gerek:
            p = s.recv(65536)
            if not p:
                raise RuntimeError("akis kapandi (kare %d)" % kareler)
            buf += p

    while kareler < n:
        # parca basligi
        while b"\r\n\r\n" not in buf:
            p = s.recv(65536)
            if not p:
                raise RuntimeError("parca basligi gelmeden kapandi (kare %d)" % kareler)
            buf += p
        pb, buf = buf.split(b"\r\n\r\n", 1)
        satirlar = pb.split(b"\r\n")
        if satirlar[0] != on_ek:
            sapmalar.append("kare %d: sinir satiri %r != %r" % (kareler, satirlar[0][:40], on_ek))
        ph = {}
        for st in satirlar[1:]:
            k, _, v = st.partition(b":")
            ph[k.strip().lower()] = v.strip()
        if ph.get(b"content-type") != b"image/jpeg":
            sapmalar.append("kare %d: parca Content-Type %r" % (kareler, ph.get(b"content-type")))
        if b"content-length" not in ph:
            sapmalar.append("kare %d: Content-Length yok" % kareler)
            raise RuntimeError("Content-Length yok; ayristirilamaz")
        cl = int(ph[b"content-length"])
        oku_kadar(cl + 2)
        veri, kuyruk, buf = buf[:cl], buf[cl:cl + 2], buf[cl + 2:]
        if kuyruk != b"\r\n":
            sapmalar.append("kare %d: parca sonu %r != CRLF" % (kareler, kuyruk))
        if not (veri[:2] == b"\xff\xd8" and veri[-2:] == b"\xff\xd9"):
            sapmalar.append("kare %d: JPEG SOI/EOI yok (%r..%r) — Content-Length yanlis?" % (kareler, veri[:2], veri[-2:]))
        k = cv2.imdecode(np.frombuffer(veri, np.uint8), cv2.IMREAD_COLOR)
        if k is None:
            sapmalar.append("kare %d: imdecode None" % kareler)
        else:
            boyutlar.add(k.shape)
        siralas = len(veri)
        siralar.append(siralas)
        kareler += 1
    s.close()
    return {"kare": kareler, "sure_s": round(time.monotonic() - t0, 2), "sapma": sapmalar[:10],
            "sapma_sayisi": len(sapmalar), "boyutlar": sorted(boyutlar), "ilk_baslik": basliklar,
            "jpeg_bayt_min_max": (min(siralar), max(siralar))}


def main():
    dizin = tempfile.TemporaryDirectory()
    avi = sahte_avi(dizin.name)
    sunucu, uretici, port, loglar = kopru(avi, fps_tavani=60.0)
    assert bekle(lambda: durum(port)["kare_sayaci"] >= 1)
    print("kopru port", port, "durum", durum(port))

    # (a) ham cerceve dogrulama: 60 kare
    print("\n== (a) ham multipart ayristirma (60 kare) ==")
    print(ham_akis_oku(port, 60))

    # (b) cv2.VideoCapture ile 300 kare + tracemalloc + iplik sayisi
    print("\n== (b) cv2.VideoCapture 300 kare, tracemalloc/iplik/RSS ==")
    gc.collect()
    tracemalloc.start(10)
    cap = cv2.VideoCapture(kk.video_url(port))
    assert cap.isOpened(), "cv2 acamadi"
    ok_say = 0
    t0 = time.monotonic()
    snap0 = tracemalloc.take_snapshot()
    ipl0 = threading.active_count()
    rss0 = rss()
    kayit = []
    for i in range(1, 301):
        ok, kare = cap.read()
        if ok and kare is not None:
            ok_say += 1
        if i in (50, 150, 300):
            gc.collect()
            cur, peak = tracemalloc.get_traced_memory()
            kayit.append((i, round(cur / 1e6, 3), round(peak / 1e6, 3), threading.active_count(), round(rss(), 1),
                          durum(port)["istemci_sayisi"]))
    snap1 = tracemalloc.take_snapshot()
    sure = time.monotonic() - t0
    print("okunan=%d/300 sure=%.1fs (%.1f fps) ipl0=%d rss0=%.1fMB" % (ok_say, sure, ok_say / sure, ipl0, rss0))
    print("kare, traced_MB, peak_MB, iplik, rss_MB, istemci_sayisi")
    for k in kayit:
        print("  ", k)
    farklar = snap1.compare_to(snap0, "lineno")
    print("tracemalloc en buyuk 6 fark (kamera_koprusu satirlari isaretli):")
    for f in farklar[:6]:
        print("   ", f)
    kk_farklar = [f for f in farklar if "kamera_koprusu" in str(f)]
    print("kamera_koprusu kaynakli farklar:", [str(f) for f in kk_farklar[:5]])
    cap.release()
    tracemalloc.stop()

    # (c) ardisik 40 istemci ac/kapa — iplik ve istemci_sayisi
    print("\n== (c) 40 ardisik istemci (raw + cv2 karisik) ==")
    ipl_once = threading.active_count()
    for i in range(40):
        if i % 2 == 0:
            r = ham_akis_oku(port, 3)
            assert r["sapma_sayisi"] == 0, r
        else:
            c = cv2.VideoCapture(kk.video_url(port))
            assert c.isOpened()
            for _ in range(3):
                c.read()
            c.release()
    bekle(lambda: durum(port)["istemci_sayisi"] == 0, tavan_s=3.0)
    time.sleep(0.5)
    print("iplik once=%d sonra=%d istemci_sayisi=%d rss=%.1fMB" % (
        ipl_once, threading.active_count(), durum(port)["istemci_sayisi"], rss()))
    print("aktif iplik adlari:", sorted(t.name for t in threading.enumerate()))
    d = durum(port)
    print("son durum:", d)
    kirmizi = [m for _, k, m in loglar if k]
    print("KIRMIZI log sayisi:", len(kirmizi), kirmizi[:3])
    kk.kopru_kapat(sunucu, uretici)
    dizin.cleanup()


if __name__ == "__main__":
    main()
