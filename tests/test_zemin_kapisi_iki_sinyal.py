"""T52 DENETIM KAPISI: zemin maskesi kapisi IKI SINYALLI hale geldi mi?

Kusur (mimarin kendi itirafi, denetim gorevi): `tests/test_zemin_kaplama_kapisi.py`
kapinin TEK sinyalli halini kilitliyordu. T52 kapiyi

    kaplama > ZEMIN_KAPLAMA_TAVANI  VE  kenar_dayanma > ZEMIN_KENAR_DAYANMA_TAVANI

haline getirdi; yeni davranisi hicbir test kapsamiyordu. Bu paket o bosluğu
kapatir ve DORT durumu ayri ayri kilitler:

    kaplama YUKSEK + kenar DUSUK  -> ATESLEMEZ   (T52'nin getirdigi YENI davranis)
    kaplama YUKSEK + kenar YUKSEK -> ATESLER
    kaplama DUSUK  + kenar DUSUK  -> ATESLEMEZ
    kaplama DUSUK  + kenar YUKSEK -> ATESLEMEZ   (kaplama sarti KORUNUYOR)

Esikler SOZLESMEDEN okunur (madde 16): bir sonraki kalibrasyonda test
kendiliginden takip eder, ciplak sayi tasimaz.

⚠ Bu paket kapinin AYIRT ETME MANTIGINI kilitler, esigin DEGERINI degil.
Esigin kalibrasyonu D-69 denetiminde olculdu, D-71 ile 0,50 yapildi.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import karar_sozlesmesi as ks
from karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI, ZEMIN_KENAR_DAYANMA_TAVANI,
                              ZEMIN_MASKESI_SUPHELI_SEBEBI, zemin_kaplamasi,
                              zemin_kenar_dayanmasi, zemin_maskesi_reddi)

H = W = 400


# ── Kontrollu maskeler ───────────────────────────────────────────────────────

def _ortada_blok(oran):
    """Kaplama ~`oran`, cevreye HIC degmeyen merkezi blok -> kenar = 0."""
    m = np.zeros((H, W), np.uint8)
    kenar_px = int(round((1.0 - np.sqrt(oran)) / 2.0 * H))
    kenar_px = max(1, kenar_px)          # cerceveye degmesin
    m[kenar_px:H - kenar_px, kenar_px:W - kenar_px] = 1
    return m


def _tam_dolu():
    """Kaplama 1.0, kenar 1.0."""
    return np.ones((H, W), np.uint8)


def _ince_cerceve(kalinlik=2):
    """Kaplama DUSUK ama kenar 1.0 — kaplama sartinin korundugunu sinar."""
    m = np.zeros((H, W), np.uint8)
    m[:kalinlik, :] = 1
    m[-kalinlik:, :] = 1
    m[:, :kalinlik] = 1
    m[:, -kalinlik:] = 1
    return m


class KontrolluMaskeTests(unittest.TestCase):
    """Once fikstürlerin GERCEKTEN istenen sinyali urettigini dogrula."""

    def test_ortada_blok_yuksek_kaplama_sifir_kenar(self):
        m = _ortada_blok(0.80)
        self.assertGreater(zemin_kaplamasi(m), ZEMIN_KAPLAMA_TAVANI)
        self.assertEqual(0.0, zemin_kenar_dayanmasi(m))

    def test_tam_dolu_her_iki_sinyal_yuksek(self):
        m = _tam_dolu()
        self.assertGreater(zemin_kaplamasi(m), ZEMIN_KAPLAMA_TAVANI)
        self.assertGreater(zemin_kenar_dayanmasi(m), ZEMIN_KENAR_DAYANMA_TAVANI)

    def test_ince_cerceve_dusuk_kaplama_yuksek_kenar(self):
        m = _ince_cerceve()
        self.assertLessEqual(zemin_kaplamasi(m), ZEMIN_KAPLAMA_TAVANI)
        self.assertGreater(zemin_kenar_dayanmasi(m), ZEMIN_KENAR_DAYANMA_TAVANI)


class IkiSinyalKapisiTests(unittest.TestCase):
    """Dort birlesim: kapi YALNIZ ikisi birden asilinca atesler."""

    def test_kaplama_YUKSEK_kenar_DUSUK_ATESLEMEZ(self):
        """T52'nin getirdigi YENI davranis — mesru genis arena elenmez."""
        for oran in (0.60, 0.70, 0.85):
            with self.subTest(kaplama=oran):
                m = _ortada_blok(oran)
                self.assertGreater(zemin_kaplamasi(m), ZEMIN_KAPLAMA_TAVANI,
                                   "fikstür kaplama tavanini asmiyor")
                self.assertIsNone(
                    zemin_maskesi_reddi(m),
                    "kenar dayanmasi DUSUKken kapi atesledi — T52 geri gitmis")

    def test_kaplama_YUKSEK_kenar_YUKSEK_ATESLER(self):
        ret = zemin_maskesi_reddi(_tam_dolu())
        self.assertIsNotNone(ret, "iki sinyal de yuksekken kapi SUSTU")
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, ret[0])

    def test_kaplama_DUSUK_kenar_YUKSEK_ATESLEMEZ(self):
        self.assertIsNone(zemin_maskesi_reddi(_ince_cerceve()))

    def test_kaplama_DUSUK_kenar_DUSUK_ATESLEMEZ(self):
        self.assertIsNone(zemin_maskesi_reddi(_ortada_blok(0.10)))

    def test_TEK_sinyal_degisimi_karari_cevirir(self):
        """AND semantigi: yalniz kenari degistirmek sonucu degistirmeli."""
        dusuk = _ortada_blok(0.80)                 # kenar 0
        yuksek = dusuk.copy()
        yuksek[0, :] = 1                            # ust kenara tam dayan
        yuksek[-1, :] = 1
        yuksek[:, 0] = 1
        yuksek[:, -1] = 1
        self.assertIsNone(zemin_maskesi_reddi(dusuk))
        self.assertIsNotNone(zemin_maskesi_reddi(yuksek))


