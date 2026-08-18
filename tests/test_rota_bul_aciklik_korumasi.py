"""T95 KAPISI: `rota_bul` (KATMAN B) `yol_duzelt`e `dt_px` GECIRIR.

NEDEN (REVIEW_LOG D-158 denetim bulgusu 2 · D-159 · D-162 · D-164).
T94 aciklik koruma kuralini `yol_duzelt`e ekledi ama YALNIZ `rpi_inference`
(KATMAN A) yolunda devreye aldi. `rota_bul` ayni fonksiyonu `dt_px`
GECIRMEDEN cagiriyordu — oysa `sonuc["dt_px"]` bir satir once kapsamdaydi.
Kural `dt_px=None` iken TAMAMEN KAPALIDIR, yani KATMAN B (`iha_haritala` ->
yayinlanan `road`) korumasiz kaliyordu.

OLCULDU (n=260, t66, ayni kosumda taban vs koruma, ayni `mk` maskeleri):
    kayip medyani 3,00 -> 0,693 px  ·  pay < 3 px olan ACIK kare  3 -> 0
    ACIK 31 -> 31 · `yol_no` 31/31 karede AYNI · waypoint medyani 31 -> 32
    gurultu altinda (sigma 2/255, 3 cekilis) ceviren kare 26 -> 26 ve
    ceviren kare KUMELERI BIREBIR AYNI · DOGRULAMA_BASARISIZ 0 -> 0

BU TESTLERIN ISI: baglantinin KOPMADIGINI kilitlemek. Kural `dt_px=None`
ile sessizce kapandigi icin, `dt_px` argumaninin dusmesi HICBIR HATA
URETMEZ — yalnizca koruma yok olur. D-58/D-60/D-116 sapma sinifi tam budur.

⚠ POZITIF KONTROL ZORUNLU (D-15/K-04: sifir olcum basari sayilmaz). Asagida
  · sahnenin `yol_duzelt`e GERCEKTEN ULASTIGI ayrica sinanir (ulasmazsa
    butun testler bos yere yesil yanardi),
  · ve `_dt_px_gecildi_mi` yardimcisinin DUSEBILDIGI karsi kontrolle
    gosterilir.
"""

import unittest

import numpy as np

from codes import costmap_path_finder as C

MPP = 0.10          # 10 cm/px -> r_gerekli_px = 1,10 / 0,10 = 11,0


def _uc_koridorlu_sahne():
    """Uc dusey koridor, ustte birlesme bandi, iki yan koridor KAPALI.

    `rota_bul`un `durum == "ACIK"` verip A* ve `yol_duzelt`e kadar gitmesi
    icin gereken en kucuk sahne. Koridor genisligi 60 px secildi: C-uzayi
    (`dt_px >= 11`) daralttiktan sonra `koridor_adaylari`nin asgari kapi
    genisligi olan `2 * r_gerekli_px = 22 px` rahatca saglanir.
    """
    n = 300
    zemin = np.zeros((n, n), np.uint8)
    engel = np.zeros((n, n), np.uint8)
    for cx in (60, 150, 240):
        zemin[:, cx - 30:cx + 30] = 1
    zemin[5:50, :] = 1                     # ust birlesme bandi (hedef bandi)
    engel[200:216, 30:90] = 1              # SOL koridor kapali
    engel[200:216, 210:270] = 1            # SAG koridor kapali
    return {0: zemin, 1: engel}


