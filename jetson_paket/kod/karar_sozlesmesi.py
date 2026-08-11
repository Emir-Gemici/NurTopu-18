"""NEDEN: Rota gecerlilik esikleri tum karar ve yayin yollarinda tek kaynaktan
okunmazsa ayni guven degeri bir yerde OPEN_ROUTE, baska yerde NO_ROUTE uretebilir.

Degerlerin mimari gerekcesi ve baglayici tanimi CONTRACTS.md SS6.3'tedir.
Bu modul yalniz kodun kullandigi tek-kaynak sabitleri tasir; cagri yerlerine
ciplak sayi yazilmaz.
"""

import math
from numbers import Real

# K-A: Secilen koridor, icerik kutusunun baslangic/hedef uc bantlarina temas eder.
HEDEF_BANT_ORANI = 0.08
BANT_TEMAS_MIN_ORANI = 0.02

# K-B: Bunun altindaki rota karari yayinlanamaz.
# 2026-08-10: 0.50 -> 0.20. Ilk deger SENTETIK sahne guveninden (0,797/1,000)
# turetilmisti; gercek 67 karede olculen dagilim min=0,244 p50=0,307 max=0,352
# std=0,030 oldugu icin 0.50 esigi %100 cekimserlik uretiyordu (D-37, D-38).
# K-B secici bir kapi DEGIL, taban koruyucusudur: guven=0.0 yayinini engeller,
# gercek kararlari elemez. Guvenligin agirligi K-A'dadir. Gerekce: CONTRACTS SS6.3.
ROTA_GUVEN_ESIGI = 0.20

# CONTRACTS.md SS6.4: analyze_path witness A* denemelerinin TOPLAM plan hucre
# butcesi. Butce asilirsa daha ince izgaraya inmek yerine fail-closed ret verilir;
# GUI worker'i tam cozunurluk A* ile saniyelerce bloke edilemez.
ROTA_PLAN_MAKS_HUCRE = 32_768

# T32 / REVIEW_LOG D-41: rota guveni ROTANIN DARBOGAZINDAN olculur.
# Eski metrik (`in_third / bx.size`) koridorun UST BANDINDAN hesaplaniyordu;
# olculdu, tespit kotulestikce YUKSELIYORDU (az piksel tek ucte-bire duserse
# oran 1,0) ve enjekte-kapi deneyinde kapi sol/orta/sag gezerken deger hic
# degismiyordu (0,326 / 0,326 / 0,326).
#
# Yeni tanim: rotanin LINE_8 pikselleri boyunca olculen EN KUCUK aciklik
# (distance transform yaricapi), icerik genisligine oranlanir. Mutlak piksel
# degil ORAN — cozunurluk degisince olcut kaymaz (CONTRACTS SS8).
# Bu aciklikta guven 1,0'a doyar; kalibrasyon olcumu REVIEW_LOG D-42'de.
ROTA_DARBOGAZ_TAM_ORANI = 0.035


def serit_no(x, icerik_x0, icerik_w):
    """Yatay koordinati serit numarasina cevir (1=sol, 2=orta, 3=sag).

    Sinirlar kare tuvalden degil letterbox ICERIK kutusundan hesaplanir
    (CONTRACTS SS8). Tek kaynak: hem karar hem gorsellestirme burayi cagirir.
    """
    if icerik_w <= 0:
        return 2
    if x < icerik_x0 + icerik_w / 3.0:
        return 1
    if x < icerik_x0 + 2.0 * icerik_w / 3.0:
        return 2
    return 3


def rota_darbogaz_guveni(darbogaz_px, icerik_w):
    """Rotanin en dar noktasindaki acikligi [0,1] guvenine cevir.

    ``darbogaz_px`` rota uzerindeki en kucuk distance-transform degeridir
    (icten tegets cemberin yaricapi; koridor genisligi ~ 2x bu deger).
    Fail-closed: gecersiz/negatif girdi 0.0 doner.
    """
    if isinstance(darbogaz_px, bool) or not isinstance(darbogaz_px, Real):
        return 0.0
    d = float(darbogaz_px)
    if not math.isfinite(d) or d <= 0.0:
        return 0.0
    tam = float(icerik_w) * ROTA_DARBOGAZ_TAM_ORANI
    if not math.isfinite(tam) or tam <= 0.0:
        return 0.0
    return round(min(1.0, d / tam), 3)

