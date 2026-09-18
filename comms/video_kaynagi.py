#!/usr/bin/env python3
"""ONARIM-19 — VIDEO TELEMETRI KAYNAGI KESFI (YKS tarafi).

NEDEN: koordinat/karar hatti radyo telemetrisindedir (telsiz BANDI kararI ACIK:
master D-499 '433 MHz', dal tunel-saha-20260918 'RFD900A 915 MHz' — bkz.
DAL_CAKISMA_RAPORU_20260918.md) ve BU MODUL ONA
DOKUNMAZ. Video telemetri ise "baglanabilirsek guzel olur" kapsamindadir (kullanici,
18 Eylul): donanim sahada takilacak, ama yer birimi goruntuyu HANGI adres/port/yoldan
verecegi **onceden bilinmiyor** — SIYI'nin surumune, kumandanin USB/tethering kipine ve
yakalama karti olup olmadigina gore degisir. Sahada elle IP denemek yerine YKS bir
**aday tablosunu tarar**, gercekten akan kaynagi bulur ve onu kullanir.

TASARIM KURALLARI (gevsetilmez):
  1. FAIL-CLOSED KARAR HATTI: bu modul hicbir kosulda rota/komut/telemetri yoluna
     dokunmaz. Video bulunamazsa YKS bugunku "VIDEO YOK" davranisinda kalir.
  2. FAIL-VISIBLE: her aday icin sonuc (`DURUM_*`) ve sebep dondurulur; "belki vardir"
     yoktur. Secilen kaynak, KANIT olarak hangi yontemle dogrulandigini tasir.
  3. DOGRULAMA = AKAN VIDEO. Acik TCP portu YETMEZ (bir port 200 dondurup video
     vermeyebilir): aday ancak `ffprobe`/OpenCV gercek bir video akisi cozunce CANLI olur.
  4. YANLIS KAYNAK SECME RISKI: PC'nin kendi web kamerasi da /dev/video0'dir. Yerel
     yakalama karti adaylari bu yuzden VARSAYILAN KAPALIDIR (`cihaz_da=True` ister).
  5. Sabitler burada TABLODUR, koda dagilmis ciplak sayi degildir (anayasa madde 16).

ADRESLER NEREDEN (dis donanim, ag degil kablo seviyesi):
  * `192.168.144.x` — SIYI hava/yer birimi kendi ic agi. .11 hava birimi, .12 yer birimi,
    .20/.25 kamera ya da HDMI donusturucu, .30 kullanici cihazi (Jetson onerisi;
    `scripts/isaretli_gosterici.py` bu sabitleri zaten REDDEDILEN liste olarak tasiyor).
  * `192.168.42.1` — kumanda USB ile PC'ye takildiginda (Android RNDIS/tethering) ag gecidi.
  * Jetson kendi HTTP koprusu (`kamera_koprusu`): ham kamera :8080, isaretli kare :8081.
Bu adreslerin hicbiri kampus agi DEGILDIR; hepsi donanimin kendi kablosunun ucudur.

RTSP -> YKS: `comms/kamera_istemci.py` YALNIZ HTTP `/kare.jpg` + `/durum` okur. Bulunan
kaynak RTSP/UDP ise araya `scripts/kamera_koprusu.py --kaynak <url>` konur (MJPEG'e cevirir);
`kopru_komutu()` o komutu uretir. Yeni video kodu yazilmaz, var olan kopru kullanilir.

OLCULEMEDI: gercek SIYI donanimi bu makinede yok. Olculen: aday uretimi, siralama,
tarama mantigi, sonuc/sebep alanlari, onbellek, kopru komutu — tests/test_onarim19_video_kaynagi.py.
"""
import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

# ── Sonuc durumlari ───────────────────────────────────────────────────────────
DURUM_CANLI = "CANLI"                 # akis cozuldu (KANIT)
DURUM_PORT_KAPALI = "PORT_KAPALI"     # TCP acilmadi / cihaz yok
DURUM_AKIS_YOK = "AKIS_YOK"           # port acik ama video akisi cozulemedi
DURUM_ARAC_YOK = "ARAC_YOK"           # ffprobe ve OpenCV yok -> dogrulanamadi
DURUM_ATLANDI = "ATLANDI"             # onceki bir aday secildi, sira gelmedi

