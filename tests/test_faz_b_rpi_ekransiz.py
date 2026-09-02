"""D-404 (Faz B, donanim-oncesi kapanis): `rpi_inference --ekransiz` kipi.

NEDEN: Gorev C olcumu — `run_camera` her karede KOSULSUZ `cv2.imshow` cagiriyordu;
ekransiz Jetson'da (systemd, DISPLAY yok) ilk karede `cv2.error` ile cokup
`Restart=always` dongusune giriyordu (sartname §6.2 hands-off ihlali).

Kilitler:
  1) ekransiz=True  -> imshow DISPLAY yok diye patlasa bile kosum TAMAMLANIR,
     butun kareler islenir; gorsel HIC uretilmez (draw_masks cagrilmaz).
  2) ekransiz=False -> davranis DEGISMEDI: imshow patlarsa hata yukselir
     (sessiz yutma yok; masaustu kullanicisi hatayi gorur).
  3) KARAR YOLU BAYT-ES: ayni kare dizisiyle iki kipte `_karari_yayinla`ya
     giden argumanlar birebir ayni (madde 15 — algoritma degismedi).
  4) run_video: kayitsiz + ekransiz kosumda imshow/draw_masks yok.
  5) CLI `--ekransiz` bayragi var; systemd birimi bu bayrakla kosar ve
     DISPLAY/XAUTHORITY tasimaz (birim dosyasi metin kilidi).
"""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import rpi_inference as ri  # noqa: E402

BIRIM = KOK / "jetson_paket" / "systemd" / "navitas-rpi-inference.service"


class _Kamera:
    def __init__(self, n, sekil=(360, 640, 3)):
        self.kalan = n
        self.sekil = sekil

    def isOpened(self):
        return True

    def read(self):
        if self.kalan <= 0:
            return False, None
        self.kalan -= 1
        return True, np.full(self.sekil, 127, np.uint8)

    def get(self, _prop):
        return 0

    def release(self):
        pass


def _maskeler():
    return {0: np.ones((640, 640), np.uint8), 1: np.zeros((640, 640), np.uint8)}


def _analiz_dizisi():
    """Kare sirasina gore degisen karar: histerezisi de calistirir."""
    sira = [
        ("1", 0.9, [(1, 2), (3, 4)], None),
        ("1", 0.9, [(1, 2), (3, 4)], None),
        (None, 0.0, [], ("KARAR_YOK", "sahte")),
    ]
    say = {"i": 0}

    def analiz(*_a, **_k):
        r = sira[min(say["i"], len(sira) - 1)]
        say["i"] += 1
        return r
    return analiz


def _imshow_display_yok(*_a, **_k):
    raise cv2.error("Navitas: DISPLAY yok (sahte cv2.error)")


class _Yayinla:
    """`_karari_yayinla` cagrilarini argumanlariyla toplar."""

    def __init__(self):
        self.cagrilar = []

    def __call__(self, yayinci, open_path, path_conf, waypoints, mpp, reddi):
        self.cagrilar.append((open_path, float(path_conf), list(waypoints),
                              mpp, reddi))


def _run_camera(kare, *, ekransiz, imshow, waitkey=0, yayinla=None):
    yayinla = yayinla or _Yayinla()
    draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(kare)), \
            mock.patch.object(cv2, "imshow", side_effect=imshow), \
            mock.patch.object(cv2, "waitKey", return_value=waitkey), \
            mock.patch.object(cv2, "destroyAllWindows"), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
            mock.patch.object(ri, "draw_masks", draw), \
            mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
            mock.patch.object(ri, "_karari_yayinla", yayinla), \
            contextlib.redirect_stdout(io.StringIO()) as cikti:
        ozet = ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             0.30, canli_olcek=(lambda _w: 0.05),
                             yayinci=object(), ekransiz=ekransiz)
    return ozet, yayinla.cagrilar, draw, cikti.getvalue()


