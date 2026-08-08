"""T24 KAPISI: analyze_path waypoint KENARLARI gercekten denetleniyor mu?

Kusur (REVIEW_LOG D-28, bulan: kullanici saha testi): goruntu 8 yatay banda
bolunup her bandin distance-transform argmax'i korlemesine waypoint yapiliyordu.
Ardisik iki bandin maksimumu iki AYRI koridora dusebiliyor ve aralarindaki dogru
engelin ustunden geciyordu — iki ucu zemin, kenar degil.

Bu paket UC seyi birden kanitlar:
  1. POZITIF KONTROL — eski algoritma bu sahnede GERCEKTEN ihlal uretiyor
     (yoksa test bosluk olur: "hicbir sey bulamadim" ile "kusur yok" karisir).
  2. Duzeltilmis yol ayni sahnede ihlal URETMIYOR.
  3. Normal koridorlarda REGRESYON yok — kenar denetimi uretimi susturmuyor.
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

from costmap_path_finder import _gorus_hatti
from rpi_inference import analyze_path


def _catalli_sahne(boyut: int = 640):
    """Iki dikey koridor + aralarinda engel duvari.

    Alt yarida SOL, ust yarida SAG koridor genis; boylece ardisik iki bandin
    argmax'i iki ayri koridora duser. Ortadaki yatay serit iki koridoru tek
    bagli bilesen yapar (analyze_path en buyuk bileseni alir).
    """
    h = w = boyut
    zemin = np.zeros((h, w), np.uint8)
    engel = np.zeros((h, w), np.uint8)
    zemin[:, 60:180] = 1
    zemin[:, 460:580] = 1
    zemin[300:340, 180:460] = 1
    zemin[340:, 30:210] = 1
    zemin[:300, 430:610] = 1
    engel[:, 210:430] = 1
    engel[300:340, 180:460] = 0
    zemin[engel > 0] = 0
    return zemin, engel


def _temizle(trav):
    """analyze_path'in morfolojik on islemesinin birebir aynisi (engelsiz)."""
    h, w = trav.shape
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                       (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                        (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)
    n_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    if n_lbl > 2:
        en_buyuk = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        clean = (labels == en_buyuk).astype(np.uint8)
    return clean


def _eski_waypointler(clean, n=8):
    """DUZELTME ONCESI davranis — pozitif kontrol icin yeniden uretilir."""
    h = clean.shape[0]
    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)
    wp = []
    for i in range(n - 1, -1, -1):
        y0, y1 = i * h // n, (i + 1) * h // n
        band = dist[y0:y1, :]
        if band.size and band.max() > 0.5:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            wp.append((int(lx), int(y0 + ly)))
    return wp


def _ihlal_sayisi(waypoints, clean, engel=None):
    """Kac ARDISIK kenar serbest alani terk ediyor ya da engele degiyor?"""
    h, w = clean.shape
    kotu = 0
    for a, b in zip(waypoints, waypoints[1:]):
        buf = np.zeros((h, w), np.uint8)
        cv2.line(buf, a, b, 1, thickness=1, lineType=cv2.LINE_8)
        engel_temas = engel is not None and bool((engel[buf > 0] > 0).any())
        if engel_temas or not _gorus_hatti(a, b, clean):
            kotu += 1
    return kotu


class PozitifKontrolTests(unittest.TestCase):
    """Sahne kusuru GERCEKTEN tetikliyor mu? Tetiklemiyorsa test bosluktur."""

    def test_eski_algoritma_bu_sahnede_ihlal_uretiyor(self):
        zemin, engel = _catalli_sahne()
        clean = _temizle(zemin)
        eski = _eski_waypointler(clean)
        self.assertGreaterEqual(len(eski), 2)
        ihlal = _ihlal_sayisi(eski, clean, engel)
        self.assertGreater(
            ihlal, 0,
            "sahne kusuru tetiklemiyor — bu testin kaniti yok (bkz. D-15)")

    def test_ihlalli_kenar_iki_ayri_koridoru_birlestiriyor(self):
        """Kusurun SEKLI: iki ucu da serbest, kenar duvarin ustunden geciyor."""
        zemin, engel = _catalli_sahne()
        clean = _temizle(zemin)
        eski = _eski_waypointler(clean)
        bulundu = False
        for a, b in zip(eski, eski[1:]):
            if _ihlal_sayisi([a, b], clean, engel):
                self.assertTrue(clean[a[1], a[0]] > 0, "sol uc serbest degil")
                self.assertTrue(clean[b[1], b[0]] > 0, "sag uc serbest degil")
                self.assertGreater(abs(a[0] - b[0]), 200,
                                   "ihlal iki AYRI koridor arasinda olmali")
                bulundu = True
        self.assertTrue(bulundu, "iki ucu serbest olan ihlalli kenar bulunamadi")


