"""Kare keskinligi (odak) olcusu — ONARIM-04 (2026-09-17).

NEDEN: Jetson'da IMX477 + 6 mm lensle canli kararlarin TAMAMI MASKE_YOK idi.
Kontrollu deney (ONARIM/ONARIM-04_canli_maske_yok.md): bilinen iyi 36 DJI karesine
Gauss bulanikligi verilince model zemini kaybediyor ve kareyi ENGEL sayiyor
(sigma 0: 32/36 karede zemin · sigma 5: 5/36 · sigma 10: 0/36, engel ~%96). Canli
IMX477 karelerinin bu olcusu 1,5 ve 2,3 = sigma~10 bolgesi. Yani odak kaymasi
algiyi TAMAMEN kapatir ve bunu ekrandan gozle ayirt etmek zor.

OLCU: gri kare uzun kenari 640 px'e INTER_AREA ile kucultulur, Laplacian varyansi.
Cozunurlukten bagimsiz karsilastirma icin sabit 640 (model girdisiyle ayni olcek).

BANTLAR (ON KAYIT, 2026-09-17 deneyi — DJI 36 + WhatsApp 67 kare, medyanlar):
  sigma0 3369 / 1373 · sigma1 582 / 353 · sigma2 67 / 66 · sigma3 16 / 20 · sigma5 3,7 / 5,4
  NET      >= 100   (sigma <= ~1,5; zemin korunuyor)
  SUPHELI  20..100  (sigma ~2..3; DJI sigma2'de 23/36 karede zemin kaldi)
  BULANIK  < 20     (sigma >= ~3; sigma5'te 5/36, sigma10'da 0/36)
Esikler sahne dokusuna baglidir (duz beton/cim daha dusuk verir) — mutlak kapi
DEGIL, odak ayari ve teshis gostergesidir. Karar yolunu ETKILEMEZ.
"""

import cv2
import numpy as np

KESKINLIK_OLCEK_PX = 640
KESKINLIK_NET_ESIK = 100.0
KESKINLIK_BULANIK_ESIK = 20.0

KESKIN_NET = "NET"
KESKIN_SUPHELI = "SUPHELI"
KESKIN_BULANIK = "BULANIK"


def kare_keskinligi(bgr):
    """BGR ya da gri kare -> Laplacian varyansi (uzun kenar 640 px'e olceklenmis)."""
    if bgr is None or getattr(bgr, "size", 0) == 0:
        raise ValueError("bos kare")
    gri = bgr if bgr.ndim == 2 else cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    uzun = max(gri.shape[:2])
    if uzun != KESKINLIK_OLCEK_PX:
        s = KESKINLIK_OLCEK_PX / float(uzun)
        boyut = (max(1, round(gri.shape[1] * s)), max(1, round(gri.shape[0] * s)))
        gri = cv2.resize(gri, boyut, interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(gri, cv2.CV_64F).var())


def keskinlik_bandi(deger):
    if not np.isfinite(deger):
        raise ValueError("keskinlik sonlu olmali")
    if deger >= KESKINLIK_NET_ESIK:
        return KESKIN_NET
    if deger >= KESKINLIK_BULANIK_ESIK:
        return KESKIN_SUPHELI
    return KESKIN_BULANIK
