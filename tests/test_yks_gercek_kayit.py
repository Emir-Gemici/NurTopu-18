"""NEDEN: Kayıttan oynatımda ölçülmemiş GNSS alanı üretilmemeli."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest


SPEC = importlib.util.spec_from_file_location(
    "fdr_gercek_kayit", Path(__file__).resolve().parents[1] / "scripts/yks_gercek_kayit.py")
MODUL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODUL)


class GercekKayitAlanlari(unittest.TestCase):
    def test_global_position_fix_uydurmaz(self):
        mesaj = SimpleNamespace(get_type=lambda: "GLOBAL_POSITION_INT", lat=409594832,
                                lon=291338194, relative_alt=3450, vx=300, vy=400)
        veri = MODUL._gps(mesaj)
        self.assertNotIn("gps_fix", veri)
        self.assertNotIn("uydu", veri)
        self.assertEqual(veri["alt"], 3.45)
        self.assertEqual(veri["hiz"], 5.0)

    def test_msl_bagil_irtifa_gibi_gosterilmez(self):
        mesaj = SimpleNamespace(get_type=lambda: "GPS_RAW_INT", fix_type=3,
                                lat=409594832, lon=291338194, alt=135000,
                                satellites_visible=17, vel=120)
        veri = MODUL._gps(mesaj)
        self.assertNotIn("alt", veri)
        self.assertEqual(veri["lat"], 40.9594832)
        self.assertEqual(veri["uydu"], 17)
        self.assertEqual(veri["hiz"], 1.2)

    def test_bilinmeyen_hiz_ve_uydu_yayimlanmaz(self):
        mesaj = SimpleNamespace(get_type=lambda: "GPS_RAW_INT", fix_type=3,
                                lat=409594832, lon=291338194,
                                satellites_visible=255, vel=65535)
        veri = MODUL._gps(mesaj)
        self.assertNotIn("hiz", veri)
        self.assertNotIn("uydu", veri)

    def test_uc_boyutlu_fix_olmayan_gps_reddedilir(self):
        mesaj = SimpleNamespace(get_type=lambda: "GPS_RAW_INT", fix_type=2)
        self.assertIsNone(MODUL._gps(mesaj))


if __name__ == "__main__":
    unittest.main()
