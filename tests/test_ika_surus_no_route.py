"""NEDEN: İKA yalnız IKA_GO, İHA inişi ve geçerli OPEN_ROUTE birlikteyken
hareket etmeli; NO_ROUTE sırasında durup yeni rota gelince güvenle toparlanmalıdır.
"""

import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "simulation" / "scripts"))

import ika_nav  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import (FrameReader, command, encode, iha_landed, open_route,
                      rota_yok)  # noqa: E402


def _ack_bekle(link, ref_seq, timeout=1.5):
    okuyucu = FrameReader()
    son = time.monotonic() + timeout
    while time.monotonic() < son:
        veri, _ = link.recv()
        for mesaj in okuyucu.feed(veri) if veri else []:
            if mesaj.get("type") == "ACK" and mesaj.get("ref") == ref_seq:
                return
    raise AssertionError(f"seq={ref_seq} için ACK gelmedi")


class _SahteRobot:
    """Gerçek karar alıcısını kullanan, yalnız kinematiği sahte robot."""

    def __init__(self, receiver, sender, recovery_route):
        self.receiver = receiver
        self.sender = sender
        self.recovery_route = recovery_route
        self.x = 0.0
        self.commands = []
        self.bloklu_komut_sayisi = 0
        self.recovery_generation = None

    def get_pose(self, _model="ika"):
        return self.x, 0.0, 0.0, 0.0

    def send_vel(self, right, left, _topic="~/ika/vel_cmd"):
        if len(self.commands) >= 20:
            raise AssertionError("Navigasyon 20 komutluk test watchdog'unu aştı")
        route, no_route, generation, _ = self.receiver.decision_snapshot()
        nonzero = abs(right) > 1e-9 or abs(left) > 1e-9
        self.commands.append({
            "right": right,
            "left": left,
            "nonzero": nonzero,
            "route_seq": route.get("seq") if route else None,
            "no_route": no_route,
            "generation": generation,
        })

        if no_route is not None:
            self.bloklu_komut_sayisi += 1
            if self.bloklu_komut_sayisi == 3:
                self.sender.send(encode(self.recovery_route))
                _ack_bekle(self.sender, self.recovery_route["seq"])
                self.recovery_generation = self.receiver.decision_snapshot()[2]
            return

        if not nonzero:
            return

        self.x += 0.4


class SurusNoRouteTests(unittest.TestCase):
    def test_no_route_boyunca_nonzero_komut_yok_ve_open_route_ile_devam(self):
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.02)
        receiver = IkaReceiver(alici_link, hb_timeout=10.0).start()
        sender = UDPLink(
            bind=("127.0.0.1", 0),
            peer=("127.0.0.1", alici_link.port),
            timeout=0.02,
        )

        ilk_rota = open_route(
            2,
            0.95,
            waypoints=[[0.0, 0.0], [1.0, 0.0]],
            ref_xy=[0.0, 0.0],
            seq=7601,
        )
        no_route = rota_yok("KAPALI_DAR", "sürüş ortası", seq=7602)
        recovery_route = open_route(
            2,
            0.96,
            waypoints=[[0.0, 0.0], [1.0, 0.0]],
            ref_xy=[0.0, 0.0],
            seq=7603,
        )

        try:
            inis = iha_landed(seq=7599)
            sender.send(encode(inis))
            _ack_bekle(sender, inis["seq"])
            ika_go = command("IKA_GO", "ika", seq=7600)
            sender.send(encode(ika_go))
            _ack_bekle(sender, ika_go["seq"])
            sender.send(encode(ilk_rota))
            _ack_bekle(sender, ilk_rota["seq"])
            robot = _SahteRobot(receiver, sender, recovery_route)
            rota_kapisi_cagrisi = 0
            no_route_gonderildi = False

            def rota_gecerli():
                nonlocal rota_kapisi_cagrisi, no_route_gonderildi
                rota_kapisi_cagrisi += 1
                sonuc = ika_nav.receiver_rota_gecerli(receiver)
                # İlk nonzero hareketten sonraki turda, son bool kontrolü ile
                # atomik motor korumasının tam arasına NO_ROUTE yerleştir.
                if rota_kapisi_cagrisi == 4 and sonuc:
                    no_route_gonderildi = True
                    sender.send(encode(no_route))
                    _ack_bekle(sender, no_route["seq"])
                return sonuc

            with (
                mock.patch.object(ika_nav, "get_pose", side_effect=robot.get_pose),
                mock.patch.object(ika_nav, "send_vel", side_effect=robot.send_vel),
                mock.patch.object(
                    ika_nav,
                    "time",
                    SimpleNamespace(sleep=lambda _seconds: None),
                ),
            ):
                tamamlandi = ika_nav.navigate_route(
                    ilk_rota,
                    verbose=False,
                    link_ok=lambda: receiver.link_ok,
                    rota_gecerli=rota_gecerli,
                    rota_korumali_gonder=lambda r, l: (
                        ika_nav.receiver_korumali_hiz_gonder(receiver, r, l)
                    ),
                )

            bloklu = [komut for komut in robot.commands
                       if komut["no_route"] is not None]
            bloklu_nonzero = sum(komut["nonzero"] for komut in bloklu)
            toparlanmis_nonzero = [
                komut for komut in robot.commands
                if robot.recovery_generation is not None
                and komut["generation"] >= robot.recovery_generation
                and komut["nonzero"]
            ]

            self.assertTrue(tamamlandi)
            self.assertTrue(no_route_gonderildi)
            self.assertGreaterEqual(len(bloklu), 3)
            self.assertEqual(0, bloklu_nonzero)
            self.assertTrue(toparlanmis_nonzero)
            self.assertEqual(7603, receiver.decision_snapshot()[0]["seq"])
            self.assertIsNone(receiver.decision_snapshot()[1])
            print(
                "[KAPI] NO_ROUTE etkin komut="
                f"{len(bloklu)}, sıfır-olmayan={bloklu_nonzero}; "
                f"OPEN_ROUTE sonrası sıfır-olmayan={len(toparlanmis_nonzero)}"
            )
        finally:
            receiver.stop()
            sender.close()
            alici_link.close()

    def test_navigate_route_rota_gecerli_callbackini_aktarir(self):
        route = {
            "road": 2,
            "waypoints": [[0.0, 0.0], [1.0, 0.0]],
            "ref_xy": [0.0, 0.0],
        }
        rota_gecerli = mock.Mock(return_value=True)
        korumali_gonder = mock.Mock(return_value=True)
        with mock.patch.object(ika_nav, "navigate", return_value=True) as navigate:
            self.assertTrue(
                ika_nav.navigate_route(
                    route,
                    verbose=False,
                    rota_gecerli=rota_gecerli,
                    rota_korumali_gonder=korumali_gonder,
                )
            )
        self.assertIs(navigate.call_args.kwargs["rota_gecerli"], rota_gecerli)
        self.assertIs(
            navigate.call_args.kwargs["rota_korumali_gonder"],
            korumali_gonder,
        )

    def test_gecersiz_open_route_rota_kapisini_acmaz(self):
        malformed = {"type": "OPEN_ROUTE", "waypoints": [], "seq": 7701}

        class SabitReceiver:
            def decision_snapshot(self):
                return malformed, None, 1, 0.0

        self.assertFalse(ika_nav.receiver_rota_gecerli(SabitReceiver()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
