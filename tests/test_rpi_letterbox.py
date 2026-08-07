"""RPi çıkarım hattındaki letterbox ön işlemesinin regresyon testleri."""

import unittest

import numpy as np

from codes.rpi_inference import (
    INFER_SIZE,
    _maskeleri_icerige_kirp,
    _preprocess,
    analyze_path,
)


class LetterboxPreprocessTests(unittest.TestCase):
    def test_yatay_goruntu_kirpilmaz(self):
        goruntu = np.full((12, 20, 3), 200, dtype=np.uint8)

        tuval, kucuk, icerik = _preprocess(goruntu)

        self.assertEqual((0, 4, 20, 12), icerik)
        self.assertEqual((20, 20, 3), tuval.shape)
        self.assertEqual((INFER_SIZE, INFER_SIZE, 3), kucuk.shape)
        np.testing.assert_array_equal(tuval[4:16, :], goruntu)
        self.assertTrue(np.all(tuval[:4, :] == 114))
        self.assertTrue(np.all(tuval[16:, :] == 114))

    def test_dikey_goruntu_kirpilmaz(self):
        goruntu = np.full((20, 12, 3), 200, dtype=np.uint8)

        tuval, _, icerik = _preprocess(goruntu)

        self.assertEqual((4, 0, 12, 20), icerik)
        self.assertEqual((20, 20, 3), tuval.shape)
        np.testing.assert_array_equal(tuval[:, 4:16], goruntu)
        self.assertTrue(np.all(tuval[:, :4] == 114))
        self.assertTrue(np.all(tuval[:, 16:] == 114))

    def test_maskeler_letterbox_dolgusundan_temizlenir(self):
        maskeler = {
            0: np.ones((8, 8), dtype=np.uint8),
            1: np.ones((8, 8), dtype=np.uint8),
        }

        sonuc = _maskeleri_icerige_kirp(maskeler, (0, 2, 8, 4))

        for maske in sonuc.values():
            self.assertEqual(32, int(maske.sum()))
            self.assertTrue(np.all(maske[:2, :] == 0))
            self.assertTrue(np.all(maske[2:6, :] == 1))
            self.assertTrue(np.all(maske[6:, :] == 0))

    def test_portre_icerigin_sag_koridoru_sag_karari_uretir(self):
        # 576x1024 portre goruntu 1024 kare tuvalde x=[224,800) araligindadir.
        # Koridorun merkezi icerigin %75'inde (net SAG), fakat kare tuvalin eski
        # 2/3 siniri olan x=682.7'nin solunda kaldigi icin eski hesap ORTA derdi.
        maske = np.zeros((1024, 1024), dtype=np.uint8)
        icerik = (224, 0, 576, 1024)
        maske[:, 627:685] = 1

        eski_tuval_karari, _, _ = analyze_path(maske)
        icerik_karari, guven, waypoints = analyze_path(maske, icerik=icerik)

        self.assertEqual(2, eski_tuval_karari)
        self.assertEqual(3, icerik_karari)
        self.assertEqual(1.0, guven)
        self.assertTrue(waypoints)

    def test_minimum_alan_esigi_letterbox_icerik_alanini_kullanir(self):
        # Portre içerik 576x1024'tür. 28x316 koridor gerçek içeriğin %1,5001'i,
        # fakat 1024x1024 tuvalin yalnız %0,844'üdür. Eski tuval paydası %1
        # eşiğinde kararı reddederken içerik paydası karar üretmelidir.
        maske = np.zeros((1024, 1024), dtype=np.uint8)
        icerik = (224, 0, 576, 1024)
        maske[300:616, 636:664] = 1

        tuval_karari, _, _ = analyze_path(maske, min_area_ratio=0.01)
        icerik_karari, guven, waypoints = analyze_path(
            maske,
            min_area_ratio=0.01,
            icerik=icerik,
        )

        self.assertAlmostEqual(
            0.015,
            float(maske.sum()) / (icerik[2] * icerik[3]),
            places=5,
        )
        self.assertIsNone(tuval_karari)
        self.assertEqual(3, icerik_karari)
        self.assertGreater(guven, 0.0)
        self.assertTrue(waypoints)


if __name__ == "__main__":
    unittest.main()
