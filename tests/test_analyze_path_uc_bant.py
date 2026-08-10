"""NEDEN: Bagli bir koridor yalniz kendi icinde guvenli olabilir; ayni bilesen
baslangic ve hedef kenarlarina ulasmiyorsa OPEN_ROUTE uretmek kapali seridi acik
raporlar (T26 / REVIEW_LOG D-29, D-30).
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import BANT_TEMAS_MIN_ORANI, HEDEF_BANT_ORANI
import rpi_inference
from rpi_inference import _uc_bant_temasi_yeterli, analyze_path


def _duz_koridor(boyut=640):
    zemin = np.zeros((boyut, boyut), np.uint8)
    zemin[:, 260:380] = 1
    return zemin


class UcBantKapisiTests(unittest.TestCase):
    def test_mutasyon_uc_kapisi_kaldirilirsa_eski_kusur_geri_doner(self):
        """Pozitif kontrol: K-A savunmalari kaldirilinca sahne yol=2 der."""
        zemin = _duz_koridor()
        engel = np.zeros_like(zemin)
        engel[300:340, :] = 1

        sahte_zincir = [(320, 280), (320, 20)]
        with mock.patch.object(
                rpi_inference, "_uc_bant_temasi_yeterli", return_value=True), \
             mock.patch.object(
                rpi_inference, "_bagli_koridor_yolu",
                return_value=(sahte_zincir, None)):
            yol, guven, waypoints = analyze_path(zemin, engel_mask=engel)

        self.assertEqual(2, yol)
        self.assertEqual(1.0, guven)
        self.assertGreaterEqual(len(waypoints), 2)

    def test_bariyerli_koridor_hedefe_bagli_sayilmaz(self):
        zemin = _duz_koridor()
        engel = np.zeros_like(zemin)
        engel[300:340, :] = 1

        yol, guven, waypoints = analyze_path(zemin, engel_mask=engel)

        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], waypoints)

    def test_bariyersiz_ayni_koridor_orta_yolu_korur(self):
        yol, guven, waypoints = analyze_path(_duz_koridor())

        self.assertEqual(2, yol)
        self.assertEqual(1.0, guven)
        self.assertGreaterEqual(len(waypoints), 6)

    def test_rette_return_clean_dortlu_donusu_korur(self):
        zemin = _duz_koridor()
        engel = np.zeros_like(zemin)
        engel[300:340, :] = 1

        yol, guven, waypoints, clean = analyze_path(
            zemin, engel_mask=engel, return_clean=True)

        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], waypoints)
        self.assertGreater(int(clean.sum()), 0)

    def test_letterbox_tuvali_degil_icerik_uclari_kullanilir(self):
        tuval = np.zeros((1024, 1024), np.uint8)
        icerik = (0, 224, 1024, 576)
        tuval[224:800, 420:604] = 1

        yol, guven, waypoints = analyze_path(tuval, icerik=icerik)

        self.assertEqual(2, yol)
        self.assertGreaterEqual(guven, 0.99)
        self.assertGreaterEqual(len(waypoints), 6)

    def test_tek_piksel_temas_sozlesme_esigini_gecmez(self):
        koridor = np.zeros((100, 100), np.uint8)
        bant_h = max(1, int(100 * HEDEF_BANT_ORANI))
        koridor[:bant_h, 50] = 1
        self.assertFalse(_uc_bant_temasi_yeterli(
            koridor, (0, 0, 100, 100), "ust"))

        gereken = int(np.ceil(100 * BANT_TEMAS_MIN_ORANI))
        koridor[:bant_h, 50:50 + gereken] = 1
        self.assertTrue(_uc_bant_temasi_yeterli(
            koridor, (0, 0, 100, 100), "ust"))

    def test_bilinmeyen_bant_tarafi_reddedilir(self):
        with self.assertRaises(ValueError):
            _uc_bant_temasi_yeterli(
                np.ones((16, 16), np.uint8), (0, 0, 16, 16), "yan")


if __name__ == "__main__":
    unittest.main(verbosity=2)
