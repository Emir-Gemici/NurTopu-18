"""
Navitas — Dron canli yayin izleyici (laptopta calisir)

RPi'nin actigi NAVITAS hotspot'una baglandiktan sonra calistir:
  - "NAVITAS HAM" penceresi : 720p H.264 dusuk gecikmeli ham kamera (ffplay)
  - "NAVITAS AI"  penceresi : model overlay + istatistik bandi (fps, uctan uca
                              gecikme, kayip %, RTT, RPi CPU°/cikarim suresi)

Kalp atisi: 2 sn'de bir RPi'ye HELLO gider → baglanti kopsa da RPi geri gelince
yayin otomatik surer; RTT ve saat farki surekli guncellenir (gecikme olcumu icin).

Kullanim:
  python3 drone/pc_izleyici.py                     # TEK pencere: AI overlay (buyutulebilir)
  python3 drone/pc_izleyici.py --rpi-ip 10.42.0.247
  python3 drone/pc_izleyici.py --ham               # AI'ya EK olarak ham kamerayi da goster
  python3 drone/pc_izleyici.py --kayit ucus1.mp4   # AI yayinini mp4 kaydet
  python3 drone/pc_izleyici.py --headless          # pencere yok, konsol istatistik

Cikis: AI penceresinde 'q' ya da Ctrl-C.
"""

import argparse
import json
import os
import select
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import (AI_BASLIK, AI_PORT, HB_ARALIK, HELLO_PORT, RAW_PORT,  # noqa: E402
                   TLM_PORT, ack_coz, hello_yap, log_kur, udp_soket)

KAYIT_FPS = 5  # AI akisi degisken hizli; kayit sabit fps ister (yaklasik)


class Baglanti:
    """Kalp atisi + RTT / saat-ofseti takibi (arka plan is parcacigi)."""

    def __init__(self, rpi_ip, log, dur):
        self._ip, self._log, self._dur = rpi_ip, log, dur
        self.rtt = None            # sn
        self.ofset = None          # rpi_saati + ofset ≈ bizim saat (EMA)
        self.bagli = threading.Event()
        self._sock = udp_soket()
        self._sock.settimeout(1.0)

    def bekle(self, sure=None):
        """Ilk basarili el sikismaya kadar bekler."""
        return self.bagli.wait(timeout=sure)

    def dongu(self):
        kayip_ust_uste = 0
        while not self._dur.is_set():
            try:
                self._sock.sendto(hello_yap(), (self._ip, HELLO_PORT))
                sonuc = ack_coz(self._sock.recv(256))
            except socket.timeout:
                sonuc = None
            except OSError as e:
                self._log.warning("ag hatasi: %s", e)
                sonuc = None
            if sonuc:
                rtt, ofset = sonuc
                self.rtt = rtt
                # saat ofsetini yumusat (tek olcum RTT gurultusune acik)
                self.ofset = ofset if self.ofset is None else 0.8 * self.ofset + 0.2 * ofset
                if not self.bagli.is_set():
                    self._log.info("RPi bulundu (%s) — rtt=%.0f ms", self._ip, rtt * 1000)
                    self.bagli.set()
                kayip_ust_uste = 0
            else:
                kayip_ust_uste += 1
                if self.bagli.is_set() and kayip_ust_uste == 3:
                    self._log.warning("RPi cevap vermiyor (3 kalp atisi kacti) — bekleniyor...")
                    self.bagli.clear()
                elif not self.bagli.is_set() and kayip_ust_uste % 5 == 1:
                    self._log.info("RPi araniyor: %s (hotspot'a bagli miyiz?)", self._ip)
            self._dur.wait(HB_ARALIK)


class Telemetri:
    """RPi telemetri paketlerini toplar; en son durumu saklar."""

    def __init__(self, log, dur):
        self._log, self._dur = log, dur
        self.son = {}
        self.son_zaman = 0.0

    def dongu(self):
        sock = udp_soket(alici_port=TLM_PORT)
        sock.settimeout(0.5)
        while not self._dur.is_set():
            try:
                data, _ = sock.recvfrom(2048)
            except socket.timeout:
                continue
            try:
                self.son = json.loads(data.decode())
                self.son_zaman = time.time()
                self._log.debug("tlm: %s", self.son)
            except (ValueError, UnicodeDecodeError):
                self._log.debug("bozuk telemetri paketi (%d B)", len(data))
        sock.close()


