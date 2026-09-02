#!/usr/bin/env python3
"""NEDEN (Faz B · CONTRACTS §7.4 · D-403): SiK 433 MHz kipinde IHA'daki UC
uretim sureci — `rpi_inference --telsiz-seri`, `iha_inis_yayinci --serial`,
`iha_komut_alici --serial` — AYNI /dev/ttyUSB0'i ister. Seri port TEK
SAHIPLIDIR: ikinci surec ya acamaz ya ilkinin bayt akisini calar ve her iki
taraf sessizce kor olur (Pixhawk tarafinda ayni olgu §7.4'te olculdu; SiK ucu
onun protokol ikizidir).

Bu surec portu TEK BASINA acar ve NAVITAS cercevelerini (comms/protocol.py:
tek satir JSON + newline) UDP loopback uzerinden COGULLAR — MAVLink router'in
NAVITAS protokolu icin karsiligi. Tuketiciler kendi UDP kiplerinde kalir; onlarin
KODU DEGISMEZ, yalniz hedef adresleri hub'a cevrilir.

  UDP -> seri : tuketici hub'in soketine datagram yollar; hub datagrami OLDUGU
                GIBI seri hatta yazar ve gonderenin adresini "ogrenilen"
                kumesine ekler (ACK'ler geri ona da gidecek).
  seri -> UDP : gelen baytlar kalici FrameReader ile cerceveye toparlanir; her
                TAM cerceve encode(decode(...)) ile yeniden tek satir yapilip
                (statik tuketiciler ∪ ogrenilenler) adreslerinin HEPSINE
                yayinlanir (fan-out). Her datagram TAM OLARAK BIR cercevedir —
                `iha_komut_alici.poll` UDP'de datagram basina taze FrameReader
                kullanir (D-403 KUCUK-4), parca gonderilirse cerceve kaybolur.

Topoloji (Jetson, SiK kipi):
  seri_hub          --port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007
  rpi_inference     --yks-hedef 127.0.0.1:5100 --ika-hedef 127.0.0.1:5100 ...
  iha_inis_yayinci  --yks 127.0.0.1:5100 --ika 127.0.0.1:5100 ...
  iha_komut_alici   --bind 0.0.0.0:5007 --mavlink udp:127.0.0.1:14552 ...
`iha_komut_alici` hic gondermeden dinler; bu yuzden STATIK tuketici olarak
verilir. `rpi_inference` / `iha_inis_yayinci` once gonderir, adresleri
ogrenilir; YKS/IKA'dan donen ACK'ler fan-out ile onlara ulasir.

Fail-closed / fail-visible:
  * Seri hat arizasi (okuma ya da yazma OSError/SerialException): seri
    KAPATILIR, KIRMIZI log, SERI_YENIDEN_ACMA_ARALIGI_S sonra `seri_ac`
    callback'iyle yeniden acma denenir. UDP tarafi YASAR; arizada UDP'den
    gelen cerceveler DUSURULUR ve sayilir — KUYRUKLANMAZ (bayat rota, hat
    donunce yayinlanmasin). Yeniden acilinca log + sayac.
  * Bozuk cerceve (JSON degil, dict degil, yeniden kodlanamiyor) yayinlanmaz,
    `bozuk` sayaci artar; sonraki gecerli cerceve gecer. HICBIR cerceve hub'i
    oldurmez (D-405): derin ic ice `[[[[...` satiri json'da RecursionError
    uretir — FrameReader onu yutar, hub ayrica feed/encode'u `except
    Exception` ile sarar (savunma derinligi; KIRMIZI log + `bozuk`).
  * UDP okuma hatasi (orn. Windows'ta tavan ustu datagram WinError 10040)
    hub'i oldurmez: `udp_hata` sayilir, ilkinde KIRMIZI log. Datagram tavani
    UDP_DATAGRAM_TAVANI_B (tam datagram alinir, budanmaz).
  * Newline'siz datagram (sozlesme disi uretici) seride SONRAKI cerceveye
    yapisip ikisini de oldururdu (D-405 Q1); hub eksik newline'i EKLER,
    `newline_eklenen` sayar, ilkinde KIRMIZI log. Uyumlu uretici (encode())
    icin bayt-es aktarim degismez.
  * Sessiz basari yalani yok: hedefsiz fan-out, yazilamayan fan-out, dusurulen
    datagram — hepsi sayilir ve periyodik logda gorunur.

Tek sahiplik (D-405): hub UDP ucunu SO_REUSEADDR'siz acar (`UDPLink(...,
reuse=False)`) — ayni --bind ile ikinci hub OSError -> cikis 3 (sessiz sagir
kopya yok). Seri portu `SerialLink(exclusive=True)` ile acar — Linux'ta
ikinci surec flock'a takilir -> cikis 4. Runbook'taki manuel komut systemd
birimi calisirken KOSULMAZ (`systemctl stop navitas-seri-hub` once).

Ogrenilen kume kurali (D-405 · CONTRACTS §7.5'e mimar yazar): tavan SAYI
tabanlidir (OGRENILEN_TAVANI); asilinca EN AZ TAZELENEN (son gonderimi en
eski) adres dusurulur ve KIRMIZI loglanir. Uzun omurlu ama seyrek gonderen
bir tuketici bu tahliyeye yakalanabilir; UZUN OMURLU TUKETICI STATIK
`--tuketici` ILE VERILIR — statik liste tahliyeye tabi degildir.

SIGTERM (systemd stop): isleyici `durdur()` bayragini kurar; dongu temiz
cikar, son sayac logu ve kapat() kosar (D-405; Python varsayilani surec
aninda olur, finally kosmazdi).

Kullanim:
  python3 seri_hub.py --port /dev/ttyUSB0 --bind 127.0.0.1:5100 \\
                      --tuketici 127.0.0.1:5007
"""
import argparse
import signal
import socket
import sys
import threading
import time
from pathlib import Path

