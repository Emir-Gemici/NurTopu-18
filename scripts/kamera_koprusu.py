#!/usr/bin/env python3
"""NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.4 · donanim kunyesi §0.2 · GOREV K):
Jetson Nano 4GB (JetPack 4.6.x, Ubuntu 18.04) uzerinde Raspberry Pi HQ kamera
(IMX477, CSI) YALNIZ GStreamer `nvarguscamerasrc` ile okunur; GStreamer'li OpenCV
yalniz SISTEM Python 3.6 + sistem OpenCV 4.1 paketinde vardir. `rpi_inference.py`
ise `ultralytics` yuzunden Python >= 3.8 venv'de kosar ve o venv'in
`opencv-python(-headless)` tekerlegi GStreamer'siz derlenmistir: venv'den
kameraya DOGRUDAN ulasilamaz.

Bu surec KOPRUDUR: sistem Python'unda kareyi alir, JPEG'e cevirir ve
`http://127.0.0.1:8080/video` ucundan multipart/x-mixed-replace (MJPEG) olarak
sunar — DroidCam'in `/video` ucuyla AYNI KALIP. `rpi_inference --kaynak http://…`
bunu (FFmpeg arka ucuyla) zaten okur; tuketici kodu DEGISMEZ.

Uclar:
  /video     multipart/x-mixed-replace MJPEG akisi (istemci basina bir iplik)
  /kare.jpg  tek TAZE kare (image/jpeg)
  /durum     JSON: kaynak_acik, kare_sayaci, fps, son_hata, boyut, ... (HER ZAMAN 200)

Fail-visible / fail-closed:
  * Kaynak acilamiyor ya da koptu -> KIRMIZI log, YENIDEN_ACMA_ARALIGI_S sonra
    yeniden acma; HTTP sunucu AYAKTA kalir, `/durum` `kaynak_acik:false` der.
  * Bayat kare SUNULMAZ: `/video` ve `/kare.jpg` yeni kare gelmiyorsa 503 verir
    ya da acik akisi KAPATIR (tuketici `KAMERA_DUSEN_KARE_UST_SINIRI` ile
    kontrollu biter, systemd onu yeniden kaldirir — cokme dongusu `--durum`da
    GORUNUR). Sahte/yer tutucu kare uretilmez.
  * Tek uretici iplik; istemciler son JPEG'in DEGISMEZ (bytes) kopyasini kilit
    altinda alir — uretici tamponu yerinde DEGISTIRMEZ, referansi degistirir.

Python 3.6 UYUMU ZORUNLUDUR (sistem Python'u): walrus, posonly, `from __future__
import annotations`, ThreadingHTTPServer (3.7), `str.removeprefix` (3.9) YOK.
Yalniz stdlib + cv2 + numpy (anayasa madde 4). Kilit:
tests/test_faz_b_kamera_koprusu.py (ast ile).

Kullanim (Jetson, systemd/navitas-kamera-koprusu.service bunu kosar):
  /usr/bin/python3 scripts/kamera_koprusu.py                # nvargus 1280x720 -> :8080
  /usr/bin/python3 scripts/kamera_koprusu.py --kaynak 0     # USB (UVC) kamera
  /usr/bin/python3 scripts/kamera_koprusu.py --kaynak dosya.avi --port 8081 --fps 5
"""
import argparse
import json
import signal
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlsplit

import cv2
import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")   # 3.7+; 3.6'da AttributeError
    except (AttributeError, OSError):
        pass


