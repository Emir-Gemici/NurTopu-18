"""NEDEN: Rota guven kapisi NaN/sonsuz gibi karsilastirmadan sizan degerleri
OPEN_ROUTE saymamali; esigin tam kendisi ise sozlesme geregi gecmelidir.
"""

import math
import unittest

from codes.karar_sozlesmesi import (
    DUSUK_GUVEN_SEBEBI,
    ROTA_GUVEN_ESIGI,
    rota_guven_reddi,
    rota_guveni_yeterli_mi,
)

ESIK_ALTI = ROTA_GUVEN_ESIGI - 0.001


class RotaGuvenSozlesmesiTests(unittest.TestCase):
    def test_esik_alti_reddedilir_esik_ve_ustu_gecer(self):
        hemen_alti = math.nextafter(ROTA_GUVEN_ESIGI, -math.inf)
        self.assertIsNotNone(rota_guven_reddi(hemen_alti))
        self.assertTrue(rota_guveni_yeterli_mi(ROTA_GUVEN_ESIGI))
        self.assertTrue(rota_guveni_yeterli_mi(1.0))

    def test_gecersiz_degerler_fail_closed_reddedilir(self):
        for deger in (None, True, False, "0.9", "abc", math.nan, math.inf,
                      -math.inf, -0.1, 1.1):
            with self.subTest(deger=deger):
                ret = rota_guven_reddi(deger)
                self.assertIsNotNone(ret)
                self.assertEqual(DUSUK_GUVEN_SEBEBI, ret[0])
                self.assertFalse(rota_guveni_yeterli_mi(deger))

    def test_ret_detayi_olculen_deger_ve_esigi_tasir(self):
        sebep, detay = rota_guven_reddi(ESIK_ALTI)
        self.assertEqual(DUSUK_GUVEN_SEBEBI, sebep)
        self.assertIn(f"{ESIK_ALTI:.3f}", detay)
        self.assertIn(f"{ROTA_GUVEN_ESIGI:.3f}", detay)

    def test_hemen_alti_detayda_esigin_kendisi_gibi_gorunmez(self):
        hemen_alti = math.nextafter(ROTA_GUVEN_ESIGI, -math.inf)
        _sebep, detay = rota_guven_reddi(hemen_alti)
        self.assertIn(repr(hemen_alti), detay)
        self.assertNotIn(
            f"Rota guveni {ROTA_GUVEN_ESIGI:.3f};", detay)


if __name__ == "__main__":
    unittest.main(verbosity=2)
