"""ONARIM-03/09: YKS kesfi — "Bluetooth mantigi": YKS kendini duyurur, Jetson eslestigi YKS'yi secer.

NEDEN (17 Eyl 2026): YKS PC'sinin IP'si DHCP ile bir gunde iki kez degisti
(10.21.8.112 -> 10.21.8.156). Jetson'daki `YKS_IP` sabit beyan oldugu icin her
degisimde telemetri yanlis adrese gidiyor, komut alici yeni adresten gelen komutu
REDDEDIYORDU. Kullanici karari: "tarasin, bluetooth mantigi gibi dogrusu secilsin".

Model:
  * ESLESME (bir kez, Bluetooth eslestirmesi gibi): YKS tarafinda `yks_eslestir.py yeni`
    bir kimlik + 32 baytlik anahtar uretir ve kisa bir ESLESME KODU gosterir. Ayni dosya
    Jetson'a kopyalanir (ya da kimlik+anahtar elle girilir). Anahtar hicbir pakette tasinmaz.
  * DUYURU: YKS her ~1 s LAN broadcast'e (UDP DUYURU_PORT) `YKS_DUYURU` yayar:
    kimlik, dinleme portu, zaman, nonce, HMAC-SHA256(anahtar, govde).
  * SECIM: Jetson yalniz (a) kimligi eslesen, (b) HMAC'i dogru, (c) zamani tazelik
    penceresinde, (d) nonce'u tekrar olmayan duyuruyu kabul eder; YKS adresi = duyurunun
    KAYNAK IP'si + duyurudaki port. Baska kimlikler "tarama" listesinde gorunur ama secilmez.
  * Zaman kontrolu Jetson saatine dayanmaz (RTC pilsiz, ONARIM-08): ilk kabulde YKS
    saatiyle fark ogrenilir, sonraki duyurular bu farka gore tazelik penceresinde olmali.

Yalniz standart kutuphane (hmac, hashlib, json, socket) — proje kurali (madde 4) ihlal edilmez.
"""
import hashlib
import hmac
import json
import os
import secrets
import socket
import threading
import time
from pathlib import Path

DUYURU_PORT = 5010
DUYURU_TIPI = "YKS_DUYURU"
DUYURU_SURUMU = 1
DUYURU_ARALIGI_S = 1.0
#: Kabul edilen duyuru, YKS saatine gore ogrenilen farktan en cok bu kadar sapabilir.
TAZELIK_PENCERESI_S = 10.0
#: Bu sure yeni gecerli duyuru gelmezse secili YKS "BAYAT" sayilir (adres korunur).
SECIM_BAYAT_S = 5.0
NONCE_HAFIZA = 256


def eslesme_uret(ad="YKS"):
    """Yeni eslesme: {"kimlik", "anahtar"(hex), "ad"}."""
    return {"kimlik": f"{ad}-{secrets.token_hex(4)}", "anahtar": secrets.token_hex(32), "ad": str(ad)}


def eslesme_kodu(eslesme):
    """Iki ekranda karsilastirilacak kisa kod (anahtarin parmak izi, 6 hane)."""
    ozet = hashlib.sha256(bytes.fromhex(eslesme["anahtar"]) + eslesme["kimlik"].encode()).hexdigest()
    return f"{int(ozet[:8], 16) % 1000000:06d}"


def eslesme_oku(yol):
    veri = json.loads(Path(yol).read_text(encoding="utf-8"))
    if not isinstance(veri, dict) or not isinstance(veri.get("kimlik"), str):
        raise ValueError("eslesme dosyasi: 'kimlik' yok")
    anahtar = bytes.fromhex(str(veri.get("anahtar", "")))
    if len(anahtar) < 16:
        raise ValueError("eslesme dosyasi: anahtar en az 16 bayt hex olmali")
    return veri


