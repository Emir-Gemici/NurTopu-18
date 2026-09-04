"""YKİ harita üst bandındaki açıklamalar birbirini örtmemelidir."""

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
GUI_YOLU = KOK / "comms" / "yks_gui.py"
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


class HaritaUstBantTests(unittest.TestCase):
    def test_uyari_aciklama_hb_ve_arena_dikey_olarak_ayridir(self):
        with mock.patch.object(yks_gui, "OLCEK", 1.0):
            for w, h in ((480, 420), (800, 600), (1120, 700)):
                with self.subTest(w=w, h=h):
                    _sol, arena_ust, olcek = yks_gui.harita_cizim_alani(w, h)
                    _ux, uyari_y, _uw = yks_gui.sematik_uyari_yerlesimi(w)
                    aciklama_y = yks_gui.S(yks_gui.HARITA_RENK_ACIKLAMA_Y_PX)
                    # HB yazısı merkezinin 20 px üstündedir (`_harita_ciz`).
                    hb_yazi_y = arena_ust + 0.04 * olcek - 20

                    self.assertLess(uyari_y, aciklama_y)
                    self.assertLess(aciklama_y, arena_ust)
                    self.assertGreaterEqual(arena_ust - aciklama_y, 30)
                    self.assertGreater(hb_yazi_y, aciklama_y + 20)

    def test_cizim_alani_canvas_sinirlarini_asmaz(self):
        with mock.patch.object(yks_gui, "OLCEK", 1.0):
            for w, h in ((480, 420), (800, 600), (1120, 700)):
                sol, ust, olcek = yks_gui.harita_cizim_alani(w, h)
                self.assertGreater(olcek, 0)
                self.assertGreaterEqual(sol, 0)
                self.assertGreaterEqual(ust, 0)
                self.assertLessEqual(sol + olcek + yks_gui.HARITA_YAN_KENAR_PX, w)
                self.assertLessEqual(ust + olcek + yks_gui.HARITA_ALT_KENAR_PX, h)

    def test_gercek_cizim_yordamları_saf_yerlesimi_ve_ayri_aciklamayi_kullanir(self):
        agac = ast.parse(GUI_YOLU.read_text(encoding="utf-8"),
                         filename=str(GUI_YOLU))
        sinif = next(n for n in agac.body
                     if isinstance(n, ast.ClassDef) and n.name == "YksArayuz")
        mxy = next(n for n in sinif.body
                   if isinstance(n, ast.FunctionDef) and n.name == "_mxy")
        harita = next(n for n in sinif.body
                      if isinstance(n, ast.FunctionDef) and n.name == "_harita_ciz")

        self.assertTrue(any(
            isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
            and c.func.id == "harita_cizim_alani" for c in ast.walk(mxy)))
        aciklamalar = []
        for cagri in (n for n in ast.walk(harita) if isinstance(n, ast.Call)):
            if not (isinstance(cagri.func, ast.Attribute)
                    and cagri.func.attr == "create_text"):
                continue
            metin = next((k.value for k in cagri.keywords if k.arg == "text"), None)
            if isinstance(metin, ast.Constant) and "YEŞİL:" in str(metin.value):
                aciklamalar.append(cagri)
        self.assertEqual(1, len(aciklamalar))
        anahtarlar = {k.arg for k in aciklamalar[0].keywords}
        self.assertIn("width", anahtarlar,
                      "dar ekranda renk açıklaması inset altına taşmamalı")


if __name__ == "__main__":
    unittest.main()
