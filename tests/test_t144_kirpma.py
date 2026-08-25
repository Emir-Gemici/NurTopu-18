"""
T144 (D-284): `dataset/download_and_convert.py` poligon tavani ALAN sirali olmali.

Kusur: eski kod `sorted(lines, key=len)` ile SATIR UZUNLUGUNA (kose sayisina)
gore siraliyordu; buyuk ama az koseli bina poligonu atilip 200 px'lik cok
koseli kiriklar tutuluyordu (13077_lab.png: 94.997 px'in 85.895'i atildi).
Sentetik kume: 1 BUYUK dortgen (4 kose) + 20 KUCUK cok koseli poligon, tavan 15
-> buyuk olan KALMALI. Mutasyon (siralama len'e donerse) bu testi dusurur.
"""

import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from dataset import download_and_convert as D

TAVAN = 15


def _buyuk_dortgen():
    # 4 kose, kenar 0,6 x 0,6 -> alan (0,6*512)^2 = 94.371 px
    return "1 0.100000 0.100000 0.700000 0.100000 0.700000 0.700000 0.100000 0.700000"


def _kucuk_cokgen(i, n_kose=24, r=0.02):
    # Cok koseli (uzun satir) ama kucuk daire; merkez izgara uzerinde
    cx, cy = 0.05 + 0.04 * (i % 10), 0.85 + 0.05 * (i // 10)
    pts = [(cx + r * math.cos(2 * math.pi * k / n_kose),
            cy + r * math.sin(2 * math.pi * k / n_kose)) for k in range(n_kose)]
    return "1 " + " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)


class T144AlanSiraliKirpma(unittest.TestCase):

    def setUp(self):
        self.kucukler = [_kucuk_cokgen(i) for i in range(20)]
        self.buyuk = _buyuk_dortgen()
        # buyuk ORTAYA konur ki "ilk N" gibi bir sira etkisi de yakalansin
        self.lines = self.kucukler[:10] + [self.buyuk] + self.kucukler[10:]

    def test_buyuk_poligon_satir_uzunlugu_kisa_olsa_da_KALIR(self):
        self.assertLess(len(self.buyuk), min(len(k) for k in self.kucukler),
                        "on kosul: buyuk poligonun satiri kucuklerden KISA olmali")
        tutulan, k = D.alana_gore_kirp(self.lines, TAVAN)
        self.assertEqual(TAVAN, len(tutulan))
        self.assertIn(self.buyuk, tutulan, "94k px bina atildi, kirik yamalar kaldi (D-284)")
        self.assertTrue(k["asti"])
        self.assertEqual(21 - TAVAN, k["atilan_poligon"])
        # atilan alan orani kucuk olmali (yalniz kucukler atildi)
        self.assertLess(k["atilan_alan"] / k["toplam_alan"], 0.05)

    def test_tavan_altinda_hicbir_sey_atilmaz(self):
        tutulan, k = D.alana_gore_kirp(self.lines[:5], TAVAN)
        self.assertEqual(5, len(tutulan))
        self.assertFalse(k["asti"])
        self.assertEqual(0, k["atilan_poligon"])
        self.assertEqual(0.0, k["atilan_alan"])

    def test_poligon_alani_contourArea_ile_uyumlu(self):
        beklenen = (0.6 * D.IMG_SIZE) ** 2
        self.assertAlmostEqual(beklenen, D.poligon_alani(self.buyuk), delta=1.0)

    def test_process_split_kirpmasi_alan_sirali(self):
        """Ucuca: process_split'in gercek yolu — 1 buyuk + 20 kucuk engel bilesenli maske."""
        from PIL import Image
        blocked_id = sorted(D.BLOCKED_HAM)[0]
        lbl = np.zeros((D.IMG_SIZE, D.IMG_SIZE), np.uint8)
        lbl[40:340, 40:340] = blocked_id                      # buyuk: 90.000 px, 4 kose
        yy, xx = np.ogrid[:D.IMG_SIZE, :D.IMG_SIZE]
        for i in range(20):                                    # kucuk: ~314 px daireler (birbirine degmez)
            cx, cy = 20 + 24 * i, 470
            lbl[(xx - cx) ** 2 + (yy - cy) ** 2 <= 10 ** 2] = blocked_id
        img = Image.fromarray(np.zeros((D.IMG_SIZE, D.IMG_SIZE, 3), np.uint8))
        sample = [{"image": img, "label": Image.fromarray(lbl)}]
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            st = D.process_split(sample, "t144", td / "img", td / "lbl")
            satirlar = (td / "lbl" / "t144_00000.txt").read_text().splitlines()
        self.assertEqual(1, st["blocked_tavan_asan"])
        self.assertEqual(D.MAX_POLYGONS // 2, st["blocked_instances"])
        alanlar = sorted(D.poligon_alani(s) for s in satirlar if s.startswith("1 "))
        self.assertGreater(alanlar[-1], 80_000, "buyuk engel bileseni etikette YOK")
        self.assertLess(st["blocked_atilan_alan_px"] / st["blocked_alan_px"], 0.05)


if __name__ == "__main__":
    unittest.main()
