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
import subprocess
import sys
import threading
import time
import tkinter as tk
import uuid
from pathlib import Path
from tkinter import font as tkfont
from rota_inceleme import RotaInceleme, rota_plani, harita_ciz as rota_detay_haritasi

from link import UDPLink, SerialLink, saha_tasiyicisi_mi, tasiyici_adi
from mavlink_tunel import (KIMLIK_YER, TASIYICI_TUNEL, TUNEL_YER_UC, TunelLink,
                           uc_coz)
from ika_receiver import IkaReceiver
from hakem_kaydi import HakemKaydi, varsayilan_hakem_log_yolu
from komut_tekrar import AckliTekrar, BOS, ONAYLANDI, VAZGECILDI
from protocol import (ACK_SONUC_KABUL, encode, ack, command, heartbeat, iha_landed,
                      kritik_komut_ack_gecerli_mi, MESAJ_OPEN_ROUTE, MESAJ_NO_ROUTE,
                      open_route, MESAJ_HEARTBEAT, MESAJ_ACK, MESAJ_CMD, MESAJ_IHA_LANDED,
                      FrameReader, PROTOCOL_VERSION, ROAD_LABEL)

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
GORUNUM_SECENEKLERI = {"saha": "harita", "canli": "algi", "kamera": "kamera", "rota": "rota"}

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
# Harita üstünde üç ayrı metin katmanı vardır: semantik uyarı, renk açıklaması
# ve HB etiketi. Aynı y koordinatına bırakıldıklarında geniş ekranda bile üst
# üste binerler. Üst bant bu üçüne ayrılmış çizim alanıdır; arena bunun altında
# başlar. Değerler görev/geometri eşiği değil, DPI ölçekli UI yerleşimidir.
HARITA_YAN_KENAR_PX = 34
HARITA_ALT_KENAR_PX = 34
HARITA_UST_BANT_PX = 96
HARITA_UYARI_Y_PX = 8
HARITA_RENK_ACIKLAMA_Y_PX = 52

# ── T226 (D-443 kusur a): kamera görünümünde VİDEO + ROTA aynı anda ─────────
# 🔴 ÖLÇÜLEN KUSUR (D-443, kod haritası): `gorunum("kamera")` şematik haritayı
# `pack_forget` ile gizliyordu; MK15 videosu açıkken hakem seçilen şeridi
# haritada GÖREMİYORDU. Kamera görünümünde haritanın KÜÇÜK kopyası videonun
# yanında durur. Çizim AYNI `_harita_ciz` yolundan, yalnız tuval farklı (iki
# çizim kodu = ayrışabilecek iki gerçek). Boyut DPI ölçekli UI yerleşimidir,
# görev/geometri eşiği değil: 300 px'te uyarı + renk açıklaması 96 px üst
# banda sığar (inset'siz tuvalde metin tüm genişliği kullanır).
MINI_HARITA_GENISLIK_PX = 300
MINI_HARITA_YUKSEKLIK_PX = 330
# ── T226-D (D-448): KÜÇÜK harita etiket yerleşimi ──────────────────────────
# 🔴 ÖLÇÜLEN KUSUR (çürütücü, 10 Eyl; bbox + ekran görüntüsü): 450×495 küçük
# haritada (OLCEK 1,5) şerit 1/3 seçiliyken komşu kapalı şeritlerin "✕ KAPALI"
# yazıları üst üste biniyordu (ekranda "✕ KAPA✕ KAPALI"); İKA-KB ↔ "2·ORTA"/
# "3·SAG", ref ↔ İKA-KB, renk açıklaması ↔ "HB (hedef)" de kesişiyordu —
# yukarıdaki "96 px üst banda sığar" varsayımı 1,5 ölçekte TUTMADI. Sabit
# piksel ofsetleri dar tuvalde tutmaz: küçük haritada etiketler METİN KUTUSU
# ÖLÇÜLEREK yerleşir (`_harita_olculu_yerlesim`), yazı tipi küçüktür ve kapalı
# şerit etiketi şerit genişliğine sığmıyorsa yalnız "✕" yazılır (anlamı renk
# açıklamasındaki "KIRMIZI: kapalı/moloz" taşır). Ana harita OPEN_ROUTE/boşta
# DEĞİŞMEDİ (master ile bayt-eş; kapı tests/test_yks_mk15_hakem_ekrani H2d).
# Değerler DPI ölçekli UI yerleşimidir, görev/geometri eşiği değil.
MINI_HARITA_YAZI_PUNTO = 8
KAPALI_SERIT_ETIKETI = "✕ KAPALI"
KAPALI_SERIT_ETIKETI_KISA = "✕"
RENK_ACIKLAMASI = "■ YEŞİL: açık/geçilebilir   ■ KIRMIZI: kapalı/moloz"
# Metinler arası ve bant altı boşluk (S(4)).
HARITA_METIN_PAYI_PX = 4
# Tek satır yüksekliği ölçüm metni: Türkçe şapkalı büyük harfler + alt uzantı.
HARITA_SATIR_OLCU_METNI = "ÇĞİÖŞÜ gjpqy()"
# Hakem haritasında İKA-KB (başlangıç) ve HB (hedef) kutu merkezleri, metre.
KB_KONUM_M = (25, 2)
HB_KONUM_M = (25, 48)
# Video karar ÜRETMEZ: hakem onayı telsiz (SiK) verisine verilir (CONTRACTS
# §6.7, D-443). Video paneli başlığında SABİT durur; etiket boşken de silinmez.
KAMERA_KARAR_NOTU = "karar üretmez — onay telsiz verisine verilir"
# `--kamera-etiket` operatör metnidir (örn. "MK15 · HDMI · yakalama"): başlığa
# ve KAMERA_KANIT `kaynak` alanına yazılır. Yazdırılamaz karakter/aşırı uzunluk
# ekranı ve kayıt satırını bozar — taşıma biçimi sınırı, karar eşiği değil.
KAMERA_ETIKETI_AZAMI_KARAKTER = 64

# ── Hakem kanıt kaydı — olay kümesi (CONTRACTS §6.8) ─────────────────────────
# NEDEN: kayıt 21 Eylül'de şartname §2.2.3 onayının DAYANAĞIDIR; ekrandaki
# kayan metin uçuş sonrası kanıt değildir. Olay ADLARI serbest metin olarak
# üretilmez (madde 16): tek küme burada durur, `CONTRACTS §6.8` tablosu ve
# koddaki çağrılar `tests/test_yks_hakem_kanit_olaylari.py` ile ÜÇ YÖNLÜ
# karşılaştırılır — biri değişip diğeri kalırsa kapı DÜŞER.
KANIT_OLAYLARI = (
    "YKS_ARAYUZ_HAZIR",
    "ROTA_ALINDI",
    "ROTA_REDDEDILDI",
    "ROTA_YOK",
    "ACK_ALINDI",
    "IKA_AKTARIM_KANITI",
    "HAKEM_ONAYI_1",
    "HAKEM_ONAYI_2",
    "HAKEM_ONAYI_REDDI",
    "IHA_INIS_KANITI",
    "KAMERA_KANIT",
    "TELEMETRI_KANIT",
    "ACIL_SENARYO",
    "KRONOMETRE_BASLADI",
    "KRONOMETRE_BITTI",
    "UI_OLAYI",
)
# `KAMERA_KANIT` / `TELEMETRI_KANIT` `_tik` döngüsünden (~8 Hz) üretilir ve
# `HakemKaydi.yaz` HER SATIRDA `fsync` yapar. Her tikte yazmak Tk geri
# çağrısını diske bağlar (ekran donar) ve kaydı okunamaz hâle getirir. Bu
# yüzden ikisi KENAR olayıdır; durum değişmezse bu aralıkta bir kez daha
# yazılır — "hâlâ aynı" satırı SÜREKLİLİK kanıtıdır (yalnız geçişler
# yazılırsa kaydın "kamera 10 dk canlı kaldı" demeye dayanağı olmaz).
KANIT_TEKRAR_ARALIGI_S = 30.0

# ── K8 erken ACK tamponu (T224 · D-441) ──────────────────────────────────────
# 🔴 ÖLÇÜLEN KUSUR (T213-B, 10 Eylül, `gt 1 orta 44`): İKA'nın OPEN_ROUTE ACK
# kopyası YKS'ye OPEN_ROUTE'tan ÖNCE ulaştı (loopback'te İKA, İHA'nın YKS'ye
# ikinci datagramından hızlı). `_ack_isle` `self.rota` boş/başka seq diye
# kopyayı ATIYORDU; İHA 'ika' ACK'ını gördüğü için İKA'ya tekrar göndermez,
# kopya BİR DAHA GELMEZ → hakem ekranında İKA kanıtı yok, 2/2 kilitli.
# Çözüm (`sim_hakem` kalıbı): erken kopya `ref` ile kısa süre saklanır,
# OPEN_ROUTE gelince eşlenir. Süre: İHA'nın YKS'ye OPEN_ROUTE tekrar penceresi
# 8 × 0,25 s = 2 s (`IhaSender.send_open_route` varsayılanları; hiçbir üretim
# çağıranı ezmiyor); 5 s bunun 2,5 katıdır. Süresi dolan kopya ATILIR: bayat
# bir ACK sonraki rotaya kanıt olamaz (fail-closed). Kanıtın damgası ve
# `iha_havada` bilgisi kopyanın GELDİĞİ anındır — anlık yolla aynı an. Yalnız
# `ref_tip="OPEN_ROUTE"` taşıyan kopya tamponlanır; `ref_tip`siz (eski üretici)
# ACK için anlık eşleme davranışı DEĞİŞMEDİ (CONTRACTS §6.6). Süre denetimi
# MONOTONİK saatle (D-384 sınıfı).
IKA_ROTA_ACK_ERKEN_TAMPON_S = 5.0

# ── Kanıt kaydı kilidi (fail-closed + fail-visible) ──────────────────────────
# 🔴 ÖLÇÜLEN KUSUR (2026-09-03): `_kanit_hatasini_goster` `btn_firlat` ve
# `btn_onay`u BİR KEZ `disabled` yapıyordu, ama düğmeleri çizen periyodik
# yollar (`_arm_ui_uygula`, `_onay_dugmesini_tazele`,
# `_aktarim_onay_dugmesini_kur`) `kanit_kaydi_hatasi` bayrağına HİÇ
# bakmıyordu. Bir tik sonra düğmeler geri açılıyor, KIRMIZI afiş ekranda
# kalıyordu: ekranda görünen ile gerçek AYRIŞIYORDU. Kilit artık düğmeleri
# çizen TEK yazardan (`_firlat_dugmesini_ciz` / `_onay_dugmesini_ciz`)
# okunur; metinler de sabit, çünkü hakem düğmenin NEDEN kapalı olduğunu
# okumadan kilidi doğrulayamaz.
# ⚠ NİYET: kilit YALNIZ uçuş/onay BAŞLATMA içindir. ARM/DISARM ve acil
# komutlar (RTL/LAND) kanıt kaydı bozukken de KULLANILABİLİR kalır —
# aracı indirebilmek emniyetin kendisidir.
KANIT_KILIDI_FIRLAT_METNI = "KANIT KAYDI HATASI — FIRLATMA KAPALI"
KANIT_KILIDI_ONAY_METNI = "KANIT KAYDI HATASI — ONAY KAPALI"

# Pixhawk'ın bildirdiği uçuş modu serbest ağ metni değildir. ArduPilot mod
# adları kısa ASCII belirteçlerdir; sınırsız/yeni satırlı bir değer hakem
# ekranını ve günlüğü zehirleyemez. Bu bir karar eşiği değil, taşıma biçimi
# sınırıdır.
UCUS_MODU_AZAMI_KARAKTER = 32
ACIL_UCUS_MODLARI = frozenset(("RTL", "LAND"))


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


def sematik_uyari_yerlesimi(genislik_px, inset_var=True):
    """Semantik uyarıyı sağ üst inset'ten yatayda ayıran yerleşim.

    ``inset_var=False``: inset çizilmeyen tuval (T226 küçük harita) — metin
    tuvalin tüm genişliğini kullanır. Ana harita (varsayılan) DEĞİŞMEDİ.
    """
    sol = S(12)
    if inset_var:
        inset_sol, _ust, _sag, _alt = inset_kutusu(genislik_px)
        sag = inset_sol - S(8)
    else:
        sag = genislik_px - S(12)
    genislik = max(0, sag - sol)
    return sol, S(HARITA_UYARI_Y_PX), genislik


def harita_cizim_alani(genislik_px, yukseklik_px, ust_px=None, alt_px=None):
    """Üst yazı bandının altında kalan kare arena çizim alanını döndür.

    ``ust_px``/``alt_px`` (T226-D): ÖLÇÜLÜ yerleşimin (küçük harita, ROTA YOK)
    üst bant / alt kenar pikseli; verilmezse sabit ana harita değerleri.
    """
    sol = S(HARITA_YAN_KENAR_PX)
    ust = S(HARITA_UST_BANT_PX) if ust_px is None else int(ust_px)
    alt = S(HARITA_ALT_KENAR_PX) if alt_px is None else int(alt_px)
    kullanilabilir_w = max(0, genislik_px - sol - S(HARITA_YAN_KENAR_PX))
    kullanilabilir_h = max(0, yukseklik_px - ust - alt)
    olcek = min(kullanilabilir_w, kullanilabilir_h)
    return sol, ust, olcek


def kamera_etiketi_dogrula(etiket):
    """``--kamera-etiket`` metnini doğrula → kırpılmış metin ("" = etiket yok).

    Yükseltir (ValueError): metin olmayan değer, yazdırılamaz karakter (satır
    sonu, sekme, kontrol), ``KAMERA_ETIKETI_AZAMI_KARAKTER`` üstü uzunluk.
    """
    if etiket is None:
        return ""
    if not isinstance(etiket, str):
        raise ValueError("kamera etiketi metin olmalı")
    metin = etiket.strip()
    if len(metin) > KAMERA_ETIKETI_AZAMI_KARAKTER:
        raise ValueError(
            f"kamera etiketi en çok {KAMERA_ETIKETI_AZAMI_KARAKTER} karakter "
            f"olabilir ({len(metin)} verildi)")
    if not metin.isprintable():
        raise ValueError("kamera etiketi yazdırılamaz karakter taşıyamaz")
    return metin


def kamera_baslik_metni(etiket):
    """Video paneli başlığı: kaynak etiketi + SABİT "karar üretmez" notu (T226)."""
    kaynak = etiket if etiket else "etiket verilmedi (--kamera-etiket)"
    return f"VİDEO KAYNAĞI: {kaynak}   |   {KAMERA_KARAR_NOTU}"


def kamera_kanit_kaynagi(url, etiket):
    """CONTRACTS §6.8 ``KAMERA_KANIT.kaynak`` = URL [+ etiket] → ``"<URL> [<etiket>]"``.

    URL yoksa None (kaynak yok — etiket tek başına kaynak değildir).
    """
    if not url:
        return None
    return f"{url} [{etiket}]" if etiket else str(url)


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


