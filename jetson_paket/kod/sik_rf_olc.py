"""SiK 433 MHz RF OLCUM ARACI — ACK gidis-donusu (RTT), kayip ve VERI HIZI.

NEDEN: D-388 seri hatti GERCEK bayt akisinda (TCP koprusu, `socket://`)
dogruladi; gercek 433 MHz RF olcumu Faz B'ye kaldi. Bu arac o olcumu yapar:
iki SiK telsiz, bir ucta `--rol yanki`, diger ucta `--rol olc`. Olcum
`comms/protocol.py`'nin GERCEK cerceveleriyle (CMD -> ACK) yapilir; yani
sahadaki IKA_GO / PARASUT tekrar dongusunun bire bir ayni yolu olculur.

NEDEN esik tekrar araliklaridir: `codes/karar_sozlesmesi.py` icindeki
`IKA_GO_TEKRAR_ARALIGI_S` (0,25 s) ve `PARASUT_TEKRAR_ARALIGI_S` (0,20 s)
"ACK gelmezse tekrar gonder" araliklaridir. RTT p95 bu araliklarin ALTINDA
degilse tekrar tasarimi anlamsizlasir: ACK yolda iken komut yeniden gider,
hat bogulur, ACK'ler gecikir (kendi kendini besleyen tikanma). Esikler
sozlesmeden IMPORT edilir (anayasa m.16), burada yeniden yazilmaz.

NEDEN `SerialLink.recv` ile ZAMANLAMA yapilmaz: pyserial `read(256)`, 256 bayt
gelene YA DA zaman asimi dolana kadar bloklar. ~70 baytlik bir ACK icin bu,
"ACK geldi" aninin okuma zaman asimina (0,3 s) YUVARLANMASI demektir — RTT
hep ~zaman asimi cikar, olcum yalan olur. Ayni sebeple YANKI tarafi da hizli
okumak zorundadir; yoksa cevabi 0,3 s geciktirir. Bu yuzden her iki rol
`_hizli_oku` kullanir: ilk bayta kadar bekle (`read(1)`), sonra birikeni
bosalt. Acma/gonderme/kapama yine `SerialLink` uzerindendir (uretim yolu).

VERI HIZI (T216 · yonerge Y-3.3.4-M03 / Y-4-M09 "kullanilan veri hizi"):
olc rolu gonderdigi/aldigi BAYT ve PAKET'i (cozulen cerceve) sayar; sure =
ilk prob gonderiminden son probun ACK'ine ya da zaman asimina kadar gecen
monotonik zaman. Rapordaki `veri_hizi` alani bayt/s, bit/s ve paket/s verir.
Bu, prob kadansindaki (`--aralik`) FIILI akistir — hattin KAPASITESI degildir:
`--aralik 0.25` uretim IKA_GO kadansidir, sayilar o kadansin yukudur. Yanki
ucu da ayni sayaclari tutar (`--json` ciktisinda). Sayaclar RTT/kayip
hesabina DOKUNMAZ (kilit: tests/test_faz_b_sik_rf_olc.py).

TASIYICI: varsayilan `seri` (SiK / `serial_for_url`). `--tasiyici udp` ayni
prob/ACK yordamini UDP uzerinde kosar (`comms/link.py UDPLink`): 127.0.0.1
loopback tabani ve WiFi/LAN hatti ayni betikle olculur; RF sayilari bu
referansla okunur. UDP'de okuma artefakti yoktur (datagram butun gelir).

VERDIKT (fail-closed):
  UYUMLU     (cikis 0) — RTT p95 < IKA_GO_TEKRAR_ARALIGI_S ve < PARASUT_TEKRAR_ARALIGI_S
  UYARI      (cikis 1) — p95 esiklerden en az birini asiyor
  OLCULEMEDI (cikis 2) — hic ACK yok (RTT ornegi yok) ya da port acilamadi;
                         "UYUMLU" DENEMEZ, sessiz basari yalani yok.
Kayip icin esik YOK (ilk olcum): yalniz raporlanir. RTT yuzdelikleri YALNIZ
ACK alinan problar uzerindendir; yuksek kayipta p95 iyimserdir — kayip
alanina birlikte bakilir. Veri hizi icin de esik YOK: raporlanir.

Kullanim (iki telsiz, iki makine ya da iki port):
    venv\\Scripts\\python.exe -B scripts/sik_rf_olc.py --rol yanki --port COM7
    venv\\Scripts\\python.exe -B scripts/sik_rf_olc.py --rol olc --port COM8 \\
        --n 50 --aralik 0.25 --json --cikti results/faz_b/sik_rtt.json
Port `serial_for_url` uyumludur: `COM7`, `/dev/ttyUSB0`, `socket://h:p`,
`loop://` (loop:// ile olc rolu kendi CMD'sini gorur, ACK gelmez: kayip %100).
UDP (loopback / LAN):
    ... --rol yanki --tasiyici udp --bind 127.0.0.1:0        (portu stderr'e yazar)
    ... --rol olc --tasiyici udp --peer 127.0.0.1:<port> --n 200 --json --cikti ...

TUNEL (bu bolum dokstringin SONUNA eklendi: satir atiflari — ATOLYE_TEST_GUNU_20260912.md
`sik_rf_olc.py:39/43` — kaymasin):
`--tasiyici tunel` (CONTRACTS §7.6 · results/tunel_20260916/ON_KAYIT.md K8):
ayni yordam MAVLink TUNNEL ucu (`comms/mavlink_tunel.TunelLink`) uzerinden
kosar — yer ucu MP aynasina (`--tunel-bind 127.0.0.1:14570 --tunel-kimlik yer`),
hava ucu MAVProxy cikisina (`--tunel-bind 127.0.0.1:14553 --tunel-kimlik hava`)
baglanir. Esikler ve verdikt mantigi AYNIDIR; kunyeye tunel sayaclari eklenir.

PROB DOLGUSU (`--prob-dolgu B`, varsayilan 0): prob CMD'sine sabit uzunlukta
`dolgu` alani eklenir, prob cercevesi TAM B bayt olur (ornek 165 B = 2 tunel
parcasi, 473 B = 4 parca) — cok parcali RTT KAYDI icindir. Yalniz dolgu=0
kosusu KAPIDIR; dolgu>0 kosusunun JSON'unda `kapi_disi: true` yazar ve verdikti
kapi SAYILMAZ (elestiri 1 bulgu 2).

ACK DOLGUSU (`--ack-dolgu B`, yalniz yanki; duzeltme turu 1): prob dolgusu
yalniz YER->HAVA yonunu buyutur; ACK tek parcali kalirdi. Uretimde 473 B
OPEN_ROUTE HAVA->YER gider (TELEM1 TX, K4'te dusen yol). Yanki ACK'i TAM B
bayta dolgular; olc ucu dolgulu ACK gorurse raporda `ack_dolgulu` sayilir ve
`kapi_disi: true` yazar. Yalniz KAYITTIR.

TUNEL AYRISTIRMA + DATAGRAM SINIRI (duzeltme turu 1; K8-0 i): `--tunel-ayristirma
datagram|akis` TunelLink kipini ezer (kayit icin). Tunel kipinde her alinan
datagram AYRICA yeni bir ayristiriciyla sinanir: ilk bayt MAVLink2 magic VE
datagram tek basina, artiksiz, en az bir gecerli pakete cozuluyorsa `hizali`,
degilse `hizasiz` sayilir (`datagram_siniri`). NEDEN: 'akis' kipinde
`mavlink_paket / alinan_datagram ~ 1` olcutu paket ORTASINDAN baslayan
datagramlarda da geciyordu (curutucu olcumu: 201 datagram, 200 paket,
cozum_hatasi 0) — 'datagram' kipine gecis onerisi paketlerin %100'unu
kaybettirirdi.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S)
from link import SerialLink, UDPLink  # noqa: E402
from mavlink_tunel import (AYRISTIRMA_AKIS, AYRISTIRMA_DATAGRAM,  # noqa: E402
                           KIMLIK_HAVA, KIMLIK_YER,
                           TASIYICI_TUNEL as _MT_TASIYICI_TUNEL,
                           TUNEL_HAVA_UC, TUNEL_PARCA_YUK_B, TUNEL_YER_UC,
                           TunelLink, uc_coz)
from protocol import (FrameReader, ack, command, encode,  # noqa: E402
                      MESAJ_ACK, MESAJ_CMD)

# SiK varsayilan air-rate'inde yaygin seri hiz (`comms/link.py` varsayilaniyla
# ayni; sozlesmede baud sabiti YOK — D-388 / link.py dokstringi).
VARSAYILAN_BAUD = 57600
VARSAYILAN_N = 50
#: Prob kadansi varsayilani = IKA_GO tekrar kadansi (olculen sey o dongudur).
VARSAYILAN_ARALIK_S = IKA_GO_TEKRAR_ARALIGI_S
#: Yanki ucunun okuma zaman asimi: yalniz KeyboardInterrupt tepkisini belirler
#: (RTT'ye etkisi yok — ilk bayt gelince okuma hemen doner).
YANKI_OKUMA_ZAMAN_ASIMI_S = 0.3
#: Olc ucunun okuma zaman asimi tavani: prob son tarihine bu kadar kaba
#: yaklasilir (kayip probda en fazla bu kadar tasma). RTT'ye etkisi YOK;
#: test bunu kilitler (p50 bu degerin yarisinin altinda kalmali).
OLC_OKUMA_ZAMAN_ASIMI_S = 0.05
#: Tek `_hizli_oku` cagrisinda bosaltilacak en fazla bayt (sel korumasi).
OKUMA_TAVANI = 4096

PROB_KOMUTU = "RF_PROBE"       # protocol.command(cmd=...) — alicilar bilmedigini yok sayar
PROB_HEDEF = "ika"             # command(hedef=...) — yanki ucu IKA rolunu oynar
YANKI_DUGUMU = "ika"           # ack(node=...)
ACK_REF_TIPI = MESAJ_CMD       # ack(ref_tip=...) — CONTRACTS §6.6

TASIYICI_SERI, TASIYICI_UDP = "seri", "udp"
TASIYICI_TUNEL = _MT_TASIYICI_TUNEL        # "tunel" (CONTRACTS §7.6)
#: Rol basina varsayilan tunel kimligi: yanki hava ucunda, olc yer ucunda (K8a).
VARSAYILAN_TUNEL_KIMLIGI = {"yanki": KIMLIK_HAVA, "olc": KIMLIK_YER}
PROB_DOLGU_ALANI = "dolgu"
KAPI_DISI_NOTU = ("--prob-dolgu > 0: cok parcali KAYIT kosusu; verdikt kapi "
                  "SAYILMAZ (yalniz dolgu=0 kosusu kapidir)")
ACK_DOLGU_NOTU = ("dolgulu ACK (yanki --ack-dolgu > 0): hava->yer cok parcali KAYIT "
                  "kosusu; verdikt kapi SAYILMAZ")
#: MAVLink2 baslangic bayti (datagram siniri denetimi).
MAVLINK2_MAGIC = 0xFD
VARSAYILAN_UDP_BIND = "127.0.0.1:0"

CIKIS_UYUMLU, CIKIS_UYARI, CIKIS_OLCULEMEDI = 0, 1, 2
VERDIKT_UYUMLU = "tekrar tasarimiyla UYUMLU"
VERDIKT_UYARI = "UYARI: RTT p95 tekrar araligini asiyor"
VERDIKT_OLCULEMEDI = "OLCULEMEDI: hic ACK alinmadi (RTT ornegi yok)"

VERI_HIZI_NOTU = ("Prob kadansindaki (aralik_s) FIILI akis; hat kapasitesi degil. "
                  "sure_s = ilk prob gonderimi -> son prob ACK/zaman asimi. "
                  "alinan_paket = cozulen cerceve sayisi (ACK + diger trafik).")


# ── Uclar ────────────────────────────────────────────────────────────────────

def uc_ac(port, baud=VARSAYILAN_BAUD, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S):
    """Uretim tasiyicisi `SerialLink` ile ucu ac (serial_for_url uyumlu)."""
    return SerialLink(port, baud, timeout=timeout)


class UdpUc:
    """UDP tasiyici ucu (loopback / LAN) — `SerialLink` ile ayni yuzey.

    `send(bytes)` / `close()` ayni; okuma `oku()` ile datagram butunudur.
    Yanki rolunde akran verilmez: ilk probun kaynak adresine cevap yazilir
    (`UDPLink.recv` adresi verir). Olc rolunde `peer` zorunludur.
    """

    def __init__(self, bind, peer=None, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S):
        self.link = UDPLink(bind=bind, peer=peer, timeout=timeout)
        self._son_adres = None

    @property
    def port(self):
        return self.link.port

    def oku(self):
        veri, adres = self.link.recv(OKUMA_TAVANI)
        if veri and adres is not None:
            self._son_adres = adres
        return veri or b""

    def send(self, data, peer=None):
        hedef = peer or self.link.peer or self._son_adres
        if hedef is None:
            raise OSError("UDP: akran bilinmiyor (yanki ilk probu gormeden yazamaz)")
        self.link.send(data, hedef)

    def close(self):
        self.link.close()


class TunelUc:
    """MAVLink TUNNEL tasiyici ucu — `UdpUc` ile ayni yuzey (oku/send/close).

    `TunelLink.recv` tam cerceve teslim eder; `oku()` onu bayt olarak verir.
    Akran arac HEARTBEAT'inden ogrenilir (TunelLink kurali); `sayac` kunyeye
    yazilir.
    """

    def __init__(self, bind, kimlik, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S,
                 ayristirma=None):
        self.link = TunelLink(bind, kimlik, timeout=timeout, ayristirma=ayristirma)
        self.datagram_siniri = {"hizali": 0, "hizasiz": 0}
        asil = self.link._datagram_isle

        def sinir_kaydi(veri, adr):
            # KAYIT: link davranisi DEGISMEZ; datagram once bagimsiz sinanir.
            anahtar = ("hizali" if datagram_siniri_hizali_mi(veri, self.link._m)
                       else "hizasiz")
            self.datagram_siniri[anahtar] += 1
            return asil(veri, adr)
        self.link._datagram_isle = sinir_kaydi

    @property
    def port(self):
        return self.link.port

    @property
    def sayac(self):
        return self.link.sayac

    def oku(self):
        return self.link.recv()[0] or b""

    def send(self, data, peer=None):
        self.link.send(data)

    def close(self):
        self.link.close()


def datagram_siniri_hizali_mi(veri, mav_modul):
    """Datagram paket sinirinda mi: ilk bayt MAVLink2 magic VE yeni bir
    ayristiriciyla tek basina, artiksiz, >= 1 gecerli pakete cozulur."""
    veri = bytes(veri)
    if not veri or veri[0] != MAVLINK2_MAGIC:
        return False
    ayr = mav_modul.MAVLink(None, srcSystem=0, srcComponent=0)
    ayr.robust_parsing = True
    try:
        mesajlar = ayr.parse_buffer(veri) or []
    except Exception:                       # ayristirici istisnasi = hizasiz
        return False
    if not mesajlar or any(m.get_type() == "BAD_DATA" for m in mesajlar):
        return False
    return sum(len(m.get_msgbuf()) for m in mesajlar) == len(veri)


def _dolgula(mesaj, dolgu_b, secenek):
    dolgu_b = int(dolgu_b)
    if dolgu_b <= 0:
        return encode(mesaj)
    mesaj[PROB_DOLGU_ALANI] = ""
    eksik = dolgu_b - len(encode(mesaj))
    if eksik < 0:
        raise ValueError(f"{secenek} {dolgu_b} B cok kucuk (en az "
                         f"{dolgu_b - eksik} B)")
    mesaj[PROB_DOLGU_ALANI] = "x" * eksik
    return encode(mesaj)


def ack_cercevesi(seq, dolgu_b=0):
    """Yanki ACK cercevesi; `dolgu_b` > 0 ise TAM `dolgu_b` bayt (KAYIT)."""
    return _dolgula(ack(seq, YANKI_DUGUMU, ref_tip=ACK_REF_TIPI), dolgu_b, "--ack-dolgu")


def prob_cercevesi(seq, dolgu_b=0):
    """Prob CMD cercevesi. `dolgu_b` > 0 ise cerceve TAM `dolgu_b` bayt olur.

    Ulasilamayacak kadar kucuk dolgu (dolgu alanli en kisa cerceveden kisa)
    ValueError verir.
    """
    return _dolgula(command(PROB_KOMUTU, PROB_HEDEF, seq=seq), dolgu_b, "--prob-dolgu")


def tunel_parca_sayisi(cerceve_b):
    """Bir cercevenin tunelde kac TUNNEL parcasina bolundugu (kayit icin)."""
    return -(-int(cerceve_b) // TUNEL_PARCA_YUK_B)


def _adres(metin):
    """'host:port' -> (host, int(port)); bozuksa ValueError."""
    host, _, port = str(metin).rpartition(":")
    if not host or not port.isdigit():
        raise ValueError(f"adres 'host:port' olmali: {metin!r}")
    return host, int(port)


def udp_uc_ac(bind=VARSAYILAN_UDP_BIND, peer=None,
              timeout=YANKI_OKUMA_ZAMAN_ASIMI_S):
    """UDP ucu ac; `bind`/`peer` 'host:port' metni ya da (host, port)."""
    b = _adres(bind) if isinstance(bind, str) else tuple(bind)
    p = None if peer is None else (_adres(peer) if isinstance(peer, str)
                                   else tuple(peer))
    return UdpUc(b, p, timeout=timeout)


def _hizli_oku(link):
    """Ilk bayta kadar bekle (en fazla link zaman asimi), sonra birikeni bosalt.

    Donus: gelen baytlar (bos ise zaman asimi). Bir cerceve parcali gelebilir;
    cagiran `FrameReader` ile birlestirir — zamanlama cerceve TAMAMLANINCA alinir.
    UDP ucunda (`UdpUc`) datagram butun doner; artefakt yok.
    """
    oku = getattr(link, "oku", None)
    if oku is not None:
        return oku()
    ser = link.ser
    ilk = ser.read(1)
    if not ilk:
        return b""
    parcalar = [ilk]
    toplam = 1
    while toplam < OKUMA_TAVANI:
        bekleyen = ser.in_waiting          # socket:// icin 0/1 doner; dongu yeter
        if bekleyen <= 0:
            break
        parca = ser.read(bekleyen)
        if not parca:
            break
        parcalar.append(parca)
        toplam += len(parca)
    return b"".join(parcalar)


def _seri_hatasi():
    """pyserial'in hata sinifi; pyserial yoksa (UDP tasiyici) OSError yeter."""
    try:
        import serial  # tembel: link.py de oyle yapar
    except ImportError:
        return OSError
    return serial.SerialException


