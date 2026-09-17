"""ONARIM-09: YKS <-> Jetson LAN + SiK AYNI ANDA (coklu hat).

Kilitler:
  C1 CokluLink: UDP'den gelen (adr ile), seriden gelen (adr=None) ikisi de alinir;
     hat yaslari iki hat icin ayri; send(peer) yalniz UDP, send(None) yalniz seri;
     send_hepsi iki hatta; tek hat bozuksa digeri gider; ikisi de bozuksa hata.
  C2 YKS _ham_gonder: CokluLink'te komut IKI hattan (ayni bayt); UDP adresi yoksa yalniz SiK.
  C3 YKS CLI: --coklu yoksa eski ret mesajlari AYNEN; --coklu --serial'siz / --iha/--ika'siz ret.
  H1 seri_hub LAN aynasi: tuketici cercevesi seriye VE LAN YKS'ye; LAN'dan pinli YKS'nin
     cercevesi tuketiciye; yabanci IP dusurulur; seri KAPALIYKEN LAN yolu yasar.
  J1 jetson_baslat KIP=ikili --kuru: hub --lan-bind/--lan-yks, tuketiciler hub'a, YKS_IP zorunlu.
"""
import io
import contextlib
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import serial  # noqa: F401
except ImportError:  # pragma: no cover
    serial = None

from link import CokluLink, SerialLink, UDPLink  # noqa: E402
from protocol import FrameReader, command, decode, encode, heartbeat  # noqa: E402

YEREL = "127.0.0.1"


def _bekle(kosul, tavan=3.0):
    bitis = time.monotonic() + tavan
    while time.monotonic() < bitis:
        sonuc = kosul()
        if sonuc:
            return sonuc
        time.sleep(0.02)
    return None


class _BozukLink:
    def send(self, data, peer=None):
        raise OSError("hat yok")

    def recv(self, bufsize=4096):
        time.sleep(0.05)
        return None, None

    def close(self):
        pass


@unittest.skipIf(serial is None, "pyserial yok")
class CokluLinkTest(unittest.TestCase):
    def setUp(self):
        self.udp = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.seri = SerialLink("loop://", 57600, timeout=0.05)
        self.link = CokluLink(self.udp, self.seri)
        self.addCleanup(self.link.close)
        self.karsi = UDPLink(bind=(YEREL, 0), timeout=0.2)
        self.addCleanup(self.karsi.close)

    def _al(self):
        return _bekle(lambda: (lambda r: r if r[0] else None)(self.link.recv()))

    def test_C1_iki_hattan_alim_ve_yaslar(self):
        self.assertEqual(self.link.hat_yaslari(), {"lan": None, "sik": None})
        self.karsi.send(b"lan\n", (YEREL, self.link.port))
        veri, adr = self._al()
        self.assertEqual(veri, b"lan\n")
        self.assertEqual(adr[1], self.karsi.port)
        self.seri.send(b"sik\n")                   # loop:// geri okur
        veri, adr = self._al()
        self.assertEqual(veri, b"sik\n")
        self.assertIsNone(adr, "SiK hattindan gelen adres tasimaz")
        y = self.link.hat_yaslari()
        self.assertIsNotNone(y["lan"])
        self.assertIsNotNone(y["sik"])

    def test_C1_gonderim_yonlendirme(self):
        self.link.send(b"yalniz-lan\n", (YEREL, self.karsi.port))
        self.assertEqual(_bekle(lambda: self.karsi.recv()[0]), b"yalniz-lan\n")
        self.link.send(b"yalniz-sik\n")
        veri, adr = self._al()
        self.assertEqual((veri, adr), (b"yalniz-sik\n", None))
        self.assertEqual(self.link.send_hepsi(b"ikisi\n", (YEREL, self.karsi.port)), ["lan", "sik"])
        self.assertEqual(_bekle(lambda: self.karsi.recv()[0]), b"ikisi\n")
        self.assertEqual(self._al(), (b"ikisi\n", None))
        self.assertEqual(self.link.send_hepsi(b"adressiz\n", None), ["sik"])

    def test_C1_tek_hat_bozuksa_digeri(self):
        l1 = CokluLink(_BozukLink(), self.seri)
        self.addCleanup(l1.close)
        self.assertEqual(l1.send_hepsi(b"x\n", (YEREL, 9)), ["sik"])
        l2 = CokluLink(_BozukLink(), _BozukLink())
        self.addCleanup(l2.close)
        with self.assertRaises(OSError):
            l2.send_hepsi(b"x\n", (YEREL, 9))


