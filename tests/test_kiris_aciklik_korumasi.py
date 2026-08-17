"""T94 KAPISI: string-pulling kirisi ACIKLIGI KORUMALI (REVIEW_LOG D-157).

NEDEN. `yol_duzelt`in gorus-hatti string-pulling'i bir kirisi yalnizca
C-uzayinda kaldigi icin kabul ediyordu. Olculdu (yer gercegi, n=260):
rotanin darbogazi medyan 4,00 px kaybediyor, 165/260 karede kayip > 2 px ve
260 karenin **213'unde** sonuc TAM 2 DUGUME (tek duz kiris) iniyordu.
K5'i dusuren `sa_000131`de kayip 10,47 px idi.

KURAL: kiris, YERINE GECTIGI ALT YOLDAN belirgin olarak daha dar olmamali —
`kiris_asgari >= (1 - BERABERLIK_BANDI) * alt_yol_asgari`.

⚠ SABIT ESIK DENENDI VE ELENDI (D-156): `kiris >= r_gerekli + MASKE_HATA`
K5'i cozdu ama kararliligi bozdu (8 -> 11/260), cunku SUREKLI bir buyuklugu
SABIT bir sayiyla kiyasliyordu. Goreli kiyasta iki buyukluk de AYNI maskeden
turer. Bu testler GORELI bicimi kilitler.
"""

import unittest

import numpy as np

from codes.costmap_path_finder import yol_duzelt
from codes.karar_sozlesmesi import BERABERLIK_BANDI


def _kose_sahnesi():
    """Dusey koridor + BIR YANDAN CIKINTI: kiris GECILEBILIR ama DAR.

    ⚠ Ilk denememde L bicimli bir kose kullandim; orada kirisi zaten
    `_gorus_hatti` reddediyordu (kose disari tasiyor), yani kural HIC
    sinanmiyordu. Testin pozitif kontrolu bunu yakaladi. Sahne, kirisin
    gecilebilir OLDUGU ama alt yoldan BELIRGIN olarak dar kaldigi bir
    geometriyle degistirildi.

    koridor : x 40..99 (genislik 60), tum y
    cikinti : x 40..61, y 50..69 ENGEL  -> o bantta serbest x 62..99

    Duz kiris x=70'te iner: cikinti bandinda aciklik ~8 px.
    Orta-eksene yaslanan yol x=81'e kayar: aciklik ~17-19 px.
    """
    tuval = np.zeros((120, 120), np.uint8)
    tuval[:, 40:100] = 1
    tuval[50:70, 40:62] = 0           # yan cikinti (engel)
    # A*'in uretecegi turden, cikintidan KACAN dugum dizisi
    yol = [(70, 110), (81, 60), (70, 10)]
    return tuval, yol


def _dt(gecilebilir):
    """URETIMIN kullandigi mesafe donusumu (rpi_inference.py:1157).

    ⚠ Ilk yazimda  kullanilmisti; uretim 
    kullaniyor. Bagimsiz denetim bunu yakaladi: kural, uretimin HIC
    uretmedigi bir mesafe alanina karsi kilitlenmis olurdu.
    """
    import cv2
    return cv2.distanceTransform(gecilebilir.astype(np.uint8), cv2.DIST_L2, 5)


def _polyline_asgari(nokta, dt):
    from codes.costmap_path_finder import _polyline_asgari_aciklik
    return _polyline_asgari_aciklik(nokta, dt)