_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

from link import SerialLink, UDPLink  # noqa: E402
from protocol import FrameReader, decode, encode  # noqa: E402

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


LOG_ONEKI = "[SERI_HUB]"
YEREL_HOST = "127.0.0.1"
#: Hub'in UDP ucu. Tuketiciler (--yks-hedef/--ika-hedef/--yks/--ika) buraya
#: yollar. Loopback'e baglanir: hub yalniz Jetson ICI cogullayicidir.
VARSAYILAN_BIND = f"{YEREL_HOST}:5100"
VARSAYILAN_BAUD = 57600           # iha_komut_alici / ika_receiver ile ayni SiK
VARSAYILAN_LOG_ARALIGI_S = 10.0   # periyodik sayac logu (0 = kapali)

#: Seri ariza sonrasi yeniden acma denemeleri arasi bekleme. 1 s: USB yeniden
#: numaralandirma ~0,5-1 s; daha sik denemek /dev dugumu daha olusmadan
#: KIRMIZI log seli uretir, daha seyrek denemek rota yayinini bosuna geciktirir.
SERI_YENIDEN_ACMA_ARALIGI_S = 1.0
#: Seri okuma zaman asimi (ilk bayt). D-403 dersi: 0,3 s'lik zaman asimi tek
#: iplikli hub'da UDP->seri yonunu her turda 300 ms bekletirdi (parasut tekrar
#: araligi 0,20 s'nin USTU). 20 ms: 57600 baud'da ~115 bayt, tur gecikmesi
#: tavani yine 20 ms — LINUX'ta (hub yalniz Jetson'da kosar). Windows'ta
#: zamanlayici tanecigi 15,6 ms: 20 ms bekleme ~31 ms, bos poll ~47 ms
#: (D-405 olcumu, olc_granul.py); testler bunu tavanlarinda hesaba katar.
#: Kilit: tests/test_faz_b_seri_hub.py (sabit <= parasut araliginin
#: bir bolumu, kurulan hub'da ser.timeout bu degere cekilir).
SERI_OKUMA_ZAMAN_ASIMI_S = 0.02
#: UDP okuma zaman asimi. `UDPLink.recv` yalniz socket.timeout'u yutar; 0
#: (gercek non-blocking) BlockingIOError sizdirir. 1 ms: tur basina tek kacirma
#: maliyeti, UDP tarafi fiilen non-blocking.
UDP_OKUMA_ZAMAN_ASIMI_S = 0.001
#: Bir turda UDP'den bosaltilacak en cok datagram / seriden yapilacak en cok
#: okuma: iki yon birbirini ACLIKTAN oldurmesin (tek iplik, sirali hizmet).
UDP_TUR_TAVANI = 64
SERI_TUR_TAVANI = 128
#: Seri kapaliyken tur hizi (UDP tarafi non-blocking oldugundan aksi halde
#: dongu sicak doner). Seri acikken tur hizini seri zaman asimi belirler.
BOS_TUR_BEKLEME_S = SERI_OKUMA_ZAMAN_ASIMI_S
#: Ogrenilen tuketici adresi tavani: her surec yeniden acilisinda yeni efemer
#: port ogrenilir; tavan asilinca EN AZ TAZELENEN (son gonderimi en eski)
#: dusurulur ve KIRMIZI loglanir (olu porta fan-out zararsizdir ama sinirsiz
#: kume 8-9 saatlik provada sessiz sismedir). D-405: tavan SAYI tabanli
#: kalir; sessiz-ama-canli tuketici korunmak istiyorsa STATIK --tuketici
#: ile verilir (dokstring kurali). Kilit: test_faz_b_seri_hub (tahliye
#: sirasi + log + uzun omurlu tuketicinin kaldigi).
OGRENILEN_TAVANI = 32
#: Bir UDP datagraminin en cok boyu: IPv4 UDP yuku 65507 B, 65535 tavan onu
#: kapsar. D-405 ("4096 B'den buyuk UDP datagram"): recv tavani 4096 iken
#: Windows'ta buyuk datagram OSError (WinError 10040) SIZDIRIP hub'i
#: olduruyor, Linux'ta ise sessizce budanip newline'siz parca seriye
#: gidiyordu. Tam datagram alinir; hata ayrica yakalanir (`udp_hata`).
UDP_DATAGRAM_TAVANI_B = 65535
#: Cerceve sonlandirici (protocol.encode her cerceveye ekler). Newline'siz
#: datagram gelirse hub bunu ekler (D-405 Q1).
CERCEVE_SONU = b"\n"