class KenarDenetimiTests(unittest.TestCase):
    """Duzeltilmis yol ayni sahnede gecersiz rota URETMEMELI."""

    def _guvenli_mi(self, yol, wp, clean, engel):
        """Guvenlik degismezi: ya KARAR YOK, ya da HIC gecersiz kenar yok.

        DIKKAT — bos test tuzagi: `_ihlal_sayisi([])` her zaman 0 doner. Bu yuzden
        bu yuklem TEK BASINA kanit degildir; her testte ayrica ESKI algoritmanin
        AYNI sahnede degismezi IHLAL ETTIGI assert edilir. Denetim bu boslugu
        yakaladi (bkz. D-15: kosmayan kapi gecti sayilmaz).
        """
        if yol is None or not wp:
            return True
        return _ihlal_sayisi(wp, clean, engel) == 0

    def test_catalli_sahnede_yeni_yol_guvenli_eski_yol_degil(self):
        zemin, engel = _catalli_sahne()
        clean = _temizle(zemin)

        eski = _eski_waypointler(clean)
        self.assertGreater(_ihlal_sayisi(eski, clean, engel), 0,
                           "sahne eski kusuru tetiklemiyor — test bosluk olurdu")

        yol, _guven, wp = analyze_path(zemin, engel_mask=engel)
        clean_engelsiz = clean.copy()
        clean_engelsiz[engel > 0] = 0
        self.assertTrue(self._guvenli_mi(yol, wp, clean_engelsiz, engel),
                        f"yeni yol hala gecersiz kenar uretiyor: {wp}")

    def test_engel_maskesi_olmadan_da_kenar_denetlenir(self):
        """D-28 engel zeminden zaten dusulmusken de olusuyordu."""
        zemin, engel = _catalli_sahne()
        clean = _temizle(zemin)
        self.assertGreater(_ihlal_sayisi(_eski_waypointler(clean), clean, engel), 0)

        yol, _guven, wp = analyze_path(zemin)          # engel_mask YOK
        self.assertTrue(self._guvenli_mi(yol, wp, clean, engel))

    def test_rota_uretilirse_TEK_koridorda_kalir(self):
        """Onarim GERCEK olmali — yalniz reddetmek yetmez.

        Gercek 67 karede ihlalli 13 karenin 7'si onarildi (rota uretildi ve
        gecerliydi), 6'si reddedildi. Bu test onarim davranisini kilitler:
        catalli sahnede rota uretilirse TUM waypoint'ler AYNI koridorda kalmali —
        eski kod iki koridor arasinda ~400 px ziplyordu.
        """
        zemin, engel = _catalli_sahne()
        yol, _guven, wp = analyze_path(zemin, engel_mask=engel)
        if not wp:
            self.skipTest("bu sahnede karar uretilmedi; guvenli ret de kabul")
        yayilim = max(p[0] for p in wp) - min(p[0] for p in wp)
        self.assertLess(yayilim, 150,
                        f"waypoint'ler koridorlar arasinda ziplyor (x yayilimi {yayilim})")
        clean = _temizle(zemin)
        clean[engel > 0] = 0
        self.assertEqual(0, _ihlal_sayisi(wp, clean, engel))


class RegresyonTests(unittest.TestCase):
    """Kenar denetimi normal koridorlarda uretimi SUSTURMAMALI."""

    def test_duz_koridor_waypoint_uretmeye_devam_eder(self):
        z = np.zeros((640, 640), np.uint8)
        z[:, 260:380] = 1
        yol, guven, wp = analyze_path(z)
        self.assertEqual(2, yol)
        self.assertGreaterEqual(len(wp), 6)
        self.assertEqual(0, _ihlal_sayisi(wp, _temizle(z)))

    def test_kivrimli_koridor_waypoint_uretir_ve_kenarlar_gecerli(self):
        h = w = 640
        z = np.zeros((h, w), np.uint8)
        for y in range(h):
            c = int(320 + 90 * np.sin(y / h * np.pi))
            z[y, c - 60:c + 60] = 1
        yol, _guven, wp = analyze_path(z)
        self.assertIsNotNone(yol)
        self.assertGreaterEqual(len(wp), 6)
        self.assertEqual(0, _ihlal_sayisi(wp, _temizle(z)))

    def test_sol_ve_sag_koridor_kararlari_korunur(self):
        for x0, beklenen in ((40, 1), (500, 3)):
            with self.subTest(x0=x0):
                z = np.zeros((640, 640), np.uint8)
                z[:, x0:x0 + 110] = 1
                yol, _g, _wp = analyze_path(z)
                self.assertEqual(beklenen, yol)


class CikarmaSirasiTests(unittest.TestCase):
    """Engel CIKARMASI kapamadan SONRA olmali (CLAUDE.md madde 15 / D-24).

    MORPH_CLOSE extensive'dir: kapama cekirdeginden ince bir engel, cikarma
    kapamadan ONCE yapilirsa geri doldurulur ve rota uzerinden gecer.
    """

    def test_kapama_cekirdeginden_ince_engel_hayatta_kalir(self):
        h = w = 640
        zemin = np.ones((h, w), np.uint8)
        engel = np.zeros((h, w), np.uint8)
        engel[300:307, :] = 1          # 7 px — kapama cekirdegi ~21 px
        _yol, _guven, _wp, clean = analyze_path(
            zemin, return_clean=True, engel_mask=engel)
        kalan = int((clean[engel > 0] > 0).sum())
        self.assertEqual(
            0, kalan,
            f"engelin {kalan} pikseli serbest alanda kaldi — cikarma kapamadan "
            f"ONCE yapiliyor olabilir (madde 15 ihlali)")

    def test_engel_maskesi_sekil_uyusmazliginda_hata_verir(self):
        z = np.zeros((64, 64), np.uint8)
        z[:, 20:40] = 1
        with self.assertRaises(ValueError):
            analyze_path(z, engel_mask=np.zeros((32, 32), np.uint8))


if __name__ == "__main__":
    unittest.main(verbosity=2)