LOG_ONEKI = "[KAMERA_KOPRUSU]"
YEREL_HOST = "127.0.0.1"
#: Kopru ucu. jetson_baslat.sh `KAMERA=http://127.0.0.1:8080/video` ile bu
#: birimi kaldirir ve rpi_inference'a ayni URL'yi verir (test kilitler).
VARSAYILAN_PORT = 8080
VIDEO_YOLU = "/video"
KARE_YOLU = "/kare.jpg"
DURUM_YOLU = "/durum"
#: JPEG kalitesi: 80 -> 720p'de ~60-120 KB/kare; 95 uzeri Nano CPU'sunu bosa yer.
VARSAYILAN_KALITE = 80
#: Uretici fps tavani. Tuketici (rpi_inference, Nano CPU'da ~1 FPS) daha hizli
#: kare TUKETEMEZ; 10 fps akisi taze tutar, JPEG kodlama yukunu torch'un
#: kullandigi 4 cekirdekten uzak tutar. 0 = tavan yok.
VARSAYILAN_FPS_TAVANI = 10.0
#: nvarguscamerasrc varsayilan kipi (IMX477 ISP olcekler). Cumartesi olculur;
#: farkli kip gerekirse --genislik/--yukseklik/--kamera-fps ya da --kaynak ile
#: TAM boru dizgisi verilir.
VARSAYILAN_GENISLIK = 1280
VARSAYILAN_YUKSEKLIK = 720
VARSAYILAN_KAMERA_FPS = 30
VARSAYILAN_SENSOR_ID = 0
KAYNAK_NVARGUS = "nvargus"          # --kaynak icin ad; bos da ayni anlama gelir
KAYNAK_TURU_NVARGUS = "nvargus"
KAYNAK_TURU_GSTREAMER = "gstreamer"
KAYNAK_TURU_INDEKS = "indeks"
KAYNAK_TURU_URL = "url"
KAYNAK_TURU_DOSYA = "dosya"
#: Kaynak arizasi sonrasi yeniden acma araligi (seri_hub ile ayni gerekce:
#: daha sik denemek log seli, daha seyrek denemek bosuna gecikme).
YENIDEN_ACMA_ARALIGI_S = 1.0
#: Ardisik okuma hatasi ust siniri; asilinca kaynak KOPTU sayilir ve yeniden
#: acilir (rpi_inference.KAMERA_DUSEN_KARE_UST_SINIRI ile ayni ruh; o modul
#: Python 3.6'da import edilemez — sabit burada, gerekcesiyle).
DUSEN_KARE_UST_SINIRI = 30
DUSEN_KARE_BEKLEME_S = 0.02
#: /video: bu kadar sure YENI kare gelmezse akis kapatilir; /kare.jpg: bundan
#: yasli kare sunulmaz. Kaynak kopunca tuketici bunu GORUR (bayat kare yok).
AKIS_KARE_BEKLEME_S = 5.0
#: Basarisiz acma denemelerinde her N. denemede bir KIRMIZI log (ilk deneme hep).
ACMA_LOG_SEYREKLIGI = 10
SINIR = "navitas-kare"              # multipart boundary
FPS_PENCERESI = 30                  # olculen fps icin son N kare zamani
VARSAYILAN_LOG_ARALIGI_S = 10.0     # periyodik sayac logu (0 = kapali)


def logla(metin, kirmizi=False, saat=time.monotonic):
    seviye = "KIRMIZI " if kirmizi else ""
    print("{} t={:.3f} {}{}".format(LOG_ONEKI, saat(), seviye, metin),
          file=sys.stderr if kirmizi else sys.stdout, flush=True)


def nvargus_boru(genislik=VARSAYILAN_GENISLIK, yukseklik=VARSAYILAN_YUKSEKLIK,
                 fps=VARSAYILAN_KAMERA_FPS, sensor_id=VARSAYILAN_SENSOR_ID):
    """Jetson CSI kamerasi icin GStreamer boru dizgisi (NVMM -> BGR -> appsink).

    `appsink drop=true max-buffers=1`: tuketici yavassa en TAZE kare kalir,
    kuyruk buyumez (gecikme = 1 kare).
    """
    return (
        "nvarguscamerasrc sensor-id={sid} ! "
        "video/x-raw(memory:NVMM), width=(int){w}, height=(int){h}, "
        "format=(string)NV12, framerate=(fraction){fps}/1 ! "
        "nvvidconv ! video/x-raw, format=(string)BGRx ! "
        "videoconvert ! video/x-raw, format=(string)BGR ! "
        "appsink drop=true max-buffers=1"
    ).format(sid=int(sensor_id), w=int(genislik), h=int(yukseklik), fps=int(fps))


def kaynagi_coz(metin, **nvargus_ayar):
    """--kaynak metnini (VideoCapture argumani, apiPreference, tur) ucluye cevir.

    bos / "nvargus" -> nvarguscamerasrc borusu (CAP_GSTREAMER)
    "0", "2"        -> kamera indeksi (USB/UVC)
    "a ! b"         -> TAM GStreamer borusu (CAP_GSTREAMER)
    "http://…"      -> URL (FFmpeg)
    diger           -> dosya/cihaz yolu
    """
    m = "" if metin is None else str(metin).strip()
    if m == "" or m == KAYNAK_NVARGUS:
        return nvargus_boru(**nvargus_ayar), cv2.CAP_GSTREAMER, KAYNAK_TURU_NVARGUS
    try:
        return int(m), cv2.CAP_ANY, KAYNAK_TURU_INDEKS
    except ValueError:
        pass
    if "!" in m:
        return m, cv2.CAP_GSTREAMER, KAYNAK_TURU_GSTREAMER
    if "://" in m:
        return m, cv2.CAP_ANY, KAYNAK_TURU_URL
    return m, cv2.CAP_ANY, KAYNAK_TURU_DOSYA


