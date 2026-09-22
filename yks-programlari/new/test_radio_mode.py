"""NEDEN: dogrudan radyo akisinda gercek, taze telemetri disinda veri uretilmemeli."""
from pathlib import Path
import json
import sys
import unittest
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / p) for p in ("comms", "codes")]
from pymavlink.dialects.v20 import ardupilotmega as mav
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

    def test_real_mavlink_fragmentation_and_no_outbound_commands(self):
        link = NativeRadioLink(("127.0.0.1", 0), "yer")
        self.addCleanup(link.close)
        enc = mav.MAVLink(None, srcSystem=1, srcComponent=1)
        wire = hb().pack(enc)
        link._datagram_isle(wire[:5], ("127.0.0.1", 12001))
        self.assertFalse(link._teslim)
        link._datagram_isle(wire[5:], ("127.0.0.1", 12001))
        result = json.loads(link._teslim.popleft())
        self.assertEqual(result["type"], "HEARTBEAT")
        self.assertEqual(link.akran, ("127.0.0.1", 12001))
        with self.assertRaises(OSError):
            link.send(b'{"type":"CMD","cmd":"ARM"}')
        link._datagram_isle(wire, ("127.0.0.1", 12002))
        self.assertFalse(link._teslim)


if __name__ == "__main__":
    unittest.main(verbosity=2)
