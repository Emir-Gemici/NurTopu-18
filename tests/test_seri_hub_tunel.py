"""K3 (hub) — `seri_hub` tunel kipi (CONTRACTS §7.6 · results/tunel_20260916/ON_KAYIT.md).

NEDEN: KIP=tunel'de navitas-seri-hub seri port yerine `TunelLink` (hava) acar.
Hub'in UDP tarafi, fan-out'u ve ariza semantigi DEGISMEZ; burada kilitlenen:
  T1  hub linkin zaman asimini SERI_OKUMA_ZAMAN_ASIMI_S'ye ceker (yeniden
      baglamada da) — D-403 tur gecikmesi dersi tunelde de gecerli;
  T2  --port / --tunel birbirini dislar, biri zorunlu; T2b --tunel + --baud RED;
  T3  tunel ucu acilamazsa cikis 4, ileti tunel ucunu ve kimligi basar ('None' yok);
  T3b seri kip iletileri BIREBIR eski metin (test_faz_b_seri_hub kilitleri);
  T4/T5 OSError -> kapat, dusur, 1 s sonra yeniden ac;
  T6  sayac logunda link sayaclari (yalniz tunelde);
  T7  yeniden acilan TunelLink'in cercevesi karsi uc hafizasinda 'yinelenen'
      diye YUTULMAZ (hafiza 0,8 s < yeniden acma 1,0 s).
Yeni testler yalniz efemer port kullanir.
"""
from __future__ import annotations

import contextlib
import io
import sys
import threading
import time
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
    import serial
except ImportError:  # pragma: no cover
    serial = None

import mavlink_tunel as mt  # noqa: E402
import seri_hub as modul  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import command, encode  # noqa: E402

YEREL = "127.0.0.1"
GEVSEK_ZAMAN_ASIMI_S = 0.3
TAVAN_S = 3.0


class _Saat:
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t


def _sessiz():
    return contextlib.ExitStack()


