"""T36b KAPISI (ON_KAYIT §25 · REVIEW_LOG D-302): kompozit kaynagin "beklenen
serit" satiri hakemi YANILTMAMALI.

OLCULDU (results/t36b/olcum.json): kompozit kumenin 9 karesinde yer gercegi
maskesiyle (ORACLE) algoritma 8/9 dogru serit yayinliyor; MODEL maskesiyle 0/9
(hepsi RET). Sebep model kusuru DEGIL: kumenin sinif 0 yer gercegi, ham karede
GORUNMEYEN sentetik bir koridordur (D-298 §3). Ekran "beklenen serit N ->
CEKIMSER" yazip birakirsa hakem sistemi arizali sanar.

Bu kapi, uyari cumlesinin kompozit kaynakta HER ZAMAN yazildigini ve karar
yoluna SIZMADIGINI kilitler.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

KAYNAK = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")


class GosterimNotu(unittest.TestCase):

    def test_uyari_kompozit_blogunda(self):
        self.assertIn("GEOMETRİK", KAYNAK,
                      "kompozit yer gerçeği uyarısı kayboldu (T36b/D-302)")
        bas = KAYNAK.index("GEOMETRİK")
        # Uyarinin USTUNDE, en yakin kaynak dali `kompozit` olmali.
        onceki = KAYNAK.rfind('if self.algi_kaynak == "kompozit":', 0, bas)
        self.assertNotEqual(-1, onceki, "uyari kompozit dalinin icinde degil")
        baska = KAYNAK.rfind('if self.algi_kaynak', onceki + 1, bas)
        self.assertEqual(-1, baska,
                         "uyari ile kompozit dali arasinda BASKA bir kaynak "
                         "dali var — uyari yanlis kaynakta yazilabilir")

    def test_uyari_beklenen_serit_ile_AYNI_dalda(self):
        """Uyari, `beklenen şerit N → UYUM` satirinin hemen yaninda olmali."""
        m = re.search(r'bilgi \+= \(f" · beklenen şerit \{_beklenen\}"'
                      r'.*?GEOMETRİK', KAYNAK, re.S)
        self.assertIsNotNone(
            m, "uyari beklenen-serit satiriyla ayni dalda degil — bazi "
               "karelerde hakem uyarisiz 'ÇEKİMSER' gorebilir")
        self.assertLess(len(m.group(0)), 1600,
                        "uyari ile beklenen-serit satiri arasi cok uzak")

    def test_uyari_karar_yoluna_SIZMIYOR(self):
        """Cumle yalniz `bilgi` metnine yazilir; karar degiskenlerine DOKUNMAZ."""
        bas = KAYNAK.index("GEOMETRİK")
        pencere = KAYNAK[bas - 600: bas + 400]
        for yasak in ("yol_no =", "guven =", "wps =", "karar_reddi ="):
            self.assertNotIn(yasak, pencere,
                             f"gosterim notu karar degiskenine yaziyor: {yasak}")


class OlcumKaydi(unittest.TestCase):
    """Kapanma kanitinin dosyasi durmali; sayilar cumleyle tutarli olmali."""

    def test_olcum_dosyasi_var_ve_tutarli(self):
        p = KOK / "results" / "t36b" / "olcum.json"
        if not p.is_file():
            self.skipTest("olcum dosyasi yok")
        d = json.loads(p.read_text(encoding="utf-8"))
        oracle = d["kollar"]["ORACLE"]
        model = d["kollar"]["MODEL"]
        self.assertGreaterEqual(oracle["dogru"], 8,
                                "ORACLE kolu on kayitli esigin (>=8/9) altina dustu")
        self.assertEqual(9, oracle["n"])
        self.assertEqual(0, model["dogru"],
                         "MODEL kolu degistiyse D-302'nin gerekcesi yeniden "
                         "olculmeli (kapanma karari o sayiya dayanmiyor ama "
                         "ekrandaki cumle ona dayaniyor)")


if __name__ == "__main__":
    unittest.main()