class AiAlici:
    """Parcalanmis JPEG karelerini birlestirir; kayip/gecikme istatistigi tutar.

    Birden fazla kare ayni anda 'ucusta' olabilir (UDP siralama garantisi yok);
    eski karenin gec gelen parcasi yeni kareyi silmez — kare_no bazli tampon,
    2 sn'den eski girdiler atilir."""

    ESKI_SN = 2.0

    def __init__(self, log):
        self._log = log
        self._tampon = {}          # kare_no → {"t":ilk_gelis, "cekim":ts, "parcalar":{}, "toplam":n}
        self.alinan = 0            # tamamlanan kare
        self.dusen = 0             # kare_no boslugundan tahmini kayip
        self.bayt = 0
        self._son_kare_no = None

    def paket(self, data):
        """Bir UDP paketi isler; kare tamamlandiysa (bgr, cekim_zamani) doner."""
        if len(data) < AI_BASLIK.size:
            return None
        kare_no, cekim, idx, toplam = AI_BASLIK.unpack(data[:AI_BASLIK.size])
        g = self._tampon.setdefault(kare_no, {"t": time.time(), "cekim": cekim,
                                              "parcalar": {}, "toplam": toplam})
        g["parcalar"][idx] = data[AI_BASLIK.size:]
        self.bayt += len(data)
        # eski yarim kareleri temizle
        simdi = time.time()
        for k in [k for k, v in self._tampon.items() if simdi - v["t"] > self.ESKI_SN]:
            self._log.debug("yarim kare atildi: %d (%d/%d parca)",
                            k, len(self._tampon[k]["parcalar"]), self._tampon[k]["toplam"])
            del self._tampon[k]
        if len(g["parcalar"]) < g["toplam"]:
            return None
        jpg = b"".join(g["parcalar"][i] for i in range(g["toplam"]))
        del self._tampon[kare_no]
        kare = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
        if kare is None:
            self._log.warning("JPEG cozulemedi (kare %d, %d B)", kare_no, len(jpg))
            return None
        self.alinan += 1
        if self._son_kare_no is not None:
            bosluk = (kare_no - self._son_kare_no) % 2**32
            if 1 < bosluk < 1000:
                self.dusen += bosluk - 1
        self._son_kare_no = kare_no
        return kare, cekim

    def kayip_orani(self):
        toplam = self.alinan + self.dusen
        return self.dusen / toplam if toplam else 0.0


def ffplay_baslat(log):
    if shutil.which("ffplay") is None:
        log.warning("ffplay yok (kur: ffmpeg paketi) → ham pencere acilmayacak")
        return None
    log.info("ham izleyici: ffplay udp://@:%d", RAW_PORT)
    return subprocess.Popen(
        ["ffplay", "-fflags", "nobuffer", "-flags", "low_delay",
         "-probesize", "100000", "-analyzeduration", "500000",
         "-window_title", "NAVITAS HAM", "-loglevel", "warning",
         f"udp://@:{RAW_PORT}?buffer_size=1048576"],
    )


