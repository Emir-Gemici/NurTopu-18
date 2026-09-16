#!/usr/bin/env python3
"""BU GERCEK ARDUPILOT DEGILDIR. — tezgah taklidi (CONTRACTS §7.6 · K4).

NEDEN: MAVLink TUNNEL koprusu (comms/mavlink_tunel.py) Pixhawk'in MAVLink
yonlendirmesine dayanir; gelistirme makinesinde Pixhawk yoktur. Bu modul
ArduPilot Copter-4.5 `GCS_MAVLink/MAVLink_routing.cpp` davranisinin tasarimda
kullanilan kurallarini UDP soketleri uzerinde taklit eder. Kurallar depoda
DOGRULANMADI; hukum gercek donanim olcumundedir (K8a/K8b). K4 kapilari yalniz
BU MODELI kanitlar.

Yonlendirme kurallari (tasarim):
  * rota her mesajdan ogrenilir: kaynak sysid -> gelen kanal;
  * HEARTBEAT gelen kanal DISINDAKI tum kanallara iletilir;
  * target_system 0 (ya da hedef alani olmayan) mesaj, rotasi olan (en az bir
    sysid ogrenilmis) kanallara iletilir, gelen kanala geri gonderilmez;
  * hedefli mesaj yalniz o sysid'in rotasi olan kanala gider; kendi sysid'ine
    hedefli mesaj yerelde tuketilir (iletilmez);
  * TX alani yetmezse (`txspace < len`) paket SESSIZCE duser (`txspace_dusen`).

Hat modeli (elestiri 1 bulgu 1/2/5, elestiri 2 bulgu 1): kanal ve yon basina
bayt kovasi; `hat_bps/10` B/s ile bosalan kuyruk. TX kuyrugu `tx_tampon_b` ile
sinirli (None = sinirsiz); RX kuyrugu karsi ucun UART'idir (sinirsiz, yalniz
hiz). Arka plan akis ureticisi SR benzeri kucuk mesajlarla TX kovasini
doldurur. Kuyruk gecikmesi GERCEK zamanla uygulanir.

Kayip karari (belirlenimci; DUZELTME TURU 1): yalniz TUNNEL mesajlarina
uygulanir ve `blake2b(tohum || kaynak_kanal || hedef_kanal || ileti_no ||
kopya_no || indis || toplam)` ozetine baglidir — RNG cekilis sirasina da,
cerceve KIMLIGINE de degil.
  * `ileti_no`: bu kaynak kanalda gorulen FARKLI NAVITAS cercevelerinin sira
    numarasi. Cerceve icerigi `t` zaman damgasi normallestirilerek
    karsilastirilir (seq/ref ve diger alanlar korunur).
  * `kopya_no`: ayni icerigin kacinci kopyasi (her kopya yeni kimlik tasir).
NEDEN (curutucu olcumu): ilk surum ozeti 5 B NAVITAS basligina (kimlik dahil)
bagliyordu. Kimlik her GONDERILEN kopyada artar; IhaSender ACK gelince
tekrari keser, yani kopya sayisi ACK'in 0,25 s pencereye yetisip
yetismedigine (gercek zaman) baglidir. Bir denemenin fazladan kopyasi
sonraki tum denemelerin kimliklerini, dolayisiyla kayip kararlarini kaydirdi:
ayni tohumla `kayip_dusen` 12/12/11/6 ve K4 1024 B alt vakasi 4 kosuda 3 kez
DUSTU, 1 kez GECTI. Yeni anahtar "N. denemenin k. kopyasinin i. parcasi"
kimligidir; kopya var oldugu surece kaderi kosudan kosuya aynidir.
Kayip, TX kuyrugundan HATTA CIKISTA uygulanir (radyoda kayip: paket UART
tamponunu gercekten isgal etmistir). Parcalar alim aninda (soketten
okunurken) kaydedilir; karar anina dek tum parcalar gelmemisse (ornegin
gonderici bir parcayi hic yollamadiysa) eski baslik ozetine dusulur ve
`kayip_anahtari_eksik` sayilir — sessiz degil.
Belirlenimci OLMAYAN bilesen (ON KAYIT'ta yazili): hat/kuyruk zamanlamasi
gercek saatle isler; `txspace_dusen` ve son kopyanin ACK'inin 0,25 s
pencereye yetismesi CPU yukune baglidir.

`MavproxyTaklit`: master (Pixhawk kanali) ile `--out` uclari arasinda aktarici.
Master'dan gelen her mesaj her cikisa AYRI datagramla yazilir (mavudp kalibi);
cikistan gelen, `mavfwd=True` iken master'a yazilir (MAVProxy 1.8.74
mavproxy.py:898-903). `heartbeat=(sysid, compid)` ile 1 Hz GCS heartbeat'i
master'a yollar (MAVProxy 255/230; Mission Planner aynasi taklidinde 255/190).
"""
from __future__ import annotations

