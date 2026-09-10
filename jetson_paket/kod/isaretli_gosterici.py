#!/usr/bin/env python3
"""NEDEN (T228 · REVIEW_LOG D-443 · results/fdr_sprint_20260910/H9_MK15/TASARIM.md §1, §2, §5):
Jetson'in isaretli karesini (T227 `rpi_inference --isaretli-yayin 127.0.0.1:8081`; sunucu
kamera_koprusu'nun HTTP sunucusudur -> AYNI uclar /kare.jpg, /video, /durum) SIYI MK15 video
hattina verir:
    Jetson DP -> DP->HDMI adaptor -> SIYI HDMI giris donusturucu (.25, H.264) -> Air Unit ->
    RF -> MK15 kumanda SIYI FPV "Camera 1" -> (kumanda HDMI aynasi) -> yakalama karti -> YKS.
Video GORSEL KANITTIR, KARAR URETMEZ: rota verisi ve hakem onayi SiK 433 MHz'te kalir
(CONTRACTS §6.7 degismez). Bu surec yoksa/cokerse veri hatti ve onay akisi ETKILENMEZ.

KIPLER (bosluk arastirmasi `mk15-bosluk`, 10 Eylul — TASARIM §5; kaynaklar GOSTERICI_KURULUM.md):
  x11  VARSAYILAN, birincil: varsayilan X11 masaustu + otomatik oturum + tam ekran cv2 penceresi
       (gdm KAPANMAZ). /kare.jpg ~5 Hz cekilir, ekran 10 Hz cizilir. DISPLAY yoksa cikis 2.
  drm  secenek: gst-launch-1.0 -v -e `souphttpsrc (/video) ! multipartdemux ! jpegdec ! identity
       name=nabiz silent=false ! nvvidconv ! video/x-raw(memory:NVMM) ! nvdrmvideosink set_mode=1`.
       Onkosul (root): gdm durur, seat0 kapanir, `modprobe nvidia-drm modeset=1`. KIRMIZI UYARI:
       DRM acilip gosterici CALISMAZSA Argus ~3 fps'e duser. kmssink KULLANILMAZ.
  rtsp YEDEK: donusturucu/DP yolu calismazsa yazilim x264 (Orin Nano'da NVENC YOK) 1280x720 @ 5 fps
       rtsp://<jetson_ip>:8554/isaretli (GstRtspServer; python3-gi + gir1.2-gst-rtsp-server-1.0).
       Jetson IP onerisi 192.168.144.30; SIYI sabitleri .11/.12/.20/.25 REDDEDILIR.
  --kuru  secilen kipin tam komutunu/ayarini yazar, HICBIR SEY ACMAZ (cikis 0).

FAIL-VISIBLE / FAIL-CLOSED — asla eski kareyi taze gibi gostermez:
  * son YENI karenin (X-Kare-Sira ya da icerik degisti) yasi > BAYAT_ESIGI_S (2 s) -> kare
    gri + karartilmis, ustte "BAYAT" bandi;
  * yas > GORUNTU_YOK_ESIGI_S (= kamera_koprusu.AKIS_KARE_BEKLEME_S), yayin erisilemiyor, HTTP
    503 ya da JPEG cozulemedi -> tam ekran KIRMIZI "GORUNTU YOK" + sebep; eski kare CIZILMEZ.
  * drm kipinde gozetmen /kare.jpg'yi yoklar; kare CANLI degilse video borusunu durdurup
    GORUNTU YOK borusunu acar (nvdrmvideosink son kareyi ekranda birakamaz).
  * T228-D (drm): /kare.jpg taze ama video borusunun identity nabzi (gst-launch -v)
    DRM_BORU_DONMA_S'den (3 s) uzun sure durursa da GORUNTU YOK (donmus boru). HISTEREZIS:
    CANLI'dan cikis ILK kotu yoklamada; donus 2 ARDISIK taze yoklama + son boru baslatmasindan
    >= 3 s (yeniden baslatma sikligi sinirli). -v satir bicimi Jetson'da OLCULEMEDI ->
    `--nabiz-sina` ile sahada DOGRULANACAK; eslesmezse drm kipi GORUNTU YOK'ta kalir (fail-closed).

OLCULEMEDI (Jetson bu makinede yok): x11/drm/rtsp'nin Jetson'da kosumu, DP->HDMI->donusturucu
EDID/HPD, camdan cama gecikme, Jetson CPU yuku, gst-launch -v nabiz satiri bicimi (PC'de gst
yok). PC'de olculen: boru dizgileri, durum mantigi, x11 penceresi (Windows), x11 dongusu (sahte
cv2), drm gozetmeni (sahte surec), nabiz ayristiricisi (sahte -v ciktisi), kuru kosum —
tests/test_isaretli_gosterici.py.

Yorumlayici: Jetson'da SISTEM Python'u (/usr/bin/python3: GUI'li python3-opencv, python3-gi).
venv'in opencv-python-headless'i pencere ACAMAZ. Yalniz stdlib + cv2 + numpy (+ rtsp'de gi).

Kullanim:
  /usr/bin/python3 scripts/isaretli_gosterici.py                      # x11, http://127.0.0.1:8081
  /usr/bin/python3 scripts/isaretli_gosterici.py --kip drm --kuru      # onkosul + borular
  /usr/bin/python3 scripts/isaretli_gosterici.py --kip rtsp --jetson-ip 192.168.144.30
  ... --sure 3 --tuval-kaydi <dizin>                                    # PC dumani / kanit
  stdbuf -oL gst-launch-1.0 -v videotestsrc is-live=true num-buffers=20 \
      ! video/x-raw,framerate=5/1 ! identity name=nabiz silent=false ! fakesink \
      | /usr/bin/python3 scripts/isaretli_gosterici.py --nabiz-sina    # -v bicim+zamanlama
"""
import argparse
import http.client
import ipaddress
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from collections import namedtuple

import cv2
import numpy as np

_BURASI = os.path.dirname(os.path.abspath(__file__))
if _BURASI not in sys.path:
    sys.path.insert(0, _BURASI)
# HTTP sozlesmesi TEK KAYNAK: T227 yayini kamera_koprusu'nun sunucusunu yeniden kullanir.
# Jetson'da ikisi de ~/navitas/scripts/ altindadir (JETSON_KILAVUZ §2), pakette kod/ altinda.
import kamera_koprusu as _kk  # noqa: E402

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


LOG_ONEKI = "[ISARETLI_GOSTERICI]"
KIP_X11 = "x11"
KIP_DRM = "drm"
KIP_RTSP = "rtsp"
KIPLER = (KIP_X11, KIP_DRM, KIP_RTSP)

#: T227 `rpi_inference --isaretli-yayin 127.0.0.1:8081` (TASARIM §1.1). jetson_baslat.sh
#: ISARETLI_YAYIN varsayilani ve .desktop dosyasi AYNI portu kullanir (test kilitler).
VARSAYILAN_KAYNAK = "http://127.0.0.1:8081"
KARE_YOLU = _kk.KARE_YOLU
VIDEO_YOLU = _kk.VIDEO_YOLU
#: /kare.jpg cekme sikligi (gorev tanimi ~5 Hz). T227 yayini <= 2 Hz uretir; 5 Hz yeni kareyi
#: en gec 200 ms'de gorur. Ekran AYRI iplikte (ana dongu) cizilir ki cekme istegi takilsa da
#: BAYAT bandi zamaninda ciksin. 5 Hz: PC dumaninda 10 Hz cizim tek cekirdegin %8-22'sini
#: yiyordu (t228/duman_ciktisi.txt); 200 ms gecikme 2 s esiginin yaninda ihmal edilir.
CEKME_HZ = 5.0
CIZIM_HZ = 5.0
ISTEK_ZAMAN_ASIMI_S = 1.0
#: ON KAYIT (gorev tanimi): kare yasi > 2 s -> BAYAT bandi. Gevsetilmez.
BAYAT_ESIGI_S = 2.0
#: Koprunun taze kare tavani ile AYNI: /kare.jpg bundan yasli kareyi zaten 503'le reddeder.
#: Yerelde de bu yastan sonra eski kare hic cizilmez.
GORUNTU_YOK_ESIGI_S = float(_kk.AKIS_KARE_BEKLEME_S)
#: TASARIM §1.1: yayin 1280x720 16:9; donusturucu 1080p30'a kadar kodlar.
TUVAL_GENISLIK = 1280
TUVAL_YUKSEKLIK = 720
PENCERE_ADI = "NAVITAS isaretli gosterici"
BAYAT_KARARTMA = 0.35
#: Renkler (BGR)
KIRMIZI_ZEMIN = (0, 0, 190)
AMBER = (0, 190, 255)
BEYAZ = (255, 255, 255)
SIYAH = (0, 0, 0)
YESIL = (0, 210, 0)
YAZI = cv2.FONT_HERSHEY_SIMPLEX

#: Yedek RTSP (TASARIM §1 "Yedek video yolu"): 1280x720 5 fps x264.
RTSP_PORT = 8554
RTSP_YOL = "/isaretli"
RTSP_FPS = 5
X264_BITRATE_KBPS = 2000
X264_KEY_INT_MAX = 10
RTSP_APPSRC_ADI = "gosterici_tuvali"
RTSP_BORU_TUVAL = "tuval"      # gostericinin cizdigi ekran (BAYAT / GORUNTU YOK dahil) -> appsrc
RTSP_BORU_HTTP = "http"        # ham /video -> souphttpsrc (bayat/yok ekrani YOK)
JETSON_IP_ONERI = "192.168.144.30"
SIYI_ALT_AG = ipaddress.IPv4Network("192.168.144.0/24")
#: SIYI sabit adresleri (MK15 kilavuzu v1.9: .11/.12/.20 degismez; HDMI giris donusturucu
#: kilavuzu v1.1: varsayilan .25). Jetson bunlardan birini alirsa hat sessizce cakisir.
SIYI_SABIT_IP = {
    "192.168.144.11": "hava birimi (Air Unit)",
    "192.168.144.12": "yer birimi (kumanda)",
    "192.168.144.20": "kumanda Android",
    "192.168.144.25": "HDMI giris donusturucu",
}

