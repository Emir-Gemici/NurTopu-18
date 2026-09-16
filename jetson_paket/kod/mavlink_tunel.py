#!/usr/bin/env python3
"""NEDEN (ON_KAYIT results/tunel_20260916 · CONTRACTS §7.6): kullanici karari
(16 Eylul) tek RFD900A ciftini Pixhawk TELEM1'de birakir; Jetson Pixhawk'a
TELEM2 uzerinden 3 telli UART ile baglidir. Pixhawk yalniz MAVLink yonlendirir,
ham NAVITAS baytlarini (comms/protocol.py: tek satir JSON + newline) TELEM2'den
TELEM1'e GECIRMEZ. Bu modul NAVITAS cercevelerini MAVLink2 TUNNEL (id 385,
yuk <= 128 B) mesajlarina parcalayip tasir.

Tasiyici `TunelLink`, `SerialLink` yuzeyini (send / recv + zaman asimi / close)
verir; `seri_hub` (hava) ve `yks_gui` (yer) onu seri port yerine kullanir.
Tuketici surecler DEGISMEZ (CONTRACTS §7.5 ilkesi).

Zincir:
  HAVA: tuketiciler -UDP 5100- seri_hub(TunelLink hava, 14553, 'datagram')
        -UDP- MAVProxy (--out udp:127.0.0.1:14553) -UART 57600- TELEM2
        -Pixhawk yonlendirme- TELEM1 -RFD900A-
  YER : RFD900A -COM- Mission Planner -ayna UDP 14570- yks_gui(TunelLink yer,
        'akis')

TUNNEL.payload ilk 5 bayt big-endian `>BHBB`:
  surum (1) · cerceve_kimligi (uint16) · indis (0..toplam-1) · toplam (1..64)
ardindan 1..123 B yuk. Son olmayan parca TAM 123 B'dir. Tel boyu
= 17 + payload_length (pymavlink 2.4.49 olcumu; son yuk bayti sifir degilken).

Kimlik/adresleme: sysid 247 (0, 1, 255, 51 ile cakismaz), hava compid 25
(USER1), yer compid 26 (USER2), hedef 0/0 (yayin — Pixhawk reboot sonrasi
hedefli adres rotasi silinir, M9). Yasam mesaji (HEARTBEAT) GONDERILMEZ.

AKRAN OGRENME (elestiri 2 bulgu 10): UDP akrani (MAVProxy cikis portu / MP
aynasi) YALNIZ arac HEARTBEAT'i (kaynak sysid = beklenen arac, tip != GCS)
tasiyan datagramin kaynagindan ogrenilir. MAVProxy (mavproxy_link.py
1058-1070) ve MP aynasi arac heartbeat'ini 1 Hz iletir; 14553/14570'e yanlis
MAVLink yazan yerel bir surec tunel hedefini ELE GECIREMEZ. Akran degisimi
KIRMIZI loglanir.

AYRISTIRMA KIPLERI (elestiri 1 bulgu 3): 'datagram' kipinde her datagram YENI
ayristiriciyla cozulur — bu oturumda olculdu: `00 fd 80`+5x00 copunden sonra
KALICI ayristirici iki gecerli TUNNEL'i yuttu, yeni ayristirici ilkini cozdu.
MAVProxy (mavudp) her mesaji ayri datagram yazar -> hava varsayilani
'datagram'. MP aynasinin datagram siniri bilinmiyor (K8-0 i) -> yer
varsayilani 'akis' (kalici ayristirici; obek yazimina dayanikli, copun bedeli
`cozum_hatasi` ile gorunur).

KIMLIK BOSLUGU (elestiri 1 bulgu 4): tek parcali ACK/CMD tamamen duserse
zaman asimi sayaci onu GORMEZ; `Birlestirici` en yuksek kimligi izler ve
atlanan kimlikleri `kimlik_boslugu`na yazar. Kimlik yalniz GERCEKTEN
gonderilen cercevede tuketilir (tavan ustu / akran yok -> tuketilmez).

Ariza semantigi: kuyruk YOK; olagan dis ariza sayac + KIRMIZI log uretir
(ConnectionReset/Refused yutulur); yerel soket arizasi OSError yukseltir ve
hub'in mevcut kapat -> 1 s -> yeniden ac yoluna girer.

pymavlink TEMBEL yuklenir (`TunelLink.__init__`): modul pymavlink'siz import
edilir (Jetson paketi izole import kilidi).
"""
from __future__ import annotations