import hashlib
import re
import select
import socket
import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

from mavlink_tunel import (TUNEL_BASLIK_B, TUNEL_BASLIK_BICIMI,  # noqa: E402
                           TUNEL_MAVLINK_MSG_ID, TUNEL_PAYLOAD_TYPE,
                           UDP_DATAGRAM_TAVANI_B)

YEREL = "127.0.0.1"
#: UART cercevesi: 1 baslangic + 8 veri + 1 bitis biti = 10 bit/bayt.
UART_BIT_PER_BAYT = 10
#: Dongu uyku tavani (olay yoksa): Windows tanecigi ~15,6 ms'in altinda.
DONGU_BEKLEME_TAVANI_S = 0.005
VARSAYILAN_HEARTBEAT_ARALIGI_S = 1.0
#: MAVProxy'nin GCS kimligi (mavproxy.py --source-system/--source-component varsayilani).
MAVPROXY_GCS_KIMLIGI = (255, 230)
#: Mission Planner GCS kimligi (MP varsayilani 255/190).
MP_GCS_KIMLIGI = (255, 190)
_BAD_DATA = "BAD_DATA"
#: NAVITAS JSON'undaki `t` zaman damgasi (protocol.encode: ayiricisiz JSON).
_ZAMAN_DAMGASI = re.compile(rb'"t":-?[0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?')
_ZAMAN_DAMGASI_YERINE = b'"t":_'
#: Kaydedilen kimlik tavani (bellek; eski kayitlar FIFO ile atilir).
PARCA_KAYDI_TAVANI = 4096


def _mav():
    from pymavlink.dialects.v20 import ardupilotmega as m   # tembel
    return m


def _ayristirici(m):
    a = m.MAVLink(None, srcSystem=0, srcComponent=0)
    a.robust_parsing = True
    return a


class Kova:
    """Hiz sinirli bayt kuyrugu (saf; saat disaridan verilir).

    `bps_b` bayt/s (None = sinirsiz), `tampon_b` bekleyen bayt tavani
    (None = sinirsiz). Paket, onundeki paketler hatta dokulunce dokulmeye
    baslar; cikis ani = baslangic + len / bps_b.

    Bekleyen bayt BAYT duzeyinde hesaplanir: hatta dokulmekte olan paketin
    gonderilmis kismi tampondan cikmistir (UART halka tamponu; ArduPilot
    `txspace` bayt sayar). Ilk surum paketi cikis anina dek TAMAMEN sayiyordu;
    256 B tamponda bu, paket basina ~yarim paketlik sahte doluluk demekti
    (K4 ilk kosusu, results/tunel_20260916/kapilar_uygulama.txt).
    """

    def __init__(self, bps_b=None, tampon_b=None):
        self.bps_b = None if bps_b is None else float(bps_b)
        self.tampon_b = None if tampon_b is None else int(tampon_b)
        self.kuyruk = deque()
        self.bekleyen_b = 0
        self._bosta_t = 0.0

    def bekleyen(self, simdi):
        """Henuz hatta dokulmemis bayt sayisi (bayt duzeyinde)."""
        if self.bps_b is None:
            return float(self.bekleyen_b)
        return max(0.0, self._bosta_t - float(simdi)) * self.bps_b

    def txspace(self, simdi):
        return None if self.tampon_b is None else self.tampon_b - self.bekleyen(simdi)

    def ekle(self, simdi, paket, ek=None):
        n = len(paket)
        if self.tampon_b is not None and self.bekleyen(simdi) + n > self.tampon_b + 1e-9:
            return False
        if self.bps_b is None:
            cikis = simdi
        else:
            cikis = max(simdi, self._bosta_t) + n / self.bps_b
            self._bosta_t = cikis
        self.kuyruk.append((cikis, paket, ek))
        self.bekleyen_b += n
        return True

    def hazirlar_ek(self, simdi):
        """Hatta dokulen paketler, `ekle`deki `ek` bilgisiyle: [(paket, ek)]."""
        cikan = []
        while self.kuyruk and self.kuyruk[0][0] <= simdi:
            _, paket, ek = self.kuyruk.popleft()
            self.bekleyen_b -= len(paket)
            cikan.append((paket, ek))
        return cikan

    def hazirlar(self, simdi):
        return [paket for paket, _ in self.hazirlar_ek(simdi)]

    def sonraki_t(self):
        return self.kuyruk[0][0] if self.kuyruk else None

    def temizle(self):
        self.kuyruk.clear()
        self.bekleyen_b = 0
        self._bosta_t = 0.0


