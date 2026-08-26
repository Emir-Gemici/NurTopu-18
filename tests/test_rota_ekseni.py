"""S2 — K-A uc-bant kapisi ROTA EKSENINE gore (yonelim).

NEDEN: Gercek DJI karelerinde (0038, REVIEW_LOG D-281 SS3) yol kadraji ENINE
kesiyor; K-A "alt->ust bant temasi" sozlesmesi bu kareleri YAPISAL diye
reddediyor. `analyze_path(rota_ekseni_derece=...)` maskeyi dondurup K-A + A*'i
rota ekseni dikey olacak sekilde kosar, ciktiyi orijinal kareye geri cevirir.

KORUNANLAR:
  (a) None -> davranis BAYT-ES (mevcut sentetik senaryo ciktilari degismez)
  (b) dikey koridor: 0 -> rota, 90 -> UC_BANT_TEMAS_YOK;
      yatay koridor:  0 -> UC_BANT_TEMAS_YOK, 90 -> rota
  (c) geri cevrilen waypoint'ler ORIJINAL serbest maskede (madde 15)
  (d) MUTASYON: geri cevirme kapatilinca (c) duser (raporda ham cikti)
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import UC_BANT_TEMAS_YOK_SEBEBI  # noqa: E402
import rpi_inference  # noqa: E402
from rpi_inference import analyze_path  # noqa: E402


def _dikey_koridor(boyut=640):
    zemin = np.zeros((boyut, boyut), np.uint8)
    zemin[:, 260:380] = 1
    return zemin


def _yatay_koridor(h=360, w=640):
    zemin = np.zeros((h, w), np.uint8)
    zemin[150:210, :] = 1
    return zemin


def _tam(maske, **kw):
    return analyze_path(maske, return_clean=True, return_reason=True,
                        return_olcum=True, **kw)


class RotaEkseniTests(unittest.TestCase):
    def test_a_none_bayt_es(self):
        """rota_ekseni_derece=None: cikti mevcut cekirdekle BIREBIR ayni."""
        for maske in (_dikey_koridor(), _yatay_koridor()):
            engel = np.zeros_like(maske)
            engel[:5, :5] = 1
            eski = rpi_inference._analyze_path_cekirdek(
                maske, return_clean=True, return_reason=True,
                return_olcum=True, engel_mask=engel)
            yeni = _tam(maske, engel_mask=engel)
            self.assertEqual(eski[0], yeni[0])
            self.assertEqual(eski[1], yeni[1])
            self.assertEqual(eski[2], yeni[2])
            self.assertTrue(np.array_equal(eski[3], yeni[3]))
            self.assertEqual(eski[4], yeni[4])
            self.assertEqual(eski[5], yeni[5])

    def test_a_sifir_derece_dikey_koridorda_none_ile_ayni(self):
        """0 derece = donusum yok: dikey koridorda None ile ayni karar."""
        maske = _dikey_koridor()
        a, b = _tam(maske), _tam(maske, rota_ekseni_derece=0)
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[1], b[1])
        self.assertEqual(a[2], b[2])
        self.assertTrue(np.array_equal(a[3], b[3]))

    def test_b_dikey_koridor_0_rota_90_uc_bant_yok(self):
        maske = _dikey_koridor()
        yol0, _, wp0, _, sebep0, _ = _tam(maske, rota_ekseni_derece=0)
        yol90, _, wp90, _, sebep90, _ = _tam(maske, rota_ekseni_derece=90)
        self.assertEqual(2, yol0)
        self.assertGreaterEqual(len(wp0), 2)
        self.assertIsNone(sebep0)
        self.assertIsNone(yol90)
        self.assertEqual([], wp90)
        self.assertEqual(UC_BANT_TEMAS_YOK_SEBEBI, sebep90[0])
        self.assertIn("rota ekseni 90", sebep90[1])

    def test_b_yatay_koridor_0_uc_bant_yok_90_rota(self):
        maske = _yatay_koridor()
        yol0, _, wp0, _, sebep0, _ = _tam(maske, rota_ekseni_derece=0)
        yol90, _, wp90, clean90, sebep90, olcum90 = _tam(
            maske, rota_ekseni_derece=90)
        self.assertIsNone(yol0)
        self.assertEqual(UC_BANT_TEMAS_YOK_SEBEBI, sebep0[0])
        self.assertEqual(2, yol90)
        self.assertGreaterEqual(len(wp90), 2)
        self.assertIsNone(sebep90)
        self.assertEqual(90.0, olcum90["rota_ekseni_derece"])
        # +90 = rota SOLDAN SAGA: waypoint'ler x'te artar, orijinal kare boyutu
        self.assertLess(wp90[0][0], wp90[-1][0])
        self.assertEqual(maske.shape, clean90.shape)
        # -90 = SAGDAN SOLA
        _, _, wpm, _, _, _ = _tam(maske, rota_ekseni_derece=-90)
        self.assertGreater(wpm[0][0], wpm[-1][0])

    def test_c_geri_cevrilen_waypointler_orijinal_serbest_maskede(self):
        """MADDE 15: rota pikselleri orijinal serbest maskenin icinde kalir."""
        for maske, derece in ((_yatay_koridor(), 90),
                              (_yatay_koridor(), -90),
                              (_dikey_koridor(), 180),
                              (_yatay_koridor(480, 640), 90)):
            yol, _, wps, clean, sebep, _ = _tam(maske, rota_ekseni_derece=derece)
            self.assertIsNotNone(yol, (derece, sebep))
            self.assertGreaterEqual(len(wps), 2)
            for x, y in wps:
                self.assertTrue(maske[y, x] > 0, (derece, x, y))
                self.assertTrue(clean[y, x] > 0, (derece, x, y))
            # temiz maske, DONDURULMEMIS cekirdek temizliginin (None yolu ile
            # ayni morfoloji) disina tasmaz: dondurme serbest alani buyutmez
            ref = rpi_inference._koridor_temizle(maske, None)
            self.assertEqual(0, int(np.count_nonzero(clean & (ref == 0))))

    def test_c_koseler_engel_sayilir(self):
        """Ara acida kadraja giren bos koseler serbest alan uretmez."""
        maske = np.ones((200, 300), np.uint8)
        M, _, boyut = rpi_inference._rota_ekseni_donusumu(maske.shape, 30)
        don = rpi_inference._dondur_en_yakin(maske, M, boyut)
        # tuval buyudu ama dolu piksel sayisi kaynagi asamaz (en-yakin ornekleme
        # yeni deger uretmez; koseler 0)
        self.assertLessEqual(int(don.sum()), int(maske.sum()) + boyut[0] + boyut[1])
        self.assertLess(int(don.sum()), boyut[0] * boyut[1])
        self.assertEqual(0, int(don[0, 0]))
        self.assertEqual(0, int(don[-1, -1]))

    def test_d_mutasyon_geri_cevirme_kapaninca_c_duser(self):
        """POZITIF KONTROL: geri cevirme kaldirilirsa waypoint'ler dondurulmus
        cercevede kalir ve (c) duser — testin dislemesi bos degil."""
        maske = _yatay_koridor()
        with mock.patch.object(rpi_inference, "_noktalari_geri_cevir",
                               side_effect=lambda pts, M: list(pts)):
            yol, _, wps, _, sebep, _ = _tam(maske, rota_ekseni_derece=90)
        # sarmalayici fail-closed davranir: disarida kalan waypoint -> KENAR_GUVENSIZ
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(rpi_inference.KENAR_GUVENSIZ_SEBEBI, sebep[0])


if __name__ == "__main__":
    unittest.main()