# ── Aday turleri ──────────────────────────────────────────────────────────────
TUR_RTSP = "rtsp"
TUR_HTTP = "http"
TUR_UDP = "udp"
TUR_CIHAZ = "cihaz"                   # yerel yakalama karti / UVC

# ── Dis donanim tablosu ───────────────────────────────────────────────────────
SIYI_KAMERA_ADRESLERI = ("192.168.144.25", "192.168.144.20",
                         "192.168.144.11", "192.168.144.12")
SIYI_RTSP_PORT = 8554
SIYI_RTSP_YOLLARI = ("main.264", "video0", "video1", "stream=0", "live")
SIYI_FPV_UDP_PORT = 37256
KUMANDA_TETHER_ADRESLERI = ("192.168.42.1", "192.168.42.129")
JETSON_HTTP_PORTLARI = (8081, 8080)   # 8081 isaretli kare (T227), 8080 ham kamera
JETSON_SIYI_IP = "192.168.144.30"     # SIYI agindayken Jetson'a onerilen adres

VARSAYILAN_TCP_ZAMAN_ASIMI_S = 0.4
VARSAYILAN_AKIS_ZAMAN_ASIMI_S = 4.0
KESIF_ONCELIGI = 2             # kesifle ogrenilen adres: elle/onbellekten hemen sonra
VARSAYILAN_ONBELLEK = str(Path.home() / ".config" / "navitas" / "video_kaynagi.json")

# Kopru: RTSP/UDP kaynagi YKS'nin okuyabildigi MJPEG'e cevirir.
HTTP_AKIS_YOLU = "/video"      # kamera_koprusu MJPEG ucu (kok URL video DEGILDIR)
KOPRU_BETIGI = "scripts/kamera_koprusu.py"
VARSAYILAN_KOPRU_PORT = 8090


class Aday(object):
    """Denenecek tek video kaynagi. `oncelik` kucukse once denenir."""

    __slots__ = ("ad", "url", "tur", "oncelik", "aciklama", "host", "port",
                 "_dogrulama_url")

    def __init__(self, ad, url, tur, oncelik, aciklama, host=None, port=None,
                 dogrulama_url=None):
        self.ad = ad
        self.url = url
        self.tur = tur
        self.oncelik = int(oncelik)
        self.aciklama = aciklama
        self.host = host
        self.port = port
        self._dogrulama_url = dogrulama_url

    @property
    def dogrulama_url(self):
        """Akisin GERCEKTEN cozulecegi uc.

        HTTP koprusunun KOK adresi bir video degildir (404 verir); akis `/video`
        ucundadir. YKS'ye verilen `url` yine koktur — `kamera_istemci` oradan
        `/kare.jpg` ve `/durum` turetir.
        """
        if self._dogrulama_url:
            return self._dogrulama_url
        if self.tur == TUR_HTTP:
            # Operator TAM bir uc verdiyse (yol bos degil) ona dokunulmaz; yalniz
            # kopru KOKU (".../" ya da yolsuz) /video'ya cevrilir.
            yol = self.url.split("://", 1)[-1]
            yol = yol[yol.find("/"):] if "/" in yol else ""
            if yol in ("", "/"):
                return self.url.rstrip("/") + HTTP_AKIS_YOLU
        return self.url

    def __repr__(self):                                    # pragma: no cover
        return "Aday({!r}, {!r})".format(self.ad, self.url)

    def sozluk(self):
        return {"ad": self.ad, "url": self.url, "tur": self.tur,
                "oncelik": self.oncelik, "aciklama": self.aciklama,
                "host": self.host, "port": self.port,
                "dogrulama_url": self.dogrulama_url}


class Sonuc(object):
    """Bir adayin tarama sonucu. `durum` DURUM_* sabitlerinden biridir."""

    __slots__ = ("aday", "durum", "sebep", "ayrinti", "sure_s")

    def __init__(self, aday, durum, sebep, ayrinti=None, sure_s=None):
        self.aday = aday
        self.durum = durum
        self.sebep = sebep
        self.ayrinti = ayrinti or {}
        self.sure_s = sure_s

    @property
    def canli(self):
        return self.durum == DURUM_CANLI

    def sozluk(self):
        d = self.aday.sozluk()
        d.update({"durum": self.durum, "sebep": self.sebep,
                  "ayrinti": self.ayrinti,
                  "sure_s": None if self.sure_s is None else round(self.sure_s, 3)})
        return d


