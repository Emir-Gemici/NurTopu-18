"""R2: hub uzerinden UDP->seri ve seri->UDP gecikmesi, 0,20 s aralikli
PARACHUTE tekrarlari, 50 ornek; p50/p95/max. Kosullar:
  A  UDP->seri, seri girisi bos
  B  UDP->seri, seri girisinde 20 Hz heartbeat akisi (mesgul hat)
  C  seri->UDP (YKS CMD -> tuketici)
  D  hub'siz dogrudan kopru (yazan->okuyan) taban cizgisi"""
import contextlib
import io
import socket
import sys
import threading
import time

from ortak import YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(None)
from link import SerialLink, UDPLink  # noqa: E402
from protocol import FrameReader, command, encode, heartbeat  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402

N = 50
ARALIK_S = 0.20
UC_ZA = 0.02


def uc(kopru, timeout=UC_ZA):
    return SerialLink(f"socket://{YEREL}:{kopru.port}", 57600, timeout=timeout)


def yuzdelik(v, p):
    s = sorted(v)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))]


def ozet(ad, gecikmeler, eksik):
    if not gecikmeler:
        print(f"{ad}: HIC ORNEK YOK (eksik={eksik})")
        return
    ms = [g * 1000.0 for g in gecikmeler]
    print(f"{ad}: n={len(ms)} eksik={eksik} p50={yuzdelik(ms, 50):.2f} ms "
          f"p95={yuzdelik(ms, 95):.2f} ms max={max(ms):.2f} ms min={min(ms):.2f} ms")


class SeriOkuyucu(threading.Thread):
    """Seri uctan cerceve okur; kosula uyan cercevelerin varis anini kaydeder."""

    def __init__(self, link, kosul):
        super().__init__(daemon=True)
        self.link, self.kosul = link, kosul
        self.varis = {}
        self.dur = threading.Event()

    def run(self):
        r = FrameReader()
        while not self.dur.is_set():
            veri, _ = self.link.recv()
            if not veri:
                continue
            simdi = time.perf_counter()
            for m in r.feed(veri):
                if self.kosul(m):
                    self.varis[m["seq"]] = simdi


class UdpOkuyucu(threading.Thread):
    def __init__(self, link, kosul):
        super().__init__(daemon=True)
        self.link, self.kosul = link, kosul
        self.varis = {}
        self.dur = threading.Event()

    def run(self):
        while not self.dur.is_set():
            veri, _ = self.link.recv()
            if not veri:
                continue
            simdi = time.perf_counter()
            for m in FrameReader().feed(veri):
                if self.kosul(m):
                    self.varis[m["seq"]] = simdi


def bekle(varis, seqler, tavan_s=3.0):
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis and not all(s in varis for s in seqler):
        time.sleep(0.01)


def kosul_cmd(m):
    return m.get("type") == "CMD" and m.get("cmd") == "PARACHUTE"


def olc_udp_seri(hub_adr, yks, mesgul=None, etiket="A"):
    okuyucu = SeriOkuyucu(yks, kosul_cmd)
    okuyucu.start()
    gonderen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gonder = {}
    taban = 1000 if etiket == "A" else 2000
    for i in range(N):
        seq = taban + i
        ham = encode(command("PARACHUTE", "iha", seq=seq))
        gonder[seq] = time.perf_counter()
        gonderen.sendto(ham, hub_adr)
        time.sleep(ARALIK_S)
    bekle(okuyucu.varis, gonder)
    okuyucu.dur.set()
    okuyucu.join(timeout=1.0)
    gonderen.close()
    gec = [okuyucu.varis[s] - gonder[s] for s in gonder if s in okuyucu.varis]
    eksik = [s for s in gonder if s not in okuyucu.varis]
    return gec, eksik


def main():
    kopru = SikKoprusu()
    hub_seri = uc(kopru, modul.SERI_OKUMA_ZAMAN_ASIMI_S)
    yks = uc(kopru)
    udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
    tuketici = UDPLink(bind=(YEREL, 0), timeout=0.02)
    log = io.StringIO()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        hub = modul.SeriHub(hub_seri, udp, [(YEREL, tuketici.port)], log_aralik_s=0)
    hub_adr = (YEREL, udp.port)

    hub._logla = lambda *a, **k: None   # surec geneli redirect yerine sustur

    def hub_kos():
        hub.calistir()

    hub_thr = threading.Thread(target=hub_kos, daemon=True)
    hub_thr.start()
    time.sleep(0.2)

    # A: UDP -> seri, seri girisi bos
    gec, eksik = olc_udp_seri(hub_adr, yks, etiket="A")
    ozet("A UDP->seri (seri girisi bos)", gec, eksik)

    # B: UDP -> seri, seri girisinde 20 Hz heartbeat (YKS -> hub yonu mesgul)
    dur_hb = threading.Event()

    def hb_akisi():
        i = 0
        while not dur_hb.is_set():
            i += 1
            yks.send(encode(heartbeat("yks", seq=i, x=1.0, y=2.0, alt=30.0)))
            time.sleep(0.05)

    hb_thr = threading.Thread(target=hb_akisi, daemon=True)
    hb_thr.start()
    gec, eksik = olc_udp_seri(hub_adr, yks, etiket="B")
    dur_hb.set()
    hb_thr.join(timeout=1.0)
    ozet("B UDP->seri (seri girisinde 20 Hz HB)", gec, eksik)

    # C: seri -> UDP (YKS CMD -> statik tuketici)
    okuyucu = UdpOkuyucu(tuketici, kosul_cmd)
    okuyucu.start()
    gonder = {}
    for i in range(N):
        seq = 3000 + i
        ham = encode(command("PARACHUTE", "iha", seq=seq))
        gonder[seq] = time.perf_counter()
        yks.send(ham)
        time.sleep(ARALIK_S)
    bekle(okuyucu.varis, gonder)
    okuyucu.dur.set()
    okuyucu.join(timeout=1.0)
    gec = [okuyucu.varis[s] - gonder[s] for s in gonder if s in okuyucu.varis]
    eksik = [s for s in gonder if s not in okuyucu.varis]
    ozet("C seri->UDP (YKS CMD -> tuketici)", gec, eksik)

    hub.durdur()
    hub_thr.join(timeout=2.0)
    hub.kapat()
    tuketici.close()
    yks.close()
    kopru.kapat()
    print("hub sayac:", hub.sayac)

    # D: hub'siz dogrudan kopru taban cizgisi
    kopru2 = SikKoprusu()
    a = uc(kopru2)
    b = uc(kopru2)
    okuyucu = SeriOkuyucu(b, kosul_cmd)
    okuyucu.start()
    gonder = {}
    for i in range(N):
        seq = 4000 + i
        ham = encode(command("PARACHUTE", "iha", seq=seq))
        gonder[seq] = time.perf_counter()
        a.send(ham)
        time.sleep(ARALIK_S)
    bekle(okuyucu.varis, gonder)
    okuyucu.dur.set()
    okuyucu.join(timeout=1.0)
    gec = [okuyucu.varis[s] - gonder[s] for s in gonder if s in okuyucu.varis]
    eksik = [s for s in gonder if s not in okuyucu.varis]
    ozet("D hub'siz kopru (taban)", gec, eksik)
    a.close()
    b.close()
    kopru2.kapat()


if __name__ == "__main__":
    main()
