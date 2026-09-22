"""Dogrudan radyo telemetry + guarded Pixhawk COMMAND_LONG/ACK tests."""
from pathlib import Path
import json
import socket
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / p) for p in ("comms", "codes")]
from pymavlink.dialects.v20 import ardupilotmega as mav
from protocol import command, decode, encode
from radio_mode import NativeRadioLink, RadioTelemetry, ARM_DURUM_TAZELIK_S


def received(message, sysid=1, component=1):
    encoder = mav.MAVLink(None, srcSystem=sysid, srcComponent=component)
    parser = mav.MAVLink(None)
    return parser.parse_buffer(message.pack(encoder))[0]


def hb(armed=False, gcs=False):
    return mav.MAVLink_heartbeat_message(mav.MAV_TYPE_GCS if gcs else mav.MAV_TYPE_QUADROTOR,
        mav.MAV_AUTOPILOT_ARDUPILOTMEGA, mav.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED | (mav.MAV_MODE_FLAG_SAFETY_ARMED if armed else 0), 0, 3, 3)


class RadioTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.telemetry = RadioTelemetry(clock=lambda: self.now)

    def test_actual_heartbeat_without_jetson_produces_only_telemetry(self):
        result = self.telemetry.accept(received(hb()))
        self.assertEqual(result["kaynak"], "PIXHAWK_MAVLINK_RADYO")
        self.assertIs(result["armed"], False)
        self.assertIs(result["pixhawk_canli"], True)
        self.assertEqual(result["mod"], "STABILIZE")
        for key in ("karar_yas", "gorev_hazir", "lat", "bat", "waypoints"):
            self.assertNotIn(key, result)

    def test_gps_freshness_fix_loss_and_unknown_battery(self):
        gps = mav.MAVLink_gps_raw_int_message(1, 3, 377000000, 382000000, 1000, 100, 100, 0, 0, 21)
        self.telemetry.accept(received(gps))
        result = self.telemetry.accept(received(hb(True)))
        self.assertEqual((result["lat"], result["lon"], result["uydu"]), (37.7, 38.2, 21))
        self.assertIs(result["armed"], True)
        self.now += ARM_DURUM_TAZELIK_S + 1
        result = self.telemetry.accept(received(hb()))
        self.assertNotIn("lat", result); self.assertNotIn("uydu", result)
        gps.fix_type = 1; gps.satellites_visible = 255
        self.telemetry.accept(received(gps))
        result = self.telemetry.accept(received(hb()))
        self.assertEqual(result["gps_fix"], 1)
        self.assertNotIn("lat", result); self.assertNotIn("uydu", result)
        self.assertNotIn("bat", result)

    def test_other_vehicle_gcs_and_wrong_component_are_not_live(self):
        for message in (received(hb(), sysid=2), received(hb(gcs=True)), received(hb(), component=25)):
            self.assertIsNone(self.telemetry.accept(message))
        self.assertEqual(self.telemetry.sequence, 0)

    def test_direct_command_and_pixhawk_ack_return_to_yki(self):
        peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer.bind(("127.0.0.1", 0))
        peer.settimeout(1.0)
        link = NativeRadioLink(("127.0.0.1", 0), "yer")
        self.addCleanup(link.close)
        self.addCleanup(peer.close)
        enc = mav.MAVLink(None, srcSystem=1, srcComponent=1)
        wire = hb().pack(enc)
        peer_address = peer.getsockname()
        link._datagram_isle(wire[:5], peer_address)
        self.assertFalse(link._teslim)
        link._datagram_isle(wire[5:], peer_address)
        result = json.loads(link._teslim.popleft())
        self.assertEqual(result["type"], "HEARTBEAT")
        self.assertEqual(link.akran, peer_address)
        request = command("ARM", "iha", oturum="a" * 16)
        link.send(encode(request))
        command_wire, _ = peer.recvfrom(4096)
        parser = mav.MAVLink(None)
        command_message = parser.parse_buffer(command_wire)[0]
        self.assertEqual(command_message.get_type(), "COMMAND_LONG")
        self.assertEqual(command_message.command, mav.MAV_CMD_COMPONENT_ARM_DISARM)
        self.assertEqual(command_message.target_system, 1)
        self.assertEqual(command_message.target_component, 1)
        self.assertEqual(command_message.param1, 1.0)

        ack_wire = mav.MAVLink_command_ack_message(
            mav.MAV_CMD_COMPONENT_ARM_DISARM, mav.MAV_RESULT_ACCEPTED,
            0, 0, 1, 1).pack(enc)
        link._datagram_isle(ack_wire, peer_address)
        response = decode(link.recv()[0])
        self.assertEqual(response["type"], "ACK")
        self.assertEqual(response["ref"], request["seq"])
        self.assertEqual(response["ref_cmd"], "ARM")
        self.assertEqual(response["sonuc"], "ACCEPTED")
        self.assertEqual(response["oturum"], "a" * 16)

    def test_direct_radio_rejects_ika_and_stale_heartbeat(self):
        link = NativeRadioLink(("127.0.0.1", 0), "yer")
        self.addCleanup(link.close)
        with self.assertRaisesRegex(OSError, "IKA"):
            link.send(encode(command("IKA_GO", "ika", oturum="b" * 16)))
        link.akran = ("127.0.0.1", 12001)
        link._son_heartbeat_t = link.saat() - ARM_DURUM_TAZELIK_S - 1
        with self.assertRaisesRegex(OSError, "bayat"):
            link.send(encode(command("ARM", "iha", oturum="b" * 16)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
