"""NEDEN (Faz B · D-393 yazilim yarisi · sartname §2.2.4/§6.4 · CONTRACTS
§6.6): YKS PARACHUTE'u ACK gelene dek tekrarliyor ama IHA'da CMD dinleyen uc
yoktu. `comms/iha_komut_alici.py` YKS CMD'sini Pixhawk'a COMMAND_LONG ile
aktarir ve YALNIZ aktarim basariliysa ACK doner. Burada kilitlenen sey ACK'in
"aldim VE yaptim" anlami ve IKA_GO idempotentlik kalibidir.

Bilesenler GERCEKTIR: UDP loopback (`UDPLink`), `loop://` seri hat
(`SerialLink`), `FrameReader`/`protocol`, ve bir testte gercek pymavlink
`udp:` baglantisi + `scripts/sahte_pixhawk.py` (gercek MAVLink cerceveleri).
Mock yalniz donanim ucunda: `mav.mav.command_long_send`.
"""
import contextlib
import io
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from pymavlink import mavutil  # noqa: E402

import iha_komut_alici as modul  # noqa: E402
from iha_komut_alici import IhaKomutAlici  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import FrameReader, command, encode, heartbeat  # noqa: E402

HEDEF_SYSID = 7          # varsayilan (1) DEGIL: degerin gectigi gorulsun
HEDEF_COMPONENT = 3
YEREL = "127.0.0.1"
# MAV_CMD_COMPONENT_ARM_DISARM param1 anlami (MAVLink common.xml): 1 = arm,
# 0 = disarm. pymavlink'te adli sabiti yok; modulun kendi sabitinden DEGIL,
# spesifikasyondan alinir ki ters cevrilmis bir sabit testi gecemesin.
ARM_PARAM1 = 1
DISARM_PARAM1 = 0
BEKLENEN_BOS_PARAMLAR = (modul.MAVLINK_PARAM_KULLANILMIYOR,) * 6


class _SahteSaat:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _sahte_mav(side_effect=None):
    """Donanim ucu mock'u: yalniz command_long_send + bos gelen kutusu."""
    m = mock.Mock(name="mav")
    m.mav.command_long_send = mock.Mock(name="command_long_send",
                                        side_effect=side_effect)
    m.recv_match = mock.Mock(name="recv_match", return_value=None)
    return m


class _UdpKurulum:
    """YKS <-> IHA alicisi, gercek UDP loopback."""

    def __init__(self, mav, **kw):
        self.alici_link = UDPLink(bind=(YEREL, 0), timeout=0.2)
        self.yks = UDPLink(bind=(YEREL, 0), timeout=0.3)
        self.alici_adr = (YEREL, self.alici_link.port)
        kw.setdefault("target_system", HEDEF_SYSID)
        kw.setdefault("target_component", HEDEF_COMPONENT)
        self.alici = IhaKomutAlici(self.alici_link, mav, **kw)
        self.log = io.StringIO()

    def gonder(self, msg):
        self.yks.send(encode(msg), self.alici_adr)

    def tur(self):
        with contextlib.redirect_stdout(self.log), \
                contextlib.redirect_stderr(self.log):
            return self.alici.poll()

    def acklar(self, sure=0.3, adet=1):
        reader = FrameReader()
        gelen = []
        bitis = time.monotonic() + sure
        while len(gelen) < adet and time.monotonic() < bitis:
            d, _ = self.yks.recv()
            if d:
                gelen.extend(m for m in reader.feed(d)
                             if m.get("type") == "ACK")
        return gelen

    def kapat(self):
        self.alici_link.close()
        self.yks.close()


def _ack_dogrula(test, a, seq):
    test.assertEqual("ACK", a.get("type"))
    test.assertEqual(seq, a.get("ref"))
    test.assertEqual("iha", a.get("node"))
    test.assertEqual("CMD", a.get("ref_tip"))


