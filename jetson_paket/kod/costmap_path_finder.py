"""COSTMAP TABANLI SERBEST ALAN + ROTA BULUCU

NEDEN: ekibin kendi cikti gorselleri (WhatsApp Image 2026-08-02 at 14.53.52*.jpeg)
rotanin park halindeki arabalarin TAM USTUNDEN gectigini gosteriyor. Model otopark
zeminini dogru buluyor ama ustundeki araclari maskeden cikarmiyor. Kok neden mimari:

  - rpi_inference.get_masks() iki sinif donduruyor ama analyze_path() SADECE
    masks[0]'i (traversable) aliyor — engel sinifi (masks[1]) 4/5 cagri yerinde
    HIC KULLANILMIYOR.
  - analyze_path() yalniz EN BUYUK BAGLI BILESENI tutuyor → 3 koridoru kiyaslamak
    yapisal olarak imkansiz, diger ikisi kiyas baslamadan siliniyor.
  - Waypoint'ler mesafe donusumunun her bantta argmax'i; sureklilik ve engel
    aciklik denetimi yok.

SARTNAME BAGLAMI: HTAB 50m x 50m, icinde 3 guzergah var, yarisma gunu YALNIZ
BIRI acik (hangisi gizli). P_gorev = 600 puan yalniz IKA hedef brandaya FIZIKSEL
TEMAS ederse, aksi halde 0. "Yanlis guzergah tespiti yapan takimlar 0 puan alarak
basarisiz sayilir." Yani sistemin tek isi: dogru koridoru secmek ve IKA'yi engele
carpmadan H'ye goturmek.

MİMARİ — İKİ KATMAN (saf Python A* kare basina kosamaz, olculdu: ROI 128x48 A*
~30 ms; Jetson'da ~2x):
  KATMAN A (her karede, ~5 ms @384px): serbest_alan() + koridor_adaylari()
    → hangi koridor acik, guven, darbogaz genisligi.
  KATMAN B (mozaikte veya ~2 Hz'de, ~30-40 ms): astar() + yol_duzelt()
    + rota_dogrula() → gercek waypoint listesi + guvenlik kaniti.

KUTUPHANE KISITI (bu venv'de dogrulandi): scipy YOK, scikit-image YOK,
cv2.ximgproc YOK → medial_axis/skeletonize kullanilamaz. Yerine ACIKLIK
AGIRLIKLI A* (heapq, stdlib): maliyet fonksiyonu distanceTransform alanini
cezalandirarak yolu koridor ORTASINA ceker — skeleton'u HESAPLAMAZ ama ona
CEKILIR, ve dar bir gecit esikte HIC VAR OLMAZ (skeleton'da var olur, sonradan
ayiklamak gerekir).

Kullanim (uc seviyeli):
  from costmap_path_finder import rota_bul
  sonuc = rota_bul({0: zemin_mask, 1: engel_mask}, mpp=0.0547,
                   baslangic=kb_mask, hedef=hb_mask)
  sonuc["durum"], sonuc["yol_no"], sonuc["waypoints_px"]
"""
import heapq
import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

try:
    from .karar_sozlesmesi import hedef_bant_yuksekligi, serit_no
except ImportError:
    from karar_sozlesmesi import hedef_bant_yuksekligi, serit_no

logger = logging.getLogger("costmap_path_finder")

# ────────────────────────────────────────────────────────────────────────────
# 1) FIZIKSEL SABITLER — turetildi, tahmin degil (bkz. modul sonundaki TAHMINLER)
# ────────────────────────────────────────────────────────────────────────────
IKA_GENISLIK_M = 0.70          # simulation/models/ika/model.sdf: govde 0.66x0.50,
                                # tekerlek kizaklari 0.62x0.08 → gercek genislik ~0.66 m,
                                # yuvarlandi. TAHMIN: gercek arac olcusu FARKLI olabilir.
MASKE_HATA_M = 0.25             # get_masks() 512-proto maskeyi tam coz. bilineer resize
                                # eder; sinir belirsizligi ~1 proto-piksel + bulanma payi.
TAKIP_HATA_M = 0.50              # IKA WP_RADIUS ile uyumlu takip hata ust siniri.
                                # (bkz. modul sonu TAHMINLER #1). r_gerekli'nin en
                                # buyuk tek terimi.
ALGI_PAYI_M = 0.25               # engel maskesinin GERCEK engelden ic kalma payi —
                                # yalniz ENGEL sisirilirken kullanilir (zemin degil).
DOYUM_CARPANI_M = 2.0            # A* aciklik cezasi bu degerden sonra doymus sayilir
                                # (en dar sim koridoru 4.0 m → yari genislik 2.0 m).

R_GEREKLI_M = (IKA_GENISLIK_M / 2.0) + MASKE_HATA_M + TAKIP_HATA_M
# = 0.35 + 0.25 + 0.50 = 1.10 m  (yari-genislik, yani gerekli aciklik yaricapi)

# ────────────────────────────────────────────────────────────────────────────
# 2) MORFOLOJI / IZGARA SABITLERI
# ────────────────────────────────────────────────────────────────────────────
AC_M = 0.30                      # zemin acma cekirdegi — SADECE tek-piksel benek
                                  # temizligi. Ada temizligi buradan DEGIL, bagli-
                                  # bilesen alan filtresinden gelir (erozyon yok).
KAPAT_M = 0.40                   # zemin kapama cekirdegi — en kucuk gercek engelden
                                  # (insan/moloz ~0.5 m) KUCUK olmak ZORUNDA, aksi
                                  # halde gorulmemis bir engelin ustunu koprulerdi.
MIN_ADA_M2 = (2.0 * R_GEREKLI_M) ** 2   # IKA'nin donebilecegi kareden kucuk parca atilir

HEDEF_M_HUCRE = 0.15             # costmap hucre boyutu (metre). Turetim: darbogaz
                                  # ayrimi icin hucre, (kenar bosluk)/2'den kucuk
                                  # olmali; R_GEREKLI_M/6 ile ust sinirlandi.
PLAN_M_HUCRE = 0.45              # A* izgara hucresi ~3x costmap hucresi (hiz icin)

LAMBDA_ACIKLIK = 3.0             # en dar hucre 1+LAMBDA=4x pahali (bkz. modul sonu #4)
US_ACIKLIK = 2.0                 # aciklik cezasi ussu (karesel — nazik rampa)

WP_ARALIK_M = 2.0                # waypoint azami araligi (mesafe VEYA aci ile decimate)
MAKS_WP = 64


class RotaGuvenlikHatasi(RuntimeError):
    """rota_dogrula(katı=True) rotanın bir engelle kesistigini tespit ettiginde."""


# ────────────────────────────────────────────────────────────────────────────
# 3) OLCEK YARDIMCILARI
# ────────────────────────────────────────────────────────────────────────────
def olcek_px(mpp, ika_genislik_m=IKA_GENISLIK_M, maske_hata_m=MASKE_HATA_M,
             takip_hata_m=TAKIP_HATA_M, algi_payi_m=ALGI_PAYI_M,
             hedef_m_hucre=HEDEF_M_HUCRE, plan_m_hucre=PLAN_M_HUCRE):
    """Metre cinsinden fiziksel sabitleri piksel/hucre birimine cevirir.

    mpp=None ise "olceksiz kip": tum degerler DOGRUDAN piksel olarak, mpp=1.0
    varsayilarak donuk — yer gercegi/test amacli, gorev ucusunda KULLANILMAZ.
    """
    m = 1.0 if mpp is None else float(mpp)
    r_gerekli_m = (ika_genislik_m / 2.0) + maske_hata_m + takip_hata_m
    return {
        "mpp": m,
        "r_gerekli_px": r_gerekli_m / m,
        "r_gerekli_m": r_gerekli_m,
        # Bu deger engel genisletmesinde YARICAP olarak kullanilir. Guvenlik
        # payi yuvarlama nedeniyle hedeflenen fiziksel degerin altina inmez.
        "algi_payi_px": max(1, int(np.ceil(algi_payi_m / m))),
        "ac_px": max(1, round(AC_M / m)),
        "kapat_px": max(1, round(KAPAT_M / m)),
        "min_ada_px": (2.0 * r_gerekli_m / m) ** 2,
        "doyum_px": DOYUM_CARPANI_M / m,
        "wp_aralik_px": WP_ARALIK_M / m,
        "hedef_m_hucre": hedef_m_hucre,
        "plan_m_hucre": plan_m_hucre,
    }