@unittest.skipIf(serial is None, "pyserial yok")
class YksKomutTest(unittest.TestCase):
    def test_C2_ham_gonder_iki_hattan(self):
        import yks_gui
        udp = UDPLink(bind=(YEREL, 0), timeout=0.05)
        seri = SerialLink("loop://", 57600, timeout=0.05)
        link = CokluLink(udp, seri)
        self.addCleanup(link.close)
        iha = UDPLink(bind=(YEREL, 0), timeout=0.2)
        self.addCleanup(iha.close)
        loglar = []
        sahte = SimpleNamespace(link=link, son_adr={"iha": (YEREL, iha.port)},
                                _logla=lambda *a, **k: loglar.append(a))
        komut = command("PARACHUTE", "iha", seq=7)
        self.assertTrue(yks_gui.YksArayuz._ham_gonder(sahte, komut))
        self.assertEqual(decode(_bekle(lambda: iha.recv()[0])), komut)
        veri = _bekle(lambda: link.recv()[0])
        self.assertEqual(decode(veri), komut, "ayni komut SiK hattina da gitti")
        # UDP adresi bilinmiyorsa yalniz SiK
        sahte.son_adr = {}
        self.assertTrue(yks_gui.YksArayuz._ham_gonder(sahte, command("RTL", "iha", seq=8)))
        self.assertEqual(decode(_bekle(lambda: link.recv()[0]))["seq"], 8)
        self.assertEqual(loglar, [])

    def test_C2_seri_hat_var(self):
        import yks_gui
        self.assertTrue(yks_gui._seri_hat_var(object.__new__(CokluLink)))
        self.assertFalse(yks_gui._seri_hat_var(object()))


class YksCliTest(unittest.TestCase):
    def _kos(self, *arg):
        return subprocess.run([sys.executable, "-B", str(KOK / "comms" / "yks_gui.py"), *arg],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=10)

    def test_C3_eski_retler_ve_coklu_kurallari(self):
        r = self._kos("--serial", "COM_TEST", "--iha", "127.0.0.1:5007")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--serial ile --iha birlikte kullanılamaz", r.stderr)
        r = self._kos("--coklu", "--iha", "127.0.0.1:5009", "--ika", "127.0.0.1:5006")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--coklu için --serial", r.stderr)
        r = self._kos("--coklu", "--serial", "COM_TEST", "--iha", "127.0.0.1:5009")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--coklu kipinde --iha ve --ika", r.stderr)
        self.assertNotIn("Traceback", r.stderr)


