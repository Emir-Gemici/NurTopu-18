"""K6 — ON_KAYIT §12 "rota yol ustunde" (sentetik kabul zinciri, 65_kabul_denetcisi).

Sinanan:
  (a) rota_yol_olcumu.py TEK tanim: 142 (test_t152) ile 61/65 ayni fonksiyonlari
      cagirir; YOLO poligon etiketi tuvale (letterbox yerlesimi) tasinir.
  (b) kucuk sentetik kume: iki etiket dosyasi + waypoint listeleri -> kare basina
      yol_payi / engel_wp / yanlis_guzergah -> 61 JSON sekli -> k6_durumu.
  (c) k6_durumu uc durumu: GECTI / DUSTU / OLCULEMEDI (girdi yok, eski 61 ciktisi,
      payda 0). OLCULEMEDI != GECTI.
  (d) 65 icinde kapi satiri: ESIK["K6_yanlis_guzergah_maks"] == 0.05 (on kayit),
      gecti["K6"] verdikte dahil, rapor satiri var. Mutasyon: satir kaldirilinca duser.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
OLCUM = KOK / "scripts" / "olcum"
BETIK65 = OLCUM / "65_kabul_denetcisi.py"

for _p in (OLCUM, KOK / "codes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _yukle(ad, yol):
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RYO = _yukle("rota_yol_olcumu_k6", OLCUM / "rota_yol_olcumu.py")
K65 = _yukle("kabul_denetcisi_k6", BETIK65)
M142 = _yukle("olcum142_k6", OLCUM / "142_gece_olcum.py")

YAN = 64   # kucuk kare tuval (kabul kumesi 640x640; oran ayni)


def _etiket_yaz(dizin: Path, ad: str, satirlar):
    p = dizin / f"{ad}.txt"
    p.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    return p


# YOLO poligon (normalize): sol yari sinif 0 (yol), sag ceyrek sinif 1 (engel)
YOL_SOL = "0 0.0 0.0 0.5 0.0 0.5 1.0 0.0 1.0"
ENGEL_SAG = "1 0.75 0.0 1.0 0.0 1.0 1.0 0.75 1.0"


def _dikey(x, n=6):
    ys = np.linspace(YAN - 4, 3, n).astype(int)
    return [[int(x), int(y)] for y in ys]


class TekTanim(unittest.TestCase):
    def test_142_ayni_modulu_kullanir(self):
        # 142'nin adlari rota_yol_olcumu'ndan gelir (kod kopyasi degil).
        self.assertEqual(M142.KAPI_B_EK2, RYO.KAPI_B_EK2)
        self.assertEqual(M142.KAPI_B_EK2, {"yol_payi_min": 0.90, "engel_wp_maks": 0})
        self.assertIs(M142.rota_yol_olc.__code__.co_filename,
                      RYO.rota_yol_olc.__code__.co_filename)
        self.assertEqual(M142.rota_yol_olc.__code__.co_filename,
                         str(OLCUM / "rota_yol_olcumu.py"))

    def test_61_ayni_modulu_ice_aktarir(self):
        src = (OLCUM / "61_rota_moloza_basma.py").read_text(encoding="utf-8")
        self.assertIn("from rota_yol_olcumu import", src)
        self.assertIn('kayit["yanlis_guzergah"] = yanlis_guzergah_mi(ry)', src)
        # tuval = analyze_path'in calistigi `sq` (h == yan); ayni tuvale rasterize
        self.assertIn("uc_durum_maske(txt, h0, w0, yan=h)", src)

    def test_letterbox_yerlesimi_preprocess_ile_ayni(self):
        # dikdortgen kare: etiket tuvale ((yan-w)//2, (yan-h)//2) ile ortalanir
        with tempfile.TemporaryDirectory() as td:
            lbl = _etiket_yaz(Path(td), "k", [YOL_SOL, ENGEL_SAG])
            h, w = 20, 40
            uc = RYO.uc_durum_maske(lbl, h, w)
            self.assertEqual(uc.shape, (40, 40))
            y0 = (40 - h) // 2
            self.assertTrue((uc[:y0] == RYO.ETIKETSIZ).all())          # ust dolgu
            self.assertTrue((uc[y0 + h:] == RYO.ETIKETSIZ).all())      # alt dolgu
            self.assertTrue((uc[y0:y0 + h, :20] == RYO.SINIF0).all())
            self.assertTrue((uc[y0:y0 + h, 30:] == RYO.SINIF1).all())


class SentetikKume(unittest.TestCase):
    """Iki kare: 'iyi' (rota yol ustunde) ve 'kotu' (engel ustunde waypoint)."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        d = Path(self.td.name)
        self.lbl = _etiket_yaz(d, "kare", [YOL_SOL, ENGEL_SAG])
        self.uc = RYO.uc_durum_maske(self.lbl, YAN, YAN)

    def tearDown(self):
        self.td.cleanup()

    def _kare(self, wps):
        o = RYO.rota_yol_olc(wps, self.uc)
        return dict(o, yanlis_guzergah=RYO.yanlis_guzergah_mi(o))

    def test_iyi_kare(self):
        k = self._kare(_dikey(10))
        self.assertEqual(k["yol_payi"], 1.0)
        self.assertEqual(k["engel_wp"], 0)
        self.assertFalse(k["yanlis_guzergah"])

    def test_engel_ustunde_wp_yanlis(self):
        k = self._kare(_dikey(56))
        self.assertGreater(k["engel_wp"], 0)
        self.assertTrue(k["yanlis_guzergah"])

    def test_yol_payi_dusuk_yanlis(self):
        # yatay: x 0..39 (40 px) -> fillPoly kenar dahil: x 0..32 = 33 px yol,
        # 7 px etiketsiz => 33/40 = 0,825 < 0,90; engel_wp 0
        k = self._kare([[0, 30], [39, 30]])
        self.assertEqual(k["engel_wp"], 0)
        self.assertAlmostEqual(k["yol_payi"], 33 / 40, places=3)
        self.assertTrue(k["yanlis_guzergah"])

    def test_61_json_sekli_ve_k6_hesabi(self):
        kayitlar = [self._kare(_dikey(10)) for _ in range(19)] + [self._kare(_dikey(56))]
        yol_olculen = [k for k in kayitlar if k["yanlis_guzergah"] is not None]
        yanlis = [k for k in yol_olculen if k["yanlis_guzergah"]]
        d = {"yol_olculen": len(yol_olculen), "yanlis_guzergah": len(yanlis)}
        durum, s = K65.k6_durumu(d)
        self.assertEqual((s["yanlis_guzergah"], s["yol_olculen"]), (1, 20))
        self.assertEqual(durum, "GECTI")                       # 0,05 <= 0,05
        d["yanlis_guzergah"] = 2
        self.assertEqual(K65.k6_durumu(d)[0], "DUSTU")         # 0,10 > 0,05