class TestKomutAktarimiVeAck(unittest.TestCase):

    def setUp(self):
        self.kurulum = None

    def tearDown(self):
        if self.kurulum is not None:
            self.kurulum.kapat()

    def test_1_parachute_command_long_send_tam_argumanlarla_ve_ack_doner(self):
        """PARACHUTE -> command_long_send(sys, comp, MAV_CMD_DO_PARACHUTE, 0,
        PARACHUTE_RELEASE, 0x6) TAM argumanlarla; ACK(ref=seq, node=iha,
        ref_tip=CMD) gonderene doner; log monoton (enjekte) saatle yazilir."""
        mav = _sahte_mav()
        saat = _SahteSaat(1000.0)
        k = self.kurulum = _UdpKurulum(mav, saat=saat)
        k.gonder(command("PARACHUTE", "iha", seq=41))
        self.assertEqual([True], k.tur())
        mav.mav.command_long_send.assert_called_once_with(
            HEDEF_SYSID, HEDEF_COMPONENT,
            mavutil.mavlink.MAV_CMD_DO_PARACHUTE,
            modul.MAVLINK_ONAY_ILK_GONDERIM,
            mavutil.mavlink.PARACHUTE_RELEASE,
            *BEKLENEN_BOS_PARAMLAR)
        acks = k.acklar()
        self.assertEqual(1, len(acks), acks)
        _ack_dogrula(self, acks[0], 41)
        self.assertIn("[IHA_KOMUT] t=1000.000", k.log.getvalue())
        self.assertEqual(1, k.alici.sayac["aktarilan"])
        self.assertEqual(1, k.alici.sayac["ack"])

    def test_2_command_long_send_istisna_firlatirsa_ack_yok(self):
        """Aktarim istisnasi -> ACK YOK (KIRMIZI log); YKS tekrarlayacak."""
        mav = _sahte_mav(side_effect=RuntimeError("seri hat kapali"))
        k = self.kurulum = _UdpKurulum(mav)
        k.gonder(command("PARACHUTE", "iha", seq=42))
        self.assertEqual([False], k.tur())
        mav.mav.command_long_send.assert_called_once()
        self.assertEqual([], k.acklar())
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertIn("ACK YOK", log)
        self.assertEqual(0, k.alici.sayac["ack"])

    def test_3_mav_none_ise_aktarim_yok_ack_yok(self):
        """MAVLink baglantisi yokken komut ne aktarilir ne ACK'lanir."""
        k = self.kurulum = _UdpKurulum(None)
        k.gonder(command("PARACHUTE", "iha", seq=43))
        self.assertEqual([False], k.tur())
        self.assertEqual([], k.acklar())
        self.assertIn("ACK YOK", k.log.getvalue())
        self.assertEqual(0, k.alici.sayac["aktarilan"])

    def test_4_ayni_seq_ikinci_kez_mavlink_tek_ack_iki(self):
        """Mukerrer (cmd, seq): command_long_send TEK, ACK IKI (IKA_GO kalibi)."""
        mav = _sahte_mav()
        k = self.kurulum = _UdpKurulum(mav)
        msg = command("PARACHUTE", "iha", seq=5)
        k.gonder(msg)
        self.assertEqual([True], k.tur())
        k.gonder(msg)
        self.assertEqual([True], k.tur())
        self.assertEqual(1, mav.mav.command_long_send.call_count)
        acks = k.acklar(sure=0.6, adet=2)
        self.assertEqual(2, len(acks), acks)
        for a in acks:
            _ack_dogrula(self, a, 5)
        self.assertEqual(1, k.alici.sayac["mukerrer"])

    def test_5_hedefi_ika_olan_cmd_ve_cmd_disi_mesaj_yok_sayilir(self):
        """hedef=ika olan CMD ve CMD olmayan mesaj: aktarim yok, ACK yok."""
        mav = _sahte_mav()
        k = self.kurulum = _UdpKurulum(mav)
        k.gonder(command("PARACHUTE", "ika", seq=44))
        k.gonder(command("IKA_GO", "ika", seq=45))
        k.gonder(heartbeat("yks", seq=46))
        sonuc = []
        for _ in range(3):
            sonuc += k.tur()
        self.assertEqual([False, False, False], sonuc)
        mav.mav.command_long_send.assert_not_called()
        self.assertEqual([], k.acklar())
        self.assertEqual(0, k.alici.sayac["cmd"])

    def test_6_arm_ve_disarm_param1_bir_ve_sifir(self):
        """ARM -> MAV_CMD_COMPONENT_ARM_DISARM param1=1; DISARM -> param1=0."""
        mav = _sahte_mav()
        k = self.kurulum = _UdpKurulum(mav)
        k.gonder(command("ARM", "iha", seq=10))
        k.gonder(command("DISARM", "iha", seq=11))
        sonuc = []
        for _ in range(2):
            sonuc += k.tur()
        self.assertEqual([True, True], sonuc)
        self.assertEqual([
            mock.call(HEDEF_SYSID, HEDEF_COMPONENT,
                      mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                      modul.MAVLINK_ONAY_ILK_GONDERIM, ARM_PARAM1,
                      *BEKLENEN_BOS_PARAMLAR),
            mock.call(HEDEF_SYSID, HEDEF_COMPONENT,
                      mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                      modul.MAVLINK_ONAY_ILK_GONDERIM, DISARM_PARAM1,
                      *BEKLENEN_BOS_PARAMLAR),
        ], mav.mav.command_long_send.call_args_list)
        acks = k.acklar(sure=0.6, adet=2)
        self.assertEqual([10, 11], sorted(a["ref"] for a in acks))

    def test_7_bilinmeyen_cmd_aktarilmaz_ve_ack_uretmez(self):
        """Bilinmeyen komut loglanir; ACK 'aldim ve yaptim' demek, gonderilmez."""
        mav = _sahte_mav()
        k = self.kurulum = _UdpKurulum(mav)
        k.gonder(command("FIRLAT", "iha", seq=47))
        self.assertEqual([False], k.tur())
        mav.mav.command_long_send.assert_not_called()
        self.assertEqual([], k.acklar())
        log = k.log.getvalue()
        self.assertIn("bilinmeyen CMD", log)
        self.assertIn("ACK YOK", log)
        self.assertEqual(1, k.alici.sayac["bilinmeyen"])

    def test_8_basarisiz_aktarim_hafizaya_yazilmaz_tekrarda_yeniden_denenir(self):
        """Idempotentlik hafizasi yalniz BASARILI aktarimi tutar: ilk deneme
        patlarsa ayni seq'in tekrari yeniden aktarilir; ACK ancak o zaman."""
        mav = _sahte_mav(side_effect=[RuntimeError("gecici"), None])
        k = self.kurulum = _UdpKurulum(mav)
        msg = command("PARACHUTE", "iha", seq=6)
        k.gonder(msg)
        self.assertEqual([False], k.tur())
        k.gonder(msg)
        self.assertEqual([True], k.tur())
        self.assertEqual(2, mav.mav.command_long_send.call_count)
        acks = k.acklar(sure=0.6, adet=2)
        self.assertEqual(1, len(acks), acks)
        _ack_dogrula(self, acks[0], 6)

    def test_9_udp_sunucu_akran_gorulmeden_ack_yok_gorulunce_aktarilir(self):
        """pymavlink `udp:` sunucusu akran gormeden write()'i sessizce dusurur;
        alici bunu 'aktarilmadi, ACK YOK' sayar; akran gorulunce aktarir."""
        istemciler = set()
        mav = SimpleNamespace(udp_server=True, clients=istemciler,
                              mav=mock.Mock(), recv_match=lambda **k: None)
        k = self.kurulum = _UdpKurulum(mav)
        msg = command("PARACHUTE", "iha", seq=48)
        k.gonder(msg)
        self.assertEqual([False], k.tur())
        mav.mav.command_long_send.assert_not_called()
        self.assertEqual([], k.acklar())
        self.assertIn("ACK YOK", k.log.getvalue())
        istemciler.add((YEREL, 14550))          # Pixhawk'tan ilk paket geldi
        k.gonder(msg)
        self.assertEqual([True], k.tur())
        mav.mav.command_long_send.assert_called_once()
        acks = k.acklar()
        self.assertEqual(1, len(acks), acks)
        _ack_dogrula(self, acks[0], 48)

    def test_10_bozuk_seq_ack_uretmez(self):
        """seq bool/str/eksik olan CMD: ACK ref uretilemez, aktarim da yok."""
        mav = _sahte_mav()
        k = self.kurulum = _UdpKurulum(mav)
        bozuk = command("PARACHUTE", "iha", seq=1)
        bozuk["seq"] = True
        k.gonder(bozuk)
        eksik = command("PARACHUTE", "iha", seq=1)
        del eksik["seq"]
        k.gonder(eksik)
        sonuc = []
        for _ in range(2):
            sonuc += k.tur()
        self.assertEqual([False, False], sonuc)
        mav.mav.command_long_send.assert_not_called()
        self.assertEqual([], k.acklar())