#: DRM onkosulu (NVIDIA belgeli nvdrmvideosink yolu; JetPack 7.2'de nvidia-drm varsayilan
#: denylist'te — nv-load-display-modules servisi). Root ister; gdm DURUR.
DRM_ON_KOSUL = (
    "sudo systemctl stop gdm",
    "sudo loginctl terminate-seat seat0",
    "sudo modprobe nvidia-drm modeset=1",
)
DRM_YOKLAMA_S = 1.0
DRM_ASGARI_OMUR_S = 2.0
#: T228-D HISTEREZIS: GORUNTU YOK'tan video borusuna donus icin gereken ARDISIK taze (CANLI)
#: yoklama sayisi. CANLI'dan cikis ise ILK bayat/hata/donmus yoklamada (guvenli taraf).
DRM_CANLI_ARDISIK = 2
#: T228-D: iki boru baslatmasi arasi asgari sure (CANLI'dan cikis ve olen video borusu HARIC).
#: nvdrmvideosink her acilista kip kurar (set_mode=1); cirpinan yayin ekrani surekli yeniden
#: acmasin. Gorev tanimi "ornegin 3 s".
DRM_ASGARI_ARALIK_S = 3.0
#: T228-D BORU ILERLEMESI: video borusuna `identity name=nabiz silent=false` + gst-launch -v;
#: son ilerleyen tampondan (hic yoksa acilistan) bu yana > esik -> boru DONMUS, GORUNTU YOK.
NABIZ_ADI = "nabiz"
DRM_BORU_DONMA_S = 3.0
#: -v ciktisinin nabiz OLMAYAN ilk bu kadar satiri 'gst: ' onekiyle loglanir (gercek bicim
#: journal'dan okunabilsin — Jetson'da OLCULEMEDI).
NABIZ_GST_LOG_SINIRI = 40
#: --nabiz-sina ZAMANLAMA denetimi: pts yayilimi en az bu kadarsa denetlenir; nabiz satirlarinin
#: varis yayilimi pts yayiliminin bu oranindan kucukse satirlar TOPLU (tamponlu) gelmistir.
NABIZ_SINA_ASGARI_PTS_S = 1.0
NABIZ_SINA_VARIS_ORANI = 0.5
ARGUS_UYARISI = (
    "nvidia-drm yuklenip nvdrmvideosink CALISMAZSA Argus (nvarguscamerasrc) ~3 fps'e duser — "
    "DRM kipi ya surekli calisir ya da hic acilmaz; kamera FPS'i DRM acikken olculmeli "
    "(mk15-bosluk arastirmasi, 10 Eylul)")
DRM_BAYAT_NOTU = (
    "drm kipinde kareye BAYAT bandi CIZILMEZ (boru /video'yu dogrudan gosterir); gozetmen "
    "/kare.jpg'yi {:g} s'de bir yoklar, kare {:g} s'den uzun sure yeni degilse, yayin "
    "erisilemezse ya da video borusunun identity nabzi {:g} s'den uzun sure durursa video "
    "borusunu durdurup GORUNTU YOK borusuna gecer (eski kare ekranda birakilmaz); video "
    "borusuna donus {} ARDISIK taze yoklama + son baslatmadan >= {:g} s ister").format(
        DRM_YOKLAMA_S, BAYAT_ESIGI_S, DRM_BORU_DONMA_S, DRM_CANLI_ARDISIK, DRM_ASGARI_ARALIK_S)
DRM_NABIZ_NOTU = (
    "gst-launch-1.0 -v nabiz satiri bicimi ve zamanlamasi Jetson'da OLCULEMEDI — DOGRULANACAK "
    "(GOSTERICI_KURULUM §5): `stdbuf -oL gst-launch-1.0 -v videotestsrc is-live=true "
    "num-buffers=20 ! video/x-raw,framerate=5/1 ! identity name={} silent=false ! fakesink | "
    "/usr/bin/python3 ~/navitas/scripts/isaretli_gosterici.py --nabiz-sina` cikis 0 (ESLESTI, "
    "ZAMANINDA) olmali; ESLESMEDI/TOPLU ise video borusu {:g} s'de bir GORUNTU YOK'a duser "
    "(fail-closed)").format(NABIZ_ADI, DRM_BORU_DONMA_S)
DRM_KURULUM_NOTU = (
    "sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-base "
    "(souphttpsrc, multipartdemux, jpegdec, textoverlay); nvvidconv/nvdrmvideosink JetPack "
    "(nvidia-l4t-gstreamer)")
RTSP_KURULUM_NOTU = (
    "sudo apt install python3-gi gir1.2-gst-rtsp-server-1.0 gstreamer1.0-plugins-good "
    "gstreamer1.0-plugins-ugly (x264enc) — SISTEM Python'u ile kos (/usr/bin/python3, venv DEGIL)")

CIKIS_TAMAM = 0
CIKIS_ORTAM = 2          # DISPLAY yok / GUI'siz OpenCV / RTSP adresi baglanamadi (argparse de 2)
CIKIS_BAGIMLILIK = 3     # gst-launch-1.0 ya da gi/GstRtspServer/eleman yok
CIKIS_NABIZ_YOK = 1      # --nabiz-sina: stdin'de hic nabiz satiri ayristirilamadi

DURUM_CANLI = "CANLI"
DURUM_BAYAT = "BAYAT"
DURUM_YOK = "GORUNTU_YOK"

EkranDurumu = namedtuple("EkranDurumu", "durum sebep yas_s")


def logla(metin, kirmizi=False, saat=time.monotonic):
    seviye = "KIRMIZI " if kirmizi else ""
    print("{} t={:.3f} {}{}".format(LOG_ONEKI, saat(), seviye, metin),
          file=sys.stderr if kirmizi else sys.stdout, flush=True)


_TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ—–", "cgiosuCGIOSUaiuAIU--")


def ascii_metin(metin):
    """cv2.putText (Hershey) yalniz ASCII cizer: Turkce harfleri sadelestir, kalani '?'."""
    m = str(metin).translate(_TR_ASCII)
    return "".join(c if 32 <= ord(c) < 127 else "?" for c in m)


# ── saf durum karari ──────────────────────────────────────────────────────────
def ekran_durumu(simdi, son_taze_t, hata=None, bayat_esigi_s=BAYAT_ESIGI_S,
                 yok_esigi_s=GORUNTU_YOK_ESIGI_S):
    """Son YENI karenin zamani + son cekme hatasi -> EkranDurumu (saf fonksiyon).

    Oncelik: hata > hic kare yok > yas > yok esigi > yas > bayat esigi > CANLI.
    Sinirda (yas == esik) bir onceki durum kalir: esikler KESIN buyuktur.
    """
    yas = None if son_taze_t is None else max(0.0, float(simdi) - float(son_taze_t))
    if hata:
        return EkranDurumu(DURUM_YOK, str(hata), yas)
    if yas is None:
        return EkranDurumu(DURUM_YOK, "henuz kare alinmadi", None)
    if yas > yok_esigi_s:
        return EkranDurumu(DURUM_YOK, "son taze kare {:.1f} s once (> {:g} s)".format(
            _yukari_ondalik(yas), yok_esigi_s), yas)
    if yas > bayat_esigi_s:
        return EkranDurumu(DURUM_BAYAT, "kare {:.1f} s eski (> {:g} s)".format(
            _yukari_ondalik(yas), bayat_esigi_s), yas)
    return EkranDurumu(DURUM_CANLI, "", yas)


