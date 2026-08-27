"""K1 (sartname SS2.2.3 · CONTRACTS SS6.5): uretim algi yolu telsiz halkasi.

run_camera / run_video, --yks-hedef/--ika-hedef verildiginde her karede
OPEN_ROUTE ya da NO_ROUTE yayinlar; HEARTBEAT ayri is parcaciginda surer.
Alici GERCEK loopback UDP'dir (IkaReceiver + ham YKS soketi); sahte soket yok.
Zamanlama Event/deadline ile beklenir, time.sleep'e dayanan varsayim yok.
"""

import contextlib
import io
import socket
import sys
import threading
import time
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
import iha_sender  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import FrameReader  # noqa: E402
from karar_sozlesmesi import (  # noqa: E402
    KARAR_YOK_SEBEBI, DUSUK_GUVEN_SEBEBI, IHA_HEARTBEAT_ARALIK_S,
    ROTA_GUVEN_ESIGI, YAYIN_REF_XY)

BEKLEME_S = 8.0


class _Kamera:
    def __init__(self, n=1, sekil=(360, 640, 3)):
        self.kalan = n
        self.sekil = sekil

    def isOpened(self):
        return True

    def read(self):
        if self.kalan <= 0:
            return False, None
        self.kalan -= 1
        return True, np.full(self.sekil, 127, np.uint8)

    def release(self):
        pass


def _maskeler():
    return {0: np.ones((640, 640), np.uint8), 1: np.zeros((640, 640), np.uint8)}


class _YksSoketi:
    """Ham UDP dinleyici: gelen cerceveleri tipe gore biriktirir (ACK gondermez)."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.1)
        self.adres = f"127.0.0.1:{self.sock.getsockname()[1]}"
        self.mesajlar = []
        self._kilit = threading.Lock()
        self._dur = threading.Event()
        self._thr = threading.Thread(target=self._dongu, daemon=True)
        self._thr.start()

    def _dongu(self):
        okuyucu = FrameReader()
        while not self._dur.is_set():
            try:
                veri, _ = self.sock.recvfrom(4096)
            except (socket.timeout, ConnectionResetError):
                continue
            for m in okuyucu.feed(veri):
                with self._kilit:
                    self.mesajlar.append(m)

    def bekle(self, tip, adet=1, sure=BEKLEME_S):
        son = time.monotonic() + sure
        while time.monotonic() < son:
            with self._kilit:
                secilen = [m for m in self.mesajlar if m.get("type") == tip]
            if len(secilen) >= adet:
                return secilen
            time.sleep(0.02)
        with self._kilit:
            return [m for m in self.mesajlar if m.get("type") == tip]

    def kapat(self):
        self._dur.set()
        self._thr.join(2)
        self.sock.close()


class _Alicilar:
    """Loopback IKA (ACK'li IkaReceiver) + YKS (ham) alici cifti."""

    def __enter__(self):
        self.ika_link = UDPLink(bind=("127.0.0.1", 0))
        self.ika = IkaReceiver(self.ika_link).start()
        self.ika_adres = f"127.0.0.1:{self.ika_link.port}"
        self.rota_geldi = threading.Event()
        self.rota_yok_geldi = threading.Event()
        self.ika.on_route = lambda _m: self.rota_geldi.set()
        self.ika.on_no_route = lambda _m: self.rota_yok_geldi.set()
        self.yks = _YksSoketi()
        return self

    def __exit__(self, *_exc):
        self.ika.stop()
        self.ika_link.close()
        self.yks.kapat()

    def yayinci(self, **kw):
        kw.setdefault("repeat", 4)
        kw.setdefault("interval", 0.1)
        return iha_sender.yayinci_kur(yks=self.yks.adres, ika=self.ika_adres, **kw)


def _kamerayi_kos(analyze, yayinci, kare=1, olcek=0.05, tus=ord("q")):
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(kare)), \
            mock.patch.object(cv2, "imshow"), \
            mock.patch.object(cv2, "waitKey", return_value=tus), \
            mock.patch.object(cv2, "destroyAllWindows"), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", analyze), \
            mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
            contextlib.redirect_stdout(io.StringIO()):
        ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]), 0.30,
                      canli_olcek=(lambda _w: olcek), yayinci=yayinci)


