"""Istemci kopunca: uretici yasiyor mu, istemci_sayisi dusuyor mu, ikinci istemci baglaniyor mu?"""
import socket
import struct
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ortak import kk, cv2, sahte_avi, kopru, bekle, durum  # noqa: E402


def ham_baglan(port):
    s = socket.create_connection(("127.0.0.1", port), timeout=10)
    s.sendall(b"GET /video HTTP/1.0\r\nHost: x\r\n\r\n")
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(65536)
    return s


def n_parca_oku(s, n):
    """Kabaca n sinir satiri gorunene kadar oku."""
    buf = b""
    while buf.count(b"--" + kk.SINIR.encode()) < n + 1:
        p = s.recv(65536)
        if not p:
            raise RuntimeError("kapandi")
        buf += p
    return len(buf)


def main():
    dizin = tempfile.TemporaryDirectory()
    avi = sahte_avi(dizin.name)
    sunucu, uretici, port, loglar = kopru(avi, fps_tavani=10.0)
    assert bekle(lambda: durum(port)["kare_sayaci"] >= 1)
    ipl0 = threading.active_count()
    print("port", port, "iplik0", ipl0)

    senaryolar = []
    # 1) RST ile sert kopus (SO_LINGER 0)
    s = ham_baglan(port)
    n_parca_oku(s, 3)
    assert bekle(lambda: durum(port)["istemci_sayisi"] == 1, 2.0)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    t0 = time.monotonic()
    s.close()
    ok = bekle(lambda: durum(port)["istemci_sayisi"] == 0, 6.0)
    senaryolar.append(("RST kopus", ok, round(time.monotonic() - t0, 3)))

    # 2) Nazik kapanis (FIN)
    s = ham_baglan(port)
    n_parca_oku(s, 3)
    assert bekle(lambda: durum(port)["istemci_sayisi"] == 1, 2.0)
    t0 = time.monotonic()
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    ok = bekle(lambda: durum(port)["istemci_sayisi"] == 0, 6.0)
    senaryolar.append(("FIN kopus", ok, round(time.monotonic() - t0, 3)))

    # 3) Istemci OKUMAYI birakir ama kapatmaz (tampon dolar -> sunucu write bloklanir mi?)
    s = ham_baglan(port)
    n_parca_oku(s, 2)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    t0 = time.monotonic()
    time.sleep(4.0)      # hic okuma
    # bu sirada uretici ilerliyor mu ve baska istemci kare alabiliyor mu?
    d1 = durum(port)
    c = cv2.VideoCapture(kk.video_url(port))
    okunan = sum(1 for _ in range(5) if c.read()[0])
    c.release()
    d2 = durum(port)
    s.close()
    ok = bekle(lambda: durum(port)["istemci_sayisi"] == 0, 8.0)
    senaryolar.append(("okumayan istemci: uretici ilerledi=%s baska istemci %d/5 kare; kapatinca sayac 0=%s"
                       % (d2["kare_sayaci"] > d1["kare_sayaci"], okunan, ok), True, round(time.monotonic() - t0, 3)))

    # 4) 3 es zamanli istemci, ikisi kopar, ucuncu okumaya devam eder
    sl = [ham_baglan(port) for _ in range(3)]
    for x in sl:
        n_parca_oku(x, 2)
    assert bekle(lambda: durum(port)["istemci_sayisi"] == 3, 2.0)
    sl[0].close(); sl[1].close()
    ok = bekle(lambda: durum(port)["istemci_sayisi"] == 1, 6.0)
    n = n_parca_oku(sl[2], 5)
    sl[2].close()
    senaryolar.append(("3 istemci, 2 kopar, 3. %d bayt daha okudu" % n, ok, 0))

    # 5) cv2 istemcisi acilip release: sonra yeni cv2 istemcisi
    c = cv2.VideoCapture(kk.video_url(port)); assert c.isOpened()
    for _ in range(3): c.read()
    c.release()
    c2 = cv2.VideoCapture(kk.video_url(port)); assert c2.isOpened()
    okunan = sum(1 for _ in range(5) if c2.read()[0])
    c2.release()
    senaryolar.append(("cv2 ikinci istemci %d/5" % okunan, okunan == 5, 0))

    bekle(lambda: durum(port)["istemci_sayisi"] == 0, 6.0)
    time.sleep(0.3)
    print("\nsenaryolar (ad, basarili, sure_s):")
    for x in senaryolar:
        print("  ", x)
    print("uretici yasiyor:", uretici.is_alive(), "kaynak_acik:", durum(port)["kaynak_acik"],
          "kare_sayaci:", durum(port)["kare_sayaci"])
    print("iplik0=%d simdi=%d adlar=%s" % (ipl0, threading.active_count(),
                                          sorted(t.name for t in threading.enumerate())))
    print("KIRMIZI loglar:", [m for _, k, m in loglar if k])
    kk.kopru_kapat(sunucu, uretici)
    dizin.cleanup()


if __name__ == "__main__":
    main()