def video_url(port=VARSAYILAN_PORT, host=YEREL_HOST):
    """rpi_inference --kaynak icin verilecek URL (jetson_baslat.sh ile ayni)."""
    return "http://{}:{}{}".format(host, int(port), VIDEO_YOLU)


def _http_yetkisi_dogrula(metin):
    """HTTP ``Host`` basligini guvenli ``host[:port]`` olarak dogrula.

    Kopru dis LAN'a ``0.0.0.0`` ile baglandiginda o adres istemci hedefi DEGILDIR.
    /durum, istegi yapan YKI'nin kullandigi Host basligini ilan eder. Kontrol
    karakteri/yol/kullanici bilgisi iceren basliklar yansitilmaz.
    """
    if not isinstance(metin, str):
        return None
    yetki = metin.strip()
    if not yetki or any(ord(c) < 33 or ord(c) == 127 for c in yetki):
        return None
    if any(c in yetki for c in "/\\?#@"):
        return None
    try:
        parca = urlsplit("//" + yetki)
        _port = parca.port
    except ValueError:
        return None
    if not parca.hostname or parca.path or parca.query or parca.fragment:
        return None
    return yetki


def _uc_url(yetki, yol):
    return None if yetki is None else "http://{}{}".format(yetki, yol)


class KareUretici(threading.Thread):
    """TEK uretici iplik: kaynagi acar, kare okur, JPEG'e cevirir, son kareyi tutar.

    Istemciler `kare_bekle` ile son JPEG'in bytes nesnesini (degismez) alir;
    tampon yerinde degistirilmez, referans degistirilir — istemci basina kopya
    anlami budur. Butun sayaclar `kilit` altindadir.
    """

    def __init__(self, kaynak_metin, kalite=VARSAYILAN_KALITE,
                 fps_tavani=VARSAYILAN_FPS_TAVANI, log_aralik_s=VARSAYILAN_LOG_ARALIGI_S,
                 saat=time.monotonic, log=logla, **nvargus_ayar):
        super().__init__(name="kamera-uretici", daemon=True)
        self.kaynak_metin = "" if kaynak_metin is None else str(kaynak_metin)
        self.kaynak_arg, self.kaynak_api, self.kaynak_turu = kaynagi_coz(
            self.kaynak_metin, **nvargus_ayar)
        self.kalite = int(kalite)
        self.fps_tavani = float(fps_tavani)
        self.log_aralik_s = float(log_aralik_s)
        self.saat = saat
        self.log = log
        self.kilit = threading.Lock()
        self.kosul = threading.Condition(self.kilit)
        self._dur = threading.Event()
        # kilit altindaki durum
        self.jpeg = None            # son karenin JPEG bytes'i (degismez)
        self.sira = 0               # her yeni karede +1 (istemci "yeni mi" buradan bilir)
        self.sekil = None           # (h, w)
        self.son_kare_t = None
        self.kaynak_acik = False
        self.son_hata = None
        self.acma_denemesi = 0      # toplam acma denemesi
        self.acma_sayisi = 0        # basarili acilis sayisi
        self.kare_sayaci = 0
        self.dusen_kare = 0
        self.kodlama_hatasi = 0
        self.istemci_sayisi = 0
        self.baslangic_t = saat()
        self._zamanlar = deque(maxlen=FPS_PENCERESI)

    # ── istemci tarafi ──────────────────────────────────────────────────
    def kare_bekle(self, onceki_sira=None, zaman_asimi_s=AKIS_KARE_BEKLEME_S,
                   azami_yas_s=None):
        """`onceki_sira`dan YENI bir kare gelene dek bekle -> (jpeg, sira) ya da (None, sira).

        onceki_sira=None: eldeki son kare (azami_yas_s verilirse yalniz tazeyse).
        """
        def hazir():
            if self._dur.is_set():          # kapanis: bekleyen istemciler hemen birakilir
                return True
            if self.jpeg is None:
                return False
            if onceki_sira is not None and self.sira == onceki_sira:
                return False
            if azami_yas_s is not None and (self.son_kare_t is None or
                                            self.saat() - self.son_kare_t > azami_yas_s):
                return False
            return True

        with self.kosul:
            if not self.kosul.wait_for(hazir, timeout=zaman_asimi_s) or self._dur.is_set():
                return None, self.sira
            return self.jpeg, self.sira

    def istemci_ekle(self):
        with self.kilit:
            self.istemci_sayisi += 1

    def istemci_cikar(self):
        with self.kilit:
            self.istemci_sayisi = max(0, self.istemci_sayisi - 1)

    def olculen_fps(self):
        """Son FPS_PENCERESI karenin ortalamasi; kilit CAGIRANDA olmali."""
        if len(self._zamanlar) < 2:
            return None
        sure = self._zamanlar[-1] - self._zamanlar[0]
        if sure <= 0:
            return None
        return (len(self._zamanlar) - 1) / sure

    def durum(self):
        """/durum JSON'unun uretici kismi (kilit altinda tutarli anlik goruntu)."""
        with self.kilit:
            simdi = self.saat()
            return {
                "kaynak": self.kaynak_metin or KAYNAK_NVARGUS,
                "kaynak_turu": self.kaynak_turu,
                "kaynak_acik": bool(self.kaynak_acik),
                "kare_sayaci": self.kare_sayaci,
                "dusen_kare": self.dusen_kare,
                "kodlama_hatasi": self.kodlama_hatasi,
                "fps": self.olculen_fps(),
                "fps_tavani": self.fps_tavani,
                "kalite": self.kalite,
                "boyut": [self.sekil[1], self.sekil[0]] if self.sekil else None,
                "son_kare_yasi_s": (None if self.son_kare_t is None
                                    else round(simdi - self.son_kare_t, 3)),
                "son_hata": self.son_hata,
                "acma_denemesi": self.acma_denemesi,
                "acma_sayisi": self.acma_sayisi,
                "istemci_sayisi": self.istemci_sayisi,
                "calisma_s": round(simdi - self.baslangic_t, 3),
            }

    # ── uretici tarafi ──────────────────────────────────────────────────
    def durdur(self):
        self._dur.set()
        with self.kosul:
            self.kosul.notify_all()

    def _ac(self):
        """Kaynagi ac; basarisizsa None (KIRMIZI log seyrekligiyle).

        Sayac ve sonuc (son_hata / kaynak_acik) AYNI kilit bloğunda yazilir:
        /durum hicbir anda "deneme sayildi ama sonucu yok" gostermez.
        """
        with self.kilit:
            deneme = self.acma_denemesi + 1
        cap = None
        hata = None
        try:
            cap = cv2.VideoCapture(self.kaynak_arg, self.kaynak_api)
            if not cap.isOpened():
                hata = "kaynak acilamadi (deneme {}): {!r} [{}]".format(
                    deneme, self.kaynak_arg, self.kaynak_turu)
        except (cv2.error, OSError, ValueError, TypeError) as exc:   # pragma: no cover - surucuye bagli
            hata = "kaynak acilirken hata (deneme {}): {!r}: {}".format(
                deneme, self.kaynak_arg, exc)
        if hata is not None:
            if cap is not None:
                cap.release()
            with self.kilit:
                self.acma_denemesi = deneme
                self.kaynak_acik = False
                self.son_hata = hata
            if deneme == 1 or deneme % ACMA_LOG_SEYREKLIGI == 0:
                self.log(hata + " — {} s sonra yeniden".format(YENIDEN_ACMA_ARALIGI_S),
                         kirmizi=True)
            return None
        with self.kilit:
            self.acma_denemesi = deneme
            self.kaynak_acik = True
            self.son_hata = None
            self.acma_sayisi += 1
        self.log("kaynak ACILDI (deneme {}): {!r} [{}]".format(
            deneme, self.kaynak_arg, self.kaynak_turu))
        return cap

    def _koptu(self, cap, neden):
        with self.kilit:
            self.kaynak_acik = False
            self.son_hata = neden
        self.log(neden + " — kaynak KAPATILDI, {} s sonra yeniden acilacak".format(
            YENIDEN_ACMA_ARALIGI_S), kirmizi=True)
        cap.release()

    def _kare_yayinla(self, kare):
        if not isinstance(kare, np.ndarray) or kare.ndim != 3 or kare.shape[2] != 3:
            return False
        try:
            ok, tampon = cv2.imencode(".jpg", kare, [int(cv2.IMWRITE_JPEG_QUALITY), self.kalite])
        except cv2.error:
            ok, tampon = False, None
        if not ok or tampon is None:
            with self.kilit:
                self.kodlama_hatasi += 1
            return False
        veri = tampon.tobytes()             # degismez kopya: istemciler bunu alir
        simdi = self.saat()
        with self.kosul:
            self.jpeg = veri
            self.sira += 1
            self.sekil = (int(kare.shape[0]), int(kare.shape[1]))
            self.son_kare_t = simdi
            self.kare_sayaci += 1
            self._zamanlar.append(simdi)
            self.kosul.notify_all()
        return True

    def _sayac_logla(self):
        d = self.durum()
        fps = d["fps"]
        self.log("kare={} dusen={} fps={} istemci={} kaynak_acik={} boyut={}".format(
            d["kare_sayaci"], d["dusen_kare"],
            "?" if fps is None else "{:.1f}".format(fps),
            d["istemci_sayisi"], d["kaynak_acik"], d["boyut"]))

    def run(self):
        cap = None
        ardisik = 0
        okunan_bu_acilis = 0
        sonraki_kare_t = None
        son_log_t = self.saat()
        try:
            while not self._dur.is_set():
                if cap is None:
                    cap = self._ac()
                    okunan_bu_acilis = 0
                    ardisik = 0
                    if cap is None:
                        self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                        continue
                ok, kare = cap.read()
                if (not ok or kare is None) and self.kaynak_turu == KAYNAK_TURU_DOSYA \
                        and okunan_bu_acilis > 0:
                    # Test/prova dosyasi bitti: basa sar (sessiz — ariza degil)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, kare = cap.read()
                    if not ok or kare is None:
                        cap.release()
                        cap = cv2.VideoCapture(self.kaynak_arg, self.kaynak_api)
                        ok, kare = cap.read() if cap.isOpened() else (False, None)
                    okunan_bu_acilis = 0
                if not ok or kare is None:
                    ardisik += 1
                    with self.kilit:
                        self.dusen_kare += 1
                    if ardisik >= DUSEN_KARE_UST_SINIRI:
                        self._koptu(cap, "{} ardisik dusen kare (ust sinir {})".format(
                            ardisik, DUSEN_KARE_UST_SINIRI))
                        cap = None
                        self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                        continue
                    self._dur.wait(DUSEN_KARE_BEKLEME_S)
                    continue
                ardisik = 0
                okunan_bu_acilis += 1
                self._kare_yayinla(kare)
                if self.log_aralik_s > 0 and self.saat() - son_log_t >= self.log_aralik_s:
                    son_log_t = self.saat()
                    self._sayac_logla()
                if self.fps_tavani > 0:
                    aralik = 1.0 / self.fps_tavani
                    simdi = self.saat()
                    if sonraki_kare_t is None or sonraki_kare_t < simdi - aralik:
                        sonraki_kare_t = simdi
                    sonraki_kare_t += aralik
                    bekle = sonraki_kare_t - simdi
                    if bekle > 0:
                        self._dur.wait(bekle)
        finally:
            if cap is not None:
                cap.release()
            with self.kosul:
                self.kaynak_acik = False
                self.kosul.notify_all()


