"""NEDEN: Fiziksel ölçek bilinmiyorsa 1,10 metrelik emniyet yarıçapı piksel
sanılamaz; güvenlik ölçümü karar üretmeden durmalı ve özet paydasını kirletmemelidir.
"""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from codes import test_rota_guvenlik as guvenlik


class _SahteModel:
    names = {}

    def predict(self, *args, **kwargs):
        return [SimpleNamespace()]


def _kayit(mpp, *, ham_ihlal=False, enj_ihlal=False,
           ham_karar=True, enj_karar=True):
    return {
        "mpp": mpp,
        "ham": {
            "ihlal": ham_ihlal,
            "karar_var": ham_karar,
            "durum": "ACIK",
        },
        "enj": {
            "ihlal": enj_ihlal,
            "karar_var": enj_karar,
            "durum": "ACIK",
        },
    }


class OlceksizGuvenlikTests(unittest.TestCase):
    def test_mpp_yokken_plan_ve_ihlal_karari_uretilmez(self):
        yol = np.ones((32, 32), dtype=np.uint8)
        engel = np.zeros((32, 32), dtype=np.uint8)

        with mock.patch.object(
                guvenlik, "get_masks", return_value={0: yol, 1: engel}), \
             mock.patch.object(
                 guvenlik, "_arac_ornek_maskeleri", return_value=[]), \
             mock.patch.object(
                 guvenlik, "mpp_arac_maskesinden", return_value=None), \
             mock.patch.object(guvenlik, "_rota_uret") as rota:
            sonuc = guvenlik.bir_kare_isle(
                np.zeros((18, 32, 3), dtype=np.uint8),
                _SahteModel(),
                _SahteModel(),
                imgsz=32,
            )

        rota.assert_not_called()
        self.assertIsNone(sonuc["mpp"])
        self.assertIsNone(sonuc["r_gerekli_px"])
        for kip in ("ham", "enj"):
            self.assertEqual("OLCEK_YOK", sonuc[kip]["durum"])
            self.assertFalse(sonuc[kip]["karar_var"])
            self.assertIsNone(sonuc[kip]["ihlal"])
            self.assertFalse(sonuc[kip]["olculebilir"])
            self.assertEqual("MPP_YOK", sonuc[kip]["olcum_disi_neden"])

    def test_olceksiz_zehir_kaydi_ihlal_paydasina_girmez(self):
        zehir = _kayit(None, ham_ihlal=True, enj_ihlal=True)
        zehir["ham"]["durum"] = "TOHUM_YOK"
        zehir["enj"]["durum"] = "TOHUM_YOK"
        sonuclar = [
            _kayit(0.1, ham_ihlal=True),
            _kayit(0.2, ham_ihlal=False),
            zehir,
        ]

        ozet = guvenlik._ozet_hesapla(sonuclar)

        self.assertEqual(3, ozet["n_kare"])
        self.assertEqual(2, ozet["olcekli_kare"])
        self.assertEqual(1, ozet["olceksiz_kare"])
        self.assertEqual("KISMI_OLCUM", ozet["olcum_durumu"])
        self.assertEqual(1, ozet["ihlal_sayisi_ham"])
        self.assertEqual(0, ozet["ihlal_sayisi_enjekte"])
        self.assertEqual(0.5, ozet["ihlal_orani_ham"])
        self.assertEqual(0.0, ozet["ihlal_orani_enjekte"])
        self.assertEqual(2, ozet["karar_sayisi_ham"])
        self.assertEqual(2, ozet["karar_sayisi_enjekte"])
        self.assertEqual(0, ozet["tohum_yok_ham"])
        self.assertEqual(0, ozet["tohum_yok_enjekte"])
        self.assertEqual(1, guvenlik._ozet_cikis_kodu(ozet))

    def test_tum_kareler_olceksizse_oran_null_olur(self):
        ozet = guvenlik._ozet_hesapla([
            _kayit(None, ham_ihlal=True, enj_ihlal=True),
            _kayit(None),
        ])

        self.assertEqual(0, ozet["olcekli_kare"])
        self.assertEqual(2, ozet["olceksiz_kare"])
        self.assertEqual("OLCUM_YOK", ozet["olcum_durumu"])
        self.assertIsNone(ozet["ihlal_orani_ham"])
        self.assertIsNone(ozet["ihlal_orani_enjekte"])
        self.assertIsNone(ozet["cekimserlik_ham"])
        self.assertIsNone(ozet["cekimserlik_enjekte"])
        self.assertEqual(1, guvenlik._ozet_cikis_kodu(ozet))


if __name__ == "__main__":
    unittest.main()