def mpp_arac_maskesinden(arac_maskeleri, tipik_genislik_m=1.8):
    """COCO arac maskelerinin kisa ekseninin medyanindan mpp TAHMINI.
    SADECE kalibrasyon/test icin — gorev yolunda KULLANILMAZ (irtifa/FOV
    degisirse yanlis olur). arac_maskeleri: liste of (h,w) uint8 binary mask."""
    genislikler = []
    for m in arac_maskeleri:
        if m.sum() < 20:
            continue
        ys, xs = np.nonzero(m)
        kutu = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))
        (kw, kh) = kutu[1]
        genislikler.append(min(kw, kh))
    if not genislikler:
        return None
    return float(tipik_genislik_m / np.median(genislikler))


# ────────────────────────────────────────────────────────────────────────────
# 4) SERBEST ALAN — hatanin duzeltildigi yer
# ────────────────────────────────────────────────────────────────────────────
def _cekirdek(px):
    """Morfoloji icin tek sayili kenar uzunlugunda eliptik cekirdek."""
    px = max(1, int(round(px)))
    if px % 2 == 0:
        px += 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (px, px))


def _yaricap_cekirdegi(yaricap_px):
    """Verilen piksel yaricapini koruyan eliptik cekirdek uret.

    OpenCV cekirdek boyutunu cap olarak alir. Algilama guvenlik payini
    dogrudan 3x3 gibi bir boyuta vermek, engeli payin yarisi kadar bile
    genisletmeyebilir.
    """
    yaricap = max(1, int(np.ceil(yaricap_px)))
    return _cekirdek(2 * yaricap + 1)


def _icerik_kutusunu_dogrula(icerik, h, w):
    """Letterbox icerik kutusunu dogrula; cagri hatasinda bos ROI don.

    ``None`` eski cagrilar icin tum tuvali temsil eder. Verilen kutu dort
    tamsayidan olusmali, pozitif olmali ve tuvalin tumuyle icinde kalmalidir.
    Gecersiz kutu sessizce kirpilmaz; fail-closed bos ROI olur.
    """
    if icerik is None:
        return 0, 0, w, h
    if isinstance(icerik, np.ndarray):
        if icerik.shape != (4,):
            return 0, 0, 0, 0
        degerler = tuple(icerik)
    elif isinstance(icerik, (tuple, list)):
        degerler = tuple(icerik)
    else:
        return 0, 0, 0, 0
    if len(degerler) != 4:
        return 0, 0, 0, 0
    if any(isinstance(v, (bool, np.bool_)) or
           not isinstance(v, (int, np.integer)) for v in degerler):
        return 0, 0, 0, 0

    x0, y0, genislik, yukseklik = (int(v) for v in degerler)
    if (genislik <= 0 or yukseklik <= 0 or x0 < 0 or y0 < 0 or
            x0 + genislik > w or y0 + yukseklik > h):
        return 0, 0, 0, 0
    return x0, y0, genislik, yukseklik


def _icerik_maskesi(h, w, icerik):
    """Dogrulanmis icerik kutusu ile yalniz-cikaran ikili maske don."""
    kutu = _icerik_kutusunu_dogrula(icerik, h, w)
    x0, y0, genislik, yukseklik = kutu
    maske = np.zeros((h, w), np.uint8)
    if genislik > 0 and yukseklik > 0:
        maske[y0:y0 + yukseklik, x0:x0 + genislik] = 1
    return kutu, maske


