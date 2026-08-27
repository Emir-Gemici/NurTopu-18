"""SENTETİK ARENA ÜRETECİ — şartname geometrisinde, gerçek enkaz dokularıyla.

NEDEN (BULGULAR §12): RescueNet mAP'i doygunlaştı ve arena benzeri sahnelere
TRANSFER OLMUYOR. Gerçek arena verisi henüz yok (saha kurulmadı). Ama arena
KURALLARLA TANIMLI bir domain: kare alan, birkaç koridor, biri açık, diğerleri
molozla kapalı. Bu yüzden sentetik olarak üretilebilir ve yer gerçeği PİKSEL
PİKSEL KUSURSUZ olur — RescueNet'in etiket belirsizliği tavanı burada yok.

Malzeme uydurma DEĞİL: enkaz/ağaç/araç kesitleri 50_doku_bankasi.py ile
RescueNet'in kendi piksel maskelerinden kesilmiş GERÇEK dokulardır.
Yöntem: domain randomization + cut-paste sentezi.

ETİKET SEMANTİĞİ (2 sınıf, mevcut şemayla birebir aynı):
  0 traversable = koridorun AÇIK (geçilebilir) kısmı
  1 blocked     = koridorun MOLOZLA KAPALI kısmı
  koridor dışı moloz/duvar/zemin = ETİKETSİZ (yol değil) — bu, modele
  "moloz her yerde geçilemez demek değil, YOL üstündeyse blocked" ayrımını
  ve "moloz asla traversable değil" kuralını öğretir.

Kullanım:
  venv\\Scripts\\python.exe 51_sentetik_arena.py --adet 3000
  venv\\Scripts\\python.exe 51_sentetik_arena.py --adet 12 --onizleme
"""
import argparse
import json
import math
import random
import re
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

import sys as _sys
_sys.path.insert(0, str(REPO / "codes"))
from karar_sozlesmesi import serit_no   # serit otoritesi TEK KAYNAK

BANKA = Path(__file__).parent / "doku_bankasi"
# T185 (D-324): banka bu depoda YOK; `50_doku_bankasi.py` ile birlikte
# egitim agacinda duruyor (`O:/navitas-local-train/doku_bankasi`).
# Yol CIPLAK sabitti ve betik "banka eksik" deyip cikiyordu — yani
# uretec bu depoda HIC kosturulamiyordu. `--banka` ile verilebilir;
# verilmezse eski varsayilan aynen kalir.
CIKTI = Path(r"O:\navitas\dataset\sentetik_arena")
TUVAL = 800          # üretim tuvali (dönüşüm payı için büyük)
BOYUT = 640          # son görüntü boyutu
# T55: manifest, `data/arena_kompozit` ile AYNI olcek varsayimini kullanir
# ki iki kume ayni araclarla olculebilsin: HTAB son goruntunun GENISLIGINE
# eslenir. Bu bir kamera olcumu DEGILDIR; arena kadrajin tamamini doldurmaz
# (yatay `kenar_x` payi vardir) ve o pay da manifeste yazilir.
HTAB_M = 50.0        # sartname HTAB 50x50 m

# T71 (D-99) · SS2.1: "IHA-IB 30 metre x 30 metre boyutlarinda MAVI bolgedir"
# (parasutle inis alani). T60'ta "figurde yok" diye kapsam disi birakilmisti;
# figurun YAPAY ZEKA urunu oldugu anlasilinca (D-99) o gerekce COKTU — artik
# METIN otoritedir ve metin bu bolgeyi ACIKCA tanimliyor.
IHA_IB_KENAR_M = 30.0
# Ton sartnamede belirtilmemistir; tek renge yakinsamak D-95'te kirilganlik
# uretti, bu yuzden sahne basina degisir. Hepsi MAVI ailesindendir (BGR).
IHA_IB_MAVILERI = [
    (170, 90, 30), (200, 120, 40), (150, 70, 20),
    (185, 105, 55), (215, 145, 70),
]
HEDEF_KENAR_M = 2.0  # sartname SS2.2.6
IZGARA_ADIM_M = HEDEF_KENAR_M  # sartname figurundeki kareler, HB ile ayni olcek
IZGARA_RENK = (48, 48, 48)
IZGARA_OPAKLIK = 0.30
HB_FIGUR_ZEMIN = (38, 38, 38)
HB_BEYAZ = (242, 242, 242)
HB_KIRMIZI = (25, 25, 210)
# T71: ped rengi sartnamede BELIRTILMEMISTIR. Tek renge yakinsamak D-95'te
# kirilganlik uretti; bu yuzden sahne basina degisir. Kirmizi H her zaman
# ustundedir — degisken olan yalnizca ZEMIN.
HB_PED_RENKLERI = [
    (242, 242, 242),   # beyaz branda
    (38, 38, 38),      # koyu ped
    (185, 185, 180),   # acik gri beton
    (120, 125, 130),   # orta gri
    (60, 95, 140),     # kahve/haki bez
]
BARIYER_KIRMIZI = (35, 35, 220)
BARIYER_BEYAZ = (238, 238, 238)
KADRAJ_OLCEK_KAYNAGI = (
    "kontrollu sentetik varsayimi: HTAB / son goruntu GENISLIGI; "
    "gercek kamera mpp olcumu degildir"
)
TEMIZLIK_IMZASI_DOSYASI = ".navitas_sentetik_arena_ureteci"
TEMIZLIK_IMZASI = "NAVITAS_SENTETIK_ARENA_V1\n"


# ---------------------------------------------------------------- doku yükleme
# Arena DÜZ bir alandır: açık zemin + AYRIK moloz yığınları. RescueNet yamaları
# ham haliyle baştan başa enkazdır; o yüzden zemin/yol yamaları "dağınıklık"
# (Laplacian varyansı) ile süzülür — yalnız TEMİZ yüzeyler kalır.
TEMIZ_ORAN = {"zemin": 0.45, "yol": 0.55}   # en temiz yüzde kaçı tutulsun

# ════════════════════════════════════════════════════════════════════════════
# T71 · RENK STRATEJISI: TEK NOKTAYA BOYAMA -> SAHNE BASINA GENIS BANT
# ════════════════════════════════════════════════════════════════════════════
# ESKIDEN (T60): her zemin yuzeyi ve HER moloz kesiti TEK bir sabit LAB
# noktasina boyaniyordu (LAB_ZEMIN_HEDEF / LAB_MOLOZ_HEDEF). O noktalar D-87'de
# `sartname_s9_arena.png`den olculmustu.
#
# 🔴 IKI SEBEPLE GECERSIZ:
#  1. D-99: o kare GERCEK ARENA DEGIL. Sartname s.8 Sekil 1 alt yazisi
#     "Gorsel TAMAMEN YAPAY ZEKA ile olusturulmustur. Gercek alani dogrudan
#     yansitmamaktadir." Yani hedefler bir ILLUSTRASYONUN kunyesiydi.
#  2. D-95: v25 tek kunyeye oturunca ona BAGIMLI oldu; dagilim disi bir
#     sahnede conf 0.02'ye kadar SIFIR zemin uretip sahneyi butunuyle ENGEL
#     ilan etti. Tek palete yakinsamak KIRILGANLIK uretiyor.
#
# YENI STRATEJI: gercek arenanin rengini BILMIYORUZ. Bu yuzden tek bir renge
# yakinsamak yerine GENIS bir bant taranir; her sahne kendi hedefini cekilisle
# alir. Model boylece "arena su renktir" degil "zemin ile moloz AYRISIR"
# kuralini ogrenmek zorunda kalir.
#
# Bantlar gercek ortulerin makul araligini kapsar (OpenCV LAB, a/b 128 merkezli):
#   zemin : kuru toprak · kum · cakil · beton · nemli toprak · asfalta yakin
#   moloz : beton · tugla · tas · golgeli enkaz
LAB_ZEMIN_BANDI = {
    "L": (105.0, 190.0),      # koyu nemli toprak .. parlak kum
    "a": (125.0, 135.0),      # -3 .. +7   (hafif yesilimsi .. hafif kizil)
    "b": (127.0, 156.0),      # -1 .. +28  (notr gri .. sicak kum)
    # T66: b bandi 129..150'den genisletildi. Ada geometrisiyle traversable
    # bolgesi IKI yuzeyi birden kapsar hale geldi (koridor izi + serit zemini)
    # ve bolge ORTALAMASI ortalamaya regresyon yapip olculen b std'yi
    # 5,90 -> 4,69'a dusurdu. Manifest CEKILISLERI degismemisti (b std 6,18
    # her iki kumede de) — yani uretec cesitliligi dusmemis, OLCUM bilesimi
    # degismisti. Bant yine de genisletildi: D-95'in yonu "daralt" degil
    # "GENISLET"tir.
}
LAB_MOLOZ_BANDI = {
    "a": (125.0, 132.0),      # -3 .. +4
    "b": (126.0, 140.0),      # -2 .. +12
}
# Moloz L'si zeminden BAGIMSIZ cekilmez: sahne cozulebilir kalmali. Moloz
# zeminden KOYUDUR (golgeli enkaz), ama farkin BUYUKLUGU genis taranir.
# T60'ta olculen tek deger dL = 41,2 idi; artik 25..75 arasi.
LAB_MOLOZ_DL = (25.0, 75.0)

ZEMIN_KROMA_KORUMA = 0.35
MOLOZ_KROMA_KORUMA = 0.20

# Sahne basina secilen hedefler. Uretec TEK IS PARCACIKLIDIR; `oku` ->
# `moloz_rengi` zinciri cok derin oldugu icin hedef parametre olarak
# gecirilmek yerine burada tutulur. `sahne_uret` her sahnenin BASINDA
# `sahne_renklerini_sec` ile ayarlar; boylece bir sahne icinde SABIT,
# sahneler arasinda CESITLIDIR.
_SAHNE_ZEMIN_HEDEFI = (154.5, 130.0, 140.25)
_SAHNE_MOLOZ_HEDEFI = (108.0, 127.5, 131.75)


def sahne_renklerini_sec(rng):
    """Bu sahnenin zemin/moloz LAB hedeflerini bantlardan cek."""
    global _SAHNE_ZEMIN_HEDEFI, _SAHNE_MOLOZ_HEDEFI
    zl = rng.uniform(*LAB_ZEMIN_BANDI["L"])
    za = rng.uniform(*LAB_ZEMIN_BANDI["a"])
    zb = rng.uniform(*LAB_ZEMIN_BANDI["b"])
    dl = rng.uniform(*LAB_MOLOZ_DL)
    ma = rng.uniform(*LAB_MOLOZ_BANDI["a"])
    mb = rng.uniform(*LAB_MOLOZ_BANDI["b"])
    _SAHNE_ZEMIN_HEDEFI = (zl, za, zb)
    _SAHNE_MOLOZ_HEDEFI = (max(20.0, zl - dl), ma, mb)
    return _SAHNE_ZEMIN_HEDEFI, _SAHNE_MOLOZ_HEDEFI

# Prosedurel zemin paleti (BGR), D-87'nin sicak/acik zemin bandinda. Yol icin
# ayri bir D-87 renk hedefi OLCULMEDI; T57 yol dokusu ve mevcut renk cesitliligi
# korunur. `PROSEDUREL_PAYI` degismez.
PALET = {
    "zemin": [(122, 140, 153), (125, 144, 158), (131, 149, 162)],
    "yol":   [(95, 95, 95), (110, 110, 112), (78, 80, 82), (130, 130, 128)],
}


def lab_ortalamasini_tasi(im, hedef, kroma_koruma=1.0):
    """BGR/BGRA dokunun LAB ortalamasini tasirken mikro yapisini koru.

    Alfa kesitlerinde yalniz gorunen pikseller olculur ve boyanir; alfa kanali
    bit-bit korunur. Additif LAB kaymasi, prosedurel tek-renk dolgu degildir.
    """
    if im.ndim != 3 or im.shape[2] not in (3, 4):
        raise ValueError("LAB yeniden boyama girdisi BGR veya BGRA olmali")
    bgr = im[:, :, :3]
    gorunen = (im[:, :, 3] > 0) if im.shape[2] == 4 else np.ones(im.shape[:2], bool)
    if not gorunen.any():
        return im.copy()
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    ort = lab[gorunen].mean(axis=0)
    hedef = np.asarray(hedef, np.float32)
    lab[:, :, 0] += hedef[0] - ort[0]
    # Renkli catiyi gecirmemek icin a/b sapmasi daraltilir; L ve dolayisiyla
    # tum mikro-yapi/golge aynen additif tasinir. Bu, duz renk dolgusu degildir.
    lab[:, :, 1:3] = (hedef[1:3]
                       + (lab[:, :, 1:3] - ort[1:3]) * float(kroma_koruma))
    yeni_bgr = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    sonuc = im.copy()
    sonuc[:, :, :3][gorunen] = yeni_bgr[gorunen]
    return sonuc


