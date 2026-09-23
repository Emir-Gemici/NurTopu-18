"""NEDEN: FDA kalkis/intikal plani ile algi izni ayni dogrulanmis hedefe baglanir."""

import hashlib
import json
import math
import os
from pathlib import Path
import sys
import threading
import time
import uuid

KOD_DIZINI = Path(__file__).resolve().parent.parent / "codes"
if KOD_DIZINI.is_dir() and str(KOD_DIZINI) not in sys.path:
    sys.path.insert(0, str(KOD_DIZINI))

from karar_sozlesmesi import DUNYA_YARICAPI_M


CMD_FDA_HAZIRLA = "FDA_HAZIRLA"
VARSAYILAN_IRTIFA_M = 30.0
VARSAYILAN_ILERI_M = 40.0
VARSAYILAN_DRONE_TEST_IRTIFA_M = 20.0
VARSAYILAN_DRONE_TEST_ILERI_M = 30.0
DRONE_TEST_ARAMA_KARE_M = 6.0
GOREV_TEKRAR_ARALIGI_S = 1.0
GOREV_TEKRAR_SAYISI = 45
GOREV_YUKLEME_TAVANI_S = 30.0
HAZIRLIK_TAZELIK_S = 3.0
KALKIS_KONUM_TOLERANSI_M = 5.0
KALKIS_YON_TOLERANSI_DERECE = 5.0
VARIS_YATAY_TOLERANSI_M = 1.5
VARIS_IRTIFA_TOLERANSI_M = 1.0
VARIS_HIZ_TAVANI_MS = 0.5
VARIS_KARARLILIK_S = 2.0
PLAN_SURUMU = 1
COPTER_AUTO_MODU = 3


def sonlu_sayi(deger, ad):
    if isinstance(deger, bool) or not isinstance(deger, (int, float)):
        raise ValueError(f"{ad} sonlu sayi olmali")
    deger = float(deger)
    if not math.isfinite(deger):
        raise ValueError(f"{ad} sonlu sayi olmali")
    return deger


def konum_dogrula(enlem, boylam):
    enlem = sonlu_sayi(enlem, "enlem")
    boylam = sonlu_sayi(boylam, "boylam")
    if not -85.0 <= enlem <= 85.0 or not -180.0 <= boylam <= 180.0:
        raise ValueError("Kutup disi gecerli konum gerekli")
    return enlem, boylam


def mesafe_m(baslangic, hedef):
    bas_enlem, bas_boylam = konum_dogrula(*baslangic)
    son_enlem, son_boylam = konum_dogrula(*hedef)
    fark_enlem = math.radians(son_enlem - bas_enlem)
    fark_boylam = math.radians((son_boylam - bas_boylam + 180.0) % 360.0 - 180.0)
    kuzey = fark_enlem * DUNYA_YARICAPI_M
    dogu = (fark_boylam * DUNYA_YARICAPI_M
            * math.cos(math.radians((bas_enlem + son_enlem) / 2.0)))
    return math.hypot(kuzey, dogu)