def serbest_alan(maskeler, *, mpp=None, yol_sinif_idler=(0,), engel_sinif_idler=(1,),
                 algi_payi_px=None, ac_px=None, kapat_px=None, min_ada_px=None,
                 icerik=None):
    """Zemin - engel = serbest alan. SIRALAMA KRITIK (asagida acikliyor).

    maskeler: {sinif_id: (h,w) uint8 binary mask} — rpi_inference.get_masks() ciktisi.

    Donen dict:
      serbest    : (h,w) uint8 — nihai gecilebilir alan
      engel_ham  : (h,w) uint8 — HAM engel birlesimi, HICBIR islem gormemis
                   (rota_dogrula bunu kullanir — belent-ve-braces kontrolu)
      dt_px      : (h,w) float32 — serbest alanin TAM Euclidean uzaklik donusumu

    NEDEN engeli robot yaricapi kadar SISIRMIYORUZ: dt_px >= r esigi, disk
    yaricapi r ile eroze etmeye MATEMATIKSEL OLARAK DENK ama TAM (dilate ile
    kose yaklasik degil). Ayrica AYNI alan hem gecilebilirlik esigi, hem
    darbogaz olcumu, hem A* aciklik maliyeti, hem son dogrulama icin kullanilir.
    """
    olc = olcek_px(mpp)
    algi_payi_px = algi_payi_px if algi_payi_px is not None else olc["algi_payi_px"]
    ac_px = ac_px if ac_px is not None else olc["ac_px"]
    kapat_px = kapat_px if kapat_px is not None else olc["kapat_px"]
    min_ada_px = min_ada_px if min_ada_px is not None else olc["min_ada_px"]

    h, w = next(iter(maskeler.values())).shape

    # --- 1) HAM engel — dokunulmaz, dogrulama icin saklanir ---
    engel_ham = np.zeros((h, w), np.uint8)
    for c in engel_sinif_idler:
        if c in maskeler:
            engel_ham = np.maximum(engel_ham, maskeler[c])

    # --- 2) engel: kapat + sisir (ALGI EKSIK-KAPSAMA PAYI icin — permissive) ---
    engel = engel_ham
    if engel.any():
        engel_cekirdegi = _yaricap_cekirdegi(algi_payi_px)
        engel = cv2.morphologyEx(engel, cv2.MORPH_CLOSE, engel_cekirdegi)
        engel = cv2.dilate(engel, engel_cekirdegi)

    # --- 3) zemin: SADECE benek temizligi (agresif erozyon YOK) ---
    zemin = np.zeros((h, w), np.uint8)
    for c in yol_sinif_idler:
        if c in maskeler:
            zemin = np.maximum(zemin, maskeler[c])
    if zemin.any():
        zemin = cv2.morphologyEx(zemin, cv2.MORPH_OPEN, _cekirdek(ac_px))
        zemin = cv2.morphologyEx(zemin, cv2.MORPH_CLOSE, _cekirdek(kapat_px))

    # --- 4) CIKARMA EN SON. Bundan sonra hicbir genisletme yapilmaz. ---
    serbest = cv2.bitwise_and(zemin, cv2.bitwise_not(engel))

    # --- 5) letterbox dolgusu YALNIZ CIKARIR; serbest alani buyutemez ---
    icerik_kutusu, icerik_maske = _icerik_maskesi(h, w, icerik)
    serbest = serbest.copy()
    serbest[icerik_maske == 0] = 0

    # --- 6) ada temizligi: alan filtresi (erozyon DEGIL) ---
    n, etiket, ist, _ = cv2.connectedComponentsWithStats(serbest, 8)
    temiz = np.zeros_like(serbest)
    for k in range(1, n):
        if ist[k, cv2.CC_STAT_AREA] >= min_ada_px:
            temiz[etiket == k] = 1
    serbest = temiz

    dt_px = cv2.distanceTransform(serbest, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    return {"serbest": serbest, "engel_ham": engel_ham, "engel": engel,
           "zemin": zemin, "dt_px": dt_px, "sekil": (h, w), "olcek": olc,
           "icerik": icerik_kutusu}


# ────────────────────────────────────────────────────────────────────────────
# 5) KORIDOR ADAYLARI — en-buyuk-bilesen yerine "kapi" testi
# ────────────────────────────────────────────────────────────────────────────
def _tohum_maske(kaynak, h, w, taraf, *, icerik=None):
    """Varsayilan tohumu letterbox iceriginin alt/ust uc bandinda kur."""
    if kaynak is not None:
        return kaynak.astype(np.uint8)

    icerik_kutusu, _icerik_maske = _icerik_maskesi(h, w, icerik)
    m = np.zeros((h, w), np.uint8)
    x0, y0, genislik, yukseklik = icerik_kutusu
    if genislik == 0 or yukseklik == 0:
        return m
    pay = hedef_bant_yuksekligi(yukseklik)
    if taraf == "alt":
        m[y0 + yukseklik - pay:y0 + yukseklik,
          x0:x0 + genislik] = 1
    else:
        m[y0:y0 + pay, x0:x0 + genislik] = 1
    return m


def _tohum_merkezi(tohum):
    """Kullanici tarafindan verilen tohumun geometrik merkez pikselini bul.

    A* cok-kaynakli tohumlardan, plan izgarasinda kaynak/hedefe bir hucre
    yakin bir yol baslatir. Gercek IKA ise KB'de, hedef de HB'de baslar/biter.
    Bu nedenle harici olarak verilen disk tohumlarda merkez pikseli ayrica
    rotaya sabitleriz. ``None`` ile uretilen genis varsayilan bantlarda bu
    islem yapilmaz; o kipte tek bir fiziksel baslangic/hedef tanimli degildir.
    """
    maske = (np.asarray(tohum) > 0).astype(np.uint8)
    if maske.ndim != 2 or not maske.any():
        return None
    # Diskte en buyuk uzaklik noktasi merkezdir; tek piksel tohumu aynen verir.
    merkezlik = cv2.distanceTransform(maske, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    y, x = np.unravel_index(int(np.argmax(merkezlik)), merkezlik.shape)
    return int(x), int(y)


def _ankoru_ekle(waypoints, ankor, basta, gecilebilir_tam):
    """Dogru C-uzayinda kalabiliyorsa fiziksel baslangic/hedefi rotaya ekle.

    Rota sonradan koordinat sistemine tasinmadan once burada kontrol edilir.
    Bir ankor ile A*'in ilk/son hucre merkezi arasindaki dogru guvenli degilse
    yaklasik bir rota gondermek yerine rota reddedilir.
    """
    if ankor is None:
        return list(waypoints), None
    x, y = ankor
    h, w = gecilebilir_tam.shape
    if not (0 <= x < w and 0 <= y < h) or not gecilebilir_tam[y, x]:
        return None, "fiziksel tohum C-uzayinda gecilebilir degil"
    if not waypoints:
        return None, "A* waypoint uretmedi"

    uc = waypoints[0] if basta else waypoints[-1]
    if (int(round(uc[0])), int(round(uc[1]))) == (x, y):
        return list(waypoints), None
    if not _gorus_hatti((x, y), uc, gecilebilir_tam):
        return None, "fiziksel tohum ile A* rotasi arasinda guvenli baglanti yok"
    return ([(x, y)] + list(waypoints)) if basta else (list(waypoints) + [(x, y)]), None


def _bagli_mi(gecilebilir, tohum_a, tohum_b):
    n, etiket = cv2.connectedComponents(gecilebilir.astype(np.uint8), 8)
    if n <= 1:
        return False
    ea = set(np.unique(etiket[(tohum_a > 0) & (gecilebilir > 0)])) - {0}
    eb = set(np.unique(etiket[(tohum_b > 0) & (gecilebilir > 0)])) - {0}
    return bool(ea & eb)


def koridor_adaylari(dt_px, r_gerekli_px, baslangic=None, hedef=None, *,
                     bant_oranlari=(0.30, 0.40, 0.50, 0.60, 0.70),
                     bant_yukseklik_orani=0.06, icerik=None):
    """3 guzergahi (ya da kac tane varsa) ayirt edip her birini degerlendirir.

    NEDEN EN-BUYUK-BAGLI-BILESEN YETMEZ: 3 guzergah baslangicta ayrilip hedefte
    BIRLESIYOR (bkz. simulation/scripts/arena.py) — yani kapali bir yol AYRI bir
    bilesen degil, ayni bilesene bagli bir CIKMAZ. Duz baglanti testi hangi
    guzergahin acik oldugunu SOYLEYEMEZ. Bu yuzden: yatay bir "kapi" bandi
    secilir, o bantta kac ayrik gecit varsa o kadar aday cikar; her aday icin
    SADECE o kapi acikken baslangic<->hedef baglantisi test edilir.

    Donen: (adaylar, tani)
      adaylar[i] = {"etiket": 1|2|3, "gecilebilir": bool, "darbogaz_px": float,
                    "kapi_merkez_x": int, "kapi_genislik_px": int,
                    "serit_yayilimi": (int, int)}
      tani: {"bant_y": (y0,y1), "n_kapi": int, "belirsiz": bool}

    ETIKET TEK KAYNAKTAN GELIR (T90 · REVIEW_LOG D-145). Bu fonksiyon eskiden
    kendi numarasini uretiyordu: n_kapi==3 iken soldan saga SIRA NUMARASI
    (i+1), aksi halde kapiyi SERBEST ALAN BBOX'ina gore uce bolerek. Oysa
    `karar_sozlesmesi.serit_no()` docstring'i "Tek kaynak: hem karar hem
    gorsellestirme burayi cagirir" der ve sinirlari LETTERBOX ICERIK
    KUTUSUNDAN alir (CONTRACTS SS8). Iki otorite olculdu: 470 aday kapinin
    104'u (%22,1) iki semada FARKLI numara aliyordu. Kadraj alinmis bir karede
    serbest alan icerik kutusunu doldurmaz; ayni fiziksel koridor iki semada
    ayrisir. Artik etiket YALNIZ `serit_no()`dan turer.

    `serit_yayilimi` TANI AMACLIDIR, karara girmez: kapi bir NOKTA degil bir
    ACIKLIKTIR ve iki seride yayilabilir. Etiketin kendisi AGIRLIK MERKEZINDEN
    turer, cunku yayinlanan `road` TEK bir sayi olmak zorundadir
    (comms/protocol.py:51).

    ⚠ Bu alan `CC_STAT_LEFT`/`CC_STAT_WIDTH` ile KESIN hesaplanir. D-145'te
    "247 karenin 7'si yalniz yayilimla aciklanir" diye gecen sayi ise bir
    OLCUM BETIGININ `cx ± genislik/2` YAKLASIMINDAN gelir ve bu alanla ayni
    sey DEGILDIR (D-145 "DOGRULANAMADI #3"). Kesin alanla yeniden olculen
    sayilar D-146'dadir; yaklasik sayi buraya gerekce olarak YAZILMAZ.
    """
    gecilebilir = (dt_px >= r_gerekli_px).astype(np.uint8)
    h, w = gecilebilir.shape
    icerik_kutusu, icerik_maske = _icerik_maskesi(h, w, icerik)
    gecilebilir[icerik_maske == 0] = 0

    # Yatay bbox ARTIK KULLANILMIYOR: etiket `serit_no()`den, yani ICERIK
    # KUTUSUNDAN turer (T90). Dikey bbox bant konumlandirmasi icin durur.
    ys, _xs = np.nonzero(gecilebilir)
    if len(ys) == 0:
        return [], {"bant_y": None, "n_kapi": 0, "belirsiz": True, "sebep": "MASKE_YOK"}

    y0_bbox, y1_bbox = int(ys.min()), int(ys.max())
    bbox_h = max(1, y1_bbox - y0_bbox)
    icerik_x0, _icerik_y0, icerik_w, _icerik_h = icerik_kutusu

    tohum_a = _tohum_maske(
        baslangic, h, w, "alt", icerik=icerik_kutusu)
    tohum_b = _tohum_maske(
        hedef, h, w, "ust", icerik=icerik_kutusu)

    min_kapi_px = 2 * r_gerekli_px
    en_iyi = None
    for oran in bant_oranlari:
        yc = y0_bbox + oran * bbox_h
        by0 = max(0, int(yc - bant_yukseklik_orani * bbox_h / 2))
        by1 = min(h, int(yc + bant_yukseklik_orani * bbox_h / 2) + 1)
        if by1 <= by0:
            continue
        serit = gecilebilir[by0:by1, :]
        n, etiket, ist, sent = cv2.connectedComponentsWithStats(serit, 8)
        kapilar = []
        for k in range(1, n):
            genislik = ist[k, cv2.CC_STAT_WIDTH]
            alan = ist[k, cv2.CC_STAT_AREA]
            if genislik >= min_kapi_px and alan >= min_kapi_px * (by1 - by0) * 0.5:
                kapilar.append({"k": k, "cx": float(sent[k][0]), "genislik": genislik,
                               "alan": alan,
                               "x0": int(ist[k, cv2.CC_STAT_LEFT])})
        if len(kapilar) > (len(en_iyi["kapilar"]) if en_iyi else 0) or (
                en_iyi and len(kapilar) == len(en_iyi["kapilar"]) and
                sum(x["alan"] for x in kapilar) > sum(x["alan"] for x in en_iyi["kapilar"])):
            en_iyi = {"by0": by0, "by1": by1, "kapilar": kapilar, "etiket": etiket}

    if en_iyi is None or not en_iyi["kapilar"]:
        return [], {"bant_y": None, "n_kapi": 0, "belirsiz": True, "sebep": "KAPI_YOK"}

    by0, by1, etiket = en_iyi["by0"], en_iyi["by1"], en_iyi["etiket"]
    kapilar = sorted(en_iyi["kapilar"], key=lambda k: k["cx"])
    n_kapi = len(kapilar)
    belirsiz = n_kapi != 3

    adaylar = []
    for kapi in kapilar:
        m_g = gecilebilir.copy()
        m_g[by0:by1, :] = 0
        alt_etiket = (etiket == kapi["k"])
        m_g[by0:by1, :][alt_etiket] = 1

        gecebiliyor = _bagli_mi(m_g, tohum_a, tohum_b)

        darbogaz_px = 0.0
        if gecebiliyor:
            lo, hi = r_gerekli_px, 4 * r_gerekli_px
            for _ in range(6):
                mid = (lo + hi) / 2.0
                aday_g = (dt_px >= mid).astype(np.uint8)
                aday_gc = aday_g.copy()
                aday_gc[by0:by1, :] = 0
                aday_gc[by0:by1, :][alt_etiket & (aday_g[by0:by1, :] > 0)] = 1
                if _bagli_mi(aday_gc, tohum_a, tohum_b):
                    lo = mid
                else:
                    hi = mid
            darbogaz_px = lo

        # TEK KAYNAK (madde 16): numara `serit_no()`den gelir, burada
        # URETILMEZ. Sira numarasi (i+1) ve serbest-alan-bbox uclemesi T90'da
        # kaldirildi — ikisi de icerik kutusundan BAGIMSIZ calisiyordu.
        # Etiket, YAYINLANAN `kapi_merkez_x` ile AYNI sayidan turer. Float `cx`
        # kullanilsaydi disaridan yapilan bir denetim (76_serit_etiketi...)
        # icerik genisligi 3'e tam bolunmedigi karelerde etiketi yeniden
        # uretemezdi: int() asagi keser ve sinira cok yakin bir kapi taraf
        # degistirirdi.
        kapi_merkez_x = int(kapi["cx"])
        etiket_no = int(serit_no(kapi_merkez_x, icerik_x0, icerik_w))
        kapi_x0 = int(kapi["x0"])
        kapi_x1 = kapi_x0 + max(1, int(kapi["genislik"])) - 1
        yay_sol = int(serit_no(kapi_x0, icerik_x0, icerik_w))
        yay_sag = int(serit_no(kapi_x1, icerik_x0, icerik_w))

        adaylar.append({
            "etiket": etiket_no, "gecilebilir": gecebiliyor,
            "darbogaz_px": darbogaz_px, "kapi_merkez_x": kapi_merkez_x,
            "kapi_genislik_px": int(kapi["genislik"]), "bilesen_alan": int(kapi["alan"]),
            "serit_yayilimi": (min(yay_sol, yay_sag), max(yay_sol, yay_sag)),
        })

    tani = {"bant_y": (by0, by1), "n_kapi": n_kapi, "belirsiz": belirsiz}
    return adaylar, tani


def _guven_hesapla(adaylar, r_gerekli_m, mpp):
    gecebilenler = sorted((a for a in adaylar if a["gecilebilir"]),
                          key=lambda a: -a["darbogaz_px"])
    if not gecebilenler:
        return 0.0, None
    kazanan = gecebilenler[0]
    darbogaz_m = kazanan["darbogaz_px"] * mpp
    bolluk = np.clip((darbogaz_m - r_gerekli_m) / max(r_gerekli_m, 1e-6), 0, 1)
    if len(gecebilenler) == 1:
        ayirt = 1.0
    else:
        d1 = kazanan["darbogaz_px"]
        d2 = gecebilenler[1]["darbogaz_px"]
        ayirt = np.clip((d1 - d2) / max(d1, 1e-6), 0, 1)
    return round(float(bolluk * ayirt), 3), kazanan


# ────────────────────────────────────────────────────────────────────────────
# 6) A* — aciklik agirlikli (medial axis YOK, kutuphane kisiti)
# ────────────────────────────────────────────────────────────────────────────
def plan_izgarasi(dt_px, gecilebilir, ds):
    """Costmap -> plan izgarasi. MIN-havuzlama (muhafazakar): bir plan hucresi
    ancak icindeki TUM costmap piksellerinin acikligi yeterliyse serbesttir.
    numpy reshape-min kullanilir (cv2.erode DEGIL — cift boyutlu cekirdegin
    capasi belirsizdir ve izgarayi sessizce kaydirabilir).
    gecilebilir parametresi kullanilmiyor (geriye uyum icin tutuldu, None gecilebilir)."""
    h, w = dt_px.shape
    h2, w2 = h // ds, w // ds
    if h2 < 1 or w2 < 1:
        return dt_px[:0, :0], None
    kirpik = dt_px[:h2 * ds, :w2 * ds].reshape(h2, ds, w2, ds)
    dt_plan = kirpik.min(axis=(1, 3))
    return dt_plan, None


def _tohum_plan_izgarasi(tohum_px, h_plan, w_plan, ds):
    """Tohum maskesini plan_izgarasi ile AYNI hucre sinirlarinda indir.

    cv2.resize, ROI'nin ds'ye bolunmeyen kusaginda koordinati kaydirabiliyor;
    A* baslangic/hedefi ile min-havuzlanmis C-uzayi ayni piksel bloklarindan
    turetilmelidir. Bir hucrede tek bir tohum pikseli bile varsa kaynak/hedef
    hucre olarak tutulur.
    """
    if h_plan < 1 or w_plan < 1:
        return np.zeros((0, 0), dtype=bool)
    kirpik = np.asarray(tohum_px, dtype=np.uint8)[:h_plan * ds, :w_plan * ds]
    return kirpik.reshape(h_plan, ds, w_plan, ds).any(axis=(1, 3))


def astar(gecilebilir_h, aciklik_m_h, hedef_h, baslangic_h, *,
          adim_m, r_gerekli_m, doyum_m=DOYUM_CARPANI_M,
          lam=LAMBDA_ACIKLIK, us=US_ACIKLIK):
    """8-komsulu, aciklik agirlikli A*. Cok-kaynakli, cok-hedefli.

    gecilebilir_h : (H,W) bool/uint8 izgara — True = serbest
    aciklik_m_h   : (H,W) float — hucre basina aciklik, METRE
    hedef_h/baslangic_h : (H,W) bool maskeler (birden fazla hucre olabilir)
    Donen: [(r,c), ...] baslangic->hedef sirali, veya None (yol yok).

    KOSE KESME YASAGI: capraz hamle ancak IKI ortogonal komsu da serbestse.
    Yoksa rota kosede degen iki engelin arasindan sizar — bir tekerlegi
    arabaya koyan hata sinifi tam budur.
    """
    H, W = gecilebilir_h.shape
    c_doy = doyum_m

    def acilik_cezasi(r, c):
        c_val = min(float(aciklik_m_h[r, c]), c_doy)
        u = (c_doy - c_val) / max(c_doy - r_gerekli_m, 1e-6)
        u = np.clip(u, 0.0, 1.0)
        return 1.0 + lam * (u ** us)

    hedef_yok = np.logical_not(hedef_h)
    h_alan = cv2.distanceTransform(hedef_yok.astype(np.uint8), cv2.DIST_L2,
                                   cv2.DIST_MASK_PRECISE) * adim_m

    komsular = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                (-1, -1, np.sqrt(2)), (-1, 1, np.sqrt(2)),
                (1, -1, np.sqrt(2)), (1, 1, np.sqrt(2))]

    g = {}
    gelen = {}
    acik = []
    sayac = 0
    for r in range(H):
        for c in range(W):
            if baslangic_h[r, c] and gecilebilir_h[r, c]:
                g[(r, c)] = 0.0
                heapq.heappush(acik, (h_alan[r, c], sayac, (r, c)))
                sayac += 1

    if not acik:
        return None

    kapali = set()
    while acik:
        f, _, (r, c) = heapq.heappop(acik)
        if (r, c) in kapali:
            continue
        kapali.add((r, c))
        if hedef_h[r, c]:
            yol = [(r, c)]
            while (r, c) in gelen:
                r, c = gelen[(r, c)]
                yol.append((r, c))
            yol.reverse()
            return yol

        for dr, dc, adim_carpan in komsular:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < H and 0 <= nc < W):
                continue
            if not gecilebilir_h[nr, nc] or (nr, nc) in kapali:
                continue
            if dr != 0 and dc != 0:
                if not gecilebilir_h[r + dr, c] or not gecilebilir_h[r, c + dc]:
                    continue   # kose kesme yasagi
            aday_g = g[(r, c)] + adim_m * adim_carpan * acilik_cezasi(nr, nc)
            if aday_g < g.get((nr, nc), float("inf")):
                g[(nr, nc)] = aday_g
                gelen[(nr, nc)] = (r, c)
                f_yeni = aday_g * (1 + 1e-4) + h_alan[nr, nc]
                heapq.heappush(acik, (f_yeni, sayac, (nr, nc)))
                sayac += 1

    return None


