"""NEDEN: YKS, hakem onayını ve manuel İKA komutunu gerçek haberleşme
hedefine fail-closed biçimde ileterek şartname kilitlerini görünür kılmalıdır.

YKS (Yer Kontrol İstasyonu) — hakem ekranı GUI'si.

Şartname §2.2.3/§6.2: İHA'nın tespit ettiği güzergâh YKS'de CANLI görünmeli,
Alan Hakemi monitörden izleyip onaylamalı. Bu arayüz, yks_monitor.py'nin
terminal sürümünün yerini alan gerçek hakem ekranıdır:

  · gerçek protokol trafiği dinler (OPEN_ROUTE / IHA_LANDED / HEARTBEAT)
  · saha haritasında (50×50 m HTAB) rotayı ve açık yolu çizer
  · İHA/İKA bağlantı canlılığını gösterir (heartbeat yaşı)
  · hakem onayı BUTONLA verilir → ACK ancak o zaman döner
    (yks_monitor.py'deki "otomatik onay" bu ekranda kaldırıldı)

Kullanım:
  python yks_gui.py --ika 127.0.0.1:5006    # 0.0.0.0:5005 dinler (UDP)
  python yks_gui.py --bind 0.0.0.0:5005 --ika 127.0.0.1:5006
  python yks_gui.py --serial COM5            # SiK telsiz (saha)
  python yks_gui.py --serial COM5 --kamera-url http://192.168.4.2:8080
  python yks_gui.py --demo                   # dahili İHA/İKA beslemesiyle tanıtım
  python yks_gui.py --demo --otokaydet 6     # 6 sn sonra pencere SS'i kaydet (rapor)

Sadece stdlib + (SS için) Pillow kullanır; tkinter Python ile gelir.
"""
import argparse
import io
import math
import os
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

from link import UDPLink, SerialLink
from ika_receiver import IkaReceiver
from komut_tekrar import AckliTekrar, ONAYLANDI, VAZGECILDI
from protocol import (ACK_SONUC_KABUL, encode, ack, command, heartbeat, iha_landed,
                      kritik_komut_ack_gecerli_mi,
                      open_route,
                      FrameReader, ROAD_LABEL)

_PROJE_KOKU = Path(__file__).resolve().parents[1]
if str(_PROJE_KOKU / "codes") not in sys.path:
    sys.path.insert(0, str(_PROJE_KOKU / "codes"))
from karar_sozlesmesi import (ARM_DURUM_TAZELIK_S,
                              ARM_TEKRAR_ARALIGI_S,
                              ARM_TEKRAR_UST_SINIRI,
                              DISARM_TEYIT_SURESI_S,
                              IKA_GO_TEKRAR_ARALIGI_S,
                              IKA_GO_TEKRAR_UST_SINIRI,
                              PARASUT_MANUEL_CEZA_PUANI,
                              PARASUT_TEKRAR_ARALIGI_S,
                              PARASUT_TEKRAR_UST_SINIRI,
                              SARTNAME_ASGARI_IRTIFA_M,
                              SARTNAME_FDA_OPERASYON_SURESI_S,
                              SARTNAME_HAZIRLIK_SURESI_S,
                              SARTNAME_IHA_GOREV_SURESI_S,
                              SARTNAME_IHA_UB_KENAR_M,
                              SARTNAME_IKA_GOREV_SURESI_S,
                              YAYIN_REF_XY,
                              YKS_TESPIT_TAZELIK_S,
                              iha_ub_ihlali,
                              ZEMIN_KAPLAMA_TAVANI,
                              ZEMIN_MASKESI_SUPHELI_SEBEBI,
                              OLCEK_KAYNAK_ARAC,
                              OLCEK_KAYNAK_ETIKETI,
                              OLCEK_KAYNAK_TELEMETRI,
                              asgari_irtifa_notu,
                              olcek_gecerli_mi, olcek_kaynak_metni,
                              rota_guven_reddi,
                              rota_olcek_reddi, zemin_kaplamasi)

# ── Renkler (koyu tema) ──────────────────────────────────────────────────────
BG      = "#0f1419"   # zemin
PANEL   = "#1a2129"   # panel zemini
CIZGI   = "#2a3441"   # panel kenarı
METIN   = "#e8edf2"
SOLUK   = "#8b98a5"
YESIL   = "#2ecc71"
SARI    = "#f0a437"
KIRMIZI = "#e15241"
MAVI    = "#4aa3df"

# T80: CLI görünüm adları ↔ iç görünüm adları. İç adlar ("harita"/"algi")
# butonlara ve V kısayoluna bağlıdır; CLI hakeme/tanıtıma bakar. Eşleme TEK
# YERDE durur ki iki taraf ayrışmasın (madde 16).
GORUNUM_SECENEKLERI = {"saha": "harita", "canli": "algi", "kamera": "kamera"}

ARENA_M = 50.0        # HTAB 50×50 m (şartname)
OLCEK = 1.0           # main() ekran DPI'sine göre ayarlar (yüksek DPI okunurluk)

# Hakem haritasındaki üç şeridin TEK çizim tablosu:
#   yol -> (merkez x, yarı genişlik, giriş y, çıkış y), metre.
# Rota ankrajı da aynı tablonun giriş noktasından türetilir; şerit ile rota
# ayrı sabitlerden çizilirse hakeme gösterilen ok sessizce başka yere kayar.
SERIT_CIZIM_TABLOSU = {
    1: (12.5, 3.0, 4.0, 46.0),
    2: (25.0, 3.0, 4.0, 46.0),
    3: (37.5, 3.0, 4.0, 46.0),
}
SEMATIK_GOSTERIM_UYARISI = (
    "SEMATIK GOSTERIM — serit tablosundan turetildi, GPS degil")
ANKOR_YOK_UYARISI = "ANKOR YOK"


def S(px):
    """Piksel ölçüsünü ekran DPI ölçeğiyle çarp (yazı puntoları tk'de otomatik)."""
    return int(px * OLCEK)


def serit_giris_ankoru(road):
    """Hakem haritasında ``road`` şeridinin güney giriş noktasını döndür.

    Bu yalnızca SEMANTİK bir ekran koordinatıdır; GPS/dünya konumu değildir.
    Bilinmeyen yol için ankraj uydurulmaz.
    """
    geometri = SERIT_CIZIM_TABLOSU.get(road)
    if geometri is None:
        return None
    merkez_x_m, _yari_genislik_m, giris_y_m, _cikis_y_m = geometri
    return merkez_x_m, giris_y_m


def rota_gosterim_geometrisi(road, ref_xy, waypoints):
    """Yayın rotasını hakem haritasına oturtan saf çizim dikişi.

    Üretim sözleşmesindeki ``ref_xy`` dünya koordinatı değil, yerel
    ofsettir. Önce yayınlanan yolun şerit girişi seçilir; ardından ref ve
    yerel waypoint ofsetleri eklenir. Eksik/bilinmeyen ankraj fail-closed olur.

    Dönüş: ``(noktalar, uyari)``. ``uyari`` varsa ``noktalar`` boştur.
    """
    ankraj = serit_giris_ankoru(road)
    if ref_xy is None or ankraj is None:
        return (), ANKOR_YOK_UYARISI
    if not waypoints:
        return (), None
    try:
        ref_x, ref_y = (float(ref_xy[0]), float(ref_xy[1]))
        baslangic = (ankraj[0] + ref_x, ankraj[1] + ref_y)
        noktalar = [baslangic]
        noktalar.extend((baslangic[0] + float(dx),
                         baslangic[1] + float(dy))
                        for dx, dy in waypoints)
    except (IndexError, TypeError, ValueError):
        return (), ANKOR_YOK_UYARISI
    return tuple(noktalar), None


def rota_ankor_uyarisi(rota):
    """OPEN_ROUTE hakemce onaylanabilir bir semantik ankraja sahip mi?"""
    if not rota:
        return ANKOR_YOK_UYARISI
    _noktalar, uyari = rota_gosterim_geometrisi(
        rota.get("road"), rota.get("ref_xy"), rota.get("waypoints"))
    return uyari


def inset_kutusu(genislik_px):
    """Sağ üst genel-saha inset'inin saf canvas kutusunu döndür."""
    boyut = S(132)
    sag = genislik_px - S(8)
    ust = S(8)
    return sag - boyut, ust, sag, ust + boyut


def sematik_uyari_yerlesimi(genislik_px):
    """Semantik uyarıyı sağ üst inset'ten yatayda ayıran yerleşim."""
    inset_sol, _ust, _sag, _alt = inset_kutusu(genislik_px)
    sol = S(12)
    genislik = max(0, inset_sol - S(8) - sol)
    return sol, S(8), genislik


def _kayit_profili():
    """Kayıt defterinin **etkin profilini** oku — TEK okuma yolu (madde 16).

    `config/model_registry.json` bu ekranın tek bildirim kaynağıdır: hangi
    ağırlık yüklenecek (T76) **ve** o ağırlığın hangi zeminde kabul edildiği
    (T77). Saha tarafında `codes/rpi_inference.py::model_kayit_dogrula` aynı
    defteri okur; ekran ile donanım tek bildirimden beslenir — biri çevrilip
    diğeri unutulamaz (D-58/D-60 ıraksama sınıfı; T58'de manifest tam bu
    yüzden sekiz gün v17 derken pakette v21 duruyordu, REVIEW_LOG D-83).

    Fail-closed: defter yoksa/bozuksa/profil yoksa **UYDURULMAZ**.
    """
    import json as _json
    defter = _PROJE_KOKU / "config" / "model_registry.json"
    try:
        veri = _json.loads(defter.read_text(encoding="utf-8"))
        return veri["profiles"][veri["default_profile"]], defter
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Üretim model kayıt defteri okunamadı ({defter}); hakem ekranı "
            "hangi ağırlığı yükleyeceğini UYDURMAZ.") from exc


def _uretim_modeli_adi():
    """Üretim ağırlığının ADI kayıt defterinden okunur (T76).

    Sürüm adı bu dosyaya ÇIPLAK YAZILMAZ. Fail-closed: ad uydurulmaz,
    hakem ekranı açılmaz. Sessiz varsayılan, ekranın sahadan farklı bir
    modeli göstermesi demektir.
    """
    profil, defter = _kayit_profili()
    try:
        yol = profil["path"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            f"Kayıt defterindeki etkin profilde `path` yok: {defter}") from exc
    ad = str(yol).replace("\\", "/").rsplit("/", 1)[-1]
    if not ad.endswith(".pt"):
        raise RuntimeError(
            f"Kayıt defterindeki etkin profil `.pt` ağırlık göstermiyor: {yol!r}")
    return ad