def ayar_dogrula(ayar):
    if not isinstance(ayar, dict):
        raise ValueError("Gorev ayari sozluk olmali")
    sonuc = dict(ayar)
    kimlik = sonuc.get("id")
    if not isinstance(kimlik, str) or len(kimlik) != 32:
        raise ValueError("Gorev kimligi 32 haneli hex olmali")
    try:
        int(kimlik, 16)
    except ValueError as exc:
        raise ValueError("Gorev kimligi hex olmali") from exc
    sonuc["lat"], sonuc["lon"] = konum_dogrula(sonuc.get("lat"), sonuc.get("lon"))
    for ad in ("yukseklik_m", "ileri_m", "yon"):
        sonuc[ad] = sonlu_sayi(sonuc.get(ad), ad)
    if not 0.0 < sonuc["yukseklik_m"] <= 1000.0:
        raise ValueError("Yukseklik 0..1000 m araliginda olmali; canli cit ayrica denetlenir")
    if not 0.0 < sonuc["ileri_m"] <= 1000.0:
        raise ValueError("Ileri mesafe 0..1000 m araliginda olmali; canli cit ayrica denetlenir")
    if not 0.0 <= sonuc["yon"] < 360.0:
        raise ValueError("Burun yonu 0 dahil, 360 haric derece olmali")
    baslangic = sonuc.get("baslangic")
    if baslangic is not None:
        if not isinstance(baslangic, dict):
            raise ValueError("baslangic koordinati sozluk olmali")
        bas_lat, bas_lon = konum_dogrula(
            baslangic.get("lat"), baslangic.get("lon"))
        if abs(bas_lat - sonuc["lat"]) > 1e-7 or abs(bas_lon - sonuc["lon"]) > 1e-7:
            raise ValueError("baslangic koordinati plan konumuyla uyusmuyor")
        sonuc["baslangic"] = {"lat": bas_lat, "lon": bas_lon}
    ika_baslangic = sonuc.get("ika_baslangic")
    if ika_baslangic is not None:
        if not isinstance(ika_baslangic, dict):
            raise ValueError("ika_baslangic koordinati sozluk olmali")
        ika_lat, ika_lon = konum_dogrula(
            ika_baslangic.get("lat"), ika_baslangic.get("lon"))
        sonuc["ika_baslangic"] = {"lat": ika_lat, "lon": ika_lon}
    kare = sonuc.get("arama_kare_m")
    if kare is not None:
        kare = sonlu_sayi(kare, "arama_kare_m")
        if not 0.0 < kare <= 50.0:
            raise ValueError("arama_kare_m 0..50 m araliginda olmali")
        sonuc["arama_kare_m"] = kare
    temel = {ad: sonuc[ad] for ad in
             ("id", "lat", "lon", "yukseklik_m", "ileri_m", "yon")}
    for ad in ("baslangic", "ika_baslangic", "arama_kare_m"):
        if ad in sonuc:
            temel[ad] = sonuc[ad]
    return temel


def hedef_konumu(ayar):
    ayar = ayar_dogrula(ayar)
    enlem = math.radians(ayar["lat"])
    boylam = math.radians(ayar["lon"])
    kerteriz = math.radians(ayar["yon"])
    yay = ayar["ileri_m"] / DUNYA_YARICAPI_M
    hedef_enlem = math.asin(math.sin(enlem) * math.cos(yay)
                           + math.cos(enlem) * math.sin(yay) * math.cos(kerteriz))
    hedef_boylam = boylam + math.atan2(
        math.sin(kerteriz) * math.sin(yay) * math.cos(enlem),
        math.cos(yay) - math.sin(enlem) * math.sin(hedef_enlem))
    return (math.degrees(hedef_enlem),
            (math.degrees(hedef_boylam) + 180.0) % 360.0 - 180.0)


def konum_ofseti(konum, kuzey_m, dogu_m):
    """Bir GPS konumunu yerel kuzey/dogu metre ofsetiyle ilerlet."""
    enlem, boylam = konum_dogrula(*konum)
    kuzey_m = sonlu_sayi(kuzey_m, "kuzey_m")
    dogu_m = sonlu_sayi(dogu_m, "dogu_m")
    yeni_enlem = enlem + math.degrees(kuzey_m / DUNYA_YARICAPI_M)
    cos_enlem = math.cos(math.radians(enlem))
    if abs(cos_enlem) < 1e-9:
        raise ValueError("kutuplara yakin konumda dogu ofseti hesaplanamaz")
    yeni_boylam = boylam + math.degrees(dogu_m / (DUNYA_YARICAPI_M * cos_enlem))
    return konum_dogrula(yeni_enlem, (yeni_boylam + 180.0) % 360.0 - 180.0)


