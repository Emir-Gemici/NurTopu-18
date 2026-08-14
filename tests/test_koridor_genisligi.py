"""T65 KAPISI: bir seritten genis "koridor" guzergah sayilmamali.

Kusur (REVIEW_LOG D-90 bulgu 3): karar yolunun ARENA SINIRI kavrami yok.
Uretec arena disina bilerek etiketsiz duz zemin cizer, model orayi hakli olarak
zemin isaretler, karar yolu tum kareyi ucte bolup o bos kenari gecerli guzergah
sayar. `sa_000070`: darbogaz 304 px — 640'lik karede neredeyse bos sahne.
AYNI KUSUR GERCEK KAREDE DE VAR.

Sinir YERELLESTIRILEMEDI (D-94): uc aday imza da guvenilmez cikti ve ucu de
gercek karede coktu; ustelik gercek arena siniri PERSPEKTIF YAMUK, tek [x0,x1]
araligi onu tanimlamiyor. Bu paket bu yuzden siniri DEGIL, koridorun kendisini
sinar: bir seridin tamamindan genis bir aciklik guzergah degil ACIK ARAZIDIR.

Paket dort seyi kanitlar:
  1. Tavan `serit_no`nun bolusumuyle AYNI kaynaktan gelir (madde 16) — ikisi
     birbirinden bagimsiz kayamaz.
  2. Tavanin USTUNDE reddeder, ALTINDA ve TAM USTUNDE etmez.
  3. Fail-closed davranis: olculemeyen girdi reddi TETIKLEMEZ (bu olcut yalniz
     pozitif kanit uzerine ates eder).
  4. Olculen dagilimla tutarli: mesru azami tavanin ALTINDA, yakalanan kusurlu
     kareler USTUNDE.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import numpy as np  # noqa: E402

from karar_sozlesmesi import (KORIDOR_DEGIL_SEBEBI,  # noqa: E402
                              ZEMIN_MASKESI_SUPHELI_SEBEBI,
                              KORIDOR_GENISLIK_TAVANI_SERIT,
                              ROTA_RET_SEBEPLERI, SERIT_SAYISI,
                              koridor_genislik_tavani_px,
                              rota_koridor_genisligi_reddi, serit_no)
from rpi_inference import analyze_path  # noqa: E402

ICERIK_W = 640

# T65 · v24 · T60 kadraj · n=260 · uretim zinciri (bkz. REVIEW_LOG D-94).
# darbogaz / icerik_w oranlari:
MESRU_AZAMI_ORAN = 0.280            # 239 arena-ici rotanin en genisi
KUSURLU_ORANLAR = (0.022, 0.028, 0.111, 0.170, 0.314,
                   0.353, 0.358, 0.375, 0.475, 0.487)


class SozlesmeKaynagiTests(unittest.TestCase):
    """Madde 16: tavan `serit_no` ile AYNI bolusumden gelmeli."""

    def test_sebep_kodu_kanonik_kumede(self):
        self.assertIn(KORIDOR_DEGIL_SEBEBI, ROTA_RET_SEBEPLERI)

    def test_serit_sayisi_serit_no_ile_TUTARLI(self):
        """`serit_no` gercekten SERIT_SAYISI kadar serit uretiyor mu?"""
        gorulen = {serit_no(x, 0, ICERIK_W) for x in range(ICERIK_W)}
        self.assertEqual(set(range(1, SERIT_SAYISI + 1)), gorulen,
                         "serit_no ile SERIT_SAYISI ayrismis — tavan yanlis "
                         "bolusumden turetilir")

    def test_serit_SINIRLARI_bolusumle_ayni_yerde(self):
        """Serit gecisleri tam olarak icerik_w/SERIT_SAYISI katlarinda mi?

        Genislik SERIT_SAYISI'na TAM bolunen bir deger secilir; aksi halde
        sinir kesirli olur ve tamsayi piksel testi bolusumu degil YUVARLAMAYI
        olcer (ilk yazimda bu hata yapildi: 640/3 = 213,33).
        """
        genislik = 600
        self.assertEqual(0, genislik % SERIT_SAYISI)
        for k in range(1, SERIT_SAYISI):
            sinir = k * genislik // SERIT_SAYISI
            with self.subTest(sinir=sinir):
                self.assertEqual(k, serit_no(sinir - 1, 0, genislik))
                self.assertEqual(k + 1, serit_no(sinir, 0, genislik))

    def test_tavan_BIR_SERIT_genisligi(self):
        self.assertAlmostEqual(ICERIK_W / float(SERIT_SAYISI),
                               koridor_genislik_tavani_px(ICERIK_W), places=6)
        self.assertEqual(1.0, KORIDOR_GENISLIK_TAVANI_SERIT,
                         "tavan fiziksel sinirdir (bir serit); fit edilmis "
                         "bir sayi degildir")


class EsikDavranisiTests(unittest.TestCase):
    """Tavanin altinda/uzerinde/tam uzerinde ne oluyor."""

    def setUp(self):
        self.tavan = koridor_genislik_tavani_px(ICERIK_W)

    def test_tavanin_ALTINDA_reddetmez(self):
        for pay in (0.01, 0.5, 0.9, 0.99):
            with self.subTest(pay=pay):
                self.assertIsNone(rota_koridor_genisligi_reddi(
                    self.tavan * pay, ICERIK_W))

    def test_tavanin_KENDISI_gecerlidir(self):
        """Sinirin kendisi reddedilmez; yalniz USTU reddedilir."""
        self.assertIsNone(rota_koridor_genisligi_reddi(self.tavan, ICERIK_W))

    def test_tavanin_USTUNDE_reddeder(self):
        for carpan in (1.01, 1.2, 1.5):
            with self.subTest(carpan=carpan):
                ret = rota_koridor_genisligi_reddi(
                    self.tavan * carpan, ICERIK_W)
                self.assertIsNotNone(ret)
                self.assertEqual(KORIDOR_DEGIL_SEBEBI, ret[0])

    def test_detay_OLCULEN_degeri_tasir(self):
        ret = rota_koridor_genisligi_reddi(304.0, ICERIK_W)
        self.assertIsNotNone(ret)
        self.assertIn("304.0", ret[1])
        self.assertIn(f"{self.tavan:.1f}", ret[1])

    def test_ICERIK_genisligine_gore_olceklenir(self):
        """Tavan mutlak piksel degil, icerik kutusunun oranidir."""
        dar = rota_koridor_genisligi_reddi(120.0, 300)     # tavan 100 -> RET
        genis = rota_koridor_genisligi_reddi(120.0, 1200)  # tavan 400 -> gecer
        self.assertIsNotNone(dar)
        self.assertIsNone(genis)


class FailClosedTests(unittest.TestCase):
    """Olculemeyen girdi bu olcutu TETIKLEMEZ — yalniz pozitif kanit ates eder."""

    def test_bozuk_darbogaz_reddi_tetiklemez(self):
        for kotu in (None, "genis", float("nan")):
            with self.subTest(darbogaz=kotu):
                self.assertIsNone(
                    rota_koridor_genisligi_reddi(kotu, ICERIK_W))

    def test_bozuk_icerik_genisligi_reddi_tetiklemez(self):
        for kotu in (0, -5, None, "genis", float("nan")):
            with self.subTest(icerik_w=kotu):
                self.assertIsNone(rota_koridor_genisligi_reddi(1e9, kotu))

    def test_SAYISAL_metin_bozuk_SAYILMAZ(self):
        """"640" bozuk girdi degildir; cozulur ve olcut normal calisir."""
        self.assertIsNotNone(rota_koridor_genisligi_reddi(1e9, "640"))
        self.assertAlmostEqual(koridor_genislik_tavani_px("640"),
                               koridor_genislik_tavani_px(640), places=6)

    def test_tavan_bozuk_girdide_SIFIR(self):
        for kotu in (0, -1, None, "x"):
            with self.subTest(icerik_w=kotu):
                self.assertEqual(0.0, koridor_genislik_tavani_px(kotu))


class OlculenDagilimTests(unittest.TestCase):
    """Tavan D-94'de olculen dagilimla tutarli mi?"""

    def test_MESRU_azami_tavanin_ALTINDA(self):
        """239 arena-ici rotanin en genisi bile tavani asmamali."""
        self.assertIsNone(
            rota_koridor_genisligi_reddi(MESRU_AZAMI_ORAN * ICERIK_W, ICERIK_W),
            "olculen en genis MESRU koridor reddedilir — tavan cok dusuk")

    def test_KUSURLU_karelerin_yarisi_YAKALANIR(self):
        """Kismi cozum: genislige gore ayrilabilen 5 kare yakalanmali."""
        yakalanan = sum(
            1 for o in KUSURLU_ORANLAR
            if rota_koridor_genisligi_reddi(o * ICERIK_W, ICERIK_W) is not None)
        self.assertEqual(
            5, yakalanan,
            "olculen kusurlu dagilimda yakalanan kare sayisi degisti — "
            "tavan ya da olcum bayat")

    def test_KISMI_cozum_oldugu_KAYITLI(self):
        """Kalan kareler ve NEDEN kacтiklari kayitli olmali — gizlenmesin.

        DORT kacan kare mesru azaminin (0,280) ALTINDA: genislikle ayirt
        EDILEMEZLER, hicbir tavan onlari mesru karelerden ayiramaz.
        BIR kacan kare (0,314) mesru azaminin USTUNDE: (0,280 · 0,314)
        araligina konacak FIT EDILMIS bir tavan onu da yakalardi.
        Bilerek yakalamiyoruz — gerekce `test_neden_FIT_EDILMIS_tavan_secilmedi`.
        """
        kacan = sorted(o for o in KUSURLU_ORANLAR
                       if rota_koridor_genisligi_reddi(
                           o * ICERIK_W, ICERIK_W) is None)
        self.assertEqual(5, len(kacan))
        ayirt_edilemez = [o for o in kacan if o <= MESRU_AZAMI_ORAN]
        fit_ile_yakalanabilir = [o for o in kacan if o > MESRU_AZAMI_ORAN]
        self.assertEqual(4, len(ayirt_edilemez))
        self.assertEqual([0.314], fit_ile_yakalanabilir)

    def test_neden_FIT_EDILMIS_tavan_secilmedi(self):
        """(0,280 · 0,333) araliginda bir tavan 6/10 yakalardi. Neden hayir?

        1. Fiziksel degil FIT EDILMIS olurdu: mesru azamisi 0,280'e dayanir.
        2. O 0,280 SENTETIK 239 kareden gelir ve uretec kadraj kipinde
           geometrik + fotometrik bozunumu KAPATIR (egim/golge/bulaniklik/JPEG
           yok). Gercek mesru dagilim bundan GENISTIR; optimist bir azamiye
           esik oturtmak D-85'in hatasidir (alt kumede tam ayrik gorunen esik
           kumenin tamaminda ayirmadi).
        3. Payi ince olurdu: 0,297'de +-0,017; bir seritlik tavanda mesru
           tarafa 0,053.
        Bu test kararin GEREKCESINI kilitler; sayilari degistiren biri bunu
        okumak zorunda kalir.
        """
        tavan_orani = koridor_genislik_tavani_px(ICERIK_W) / ICERIK_W
        self.assertGreater(tavan_orani - MESRU_AZAMI_ORAN, 0.05,
                           "mesru tarafta pay 0,05'in altina dustu — fit "
                           "edilmis esikten farki kalmadi")

    def test_tavan_MESRU_azami_ile_KUSURLU_arasinda(self):
        """Tavanin iki tarafinda da olculmus pay olmali (D-86 dersi)."""
        tavan_orani = koridor_genislik_tavani_px(ICERIK_W) / ICERIK_W
        ustteki = min(o for o in KUSURLU_ORANLAR if o > tavan_orani)
        self.assertGreater(tavan_orani, MESRU_AZAMI_ORAN,
                           "mesru tarafta pay YOK")
        self.assertGreater(ustteki, tavan_orani,
                           "kusurlu tarafta pay YOK")