# ── Veri hizi ────────────────────────────────────────────────────────────────

def veri_hizi_hesapla(sure_s, gonderilen_bayt, alinan_bayt,
                      gonderilen_paket, alinan_paket):
    """Sayaclardan hiz sozlugu; sure <= 0 ise hizlar None (0'a bolme yok)."""
    sure_s = float(sure_s)
    gecerli = sure_s > 0.0

    def hiz(deger):
        return (deger / sure_s) if gecerli else None

    return {
        "sure_s": sure_s,
        "gonderilen_bayt": int(gonderilen_bayt),
        "alinan_bayt": int(alinan_bayt),
        "gonderilen_paket": int(gonderilen_paket),
        "alinan_paket": int(alinan_paket),
        "gonderilen_bayt_s": hiz(gonderilen_bayt),
        "alinan_bayt_s": hiz(alinan_bayt),
        "gonderilen_bit_s": hiz(8 * gonderilen_bayt),
        "alinan_bit_s": hiz(8 * alinan_bayt),
        "gonderilen_paket_s": hiz(gonderilen_paket),
        "alinan_paket_s": hiz(alinan_paket),
        "not": VERI_HIZI_NOTU,
    }


# ── Rol: yanki ───────────────────────────────────────────────────────────────

def _prob_mu(mesaj):
    return (isinstance(mesaj, dict) and mesaj.get("type") == MESAJ_CMD
            and mesaj.get("cmd") == PROB_KOMUTU
            and isinstance(mesaj.get("seq"), int)
            and not isinstance(mesaj.get("seq"), bool))