def _arac_dedektoru_yolu():
    """Ölçek katman 3'ün DOTA OBB ağırlığı — `(yol|None, sebep)` (T86).

    Yol ÇIPLAK YAZILMAZ; kayıt defterindeki `arac_referansi` profilinden gelir
    (madde 16, T85'te üretim modeli için kurulan desen). Burada fail-closed
    **fırlatmak** yanlış olurdu: katman 3'ün yokluğu bir arıza değil, meşru
    bir durumdur (arenada araç yoktur, Jetson paketinde bu ağırlık yoktur).
    Fail-closed olan şey **sessizlik**: sebep döner ve EKRANA yazılır.
    """
    import json as _json
    defter = _PROJE_KOKU / "config" / "model_registry.json"
    try:
        veri = _json.loads(defter.read_text(encoding="utf-8"))
        profil = veri["profiles"]["arac_referansi"]
        yol = _PROJE_KOKU / profil["path"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        return None, (f"kayıt defterinde `arac_referansi` profili yok/bozuk "
                      f"({type(exc).__name__})")
    if not yol.is_file():
        return None, f"ağırlık diskte yok: {yol.name}"
    return yol, f"kayıt defteri profili `arac_referansi` ({yol.name})"


def _kabul_kumesi_koku():
    """Üretim modelinin **KABUL EDİLDİĞİ** kadraj kümesinin kökü (T77).

    Kusur (D-116/5): bu satır T60 kümesini gösteriyordu, oysa v27 **T66**
    kümesinde kabul edilmişti (D-115). Yani hakem ekranı modeli, kabul
    edilmediği bir dağılımda gösteriyordu — ölçüldü: T60 **11/12**,
    T66 **12/12**.

    Kabul kümesi modelin KİMLİĞİNİN parçasıdır (hangi zeminde kabul edildi),
    bu yüzden ağırlıkla **aynı yerde** durur: sürüm değişince küme de tek
    yerden değişir, ikisi ayrı ayrı güncellenmez.

    ⚠ Dizinin VAR OLMASI şart koşulmaz — küme depo dışındadır
    (`O:\\navitas-local-train\\...`) ve temiz bir klonda bulunmayabilir. O
    durumda ekran "Kaynak boş" der; sessizce BAŞKA bir kümeye düşmez.
    Fail-closed olan şey **bildirimin yokluğudur**, verinin değil.
    """
    profil, defter = _kayit_profili()
    ham = profil.get("kabul_kumesi") if isinstance(profil, dict) else None
    if not isinstance(ham, str) or not ham.strip():
        raise RuntimeError(
            f"Kayıt defterindeki etkin profilde `kabul_kumesi` yok/geçersiz "
            f"({defter}); hakem ekranı modeli hangi zeminde göstereceğini "
            "UYDURMAZ.")
    return Path(ham.strip())


def _udp_adres(deger):
    """Argparse için IPv4/host:port hedefini doğrula ve tuple'a dönüştür."""
    try:
        host, port_metni = deger.rsplit(":", 1)
        port = int(port_metni)
    except (AttributeError, TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("HOST:PORT biçimi gerekli") from exc
    if not host or not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("HOST dolu, PORT 1..65535 olmalı")
    return host, port


def _ss(saniye):
    """Saniye → "MM:SS" (kronometre başlıkları SAYIDAN türer, elle yazılmaz)."""
    saniye = int(round(saniye))
    return f"{saniye // 60:02d}:{saniye % 60:02d}"


def arm_telemetri_degeri(mesaj):
    """HEARTBEAT'teki fiziksel ARM durumunu sıkı doğrula.

    JSON'da ``0``/``1`` ile ``false``/``true`` birbirine benzese de operatör
    eyleyicisi için yalnız gerçek bool kabul edilir. Eksik/bozuk alan durum
    uydurmaz; ``None`` ile fail-closed kalır.
    """
    deger = mesaj.get("armed") if isinstance(mesaj, dict) else None
    return deger if type(deger) is bool else None


def gps_gosterim_metni(telemetri):
    """Ham GNSS alanlarını insan-okunur yap; harita koordinatı üretme."""
    if not isinstance(telemetri, dict):
        telemetri = {}
    lat, lon = telemetri.get("lat"), telemetri.get("lon")
    fix, uydu = telemetri.get("gps_fix"), telemetri.get("uydu")
    if lat is None or lon is None:
        konum = "konum YOK"
    else:
        try:
            konum = f"{float(lat):.7f}, {float(lon):.7f}"
        except (TypeError, ValueError, OverflowError):
            konum = "konum BOZUK"
    fix_metin = f"fix {fix}" if fix is not None else "fix YOK"
    uydu_metin = f"{uydu} uydu" if uydu is not None else "uydu YOK"
    return (f"HAM GNSS: {konum} · {fix_metin} · {uydu_metin} · "
            "SEMANTİK HARİTADA KULLANILMAZ")


class YksArayuz:
    # T170 (ON_KAYIT §37): bu üç limit ÇIPLAK yazılıydı (900/600/900) ve
    # başlıklarındaki "/ 15:00" metinleri de elle yazılmıştı — yani sözleşme
    # değişse ekran ESKİ sayıyı göstermeye devam ederdi. Artık üçü de
    # `karar_sozlesmesi`den gelir ve başlık SAYIDAN türer (madde 16).
    IHA_LIMIT = SARTNAME_IHA_GOREV_SURESI_S      # §6.2 fırlatma → paraşütle iniş
    IKA_LIMIT = SARTNAME_IKA_GOREV_SURESI_S      # §6.2 teker dönüşü → HB temas
    HAZIRLIK_LIMIT = SARTNAME_HAZIRLIK_SURESI_S  # §6.2 alan girişi → takım hazır
    # §5.3.2 FDA test uçuşu kipinde İHA bütçesi DAHA SIKIDIR (tek 10 dk).
    # `--fda` ile örnek düzeyinde ezilir; varsayılan yarışma günü kipidir.
    fda_kipi = False

    def __init__(
            self, kok, link, otomatik_onay=False, demo=False, ika_peer=None,
            iha_peer=None, kamera_url=None):
        self.kok = kok
        self.link = link
        self.reader = FrameReader()
        self.gelen = queue.Queue()
        self.otomatik_onay = otomatik_onay
        self.demo = demo
        # Senaryo anahtarları — TRUE = SAĞLIKLI. F2/F3 haberleşmeyi, F4/F5 ise
        # TELEMETRİYİ keser. 🔴 T177 (D-323): F4/F5 eskiden yalnız GÜNLÜĞE
        # yazıyordu; panel aynı anda "12.6 V · 14 uydu" göstermeye devam
        # ediyordu. Ekranın kendi kendisiyle çelişmesi, tatbikatı izleyenin
        # gözünde senaryoyu değil SİSTEMİ şüpheli yapar.
        self.demo_durum = {"iha_hb": True, "ika_hb": True,
                           "iha_bat": True, "iha_gnss": True,
                           "iha_algi": True}   # F6 (D-383): algi canliligi

        self.rota = None            # son OPEN_ROUTE mesajı
        # T169 · §6.2: tespitin YAŞI. Şartname "gerçek zamanlı" der; bayat bir
        # tespit ekranda canlı görünürse hakem geçersiz bir onay verir.
        self.rota_zaman = None      # son KABUL EDİLEN OPEN_ROUTE'un yerel saati
        self.tespit_bayat = False   # `_durum_tazele` her saniye günceller
        self.rota_yok = None        # son NO_ROUTE; kırmızı güvenlik bandı için
        self.rota_adr = None        # ACK dönülecek adres
        self.onaylandi = False
        self.son_hb = {}            # node -> zaman
        # A2 (D-381): IHA'nin bildirdigi son ALGI KARARI yasi.
        # (deger_sn, alim_zamani) — etkin yas = deger + (simdi - alim).
        # None = alan HIC gelmedi -> yas BILINMIYOR, TAZE SAYILMAZ.
        self.karar_yas_rx = None
        self.son_adr = {}           # node -> adres (CMD gönderimi için)
        self.sabit_adr = {}         # CLI ile pinlenen adres heartbeat ile değişmez
        if ika_peer is not None:
            self.son_adr["ika"] = ika_peer
            self.sabit_adr["ika"] = ika_peer
        # D-403 (çürütücü KRİTİK-1): iha adresi yalnız heartbeat/OPEN_ROUTE
        # kaynağından öğreniliyordu — o adres rpi_inference'ın EFEMER portudur,
        # komut alıcısının (iha_komut_alici --bind) değil. PARACHUTE komutu
        # sahada alıcıya HİÇ ulaşmazdı. `--iha` ile pinlenir; heartbeat ezemez.
        if iha_peer is not None:
            self.son_adr["iha"] = iha_peer
            self.sabit_adr["iha"] = iha_peer
        self.sayac = {
            "OPEN_ROUTE": 0,
            "OPEN_ROUTE_RED": 0,
            "NO_ROUTE": 0,
            "IHA_LANDED": 0,
            "HEARTBEAT": 0,
            "ACK_TX": 0,
        }
        self.iha_landed_seq = None       # üretim İHA'sından gelen son iniş olayı
        # K4: IKA_GO ACK'lı tekrar gönderimi (durum makinesi Tk'dan bağımsız)
        self.ika_go_tekrar = AckliTekrar(
            self._ham_gonder, IKA_GO_TEKRAR_ARALIGI_S, IKA_GO_TEKRAR_UST_SINIRI)
        self.ika_go_ack_zamani = None    # İKA'nın IKA_GO ACK'ı (duvar saati)
        # P9a (D-393): PARACHUTE, ACK gelene dek tekrarlanır — en kritik acil
        # komut tek UDP paketine emanet edilemez (IKA_GO/K4 ile aynı ilke).
        self.parasut_tekrar = AckliTekrar(
            self._ham_gonder, PARASUT_TEKRAR_ARALIGI_S,
            PARASUT_TEKRAR_UST_SINIRI)
        self.parasut_ack_zamani = None
        # ARM/DISARM da tek paket değildir. Daha önemlisi, komut gönderimi
        # fiziksel durum kanıtı değildir: güçlü İHA ACK'i + taze Pixhawk
        # HEARTBEAT ``armed`` alanı birlikte gelmeden fırlatma açılmaz.
        self.arm_tekrar = AckliTekrar(
            self._ham_gonder, ARM_TEKRAR_ARALIGI_S,
            ARM_TEKRAR_UST_SINIRI)
        self.arm_bekleyen_komut = None
        self.arm_ack_zamani = None
        self.arm_durum_zamani = None
        # K8: İKA'nın OPEN_ROUTE ACK kanıtı: seq -> duvar saati. Hakem 2. onayı
        # ancak geçerli rota seq'i bu sözlükte varsa verebilir (fail-closed).
        self.ika_rota_ack = {}
        self.arm_acik = None
        self.tespit_onayli = False          # §2.2.3 iki aşamalı onayın 1. adımı
        self.t_iha0 = self.t_iha1 = None    # İHA görev kronometresi
        self.t_ika0 = self.t_ika1 = None    # İKA görev kronometresi
        self.t_haz0 = self.t_haz1 = None    # hazırlık kronometresi (§6.2)
        self.ceza_toplam = 0                # birikmiş ceza puanı
        self.parasut_teyit = 0.0            # iki adımlı paraşüt emniyeti
        self.mod = {}                       # node -> uçuş modu (AUTO/MANUEL)
        self._manuel_uyarildi = False
        self.iha_iz = []                    # İHA-UB içindeki konum izi (T162)
        self.tel = {}                       # node -> son telemetri alanları
        self.rx_alim = {}                   # seq -> kaç kez alındı (tekrar gönderim)
        self._detay_base = ""
        # canlı algı (v3 modeli ile gerçek çıkarım)
        self.algi_kuyruk = queue.Queue()
        self.algi_model = None
        # T86: ölçek katman 3 dedektörü — `(model|None, sebep)`; None ise HİÇ
        # denenmedi demektir. Tembel yüklenir, tek sefer.
        self._arac_modeli_durumu = None
        self.algi_mesgul = False
        # T29 (D-39): Bu yalnız semptom yönetimidir; asıl sorun D-21'deki v21
        # arena/RescueNet domain boşluğudur. Gemini/val tanısal karşılaştırma için kalır.
        # AÇILIŞ KAYNAĞI listenin ilkidir: `kompozit` — üç-kapılı arena
        # mantığının GEÇERLİ olduğu tek küme (yer gerçeği manifest'te).
        # `drone` bir otoparktır ve orada koridor seçimi sınanmaz (D-53).
        self.algi_kaynak = self.ALGI_VARSAYILAN_KAYNAK
        self.algi_idx = 0
        self._algi_foto = None              # ImageTk referansı (GC koruması)
        # Canlı RAW kamera, karar/telemetri SiK hattından AYRI bir LAN veri
        # düzlemidir. İstemci arızası ana Tk döngüsünü ve komutları bloklamaz.
        self.kamera_url = kamera_url
        self.kamera_istemci = None
        self._kamera_surum = -1
        self._kamera_foto = None

        self._arayuz_kur()
        if kamera_url:
            from kamera_istemci import KameraIstemci
            self.kamera_istemci = KameraIstemci(kamera_url)
            self.kamera_istemci.baslat()
        threading.Thread(target=self._dinle, daemon=True).start()
        self._tik()

    # ── Arayüz kurulumu ──────────────────────────────────────────────────────
    def _arayuz_kur(self):
        self.kok.title("NAVITAS — Yer Kontrol İstasyonu (YKS) · Hakem Ekranı")
        self.kok.configure(bg=BG)
        # ekran boyutuna göre pencere (yüksek DPI'da okunur kalır)
        sw, sh = self.kok.winfo_screenwidth(), self.kok.winfo_screenheight()
        w, h = min(S(1240), int(sw * 0.92)), min(S(940), int(sh * 0.90))
        self.kok.geometry(f"{w}x{h}")
        self.kok.minsize(S(1050), S(760))

        self.f_baslik = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.f_buyuk = tkfont.Font(family="Segoe UI", size=36, weight="bold")
        self.f_orta = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.f_kucuk = tkfont.Font(family="Segoe UI", size=10)
        self.f_mono = tkfont.Font(family="Consolas", size=10)

        # Başlık şeridi
        ust = tk.Frame(self.kok, bg=BG)
        ust.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(ust, text="NAVITAS", font=self.f_baslik, fg=YESIL, bg=BG).pack(side="left")
        tk.Label(ust, text="  YER KONTROL İSTASYONU — HAKEM EKRANI", font=self.f_baslik,
                 fg=METIN, bg=BG).pack(side="left")
        self.lbl_saat = tk.Label(ust, text="", font=self.f_orta, fg=SOLUK, bg=BG)
        self.lbl_saat.pack(side="right")
        # 🔴 T178 (D-323): uc kronometre kalabalik ALT satirda duruyordu ve IHA
        # olani HER DPI olceginde KIRPILIYORDU ("IA ⏱ --:-- / 15:0("). Sure
        # butcesi sartname §6.2/§5.3.2'nin puanlanan eksenidir ve operatorun
        # BAKTIGI yerde, kirpilmadan durmalidir. Ust serit bostu; buraya alindi.
        self.lbl_kron_iha = tk.Label(ust, text="", font=self.f_orta,
                                     fg=SOLUK, bg=BG)
        self.lbl_kron_iha.pack(side="right", padx=(0, 18))
        self.lbl_kron_ika = tk.Label(ust, text="", font=self.f_orta,
                                     fg=SOLUK, bg=BG)
        self.lbl_kron_ika.pack(side="right", padx=(0, 18))
        self.lbl_kron_haz = tk.Label(ust, text="", font=self.f_orta,
                                     fg=SOLUK, bg=BG)
        self.lbl_kron_haz.pack(side="right", padx=(0, 18))

        # Yazılım zinciri şeridi (parçaların bağlantısı)
        zincir = tk.Frame(self.kok, bg=PANEL, highlightbackground=CIZGI, highlightthickness=1)
        zincir.pack(fill="x", padx=14, pady=4)
        self.zincir_etiket = {}
        adimlar = ["Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                   "433 MHz TX", "YKS (bu ekran)", "İKA"]
        for i, ad in enumerate(adimlar):
            e = tk.Label(zincir, text=ad, font=self.f_kucuk, fg=SOLUK, bg=PANEL,
                         padx=10, pady=6)
            e.pack(side="left")
            self.zincir_etiket[ad] = e
            if i < len(adimlar) - 1:
                tk.Label(zincir, text="→", font=self.f_orta, fg=CIZGI, bg=PANEL).pack(side="left")

        govde = tk.Frame(self.kok, bg=BG)
        govde.pack(fill="both", expand=True, padx=14, pady=4)

        # Sol: iki görünüm — saha haritası / canlı algı (v3)
        _m = self.ALGI_MODEL_DOSYA.rsplit(".", 1)[0]
        sol = self._panel(govde, "SAHA HARİTASI — HTAB 50×50 m   |   "
                                 f"CANLI ALGI — {_m} (GERÇEK çıkarım)")
        sol.pack(side="left", fill="both", expand=True, padx=(0, 8))

        anahtar = tk.Frame(sol, bg=PANEL)
        anahtar.pack(fill="x", padx=10, pady=(4, 0))
        self.btn_gor_harita = tk.Button(anahtar, text="◈ Saha Haritası (V)",
                                        font=self.f_kucuk, fg=BG, bg=YESIL,
                                        relief="flat", padx=8, pady=3,
                                        command=lambda: self.gorunum("harita"))
        self.btn_gor_harita.pack(side="left", padx=(0, 6))
        self.btn_gor_algi = tk.Button(anahtar, text=f"◉ Canlı Algı — {_m} (V)",
                                      font=self.f_kucuk, fg=METIN, bg="#232e3a",
                                      relief="flat", padx=8, pady=3,
                                      command=lambda: self.gorunum("algi"))
        self.btn_gor_algi.pack(side="left")
        self.btn_gor_kamera = tk.Button(
            anahtar, text="▣ RAW Kamera (C)", font=self.f_kucuk,
            fg=METIN, bg="#232e3a", relief="flat", padx=8, pady=3,
            command=lambda: self.gorunum("kamera"))
        self.btn_gor_kamera.pack(side="left", padx=(6, 0))

        self.harita = tk.Canvas(sol, width=S(480), height=S(420), bg="#121920",
                                highlightthickness=0)
        self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True)

        # canlı algı görünümü (başta gizli)
        self.algi_cerceve = tk.Frame(sol, bg=PANEL)
        self.lbl_algi_img = tk.Label(self.algi_cerceve, bg="#121920",
                                     text=f"{_m} modeli ilk geçişte yüklenecek…",
                                     fg=SOLUK, font=self.f_kucuk)
        self.lbl_algi_img.pack(padx=10, pady=(4, 4), fill="both", expand=True)
        arow = tk.Frame(self.algi_cerceve, bg=PANEL)
        arow.pack(fill="x", padx=10)
        for ad, kom in (("◀ Önceki (←)", self.algi_onceki),
                        ("Sonraki (→) ▶", self.algi_sonraki),
                        ("Kaynak değiştir (K)", self.algi_kaynak_degistir)):
            tk.Button(arow, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=MAVI, activeforeground=BG, relief="flat",
                      padx=7, pady=3, command=kom).pack(side="left", padx=(0, 6))
        self.lbl_algi_bilgi = tk.Label(self.algi_cerceve, text="—",
                                       font=self.f_kucuk, fg=SOLUK, bg=PANEL,
                                       anchor="w", wraplength=S(640),
                                       justify="left")
        self.lbl_algi_bilgi.pack(fill="x", padx=10, pady=(2, 4))

        # Canlı kamera, yerel model çıkarımı değildir. Jetson'ın /kare.jpg
        # ucundan ayrı Wi-Fi/LAN üstünde gelir; bu görünüm karar üretmez.
        self.kamera_cerceve = tk.Frame(sol, bg=PANEL)
        self.lbl_kamera_img = tk.Label(
            self.kamera_cerceve, bg="#121920", fg=SOLUK,
            text=("KAMERA URL YOK — --kamera-url http://<JETSON_IP>:8080"
                  if not self.kamera_url else "RAW kamera bağlanıyor…"),
            font=self.f_kucuk)
        self.lbl_kamera_img.pack(padx=10, pady=(4, 4), fill="both", expand=True)
        self.lbl_kamera_bilgi = tk.Label(
            self.kamera_cerceve,
            text=(f"Kaynak: {self.kamera_url}" if self.kamera_url else
                  "Video SiK 433 MHz üzerinden TAŞINMAZ; ayrı LAN gerekir."),
            font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
            wraplength=S(640), justify="left")
        self.lbl_kamera_bilgi.pack(fill="x", padx=10, pady=(2, 4))
        self.gorunum_adi = "harita"

        # Acil durum senaryo tatbikatı (yalnız --demo modunda etkin)
        tk.Label(sol, text="ACİL DURUM SENARYOLARI — arıza emniyet tatbikatı "
                           "(DDR B.3.3.1 tablosu; simülasyon)",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left").pack(fill="x", padx=10)
        btnf = tk.Frame(sol, bg=PANEL)
        btnf.pack(fill="x", padx=10, pady=(2, 10))
        for i, (ad, kod) in enumerate((("F1 RC kaybı", "rc"), ("F2 YKS kaybı", "yks"),
                                       ("F3 İKA kaybı", "ika"), ("F4 Batarya", "bat"),
                                       ("F5 GNSS", "gnss"), ("F6 Algı aşımı", "algi"))):
            tk.Button(btnf, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=SARI, activeforeground=BG, relief="flat",
                      padx=7, pady=3,
                      state=("normal" if self.demo else "disabled"),
                      command=lambda k=kod: self.senaryo(k)
                      ).pack(side="left", padx=(0, 6))

        # Demo / SS kontrolleri ("hile tuşları") — onay akışını yeniden izlemek
        # ve ekran görüntüsü sahnelemek için
        tk.Label(sol, text="DEMO / SS KONTROLLERİ — kısayollar: F1–F6 senaryo · "
                           "N yeni tespit · R onayı sıfırla · A arm · V harita/algı · "
                           "C RAW kamera · "
                           "←/→ algı görüntüsü · K kaynak",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left").pack(fill="x", padx=10)
        dkf = tk.Frame(sol, bg=PANEL)
        dkf.pack(fill="x", padx=10, pady=(2, 10))
        for ad, kom in (("Yeni tespit üret (N)", self.yeni_tespit),
                        ("Hakem onayını sıfırla (R)", self.onay_sifirla)):
            tk.Button(dkf, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=MAVI, activeforeground=BG, relief="flat",
                      padx=7, pady=3,
                      state=("normal" if self.demo else "disabled"),
                      command=kom).pack(side="left", padx=(0, 6))

        sag = tk.Frame(govde, bg=BG, width=S(440))
        sag.pack(side="left", fill="y")
        sag.pack_propagate(False)

        # Sağ 1: açık yol kararı
        p1 = self._panel(sag, self.KUTU_BASLIK["protokol"])
        p1.pack(fill="x", pady=(0, 8))
        self.p_karar = p1                       # T81: başlık kaynağı yazacak
        self._kutu = {k: dict(v) for k, v in self.KUTU_VARSAYILAN.items()}
        self.lbl_karar = tk.Label(p1, text="— BEKLENİYOR —", font=self.f_buyuk,
                                  fg=SOLUK, bg=PANEL)
        self.lbl_karar.pack(pady=(2, 0))
        self.lbl_detay = tk.Label(p1, text="İHA taraması sürüyor", font=self.f_kucuk,
                                  fg=SOLUK, bg=PANEL, wraplength=S(400), justify="center")
        self.lbl_detay.pack(pady=(0, 6))
        self.guven_cubuk = tk.Canvas(p1, width=S(380), height=S(20), bg="#121920",
                                     highlightthickness=0)
        self.guven_cubuk.pack(pady=(0, 12))

        # Sağ 2: hakem onayı
        p2 = self._panel(sag, "ALAN HAKEMİ ONAYI (şartname §6.2)")
        p2.pack(fill="x", pady=(0, 8))
        self.btn_onay = tk.Button(p2, text="TESPİTİ ONAYLA → ACK GÖNDER",
                                  font=self.f_orta, fg=BG, bg=SOLUK,
                                  activebackground=YESIL, relief="flat",
                                  state="disabled", command=self.onayla, pady=8)
        self.btn_onay.pack(fill="x", padx=10, pady=(4, 4))
        self.lbl_onay = tk.Label(p2, text="Onay bekleyen tespit yok", font=self.f_kucuk,
                                 fg=SOLUK, bg=PANEL, wraplength=S(400),
                                 justify="center")
        self.lbl_onay.pack(pady=(0, 8))

        # Sağ 2b: rota analizi (segment eksen değişimleri)
        p2b = self._panel(sag, "ROTA ANALİZİ — segment / eksen değişimleri")
        p2b.pack(fill="x", pady=(0, 8))
        rkap = tk.Frame(p2b, bg=PANEL)
        rkap.pack(fill="x", padx=10, pady=(2, 8))
        rkay = tk.Scrollbar(rkap, width=S(12))
        rkay.pack(side="right", fill="y")
        self.rota_metin = tk.Text(rkap, height=6, bg="#121920", fg=METIN, bd=0,
                                  font=self.f_mono, state="disabled", wrap="none",
                                  yscrollcommand=rkay.set)
        self.rota_metin.pack(side="left", fill="both", expand=True)
        rkay.config(command=self.rota_metin.yview)

        # Sağ 3: bağlantı durumu
        p3 = self._panel(sag, "BAĞLANTI / DÜĞÜM DURUMU")
        p3.pack(fill="x", pady=(0, 8))
        self.lbl_dugum = {}
        for ad in ("iha", "ika"):
            sat = tk.Frame(p3, bg=PANEL)
            sat.pack(fill="x", padx=10, pady=2)
            nokta = tk.Label(sat, text="●", font=self.f_orta, fg=KIRMIZI, bg=PANEL)
            nokta.pack(side="left")
            metin = tk.Label(sat, text=f"{ad.upper()}  — sinyal yok", font=self.f_kucuk,
                             fg=SOLUK, bg=PANEL, wraplength=S(390), justify="left")
            metin.pack(side="left", padx=6)
            self.lbl_dugum[ad] = (nokta, metin)
        self.lbl_ucus = tk.Label(p3, text="İHA UÇUŞ DURUMU: OTONOM GÖREV (AUTO)",
                                 font=self.f_orta, fg=YESIL, bg=PANEL,
                                 wraplength=S(410), justify="left")
        self.lbl_ucus.pack(padx=10, pady=(4, 0), anchor="w")
        self.lbl_gps = tk.Label(
            p3, text=gps_gosterim_metni({}), font=self.f_mono, fg=KIRMIZI,
            bg=PANEL, wraplength=S(410), justify="left")
        self.lbl_gps.pack(padx=10, pady=(4, 0), anchor="w")
        self.lbl_sayac = tk.Label(p3, text="", font=self.f_mono, fg=SOLUK, bg=PANEL)
        self.lbl_sayac.pack(padx=10, pady=(2, 8), anchor="w")

        # Sağ 4: mesaj günlüğü
        p4 = self._panel(sag, "MESAJ GÜNLÜĞÜ (canlı protokol trafiği)")
        p4.pack(fill="both", expand=True)
        gkap = tk.Frame(p4, bg=PANEL)
        gkap.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        kaydirak = tk.Scrollbar(gkap, width=S(12))
        kaydirak.pack(side="right", fill="y")
        self.gunluk = tk.Text(gkap, height=9, bg="#121920", fg=METIN, bd=0,
                              font=self.f_mono, state="disabled", wrap="word",
                              yscrollcommand=kaydirak.set)
        self.gunluk.pack(side="left", fill="both", expand=True)
        kaydirak.config(command=self.gunluk.yview)
        for renk_ad, renk in (("yesil", YESIL), ("sari", SARI),
                              ("kirmizi", KIRMIZI), ("mavi", MAVI),
                              ("soluk", SOLUK)):
            self.gunluk.tag_configure(renk_ad, foreground=renk)

        # Alt durum çubuğu
        alt = tk.Frame(self.kok, bg=PANEL)
        alt.pack(fill="x", side="bottom")
        tasiyici = "SiK 433 MHz (seri)" if isinstance(self.link, SerialLink) \
            else f"UDP :{self.link.port}"
        tk.Label(alt, text=f"  Taşıyıcı: {tasiyici}   ·   Protokol: newline-JSON v1"
                           f"   ·   Çerçeve: OPEN_ROUTE / IHA_LANDED / "
                           f"HEARTBEAT / ACK / CMD",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, wraplength=S(1150),
                 justify="left").pack(side="left", pady=3)

        # Görev kontrol & kronometre şeridi — 2 satır:
        # 1) hazırlık akışı (§6.2 hands-off), 2) uçuş/intikal akışı + paraşüt
        gorev = tk.Frame(self.kok, bg=PANEL, highlightbackground=CIZGI,
                         highlightthickness=1)
        gorev.pack(fill="x", side="bottom", padx=14, pady=(0, 4))
        satir1 = tk.Frame(gorev, bg=PANEL)
        satir1.pack(fill="x")
        satir2 = tk.Frame(gorev, bg=PANEL)
        satir2.pack(fill="x")

        def gbuton(ana, metin, komut, aktif=True):
            b = tk.Button(ana, text=metin, font=self.f_kucuk, fg=METIN,
                          bg="#232e3a", activebackground=SARI, activeforeground=BG,
                          relief="flat", padx=8, pady=3, command=komut,
                          state=("normal" if aktif else "disabled"))
            b.pack(side="left", padx=5, pady=3)
            return b

        # satır 1 — hazırlık (§6.2: 15 dk, Takım Hazır'la durur; müdahale +100 ceza)
        self.btn_alan = gbuton(satir1, "ALAN GİRİŞİ", self.alan_girisi)
        self.btn_hazir = gbuton(satir1, "TAKIM HAZIR", self.takim_hazir, aktif=False)
        self.btn_mudahale = gbuton(satir1, "MÜDAHALE (−100)", self.mudahale,
                                   aktif=False)
        self.lbl_ceza = tk.Label(satir1, text="CEZA Σ 0", font=self.f_orta,
                                 fg=SOLUK, bg=PANEL)
        self.lbl_ceza.pack(side="right", padx=10)

        # satır 2 — uçuş/intikal
        self.btn_arm = gbuton(satir2, "ARM DURUMU BEKLENİYOR", self.arm_degistir,
                              aktif=False)
        self.btn_firlat = gbuton(satir2, "FIRLATMA", self.firlatma, aktif=False)
        self.btn_iha_indi = gbuton(satir2, "İHA İNDİ", self.iha_indi, aktif=False)
        self.btn_parasut = gbuton(satir2, "PARAŞÜT (manuel −50)", self.parasut)
        # §2.2.5 kilidini GÖSTERMEK için hep tıklanabilir — erken basılırsa reddeder
        self.btn_ika_go = gbuton(satir2, "İKA BAŞLAT", self.ika_baslat)
        self.btn_hb = gbuton(satir2, "HB TEMAS", self.hb_temas, aktif=False)

        self.lbl_arm = tk.Label(satir2, text="SİSTEM: ARM DURUMU BİLİNMİYOR",
                                font=self.f_orta, fg=KIRMIZI, bg=PANEL)
        self.lbl_arm.pack(side="left", padx=10)
        self.lbl_ika_go = tk.Label(satir2, text="İKA_GO: —",
                                   font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_ika_go.pack(side="left", padx=10)

        # kısayollar ("hile tuşları")
        for i, kod in enumerate(("rc", "yks", "ika", "bat", "gnss", "algi"), 1):
            self.kok.bind(f"<F{i}>", lambda e, k=kod: self.senaryo(k))
        # 🔴 T177 (D-323): kisayollar YALNIZ kucuk harfe bagliydi. Caps Lock
        # acikken ya da Shift basiliyken BESI BIRDEN sessizce oluyordu — sunum
        # sirasinda tusa basip hicbir sey olmamasi "bozuk" izlenimi verir.
        # Her kisayol IKI harf durumuna da baglanir.
        def _kisayol(harf, islev):
            self.kok.bind(f"<KeyPress-{harf.lower()}>", lambda e: islev())
            self.kok.bind(f"<KeyPress-{harf.upper()}>", lambda e: islev())

        _kisayol("n", self.yeni_tespit)
        _kisayol("r", self.onay_sifirla)
        _kisayol("a", self.arm_degistir)
        _kisayol("c", lambda: self.gorunum("kamera"))
        _kisayol("v", lambda: self.gorunum(
            "algi" if self.gorunum_adi == "harita" else "harita"))
        _kisayol("k", self.algi_kaynak_degistir)
        self.kok.bind("<Left>", lambda e: self.algi_onceki())
        self.kok.bind("<Right>", lambda e: self.algi_sonraki())

        self._harita_ciz()

    def _panel(self, ebeveyn, baslik):
        p = tk.Frame(ebeveyn, bg=PANEL, highlightbackground=CIZGI, highlightthickness=1)
        # T81: başlık etiketi saklanır — AÇIK YOL TESPİTİ kutusu KAYNAĞINI
        # başlıkta da yazmak zorunda (telsiz mi, yerel algı mı).
        p.baslik_etiketi = tk.Label(p, text=baslik, font=self.f_kucuk, fg=SOLUK,
                                    bg=PANEL, anchor="w")
        p.baslik_etiketi.pack(fill="x", padx=10, pady=(6, 0))
        return p

    # ── AÇIK YOL TESPİTİ kutusu — KAYNAK AYRIMI (T81) ────────────────────────
    # 🔴 Bu kutu iki AYRI kaynaktan beslenebilir ve ikisi ASLA karışmamalıdır:
    #   `protokol` : telsizden gelen OPEN_ROUTE/NO_ROUTE — aracın kendi kararı
    #   `yerel`    : bu ekranın kendi çıkarımı — araç bunu GÖRMEDİ, göndermedi
    # Hakem §6.2 onayını aracın gönderdiği rotaya verir. Ekranın kendi hesabını
    # telsizden gelmiş sanarsa onay YANLIŞ VERİYE dayanır — kusurun kendisinden
    # daha ağır bir hata. Bu yüzden hangi kaynağın gösterildiğini GÖRÜNÜM
    # belirler (mesaj değil) ve kaynak hem başlıkta hem detay satırında yazılır.
    KUTU_VARSAYILAN = {
        "protokol": {"karar": "— BEKLENİYOR —", "renk": SOLUK,
                     "detay": "İHA taraması sürüyor", "guven": None},
        "yerel": {"karar": "— ÇÖZÜMLENİYOR —", "renk": SOLUK,
                  "detay": "YEREL ALGI — telsiz DEĞİL · henüz kare işlenmedi",
                  "guven": None},
    }
    KUTU_BASLIK = {
        "protokol": "AÇIK YOL TESPİTİ",
        # ⚠ Emoji YOK: tkinter'in yazıtipi renkli emojiyi çizemiyor, hakem
        # ekranında taralı bir kutu görünüyordu. Uyarı METİNLE taşınır.
        "yerel": "AÇIK YOL TESPİTİ — YEREL ALGI (telsiz DEĞİL)",
    }
    YEREL_IMZA = "YEREL ALGI — telsiz DEĞİL"

    def _kutu_kaynagi(self):
        """Kutuyu hangi kaynak besler? GÖRÜNÜM belirler, gelen mesaj DEĞİL."""
        return "yerel" if getattr(self, "gorunum_adi", "harita") == "algi" \
            else "protokol"

    def _kutu_yaz(self, kaynak, **alanlar):
        """Kaynağın durumunu SAKLA; ekrana yalnız GÖRÜNÜMÜN kaynağı basılır.

        Karıştırma yasağı burada uygulanır: canlı algı görünümündeyken gelen
        bir OPEN_ROUTE kutuyu BOYAMAZ — durumu güncellenir, haritaya
        dönüldüğünde olduğu gibi görünür. Sayaçlar/günlük etkilenmez.
        """
        if not hasattr(self, "_kutu"):
            self._kutu = {k: dict(v) for k, v in self.KUTU_VARSAYILAN.items()}
        self._kutu[kaynak].update(
            {a: d for a, d in alanlar.items() if d is not None})
        if kaynak == self._kutu_kaynagi():
            self._kutu_ciz()

    def _kutu_ciz(self):
        """Kutuyu GÖRÜNÜMÜN kaynağından çiz — başlık dâhil."""
        if not hasattr(self, "_kutu"):
            self._kutu = {k: dict(v) for k, v in self.KUTU_VARSAYILAN.items()}
        kaynak = self._kutu_kaynagi()
        d = self._kutu[kaynak]
        p = getattr(self, "p_karar", None)
        if p is not None:
            p.baslik_etiketi.config(text=self.KUTU_BASLIK[kaynak])
        self.lbl_karar.config(text=d["karar"], fg=d["renk"])
        self.lbl_detay.config(text=d["detay"])
        self._guven_ciz(d["guven"] if d["guven"] is not None else 0.0)

    def _yerel_karari_goster(self, y):
        """Canlı algının kararını kutuya yaz (§6.2 karıştırma yasağı ile)."""
        if not y:
            return
        yer = f"{y.get('kaynak')}/{y.get('kare')}"
        if y.get("yol_no"):
            karar = f"{y['yol_no']} · {ROAD_LABEL[y['yol_no']].upper()}"
            renk = YESIL
            detay = (f"{self.YEREL_IMZA} · {yer} · "
                     f"güven {y.get('guven_metin')}")
            # T86: güvenin İÇİNDE ölçek çarpanı var; hakem hangi katmandan
            # geldiğini kutuda da görmeli (sessiz düşüş yasak, D-126).
            if y.get("olcek_kaynagi"):
                detay += (f" · ölçek "
                          f"{OLCEK_KAYNAK_ETIKETI.get(y['olcek_kaynagi'], y['olcek_kaynagi'])}"
                          f" ×{y.get('olcek_carpani', 0.0):.2f}")
        else:
            karar = "ROTA YOK"
            renk = KIRMIZI
            sebep = y.get("ret") or "TESPİT YOK"
            detay = f"{self.YEREL_IMZA} · {yer} · {sebep}"
            if y.get("gerekce"):
                detay += f" · {y['gerekce']}"
        self._kutu_yaz("yerel", karar=karar, renk=renk, detay=detay,
                       guven=y.get("guven") if y.get("guven") is not None else 0.0)

    # ── Harita ───────────────────────────────────────────────────────────────
    def _mxy(self, x_m, y_m):
        """Metre (0..50, y kuzey) → canvas pikseli."""
        w = self.harita.winfo_width() or 480
        h = self.harita.winfo_height() or 480
        kenar = S(34)
        olcek = min(w, h) - 2 * kenar
        px = kenar + (x_m / ARENA_M) * olcek
        py = h - kenar - (y_m / ARENA_M) * olcek   # y yukarı = kuzey
        return px, py

    def _harita_ciz(self):
        c = self.harita
        c.delete("all")
        w = c.winfo_width()
        if w <= 1:
            w = S(480)
        # grid (5 m)
        for m in range(0, 51, 5):
            x0, y0 = self._mxy(m, 0)
            x1, y1 = self._mxy(m, 50)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
            x0, y0 = self._mxy(0, m)
            x1, y1 = self._mxy(50, m)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
        # arena çerçevesi
        x0, y0 = self._mxy(0, 0)
        x1, y1 = self._mxy(50, 50)
        c.create_rectangle(x0, y0, x1, y1, outline=CIZGI, width=2)

        # 3 yol koridoru — tespit sonrası: açık yol YEŞİL, geri kalan HER YER
        # (kapalı koridorlar + moloz sahası) KIRMIZI = gidilemez
        # Yeni NO_ROUTE, eski OPEN_ROUTE önbelleğini görsel olarak geçersiz
        # kılar: hakem ekranda yeşil bir rota görüp yanlış onay vermemelidir.
        acik = (self.rota["road"]
                if self.rota and not self.rota_yok
                and rota_ankor_uyarisi(self.rota) is None else None)
        if acik is not None:
            c.create_rectangle(x0, y0, x1, y1, fill=KIRMIZI, stipple="gray12",
                               outline="")
            lx, ly = self._mxy(0.8, 51.8)
            c.create_text(lx, ly, text="■ yeşil = geçilebilir açık yol   "
                                       "■ kırmızı = gidilemez (moloz / kapalı)",
                          fill=SOLUK, font=self.f_kucuk, anchor="w")
        for yol, geometri in SERIT_CIZIM_TABLOSU.items():
            xm, yari_genislik_m, giris_y_m, cikis_y_m = geometri
            secili = (yol == acik)
            px0, py0 = self._mxy(xm - yari_genislik_m, giris_y_m)
            px1, py1 = self._mxy(xm + yari_genislik_m, cikis_y_m)
            if secili:
                c.create_rectangle(px0, py0, px1, py1, fill=YESIL,
                                   stipple="gray25", outline=YESIL, width=2)
            elif acik is not None:
                c.create_rectangle(px0, py0, px1, py1, fill=KIRMIZI,
                                   stipple="gray25", outline=KIRMIZI,
                                   width=1, dash=(3, 3))
            else:
                c.create_rectangle(px0, py0, px1, py1, outline="#25303c",
                                   width=1, dash=(3, 3))
            tx, ty = self._mxy(xm, -2.4)          # arena çerçevesinin ALTINA yaz
            c.create_text(tx, ty, text=f"{yol}·{ROAD_LABEL[yol].upper()}",
                          fill=YESIL if secili else SOLUK, font=self.f_kucuk)
            if not secili and acik is not None:
                kx, ky = self._mxy(xm, 25)
                c.create_text(kx, ky, text="✕ KAPALI", fill="#ff8878",
                              font=self.f_kucuk)

        # İKA-KB (başlangıç, güney) ve HB (hedef, kuzey)
        kx, ky = self._mxy(25, 2)
        c.create_rectangle(kx - 12, ky - 12, kx + 12, ky + 12, outline=MAVI, width=2)
        c.create_text(kx + 16, ky, text="İKA-KB", fill=MAVI, font=self.f_kucuk,
                      anchor="w")
        hx, hy = self._mxy(25, 48)
        c.create_rectangle(hx - 12, hy - 12, hx + 12, hy + 12, outline=KIRMIZI, width=2)
        c.create_text(hx, hy, text="H", fill=KIRMIZI, font=self.f_orta)
        c.create_text(hx, hy - 20, text="HB (hedef)", fill=KIRMIZI, font=self.f_kucuk)

        # rota: şerit giriş ankrajı + yerel ref_xy + yerel waypoint'ler.
        # Bu bir GPS/dünya konumu değil, hakem için semantik gösterimdir.
        rota_uyarisi = None
        if self.rota and not self.rota_yok:
            noktalar, rota_uyarisi = rota_gosterim_geometrisi(
                self.rota.get("road"), self.rota.get("ref_xy"),
                self.rota.get("waypoints"))
        else:
            noktalar = ()
        if noktalar:
            pks = [self._mxy(x, y) for x, y in noktalar]
            for (ax, ay), (bx, by) in zip(pks, pks[1:]):
                c.create_line(ax, ay, bx, by, fill=YESIL, width=3, arrow="last")
            rx, ry = pks[0]
            c.create_oval(rx - 5, ry - 5, rx + 5, ry + 5, fill=SARI, outline="")
            c.create_text(rx - 16, ry, text="ref", fill=SARI, font=self.f_kucuk, anchor="e")
        if rota_uyarisi:
            ux, uy = self._mxy(25, 25)
            c.create_text(ux, uy, text=rota_uyarisi, fill=KIRMIZI,
                          font=self.f_orta, anchor="center", width=w - S(48))

        if self.rota_yok:
            sebep = self.rota_yok.get("sebep", "bilinmeyen neden")
            detay = self.rota_yok.get("detay")
            w, h = c.winfo_width() or S(480), c.winfo_height() or S(420)
            bant_h = max(S(42), h // 10)
            c.create_rectangle(0, 0, w, bant_h, fill=KIRMIZI, outline="")
            metin = f"ROTA YOK — {sebep} · İKA GÜVENLİ DURUŞTA"
            if detay:
                metin += f"\n{detay}"
            c.create_text(S(12), bant_h // 2, text=metin, fill="white",
                          font=self.f_kucuk, anchor="w", width=w - S(24))

        # Hakemin GPS sanmaması gereken semantik gösterim uyarısı en son
        # çizilir; grid/rota-yok katmanları metni sonradan örtemez. Sağ üstteki
        # inset ayrı çağrıda çizildiği için yatay kutular da çakışmaz.
        uyari_x, uyari_y, uyari_w = sematik_uyari_yerlesimi(w)
        c.create_text(uyari_x, uyari_y, text=SEMATIK_GOSTERIM_UYARISI,
                      fill=SARI, font=self.f_kucuk, anchor="nw",
                      width=uyari_w)

    def _inset_ciz(self):
        """Mini genel-saha: İHA-UB çerçevesi (kenar SÖZLEŞMEDEN) + HTAB + İHA-İB (mavi)
        + İHA canlı konum izi (heartbeat x,y alanlarından)."""
        c = self.harita
        c.delete("inset")
        gw = int(c.winfo_width())
        if gw <= 1:
            gw = S(480)
        x0, y0, x1, y1 = inset_kutusu(gw)
        b = x1 - x0
        c.create_rectangle(x0, y0, x1, y1, fill="#0d1318", outline=CIZGI,
                           tags="inset")

        def ub(px, py):        # İHA-UB metre (0..kenar, y kuzey) → inset pikseli
            # T162: kenar SÖZLEŞMEDEN; çerçeve ile geofence kapısı TANIM GEREĞİ
            # aynı sayıyı kullanır (eskiden ikisi ayrı ayrı `300` yazıyordu).
            kenar = SARTNAME_IHA_UB_KENAR_M
            return (x0 + px / kenar * b, y1 - py / kenar * b)

        c.create_text(x0 + 4, y0 + 8,
                      text=f"İHA-UB {SARTNAME_IHA_UB_KENAR_M:.0f}×"
                           f"{SARTNAME_IHA_UB_KENAR_M:.0f} m", fill=SOLUK,
                      font=self.f_kucuk, anchor="w", tags="inset")
        hx0, hy0 = ub(125, 125)
        hx1, hy1 = ub(175, 175)
        c.create_rectangle(hx0, hy0, hx1, hy1, outline=SARI, tags="inset")
        c.create_text(*ub(150, 110), text="HTAB", fill=SARI,
                      font=self.f_kucuk, tags="inset")
        ix0, iy0 = ub(40, 230)
        ix1, iy1 = ub(70, 260)
        c.create_rectangle(ix0, iy0, ix1, iy1, outline=MAVI, fill=MAVI,
                           stipple="gray25", tags="inset")
        c.create_text(*ub(55, 215), text="İHA-İB", fill=MAVI,
                      font=self.f_kucuk, tags="inset")
        if len(self.iha_iz) >= 2:
            pts = []
            for mx, my in self.iha_iz:
                pts.extend(ub(mx, my))
            c.create_line(*pts, fill=YESIL, width=1, tags="inset")
            sx, sy = ub(*self.iha_iz[-1])
            c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=YESIL,
                          outline="", tags="inset")

    # ── Ağ dinleyici (arka plan iş parçacığı) ────────────────────────────────
    def _dinle(self):
        while True:
            try:
                d, adr = self.link.recv()
            except OSError as exc:
                # Soket GERÇEKTEN kapandıysa (pencere kapanıyor) çık. Aksi hâlde
                # bu geçici bir ağ hatasıdır ve dinleyiciyi KALICI öldürmemeli:
                # eskiden tek bir ölü akran hakem ekranını sessizce sağırlaştırıyordu
                # (ekran donmuyor ama hiçbir çerçeve işlenmiyordu).
                soket = getattr(self.link, "sock", None)
                if soket is None or soket.fileno() == -1:
                    return
                # Tk thread-güvenli değil; günlüğe ana döngü kuyruğundan yazılır.
                self.algi_kuyruk.put(
                    ("log", f"⚠ ağ hatası yok sayıldı: {type(exc).__name__}: {exc}"))
                continue
            if not d:
                continue
            for m in self.reader.feed(d):
                self.gelen.put((m, adr))

    # ── Ana döngü tiki ───────────────────────────────────────────────────────
    def _tik(self):
        while not self.gelen.empty():
            m, adr = self.gelen.get()
            # Tek bir BOZUK çerçeve hakem ekranını KALICI dondurmamalı: _tik
            # kendi zincirini `after(120)` ile kuruyor, burada fırlayan bir
            # istisna o zinciri kopartıyor ve saat, günlük, kronometreler,
            # butonlar hepsi ölüyordu. Ölçüldü: `ref_xy=None` taşıyan geçerli
            # bir OPEN_ROUTE (protokol buna izin veriyor, protocol.py:44-45)
            # `m['ref_xy'][0]` ile TypeError üretiyordu.
            try:
                self._mesaj_isle(m, adr)
            except Exception as exc:
                self._logla(f"⚠ BOZUK ÇERÇEVE yok sayıldı — "
                            f"{type(exc).__name__}: {exc}", "sari")
        while not self.algi_kuyruk.empty():
            paket = self.algi_kuyruk.get()
            if paket[0] == "sonuc":
                gorsel, bilgi, log_satiri = paket[1], paket[2], paket[3]
                self._algi_sonucu_goster(gorsel, bilgi)
                # T81: sağ panel de canlı algının kararını göstersin. Kutu
                # yalnız CANLI ALGI görünümündeyken bu değeri basar; sayaçlara
                # ve protokol durumuna DOKUNMAZ.
                self._yerel_karari_goster(paket[4] if len(paket) > 4 else None)
                self._logla(log_satiri, "yesil")
            elif paket[0] == "hata":
                # Worker hatasi yalniz gunluge dusunce algi paneli sonsuza dek
                # "isleniyor" gorunuyordu. Hatayi ayni panelde gorunur kil.
                self.lbl_algi_img.config(
                    image="", text="ALGİ HATASI — ayrıntı aşağıda")
                self.lbl_algi_bilgi.config(text=paket[1])
                # T81: hata da SESSİZ kalmasın — kutu sonsuza dek
                # "ÇÖZÜMLENİYOR" görünmemeli.
                self._kutu_yaz("yerel", karar="ALGI HATASI", renk=KIRMIZI,
                               detay=f"{self.YEREL_IMZA} · {paket[1]}",
                               guven=0.0)
                self._logla(paket[1], "sari")
            else:
                self._logla(paket[1], "mavi")
        self._kamera_tazele()
        self._durum_tazele()
        self.kok.after(120, self._tik)

    def _mesaj_isle(self, m, adr):
        tip = m.get("type")
        if tip == "OPEN_ROUTE":
            guven_reddi = rota_guven_reddi(m.get("conf"))
            if guven_reddi is not None:
                self._open_route_guven_reddini_goster(m, guven_reddi)
                return
            self._dugum_adresini_ogren("iha", adr)
            yeni = (self.rota is None) or (m["seq"] != self.rota["seq"])
            self.rota, self.rota_adr = m, adr
            # T169 · §6.2: her KABUL EDILEN cerceve tespiti TAZELER — tekrar
            # gonderim de canlilik kanitidir. Bayatlik `_durum_tazele`de olculur.
            # D-384: damga MONOTONIK — duvar saati (NTP/elle duzeltme)
            # geri atlarsa BAYAT tespit TAZE gorunuyordu (D-383'un
            # karar_yas icin kapattigi fail-open sinifinin A2-oncesi
            # ikizi; curutucu isaret etti). Tum tazelik damgalari ve
            # okurlari ayni saate gecti.
            self.rota_zaman = time.monotonic()
            self.tespit_bayat = False
            self.rota_yok = None
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            ankor_uyarisi = rota_ankor_uyarisi(m)
            if yeni:
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac["OPEN_ROUTE"] += 1
                self._logla(f"OPEN_ROUTE  yol={m['road']}({m['label']}) "
                            f"güven={m['conf']} seq={m['seq']} wp={len(m['waypoints'])}",
                            "yesil")
                if self.t_iha1:
                    self._logla("⚠ GEÇERSİZLİK RİSKİ: aktarım İHA inişinden SONRA "
                                "geldi — şartname §6.4: aktarım HAVADA tamamlanmalı!",
                                "sari")
                if ankor_uyarisi:
                    self._kutu_yaz("protokol", karar=ANKOR_YOK_UYARISI,
                                   renk=KIRMIZI)
                else:
                    self._kutu_yaz("protokol",
                                   karar=f"{m['road']} · {m['label'].upper()}",
                                   renk=YESIL)
                # ref_xy protokolce None OLABILIR (protocol.py:44-45) ve
                # iha_sender geometri dogrulamasini yalniz ika/broadcast akrani
                # varken kosar — yani "--yks" tek hedefliyken None gelir.
                _ref = m.get("ref_xy") or ("—", "—")
                self._detay_base = (f"seq={m['seq']} · ref=({_ref[0]}, "
                                     f"{_ref[1]}) m · {len(m.get('waypoints') or [])} waypoint")
                self._rota_analiz(m)
                if ankor_uyarisi:
                    self._ankor_yok_onayini_kapat(logla=True)
                else:
                    self.btn_onay.config(state="normal", bg=SARI,
                                         text="1) TESPİTİ DOĞRULA (§2.2.3)")
                    self.lbl_onay.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                                              "gönderimde (ACK yok)", fg=SARI)
                # T171 · §5.3.2: tespit ASGARİ İRTİFANIN ALTINDA üretildiyse
                # hakem bunu ONAYLAMADAN ÖNCE görmeli. Ret DEĞİL — İHA
                # kalkış/inişte de kare üretir; ama madde "asgari 30 metre
                # irtifadan ... tespit etmek" der. İrtifa BİLİNMİYORSA da
                # sessiz kalınmaz: bilinmediği yazılır (D-319).
                self._irtifa_notunu_goster()
                self._kutu_yaz("protokol", guven=m["conf"])
                self._harita_ciz()
                self._zincir(("Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                              "433 MHz TX", "YKS (bu ekran)"))
                if self.otomatik_onay and not ankor_uyarisi:
                    self.kok.after(2500, self.onayla)
            # tekrar-gönderim mekanizması canlı izlensin (jüri: ACK'siz teslim yok)
            self._kutu_yaz(
                "protokol",
                detay=f"{self._detay_base} · alım #{self.rx_alim[m['seq']]}")
        elif tip == "NO_ROUTE":
            self._dugum_adresini_ogren("iha", adr)
            onceki_seq = self.rota_yok.get("seq") if self.rota_yok else None
            yeni = m.get("seq") != onceki_seq
            self.rota_yok = m
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            # NO_ROUTE da aktarımın teslim edildiğini kanıtlamalıdır. Bu bir
            # rota onayı değil, İKA'nın hareket etmeyeceği güvenlik bildirimidir.
            # T206 (D-405 Q4): ACK `ref_tip` taşır — hub fan-out'unda seq
            # çakışan başka tipteki bekleyen bu ACK'i sahiplenemez (§6.6).
            if adr is not None:
                self.link.send(encode(ack(m["seq"], "yks", tip)), adr)
            elif isinstance(self.link, SerialLink):
                self.link.send(encode(ack(m["seq"], "yks", tip)))
            self.sayac["ACK_TX"] += 1
            if yeni:
                sebep = m.get("sebep", "bilinmeyen neden")
                detay = m.get("detay")
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac["NO_ROUTE"] += 1
                self._detay_base = f"seq={m['seq']} · {sebep}"
                self._kutu_yaz("protokol", karar="ROTA YOK", renk=KIRMIZI,
                               detay=self._detay_base
                               + (f" · {detay}" if detay else ""))
                self.btn_onay.config(state="disabled", bg="#232e3a",
                                     text="ROTA YOK — ACK OTOMATİK GÖNDERİLDİ")
                self.lbl_onay.config(text="Costmap güvenli rota üretmedi; İKA hareket etmez.",
                                      fg=KIRMIZI)
                self._kutu_yaz("protokol", guven=0.0)
                self._harita_ciz()
                self._logla(f"NO_ROUTE · {sebep}"
                            + (f" · {detay}" if detay else "")
                            + " → güvenli duruş ACK'i gönderildi", "sari")
        elif tip == "ACK":
            self._ack_isle(m, adr)
        elif tip == "IHA_LANDED":
            seq = m.get("seq")
            if (m.get("node") != "iha" or isinstance(seq, bool)
                    or not isinstance(seq, int)):
                return
            # T206 (D-405 Q4): `ref_tip` — IHA_LANDED seq'i İHA'nın OPEN_ROUTE
            # seq'iyle çakışırsa bu ACK yanlış bekleyene bağlanamaz (§6.6).
            if adr is not None:
                self.link.send(encode(ack(seq, "yks", tip)), adr)
            elif isinstance(self.link, SerialLink):
                self.link.send(encode(ack(seq, "yks", tip)))
            self.sayac["ACK_TX"] += 1
            if seq != self.iha_landed_seq:
                self.iha_landed_seq = seq
                self.sayac["IHA_LANDED"] += 1
                self._logla(
                    f"IHA_LANDED · üretim uçuşu iniş kanıtı alındı → ACK ref={seq}",
                    "yesil",
                )
                # P9c (D-393) — §2.2.3 sıra denetimi: iniş kanıtı, İKA'nın
                # OPEN_ROUTE ACK'ından ÖNCE geldiyse aktarım havada BİTMEMİŞTİR.
                if not (self.rota and self.rota["seq"] in self.ika_rota_ack):
                    self._logla(
                        "⚠ İHLAL RİSKİ: iniş kanıtı geldi ama İKA'nın rota "
                        "ACK kanıtı YOK — aktarım İHA havadayken "
                        "tamamlanmadı (§2.2.3)", "kirmizi")
                # Operatör düğmesi güvenlik sinyali üretmez; tersine gerçek
                # protokol olayı mevcut UI/kronometre kaydını besler.
                self.iha_indi()
        elif tip == "HEARTBEAT":
            dugum = m.get("node", "?")
            self.son_hb[dugum] = time.monotonic()   # D-384: monotonik
            self._dugum_adresini_ogren(dugum, adr)
            # A2 (D-381): algi canliligi hat canliligindan AYRI izlenir.
            # D-383 (curutucu): (1) alim damgasi ve gecen-sure hesabi
            # MONOTONIK — duvar saati (NTP/elle duzeltme) geri atlarsa
            # etkin yas negatiflesip BAYAT tespiti TAZE gosteriyordu; IHA
            # tarafi zaten monotonikti, alim tarafi asimetrik kalmisti.
            # (2) NaN/negatif deger KABUL EDILMEZ: nan > esik daima False
            # oldugundan NaN, "eksik alan = BILINMIYOR" korumasini atlatip
            # tespiti KALICI taze gosterirdi. Gecersiz deger YOK sayilir.
            if dugum == "iha" and "karar_yas" in m:
                try:
                    _ky = float(m["karar_yas"])
                    if math.isfinite(_ky) and _ky >= 0.0:
                        self.karar_yas_rx = (_ky, time.monotonic())
                except (TypeError, ValueError):
                    pass          # bozuk deger yut: eski deger/None kalir
            # Her heartbeat snapshot'tır: alan gelmediyse eski değer SAKLANMAZ.
            # Aksi hâlde GNSS kesildiğinde son koordinat sonsuza dek canlı görünür.
            tel = {k: m[k] for k in (
                "alt", "hiz", "bat", "uydu", "lat", "lon", "gps_fix")
                   if k in m}
            self.tel[dugum] = tel
            if dugum == "iha":
                armed = arm_telemetri_degeri(m)
                if armed is not None:
                    self.arm_acik = armed
                    self.arm_durum_zamani = time.monotonic()
                    self._arm_bekleyeni_tamamla()
                self._arm_ui_uygula()
            if "mod" in m:
                self.mod[dugum] = m["mod"]
                if m["mod"] != "AUTO" and not self._manuel_uyarildi:
                    self._manuel_uyarildi = True
                    self._logla(f"⚠ {dugum.upper()} MANUEL MODA GEÇTİ — tam otonomi "
                                "ihlali: UÇUŞ GEÇERSİZ sayılır (§6.4)", "sari")
            if dugum == "iha" and "x" in m and "y" in m:
                self.iha_iz.append((float(m["x"]), float(m["y"])))
                del self.iha_iz[:-150]         # son 150 nokta
                # geofence: İHA-UB dışına taşma = alan ihlali (§6.2/§6.4).
                # T162: kural ve kenar uzunluğu SÖZLEŞMEDEN gelir — `300` burada
                # ÇIPLAK yazılıydı (madde 16) ve üretimde `x,y` üreten yol
                # olmadığı için bu kapı SAHADA HİÇ ateş almıyordu.
                _ihlal = iha_ub_ihlali(m["x"], m["y"])
                if _ihlal is not None:
                    self._logla(f"⚠ ALAN İHLALİ: {_ihlal[1]} — uçuş başarısız "
                                "sayılır (§6.4)", "sari")
            self.sayac["HEARTBEAT"] += 1

    def _open_route_guven_reddini_goster(self, m, guven_reddi):
        """Eşik altı OPEN_ROUTE'u hakeme görünür kıl; rota ACK'i ASLA üretme."""
        sebep, detay = guven_reddi
        seq = m.get("seq")
        onceki_seq = (self.rota_yok.get("seq") if self.rota_yok else None)
        yeni = seq != onceki_seq
        self.rota_yok = {
            "type": "NO_ROUTE", "sebep": sebep, "detay": detay, "seq": seq,
            "kaynak_type": "OPEN_ROUTE",
        }
        self.rx_alim[seq] = self.rx_alim.get(seq, 0) + 1
        self.onaylandi = False
        self.tespit_onayli = False
        if yeni:
            self.sayac["OPEN_ROUTE_RED"] += 1
            self._detay_base = f"seq={seq} · {sebep}"
            self._kutu_yaz("protokol", karar="ROTA YOK", renk=KIRMIZI,
                           detay=f"{self._detay_base} · {detay}")
            self.btn_onay.config(
                state="disabled", bg="#232e3a",
                text="DÜŞÜK GÜVEN — OPEN_ROUTE REDDEDİLDİ")
            self.lbl_onay.config(
                text="Rota güven eşiğinin altında; ACK gönderilmedi, İKA hareket etmez.",
                fg=KIRMIZI)
            self._kutu_yaz("protokol", guven=0.0)
            self._harita_ciz()
            self._logla(
                f"OPEN_ROUTE REDDEDİLDİ · {sebep} · {detay} · ACK YOK",
                "sari")
        self._kutu_yaz(
            "protokol",
            detay=f"{self._detay_base} · alım #{self.rx_alim[seq]} · ACK YOK")

    def _ankor_yok_onayini_kapat(self, logla=False):
        """Eksik semantik ankrajı görünür kıl ve hakem onayını kapat."""
        btn = getattr(self, "btn_onay", None)
        if btn is not None:
            btn.config(state="disabled", bg="#232e3a",
                       text="ANKOR YOK — ONAY KAPALI")
        etiket = getattr(self, "lbl_onay", None)
        if etiket is not None:
            etiket.config(
                text="ANKOR YOK — rota şeride yerleştirilemedi; hakem onayı "
                     "ve ACK fail-closed kapatıldı.",
                fg=KIRMIZI)
        if logla:
            self._logla("HAKEM ONAYI REDDEDİLDİ: ANKOR YOK — rota şeride "
                        "yerleştirilemedi, ACK gönderilmedi", "sari")

    def onayla(self):
        """Şartname §2.2.3 İKİ AŞAMALI hakem onayı: (1) güzergâh tespitinin
        doğrulanması, (2) İKA'ya aktarımın doğrulanması → ACK ancak 2. adımda."""
        if not self.rota or self.rota_yok or self.onaylandi:
            return
        # A1 fail-closed: dugme durumu tek savunma degildir. Otomatik onay,
        # klavye veya dogrudan cagri eksik ankrajli rotayi onaylayamaz.
        if rota_ankor_uyarisi(self.rota):
            self._ankor_yok_onayini_kapat(logla=True)
            return
        # T169 · §6.2 FAIL-CLOSED: dugme TEK savunma degildir. Otomatik onay
        # (`--otomatik-onay`), klavye ya da bir zamanlayici bu yolu dugme
        # kapaliyken de cagirabilir; BAYAT tespit icin ACK URETILMEZ.
        if self._tespiti_yaslandir():
            self._logla("HAKEM ONAYI REDDEDILDI: tespit BAYAT (§6.2 gercek "
                        "zamanli aktarim) — ACK gonderilmedi", "sari")
            return
        if not self.tespit_onayli:
            self.tespit_onayli = True
            self._logla("HAKEM 1/2: güzergâh TESPİTİ doğrulandı (§2.2.3)", "sari")
            self._aktarim_onay_dugmesini_kur()
            return
        # K8 fail-closed: İKA'nın bu rota için OPEN_ROUTE ACK kanıtı ekranda
        # görünmeden "İKA'ya aktarıldı" onayı VERİLMEZ (şartname §2.2.3).
        if not self.ika_aktarim_kaniti_var():
            self._aktarim_onay_dugmesini_kur()
            self._logla("HAKEM 2/2 REDDEDİLDİ: İKA'dan OPEN_ROUTE ACK kanıtı yok "
                        f"(seq={self.rota['seq']}) — kanıtsız onay verilmez", "sari")
            return
        # T206 (D-405 Q4): hakem ACK'i `ref_tip` taşır (§6.6). `self.rota`
        # yalnız `_mesaj_isle`'nin OPEN_ROUTE dalında atanır, yani bu yol
        # tanım gereği OPEN_ROUTE onayıdır; alan eksikse (Tk'siz fikstürler)
        # tip yine OPEN_ROUTE'tur — ref_tip'siz (zayıf) ACK üretilmez.
        rota_ack = ack(self.rota["seq"], "yks",
                       self.rota.get("type") or "OPEN_ROUTE")
        if self.rota_adr is not None:
            self.link.send(encode(rota_ack), self.rota_adr)
        else:                                   # seri hat: adres kavramı yok
            self.link.send(encode(rota_ack))
        self.onaylandi = True
        self.sayac["ACK_TX"] += 1
        if self.t_iha1 is not None:
            havada = " · ⚠ aktarım İHA inişinden SONRA (§6.4 geçersizlik riski)"
        elif self.iha_landed_seq is not None:
            havada = " · AKTARIM ZAMANI BİLİNMİYOR (IHA_LANDED kanıtı var)"
        else:
            havada = " · İHA henüz inmedi"
        kanit = time.strftime("%H:%M:%S", time.localtime(
            self.ika_rota_ack[self.rota["seq"]]))
        self.btn_onay.config(state="disabled", bg=YESIL, text="ONAYLANDI ✓✓")
        self.lbl_onay.config(text=f"Hakem onayı tam — ACK(seq={self.rota['seq']}) "
                                  f"İHA'ya iletildi · İKA ACK kanıtı {kanit}"
                                  f"{havada}", fg=YESIL)
        self._logla(f"HAKEM 2/2: İKA'ya aktarım doğrulandı → ACK ref={self.rota['seq']}",
                    "sari")
        self._zincir(("Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                      "433 MHz TX", "YKS (bu ekran)", "İKA"))

    # ── K8: İKA aktarım kanıtı (fail-closed hakem kapısı) ────────────────────
    def ika_aktarim_kaniti_var(self):
        """Geçerli rota seq'i için İKA'dan OPEN_ROUTE ACK görüldü mü?"""
        return bool(self.rota) and self.rota["seq"] in self.ika_rota_ack

    def _onay_dugmesini_tazele(self):
        """Bayatlik kalkinca onay dugmesini DOGRU asamaya geri kur (T176).

        Iki asamali akista (sartname §2.2.3) dugmenin hâli, tespitin hangi
        asamada oldugunu yansitmali: henuz dogrulanmadiysa 1. asama, tespit
        dogrulandiysa 2. asama (kaniti varsa aktif, yoksa gerekceyle pasif).
        Onay TAMAMLANDIYSA dugmeye DOKUNULMAZ.
        """
        if self.onaylandi or not self.rota or self.rota_yok:
            return
        btn = getattr(self, "btn_onay", None)
        if btn is None:
            return
        if rota_ankor_uyarisi(self.rota):
            self._ankor_yok_onayini_kapat()
            return
        if self.tespit_onayli:
            self._aktarim_onay_dugmesini_kur()
            return
        btn.config(state="normal", bg=SARI,
                   text="1) TESPİTİ DOĞRULA (§2.2.3)")
        etiket = getattr(self, "lbl_onay", None)
        if etiket is not None:
            etiket.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                               "gönderimde (ACK yok)", fg=SARI)

    def _aktarim_onay_dugmesini_kur(self):
        """Tespit onaylandıktan sonra 2. düğmenin hâli: kanıt varsa aktif,
        yoksa PASİF + gerekçe metni (kanıt gelince `_ack_isle` yeniden çağırır)."""
        if rota_ankor_uyarisi(self.rota):
            self._ankor_yok_onayini_kapat()
            return
        if self.ika_aktarim_kaniti_var():
            kanit = time.strftime("%H:%M:%S", time.localtime(
                self.ika_rota_ack[self.rota["seq"]]))
            self.btn_onay.config(state="normal", bg=SARI,
                                 text="2) İKA'YA AKTARIMI ONAYLA → ACK")
            self.lbl_onay.config(
                text=f"Tespit doğrulandı ✓ · İKA ALDI ✓ {kanit} "
                     f"(OPEN_ROUTE ACK seq={self.rota['seq']}) — aktarımı "
                     "onaylayabilirsiniz (§2.2.3 ikinci onay)", fg=SARI)
        else:
            self.btn_onay.config(state="disabled", bg="#232e3a",
                                 text="2) İKA ACK KANITI BEKLENİYOR")
            self.lbl_onay.config(
                text="Tespit doğrulandı ✓ — ama İKA'dan OPEN_ROUTE ACK kanıtı "
                     f"GÖRÜNMEDİ (seq={self.rota['seq']}). Kanıt gelmeden "
                     "'İKA'ya aktarıldı' onayı verilemez (§2.2.3, fail-closed).",
                fg=KIRMIZI)

    def _ack_isle(self, m, adr):
        """Gelen ACK'ları bekleyenlere bağla: IKA_GO tekrarı (K4) ve İKA rota
        kanıtı (K8). `ref_tip` yoksa yalnız `ref` ile eşlenir (CONTRACTS §6.6)."""
        ref = m.get("ref")
        if isinstance(ref, bool) or not isinstance(ref, int):
            return
        if m.get("node") == "iha":
            arm_tekrar = getattr(self, "arm_tekrar", None)
            arm_komut = getattr(self, "arm_bekleyen_komut", None)
            arm_mesaji = getattr(arm_tekrar, "mesaj", None)
            if (arm_tekrar is not None and arm_komut and arm_mesaji
                    and kritik_komut_ack_gecerli_mi(
                        m, arm_mesaji.get("seq"), arm_komut, node="iha")
                    and arm_tekrar.ack_geldi(m)):
                self.arm_ack_zamani = time.monotonic()
                self._logla(f"İHA ALDI ✓ {arm_komut} güçlü ACK ref={ref}; "
                            "taze Pixhawk HEARTBEAT durumu bekleniyor", "yesil")
                self._arm_bekleyeni_tamamla()
                self._arm_ui_uygula()
            # P9a (D-393): PARACHUTE ACK'ı İHA düğümünden gelir — eski kod
            # iha ACK'larını hiç işlemiyordu (yalnız ika'da erken dönüş).
            # `__init__` koşmadan kurulan örneklerde (testler, D-320 kalıbı)
            # öznitelik olmayabilir; yokluk "bekleyen paraşüt yok" demektir.
            parasut_tekrar = getattr(self, "parasut_tekrar", None)
            parasut_mesaji = getattr(parasut_tekrar, "mesaj", None)
            if (parasut_tekrar is not None and parasut_mesaji
                    and kritik_komut_ack_gecerli_mi(
                        m, parasut_mesaji.get("seq"), "PARACHUTE", node="iha")
                    and parasut_tekrar.ack_geldi(m)):
                self.parasut_ack_zamani = time.time()
                damga = time.strftime("%H:%M:%S",
                                      time.localtime(self.parasut_ack_zamani))
                self._logla(f"İHA ALDI ✓ PARACHUTE ACK ref={ref} · {damga} · "
                            f"{parasut_tekrar.deneme} gönderim", "yesil")
                # D-403: "ACILDI" yalniz ACK'ta (Pixhawk COMMAND_ACK ACCEPTED)
                dugme = getattr(self, "btn_parasut", None)
                if dugme is not None:
                    dugme.config(text="PARAŞÜT AÇILDI ✓ (İHA ACK)")
            return
        if m.get("node") != "ika":
            return
        self._dugum_adresini_ogren("ika", adr)
        ref_tip = m.get("ref_tip")
        if self.ika_go_tekrar.ack_geldi(m):
            self.ika_go_ack_zamani = time.time()
            damga = time.strftime("%H:%M:%S", time.localtime(self.ika_go_ack_zamani))
            self.lbl_ika_go.config(text=f"İKA ALDI ✓ {damga}", fg=YESIL)
            self._logla(f"İKA ALDI ✓ IKA_GO ACK ref={ref} · {damga} · "
                        f"{self.ika_go_tekrar.deneme} gönderim", "yesil")
            if self.t_ika0 and not self.t_ika1:
                self.btn_hb.config(state="normal", bg=SARI)   # HB TEMAS artık anlamlı
        if (self.rota and ref == self.rota["seq"]
                and ref_tip in (None, "OPEN_ROUTE")
                and ref not in self.ika_rota_ack):
            self.ika_rota_ack[ref] = time.time()
            damga = time.strftime("%H:%M:%S", time.localtime(self.ika_rota_ack[ref]))
            # P9c (D-393) — §2.2.3: "Bu aktarımın İHA havada iken tamamlanması
            # gerekmektedir." Kanıt anında havada/yerde damgası basılır.
            havada = self._iha_havada_mi()
            self._logla(f"İKA ALDI ✓ OPEN_ROUTE ACK ref={ref} · {damga} "
                        "(aktarım kanıtı ekranda) · "
                        + ("İHA HAVADA ✓ (§2.2.3)" if havada else
                           "⚠ İHA HAVADA DEĞİL — §2.2.3 aktarım havadayken "
                           "bitmeliydi"),
                        "yesil" if havada else "sari")
            if self.tespit_onayli and not self.onaylandi:
                self._aktarim_onay_dugmesini_kur()
                if self.otomatik_onay:
                    self.kok.after(500, self.onayla)

    # ── Acil durum senaryoları (arıza emniyet tatbikatı) ─────────────────────
    # Davranışlar takım tasarımından: avionics_software.md "Arıza Emniyet
    # Senaryoları" tablosu + comms/ika_receiver.py gerçek failsafe'i + şartname
    # §6.4 (manuel müdahale = uçuş geçersiz → tüm aksiyonlar OTONOM olmalı).
    def senaryo(self, kod):
        if not self.demo:
            return
        # 🔴 T178 (D-323): her senaryo kendi geri-dönüş zamanlayıcısını kuruyor
        # ve hiçbiri diğerini İPTAL ETMİYORDU. F1'e basıp 1 sn sonra F2'ye
        # basılırsa, F1'in 6 sn'lik zamanlayıcısı F2 HÂLÂ YÜRÜRLÜKTEYKEN bandı
        # yeşil "OTONOM GÖREV"e çeviriyordu: bağlantı kesikken ekran "her şey
        # yolunda" diyordu. Jeton ile: geciken geri-dönüş, kendisinden SONRA
        # bir senaryo başladıysa bandı ARTIK değiştirmez.
        # ⚠ Anahtarı geri açmak jetondan BAĞIMSIZDIR — aksi hâlde üstü örtülen
        # senaryonun kestiği telemetri KALICI kesik kalır.
        self._senaryo_no = getattr(self, "_senaryo_no", 0) + 1
        no = self._senaryo_no

        def band_geri():
            """Bandı normale döndür — YALNIZ bu senaryo hâlâ güncelse."""
            if no != self._senaryo_no:
                return False
            self._ucus_normal()
            return True

        if kod == "rc":
            self._logla("SENARYO · Kumanda (RC) bağlantısı KESİLDİ", "sari")
            self._logla("  → Görev tam otonom (AUTO): uçuş KESİNTİSİZ sürer.", "soluk")
            self._logla("  → Kumanda yalnız emniyet pilotu yetkisidir; şartname", "soluk")
            self._logla("    gereği manuel müdahale zaten uçuşu geçersiz kılar.", "soluk")
            self._ucus("RC YOK — OTONOM GÖREVE DEVAM (AUTO)", SARI)

            def rc_geri():
                self._logla("RC bağlantısı geri geldi — uçuş kipi değişmedi", "yesil")
                band_geri()
            self.kok.after(6000, rc_geri)
        elif kod == "yks":
            self.demo_durum["iha_hb"] = False
            self._logla("SENARYO · İHA↔YKS telsiz bağlantısı KESİLDİ", "sari")
            self._logla("  → İHA: tekrar gönderim + >3 sn'de güvenli bölgede", "soluk")
            self._logla("    LOITER; kesinti uzarsa OTONOM paraşütle iniş.", "soluk")
            self._ucus("BAĞLANTI KAYBI — GÜVENLİ BÖLGEDE LOITER", KIRMIZI)

            def yks_geri():
                self.demo_durum["iha_hb"] = True          # anahtar HER HÂLDE geri
                self._logla("İHA bağlantısı DÖNDÜ — göreve devam", "yesil")
                band_geri()
            self.kok.after(7000, yks_geri)
        elif kod == "ika":
            self.demo_durum["ika_hb"] = False
            self._logla("SENARYO · İKA bağlantısı KESİLDİ", "sari")
            self._logla("  → İKA failsafe (ika_receiver.py — GERÇEK davranış):", "soluk")
            self._logla("    GÜVENLİ DURMA; rota önbelleği KORUNUR.", "soluk")

            def ika_geri():
                self.demo_durum["ika_hb"] = True
                self._logla("İKA bağlantısı DÖNDÜ — kaldığı waypoint'ten devam", "yesil")
            self.kok.after(7000, ika_geri)
        elif kod == "bat":
            self.demo_durum["iha_bat"] = False       # T177: panel de DÜŞSÜN
            self._logla("SENARYO · Batarya KRİTİK (<%15)", "sari")
            self._logla("  → RTH + İHA-İB üzerinde OTONOM paraşüt inişi", "soluk")
            self._logla("    (manuel tetik -50 ceza; bu yüzden tetik otonom).", "soluk")
            self._ucus("KRİTİK BATARYA — RTH + OTONOM PARAŞÜT (İHA-İB)", KIRMIZI)

            def bat_geri():
                self.demo_durum["iha_bat"] = True
                self._logla("Batarya paketi değişti — telemetri normale döndü",
                            "yesil")
                band_geri()
            self.kok.after(7000, bat_geri)
        elif kod == "gnss":
            self.demo_durum["iha_gnss"] = False      # T177: uydu sayısı 0'a düşer
            self._logla("SENARYO · GNSS fix KAYBI", "sari")
            self._logla("  → Barometrik irtifa tutuşu + yeniden fix bekleme;", "soluk")
            self._logla("    süre kritikleşirse otonom paraşütle güvenli iniş.", "soluk")
            self._ucus("GNSS YOK — BAROMETRİK TUTUŞ, FIX BEKLENİYOR", SARI)

            def gnss_geri():
                self.demo_durum["iha_gnss"] = True
                self._logla("GNSS fix GERİ GELDİ — konum yeniden güncelleniyor",
                            "yesil")
                band_geri()
            self.kok.after(7000, gnss_geri)
        elif kod == "algi":
            self._logla("SENARYO · Görüntü işleme zaman aşımı (>30 sn tespit yok)", "sari")
            self._logla("  → Tarama deseni BİR KEZ yinelenir; yine yoksa YKS'ye", "soluk")
            self._logla("    'TESPİT YOK' bildirilir (yanlış yönlendirme yasak;", "soluk")
            self._logla("    rota sağlamlık süzgeci <3 waypoint'te göndermez).", "soluk")
            # D-383 (çürütücü): önceden bu senaryo demo_durum'a HİÇ
            # dokunmuyordu — bant "ALGI ZAMAN AŞIMI" derken karar_yas 0,5 sn
            # taze akmaya devam ediyor, ekran kendisiyle ÇELİŞİYORDU
            # (T177/D-323'ün yasakladığı örüntü). Artık algı anahtarı
            # kesilir: demo İHA'sı karar damgasını DONDURUR, karar_yas
            # büyür, tazelik kutusu ~5 sn'de BAYAT(algı) olur — A2'nin
            # yakaladığı gerçek durum tatbikatta da görünür.
            self.demo_durum["iha_algi"] = False

            def algi_geri():
                self.demo_durum["iha_algi"] = True   # anahtar HER HÂLDE geri
                self._logla("ALGI GERİ GELDİ — karar üretimi sürüyor", "yesil")
                band_geri()
            self._ucus("ALGI ZAMAN AŞIMI — TARAMA YİNELENİYOR", SARI)
            self.kok.after(9000, algi_geri)

    def _rota_analiz(self, m):
        """Segment bazlı eksen değişimi tablosu: Δx/Δy, uzunluk, yön, dönüş."""
        wps = m.get("waypoints") or []
        satirlar = []
        onceki = (0.0, 0.0)                 # referans noktasına göre yerel
        onceki_yon = None
        toplam = yanal = 0.0
        keskin = 0.0
        for i, (x, y) in enumerate(wps, 1):
            dx, dy = x - onceki[0], y - onceki[1]
            uz = math.hypot(dx, dy)
            toplam += uz
            yanal += abs(dx)
            yon = math.degrees(math.atan2(dx, dy))       # 0° = kuzey (ileri)
            kimden = "ref " if i == 1 else f"wp{i-1:<2}"
            satir = (f"{kimden}→wp{i:<2} Δx{dx:+5.1f} Δy{dy:+5.1f} · "
                     f"{uz:4.1f} m · yön {yon:+6.1f}°")
            if onceki_yon is not None:
                donus = (yon - onceki_yon + 180) % 360 - 180
                keskin = max(keskin, abs(donus))
                satir += f" · dönüş {donus:+5.1f}°"
            satirlar.append(satir)
            onceki, onceki_yon = (x, y), yon
        if satirlar:
            satirlar.append(f"TOPLAM {toplam:.1f} m yol · yanal |Δx| {yanal:.1f} m "
                            f"· en keskin dönüş {keskin:.0f}°")
        self.rota_metin.config(state="normal")
        self.rota_metin.delete("1.0", "end")
        self.rota_metin.insert("end", "\n".join(satirlar) or "rota verisi yok")
        self.rota_metin.config(state="disabled")

    def _ucus(self, metin, renk):
        self.lbl_ucus.config(text=f"İHA UÇUŞ DURUMU: {metin}", fg=renk)

    def _ucus_normal(self):
        self.lbl_ucus.config(text="İHA UÇUŞ DURUMU: OTONOM GÖREV (AUTO)", fg=YESIL)

    # ── Canlı algı: v3 modeliyle GERÇEK çıkarım ──────────────────────────────
    # Karar zinciri sahadakiyle AYNI: codes/rpi_inference.py'nin get_masks +
    # analyze_path fonksiyonları kullanılır (kopya algoritma yok).
    # `kompozit` açılış kaynağı olarak korunur. T64: şartnameye sadık T60 kadraj
    # kümesi ve tek gerçek arena karesi ayrıca seçilebilir. `drone` bir otopark,
    # `gemini`/`val` afet/yol fotoğrafıdır; domain boşluğunu hakeme göstermek için
    # listede kalırlar (REVIEW_LOG D-53/D-90).
    # 🔴 T187 (D-324, kullanici istegi "dji klasorundeki yeni verileri de test
    # klasorune alabilirsin"): DJI kareleri RescueNet `test` kumesinin ICINE
    # bosaltilmadi — o kume 305 karelik bir OLCUM kumesidir ve karistirmak onu
    # kirletirdi. Bunun yerine AYRI ve ADI BELLI bir kaynak eklendi.
    # ⚠ Ne oldugu ekranda YAZILI: bu kareler GECE cekimi (medyan parlaklik 19),
    # NADIR DEGIL (yerden/egik) ve icinde arena/koridor/bariyer YOK. Rota
    # BEKLENMEZ; olcek de yoktur (OLCEK_YOK dogru davranistir).
    ALGI_KAYNAKLAR = ("kompozit", "arena_kadraj", "arena_gercek",
                      "drone", "dji_gece", "gemini", "test", "val")
    # 🔴 T173 (D-322) — ACILIS KAYNAGI ARTIK KABUL KUMESIDIR.
    # Ekran, uretim modelinin KABUL EDILDIGI dagilimda acilmalidir. Bu, D-116/5'in
    # dersidir: hakem ekrani modeli KABUL EDILMEDIGI bir dagilimda gosterirse,
    # gorulen sey sertifikaladigimiz sey DEGILDIR.
    # Olculdu: `arena_kadraj` (kabul kumesi) 12/12 rota veriyor (D-298 SS1);
    # `kompozit` 9/9 karede rota VERMIYOR (D-298/D-302) cunku arka plani bir
    # OTOPARKTIR ve uretim modeli araclari engel gorur — o kurgu v21'in gevsek
    # zemin maskesiyle kurulmustu (T173 olcumu: v36 ile 67 karenin yalnizca 3'u
    # kurulabiliyor ve onlar da rota vermiyor; 90 derece dondurme de cozmuyor).
    # `kompozit` LISTEDE KALIR (secilebilir, tanisal deger tasir); yalnizca
    # ACILIS kaynagi degisti.
    ALGI_VARSAYILAN_KAYNAK = "arena_kadraj"
    # T76 (mimar karari, REVIEW_LOG D-115): uretim modeli v24 -> v27.
    # ⚠ SURUM ADI ARTIK BURAYA YAZILMIYOR. T58'de bu satir CIPLAK SABITTI ve
    # zincirin dort ucu (paket, manifest, iki kilavuz) ELLE hizalanmak
    # zorundaydi. Ad artik KAYIT DEFTERINDEN turetilir (madde 16); saha kodu da
    # ayni defteri okur, boylece ikisi TANIM GEREGI ayni modeli gosterir.
    ALGI_MODEL_DOSYA = _uretim_modeli_adi()
    # T36: cikarim esigi URETIMDEN gelir. `codes/rpi_inference.py` `run_image`
    # yolunda predict esigi `--conf` argumaniyla verilir, varsayilani 0.30
    # (`:1116`). GUI kendi esigini SECMEZ; bu deger uretimin varsayilanidir ve
    # `tests/test_yks_gui_uretim_hizasi.py` onu kaynaktan okuyup kilitler —
    # uretim varsayilani degisirse test duser, ekran sessizce ayrismaz.
    ALGI_PREDICT_CONF = 0.30
    # Kompozit kume yer gercegi. SALT GOSTERIM: karar yoluna GIRMEZ (aksi hâlde
    # test kendi kendini dogrular). Bkz. test_beklenen_serit_karara_sizmiyor.
    ALGI_KOMPOZIT_DIZIN = ("data", "arena_kompozit")
    # T77 (kusur D-116/5): burada T60 kumesinin yolu CIPLAK yaziliydi ve model
    # v27'ye gecince kimse cevirmedi — ekran modeli KABUL EDILMEDIGI bir
    # dagilimda gosteriyordu. Yol artik kayit defterindeki `kabul_kumesi`
    # alanindan gelir; surum degisince kume de TEK YERDEN degisir.
    ALGI_ARENA_KADRAJ_KOKU = _kabul_kumesi_koku()
    ALGI_ARENA_GERCEK_DOSYA = (
        _PROJE_KOKU / "data" / "arena_referans" / "sartname_s9_arena.png")
    # 🔴 T86 · D-90: bu kaynaklarda TEK SKALER ÖLÇEK GEÇERSİZDİR — eğik arena
    # bakışında 2,0 m hedef yatayda ~72 px, dikeyde ~38 px'tir. `_kaynak_olcegi`
    # orada ölçeği "bilmiyorum" diye değil **REDDEDEREK** döndürür. Ölçek
    # kâhininin 3. katmanı bu reddi EZMEMELİDİR: sahnede araç görülse bile
    # oradan tek bir mpp türetmek, D-90'ın ölçtüğü geometrik gerçeği yok
    # saymaktır. Yokluk ile RET aynı şey değildir.
    ALGI_SKALER_OLCEK_GECERSIZ = ("arena_gercek",)
    # T86: ölçek katman 3 dedektörünün SINIF düzeyindeki varsayılanı. `__init__`
    # ayrıca örnek düzeyinde kurar; sınıf düzeyinde de durmasının sebebi,
    # worker'ın `__init__` koşmadan kurulan örneklerle de sınanmasıdır
    # (tests/test_yks_gui_uretim_hizasi.py). Eksik öznitelik, ölçek katmanını
    # sessizce değil GÖRÜNÜR biçimde kapatmalı.
    _arac_modeli_durumu = None
    # T169 · §6.2: tespit tazeliginin SINIF DUZEYI varsayilanlari. Ornek
    # duzeyinde `__init__` de kurar; burada da durmasinin sebebi `_arac_modeli_durumu`
    # ile AYNI: bu sinif, `__init__` kosmadan kurulan orneklerle de sinaniyor
    # (tests/test_ika_go_ackli_tekrar.py, test_yks_gui_aktarim_zamani.py).
    # Eksik oznitelik AttributeError ile patlamak yerine "zaman damgasi YOK"
    # demeli; damga yoksa yaslandirma HICBIR SEY yapmaz (eski davranis birebir).
    rota_zaman = None
    tespit_bayat = False
    # T171: telemetri sozlugu de sinif duzeyinde. `__init__` kosmadan kurulan
    # orneklerde (testler) irtifa notu AttributeError ile patlamak yerine
    # "irtifa bilinmiyor" demeli — bu, notun kendi sozlesmesidir.

    def _algi_gorseller(self):
        kok_dizin = Path(__file__).resolve().parents[1]
        kaynaklar = {
            "kompozit": kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "images",
            # Kök altında aynı adlı 24 `_onizleme` karesi de var. Yalnız gerçek
            # veri bölümleri listelenir; önizlemeye manifest ölçeği bağlanamaz.
            "arena_kadraj": Path(self.ALGI_ARENA_KADRAJ_KOKU) / "images",
            "arena_gercek": Path(self.ALGI_ARENA_GERCEK_DOSYA),
            "gemini": kok_dizin / "test_images" / "gemini",
            "test": kok_dizin / "test_images" / "test" / "images",
            "val": kok_dizin / "dataset" / "rescuenet_yolo" / "images" / "val",
            "drone": kok_dizin / "data" / "raw_frames",
            # T187: gercek DJI ucus kareleri (2026-08-20 gece prova oturumu).
            "dji_gece": kok_dizin / "data" / "dji_prova_kareler",
        }
        yol = kaynaklar[self.algi_kaynak]
        uzantilar = (".png", ".jpg", ".jpeg")
        if yol.is_file():
            return [yol] if yol.suffix.lower() in uzantilar else []
        if not yol.is_dir():
            return []
        return sorted(p for p in yol.rglob("*") if p.suffix.lower() in uzantilar)

    def _kompozit_yer_gercegi(self):
        """Kompozit kümenin manifest'inden {dosya_adı: beklenen_açık_şerit}.

        SALT GÖSTERİM. Bu değer karar yoluna GİRMEZ — girseydi ekran kendi
        beklentisini doğrulamış olurdu (D-15 sınıfı vakum kapı).

        Fail-closed: manifest okunamazsa sessizce boş dönmez, hatayı yükseltir;
        çağıran hatayı hakem günlüğüne yazar. "Yer gerçeği yok" ile "yer
        gerçeği okunamadı" ekranda aynı görünemez.
        """
        import json
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        mf = kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "manifest.json"
        veri = json.loads(mf.read_text(encoding="utf-8"))
        gercek = {}
        for ornek in veri.get("ornekler", []):
            arena = ornek.get("arena")
            cikti = ornek.get("cikti")
            if not arena or not cikti:
                continue
            serit = arena.get("acik_serit")
            if serit is not None:
                gercek[pathlib.Path(cikti).name] = int(serit)
        if not gercek:
            raise ValueError(f"manifest'te acik_serit taşıyan örnek yok: {mf}")
        return gercek

    def _kompozit_olcekleri(self):
        """Kompozit kümenin manifest'inden {dosya_adı: mpp}.

        T44 · Halka 5: ekran, ölçeği kaynağından okur. Kompozit küme
        `arena.mpp` taşır (kontrollü kompozit varsayımı — gerçek kamera
        ölçümü DEĞİL, manifest kendi böyle beyan ediyor).

        Fail-closed: manifest okunamaz/bozuksa yükseltir; çağıran hatayı
        hakem günlüğüne yazar ve ölçeksiz sayar. Sessiz varsayılan YOK.
        """
        import json
        import pathlib
        kok_dizin = pathlib.Path(__file__).resolve().parents[1]
        mf = kok_dizin.joinpath(*self.ALGI_KOMPOZIT_DIZIN) / "manifest.json"
        veri = json.loads(mf.read_text(encoding="utf-8"))
        olcekler = {}
        for ornek in veri.get("ornekler", []):
            arena = ornek.get("arena")
            cikti = ornek.get("cikti")
            if not arena or not cikti:
                continue
            mpp = arena.get("mpp")
            if olcek_gecerli_mi(mpp):
                olcekler[pathlib.Path(cikti).name] = float(mpp)
        if not olcekler:
            raise ValueError(f"manifest'te gecerli mpp tasiyan ornek yok: {mf}")
        return olcekler

    def _arena_kadraj_olcekleri(self):
        """T60 manifest'inden güvenli ``{tam_görsel_yolu: mpp|None}`` haritası.

        Manifest yolları küme köküne göre ``images/train|val/...`` biçimindedir.
        Basename eşlemesi yapılmaz: `_onizleme` aynı adları taşır ve ileride
        train/val adları da çakışabilir. Mutlak, kök dışına taşan veya yinelenen
        yollar fail-closed reddedilir. Eksik/geçersiz mpp ise ``None`` kalır;
        hiçbir ölçek uydurulmaz.
        """
        import json

        kok = Path(self.ALGI_ARENA_KADRAJ_KOKU).resolve()
        gorsel_koku = (kok / "images").resolve()
        mf = kok / "manifest.json"
        veri = json.loads(mf.read_text(encoding="utf-8"))
        ornekler = veri.get("ornekler")
        if not isinstance(ornekler, list) or not ornekler:
            raise ValueError(f"manifest'te örnek listesi yok: {mf}")

        olcekler = {}
        for sira, ornek in enumerate(ornekler):
            if not isinstance(ornek, dict):
                raise ValueError(f"manifest örneği sözlük değil: sıra={sira}")
            cikti = ornek.get("cikti")
            if not isinstance(cikti, str) or not cikti.strip():
                raise ValueError(f"manifest çıktısı yok/geçersiz: sıra={sira}")
            goreli = Path(cikti)
            if goreli.is_absolute():
                raise ValueError(f"manifest çıktısı mutlak olamaz: {cikti}")
            if ".." in goreli.parts:
                raise ValueError(f"manifest çıktısı üst dizine çıkamaz: {cikti}")
            tam = (kok / goreli).resolve()
            try:
                tam.relative_to(gorsel_koku)
            except ValueError as exc:
                raise ValueError(
                    f"manifest çıktısı images dışına taşıyor: {cikti}") from exc
            if tam in olcekler:
                raise ValueError(f"manifest çıktısı yinelenmiş: {cikti}")
            arena = ornek.get("arena")
            mpp = arena.get("mpp") if isinstance(arena, dict) else None
            olcekler[tam] = float(mpp) if olcek_gecerli_mi(mpp) else None
        return olcekler

    def _kaynak_olcegi(self, yol):
        """Kaynağa göre `(mpp, açıklama)`. Ölçek yoksa `(None, sebep)`.

        ⚠ **Ölçek uydurulmaz.** T60 kadraj kümesi manifest ölçeğini taşır. Eğik
        gerçek arena karesi ile `drone` / `gemini` / `val` / `test` kümelerinde
        güvenilir tek skaler ölçek yoktur. Orada `mpp=None` dönmek "kısıt yok"
        değil, `rota_olcek_reddi` ile `OLCEK_YOK` demektir (CONTRACTS §5.2/1).
        """
        if self.algi_kaynak == "arena_gercek":
            return None, ("D-90: eğik arena bakışında 2,0 m HB yatayda yaklaşık "
                          "72 px, dikeyde yaklaşık 38 px; tek skaler mpp "
                          "geçersiz — yerel rota kararı üretilmez")
        if self.algi_kaynak == "arena_kadraj":
            try:
                olcekler = self._arena_kadraj_olcekleri()
            except (OSError, TypeError, ValueError) as exc:
                return None, (f"kabul kümesi manifesti okunamadı/geçersiz: "
                              f"{type(exc).__name__}: {exc} — "
                              "ölçek uydurulmadı")
            secili = Path(yol).resolve()
            if secili not in olcekler:
                return None, (f"manifest'te seçili görsel yok: {secili.name} "
                              "— ölçek uydurulmadı")
            mpp = olcekler[secili]
            if mpp is None:
                return None, (f"manifest'te {secili.name} için mpp yok/geçersiz "
                              "— ölçek uydurulmadı")
            return mpp, ("kabul kümesi manifesti "
                         "(kontrollü sentetik kadraj varsayımı)")
        if self.algi_kaynak != "kompozit":
            return None, (f"{self.algi_kaynak} kümesinde telemetri/ölçek yok "
                          "— irtifa+FOV bilinmiyor")
        mpp = self._kompozit_olcekleri().get(yol.name)
        if mpp is None:
            return None, f"manifest'te {yol.name} için mpp yok"
        return mpp, "manifest (kontrollü kompozit varsayımı)"

    def _arac_modeli(self):
        """Ölçek katman 3 dedektörünü GEREKİNCE yükle ve önbellekle (T86).

        Ağırlık 53 MB'dir; `arena_kadraj` gibi manifest ölçeği taşıyan
        kaynaklarda HİÇ yüklenmez. Yüklenemezse `None` döner ve sebep hakem
        günlüğüne yazılır — sessizce ölçeksiz kalınmaz.
        """
        if self._arac_modeli_durumu is not None:
            return self._arac_modeli_durumu[0]
        yol, sebep = _arac_dedektoru_yolu()
        if yol is None:
            self._arac_modeli_durumu = (None, sebep)
            self.algi_kuyruk.put(("log", f"ÖLÇEK katman 3 KAPALI: {sebep}"))
            return None
        try:
            from ultralytics import YOLO
            model = YOLO(str(yol), task="obb")
        except Exception as exc:                  # fail-closed: ölçek uydurma
            self._arac_modeli_durumu = (
                None, f"yüklenemedi: {type(exc).__name__}: {exc}")
            self.algi_kuyruk.put(("log",
                f"ÖLÇEK katman 3 YÜKLENEMEDİ: {type(exc).__name__}: {exc}"))
            return None
        self._arac_modeli_durumu = (model, sebep)
        self.algi_kuyruk.put(("log", f"ÖLÇEK katman 3 hazır — {sebep}"))
        return model

    def gorunum(self, ad):
        if ad not in ("harita", "algi", "kamera"):
            raise ValueError(f"bilinmeyen görünüm: {ad!r}")
        self.gorunum_adi = ad
        # T81: kutu GÖRÜNÜMÜN kaynağından beslenir — geçişte yeniden çizilir.
        # Harita görünümüne dönüldüğünde protokol durumu OLDUĞU GİBİ görünür;
        # canlı algı görünümünde telsiz değeri EKRANA BASILMAZ.
        self._kutu_ciz()
        if ad == "harita":
            self.algi_cerceve.pack_forget()
            self.kamera_cerceve.pack_forget()
            self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True)
            self.btn_gor_harita.config(fg=BG, bg=YESIL)
            self.btn_gor_algi.config(fg=METIN, bg="#232e3a")
            self.btn_gor_kamera.config(fg=METIN, bg="#232e3a")
            self._harita_ciz()
        elif ad == "algi":
            self.harita.pack_forget()
            self.kamera_cerceve.pack_forget()
            self.algi_cerceve.pack(fill="both", expand=True)
            self.btn_gor_algi.config(fg=BG, bg=YESIL)
            self.btn_gor_harita.config(fg=METIN, bg="#232e3a")
            self.btn_gor_kamera.config(fg=METIN, bg="#232e3a")
            self._algi_iste()
        else:
            self.harita.pack_forget()
            self.algi_cerceve.pack_forget()
            self.kamera_cerceve.pack(fill="both", expand=True)
            self.btn_gor_kamera.config(fg=BG, bg=YESIL)
            self.btn_gor_harita.config(fg=METIN, bg="#232e3a")
            self.btn_gor_algi.config(fg=METIN, bg="#232e3a")
            self._kamera_tazele()

    def _kamera_tazele(self):
        """LAN kamera snapshot'ını Tk ana döngüsünde sun; ağ I/O'su yapma."""
        istemci = getattr(self, "kamera_istemci", None)
        etiket = getattr(self, "lbl_kamera_img", None)
        bilgi = getattr(self, "lbl_kamera_bilgi", None)
        if etiket is None or bilgi is None:
            return
        if istemci is None:
            etiket.config(image="", text="KAMERA URL YOK — RAW görüntü kapalı",
                          fg=KIRMIZI)
            bilgi.config(text="--kamera-url http://<JETSON_IP>:8080 verin · "
                               "video SiK üzerinden taşınmaz", fg=KIRMIZI)
            return
        try:
            snap = istemci.snapshot()
        except Exception as exc:
            snap = {"surum": None, "jpeg": None, "durum": "HATA",
                    "hata": f"istemci snapshot hatası: {type(exc).__name__}: {exc}",
                    "kare_yasi_s": None, "kaynak": self.kamera_url}
        jpeg = snap.get("jpeg")
        surum = snap.get("surum")
        if jpeg is not None and surum != self._kamera_surum:
            try:
                from PIL import Image, ImageOps, ImageTk
                resim = ImageOps.exif_transpose(Image.open(io.BytesIO(jpeg)))
                resim.thumbnail((S(660), S(430)), Image.Resampling.LANCZOS)
                self._kamera_foto = ImageTk.PhotoImage(resim.convert("RGB"))
                etiket.config(image=self._kamera_foto, text="", fg=METIN)
                self._kamera_surum = surum
            except Exception as exc:
                jpeg = None
                snap["hata"] = f"JPEG çözülemedi: {type(exc).__name__}: {exc}"
                snap["durum"] = "HATA"
        if jpeg is None:
            self._kamera_foto = None
            etiket.config(image="", text="KAMERA YOK — son kare kullanılmıyor",
                          fg=KIRMIZI)
        yas = snap.get("kare_yasi_s")
        yas_metin = "yaş YOK" if yas is None else f"kare yaşı {float(yas):.2f} sn"
        durum = str(snap.get("durum") or "BİLİNMİYOR")
        hata = snap.get("hata")
        metin = f"{durum} · {yas_metin} · {snap.get('kaynak') or self.kamera_url}"
        if hata:
            metin += f" · {hata}"
        bilgi.config(text=metin, fg=YESIL if jpeg is not None else KIRMIZI)

    def _algi_gorunumu_sart(self, ne):
        """ALGI gezinme komutlari yalniz ALGI gorunumunde anlamlidir.

        🔴 T181 (D-323): uc komut da `if self.gorunum_adi != "algi": return`
        ile SESSIZCE dusuyordu. Oysa uc dugme de (◀ Onceki · Sonraki ▶ ·
        Kaynak degistir) SOL PANELDE, yani harita gorunumunde de EKRANDA
        DURUYOR; basilinca hicbir sey olmuyordu — ayni sey K ve ok tuslari
        icin de gecerliydi. Izleyen icin bu "dugme bozuk" demektir.
        Sessiz sifir yasak: calismama NEDENI ve cikis yolu yazilir.
        """
        if self.gorunum_adi == "algi":
            return True
        self._logla(f"{ne} yalnız CANLI ALGI görünümünde çalışır — "
                    "V tuşu (veya CANLI ALGI düğmesi) ile geçin", "sari")
        return False

    def algi_sonraki(self):
        if not self._algi_gorunumu_sart("Sonraki ▶ (→)"):
            return
        self.algi_idx += 1
        self._algi_iste()

    def algi_onceki(self):
        if not self._algi_gorunumu_sart("◀ Önceki (←)"):
            return
        self.algi_idx -= 1
        self._algi_iste()

    def algi_kaynak_degistir(self):
        if not self._algi_gorunumu_sart("Kaynak değiştir (K)"):
            return
        sira = self.ALGI_KAYNAKLAR
        self.algi_kaynak = sira[(sira.index(self.algi_kaynak) + 1) % len(sira)]
        self.algi_idx = 0
        aciklama = {"kompozit": "kontrollü arena kompoziti — YER GERÇEĞİ var",
                    "arena_kadraj": "T60 şartname kadrajı — manifest ölçeği var",
                    "arena_gercek": ("tek gerçek arena karesi — eğik perspektif, "
                                      "tek skaler ölçek yok"),
                    "gemini": "arena tipi görseller",
                    "test": "takım test seti (test_images/test)",
                    "val": "RescueNet doğrulama seti",
                    "drone": "gerçek nadir drone kareleri (OTOPARK, arena değil)",
                    "dji_gece": ("kendi DJI uçuşumuz — 2026-08-20 GECE prova "
                                 "oturumu; nadir DEĞİL, arena/koridor/bariyer "
                                 "YOK, ölçek yok → rota BEKLENMEZ")
                    }[self.algi_kaynak]
        self._logla(f"ALGI kaynağı: {self.algi_kaynak} ({aciklama})", "mavi")
        self._algi_iste()

    def _algi_iste(self):
        if self.algi_mesgul:
            return
        gorseller = self._algi_gorseller()
        if not gorseller:
            self.lbl_algi_bilgi.config(
                text=f"Kaynak boş: {self.algi_kaynak} — "
                     "val için dataset/rescuenet_yolo üretilmiş olmalı")
            return
        yol = gorseller[self.algi_idx % len(gorseller)]
        self.algi_mesgul = True
        self.lbl_algi_bilgi.config(text=f"{yol.name} işleniyor… "
                                        + ("( modeli yükleniyor — ilk sefer "
                                           "birkaç sn)" if self.algi_model is None
                                           else ""))
        threading.Thread(target=self._algi_kos, args=(yol,), daemon=True).start()

    def _algi_kos(self, yol):
        """Arka plan iş parçacığı: v ile gerçek çıkarım + saha karar zinciri."""
        try:
            import pathlib
            import sys as _sys
            import cv2
            import numpy as np
            kok_dizin = pathlib.Path(__file__).resolve().parents[1]
            _sys.path.insert(0, str(kok_dizin / "codes"))
            from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,
                                       _preprocess, _rota_kararini_esikle,
                                       analyze_path, get_masks,
                                       kare_olcek_kahini)

            if self.algi_model is None:
                from ultralytics import YOLO
                model_yolu = kok_dizin / "models" / self.ALGI_MODEL_DOSYA
                self.algi_model = YOLO(str(model_yolu))
                import hashlib
                _h = hashlib.sha256()
                with open(model_yolu, "rb") as _fh:
                    for _blok in iter(lambda: _fh.read(1 << 20), b""):
                        _h.update(_blok)
                self.algi_kuyruk.put(("log",
                    f"{model_yolu.stem} modeli yüklendi: {model_yolu.name} "
                    f"(SHA {_h.hexdigest()[:8]})"))

            img = cv2.imread(str(yol))
            t0 = time.perf_counter()
            # ── ÜRETİM ALGI HATTI — GUI kendi hattını KURMAZ (T36 / madde 16) ──
            # `CONTRACTS.md` §11.2: Halka 3 (Çıkarım) ve Halka 4 (Maske) sahibi
            # `codes/rpi_inference.py`. Aşağıdaki sıra o dosyanın `run_image`
            # gövdesinin (:920-932) birebir aynısıdır ve parametreler oradan
            # okunur — çıplak sabit yazılmaz. Jetson saha paketi de bu dosyanın
            # BAYT-BİREBİR kopyasıdır, yani hakem ekranı sahanın gerçekten
            # koştuğu yolu gösterir.
            #
            # `simulation/scripts/iha_perceive.py` bilerek KULLANILMAZ: §11.1/1
            # `simulation/` altındaki hiçbir dosyanın halka sahibi olmasını
            # yasaklar ve o dosya saha paketinde hiç yoktur. İki üretim yolu
            # 67 gerçek karenin 13'ünde birbirinden ayrışıyor (REVIEW_LOG D-58);
            # hakem ekranı sözleşmenin sahip yazdığı yola hizalanır.
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            sonuc = self.algi_model.predict(
                small, imgsz=INFER_SIZE, conf=self.ALGI_PREDICT_CONF,
                verbose=False)
            maskeler = get_masks(sonuc, h, w)
            maskeler = _maskeleri_icerige_kirp(maskeler, icerik)
            trav, blok = maskeler[0], maskeler[1]
            ms = (time.perf_counter() - t0) * 1000
            cikarim = "üretim (rpi_inference)"
            # Ham zemin maskesini koru: §6.4'te MASKE_YOK, modelin hiç zemin
            # ÜRETMEMESİ demektir. Engeli girdiden burada oyarsak model zemin
            # bulmuş olsa bile tam örtülen sahneyi yanlış MASKE_YOK raporlarız.
            trav_serbest = trav.copy()
            trav_serbest[blok > 0] = 0
            # ── ÖLÇEK (Halka 5) — T44 · CONTRACTS §5 ───────────────────────
            # T43 ölçek kapısını üç GÖREV çağrı yerine koydu; GUI onları
            # çağırmıyordu ve 16 otopark karesinin 16'sında ekran karar
            # verirken üretim `OLCEK_YOK` diyordu. İki ayrı kusur:
            #   (1) hakeme SİSTEM KISITI sahne kusuru gibi gösteriliyordu;
            #   (2) C-uzayı ekrana hiç ulaşmıyordu (mpp yok -> r_gerekli_px yok).
            # Üretimin kapısı KOPYALANMAZ, `rota_olcek_reddi` çağrılır.
            beyan, olcek_notu = None, None
            try:
                beyan, olcek_notu = self._kaynak_olcegi(yol)
            except Exception as _oe:      # fail-closed: sessiz varsayılan YOK
                olcek_notu = f"manifest okunamadı: {type(_oe).__name__}: {_oe}"
                self.algi_kuyruk.put(("log",
                    f"⚠ ÖLÇEK OKUNAMADI: {olcek_notu} — ölçeksiz sayılıyor, "
                    "rota yayınlanmaz"))
            # T86: kaynağın kendi beyanı ÖLÇEK KÂHİNİNİN 1. KATMANIDIR. Beyan
            # yoksa üretimin çözücüsü katman 2/3'ü dener — çözücü KOPYALANMAZ,
            # `codes/rpi_inference.py` içindeki fonksiyon çağrılır (madde 16).
            _katman3_yasak = (self.algi_kaynak
                              in self.ALGI_SKALER_OLCEK_GECERSIZ)
            kahin = kare_olcek_kahini(
                beyan, None, icerik, bgr=img,
                arac_modeli=(None if (olcek_gecerli_mi(beyan) or _katman3_yasak)
                             else self._arac_modeli()))
            if _katman3_yasak:
                # Sessiz düşüş yasak: katmanın neden çalıştırılmadığı yazılır.
                kahin["denenen"] = [
                    (k, "bu kaynakta tek skaler ölçek GEÇERSİZ (D-90) — "
                        "katman ÇALIŞTIRILMADI" if k == OLCEK_KAYNAK_ARAC else n)
                    for k, n in kahin["denenen"]]
            mpp = kahin["mpp"]
            if kahin["kaynak"] == OLCEK_KAYNAK_TELEMETRI and olcek_notu:
                # Kaynağın KENDİ açıklaması ("kabul kümesi manifesti…") daha
                # bilgilidir; kâhinin genel metni onun yerini almaz.
                kahin["detay"] = olcek_notu
            olcek_beyani = olcek_kaynak_metni(kahin)
            if kahin["kaynak"] is None and olcek_notu:
                # ⚠ Kâhinin katman dökümü, kaynağın KENDİ gerekçesinin yerine
                # GEÇMEZ. `arena_gercek` için ekran D-90'ı anlatır ("eğik arena
                # bakışında 2,0 m HB yatayda ~72 px…"); bu cümle kaybolursa
                # hakem sistem kısıtını sahne kusuru sanır. İkisi de yazılır.
                olcek_beyani = f"{olcek_notu} · {olcek_beyani}"
            olcek_reddi = rota_olcek_reddi(mpp)

            # Karar üretimin KENDİ çağrısıdır; `return_clean/reason/olcum`
            # yalnız GÖSTERİM için ek dönüşlerdir — aynı saf fonksiyon, aynı
            # girdi, aynı karar. İkinci bir predict yapılmaz.
            (ham_yol, guven, ham_wps, koridor,
             karar_reddi, rota_olcumu) = analyze_path(
                trav, icerik=icerik, engel_mask=blok, mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True,
                olcek_kaynagi=kahin["kaynak"])
            # ONCELIK (CONTRACTS SS6.4/3): YAPISAL ret ezilmez. `analyze_path`
            # zaten reddettiyse sebebi KORUNUR — olcek eksikligi bir yapilandirma
            # boslugu, `ZEMIN_MASKESI_SUPHELI` ise ALGI ARIZASIDIR; hakeme
            # gosterilmesi gereken daha derin olandir.
            if olcek_reddi is not None and karar_reddi is None:
                # Ölçek yoksa gövde açıklığı doğrulanamaz -> rota YAYINLANMAZ.
                ham_yol, guven, ham_wps = None, 0.0, []
                karar_reddi = olcek_reddi
            # K-B üretimin kendi eşikleyicisiyle uygulanır — kopya eşik yok.
            yol_no, guven, wps, karar_reddi = _rota_kararini_esikle(
                ham_yol, guven, ham_wps, karar_reddi)

            # Görselleştirme İLKESİ: yalnızca kararın KULLANDIĞI temiz koridor
            # basılır (ham maskedeki gürültü blobları çizilmez — onlar kararı
            # zaten etkilemiyor). Koridor ORİJİNAL renkte kalır; geri kalan her
            # yer KIRMIZI (geçilemez), tespitli moloz KOYU kırmızı; sınır +
            # rota SARI. Yeşil kullanılmaz.
            gorsel = sq.copy()
            kirmizi = np.zeros_like(sq)
            kirmizi[:] = (40, 40, 210)                      # BGR kırmızı
            acik_ton = cv2.addWeighted(sq, 0.45, kirmizi, 0.55, 0)
            koyu_ton = cv2.addWeighted(sq, 0.20, kirmizi, 0.80, 0)
            maske_var = bool(np.any(trav_serbest) or np.any(blok))
            gosterim = ("segmentasyon maskesi (rota değil)"
                        if maske_var else "maske yok")
            if yol_no is not None and wps:
                # SÜRÜŞ KORİDORU: rota merkez hattı ± ölçülen yol yarıçapı
                # (distance transform medyanı), geçilebilir alanla kesişik —
                # İKA'nın gerçekten süreceği bant. Bilgi satırında etiketli.
                # Tamami gecilebilir bir maskede OpenCV, goruntu disinda
                # sifir sinir gormedigi icin FLT_MAX dondurebilir. Bu deger
                # ``int(median)`` ile cizgi kalinligina cevrilince ALGİ worker'i
                # sessizce dusuruyordu. Goruntu disini kapali sayan 1 px cerceve
                # hem geometrik olarak dogru hem de mesafeyi sonlu tutar.
                sinirli_koridor = cv2.copyMakeBorder(
                    koridor, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
                dist = cv2.distanceTransform(
                    sinirli_koridor, cv2.DIST_L2, 5)[1:-1, 1:-1]
                yarich = [dist[py, px] for (px, py) in wps if dist[py, px] > 0]
                yr = int(np.median(yarich)) if yarich else max(8, w // 20)
                yr = max(1, min(yr, max(1, min(h, w) // 2)))
                band = np.zeros((h, w), np.uint8)
                cv2.polylines(band, [np.array(wps, np.int32)], False, 1,
                              thickness=max(4, 2 * yr))
                band &= koridor
                gorsel[band == 0] = acik_ton[band == 0]     # bant dışı → kırmızı
                gorsel[blok > 0] = koyu_ton[blok > 0]       # moloz → koyu kırmızı
                # bant sınırı: yumuşatılmış, sadeleştirilmiş SARI kontur
                yumusak = cv2.GaussianBlur(band * 255, (0, 0),
                                           max(2.0, w / 500))
                yumusak = (yumusak > 127).astype(np.uint8)
                konturlar, _ = cv2.findContours(yumusak, cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
                for k in konturlar:
                    k = cv2.approxPolyDP(k, 0.002 * cv2.arcLength(k, True), True)
                    cv2.drawContours(gorsel, [k], -1, (0, 220, 255),
                                     max(3, w // 250))
            else:
                # Rota yokken segmentasyon yine görünür kalır: hakem modelin
                # maske üretip üretmediğini rota kararından AYRI görebilmelidir.
                # Mavi ton yalnız maske kanıtıdır; sarı rota/waypoint çizilmez.
                if maske_var:
                    maske_rengi = np.zeros_like(sq)
                    maske_rengi[:] = (210, 130, 45)
                    maske_ton = cv2.addWeighted(
                        sq, 0.55, maske_rengi, 0.45, 0)
                    gorsel[trav_serbest > 0] = maske_ton[trav_serbest > 0]
                    gorsel[blok > 0] = koyu_ton[blok > 0]
                # TESPİT/ROTA YOK: görüntüyü sele boğma — dürüst uyarı bandı bas
                bant_h = max(60, h // 10)
                gorsel[:bant_h] = cv2.addWeighted(
                    sq[:bant_h], 0.25, kirmizi[:bant_h], 0.75, 0)
                ret_metin = (f"ROTA YOK: {karar_reddi[0]}"
                             if karar_reddi else
                             "ACIK YOL TESPIT EDILEMEDI")
                cv2.putText(gorsel, ret_metin + " (guvenli: rota gonderilmez)",
                            (16, int(bant_h * 0.48)),
                            cv2.FONT_HERSHEY_SIMPLEX, max(0.6, w / 1800),
                            (255, 255, 255), max(1, w // 900))
                maske_metin = ("SEGMENTASYON MASKESI (ROTA DEGIL)"
                               if maske_var else "SEGMENTASYON MASKESI YOK")
                cv2.putText(gorsel, maske_metin,
                            (16, int(bant_h * 0.82)),
                            cv2.FONT_HERSHEY_SIMPLEX, max(0.55, w / 1900),
                            (255, 255, 255), max(1, w // 1000))
            if yol_no is not None and wps:
                gosterim = "sürüş koridoru"
            # şerit sınırları — letterbox İÇERİK kutusundan (§8). Tuvalden
            # (w//3) çizmek dolgu kadar kaydırır ve ekranda gösterilen şerit
            # `analyze_path`'in kullandığı şeritle örtüşmezdi.
            _ix0, _iy0, _iw, _ih = icerik
            for _k in (1, 2):
                _x = int(_ix0 + _k * _iw / 3.0)
                cv2.line(gorsel, (_x, _iy0), (_x, _iy0 + _ih),
                         (110, 110, 110), 1)
            if wps:
                pts = np.array(wps, dtype=np.int32)
                cv2.polylines(gorsel, [pts], False, (0, 220, 255), max(2, w // 300))
                for (px, py) in wps:
                    cv2.circle(gorsel, (px, py), max(3, w // 150), (0, 220, 255), -1)
                # Kalin sari cizgi merkez hatti guvenli olsa bile arac
                # konturuna tasabilir. Engel katmanini en son basarak arac
                # etiketini rota cizgisinin altinda birakma.
                if yol_no is not None:
                    gorsel[blok > 0] = koyu_ton[blok > 0]

            trav_oran = 100.0 * trav_serbest.mean()
            blok_oran = 100.0 * blok.mean()
            karar = (f"{yol_no}·{ROAD_LABEL[yol_no].upper()}" if yol_no else
                     (f"ROTA YOK · {karar_reddi[0]}" if karar_reddi
                      else "TESPİT YOK"))
            try:
                guven_sayi = float(guven)
                if isinstance(guven, bool) or not math.isfinite(guven_sayi):
                    raise ValueError("gecersiz rota guveni")
                # K-B sinirinda iki hane, 0.199 gibi bir reddi 0.20 diye
                # gosterip operatoru yaniltir. Sozlesme esigi de uc hanelidir.
                guven_metin = f"{guven_sayi:.3f}"
            except (TypeError, ValueError, OverflowError):
                # Fail-closed guven reddi, hata metnini gosterirken tekrar
                # bicimlendirme istisnasiyla worker'i dusurmemeli.
                guven_metin = repr(guven)
            bilgi = (f"{self.algi_kaynak}/{yol.name} → karar: {karar} · "
                     f"güven {guven_metin} · {ms:.0f} ms · çıkarım: {cikarim} · "
                     f"predict conf {self.ALGI_PREDICT_CONF:.2f}"
                     + f" · traversable %{trav_oran:.0f} · blocked %{blok_oran:.0f}"
                       f" · gösterim: {gosterim} · model: {self.ALGI_MODEL_DOSYA}")
            if self.algi_kaynak == "kompozit":
                # YER GERÇEĞİ — yalnızca GÖSTERİM. Karar zaten yukarıda
                # verilmiştir; bu satır onu değiştirmez, yalnız hakemin
                # "sistem 2 dedi, beklenen 2" diye görmesini sağlar.
                try:
                    _beklenen = self._kompozit_yer_gercegi().get(yol.name)
                except Exception as _e:      # fail-closed: sessiz boş GÖSTERME
                    self.algi_kuyruk.put(("log",
                        f"⚠ KOMPOZİT YER GERÇEĞİ OKUNAMADI: "
                        f"{type(_e).__name__}: {_e} — beklenen şerit "
                        "gösterilemiyor (karar bundan etkilenmez)"))
                    bilgi += " · beklenen şerit: OKUNAMADI"
                else:
                    if _beklenen is None:
                        bilgi += " · beklenen şerit: manifest'te YOK"
                    else:
                        _uyum = ("UYUMLU" if yol_no == _beklenen
                                 else ("ÇEKİMSER" if yol_no is None
                                       else "UYUMSUZ"))
                        bilgi += (f" · beklenen şerit {_beklenen}"
                                  f" → {_uyum}")
                        # T36b · D-302 — GÖSTERİM DOĞRULUĞU. Bu kümenin yer
                        # gerçeği, ham karede GÖRÜNMEYEN geometrik bir kurgudur
                        # (otopark çekimine yapıştırılmış arena koridoru;
                        # ölçüldü: D-298 §3, `results/gece_20260826/
                        # kompozit_panel.png`). Model o koridoru üretemez ve
                        # ÜRETMEMELİDİR de — asfaltı geçilebilir, araçları engel
                        # işaretlemesi DOĞRU davranıştır. Ölçüldü (D-302,
                        # `results/t36b/olcum.json`): yer gerçeği maskesiyle
                        # algoritma 8/9 doğru; MODEL maskesiyle 0/9. Bu satır
                        # olmadan hakem "ÇEKİMSER" görüp sistemi arızalı sanar.
                        bilgi += (" · ⚠ bu kümede yer gerçeği GEOMETRİK "
                                  "KURGUDUR (ham karede görünmez) — uyum ALGI "
                                  "başarısının ölçütü DEĞİLDİR (D-298/D-302)")
            # T48 — ZEMİN MASKESİ ŞÜPHELİ: hakem sistemin NEDEN karar
            # vermediğini görmeli. Eşik sözleşmeden okunur, çıplak yazılmaz.
            if karar_reddi is not None                     and karar_reddi[0] == ZEMIN_MASKESI_SUPHELI_SEBEBI:
                _kap = 100.0 * zemin_kaplamasi(trav, icerik)
                bilgi += (f" · ⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %{_kap:.0f}"
                          f" (tavan %{100.0 * ZEMIN_KAPLAMA_TAVANI:.0f})")
            # ÖLÇEK KANITI: hakem "C-uzayı uygulandı mı" sorusunu ekrandan
            # cevaplayabilmeli. Ölçeksiz kip SESSİZ kalamaz (§5.2/3).
            # T86: ölçeğin HANGİ KATMANDAN geldiği ve güven çarpanı ekranda
            # yazılıdır — katman 3'ten gelen bir ölçek telemetriyle AYNI
            # güvende sunulamaz (D-126). Sessiz düşüş yasaktır: ölçek yoksa
            # hangi katmanın neden düştüğü tek tek yazılır.
            if mpp is not None and rota_olcumu is not None                     and rota_olcumu.get("r_gerekli_px"):
                bilgi += (f" · ölçek {mpp:.4f} m/px ({olcek_beyani})"
                          f" · gövde açıklığı {rota_olcumu['r_gerekli_px']:.1f} px"
                          " · C-uzayı UYGULANDI")
            else:
                bilgi += (f" · ölçek YOK ({olcek_beyani})"
                          " · C-uzayı UYGULANAMADI")
            if rota_olcumu is not None:
                # Kanıt satırı: güvenin NEREDEN geldiği ekranda görünür olmalı.
                n1, n2, n3 = rota_olcumu["seritler"]
                # T155: yayınlanan `road` artık GÖVDE kararıdır; darboğaz
                # şeridi TANI olarak kalır (ikisi ayrışırsa hakem görsün).
                bilgi += (f" · darboğaz {rota_olcumu['darbogaz_px']:.1f} px"
                          f" @ şerit {rota_olcumu['darbogaz_serit']} (tanı)"
                          f" · yayınlanan şerit {rota_olcumu['serit_karari']}"
                          f" · rota şerit dağılımı {n1}/{n2}/{n3} px")
                if rota_olcumu["cok_seritli"]:
                    bilgi += " · ⚠ ROTA ŞERİT DEĞİŞTİRİYOR (tek etiket eksik kalır)"
            if karar_reddi is not None:
                bilgi += f" · {karar_reddi[1]}"
            _ad = self.ALGI_MODEL_DOSYA.rsplit(".", 1)[0]
            if rota_olcumu is not None and rota_olcumu["cok_seritli"]:
                # Hakem bunu kaçırmamalı: tek `road` etiketi rotanın tamamını
                # anlatmıyor. Fail-closed değil — rota doğrulanmış, yalnız ADI
                # eksik; kararı yumuşatmadan görünür kılıyoruz (SS6.4/3).
                self.algi_kuyruk.put(("log",
                    f"⚠ ROTA ŞERİT DEĞİŞTİRİYOR: yayınlanan şerit "
                    f"{rota_olcumu['serit_karari']}, dağılım "
                    f"{rota_olcumu['seritler']} px (darboğaz şeridi "
                    f"{rota_olcumu['darbogaz_serit']}, tanı) — yayınlanan "
                    "`road` rotanın GÖVDESİNİ adlandırır, tamamını değil"))
            # T81: sağ paneldeki AÇIK YOL TESPİTİ kutusu için YAPISAL karar.
            # Bilgi METNİ ayrıştırılmaz — ayrıştırma sessizce bozulur ve kutu
            # yanlış değer gösterir; hakem onayı buna dayanır (§6.2).
            try:
                _guven_f = float(guven)
                if isinstance(guven, bool) or not math.isfinite(_guven_f):
                    _guven_f = None
            except (TypeError, ValueError, OverflowError):
                _guven_f = None
            self.algi_kuyruk.put(("sonuc", gorsel, bilgi,
                                  f"ALGI({_ad}) {self.algi_kaynak}/{yol.name} "
                                  f"→ {karar} "
                                  f"güven={guven_metin} · {ms:.0f} ms",
                                  {"yol_no": yol_no,
                                   "guven": _guven_f,
                                   "guven_metin": guven_metin,
                                   "ret": karar_reddi[0] if karar_reddi else None,
                                   "gerekce": karar_reddi[1] if karar_reddi else None,
                                   "kaynak": self.algi_kaynak,
                                   # T86: ölçeğin KATMANI karar nesnesinde de
                                   # taşınır — kutu telemetri ile araç
                                   # referansını aynı güvende göstermesin.
                                   "olcek_kaynagi": kahin["kaynak"],
                                   "olcek_carpani": kahin["guven_carpani"],
                                   "kare": yol.name}))
        except Exception as e:
            self.algi_kuyruk.put(
                ("hata", f"ALGI HATASI: {type(e).__name__}: {e}"))
        finally:
            self.algi_mesgul = False

    def _algi_sonucu_goster(self, gorsel_bgr, bilgi):
        import cv2
        from PIL import Image, ImageTk
        h, w = gorsel_bgr.shape[:2]
        hedef_w, hedef_h = S(660), S(430)
        olcek = min(hedef_w / w, hedef_h / h)
        yeni = cv2.resize(gorsel_bgr, (int(w * olcek), int(h * olcek)),
                          interpolation=cv2.INTER_AREA)   # keskin küçültme
        rgb = cv2.cvtColor(yeni, cv2.COLOR_BGR2RGB)
        self._algi_foto = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.lbl_algi_img.config(image=self._algi_foto, text="")
        self.lbl_algi_bilgi.config(text=bilgi)

    # ── Demo / SS kontrolleri ("hile tuşları") ───────────────────────────────
    def yeni_tespit(self):
        """(demo) Taze OPEN_ROUTE üret — hakem onay akışı baştan izlenebilir."""
        if not self.demo:
            return
        import random
        yol = random.choice((1, 2, 3))
        # A1: hakem haritasi `road` seridinin girisini semantik ankraj secer;
        # demo da saha gibi sifir YEREL ref ve o ankraja gore yerel rota yollar.
        wps, dy = [], 0.0
        for _ in (0.35, 0.55, 0.70, 0.82, 0.90, 0.96, 1.0, 1.0):
            wps.append([round(random.uniform(-1.2, 1.2), 1),
                        round(dy, 1)])
            dy += 5.6
        m = open_route(road=yol, conf=round(random.uniform(0.72, 0.97), 2),
                       ref_xy=list(YAYIN_REF_XY), waypoints=wps)
        self._logla(f"(demo) yeni tespit üretildi — yol {yol}", "mavi")
        # 🔴 T179 (D-323): uretilen cerceve YALNIZ ekrana enjekte ediliyordu;
        # IKA onu HIC gormuyordu, dolayisiyla K8'in istedigi "IKA ALDI" ACK
        # kaniti ASLA gelmiyor ve 2. onay asamasi KALICI kilitleniyordu.
        # Cerceve artik IKA'ya da GERCEK soketten gider — kanit yolu ayni.
        _ika = self.son_adr.get("ika") or self.sabit_adr.get("ika")
        if _ika is not None:
            try:
                self.link.send(encode(m), _ika)
            except Exception as exc:
                self._logla(f"(demo) İKA'ya iletilemedi: "
                            f"{type(exc).__name__}: {exc}", "sari")
        else:
            self._logla("(demo) İKA adresi henüz bilinmiyor — 2. onay için "
                        "İKA ACK kanıtı gelmeyebilir", "sari")
        self._mesaj_isle(m, ("127.0.0.1", self.link.port))

    def onay_sifirla(self):
        """(demo) Onay durumunu geri al — 'BEKLENİYOR' hali tekrar görüntülenir."""
        if not self.demo or not self.rota:
            return
        self.onaylandi = False
        self.tespit_onayli = False
        self.btn_onay.config(state="normal", bg=SARI,
                             text="1) TESPİTİ DOĞRULA (§2.2.3)")
        self.lbl_onay.config(text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
                                  "gönderimde (ACK yok)", fg=SARI)
        self._logla("(demo) hakem onayı sıfırlandı — akış baştan izlenebilir", "mavi")

    # ── Görev kontrol & kronometre (şartname süreleri + §2.2.5 kilidi) ───────
    def _dugum_adresini_ogren(self, dugum, adr):
        """Dinamik adresi öğren; CLI ile pinlenen hedefi asla ezme."""
        if adr is not None and dugum not in self.sabit_adr:
            self.son_adr[dugum] = adr

    def _ham_gonder(self, komut_mesaji):
        """Hazır komut mesajını (AYNI seq) taşıyıcıya ver — tekrarlar bunu kullanır."""
        hedef_dugum = komut_mesaji["hedef"]
        adr = self.son_adr.get(hedef_dugum)
        cmd = komut_mesaji["cmd"]
        mesaj = encode(komut_mesaji)
        try:
            if isinstance(self.link, SerialLink):
                self.link.send(mesaj)
            elif adr is not None and adr[1]:
                self.link.send(mesaj, adr)
            else:
                self._logla(
                    f"CMD GÖNDERİLEMEDİ → {hedef_dugum}: {cmd} — UDP adresi yok",
                    "kirmizi",
                )
                return False
        except (OSError, TypeError, ValueError) as exc:
            self._logla(
                f"CMD GÖNDERİLEMEDİ → {hedef_dugum}: {cmd} — {exc}", "kirmizi")
            return False
        return True

    def _cmd_gonder(self, cmd, hedef_dugum):
        komut_mesaji = command(cmd, hedef_dugum)
        if not self._ham_gonder(komut_mesaji):
            return False
        self._logla(f"CMD → {hedef_dugum}: {cmd}", "mavi")
        return komut_mesaji["seq"]

    # T180 (D-323): ucus surerken TEYITSIZ DISARM. Tek 'a' tusu ya da tek tik
    # ucan araca DISARM yolluyordu ve ekran ayni anda "OTONOM GOREV (AUTO)" ile
    # "DISARM — guvenli" diyordu. Modal pencere ACILMAZ (demo akisini kilitler);
    # bunun yerine IKI ADIMLI teyit: ilk basis uyarir, ikincisi gonderir.
    def _iha_havada_mi(self):
        """Heartbeat canli ve inis kaniti YOKSA arac havada sayilir."""
        # `__init__` kosmadan kurulan orneklerde (testler) oznitelik olmayabilir;
        # eksiklik "inis kaniti YOK" demektir, AttributeError degil.
        if getattr(self, "iha_landed_seq", None) is not None:
            return False
        t = (getattr(self, "son_hb", None) or {}).get("iha")
        return t is not None and (time.monotonic() - t) < ARM_DURUM_TAZELIK_S

    def _arm_durumu_taze_mi(self, simdi=None):
        """Pixhawk HEARTBEAT ARM durumu hâlâ güvenilir mi?"""
        simdi = time.monotonic() if simdi is None else float(simdi)
        damga = getattr(self, "arm_durum_zamani", None)
        return (damga is not None and type(getattr(self, "arm_acik", None)) is bool
                and 0.0 <= simdi - damga <= ARM_DURUM_TAZELIK_S)

    def _arm_ui_uygula(self):
        """ARM gerçeğini tek yerden çiz; bilinmeyen/bekleyen fail-closed."""
        btn = getattr(self, "btn_arm", None)
        etiket = getattr(self, "lbl_arm", None)
        firlat = getattr(self, "btn_firlat", None)
        if btn is None or etiket is None or firlat is None:
            return
        bekleyen = getattr(self, "arm_bekleyen_komut", None)
        if bekleyen:
            btn.config(state="disabled", bg=SARI,
                       text=f"{bekleyen} — ACK + ARAÇ DURUMU BEKLENİYOR")
            etiket.config(
                text=f"SİSTEM: {bekleyen} İSTEĞİ GÖNDERİLDİ — doğrulanmadı",
                fg=SARI)
            firlat.config(state="disabled", bg="#232e3a")
            return
        if not self._arm_durumu_taze_mi():
            btn.config(state="disabled", bg="#232e3a",
                       text="ARM DURUMU BEKLENİYOR")
            etiket.config(text="SİSTEM: ARM DURUMU BİLİNMİYOR/BAYAT", fg=KIRMIZI)
            firlat.config(state="disabled", bg="#232e3a")
            return
        if self.arm_acik:
            btn.config(state="normal", text="DISARM (A)", bg=KIRMIZI)
            etiket.config(text="SİSTEM: ARM ✓ — PIXHAWK HEARTBEAT", fg=SARI)
            firlat.config(state="normal", bg=SARI)
        else:
            btn.config(state="normal", text="ARM (A)", bg="#232e3a")
            etiket.config(text="SİSTEM: DISARM ✓ — PIXHAWK HEARTBEAT", fg=SOLUK)
            firlat.config(state="disabled", bg="#232e3a")

    def _arm_bekleyeni_tamamla(self):
        """Güçlü ACK ve eşleşen taze araç durumu birlikteyse işlemi bitir."""
        komut = getattr(self, "arm_bekleyen_komut", None)
        if not komut or getattr(self, "arm_ack_zamani", None) is None:
            return False
        beklenen = komut == "ARM"
        if not self._arm_durumu_taze_mi() or self.arm_acik is not beklenen:
            return False
        deneme = getattr(getattr(self, "arm_tekrar", None), "deneme", 0)
        self.arm_bekleyen_komut = None
        self.arm_ack_zamani = None
        self._logla(f"İHA {komut} DOĞRULANDI ✓ Pixhawk ACK + taze HEARTBEAT "
                    f"(armed={beklenen}, {deneme} gönderim)", "yesil")
        self._arm_ui_uygula()
        return True

    def arm_degistir(self):
        if getattr(self, "arm_bekleyen_komut", None):
            self._logla("ARM/DISARM isteği zaten bekliyor — ikinci komut "
                        "gönderilmedi", "sari")
            return
        if not self._arm_durumu_taze_mi():
            self._arm_ui_uygula()
            self._logla(f"ARM/DISARM REDDEDİLDİ: Pixhawk `armed` telemetrisi "
                        f"yok veya {ARM_DURUM_TAZELIK_S:.1f} sn'den bayat; "
                        "mevcut durum bilinmeden ters komut seçilmez", "kirmizi")
            return
        yeni_arm_acik = not self.arm_acik
        komut = "ARM" if yeni_arm_acik else "DISARM"
        if komut == "DISARM" and self._iha_havada_mi():
            simdi = time.monotonic()
            bekleyen = getattr(self, "_disarm_teyit_t", 0.0)
            if simdi - bekleyen > DISARM_TEYIT_SURESI_S:
                self._disarm_teyit_t = simdi
                self.btn_arm.config(text="DISARM? TEKRAR BAS", bg=SARI)
                self._logla(
                    "⚠ İHA HAVADA (heartbeat canlı, iniş kanıtı yok) — DISARM "
                    f"gönderilmedi. Onaylamak için {DISARM_TEYIT_SURESI_S:.0f} "
                    "sn içinde TEKRAR bas.", "sari")
                return
            self._disarm_teyit_t = 0.0
        komut_mesaji = command(komut, "iha")
        if not self.arm_tekrar.baslat(komut_mesaji):
            return
        self.arm_bekleyen_komut = komut
        self.arm_ack_zamani = None
        self._arm_ui_uygula()
        self._logla(f"CMD → iha: {komut} (seq={komut_mesaji['seq']}, fiziksel "
                    f"durum DEĞİŞMEDİ; ACK + HEARTBEAT bekleniyor · "
                    f"{ARM_TEKRAR_ARALIGI_S:.2f} s × ≤{ARM_TEKRAR_UST_SINIRI})",
                    "mavi")
        self._arm_tik()

    def _arm_tik(self):
        """ARM/DISARM tekrarını ve ACK-sonrası araç durumu penceresini izle."""
        tekrar = getattr(self, "arm_tekrar", None)
        if tekrar is None or not getattr(self, "arm_bekleyen_komut", None):
            return
        durum = tekrar.tik()
        if durum == VAZGECILDI:
            komut = self.arm_bekleyen_komut
            self.arm_bekleyen_komut = None
            self.arm_ack_zamani = None
            self._logla(f"İHA ONAY VERMEDİ ✗ {komut} {tekrar.deneme} kez "
                        "gönderildi; güçlü ACK gelmedi — durum değiştirilmedi",
                        "kirmizi")
            self._arm_ui_uygula()
            return
        if durum == ONAYLANDI:
            if self._arm_bekleyeni_tamamla():
                return
            if (self.arm_ack_zamani is not None
                    and time.monotonic() - self.arm_ack_zamani
                    > ARM_DURUM_TAZELIK_S):
                komut = self.arm_bekleyen_komut
                self.arm_bekleyen_komut = None
                self.arm_ack_zamani = None
                self._logla(f"İHA {komut} ACK verdi ama eşleşen taze `armed` "
                            "HEARTBEAT gelmedi — fırlatma KAPALI", "kirmizi")
                self._arm_ui_uygula()
                return
        self.kok.after(int(ARM_TEKRAR_ARALIGI_S * 1000), self._arm_tik)

    def firlatma(self):
        if self.t_iha0:
            return
        # P9b (D-393) — §6.2: fırlatma ancak arming sonrası. Düğme zaten
        # DISARM'da kapalıdır ama otorite düğme durumu DEĞİL bu kilittir
        # (T180 sınıfı: UI durumu tek başına emniyet sinyali sayılmaz).
        if (not self._arm_durumu_taze_mi()
                or getattr(self, "arm_bekleyen_komut", None)
                or self.arm_acik is not True):
            self._arm_ui_uygula()
            self._logla("KİLİT ✋ taze Pixhawk HEARTBEAT ile ARM doğrulanmadan "
                        "FIRLATMA damgası atılamaz "
                        "(şartname §6.2 hakem onaylı fırlatma) — REDDEDİLDİ",
                        "sari")
            return
        self.t_iha0 = time.time()
        self._logla("GÖREV · FIRLATMA — İHA kronometresi başladı (limit 15:00)", "mavi")
        self.btn_firlat.config(state="disabled", bg="#232e3a")
        self.btn_iha_indi.config(state="normal", bg=SARI)

    def iha_indi(self):
        if not self.t_iha0 or self.t_iha1:
            return
        self.t_iha1 = time.time()
        sure = self.t_iha1 - self.t_iha0
        asim = sure > self.IHA_LIMIT
        self._logla(f"GÖREV · İHA İNDİ — uçuş süresi {sure/60:.1f} dk"
                    + (" → SÜRE AŞIMI: UÇUŞ GEÇERSİZ (şartname §6.4)" if asim else ""),
                    "sari" if asim else "yesil")
        if not self.onaylandi:
            self._logla("  ⚠ İHA indi ama aktarım havadayken hakem onayı YOKTU — "
                        "§6.4 geçersizlik riski!", "sari")
        self.btn_iha_indi.config(state="disabled", bg="#232e3a")
        self._ucus("İNİŞ TAMAM — PARAŞÜT (İHA-İB)", MAVI)

    def ika_baslat(self):
        # YAZILIM KİLİDİ — şartname §2.2.5: "İHA yere temas etmeden İKA
        # hareket edemez"; §6.2: intikal ancak onaylı veri sonrası. t_iha1
        # yalnız UI kronometresidir; sürüş izninin otoritesi protokol latch'idir.
        if self.iha_landed_seq is None:
            self._logla("KİLİT ✋ Üretim IHA_LANDED kanıtı alınmadan İKA "
                        "hareket EDEMEZ (şartname §2.2.5) — komut REDDEDİLDİ",
                        "sari")
            return
        if not self.onaylandi:
            self._logla("KİLİT ✋ Hakem onayı (ACK) olmadan İKA intikali "
                        "başlatılamaz (şartname §6.2) — komut REDDEDİLDİ", "sari")
            return
        if self.t_ika0:
            return
        # K4: IKA_GO ACK gelene dek AYNI seq ile tekrar gönderilir (D-02).
        komut_mesaji = command("IKA_GO", "ika")
        if not self.ika_go_tekrar.baslat(komut_mesaji):
            return
        self._logla(f"CMD → ika: IKA_GO (seq={komut_mesaji['seq']}, ACK bekleniyor · "
                    f"{IKA_GO_TEKRAR_ARALIGI_S:.2f} s × ≤{IKA_GO_TEKRAR_UST_SINIRI})",
                    "mavi")
        self.t_ika0 = time.time()
        self.t_ika1 = None
        self._logla("GÖREV · İKA İNTİKALİ BAŞLADI — kronometre limit 10:00 "
                    "(kilit koşulları sağlandı ✓)", "mavi")
        self.btn_ika_go.config(state="disabled", bg="#232e3a")
        # HB TEMAS düğmesi İKA'nın IKA_GO ACK'ı (İKA ALDI) gelince açılır
        # (_ack_isle); İKA komutu almadan HB teması mantıksal olarak olamaz.
        self.lbl_ika_go.config(text="İKA_GO gönderildi · ACK bekleniyor…", fg=SARI)
        self.kok.after(int(IKA_GO_TEKRAR_ARALIGI_S * 1000), self._ika_go_tik)

    def _ika_go_tik(self):
        """Zamanlayıcı adımı: ACK yoksa tekrar; üst sınırda KIRMIZI hata + düğme
        yeniden aktif (görev kaybedilmez, operatör tekrar tetikler)."""
        durum = self.ika_go_tekrar.tik()
        if durum == ONAYLANDI:
            return
        if durum == VAZGECILDI:
            self._logla(f"İKA ONAY VERMEDİ ✗ IKA_GO {self.ika_go_tekrar.deneme} kez "
                        "gönderildi, ACK gelmedi — düğme yeniden aktif", "kirmizi")
            self.lbl_ika_go.config(text="İKA ONAY VERMEDİ ✗", fg=KIRMIZI)
            # Kronometre başlamamış sayılır: HER İKİ damga sıfırlanır; t_ika1
            # kalırsa yeniden IKA_GO sonrası hb_temas kalıcı kilitlenirdi.
            self.t_ika0 = self.t_ika1 = None
            self.btn_ika_go.config(state="normal", bg=KIRMIZI)
            self.btn_hb.config(state="disabled", bg="#232e3a")
            return
        if self.ika_go_tekrar.bekliyor:
            self.kok.after(int(IKA_GO_TEKRAR_ARALIGI_S * 1000), self._ika_go_tik)

    def hb_temas(self):
        if not self.t_ika0 or self.t_ika1:
            return
        self.t_ika1 = time.time()
        s = self.t_ika1 - self.t_ika0
        ok = s <= self.IKA_LIMIT
        self._logla(f"GÖREV · HB TEMAS — İKA süresi {s/60:.1f} dk → "
                    + ("GÖREV BAŞARILI (P_görev = 600 puan)" if ok
                       else "SÜRE AŞIMI — İKA görevi BAŞARISIZ"),
                    "yesil" if ok else "sari")
        self.btn_hb.config(state="disabled", bg=YESIL if ok else KIRMIZI)

    # ── Hazırlık akışı (§6.2) + ceza + manuel paraşüt (§2.2.4) ───────────────
    def _ceza_ekle(self, puan, sebep):
        self.ceza_toplam += puan
        self.lbl_ceza.config(text=f"CEZA Σ −{self.ceza_toplam}", fg=KIRMIZI)
        self._logla(f"CEZA −{puan}: {sebep} (toplam −{self.ceza_toplam})", "sari")

    def alan_girisi(self):
        if self.t_haz0:
            return
        self.t_haz0 = time.time()
        self._logla("HAZIRLIK · Alan girişi — 15:00 hazırlık süresi başladı (§6.2)",
                    "mavi")
        self.btn_alan.config(state="disabled", bg="#232e3a")
        self.btn_hazir.config(state="normal", bg=SARI)

    def takim_hazir(self):
        if not self.t_haz0 or self.t_haz1:
            return
        self.t_haz1 = time.time()
        s = self.t_haz1 - self.t_haz0
        puan = max(0, int((900 - s) / 30))
        self._logla(f"HAZIRLIK · 'TAKIM HAZIR' — süre {s/60:.1f} dk (hands-off); "
                    f"tasarruf puanı ≈ +{puan} (§7 t_hazırlık)", "yesil")
        self.btn_hazir.config(state="disabled", bg="#232e3a")
        self.btn_mudahale.config(state="normal", bg=SARI)

    def mudahale(self):
        # §6.2: hands-off sonrası müdahale = −100 ceza + süre hazırlığa eklenir
        if not self.t_haz1:
            return
        self.t_haz0 += time.time() - self.t_haz1   # kronometre kaldığı yerden sürer
        self.t_haz1 = None
        self._ceza_ekle(100, "hands-off sonrası sisteme müdahale (§6.2)")
        self._logla("HAZIRLIK · kronometre DEVAM EDİYOR — müdahale süresi "
                    "hazırlığa ekleniyor; bitince tekrar TAKIM HAZIR verin", "sari")
        self.btn_hazir.config(state="normal", bg=SARI)
        self.btn_mudahale.config(state="disabled", bg="#232e3a")

    def parasut(self):
        # İki adımlı emniyet: yanlışlıkla tek tık paraşüt açamaz
        simdi = time.time()
        if simdi - self.parasut_teyit > 3.0:
            self.parasut_teyit = simdi
            self.btn_parasut.config(bg=KIRMIZI, text="EMİN MİSİN? tekrar bas (3 sn)")
            self.kok.after(3200, lambda: self.btn_parasut.config(
                bg="#232e3a", text="PARAŞÜT (manuel −50)"))
            return
        # P9a (D-393): tek atış `_cmd_gonder` yerine ACK'lı tekrar — paraşüt
        # komutu kaybolursa bunu SESSİZCE kaybetmek kabul edilemez (§6.4).
        komut_mesaji = command("PARACHUTE", "iha")
        if not self.parasut_tekrar.baslat(komut_mesaji):
            # `_ham_gonder` GONDERILEMEDI'yi zaten kirmizi loglar (komut
            # durustlugu sozlesmesi: iletilmeyen komut basari/ceza uretmez).
            return
        self._ceza_ekle(PARASUT_MANUEL_CEZA_PUANI,
                        "manuel paraşüt tetikleme (§2.2.4)")
        self._ucus(f"PARAŞÜT — MANUEL TETİKLENDİ "
                   f"(−{PARASUT_MANUEL_CEZA_PUANI})", KIRMIZI)
        self._logla(f"CMD → iha: PARACHUTE (seq={komut_mesaji['seq']}, ACK "
                    f"bekleniyor · {PARASUT_TEKRAR_ARALIGI_S:.2f} s × "
                    f"≤{PARASUT_TEKRAR_UST_SINIRI})", "kirmizi")
        # D-403 (curutucu): dugme GONDERIMDE "ACILDI" diyordu — ACK'siz.
        # Simdi: gonderildi/ACK bekleniyor; "ACILDI ✓" yalniz IHA ACK'inde
        # (_ack_isle), o da Pixhawk COMMAND_ACK ACCEPTED'e bagli.
        self.btn_parasut.config(state="disabled", bg=KIRMIZI,
                                text="PARAŞÜT GÖNDERİLDİ — İHA ACK bekleniyor")
        self._parasut_tik()

    def _parasut_tik(self):
        """PARACHUTE ACK zamanlayıcısı (K4 kalıbı): ACK yoksa tekrar; üst
        sınırda görünür KIRMIZI hata + düğme yeniden açılır."""
        durum = self.parasut_tekrar.tik()
        if durum == ONAYLANDI:
            return
        if durum == VAZGECILDI:
            self._logla(f"İHA ONAY VERMEDİ ✗ PARACHUTE "
                        f"{self.parasut_tekrar.deneme} kez gönderildi, ACK "
                        "gelmedi — düğme yeniden aktif; İHA hattını kontrol et",
                        "kirmizi")
            self.btn_parasut.config(state="normal", bg=KIRMIZI,
                                    text="PARAŞÜT ACK YOK — TEKRAR")
            return
        if self.parasut_tekrar.bekliyor:
            self.kok.after(int(PARASUT_TEKRAR_ARALIGI_S * 1000),
                           self._parasut_tik)

    def _kron_metin(self, t0, t1, limit):
        if not t0:
            return "--:--", SOLUK
        kalan = limit - ((t1 or time.time()) - t0)
        dk, sn = divmod(int(abs(kalan)), 60)
        if kalan < 0:
            return f"-{dk:02d}:{sn:02d} AŞIM", KIRMIZI
        return f"{dk:02d}:{sn:02d}", (YESIL if kalan > 180 else
                                      SARI if kalan > 60 else KIRMIZI)

    # ── Yardımcılar ──────────────────────────────────────────────────────────
    def _guven_ciz(self, conf):
        c = self.guven_cubuk
        c.delete("all")
        w = S(380)
        c.create_rectangle(0, 0, w, S(20), outline=CIZGI)
        c.create_rectangle(0, 0, int(w * conf), S(20), fill=YESIL, outline="")
        c.create_text(w // 2, S(10), text=f"güven %{conf * 100:.0f}", fill=BG,
                      font=self.f_kucuk)

    def _zincir(self, aktifler):
        for ad, e in self.zincir_etiket.items():
            e.config(fg=YESIL if ad in aktifler else SOLUK,
                     bg="#15251b" if ad in aktifler else PANEL)

    def _irtifa_notunu_goster(self):
        """§5.3.2 · T171: tespitin irtifasini hakem gunlugune yaz.

        Sartname: "...Acik Guzergah'i ASGARI 30 METRE IRTIFADAN ucarak ...
        tespit etmek..." Asgarinin altinda uretilmis bir tespit maddeyi
        KARSILAMAZ; hakem onaylamadan once bunu gormelidir.

        🔴 RET DEGIL, GOSTERIM: IHA kalkis/inis sirasinda da kare uretir;
        orada rotayi reddetmek yanlis olurdu. Karar/telsiz mantigina
        DOKUNULMAZ — yalnizca hakem gunlugune bir satir duser.

        Irtifa BILINMIYORSA sessiz kalinmaz: "bilinmiyor" ile "asgarinin
        altinda" ayni sey degildir, ikisi de AYRI AYRI yazilir.
        """
        tel = (getattr(self, "tel", None) or {}).get("iha") or {}
        irtifa = tel.get("alt")
        if irtifa is None:
            self._logla(
                f"ℹ İRTİFA BİLİNMİYOR: İHA telemetrisi `alt` yayınlamıyor — "
                f"§5.3.2 asgari {SARTNAME_ASGARI_IRTIFA_M:.0f} m şartı "
                "ekrandan DOĞRULANAMAZ", "soluk")
            return None
        not_ = asgari_irtifa_notu(irtifa)
        if not_ is None:
            self._logla(f"irtifa {float(irtifa):.1f} m — §5.3.2 asgari "
                        f"{SARTNAME_ASGARI_IRTIFA_M:.0f} m sağlanıyor", "soluk")
            return None
        self._logla(f"⚠ {not_[1]}", "sari")
        # 🔴 T180 (D-323): uyarı YALNIZ günlüğe düşüyordu. Oysa bu yöntemin
        # kendi sözleşmesi "hakem onaylamadan ÖNCE bunu görmelidir" der.
        # Günlük AKAN bir şerittir: hakem tam o anda haritaya bakıyorsa uyarı
        # gözünden kaçar ve §5.3.2'yi karşılamayan bir tespiti onaylar.
        # Uyarı, ONAY DÜĞMESİNİN yanında ve onay verilene dek DURUR.
        etiket = getattr(self, "lbl_onay", None)
        if etiket is not None:
            etiket.config(
                text=(f"⚠ ASGARİ İRTİFA ALTI: {float(irtifa):.1f} m < "
                      f"{SARTNAME_ASGARI_IRTIFA_M:.0f} m (§5.3.2) — "
                      "hakem onayı BEKLENİYOR"), fg=KIRMIZI)
        return not_

    def _tespiti_yaslandir(self, simdi=None):
        """§6.2 · T169: BAYAT tespit canliymis gibi gosterilemez.

        Sartname "acik yol guzergahi GERCEK ZAMANLI olarak ... monitor
        uzerinden izlenmelidir" der ve "hakem onayi alinmayan tespitler
        gecersiz sayilir". Tersi de dogrudur: hakem BAYAT bir tespiti
        onaylarsa verdigi onay gercek zamanli bir tespite ait DEGILDIR.

        Kusur (D-317): dugum canliligi izleniyordu (nokta 3 s'de kirmiziya
        doner) ama KARAR KUTUSU yaslanmiyordu; telsiz kesilse bile 36 puntoluk
        yesil karar ve ETKIN onay dugmesi ekranda kaliyordu.

        Davranis: yas <= `YKS_TESPIT_TAZELIK_S` -> HICBIR SEY degismez
        (bugunku davranis birebir). Yas asilirsa karar BAYAT isaretlenir ve
        onay dugmesi KAPANIR. Yeni bir OPEN_ROUTE gelince kilit ACILIR —
        kalici degildir. Doner: bayat mi (bool).
        """
        simdi = time.time() if simdi is None else simdi
        if not self.rota or self.rota_yok:
            return False
        # 🔴 T172 (D-321) — ÖLÇÜT DÜZELTİLDİ. T169 tazeliği yalnız son
        # OPEN_ROUTE'un yaşına bağlamıştı; ama İHA rotayı ACK ALANA KADAR
        # tekrarlar ve ACK gelince SUSAR. Yani ölçüt protokolün NORMAL
        # davranışını arıza sayıyordu: demo kipinde İKA ACK'ledikten 5 sn
        # sonra hakemin onay düğmesi KAPANIYORDU (görsel kanıt:
        # results/demo_hazirlik/01_harita.png).
        # Yakalanması gereken şey HATTIN ÖLMESİDİR. İHA canlıysa (heartbeat
        # akıyorsa) son kararı geçerlidir. Bu yüzden yaş, İKİ kanalın
        # TAZE OLANINDAN okunur.
        # D-384: yaslar MONOTONIK saatten — `simdi` (duvar saati) yas
        # hesabina ARTIK girmez; parametre cagiran imzalari bozulmasin
        # diye duruyor. Duvar saatiyle: geri atlama bayat tespiti taze
        # gosterirdi (fail-open), ileri atlama taze tespiti bayatlatirdi.
        _mono = time.monotonic()
        yaslar = []
        if self.rota_zaman is not None:
            yaslar.append(_mono - self.rota_zaman)
        _hb = (getattr(self, "son_hb", None) or {}).get("iha")
        if _hb is not None:
            yaslar.append(_mono - _hb)
        if not yaslar:
            return False        # damga YOK -> hüküm verilmez (hükümsüz)
        yas = min(yaslar)
        bayat = yas > YKS_TESPIT_TAZELIK_S
        # 🔴 A2 (D-381): HAT canliligi ALGI canliligi DEGILDIR. D-374 olctu:
        # gercek ucusta algi 45-51 s'lik araliklarda HIC karar uretemiyor;
        # heartbeat o sirada AKMAYA DEVAM EDER ve yukaridaki min() ekrani
        # "CANLI" tutar. `karar_yas` bu bosluk icindir:
        #   · alan geldiyse: etkin yas = gonderilen yas + gecen sure; esigi
        #     asarsa karar BAYAT'tir — heartbeat taze olsa bile.
        #   · alan HIC gelmediyse: yas BILINMIYOR -> TAZE SAYILMAZ. Eksik
        #     alan "taze" demek DEGILDIR (yeni IHA alani HER heartbeat'te
        #     yollar; yokluk eski/bozuk yayinci demektir).
        # min() mantigi KALDIRILMADI (T172/D-321: ACK sonrasi OPEN_ROUTE
        # susar, hat canliligini heartbeat tasir) — karar_yas TAZEyken
        # davranis birebir eskisidir; bu blok yalniz BAYATLIK EKLER,
        # tazelik eklemez (fail-closed yon).
        _bayat_kaynak = "hat" if bayat else None
        _kyx = getattr(self, "karar_yas_rx", None)
        # D-383: derinlemesine savunma — alim katmani suzse de burada da
        # gecersiz deger BILINMIYOR sayilir (nan > esik daima False tuzagi).
        if _kyx is not None and not (math.isfinite(_kyx[0])
                                     and _kyx[0] >= 0.0):
            _kyx = None
        if _kyx is not None:
            # Gecen sure MONOTONIK saatle (D-383): alim damgasi
            # time.monotonic() ile atilir; duvar saatinin geri atlamasi
            # etkin yasi kucultemez. `simdi` yalniz min() yolunundur.
            _etkin_karar_yas = _kyx[0] + (time.monotonic() - _kyx[1])
            if _etkin_karar_yas > YKS_TESPIT_TAZELIK_S:
                bayat = True
                yas = _etkin_karar_yas
                _bayat_kaynak = "algi"
        else:
            bayat = True
            _bayat_kaynak = "bilinmiyor"
        # 🔴 T176 (D-323): BAYATLIK SIMETRIK OLMALI. Once yalniz KAPATIYORDU;
        # veri geri gelince dugme ancak YENI BIR seq ile aciliyordu. F2 (YKS
        # kaybi) senaryosundan sonra hat donse bile ekran "olu" kaliyordu.
        # Artik tazelik dondugu anda dugme KENDILIGINDEN geri kurulur.
        if not bayat and self.tespit_bayat:
            self.tespit_bayat = False
            self._kutu_yaz("protokol", renk=YESIL)
            self._onay_dugmesini_tazele()
            self._logla("✓ Tespit yeniden TAZE — hakem onayı yeniden açıldı "
                        "(§6.2 gerçek zamanlı aktarım sürüyor)", "yesil")
        # K1 (D-385, kullanıcı onayı · ön kayıt results/k1_tazelik_damgasi):
        # BAYATKEN kutunun detay satırı CANLI yaş damgası taşır ve her tikte
        # güncellenir — karar metni ve güven SİLİNMEZ, onay kilidi DEĞİŞMEZ,
        # günlük yine BİR KEZ yazılır (aşağıdaki blok). Hakem böylece hem
        # tespitin ne kadar eski olduğunu hem bayatlığın SEBEBİNİ görür.
        if bayat and not self.onaylandi:
            if _bayat_kaynak == "bilinmiyor":
                _damga = "⏱ tespit yaşı BİLİNMİYOR (İHA karar_yas göndermiyor)"
            elif _bayat_kaynak == "algi":
                _damga = (f"⏱ son ALGI kararı {yas:.0f} sn önce — "
                          f"algı sustu (hat canlı)")
            else:
                _damga = f"⏱ son veri {yas:.0f} sn önce — hat kesik"
            self._kutu_yaz("protokol", detay=_damga)
        # Onaylanmış tespit SONRADAN bayat işaretlenmez: onay TAZEYKEN verildi,
        # sonradan sarıya boyamak hakemi yanıltır (D-321).
        if bayat and not self.tespit_bayat and not self.onaylandi:
            self.tespit_bayat = True
            self._kutu_yaz("protokol", renk=SARI)
            btn = getattr(self, "btn_onay", None)
            if btn is not None:
                btn.config(state="disabled", bg="#232e3a",
                           text="BAYAT TESPİT — ONAY KAPALI")
            if _bayat_kaynak == "bilinmiyor":
                _sebep = ("TESPİT YAŞI BİLİNMİYOR: İHA `karar_yas` alanı "
                          "göndermiyor (eski/bozuk yayıncı) — taze sayılamaz")
            elif _bayat_kaynak == "algi":
                _sebep = (f"İHA'nın son ALGI kararı {yas:.0f} sn önce — hat "
                          f"canlı olsa bile algı susmuş (tazelik "
                          f"{YKS_TESPIT_TAZELIK_S:.0f} sn)")
            else:
                _sebep = (f"İHA'dan {yas:.0f} sn veri yok "
                          f"(ne güzergâh ne heartbeat; tazelik "
                          f"{YKS_TESPIT_TAZELIK_S:.0f} sn)")
            etiket = getattr(self, "lbl_onay", None)
            if etiket is not None:
                etiket.config(
                    text=(f"⚠ BAYAT TESPİT: {_sebep}. "
                          "Şartname §6.2 GERÇEK ZAMANLI aktarım ister — "
                          "onay KAPATILDI, yeni tespit bekleniyor."),
                    fg=SARI)
            self._logla(
                f"⚠ BAYAT TESPİT: {_sebep} — hakem onayı kapatıldı "
                "(§6.2 gerçek zamanlı aktarım)", "sari")
        return bayat

    def _durum_tazele(self):
        self.lbl_saat.config(text=time.strftime("%H:%M:%S"))
        simdi = time.time()
        self._tespiti_yaslandir(simdi)
        _mono = time.monotonic()               # D-384: damgalar monotonik
        for ad, (nokta, metin) in self.lbl_dugum.items():
            t = self.son_hb.get(ad)
            if t is None:
                nokta.config(fg=KIRMIZI)
                metin.config(text=f"{ad.upper()}  — sinyal yok")
            else:
                yas = _mono - t
                canli = yas < 3.0                      # ika_receiver failsafe eşiği
                nokta.config(fg=YESIL if canli else KIRMIZI)
                tel = self.tel.get(ad) or {}
                parcalar = []
                if "alt" in tel:
                    parcalar.append(f"{tel['alt']:.0f} m")
                if "hiz" in tel:
                    parcalar.append(f"{tel['hiz']:.1f} m/s")
                if "bat" in tel:
                    parcalar.append(f"{tel['bat']:.1f} V")
                if "uydu" in tel:
                    parcalar.append(f"{tel['uydu']} uydu")
                ek = (" · " + " · ".join(parcalar)) if parcalar else ""
                mod = self.mod.get(ad)
                if mod:
                    ek += f" · mod {mod}" + ("" if mod == "AUTO" else " ⚠GEÇERSİZ")
                metin.config(text=f"{ad.upper()} — hb {yas:.1f} sn{ek}"
                                  + ("" if canli else "  (BAĞLANTI KAYBI!)"))
        gps_etiket = getattr(self, "lbl_gps", None)
        if gps_etiket is not None:
            iha_hb = self.son_hb.get("iha")
            if iha_hb is None or _mono - iha_hb >= ARM_DURUM_TAZELIK_S:
                gps_etiket.config(
                    text="HAM GNSS: TELEMETRİ YOK/BAYAT · SEMANTİK HARİTADA "
                         "KULLANILMAZ", fg=KIRMIZI)
            else:
                gps_tel = self.tel.get("iha") or {}
                gps_var = all(k in gps_tel for k in ("lat", "lon", "gps_fix"))
                gps_etiket.config(text=gps_gosterim_metni(gps_tel),
                                  fg=YESIL if gps_var else SARI)
        self._arm_ui_uygula()
        self.lbl_sayac.config(
            text=f"OPEN_ROUTE {self.sayac['OPEN_ROUTE']} · "
                 f"RED {self.sayac['OPEN_ROUTE_RED']} · "
                 f"NO_ROUTE {self.sayac['NO_ROUTE']} · "
                 f"LANDED {self.sayac['IHA_LANDED']} · "
                 f"HB {self.sayac['HEARTBEAT']} · "
                 f"ACK {self.sayac['ACK_TX']}")
        m1, r1 = self._kron_metin(self.t_iha0, self.t_iha1, self.IHA_LIMIT)
        _ek = " §5.3.2 FDA" if self.fda_kipi else ""
        self.lbl_kron_iha.config(
            text=f"İHA ⏱ {m1} / {_ss(self.IHA_LIMIT)}{_ek}", fg=r1)
        m2, r2 = self._kron_metin(self.t_ika0, self.t_ika1, self.IKA_LIMIT)
        self.lbl_kron_ika.config(
            text=f"İKA ⏱ {m2} / {_ss(self.IKA_LIMIT)}", fg=r2)
        m3, r3 = self._kron_metin(self.t_haz0, self.t_haz1, self.HAZIRLIK_LIMIT)
        self.lbl_kron_haz.config(
            text=f"HAZIRLIK ⏱ {m3} / {_ss(self.HAZIRLIK_LIMIT)}", fg=r3)
        if self.gorunum_adi == "harita":
            self._inset_ciz()

    def _logla(self, satir, renk="soluk"):
        self.gunluk.config(state="normal")
        self.gunluk.insert("end", time.strftime("[%H:%M:%S] ") + satir + "\n", renk)
        self.gunluk.see("end")
        self.gunluk.config(state="disabled")


# ── Demo beslemesi: gerçek protokolle sahte İHA + İKA ────────────────────────
# T175 · D-323: demo IHA'si rota ACK'inden bu kadar sonra "iner" ve inis
# kanitini yayinlar. Sunucunun aktarimi ekranda gorup anlatmasina zaman birakir;
# saha davranisini taklit eder (once aktarim, sonra inis — sartname §2.2.4).
INIS_GECIKME_S = 6.0


def demo_besle(yks_port, durum):
    """Aynı comms primitifleriyle İHA/İKA davranışını üretir (tanıtım için).
    İHA: 1 Hz heartbeat + ACK gelene dek OPEN_ROUTE tekrar gönderimi.
    İKA: 1 Hz heartbeat. `durum` anahtarları senaryo butonlarıyla kesilir."""
    hedef = ("127.0.0.1", yks_port)
    ika_link = UDPLink()
    ika_hedef = ("127.0.0.1", ika_link.port)

    def iha():
        link = UDPLink()
        reader = FrameReader()
        rota = open_route(
            road=2, conf=0.91, ref_xy=list(YAYIN_REF_XY),
            waypoints=[[0.6, 0.5], [-0.8, 5.0], [1.2, 10.0], [-0.4, 15.5],
                       [1.8, 21.0], [0.2, 27.0], [-1.0, 33.0], [0.0, 40.0]])
        onay = False
        onay_t = 0.0
        indi = False           # T175: inis kaniti bir kez yayinlanir
        t0 = time.time()
        sonra = t0 + 3.0                                   # 3 sn tarama süsü
        son_tx = 0.0
        son_karar_t = time.time()      # F6 (D-383): algi kesilince DONAR
        son_xy = (150.0, 150.0)        # GNSS kaybinda konum DONAR
        armed = False                  # demo da komut gonderiminden durum uydurmaz
        # 🔴 T179 (D-323): burada `while time.time() - t0 < 600` yaziyordu —
        # besleme 10 DAKIKADA SESSIZCE OLUYORDU. Sunum 10 dakikayi asarsa
        # (kaptana anlatirken cok olasi) heartbeat kesilir, ekran "baglanti
        # yok"a duser ve sistem BOZULMUS gibi gorunur. Is parcaciklari daemon;
        # surec kapaninca zaten olurler — sure sinirinin islevi YOKTU.
        while True:
            if durum["iha_hb"]:                            # YKS-kaybı senaryosu keser
                sn = time.time() - t0
                # Batarya taban degeri: uzun sunumda eksiye dusmesin (aksi
                # halde ekran 3 saat sonra "-1.2 V" gosterirdi).
                if durum.get("iha_bat", True):
                    bat = round(max(11.1, 12.6 - 0.0012 * sn), 2)
                else:                                      # F4: KRITIK (<%15)
                    bat = round(10.4 + 0.10 * math.sin(sn / 4), 2)
                if durum.get("iha_gnss", True):            # F5: fix yok -> 0 uydu
                    uydu = 14 + int(sn / 7) % 3
                    son_xy = (round(150 + 85 * math.cos(sn / 11), 1),
                              round(150 + 62 * math.sin(sn / 11), 1))
                else:
                    uydu = 0                               # konum guncellenmez
                # A2 (D-381) + F6 (D-383): algi anahtari ACIKKEN damga her
                # turda tazelenir (karar_yas ~0 sn, taze); F6 kesince damga
                # DONAR ve yas gercekten buyur — bant ile tazelik kutusu
                # artik ayni seyi soyler (T177 celiskisi kapandi). Alan hic
                # gonderilmese ekran (dogru olarak) BILINMIYOR der.
                if durum.get("iha_algi", True):
                    son_karar_t = time.time()
                hb = heartbeat("iha")                      # ek telemetri alanları:
                hb.update(alt=round(30 + 1.8 * math.sin(sn / 5), 1),
                          hiz=round(16.5 + 1.2 * math.sin(sn / 3.7), 1),
                          bat=bat, uydu=uydu,
                          mod="AUTO",                      # tam otonomi (§6.2)
                          karar_yas=round(time.time() - son_karar_t, 2),
                          x=son_xy[0], y=son_xy[1],
                          lat=37.7648000 + son_xy[1] / 111_320.0,
                          lon=38.2786000 + son_xy[0] / 88_600.0,
                          gps_fix=3 if durum.get("iha_gnss", True) else 1,
                          armed=armed)
                link.send(encode(hb), hedef)
                if time.time() >= sonra and not onay and time.time() - son_tx > 1.2:
                    link.send(encode(rota), hedef)         # ACK yok → tekrar
                    link.send(encode(rota), ika_hedef)     # İKA ACK'ı YKS'ye yansır
                    son_tx = time.time()
            # 🔴 T175 (D-323): rota aktarimi ACK'lendikten sonra IHA INER ve
            # inis kanitini GERCEK protokol cercevesiyle yayinlar. Bu olmadan
            # `iha_landed_seq` hic kurulmuyordu ve sartname §2.2.5 kilidi
            # (IHA yere temas etmeden IKA hareket edemez) demo kipinde KALICI
            # RET veriyordu: IKA BASLAT ve HB TEMAS hic acilmiyor, gorevin
            # IKINCI YARISI ulasilamiyordu. Kilit DOGRU; eksik olan besleme
            # idi — bu yuzden duzeltme BESLEMEDE, kilitte DEGIL.
            if onay and not indi and time.time() - onay_t >= INIS_GECIKME_S:
                inis = iha_landed()
                for _ in range(4):                 # RF kaybina karsi tekrar
                    link.send(encode(inis), hedef)
                    time.sleep(0.15)
                indi = True
            d, _ = link.recv()
            for m in reader.feed(d) if d else []:
                if m.get("type") == "ACK" and m.get("ref") == rota["seq"]:
                    if not onay:
                        onay_t = time.time()
                    onay = True
                elif (m.get("type") == "CMD" and m.get("hedef") == "iha"
                      and m.get("cmd") in ("ARM", "DISARM", "PARACHUTE")):
                    if m["cmd"] == "ARM":
                        armed = True
                    elif m["cmd"] == "DISARM":
                        armed = False
                    link.send(encode(ack(
                        m["seq"], "iha", "CMD", ref_cmd=m["cmd"],
                        sonuc=ACK_SONUC_KABUL)), hedef)
            time.sleep(0.5)

    def ika():
        link = ika_link
        receiver = IkaReceiver(link, yks_peer=hedef)     # K8: rota ACK kopyası
        t0 = time.time()
        while True:                                        # T179: sure siniri YOK
            if durum["ika_hb"]:                            # İKA-kaybı senaryosu keser
                sn = time.time() - t0
                hb = heartbeat("ika")
                hb.update(hiz=0.0, bat=round(max(11.0, 11.9 - 0.0008 * sn), 2),
                          uydu=12 + int(sn / 9) % 3, mod="AUTO")
                link.send(encode(hb), hedef)
            # Demo da gerçek alıcı yolunu kullanır; IKA_GO latch + ACK yalnız
            # ekranda görünmekle kalmaz, aynı UDP soketinde gerçekten tüketilir.
            receiver.poll()
            time.sleep(1.0)

    threading.Thread(target=iha, daemon=True).start()
    threading.Thread(target=ika, daemon=True).start()


def main():
    ap = argparse.ArgumentParser(description="Navitas YKS hakem ekranı")
    ap.add_argument("--bind", default="0.0.0.0:5005")
    ap.add_argument("--ika", type=_udp_adres,
                    help="İKA komut hedefi host:port (UDP için zorunlu)")
    ap.add_argument("--iha", type=_udp_adres,
                    help="İHA komut alıcısı host:port (iha_komut_alici --bind; "
                         "PARAŞÜT/ARM komutları buraya gider — verilmezse "
                         "heartbeat kaynağı kullanılır ve komut alıcıya "
                         "ULAŞMAZ, D-403)")
    ap.add_argument("--serial", help="SiK telsiz seri portu (örn. COM5)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument(
        "--kamera-url", default=os.environ.get("NAVITAS_KAMERA_URL"),
        help=("Jetson RAW kamera kökü (örn. http://192.168.4.2:8080). "
              "Yalnız ayrı Wi-Fi/LAN; SiK üzerinden video taşınmaz. "
              "Varsayılan: NAVITAS_KAMERA_URL, yoksa kamera kapalı"))
    ap.add_argument("--demo", action="store_true",
                    help="dahili İHA/İKA beslemesi (tanıtım + otomatik hakem onayı)")
    ap.add_argument("--otokaydet", type=float, default=0,
                    help="N sn sonra pencere görüntüsünü PNG kaydet (rapor için)")
    ap.add_argument("--senaryo", choices=("rc", "yks", "ika", "bat", "gnss",
                                          "algi"),
                    help="demo kipinde SS'den 3 sn önce bu acil durum "
                         "senaryosunu tetikle (tatbikatın ekrandaki etkisi "
                         "kanıtlanabilsin diye)")
    ap.add_argument("--kaydet-yolu", default="yks_ekran.png")
    ap.add_argument("--kapat", action="store_true", help="otokaydet sonrası çık")
    # T80 · ⚠ VARSAYILANLAR DEĞİŞMEDİ: ikisi de `None`, yani verilmezse ekran
    # bugünkü gibi `kompozit` kaynağı ve "Saha Haritası" görünümüyle açılır.
    # `kompozit` bilerek korunur — bir OTOPARK karesidir ve domain boşluğunu
    # hakeme gösterir (D-53/D-90); orada `ZEMIN_MASKESI_SUPHELI` MEŞRUDUR
    # (D-118, görselle doğrulandı: model binanın çatısını zemin sayıyor).
    # Bu görev yalnız SEÇİLEBİLİR yapar, varsayılanı taşımaz.
    # 🔴 T182 (D-323): yardim metni varsayilani `ALGI_KAYNAKLAR[0]`dan
    # (= "kompozit") turetiyordu; oysa T161'den beri gercek varsayilan
    # `ALGI_VARSAYILAN_KAYNAK` (= "arena_kadraj"). `--help` YANLIS soyluyordu.
    # Varsayilan, ONU BELIRLEYEN sabitten okunur — baska hicbir yerden.
    ap.add_argument("--kaynak", choices=YksArayuz.ALGI_KAYNAKLAR,
                    help="canlı algı açılış kaynağı (varsayılan: "
                         f"{YksArayuz.ALGI_VARSAYILAN_KAYNAK}); geçerli "
                         "değerler ALGI_KAYNAKLAR'dan okunur")
    ap.add_argument(
        "--fda", action="store_true",
        help=("şartname §5.3.2 'Drone ile Görev Test Uçuşu' kipi: İHA "
              "kronometresi TÜM operasyon için 10 dk gösterir (kalkış + "
              "tespit + aktarım + iniş). Verilmezse §6.2 yarışma günü "
              "bütçesi (15 dk) kullanılır"))
    ap.add_argument("--gorunum", choices=tuple(GORUNUM_SECENEKLERI),
                    help="açılış görünümü (varsayılan: saha)")
    args = ap.parse_args()

    if args.serial and args.demo:
        ap.error("--demo yalnız UDP kipinde kullanılabilir")
    if args.serial and args.ika:
        ap.error("--serial ile --ika birlikte kullanılamaz")
    if not args.serial and not args.demo and not args.ika:
        ap.error("UDP kipinde --ika HOST:PORT zorunlu")

    global OLCEK
    try:  # yüksek DPI: netlik + piksel ölçülerini ekrana göre büyüt (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        OLCEK = max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        pass

    if args.serial:
        link = SerialLink(args.serial, args.baud)
        ika_peer = None
        iha_peer = None
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        ika_peer = args.ika
        iha_peer = args.iha

    kok = tk.Tk()
    # otomatik onay YOK: hakem onay akışı elle incelenebilsin (buton/R kısayolu)
    app = YksArayuz(
        kok, link, otomatik_onay=False, demo=args.demo, ika_peer=ika_peer,
        iha_peer=iha_peer, kamera_url=args.kamera_url)
    app._logla(f"YKS hazır — dinleniyor: "
               f"{args.serial or args.bind}", "mavi")
    app._logla(
        (f"RAW kamera LAN kaynağı: {args.kamera_url}" if args.kamera_url else
         "RAW kamera KAPALI: --kamera-url/NAVITAS_KAMERA_URL verilmedi; "
         "telemetri ve komut hattı çalışmaya devam eder"),
        "mavi" if args.kamera_url else "sari")

    if args.demo:
        demo_besle(link.port, app.demo_durum)
        app._logla("DEMO modu: dahili İHA/İKA beslemesi başladı — "
                   "senaryo butonları etkin", "mavi")

    # T80: kaynak GÖRÜNÜMDEN ÖNCE kurulur — `gorunum("algi")` çıkarımı hemen
    # tetikler, sonra ayarlanan kaynak o ilk kareyi kaçırırdı.
    if args.fda:
        # T170 · §5.3.2: FDA test ucusunun butcesi TEK ve daha SIKIDIR (10 dk).
        # Ornek duzeyinde ezilir; sinif varsayilani (yarisma gunu) DEGISMEZ.
        app.IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S
        app.fda_kipi = True
        app._logla(
            "§5.3.2 FDA KİPİ: İHA bütçesi "
            f"{_ss(SARTNAME_FDA_OPERASYON_SURESI_S)} (kalkış+tespit+aktarım+"
            "iniş). Süreyi aşan takım 0 PUAN alır.", "sari")
    if args.kaynak:
        app.algi_kaynak = args.kaynak
        app.algi_idx = 0
        app._logla(f"ALGI kaynağı (--kaynak): {args.kaynak}", "mavi")
    if args.gorunum:
        app.gorunum(GORUNUM_SECENEKLERI[args.gorunum])
        app._logla(f"Açılış görünümü (--gorunum): {args.gorunum}", "mavi")

    if args.senaryo:
        # Senaryolar YALNIZ demo kipinde etkindir (`senaryo()` kendi de
        # korur); burada da sessiz kalmamak icin sebebi yazariz.
        if not args.demo:
            app._logla("--senaryo YOKSAYILDI: yalnız --demo kipinde çalışır",
                       "sari")
        else:
            gecikme = max(0.5, args.otokaydet - 3.0) if args.otokaydet > 0 else 3.0
            kok.after(int(gecikme * 1000), lambda: app.senaryo(args.senaryo))

    if args.otokaydet > 0:
        # SS modunda pencere HEP önde olsun — yoksa arkadaki pencere yakalanır
        kok.attributes("-topmost", True)
        kok.lift()

        # T80: hedef alt dizin yoksa SS sessizce kaybolmasın.
        Path(args.kaydet_yolu).parent.mkdir(parents=True, exist_ok=True)

        def kaydet():
            from PIL import ImageGrab
            kok.lift()
            kok.focus_force()
            kok.update()
            x, y = kok.winfo_rootx(), kok.winfo_rooty()
            w, h = kok.winfo_width(), kok.winfo_height()
            ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(args.kaydet_yolu)
            print(f"SS kaydedildi: {args.kaydet_yolu}")
            if args.kapat:
                kok.destroy()
        kok.after(int(args.otokaydet * 1000), kaydet)

    try:
        kok.mainloop()
    finally:
        kamera = getattr(app, "kamera_istemci", None)
        if kamera is not None:
            kamera.durdur()
        link.close()


if __name__ == "__main__":
    main()