def _ozet_orani(anahtar):
    ozet = hashlib.blake2b(anahtar, digest_size=8).digest()
    return int.from_bytes(ozet, "big") / float(1 << 64)


def kayip_ozeti(tohum, kaynak_kanal, hedef_kanal, tunnel_yuku):
    """YEDEK anahtar: [0, 1) deger (tohum + kanallar + 5 B NAVITAS basligi).

    Kimligi icerdigi icin gonderim sirasina baglidir; yalniz kopya anahtari
    kurulamadiginda kullanilir (`kayip_anahtari_eksik`)."""
    anahtar = (struct.pack(">QBB", int(tohum) & 0xFFFFFFFFFFFFFFFF,
                           int(kaynak_kanal), int(hedef_kanal))
               + bytes(tunnel_yuku)[:TUNEL_BASLIK_B])
    return _ozet_orani(anahtar)


def kopya_kayip_ozeti(tohum, kaynak_kanal, hedef_kanal, ileti_no, kopya_no, indis, toplam):
    """[0, 1) deger: 'kaynak kanaldaki ileti_no. farkli cercevenin kopya_no.
    kopyasinin indis/toplam parcasi' — kimlikten ve zaman damgasindan bagimsiz."""
    anahtar = struct.pack(">QBBIIBB", int(tohum) & 0xFFFFFFFFFFFFFFFF,
                          int(kaynak_kanal), int(hedef_kanal), int(ileti_no),
                          int(kopya_no), int(indis), int(toplam))
    return _ozet_orani(anahtar)


def cerceve_icerik_anahtari(cerceve):
    """NAVITAS cercevesi -> `t` zaman damgasi normallestirilmis icerik."""
    return _ZAMAN_DAMGASI.sub(_ZAMAN_DAMGASI_YERINE, bytes(cerceve))