class SinirDavranisiTests(unittest.TestCase):
    """Esigin KENDISI gecerlidir; yalniz USTU reddedilir (`>` semantigi)."""

    def test_kenar_esigin_KENDISINDE_atesleMEZ(self):
        m = _tam_dolu()
        with mock.patch.object(ks, "ZEMIN_KENAR_DAYANMA_TAVANI",
                               zemin_kenar_dayanmasi(m)):
            self.assertIsNone(zemin_maskesi_reddi(m))

    def test_kaplama_esigin_KENDISINDE_atesleMEZ(self):
        m = _tam_dolu()
        with mock.patch.object(ks, "ZEMIN_KAPLAMA_TAVANI", zemin_kaplamasi(m)):
            self.assertIsNone(zemin_maskesi_reddi(m))

    def test_detay_IKI_olcumu_de_tasir(self):
        ret = zemin_maskesi_reddi(_tam_dolu())
        self.assertIsNotNone(ret)
        self.assertIn(f"%{100 * ZEMIN_KAPLAMA_TAVANI:.1f}", ret[1])
        self.assertIn(f"%{100 * ZEMIN_KENAR_DAYANMA_TAVANI:.1f}", ret[1])


class PozitifKontrolTests(unittest.TestCase):
    """Kapi devre disi birakilinca bu paket DUSMELI (D-15 vakum korumasi)."""

    def test_kapi_devre_disi_birakilinca_ATESLEYEN_durum_kaybolur(self):
        m = _tam_dolu()
        self.assertIsNotNone(zemin_maskesi_reddi(m), "on kosul: kapi atesliyor")
        # Kapiyi etkisizlestir: kenar tavanini erisilemez yap.
        with mock.patch.object(ks, "ZEMIN_KENAR_DAYANMA_TAVANI", 1.01):
            self.assertIsNone(
                zemin_maskesi_reddi(m),
                "kenar tavani devre disi birakildigi halde kapi hala atesliyor "
                "— testin ATESLER durumu kapiyi GERCEKTEN olcmuyor")
        with mock.patch.object(ks, "ZEMIN_KAPLAMA_TAVANI", 1.01):
            self.assertIsNone(
                zemin_maskesi_reddi(m),
                "kaplama tavani devre disi birakildigi halde kapi atesliyor")

    def test_iki_sinyal_gercekten_AND_ile_baglanmis(self):
        """OR olsaydi 'kaplama yuksek + kenar dusuk' ATESLERDI."""
        m = _ortada_blok(0.80)
        self.assertGreater(zemin_kaplamasi(m), ZEMIN_KAPLAMA_TAVANI)
        self.assertLessEqual(zemin_kenar_dayanmasi(m),
                             ZEMIN_KENAR_DAYANMA_TAVANI)
        self.assertIsNone(zemin_maskesi_reddi(m),
                          "kapi OR gibi davraniyor — AND olmali")


