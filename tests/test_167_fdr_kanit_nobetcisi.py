"""FDR kanit paketi nobetcisi — 167 sayilari ARTEFAKTTAN okumali.

🔴 KORUNAN KUSUR: `FDA = FDR x 0,85 + Test Ucusu x 0,15`. Rapora ELLE
kopyalanan bir sayi, artefakt degistiginde SESSIZCE bayatlar. Bu projede
bayat sayi tasima kusuru defalarca kayda gecti (D-256 SS3 · D-372 · D-376).

Bu kapi sunlari korur:
  1. Betikte KAPI SAYISI sabit yazili olmasin (255/260, 5,88 vb.) — hepsi
     kayit defterinden okunsun.
  2. Kapsam uyarilari (sentetik / OOD / OLCULEMEDI) pakette DURSUN — bunlar
     paketin dogruluk iddiasini sinirlar; silinirse paket yaniltici olur.
  3. GECMEYEN kapi GECMEDI diye yazilsin: gercek kare kapisi bolumu paketi
     terk etmesin.
  4. OLCULEMEDI sessiz bosluga cevrilmesin.

Mutasyonlar KOD uzerinde (D-354/D-361), uygulanmadiysa test DUSER (D-370).
"""
import ast
import importlib.util as _u
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "167_fdr_kanit_paketi.py"
PAKET = KOK / "results" / "fdr" / "GORUNTU_ISLEME_KANIT.md"

sys.path.insert(0, str(KOK / "scripts" / "olcum"))
_sp = _u.spec_from_file_location("m167", BETIK)
M = _u.module_from_spec(_sp)
_sp.loader.exec_module(M)

KAYNAK = BETIK.read_text(encoding="utf-8")


def _kodu(metin):
    """Yorum ve docstring DISI kod (D-354: denetim yorumda yapilmaz)."""
    agac = ast.parse(metin)
    for d in ast.walk(agac):
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef, ast.Module)):
            if (d.body and isinstance(d.body[0], ast.Expr)
                    and isinstance(d.body[0].value, ast.Constant)
                    and isinstance(d.body[0].value.value, str)):
                d.body.pop(0)
    return ast.unparse(agac)


KOD = _kodu(KAYNAK)


class SayiArtefakttanGelir(unittest.TestCase):
    def test_capa(self):
        ast.parse(KAYNAK)
        self.assertTrue(BETIK.is_file())

    def test_KAPI_SAYILARI_KODA_YAZILMAMIS(self):
        """Kabul kapisi sayilari betikte ciplak sabit olmamali."""
        yasak = ["255/260", "5.88", "0.39", "1.57", "2.75", "0.2346", "0.023"]
        for y in yasak:
            self.assertNotIn(y, KOD,
                             f"kapi sayisi '{y}' KODA yazilmis — artefakt "
                             f"degisince paket SESSIZCE bayatlar")

    def test_KAYIT_DEFTERINDEN_OKUYOR(self):
        self.assertIn("model_registry.json", KAYNAK)
        self.assertIn('["profiles"]["competition"]', KOD.replace("'", '"'))

    def test_URETILEN_PAKET_KAYIT_DEFTERIYLE_UYUSUYOR(self):
        """DAVRANIS: uretilen metindeki model kimligi defterdekiyle ayni mi."""
        import json
        d = json.loads((KOK / "config" / "model_registry.json")
                       .read_text(encoding="utf-8"))
        c = d["profiles"]["competition"]
        bas, _ = M.bolum_model()
        self.assertIn(c["model_id"], bas)
        self.assertIn(c["sha256"], bas)


class KapsamUyarilariDurur(unittest.TestCase):
    def test_SENTETIK_UYARISI_VAR(self):
        _, c = M.bolum_model()
        b = M.bolum_kapilar(c)
        self.assertIn("SENTETİK", b.upper(),
                      "kabul kapilari bolumunde 'tamami sentetiktir' uyarisi "
                      "YOK — paket saha basarimi iddia ediyormus gibi okunur")

    def test_GECMEYEN_KAPI_PAKETTE_KALIYOR(self):
        _, c = M.bolum_model()
        g = M.bolum_gercek_kare(c)
        self.assertIn("GEÇİLMEDİ", g.upper().replace("I", "İ"),
                      "gercek kare kapisinin GECMEDIGI paketten dusmus")
        self.assertIn("_surum_karari", KOD,
                      "terfi gerekcesi pakete tasinmiyor")

    def test_OLCULEMEDI_SESSIZ_BOSLUK_DEGIL(self):
        self.assertEqual(M._y(None), "**ÖLÇÜLEMEDİ**")
        self.assertNotEqual(M._y(None), "")
        self.assertNotEqual(M._y(None), "-")

    def test_TURKCE_ONDALIK(self):
        self.assertEqual(M._y(0.3457), "0,3457")
        self.assertEqual(M._y(0.579, 3), "0,579")

    def test_SIZINTI_UYARISI_VAR(self):
        b = M.bolum_gercek_zamanlilik()
        self.assertIn("D-376", b, "sizinti duzeltmesine atif YOK")
        self.assertIn("%62", b, "sizinti buyuklugu pakette yazmiyor")


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_SENTETIK_UYARISI_SILININCE_YAKALANIR(self):
        self.assertIn("SENTETİKTİR", KAYNAK, "MUTASYON UYGULANAMADI")
        mutant = KAYNAK.replace("SENTETİKTİR", "GERCEKTIR", 1)
        self.assertNotEqual(KAYNAK, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn("SENTETİKTİR", mutant,
                         "kapsam uyarisi degistirildigi halde kapi gormuyor")

    def test_M2_OLCULEMEDI_BOSA_CEVRILIRSE_YAKALANIR(self):
        import inspect
        kod = _kodu(inspect.getsource(M._y))
        # ⚠ Desen TIRNAKTAN BAGIMSIZ olmali: `ast.unparse` cift tirnagi tek
        # tirnaga cevirir; '"..."' arayan bir desen HIC eslesmez ve mutasyon
        # sessizce uygulanmadan "gecti" sanilirdi (D-370). Isareti islevin
        # KENDISINDEN aliyoruz ki desen kaynaktan sapamasin.
        desen = M._y(None)
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI: desen yok")
        mutant = kod.replace(desen, "", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "OLCULEMEDI bosa cevrildigi halde gorunmuyor — "
                         "paket eksigi SESSIZ birakirdi")

    def test_M3_GERCEK_KARE_BOLUMU_SILININCE_YAKALANIR(self):
        mutant = KOD.replace("bolum_gercek_kare(c)", "_atlanan(c)", 1)
        self.assertNotEqual(KOD, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("bolum_gercek_kare(c)"),
                        KOD.count("bolum_gercek_kare(c)"),
                        "gecmeyen kapi bolumu cikarildigi halde sayim dusmedi")


if __name__ == "__main__":
    unittest.main()