def yanki_kos(link, dur=None, ilerleme=None, sayac=None, saat=time.monotonic,
              ack_dolgu_b=0):
    """Gelen her CMD(RF_PROBE) icin ack(seq, "ika", "CMD") yaz.

    `dur` (threading.Event) verilirse o kurulunca doner; verilmezse
    KeyboardInterrupt ya da hat kopana kadar surer. Cevaplanan sayiyi dondurur.
    `sayac` (dict) verilirse bayt/paket sayaclari ve sure ona yazilir
    (ilk gelen bayttan son ACK yazimina kadar); donus tipi DEGISMEZ.
    KeyboardInterrupt (Ctrl+C, sahadaki olagan cikis) dongunun olagan sonudur:
    sayac yine yazilir ve cevaplanan sayi dondurulur (duzeltme turu 1: once
    Ctrl+C'de `veri_hizi` bos, `cevaplanan` 0 kaliyordu).
    `ack_dolgu_b` > 0: ACK TAM o boya dolgulanir (hava->yer cok parcali KAYIT).
    """
    okuyucu = FrameReader()
    cevaplanan = 0
    hata = _seri_hatasi()
    alinan_bayt = gonderilen_bayt = alinan_paket = 0
    t_ilk = t_son = None
    try:
        while dur is None or not dur.is_set():
            try:
                veri = _hizli_oku(link)
            except (hata, OSError) as exc:
                if ilerleme:
                    ilerleme(f"yanki: hat koptu ({exc})")
                break
            if not veri:
                continue
            if t_ilk is None:
                t_ilk = saat()
            alinan_bayt += len(veri)
            for mesaj in okuyucu.feed(veri):
                alinan_paket += 1
                if not _prob_mu(mesaj):
                    continue                   # baska trafik: yok say
                cerceve = ack_cercevesi(mesaj["seq"], ack_dolgu_b)
                link.send(cerceve)
                gonderilen_bayt += len(cerceve)
                cevaplanan += 1
                t_son = saat()
                if ilerleme:
                    ilerleme(f"yanki: seq={mesaj['seq']} -> ACK ({cevaplanan})")
    except KeyboardInterrupt:
        if ilerleme:
            ilerleme("yanki: Ctrl+C — sayaclar yaziliyor")
    if sayac is not None:
        sure = (t_son - t_ilk) if (t_ilk is not None and t_son is not None) else 0.0
        sayac.update(veri_hizi_hesapla(sure, gonderilen_bayt, alinan_bayt,
                                       cevaplanan, alinan_paket))
    return cevaplanan


