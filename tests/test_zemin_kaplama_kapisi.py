"""T48 KAPISI: zemin maskesi coktugunde rota YAYINLANIYOR mu?

Kusur (kullanici gordu, REVIEW_LOG D-62): hakem ekrani bina CATISI ve CIM
uzerinden gecen bir rotayi kendinden emin ciziyordu. Uretim modeli bu alanda
pratikte "arac mi, degil mi" ayiricisidir; cati, cim ve toprak zemin sinifina
duser. Maske "DOLU" gorundugu icin mevcut kapilarin HICBIRI bunu yakalayamaz:
K-A uc bantlara temasi gorur, C-uzayi acikligi gorur, K-B guveni gorur — ucu de
memnun kalir.

Bu paket UC seyi kanitlar:
  1. Kapi tavanin USTUNDE atesler, ALTINDA atesle-MEZ (pozitif + negatif kontrol).
  2. Kapi ROTADAN ONCE calisir ve fail-closed doner (waypoint uretilmez).
  3. Kapi madde 15 acisindan NOTRDUR: maskeye dokunmaz, tek piksel eklemez.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import (ROTA_RET_SEBEPLERI, ZEMIN_KAPLAMA_TAVANI,
                              ZEMIN_MASKESI_SUPHELI_SEBEBI, zemin_kaplamasi,
                              zemin_maskesi_reddi)
from rpi_inference import analyze_path

H, W = 600, 900


def _kaplamali(oran):
    """Soldan `oran` kadarini zemin sayan maske — kaplama TAM olarak `oran`."""
    m = np.zeros((H, W), np.uint8)
    m[:, :int(round(W * oran))] = 1
    return m


class KaplamaOlcumuTests(unittest.TestCase):

    def test_kaplama_icerik_kutusundan_olculur(self):
        m = np.zeros((H, W), np.uint8)
        m[:, :W // 2] = 1
        self.assertAlmostEqual(0.5, zemin_kaplamasi(m), places=3)
        # icerik yalniz SOL yariysa ayni maske %100 kaplar
        self.assertAlmostEqual(
            1.0, zemin_kaplamasi(m, (0, 0, W // 2, H)), places=3)
        # icerik yalniz SAG yariysa %0
        self.assertAlmostEqual(
            0.0, zemin_kaplamasi(m, (W // 2, 0, W // 2, H)), places=3)

    def test_bozuk_girdi_fail_closed(self):
        for kotu in (np.zeros((0, 0), np.uint8), np.zeros((5,), np.uint8)):
            self.assertEqual(0.0, zemin_kaplamasi(kotu))
        m = np.ones((H, W), np.uint8)
        self.assertEqual(0.0, zemin_kaplamasi(m, (0, 0, 0, 0)))

    def test_sebep_kodu_sozlesme_kumesinde(self):
        self.assertIn(ZEMIN_MASKESI_SUPHELI_SEBEBI, ROTA_RET_SEBEPLERI)


class KapiEsigiTests(unittest.TestCase):
    """Esik SOZLESMEDEN okunur; test ciplak sayi tasimaz (madde 16)."""

    def test_tavanin_ALTINDA_atesle_MEZ(self):
        for pay in (0.5, 0.8, 0.95, 0.999):
            oran = ZEMIN_KAPLAMA_TAVANI * pay
            with self.subTest(kaplama=round(oran, 3)):
                self.assertIsNone(zemin_maskesi_reddi(_kaplamali(oran)))

    def test_tavanin_USTUNDE_atesler(self):
        for carpan in (1.02, 1.2, 1.5, 1.8):
            oran = min(1.0, ZEMIN_KAPLAMA_TAVANI * carpan)
            with self.subTest(kaplama=round(oran, 3)):
                ret = zemin_maskesi_reddi(_kaplamali(oran))
                self.assertIsNotNone(ret)
                self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, ret[0])

    def test_tavanin_KENDISI_gecerlidir(self):
        """Sinirin kendisi reddedilmez; yalniz USTU reddedilir."""
        self.assertIsNone(zemin_maskesi_reddi(_kaplamali(ZEMIN_KAPLAMA_TAVANI)))

    def test_detay_OLCULEN_degeri_tasir(self):
        ret = zemin_maskesi_reddi(_kaplamali(0.80))
        self.assertIsNotNone(ret)
        self.assertIn("%80", ret[1])
        self.assertIn(f"%{100 * ZEMIN_KAPLAMA_TAVANI:.1f}", ret[1])


class AnalyzePathEntegrasyonTests(unittest.TestCase):

    def test_cokmus_maske_ROTA_URETMEZ(self):
        yol, guven, wps, ret = analyze_path(
            _kaplamali(0.90), return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps, "cokmus maskede waypoint uretildi")
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, ret[0])

    def test_saglikli_koridor_ETKILENMEZ(self):
        m = np.zeros((H, W), np.uint8)
        m[:, 100:320] = 1                       # kaplama ~%24
        yol, guven, wps, ret = analyze_path(
            m, return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(ret)
        self.assertEqual(1, yol)
        self.assertGreaterEqual(len(wps), 2)

    def test_kapi_ROTADAN_ONCE_calisir(self):
        """Cokmus maskede rota kurma asamasi HIC calismamali."""
        from unittest import mock
        import rpi_inference
        with mock.patch.object(rpi_inference, "_bagli_koridor_yolu") as rota:
            analyze_path(_kaplamali(0.90), return_reason=True,
                         min_area_ratio=0.001)
        self.assertEqual(
            0, rota.call_count,
            "kapi rotadan SONRA calisiyor — bosuna A* kosuluyor")

    def test_kapi_icerik_kutusunu_KULLANIR(self):
        """Letterbox dolgusu kaplamayi yapay olarak dusurmemeli."""
        yan = 1200
        m = np.zeros((yan, yan), np.uint8)
        # icerik yalniz orta serit; onun %90'i zemin
        x0, iw = 300, 600
        m[:, x0:x0 + int(iw * 0.9)] = 1
        self.assertIsNone(
            zemin_maskesi_reddi(m),
            "tuvalin tamami paydaya girerse cokme gizlenir")
        self.assertIsNotNone(
            zemin_maskesi_reddi(m, (x0, 0, iw, yan)),
            "icerik kutusu verilince cokme GORULMELI")

    def test_MADDE_15_kapi_maskeye_DOKUNMAZ(self):
        """Kapi yalniz reddeder; tek piksel eklemez/cikarmaz."""
        m = _kaplamali(0.90)
        kopya = m.copy()
        zemin_maskesi_reddi(m)
        analyze_path(m, return_reason=True, min_area_ratio=0.001)
        self.assertTrue(np.array_equal(kopya, m),
                        "kapi girdi maskesini DEGISTIRDI")


class OlculmusTabanTests(unittest.TestCase):
    """Esigin gerekcesi olculmus tabandan gelir — kayitla tutarli mi?"""

    def test_esik_olculen_MESRU_azaminin_USTUNDE(self):
        """Olculen en yuksek mesru kaplama: genel kapinin kendi sahneleri %42,6."""
        self.assertGreater(ZEMIN_KAPLAMA_TAVANI, 0.426)

    def test_esik_olculen_COKMUS_asgarisinin_ALTINDA(self):
        """Olculen en dusuk cokmus kaplama: v21 kompozit arena %76,0."""
        self.assertLess(ZEMIN_KAPLAMA_TAVANI, 0.760)

    def test_genel_kapi_sahneleri_kapidan_GECER(self):
        """`codes/test_rota_sentetik.py`'nin 15 sahnesi reddedilmemeli."""
        import test_rota_sentetik as trs
        en_yuksek = 0.0
        for harita in range(1, 6):
            for zorluk in ("kolay", "orta", "zor"):
                zemin = trs.sahne_uret(harita, zorluk)[1]
                oran = zemin_kaplamasi(zemin)
                en_yuksek = max(en_yuksek, oran)
                self.assertIsNone(
                    zemin_maskesi_reddi(zemin),
                    f"genel kapi sahnesi {harita}/{zorluk} reddedildi "
                    f"(kaplama %{100 * oran:.1f})")
        self.assertGreater(en_yuksek, 0.40,
                           "sahneler beklenenden dar — taban degismis olabilir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