# CONTRACTS.md SS6.4: karar reddi sebep kodlari. Cagri yerlerine ciplak
# string yazilmaz; tum uretim ve ekran yollari bu tek kaynagi kullanir.
OLCEK_YOK_SEBEBI = "OLCEK_YOK"
ZEMIN_MASKESI_SUPHELI_SEBEBI = "ZEMIN_MASKESI_SUPHELI"
MASKE_YOK_SEBEBI = "MASKE_YOK"
BILESEN_YOK_SEBEBI = "BILESEN_YOK"
UC_BANT_TEMAS_YOK_SEBEBI = "UC_BANT_TEMAS_YOK"
ALAN_YETERSIZ_SEBEBI = "ALAN_YETERSIZ"
GORUS_HATTI_KOPUK_SEBEBI = "GORUS_HATTI_KOPUK"
KENAR_GUVENSIZ_SEBEBI = "KENAR_GUVENSIZ"
DUSUK_GUVEN_SEBEBI = "DUSUK_GUVEN"

ROTA_RET_SEBEPLERI = frozenset({
    OLCEK_YOK_SEBEBI,
    ZEMIN_MASKESI_SUPHELI_SEBEBI,
    MASKE_YOK_SEBEBI,
    BILESEN_YOK_SEBEBI,
    UC_BANT_TEMAS_YOK_SEBEBI,
    ALAN_YETERSIZ_SEBEBI,
    GORUS_HATTI_KOPUK_SEBEBI,
    KENAR_GUVENSIZ_SEBEBI,
    DUSUK_GUVEN_SEBEBI,
})


def _guven_metin(deger):
    """Esik altini esigin kendisine yuvarlamadan insan-okur yaz."""
    uc_hane = f"{deger:.3f}"
    if (deger < ROTA_GUVEN_ESIGI
            and uc_hane == f"{ROTA_GUVEN_ESIGI:.3f}"):
        return f"{deger:.17g}"
    return uc_hane


def hedef_bant_yuksekligi(icerik_h):
    """CONTRACTS SS6.3/K-A bant yuksekligini piksele cevir."""
    return max(1, int(int(icerik_h) * HEDEF_BANT_ORANI))


def bant_temasi_gereken_px(icerik_w):
    """K-A'nin oransal yatay temas alt sinirini tam piksele cevir."""
    return max(1, int(math.ceil(int(icerik_w) * BANT_TEMAS_MIN_ORANI)))


def bant_temasi_yeterli_mi(temas_px, icerik_w):
    """Yatay temas genisligi K-A'nin oransal alt sinirini geciyor mu?"""
    return int(temas_px) >= bant_temasi_gereken_px(icerik_w)


def rota_guven_reddi(guven):
    """Gecerli guvende None, aksi halde kanonik ``(sebep, detay)`` doner.

    Bool, sayisal olmayan deger, NaN/sonsuz ve [0,1] disi degerler fail-closed
    reddedilir. Esigin kendisi gecerlidir; yalniz alti reddedilir.
    """
    if isinstance(guven, bool) or not isinstance(guven, Real):
        return (DUSUK_GUVEN_SEBEBI,
                f"Rota guveni gecersiz ({guven!r}); gereken >= "
                f"{ROTA_GUVEN_ESIGI:.3f}.")
    deger = float(guven)
    if not math.isfinite(deger) or not 0.0 <= deger <= 1.0:
        return (DUSUK_GUVEN_SEBEBI,
                f"Rota guveni gecersiz ({deger!r}); gereken >= "
                f"{ROTA_GUVEN_ESIGI:.3f}.")
    if deger < ROTA_GUVEN_ESIGI:
        return (DUSUK_GUVEN_SEBEBI,
                f"Rota guveni {_guven_metin(deger)}; gereken >= "
                f"{ROTA_GUVEN_ESIGI:.3f}.")
    return None


def rota_guveni_yeterli_mi(guven):
    """Rota guveni K-B'ye gore OPEN_ROUTE icin yeterli mi?"""
    return rota_guven_reddi(guven) is None


# ════════════════════════════════════════════════════════════════════════════
# T43 · HALKA 5 — OLCEK (mpp) SOZLESMESI   (CONTRACTS.md SS5, SS11.2 Halka 5)
# ════════════════════════════════════════════════════════════════════════════
# NEDEN BURADA: bu halka D-22'den beri SAHIPSIZ'di. Saha kod yolunda `mpp`
# ureten hicbir kod yoktu; tek kaynak `simulation/scripts/iha_haritala.py:66`
# sabitiydi ve SS11.1/1 geregi sahip SAYILMAZ (saha paketinde de yok).
#
# 🔴 SESSIZ VARSAYIM — kapatilan kusur: `costmap_path_finder.olcek_px(None)`
# `m = 1.0` alip `r_gerekli_px` degerini 1,10 PIKSEL uretiyordu. Bu "olcek yok"
# demek DEGIL, "olcek 1 metre/piksel" demektir; gercek deger kompozit arenada
# 1,10 / 0,0868 = 12,7 px. Yani govde acikligi sessizce ~11 KAT kuculuyor ve
# hicbir uyari basilmiyordu.
SARTNAME_ASGARI_IRTIFA_M = 30.0   # sartname SS5.3.2 asgari gorev irtifasi
IRTIFA_MAKUL_UST_M = 200.0        # ustu telemetri hatasi sayilir (fail-closed)


