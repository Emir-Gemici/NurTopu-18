"""
Navitas — Dron RPi5 canli yayin (RPi tarafinda calisir)

RPi5 + CSI kamera goruntusunu RPi'nin actigi WiFi hotspot uzerinden (internet YOK)
laptopa aktarir:

  - HAM yayin   : 1280x720 H.264 (MPEG-TS)          → UDP <izleyici>:5600
  - AI yayin    : 640x360 model overlay (acik yol)   → UDP <izleyici>:5601
  - TELEMETRI   : JSON durum (fps, cikarim ms, CPU°) → UDP <izleyici>:5602  (2 sn'de bir)

Izleyici IP'si elle girilmez: pc_izleyici.py 5599'a kalp atisi (HELLO) atar; yayin
o adrese akar. Kalp atisi HEDEF_ZAMANASIMI (8 sn) kesilirse yayin durdurulur
(bosa bant/CPU harcanmaz), izleyici geri gelince kaldigi yerden surer.

Kullanim (RPi'de):
  python3 drone/rpi_yayin.py                       # kamera + model
  python3 drone/rpi_yayin.py --no-ai               # sadece ham yayin
  python3 drone/rpi_yayin.py --debug --log-file /tmp/navitas_yayin.log

Yerel test (kamerasiz, herhangi bir makinede):
  python3 drone/rpi_yayin.py --sim test_images/ai   # klasor/video/gorsel kaynak

Gereksinim: RPi OS Bookworm, python3-picamera2, ffmpeg, ultralytics (README_KURULUM.md)
"""

import argparse
import shutil
import signal
import socket
import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

_kok = Path(__file__).resolve().parent
sys.path.insert(0, str(_kok))
sys.path.insert(0, str(_kok.parent / "codes"))
sys.path.insert(0, str(_kok.parent / "simulation" / "scripts"))

import cv2  # noqa: E402

from ortak import (AI_PORT, HEDEF_ZAMANASIMI, HELLO_PORT, RAW_PORT, TLM_PORT,  # noqa: E402
                   ack_yap, hello_coz, jpeg_gonder, log_kur, udp_soket)

MAIN_SIZE = (1280, 720)          # ham H.264
LORES_SIZE = (640, 360)          # model girisi + AI overlay
LANE_NAMES = {1: "SOL", 2: "ORTA", 3: "SAG"}
SIM_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SIM_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


class Hedef:
    """Izleyici adresi + son kalp atisi. Kalp atisi kesilince yayin durur."""

    def __init__(self, log):
        self._ip = None
        self._son_hb = 0.0
        self._lock = threading.Lock()
        self.degisti = threading.Event()   # ana donguyu uyandirir (ip degisti / dustu)
        self._log = log

    def kalp_atisi(self, ip):
        with self._lock:
            self._son_hb = time.time()
            if ip != self._ip:
                self._log.info("izleyici %s → %s", self._ip or "-", ip)
                self._ip = ip
                self.degisti.set()

    def aktif_ip(self):
        """Canli (zaman asimina ugramamis) izleyici IP'si, yoksa None."""
        with self._lock:
            if self._ip and time.time() - self._son_hb <= HEDEF_ZAMANASIMI:
                return self._ip
            return None

    def dusur(self):
        with self._lock:
            if self._ip is not None:
                self._log.warning("izleyici %s kalp atisi kesildi (> %.0f sn) — yayin durduruluyor",
                                  self._ip, HEDEF_ZAMANASIMI)
                self._ip = None
                self.degisti.set()


def hello_dinle(hedef, log, dur: threading.Event):
    sock = udp_soket(alici_port=HELLO_PORT)
    sock.settimeout(0.5)
    log.info("hello dinleniyor: udp %d", HELLO_PORT)
    while not dur.is_set():
        try:
            data, addr = sock.recvfrom(256)
            t_izleyici = hello_coz(data)
            if t_izleyici is False:
                log.debug("taninmayan paket: %s → %r", addr, data[:32])
                continue
            sock.sendto(ack_yap(t_izleyici), addr)
            hedef.kalp_atisi(addr[0])
        except socket.timeout:
            continue
        except OSError as e:   # GUCLENDIRME: gecici ag hatasi dinleyiciyi oldurmesin
            log.debug("hello soket hatasi (devam): %s", e)
            time.sleep(0.2)
    sock.close()


