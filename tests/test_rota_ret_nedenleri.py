"""T25/T28 kapisi: rota reddi hakeme kanonik ve ayirt edilebilir bildirilir."""

from __future__ import annotations

import queue
import sys
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for dizin in (KOK / "codes", KOK / "comms", KOK / "simulation" / "scripts"):
    if str(dizin) not in sys.path:
        sys.path.insert(0, str(dizin))

import iha_perceive
import rpi_inference
import yks_gui
from iha_sender import IhaSender
from protocol import FrameReader
from karar_sozlesmesi import (
    ALAN_YETERSIZ_SEBEBI,
    BILESEN_YOK_SEBEBI,
    DUSUK_GUVEN_SEBEBI,
    GORUS_HATTI_KOPUK_SEBEBI,
    KENAR_GUVENSIZ_SEBEBI,
    MASKE_YOK_SEBEBI,
    ROTA_GUVEN_ESIGI,
    ROTA_RET_SEBEPLERI,
    UC_BANT_TEMAS_YOK_SEBEBI,
)


def _duz_koridor(boyut=128, x0=40, x1=88):
    zemin = np.zeros((boyut, boyut), np.uint8)
    zemin[:, x0:x1] = 1
    return zemin


class AnalyzePathRetNedeniTests(unittest.TestCase):
    def test_sebep_kodlari_sozlesmedeki_yedi_degerdir(self):
        self.assertEqual({
            MASKE_YOK_SEBEBI,
            BILESEN_YOK_SEBEBI,
            UC_BANT_TEMAS_YOK_SEBEBI,
            ALAN_YETERSIZ_SEBEBI,
            GORUS_HATTI_KOPUK_SEBEBI,
            KENAR_GUVENSIZ_SEBEBI,
            DUSUK_GUVEN_SEBEBI,
        }, set(ROTA_RET_SEBEPLERI))

    def test_varsayilan_ve_opt_in_tuple_ariteleri_korunur(self):
        zemin = _duz_koridor()

        varsayilan = rpi_inference.analyze_path(zemin)
        temiz = rpi_inference.analyze_path(zemin, return_clean=True)
        nedenli = rpi_inference.analyze_path(zemin, return_reason=True)
        ikisi = rpi_inference.analyze_path(
            zemin, return_clean=True, return_reason=True)

        self.assertEqual(3, len(varsayilan))
        self.assertEqual(4, len(temiz))
        self.assertIsInstance(temiz[3], np.ndarray)
        self.assertEqual(4, len(nedenli))
        self.assertIsNone(nedenli[3])
        self.assertEqual(5, len(ikisi))
        self.assertIsInstance(ikisi[3], np.ndarray)
        self.assertIsNone(ikisi[4])
        self.assertEqual(varsayilan[:3], temiz[:3])
        self.assertEqual(varsayilan[:3], nedenli[:3])

    def test_maske_yok_ve_bilesen_yok_ayridir(self):
        bos = np.zeros((128, 128), np.uint8)
        yol, guven, wps, ret = rpi_inference.analyze_path(
            bos, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps)
        self.assertEqual(MASKE_YOK_SEBEBI, ret[0])
        self.assertIn("0 piksel", ret[1])

        seyrek = np.zeros_like(bos)
        seyrek[64, 64] = 1  # MORPH_OPEN sonrasi bilesen kalmaz
        yol, guven, wps, ret = rpi_inference.analyze_path(
            seyrek, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps)
        self.assertEqual(BILESEN_YOK_SEBEBI, ret[0])
        self.assertIn("1 piksel", ret[1])

    def test_engel_zeminin_tamamini_orterse_maske_yok_denmez(self):
        zemin = np.ones((128, 128), np.uint8)
        engel = np.ones_like(zemin)
        yol, _guven, wps, ret = rpi_inference.analyze_path(
            zemin, engel_mask=engel, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(BILESEN_YOK_SEBEBI, ret[0])

    def test_uc_bant_alan_gorus_ve_kenar_reti_olculu_detay_tasir(self):
        zemin = _duz_koridor()
        engel = np.zeros_like(zemin)
        engel[60:68, 40:88] = 1
        yol, _guven, wps, ret = rpi_inference.analyze_path(
            zemin, engel_mask=engel, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(UC_BANT_TEMAS_YOK_SEBEBI, ret[0])
        self.assertIn("alt=", ret[1])
        self.assertIn("ust=", ret[1])
        self.assertIn("gereken", ret[1])

        ince = _duz_koridor(x0=62, x1=66)
        yol, _guven, wps, ret = rpi_inference.analyze_path(
            ince, min_area_ratio=0.05, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(ALAN_YETERSIZ_SEBEBI, ret[0])
        self.assertIn("0.05", ret[1])

        with mock.patch.object(
                rpi_inference, "_bagli_koridor_yolu",
                return_value=(None, "alt_tohum=24px; A*=yok")):
            yol, _guven, wps, ret = rpi_inference.analyze_path(
                zemin, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(GORUS_HATTI_KOPUK_SEBEBI, ret[0])
        self.assertIn("alt_tohum", ret[1])

        sahte_zincir = [(64, 120), (64, 8)]
        with mock.patch.object(
                rpi_inference, "_bagli_koridor_yolu",
                return_value=(sahte_zincir, None)), \
             mock.patch.object(
                rpi_inference, "_rotayi_ornekle",
                return_value=sahte_zincir), \
             mock.patch.object(
                rpi_inference, "_kenarlar_guvenli", return_value=False):
            yol, _guven, wps, ret = rpi_inference.analyze_path(
                zemin, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(KENAR_GUVENSIZ_SEBEBI, ret[0])
        self.assertIn("kenar", ret[1])

    def test_yapisal_ret_dusuk_guven_ile_ezilmez(self):
        onceki = (MASKE_YOK_SEBEBI, "Zemin maskesi 0 piksel.")
        yol, guven, wps, ret = rpi_inference._rota_kararini_esikle(
            None, 0.0, [], onceki)
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps)
        self.assertEqual(onceki, ret)


class _Model:
    def predict(self, *_args, **_kwargs):
        return object()


class _SahteLink:
    def __init__(self):
        self.sent = []

    def send(self, data, peer=None):
        self.sent.append((data, peer))

    def recv(self, bufsize=4096):
        del bufsize
        return None, None


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
    gui.algi_kaynak = "drone"
    return gui


class YksGuiRetNedeniTests(unittest.TestCase):
    def _worker_calistir(self, zemin, engel, analyze_sahte=None):
        goruntu = np.zeros((*zemin.shape, 3), np.uint8)

        def maskeler(_sonuc, _h, _w, min_conf=None):
            del min_conf
            return {0: zemin.copy(), 1: engel.copy()}

        gui = _gui()
        put_text_cagrilari = []
        gercek_put_text = cv2.putText

        def put_text_sarmal(*args, **kwargs):
            put_text_cagrilari.append(str(args[1]))
            return gercek_put_text(*args, **kwargs)

        yamalar = [
            mock.patch.object(cv2, "imread", return_value=goruntu),
            mock.patch.object(rpi_inference, "get_masks", side_effect=maskeler),
            mock.patch.object(cv2, "putText", side_effect=put_text_sarmal),
        ]
        if analyze_sahte is not None:
            yamalar.append(mock.patch.object(
                rpi_inference, "analyze_path", side_effect=analyze_sahte))

        with yamalar[0], yamalar[1], yamalar[2]:
            if len(yamalar) == 4:
                with yamalar[3]:
                    gui._algi_kos(Path("ret-sahnesi.jpg"))
            else:
                gui._algi_kos(Path("ret-sahnesi.jpg"))

        paketler = list(gui.algi_kuyruk.queue)
        self.assertFalse(any(p[0] == "hata" for p in paketler), paketler)
        sonuc = next(p for p in paketler if p[0] == "sonuc")
        return sonuc[2], sonuc[3], put_text_cagrilari

    def test_uc_farkli_ret_gui_panelinde_uc_farkli_metin_uretir(self):
        bos = np.zeros((128, 128), np.uint8)
        maskesiz = self._worker_calistir(bos, bos)

        zemin = _duz_koridor()
        bariyer = np.zeros_like(zemin)
        bariyer[60:68, 40:88] = 1
        uc_bant = self._worker_calistir(zemin, bariyer)

        temiz = zemin.copy()

        def dusuk_guven(*_args, **_kwargs):
            return (2, ROTA_GUVEN_ESIGI - 0.001,
                    [(64, 120), (64, 8)], temiz.copy(), None, _SAHTE_OLCUM)

        dusuk = self._worker_calistir(zemin, bos, dusuk_guven)

        for beklenen, paket in (
                (MASKE_YOK_SEBEBI, maskesiz),
                (UC_BANT_TEMAS_YOK_SEBEBI, uc_bant),
                (DUSUK_GUVEN_SEBEBI, dusuk)):
            bilgi, log, bannerlar = paket
            self.assertIn(beklenen, bilgi)
            self.assertIn(beklenen, log)
            self.assertTrue(any(beklenen in metin for metin in bannerlar))

        self.assertEqual(3, len({p[0] for p in (maskesiz, uc_bant, dusuk)}))
        self.assertIn(
            f"güven {ROTA_GUVEN_ESIGI - 0.001:.3f}", dusuk[0])

    def test_iha_perceive_yapisal_reti_json_yoluna_tasir(self):
        zemin = np.zeros((64, 64), np.uint8)
        maskeler = {0: zemin, 1: zemin.copy()}

        with mock.patch.object(rpi_inference, "get_masks", return_value=maskeler), \
             mock.patch.object(rpi_inference, "is_dark", return_value=False):
            sonuc = iha_perceive._infer(
                np.zeros((64, 64, 3), np.uint8), _Model(), 0.15, 64,
                return_reason=True)

        _icerik, _maskeler, yol, guven, wps, _kip, ret = sonuc
        self.assertIsNone(yol)
        self.assertEqual(0.0, guven)
        self.assertEqual([], wps)
        self.assertEqual(MASKE_YOK_SEBEBI, ret[0])

    def test_iha_perceive_engel_maskesini_analyzera_tasir(self):
        zemin = _duz_koridor(64, 20, 44)
        engel = np.zeros_like(zemin)
        engel[30:34, 20:44] = 1
        maskeler = {0: zemin, 1: engel}

        with mock.patch.object(rpi_inference, "get_masks", return_value=maskeler), \
             mock.patch.object(rpi_inference, "is_dark", return_value=False):
            sonuc = iha_perceive._infer(
                np.zeros((64, 64, 3), np.uint8), _Model(), 0.15, 64,
                return_reason=True)

        _icerik, _maskeler, yol, _guven, wps, _kip, ret = sonuc
        self.assertIsNone(yol)
        self.assertEqual([], wps)
        self.assertEqual(UC_BANT_TEMAS_YOK_SEBEBI, ret[0])

    def test_yapisal_ret_no_route_yayininda_aynen_korunur(self):
        zemin = _duz_koridor()
        engel = np.zeros_like(zemin)
        engel[60:68, 40:88] = 1
        yol, _guven, wps, ret = rpi_inference.analyze_path(
            zemin, engel_mask=engel, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual([], wps)

        link = _SahteLink()
        IhaSender(link).send_no_route(
            *ret, repeat=1, interval=0.0, wait_ack=False)
        okuyucu = FrameReader()
        mesajlar = [mesaj for veri, _peer in link.sent
                    for mesaj in okuyucu.feed(veri)]

        self.assertEqual(["NO_ROUTE"], [m["type"] for m in mesajlar])
        self.assertEqual(ret[0], mesajlar[0]["sebep"])
        self.assertEqual(ret[1], mesajlar[0]["detay"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
