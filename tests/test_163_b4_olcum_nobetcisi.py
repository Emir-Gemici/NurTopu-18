"""B4 olcum nobetcisi — 163_b4_p_ve_kosu.py ON KAYITTAN SAPMASIN.

Korudugu seyler (ON_KAYIT: results/b4_fps/ON_KAYIT.md):
  1. Dondurulan FOV degerleri (EK-1 §E1.4) betikte SONRADAN degistirilemez —
     uc deger de on kayit metninde birebir gecmek zorundadir.
  2. G2 esigi (0,22) ve G1 esigi (YKS_TESPIT_TAZELIK_S) sozlesmeyle kilitli;
     ciplak kopya sabit yazilamaz (madde 16).
  3. Hukum >=30 m KATMANINDAN okunur (EK-2 kural 1) — `p_tam` ile verilen
     hukum on kayit ihlalidir.
  4. OLCULEMEDI != GECTI: bos katman GECTI sayilamaz.
  5. Uretim zinciri halkalari (olcek reddi + esikleme) betikte durur —
     olcek tuzagi (EK-1 §E1.1) geri gelemez.

Mutasyonlar KOD uzerinde (D-354/D-361) ve uygulanmadiysa test DUSER (D-370).
"""
import ast
import inspect
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "163_b4_p_ve_kosu.py"
ON_KAYIT = KOK / "results" / "b4_fps" / "ON_KAYIT.md"

sys.path.insert(0, str(KOK / "scripts" / "olcum"))
import importlib.util as _u

_sp = _u.spec_from_file_location("m163", BETIK)
M = _u.module_from_spec(_sp)
_sp.loader.exec_module(M)

KAYNAK = BETIK.read_text(encoding="utf-8")
KAYIT_METNI = ON_KAYIT.read_text(encoding="utf-8")


def _kodu(metin):
    """Yorumlar atilir — denetim YORUM uzerinde yapilmaz (D-354)."""
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


def _sahte_r(p_katman, kosu_maks, n_katman=100, p_tam=0.99):
    fov = {}
    for f in M.FOV_DUYARLILIK:
        fov[str(f)] = {"p_katman": p_katman, "p_tam": p_tam,
                       "n_katman": n_katman, "kosu_maks_s": kosu_maks}
    return {"kume": "R", "n": n_katman, "fov": fov, "kareler": []}


class OnKayitKilidi(unittest.TestCase):
    def test_capa_BETIK_AYRISTIRILIYOR(self):
        ast.parse(KAYNAK)
        self.assertTrue(ON_KAYIT.is_file())

    def test_FOV_DEGERLERI_ON_KAYITTA_GECIYOR(self):
        """EK-1 §E1.4: FOV sonuca bakilarak SECILMEZ — uc deger donduruldu."""
        self.assertEqual(len(M.FOV_DUYARLILIK), 3)
        for f in M.FOV_DUYARLILIK:
            tr = f"{f:.1f}".replace(".", ",")
            self.assertIn(tr, KAYIT_METNI,
                          f"betikteki FOV {f} on kayitta YOK — sonradan "
                          f"degistirilmis olabilir (D-107)")
        self.assertIn(M.FOV_ESAS, M.FOV_DUYARLILIK)

    def test_ESIKLER_SOZLESMEYLE_KILITLI(self):
        from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S
        self.assertEqual(M.G1_KOSU_MAKS_S, YKS_TESPIT_TAZELIK_S,
                         "G1 esigi sozlesmeden kopmus (madde 16)")
        self.assertEqual(M.G2_P_ASGARI, 0.22)
        self.assertIn("0,22", KAYIT_METNI)

    def test_URETIM_ZINCIRI_HALKALARI_DURUYOR(self):
        """Olcek tuzagi (EK-1 §E1.1) geri gelmesin: red + esikleme cagrilir."""
        kod = _kodu(KAYNAK)
        for halka in ("rota_olcek_reddi(", "_rota_kararini_esikle(",
                      "_maskeleri_icerige_kirp(", "return_reason=True"):
            self.assertIn(halka, kod,
                          f"uretim zinciri halkasi eksik: {halka}")

    def test_HUKUM_KATMANDAN_OKUNUYOR(self):
        """EK-2 kural 1: G1/G2_R hukmu p_katman'dan. p_tam yalniz baglam."""
        kod = _kodu(inspect.getsource(M.hukum))
        self.assertIn('"p_katman"', kod.replace("'", '"'),
                      "hukum() katmani okumuyor — EK-2 ihlali")
        # p_tam yalniz baglam alaninda gecebilir:
        for satir in kod.splitlines():
            if '"G1"' in satir or "G1 =" in satir:
                self.assertNotIn("p_tam", satir)