@unittest.skipIf(pymavlink is None, "pymavlink kurulu degil")
class SeriHubTunelTests(unittest.TestCase):
    def _link(self, kimlik=mt.KIMLIK_HAVA, **kw):
        kw.setdefault("log", lambda *a, **k: None)
        ln = mt.TunelLink((YEREL, 0), kimlik, **kw)
        self.addCleanup(ln.close)
        return ln

    def _hub(self, seri, **kw):
        udp = UDPLink(bind=(YEREL, 0), timeout=GEVSEK_ZAMAN_ASIMI_S, reuse=False)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            hub = modul.SeriHub(seri, udp, kw.pop("tuketiciler", []), **kw)
        self.addCleanup(hub.kapat)
        return hub

    def test_T1_hub_tunel_zaman_asimini_sabitine_ceker_yeniden_baglamada_da(self):
        ln = self._link(timeout=GEVSEK_ZAMAN_ASIMI_S)
        self.assertEqual(GEVSEK_ZAMAN_ASIMI_S, ln.timeout, "on kosul")
        hub = self._hub(ln)
        self.assertEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, hub.seri_link.timeout)
        yeni = self._link(timeout=GEVSEK_ZAMAN_ASIMI_S)
        with contextlib.redirect_stdout(io.StringIO()):
            hub._seri_bagla(yeni)
        self.assertEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, yeni.timeout)

    def test_T2_port_ve_tunel_birbirini_dislar_biri_zorunlu(self):
        for argv in ([], ["--port", "loop://", "--tunel", f"{YEREL}:0"],
                     ["--tunel", "bozuk"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as cm, \
                    contextlib.redirect_stderr(io.StringIO()):
                modul.main(argv)
            self.assertEqual(2, cm.exception.code)

    def _durdurulan_hub_yamasi(self):
        """Gercek SeriHub'i kurar ama 0,2 s sonra durdurur: arguman reddi
        kirilirsa (mutant M35) test ASILI KALMAZ, FAIL olarak gorunur."""
        orijinal = modul.SeriHub

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            threading.Timer(0.2, hub.durdur).start()
            return hub
        return mock.patch.object(modul, "SeriHub", side_effect=yakala)

    def test_T2b_tunel_ile_baud_verilirse_SystemExit_2(self):
        hata = io.StringIO()
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(hata),                 contextlib.redirect_stdout(io.StringIO()), self._durdurulan_hub_yamasi():
            modul.main(["--tunel", f"{YEREL}:0", "--baud", "57600", "--bind", f"{YEREL}:0",
                        "--log-aralik", "0"])
        self.assertEqual(2, cm.exception.code)
        self.assertIn("--baud", hata.getvalue())

    def test_T2c_tunel_kimlik_denetimi_tunel_dalinda(self):
        for argv, parca in (
                (["--tunel", f"{YEREL}:0", "--tunel-kimlik", "iha"], "--tunel-kimlik"),
                (["--port", "loop://", "--tunel-kimlik", mt.KIMLIK_HAVA], "--tunel-kimlik")):
            hata = io.StringIO()
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as cm,                     contextlib.redirect_stderr(hata), contextlib.redirect_stdout(io.StringIO()),                     self._durdurulan_hub_yamasi():
                modul.main(argv + ["--bind", f"{YEREL}:0", "--log-aralik", "0"])
            self.assertEqual(2, cm.exception.code)
            self.assertIn(parca, hata.getvalue())

    def test_T3_tunel_ucu_doluysa_cikis_4_ileti_uc_ve_kimlik_None_yok(self):
        dolu = self._link()
        hata = io.StringIO()
        with mock.patch.object(modul, "SeriHub") as hub_sinifi, \
                contextlib.redirect_stderr(hata), contextlib.redirect_stdout(io.StringIO()):
            kod = modul.main(["--tunel", f"{YEREL}:{dolu.port}", "--tunel-kimlik", "hava",
                              "--bind", f"{YEREL}:0"])
        self.assertEqual(4, kod)
        metin = hata.getvalue()
        self.assertIn("KIRMIZI", metin)
        self.assertIn(f"tunel {YEREL}:{dolu.port}", metin)
        self.assertIn("kimlik=hava", metin)
        self.assertNotIn("None", metin)
        hub_sinifi.assert_not_called()

    @unittest.skipIf(serial is None, "pyserial kurulu degil")
    def test_T3b_seri_kip_iletileri_birebir_eski_metin(self):
        hata = io.StringIO()
        with mock.patch.object(modul, "SeriHub"), contextlib.redirect_stderr(hata), \
                contextlib.redirect_stdout(io.StringIO()):
            kod = modul.main(["--port", "COM_YOK_BOYLE_BIR_PORT", "--bind", f"{YEREL}:0"])
        self.assertEqual(4, kod)
        self.assertIn("KIRMIZI HATA: seri port acilamadi 'COM_YOK_BOYLE_BIR_PORT': ",
                      hata.getvalue())
        cikti = io.StringIO()
        orijinal = modul.SeriHub

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            threading.Timer(0.2, hub.durdur).start()
            return hub
        with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
                contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(io.StringIO()):
            kod = modul.main(["--port", "loop://", "--bind", f"{YEREL}:0", "--log-aralik", "0"])
        self.assertEqual(0, kod)
        self.assertRegex(cikti.getvalue(),
                         r"\[SERI_HUB\] seri loop:// @ 57600 <-> udp 127\.0\.0\.1:\d+ statik=0")

    def test_T3c_tunel_kipi_cli_hub_kurulur_ileti_tunel_ucu(self):
        cikti = io.StringIO()
        orijinal = modul.SeriHub
        kurulan = {}

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            kurulan["hub"] = hub
            threading.Timer(0.2, hub.durdur).start()
            return hub
        with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
                contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(io.StringIO()):
            kod = modul.main(["--tunel", f"{YEREL}:0", "--bind", f"{YEREL}:0",
                              "--log-aralik", "0"])
        self.assertEqual(0, kod)
        self.assertRegex(cikti.getvalue(),
                         r"\[SERI_HUB\] tunel 127\.0\.0\.1:0 kimlik=hava <-> udp ")
        self.assertNotIn("None", cikti.getvalue())
        yeni = kurulan["hub"].seri_ac()
        self.addCleanup(yeni.close)
        self.assertIsInstance(yeni, mt.TunelLink)

    def test_T4_T5_oserror_kapat_dusur_yeniden_ac(self):
        saat = _Saat()
        acilan = []

        def seri_ac():
            ln = mt.TunelLink((YEREL, 0), mt.KIMLIK_HAVA, log=lambda *a, **k: None)
            acilan.append(ln)
            self.addCleanup(ln.close)
            return ln
        hub = self._hub(seri_ac(), seri_ac=seri_ac, saat=saat, log_aralik_s=0)
        ilk = hub.seri_link
        tuketici = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(tuketici.close)
        with mock.patch.object(ilk, "recv", side_effect=OSError("yerel soket arizasi")), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()) as hata:
            hub.poll()
        self.assertIn("KIRMIZI", hata.getvalue())
        self.assertIsNone(hub.seri_link)
        self.assertEqual(1, hub.sayac["seri_ariza"])
        self.assertEqual(-1, ilk.sock.fileno(), "arizali tunel ucu kapatilmali")
        tuketici.send(encode(command("PARACHUTE", "iha", seq=1)), hub.udp_link.sock.getsockname())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            bitis = time.monotonic() + TAVAN_S
            while hub.sayac["dusurulen"] == 0 and time.monotonic() < bitis:
                hub.poll()
        self.assertEqual(1, hub.sayac["dusurulen"], "arizada UDP cercevesi DUSURULUR")
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            hub.poll()
        self.assertIsInstance(hub.seri_link, mt.TunelLink)
        self.assertIsNot(ilk, hub.seri_link)
        self.assertEqual(1, hub.sayac["yeniden_acma"])
        self.assertEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, hub.seri_link.timeout)

    def test_T6_sayac_logu_tunel_sayaclarini_basar_seride_basmaz(self):
        hub = self._hub(self._link(), log_aralik_s=0)
        with contextlib.redirect_stdout(io.StringIO()) as out, \
                contextlib.redirect_stderr(io.StringIO()):
            hub._sayac_logla()
        self.assertIn("tunel sayac", out.getvalue())
        self.assertIn("kimlik_boslugu=", out.getvalue())
        self.assertIn("zaman_asimi_dusen=", out.getvalue())
        if serial is not None:
            from link import SerialLink
            hub2 = self._hub(SerialLink("loop://", timeout=0.02), log_aralik_s=0)
            with contextlib.redirect_stdout(io.StringIO()) as out2, \
                    contextlib.redirect_stderr(io.StringIO()):
                hub2._sayac_logla()
            self.assertNotIn("tunel sayac", out2.getvalue())

    def test_T7_yeniden_acilan_uc_ayni_kimlikle_bile_YUTULMAZ(self):
        """Eski uc kimlik 500..502 ile uc cerceve yollar; hub arizada kapatir ve
        SERI_YENIDEN_ACMA_ARALIGI_S sonra yeni uc AYNI baslangic kimligiyle (500,
        zorlanmis en kotu durum) acilir. Karsi uc yeni cerceveyi TESLIM etmeli:
        hafiza (0,8 s) yeniden acma araligindan (1,0 s) kisadir."""
        yer = self._link(mt.KIMLIK_YER, timeout=0.05)
        kimlikler = iter([500, 500])

        def seri_ac():
            ln = mt.TunelLink((YEREL, 0), mt.KIMLIK_HAVA, ilk_kimlik=next(kimlikler),
                              log=lambda *a, **k: None)
            ln.akran = (YEREL, yer.port)
            ln._son_akran_t = ln.saat()
            self.addCleanup(ln.close)
            return ln
        hub = self._hub(seri_ac(), seri_ac=seri_ac, log_aralik_s=0)
        yer.akran = (YEREL, hub.seri_link.port)
        tuketici = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(tuketici.close)
        hub_adr = hub.udp_link.sock.getsockname()

        def yolla_ve_al(metin):
            tuketici.send(metin, hub_adr)
            bitis = time.monotonic() + TAVAN_S
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                while time.monotonic() < bitis:
                    hub.poll()
                    veri, _ = yer.recv()
                    if veri is not None:
                        return veri
            return None
        for i in range(3):
            self.assertEqual(f"eski {i}\n".encode(), yolla_ve_al(f"eski {i}\n".encode()))
        with mock.patch.object(hub.seri_link, "recv", side_effect=OSError("ariza")), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            hub.poll()
        self.assertIsNone(hub.seri_link)
        bitis = time.monotonic() + TAVAN_S
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            while hub.seri_link is None and time.monotonic() < bitis:
                hub.poll()
                yer.recv()
        self.assertIsNotNone(hub.seri_link)
        self.assertEqual(500, hub.seri_link._sonraki_kimlik, "zorlanmis kimlik tekrari")
        self.assertEqual(b"yeni 0\n", yolla_ve_al(b"yeni 0\n"),
                         "yeni ucun cercevesi eski hafizaya takilip yutuldu")
        s = yer.sayac
        self.assertEqual(0, s["yinelenen_parca"])
        self.assertGreaterEqual(s["kimlik_geri"] + s["kimlik_sicramasi"] + s["kimlik_boslugu"], 1)