# ── Rol: olc ─────────────────────────────────────────────────────────────────

def _ack_eslesir(mesaj, seq):
    if not isinstance(mesaj, dict) or mesaj.get("type") != MESAJ_ACK:
        return False
    if mesaj.get("ref") != seq:
        return False
    # ref_tip yoksa yalniz ref ile eslenir (geriye uyumlu, CONTRACTS §6.6)
    return mesaj.get("ref_tip", ACK_REF_TIPI) == ACK_REF_TIPI


def yuzdelik(degerler, p):
    """En yakin sira (nearest-rank) yuzdeligi; bos listede None."""
    if not degerler:
        return None
    sirali = sorted(degerler)
    k = max(1, min(len(sirali), math.ceil(p / 100.0 * len(sirali))))
    return sirali[k - 1]


def olc_kos(link, n, aralik, zaman_asimi=None, ilerleme=None,
            saat=time.monotonic, prob_dolgu_b=0):
    """n prob gonder, her biri icin ACK RTT olc; rapor sozlugu dondur.

    Prob i icin seq=i (1..n) — ACK `ref` ile eslenir. Zaman asimi icinde
    gelmeyen ACK KAYIP sayilir; sonradan gelen (bekleyen seq'e ait olmayan)
    ACK `gec_ack` sayacina yazilir, RTT'ye GIRMEZ. Bayt/paket sayaclari
    (`veri_hizi`) RTT ve kayip hesabindan BAGIMSIZDIR: yalniz sayar.
    """
    n = int(n)
    aralik = float(aralik)
    if n < 1 or not (aralik > 0):
        raise ValueError("n >= 1 ve aralik > 0 olmali")
    zaman_asimi = 2.0 * aralik if zaman_asimi is None else float(zaman_asimi)
    if not (zaman_asimi > 0):
        raise ValueError("zaman asimi > 0 olmali")

    okuyucu = FrameReader()
    hata = _seri_hatasi()
    rtt_ms = []
    gonderilen = 0
    gec_ack = 0
    hat_koptu = None
    gonderilen_bayt = alinan_bayt = alinan_paket = 0
    ack_dolgulu = 0
    t_ilk = None

    for seq in range(1, n + 1):
        cerceve = prob_cercevesi(seq, prob_dolgu_b)
        t0 = saat()
        if t_ilk is None:
            t_ilk = t0
        try:
            link.send(cerceve)
        except (hata, OSError) as exc:
            hat_koptu = f"gonderim {seq}: {exc}"
            break
        gonderilen += 1
        gonderilen_bayt += len(cerceve)
        son = t0 + zaman_asimi
        rtt = None
        while rtt is None and saat() < son:
            try:
                veri = _hizli_oku(link)
            except (hata, OSError) as exc:
                hat_koptu = f"okuma {seq}: {exc}"
                break
            alinan_bayt += len(veri)
            for mesaj in okuyucu.feed(veri):
                alinan_paket += 1
                if _ack_eslesir(mesaj, seq):
                    rtt = (saat() - t0) * 1000.0
                    if PROB_DOLGU_ALANI in mesaj:
                        ack_dolgulu += 1
                    break
                if isinstance(mesaj, dict) and mesaj.get("type") == MESAJ_ACK:
                    gec_ack += 1
        if hat_koptu:
            break
        if rtt is None:
            if ilerleme:
                ilerleme(f"prob {seq}/{n}: KAYIP (> {zaman_asimi * 1000:.0f} ms)")
        else:
            rtt_ms.append(rtt)
            if ilerleme:
                ilerleme(f"prob {seq}/{n}: rtt={rtt:.1f} ms")
        kalan = (t0 + aralik) - saat()
        if kalan > 0 and seq < n:
            time.sleep(kalan)
    sure_s = (saat() - t_ilk) if t_ilk is not None else 0.0

    ack_alinan = len(rtt_ms)
    kayip = gonderilen - ack_alinan
    p50, p95 = yuzdelik(rtt_ms, 50), yuzdelik(rtt_ms, 95)
    esik_s = {"IKA_GO_TEKRAR_ARALIGI_S": IKA_GO_TEKRAR_ARALIGI_S,
              "PARASUT_TEKRAR_ARALIGI_S": PARASUT_TEKRAR_ARALIGI_S}

    if p95 is None:
        verdikt, cikis = VERDIKT_OLCULEMEDI, CIKIS_OLCULEMEDI
    elif p95 / 1000.0 < min(esik_s.values()):
        verdikt, cikis = VERDIKT_UYUMLU, CIKIS_UYUMLU
    else:
        verdikt, cikis = VERDIKT_UYARI, CIKIS_UYARI

    rapor = {
        "rol": "olc",
        "n": n, "aralik_s": aralik, "zaman_asimi_s": zaman_asimi,
        "gonderilen": gonderilen, "ack_alinan": ack_alinan,
        "kayip": kayip,
        "kayip_yuzde": (100.0 * kayip / gonderilen) if gonderilen else 100.0,
        "gec_ack": gec_ack,
        "rtt_ms": {
            "ornek": ack_alinan,
            "p50": p50, "p95": p95,
            "min": (min(rtt_ms) if rtt_ms else None),
            "maks": (max(rtt_ms) if rtt_ms else None),
        },
        "veri_hizi": veri_hizi_hesapla(sure_s, gonderilen_bayt, alinan_bayt,
                                       gonderilen, alinan_paket),
        "esik_s": esik_s,
        "verdikt": verdikt,
        "cikis_kodu": cikis,
        "not": ("RTT yuzdelikleri yalniz ACK alinan problar uzerindendir; "
                "kayip icin esik yok, birlikte okunur."),
        "prob_dolgu_b": int(prob_dolgu_b),
        "ack_dolgulu": ack_dolgulu,
        "kapi_disi": int(prob_dolgu_b) > 0 or ack_dolgulu > 0,
    }
    if rapor["kapi_disi"]:
        rapor["kapi_disi_notu"] = (KAPI_DISI_NOTU if int(prob_dolgu_b) > 0
                                   else ACK_DOLGU_NOTU)
    if hat_koptu:
        rapor["hat_koptu"] = hat_koptu
        # Hat koparsa olcum tamamlanmamistir: UYUMLU denemez.
        if rapor["cikis_kodu"] == CIKIS_UYUMLU:
            rapor["verdikt"] = "OLCULEMEDI: hat koptu — " + hat_koptu
            rapor["cikis_kodu"] = CIKIS_OLCULEMEDI
    return rapor


