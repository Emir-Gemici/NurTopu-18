"""YKS algi gorunumunun arac maskesini rota kenarlarinda koruma kapisi.

NEDEN: GUI araci MORPH_CLOSE oncesi zeminden oyup ham engel maskesini
``analyze_path``'e vermiyordu. Ince arac boslugu geri doluyor, sari waypoint
kenari modelin dogru etiketledigi aracin ustunden gecebiliyordu.
"""

from __future__ import annotations

import queue
import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for dizin in (KOK / "comms", KOK / "codes"):
    if str(dizin) not in sys.path:
        sys.path.insert(0, str(dizin))

import costmap_path_finder
import rpi_inference
import yks_gui


def _aracli_koridor():
    zemin = np.zeros((640, 640), np.uint8)
    zemin[:, 260:380] = 1
    arac = np.zeros_like(zemin)
    arac[300:307, 290:350] = 1
    return zemin, arac


def _kenar_arac_kesisimi(waypoints, arac):
    toplam = 0
    for bas, son in zip(waypoints, waypoints[1:]):
        cizgi = np.zeros_like(arac)
        cv2.line(cizgi, bas, son, 1, 1, cv2.LINE_8)
        toplam += int(((cizgi > 0) & (arac > 0)).sum())
    return toplam


class _Model:
    def predict(self, *_args, **_kwargs):
        return object()


# T31/T32 (D-41): `analyze_path` artik `return_olcum=True` ile ALTINCI eleman
# dondurur ve GUI onu ekrana basar. Sahte analizorlerin de ayni ariteyi
# tasimasi gerekir — yoksa test uretim sozlesmesinden sessizce ayrisir.
_SAHTE_OLCUM = {
    "darbogaz_serit": 2,
    "baskin_serit": 2,
    "seritler": (0, 120, 0),
    "darbogaz_px": 24.0,
    "darbogaz_xy": (64, 64),
    "serit_min_px": (None, 24.0, None),
    "cok_seritli": False,
    "rota_px": 120,
}

def _gui():
    gui = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
    gui.algi_model = _Model()
    gui.algi_kuyruk = queue.Queue()
    gui.algi_mesgul = True
    gui.algi_kaynak = "test"
    return gui


