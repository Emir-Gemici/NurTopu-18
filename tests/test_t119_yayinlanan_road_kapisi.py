"""T119 KAPISI: ayirt edici sahnede YAYINLANAN `road` DEGERI assert edilir.

Kusur zemini (Filo 3 mutasyon supurmesi + mimar hukmu D-209):
  `test_rota_serit_etiketi.py` ayirt edici zikzak sahnesinde yalniz `olcum`
  sozlugunun ALANLARINI (`darbogaz_serit`, `baskin_serit`) sinar; analyze_path
  cagrisinin YAYINLADIGI `yol` degerini o sahnede hic assert etmez. Sonuc:
  `rpi_inference.py:1349` (`open_path = olcum["darbogaz_serit"]`) satirina
  `darbogaz -> baskin` mutasyonu uygulandiginda o dosyadan SIFIR test dusuyordu
  (0/21) — yayin hatti fiilen korumasizdi.

Bu dosya tam o boslugu kapatir: zikzak sahnesinde (rota alt/ust serit 3'te,
tek gecis serit 1'deki kapidan) YAYINLANAN degerin
  (a) bagimsiz yer gercegiyle (kapinin seridi = 1) ve
  (b) darbogaz sozlesmesiyle (`yol == olcum["darbogaz_serit"]`)
uyustugunu, ve ayrisan sahnede baskin seride ESITLENMEDIGINI dogrudan sinar.

Sahne ureticisi `test_rota_serit_etiketi._zikzak`ten IMPORT edilir — kopya
tutulmaz (tekrarlayan kusur sinifi: "iki kopya, yalniz biri zorlaniyor").
Cross-import emsali: `test_costmap_on_images.py:37`.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))
if str(KOK / "tests") not in sys.path:
    sys.path.insert(0, str(KOK / "tests"))

from test_rota_serit_etiketi import _zikzak  # noqa: E402
from rpi_inference import analyze_path  # noqa: E402

# Kapinin yarim genisligi gate disindaki koridorlardan (dt yaricapi ~24 px,
# 48 px yukseklikli yatay bantlar) BELIRGIN kucuk kalsin diye dar kapilar:
# 16 px -> yaricap ~8, 24 px -> ~12. Boylece darbogaz KESIN kapidadir ve
# yer gercegi (serit 1) beraberlik bandina dusmez.
DAR_KAPILAR = (16, 24)
TUM_KAPILAR = (16, 24, 48, 64)
KAPI_SERIDI = 1          # _zikzak'in tek gecisi: serit 1'deki kapi
BASKIN_SERIT = 3         # alt/ust dikeyler + rota kutlesi serit 3'te


def _kos(kapi_px):
    yol, guven, wps, koridor, ret, olc = analyze_path(
        _zikzak(kapi_px), n_waypoints=8, return_clean=True,
        return_reason=True, return_olcum=True, min_area_ratio=0.001)
    return yol, olc


class T119YayinlananRoadTests(unittest.TestCase):
    """Yayinlanan `road`, ayirt edici sahnede DEGER olarak dogru mu?"""

    def test_zikzak_yayinlanan_road_yer_gercegidir(self):
        """KAPI: dar kapili zikzakta yayinlanan deger = kapinin seridi (1).

        Bagimsiz kahin: sahnenin alt->ust TEK gecisi serit 1'deki kapidir ve
        dar kapilarda rotanin en dar noktasi zorunlu olarak o kapidir. Yayin
        `baskin_serit` (3) uzerinden yapilsaydi bu test DUSERDI — alan adina
        degil YAYINLANAN DEGERE bakar.
        """
        olculen = 0
        for kapi_px in DAR_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                olculen += 1
                self.assertEqual(
                    yol, KAPI_SERIDI,
                    f"kapi_px={kapi_px}: tek gecis serit {KAPI_SERIDI}'de "
                    f"ama yayinlanan road={yol}")
        self.assertGreaterEqual(
            olculen, 1,
            "dar kapili zikzakta hic karar uretilmedi — kapi bos kaldi "
            "(D-15/K-04: sifir olcum basari sayilmaz)")

    def test_zikzak_ayrisan_sahnede_yayin_baskina_esitlenmez(self):
        """KAPI: darbogaz != baskin iken yayinlanan deger baskin OLAMAZ."""
        ayrisan = 0
        for kapi_px in TUM_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                if olc["darbogaz_serit"] == olc["baskin_serit"]:
                    continue
                ayrisan += 1
                self.assertNotEqual(
                    yol, olc["baskin_serit"],
                    f"kapi_px={kapi_px}: yayinlanan road={yol} BASKIN seride "
                    f"esit (darbogaz={olc['darbogaz_serit']}) — D-41 kusuru "
                    "yayin hattina geri gelmis")
        self.assertGreaterEqual(
            ayrisan, 1,
            "hicbir sahnede darbogaz != baskin — sahne ayirt edici degil, "
            "test bosluk (D-15 vakum kapi riski)")

    def test_zikzak_sahne_gecerliligi_baskin_hala_uc(self):
        """POZITIF KONTROL: sahne bozulursa yukaridaki kapilar anlamsizlasir.

        `baskin_serit == 3` degilse zikzak geometrisi degismis demektir;
        o zaman "yayin baskina esitlenmedi" testi bir sey ayirt etmiyordur.
        """
        gorulen = 0
        for kapi_px in TUM_KAPILAR:
            yol, olc = _kos(kapi_px)
            if olc is None:
                continue
            gorulen += 1
            self.assertEqual(
                olc["baskin_serit"], BASKIN_SERIT,
                f"kapi_px={kapi_px}: baskin_serit={olc['baskin_serit']} — "
                "zikzak sahnesi beklenen geometride degil")
        self.assertGreaterEqual(gorulen, 2, "sahne olcumleri uretilemedi")

    def test_yayin_darbogaz_sozlesmesine_bagli(self):
        """Tutarlilik: her olculebilir sahnede yayin = olcumun darbogazi.

        Tek basina yeterli kapi DEGILDIR (ic tutarlilik, yer gercegi degil);
        yukaridaki iki degere-dayali kapinin yaninda regresyon sinyalidir.
        """
        for kapi_px in TUM_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                self.assertEqual(
                    yol, olc["darbogaz_serit"],
                    f"kapi_px={kapi_px}: yayinlanan road={yol} != "
                    f"darbogaz_serit={olc['darbogaz_serit']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
