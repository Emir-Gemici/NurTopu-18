"""T153 KAPISI: ince BETON SERIT (drenaj kanali / bordur) engel sayilir, YOL SAYILMAZ.

Kusur (REVIEW_LOG D-289 / D-290, gercek karede olculdu, model degismeden):
  v35 engel->zemin sizintisi TEK kaynakli — yol kenarindaki beton drenaj kanali
  (acik gri/beyaz, ~5-15 px @960, uzun) zemin sayiliyor; val82'de 10 yanlis
  guzergahin 8'i bu kanal ustunde, test29'da 196 numarali karede rota kanal
  ustunde. Cozum T67 kalibinda KATMAN 2 klasik dedektor (ON_KAYIT §13).

🔴 BU PAKETIN ASIL ISI TUZAGI KILITLEMEK: "acik renkli = engel" naif kurali
GENIS ACIK YOLU da engel yapar ve rota hic uretilmez. Ayrim GENISLIKLE
yapilir; genislik UST siniri kalkinca genis yol da engel olur — bu dosyadaki
`test_GENIS_ACIK_YOL_engel_SAYILMAZ` o mutasyonda DUSMELIDIR (rapor kaniti:
results/t153/rapor.md).

Ikinci kilit: VARSAYILAN KAPALI. Kapaliyken `get_masks` ciktisi T153
oncesiyle BAYT-ES aynidir; benimseme ON_KAYIT §13 kuralina baglidir ve o
karar mimarindir. Sabit acilirsa bu dosyadaki varsayilan testi de bilerek
guncellenir — sessizce degismez.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import karar_sozlesmesi as KS  # noqa: E402
import rpi_inference  # noqa: E402
from karar_sozlesmesi import (BARIYER_EN_BOY_ORANI,  # noqa: E402
                              BARIYER_ENGEL_SINIFI,
                              INCE_BETON_ASGARI_UZUNLUK_ORANI,
                              INCE_BETON_EN_BOY_ORANI,
                              INCE_BETON_GENISLIK_ALT_ORANI,
                              INCE_BETON_GENISLIK_UST_ORANI,
                              INCE_BETON_KROMA_UST, INCE_BETON_L_ESIGI,
                              INCE_BETON_SERIT_ETKIN,
                              INCE_BETON_SERIT_ORTAM_DEGISKENI,
                              ince_beton_serit_maskesi)
from rpi_inference import get_masks  # noqa: E402

YAN = 512
ZEMIN = (70, 70, 70)          # koyu toprak (L ~ 30)
BETON = (235, 235, 235)       # acik gri beton (L ~ 236, kroma 0)
KIRMIZI = (28, 26, 205)       # doymus kirmizi — T67'nin alani


def _tuval(yan=YAN):
    return np.full((yan, yan, 3), ZEMIN, np.uint8)


def _serit(genislik, p0=(80, 420), p1=(430, 90), renk=BETON, tuval=None):
    """Capraz, `genislik` px kalinliginda dolu serit (kanal gorunumu)."""
    t = _tuval() if tuval is None else tuval
    cv2.line(t, p0, p1, renk, int(genislik), cv2.LINE_8)
    return t


def _dikdortgen(bw, bh, sol_ust=(60, 200), renk=BETON, tuval=None):
    t = _tuval() if tuval is None else tuval
    x, y = sol_ust
    cv2.rectangle(t, (x, y), (x + bw - 1, y + bh - 1), renk, -1)
    return t


class _SahteSonuc:
    """`get_masks` icin en kucuk sonuc nesnesi: model HICBIR SEY gormedi."""

    def __init__(self, goruntu):
        self.masks = None
        self.orig_img = goruntu


def _ortamsiz():
    """Ortam degiskeni TEMIZ — test makinenin ayarina bagli kalmasin."""
    ortam = {k: v for k, v in os.environ.items()
             if k != INCE_BETON_SERIT_ORTAM_DEGISKENI}
    return mock.patch.dict(os.environ, ortam, clear=True)


class SozlesmeTests(unittest.TestCase):

    def test_VARSAYILAN_KAPALI(self):
        """ON_KAYIT §13: benimseme kurali saglanmadan varsayilan ACILMAZ."""
        self.assertIs(INCE_BETON_SERIT_ETKIN, False)

    def test_olcutler_ORAN_olarak_tanimli_ve_sirali(self):
        """CONTRACTS SS8: mutlak piksel degil oran; alt < ust; uzunluk > ust."""
        for oran in (INCE_BETON_GENISLIK_ALT_ORANI, INCE_BETON_GENISLIK_UST_ORANI,
                     INCE_BETON_ASGARI_UZUNLUK_ORANI):
            self.assertGreater(oran, 0.0)
            self.assertLess(oran, 1.0)
        self.assertLess(INCE_BETON_GENISLIK_ALT_ORANI, INCE_BETON_GENISLIK_UST_ORANI)
        self.assertGreater(INCE_BETON_ASGARI_UZUNLUK_ORANI, INCE_BETON_GENISLIK_UST_ORANI)
        # ON_KAYIT §13: 3-14 px @512
        self.assertEqual(3, round(INCE_BETON_GENISLIK_ALT_ORANI * 512))
        self.assertEqual(14, round(INCE_BETON_GENISLIK_UST_ORANI * 512))

    def test_en_boy_T67_ile_AYNI(self):
        self.assertEqual(BARIYER_EN_BOY_ORANI, INCE_BETON_EN_BOY_ORANI)

    def test_kroma_esigi_T67_kirmizisinin_ALTINDA(self):
        """Iki dedektor ayni yapiyi SECEMEZ: beton kroma ustu < bariyer kroma alti."""
        self.assertLess(INCE_BETON_KROMA_UST, KS.BARIYER_KROMA_ESIGI)


class DedektorTests(unittest.TestCase):

    def test_DAR_ACIK_SERIT_engel_SAYILIR(self):
        """POZITIF KONTROL: 6 px @512 kanal (fiziksel ~0,5 m) yakalanir."""
        t = _serit(6)
        m = ince_beton_serit_maskesi(t)
        self.assertIsNotNone(m)
        self.assertEqual(m.shape, (YAN, YAN))
        beton = np.all(t == BETON, axis=2)
        yakalanan = float((m > 0)[beton].mean())
        self.assertGreater(yakalanan, 0.80, f"seridin yalniz %{100*yakalanan:.0f}'i yakalandi")
        # zemin uzerine TASMAZ (kapama sisirmesi dahil 2 px pay)
        dis = cv2.dilate(beton.astype(np.uint8), np.ones((5, 5), np.uint8)) == 0
        self.assertEqual(0, int((m > 0)[dis].sum()), "serit disina engel yazildi")

    def test_genislik_bandinin_ICINDEKI_her_serit_yakalanir(self):
        for g in (4, 8, 12):
            with self.subTest(genislik=g):
                self.assertGreater(int(ince_beton_serit_maskesi(_serit(g)).sum()), 0)

    def test_GENIS_ACIK_YOL_engel_SAYILMAZ(self):
        """🔴 TUZAK KILIDI: 60 px @512 acik toprak yol (uzun: 400 px) YOL kalir.

        MUTASYON: `INCE_BETON_GENISLIK_UST_ORANI` kaldirilinca (1.0) bu test
        DUSER — genislik ust siniri "yol degil kanal" ayriminin tasiyicisidir.
        """
        for bw in (30, 60, 120):
            with self.subTest(genislik=bw):
                t = _dikdortgen(400, bw, sol_ust=(50, 150))
                self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()),
                                 f"{bw} px genis yol engel sayildi — rota HIC uretilmez")

    def test_GENIS_CAPRAZ_YOL_engel_SAYILMAZ(self):
        t = _serit(40)
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))

    def test_KABLO_ince_cizgi_engel_SAYILMAZ(self):
        """ALT sinir: 1-2 px tel/kablo/kenar cizgisi (f196'da havai hat var).

        Capraz 1 px + yatay 2 px (capraz 2 px cizgi rasterde 3 px'e cikar ve
        alt siniri gecer; sinir piksel genisligi uzerinden tanimlidir).
        """
        self.assertEqual(0, int(ince_beton_serit_maskesi(_serit(1)).sum()))
        t = _tuval()
        cv2.rectangle(t, (60, 256), (450, 257), BETON, -1)      # 2 px yatay
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))

    def test_KISA_PARLAK_LEKE_engel_SAYILMAZ(self):
        """Uzun degil: 6 x 20 px tas / arac tavani."""
        t = _dikdortgen(20, 6, sol_ust=(200, 200))
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))
        # en/boy tam esikte (4x) ama asgari uzunlugun altinda -> yine 0
        t = _dikdortgen(24, 6, sol_ust=(200, 200))
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))

    def test_KIRMIZI_SERIT_bu_dedektore_GIRMEZ(self):
        """Kroma: kirmizi bariyer T67'nin isidir; burada 0 (cakisma yok)."""
        t = _serit(6, renk=KIRMIZI)
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))
        self.assertGreater(int(KS.ince_bariyer_maskesi(_dikdortgen(300, 6, sol_ust=(100, 250), renk=KIRMIZI)).sum()), 0,
                           "fikstur T67 tarafinda da sinanmis olmali")

    def test_KONTRASTSIZ_serit_engel_SAYILMAZ(self):
        """Parlak yol ortasindaki biraz daha parlak serit: halka kontrasti < esik."""
        t = np.full((YAN, YAN, 3), (228, 228, 228), np.uint8)   # L ~ 229 >= esik
        cv2.line(t, (80, 420), (430, 90), (240, 240, 240), 6)    # fark ~10 L
        self.assertEqual(0, int(ince_beton_serit_maskesi(t).sum()))

    def test_AYNI_KAREDE_yol_KALIR_kanal_ENGEL(self):
        """Gercek sahne: genis acik yol + kenarinda dar kanal (f157 gorunumu)."""
        t = _dikdortgen(60, 400, sol_ust=(200, 60))              # dikey genis yol
        cv2.line(t, (300, 60), (300, 459), BETON, 6)             # yolun sagindaki kanal
        m = ince_beton_serit_maskesi(t)
        self.assertEqual(0, int(m[60:460, 200:260].sum()), "YOL engel oldu")
        self.assertGreater(int(m[100:420, 297:304].sum()), 0, "kanal KACIRILDI")

    def test_fail_closed_cozulemeyen_girdi(self):
        self.assertIsNone(ince_beton_serit_maskesi(np.zeros((32, 32), np.uint8)))
        self.assertIsNone(ince_beton_serit_maskesi(np.zeros((0, 0, 3), np.uint8)))
        kucuk = ince_beton_serit_maskesi(np.full((2, 2, 3), 255, np.uint8))
        self.assertEqual(0, int(kucuk.sum()))

    def test_olcek_bagimsiz_ORAN(self):
        """1024 tuvalde 12 px serit (= 6 px @512) de yakalanir."""
        t = np.full((1024, 1024, 3), ZEMIN, np.uint8)
        cv2.line(t, (160, 840), (860, 180), BETON, 12)
        self.assertGreater(int(ince_beton_serit_maskesi(t).sum()), 0)
        # ayni tuvalde 6 px (= 3 px @512 altinda: 2 px) serit alt sinirin altinda kalir
        t2 = np.full((1024, 1024, 3), ZEMIN, np.uint8)
        cv2.line(t2, (160, 840), (860, 180), BETON, 4)
        self.assertEqual(0, int(ince_beton_serit_maskesi(t2).sum()))