def _ms(deger):
    return "-" if deger is None else f"{deger:.1f} ms"


def _hiz(deger, birim):
    return "-" if deger is None else f"{deger:.1f} {birim}"


def veri_hizi_metni(v):
    """`veri_hizi` sozlugunu tek satirda ozetle (rapor metni ve yanki cikisi)."""
    return (f"gonderilen {v['gonderilen_bayt']} B / {v['gonderilen_paket']} pkt "
            f"-> {_hiz(v['gonderilen_bayt_s'], 'B/s')} "
            f"({_hiz(v['gonderilen_paket_s'], 'pkt/s')}) · "
            f"alinan {v['alinan_bayt']} B / {v['alinan_paket']} pkt "
            f"-> {_hiz(v['alinan_bayt_s'], 'B/s')} "
            f"({_hiz(v['alinan_paket_s'], 'pkt/s')}) · sure {v['sure_s']:.2f} s")


def rapor_metni(rapor):
    r = rapor["rtt_ms"]
    satirlar = [
        f"gonderilen : {rapor['gonderilen']}",
        f"ACK alinan : {rapor['ack_alinan']}",
        f"kayip      : {rapor['kayip']} (%{rapor['kayip_yuzde']:.1f})"
        + (f"  gec ACK: {rapor['gec_ack']}" if rapor["gec_ack"] else ""),
        f"RTT p50    : {_ms(r['p50'])}",
        f"RTT p95    : {_ms(r['p95'])}",
        f"RTT maks   : {_ms(r['maks'])}",
        f"veri hizi  : {veri_hizi_metni(rapor['veri_hizi'])}",
        "esik       : p95 < IKA_GO_TEKRAR_ARALIGI_S="
        f"{rapor['esik_s']['IKA_GO_TEKRAR_ARALIGI_S'] * 1000:.0f} ms ve "
        f"< PARASUT_TEKRAR_ARALIGI_S="
        f"{rapor['esik_s']['PARASUT_TEKRAR_ARALIGI_S'] * 1000:.0f} ms",
        f"VERDIKT    : {rapor['verdikt']}",
    ]
    if rapor.get("hat_koptu"):
        satirlar.append(f"HAT KOPTU  : {rapor['hat_koptu']}")
    if rapor.get("kapi_disi"):
        satirlar.append(f"KAPI DISI  : {rapor.get('kapi_disi_notu', KAPI_DISI_NOTU)}")
    return "\n".join(satirlar)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _ilerleme_yaz(satir):
    print(satir, file=sys.stderr, flush=True)


