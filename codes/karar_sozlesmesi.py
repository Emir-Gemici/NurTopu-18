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
KORIDOR_DEGIL_SEBEBI = "KORIDOR_DEGIL"      # T65 · D-94

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
    KORIDOR_DEGIL_SEBEBI,
})


# ════════════════════════════════════════════════════════════════════════════
# T65 · KORIDOR GENISLIK TAVANI   (CONTRACTS.md SS6.4 · REVIEW_LOG D-90/3, D-94)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (D-90 bulgu 3): karar yolunun ARENA SINIRI kavrami yok. Uretec arena
# disina bilerek ETIKETSIZ duz zemin cizer (gercekcidir; dronun gordugu arazi
# arena ile bitmez), model orayi HAKLI OLARAK zemin isaretler, karar yolu ise
# tum kareyi ucte bolup o bos kenari gecerli guzergah sayar. AYNI KUSUR GERCEK
# KAREDE DE VAR (`sartname_s9_arena.png`: izgarali arenanin disindaki toprak da
# zemin isaretleniyor). Sentetik bir yan etki DEGILDIR.
#
# ⚠ SINIRI YERELLESTIRME DENENDI VE BASARISIZ OLDU (T65 FAZ 1, D-94). Uc aday
# imza olculdu; UCU DE guvenilmez cikti ve UCU DE gercek karede coktu:
#
#   imza                n     IoU medyan   guvenilir mi   gercek karede
#   izgara cizgileri   260        0.806         HAYIR     TUM KAREYI verdi
#   moloz kapsayan k.  260        0.664         HAYIR     — (dar yanli)
#   dis cerceve        260        0.960         HAYIR     HIC sinir uretemedi
#
# Ve daha temelde: GERCEK ARENA SINIRI DIKEY DEGIL. Perspektif nedeniyle yamuk
# (sol kenar x~190 ust -> x~65 alt; sag x~920 -> x~1015). Tek bir [x0,x1]
# araligi gercek arenayi TANIMLAMAZ; indirgenemez hata ~50-60 px.
#
# BU YUZDEN SINIR YERELLESTIRILMIYOR. Onun yerine kusurun OLCULEN yapisindan
# yararlanilir: hata DEJENERE. Rota ya tamamen arena icinde ya tamamen disinda:
#
#   arena disi oran == 0.000 -> 238 kare · == 0.001 -> 1 · == 1.000 -> 10
#
# Ara deger YOKTUR. Dolayisiyla "sinir nerede" sorusunu yanitlamak GEREKMEZ;
# "bu bir koridor mu" sorusu yeterlidir.
#
# OLCUT: koridorun EN DAR yeri bir SERIDIN tamamindan genis olamaz. Sartname
# arenada UC guzergah tanimlar ve bunlar molozla ayrilir; bir seridin tamaminden
# genis bir "koridor" uc guzergahtan biri DEGILDIR — acik arazidir.
# Tavan `serit_no`nun kendi bolusumunden turetilir, ciplak sayi degildir (m.16).
#
# OLCUM (v24 · T60 kadraj · n=260 · uretim zinciri · rota uretilen 249):
#
#   kume                     darbogaz/icerik_w
#     MESRU (arena ici) 239   medyan 0.094 · p95 0.208 · MAKS 0.280
#     KUSURLU (disi)     10   0.022 · 0.028 · 0.111 · 0.170 · 0.314 · 0.353
#                             0.358 · 0.375 · 0.475 · 0.487
#
#   tavan = 1/3 (bir serit)  -> yanlis elenen MESRU 0/239 · yakalanan 5/10
#   mesru tarafa pay 0.053 (0.280 -> 0.333) · kusurlu tarafa pay 0.020
#
# ⚠ BU KISMI BIR COZUMDUR — gizlenmiyor. Kalan 5 kusurlu kare genislige gore
# MESRU karelerden AYIRT EDILEMEZ: arena disi bolge her zaman bos degildir
# (or. `sa_000068` arena disinda bir OTOPARK fotografi tasir, park cizgileriyle;
# model orada 14 px darbogazli kendi koridorunu bulur). Genislik olcutu bu
# sinifi yakalayamaz; gerceken sinir bilgisi gerekir ve o bilgi bugun YOK.
#
# ⚠ MADDE 15: bu olcut yalniz REDDEDER. Serbest alani buyutmez, maskeye
# dokunmaz, tek piksel eklemez.
SERIT_SAYISI = 3
# `serit_no` ayni bolusumu kodlar; ikisinin uyumu testle kilitlenir
# (`tests/test_koridor_genisligi.py`), boylece biri degisip digeri kalamaz.

