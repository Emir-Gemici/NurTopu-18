"""T134 KAPISI: `rota_bul` da zemin maskesi saglamlik kapisini UYGULAR.

NEDEN (olcum D-267 §2, mimar). Kapi IKI rota ureticisinden yalnizca
`analyze_path`te vardi (`rpi_inference.py:1166`); `costmap_path_finder` ve
`simulation/scripts/iha_haritala` gecis sayisi **0** idi. Yani `iha_haritala`
yolunda kapi HICBIR KATMANDA yoktu — ve kapisiz olan yol IKA'ya YAYINLANAN
`rota.json`u ureten yoldu (:324 rota_bul -> :365 yazar). Olculen davranis:
cokmus zemin maskesinde (kaplama %96,5 · tavan %67) `durum=ACIK · guven=1,0 ·
22 waypoint`. Sinif: "iki kopya, biri zorlanmiyor" — DOKUZUNCU ornek.

🔴 BU DOSYA ESIK SINAMAZ. `ZEMIN_KAPLAMA_TAVANI` (0,67) ve
`ZEMIN_KENAR_DAYANMA_TAVANI` (0,50) yalnizca OKUNUR; hicbir test onlarin
DEGERINI dogrulamaz, cunku esik degeri bu gorevin konusu DEGILDIR (T134:
"bu bir YER isidir"). Sinanan sey kapinin YERI ve OLCTUGU SEYdir.

SINANAN DORT SEY:
  a) Cokmus maskede `rota_bul` rota URETMEZ (kapi calisiyor).
  b) POZITIF KONTROL: saglam sahnede rota HALA uretilir (kapi her seyi
     reddetmiyor) — sahne genel kapinin KENDI ureticisinden gelir.
  c) Olcum HAM maskede yapilir, `serbest_alan` CIKTISINDA degil. Bu, yanlis
     yerlesimin kapiyi SESSIZLESTIRDIGI olculmus durumdur.
  d) Gecersiz icerik kutusunda yayinlanan sebep kodu DEGISMEZ (`MASKE_YOK`).
"""

import unittest

import numpy as np

from codes.costmap_path_finder import rota_bul, serbest_alan
from codes.karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI,
                                    ZEMIN_MASKESI_SUPHELI_SEBEBI,
                                    zemin_kaplamasi)


def _cokmus_sahne(h=240, w=320):
    """Model her seyi zemin sanmis: kaplama 1,0 — cati/cim/toprak dahil."""
    return {0: np.ones((h, w), np.uint8), 1: np.zeros((h, w), np.uint8)}


class KapiCokmusMaskedeReddederTests(unittest.TestCase):
    """(a) Kapi calisiyor mu."""

    def test_cokmus_maskede_rota_URETILMEZ(self):
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=True)
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, sonuc["durum"])
        self.assertEqual([], sonuc["waypoints_px"])
        self.assertIsNone(sonuc["yol_no"])
        self.assertEqual(0.0, sonuc["guven"])

    def test_sebep_METNI_yazili_sessiz_ret_YOK(self):
        """Ret sebebi bos birakilirsa hakem neden rota olmadigini goremez."""
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=True)
        self.assertTrue(str(sonuc["sebep"]).strip())
        self.assertIn("%", str(sonuc["sebep"]))

    def test_plan_False_yolunda_da_reddeder(self):
        """`plan=False` (jetson_fps, kamera_dogrula) kapiyi ATLAMAMALI."""
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=False)
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, sonuc["durum"])

    def test_icerik_kutusu_VERILDIGINDE_de_reddeder(self):
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=True,
                         icerik=(0, 0, 320, 240))
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, sonuc["durum"])


class PozitifKontrolTests(unittest.TestCase):
    """(b) 🔴 Kapi HER SEYI reddetmiyor — saglam sahnede rota HALA cikiyor.

    Sahne genel kapinin (`codes/test_rota_sentetik.py`, 15/15) KENDI
    ureticisinden gelir; buraya kopyalanmaz. Kopya sahne, sahnenin degismesi
    halinde bu testi sessizce ALAKASIZ kilardi.
    """

    @classmethod
    def setUpClass(cls):
        import sys
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent
        for ek in (kok / "codes", kok / "simulation" / "scripts"):
            if str(ek) not in sys.path:
                sys.path.insert(0, str(ek))
        import test_rota_sentetik as T
        cls.T = T
        cls.H, cls.zemin, cls.engel, cls.bas, cls.hed = T.sahne_uret(1, "kolay")

    def test_saglam_sahnede_rota_URETILIYOR(self):
        sonuc = rota_bul({0: self.zemin, 1: self.engel}, mpp=self.T.MPP,
                         baslangic=self.bas, hedef=self.hed, plan=True)
        self.assertNotEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, sonuc["durum"])
        self.assertTrue(sonuc["waypoints_px"],
                        "saglam sahnede waypoint URETILMEDI — kapi her seyi "
                        "reddediyor olabilir")

    def test_saglam_sahnenin_kaplamasi_TAVANIN_ALTINDA(self):
        """Pozitif kontrolun BOS olmadigini sabitler: sahne gercekten mesru."""
        kaplama = zemin_kaplamasi(self.zemin > 0, None)
        self.assertLess(kaplama, ZEMIN_KAPLAMA_TAVANI)