def _yukari_ondalik(deger):
    """0,1'e YUKARI yuvarla: esigi asan yas ekranda esikten kucuk/esit okunmasin
    (PC dumani: 2,04 s '2.0 s eski (> 2 s)' yaziliyordu)."""
    return -(-(float(deger) * 10.0 - 1e-9) // 1) / 10.0


def kaynak_kok(metin):
    """'http://127.0.0.1:8081' (sonda '/' olabilir) -> kok URL. Yol/sorgu -> ValueError:
    gosterici /kare.jpg ve /video'yu KENDISI ekler (kamera_koprusu uclari)."""
    m = str(metin).strip().rstrip("/")
    try:
        p = urllib.parse.urlsplit(m)
        _port = p.port
    except ValueError as exc:
        raise ValueError("--kaynak gecersiz: {!r} ({})".format(metin, exc))
    if p.scheme != "http" or not p.hostname or p.path or p.query or p.fragment:
        raise ValueError("--kaynak http://<host>:<port> olmali (yol YOK; gosterici {} ve {} "
                         "ekler): {!r}".format(KARE_YOLU, VIDEO_YOLU, metin))
    return m


def jetson_ip_dogrula(metin):
    """RTSP yayin adresi -> (ip, uyarilar). SIYI sabitleri ve anlamsiz adresler ValueError."""
    ham = "" if metin is None else str(metin).strip()
    try:
        ip = ipaddress.IPv4Address(ham)
    except ValueError:
        raise ValueError("--jetson-ip gecerli IPv4 degil: {!r} (oneri {})".format(
            ham, JETSON_IP_ONERI))
    s = str(ip)
    if s in SIYI_SABIT_IP:
        raise ValueError(
            "--jetson-ip {} YASAK: SIYI {} adresi (sabitler .11 hava / .12 yer / .20 Android / "
            ".25 HDMI donusturucu); oneri {}".format(s, SIYI_SABIT_IP[s], JETSON_IP_ONERI))
    if ip.is_unspecified or ip.is_multicast or s == "255.255.255.255":
        raise ValueError("--jetson-ip {}: bir arayuz adresi olmali (RTSP URL'si bu adresi "
                         "ilan eder)".format(s))
    uyarilar = []
    if ip in SIYI_ALT_AG:
        if ip in (SIYI_ALT_AG.network_address, SIYI_ALT_AG.broadcast_address):
            raise ValueError("--jetson-ip {}: ag/yayin adresi".format(s))
    else:
        uyarilar.append(
            "--jetson-ip {} SIYI alt aginda ({}) DEGIL — hava birimi RTSP'yi yalniz "
            "192.168.144.X'ten ceker; yalniz masa testi".format(s, SIYI_ALT_AG))
    return s, uyarilar


# ── tuval cizimi ──────────────────────────────────────────────────────────────
def sigdir(kare, genislik=TUVAL_GENISLIK, yukseklik=TUVAL_YUKSEKLIK):
    """Kareyi en-boy korunarak (siyah bantla) genislik x yukseklik tuvale yerlestir."""
    tuval = np.zeros((yukseklik, genislik, 3), np.uint8)
    if kare is None or getattr(kare, "size", 0) == 0:
        return tuval
    if kare.ndim == 2:
        kare = cv2.cvtColor(kare, cv2.COLOR_GRAY2BGR)
    h, w = kare.shape[:2]
    olcek = min(genislik / float(w), yukseklik / float(h))
    yw, yh = max(1, int(round(w * olcek))), max(1, int(round(h * olcek)))
    kucuk = kare if (yw, yh) == (w, h) else cv2.resize(
        kare, (yw, yh), interpolation=cv2.INTER_AREA if olcek < 1 else cv2.INTER_LINEAR)
    x0, y0 = (genislik - yw) // 2, (yukseklik - yh) // 2
    tuval[y0:y0 + yh, x0:x0 + yw] = kucuk
    return tuval


def _yazi(tuval, metin, merkez_y, olcek, kalinlik, renk):
    """Yatayda ortali ASCII yazi; tuvale sigmazsa olcek kuculur (tasma yok)."""
    m = ascii_metin(metin)
    azami = tuval.shape[1] - 40
    (tw, th), _ = cv2.getTextSize(m, YAZI, olcek, kalinlik)
    if tw > azami:
        oran = azami / float(tw)
        olcek *= oran
        kalinlik = max(1, int(round(kalinlik * oran)))
        (tw, th), _ = cv2.getTextSize(m, YAZI, olcek, kalinlik)
    x = max(0, (tuval.shape[1] - tw) // 2)
    cv2.putText(tuval, m, (x, int(merkez_y + th // 2)), YAZI, olcek, renk, kalinlik, cv2.LINE_AA)


def _satirlara_bol(metin, azami=56, en_cok=4):
    satirlar, simdiki = [], ""
    for k in ascii_metin(metin).split():
        aday = (simdiki + " " + k).strip()
        if len(aday) > azami and simdiki:
            satirlar.append(simdiki)
            simdiki = k
        else:
            simdiki = aday
    if simdiki:
        satirlar.append(simdiki)
    return satirlar[:en_cok] or [""]


def tuval_ciz(durum, kare=None, saat_metni=None, genislik=TUVAL_GENISLIK,
              yukseklik=TUVAL_YUKSEKLIK):
    """EkranDurumu + son kare -> gosterilecek BGR tuval (genislik x yukseklik).

    GORUNTU_YOK'ta (ve kare yokken her durumda) eski kare ASLA cizilmez; BAYAT'ta kare gri +
    karartilmis ve ustte bant tasir — taze kareyle karistirilamaz.
    """
    if durum.durum == DURUM_CANLI and kare is not None:
        tuval = sigdir(kare, genislik, yukseklik)
        etiket = "CANLI {:.1f} s".format(durum.yas_s or 0.0)
        (tw, th), _ = cv2.getTextSize(etiket, YAZI, 0.6, 1)
        cv2.rectangle(tuval, (genislik - tw - 22, yukseklik - th - 22),
                      (genislik - 6, yukseklik - 6), SIYAH, -1)
        cv2.putText(tuval, etiket, (genislik - tw - 14, yukseklik - 14), YAZI, 0.6, YESIL, 1,
                    cv2.LINE_AA)
        return tuval
    if durum.durum == DURUM_BAYAT and kare is not None:
        tuval = sigdir(kare, genislik, yukseklik)
        gri = cv2.cvtColor(cv2.cvtColor(tuval, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
        tuval = (gri.astype(np.float32) * BAYAT_KARARTMA).astype(np.uint8)
        bant = yukseklik // 5
        tuval[:bant] = AMBER
        _yazi(tuval, "BAYAT - " + durum.sebep, bant // 2, 1.6, 3, SIYAH)
        return tuval
    tuval = np.empty((yukseklik, genislik, 3), np.uint8)
    tuval[:] = KIRMIZI_ZEMIN
    _yazi(tuval, "GORUNTU YOK", yukseklik // 3, 4.0, 10, BEYAZ)
    sebep = durum.sebep if durum.durum == DURUM_YOK else "kare yok"
    for i, satir in enumerate(_satirlara_bol(sebep)):
        _yazi(tuval, satir, yukseklik // 2 + 40 + i * 56, 1.3, 2, BEYAZ)
    alt = "NAVITAS isaretli gosterici - karar uretmez"
    if saat_metni:
        alt += " - " + saat_metni
    _yazi(tuval, alt, yukseklik - 40, 0.8, 1, BEYAZ)
    return tuval


# ── kare cekici (HTTP istemcisi) ──────────────────────────────────────────────
def http_hata_sebebi(kod, govde):
    """HTTP hata kodu + kopru JSON govdesi -> okunur sebep (son_hata > hata)."""
    ayrinti = ""
    try:
        d = json.loads(govde.decode("utf-8"))
        ayrinti = d.get("son_hata") or d.get("hata") or ""
    except (ValueError, AttributeError, UnicodeDecodeError):
        pass
    return "yayin HTTP {}{}".format(kod, ": {}".format(ayrinti) if ayrinti else "")


class KareCekici(threading.Thread):
    """/kare.jpg'yi ~hz ile ceker; son YENI kareyi ve zamanini, son hatayi tutar.

    Yeni kare = (X-Kare-Sira, crc32(govde)) imzasi degisti. Ayni imza tazelik UZATMAZ
    (kamera_koprusu donuk kare kalibi). Hata her basarili cekmede temizlenir. Proxy
    ortam degiskenleri KULLANILMAZ (127.0.0.1 bir vekile gitmesin).
    """

    def __init__(self, kaynak=VARSAYILAN_KAYNAK, hz=CEKME_HZ,
                 zaman_asimi_s=ISTEK_ZAMAN_ASIMI_S, saat=time.monotonic, log=logla):
        super().__init__(name="isaretli-cekici", daemon=True)
        self.kare_url = kaynak_kok(kaynak) + KARE_YOLU
        self.hz = float(hz)
        self.zaman_asimi_s = float(zaman_asimi_s)
        self.saat = saat
        self.log = log
        self._acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.kilit = threading.Lock()
        self._dur = threading.Event()
        self.kare = None
        self.son_taze_t = None
        self.hata = None
        self.sira = None
        self._imza = None
        self.istek = 0
        self.basari = 0
        self.yeni_kare = 0
        self.hata_sayisi = 0

    def anlik(self):
        """(kare, son_taze_t, hata, sira) — kilit altinda tutarli anlik goruntu."""
        with self.kilit:
            return self.kare, self.son_taze_t, self.hata, self.sira

    def _hata(self, neden):
        with self.kilit:
            onceki = self.hata
            self.hata = neden
            self.hata_sayisi += 1
        if onceki != neden:
            self.log(neden, kirmizi=True)
        return False

    def cek_bir_kez(self):
        """Tek GET /kare.jpg. Donus: YENI kare geldi mi."""
        with self.kilit:
            self.istek += 1
        try:
            with self._acici.open(self.kare_url, timeout=self.zaman_asimi_s) as yanit:
                govde = yanit.read()
                sira = yanit.headers.get("X-Kare-Sira")
        except urllib.error.HTTPError as exc:
            try:
                ek = exc.read()
            except (OSError, http.client.HTTPException):
                ek = b""
            return self._hata(http_hata_sebebi(exc.code, ek))
        except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError) as exc:
            neden = getattr(exc, "reason", None) or exc
            return self._hata("yayin erisilemiyor ({}): {}".format(self.kare_url, neden))
        imza = (sira, zlib.crc32(govde))
        with self.kilit:
            ayni = imza == self._imza
        if ayni:
            # Ayni bayt: cozmeye gerek yok, tazelik UZAMAZ; ama yayin ayakta -> hata temizlenir.
            with self.kilit:
                onceki_hata, self.hata = self.hata, None
                self.basari += 1
            if onceki_hata is not None:
                self.log("yayin yanit veriyor (kare yeni degil): {}".format(self.kare_url))
            return False
        kare = cv2.imdecode(np.frombuffer(govde, np.uint8), cv2.IMREAD_COLOR) if govde else None
        if kare is None:
            return self._hata("JPEG cozulemedi ({} bayt, {})".format(len(govde), self.kare_url))
        simdi = self.saat()
        with self.kilit:
            onceki_hata, self.hata = self.hata, None
            self.basari += 1
            self.yeni_kare += 1
            self._imza = imza
            self.kare = kare
            self.son_taze_t = simdi
            self.sira = sira
        if onceki_hata is not None:
            self.log("yayin geri geldi: {} (sira {})".format(self.kare_url, sira))
        return True

    def run(self):
        aralik = 1.0 / self.hz if self.hz > 0 else 1.0 / CEKME_HZ
        while not self._dur.is_set():
            t0 = time.monotonic()
            try:
                self.cek_bir_kez()
            except Exception as exc:   # iplik OLMEZ: beklenmeyen hata da GORUNTU YOK olur
                self._hata("cekici istisnasi {}: {}".format(type(exc).__name__, exc))
            self._dur.wait(max(0.0, aralik - (time.monotonic() - t0)))

    def durdur(self):
        self._dur.set()

    def sayaclar(self):
        with self.kilit:
            return {"istek": self.istek, "basari": self.basari, "yeni_kare": self.yeni_kare,
                    "hata": self.hata_sayisi}


# ── x11 kipi ──────────────────────────────────────────────────────────────────
def ekran_ortami_hatasi(ortam=None, platform=None):
    """x11 kipi icin grafik oturum var mi? None = tamam, aksi halde acik hata metni.

    Linux disinda (Windows PC dumani) pencere sistemi DISPLAY'e bagli degildir.
    """
    ortam = os.environ if ortam is None else ortam
    platform = sys.platform if platform is None else platform
    if not str(platform).startswith("linux"):
        return None
    if ortam.get("DISPLAY"):
        return None
    ek = ""
    if ortam.get("WAYLAND_DISPLAY"):
        ek = " (WAYLAND_DISPLAY var ama DISPLAY yok: GDM'de Xorg oturumu — WaylandEnable=false)"
    return ("DISPLAY yok — x11 kipi grafik oturum ister: otomatik oturum + autostart "
            "(gosterici/GOSTERICI_KURULUM.md), ssh'ten DISPLAY=:0; ekransiz: --kip drm / "
            "--kip rtsp" + ek)


def ekran_koruyucuyu_kapat(platform=None, calistir=subprocess.run):
    """X11 ekran koruyucu / DPMS kapat (en iyi caba; basarisizlik UYARI, cikis degil)."""
    platform = sys.platform if platform is None else platform
    if not str(platform).startswith("linux"):
        return
    if shutil.which("xset") is None:
        logla("[UYARI] xset yok — ekran koruyucu/DPMS acik kalabilir (GOSTERICI_KURULUM.md: "
              "gsettings idle-delay 0)", kirmizi=True)
        return
    for argv in (["xset", "s", "off"], ["xset", "s", "noblank"], ["xset", "-dpms"]):
        try:
            calistir(argv, timeout=5, check=False, capture_output=True)
        except (OSError, subprocess.SubprocessError) as exc:
            logla("[UYARI] {} basarisiz: {}".format(" ".join(argv), exc), kirmizi=True)
            return


class TuvalKaydi:
    """--tuval-kaydi: durum degisiminde ve cikista tuvali JPEG yaz (kanit / PC dumani)."""

    def __init__(self, dizin):
        self.dizin = dizin
        self.n = 0
        if dizin:
            os.makedirs(dizin, exist_ok=True)

    def _yaz(self, ad, tuval):
        if not self.dizin or tuval is None:
            return
        yol = os.path.join(self.dizin, ad)
        if cv2.imwrite(yol, tuval, [int(cv2.IMWRITE_JPEG_QUALITY), 85]):
            logla("tuval kaydi: {}".format(yol))
        else:
            logla("tuval kaydi YAZILAMADI: {}".format(yol), kirmizi=True)

    def durum_degisti(self, durum, tuval):
        self.n += 1
        self._yaz("{:02d}_{}.jpg".format(self.n, durum), tuval)

    def son(self, tuval):
        self._yaz("son.jpg", tuval)


def _sinyal_kur(dur):
    try:
        return signal.signal(signal.SIGTERM, lambda _s, _f: dur.set())
    except (ValueError, OSError, AttributeError):   # ana iplik degil / platform
        return None


def _sinyal_geri(eski):
    if eski is None:
        return
    try:
        signal.signal(signal.SIGTERM, eski)
    except (ValueError, OSError, AttributeError):
        pass


def _durum_logu(onceki, d, onek="ekran", log=None):
    (log or logla)("{} {} -> {}{}".format(onek, onceki or "-", d.durum,
                                          " ({})".format(d.sebep) if d.sebep else ""),
                   kirmizi=d.durum == DURUM_YOK)


def x11_kos(args, ortam=None, platform=None, saat=time.monotonic, cv=cv2,
            cekici_uret=KareCekici):
    """x11 kipi: tam ekran pencere dongusu.

    T228-D: `cv` (namedWindow/setWindowProperty/imshow/waitKey/destroyAllWindows/error + pencere
    sabitleri) ve `cekici_uret(kaynak, hz=...)` (KareCekici arayuzu: start/anlik/durdur/join/
    sayaclar/kare_url) TEST icin enjekte edilebilir — dongudeki ekran_durumu cagrisi sahte cv2 ile
    kilitlenir. Varsayilanlarla davranis T228 ile AYNIDIR.
    """
    hata = ekran_ortami_hatasi(ortam, platform)
    if hata:
        logla("HATA: " + hata, kirmizi=True)
        return CIKIS_ORTAM
    try:
        cv.namedWindow(PENCERE_ADI, cv.WINDOW_NORMAL)
        cv.setWindowProperty(PENCERE_ADI, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
    except cv.error as exc:
        logla("HATA: cv2 penceresi acilamadi ({}) — GUI'siz OpenCV (opencv-python-headless / "
              "venv)? SISTEM Python'u + python3-opencv kullan".format(exc), kirmizi=True)
        return CIKIS_ORTAM
    ekran_koruyucuyu_kapat(platform)
    cekici = cekici_uret(args.kaynak, hz=args.hz)
    kayit = TuvalKaydi(args.tuval_kaydi)
    dur = threading.Event()
    eski_sinyal = _sinyal_kur(dur)
    logla("basladi: kip=x11 kaynak={} cekme={:g} Hz bayat>{:g} s goruntu_yok>{:g} s{}".format(
        cekici.kare_url, args.hz, BAYAT_ESIGI_S, GORUNTU_YOK_ESIGI_S,
        " sure={:g} s".format(args.sure) if args.sure else ""))
    cekici.start()
    t0 = saat()
    cpu0 = time.process_time()
    bitis = t0 + args.sure if args.sure else None
    onceki = None
    cizim = 0
    tuval = None
    try:
        while not dur.is_set():
            kare, son_t, cekme_hatasi, _sira = cekici.anlik()
            d = ekran_durumu(saat(), son_t, cekme_hatasi)
            tuval = tuval_ciz(d, kare, saat_metni=time.strftime("%H:%M:%S"))
            if d.durum != onceki:
                _durum_logu(onceki, d)
                kayit.durum_degisti(d.durum, tuval)
                onceki = d.durum
            cv.imshow(PENCERE_ADI, tuval)
            cizim += 1
            tus = cv.waitKey(max(1, int(1000.0 / CIZIM_HZ))) & 0xFF
            if tus in (27, ord("q")):
                logla("klavyeden cikis")
                break
            if bitis is not None and saat() >= bitis:
                break
    finally:
        cekici.durdur()
        cekici.join(2.0)
        try:
            cv.destroyAllWindows()
        except cv.error:
            pass
        kayit.son(tuval)
        _sinyal_geri(eski_sinyal)
        sure = max(1e-6, saat() - t0)
        cpu = time.process_time() - cpu0
        s = cekici.sayaclar()
        logla("ozet: kip=x11 sure={:.1f} s cizim={} istek={} basari={} yeni_kare={} hata={} "
              "cpu={:.2f} s (tek cekirdegin %{:.0f}'i)".format(
                  sure, cizim, s["istek"], s["basari"], s["yeni_kare"], s["hata"], cpu,
                  100.0 * cpu / sure))
    return CIKIS_TAMAM


# ── drm kipi ──────────────────────────────────────────────────────────────────
#: drm_gozetmen boru turleri (log metinleri de bunlardir)
BORU_VIDEO = "video"
BORU_YOK = "GORUNTU YOK"

#: drm_boru_karari donusu: boru = ekranda olmasi gereken boru (None: hic boru yok, bekle);
#: baslat = simdi yeni surec acilsin (calisan varsa once durdurulur); guvenlik = baslatma
#: sikligina TAKILMAYAN cikis (CANLI'dan cikis / olen video borusu).
DrmKarar = namedtuple("DrmKarar", "boru baslat guvenlik")


def _drm_sink(conn_id=None):
    return "nvdrmvideosink set_mode=1 sync=false" + (
        " conn_id={}".format(int(conn_id)) if conn_id is not None else "")


def drm_boru(kaynak=VARSAYILAN_KAYNAK, genislik=TUVAL_GENISLIK, yukseklik=TUVAL_YUKSEKLIK,
             conn_id=None):
    """DRM video borusu: /video MJPEG -> jpegdec -> identity (nabiz) -> NVMM -> nvdrmvideosink.

    T228-D: `identity name=nabiz silent=false` her tamponda last-message yayar; `gst-launch-1.0
    -v` bunu stdout'a basar -> gozetmen borunun ILERLEDIGINI izler (NabizIzleyici). identity
    jpegdec'ten SONRA, sistem belleginde durur (NVMM caps'li identity Jetson'da OLCULEMEDI). Boruda
    kuyruk yok: souphttpsrc'nin akis ipligi sink'e kadar TEK iplik — sink takilirsa identity de
    yeni tampon gecirmez, nabiz durur.
    """
    return ("souphttpsrc location={} is-live=true do-timestamp=true ! multipartdemux ! jpegdec ! "
            "identity name={} silent=false ! nvvidconv ! video/x-raw(memory:NVMM),width={},"
            "height={} ! {}").format(kaynak_kok(kaynak) + VIDEO_YOLU, NABIZ_ADI, int(genislik),
                                     int(yukseklik), _drm_sink(conn_id))


def drm_video_argv(gst="gst-launch-1.0", kaynak=VARSAYILAN_KAYNAK, conn_id=None, stdbuf=None):
    """Video borusu argv'si — TEK KAYNAK (drm_kos ve --kuru ayni argv'yi kullanir).
    `-v`: identity nabiz satirlari stdout'a; `-e`: durdurmada EOS. `stdbuf` (yol) verilirse
    `stdbuf -oL` oneki: stdout boruya bagliyken -v satirlari SATIR tamponlu gelsin — blok tampon
    nabzi toplu getirip saglikli boruyu 'donmus' gosterirdi (gst-launch'in kendi fflush'i
    Jetson'da OLCULEMEDI)."""
    onek = [stdbuf, "-oL"] if stdbuf else []
    return onek + [gst, "-v", "-e", drm_boru(kaynak, conn_id=conn_id)]


_GST_METIN_IZINLI = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,:/()_->")


def _gst_metni(metin, azami=110):
    """textoverlay text="..." icin guvenli ASCII (tirnak/unlem/kacis YOK)."""
    m = "".join(c if c in _GST_METIN_IZINLI else " " for c in ascii_metin(metin))
    return " ".join(m.split())[:azami]


def drm_goruntu_yok_boru(sebep, genislik=TUVAL_GENISLIK, yukseklik=TUVAL_YUKSEKLIK,
                         conn_id=None):
    """Yayin yokken DRM ekrani: kirmizi zemin + "GORUNTU YOK - sebep". Eski kare KAYNAGI YOK."""
    return ('videotestsrc pattern=red is-live=true ! video/x-raw,width={w},height={h},'
            'framerate=5/1 ! textoverlay text="{m}" valignment=center halignment=center '
            'font-desc="Sans Bold 28" ! nvvidconv ! video/x-raw(memory:NVMM),width={w},'
            'height={h} ! {sink}').format(w=int(genislik), h=int(yukseklik),
                                          m=_gst_metni("GORUNTU YOK - " + str(sebep)),
                                          sink=_drm_sink(conn_id))


def boru_elemanlari(boru):
    """Boru dizgisindeki eleman adlari (sirali; caps parcalari haric)."""
    elemanlar = []
    for parca in boru.strip().strip("()").split("!"):
        ad = parca.strip().split(" ", 1)[0] if parca.strip() else ""
        if ad and "/" not in ad:
            elemanlar.append(ad)
    return elemanlar


def komut_metni(argv):
    return " ".join(shlex.quote(str(a)) for a in argv)


def _sureci_durdur(p, zaman_asimi_s=3.0):
    if p.poll() is None:
        try:
            p.terminate()
            p.wait(timeout=zaman_asimi_s)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
        except OSError:
            pass
    return p.returncode


# ── drm boru nabzi (T228-D) ───────────────────────────────────────────────────
_NABIZ_TUR = re.compile(r"\b(chain|event)\b")
_NABIZ_PTS = re.compile(r"\bpts\s*[:=]\s*(\d+):(\d{1,2}):(\d{1,2}(?:\.\d+)?)")
_NABIZ_ELEMAN = {}


def _nabiz_eleman_kalibi(ad):
    k = _NABIZ_ELEMAN.get(ad)
    if k is None:
        a = re.escape(ad)
        # '/...:nabiz' ya da satir basi 'nabiz' (ardindan harf/rakam/'.' YOK -> 'nabizci' ve pad
        # caps satiri 'nabiz.GstPad:src' sayilmaz) ya da pad adi '(nabiz:sink)'
        k = _NABIZ_ELEMAN[ad] = re.compile(r"(?:(?:^|[:/]){0}(?![\w.])|\({0}:)".format(a))
    return k


def nabiz_ayristir(satir, ad=NABIZ_ADI):
    """`gst-launch-1.0 -v` satiri -> None (nabiz degil) ya da {"pts_s": float|None} (saf).

    Jetson'da bicim OLCULEMEDI (GOSTERICI_KURULUM §5 DOGRULANACAK; sahada `--nabiz-sina`) ->
    TOLERANSLI kural, bosluk/yildiz sayisina bagli DEGIL:
      * satir `ad` elemanina ait: yolda ':nabiz' (GstIdentity:nabiz), satir basi 'nabiz' ya da
        pad '(nabiz:'; 'nabizci', 'identity0' ve pad caps satiri ('nabiz.GstPad:src') SAYILMAZ;
      * degerde once 'chain' gecmeli (tampon); once 'event' geciyorsa (stream-start, segment,
        eos) ilerleme DEGIL;
      * 'pts: H:MM:SS.nnnnnnnnn' varsa okunur; 'none' ya da 99:99:99.* (GST_CLOCK_TIME_NONE) -> None.
    Beklenen bicim (GStreamer 1.x gstidentity.c last-message + gst-launch deep-notify; KAYNAK:
    kaynak kod bilgisi, Jetson'da OLCULMEDI):
      /GstPipeline:pipeline0/GstIdentity:nabiz: last-message = chain   ******* (nabiz:sink)
      (1382400 bytes, dts: none, pts: 0:00:01.234567890, duration: none, ...) 0x7f8c00b1c0
    """
    s = str(satir).strip()
    if not s or ad not in s or not _nabiz_eleman_kalibi(ad).search(s):
        return None
    deger = s.split("last-message", 1)[1] if "last-message" in s else s
    tur = _NABIZ_TUR.search(deger)
    if tur is None or tur.group(1) != "chain":
        return None
    pts = None
    m = _NABIZ_PTS.search(deger)
    if m:
        sa, dk, sn = int(m.group(1)), int(m.group(2)), float(m.group(3))
        if not (sa == 99 and dk == 99):
            pts = sa * 3600.0 + dk * 60.0 + sn
    return {"pts_s": pts}


class NabizIzleyici:
    """`gst-launch-1.0 -v` stdout'unu okur; son ILERLEYEN tamponun (nabiz) zamanini tutar.

    Ilerleme = nabiz satiri VE (pts yok ya da onceki pts'ten BUYUK); ayni/geri pts ilerleme
    DEGIL. Nabiz olmayan ilk `gst_log_siniri` satir 'gst: ' onekiyle loglanir — Jetson'daki
    GERCEK -v bicimi journal'dan okunabilsin (GOSTERICI_KURULUM §5 DOGRULANACAK). Okuyucu iplik
    boruyu SUREKLI bosaltir (dolan stdout borusu gst-launch'i durdurmasin).
    """

    def __init__(self, ad=NABIZ_ADI, saat=time.monotonic, log=logla,
                 gst_log_siniri=NABIZ_GST_LOG_SINIRI):
        self.ad = ad
        self.saat = saat
        self.log = log
        self.gst_log_siniri = int(gst_log_siniri)
        self.kilit = threading.Lock()
        self.son_t = None
        self.son_pts = None
        self.ilk_pts = None
        self.pts_ilk_t = None
        self.pts_son_t = None
        self.nabiz = 0
        self.satir_sayisi = 0
        self.ornek = []

    def besle(self, satir, simdi=None):
        """Bir -v satiri isle. Donus: bu satir ILERLEME mi (son_t guncellendi mi)."""
        n = nabiz_ayristir(satir, self.ad)
        t = self.saat() if simdi is None else simdi
        yaz = None
        with self.kilit:
            self.satir_sayisi += 1
            ilerledi = False
            if n is None:
                if len(self.ornek) < self.gst_log_siniri:
                    yaz = str(satir).strip()[:300]
                    if yaz:
                        self.ornek.append(yaz)
            else:
                pts = n["pts_s"]
                ilerledi = pts is None or self.son_pts is None or pts > self.son_pts
                if ilerledi:
                    if pts is not None:
                        if self.ilk_pts is None:
                            self.ilk_pts, self.pts_ilk_t = pts, t
                        self.son_pts, self.pts_son_t = pts, t
                    self.son_t = t
                    self.nabiz += 1
            ilk = ilerledi and self.nabiz == 1
        if yaz:
            self.log("gst: " + yaz)
        if ilk:
            self.log("DRM video borusu: ilk nabiz (ilerleyen tampon) goruldu")
        return ilerledi

    def son(self):
        with self.kilit:
            return self.son_t

    def ozet(self):
        with self.kilit:
            return {"satir": self.satir_sayisi, "nabiz": self.nabiz, "son_pts": self.son_pts,
                    "ilk_pts": self.ilk_pts, "pts_ilk_t": self.pts_ilk_t,
                    "pts_son_t": self.pts_son_t, "ornek": list(self.ornek)}

    def akimi_oku(self, akim):
        """Ayri (daemon) iplikte akimi EOF'a kadar okur; ipligi dondurur."""
        iplik = threading.Thread(target=self._oku, args=(akim,), name="drm-nabiz", daemon=True)
        iplik.start()
        return iplik

    def _oku(self, akim):
        try:
            for satir in iter(akim.readline, ""):
                self.besle(satir)
        except (OSError, ValueError):   # boru kapandi
            pass


def nabiz_sina(akim, cikti=print, saat=time.monotonic):
    """--nabiz-sina: stdin'deki `gst-launch-1.0 -v` ciktisini nabiz ayristiricisiyla sina
    (Jetson'da GERCEK bicim + ZAMANLAMA dogrulamasi, GOSTERICI_KURULUM §4/§5). Hicbir sey acmaz.

    Zamanlama: nabiz satirlarinin VARIS yayilimi pts yayilimiyla kiyaslanir. Canli boruda
    (videotestsrc is-live=true) satirlar zamaninda gelirse iki yayilim yakindir; cikti blok
    tamponluysa satirlar TOPLU gelir (varis << pts) -> drm kipinde nabiz gecikir, saglikli boru
    'donmus' sayilirdi. pts yayilimi < NABIZ_SINA_ASGARI_PTS_S ise zamanlama denetlenemez.
    Donus: 0 ESLESTI (zamanlama ZAMANINDA ya da denetlenemedi) · 1 hic nabiz yok ya da TOPLU.
    """
    iz = NabizIzleyici(saat=saat, log=lambda *_a, **_k: None, gst_log_siniri=5)
    for satir in iter(akim.readline, ""):
        iz.besle(satir)
    o = iz.ozet()
    if not o["nabiz"]:
        cikti("NABIZ_SINA: ESLESMEDI — {} satir, HIC nabiz ayristirilamadi: gst-launch-1.0 -v "
              "bicimi DOGRULANACAK (GOSTERICI_KURULUM §5); drm kipinde video borusu {:g} s'de bir "
              "GORUNTU YOK'a duser (fail-closed). Ilk taninmayan satirlar:".format(
                  o["satir"], DRM_BORU_DONMA_S))
        for s in o["ornek"]:
            cikti("  " + s)
        return CIKIS_NABIZ_YOK
    ozet = "{} satir, {} nabiz (ilerleyen tampon); son pts {}".format(
        o["satir"], o["nabiz"], "yok" if o["son_pts"] is None else "{:.3f} s".format(o["son_pts"]))
    pts_yay = None if o["ilk_pts"] is None else o["son_pts"] - o["ilk_pts"]
    if pts_yay is None or pts_yay < NABIZ_SINA_ASGARI_PTS_S:
        cikti("NABIZ_SINA: ESLESTI — {}; ZAMANLAMA denetlenemedi (pts yayilimi < {:g} s ya da pts "
              "yok) — canli boruyla kos (GOSTERICI_KURULUM §5)".format(ozet, NABIZ_SINA_ASGARI_PTS_S))
        return CIKIS_TAMAM
    varis = o["pts_son_t"] - o["pts_ilk_t"]
    if varis < NABIZ_SINA_VARIS_ORANI * pts_yay:
        cikti("NABIZ_SINA: TOPLU — {}; varis yayilimi {:.2f} s < pts yayilimi {:.2f} s x {:g}: -v "
              "ciktisi TAMPONLU geliyor -> drm kipinde nabiz gecikir, saglikli boru 'donmus' "
              "sayilir. `stdbuf -oL gst-launch-1.0 ...` ile yeniden dene; duzelmezse x11 kipinde "
              "kal".format(ozet, varis, pts_yay, NABIZ_SINA_VARIS_ORANI))
        return CIKIS_NABIZ_YOK
    cikti("NABIZ_SINA: ESLESTI — {}; ZAMANINDA: varis yayilimi {:.2f} s / pts yayilimi {:.2f} s"
          .format(ozet, varis, pts_yay))
    return CIKIS_TAMAM


def boru_donmus_mu(simdi, baslama_t, son_nabiz_t, esik_s=DRM_BORU_DONMA_S):
    """Saf: video borusu `esik_s`'den UZUN suredir ilerlemedi mi? Referans son nabiz; hic nabiz
    yoksa borunun baslama ani (acilis payi = esik). Sinirda (== esik) donmus DEGIL."""
    ref = float(baslama_t) if son_nabiz_t is None else max(float(baslama_t), float(son_nabiz_t))
    return float(simdi) - ref > esik_s


def _donma_sebebi(simdi, baslama_t, son_nabiz_t, esik_s):
    if son_nabiz_t is None:
        return "video borusu ilerlemiyor: acilistan beri {:.1f} s tampon yok (> {:g} s)".format(
            _yukari_ondalik(float(simdi) - float(baslama_t)), esik_s)
    return "video borusu ilerlemiyor: son tampon {:.1f} s once (> {:g} s)".format(
        _yukari_ondalik(float(simdi) - max(float(baslama_t), float(son_nabiz_t))), esik_s)


def drm_boru_karari(calisan, son_boru, taze, ardisik, simdi, son_baslatma_t,
                    gerekli_ardisik=DRM_CANLI_ARDISIK, asgari_aralik_s=DRM_ASGARI_ARALIK_S):
    """Saf DRM karari (T228-D): histerezis + boru yeniden baslatma sikligi.

    calisan : su an CALISAN boru (BORU_VIDEO / BORU_YOK / None = boru yok: acilis ya da boru
              kendiliginden bitti)
    son_boru: en son BASLATILAN borunun turu (None = hic)
    taze    : bu yoklamada kare CANLI mi (video borusu calisiyorsa nabzi da ilerliyor mu)
    ardisik : bu yoklama DAHIL ardisik taze yoklama sayisi
    Kurallar:
      * CANLI'dan (video borusundan) cikis ILK bayat/hata/donmus yoklamada — sikliga takilmaz
        (guvenli taraf: eski kare ekranda kalmaz);
      * video borusu kendiliginden bittiyse GORUNTU YOK borusu HEMEN (son kare ekranda kalmasin);
      * video borusuna donus yalniz `gerekli_ardisik` ARDISIK taze yoklama VE son baslatmadan bu
        yana >= `asgari_aralik_s` ile (cirpinan yayin nvdrmvideosink'i surekli yeniden acmasin);
      * GORUNTU YOK borusunun (acilis / olen YOK borusu) yeniden baslatmasi da ayni sikliga
        tabidir; beklerken calisan boru surer.
    """
    serbest = son_baslatma_t is None or (float(simdi) - float(son_baslatma_t)) >= asgari_aralik_s
    if calisan == BORU_VIDEO:
        if taze:
            return DrmKarar(BORU_VIDEO, False, False)
        return DrmKarar(BORU_YOK, True, True)          # CANLI'dan cikis ANINDA (guvenli taraf)
    if calisan is None and son_boru == BORU_VIDEO:
        return DrmKarar(BORU_YOK, True, True)          # olen video borusu: son kare kalmasin
    istenen = BORU_VIDEO if (taze and ardisik >= gerekli_ardisik) else BORU_YOK
    if calisan == istenen:
        return DrmKarar(istenen, False, False)
    if not serbest:
        return DrmKarar(calisan, False, False)         # bekle: calisan boru (ya da hic) surer
    return DrmKarar(istenen, True, False)


def drm_gozetmen(video_argv, yok_argv_uret, durum_oku, baslat, bitti, uyku=time.sleep,
                 saat=time.monotonic, log=logla, yoklama_s=DRM_YOKLAMA_S,
                 asgari_omur_s=DRM_ASGARI_OMUR_S, ilerleme_oku=None,
                 donma_esigi_s=DRM_BORU_DONMA_S, gerekli_ardisik=DRM_CANLI_ARDISIK,
                 asgari_aralik_s=DRM_ASGARI_ARALIK_S):
    """drm kipi gozetmeni: yayin CANLI iken video borusu, degilse GORUNTU YOK borusu.

    Her `yoklama_s`'de bir: (1) calisan boru kendiliginden bittiyse KIRMIZI log (omur <
    `asgari_omur_s` ise Argus uyarisi); (2) /kare.jpg yoklanir (`durum_oku`); (3) video borusu
    calisiyorsa `ilerleme_oku(p)` (son nabiz zamani ya da None) ile boru ilerlemesi denetlenir —
    `donma_esigi_s`'den uzun sure tampon yoksa kare taze olsa da GORUNTU YOK; (4) karar SAF
    `drm_boru_karari`'ndadir (histerezis + baslatma sikligi). `ilerleme_oku` None ise nabiz
    denetimi yapilmaz (drm_kos HER ZAMAN verir). Donus: baslatilan surec sayisi.
    """
    sayac = 0
    p = None
    calisan = son_boru = None
    baslama_t = son_baslatma_t = None
    ardisik = 0
    onceki_durum = None
    try:
        while not bitti():
            if p is not None and p.poll() is not None:
                omur = saat() - baslama_t
                log("DRM {} borusu kendiliginden bitti rc={} omur={:.1f} s".format(
                    calisan, p.returncode, omur), kirmizi=True)
                if omur < asgari_omur_s:
                    log("[UYARI] boru {:.1f} s icinde bitti (gdm/nvidia-drm/EDID?) — {}".format(
                        omur, ARGUS_UYARISI), kirmizi=True)
                if calisan == BORU_VIDEO:
                    ardisik = 0
                p, calisan = None, None
            d = durum_oku()
            simdi = saat()
            taze = d.durum == DURUM_CANLI
            if taze and calisan == BORU_VIDEO and ilerleme_oku is not None:
                son_nabiz = ilerleme_oku(p)
                if boru_donmus_mu(simdi, baslama_t, son_nabiz, donma_esigi_s):
                    d = EkranDurumu(DURUM_YOK, _donma_sebebi(simdi, baslama_t, son_nabiz,
                                                             donma_esigi_s), d.yas_s)
                    taze = False
                    if son_nabiz is None:
                        log("[UYARI] video borusundan HIC nabiz ayristirilamadi — gst-launch-1.0 "
                            "-v bicimi DOGRULANACAK (GOSTERICI_KURULUM §5, --nabiz-sina); boru "
                            "gercekten akmiyor da olabilir", kirmizi=True)
            ardisik = ardisik + 1 if taze else 0
            if d.durum != onceki_durum:
                _durum_logu(onceki_durum, d, onek="DRM yoklama", log=log)
                onceki_durum = d.durum
            k = drm_boru_karari(calisan, son_boru, taze, ardisik, simdi, son_baslatma_t,
                                gerekli_ardisik=gerekli_ardisik, asgari_aralik_s=asgari_aralik_s)
            if k.baslat:
                if p is not None:
                    _sureci_durdur(p)
                if k.boru == BORU_VIDEO:
                    argv, sebep = video_argv, ""
                else:
                    sebep = d.sebep if d.durum != DURUM_CANLI else (
                        "yayin dogrulaniyor ({}/{} ardisik taze yoklama)".format(
                            ardisik, gerekli_ardisik))
                    argv = yok_argv_uret(sebep)
                p = baslat(argv)
                sayac += 1
                calisan = son_boru = k.boru
                baslama_t = son_baslatma_t = saat()
                log("DRM {} borusu basladi{}".format(
                    k.boru, " ({})".format(sebep) if sebep else ""), kirmizi=k.boru != BORU_VIDEO)
            uyku(yoklama_s)
    finally:
        if p is not None:
            _sureci_durdur(p)
    return sayac


def drm_kos(args, baslat=subprocess.Popen, gst_yolu=None, saat=time.monotonic,
            stdbuf_yolu=None):
    gst = gst_yolu if gst_yolu is not None else shutil.which("gst-launch-1.0")
    if not gst:
        logla("HATA: gst-launch-1.0 yok — " + DRM_KURULUM_NOTU, kirmizi=True)
        return CIKIS_BAGIMLILIK
    logla("[UYARI] " + ARGUS_UYARISI, kirmizi=True)
    cekici = KareCekici(args.kaynak, hz=args.hz)

    def durum_oku():
        cekici.cek_bir_kez()
        _k, son_t, h, _s = cekici.anlik()
        return ekran_durumu(saat(), son_t, h)

    dur = threading.Event()
    eski_sinyal = _sinyal_kur(dur)
    bitis = saat() + args.sure if args.sure else None

    def bitti():
        return dur.is_set() or (bitis is not None and saat() >= bitis)

    stdbuf = stdbuf_yolu if stdbuf_yolu is not None else shutil.which("stdbuf")
    if not stdbuf:
        logla("[UYARI] stdbuf yok — video borusu -v ciktisi satir tamponu garantisiz (gst-launch "
              "fflush'i DOGRULANACAK; toplu gelen nabiz saglikli boruyu 'donmus' gosterebilir)",
              kirmizi=True)
    video = drm_video_argv(gst, args.kaynak, conn_id=args.conn_id, stdbuf=stdbuf or None)
    son = {"p": None, "iz": None}

    def boru_baslat(argv):
        if argv != video:
            return baslat(argv)
        # video borusu: -v ciktisi BORUYA; okuyucu iplik nabzi izler ve boruyu bosaltir
        p = baslat(argv, stdout=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
                   bufsize=1)
        iz = NabizIzleyici(saat=saat)
        iz.akimi_oku(p.stdout)
        son["p"], son["iz"] = p, iz
        return p

    def ilerleme_oku(p):
        return son["iz"].son() if (son["p"] is p and son["iz"] is not None) else None

    logla("DRM gozetmen: yoklama {:g} s · CANLI'ya donus {} ardisik taze yoklama · baslatma "
          "araligi >= {:g} s · boru nabzi (identity {}) > {:g} s durursa GORUNTU YOK".format(
              DRM_YOKLAMA_S, DRM_CANLI_ARDISIK, DRM_ASGARI_ARALIK_S, NABIZ_ADI, DRM_BORU_DONMA_S))
    try:
        drm_gozetmen(video, lambda sebep: [gst, drm_goruntu_yok_boru(sebep, conn_id=args.conn_id)],
                     durum_oku, boru_baslat, bitti, saat=saat, yoklama_s=DRM_YOKLAMA_S,
                     asgari_omur_s=DRM_ASGARI_OMUR_S, ilerleme_oku=ilerleme_oku,
                     donma_esigi_s=DRM_BORU_DONMA_S, gerekli_ardisik=DRM_CANLI_ARDISIK,
                     asgari_aralik_s=DRM_ASGARI_ARALIK_S)
    finally:
        _sinyal_geri(eski_sinyal)
    return CIKIS_TAMAM


# ── rtsp kipi (YEDEK) ─────────────────────────────────────────────────────────
def rtsp_url(ip, port=RTSP_PORT):
    return "rtsp://{}:{}{}".format(ip, int(port), RTSP_YOL)


def rtsp_boru(tur=RTSP_BORU_TUVAL, kaynak=VARSAYILAN_KAYNAK, genislik=TUVAL_GENISLIK,
              yukseklik=TUVAL_YUKSEKLIK, fps=RTSP_FPS, bitrate_kbps=X264_BITRATE_KBPS,
              key_int_max=X264_KEY_INT_MAX):
    """GstRtspServer fabrika borusu ("( ... )"). tuval: gostericinin cizdigi ekran appsrc'ye
    itilir (BAYAT / GORUNTU YOK ekranlari RTSP'ye de gider); http: ham /video souphttpsrc."""
    x264 = ("x264enc tune=zerolatency speed-preset=ultrafast bitrate={} key-int-max={}").format(
        int(bitrate_kbps), int(key_int_max))
    cikis = "rtph264pay name=pay0 pt=96 config-interval=1"
    if tur == RTSP_BORU_TUVAL:
        giris = ("appsrc name={} is-live=true block=true format=time "
                 "caps=video/x-raw,format=BGR,width={},height={},framerate={}/1 ! "
                 "videoconvert ! video/x-raw,format=I420").format(
                     RTSP_APPSRC_ADI, int(genislik), int(yukseklik), int(fps))
    elif tur == RTSP_BORU_HTTP:
        giris = ("souphttpsrc location={} is-live=true do-timestamp=true ! multipartdemux ! "
                 "jpegdec ! videoconvert ! videoscale ! videorate ! "
                 "video/x-raw,format=I420,width={},height={},framerate={}/1").format(
                     kaynak_kok(kaynak) + VIDEO_YOLU, int(genislik), int(yukseklik), int(fps))
    else:
        raise ValueError("rtsp boru turu taninmiyor: {!r}".format(tur))
    return "( {} ! {} ! {} )".format(giris, x264, cikis)


def gi_durumu():
    """(var_mi, ayrinti): python3-gi + GstRtspServer 1.0 yuklenebiliyor mu (hicbir sey acmaz)."""
    try:
        import gi
        gi.require_version("Gst", "1.0")
        gi.require_version("GstRtspServer", "1.0")
        from gi.repository import Gst, GstRtspServer  # noqa: F401
    except (ImportError, ValueError) as exc:
        return False, "{}: {}".format(type(exc).__name__, exc)
    return True, "gi {} + GstRtspServer 1.0".format(getattr(gi, "__version__", "?"))


def rtsp_kos(args, saat=time.monotonic):   # pragma: no cover - Jetson'da (gi) kosar; PC'de OLCULEMEDI
    var, ayrinti = gi_durumu()
    if not var:
        logla("HATA: rtsp kipi GStreamer RTSP sunucusu ister ({}) — kurulum: {}".format(
            ayrinti, RTSP_KURULUM_NOTU), kirmizi=True)
        return CIKIS_BAGIMLILIK
    import gi
    gi.require_version("Gst", "1.0")
    gi.require_version("GstRtspServer", "1.0")
    from gi.repository import GLib, Gst, GstRtspServer
    Gst.init(None)
    boru = rtsp_boru(args.rtsp_boru, args.kaynak)
    eksik = [e for e in boru_elemanlari(boru) if Gst.ElementFactory.find(e) is None]
    if eksik:
        logla("HATA: GStreamer elemanlari yok: {} — {}".format(", ".join(eksik),
                                                              RTSP_KURULUM_NOTU), kirmizi=True)
        return CIKIS_BAGIMLILIK
    fabrika = GstRtspServer.RTSPMediaFactory()
    fabrika.set_launch(boru)
    fabrika.set_shared(True)
    cekici = None
    if args.rtsp_boru == RTSP_BORU_TUVAL:
        cekici = KareCekici(args.kaynak, hz=args.hz)
        cekici.start()
        kare_suresi = Gst.SECOND // RTSP_FPS
        iz = {"onceki": None}

        def tuval_uret():
            kare, son_t, hata, _s = cekici.anlik()
            d = ekran_durumu(saat(), son_t, hata)
            if d.durum != iz["onceki"]:
                _durum_logu(iz["onceki"], d, onek="RTSP ekran")
                iz["onceki"] = d.durum
            return tuval_ciz(d, kare, saat_metni=time.strftime("%H:%M:%S"))

        def yapilandir(_fabrika, medya):
            eleman = medya.get_element()
            appsrc = (eleman.get_by_name(RTSP_APPSRC_ADI) if hasattr(eleman, "get_by_name")
                      else eleman.get_child_by_name(RTSP_APPSRC_ADI))
            sayac = [0]

            def veri_iste(src, _uzunluk):
                tuval = np.ascontiguousarray(tuval_uret())
                tampon = Gst.Buffer.new_wrapped(tuval.tobytes())
                tampon.duration = kare_suresi
                tampon.pts = tampon.dts = sayac[0] * kare_suresi
                tampon.offset = sayac[0]
                sayac[0] += 1
                src.emit("push-buffer", tampon)

            appsrc.connect("need-data", veri_iste)

        fabrika.connect("media-configure", yapilandir)
    sunucu = GstRtspServer.RTSPServer()
    sunucu.set_address(args.jetson_ip)
    sunucu.set_service(str(args.rtsp_port))
    sunucu.get_mount_points().add_factory(RTSP_YOL, fabrika)
    if not sunucu.attach(None):
        logla("HATA: RTSP sunucusu {}:{} baglanamadi (IP bu makinede yok / port dolu?)".format(
            args.jetson_ip, args.rtsp_port), kirmizi=True)
        if cekici is not None:
            cekici.durdur()
        return CIKIS_ORTAM
    dongu = GLib.MainLoop()

    def _bitir(*_a):
        dongu.quit()
        return False

    if args.sure:
        GLib.timeout_add(int(args.sure * 1000), _bitir)
    try:
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, _bitir)
    except (AttributeError, TypeError):
        pass
    logla("RTSP yayini: {} · {}x{} @ {} fps · x264 {} kbit/s key-int-max {} · boru={}".format(
        rtsp_url(args.jetson_ip, args.rtsp_port), TUVAL_GENISLIK, TUVAL_YUKSEKLIK, RTSP_FPS,
        X264_BITRATE_KBPS, X264_KEY_INT_MAX, args.rtsp_boru))
    try:
        dongu.run()
    except KeyboardInterrupt:
        pass
    finally:
        if cekici is not None:
            cekici.durdur()
            cekici.join(2.0)
    return CIKIS_TAMAM


# ── kuru kosum + CLI ──────────────────────────────────────────────────────────
def kuru_satirlari(args, ortam=None, platform=None, ip_uyarilari=(), gst_bul=shutil.which,
                   gi_kontrol=gi_durumu):
    """--kuru: secilen kipin tam komutu/ayari (HICBIR SEY ACILMAZ)."""
    s = ["# isaretli_gosterici --kuru · KIP={} · HICBIR SEY ACILMADI (pencere/boru/sunucu "
         "yok)".format(args.kip),
         "kaynak: {} ({} / {}) — T227 rpi_inference --isaretli-yayin; kamera_koprusu ile ayni "
         "uclar".format(args.kaynak, KARE_YOLU, VIDEO_YOLU),
         "esikler: BAYAT > {:g} s (kare gri+karartilmis + bant) · GORUNTU YOK > {:g} s ya da "
         "erisilemeyen / 503 / cozulemeyen kare (eski kare CIZILMEZ)".format(
             BAYAT_ESIGI_S, GORUNTU_YOK_ESIGI_S),
         "KARAR URETMEZ: rota verisi + hakem onayi SiK 433 MHz'te (CONTRACTS §6.7); video "
         "koparsa ucus gecersiz OLMAZ"]
    jetson = ["/usr/bin/python3", "~/navitas/scripts/isaretli_gosterici.py", "--kip", args.kip,
              "--kaynak", args.kaynak]
    if args.kip == KIP_X11:
        s.append("x11: pencere {!r} WINDOW_FULLSCREEN · tuval {}x{} · cekme {:g} Hz ({}) · "
                 "cizim {:g} Hz".format(PENCERE_ADI, TUVAL_GENISLIK, TUVAL_YUKSEKLIK, args.hz,
                                        args.kaynak + KARE_YOLU, CIZIM_HZ))
        o = os.environ if ortam is None else ortam
        h = ekran_ortami_hatasi(o, platform)
        if h:
            s.append("[UYARI] {} — gercek kosum cikis {}".format(h, CIKIS_ORTAM))
        elif o.get("DISPLAY"):
            s.append("[VAR] DISPLAY={}".format(o.get("DISPLAY")))
        else:
            s.append("[BILGI] platform {}: DISPLAY denetimi yok (Linux disi)".format(
                platform or sys.platform))
        s.append("baslatan: X11 otomatik oturum + ~/.config/autostart/"
                 "navitas-isaretli-gosterici.desktop (gosterici/GOSTERICI_KURULUM.md)")
    elif args.kip == KIP_DRM:
        s.append("## on kosul (root; gdm DURUR -> masaustu gider) — birim "
                 "navitas-isaretli-gosterici-drm.service VARSAYILAN KAPALI")
        s.extend(DRM_ON_KOSUL)
        s.append("## video borusu (yayin CANLI iken; -v: identity nabiz satirlari gozetmene)")
        s.append(komut_metni(drm_video_argv("gst-launch-1.0", args.kaynak, conn_id=args.conn_id)))
        s.append("## GORUNTU YOK borusu (yayin yok, kare > {:g} s yeni degil ya da boru nabzi "
                 "> {:g} s yok)".format(BAYAT_ESIGI_S, DRM_BORU_DONMA_S))
        s.append(komut_metni(["gst-launch-1.0",
                              drm_goruntu_yok_boru("SEBEP", conn_id=args.conn_id)]))
        s.append("[UYARI] " + ARGUS_UYARISI)
        s.append("[BILGI] " + DRM_BAYAT_NOTU)
        s.append("[DOGRULANACAK] " + DRM_NABIZ_NOTU)
        sb = gst_bul("stdbuf")
        s.append("[BILGI] drm_kos video borusunu `stdbuf -oL` onekiyle kosar (-v satir tamponlu): "
                 "stdbuf {}".format("VAR ({})".format(sb) if sb else
                                    "YOK — onek konmaz, gst-launch fflush'ina guvenilir "
                                    "(DOGRULANACAK)"))
        gst = gst_bul("gst-launch-1.0")
        s.append("[VAR] gst-launch-1.0 ({})".format(gst) if gst else
                 "[YOK] gst-launch-1.0 (PATH) — gercek kosum cikis {}: {}".format(
                     CIKIS_BAGIMLILIK, DRM_KURULUM_NOTU))
    else:
        jetson += ["--jetson-ip", args.jetson_ip, "--rtsp-boru", args.rtsp_boru]
        s.append("RTSP (YEDEK): {} · {}x{} @ {} fps · x264 {} kbit/s key-int-max {} "
                 "(Orin Nano'da NVENC YOK — yazilim x264)".format(
                     rtsp_url(args.jetson_ip, args.rtsp_port), TUVAL_GENISLIK, TUVAL_YUKSEKLIK,
                     RTSP_FPS, X264_BITRATE_KBPS, X264_KEY_INT_MAX))
        s.append("IP plani: SIYI sabit {} YASAK; oneri {}".format(
            " / ".join(".{} {}".format(ip.rsplit(".", 1)[1], ad)
                       for ip, ad in sorted(SIYI_SABIT_IP.items())), JETSON_IP_ONERI))
        s.extend("[UYARI] " + u for u in ip_uyarilari)
        s.append("boru ({}): {}".format(args.rtsp_boru, rtsp_boru(args.rtsp_boru, args.kaynak)))
        var, ayrinti = gi_kontrol()
        s.append("[VAR] {}".format(ayrinti) if var else
                 "[YOK] python3-gi + GstRtspServer ({}) — gercek kosum cikis {}: {}".format(
                     ayrinti, CIKIS_BAGIMLILIK, RTSP_KURULUM_NOTU))
        s.append("NOT: hava biriminin LAN&PWR portu donusturucudeyse Jetson icin ethernet "
                 "anahtari gerekir (TASARIM §1 yedek yol)")
    s.append("KOMUT (Jetson): " + " ".join(jetson))
    s.append("KURU: tamam (cikis 0) — hicbir sey acilmadi")
    return s


def _parser():
    p = argparse.ArgumentParser(
        description="NAVITAS isaretli gosterici (T228): isaretli kare -> tam ekran (x11/drm) "
                    "ya da yedek RTSP; KARAR URETMEZ")
    p.add_argument("--kip", choices=KIPLER, default=KIP_X11,
                   help="x11 (varsayilan, masaustu tam ekran) | drm (nvdrmvideosink, gdm kapali) "
                        "| rtsp (yedek x264)")
    p.add_argument("--kaynak", default=VARSAYILAN_KAYNAK,
                   help="isaretli yayin koku http://host:port (varsayilan {}; T227)".format(
                       VARSAYILAN_KAYNAK))
    p.add_argument("--kuru", action="store_true",
                   help="secilen kipin komutunu/ayarini yaz, HICBIR SEY ACMA")
    p.add_argument("--sure", type=float, default=0.0,
                   help="saniye sonra cik (0 = surekli; PC dumani)")
    p.add_argument("--hz", type=float, default=CEKME_HZ, help="/kare.jpg cekme sikligi (Hz)")
    p.add_argument("--tuval-kaydi", default=None,
                   help="x11: durum degisiminde + cikista tuvali JPEG olarak bu dizine yaz")
    p.add_argument("--conn-id", type=int, default=None, help="drm: nvdrmvideosink conn_id")
    p.add_argument("--jetson-ip", default=JETSON_IP_ONERI,
                   help="rtsp: yayin adresi (varsayilan {}; SIYI .11/.12/.20/.25 YASAK)".format(
                       JETSON_IP_ONERI))
    p.add_argument("--rtsp-port", type=int, default=RTSP_PORT, help="rtsp portu")
    p.add_argument("--rtsp-boru", choices=(RTSP_BORU_TUVAL, RTSP_BORU_HTTP),
                   default=RTSP_BORU_TUVAL,
                   help="tuval: cizilen ekran (BAYAT/GORUNTU YOK dahil) appsrc ile | http: ham "
                        "/video souphttpsrc")
    p.add_argument("--nabiz-sina", action="store_true",
                   help="stdin'deki gst-launch-1.0 -v ciktisini drm nabiz ayristiricisiyla sina "
                        "(Jetson'da -v bicimi dogrulamasi, GOSTERICI_KURULUM §5); hicbir sey acmaz")
    return p


def _stdin_utf8():
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass
    return sys.stdin


def main(argv=None, ortam=None, platform=None):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.nabiz_sina:
        return nabiz_sina(_stdin_utf8())
    try:
        args.kaynak = kaynak_kok(args.kaynak)
    except ValueError as exc:
        parser.error(str(exc))
    if args.sure < 0:
        parser.error("--sure negatif olamaz")
    if not 0 < args.hz <= 30:
        parser.error("--hz 0 ile 30 arasinda olmali")
    if not 1 <= args.rtsp_port <= 65535:
        parser.error("--rtsp-port 1-65535 arasi olmali")
    ip_uyarilari = []
    if args.kip == KIP_RTSP:
        try:
            args.jetson_ip, ip_uyarilari = jetson_ip_dogrula(args.jetson_ip)
        except ValueError as exc:
            parser.error(str(exc))
    if args.kuru:
        for satir in kuru_satirlari(args, ortam=ortam, platform=platform,
                                    ip_uyarilari=ip_uyarilari):
            print(satir)
        return CIKIS_TAMAM
    for u in ip_uyarilari:
        logla("[UYARI] " + u, kirmizi=True)
    if args.kip == KIP_X11:
        return x11_kos(args, ortam=ortam, platform=platform)
    if args.kip == KIP_DRM:
        return drm_kos(args)
    return rtsp_kos(args)


if __name__ == "__main__":
    raise SystemExit(main())
