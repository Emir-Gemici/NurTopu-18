"""T189 — K5A (ACILI BARIYER NUFUSU) kolunun zincire BAGLI oldugunu sinar.

ON KAYIT: REVIEW_LOG D-334 (ilk) + D-336 (metrik duzeltmesi).

🔴 NEDEN VAR: K5'in yer gercegi nufusundaki HER bariyer YATAYDI (kume
T184'ten once uretildi, manifestinde `bariyer_acisi` alani bile yok). Yani
K5, T184'un duzelttigi DONME KORLUGUNU ne yakalayabilir ne de duzelmeyi
dogrulayabilirdi — TEST_SPECS SS4.1 anlaminda VAKUM KAPI.

Bu dosyanin en onemli testi `test_ACILI_kume_GERCEKTEN_acili`: K5A yanlislikla
(ya da bir "duzeltme" sirasinda) YATAY kumeye yoneltilirse kol sessizce K5'in
KOPYASI olur ve hicbir sey olcmez. O durumda buradan DUSER.
"""
import json
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DENETCI = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
KANIT = KOK / "scripts" / "olcum" / "results" / "t63" / "t189_ayirt_edicilik.json"


def _cagri(metin: str, betik: str, kume_argumani: bool) -> str:
    """`kos("<betik>", [...])` cagrilarindan `--kume` iceren/icermeyeni dondur.

    T196 dersi: mutasyon CAGRI duzeyinde, denetim DOSYA duzeyinde olursa
    test kendini kandirir. Bu yuzden burada da yalniz CAGRI govdesine bakilir.
    """
    ara, i = f'kos("{betik}"', 0
    while True:
        i = metin.find(ara, i)
        if i < 0:
            return ""
        j = metin.find("])", i)
        govde = metin[i:j + 2] if j > 0 else metin[i:]
        if ("--kume" in govde) == kume_argumani:
            return govde
        i = j if j > 0 else i + len(ara)


class K5AZincirBaglantisi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metin = DENETCI.read_text(encoding="utf-8")
        cls.cagri = _cagri(cls.metin, "66_k5_bariyer_populasyon.py", True)

    def test_K5A_verdikte_BAGLI(self):
        self.assertIn('gecti["K5A"]', self.metin,
                      "K5A `gecti` sozlugune girmiyor — VERDIKT'i etkilemez")

    def test_OLCULEMEDI_BLOKLAR(self):
        self.assertIn('gecti["K5A"] = sonuc["K5A_durum"] == "GECTI"', self.metin,
                      "K5A esitligi `== GECTI` degil — OLCULEMEDI sizabilir")

    def test_bayat_json_siliniyor(self):
        self.assertIn("k5aj.unlink(missing_ok=True)", self.metin,
                      "onceki kosumun K5A json'u silinmiyor (T125 kalibi)")

    def test_KOSUMDA_denetlenen_agirlikla_uretiliyor(self):
        self.assertTrue(self.cagri, "K5A cagrisi (--kume'li) ayristirilamadi")
        self.assertIn('"--model", str(args.model)', self.cagri,
                      "K5A olcumu denetlenen agirlikla uretilmiyor")

    def test_MUTASYON_bag_kaldirilinca_kilit_DUSER(self):
        mutant = self.metin.replace('gecti["K5A"] = sonuc["K5A_durum"] == "GECTI"',
                                    "# K5A bagi kaldirildi", 1)
        self.assertNotEqual(self.metin, mutant, "mutasyon uygulanamadi")
        self.assertNotIn('gecti["K5A"]', mutant,
                         "bag kaldirildigi hâlde kilit hâlâ 'bagli' diyor")

    def test_MUTASYON_BASKA_CAGRININ_argumani_KIRLETMEZ(self):
        """K5'in (--kume'suz) cagrisi K5A kilidini AYAKTA gostermemeli (T196)."""
        bozuk = self.cagri.replace('"--model", str(args.model)',
                                   '"--model", "models/baska.pt"')
        mutant = self.metin.replace(self.cagri, bozuk, 1)
        self.assertNotEqual(self.metin, mutant, "mutasyon uygulanamadi")
        self.assertIn('"--model", str(args.model)', mutant,
                      "on kosul: desen zincirde BASKA yerde de gecmeli")
        self.assertNotIn('"--model", str(args.model)',
                         _cagri(mutant, "66_k5_bariyer_populasyon.py", True),
                         "K5A cagrisi bozuldugu hâlde kilit 'ayakta' diyor")


