"""YKS PC ile MK15 video kaynağı arasında imzalı ağ keşfi.

Keşif yalnızca kaynak adresini bulur; bulunan adres doğrudan video doğrulamasından
geçmeden canlı kabul edilmez. MAVLink ve görev komutları bu modülün kapsamı
dışındadır.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import threading
import time


DUYURU_PORT = 5010
DUYURU_TIPI = "NAVITAS_VIDEO_DUYURU"
DUYURU_SURUMU = 1
DUYURU_ARALIGI_S = 1.0
TAZELIK_PENCERESI_S = 10.0
SECIM_BAYAT_S = 5.0


def eslesme_uret(ad="YKS-PC"):
    return {
        "kimlik": f"{ad}-{secrets.token_hex(4)}",
        "anahtar": secrets.token_hex(32),
        "ad": str(ad),
    }


def eslesme_kodu(eslesme):
    veri = bytes.fromhex(eslesme["anahtar"]) + eslesme["kimlik"].encode()
    return f"{int(hashlib.sha256(veri).hexdigest()[:8], 16) % 1000000:06d}"


def eslesme_oku(yol):
    veri = json.loads(Path(yol).read_text(encoding="utf-8"))
    if not isinstance(veri, dict) or not isinstance(veri.get("kimlik"), str):
        raise ValueError("eşleşme dosyasında kimlik yok")
    anahtar = bytes.fromhex(str(veri.get("anahtar", "")))
    if len(anahtar) < 16:
        raise ValueError("eşleşme anahtarı en az 16 bayt hex olmalı")
    return veri


def eslesme_yaz(yol, eslesme):
    hedef = Path(yol)
    hedef.parent.mkdir(parents=True, exist_ok=True)
    gecici = hedef.with_suffix(hedef.suffix + ".tmp")
    gecici.write_text(json.dumps(eslesme, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    try:
        os.chmod(gecici, 0o600)
    except OSError:
        pass
    os.replace(gecici, hedef)


def _govde(eslesme, port, video_url, t, nonce):
    return json.dumps({
        "v": DUYURU_SURUMU,
        "type": DUYURU_TIPI,
        "kimlik": eslesme["kimlik"],
        "port": int(port),
        "video_url": str(video_url),
        "t": round(float(t), 3),
        "nonce": nonce,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")


def duyuru_uret(eslesme, port, video_url, *, t=None, nonce=None):
    govde = _govde(eslesme, port, video_url,
                   time.time() if t is None else t,
                   nonce or secrets.token_hex(8))
    paket = json.loads(govde)
    paket["mac"] = hmac.new(bytes.fromhex(eslesme["anahtar"]), govde,
                             hashlib.sha256).hexdigest()
    return (json.dumps(paket, separators=(",", ":")) + "\n").encode()


def duyuru_coz(veri):
    try:
        paket = json.loads(veri.decode("utf-8"))
        if (not isinstance(paket, dict) or paket.get("v") != DUYURU_SURUMU
                or paket.get("type") != DUYURU_TIPI
                or not isinstance(paket.get("kimlik"), str)
                or not isinstance(paket.get("video_url"), str)
                or not isinstance(paket.get("mac"), str)):
            return None
        paket["port"] = int(paket["port"])
        paket["t"] = float(paket["t"])
        if not 1 <= paket["port"] <= 65535:
            return None
        return paket
    except (UnicodeDecodeError, ValueError, TypeError, KeyError):
        return None


class YksSecici:
    def __init__(self, eslesme, *, saat=time.monotonic, duvar=time.time):
        self.eslesme = eslesme
        self._anahtar = bytes.fromhex(eslesme["anahtar"])
        self.saat, self.duvar = saat, duvar
        self.adres = None
        self.video_url = None
        self._son_kabul = None
        self._saat_farki = None
        self._nonce = []
        self.sayac = {"kabul": 0, "kimlik_red": 0, "imza_red": 0,
                      "bayat_red": 0, "tekrar_red": 0, "bozuk": 0}

    def isle(self, veri, kaynak_ip):
        paket = duyuru_coz(veri)
        if paket is None:
            self.sayac["bozuk"] += 1
            return "BOZUK"
        if paket["kimlik"] != self.eslesme["kimlik"]:
            self.sayac["kimlik_red"] += 1
            return "KIMLIK_RED"
        govde = _govde(self.eslesme, paket["port"], paket["video_url"],
                       paket["t"], paket["nonce"])
        beklenen = hmac.new(self._anahtar, govde, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(beklenen, paket["mac"]):
            self.sayac["imza_red"] += 1
            return "IMZA_RED"
        fark = paket["t"] - self.duvar()
        if self._saat_farki is not None and abs(fark - self._saat_farki) > TAZELIK_PENCERESI_S:
            self.sayac["bayat_red"] += 1
            return "BAYAT_RED"
        if paket["nonce"] in self._nonce:
            self.sayac["tekrar_red"] += 1
            return "TEKRAR_RED"
        self._nonce.append(paket["nonce"])
        del self._nonce[:-256]
        self._saat_farki = fark if self._saat_farki is None else 0.9 * self._saat_farki + 0.1 * fark
        eski = self.adres
        self.adres = (str(kaynak_ip), paket["port"])
        self.video_url = paket["video_url"]
        self._son_kabul = self.saat()
        self.sayac["kabul"] += 1
        return "ADRES_DEGISTI" if eski != self.adres else "KABUL"

    def durum(self):
        if self.adres is None:
            return "YOK"
        return "TAZE" if self.saat() - self._son_kabul <= SECIM_BAYAT_S else "BAYAT"


def dinleyici_soketi(bind=("0.0.0.0", DUYURU_PORT)):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(bind)
    return sock


class DuyuruYayinci(threading.Thread):
    def __init__(self, eslesme, port, video_url, *, hedefler=None,
                 aralik_s=DUYURU_ARALIGI_S, log=lambda *_: None):
        super().__init__(name="yks-video-duyuru", daemon=True)
        self.eslesme, self.port, self.video_url = eslesme, int(port), str(video_url)
        self.hedefler = list(hedefler or [("255.255.255.255", DUYURU_PORT)])
        self.aralik_s, self.log = float(aralik_s), log
        self._dur = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self):
        while not self._dur.is_set():
            paket = duyuru_uret(self.eslesme, self.port, self.video_url)
            for hedef in self.hedefler:
                try:
                    self.sock.sendto(paket, hedef)
                except OSError as exc:
                    self.log(f"video duyurusu gönderilemedi: {exc}")
            self._dur.wait(self.aralik_s)

    def durdur(self):
        self._dur.set()
        try:
            self.sock.close()
        except OSError:
            pass


class KesifDinleyici(threading.Thread):
    def __init__(self, secici, geri_cagir, *, bind=("0.0.0.0", DUYURU_PORT),
                 log=lambda *_: None):
        super().__init__(name="yks-video-kesif", daemon=True)
        self.secici, self.geri_cagir, self.log = secici, geri_cagir, log
        self.sock = dinleyici_soketi(bind)
        self.sock.settimeout(0.3)
        self._dur = threading.Event()

    def run(self):
        while not self._dur.is_set():
            try:
                veri, adres = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                return
            if self.secici.isle(veri, adres[0]) == "ADRES_DEGISTI":
                try:
                    self.geri_cagir(self.secici.video_url, self.secici.adres)
                except Exception as exc:
                    self.log(f"video keşif geri çağrısı başarısız: {exc}")

    def durdur(self):
        self._dur.set()
        try:
            self.sock.close()
        except OSError:
            pass