# ── Yerel ag ipucu ────────────────────────────────────────────────────────────
def yerel_yol(host, saat=time.monotonic):
    """`host`a giden yerel IP (paket GONDERMEZ) ya da None.

    UDP soketini `connect` etmek yalniz yonlendirme tablosuna bakar. Donen adres
    hedefle ayni /24'te ise donanim DOGRUDAN bagli demektir; bu adaylar one alinir.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, 9))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def ayni_ag(host):
    """`host` ile PC ayni /24'te mi (kaba ama tasinabilir yakinlik olcusu)."""
    yerel = yerel_yol(host)
    if not yerel:
        return False
    return yerel.rsplit(".", 1)[0] == str(host).rsplit(".", 1)[0]


# ── Aday uretimi ──────────────────────────────────────────────────────────────
def cihaz_adaylari(listele=None):
    """Yerel yakalama karti / UVC adaylari. VARSAYILAN OLARAK KULLANILMAZ (kural 4)."""
    adaylar = []
    if listele is None:
        def listele():
            try:
                return sorted(p for p in os.listdir("/dev") if p.startswith("video"))
            except OSError:
                return []
    if os.name == "nt":
        for i in range(4):
            adaylar.append(Aday("yakalama-%d" % i, str(i), TUR_CIHAZ, 30,
                                "Windows yakalama karti indeksi %d" % i))
        return adaylar
    for ad in listele():
        yol = "/dev/" + ad
        adaylar.append(Aday(ad, yol, TUR_CIHAZ, 30,
                            "yerel V4L2 aygiti (yakalama karti YA DA PC web kamerasi)"))
    return adaylar


def siyi_adaylari(oncelik_temel=10):
    """SIYI yer birimi adaylari: adres x RTSP yolu, sonra FPV UDP ucu."""
    adaylar = []
    for i, ip in enumerate(SIYI_KAMERA_ADRESLERI):
        yakin = ayni_ag(ip)
        for j, yol in enumerate(SIYI_RTSP_YOLLARI):
            adaylar.append(Aday(
                "siyi-%s-%s" % (ip.rsplit(".", 1)[1], yol.replace("=", "")),
                "rtsp://%s:%d/%s" % (ip, SIYI_RTSP_PORT, yol),
                TUR_RTSP,
                oncelik_temel + (0 if yakin else 20) + i * 2 + (0 if j == 0 else 1),
                "SIYI yer birimi RTSP%s" % (" (ag dogrudan bagli)" if yakin else ""),
                host=ip, port=SIYI_RTSP_PORT))
    for ip in SIYI_KAMERA_ADRESLERI[:1]:
        adaylar.append(Aday(
            "siyi-fpv-udp", "udp://%s:%d" % (ip, SIYI_FPV_UDP_PORT), TUR_UDP,
            oncelik_temel + 40, "SIYI FPV UDP ucu (yalniz bazi surumler)",
            host=ip, port=SIYI_FPV_UDP_PORT))
    return adaylar


def kumanda_adaylari(oncelik_temel=25):
    """Kumanda USB/tethering ile PC'ye takildiginda gorulen adresler."""
    adaylar = []
    for ip in KUMANDA_TETHER_ADRESLERI:
        yakin = ayni_ag(ip)
        adaylar.append(Aday(
            "kumanda-%s" % ip.rsplit(".", 1)[1],
            "rtsp://%s:%d/%s" % (ip, SIYI_RTSP_PORT, SIYI_RTSP_YOLLARI[0]),
            TUR_RTSP, oncelik_temel + (0 if yakin else 20),
            "kumanda USB/tethering agi%s" % (" (bagli)" if yakin else ""),
            host=ip, port=SIYI_RTSP_PORT))
    return adaylar