def panel_bas(kare, satirlar):
    """Kare altina yari saydam istatistik bandi."""
    h, w = kare.shape[:2]
    bant_h = 16 * len(satirlar) + 8
    kare[h - bant_h:h] = (kare[h - bant_h:h] * 0.35).astype(kare.dtype)
    for i, s in enumerate(satirlar):
        cv2.putText(kare, s, (8, h - bant_h + 16 * (i + 1)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    return kare


def main():
    ap = argparse.ArgumentParser(description="Navitas dron yayin izleyici")
    ap.add_argument("--rpi-ip", default="10.42.1.1",
                    help="RPi adresi (NAVITAS hotspot'unda RPi 10.42.1.1; "
                         "ethernet paylasiminda 10.42.0.x)")
    ap.add_argument("--ham", action="store_true",
                    help="AYRICA ham (overlaysiz) kamerayi da ayri pencerede goster (ffplay)")
    ap.add_argument("--kayit", metavar="DOSYA.mp4", help="AI yayinini mp4 olarak kaydet")
    ap.add_argument("--headless", action="store_true",
                    help="pencere acma, konsola istatistik yaz")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--log-file", help="loglari dosyaya da yaz")
    args = ap.parse_args()

    log = log_kur("pc_izleyici", args.debug, args.log_file)
    headless = args.headless or not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if headless and not args.headless:
        log.warning("goruntu ortami yok (DISPLAY/WAYLAND yok) → headless mod")

    dur = threading.Event()
    baglanti = Baglanti(args.rpi_ip, log, dur)
    telemetri = Telemetri(log, dur)

    # once alici portlari ac (ilk kareler kacmasin), sonra kalp atisi basla
    ai_sock = udp_soket(alici_port=AI_PORT)
    ai_sock.setblocking(False)   # drain icin sart: timeout'lu sokette DONTWAIT islemez
    alici = AiAlici(log)
    # VARSAYILAN: TEK pencere (AI overlay + sonuclar). Ham (overlaysiz) pencere sadece
    # --ham verilince acilir. AI penceresi YENIDEN BOYUTLANDIRILABILIR (WINDOW_NORMAL).
    ffproc = ffplay_baslat(log) if (args.ham and not headless) else None
    if not headless:
        cv2.namedWindow("NAVITAS AI", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("NAVITAS AI", 1280, 720)   # baslangic buyuk boyut (elle degistirilebilir)

    threading.Thread(target=baglanti.dongu, daemon=True).start()
    threading.Thread(target=telemetri.dongu, daemon=True).start()

    yazici = None
    if args.kayit:
        yazici = cv2.VideoWriter(args.kayit, cv2.VideoWriter_fourcc(*"mp4v"),
                                 KAYIT_FPS, (640, 360))
        log.info("kayit: %s (~%d fps)", args.kayit, KAYIT_FPS)

    fps, gecikme_ms = 0.0, None
    t_fps, n_fps = time.time(), 0
    t_rapor = time.time()
    atlanan, yazilan = 0, 0
    try:
        while not dur.is_set():
            # biriken TUM paketleri isle, EN YENI tam kareyi goster → tampon
            # doldugunda eski kareleri sirayla oynatmak yerine canliya atla
            sonuc = None
            try:
                while True:
                    s = alici.paket(ai_sock.recv(AI_BASLIK.size + 1500))
                    if s is not None:
                        if sonuc is not None:
                            atlanan += 1
                        sonuc = s
            except BlockingIOError:
                pass
            if sonuc is None:
                select.select([ai_sock], [], [], 0.05)   # paket gelene dek bekle (CPU yakma)
            if sonuc is not None:
                kare, cekim = sonuc
                n_fps += 1
                if time.time() - t_fps >= 2:
                    fps = n_fps / (time.time() - t_fps)
                    t_fps, n_fps = time.time(), 0
                if baglanti.ofset is not None:
                    gecikme_ms = (time.time() - (cekim + baglanti.ofset)) * 1000
                tlm = telemetri.son
                satirlar = [
                    f"izleyici: {fps:.1f} fps  gecikme={gecikme_ms:.0f} ms  kayip={alici.kayip_orani()*100:.1f}%"
                    if gecikme_ms is not None else f"izleyici: {fps:.1f} fps",
                    (f"rpi: {tlm.get('ai_fps', '?')} fps  cikarim={tlm.get('cikarim_ms', 0):.0f} ms  "
                     f"cpu={tlm.get('cpu_c') or '?'}C  karar={tlm.get('karar', '-')}"
                     f"  rtt={baglanti.rtt * 1000:.0f} ms" if tlm and baglanti.rtt else
                     "rpi telemetri bekleniyor..."),
                ]
                kare = panel_bas(kare, satirlar)
                if yazici is not None:
                    yazici.write(kare)
                    yazilan += 1
                if not headless:
                    cv2.imshow("NAVITAS AI", kare)

            if headless:
                if time.time() - t_rapor >= 2 and alici.alinan:
                    log.info("ai: %.1f fps  gecikme=%s  kayip=%.1f%%  toplam=%d kare  %s",
                             fps, f"{gecikme_ms:.0f} ms" if gecikme_ms is not None else "?",
                             alici.kayip_orani() * 100, alici.alinan,
                             f"tlm={telemetri.son.get('karar', '-')}" if telemetri.son else "")
                    t_rapor = time.time()
            else:
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                if ffproc is not None and ffproc.poll() is not None:
                    log.warning("ffplay kapandi (kod %s) — yeniden baslatiliyor", ffproc.returncode)
                    ffproc = ffplay_baslat(log)
    except KeyboardInterrupt:
        pass
    finally:
        dur.set()
        if yazici is not None:
            yazici.release()
            log.info("kayit kapatildi: %s (%d kare)", args.kayit, yazilan)
        if ffproc is not None:
            ffproc.terminate()
        cv2.destroyAllWindows()
        log.info("ozet: %d kare alindi (%d canlilik icin atlandi), ~%d kayip (%.1f%%), %.1f MB",
                 alici.alinan, atlanan, alici.dusen, alici.kayip_orani() * 100,
                 alici.bayt / 1e6)
    return 0


if __name__ == "__main__":
    sys.exit(main())