class ArdupilotYonlendiriciTaklit:
    """BU GERCEK ARDUPILOT DEGILDIR. Kanal = bir UDP soketi (UART yerine)."""

    def __init__(self, kanal_sayisi=2, sysid=1, compid=1, kayip=0.0, tohum=0,
                 hat_bps=None, tx_tampon_b=None, arka_plan=None,
                 heartbeat_aralik_s=VARSAYILAN_HEARTBEAT_ARALIGI_S):
        self._m = _mav()
        self.kanal_sayisi = int(kanal_sayisi)
        self.sysid, self.compid = int(sysid), int(compid)
        self.kayip = float(kayip)
        self.tohum = int(tohum)
        bps_b = None if hat_bps is None else float(hat_bps) / UART_BIT_PER_BAYT
        self.hat_bps = hat_bps
        self.arka_plan = {int(k): float(v) for k, v in (arka_plan or {}).items()}
        self.heartbeat_aralik_s = float(heartbeat_aralik_s)
        self.socks = []
        for _ in range(self.kanal_sayisi):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((YEREL, 0))
            self.socks.append(s)
        self.akranlar = [None] * self.kanal_sayisi
        self.tx = [Kova(bps_b, tx_tampon_b) for _ in range(self.kanal_sayisi)]
        self.rx = [Kova(bps_b, None) for _ in range(self.kanal_sayisi)]
        self._ayr = [_ayristirici(self._m) for _ in range(self.kanal_sayisi)]
        self._kod = self._m.MAVLink(None, srcSystem=self.sysid, srcComponent=self.compid)
        self.rotalar = {}                     # sysid -> {kanal}
        self.sayac = {"alinan_paket": 0, "iletilen": 0, "txspace_dusen": 0,
                      "kayip_dusen": 0, "yerel": 0, "hedefsiz": 0, "bozuk": 0,
                      "arka_plan_b": 0, "arka_plan_atlanan": 0, "heartbeat": 0,
                      "sifirlama": 0, "kesintide_atilan": 0,
                      "kayip_anahtari_eksik": 0}
        # Kopya anahtari (belirlenimci kayip; modul dokstringi):
        self._kayit_ayr = [_ayristirici(self._m) for _ in range(self.kanal_sayisi)]
        self._parca_kaydi = [dict() for _ in range(self.kanal_sayisi)]    # kimlik -> kayit
        self._ileti_defteri = [dict() for _ in range(self.kanal_sayisi)]  # icerik -> [no, kopya]
        self._kilit = threading.RLock()
        self._dur = threading.Event()
        self._iplik = None
        self._son_hb_t = None
        self._kredi = {k: 0.0 for k in self.arka_plan}
        self._son_t = None
        self._kesinti_bitis = 0.0

    # ── kurulum ──────────────────────────────────────────────────────────
    def kanal_adresi(self, kanal):
        return self.socks[kanal].getsockname()

    def kanal_bagla(self, kanal, adr):
        with self._kilit:
            self.akranlar[kanal] = (str(adr[0]), int(adr[1]))

    def kayip_mi(self, kaynak_kanal, hedef_kanal, tunnel_yuku):
        """Kayip karari. Kopya anahtari kurulmussa onunla (belirlenimci), yoksa
        yedek baslik ozetiyle (`kayip_anahtari_eksik` sayilir)."""
        if self.kayip <= 0.0:
            return False
        yuk = bytes(tunnel_yuku)
        anahtar = self._kopya_anahtari(kaynak_kanal, yuk)
        if anahtar is None:
            self.sayac["kayip_anahtari_eksik"] += 1
            return kayip_ozeti(self.tohum, kaynak_kanal, hedef_kanal, yuk) < self.kayip
        ileti_no, kopya_no, indis, toplam = anahtar
        return kopya_kayip_ozeti(self.tohum, kaynak_kanal, hedef_kanal, ileti_no,
                                 kopya_no, indis, toplam) < self.kayip

    # ── kopya anahtari: alim aninda parca kaydi ─────────────────────────
    def parca_kaydet(self, kanal, tunnel_yuku):
        """Bir TUNNEL yukunu kaynak kanalin parca kaydina isle (alim ani).

        Kimligin tum parcalari geldiginde icerik (t normallestirilmis) ileti
        defterine yazilir: yeni icerik yeni `ileti_no`, bilinen icerik
        `kopya_no`+1. Kimlik tekrar kullanilirsa (farkli icerikli parca) kayit
        sifirlanir."""
        yuk = bytes(tunnel_yuku)
        if len(yuk) <= TUNEL_BASLIK_B:
            return
        _surum, kimlik, indis, toplam = struct.unpack_from(TUNEL_BASLIK_BICIMI, yuk)
        if toplam == 0 or indis >= toplam:
            return
        kayitlar = self._parca_kaydi[kanal]
        kayit = kayitlar.get(kimlik)
        parca = yuk[TUNEL_BASLIK_B:]
        if kayit is not None and (kayit["toplam"] != toplam
                                  or kayit["parcalar"].get(indis, parca) != parca):
            del kayitlar[kimlik]
            kayit = None
        if kayit is None:
            if len(kayitlar) >= PARCA_KAYDI_TAVANI:
                del kayitlar[next(iter(kayitlar))]
            kayit = {"toplam": toplam, "parcalar": {}, "anahtar": None}
            kayitlar[kimlik] = kayit
        kayit["parcalar"][indis] = parca
        if kayit["anahtar"] is None and len(kayit["parcalar"]) == toplam:
            icerik = cerceve_icerik_anahtari(
                b"".join(kayit["parcalar"][i] for i in range(toplam)))
            defter = self._ileti_defteri[kanal].setdefault(
                icerik, [len(self._ileti_defteri[kanal]), 0])
            defter[1] += 1
            kayit["anahtar"] = (defter[0], defter[1])

    def _kopya_anahtari(self, kanal, yuk):
        if len(yuk) <= TUNEL_BASLIK_B:
            return None
        _surum, kimlik, indis, toplam = struct.unpack_from(TUNEL_BASLIK_BICIMI, yuk)
        kayit = self._parca_kaydi[kanal].get(kimlik)
        if kayit is None or kayit["anahtar"] is None or kayit["toplam"] != toplam:
            return None
        return kayit["anahtar"] + (indis, toplam)

    def _kaydet_datagram(self, kanal, veri):
        for msg in self._kayit_ayr[kanal].parse_buffer(veri) or []:
            if (msg.get_type() != _BAD_DATA and msg.get_msgId() == TUNEL_MAVLINK_MSG_ID
                    and msg.payload_type == TUNEL_PAYLOAD_TYPE):
                self.parca_kaydet(kanal, bytes(msg.payload[:int(msg.payload_length)]))

    def sifirla(self, kesinti_s=0.0):
        """Reboot benzetimi: rotalar silinir, kuyruklar bosalir; `kesinti_s`
        boyunca gelen her sey atilir ve heartbeat gonderilmez."""
        with self._kilit:
            self.rotalar.clear()
            for k in self.tx + self.rx:
                k.temizle()
            self._ayr = [_ayristirici(self._m) for _ in range(self.kanal_sayisi)]
            self._kayit_ayr = [_ayristirici(self._m) for _ in range(self.kanal_sayisi)]
            for kayitlar in self._parca_kaydi:
                kayitlar.clear()
            self._kesinti_bitis = time.monotonic() + float(kesinti_s)
            self._son_hb_t = None
            self.sayac["sifirlama"] += 1

    # ── yonlendirme ──────────────────────────────────────────────────────
    def _rotali_kanal(self, kanal):
        return any(kanal in s for s in self.rotalar.values())

    def _hedefler(self, msg, gelen):
        msgid = msg.get_msgId()
        diger = [k for k in range(self.kanal_sayisi)
                 if k != gelen and self.akranlar[k] is not None]
        if msgid == self._m.MAVLINK_MSG_ID_HEARTBEAT:
            return diger
        hedef = getattr(msg, "target_system", None)
        if hedef is None or int(hedef) == 0:
            return [k for k in diger if self._rotali_kanal(k)]
        if int(hedef) == self.sysid:
            self.sayac["yerel"] += 1
            return []
        return [k for k in diger if k in self.rotalar.get(int(hedef), ())]

    def _yonlendir(self, gelen, veri, simdi):
        for msg in self._ayr[gelen].parse_buffer(veri) or []:
            if msg.get_type() == _BAD_DATA:
                self.sayac["bozuk"] += 1
                continue
            self.sayac["alinan_paket"] += 1
            self.rotalar.setdefault(int(msg.get_srcSystem()), set()).add(gelen)
            hedefler = self._hedefler(msg, gelen)
            if not hedefler and msg.get_msgId() != self._m.MAVLINK_MSG_ID_HEARTBEAT:
                if getattr(msg, "target_system", None) != self.sysid:
                    self.sayac["hedefsiz"] += 1
            ham = bytes(msg.get_msgbuf())
            tunel = msg.get_msgId() == TUNEL_MAVLINK_MSG_ID
            ek = (gelen, bytes(msg.payload)) if tunel else None
            for h in hedefler:
                # Kayip burada DEGIL, hatta cikista (radyo) uygulanir: paket TX
                # tamponunu gercekten isgal eder (kopya anahtari icin dokstring).
                if not self.tx[h].ekle(simdi, ham, ek):
                    self.sayac["txspace_dusen"] += 1
                    continue
                self.sayac["iletilen"] += 1

    def _heartbeat_ve_arka_plan(self, simdi):
        if simdi < self._kesinti_bitis:
            return
        if (self._son_hb_t is None
                or simdi - self._son_hb_t >= self.heartbeat_aralik_s):
            self._son_hb_t = simdi
            hb = self._kod.heartbeat_encode(
                self._m.MAV_TYPE_QUADROTOR, self._m.MAV_AUTOPILOT_ARDUPILOTMEGA,
                0, 0, self._m.MAV_STATE_STANDBY).pack(self._kod)
            for k in range(self.kanal_sayisi):
                if self.akranlar[k] is not None and self.tx[k].ekle(simdi, hb):
                    self.sayac["heartbeat"] += 1
        dt = 0.0 if self._son_t is None else max(0.0, simdi - self._son_t)
        for k, bps in self.arka_plan.items():
            if self.akranlar[k] is None:
                continue
            self._kredi[k] = min(self._kredi[k] + bps * dt, bps)   # patlama tavani 1 s
            while True:
                paket = self._kod.attitude_encode(
                    int(simdi * 1000) & 0xFFFFFFFF, 0.1, 0.2, 0.3, 0.01, 0.02,
                    0.03).pack(self._kod)
                if self._kredi[k] < len(paket):
                    break
                self._kredi[k] -= len(paket)
                if self.tx[k].ekle(simdi, paket):
                    self.sayac["arka_plan_b"] += len(paket)
                else:
                    self.sayac["arka_plan_atlanan"] += 1   # akis mesaji: yer yoksa atlanir
        self._son_t = simdi

    def tur(self, bekleme_s=DONGU_BEKLEME_TAVANI_S):
        """Bir dongu turu (test icin disaridan da cagrilabilir)."""
        with self._kilit:
            simdi = time.monotonic()
            self._heartbeat_ve_arka_plan(simdi)
            for k in range(self.kanal_sayisi):
                for veri in self.rx[k].hazirlar(simdi):
                    self._yonlendir(k, veri, simdi)
                for paket, ek in self.tx[k].hazirlar_ek(simdi):
                    if ek is not None and self.kayip_mi(ek[0], k, ek[1]):
                        self.sayac["kayip_dusen"] += 1
                        continue
                    if self.akranlar[k] is not None:
                        try:
                            self.socks[k].sendto(paket, self.akranlar[k])
                        except OSError:
                            pass
            olaylar = [t for q in self.tx + self.rx
                       for t in (q.sonraki_t(),) if t is not None]
        bekle = bekleme_s
        if olaylar:
            bekle = max(0.0, min(bekle, min(olaylar) - time.monotonic()))
        try:
            hazir, _, _ = select.select(self.socks, [], [], bekle)
        except (OSError, ValueError):
            return
        for s in hazir:
            k = self.socks.index(s)
            try:
                veri, adr = s.recvfrom(UDP_DATAGRAM_TAVANI_B)
            except OSError:
                continue
            with self._kilit:
                simdi = time.monotonic()
                if simdi < self._kesinti_bitis:
                    self.sayac["kesintide_atilan"] += 1
                    continue
                self.akranlar[k] = (str(adr[0]), int(adr[1]))
                self._kaydet_datagram(k, veri)
                self.rx[k].ekle(simdi, veri)

    def baslat(self):
        self._dur.clear()
        self._iplik = threading.Thread(target=self._dongu, daemon=True,
                                       name="ardupilot-taklit")
        self._iplik.start()
        return self

    def _dongu(self):
        while not self._dur.is_set():
            self.tur()

    def durdur(self):
        self._dur.set()
        if self._iplik is not None:
            self._iplik.join(timeout=2.0)
        for s in self.socks:
            try:
                s.close()
            except OSError:
                pass


