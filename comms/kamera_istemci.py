"""NEDEN: YKİ hakem ekranı, İHA kamerasını SiK hattına yüklemeden ayrı LAN
üzerinden okuyabilmelidir.

Bu modül GUI'den bağımsız, küçük bir canlı-kamera istemcisidir. Jetson'daki
``scripts/kamera_koprusu.py`` uçlarını kullanır:

* ``/kare.jpg`` sınırlı hızda çekilir; sürekli MJPEG bağlantısının YKİ'ye
  gereksiz bant yükü bindirmesi önlenir.
* ``/durum`` kaynak sağlığını bildirir.
* Ağ I/O'su yalnız arka plan iş parçacığındadır. GUI ana döngüsü asla ağda
  beklemez.
* Yalnız en son DEĞİŞEN kare tutulur. Aynı ``X-Kare-Sira``/JPEG tekrar tekrar
  gelirse tazelik yenilenmez; donmuş görüntü canlı sayılmaz.
* Bayat ya da kaynak-kapalı kare ``snapshot()`` sonucunda geri verilmez. Son eski
  görüntüyü ekranda canlıymış gibi dondurmak yasaktır.

Video/telemetri ayrımı bilinçlidir: bu modül ``comms.link`` veya SiK ile
konuşmaz. Rota, ACK ve ARM/DISARM otoritesi mevcut NAVITAS protokolüdür; bu
istemci yalnız RAW hakem görüntüsünü taşır.
"""
import http.client
import json
import math
import threading
import time
import urllib.error
import urllib.request
import zlib
from urllib.parse import urlsplit, urlunsplit

import cv2
import numpy as np


KARE_YOLU = "/kare.jpg"
DURUM_YOLU = "/durum"

# 5 Hz, Q80 720p'de köprünün ölçüm notundaki 60--120 KiB/kareye göre yaklaşık
# 2,4--4,8 Mbit/s'tir. Bu bir SiK ayarı DEĞİLDİR; ayrı Wi-Fi/LAN önizlemesidir.
VARSAYILAN_KARE_ARALIGI_S = 0.2
# Sağlık JSON'u görüntüden daha seyrek okunur; kaynak kapalı durumu yine görünür.
VARSAYILAN_DURUM_ARALIGI_S = 1.0
# LAN isteği bu sürede dönmezse GUI bekletilmez; sonraki turda yeniden denenir.
VARSAYILAN_ISTEK_ZAMAN_ASIMI_S = 1.0
# İki kare aralığının çok üstündeki görüntü canlı sayılmaz. Değer çağıran
# tarafından saha ölçümüne göre daraltılabilir; tek yerde tutulur.
VARSAYILAN_KARE_TAZELIK_S = 2.0
# /durum geçici olarak düşse de taze JPEG gösterilebilir; sağlık bilinmiyor diye
# ayrıca işaretlenir. Eski ``kaynak_acik=False`` sonsuza dek hüküm sürmez.
VARSAYILAN_DURUM_TAZELIK_S = 3.0
# Hatalı/hasım HTTP sunucusu belleği sınırsız büyütemez.
AZAMI_JPEG_BAYT = 5 * 1024 * 1024
AZAMI_DURUM_BAYT = 64 * 1024

DURUM_CANLI = "CANLI"
DURUM_CANLI_SAGLIK_BILINMIYOR = "CANLI_SAGLIK_BILINMIYOR"
DURUM_KAYNAK_KAPALI = "KAYNAK_KAPALI"
DURUM_KARE_BAYAT = "KARE_BAYAT"
DURUM_BAGLANAMADI = "BAGLANAMADI"


class KameraURLHatasi(ValueError):
    """Kamera ucu açık ve güvenli biçimde çözülemedi."""


