"""NEDEN: Letterbox dolgusu rota geometrisini veya fail-closed karari bozmamali."""

import unittest

import numpy as np

from codes.costmap_path_finder import (analyze_path_uyumlu, rota_bul,
                                       serbest_alan)
from codes.rpi_inference import _preprocess


def _uc_koridorlu_sahne():
    """Dolguda iki kapali, ortasi acik uc koridorlu deterministik arena."""
    ham_kare = np.full((288, 512, 3), 127, np.uint8)
    tuval, _kucuk, icerik = _preprocess(ham_kare)
    tuval_boyutu = tuval.shape[0]
    zemin = np.zeros((tuval_boyutu, tuval_boyutu), np.uint8)
    engel = np.zeros_like(zemin)
    for x0, x1 in ((40, 140), (206, 306), (372, 472)):
        zemin[112:400, x0:x1] = 1
    engel[290:320, 35:145] = 1
    engel[290:320, 367:477] = 1
    return {0: zemin, 1: engel}, icerik


class CostmapLetterboxIcerikTests(unittest.TestCase):
    def test_dolgulu_girdi_eski_ve_icerikli_davranisi_kilitler(self):
        maskeler, icerik = _uc_koridorlu_sahne()

        eski = rota_bul(maskeler, mpp=None, plan=False)
        yeni = rota_bul(maskeler, mpp=None, plan=False, icerik=icerik)

        self.assertEqual("KAPALI_DAR", eski["durum"])
        self.assertIsNone(eski["yol_no"])
        self.assertEqual("ACIK", yeni["durum"])
        self.assertEqual(2, yeni["yol_no"])

    def test_icerik_none_geriye_uyumlu_tam_tuvaldir(self):
        maskeler, _icerik = _uc_koridorlu_sahne()
        h, w = maskeler[0].shape

        varsayilan = rota_bul(maskeler, mpp=None, plan=False)
        tam_tuval = rota_bul(
            maskeler, mpp=None, plan=False, icerik=(0, 0, w, h))

        self.assertEqual(varsayilan["durum"], tam_tuval["durum"])
        self.assertEqual(varsayilan["yol_no"], tam_tuval["yol_no"])
        self.assertEqual(
            [(a["etiket"], a["gecilebilir"]) for a in varsayilan["adaylar"]],
            [(a["etiket"], a["gecilebilir"]) for a in tam_tuval["adaylar"]],
        )

    def test_roi_serbest_alani_buyutmez_ve_k2_yalniz_cikarir(self):
        zemin = np.ones((80, 80), np.uint8)
        engelsiz = np.zeros_like(zemin)
        engelli = np.zeros_like(zemin)
        engelli[30:50, 35:45] = 1
        icerik = (10, 20, 60, 40)

        eski_k1 = serbest_alan({0: zemin, 1: engelsiz}, mpp=None)
        yeni_k1 = serbest_alan(
            {0: zemin, 1: engelsiz}, mpp=None, icerik=icerik)
        yeni_k2 = serbest_alan(
            {0: zemin, 1: engelli}, mpp=None, icerik=icerik)

        self.assertLessEqual(
            int(np.count_nonzero(yeni_k1["serbest"])),
            int(np.count_nonzero(eski_k1["serbest"])),
        )
        self.assertFalse(np.any(
            (yeni_k1["serbest"] > 0) & (eski_k1["serbest"] == 0)))
        self.assertFalse(np.any(
            (yeni_k2["serbest"] > 0) & (yeni_k1["serbest"] == 0)))

        roi_disi = np.ones_like(zemin, dtype=bool)
        x0, y0, w, h = icerik
        roi_disi[y0:y0 + h, x0:x0 + w] = False
        self.assertFalse(np.any(yeni_k1["serbest"][roi_disi]))

    def test_belirsiz_coklu_fail_closed_kalir(self):
        tuval_boyutu = 160
        icerik = (0, 20, tuval_boyutu, 120)
        zemin = np.zeros((tuval_boyutu, tuval_boyutu), np.uint8)
        for x0, x1 in ((8, 32), (46, 70), (88, 112), (128, 152)):
            zemin[20:140, x0:x1] = 1

        sonuc = rota_bul(
            {0: zemin, 1: np.zeros_like(zemin)},
            mpp=None,
            plan=False,
            icerik=icerik,
        )

        self.assertEqual("BELIRSIZ_COKLU", sonuc["durum"])
        self.assertIsNone(sonuc["yol_no"])
        self.assertEqual([], sonuc["waypoints_px"])
        self.assertEqual(4, len(sonuc["adaylar"]))

    def test_gecersiz_icerik_kutulari_fail_closed_kalir(self):
        zemin = np.ones((64, 64), np.uint8)
        maskeler = {0: zemin, 1: np.zeros_like(zemin)}
        gecersiz_kutular = {
            "nesne_degil": object(),
            "eksik_alan": (0, 0, 64),
            "fazla_alan": (0, 0, 64, 64, 1),
            "bos_genislik": (0, 0, 0, 64),
            "bos_yukseklik": (0, 0, 64, 0),
            "negatif_x": (-1, 0, 64, 64),
            "negatif_y": (0, -1, 64, 64),
            "saga_tasan": (0, 0, 65, 64),
            "alta_tasan": (0, 0, 64, 65),
            "kesirli": (0.0, 0, 64, 64),
            "python_bool": (False, 0, 64, 64),
            "numpy_bool": (np.bool_(False), 0, 64, 64),
            "nan": (np.nan, 0, 64, 64),
            "inf": (np.inf, 0, 64, 64),
            "metin": ("0", 0, 64, 64),
            "sozluk": {0: 0, 1: 0, 2: 64, 3: 64},
            "kume": {0, 1, 63, 64},
            "uretec": (v for v in (0, 0, 64, 64)),
            "iki_boyutlu_dizi": np.array([[0, 0], [64, 64]]),
        }

        for ad, icerik in gecersiz_kutular.items():
            with self.subTest(ad=ad):
                sonuc = rota_bul(
                    maskeler, mpp=None, plan=False, icerik=icerik)
                self.assertEqual("MASKE_YOK", sonuc["durum"])
                self.assertIsNone(sonuc["yol_no"])
                self.assertEqual([], sonuc["waypoints_px"])

    def test_numpy_tamsayi_icerik_kutusu_kabul_edilir(self):
        zemin = np.ones((64, 64), np.uint8)
        icerik = tuple(np.int64(v) for v in (8, 8, 48, 48))

        sonuc = serbest_alan(
            {0: zemin, 1: np.zeros_like(zemin)},
            mpp=None,
            icerik=icerik,
        )

        self.assertEqual((8, 8, 48, 48), sonuc["icerik"])
        self.assertEqual(48 * 48, int(np.count_nonzero(sonuc["serbest"])))

    def test_uyumluluk_koprusu_temiz_maskede_icerigi_korur(self):
        maskeler, icerik = _uc_koridorlu_sahne()
        x0, y0, w, h = icerik
        roi_disi = np.ones_like(maskeler[0], dtype=bool)
        roi_disi[y0:y0 + h, x0:x0 + w] = False
        # Eski uyumluluk fallback'i bu kasitli dolgu tespitlerini yeniden
        # serbest sayiyordu; test kusuru gercekten oldurmek icin dolgu bos degil.
        maskeler[0][roi_disi] = 1

        yol, _guven, _waypoints, temiz = analyze_path_uyumlu(
            maskeler, return_clean=True, mpp=0.1, icerik=icerik)
        dogrudan = rota_bul(
            maskeler,
            mpp=0.1,
            plan=True,
            gorsel_cikti=True,
            icerik=icerik,
        )

        self.assertEqual(2, yol)
        np.testing.assert_array_equal(dogrudan["serbest"], temiz)
        self.assertFalse(np.any(temiz[roi_disi]))

    def test_a_star_tohumlari_da_icerik_uclarindan_kurulur(self):
        maskeler, icerik = _uc_koridorlu_sahne()

        sonuc = rota_bul(maskeler, mpp=0.1, plan=True, icerik=icerik)

        self.assertEqual("ACIK", sonuc["durum"])
        self.assertEqual(2, sonuc["yol_no"])
        self.assertTrue(sonuc["waypoints_px"])
        x0, y0, w, h = icerik
        self.assertTrue(all(
            x0 <= x < x0 + w and y0 <= y < y0 + h
            for x, y in sonuc["waypoints_px"]
        ))
        self.assertEqual([], sonuc["ihlaller"])


if __name__ == "__main__":
    unittest.main()
