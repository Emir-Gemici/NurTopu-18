"""T152 — ON_KAYIT §11(2) "rota yol ustunde mi" kapisi (142_gece_olcum.py, b-ek2).

Sentetik uc durumlu etiket (0 etiketsiz · 1 sinif 0 · 2 sinif 1) + waypoint listesiyle
142'nin kapi fonksiyonlari (rota_yol_olc, yanlis_guzergah_mi, rota_yol_kapisi) dogrudan sinanir.
Sabitler ON_KAYIT §11(2): yol payi >= 0,90 VE sinif 1 ustunde 0 waypoint.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "142_gece_olcum.py"


def _yukle():
    spec = importlib.util.spec_from_file_location("olcum142", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _yukle()
YAN = 100


def _etiket():
    """100x100 tuval: sol yari (x<50) sinif 0 (yol), x in [50,70) etiketsiz (cim),
    x >= 70 sinif 1 (engel)."""
    uc = np.zeros((YAN, YAN), np.uint8)
    uc[:, :50] = M.SINIF0
    uc[:, 70:] = M.SINIF1
    return uc


def _dikey(x, n=8):
    """x sutununda alt->ust n waypoint."""
    ys = np.linspace(95, 5, n).astype(int)
    return [[int(x), int(y)] for y in ys]


class RotaYolOlc(unittest.TestCase):
    def test_a_yol_ustunde_rota_gecer(self):
        o = M.rota_yol_olc(_dikey(20), _etiket())
        self.assertEqual(o["yol_payi"], 1.0)
        self.assertEqual(o["engel_wp"], 0)
        self.assertEqual(o["etiketsiz_payi"], 0.0)
        self.assertEqual(o["cizgi_px"], 91)          # y 5..95 dahil, 1 px genislik
        self.assertFalse(M.yanlis_guzergah_mi(o))

    def test_b_cimden_gecen_rota_pay_yarim_yanlis(self):
        # yatay cizgi x=30..69 (40 px): 20 px yol, 20 px etiketsiz -> pay 0,5
        wps = [[30, 50], [69, 50]]
        o = M.rota_yol_olc(wps, _etiket())
        self.assertEqual(o["cizgi_px"], 40)
        self.assertEqual(o["yol_payi"], 0.5)
        self.assertEqual(o["etiketsiz_payi"], 0.5)
        self.assertEqual(o["engel_wp"], 0)           # engel yok, yine de YANLIS
        self.assertTrue(M.yanlis_guzergah_mi(o))

    def test_c_sinif1_ustunde_tek_waypoint_yanlis(self):
        wps = _dikey(20)
        wps[3] = [80, wps[3][1]]                     # tek waypoint engel ustune
        o = M.rota_yol_olc(wps, _etiket())
        self.assertEqual(o["engel_wp"], 1)
        self.assertTrue(M.yanlis_guzergah_mi(o))
        # ayni rota, engel waypoint'i olmadan yol ustunde kalir (kontrol)
        self.assertFalse(M.yanlis_guzergah_mi(M.rota_yol_olc(_dikey(20), _etiket())))

    def test_c2_tuval_disi_waypoint_engel_sayilir(self):
        wps = _dikey(20)
        wps[0] = [20, 150]                           # tuval disi -> fail-closed
        o = M.rota_yol_olc(wps, _etiket())
        self.assertEqual(o["engel_wp"], 1)
        self.assertTrue(M.yanlis_guzergah_mi(o))

    def test_d_esik_tam_sinir(self):
        self.assertEqual(M.KAPI_B_EK2, {"yol_payi_min": 0.90, "engel_wp_maks": 0})
        self.assertFalse(M.yanlis_guzergah_mi({"yol_payi": 0.90, "engel_wp": 0}))
        self.assertTrue(M.yanlis_guzergah_mi({"yol_payi": 0.89, "engel_wp": 0}))
        # cizgiden turetilmis sinir: 100 px cizgi, 90 px yol / 10 px etiketsiz
        uc = np.zeros((YAN, YAN), np.uint8)
        uc[:, :90] = M.SINIF0
        o = M.rota_yol_olc([[0, 50], [99, 50]], uc)
        self.assertEqual(o["cizgi_px"], 100)
        self.assertEqual(o["yol_payi"], 0.9)
        self.assertFalse(M.yanlis_guzergah_mi(o))
        uc[:, 89] = M.ETIKETSIZ                      # 89 px yol -> 0,89
        o = M.rota_yol_olc([[0, 50], [99, 50]], uc)
        self.assertEqual(o["yol_payi"], 0.89)
        self.assertTrue(M.yanlis_guzergah_mi(o))

    def test_e_mutasyon_yol_payi_kiyasi_kaldirilinca_b_gecer(self):
        """Kapi satiri (yol_payi < 0,90) kaldirilmis MUTANT: yalniz engel_wp'ye bakar.
        (b) senaryosu (pay 0,5, engel yok) mutantta 'yol ustunde' cikar — yani test_b
        bu mutasyonu yakalar. Burada mock ile ayni sey kanitlanir."""
        o = M.rota_yol_olc([[30, 50], [69, 50]], _etiket())
        self.assertTrue(M.yanlis_guzergah_mi(o))    # asil kod: YANLIS

        def mutant(olcum, kapi=M.KAPI_B_EK2):
            if olcum["engel_wp"] > kapi["engel_wp_maks"]:
                return True
            return False

        with mock.patch.object(M, "yanlis_guzergah_mi", mutant):
            self.assertFalse(M.yanlis_guzergah_mi(o))   # mutant (b)'yi gecirir
            with self.assertRaises(AssertionError):
                self.assertTrue(M.yanlis_guzergah_mi(o))  # test_b'nin iddiasi duser


class RotaYolKapisi(unittest.TestCase):
    """Dosya tabanli yol: YOLO etiket + sahte 126 satirlari -> rota_yol_kapisi."""

    def setUp(self):
        import cv2
        self.tmp = tempfile.TemporaryDirectory()
        kok = Path(self.tmp.name)
        self.kareler = kok / "images"; self.kareler.mkdir()
        self.etiket = kok / "labels"; self.etiket.mkdir()
        # 100x60 kare -> 100x100 tuval, y0 = 20
        cv2.imwrite(str(self.kareler / "k.jpg"), np.zeros((60, 100, 3), np.uint8))
        # sinif 0: sol yari; sinif 1: sag %30 (normalize poligon)
        (self.etiket / "k.txt").write_text(
            "0 0 0 0.5 0 0.5 1 0 1\n1 0.7 0 1 0 1 1 0.7 1\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_uc_durum_maske_tuvale_yerlesir(self):
        uc = M.uc_durum_maske(self.etiket / "k.txt", 60, 100)
        self.assertEqual(uc.shape, (100, 100))
        self.assertEqual(int(uc[10, 10]), M.ETIKETSIZ)     # dolgu bandi
        self.assertEqual(int(uc[50, 10]), M.SINIF0)
        self.assertEqual(int(uc[50, 60]), M.ETIKETSIZ)
        self.assertEqual(int(uc[50, 90]), M.SINIF1)

    def test_kapi_yalniz_rota_karelerini_sayar(self):
        kareler126 = [
            {"kare": "k.jpg", "olceksiz_sebep": None, "olceksiz_wps": [[20, 75], [20, 25]]},
            {"kare": "k.jpg", "olceksiz_sebep": None, "olceksiz_wps": [[20, 75], [85, 25]]},
            {"kare": "k.jpg", "olceksiz_sebep": "MASKE_YOK", "olceksiz_wps": []},
        ]
        r = M.rota_yol_kapisi(kareler126, self.etiket, self.kareler)
        self.assertEqual(r["rota_kare"], 2)
        self.assertEqual(r["yanlis_guzergah"], 1)
        self.assertFalse(r["rota_yol"][0]["yanlis_guzergah"])
        self.assertTrue(r["rota_yol"][1]["yanlis_guzergah"])
        self.assertEqual(r["kapi"], M.KAPI_B_EK2)
        json.dumps(r)                                     # JSON'a yazilabilir

    def test_eski_126_ciktisi_wps_yoksa_acik_hata(self):
        with self.assertRaises(SystemExit):
            M.rota_yol_kapisi([{"kare": "k.jpg", "olceksiz_sebep": None}], self.etiket, self.kareler)


if __name__ == "__main__":
    unittest.main()