def _daginiklik(im):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def banka_yukle():
    b = {}
    for k in ("enkaz", "agac", "arac"):
        d = BANKA / k
        b[k] = sorted(d.glob("*.png")) if d.exists() else []
        if not b[k]:
            raise SystemExit(f"doku bankası eksik: {d}\nÖnce 50_doku_bankasi.py çalıştırın.")
    # moloz dokusu: süzme YOK (moloz zaten dağınıktır), belleğe al
    b["enkaz_doku"] = []
    for p in sorted((BANKA / "enkaz_doku").glob("*.png")):
        im = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if im is not None and min(im.shape[:2]) >= 32:
            # T71: ONCEDEN BOYAMA YOK. Eskiden burada tek sabit hedefe
            # boyaniyordu ve tum kume ayni molozu goruyordu; artik ham tutulur,
            # sahne basina `_SAHNE_MOLOZ_HEDEFI` ile boyanir.
            b["enkaz_doku"].append(im)
    if not b["enkaz_doku"]:
        raise SystemExit("enkaz_doku boş — 50_doku_bankasi.py'yi --sifirla ile koşun.")
    print(f"  enkaz_doku: {len(b['enkaz_doku'])} moloz dokusu")

    # yüzey yamaları: belleğe al, dağınıklığa göre süz
    for k in ("yol", "zemin"):
        d = BANKA / k
        yol_listesi = sorted(d.glob("*.png"))
        if not yol_listesi:
            raise SystemExit(f"doku bankası eksik: {d}\nÖnce 50_doku_bankasi.py çalıştırın.")
        yuklu = []
        for p in yol_listesi:
            im = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if im is not None and min(im.shape[:2]) >= 32:
                yuklu.append((_daginiklik(im), im))
        yuklu.sort(key=lambda t: t[0])
        tut = max(20, int(len(yuklu) * TEMIZ_ORAN[k]))
        b[k] = [im for _, im in yuklu[:tut]]
        print(f"  {k}: {len(yuklu)} yamadan {tut} temiz olanı tutuldu "
              f"(dağınıklık ≤ {yuklu[tut - 1][0]:.0f})")
    return b


# T57 · PROSEDUREL YUZEY DOKUSU — OLCULMUS SABITLER (REVIEW_LOG D-79, D-80)
#
# KUSUR: gurultu `im.shape` = (H, W, 3) ile uretiliyordu, yani HER KANAL
# BAGIMSIZ. Gercek yuzey dokusu ise agirlikla PARLAKLIK degisimidir. Sonuc:
# duz zemin uzerinde RENKLI BENEK.
#
# HEDEF NASIL SECILDI (korukoru kopyalanmadi): banka yamalari GERCEK SAHNE
# parcalaridir; parlaklik std'lerinin buyuk kismi dokudan degil ICERIKTEN
# (golge, nesne, yapi) gelir. Bu yuzden 6 px Gauss ile YUKSEK GECIRGEN alinip
# yalniz DOKU bileseni olculdu (n=40 yama):
#
#   kaynak              global kroma  global parlak  DOKU kroma  DOKU parlak  k/p
#   prosedurel zemin           7,92          9,50        6,95         8,10   0,86
#   prosedurel yol             6,56          9,97        6,17         8,45   0,73
#   GERCEK banka zemin         8,12         50,37        1,82        12,15   0,15
#   GERCEK banka yol           1,05          6,90        0,54         3,68   0,15
#
# Iki gercek kategori de k/p = 0,15'te bulusuyor — hedef budur. Parlaklik
# genligi ise kategoriye gore AYRI: zemin ~12, yol ~3,7 (asfalt daha duzdur).
# Asagidaki bantlar bu hedeflere kalibre edildi (supurme D-80'de).
DOKU_GENLIGI = {                    # (ince_alt, ince_ust, kaba_alt, kaba_ust)
    "zemin": (7.0, 10.5, 8.0, 12.5),   # -> DOKU parlaklik ~8,5-12,7
    "yol":   (2.0, 4.0, 2.0, 5.0),     # -> DOKU parlaklik ~2,6-5,1
}
RENK_SAPMASI = 1.5                  # -> DOKU kroma/parlaklik ~0,14 (hedef 0,15)

# `yuzey_sec` prosedurel payi — OLCUMLE gerekcelendirildi. Docstring "%45"
# diyordu ama kod %60 kullaniyordu; ikisi de olculmemisti. Bankadaki yamalarin
# gercekten "temiz duz yuzey" olup olmadigi olculdu (ICERIK parlaklik std < 8):
#
#   kategori   n     p50 icerik std   TEMIZ (<8)
#   zemin    315            39,8         2/315   -> banka temiz zemin VEREMIYOR
#   yol      385             9,9       166/385   -> banka temiz yol BOL VERIYOR
#
# Bu yuzden pay KATEGORIYE GORE ayrildi. Sifirlanmadi: prosedurel yuzey
# hala tek temiz-zemin kaynagidir; ama yolda gercek yama daha gercekcidir.
PROSEDUREL_PAYI = {"zemin": 0.70, "yol": 0.35}