class PikselRotaCevirimiTests(unittest.TestCase):
    def test_ilk_nokta_sifir_y_ekseni_ters_ve_segment_yogunlastirilir(self):
        yerel = [list(n) for n in iha_sender.piksel_rotayi_yerele_cevir(
            [(320, 600), (320, 300), (340, 40)], 0.05)]
        self.assertEqual([0.0, 0.0], yerel[0])
        # (320,300): 300 px yukari = +15 m ileri; x degismedi
        self.assertIn([0.0, 15.0], yerel)
        # son nokta: dx=+20 px=1 m, dy=560 px yukari=+28 m
        self.assertEqual([1.0, 28.0], yerel[-1])
        for a, b in zip(yerel, yerel[1:]):
            self.assertLessEqual(((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5,
                                 iha_sender.MAX_SEGMENT_M + 1e-9)
        self.assertGreater(len(yerel), 3)   # yogunlastirildi

    def test_olceksiz_veya_tek_noktali_rota_reddedilir(self):
        with self.assertRaises(ValueError):
            iha_sender.piksel_rotayi_yerele_cevir([(0, 0), (0, 10)], None)
        with self.assertRaises(ValueError):
            iha_sender.piksel_rotayi_yerele_cevir([(0, 0)], 0.05)


class RunCameraTelsizTests(unittest.TestCase):
    def test_open_route_ika_ve_yks_ye_ulasir_road_sozlesmesiyle(self):
        analyze = mock.Mock(return_value=(2, 0.9, [(320, 600), (320, 300), (320, 40)], None))
        with _Alicilar() as al:
            y = al.yayinci().start()
            try:
                _kamerayi_kos(analyze, y)
            finally:
                self.assertTrue(y.stop())
                y.sender.link.close()
            self.assertTrue(al.rota_geldi.wait(BEKLEME_S), f"IKA'ya OPEN_ROUTE gelmedi; hata={y.hata}")
            msg = al.ika.latest
            self.assertEqual("OPEN_ROUTE", msg["type"])
            self.assertEqual(2, msg["road"])
            self.assertEqual("orta", msg["label"])
            self.assertAlmostEqual(0.9, msg["conf"])
            self.assertEqual(list(YAYIN_REF_XY), msg["ref_xy"])
            self.assertEqual([0.0, 0.0], msg["waypoints"][0])
            self.assertEqual([0.0, 28.0], msg["waypoints"][-1])
            # YKS ham soketi ACK gondermez: ayni seq `repeat` kez tekrarlanir
            # (RF kaybina karsi sozlesme); yeni bir karar UYDURULMAZ.
            yks = al.yks.bekle("OPEN_ROUTE")
            self.assertGreaterEqual(len(yks), 1, "YKS'ye OPEN_ROUTE ulasmadi")
            self.assertEqual({msg["seq"]}, {m["seq"] for m in yks})
            self.assertEqual([("OPEN_ROUTE", 2)], [g[:2] for g in y.gonderilen])
            self.assertIn("ika", y.gonderilen[0][3])   # ACK alindi
            self.assertEqual([], y.hata)

    def test_ret_sebepli_karar_no_route_olur(self):
        analyze = mock.Mock(return_value=(None, 0.0, [], ("KAPALI_DAR", "test")))
        with _Alicilar() as al:
            y = al.yayinci().start()
            try:
                _kamerayi_kos(analyze, y)
            finally:
                self.assertTrue(y.stop())
                y.sender.link.close()
            self.assertTrue(al.rota_yok_geldi.wait(BEKLEME_S))
            self.assertIsNone(al.ika.latest)
            self.assertEqual("KAPALI_DAR", al.ika.last_no_route["sebep"])
            self.assertEqual("test", al.ika.last_no_route["detay"])
            self.assertEqual({"KAPALI_DAR"}, {m["sebep"] for m in al.yks.bekle("NO_ROUTE")})

    def test_karar_yok_sessizlik_degil_no_route_karar_yok(self):
        analyze = mock.Mock(return_value=(None, 0.0, [], None))
        with _Alicilar() as al:
            y = al.yayinci().start()
            try:
                _kamerayi_kos(analyze, y)
            finally:
                self.assertTrue(y.stop())
                y.sender.link.close()
            self.assertTrue(al.rota_yok_geldi.wait(BEKLEME_S))
            self.assertEqual(KARAR_YOK_SEBEBI, al.ika.last_no_route["sebep"])

    def test_esik_alti_guven_open_route_olarak_KACAMAZ(self):
        """Kapı IhaSender.send_open_route'tadir (cogaltilmaz); yayinci ona uyar."""
        dusuk = ROTA_GUVEN_ESIGI / 2
        analyze = mock.Mock(return_value=(1, dusuk, [(320, 600), (320, 300)], None))
        # _rota_kararini_esikle zaten esik altini reddeder; yayinciyi ondan
        # BAGIMSIZ sinamak icin esiklemeyi devre disi birakip dogrudan besle.
        with _Alicilar() as al, \
                mock.patch.object(ri, "_rota_kararini_esikle",
                                  side_effect=lambda o, c, w, r=None: (o, c, w, r)):
            y = al.yayinci().start()
            try:
                _kamerayi_kos(analyze, y)
            finally:
                self.assertTrue(y.stop())
                y.sender.link.close()
            self.assertTrue(al.rota_yok_geldi.wait(BEKLEME_S))
            self.assertIsNone(al.ika.latest)
            self.assertEqual(DUSUK_GUVEN_SEBEBI, al.ika.last_no_route["sebep"])
            self.assertEqual([], al.yks.bekle("OPEN_ROUTE", sure=0.3))

    def test_ret_sebebi_varken_yol_verilse_bile_open_route_uretilmez(self):
        sender = mock.Mock()
        sender.send_no_route.return_value = (1, {"ika"})
        y = iha_sender.KararYayinci(sender)
        y._karari_gonder(2, 0.95, [(320, 600), (320, 300)], 0.05, ("KENAR_GUVENSIZ", "x"))
        sender.send_open_route.assert_not_called()
        sender.send_no_route.assert_called_once()
        self.assertEqual("KENAR_GUVENSIZ", sender.send_no_route.call_args.args[0])

    def test_heartbeat_ayri_is_parcaciginda_surekli_yayinlanir(self):
        with _Alicilar() as al:
            y = al.yayinci(heartbeat_aralik=0.05).start()
            try:
                hb = al.yks.bekle("HEARTBEAT", adet=3)
            finally:
                self.assertTrue(y.stop())
                y.sender.link.close()
            self.assertGreaterEqual(len(hb), 3)
            self.assertTrue(all(m["node"] == "iha" for m in hb))
            self.assertTrue(al.ika.link_ok)   # IkaReceiver HEARTBEAT ile canli
        # Varsayilan aralik sozlesmeden gelir ve alici zaman asimindan kisadir.
        self.assertEqual(IHA_HEARTBEAT_ARALIK_S, iha_sender.KararYayinci(mock.Mock()).heartbeat_aralik)
        self.assertLess(IHA_HEARTBEAT_ARALIK_S, IkaReceiver(mock.Mock()).hb_timeout)

    def test_hedef_verilmezse_telsiz_modulu_HIC_yuklenmez(self):
        analyze = mock.Mock(return_value=(2, 0.9, [(320, 600), (320, 40)], None))
        with mock.patch.object(ri, "_iha_sender_modulu",
                               side_effect=AssertionError("telsiz yuklenmemeli")) as m, \
                mock.patch.object(socket, "socket",
                                  side_effect=AssertionError("soket acilmamali")):
            _kamerayi_kos(analyze, None)
        m.assert_not_called()
        self.assertIsNone(iha_sender.yayinci_kur())


class CliTests(unittest.TestCase):
    def test_hedef_yalniz_camera_veya_video_ile(self):
        p = ri._arguman_ayristirici()
        args = p.parse_args(["--image", "x.jpg", "--yks-hedef", "127.0.0.1:5005"])
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                ri._argumanlari_dogrula(p, args)
        args = p.parse_args(["--video", "x.mp4", "--mpp", "0.05",
                             "--yks-hedef", "127.0.0.1:5005", "--ika-hedef", "10.0.0.2:5006"])
        ri._argumanlari_dogrula(p, args)
        args = p.parse_args(["--video", "x.mp4", "--yks-hedef", "127.0.0.1"])
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                ri._argumanlari_dogrula(p, args)

    def test_main_yayinciyi_kurar_ve_kapatir(self):
        yayinci = mock.Mock()
        yayinci.heartbeat_aralik = 1.0
        yayinci.hata = []
        yayinci.stop.return_value = True
        modul = SimpleNamespace(yayinci_kur=mock.Mock(return_value=yayinci))
        yayinci.start.return_value = yayinci
        with mock.patch.object(sys, "argv", ["rpi", "--video", "x.mp4", "--mpp", "0.05",
                                             "--yks-hedef", "127.0.0.1:5005"]), \
                mock.patch.object(ri, "_iha_sender_modulu", return_value=modul), \
                mock.patch.object(ri, "load_model", return_value=(object(), Path("m.pt"), {"durum": "ok"})), \
                mock.patch.object(ri, "run_video") as rv, \
                contextlib.redirect_stdout(io.StringIO()):
            ri.main()
        # T162: `--ub-referans` verilmedigi icin konum saglayici None GECMELIDIR
        # — yani alan ihlali denetimi ACIKCA kapali kalir (sessiz sifir yasak).
        modul.yayinci_kur.assert_called_once_with(
            yks="127.0.0.1:5005", ika=None, seri=None, baud=57600,
            konum_saglayici=None)
        self.assertIs(yayinci, rv.call_args.kwargs["yayinci"])
        yayinci.stop.assert_called_once()
        yayinci.sender.link.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