class KopruIstekleyici(BaseHTTPRequestHandler):
    """HTTP uclari; `self.server.uretici` KareUretici'dir."""

    server_version = "NavitasKameraKoprusu/1"
    protocol_version = "HTTP/1.0"      # akis: yanit bitince baglanti kapanir

    def log_message(self, bicim, *args):   # BaseHTTPRequestHandler stderr'ini bastir
        if getattr(self.server, "istek_logu", False):
            self.server.uretici.log("istek {} {}".format(self.address_string(), bicim % args))

    def _json(self, kod, veri):
        govde = json.dumps(veri, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(govde)

    def _durum_sozlugu(self):
        u = self.server.uretici
        d = u.durum()
        bind_host = str(self.server.server_address[0])
        port = int(self.server.server_address[1])
        # ``0.0.0.0`` bir DINLEME beyanidir, YKI'nin baglanabilecegi URL degil.
        # HTTP istemcisinin Host basligi gercek arayuz/IP'yi tasir. Gecersiz ya
        # da eksikse yalniz belirli bir bind adresi guvenli geri donus olabilir.
        yetki = _http_yetkisi_dogrula(self.headers.get("Host"))
        if yetki is None and bind_host not in ("0.0.0.0", "::", ""):
            yetki = "{}:{}".format(bind_host, port)
        d["port"] = port
        d["bind_host"] = bind_host
        d["istek_host"] = yetki
        d["video_url"] = _uc_url(yetki, VIDEO_YOLU)
        d["kare_url"] = _uc_url(yetki, KARE_YOLU)
        d["durum_url"] = _uc_url(yetki, DURUM_YOLU)
        return d

    def do_GET(self):
        yol = self.path.split("?", 1)[0]
        if yol == VIDEO_YOLU:
            self._video()
        elif yol == KARE_YOLU:
            self._kare()
        elif yol == DURUM_YOLU:
            self._json(200, self._durum_sozlugu())
        elif yol == "/":
            govde = "NAVITAS kamera koprusu: {} {} {}\n".format(
                VIDEO_YOLU, KARE_YOLU, DURUM_YOLU).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)
        else:
            self._json(404, {"hata": "bilinmeyen yol", "yol": yol,
                             "uclar": [VIDEO_YOLU, KARE_YOLU, DURUM_YOLU]})

    def _kaynak_yok(self):
        d = self._durum_sozlugu()
        d["hata"] = "kaynak acik degil ya da taze kare yok"
        self._json(503, d)

    def _kare(self):
        u = self.server.uretici
        veri, sira = u.kare_bekle(None, zaman_asimi_s=0.0, azami_yas_s=AKIS_KARE_BEKLEME_S)
        if veri is None:
            self._kaynak_yok()
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Kare-Sira", str(sira))
        self.end_headers()
        self.wfile.write(veri)

    def _video(self):
        u = self.server.uretici
        # Kaynak kapaliyken bekletmeden 503: tuketici (cv2.VideoCapture) hemen
        # "acilamadi" gorsun. Acikken ilk kare icin en cok AKIS_KARE_BEKLEME_S.
        with u.kilit:
            acik = u.kaynak_acik
        veri, sira = (u.kare_bekle(None, AKIS_KARE_BEKLEME_S, azami_yas_s=AKIS_KARE_BEKLEME_S)
                      if acik else (None, 0))
        if veri is None:
            self._kaynak_yok()
            return
        self.send_response(200)
        self.send_header("Content-Type",
                         "multipart/x-mixed-replace; boundary={}".format(SINIR))
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        u.istemci_ekle()
        gonderilen = 0
        try:
            while True:
                baslik = ("--{}\r\nContent-Type: image/jpeg\r\n"
                          "Content-Length: {}\r\n\r\n").format(SINIR, len(veri)).encode("ascii")
                self.wfile.write(baslik)
                self.wfile.write(veri)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
                gonderilen += 1
                veri, sira = u.kare_bekle(sira, AKIS_KARE_BEKLEME_S)
                if veri is None:
                    if u._dur.is_set():        # kopru kapaniyor: sessiz bitis
                        break
                    u.log("akis {}: {} s yeni kare yok — istemci baglantisi KAPATILDI "
                          "(gonderilen={})".format(self.address_string(),
                                                   AKIS_KARE_BEKLEME_S, gonderilen),
                          kirmizi=True)
                    break
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass                       # istemci kapatti
        finally:
            u.istemci_cikar()


