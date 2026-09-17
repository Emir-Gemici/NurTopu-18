"""ONARIM-03: YKS kesfi ("Bluetooth mantigi") — comms/yks_kesif.py + scripts/yks_eslestir.py.

Kilitler:
  K1 dogru eslesme -> KABUL, adres = KAYNAK IP + duyurudaki port; IP degisince ADRES_DEGISTI.
  K2 baska kimlik secilmez (tarama listesinde gorunur); yanlis anahtar IMZA_RED;
     govde degistirilirse (port oynatma) IMZA_RED.
  K3 ayni duyuru tekrar oynatilirsa TEKRAR_RED; YKS saatine gore ogrenilen farktan
     > 10 s sapan duyuru BAYAT_RED (Jetson RTC'sine dayanmaz).
  K4 secim tazeligi: 5 s yeni kabul yoksa BAYAT, adres korunur.
  K5 eslesme dosyasi 0600, kod iki tarafta ayni; bozuk dosya ret.
  K6 gercek soket: yayinci -> dinleyici yerel dongude KABUL; `tara` CLI listeler.
"""
import contextlib
import io
import os
import socket
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "comms", KOK / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import yks_kesif as yk  # noqa: E402


class _Saat:
    def __init__(self, t=100.0):
        self.t = t

    def __call__(self):
        return self.t


class Secici(unittest.TestCase):
    def setUp(self):
        self.es = yk.eslesme_uret("YKS")
        self.mono, self.duvar = _Saat(100.0), _Saat(1_000_000.0)
        self.s = yk.YksSecici(self.es, saat=self.mono, duvar=self.duvar)

    def test_K1_kabul_ve_adres_degisimi(self):
        p = yk.duyuru_uret(self.es, 5005, t=5_000_000.0)       # YKS saati farkli olabilir
        self.assertEqual(self.s.isle(p, "10.21.8.112"), "ADRES_DEGISTI")
        self.assertEqual(self.s.adres, ("10.21.8.112", 5005))
        self.assertEqual(self.s.isle(yk.duyuru_uret(self.es, 5005, t=5_000_001.0), "10.21.8.112"), "KABUL")
        self.assertEqual(self.s.isle(yk.duyuru_uret(self.es, 5005, t=5_000_002.0), "10.21.8.156"), "ADRES_DEGISTI")
        self.assertEqual(self.s.adres, ("10.21.8.156", 5005))
        self.assertEqual(self.s.sayac["adres_degisti"], 1)

    def test_K2_baska_kimlik_ve_imza(self):
        baska = yk.eslesme_uret("SAHTE")
        self.assertEqual(self.s.isle(yk.duyuru_uret(baska, 5005), "10.0.0.66"), "BASKA_KIMLIK")
        self.assertIsNone(self.s.adres)
        self.assertIn(baska["kimlik"], self.s.gorulen)
        ayni_kimlik_yanlis_anahtar = {"kimlik": self.es["kimlik"], "anahtar": baska["anahtar"]}
        self.assertEqual(self.s.isle(yk.duyuru_uret(ayni_kimlik_yanlis_anahtar, 5005), "10.0.0.66"), "IMZA_RED")
        p = yk.duyuru_uret(self.es, 5005).replace(b'"port":5005', b'"port":6666')
        self.assertEqual(self.s.isle(p, "10.0.0.66"), "IMZA_RED")
        self.assertIsNone(self.s.adres)
        self.assertEqual(self.s.isle(b"{bozuk", "10.0.0.66"), "BOZUK")

    def test_K3_tekrar_ve_bayat(self):
        p = yk.duyuru_uret(self.es, 5005, t=2000.0)
        self.assertEqual(self.s.isle(p, "10.0.0.5"), "ADRES_DEGISTI")
        self.assertEqual(self.s.isle(p, "10.0.0.5"), "TEKRAR_RED")
        self.duvar.t += 1.0
        self.assertEqual(self.s.isle(yk.duyuru_uret(self.es, 5005, t=2001.0), "10.0.0.5"), "KABUL")
        # kaydedilmis eski duyuru 60 s sonra tekrar oynatiliyor (nonce farkli uretilemez ama t eski)
        self.duvar.t += 60.0
        eski = yk.duyuru_uret(self.es, 5005, t=2002.0)
        self.assertEqual(self.s.isle(eski, "10.0.0.99"), "BAYAT_RED")
        self.assertEqual(self.s.adres, ("10.0.0.5", 5005), "bayat duyuru adresi ELE GECIREMEZ")

    def test_K4_secim_tazeligi(self):
        self.assertEqual(self.s.durum(), "YOK")
        self.s.isle(yk.duyuru_uret(self.es, 5005, t=1.0), "10.0.0.5")
        self.assertEqual(self.s.durum(), "TAZE")
        self.mono.t += yk.SECIM_BAYAT_S + 0.1
        self.assertEqual(self.s.durum(), "BAYAT")
        self.assertEqual(self.s.adres, ("10.0.0.5", 5005))


