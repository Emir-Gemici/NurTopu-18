"""RPi çıkarım hattındaki letterbox ön işlemesinin regresyon testleri."""

import unittest

import numpy as np

from codes.rpi_inference import (
    INFER_SIZE,
    _maskeleri_icerige_kirp,
    _preprocess,
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


if __name__ == "__main__":
    unittest.main()
