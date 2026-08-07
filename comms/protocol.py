"""NEDEN: Rota, canlılık, manuel izin ve İHA iniş kanıtı UDP/seri taşıyıcıdan
bağımsız, çerçeveli ve ACK ile ilişkilendirilebilir mesajlar olmalıdır.

Navitas haberleşme protokolü — taşıyıcıdan BAĞIMSIZ çerçeveli JSON mesajları.

Aynı mesajlar hem dev/sim'de UDP üzerinden, hem sahada SiK Radio 433 MHz
(transparan seri) üzerinden gider. Çerçeveleme: newline ('\\n') ile ayrılmış
JSON satırları — hem UDP hem seri akış için güvenli.

Mesaj tipleri:
  OPEN_ROUTE — İHA'nın tespit ettiği açık yol (asıl görev verisi)
  HEARTBEAT  — bağlantı canlılığı (failsafe için)
  ACK        — alındı onayı (YKS/İKA → İHA)
  CMD        — YKS operatör komutu (ör. IKA_GO)
  IHA_LANDED — İHA uçuş yazılımının doğruladığı iniş tamam olayı
"""
import itertools
import json
import time

PROTOCOL_VERSION = 1
ROAD_LABEL = {1: "sol", 2: "orta", 3: "sag"}     # şartname yön kuralı
LABEL_ROAD = {v: k for k, v in ROAD_LABEL.items()}

_seq = itertools.count(1)


# ── Mesaj üreticiler ──────────────────────────────────────────────────────────

def open_route(road, conf, waypoints=None, ref_xy=None, seq=None):
    """İHA → (YKS, İKA): açık yol = road (1=sol 2=orta 3=sag) + güven +
    referans noktası + yerel waypoint'ler.

    ref_xy    : İHA'nın ilan ettiği başlangıç referans noktası [x, y] (metre;
                İKA rotayı bu noktaya göre kendi çerçevesine oturtur).
    waypoints : referans noktasına GÖRE yerel [[x,y], ...] listesi (metre).
    """
    if road not in ROAD_LABEL:
        raise ValueError(f"road 1-3 olmalı, gelen: {road}")
    return {
        "v": PROTOCOL_VERSION, "type": "OPEN_ROUTE",
        "road": int(road), "label": ROAD_LABEL[road],
        "conf": round(float(conf), 3),
        "ref_xy": ([round(float(ref_xy[0]), 2), round(float(ref_xy[1]), 2)]
                   if ref_xy else None),
        "waypoints": waypoints or [],          # [[x,y], ...] ref_xy'ye göre yerel
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }


def rota_yok(sebep, detay=None, seq=None):
    """İHA → (YKS, İKA): doğrulanmış rota üretilemedi bilgisini gönder.

    NEDEN ayrı bir mesaj türü: ``OPEN_ROUTE`` yalnız hareket edilecek yol
    kimliği ve geometri taşır. Costmap rota üretemediğinde sessizlik, bağlantı
    kesintisiyle güvenli ret kararını ayırt edilemez yapar.
    """
    sebep = str(sebep).strip()
    if not sebep:
        raise ValueError("NO_ROUTE için sebep gerekli")
    msg = {
        "v": PROTOCOL_VERSION, "type": "NO_ROUTE", "sebep": sebep,
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }
    if detay is not None:
        msg["detay"] = str(detay)
    return msg


def heartbeat(node, seq=None):
    return {"v": PROTOCOL_VERSION, "type": "HEARTBEAT", "node": node,
            "seq": next(_seq) if seq is None else int(seq), "t": round(time.time(), 3)}


def ack(ref_seq, node):
    return {"v": PROTOCOL_VERSION, "type": "ACK", "ref": int(ref_seq),
            "node": node, "t": round(time.time(), 3)}


def command(cmd, hedef, seq=None):
    """YKS → İHA/İKA operatör komutu (ör. ARM / DISARM / IKA_GO).

    Şartname §2.2.5: İKA intikali YKS'deki takım üyesince manuel tetiklenir —
    IKA_GO bu tetik içindir. Alıcılar bilmedikleri tipi yok sayar (geriye uyumlu).
    """
    return {"v": PROTOCOL_VERSION, "type": "CMD", "cmd": str(cmd),
            "hedef": hedef, "seq": next(_seq) if seq is None else int(seq),
            "t": round(time.time(), 3)}


def iha_landed(seq=None):
    """İHA → (YKS, İKA): üretim uçuşu başarıyla tamamlanıp yere temas edildi.

    Bu olay operatör komutu değildir; YKS'deki manuel ``İHA İNDİ`` düğmesi
    güvenlik latch'ini kuramaz. Alıcı, ``node`` ve ``seq`` alanlarını latch'ten
    önce doğrular.
    """
    return {
        "v": PROTOCOL_VERSION,
        "type": "IHA_LANDED",
        "node": "iha",
        "seq": next(_seq) if seq is None else int(seq),
        "t": round(time.time(), 3),
    }


# ── Çerçeveleme (encode/decode) ───────────────────────────────────────────────

def encode(msg) -> bytes:
    """Mesaj dict → tek satır JSON + '\\n' (çerçeve)."""
    return (json.dumps(msg, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def decode(line: bytes) -> dict:
    """Tek çerçeve (satır) → mesaj dict."""
    return json.loads(line.decode("utf-8").strip())


class FrameReader:
    """Seri/UDP byte akışından newline çerçevelerini ayıklar (parçalı veri güvenli)."""

    def __init__(self):
        self._buf = b""

    def feed(self, data: bytes):
        """Gelen byte'ları besle, tamamlanan her mesajı yield et."""
        if not data:
            return
        self._buf += data
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            line = line.strip()
            if line:
                try:
                    yield decode(line)
                except (ValueError, UnicodeDecodeError):
                    pass  # bozuk çerçeveyi at (RF gürültüsü)