KORIDOR_GENISLIK_TAVANI_SERIT = 1.0
# Bir koridor EN COK bir serit kadar genis olabilir. 1.0 fiziksel siniridir,
# olcumle FIT EDILMIS bir sayi degildir; olculen mesru azami (0.280) bu sinirin
# altinda kalarak onu DOGRULAR.


def koridor_genislik_tavani_px(icerik_w):
    """Bir koridorun asamayacagi darbogaz genisligi (piksel)."""
    try:
        genislik = float(icerik_w)
    except (TypeError, ValueError):
        return 0.0
    if not genislik > 0.0:
        return 0.0
    return genislik / float(SERIT_SAYISI) * KORIDOR_GENISLIK_TAVANI_SERIT


def rota_koridor_genisligi_reddi(darbogaz_px, icerik_w):
    """Darbogazi bir seritten genis olan "koridor" bir guzergah DEGILDIR.

    Kanonik ``(sebep, detay)`` doner; koridor makul genislikteyse ``None``.
    Fail-closed: olculemeyen darbogaz reddi TETIKLEMEZ — bu olcut yalniz
    POZITIF bir kanit (olculmus asiri genislik) uzerine ates eder; olcum
    yoksa karar diger kapilara birakilir.
    """
    tavan = koridor_genislik_tavani_px(icerik_w)
    if tavan <= 0.0:
        return None
    try:
        darbogaz = float(darbogaz_px)
    except (TypeError, ValueError):
        return None
    if not darbogaz > tavan:
        return None
    return (KORIDOR_DEGIL_SEBEBI,
            f"Rota darbogazi {darbogaz:.1f} px, bir seridin tamamindan "
            f"({tavan:.1f} px) genis. Bu bir guzergah degil ACIK ARAZIDIR; "
            f"rota uretilmez.")


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
# T70 / REVIEW_LOG D-98: kare olcegi yalniz bu yastan daha yeni MAVLink
# GLOBAL_POSITION_INT.relative_alt orneginden turetilebilir. Bu bir saha mesaj
# hizi varsayimi degil, azami guvenlik yasidir: daha yavas/eksik akis rotayi
# OLCEK_YOK ile fail-closed durdurur. Host monotonic saati kullanilir.
TELEMETRI_IRTIFA_TAZELIK_S = 0.50


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
# Yukaridaki tablo v21 ciktilariyla turetildi ve TAVAN = 0.55 secilmisti.
#
# ════════════════════════════════════════════════════════════════════════════
# T59 · YENIDEN KALIBRASYON: 0.55 -> 0.67   (REVIEW_LOG D-84, D-85, D-86)
# ════════════════════════════════════════════════════════════════════════════
# IKI SEY BIRDEN DEGISTI:
#   (1) Uretim modeli v24 oldu (T58) — esikler v21 ciktilarindan turetilmisti;
#   (2) elimize GERCEK ARENA karesi gecti (D-84): sartname s.9,
#       `data/arena_referans/sartname_s9_arena.png` — projenin TEK gercek arena
#       goruntusu. v24 onu DOGRU segmentliyor (gozle dogrulandi: toprak zemin
#       yesil, moloz haric, uc koridor izlenebilir).
#
# 🔴 KUSUR: 0.55 tavani DOGRU segmentlenmis GERCEK ARENAYI reddediyordu.
#       gercek arena  kaplama 0.579 > 0.55  VE  kenar 0.585 > 0.50  -> RET
#
# BAGIMSIZ OLCUM (T59, v24, uretim zinciri, conf=0.30 — KUMENIN TAMAMI):
#
#   kume                     n    kaplama min..maks    kenar min..maks
#     MESRU kadraj arena    260    0.000..0.863        0.000..0.682
#     MESRU GERCEK ARENA      1    0.579               0.585
#     COKUS otopark          67    0.770..0.866        0.579..0.971
#
#   kaplama tek basina: mesru maks 0.863 > cokus min 0.770   CAKISIK
#   kenar   tek basina: mesru maks 0.682 > cokus min 0.579   CAKISIK
#   -> HICBIR SINYAL TEK BASINA AYIRMIYOR; kapi AND birlesimidir.
#
#   esik cifti              mesru elenen      kacan cokme
#     (0.55, 0.50) ESKI      3/261             0/67   <- biri GERCEK ARENA
#     (0.67, 0.50) YENI      1/261             0/67
#
# ⚠ TAM AYRIK CIFT YOKTUR. Mimarin 220 kareli alt kumesinde (0.67, 0.50) tam
# ayirim veriyordu (D-85: mesru elenen 0/221, pay 0.062); kumenin TAMAMINDA
# vermiyor. Kalan tek elenen kare `sa_000001.jpg` (kaplama 0.856 · kenar 0.682):
# yer gercegiyle kiyaslandi — GT kaplama 0.717, IoU 0.810, ama GT kenar yalniz
# 0.359. Model o karede sinira GERCEGIN IKI KATI dayaniyor; SINIR DURUM,
# duz bir yanlis pozitif degil.
#
# ⚠ 0.67'NIN OLCULMUS BEDELI: `sa_000150.jpg` artik kapidan GECIYOR
# (kaplama 0.617 < 0.67). O karede model GERCEKTEN cokmus: GT kaplama 0.380,
# model 0.617 (+0.237), IoU 0.613, kenar 0.658 iken GT kenar 0.190. Yani bu
# yukseltme ORTA SIDDETLI cokmeye acik kapi birakir — yukaridaki v13 uyarisinin
# somut ornegidir. Kaplama+kenar bu sinifi yakalayamaz; maskenin YAPISI
# (doku/renk tutarliligi) gerekir — ayri gorev.
#
# 🔴 ESIKLER MODELE BAGLIDIR. v21 icin turetilen 0.55 v24'te YANLISTI ve gercek
# arenayi eliyordu. v24 icin turetilen 0.67 bir sonraki modelde yanlis olabilir.
# URETIM MODELI HER DEGISTIGINDE BU KALIBRASYON ZORUNLU ADIMDIR.
#
# 🔴 GERCEK ARENA TEK KAREDIR. Mesru taraf bir dagilima degil TEK NOKTAYA karsi
# olculdu. Ikinci bir gercek arena karesi geldiginde esik YENIDEN olculmelidir.
#
# ⚠ GOREV TABLOSUNDAKI v13 SATIRI KULLANILAMADI. "v13 cokmus, kaplama %43,4"
# deniyordu; fakat (1) v13 agirligi depoda YOK, olculemedi; (2) satirin kendi
# iki sayisi tek tanim altinda tutarsiz (%43,4 ve "goruntunun %84,7'sini
# boyuyor"). Bu yuzden tavan olculebilen kaynaklardan turetildi.
ZEMIN_KAPLAMA_TAVANI = 0.67


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