class HukumDavranisi(unittest.TestCase):
    """Metin degil DAVRANIS: hukum() sahte veriyle dogru karar veriyor mu."""

    def test_BOS_KATMAN_GECTI_SAYILMAZ(self):
        h = M.hukum(_sahte_r(p_katman=None, kosu_maks=0, n_katman=0),
                    {"p": None})
        self.assertEqual(h["G1"]["durum"], "OLCULEMEDI")
        self.assertEqual(h["G2_R"]["durum"], "OLCULEMEDI")
        self.assertEqual(h["G2_S"]["durum"], "OLCULEMEDI")

    def test_G1_SINIRDA_DUSER(self):
        """Kosu tam 5 s ise tazelik penceresi DOLMUSTUR: GECTI degil."""
        h = M.hukum(_sahte_r(p_katman=0.9, kosu_maks=5), {"p": 0.9})
        self.assertEqual(h["G1"]["durum"], "DUSTU")
        h = M.hukum(_sahte_r(p_katman=0.9, kosu_maks=4), {"p": 0.9})
        self.assertEqual(h["G1"]["durum"], "GECTI")

    def test_G2_ESIK_ALTINDA_DUSER(self):
        h = M.hukum(_sahte_r(p_katman=0.21, kosu_maks=0), {"p": 0.23})
        self.assertEqual(h["G2_R"]["durum"], "DUSTU")
        self.assertEqual(h["G2_S"]["durum"], "GECTI")

    def test_GEREKLI_FPS_FORMULU(self):
        h = M.hukum(_sahte_r(p_katman=0.5, kosu_maks=0), {"p": 0.2})
        self.assertAlmostEqual(h["gerekli_fps_R"], 1.0 / (5.0 * 0.5))
        self.assertAlmostEqual(h["gerekli_fps_S"], 1.0 / (5.0 * 0.2))

    def test_KOSULAR_DOGRU_SAYILIYOR(self):
        self.assertEqual(M._kosular([True, False, False, True, False]), [2, 1])
        self.assertEqual(M._kosular([False] * 4), [4])
        self.assertEqual(M._kosular([True, True]), [])


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_HUKUM_TAMDAN_OKUTULURSA_YAKALANIR(self):
        kod = _kodu(inspect.getsource(M.hukum))
        desen = '["p_katman"]'
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI: desen yok (D-370)")
        mutant = kod.replace(desen, '["p_tam"]')
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "p_katman kaldirildigi halde denetim gormuyor — "
                         "BOS KAPI: hukum sessizce tam kumeye kayabilirdi")

    def test_M2_FOV_DEGISTIRILIRSE_YAKALANIR(self):
        sahte_fov = 71.0
        self.assertNotIn(sahte_fov, M.FOV_DUYARLILIK,
                         "MUTASYON UYGULANAMADI: 71,0 zaten listede")
        tr = f"{sahte_fov:.1f}".replace(".", ",")
        self.assertNotIn(tr, KAYIT_METNI,
                         "on kayitta 71,0 geciyor — mutasyon ayirt edici "
                         "degil, baska deger secilmeli")

    def test_M3_ZINCIR_HALKASI_SILINIRSE_YAKALANIR(self):
        kod = _kodu(KAYNAK)
        mutant = kod.replace("rota_olcek_reddi(", "_atlanan_red(", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("rota_olcek_reddi("),
                        kod.count("rota_olcek_reddi("),
                        "olcek reddi halkasi silindigi halde sayim dusmedi")


if __name__ == "__main__":
    unittest.main()
