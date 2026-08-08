"""NEDEN: Rota güvenlik ölçümündeki letterbox tohumları ve özet sözleşmesi
üretim koordinatlarıyla aynı kalmalıdır; bu testler sessiz sapmaları yakalar."""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from codes import test_rota_guvenlik as guvenlik


class _SahteTensor:
    def __init__(self, veri):
        self._veri = np.asarray(veri)

    def cpu(self):
        return self

    def numpy(self):
        return self._veri


class _SahteModel:
    names = {}

    def predict(self, *args, **kwargs):
        return [SimpleNamespace()]


class IcerikTohumuTests(unittest.TestCase):
    def test_dota_obb_arac_poligonlarini_tekil_maskeler_yapar(self):
        sonuc = SimpleNamespace(
            obb=SimpleNamespace(
                cls=_SahteTensor([10, 2]),
                xyxyxyxy=_SahteTensor([
                    [[4, 5], [11, 5], [11, 14], [4, 14]],
                    [[20, 20], [25, 20], [25, 25], [20, 25]],
                ]),
            ),
            masks=None,
            boxes=None,
        )

        maskeler = guvenlik._arac_ornek_maskeleri(
            [sonuc], {10: "small vehicle", 2: "plane"}, 32, 32)

        self.assertEqual(1, len(maskeler))
        self.assertEqual((32, 32), maskeler[0].shape)
        self.assertEqual(1, int(maskeler[0][8, 7]))
        self.assertEqual(0, int(maskeler[0][22, 22]))

    def test_eski_coco_segmentasyonunu_tekil_maskelerle_destekler(self):
        ham_maskeler = np.zeros((2, 8, 8), dtype=np.float32)
        ham_maskeler[0, 1:4, 2:6] = 1.0
        ham_maskeler[1, 5:7, 5:7] = 1.0
        sonuc = SimpleNamespace(
            obb=None,
            masks=SimpleNamespace(data=_SahteTensor(ham_maskeler)),
            boxes=SimpleNamespace(cls=_SahteTensor([2, 0])),
        )

        maskeler = guvenlik._arac_ornek_maskeleri(
            [sonuc], {0: "person", 2: "car"}, 16, 16)

        self.assertEqual(1, len(maskeler))
        self.assertTrue(maskeler[0][3:8, 4:12].any())
        self.assertFalse(maskeler[0][11:, 11:].any())

    def test_arac_kahini_ham_planlayiciya_sizmaz(self):
        yol = np.ones((32, 32), dtype=np.uint8)
        engel = np.zeros((32, 32), dtype=np.uint8)
        arac = np.zeros((32, 32), dtype=np.uint8)
        arac[10:18, 12:20] = 1
        rota_yok = {"durum": "KAPALI", "waypoints_px": []}

        with mock.patch.object(
                guvenlik, "get_masks", return_value={0: yol, 1: engel}), \
             mock.patch.object(
                 guvenlik, "_arac_ornek_maskeleri", return_value=[arac]), \
             mock.patch.object(
                 guvenlik, "mpp_arac_maskesinden", return_value=0.1), \
             mock.patch.object(
                 guvenlik, "_rota_uret", side_effect=[rota_yok, rota_yok]) as rota:
            guvenlik.bir_kare_isle(
                np.zeros((18, 32, 3), dtype=np.uint8),
                _SahteModel(),
                _SahteModel(),
                imgsz=32,
            )

        ham_maskeler = rota.call_args_list[0].args[0]
        enjekte_maskeler = rota.call_args_list[1].args[0]
        self.assertFalse(ham_maskeler[1].any())
        self.assertTrue(enjekte_maskeler[1][10:18, 12:20].all())

    def test_yatay_letterbox_tohumlari_icerikte_kalir(self):
        gecilebilir = np.zeros((896, 896), dtype=np.uint8)
        icerik = (0, 196, 896, 504)
        gecilebilir[196:700, :] = 1

        alt = guvenlik._merkez_tohumu(
            gecilebilir, "alt", yaricap_px=3, icerik=icerik)
        ust = guvenlik._merkez_tohumu(
            gecilebilir, "ust", yaricap_px=3, icerik=icerik)

        self.assertTrue(alt.any())
        self.assertTrue(ust.any())
        self.assertFalse(alt[:196, :].any())
        self.assertFalse(alt[700:, :].any())
        self.assertFalse(ust[:196, :].any())
        self.assertFalse(ust[700:, :].any())
        self.assertGreaterEqual(int(np.nonzero(alt)[0].max()), 696)
        self.assertLessEqual(int(np.nonzero(ust)[0].min()), 199)

    def test_dikey_letterbox_tohumlari_yatay_dolgudan_uzak_kalir(self):
        gecilebilir = np.zeros((896, 896), dtype=np.uint8)
        icerik = (196, 0, 504, 896)
        gecilebilir[:, 196:700] = 1

        alt = guvenlik._merkez_tohumu(
            gecilebilir, "alt", yaricap_px=3, icerik=icerik)
        ust = guvenlik._merkez_tohumu(
            gecilebilir, "ust", yaricap_px=3, icerik=icerik)

        self.assertTrue(alt.any())
        self.assertTrue(ust.any())
        self.assertFalse(alt[:, :196].any())
        self.assertFalse(alt[:, 700:].any())
        self.assertFalse(ust[:, :196].any())
        self.assertFalse(ust[:, 700:].any())

    def test_bos_bant_tohum_yok_durumu_uretir(self):
        sahte_sonuc = {
            "olcek": {
                "plan_m_hucre": 0.1,
                "mpp": 0.1,
                "r_gerekli_px": 1.0,
            },
            "sekil": (32, 32),
            "dt_px": np.zeros((32, 32), dtype=np.float32),
        }
        with mock.patch.object(
                guvenlik, "serbest_alan", return_value=sahte_sonuc):
            sonuc = guvenlik._rota_uret(
                {0: np.zeros((32, 32), np.uint8)},
                mpp=0.1,
                icerik=(0, 8, 32, 16),
            )

        self.assertEqual("TOHUM_YOK", sonuc["durum"])
        self.assertEqual(["alt", "ust"], sonuc["tohum_yok_taraflar"])

    def test_plan_izgarasinda_kaybolan_tohum_tohum_yok_olur(self):
        sahte_sonuc = {
            "olcek": {
                "plan_m_hucre": 0.2,
                "mpp": 0.1,
                "r_gerekli_px": 1.0,
            },
            "sekil": (8, 8),
            "dt_px": np.full((8, 8), 2.0, dtype=np.float32),
        }
        plan_dt = np.zeros((4, 4), dtype=np.float32)

        with mock.patch.object(
                guvenlik, "serbest_alan", return_value=sahte_sonuc), \
             mock.patch.object(
                 guvenlik, "plan_izgarasi", return_value=(plan_dt, None)):
            sonuc = guvenlik._rota_uret(
                {0: np.ones((8, 8), np.uint8)},
                mpp=0.1,
                icerik=(0, 0, 8, 8),
            )

        self.assertEqual("TOHUM_YOK", sonuc["durum"])
        self.assertEqual(["alt", "ust"], sonuc["tohum_yok_taraflar"])

    def test_ozet_tohum_yok_sayaclarini_ayri_tutar(self):
        sonuclar = [
            {
                "ham": {"ihlal": False, "karar_var": False,
                        "durum": "TOHUM_YOK"},
                "enj": {"ihlal": False, "karar_var": True, "durum": "ACIK"},
                "mpp": 0.1,
            },
            {
                "ham": {"ihlal": True, "karar_var": True, "durum": "ACIK"},
                "enj": {"ihlal": False, "karar_var": False,
                        "durum": "TOHUM_YOK"},
                "mpp": 0.1,
            },
        ]

        ozet = guvenlik._ozet_hesapla(sonuclar)

        self.assertEqual(1, ozet["tohum_yok_ham"])
        self.assertEqual(1, ozet["tohum_yok_enjekte"])
        self.assertEqual(0.5, ozet["ihlal_orani_ham"])


if __name__ == "__main__":
    unittest.main()
