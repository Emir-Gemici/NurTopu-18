"""NEDEN: Saha iniş yayıncısı kanıt oluşmadan paket üretmemeli; kanıt
oluştuğunda da simülasyondan kopyalanmış ikinci bir yol yerine aynı ACK'li
IHA_LANDED gövdesini UDP ve SiK taşıyıcısında kullanmalıdır.
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
COMMS = KOK / "comms"
if str(COMMS) not in sys.path:
    sys.path.insert(0, str(COMMS))

import iha_inis_yayinci as yayinci  # noqa: E402
import inis_kaniti as kanit  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import ack, decode, encode  # noqa: E402


class SahteMav:
    def __init__(self):
        self.kapandi = False

    def close(self):
        self.kapandi = True


class MavMesaj:
    def __init__(self, tip, **alanlar):
        self._tip = tip
        for ad, deger in alanlar.items():
            setattr(self, ad, deger)

    def get_type(self):
        return self._tip

    def get_srcSystem(self):
        return 42


class KanitMav(SahteMav):
    def __init__(self):
        super().__init__()
        self.mesajlar = []
        for _ in range(3):
            self.mesajlar.extend([
                MavMesaj(kanit.MESAJ_EXTENDED_SYS_STATE, landed_state=1),
                MavMesaj(kanit.MESAJ_GLOBAL_POSITION_INT, relative_alt=250),
            ])

    def recv_match(self, **kwargs):
        if not kwargs.get("blocking") or kwargs.get("timeout", 0) <= 0:
            raise ValueError("bounded blocking okuma gerekli")
        return self.mesajlar.pop(0) if self.mesajlar else None


class AckLink:
    def __init__(self, ack_dugumleri=()):
        self.ack_dugumleri = tuple(ack_dugumleri)
        self.kuyruk = []
        self.gonderilen = []
        self.kapandi = False

    def send(self, data, peer=None):
        self.gonderilen.append((data, peer))
        mesaj = decode(data)
        if mesaj and mesaj.get("type") == "IHA_LANDED":
            self.kuyruk.extend(
                encode(ack(mesaj["seq"], dugum))
                for dugum in self.ack_dugumleri)

    def recv(self):
        return (self.kuyruk.pop(0), None) if self.kuyruk else (None, None)

    def close(self):
        self.kapandi = True


class KayitSerial(SerialLink):
    def __init__(self):
        self.gonderilen = []

    def send(self, data, peer=None):
        self.gonderilen.append((data, peer))


class OrtakYayinGovdesiTests(unittest.TestCase):
    def test_serial_broadcast_tek_fiziksel_mesajla_iki_ack_bekler(self):
        link = AckLink(("ika", "yks"))
        sonuc = yayinci.iha_inisini_yayinla(
            {"ika": None, "yks": None}, repeat=1, interval=0.01,
            tasiyici=link)
        self.assertTrue(sonuc)
        self.assertEqual(1, len(link.gonderilen))
        self.assertTrue(link.kapandi)

    def test_ack_eksigi_false_ve_tasiyici_kapali(self):
        link = AckLink()
        self.assertFalse(yayinci.iha_inisini_yayinla(
            {"ika": None}, repeat=1, interval=0.001, tasiyici=link))
        self.assertTrue(link.kapandi)

    def test_bos_hedefte_enjekte_tasiyici_da_kapanir(self):
        link = AckLink()
        self.assertTrue(yayinci.iha_inisini_yayinla({}, tasiyici=link))
        self.assertTrue(link.kapandi)

    def test_ika_receiver_serial_hatta_adressiz_ack_gonderir(self):
        link = KayitSerial()
        receiver = IkaReceiver(link)
        receiver._kontrol_mesaji_ack(17, None)
        self.assertEqual(1, len(link.gonderilen))
        mesaj = decode(link.gonderilen[0][0])
        self.assertEqual(("ACK", 17, "ika"),
                         (mesaj["type"], mesaj["ref"], mesaj["node"]))


class SahaCliTests(unittest.TestCase):
    def test_pixhawk_kanitindan_gercek_udp_ika_latch_i_acilir(self):
        mav = KanitMav()
        mavutil = SimpleNamespace(mavlink=SimpleNamespace(
            MAV_LANDED_STATE_ON_GROUND=1))
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        receiver = IkaReceiver(alici_link, hb_timeout=2.0).start()
        try:
            with mock.patch.object(
                    yayinci, "mavlink_baglantisi_ac", return_value=mav), \
                 mock.patch.object(
                    kanit, "_mavutil_al", return_value=mavutil):
                sonuc = yayinci.main([
                    "--mavlink", "mock:pixhawk",
                    "--kanit-timeout", "2",
                    "--heartbeat-sure", "0",
                    "--ika", f"127.0.0.1:{alici_link.port}",
                ])
            self.assertEqual(0, sonuc)
            self.assertTrue(receiver.wait_iha_landed(1.0))
            self.assertTrue(receiver.iha_landed)
            self.assertTrue(mav.kapandi)
            print("[T20_KAPI] IHA_LANDED_saha=1 ACK=ika exit=0")
        finally:
            receiver.stop()
            alici_link.close()

    def test_kanit_false_ise_hicbir_yayin_hatti_acilmaz(self):
        mav = SahteMav()
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac", return_value=mav), \
             mock.patch.object(yayinci, "yerde_mi", return_value=False), \
             mock.patch.object(yayinci, "SerialLink") as serial, \
             mock.patch.object(yayinci, "iha_inisini_yayinla") as yayin, \
             contextlib.redirect_stderr(io.StringIO()):
            sonuc = yayinci.main([
                "--mavlink", "udp:127.0.0.1:14550",
                "--kanit-timeout", "5",
                "--heartbeat-sure", "0",
                "--serial", "COM7",
            ])
        self.assertEqual(3, sonuc)
        serial.assert_not_called()
        yayin.assert_not_called()
        self.assertTrue(mav.kapandi)

    def test_udp_hedefleri_kanit_sonrasi_ortak_govdeye_gider(self):
        mav = SahteMav()
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac", return_value=mav), \
             mock.patch.object(yayinci, "yerde_mi", return_value=True), \
             mock.patch.object(
                 yayinci, "iha_inisini_yayinla", return_value=True) as yayin:
            sonuc = yayinci.main([
                "--mavlink", "udp:127.0.0.1:14550",
                "--kanit-timeout", "5",
                "--heartbeat-sure", "0",
                "--ika", "127.0.0.1:5006", "--yks", "127.0.0.1:5005",
            ])
        self.assertEqual(0, sonuc)
        yayin.assert_called_once_with({
            "ika": ("127.0.0.1", 5006),
            "yks": ("127.0.0.1", 5005),
        }, heartbeat_suresi=0.0,
            heartbeat_araligi=yayinci.IHA_INIS_HEARTBEAT_ARALIGI_S)
        self.assertTrue(mav.kapandi)
        self.assertGreater(mav.inis_kaniti_deadline_monotonic,
                           yayinci.time.monotonic())

    def test_serial_kanit_sonrasi_ika_ack_bekler(self):
        mav = SahteMav()
        link = mock.Mock()
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac", return_value=mav), \
             mock.patch.object(yayinci, "yerde_mi", return_value=True), \
             mock.patch.object(yayinci, "SerialLink", return_value=link) as serial, \
             mock.patch.object(
                 yayinci, "iha_inisini_yayinla", return_value=True) as yayin:
            sonuc = yayinci.main([
                "--mavlink", "/dev/ttyACM0", "--serial", "/dev/ttyUSB0",
                "--kanit-timeout", "5",
                "--heartbeat-sure", "0",
                "--baud", "57600",
            ])
        self.assertEqual(0, sonuc)
        serial.assert_called_once_with("/dev/ttyUSB0", 57600)
        yayin.assert_called_once_with(
            {"ika": None}, tasiyici=link, heartbeat_suresi=0.0,
            heartbeat_araligi=yayinci.IHA_INIS_HEARTBEAT_ARALIGI_S)

    def test_pymavlink_eksigi_acik_nonzero_doner(self):
        hata = io.StringIO()
        with mock.patch.object(
                yayinci, "mavlink_baglantisi_ac",
                side_effect=ImportError("pymavlink gerekli")), \
             contextlib.redirect_stderr(hata):
            sonuc = yayinci.main([
                "--mavlink", "udp:127.0.0.1:14550",
                "--kanit-timeout", "5",
                "--heartbeat-sure", "0",
                "--ika", "127.0.0.1:5006",
            ])
        self.assertEqual(2, sonuc)
        self.assertIn("pymavlink gerekli", hata.getvalue())

    def test_gecersiz_udp_hedefi_mavlinki_acmadan_reddedilir(self):
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac") as baglan, \
             contextlib.redirect_stderr(io.StringIO()):
            sonuc = yayinci.main([
                "--mavlink", "udp:127.0.0.1:14550",
                "--kanit-timeout", "5",
                "--heartbeat-sure", "0",
                "--ika", "bozuk-hedef",
            ])
        self.assertEqual(4, sonuc)
        baglan.assert_not_called()

    def test_kanit_timeout_default_degil_ve_pozitif_olmalidir(self):
        for argv in (
            ["--mavlink", "udp:x", "--ika", "127.0.0.1:5006"],
            ["--mavlink", "udp:x", "--kanit-timeout", "0",
             "--ika", "127.0.0.1:5006"],
        ):
            with self.subTest(argv=argv), \
                 contextlib.redirect_stderr(io.StringIO()), \
                 self.assertRaises(SystemExit) as yakalanan:
                yayinci.main(argv)
            self.assertEqual(2, yakalanan.exception.code)

    def test_help_pymavlink_olmadan_calismaya_devam_eder(self):
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(SystemExit, "0"):
                yayinci.main(["--help"])


if __name__ == "__main__":
    unittest.main()