import random
import select
import socket
import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

from iha_komut_alici import VARSAYILAN_HEDEF_SYSID  # noqa: E402

# ── §7.6 sabitleri — TEK KAYNAK (CONTRACTS §7.6 tablosu; kilit:
#    tests/test_mavlink_tunel_sozlesme.py) ──────────────────────────────────
#: ardupilotmega.MAVLINK_MSG_ID_TUNNEL (test pymavlink ile esitler).
TUNEL_MAVLINK_MSG_ID = 385
#: >32767 yerel deney araligi (common.xml MAV_TUNNEL_PAYLOAD_TYPE); enum'da yok.
TUNEL_PAYLOAD_TYPE = 0xCE56
#: TUNNEL.payload dizisinin boyu (array_lengths[-1]).
TUNEL_MAVLINK_YUK_B = 128
TUNEL_SURUM = 1
TUNEL_BASLIK_BICIMI = ">BHBB"
TUNEL_BASLIK_B = struct.calcsize(TUNEL_BASLIK_BICIMI)
TUNEL_PARCA_YUK_B = TUNEL_MAVLINK_YUK_B - TUNEL_BASLIK_B
#: Tavan KORUNDU: protocol.py "< 4 KiB" beyan eder; olculen en buyuk mesru
#: cerceve 1172 B. 4096'nin altina inmek beyan edilen cerceveyi reddederdi.
TUNEL_AZAMI_PARCA = 64
TUNEL_AZAMI_CERCEVE_B = TUNEL_AZAMI_PARCA * TUNEL_PARCA_YUK_B
#: Kimlik alani uint16 (baslik bicimindeki H).
TUNEL_KIMLIK_MODU = 1 << (8 * struct.calcsize(">H"))
TUNEL_SYSID = 247
TUNEL_HAVA_COMPID = 25     # MAV_COMP_ID_USER1
TUNEL_YER_COMPID = 26      # MAV_COMP_ID_USER2
TUNEL_HEDEF_SYSID = 0      # yayin
TUNEL_HEDEF_COMPID = 0
TUNEL_HAVA_UC = "127.0.0.1:14553"          # MAVProxy --out = hub --tunel
TUNEL_YER_UC = "127.0.0.1:14570"           # MP aynasi = yks_gui --tunel
TUNEL_OLCUM_YANKI_UC = "127.0.0.1:5190"    # K8b: hub ek --tuketici = yanki --bind
#: Hareketsizlik zaman asimi (~4 x A6 RTT p95 126,5 ms); < hafiza.
TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S = 0.5
#: Tamamlanan kimlik hafizasi. KESIN < seri_hub.SERI_YENIDEN_ACMA_ARALIGI_S
#: (1,0 s) ve < systemd RestartSec 2: yeniden acilan ucun yeni kimligi eski
#: hafizaya takilip "yinelenen" diye yutulamaz (elestiri 1 bulgu 7).
TUNEL_TAMAMLANAN_HAFIZA_S = 0.8
TUNEL_ESZAMANLI_KISMI_TAVANI = 16
#: 1 Hz arac heartbeat x 3.
TUNEL_AKRAN_SESSIZLIK_S = 3.0
#: ~5 cerceve/s ile ~51 s kesintiye kadar kayip "bosluk", otesi "sicrama".
#: Rastgele yeniden baslangicin bosluk sanilma olasiligi 256/65536 ~ %0,4
#: (HESAP, olcum degil).
TUNEL_KIMLIK_ILERI_PENCERE = 256
AYRISTIRMA_DATAGRAM = "datagram"
AYRISTIRMA_AKIS = "akis"
TUNEL_HAVA_AYRISTIRMA = AYRISTIRMA_DATAGRAM
TUNEL_YER_AYRISTIRMA = AYRISTIRMA_AKIS
KIMLIK_HAVA = "hava"
KIMLIK_YER = "yer"
TASIYICI_TUNEL = "tunel"
#: UDP datagram tavani (IPv4 UDP yuku 65507 B; seri_hub.UDP_DATAGRAM_TAVANI_B ikizi).
UDP_DATAGRAM_TAVANI_B = 65535
VARSAYILAN_ZAMAN_ASIMI_S = 0.3   # SerialLink varsayilaniyla ayni (K3_12)
LOG_ONEKI = "[TUNEL]"