def _adres(metin, efemer_serbest=False):
    """'HOST:PORT' -> (ip, port). Ad cozumlenir ki statik 'localhost:5007' ile
    ogrenilen ('127.0.0.1', 5007) AYNI hedef sayilsin (fan-out tekilligi).
    Port 0 (efemer) yalniz --bind icin serbesttir; bir tuketiciye 0 portuna
    gonderim anlamsizdir."""
    try:
        host, port = str(metin).rsplit(":", 1)
        port = int(port)
    except ValueError as exc:
        raise ValueError(f"adres HOST:PORT bicimde olmali: {metin!r}") from exc
    alt = 0 if efemer_serbest else 1
    if not alt <= port <= 65535:
        raise ValueError(f"port {alt}..65535 olmali: {metin!r}")
    host = host.strip("[]") or YEREL_HOST
    try:
        ip = socket.gethostbyname(host)
    except OSError as exc:
        raise ValueError(f"adres cozumlenemedi: {metin!r} ({exc})") from exc
    return (ip, port)


class SeriHub:
    """SiK seri hatti <-> UDP loopback cogullayicisi (tek iplik, `poll` turlu).

    seri_link   : SerialLink (hub portu TEK BASINA acar). None verilirse hub
                  "ariza" durumunda baslar ve `seri_ac` ile acmayi dener.
    udp_link    : hub'in KENDI UDP soketi (UDPLink(bind=...)); tuketiciler
                  buraya yollar, fan-out buradan cikar. Zaman asimi hub
                  tarafindan UDP_OKUMA_ZAMAN_ASIMI_S'ye cekilir (hub'in
                  sahip oldugu soket; D-403 gecikme dersi).
    tuketiciler : statik (host, port) listesi — hic gondermeden de cerceve
                  alacak DINLEYEN surecler (orn. iha_komut_alici 5007).
    seri_ac     : arizada yeniden acma callback'i, SerialLink dondurur
                  (orn. lambda: SerialLink(port, baud)). None ise hub ariza
                  sonrasi seri tarafi KAPALI kalir (UDP tarafi yine yasar,
                  datagramlar dusurulur ve sayilir).
    saat        : monotonik saat (test enjeksiyonu icin).
    """

    def __init__(self, seri_link, udp_link, tuketiciler=(), *, seri_ac=None,
                 yeniden_acma_araligi_s=SERI_YENIDEN_ACMA_ARALIGI_S,
                 log_aralik_s=VARSAYILAN_LOG_ARALIGI_S, saat=time.monotonic):
        if not callable(saat):
            raise TypeError("saat cagrilabilir olmali")
        if seri_ac is not None and not callable(seri_ac):
            raise TypeError("seri_ac cagrilabilir olmali")
        if float(yeniden_acma_araligi_s) < 0:
            raise ValueError("yeniden acma araligi negatif olamaz")
        self.saat = saat
        self.udp_link = udp_link
        self.tuketiciler = []
        for adr in tuketiciler:
            host, port = adr
            adr = (str(host), int(port))
            if adr not in self.tuketiciler:
                self.tuketiciler.append(adr)
        self.seri_ac = seri_ac
        self.yeniden_acma_araligi_s = float(yeniden_acma_araligi_s)
        self.log_aralik_s = float(log_aralik_s)
        self.ogrenilen = {}              # adr -> son gorulme (saat); ekleme sirali
        self.okuyucu = FrameReader()     # kalici: seri bayt akisi
        self.sayac = {"udp_alinan": 0, "seri_yazilan": 0, "seri_cerceve": 0,
                      "fanout_gonderim": 0, "fanout_hata": 0, "hedefsiz": 0,
                      "bozuk": 0, "dusurulen": 0, "seri_ariza": 0,
                      "yeniden_acma": 0, "yeniden_acma_hatasi": 0,
                      # D-405: UDP okuma hatasi (hub olmez) / eksik newline
                      "udp_hata": 0, "newline_eklenen": 0}
        self._dur = threading.Event()
        self._ariza_t = None             # seri kapaliyken: son ariza/deneme ani
        self._seri_yok_loglandi = False
        self._hedefsiz_loglandi = False
        self._udp_hata_loglandi = False   # ilkinde KIRMIZI, sonrasi sayacta
        self._newline_loglandi = False
        self._son_log_t = None
        self.seri_link = None
        sock = getattr(udp_link, "sock", None)
        if sock is not None:
            sock.settimeout(UDP_OKUMA_ZAMAN_ASIMI_S)
        if seri_link is not None:
            self._seri_bagla(seri_link, ilk=True)
        else:
            self._ariza_t = self.saat()
            self._logla("seri hat KAPALI basladi; yeniden acma denenecek",
                        kirmizi=True)

    # ── log ──────────────────────────────────────────────────────────────
    def _logla(self, metin, kirmizi=False):
        try:
            damga = f"t={float(self.saat()):.3f}"
        except (TypeError, ValueError, OverflowError):
            damga = "t=?"
        seviye = "KIRMIZI " if kirmizi else ""
        print(f"{LOG_ONEKI} {damga} {seviye}{metin}",
              file=sys.stderr if kirmizi else sys.stdout, flush=True)

    def _sayac_logla(self):
        ozet = " ".join(f"{k}={v}" for k, v in self.sayac.items())
        self._logla(f"sayac {ozet} atilan_bayt={self.okuyucu.atilan_bayt} "
                    f"seri={'acik' if self.seri_link is not None else 'KAPALI'} "
                    f"statik={len(self.tuketiciler)} ogrenilen={len(self.ogrenilen)}",
                    kirmizi=self.seri_link is None)

    # ── seri hat yasam dongusu ───────────────────────────────────────────
    def _seri_bagla(self, link, ilk=False):
        ser = getattr(link, "ser", None)
        if ser is not None:
            try:
                # Hub'in sahip oldugu port: tur gecikmesi tavani (dokstring).
                ser.timeout = SERI_OKUMA_ZAMAN_ASIMI_S
            except (AttributeError, ValueError, OSError):
                pass
        self.seri_link = link
        self.okuyucu = FrameReader()     # yeni akis: eski yarim cerceve atilir
        self._ariza_t = None
        self._seri_yok_loglandi = False
        if not ilk:
            self.sayac["yeniden_acma"] += 1
            self._logla("seri hat YENIDEN ACILDI")

    def _seri_arizasi(self, yon, exc):
        """Seri okuma/yazma hatasi: kapat, KIRMIZI log, yeniden acma saatini kur."""
        link, self.seri_link = self.seri_link, None
        self.sayac["seri_ariza"] += 1
        self._ariza_t = self.saat()
        self._logla(f"seri hat {yon} ARIZASI ({type(exc).__name__}: {exc}); "
                    f"seri kapatildi, UDP tarafi yasiyor, gelen cerceveler "
                    f"DUSURULECEK; {self.yeniden_acma_araligi_s:.1f} s sonra "
                    f"yeniden acma " +
                    ("denenecek" if self.seri_ac else "YOK (seri_ac verilmedi)"),
                    kirmizi=True)
        if link is not None:
            try:
                link.close()
            except Exception as exc2:      # kapatma hatasi arizayi gizlemesin
                self._logla(f"seri kapatma hatasi ({type(exc2).__name__}: "
                            f"{exc2})", kirmizi=True)

    def _seri_yeniden_ac_gerekirse(self):
        if self.seri_link is not None:
            return
        if self.seri_ac is None:
            if not self._seri_yok_loglandi:
                self._seri_yok_loglandi = True
                self._logla("seri hat KAPALI ve yeniden acici yok; UDP "
                            "cerceveleri dusurulmeye devam edecek", kirmizi=True)
            return
        simdi = self.saat()
        if (self._ariza_t is not None
                and simdi - self._ariza_t < self.yeniden_acma_araligi_s):
            return
        self._ariza_t = simdi
        try:
            link = self.seri_ac()
        except Exception as exc:           # SerialException, OSError, ImportError
            self.sayac["yeniden_acma_hatasi"] += 1
            self._logla(f"seri yeniden acma BASARISIZ ({type(exc).__name__}: "
                        f"{exc}); {self.yeniden_acma_araligi_s:.1f} s sonra tekrar",
                        kirmizi=True)
            return
        if link is None:
            self.sayac["yeniden_acma_hatasi"] += 1
            self._logla("seri yeniden acma BASARISIZ (seri_ac None dondu)",
                        kirmizi=True)
            return
        self._seri_bagla(link)

    # ── UDP -> seri ──────────────────────────────────────────────────────
    def _ogren(self, adr):
        if adr is None:
            return
        adr = (str(adr[0]), int(adr[1]))
        yeni = adr not in self.ogrenilen
        self.ogrenilen.pop(adr, None)   # sona tasi: ekleme sirasi = tazelik
        self.ogrenilen[adr] = self.saat()
        if yeni:
            self._logla(f"tuketici ogrenildi: {adr[0]}:{adr[1]}")
        while len(self.ogrenilen) > OGRENILEN_TAVANI:
            eski = next(iter(self.ogrenilen))
            del self.ogrenilen[eski]
            self._logla(f"ogrenilen tavani ({OGRENILEN_TAVANI}) asildi; en az "
                        f"tazelenen dusuruldu: {eski[0]}:{eski[1]} (uzun omurlu "
                        f"tuketici STATIK --tuketici ile verilir)", kirmizi=True)

    def _udp_turu(self):
        for _ in range(UDP_TUR_TAVANI):
            try:
                veri, adr = self.udp_link.recv(UDP_DATAGRAM_TAVANI_B)
            except OSError as exc:
                # D-405 ("4096 B'den buyuk UDP datagram"): recv hatasi (WinError
                # 10040 vb.) hub'i OLDURMEZ — calistir() yalniz KeyboardInterrupt
                # yakalar, sizan OSError surecin cikisi ve ~2 s kor pencereydi.
                # Sayilir; ilkinde KIRMIZI, sonrasi periyodik sayacta (sel yok).
                self.sayac["udp_hata"] += 1
                if not self._udp_hata_loglandi:
                    self._udp_hata_loglandi = True
                    self._logla(f"UDP okuma HATASI ({type(exc).__name__}: {exc});"
                                f" datagram dusuruldu, hub yasiyor (sonrakiler "
                                f"yalniz udp_hata sayacinda)", kirmizi=True)
                return
            if not veri:
                return
            self.sayac["udp_alinan"] += 1
            self._ogren(adr)
            if self.seri_link is None:
                self.sayac["dusurulen"] += 1        # kuyruk YOK: bayat rota olmasin
                continue
            if not veri.endswith(CERCEVE_SONU):
                # D-405 Q1 ("newline'siz datagram seride SONRAKI cerceveye
                # yapisir"): seri bayt akisinda sinir yalniz newline'dir;
                # eksikse bu datagram VE komsusu YKS'de birlikte kaybolurdu
                # (olculdu: seri_yazilan=2, YKS 0 cerceve). Uyumlu uretici
                # (protocol.encode) icin bu dal hic kosmaz -> bayt-es aktarim.
                veri += CERCEVE_SONU
                self.sayac["newline_eklenen"] += 1
                if not self._newline_loglandi:
                    self._newline_loglandi = True
                    self._logla(f"newline'siz datagram ({adr[0]}:{adr[1]}, "
                                f"{len(veri) - 1} B): sozlesme disi uretici; "
                                f"newline EKLENDI (sonrakiler yalniz sayacta)",
                                kirmizi=True)
            try:
                self.seri_link.send(veri)
            except OSError as exc:                  # SerialException dahil
                self.sayac["dusurulen"] += 1
                self._seri_arizasi("yazma", exc)
                continue
            self.sayac["seri_yazilan"] += 1

    # ── seri -> UDP (fan-out) ────────────────────────────────────────────
    def hedefler(self):
        """Statik tuketiciler ∪ ogrenilenler, tekil, sirali."""
        return list(dict.fromkeys(self.tuketiciler + list(self.ogrenilen)))

    def _fanout(self, veri):
        hedefler = self.hedefler()
        if not hedefler:
            self.sayac["hedefsiz"] += 1
            if not self._hedefsiz_loglandi:
                self._hedefsiz_loglandi = True
                self._logla("seriden cerceve geldi ama HICBIR tuketici yok "
                            "(statik verilmedi, kimse gondermedi); cerceve "
                            "dusuruldu", kirmizi=True)
            return
        for adr in hedefler:
            try:
                self.udp_link.send(veri, adr)
            except OSError as exc:
                self.sayac["fanout_hata"] += 1
                self._logla(f"fan-out {adr[0]}:{adr[1]} yazilamadi "
                            f"({type(exc).__name__}: {exc})", kirmizi=True)
            else:
                self.sayac["fanout_gonderim"] += 1

    def _cerceveleri_isle(self, veri):
        # `bozuk` = newline ile kapanip cerceve uretmeyen her parca (JSON degil,
        # bos satir) + dict olmayan ya da yeniden kodlanamayan (NaN) JSON.
        # FrameReader bozugu SESSIZCE atar; hub GORUNUR sayar (fail-visible).
        cerceveler = []
        try:
            for mesaj in self.okuyucu.feed(veri):
                cerceveler.append(mesaj)
        except Exception as exc:
            # D-405 ("Hub sureci derin ic ice JSON satirinda RecursionError ile
            # OLUR"): FrameReader artik RecursionError'i da yutar; bu sarmal
            # SAVUNMA DERINLIGIDIR — hub SiK hattinin tek erisim noktasidir,
            # cozucuden sizan HICBIR istisna onu oldurmez. Istisnali satir
            # cerceve uretmedi; asagidaki newline farki onu `bozuk` sayar.
            # Uretecin kalan tamponu korunur (satir zaten ayrilmisti).
            self._logla(f"cerceve cozme ISTISNASI ({type(exc).__name__}: "
                        f"{str(exc)[:120]}); parca bozuk sayildi, hub yasiyor",
                        kirmizi=True)
        self.sayac["bozuk"] += veri.count(b"\n") - len(cerceveler)
        for mesaj in cerceveler:
            if not isinstance(mesaj, dict):
                self.sayac["bozuk"] += 1           # tuketiciler m.get(...) yapar
                continue
            try:
                ham = encode(mesaj)                # tek satir + newline garanti
            except Exception as exc:               # TypeError/ValueError (NaN) + D-405 beklenmeyen
                self.sayac["bozuk"] += 1
                self._logla(f"cerceve yeniden kodlanamadi ({type(exc).__name__}: "
                            f"{str(exc)[:120]}); dusuruldu", kirmizi=True)
                continue
            self.sayac["seri_cerceve"] += 1
            self._fanout(ham)

    def _seri_turu(self):
        if self.seri_link is None:
            self._dur.wait(BOS_TUR_BEKLEME_S)   # sicak dongu olmasin
            return
        for _ in range(SERI_TUR_TAVANI):
            try:
                veri, _adr = self.seri_link.recv()
            except OSError as exc:                  # SerialException dahil
                self._seri_arizasi("okuma", exc)
                return
            if not veri:
                return
            self._cerceveleri_isle(veri)

    # ── dongu ────────────────────────────────────────────────────────────
    def poll(self):
        """Bir tur: gerekirse seriyi yeniden ac; UDP -> seri; seri -> fan-out."""
        self._seri_yeniden_ac_gerekirse()
        self._udp_turu()
        self._seri_turu()
        if self.log_aralik_s > 0:
            simdi = self.saat()
            if self._son_log_t is None:
                self._son_log_t = simdi
            elif simdi - self._son_log_t >= self.log_aralik_s:
                self._son_log_t = simdi
                self._sayac_logla()

    def calistir(self):
        self._dur.clear()
        self._logla(f"basladi: seri={'acik' if self.seri_link else 'KAPALI'} "
                    f"udp={getattr(self.udp_link, 'port', '?')} statik="
                    + ",".join(f"{h}:{p}" for h, p in self.tuketiciler))
        try:
            while not self._dur.is_set():
                self.poll()
        except KeyboardInterrupt:
            self._logla("kapatiliyor (KeyboardInterrupt)")
        finally:
            self._sayac_logla()

    def durdur(self):
        self._dur.set()

    def kapat(self):
        self.durdur()
        for nesne in (self.seri_link, self.udp_link):
            kapat = getattr(nesne, "close", None)
            if callable(kapat):
                try:
                    kapat()
                except (OSError, RuntimeError):
                    pass
        self.seri_link = None