def jetson_adaylari(jetson_ip, oncelik_temel=40, kesif_ip=None):
    """Jetson'in kendi HTTP koprusu — video telsizi YOKKEN (kablo/LAN) yedek yol.

    `kesif_ip`: ONARIM-03b eslesme duyurusundan OGRENILEN adres. Internet/router
    yokken (dogrudan Ethernet, link-local 169.254.x.x) Jetson'in IP'si onceden
    bilinemez; kesif onu zaten ogrendigi icin video da ayni adresten aranir ve
    bu aday elle verilenden sonra EN ONCE denenir.
    """
    adaylar = []
    ipler = []
    for ip in (kesif_ip, jetson_ip):
        if ip and ip not in ipler:
            ipler.append(ip)
    for i, ip in enumerate(ipler):
        kesifle = (kesif_ip is not None and ip == kesif_ip)
        for j, port in enumerate(JETSON_HTTP_PORTLARI):
            adaylar.append(Aday(
                "jetson-%s-%d" % (ip.rsplit(".", 1)[1], port),
                "http://%s:%d/" % (ip, port), TUR_HTTP,
                (KESIF_ONCELIGI if kesifle else oncelik_temel + i * 4) + j,
                "Jetson kamera koprusu (%s)%s" % (
                    "isaretli kare" if port == 8081 else "ham kamera",
                    " — adres KESIFTEN" if kesifle else ""),
                host=ip, port=port))
    return adaylar


def _elle_aday(url, oncelik=0):
    tur = TUR_HTTP
    if url.startswith("rtsp://"):
        tur = TUR_RTSP
    elif url.startswith("udp://"):
        tur = TUR_UDP
    elif "://" not in url:
        tur = TUR_CIHAZ
    host = port = None
    if "://" in url:
        yetki = url.split("://", 1)[1].split("/", 1)[0]
        if ":" in yetki:
            host, _, p = yetki.partition(":")
            try:
                port = int(p)
            except ValueError:
                port = None
        else:
            host = yetki
    return tur, host, port


def adaylari_uret(elle=None, jetson_ip=None, hatirlanan=None, cihaz_da=False,
                  cihaz_listele=None, kesif_ip=None):
    """Denenecek adaylari oncelik sirasinda uret (ilk eleman once denenir).

    Sira: elle verilen > son basarili (onbellek) > SIYI/kumanda ag adaylari >
    Jetson koprusu > (istenirse) yerel yakalama karti.
    """
    adaylar = []
    if elle:
        tur, host, port = _elle_aday(elle)
        adaylar.append(Aday("elle", elle, tur, 0, "operatorun verdigi kaynak",
                            host=host, port=port))
    if hatirlanan and hatirlanan != elle:
        tur, host, port = _elle_aday(hatirlanan)
        adaylar.append(Aday("hatirlanan", hatirlanan, tur, 1,
                            "son basarili kaynak (onbellek)", host=host, port=port))
    adaylar.extend(siyi_adaylari())
    adaylar.extend(kumanda_adaylari())
    adaylar.extend(jetson_adaylari(jetson_ip, kesif_ip=kesif_ip))
    if cihaz_da:
        adaylar.extend(cihaz_adaylari(cihaz_listele))
    gorulen, benzersiz = set(), []
    for a in adaylar:
        if a.url in gorulen:
            continue
        gorulen.add(a.url)
        benzersiz.append(a)
    benzersiz.sort(key=lambda a: a.oncelik)
    return benzersiz


# ── Dogrulama ─────────────────────────────────────────────────────────────────
def tcp_dene(host, port, zaman_asimi_s=VARSAYILAN_TCP_ZAMAN_ASIMI_S):
    """TCP baglanti kurulabiliyor mu (hizli eleme). Akis KANITI DEGILDIR."""
    try:
        s = socket.create_connection((host, int(port)), timeout=zaman_asimi_s)
    except OSError:
        return False
    s.close()
    return True


def ffprobe_yolu():
    return shutil.which("ffprobe")


