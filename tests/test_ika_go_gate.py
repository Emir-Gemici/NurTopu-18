"""NEDEN: Geçerli OPEN_ROUTE tek başına İKA'yı hareket ettirmemeli; gerçek UDP
çiftinde yalnız YKS'nin hedefli IKA_GO komutu sürüş kapısını açmalıdır.
"""

import os
import sys
import subprocess
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "simulation" / "scripts"))

import ika_nav  # noqa: E402
import link as link_modulu  # noqa: E402
import navitas_sim  # noqa: E402
import yks_gui  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import (FrameReader, command, encode, iha_landed,
                      open_route)  # noqa: E402


def _ack_bekle(link, ref_seq=None, timeout=1.5):
    okuyucu = FrameReader()
    son = time.monotonic() + timeout
    while time.monotonic() < son:
        veri, _ = link.recv()
        for mesaj in okuyucu.feed(veri) if veri else []:
            if (mesaj.get("type") == "ACK"
                    and (ref_seq is None or mesaj.get("ref") == ref_seq)):
                return mesaj
    raise AssertionError(f"seq={ref_seq!r} için ACK gelmedi")


class IkaGoGateTests(unittest.TestCase):
    @staticmethod
    def _yks_olustur(link, ika_peer=None):
        arayuz = object.__new__(yks_gui.YksArayuz)
        arayuz.link = link
        arayuz.son_adr = {} if ika_peer is None else {"ika": ika_peer}
        arayuz.sabit_adr = {} if ika_peer is None else {"ika": ika_peer}
        arayuz._logla = mock.Mock()
        # K4: ika_baslat artık ACK'lı tekrar makinesi üzerinden gönderir
        arayuz.ika_go_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.IKA_GO_TEKRAR_ARALIGI_S,
            yks_gui.IKA_GO_TEKRAR_UST_SINIRI)
        return arayuz

    def test_gercek_udp_ika_go_oncesi_hareket_yok_sonrasi_var(self):
        alici_hazir = threading.Event()
        manuel_bekleme_basladi = threading.Event()
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
            korumali_gonder = kwargs["rota_korumali_gonder"]
            if not korumali_gonder(0.6, 0.6):
                raise AssertionError("IKA_GO sonrası korumalı motor kapısı açılmadı")
            navigate_cagrildi.set()
            return True

        def motor_komutu(right, left):
            if (right, left) == (0, 0):
                manuel_bekleme_basladi.set()

        iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        bekleyen = threading.Thread(target=gorev, name="ika-go-gorevi", daemon=True)
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
                with mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"), \
                     mock.patch.object(yks_gui.YksArayuz, "_tik"), \
                     mock.patch.object(yks_gui.threading.Thread, "start"):
                    yks = yks_gui.YksArayuz(
                        mock.Mock(), yks_link, ika_peer=hedef)
                yks._logla = mock.Mock()
                self.assertEqual(hedef, yks.son_adr["ika"])

                rota = open_route(
                    2,
                    0.95,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[0.0, 0.0],
                    seq=8101,
                )
                iha_link.send(encode(rota), hedef)
                _ack_bekle(iha_link, rota["seq"])
                self.assertTrue(manuel_bekleme_basladi.wait(timeout=1.0))
                self.assertFalse(navigate_cagrildi.is_set())
                self.assertTrue(bekleyen.is_alive())

                # T13 sonrası iniş bacağı önceden açık tutulur; bu testte son
                # eksik ve ölçülen bacak yalnız manuel IKA_GO olmalıdır.
                inis = iha_landed(seq=8100)
                iha_link.send(encode(inis), hedef)
                _ack_bekle(iha_link, inis["seq"])
                self.assertFalse(navigate_cagrildi.is_set())

                bilinmeyen = command("BILINMEYEN", "ika", seq=8102)
                yks_link.send(encode(bilinmeyen), hedef)
                yanlis_hedef = command("IKA_GO", "iha", seq=8103)
                yks_link.send(encode(yanlis_hedef), hedef)
                # İkinci OPEN_ROUTE ACK'i, önceki iki UDP çerçevesinin alıcı
                # thread'inde işlendiği bir sıra bariyeridir.
                rota_bariyeri = open_route(
                    2,
                    0.96,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[0.0, 0.0],
                    seq=8104,
                )
                iha_link.send(encode(rota_bariyeri), hedef)
                _ack_bekle(iha_link, rota_bariyeri["seq"])
                self.assertFalse(navigate_cagrildi.is_set())

                izin_seq = yks._cmd_gonder("IKA_GO", "ika")
                self.assertIs(type(izin_seq), int)
                ack = _ack_bekle(yks_link, izin_seq)
                self.assertEqual("ika", ack["node"])
                bekleyen.join(timeout=1.5)

                self.assertFalse(bekleyen.is_alive())
                self.assertFalse(hatalar, hatalar)
                self.assertTrue(sonuc.get("deger"))
                self.assertTrue(navigate_cagrildi.is_set())
                navigate.assert_called_once()
                motor_komutlari = [
                    c.args[:2] for c in motor.call_args_list if len(c.args) >= 2
                ]
                self.assertGreaterEqual(len(motor_komutlari), 2)
                self.assertEqual(1, sum(
                    komut != (0, 0) for komut in motor_komutlari
                ))
                self.assertIn((0.6, 0.6), motor_komutlari)
                yks._logla.assert_called_with("CMD → ika: IKA_GO", "mavi")
                print("[T12_KAPI] IHA_LANDED_onceden=1 YKS_UDP_TX=1 "
                      "IKA_GO_oncesi_hareket=0 "
                      "IKA_GO_sonrasi_nonzero_motor=1 ACK=ika exit=0")
            finally:
                iha_link.close()
                yks_link.close()
                bekleyen.join(timeout=2.5)

    def test_udp_adresi_yokken_ika_baslat_fail_closed(self):
        link = mock.Mock(spec=UDPLink)
        yks = self._yks_olustur(link)
        yks.t_iha1 = 1.0
        yks.iha_landed_seq = 1
        yks.onaylandi = True
        yks.t_ika0 = None
        yks.btn_ika_go = mock.Mock()
        yks.btn_hb = mock.Mock()

        yks.ika_baslat()

        self.assertIsNone(yks.t_ika0)
        link.send.assert_not_called()
        yks.btn_ika_go.config.assert_not_called()
        yks.btn_hb.config.assert_not_called()
        self.assertIn("UDP adresi yok", yks._logla.call_args.args[0])

    def test_bilinmeyen_cmd_iha_linkini_canlandirmaz(self):
        receiver = IkaReceiver(mock.Mock(), send_ack=False)
        receiver._handle(open_route(
            2,
            0.95,
            waypoints=[[0.0, 0.0], [1.0, 0.0]],
            ref_xy=[0.0, 0.0],
            seq=8201,
        ), ("127.0.0.1", 10001))
        receiver._handle(command("IKA_GO", "ika", seq=8202),
                         ("127.0.0.1", 10002))
        receiver._handle(iha_landed(seq=8205), ("127.0.0.1", 10001))
        receiver.link_lost = True
        onceki_rx = receiver.last_rx
        hareket = mock.Mock()

        receiver._handle(command("BILINMEYEN", "ika", seq=8203),
                         ("127.0.0.1", 10002))
        receiver._handle(command("IKA_GO", "iha", seq=8204),
                         ("127.0.0.1", 10002))

        self.assertTrue(receiver.link_lost)
        self.assertEqual(onceki_rx, receiver.last_rx)
        self.assertFalse(receiver.run_if_route_valid(hareket))
        hareket.assert_not_called()

    def test_seq_olmayan_ika_go_izin_acmaz(self):
        link = mock.Mock()
        receiver = IkaReceiver(link)

        receiver._handle(
            {"type": "CMD", "cmd": "IKA_GO", "hedef": "ika"},
            ("127.0.0.1", 10002),
        )

        self.assertFalse(receiver.ika_go)
        self.assertFalse(receiver.wait_ika_go(0))
        link.send.assert_not_called()

    def test_ika_go_ack_hatasi_aliciyi_ve_latchi_bozmaz(self):
        link = mock.Mock()
        link.send.side_effect = OSError("ACK taşıyıcısı kapalı")
        receiver = IkaReceiver(link)

        receiver._handle(command("IKA_GO", "ika", seq=8301),
                         ("127.0.0.1", 10002))

        self.assertTrue(receiver.ika_go)
        self.assertTrue(receiver.wait_ika_go(0))
        link.send.assert_called_once()

    def test_cli_ile_pinlenen_ika_adresi_heartbeat_ile_ezilmez(self):
        sabit = ("10.0.0.42", 5006)
        yks = self._yks_olustur(mock.Mock(), sabit)

        yks._dugum_adresini_ogren("ika", ("127.0.0.1", 61234))

        self.assertEqual(sabit, yks.son_adr["ika"])

    def test_udp_cli_ika_adresi_olmadan_gui_acmaz(self):
        sonuc = subprocess.run(
            [
                sys.executable,
                "-B",
                str(KOK / "comms" / "yks_gui.py"),
                "--bind",
                "127.0.0.1:0",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=5,
        )

        self.assertEqual(2, sonuc.returncode)
        self.assertIn("UDP kipinde --ika HOST:PORT zorunlu", sonuc.stderr)
        self.assertNotIn("Traceback", sonuc.stderr)

    def test_serial_ile_udp_ika_adresi_birlikte_reddedilir(self):
        sonuc = subprocess.run(
            [
                sys.executable,
                "-B",
                str(KOK / "comms" / "yks_gui.py"),
                "--serial",
                "COM_TEST",
                "--ika",
                "127.0.0.1:5006",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=5,
        )

        self.assertEqual(2, sonuc.returncode)
        self.assertIn("--serial ile --ika birlikte kullanılamaz", sonuc.stderr)
        self.assertNotIn("Traceback", sonuc.stderr)

    def test_demo_serial_link_acilmadan_reddedilir(self):
        sonuc = subprocess.run(
            [
                sys.executable,
                "-B",
                str(KOK / "comms" / "yks_gui.py"),
                "--serial",
                "COM_TEST",
                "--demo",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=5,
        )

        self.assertEqual(2, sonuc.returncode)
        self.assertIn("--demo yalnız UDP kipinde kullanılabilir", sonuc.stderr)
        self.assertNotIn("Traceback", sonuc.stderr)


if __name__ == "__main__":
    unittest.main()
