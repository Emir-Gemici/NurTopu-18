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
    # T155: YAYINLANAN alan; sahte olcum de tasimak zorunda.
    "serit_karari": 2,
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

        # T36: GUI artik kendi `n_waypoints`ini SECMIYOR; uretim varsayilani
        # (`analyze_path` imzasi) gecerli. Kiyas da onunla yapilir.
        eski = rpi_inference.analyze_path(oyulmus)
        yeni = rpi_inference.analyze_path(oyulmus, engel_mask=bariyer)

        self.assertEqual(2, eski[0])
        self.assertIsNone(yeni[0])
        self.assertEqual([], yeni[2])

    def test_gui_ham_engeli_analyze_path_son_kapisina_baglar(self):
        zemin, arac = _aracli_koridor()
        once = zemin.copy()
        once[arac > 0] = 0
        eski = rpi_inference.analyze_path(
            once, return_clean=True)
        self.assertEqual(2, eski[0])
        self.assertGreater(_kenar_arac_kesisimi(eski[2], arac), 0)

        cagri = []
        gercek_analyze = rpi_inference.analyze_path

        def analyze_sarmal(*args, **kwargs):
            sonuc = gercek_analyze(*args, **kwargs)
            cagri.append((args, kwargs, sonuc))
            return sonuc

        def maskeler(_sonuc, _h, _w, min_conf=None):
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
        # T36: GUI kendi `n_waypoints`ini SECMEZ; uretim varsayilani gecerli.
        self.assertNotIn(
            "n_waypoints", kwargs,
            "GUI hala kendi ornekleme sayisini dayatiyor (T36 ihlali)")
        # T35 sozlesmesi: letterbox icerik kutusu MUTLAKA gecirilir.
        self.assertIn("icerik", kwargs)
        self.assertEqual(4, len(kwargs["icerik"]))
        # D-40'in kok nedeni: HAM engel maskesi son kapiya baglanmali. Maske
        # artik dolgu kirpmasindan gectigi icin bire bir esitlik yerine
        # "arac pikselleri engel maskesinde duruyor mu" olculur.
        self.assertIsNotNone(kwargs["engel_mask"])
        self.assertGreater(int(np.count_nonzero(kwargs["engel_mask"])), 0)
        self.assertEqual(0, int((sonuc[3][arac > 0] > 0).sum()))
        self.assertTrue(
            sonuc[0] is None or _kenar_arac_kesisimi(sonuc[2], arac) == 0
        )
        self.assertTrue(any(kayit[0] == "sonuc" for kayit in list(gui.algi_kuyruk.queue)))

    def test_gui_uretimin_waypointlerini_DEGISTIRMEDEN_yayinlar(self):
        """T36: GUI artik rotayi kendi bolmuyor — ekran uretimi gosterir.

        Eski davranis (`_maks_aralikla_bol` ile ara dugum ekleme) KALDIRILDI:
        hakem ekrani telde gidenden farkli bir polyline gosteremez. Kaldirmanin
        olculmus bedeli yok — 67 gercek karenin 57'sinde karar uretiliyor ve
        uretimin kendi azami kenari tuval yuksekliginin p50 %6,8 / maks %7,7'si
        (eski GUI siniri 1/12 = %8,3). Sinirı asan kare: 0/57.
        """
        zemin, arac = _aracli_koridor()
        gorulen = {}
        gercek_analyze = rpi_inference.analyze_path

        def analyze_sarmal(*args, **kwargs):
            sonuc = gercek_analyze(*args, **kwargs)
            gorulen["wps"] = list(sonuc[2])
            return sonuc

        def maskeler(_sonuc, _h, _w, min_conf=None):
            return {0: zemin.copy(), 1: arac.copy()}

        gui = _gui()
        goruntu = np.zeros((640, 640, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu),              mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler),              mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=analyze_sarmal):
            gui._algi_kos(Path("aracli.jpg"))

        # `_maks_aralikla_bol`u `analyze_path` KENDI icinde mesru olarak
        # kullanir (`_rotayi_ornekle`). Olculecek sey onun cagrilip
        # cagrilmadigi degil, GUI GOVDESININ rotaya dokunup dokunmadigidir.
        govde = (KOK / "comms" / "yks_gui.py").read_text(
            encoding="utf-8").split("def _algi_kos", 1)[1].split(
                "def _algi_sonucu_goster", 1)[0]
        for yasak in ("_maks_aralikla_bol", "MAKS_WP", "_kenarlar_guvenli"):
            self.assertNotIn(
                yasak, govde,
                f"GUI hala rotayi kendi isliyor: {yasak}")
        self.assertTrue(
            any(k[0] == "sonuc" for k in list(gui.algi_kuyruk.queue)))
        self.assertIn("wps", gorulen)

    def test_panoramik_kare_worker_i_dusurmez(self):
        """Dayaniklilik: cok genis kare + tam gecilebilir maske.

        Tamami gecilebilir maskede `distanceTransform` FLT_MAX dondurebiliyor
        ve `int(medyan)` cizgi kalinligina cevrilince worker sessizce
        dusuyordu (D-41). Kapi, sonuc paketinin GERCEKTEN yazildigini kilitler.
        """
        h, w = 128, 1024
        zemin = np.ones((h, w), np.uint8)
        arac = np.zeros_like(zemin)

        def maskeler(_sonuc, _h, _w, min_conf=None):
            yan = max(_h, _w)
            z = np.zeros((yan, yan), np.uint8)
            a = np.zeros((yan, yan), np.uint8)
            y0, x0 = (yan - h) // 2, (yan - w) // 2
            z[y0:y0 + h, x0:x0 + w] = zemin
            a[y0:y0 + h, x0:x0 + w] = arac
            return {0: z, 1: a}

        gui = _gui()
        goruntu = np.zeros((h, w, 3), np.uint8)
        with mock.patch.object(cv2, "imread", return_value=goruntu),              mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler):
            gui._algi_kos(Path("panorama.jpg"))

        paketler = list(gui.algi_kuyruk.queue)
        self.assertFalse(any(p[0] == "hata" for p in paketler), paketler)
        self.assertTrue(any(p[0] == "sonuc" for p in paketler))

    def test_gecersiz_guven_gosterimi_worker_i_dusurmez(self):
        zemin = np.ones((128, 128), np.uint8)
        arac = np.zeros_like(zemin)
        goruntu = np.zeros((128, 128, 3), np.uint8)

        def maskeler(_sonuc, _h, _w, min_conf=None):
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