class Dosya(unittest.TestCase):
    def test_K5_dosya_izni_kod_ve_bozuk(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "alt" / "eslesme.json"
            es = yk.eslesme_uret("YKS")
            yk.eslesme_yaz(yol, es)
            self.assertEqual(stat.S_IMODE(os.stat(yol).st_mode), 0o600)
            okunan = yk.eslesme_oku(yol)
            self.assertEqual(yk.eslesme_kodu(okunan), yk.eslesme_kodu(es))
            self.assertRegex(yk.eslesme_kodu(es), r"^\d{6}$")
            kotu = Path(d) / "kotu.json"
            kotu.write_text('{"kimlik": "x", "anahtar": "abcd"}')
            with self.assertRaises(ValueError):
                yk.eslesme_oku(kotu)


class GercekSoket(unittest.TestCase):
    def test_K6_yayinci_dinleyici_ve_tara(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        es = yk.eslesme_uret("YKS")
        yay = yk.DuyuruYayinci(es, 5005, hedefler=[("127.0.0.1", port)], aralik_s=0.2, log=lambda *_: None)
        dinle = yk.dinleyici_soketi(("127.0.0.1", port))
        self.addCleanup(dinle.close)
        yay.start()
        self.addCleanup(yay.durdur)
        secici = yk.YksSecici(es)
        bitis = time.monotonic() + 3
        sonuc = None
        while time.monotonic() < bitis and sonuc is None:
            try:
                veri, adr = dinle.recvfrom(2048)
                sonuc = secici.isle(veri, adr[0])
            except BlockingIOError:
                time.sleep(0.05)
        self.assertEqual(sonuc, "ADRES_DEGISTI")
        self.assertEqual(secici.adres, ("127.0.0.1", 5005))
        dinle.close()
        import yks_eslestir
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "e.json"
            yk.eslesme_yaz(yol, es)
            with contextlib.redirect_stdout(io.StringIO()) as c:
                kod = yks_eslestir.main(["tara", "--sure", "1.5", "--dosya", str(yol), "--port", str(port)])
        self.assertEqual(kod, 0, c.getvalue())
        self.assertIn(es["kimlik"], c.getvalue())
        self.assertIn("SECILEN", c.getvalue())


class HubKesif(unittest.TestCase):
    """K7 — seri_hub --lan-yks-eslesme: adres ogrenilir, degisim izlenir, sahte duyuru ele geciremez."""

    def test_K7_hub_eslesen_yksyi_ogrenir(self):
        import contextlib as _c
        import seri_hub
        from link import UDPLink
        from protocol import decode, encode, heartbeat
        es = yk.eslesme_uret("YKS")
        kesif = yk.dinleyici_soketi(("127.0.0.1", 0))
        kesif_port = kesif.getsockname()[1]
        lan = UDPLink(bind=("127.0.0.1", 0), timeout=0.0, reuse=False)
        udp = UDPLink(bind=("127.0.0.1", 0), timeout=0.01)
        yks = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        self.addCleanup(yks.close)
        log = io.StringIO()
        with _c.redirect_stdout(log), _c.redirect_stderr(log):
            hub = seri_hub.SeriHub(None, udp, [], seri_ac=lambda: (_ for _ in ()).throw(OSError("yok")),
                                   lan_link=lan, yks_secici=yk.YksSecici(es), kesif_soketi=kesif)
        self.addCleanup(hub.kapat)
        uretici = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        self.addCleanup(uretici.close)
        gonder = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(gonder.close)

        def tur(n=3):
            with _c.redirect_stdout(log), _c.redirect_stderr(log):
                for _ in range(n):
                    hub.poll()

        # eslesme yokken: LAN'a gonderilmez, sayilir
        uretici.send(encode(heartbeat("iha", seq=1)), ("127.0.0.1", udp.port))
        tur()
        self.assertIsNone(hub.lan_yks)
        self.assertGreaterEqual(hub.sayac["lan_yks_yok"], 1)
        # sahte (baska anahtar) duyuru adres vermez
        sahte = {"kimlik": es["kimlik"], "anahtar": yk.eslesme_uret()["anahtar"]}
        gonder.sendto(yk.duyuru_uret(sahte, yks.port), ("127.0.0.1", kesif_port))
        tur()
        self.assertIsNone(hub.lan_yks)
        # gercek duyuru -> adres ogrenilir -> heartbeat YKS'ye ulasir
        gonder.sendto(yk.duyuru_uret(es, yks.port), ("127.0.0.1", kesif_port))
        tur()
        self.assertEqual(hub.lan_yks, ("127.0.0.1", yks.port))
        uretici.send(encode(heartbeat("iha", seq=2)), ("127.0.0.1", udp.port))
        tur()
        gelen = None
        for _ in range(50):
            gelen = yks.recv()[0]
            if gelen:
                break
            tur(1)
        self.assertEqual(decode(gelen)["seq"], 2)
        self.assertIn("YKS KESFI", log.getvalue())

    def test_K7b_hub_cli_kurallari(self):
        import seri_hub
        with contextlib.redirect_stderr(io.StringIO()) as e, self.assertRaises(SystemExit):
            seri_hub.main(["--port", "loop://", "--lan-bind", "127.0.0.1:0",
                           "--lan-yks", "127.0.0.1:5005", "--lan-yks-eslesme", "x.json"])
        self.assertIn("tam biri", e.getvalue())


class BaslatVeYks(unittest.TestCase):
    def test_K8_jetson_baslat_yks_eslesme(self):
        sys.path.insert(0, str(KOK / "tests"))
        from test_faz_b_jetson_baslat import BETIK, _AnaMakine, _arg_degeri, _bolumler, _kos
        m = _AnaMakine()
        self.addCleanup(m.temizle)
        dosya = m.d / "yks_eslesme.json"
        yk.eslesme_yaz(dosya, yk.eslesme_uret())
        kod, out, _ = _kos(BETIK, m.env(KIP="ikili", FOV="78", YKS_ESLESME=str(dosya)))
        hub = _bolumler(out)["birimler"]["navitas-seri-hub"]
        self.assertEqual(_arg_degeri(hub, "--lan-yks-eslesme"), str(dosya))
        self.assertNotIn("--lan-yks ", hub + " ")
        self.assertIn(f"[VAR] YKS eslesme {dosya}", out)
        self.assertNotIn("YKS_IP ya da YKS_ESLESME", out)

    def test_K9_yks_duyurusu_baslat(self):
        sys.path.insert(0, str(KOK / "comms"))
        import yks_gui
        from types import SimpleNamespace

        class _Yay:
            def __init__(self, es, port, hedefler, log):
                self.es, self.port, self.hedefler = es, port, hedefler

            def start(self):
                pass
        loglar = []
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "yeni" / "e.json"
            args = SimpleNamespace(eslesme=yol, bind="0.0.0.0:5005", iha=("10.21.8.7", 5009))
            y = yks_gui.yks_duyurusu_baslat(args, lambda m, r=None: loglar.append(m), yayinci_sinifi=_Yay)
            self.assertTrue(yol.is_file(), "eslesme dosyasi yoksa uretilir")
            self.assertEqual(y.port, 5005)
            self.assertEqual(y.hedefler, [("255.255.255.255", yk.DUYURU_PORT), ("10.21.8.7", yk.DUYURU_PORT)])
            self.assertIn("EŞLEŞME KODU", loglar[-1])
            bozuk = Path(d) / "bozuk.json"
            bozuk.write_text("{}")
            args.eslesme = bozuk
            self.assertIsNone(yks_gui.yks_duyurusu_baslat(args, lambda m, r=None: loglar.append(m)))
            self.assertIn("BAŞLATILAMADI", loglar[-1])


if __name__ == "__main__":
    unittest.main()