class AciliKumeGercektenAcili(unittest.TestCase):
    """🔴 EN ONEMLI TEST: kol YATAY kumeye yoneltilirse K5'in KOPYASI olur."""

    @classmethod
    def setUpClass(cls):
        import sys
        sys.path.insert(0, str(KOK / "scripts" / "olcum"))
        from importlib import import_module
        cls.mod = import_module("65_kabul_denetcisi")

    def test_registry_ALANI_VAR_ve_dizin_MEVCUT(self):
        yol = self.mod.kabul_kumesi_acili_yolu()
        self.assertTrue(yol.is_dir(), f"acili kume dizini yok: {yol}")

    def test_YATAY_kumeyle_AYNI_DEGIL(self):
        self.assertNotEqual(
            self.mod.kabul_kumesi_acili_yolu().resolve(),
            self.mod.kabul_kumesi_yolu().resolve(),
            "K5A, K5 ile AYNI kumeye bakiyor — kol K5'in KOPYASI, "
            "hicbir sey olcmuyor (vakum kapi)")

    def test_manifest_bariyer_acisi_SIFIR_DEGIL(self):
        m = json.loads((self.mod.kabul_kumesi_acili_yolu() / "manifest.json")
                       .read_text(encoding="utf-8"))
        aci = m.get("parametreler", {}).get("bariyer_acisi")
        self.assertIsNotNone(aci, "manifestte `bariyer_acisi` alani YOK — "
                                  "kume T184 oncesi uretecle uretilmis olabilir")
        self.assertGreater(aci, 0.0,
                           "acili kumenin bariyer acisi 0 — bariyerlerin hepsi "
                           "YATAY, kol donme korlugunu olcemez")

    def test_YATAY_kume_hâlâ_ACISIZ(self):
        """Capa: yatay kume DEGISTIRILMEMELI (K1/K7 capalari ona bagli)."""
        m = json.loads((self.mod.kabul_kumesi_yolu() / "manifest.json")
                       .read_text(encoding="utf-8"))
        self.assertIn(m.get("parametreler", {}).get("bariyer_acisi", 0.0),
                      (0.0, None),
                      "YATAY kabul kumesi degistirilmis — K1/K7 ON KAYITLI "
                      "sayilari artik baska bir dagilima ait")


class AyirtEdicilikKaniti(unittest.TestCase):
    """ON KAYIT D-336'nin uc sarti KANITLA karsilanmis olmali."""

    def test_kanit_dosyasi_VAR(self):
        self.assertTrue(KANIT.is_file(),
                        f"ayirt edicilik kaniti yok: {KANIT} — "
                        "`156_t189_bariyer_aci_kanit.py` kosulmali")

    def test_AYIRT_EDICI(self):
        d = json.loads(KANIT.read_text(encoding="utf-8"))
        ok = d["_on_kayit"]
        self.assertGreaterEqual(ok["sart1_acili_dusus_puan"], 40.0,
                                "acili nufusta T184 oncesi dedektorun dususu "
                                "40 puandan az — nufus ayirt edici DEGIL")
        self.assertTrue(ok["sart3"],
                        "mutant YATAY nufusta da dusuyor — kusur donmeye ozgu "
                        "degil, kontrol tutmadi")
        self.assertTrue(ok["ayirt_edici"])

    def test_YATAY_kontrolu_BIREBIR(self):
        """Yatayda mutant == saglam: T184 birlesimi yatayda HICBIR SEY eklemez."""
        d = json.loads(KANIT.read_text(encoding="utf-8"))
        self.assertEqual(d["yatay_mutant"]["bariyerli"],
                         d["yatay_saglam"]["bariyerli"],
                         "yatay nufusta iki dedektor AYRISIYOR — T184 birlesimi "
                         "yatay davranisi DEGISTIRMIS olur (madde 15 riski)")


if __name__ == "__main__":
    unittest.main()