def _dogrulanmis_algi_modeli_yukle(*, calisan_imgsz, beklenen_dosya):
    """Etkin algı modelini kayıtlı soyuyla doğruladıktan sonra yükle.

    Yalnız dosya adını göstermek kanıt değildir: yanlış/bozulmuş bir ağırlık aynı
    adla diskte durabilir. ``model_registry.resolve_model(verify=True)`` SHA-256,
    dosya varlığı ve profil biçimini YOLO nesnesi kurulmadan önce doğrular. YKİ
    ayrıca çalışan çıkarım boyunu profilin ``imgsz`` alanıyla karşılaştırır;
    uyuşmazlıkta model hiç yüklenmez (fail-closed).
    """
    from model_registry import resolve_model

    model_yolu, profil = resolve_model(
        registry_path=_PROJE_KOKU / "config" / "model_registry.json",
        verify=True)
    if model_yolu.name != beklenen_dosya:
        raise RuntimeError(
            "YKİ algı modeli kayıt defterinden ayrıştı: "
            f"beklenen={beklenen_dosya!r}, çözülen={model_yolu.name!r}")
    try:
        imgsz_uyumlu = int(profil.get("imgsz")) == int(calisan_imgsz)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "YKİ algı modeli profilinde geçerli `imgsz` yok") from exc
    if not imgsz_uyumlu:
        raise RuntimeError(
            "YKİ algı modeli çıkarım boyuyla ayrıştı: "
            f"profil={profil.get('imgsz')!r}, çalışan={calisan_imgsz!r}")

    from ultralytics import YOLO
    return YOLO(str(model_yolu), task="segment"), model_yolu, profil


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

    ⚠ Dizinin VAR OLMASI şart koşulmaz (temiz klon / paket eksik olabilir). O
    durumda ekran "Kaynak boş" der; sessizce BAŞKA bir kümeye düşmez.
    Fail-closed olan şey **bildirimin yokluğudur**, verinin değil.
    T220: yol depo köküne GÖRELİ (madde 16); mutlak yol da kabul (pathlib `/`).
    """
    profil, defter = _kayit_profili()
    ham = profil.get("kabul_kumesi") if isinstance(profil, dict) else None
    if not isinstance(ham, str) or not ham.strip():
        raise RuntimeError(
            f"Kayıt defterindeki etkin profilde `kabul_kumesi` yok/geçersiz "
            f"({defter}); hakem ekranı modeli hangi zeminde göstereceğini "
            "UYDURMAZ.")
    return _PROJE_KOKU / Path(ham.strip())     # göreli -> depo kökü; mutlak -> kendisi


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


#: CONTRACTS §7.6: tunel sayac artislari en cok bu aralikla gunluge yazilir.
TUNEL_SAYAC_LOG_ARALIGI_S = 1.0
#: Artisi KIRMIZI loglanan tunel sayaclari (kayip / tavan / akran degisimi).
TUNEL_KIRMIZI_SAYACLAR = ("zaman_asimi_dusen", "kimlik_boslugu", "tavan_ustu",
                          "akran_degisti")


def yks_udp_linki_ac(bind):
    """YKİ dinleme portunu tek sahipli aç; ikinci süreç sessizce bayt çalamaz."""
    return UDPLink(bind=bind, reuse=False)


def _repo_commit_oku(kok=_PROJE_KOKU):
    """Koşan çalışma ağacının commit kimliğini oku; paket kopyasında uydurma."""
    try:
        sonuc = subprocess.run(
            ("git", "rev-parse", "HEAD"), cwd=str(kok),
            capture_output=True, text=True, timeout=2.0, check=True)
        commit = sonuc.stdout.strip().lower()
    except (OSError, subprocess.SubprocessError):
        return None
    return (commit if len(commit) == 40
            and all(c in "0123456789abcdef" for c in commit) else None)


def _repo_calisma_agaci_oku(kok=_PROJE_KOKU):
    """Başlangıçtaki çalışma ağacı beyanını oku; okunamıyorsa temiz UYDURMA."""
    try:
        sonuc = subprocess.run(
            ("git", "status", "--porcelain=v1", "--untracked-files=all"),
            cwd=str(kok), capture_output=True, text=True, timeout=3.0,
            check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return {"durum": "BILINMIYOR", "degisiklikler": [],
                "hata": type(exc).__name__}
    satirlar = [satir for satir in sonuc.stdout.splitlines() if satir]
    return {"durum": "KIRLI" if satirlar else "TEMIZ",
            "degisiklikler": satirlar, "hata": None}


def _dosya_sha256_oku(yol):
    """Koşan kaynak dosyanın tam özetini oku; hata varsa kanıt uydurma."""
    import hashlib

    try:
        ozet = hashlib.sha256()
        with Path(yol).open("rb") as akis:
            for parca in iter(lambda: akis.read(1024 * 1024), b""):
                ozet.update(parca)
        return ozet.hexdigest()
    except OSError:
        return None


def yki_oturum_kunyesi(*, fda_kipi, dinleme, iha_hedef=None,
                       ika_hedef=None, seri_port=None, baud=None,
                       kamera_url=None, algi_kaynagi=None, gorunum=None,
                       baslatma_argumanlari=()):
    """YKS başlangıcını uçuş sonrasında yeniden kurmaya yeterli künye üret."""
    profil, _defter = _kayit_profili()
    model_yolu = profil.get("path") if isinstance(profil, dict) else None
    model_dosya = (str(model_yolu).replace("\\", "/").rsplit("/", 1)[-1]
                   if isinstance(model_yolu, str) else None)
    return {
        "gorev_kipi": "fda" if fda_kipi else "yarisma",
        "fda_kipi": bool(fda_kipi),
        "protokol_surum": PROTOCOL_VERSION,
        "dinleme": dinleme,
        "iha_hedef": list(iha_hedef) if iha_hedef is not None else None,
        "ika_hedef": list(ika_hedef) if ika_hedef is not None else None,
        "seri_port": seri_port,
        "baud": baud if seri_port is not None else None,
        "kamera_url": kamera_url,
        "algi_kaynagi": algi_kaynagi,
        "gorunum": gorunum,
        "model": {
            "model_id": profil.get("model_id"),
            "dosya": model_dosya,
            "imgsz": profil.get("imgsz"),
            "sha256": profil.get("sha256"),
        },
        "repo_commit": _repo_commit_oku(),
        # Commit tek başına yeterli değildir: çalışma ağacı kirliyse koşan kod
        # HEAD ile aynı olmayabilir. Durum + gerçek YKİ kaynak özeti birlikte
        # uçuş sonrası "hangi ekran koştu?" sorusunu sessizce geçiştirmez.
        "repo_calisma_agaci": _repo_calisma_agaci_oku(),
        "yki_kaynak_sha256": _dosya_sha256_oku(Path(__file__)),
        "baslatma_argumanlari": list(baslatma_argumanlari),
    }


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


def heartbeat_telemetrisi_dogrula(mesaj):
    """Ağdan gelen HEARTBEAT telemetrisini alan alan doğrula.

    Bir bozuk alan bütün heartbeat'i veya komşu geçerli alanları düşürmez;
    yalnız kendisi dışarıda bırakılır. JSON sayıları için bool özellikle
    reddedilir (Python'da ``bool``, ``int`` alt sınıfıdır). Böylece biçimleme
    hatası Tk ana döngüsünü kalıcı durduramaz ve NaN/Inf ekrana sızamaz.
    """
    if not isinstance(mesaj, dict):
        return {}, ("mesaj",)
    temiz = {}
    reddedilen = []

    def sayi(ad, *, alt=None, ust=None, ust_dahil=True):
        deger = mesaj.get(ad)
        if deger is None:
            return
        if isinstance(deger, bool) or not isinstance(deger, (int, float)):
            reddedilen.append(ad)
            return
        deger = float(deger)
        if (not math.isfinite(deger)
                or (alt is not None and deger < alt)
                or (ust is not None and
                    (deger > ust if ust_dahil else deger >= ust))):
            reddedilen.append(ad)
            return
        temiz[ad] = deger

    sayi("alt")
    sayi("hiz", alt=0.0)
    sayi("yon", alt=0.0, ust=360.0, ust_dahil=False)
    sayi("bat", alt=0.0)
    sayi("lat", alt=-90.0, ust=90.0)
    sayi("lon", alt=-180.0, ust=180.0)
    sayi("x")
    sayi("y")

    for ad, alt, ust in (("gps_fix", 0, 255), ("uydu", 0, 254),
                         ("bat_yuzde", 0, 100)):
        deger = mesaj.get(ad)
        if deger is None:
            continue
        if (isinstance(deger, bool) or not isinstance(deger, int)
                or not alt <= deger <= ust):
            reddedilen.append(ad)
        else:
            temiz[ad] = deger

    pixhawk = mesaj.get("pixhawk_canli")
    if pixhawk is not None:
        if type(pixhawk) is bool:
            temiz["pixhawk_canli"] = pixhawk
        else:
            reddedilen.append("pixhawk_canli")

    mod = mesaj.get("mod")
    if mod is not None:
        aday = mod.strip().upper() if isinstance(mod, str) else ""
        if (aday and len(aday) <= UCUS_MODU_AZAMI_KARAKTER
                and all(c.isascii() and (c.isalnum() or c in "_-")
                        for c in aday)):
            temiz["mod"] = aday
        else:
            reddedilen.append("mod")

    # Koordinatlar bir çifttir. Tek ekseni göstermek/kaydetmek geçerli konum
    # izlenimi verir; eşinden biri bozuksa ikisi de fail-closed çıkarılır.
    for a, b in (("lat", "lon"), ("x", "y")):
        if (a in temiz) != (b in temiz):
            temiz.pop(a, None)
            temiz.pop(b, None)
            for ad in (a, b):
                if ad not in reddedilen:
                    reddedilen.append(ad)
    return temiz, tuple(sorted(set(reddedilen)))


def ucus_modu_sunumu(mod):
    """Uçuş modunu operatöre yanlış 'manuel' hükmü kurmadan sun."""
    if mod == "AUTO":
        return "OTONOM GÖREV (AUTO)", YESIL
    if mod in ACIL_UCUS_MODLARI:
        return f"ACİL EMNİYET MODU ({mod}) — GÖREV SONLANDIRILIYOR", KIRMIZI
    return f"PIXHAWK MODU: {mod} — AUTO DEĞİL", SARI


def gps_gosterim_metni(telemetri):
    """Ham GNSS alanlarını insan-okunur yap; harita koordinatı üretme."""
    if not isinstance(telemetri, dict):
        telemetri = {}
    gecerli, sebep = gps_telemetrisi_dogrula(telemetri)
    lat, lon = telemetri.get("lat"), telemetri.get("lon")
    fix, uydu = telemetri.get("gps_fix"), telemetri.get("uydu")
    if lat is None or lon is None:
        konum = "konum YOK"
    else:
        try:
            lat_f, lon_f = float(lat), float(lon)
            konum = (f"{lat_f:.7f}, {lon_f:.7f}"
                     if math.isfinite(lat_f) and math.isfinite(lon_f)
                     else "konum BOZUK")
        except (TypeError, ValueError, OverflowError):
            konum = "konum BOZUK"
    fix_metin = f"fix {fix}" if fix is not None else "fix YOK"
    uydu_metin = f"{uydu} uydu" if uydu is not None else "uydu YOK"
    durum = "3B FIX ✓" if gecerli else f"FIX YETERSİZ: {sebep}"
    return (f"HAM GNSS: {konum} · {fix_metin} · {uydu_metin} · {durum} · "
            "SEMANTİK HARİTADA KULLANILMAZ")


def gps_telemetrisi_dogrula(telemetri):
    """Hakem ekranı için en az 3B fix + sonlu, bant içi koordinat iste."""
    if not isinstance(telemetri, dict):
        return False, "telemetri yok"
    fix = telemetri.get("gps_fix")
    if isinstance(fix, bool) or not isinstance(fix, int) or fix < 3:
        return False, "3B fix yok"
    try:
        lat = float(telemetri.get("lat"))
        lon = float(telemetri.get("lon"))
    except (TypeError, ValueError, OverflowError):
        return False, "konum yok/bozuk"
    if not math.isfinite(lat) or not math.isfinite(lon):
        return False, "konum sonlu değil"
    if not -90.0 <= lat <= 90.0 or not -180.0 <= lon <= 180.0:
        return False, "konum dünya bandı dışında"
    return True, "3B fix"


def _udp_adresi_gecerli(adr):
    return bool(
        isinstance(adr, tuple) and len(adr) == 2
        and isinstance(adr[0], str) and adr[0]
        and not isinstance(adr[1], bool) and isinstance(adr[1], int)
        and 1 <= adr[1] <= 65535)


def mesaj_kaynagi_dogrula(mesaj, adr, iha_peer, ika_peer):
    """UDP çerçevesini beklenen fiziksel uçla eşleştir.

    İHA algı/telemetri yayıncısı efemer UDP portu kullanır; bu nedenle
    OPEN_ROUTE/NO_ROUTE/IHA_LANDED/HEARTBEAT için Jetson IP'si pinlenir.
    Eyleyici ACK'i ise ``iha_komut_alici`` sabit portundan gelmelidir. İKA
    süreci sabit 5006 ucuyla eşlenir. ``adr=None`` seri taşıyıcıdır ve adres
    katmanında doğrulanamaz; protokol/sıra kilitleri yine uygulanır.
    """
    if adr is None:
        return True, "seri taşıyıcı"
    if not isinstance(mesaj, dict) or not _udp_adresi_gecerli(adr):
        return False, "bozuk mesaj veya UDP kaynak adresi"
    tip = mesaj.get("type")
    node = mesaj.get("node")
    iha_verisi = tip in (MESAJ_OPEN_ROUTE, MESAJ_NO_ROUTE, MESAJ_IHA_LANDED)
    if iha_verisi or (tip == MESAJ_HEARTBEAT and node == "iha"):
        if not _udp_adresi_gecerli(iha_peer):
            return False, "İHA kaynağı pinlenmemiş"
        return ((adr[0] == iha_peer[0]),
                "İHA verisi Jetson IP'sinden gelmeli")
    if tip == MESAJ_ACK and node == "iha":
        if not _udp_adresi_gecerli(iha_peer):
            return False, "İHA ACK kaynağı pinlenmemiş"
        return (adr == iha_peer,
                "İHA eyleyici ACK'i komut alıcısının tam ucundan gelmeli")
    if ((tip == MESAJ_HEARTBEAT and node == "ika")
            or (tip == MESAJ_ACK and node == "ika")):
        if not _udp_adresi_gecerli(ika_peer):
            return False, "İKA kaynağı pinlenmemiş"
        return (adr == ika_peer, "İKA verisi sabit ucundan gelmeli")
    return False, f"kaynak kuralı olmayan tip/node: {tip!r}/{node!r}"


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
    # ``__new__`` ile kurulan eski test fikstürleri için geriye uyumlu kapalı
    # varsayılan; gerçek kurucu bunları açıkça saha kipine göre ayarlar.
    kaynak_kilidi = False
    protokol_kilidi = False

    def __init__(
            self, kok, link, otomatik_onay=False, demo=False, ika_peer=None,
            iha_peer=None, kamera_url=None, hakem_log_yolu=None,
            oturum_kunyesi=None, kamera_etiket="", tek_rota=False):
        self.kok = kok
        self.tek_rota = bool(tek_rota)
        self.link = link
        self.reader = FrameReader()
        self.gelen = queue.Queue()
        self.otomatik_onay = otomatik_onay
        self.demo = demo
        self.protokol_kilidi = not demo
        self.kaynak_kilidi = bool(
            not demo and not saha_tasiyicisi_mi(link)
            and iha_peer is not None and ika_peer is not None)
        self._son_heartbeat_seq = {}
        self.kaynak_ret_sayaci = 0
        self.protokol_ret_sayaci = 0
        # Kritik IHA komutlari bir YKS surec/oturum kimligi tasir. Alici ayni
        # oturum+seq+cmd tekrarini yeniden eyleme donusturmez; yalniz guclu
        # ACK'i yineler. Boylece gecikmis UDP/SiK kuyrugu motoru ikinci kez
        # ARM/DISARM/PARACHUTE etmez.
        self.komut_oturumu = uuid.uuid4().hex
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
            MESAJ_OPEN_ROUTE: 0,
            "OPEN_ROUTE_RED": 0,
            MESAJ_NO_ROUTE: 0,
            MESAJ_IHA_LANDED: 0,
            MESAJ_HEARTBEAT: 0,
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
        # Yanlis tek tik; pervaneyi calistiramaz, havadaki araci indiremez ve
        # acil ucus modunu degistiremez. Tum kritik dugmeler ayni sozlesme
        # penceresini kullanir; yeni ciplak zaman esigi yoktur.
        self._kritik_teyit = {}
        self.acil_tekrar = AckliTekrar(
            self._ham_gonder, ARM_TEKRAR_ARALIGI_S,
            ARM_TEKRAR_UST_SINIRI)
        self.acil_bekleyen_komut = None
        self.acil_ack_zamani = None
        # K8: İKA'nın OPEN_ROUTE ACK kanıtı: seq -> duvar saati. Hakem 2. onayı
        # ancak geçerli rota seq'i bu sözlükte varsa verebilir (fail-closed).
        self.ika_rota_ack = {}
        # T224 (D-441): OPEN_ROUTE'tan ÖNCE gelen İKA ACK kopyası —
        # ref -> (geliş duvar saati, geliş monotonik, gelişte İHA havada mı).
        self._erken_ika_rota_ack = {}
        self.arm_acik = None
        self.tespit_onayli = False          # §2.2.3 iki aşamalı onayın 1. adımı
        self.t_iha0 = self.t_iha1 = None    # İHA görev kronometresi
        self.t_ika0 = self.t_ika1 = None    # İKA görev kronometresi
        self.t_haz0 = self.t_haz1 = None    # hazırlık kronometresi (§6.2)
        self.ceza_toplam = 0                # birikmiş ceza puanı
        self.parasut_teyit = 0.0            # iki adımlı paraşüt emniyeti
        self.mod = {}                       # node -> uçuş modu (AUTO/MANUEL)
        self.mod_durum_zamani = {}          # node -> son doğrulanmış mod heartbeat'i
        self._manuel_uyarildi = False
        self.telemetri_ret_sayaci = 0
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
        # T226: video kaynak etiketi (örn. "MK15 · HDMI · yakalama") — video
        # paneli başlığı ve KAMERA_KANIT `kaynak` alanı (CONTRACTS §6.8).
        # Karar üretmez; `_arayuz_kur`dan ÖNCE kurulur (başlık onu okur).
        self.kamera_etiket = kamera_etiketi_dogrula(kamera_etiket)
        self.kamera_istemci = None
        self._kamera_surum = -1
        self._kamera_foto = None
        # CONTRACTS §6.8 — döngüsel kanıt olaylarının KENAR durumu ve son
        # yazma damgası. Dördü de `_kanit_durumu_yaz` tarafından OKUNUR:
        # kenar tespiti için DURUM, tekrar sınırlaması için DAMGA gerekir.
        self._kamera_kanit_durumu = None
        self._son_kamera_kanit_monotonic = None
        self._telemetri_kanit_durumu = None
        self._son_telemetri_kanit_monotonic = None
        self.kanit_kaydi_hatasi = None
        self._kanit_kilidi_metni = None
        # Doğrudan sınıf kullanan test/demo fikstürleri None ile yazmasız
        # kalabilir; saha main() yolu her zaman varsayılan veya açık bir dosya
        # geçirir. Dosya açılamazsa kurucu yükseltir ve saha sessizce kanıtsız
        # başlamaz.
        self.hakem_kaydi = (
            HakemKaydi(hakem_log_yolu) if hakem_log_yolu is not None else None)

        self._arayuz_kur()
        if kamera_url:
            from kamera_istemci import KameraIstemci
            self.kamera_istemci = KameraIstemci(kamera_url)
            self.kamera_istemci.baslat()
        if oturum_kunyesi is not None and not isinstance(oturum_kunyesi, dict):
            raise TypeError("oturum_kunyesi dict veya None olmalı")
        hazir_kaydi = {
            "demo": bool(demo),
            "kamera_yapilandirildi": bool(kamera_url),
            "tasiyici": tasiyici_adi(link),
            "komut_oturumu": self.komut_oturumu,
        }
        if oturum_kunyesi:
            cakisan = sorted(set(hazir_kaydi) & set(oturum_kunyesi))
            if cakisan:
                raise ValueError(
                    f"oturum_kunyesi zorunlu alanı ezemez: {cakisan}")
            hazir_kaydi.update(oturum_kunyesi)
        self._kanit_yaz("YKS_ARAYUZ_HAZIR", **hazir_kaydi)
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
        # T226-D (D-448): küçük harita etiketleri (dar tuval, ölçülü yerleşim).
        self.f_mini = tkfont.Font(family="Segoe UI",
                                  size=MINI_HARITA_YAZI_PUNTO)
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
                   "RFD900A TX", "YKS (bu ekran)", "İKA"]
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
        if self.tek_rota:
            sol.baslik_etiketi.config(text="ALINAN ROTA — HAKEM İNCELEMESİ / METRE")
            sol.pack_propagate(False)

        anahtar = tk.Frame(sol, bg=PANEL)
        anahtar.pack(fill="x", padx=10, pady=(4, 0))
        self._gorunum_anahtari = anahtar   # T226: kamera çerçevesi bunun ALTINA
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
        self.btn_gor_rota = tk.Button(
            anahtar, text="Rota / hareket planı", font=self.f_kucuk,
            fg=METIN, bg="#232e3a", relief="flat", padx=8, pady=3,
            command=lambda: self.gorunum("rota"))
        self.btn_gor_rota.pack(side="left", padx=(6, 0))
        if self.tek_rota:
            self.btn_gor_harita.config(text="Rota haritası")
            self.btn_gor_algi.config(text="Yerel algı")
            self.btn_gor_kamera.config(text="Video / rota")
        self.rota_paneli = RotaInceleme(sol)

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
        # T226 (D-443 kusur a): başlık = kaynak etiketi + SABİT not; video ile
        # KÜÇÜK şematik harita YAN YANA — hakem rotayı video açıkken de görür.
        self.kamera_cerceve = tk.Frame(sol, bg=PANEL)
        self.lbl_kamera_baslik = tk.Label(
            self.kamera_cerceve, text=kamera_baslik_metni(self.kamera_etiket),
            font=self.f_kucuk, fg=SARI, bg=PANEL, anchor="w",
            wraplength=S(640), justify="left")
        self.lbl_kamera_baslik.pack(fill="x", padx=10, pady=(4, 0))
        kamera_govde = tk.Frame(self.kamera_cerceve, bg=PANEL)
        kamera_govde.pack(fill="both", expand=True)
        # Video karesinin İSTEDİĞİ boyut gövdeye yayılmaz: aksi hâlde geniş
        # kare sol paneli büyütür ve sağdaki onay panelini daraltırdı.
        kamera_govde.pack_propagate(False)
        self.videosuz_rota = RotaInceleme(kamera_govde)
        self._videosuz_rota_acik = False
        self.mini_harita_cerceve = tk.Frame(kamera_govde, bg=PANEL)
        self.mini_harita_cerceve.pack(side="right", fill="y", padx=(0, 10),
                                      pady=(4, 4))
        tk.Label(self.mini_harita_cerceve, text="ROTA — telsiz verisi (şematik)",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w").pack(fill="x")
        self.mini_harita = tk.Canvas(
            self.mini_harita_cerceve, width=S(MINI_HARITA_GENISLIK_PX),
            height=S(MINI_HARITA_YUKSEKLIK_PX), bg="#121920",
            highlightthickness=0)
        self.mini_harita.pack(anchor="n")
        # Yerleşim tamamlanınca (ilk gösterim, pencere boyutu) AYNI çizim yolu.
        self.mini_harita.bind(
            "<Configure>", lambda _e: self._harita_ciz(self.mini_harita))
        self.lbl_kamera_img = tk.Label(
            kamera_govde, bg="#121920", fg=SOLUK,
            text=("KAMERA URL YOK — --kamera-url http://<JETSON_IP>:8080"
                  if not self.kamera_url else "RAW kamera bağlanıyor…"),
            font=self.f_orta, justify="center")
        self.lbl_kamera_img.pack(side="left", padx=10, pady=(4, 4), fill="both",
                                 expand=True)
        self.lbl_kamera_bilgi = tk.Label(
            self.kamera_cerceve,
            text=(f"Kaynak: {self.kamera_url}" if self.kamera_url else
                  "Video RFD900A üzerinden TAŞINMAZ; ayrı LAN gerekir."),
            font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
            wraplength=S(640), justify="left")
        self.lbl_kamera_bilgi.pack(fill="x", padx=10, pady=(2, 4))
        self.gorunum_adi = "harita"

        # Acil durum senaryo tatbikatı (yalnız --demo modunda etkin)
        senaryo_baslik = tk.Label(sol, text="ACİL DURUM SENARYOLARI — arıza emniyet tatbikatı "
                           "(DDR B.3.3.1 tablosu; simülasyon)",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left")
        senaryo_baslik.pack(fill="x", padx=10)
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
        demo_baslik = tk.Label(sol, text="DEMO / SS KONTROLLERİ — kısayollar: F1–F6 senaryo · "
                           "N yeni tespit · R onayı sıfırla · A arm · V harita/algı · "
                           "C RAW kamera · "
                           "←/→ algı görüntüsü · K kaynak",
                 font=self.f_kucuk, fg=SOLUK, bg=PANEL, anchor="w",
                 wraplength=S(660), justify="left")
        demo_baslik.pack(fill="x", padx=10)
        dkf = tk.Frame(sol, bg=PANEL)
        dkf.pack(fill="x", padx=10, pady=(2, 10))
        for ad, kom in (("Yeni tespit üret (N)", self.yeni_tespit),
                        ("Hakem onayını sıfırla (R)", self.onay_sifirla)):
            tk.Button(dkf, text=ad, font=self.f_kucuk, fg=METIN, bg="#232e3a",
                      activebackground=MAVI, activeforeground=BG, relief="flat",
                      padx=7, pady=3,
                      state=("normal" if self.demo else "disabled"),
                      command=kom).pack(side="left", padx=(0, 6))

        if self.tek_rota and not self.demo:
            for kontrol in (senaryo_baslik, btnf, demo_baslik, dkf):
                kontrol.pack_forget()

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
        self.lbl_ucus = tk.Label(p3, text="İHA UÇUŞ DURUMU: PIXHAWK MODU BEKLENİYOR",
                                 font=self.f_orta, fg=KIRMIZI, bg=PANEL,
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
        if tasiyici_adi(self.link) == TASIYICI_TUNEL:
            tasiyici = "MAVLink TUNNEL (Pixhawk TELEM1 → RFD900A)"
        elif saha_tasiyicisi_mi(self.link):
            tasiyici = "RFD900A 915–928 MHz (seri)"
        else:
            tasiyici = f"UDP :{self.link.port}"
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
        satir3 = tk.Frame(gorev, bg=PANEL)
        satir3.pack(fill="x")

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

        # Acil komutlar paraşütten ayrıdır: FDA çoklu rotorda da kullanılabilir.
        # ACK yalnız Pixhawk'ın komutu KABUL ettiğini söyler; tamamlandığını değil.
        self.btn_rtl = gbuton(satir3, "ACİL RTL", lambda: self.acil_komut("RTL"))
        self.btn_land = gbuton(satir3, "ACİL LAND", lambda: self.acil_komut("LAND"))
        self.lbl_acil = tk.Label(
            satir3, text="ACİL UÇUŞ KOMUTU: — · RC pilotu fiziksel yedektir",
            font=self.f_orta, fg=SOLUK, bg=PANEL)
        self.lbl_acil.pack(side="left", padx=10)
        if self.tek_rota:
            alt.pack_configure(before=govde)
            gorev.pack_configure(before=govde)

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
        if (getattr(self, "tek_rota", False) and kaynak == "protokol"
                and getattr(self, "rota", None) and not getattr(self, "rota_yok", None)
                and d["karar"] == f"{self.rota['road']} · {self.rota['label'].upper()}"):
            self.lbl_karar.config(text="TEK ROTA" if self._tek_rota_gecerli() else "GEOMETRİ YOK",
                                  fg=d["renk"] if self._tek_rota_gecerli() else KIRMIZI)
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
    def _mxy(self, x_m, y_m, tuval=None):
        """Metre (0..50, y kuzey) → canvas pikseli (``tuval`` yoksa ana harita)."""
        c = self.harita if tuval is None else tuval
        w = c.winfo_width() or 480
        h = c.winfo_height() or 480
        # T226-D (D-448): ölçülü yerleşimli tuvalin (küçük harita; ana haritada
        # yalnız ROTA YOK'ta ve gerekirse) arena alanı `_harita_ciz`de ölçülüp
        # kaydedilir. Kayıt yoksa alan eskisi gibi saf fonksiyondan gelir.
        alan = getattr(self, "_olculu_alan", {}).get(str(c))
        sol, ust, olcek = alan if alan is not None else harita_cizim_alani(w, h)
        px = sol + (x_m / ARENA_M) * olcek
        py = ust + (1.0 - y_m / ARENA_M) * olcek   # y yukarı = kuzey
        return px, py

    @staticmethod
    def _metin_kutusu(c, metin, font, genislik=0):
        """``metin``in ``c`` tuvalinde kaplayacağı ``(w, h)`` pikseli (T226-D).

        GEÇİCİ bir metin öğesiyle Tk'nin KENDİ yerleşimi (satır sarma dahil)
        ölçülür ve öğe hemen silinir — tahmini karakter genişliği kullanılmaz.
        Ölçüm yüzeyi olmayan tuvalde (Tk'siz kayıt tuvali) ``None`` döner;
        çağıran sabit yerleşime düşer.
        """
        if not (hasattr(c, "bbox") and hasattr(c, "create_text")):
            return None
        try:
            oge = c.create_text(0, 0, text=metin, font=font, anchor="nw",
                                width=max(0, int(genislik)))
            try:
                kutu = c.bbox(oge)
            finally:
                c.delete(oge)
            x0, y0, x1, y1 = (int(v) for v in kutu)
        except Exception:                        # ölçülemedi → sabit yerleşim
            return None
        return x1 - x0, y1 - y0

    @staticmethod
    def _kesisim_alani(a, b):
        """İki ``(x0, y0, x1, y1)`` kutusunun kesişim alanı (0 = kesişmez)."""
        return (max(0, min(a[2], b[2]) - max(a[0], b[0]))
                * max(0, min(a[3], b[3]) - max(a[1], b[1])))

    def _etiket_yerlestir(self, c, oge, adaylar):
        """T226-D: metin öğesini, başka bir METİNLE kesişmeyen ve tuvalden
        taşmayan İLK aday konuma ``(x, y, çapa)`` taşı; hiçbiri boş değilse
        (taşma, kesişim alanı) en küçük olana. Yalnız küçük haritada kullanılır.
        """
        tw, th = c.winfo_width(), c.winfo_height()
        en_iyi = None
        for x, y, capa in adaylar:
            c.coords(oge, x, y)
            c.itemconfigure(oge, anchor=capa)
            kutu = c.bbox(oge)
            ceza = sum(self._kesisim_alani(kutu, c.bbox(d))
                       for d in c.find_overlapping(*kutu)
                       if d != oge and c.type(d) == "text")
            tasma = (kutu[0] < 0 or kutu[1] < 0 or kutu[2] > tw
                     or kutu[3] > th)
            if ceza == 0 and not tasma:
                return
            skor = (tasma, ceza)
            if en_iyi is None or skor < en_iyi[0]:
                en_iyi = (skor, x, y, capa)
        _skor, x, y, capa = en_iyi
        c.coords(oge, x, y)
        c.itemconfigure(oge, anchor=capa)

    def _harita_olculu_yerlesim(self, c, w, rota_yok_metni, inset_var):
        """T226-D (D-448): üst bant + arena alanını METİN KUTULARI ÖLÇÜLEREK kur.

        Dönüş: ``font`` etiket fontu · ``kucuk`` · ``bant_h``/``bant_w`` ROTA
        YOK bandı · ``uyari_y`` SEMATİK uyarısı · ``aciklama_y`` renk
        açıklaması (küçük) · ``etiket_h`` tek satır yüksekliği (küçük) ·
        ``alan`` ``(sol, ust, olcek)`` ya da ``None`` (= sabit ana harita alanı).

        Küçük harita (``inset_var=False``): uyarı → renk açıklaması (yeri HER
        durumda ayrılır: boşta ↔ OPEN_ROUTE arena zıplamaz) → HB etiketi →
        arena → İKA-KB yarım satırı + şerit adları satırı.
        ROTA YOK (iki harita): bant yüksekliği bant metninden ölçülür, uyarı
        bandın ALTINA (+S(4)) iner; ana haritada arena YALNIZ HB etiketi
        uyarıya değecekse aşağı iner. Ölçüm yüzeyi olmayan tuvalde bant sabit
        yüksekliğe (``max(S(42), h // 10)``), arena sabit alana düşer.
        """
        kucuk = not inset_var
        f = (getattr(self, "f_mini", None) if kucuk else None) or self.f_kucuk
        h = c.winfo_height() or S(420)
        pay = S(HARITA_METIN_PAYI_PX)
        _ux, uyari_y0, uyari_w = sematik_uyari_yerlesimi(w, inset_var)
        y = {"font": f, "kucuk": kucuk, "bant_h": None, "bant_w": uyari_w,
             "uyari_y": uyari_y0, "aciklama_y": None, "etiket_h": None,
             "alan": None}
        if rota_yok_metni:
            bant = self._metin_kutusu(c, rota_yok_metni, f, uyari_w)
            y["bant_h"] = max(S(42), h // 10,
                              0 if bant is None else bant[1] + 2 * pay)
            y["uyari_y"] = y["bant_h"] + pay
        uyari = self._metin_kutusu(c, SEMATIK_GOSTERIM_UYARISI, f, uyari_w)
        satir = self._metin_kutusu(c, HARITA_SATIR_OLCU_METNI, f)
        if uyari is None or satir is None:
            return y
        ust_sinir = y["uyari_y"] + uyari[1]         # üst metin yığınının altı
        hb_pay = 1.0 - HB_KONUM_M[1] / ARENA_M       # H kutusu merkezi / olcek
        if kucuk:
            aciklama = self._metin_kutusu(c, RENK_ACIKLAMASI, f, uyari_w)
            y["aciklama_y"] = uyari_y0 + uyari[1] + S(2)
            ust_sinir = max(ust_sinir,
                            y["aciklama_y"] + (aciklama or (0, 0))[1])
            y["etiket_h"] = satir[1]
            # İKA-KB etiketi arena altına en çok yarım satır taşar; şerit
            # adları onun altında tek satır (`n` çapası).
            alt = max(S(2), (satir[1] + 1) // 2 + S(2)) + satir[1] + S(2)
            ust = ust_sinir + pay

            def hb_ustu(u, olcek):       # HB `s` çapalı: H kutusunun (±12) üstü
                return u + hb_pay * olcek - 12 - S(2) - satir[1]
        else:
            alt = S(HARITA_ALT_KENAR_PX)
            ust = S(HARITA_UST_BANT_PX)

            def hb_ustu(u, olcek):       # ana harita: HB merkezi H'nin 20 px üstü
                return u + hb_pay * olcek - 20 - (satir[1] + 1) // 2
        for _ in range(12):
            _sol, u, olcek = harita_cizim_alani(w, h, ust_px=ust, alt_px=alt)
            eksik = ust_sinir + pay - hb_ustu(u, olcek)
            if eksik <= 0:
                break
            ust += int(math.ceil(eksik))
        if kucuk or ust != S(HARITA_UST_BANT_PX):
            y["alan"] = harita_cizim_alani(w, h, ust_px=ust, alt_px=alt)
        return y

    def _harita_ciz(self, tuval=None):
        """Şematik haritayı çiz. ``tuval`` verilmezse ANA harita çizilir ve
        kamera görünümündeki KÜÇÜK kopya (T226, D-443 kusur a) da AYNI yoldan
        tazelenir: seçili şerit, ROTA YOK bandı ve SEMATIK uyarısı ikisinde de
        aynı koddan gelir — yalnız tuval boyutu farklıdır.

        T226-D (D-448): küçük haritada etiketler METİN KUTUSU ÖLÇÜLEREK
        yerleşir (sabit ofsetler 450×495'te üst üste biniyordu). Ana harita
        OPEN_ROUTE/boşta master ile BAYT-EŞ; yalnız ROTA YOK'ta bant metni
        ölçülür ve SEMATİK uyarısı bandın ALTINA iner."""
        if tuval is None:
            mini = getattr(self, "mini_harita", None)
            if mini is not None and getattr(self, "gorunum_adi", None) == "kamera":
                self._harita_ciz(mini)
            tuval = self.harita
        c = tuval
        if getattr(self, "tek_rota", False):
            plan, durum, renk = self._tek_rota_harita_verisi()
            rota_detay_haritasi(c, plan, durum=durum, renk=renk)
            return
        # Inset (İHA-UB genel saha) yalnız ana haritada çizilir.
        inset_var = c is self.harita
        c.delete("all")
        w = c.winfo_width()
        if w <= 1:
            w = S(480)
        # Yeni NO_ROUTE, eski OPEN_ROUTE önbelleğini görsel olarak geçersiz
        # kılar: hakem ekranda yeşil bir rota görüp yanlış onay vermemelidir.
        acik = (self.rota["road"]
                if self.rota and not self.rota_yok
                and rota_ankor_uyarisi(self.rota) is None else None)
        rota_yok_metni = None
        if self.rota_yok:
            sebep = self.rota_yok.get("sebep", "bilinmeyen neden")
            detay = self.rota_yok.get("detay")
            rota_yok_metni = f"ROTA YOK — {sebep} · İKA GÜVENLİ DURUŞTA"
            if detay:
                rota_yok_metni += f"\n{detay}"
        # T226-D: ölçülü yerleşim küçük haritada HER durumda, ana haritada
        # YALNIZ ROTA YOK'ta. `olcu is None` = ana harita OPEN_ROUTE/boşta:
        # master ile bayt-eş yol (kapı: tests/artifacts/t226d/ana_harita_master.json).
        olcu = (self._harita_olculu_yerlesim(c, w, rota_yok_metni, inset_var)
                if (not inset_var or rota_yok_metni) else None)
        alanlar = self.__dict__.setdefault("_olculu_alan", {})
        if olcu is not None and olcu["alan"] is not None:
            alanlar[str(c)] = olcu["alan"]
        else:
            alanlar.pop(str(c), None)
        kucuk = olcu is not None and olcu["kucuk"]
        f_etiket = self.f_kucuk if olcu is None else olcu["font"]
        # grid (5 m)
        for m in range(0, 51, 5):
            x0, y0 = self._mxy(m, 0, c)
            x1, y1 = self._mxy(m, 50, c)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
            x0, y0 = self._mxy(0, m, c)
            x1, y1 = self._mxy(50, m, c)
            c.create_line(x0, y0, x1, y1, fill="#1c2630")
        # arena çerçevesi
        x0, y0 = self._mxy(0, 0, c)
        x1, y1 = self._mxy(50, 50, c)
        c.create_rectangle(x0, y0, x1, y1, outline=CIZGI, width=2)

        # 3 yol koridoru — tespit sonrası: açık yol YEŞİL, geri kalan HER YER
        # (kapalı koridorlar + moloz sahası) KIRMIZI = gidilemez
        if acik is not None:
            c.create_rectangle(x0, y0, x1, y1, fill=KIRMIZI, stipple="gray12",
                               outline="")
            lx, _uyari_y, aciklama_w = sematik_uyari_yerlesimi(w, inset_var)
            c.create_text(
                lx, (olcu["aciklama_y"] if kucuk and olcu["aciklama_y"] is not None
                     else S(HARITA_RENK_ACIKLAMA_Y_PX)),
                text=RENK_ACIKLAMASI,
                fill=SOLUK, font=f_etiket, anchor="nw", width=aciklama_w)
        # T226-D küçük harita: şerit adları arena + İKA-KB etiketinin ALTINDA
        # tek satır; kapalı şerit etiketi şerit genişliğine SIĞMAZSA yalnız "✕".
        serit_adi_y = None
        kapali_etiketi = KAPALI_SERIT_ETIKETI
        serit_adi_kisa = False
        if kucuk and olcu["etiket_h"] is not None:
            _ax, arena_alt = self._mxy(0, 0, c)
            _kx, kb_y = self._mxy(*KB_KONUM_M, c)
            serit_adi_y = max(arena_alt + S(2),
                              kb_y + (olcu["etiket_h"] + 1) // 2 + S(2))
            kutu = self._metin_kutusu(c, KAPALI_SERIT_ETIKETI, f_etiket)
            serit_px = min(self._mxy(xm + yg, 0, c)[0] - self._mxy(xm - yg, 0, c)[0]
                           for xm, yg, _giris, _cikis in SERIT_CIZIM_TABLOSU.values())
            if kutu is None or kutu[0] > serit_px - S(2):
                kapali_etiketi = KAPALI_SERIT_ETIKETI_KISA
            # Sıkışık küçük haritada (küçük ekran / yüksek DPI, ölçüldü: 1,5
            # ölçekte ~450×340) komşu şerit adları birbirine değiyorsa yalnız
            # şerit NUMARASI yazılır; seçili şerit yine YEŞİL, tam ad sağ
            # paneldeki karar kutusundadır.
            merkezler = sorted(self._mxy(g[0], 0, c)[0]
                               for g in SERIT_CIZIM_TABLOSU.values())
            aralik = min(b - a for a, b in zip(merkezler, merkezler[1:]))
            for yol in SERIT_CIZIM_TABLOSU:
                ad_kutusu = self._metin_kutusu(
                    c, f"{yol}·{ROAD_LABEL[yol].upper()}", f_etiket)
                if (ad_kutusu is None
                        or ad_kutusu[0] > aralik - S(HARITA_METIN_PAYI_PX)):
                    serit_adi_kisa = True
        for yol, geometri in SERIT_CIZIM_TABLOSU.items():
            xm, yari_genislik_m, giris_y_m, cikis_y_m = geometri
            secili = (yol == acik)
            px0, py0 = self._mxy(xm - yari_genislik_m, giris_y_m, c)
            px1, py1 = self._mxy(xm + yari_genislik_m, cikis_y_m, c)
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
            tx, ty = self._mxy(xm, -2.4, c)          # arena çerçevesinin ALTINA yaz
            ad_capa = {}
            if serit_adi_y is not None:
                ty, ad_capa = serit_adi_y, {"anchor": "n"}
            c.create_text(tx, ty, text=(f"{yol}" if serit_adi_kisa
                                        else f"{yol}·{ROAD_LABEL[yol].upper()}"),
                          fill=YESIL if secili else SOLUK, font=f_etiket,
                          **ad_capa)
            if not secili and acik is not None:
                kx, ky = self._mxy(xm, 25, c)
                c.create_text(kx, ky, text=kapali_etiketi, fill="#ff8878",
                              font=f_etiket)

        # İKA-KB (başlangıç, güney) ve HB (hedef, kuzey)
        kx, ky = self._mxy(*KB_KONUM_M, c)
        c.create_rectangle(kx - 12, ky - 12, kx + 12, ky + 12, outline=MAVI, width=2)
        c.create_text(kx + 12 + S(4) if kucuk else kx + 16, ky, text="İKA-KB",
                      fill=MAVI, font=f_etiket, anchor="w")
        hx, hy = self._mxy(*HB_KONUM_M, c)
        c.create_rectangle(hx - 12, hy - 12, hx + 12, hy + 12, outline=KIRMIZI, width=2)
        c.create_text(hx, hy, text="H", fill=KIRMIZI, font=self.f_orta)
        # Küçük haritada HB etiketi H kutusunun ÜSTÜNE oturur (`s` çapası).
        hb_y, hb_capa = ((hy - 12 - S(2), {"anchor": "s"}) if kucuk
                         else (hy - 20, {}))
        c.create_text(hx, hb_y, text="HB (hedef)", fill=KIRMIZI, font=f_etiket,
                      **hb_capa)

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
            pks = [self._mxy(x, y, c) for x, y in noktalar]
            for (ax, ay), (bx, by) in zip(pks, pks[1:]):
                c.create_line(ax, ay, bx, by, fill=YESIL, width=3, arrow="last")
            rx, ry = pks[0]
            c.create_oval(rx - 5, ry - 5, rx + 5, ry + 5, fill=SARI, outline="")
            # T226-D: küçük haritada "ref" İKA-KB/şerit adlarıyla KESİŞMEYEN
            # yana yerleşir (şerit 3'te sol yan İKA-KB'nin üstüne düşüyordu).
            ref_adaylari = (((rx - S(8), ry, "e"), (rx + S(8), ry, "w"),
                             (rx - S(8), ry - S(8), "se"),
                             (rx + S(8), ry - S(8), "sw")) if kucuk
                            else ((rx - 16, ry, "e"),))
            ref_x, ref_y, ref_capa = ref_adaylari[0]
            ref = c.create_text(ref_x, ref_y, text="ref", fill=SARI,
                                font=f_etiket, anchor=ref_capa)
            if len(ref_adaylari) > 1:
                self._etiket_yerlestir(c, ref, ref_adaylari)
        if rota_uyarisi:
            ux, uy = self._mxy(25, 25, c)
            c.create_text(ux, uy, text=rota_uyarisi, fill=KIRMIZI,
                          font=self.f_orta, anchor="center", width=w - S(48))

        if rota_yok_metni:
            # T226-D (D-448): bant yüksekliği METİNDEN ölçülür (detay satırı
            # bandın dışına taşıyordu) ve metin SEMATİK uyarısıyla aynı yatay
            # aralıkta (ana haritada inset'in solunda) sarılır.
            bant_h = olcu["bant_h"]
            c.create_rectangle(0, 0, w, bant_h, fill=KIRMIZI, outline="")
            c.create_text(S(12), bant_h // 2, text=rota_yok_metni, fill="white",
                          font=f_etiket, anchor="w", width=olcu["bant_w"])

        # Hakemin GPS sanmaması gereken semantik gösterim uyarısı en son
        # çizilir; grid/rota-yok katmanları metni sonradan örtemez. Sağ üstteki
        # inset ayrı çağrıda çizildiği için yatay kutular da çakışmaz.
        # T226-D (D-448): ROTA YOK bandı varken uyarı bandın ALTINA iner
        # (bant alti + S(4)); önceden ikisi de üst banttaydı ve üst üste
        # biniyordu (ana harita bbox (17,22,518,50) / (17,12,547,40)).
        uyari_x, uyari_y, uyari_w = sematik_uyari_yerlesimi(w, inset_var)
        if olcu is not None:
            uyari_y = olcu["uyari_y"]
        c.create_text(uyari_x, uyari_y, text=SEMATIK_GOSTERIM_UYARISI,
                      fill=SARI, font=f_etiket, anchor="nw",
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
            # UDP datagramı zaten bir çerçeve sınırıdır. Kalıcı seri tamponunu
            # datagramlar arasında kullanmak, newline'sız tek bozuk paketin
            # sonraki geçerli ACK/HEARTBEAT'i de kendine yapıştırıp yutmasına
            # izin veriyordu. Seri hatta parçalı çerçeve desteği korunur.
            okuyucu = FrameReader() if adr is not None else self.reader
            for m in okuyucu.feed(d):
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
        try:
            self._tunel_sayac_izle()
        except Exception as exc:              # izleme hakem ekranini DONDURMAZ
            self._logla(f"⚠ tünel sayaç izleme hatası — {type(exc).__name__}: {exc}",
                        "sari")
        self._kamera_tazele()
        self._durum_tazele()
        self.kok.after(120, self._tik)

    def _tunel_sayac_izle(self, simdi=None):
        """CONTRACTS §7.6: tunel sayac artislarini en cok 1 Hz ile KIRMIZI yaz.

        `zaman_asimi_dusen`, `kimlik_boslugu`, `tavan_ustu`, `akran_degisti`
        artislari hakem gunlugunde gorunur; seri/UDP kipinde hicbir sey yapmaz.
        """
        if tasiyici_adi(self.link) != TASIYICI_TUNEL:
            return None
        sayac = getattr(self.link, "sayac", None)
        if not isinstance(sayac, dict):
            return None
        simdi = time.monotonic() if simdi is None else float(simdi)
        son_t = getattr(self, "_tunel_sayac_t", None)
        if son_t is not None and simdi - son_t < TUNEL_SAYAC_LOG_ARALIGI_S:
            return None
        self._tunel_sayac_t = simdi
        onceki = getattr(self, "_tunel_sayac_onceki", None) or {}
        artis = {k: int(sayac.get(k, 0)) - int(onceki.get(k, 0))
                 for k in TUNEL_KIRMIZI_SAYACLAR
                 if int(sayac.get(k, 0)) > int(onceki.get(k, 0))}
        self._tunel_sayac_onceki = dict(sayac)
        if artis:
            self._logla("TÜNEL SAYAÇ ARTIŞI: " + " ".join(
                f"{k}+{v}" for k, v in artis.items()), "kirmizi")
        return artis

    def _heartbeat_sirasi_gecerli(self, dugum, seq, simdi=None):
        """Aynı canlı oturumda geri/tekrar heartbeat'in durumu ezmesini önle."""
        if (dugum not in ("iha", "ika") or isinstance(seq, bool)
                or not isinstance(seq, int) or seq < 0):
            return False
        simdi = time.monotonic() if simdi is None else float(simdi)
        onceki = getattr(self, "_son_heartbeat_seq", {}).get(dugum)
        if onceki is not None:
            onceki_seq, onceki_zaman = onceki
            if seq <= onceki_seq and simdi - onceki_zaman <= ARM_DURUM_TAZELIK_S:
                return False
        if not hasattr(self, "_son_heartbeat_seq"):
            self._son_heartbeat_seq = {}
        self._son_heartbeat_seq[dugum] = (seq, simdi)
        return True

    def _mesaj_isle(self, m, adr):
        if getattr(self, "protokol_kilidi", False):
            if (not isinstance(m, dict) or m.get("v") != PROTOCOL_VERSION
                    or not isinstance(m.get("type"), str)):
                self.protokol_ret_sayaci = getattr(
                    self, "protokol_ret_sayaci", 0) + 1
                if self.protokol_ret_sayaci in (1, 10, 100):
                    self._logla("⚠ PROTOKOL ZARFI REDDEDİLDİ: sürüm/tip bozuk "
                                f"(sayı={self.protokol_ret_sayaci})", "sari")
                return
        if getattr(self, "kaynak_kilidi", False):
            uygun, sebep = mesaj_kaynagi_dogrula(
                m, adr, getattr(self, "sabit_adr", {}).get("iha"),
                getattr(self, "sabit_adr", {}).get("ika"))
            if not uygun:
                self.kaynak_ret_sayaci = getattr(
                    self, "kaynak_ret_sayaci", 0) + 1
                if self.kaynak_ret_sayaci in (1, 10, 100):
                    self._logla(f"⚠ KAYNAK REDDEDİLDİ: {sebep}; adr={adr!r} "
                                f"(sayı={self.kaynak_ret_sayaci})", "sari")
                return
        tip = m.get("type")
        if tip == MESAJ_OPEN_ROUTE:
            guven_reddi = rota_guven_reddi(m.get("conf"))
            if guven_reddi is not None:
                self._open_route_guven_reddini_goster(m, guven_reddi)
                return
            self._dugum_adresini_ogren("iha", adr)
            yeni = (self.rota is None) or (m["seq"] != self.rota["seq"])
            if not yeni and getattr(self, "tek_rota", False):
                yeni = (m.get("ref_xy") != self.rota.get("ref_xy")
                        or m.get("waypoints") != self.rota.get("waypoints"))
                if yeni:
                    self.ika_rota_ack.pop(m["seq"], None)
                    self._erken_ika_rota_ack.pop(m["seq"], None)
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
            # T248 (curutucu bulgusu): TEKRAR gonderilen OPEN_ROUTE (ayni seq)
            # de `rota_yok`u temizler ama `yeni` FALSE oldugu icin asagidaki
            # cizim blogu kosmaz. Ekranin durumla ayrisip ayrismadigini bu
            # bayrak olcer; kullanimi `if yeni:` blogunun HEMEN ALTINDA.
            rota_yok_temizlendi = self.rota_yok is not None
            self.rota_yok = None
            self.rx_alim[m["seq"]] = self.rx_alim.get(m["seq"], 0) + 1
            ankor_uyarisi = rota_ankor_uyarisi(m)
            if yeni:
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac[MESAJ_OPEN_ROUTE] += 1
                # CONTRACTS §6.8 — hakem onayının dayanağı olan tespit:
                # hangi şerit, hangi güvenle, kaç waypoint ile geldi.
                self._kanit_yaz("ROTA_ALINDI", seq=m.get("seq"),
                                road=m.get("road"), label=m.get("label"),
                                conf=m.get("conf"),
                                waypoint=len(m.get("waypoints") or []),
                                ankor=not bool(ankor_uyarisi),
                                **self._rota_kanit_geometrisi(m))
                rota_etiketi = ("tek rota" if getattr(self, "tek_rota", False)
                                else f"yol={m['road']}({m['label']})")
                self._logla(f"OPEN_ROUTE  {rota_etiketi} "
                            f"güven={m['conf']} seq={m['seq']} wp={len(m['waypoints'])}",
                            "yesil")
                if self.t_iha1 is not None:
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
                    self._onay_dugmesini_ciz(
                        True, "1) TESPİTİ DOĞRULA (§2.2.3)")
                    if not self._kanit_kilidi_var():
                        self.lbl_onay.config(
                            text="⚠ Hakem onayı BEKLENİYOR — İHA tekrar "
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
                              "RFD900A TX", "YKS (bu ekran)"))
                if self.otomatik_onay and not ankor_uyarisi:
                    self.kok.after(2500, self.onayla)
            elif rota_yok_temizlendi:
                # 🔴 T248: NO_ROUTE'tan SONRA gelen TEKRAR kopyasi (sahada
                # `iha_sender._tekrarli_gonder(repeat=8, interval=0.25)`
                # tam olarak bunu uretir) durumu "rota kabul"e cevirir; harita
                # cizilmezse hakem ekraninda "ROTA YOK" bandi ASILI KALIR ve
                # hakem rotayi EKRANDAN onayladigi icin gorev puani etkilenir.
                # DAR kosul: yalniz DURUM DEGISTIYSE cizilir — 8 kopyanin
                # tamaminda cizmek 8 kat gereksiz yuktur (kapi: H2g/T248b).
                self._harita_ciz()
            # T224 (D-441): İKA'nın ACK kopyası bu rotadan ÖNCE geldiyse
            # tampondan eşlenir — kanıt olayı ROTA_ALINDI'dan SONRA düşer.
            self._erken_ika_rota_ack_esle(m["seq"])
            # tekrar-gönderim mekanizması canlı izlensin (jüri: ACK'siz teslim yok)
            self._kutu_yaz(
                "protokol",
                detay=f"{self._detay_base} · alım #{self.rx_alim[m['seq']]}")
        elif tip == MESAJ_NO_ROUTE:
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
            elif saha_tasiyicisi_mi(self.link):
                self.link.send(encode(ack(m["seq"], "yks", tip)))
            self.sayac["ACK_TX"] += 1
            if yeni:
                sebep = m.get("sebep", "bilinmeyen neden")
                detay = m.get("detay")
                self.onaylandi = False
                self.tespit_onayli = False
                self.sayac[MESAJ_NO_ROUTE] += 1
                # CONTRACTS §6.8: "rota yok" SESSİZLİKTEN farklıdır (§6.1) —
                # kayıtta da farklı görünmek zorundadır.
                self._kanit_yaz("ROTA_YOK", seq=m.get("seq"), sebep=sebep,
                                detay=detay)
                self._detay_base = f"seq={m['seq']} · {sebep}"
                self._kutu_yaz("protokol", karar="ROTA YOK", renk=KIRMIZI,
                               detay=self._detay_base
                               + (f" · {detay}" if detay else ""))
                self._onay_dugmesini_ciz(
                    False, "ROTA YOK — ACK OTOMATİK GÖNDERİLDİ")
                if not self._kanit_kilidi_var():
                    self.lbl_onay.config(
                        text="Costmap güvenli rota üretmedi; İKA hareket etmez.",
                        fg=KIRMIZI)
                self._kutu_yaz("protokol", guven=0.0)
                self._harita_ciz()
                self._logla(f"NO_ROUTE · {sebep}"
                            + (f" · {detay}" if detay else "")
                            + " → güvenli duruş ACK'i gönderildi", "sari")
        elif tip == MESAJ_ACK:
            self._ack_isle(m, adr)
        elif tip == MESAJ_IHA_LANDED:
            seq = m.get("seq")
            if (m.get("node") != "iha" or isinstance(seq, bool)
                    or not isinstance(seq, int)):
                return
            # T206 (D-405 Q4): `ref_tip` — IHA_LANDED seq'i İHA'nın OPEN_ROUTE
            # seq'iyle çakışırsa bu ACK yanlış bekleyene bağlanamaz (§6.6).
            if adr is not None:
                self.link.send(encode(ack(seq, "yks", tip)), adr)
            elif saha_tasiyicisi_mi(self.link):
                self.link.send(encode(ack(seq, "yks", tip)))
            self.sayac["ACK_TX"] += 1
            if seq != self.iha_landed_seq:
                self.iha_landed_seq = seq
                self.sayac[MESAJ_IHA_LANDED] += 1
                # CONTRACTS §6.8 — §2.2.3 SIRA denetimi kayda da düşer:
                # iniş kanıtı geldiğinde İKA'nın rota ACK'i var mıydı?
                self._kanit_yaz(
                    "IHA_INIS_KANITI", seq=seq,
                    ika_rota_ack_var=bool(
                        self.rota and self.rota.get("seq") in self.ika_rota_ack))
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
        elif tip == MESAJ_HEARTBEAT:
            dugum = m.get("node", "?")
            _hb_simdi = time.monotonic()
            if (getattr(self, "protokol_kilidi", False)
                    and not self._heartbeat_sirasi_gecerli(
                        dugum, m.get("seq"), _hb_simdi)):
                self.protokol_ret_sayaci = getattr(
                    self, "protokol_ret_sayaci", 0) + 1
                if self.protokol_ret_sayaci in (1, 10, 100):
                    self._logla(f"⚠ HEARTBEAT SIRA REDDİ: node={dugum!r} "
                                f"seq={m.get('seq')!r}", "sari")
                return
            self.son_hb[dugum] = _hb_simdi   # D-384: monotonik
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
            # Ağ girdisi ayrıca alan alan doğrulanır; ör. `bat="x"` doğrudan
            # ``:.1f`` biçimleyicisine ulaşırsa bütün Tk tazeleme zinciri ölür.
            temiz, bozuk = heartbeat_telemetrisi_dogrula(m)
            if bozuk:
                self.telemetri_ret_sayaci = getattr(
                    self, "telemetri_ret_sayaci", 0) + 1
                if self.telemetri_ret_sayaci in (1, 10, 100):
                    self._logla(
                        "⚠ BOZUK HEARTBEAT TELEMETRİSİ alan bazında elendi: "
                        + ", ".join(bozuk), "sari")
            tel = {k: temiz[k] for k in (
                "alt", "hiz", "yon", "bat", "bat_yuzde", "uydu", "lat",
                "lon", "gps_fix", "pixhawk_canli") if k in temiz}
            self.tel[dugum] = tel
            if dugum == "iha":
                armed = arm_telemetri_degeri(m)
                if armed is not None:
                    self.arm_acik = armed
                    self.arm_durum_zamani = time.monotonic()
                    self._arm_bekleyeni_tamamla()
                else:
                    # HEARTBEAT bir snapshot'tir. Navitas link'i canli olsa da
                    # Pixhawk armed alani yoksa son bilinen durumu tasimak,
                    # kopuk otopilotla firlatma dugmesini acik birakirdi.
                    self.arm_acik = None
                    self.arm_durum_zamani = None
                self._arm_ui_uygula()
            mod = temiz.get("mod")
            if mod is not None:
                self.mod[dugum] = mod
                if not hasattr(self, "mod_durum_zamani"):
                    self.mod_durum_zamani = {}
                self.mod_durum_zamani[dugum] = _hb_simdi
                if dugum == "iha":
                    self._ucus(*ucus_modu_sunumu(mod))
                    self._acil_bekleyeni_tamamla()
                if (mod not in ({"AUTO"} | ACIL_UCUS_MODLARI)
                        and not self._manuel_uyarildi):
                    self._manuel_uyarildi = True
                    self._logla(f"⚠ {dugum.upper()} MANUEL MODA GEÇTİ — tam otonomi "
                                "ihlali: UÇUŞ GEÇERSİZ sayılır (§6.4)", "sari")
            else:
                self.mod.pop(dugum, None)
                (getattr(self, "mod_durum_zamani", {}) or {}).pop(dugum, None)
                if dugum == "iha":
                    self._ucus("PIXHAWK MODU YOK", KIRMIZI)
            if dugum == "iha" and "x" in temiz and "y" in temiz:
                self.iha_iz.append((temiz["x"], temiz["y"]))
                del self.iha_iz[:-150]         # son 150 nokta
                # geofence: İHA-UB dışına taşma = alan ihlali (§6.2/§6.4).
                # T162: kural ve kenar uzunluğu SÖZLEŞMEDEN gelir — `300` burada
                # ÇIPLAK yazılıydı (madde 16) ve üretimde `x,y` üreten yol
                # olmadığı için bu kapı SAHADA HİÇ ateş almıyordu.
                _ihlal = iha_ub_ihlali(temiz["x"], temiz["y"])
                if _ihlal is not None:
                    self._logla(f"⚠ ALAN İHLALİ: {_ihlal[1]} — uçuş başarısız "
                                "sayılır (§6.4)", "sari")
            self.sayac[MESAJ_HEARTBEAT] += 1
        self._rota_panelini_tazele()

    def _open_route_guven_reddini_goster(self, m, guven_reddi):
        """Eşik altı OPEN_ROUTE'u hakeme görünür kıl; rota ACK'i ASLA üretme."""
        sebep, detay = guven_reddi
        seq = m.get("seq")
        onceki_seq = (self.rota_yok.get("seq") if self.rota_yok else None)
        yeni = seq != onceki_seq
        self.rota_yok = {
            "type": MESAJ_NO_ROUTE, "sebep": sebep, "detay": detay, "seq": seq,
            "kaynak_type": MESAJ_OPEN_ROUTE,
        }
        self.rx_alim[seq] = self.rx_alim.get(seq, 0) + 1
        self.onaylandi = False
        self.tespit_onayli = False
        if yeni:
            self.sayac["OPEN_ROUTE_RED"] += 1
            # CONTRACTS §6.8: eşik altı tespit için ACK ÜRETİLMEZ; reddin
            # kendisi kanıttır — "hakem neden onaylamadı" 21 Eylül'de sorulur.
            self._kanit_yaz("ROTA_REDDEDILDI", seq=seq, sebep=sebep,
                            detay=detay)
            self._detay_base = f"seq={seq} · {sebep}"
            self._kutu_yaz("protokol", karar="ROTA YOK", renk=KIRMIZI,
                           detay=f"{self._detay_base} · {detay}")
            self._onay_dugmesini_ciz(
                False, "DÜŞÜK GÜVEN — OPEN_ROUTE REDDEDİLDİ")
            if not self._kanit_kilidi_var():
                self.lbl_onay.config(
                    text="Rota güven eşiğinin altında; ACK gönderilmedi, "
                         "İKA hareket etmez.", fg=KIRMIZI)
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
        self._onay_dugmesini_ciz(False, "ANKOR YOK — ONAY KAPALI")
        if self._kanit_kilidi_var():
            if logla:
                self._logla("HAKEM ONAYI REDDEDİLDİ: ANKOR YOK — rota şeride "
                            "yerleştirilemedi, ACK gönderilmedi", "sari")
            return
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
        if getattr(self, "tek_rota", False) and not self._tek_rota_gecerli():
            self._onay_dugmesini_ciz(False, "ROTA GEOMETRİSİ YOK — ONAY KAPALI")
            return
        # KANIT KİLİDİ — düğme durumu TEK savunma değildir (T180 sınıfı):
        # `--otomatik-onay`, klavye kısayolu ve zamanlayıcı bu yolu düğme
        # kapalıyken de çağırır. Kanıt kaydı yazamıyorsa §2.2.3 hakem onayı
        # VERİLMEZ ve ACK üretilmez: kaydı olmayan onay, 21 Eylül'de
        # dayanaksızdır. ARM/DISARM ve acil komutlar bundan etkilenmez.
        if self._kanit_kilidi_var():
            self._onay_dugmesini_ciz(False, KANIT_KILIDI_ONAY_METNI)
            self._logla("KİLİT ✋ KANIT KAYDI YAZILAMIYOR — hakem onayı "
                        "VERİLMEDİ, ACK gönderilmedi (§2.2.3): "
                        f"{self.kanit_kaydi_hatasi}", "kirmizi")
            return
        # A1 fail-closed: dugme durumu tek savunma degildir. Otomatik onay,
        # klavye veya dogrudan cagri eksik ankrajli rotayi onaylayamaz.
        if rota_ankor_uyarisi(self.rota):
            self._ankor_yok_onayini_kapat(logla=True)
            self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),
                            sebep="ANKOR_YOK")
            return
        # T169 · §6.2 FAIL-CLOSED: dugme TEK savunma degildir. Otomatik onay
        # (`--otomatik-onay`), klavye ya da bir zamanlayici bu yolu dugme
        # kapaliyken de cagirabilir; BAYAT tespit icin ACK URETILMEZ.
        if self._tespiti_yaslandir():
            self._logla("HAKEM ONAYI REDDEDILDI: tespit BAYAT (§6.2 gercek "
                        "zamanli aktarim) — ACK gonderilmedi", "sari")
            self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),
                            sebep="BAYAT_TESPIT")
            return
        if not self.tespit_onayli:
            self.tespit_onayli = True
            self._logla("HAKEM 1/2: güzergâh TESPİTİ doğrulandı (§2.2.3)", "sari")
            # CONTRACTS §6.8 — §2.2.3 iki aşamalı onayın 1. aşaması.
            self._kanit_yaz("HAKEM_ONAYI_1", seq=self.rota.get("seq"),
                            road=self.rota.get("road"),
                            conf=self.rota.get("conf"),
                            **self._rota_kanit_geometrisi(self.rota))
            self._aktarim_onay_dugmesini_kur()
            return
        # K8 fail-closed: İKA'nın bu rota için OPEN_ROUTE ACK kanıtı ekranda
        # görünmeden "İKA'ya aktarıldı" onayı VERİLMEZ (şartname §2.2.3).
        # ⚠ CONTRACTS §6.7 (D-407): FDA görev test uçuşunda (§5.3.2) İKA YOKTUR —
        # aktarım hedefi YKS'dir. Bu kanıt hiç gelmeyeceği için kilit orada
        # onayı SONSUZA DEK kapatırdı; şartname hakem onayını zorunlu kıldığından
        # uçuş geçersiz olurdu. FDA'da 2/2 = "YKS'de canlı görüldü + hakem onayı".
        if not self.fda_kipi and not self.ika_aktarim_kaniti_var():
            self._aktarim_onay_dugmesini_kur()
            self._logla("HAKEM 2/2 REDDEDİLDİ: İKA'dan OPEN_ROUTE ACK kanıtı yok "
                        f"(seq={self.rota['seq']}) — kanıtsız onay verilmez", "sari")
            self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=self.rota.get("seq"),
                            sebep="IKA_ACK_KANITI_YOK")
            return
        # T206 (D-405 Q4): hakem ACK'i `ref_tip` taşır (§6.6). `self.rota`
        # yalnız `_mesaj_isle`'nin OPEN_ROUTE dalında atanır, yani bu yol
        # tanım gereği OPEN_ROUTE onayıdır; alan eksikse (Tk'siz fikstürler)
        # tip yine OPEN_ROUTE'tur — ref_tip'siz (zayıf) ACK üretilmez.
        rota_ack = ack(self.rota["seq"], "yks",
                       self.rota.get("type") or MESAJ_OPEN_ROUTE)
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
        # CONTRACTS §6.7: FDA'da İKA kanıtı YOK — dayanak YKS'ye canlı aktarımdır.
        if self.fda_kipi:
            dayanak = "FDA §5.3.2: İKA yok — onay YKS aktarımına dayanır"
        else:
            dayanak = "İKA ACK kanıtı " + time.strftime(
                "%H:%M:%S", time.localtime(self.ika_rota_ack[self.rota["seq"]]))
        # CONTRACTS §6.8 — §2.2.3'ün ONAY satırı: ACK link'e YAZILDIKTAN sonra
        # yazılır; "onaylandı ama ACK gitmedi" diyen bir kanıt satırı olamaz.
        self._kanit_yaz("HAKEM_ONAYI_2", seq=self.rota.get("seq"),
                        ref_tip=rota_ack.get("ref_tip"),
                        fda_kipi=bool(self.fda_kipi), dayanak=dayanak,
                        iha_indi=bool(self.t_iha1 is not None
                                       or self.iha_landed_seq is not None),
                        **self._rota_kanit_geometrisi(self.rota))
        self._onay_dugmesini_ciz(False, "ONAYLANDI ✓✓", bg=YESIL)
        if not self._kanit_kilidi_var():
            self.lbl_onay.config(
                text=f"Hakem onayı tam — ACK(seq={self.rota['seq']}) "
                     f"İHA'ya iletildi · {dayanak}{havada}", fg=YESIL)
        self._logla(
            ("HAKEM 2/2: YKS'ye canlı aktarım doğrulandı (FDA §5.3.2) → ACK ref="
             if self.fda_kipi else
             "HAKEM 2/2: İKA'ya aktarım doğrulandı → ACK ref=")
            + str(self.rota["seq"]), "sari")
        self._zincir(("Kamera (İHA)", "YOLOv8-seg", "Rota Üretimi",
                      "RFD900A TX", "YKS (bu ekran)")
                     + (() if self.fda_kipi else ("İKA",)))

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
        # Kanıt kilidi `_onay_dugmesini_ciz` içinde; bu periyodik yol tam da
        # kilidi ESKİDEN geri açan yollardan biriydi.
        self._onay_dugmesini_ciz(True, "1) TESPİTİ DOĞRULA (§2.2.3)")
        if self._kanit_kilidi_var():
            return
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
            self._onay_dugmesini_ciz(
                True, "2) İKA'YA AKTARIMI ONAYLA → ACK")
            if self._kanit_kilidi_var():
                return
            self.lbl_onay.config(
                text=f"Tespit doğrulandı ✓ · İKA ALDI ✓ {kanit} "
                     f"(OPEN_ROUTE ACK seq={self.rota['seq']}) — aktarımı "
                     "onaylayabilirsiniz (§2.2.3 ikinci onay)", fg=SARI)
        else:
            self._onay_dugmesini_ciz(False, "2) İKA ACK KANITI BEKLENİYOR")
            if self._kanit_kilidi_var():
                return
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
        # CONTRACTS §6.8: ACK bağlama sözleşmesinin (§6.6) denetlenebilmesi
        # için ham olay `ref` VE `ref_tip` ile yazılır — bağlama SONUCU ayrı
        # olaylarda görünür (IKA_AKTARIM_KANITI, HAKEM_ONAYI_2). Bozuk `ref`
        # taşıyan çerçeve yukarıda düşer: kayıt da onu ACK saymaz.
        self._kanit_yaz("ACK_ALINDI", node=m.get("node"), ref=ref,
                        ref_tip=m.get("ref_tip"))
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
                # COMMAND_ACK ACCEPTED komutun kabul kanitidir; mekanik
                # paraşütün gerçekten açıldığına dair ayrı bir sensör değildir.
                dugme = getattr(self, "btn_parasut", None)
                if dugme is not None:
                    dugme.config(text="PARAŞÜT KOMUTU KABUL ✓ (PIXHAWK ACK)")
            acil_tekrar = getattr(self, "acil_tekrar", None)
            acil_komut = getattr(self, "acil_bekleyen_komut", None)
            acil_mesaji = getattr(acil_tekrar, "mesaj", None)
            if (acil_tekrar is not None and acil_komut and acil_mesaji
                    and kritik_komut_ack_gecerli_mi(
                        m, acil_mesaji.get("seq"), acil_komut, node="iha")
                    and acil_tekrar.ack_geldi(m)):
                self.acil_ack_zamani = time.monotonic()
                self._logla(
                    f"İHA ALDI ✓ {acil_komut} Pixhawk COMMAND_ACK ACCEPTED; "
                    f"{acil_komut} uçuş modu henüz DOĞRULANMADI — "
                    "HEARTBEAT bekleniyor", "yesil")
                etiket = getattr(self, "lbl_acil", None)
                if etiket is not None:
                    etiket.config(
                        text=f"ACİL UÇUŞ KOMUTU: {acil_komut} KABUL ✓ · "
                             f"{acil_komut} MODU BEKLENİYOR",
                        fg=SARI)
                self._acil_bekleyeni_tamamla()
                self._acil_ui_uygula()
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
            if self.t_ika0 is not None and self.t_ika1 is None:
                self.btn_hb.config(state="normal", bg=SARI)   # HB TEMAS artık anlamlı
        if ref_tip in (None, MESAJ_OPEN_ROUTE) and ref not in self.ika_rota_ack:
            if self.rota and ref == self.rota["seq"]:
                self._ika_rota_ack_bagla(ref, time.time(), self._iha_havada_mi())
            elif ref_tip == MESAJ_OPEN_ROUTE:
                # T224 (D-441): rota henüz yok ya da başka seq — kopya bir
                # daha gelmeyeceği için ATILMAZ, kısa süre saklanır.
                self._erken_ika_rota_ack_sakla(ref)

    def _ika_rota_ack_bagla(self, ref, damga, havada, erken=False):
        """K8 kanıtını ekrana ve kayda bağla — anlık ACK (`_ack_isle`) ile
        tampondan eşlenen erken ACK (`_erken_ika_rota_ack_esle`) AYNI yolu
        kullanır. `damga` (duvar saati) ve `havada` kopyanın GELDİĞİ anındır.

        P9c (D-393) — §2.2.3: "Bu aktarımın İHA havada iken tamamlanması
        gerekmektedir." Kanıt anında havada/yerde damgası basılır; kanıt anı
        ACK'ın geliş anıdır, tampondan eşlemenin anı DEĞİL (T224).
        """
        self.ika_rota_ack[ref] = damga
        damga_metni = time.strftime("%H:%M:%S", time.localtime(damga))
        # CONTRACTS §6.8 — K8 kanıtı: 2. onay aşamasının fail-closed
        # dayanağı budur; ekranda görünmesi yetmez, kayda da düşer.
        # `erken` alanı yalnız tampondan eşlenince yazılır (anlık satır aynı).
        alanlar = {"seq": ref, "iha_havada": havada}
        if erken:
            alanlar["erken"] = True
        self._kanit_yaz("IKA_AKTARIM_KANITI", **alanlar)
        self._logla(f"İKA ALDI ✓ OPEN_ROUTE ACK ref={ref} · {damga_metni} "
                    + ("(rotadan ÖNCE gelmişti, tampondan eşlendi · T224) "
                       if erken else "")
                    + "(aktarım kanıtı ekranda) · "
                    + ("İHA HAVADA ✓ (§2.2.3)" if havada else
                       "⚠ İHA HAVADA DEĞİL — §2.2.3 aktarım havadayken "
                       "bitmeliydi"),
                    "yesil" if havada else "sari")
        if self.tespit_onayli and not self.onaylandi:
            self._aktarim_onay_dugmesini_kur()
            if self.otomatik_onay:
                self.kok.after(500, self.onayla)

    def _erken_ika_rota_ack_sakla(self, ref):
        """Geçerli rotayla eşleşmeyen İKA OPEN_ROUTE ACK kopyasını kısa süre
        sakla (T224); o seq'li OPEN_ROUTE kabul edilince
        `_erken_ika_rota_ack_esle` bağlar.

        Kayıt = (geliş duvar saati, geliş monotonik, gelişte İHA havada mı):
        kanıtın damgası ve §2.2.3 havada bilgisi anlık yoldaki gibi ACK'ın
        GELDİĞİ anındır. İlk geliş korunur (kopya yinelenirse üzerine
        yazılmaz — kanıt zamanı İKA'nın rotayı İLK aldığı andır). Süresi
        dolmuş kayıtlar her gelişte temizlenir: tampon sınırlı kalır.
        """
        simdi = time.monotonic()
        tampon = getattr(self, "_erken_ika_rota_ack", None)
        if tampon is None:
            tampon = self._erken_ika_rota_ack = {}
        for bayat in [r for r, kayit in tampon.items()
                      if simdi - kayit[1] > IKA_ROTA_ACK_ERKEN_TAMPON_S]:
            del tampon[bayat]
        if ref in tampon:
            return
        tampon[ref] = (time.time(), simdi, self._iha_havada_mi())
        # Metin her durumda DOĞRU olmalı (UI_OLAYI olarak hakem kaydına düşer):
        # kopya rotadan önce de gelmiş olabilir, değiştirilen eski bir rotaya
        # ait geç kopya da olabilir — ikisinde de "geçerli rotayla eşleşmedi".
        self._logla(f"İKA OPEN_ROUTE ACK ref={ref} geçerli rotayla eşleşmedi "
                    "(rota yok ya da başka seq) — "
                    f"{IKA_ROTA_ACK_ERKEN_TAMPON_S:.0f} s saklanıyor; bu seq'li "
                    "OPEN_ROUTE gelirse eşlenecek (K8 erken tampon · T224)",
                    "sari")

    def _erken_ika_rota_ack_esle(self, seq):
        """Kabul edilen OPEN_ROUTE için tampondaki erken ACK'ı bağla (T224).

        Süresi (`IKA_ROTA_ACK_ERKEN_TAMPON_S`) dolmuş kopya kanıt SAYILMAZ ve
        atılır — fail-closed: hakem 2/2'yi ancak taze kanıtla açar.
        """
        tampon = getattr(self, "_erken_ika_rota_ack", None)
        if not tampon:
            return False
        kayit = tampon.pop(seq, None)
        if kayit is None or seq in self.ika_rota_ack:
            return False
        damga, gelis, havada = kayit
        if time.monotonic() - gelis > IKA_ROTA_ACK_ERKEN_TAMPON_S:
            self._logla(f"⚠ İKA OPEN_ROUTE ACK ref={seq} tamponda BAYATLADI "
                        f"(> {IKA_ROTA_ACK_ERKEN_TAMPON_S:.0f} s) — kanıt "
                        "sayılmadı; 2/2 için İKA'dan yeni ACK gerekir (T224)",
                        "sari")
            return False
        self._ika_rota_ack_bagla(seq, damga, havada, erken=True)
        return True

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
        # CONTRACTS §6.8 — tatbikatın KENDİSİ de kanıttır (DDR B.3.3.1):
        # ekranda kırmızı bant gören hakem, kaydında hangi senaryonun ne
        # zaman tetiklendiğini görmeden tatbikatı doğrulayamaz.
        self._kanit_yaz("ACIL_SENARYO", kod=kod, senaryo_no=no)

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
        """Rota noktalarını ref, yerel ve birleşik koordinatlarıyla göster."""
        if getattr(self, "tek_rota", False):
            try:
                plan = rota_plani(m)
                satirlar = ["TEK ROTA · ref + waypoint / metre · GPS değil"]
                for adim in plan["adimlar"]:
                    satirlar.append(f"P{adim['sira']:02d} · X={adim['nokta'][0]:+.2f} "
                                     f"Y={adim['nokta'][1]:+.2f} · {adim['hareket']}")
                satirlar.append(f"TOPLAM {plan['toplam']:.2f} m · gerçekleşmiş sürüş değil")
            except (ValueError, TypeError, OverflowError) as exc:
                satirlar = ["GEÇERLİ ROTA YOK: " + str(exc)]
            self.rota_metin.config(state="normal")
            self.rota_metin.delete("1.0", "end")
            self.rota_metin.insert("end", "\n".join(satirlar))
            self.rota_metin.config(state="disabled")
            return
        wps = m.get("waypoints") or []
        satirlar = []
        onceki = (0.0, 0.0)                 # referans noktasına göre yerel
        onceki_yon = None
        toplam = yanal = 0.0
        keskin = 0.0
        ref = m.get("ref_xy")
        if isinstance(ref, (list, tuple)) and len(ref) == 2:
            try:
                ref_x, ref_y = float(ref[0]), float(ref[1])
                if not math.isfinite(ref_x) or not math.isfinite(ref_y):
                    raise ValueError
                satirlar.append(
                    f"REF [{ref_x:+.2f}, {ref_y:+.2f}] m · rota koordinatı "
                    "GNSS değil, yerel çerçevedir")
            except (TypeError, ValueError):
                ref_x = ref_y = None
                satirlar.append("REF yok/geçersiz · birleşik koordinat gösterilmiyor")
        else:
            ref_x = ref_y = None
            satirlar.append("REF yok · birleşik koordinat gösterilmiyor")
        for i, (x, y) in enumerate(wps, 1):
            dx, dy = x - onceki[0], y - onceki[1]
            uz = math.hypot(dx, dy)
            toplam += uz
            yanal += abs(dx)
            yon = math.degrees(math.atan2(dx, dy))       # 0° = kuzey (ileri)
            kimden = "ref " if i == 1 else f"wp{i-1:<2}"
            satir = (f"{kimden}→wp{i:<2} Δx{dx:+5.1f} Δy{dy:+5.1f} · "
                     f"{uz:4.1f} m · yön {yon:+6.1f}°")
            if ref_x is not None:
                satir += (f" · yerel [{x:+.2f}, {y:+.2f}]"
                          f" · birleşik [{ref_x + x:+.2f}, {ref_y + y:+.2f}]")
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
        etiket = getattr(self, "lbl_ucus", None)
        if etiket is not None:
            etiket.config(text=f"İHA UÇUŞ DURUMU: {metin}", fg=renk)

    def _ucus_normal(self):
        self._ucus("OTONOM GÖREV (AUTO)", YESIL)

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
        if ad not in ("harita", "algi", "kamera", "rota"):
            raise ValueError(f"bilinmeyen görünüm: {ad!r}")
        self.gorunum_adi = ad
        # T81: kutu GÖRÜNÜMÜN kaynağından beslenir — geçişte yeniden çizilir.
        # Harita görünümüne dönüldüğünde protokol durumu OLDUĞU GİBİ görünür;
        # canlı algı görünümünde telsiz değeri EKRANA BASILMAZ.
        self._kutu_ciz()
        # T226-D (D-448): görünüm çerçevesi görünüm düğmelerinin HEMEN altına
        # paketlenir (ilk açılıştaki sıra). Çıplak `pack()` sona ekliyordu:
        # kamera → harita dönüşünde harita sol panelin SONUNA, senaryo/demo
        # düğmelerinin altına düşüyordu (T226 öncesinden; ölçüldü, D-448).
        anahtar = getattr(self, "_gorunum_anahtari", None)
        yer = {"after": anahtar} if anahtar is not None else {}
        if getattr(self, "rota_paneli", None) is not None:
            self.rota_paneli.pack_forget()
            self.btn_gor_rota.config(fg=BG if ad == "rota" else METIN,
                                     bg=YESIL if ad == "rota" else "#232e3a")
        if ad == "rota":
            self.harita.pack_forget()
            self.algi_cerceve.pack_forget()
            self.kamera_cerceve.pack_forget()
            self.rota_paneli.pack(fill="both", expand=True, **yer)
            for dugme in (self.btn_gor_harita, self.btn_gor_algi, self.btn_gor_kamera):
                dugme.config(fg=METIN, bg="#232e3a")
            self._rota_panelini_tazele()
            return
        if ad == "harita":
            self.algi_cerceve.pack_forget()
            self.kamera_cerceve.pack_forget()
            self.harita.pack(padx=10, pady=(4, 6), fill="both", expand=True,
                             **yer)
            self.btn_gor_harita.config(fg=BG, bg=YESIL)
            self.btn_gor_algi.config(fg=METIN, bg="#232e3a")
            self.btn_gor_kamera.config(fg=METIN, bg="#232e3a")
            self._harita_ciz()
        elif ad == "algi":
            self.harita.pack_forget()
            self.kamera_cerceve.pack_forget()
            self.algi_cerceve.pack(fill="both", expand=True, **yer)
            self.btn_gor_algi.config(fg=BG, bg=YESIL)
            self.btn_gor_harita.config(fg=METIN, bg="#232e3a")
            self.btn_gor_kamera.config(fg=METIN, bg="#232e3a")
            self._algi_iste()
        else:
            self.harita.pack_forget()
            self.algi_cerceve.pack_forget()
            # T226 (D-443 kusur a): kamera çerçevesi görünüm düğmelerinin HEMEN
            # altına; içindeki KÜÇÜK harita GİZLENMEZ (video + rota aynı anda).
            self.kamera_cerceve.pack(fill="both", expand=True, **yer)
            self.btn_gor_kamera.config(fg=BG, bg=YESIL)
            self.btn_gor_harita.config(fg=METIN, bg="#232e3a")
            self.btn_gor_algi.config(fg=METIN, bg="#232e3a")
            self._harita_ciz()          # küçük kopya güncel rotayla
            self._kamera_tazele()

    def _videosuz_panel_yaz(self, etiket, neden):
        """Video yokken kamera panelini boş bırakma: telemetri kipini söyle.

        NEDEN (ekran görüntüsüyle ölçüldü, 13 Eylül): video kopukken panel
        yalnız küçük tek satırlık bir yazı taşıyan BOŞ bir kutuydu; hakem
        ekranın telemetriyle çalışmaya devam ettiğini göremiyordu.
        "telemetri ile izleniyor" yalnız İHA telemetrisi TAZEYKEN yazılır —
        telemetri de kesikse panel bunu söyler (ekran kendi kendisiyle
        çelişmesin, T177 sınıfı). Tazelik ölçütü `lbl_gps` ile AYNI
        (`ARM_DURUM_TAZELIK_S`). Son kare gösterilmez; video karar üretmez.
        """
        hb = (getattr(self, "son_hb", None) or {}).get("iha")
        taze = hb is not None and time.monotonic() - hb < ARM_DURUM_TAZELIK_S
        baslik = ("VİDEO BAĞLANTISI YOK — telemetri ile izleniyor" if taze else
                  "VİDEO BAĞLANTISI YOK — İHA TELEMETRİSİ DE YOK/BAYAT")
        etiket.config(
            image="", fg=SARI if taze else KIRMIZI,
            text=(f"{baslik}\n\n{neden}\n\nRota, hakem onayı ve komutlar "
                  "telsiz verisine dayanır; video karar üretmez."),
            wraplength=max(S(160), self._kamera_resim_kutusu(etiket)[0] - S(16)))
        if getattr(self, "tek_rota", False) and getattr(self, "videosuz_rota", None) is not None:
            etiket.pack_forget()
            self.mini_harita_cerceve.pack_forget()
            if not self._videosuz_rota_acik:
                self.videosuz_rota.pack(fill="both", expand=True)
                self._videosuz_rota_acik = True
            self._rota_panelini_tazele()

    def _kamera_tazele(self):
        """LAN kamera snapshot'ını Tk ana döngüsünde sun; ağ I/O'su yapma."""
        istemci = getattr(self, "kamera_istemci", None)
        etiket = getattr(self, "lbl_kamera_img", None)
        bilgi = getattr(self, "lbl_kamera_bilgi", None)
        if etiket is None or bilgi is None:
            return
        if istemci is None:
            self._videosuz_panel_yaz(
                etiket, "KAMERA URL YOK — RAW görüntü kapalı")
            bilgi.config(text="--kamera-url http://<JETSON_IP>:8080 verin · "
                               "video SiK üzerinden taşınmaz", fg=KIRMIZI)
            # CONTRACTS §6.8: "kamera yoktu" da KANITTIR — kayıtta boşluk
            # bırakmak, sonradan "kamera vardı ama yazılmadı" savunmasına
            # kapı açar. Kenar olayı: bir kez yazılır, sonra tekrar aralığında.
            self._kamera_kanitini_yaz(
                "YAPILANDIRILMADI", kare_yasi_s=None, kare_sira=None,
                kaynak=None, hata="kamera URL verilmedi", calisiyor=False)
            return
        try:
            snap = istemci.snapshot()
        except Exception as exc:
            snap = {"surum": None, "jpeg": None, "durum": "HATA",
                    "hata": f"istemci snapshot hatası: {type(exc).__name__}: {exc}",
                    "kare_yasi_s": None, "kaynak": self.kamera_url}
        jpeg = snap.get("jpeg")
        surum = snap.get("surum")
        if jpeg is not None and getattr(self, "_videosuz_rota_acik", False):
            self.videosuz_rota.pack_forget()
            self._videosuz_rota_acik = False
            self.mini_harita_cerceve.pack(side="right", fill="y", padx=(0, 10), pady=(4, 4))
            etiket.pack(side="left", padx=10, pady=(4, 4), fill="both", expand=True)
            self._kamera_surum = -1
        if jpeg is not None and surum != self._kamera_surum:
            try:
                from PIL import Image, ImageOps, ImageTk
                resim = ImageOps.exif_transpose(Image.open(io.BytesIO(jpeg)))
                resim.thumbnail(self._kamera_resim_kutusu(etiket),
                                Image.Resampling.LANCZOS)
                self._kamera_foto = ImageTk.PhotoImage(resim.convert("RGB"))
                etiket.config(image=self._kamera_foto, text="", fg=METIN)
                self._kamera_surum = surum
            except Exception as exc:
                jpeg = None
                snap["hata"] = f"JPEG çözülemedi: {type(exc).__name__}: {exc}"
                snap["durum"] = "HATA"
        if jpeg is None:
            self._kamera_foto = None
            self._videosuz_panel_yaz(
                etiket, "KAMERA YOK — son kare kullanılmıyor")
        yas = snap.get("kare_yasi_s")
        yas_metin = "yaş YOK" if yas is None else f"kare yaşı {float(yas):.2f} sn"
        durum = str(snap.get("durum") or "BİLİNMİYOR")
        hata = snap.get("hata")
        metin = f"{durum} · {yas_metin} · {snap.get('kaynak') or self.kamera_url}"
        if hata:
            metin += f" · {hata}"
        bilgi.config(text=metin, fg=YESIL if jpeg is not None else KIRMIZI)
        # CONTRACTS §6.8: kanıt durumu SAĞLIK + KARE ikilisidir. İkisi bugün
        # `kamera_istemci`de birlikte hareket ediyor ama kayıt bu eşleşmeye
        # GÜVENMEZ: kare kaybolup sağlık "CANLI" kalırsa hakem kaydı bunu
        # yine de görmek zorundadır.
        self._kamera_kanitini_yaz(
            f"{durum}·{'KARE' if jpeg is not None else 'KARE_YOK'}",
            kare_sira=snap.get("kare_sira"),
            kare_yasi_s=(None if yas is None else round(float(yas), 3)),
            # T226: kaynak = URL [+ etiket] (CONTRACTS §6.8). `getattr`:
            # kurucuyu atlayan fikstürlerde etiket yoktur → yalnız URL.
            kaynak=kamera_kanit_kaynagi(
                snap.get("kaynak") or getattr(self, "kamera_url", None),
                getattr(self, "kamera_etiket", "")),
            hata=(str(hata) if hata else None),
            calisiyor=bool(snap.get("calisiyor")))

    def _rota_kanit_geometrisi(self, mesaj):
        if not getattr(self, "tek_rota", False):
            return {}
        try:
            plan = rota_plani(mesaj)
        except (ValueError, TypeError, OverflowError):
            return {"gosterim": "tek_rota", "geometri": "gecersiz"}
        return {"gosterim": "tek_rota", "rota_sha256": plan["sha256"],
                "ref_xy": mesaj["ref_xy"], "waypoints": mesaj["waypoints"],
                "cerceve": "ref_xy + waypoint; GPS degil"}

    def _tek_rota_gecerli(self):
        try:
            rota_plani(getattr(self, "rota", None))
            return True
        except (ValueError, TypeError, OverflowError):
            return False

    def _rota_guncelligi(self):
        simdi = time.monotonic()
        karar = getattr(self, "karar_yas_rx", None)
        damgalar = [damga for damga in (getattr(self, "rota_zaman", None),
                     getattr(self, "son_hb", {}).get("iha")) if damga is not None]
        if not damgalar or karar is None:
            return False
        karar_yasi = karar[0] + simdi - karar[1]
        hat_yasi = simdi - max(damgalar)
        return (math.isfinite(karar_yasi) and 0 <= karar_yasi <= YKS_TESPIT_TAZELIK_S
                and 0 <= hat_yasi <= YKS_TESPIT_TAZELIK_S)

    def _tek_rota_harita_verisi(self):
        if getattr(self, "rota_yok", None):
            return None, "ROTA YOK — " + str(self.rota_yok.get("sebep", "Ret alındı")), KIRMIZI
        try:
            plan = rota_plani(getattr(self, "rota", None))
        except (ValueError, TypeError, OverflowError):
            return None, "GEÇERLİ ROTA VERİSİ BEKLENİYOR", SOLUK
        if not self._rota_guncelligi():
            return plan, "ESKİ PLAN / GÜNCELLİK YOK — GPS DEĞİL", SARI
        return plan, "ALINAN ROTA / METRE — GPS VE YOL SINIRI DEĞİL", MAVI

    def _rota_panelini_tazele(self):
        paneller = [panel for panel in (getattr(self, "rota_paneli", None),
                    getattr(self, "videosuz_rota", None)) if panel is not None]
        if not paneller:
            return
        simdi = time.monotonic()
        rota = getattr(self, "rota", None)
        damga = getattr(self, "rota_zaman", None)
        yas = "paket yok" if damga is None else f"paket alımı {max(0, simdi - damga):.1f} s önce"
        onay = ("Onay: 2/2 (verildiği anın kaydı)" if self.onaylandi else
                "Onay: 1/2" if self.tespit_onayli else "Onay bekleniyor")
        aktarim = ("FDA: İKA sürüşü yok" if self.fda_kipi else
                   "İKA ACK: var" if rota and rota["seq"] in self.ika_rota_ack else "İKA ACK: yok")
        video = "Video: bağlı değil" if self.kamera_istemci is None or self._kamera_foto is None else "Video: kare var"
        kaynak = ("DEMO / SENTETİK PAKET" if self.demo else "İHA'DAN ALINAN ROTA") + " · " + yas
        for panel in paneller:
            if panel.winfo_manager():
                panel.guncelle(rota, ret=self.rota_yok, bayat=not self._rota_guncelligi(),
                               kaynak=kaynak, onay=onay + " · " + aktarim, video=video)

    def _kamera_resim_kutusu(self, etiket):
        """Video karesinin sığacağı kutu (T226): etiketin GERÇEK alanı (küçük
        harita yanında); yerleşim henüz yoksa eski sabit kutu."""
        try:
            w, h = int(etiket.winfo_width()), int(etiket.winfo_height())
        except Exception:
            w = h = 0
        if w < S(160) or h < S(90):
            return S(660), S(430)
        return w - S(8), h - S(8)

    def _kamera_kanitini_yaz(self, durum, **alanlar):
        """Kamera kanıt durumunu hakem kaydına KENAR olayı olarak yaz (§6.8)."""
        return self._kanit_durumu_yaz(
            "KAMERA_KANIT", durum,
            "_kamera_kanit_durumu", "_son_kamera_kanit_monotonic", **alanlar)

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
                self.algi_model, model_yolu, model_profili = (
                    _dogrulanmis_algi_modeli_yukle(
                        calisan_imgsz=INFER_SIZE,
                        beklenen_dosya=self.ALGI_MODEL_DOSYA))
                self.algi_kuyruk.put(("log",
                    f"{model_yolu.stem} modeli KAYITLI SOYLA doğrulandı: "
                    f"{model_yolu.name} (SHA {model_profili['sha256'][:8]} · "
                    f"imgsz {model_profili['imgsz']})"))

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
        self._onay_dugmesini_ciz(True, "1) TESPİTİ DOĞRULA (§2.2.3)")
        if not self._kanit_kilidi_var():
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
            if saha_tasiyicisi_mi(self.link):
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
        komut_mesaji = self._komut_mesaji(cmd, hedef_dugum)
        if not self._ham_gonder(komut_mesaji):
            return False
        self._logla(f"CMD → {hedef_dugum}: {cmd}", "mavi")
        return komut_mesaji["seq"]

    def _komut_mesaji(self, cmd, hedef_dugum):
        """İHA eyleyici komutunu bu YKS sürecinin tekrar oturumuna bağla."""
        if hedef_dugum != "iha":
            return command(cmd, hedef_dugum)
        oturum = getattr(self, "komut_oturumu", None)
        if not isinstance(oturum, str):
            # ``__new__`` kullanan test/entegrasyon fikstürleri dahil hiçbir
            # İHA eyleyici komutu saha protokolüne oturumsuz çıkmaz.
            oturum = uuid.uuid4().hex
            self.komut_oturumu = oturum
        return command(cmd, hedef_dugum, oturum=oturum)

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

    def _kritik_teyit_bekliyor(self, anahtar, simdi=None):
        """Teyit penceresi saat geri sıçramasına da fail-closed dayanır."""
        simdi = time.monotonic() if simdi is None else float(simdi)
        kayitlar = getattr(self, "_kritik_teyit", {})
        onceki = kayitlar.get(anahtar)
        if onceki is None:
            return False
        yas = simdi - onceki
        return 0.0 <= yas <= DISARM_TEYIT_SURESI_S

    def _kritik_teyit_al(self, anahtar, aciklama):
        """İki ayrı tık ister; ilk tık hiçbir ağ/eyleyici çıktısı üretmez.

        Buradan EKRANA YAZILMAZ. Teyit niyeti yalnız `_kritik_teyit`
        sözlüğünde tutulur; düğme metnini çağıranın gerçek-çizim yordamı
        (`_arm_ui_uygula` / `_acil_ui_uygula`) o sözlükten TÜRETİR.
        NEDEN (T180 sınıfı): düğmenin iki yazarı olduğunda ikinci tık
        anahtarı `pop` edip komut başarısız olunca (UDP adresi yok, ACK yok,
        gönderim hatası) ekranda BEKLEYEN TEYİT YOKKEN "TEKRAR BAS" asılı
        kalıyordu. Bu dosyanın sözleşmesi: "iletim yokluğu operatör onayı
        değildir" — bekleyen onay yokken "TEKRAR BAS" göstermek tam olarak o
        sınıf yanıltmadır ve hakem ekranındadır. Tek yazar = asılı metin YOK.
        """
        simdi = time.monotonic()
        if self._kritik_teyit_bekliyor(anahtar, simdi):
            self._kritik_teyit.pop(anahtar, None)
            return True
        kayitlar = getattr(self, "_kritik_teyit", None)
        if not isinstance(kayitlar, dict):
            kayitlar = {}
            self._kritik_teyit = kayitlar
        kayitlar.clear()                  # ayni anda yalnız tek kritik niyet
        kayitlar[anahtar] = simdi
        self._logla(
            f"⚠ {aciklama} GÖNDERİLMEDİ. Onaylamak için "
            f"{DISARM_TEYIT_SURESI_S:.0f} sn içinde aynı düğmeye TEKRAR bas.",
            "sari")
        return False

    def _arm_ui_uygula(self):
        """ARM gerçeğini tek yerden çiz; bilinmeyen/bekleyen fail-closed."""
        btn = getattr(self, "btn_arm", None)
        etiket = getattr(self, "lbl_arm", None)
        firlat = getattr(self, "btn_firlat", None)
        if btn is None or etiket is None or firlat is None:
            return
        # ⚠ ARM düğmesi kanıt kilidinden ETKİLENMEZ (niyet korunur): kanıt
        # kaydı bozukken de aracı ARM/DISARM edebilmek emniyettir. Kilit
        # yalnız FIRLATMA'ya iner ve onu `_firlat_dugmesini_ciz` uygular.
        bekleyen = getattr(self, "arm_bekleyen_komut", None)
        if bekleyen:
            btn.config(state="disabled", bg=SARI,
                       text=f"{bekleyen} — ACK + ARAÇ DURUMU BEKLENİYOR")
            etiket.config(
                text=f"SİSTEM: {bekleyen} İSTEĞİ GÖNDERİLDİ — doğrulanmadı",
                fg=SARI)
            self._firlat_dugmesini_ciz(False)
            return
        if not self._arm_durumu_taze_mi():
            btn.config(state="disabled", bg="#232e3a",
                       text="ARM DURUMU BEKLENİYOR")
            etiket.config(text="SİSTEM: ARM DURUMU BİLİNMİYOR/BAYAT", fg=KIRMIZI)
            self._firlat_dugmesini_ciz(False)
            return
        if self.arm_acik:
            btn.config(state="normal", text="DISARM (A)", bg=KIRMIZI)
            etiket.config(text="SİSTEM: ARM ✓ — PIXHAWK HEARTBEAT", fg=SARI)
            self._firlat_dugmesini_ciz(True)
        else:
            btn.config(state="normal", text="ARM (A)", bg="#232e3a")
            etiket.config(text="SİSTEM: DISARM ✓ — PIXHAWK HEARTBEAT", fg=SOLUK)
            self._firlat_dugmesini_ciz(False)
        komut = "DISARM" if self.arm_acik else "ARM"
        if self._kritik_teyit_bekliyor(komut):
            btn.config(text=f"{komut}? TEKRAR BAS", bg=SARI)

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
        self._acil_ui_uygula()
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
        durum = ("İHA HAVADA — DISARM" if komut == "DISARM" and self._iha_havada_mi()
                 else komut)
        if not self._kritik_teyit_al(komut, durum):
            # Teyit BEKLİYOR: metni `_arm_ui_uygula` sözlükten türetir.
            self._arm_ui_uygula()
            return
        komut_mesaji = self._komut_mesaji(komut, "iha")
        if not self.arm_tekrar.baslat(komut_mesaji):
            # Teyit anahtarı yukarıda TÜKETİLDİ ama komut çıkmadı → BEKLEYEN
            # TEYİT YOK. Ekranı gerçeğe döndür: "ARM? TEKRAR BAS" asılı
            # kalırsa hakem bekleyen bir onay olduğunu sanır (iletim yokluğu
            # operatör onayı değildir). Kırmızı "CMD GÖNDERİLEMEDİ" kaydını
            # `_ham_gonder` zaten yazdı — hata görünürdür. Sonraki tık, anahtar
            # tüketildiği için YENİ bir teyit turu başlatır; doğrudan ARM ETMEZ.
            self._arm_ui_uygula()
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

    def _acil_ui_uygula(self):
        """RTL/LAND düğmelerini ACK + hedef-mod durumundan tek yerde çiz."""
        bekleyen = getattr(self, "acil_bekleyen_komut", None)
        asama = ("MOD BEKLENİYOR" if bekleyen
                 and getattr(self, "acil_ack_zamani", None) is not None
                 else "ACK BEKLENİYOR")
        for komut, ad in (("RTL", "btn_rtl"), ("LAND", "btn_land")):
            dugme = getattr(self, ad, None)
            if dugme is None:
                continue
            if bekleyen:
                dugme.config(state="disabled", bg=SARI,
                             text=f"{bekleyen} {asama}")
            elif self._kritik_teyit_bekliyor(komut):
                dugme.config(state="normal", bg=SARI,
                             text=f"{komut}? TEKRAR BAS")
            else:
                dugme.config(state="normal", bg=KIRMIZI,
                             text=f"ACİL {komut}")

    def _acil_bekleyeni_tamamla(self, simdi=None):
        """Acil komutu ancak ACK'ten SONRA gelen eşleşen modla tamamla."""
        komut = getattr(self, "acil_bekleyen_komut", None)
        ack_zamani = getattr(self, "acil_ack_zamani", None)
        if komut not in ACIL_UCUS_MODLARI or ack_zamani is None:
            return False
        simdi = time.monotonic() if simdi is None else float(simdi)
        mod_zamani = (getattr(self, "mod_durum_zamani", {}) or {}).get("iha")
        iha_hb = (getattr(self, "son_hb", {}) or {}).get("iha")
        if (mod_zamani is None or iha_hb is None
                or mod_zamani < ack_zamani
                or not 0.0 <= simdi - iha_hb <= ARM_DURUM_TAZELIK_S
                or (getattr(self, "mod", {}) or {}).get("iha") != komut):
            return False
        deneme = getattr(getattr(self, "acil_tekrar", None), "deneme", 0)
        self.acil_bekleyen_komut = None
        self.acil_ack_zamani = None
        etiket = getattr(self, "lbl_acil", None)
        if etiket is not None:
            etiket.config(
                text=f"ACİL UÇUŞ KOMUTU: {komut} MOD DOĞRULANDI ✓ · "
                     "ARAÇ DURUMUNU İZLE",
                fg=KIRMIZI)
        self._logla(
            f"İHA {komut} MOD DOĞRULANDI ✓ Pixhawk COMMAND_ACK + "
            f"ACK sonrası taze HEARTBEAT ({deneme} gönderim)", "yesil")
        self._acil_ui_uygula()
        return True

    def acil_komut(self, komut):
        """İki tık + aynı-seq tekrar + güçlü Pixhawk ACK ile RTL/LAND iste."""
        if komut not in ("RTL", "LAND"):
            raise ValueError(f"bilinmeyen acil komut: {komut!r}")
        if getattr(self, "acil_bekleyen_komut", None):
            self._logla("Acil uçuş komutu zaten ACK bekliyor — ikinci komut "
                        "gönderilmedi", "sari")
            return
        if not self._kritik_teyit_al(
                komut,
                f"ACİL {komut} (ACK yalnız kabulü kanıtlar; RC pilotu hazır olmalı)"):
            # Metni `_acil_ui_uygula` `_kritik_teyit`ten türetir (tek yazar).
            self._acil_ui_uygula()
            return
        mesaj = self._komut_mesaji(komut, "iha")
        tekrar = getattr(self, "acil_tekrar", None)
        if tekrar is None or not tekrar.baslat(mesaj):
            # arm_degistir ile AYNI kural: teyit tüketildi, komut çıkmadı →
            # düğme "ACİL {komut}"a döner, bekleyen teyit gösterilmez.
            self._acil_ui_uygula()
            return
        self.acil_bekleyen_komut = komut
        self.acil_ack_zamani = None
        etiket = getattr(self, "lbl_acil", None)
        if etiket is not None:
            etiket.config(text=f"ACİL UÇUŞ KOMUTU: {komut} GÖNDERİLDİ · "
                                "PIXHAWK ACK BEKLENİYOR", fg=KIRMIZI)
        self._logla(f"CMD → iha: {komut} (seq={mesaj['seq']}, ACK bekleniyor · "
                    f"{ARM_TEKRAR_ARALIGI_S:.2f} s × "
                    f"≤{ARM_TEKRAR_UST_SINIRI})", "kirmizi")
        self._acil_ui_uygula()
        self._acil_tik()

    def _acil_tik(self):
        tekrar = getattr(self, "acil_tekrar", None)
        if tekrar is None or not getattr(self, "acil_bekleyen_komut", None):
            return
        durum = tekrar.tik()
        if durum == VAZGECILDI:
            komut = self.acil_bekleyen_komut
            self.acil_bekleyen_komut = None
            self._logla(f"İHA ONAY VERMEDİ ✗ {komut} {tekrar.deneme} kez "
                        "gönderildi; Pixhawk COMMAND_ACK gelmedi — RC pilotu "
                        "fiziksel yedeği kullansın", "kirmizi")
            etiket = getattr(self, "lbl_acil", None)
            if etiket is not None:
                etiket.config(text=f"ACİL UÇUŞ KOMUTU: {komut} ACK YOK · RC YEDEK",
                              fg=KIRMIZI)
            self._acil_ui_uygula()
            return
        if durum == ONAYLANDI:
            if self._acil_bekleyeni_tamamla():
                return
            ack_zamani = getattr(self, "acil_ack_zamani", None)
            if (ack_zamani is not None
                    and time.monotonic() - ack_zamani
                    > ARM_DURUM_TAZELIK_S):
                komut = self.acil_bekleyen_komut
                self.acil_bekleyen_komut = None
                self.acil_ack_zamani = None
                self._logla(
                    f"İHA {komut} ACK verdi ama ACK sonrası eşleşen taze "
                    f"{komut} mod HEARTBEAT'i gelmedi — TAMAMLANMADI; "
                    "RC pilotu fiziksel yedeği kullansın", "kirmizi")
                etiket = getattr(self, "lbl_acil", None)
                if etiket is not None:
                    etiket.config(
                        text=f"ACİL UÇUŞ KOMUTU: {komut} ACK VAR · MOD YOK · "
                             "RC YEDEK",
                        fg=KIRMIZI)
                self._acil_ui_uygula()
                return
        kok = getattr(self, "kok", None)
        if kok is not None:
            kok.after(int(ARM_TEKRAR_ARALIGI_S * 1000), self._acil_tik)

    def firlatma(self):
        if self.t_iha0 is not None:
            return
        # KANIT KİLİDİ — düğme durumu TEK savunma değildir (T180 sınıfı):
        # klavye, otomasyon ya da doğrudan çağrı bu yolu düğme kapalıyken de
        # tetikleyebilir. Kanıt kaydı yazamıyorsa uçuş kronometresi
        # BAŞLATILMAZ: kayıtsız uçuşun 21 Eylül'de dayanağı olmaz.
        if self._kanit_kilidi_var():
            self._firlat_dugmesini_ciz(False)
            self._logla("KİLİT ✋ KANIT KAYDI YAZILAMIYOR — FIRLATMA damgası "
                        "atılmadı (ARM/DISARM ve acil komutlar açık): "
                        f"{self.kanit_kaydi_hatasi}", "kirmizi")
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
        # Görev süresi duvar saatinden ölçülmez. NTP/operatör saat düzeltmesi
        # puanlanan süreyi geri veya ileri sıçratamaz; insan-okur tarih damgası
        # HakemKaydi tarafından ayrıca gerçek saatle yazılır.
        self.t_iha0 = time.monotonic()
        # CONTRACTS §6.8 — süre bütçesi §6.2/§5.3.2'nin PUANLANAN eksenidir;
        # başlangıç/bitiş damgaları ekrandan değil kayıttan doğrulanır.
        self._kanit_yaz("KRONOMETRE_BASLADI", kron="iha",
                        limit_s=self.IHA_LIMIT, devam=False)
        self._logla("GÖREV · FIRLATMA — İHA kronometresi başladı (limit 15:00)", "mavi")
        self._firlat_dugmesini_ciz(False)
        self.btn_iha_indi.config(state="normal", bg=SARI)

    def iha_indi(self):
        if self.t_iha0 is None or self.t_iha1 is not None:
            return
        self.t_iha1 = time.monotonic()
        sure = self.t_iha1 - self.t_iha0
        asim = sure > self.IHA_LIMIT
        self._kanit_yaz("KRONOMETRE_BITTI", kron="iha", sure_s=round(sure, 3),
                        limit_s=self.IHA_LIMIT, asim=bool(asim))
        self._logla(f"GÖREV · İHA İNDİ — uçuş süresi {sure/60:.1f} dk"
                    + (" → SÜRE AŞIMI: UÇUŞ GEÇERSİZ (şartname §6.4)" if asim else ""),
                    "sari" if asim else "yesil")
        if not self.onaylandi:
            self._logla("  ⚠ İHA indi ama aktarım havadayken hakem onayı YOKTU — "
                        "§6.4 geçersizlik riski!", "sari")
        self.btn_iha_indi.config(state="disabled", bg="#232e3a")
        self._ucus("İNİŞ TAMAM — PARAŞÜT (İHA-İB)", MAVI)

    def ika_baslat(self):
        # CONTRACTS §6.7: FDA görev test uçuşunda İKA YOKTUR (§5.3.2 yalnız
        # İHA + YKS). Düğme kapalıdır; eylem burada da reddedilir.
        if self.fda_kipi:
            self._logla("KİLİT ✋ FDA kipinde İKA yok (§5.3.2) — IKA_GO "
                        "GÖNDERİLMEDİ", "sari")
            return
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
        if self.t_ika0 is not None:
            return
        # K4: IKA_GO ACK gelene dek AYNI seq ile tekrar gönderilir (D-02).
        komut_mesaji = command("IKA_GO", "ika")
        if not self.ika_go_tekrar.baslat(komut_mesaji):
            return
        self._logla(f"CMD → ika: IKA_GO (seq={komut_mesaji['seq']}, ACK bekleniyor · "
                    f"{IKA_GO_TEKRAR_ARALIGI_S:.2f} s × ≤{IKA_GO_TEKRAR_UST_SINIRI})",
                    "mavi")
        self.t_ika0 = time.monotonic()
        self.t_ika1 = None
        self._kanit_yaz("KRONOMETRE_BASLADI", kron="ika",
                        limit_s=self.IKA_LIMIT, devam=False)
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
        if self.t_ika0 is None or self.t_ika1 is not None:
            return
        self.t_ika1 = time.monotonic()
        s = self.t_ika1 - self.t_ika0
        ok = s <= self.IKA_LIMIT
        self._kanit_yaz("KRONOMETRE_BITTI", kron="ika", sure_s=round(s, 3),
                        limit_s=self.IKA_LIMIT, asim=not ok)
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
        if self.t_haz0 is not None:
            return
        self.t_haz0 = time.monotonic()
        self._kanit_yaz("KRONOMETRE_BASLADI", kron="hazirlik",
                        limit_s=self.HAZIRLIK_LIMIT, devam=False)
        self._logla("HAZIRLIK · Alan girişi — 15:00 hazırlık süresi başladı (§6.2)",
                    "mavi")
        self.btn_alan.config(state="disabled", bg="#232e3a")
        self.btn_hazir.config(state="normal", bg=SARI)

    def takim_hazir(self):
        if self.t_haz0 is None or self.t_haz1 is not None:
            return
        self.t_haz1 = time.monotonic()
        s = self.t_haz1 - self.t_haz0
        puan = max(0, int((900 - s) / 30))
        self._kanit_yaz("KRONOMETRE_BITTI", kron="hazirlik", sure_s=round(s, 3),
                        limit_s=self.HAZIRLIK_LIMIT,
                        asim=bool(s > self.HAZIRLIK_LIMIT))
        self._logla(f"HAZIRLIK · 'TAKIM HAZIR' — süre {s/60:.1f} dk (hands-off); "
                    f"tasarruf puanı ≈ +{puan} (§7 t_hazırlık)", "yesil")
        self.btn_hazir.config(state="disabled", bg="#232e3a")
        self.btn_mudahale.config(state="normal", bg=SARI)

    def mudahale(self):
        # §6.2: hands-off sonrası müdahale = −100 ceza + süre hazırlığa eklenir
        if self.t_haz1 is None:
            return
        self.t_haz0 += time.monotonic() - self.t_haz1  # kaldığı yerden sürer
        self.t_haz1 = None
        # CONTRACTS §6.8: müdahale kronometreyi YENİDEN başlatmaz, KALDIĞI
        # yerden sürdürür — `devam=True` bu ayrımı kayıtta korur.
        self._kanit_yaz("KRONOMETRE_BASLADI", kron="hazirlik",
                        limit_s=self.HAZIRLIK_LIMIT, devam=True)
        self._ceza_ekle(100, "hands-off sonrası sisteme müdahale (§6.2)")
        self._logla("HAZIRLIK · kronometre DEVAM EDİYOR — müdahale süresi "
                    "hazırlığa ekleniyor; bitince tekrar TAKIM HAZIR verin", "sari")
        self.btn_hazir.config(state="normal", bg=SARI)
        self.btn_mudahale.config(state="disabled", bg="#232e3a")

    def fda_kipini_uygula(self):
        """CONTRACTS §6.7: `--fda` açılışta çağrılır; kip koşarken DEĞİŞMEZ.

        Yalnız ETİKET ve düğme durumudur — asıl kilitler `parasut()`,
        `ika_baslat()` ve `onayla()` içindedir (düğme durumu tek başına
        emniyet sinyali değildir, T180 sınıfı). Tk'siz fikstürlerde düğme
        yoktur; hepsi `getattr` ile korumalıdır.
        """
        self.fda_kipi = True
        self.IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S
        for ad, metin, kapat in (
                ("btn_firlat", "KALKIŞ ZAMANI / KRONOMETRE", False),
                ("btn_parasut", "PARAŞÜT (FDA dışı)", True),
                ("btn_ika_go", "İKA (FDA dışı)", True)):
            dugme = getattr(self, ad, None)
            if dugme is None:
                continue
            try:
                dugme.config(text=metin)
                if kapat:
                    dugme.config(state="disabled", bg="#232e3a", fg=SOLUK)
            except Exception:                    # Tk yok / fikstür
                pass

    def parasut(self):
        # CONTRACTS §6.7 (D-407): FDA görev test uçuşu ÇOKLU ROTORLA yapılır —
        # araçta paraşüt yoktur, §2.2.4'ün manuel yedeği (−50) o göreve aittir.
        # Düğme durumu tek savunma değildir (T180 sınıfı): eylem burada da
        # reddedilir, link'e HİÇBİR ŞEY yazılmaz.
        if self.fda_kipi:
            self._logla("KİLİT ✋ FDA kipinde paraşüt yok (çoklu rotor) — "
                        "komut GÖNDERİLMEDİ (§5.3.2)", "kirmizi")
            return
        # İki adımlı emniyet: yanlışlıkla tek tık paraşüt açamaz
        simdi = time.monotonic()
        if simdi - self.parasut_teyit > 3.0:
            self.parasut_teyit = simdi
            self.btn_parasut.config(bg=KIRMIZI, text="EMİN MİSİN? tekrar bas (3 sn)")
            # Geri alma KOŞULLU olmalı: eski koşulsuz lambda, teyit penceresi
            # içinde gönderilen PARACHUTE komutunun "GÖNDERİLDİ — İHA ACK
            # bekleniyor" metnini de, ACK gelmeyince yazılan kırmızı "ACK YOK
            # — TEKRAR" hatasını da 3,2 sn sonra eziyordu; hakem, uçuşta komut
            # varken düğmeyi boşta görüyordu. Aynı sınıf kusur (ekran gerçeği).
            self.kok.after(3200, lambda d=simdi: self._parasut_teyit_sondur(d))
            return
        # P9a (D-393): tek atış `_cmd_gonder` yerine ACK'lı tekrar — paraşüt
        # komutu kaybolursa bunu SESSİZCE kaybetmek kabul edilemez (§6.4).
        komut_mesaji = self._komut_mesaji("PARACHUTE", "iha")
        if not self.parasut_tekrar.baslat(komut_mesaji):
            # `_ham_gonder` GONDERILEMEDI'yi zaten kirmizi loglar (komut
            # durustlugu sozlesmesi: iletilmeyen komut basari/ceza uretmez).
            return
        self._ceza_ekle(PARASUT_MANUEL_CEZA_PUANI,
                        "manuel paraşüt tetikleme (§2.2.4)")
        self._ucus(f"PARAŞÜT İSTEĞİ GÖNDERİLDİ — ACK BEKLENİYOR "
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

    def _parasut_teyit_sondur(self, damga):
        """Süresi dolan paraşüt teyidini ekrandan sil — komut yolu devraldıysa
        DOKUNMA.

        Zamanlayıcı, `damga` anındaki tıkın açtığı teyit penceresi kapandıktan
        sonra ateşler. Yazma hakkı yalnız o pencerenindir:
          * `parasut_teyit != damga` → yeni bir teyit turu başlamış, metin onun;
          * `parasut_tekrar.durum != BOS` → PARACHUTE gönderilmiş; gönderim /
            ACK / "ACK YOK — TEKRAR" metni komut yolunundur, ezilmez.
        Teyit sahibi ise pencere gerçekten kapanmıştır: damga da SIFIRLANIR ki
        durum ile ekran ayrışmasın (bekleyen teyit yokken "tekrar bas" YOK).
        """
        dugme = getattr(self, "btn_parasut", None)
        if dugme is None or self.parasut_teyit != damga:
            return
        tekrar = getattr(self, "parasut_tekrar", None)
        if tekrar is not None and getattr(tekrar, "durum", BOS) != BOS:
            return
        self.parasut_teyit = 0.0
        dugme.config(bg="#232e3a", text="PARAŞÜT (manuel −50)")

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
        if t0 is None:
            return "--:--", SOLUK
        kalan = limit - (((time.monotonic() if t1 is None else t1) - t0))
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
            self._onay_dugmesini_ciz(False, "BAYAT TESPİT — ONAY KAPALI")
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
        self._rota_panelini_tazele()
        _mono = time.monotonic()               # D-384: damgalar monotonik
        tel_durum = {}                         # CONTRACTS §6.8 kanıt özeti
        tel_yas = {}
        for ad, (nokta, metin) in self.lbl_dugum.items():
            t = self.son_hb.get(ad)
            if t is None:
                nokta.config(fg=KIRMIZI)
                metin.config(text=f"{ad.upper()}  — sinyal yok")
                tel_durum[ad] = "YOK"
                tel_yas[ad] = None
            else:
                yas = _mono - t
                canli = 0.0 <= yas < 3.0               # ika_receiver failsafe eşiği
                tel_durum[ad] = "TAZE" if canli else "BAYAT"
                tel_yas[ad] = round(yas, 1)
                tel = self.tel.get(ad) or {}
                pixhawk_ok = (ad != "iha"
                              or tel.get("pixhawk_canli") is True)
                # Jetson/Navitas heartbeat'i ile Pixhawk canlılığı AYRI
                # sinyallerdir. Jetson canlı ama otopilot kopukken yeşil nokta
                # göstermek operatöre aracın kontrol edilebilir olduğu yalanını
                # söyler; sarı = taşıyıcı canlı, Pixhawk kanıtı yok.
                nokta.config(
                    fg=(YESIL if canli and pixhawk_ok
                        else SARI if canli else KIRMIZI))
                parcalar = []
                if "alt" in tel:
                    parcalar.append(f"{tel['alt']:.0f} m")
                if "hiz" in tel:
                    parcalar.append(f"{tel['hiz']:.1f} m/s")
                if "yon" in tel:
                    parcalar.append(f"{tel['yon']:.0f}°")
                if "bat" in tel:
                    parcalar.append(f"{tel['bat']:.1f} V")
                if "bat_yuzde" in tel:
                    parcalar.append(f"%{tel['bat_yuzde']} pil")
                if "uydu" in tel:
                    parcalar.append(f"{tel['uydu']} uydu")
                if ad == "iha":
                    parcalar.append(
                        "Pixhawk ✓" if tel.get("pixhawk_canli") is True
                        else "PIXHAWK YOK/BAYAT")
                ek = (" · " + " · ".join(parcalar)) if parcalar else ""
                mod = self.mod.get(ad)
                if mod:
                    if mod in ACIL_UCUS_MODLARI:
                        mod_notu = " ⚠ACİL EMNİYET"
                    elif mod == "AUTO":
                        mod_notu = ""
                    else:
                        mod_notu = " ⚠AUTO DIŞI"
                    ek += f" · mod {mod}{mod_notu}"
                metin.config(text=f"{ad.upper()} — hb {yas:.1f} sn{ek}"
                                  + ("" if canli else "  (BAĞLANTI KAYBI!)"))
        # CONTRACTS §6.8 — telemetri tazelik ÖZETİ hakem kaydına KENAR olayı
        # olarak düşer. Her heartbeat'e satır yazmak (1 Hz × düğüm) kaydı
        # gürültüye boğardı; hiç yazmamak ise "hat NE ZAMAN kesildi, ne kadar
        # kesik kaldı" sorusunu 21 Eylül'de cevapsız bırakırdı.
        # `dugumler` Codex'in ayrıntılı örneğidir: durum satırı ÖZET, bu alan
        # o anın ham telemetrisidir (ikisi birbirinin yerine geçmez).
        if tel_durum:
            dugumler = {}
            for ad in ("iha", "ika"):
                hb = self.son_hb.get(ad)
                dugumler[ad] = {
                    "hb_yasi_s": (None if hb is None else round(_mono - hb, 3)),
                    "telemetri": dict(self.tel.get(ad) or {}),
                    "mod": self.mod.get(ad),
                }
            self._kanit_durumu_yaz(
                "TELEMETRI_KANIT",
                "·".join(f"{a}={tel_durum[a]}" for a in sorted(tel_durum)),
                "_telemetri_kanit_durumu", "_son_telemetri_kanit_monotonic",
                bayat=sorted(a for a, d in tel_durum.items() if d != "TAZE"),
                yas_s=tel_yas, dugumler=dugumler)
        gps_etiket = getattr(self, "lbl_gps", None)
        if gps_etiket is not None:
            iha_hb = self.son_hb.get("iha")
            if iha_hb is None or _mono - iha_hb >= ARM_DURUM_TAZELIK_S:
                gps_etiket.config(
                    text="HAM GNSS: TELEMETRİ YOK/BAYAT · SEMANTİK HARİTADA "
                         "KULLANILMAZ", fg=KIRMIZI)
            else:
                gps_tel = self.tel.get("iha") or {}
                gps_var, _ = gps_telemetrisi_dogrula(gps_tel)
                gps_etiket.config(text=gps_gosterim_metni(gps_tel),
                                  fg=YESIL if gps_var else KIRMIZI)
        iha_hb = self.son_hb.get("iha")
        if iha_hb is None or _mono - iha_hb >= ARM_DURUM_TAZELIK_S:
            self._ucus("PIXHAWK MODU YOK/BAYAT", KIRMIZI)
        else:
            mod = self.mod.get("iha")
            if mod:
                self._ucus(*ucus_modu_sunumu(mod))
            else:
                self._ucus("PIXHAWK MODU YOK", KIRMIZI)
        self._arm_ui_uygula()
        self._acil_ui_uygula()
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

    def _kanit_kilidi_var(self):
        """Kanıt kaydı bozuk mu? — düğmeleri çizen HER yolun okuduğu TEK gerçek.

        🔴 Bu yordam olmadan kilit fail-OPEN'dı: `_kanit_hatasini_goster`
        düğmeleri bir kez kapatıyordu, periyodik tazeleme (`_arm_ui_uygula`,
        `_onay_dugmesini_tazele`, `_aktarim_onay_dugmesini_kur`) bayrağa
        bakmadan geri açıyordu. KIRMIZI afiş ekranda kalıyor, düğmeler
        çalışıyordu — bu deponun yasakladığı "ekran ile gerçek ayrışması"
        sınıfının ta kendisi.

        Bayrak KENDİLİĞİNDEN temizlenmez: hata giderilmeden düğmeler
        açılmaz, oturum kanıtsız devam ETMEZ.
        """
        return getattr(self, "kanit_kaydi_hatasi", None) is not None

    def _firlat_dugmesini_ciz(self, aktif):
        """`btn_firlat`ın TEK yazarı — kanıt kilidi burada uygulanır.

        Kilit varken düğme yalnız `disabled` yapılmaz, METNİ de kilidi
        söyler: kapalı bir düğmeye bakan hakem nedenini okuyamazsa
        "bozuk arayüz" ile "fail-closed kilit"i ayıramaz.
        """
        dugme = getattr(self, "btn_firlat", None)
        if dugme is None:
            return
        try:
            if self._kanit_kilidi_var():
                dugme.config(state="disabled", bg=KIRMIZI,
                             text=KANIT_KILIDI_FIRLAT_METNI)
            elif aktif:
                dugme.config(state="normal", bg=SARI)
            else:
                dugme.config(state="disabled", bg="#232e3a")
        except Exception:                      # Tk yok / fikstür
            pass

    def _onay_dugmesini_ciz(self, aktif, metin, bg=None):
        """`btn_onay`ın TEK yazarı — kanıt kilidi burada uygulanır.

        Kilitliyken `lbl_onay` da yeniden yazılır: afişi bir kez basıp
        sonra başka metinle ezmek, kilidi ekrandan SİLERDİ.
        """
        if aktif and getattr(self, "tek_rota", False) and not self._tek_rota_gecerli():
            aktif, metin = False, "ROTA GEOMETRİSİ YOK — ONAY KAPALI"
        dugme = getattr(self, "btn_onay", None)
        kilit = self._kanit_kilidi_var()
        if dugme is not None:
            try:
                if kilit:
                    dugme.config(state="disabled", bg=KIRMIZI,
                                 text=KANIT_KILIDI_ONAY_METNI)
                else:
                    dugme.config(state="normal" if aktif else "disabled",
                                 bg=bg or (SARI if aktif else "#232e3a"),
                                 text=metin)
            except Exception:                  # Tk yok / fikstür
                pass
        if not kilit:
            return
        etiket = getattr(self, "lbl_onay", None)
        afis = getattr(self, "_kanit_kilidi_metni", None)
        if etiket is not None and afis:
            try:
                etiket.config(text=afis, fg=KIRMIZI)
            except Exception:
                pass

    def _kanit_hatasini_goster(self, exc):
        """Disk hatasını görünür ve uçuş başlangıcı için fail-closed yap."""
        if self._kanit_kilidi_var():
            return
        self.kanit_kaydi_hatasi = f"{type(exc).__name__}: {exc}"
        metin = ("KANIT KAYDI HATASI — uçuş/onay başlatma kapatıldı; ARM ve "
                 f"acil komutlar kullanılabilir: {self.kanit_kaydi_hatasi}")
        self._kanit_kilidi_metni = metin
        print(metin, file=sys.stderr, flush=True)
        gunluk = getattr(self, "gunluk", None)
        if gunluk is not None:
            try:
                gunluk.config(state="normal")
                gunluk.insert("end", time.strftime("[%H:%M:%S] ") + metin + "\n",
                              "kirmizi")
                gunluk.see("end")
                gunluk.config(state="disabled")
            except Exception:
                pass
        # Kilit artık bu iki yazardan okunur; buradaki çağrı yalnız afişi
        # ANINDA basar (bir sonraki tiki beklemeden).
        self._firlat_dugmesini_ciz(False)
        self._onay_dugmesini_ciz(False, KANIT_KILIDI_ONAY_METNI)

    def _kanit_yaz(self, olay, **alanlar):
        kayit = getattr(self, "hakem_kaydi", None)
        if kayit is None or self._kanit_kilidi_var():
            return None
        try:
            return kayit.yaz(olay, **alanlar)
        except Exception as exc:
            self._kanit_hatasini_goster(
                RuntimeError(f"{olay}: {type(exc).__name__}: {exc}"))
            return None

    def _kanit_durumu_yaz(self, olay, durum, durum_alani, damga_alani, **alanlar):
        """DÖNGÜSEL kanıt olayını KENAR + tekrar aralığıyla yaz (CONTRACTS §6.8).

        NEDEN: `_kamera_tazele` ve `_durum_tazele` `_tik`ten ~8 Hz çağrılır;
        `HakemKaydi.yaz` her satırda `flush`+`fsync` yapar. Her tikte yazmak
        Tk geri çağrısını diske bağlar (ekran donar, komut gecikir) ve kaydı
        okunamaz hâle getirir. Bu yüzden:

          · durum DEĞİŞTİYSE hemen yazılır (`degisim=True`),
          · değişmediyse en çok `KANIT_TEKRAR_ARALIGI_S`'de bir
            (`degisim=False`) — "hâlâ aynı" satırı SÜREKLİLİK kanıtıdır;
            yalnız geçişler yazılsaydı kayıt "kamera görev boyunca canlıydı"
            diyemezdi.

        Damga MONOTONİK saattendir (D-384 sınıfı): duvar saati geri atlarsa
        tekrar aralığı sessizce uzardı.
        """
        onceki = getattr(self, durum_alani, None)
        son = getattr(self, damga_alani, None)
        simdi = time.monotonic()
        degisim = durum != onceki
        if (not degisim and son is not None
                and simdi - son < KANIT_TEKRAR_ARALIGI_S):
            return None
        # Damga yazma BAŞARISIZ olsa da ilerler: disk hatasında 8 Hz yeniden
        # denemek `kanit_kaydi_hatasi`yı korur ama ekranı kilitlerdi.
        setattr(self, durum_alani, durum)
        setattr(self, damga_alani, simdi)
        return self._kanit_yaz(olay, durum=durum, degisim=degisim, **alanlar)

    def _logla(self, satir, renk="soluk"):
        self.gunluk.config(state="normal")
        self.gunluk.insert("end", time.strftime("[%H:%M:%S] ") + satir + "\n", renk)
        self.gunluk.see("end")
        self.gunluk.config(state="disabled")
        self._kanit_yaz("UI_OLAYI", mesaj=str(satir), seviye=str(renk))


# ── Demo beslemesi: gerçek protokolle sahte İHA + İKA ────────────────────────
# T175 · D-323: demo IHA'si rota ACK'inden bu kadar sonra "iner" ve inis
# kanitini yayinlar. Sunucunun aktarimi ekranda gorup anlatmasina zaman birakir;
# saha davranisini taklit eder (once aktarim, sonra inis — sartname §2.2.4).
INIS_GECIKME_S = 6.0
DEMO_IHA_KOMUTLARI = frozenset(("ARM", "DISARM", "PARACHUTE", "RTL", "LAND"))


def demo_iha_komutunu_uygula(mesaj, armed, ucus_modu):
    """Demo İHA durumunu üretimdeki kabul edilen komut kümesine göre ilerlet.

    Dönüş ``(armed, ucus_modu, kabul)`` biçimindedir. Paraşüt bu basit demo
    durumunda ayrı mekanik sensöre sahip olmadığı için yalnız ACK alır; ARM ve
    acil mod durumları ise sonraki HEARTBEAT ile ayrıca doğrulanabilir.
    """
    if (not isinstance(mesaj, dict) or mesaj.get("type") != MESAJ_CMD
            or mesaj.get("hedef") != "iha"
            or mesaj.get("cmd") not in DEMO_IHA_KOMUTLARI):
        return armed, ucus_modu, False
    komut = mesaj["cmd"]
    if komut == "ARM":
        armed = True
    elif komut == "DISARM":
        armed = False
    elif komut in ACIL_UCUS_MODLARI:
        ucus_modu = komut
    return armed, ucus_modu, True


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
        ucus_modu = "AUTO"             # RTL/LAND sonraki heartbeat'te doğrulanır
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
                    bat_yuzde = max(20, int(round(92 - 0.02 * sn)))
                else:                                      # F4: KRITIK (<%15)
                    bat = round(10.4 + 0.10 * math.sin(sn / 4), 2)
                    bat_yuzde = 10
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
                           bat=bat, bat_yuzde=bat_yuzde, uydu=uydu,
                           mod=ucus_modu,
                           karar_yas=round(time.time() - son_karar_t, 2),
                           x=son_xy[0], y=son_xy[1],
                           lat=37.7648000 + son_xy[1] / 111_320.0,
                           lon=38.2786000 + son_xy[0] / 88_600.0,
                           gps_fix=3 if durum.get("iha_gnss", True) else 1,
                           armed=armed, pixhawk_canli=True)
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
                if m.get("type") == MESAJ_ACK and m.get("ref") == rota["seq"]:
                    if not onay:
                        onay_t = time.time()
                    onay = True
                else:
                    armed, ucus_modu, kabul = demo_iha_komutunu_uygula(
                        m, armed, ucus_modu)
                    if not kabul:
                        continue
                    link.send(encode(ack(
                        m["seq"], "iha", MESAJ_CMD, ref_cmd=m["cmd"],
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


def kapanis_kaynaklarini_temizle(app, link):
    """YKİ kaynaklarını birbirinden bağımsız ve en iyi gayretle kapat.

    Kamera iş parçacığındaki ya da kanıt günlüğündeki bir kapanış hatası, kalan
    kaynağın açık bırakılmasına neden olmamalıdır.  Hatalar stderr'e ayrı ayrı
    yazılır; çağıran, kapanışın hangi parçalarının aksadığını dönüş değerinden
    de görebilir.
    """
    kaynaklar = (
        ("KAMERA", getattr(app, "kamera_istemci", None), "durdur"),
        ("KANIT KAYDI", getattr(app, "hakem_kaydi", None), "kapat"),
        ("HABERLEŞME", link, "close"),
    )
    hatalar = []
    for ad, kaynak, metot_adi in kaynaklar:
        if kaynak is None:
            continue
        try:
            getattr(kaynak, metot_adi)()
        except Exception as exc:
            hata = f"{ad} KAPATMA HATASI: {exc}"
            hatalar.append(hata)
            print(hata, file=sys.stderr, flush=True)
    return tuple(hatalar)


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
    # CONTRACTS §7.6 (results/tunel_20260916/ON_KAYIT.md): tek RFD900A Pixhawk
    # TELEM1'de; COM'un tek sahibi Mission Planner'dır. NAVITAS çerçeveleri MP
    # aynasından (UDP Client 127.0.0.1:14570) MAVLink TUNNEL ile alınır.
    ap.add_argument("--tunel", metavar="HOST:PORT",
                    help=f"MAVLink TUNNEL yer ucu (Mission Planner aynası, örn. "
                         f"{TUNEL_YER_UC}); --serial/--demo/--ika/--iha ile "
                         f"birlikte kullanılamaz")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument(
        "--kamera-url", default=os.environ.get("NAVITAS_KAMERA_URL"),
        help=("Jetson RAW kamera kökü (örn. http://192.168.4.2:8080). "
              "Yalnız ayrı Wi-Fi/LAN; SiK üzerinden video taşınmaz. "
              "Varsayılan: NAVITAS_KAMERA_URL, yoksa kamera kapalı"))
    # T226 (D-443): video kaynak etiketi — başlık + KAMERA_KANIT kaynak alanı.
    ap.add_argument(
        "--kamera-etiket", default="",
        help=("video kaynak etiketi (örn. 'MK15 · HDMI · yakalama'): video "
              "paneli başlığına ve KAMERA_KANIT kaynak alanına yazılır "
              "(CONTRACTS §6.8). Video karar üretmez — onay telsiz verisine "
              "verilir. Varsayılan boş; en çok "
              f"{KAMERA_ETIKETI_AZAMI_KARAKTER} karakter"))
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
    ap.add_argument(
        "--hakem-log", type=Path,
        help=("kalıcı UTF-8 JSONL kanıt yolu. Verilmezse "
              "results/prova/<tarih_saat_pid>/hakem_log.jsonl otomatik açılır"))
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
    ap.add_argument("--tek-rota", action="store_true",
                    help="Şerit şeması yerine gelen waypoint geometrisi ve hareket planı; FDA'da otomatik açılır")
    ap.add_argument("--gorunum", choices=tuple(GORUNUM_SECENEKLERI),
                    help="açılış görünümü (varsayılan: saha; --tek-rota/--fda ile rota)")
    args = ap.parse_args()

    try:
        args.kamera_etiket = kamera_etiketi_dogrula(args.kamera_etiket)
    except ValueError as exc:
        ap.error(f"--kamera-etiket: {exc}")
    if args.tunel and args.serial:
        ap.error("--tunel ile --serial birlikte kullanılamaz")
    if args.tunel and args.demo:
        ap.error("--demo yalnız UDP kipinde kullanılabilir (--tunel ile olmaz)")
    if args.tunel and args.ika:
        ap.error("--tunel ile --ika birlikte kullanılamaz")
    if args.tunel and args.iha:
        ap.error("--tunel ile --iha birlikte kullanılamaz; tünel kipinde İHA "
                 "aynı MAVLink hattındadır ve UDP hedefi uygulanmaz")
    if args.serial and args.demo:
        ap.error("--demo yalnız UDP kipinde kullanılabilir")
    if args.serial and args.ika:
        ap.error("--serial ile --ika birlikte kullanılamaz")
    if args.serial and args.iha:
        ap.error("--serial ile --iha birlikte kullanılamaz; seri kipte İHA "
                 "aynı SiK hattındadır ve UDP hedefi uygulanmaz")
    if not args.serial and not args.demo and not args.ika and not args.tunel:
        ap.error("UDP kipinde --ika HOST:PORT zorunlu")
    if not args.serial and not args.demo and not args.iha and not args.tunel:
        ap.error("UDP kipinde --iha HOST:PORT zorunlu: ARM/DISARM/RTL/LAND "
                 "efemer heartbeat portuna gönderilemez")

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
    elif args.tunel:
        try:
            link = TunelLink(uc_coz(args.tunel), KIMLIK_YER)
        except (OSError, ValueError) as exc:
            ap.error(
                f"YKİ tünel ucu açılamadı ({args.tunel}): {exc}. Mission Planner "
                "aynası (UDP Client) bu porta yazmalı; başka bir YKİ aynı portu "
                "kullanıyor olabilir.")
        ika_peer = None
        iha_peer = None
    else:
        h, p = args.bind.split(":")
        try:
            link = yks_udp_linki_ac((h, int(p)))
        except OSError as exc:
            ap.error(
                f"YKİ UDP dinleme ucu açılamadı ({args.bind}): {exc}. "
                "Başka bir YKİ/izleyici aynı portu kullanıyor olabilir; çalışan "
                "oturumu kapatın veya açıkça farklı --bind portu seçin.")
        ika_peer = args.ika
        iha_peer = args.iha

    # Elestiri 2 bulgu 2: `f'tunel://{None}'` bos olmayan dizgedir; kosullu ifade.
    dinleme = args.serial or (f"tunel://{args.tunel}" if args.tunel else args.bind)
    oturum_kunyesi = yki_oturum_kunyesi(
        fda_kipi=args.fda,
        dinleme=dinleme,
        iha_hedef=iha_peer,
        ika_hedef=ika_peer,
        seri_port=args.serial,
        baud=args.baud,
        kamera_url=args.kamera_url,
        algi_kaynagi=args.kaynak or YksArayuz.ALGI_VARSAYILAN_KAYNAK,
        gorunum=args.gorunum or ("rota" if args.tek_rota or args.fda else "saha"),
        baslatma_argumanlari=sys.argv[1:],
    )

    hakem_log_yolu = (args.hakem_log if args.hakem_log is not None
                       else varsayilan_hakem_log_yolu(_PROJE_KOKU))
    kok = tk.Tk()
    # otomatik onay YOK: hakem onay akışı elle incelenebilsin (buton/R kısayolu)
    try:
        app = YksArayuz(
            kok, link, otomatik_onay=False, demo=args.demo, ika_peer=ika_peer,
            iha_peer=iha_peer, kamera_url=args.kamera_url,
            hakem_log_yolu=hakem_log_yolu,
            oturum_kunyesi=oturum_kunyesi,
            kamera_etiket=args.kamera_etiket, tek_rota=args.tek_rota or args.fda)
    except Exception:
        link.close()
        kok.destroy()
        raise
    app._logla(f"YKS hazır — dinleniyor: "
               f"{dinleme}", "mavi")
    app._logla(f"KALICI HAKEM KAYDI: {hakem_log_yolu}", "mavi")
    app._logla(
        (f"RAW kamera LAN kaynağı: {args.kamera_url}" if args.kamera_url else
         "RAW kamera KAPALI: --kamera-url/NAVITAS_KAMERA_URL verilmedi; "
         "telemetri ve komut hattı çalışmaya devam eder"),
        "mavi" if args.kamera_url else "sari")
    if args.kamera_etiket:
        app._logla(
            (f"VİDEO KAYNAK ETİKETİ: {args.kamera_etiket} — {KAMERA_KARAR_NOTU}"
             if args.kamera_url else
             f"VİDEO KAYNAK ETİKETİ verildi ({args.kamera_etiket}) ama "
             "--kamera-url YOK: etiket yalnız başlıkta, kanıt kaynağı boş"),
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
        app.fda_kipini_uygula()          # CONTRACTS §6.7 (bütçe + etiket + kilitler)
        app._logla(
            "§5.3.2 FDA KİPİ: İHA bütçesi "
            f"{_ss(SARTNAME_FDA_OPERASYON_SURESI_S)} (kalkış+tespit+aktarım+"
            "iniş). Süreyi aşan takım 0 PUAN alır.", "sari")
        app._logla(
            "FDA: paraşüt ve İKA düğmeleri KAPALI (çoklu rotor, İKA yok); "
            "hakem 2/2 onayı İKA kanıtı ARAMAZ — dayanak YKS'ye canlı aktarım.",
            "sari")
    if args.kaynak:
        app.algi_kaynak = args.kaynak
        app.algi_idx = 0
        app._logla(f"ALGI kaynağı (--kaynak): {args.kaynak}", "mavi")
    if args.gorunum:
        app.gorunum(GORUNUM_SECENEKLERI[args.gorunum])
        app._logla(f"Açılış görünümü (--gorunum): {args.gorunum}", "mavi")
    elif args.tek_rota or args.fda:
        app.gorunum("rota")
        app._logla("TEK ROTA GÖSTERİMİ: alınan waypoint geometrisi; şerit veya GPS konumu uydurulmaz", "mavi")

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
        kapanis_kaynaklarini_temizle(app, link)


if __name__ == "__main__":
    main()