@unittest.skipIf(serial is None, "pyserial yok")
class HubLanAynasiTest(unittest.TestCase):
    def setUp(self):
        from test_faz_b_seri_hub import _HubKurulum, _tuketici  # noqa: F401
        import seri_hub
        self.seri_hub = seri_hub
        self._HubKurulum = _HubKurulum
        self.yks_lan = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(self.yks_lan.close)
        self.lan = UDPLink(bind=(YEREL, 0), timeout=0.0, reuse=False)
        self.tuketici = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(self.tuketici.close)

    def _kur(self):
        k = self._HubKurulum(self, tuketiciler=[(YEREL, self.tuketici.port)],
                             lan_link=self.lan, lan_yks=(YEREL, self.yks_lan.port))
        return k

    def test_H1_tuketici_cercevesi_seriye_ve_LANa(self):
        k = self._kur()
        hb = heartbeat("iha", seq=3)
        uretici = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(uretici.close)
        uretici.send(encode(hb), k.hub_adr)
        mesaj, _ = k.yks_bekle(lambda m: m.get("seq") == 3)
        self.assertEqual(mesaj, hb, "seri yol")
        lan = _bekle(lambda: (k.tur(), self.yks_lan.recv()[0])[1])
        self.assertEqual(decode(lan), hb, "LAN aynasi")
        self.assertEqual(k.hub.sayac["lan_gonderilen"], 1)

    def test_H1_LANdan_komut_tuketiciye_yabanci_dusurulur(self):
        k = self._kur()
        cmd = command("PARACHUTE", "iha", seq=11)
        self.yks_lan.send(encode(cmd), (YEREL, self.lan.port))
        gelen = _bekle(lambda: (k.tur(), self.tuketici.recv()[0])[1])
        self.assertEqual(decode(gelen), cmd)
        self.assertEqual(k.hub.sayac["lan_cerceve"], 1)
        self.assertEqual(k.hub.sayac["seri_cerceve"], 0, "LAN cercevesi seri sayacina yazilmaz")
        # yabanci: 127.0.0.2'den (loopback alias) gelen dusurulur
        try:
            yabanci = UDPLink(bind=("127.0.0.2", 0), timeout=0.02)
        except OSError:
            self.skipTest("127.0.0.2 baglanamiyor")
        self.addCleanup(yabanci.close)
        yabanci.send(encode(command("ARM", "iha", seq=12)), (YEREL, self.lan.port))
        _bekle(lambda: (k.tur(), k.hub.sayac["lan_yabanci"] >= 1)[1])
        self.assertEqual(k.hub.sayac["lan_yabanci"], 1)
        k.tur(5)
        self.assertEqual(self.tuketici.recv()[0], None, "yabanci komut tuketiciye GITMEZ")

    def test_H1_seri_kapaliyken_LAN_yasar(self):
        uretici = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(uretici.close)
        udp = UDPLink(bind=(YEREL, 0), timeout=0.01)
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            hub = self.seri_hub.SeriHub(None, udp, [(YEREL, self.tuketici.port)],
                                        seri_ac=lambda: (_ for _ in ()).throw(OSError("yok")),
                                        lan_link=self.lan, lan_yks=(YEREL, self.yks_lan.port))
        self.addCleanup(hub.kapat)
        hb = heartbeat("iha", seq=21)
        uretici.send(encode(hb), (YEREL, udp.port))

        def tur():
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                hub.poll()
            return self.yks_lan.recv()[0]
        self.assertEqual(decode(_bekle(tur)), hb)
        self.assertGreaterEqual(hub.sayac["dusurulen"], 1, "seri yok: seri tarafi dusurdu")

    def test_H1_yapilandirma_hatasi(self):
        udp = UDPLink(bind=(YEREL, 0), timeout=0.01)
        self.addCleanup(udp.close)
        with self.assertRaises(ValueError):
            self.seri_hub.SeriHub(None, udp, [], lan_link=self.lan, lan_yks=None)
        self.lan.close()


class JetsonIkiliKipTest(unittest.TestCase):
    def test_J1_kuru_ikili(self):
        from test_faz_b_jetson_baslat import BETIK, _AnaMakine, _arg_degeri, _bolumler, _kos
        m = _AnaMakine()
        self.addCleanup(m.temizle)
        kod, out, err = _kos(BETIK, m.env(KIP="ikili", FOV="78", YKS_IP="10.0.0.9"))
        b = _bolumler(out)
        hub = b["birimler"].get("navitas-seri-hub")
        self.assertIsNotNone(hub, out)
        self.assertEqual(_arg_degeri(hub, "--lan-bind"), "0.0.0.0:5009")
        self.assertEqual(_arg_degeri(hub, "--lan-yks"), "10.0.0.9:5005")
        self.assertEqual(_arg_degeri(hub, "--bind"), "127.0.0.1:5100")
        self.assertEqual(_arg_degeri(b["birimler"]["navitas-rpi-inference"], "--yks-hedef"), "127.0.0.1:5100")
        self.assertEqual(_arg_degeri(b["birimler"]["navitas-iha-komut-alici"], "--izinli-kaynak"), "127.0.0.1:5100")
        kod2, out2, _ = _kos(BETIK, m.env(KIP="ikili", FOV="78"))
        self.assertEqual(kod2, 3, out2)
        self.assertIn("YKS_IP (KIP=ikili", out2)
        kod3, out3, _ = _kos(BETIK, m.env(KIP="sik", FOV="78"))
        self.assertNotIn("--lan-bind", _bolumler(out3)["birimler"].get("navitas-seri-hub", ""))


if __name__ == "__main__":
    unittest.main()
