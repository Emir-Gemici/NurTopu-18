"""T67 KAPISI: ince BARIYER engel sayilir, HB pedi SAYILMAZ.

Kusur (REVIEW_LOG D-92, gercek arena karesinde MODEL KULLANILMADAN olculdu):

    bariyer pikselleri n = 3644
      model ENGEL diyor : %0,0      <- tek piksel bile degil
      model ZEMIN diyor : %30,9
    ROTA x BARIYER kesisimi: 59 px  -> KESIYOR (gorsel dogrulandi)

Korumalarin hicbiri atesliyordu: zemin kapisi susuyor, karar reddi yok, guven
0,75. Rotayi yayindan alikoyan TEK sey `OLCEK_YOK` idi — bir kapi degil, bir
EKSIKLIK.

MODEL BEKLENMEDI (D-93): uretec bariyeri YALNIZ zaten kapali seritlere koyuyor;
acik zeminde bariyer orani %0,0. Egitim verisi bu ornegi hic icermiyor, model
ogrenemez. Cozum KATMAN 2'de klasik dedektordur.

🔴 BU PAKETIN ASIL ISI TUZAGI KILITLEMEK. Sartname METNI hedefi "2x2 m KIRMIZI
branda" diyor. Naif bir "kirmizi = engel" kurali HB'yi engel yapar, IKA hedefe
HICBIR ZAMAN ulasamaz ve P_gorev = 0 olur. Ayrim RENKLE DEGIL SEKILLE yapilir
ve asagida SENTETIK KIRMIZI HB ile dogrudan sinanir — gercek karede HB
siyah/beyaz oldugu icin yalniz o kareye bakmak ZAYIF kanittir.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import rpi_inference  # noqa: E402
from karar_sozlesmesi import (BARIYER_ASGARI_GENISLIK_ORANI,  # noqa: E402
                              BARIYER_EN_BOY_ORANI,
                              BARIYER_ENGEL_SINIFI, BARIYER_KROMA_ESIGI,
                              ince_bariyer_maskesi)
from rpi_inference import get_masks  # noqa: E402

ARENA = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
KIRMIZI = (28, 26, 205)      # BGR, doymus — sartname METNINDEKI "kirmizi branda"
NOTR = (150, 150, 150)


def _tuval(yan=640):
    return np.full((yan, yan, 3), NOTR, np.uint8)


def _dikdortgen(bw, bh, yan=640, sol_ust=(200, 200), renk=KIRMIZI):
    t = _tuval(yan)
    x, y = sol_ust
    cv2.rectangle(t, (x, y), (x + bw, y + bh), renk, -1)
    return t


class _SahteSonuc:
    """`get_masks` icin en kucuk sonuc nesnesi: model HICBIR SEY gormedi."""

    def __init__(self, goruntu):
        self.masks = None
        self.orig_img = goruntu


class SozlesmeKaynagiTests(unittest.TestCase):

    def test_ENGEL_SINIFI_sema_ile_TUTARLI(self):
        """`sinif_semasi` Jetson paketinde YOK, oradan import EDILEMEZ.

        Bu yuzden deger sozlesmede tekrarlanir; ayrismasin diye burada
        kilitlenir (madde 16).
        """
        from sinif_semasi import ENGEL
        self.assertEqual(ENGEL, BARIYER_ENGEL_SINIFI)

    def test_olcutler_ORAN_olarak_tanimli(self):
        """CONTRACTS SS8: mutlak piksel degil oran — cozunurluk kaydirmasin."""
        self.assertLess(0.0, BARIYER_ASGARI_GENISLIK_ORANI)
        self.assertLess(BARIYER_ASGARI_GENISLIK_ORANI, 1.0)


class HedefKorumaTests(unittest.TestCase):
    """🔴 TUZAK KILIDI: HB pedi hicbir kosulda engel sayilmamali."""

    def test_KIRMIZI_KARE_HB_engel_SAYILMAZ(self):
        """Sartname METNINE sadik en kotu durum: doymus kirmizi 2x2 m branda."""
        for kenar in (32, 64, 96, 128):
            with self.subTest(kenar=kenar):
                t = _dikdortgen(kenar, kenar)
                a = cv2.cvtColor(t, cv2.COLOR_BGR2LAB)[:, :, 1].astype(np.int16) - 128
                self.assertGreater(
                    int(a.max()), BARIYER_KROMA_ESIGI,
                    "fikstur kroma kapisini gecmiyor; koruma sinanmis olmaz")
                self.assertEqual(
                    0, int(ince_bariyer_maskesi(t).sum()),
                    f"{kenar}x{kenar} KIRMIZI HB engel sayildi — IKA hedefe "
                    f"ULASAMAZ, P_gorev = 0")

    def test_AYNI_KAREDE_bariyer_YAKALANIR(self):
        """POZITIF KONTROL (D-15/K-04): 'hicbir sey bulamiyor' basari degildir."""
        t = _dikdortgen(64, 64, sol_ust=(100, 100))
        cv2.rectangle(t, (300, 400), (540, 414), KIRMIZI, -1)
        m = ince_bariyer_maskesi(t)
        self.assertEqual(0, int(m[100:164, 100:164].sum()), "HB oldu")
        self.assertGreater(int(m[400:414, 300:540].sum()), 0,
                           "ayni karede bariyer KACIRILDI — dedektor calismiyor")

    def test_EN_BOY_esigi_ikisinin_ORTASINDA(self):
        """HB en/boy 1,0 (T60'ta n=260 olculdu) · bariyer 7,0 ve 14,2."""
        self.assertGreater(BARIYER_EN_BOY_ORANI, 1.0 * 2.0,
                           "HB tarafinda pay yetersiz")
        self.assertLess(BARIYER_EN_BOY_ORANI, 7.0,
                        "olculen EN KISA bariyer kolunu (en/boy 7,0) elerdi")

    def test_esik_KENDISI_engel_sayilmaz(self):
        """en/boy tam esikte olan yapi ELENIR; yalniz USTU engel olur."""
        bh = 50
        bw = int(BARIYER_EN_BOY_ORANI * bh)
        self.assertEqual(0, int(ince_bariyer_maskesi(
            _dikdortgen(bw, bh)).sum()))
        self.assertGreater(int(ince_bariyer_maskesi(
            _dikdortgen(bw + 6, bh - 1)).sum()), 0)


class GercekArenaTests(unittest.TestCase):
    """Olculen kare (D-92). Kare yoksa ATLANIR — temiz klonda kirmizi yanmaz."""

    @classmethod
    def setUpClass(cls):
        if not ARENA.is_file():
            raise unittest.SkipTest(f"gercek arena karesi yok: {ARENA}")
        cls.img = cv2.imread(str(ARENA))
        if cls.img is None:
            raise unittest.SkipTest("arena karesi okunamadi")
        cls.kol = ince_bariyer_maskesi(cls.img)

    def test_IKI_bariyer_kolu_bulunur(self):
        n, _lbl, st, _c = cv2.connectedComponentsWithStats(self.kol, 8)
        self.assertEqual(2, n - 1, "gercek karede iki bariyer kolu var (D-92)")
        genislikler = sorted(int(st[i][2]) for i in range(1, n))
        self.assertEqual([98, 228], genislikler, "olculen kol genislikleri bayat")

    def test_olculen_piksel_sayisi_KORUNUR(self):
        self.assertEqual(3644, int(self.kol.sum()),
                         "D-92'de olculen bariyer piksel sayisi degisti")

    def test_HB_pedi_engel_SAYILMAZ(self):
        """Gercek karede HB siyah/beyaz; kroma zaten esigin altinda."""
        x, y, w, h = 322, 125, 62, 50
        self.assertEqual(0, int(self.kol[y:y + h, x:x + w].sum()))

    def test_IHA_ve_IKA_engel_SAYILMAZ(self):
        """Sahnedeki diger yapilar (IHA govdesi, IKA) kroma kapisini gecmemeli."""
        for ad, (x, y, w, h) in (("IHA", (480, 100, 110, 60)),
                                 ("IKA", (505, 540, 60, 55))):
            with self.subTest(yapi=ad):
                self.assertEqual(0, int(self.kol[y:y + h, x:x + w].sum()))


class CozunurlukBagimsizligiTests(unittest.TestCase):
    """Olcutler ORAN oldugu icin olcek degisince sonuc kaymamali."""

    def test_ayni_sekil_farkli_olcekte_AYNI_karar(self):
        for yan in (320, 640, 1280):
            with self.subTest(yan=yan):
                kare = int(yan * 0.10)
                self.assertEqual(0, int(ince_bariyer_maskesi(
                    _dikdortgen(kare, kare, yan=yan,
                                sol_ust=(yan // 4, yan // 4))).sum()),
                    "KARE yapi bu olcekte engel sayildi")
                bw = int(yan * 0.35)
                bh = max(2, int(yan * 0.02))
                self.assertGreater(int(ince_bariyer_maskesi(
                    _dikdortgen(bw, bh, yan=yan,
                                sol_ust=(yan // 4, yan // 2))).sum()), 0,
                    "UZUN yapi bu olcekte kacirildi")


class FailSafeTests(unittest.TestCase):
    """Cozulemeyen girdi hicbir sey EKLEMEZ ve hicbir sey CIKARMAZ."""

    def test_bozuk_girdi_None_doner(self):
        for kotu in (None, np.zeros((5, 5), np.uint8), np.zeros((0, 0, 3), np.uint8)):
            with self.subTest(girdi=type(kotu).__name__):
                self.assertIsNone(ince_bariyer_maskesi(kotu))

    def test_kromasiz_sahnede_BOS_maske(self):
        m = ince_bariyer_maskesi(_tuval())
        self.assertIsNotNone(m)
        self.assertEqual(0, int(m.sum()))


class GetMasksEntegrasyonTests(unittest.TestCase):
    """T67 baglantisi: `get_masks` dedektoru GERCEKTEN uyguluyor mu?"""

    def _sonuc(self, goruntu):
        return [_SahteSonuc(goruntu)]

    def test_model_HIC_maske_uretmese_bile_bariyer_ISARETLENIR(self):
        """`r.masks is None` dalinda da calismali — eski kod erken donuyordu."""
        t = _dikdortgen(240, 14, yan=512, sol_ust=(100, 250))
        m = get_masks(self._sonuc(t), 512, 512)
        self.assertGreater(int(m[BARIYER_ENGEL_SINIFI].sum()), 0,
                           "model bos donunce bariyer de kayboldu")
        self.assertEqual(0, int(m[0].sum()), "zemin katmani kirletildi")

    def test_HB_get_masks_yolunda_da_KORUNUR(self):
        t = _dikdortgen(96, 96, yan=512, sol_ust=(100, 100))
        m = get_masks(self._sonuc(t), 512, 512)
        self.assertEqual(0, int(m[BARIYER_ENGEL_SINIFI].sum()))

    def test_MADDE_15_engel_katmani_yalniz_BUYUR(self):
        """Serbest alan `zemin AND NOT engel`; engeli buyutmek onu KUCULTUR."""
        t = _dikdortgen(240, 14, yan=512, sol_ust=(100, 250))
        acik = get_masks(self._sonuc(t), 512, 512)
        from unittest import mock
        with mock.patch.object(rpi_inference, "ince_bariyer_maskesi",
                               lambda *a, **k: None):
            kapali = get_masks(self._sonuc(t), 512, 512)
        self.assertTrue(
            np.all(acik[BARIYER_ENGEL_SINIFI] >= kapali[BARIYER_ENGEL_SINIFI]),
            "dedektor engel katmanindan piksel CIKARDI (madde 15 ihlali)")
        self.assertTrue(np.array_equal(acik[0], kapali[0]),
                        "dedektor ZEMIN katmanina dokundu")

    def test_goruntu_YOKSA_sessizce_atlanir(self):
        """Sahte model / eski sonuc nesnesi zinciri kirmamali."""
        class _Gorunusuz:
            masks = None
            orig_img = None
        m = get_masks([_Gorunusuz()], 64, 64)
        self.assertEqual(0, int(m[BARIYER_ENGEL_SINIFI].sum()))

    def test_ENGEL_sinifi_istenmemisse_dokunmaz(self):
        t = _dikdortgen(240, 14, yan=512, sol_ust=(100, 250))
        m = get_masks(self._sonuc(t), 512, 512, sinif_idler=(0,))
        self.assertEqual({0}, set(m.keys()))
        self.assertEqual(0, int(m[0].sum()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
