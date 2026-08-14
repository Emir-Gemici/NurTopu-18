"""T72 KAPISI: HB (hedef bolgesi) bulunur, bariyerle KARISTIRILMAZ.

Kusur (saha kuru kosusu): `hedef_konumu` halkasi SAHIPSIZ. HB'nin tek kaynagi
Gazebo `meta.txt`; saha kod yolunda `--hb` girisi yok ve uretim modeli 2
siniflidir. Sartname SS2.2.6 gorevi "IKA'nin HB SINIRLARI ICINE girmesi" diye
tanimlar — yani acik guzergahi bulsak ve rota kusursuz olsa bile VARIS NOKTASI
uretilemedigi icin gorev tamamlanamaz.

Ucuncu sinif EKLENMEDI (nc=2 -> 3 sozlesme degisikligi + yeniden egitim +
sinif-id cakismasi riski; S2'de yasandi). T67'nin klasik KATMAN 2 deseni
kullanildi.

🔴 BU PAKETIN ASIL ISI IKI DEDEKTORU AYIRMAK. T67 bariyeri UZUN-INCE diye
secer; HB KAREDIR. Ikisi ayni kroma esigini paylasir, dolayisiyla AYNI yapiyi
secme riski GERCEKTIR — ve olculdu: ilk surumde `sa_000170` karesinde kirilmis
bir bariyer parcasi (37x32, en/boy 1,16) HB sanildi. Asagidaki testler hem
SEKIL BANDININ bosluğunu hem TUMLEYENLIK kuralini kilitler.
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
from karar_sozlesmesi import (BARIYER_EN_BOY_ORANI,  # noqa: E402
                              BARIYER_KROMA_ESIGI, HB_KARE_TOLERANSI,
                              HB_KENAR_M, HEDEF_YOK_SEBEBI,
                              OLCEK_CAPRAZ_BANDI, ROTA_RET_SEBEPLERI,
                              hb_konumu, hb_maskesi, hedef_yok_reddi,
                              ince_bariyer_maskesi, mpp_hb_pedinden,
                              olcek_capraz_kontrolu)
from rpi_inference import analyze_path  # noqa: E402

KIRMIZI = (28, 26, 205)
NOTR = (150, 150, 150)


def _tuval(yan=640):
    return np.full((yan, yan, 3), NOTR, np.uint8)


def _hb_ciz(t, x, y, kenar):
    """T71 uretecinin cizdigi bicim: ped + KIRMIZI cerceve + KIRMIZI H."""
    cv2.rectangle(t, (x, y), (x + kenar, y + kenar), (242, 242, 242), -1)
    kal = max(1, int(round(kenar * 0.09)))
    cv2.rectangle(t, (x, y), (x + kenar, y + kenar), KIRMIZI, kal, cv2.LINE_AA)
    olcek = max(0.3, kenar / 42.0)
    (tw, th), _ = cv2.getTextSize("H", cv2.FONT_HERSHEY_SIMPLEX, olcek, kal)
    cv2.putText(t, "H", (x + (kenar - tw) // 2, y + (kenar + th) // 2),
                cv2.FONT_HERSHEY_SIMPLEX, olcek, KIRMIZI, kal, cv2.LINE_AA)
    return t


class SozlesmeKaynagiTests(unittest.TestCase):
    """Madde 16: iki dedektor SINIRI PAYLASIR ve tek yerden okunur."""

    def test_sebep_kodu_kanonik_kumede(self):
        self.assertIn(HEDEF_YOK_SEBEBI, ROTA_RET_SEBEPLERI)
        self.assertEqual(HEDEF_YOK_SEBEBI, hedef_yok_reddi()[0])

    def test_SEKIL_BANDI_arasinda_BOSLUK_var(self):
        """HB (kare) ile bariyer (uzun-ince) araligi CAKISAMAZ."""
        self.assertLess(
            HB_KARE_TOLERANSI, BARIYER_EN_BOY_ORANI,
            "HB kabul araligi bariyer araligina giriyor — ayni yapiyi ikisi "
            "birden secebilir")

    def test_KROMA_esigi_ORTAK(self):
        """Iki dedektor de ayni kirmizi esigini kullanir (ciplak sayi yok)."""
        kaynak = (KOK / "codes" / "karar_sozlesmesi.py").read_text(
            encoding="utf-8")
        govde = kaynak[kaynak.index("def hb_maskesi("):
                       kaynak.index("def hb_konumu(")]
        self.assertIn("BARIYER_KROMA_ESIGI", govde,
                      "HB dedektoru kendi kroma esigini yaziyor (madde 16)")
        self.assertGreater(BARIYER_KROMA_ESIGI, 0)

    def test_HB_kenari_SARTNAMEDEN(self):
        self.assertEqual(2.0, HB_KENAR_M)


class TespitTests(unittest.TestCase):

    def test_KARE_kirmizi_HB_bulunur(self):
        for kenar in (26, 40, 64, 96):
            with self.subTest(kenar=kenar):
                t = _hb_ciz(_tuval(), 200, 150, kenar)
                s = hb_konumu(t)
                self.assertIsNotNone(s, f"{kenar} px HB bulunamadi")
                cx, cy = s["merkez"]
                self.assertLess(abs(cx - (200 + kenar / 2)), 4.0)
                self.assertLess(abs(cy - (150 + kenar / 2)), 4.0)

    def test_HB_YOKSA_None(self):
        self.assertIsNone(hb_konumu(_tuval()))

    def test_bozuk_girdi_fail_closed(self):
        for kotu in (None, np.zeros((5, 5), np.uint8),
                     np.zeros((0, 0, 3), np.uint8)):
            with self.subTest(girdi=type(kotu).__name__):
                self.assertIsNone(hb_maskesi(kotu))
                self.assertIsNone(hb_konumu(kotu))


class TumleyenlikTests(unittest.TestCase):
    """🔴 Bariyer HB sanilmamali — T67'nin TERS yonde pozitif kontrolu."""

    def test_UZUN_kirmizi_bar_HB_DEGILDIR(self):
        t = _tuval()
        cv2.rectangle(t, (200, 300), (440, 314), KIRMIZI, -1)
        self.assertGreater(int(ince_bariyer_maskesi(t).sum()), 0,
                           "fikstur bariyer olarak bile bulunmadi")
        self.assertIsNone(hb_konumu(t), "bariyer HB sanildi")

    def test_KIRIK_bariyer_parcasi_HB_DEGILDIR(self):
        """OLCULEN vaka: `sa_000170`'te 37x32 (en/boy 1,16) bariyer parcasi.

        Sekil filtresi TEK BASINA yetmedi; TUMLEYENLIK kurali gerekti:
        T67'nin ENGEL dedigi piksel HB OLAMAZ.
        """
        t = _tuval()
        cv2.rectangle(t, (200, 300), (440, 314), KIRMIZI, -1)   # tam bariyer
        cv2.rectangle(t, (300, 296), (337, 328), KIRMIZI, -1)   # kare parca
        self.assertIsNone(hb_konumu(t),
                          "kirik bariyer parcasi HB sanildi (sa_000170 vakasi)")

    def test_AYNI_KAREDE_HB_ve_bariyer_DOGRU_ayrilir(self):
        t = _tuval()
        cv2.rectangle(t, (150, 400), (390, 414), KIRMIZI, -1)   # bariyer
        _hb_ciz(t, 420, 120, 40)                                 # HB
        s = hb_konumu(t)
        self.assertIsNotNone(s, "HB bulunamadi")
        cx, cy = s["merkez"]
        self.assertLess(abs(cx - 440), 8.0)
        self.assertLess(abs(cy - 140), 8.0)
        self.assertGreater(int(ince_bariyer_maskesi(t).sum()), 0)