class K6Durumu(unittest.TestCase):
    def test_esik_on_kayit(self):
        self.assertEqual(K65.ESIK["K6_yanlis_guzergah_maks"], 0.05)

    def test_olculemedi_girdi_yok(self):
        self.assertEqual(K65.k6_durumu(None)[0], "OLCULEMEDI")

    def test_olculemedi_eski_61_ciktisi(self):
        # K6 alanlari olmayan (eski) 61 JSON'u: 'basan' var ama yol_olculen yok
        self.assertEqual(K65.k6_durumu({"n": 260, "rota_uretilen": 200, "basan": 0})[0],
                         "OLCULEMEDI")

    def test_olculemedi_payda_sifir(self):
        self.assertEqual(K65.k6_durumu({"yol_olculen": 0, "yanlis_guzergah": 0})[0],
                         "OLCULEMEDI")

    def test_esik_sozlukten(self):
        e = dict(K65.ESIK, K6_yanlis_guzergah_maks=0.5)
        self.assertEqual(K65.k6_durumu({"yol_olculen": 10, "yanlis_guzergah": 3}, e)[0],
                         "GECTI")
        self.assertEqual(K65.k6_durumu({"yol_olculen": 10, "yanlis_guzergah": 3})[0],
                         "DUSTU")


class KapiSatiri(unittest.TestCase):
    SRC = BETIK65.read_text(encoding="utf-8")

    def test_gecti_k6_verdikte_dahil(self):
        # gecti["K6"] atanir; VERDIKT `all(gecti.values())` uzerinden K6'yi kapsar.
        self.assertRegex(self.SRC, r'gecti\["K6"\]\s*=\s*k6\s*==\s*"GECTI"')
        self.assertIn("all(gecti.values())", self.SRC)
        self.assertIn('durumlar["K6"] = sonuc.get("K6_durum")', self.SRC)

    def test_rapor_satiri_ve_json_alanlari(self):
        self.assertIn("K6 ROTA YOL USTUNDE <= %", self.SRC)
        for alan in ("K6_yanlis_guzergah", "K6_oran", "K6_durum", "K6_yanlis_kareler"):
            self.assertIn(f'sonuc["{alan}"]', self.SRC)

    def test_k6_verdikti_bloklar_simulasyon(self):
        # VERDIKT mantiginin kopyasi degil: gecti sozlugunun all() semantigi.
        gecti = {"K0": True, "K1": True, "K2": True, "K3": True, "K4": True, "K5": True}
        gecti["K6"] = K65.k6_durumu(None)[0] == "GECTI"
        self.assertFalse(all(gecti.values()))


if __name__ == "__main__":
    unittest.main()