def akis_dogrula_ffprobe(url, zaman_asimi_s=VARSAYILAN_AKIS_ZAMAN_ASIMI_S,
                         calistir=None):
    """ffprobe ile ilk video akisini coz. -> (basarili, ayrinti_sozlugu)."""
    arac = ffprobe_yolu()
    if not arac:
        return None, {"sebep": "ffprobe yok"}
    komut = [arac, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,avg_frame_rate",
             "-of", "json"]
    if url.startswith("rtsp://"):
        komut += ["-rtsp_transport", "tcp"]
    komut.append(url)
    calistir = calistir or _calistir
    try:
        kod, cikti, hata = calistir(komut, zaman_asimi_s)
    except Exception as e:                                  # pragma: no cover
        return False, {"sebep": "ffprobe calismadi: %s" % e}
    if kod != 0:
        return False, {"sebep": (hata or "").strip().splitlines()[-1] if hata else
                       "ffprobe kod %s" % kod}
    try:
        veri = json.loads(cikti or "{}")
        akis = (veri.get("streams") or [None])[0]
    except (ValueError, IndexError):
        akis = None
    if not akis:
        return False, {"sebep": "video akisi yok"}
    return True, {"codec": akis.get("codec_name"),
                  "genislik": akis.get("width"), "yukseklik": akis.get("height"),
                  "fps": akis.get("avg_frame_rate"), "yontem": "ffprobe"}


def _calistir(komut, zaman_asimi_s):
    p = subprocess.run(komut, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=zaman_asimi_s + 1)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def akis_dogrula_cv2(url, zaman_asimi_s=VARSAYILAN_AKIS_ZAMAN_ASIMI_S):
    """ffprobe yoksa OpenCV ile tek kare oku (yavas; yalniz yedek yol)."""
    try:
        import cv2
    except ImportError:
        return None, {"sebep": "OpenCV yok"}
    if url.startswith("rtsp://"):
        os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
    try:
        kaynak = int(url) if url.isdigit() else url
    except (AttributeError, ValueError):
        kaynak = url
    cap = cv2.VideoCapture(kaynak)
    try:
        if not cap.isOpened():
            return False, {"sebep": "VideoCapture acilmadi"}
        bas = time.monotonic()
        while time.monotonic() - bas < zaman_asimi_s:
            ok, kare = cap.read()
            if ok and kare is not None and getattr(kare, "size", 0):
                return True, {"genislik": int(kare.shape[1]),
                              "yukseklik": int(kare.shape[0]), "yontem": "opencv"}
        return False, {"sebep": "kare gelmedi (%.1f s)" % zaman_asimi_s}
    finally:
        cap.release()


def akis_dogrula(url, zaman_asimi_s=VARSAYILAN_AKIS_ZAMAN_ASIMI_S):
    """Once ffprobe (hizli, surec izolasyonlu), yoksa OpenCV. -> (bool|None, ayrinti)."""
    ok, ayrinti = akis_dogrula_ffprobe(url, zaman_asimi_s)
    if ok is None:
        ok, ayrinti = akis_dogrula_cv2(url, zaman_asimi_s)
    return ok, ayrinti


# ── Tarama ────────────────────────────────────────────────────────────────────
def tara(adaylar, tcp_dene_f=tcp_dene, akis_dogrula_f=akis_dogrula,
         tcp_zaman_asimi_s=VARSAYILAN_TCP_ZAMAN_ASIMI_S,
         akis_zaman_asimi_s=VARSAYILAN_AKIS_ZAMAN_ASIMI_S,
         ilk_bulunanda_dur=True, saat=time.monotonic, log=None):
    """Adaylari sirayla dene. -> Sonuc listesi (adaylarla AYNI sirada).

    Ilk CANLI bulununca kalanlar DURUM_ATLANDI ile isaretlenir (sahada tarama
    suresi onemlidir); `ilk_bulunanda_dur=False` tam envanter cikarir.
    """
    sonuclar, bulundu = [], False
    tcp_onbellek = {}        # (host, port) -> bool: ayni uc birden cok yol icin denenmez
    for aday in adaylar:
        if bulundu and ilk_bulunanda_dur:
            sonuclar.append(Sonuc(aday, DURUM_ATLANDI, "onceki aday CANLI bulundu"))
            continue
        bas = saat()
        if aday.tur != TUR_CIHAZ and aday.host and aday.port and aday.tur != TUR_UDP:
            anahtar = (aday.host, aday.port)
            if anahtar not in tcp_onbellek:
                tcp_onbellek[anahtar] = tcp_dene_f(aday.host, aday.port, tcp_zaman_asimi_s)
            if not tcp_onbellek[anahtar]:
                sonuclar.append(Sonuc(aday, DURUM_PORT_KAPALI,
                                      "TCP %s:%s acilmadi" % (aday.host, aday.port),
                                      sure_s=saat() - bas))
                if log:
                    log("video aday %s: PORT KAPALI" % aday.ad)
                continue
        ok, ayrinti = akis_dogrula_f(aday.dogrulama_url, akis_zaman_asimi_s)
        sure = saat() - bas
        if ok is None:
            sonuclar.append(Sonuc(aday, DURUM_ARAC_YOK,
                                  ayrinti.get("sebep", "dogrulama araci yok"),
                                  ayrinti, sure))
        elif ok:
            sonuclar.append(Sonuc(aday, DURUM_CANLI, "akis cozuldu", ayrinti, sure))
            bulundu = True
            if log:
                log("video kaynagi BULUNDU: %s (%s)" % (aday.url, ayrinti.get("yontem")))
        else:
            sonuclar.append(Sonuc(aday, DURUM_AKIS_YOK,
                                  ayrinti.get("sebep", "akis cozulemedi"), ayrinti, sure))
    return sonuclar