# T52 / REVIEW_LOG D-66: KAPLAMA TEK BASINA AYIRT ETMIYOR — olculdu.
# 218 mesru (kadraj arena) + 67 cokme (otopark) karesinde aday olcutler:
#
#   olcut            MESRU min..maks     COKUS min..maks   ayrisma
#   kaplama          0.001..0.809        0.725..0.833      CAKISIK
#   doluluk          0.007..0.897        0.726..0.836      CAKISIK
#   tikizlik         0.013..0.966        0.728..0.838      CAKISIK
#   en_buyuk_pay     0.208..1.000        0.995..1.000      CAKISIK
#   engel_orani      0.000..0.998        0.158..0.265      CAKISIK
#   kenar_dayanma    0.000..0.339        0.579..0.964      +0.240  <- TEK AYIRAN
#
# FIZIKSEL GEREKCE: cokmus maske sahneyi ayirt etmedigi icin goruntu CEVRESININ
# neredeyse tamamina dayanir (%58-96). Mesru arena zemininde koridorlar kenara
# ULASIR ama yalnizca kendi genislikleri kadar — cevrenin en fazla %34'u.
# Kaplama bunu goremez cunku cokmus blob ile genis acik arena AYNI alani kaplar.
#
# Esik iki dagilimin ORTASI: (0.339 + 0.579) / 2 = 0.459 -> 0.45 (mesru tarafa
# 0.111, cokme tarafina 0.129 pay). Olculen kumelerde yanlis-negatif 0/218,
# yanlis-pozitif 0/67.
# T52 · KENAR DAYANMA TAVANI — UC KISITIN KESISIMI (D-69 denetimi, D-71 karari).
# Olcum: 320 MESRU yer-gercegi maskesi (sentetik_arena val 60 + kadraj val 26 +
# kadraj train 234; model YOK) ve 67 COKMUS kare (v21'in otopark ciktisi).
# Kose cift sayimi duzeltildikten SONRA yeniden olculdu:
#
#   (a) MESRU azami (kaplama tavanini asan 11 kare) : 0,453   -> tavan USTUNDE olmali
#   (b) mevcut test paketinin COKME fiksturu asgari : 0,536   -> tavan ALTINDA olmali
#   (c) COKMUS kume kenar asgarisi                  : 0,583   -> tavan ALTINDA olmali
#
#   gecerli aralik (0,453 · 0,536) — genislik 0,083; 0,50 pratikte ORTASI.
#   0,50'de paylar: mesru +0,047 · test +0,036 · cokme +0,083
#   sonuc: mesru elenen 0/320 · cokme yakalanan 67/67
#
# ONCEKI 0,45 olculen mesru azaminin (0,453) ALTINDAYDI: payi -0,002 ve
# 1/320 mesru kareyi eliyordu (D-69).
ZEMIN_KENAR_DAYANMA_TAVANI = 0.50