# ── CLI ──────────────────────────────────────────────────────────────────────

#: `_sigterm_kur` isleyiciyi kuramadiysa (ana iplik disi) dondurdugu nobetci.
_SIGTERM_KURULAMADI = object()


def _sigterm_kur(hub):
    """SIGTERM -> hub.durdur(); onceki isleyiciyi dondurur (geri alma icin).

    D-405 ("SIGTERM isleyicisi yok"): systemd `stop` SIGTERM yollar; Python
    varsayilani surecin ANINDA olmesidir -> calistir() finally'si, son sayac
    logu (dusurulen/bozuk/fanout_hata) ve kapat() kosmaz, TimeoutStopSec=5
    anlamsizdi. Isleyici yalniz bayragi kurar; dongu bir tur icinde (<= seri
    zaman asimi) temiz cikar, cikis 0. `signal.signal` yalniz ana iplikte
    calisir; iplikten cagrilan main (test) icin KIRMIZI not, isleyici yok.
    """
    def isleyici(signum, frame):        # noqa: ARG001 — imza signal'in
        hub.durdur()

    try:
        eski = signal.signal(signal.SIGTERM, isleyici)
    except (ValueError, OSError, AttributeError) as exc:
        print(f"{LOG_ONEKI} KIRMIZI SIGTERM isleyicisi kurulamadi "
              f"({type(exc).__name__}: {exc}); systemd stop'ta son sayac logu "
              f"kaybolur", file=sys.stderr, flush=True)
        return _SIGTERM_KURULAMADI
    return signal.SIG_DFL if eski is None else eski


