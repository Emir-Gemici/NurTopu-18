"""NEDEN: Esik alti veya gecersiz guven tel uzerinde OPEN_ROUTE olamaz;
NO_ROUTE/DUSUK_GUVEN ACK'li gitmeli ve YKS bunu hakem onayina acmamalidir.
"""

from __future__ import annotations

import math
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for dizin in (KOK / "comms", KOK / "codes", KOK / "simulation" / "scripts"):
    if str(dizin) not in sys.path:
        sys.path.insert(0, str(dizin))

import rpi_inference
from iha_sender import IhaSender
from link import UDPLink
from protocol import FrameReader, ack, encode, open_route
from karar_sozlesmesi import DUSUK_GUVEN_SEBEBI, ROTA_GUVEN_ESIGI
import iha_perceive
import yks_gui

ESIK_ALTI = ROTA_GUVEN_ESIGI - 0.001


class _SahteLink:
    def __init__(self):
        self.sent = []

    def send(self, data, peer=None):
        self.sent.append((data, peer))

    def recv(self, bufsize=4096):
        return None, None


def _mesajlar(link):
    okuyucu = FrameReader()
    sonuc = []
    for veri, _peer in link.sent:
        sonuc.extend(okuyucu.feed(veri))
    return sonuc


class IhaSenderSonSavunmaTests(unittest.TestCase):
    def test_esik_alti_ve_gecersiz_guven_open_route_yayinlamaz(self):
        for guven in (ESIK_ALTI, 0.0, math.nan, math.inf, -math.inf,
                      -0.1, 1.1, True):
            with self.subTest(guven=guven):
                link = _SahteLink()
                sender = IhaSender(link)
                sender.send_open_route(
                    2, guven, repeat=1, interval=0.0, wait_ack=False)
                mesajlar = _mesajlar(link)
                self.assertEqual(0, sum(m["type"] == "OPEN_ROUTE" for m in mesajlar))
                self.assertEqual(1, sum(m["type"] == "NO_ROUTE" for m in mesajlar))
                self.assertEqual(DUSUK_GUVEN_SEBEBI, mesajlar[0]["sebep"])

    def test_esigin_kendisi_open_route_yayinlar(self):
        link = _SahteLink()
        sender = IhaSender(link)
        sender.send_open_route(
            2, ROTA_GUVEN_ESIGI, repeat=1, interval=0.0, wait_ack=False)
        mesajlar = _mesajlar(link)
        self.assertEqual(["OPEN_ROUTE"], [m["type"] for m in mesajlar])

    def _loopback_karari(self, guven):
        alici = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        gonderen_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        gelen = []
        dur = threading.Event()

        def dinle():
            okuyucu = FrameReader()
            while not dur.is_set():
                veri, adres = alici.recv()
                for mesaj in okuyucu.feed(veri) if veri else []:
                    gelen.append(mesaj)
                    alici.send(encode(ack(mesaj["seq"], "ika")), adres)

        is_parcacigi = threading.Thread(target=dinle, daemon=True)
        is_parcacigi.start()
        try:
            sender = IhaSender(
                gonderen_link, {"ika": ("127.0.0.1", alici.port)})
            _seq, acked = sender.send_open_route(
                2, guven, waypoints=[[0.0, 0.0], [0.0, 2.0]],
                ref_xy=[0.0, 0.0], repeat=4, interval=0.08, wait_ack=True)
            son = time.monotonic() + 1.0
            while time.monotonic() < son and not gelen:
                time.sleep(0.01)
            return acked, list(gelen)
        finally:
            dur.set()
            is_parcacigi.join(timeout=1.0)
            alici.close()
            gonderen_link.close()

    def test_gercek_udp_esik_alti_no_route_esik_open_route(self):
        acked, dusuk = self._loopback_karari(ESIK_ALTI)
        self.assertEqual({"ika"}, acked)
        self.assertTrue(dusuk)
        self.assertEqual({"NO_ROUTE"}, {m["type"] for m in dusuk})
        self.assertEqual(DUSUK_GUVEN_SEBEBI, dusuk[0]["sebep"])

        acked, sinir = self._loopback_karari(ROTA_GUVEN_ESIGI)
        self.assertEqual({"ika"}, acked)
        self.assertTrue(sinir)
        self.assertEqual({"OPEN_ROUTE"}, {m["type"] for m in sinir})


