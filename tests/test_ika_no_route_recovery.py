"""Geçici NO_ROUTE sonrasında İKA görevinin toparlanma testi."""

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
import ika_receiver  # noqa: E402,F401  (patch öncesi gerçek UDPLink'i yükle)
import link as link_modulu  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import FrameReader, encode, open_route, rota_yok  # noqa: E402


def _ack_bekle(link, ref_seq, timeout=1.5):
    okuyucu = FrameReader()
    son = time.monotonic() + timeout
    while time.monotonic() < son:
        veri, _ = link.recv()
        for mesaj in okuyucu.feed(veri) if veri else []:
            if mesaj.get("type") == "ACK" and mesaj.get("ref") == ref_seq:
                return
    raise AssertionError(f"seq={ref_seq} için ACK gelmedi")


def _rota_beklemeyi_baslat(timeout):
    """Gerçek alıcının ephemeral porta bind oluşunu event ile bildir."""
    alici_hazir = threading.Event()
    port = {}
    sonuc = {}
    hatalar = []
    baslangic = {}
    gercek_udp_link = UDPLink

    def udp_link_olustur(*args, **kwargs):
        alici_link = gercek_udp_link(*args, **kwargs)
        port["deger"] = alici_link.port
        alici_hazir.set()
        return alici_link

    def rota_bekle():
        try:
            baslangic["t"] = time.monotonic()
            sonuc["alindi"] = ika_nav.wait_open_route_from_comms(
                bind="127.0.0.1:0", timeout=timeout, keep_receiver=True)
        except BaseException as exc:  # Thread hatasını ana teste taşı.
            hatalar.append(exc)

    bekleyen = threading.Thread(target=rota_bekle, daemon=True)
    with mock.patch.object(
            link_modulu, "UDPLink", side_effect=udp_link_olustur):
        bekleyen.start()
        if not alici_hazir.wait(timeout=1.0):
            raise AssertionError(f"İKA alıcısı başlayamadı: {hatalar}")

    return bekleyen, sonuc, hatalar, port["deger"], baslangic["t"]


def _sonuctaki_aliciyi_kapat(sonuc):
    alindi = sonuc.get("alindi")
    if isinstance(alindi, tuple) and len(alindi) == 2:
        receiver = alindi[1]
        receiver.stop()
        receiver.link.close()