def drone_test_kare_noktalari(ayar):
    """H merkezinin etrafında, burun eksenine bağlı 6 m kare köşelerini üret."""
    ayar = ayar_dogrula(ayar)
    kare = ayar.get("arama_kare_m", DRONE_TEST_ARAMA_KARE_M)
    merkez = hedef_konumu(ayar)
    yari = kare / 2.0
    yaw = math.radians(ayar["yon"])
    noktalar = []
    for ileri, saga in ((yari, yari), (-yari, yari),
                        (-yari, -yari), (yari, -yari), (yari, yari)):
        kuzey = ileri * math.cos(yaw) - saga * math.sin(yaw)
        dogu = ileri * math.sin(yaw) + saga * math.cos(yaw)
        noktalar.append(konum_ofseti(merkez, kuzey, dogu))
    return noktalar


def ayar_ozeti(ayar):
    metin = json.dumps(ayar_dogrula(ayar), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def atomik_json_yaz(yol, veri):
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_name(yol.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with gecici.open("x", encoding="utf-8") as dosya:
            json.dump(veri, dosya, ensure_ascii=False, allow_nan=False)
            dosya.flush()
            os.fsync(dosya.fileno())
        os.replace(gecici, yol)
    finally:
        if gecici.exists():
            gecici.unlink()


def json_oku(yol):
    with Path(yol).open("r", encoding="utf-8") as dosya:
        veri = json.load(dosya)
    if not isinstance(veri, dict):
        raise ValueError("JSON nesnesi gerekli")
    return veri


def hazirlik_yolu(yol):
    return Path(str(yol) + ".algi_hazir.json")


def hazirlik_oku(yol, simdi=None):
    simdi = time.monotonic() if simdi is None else simdi
    veri = json_oku(hazirlik_yolu(yol))
    yas = simdi - sonlu_sayi(veri.get("monotonik"), "hazirlik zamani")
    if (veri.get("v") != PLAN_SURUMU or veri.get("hazir") is not True
            or not isinstance(veri.get("oturum"), str)
            or not 0.0 <= yas <= HAZIRLIK_TAZELIK_S):
        raise ValueError("Algi gorev kapisi hazir degil veya bayat")
    return veri


class AlgiGorevKapisi:
    def __init__(self, yol, telemetri_saglayici, saat=time.monotonic):
        if not callable(telemetri_saglayici):
            raise ValueError("Canli telemetri saglayicisi zorunlu")
        self.yol = Path(yol)
        self.telemetri_saglayici = telemetri_saglayici
        self.saat = saat
        self.oturum = uuid.uuid4().hex
        self.hazir = False
        self.durum = "GOREV_BEKLENIYOR"
        self.plan = None
        self._plan_ozeti = None
        self._yerde_goruldu = False
        self._auto_goruldu = False
        self._tamamlandi = False
        self._varis_baslangici = None
        self._son_hazirlik_yazimi = None
        self._kilit = threading.RLock()

    def etkinlestir(self):
        with self._kilit:
            self.hazir = True
            self._hazirlik_yaz()

    def kapat(self):
        with self._kilit:
            self.hazir = False
            self._hazirlik_yaz()

    def _hazirlik_yaz(self):
        simdi = self.saat()
        atomik_json_yaz(hazirlik_yolu(self.yol), {
            "v": PLAN_SURUMU, "oturum": self.oturum,
            "hazir": self.hazir, "monotonik": simdi})
        self._son_hazirlik_yazimi = simdi

    def _plan_oku(self, telemetri):
        veri = json_oku(self.yol)
        if veri.get("v") != PLAN_SURUMU or veri.get("algi_oturumu") != self.oturum:
            raise ValueError("Gorev bu algi oturumuna ait degil")
        ayar = ayar_dogrula(veri.get("ayar"))
        ozet = ayar_ozeti(ayar)
        if veri.get("ozet") != ozet or veri.get("dogrulandi") is not True:
            raise ValueError("Gorev yukleme ve geri okuma kaniti yok")
        hedef_irtifa = sonlu_sayi(veri.get("hedef_irtifa_m"), "hedef irtifa")
        if hedef_irtifa <= 0:
            raise ValueError("Goreli hedef irtifa pozitif olmali")
        if self._plan_ozeti != ozet:
            if telemetri.get("armed") is not False:
                raise ValueError("Yeni gorev once yerde ve DISARM gorulmeli")
            self.plan = veri
            self._plan_ozeti = ozet
            self._yerde_goruldu = True
            self._auto_goruldu = False
            self._tamamlandi = False
            self._varis_baslangici = None
        self.plan = veri
        return ayar, hedef_irtifa

    def _degerlendir(self, telemetri):
        simdi = self.saat()
        if not self.hazir:
            return "GOREV_KAPISI_HAZIR_DEGIL"
        if not isinstance(telemetri, dict) or telemetri.get("pixhawk_canli") is not True:
            return "TELEMETRI_BEKLENIYOR"
        try:
            ayar, hedef_irtifa = self._plan_oku(telemetri)
        except (OSError, ValueError, TypeError):
            self.plan = None
            return "GOREV_BEKLENIYOR"
        if type(telemetri.get("armed")) is not bool:
            return "TELEMETRI_BEKLENIYOR"
        if telemetri.get("armed") is False:
            if self._auto_goruldu:
                self._tamamlandi = True
            return "RC_AUTO_BEKLENIYOR"
        if self._tamamlandi:
            return "YENI_GOREV_GEREKLI"
        if telemetri.get("mod") != "AUTO":
            return "AUTO_DISI_ALGI_KAPALI"
        if not self._yerde_goruldu:
            return "YER_ONAYI_YOK"
        self._auto_goruldu = True
        try:
            fix = sonlu_sayi(telemetri.get("gps_fix"), "gps_fix")
            konum = konum_dogrula(telemetri.get("lat"), telemetri.get("lon"))
            irtifa = sonlu_sayi(telemetri.get("alt"), "irtifa")
            hiz = sonlu_sayi(telemetri.get("hiz"), "hiz")
        except ValueError:
            return "TELEMETRI_BEKLENIYOR"
        if fix < 3 or hiz < 0:
            return "TELEMETRI_BEKLENIYOR"
        if abs(irtifa - hedef_irtifa) > VARIS_IRTIFA_TOLERANSI_M:
            return "YUKSELME_VEYA_IRTIFA_DUZELTME"
        if mesafe_m(konum, hedef_konumu(ayar)) > VARIS_YATAY_TOLERANSI_M:
            return "HEDEFE_INTIKAL"
        if hiz > VARIS_HIZ_TAVANI_MS:
            return "HEDEFTE_YAVASLAMA"
        if self._varis_baslangici is None:
            self._varis_baslangici = simdi
        if simdi - self._varis_baslangici < VARIS_KARARLILIK_S:
            return "HEDEFTE_KARARLILIK"
        return "ALGI_AKTIF"

    def guncelle(self, telemetri=None):
        with self._kilit:
            simdi = self.saat()
            if self.hazir and (self._son_hazirlik_yazimi is None
                               or simdi - self._son_hazirlik_yazimi >= 1.0):
                self._hazirlik_yaz()
            if telemetri is None:
                try:
                    telemetri = self.telemetri_saglayici()
                except Exception:
                    telemetri = {}
            self.durum = self._degerlendir(telemetri)
            if self.durum not in ("HEDEFTE_KARARLILIK", "ALGI_AKTIF"):
                self._varis_baslangici = None
            return self.durum == "ALGI_AKTIF"

    def telemetri(self):
        with self._kilit:
            try:
                veri = dict(self.telemetri_saglayici() or {})
            except Exception:
                veri = {}
            self.guncelle(veri)
            veri["gorev_hazir"] = self.hazir
            veri["gorev_durum"] = self.durum
            if self.plan is not None:
                veri["gorev_id"] = self.plan["ayar"]["id"]
            return veri