# ---------------------------------------------------------------- kamera katmani

RAW_FPS = 10   # ham yayin kare/sn (yazilim H.264 → CPU'yu AI ile paylasir)


def _ffmpeg_raw_proc(ip, bitrate):
    """main-boyut BGR kareleri stdin'den alip libx264 (zerolatency) ile
    MPEG-TS/UDP olarak yollayan ffmpeg sureci. RPi5'te donanim H.264 encoder
    YOK → yazilim kodlama; picamera2'nin libav encoder'i Ubuntu 26.04'te PyAV
    uyumsuzlugundan bozuk oldugu icin ham yayin bu ortak yoldan gecer."""
    w, h = MAIN_SIZE
    return subprocess.Popen(
        ["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
         "-r", str(RAW_FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
         "-pix_fmt", "yuv420p", "-g", str(RAW_FPS), "-b:v", str(bitrate),
         "-f", "mpegts", f"udp://{ip}:{RAW_PORT}?pkt_size=1316"],
        stdin=subprocess.PIPE,
    )


class HamPompaKarisim:
    """Ham yayin ortak mantigi: _ham_kare() (main-boyut BGR) ureten alt siniflar
    icin ffmpeg pompasini ac/kapa. PiKamera + SimKamera paylasir."""

    def _pompa_kur(self):
        self._proc = None
        self._pompa_dur = threading.Event()
        self._pompa = None

    def ham_baslat(self, ip):
        self.ham_durdur()
        if shutil.which("ffmpeg") is None:
            self._log.warning("ffmpeg yok → ham yayin atlandi")
            return
        self._proc = _ffmpeg_raw_proc(ip, self._bitrate)
        self._pompa_dur.clear()
        self._pompa = threading.Thread(target=self._pompala, daemon=True)
        self._pompa.start()
        self._log.info("ham H.264 basladi → udp://%s:%d (%.1f Mbps)",
                       ip, RAW_PORT, self._bitrate / 1e6)

    def _pompala(self):
        aralik = 1.0 / RAW_FPS
        while not self._pompa_dur.is_set() and self._proc.poll() is None:
            t = time.time()
            kare = self._ham_kare()
            try:
                self._proc.stdin.write(kare.tobytes())
            except (BrokenPipeError, ValueError):
                break
            bekle = aralik - (time.time() - t)
            if bekle > 0:
                time.sleep(bekle)

    def ham_durdur(self):
        self._pompa_dur.set()
        if self._proc is not None:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()
            self._proc = None
            self._log.info("ham yayin durdu")


class PiKamera(HamPompaKarisim):
    """Gercek donanim: Picamera2 cift akis — main (ham yayin) + lores (AI)."""

    def __init__(self, log, bitrate, dondur=0):
        from libcamera import Transform
        from picamera2 import Picamera2
        self._log = log
        self._bitrate = bitrate
        self._pompa_kur()
        self.picam = Picamera2()
        # dondur=180: bant/yapistirma montajinda kamera ters durabilir —
        # ISP seviyesinde cevrilir, HER IKI akisa (ham + AI) birden uygulanir.
        # main de RGB888 → capture_array dogrudan islenebilir kare verir.
        cfg = self.picam.create_video_configuration(
            main={"size": MAIN_SIZE, "format": "RGB888"},
            lores={"size": LORES_SIZE, "format": "RGB888"},
            transform=Transform(hflip=(dondur == 180), vflip=(dondur == 180)),
        )
        self.picam.configure(cfg)
        self.picam.start()
        log.info("kamera acildi: main=%s lores=%s dondur=%d°", MAIN_SIZE, LORES_SIZE, dondur)

    # NOT: picamera2'de "RGB888" formati aslinda BGR sirali dizi verir (libcamera
    # adlandirma tuhafligi). OpenCV/ffmpeg zaten BGR bekledigi icin diziyi DOGRUDAN
    # kullaniyoruz — cvtColor(RGB2BGR) EKSTRA takas yapip renkleri ters ceviriyordu
    # (kirmizi↔mavi → mavimsi goruntu).
    def kare_al(self):
        return self.picam.capture_array("lores")

    def _ham_kare(self):
        return self.picam.capture_array("main")

    def kapat(self):
        self.ham_durdur()
        self.picam.stop()


class SimKamera(HamPompaKarisim):
    """Kamerasiz test: klasor/video/gorselden kare uretir; ham yayini gercek
    kamerayla AYNI ffmpeg yolundan yollar → izleyici tarafi birebir ayni kodla
    test edilir."""

    def __init__(self, log, bitrate, kaynak, dondur=0):
        self._log, self._bitrate = log, bitrate
        self._dondur = dondur
        self._kareler = self._yukle(Path(kaynak))
        self._pompa_kur()
        log.info("SIM kaynak: %s (%d kare) — GERCEK KAMERA DEGIL", kaynak, len(self._kareler))

    def _yukle(self, p):
        kareler = []
        if p.is_dir():
            dosyalar = sorted(x for x in p.iterdir() if x.suffix.lower() in SIM_EXT)
        elif p.suffix.lower() in SIM_VIDEO_EXT:
            cap = cv2.VideoCapture(str(p))
            while len(kareler) < 300:
                ok, kare = cap.read()
                if not ok:
                    break
                kareler.append(cv2.resize(kare, LORES_SIZE))
            cap.release()
            dosyalar = []
        else:
            dosyalar = [p]
        for d in dosyalar:
            img = cv2.imread(str(d))
            if img is not None:
                kareler.append(cv2.resize(img, LORES_SIZE))
        if not kareler:
            raise SystemExit(f"HATA: sim kaynaginda kare yok: {p}")
        return kareler

    def kare_al(self):
        # saniyede bir kaynak kare degisir + zaman damgasi basilir (kareler ayirt edilebilsin)
        kare = self._kareler[int(time.time()) % len(self._kareler)].copy()
        if self._dondur == 180:
            kare = cv2.rotate(kare, cv2.ROTATE_180)
        cv2.putText(kare, f"SIM {time.strftime('%H:%M:%S')}", (8, LORES_SIZE[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return kare

    def _ham_kare(self):
        return cv2.resize(self.kare_al(), MAIN_SIZE)

    def kapat(self):
        self.ham_durdur()


# ---------------------------------------------------------------- AI + telemetri

class Durum:
    """AI dongusu ile telemetri arasinda paylasilan son durum."""

    def __init__(self):
        self.lock = threading.Lock()
        self.d = {"kare_no": 0, "ai_fps": 0.0, "cikarim_ms": 0.0,
                  "karar": "-", "guven": 0.0, "gonderim_parca": 0}

    def guncelle(self, **kv):
        with self.lock:
            self.d.update(kv)

    def kopya(self):
        with self.lock:
            return dict(self.d)


def cpu_sicaklik():
    try:
        return int(Path("/sys/class/thermal/thermal_zone0/temp").read_text()) / 1000.0
    except (OSError, ValueError):
        return None


KAYIT_FPS = 5   # kayit videosu icin nominal fps (AI degisken hizli, sabit fps ile yaz)


class Kayit:
    """AI overlay'ini RPi'de YERELDE kaydeder. Her izleyici oturumu = bir kayit.
    Duzen:  <base>/YYYY-MM-DD/<HHMMSS>_<id>_video.mp4
                              <HHMMSS>_<id>_meta.json   (ozet: baslangic/bitis/kare/karar)
                              <HHMMSS>_<id>.log          (oturum log'u)
    id = o gun icindeki sira no (01, 02, ...). Ayni tarih → ayni gun klasoru."""

    def __init__(self, base_dir, log):
        self.base = Path(base_dir)
        self._log = log
        self.writer = None
        self.log_handler = None
        self._sifirla()

    def _sifirla(self):
        self.writer = None
        self.meta_yol = None
        self.baslangic = None
        self.kare_sayi = 0
        self.kararlar = {}

    def aktif(self):
        return self.writer is not None

    def baslat(self):
        import logging
        now = datetime.now()
        gun = self.base / now.strftime("%Y-%m-%d")
        gun.mkdir(parents=True, exist_ok=True)
        idn = len(list(gun.glob("*_video.mp4"))) + 1        # o gun kacinci oturum
        onek = f"{now.strftime('%H%M%S')}_{idn:02d}"        # SAAT(saniye)_ID
        video_yol = gun / f"{onek}_video.mp4"
        self.meta_yol = gun / f"{onek}_meta.json"
        self.writer = cv2.VideoWriter(str(video_yol),
                                      cv2.VideoWriter_fourcc(*"mp4v"),
                                      KAYIT_FPS, LORES_SIZE)
        # oturum log'u: ana log'a ek olarak bu oturumu ayri dosyaya da yaz
        self.log_handler = logging.FileHandler(gun / f"{onek}.log")
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s.%(msecs)03d %(levelname).1s %(message)s",
                              datefmt="%H:%M:%S"))
        self._log.addHandler(self.log_handler)
        self.baslangic = now
        self.kare_sayi = 0
        self.kararlar = {}
        self._log.info("KAYIT basladi → %s", video_yol)

    def kare_yaz(self, vis, karar):
        if self.writer is None:
            return
        self.writer.write(vis)
        self.kare_sayi += 1
        self.kararlar[karar] = self.kararlar.get(karar, 0) + 1

    def kapat(self):
        if self.writer is None:
            return
        self.writer.release()
        bitis = datetime.now()
        sure = (bitis - self.baslangic).total_seconds()
        meta = {
            "baslangic": self.baslangic.isoformat(timespec="seconds"),
            "bitis": bitis.isoformat(timespec="seconds"),
            "sure_sn": round(sure, 1),
            "kare_sayisi": self.kare_sayi,
            "ortalama_fps": round(self.kare_sayi / sure, 2) if sure > 0 else 0,
            "karar_dagilimi": self.kararlar,
            "cozunurluk": f"{LORES_SIZE[0]}x{LORES_SIZE[1]}",
            "cpu_c": cpu_sicaklik(),
        }
        try:
            self.meta_yol.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        except OSError as e:
            self._log.warning("meta yazilamadi: %s", e)
        self._log.info("KAYIT kapandi: %d kare, %.1f sn", self.kare_sayi, sure)
        if self.log_handler is not None:
            self._log.removeHandler(self.log_handler)
            self.log_handler.close()
        self._sifirla()


def _ai_bir_kare(kamera, model, _infer, draw_masks, conf, imgsz, kalite):
    """Tek AI karesi uret → (jpg_bytes, cekim_zamani, karar, guven, cikarim_ms, n_parca_yok).
    Ayri fonksiyon: ai_dongusu bunu try/except ile sarar, hata tek kareyi atlar."""
    bgr = kamera.kare_al()
    cekim = time.time()
    t1 = time.time()
    content, masks, open_path, guven, wps = _infer(bgr, model, conf, imgsz)
    cikarim_ms = (time.time() - t1) * 1000

    vis = draw_masks(content, masks)
    for x, y in wps:
        cv2.circle(vis, (int(x), int(y)), 4, (0, 255, 255), -1)
    karar = LANE_NAMES.get(open_path, "YOK")
    cv2.putText(vis, f"ACIK YOL: {karar}  guven={guven:.2f}", (8, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    if vis.shape[:2] != (LORES_SIZE[1], LORES_SIZE[0]):
        vis = cv2.resize(vis, LORES_SIZE)   # izleyici/kayit sabit boyut bekler
    ok, jpg = cv2.imencode(".jpg", vis, [cv2.IMWRITE_JPEG_QUALITY, kalite])
    if not ok:
        raise RuntimeError("JPEG kodlama basarisiz")
    return jpg.tobytes(), vis, cekim, karar, round(float(guven), 3), cikarim_ms


def ai_dongusu(kamera, hedef, durum, log, dur, conf, imgsz, ai_fps_siniri, ai_kalite,
               kayit=None):
    # _infer = kanitlanmis algi hatti: letterbox (en-boy korunur, serit kaybolmaz)
    # + conf fallback (0.05) + karanlikta isik-normalize cift kosu (iha_perceive)
    from iha_perceive import _infer
    from rpi_inference import draw_masks, load_model

    t0 = time.time()
    model = load_model()
    # ilk cikarim yavas olur (agirlik yukleme) — sayimlari bozmasin diye isinma:
    _infer(np.zeros((LORES_SIZE[1], LORES_SIZE[0], 3), np.uint8), model, conf, imgsz)
    log.info("model hazir (%.1f sn) — conf=%.2f imgsz=%d jpeg_kalite=%d",
             time.time() - t0, conf, imgsz, ai_kalite)

    sock = udp_soket()
    kare_no = 0
    sayac, sure_cikarim, byte_top, t_rapor = 0, 0.0, 0, time.time()
    son_karar = "-"
    hata_sayac, son_hata_log = 0, 0.0
    while not dur.is_set():
        ip = hedef.aktif_ip()
        if ip is None:
            if kayit is not None and kayit.aktif():
                kayit.kapat()             # oturum bitti → kaydi kapat + meta yaz
            time.sleep(0.2)
            continue
        if kayit is not None and not kayit.aktif():
            kayit.baslat()                # yeni izleyici oturumu → yeni kayit
        t_dongu = time.time()

        # GUCLENDIRME: tek kare hatasi (kamera/cikarim/kodlama) thread'i OLDURMESIN —
        # logla, kisa bekle, devam et. (picamera2 encoder cokmesi gibi durumlar sessizce
        # tum yayini dusurmesin diye.)
        try:
            jpg, vis, cekim, karar, guven, cikarim_ms = _ai_bir_kare(
                kamera, model, _infer, draw_masks, conf, imgsz, ai_kalite)
        except Exception as e:
            hata_sayac += 1
            if time.time() - son_hata_log >= 5:
                log.error("ai kare hatasi (%d kez): %s", hata_sayac, e)
                son_hata_log = time.time()
            time.sleep(0.1)
            continue

        # WIFI KAYBI AZALTMA: kucuk JPEG → az UDP parcasi → bir parca kaybinda daha az
        # kare duser. jpeg_gonder parca sayisini doner; buyukse ai_kalite dusurulmeli.
        n_parca = jpeg_gonder(sock, ip, AI_PORT, kare_no, cekim, jpg)
        durum.guncelle(kare_no=kare_no, cikarim_ms=cikarim_ms, karar=karar,
                       guven=guven, gonderim_parca=n_parca)
        kare_no = (kare_no + 1) % 2**32
        son_karar = karar
        if kayit is not None:
            kayit.kare_yaz(vis, karar)    # AI overlay'ini RPi'ye kaydet

        sayac += 1
        sure_cikarim += cikarim_ms
        byte_top += len(jpg)
        gecen = time.time() - t_rapor
        if gecen >= 5:
            fps = sayac / gecen
            durum.guncelle(ai_fps=round(fps, 2))
            log.info("ai: %.1f fps  cikarim=%.0f ms  kare~%.0fKB/%d parca  karar=%s",
                     fps, sure_cikarim / sayac, byte_top / sayac / 1024,
                     -(-int(byte_top / sayac) // 1400), son_karar)
            sayac, sure_cikarim, byte_top, t_rapor = 0, 0.0, 0, time.time()

        if ai_fps_siniri > 0:
            bekle = 1.0 / ai_fps_siniri - (time.time() - t_dongu)
            if bekle > 0:
                time.sleep(bekle)


def telemetri_dongusu(hedef, durum, log, dur, baslangic):
    import json
    sock = udp_soket()
    while not dur.is_set():
        time.sleep(2.0)
        # GUCLENDIRME: telemetri hicbir kosulda ana isi/AI'yi etkilememeli — tum
        # govde try ile korunur (cpu okuma / json / soket hatasi thread'i oldurmesin).
        try:
            ip = hedef.aktif_ip()
            if ip is None:
                continue
            d = durum.kopya()
            d.update(t=time.time(), calisma_sn=round(time.time() - baslangic, 1),
                     cpu_c=cpu_sicaklik())
            sock.sendto(json.dumps(d).encode(), (ip, TLM_PORT))
            log.debug("tlm → %s: %s", ip, d)
        except Exception as e:
            log.warning("telemetri hatasi (atlaniyor): %s", e)


# ---------------------------------------------------------------- ana akis

def main():
    ap = argparse.ArgumentParser(description="Navitas dron RPi yayin")
    ap.add_argument("--sim", metavar="KAYNAK",
                    help="kamerasiz test: gorsel klasoru / video / tek gorsel")
    ap.add_argument("--no-ai", action="store_true", help="model calistirma, sadece ham yayin")
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--imgsz", type=int, default=512)
    ap.add_argument("--bitrate", type=int, default=4_000_000, help="ham H.264 bps (vars. 4M)")
    ap.add_argument("--ai-fps", type=float, default=0.0,
                    help="AI kare sinirlamasi (0=serbest; CPU/isi icin ornek: 3)")
    ap.add_argument("--ai-kalite", type=int, default=55, metavar="0-100",
                    help="AI overlay JPEG kalitesi (dusuk=kucuk kare=wifi'da az kayip; vars. 55)")
    ap.add_argument("--kayit", action="store_true",
                    help="her izleyici oturumunu RPi'ye YEREL kaydet (video+meta+log)")
    ap.add_argument("--kayit-dir", default=str(_kok.parent / "kayitlar"),
                    help="kayit kok dizini (vars. ~/navitas/kayitlar). Tarih/SAAT_id ile adlandirilir")
    ap.add_argument("--dondur", type=int, choices=[0, 180], default=0,
                    help="kamera ters monteliyse 180 (bant/yapistirma montaji icin)")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--log-file", help="loglari dosyaya da yaz")
    args = ap.parse_args()

    log = log_kur("rpi_yayin", args.debug, args.log_file)
    dur = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: dur.set())

    # AG DINLEYICILERI HEMEN BASLAT — kameradan BAGIMSIZ. Boylece kamera bozuk/gevsek
    # olsa bile RPi izleyiciye CEVAP VERIR (HELLO + telemetri "kamera yok" bilgisiyle),
    # sistem "sagir" kalmaz. (Onceden kamera-retry ag thread'lerini bloke ediyordu.)
    hedef = Hedef(log)
    durum = Durum()
    baslangic = time.time()
    threading.Thread(target=hello_dinle, args=(hedef, log, dur), daemon=True).start()
    threading.Thread(target=telemetri_dongusu,
                     args=(hedef, durum, log, dur, baslangic), daemon=True).start()

    if args.sim:
        kamera = SimKamera(log, args.bitrate, args.sim, args.dondur)
    else:
        # GUCLENDIRME: kamera acilamazsa (serit kablo gevsek → "chip id" I/O hatasi,
        # ya da baska bir sebep) CRASH-LOOP yapma; net mesaj ver, 5sn'de bir tekrar dene.
        # Kablo yeniden oturtulunca servis KENDILIGINDEN duzelir (yeniden baslatma gerekmez).
        kamera = None
        while kamera is None and not dur.is_set():
            durum.guncelle(karar="KAMERA-YOK")   # izleyici bandinda gorunur
            try:
                kamera = PiKamera(log, args.bitrate, args.dondur)
            except ImportError:
                log.error("picamera2 yok. RPi'de kur: sudo apt install python3-picamera2 "
                          "(kamerasiz test icin: --sim <kaynak>)")
                return 1
            except Exception as e:
                log.error("KAMERA ACILAMADI (serit kablo gevsek olabilir — imx708 chip id "
                          "I/O hatasi tipik): %s — kabloyu kontrol et, 5sn sonra tekrar", e)
                dur.wait(5)
        if kamera is None:
            return 0
        durum.guncelle(karar="-")

    kayit = Kayit(args.kayit_dir, log) if args.kayit else None
    if kayit is not None:
        log.info("KAYIT acik → %s (her oturum: tarih/SAAT_id_video.mp4 + meta + log)",
                 args.kayit_dir)
    if not args.no_ai:
        threading.Thread(target=ai_dongusu,
                         args=(kamera, hedef, durum, log, dur, args.conf,
                               args.imgsz, args.ai_fps, args.ai_kalite, kayit),
                         daemon=True).start()

    # Ana dongu: ham yayini izleyiciye gore ac/kapa (kalp atisi kesilirse durdur).
    ham_ip = None
    try:
        while not dur.is_set():
            hedef.degisti.wait(timeout=1.0)
            hedef.degisti.clear()
            ip = hedef.aktif_ip()
            if ip == ham_ip:
                continue
            if ip is None:
                kamera.ham_durdur()
            else:
                kamera.ham_baslat(ip)
            ham_ip = ip
            if ip is None:
                hedef.dusur()   # ip'yi temizle ki geri gelince degisti tetiklensin
    except KeyboardInterrupt:
        pass
    finally:
        dur.set()
        if kayit is not None and kayit.aktif():
            kayit.kapat()          # kapanista yarim kaydi sonlandir (meta yaz)
        kamera.kapat()
        log.info("kapatildi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
