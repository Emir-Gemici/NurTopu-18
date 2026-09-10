"""T168/T193 (D-378) — kabul kumesinin OLCULMUS istisna notlari.

Korunan iki gercek:
  1. `sa_000121` beyani ACIK ama C-uzayinda GECILEMEZ (D-329) -> kume tavani
     fiilen 259/260. Kumenin beyanina dayanan olcumler bunu BILMELI.
  2. `sa_000090`'da K7'nin dususu GERCEK POZITIF: karar seridi 3 'dar+bariyer'
     insa edilmis, kalinti koridor sozlesme koridorunun ve gercek arac
     genisliginin ALTINDA (T168 olcumu). "Etiket kapsami mi model mi" sorusu
     BU kare icin kapanmistir; denetci bunu her kosumda soylemeli.

Notlar HUKUM DEGISTIRMEZ — bilgi blogudur; sidecar okunamazsa denetci
davranisi degismez (fail-open BILGI, fail-closed HUKUM ilkesi).

En onemli test: sa_000090 hukmu PROZDAN degil, manifest + sozlesme
sabitlerinden HER KOSUMDA YENIDEN TURETILIR — not, kaynagindan sapamaz.
"""
import importlib.util as _u
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SIDECAR = KOK / "scripts" / "olcum" / "kabul_kumesi_bilinen_kareler.json"
DENETCI = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
sys.path.insert(0, str(KOK / "codes"))
sys.path.insert(0, str(KOK / "scripts" / "olcum"))


def _t66_manifesti():
    """T220 / K10: manifest yolu registry'nin `kabul_kumesi`sinden TURETILIR
    (65_kabul_denetcisi.kabul_kumesi_yolu, depo kokune goreli) — eskiden ciplak
    `O:/navitas-local-train/...` idi. Kume yoksa None -> testler ATLAR."""
    try:
        from importlib import import_module
        return import_module("65_kabul_denetcisi").kabul_kumesi_yolu() / "manifest.json"
    except RuntimeError:
        return KOK / "data" / "kabul" / "sentetik_arena_kadraj_t66" / "manifest.json"


MANIFEST = _t66_manifesti()

KAYNAK = DENETCI.read_text(encoding="utf-8")
NOTLAR = json.loads(SIDECAR.read_text(encoding="utf-8"))


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


class SidecarIcerigi(unittest.TestCase):
    def test_capa(self):
        self.assertIn("sa_000121.jpg", NOTLAR)
        self.assertIn("sa_000090.jpg", NOTLAR)

    def test_turler_dogru(self):
        self.assertEqual(NOTLAR["sa_000121.jpg"]["tur"], "TAVAN")
        self.assertEqual(NOTLAR["sa_000090.jpg"]["tur"],
                         "MODEL_HATASI_DOGRULANDI")

    def test_her_notun_kaniti_var(self):
        for k, v in NOTLAR.items():
            if k.startswith("_"):
                continue
            self.assertTrue(v.get("kanit"),
                            f"{k}: kanitsiz not — defter kurali madde 6")


class Sa000090HukmuYenidenTuretilir(unittest.TestCase):
    """Notun dayandigi aritmetik, kaynaklardan HER KOSUMDA yeniden kurulur."""

    def test_serit3_uc_olcutte_de_gecilemez(self):
        if not MANIFEST.is_file():
            self.skipTest("t66 manifesti bu makinede yok — turetim OLCULEMEDI")
        from costmap_path_finder import R_GEREKLI_M
        from karar_sozlesmesi import ARAC_GENISLIGI_M
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ornek = next(o for o in man["ornekler"]
                     if "sa_000090" in str(o.get("cikti")))
        arena = ornek["arena"]
        serit = next(s for s in arena["uretec_seritleri"]
                     if s.get("karar_seridi") == 3)
        self.assertEqual(serit["durum"], "dar+bariyer")
        self.assertFalse(serit["gecilebilir"])
        kutu = serit["gecilebilir_kutu"]
        self.assertIsNotNone(kutu, "dar seritte kalinti kutu bekleniyordu")
        genislik_m = kutu[2] * arena["mpp"]
        # uretim koridoru: 2 x R_GEREKLI_M
        self.assertLess(genislik_m, 2 * R_GEREKLI_M,
                        "kalinti koridor uretim koridorundan genis cikti — "
                        "notun hukmu ARTIK YANLIS, sidecar guncellenmeli")
        # gercek arac genisligi
        self.assertLess(genislik_m, ARAC_GENISLIGI_M,
                        "kalinti koridor gercek aractan genis cikti — "
                        "notun hukmu ARTIK YANLIS")
        # notun yazdigi sayi ile turetim ayni mi (0,01 m toleransla)
        self.assertAlmostEqual(genislik_m, 1.095, delta=0.01,
                               msg="nottaki 1,095 m turetimle uyusmuyor")

    def test_acik_serit_2_ve_kapali_1_3(self):
        if not MANIFEST.is_file():
            self.skipTest("t66 manifesti bu makinede yok")
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        ornek = next(o for o in man["ornekler"]
                     if "sa_000090" in str(o.get("cikti")))
        self.assertEqual(ornek["arena"]["acik_serit"], 2)
        self.assertEqual(sorted(ornek["arena"]["kapali_seritler"]), [1, 3])


class DenetciBaglantisi(unittest.TestCase):
    def test_denetci_sidecari_okuyor(self):
        kod = _kodu(KAYNAK)
        self.assertIn("kume_bilinen_kareler()", kod)
        self.assertGreaterEqual(kod.count("kume_bilinen_kareler()"), 2,
                                "hem K7 blogu hem tavan blogu okumali")

    def test_sidecar_yoksa_bos_doner(self):
        """Bilgi blogu HUKUM tasimaz: dosya yoksa denetci davranisi degismez."""
        sp = _u.spec_from_file_location("m65_bk", DENETCI)
        m = _u.module_from_spec(sp)
        sp.loader.exec_module(m)
        eski = m.BILINEN_KARELER_YOLU
        try:
            m.BILINEN_KARELER_YOLU = Path("olmayan_dosya_xyz.json")
            self.assertEqual(m.kume_bilinen_kareler(), {})
        finally:
            m.BILINEN_KARELER_YOLU = eski
        # gercek dosyayla iki kayit gelmeli
        d = m.kume_bilinen_kareler()
        self.assertIn("sa_000121.jpg", d)
        self.assertNotIn("_ne", d, "alt cizgi alanlari suzulmeli")

    def test_MUTASYON_baglanti_kaldirilinca_yakalanir(self):
        kod = _kodu(KAYNAK)
        mutant = kod.replace("kume_bilinen_kareler()", "_atlanan()", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("kume_bilinen_kareler()"),
                        kod.count("kume_bilinen_kareler()"),
                        "baglanti kaldirildigi halde sayim dusmedi")


if __name__ == "__main__":
    unittest.main()
