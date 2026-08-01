"""Validated, bounded Navitas wire protocol for UDP and transparent serial links."""

from __future__ import annotations

import itertools
import json
import math
import secrets
import time
import zlib

PROTOCOL_VERSION = 2
MAX_FRAME_BYTES = 16 * 1024
MAX_WAYPOINTS = 64
MAX_COORDINATE_M = 10_000.0
ROAD_LABEL = {1: "sol", 2: "orta", 3: "sag"}
LABEL_ROAD = {v: k for k, v in ROAD_LABEL.items()}

_seq = itertools.count(1)
_session = secrets.token_hex(8)


class ProtocolError(ValueError):
    pass


def _base(msg_type, seq=None, source=None):
    msg = {"v": PROTOCOL_VERSION, "type": msg_type, "session": _session,
           "seq": next(_seq) if seq is None else int(seq), "t": round(time.time(), 3)}
    if source:
        msg["source"] = source
    return msg


def open_route(road, conf, waypoints=None, ref_xy=None, seq=None):
    if road not in ROAD_LABEL:
        raise ValueError(f"road 1-3 olmalı, gelen: {road}")
    msg = _base("OPEN_ROUTE", seq, "iha")
    msg.update({
        "road": int(road), "label": ROAD_LABEL[road], "conf": round(float(conf), 3),
        "ref_xy": ([round(float(ref_xy[0]), 2), round(float(ref_xy[1]), 2)]
                   if ref_xy else None),
        "waypoints": [[round(float(x), 3), round(float(y), 3)]
                      for x, y in (waypoints or [])],
    })
    validate_message(msg)
    return msg


def heartbeat(node, seq=None):
    msg = _base("HEARTBEAT", seq, node)
    msg["node"] = node
    validate_message(msg)
    return msg


def ack(ref_seq, node, session=None):
    msg = _base("ACK", source=node)
    msg.update({"ref": int(ref_seq), "node": node, "ref_session": session})
    validate_message(msg)
    return msg


def command(cmd, hedef, seq=None):
    msg = _base("CMD", seq, "yks")
    msg.update({"cmd": str(cmd), "hedef": str(hedef)})
    validate_message(msg)
    return msg


def _canonical(msg):
    unsigned = {key: value for key, value in msg.items() if key != "crc32"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def encode(msg) -> bytes:
    checked = dict(msg)
    validate_message(checked)
    if checked.get("v", 1) >= 2:
        checked["crc32"] = f"{zlib.crc32(_canonical(checked)) & 0xffffffff:08x}"
    data = (json.dumps(checked, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")
    if len(data) > MAX_FRAME_BYTES:
        raise ProtocolError(f"çerçeve çok büyük: {len(data)} > {MAX_FRAME_BYTES}")
    return data


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ProtocolError(f"{field} sonlu sayı olmalı")
    return float(value)


def _short_text(value, field):
    if not isinstance(value, str) or not value or len(value) > 32:
        raise ProtocolError(f"{field} 1-32 karakter olmalı")


def validate_message(msg):
    if not isinstance(msg, dict):
        raise ProtocolError("mesaj JSON nesnesi olmalı")
    if msg.get("v") not in (1, PROTOCOL_VERSION):
        raise ProtocolError(f"desteklenmeyen protokol sürümü: {msg.get('v')}")
    msg_type = msg.get("type")
    if msg_type not in {"OPEN_ROUTE", "HEARTBEAT", "ACK", "CMD"}:
        raise ProtocolError(f"bilinmeyen mesaj tipi: {msg_type}")
    if "t" in msg:
        _finite_number(msg["t"], "t")
    if msg_type != "ACK":
        if isinstance(msg.get("seq"), bool) or not isinstance(msg.get("seq"), int) or msg["seq"] < 0:
            raise ProtocolError("seq negatif olmayan tamsayı olmalı")
    if msg.get("v") == PROTOCOL_VERSION:
        _short_text(msg.get("session"), "session")

    if msg_type == "OPEN_ROUTE":
        road = msg.get("road")
        if road not in ROAD_LABEL or msg.get("label") != ROAD_LABEL[road]:
            raise ProtocolError("road/label tutarsız")
        conf = _finite_number(msg.get("conf"), "conf")
        if not 0.0 <= conf <= 1.0:
            raise ProtocolError("conf 0..1 aralığında olmalı")
        waypoints = msg.get("waypoints", [])
        if not isinstance(waypoints, list) or len(waypoints) > MAX_WAYPOINTS:
            raise ProtocolError(f"waypoints en fazla {MAX_WAYPOINTS} nokta olmalı")
        points = waypoints + ([msg["ref_xy"]] if msg.get("ref_xy") is not None else [])
        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ProtocolError("koordinat [x,y] olmalı")
            if any(abs(_finite_number(v, "koordinat")) > MAX_COORDINATE_M for v in point):
                raise ProtocolError("koordinat güvenli sınır dışında")
    elif msg_type in {"HEARTBEAT", "ACK"}:
        _short_text(msg.get("node"), "node")
        if msg_type == "ACK" and (not isinstance(msg.get("ref"), int) or msg["ref"] < 0):
            raise ProtocolError("ACK ref negatif olmayan tamsayı olmalı")
    else:
        _short_text(msg.get("cmd"), "cmd")
        _short_text(msg.get("hedef"), "hedef")
    return msg


def decode(line: bytes) -> dict:
    if len(line) > MAX_FRAME_BYTES:
        raise ProtocolError("çerçeve boyut sınırını aşıyor")
    try:
        msg = json.loads(line.decode("utf-8").strip())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProtocolError(f"geçersiz JSON: {exc}") from exc
    if isinstance(msg, dict) and msg.get("v") == PROTOCOL_VERSION:
        supplied = msg.get("crc32")
        expected = f"{zlib.crc32(_canonical(msg)) & 0xffffffff:08x}"
        if not isinstance(supplied, str) or not secrets.compare_digest(supplied, expected):
            raise ProtocolError("CRC32 uyuşmuyor")
    return validate_message(msg)


class ReplayGuard:
    """Reject stale/duplicate sequence numbers per source boot session."""

    def __init__(self):
        self._latest = {}

    def accept(self, msg):
        if "seq" not in msg:
            return True
        key = (msg.get("source", "unknown"), msg.get("session", "legacy"))
        seq = msg["seq"]
        if seq <= self._latest.get(key, -1):
            return False
        self._latest[key] = seq
        return True


class FrameReader:
    """Bounded newline frame reader; malformed RF input cannot grow memory forever."""

    def __init__(self, max_frame_bytes=MAX_FRAME_BYTES):
        self._buf = b""
        self.max_frame_bytes = max_frame_bytes
        self.dropped = 0

    def feed(self, data: bytes):
        if not data:
            return
        self._buf += data
        if len(self._buf) > self.max_frame_bytes and b"\n" not in self._buf:
            self._buf = b""
            self.dropped += 1
            return
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            if len(line) > self.max_frame_bytes:
                self.dropped += 1
                continue
            try:
                yield decode(line)
            except ProtocolError:
                self.dropped += 1
        if len(self._buf) > self.max_frame_bytes:
            self._buf = b""
            self.dropped += 1
