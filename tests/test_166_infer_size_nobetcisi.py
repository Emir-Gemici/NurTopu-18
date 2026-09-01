"""166 INFER_SIZE olcumu nobetcisi — ON_KAYIT_INFER_SIZE kilitleri.

  1. TABAN/ADAY (512/640) ve I2/I3/I4 esikleri sonradan degistirilemez;
     I3 esigi SOZLESMEDEN gelir (YKS_TESPIT_TAZELIK_S), ciplak kopya degil.
  2. D-375 korumasi: iki AYRI model ornegi + kod ici `imgsz` dogrulamasi.
     Tek nesneye iki imgsz verilirse arguman sessizce yok sayilabilir ve
     olcum FARKSIZLIK uretir ("denk" sanilir).
  3. I2 bir REDDETME kapisidir: S'te gerileme varsa I1 ne olursa olsun RED.
  4. OLCULEMEDI != GECTI.

Mutasyonlar KOD uzerinde (D-354/D-361), uygulanmadiysa test DUSER (D-370).
"""
import ast
import importlib.util as _u
import inspect
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "166_infer_size_640.py"
ON_KAYIT = KOK / "results" / "b4_fps" / "ON_KAYIT_INFER_SIZE.md"

sys.path.insert(0, str(KOK / "scripts" / "olcum"))
_sp = _u.spec_from_file_location("m166", BETIK)
M = _u.module_from_spec(_sp)
_sp.loader.exec_module(M)

KAYNAK = BETIK.read_text(encoding="utf-8")
KAYIT = ON_KAYIT.read_text(encoding="utf-8")


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


def _r(dosya, ucus, y512, y640, ms512=10.0, ms640=20.0):
    return {"dosya": dosya, "ucus": ucus, "zaman_sn": 0.0, "rel_alt": 31.0,
            "512": {"yol": y512, "red": None, "cikarim_ms": ms512},
            "640": {"yol": y640, "red": None, "cikarim_ms": ms640}}


def _s(kare, y512, y640, gt):
    return {"kare": kare, "acik_serit": gt,
            "512": {"yol": y512, "red": None, "cikarim_ms": 10.0},
            "640": {"yol": y640, "red": None, "cikarim_ms": 20.0}}


class OnKayitKilidi(unittest.TestCase):
    def test_capa(self):
        ast.parse(KAYNAK)
        self.assertTrue(ON_KAYIT.is_file())

    def test_TABAN_ADAY_DONDURULDU(self):
        self.assertEqual((M.TABAN, M.ADAY), (512, 640))
        self.assertIn("512", KAYIT)
        self.assertIn("640", KAYIT)

    def test_I3_ESIGI_SOZLESMEDEN(self):
        from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S
        self.assertEqual(M.I3_KOSU_ESIGI_S, YKS_TESPIT_TAZELIK_S,
                         "I3 esigi sozlesmeden kopmus (madde 16)")

    def test_I4_GEREKLI_FPS_D374_ILE_AYNI(self):
        self.assertEqual(M.I4_GEREKLI_FPS, 0.41)
        self.assertIn("0,41", KAYIT)

    def test_D375_KORUMASI_YERINDE(self):
        kod = _kodu(KAYNAK)
        self.assertIn("m512 = YOLO", kod)
        self.assertIn("m640 = YOLO", kod)
        self.assertGreaterEqual(kod.count("_imgsz_dogrula("), 2,
                                "imgsz dogrulamasi eksik — arguman sessizce "
                                "yok sayilirsa olcum FARKSIZLIK uretir")

    def test_URETIM_ZINCIRI(self):
        kod = _kodu(KAYNAK)
        for halka in ("rota_olcek_reddi(", "_rota_kararini_esikle(",
                      "_maskeleri_icerige_kirp("):
            self.assertIn(halka, kod, f"halka eksik: {halka}")