# ────────────────────────────────────────────────────────────────────────────
# 7) SON ISLEM: duzeltme + waypoint decimasyonu
# ────────────────────────────────────────────────────────────────────────────
def _gorus_hatti(p1, p2, gecilebilir_tam):
    h, w = gecilebilir_tam.shape
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    x2, y2 = int(round(p2[0])), int(round(p2[1]))
    if not (0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h):
        return False
    # Son guvenlik kapisi rota_dogrula() da cv2.polylines kullanir. Ayni
    # rasterizasyonu burada kullanmak, farkli cizgi yuvarlamasinin guvenli
    # saydigi bir kisayolun sonradan reddedilmesini onler. Tum mozaik yerine
    # yalniz segmentin sinirlayici kutusunu ayirmak, kivrimli rotalarda
    # O(n^2 * H * W) gecici maske tahsisini onler.
    sol, sag = min(x1, x2), max(x1, x2)
    ust, alt = min(y1, y2), max(y1, y2)
    cizgi = np.zeros((alt - ust + 1, sag - sol + 1), np.uint8)
    cv2.line(cizgi, (x1 - sol, y1 - ust), (x2 - sol, y2 - ust),
             1, thickness=1, lineType=cv2.LINE_8)
    pencere = gecilebilir_tam[ust:alt + 1, sol:sag + 1]
    return bool(pencere[cizgi > 0].all())