_COMPID = {KIMLIK_HAVA: TUNEL_HAVA_COMPID, KIMLIK_YER: TUNEL_YER_COMPID}
_KARSI = {KIMLIK_HAVA: KIMLIK_YER, KIMLIK_YER: KIMLIK_HAVA}
_VARSAYILAN_AYRISTIRMA = {KIMLIK_HAVA: TUNEL_HAVA_AYRISTIRMA,
                          KIMLIK_YER: TUNEL_YER_AYRISTIRMA}
_BAD_DATA = "BAD_DATA"


def uc_coz(metin):
    """'HOST:PORT' -> (host, port). Bozuksa ValueError."""
    host, _, port = str(metin).rpartition(":")
    if not host or not port.isdigit() or not 0 <= int(port) <= 65535:
        raise ValueError(f"tunel ucu HOST:PORT olmali: {metin!r}")
    return host.strip("[]"), int(port)


def _varsayilan_log(metin, kirmizi=False):
    seviye = "KIRMIZI " if kirmizi else ""
    print(f"{LOG_ONEKI} {seviye}{metin}",
          file=sys.stderr if kirmizi else sys.stdout, flush=True)


# ── Saf parcalama ────────────────────────────────────────────────────────────

def parcalara_bol(cerceve_kimligi, veri):
    """NAVITAS cercevesini TUNNEL yuklerine bol: [baslik + 1..123 B, ...].

    Bos veri -> [] (gonderilecek bir sey yok). Tavan ustu -> ValueError.
    """
    veri = bytes(veri)
    kimlik = int(cerceve_kimligi)
    if not 0 <= kimlik < TUNEL_KIMLIK_MODU:
        raise ValueError(f"cerceve kimligi uint16 olmali: {cerceve_kimligi!r}")
    if not veri:
        return []
    if len(veri) > TUNEL_AZAMI_CERCEVE_B:
        raise ValueError(f"cerceve {len(veri)} B > tavan {TUNEL_AZAMI_CERCEVE_B} B")
    toplam = -(-len(veri) // TUNEL_PARCA_YUK_B)
    return [struct.pack(TUNEL_BASLIK_BICIMI, TUNEL_SURUM, kimlik, i, toplam)
            + veri[i * TUNEL_PARCA_YUK_B:(i + 1) * TUNEL_PARCA_YUK_B]
            for i in range(toplam)]


class Birlestirici:
    """TUNNEL yuklerinden tam NAVITAS cercevesini kurar (saf; saat enjekte).

    Kurallar: gecerli baslik (surum, 1<=toplam<=64, indis<toplam, son olmayan
    parca tam 123 B); tutarsiz parca (ayni kimlik farkli toplam ya da ayni
    indis farkli icerik) kismi cerceveyi TAMAMEN atar; yinelenen parca yok
    sayilir; sira disi parca kabul edilir; hareketsizlik zaman asimi ve
    eszamanli kismi tavani. Tamamlanan kimlik `hafiza_s` boyunca hatirlanir
    (tek parcali kopya ikinci kez teslim edilmez).
    """

    SAYAC_ANAHTARLARI = ("alinan_parca", "bozuk_parca", "tutarsiz_parca",
                         "yinelenen_parca", "zaman_asimi_dusen",
                         "eszamanli_tavan_dusen", "tamamlanan_cerceve",
                         "kimlik_boslugu", "kimlik_geri", "kimlik_sicramasi")

    def __init__(self, saat=time.monotonic,
                 zaman_asimi_s=TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S,
                 hafiza_s=TUNEL_TAMAMLANAN_HAFIZA_S,
                 eszamanli_tavan=TUNEL_ESZAMANLI_KISMI_TAVANI,
                 kimlik_penceresi=TUNEL_KIMLIK_ILERI_PENCERE, log=None):
        if not callable(saat):
            raise TypeError("saat cagrilabilir olmali")
        self.saat = saat
        self.zaman_asimi_s = float(zaman_asimi_s)
        self.hafiza_s = float(hafiza_s)
        self.eszamanli_tavan = int(eszamanli_tavan)
        self.kimlik_penceresi = int(kimlik_penceresi)
        self.log = log or _varsayilan_log
        self.sayac = {k: 0 for k in self.SAYAC_ANAHTARLARI}
        self._kismi = {}        # kimlik -> {"toplam", "parcalar", "son_t"}
        self._tamamlanan = {}   # kimlik -> tamamlanma ani
        self._en_yuksek = None
        self._sicrama_loglandi = False

    # ── kimlik bosluk izleyicisi ─────────────────────────────────────────
    def _kimlik_izle(self, kimlik):
        if self._en_yuksek is None:
            self._en_yuksek = kimlik            # ilk gorulen: yalniz kayit
            return
        d = (kimlik - self._en_yuksek) % TUNEL_KIMLIK_MODU
        if d == 0:
            return
        if d <= self.kimlik_penceresi:
            self.sayac["kimlik_boslugu"] += d - 1
            self._en_yuksek = kimlik
        elif d >= TUNEL_KIMLIK_MODU - self.kimlik_penceresi:
            self.sayac["kimlik_geri"] += 1
        else:
            self.sayac["kimlik_sicramasi"] += 1
            if not self._sicrama_loglandi:
                self._sicrama_loglandi = True
                self.log(f"kimlik SICRAMASI {self._en_yuksek} -> {kimlik} "
                         f"(karsi uc yeniden basladi?); sonrakiler yalniz "
                         f"kimlik_sicramasi sayacinda", True)
            self._en_yuksek = kimlik

    def tara(self):
        """Zaman asimina ugrayan kismi cerceveleri dusur; dusen sayisini dondur."""
        simdi = self.saat()
        dusen = [k for k, v in self._kismi.items()
                 if simdi - v["son_t"] > self.zaman_asimi_s]
        for k in dusen:
            del self._kismi[k]
        self.sayac["zaman_asimi_dusen"] += len(dusen)
        for k in [k for k, t in self._tamamlanan.items()
                  if simdi - t > self.hafiza_s]:
            del self._tamamlanan[k]
        return len(dusen)

    def ekle(self, yuk):
        """Bir TUNNEL yuku ekle; cerceve tamamlandiysa bytes, yoksa None."""
        self.tara()
        yuk = bytes(yuk)
        if len(yuk) <= TUNEL_BASLIK_B or len(yuk) > TUNEL_MAVLINK_YUK_B:
            self.sayac["bozuk_parca"] += 1
            return None
        surum, kimlik, indis, toplam = struct.unpack_from(TUNEL_BASLIK_BICIMI, yuk)
        parca = yuk[TUNEL_BASLIK_B:]
        if (surum != TUNEL_SURUM or not 1 <= toplam <= TUNEL_AZAMI_PARCA
                or indis >= toplam
                or (indis < toplam - 1 and len(parca) != TUNEL_PARCA_YUK_B)):
            self.sayac["bozuk_parca"] += 1
            return None
        self.sayac["alinan_parca"] += 1
        self._kimlik_izle(kimlik)
        simdi = self.saat()
        if kimlik in self._tamamlanan:
            self.sayac["yinelenen_parca"] += 1
            return None
        k = self._kismi.get(kimlik)
        if k is None:
            if len(self._kismi) >= self.eszamanli_tavan:
                eski = min(self._kismi, key=lambda x: self._kismi[x]["son_t"])
                del self._kismi[eski]
                self.sayac["eszamanli_tavan_dusen"] += 1
            k = {"toplam": toplam, "parcalar": {}, "son_t": simdi}
            self._kismi[kimlik] = k
        elif k["toplam"] != toplam:
            self.sayac["tutarsiz_parca"] += 1
            del self._kismi[kimlik]
            return None
        onceki = k["parcalar"].get(indis)
        if onceki is not None:
            if onceki != parca:
                self.sayac["tutarsiz_parca"] += 1
                del self._kismi[kimlik]
                return None
            self.sayac["yinelenen_parca"] += 1
            k["son_t"] = simdi
            return None
        k["parcalar"][indis] = parca
        k["son_t"] = simdi
        if len(k["parcalar"]) < toplam:
            return None
        del self._kismi[kimlik]
        self._tamamlanan[kimlik] = simdi
        self.sayac["tamamlanan_cerceve"] += 1
        return b"".join(k["parcalar"][i] for i in range(toplam))


# ── Tasiyici ─────────────────────────────────────────────────────────────────

class TunelLink:
    """MAVLink2 TUNNEL tasiyicisi — `SerialLink` yuzeyi (send/recv/close).

    `recv` her zaman (bytes|None, None) dondurur: adres katmani yoktur (seri
    tasiyici gibi), bir cagri en cok bir TAM cerceve teslim eder; `timeout`
    cagri basina TOPLAM son tarihtir (yabanci MAVLink seli altinda da).
    """

    SAHA_TASIYICI = True
    TASIYICI_ADI = TASIYICI_TUNEL

    LINK_SAYAC_ANAHTARLARI = (
        "gonderilen_cerceve", "gonderilen_parca", "tavan_ustu", "akran_yok",
        "gonderim_hatasi", "akran_sessizken_gonderilen", "alinan_datagram",
        "mavlink_paket", "cozum_hatasi", "yabanci_mesaj", "yabanci_payload_type",
        "kendi_yanki", "yabanci_kaynak", "teslim_cerceve", "udp_red",
        "akrandisi_datagram", "akran_degisti")

    def __init__(self, bind=("127.0.0.1", 0), kimlik=KIMLIK_HAVA, *, peer=None,
                 timeout=VARSAYILAN_ZAMAN_ASIMI_S, reuse=False, ayristirma=None,
                 beklenen_arac_sysid=VARSAYILAN_HEDEF_SYSID,
                 saat=time.monotonic, log=None, ilk_kimlik=None):
        if kimlik not in _COMPID:
            raise ValueError(f"kimlik 'hava' ya da 'yer' olmali: {kimlik!r}")
        if ayristirma is None:
            ayristirma = _VARSAYILAN_AYRISTIRMA[kimlik]
        if ayristirma not in (AYRISTIRMA_DATAGRAM, AYRISTIRMA_AKIS):
            raise ValueError(f"ayristirma 'datagram' ya da 'akis' olmali: {ayristirma!r}")
        if not callable(saat):
            raise TypeError("saat cagrilabilir olmali")
        if isinstance(bind, str):
            bind = uc_coz(bind)
        from pymavlink.dialects.v20 import ardupilotmega as mav_modul  # tembel
        self._m = mav_modul
        self.kimlik = kimlik
        self.compid = _COMPID[kimlik]
        self.karsi_compid = _COMPID[_KARSI[kimlik]]
        self.ayristirma = ayristirma
        self.beklenen_arac_sysid = int(beklenen_arac_sysid)
        self.saat = saat
        self.log = log or _varsayilan_log
        self._kilit = threading.Lock()
        self._link_sayac = {k: 0 for k in self.LINK_SAYAC_ANAHTARLARI}
        self.birlestirici = Birlestirici(saat=saat, log=self.log)
        # Kodlayici ve ayristirici AYRI nesnelerdir (paket seq'i / tampon karismaz).
        self._kodlayici = mav_modul.MAVLink(None, srcSystem=TUNEL_SYSID,
                                            srcComponent=self.compid)
        self._kalici = self._yeni_ayristirici()
        if ilk_kimlik is None:
            ilk_kimlik = random.SystemRandom().randrange(TUNEL_KIMLIK_MODU)
        self._sonraki_kimlik = int(ilk_kimlik) % TUNEL_KIMLIK_MODU
        self._teslim = deque()
        self._kapali = False
        self._timeout = None
        self.timeout = timeout
        self.akran = None if peer is None else (str(peer[0]), int(peer[1]))
        self._son_akran_t = saat() if self.akran is not None else None
        self._akran_yok_loglandi = False
        self._sessizlik_loglandi = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # UDPLink kalibi (D-405 tek sahiplik): reuse=False -> ikinci bind OSError.
        if reuse:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        elif hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            self.sock.bind(bind)
        except OSError:
            self.sock.close()
            raise

    # ── ozellikler ───────────────────────────────────────────────────────
    @property
    def port(self):
        return self.sock.getsockname()[1]

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, deger):
        deger = float(deger)
        if not deger >= 0:
            raise ValueError("timeout >= 0 olmali")
        self._timeout = deger

    @property
    def sayac(self):
        """Link + birlestirici sayaclari (kopya)."""
        birlesik = dict(self._link_sayac)
        birlesik.update(self.birlestirici.sayac)
        return birlesik

    def _yeni_ayristirici(self):
        ayr = self._m.MAVLink(None, srcSystem=0, srcComponent=0)
        ayr.robust_parsing = True
        return ayr

    def _kapali_mi(self):
        if self._kapali:
            raise OSError("TunelLink kapali")

    # ── gonderim ─────────────────────────────────────────────────────────
    def send(self, data, peer=None):     # noqa: ARG002 — peer yok sayilir
        self._kapali_mi()
        if not data:
            return
        data = bytes(data)
        if len(data) > TUNEL_AZAMI_CERCEVE_B:
            self._link_sayac["tavan_ustu"] += 1
            self.log(f"cerceve {len(data)} B > tavan {TUNEL_AZAMI_CERCEVE_B} B: "
                     f"GONDERILMEDI (tavan_ustu={self._link_sayac['tavan_ustu']})",
                     True)
            return
        with self._kilit:
            akran = self.akran
            if akran is None:
                self._link_sayac["akran_yok"] += 1
                if not self._akran_yok_loglandi:
                    self._akran_yok_loglandi = True
                    self.log(f"akran YOK (arac HEARTBEAT'i henuz gelmedi): cerceve "
                             f"dusuruldu; sonrakiler yalniz akran_yok sayacinda",
                             True)
                return
            if (self._son_akran_t is not None
                    and self.saat() - self._son_akran_t > TUNEL_AKRAN_SESSIZLIK_S):
                self._link_sayac["akran_sessizken_gonderilen"] += 1
                if not self._sessizlik_loglandi:
                    self._sessizlik_loglandi = True
                    self.log(f"akran {akran[0]}:{akran[1]} {TUNEL_AKRAN_SESSIZLIK_S:.0f} s"
                             f"'den uzun SESSIZ; gonderim suruyor (bolum basina tek log)",
                             True)
            kimlik = self._sonraki_kimlik
            self._sonraki_kimlik = (kimlik + 1) % TUNEL_KIMLIK_MODU
            self._link_sayac["gonderilen_cerceve"] += 1
            for parca in parcalara_bol(kimlik, data):
                dolgu = bytes(TUNEL_MAVLINK_YUK_B - len(parca))
                paket = self._kodlayici.tunnel_encode(
                    TUNEL_HEDEF_SYSID, TUNEL_HEDEF_COMPID, TUNEL_PAYLOAD_TYPE,
                    len(parca), parca + dolgu).pack(self._kodlayici)
                try:
                    self.sock.sendto(paket, akran)
                except (ConnectionResetError, ConnectionRefusedError):
                    self._link_sayac["gonderim_hatasi"] += 1
                    return
                self._link_sayac["gonderilen_parca"] += 1

    # ── alim ─────────────────────────────────────────────────────────────
    def _datagram_isle(self, veri, adr):
        self._link_sayac["alinan_datagram"] += 1
        ayr = (self._yeni_ayristirici() if self.ayristirma == AYRISTIRMA_DATAGRAM
               else self._kalici)
        try:
            mesajlar = ayr.parse_buffer(veri) or []
        except Exception:                     # ayristirici hic bir veriyle olmemeli
            self._link_sayac["cozum_hatasi"] += 1
            if self.ayristirma == AYRISTIRMA_AKIS:
                self._kalici = self._yeni_ayristirici()
            mesajlar = []
        arac_hb = False
        hb_id = self._m.MAVLINK_MSG_ID_HEARTBEAT
        for msg in mesajlar:
            if msg.get_type() == _BAD_DATA:
                self._link_sayac["cozum_hatasi"] += 1
                continue
            self._link_sayac["mavlink_paket"] += 1
            msgid = msg.get_msgId()
            if msgid == hb_id:
                if (msg.get_srcSystem() == self.beklenen_arac_sysid
                        and msg.type != self._m.MAV_TYPE_GCS):
                    arac_hb = True
                continue
            if msgid != TUNEL_MAVLINK_MSG_ID:
                self._link_sayac["yabanci_mesaj"] += 1
                continue
            if msg.payload_type != TUNEL_PAYLOAD_TYPE:
                self._link_sayac["yabanci_payload_type"] += 1
                continue
            kaynak = (msg.get_srcSystem(), msg.get_srcComponent())
            if kaynak == (TUNEL_SYSID, self.compid):
                self._link_sayac["kendi_yanki"] += 1
                continue
            if kaynak != (TUNEL_SYSID, self.karsi_compid):
                self._link_sayac["yabanci_kaynak"] += 1
                continue
            uzunluk = int(msg.payload_length)
            if not 0 <= uzunluk <= TUNEL_MAVLINK_YUK_B:
                self.birlestirici.sayac["bozuk_parca"] += 1
                continue
            cerceve = self.birlestirici.ekle(bytes(msg.payload[:uzunluk]))
            if cerceve is not None:
                self._link_sayac["teslim_cerceve"] += 1
                self._teslim.append(cerceve)
        adr = (str(adr[0]), int(adr[1]))
        with self._kilit:
            if arac_hb:
                if self.akran is None:
                    self.log(f"akran ogrenildi (arac HEARTBEAT): {adr[0]}:{adr[1]}")
                elif adr != self.akran:
                    self._link_sayac["akran_degisti"] += 1
                    self.log(f"akran DEGISTI {self.akran[0]}:{self.akran[1]} -> "
                             f"{adr[0]}:{adr[1]} (akran_degisti="
                             f"{self._link_sayac['akran_degisti']})", True)
                self.akran = adr
                self._son_akran_t = self.saat()
                self._sessizlik_loglandi = False
                self._akran_yok_loglandi = False
            elif adr == self.akran:
                self._son_akran_t = self.saat()
                self._sessizlik_loglandi = False
            else:
                self._link_sayac["akrandisi_datagram"] += 1

    def recv(self, bufsize=TUNEL_AZAMI_CERCEVE_B):   # noqa: ARG002 — cerceve bolunmez
        """(cerceve, None); son tarih icinde tam cerceve yoksa (None, None)."""
        self._kapali_mi()
        son = time.monotonic() + self._timeout
        while True:
            self.birlestirici.tara()
            if self._teslim:
                return self._teslim.popleft(), None
            kalan = son - time.monotonic()
            try:
                hazir, _, _ = select.select([self.sock], [], [], max(0.0, kalan))
            except (ValueError, OSError):
                self._kapali_mi()
                raise
            if not hazir:
                return None, None
            try:
                veri, adr = self.sock.recvfrom(UDP_DATAGRAM_TAVANI_B)
            except (ConnectionResetError, ConnectionRefusedError):
                self._link_sayac["udp_red"] += 1
                if time.monotonic() >= son:
                    return None, None
                continue
            self._datagram_isle(veri, adr)
            if not self._teslim and time.monotonic() >= son:
                return None, None

    def close(self):
        if self._kapali:
            return
        self._kapali = True
        self.sock.close()
