"""ONARIM-06 / T227: `rpi_inference --isaretli-yayin` — yayinlanmis karar bindirmeli yerel yayin.

Kilitler:
  1) Etiket: serit -> "SECILEN ROTA: n - AD", ret -> "ROTA YOK - sebep".
  2) Cizim: 1280x720, maske renkleri icerikte, etiket seridi var; 16:9 disi icerik dolgulanir.
  3) KARAR YOLU BAYT-ES: isaretli yayin acik/kapali `_karari_yayinla` cagrilari birebir ayni.
  4) Bindirme YAYINLANAN karardan: KararYumusatici'nin bastirdigi farkli serit adayi
     bindirmedeki etiketi DEGISTIRMEZ (mutasyon: her karede karar_yayinlandi -> DUSER).
  5) HTTP: /kare.jpg 200 JPEG (1280x720), /durum JSON; <= 2 Hz sinir.
  6) CLI: yalniz --camera ile; HOST:PORT bicimi; port doluysa UYARI + None (kosum surer).
"""
import contextlib
import io
import json
import socket
import sys
import time
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "scripts", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import isaretli_yayin as iy  # noqa: E402
import rpi_inference as ri  # noqa: E402
from test_faz_b_rpi_ekransiz import _Kamera, _Yayinla, _maskeler  # noqa: E402


class _SahteIsaretli:
    def __init__(self):
        self.yayinlanan = []
        self.kareler = []

    def karar_yayinlandi(self, yol, guven, waypoints, red, seq):
        self.yayinlanan.append((yol, seq))

    def kare_bildir(self, tuval, icerik, masks, seq):
        self.kareler.append(seq)
        return True


def _kos(kararlar, isaretli):
    say = {"i": 0}

    def analiz(*_a, **_k):
        r = kararlar[min(say["i"], len(kararlar) - 1)]
        say["i"] += 1
        return r
    yayinla = _Yayinla()
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(len(kararlar))), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", analiz), \
            mock.patch.object(ri, "_karari_yayinla", yayinla), \
            contextlib.redirect_stdout(io.StringIO()):
        ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]), 0.30,
                      canli_olcek=(lambda _w: 0.05), yayinci=object(), ekransiz=True,
                      isaretli=isaretli)
    return yayinla.cagrilar


_R1 = (1, 0.9, [(10, 20), (30, 40)], None)
_R3 = (3, 0.9, [(50, 60), (70, 80)], None)
_RED = (None, 0.0, [], ("KARAR_YOK", "sahte"))


class Etiket(unittest.TestCase):
    def test_metinler(self):
        self.assertEqual(iy.etiket_metni(2, None), "SECILEN ROTA: 2 - ORTA")
        self.assertEqual(iy.etiket_metni(None, "MASKE_YOK"), "ROTA YOK - MASKE_YOK")
        self.assertEqual(iy.etiket_metni(None, None), "ROTA YOK")


class Cizim(unittest.TestCase):
    def test_boyut_renk_etiket(self):
        tuval = np.full((1920, 1920, 3), 100, np.uint8)
        icerik = (0, 420, 1920, 1080)
        m0 = np.zeros((1920, 1920), np.uint8)
        m0[900:1400, 0:900] = 1
        m1 = np.zeros((1920, 1920), np.uint8)
        m1[900:1400, 1000:1900] = 1
        karar = {"yol": 2, "guven": 0.8, "waypoints": [(960, 1400), (960, 600)], "red": None,
                 "yayin_seq": 7}
        k = iy.isaretli_kare_ciz(tuval, icerik, {0: m0, 1: m1}, karar, 9, 0.0)
        self.assertEqual(k.shape, (720, 1280, 3))
        sol, sag = k[400, 200].astype(int), k[400, 1000].astype(int)
        self.assertGreater(sol[1], sol[2], "zemin yesil")
        self.assertGreater(sag[2], sag[1], "engel kirmizi")
        self.assertTrue((k[5:90, 5:600] > 150).any(), "etiket seridi yazili")

    def test_4_3_icerik_dolgulanir(self):
        tuval = np.full((1640, 1640, 3), 200, np.uint8)
        k = iy.isaretli_kare_ciz(tuval, (0, 205, 1640, 1230), {}, {"yol": None, "red": "X"}, 1, 0.0)
        self.assertEqual(k.shape, (720, 1280, 3))
        self.assertTrue((k[400, 5] == 0).all(), "yan dolgu siyah")


