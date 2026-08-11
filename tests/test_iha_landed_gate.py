"""NEDEN: Manuel IKA_GO tek başına İKA'yı hareket ettirmemeli; gerçek İHA
iniş olayı ACK ile alınmadan atomik motor kapısı sıfır-olmayan komut açmamalıdır.
"""

import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "simulation" / "scripts"))

import ika_nav  # noqa: E402
import ika_receiver as ika_receiver_modulu  # noqa: E402
import link as link_modulu  # noqa: E402
import navitas_sim  # noqa: E402
import yks_gui  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import (FrameReader, command, decode, encode, iha_landed,
                      open_route)  # noqa: E402


def _ack_bekle(link, ref_seq, timeout=1.5):
    okuyucu = FrameReader()
    son = time.monotonic() + timeout
    while time.monotonic() < son:
        veri, _ = link.recv()
        for mesaj in okuyucu.feed(veri) if veri else []:
            if (mesaj.get("type") == "ACK"
                    and mesaj.get("ref") == ref_seq):
                return mesaj
    raise AssertionError(f"seq={ref_seq} için ACK gelmedi")


def _yks_headless(link, ika_peer):
    with mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"), \
         mock.patch.object(yks_gui.YksArayuz, "_tik"), \
         mock.patch.object(yks_gui.threading.Thread, "start"):
        arayuz = yks_gui.YksArayuz(mock.Mock(), link, ika_peer=ika_peer)
    arayuz._logla = mock.Mock()
    return arayuz