def _url_dogrula(url, beklenen_yol, kok_izinli=False):
    if not isinstance(url, str) or not url.strip():
        raise KameraURLHatasi("kamera URL'si boş olamaz")
    metin = url.strip()
    try:
        parca = urlsplit(metin)
        port = parca.port
    except ValueError as exc:
        raise KameraURLHatasi("kamera URL portu geçersiz: {}".format(exc))
    if parca.scheme.lower() != "http":
        raise KameraURLHatasi("kamera URL yalnız http olabilir (ayrı, kapalı LAN)")
    if not parca.hostname:
        raise KameraURLHatasi("kamera URL host içermeli")
    if parca.username is not None or parca.password is not None:
        raise KameraURLHatasi("kamera URL kullanıcı/parola taşıyamaz")
    if parca.hostname in ("0.0.0.0", "::"):
        raise KameraURLHatasi("0.0.0.0/:: dinleme adresidir, istemci hedefi olamaz")
    yol = parca.path
    if kok_izinli and yol in ("", "/"):
        yol = beklenen_yol
    elif yol != beklenen_yol:
        raise KameraURLHatasi(
            "kamera URL yolu {}{} olmalı: {!r}".format(
                "kök veya " if kok_izinli else "", beklenen_yol, parca.path))
    if parca.query or parca.fragment:
        raise KameraURLHatasi("kamera URL sorgu veya parça taşıyamaz")
    if port is not None and not (1 <= port <= 65535):
        raise KameraURLHatasi("kamera URL portu 1..65535 olmalı")
    # urlsplit şemayı ayırdıktan sonra netloc güvenlidir; yol/sorgu açıkça
    # yeniden kurulur. Böylece çağıran metindeki gizli fragment taşınmaz.
    return urlunsplit(("http", parca.netloc, yol, "", ""))


def kamera_uclari(kare_url, durum_url=None):
    """Açık beyanı doğrula ve ``(kare_url, durum_url)`` döndür.

    Durum ucu verilmezse aynı şema/host/porttan türetilir. Verilirse başka bir
    makineye yönelmesine izin verilmez; görüntü ile sağlık aynı köprüye aittir.
    """
    # YKS CLI'si operatöre köprü KÖKÜNÜ beyan ettirir; eski/doğrudan çağıranlar
    # tam /kare.jpg ucunu verebilir. İkisi de tek kanonik kare URL'sine çevrilir.
    kare = _url_dogrula(kare_url, KARE_YOLU, kok_izinli=True)
    k = urlsplit(kare)
    if durum_url is None:
        durum = urlunsplit((k.scheme, k.netloc, DURUM_YOLU, "", ""))
    else:
        durum = _url_dogrula(durum_url, DURUM_YOLU)
        d = urlsplit(durum)
        k_port = k.port if k.port is not None else 80
        d_port = d.port if d.port is not None else 80
        if (k.hostname.lower(), k_port) != (d.hostname.lower(), d_port):
            raise KameraURLHatasi("kare ve durum uçları aynı host/portta olmalı")
    return kare, durum


def _dogrudan_url_ac(istek, timeout):
    """Yerel kamera trafiğini ortam HTTP proxy'sine göndermeden aç."""
    acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return acici.open(istek, timeout=timeout)


