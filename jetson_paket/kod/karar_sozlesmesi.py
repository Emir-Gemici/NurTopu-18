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
MASKE_YOK_SEBEBI = "MASKE_YOK"
BILESEN_YOK_SEBEBI = "BILESEN_YOK"
UC_BANT_TEMAS_YOK_SEBEBI = "UC_BANT_TEMAS_YOK"
ALAN_YETERSIZ_SEBEBI = "ALAN_YETERSIZ"
GORUS_HATTI_KOPUK_SEBEBI = "GORUS_HATTI_KOPUK"
KENAR_GUVENSIZ_SEBEBI = "KENAR_GUVENSIZ"
DUSUK_GUVEN_SEBEBI = "DUSUK_GUVEN"

ROTA_RET_SEBEPLERI = frozenset({
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