def _bresenham_noktalari(bas, son):
    """LINE_8 ile uyumlu sirali tamsayi cizgi noktalarini uret."""
    x0, y0 = int(round(bas[0])), int(round(bas[1]))
    x1, y1 = int(round(son[0])), int(round(son[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    hata = dx + dy
    noktalar = []
    while True:
        noktalar.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return noktalar
        e2 = 2 * hata
        if e2 >= dy:
            hata += dy
            x0 += sx
        if e2 <= dx:
            hata += dx
            y0 += sy


def _maks_aralikla_bol(noktalar, maks_aralik_px, maks_wp, gecilebilir_tam=None):
    """Guvenli rota segmentlerini izinli azami aralikla bol.

    String-pulling iki uzak koseyi tek dogru parcasina indirebilir. Dogru
    C-uzayinda guvenli olsa bile IKA'nin sonraki hedefi onlarca metre uzakta
    kalir ve takip hatasi buyur. Ara noktalar, zaten gorus hatti dogrulanmis
    segmentlerin uzerine konur.

    ``maks_wp`` haberlesme/arayuz icin yumusak bir hedeftir. Azami aralik
    guvenlik kuralidir; ikisi celisirse rota seyreltilmez.
    """
    if len(noktalar) < 2 or maks_aralik_px <= 0:
        return list(noktalar)

    bolunmus = [tuple(map(int, map(round, noktalar[0])))]
    for bas, son in zip(noktalar, noktalar[1:]):
        if gecilebilir_tam is None:
            bx, by = bas
            sx, sy = son
            uzaklik = float(np.hypot(sx - bx, sy - by))
            adim_sayisi = max(1, int(np.ceil(uzaklik / maks_aralik_px)))
            for adim in range(1, adim_sayisi + 1):
                t = adim / adim_sayisi
                nokta = (int(round(bx + (sx - bx) * t)),
                         int(round(by + (sy - by) * t)))
                if nokta != bolunmus[-1]:
                    bolunmus.append(nokta)
            continue

        # Tam sayiya yuvarlanmis ara uclar farkli bir Bresenham cizgisi
        # olusturup serbest alan sinirina degiyordu. Ana guvenli cizginin
        # piksellerinden secip her yeni parcayi tekrar denetliyoruz.
        cizgi = _bresenham_noktalari(bas, son)
        i = 0
        son_i = len(cizgi) - 1
        # N adet 8-komsu adimda en kotu uzaklik sqrt(2)*N'dir.
        en_cok_adim = max(1, int(np.floor(maks_aralik_px / np.sqrt(2))))
        while i < son_i:
            aday_i = min(son_i, i + en_cok_adim)
            while aday_i > i and not _gorus_hatti(bolunmus[-1], cizgi[aday_i],
                                                   gecilebilir_tam):
                aday_i -= 1
            if aday_i == i:
                # Normalde ana cizgi C-uzayinda oldugu icin bu dala dusmez;
                # sonraki guvenlik kapisi yine de ihlali reddeder.
                aday_i = min(son_i, i + 1)
            nokta = cizgi[aday_i]
            if nokta != bolunmus[-1]:
                bolunmus.append(nokta)
            i = aday_i

    if len(bolunmus) > maks_wp:
        logger.warning(
            "Rota %d waypoint gerektiriyor (yumusak hedef: %d); "
            "azami aralik guvenligi icin seyreltilmedi.",
            len(bolunmus), maks_wp,
        )
    return bolunmus


def yol_duzelt(yol_px, gecilebilir_tam, *, wp_aralik_px=WP_ARALIK_M,
              aci_esigi_derece=15.0, maks_wp=MAKS_WP):
    """Gorus-hatti string-pulling + kose secimi + azami waypoint araligi.
    gecilebilir_tam'a karsi DOGRULANIR — asla korlemesine kisaltma yapilmaz."""
    if len(yol_px) < 2:
        return list(yol_px)

    # 1) gorus hatti ile azalt
    sadelesmis = [yol_px[0]]
    i = 0
    n = len(yol_px)
    while i < n - 1:
        j = n - 1
        while j > i + 1 and not _gorus_hatti(yol_px[i], yol_px[j], gecilebilir_tam):
            j -= 1
        sadelesmis.append(yol_px[j])
        i = j

    # 2) mesafe VEYA aci ile decimasyon (aci sarti kosk kesmeyi engeller)
    if len(sadelesmis) <= 2:
        return _maks_aralikla_bol(sadelesmis, wp_aralik_px, maks_wp, gecilebilir_tam)

    tutulan = [sadelesmis[0]]
    for k in range(1, len(sadelesmis) - 1):
        onceki = tutulan[-1]
        simdiki = sadelesmis[k]
        sonraki = sadelesmis[k + 1]
        mesafe = np.hypot(simdiki[0] - onceki[0], simdiki[1] - onceki[1])
        v1 = np.array(simdiki) - np.array(onceki)
        v2 = np.array(sonraki) - np.array(simdiki)
        aci = 0.0
        if np.linalg.norm(v1) > 1e-6 and np.linalg.norm(v2) > 1e-6:
            cos_aci = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            aci = np.degrees(np.arccos(np.clip(cos_aci, -1, 1)))
        if mesafe >= wp_aralik_px or aci >= aci_esigi_derece:
            tutulan.append(simdiki)
    tutulan.append(sadelesmis[-1])

    return _maks_aralikla_bol(tutulan, wp_aralik_px, maks_wp, gecilebilir_tam)


def rota_dogrula(waypoints_px, engel_ham, dt_px_tam, r_gerekli_px, *, katı=False):
    """SON GUVENLIK KAPISI — her waypoint VE her segment yeniden denetlenir,
    HAM (islenmemis) engel maskesine karsi. Bu, arabanin ustunden gecme
    hatasini yakalayacak kapidir.

    Donen: (ok, ihlaller). katı=True ise ihlalde RotaGuvenlikHatasi firlatir.
    """
    ihlaller = []
    h, w = dt_px_tam.shape

    for i, (x, y) in enumerate(waypoints_px):
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= xi < w and 0 <= yi < h):
            ihlaller.append({"tur": "waypoint", "indis": i, "px": (x, y),
                            "aciklik_px": 0.0, "gerekli_px": r_gerekli_px,
                            "engel_ham_temas": True, "sebep": "sinir_disi"})
            continue
        aciklik = float(dt_px_tam[yi, xi])
        engel_temas = bool(engel_ham[yi, xi] > 0)
        if aciklik < r_gerekli_px or engel_temas:
            ihlaller.append({"tur": "waypoint", "indis": i, "px": (x, y),
                            "aciklik_px": aciklik, "gerekli_px": r_gerekli_px,
                            "engel_ham_temas": engel_temas})

    if len(waypoints_px) >= 2:
        buf = np.zeros((h, w), np.uint8)
        pts = np.array(waypoints_px, dtype=np.int32).reshape(-1, 1, 2)
        cv2.polylines(buf, [pts], False, 1, thickness=1)
        if buf.any():
            min_aciklik = float(dt_px_tam[buf > 0].min())
            engel_kesisim = bool((engel_ham[buf > 0] > 0).any())
            if min_aciklik < r_gerekli_px or engel_kesisim:
                for i in range(len(waypoints_px) - 1):
                    seg_buf = np.zeros((h, w), np.uint8)
                    seg = np.array([waypoints_px[i], waypoints_px[i + 1]], dtype=np.int32)
                    cv2.polylines(seg_buf, [seg.reshape(-1, 1, 2)], False, 1, thickness=1)
                    if not seg_buf.any():
                        continue
                    seg_min = float(dt_px_tam[seg_buf > 0].min())
                    seg_engel = bool((engel_ham[seg_buf > 0] > 0).any())
                    if seg_min < r_gerekli_px or seg_engel:
                        ihlaller.append({"tur": "segment", "indis": i,
                                        "px": (waypoints_px[i], waypoints_px[i + 1]),
                                        "aciklik_px": seg_min, "gerekli_px": r_gerekli_px,
                                        "engel_ham_temas": seg_engel})

    ok = len(ihlaller) == 0
    if not ok:
        logger.error("rota_dogrula: %d ihlal bulundu — %s", len(ihlaller), ihlaller[:3])
        if katı:
            raise RotaGuvenlikHatasi(f"{len(ihlaller)} guvenlik ihlali: {ihlaller[:3]}")
    return ok, ihlaller


# ────────────────────────────────────────────────────────────────────────────
# 8) UST SEVIYE
# ────────────────────────────────────────────────────────────────────────────
def rota_bul(maskeler, *, mpp=None, baslangic=None, hedef=None, plan=True,
             yol_sinif_idler=(0,), engel_sinif_idler=(1,), gorsel_cikti=False,
             icerik=None):
    """Ust seviye giris noktasi. Dondugu dict:
      durum: "ACIK" | "MASKE_YOK" | "KAPALI_KOPUK" | "KAPALI_DAR"
           | "BELIRSIZ_COKLU" | "BELIRSIZ_TEK_KAPI" | "DOGRULAMA_BASARISIZ"
      yol_no: 1|2|3|None, guven: float, waypoints_px: [(x,y),...]

    icerik: letterbox tuvalindeki gercek goruntu dikdortgeni ``(x0,y0,w,h)``.
      ``None`` geriye uyumlu olarak tum tuvali icerik sayar. Verilen kutu
      gecersizse fail-closed bos ROI olur. Kutu serbest alani yalniz daraltir ve
      varsayilan baslangic/hedef bantlarini konumlandirir.
    """
    import time
    t0 = time.perf_counter()
    sonuc = serbest_alan(maskeler, mpp=mpp, yol_sinif_idler=yol_sinif_idler,
                         engel_sinif_idler=engel_sinif_idler, icerik=icerik)
    t1 = time.perf_counter()
    olc = sonuc["olcek"]

    adaylar, tani = koridor_adaylari(sonuc["dt_px"], olc["r_gerekli_px"],
                                     baslangic, hedef, icerik=sonuc["icerik"])
    t2 = time.perf_counter()

    cikti = {
        "durum": None, "yol_no": None, "guven": 0.0, "sebep": "",
        "waypoints_px": [], "darbogaz_m": None, "adaylar": adaylar,
        "en_iyi_aday": None, "ihlaller": [],
        "sure_ms": {"costmap": round((t1 - t0) * 1000, 2),
                    "koridor": round((t2 - t1) * 1000, 2)},
    }
    if gorsel_cikti:
        cikti.update({"serbest": sonuc["serbest"], "engel": sonuc["engel_ham"],
                     "dt_px": sonuc["dt_px"]})

    if not adaylar:
        cikti["durum"] = tani.get("sebep", "MASKE_YOK")
        cikti["sebep"] = "Serbest alanda gecerli kapi bulunamadi."
        return cikti

    if tani["n_kapi"] == 1:
        cikti["durum"] = "BELIRSIZ_TEK_KAPI"
        cikti["sebep"] = "Yalniz bir kapi tespit edildi — 3 guzergah ayirt edilemedi."
        cikti["en_iyi_aday"] = adaylar[0]
        return cikti

    guven, kazanan = _guven_hesapla(adaylar, olc["r_gerekli_m"], olc["mpp"])
    gecebilenler = [a for a in adaylar if a["gecilebilir"]]

    if not gecebilenler:
        # hicbiri gecilebilir degil: KOPUK mu DAR mi ayir
        durum = "KAPALI_DAR" if any(a["bilesen_alan"] > 0 for a in adaylar) else "KAPALI_KOPUK"
        cikti["durum"] = durum
        cikti["sebep"] = "Hicbir koridor gerekli aciklikta gecilebilir degil."
        cikti["en_iyi_aday"] = max(adaylar, key=lambda a: a["kapi_genislik_px"], default=None)
        return cikti

    if tani["belirsiz"] and tani["n_kapi"] != 3:
        cikti["durum"] = "BELIRSIZ_COKLU"
        cikti["sebep"] = f"{tani['n_kapi']} kapi tespit edildi (3 beklenir)."
        cikti["en_iyi_aday"] = kazanan
        cikti["guven"] = guven
        return cikti

    # T90 · ETIKET COKUSMASI FAIL-CLOSED (bagimsiz denetim bulgusu, D-146).
    # `serit_no()` COK-BIRE bir eslemedir: iki AYRI kapi ayni serit numarasini
    # alabilir. Eski sema (n_kapi==3 -> i+1) bunu farkli numara UYDURARAK
    # gizliyordu, yani `ACIK` yolunda `road` HIC belirsiz olamazdi; T90 bu
    # durumu MUMKUN kildi. Kazananin numarasini baska bir GECILEBILIR kapi da
    # tasiyorsa yayinlanan `road` HANGI koridorun dogrulandigini SOYLEMEZ ve
    # `comms/ika_receiver.py:11` -> `plan_path(road)` planlayicinin
    # REDDETMEDIGI degil, SECMEDIGI koridora surebilir. Bu fail-dangerous'tur;
    # karar VERILMEZ.
    #
    # Kontrol DAR tutulur: yalnizca KAZANANIN etiketini paylasan GECILEBILIR
    # kapilar sayilir. Gecilemez bir kapinin ayni numarayi tasimasi belirsizlik
    # YARATMAZ (IKA zaten gecilebilir olani surer), genis bir kontrol bosuna
    # yetenek yakardi.
    ayni_etiketli = [a for a in gecebilenler
                     if a["etiket"] == kazanan["etiket"]]
    if len(ayni_etiketli) > 1:
        cikti["durum"] = "BELIRSIZ_COKLU"
        cikti["sebep"] = (
            f"{len(ayni_etiketli)} gecilebilir kapi ayni seridi "
            f"({kazanan['etiket']}) gosteriyor — koridor ayirt edilemedi.")
        cikti["en_iyi_aday"] = kazanan
        cikti["guven"] = guven
        return cikti

    cikti["yol_no"] = kazanan["etiket"]
    cikti["guven"] = guven
    cikti["darbogaz_m"] = round(kazanan["darbogaz_px"] * olc["mpp"], 3)
    cikti["durum"] = "ACIK"

    if not plan:
        return cikti

    h, w = sonuc["sekil"]

    # --- ROI kisitlamasi: A*'i TUM goruntude degil, baslangic<->hedefi
    # birbirine baglayan bilesenin sinirlayici kutusunda kostur. Sartname
    # ucusunda kare 300x300 m UB icinde yalniz 50x50 m HTAB kullanilabilir
    # oldugundan bu genelde buyuk bir hizlanma saglar (sentetik testte HTAB
    # tuvali doldurdugu icin kazanc kucuk gorunur, gercek karede buyuktur).
    gecilebilir_tam_bool = (sonuc["dt_px"] >= olc["r_gerekli_px"]).astype(np.uint8)
    tohum_a_tam = _tohum_maske(
        baslangic, h, w, "alt", icerik=sonuc["icerik"])
    tohum_b_tam = _tohum_maske(
        hedef, h, w, "ust", icerik=sonuc["icerik"])
    n_cc, etiket_cc = cv2.connectedComponents(gecilebilir_tam_bool, 8)
    ea = set(np.unique(etiket_cc[(tohum_a_tam > 0) & (gecilebilir_tam_bool > 0)])) - {0}
    eb = set(np.unique(etiket_cc[(tohum_b_tam > 0) & (gecilebilir_tam_bool > 0)])) - {0}
    ortak = ea & eb
    pay_px = int(round(2 * olc["r_gerekli_px"]))
    if ortak:
        bilesen_id = next(iter(ortak))
        ys_roi, xs_roi = np.nonzero(etiket_cc == bilesen_id)
        y0r, y1r = max(0, int(ys_roi.min()) - pay_px), min(h, int(ys_roi.max()) + pay_px + 1)
        x0r, x1r = max(0, int(xs_roi.min()) - pay_px), min(w, int(xs_roi.max()) + pay_px + 1)
    else:
        y0r, y1r, x0r, x1r = 0, h, 0, w

    # Girdi maskesi her zaman HEDEF_M_HUCRE cozunurlugunde gelmez (ornegin
    # ortomozaik ~5.5 cm/px). Plan izgarasinin adimi, gercek kaynak olceginden
    # turetilmeli; aksi halde A* maliyeti ile piksel geometrisi farkli olur.
    ds = max(1, int(round(olc["plan_m_hucre"] / olc["mpp"])))
    dt_roi = sonuc["dt_px"][y0r:y1r, x0r:x1r]
    dt_plan, _ = plan_izgarasi(dt_roi, None, ds)
    if dt_plan.size == 0:
        cikti["sebep"] += " (plan izgarasi bos)"
        return cikti

    gecilebilir_plan = dt_plan >= olc["r_gerekli_px"]
    adim_m = ds * olc["mpp"]
    aciklik_m = np.minimum(dt_plan * olc["mpp"], DOYUM_CARPANI_M)

    h2, w2 = gecilebilir_plan.shape
    tohum_a_roi = tohum_a_tam[y0r:y1r, x0r:x1r]
    tohum_b_roi = tohum_b_tam[y0r:y1r, x0r:x1r]
    tohum_a = _tohum_plan_izgarasi(tohum_a_roi, h2, w2, ds)
    tohum_b = _tohum_plan_izgarasi(tohum_b_roi, h2, w2, ds)

    t3 = time.perf_counter()
    yol_izgara = astar(gecilebilir_plan, aciklik_m, tohum_b, tohum_a,
                       adim_m=adim_m, r_gerekli_m=olc["r_gerekli_m"])
    t4 = time.perf_counter()
    cikti["sure_ms"]["astar"] = round((t4 - t3) * 1000, 2)
    cikti["sure_ms"]["roi"] = f"{x1r-x0r}x{y1r-y0r}"

    if yol_izgara is None:
        cikti["durum"] = "KAPALI_DAR"
        cikti["sebep"] = "Karar 'ACIK' ama A* plan izgarasinda yol bulamadi (tutarsizlik)."
        cikti["yol_no"] = None
        return cikti

    # plan hucre -> ROI pikseli -> TAM goruntu pikseli (x0r,y0r ofseti geri eklenir)
    yol_px_kaba = [(x0r + int((c + 0.5) * ds), y0r + int((r + 0.5) * ds)) for r, c in yol_izgara]

    yol_px = []
    for x, y in yol_px_kaba:
        pay = ds
        x0, x1 = max(0, x - pay), min(w, x + pay + 1)
        y0, y1 = max(0, y - pay), min(h, y + pay + 1)
        pencere = sonuc["dt_px"][y0:y1, x0:x1]
        if pencere.size:
            ly, lx = np.unravel_index(np.argmax(pencere), pencere.shape)
            yol_px.append((x0 + lx, y0 + ly))
        else:
            yol_px.append((x, y))

    # DIKKAT: string-pulling icin "serbest" (ham maske) DEGIL, C-UZAYI serbest
    # kumesi (dt_px >= r_gerekli) kullanilmali. Aksi halde gorus-hatti kisayolu
    # koridor KENARINA (aciklik ~1 px) yapisan bir duz cizgiyi "gorunur" sayar —
    # rota_dogrula sonra bunu haklı olarak reddeder. Ilk denemede tam bu bulundu.
    gecilebilir_tam = sonuc["dt_px"] >= olc["r_gerekli_px"]
    waypoints = yol_duzelt(yol_px, gecilebilir_tam, wp_aralik_px=olc["wp_aralik_px"])
    t5 = time.perf_counter()
    cikti["sure_ms"]["duzelt"] = round((t5 - t4) * 1000, 2)

    # Harici tohumlar gercek KB/HB koordinatlarini temsil eder. A* plan
    # izgarasinin hucre merkezinden baslayip bitmesi halinde IKA'ya sonradan
    # dogrulanmamis kisa bir ilk/son segment eklenmis olurdu. Ankora olan
    # baglantiyi burada ayni C-uzayina karsi kontrol edip rota parcasina dahil
    # ediyoruz; guvenli degilse hic rota vermiyoruz.
    if baslangic is not None:
        waypoints, neden = _ankoru_ekle(
            waypoints, _tohum_merkezi(tohum_a_tam), True, gecilebilir_tam)
        if waypoints is None:
            cikti["durum"] = "DOGRULAMA_BASARISIZ"
            cikti["yol_no"] = None
            cikti["sebep"] = f"KB ankoru eklenemedi: {neden}."
            return cikti
    if hedef is not None:
        waypoints, neden = _ankoru_ekle(
            waypoints, _tohum_merkezi(tohum_b_tam), False, gecilebilir_tam)
        if waypoints is None:
            cikti["durum"] = "DOGRULAMA_BASARISIZ"
            cikti["yol_no"] = None
            cikti["sebep"] = f"HB ankoru eklenemedi: {neden}."
            return cikti
    # Ankorlar plan izgarasinin ilk/son merkezinden biraz uzakta olabilir.
    # IKA takip hatasinin buyumemesi icin bunlar dahil tum segmentlerdeki
    # waypoint araligi sinirini yeniden uygula.
    waypoints = _maks_aralikla_bol(
        waypoints, olc["wp_aralik_px"], MAKS_WP, gecilebilir_tam)

    ok, ihlaller = rota_dogrula(waypoints, sonuc["engel_ham"], sonuc["dt_px"],
                                olc["r_gerekli_px"], katı=False)
    if not ok:
        # Yerel distance-transform zirvesine kaydirma + string-pulling nadiren
        # raster kenarinda farkli bir pikselden gecebilir. A*'in min-havuzlu
        # plan hucre merkezleri ise dogrudan C-uzayinda kalir; kisaltmadan
        # once bu muhafazakar rotayi son kez dene.
        ham_waypoints = list(yol_px_kaba)
        ham_ankor_hatasi = None
        if baslangic is not None:
            ham_waypoints, ham_ankor_hatasi = _ankoru_ekle(
                ham_waypoints, _tohum_merkezi(tohum_a_tam), True, gecilebilir_tam)
        if ham_waypoints is not None and hedef is not None:
            ham_waypoints, ham_ankor_hatasi = _ankoru_ekle(
                ham_waypoints, _tohum_merkezi(tohum_b_tam), False, gecilebilir_tam)
        if ham_waypoints is None:
            # rota_dogrula() bos listeyi dogal olarak temiz sayar; ankorsuz
            # muhafazakar rota bunu gecersiz kilacak sekilde isaretlenir.
            ham_waypoints = []
        ham_ok, ham_ihlaller = rota_dogrula(
            ham_waypoints, sonuc["engel_ham"], sonuc["dt_px"],
            olc["r_gerekli_px"], katı=False,
        )
        if ham_ankor_hatasi:
            ham_ok = False
            ham_ihlaller = [{"tur": "ankor", "sebep": ham_ankor_hatasi}]
        if ham_ok:
            logger.warning(
                "Duzeltilmis rota raster denetiminden gecmedi; "
                "muhafazakar A* hucre merkezleri kullaniliyor."
            )
            waypoints, ok, ihlaller = ham_waypoints, True, []
        else:
            ihlaller = ham_ihlaller
    t6 = time.perf_counter()
    cikti["sure_ms"]["dogrulama"] = round((t6 - t5) * 1000, 2)
    cikti["ihlaller"] = ihlaller

    if not ok:
        cikti["durum"] = "DOGRULAMA_BASARISIZ"
        cikti["yol_no"] = None
        cikti["sebep"] = f"Rota {len(ihlaller)} guvenlik ihlali icerdi — reddedildi."
        cikti["waypoints_px"] = []
        return cikti

    cikti["waypoints_px"] = waypoints
    return cikti


# ────────────────────────────────────────────────────────────────────────────
# 9) GERIYE UYUM KOPRUSU — analyze_path ile AYNI donus sekli
# ────────────────────────────────────────────────────────────────────────────
def analyze_path_uyumlu(maskeler_veya_trav, n_waypoints=8, return_clean=False,
                        min_area_ratio=0.01, **kw):
    """rpi_inference.analyze_path ile AYNI donus sekli — cagri yerleri
    TEK SATIRLIK import degisikligiyle bu fonksiyona gecebilsin diye.

    maskeler_veya_trav: {sinif_id: mask} dict (YENI, engel-farkinda) VEYA
    bare (h,w) traversable mask (ESKI, geriye uyum — engelsiz varsayilir).
    """
    if isinstance(maskeler_veya_trav, dict):
        maskeler = maskeler_veya_trav
    else:
        maskeler = {0: maskeler_veya_trav}

    rota_kw = dict(kw)
    if return_clean:
        # Temiz maske karar ile AYNI ROI sozlesmesinden gelmelidir. Burada
        # serbest alani yeniden kurmak, icerik kutusunu dusurup dolguyu yeniden
        # serbest gosterebilirdi.
        rota_kw["gorsel_cikti"] = True
    sonuc = rota_bul(maskeler, plan=True, **rota_kw)
    open_path = sonuc["yol_no"]
    guven = sonuc["guven"]
    waypoints = [tuple(wp) for wp in sonuc["waypoints_px"]]

    if sonuc["durum"] != "ACIK":
        h, w = next(iter(maskeler.values())).shape
        bos = np.zeros((h, w), np.uint8)
        if return_clean:
            return None, 0.0, [], bos
        return None, 0.0, []

    if return_clean:
        clean = sonuc["serbest"]
        return open_path, guven, waypoints, clean
    return open_path, guven, waypoints


# ────────────────────────────────────────────────────────────────────────────
# TAHMINLER — ucustan once OLCULMELI (varsayim olarak birakilmasin)
#
# 1. TAKIP_HATA_M = 0.40 — saf varsayim, r_gerekli'nin EN BUYUK terimi.
#    Sim'den olcum: komut verilen cizgiye IKA'nin maksimum yanal sapmasi.
# 2. IKA_GENISLIK_M = 0.70 — simulation/models/ika/model.sdf'ten turetildi.
#    GERCEK aracin olcusu FARKLI olabilir; sartname yalniz 1m x 1m IKA-KB
#    kutusuna sigmasini zorunlu kiliyor.
# 3. Gercek HTAB koridor genislikleri sartnamede YOK. Yalniz "esik fazla dar
#    koridoru reddediyor mu" sagligi icin kullanildi, tasarim girdisi degil.
# 4. LAMBDA_ACIKLIK=3.0, US_ACIKLIK=2.0 — gerekceli (4x azami ceza, karesel
#    rampa) ama AMPIRIK DEGIL. test_rota_sentetik.py'deki yer gercegi merkez
#    cizgilerine karsi taranip fit edilebilir.
# 5. Jetson ~= 2x masaustu (saf Python) — 5 Agustos'ta olculecek.
# ────────────────────────────────────────────────────────────────────────────