def mpp_irtifadan(irtifa_m, goruntu_genislik_px, *, yatay_fov_derece=None,
                  odak_px=None):
    """Nadir (90 derece) kamerada metre/piksel uret. Uretilemezse ``None``.

    Iki kaynak — biri verilmelidir:
      · FOV yolu  : ``mpp = 2 * h * tan(FOV_yatay / 2) / W_px``
      · Odak yolu : ``mpp = h / f_px``   (pinhole; f piksel cinsinden)

    ``irtifa_m`` saha kaynagi MAVLink ``GLOBAL_POSITION_INT.relative_alt``tir
    (mm); `comms/inis_kaniti.py:143` ayni alani zaten okuyor — ikinci bir
    telemetri yolu turetilmez.

    FAIL-CLOSED: gecersiz/eksik girdi, bool, NaN, sonsuz, sifir veya negatif
    deger, makul irtifa bandi disi olcum -> ``None``. "Tahmini olcek" DONMEZ.
    """
    def _sayi(x):
        if isinstance(x, bool) or not isinstance(x, Real):
            return None
        d = float(x)
        return d if math.isfinite(d) else None

    h = _sayi(irtifa_m)
    w = _sayi(goruntu_genislik_px)
    if h is None or w is None or h <= 0.0 or w <= 0.0:
        return None
    if h > IRTIFA_MAKUL_UST_M:
        return None
    f = _sayi(odak_px)
    if f is not None and f > 0.0:
        return h / f
    fov = _sayi(yatay_fov_derece)
    if fov is not None and 0.0 < fov < 180.0:
        return (2.0 * h * math.tan(math.radians(fov) / 2.0)) / w
    return None


def olcek_gecerli_mi(mpp):
    """`mpp` gercek bir olcek mi? Bool/NaN/sonsuz/<=0 fail-closed reddedilir."""
    if isinstance(mpp, bool) or not isinstance(mpp, Real):
        return False
    d = float(mpp)
    return math.isfinite(d) and d > 0.0


def rota_olcek_reddi(mpp, *, irtifa_m=None):
    """Gorev yolunda olcek yoksa kanonik ``(sebep, detay)``; varsa ``None``.

    CONTRACTS SS11.3 Halka 5 olcutu: *"`mpp` turetilemiyorsa halka OLCEK_YOK
    dondurecek ve rota URETILMEYECEK."* Sessiz varsayilan YASAK.
    """
    if not olcek_gecerli_mi(mpp):
        return (OLCEK_YOK_SEBEBI,
                f"Olcek (mpp) turetilemedi ({mpp!r}); irtifa+FOV/odak "
                "gerekli. Olceksiz kipte govde acikligi dogrulanamaz, "
                "rota yayinlanmaz.")
    if irtifa_m is not None:
        h = float(irtifa_m) if olcek_gecerli_mi(irtifa_m) else None
        if h is not None and h < SARTNAME_ASGARI_IRTIFA_M:
            # Ret DEGIL, olculen makullük notu: IHA inis/kalkista da kare uretir.
            return None
    return None


def r_gerekli_piksel(mpp, r_gerekli_m):
    """Fiziksel gerekli acikligi piksele cevir; olcek yoksa ``None``.

    ``None`` donusu "kisit yok" DEGIL, "kisit UYGULANAMAZ" demektir; cagiran
    ya olceksiz kipte oldugunu acikca kaydeder ya da OLCEK_YOK ile reddeder.
    """
    if not olcek_gecerli_mi(mpp):
        return None
    return float(r_gerekli_m) / float(mpp)


