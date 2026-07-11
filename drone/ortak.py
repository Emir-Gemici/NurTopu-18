"""
Navitas dron yayini — ortak protokol + log altyapisi.
rpi_yayin.py (RPi) ve pc_izleyici.py (laptop) ayni tanimlari kullanir.

Kanallar (hepsi UDP):
  5599  HELLO / kalp atisi   izleyici → RPi   "NAVITAS_HELLO {json}"  → ACK doner
  5600  HAM video            RPi → izleyici   H.264 / MPEG-TS
  5601  AI overlay           RPi → izleyici   parcalanmis JPEG (AI_BASLIK + veri)
  5602  TELEMETRI            RPi → izleyici   JSON (2 sn'de bir)

HELLO el sikismasi ayni zamanda saat esitlemesi yapar:
  izleyici HELLO icine kendi saatini koyar; RPi ACK'ta onu + kendi saatini geri
  yollar → izleyici RTT ve saat farkini (ofset) hesaplar → AI karelerindeki
  cekim zamanindan UCTAN UCA GECIKME olculur.
"""

import json
import logging
import socket
import struct
import sys
import time

HELLO_PORT = 5599
RAW_PORT = 5600
AI_PORT = 5601
TLM_PORT = 5602

HELLO_ONEK = b"NAVITAS_HELLO"
ACK_ONEK = b"NAVITAS_ACK"

# AI kare basligi: kare_no (uint32), cekim_zamani (double, RPi saati),
# parca_no (uint16), parca_toplam (uint16)
AI_BASLIK = struct.Struct("!IdHH")
CHUNK = 1400                     # MTU alti → IP fragmantasyonu yok
UDP_BUF = 1 << 20                # 1 MiB soket tamponu (patlama kaybina karsi)

HB_ARALIK = 2.0                  # izleyici kalp atisi (sn)
HEDEF_ZAMANASIMI = 8.0           # bu kadar sure kalp atisi yoksa yayin durur (sn)


def log_kur(ad, debug=False, dosya=None):
    """Zaman damgali, seviyeli log. dosya verilirse oraya da yazar."""
    log = logging.getLogger(ad)
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    log.propagate = False
    bicim = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname).1s [%(name)s] %(message)s",
                              datefmt="%H:%M:%S")
    el = logging.StreamHandler(sys.stdout)
    el.setFormatter(bicim)
    log.addHandler(el)
    if dosya:
        fl = logging.FileHandler(dosya)
        fl.setFormatter(bicim)
        log.addHandler(fl)
    return log


def udp_soket(alici_port=None):
    """Tamponlari buyutulmus UDP soketi. alici_port verilirse baglanir."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, UDP_BUF)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, UDP_BUF)
    if alici_port is not None:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", alici_port))
    return s


def hello_yap():
    return HELLO_ONEK + b" " + json.dumps({"t_izleyici": time.time()}).encode()


def hello_coz(data):
    """HELLO paketi → t_izleyici (yoksa None). Gecersiz paket → False."""
    if not data.startswith(HELLO_ONEK):
        return False
    try:
        return json.loads(data[len(HELLO_ONEK):].decode() or "{}").get("t_izleyici")
    except (ValueError, UnicodeDecodeError):
        return None


def ack_yap(t_izleyici):
    return ACK_ONEK + b" " + json.dumps(
        {"t_izleyici": t_izleyici, "t_rpi": time.time()}).encode()


def ack_coz(data):
    """ACK → (rtt, saat_ofseti) ya da None. ofset: rpi_saati + ofset ≈ bizim saat."""
    if not data.startswith(ACK_ONEK):
        return None
    try:
        d = json.loads(data[len(ACK_ONEK):].decode())
        simdi = time.time()
        rtt = simdi - d["t_izleyici"]
        ofset = simdi - rtt / 2 - d["t_rpi"]
        return rtt, ofset
    except (ValueError, KeyError, UnicodeDecodeError):
        return None


def jpeg_gonder(sock, ip, port, kare_no, cekim_zamani, jpg):
    """JPEG'i CHUNK boyutlu parcalara bolup AI_BASLIK'la yollar."""
    n = (len(jpg) + CHUNK - 1) // CHUNK
    for i in range(n):
        veri = AI_BASLIK.pack(kare_no, cekim_zamani, i, n) + jpg[i * CHUNK:(i + 1) * CHUNK]
        sock.sendto(veri, (ip, port))
    return n
