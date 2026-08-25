"""T145 (D-285 §5) — 138 kare uygunluk denetiminin KARANLIK / GURULTULU kapisi.

Codex D-282'de mekanik karsi ornek uretti: 0,03x karartilmis + Gauss
gurultulu kare (gozle okunamaz) dort bayragin hepsinden geciyordu. Bu test
ayni mutasyonu (ayni tohum, ayni parametreler) yeniden uretir ve bayrak
ALMASINI zorlar; temiz gunduz kareleri ise bayrak ALMAMALIDIR.

Girdi kareler O:/navitas/results/dji_20260822/kareler/*.jpg — worktree'de
yoksa test atlanir (skip), sessizce gecmez.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "138_kare_uygunluk_denetimi.py"
KARELER = [Path("O:/navitas/results/dji_20260822/kareler"),
           KOK / "results" / "dji_20260822" / "kareler"]
# BULANIK icin referans alt siniri: D-282 yeniden uretimindeki turetilmis
# deger (results/codex_denetim/d282/kare_uygunluk_yeniden.json: 465,27).
# Referans kume worktree'de olmayabilir; bu test KESKINLIK bandini sinamaz.
KES_ALT = 465.27


def _modul():
    spec = importlib.util.spec_from_file_location("kud138", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _kareler():
    for k in KARELER:
        yol = sorted(k.glob("*.jpg"))
        if yol:
            return yol
    return []


def _codex_mutasyonu(img):
    """results/codex_denetim/bagimsiz_sayim.py:229-236 ile AYNI islem."""
    temel = cv2.resize(img, (960, 540), interpolation=cv2.INTER_AREA)
    rng = np.random.default_rng(282)
    return np.clip(temel.astype(np.float32) * 0.03 +
                   rng.normal(12.0, 8.0, temel.shape), 3, 60).astype(np.uint8)


class T145Uygunluk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _modul()
        cls.kareler = _kareler()
        if not cls.kareler:
            raise unittest.SkipTest("gunduz kareleri yok: %s" % KARELER[0])

    def test_codex_karanlik_gurultulu_bayrak_alir(self):
        img = cv2.imread(str(self.kareler[0]))
        o = self.m.olcutler(_codex_mutasyonu(img))
        b = self.m.bayraklar(o, KES_ALT)
        self.assertIn("KARANLIK", b, o)
        self.assertIn("GURULTULU", b, o)
        # Codex'in gozlemi korunuyor: gurultu keskinligi YUKSELTIR, BULANIK yok
        self.assertNotIn("BULANIK", b, o)

    def test_yalniz_karartma_karanlik_alir(self):
        img = cv2.imread(str(self.kareler[0]))
        kar = np.clip(img.astype(np.float32) * 0.1, 0, 255).astype(np.uint8)
        b = self.m.bayraklar(self.m.olcutler(kar), KES_ALT)
        self.assertIn("KARANLIK", b)

    def test_temiz_gunduz_kareleri_bayrak_almaz(self):
        for p in self.kareler:
            o = self.m.olcutler(cv2.imread(str(p)))
            b = self.m.bayraklar(o, KES_ALT)
            self.assertEqual(b, [], "%s -> %s %s" % (p.name, b, o))

    def test_sabitler_olculmus_bosluktadir(self):
        # gece en aydinlik kare 76,2 < ALT < etiketli gunduz min 96,3 (T138/T145)
        self.assertGreater(self.m.PARLAKLIK_ALT, 76.2)
        self.assertLess(self.m.PARLAKLIK_ALT, 96.3)
        # DJI 768 kare maks 2,84 < UST < Codex tam-cozunurluk varyanti 3,77
        self.assertGreater(self.m.GURULTU_ORANI_UST, 2.84)
        self.assertLess(self.m.GURULTU_ORANI_UST, 3.77)


if __name__ == "__main__":
    unittest.main()