def zemin_kenar_dayanmasi(trav, icerik=None):
    """Zemin maskesinin ICERIK kutusu CEVRESINE degme orani [0,1]."""
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
    # KOSE PIKSELLERI BIR KEZ SAYILIR (D-69 bulgusu, D-71 karari). Onceki
    # surum dort kenari ayri ayri toplayip paydayi `2*(ih+iw)` aliyordu;
    # olculdu: tek KOSE pikseli tek KENAR pikselinin 2,00 kati katki
    # veriyordu. Azami yine 1,0'da kaldigi icin tutarliydi ama kose agirligi
    # sahte bir sinyaldi. Cerceve maskesi her cevre pikselini bir kez sayar
    # ve 1x1 / 1xN / Nx1 kutularda da dogru calisir.
    cerceve = _np.zeros(kutu.shape, dtype=bool)
    cerceve[0, :] = True
    cerceve[-1, :] = True
    cerceve[:, 0] = True
    cerceve[:, -1] = True
    payda = int(_np.count_nonzero(cerceve))
    if payda == 0:
        return 0.0
    return float(_np.count_nonzero(kutu[cerceve])) / float(payda)


def icerik_kutusu_gecerli_mi(icerik, sekil):
    """`icerik` kutusu bu maske icin GECERLI mi? Fail-closed olcut.

    Gecerli sayilmasi icin dortlu olmali ve her ogesi bool OLMAYAN, sonlu,
    TAM SAYI degerinde olmali; kutu maskenin icine TAM sigmali (tasma yok),
    genislik ve yukseklik pozitif olmali. `None` gecerlidir (tum maske).

    NEDEN (D-69): `zemin_maskesi_reddi` bozuk kutuda 0,0 olcup SUSUYORDU —
    tamamen dolu, cevreye tam dayanan bir maske bile geciyordu. Kardes
    sozlesme fonksiyonlari (`rota_guven_reddi`, `rota_olcek_reddi`,
    `mpp_irtifadan`) gecersiz girdide FAIL-CLOSED; bu kapi da oyle olmali.
    """
    if icerik is None:
        return True
    try:
        ogeler = list(icerik)
    except TypeError:
        return False
    if len(ogeler) != 4:
        return False
    tam = []
    for oge in ogeler:
        if isinstance(oge, bool) or not isinstance(oge, Real):
            return False
        d = float(oge)
        if not math.isfinite(d) or not d.is_integer():
            return False
        tam.append(int(d))
    x0, y0, iw, ih = tam
    if iw <= 0 or ih <= 0 or x0 < 0 or y0 < 0:
        return False
    h, w = int(sekil[0]), int(sekil[1])
    return (x0 + iw) <= w and (y0 + ih) <= h