class KararYolu(unittest.TestCase):
    def test_3_acik_kapali_yayinlar_birebir(self):
        kararlar = [_R1, _R1, _R3, _R3, _R3, _RED, _R1]
        kapali = _kos(kararlar, None)
        acik = _kos(kararlar, _SahteIsaretli())
        self.assertGreaterEqual(len(kapali), 3)
        self.assertEqual(kapali, acik)

    def test_4_bastirilan_aday_bindirmeyi_degistirmez(self):
        s = _SahteIsaretli()
        cagrilar = _kos([_R1, _R3], s)
        self.assertEqual([y for y, _ in s.yayinlanan], [c[0] for c in cagrilar])
        self.assertEqual(s.yayinlanan, [(1, 1)], "farkli serit adayi teyitsiz: bindirme 1'de kalir")
        self.assertEqual(s.kareler, [1, 2])


class Http(unittest.TestCase):
    def test_5_kare_durum_ve_hiz_siniri(self):
        saat = {"t": 100.0}
        y = iy.IsaretliYayin("127.0.0.1", 0, saat=lambda: saat["t"], log=lambda *_: None).baslat()
        try:
            tuval = np.full((720, 1280, 3), 80, np.uint8)
            tuval = cv2.copyMakeBorder(tuval, 280, 280, 0, 0, cv2.BORDER_CONSTANT, value=114)
            y.karar_yayinlandi(3, 0.77, [(100, 500)], None, 5)
            self.assertTrue(y.kare_bildir(tuval, (0, 280, 1280, 720), _maskeler(), 5))
            saat["t"] += 0.1
            self.assertFalse(y.kare_bildir(tuval, (0, 280, 1280, 720), _maskeler(), 6), "<= 2 Hz")
            host, port = y.adres
            veri = None
            for _ in range(50):
                try:
                    with urllib.request.urlopen(f"http://{host}:{port}/kare.jpg", timeout=2) as r:
                        veri = r.read()
                    break
                except Exception:
                    time.sleep(0.05)
            self.assertIsNotNone(veri)
            kare = cv2.imdecode(np.frombuffer(veri, np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual(kare.shape, (720, 1280, 3))
            with urllib.request.urlopen(f"http://{host}:{port}/durum", timeout=2) as r:
                d = json.loads(r.read())
            self.assertEqual(d["boyut"], [1280, 720])
            self.assertEqual(y.atlanan, 1)
        finally:
            y.durdur()


class Cli(unittest.TestCase):
    def _hata(self, argv):
        parser = ri._arguman_ayristirici()
        args = parser.parse_args(argv)
        with contextlib.redirect_stderr(io.StringIO()) as e, self.assertRaises(SystemExit) as cm:
            ri._argumanlari_dogrula(parser, args)
        return cm.exception.code, e.getvalue()

    def test_6_yalniz_camera_ve_bicim(self):
        kod, metin = self._hata(["--image", "x.jpg", "--isaretli-yayin", "127.0.0.1:8081"])
        self.assertEqual(kod, 2)
        self.assertIn("--isaretli-yayin yalniz --camera", metin)
        kod, metin = self._hata(["--camera", "--mavlink", "udp:127.0.0.1:14550", "--mav-sysid", "1",
                                 "--fov", "63", "--isaretli-yayin", "8081"])
        self.assertEqual(kod, 2)
        self.assertIn("HOST:PORT", metin)

    def test_6b_port_doluysa_none(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as c:
                self.assertIsNone(ri.isaretli_yayin_ac(f"127.0.0.1:{s.getsockname()[1]}"))
            self.assertIn("UYARI: isaretli yayin ACILAMADI", c.getvalue())
        finally:
            s.close()

    def test_jetson_baslat_bayragi_taniyor(self):
        import re
        self.assertRegex((KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8"),
                         re.compile(r"[\"']--isaretli-yayin[\"']"))


if __name__ == "__main__":
    unittest.main()