class IhaLandedGateTests(unittest.TestCase):
    def test_gercek_udp_ika_go_var_landed_yoksa_hareket_yok(self):
        alici_hazir = threading.Event()
        izin_bekleme_basladi = threading.Event()
        navigate_cagrildi = threading.Event()
        port = {}
        sonuc = {}
        hatalar = []
        gercek_udp_link = UDPLink

        def udp_link_olustur(*args, **kwargs):
            alici = gercek_udp_link(*args, **kwargs)
            port["deger"] = alici.port
            alici_hazir.set()
            return alici

        def gorev():
            try:
                sonuc["deger"] = navitas_sim.dinamik_ika_gorevi(
                    "127.0.0.1:0", timeout=2.0)
            except BaseException as exc:
                hatalar.append(exc)

        def sahte_navigate(*_args, **kwargs):
            if not kwargs["rota_korumali_gonder"](0.7, 0.7):
                raise AssertionError("İniş sonrası atomik motor kapısı açılmadı")
            navigate_cagrildi.set()
            return True

        def motor_komutu(right, left):
            if (right, left) == (0, 0):
                izin_bekleme_basladi.set()

        iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        bekleyen = threading.Thread(
            target=gorev, name="iha-landed-gorevi", daemon=True)
        with mock.patch.object(
                link_modulu, "UDPLink", side_effect=udp_link_olustur), \
             mock.patch.object(
                 ika_nav, "navigate_route", side_effect=sahte_navigate) as navigate, \
             mock.patch.object(
                 ika_nav, "send_vel", side_effect=motor_komutu) as motor:
            try:
                bekleyen.start()
                self.assertTrue(alici_hazir.wait(timeout=1.0), hatalar)
                hedef = ("127.0.0.1", port["deger"])
                yks = _yks_headless(yks_link, hedef)

                rota = open_route(
                    2,
                    0.95,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[0.0, 0.0],
                    seq=9101,
                )
                iha_link.send(encode(rota), hedef)
                _ack_bekle(iha_link, rota["seq"])
                self.assertTrue(izin_bekleme_basladi.wait(timeout=1.0))

                ika_go_seq = yks._cmd_gonder("IKA_GO", "ika")
                self.assertIs(type(ika_go_seq), int)
                _ack_bekle(yks_link, ika_go_seq)
                self.assertFalse(navigate_cagrildi.is_set())
                self.assertTrue(bekleyen.is_alive())
                self.assertFalse(any(
                    c.args[:2] != (0, 0) for c in motor.call_args_list
                    if len(c.args) >= 2
                ))

                yayin_dursun = threading.Event()
                yayin_dursun.set()
                self.assertTrue(navitas_sim.iha_inisini_yayinla(
                    {"ika": hedef},
                    heartbeat_until=yayin_dursun,
                    repeat=6,
                    interval=0.05,
                ))
                bekleyen.join(timeout=1.5)

                self.assertFalse(bekleyen.is_alive())
                self.assertFalse(hatalar, hatalar)
                self.assertTrue(sonuc.get("deger"))
                navigate.assert_called_once()
                motor_komutlari = [
                    c.args[:2] for c in motor.call_args_list if len(c.args) >= 2
                ]
                self.assertEqual(1, sum(
                    komut != (0, 0) for komut in motor_komutlari
                ))
                self.assertIn((0.7, 0.7), motor_komutlari)
                print("[T13_KAPI] IKA_GO=1 LANDED_oncesi_nonzero=0 "
                      "LANDED_sonrasi_nonzero=1 ACK=ika exit=0")
            finally:
                iha_link.close()
                yks_link.close()
                bekleyen.join(timeout=2.5)

    def test_landed_ve_ika_go_gelis_sirasi_onemsizdir(self):
        receiver = IkaReceiver(mock.Mock(), send_ack=False)
        receiver._handle(iha_landed(seq=9201), ("127.0.0.1", 10001))
        self.assertFalse(receiver.wait_surus_izni(0))

        receiver._handle(command("IKA_GO", "ika", seq=9202),
                         ("127.0.0.1", 10002))

        self.assertTrue(receiver.wait_surus_izni(0))

    def test_deadline_sonrasi_iki_izin_de_hareketi_acmaz(self):
        timeout = 0.08
        alici_hazir = threading.Event()
        dogrulama_deadline_sonrasi = threading.Event()
        dogrulamaya_devam = threading.Event()
        port = {}
        yakalanan = {}
        sonuc = {}
        hatalar = []
        baslangic = {}
        gercek_udp_link = UDPLink
        gercek_receiver = IkaReceiver
        gercek_dogrula = ika_nav.route_to_world_waypoints

        def udp_link_olustur(*args, **kwargs):
            alici = gercek_udp_link(*args, **kwargs)
            port["deger"] = alici.port
            alici_hazir.set()
            return alici

        def receiver_olustur(*args, **kwargs):
            receiver = gercek_receiver(*args, **kwargs)
            yakalanan["receiver"] = receiver
            return receiver

        def yavas_dogrula(route):
            if not dogrulama_deadline_sonrasi.is_set():
                hedef = baslangic["t"] + timeout + 0.05
                kalan = hedef - time.monotonic()
                if kalan > 0:
                    time.sleep(kalan)
                dogrulama_deadline_sonrasi.set()
                dogrulamaya_devam.wait(timeout=1.0)
            return gercek_dogrula(route)

        def gorev():
            try:
                baslangic["t"] = time.monotonic()
                sonuc["deger"] = navitas_sim.dinamik_ika_gorevi(
                    "127.0.0.1:0", timeout=timeout)
            except BaseException as exc:
                hatalar.append(exc)

        sender = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        worker = threading.Thread(target=gorev, daemon=True)
        with mock.patch.object(
                link_modulu, "UDPLink", side_effect=udp_link_olustur), \
             mock.patch.object(
                 ika_receiver_modulu, "IkaReceiver",
                 side_effect=receiver_olustur), \
             mock.patch.object(
                 ika_nav, "route_to_world_waypoints",
                 side_effect=yavas_dogrula), \
             mock.patch.object(
                 ika_nav, "navigate_route", return_value=True) as navigate, \
             mock.patch.object(ika_nav, "send_vel"):
            try:
                worker.start()
                self.assertTrue(alici_hazir.wait(timeout=1.0), hatalar)
                hedef = ("127.0.0.1", port["deger"])
                rota = open_route(
                    2,
                    0.95,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[0.0, 0.0],
                    seq=9251,
                )
                sender.send(encode(rota), hedef)
                self.assertTrue(
                    dogrulama_deadline_sonrasi.wait(timeout=1.0), hatalar)

                sender.send(
                    encode(command("IKA_GO", "ika", seq=9252)), hedef)
                sender.send(encode(iha_landed(seq=9253)), hedef)
                alindi_deadline = time.monotonic() + 1.0
                receiver = yakalanan["receiver"]
                while (time.monotonic() < alindi_deadline
                       and not (receiver.ika_go and receiver.iha_landed)):
                    time.sleep(0.005)
                self.assertTrue(receiver.ika_go)
                self.assertTrue(receiver.iha_landed)
                self.assertGreater(receiver.ika_go_monotonic,
                                   baslangic["t"] + timeout)
                self.assertGreater(receiver.iha_landed_monotonic,
                                   baslangic["t"] + timeout)
                dogrulamaya_devam.set()
                worker.join(timeout=1.0)

                self.assertFalse(worker.is_alive())
                self.assertFalse(hatalar, hatalar)
                self.assertIs(sonuc.get("deger"), False)
                navigate.assert_not_called()
                print("[T13_DEADLINE] timeout_sonrasi_latch=2 "
                      "navigate_calls=0 sonuc=guvenli_ret")
            finally:
                dogrulamaya_devam.set()
                sender.close()
                worker.join(timeout=1.0)

    def test_bozuk_landed_latch_ve_link_acmaz(self):
        receiver = IkaReceiver(mock.Mock(), send_ack=False)
        receiver.link_lost = True
        onceki_rx = receiver.last_rx

        receiver._handle(
            {"type": "IHA_LANDED", "node": "yks", "seq": 9301},
            ("127.0.0.1", 10001),
        )
        receiver._handle(
            {"type": "IHA_LANDED", "node": "iha"},
            ("127.0.0.1", 10001),
        )

        self.assertFalse(receiver.iha_landed)
        self.assertTrue(receiver.link_lost)
        self.assertEqual(onceki_rx, receiver.last_rx)

    def test_ucus_basarisizsa_landed_yayinlanmaz(self):
        with mock.patch.object(
                navitas_sim.iha_flight, "fly", return_value=False), \
             mock.patch.object(navitas_sim, "iha_inisini_yayinla") as yayin:
            sonuc = navitas_sim.iha_ucus_ve_inis_gorevi(
                1.0, {"ika": ("127.0.0.1", 5006)})

        self.assertFalse(sonuc)
        yayin.assert_not_called()

    def test_ucus_basarili_ama_landed_ack_yoksa_gorev_basarisizdir(self):
        with mock.patch.object(
                navitas_sim.iha_flight, "fly", return_value=True), \
             mock.patch.object(
                 navitas_sim, "iha_inisini_yayinla", return_value=False) as yayin:
            sonuc = navitas_sim.iha_ucus_ve_inis_gorevi(
                1.0, {"ika": ("127.0.0.1", 5006)})

        self.assertFalse(sonuc)
        yayin.assert_called_once()

    def test_yks_landed_olayini_uretmeyip_ackler(self):
        link = mock.Mock()
        yks = _yks_headless(link, ("127.0.0.1", 5006))
        yks.iha_indi = mock.Mock()
        olay = iha_landed(seq=9401)
        kaynak = ("127.0.0.1", 5010)

        yks._mesaj_isle(olay, kaynak)

        link.send.assert_called_once()
        ack_verisi, ack_hedefi = link.send.call_args.args
        self.assertEqual(kaynak, ack_hedefi)
        ack_mesaji = decode(ack_verisi)
        self.assertEqual("ACK", ack_mesaji["type"])
        self.assertEqual(olay["seq"], ack_mesaji["ref"])
        self.assertEqual("yks", ack_mesaji["node"])
        yks.iha_indi.assert_called_once_with()

    def test_yks_manuel_iha_indi_kaydi_ika_go_kilidini_acmaz(self):
        yks = object.__new__(yks_gui.YksArayuz)
        yks.t_iha1 = 1.0                 # operatör düğmesi yalnız kayıt oluşturdu
        yks.iha_landed_seq = None        # üretim protokol kanıtı yok
        yks.onaylandi = True
        yks.t_ika0 = None
        yks._cmd_gonder = mock.Mock()
        yks._logla = mock.Mock()

        yks.ika_baslat()

        yks._cmd_gonder.assert_not_called()
        self.assertIsNone(yks.t_ika0)
        self.assertIn("IHA_LANDED", yks._logla.call_args.args[0])

    def test_yks_protokol_latchi_operator_dizisi_olmadan_ika_go_yayinlar(self):
        link = mock.Mock()
        yks = _yks_headless(link, ("127.0.0.1", 5006))
        yks.onaylandi = True
        yks.btn_ika_go = mock.Mock()
        yks.btn_hb = mock.Mock()

        yks._mesaj_isle(iha_landed(seq=9501), ("127.0.0.1", 5010))

        self.assertIsNone(yks.t_iha0)
        self.assertIsNone(yks.t_iha1)
        self.assertEqual(9501, yks.iha_landed_seq)
        yks._logla.reset_mock()
        link.send.reset_mock()
        with mock.patch.object(yks_gui.time, "time", return_value=123.0):
            yks.ika_baslat()

        link.send.assert_called_once()
        komut_verisi, komut_hedefi = link.send.call_args.args
        komut_mesaji = decode(komut_verisi)
        self.assertEqual("CMD", komut_mesaji["type"])
        self.assertEqual("IKA_GO", komut_mesaji["cmd"])
        self.assertEqual("ika", komut_mesaji["hedef"])
        self.assertEqual(("127.0.0.1", 5006), komut_hedefi)
        self.assertEqual(123.0, yks.t_ika0)
        self.assertFalse(any(
            "REDDEDİLDİ" in cagri.args[0]
            for cagri in yks._logla.call_args_list
        ))

    def test_yks_landed_yokken_operator_dizisi_olmadan_ika_go_reddedilir(self):
        yks = object.__new__(yks_gui.YksArayuz)
        yks.t_iha0 = None
        yks.t_iha1 = None
        yks.iha_landed_seq = None
        yks.onaylandi = True
        yks.t_ika0 = None
        yks._cmd_gonder = mock.Mock()
        yks._logla = mock.Mock()

        yks.ika_baslat()

        yks._cmd_gonder.assert_not_called()
        self.assertIsNone(yks.t_ika0)
        self.assertIn("REDDEDİLDİ", yks._logla.call_args.args[0])

    def test_landed_sonrasi_heartbeat_linki_canli_tutar(self):
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        receiver = IkaReceiver(alici_link, hb_timeout=0.8).start()
        dur = threading.Event()
        sonuc = {}

        def yayinla():
            sonuc["deger"] = navitas_sim.iha_inisini_yayinla(
                {"ika": ("127.0.0.1", alici_link.port)},
                heartbeat_until=dur,
                repeat=6,
                interval=0.05,
            )

        thread = threading.Thread(target=yayinla, daemon=True)
        try:
            thread.start()
            self.assertTrue(receiver.wait_iha_landed(1.0))
            time.sleep(1.1)
            self.assertTrue(receiver.link_ok)
        finally:
            dur.set()
            thread.join(timeout=1.0)
            receiver.stop()
            alici_link.close()

        self.assertFalse(thread.is_alive())
        self.assertTrue(sonuc.get("deger"))

    def test_yks_ack_eksikken_de_ika_bitene_dek_heartbeat_surer(self):
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        sessiz_yks = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        receiver = IkaReceiver(alici_link, hb_timeout=0.8).start()
        dur = threading.Event()
        sonuc = {}

        def yayinla():
            sonuc["deger"] = navitas_sim.iha_inisini_yayinla(
                {
                    "ika": ("127.0.0.1", alici_link.port),
                    "yks": ("127.0.0.1", sessiz_yks.port),
                },
                heartbeat_until=dur,
                repeat=8,
                interval=0.05,
            )

        thread = threading.Thread(target=yayinla, daemon=True)
        try:
            thread.start()
            self.assertTrue(receiver.wait_iha_landed(1.0))
            time.sleep(1.1)
            self.assertTrue(receiver.link_ok)
            self.assertTrue(thread.is_alive())
        finally:
            dur.set()
            thread.join(timeout=1.0)
            receiver.stop()
            alici_link.close()
            sessiz_yks.close()

        self.assertFalse(thread.is_alive())
        self.assertIs(sonuc.get("deger"), False)


if __name__ == "__main__":
    unittest.main()