def prosedurel_yuzey(rng, kat, boyut=128):
    """RescueNet'te bulunmayan TEMİZ yüzey (düz çim/toprak/beton/asfalt).

    Doku TEK KANALLI parlaklik gurultusudur ve uc kanala AYNI uygulanir;
    renk sapmasi ayrica ve ZAYIF eklenir (bkz. `RENK_SAPMASI`).
    """
    taban = np.array(rng.choice(PALET[kat]), np.float32)
    taban = taban * rng.uniform(0.82, 1.18)
    im = np.full((boyut, boyut, 3), taban, np.float32)
    ia, iu, ka, ku = DOKU_GENLIGI.get(kat, DOKU_GENLIGI["zemin"])
    ince = np.random.normal(0, rng.uniform(ia, iu), (boyut, boyut))
    kaba = np.random.normal(0, rng.uniform(ka, ku),
                            (boyut // 8, boyut // 8))
    kaba = cv2.resize(kaba, (boyut, boyut), interpolation=cv2.INTER_CUBIC)
    im += (ince + kaba)[:, :, None]                     # UC KANALA AYNI
    im += np.random.normal(0, RENK_SAPMASI, im.shape)   # ZAYIF renk sapmasi
    sonuc = np.clip(im, 0, 255).astype(np.uint8)
    if kat == "zemin":
        sonuc = lab_ortalamasini_tasi(
            sonuc, _SAHNE_ZEMIN_HEDEFI, ZEMIN_KROMA_KORUMA)
    return sonuc


def yuzey_sec(rng, banka, kat):
    """Kategoriye gore prosedurel/gercek yama sec (`PROSEDUREL_PAYI`)."""
    if rng.random() < PROSEDUREL_PAYI.get(kat, 0.60) or not banka[kat]:
        return prosedurel_yuzey(rng, kat)
    yama = banka[kat][rng.randrange(len(banka[kat]))]
    return (lab_ortalamasini_tasi(yama, _SAHNE_ZEMIN_HEDEFI, ZEMIN_KROMA_KORUMA)
            if kat == "zemin" else yama)


def arena_yuzeyi_renklendir(yuzey):
    """Koridor dokusunu D-87'de olculen sicak zemin bandina yeniden boya.

    Yol icin ayri bir renk hedefi yoktur; T60 arenasinda HB'ye giden
    traversable yuzey, olculmus ZEMIN sinifidir. Doku/golge degismez.
    """
    return lab_ortalamasini_tasi(
        yuzey, _SAHNE_ZEMIN_HEDEFI, ZEMIN_KROMA_KORUMA)


def moloz_rengi(rgba, rng):
    """Kesitin LAB ortalamasini moloz bandina tasi; alfa/dokuyu koru.

    NEDEN: RescueNet kesitleri hasarlı BİNA çatısıdır — turkuaz, pembe, kiremit.
    Arena molozu ise beton ve tuğladır. Çatı renkleri bırakılırsa model
    "renkli yama = engel" gibi yanlış bir kural öğrenir. T60: eski %35
    dokunmama dali renkli catilari geciriyordu; artik HER kesit yeniden boyanir.
    Eski uc RNG cekilisi akisi kaydirmamak icin yine tuketilir.
    """
    rng.random()
    rng.uniform(0.10, 0.40)
    rng.randint(5, 22)
    return lab_ortalamasini_tasi(rgba, _SAHNE_MOLOZ_HEDEFI, MOLOZ_KROMA_KORUMA)


# Kesitler sahne başına ~30 kez diskten okunuyordu; 3300 sahne = ~100 bin PNG
# açma. Bellekte tut (tüm banka ~300 MB, makinede 96 GB var).
_KESIT_ONBELLEK = {}


def oku(p, alfali, rng=None):
    anahtar = str(p)
    im = _KESIT_ONBELLEK.get(anahtar)
    if im is None:
        im = cv2.imread(anahtar, cv2.IMREAD_UNCHANGED if alfali else cv2.IMREAD_COLOR)
        if im is None or (alfali and (im.ndim != 3 or im.shape[2] != 4)):
            _KESIT_ONBELLEK[anahtar] = False
            return None
        _KESIT_ONBELLEK[anahtar] = im
    elif im is False:
        return None
    # moloz_rengi yeni dizi döndürür; önbellekteki orijinal değişmez
    return im if rng is None else moloz_rengi(im, rng)


# ---------------------------------------------------------------- geometri
def serit(rng, x0, genislik, t0, t1, n=40, alt=None, ust=None, duz=False):
    """Alttan yukarı giden EĞRİ koridorun [t0,t1] dilimini poligon olarak ver.

    t=0 arenanın altı (y=alt), t=1 üstü (y=ust). Eğrilik sinüs; genişlik
    hafif dalgalanır.
    """
    if alt is None:
        alt = TUVAL
    if ust is None:
        ust = 0.0
    genlik = rng.uniform(0, TUVAL * 0.10)
    faz = rng.uniform(0, 2 * math.pi)
    frek = rng.uniform(0.6, 1.8)
    gd = rng.uniform(0.0, 0.25)      # genişlik dalgalanması
    if duz:
        # T56 · KADRAJ KIPI: koridor DUZ. Egrilik EGITIM kipinde KALIR —
        # gerekcesi (model "duz dikey bant = koridor" kestirmesini ogrenmesin)
        # egitim zemini icin gecerlidir. OLCUM zemininin isi gerceklik:
        # sartname arenasinda koridorlar duzdur. Dort rng degeri yine cekilir,
        # boylece iki kip ayni tohumda karsilastirilabilir kalir.
        genlik = 0.0
        gd = 0.0

    sol, sag = [], []
    for i in range(n):
        t = t0 + (t1 - t0) * i / (n - 1)
        y = alt + (ust - alt) * t
        x = x0 + genlik * math.sin(2 * math.pi * frek * t + faz)
        w = genislik * (1 + gd * math.sin(3 * math.pi * t + faz))
        sol.append((x - w / 2, y))
        sag.append((x + w / 2, y))
    return np.array(sol + sag[::-1], np.float32)


def ic_serit(poly, oran, kaydir=0.0):
    """Şerit poligonunun İÇİNDEN geçen DAR iz poligonu.

    NEDEN: gerçek arena görüntüsü `2.png`'de geçilebilir bölge ayrı bir yüzey
    değil — moloz yığınlarının ARASINDAN geçen dar bir izdir ve zeminle aynı
    malzemedendir. Hem RescueNet hem üretecin ilk sürümü modele "geçilebilir =
    ayırt edilebilir yüzey" öğretiyordu; bu yüzden hiçbir model orada çıktı
    üretemedi. Bu fonksiyon o boşluğu kapatır.

    Kenarlar şeridin KENDİ kenarlarından türetildiği için iz asla şeridi aşamaz.
    oran: şerit genişliğinin kaçta kaçı · kaydir: yanal kayma (-1..1, 0=ortada)
    """
    n = len(poly) // 2
    sol, sag = [], []
    for i in range(n):
        a, b = poly[i], poly[len(poly) - 1 - i]
        merkez = (a + b) / 2 + (b - a) * (kaydir * (0.5 - oran / 2))
        yari = (b - a) * (oran / 2)
        sol.append(merkez - yari)
        sag.append(merkez + yari)
    return np.array(sol + sag[::-1], np.float32)


def _harmanli_dose(yama, h, w, bindirme_orani=0.35):
    """Yamayi DIKISSIZ dose: ortusen doseme + tuy agirlikli capraz gecis.

    Aynalama YOK. Ortusme bolgesinde her dosemenin agirligi kenara dogru
    sifira iner; toplamda gecis yumusar ve sert dikis gorunmez. Yalniz
    numpy/OpenCV kullanir.
    """
    th, tw = yama.shape[:2]
    bind = max(1, int(min(th, tw) * bindirme_orani))
    adim_y, adim_x = max(1, th - bind), max(1, tw - bind)
    fy = np.clip(np.minimum(np.arange(th), th - 1 - np.arange(th)) / float(bind),
                 0.0, 1.0)
    fx = np.clip(np.minimum(np.arange(tw), tw - 1 - np.arange(tw)) / float(bind),
                 0.0, 1.0)
    agirlik_yama = (fy[:, None] * fx[None, :]).astype(np.float32)[:, :, None]
    agirlik_yama = np.maximum(agirlik_yama, 1e-3)
    H, W = h + 2 * th, w + 2 * tw
    birikim = np.zeros((H, W, 3), np.float32)
    toplam = np.zeros((H, W, 1), np.float32)
    parca = yama.astype(np.float32)
    for oy in range(0, H - th + 1, adim_y):
        for ox in range(0, W - tw + 1, adim_x):
            birikim[oy:oy + th, ox:ox + tw] += parca * agirlik_yama
            toplam[oy:oy + th, ox:ox + tw] += agirlik_yama
    sonuc = birikim[th:th + h, tw:tw + w] / np.maximum(toplam[th:th + h, tw:tw + w],
                                                       1e-6)
    return np.clip(sonuc, 0, 255).astype(np.uint8)


def doku_tekrar(yama, h, w, rng, kadraj=False):
    """Yamayı hedef alana döşe — GÖRÜNÜR TEKRAR DESENİ ÜRETMEDEN.

    Küçük yamalar (48-64 px) 800 piksele döşenince 10-25 tekrar çıkıyor ve
    apaçık periyodik bir desen oluşuyordu. Bu, sentetik olduğunu ele veren
    türden bir artefakt: model onu kestirme ipucu olarak öğrenir. İki önlem:
    (1) yama en az hedefin 1/3'ü olacak şekilde büyütülür → en çok ~3 tekrar,
    (2) komşu döşemeler aynalanır → kalan tekrar da göze çarpmaz.
    """
    hedef = max(h, w) / rng.uniform(1.0, 3.0)
    if kadraj:
        # T56 · KADRAJ KIPI: AYNALAMA YOK. Aynalama egitim kipinde kalir
        # (gerekcesi: kalan tekrari goze batirmamak). Olcum zemininde ise
        # aynalanmis kesitler KALEYDOSKOPIK bir desen uretiyordu.
        #
        # ⚠ ILK DENEMEM YANLISTI: yamayi TEK dosemeye buyuttum; periyodiklik
        # yapisal olarak yok oldu ama 48-64 px yama 800 piksele cikinca DOKU
        # DA yok oldu — gozle bakildiginda asfalt degil BULANIK RENKLI LEKE
        # cikti. Sayi iyiydi, gorsel kotuydu; gorsel kazandi.
        #
        # Cozum: ILIMLI buyutme (~2 doseme, doku korunur) + DIKIS HARMANLAMA.
        # Ortusme bolgesinde tuy (feather) agirlikli capraz gecis yapilir,
        # boylece ne sert dikis ne de aynalama simetrisi kalir.
        ol = max((max(h, w) / 2.0) / max(8, min(yama.shape[:2])), 1.0)
        y = cv2.resize(yama, None, fx=ol, fy=ol, interpolation=cv2.INTER_LINEAR)
        return _harmanli_dose(y, h, w)
    ol = max(hedef / max(8, min(yama.shape[:2])), 0.5)
    y = cv2.resize(yama, None, fx=ol, fy=ol, interpolation=cv2.INTER_LINEAR)
    blok = np.vstack([np.hstack([y, y[:, ::-1]]),
                      np.hstack([y[::-1], y[::-1, ::-1]])])
    bh, bw = blok.shape[:2]
    return np.tile(blok, (h // bh + 2, w // bw + 2, 1))[:h, :w]


def doku_doldur(tuval, maske, yama, rng, kadraj=False):
    """maske==1 olan yerleri `yama` dokusunu döşeyerek boya."""
    h, w = tuval.shape[:2]
    tuval[maske > 0] = doku_tekrar(yama, h, w, rng, kadraj)[maske > 0]


def zemin_izgarasi_ciz(tuval, x0, y0, x1, y1):
    """Arena icine fiziksel olarak kare, ince koyu zemin izgarasi ciz."""
    adim = max(1, int(round(IZGARA_ADIM_M * TUVAL / HTAB_M)))
    katman = tuval.copy()
    x0, y0 = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))
    for x in range(x0, x1 + 1, adim):
        cv2.line(katman, (x, y0), (x, y1), IZGARA_RENK, 1, cv2.LINE_AA)
    for y in range(y0, y1 + 1, adim):
        cv2.line(katman, (x0, y), (x1, y), IZGARA_RENK, 1, cv2.LINE_AA)
    bolge = np.zeros(tuval.shape[:2], np.uint8)
    cv2.rectangle(bolge, (x0, y0), (x1, y1), 1, -1)
    harman = cv2.addWeighted(tuval, 1.0 - IZGARA_OPAKLIK,
                             katman, IZGARA_OPAKLIK, 0)
    tuval[bolge > 0] = harman[bolge > 0]


def iha_ib_ciz(tuval, rng):
    """30x30 m MAVI parasutle inis alanini ISARETLE (SS2.1).

    Bu bir ISARETTIR, engel DEGILDIR: altindaki zemin surulebilir kalir ve
    kimlik haritasina DOKUNULMAZ (HB ve izgara ile ayni muamele). Bu yuzden
    duz boya degil YARI SAYDAM tint uygulanir — zemin dokusu, golgesi ve
    mikro yapisi korunur; aksi halde arenanin %36'sinda doku SILINIRDI.

    ⚠ T67 ETKILESIMI: ince bariyer dedektoru `LAB a* > 25` arar. MAVI'nin a*
    degeri NEGATIFTIR, dolayisiyla bu bolge engel sayilmaz. T71 ciktisi
    uzerinde AYRICA olculur.
    """
    kenar_px = max(4, int(round(IHA_IB_KENAR_M * TUVAL / HTAB_M)))
    x0 = int(rng.uniform(0, max(1, TUVAL - kenar_px)))
    y0 = int(rng.uniform(0, max(1, TUVAL - kenar_px)))
    ton = IHA_IB_MAVILERI[int(rng.random() * len(IHA_IB_MAVILERI))]
    saydam = rng.uniform(0.22, 0.45)
    x1, y1 = x0 + kenar_px, y0 + kenar_px
    roi = tuval[y0:y1, x0:x1]
    if roi.size:
        kat = np.full(roi.shape, ton, np.uint8)
        tuval[y0:y1, x0:x1] = cv2.addWeighted(roi, 1.0 - saydam, kat, saydam, 0)
    cv2.rectangle(tuval, (x0, y0), (x1 - 1, y1 - 1), ton,
                  max(2, int(round(kenar_px * 0.012))), cv2.LINE_AA)
    return (x0, y0, kenar_px, kenar_px)


def arena_disi_zemini_yenile(tuval, kenar, ust, alt, zemin_dosemesi):
    """Serit dolgularinin tasan dosemesini arena disinda zeminle geri kur."""
    arena = np.zeros(tuval.shape[:2], np.uint8)
    cv2.rectangle(arena, (int(round(kenar)), int(round(ust))),
                  (int(round(TUVAL - kenar)), int(round(alt))), 1, -1)
    dis = (arena == 0).astype(np.uint8)
    tuval[dis > 0] = zemin_dosemesi[dis > 0]


def seritli_bariyer_ciz(tuval, x0, x1, y, kalinlik, beyazla_basla,
                        aci_derece=0.0):
    """Figurdeki uzun-ince kirmizi/beyaz yol bariyerini RNG'siz ciz.

    `aci_derece` kolun YATAYA gore egimidir (T185 · D-324). Uc noktalari
    x = x0 ve x = x1'de KALIR; yalnizca y'leri ayrisir. Boylece kol seridi
    YATAYDA hala UCTAN UCA kapatir — egim koridoru acmaz, yalnizca kolu
    egik gosterir.

    ⚠ `aci_derece = 0.0` OZGUN yolu BIREBIR korur (ayni piksel, ayni parca
    sinirlari): mevcut kabul kumesi `sentetik_arena_kadraj_t66` bu ciktiya
    baglidir ve DONDURULMUSTUR.
    """
    x0, x1 = sorted((int(round(x0)), int(round(x1))))
    y = int(round(y))
    kalinlik = max(2, int(round(kalinlik)))
    parca = max(kalinlik * 3, 1)
    sira = 1 if beyazla_basla else 0

    if float(aci_derece) == 0.0:                 # OZGUN YOL — degistirilmedi
        cv2.line(tuval, (x0, y), (x1, y), (35, 35, 35), kalinlik + 2,
                 cv2.LINE_AA)
        for j, bas in enumerate(range(x0, x1 + 1, parca)):
            son = min(x1, bas + parca)
            renk = BARIYER_BEYAZ if (j + sira) % 2 else BARIYER_KIRMIZI
            cv2.line(tuval, (bas, y), (son, y), renk, kalinlik, cv2.LINE_AA)
        return

    yari = (x1 - x0) / 2.0
    dy = yari * math.tan(math.radians(float(aci_derece)))
    p0 = (x0, int(round(y - dy)))
    p1 = (x1, int(round(y + dy)))
    cv2.line(tuval, p0, p1, (35, 35, 35), kalinlik + 2, cv2.LINE_AA)
    uzunluk = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n_parca = max(1, int(math.ceil(uzunluk / parca)))
    for j in range(n_parca):
        t0, t1 = j / n_parca, min(1.0, (j + 1) / n_parca)
        a = (int(round(p0[0] + (p1[0] - p0[0]) * t0)),
             int(round(p0[1] + (p1[1] - p0[1]) * t0)))
        b = (int(round(p0[0] + (p1[0] - p0[0]) * t1)),
             int(round(p0[1] + (p1[1] - p0[1]) * t1)))
        renk = BARIYER_BEYAZ if (j + sira) % 2 else BARIYER_KIRMIZI
        cv2.line(tuval, a, b, renk, kalinlik, cv2.LINE_AA)


def hb_ciz(tuval, kutu, ped_rengi):
    """2x2 m HB: sartname METNINE gore uzerinde KIRMIZI H HARFI olan bolge.

    T71 (D-99): figur YAPAY ZEKA urunudur, artik METIN otoritedir. SS2.1:
    "2 metre x 2 metre boyutlarinda uzerinde KIRMIZI H harfi bulunacagi bir
    bolgedir." Iki eski varyant da metne uymuyordu:
      · T60 "figur" varyanti : SIYAH ped + BEYAZ H  -> H var ama KIRMIZI DEGIL
      · T56 "kirmizi branda"  : duz KIRMIZI dikdortgen -> kirmizi ama H YOK
    Dogrusu: ped uzerinde KIRMIZI H. Ped rengi sartnamede BELIRTILMEMISTIR,
    bu yuzden cesitlilik stratejisi geregi sahne basina degisir (tek palete
    yakinsamak D-95'te kirilganlik uretti).

    ⚠ T67 ETKILESIMI: ince bariyer dedektoru yuksek kromali UZUN-INCE yapiyi
    engel sayar. HB KAREDIR (en/boy 1,0) ve H harfinin bilesen kutusu da
    karedir; dedektor onu ELEMEZ. Bu `tests/test_ince_bariyer.py` ile
    kilitlidir ve T71 ciktisi uzerinde AYRICA olculur.
    """
    x0, y0, w, h = kutu
    roi = tuval[y0:y0 + h, x0:x0 + w].copy()
    x1, y1 = w - 1, h - 1
    cv2.rectangle(roi, (0, 0), (x1, y1), ped_rengi, -1)
    kal = max(1, int(round(min(w, h) * 0.09)))
    # KIRMIZI cerceve + KIRMIZI H — sartnamenin istedigi isaret
    cv2.rectangle(roi, (0, 0), (x1, y1), HB_KIRMIZI, kal, cv2.LINE_AA)
    olcek = max(0.3, min(w, h) / 42.0)
    (tw, th), _ = cv2.getTextSize("H", cv2.FONT_HERSHEY_SIMPLEX, olcek, kal)
    cv2.putText(roi, "H", ((w - tw) // 2, (h + th) // 2),
                cv2.FONT_HERSHEY_SIMPLEX, olcek, HB_KIRMIZI, kal, cv2.LINE_AA)
    tuval[y0:y0 + h, x0:x0 + w] = roi


def hb_karari(rng, kadraj):
    """HB varlik karari + PED RENGI. Iki kipte de ESIT iki RNG cekilisi.

    T71: eski ikinci cekilis "figur mu kirmizi branda mi" varyantiniydi.
    Varyant KALKTI (metin otoritedir, HB her zaman KIRMIZI H tasir); ayni
    cekilis artik PED RENGINI seciyor. Cekilis SAYISI degismedi.
    """
    celdirici_var = rng.random() < 0.55
    ped = HB_PED_RENKLERI[int(rng.random() * len(HB_PED_RENKLERI))]
    return (kadraj or celdirici_var), ped


def hedef_kutusu_bul(kimlik, gecilebilir_kimlikler, ust, merkezler=None):
    """2 m pedi TAMAMI mevcut class-0 bolgesindeyken ust ucta yerlestir."""
    kenar = max(1, int(round(HEDEF_KENAR_M * TUVAL / HTAB_M)))
    pay = int(round(kenar * 0.6))
    for indis, k in enumerate(gecilebilir_kimlikler):
        maske = kimlik == k
        ys, _ = np.nonzero(maske)
        if not len(ys):
            continue
        merkez_y = int(round(max(float(ys.min()), float(ust)) + pay + kenar / 2.0))
        merkez_y = min(max(merkez_y, kenar // 2), TUVAL - (kenar + 1) // 2)
        satirlar = np.flatnonzero(maske.any(axis=1))
        satir = int(satirlar[np.argmin(np.abs(satirlar - merkez_y))])
        xs = np.flatnonzero(maske[satir])
        if not len(xs):
            continue
        merkez_x = (float(xs.mean()) if merkezler is None
                    else float(merkezler[indis]))
        y0 = min(max(int(round(merkez_y - kenar / 2.0)), 0), TUVAL - kenar)
        beklenen_serit = serit_no(merkez_x * BOYUT / TUVAL, 0, BOYUT)
        adaylar = []
        for x0 in range(0, TUVAL - kenar + 1):
            hx = (x0 + kenar / 2.0) * BOYUT / TUVAL
            if serit_no(hx, 0, BOYUT) != beklenen_serit:
                continue
            if np.all(maske[y0:y0 + kenar, x0:x0 + kenar]):
                adaylar.append((abs((x0 + kenar / 2.0) - merkez_x), x0))
        if adaylar:
            _, x0 = min(adaylar)
            pad = np.zeros(kimlik.shape, np.uint8)
            cv2.rectangle(pad, (x0, y0), (x0 + kenar - 1, y0 + kenar - 1), 1, -1)
            return [x0, y0, kenar, kenar], pad, int(np.count_nonzero(pad))
    return None, None, 0


def moloz_adalari(serit_m, rng, ust, alt, kapat, gecit_orani=None):
    """Serit icine MOLOZ ADALARI yerlestir; blocked olacak maskeyi dondur.

    T66 · NEDEN: uretec kareyi bastan sona DIKEY SERITLERE boluyordu ve kapali
    seridin TAMAMI tek parca blocked oluyordu — duvar duvara bant. Sartname
    SS2.1 ise guzergahlari "moloz YIGINLARI ARASINDA olusturulmus uc yol"
    diye tanimlar: acik genis bir alan ve icine serpilmis ADALAR.

    ⚠ v16 DERSI KORUNUR (kod icinde yazili): ETIKETSIZ moloz modele "genis
    bolge = gecilebilir" onyargisi ogretmisti. Burada o risk YOKTUR — adalarin
    tamami blocked, aralarindaki zemin traversable etiketlenir.
    ⚠ IKINCI RISK, OLCUMLE YAKALANDI: ilk denememde adalar cok seyrekti ve
    traversable orani %24,4 -> %53,9'a firladi, blocked %30,1 -> %5,4'e dustu
    (trav/blok orani 0,8 -> 10,0). Bu, v16 kusurunun BASKA yoldan geri
    donmesiydi. Yogunluk `MOLOZ_ADA_YOGUNLUGU` ile T71 seviyesine ayarlandi.

    kapat=True  -> adalar seridi ENINE kapatan bir BANT olusturur (gecis yok)
    kapat=False -> adalar yalniz kenarlara serpilir, dusey gecit ACIK kalir
    gecit_orani -> "dar" seridi icin: bant icinde birakilan gecit genisligi
    """
    h, w = serit_m.shape
    ys, xs = np.nonzero(serit_m)
    if xs.size == 0:
        return np.zeros_like(serit_m)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    gen, yuk = max(1, x1 - x0), max(1, y1 - y0)
    ada = np.zeros_like(serit_m)

    def kume(cx, cy, r):
        """Tek bir moloz YIGINI: ust uste birkac elips (duz oval degil)."""
        for _ in range(rng.randint(3, 7)):
            ox = cx + rng.uniform(-r * 0.55, r * 0.55)
            oy = cy + rng.uniform(-r * 0.55, r * 0.55)
            eks = (max(3, int(r * rng.uniform(0.45, 0.95))),
                   max(3, int(r * rng.uniform(0.35, 0.80))))
            cv2.ellipse(ada, (int(ox), int(oy)), eks,
                        rng.uniform(0, 180), 0, 360, 1, -1)

    if kapat:
        # ENINE KAPATAN BANT — seridi bir Y araliginda tamamen keser.
        by = rng.uniform(y0 + yuk * 0.20, y1 - yuk * 0.20)
        kal = yuk * rng.uniform(0.20, 0.36)
        n = max(5, int(gen / (gen * rng.uniform(0.11, 0.17))))
        gecit_x = gecit_yari = None
        if gecit_orani:
            gecit_x = rng.uniform(x0 + gen * 0.22, x1 - gen * 0.22)
            gecit_yari = gen * gecit_orani * 0.5
        for i in range(n + 1):
            cx = x0 + gen * i / n
            if gecit_x is not None and abs(cx - gecit_x) < gecit_yari:
                continue
            kume(cx, by + rng.uniform(-kal * 0.35, kal * 0.35), kal * 0.62)
        # bandin disinda da YIGINLAR: arena molozla doludur
        for _ in range(rng.randint(8, 15)):
            kume(rng.uniform(x0, x1), rng.uniform(y0, y1),
                 gen * rng.uniform(0.18, 0.38))
    else:
        # ACIK SERIT: yiginlar KENARLARA yaslanir, ortada dusey gecit kalir.
        # T66 olcumu: ilk ayarda (0.15..0.26) kalan koridor cok darlasti ve
        # 260 karenin 50'si `DUSUK_GUVEN` ile cekimser kaldi (darbogaz < 4,5 px).
        # Gecit genisletildi; adalar hala kenarlari tutuyor.
        gecit_yari = gen * rng.uniform(0.24, 0.36)
        merkez_x = (x0 + x1) / 2.0 + rng.uniform(-gen * 0.12, gen * 0.12)
        for _ in range(rng.randint(8, 14)):
            sol = rng.random() < 0.5
            cx = (rng.uniform(x0 - gen * 0.05, merkez_x - gecit_yari) if sol
                  else rng.uniform(merkez_x + gecit_yari, x1 + gen * 0.05))
            kume(cx, rng.uniform(y0, y1), gen * rng.uniform(0.17, 0.36))
        # gecidi acik tut: koridor seridini maskeden CIKAR
        cv2.rectangle(ada, (int(merkez_x - gecit_yari), y0 - 2),
                      (int(merkez_x + gecit_yari), y1 + 2), 0, -1)

    return cv2.bitwise_and(ada, serit_m)


def moloz_yigini(tuval, kimlik, rng, banka, cx, cy, yaricap, parca=True, isik=None,
                 sinir=None):
    """Düzensiz moloz yığını: elips birleşimi blob + GERÇEK moloz dokusu.

    Tek tek bina kesiti yapıştırmak yıkık ŞEHİR görüntüsü veriyordu; arena
    enkazı ise ayrık, düzensiz YIĞINLARdır. Kenarlar yumuşatılır (sert kesim
    izi modele sahte ipucu vermesin).
    """
    # SADECE yığının kendi kutusunda çalış — tüm tuvali float'a çevirmek
    # sahne başına 20-30 kez tekrarlanıyordu ve üretimi 7 kat yavaşlatmıştı.
    H, W = tuval.shape[:2]
    pay = int(yaricap * 2.2) + 8
    x1, y1 = max(0, int(cx) - pay), max(0, int(cy) - pay)
    x2, y2 = min(W, int(cx) + pay), min(H, int(cy) + pay)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return
    rh, rw = y2 - y1, x2 - x1
    lcx, lcy = cx - x1, cy - y1

    m = np.zeros((rh, rw), np.uint8)
    for _ in range(rng.randint(3, 8)):
        ex = int(lcx + rng.gauss(0, yaricap * 0.45))
        ey = int(lcy + rng.gauss(0, yaricap * 0.45))
        eks = (max(4, int(yaricap * rng.uniform(0.30, 0.95))),
               max(4, int(yaricap * rng.uniform(0.30, 0.95))))
        cv2.ellipse(m, (ex, ey), eks, rng.uniform(0, 180), 0, 360, 255, -1)
    m = cv2.GaussianBlur(m, (0, 0), max(1.0, yaricap * 0.07))
    if sinir is not None:
        # Yığın ŞERİDİ AŞMASIN: taşan moloz komşu AÇIK şeride düşerse orada
        # "traversable" etiketi taşır — v16'yı bozan zehrin aynısı.
        m = (m * sinir[y1:y2, x1:x2]).astype(np.uint8)
    if not m.any():
        return

    roi = tuval[y1:y2, x1:x2]
    # T71: banka artik HAM tutuluyor (sahne basina boyanmak icin). Boyama
    # BURADA yapilir; atlanirsa ham RescueNet dokusu (mavi gokyuzu, beyaz
    # bulut, renkli cati) dogrudan basilir — D-78/T60'in cozdugu kusur geri
    # doner. Ilk denememde tam bu oldu ve GORSELDE yakalandi (D-80: gorsel kazanir).
    doku = lab_ortalamasini_tasi(
        banka["enkaz_doku"][rng.randrange(len(banka["enkaz_doku"]))],
        _SAHNE_MOLOZ_HEDEFI, MOLOZ_KROMA_KORUMA)
    doku = doku_tekrar(doku, rh, rw, rng)
    a = (m.astype(np.float32) / 255.0)[..., None]

    if isik is not None:            # yığının kendi gölgesi
        ga = np.roll(m, (int(yaricap * isik[1]), int(yaricap * isik[0])), (0, 1))
        ga = cv2.GaussianBlur(ga, (0, 0), max(1.0, yaricap * 0.15))
        ga = (ga.astype(np.float32) / 255.0 * rng.uniform(0.20, 0.45))[..., None]
        roi[:] = (roi.astype(np.float32) * (1 - ga)).astype(np.uint8)

    roi[:] = (roi.astype(np.float32) * (1 - a) + doku.astype(np.float32) * a
              ).astype(np.uint8)

    if parca:                       # tepesine birkaç iri parça → kabartı hissi
        for _ in range(rng.randint(1, 5)):
            g = oku(rng.choice(banka["enkaz"]), True, rng)
            if g is None:
                continue
            yapistir(tuval, kimlik, g,
                     cx + rng.gauss(0, yaricap * 0.6), cy + rng.gauss(0, yaricap * 0.6),
                     rng.uniform(0.25, 0.7), rng.uniform(0, 360), rng, isik=isik,
                     sinir=sinir)


def yapistir(tuval, kimlik, rgba, mx, my, olcek, aci, rng, kimlik_no=None, isik=None,
             sinir=None):
    """RGBA kesiti (mx,my) merkezine ölçekleyip döndürerek yapıştır.

    isik = (dx, dy) oranı verilirse GÖLGE düşürülür ve alfa kenarı yumuşatılır.
    NEDEN: kes-yapıştır sentezinin en bilinen kusuru, nesnelerin gölgesiz ve
    keskin kenarlı olması ("havada duran nesne"). Model bu artefaktı kestirme
    ipucu olarak öğrenir ve gerçek görüntüye transfer olmaz. Gölge yönü sahne
    boyunca SABİTtir — tutarsız gölge de aynı derecede ele verir.
    """
    h0, w0 = rgba.shape[:2]
    yw, yh = max(8, int(w0 * olcek)), max(8, int(h0 * olcek))
    y = cv2.resize(rgba, (yw, yh), interpolation=cv2.INTER_LINEAR)
    M = cv2.getRotationMatrix2D((yw / 2, yh / 2), aci, 1.0)
    kos = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(yh * kos[1] + yw * kos[0]), int(yh * kos[0] + yw * kos[1])
    M[0, 2] += nw / 2 - yw / 2
    M[1, 2] += nh / 2 - yh / 2
    y = cv2.warpAffine(y, M, (nw, nh), flags=cv2.INTER_LINEAR,
                       borderValue=(0, 0, 0, 0))

    H, W = tuval.shape[:2]
    x1, y1 = int(mx - nw / 2), int(my - nh / 2)
    x2, y2 = x1 + nw, y1 + nh
    kx1, ky1 = max(0, x1), max(0, y1)
    kx2, ky2 = min(W, x2), min(H, y2)
    if kx2 <= kx1 or ky2 <= ky1:
        return
    kes = y[ky1 - y1:ky2 - y1, kx1 - x1:kx2 - x1]
    a = (kes[:, :, 3:4].astype(np.float32) / 255.0)
    # kenar yumuşatma: sert alfa kesimi sentetik olduğunu ele verir
    a = cv2.GaussianBlur(a, (0, 0), rng.uniform(0.6, 2.2))[..., None]
    if sinir is not None:            # verilen bölgenin dışına taşma
        a = a * sinir[ky1:ky2, kx1:kx2, None]
        if a.max() <= 0:
            return

    if isik is not None:
        gx, gy = int(nw * isik[0]), int(nh * isik[1])
        sx1, sy1 = kx1 + gx, ky1 + gy
        sx2, sy2 = kx2 + gx, ky2 + gy
        cx1, cy1 = max(0, sx1), max(0, sy1)
        cx2, cy2 = min(W, sx2), min(H, sy2)
        if cx2 > cx1 and cy2 > cy1:
            ga = a[cy1 - sy1:cy2 - sy1, cx1 - sx1:cx2 - sx1]
            ga = cv2.GaussianBlur(ga, (0, 0), max(1.0, min(nw, nh) * 0.06))[..., None]
            ga = ga * rng.uniform(0.25, 0.5)
            g = tuval[cy1:cy2, cx1:cx2].astype(np.float32)
            tuval[cy1:cy2, cx1:cx2] = (g * (1 - ga)).astype(np.uint8)

    bolge = tuval[ky1:ky2, kx1:kx2].astype(np.float32)
    tuval[ky1:ky2, kx1:kx2] = (bolge * (1 - a) + kes[:, :, :3] * a).astype(np.uint8)
    if kimlik_no is not None:
        kimlik[ky1:ky2, kx1:kx2][a[:, :, 0] > 0.5] = kimlik_no


# ---------------------------------------------------------------- sahne
def _karar_seridi(x_tuval, tuval, boyut):
    """TUVAL x koordinatini SON GORUNTUDEKI karar seridine (1/2/3) cevir.

    Serit sinirlarini kendimiz UCE BOLMEYIZ — otorite `karar_sozlesmesi.serit_no`.
    Son goruntu kare (boyut x boyut) oldugu icin icerik kutusu (0,0,boyut,boyut).
    """
    x_son = float(x_tuval) * float(boyut) / float(tuval)
    return int(serit_no(x_son, 0, boyut))


def _manifest_kaydi(bilgi, ad, bolum, tohum):
    """Bir karenin manifest kaydi — `data/arena_kompozit` alan adlariyla."""
    tuval, boyut = bilgi["tuval"], bilgi["boyut"]
    olcek = float(boyut) / float(tuval)

    def kutu_son(k):
        return None if k is None else [round(v * olcek, 2) for v in k]

    seritler = []
    acik_kararlar, bariyerler = set(), []
    for s in bilgi["seritler"]:
        kd = (_karar_seridi(s["gecilebilir_merkez_x"], tuval, boyut)
              if s["gecilebilir_merkez_x"] is not None else None)
        kayit = {
            "indis": s["indis"], "durum": s["durum"],
            "gecilebilir": s["gecilebilir"],
            "serit_kutusu": kutu_son(s["serit_kutusu"]),
            "gecilebilir_kutu": kutu_son(s["gecilebilir_kutu"]),
            "karar_seridi": kd,
            "merkez_cizgisi_sapma_px": (
                None if s.get("merkez_cizgisi_sapma_px") is None
                else round(s["merkez_cizgisi_sapma_px"] * olcek, 4)),
        }
        seritler.append(kayit)
        if s["gecilebilir"] and kd is not None:
            acik_kararlar.add(kd)
        else:
            bariyerler.append({
                "serit": _karar_seridi(
                    (s["serit_kutusu"][0] + s["serit_kutusu"][2] / 2.0)
                    if s["serit_kutusu"] else 0.0, tuval, boyut),
                "kutu": kutu_son(s["serit_kutusu"]),
                "pencere": kutu_son(s["serit_kutusu"]),
                "uretec_indisi": s["indis"],
            })

    tek = len(acik_kararlar) == 1
    acik = next(iter(acik_kararlar)) if tek else None
    hedef_serit = None
    if bilgi.get("hedef_kutusu"):
        hx = bilgi["hedef_kutusu"][0] + bilgi["hedef_kutusu"][2] / 2.0
        adaylar = [s["karar_seridi"] for s in seritler
                   if s["gecilebilir"] and s["karar_seridi"] is not None
                   and s["gecilebilir_kutu"] is not None
                   and s["gecilebilir_kutu"][0] <= hx * olcek
                   <= s["gecilebilir_kutu"][0] + s["gecilebilir_kutu"][2]]
        hedef_serit = adaylar[0] if adaylar else _karar_seridi(hx, tuval, boyut)
    return {
        "kaynak": None,
        "cikti": f"images/{bolum}/{ad}.jpg",
        "bolum": bolum,
        "durum": "YAZILDI",
        "arena": {
            "hedef_kutu": kutu_son(bilgi.get("hedef_kutusu")),
            "hedef_serit": hedef_serit,
            "hedef_kenar_m": bilgi.get("hedef_kenar_m"),
            "iha_ib_kutu": bilgi.get("iha_ib_kutu"),
            "iha_ib_kenar_m": bilgi.get("iha_ib_kenar_m"),
            "lab_zemin_hedefi": bilgi.get("lab_zemin_hedefi"),
            "lab_moloz_hedefi": bilgi.get("lab_moloz_hedefi"),
            "hedef_varyanti": bilgi.get("hedef_varyanti"),
            "hedef_onceki_gecilebilir_temas_px":
                bilgi.get("hedef_onceki_gecilebilir_temas_px", 0),
            "hedef_pad_alani_px": bilgi.get("hedef_pad_alani_px", 0),
            "acik_serit": acik,
            "kapali_seritler": ([k for k in (1, 2, 3) if k != acik] if tek
                                else sorted({1, 2, 3} - acik_kararlar)),
            "acik_serit_adaylari": sorted(acik_kararlar),
            "belirsiz": not tek,
            "bariyerler": bariyerler,
            "icerik": [0, 0, boyut, boyut],
            "mpp": HTAB_M / float(boyut),
            "olcek_kaynagi": KADRAJ_OLCEK_KAYNAGI,
            "beklenen_durum": "ACIK" if tek else "BELIRSIZ",
            "beklenti_kaynagi": "uretec_serit_durumu",
            "tohum": tohum,
            "arena_x_araligi": [round(bilgi["kenar_x"] * olcek, 2),
                                round((tuval - bilgi["kenar_x"]) * olcek, 2)],
            "uretec_seritleri": seritler,
        },
    }


def _kutu(poly):
    """Poligonun TUVAL koordinatlarindaki sinirlayici kutusu [x, y, w, h]."""
    if poly is None or len(poly) == 0:
        return None
    a = np.asarray(poly, dtype=np.float64)
    x0, y0 = float(a[:, 0].min()), float(a[:, 1].min())
    x1, y1 = float(a[:, 0].max()), float(a[:, 1].max())
    return [x0, y0, x1 - x0, y1 - y0]


def _serit_kaydi(i, durum, serit_poly, gecilebilir_poly):
    """Bir uretec seridinin manifest kaydi (TUVAL koordinatlarinda).

    `gecilebilir_poly` yalniz serit gecilebilirse (acik / dar) doludur;
    "kapali" seritte None'dir. Karar yolunun 1/2/3 serit numarasina cevirme
    isi `main`'de, son goruntu olceginde yapilir.
    """
    kutu = _kutu(serit_poly)
    g_kutu = _kutu(gecilebilir_poly)
    merkez_x = None
    sapma = None
    if gecilebilir_poly is not None and len(gecilebilir_poly):
        p = np.asarray(gecilebilir_poly, dtype=np.float64)
        merkez_x = float(p[:, 0].mean())
        n = len(p) // 2
        if n and len(p) == 2 * n:
            merkez = (p[:n, 0] + p[n:, 0][::-1]) / 2.0
            sapma = float(np.max(np.abs(merkez - merkez.mean())))
    return {
        "indis": int(i),
        "durum": str(durum),
        "gecilebilir": durum in ("acik", "dar", "kismi"),
        "serit_kutusu": kutu,
        "gecilebilir_kutu": g_kutu,
        "gecilebilir_merkez_x": merkez_x,
        "merkez_cizgisi_sapma_px": sapma,
    }


def sahne_uret(rng, banka, ayni_malzeme=0.45, dar_orani=0.28, kadraj=False,
               bilgi=None, bariyer_acisi=0.0):
    """Bir sentetik arena üret. -> (görüntü BGR, kimlik haritası, {kimlik: sınıf})"""
    tuval = np.zeros((TUVAL, TUVAL, 3), np.uint8)
    kimlik = np.zeros((TUVAL, TUVAL), np.int32)
    siniflar = {}
    sonraki = [1]
    # T71: bu sahnenin zemin/moloz LAB hedeflerini GENIS banttan cek. Tek
    # noktaya boyamak (T60) modeli o kunyeye BAGIMLI yapiyordu (D-95).
    _zemin_hedefi, _moloz_hedefi = sahne_renklerini_sec(rng)

    # sahne boyunca SABİT ışık yönü (tutarsız gölge sentetikliği ele verir)
    aci = rng.uniform(0, 2 * math.pi)
    guc = rng.uniform(0.05, 0.16)
    isik = (guc * math.cos(aci), guc * math.sin(aci))

    def yeni(c):
        k = sonraki[0]
        sonraki[0] += 1
        siniflar[k] = c
        return k

    # --- zemin + yol yüzeyi ---
    # Yol ile zemin AYIRT EDİLEBİLİR olmalı; ikisi de aynı griye düşerse
    # sahnede öğrenilecek sinyal kalmaz. Ortalama renk farkı zorlanır.
    zem_doku = yuzey_sec(rng, banka, "zemin")
    zem_ort = zem_doku.reshape(-1, 3).mean(0)
    yol_doku = yuzey_sec(rng, banka, "yol")
    for _ in range(10):
        if np.linalg.norm(yol_doku.reshape(-1, 3).mean(0) - zem_ort) > 30:
            break
        yol_doku = yuzey_sec(rng, banka, "yol")
    zemin_dosemesi = doku_tekrar(zem_doku, TUVAL, TUVAL, rng, kadraj)
    zemin_dosemesi = lab_ortalamasini_tasi(
        zemin_dosemesi, _SAHNE_ZEMIN_HEDEFI, ZEMIN_KROMA_KORUMA)
    tuval[:] = zemin_dosemesi

    # --- ŞERİTLER (arena modeli) ---
    # v16 DERSİ: önceki sürümde koridorlar ince bantlardı ve koridor DIŞINDAKİ
    # moloz ETİKETSİZ kalıyordu. Model molozun geçilemez olduğunu yalnız kapalı
    # koridorların içinde görüyordu; açık alanda duran yığın onun için tanımsızdı
    # ve "geniş bölge = geçilebilir" önyargısı kazandı → arenada molozun %31,6'sına
    # "geçilebilir" dedi (v15'te %2,7 idi).
    # DÜZELTME: arena duvarlarla ayrılmış ŞERİTLERdir ve şeritlerin TAMAMI
    # etiketlidir. Moloz her zaman blocked şeridin içindedir → ETİKETSİZ MOLOZ YOK.
    # ARENA ÖLÇEĞİ GENİŞ ARALIKTA RASTGELE: arena kareyi doldurmak zorunda değil,
    # İHA görüntüsünde çevresiyle birlikte görünür (gerçek arena görselinde de
    # öyle: kenarlıklı alan, çevresi boş zemin). Bu hem etiketli alan oranını
    # gerçek dağılıma yaklaştırır hem de modelin "büyük bölge = geçilebilir"
    # gibi SABİT bir ölçek önyargısı kurmasını engeller.
    n_ser = rng.choice([2, 3, 3, 3, 4, 5])
    kenar = TUVAL * rng.uniform(0.05, 0.32)
    if kadraj:
        # T51 KADRAJ KIPI: koridorlar icerik kutusunun UST ve ALT uclarina
        # ULASIR. Olculdu (24 kare): tam karede UC_BANT_TEMAS_YOK 21, rota
        # 3/24; arenaya kirpilinca 14/24 — kusur modelde degil, uretecin
        # YERLESIMINDE: dikey pay koridoru uc bantlardan kopariyordu.
        # EGITIM KIPI (kadraj=False) DEGISMEZ; pay ve donus cesitlilik icin
        # degerlidir, silinmedi.
        kenar_y = 0.0
    else:
        kenar_y = TUVAL * rng.uniform(0.0, 0.28)
    alt, ust = TUVAL - kenar_y, kenar_y
    alan = TUVAL - 2 * kenar
    sinirlar = [kenar + alan * i / n_ser for i in range(n_ser + 1)]
    duvar_kal = rng.uniform(5, 16)

    # Yarışma mantığı: şeritlerin ÇOĞU kapalıdır, geçit azdır ("hangi yol açık"
    # sorusu ancak öyle anlamlı olur). Bu dağılım aynı zamanda görüntü başına
    # traversable oranını gerçek RescueNet dağılımına (%8,5) yaklaştırır —
    # v16'da %16,8 ile iki katıydı ve model "geniş bölge = geçilebilir" öğrenmişti.
    # "dar": şeridin çoğu moloz, içinden dar bir iz geçiyor (2.png tipi)
    kalan = 1.0 - dar_orani
    if kadraj:
        # "kismi" serit TANIMI GEREGI kareyi bastan basa gecmez; kadraj
        # kipinde uc-bant temasini imkansiz kilar. Agirligi "acik"a devredilir.
        durumlar = [rng.choices(["kapali", "acik", "dar"],
                                [kalan * 0.583, kalan * 0.417, dar_orani])[0]
                    for _ in range(n_ser)]
    else:
        durumlar = [rng.choices(["kapali", "acik", "kismi", "dar"],
                                [kalan * 0.583, kalan * 0.222, kalan * 0.195,
                                 dar_orani])[0] for _ in range(n_ser)]
    if not any(d in ("acik", "kismi", "dar") for d in durumlar):
        durumlar[rng.randrange(n_ser)] = rng.choice(["acik", "dar"])
    if "acik" not in durumlar:
        # 2 m HB yalnız TAM açık şeritte durur. Yeni RNG çekilişi yapılmaz;
        # mevcut geçilebilir seçimlerden ilki açık olarak yorumlanır.
        aday = next(i for i, d in enumerate(durumlar)
                     if d in ("dar", "kismi"))
        durumlar[aday] = "acik"

    kapali_seritler = []          # (poligon, kırpma maskesi) — moloz buraya
    # T55: seridin AÇIK olup olmadığı YALNIZ burada bilinir. `class-0`'dan
    # türetilemez — üç şeritli arenada traversable ÜÇ koridoru da kaplar;
    # şeritleri ayıran zemin değil, üzerlerindeki BARİYERLERdir (D-70:
    # türetme denendi, %83,7 uyum çıktı ve hataların deseni ölçütün yanlış
    # olduğunu gösterdi). Bu yüzden durum ÜRETİM ANINDA kaydedilir.
    serit_kayitlari = [] if bilgi is not None else None
    gecilebilir_merkezler = []      # manifest/T56 geriye uyumu
    gecilebilir_kimlikler = []      # T60: 2 m HB gercek class-0'a baglanir
    hedef_kimlikler = []            # yalnız tam ACIK şeritler HB taşıyabilir
    hedef_merkezler = []
    for i, durum in enumerate(durumlar):
        merkez = (sinirlar[i] + sinirlar[i + 1]) / 2
        # T66: seritler BITISIK. Eskiden aralarinda `duvar_kal * 1.5` kadar
        # ETIKETSIZ bosluk kaliyordu ve zemin "dar dikey bantlar" gibi
        # gorunuyordu. Sartname SS2.1'e gore arena zemini GENIS ve BAGLANTILI
        # bir alandir; seritleri ayiran sey bosluk degil MOLOZ ADALARIDIR.
        gen = (sinirlar[i + 1] - sinirlar[i])
        if gen < 12:
            continue

        # Geçilebilir yüzey her zaman ZEMİNDEN AYIRT EDİLEBİLİR olmak zorunda
        # değil: arenada yol çoğu kez zeminle aynı malzemedendir, yalnız
        # üstünde engel yoktur. %45 olasılıkla aynı malzeme kullanılır.
        iz_doku = (zem_doku if rng.random() < ayni_malzeme
                   else arena_yuzeyi_renklendir(yol_doku))

        if durum == "dar":
            # T66: "dar" artik ADA BANDI + icinde birakilan GECIT. Eskiden
            # serit boyunca uzanan ince bir izdi (duvar duvara bant gorunumu).
            poly = serit(rng, merkez, gen, 0.0, 1.0, alt=alt, ust=ust,
                         duz=kadraj)
            iz = ic_serit(poly, rng.uniform(0.14, 0.38), rng.uniform(-0.8, 0.8))
            Lm = np.zeros((TUVAL, TUVAL), np.uint8)
            cv2.fillPoly(Lm, [poly.astype(np.int32)], 1)
            Bm = moloz_adalari(Lm, rng, ust, alt, kapat=True,
                               gecit_orani=rng.uniform(0.26, 0.44))
            Tm = cv2.bitwise_and(Lm, cv2.bitwise_not(Bm * 255) // 255)
            if int(Tm.sum()) < 600 or int(Bm.sum()) < 600:
                continue
            doku_doldur(tuval, Lm, iz_doku, rng, kadraj)   # tüm şerit aynı yüzey
            kimlik[Bm > 0] = yeni(1)                  # ADALAR = blocked
            gecilebilir_kimlik = yeni(0)
            kimlik[Tm > 0] = gecilebilir_kimlik       # adalar ARASI = traversable
            gecilebilir_kimlikler.append(gecilebilir_kimlik)
            kapali_seritler.append((poly, Bm))        # moloz yalnız ADALARA
            gecilebilir_merkezler.append(
                float(np.asarray(iz, dtype=np.float64)[:, 0].mean()))
            if serit_kayitlari is not None:
                serit_kayitlari.append(_serit_kaydi(i, durum, poly, iz))
            continue

        if durum == "kismi":
            kesim = rng.uniform(0.35, 0.7)
            dilimler = [(0.0, kesim, 0), (kesim, 1.0, 1)]
        else:
            dilimler = [(0.0, 1.0, 0 if durum == "acik" else 1)]

        gecilebilir_poly = None
        serit_poly = None
        for t0, t1, c in dilimler:
            poly = serit(rng, merkez, gen, t0, t1, alt=alt, ust=ust,
                         duz=kadraj)
            m = np.zeros((TUVAL, TUVAL), np.uint8)
            cv2.fillPoly(m, [poly.astype(np.int32)], 1)
            doku_doldur(tuval, m, iz_doku if c == 0 else zem_doku, rng, kadraj)
            # T66 · ADA GEOMETRISI: dilim tek parca boyanmaz. Kapali dilimde
            # adalar seridi ENINE KAPATIR (gecis yok); acik dilimde adalar
            # yalniz KENARLARA yaslanir ve dusey gecit acik kalir. Iki halde de
            # adalar blocked, aralari traversable etiketlenir — ETIKETSIZ
            # MOLOZ URETILMEZ (v16 dersi korunur).
            ada = moloz_adalari(m, rng, ust, alt, kapat=(c == 1))
            zem = cv2.bitwise_and(m, cv2.bitwise_not(ada * 255) // 255)
            if int(zem.sum()) < 600:
                ada = np.zeros_like(m)
                zem = m
            k_zem = yeni(0)
            kimlik[zem > 0] = k_zem
            if int(ada.sum()) >= 400:
                kimlik[ada > 0] = yeni(1)
                kapali_seritler.append((poly, ada))
            if serit_poly is None:
                serit_poly = poly
            if c == 0 and gecilebilir_poly is None:
                gecilebilir_poly = poly
                gecilebilir_kimlikler.append(k_zem)
                if durum == "acik":
                    hedef_kimlikler.append(k_zem)
                    hedef_merkezler.append(float(np.asarray(poly)[:, 0].mean()))
        if gecilebilir_poly is not None:
            gecilebilir_merkezler.append(
                float(np.asarray(gecilebilir_poly, dtype=np.float64)[:, 0].mean()))
        if serit_kayitlari is not None:
            serit_kayitlari.append(
                _serit_kaydi(i, durum, serit_poly, gecilebilir_poly))

    # `doku_tekrar` tum tuvali uretir; serit maskesi arena disina tasmiyor ama
    # harmanli doseme hesaplamasi dis zemini dolayli etkileyebiliyordu. D-87
    # renk kapisi icin arena disini secilen ZEMIN dokusuyla acikca geri kur.
    arena_disi_zemini_yenile(tuval, kenar, ust, alt, zemin_dosemesi)

    # T60: kareli zemin figurdedir; yalniz arena icine, nesnelerden ONCE cizilir.
    zemin_izgarasi_ciz(tuval, kenar, ust, TUVAL - kenar, alt)

    # T71 · SS2.1: 30x30 m MAVI IHA-IB. Izgaradan SONRA, nesnelerden ONCE —
    # yerdeki bir isarettir; moloz ve HB onun USTUNE biner.
    iha_ib_kutusu = iha_ib_ciz(tuval, rng)

    # --- duvarlar: şerit sınırlarında (arena yapısı) ---
    for x in sinirlar:
        if rng.random() < 0.85:
            y0 = rng.uniform(ust, ust + (alt - ust) * 0.25) if rng.random() < 0.3 else ust
            y1 = rng.uniform(ust + (alt - ust) * 0.75, alt) if rng.random() < 0.3 else alt
            renk = rng.choice([(180, 180, 180), (150, 155, 160), (200, 200, 210)])
            cv2.line(tuval, (int(x), int(y0)), (int(x), int(y1)), renk, int(duvar_kal))
    # Ara bariyer RNG cekilisleri burada AYNI sirayla tuketilir. Cizim molozdan
    # sonra yapilir; ham serit indisi yalniz TAM KAPALI seritlere eslenir.
    # ── T68 (T66 ile birlesik): BARIYER ARTIK ACIK KORIDORU DA KAPATIR ──────
    # ESKIDEN (D-93 olctu): bariyer YALNIZ `kapali_indisler`e konuyordu, yani
    # zaten molozla dolu seritlere. Acik zemin ustundeki bariyer orani %0,0 idi
    # ve model "acik gorunen zeminde bariyer" ornegini HIC gormuyordu — bu
    # yuzden ogrenemiyordu da. Ada geometrisiyle (T66) koridorlar artik gercek
    # gecitlerdir; bariyer onlari ANLAMLI bicimde kapatabilir.
    #
    # UC KURAL:
    #  1. Hedef once GECILEBILIR seritlerden secilir (acik/dar) — asil vaka.
    #  2. EN AZ BIR gecilebilir serit ACIK BIRAKILIR; aksi halde sahnenin
    #     cozumu olmaz ve kadraj kapilari (rota 260/260) coker.
    #  3. Bariyerin KENDI pikselleri `blocked` etiketlenir (altindaki zemin
    #     DEGIL) ve serit kaydinin `gecilebilir` alani False'a cevrilir —
    #     yoksa manifest `acik_serit` YALAN SOYLER.
    gecilebilir_indisler = [i for i, d in enumerate(durumlar)
                            if d in ("acik", "dar", "kismi")]
    kapali_indisler = [i for i, d in enumerate(durumlar) if d == "kapali"]
    # en az biri acik kalmali: kapatilabilecek havuz = gecilebilir - 1
    # Korunacak serit: mumkunse bir "acik" serit. Ilk denemede korunan serit
    # cogu kez "dar" oluyordu ve bariyer genis olani kapatinca sahnede yalniz
    # cok dar bir gecit kaliyordu -> 260 karenin 50'si DUSUK_GUVEN.
    _acik_idx = [i for i in gecilebilir_indisler if durumlar[i] == "acik"]
    _korunan = _acik_idx[0] if _acik_idx else (
        gecilebilir_indisler[0] if gecilebilir_indisler else None)
    kapatilabilir = [i for i in gecilebilir_indisler if i != _korunan]
    bariyer_tarifleri = []
    bariyer_kapattigi = []
    for _ in range(rng.randint(0, 3)):
        ham_i = rng.randrange(n_ser)
        y = rng.uniform(ust + (alt - ust) * 0.2, ust + (alt - ust) * 0.8)
        faz = rng.choice([(210, 210, 215), (60, 60, 200)])
        kalinlik = rng.uniform(4, 11)
        havuz = kapatilabilir if kapatilabilir else kapali_indisler
        if havuz:
            i = havuz[ham_i % len(havuz)]
            # T185 (D-324): bariyer kolunun YATAYA gore egimi. `bariyer_acisi`
            # 0 iken `rng` HIC TUKETILMEZ — RNG akisi ve dolayisiyla mevcut
            # kabul kumesi `sentetik_arena_kadraj_t66` BIREBIR korunur.
            aci_b = (rng.uniform(-bariyer_acisi, bariyer_acisi)
                     if bariyer_acisi > 0.0 else 0.0)
            bariyer_tarifleri.append((sinirlar[i], sinirlar[i + 1], y,
                                       kalinlik, faz[0] > 100, aci_b))
            if i in kapatilabilir:
                bariyer_kapattigi.append(i)
                if i in kapatilabilir:
                    kapatilabilir = [j for j in kapatilabilir if j != i]
    # arena dış çerçevesi (gerçek arenada belirgin bir sınır vardır)
    if rng.random() < 0.5:
        cv2.rectangle(tuval, (int(kenar), int(ust)), (int(TUVAL - kenar), int(alt)),
                      rng.choice([(60, 190, 230), (200, 200, 200), (70, 70, 70)]),
                      int(rng.uniform(5, 18)))

    # --- KAPALI bölgeleri MOLOZLA DOLDUR (etiket zaten blocked) ---
    for poly, serit_m in kapali_seritler:
        # serit_m: moloz buraya KIRPILIR — komşu açık şeride VE dar izin
        # üstüne sızamaz. Sızsaydı orada "traversable" etiketi taşırdı.
        n = len(poly) // 2
        adim = max(1, int(n / rng.uniform(6, 14)))
        for i in range(0, n, adim):
            sol_p, sag_p = poly[i], poly[len(poly) - 1 - i]
            mx, my = (sol_p + sag_p) / 2
            gen = float(np.linalg.norm(sag_p - sol_p))
            moloz_yigini(tuval, kimlik, rng, banka,
                         mx + rng.gauss(0, gen * 0.10), my + rng.gauss(0, gen * 0.10),
                         gen * rng.uniform(0.30, 0.55), isik=isik, sinir=serit_m)

    # T68: bariyerin KENDI pikselleri `blocked` etiketlenir. Altindaki zemin
    # DEGISTIRILMEZ — bariyer yukseltilmis ince bir yapidir, zemin gorunur
    # kalir; ama IKA oradan GECEMEZ. Etiket bariyerin kapladigi seride yazilir.
    for x0b, x1b, yb, kalb, fazb, acib in bariyer_tarifleri:
        onceki = tuval.copy()
        seritli_bariyer_ciz(tuval, x0b, x1b, yb, kalb, fazb,
                            aci_derece=acib)
        degisen = (np.abs(tuval.astype(np.int16)
                          - onceki.astype(np.int16)).sum(axis=2) > 12)
        if int(degisen.sum()) >= 200:
            kimlik[degisen] = yeni(1)

    # T68: kapatilan seritlerin kaydi DUZELTILIR; yoksa manifest `acik_serit`
    # bariyerle kapanmis bir seridi hala ACIK gosterir (yer gercegi YALAN olur).
    if serit_kayitlari is not None and bariyer_kapattigi:
        for kayit in serit_kayitlari:
            if kayit["indis"] in bariyer_kapattigi:
                kayit["gecilebilir"] = False
                kayit["durum"] = f"{kayit['durum']}+bariyer"

    # --- arena DIŞI (kenar payı): düz zemin, etiketsiz, moloz YOK ---
    # Burada moloz olsaydı yine etiketsiz moloz üretmiş olurduk — v16 hatası.

    # --- HEDEF ---
    hedef_kutusu = None
    hedef_temas_px = 0
    hedef_pad_alani_px = 0
    hedef_varyanti = None
    # RNG AKISI KORUNUR: celdirici cekilisi HER IKI kipte de tuketilir. Aksi
    # halde kadraj kipinde akis kayiyor ve ayni tohum+indis iki kipte FARKLI
    # sahne uretiyordu — iki kumeyi kare kare karsilastirmak imkansizlasiyordu.
    _hb_var, _hb_ped_rengi = hb_karari(rng, kadraj)
    if _hb_var:
        kutu, pad, hedef_temas_px = hedef_kutusu_bul(
            kimlik, hedef_kimlikler, ust, hedef_merkezler)
        if kutu is not None:
            # HB gecilebilir zeminin USTUNDEDIR. Yerlesimden once pedin tamami
            # class-0 oldugu icin kimlik haritasi degistirilmez; engeli zemine
            # cevirerek veya yeni etiket basarak kanit uretmeyiz.
            hb_ciz(tuval, kutu, _hb_ped_rengi)
            hedef_kutusu = kutu
            hedef_pad_alani_px = int(np.count_nonzero(pad))
            # T71: tek varyant kaldi — sartname METNI (SS2.1) "uzerinde KIRMIZI
            # H harfi". Degisken olan yalniz PED RENGIDIR, isaret degil.
            hedef_varyanti = "metin_kirmizi_H"

    if bilgi is not None:
        bilgi.update({
            "tuval": TUVAL,
            "boyut": BOYUT,
            "n_serit": int(n_ser),
            "kenar_x": float(kenar),
            "kenar_y": float(kenar_y),
            "duvar_kalinligi": float(duvar_kal),
            "serit_sinirlari": [float(s) for s in sinirlar],
            "seritler": serit_kayitlari or [],
            "hedef_kutusu": hedef_kutusu,
            "hedef_kenar_m": HEDEF_KENAR_M if hedef_kutusu else None,
            "iha_ib_kutu": [float(v) for v in iha_ib_kutusu],
            "iha_ib_kenar_m": IHA_IB_KENAR_M,
            "lab_zemin_hedefi": [round(float(v), 2) for v in _zemin_hedefi],
            "lab_moloz_hedefi": [round(float(v), 2) for v in _moloz_hedefi],
            "hedef_varyanti": hedef_varyanti,
            "hedef_onceki_gecilebilir_temas_px": int(hedef_temas_px),
            "hedef_pad_alani_px": int(hedef_pad_alani_px),
        })
    return tuval, kimlik, siniflar


# ---------------------------------------------------------------- bozunumlar
def geometrik(rng, im, kimlik, kadraj=False):
    """Aynı dönüşümü görüntüye VE kimlik haritasına uygula (etiket bozulmaz).

    T51: `kadraj=True` iken donus ve perspektif UYGULANMAZ — ikisi de
    koridorun uclarini kadrajin disina tasiyip uc-bant temasini bozuyordu.
    Egitim kipinde (varsayilan) davranis AYNEN korunur.
    """
    if kadraj:
        return im, kimlik
    h, w = im.shape[:2]
    aci = rng.uniform(-25, 25)
    ol = rng.uniform(0.88, 1.12)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), aci, ol)
    M = np.vstack([M, [0, 0, 1]])
    # hafif perspektif (İHA eğimi)
    d = rng.uniform(0, 0.055) * w
    kaynak = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    hedef = kaynak + np.float32([[rng.uniform(-d, d), rng.uniform(-d, d)] for _ in range(4)])
    P = cv2.getPerspectiveTransform(kaynak, hedef) @ M
    im = cv2.warpPerspective(im, P, (w, h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_REFLECT_101)
    kimlik = cv2.warpPerspective(kimlik, P, (w, h), flags=cv2.INTER_NEAREST,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return im, kimlik


def fotometrik(rng, im):
    # NOT: bozunum GÜÇLÜ ama YAKMAYACAK kadar — aşırı parlaklık sahneyi beyaza
    # boyayıp koridor/zemin ayrımını yok ediyordu, yani öğrenilecek sinyali siliyordu.
    im = im.astype(np.float32)
    im *= rng.uniform(0.72, 1.22)                                  # parlaklık
    im = (im - im.mean()) * rng.uniform(0.85, 1.20) + im.mean()    # kontrast
    im = np.clip(im, 0, 255).astype(np.uint8)

    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + rng.randint(-12, 12)) % 180        # renk tonu
    hsv[..., 1] = np.clip(hsv[..., 1] * rng.uniform(0.65, 1.35), 0, 255)
    im = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR)

    if rng.random() < 0.55:                                         # gölge
        h, w = im.shape[:2]
        p = np.array([[rng.randint(0, w), rng.randint(0, h)] for _ in range(rng.randint(3, 6))])
        katman = im.copy()
        cv2.fillPoly(katman, [cv2.convexHull(p)], (0, 0, 0))
        im = cv2.addWeighted(im, 1 - rng.uniform(0.08, 0.30), katman,
                             rng.uniform(0.08, 0.30), 0)

    if rng.random() < 0.5:                                          # bulanıklık
        k = rng.choice([3, 3, 5])
        im = cv2.GaussianBlur(im, (k, k), 0)
    if rng.random() < 0.45:                                         # gürültü
        im = np.clip(im.astype(np.int16) +
                     np.random.randint(-14, 15, im.shape, np.int16), 0, 255).astype(np.uint8)
    if rng.random() < 0.5:                                          # JPEG bozunumu
        ok, buf = cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, rng.randint(45, 92)])
        if ok:
            im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return im


def fotometrik_rng_tuket(rng, im, kadraj=False):
    """Fotometrik RNG/NumPy akisini iki kipte esit tut; kadrajda sonucu at."""
    sonuc = fotometrik(rng, im.copy())
    return im if kadraj else sonuc


# ---------------------------------------------------------------- etiket
def _yaklastir(cnt, oran=0.0015):
    # T66: eps 0.0035 -> 0.0015. Ada geometrisinde bolge sayisi cok arttigi
    # icin sadelestirmenin KENAR ARTIGI da artiyordu: class-0 ile class-1
    # poligonlari ada sinirlarinda 1-2 px ust uste biniyor (olculdu: %0,46,
    # bilesenler ince yatay bar DEGIL yani bariyer kaynakli degil).
    eps = oran * cv2.arcLength(cnt, True)
    return cv2.approxPolyDP(cnt, eps, True).reshape(-1, 2).astype(np.int32)


def delikli_poligonlar(m):
    """Delikli ikili maskeyi DELIGI KORUYAN tek-parca poligonlara cevir.

    T66 · NEDEN: eski `etiketle` `RETR_EXTERNAL` kullaniyordu, yani DELIKLERI
    ATIYORDU. Serit tabanli geometride bunun bedeli kucuktu (olculdu: T71
    kumesinde 260 karenin 65'inde class-0 ile class-1 ust uste biniyordu,
    cakisan alan traversable'in medyan %0,7'si — "dar" seridin ic izi hem
    gecilebilir hem engel etiketleniyordu).
    ADA tabanli geometride ayni kusur YIKICI olurdu: zemin, ortasinda moloz
    ADALARI olan genis bir bolgedir; delikler atilirsa HER ADA "traversable"
    etiketlenir ve yer gercegi tam tersini soyler.

    YOLO-seg poligonu delik TASIYAMAZ. Cozum: her delik, dis halkaya en yakin
    kose ciftinden bir YARIK ile baglanir; sonuc tek basit poligondur ve
    `fillPoly` ile yeniden rasterize edildiginde ozgun maskeyi BIREBIR verir
    (olculdu: tek merkezi delik ve uc ada icin IoU 1,0000 · fark 0 px).
    """
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return []
    hier = hier[0]
    cikti = []
    for i, h in enumerate(hier):
        if h[3] != -1:                       # delik: ust seviyede degil
            continue
        if cv2.contourArea(cs[i]) < 300:
            continue
        dis = _yaklastir(cs[i])
        if len(dis) < 3:
            continue
        j = h[2]
        while j != -1:
            if cv2.contourArea(cs[j]) >= 40:
                delik = _yaklastir(cs[j])
                if len(delik) >= 3:
                    d = ((dis[:, None, :] - delik[None, :, :]) ** 2).sum(-1)
                    a, b = np.unravel_index(d.argmin(), d.shape)
                    dsira = np.roll(delik, -b, axis=0)
                    dis = np.vstack([dis[:a + 1], dsira, dsira[:1], dis[a:]])
            j = hier[j][0]
        cikti.append(dis)
    return cikti


def etiketle(kimlik, siniflar, boyut):
    """kimlik haritasından YOLO-seg poligon satırları üret (delik-duyarli)."""
    satir = []
    for k, c in siniflar.items():
        m = (kimlik == k).astype(np.uint8)
        if int(m.sum()) < 400:               # dönüşümde kırpılıp yok olmuş
            continue
        for ap in delikli_poligonlar(m):
            if len(ap) < 3:
                continue
            n = (ap.astype(np.float32) / boyut).clip(0, 1)
            satir.append(f"{c} " + " ".join(f"{v:.6f}" for v in n.reshape(-1)))
    return satir


# ---------------------------------------------------------------- ana
def _uretec_ciktisini_temizle(kok):
    """Yalniz imzali uretec ciktisini, tam preflight sonrasinda temizle."""
    hedefler = [kok / "images" / "train", kok / "images" / "val",
                kok / "labels" / "train", kok / "labels" / "val",
                kok / "_onizleme"]
    desen = re.compile(r"^sa_[0-9]{6}\.(?:jpg|jpeg|png|txt)$", re.IGNORECASE)
    imza = kok / TEMIZLIK_IMZASI_DOSYASI
    manifest = kok / "manifest.json"
    data_yaml = kok / "data.yaml"

    yabanci = []
    silinecek = []
    for d in hedefler:
        if not d.exists():
            continue
        if d.is_symlink() or not d.is_dir():
            yabanci.append(d)
            continue
        for p in d.iterdir():
            if p.is_symlink() or not p.is_file() or not desen.fullmatch(p.name):
                yabanci.append(p)
            else:
                silinecek.append(p)

    imzali = False
    if imza.exists():
        if (imza.is_symlink() or not imza.is_file()
                or imza.read_text(encoding="ascii") != TEMIZLIK_IMZASI):
            yabanci.append(imza)
        else:
            imzali = True
    if manifest.exists():
        try:
            meta = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_gecerli = meta.get("parametreler", {}).get("uretec") == Path(__file__).name
        except (OSError, UnicodeError, json.JSONDecodeError):
            manifest_gecerli = False
        if manifest.is_symlink() or not manifest.is_file() or not manifest_gecerli:
            yabanci.append(manifest)
        else:
            imzali = True
            silinecek.append(manifest)
    if data_yaml.exists():
        try:
            data_gecerli = data_yaml.read_text(encoding="utf-8").startswith(
                "# SENTETİK ARENA — 51_sentetik_arena.py")
        except (OSError, UnicodeError):
            data_gecerli = False
        if data_yaml.is_symlink() or not data_yaml.is_file() or not data_gecerli:
            yabanci.append(data_yaml)
        else:
            imzali = True
            silinecek.append(data_yaml)

    uretim_izi_var = bool(silinecek) or any(d.exists() for d in hedefler)
    if uretim_izi_var and not imzali:
        yabanci.append(kok / "(uretec_imzasi_yok)")
    if yabanci:
        adlar = ", ".join(str(p) for p in yabanci[:5])
        raise SystemExit(f"temizleme reddedildi; yabanci icerik var: {adlar}")

    # MUTASYON ancak butun hedefler ve kok metadatasi dogrulandiktan sonra baslar.
    for p in silinecek:
        p.unlink()
    kok.mkdir(parents=True, exist_ok=True)
    imza.write_text(TEMIZLIK_IMZASI, encoding="ascii")
    return len(silinecek)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adet", type=int, default=3000)
    ap.add_argument("--val-orani", type=float, default=0.1)
    ap.add_argument("--cikti", default=str(CIKTI))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--onizleme", action="store_true",
                    help="etiket bindirmeli önizleme görselleri de yaz")
    # --- v18 ayrıştırma deneyi için parametreler ---
    # v18'de üç şey aynı anda değişti ve model işletme eşiğinde tamamen sustu;
    # hangisinin zarar verdiği ayrıştırılamadı. Bu iki oran artık komut satırından
    # verilebilir, böylece her deney TEK değişkenli olabilir.
    ap.add_argument("--ayni-malzeme-orani", type=float, default=0.45,
                    help="geçilebilir yüzeyin zeminle AYNI dokudan olma olasılığı "
                         "(0.0 = yol her zaman zeminden ayırt edilebilir)")
    ap.add_argument("--kadraj", action="store_true",
                    help="T51 KADRAJ KIPI: koridorlar ust/alt uc bantlara "
                         "ULASIR (dikey pay 0, donus/perspektif kapali, "
                         "'kismi' serit yok). Yalniz demo/dogrulama kumesi "
                         "icin; EGITIM KIPINI DEGISTIRMEZ.")
    ap.add_argument("--banka", default=None,
                    help="doku bankasi dizini (varsayilan: betigin "
                         "yanindaki doku_bankasi/)")
    ap.add_argument("--bariyer-acisi", type=float, default=0.0,
                    help="bariyer kolunun yataya gore AZAMI egimi (derece). "
                         "0 = ozgun davranis (RNG akisi degismez, kabul "
                         "kumesi birebir uretilir). Onerilen: 45 — model "
                         "bariyeri yalniz yataya yakin acilarda goruyordu "
                         "(D-324: 60/120/135 derecede %0,0).")
    ap.add_argument("--dar-orani", type=float, default=0.28,
                    help="şeritlerin 'dar iz' (moloz arasından ince yol) olma olasılığı")
    ap.add_argument("--temizle", action=argparse.BooleanOptionalAction, default=True,
                    help="varsayilan ACIK: onceki sa_* goruntu/etiketlerini temizle")
    args = ap.parse_args()
    if args.banka:
        global BANKA
        BANKA = Path(args.banka)

    rng = random.Random(args.seed)
    np.random.seed(args.seed)
    banka = banka_yukle()
    kok = Path(args.cikti)
    if args.temizle:
        temizlenen = _uretec_ciktisini_temizle(kok)
        print(f"  temizlenen   : {temizlenen} eski uretec dosyasi")
    for s in ("train", "val"):
        (kok / "images" / s).mkdir(parents=True, exist_ok=True)
        (kok / "labels" / s).mkdir(parents=True, exist_ok=True)
    if args.onizleme:
        (kok / "_onizleme").mkdir(exist_ok=True)

    n_val = int(args.adet * args.val_orani)
    sayim = {0: 0, 1: 0}
    bos = 0
    ornekler: list = []

    for i in range(args.adet):
        sahne_bilgi = {} if args.kadraj else None
        im, kimlik, siniflar = sahne_uret(rng, banka, args.ayni_malzeme_orani,
                                          args.dar_orani, kadraj=args.kadraj,
                                          bilgi=sahne_bilgi,
                                          bariyer_acisi=args.bariyer_acisi)
        im, kimlik = geometrik(rng, im, kimlik, kadraj=args.kadraj)
        im = cv2.resize(im, (BOYUT, BOYUT), interpolation=cv2.INTER_AREA)
        kimlik = cv2.resize(kimlik, (BOYUT, BOYUT), interpolation=cv2.INTER_NEAREST)
        im = fotometrik_rng_tuket(rng, im, kadraj=args.kadraj)

        satir = etiketle(kimlik, siniflar, BOYUT)
        if not satir:
            bos += 1
            continue
        for s in satir:
            sayim[int(s[0])] += 1

        b = "val" if i < n_val else "train"
        ad = f"sa_{i:06d}"
        if sahne_bilgi is not None:
            ornekler.append(_manifest_kaydi(sahne_bilgi, ad, b, args.seed))
        cv2.imwrite(str(kok / "images" / b / f"{ad}.jpg"), im,
                    [cv2.IMWRITE_JPEG_QUALITY, 92])
        (kok / "labels" / b / f"{ad}.txt").write_text("\n".join(satir) + "\n",
                                                      encoding="utf-8")

        if args.onizleme and i < 24:
            ov = im.copy()
            for s in satir:
                p = s.split()
                c = int(p[0])
                pts = (np.asarray(p[1:], np.float32).reshape(-1, 2) * BOYUT).astype(np.int32)
                cv2.fillPoly(ov, [pts], (0, 200, 0) if c == 0 else (0, 0, 220))
            vis = cv2.addWeighted(im, 0.6, ov, 0.4, 0)
            cv2.imwrite(str(kok / "_onizleme" / f"{ad}.jpg"), vis)

        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{args.adet}")

    (kok / "data.yaml").write_text(
        f"# SENTETİK ARENA — 51_sentetik_arena.py (seed={args.seed}, "
        f"ayni_malzeme={args.ayni_malzeme_orani}, dar={args.dar_orani}, "
        f"kadraj={args.kadraj})\n"
        f"path: {kok}\ntrain: images/train\nval: images/val\n\n"
        "nc: 2\nnames:\n  0: traversable\n  1: blocked\n", encoding="utf-8")

    if args.kadraj:
        belirsiz = sum(1 for o in ornekler if o["arena"]["acik_serit"] is None)
        (kok / "manifest.json").write_text(json.dumps({
            "parametreler": {
                "uretec": "51_sentetik_arena.py",
                "kip": "kadraj",
                "tohum": args.seed,
                "adet": args.adet,
                "val_orani": args.val_orani,
                "ayni_malzeme_orani": args.ayni_malzeme_orani,
                "dar_orani": args.dar_orani,
                "bariyer_acisi": args.bariyer_acisi,
                "tuval": TUVAL,
                "boyut": BOYUT,
                "siniflar": {"0": "traversable", "1": "blocked"},
                "olcek_kaynagi": KADRAJ_OLCEK_KAYNAGI,
                "acik_serit_kaynagi":
                    "URETIM ANINDA kaydedilen serit durumu; class-0'dan "
                    "TURETILEMEZ (REVIEW_LOG D-70)",
                "belirsiz_kare": belirsiz,
            },
            "ornekler": ornekler,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  manifest     : {kok / 'manifest.json'} "
              f"({len(ornekler)} kayit, belirsiz {belirsiz})")

    print(f"\nSENTETİK ARENA HAZIR: {kok}")
    print(f"  görüntü      : {args.adet - bos} (boş atlanan: {bos})")
    print(f"  traversable  : {sayim[0]} poligon")
    print(f"  blocked      : {sayim[1]} poligon")
    if args.onizleme:
        print(f"  önizleme     : {kok / '_onizleme'}")


if __name__ == "__main__":
    main()