class KirisAciklikKorumasiTests(unittest.TestCase):
    def setUp(self):
        self.gec, self.yol = _kose_sahnesi()
        self.dt = _dt(self.gec)

    def test_dt_verilmezse_davranis_DEGISMEZ(self):
        """Geriye uyum: `dt_px=None` iken kural HIC calismaz.

        Mevcut cagri yerleri ve eski testler bu yolla korunur.
        """
        korumasiz = yol_duzelt(self.yol, self.gec > 0,
                               wp_aralik_px=1e6, aci_esigi_derece=0.0,
                               maks_wp=len(self.yol))
        # Kiris GECILEBILIR oldugu icin string-pulling tek hamlede uca atlar.
        self.assertEqual(2, len(korumasiz))

    def test_dt_verilirse_KOSE_KESEN_kiris_REDDEDILIR(self):
        korumasiz = yol_duzelt(self.yol, self.gec > 0,
                               wp_aralik_px=1e6, aci_esigi_derece=0.0,
                               maks_wp=len(self.yol))
        korumali = yol_duzelt(self.yol, self.gec > 0,
                              wp_aralik_px=1e6, aci_esigi_derece=0.0,
                              maks_wp=len(self.yol), dt_px=self.dt)

        # POZITIF KONTROL: sahne gercekten AYIRT EDICI olmali, yoksa test bosa
        # gecer.
        self.assertGreater(
            len(korumali), len(korumasiz),
            "sahne ayirt edici degil: koruma dugum eklemedi")

        a_korumasiz = _polyline_asgari(korumasiz, self.dt)
        a_korumali = _polyline_asgari(korumali, self.dt)
        self.assertGreater(
            a_korumali, a_korumasiz,
            "koruma acikligi ARTIRMALI; artirmiyorsa kural islevsizdir")

    def test_koruma_YALNIZCA_dugum_EKLER(self):
        """Yon kontrolu: kural kisaltmayi REDDEDER, asla fazladan kisaltmaz."""
        korumasiz = yol_duzelt(self.yol, self.gec > 0,
                               wp_aralik_px=1e6, aci_esigi_derece=0.0,
                               maks_wp=len(self.yol))
        korumali = yol_duzelt(self.yol, self.gec > 0,
                              wp_aralik_px=1e6, aci_esigi_derece=0.0,
                              maks_wp=len(self.yol), dt_px=self.dt)
        self.assertGreaterEqual(len(korumali), len(korumasiz))
        # Uclar KORUNUR — kural yalnizca ARADAKI kisaltmayi etkiler.
        self.assertEqual(tuple(korumasiz[0]), tuple(korumali[0]))
        self.assertEqual(tuple(korumasiz[-1]), tuple(korumali[-1]))

    def test_band_SOZLESMEDEN_gelir(self):
        """`kiris_bandi` ciplak sayi degil; varsayilan sozlesmeden okunur."""
        import inspect
        imza = inspect.signature(yol_duzelt)
        self.assertEqual(BERABERLIK_BANDI,
                         imza.parameters["kiris_bandi"].default)

    def test_band_1_ise_hicbir_kiris_REDDEDILMEZ(self):
        """Sinir davranisi: band=1 -> esik 0 -> kural etkisiz kalmali.

        Bu, kuralin YONUNU sinar: band buyudukce koruma GEVSER.
        """
        gevsek = yol_duzelt(self.yol, self.gec > 0,
                            wp_aralik_px=1e6, aci_esigi_derece=0.0,
                            maks_wp=len(self.yol), dt_px=self.dt,
                            kiris_bandi=1.0)
        korumasiz = yol_duzelt(self.yol, self.gec > 0,
                               wp_aralik_px=1e6, aci_esigi_derece=0.0,
                               maks_wp=len(self.yol))
        self.assertEqual(len(korumasiz), len(gevsek))

    def test_asama2_KORUMAYI_SILMEZ(self):
        """Aci esigi varsayilan (15) iken de koruma AYAKTA kalmali.

        Bagimsiz denetim bulgusu: asama 2 (aci/mesafe seyreltmesi) asama 1'in
        geri ekledigi dugumleri denetimsiz siliyordu ve sonuc korumasiz haliyle
        BIREBIR ayni cikiyordu.
        """
        korumasiz = yol_duzelt(self.yol, self.gec > 0, wp_aralik_px=1e6,
                               aci_esigi_derece=15.0, maks_wp=len(self.yol))
        korumali = yol_duzelt(self.yol, self.gec > 0, wp_aralik_px=1e6,
                              aci_esigi_derece=15.0, maks_wp=len(self.yol),
                              dt_px=self.dt)
        self.assertGreater(len(korumali), len(korumasiz),
                           "asama 2 korumayi siliyor")
        self.assertGreater(_polyline_asgari(korumali, self.dt),
                           _polyline_asgari(korumasiz, self.dt))

    def test_dt_ve_maske_cozunurlugu_UYUSMALI(self):
        """Sessiz kirpma yerine ACIK hata (denetim bulgusu 8)."""
        with self.assertRaises(ValueError):
            yol_duzelt(self.yol, self.gec > 0, dt_px=self.dt[:50, :50])

    def test_tek_noktali_yol_cokmez(self):
        self.assertEqual([(5, 5)], yol_duzelt([(5, 5)], self.gec > 0,
                                              dt_px=self.dt))


if __name__ == "__main__":
    unittest.main(verbosity=2)