def _uc_ac_cli(a, ap, timeout):
    """Argumanlara gore ucu ac; (uc, kunye) dondurur. Acilamazsa None, kunye."""
    if a.tasiyici == TASIYICI_TUNEL:
        kunye = {"tasiyici": TASIYICI_TUNEL, "tunel_bind": a.tunel_bind,
                 "tunel_kimlik": a.tunel_kimlik}
        try:
            uc = TunelUc(uc_coz(a.tunel_bind), a.tunel_kimlik, timeout=timeout,
                         ayristirma=a.tunel_ayristirma)
        except (ImportError, OSError, ValueError) as exc:
            return None, kunye, f"tunel ucu acilamadi ({a.tunel_bind}): {exc}"
        kunye["tunel_ayristirma"] = uc.link.ayristirma
        return uc, kunye, None
    if a.tasiyici == TASIYICI_UDP:
        kunye = {"tasiyici": TASIYICI_UDP, "bind": a.bind, "peer": a.peer}
        try:
            uc = udp_uc_ac(a.bind, a.peer, timeout=timeout)
        except (OSError, ValueError) as exc:
            return None, kunye, f"UDP ucu acilamadi ({a.bind} -> {a.peer}): {exc}"
        kunye["bind"] = f"{_adres(a.bind)[0]}:{uc.port}"   # 0 -> gercek port
        return uc, kunye, None
    kunye = {"tasiyici": TASIYICI_SERI, "port": a.port, "baud": a.baud}
    try:
        hata = _seri_hatasi()
        uc = uc_ac(a.port, a.baud, timeout=timeout)
    except (hata, OSError, ValueError) as exc:
        return None, kunye, f"port acilamadi ({a.port}): {exc}"
    return uc, kunye, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rol", choices=("yanki", "olc"), required=True)
    ap.add_argument("--tasiyici", choices=(TASIYICI_SERI, TASIYICI_UDP, TASIYICI_TUNEL),
                    default=TASIYICI_SERI,
                    help="seri (SiK, varsayilan), udp (loopback/LAN) ya da tunel "
                         "(MAVLink TUNNEL, CONTRACTS §7.6)")
    ap.add_argument("--tunel-bind", default=None, metavar="HOST:PORT",
                    help=f"tunel: dinlenen uc (yer: MP aynasi {TUNEL_YER_UC}; "
                         f"hava: MAVProxy cikisi {TUNEL_HAVA_UC})")
    ap.add_argument("--tunel-kimlik", choices=(KIMLIK_HAVA, KIMLIK_YER), default=None,
                    help="tunel ucunun kimligi (varsayilan: yanki=hava, olc=yer)")
    ap.add_argument("--prob-dolgu", type=int, default=0, metavar="B",
                    help="prob cercevesini TAM B bayt yap (0 = dolgu yok; >0 kosu "
                         "KAPI DISI kayittir)")
    ap.add_argument("--ack-dolgu", type=int, default=0, metavar="B",
                    help="yanki: ACK cercevesini TAM B bayt yap (hava->yer cok "
                         "parcali KAYIT; olc raporu kapi_disi yazar)")
    ap.add_argument("--tunel-ayristirma", choices=(AYRISTIRMA_DATAGRAM, AYRISTIRMA_AKIS),
                    default=None,
                    help="tunel: ayristirma kipini ez (KAYIT; varsayilan kimlige gore)")
    ap.add_argument("--port", default=None,
                    help="seri: serial_for_url uyumlu: COM7, /dev/ttyUSB0, socket://, loop://")
    ap.add_argument("--baud", type=int, default=VARSAYILAN_BAUD)
    ap.add_argument("--bind", default=VARSAYILAN_UDP_BIND,
                    help="udp: dinlenen host:port (0 = ephemeral; yanki portu stderr'e yazar)")
    ap.add_argument("--peer", default=None,
                    help="udp: karsi uc host:port (olc icin zorunlu)")
    ap.add_argument("--n", type=int, default=VARSAYILAN_N, help="prob sayisi (olc)")
    ap.add_argument("--aralik", type=float, default=VARSAYILAN_ARALIK_S,
                    help="prob araligi s (olc); varsayilan IKA_GO tekrar araligi")
    ap.add_argument("--zaman-asimi", type=float, default=None,
                    help="ACK bekleme s (olc); varsayilan 2*aralik")
    ap.add_argument("--json", action="store_true", help="raporu JSON bas")
    ap.add_argument("--cikti", default=None, help="raporu bu JSON dosyasina da yaz")
    ap.add_argument("--sessiz", action="store_true", help="prob ilerlemesini basma")
    a = ap.parse_args(argv)

    if a.prob_dolgu < 0:
        ap.error("--prob-dolgu negatif olamaz")
    if a.ack_dolgu < 0:
        ap.error("--ack-dolgu negatif olamaz")
    if a.ack_dolgu > 0 and a.rol != "yanki":
        ap.error("--ack-dolgu yalniz --rol yanki ile anlamlidir")
    if a.tunel_ayristirma is not None and a.tasiyici != TASIYICI_TUNEL:
        ap.error("--tunel-ayristirma yalniz --tasiyici tunel ile anlamlidir")
    try:
        prob_cercevesi(1, a.prob_dolgu)
        ack_cercevesi(1, a.ack_dolgu)
    except ValueError as exc:
        ap.error(str(exc))
    if a.tasiyici == TASIYICI_TUNEL:
        if a.tunel_kimlik is None:
            a.tunel_kimlik = VARSAYILAN_TUNEL_KIMLIGI[a.rol]
        if not a.tunel_bind:
            ap.error("--tasiyici tunel icin --tunel-bind HOST:PORT gerekli")
        try:
            uc_coz(a.tunel_bind)
        except ValueError as exc:
            ap.error(str(exc))
    elif a.tasiyici == TASIYICI_SERI:
        if not a.port:
            ap.error("--tasiyici seri icin --port gerekli")
        try:
            import serial  # noqa: F401
        except ImportError:
            print("OLCULEMEDI: pyserial kurulu degil (venv: pip install pyserial)",
                  file=sys.stderr)
            return CIKIS_OLCULEMEDI
    else:
        if a.rol == "olc" and not a.peer:
            ap.error("--tasiyici udp + --rol olc icin --peer host:port gerekli")
        try:
            _adres(a.bind)
            if a.peer:
                _adres(a.peer)
        except ValueError as exc:
            ap.error(str(exc))

    ilerleme = None if a.sessiz else _ilerleme_yaz

    if a.rol == "olc":
        if a.n < 1 or not (a.aralik > 0) or (a.zaman_asimi is not None
                                             and not (a.zaman_asimi > 0)):
            ap.error("--n >= 1, --aralik > 0, --zaman-asimi > 0 olmali")
        link, kunye, hata_metni = _uc_ac_cli(a, ap, timeout=min(
            a.zaman_asimi if a.zaman_asimi else 2.0 * a.aralik,
            OLC_OKUMA_ZAMAN_ASIMI_S))
        if link is None:
            print(f"OLCULEMEDI: {hata_metni}", file=sys.stderr)
            return CIKIS_OLCULEMEDI
        try:
            rapor = olc_kos(link, a.n, a.aralik, a.zaman_asimi, ilerleme=ilerleme,
                            prob_dolgu_b=a.prob_dolgu)
        finally:
            link.close()
        rapor.update(kunye)
        if a.tasiyici == TASIYICI_TUNEL:
            rapor["tunel_sayac"] = link.sayac
            rapor["datagram_siniri"] = dict(link.datagram_siniri)
            rapor["prob_tunel_parca"] = tunel_parca_sayisi(
                len(prob_cercevesi(1, a.prob_dolgu)))
        if a.cikti:
            yol = Path(a.cikti)
            yol.parent.mkdir(parents=True, exist_ok=True)
            yol.write_text(json.dumps(rapor, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        if a.json:
            print(json.dumps(rapor, ensure_ascii=False))
        else:
            print(rapor_metni(rapor))
        return rapor["cikis_kodu"]

    # rol == yanki
    link, kunye, hata_metni = _uc_ac_cli(a, ap, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S)
    if link is None:
        print(f"yanki: {hata_metni}", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    if a.tasiyici == TASIYICI_UDP:
        uc_adi = kunye["bind"]
    elif a.tasiyici == TASIYICI_TUNEL:
        uc_adi = f"{a.tunel_bind} kimlik={a.tunel_kimlik}"
    else:
        uc_adi = f"{a.port} @ {a.baud}"
    # Bu satir --sessiz'de de yazilir: UDP'de ephemeral port yalniz buradan ogrenilir.
    _ilerleme_yaz(f"yanki: dinliyor {a.tasiyici}://{uc_adi} — CMD({PROB_KOMUTU}) "
                  "bekleniyor (Ctrl+C ile cik)")
    cevaplanan = 0
    sayac = {}
    try:
        cevaplanan = yanki_kos(link, ilerleme=ilerleme, sayac=sayac,
                               ack_dolgu_b=a.ack_dolgu)
    except KeyboardInterrupt:
        pass
    finally:
        link.close()
    sonuc = {"rol": "yanki", "cevaplanan": cevaplanan}
    sonuc.update(kunye)
    if a.ack_dolgu > 0:
        sonuc["ack_dolgu_b"] = a.ack_dolgu
        sonuc["ack_tunel_parca"] = tunel_parca_sayisi(len(ack_cercevesi(1, a.ack_dolgu)))
        sonuc["kapi_disi"] = True
        sonuc["kapi_disi_notu"] = ACK_DOLGU_NOTU
    if a.tasiyici == TASIYICI_TUNEL:
        sonuc["tunel_sayac"] = link.sayac
        sonuc["datagram_siniri"] = dict(link.datagram_siniri)
    if sayac:
        sonuc["veri_hizi"] = sayac
    if a.cikti:
        yol = Path(a.cikti)
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(json.dumps(sonuc, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    if a.json:
        print(json.dumps(sonuc, ensure_ascii=False))
    else:
        print(f"yanki: cevaplanan prob = {cevaplanan}"
              + (f" · veri hizi: {veri_hizi_metni(sayac)}" if sayac else ""))
    return CIKIS_UYUMLU


if __name__ == "__main__":
    sys.exit(main())