def _sigterm_geri_al(eski):
    """main() cikarken onceki SIGTERM isleyicisini geri koy (test hijyeni)."""
    if eski is _SIGTERM_KURULAMADI:
        return
    try:
        signal.signal(signal.SIGTERM, eski)
    except (ValueError, OSError, TypeError):
        pass


def _arg_parser():
    ap = argparse.ArgumentParser(
        description="SiK seri hub: portu tek basina acar, NAVITAS cercevelerini "
                    "UDP loopback uzerinden cogullar (CONTRACTS §7.4 ikizi)")
    ap.add_argument("--port", required=True,
                    help="SiK seri portu (serial_for_url uyumlu: /dev/ttyUSB0, "
                         "COM7, socket://host:port, loop://)")
    ap.add_argument("--baud", type=int, default=VARSAYILAN_BAUD,
                    help="SiK seri baud (varsayilan %(default)s)")
    ap.add_argument("--bind", default=VARSAYILAN_BIND,
                    help="hub UDP ucu HOST:PORT; tuketiciler buraya yollar "
                         "(varsayilan %(default)s)")
    ap.add_argument("--tuketici", action="append", default=[], metavar="HOST:PORT",
                    help="statik dinleyici (tekrarlanabilir; orn. iha_komut_alici "
                         "127.0.0.1:5007) — gondermeden de cerceve alir")
    ap.add_argument("--log-aralik", type=float, default=VARSAYILAN_LOG_ARALIGI_S,
                    help="periyodik sayac logu (sn; 0 = kapali; varsayilan "
                         "%(default)s)")
    return ap