class TestSeriHatVeDongu(unittest.TestCase):

    def test_11_seri_hatta_ack_link_send_ile_yayinlanir(self):
        """SiK (adr None) hattinda ACK `link.send(data)` ile ortama yazilir —
        gercek `loop://` bayt akisi uzerinden."""
        mav = _sahte_mav()
        link = SerialLink("loop://", modul.VARSAYILAN_BAUD, timeout=0.1)
        try:
            alici = IhaKomutAlici(link, mav, target_system=HEDEF_SYSID,
                                  target_component=HEDEF_COMPONENT)
            link.ser.write(encode(command("PARACHUTE", "iha", seq=77)))
            with contextlib.redirect_stdout(io.StringIO()):
                sonuc = alici.poll()
            self.assertEqual([True], sonuc)
            mav.mav.command_long_send.assert_called_once()
            ham = link.ser.read(4096)
            acks = [m for m in FrameReader().feed(ham)
                    if m.get("type") == "ACK"]
            self.assertEqual(1, len(acks), ham)
            _ack_dogrula(self, acks[0], 77)
        finally:
            link.close()

    def test_12_calistir_dongusu_gercek_udp_ile_ack_doner_ve_durdur_ile_cikar(self):
        """calistir(): FrameReader+link.recv dongusu ayri thread'de kosarken
        PARACHUTE'a ACK doner; durdur() donguyu bitirir."""
        mav = _sahte_mav()
        k = _UdpKurulum(mav)
        cikti = io.StringIO()
        try:
            with contextlib.redirect_stdout(cikti), \
                    contextlib.redirect_stderr(cikti):
                thr = threading.Thread(target=k.alici.calistir, daemon=True)
                thr.start()
                k.gonder(command("PARACHUTE", "iha", seq=90))
                acks = k.acklar(sure=2.0)
                k.alici.durdur()
                thr.join(timeout=2.0)
            self.assertFalse(thr.is_alive())
            self.assertEqual(1, len(acks), acks)
            _ack_dogrula(self, acks[0], 90)
            mav.mav.command_long_send.assert_called_once()
        finally:
            k.kapat()

    def test_13_gercek_mavlink_hedefi_sahte_pixhawk_command_long_alir(self):
        """Gercek pymavlink `udp:` ucu + sahte_pixhawk (gercek MAVLink
        cerceveleri): PARACHUTE, Pixhawk tarafinda COMMAND_LONG olarak
        MAV_CMD_DO_PARACHUTE/PARACHUTE_RELEASE ile ALINIR ve ACK doner."""
        from sahte_pixhawk import SahtePixhawk
        mav = mavutil.mavlink_connection(f"udp:{YEREL}:0")
        k = None
        try:
            port = mav.port.getsockname()[1]
            self.assertTrue(port > 0)
            k = _UdpKurulum(mav, target_system=HEDEF_SYSID,
                            target_component=HEDEF_COMPONENT)
            with SahtePixhawk(f"udpout:{YEREL}:{port}", senaryo="ucus") as sp:
                # Akran adresi ancak gelen kutusu bosaltilinca ogrenilir.
                for _ in range(25):
                    k.tur()
                    if modul.mav_hedefi_biliniyor_mu(mav):
                        break
                self.assertTrue(modul.mav_hedefi_biliniyor_mu(mav),
                                "sahte pixhawk'tan paket gelmedi")
                k.gonder(command("PARACHUTE", "iha", seq=91))
                self.assertEqual([True], k.tur())
                acks = k.acklar()
                self.assertEqual(1, len(acks), acks)
                _ack_dogrula(self, acks[0], 91)
                gelen = sp._mav.recv_match(type="COMMAND_LONG", blocking=True,
                                           timeout=3.0)
                self.assertIsNotNone(gelen, "Pixhawk COMMAND_LONG almadi")
                self.assertEqual(mavutil.mavlink.MAV_CMD_DO_PARACHUTE,
                                 gelen.command)
                self.assertEqual(mavutil.mavlink.PARACHUTE_RELEASE,
                                 gelen.param1)
                self.assertEqual(HEDEF_SYSID, gelen.target_system)
                self.assertEqual(HEDEF_COMPONENT, gelen.target_component)
                self.assertEqual(modul.MAVLINK_ONAY_ILK_GONDERIM,
                                 gelen.confirmation)
        finally:
            if k is not None:
                k.kapat()
            mav.close()