class IcerikKutusuTests(unittest.TestCase):
    """Kenar olcumu ICERIK kutusuna gore mi yapiliyor?"""

    def test_kenar_icerik_kutusundan_olculur(self):
        m = np.zeros((H, W), np.uint8)
        m[:, :W // 2] = 1
        self.assertAlmostEqual(1.0, zemin_kenar_dayanmasi(m, (0, 0, W // 2, H)),
                               places=6)
        self.assertAlmostEqual(0.0, zemin_kenar_dayanmasi(m, (W // 2, 0, W // 2, H)),
                               places=6)

    def test_tasan_icerik_kirpilir(self):
        m = _tam_dolu()
        self.assertAlmostEqual(1.0, zemin_kenar_dayanmasi(m, (0, 0, 10_000, H)),
                               places=6)

    def test_gecersiz_icerikte_FAIL_CLOSED(self):
        """D-71: bozuk/tasan/kesirli/bool icerikte kapi SUSMAZ, REDDEDER.

        Sebep `ALAN_YETERSIZ`: `analyze_path:606` ayni kosulu (gecersiz/bos
        icerik kutusu) zaten bu kodla reddediyor; ikinci bir sebep kodu
        turetmek yerine uretimin kanonik cevabi korunur.
        """
        m = _tam_dolu()
        self.assertIsNotNone(zemin_maskesi_reddi(m), "on kosul")
        bozuklar = [
            (0, 0, 0, H),            # sifir genislik
            (0, 0, W, 0),            # sifir yukseklik
            (0, 0, 10_000, H),       # tasan genislik
            (W + 50, 0, 100, H),     # kutu maskenin disinda
            (-5, 0, 100, H),         # negatif x0
            (0, 0, 100.5, H),        # KESIRLI
            (0, 0, True, H),         # BOOL
            (0, 0, 100),             # eksik oge
            (0, 0, None, H),         # sayisal olmayan
            (0, 0, float("nan"), H),
            (0, 0, float("inf"), H),
        ]
        for bozuk in bozuklar:
            with self.subTest(icerik=bozuk):
                ret = zemin_maskesi_reddi(m, bozuk)
                self.assertIsNotNone(
                    ret, f"gecersiz icerik {bozuk!r} ile kapi SUSTU (fail-open)")
                self.assertEqual(ks.ALAN_YETERSIZ_SEBEBI, ret[0])

    def test_gecerli_kesirsiz_tam_sayi_icerik_KABUL_edilir(self):
        """Regresyon: gecerli kutu (int ve tam-degerli float) reddedilmemeli."""
        m = _ortada_blok(0.10)      # kaplama dusuk -> kapi susmali
        for iyi in ((0, 0, W, H), (0.0, 0.0, float(W), float(H)),
                    (10, 10, W - 20, H - 20)):
            with self.subTest(icerik=iyi):
                self.assertIsNone(zemin_maskesi_reddi(m, iyi))

    def test_iki_boyutlu_olmayan_maske_FAIL_CLOSED(self):
        for kotu in (np.ones((5,), np.uint8), np.ones((4, 4, 3), np.uint8)):
            with self.subTest(sekil=kotu.shape):
                ret = zemin_maskesi_reddi(kotu)
                self.assertIsNotNone(ret)
                self.assertEqual(ks.ALAN_YETERSIZ_SEBEBI, ret[0])

    def test_MUTASYON_fail_closed_kaldirilirsa_test_DUSER(self):
        """Fail-closed dali icin POZITIF KONTROL (D-15 vakum korumasi)."""
        m = _tam_dolu()
        with mock.patch.object(ks, "icerik_kutusu_gecerli_mi",
                               return_value=True):
            # Dogrulama devre disi -> bozuk kutu yine 0,0 olculur ve kapi susar
            self.assertIsNone(
                zemin_maskesi_reddi(m, (0, 0, 0, H)),
                "dogrulama devre disi birakildigi halde kapi hala reddediyor "
                "— fail-closed testi kapiyi GERCEKTEN olcmuyor")


class KoseSayimiTests(unittest.TestCase):
    """D-71: kose pikselleri BIR KEZ sayilir (onceden 2x agirlikliydi)."""

    def test_kose_ve_kenar_pikseli_ESIT_agirlikli(self):
        kose = np.zeros((H, W), np.uint8)
        kose[0, 0] = 1
        kenar = np.zeros((H, W), np.uint8)
        kenar[0, W // 2] = 1
        self.assertAlmostEqual(zemin_kenar_dayanmasi(kose),
                               zemin_kenar_dayanmasi(kenar), places=9)

    def test_cevre_paydasi_dogru(self):
        kose = np.zeros((H, W), np.uint8)
        kose[0, 0] = 1
        self.assertAlmostEqual(1.0 / (2 * W + 2 * H - 4),
                               zemin_kenar_dayanmasi(kose), places=9)

    def test_dejenere_kutularda_tanimli(self):
        for sekil in ((1, 50), (50, 1), (1, 1)):
            with self.subTest(sekil=sekil):
                self.assertAlmostEqual(
                    1.0, zemin_kenar_dayanmasi(np.ones(sekil, np.uint8)),
                    places=9)


if __name__ == "__main__":
    unittest.main(verbosity=2)