"""T188 KAPISI (ON_KAYIT 2026-08-28 SS8 · REVIEW_LOG D-326):
zemin kapamasinin FIZIKSEL TAVANI — "duba sirasi" kusuru.

OLCULEN KUSUR:
  `rpi_inference` zemin maskesine morfolojik KAPAMA uyguluyordu ve cekirdek
  `max(7, w // 30)` idi — goruntu GENISLIGININ ORANI, METRIK DEGIL.
  512 px'te 17 px, 3840 px'te 128 px. mpp 0,05'te 17 px = **0,85 m**: bir
  dubadan buyuk, arac yaricapiyla kiyaslanabilir.

  SONUC (sentetik olcum, DORT yapilandirmanin DORDUNDE de ayni):

      duba capi / araligi   ENGEL sinifinda    yalniz ZEMIN DELIGI
      0,40 m / 1,00 m       KAPALI (dogru)     yol=2  guven 1.00  <- YANLIS
      0,60 m / 1,20 m       KAPALI (dogru)     yol=2  guven 1.00  <- YANLIS
      0,30 m / 0,80 m       KAPALI (dogru)     yol=2  guven 1.00  <- YANLIS

  Yani model dubalari ENGEL sinifina koymayi kacirirsa ve zemin maskesinde
  yalnizca DELIK kalirsa, kapama delikleri geri dolduruyor ve sistem TAM
  GUVENLE acik yol bildiriyordu. Sartname SS2.1: yanlis guzergah = 0 PUAN.

⚠ KAPAMA, SERBEST ALANI BUYUTEN TEK ISLEMDIR (madde 15 tam olarak bunu
yasaklar). Tavan bu yuzden `min(mevcut, metrik)` seklinde uygulanir: cekirdek
yalnizca KUCULEBILIR, dolayisiyla serbest alan yalnizca KUCULUR — madde 15
olcumle degil INSA ile korunur.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import (KAPAMA_AZAMI_M,  # noqa: E402
                              kapama_cekirdegi_px)
from rpi_inference import _koridor_temizle, analyze_path  # noqa: E402

H = W = 640
MPP = 0.05          # 640 px -> 32 m saha


def _koridor(cap_m=0.0, ara_m=1.0, engel_sinifina=False):
    """Dikey koridor; istege bagli olarak enine bir DUBA SIRASI."""
    zemin = np.zeros((H, W), np.uint8)
    zemin[:, 200:440] = 1                       # 12 m genislik
    engel = np.zeros((H, W), np.uint8)
    if cap_m > 0:
        cap = max(1, int(round(cap_m / MPP)))
        ara = max(1, int(round(ara_m / MPP)))
        for x in range(200 + cap, 440, ara):
            cv2.circle(zemin, (x, H // 2), cap // 2, 0, -1)
            if engel_sinifina:
                cv2.circle(engel, (x, H // 2), cap // 2, 1, -1)
    return zemin, engel


class TavanSabitleri(unittest.TestCase):

    def test_tavan_ALGI_PAYI_ile_AYNI(self):
        """Tavan, algi belirsizligi olcegidir — uydurma bir sayi degil."""
        from costmap_path_finder import ALGI_PAYI_M
        self.assertEqual(ALGI_PAYI_M, KAPAMA_AZAMI_M)

    def test_tavan_ARAC_YARICAPINDAN_kucuk(self):
        """Kapama, aracin gecemeyecegi bir bosluğu DOLDURAMAMALI."""
        from karar_sozlesmesi import ARAC_GENISLIGI_M
        self.assertLess(KAPAMA_AZAMI_M, ARAC_GENISLIGI_M / 2.0)


class CekirdekTavani(unittest.TestCase):
    """`kapama_cekirdegi_px` — cekirdek YALNIZCA kuculebilir."""

    def test_mpp_verilince_KUCULUR(self):
        self.assertEqual(5, kapama_cekirdegi_px(17, 0.05))
        self.assertEqual(13, kapama_cekirdegi_px(17, 0.02))
        self.assertEqual(20, kapama_cekirdegi_px(128, 0.013))

    def test_ASLA_BUYUMEZ(self):
        """Madde 15: sonuc hicbir kosulda girdiden buyuk olamaz."""
        for mevcut in (3, 7, 17, 33, 128):
            for mpp in (0.001, 0.01, 0.05, 0.2, 1.0, 10.0):
                with self.subTest(mevcut=mevcut, mpp=mpp):
                    self.assertLessEqual(kapama_cekirdegi_px(mevcut, mpp),
                                         mevcut)

    def test_mpp_YOKSA_davranis_DEGISMEZ(self):
        """Fail-safe: olculemeyen durumda degisiklik yapilmaz."""
        for gecersiz in (None, 0, -1.0, True, float("nan"), float("inf"), "x"):
            with self.subTest(mpp=repr(gecersiz)):
                self.assertEqual(17, kapama_cekirdegi_px(17, gecersiz))

    def test_en_az_1_px(self):
        self.assertGreaterEqual(kapama_cekirdegi_px(17, 100.0), 1)

    def test_tavan_FORMULU_dogru(self):
        for mpp in (0.05, 0.02, 0.013):
            with self.subTest(mpp=mpp):
                beklenen = int(math.ceil(KAPAMA_AZAMI_M / mpp))
                self.assertEqual(min(999, beklenen),
                                 kapama_cekirdegi_px(999, mpp))


class DubaSirasiGECILMEZ(unittest.TestCase):
    """🔴 ASIL KAPI. Bes yapilandirmada da koridor KAPALI kalmali."""

    YAPILANDIRMALAR = ((0.40, 1.00), (0.40, 1.50), (0.60, 1.20),
                       (0.30, 0.80), (0.50, 1.20))

    def test_zemin_DELIGI_olarak_birakilan_duba_sirasi_KAPATIR(self):
        for cap_m, ara_m in self.YAPILANDIRMALAR:
            with self.subTest(cap=cap_m, aralik=ara_m):
                zemin, _ = _koridor(cap_m, ara_m, engel_sinifina=False)
                yol, guven, _wps, red = analyze_path(
                    zemin, icerik=(0, 0, W, H), engel_mask=None, mpp=MPP,
                    return_reason=True)
                self.assertIsNone(
                    yol,
                    f"duba {cap_m} m / {ara_m} m: koridor ACIK cikti "
                    f"(guven {guven}) — sartname SS2.1: yanlis guzergah 0 PUAN")

    def test_ENGEL_sinifindaki_duba_da_KAPATIR(self):
        """Model dubalari GORURSE de kapanmali (iki yol da calismali)."""
        for cap_m, ara_m in self.YAPILANDIRMALAR:
            with self.subTest(cap=cap_m, aralik=ara_m):
                zemin, engel = _koridor(cap_m, ara_m, engel_sinifina=True)
                yol, _g, _w, _r = analyze_path(
                    zemin, icerik=(0, 0, W, H), engel_mask=engel, mpp=MPP,
                    return_reason=True)
                self.assertIsNone(yol)

    def test_POZITIF_KONTROL_temiz_koridor_ROTA_VERIR(self):
        """Kapi 'her seyi reddet' degil: engelsiz koridorda rota CIKMALI."""
        zemin, _ = _koridor()
        yol, guven, _w, red = analyze_path(
            zemin, icerik=(0, 0, W, H), mpp=MPP, return_reason=True)
        self.assertIsNotNone(yol, f"temiz koridorda rota yok: {red}")
        self.assertGreater(guven, 0.5)

    def test_MUTASYON_tavan_KALKARSA_kusur_geri_gelir(self):
        """Kapinin bos olmadigi: tavansiz cekirdekle duba sirasi DOLUYOR."""
        zemin, _ = _koridor(0.40, 1.00, engel_sinifina=False)
        h, w = zemin.shape
        tavansiz = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
        kapali = cv2.morphologyEx(zemin, cv2.MORPH_CLOSE, tavansiz)
        # Delikler dolduysa koridor kesitinde bosluk KALMAZ
        kesit = kapali[h // 2, 200:440]
        self.assertGreater(
            float(kesit.mean()), 0.90,
            "tavansiz cekirdek dubalari doldurmuyor — kusur yeniden "
            "uretilemiyor, yani bu kapi BOS")
        tavanli = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kapama_cekirdegi_px(max(7, w // 30), MPP),
                                kapama_cekirdegi_px(max(7, h // 30), MPP)))
        kesit2 = cv2.morphologyEx(zemin, cv2.MORPH_CLOSE, tavanli)[h // 2, 200:440]
        self.assertLess(float(kesit2.mean()), 0.90,
                        "tavanli cekirdek de dolduruyor — tavan etkisiz")


class KoridorTemizleImzasi(unittest.TestCase):

    def test_mpp_gecirilebiliyor(self):
        zemin, engel = _koridor(0.40, 1.00)
        a = _koridor_temizle(zemin, engel)              # eski cagri sekli
        b = _koridor_temizle(zemin, engel, MPP)         # tavanli
        self.assertEqual(a.shape, b.shape)
        self.assertLessEqual(int((b > 0).sum()), int((a > 0).sum()),
                             "tavanli temizlik DAHA COK serbest alan uretti "
                             "— madde 15 ihlali")

    def test_URETIM_cagrisi_mpp_GECIRIYOR(self):
        kaynak = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
        self.assertIn("_koridor_temizle(trav_mask, engel_mask, mpp)", kaynak,
                      "uretim yolu mpp gecirmiyor — tavan olu kalir")
        self.assertIn("kapama_cekirdegi_px(max(7, w // 30), mpp)", kaynak)


if __name__ == "__main__":
    unittest.main()
