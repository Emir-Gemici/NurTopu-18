import json
import unittest

from comms.protocol import (FrameReader, MAX_FRAME_BYTES, ProtocolError, ReplayGuard,
                            decode, encode, open_route)
from comms.ika_receiver import IkaReceiver


class ProtocolTests(unittest.TestCase):
    def test_v2_round_trip_has_integrity_and_identity(self):
        msg = open_route(2, 0.91, [[0, 0], [1.2, 8.4]], [-20, -24.5], seq=42)
        decoded = decode(encode(msg))
        self.assertEqual(decoded["road"], 2)
        self.assertEqual(decoded["seq"], 42)
        self.assertIn("crc32", decoded)
        self.assertIn("session", decoded)

    def test_tamper_is_rejected(self):
        wire = encode(open_route(1, 0.8, seq=8))
        payload = json.loads(wire)
        payload["road"] = 3
        tampered = json.dumps(payload).encode()
        with self.assertRaises(ProtocolError):
            decode(tampered)

    def test_invalid_values_are_rejected(self):
        with self.assertRaises((ProtocolError, ValueError)):
            open_route(2, float("nan"))
        with self.assertRaises(ProtocolError):
            open_route(2, 0.8, [[0, 0]] * 65)

    def test_reader_bounds_noise_and_resynchronizes(self):
        reader = FrameReader(max_frame_bytes=64)
        self.assertEqual(list(reader.feed(b"x" * 65)), [])
        self.assertEqual(reader.dropped, 1)
        self.assertEqual(list(reader.feed(b"not-json\n")), [])
        self.assertEqual(reader.dropped, 2)

    def test_replay_guard_rejects_duplicate_and_stale(self):
        guard = ReplayGuard()
        newest = open_route(1, 0.8, seq=10)
        duplicate = dict(newest)
        stale = dict(newest, seq=9)
        self.assertTrue(guard.accept(newest))
        self.assertFalse(guard.accept(duplicate))
        self.assertFalse(guard.accept(stale))

    def test_serial_style_receiver_acks_retry_but_applies_once(self):
        class FakeSerialLink:
            def __init__(self):
                self.sent = []

            def send(self, data, peer=None):
                self.sent.append((data, peer))

        link = FakeSerialLink()
        receiver = IkaReceiver(link)
        applied = []
        receiver.on_route = lambda msg: applied.append(msg["seq"])
        route = open_route(3, 0.75, seq=77)
        receiver._handle(route, None)
        receiver._handle(route, None)
        self.assertEqual(applied, [77])
        self.assertEqual(len(link.sent), 2)
        for wire, peer in link.sent:
            ack_msg = decode(wire)
            self.assertEqual(ack_msg["ref"], 77)
            self.assertIsNone(peer)


if __name__ == "__main__":
    unittest.main()