class ErkenKararYollariTests(unittest.TestCase):
    def test_rpi_esik_alti_yolu_ve_waypointleri_temizler(self):
        yol, guven, wps, ret = rpi_inference._rota_kararini_esikle(
            2, ESIK_ALTI, [(10, 20), (10, 10)])
        self.assertIsNone(yol)
        self.assertEqual(ESIK_ALTI, guven)
        self.assertEqual([], wps)
        self.assertEqual(DUSUK_GUVEN_SEBEBI, ret[0])

        yol, _guven, wps, ret = rpi_inference._rota_kararini_esikle(
            2, ROTA_GUVEN_ESIGI, [(10, 20), (10, 10)])
        self.assertEqual(2, yol)
        self.assertTrue(wps)
        self.assertIsNone(ret)

    def test_iha_perceive_esik_altini_nedeniyle_reddeder(self):
        zemin = np.ones((64, 64), np.uint8)
        maskeler = {0: zemin, 1: np.zeros_like(zemin)}

        class Model:
            def predict(self, *args, **kwargs):
                return object()

        with mock.patch.object(rpi_inference, "get_masks", return_value=maskeler), \
             mock.patch.object(rpi_inference, "is_dark", return_value=False), \
             mock.patch.object(
                 rpi_inference, "analyze_path",
                 return_value=(2, ESIK_ALTI, [(32, 60), (32, 4)], None)) as analiz:
            sonuc = iha_perceive._infer(
                np.zeros((64, 64, 3), np.uint8), Model(), 0.15, 64,
                return_reason=True)

        analiz.assert_called_once()
        analiz_args, analiz_kwargs = analiz.call_args
        np.testing.assert_array_equal(maskeler[0], analiz_args[0])
        np.testing.assert_array_equal(maskeler[1], analiz_kwargs["engel_mask"])
        self.assertIs(True, analiz_kwargs["return_reason"])

        _icerik, _maskeler, yol, guven, wps, _kip, ret = sonuc
        self.assertIsNone(yol)
        self.assertEqual(ESIK_ALTI, guven)
        self.assertEqual([], wps)
        self.assertEqual(DUSUK_GUVEN_SEBEBI, ret[0])


class _Widget:
    def __init__(self):
        self.son = {}

    def config(self, **kwargs):
        self.son.update(kwargs)


class YksGuvenKapisiTests(unittest.TestCase):
    def _gui(self):
        gui = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
        gui.link = _SahteLink()
        gui.rota = None
        gui.rota_yok = None
        gui.rota_adr = None
        gui.rx_alim = {}
        gui.onaylandi = False
        gui.tespit_onayli = False
        gui.otomatik_onay = False
        gui.t_iha1 = None
        gui.sayac = {"OPEN_ROUTE": 0, "OPEN_ROUTE_RED": 0, "NO_ROUTE": 0,
                     "IHA_LANDED": 0, "HEARTBEAT": 0, "ACK_TX": 0}
        gui.lbl_karar = _Widget()
        gui.lbl_detay = _Widget()
        gui.btn_onay = _Widget()
        gui.lbl_onay = _Widget()
        gui._dugum_adresini_ogren = lambda *_a: None
        gui._guven_ciz = lambda *_a: None
        gui._harita_ciz = lambda: None
        gui._zincir = lambda *_a: None
        gui._rota_analiz = lambda *_a: None
        gui._loglar = []
        gui._logla = lambda metin, renk="soluk": gui._loglar.append((renk, metin))
        return gui

    def test_dusuk_guven_onaya_acilmaz_ve_ack_uretmez(self):
        gui = self._gui()
        onceki = open_route(
            2, ROTA_GUVEN_ESIGI, [[0.0, 0.0]], [0.0, 0.0], seq=2500)
        gui._mesaj_isle(onceki, ("127.0.0.1", 5000))
        mesaj = open_route(
            2, ESIK_ALTI, [[0.0, 0.0]], [0.0, 0.0], seq=2501)

        gui._mesaj_isle(mesaj, ("127.0.0.1", 5000))
        gui.onayla()
        gui.onayla()

        self.assertEqual(2500, gui.rota["seq"])
        self.assertEqual(DUSUK_GUVEN_SEBEBI, gui.rota_yok["sebep"])
        self.assertEqual("disabled", gui.btn_onay.son["state"])
        self.assertEqual(1, gui.sayac["OPEN_ROUTE_RED"])
        self.assertEqual([], gui.link.sent)
        self.assertTrue(any("ACK YOK" in metin for _renk, metin in gui._loglar))

    def test_esik_degeri_normal_open_route_akisini_korur(self):
        gui = self._gui()
        mesaj = open_route(
            2, ROTA_GUVEN_ESIGI, [[0.0, 0.0]], [0.0, 0.0], seq=2502)

        gui._mesaj_isle(mesaj, ("127.0.0.1", 5000))

        self.assertEqual(2502, gui.rota["seq"])
        self.assertIsNone(gui.rota_yok)
        self.assertEqual("normal", gui.btn_onay.son["state"])

    def test_esigin_hemen_alti_serilestirmede_yukariya_yuvarlanmaz(self):
        gui = self._gui()
        hemen_alti = math.nextafter(ROTA_GUVEN_ESIGI, -math.inf)
        tel = encode(open_route(
            2, hemen_alti, [[0.0, 0.0]], [0.0, 0.0], seq=2503))
        [mesaj] = FrameReader().feed(tel)

        self.assertLess(mesaj["conf"], ROTA_GUVEN_ESIGI)
        gui._mesaj_isle(mesaj, ("127.0.0.1", 5000))
        self.assertIsNone(gui.rota)
        self.assertEqual(DUSUK_GUVEN_SEBEBI, gui.rota_yok["sebep"])
        self.assertEqual([], gui.link.sent)


if __name__ == "__main__":
    unittest.main(verbosity=2)