class RotaBulAciklikKorumasi(unittest.TestCase):

    def _kosup_yakala(self):
        """`rota_bul`u kos, `serbest_alan` ve `yol_duzelt` cagrilarini yakala.

        Uretim kodu DEGISTIRILMEZ; yalniz modul nitelikleri gecici olarak
        sarmalanir ve `finally` ile geri konur.
        """
        yakalanan = {"duzelt": [], "dt_px": []}
        gercek_serbest = C.serbest_alan
        gercek_duzelt = C.yol_duzelt

        def serbest(*a, **kw):
            s = gercek_serbest(*a, **kw)
            yakalanan["dt_px"].append(s["dt_px"])
            return s

        def duzelt(yol_px, gecilebilir_tam, **kw):
            yakalanan["duzelt"].append((gecilebilir_tam, kw))
            return gercek_duzelt(yol_px, gecilebilir_tam, **kw)

        C.serbest_alan = serbest
        C.yol_duzelt = duzelt
        try:
            sonuc = C.rota_bul(_uc_koridorlu_sahne(), mpp=MPP)
        finally:
            C.serbest_alan = gercek_serbest
            C.yol_duzelt = gercek_duzelt
        return sonuc, yakalanan

    @staticmethod
    def _dt_px_gecildi_mi(cagrilar):
        """Her `yol_duzelt` cagrisinda kullanilabilir bir `dt_px` var mi?

        Bos liste FAIL sayilir: hic cagri yoksa "gecildi" denemez.
        """
        return bool(cagrilar) and all(
            kw.get("dt_px") is not None for _gec, kw in cagrilar)

    # ── pozitif kontrol: sahne gercekten yol_duzelt'e ulasiyor mu ──────────
    def test_sahne_yol_duzelte_ULASIYOR(self):
        sonuc, y = self._kosup_yakala()
        self.assertEqual("ACIK", sonuc["durum"], sonuc.get("sebep"))
        self.assertTrue(
            y["duzelt"],
            "yol_duzelt HIC cagrilmadi — asagidaki testler BOS YERE gecerdi")
        self.assertTrue(sonuc["waypoints_px"], "rota uretilmedi")

    # ── asil kapi ─────────────────────────────────────────────────────────
    def test_rota_bul_yol_duzelte_dt_px_GECIRIYOR(self):
        _sonuc, y = self._kosup_yakala()
        self.assertTrue(
            self._dt_px_gecildi_mi(y["duzelt"]),
            "rota_bul `yol_duzelt`e `dt_px` GECIRMIYOR — aciklik korumasi "
            "sessizce KAPALI (D-158 bulgu 2 · D-164)")

    def test_gecilen_dt_px_SERBEST_ALANIN_URETTIGI_DIZIDIR(self):
        """Herhangi bir dizi degil, `serbest_alan`in dondurdugu `dt_px`.

        Baska bir mesafe donusumu gecilseydi kural, uretimin C-uzayini
        kurdugu alandan FARKLI bir alana karsi kilitlenirdi (D-158 bulgu 4
        aynen bu hataydi: test `DIST_MASK_PRECISE`, uretim `DIST_L2, 5`).
        """
        _sonuc, y = self._kosup_yakala()
        self.assertTrue(y["dt_px"], "serbest_alan cagrilmadi")
        gecen = y["duzelt"][0][1]["dt_px"]
        self.assertIs(gecen, y["dt_px"][-1],
                      "gecilen dizi `sonuc['dt_px']` DEGIL — baska bir alan")

    def test_dt_px_ile_gecilebilir_tam_AYNI_SEKILDE(self):
        """`yol_duzelt` uyusmazlikta `ValueError` firlatir; kapi burada,
        cagri yerinde de kilitlenir."""
        _sonuc, y = self._kosup_yakala()
        gecilebilir, kw = y["duzelt"][0]
        self.assertEqual(np.shape(gecilebilir), np.shape(kw["dt_px"]))

    # ── karsi kontrol: yardimci DUSEBILIYOR mu ────────────────────────────
    def test_KARSI_KONTROL_yardimci_dusebiliyor(self):
        """`_dt_px_gecildi_mi` her zaman True donen bos bir kontrol degil."""
        self.assertFalse(self._dt_px_gecildi_mi([]))
        self.assertFalse(self._dt_px_gecildi_mi(
            [(np.zeros((4, 4)), {"wp_aralik_px": 5})]))
        self.assertFalse(self._dt_px_gecildi_mi(
            [(np.zeros((4, 4)), {"dt_px": None})]))
        self.assertFalse(self._dt_px_gecildi_mi([
            (np.zeros((4, 4)), {"dt_px": np.zeros((4, 4))}),
            (np.zeros((4, 4)), {"wp_aralik_px": 5}),      # biri bile eksikse FAIL
        ]))
        self.assertTrue(self._dt_px_gecildi_mi(
            [(np.zeros((4, 4)), {"dt_px": np.zeros((4, 4))})]))


if __name__ == "__main__":
    unittest.main()
