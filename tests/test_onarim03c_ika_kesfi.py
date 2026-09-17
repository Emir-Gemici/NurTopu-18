"""ONARIM-03c: IKA de eslesmeyle bulunur (RPi kurulmadi — kod altyapisi, PC'de sinanir).

Kilitler:
  I1 tur imzanin icinde: IKA secicisi YKS duyurusunu BASKA_TUR sayar (ve tersi); IKA dosyasiyla
     uretilen duyuru IKA secicisinde KABUL; tur alansiz eski dosya YKS sayilir.
  I2 YKS: --ika-eslesme ile kaynak kilidi ACIK kalir; IKA bulunana dek IKA HEARTBEAT reddedilir,
     ika_adresini_uygula sonrasi kabul edilir; CLI --ika ile birlikte verilemez.
  I3 ika_receiver duyurusu: IKA turu sart, seri kipte baslamaz, hedefler broadcast + --yks host'u.
  I4 hub: IKA kesfedilince cerceveler IKA'ya da gider (YKS henuz bulunmamisken bile); IKA IP'sinden
     gelen cerceve tuketiciye ulasir.
  I5 jetson_baslat KIP=ikili IKA_ESLESME: hub --lan-ika-eslesme; YKS_ESLESME yoksa [YOK].
"""
import contextlib
import io
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "comms", KOK / "codes", KOK / "scripts", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import yks_kesif as yk  # noqa: E402


class TurAyrimi(unittest.TestCase):
    def test_I1(self):
        ika = yk.eslesme_uret("IKA", "IKA")
        yks = yk.eslesme_uret("YKS", "YKS")
        si, sy = yk.DugumSecici(ika), yk.DugumSecici(yks)
        self.assertEqual(si.isle(yk.duyuru_uret(yks, 5005), "10.0.0.1"), "BASKA_TUR")
        self.assertEqual(sy.isle(yk.duyuru_uret(ika, 5006), "10.0.0.2"), "BASKA_TUR")
        self.assertEqual(si.isle(yk.duyuru_uret(ika, 5006), "10.0.0.2"), "ADRES_DEGISTI")
        self.assertEqual(si.adres, ("10.0.0.2", 5006))
        # ayni anahtar + kimlikle turu YKS'ye cevirip imzayi koruma denemesi: govde tur icerir -> IMZA_RED
        sahte = yk.duyuru_uret(ika, 5006).replace(b'"type":"IKA_DUYURU"', b'"type":"YKS_DUYURU"')
        sy_ayni = yk.DugumSecici({**ika, "tur": "YKS"})
        self.assertEqual(sy_ayni.isle(sahte, "10.0.0.9"), "IMZA_RED")
        with tempfile.TemporaryDirectory() as d:
            eski = Path(d) / "eski.json"
            eski.write_text('{"kimlik": "YKS-x", "anahtar": "%s"}' % ("ab" * 32))
            self.assertEqual(yk.eslesme_oku(eski)["tur"], "YKS")
        with self.assertRaises(ValueError):
            yk.eslesme_uret("X", "UCAK")


