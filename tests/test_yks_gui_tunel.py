"""K7 — YKS hakem ekrani tunel kipi (`comms/yks_gui.py --tunel`, CONTRACTS §7.6).

NEDEN: yer tarafinda COM'un tek sahibi Mission Planner'dir; NAVITAS verisi MP
aynasindan (UDP 127.0.0.1:14570) `TunelLink('yer')` ile alinir. Kilitlenenler:
  Y0 `--tunel` TEK BASINA argparse'tan gecer (UDP'nin --ika/--iha zorunlulugu
     tunelde uygulanmaz — elestiri 2 bulgu 3) ve main tunel linkini kurar;
  Y1/Y2 `--tunel` ile --serial/--demo/--ika/--iha REDDEDILIR (link acilmadan);
  Y3 kunye `dinleme` ve baslangic logu uc kipte BIREBIR (udp -> args.bind,
     serial -> port, tunel -> 'tunel://HOST:PORT'; `f'tunel://{None}'` tuzagi);
  Y4 saha tasiyicisi dallari (ACK peer'siz, CMD `_ham_gonder` adressiz) tunel
     linkinde de calisir; Y5 `tasiyici == 'tunel'`, tunel sayac izleme 1 Hz.
Tk acilmaz: `tk.Tk`, `YksArayuz` ve kapanis yardimcisi mock'lanir; argparse ve
link kurulumu GERCEKTIR (efemer port).

⚠ ORTAM: HEAD b5595cc9'da `comms/rota_inceleme.py` depoda YOK (ana calisma
agacinda izlenmeyen dosya); o yokken `yks_gui` import EDILEMEZ ve bu dosya
GORUNUR bicimde atlanir (YAPILAMADI). Diger yks testleri ayni nedenle tabanda
ERROR verir (results/tunel_20260916/taban_suit.txt).
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    import pymavlink  # noqa: F401
except ImportError:  # pragma: no cover
    pymavlink = None

try:
    import yks_gui
    YKS_IMPORT_HATASI = None
except ModuleNotFoundError as exc:          # yalniz eksik modul: gorunur atlama
    yks_gui = None
    YKS_IMPORT_HATASI = exc

import mavlink_tunel as mt  # noqa: E402
from link import saha_tasiyicisi_mi, tasiyici_adi  # noqa: E402

YEREL = "127.0.0.1"


class _SahteTunel:
    """Saha tasiyicisi isaretli sahte link (sinif duzeyi isaret, TunelLink ikizi)."""
    SAHA_TASIYICI = True
    TASIYICI_ADI = mt.TASIYICI_TUNEL

    def __init__(self):
        self.gonderilen = []
        self.sayac = {k: 0 for k in mt.TunelLink.LINK_SAYAC_ANAHTARLARI
                      + mt.Birlestirici.SAYAC_ANAHTARLARI}

    def send(self, data, peer=None):
        self.gonderilen.append((data, peer))


@unittest.skipIf(yks_gui is None, f"YAPILAMADI: yks_gui import edilemedi ({YKS_IMPORT_HATASI})")
@unittest.skipIf(pymavlink is None, "pymavlink kurulu degil")
class YksGuiTunelMainTests(unittest.TestCase):
    def _main(self, argv, seri_link=None):
        """main()'i Tk'siz kostur; (YksArayuz mock, kunye kwargs, olusan link)."""
        d = tempfile.mkdtemp(prefix="yks_tunel_")
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        kunye = {}
        gercek_kunye = yks_gui.yki_oturum_kunyesi

        def kunye_yakala(**kw):
            kunye.update(kw)
            return gercek_kunye(**kw)
        arayuz = mock.Mock(name="YksArayuz")
        arayuz.ALGI_KAYNAKLAR = yks_gui.YksArayuz.ALGI_KAYNAKLAR
        arayuz.ALGI_VARSAYILAN_KAYNAK = yks_gui.YksArayuz.ALGI_VARSAYILAN_KAYNAK
        env = {k: v for k, v in os.environ.items() if k != "NAVITAS_KAMERA_URL"}
        yamalar = [
            mock.patch.object(sys, "argv", ["yks_gui.py", *argv, "--hakem-log",
                                            str(Path(d) / "hakem.jsonl")]),
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(yks_gui.tk, "Tk", mock.Mock(name="Tk")),
            mock.patch.object(yks_gui, "YksArayuz", arayuz),
            mock.patch.object(yks_gui, "kapanis_kaynaklarini_temizle", mock.Mock()),
            mock.patch.object(yks_gui, "yki_oturum_kunyesi", side_effect=kunye_yakala),
        ]
        if seri_link is not None:
            yamalar.append(mock.patch.object(yks_gui, "SerialLink", return_value=seri_link))
        with contextlib.ExitStack() as yigin:
            for y in yamalar:
                yigin.enter_context(y)
            yks_gui.main()
        link = arayuz.call_args[0][1]
        kapat = getattr(link, "close", None)
        if callable(kapat):
            self.addCleanup(kapat)
        return arayuz, kunye, link

    def _baslangic_logu(self, arayuz):
        return [c.args[0] for c in arayuz.return_value._logla.call_args_list
                if str(c.args[0]).startswith("YKS hazır — dinleniyor")]

    def test_Y0_tunel_tek_basina_argparse_gecer_ve_tunel_linki_kurulur(self):
        arayuz, kunye, link = self._main(["--tunel", f"{YEREL}:0"])
        self.assertIsInstance(link, mt.TunelLink)
        self.assertEqual(mt.KIMLIK_YER, link.kimlik)
        self.assertEqual(mt.TUNEL_YER_AYRISTIRMA, link.ayristirma)
        kw = arayuz.call_args.kwargs
        self.assertIsNone(kw["iha_peer"])
        self.assertIsNone(kw["ika_peer"])
        self.assertFalse(kw["demo"])

    def test_Y1_Y2_tunel_ile_serial_demo_ika_iha_REDDEDILIR_link_acilmadan(self):
        for ek, parca in ((["--serial", "COM5"], "--tunel ile --serial"),
                          (["--demo"], "--demo yalnız UDP"),
                          (["--ika", "127.0.0.1:5006"], "--tunel ile --ika"),
                          (["--iha", "127.0.0.1:5007"], "--tunel ile --iha")):
            with self.subTest(ek=ek):
                hata = io.StringIO()
                with mock.patch.object(sys, "argv", ["yks_gui.py", "--tunel", f"{YEREL}:0", *ek]), \
                        mock.patch.object(yks_gui, "TunelLink", side_effect=AssertionError("acildi")), \
                        mock.patch.object(yks_gui, "SerialLink", side_effect=AssertionError("acildi")), \
                        contextlib.redirect_stderr(hata), self.assertRaises(SystemExit) as cm:
                    yks_gui.main()
                self.assertEqual(2, cm.exception.code)
                self.assertIn(parca, hata.getvalue())

    def test_Y1b_udp_kipinde_ika_iha_zorunlulugu_DEGISMEDI(self):
        hata = io.StringIO()
        with mock.patch.object(sys, "argv", ["yks_gui.py", "--bind", f"{YEREL}:0"]), \
                contextlib.redirect_stderr(hata), self.assertRaises(SystemExit):
            yks_gui.main()
        self.assertIn("UDP kipinde --ika HOST:PORT zorunlu", hata.getvalue())

    def test_Y3_kunye_dinleme_ve_baslangic_logu_uc_kipte_BIREBIR(self):
        seri = mock.Mock(name="SerialLink")
        durumlar = (
            (["--bind", f"{YEREL}:0", "--ika", "127.0.0.1:5006", "--iha", "127.0.0.1:5007"],
             f"{YEREL}:0", None),
            (["--serial", "COM5"], "COM5", seri),
            (["--tunel", f"{YEREL}:0"], f"tunel://{YEREL}:0", None),
        )
        for argv, beklenen, seri_link in durumlar:
            with self.subTest(argv=argv):
                arayuz, kunye, _link = self._main(argv, seri_link=seri_link)
                self.assertEqual(beklenen, kunye["dinleme"])
                self.assertNotIn("None", kunye["dinleme"])
                self.assertEqual([f"YKS hazır — dinleniyor: {beklenen}"],
                                 self._baslangic_logu(arayuz))


@unittest.skipIf(yks_gui is None, f"YAPILAMADI: yks_gui import edilemedi ({YKS_IMPORT_HATASI})")
class YksGuiTunelDallariTests(unittest.TestCase):
    def _app(self, link):
        app = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
        app.link = link
        app.son_adr = {}
        app.sabit_adr = {}
        app._logla = mock.Mock()
        return app

    def test_Y4_ham_gonder_tunelde_adressiz_gonderir(self):
        link = _SahteTunel()
        app = self._app(link)
        self.assertTrue(app._ham_gonder(yks_gui.command("PARACHUTE", "iha", seq=5)))
        self.assertEqual(1, len(link.gonderilen))
        self.assertIsNone(link.gonderilen[0][1], "tunelde UDP adresi YOK, ortam yayini")
        udp_benzeri = mock.Mock(name="UDPLink")
        app2 = self._app(udp_benzeri)
        self.assertFalse(app2._ham_gonder(yks_gui.command("PARACHUTE", "iha", seq=6)),
                         "mock link saha tasiyicisi SAYILMAZ (sinif isareti yok)")

    def test_Y5_tasiyici_adi_ve_kaynak_kilidi(self):
        link = _SahteTunel()
        self.assertTrue(saha_tasiyicisi_mi(link))
        self.assertEqual("tunel", tasiyici_adi(link))
        self.assertTrue(saha_tasiyicisi_mi(mt.TunelLink.__new__(mt.TunelLink)))
        self.assertEqual("tunel", tasiyici_adi(mt.TunelLink.__new__(mt.TunelLink)))
        from link import SerialLink, UDPLink
        self.assertEqual("serial", tasiyici_adi(SerialLink.__new__(SerialLink)))
        self.assertEqual("udp", tasiyici_adi(UDPLink.__new__(UDPLink)))
        self.assertEqual("udp", tasiyici_adi(mock.Mock()))

    def test_Y5b_tunel_sayac_artisi_1_Hz_KIRMIZI_seride_sessiz(self):
        link = _SahteTunel()
        app = self._app(link)
        self.assertEqual({}, app._tunel_sayac_izle(simdi=100.0))
        link.sayac["kimlik_boslugu"] += 2
        link.sayac["alinan_datagram"] += 50
        self.assertIsNone(app._tunel_sayac_izle(simdi=100.5), "1 Hz'den sik yazilmaz")
        artis = app._tunel_sayac_izle(simdi=101.1)
        self.assertEqual({"kimlik_boslugu": 2}, artis)
        app._logla.assert_called_once()
        self.assertEqual("kirmizi", app._logla.call_args.args[1])
        self.assertIn("kimlik_boslugu+2", app._logla.call_args.args[0])
        link.sayac["akran_degisti"] += 1
        link.sayac["zaman_asimi_dusen"] += 1
        link.sayac["tavan_ustu"] += 1
        self.assertEqual({"zaman_asimi_dusen": 1, "tavan_ustu": 1, "akran_degisti": 1},
                         app._tunel_sayac_izle(simdi=102.2))
        seri_app = self._app(mock.Mock())
        self.assertIsNone(seri_app._tunel_sayac_izle(simdi=5.0))
        seri_app._logla.assert_not_called()


if __name__ == "__main__":
    unittest.main()