class KameraIstemci:
    """Jetson ``/kare.jpg`` + ``/durum`` uçlarının non-blocking okuyucusu.

    ``baslat()`` hemen döner. ``snapshot()`` kilit altında tutarlı bir sözlük
    verir. Bağlayıcı GUI yüzeyi en az şu alanları taşır:
    ``surum, jpeg, durum, hata, kare_yasi_s, kaynak``. ``jpeg`` değişmez
    ``bytes`` nesnesidir; 503/timeout/kaynak-kapalı/bayat durumda ``None`` olur.
    """

    def __init__(self, kare_url, durum_url=None, *,
                 kare_araligi_s=VARSAYILAN_KARE_ARALIGI_S,
                 durum_araligi_s=VARSAYILAN_DURUM_ARALIGI_S,
                 istek_zaman_asimi_s=VARSAYILAN_ISTEK_ZAMAN_ASIMI_S,
                 kare_tazelik_s=VARSAYILAN_KARE_TAZELIK_S,
                 durum_tazelik_s=VARSAYILAN_DURUM_TAZELIK_S,
                 url_ac=_dogrudan_url_ac, saat=time.monotonic):
        self.kare_url, self.durum_url = kamera_uclari(kare_url, durum_url)
        degerler = {
            "kare_araligi_s": kare_araligi_s,
            "durum_araligi_s": durum_araligi_s,
            "istek_zaman_asimi_s": istek_zaman_asimi_s,
            "kare_tazelik_s": kare_tazelik_s,
            "durum_tazelik_s": durum_tazelik_s,
        }
        for ad, deger in degerler.items():
            try:
                sayi = float(deger)
            except (TypeError, ValueError):
                raise ValueError("{} sayısal olmalı".format(ad))
            if not math.isfinite(sayi) or sayi <= 0:
                raise ValueError("{} pozitif ve sonlu olmalı".format(ad))
            setattr(self, ad, sayi)
        if not callable(url_ac) or not callable(saat):
            raise TypeError("url_ac ve saat çağrılabilir olmalı")
        self._url_ac = url_ac
        self._saat = saat
        self._kilit = threading.Lock()
        self._dur = threading.Event()
        self._iplik = None

        self._jpeg = None
        self._kare = None
        self._kare_token = None
        self._kare_sira = None
        self._son_kare_t = None
        self._kare_gecerli = False
        self._surum = 0
        self._uzak_durum = None
        self._son_durum_t = None
        self._kare_hata = "kamera henüz bağlanmadı"
        self._durum_hata = "kamera durumu henüz alınmadı"
        self._kare_istek = 0
        self._durum_istek = 0
        self._degisen_kare = 0
        self._alinan_bayt = 0

    def baslat(self):
        """Worker'ı başlat; zaten çalışıyorsa ``False``, yeniyse ``True``."""
        with self._kilit:
            if self._iplik is not None and self._iplik.is_alive():
                return False
            self._dur.clear()
            self._iplik = threading.Thread(
                target=self._dongu, name="yki-canli-kamera", daemon=True)
            self._iplik.start()
            return True

    def durdur(self, zaman_asimi_s=None):
        """Worker'ı durdur; I/O timeout'u kadar bekleyip sonuç durumunu döndür."""
        self._dur.set()
        with self._kilit:
            iplik = self._iplik
        if iplik is None:
            return True
        if zaman_asimi_s is None:
            zaman_asimi_s = self.istek_zaman_asimi_s + 1.0
        iplik.join(max(0.0, float(zaman_asimi_s)))
        return not iplik.is_alive()

    def calisiyor(self):
        with self._kilit:
            return self._iplik is not None and self._iplik.is_alive()

    def __enter__(self):
        self.baslat()
        return self

    def __exit__(self, _tur, _deger, _iz):
        self.durdur()

    def snapshot(self):
        """Thread-safe son durum; bayat/kapalı/503'te ``jpeg`` daima None."""
        simdi = self._saat()
        with self._kilit:
            jpeg = self._jpeg
            kare = self._kare
            kare_yasi = (None if self._son_kare_t is None
                          else max(0.0, simdi - self._son_kare_t))
            durum_yasi = (None if self._son_durum_t is None
                           else max(0.0, simdi - self._son_durum_t))
            uzak = dict(self._uzak_durum) if isinstance(self._uzak_durum, dict) else None
            durum_taze = durum_yasi is not None and durum_yasi <= self.durum_tazelik_s
            kaynak_kapali = bool(
                durum_taze and uzak is not None and uzak.get("kaynak_acik") is False)
            kare_taze = (self._kare_gecerli and jpeg is not None and
                          kare is not None and kare_yasi is not None
                          and kare_yasi <= self.kare_tazelik_s)

            if kaynak_kapali:
                saglik = DURUM_KAYNAK_KAPALI
                gorunen_jpeg = None
                gorunen = None
                hata = uzak.get("son_hata") or "Jetson kamera kaynağı kapalı"
            elif not kare_taze:
                gorunen_jpeg = None
                gorunen = None
                if self._son_kare_t is None:
                    saglik = DURUM_BAGLANAMADI
                    hata = self._kare_hata or "kamera karesi alınamadı"
                else:
                    saglik = DURUM_KARE_BAYAT
                    hata = self._kare_hata or "kamera karesi bayat"
            elif not durum_taze:
                saglik = DURUM_CANLI_SAGLIK_BILINMIYOR
                gorunen_jpeg = jpeg
                gorunen = kare
                hata = self._durum_hata or "kamera sağlık bilgisi bayat"
            else:
                saglik = DURUM_CANLI
                gorunen_jpeg = jpeg
                gorunen = kare
                hata = None

            return {
                "surum": self._surum,
                "jpeg": gorunen_jpeg,
                "durum": saglik,
                "hata": hata,
                "kaynak": self.kare_url,
                "saglik": saglik,
                "canli": gorunen is not None,
                "kare": gorunen,
                "kare_sira": self._kare_sira,
                "kare_yasi_s": kare_yasi,
                "durum_yasi_s": durum_yasi,
                "son_hata": hata,
                "uzak_durum": uzak,
                "kare_url": self.kare_url,
                "durum_url": self.durum_url,
                "kare_istek": self._kare_istek,
                "durum_istek": self._durum_istek,
                "degisen_kare": self._degisen_kare,
                "alinan_bayt": self._alinan_bayt,
                "calisiyor": self._iplik is not None and self._iplik.is_alive(),
            }

    def _yanit_oku(self, url, azami_bayt, beklenen_tur):
        istek = urllib.request.Request(
            url, headers={"User-Agent": "NAVITAS-YKI-Kamera/1", "Cache-Control": "no-cache"})
        with self._url_ac(istek, timeout=self.istek_zaman_asimi_s) as yanit:
            kod = getattr(yanit, "status", None)
            if kod is None:
                kod = yanit.getcode()
            if kod != 200:
                raise OSError("HTTP {}".format(kod))
            tur = (yanit.headers.get("Content-Type") or "").lower()
            if not tur.startswith(beklenen_tur):
                raise ValueError("beklenmeyen Content-Type: {!r}".format(tur))
            veri = yanit.read(azami_bayt + 1)
            if len(veri) > azami_bayt:
                raise ValueError("yanıt boyutu sınırı aştı: {} bayt".format(azami_bayt))
            return veri, yanit.headers

    @staticmethod
    def _hata_metni(exc):
        if isinstance(exc, urllib.error.HTTPError):
            return "HTTP {} {}".format(exc.code, exc.reason)
        if isinstance(exc, urllib.error.URLError):
            return "bağlantı hatası: {}".format(exc.reason)
        return "{}: {}".format(type(exc).__name__, exc)

    def _kare_dene(self):
        try:
            veri, baslik = self._yanit_oku(self.kare_url, AZAMI_JPEG_BAYT, "image/jpeg")
            dizi = np.frombuffer(veri, dtype=np.uint8)
            kare = cv2.imdecode(dizi, cv2.IMREAD_COLOR)
            if kare is None or kare.ndim != 3 or kare.shape[2] != 3:
                raise ValueError("JPEG çözülemedi veya BGR üç kanallı değil")
            sira_metin = baslik.get("X-Kare-Sira")
            try:
                sira = int(sira_metin) if sira_metin is not None else None
            except ValueError:
                raise ValueError("X-Kare-Sira tam sayı değil: {!r}".format(sira_metin))
            token = (sira, len(veri), zlib.crc32(veri) & 0xffffffff)
            kare.setflags(write=False)
            simdi = self._saat()
            with self._kilit:
                self._kare_istek += 1
                self._alinan_bayt += len(veri)
                self._kare_hata = None
                self._kare_gecerli = True
                if token != self._kare_token:
                    self._jpeg = bytes(veri)
                    self._kare = kare
                    self._kare_token = token
                    self._kare_sira = sira
                    self._son_kare_t = simdi
                    self._degisen_kare += 1
                    self._surum += 1
        except (OSError, ValueError, TypeError, cv2.error, http.client.HTTPException,
                urllib.error.URLError) as exc:
            with self._kilit:
                self._kare_istek += 1
                self._kare_gecerli = False
                self._kare_hata = self._hata_metni(exc)

    def _durum_dene(self):
        try:
            veri, _baslik = self._yanit_oku(
                self.durum_url, AZAMI_DURUM_BAYT, "application/json")
            durum = json.loads(veri.decode("utf-8"))
            if not isinstance(durum, dict):
                raise ValueError("durum JSON nesne olmalı")
            if not isinstance(durum.get("kaynak_acik"), bool):
                raise ValueError("durum kaynak_acik bool alanı taşımıyor")
            with self._kilit:
                self._durum_istek += 1
                self._uzak_durum = durum
                self._son_durum_t = self._saat()
                self._durum_hata = None
        except (OSError, ValueError, TypeError, UnicodeError, json.JSONDecodeError,
                http.client.HTTPException,
                urllib.error.URLError) as exc:
            with self._kilit:
                self._durum_istek += 1
                self._durum_hata = self._hata_metni(exc)

    def _dongu(self):
        sonraki_durum = 0.0
        while not self._dur.is_set():
            baslangic = self._saat()
            self._kare_dene()
            simdi = self._saat()
            if simdi >= sonraki_durum:
                self._durum_dene()
                sonraki_durum = self._saat() + self.durum_araligi_s
            gecen = self._saat() - baslangic
            self._dur.wait(max(0.0, self.kare_araligi_s - gecen))
