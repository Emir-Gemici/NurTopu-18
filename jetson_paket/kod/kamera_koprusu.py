#!/usr/bin/env python3
"""[D-431: kart Orin Nano cikti - asagidaki 'Nano 4GB / JetPack 4.6' kunyesi GECERSIZ, bkz. 2. paragraf]
NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.4 · donanim kunyesi §0.2 · GOREV K):
Jetson Nano 4GB (JetPack 4.6.x, Ubuntu 18.04) uzerinde Raspberry Pi HQ kamera
(IMX477, CSI) YALNIZ GStreamer `nvarguscamerasrc` ile okunur; GStreamer'li OpenCV
yalniz SISTEM Python 3.6 + sistem OpenCV 4.1 paketinde vardir. `rpi_inference.py`
ise `ultralytics` yuzunden Python >= 3.8 venv'de kosar ve o venv'in
`opencv-python(-headless)` tekerlegi GStreamer'siz derlenmistir: venv'den
kameraya DOGRUDAN ulasilamaz.

D-431 (6 Eylul 2026, OLCULDU): kart Jetson Nano degil Jetson Orin Nano Developer Kit 4 GB
(JetPack 7.2.1, Ubuntu 24.04, sistem Python 3.12 + python3-opencv 4.6 GStreamer'li). Ayrim
aynen gecerli: kopru SISTEM Python'unda kosar, rpi_inference ~/venv312'de. Py3.6 / cv2 4.1
API kisiti (tests/test_faz_b_kamera_koprusu.py) bilerek TUTULUR - daha siki kapi gevsetilmez.

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
  # T226 (D-443, MK15 video hatti): PC'de HDMI yakalama karti (UVC) -> YKS
  python scripts/kamera_koprusu.py --kaynak 0 --arka-uc dshow --genislik 1280 --yukseklik 720 --kamera-fps 30

Kip ayari (T226): indeks ("0") ya da V4L2 aygit ("/dev/video1") kaynaginda
--genislik/--yukseklik/--kamera-fps VERILIRSE cap.set ile uygulanir; surucunun
bildirdigi deger (`kamera_ayari`), gercek kare boyutu (`boyut`) ve ikisinin
istenenle eslesmesi (`cozunurluk_eslesti`) /durum'a yazilir, uyusmazlik KIRMIZI
loglanir. Verilmezse surucu varsayilani (eski davranis; olculdu: bu PC'nin web
kamerasi 640x480 aciliyor). --arka-uc {auto,dshow,msmf,v4l2} yalniz indeks/aygit
kaynaginda apiPreference'tir. nvargus borusu DEGISMEZ (kip boru dizgisinde).
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
#: YALNIZ GORUNTULEME hatti (21 Eyl 2026): model hattindan (/video) AYRI.
#: /video'nun sundugu JPEG'den turetilir; uretici ve /video koduna dokunulmaz.
EKRAN_YOLU = "/ekran"
EKRAN_KARE_YOLU = "/ekran.jpg"
EKRAN_BOYUT = (1280, 720)           # (genislik, yukseklik) — 16:9 yatay ekran
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
#: T226 (D-443): V4L2 aygit yolu (/dev/videoN) DOSYA degil CIHAZ'dir: dosya sonu
#: "basa sar" mantigi uygulanmaz, kip ayari (cozunurluk/FPS) uygulanir.
KAYNAK_TURU_CIHAZ = "cihaz"
CIHAZ_YOLU_ONEKI = "/dev/video"
#: Kip ayarinin (cap.set) uygulandigi kaynak turleri. nvargus kipi boru
#: dizgisindedir (set UYGULANMAZ — davranis degismez); URL/dosya/GStreamer
#: kaynaginda cozunurluk kaynagin ozelligidir, koprunun degil.
KIP_AYARLI_TURLER = (KAYNAK_TURU_INDEKS, KAYNAK_TURU_CIHAZ)
#: T226: --arka-uc -> cv2 VideoCapture apiPreference. OLCULDU (D-443, 10 Eyl):
#: bu PC'nin web kamerasi indeks 0'da surucu varsayilani 640x480 aciliyor;
#: DSHOW ve MSMF ile set(1280x720) tuttu. Yakalama kartinda (MS2130 vb.) hangisi
#: kararli, sahada olculur -> secilebilir olmali. auto = CAP_ANY (eski davranis).
ARKA_UC_OTOMATIK = "auto"
ARKA_UC_SECENEKLERI = ("auto", "dshow", "msmf", "v4l2")
#: T226-D (D-448): arka uc sabitleri modul YUKLENIRKEN okunur; bir derlemede
#: (Jetson python3-opencv) sabit eksikse `cv2.CAP_DSHOW` AttributeError ile
#: importu -- dolayisiyla kopruyu, nvargus yolu dahil -- dusururdu. Yedek
#: degerler OpenCV videoio `VideoCaptureAPIs` enum sayilaridir (sabit, ABI):
#: CAP_DSHOW=700, CAP_MSMF=1400, CAP_V4L2=200.
ARKA_UC_API = {
    "auto": cv2.CAP_ANY,
    "dshow": getattr(cv2, "CAP_DSHOW", 700),
    "msmf": getattr(cv2, "CAP_MSMF", 1400),
    "v4l2": getattr(cv2, "CAP_V4L2", 200),
}
#: cap.set SIRASI: once cozunurluk, sonra FPS (DSHOW'da FPS, kip secildikten
#: sonra anlamlidir). Adlar /durum `kamera_ayari` anahtarlaridir.
KIP_OZELLIKLERI = (
    ("genislik", cv2.CAP_PROP_FRAME_WIDTH),
    ("yukseklik", cv2.CAP_PROP_FRAME_HEIGHT),
    ("fps", cv2.CAP_PROP_FPS),
)
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
#: Kamera surucusu bazen basarili ``read`` donerken ayni donmus tamponu tekrarlar.
#: Bayt-es JPEG, sensor gurultusu olan canli kamerada yeni kare kaniti DEGILDIR.
#: Icerik bu sure boyunca degismezse kaynak kopmus sayilir; ayni sure HTTP'nin
#: taze kare tavanidir, dolayisiyla iki ayri tazelik tanimi iraksamaz.
DONUK_KARE_AZAMI_S = AKIS_KARE_BEKLEME_S
#: Basarisiz acma denemelerinde her N. denemede bir KIRMIZI log (ilk deneme hep).
ACMA_LOG_SEYREKLIGI = 10
SINIR = "navitas-kare"              # multipart boundary
FPS_PENCERESI = 30                  # olculen fps icin son N kare zamani
VARSAYILAN_LOG_ARALIGI_S = 10.0     # periyodik sayac logu (0 = kapali)
#: Montaj duzeltmesi (21 Eyl 2026, saha): kare JPEG'e basilmadan HEMEN ONCE saat
#: yonunde dondurulur. 0 = dokunulmaz (eski davranis BAYT-ES). 90/270'te EN ve
#: BOY YER DEGISTIRIR (1280x720 -> 720x1280): tuketici olcegi FOV'dan genislikle
#: turetiyorsa (`mpp_irtifadan`) FOV'u YENI yatay eksene gore vermelidir.
DONDURME_SECENEKLERI = (0, 90, 180, 270)
_DONDURME_INDEKS = {}   # (derece, h, w) -> (satir, sutun); boyut basina BIR KEZ kurulur


def _dondurme_indeksi(derece, h, w):
    anahtar = (derece, h, w)
    ind = _DONDURME_INDEKS.get(anahtar)
    if ind is None:
        if derece == 90:        # cikis[i, j] = giris[h-1-j, i]
            satir = np.asarray(list(range(h - 1, -1, -1))).reshape(1, h)
            sutun = np.asarray(list(range(w))).reshape(w, 1)
        else:                   # 270: cikis[i, j] = giris[j, w-1-i]
            satir = np.asarray(list(range(h))).reshape(1, h)
            sutun = np.asarray(list(range(w - 1, -1, -1))).reshape(w, 1)
        ind = (satir, sutun)
        _DONDURME_INDEKS[anahtar] = ind
    return ind


def kare_dondur(kare, derece):
    """Kareyi saat yonunde `derece` kadar dondur. 0 -> AYNI nesne (kopya yok).

    Yalniz 3.6 beyaz listesindeki numpy kullanilir: `cv2.rotate` listede YOK
    (tests/test_faz_b_kamera_koprusu.py K5). Cikis her zaman bitisik (imencode).
    """
    if derece == 0:
        return kare
    if derece == 180:
        return np.ascontiguousarray(kare[::-1, ::-1])
    satir, sutun = _dondurme_indeksi(derece, kare.shape[0], kare.shape[1])
    return kare[satir, sutun]


def ekran_karesi(kare, hedef=EKRAN_BOYUT):
    """YALNIZ GORUNTULEME: en-boy KORUNARAK buyut, ORTADAN kirp -> `hedef` (w, h).

    Model hattina GIRMEZ: FOV, olcek (mpp), koordinat ve tespit bu kareyi GORMEZ.
    Tam FOV + bozulmamis oran + 16:9 doldurma ayni anda mumkun olmadigi icin
    kenarlar BILINCLI kirpilir (720x1280 kaynakta ortadaki 720x405 kalir).
    Once kirpip sonra olcekler (ayni sonuc, Jetson'da daha az is).
    """
    tw, th = hedef
    h, w = kare.shape[:2]
    olcek = max(tw / float(w), th / float(h))
    kw = min(w, int(round(tw / olcek)))
    kh = min(h, int(round(th / olcek)))
    x0 = (w - kw) // 2
    y0 = (h - kh) // 2
    pencere = kare[y0:y0 + kh, x0:x0 + kw]
    yontem = cv2.INTER_LINEAR if olcek > 1.0 else cv2.INTER_AREA
    return cv2.resize(pencere, (tw, th), interpolation=yontem)


def ekran_jpeg(veri, kalite=VARSAYILAN_KALITE, hedef=EKRAN_BOYUT):
    """Model hattinin JPEG'i -> ekran JPEG'i; cozulemez/kodlanamazsa None."""
    try:
        kare = cv2.imdecode(np.frombuffer(veri, np.uint8), cv2.IMREAD_COLOR)
        if kare is None:
            return None
        ok, tampon = cv2.imencode(".jpg", ekran_karesi(kare, hedef),
                                  [int(cv2.IMWRITE_JPEG_QUALITY), int(kalite)])
    except cv2.error:
        return None
    return tampon.tobytes() if ok else None


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


def kaynagi_coz(metin, arka_uc=ARKA_UC_OTOMATIK, **nvargus_ayar):
    """--kaynak metnini (VideoCapture argumani, apiPreference, tur) ucluye cevir.

    bos / "nvargus" -> nvarguscamerasrc borusu (CAP_GSTREAMER)
    "0", "2"        -> kamera indeksi (USB/UVC; apiPreference = arka_uc)
    "/dev/video1"   -> V4L2 aygit yolu (CIHAZ; apiPreference = arka_uc)
    "a ! b"         -> TAM GStreamer borusu (CAP_GSTREAMER)
    "http://…"      -> URL (FFmpeg)
    diger           -> dosya yolu

    `arka_uc` yalniz indeks/aygit kaynaginda anlamlidir; baska kaynakta "auto"
    disi deger ValueError'dur — sessizce yok sayilmaz (nvargus borusu
    CAP_GSTREAMER disinda bir arka uca verilemez).
    """
    if arka_uc not in ARKA_UC_API:
        raise ValueError("bilinmeyen arka uc {!r} (secenekler: {})".format(
            arka_uc, ", ".join(ARKA_UC_SECENEKLERI)))
    m = "" if metin is None else str(metin).strip()
    try:
        return int(m), ARKA_UC_API[arka_uc], KAYNAK_TURU_INDEKS
    except ValueError:
        pass
    if m.startswith(CIHAZ_YOLU_ONEKI) and m[len(CIHAZ_YOLU_ONEKI):].isdigit():
        return m, ARKA_UC_API[arka_uc], KAYNAK_TURU_CIHAZ
    if arka_uc != ARKA_UC_OTOMATIK:
        raise ValueError("--arka-uc {} yalniz indeks/aygit kaynaginda gecerli "
                         "(kaynak {!r})".format(arka_uc, m or KAYNAK_NVARGUS))
    if m == "" or m == KAYNAK_NVARGUS:
        return nvargus_boru(**nvargus_ayar), cv2.CAP_GSTREAMER, KAYNAK_TURU_NVARGUS
    if "!" in m:
        return m, cv2.CAP_GSTREAMER, KAYNAK_TURU_GSTREAMER
    if "://" in m:
        return m, cv2.CAP_ANY, KAYNAK_TURU_URL
    return m, cv2.CAP_ANY, KAYNAK_TURU_DOSYA


def video_url(port=VARSAYILAN_PORT, host=YEREL_HOST):
    """rpi_inference --kaynak icin verilecek URL (jetson_baslat.sh ile ayni)."""
    return "http://{}:{}{}".format(host, int(port), VIDEO_YOLU)


def _sayi_ya_da_none(deger):
    try:
        return round(float(deger), 3)
    except (TypeError, ValueError):
        return None


def cihaz_kipini_uygula(cap, istek):
    """Indeks/aygit kaynaginda istenen kipi ``cap.set`` ile uygula, raporla (T226).

    ``istek``: {"genislik", "yukseklik", "fps"} alanlarindan YALNIZ acikca
    verilenler. Donus (/durum ``kamera_ayari``):
      istenen   — istek aynen
      set_kabul — alan basina surucunun ``set`` donusu (bool)
      surucu    — ``get`` ile okunan deger: surucunun BILDIRIMI; gercek kare
                  boyutu ayrica /durum ``boyut``'tadir (ikisi ayrisabilir)
      hata      — surucu istisnasi; kaynak acik kalir, akis surucunun sectigi
                  kipte surer (fail-visible: /durum + KIRMIZI log)
    """
    rapor = {"istenen": dict(istek), "set_kabul": {}, "surucu": {}, "hata": None}
    try:
        for ad, ozellik in KIP_OZELLIKLERI:
            if istek.get(ad) is not None:
                rapor["set_kabul"][ad] = bool(cap.set(ozellik, float(istek[ad])))
        for ad, ozellik in KIP_OZELLIKLERI:
            rapor["surucu"][ad] = _sayi_ya_da_none(cap.get(ozellik))
    except Exception as exc:  # cv2.error ve surucu eklentisi istisnalari
        rapor["hata"] = "kip ayari istisnasi {}: {}".format(type(exc).__name__, exc)
    return rapor


def kip_sorunlari(rapor):
    """Kip raporundaki uyusmazliklar -> metin listesi (bos = istenen uygulandi)."""
    sorun = []
    if rapor.get("hata"):
        sorun.append(rapor["hata"])
    red = [ad for ad, _o in KIP_OZELLIKLERI if rapor["set_kabul"].get(ad) is False]
    if red:
        sorun.append("set REDDEDILDI: " + ", ".join(red))
    for ad in ("genislik", "yukseklik"):
        istenen = rapor["istenen"].get(ad)
        bildirilen = rapor["surucu"].get(ad)
        if istenen is not None and bildirilen is not None \
                and int(round(bildirilen)) != int(istenen):
            sorun.append("{} surucu {} != istenen {}".format(
                ad, int(round(bildirilen)), int(istenen)))
    return sorun


def _kip_metni(kip):
    return "{}x{}@{}".format(kip.get("genislik", "?"), kip.get("yukseklik", "?"),
                             kip.get("fps", "?"))


def _arka_uc_adi(cap):
    """Acilan arka ucun adi (DSHOW/MSMF/V4L2...); okunamazsa None."""
    try:
        return str(cap.getBackendName())
    except Exception:  # eski/sahte capture nesnesi ya da surucu istisnasi
        return None


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
                 saat=time.monotonic, log=logla, arka_uc=ARKA_UC_OTOMATIK, dondur=0,
                 **kip_ayari):
        super().__init__(name="kamera-uretici", daemon=True)
        if dondur not in DONDURME_SECENEKLERI:
            raise ValueError("dondur {!r} gecersiz; secenekler {}".format(
                dondur, DONDURME_SECENEKLERI))
        self.dondur = int(dondur)
        self.kaynak_metin = "" if kaynak_metin is None else str(kaynak_metin)
        # T226: None = "verilmedi" -> nvargus'ta boru varsayilani, indeks/aygitta
        # surucu varsayilani (cap.set CAGRILMAZ — eski davranis birebir).
        ayar = {ad: deger for ad, deger in kip_ayari.items() if deger is not None}
        self.arka_uc = arka_uc
        self.kaynak_arg, self.kaynak_api, self.kaynak_turu = kaynagi_coz(
            self.kaynak_metin, arka_uc=arka_uc, **ayar)
        self.kip_istegi = ({ad: ayar[ad] for ad, _o in KIP_OZELLIKLERI if ad in ayar}
                           if self.kaynak_turu in KIP_AYARLI_TURLER else {})
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
        # HTTP onbellegi kopusta temizlenir; bu imza ise kaynak nesilleri
        # arasinda korunur. Ayni donmus tampon yeniden acilista "taze" olamaz.
        self._son_icerik = None
        self._son_icerik_t = None
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
        self.donuk_kare = 0
        self.donuk_kare_ardisik = 0
        self.istemci_sayisi = 0
        self.kamera_ayari = None    # T226: son acilistaki kip raporu (degismez sozluk)
        self.arka_uc_adi = None     # T226: acilan arka ucun adi (indeks/aygit)
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

    def _cozunurluk_eslesti(self):
        """GERCEK kare boyutu istenen kiple ayni mi; kilit CAGIRANDA olmali.

        None: istenen cozunurluk yok ya da henuz kare yok (OLCULEMEDI, gecti degil).
        """
        w = self.kip_istegi.get("genislik")
        h = self.kip_istegi.get("yukseklik")
        if self.dondur in (90, 270):
            # istek KAMERA kipidir (dondurme oncesi); sunulan kare en/boy degistirir
            w, h = h, w
        if self.sekil is None or (w is None and h is None):
            return None
        return bool((w is None or self.sekil[1] == int(w)) and
                    (h is None or self.sekil[0] == int(h)))

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
                "donuk_kare": self.donuk_kare,
                "donuk_kare_ardisik": self.donuk_kare_ardisik,
                "fps": self.olculen_fps(),
                "fps_tavani": self.fps_tavani,
                "kalite": self.kalite,
                "boyut": [self.sekil[1], self.sekil[0]] if self.sekil else None,
                "dondur": self.dondur,
                "son_kare_yasi_s": (None if self.son_kare_t is None
                                    else round(simdi - self.son_kare_t, 3)),
                "son_hata": self.son_hata,
                "acma_denemesi": self.acma_denemesi,
                "acma_sayisi": self.acma_sayisi,
                "istemci_sayisi": self.istemci_sayisi,
                "calisma_s": round(simdi - self.baslangic_t, 3),
                # T226: indeks/aygit kaynaginda istenen kip, surucu bildirimi
                # ve gercek kare boyutuyla eslesme (boyut yukarida).
                "arka_uc": self.arka_uc,
                "arka_uc_adi": self.arka_uc_adi,
                "kip_istegi": dict(self.kip_istegi) or None,
                "kamera_ayari": (None if self.kamera_ayari is None else
                                 {ad: (dict(deger) if isinstance(deger, dict) else deger)
                                  for ad, deger in self.kamera_ayari.items()}),
                "cozunurluk_eslesti": self._cozunurluk_eslesti(),
            }

    # ── uretici tarafi ──────────────────────────────────────────────────
    def durdur(self):
        self._dur.set()
        with self.kosul:
            self.kosul.notify_all()

    def _onbellegi_temizle_kilitli(self):
        """Eski kaynaktan kare sizmasini engelle; cagirirken ``kosul`` kilitli olmali."""
        self.jpeg = None
        self.sekil = None
        self.son_kare_t = None
        self.donuk_kare_ardisik = 0
        self._zamanlar.clear()

    def _guvenli_birak(self, cap):
        if cap is None:
            return
        try:
            cap.release()
        except Exception as exc:  # Surucu kapanista da Python istisnasi uretebilir.
            self.log("kaynak birakilirken hata: {!r}".format(exc), kirmizi=True)

    @staticmethod
    def _oku(cap):
        """Surucu istisnasini uretici ipliginden kacirmadan olculebilir sonuca cevir."""
        try:
            ok, kare = cap.read()
            return bool(ok), kare, None
        except Exception as exc:  # cv2.error/OSError yaninda uretici eklentisi hatalari da gelir.
            return False, None, "kamera read istisnasi {}: {}".format(
                type(exc).__name__, exc)

    def _ac(self):
        """Kaynagi ac; basarisizsa None (KIRMIZI log seyrekligiyle).

        Sayac ve sonuc (son_hata / kaynak_acik) AYNI kilit bloğunda yazilir:
        /durum hicbir anda "deneme sayildi ama sonucu yok" gostermez.
        """
        # Her acma girisimi yeni bir kaynak neslidir. Onceki neslin JPEG'i,
        # boyutu ve tazelik zamani acma surerken dahi HTTP'den sunulamaz.
        with self.kosul:
            self.kaynak_acik = False
            self._onbellegi_temizle_kilitli()
            self.kosul.notify_all()
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
                self._guvenli_birak(cap)
            with self.kilit:
                self.acma_denemesi = deneme
                self.kaynak_acik = False
                self.son_hata = hata
            if deneme == 1 or deneme % ACMA_LOG_SEYREKLIGI == 0:
                self.log(hata + " — {} s sonra yeniden".format(YENIDEN_ACMA_ARALIGI_S),
                         kirmizi=True)
            return None
        # T226: kip YALNIZ indeks/aygitta ve yalniz acikca istendiyse uygulanir;
        # nvargus/URL/dosya yolu bu blogu atlar (davranis degismez).
        rapor = arka_uc_adi = None
        if self.kaynak_turu in KIP_AYARLI_TURLER:
            if self.kip_istegi:
                rapor = cihaz_kipini_uygula(cap, self.kip_istegi)
            arka_uc_adi = _arka_uc_adi(cap)
        with self.kilit:
            self.acma_denemesi = deneme
            self.kaynak_acik = True
            self.son_hata = None
            self.acma_sayisi += 1
            self.kamera_ayari = rapor
            self.arka_uc_adi = arka_uc_adi
        self.log("kaynak ACILDI (deneme {}): {!r} [{}]".format(
            deneme, self.kaynak_arg, self.kaynak_turu))
        if rapor is not None:
            sorun = kip_sorunlari(rapor)
            metin = "kamera kipi: istenen {} · surucu {} · arka uc {}".format(
                _kip_metni(rapor["istenen"]), _kip_metni(rapor["surucu"]),
                arka_uc_adi or self.arka_uc)
            if sorun:
                self.log(metin + " — istenen kip UYGULANMADI: " + "; ".join(sorun),
                         kirmizi=True)
            else:
                self.log(metin)
        return cap

    def _koptu(self, cap, neden):
        with self.kosul:
            self.kaynak_acik = False
            self.son_hata = neden
            self._onbellegi_temizle_kilitli()
            self.kosul.notify_all()
        self.log(neden + " — kaynak KAPATILDI, {} s sonra yeniden acilacak".format(
            YENIDEN_ACMA_ARALIGI_S), kirmizi=True)
        self._guvenli_birak(cap)

    def _kare_yayinla(self, kare):
        if not isinstance(kare, np.ndarray) or kare.ndim != 3 or kare.shape[2] != 3:
            return False, False
        kare = kare_dondur(kare, self.dondur)
        try:
            ok, tampon = cv2.imencode(".jpg", kare, [int(cv2.IMWRITE_JPEG_QUALITY), self.kalite])
        except cv2.error:
            ok, tampon = False, None
        if not ok or tampon is None:
            with self.kilit:
                self.kodlama_hatasi += 1
            return False, False
        veri = tampon.tobytes()             # degismez kopya: istemciler bunu alir
        simdi = self.saat()
        with self.kosul:
            if self._son_icerik == veri:
                # Basarili read tek basina canlilik kaniti degildir. Sirayi ve
                # son_kare_t'yi ilerletmeyerek HTTP tazeligini fail-closed tut.
                self.donuk_kare += 1
                self.donuk_kare_ardisik += 1
                dondu = (self._son_icerik_t is not None and
                         simdi - self._son_icerik_t >= DONUK_KARE_AZAMI_S)
                return False, dondu
            self._son_icerik = veri
            self._son_icerik_t = simdi
            self.jpeg = veri
            self.sira += 1
            self.sekil = (int(kare.shape[0]), int(kare.shape[1]))
            self.son_kare_t = simdi
            self.kare_sayaci += 1
            self.donuk_kare_ardisik = 0
            self._zamanlar.append(simdi)
            self.kosul.notify_all()
        return True, False

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
                ok, kare, okuma_hatasi = self._oku(cap)
                if okuma_hatasi is not None:
                    self._koptu(cap, okuma_hatasi)
                    cap = None
                    self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                    continue
                if (not ok or kare is None) and self.kaynak_turu == KAYNAK_TURU_DOSYA \
                        and okunan_bu_acilis > 0:
                    # Test/prova dosyasi bitti: basa sar (sessiz — ariza degil)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok, kare, okuma_hatasi = self._oku(cap)
                    if okuma_hatasi is not None:
                        self._koptu(cap, okuma_hatasi)
                        cap = None
                        self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                        continue
                    if not ok or kare is None:
                        self._guvenli_birak(cap)
                        try:
                            cap = cv2.VideoCapture(self.kaynak_arg, self.kaynak_api)
                            ok, kare, okuma_hatasi = (self._oku(cap) if cap.isOpened()
                                                     else (False, None, None))
                        except Exception as exc:
                            cap = None
                            ok, kare = False, None
                            okuma_hatasi = "dosya yeniden acma istisnasi {}: {}".format(
                                type(exc).__name__, exc)
                        if okuma_hatasi is not None:
                            self._koptu(cap, okuma_hatasi)
                            cap = None
                            self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                            continue
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
                _yayinlandi, dondu = self._kare_yayinla(kare)
                if dondu:
                    self._koptu(cap, "kamera goruntusu {:.1f} s degismedi (donuk kare)".format(
                        DONUK_KARE_AZAMI_S))
                    cap = None
                    self._dur.wait(YENIDEN_ACMA_ARALIGI_S)
                    continue
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
                self._guvenli_birak(cap)
            with self.kosul:
                self.kaynak_acik = False
                self._onbellegi_temizle_kilitli()
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
        d["ekran_url"] = _uc_url(yetki, EKRAN_YOLU)
        d["ekran_boyut"] = list(EKRAN_BOYUT)
        return d

    def do_GET(self):
        yol = self.path.split("?", 1)[0]
        if yol == VIDEO_YOLU:
            self._video()
        elif yol == KARE_YOLU:
            self._kare()
        elif yol == EKRAN_YOLU:
            self._ekran_video()
        elif yol == EKRAN_KARE_YOLU:
            self._ekran_kare()
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

    # ── YALNIZ GORUNTULEME hatti ────────────────────────────────────────
    # /video ve /kare.jpg'ye (model hatti) DOKUNMAZ; ayni JPEG'i okuyup kendi
    # ipliginde donusturur. Isleme maliyeti yalniz biri ekrani izlerken olusur.
    # Ekran istemcileri `istemci_sayisi`na SAYILMAZ (o sayac model tuketicisidir).
    def _ekran_kare(self):
        u = self.server.uretici
        veri, sira = u.kare_bekle(None, zaman_asimi_s=0.0, azami_yas_s=AKIS_KARE_BEKLEME_S)
        ekran = None if veri is None else ekran_jpeg(veri, u.kalite)
        if ekran is None:
            self._kaynak_yok()
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(ekran)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Kare-Sira", str(sira))
        self.end_headers()
        self.wfile.write(ekran)

    def _ekran_video(self):
        u = self.server.uretici
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
        try:
            while veri is not None:
                ekran = ekran_jpeg(veri, u.kalite)
                if ekran is not None:
                    baslik = ("--{}\r\nContent-Type: image/jpeg\r\n"
                              "Content-Length: {}\r\n\r\n").format(
                                  SINIR, len(ekran)).encode("ascii")
                    self.wfile.write(baslik)
                    self.wfile.write(ekran)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                veri, sira = u.kare_bekle(sira, AKIS_KARE_BEKLEME_S)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass                       # istemci kapatti


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
              istek_logu=False, log=logla, arka_uc=ARKA_UC_OTOMATIK, dondur=0,
              **kip_ayari):
    """Uretici ipligini baslat + HTTP sunucuyu BAGLA (serve_forever CAGIRMAZ).

    -> (sunucu, uretici). port=0: efemer (test). Kaynak yoksa da doner —
    uretici arka planda yeniden acma dongusundedir (fail-visible).
    `kip_ayari`: genislik/yukseklik/fps/sensor_id (None = verilmedi).
    """
    uretici = KareUretici(kaynak, kalite=kalite, fps_tavani=fps_tavani,
                          log_aralik_s=log_aralik_s, log=log, arka_uc=arka_uc,
                          dondur=dondur, **kip_ayari)
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
    # T226: varsayilan None = "verilmedi": nvargus borusu VARSAYILAN_* ile kurulur
    # (davranis degismez); indeks/aygitta cap.set yalniz verilince cagrilir.
    p.add_argument("--genislik", type=int, default=None,
                   help="kip genisligi: nvargus borusu (verilmezse {}) ya da indeks/aygit "
                        "kaynaginda cap.set (verilmezse surucu varsayilani)".format(
                            VARSAYILAN_GENISLIK))
    p.add_argument("--yukseklik", type=int, default=None,
                   help="kip yuksekligi: nvargus (verilmezse {}) ya da indeks/aygitta "
                        "cap.set".format(VARSAYILAN_YUKSEKLIK))
    p.add_argument("--kamera-fps", type=int, default=None,
                   help="kip fps: nvargus (verilmezse {}) ya da indeks/aygitta "
                        "cap.set".format(VARSAYILAN_KAMERA_FPS))
    p.add_argument("--sensor-id", type=int, default=VARSAYILAN_SENSOR_ID, help="nvargus sensor-id")
    p.add_argument("--arka-uc", choices=ARKA_UC_SECENEKLERI, default=ARKA_UC_OTOMATIK,
                   help="indeks/aygit kaynaginda VideoCapture apiPreference: auto=CAP_ANY, "
                        "dshow/msmf (Windows yakalama karti), v4l2 (Linux); baska "
                        "kaynakta yalniz auto")
    p.add_argument("--log-aralik", type=float, default=VARSAYILAN_LOG_ARALIGI_S,
                   help="periyodik sayac logu (s), 0 = kapali")
    p.add_argument("--istek-logu", action="store_true", help="her HTTP istegini logla")
    p.add_argument("--dondur", type=int, choices=DONDURME_SECENEKLERI, default=0,
                   help="kareyi SAAT YONUNDE dondur (derece; montaj duzeltmesi). "
                        "90/270'te en-boy yer degistirir: tuketicinin FOV'u yeni "
                        "yatay eksene gore verilmeli. Varsayilan 0 = dokunulmaz")
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
    if any(d is not None and d <= 0 for d in (args.genislik, args.yukseklik, args.kamera_fps)):
        parser.error("--genislik/--yukseklik/--kamera-fps pozitif olmali")
    try:
        kaynagi_coz(args.kaynak, arka_uc=args.arka_uc)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        sunucu, uretici = kopru_kur(
            args.kaynak, port=args.port, host=args.host, kalite=args.kalite,
            fps_tavani=args.fps, log_aralik_s=args.log_aralik, istek_logu=args.istek_logu,
            arka_uc=args.arka_uc, dondur=args.dondur,
            genislik=args.genislik, yukseklik=args.yukseklik, fps=args.kamera_fps,
            sensor_id=args.sensor_id)
    except OSError as exc:
        # Port doluysa SESSIZ beklemek yok: systemd 2 s sonra yeniden dener, journal gosterir
        logla("HATA: HTTP ucu acilamadi {}:{}: {}".format(args.host, args.port, exc), kirmizi=True)
        return 3
    port = sunucu.server_address[1]
    logla("dinliyor {} · kare {} · durum {} · kaynak={!r} [{}] kalite={} fps_tavani={} "
          "arka_uc={} kip={} dondur={}".format(
              video_url(port, args.host), "http://{}:{}{}".format(args.host, port, KARE_YOLU),
              "http://{}:{}{}".format(args.host, port, DURUM_YOLU),
              uretici.kaynak_metin or KAYNAK_NVARGUS, uretici.kaynak_turu, args.kalite,
              args.fps, args.arka_uc,
              _kip_metni(uretici.kip_istegi) if uretici.kip_istegi else "-", args.dondur))

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