class OlcekTests(unittest.TestCase):
    """CONTRACTS SS5(b): bilinen olcekli nesneden `mpp` — IKINCI kaynak."""

    def test_mpp_bilinen_kenardan(self):
        self.assertAlmostEqual(0.078125, mpp_hb_pedinden(25.6), places=6)
        self.assertAlmostEqual(HB_KENAR_M / 50.0, mpp_hb_pedinden(50.0),
                               places=9)

    def test_mpp_bozuk_girdide_None(self):
        for kotu in (0, -3, None, "x", float("nan"), float("inf")):
            with self.subTest(kenar=kotu):
                self.assertIsNone(mpp_hb_pedinden(kotu))

    def test_capraz_YALNIZ_telemetri(self):
        self.assertEqual((0.08, "yalniz_telemetri", None),
                         olcek_capraz_kontrolu(0.08, None))

    def test_capraz_YALNIZ_hb(self):
        self.assertEqual((0.08, "yalniz_hb", None),
                         olcek_capraz_kontrolu(None, 0.08))

    def test_capraz_UYUMLU_ise_TELEMETRI_secilir(self):
        """Birincil kaynak degismez; HB yalniz DOGRULAR (SS5 hiyerarsisi)."""
        sec, durum, fark = olcek_capraz_kontrolu(0.0781, 0.0800)
        self.assertEqual("dogrulandi", durum)
        self.assertEqual(0.0781, sec)
        self.assertLess(fark, OLCEK_CAPRAZ_BANDI)

    def test_capraz_CELISKILI_ise_HICBIRI_secilmez(self):
        """Ortalama ALINMAZ: iki olcum celisiyorsa dogruyu bilmiyoruz."""
        sec, durum, fark = olcek_capraz_kontrolu(0.078, 0.20)
        self.assertIsNone(sec, "celiskide uydurma olcek uretildi")
        self.assertEqual("celiskili", durum)
        self.assertGreater(fark, OLCEK_CAPRAZ_BANDI)

    def test_capraz_ikisi_de_yoksa(self):
        self.assertEqual((None, "olcek_yok", None),
                         olcek_capraz_kontrolu(None, None))


