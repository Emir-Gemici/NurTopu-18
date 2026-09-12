"""MESAJ PAKET BOYUTU ve GERCEK GOREV VERI HIZI OLCUM ARACI (T243).

NEDEN: yonerge Y-3.3.4-M03 "aktarilan veri paketlerinin NIHAI YAPISI, VERI HIZI
ve gecikme test sonuclari" ister. FDR'de gecikme olculmustu (SS3.3.4.3.3), ama
(a) mesaj tipi basina PAKET BOYUTU tablosu hic yoktu ve (b) olculen veri hizi
yalniz `IKA_GO`/`PARASUT` PROB kadansiydi (`scripts/sik_rf_olc.py`) — gercek
gorev trafigi (OPEN_ROUTE + tam telemetrili HEARTBEAT + ACK karisimi) hic
olculmedi. Kodda gecen "~200 B cerceve" yalniz bir tasarim notudur (D-462 C).

Bu arac iki kipte calisir:

  --kip boyut    `comms/protocol.py` URETICILERINI cagirir ve `encode()`
                 sonucunun `len()`'ini sayar. Bayt sayisi UYDURULMAZ, elle
                 hesaplanmaz, `json.dumps` kopyasiyla taklit edilmez.

  --kip karisim  GERCEK `IhaSender` + `KararYayinci` + `IkaReceiver` yollarini
                 UDP loopback (ephemeral port) uzerinde kosturur ve HATTA
                 GIDEN baytlari sayar. Sentetik olan yalniz rota geometrisidir;
                 boyutlar gercek `encode()` akisindan gelir.

ON KAYIT: results/fdr_sprint_20260910/T243/ON_KAYIT.md (olcumden ONCE yazildi,
ayri commit). Olculecek nicelikler (N1..N12), yontem, tohum ve RAPOR olcutu
oradadir. Bu bir KAPI DEGILDIR: hukum "olculdu / OLCULEMEDI"dir.

BELIRLENIM (boyut kipi): `t` ve `seq` alanlarinin GENISLIGI sabitlenir —
`protocol` modulunun `time` baglantisi gecici olarak sabit deger dondurur ve
her uretici `seq` acikca verilir. Alanlar KALDIRILMAZ; cerceve alan alan
uretimdekiyle aynidir. Gercek saat altindaki bayt oynamasi ayrica olculur.

SINIR: burada RF YOKTUR. Karisim olcumu 127.0.0.1 UDP loopback'tir; SiK 433 MHz
hattinin fiili veri hizi hala OLCULEMEDI (FDR SS3.3.4.3.4). Hat doluluk orani
57600 8N1 icin HESAPTIR (10 bit/bayt), radyonun hava hizi ve ECC durumu
OKUNMAMISTIR.

Kullanim:
    venv\\Scripts\\python.exe -X utf8 -B scripts/paket_boyutu_olc.py \\
        --kip hepsi --cikti-dizin results/fdr_sprint_20260910/T243
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import threading
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "comms", KOK / "scripts"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import protocol  # noqa: E402
from protocol import (HEARTBEAT_TELEMETRI_ALANLARI, MESAJ_ACK,  # noqa: E402
                      MESAJ_CMD, MESAJ_IHA_LANDED, MESAJ_NO_ROUTE,
                      MESAJ_OPEN_ROUTE, MESAJ_HEARTBEAT, ack, command, decode,
                      encode, heartbeat, iha_landed, open_route, rota_yok)
from iha_sender import (MAX_WAYPOINTS, IhaSender,  # noqa: E402
                        KararYayinci, piksel_rotayi_yerele_cevir)
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from karar_sozlesmesi import (IHA_HEARTBEAT_ARALIK_S,  # noqa: E402
                              SARTNAME_IHA_GOREV_SURESI_S,
                              SARTNAME_IKA_GOREV_SURESI_S, YAYIN_REF_XY)
# Hiz sozlugu TEK yerden gelir (kopya hesap yazilmaz): T216 araci.
from sik_rf_olc import veri_hizi_hesapla  # noqa: E402

# ── ON KAYIT sabitleri (SS2.1, SS5) ──────────────────────────────────────────
TOHUM = 20260912
SABIT_ZAMAN = 1789000000.123      # `t` alaninin genisligini kilitler
SABIT_SEQ = 1000                  # `seq` alaninin genisligini kilitler (4 hane)
SAAT_ORNEK = 200                  # gercek saat altinda bayt oynamasi ornegi
SEQ_BASAMAKLARI = (1, 10, 100, 1000, 10000)
WAYPOINT_EGRISI = tuple(range(1, 21))

#: Olcek (m/piksel) — sentetik piksel rotayi URETIM yoluyla metreye cevirir.
OLCEK_MPP = 0.05
#: Sentetik piksel rota: 21 nokta, adim 40 px ileri + 7 px saga.
PIKSEL_ADIM_ILERI = 40
PIKSEL_ADIM_SAGA = 7
PIKSEL_NOKTA = 21
PIKSEL_BASLANGIC = (640.0, 720.0)

#: Karar cerceve ornegi (uretim buyukluk sinifi).
ORNEK_ROAD = 2
ORNEK_CONF = 0.9134
#: float32 modeli ciktisinin float'a genisleyen ondaligi (conf alan genisligi).
ORNEK_CONF_GENIS = 0.9133999943733215
ORNEK_SEBEP = "KAPALI_DAR"
ORNEK_DETAY = "costmap guvenli rota uretmedi"
ORNEK_CMD = "IKA_GO"
ORNEK_HEDEF = "ika"
ORNEK_OTURUM = "0123456789abcdef0123456789abcdef"   # 32 karakter (16..64 bandi)

#: HEARTBEAT tam telemetri — uretim yolunun urettigi alan kumesi:
#: `codes/rpi_inference.py::_telemetri_saglayici` 12 alan + `x`,`y` (referans
#: beyan edilmisse) + `KararYayinci` `karar_yas`. Kume, sozlesmedeki
#: `HEARTBEAT_TELEMETRI_ALANLARI` ile BIREBIR esit olmak zorundadir (asagida
#: dogrulanir) — sozlesmeye alan eklenirse bu olcum SESSIZCE bayatlamaz.
TAM_TELEMETRI = {
    "x": 123.45, "y": -67.89, "alt": 31.4, "hiz": 16.5, "yon": 214.7,
    "bat": 12.34, "bat_yuzde": 87, "uydu": 14, "karar_yas": 0.74,
    "lat": 37.7648123, "lon": 38.2786456, "gps_fix": 3, "armed": True,
    "mod": "AUTO", "pixhawk_canli": True,
}

# ── Hat butcesi (SS2.3) — HESAP, olcum degil ─────────────────────────────────
BAUD = 57600
BIT_BASINA_BAYT = 10               # 8N1: 1 start + 8 veri + 1 stop
HAM_BAYT_S = BAUD / BIT_BASINA_BAYT           # 5760 B/s
MS_BASINA_BAYT = 1000.0 * BIT_BASINA_BAYT / BAUD   # 0,174 ms
#: ON KAYIT SS4 madde 2 — RAPOR olcutu (kapi degil).
RAPOR_DOLULUK_ESIGI_YUZDE = 80.0

#: Karar kadanslari — ikisi de olculmus artefakttan (ON_KAYIT SS2.2 madde 6).
JETSON_PT_P50_MS = 739.076         # results/jetson_20260906/.../ozet.json
KADANS_TAVAN_HZ = 2.0
PENCERE_S = 60.0
KOVA_S = 1.0

OLCUM_ETIKETI = "olcum"
TASIYICI_NOTU = ("UDP loopback 127.0.0.1 (ephemeral port). RF DEGILDIR: "
                 "SiK 433 MHz hattinin veri hizi hala OLCULEMEDI.")


# ── Belirlenimli saat ────────────────────────────────────────────────────────

class _SabitSaat:
    """`protocol` modulunun `time` baglantisinin yerine gecen kucuk vekil.

    Yalniz `protocol`in ad alanindaki ad degistirilir; `time` modulunun kendisi
    ve baska hicbir modul ETKILENMEZ.
    """

    def __init__(self, deger):
        self._deger = float(deger)

    def time(self):
        return self._deger


class sabit_saat:
    """`with sabit_saat():` — `protocol.time` gecici olarak sabitlenir."""

    def __init__(self, deger=SABIT_ZAMAN):
        self._deger = deger
        self._eski = None

    def __enter__(self):
        self._eski = protocol.time
        protocol.time = _SabitSaat(self._deger)
        return self

    def __exit__(self, *_):
        protocol.time = self._eski
        return False


def boy(msg):
    """Cerceve boyutu = `len(protocol.encode(msg))` — GERCEK bayt."""
    return len(encode(msg))


# ── Sentetik rota (geometri sentetik, boyut degil) ───────────────────────────

def piksel_rota(n=PIKSEL_NOKTA):
    """Kapali bicimli, rastgeleliksiz piksel rota (ON_KAYIT SS5)."""
    x0, y0 = PIKSEL_BASLANGIC
    return [[x0 + PIKSEL_ADIM_SAGA * i, y0 - PIKSEL_ADIM_ILERI * i]
            for i in range(n)]


def uretim_waypointleri():
    """URETIM yolundan (piksel -> yerel metre) waypoint listesi."""
    return piksel_rotayi_yerele_cevir(piksel_rota(), OLCEK_MPP)


def en_genis_waypointler(n):
    """Sozlesme tavanindaki en uzun ondalik gosterim (UST SINIR, tipik degil)."""
    return [[-59.99, -59.99] for _ in range(n)]


# ── KIP 1: paket boyutu ──────────────────────────────────────────────────────

def boyut_olc():
    """N1..N5 — hepsi `protocol.encode()` cagrilarak sayilir."""
    if set(TAM_TELEMETRI) != set(HEARTBEAT_TELEMETRI_ALANLARI):
        raise SystemExit(
            "OLCULEMEDI: TAM_TELEMETRI alan kumesi sozlesmedeki "
            "HEARTBEAT_TELEMETRI_ALANLARI ile ayni degil; eksik/fazla: "
            f"{sorted(set(TAM_TELEMETRI) ^ set(HEARTBEAT_TELEMETRI_ALANLARI))}")

    yerel = uretim_waypointleri()
    ref = [float(YAYIN_REF_XY[0]), float(YAYIN_REF_XY[1])]
    sonuc = {}

    with sabit_saat():
        # ── N1: mesaj tipi basina cerceve ────────────────────────────────────
        ornekler = {
            MESAJ_OPEN_ROUTE: open_route(ORNEK_ROAD, ORNEK_CONF, yerel, ref,
                                         seq=SABIT_SEQ),
            MESAJ_NO_ROUTE: rota_yok(ORNEK_SEBEP, ORNEK_DETAY, seq=SABIT_SEQ),
            MESAJ_HEARTBEAT: heartbeat("iha", seq=SABIT_SEQ, **TAM_TELEMETRI),
            MESAJ_ACK: ack(SABIT_SEQ, "ika", MESAJ_OPEN_ROUTE),
            MESAJ_CMD: command(ORNEK_CMD, ORNEK_HEDEF, seq=SABIT_SEQ,
                               oturum=ORNEK_OTURUM),
            MESAJ_IHA_LANDED: iha_landed(seq=SABIT_SEQ),
        }
        sonuc["N1_tip_basina_bayt"] = {t: boy(m) for t, m in ornekler.items()}
        sonuc["N1_alanlar"] = {t: sorted(m) for t, m in ornekler.items()}

        # Degisken alanlari OLMAYAN en kucuk bicimler (sabit alan tabani).
        asgari = {
            MESAJ_OPEN_ROUTE: open_route(ORNEK_ROAD, ORNEK_CONF, [], None,
                                         seq=SABIT_SEQ),
            MESAJ_NO_ROUTE: rota_yok(ORNEK_SEBEP, None, seq=SABIT_SEQ),
            MESAJ_HEARTBEAT: heartbeat("iha", seq=SABIT_SEQ),
            MESAJ_ACK: ack(SABIT_SEQ, "ika"),
            MESAJ_CMD: command(ORNEK_CMD, ORNEK_HEDEF, seq=SABIT_SEQ),
            MESAJ_IHA_LANDED: iha_landed(seq=SABIT_SEQ),
        }
        sonuc["N1_asgari_bayt"] = {t: boy(m) for t, m in asgari.items()}

        # ── N2: OPEN_ROUTE waypoint egrisi ───────────────────────────────────
        egri_uretim, egri_genis = {}, {}
        for n in WAYPOINT_EGRISI:
            egri_uretim[n] = boy(open_route(ORNEK_ROAD, ORNEK_CONF,
                                            yerel[:n], ref, seq=SABIT_SEQ))
            egri_genis[n] = boy(open_route(ORNEK_ROAD, ORNEK_CONF,
                                           en_genis_waypointler(n),
                                           [-59.99, -59.99], seq=SABIT_SEQ))
        # Sozlesme tavani ayri bir UST SINIR satiri (ON_KAYIT SS2.2-EK).
        egri_uretim[MAX_WAYPOINTS] = boy(open_route(
            ORNEK_ROAD, ORNEK_CONF,
            (yerel * ((MAX_WAYPOINTS // len(yerel)) + 1))[:MAX_WAYPOINTS],
            ref, seq=SABIT_SEQ))
        egri_genis[MAX_WAYPOINTS] = boy(open_route(
            ORNEK_ROAD, ORNEK_CONF, en_genis_waypointler(MAX_WAYPOINTS),
            [-59.99, -59.99], seq=SABIT_SEQ))
        sonuc["N2_open_route_egrisi"] = {
            "uretim_yolu": {str(k): v for k, v in sorted(egri_uretim.items())},
            "en_genis": {str(k): v for k, v in sorted(egri_genis.items())},
            "sozlesme_tavani_waypoint": MAX_WAYPOINTS,
            "karisimda_kullanilan_waypoint": len(yerel),
        }

        # ── N3: HEARTBEAT iki uc ─────────────────────────────────────────────
        tam_hb = heartbeat("iha", seq=SABIT_SEQ, **TAM_TELEMETRI)
        sonuc["N3_heartbeat"] = {
            "asgari_bayt": boy(heartbeat("iha", seq=SABIT_SEQ)),
            "tam_telemetri_bayt": boy(tam_hb),
            "tam_telemetri_alan_sayisi": len(TAM_TELEMETRI),
            "alanlar": sorted(TAM_TELEMETRI),
        }

        # ── N4: alan basina marjinal maliyet ─────────────────────────────────
        marjinal = {}
        for alan in sorted(TAM_TELEMETRI):
            eksik = {k: v for k, v in TAM_TELEMETRI.items() if k != alan}
            marjinal[alan] = boy(tam_hb) - boy(
                heartbeat("iha", seq=SABIT_SEQ, **eksik))
        sonuc["N4_alan_marjinal_bayt"] = marjinal

        # conf alaninin ondalik genisligi (model ciktisi float32 -> float).
        sonuc["N4_conf_ondalik_bayt"] = {
            "kisa": boy(open_route(ORNEK_ROAD, ORNEK_CONF, yerel, ref,
                                   seq=SABIT_SEQ)),
            "float32_genisleyen": boy(open_route(
                ORNEK_ROAD, ORNEK_CONF_GENIS, yerel, ref, seq=SABIT_SEQ)),
        }

        # ── N5a: seq basamak egrisi ──────────────────────────────────────────
        sonuc["N5_seq_basamak_bayt"] = {
            str(s): boy(heartbeat("iha", seq=s, **TAM_TELEMETRI))
            for s in SEQ_BASAMAKLARI}

    # ── N5b: GERCEK saat altinda bayt oynamasi ───────────────────────────────
    # `t` = round(time.time(), 3); ondaligin sondaki sifirlari JSON'da
    # kisalir, yani AYNI cerceve gercek saat altinda birkac bayt oynar.
    boyutlar = []
    for _ in range(SAAT_ORNEK):
        boyutlar.append(boy(heartbeat("iha", seq=SABIT_SEQ, **TAM_TELEMETRI)))
        time.sleep(0.001)
    sonuc["N5_gercek_saat_bayt"] = {
        "ornek": len(boyutlar), "min": min(boyutlar), "maks": max(boyutlar),
        "sabit_saatteki_deger": sonuc["N3_heartbeat"]["tam_telemetri_bayt"],
    }

    # Cozulebilirlik kaniti: her cerceve GERCEK `decode()` ile geri okunur ve
    # yeniden cerceveleme BAYT-ES cikar. (Sozluk esitligi aranmaz: uretici
    # waypoint'leri demet dondurur, JSON'dan liste olarak geri gelir — teldeki
    # bayt ayni, Python tipi degil.)
    for tip, m in ornekler.items():
        if encode(decode(encode(m))) != encode(m):
            raise SystemExit(
                f"OLCULEMEDI: {tip} cerceve donusu bayt-es degil")
    sonuc["cerceve_donusu_bayt_es"] = True
    return sonuc


# ── KIP 2: gercek gorev karisimi ─────────────────────────────────────────────

class SayanLink:
    """Uretim link'ini saydam kusatan bayt/paket sayaci.

    Davranisi DEGISTIRMEZ: `send`/`recv` aynen alt link'e gider. UDP'de datagram
    = cerceve oldugundan paket sayaci cozulen cerceve sayisiyla ayni anlamdadir
    (`scripts/sik_rf_olc.py` ile ayni sozlesme).
    """

    def __init__(self, link, saat=time.monotonic):
        self.link = link
        self._saat = saat
        self._kilit = threading.Lock()
        self.t0 = None
        self.t_son = None
        self.gonderilen_bayt = 0
        self.gonderilen_paket = 0
        self.alinan_bayt = 0
        self.alinan_paket = 0
        self.kovalar = {}

    @property
    def peer(self):
        return self.link.peer

    def send(self, data, peer=None):
        simdi = self._saat()
        with self._kilit:
            if self.t0 is None:
                self.t0 = simdi
            self.t_son = simdi
            self.gonderilen_bayt += len(data)
            self.gonderilen_paket += 1
            kova = int((simdi - self.t0) / KOVA_S)
            self.kovalar[kova] = self.kovalar.get(kova, 0) + len(data)
        self.link.send(data, peer)

    def recv(self, *a, **kw):
        veri, adres = self.link.recv(*a, **kw)
        if veri:
            simdi = self._saat()
            with self._kilit:
                if self.t0 is None:
                    self.t0 = simdi
                self.t_son = simdi
                self.alinan_bayt += len(veri)
                self.alinan_paket += 1
        return veri, adres

    def close(self):
        self.link.close()

    def hiz(self):
        sure = 0.0 if self.t0 is None else max(0.0, self.t_son - self.t0)
        d = veri_hizi_hesapla(sure, self.gonderilen_bayt, self.alinan_bayt,
                              self.gonderilen_paket, self.alinan_paket)
        # N8: 1,0 s'lik kovalarda tepe. Son (kismi) kova disarida birakilir —
        # yarim saniyelik bir kova tepe degeri YAPAY olarak dusurur/yukseltir.
        tam_kovalar = [v for k, v in sorted(self.kovalar.items())
                       if k < int(sure / KOVA_S)]
        d["tepe_gonderilen_bayt_s"] = max(tam_kovalar) if tam_kovalar else None
        d["kova_sayisi"] = len(tam_kovalar)
        return d


class YksUcu:
    """URETIMDEKI YKS davranisi (comms/yks_gui.py):

    `NO_ROUTE` ve `IHA_LANDED`'a ACK uretir; `OPEN_ROUTE`'a URETMEZ — o ACK
    hakem 2/2 onayina baglidir (CONTRACTS SS6.6). Olcum bunu duzeltmez.
    """

    def __init__(self, link):
        self.link = link
        self.reader = protocol.FrameReader()
        self.sayim = {}
        self._dur = threading.Event()
        self._thr = threading.Thread(target=self._dongu, daemon=True)

    def start(self):
        self._thr.start()
        return self

    def stop(self):
        self._dur.set()
        self._thr.join(timeout=2.0)

    def _dongu(self):
        while not self._dur.is_set():
            veri, adres = self.link.recv()
            if not veri:
                continue
            for m in self.reader.feed(veri):
                tip = m.get("type")
                self.sayim[tip] = self.sayim.get(tip, 0) + 1
                if tip in (MESAJ_NO_ROUTE, MESAJ_IHA_LANDED):
                    self.link.send(encode(ack(m["seq"], "yks", tip)), adres)


def karisim_kos(yapilandirma, kadans_hz, pencere_s=PENCERE_S):
    """Gercek uretim yollariyla gorev karisimini kosar, hatta giden bayti sayar.

    `yapilandirma` = "saha"  -> tek yayin hatti, `wait_ack=False` (SiK yolu)
                   = "udp"   -> `ika` + `yks` akranlari, `wait_ack=True`
    """
    yerel = uretim_waypointleri()
    piksel = piksel_rota()
    kapatilacak, sonuc = [], {}
    try:
        if yapilandirma == "udp":
            ika_link = SayanLink(UDPLink(bind=("127.0.0.1", 0), timeout=0.05))
            yks_link = SayanLink(UDPLink(bind=("127.0.0.1", 0), timeout=0.05))
            kapatilacak += [ika_link, yks_link]
            ika_adres = ("127.0.0.1", ika_link.link.port)
            yks_adres = ("127.0.0.1", yks_link.link.port)
            iha_link = SayanLink(UDPLink(bind=("127.0.0.1", 0), timeout=0.3))
            kapatilacak.append(iha_link)
            # K8: IKA rota ACK'inin YKS'ye yansitilmasi URETIM davranisidir.
            ika = IkaReceiver(ika_link, yks_peer=yks_adres).start()
            yks = YksUcu(yks_link).start()
            peers = {"ika": ika_adres, "yks": yks_adres}
            wait_ack = True
            uclar = {"iha": iha_link, "ika": ika_link, "yks": yks_link}
        elif yapilandirma == "saha":
            # SiK seri hattinin UDP ikizi: TEK yayin ortami, gonderen ACK
            # BEKLEMEZ (`yayinci_kur` seri dalinda `wait_ack=False`). Ama ALICI
            # yine de ACK URETIR (`IkaReceiver.send_ack` varsayilani True,
            # seride `_rota_ack` ortama tek kopya yazar) — o baytlar ortak
            # ortamda hat yukune GIRER ve burada sayilir.
            ika_link = SayanLink(UDPLink(bind=("127.0.0.1", 0), timeout=0.05))
            kapatilacak.append(ika_link)
            iha_link = SayanLink(UDPLink(bind=("127.0.0.1", 0), timeout=0.3))
            kapatilacak.append(iha_link)
            ika = IkaReceiver(ika_link).start()
            yks = None
            peers = {"broadcast": ("127.0.0.1", ika_link.link.port)}
            wait_ack = False
            uclar = {"iha": iha_link, "ika": ika_link}
        else:
            raise ValueError(f"bilinmeyen yapilandirma: {yapilandirma}")

        yayinci = KararYayinci(
            IhaSender(iha_link, peers),
            heartbeat_aralik=IHA_HEARTBEAT_ARALIK_S,
            repeat=4, interval=0.25, wait_ack=wait_ack,
            telemetri_saglayici=lambda: dict(
                {k: v for k, v in TAM_TELEMETRI.items() if k != "karar_yas"}),
        ).start()

        adim = 1.0 / float(kadans_hz)
        bas = time.monotonic()
        sonraki = bas
        beslenen = 0
        while time.monotonic() - bas < pencere_s:
            simdi = time.monotonic()
            if simdi >= sonraki:
                yayinci.karar(ORNEK_ROAD, ORNEK_CONF, piksel, OLCEK_MPP)
                beslenen += 1
                sonraki += adim
            time.sleep(0.005)
        yayinci.stop()
        if yks is not None:
            yks.stop()
        ika.stop()

        hiz = iha_link.hiz()
        hat = hat_yuku(uclar)
        gonderilen_tipler = {}
        for tip, _bilgi, _seq, _acked in yayinci.gonderilen:
            gonderilen_tipler[tip] = gonderilen_tipler.get(tip, 0) + 1
        sonuc = {
            "yapilandirma": yapilandirma,
            "wait_ack": wait_ack,
            "akranlar": sorted(peers),
            "karar_kadansi_hz": float(kadans_hz),
            "heartbeat_araligi_s": float(IHA_HEARTBEAT_ARALIK_S),
            "pencere_s": float(pencere_s),
            "waypoint_sayisi": len(yerel),
            "beslenen_karar": beslenen,
            "yayinlanan_karar": len(yayinci.gonderilen),
            "yayinlanan_karar_tipleri": gonderilen_tipler,
            "heartbeat_sayisi": yayinci.heartbeat_sayisi,
            "yayinci_hatalari": list(yayinci.hata),
            "veri_hizi": hiz,
            "hat_yuku": hat,
            "uc_basina_gonderilen_bayt": {
                ad: uc.gonderilen_bayt for ad, uc in sorted(uclar.items())},
        }
        if yks is not None:
            sonuc["yks_gorulen_tipler"] = dict(yks.sayim)
    finally:
        for k in kapatilacak:
            try:
                k.close()
            except OSError:
                pass
    return sonuc


def hat_yuku(uclar):
    """ORTAK ORTAMA giden toplam: her ucun GONDERDIGI bayt/paket toplami.

    NEDEN ucun kendi RX'i degil: SiK hava arayuzu TDM'dir, iki yon AYNI kanali
    paylasir. Gondericinin ACK'i BEKLEMEDIGI saha yapilandirmasinda alicinin
    urettigi ACK gondericinin soketinde hic okunmaz — ama ortamda YER KAPLAR.
    Ilk kosumda (kosum_ciktisi_v1_eksik.txt) bu bayt sayilmiyordu; duzeltme hat
    yukunu BUYUTUR, kucultmez.
    """
    bayt = sum(u.gonderilen_bayt for u in uclar.values())
    paket = sum(u.gonderilen_paket for u in uclar.values())
    t0 = min((u.t0 for u in uclar.values() if u.t0 is not None), default=None)
    t1 = max((u.t_son for u in uclar.values() if u.t_son is not None),
             default=None)
    sure = 0.0 if t0 is None else max(0.0, t1 - t0)
    d = veri_hizi_hesapla(sure, bayt, 0, paket, 0)
    d["not"] = ("ORTAK ORTAM yuku: tum uclarin GONDERDIGI bayt/paket toplami "
                "(IHA yayini + alici ACK'leri). Alinan sutunu bu hesapta "
                "kullanilmaz; cift saymayi onlemek icin sifirdir.")
    return d


def doluluk(hiz, hat=None):
    """57600 8N1 hat doluluk orani — HESAP (10 bit/bayt), olcum degil."""
    tx = hiz.get("gonderilen_bayt_s")
    if tx is None:
        return None
    if hat is not None and hat.get("gonderilen_bayt_s") is not None:
        paylasimli = hat["gonderilen_bayt_s"]
    else:
        paylasimli = tx + (hiz.get("alinan_bayt_s") or 0.0)
    return {
        "ham_bayt_s": HAM_BAYT_S,
        "ms_basina_bayt": round(MS_BASINA_BAYT, 4),
        "tek_yon_yuzde": round(100.0 * tx / HAM_BAYT_S, 2),
        "paylasimli_yuzde": round(100.0 * paylasimli / HAM_BAYT_S, 2),
        "ecc_acikken_paylasimli_yuzde": round(
            100.0 * paylasimli / (HAM_BAYT_S / 2.0), 2),
        "ecc_durumu": "OLCULEMEDI",
        "not": ("Doluluk HESAPTIR (57600 8N1 = 10 bit/bayt -> 5760 B/s). "
                "SiK hava arayuzu TDM ile iki yon arasinda PAYLASILIR; "
                "hava hizi (Air Speed) ve ECC ayari OKUNMAMISTIR "
                "(results/atolye_20260912/SONUC_SABLONU.md A6 satiri bos). "
                "ECC acikken etkin hiz yariya iner — kaynak "
                "ATOLYE_TEST_GUNU_20260912.md A6 'HESAP + BENZER OLCUM "
                "- olcum degil' satiri; varsayim degil, ALINTIDIR."),
    }


def gorev_toplami(hiz):
    """N10 — EKSTRAPOLASYON: olculen ortalama B/s x sartname gorev suresi."""
    tx = hiz.get("gonderilen_bayt_s")
    if tx is None:
        return None
    return {
        "yontem": "EKSTRAPOLASYON (olculen ortalama B/s x sure); "
                  "900 s'lik kosum YAPILMADI",
        "iha_gorev_suresi_s": float(SARTNAME_IHA_GOREV_SURESI_S),
        "ika_gorev_suresi_s": float(SARTNAME_IKA_GOREV_SURESI_S),
        "iha_toplam_bayt": int(round(tx * SARTNAME_IHA_GOREV_SURESI_S)),
        "ika_toplam_bayt": int(round(tx * SARTNAME_IKA_GOREV_SURESI_S)),
    }


def karisim_olc(pencere_s=PENCERE_S):
    kadanslar = {
        "jetson_olculmus": round(1000.0 / JETSON_PT_P50_MS, 3),
        "tavan": KADANS_TAVAN_HZ,
    }
    kosumlar = {}
    for yapilandirma in ("saha", "udp"):
        for ad, hz in kadanslar.items():
            anahtar = f"{yapilandirma}_{ad}"
            r = karisim_kos(yapilandirma, hz, pencere_s)
            r["kadans_adi"] = ad
            r["doluluk"] = doluluk(r["veri_hizi"], r["hat_yuku"])
            r["gorev_toplami"] = gorev_toplami(r["veri_hizi"])
            kosumlar[anahtar] = r
            print(f"  [{anahtar}] kadans {hz} Hz · "
                  f"TX {r['veri_hizi']['gonderilen_bayt']} B / "
                  f"{r['veri_hizi']['gonderilen_paket']} pkt · "
                  f"{r['veri_hizi']['gonderilen_bayt_s']:.1f} B/s · "
                  f"doluluk %{r['doluluk']['paylasimli_yuzde']}", flush=True)
    return {
        "kadanslar_hz": kadanslar,
        "kadans_kaynagi": {
            "jetson_olculmus": ("results/jetson_20260906/"
                                "jetson_fps_20260906_orin_nano/ozet.json "
                                "vakalar[0].metrikler_ms.toplam_ms.p50 = "
                                f"{JETSON_PT_P50_MS} ms"),
            "tavan": "olculen kadans DEGIL; ust sinir senaryosu (ON_KAYIT SS2.2)",
        },
        "kosumlar": kosumlar,
    }


# ── Okunur tablo (JSON'lardan URETILIR, elle yazilmaz) ───────────────────────

def tr(x, basamak=1):
    """Turkce ondalik (virgul) bicimi — tablo ve FDR ayni sayiyi gorur."""
    if x is None:
        return "OLCULEMEDI"
    return f"{x:.{basamak}f}".replace(".", ",")


def tavan_waypoint_duyarliligi(boyut, kosum):
    """HESAP: rota sozlesme tavanindaki waypoint sayisina cikarsa hat yuku.

    Olcum degildir — olculen hat yukune, olculen iki OPEN_ROUTE boyutunun
    farki x olculen OPEN_ROUTE cerceve sayisi eklenir. Her carpan bir
    artefakttan gelir.
    """
    egri = boyut["N2_open_route_egrisi"]
    tavan = str(egri["sozlesme_tavani_waypoint"])
    # Karisimda kullanilan cerceve = N1'deki OPEN_ROUTE ornegidir (ayni rota).
    fark = (egri["uretim_yolu"][tavan]
            - boyut["N1_tip_basina_bayt"][MESAJ_OPEN_ROUTE])
    cerceve = kosum["yayinlanan_karar"] * _tur_sayisi(kosum)
    hat = kosum["hat_yuku"]
    sure = hat["sure_s"]
    if sure <= 0:
        return None
    yeni_bayt_s = hat["gonderilen_bayt_s"] + (fark * cerceve) / sure
    return {
        "waypoint_farki_bayt": fark,
        "open_route_cerceve_sayisi": cerceve,
        "hat_bayt_s": yeni_bayt_s,
        "paylasimli_yuzde": 100.0 * yeni_bayt_s / HAM_BAYT_S,
        "ecc_acikken_paylasimli_yuzde": 100.0 * yeni_bayt_s / (HAM_BAYT_S / 2.0),
    }


def _tur_sayisi(kosum):
    """Bir kararin hatta kac OPEN_ROUTE cercevesi urettigi — OLCUMDEN."""
    karar = kosum["yayinlanan_karar"]
    if not karar:
        return 0
    if kosum["yapilandirma"] == "udp":
        return kosum["yks_gorulen_tipler"].get(MESAJ_OPEN_ROUTE, 0) / karar
    # saha: tek ortam, IKA gordugu her cerceveye ACK yazar -> ACK sayisi = cerceve
    return round((kosum["veri_hizi"]["gonderilen_paket"]
                  - kosum["heartbeat_sayisi"]) / karar, 3)


def tablo_uret(boyut, karisim):
    b, k = boyut, karisim
    egri = b["N2_open_route_egrisi"]
    s = []
    s.append("# T243 — mesaj paket boyutu ve gerçek görev veri hızı (ÖLÇÜM)")
    s.append("")
    s.append("> Bu dosya **üretilir** (`scripts/paket_boyutu_olc.py --kip tablo`); "
             "elle düzenlenmez. Her sayı `paket_boyutu.json` ya da "
             "`gorev_veri_hizi.json` dosyasından gelir.")
    s.append("")
    s.append(f"- ölçüm: {b['kunye']['zaman']} · {b['kunye']['makine']} · "
             f"Python {b['kunye']['python']}")
    s.append(f"- ön kayıt: `{b['kunye']['on_kayit']}` · tohum {b['kunye']['tohum']}")
    s.append(f"- taşıyıcı: {b['kunye']['tasiyici_notu']}")
    s.append("")

    s.append("## 1. Mesaj tipi başına çerçeve boyutu (N1)")
    s.append("")
    s.append("`len(protocol.encode(msg))` — gerçek bayt. `t` ve `seq` genişliği "
             f"sabitlendi (`t` = {b['kunye']['sabit_zaman']}, "
             f"`seq` = {b['kunye']['sabit_seq']}).")
    s.append("")
    s.append("| `type` | asgari alanla (B) | örnek çerçeve (B) | örnek çerçevenin alanları |")
    s.append("|---|---:|---:|---|")
    for tip in (MESAJ_OPEN_ROUTE, MESAJ_NO_ROUTE, MESAJ_HEARTBEAT, MESAJ_ACK,
                MESAJ_CMD, MESAJ_IHA_LANDED):
        s.append(f"| `{tip}` | {b['N1_asgari_bayt'][tip]} | "
                 f"{b['N1_tip_basina_bayt'][tip]} | "
                 + ", ".join(f"`{a}`" for a in b["N1_alanlar"][tip]) + " |")
    s.append("")
    s.append(f"Örnek çerçeveler: `OPEN_ROUTE` üretim yolundan "
             f"{egri['karisimda_kullanilan_waypoint']} waypoint'li rota; "
             f"`HEARTBEAT` tam telemetri "
             f"({b['N3_heartbeat']['tam_telemetri_alan_sayisi']} alan); "
             f"`CMD` `oturum` alanlı; `ACK` `ref_tip` alanlı. Her çerçeve "
             "`decode()` ile geri okunup yeniden çerçevelendiğinde bayt-eş "
             f"çıktı: **{str(b['cerceve_donusu_bayt_es']).lower()}**.")
    s.append("")

    s.append("## 2. `OPEN_ROUTE` — waypoint sayısına göre (N2)")
    s.append("")
    s.append("| waypoint | üretim yolu (B) | en geniş / üst sınır (B) |")
    s.append("|---:|---:|---:|")
    for n in [str(x) for x in WAYPOINT_EGRISI] + [str(egri["sozlesme_tavani_waypoint"])]:
        etiket = n + (" (sözleşme tavanı)"
                      if n == str(egri["sozlesme_tavani_waypoint"]) else "")
        s.append(f"| {etiket} | {egri['uretim_yolu'][n]} | {egri['en_genis'][n]} |")
    egim_u = (egri["uretim_yolu"]["20"] - egri["uretim_yolu"]["10"]) / 10.0
    egim_g = (egri["en_genis"]["20"] - egri["en_genis"]["10"]) / 10.0
    s.append("")
    s.append(f"Eğim: üretim yolunda **{tr(egim_u, 1)} B/waypoint**, en geniş "
             f"gösterimde **{tr(egim_g, 1)} B/waypoint** (10 → 20 waypoint "
             "aralığından). `conf` alanının ondalık genişliği de boyutu "
             f"değiştirir: {b['N4_conf_ondalik_bayt']['kisa']} B (kısa) → "
             f"{b['N4_conf_ondalik_bayt']['float32_genisleyen']} B "
             "(float32'den genişleyen ondalık).")
    s.append("")

    s.append("## 3. `HEARTBEAT` telemetri alanlarının maliyeti (N3, N4)")
    s.append("")
    s.append(f"asgari (`node` + ortak alanlar) **{b['N3_heartbeat']['asgari_bayt']} B** → "
             f"tam telemetri **{b['N3_heartbeat']['tam_telemetri_bayt']} B** "
             f"({b['N3_heartbeat']['tam_telemetri_alan_sayisi']} alan).")
    s.append("")
    s.append("| alan | marjinal maliyet (B) |")
    s.append("|---|---:|")
    for alan, bayt in sorted(b["N4_alan_marjinal_bayt"].items(),
                             key=lambda kv: (-kv[1], kv[0])):
        s.append(f"| `{alan}` | {bayt} |")
    s.append("")

    s.append("## 4. `seq` ve `t` alanlarının bayt oynaması (N5)")
    s.append("")
    s.append("| `seq` | tam telemetrili `HEARTBEAT` (B) |")
    s.append("|---:|---:|")
    for sq in SEQ_BASAMAKLARI:
        s.append(f"| {sq} | {b['N5_seq_basamak_bayt'][str(sq)]} |")
    g = b["N5_gercek_saat_bayt"]
    s.append("")
    s.append(f"Gerçek saat altında ({g['ornek']} örnek) aynı çerçeve "
             f"**{g['min']}–{g['maks']} B** arasında oynar: `t` = "
             "`round(time.time(), 3)` ve ondalığın sondaki sıfırları JSON'da "
             "kısalır. Sabit saatteki değer "
             f"{g['sabit_saatteki_deger']} B'dir.")
    s.append("")

    s.append("## 5. Gerçek görev karışımı — ölçülen veri hızı (N6–N9)")
    s.append("")
    s.append(f"Pencere kadans başına {tr(k['kosumlar']['saha_tavan']['pencere_s'], 0)} s. "
             "`saha` = SiK seri yolunun UDP ikizi (tek yayın ortamı, "
             "`wait_ack=False`); `udp` = dev/sim yolu (`ika` + `yks` akranları, "
             "`wait_ack=True`). Kadanslar: "
             f"{tr(k['kadanslar_hz']['jetson_olculmus'], 3)} Hz "
             "(Jetson Orin Nano `pt` p50'den ÖLÇÜLMÜŞ) ve "
             f"{tr(k['kadanslar_hz']['tavan'], 1)} Hz (ölçülen kadans değil, "
             "**tavan senaryosu**).")
    s.append("")
    s.append("| koşum | beslenen karar | **yayınlanan** karar | HEARTBEAT | "
             "İHA TX (B) | İHA TX (B/s) | İHA TX (pkt/s) | tepe TX (B/s) | "
             "İHA RX (B/s) | ortak ortam (B/s) |")
    s.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for ad in ("saha_jetson_olculmus", "saha_tavan", "udp_jetson_olculmus",
               "udp_tavan"):
        r = k["kosumlar"][ad]
        v, h = r["veri_hizi"], r["hat_yuku"]
        s.append(f"| `{ad}` | {r['beslenen_karar']} | {r['yayinlanan_karar']} | "
                 f"{r['heartbeat_sayisi']} | {v['gonderilen_bayt']} | "
                 f"{tr(v['gonderilen_bayt_s'], 1)} | "
                 f"{tr(v['gonderilen_paket_s'], 3)} | "
                 f"{v['tepe_gonderilen_bayt_s']} | "
                 f"{tr(v['alinan_bayt_s'], 1)} | "
                 f"{tr(h['gonderilen_bayt_s'], 1)} |")
    s.append("")
    s.append("🔴 **Ölçümün asıl bulgusu — karar yayın tavanı ≈ 1 karar/s.** "
             "Beslenen karar sayısı kadansla artıyor ama **yayınlanan** karar "
             "sayısı artmıyor: `IhaSender._tekrarli_gonder` her kararı "
             "`repeat=4 × interval=0,25 s` = **1,0 s** boyunca tutar; "
             "`KararYayinci`'nin latest-wins yuvası fazlasını düşürür. "
             f"`saha` koşumlarında {k['kosumlar']['saha_jetson_olculmus']['beslenen_karar']} "
             f"ve {k['kosumlar']['saha_tavan']['beslenen_karar']} besleme, "
             f"ikisinde de {k['kosumlar']['saha_tavan']['yayinlanan_karar']} yayın "
             f"verdi; `udp` koşumlarında "
             f"{k['kosumlar']['udp_jetson_olculmus']['beslenen_karar']} ve "
             f"{k['kosumlar']['udp_tavan']['beslenen_karar']} besleme, ikisinde de "
             f"{k['kosumlar']['udp_tavan']['yayinlanan_karar']} yayın verdi. "
             "Bu bir hat darboğazı değil, **gönderim tekrar tasarımının** "
             "sonucudur (D-383'te ölçülen ~3,3/s sınıfının aynı ailesi).")
    s.append("")
    s.append("`udp` koşumunda YKS `OPEN_ROUTE`'a ACK üretmez (hakem 2/2'ye "
             "bağlıdır, `CONTRACTS.md` §6.6); bu yüzden her karar tekrar "
             "turunun tamamını koşar. YKS ucunun gördüğü çerçeveler: "
             + " · ".join(
                 f"`{t}` {n}" for t, n in sorted(
                     k["kosumlar"]["udp_tavan"]["yks_gorulen_tipler"].items()))
             + ".")
    s.append("")

    s.append("## 6. Görev süresi boyunca toplam (N10) — EKSTRAPOLASYON")
    s.append("")
    gt = k["kosumlar"]["saha_tavan"]["gorev_toplami"]
    s.append(f"Yöntem: {gt['yontem']}. Süreler şartname §6.2'den "
             f"(İHA {tr(gt['iha_gorev_suresi_s'], 0)} s, "
             f"İKA {tr(gt['ika_gorev_suresi_s'], 0)} s).")
    s.append("")
    s.append("| koşum | İHA 900 s (B) | İKA 600 s (B) |")
    s.append("|---|---:|---:|")
    for ad in ("saha_jetson_olculmus", "saha_tavan", "udp_jetson_olculmus",
               "udp_tavan"):
        g2 = k["kosumlar"][ad]["gorev_toplami"]
        s.append(f"| `{ad}` | {g2['iha_toplam_bayt']} | {g2['ika_toplam_bayt']} |")
    s.append("")

    s.append("## 7. 57600 8N1 hat doluluğu (N11, N12) — HESAP")
    s.append("")
    d0 = k["kosumlar"]["saha_tavan"]["doluluk"]
    s.append(f"Ham bütçe {tr(d0['ham_bayt_s'], 0)} B/s "
             f"(57600 baud, 8N1 = 10 bit/bayt → {tr(d0['ms_basina_bayt'], 3)} ms/bayt). "
             "Doluluk **hesaptır**, ölçüm değildir.")
    s.append("")
    s.append("| koşum | tek yön (İHA TX) | paylaşımlı (ortak ortam) | ECC açıkken paylaşımlı |")
    s.append("|---|---:|---:|---:|")
    for ad in ("saha_jetson_olculmus", "saha_tavan", "udp_jetson_olculmus",
               "udp_tavan"):
        d = k["kosumlar"][ad]["doluluk"]
        s.append(f"| `{ad}` | %{tr(d['tek_yon_yuzde'], 2)} | "
                 f"%{tr(d['paylasimli_yuzde'], 2)} | "
                 f"%{tr(d['ecc_acikken_paylasimli_yuzde'], 2)} |")
    s.append("")
    s.append(f"**ECC durumu: {d0['ecc_durumu']}.** {d0['not']}")
    s.append("")

    s.append("## 8. Duyarlılık — rota sözleşme tavanına çıkarsa (HESAP)")
    s.append("")
    s.append("| koşum | waypoint farkı (B) | `OPEN_ROUTE` çerçevesi | ortak ortam (B/s) | paylaşımlı | ECC açıkken |")
    s.append("|---|---:|---:|---:|---:|---:|")
    for ad in ("saha_tavan", "udp_tavan"):
        du = tavan_waypoint_duyarliligi(b, k["kosumlar"][ad])
        s.append(f"| `{ad}` | {du['waypoint_farki_bayt']} | "
                 f"{tr(du['open_route_cerceve_sayisi'], 0)} | "
                 f"{tr(du['hat_bayt_s'], 1)} | %{tr(du['paylasimli_yuzde'], 2)} | "
                 f"%{tr(du['ecc_acikken_paylasimli_yuzde'], 2)} |")
    s.append("")
    s.append("Rota sözleşme tavanındaki waypoint sayısına çıkarsa hat doluluğu "
             "yukarıdaki değerlere taşınır; ECC açık sütunu ham bütçeyi aşar. "
             "Bu bir ölçüm değil, ölçülen iki büyüklüğün (çerçeve boyutu farkı × "
             "çerçeve sayısı) çarpımıdır.")
    s.append("")
    return "\n".join(s) + "\n"


# ── Kunye ve yazim ───────────────────────────────────────────────────────────

def kunye():
    return {
        "etiket": OLCUM_ETIKETI,
        "is": "T243",
        "kayit": "D-462 C · yonerge Y-3.3.4-M03",
        "on_kayit": "results/fdr_sprint_20260910/T243/ON_KAYIT.md",
        "arac": "scripts/paket_boyutu_olc.py",
        "tohum": TOHUM,
        "zaman": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "makine": platform.platform(),
        "python": platform.python_version(),
        "tasiyici_notu": TASIYICI_NOTU,
        "sabit_zaman": SABIT_ZAMAN,
        "sabit_seq": SABIT_SEQ,
        "protokol_surumu": protocol.PROTOCOL_VERSION,
        "rapor_doluluk_esigi_yuzde": RAPOR_DOLULUK_ESIGI_YUZDE,
    }


def _yaz(yol, veri):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"  -> {yol}", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kip", choices=("boyut", "karisim", "tablo", "hepsi"),
                    default="hepsi")
    ap.add_argument("--pencere", type=float, default=PENCERE_S,
                    help="karisim kipinde kadans basina pencere (s)")
    ap.add_argument("--cikti-dizin", default=None,
                    help="JSON ciktilarinin yazilacagi dizin")
    a = ap.parse_args(argv)

    dizin = Path(a.cikti_dizin) if a.cikti_dizin else None
    if a.kip in ("boyut", "hepsi"):
        print("[boyut] protocol.encode() ile gercek bayt sayimi", flush=True)
        b = {"kunye": kunye(), **boyut_olc()}
        print(f"  tip basina: {b['N1_tip_basina_bayt']}", flush=True)
        if dizin:
            _yaz(dizin / "paket_boyutu.json", b)
    if a.kip in ("karisim", "hepsi"):
        print(f"[karisim] gercek gorev trafigi, pencere {a.pencere:.0f} s x 4 "
              "kosum", flush=True)
        k = {"kunye": kunye(), **karisim_olc(a.pencere)}
        if dizin:
            _yaz(dizin / "gorev_veri_hizi.json", k)
    if a.kip in ("tablo", "hepsi"):
        if not dizin:
            print("[tablo] --cikti-dizin gerekli", file=sys.stderr)
            return 2
        b = json.loads((dizin / "paket_boyutu.json").read_text(encoding="utf-8"))
        k = json.loads((dizin / "gorev_veri_hizi.json").read_text(encoding="utf-8"))
        yol = dizin / "TABLO.md"
        yol.write_text(tablo_uret(b, k), encoding="utf-8")
        print(f"  -> {yol}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