def zemin_maskesi_reddi(trav, icerik=None):
    """Maske ayirt etmiyorsa kanonik ``(sebep, detay)``; aksi halde ``None``.

    IKI SINYAL, ikisi de asilirsa reddedilir:
      * kaplama > ZEMIN_KAPLAMA_TAVANI          (kaba siddet olcusu)
      * kenar dayanma > ZEMIN_KENAR_DAYANMA_TAVANI (AYIRT EDICI olcut, T52)

    Kaplama tek basina mesru genis arenayi da eliyordu (11/260, D-65); kenar
    dayanmasi o hatayi kaldirir. Kaplama sarti KORUNUR cunku dar ama cevreye
    dayanan (or. tek serit kenar boyunca) sahneler mesru olabilir.

    Kapi yalniz REDDEDER — maskeye dokunmaz, serbest alani BUYUTMEZ
    (CLAUDE.md madde 15 acisindan notrdur, cunku hicbir piksel eklemez).
    """
    import numpy as _np
    sekil = _np.asarray(trav).shape
    if len(sekil) != 2 or not icerik_kutusu_gecerli_mi(icerik, sekil):
        # FAIL-CLOSED (D-71): olcum yapilamiyorsa kapi SUSMAZ, reddeder.
        # Sebep `ALAN_YETERSIZ`: `analyze_path:606` ayni kosulu (gecersiz/bos
        # icerik kutusu) ZATEN bu kodla reddediyor — ikinci bir sebep kodu
        # turetmek yerine uretimin mevcut kanonik cevabi korunur.
        return (ALAN_YETERSIZ_SEBEBI,
                f"Icerik kutusu gecersiz ({icerik!r}) veya maske 2 boyutlu "
                f"degil (sekil {tuple(sekil)}); zemin maskesi saglamligi "
                "olculemedi, rota uretilmez.")
    oran = zemin_kaplamasi(trav, icerik)
    if oran <= ZEMIN_KAPLAMA_TAVANI:
        return None
    kenar = zemin_kenar_dayanmasi(trav, icerik)
    if kenar <= ZEMIN_KENAR_DAYANMA_TAVANI:
        return None
    return (ZEMIN_MASKESI_SUPHELI_SEBEBI,
            f"Zemin maskesi icerigin %{100.0 * oran:.1f}'ini kapliyor "
            f"(tavan %{100.0 * ZEMIN_KAPLAMA_TAVANI:.1f}) VE cevrenin "
            f"%{100.0 * kenar:.1f}'ine dayaniyor (tavan "
            f"%{100.0 * ZEMIN_KENAR_DAYANMA_TAVANI:.1f}). Maske sahneyi ayirt "
            "etmiyor (cati/cim/toprak zemin sayilmis olabilir); rota "
            "uretilmez.")