class YksIkaKesfi(unittest.TestCase):
    def test_I2_kaynak_kilidi_ve_adres(self):
        import yks_gui
        import queue
        app = SimpleNamespace(sabit_adr={"iha": ("10.21.8.7", 5009)}, son_adr={}, algi_kuyruk=queue.Queue())
        hb = {"v": 1, "type": "HEARTBEAT", "node": "ika", "seq": 1}
        uygun, _ = yks_gui.mesaj_kaynagi_dogrula(hb, ("10.0.0.50", 5006), app.sabit_adr["iha"],
                                                 app.sabit_adr.get("ika"))
        self.assertFalse(uygun, "IKA bulunmadan IKA verisi REDDEDILMELI")
        yks_gui.ika_adresini_uygula(app, ("10.0.0.50", 5006))
        self.assertEqual(app.sabit_adr["ika"], ("10.0.0.50", 5006))
        self.assertEqual(app.son_adr["ika"], ("10.0.0.50", 5006))
        uygun, _ = yks_gui.mesaj_kaynagi_dogrula(hb, ("10.0.0.50", 5006), app.sabit_adr["iha"],
                                                 app.sabit_adr.get("ika"))
        self.assertTrue(uygun)
        self.assertIn("İKA KEŞFİ", app.algi_kuyruk.get_nowait()[1])

    def test_I2b_cli(self):
        import subprocess
        import os
        r = subprocess.run([sys.executable, "-B", str(KOK / "comms" / "yks_gui.py"), "--iha", "127.0.0.1:5009",
                            "--ika", "127.0.0.1:5006", "--ika-eslesme", "x.json"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=10)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--ika ile --ika-eslesme birlikte", r.stderr)

    def test_I2c_kaynak_kilidi_kesifle_acik(self):
        """YksArayuz kurucusu: ika_peer None ama ika_kesif=True -> kaynak_kilidi True (kaynak metin kilidi)."""
        metin = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        self.assertIn("and iha_peer is not None and (ika_peer is not None or ika_kesif))", metin)


class IkaDuyurusu(unittest.TestCase):
    def test_I3(self):
        import ika_receiver

        class _Yay:
            def __init__(self, es, port, hedefler, log):
                self.es, self.port, self.hedefler = es, port, hedefler

            def start(self):
                pass
        with tempfile.TemporaryDirectory() as d:
            ika = Path(d) / "ika.json"
            yk.eslesme_yaz(ika, yk.eslesme_uret("IKA", "IKA"))
            yks = Path(d) / "yks.json"
            yk.eslesme_yaz(yks, yk.eslesme_uret("YKS", "YKS"))
            log = []
            y = ika_receiver.ika_duyurusu_baslat(
                SimpleNamespace(serial=None, eslesme=str(ika), bind="0.0.0.0:5006", yks="10.21.8.156:5005"),
                yayinci_sinifi=_Yay, log=log.append)
            self.assertEqual(y.port, 5006)
            self.assertEqual(y.hedefler, [("255.255.255.255", yk.DUYURU_PORT), ("10.21.8.156", yk.DUYURU_PORT)])
            self.assertIn("EŞLEŞME KODU", log[-1])
            self.assertIsNone(ika_receiver.ika_duyurusu_baslat(
                SimpleNamespace(serial="/dev/ttyUSB0", eslesme=str(ika), bind="0.0.0.0:5006", yks=None),
                yayinci_sinifi=_Yay, log=log.append))
            with self.assertRaises(SystemExit):
                ika_receiver.ika_duyurusu_baslat(
                    SimpleNamespace(serial=None, eslesme=str(yks), bind="0.0.0.0:5006", yks=None),
                    yayinci_sinifi=_Yay, log=log.append)


class HubIka(unittest.TestCase):
    def test_I4(self):
        import seri_hub
        from link import UDPLink
        from protocol import ack, decode, encode, heartbeat
        yks_es, ika_es = yk.eslesme_uret("YKS", "YKS"), yk.eslesme_uret("IKA", "IKA")
        kesif = yk.dinleyici_soketi(("127.0.0.1", 0))
        kport = kesif.getsockname()[1]
        lan = UDPLink(bind=("127.0.0.1", 0), timeout=0.0, reuse=False)
        udp = UDPLink(bind=("127.0.0.1", 0), timeout=0.01)
        ika = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        tuketici = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        for x in (ika, tuketici):
            self.addCleanup(x.close)
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            hub = seri_hub.SeriHub(None, udp, [("127.0.0.1", tuketici.port)],
                                   seri_ac=lambda: (_ for _ in ()).throw(OSError("yok")),
                                   lan_link=lan, yks_secici=yk.YksSecici(yks_es), kesif_soketi=kesif,
                                   ika_secici=yk.DugumSecici(ika_es))
        self.addCleanup(hub.kapat)
        g = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(g.close)
        uretici = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        self.addCleanup(uretici.close)

        def tur(n=3):
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                for _ in range(n):
                    hub.poll()
        g.sendto(yk.duyuru_uret(ika_es, ika.port), ("127.0.0.1", kport))
        tur()
        self.assertEqual(hub.lan_ika, ("127.0.0.1", ika.port))
        self.assertIsNone(hub.lan_yks, "YKS henuz bulunmadi")
        uretici.send(encode(heartbeat("iha", seq=5)), ("127.0.0.1", udp.port))
        gelen = None
        for _ in range(50):
            tur(1)
            gelen = ika.recv()[0]
            if gelen:
                break
        self.assertEqual(decode(gelen)["seq"], 5, "IKA'ya YKS'den bagimsiz aynalandi")
        ika.send(encode(ack(5, "ika", "OPEN_ROUTE")), ("127.0.0.1", lan.port))
        donen = None
        for _ in range(50):
            tur(1)
            donen = tuketici.recv()[0]
            if donen:
                break
        self.assertEqual(decode(donen)["node"], "ika")
        self.assertIn("IKA KESFI", log.getvalue())


class BaslatIka(unittest.TestCase):
    def test_I5(self):
        from test_faz_b_jetson_baslat import BETIK, _AnaMakine, _arg_degeri, _bolumler, _kos
        m = _AnaMakine()
        self.addCleanup(m.temizle)
        yks, ika = m.d / "yks.json", m.d / "ika.json"
        yk.eslesme_yaz(yks, yk.eslesme_uret("YKS", "YKS"))
        yk.eslesme_yaz(ika, yk.eslesme_uret("IKA", "IKA"))
        kod, out, _ = _kos(BETIK, m.env(KIP="ikili", FOV="78", YKS_ESLESME=str(yks), IKA_ESLESME=str(ika)))
        hub = _bolumler(out)["birimler"]["navitas-seri-hub"]
        self.assertEqual(_arg_degeri(hub, "--lan-ika-eslesme"), str(ika))
        self.assertIn(f"[VAR] IKA eslesme {ika}", out)
        kod2, out2, _ = _kos(BETIK, m.env(KIP="ikili", FOV="78", YKS_IP="10.0.0.9", IKA_ESLESME=str(ika)))
        self.assertIn("[YOK] IKA_ESLESME icin YKS_ESLESME de gerekli", out2)
        self.assertEqual(kod2, 3)


if __name__ == "__main__":
    unittest.main()
