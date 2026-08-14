"""T83 KAPISI: olcek UC KATMANDAN turetilir ve KAYNAGINI BEYAN EDER.

Kusur (REVIEW_LOG D-124): `mpp` yalnizca telemetriden turetilebiliyordu.
Telemetrisiz goruntude `OLCEK_YOK` duser ve C-uzayi HIC kosmaz — 67 gercek
otopark karesinin 67'sinde olan tam budur.

🔴 BU PAKETIN OMURGASI SESSIZ DUSUS YASAGIDIR. Kahin bir olcek uretmekle
yukumlu DEGILDIR; uretirse HANGI KATMANDAN uretildigini soylemekle yukumludur.
Katman dustukce guven de duser — telemetri disi bir olcek telemetriyle AYNI
guvende sunulamaz.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import rpi_inference as R  # noqa: E402
from karar_sozlesmesi import (OLCEK_GUVEN_CARPANI,  # noqa: E402
                              OLCEK_KAYNAK_ARAC, OLCEK_KAYNAK_ARENA,
                              OLCEK_KAYNAK_SIRASI, OLCEK_KAYNAK_TELEMETRI,
                              SENARYO_BOYUTLARI_M, mpp_arac_referansindan,
                              mpp_arena_sinirindan, olcek_guveni_uygula,
                              olcek_kahini)


class KatmanSirasiTests(unittest.TestCase):
    """Telemetri OTORITEDIR: varsa digerleri DEVREYE GIRMEZ."""

    def test_TELEMETRI_varken_digerleri_DEVREYE_GIRMEZ(self):
        s = olcek_kahini(irtifa_m=30.0, goruntu_genislik_px=1024,
                         yatay_fov_derece=70.0,
                         arena_sinir_px=800.0, senaryo="HTAB",
                         arac_kisa_kenar_px=24.0)
        self.assertEqual(OLCEK_KAYNAK_TELEMETRI, s["kaynak"])
        self.assertEqual(1.00, s["guven_carpani"])

    def test_TELEMETRI_yoksa_ARENA_devreye_girer(self):
        s = olcek_kahini(arena_sinir_px=1000.0, senaryo="HTAB",
                         arac_kisa_kenar_px=24.0)
        self.assertEqual(OLCEK_KAYNAK_ARENA, s["kaynak"])
        self.assertAlmostEqual(50.0 / 1000.0, s["mpp"])

    def test_ILK_IKISI_yoksa_ARAC_devreye_girer(self):
        s = olcek_kahini(arac_kisa_kenar_px=24.0)
        self.assertEqual(OLCEK_KAYNAK_ARAC, s["kaynak"])
        self.assertAlmostEqual(1.80 / 24.0, s["mpp"])

    def test_HICBIRI_yoksa_FAIL_CLOSED(self):
        s = olcek_kahini()
        self.assertIsNone(s["mpp"])
        self.assertIsNone(s["kaynak"])
        self.assertEqual(0.0, s["guven_carpani"])

    def test_sira_SOZLESMEDE_yazili(self):
        self.assertEqual((OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                          OLCEK_KAYNAK_ARAC), OLCEK_KAYNAK_SIRASI)


class SessizDususYasagiTests(unittest.TestCase):
    """Hangi katmanin NEDEN devreye girmedigi KAYITLI olmali."""

    def test_denenen_katmanlar_SEBEBIYLE_kayitli(self):
        s = olcek_kahini(arac_kisa_kenar_px=24.0)
        kaynaklar = [k for k, _ in s["denenen"]]
        self.assertEqual([OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                          OLCEK_KAYNAK_ARAC], kaynaklar)
        for _, sebep in s["denenen"]:
            self.assertTrue(sebep.strip(), "sebep BOS birakilmis")

    def test_uretilemeyince_UC_sebep_de_yazili(self):
        s = olcek_kahini()
        self.assertEqual(3, len(s["denenen"]))
        self.assertIsNone(s["kaynak"])

    def test_kaynak_KARAR_NESNESINE_yaziliyor(self):
        """`analyze_path` olcek kaynagini olcum sozlugune koymali."""
        import numpy as np
        trav = np.zeros((240, 240), np.uint8)
        trav[:, 100:140] = 1
        _yol, _g, _wp, _ret, olcum = R.analyze_path(
            trav, icerik=(0, 0, 240, 240), mpp=0.05,
            return_reason=True, return_olcum=True)
        if olcum is not None:
            self.assertIn("olcek_kaynagi", olcum)
            self.assertIn("olcek_guven_carpani", olcum)


class GuvenDusmeliTests(unittest.TestCase):
    """🔴 Katman 2/3 telemetriyle AYNI guvende sunulamaz."""

    def test_TELEMETRI_disi_katmanlar_1den_KUCUK(self):
        self.assertEqual(1.00, OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_TELEMETRI])
        for k in (OLCEK_KAYNAK_ARENA, OLCEK_KAYNAK_ARAC):
            with self.subTest(kaynak=k):
                self.assertLess(OLCEK_GUVEN_CARPANI[k], 1.00)
                self.assertGreater(OLCEK_GUVEN_CARPANI[k], 0.0)

    def test_guven_KAYNAGA_gore_iniyor(self):
        self.assertAlmostEqual(0.80, olcek_guveni_uygula(
            0.80, OLCEK_KAYNAK_TELEMETRI))
        self.assertLess(olcek_guveni_uygula(0.80, OLCEK_KAYNAK_ARAC), 0.80)
        self.assertLess(olcek_guveni_uygula(0.80, OLCEK_KAYNAK_ARENA), 0.80)

    def test_bilinmeyen_kaynak_guveni_SIFIRLAR(self):
        self.assertEqual(0.0, olcek_guveni_uygula(0.9, "uydurma_kaynak"))

    def test_gecersiz_guven_SIFIR_doner(self):
        for g in (None, True, float("nan"), float("inf"), -1.0, 0.0, "0.5"):
            with self.subTest(guven=repr(g)):
                self.assertEqual(0.0, olcek_guveni_uygula(
                    g, OLCEK_KAYNAK_TELEMETRI))

    def test_analyze_path_VARSAYILANI_telemetri(self):
        """Geriye uyum: mevcut cagri yerleri BIREBIR ayni guveni almali."""
        import inspect
        imza = inspect.signature(R.analyze_path)
        self.assertEqual(OLCEK_KAYNAK_TELEMETRI,
                         imza.parameters["olcek_kaynagi"].default)


class SenaryoBeyanEdilirTests(unittest.TestCase):
    """🔴 Senaryo TAHMIN EDILMEZ: yanlis senaryo 2,5 kat olcek hatasidir."""

    def test_senaryo_BEYAN_EDILMEDIYSE_katman_devreye_GIRMEZ(self):
        for senaryo in (None, "", "htab", "ARENA", 50, True):
            with self.subTest(senaryo=repr(senaryo)):
                self.assertIsNone(mpp_arena_sinirindan(1000.0, senaryo))

    def test_YANLIS_senaryo_2_5_KAT_hata_uretir(self):
        """Neden tahmin edilmedigini SAYIYLA kaydet."""
        dogru = mpp_arena_sinirindan(1000.0, "HTAB")     # 50 m
        yanlis = mpp_arena_sinirindan(1000.0, "FDA")     # 20 m
        self.assertAlmostEqual(2.5, dogru / yanlis, places=6)

    def test_uc_senaryo_da_TANIMLI(self):
        self.assertEqual({"HTAB": 50.0, "IHA_IB": 30.0, "FDA": 20.0},
                         SENARYO_BOYUTLARI_M)

    def test_sinir_TESPIT_EDILEMEDIYSE_katman_devreye_GIRMEZ(self):
        """"kare = arena" VARSAYILMAZ: sinir yoksa olcek de yok."""
        for px in (None, 0, -5, float("nan"), float("inf"), True, "1000"):
            with self.subTest(sinir=repr(px)):
                self.assertIsNone(mpp_arena_sinirindan(px, "HTAB"))
        s = olcek_kahini(senaryo="HTAB", arena_sinir_px=None)
        self.assertNotEqual(OLCEK_KAYNAK_ARENA, s["kaynak"])


class AracReferansiTests(unittest.TestCase):
    """D-124: DOTA-OBB kisa kenari = govde genisligi ~1,80 m."""

    def test_kisa_kenardan_mpp(self):
        self.assertAlmostEqual(1.80 / 24.0, mpp_arac_referansindan(24.0))

    def test_gecersiz_girdi_FAIL_CLOSED(self):
        for px in (None, 0, -3, float("nan"), float("inf"), True, "24"):
            with self.subTest(px=repr(px)):
                self.assertIsNone(mpp_arac_referansindan(px))

    def test_arac_genisligi_bandi_DUYARLILIGI(self):
        """1,70-1,90 m bandi olcegi %11,1 aralikta oynatir — kayitli olsun.

        (1,90 - 1,70) / 1,80 = 0,1111. Bu, arac referansinin INDIRGENEMEZ
        belirsizligidir ve `OLCEK_GUVEN_CARPANI` orada 1,00 OLAMAZ demenin
        sayisal gerekcesidir.
        """
        alt = mpp_arac_referansindan(24.0, 1.70)
        ust = mpp_arac_referansindan(24.0, 1.90)
        self.assertAlmostEqual(0.11111,
                               (ust - alt) / mpp_arac_referansindan(24.0),
                               places=4)

    def test_gecersiz_arac_genisligi_REDDEDILIR(self):
        for g in (0, -1.8, float("nan"), True, None, "1.8"):
            with self.subTest(g=repr(g)):
                self.assertIsNone(mpp_arac_referansindan(24.0, g))


if __name__ == "__main__":
    unittest.main(verbosity=2)