class YksGuiAracEngeliTests(unittest.TestCase):
    def test_ince_tam_bariyer_morfolojiyle_acik_yola_donmez(self):
        zemin = np.zeros((640, 640), np.uint8)
        zemin[:, 260:380] = 1
        bariyer = np.zeros_like(zemin)
        bariyer[300:307, 260:380] = 1
        oyulmus = zemin.copy()
        oyulmus[bariyer > 0] = 0

        eski = rpi_inference.analyze_path(
            oyulmus,
            n_waypoints=yks_gui.YksArayuz.ALGI_WAYPOINT_BANT_SAYISI,
        )
        yeni = rpi_inference.analyze_path(
            oyulmus,
            n_waypoints=yks_gui.YksArayuz.ALGI_WAYPOINT_BANT_SAYISI,
            engel_mask=bariyer,
        )

        self.assertEqual(2, eski[0])
        self.assertIsNone(yeni[0])
        self.assertEqual([], yeni[2])

    def test_gui_ham_engeli_analyze_path_son_kapisina_baglar(self):
        zemin, arac = _aracli_koridor()
        once = zemin.copy()
        once[arac > 0] = 0
        eski = rpi_inference.analyze_path(
            once,
            n_waypoints=yks_gui.YksArayuz.ALGI_WAYPOINT_BANT_SAYISI,
            return_clean=True,
            min_area_ratio=0.02,
        )
        self.assertEqual(2, eski[0])
        self.assertGreater(_kenar_arac_kesisimi(eski[2], arac), 0)

        cagri = []
        gercek_analyze = rpi_inference.analyze_path

        def analyze_sarmal(*args, **kwargs):
            sonuc = gercek_analyze(*args, **kwargs)
            cagri.append((args, kwargs, sonuc))
            return sonuc

        def maskeler(_sonuc, _h, _w, min_conf):
            if min_conf == 0.10:
                return {0: zemin.copy(), 1: arac.copy()}
            return {0: zemin.copy(), 1: arac.copy()}

        gui = _gui()
        goruntu = np.zeros((640, 640, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu), \
             mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler), \
             mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=analyze_sarmal):
            gui._algi_kos(Path("aracli.jpg"))

        self.assertEqual(1, len(cagri))
        _args, kwargs, sonuc = cagri[0]
        self.assertEqual(
            yks_gui.YksArayuz.ALGI_WAYPOINT_BANT_SAYISI,
            kwargs["n_waypoints"],
        )
        self.assertEqual(8, kwargs["n_waypoints"])
        self.assertTrue(np.array_equal(zemin, _args[0]))
        self.assertTrue(np.array_equal(arac, kwargs["engel_mask"]))
        self.assertEqual(0, int((sonuc[3][arac > 0] > 0).sum()))
        self.assertTrue(
            sonuc[0] is None or _kenar_arac_kesisimi(sonuc[2], arac) == 0
        )
        self.assertTrue(any(kayit[0] == "sonuc" for kayit in list(gui.algi_kuyruk.queue)))

    def test_gui_uzun_guvenli_kenari_ara_noktalarla_boler(self):
        zemin = np.ones((640, 640), np.uint8)
        arac = np.zeros_like(zemin)
        uzun_yol = [(40, 600), (600, 40)]
        bolme_cagrisi = []
        gercek_bol = costmap_path_finder._maks_aralikla_bol

        def analyze_sahte(*_args, **_kwargs):
            return 2, 1.0, list(uzun_yol), zemin.copy(), None, _SAHTE_OLCUM

        def bol_sarmal(*args, **kwargs):
            sonuc = gercek_bol(*args, **kwargs)
            bolme_cagrisi.append((args, sonuc))
            return sonuc

        def maskeler(_sonuc, _h, _w, min_conf):
            del min_conf
            return {0: zemin.copy(), 1: arac.copy()}

        gui = _gui()
        goruntu = np.zeros((640, 640, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu), \
             mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler), \
             mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=analyze_sahte), \
             mock.patch.object(costmap_path_finder, "_maks_aralikla_bol",
                               side_effect=bol_sarmal):
            gui._algi_kos(Path("uzun.jpg"))

        self.assertEqual(1, len(bolme_cagrisi))
        args, bolunmus = bolme_cagrisi[0]
        maks_kenar = float(args[1])
        self.assertAlmostEqual(
            640 * yks_gui.YksArayuz.ALGI_MAKS_KENAR_ORANI,
            maks_kenar,
        )
        self.assertGreater(len(bolunmus), len(uzun_yol))
        for bas, son in zip(bolunmus, bolunmus[1:]):
            self.assertLessEqual(
                float(np.hypot(son[0] - bas[0], son[1] - bas[1])),
                maks_kenar + 1e-9,
            )
        # Tam-gecilebilir maske distanceTransform'da FLT_MAX uretebiliyordu;
        # bolme cagrisi yapilsa bile render asamasinda worker cokup sonuc
        # kuyruga hic yazilmayabiliyordu. Test gercek sonuc paketini kilitler.
        self.assertTrue(
            any(kayit[0] == "sonuc" for kayit in list(gui.algi_kuyruk.queue))
        )

    def test_kalin_sari_cizgi_arac_etiketinin_ustunu_boyamaz(self):
        zemin = np.ones((640, 640), np.uint8)
        arac = np.zeros_like(zemin)
        arac[240:400, 301:305] = 1
        yol = [(300, 600), (300, 40)]

        def analyze_sahte(*_args, **_kwargs):
            clean = zemin.copy()
            clean[arac > 0] = 0
            return 2, 1.0, list(yol), clean, None, _SAHTE_OLCUM

        def maskeler(_sonuc, _h, _w, min_conf):
            del min_conf
            return {0: zemin.copy(), 1: arac.copy()}

        # Pozitif kontrol: GUI'nin sari kalinlik/circle ayari araca tasar.
        sari = np.zeros((640, 640), np.uint8)
        cv2.polylines(sari, [np.array(yol, np.int32)], False, 1, thickness=2)
        for nokta in yol:
            cv2.circle(sari, nokta, 4, 1, -1)
        self.assertGreater(int(sari[arac > 0].sum()), 0)

        gui = _gui()
        goruntu = np.zeros((640, 640, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu), \
             mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler), \
             mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=analyze_sahte):
            gui._algi_kos(Path("yakin.jpg"))

        sonuc = next(k for k in list(gui.algi_kuyruk.queue) if k[0] == "sonuc")
        gorsel = sonuc[1]
        sari_piksel = np.all(gorsel == np.array([0, 220, 255]), axis=2)
        self.assertEqual(0, int(sari_piksel[arac > 0].sum()))

    def test_panoramik_rotada_waypoint_siniri_worker_i_dusurmez(self):
        h, w = 100, 1399
        zemin = np.ones((h, w), np.uint8)
        arac = np.zeros_like(zemin)
        uzun_yol = [(10, 90), (w - 10, 10)]

        def analyze_sahte(*_args, **_kwargs):
            return 2, 1.0, list(uzun_yol), zemin.copy(), None, _SAHTE_OLCUM

        def maskeler(_sonuc, _h, _w, min_conf):
            del min_conf
            return {0: zemin.copy(), 1: arac.copy()}

        dogrulanan_wps = []
        gercek_kenar_kapisi = rpi_inference._kenarlar_guvenli

        def kenar_kapisi_sarmal(waypoints, *args, **kwargs):
            dogrulanan_wps.append(list(waypoints))
            return gercek_kenar_kapisi(waypoints, *args, **kwargs)

        gui = _gui()
        goruntu = np.zeros((h, w, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu), \
             mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler), \
             mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=analyze_sahte), \
             mock.patch.object(rpi_inference, "_kenarlar_guvenli",
                               side_effect=kenar_kapisi_sarmal):
            gui._algi_kos(Path("panorama.jpg"))

        paketler = list(gui.algi_kuyruk.queue)
        self.assertFalse(any(p[0] == "hata" for p in paketler))
        sonuc = next(p for p in paketler if p[0] == "sonuc")
        # Gorsel uzerindeki sari dugumleri saymak yerine planlayicinin hard
        # sinirini, ayni geometriyle yardimci seviyesinde de kilitle.
        hedef = max(1.0, h * yks_gui.YksArayuz.ALGI_MAKS_KENAR_ORANI)
        hedef_adim = max(1, int(np.floor(hedef / np.sqrt(2.0))))
        gereken = 1 + int(np.ceil((w - 20) / hedef_adim))
        self.assertGreater(gereken, costmap_path_finder.MAKS_WP)
        self.assertEqual(1, len(dogrulanan_wps))
        self.assertLessEqual(
            len(dogrulanan_wps[0]), costmap_path_finder.MAKS_WP
        )
        self.assertEqual("sonuc", sonuc[0])

    def test_gecersiz_guven_gosterimi_worker_i_dusurmez(self):
        zemin = np.ones((128, 128), np.uint8)
        arac = np.zeros_like(zemin)
        goruntu = np.zeros((128, 128, 3), np.uint8)

        def maskeler(_sonuc, _h, _w, min_conf):
            del min_conf
            return {0: zemin.copy(), 1: arac.copy()}

        for gecersiz in (None, "0.9"):
            with self.subTest(guven=gecersiz):
                def analyze_sahte(*_args, **_kwargs):
                    return (2, gecersiz, [(64, 120), (64, 8)],
                            zemin.copy(), None, _SAHTE_OLCUM)

                gui = _gui()
                with mock.patch.object(cv2, "imread", return_value=goruntu), \
                     mock.patch.object(rpi_inference, "get_masks",
                                       side_effect=maskeler), \
                     mock.patch.object(rpi_inference, "analyze_path",
                                       side_effect=analyze_sahte):
                    gui._algi_kos(Path("gecersiz-guven.jpg"))

                paketler = list(gui.algi_kuyruk.queue)
                self.assertTrue(any(p[0] == "sonuc" for p in paketler))
                self.assertFalse(any(p[0] == "hata" for p in paketler))

    def test_worker_hatasi_panel_icin_ayri_paket_uretir(self):
        gui = _gui()
        with mock.patch.object(cv2, "imread", return_value=None):
            gui._algi_kos(Path("okunamayan.jpg"))

        paketler = list(gui.algi_kuyruk.queue)
        hata = next(p for p in paketler if p[0] == "hata")
        self.assertIn("ALGI HATASI", hata[1])
        self.assertIn("AttributeError", hata[1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
