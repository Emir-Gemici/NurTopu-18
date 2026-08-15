"""T88 KAPISI: arena izgara dedektoru NE YAPAR, NE YAPMAZ?

Bu paket iki seyi ayri ayri civiler:
  1. ✅ SINIFLANDIRMA calisir: izgarasiz karede `arena_izgarasi_var_mi` False
     doner — "kare = arena" VARSAYIMI YOKTUR (kahinin sozlesmesi).
  2. 🔴 YERELLESTIRME CALISMAZ: olculen aciklik gercek sinirdan KUCUKTUR ve
     hata EMNIYETSIZ yondedir. Bu yuzden hicbir uretim yolu onu cagirmaz.
     Asagidaki test tam da BU BAGLANTISIZLIGI kilitler — biri ileride
     baglarsa kapi kirmizi yanar ve once bu kaydi okur (REVIEW_LOG D-138).
"""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import rpi_inference  # noqa: E402
from karar_sozlesmesi import (ARENA_IZGARA_ASGARI_PARCA,  # noqa: E402
                              arena_izgara_acikligi_px,
                              arena_izgara_parcalari,
                              arena_izgarasi_var_mi,
                              olcek_kahini, rota_olcek_reddi)

ARENA_KARESI = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"


def _duz_zemin(h=400, w=600, ton=150):
    return np.full((h, w, 3), ton, np.uint8)


class SessizVarsayimYokTests(unittest.TestCase):
    """🔴 'KARE = ARENA' VARSAYMA — dedektorun ilk sozlesmesi."""

    def test_duz_karede_izgara_YOK(self):
        self.assertFalse(arena_izgarasi_var_mi(_duz_zemin()))
        self.assertIsNone(arena_izgara_acikligi_px(_duz_zemin()))

    def test_gurultulu_karede_izgara_YOK(self):
        rng = np.random.default_rng(0)
        gurultu = rng.integers(0, 255, (400, 600, 3), dtype=np.uint8)
        self.assertFalse(arena_izgarasi_var_mi(gurultu))
        self.assertIsNone(arena_izgara_acikligi_px(gurultu))

    def test_TEK_AILE_yetmez_iki_dik_aile_gerekir(self):
        """Yalniz yatay cizgi (yol seridi, park cizgisi) arena DEGILDIR."""
        im = _duz_zemin(400, 600)
        for y in range(40, 380, 40):
            im[y:y + 2, :] = 20                       # bol yatay, sifir dikey
        dikey, yatay = arena_izgara_parcalari(im)
        self.assertGreaterEqual(len(yatay), ARENA_IZGARA_ASGARI_PARCA)
        self.assertLess(len(dikey), ARENA_IZGARA_ASGARI_PARCA)
        self.assertFalse(arena_izgarasi_var_mi(im))

    def test_bozuk_girdide_FAIL_CLOSED(self):
        for kotu in (np.zeros((0, 0, 3), np.uint8), np.zeros((10, 10), np.uint8),
                     np.zeros((4, 4, 3), np.uint8)):
            with self.subTest(sekil=kotu.shape):
                self.assertEqual(([], []), arena_izgara_parcalari(kotu))
                self.assertIsNone(arena_izgara_acikligi_px(kotu))

    def test_izgara_bulunmayinca_kahin_katman2yi_ATLAR_ve_kapi_REDDEDER(self):
        """Kapi (d): sinir yoksa olcek yok, olcek yoksa rota YAYINLANMAZ."""
        kahin = olcek_kahini(arena_sinir_px=None, senaryo="HTAB")
        self.assertIsNone(kahin["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(kahin["mpp"]))
        self.assertIn("arena_siniri", [k for k, _ in kahin["denenen"]])


class IzgaraTaninirTests(unittest.TestCase):
    """Sentetik izgara: iki dik aile varsa TANINIR (pozitif kontrol)."""

    def test_iki_dik_aile_varsa_izgara_TANINIR(self):
        im = _duz_zemin(500, 700)
        for y in range(50, 470, 45):
            im[y:y + 2, 40:660] = 20
        for x in range(60, 660, 45):
            im[40:470, x:x + 2] = 20
        self.assertTrue(arena_izgarasi_var_mi(im))
        self.assertIsNotNone(arena_izgara_acikligi_px(im))

    @unittest.skipUnless(ARENA_KARESI.is_file(), "gercek arena karesi diskte yok")
    def test_GERCEK_arena_karesinde_izgara_TANINIR(self):
        import cv2
        im = cv2.imread(str(ARENA_KARESI))
        self.assertTrue(arena_izgarasi_var_mi(im),
                        "elimizdeki TEK gercek arena karesinde izgara taninmadi")


class YerellestirmeCALISMIYOR_Tests(unittest.TestCase):
    """🔴 T88'in ASIL sorusu: sinir NEREDE? Cevap OLCULDU ve YETERSIZ."""

    @unittest.skipUnless(ARENA_KARESI.is_file(), "gercek arena karesi diskte yok")
    def test_olculen_aciklik_gercek_sinirdan_KUCUK(self):
        """535 px olculuyor, izgaranin gercek uzanimi ~840 px (D-138).

        Hata YONU emniyetsizdir: `r_gerekli_px` oldugundan KUCUK cikar, yani
        gecilemeyecek koridor gecilebilir sayilir. Bu test sayiyi KILITLER;
        biri dedektoru duzeltirse burasi kirmizi yanar ve KAYIT guncellenir.
        """
        import cv2
        aciklik = arena_izgara_acikligi_px(cv2.imread(str(ARENA_KARESI)))
        self.assertIsNotNone(aciklik)
        self.assertLess(aciklik, 700.0,
                        "aciklik beklenenden BUYUK — D-138 olcumu degismis "
                        "olabilir, kayit guncellenmeli")

    def test_dedektor_URETIM_OLCEK_YOLUNA_BAGLI_DEGIL(self):
        """Baglanti YOK; olursa bu kapi once REVIEW_LOG D-138'i okutur."""
        kaynak = inspect.getsource(rpi_inference.kare_olcek_kahini)
        for ad in ("arena_izgara_acikligi_px", "arena_izgarasi_var_mi",
                   "arena_izgara_parcalari"):
            with self.subTest(fonksiyon=ad):
                self.assertNotIn(
                    ad, kaynak,
                    "arena izgara dedektoru uretim olcek yoluna baglanmis; "
                    "olculen aciklik gercek sinirdan KUCUK ve hata EMNIYETSIZ "
                    "yonde (D-138). Baglamadan once o kaydi okuyun.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
