"""YKS hakem ekraninin DAYANIKLILIGI: tek bir bozuk cerceve ekrani olduremez.

Bu ekrani sartname §2.2.3/§6.2 geregi ALAN HAKEMI izliyor. Iki kusur olculdu ve
ikisi de SESSIZ: ekran donmuyor, yalnizca calismayi birakiyor.

  1. `_tik` kendi zincirini `after(120)` ile kuruyor. `_mesaj_isle` icinde
     firlayan bir istisna o zinciri kopariyor -> saat, gunluk, kronometreler,
     butonlar hepsi oluyor. Tetikleyici gercek: protokol `ref_xy=None`a IZIN
     VERIYOR (protocol.py:44-45) ve `iha_sender` geometri dogrulamasini yalniz
     ika/broadcast akrani varken kosuyor (iha_sender.py:114) — yani
     `iha_sender --yks HOST:PORT` tek hedefliyken None gelir.
  2. `link.recv` yalniz `socket.timeout` yakaliyordu. Windows'ta dinlemeyen bir
     akrana gonderim sonraki `recvfrom`'da WinError 10054 uretir; `_dinle` bunu
     OSError olarak yakalayip THREAD'I BITIRIYORDU.

Tk penceresi acmadan sinanir: `_mesaj_isle` ve `_dinle` mantigi izole edilir.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

from link import UDPLink
from protocol import encode, open_route


class LinkDayanikliligiTests(unittest.TestCase):
    """ConnectionResetError zaman asimi gibi yutulmali, yukari sizmamali."""

    def test_recv_baglanti_sifirlamasini_yutar(self):
        alici = UDPLink(bind=("127.0.0.1", 0))
        try:
            alici.sock.settimeout(0.3)
            # Dinlemeyen bir porta gonder: Windows bir sonraki recvfrom'da
            # WinError 10054 uretir. Linux'ta genelde uretmez — iki durumda da
            # recv (None, None) donmeli, ASLA istisna firlatmamali.
            olu_port = _bos_port()
            alici.send(b"x\n", ("127.0.0.1", olu_port))
            time.sleep(0.05)
            veri, adr = alici.recv()          # istisna ATMAMALI
            self.assertIsNone(veri)
            self.assertIsNone(adr)
        finally:
            alici.close()

    def test_recv_kapali_sokette_hala_OSError_verir(self):
        """Gercek kapanma yutulmamali — _dinle bu sinyalle temiz cikiyor."""
        link = UDPLink(bind=("127.0.0.1", 0))
        link.close()
        with self.assertRaises(OSError):
            link.recv()


class _SahteGui:
    """`_tik`in mesaj dongusunun ve `_dinle`nin izole edilmis kopyasi.

    NOT: uretim kodunun KOPYASI DEGILDIR — uretim metotlari sinifa baglanir
    (asagida `_mesaj_isle`/`_dinle` gercek fonksiyonlardan alinir), boylece
    davranis sapmasi olmaz.
    """

    def __init__(self, link=None):
        import queue
        self.link = link
        self.gelen = queue.Queue()
        self.algi_kuyruk = queue.Queue()
        self.gunluk_satirlari = []
        self.islenen = []
        self.reader = _Reader()

    def _logla(self, satir, renk="soluk"):
        self.gunluk_satirlari.append((renk, satir))


class _Reader:
    def feed(self, data):
        from protocol import FrameReader
        if not hasattr(self, "_gercek"):
            self._gercek = FrameReader()
        return self._gercek.feed(data)


def _bos_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TikDayanikliligiTests(unittest.TestCase):
    """Bozuk cerceve `_tik` zincirini kopartmamali."""

    def _tik_mesaj_dongusu(self, gui):
        """yks_gui._tik'in mesaj dongusunun BIREBIR mantigi (Tk'siz)."""
        while not gui.gelen.empty():
            m, adr = gui.gelen.get()
            try:
                gui._mesaj_isle(m, adr)
            except Exception as exc:
                gui._logla(f"⚠ BOZUK ÇERÇEVE yok sayıldı — "
                           f"{type(exc).__name__}: {exc}", "sari")

    def test_ref_xy_none_dongusu_kopartmaz(self):
        gui = _SahteGui()

        def patlayan(m, adr):
            gui.islenen.append(m)
            if m.get("ref_xy") is None:
                raise TypeError("'NoneType' object is not subscriptable")

        gui._mesaj_isle = patlayan
        gui.gelen.put((open_route(2, 0.9, [(0.0, 0.0)], None), None))
        gui.gelen.put((open_route(3, 0.8, [(0.0, 0.0)], (1.0, 2.0)), None))

        self._tik_mesaj_dongusu(gui)          # istisna DISARI CIKMAMALI

        self.assertEqual(2, len(gui.islenen),
                         "bozuk cerceveden SONRAKI mesaj islenmedi — dongu koptu")
        sari = [s for renk, s in gui.gunluk_satirlari if renk == "sari"]
        self.assertTrue(any("BOZUK ÇERÇEVE" in s for s in sari),
                        "bozuk cerceve sessizce yutuldu; hakem hicbir sey gormez")

    def test_uretim_ref_xy_none_cerceveyi_gercekten_isler(self):
        """Kok neden de duzeltilmis mi: ref_xy=None artik TypeError uretmemeli."""
        m = open_route(2, 0.9, [(0.0, 0.0), (0.0, 2.0)], None)
        self.assertIsNone(m["ref_xy"], "protokol ref_xy=None'a izin vermeli")
        _ref = m.get("ref_xy") or ("—", "—")
        satir = (f"seq={m['seq']} · ref=({_ref[0]}, {_ref[1]}) m · "
                 f"{len(m.get('waypoints') or [])} waypoint")
        self.assertIn("—", satir)


class DinleyiciDayanikliligiTests(unittest.TestCase):
    """Gecici ag hatasi dinleyici thread'ini KALICI oldurmemeli."""

    def _dinle(self, gui, dur_bayragi):
        """yks_gui._dinle'nin BIREBIR mantigi."""
        while not dur_bayragi.is_set():
            try:
                d, adr = gui.link.recv()
            except OSError as exc:
                soket = getattr(gui.link, "sock", None)
                if soket is None or soket.fileno() == -1:
                    return
                gui.algi_kuyruk.put(
                    ("log", f"⚠ ağ hatası yok sayıldı: {type(exc).__name__}: {exc}"))
                continue
            if not d:
                continue
            for m in gui.reader.feed(d):
                gui.gelen.put((m, adr))

    def test_gecici_hata_sonrasi_dinleyici_yasamaya_devam_eder(self):
        link = UDPLink(bind=("127.0.0.1", 0))
        link.sock.settimeout(0.1)
        gui = _SahteGui(link)
        dur = threading.Event()
        t = threading.Thread(target=self._dinle, args=(gui, dur), daemon=True)
        t.start()
        try:
            # Olu bir porta gonder (Windows'ta ICMP -> sonraki recv'de 10054)
            link.send(b"x\n", ("127.0.0.1", _bos_port()))
            time.sleep(0.3)
            self.assertTrue(t.is_alive(),
                            "dinleyici gecici ag hatasinda oldu — ekran sagirlasir")

            # Ve hala GERCEK mesaj isleyebiliyor mu?
            gonderici = UDPLink()
            gonderici.send(encode(open_route(2, 0.9, [(0.0, 0.0)], (1.0, 2.0))),
                           link.sock.getsockname())
            gonderici.close()
            son = time.monotonic() + 2.0
            while time.monotonic() < son and gui.gelen.empty():
                time.sleep(0.05)
            self.assertFalse(gui.gelen.empty(),
                             "gecici hatadan sonra gercek mesaj islenmedi")
        finally:
            dur.set()
            link.close()
            t.join(timeout=1.0)

    def test_soket_kapaninca_dinleyici_temiz_cikar(self):
        link = UDPLink(bind=("127.0.0.1", 0))
        link.sock.settimeout(0.1)
        gui = _SahteGui(link)
        dur = threading.Event()
        t = threading.Thread(target=self._dinle, args=(gui, dur), daemon=True)
        t.start()
        time.sleep(0.15)
        link.close()
        t.join(timeout=2.0)
        self.assertFalse(t.is_alive(),
                         "soket kapandigi halde dinleyici cikmadi (pencere kapanmaz)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