def sec(sonuclar):
    """Ilk CANLI sonucu dondur, yoksa None."""
    for s in sonuclar:
        if s.canli:
            return s
    return None


def kesfet(elle=None, jetson_ip=None, onbellek=VARSAYILAN_ONBELLEK, cihaz_da=False,
           kesif_ip=None, **tara_ayar):
    """Aday uret + tara + sec + hatirla. -> (Sonuc|None, [Sonuc])."""
    hatirlanan = hatirlanan_oku(onbellek) if onbellek else None
    adaylar = adaylari_uret(elle=elle, jetson_ip=jetson_ip, hatirlanan=hatirlanan,
                            cihaz_da=cihaz_da, kesif_ip=kesif_ip)
    sonuclar = tara(adaylar, **tara_ayar)
    secilen = sec(sonuclar)
    if secilen is not None and onbellek:
        hatirla(onbellek, secilen.aday.url)
    return secilen, sonuclar


# ── Onbellek ──────────────────────────────────────────────────────────────────
def hatirlanan_oku(yol=VARSAYILAN_ONBELLEK):
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("url") or None
    except (OSError, ValueError):
        return None


def hatirla(yol, url):
    """Son basarili kaynagi yaz (bir sonraki acilista ILK denenir)."""
    try:
        p = Path(yol)
        p.parent.mkdir(parents=True, exist_ok=True)
        gecici = str(p) + ".tmp"
        with open(gecici, "w", encoding="utf-8") as f:
            json.dump({"url": url, "t": time.time()}, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(gecici, str(p))
        return True
    except OSError:
        return False


# ── YKS'ye baglama ────────────────────────────────────────────────────────────
def kopru_gerekli(aday):
    """YKS dogrudan okuyabiliyor mu? HTTP koprusu disindaki her sey koprulenir."""
    return aday.tur != TUR_HTTP


def kopru_komutu(aday, port=VARSAYILAN_KOPRU_PORT, yorumlayici=None, kok=None):
    """RTSP/UDP/cihaz kaynagini YKS'nin okudugu MJPEG'e ceviren komut satiri."""
    yorumlayici = yorumlayici or sys.executable
    kok = Path(kok) if kok else Path(__file__).resolve().parents[1]
    return [yorumlayici, str(kok / KOPRU_BETIGI), "--kaynak", aday.url,
            "--port", str(int(port))]


def yks_kamera_url(aday, port=VARSAYILAN_KOPRU_PORT, host="127.0.0.1"):
    """`yks_gui --kamera-url` icin kok URL (kopru gerekiyorsa yerel kopru kokudur)."""
    if not kopru_gerekli(aday):
        return aday.url.rstrip("/") + "/"
    return "http://%s:%d/" % (host, int(port))


# ── CLI ───────────────────────────────────────────────────────────────────────
def _tablo(sonuclar):
    satirlar = ["%-22s %-46s %-12s %s" % ("ADAY", "URL", "DURUM", "SEBEP/AYRINTI")]
    for s in sonuclar:
        ek = s.sebep
        if s.canli:
            a = s.ayrinti
            ek = "%sx%s %s (%s)" % (a.get("genislik"), a.get("yukseklik"),
                                    a.get("codec") or "", a.get("yontem"))
        satirlar.append("%-22s %-46s %-12s %s" % (s.aday.ad, s.aday.url[:46], s.durum, ek))
    return "\n".join(satirlar)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Video telemetri kaynagini tara ve bul (ONARIM-19). "
                    "Koordinat/karar hattina DOKUNMAZ.")
    ap.add_argument("--url", default=os.environ.get("NAVITAS_VIDEO_URL"),
                    help="bilinen kaynak; verilirse ILK denenir")
    ap.add_argument("--jetson", default=os.environ.get("NAVITAS_JETSON_IP"),
                    help="Jetson IP (kendi HTTP koprusu yedek yol olarak denensin)")
    ap.add_argument("--kesif-ip", default=None,
                    help="ONARIM-03b eslesme duyurusundan ogrenilen Jetson adresi "
                         "(link-local/dogrudan kablo: IP onceden bilinmez)")
    ap.add_argument("--cihaz-da", action="store_true",
                    help="yerel /dev/video* aygitlarini da dene (DIKKAT: PC web kamerasi da bulunur)")
    ap.add_argument("--tam", action="store_true", help="ilk bulunanda durma, tam envanter")
    ap.add_argument("--onbellek", default=VARSAYILAN_ONBELLEK)
    ap.add_argument("--onbellek-yok", action="store_true")
    ap.add_argument("--tcp-zaman-asimi", type=float, default=VARSAYILAN_TCP_ZAMAN_ASIMI_S)
    ap.add_argument("--akis-zaman-asimi", type=float, default=VARSAYILAN_AKIS_ZAMAN_ASIMI_S)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--liste", action="store_true", help="hicbir sey deneme, adaylari yaz")
    a = ap.parse_args(argv)

    onbellek = None if a.onbellek_yok else a.onbellek
    if a.liste:
        adaylar = adaylari_uret(elle=a.url, jetson_ip=a.jetson,
                                hatirlanan=hatirlanan_oku(onbellek) if onbellek else None,
                                cihaz_da=a.cihaz_da, kesif_ip=a.kesif_ip)
        if a.json:
            print(json.dumps([x.sozluk() for x in adaylar], ensure_ascii=False, indent=2))
        else:
            for x in adaylar:
                print("%-22s %-46s %-6s %s" % (x.ad, x.url, x.oncelik, x.aciklama))
        return 0

    secilen, sonuclar = kesfet(
        elle=a.url, jetson_ip=a.jetson, onbellek=onbellek, cihaz_da=a.cihaz_da,
        kesif_ip=a.kesif_ip,
        tcp_zaman_asimi_s=a.tcp_zaman_asimi, akis_zaman_asimi_s=a.akis_zaman_asimi,
        ilk_bulunanda_dur=not a.tam)
    if a.json:
        print(json.dumps({
            "secilen": secilen.sozluk() if secilen else None,
            "yks_kamera_url": yks_kamera_url(secilen.aday) if secilen else None,
            "kopru_komutu": (kopru_komutu(secilen.aday) if secilen and
                             kopru_gerekli(secilen.aday) else None),
            "sonuclar": [s.sozluk() for s in sonuclar],
        }, ensure_ascii=False, indent=2))
        return 0 if secilen else 1
    print(_tablo(sonuclar))
    if not secilen:
        denendi = sum(1 for s in sonuclar if s.durum != DURUM_ATLANDI)
        print("\nVIDEO KAYNAGI BULUNAMADI (%d aday denendi). Karar/koordinat hatti "
              "ETKILENMEZ." % denendi)
        if not ffprobe_yolu():
            print("UYARI: ffprobe kurulu degil; dogrulama OpenCV'ye dustu (yavas).")
        return 1
    print("\nSECILEN: %s (%s)" % (secilen.aday.url, secilen.aday.aciklama))
    if kopru_gerekli(secilen.aday):
        print("KOPRU  : " + " ".join(kopru_komutu(secilen.aday)))
    print("YKS    : --kamera-url %s" % yks_kamera_url(secilen.aday))
    return 0


if __name__ == "__main__":
    sys.exit(main())