# ════════════════════════════════════════════════════════════════════════════
# T67 · INCE BARIYER DEDEKTORU — KATMAN 2   (CONTRACTS SS2 · REVIEW_LOG D-92/93)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (gercek arena karesinde, MODEL KULLANILMADAN olculdu — D-92):
#
#   bariyer pikselleri n = 3644
#     model ENGEL diyor : %0,0     <- tek piksel bile degil
#     model ZEMIN diyor : %30,9
#   ROTA x BARIYER kesisimi: 59 px  -> KESIYOR (gorsel dogrulandi)
#
# Korumalarin HICBIRI ateslemiyor: zemin kapisi susuyor (kaplama 0,579 < 0,67),
# karar reddi yok, guven 0,75, darbogaz 27,8 px "genis" gorunuyor. Rotayi
# yayindan alikoyan TEK sey `OLCEK_YOK` — bir kapi degil, bir EKSIKLIK.
#
# MODEL BEKLENMIYOR (D-93): uretec bariyeri YALNIZ zaten KAPALI seritlere
# koyuyor; acik zeminde bariyer orani %0,0. Egitim verisi "acik gorunen zeminde
# bariyer" ornegi HIC icermiyor, dolayisiyla model bunu ogrenemez. Cozum
# KATMAN 2'de klasik dedektordur.
#
# NEDEN KROMA CALISIR: D-87 gercek arenanin renk kunyesini olctu — sahnenin
# TAMAMINDA |a*| < 1 (baskin paletin alti kumesinde de). Bariyer sahnedeki TEK
# yuksek kromali yapidir; olculen tepe a* = 44. Esik 25 iki tarafa da genis pay
# birakir (gurultu tarafina 25x, bariyer tarafina 1,76x).
#
# 🔴 TUZAK — "KIRMIZI = ENGEL" KURALI HEDEFI OLDURUR. Sartname METNI hedefi
# "2x2 m KIRMIZI branda" diyor (figur notr gosteriyor; celiski D-87'de). Naif
# bir kirmizi kurali HB'yi engel sayar, IKA hedefe HICBIR ZAMAN ulasamaz ve
# P_gorev = 0 olur. Ayrim RENKLE DEGIL SEKILLE yapilir:
#
#   yapi            en/boy (olculen)      sonuc
#   HB pedi         1,00 (T60, n=260)     KARE  -> ELENIR, engel sayilmaz
#   bariyer kolu    7,0  ve  14,2         UZUN  -> engel sayilir
#
# Esik 4,0 ikisinin ORTASINDADIR: HB tarafina 4,0x, bariyer tarafina 1,75x pay.
#
# OLCUTLER ORAN'DIR, PIKSEL DEGIL (CONTRACTS SS8). Referans olcum betigi
# (`63_bariyer_kesisimi.py`) ciplak piksel kullaniyordu (61x5 cekirdek, alan
# 300, genislik 60) ve 1059 genisligindeki KAYNAK karede kalibre edilmisti;
# uretim zincirinde tespit `small` (512x512) uzerinde yapilir ve orada o
# sabitler KISA KOLU KACIRIYOR (w=47 < 60). Orana cevrilince uc cozunurlukte de
# ayni iki kol bulunuyor:
#
#   cozunurluk        kol    w/W (kisa · uzun)    en/boy (kisa · uzun)
#   KAYNAK 1059x634    2     0,093 · 0,215        7,0 · 14,2
#   sq     1059x1059   2     0,093 · 0,215        7,0 · 14,2
#   small   512x512    2     0,092 · 0,215        6,7 · 13,8
#
# ⚠ MADDE 15: bu dedektor yalniz ENGEL KATMANINA EKLER. Serbest alan
# `zemin AND NOT engel` oldugu icin sonuc yalniz KUCULUR; hicbir kosulda
# buyumez. CONTRACTS SS2: "Katman 2'ye yeni bir dedektor eklemek monotonik
# olarak GUVENLIDIR."
#
# 🔴 KALIBRASYON ZEMINI GERCEK ARENA DEGIL, TEK BIR YAPAY ZEKA GORUNTUSUDUR
# (D-99). Sartname Sekil 1 alt yazisi: "Gorsel tamamen yapay zeka ile
# olusturulmustur. Gercek alani dogrudan yansitmamaktadir." Bariyerin
# KIRMIZI-BEYAZ gorunumu bu yuzden UYDURMADIR; gercek arenada fiziki engeller
# kirmizi OLMAYABILIR ve o durumda bu dedektor HIC ATESLEMEZ (fail-safe:
# sistem T67 oncesi davranisa doner, hicbir sey bozulmaz).
# AYAKTA KALAN GEREKCE: sartname METNI (SS2.1) kapali guzergahlarin "fiziki
# engellerle kapatilacagini" soyler — ince-engel riski GERCEKTIR, yalniz
# gorunumu bilinmiyor.
# "Bariyer sorunu cozuldu" genel bir iddia DEGILDIR.
#
# 🔴 D-99 TUZAGI KESINLESTIRDI: figur yapay oldugu icin artik METIN OTORITEDIR
# ve metin (SS2.1) hedefi "uzerinde KIRMIZI H harfi bulunacagi bir bolge" diye
# tanimlar. Yani HB GERCEKTEN KIRMIZIDIR; D-87'nin figure dayanan "notr ped"
# hukmu GECERSIZDIR. Asagidaki SEKIL ayrimi bu yuzden sussuz degil, TASIYICIDIR.
BARIYER_KROMA_ESIGI = 25
BARIYER_EN_BOY_ORANI = 4.0
BARIYER_ASGARI_GENISLIK_ORANI = 60.0 / 1059.0        # ~0,0567
BARIYER_ASGARI_ALAN_ORANI = 300.0 / (1059.0 * 634.0)  # ~0,000447
BARIYER_KAPAMA_ORANI = 61.0 / 1059.0                  # ~0,0576