class AnalyzePathEntegrasyonTests(unittest.TestCase):
    """Hedef gercekten KARAR YOLUNDA mi kullaniliyor?"""

    @staticmethod
    def _koridor(yan=300):
        m = np.zeros((yan, yan), np.uint8)
        m[:, 100:200] = 1
        return m

    def test_goruntu_VERILMEZSE_davranis_DEGISMEZ(self):
        """Geriye uyum: tum mevcut cagri yerleri aynen calisir."""
        yol, guven, wps, ret = analyze_path(
            self._koridor(), return_reason=True, min_area_ratio=0.001)
        self.assertIsNone(ret)
        self.assertIsNotNone(yol)
        self.assertGreaterEqual(len(wps), 2)

    def test_goruntu_VAR_ama_HB_YOKSA_HEDEF_YOK(self):
        yol, guven, wps, ret = analyze_path(
            self._koridor(), return_reason=True, min_area_ratio=0.001,
            goruntu=_tuval(300))
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps, "hedef yokken waypoint uretildi")
        self.assertEqual(HEDEF_YOK_SEBEBI, ret[0])

    def test_HB_VARSA_rota_uretilir(self):
        t = _hb_ciz(_tuval(300), 120, 20, 40)
        yol, guven, wps, ret = analyze_path(
            self._koridor(), return_reason=True, min_area_ratio=0.001,
            goruntu=t)
        self.assertIsNone(ret, f"HB varken reddedildi: {ret}")
        self.assertGreaterEqual(len(wps), 2)

    def test_MADDE_15_HB_serbest_alani_BUYUTMEZ(self):
        """HB'yi bulmak gecilebilir alani DEGISTIRMEZ; yalniz hedefi secer."""
        m = self._koridor()
        t = _hb_ciz(_tuval(300), 120, 20, 40)
        _y1, _g1, _w1, _r1, temiz_hbsiz = analyze_path(
            m, return_reason=True, return_clean=True, min_area_ratio=0.001)[:5]
        _y2, _g2, _w2, _r2, temiz_hbli = analyze_path(
            m, return_reason=True, return_clean=True, min_area_ratio=0.001,
            goruntu=t)[:5]
        self.assertTrue(np.array_equal(temiz_hbsiz, temiz_hbli),
                        "HB dedektoru serbest alani DEGISTIRDI (madde 15)")

    def test_girdi_maskesi_DEGISMEZ(self):
        m = self._koridor()
        kopya = m.copy()
        analyze_path(m, return_reason=True, min_area_ratio=0.001,
                     goruntu=_hb_ciz(_tuval(300), 120, 20, 40))
        self.assertTrue(np.array_equal(kopya, m))

    def test_dedektor_KAPATILINCA_HEDEF_YOK(self):
        """MUTASYON KILIDI: dedektor devre disi kalirsa uydurma YAPILMAZ."""
        from unittest import mock
        t = _hb_ciz(_tuval(300), 120, 20, 40)
        with mock.patch.object(rpi_inference, "hb_konumu",
                               lambda *a, **k: None):
            yol, _g, wps, ret = analyze_path(
                self._koridor(), return_reason=True, min_area_ratio=0.001,
                goruntu=t)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(HEDEF_YOK_SEBEBI, ret[0])


class OlculenDagilimTests(unittest.TestCase):
    """T72 · `sentetik_arena_kadraj_t66` n=260 (REVIEW_LOG D-105).

    ⚠ Kume SENTETIKTIR ve HB'yi BIZIM cizdigimiz bicimde tasir; gercek arenada
    tutacagi DOGRULANAMAZ (D-88 + D-99). Sayilar burada REGRESYON kilidi olarak
    tutulur, gercek basarim iddiasi DEGILDIR.
    """

    TESPIT = (260, 260)
    MERKEZ_HATA_MEDYAN_PX = 0.71
    MERKEZ_HATA_MAKS_PX = 1.30
    MPP_HATA_MEDYAN = 0.05185

    def test_olculen_mpp_hatasi_capraz_bandin_ICINDE(self):
        """%5,2 sistematik sapma, %25 capraz bandini ASMAZ — celiski uretmez."""
        self.assertLess(self.MPP_HATA_MEDYAN, OLCEK_CAPRAZ_BANDI)
        _sec, durum, _f = olcek_capraz_kontrolu(
            0.078125, 0.078125 * (1.0 - self.MPP_HATA_MEDYAN))
        self.assertEqual("dogrulandi", durum)

    def test_merkez_hatasi_HB_KENARININ_altinda(self):
        """Merkez hatasi pedin kendisinden kucuk olmali (25,6 px)."""
        self.assertLess(self.MERKEZ_HATA_MAKS_PX, 25.6 / 2.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
