"""T79 KAPISI: koridor secimi gurultuye karsi DETERMINISTIK, ama GUVENLI.

Olculen kusur (D-122): Gauss sigma=2/255 (%0,8) altinda 260 karenin 9'unda
secilen koridor degisiyor. %0,8 GERCEGIN ALT SINIRIDIR.

⚠ T79 teshisi onerilen careyi KISMEN CURUTTU: ceviren 9 karenin yalniz 2'sinde
BERABERLIK vardir; kalan 7'de rota FIZIKSEL OLARAK tasinir (4 karede her
kosuda TEK serit doludur — kiyaslanacak ikinci aday yoktur). Bu paket bu
yuzden iki AYRI seyi kilitler:
  1. Beraberlik bandi GERCEK beraberligi determinize eder (ve baska bir sey
     iddia etmez).
  2. Histerezis GUVENLIGI BOZMAZ — onceki koridor gecilemez olur olmaz birakilir.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import (BERABERLIK_BANDI, beraber_adaylar,  # noqa: E402
                              koridor_histerezisi)


class BeraberlikBandiTests(unittest.TestCase):
    """Band GURULTU TABANINDAN gelir; ciplak sayi degildir (D-112: 0,04)."""

    def test_band_olculen_gurultu_tabani(self):
        self.assertEqual(0.04, BERABERLIK_BANDI)

    def test_TAM_beraberlik_iki_adayi_da_verir(self):
        """`sa_000232` olcumu: 23,00 / 23,00 -> bagil fark 0,0000."""
        self.assertEqual([0, 1], beraber_adaylar([23.0, 23.0, None]))

    def test_OLCULEN_yakin_beraberlik_bandin_ICINDE(self):
        """`sa_000258` g2 olcumu: 18,00 / 17,98 -> 0,0009."""
        self.assertEqual([1, 2], beraber_adaylar([None, 18.0, 17.98]))

    def test_BELIRGIN_fark_tek_aday_birakir(self):
        """`sa_000025`: 20,00 / 42,79 -> 0,5326, beraberlik YOK."""
        self.assertEqual([0], beraber_adaylar([20.0, 42.79, None]))

    def test_band_SINIRI(self):
        # (a - min)/a <= 0.04  ->  a <= min/0.96
        self.assertEqual([0, 1], beraber_adaylar([100.0, 104.0, None]))
        self.assertEqual([0], beraber_adaylar([100.0, 105.0, None]))

    def test_TEK_serit_beraberlik_uretmez(self):
        """Ceviren 4 karede her kosuda tek serit dolu — band burada CARESIZ."""
        self.assertEqual([1], beraber_adaylar([None, 15.0, None]))

    def test_gecersiz_girdiler_ELENIR(self):
        self.assertEqual([], beraber_adaylar([None, None, None]))
        self.assertEqual([], beraber_adaylar([]))
        self.assertEqual([1], beraber_adaylar([float("nan"), 15.0, True]))


class HisterezisGuvenligiTests(unittest.TestCase):
    """🔴 Histerezis GUVENLIGI GECIKTIREMEZ."""

    def test_onceki_GECILEMEZSE_ANINDA_birakilir(self):
        """Baglayici kural: eski koridor kapandiysa histerezis DEVREDE DEGIL."""
        secim = koridor_histerezisi(
            onceki_serit=1, aday_serit=3, gecilebilir_seritler={3},
            onceki_aciklik=90.0, aday_aciklik=20.0)
        self.assertEqual(3, secim, "gecilemez koridor histerezisle KORUNDU")

    def test_onceki_gecilebilirken_KUCUK_fark_KORUNUR(self):
        secim = koridor_histerezisi(
            onceki_serit=1, aday_serit=2, gecilebilir_seritler={1, 2},
            onceki_aciklik=20.0, aday_aciklik=20.5)
        self.assertEqual(1, secim)

    def test_aday_BELIRGIN_iyiyse_gecilir(self):
        secim = koridor_histerezisi(
            onceki_serit=1, aday_serit=2, gecilebilir_seritler={1, 2},
            onceki_aciklik=20.0, aday_aciklik=40.0)
        self.assertEqual(2, secim)

    def test_olculemiyorsa_histerezis_UYGULANMAZ(self):
        """Fail-open DEGIL fail-through: olcum yoksa aday secilir, eski
        koridor 'olcemedim' diye korunmaz."""
        for o, a in ((None, 20.0), (20.0, None), (None, None),
                     (0.0, 20.0), (float("nan"), 20.0)):
            with self.subTest(onceki=o, aday=a):
                self.assertEqual(2, koridor_histerezisi(
                    1, 2, {1, 2}, onceki_aciklik=o, aday_aciklik=a))

    def test_onceki_YOKSA_aday_secilir(self):
        self.assertEqual(2, koridor_histerezisi(None, 2, {1, 2}, 20.0, 20.1))

    def test_ayni_seritte_degisiklik_YOK(self):
        self.assertEqual(2, koridor_histerezisi(2, 2, {1, 2}, 20.0, 20.1))

    def test_aday_gecilemezse_dokunulmaz(self):
        """Aday kumede degilse karar cagirana aittir; histerezis ARA GIRMEZ."""
        self.assertEqual(3, koridor_histerezisi(1, 3, {1}, 20.0, 20.1))


class UretimYolundaTests(unittest.TestCase):
    """Band uretim yolunda GERCEKTEN kullaniliyor mu?"""

    def test_rota_serit_olcumu_bandi_KULLANIYOR(self):
        kaynak = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
        govde = kaynak.split("def _rota_serit_olcumu", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("beraber_adaylar", govde,
                      "beraberlik bandi uretim yolunda KULLANILMIYOR")

    def test_beraberlikte_COK_ROTA_PIKSELI_kazanir(self):
        """Deterministik kural: band icinde once sayim, sonra kucuk indis.

        ⚠ Beklenen serit ELLE yazilmaz: `_rota_pikselleri` ardisik noktalar
        ARASINI da tarar, dolayisiyla serit dagilimi rasterlestirmeye baglidir.
        Beklenti donen `seritler` sayimindan TURETILIR — test boylece
        rasterlestirme ayrintisina degil KURALA bakar.
        """
        import numpy as np
        import rpi_inference as R
        # dist HER YERDE ayni -> tum dolu seritler TAM beraberlikte
        dist = np.full((400, 480), 30.0, np.float32)
        rota = ([(120, y) for y in range(60)]
                + [(300, y) for y in range(59, 79)])
        olcum = R._rota_serit_olcumu(rota, dist, (0, 0, 480, 400))
        self.assertIsNotNone(olcum)
        sayim = olcum["seritler"]
        beklenen = min(
            [i for i in range(3) if sayim[i] > 0],
            key=lambda i: (-sayim[i], i)) + 1
        self.assertEqual(beklenen, olcum["darbogaz_serit"],
                         f"beraberlikte kural uygulanmadi (sayim={sayim})")

    def test_ayni_girdi_AYNI_karari_verir(self):
        """Determinizm: tarama sirasi ya da sozluk sirasi karara giremez."""
        import numpy as np
        import rpi_inference as R
        dist = np.full((400, 480), 30.0, np.float32)
        rota = ([(120, y) for y in range(60)]
                + [(300, y) for y in range(59, 79)])
        ilk = R._rota_serit_olcumu(rota, dist, (0, 0, 480, 400))
        for _ in range(5):
            self.assertEqual(ilk, R._rota_serit_olcumu(
                rota, dist, (0, 0, 480, 400)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