def ince_bariyer_maskesi(bgr):
    """Uzun/ince/yuksek-kromali YATAY yapilari isaretle (KATMAN 2 engeli).

    Girdi BGR goruntu; cikti ayni (h, w) boyutunda uint8 ikili maske.
    Fail-closed: cozulemeyen girdide BOS maske doner — yani hicbir sey
    EKLEMEZ. Bu olcut hicbir kosulda serbest alani BUYUTEMEZ (madde 15).
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return None
    im = _np.asarray(bgr)
    if im.ndim != 3 or im.shape[2] != 3 or im.size == 0:
        return None
    h, w = im.shape[:2]
    if h < 3 or w < 3:
        return _np.zeros((max(h, 0), max(w, 0)), _np.uint8)

    lab = _cv2.cvtColor(im.astype(_np.uint8), _cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(_np.int16) - 128
    kirmizi = (a > BARIYER_KROMA_ESIGI).astype(_np.uint8)

    # Serit araliklarini (beyaz bantlar) kapatarak kolu TEK PARCA yap.
    # Cekirdek genislige oranlidir; sabit piksel cozunurluk degisince kayar.
    kx = max(3, int(round(w * BARIYER_KAPAMA_ORANI)) | 1)
    ky = max(3, int(round(kx / 12.0)) | 1)
    kirmizi = _cv2.morphologyEx(
        kirmizi, _cv2.MORPH_CLOSE,
        _cv2.getStructuringElement(_cv2.MORPH_RECT, (kx, ky)))

    n, lbl, st, _ = _cv2.connectedComponentsWithStats(kirmizi, 8)
    asgari_alan = max(1.0, BARIYER_ASGARI_ALAN_ORANI * w * h)
    asgari_gen = max(2.0, BARIYER_ASGARI_GENISLIK_ORANI * w)
    kol = _np.zeros((h, w), _np.uint8)
    for i in range(1, n):
        x, y, bw, bh, alan = st[i]
        if alan < asgari_alan:
            continue
        # UZUN ve INCE olmali: HB pedi KAREDIR ve buradan GECEMEZ.
        if bw > BARIYER_EN_BOY_ORANI * max(1, bh) and bw > asgari_gen:
            kol[lbl == i] = 1
    return kol


# T67: bariyer hangi maske katmanina EKLENIR. `sinif_semasi.ENGEL` ile ayni
# olmak ZORUNDADIR; ama `sinif_semasi` Jetson saha paketinde YOKTUR
# (`scripts/jetson_paket_hazirla.py` KOPYALAR listesi), bu yuzden buradan
# import EDILEMEZ — sahada ImportError olurdu. Iki degerin esitligi
# `tests/test_ince_bariyer.py` ile kilitlenir; biri degisip digeri kalamaz.
BARIYER_ENGEL_SINIFI = 1
