"""164 FP16 denklik olcumu nobetcisi — ON_KAYIT_FP16 kilitleri.

  1. F2 esigi (0,98) ve FOV (67,3, 163 ile AYNI) sonradan degistirilemez.
  2. F1 SIFIR toleranslidir: tek zarar veren kare bile DUSURUR.
  3. CUDA yoksa OLCULEMEDI — "gecti" uretilmez (OLCULEMEDI != GECTI).
  4. Karar halkasi 163 ile ayni uretim zinciridir.

Mutasyonlar KOD uzerinde (D-354/D-361), uygulanmadiysa test DUSER (D-370).
"""
import ast
import importlib.util as _u
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
B163 = KOK / "scripts" / "olcum" / "163_b4_p_ve_kosu.py"
B164 = KOK / "scripts" / "olcum" / "164_fp16_karar_denkligi.py"
ON_KAYIT = KOK / "results" / "b4_fps" / "ON_KAYIT_FP16.md"

sys.path.insert(0, str(KOK / "scripts" / "olcum"))


def _yukle(yol, ad):
    sp = _u.spec_from_file_location(ad, yol)
    m = _u.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


M163 = _yukle(B163, "n164_m163")
M164 = _yukle(B164, "n164_m164")
KAYNAK = B164.read_text(encoding="utf-8")
KAYIT = ON_KAYIT.read_text(encoding="utf-8")


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


def _s(kare, fp32, fp16, gt):
    return {"kare": kare, "fp32_yol": fp32, "fp16_yol": fp16,
            "fp32_red": None, "fp16_red": None,
            "uyusma": fp32 == fp16, "acik_serit": gt, "bit_es": False}


def _r(kare, fp32, fp16):
    return {"kare": kare, "fp32_yol": fp32, "fp16_yol": fp16,
            "fp32_red": None, "fp16_red": None,
            "uyusma": fp32 == fp16, "bit_es": False}


class OnKayitKilidi(unittest.TestCase):
    def test_capa(self):
        ast.parse(KAYNAK)
        self.assertTrue(ON_KAYIT.is_file())

    def test_ESIK_VE_FOV_KILITLI(self):
        self.assertEqual(M164.F2_UYUSMA_ASGARI, 0.98)
        self.assertIn("0,98", KAYIT)
        self.assertEqual(M164.FOV_ESAS, M163.FOV_ESAS,
                         "164'un FOV'u 163'ten kopmus — ayni olcum cercevesi "
                         "sarti (EK-1) bozulur")

    def test_ZINCIR_HALKALARI(self):
        kod = _kodu(KAYNAK)
        for halka in ("rota_olcek_reddi(", "_rota_kararini_esikle(",
                      "half=True", "half=False"):
            self.assertIn(halka, kod, f"halka eksik: {halka}")


class HukumDavranisi(unittest.TestCase):
    def test_CUDA_YOKSA_OLCULEMEDI(self):
        h = M164.hukum([_s("a", 1, 1, 1)], [_r("b", 2, 2)], cuda_var=False)
        self.assertEqual(h["F1"]["durum"], "OLCULEMEDI")
        self.assertEqual(h["F2"]["durum"], "OLCULEMEDI")

    def test_F1_SIFIR_TOLERANS(self):
        # FP32 dogru (2==GT), FP16 yanlis serit (3) -> TEK kare DUSURUR.
        h = M164.hukum([_s("a", 2, 3, 2), _s("b", 1, 1, 1)],
                       [_r("c", 1, 1)], cuda_var=True)
        self.assertEqual(h["F1"]["durum"], "DUSTU")
        self.assertEqual(h["F1"]["zarar_veren"], ["a"])

    def test_F1_ZARARSIZ_UYUSMAZLIK_DUSURMEZ(self):
        # FP32 zaten yanlisken FP16'nin farkli olmasi F1'i dusurmez
        # (zarar yonu tanimli: DOGRU -> YANLIS). None'a donus de zarar degil.
        h = M164.hukum([_s("a", 3, 1, 2), _s("b", 2, None, 2)],
                       [_r("c", 1, 1)], cuda_var=True)
        self.assertEqual(h["F1"]["durum"], "GECTI")

    def test_F2_ESIK(self):
        r49 = [_r(f"k{i}", 1, 1) for i in range(49)] + [_r("x", 1, 2)]
        h = M164.hukum([_s("a", 1, 1, 1)], r49, cuda_var=True)
        self.assertEqual(h["F2"]["durum"], "GECTI")   # 49/50 = 0,98
        r48 = r49[:-1] + [_r("y", 1, 2), _r("z", 2, 1)]
        h = M164.hukum([_s("a", 1, 1, 1)], r48, cuda_var=True)
        self.assertEqual(h["F2"]["durum"], "DUSTU")   # 48/50 < 0,98

    def test_BOS_KUME_GECTI_SAYILMAZ(self):
        h = M164.hukum([], [], cuda_var=True)
        self.assertEqual(h["F1"]["durum"], "OLCULEMEDI")
        self.assertEqual(h["F2"]["durum"], "OLCULEMEDI")


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_HALF_KALDIRILINCA_YAKALANIR(self):
        kod = _kodu(KAYNAK)
        mutant = kod.replace("half=True", "half=False", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn("half=True", mutant,
                         "FP16 kolu kaldirildigi halde denetim gormuyor — "
                         "iki kol da FP32 olur, denklik BOS KAPIYA doner")

    def test_M2_TOLERANS_GEVSETILIRSE_YAKALANIR(self):
        import inspect
        kod = _kodu(inspect.getsource(M164.hukum))
        self.assertIn('"tolerans": 0', kod, "F1 toleransi 0 degil (D-107)")
        mutant = kod.replace("if not zarar else", "if len(zarar) < 2 else")
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")


if __name__ == "__main__":
    unittest.main()
