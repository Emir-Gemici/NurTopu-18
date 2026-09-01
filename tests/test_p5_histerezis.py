"""P5 (D-396) — YAYIN HISTEREZISI: KararYumusatici + kablolama kilidi.

ON KAYIT: results/p5_histerezis/ON_KAYIT.md (H1..H6 uygulamadan once).

Sozlesme: NO_ROUTE ASLA geciktirilmez; farkli serit ancak K ardisik karede
teyitlenirse yayina gecer; bastirma en fazla K-1 ardisik kare surebilir;
analiz katmani (61/65 zinciri) yumusaticiyi GORMEZ (madde 15).
"""
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from karar_sozlesmesi import (KARAR_HISTEREZIS_KARE,  # noqa: E402
                              KararYumusatici)

RPI = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


class DurumMakinesi(unittest.TestCase):
    def test_H2_no_route_asla_bastirilmaz(self):
        y = KararYumusatici()
        self.assertTrue(y.suz(2, None))            # rota yayimlandi
        for _ in range(10):
            self.assertTrue(y.suz(None, "KAPALI"),  # ret HEP gecer
                            "ON_KAYIT H2: NO_ROUTE bastirildi")
        self.assertTrue(y.suz(None, None), "rotasiz kare de aninda gecer")

    def test_ilk_rota_aninda_yayimlanir(self):
        self.assertTrue(KararYumusatici().suz(1, None))

    def test_no_route_sonrasi_ilk_rota_aninda(self):
        y = KararYumusatici()
        y.suz(1, None)
        y.suz(None, "KAPALI")
        self.assertTrue(y.suz(3, None),
                        "NO_ROUTE sonrasi ilk rota beklemeden yayimlanmali")

    def test_ayni_serit_hep_gecer(self):
        y = KararYumusatici()
        for _ in range(5):
            self.assertTrue(y.suz(2, None))

    def test_H3_farkli_serit_ancak_K_ardisik_teyitle(self):
        K = KARAR_HISTEREZIS_KARE
        y = KararYumusatici()
        self.assertTrue(y.suz(2, None))
        for i in range(K - 1):
            self.assertFalse(y.suz(1, None),
                             f"{i+1}. kare erken yayimladi (K={K})")
        self.assertTrue(y.suz(1, None), "K'inci teyit yayimlamali")
        self.assertTrue(y.suz(1, None), "gecis sonrasi yeni serit 'ayni'dir")

    def test_H4_tek_kare_cevrilme_bastirilir(self):
        """Gurultu deseni 2,1,2,2,...: 1 hic yayimlanmaz."""
        y = KararYumusatici()
        yayimlar = [(2, y.suz(2, None)), (1, y.suz(1, None)),
                    (2, y.suz(2, None)), (2, y.suz(2, None))]
        self.assertEqual([(2, True), (1, False), (2, True), (2, True)],
                         yayimlar, "tek-kare cevrilme yayina sizdi")

    def test_H5_bastirma_en_fazla_K_eksi_1_kare(self):
        K = KARAR_HISTEREZIS_KARE
        y = KararYumusatici()
        y.suz(2, None)
        ardisik = en_kotu = 0
        for yol in [1, 3] * (3 * K):          # surekli celisen aday
            if y.suz(yol, None):
                ardisik = 0
            else:
                ardisik += 1
                en_kotu = max(en_kotu, ardisik)
        self.assertLessEqual(en_kotu, K - 1,
                             "ON_KAYIT H5: bastirma K-1'i asti — tazelik "
                             "penceresi tehlikede")

    def test_aday_kesintisi_sayaci_sifirlar(self):
        """2 -> 1,1, 2, 1 dizisinde son 1 tek basina gecis saglayamaz."""
        K = KARAR_HISTEREZIS_KARE
        y = KararYumusatici()
        y.suz(2, None)
        if K >= 3:
            self.assertFalse(y.suz(1, None))
            self.assertFalse(y.suz(1, None))
            self.assertTrue(y.suz(2, None), "eski serit teyidi gecer")
            self.assertFalse(y.suz(1, None),
                             "aday sayaci sifirlanmadi — kesintili aday "
                             "birikimle gecis yapabilir")

    def test_gecersiz_esik_reddi(self):
        for esik in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                KararYumusatici(esik=esik)


class KablolamaKilidi(unittest.TestCase):
    """D-396 kablolamasi: iki AKIS yolu suzgecten gecer, run_image GECMEZ."""

    def test_iki_akis_yolu_suzgecli(self):
        kod = _kodu(RPI)
        self.assertEqual(
            kod.count("if yumusatici.suz(open_path, karar_reddi):"), 2,
            "run_video + run_camera yayinlari suzgecten gecmeli (2 nokta)")
        self.assertEqual(kod.count("yumusatici = KararYumusatici()"), 2,
                         "her akis kendi yumusaticisini kurmali")

    def test_run_image_suzgecsiz(self):
        kod = _kodu(RPI)
        i = kod.find("def run_image")
        j = kod.find("def run_video")
        self.assertNotIn("yumusatici", kod[i:j],
                         "run_image tek karedir; histerezis akis icindir")

    def test_MUTASYON_suzgec_dusurulurse_yakalanir(self):
        kod = _kodu(RPI)
        mutant = kod.replace("if yumusatici.suz(open_path, karar_reddi):",
                             "if True:", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("if yumusatici.suz(open_path, karar_reddi):"),
                        2, "suzgec dusuruldu ve sayim dusmedi")


if __name__ == "__main__":
    unittest.main()