class OlcumHamMaskedeTests(unittest.TestCase):
    """(c) 🔴 YANLIS YERLESIM KAPIYI SUSTURUR — olculmus durum.

    `serbest_alan` cikitisi olculseydi: tam cokmus maske HAM 1,0000 iken
    serbest alan tavanin ALTINA duser ve kapi SUSARDI. Bu test o farkin
    GERCEKTEN var oldugunu ve kapinin HAM tarafta durdugunu kilitler.
    """

    @staticmethod
    def _ayirt_eden_sahne(h=240, w=320):
        """HAM kaplama 1,0000 · SERBEST kaplama 0,4969 (olculdu).

        Zemin tamamen dolu (model her seyi zemin sanmis) ama engel sol yarim
        tuvali kapliyor. Kapi HAM tarafta ise REDDEDER; `serbest_alan`
        ciktisinda olcseydi 0,4969 < 0,67 oldugu icin SUSARDI.
        ⚠ Fikstur DEGISIRSE ilk test bunu yakalar (ayirt ediciligi sinar).
        """
        zemin = np.ones((h, w), np.uint8)
        engel = np.zeros((h, w), np.uint8)
        engel[:, : w // 2] = 1
        return {0: zemin, 1: engel}

    def test_fikstur_GERCEKTEN_ayirt_ediyor(self):
        """Once ayirt ediciligi sabitle — yoksa asagidaki test BOS yesildir."""
        maskeler = self._ayirt_eden_sahne()
        ham = zemin_kaplamasi(maskeler[0] > 0, None)
        serbest = zemin_kaplamasi(
            serbest_alan(maskeler, mpp=None)["serbest"] > 0, None)
        self.assertGreater(ham, ZEMIN_KAPLAMA_TAVANI)
        self.assertLess(serbest, ZEMIN_KAPLAMA_TAVANI,
                        "serbest alan tavanin ustunde kaldi — bu fikstur artik "
                        "yanlis yerlesimi AYIRT ETMIYOR")

    def test_kapi_YINE_DE_reddediyor_yani_HAM_tarafta(self):
        sonuc = rota_bul(self._ayirt_eden_sahne(), mpp=None, plan=True)
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, sonuc["durum"],
                         "kapi serbest_alan ciktisini olcuyor olabilir — "
                         "bu yerlesim cokmus maskede SUSARDI")


class GecersizKutuSozlesmesiTests(unittest.TestCase):
    """(d) Gecersiz kutuda YAYINLANAN sebep kodu DEGISMEDI.

    `zemin_maskesi_reddi` gecersiz kutuda `ALAN_YETERSIZ` doner (D-71,
    fail-closed). `rota_bul`un yayinlanan cevabi ise `MASKE_YOK`tur. Bos ROI
    zaten rota URETMEZ; kapiyi orada kosturmak guvenlik EKLEMEZ, yalnizca
    sozlesmeyi kaydirirdi. Bu test o kaymayi YASAKLAR.
    """

    def test_tasan_kutu_MASKE_YOK_kalir(self):
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=False,
                         icerik=(0, 0, 400, 240))
        self.assertEqual("MASKE_YOK", sonuc["durum"])

    def test_nesne_olmayan_kutu_MASKE_YOK_kalir(self):
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=False,
                         icerik=object())
        self.assertEqual("MASKE_YOK", sonuc["durum"])

    def test_bos_genislikli_kutu_MASKE_YOK_kalir(self):
        sonuc = rota_bul(_cokmus_sahne(), mpp=None, plan=False,
                         icerik=(0, 0, 0, 240))
        self.assertEqual("MASKE_YOK", sonuc["durum"])


class IkiKopyaAyniKapiyiTasirTests(unittest.TestCase):
    """T134'un kendi sinifi: "iki kopya, biri zorlanmiyor" TEKRARLAMASIN."""

    def test_jetson_paket_kopyasi_da_kapiyi_TASIR(self):
        from pathlib import Path
        kok = Path(__file__).resolve().parent.parent
        depo = (kok / "codes" / "costmap_path_finder.py").read_text(encoding="utf-8")
        paket = (kok / "jetson_paket" / "kod" / "costmap_path_finder.py").read_text(encoding="utf-8")
        for metin, ad in ((depo, "codes"), (paket, "jetson_paket/kod")):
            self.assertIn("zemin_maskesi_reddi", metin,
                          f"{ad} kopyasinda kapi YOK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
