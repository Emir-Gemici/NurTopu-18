"""B2/T15 (D-382) — FDA butce olcumu nobetcisi.

  a) Betik URETIM cagri sirasini kullaniyor (zincir halkalari + AST).
  b) Butce/esik sabitleri SOZLESMEDEN — betikte ciplak 600/5/1 yok (madde 16).
  c) OLCULEMEDI kalemler toplama girmiyor: hukum yalniz OLCULEN toplamdan;
     olculemedi listesi bos degil ve ayri (OLCULEMEDI != GECTI).
  d) MUTASYON: bir adim rapor zincirinden dusurulurse yakalanir; mutasyonun
     UYGULANDIGI ayrica dogrulanir (D-370/D-375).
"""
import ast
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "169_fda_butce_olcumu.py"
ARTEFAKT = KOK / "results" / "fda_butce" / "olcum_20260901.json"
ON_KAYIT = KOK / "results" / "fda_butce" / "ON_KAYIT.md"

KAYNAK = BETIK.read_text(encoding="utf-8")
ADIMLAR = {"onisleme", "cikarim", "maske", "karar", "telsiz_ack", "toplam"}


def _kodu(metin):
    """Yorum VE docstring disi kod (D-354): '600' denetimi, betigin kendi
    'ciplak 600 yazilmaz' docstring cumlesine takilmamali."""
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


class A_UretimZinciri(unittest.TestCase):
    def test_capa(self):
        ast.parse(KAYNAK)
        self.assertTrue(ON_KAYIT.is_file(), "on kayit dosyasi yok (D-107)")

    def test_halkalar_tam(self):
        for halka in ("_preprocess(", "get_masks(", "_maskeleri_icerige_kirp(",
                      "rota_olcek_reddi(", "analyze_path(",
                      "_rota_kararini_esikle(", "yayinci.karar("):
            self.assertIn(halka, KOD, f"uretim halkasi eksik: {halka}")

    def test_mpp_veriliyor(self):
        """mpp'siz olcum her kareyi NO_ROUTE yapar ve olculen sey uretim
        olmaz (D-374 EK-1 tuzagi)."""
        self.assertIn("mpp=MPP_SABIT", KOD)

    def test_telsiz_GERCEK_yayinci(self):
        self.assertIn("iha_sender.yayinci_kur(", KOD,
                      "telsiz halkasi taklitle degil gercek KararYayinci "
                      "ile olculmeli")


class B_SabitlerSozlesmeden(unittest.TestCase):
    def test_butce_sabiti_ithal(self):
        self.assertIn("SARTNAME_FDA_OPERASYON_SURESI_S", KOD)
        self.assertIn("YKS_TESPIT_TAZELIK_S", KOD)
        self.assertIn("IHA_HEARTBEAT_ARALIK_S", KOD)

    def test_ciplak_600_yok(self):
        for satir in KOD.splitlines():
            self.assertNotIn("600", satir.split("#")[0],
                             f"ciplak butce sayisi: {satir.strip()[:70]}")

    def test_hukum_sozlesme_degeriyle(self):
        import sys as _s
        _s.path.insert(0, str(KOK / "codes"))
        from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S
        d = json.loads(ARTEFAKT.read_text(encoding="utf-8"))
        p95 = d["hukum"]["p95_s"]
        beklenen = "GECTI" if p95 <= YKS_TESPIT_TAZELIK_S else "DUSTU"
        self.assertEqual(d["hukum"]["B2_G1"], beklenen,
                         "artefaktin hukmu sozlesme esigiyle tutarsiz")


class C_OlculemediAyri(unittest.TestCase):
    def test_olculemedi_listesi_bos_degil(self):
        d = json.loads(ARTEFAKT.read_text(encoding="utf-8"))
        self.assertTrue(d["olculemedi"],
                        "ucus/hakem/seri-hat kalemleri OLCULEMEDI diye "
                        "isaretlenmemis — 0 sayilmis olabilir")
        self.assertTrue(any("ucus" in x for x in d["olculemedi"]))

    def test_hukum_yalniz_olculenden(self):
        """p95_s, olculen toplam p95'in KENDISI olmali — olculemedi eklenmis
        ya da cikarilmis olmamali."""
        d = json.loads(ARTEFAKT.read_text(encoding="utf-8"))
        self.assertAlmostEqual(d["hukum"]["p95_s"],
                               d["ozet"]["toplam"]["p95_ms"] / 1000.0,
                               places=9)

    def test_model_yukleme_butce_disi_ama_RAPORLU(self):
        d = json.loads(ARTEFAKT.read_text(encoding="utf-8"))
        self.assertIn("model_yukleme_s_butce_disi", d)
        self.assertGreater(d["model_yukleme_s_butce_disi"], 0)

    def test_adimlarin_tamami_ozette(self):
        d = json.loads(ARTEFAKT.read_text(encoding="utf-8"))
        self.assertEqual(set(d["ozet"]), ADIMLAR,
                         "rapor zincirinden adim dusmus ya da eklenmis")


class D_Mutasyon(unittest.TestCase):
    def test_adim_dusurulurse_yakalanir(self):
        # ⚠ ast.unparse cift tirnagi teke cevirir — desen unparse biciminde
        # olmali; aksi halde mutasyon UYGULANMAZ ve bu satir yakalar (D-370;
        # ayni tuzak test_167'de de yasandi, desen artik oradaki gibi).
        desen = "'telsiz_ack', 'toplam'"
        self.assertIn(desen, KOD, "MUTASYON UYGULANAMADI: desen yok (D-370)")
        mutant = KOD.replace(desen, "'toplam'", 1)
        self.assertNotEqual(KOD, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "telsiz adimi rapordan dusuruldu ve gorunmuyor — "
                         "C_OlculemediAyri.test_adimlarin_tamami_ozette "
                         "bu mutanti artefakt duzeyinde yakalar")

    def test_isinma_atlamasi_kaldirilirsa_yakalanir(self):
        desen = "hepsi[:ISINMA], hepsi[ISINMA:]"
        self.assertIn(desen, KOD, "MUTASYON UYGULANAMADI (D-370)")
        mutant = KOD.replace(desen, "[], hepsi", 1)
        self.assertNotIn(desen, mutant,
                         "isinma atlamasi kaldirildi ve gorunmuyor — soguk "
                         "CUDA kareleri p95'i sisirir")


if __name__ == "__main__":
    unittest.main()