class GeciciNoRouteToparlanmaTests(unittest.TestCase):
    def test_no_route_sonrasi_open_route_surulur(self):
        bekleyen, sonuc, bekleyen_hatalari, port, _ = (
            _rota_beklemeyi_baslat(timeout=3.0))

        link = UDPLink(bind=("127.0.0.1", 0),
                       peer=("127.0.0.1", port), timeout=0.1)
        try:
            ret = rota_yok("KAPALI_DAR", "geçici maske", seq=7001)
            link.send(encode(ret))
            _ack_bekle(link, ret["seq"])

            # Eski hata burada NO_ROUTE'u döndürüp alıcıyı kapatıyordu.
            time.sleep(0.30)
            self.assertTrue(bekleyen.is_alive(),
                            "Geçici NO_ROUTE beklemeyi erken sonlandırdı")
            self.assertNotIn("alindi", sonuc)

            rota = open_route(
                2,
                0.92,
                waypoints=[[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
                ref_xy=[10.0, 20.0],
                seq=7002,
            )
            link.send(encode(rota))
            _ack_bekle(link, rota["seq"])
            bekleyen.join(timeout=2.0)

            self.assertFalse(bekleyen.is_alive(), "Rota bekleme thread'i kapanmadı")
            self.assertFalse(bekleyen_hatalari, bekleyen_hatalari)
            self.assertIsInstance(sonuc.get("alindi"), tuple)
            route, receiver = sonuc["alindi"]
            self.assertEqual("OPEN_ROUTE", route["type"])
            self.assertEqual(7002, route["seq"])
            self.assertIsNone(receiver.last_no_route)

            with mock.patch.object(ika_nav, "navigate", return_value=True) as sur:
                self.assertTrue(
                    ika_nav.navigate_route(
                        route, verbose=False, link_ok=lambda: receiver.link_ok))
                sur.assert_called_once()

            # keep_receiver=True sahipliği devrettikten sonra alıcının gerçekten
            # canlı kaldığını yeni karar + ACK ile davranışsal olarak doğrula.
            yeni_rota = open_route(
                2,
                0.95,
                waypoints=[[0.0, 0.0], [1.0, 0.0]],
                ref_xy=[10.0, 20.0],
                seq=7003,
            )
            link.send(encode(yeni_rota))
            _ack_bekle(link, yeni_rota["seq"])
            guncel_rota, guncel_no_route, _, _ = receiver.decision_snapshot()
            self.assertEqual(7003, guncel_rota["seq"])
            self.assertIsNone(guncel_no_route)
        finally:
            link.close()
            bekleyen.join(timeout=4.0)
            _sonuctaki_aliciyi_kapat(sonuc)

    def test_deadline_oncesi_open_route_kaybolmaz(self):
        timeout = 1.0
        bekleyen, sonuc, bekleyen_hatalari, port, baslangic = (
            _rota_beklemeyi_baslat(timeout=timeout))
        link = UDPLink(bind=("127.0.0.1", 0),
                       peer=("127.0.0.1", port), timeout=0.1)
        try:
            ret = rota_yok("KAPALI_DAR", seq=7101)
            link.send(encode(ret))
            _ack_bekle(link, ret["seq"])

            # 200 ms poll aralığının içine, deadline'dan 150 ms önce gönder.
            hedef = baslangic + timeout - 0.15
            time.sleep(max(0.0, hedef - time.monotonic()))
            rota = open_route(
                3,
                0.90,
                waypoints=[[0.0, 0.0], [1.0, 0.0]],
                ref_xy=[4.0, 5.0],
                seq=7102,
            )
            link.send(encode(rota))
            _ack_bekle(link, rota["seq"])
            ack_zamani = time.monotonic()
            self.assertLess(ack_zamani - baslangic, timeout,
                            "OPEN_ROUTE deadline'dan önce ACK'lenmedi")

            bekleyen.join(timeout=2.0)
            self.assertFalse(bekleyen.is_alive(), "Rota bekleme thread'i kapanmadı")
            self.assertFalse(bekleyen_hatalari, bekleyen_hatalari)
            self.assertIsInstance(sonuc.get("alindi"), tuple)
            route, receiver = sonuc["alindi"]
            self.assertEqual(7102, route["seq"])

            # Terminal snapshot'tan kabul edilen rota, durmuş bir receiver ile
            # devredilemez; sonraki mesajı işleyip ACK üretmeye devam etmelidir.
            sonraki_rota = open_route(
                3,
                0.93,
                waypoints=[[0.0, 0.0], [1.0, 0.0]],
                ref_xy=[4.0, 5.0],
                seq=7103,
            )
            link.send(encode(sonraki_rota))
            _ack_bekle(link, sonraki_rota["seq"])
            guncel_rota, guncel_no_route, _, _ = receiver.decision_snapshot()
            self.assertEqual(7103, guncel_rota["seq"])
            self.assertIsNone(guncel_no_route)
        finally:
            link.close()
            bekleyen.join(timeout=2.0)
            _sonuctaki_aliciyi_kapat(sonuc)

    def test_deadline_sonrasi_open_route_reddedilir(self):
        timeout = 0.4
        ilk_snapshot = threading.Event()
        gercek_snapshot = ika_receiver.IkaReceiver.decision_snapshot

        def gecikmeli_ilk_snapshot(receiver):
            if not ilk_snapshot.is_set():
                ilk_snapshot.set()
                # wait_open_route saat kontrolünü deadline öncesinde yapmış olsa
                # bile snapshot'ın kendisini deadline sonrasına sarkıt.
                time.sleep(timeout + 0.15)
            return gercek_snapshot(receiver)

        with mock.patch.object(
                ika_receiver.IkaReceiver,
                "decision_snapshot",
                gecikmeli_ilk_snapshot):
            bekleyen, sonuc, bekleyen_hatalari, port, baslangic = (
                _rota_beklemeyi_baslat(timeout=timeout))
            self.assertTrue(ilk_snapshot.wait(timeout=1.0))
            link = UDPLink(bind=("127.0.0.1", 0),
                           peer=("127.0.0.1", port), timeout=0.1)
            try:
                hedef = baslangic + timeout + 0.05
                time.sleep(max(0.0, hedef - time.monotonic()))
                gec_rota = open_route(
                    1,
                    0.99,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[1.0, 2.0],
                    seq=7201,
                )
                link.send(encode(gec_rota))
                _ack_bekle(link, gec_rota["seq"])

                bekleyen.join(timeout=2.0)
                self.assertFalse(bekleyen.is_alive(),
                                 "Rota bekleme thread'i kapanmadı")
                self.assertFalse(bekleyen_hatalari, bekleyen_hatalari)
                self.assertIsNone(
                    sonuc.get("alindi"),
                    "Deadline sonrasında işlenen OPEN_ROUTE kabul edildi")
            finally:
                link.close()
                bekleyen.join(timeout=2.0)
                _sonuctaki_aliciyi_kapat(sonuc)

    def test_deadline_sonrasi_retry_onceki_rotayi_ezmez(self):
        timeout = 0.4
        ilk_snapshot = threading.Event()
        gercek_snapshot = ika_receiver.IkaReceiver.decision_snapshot

        def gecikmeli_ilk_snapshot(receiver):
            if not ilk_snapshot.is_set():
                ilk_snapshot.set()
                time.sleep(timeout + 0.20)
            return gercek_snapshot(receiver)

        with mock.patch.object(
                ika_receiver.IkaReceiver,
                "decision_snapshot",
                gecikmeli_ilk_snapshot):
            bekleyen, sonuc, bekleyen_hatalari, port, baslangic = (
                _rota_beklemeyi_baslat(timeout=timeout))
            self.assertTrue(ilk_snapshot.wait(timeout=1.0))
            link = UDPLink(bind=("127.0.0.1", 0),
                           peer=("127.0.0.1", port), timeout=0.1)
            try:
                rota = open_route(
                    2,
                    0.88,
                    waypoints=[[0.0, 0.0], [1.0, 0.0]],
                    ref_xy=[2.0, 3.0],
                    seq=7301,
                )
                once = baslangic + timeout - 0.15
                time.sleep(max(0.0, once - time.monotonic()))
                cerceve = encode(rota)
                link.send(cerceve)
                _ack_bekle(link, rota["seq"])

                # Aynı seq retry deadline sonrasında işlenir. Canlı durumun
                # zamanı değişse de cutoff snapshot'ı önceki kabulü korumalıdır.
                sonra = baslangic + timeout + 0.05
                time.sleep(max(0.0, sonra - time.monotonic()))
                link.send(cerceve)
                _ack_bekle(link, rota["seq"])

                bekleyen.join(timeout=2.0)
                self.assertFalse(bekleyen.is_alive(),
                                 "Rota bekleme thread'i kapanmadı")
                self.assertFalse(bekleyen_hatalari, bekleyen_hatalari)
                self.assertIsInstance(sonuc.get("alindi"), tuple)
                alinan_rota, _ = sonuc["alindi"]
                self.assertEqual(7301, alinan_rota["seq"])
            finally:
                link.close()
                bekleyen.join(timeout=2.0)
                _sonuctaki_aliciyi_kapat(sonuc)


if __name__ == "__main__":
    unittest.main()