class EkransizKamera(unittest.TestCase):
    def test_1_ekransiz_display_yokken_TAMAMLANIR_ve_gorsel_uretilmez(self):
        ozet, cagrilar, draw, cikti = _run_camera(
            3, ekransiz=True, imshow=_imshow_display_yok)
        self.assertEqual(3, ozet["okunan"], ozet)
        self.assertIsNotNone(ozet["bitis"])
        self.assertNotEqual(ri.KAMERA_BITIS_KULLANICI, ozet["bitis"])
        self.assertEqual(0, draw.call_count, "ekransizda draw_masks cagrilmamali")
        self.assertGreaterEqual(len(cagrilar), 1, "karar yayini surmeli")
        self.assertIn("EKRANSIZ kip", cikti)

    def test_2_varsayilan_kipte_imshow_hatasi_YUKSELIR_davranis_degismedi(self):
        with self.assertRaises(cv2.error):
            _run_camera(3, ekransiz=False, imshow=_imshow_display_yok)

    def test_3_karar_yolu_iki_kipte_BIREBIR_ayni(self):
        _, ekranli, draw_e, _ = _run_camera(3, ekransiz=False, imshow=lambda *a, **k: None)
        _, ekransiz, draw_s, _ = _run_camera(3, ekransiz=True, imshow=_imshow_display_yok)
        self.assertEqual(ekranli, ekransiz)
        self.assertEqual(3, draw_e.call_count, "ekranli kipte her kare cizilir")
        self.assertEqual(0, draw_s.call_count)
        # Vakum kontrolu: karsilastirma bos listeyle gecmesin.
        self.assertGreaterEqual(len(ekranli), 2, ekranli)

    def test_4_ekranli_kipte_q_durdurur_ekransizda_waitKey_hic_cagrilmaz(self):
        ozet, _, _, _ = _run_camera(3, ekransiz=False,
                                    imshow=lambda *a, **k: None, waitkey=ord("q"))
        self.assertEqual(ri.KAMERA_BITIS_KULLANICI, ozet["bitis"])
        with mock.patch.object(cv2, "waitKey") as wk:
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(2)), \
                    mock.patch.object(cv2, "imshow", side_effect=_imshow_display_yok), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=True)
        self.assertEqual(0, wk.call_count)


class EkransizVideo(unittest.TestCase):
    def test_5_kayitsiz_ekransiz_videoda_imshow_ve_cizim_yok(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "sahte.mp4"
            yol.write_bytes(b"\x00")
            draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
            imshow = mock.MagicMock(side_effect=_imshow_display_yok)
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(3)), \
                    mock.patch.object(cv2, "imshow", imshow), \
                    mock.patch.object(cv2, "waitKey", return_value=0), \
                    mock.patch.object(cv2, "destroyAllWindows"), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "draw_masks", draw), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_video(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             str(yol), 0.30, save=False, mpp=0.05,
                             ekransiz=True)
            self.assertEqual(0, imshow.call_count)
            self.assertEqual(0, draw.call_count)


class CliVeBirim(unittest.TestCase):
    def test_6_cli_ekransiz_bayragi_var(self):
        sonuc = subprocess.run(
            [sys.executable, "-B", str(KOK / "codes" / "rpi_inference.py"), "--help"],
            capture_output=True, text=True, timeout=120, cwd=KOK)
        self.assertEqual(0, sonuc.returncode, sonuc.stderr[-800:])
        self.assertIn("--ekransiz", sonuc.stdout)

    def test_7_systemd_birimi_ekransiz_kosar_DISPLAY_tasimaz(self):
        metin = BIRIM.read_text(encoding="utf-8")
        exec_start = [s for s in metin.splitlines() if s.startswith("ExecStart=")]
        self.assertEqual(1, len(exec_start), exec_start)
        self.assertIn("--ekransiz", exec_start[0])
        self.assertIn("--camera", exec_start[0])
        for s in metin.splitlines():
            if s.startswith("#"):
                continue
            self.assertNotIn("DISPLAY", s, s)
            self.assertNotIn("XAUTHORITY", s, s)


if __name__ == "__main__":
    unittest.main()
