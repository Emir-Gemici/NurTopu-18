"""NEDEN: Doğruluk ölçümü üretimdeki karar fonksiyonundan ayrılamaz."""

import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "codes"))

import rpi_inference  # noqa: E402
import test_accuracy  # noqa: E402


def _eski_karar(mask):
    """Yalnız önce/sonra kanıtı için T8 öncesi üç-bölge kararını dondur."""
    h, w = mask.shape
    k_open = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)
    top = clean[:int(h * 0.4), :]
    thirds = [
        int(top[:, :w // 3].sum()),
        int(top[:, w // 3:2 * w // 3].sum()),
        int(top[:, 2 * w // 3:].sum()),
    ]
    total = sum(thirds)
    if total == 0:
        return None, 0.0
    decision = int(np.argmax(thirds)) + 1
    return decision, round(thirds[decision - 1] / total, 3)


class AccuracyProductionPathTests(unittest.TestCase):
    def test_analyze_path_uretim_fonksiyonunun_aynisidir(self):
        self.assertIs(test_accuracy.analyze_path, rpi_inference.analyze_path)

    def test_infer_frame_letterbox_icerigini_uretim_fonksiyonuna_aktarir(self):
        image = np.zeros((20, 12, 3), dtype=np.uint8)
        model = mock.Mock()
        model.predict.return_value = []
        masks = {
            0: np.ones((20, 20), dtype=np.uint8),
            1: np.zeros((20, 20), dtype=np.uint8),
        }

        with (
            mock.patch.object(test_accuracy, "get_masks", return_value=masks),
            mock.patch.object(
                test_accuracy,
                "analyze_path",
                return_value=(2, 1.0, [(10, 19), (10, 0)]),
            ) as analyze,
        ):
            test_accuracy._infer_frame(model, image, conf=0.30)

        self.assertEqual((4, 0, 12, 20), analyze.call_args.kwargs["icerik"])
        verilen_maske = analyze.call_args.args[0]
        self.assertEqual(240, int(verilen_maske.sum()))
        self.assertTrue(np.all(verilen_maske[:, :4] == 0))
        self.assertTrue(np.all(verilen_maske[:, 16:] == 0))

    def test_uc_ayrisma_senaryosu_uretim_karariyla_birlesir(self):
        orta_ve_sol_gurultu = np.zeros((300, 300), dtype=np.uint8)
        orta_ve_sol_gurultu[:, 130:170] = 1
        orta_ve_sol_gurultu[:80, :100] = 1

        kucuk_gurultu = np.zeros((300, 300), dtype=np.uint8)
        kucuk_gurultu[:30, 10:20] = 1

        iki_kollu_tek_bilesen = np.zeros((300, 300), dtype=np.uint8)
        iki_kollu_tek_bilesen[:100, 10:20] = 1
        iki_kollu_tek_bilesen[:100, 220:245] = 1
        iki_kollu_tek_bilesen[90:110, 10:245] = 1
        iki_kollu_tek_bilesen[100:, 140:160] = 1

        senaryolar = [
            ("S1", orta_ve_sol_gurultu, 2),
            ("S2", kucuk_gurultu, None),
            ("S3", iki_kollu_tek_bilesen, 2),
        ]
        once_dogru = 0
        sonra_dogru = 0
        for ad, maske, beklenen in senaryolar:
            once, once_guven = _eski_karar(maske)
            sonra, sonra_guven, _ = test_accuracy.analyze_path(maske)
            once_dogru += int(once == beklenen)
            sonra_dogru += int(sonra == beklenen)
            print(
                f"[ONCE/SONRA] {ad}: {once}/{once_guven:.3f} -> "
                f"{sonra}/{sonra_guven:.3f} (beklenen={beklenen})"
            )
            self.assertEqual(beklenen, sonra)

        print(
            "[ONCE/SONRA] uretim karariyla uyum: "
            f"{once_dogru}/3 -> {sonra_dogru}/3"
        )
        self.assertEqual(0, once_dogru)
        self.assertEqual(3, sonra_dogru)


if __name__ == "__main__":
    unittest.main(verbosity=2)