class KopruSunucusu(ThreadingMixIn, HTTPServer):
    """Istemci basina iplik (ThreadingHTTPServer 3.7+, burada 3.6 uyumlu)."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, adres, uretici, istek_logu=False):
        self.uretici = uretici
        self.istek_logu = istek_logu
        super().__init__(adres, KopruIstekleyici)


def kopru_kur(kaynak, port=VARSAYILAN_PORT, host=YEREL_HOST, kalite=VARSAYILAN_KALITE,
              fps_tavani=VARSAYILAN_FPS_TAVANI, log_aralik_s=VARSAYILAN_LOG_ARALIGI_S,
              istek_logu=False, log=logla, **nvargus_ayar):
    """Uretici ipligini baslat + HTTP sunucuyu BAGLA (serve_forever CAGIRMAZ).

    -> (sunucu, uretici). port=0: efemer (test). Kaynak yoksa da doner —
    uretici arka planda yeniden acma dongusundedir (fail-visible).
    """
    uretici = KareUretici(kaynak, kalite=kalite, fps_tavani=fps_tavani,
                          log_aralik_s=log_aralik_s, log=log, **nvargus_ayar)
    sunucu = KopruSunucusu((host, int(port)), uretici, istek_logu=istek_logu)
    uretici.start()
    return sunucu, uretici


def kopru_kapat(sunucu, uretici):
    """Uretici + sunucuyu kapat. `shutdown` serve_forever kosmuyorsa hemen doner."""
    uretici.durdur()
    sunucu.shutdown()
    sunucu.server_close()
    uretici.join(timeout=3.0)


def _parser():
    p = argparse.ArgumentParser(
        description="NAVITAS kamera koprusu: kaynak (CSI/USB/dosya) -> MJPEG HTTP")
    p.add_argument("--kaynak", default=KAYNAK_NVARGUS,
                   help="'nvargus' (varsayilan, CSI IMX477), kamera indeksi (0), "
                        "TAM GStreamer borusu ('a ! b'), URL ya da dosya yolu (test)")
    p.add_argument("--port", type=int, default=VARSAYILAN_PORT,
                   help="HTTP portu (varsayilan {}; 0 = efemer, baslarken yazilir)".format(
                       VARSAYILAN_PORT))
    p.add_argument("--host", default=YEREL_HOST,
                   help="dinlenecek adres (varsayilan {}; PC'den izlemek icin 0.0.0.0)".format(
                       YEREL_HOST))
    p.add_argument("--kalite", type=int, default=VARSAYILAN_KALITE, help="JPEG kalitesi 1-100")
    p.add_argument("--fps", type=float, default=VARSAYILAN_FPS_TAVANI,
                   help="uretici fps tavani (0 = tavan yok)")
    p.add_argument("--genislik", type=int, default=VARSAYILAN_GENISLIK, help="nvargus kip genisligi")
    p.add_argument("--yukseklik", type=int, default=VARSAYILAN_YUKSEKLIK, help="nvargus kip yuksekligi")
    p.add_argument("--kamera-fps", type=int, default=VARSAYILAN_KAMERA_FPS, help="nvargus kip fps")
    p.add_argument("--sensor-id", type=int, default=VARSAYILAN_SENSOR_ID, help="nvargus sensor-id")
    p.add_argument("--log-aralik", type=float, default=VARSAYILAN_LOG_ARALIGI_S,
                   help="periyodik sayac logu (s), 0 = kapali")
    p.add_argument("--istek-logu", action="store_true", help="her HTTP istegini logla")
    return p


def main(argv=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if not 1 <= args.kalite <= 100:
        parser.error("--kalite 1-100 arasi olmali")
    if args.fps < 0:
        parser.error("--fps negatif olamaz")
    if args.port < 0 or args.port > 65535:
        parser.error("--port 0-65535 arasi olmali")
    if args.genislik <= 0 or args.yukseklik <= 0 or args.kamera_fps <= 0:
        parser.error("--genislik/--yukseklik/--kamera-fps pozitif olmali")
    try:
        sunucu, uretici = kopru_kur(
            args.kaynak, port=args.port, host=args.host, kalite=args.kalite,
            fps_tavani=args.fps, log_aralik_s=args.log_aralik, istek_logu=args.istek_logu,
            genislik=args.genislik, yukseklik=args.yukseklik, fps=args.kamera_fps,
            sensor_id=args.sensor_id)
    except OSError as exc:
        # Port doluysa SESSIZ beklemek yok: systemd 2 s sonra yeniden dener, journal gosterir
        logla("HATA: HTTP ucu acilamadi {}:{}: {}".format(args.host, args.port, exc), kirmizi=True)
        return 3
    port = sunucu.server_address[1]
    logla("dinliyor {} · kare {} · durum {} · kaynak={!r} [{}] kalite={} fps_tavani={}".format(
        video_url(port, args.host), "http://{}:{}{}".format(args.host, port, KARE_YOLU),
        "http://{}:{}{}".format(args.host, port, DURUM_YOLU),
        uretici.kaynak_metin or KAYNAK_NVARGUS, uretici.kaynak_turu, args.kalite, args.fps))

    def _sinyal(_s, _f):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _sinyal)
    try:
        sunucu.serve_forever(poll_interval=0.2)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        kopru_kapat(sunucu, uretici)
        logla("kapandi")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