class AnalyzePathEntegrasyonTests(unittest.TestCase):
    """T69: olcut SOZLESMEDE degil, KARAR YOLUNDA da yururlukte mi?

    T65 sozlesmeyi teslim etti ama kisiti BAGLAYAMADI (izin listesinde
    `rpi_inference.py` yoktu — D-96, mimarin kapsam hatasi). T69 tek cagriyi
    ekledi. Bu sinif o BAGLANTIYI kilitler: cagri silinirse buradan duser.
    """

    @staticmethod
    def _bant(yan, oran):
        """Ortada `oran` genisliginde dikey bant.

        Kaplama kapisina (T48/T59) TAKILMAZ: bant sol/sag kenara degmedigi
        icin kenar-dayanma dusuk kalir ve o kapi bir AND birlesimidir.
        Darbogaz yaricapi ~ (oran*yan)/2 olur.
        """
        m = np.zeros((yan, yan), np.uint8)
        gen = int(round(yan * oran))
        x0 = (yan - gen) // 2
        m[:, x0:x0 + gen] = 1
        return m

    def test_fikstur_gercekten_istenen_darbogazi_uretiyor(self):
        """Once fiksturun kendisini dogrula (kor kapi kurma)."""
        yan = 300
        genis = self._bant(yan, 0.80)
        _y, _g, _w, ret = analyze_path(genis, return_reason=True,
                                       min_area_ratio=0.001)
        self.assertIsNotNone(ret, "genis bant hic reddedilmedi")
        self.assertNotEqual(
            ZEMIN_MASKESI_SUPHELI_SEBEBI, ret[0],
            "fikstur ZEMIN kapisina takildi; koridor olcutu sinanamiyor")

    def test_ASIRI_GENIS_koridor_KORIDOR_DEGIL_ile_reddedilir(self):
        yan = 300
        _yol, _guven, _wp, ret = analyze_path(
            self._bant(yan, 0.80), return_reason=True, min_area_ratio=0.001)
        self.assertIsNotNone(ret)
        self.assertEqual(KORIDOR_DEGIL_SEBEBI, ret[0])
        self.assertIn("px", ret[1])

    def test_ret_FAIL_CLOSED(self):
        """Reddedilen karede yol, guven ve waypoint YAYINLANMAZ."""
        yol, guven, wps, ret = analyze_path(
            self._bant(300, 0.80), return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps, "reddedilen karede waypoint uretildi")
        self.assertEqual(KORIDOR_DEGIL_SEBEBI, ret[0])

    def test_MAKUL_koridor_ETKILENMEZ(self):
        """Negatif kontrol: tavanin altindaki bant normal rota uretmeli."""
        yol, guven, wps, ret = analyze_path(
            self._bant(300, 0.40), return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(ret, f"makul koridor reddedildi: {ret}")
        self.assertIsNotNone(yol)
        self.assertGreater(guven, 0.0)
        self.assertGreaterEqual(len(wps), 2)

    def test_MADDE_15_kisit_maskeye_DOKUNMAZ(self):
        m = self._bant(300, 0.80)
        kopya = m.copy()
        analyze_path(m, return_reason=True, min_area_ratio=0.001)
        self.assertTrue(np.array_equal(kopya, m),
                        "kisit girdi maskesini DEGISTIRDI")

    def test_kisit_SOZLESMEDEN_cagriliyor(self):
        """Karar yolu kendi kopyasini yazmamali (madde 16)."""
        import karar_sozlesmesi
        import rpi_inference
        self.assertIs(rpi_inference.rota_koridor_genisligi_reddi,
                      karar_sozlesmesi.rota_koridor_genisligi_reddi)

    def test_kisit_KAPATILINCA_rota_URETILIR(self):
        """Mutasyon kilidi: kisit devre disi kalirsa ayni kare gecmeli.

        Boylece yukaridaki reddin KISITTAN geldigi kanitlanir; baska bir
        kapinin yan etkisi olsaydi bu test de reddedilirdi.
        """
        from unittest import mock
        import rpi_inference
        m = self._bant(300, 0.80)
        with mock.patch.object(rpi_inference, "rota_koridor_genisligi_reddi",
                               lambda *a, **k: None):
            yol, _guven, wps, ret = analyze_path(
                m, return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(ret, f"kisit kapaliyken baska kapi reddetti: {ret}")
        self.assertIsNotNone(yol)
        self.assertGreaterEqual(len(wps), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