class SeriHubIzoleImportTests(unittest.TestCase):
    """T8 (duzeltme turu 1, gerileme bulgusu): KIP=sik hub'i mavlink_tunel.py
    OLMADAN calismali. Once seri_hub modul duzeyinde mavlink_tunel'i import
    ediyordu; yalniz seri_hub.py'si guncellenmis bir Jetson'da (jetson_baslat
    mavlink_tunel.py'yi yalniz KIP=tunel'de denetler) sik hub'i
    ModuleNotFoundError ile Restart=always cokme dongusune girerdi."""

    def _izole_dizin(self):
        import shutil
        import tempfile
        dizin = Path(tempfile.mkdtemp(prefix="seri_hub_izole_"))
        self.addCleanup(shutil.rmtree, dizin, True)
        for ad in ("seri_hub.py", "link.py", "protocol.py"):
            shutil.copy2(KOK / "comms" / ad, dizin / ad)
        return dizin

    def _kos(self, dizin, *arg):
        import subprocess
        return subprocess.run([sys.executable, "-B", *arg], cwd=str(dizin),
                              capture_output=True, text=True, timeout=60)

    def test_T8_sik_kipi_mavlink_tunel_olmadan_import_ve_yardim(self):
        dizin = self._izole_dizin()
        self.assertFalse((dizin / "mavlink_tunel.py").exists())
        r = self._kos(dizin, "seri_hub.py", "--port", "loop://", "--help")
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("--port", r.stdout)
        self.assertNotIn("ModuleNotFoundError", r.stderr)
        kod = ("import sys; import seri_hub; "
               "assert 'mavlink_tunel' not in sys.modules, 'tunel modulu yuklendi'; "
               "assert 'iha_komut_alici' not in sys.modules; print('OK')")
        r = self._kos(dizin, "-c", kod)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("OK", r.stdout)

    @unittest.skipIf(serial is None, "pyserial kurulu degil")
    def test_T8b_sik_kipi_izole_dizinde_hub_kurulur_ve_durur(self):
        dizin = self._izole_dizin()
        kod = ("import sys, threading; import seri_hub as m; o = m.SeriHub\n"
               "def y(*a, **k):\n"
               "    h = o(*a, **k); threading.Timer(0.3, h.durdur).start(); return h\n"
               "m.SeriHub = y\n"
               "r = m.main(['--port', 'loop://', '--bind', '127.0.0.1:0', '--log-aralik', '0'])\n"
               "assert 'mavlink_tunel' not in sys.modules\n"
               "print('CIKIS', r)")
        r = self._kos(dizin, "-c", kod)
        self.assertEqual(0, r.returncode, r.stderr)
        self.assertIn("CIKIS 0", r.stdout)
        self.assertIn("[SERI_HUB] seri loop:// @ 57600", r.stdout)


if __name__ == "__main__":
    unittest.main()