def main(argv=None):
    parser = _arg_parser()
    args = parser.parse_args(argv)
    if args.baud <= 0:
        parser.error("--baud pozitif olmali")
    if args.log_aralik < 0:
        parser.error("--log-aralik negatif olamaz")
    try:
        bind = _adres(args.bind, efemer_serbest=True)
        tuketiciler = [_adres(t) for t in args.tuketici]
    except ValueError as exc:
        parser.error(str(exc))

    def seri_ac():
        return SerialLink(args.port, args.baud, timeout=SERI_OKUMA_ZAMAN_ASIMI_S)

    udp = None
    hub = None
    sigterm_eski = _SIGTERM_KURULAMADI
    try:
        try:
            # D-405 tek sahiplik: SO_REUSEADDR YOK — ayni --bind ile ikinci hub
            # (runbook'taki manuel komut + systemd birimi) sessizce sagir bir
            # kopya olmak yerine burada OSError alir -> cikis 3.
            udp = UDPLink(bind=bind, timeout=UDP_OKUMA_ZAMAN_ASIMI_S,
                          reuse=False)
        except OSError as exc:
            print(f"{LOG_ONEKI} KIRMIZI HATA: UDP ucu acilamadi {args.bind}: "
                  f"{exc} (baska bir hub mu calisiyor? once `systemctl stop "
                  f"navitas-seri-hub`)", file=sys.stderr, flush=True)
            return 3
        try:
            seri = seri_ac()
        except (ImportError, OSError, ValueError) as exc:
            # Acilista port yoksa SESSIZCE beklemek yerine gorunur cikis:
            # operator yanlis --port'u hemen gorsun. Ucus icinde kopma ayri
            # (hub calisirken ariza -> yeniden acma dongusu).
            print(f"{LOG_ONEKI} KIRMIZI HATA: seri port acilamadi {args.port!r}: "
                  f"{exc}", file=sys.stderr, flush=True)
            return 4
        hub = SeriHub(seri, udp, tuketiciler, seri_ac=seri_ac,
                      log_aralik_s=args.log_aralik)
        sigterm_eski = _sigterm_kur(hub)           # D-405: systemd stop temiz
        print(f"{LOG_ONEKI} seri {args.port} @ {args.baud} <-> udp "
              f"{bind[0]}:{bind[1]} statik={len(tuketiciler)}", flush=True)
        hub.calistir()
        return 0
    finally:
        _sigterm_geri_al(sigterm_eski)
        if hub is not None:
            hub.kapat()
        elif udp is not None:
            udp.close()


if __name__ == "__main__":
    raise SystemExit(main())