def eslesme_yaz(yol, eslesme):
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(yol.suffix + ".tmp")
    gecici.write_text(json.dumps(eslesme, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.chmod(gecici, 0o600)                         # anahtar: yalniz sahibi okur
    os.replace(gecici, yol)


def _govde(kimlik, port, t, nonce):
    return json.dumps({"v": DUYURU_SURUMU, "type": DUYURU_TIPI, "kimlik": kimlik,
                       "port": int(port), "t": round(float(t), 3), "nonce": nonce},
                      sort_keys=True, separators=(",", ":")).encode("utf-8")


def duyuru_uret(eslesme, port, t=None, nonce=None):
    t = time.time() if t is None else t
    nonce = nonce or secrets.token_hex(8)
    govde = _govde(eslesme["kimlik"], port, t, nonce)
    mac = hmac.new(bytes.fromhex(eslesme["anahtar"]), govde, hashlib.sha256).hexdigest()
    paket = json.loads(govde)
    paket["mac"] = mac
    return (json.dumps(paket, separators=(",", ":")) + "\n").encode("utf-8")


def duyuru_coz(veri):
    """Imza DOGRULAMADAN ayristir (tarama listesi icin). Gecersizse None."""
    try:
        m = json.loads(veri.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, AttributeError):
        return None
    if (not isinstance(m, dict) or m.get("type") != DUYURU_TIPI or m.get("v") != DUYURU_SURUMU
            or not isinstance(m.get("kimlik"), str) or not isinstance(m.get("nonce"), str)
            or not isinstance(m.get("mac"), str)):
        return None
    try:
        port, t = int(m["port"]), float(m["t"])
    except (KeyError, TypeError, ValueError):
        return None
    if not 1 <= port <= 65535:
        return None
    m["port"], m["t"] = port, t
    return m


class YksSecici:
    """Jetson tarafi: duyurulari dogrular, eslesen YKS'nin guncel adresini tutar. Saf (soket yok)."""

    def __init__(self, eslesme, *, saat=time.monotonic, duvar=time.time):
        self.eslesme = eslesme
        self._anahtar = bytes.fromhex(eslesme["anahtar"])
        self.saat = saat
        self.duvar = duvar
        self.adres = None              # (ip, port)
        self._son_kabul = None
        self._saat_farki = None        # YKS t - Jetson duvar
        self._nonce = []
        self.gorulen = {}              # kimlik -> {"ip","port","son","dogrulandi"}
        self.sayac = {"kabul": 0, "baska_kimlik": 0, "imza_red": 0, "bayat_red": 0,
                      "tekrar_red": 0, "bozuk": 0, "adres_degisti": 0}

    def isle(self, veri, kaynak_ip):
        """-> "KABUL" | "ADRES_DEGISTI" | red sebebi (str)."""
        m = duyuru_coz(veri)
        if m is None:
            self.sayac["bozuk"] += 1
            return "BOZUK"
        simdi = self.saat()
        g = self.gorulen.setdefault(m["kimlik"], {})
        g.update(ip=kaynak_ip, port=m["port"], son=simdi)
        if m["kimlik"] != self.eslesme["kimlik"]:
            g["dogrulandi"] = False
            self.sayac["baska_kimlik"] += 1
            return "BASKA_KIMLIK"
        beklenen = hmac.new(self._anahtar, _govde(m["kimlik"], m["port"], m["t"], m["nonce"]),
                            hashlib.sha256).hexdigest()
        if not hmac.compare_digest(beklenen, m["mac"]):
            g["dogrulandi"] = False
            self.sayac["imza_red"] += 1
            return "IMZA_RED"
        fark = m["t"] - self.duvar()
        if self._saat_farki is not None and abs(fark - self._saat_farki) > TAZELIK_PENCERESI_S:
            self.sayac["bayat_red"] += 1
            return "BAYAT_RED"
        if m["nonce"] in self._nonce:
            self.sayac["tekrar_red"] += 1
            return "TEKRAR_RED"
        self._nonce.append(m["nonce"])
        del self._nonce[:-NONCE_HAFIZA]
        if self._saat_farki is None:
            self._saat_farki = fark
        else:                                   # yavas izle (YKS saati kayabilir)
            self._saat_farki = 0.9 * self._saat_farki + 0.1 * fark
        g["dogrulandi"] = True
        yeni = (str(kaynak_ip), int(m["port"]))
        self._son_kabul = simdi
        self.sayac["kabul"] += 1
        if yeni != self.adres:
            eski, self.adres = self.adres, yeni
            if eski is not None:
                self.sayac["adres_degisti"] += 1
            return "ADRES_DEGISTI"
        return "KABUL"

    def durum(self):
        if self.adres is None:
            return "YOK"
        return "TAZE" if self.saat() - self._son_kabul <= SECIM_BAYAT_S else "BAYAT"


class DuyuruYayinci(threading.Thread):
    """YKS tarafi: her DUYURU_ARALIGI_S'de broadcast. Hata YKS'yi durdurmaz."""

    def __init__(self, eslesme, port, *, hedefler=(("255.255.255.255", DUYURU_PORT),),
                 aralik_s=DUYURU_ARALIGI_S, log=print):
        super().__init__(name="yks-duyuru", daemon=True)
        self.eslesme, self.port, self.hedefler = eslesme, int(port), list(hedefler)
        self.aralik_s, self.log = float(aralik_s), log
        self._dur = threading.Event()
        self.gonderilen = 0
        self.hata = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def run(self):
        while not self._dur.is_set():
            paket = duyuru_uret(self.eslesme, self.port)
            for hedef in self.hedefler:
                try:
                    self.sock.sendto(paket, hedef)
                    self.gonderilen += 1
                except OSError as exc:
                    self.hata += 1
                    if self.hata in (1, 100):
                        self.log(f"YKS duyurusu gonderilemedi {hedef}: {exc}")
            self._dur.wait(self.aralik_s)

    def durdur(self):
        self._dur.set()
        try:
            self.sock.close()
        except OSError:
            pass


def dinleyici_soketi(bind=("0.0.0.0", DUYURU_PORT)):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(bind)
    s.settimeout(0.0)
    return s