class TestCli(unittest.TestCase):

    def test_14_cli_mavlink_zorunlu(self):
        """--mavlink verilmeden surec baslamaz (argparse hatasi, cikis 2)."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                modul.main(["--bind", f"{YEREL}:0"])
        self.assertEqual(2, cm.exception.code)

    def test_15_cli_mavlink_acilamazsa_cikis_2_ve_tasiyici_acilmaz(self):
        """MAVLink acilamazsa surec 2 ile cikar; UDP tasiyici hic kurulmaz."""
        with mock.patch.object(modul, "mavlink_baglantisi_ac",
                               side_effect=ConnectionError("yok")), \
                mock.patch.object(modul, "UDPLink") as udp, \
                contextlib.redirect_stderr(io.StringIO()):
            kod = modul.main(["--mavlink", "udp:127.0.0.1:14560",
                              "--bind", f"{YEREL}:0"])
        self.assertEqual(2, kod)
        udp.assert_not_called()

    def test_16_cli_sysid_araligi_denetlenir(self):
        """--sysid 0 ya da 256 kabul edilmez (MAVLink 1..255)."""
        for kotu in ("0", "256"):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    modul.main(["--mavlink", "udp:127.0.0.1:14560",
                                "--sysid", kotu])
            self.assertEqual(2, cm.exception.code)


if __name__ == "__main__":
    unittest.main()