class GetMasksTests(unittest.TestCase):
    """Uretim yolu: `get_masks` ENGEL katmanina OR; kapaliyken BAYT-ES."""

    def setUp(self):
        self.t = _serit(6)
        self.assertGreater(int(ince_beton_serit_maskesi(self.t).sum()), 0,
                           "fikstur dedektoru tetiklemiyor; kapali/acik farki sinanmaz")

    def test_KAPALI_varsayilan_BAYT_ES(self):
        with _ortamsiz():
            kapali = get_masks([_SahteSonuc(self.t)], YAN, YAN)
            acik_degil = get_masks([_SahteSonuc(self.t)], YAN, YAN, ince_beton_serit=False)
        for k in (0, 1):
            self.assertEqual(kapali[k].tobytes(), acik_degil[k].tobytes())
        self.assertEqual(0, int(kapali[BARIYER_ENGEL_SINIFI].sum()),
                         "KAPALIYKEN engel katmanina bir sey eklendi")

    def test_ACIK_parametre_engele_OR(self):
        with _ortamsiz():
            acik = get_masks([_SahteSonuc(self.t)], YAN, YAN, ince_beton_serit=True)
        beklenen = ince_beton_serit_maskesi(self.t)
        self.assertEqual(acik[BARIYER_ENGEL_SINIFI].tobytes(), beklenen.tobytes())
        self.assertEqual(0, int(acik[0].sum()), "ZEMIN katmanina dokunuldu")

    def test_ACIK_farkli_cozunurluk_yeniden_olceklenir(self):
        with _ortamsiz():
            acik = get_masks([_SahteSonuc(self.t)], 2048, 2048, ince_beton_serit=True)
        self.assertEqual((2048, 2048), acik[BARIYER_ENGEL_SINIFI].shape)
        self.assertGreater(int(acik[BARIYER_ENGEL_SINIFI].sum()), 0)

    def test_ORTAM_DEGISKENI_1_acar_0_kapatir(self):
        with _ortamsiz(), mock.patch.dict(os.environ, {INCE_BETON_SERIT_ORTAM_DEGISKENI: "1"}):
            self.assertGreater(int(get_masks([_SahteSonuc(self.t)], YAN, YAN)[1].sum()), 0)
        with _ortamsiz(), mock.patch.dict(os.environ, {INCE_BETON_SERIT_ORTAM_DEGISKENI: "0"}):
            self.assertEqual(0, int(get_masks([_SahteSonuc(self.t)], YAN, YAN)[1].sum()))
        # parametre ortamdan USTUNDUR
        with _ortamsiz(), mock.patch.dict(os.environ, {INCE_BETON_SERIT_ORTAM_DEGISKENI: "1"}):
            self.assertEqual(0, int(get_masks([_SahteSonuc(self.t)], YAN, YAN,
                                              ince_beton_serit=False)[1].sum()))

    def test_MADDE_15_serbest_alan_yalniz_KUCULUR(self):
        """serbest(K1 AND NOT K2): acikken kapaliya gore ALT KUME."""
        zemin = np.ones((YAN, YAN), np.uint8)   # model her yeri zemin gordu varsayimi
        with _ortamsiz():
            kapali = get_masks([_SahteSonuc(self.t)], YAN, YAN, ince_beton_serit=False)
            acik = get_masks([_SahteSonuc(self.t)], YAN, YAN, ince_beton_serit=True)
        serbest_kapali = zemin & (kapali[1] == 0)
        serbest_acik = zemin & (acik[1] == 0)
        self.assertTrue(bool(np.all(serbest_acik <= serbest_kapali)))
        self.assertLess(int(serbest_acik.sum()), int(serbest_kapali.sum()),
                        "acikken hicbir sey cikarilmadi — kapi bos yere yesil")

    def test_goruntusuz_sonucta_SESSIZCE_atlanir(self):
        r = _SahteSonuc(None)
        with _ortamsiz():
            m = get_masks([r], YAN, YAN, ince_beton_serit=True)
        self.assertEqual(0, int(m[1].sum()))

    def test_T67_bariyer_ile_BIRLIKTE_calisir(self):
        """Ayni karede kirmizi bariyer (T67) + beton kanal (T153): ikisi de engel."""
        t = _serit(6)
        cv2.rectangle(t, (100, 470), (400, 484), KIRMIZI, -1)
        with _ortamsiz():
            m = get_masks([_SahteSonuc(t)], YAN, YAN, ince_beton_serit=True)
        self.assertGreater(int(m[1][470:485, 100:400].sum()), 0, "bariyer kayboldu")
        beton = np.all(t == BETON, axis=2)
        self.assertGreater(float(m[1][beton].mean()), 0.8, "kanal kayboldu")


if __name__ == "__main__":
    unittest.main()