class MavproxyTaklit:
    """BU GERCEK MAVPROXY DEGILDIR. master <-> --out uclari aktaricisi."""

    def __init__(self, master, outs, mavfwd=True, heartbeat=MAVPROXY_GCS_KIMLIGI,
                 heartbeat_aralik_s=VARSAYILAN_HEARTBEAT_ARALIGI_S):
        self._m = _mav()
        self.master = (str(master[0]), int(master[1]))
        self.outs = [(str(h), int(p)) for h, p in outs]
        self.mavfwd = bool(mavfwd)
        self.heartbeat = heartbeat
        self.heartbeat_aralik_s = float(heartbeat_aralik_s)
        self.sayac = {"master_paket": 0, "cikisa_yazilan": 0, "mastera_yazilan": 0,
                      "mavfwd_atilan": 0, "yeniden_baslatma": 0}
        self._kilit = threading.RLock()
        self._dur = threading.Event()
        self._iplik = None
        self._ac()

    def _ac(self):
        self.master_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.master_sock.bind((YEREL, 0))
        self.out_socks = []
        for _ in self.outs:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((YEREL, 0))
            self.out_socks.append(s)
        self._master_ayr = _ayristirici(self._m)
        self._out_ayr = [_ayristirici(self._m) for _ in self.outs]
        self._kod = None
        if self.heartbeat is not None:
            self._kod = self._m.MAVLink(None, srcSystem=int(self.heartbeat[0]),
                                        srcComponent=int(self.heartbeat[1]))
        self._son_hb_t = None

    def _kapat_soketler(self):
        for s in [self.master_sock] + self.out_socks:
            try:
                s.close()
            except OSError:
                pass

    @property
    def master_adresi(self):
        return self.master_sock.getsockname()

    def cikis_adresi(self, i=0):
        return self.out_socks[i].getsockname()

    def heartbeat_ayarla(self, kimlik):
        with self._kilit:
            self.heartbeat = kimlik
            self._kod = (None if kimlik is None else self._m.MAVLink(
                None, srcSystem=int(kimlik[0]), srcComponent=int(kimlik[1])))
            self._son_hb_t = None

    def yeniden_baslat(self):
        """Surec yeniden baslamasi: yeni efemer portlar, bos ayristiricilar."""
        with self._kilit:
            self._kapat_soketler()
            self._ac()
            self.sayac["yeniden_baslatma"] += 1

    def tur(self, bekleme_s=DONGU_BEKLEME_TAVANI_S):
        with self._kilit:
            simdi = time.monotonic()
            if self._kod is not None and (
                    self._son_hb_t is None
                    or simdi - self._son_hb_t >= self.heartbeat_aralik_s):
                self._son_hb_t = simdi
                hb = self._kod.heartbeat_encode(
                    self._m.MAV_TYPE_GCS, self._m.MAV_AUTOPILOT_INVALID, 0, 0,
                    self._m.MAV_STATE_ACTIVE).pack(self._kod)
                try:
                    self.master_sock.sendto(hb, self.master)
                except OSError:
                    pass
            socks = [self.master_sock] + list(self.out_socks)
        try:
            hazir, _, _ = select.select(socks, [], [], bekleme_s)
        except (OSError, ValueError):
            return
        with self._kilit:
            for s in hazir:
                if s not in [self.master_sock] + self.out_socks:
                    continue                      # yeniden baslatmada kapandi
                try:
                    veri, _adr = s.recvfrom(UDP_DATAGRAM_TAVANI_B)
                except OSError:
                    continue
                if s is self.master_sock:
                    for msg in self._master_ayr.parse_buffer(veri) or []:
                        if msg.get_type() == _BAD_DATA:
                            continue
                        self.sayac["master_paket"] += 1
                        ham = bytes(msg.get_msgbuf())
                        for os_, adr in zip(self.out_socks, self.outs):
                            try:
                                os_.sendto(ham, adr)      # mesaj basina datagram
                                self.sayac["cikisa_yazilan"] += 1
                            except OSError:
                                pass
                else:
                    i = self.out_socks.index(s)
                    for msg in self._out_ayr[i].parse_buffer(veri) or []:
                        if msg.get_type() == _BAD_DATA:
                            continue
                        if not self.mavfwd:
                            self.sayac["mavfwd_atilan"] += 1
                            continue
                        try:
                            self.master_sock.sendto(bytes(msg.get_msgbuf()),
                                                    self.master)
                            self.sayac["mastera_yazilan"] += 1
                        except OSError:
                            pass

    def baslat(self):
        self._dur.clear()
        self._iplik = threading.Thread(target=self._dongu, daemon=True,
                                       name="mavproxy-taklit")
        self._iplik.start()
        return self

    def _dongu(self):
        while not self._dur.is_set():
            self.tur()

    def durdur(self):
        self._dur.set()
        if self._iplik is not None:
            self._iplik.join(timeout=2.0)
        self._kapat_soketler()