# ════════════════════════════════════════════════════════════════════════════
# T48 · ZEMIN MASKESI SAGLAMLIK KAPISI   (CONTRACTS.md SS6.4)
# ════════════════════════════════════════════════════════════════════════════
# NEDEN: v21 bu alanda pratikte "arac mi, degil mi" ayiricisidir; CATI, CIM ve
# TOPRAK hepsi zemin sinifina duser. Sistem maskenin coktugunu ANLAMIYOR ve
# rotayi yine de uretiyordu — kullanici hakem ekraninda bina catisi uzerinden
# gecen bir rota gordu. Karar zinciri bunu yakalayamaz cunku maske "dolu"
# gorunur; her yapisal kapi (K-A, C-uzayi, K-B) memnun kalir.
#
# OLCUM — kaplama := zemin (sinif 0) maskesinin ICERIK kutusundaki piksel orani.
# Uretim zinciri (`_preprocess` + `get_masks` + `_maskeleri_icerige_kirp`),
# conf=0.30. Uc BAGIMSIZ mesru kaynak ve iki cokmus kume olculdu:
#
#   MESRU (kapi ATESLEMEMELI)                          n     p50    p95    MAKS
#     sentetik arena YER GERCEGI (etiket poligonlari)  60   %11,7  %22,1  %39,0
#     sentetik arena, v17 + v21 model ciktisi         120   %11,8  %23,2  %38,7
#     genel kapinin KENDI 15 sahnesi                   15   %36,4    —    %42,6
#
#   COKMUS (kapi ATESLEMELI)                           n     p50           MIN
#     v21 otopark (cati/cim yesil)                     67   %79,9         %76,7
#     v21 kompozit arena                                7   %82,7         %76,0
#
# Iki kip arasinda %42,6 ile %76,0 arasinda GENIS ve BOS bir aralik var.
# TAVAN = 0.55 secildi:
#   · olculen en yuksek MESRU kaplamanin (%42,6) 1,29 kati — maske gurultusu
#     icin pay birakir, genel kapinin kendi sahnelerini reddetmez;
#   · olculen en dusuk COKMUS kaplamanin (%76,0) 0,72 kati — cokmeyi kacirmaz;
#   · 194 model karesi + 60 yer gercegi + 15 kapi sahnesinde yanlis pozitif 0,
#     kacirma 0.
#   · Anlami: icerigin YARISINDAN fazlasi "surulebilir zemin" iddia ediliyorsa
#     maske artik sahneyi AYIRT ETMIYOR demektir.
#
# ⚠ GOREV TABLOSUNDAKI v13 SATIRI KULLANILAMADI. "v13 cokmus, kaplama %43,4"
# deniyordu; fakat (1) v13 agirligi depoda YOK, olculemedi; (2) satirin kendi
# iki sayisi tek tanim altinda tutarsiz (%43,4 ve "goruntunun %84,7'sini
# boyuyor"); (3) en onemlisi, %43,4 genel kapinin KENDI mesru sahnelerinin
# azamisinin (%42,6) yalniz 0,8 puan ustunde — o degeri yakalayan bir tavan
# `codes/test_rota_sentetik.py` 15/15 kapisini kirardi. Bu yuzden tavan
# olculebilen kaynaklardan turetildi. v13 benzeri ORTA siddetli bir cokme bu
# kapidan GECER; yakalamak icin kaplama tek basina yetmez, maskenin YAPISI
# (or. doku/renk tutarliligi) gerekir — ayri gorev.
ZEMIN_KAPLAMA_TAVANI = 0.55


def zemin_kaplamasi(trav, icerik=None):
    """Zemin maskesinin ICERIK kutusundaki piksel orani [0,1]."""
    import numpy as _np
    m = _np.asarray(trav)
    if m.ndim != 2 or m.size == 0:
        return 0.0
    h, w = m.shape
    if icerik is None:
        x0, y0, iw, ih = 0, 0, w, h
    else:
        x0 = max(0, min(w, int(icerik[0])))
        y0 = max(0, min(h, int(icerik[1])))
        iw = max(0, min(w - x0, int(icerik[2])))
        ih = max(0, min(h - y0, int(icerik[3])))
    if iw <= 0 or ih <= 0:
        return 0.0
    kutu = m[y0:y0 + ih, x0:x0 + iw]
    return float(_np.count_nonzero(kutu)) / float(iw * ih)


def zemin_maskesi_reddi(trav, icerik=None):
    """Kaplama tavani asilirsa kanonik ``(sebep, detay)``; aksi halde ``None``.

    Kapi yalniz REDDEDER — maskeye dokunmaz, serbest alani BUYUTMEZ
    (CLAUDE.md madde 15 acisindan notrdur, cunku hicbir piksel eklemez).
    """
    oran = zemin_kaplamasi(trav, icerik)
    if oran <= ZEMIN_KAPLAMA_TAVANI:
        return None
    return (ZEMIN_MASKESI_SUPHELI_SEBEBI,
            f"Zemin maskesi icerigin %{100.0 * oran:.1f}'ini kapliyor; "
            f"tavan %{100.0 * ZEMIN_KAPLAMA_TAVANI:.1f}. Maske sahneyi ayirt "
            "etmiyor (cati/cim/toprak zemin sayilmis olabilir); rota "
            "uretilmez.")
