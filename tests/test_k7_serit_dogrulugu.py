"""K7 KAPISI (ON_KAYIT SS34 · REVIEW_LOG D-314): yayinlanan SERIT DOGRULUGU.

NEDEN VAR: sartname SS2.1/SS5.3.2 yanlis guzergaha 0 PUAN verir ve hakem
NUMARAYI canli onaylar (SS2.2.3). Kabul zinciri 2026-08-27'ye kadar bu ekseni
HIC olcmuyordu — K1 rota URETIMINI, K6 rotanin yol USTUNDE olmasini olcer.

NEDEN DONDURULMUS ALT KUME: serit numarasi ucte birlerden hesaplanir; koridor
kapisi bir sinira denk geldiginde etiket TANIM GEREGI belirsizdir (T101).
Olculdu (D-312): kabul kumesinin %54'u boyle ve serit ayrismasinin %100'u
oradan geliyor. Kapi YALNIZ `config/k7_iyi_kosullu_kume.json` (88 kare)
uzerinde olcer; orada manifest ile koridor envanteri %100 uyusur.

BOS KAPI YASAGI (TEST_SPECS SS4.1) — on kayitli UC mutasyon:
  1. serit karari bozulunca K7 DUSMELI (zincir duyarli mi),
  2. alt kume listesi degisince kilit DUSMELI (kume sessizce kayamaz),
  3. az rota uretip %100 dogruluk elde etmek K7'yi GECIREMEMELI (payda oyunu).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KUME_DOSYASI = KOK / "config" / "k7_iyi_kosullu_kume.json"
OLCUM = KOK / "results" / "t165" / "k7_olcum.json"

# Alt kumenin DONDURULMUS ozeti. Degisirse bu test DUSER ve degisiklik
# ON KAYITLA gerekcelendirilmek zorunda kalir (kume sessizce kayamaz).
# 🔴 OZET ICERIK UZERINDEN alinir (kanonik JSON), BAYT uzerinden DEGIL: satir
# sonu cevrimi (CRLF/LF) ya da girinti degisikligi kilidi KIRMAMALI; kilit
# LISTENIN KENDISINI korur, dosyanin bicimini degil.
KUME_SHA256 = "f522703eccd9c1bb4d8e861c2b7cc28bb5322a0f0a620e05c188f64704a79d66"


def _kanonik_ozet(yol: Path) -> str:
    veri = json.loads(yol.read_text(encoding="utf-8"))
    kanonik = json.dumps(veri, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(kanonik).hexdigest()


def _modul(ad: str, yol: Path):
    if str(KOK / "scripts" / "olcum") not in sys.path:
        sys.path.insert(0, str(KOK / "scripts" / "olcum"))
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _denetci():
    return _modul("_k7_denetci", KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py")


class KumeKilidi(unittest.TestCase):
    """MUTASYON 2: alt kume listesi degisirse kapi baska bir seyi olcer."""

    def test_dosya_var_ve_88_kare(self):
        self.assertTrue(KUME_DOSYASI.is_file(), "K7 alt kumesi yok")
        veri = json.loads(KUME_DOSYASI.read_text(encoding="utf-8"))
        self.assertEqual(88, veri["n"])
        self.assertEqual(88, len(veri["kareler"]))

    def test_sha256_DONDURULMUS(self):
        sha = _kanonik_ozet(KUME_DOSYASI)
        self.assertEqual(
            KUME_SHA256, sha,
            "K7 alt kumesi DEGISTI. Bu, kapinin olctugu seyi degistirir; "
            "degisiklik ON KAYITLA gerekcelendirilmeli ve bu sabit orada "
            "guncellenmelidir (REVIEW_LOG D-314).")

    def test_her_karenin_referans_seridi_var(self):
        veri = json.loads(KUME_DOSYASI.read_text(encoding="utf-8"))
        for k in veri["kareler"]:
            with self.subTest(kare=k["kare"]):
                self.assertIn(k["referans_serit"], (1, 2, 3))
                # Iyi kosulluluk sarti: kapi TEK seride dusmeli.
                y = k["serit_yayilimi"]
                self.assertEqual(y[0], y[1],
                                 "kotu kosullu kare alt kumeye sizmis")

    def test_gerekce_dosyada_yazili(self):
        veri = json.loads(KUME_DOSYASI.read_text(encoding="utf-8"))
        for alan in ("_neden", "_turetme", "_uyari"):
            self.assertIn(alan, veri)
        self.assertIn("T101", veri["_neden"])


class EsikVeUcDurum(unittest.TestCase):

    def setUp(self):
        self.m = _denetci()

    def test_esikler_sozlesmede(self):
        self.assertEqual(0.95, self.m.ESIK["K7_serit_dogruluk_min"])
        self.assertEqual(80, self.m.ESIK["K7_rota_uretilen_min"])

    def test_girdi_yoksa_OLCULEMEDI(self):
        self.assertEqual("OLCULEMEDI", self.m.k7_durumu(None)[0])
        self.assertEqual("OLCULEMEDI", self.m.k7_durumu({})[0])

    def test_payda_sifirsa_OLCULEMEDI_GECTI_DEGIL(self):
        durum, _d = self.m.k7_durumu({"rota_uretilen": 0, "dogru": 0})
        self.assertEqual("OLCULEMEDI", durum,
                         "payda 0 GECTI sayildi — vakum kapi")

    def test_esik_ustu_GECTI(self):
        durum, d = self.m.k7_durumu({"rota_uretilen": 85, "dogru": 84})
        self.assertEqual("GECTI", durum)
        self.assertAlmostEqual(84 / 85, d["dogruluk"])

    def test_esik_alti_DUSTU(self):
        self.assertEqual("DUSTU",
                         self.m.k7_durumu({"rota_uretilen": 85, "dogru": 70})[0])

    def test_MUTASYON_3_payda_oyunu_GECEMEZ(self):
        """Az rota uretip %100 dogruluk elde etmek kapiyi GECIREMEZ."""
        durum, d = self.m.k7_durumu({"rota_uretilen": 2, "dogru": 2})
        self.assertEqual("DUSTU", durum,
                         "2 karede %100 dogruluk kapiyi gecirdi — payda oyunu "
                         "yasagi calismiyor")
        self.assertFalse(d["payda_yeterli"])
        self.assertEqual(1.0, d["dogruluk"])

    def test_esik_SINIRINDA_davranis(self):
        """>= karsilastirmasi: tam esikte GECER, bir altinda DUSER."""
        self.assertEqual("GECTI", self.m.k7_durumu(
            {"rota_uretilen": 80, "dogru": 76})[0])          # %95,0 · payda 80
        self.assertEqual("DUSTU", self.m.k7_durumu(
            {"rota_uretilen": 79, "dogru": 79})[0])          # payda 79 < 80


class OlculenTaban(unittest.TestCase):
    """Uretim modelinin olculen degeri kapidan GECIYOR mu — ve kayit duruyor mu."""

    def setUp(self):
        if not OLCUM.is_file():
            self.skipTest("K7 olcum dosyasi yok")
        self.ozet = json.loads(OLCUM.read_text(encoding="utf-8"))["ozet"]
        self.m = _denetci()

    def test_uretim_tabani_GECIYOR(self):
        durum, d = self.m.k7_durumu(self.ozet)
        self.assertEqual("GECTI", durum, d)

    def test_taban_sayilari_kayitla_tutarli(self):
        self.assertEqual(88, self.ozet["kume_n"])
        self.assertEqual(85, self.ozet["rota_uretilen"])
        self.assertEqual(84, self.ozet["dogru"])


class OlcumBetigi(unittest.TestCase):
    """Betik alt kumeyi DOSYADAN okumali, kosum aninda TURETMEMELI."""

    def setUp(self):
        self.m = _modul("_k7_olcum",
                        KOK / "scripts" / "olcum" / "151_k7_serit_dogrulugu.py")

    def test_kume_dosyadan_okunuyor(self):
        veri = self.m.iyi_kosullu_kume()
        self.assertEqual(88, veri["n"])

    def test_tutarsiz_dosya_REDDEDILIR(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "k.json"
            p.write_text(json.dumps({"n": 88, "kareler": [{"kare": "a"}]}),
                         encoding="utf-8")
            with self.assertRaises(ValueError):
                self.m.iyi_kosullu_kume(p)

    def test_betik_koridor_adaylarini_YENIDEN_CAGIRMIYOR(self):
        kaynak = (KOK / "scripts" / "olcum" /
                  "151_k7_serit_dogrulugu.py").read_text(encoding="utf-8")
        self.assertNotIn("koridor_adaylari", kaynak,
                         "kapi alt kumeyi kosum aninda yeniden turetiyor — "
                         "kume sessizce kayabilir")
        self.assertIn("k7_iyi_kosullu_kume.json", kaynak)


class ZincirDuyarliligi(unittest.TestCase):
    """MUTASYON 1: serit karari bozulunca dogruluk COKMELI.

    Zincirin serit kararina duyarliligi genel kapinin KOL 2'sinde de olculur
    (T156/D-299: `rota_serit_karari` bozulunca 15/15 -> 6/15). Burada K7'nin
    OZETLEME yolunun ayni bozulmayi DUSUS olarak raporladigi kilitlenir.
    """

    def setUp(self):
        self.m = _modul("_k7_olcum2",
                        KOK / "scripts" / "olcum" / "151_k7_serit_dogrulugu.py")
        self.d = _denetci()

    def test_bozuk_serit_karari_DUSURUR(self):
        veri = json.loads(KUME_DOSYASI.read_text(encoding="utf-8"))
        # Sabit serit yayinlayan bir model taklidi: her karede 1 der.
        satirlar = [{"kare": k["kare"], "referans_serit": k["referans_serit"],
                     "yayinlanan": 1, "ret": None,
                     "dogru": k["referans_serit"] == 1}
                    for k in veri["kareler"]]
        ozet = self.m.ozetle(satirlar, veri["n"])
        durum, detay = self.d.k7_durumu(ozet)
        self.assertEqual("DUSTU", durum,
                         f"sabit serit yayinlayan model K7'yi gecti: {detay}")
        self.assertLess(detay["dogruluk"], 0.95)

    def test_kusursuz_model_GECER(self):
        veri = json.loads(KUME_DOSYASI.read_text(encoding="utf-8"))
        satirlar = [{"kare": k["kare"], "referans_serit": k["referans_serit"],
                     "yayinlanan": k["referans_serit"], "ret": None,
                     "dogru": True} for k in veri["kareler"]]
        ozet = self.m.ozetle(satirlar, veri["n"])
        self.assertEqual("GECTI", self.d.k7_durumu(ozet)[0])


if __name__ == "__main__":
    unittest.main()