class HukumDavranisi(unittest.TestCase):
    def test_BOS_KUME_OLCULEMEDI(self):
        self.assertEqual(M.hukum([], [], set())["durum"], "OLCULEMEDI")

    def test_I1_SIFIRSA_KALDIRAC_DEGIL(self):
        r = [_r("a", "u", None, None), _r("b", "u", None, None)]
        h = M.hukum(r, [_s("s1", 1, 1, 1)], {"a", "b"})
        self.assertEqual(h["I1_tani"]["hukum"], "COZUNURLUK_KALDIRAC_DEGIL")
        self.assertEqual(h["I1_tani"]["p_640"], 0.0)

    def test_I1_KURTARMA_VARSA_KISMEN(self):
        r = [_r("a", "u", None, 2), _r("b", "u", None, None)]
        h = M.hukum(r, [_s("s1", 1, 1, 1)], {"a", "b"})
        self.assertEqual(h["I1_tani"]["hukum"], "KISMEN_CALISIYOR")
        self.assertAlmostEqual(h["I1_tani"]["p_640"], 0.5)

    def test_I2_GERILEME_DUSURUR(self):
        # 10 karede 512 hepsini buluyor, 640 sekizini -> fark -0,20 < -0,02
        s = [_s(f"k{i}", 1, 1 if i < 8 else None, 1) for i in range(10)]
        h = M.hukum([_r("a", "u", 1, 1)], s, set())
        self.assertEqual(h["I2_gerileme"]["durum"], "DUSTU")

    def test_I2_SINIRDA_GECER(self):
        # 100 karede 2 kayip -> fark tam -0,02, tavanda: GECER
        s = [_s(f"k{i}", 1, 1 if i < 98 else None, 1) for i in range(100)]
        h = M.hukum([_r("a", "u", 1, 1)], s, set())
        self.assertAlmostEqual(h["I2_gerileme"]["fark"], -0.02)
        self.assertEqual(h["I2_gerileme"]["durum"], "GECTI")

    def test_I2_DOGRU_YANLISA_DONEN_SAYILIYOR(self):
        s = [_s("k0", 2, 3, 2), _s("k1", 1, 1, 1)]
        h = M.hukum([_r("a", "u", 1, 1)], s, set())
        self.assertEqual(h["I2_gerileme"]["dogru_yanlisa_donen"], 1)

    def test_I3_KOSU_UCUS_ICINDE_SAYILIYOR(self):
        """Iki ucusun ucu BIRLESTIRILIRSE olmayan bir kosu uydurulur."""
        r = [_r("a1", "U1", 1, None), _r("b1", "U2", 1, None)]
        h = M.hukum(r, [_s("s", 1, 1, 1)], set())
        self.assertEqual(h["I3_kapi"]["kosu_640"]["maks"], 1,
                         "ucuslar birlestirilmis — kosu 2 cikti")

    def test_I3_SINIRDA_DUSER(self):
        r = [_r(f"k{i}", "U", 1, None) for i in range(5)]
        h = M.hukum(r, [_s("s", 1, 1, 1)], set())
        self.assertEqual(h["I3_kapi"]["kosu_640"]["maks"], 5)
        self.assertEqual(h["I3_kapi"]["durum"], "DUSTU")

    def test_I4_MALIYET_BUTCEYI_ASARSA_YAKALANIR(self):
        # c = 40/10 = 4 -> etkin 0,9/4 = 0,225 < 0,41
        r = [_r("a", "U", 1, 1, ms512=10.0, ms640=40.0)]
        h = M.hukum(r, [_s("s", 1, 1, 1)], set())
        self.assertEqual(h["I4_fps"]["durum"], "FPS_BUTCESI_YETMEZ")
        r = [_r("a", "U", 1, 1, ms512=10.0, ms640=15.0)]
        h = M.hukum(r, [_s("s", 1, 1, 1)], set())
        self.assertEqual(h["I4_fps"]["durum"], "GECTI")


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_IMGSZ_DOGRULAMASI_SILININCE_YAKALANIR(self):
        kod = _kodu(KAYNAK)
        mutant = kod.replace("_imgsz_dogrula(model, boy, ad)",
                             "_atlanan(model, boy, ad)", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("_imgsz_dogrula("),
                        kod.count("_imgsz_dogrula("),
                        "koruma silindigi halde sayim dusmedi — BOS KAPI")

    def test_M2_I2_KAPISI_GEVSETILIRSE_YAKALANIR(self):
        """⚠ Mutasyon KIYAS satirini hedeflemeli; `-I2_GERILEME_TAVANI` ayrica
        rapor alaninda ("tavan": ...) da geciyor — ilk kopyayi degistirmek
        kapiyi HIC etkilemezdi (D-354/D-361 kaliminin bir baska yuzu)."""
        kod = _kodu(inspect.getsource(M.hukum))
        desen = ">= -I2_GERILEME_TAVANI - I2_EPSILON"
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI: kiyas deseni yok")
        mutant = kod.replace(desen, ">= -1.0", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "gerileme kiyasi gevsetildigi halde gorunmuyor")


if __name__ == "__main__":
    unittest.main()
