"""NEDEN: n_waypoints rota guvenligini degil yalniz cikti yogunlugunu belirler.

T30 oncesinde ayni kivrimli koridor 8 bantta reddedilirken 16/24/32 bantta
acik sayiliyordu. Bu kapı hem eski salinimi pozitif kontrolle yeniden uretir,
hem yeni witness yolunun dort ornekleme degerinde ayni karari verdigini kanitlar.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import rpi_inference
from karar_sozlesmesi import (GORUS_HATTI_KOPUK_SEBEBI,
                              ROTA_PLAN_MAKS_HUCRE)


def _kivrimli_koridor(boyut=256):
    zemin = np.zeros((boyut, boyut), np.uint8)
    for y in range(boyut):
        merkez = int(128 + 60 * np.sin(y / boyut * 4 * np.pi))
        zemin[y, merkez - 12:merkez + 12] = 1
    return zemin


def _temizle(trav):
    h, w = trav.shape
    k_open = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)
    n_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    if n_lbl > 2:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        clean = (labels == largest).astype(np.uint8)
    return clean


def _eski_bant_zinciri_kuruldu_mu(clean, n_waypoints):
    """T30 oncesi bant-greedy zincirinin kararini pozitif kontrol icin uret."""
    h = clean.shape[0]
    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)
    waypoints = []
    for i in range(n_waypoints - 1, -1, -1):
        y0 = i * h // n_waypoints
        y1 = (i + 1) * h // n_waypoints
        band = dist[y0:y1, :]
        if band.size == 0 or band.max() <= 0.5:
            continue
        if not waypoints:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            waypoints.append((int(lx), int(y0 + ly)))
            continue
        aday = rpi_inference._bandda_gorunur_en_genis(
            band, y0, waypoints[-1], clean)
        if aday is None:
            return False
        waypoints.append(aday)
    return len(waypoints) >= 2


class OrneklemeKararliligiTests(unittest.TestCase):
    def test_kivrimli_koridorda_dort_ornekleme_ayni_guvenli_karari_verir(self):
        zemin = _kivrimli_koridor()
        clean_eski = _temizle(zemin)

        # Pozitif kontrol: eski algoritma ayni maskede gercekten saliniyordu.
        self.assertFalse(_eski_bant_zinciri_kuruldu_mu(clean_eski, 8))
        self.assertTrue(_eski_bant_zinciri_kuruldu_mu(clean_eski, 16))

        kararlar = []
        for n in (8, 16, 24, 32):
            with self.subTest(n_waypoints=n):
                yol, guven, wps, clean, ret = rpi_inference.analyze_path(
                    zemin, n_waypoints=n, return_clean=True,
                    return_reason=True)
                kararlar.append((yol, ret[0] if ret else None))
                self.assertEqual(2, yol)
                self.assertEqual(0.599, guven)
                self.assertIsNone(ret)
                self.assertGreaterEqual(len(wps), 2)
                self.assertTrue(
                    rpi_inference._kenarlar_guvenli(wps, clean), wps)

        self.assertEqual(1, len(set(kararlar)), kararlar)

    def test_witness_uretilemezse_kenar_degil_gorus_hatti_kopuk(self):
        zemin = np.zeros((128, 128), np.uint8)
        zemin[:, 40:88] = 1
        with mock.patch.object(rpi_inference, "astar", return_value=None):
            yol, guven, wps, ret = rpi_inference.analyze_path(
                zemin, return_reason=True)

        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps)
        self.assertEqual(GORUS_HATTI_KOPUK_SEBEBI, ret[0])
        self.assertIn("denenen_plan_adim_hucre", ret[1])

    def test_witness_gercek_icerik_uc_bantlarina_ankorlanir(self):
        zemin = np.zeros((1024, 1024), np.uint8)
        icerik = (0, 461, 1024, 102)
        zemin[461:563, 480:544] = 1

        bant_h = rpi_inference.hedef_bant_yuksekligi(icerik[3])
        for n in (2, 8, 32, 256):
            with self.subTest(n_waypoints=n):
                yol, _guven, wps, ret = rpi_inference.analyze_path(
                    zemin, n_waypoints=n, icerik=icerik,
                    return_reason=True)

                self.assertEqual(2, yol)
                self.assertIsNone(ret)
                self.assertGreaterEqual(len(wps), 2)
                self.assertGreaterEqual(
                    wps[0][1], icerik[1] + icerik[3] - bant_h)
                self.assertLess(wps[-1][1], icerik[1] + bant_h)

    def test_astar_denemeleri_toplam_hucre_butcesini_asmaz(self):
        koridor = np.ones((512, 512), np.uint8)
        dist = np.ones_like(koridor, dtype=np.float32)
        gorulen_hucreler = []

        def _yol_yok(gecilebilir, *_args, **_kwargs):
            gorulen_hucreler.append(int(gecilebilir.size))
            return None

        with mock.patch.object(rpi_inference, "astar", side_effect=_yol_yok):
            yol, detay = rpi_inference._bagli_koridor_yolu(
                koridor, (0, 0, 512, 512), dist, ilk_plan_adimi=8)

        self.assertIsNone(yol)
        self.assertTrue(gorulen_hucreler)
        self.assertLessEqual(sum(gorulen_hucreler), ROTA_PLAN_MAKS_HUCRE)
        self.assertNotIn(512 * 512, gorulen_hucreler)
        self.assertIn(f"plan_hucre_butcesi={ROTA_PLAN_MAKS_HUCRE}", detay)


if __name__ == "__main__":
    unittest.main(verbosity=2)
