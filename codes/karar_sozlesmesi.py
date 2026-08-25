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
HEDEF_YOK_SEBEBI = "HEDEF_YOK"              # T72 · D-105

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
    HEDEF_YOK_SEBEBI,
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

# ── T143 · CANLI KAMERA DUSEN KARE SOZLESMESI (D-284, T18 curutucusu) ────────
# Kusur: `run_camera` dongusu `cap.read()` ilk `False` dondugunde SESSIZCE
# bitiyordu — ne sayac, ne yeniden deneme, ne log. USB/DroidCam hattinda tek
# bir kare kaybi (kablo titremesi, bant genisligi) butun algi hattini kapatir
# ve sahada kimse NEDEN durdugunu bilmezdi.
#
# Gerekce (tahmin degil, tasarim kisiti):
#  * UST SINIR ardisik dusen kareye uygulanir (toplam degil): kamera gercekten
#    koptuysa ardisik kayip surer, gecici titremede bir sonraki kare gelir ve
#    ardisik sayac sifirlanir. 30 kare, 30 fps kaynakta ~1 s'lik kesintiye
#    tekabul eder; daha uzunu "kamera yok" sayilir ve dongu LOGLU biter
#    (fail-closed: kamerasiz sonsuz bekleme YOK).
#  * BEKLEME her basarisiz okumadan sonra uygulanir ki cap.read() aninda
#    donerken mesgul dongu CPU'yu yemesin; 20 ms x 30 = ~0,6 s ek gecikme.
# Toplam dusen kare sayisi da tutulur ve bitiste raporlanir (YKS/log).
KAMERA_DUSEN_KARE_UST_SINIRI = 30      # ARDISIK dusen kare; asilinca kontrollu bitis
KAMERA_DUSEN_KARE_BEKLEME_S = 0.02     # her basarisiz okumadan sonra bekleme (s)
KAMERA_BITIS_KULLANICI = "KULLANICI_DURDURDU"
KAMERA_BITIS_DUSEN_KARE = "DUSEN_KARE_UST_SINIRI"
KAMERA_BITIS_ACILAMADI = "KAMERA_ACILAMADI"

# ── T143 · KAYIT DEFTERI TUREV YER TUTUCUSU ──────────────────────────────────
# `.engine`/`.onnx` turevleri kayit defterinde `turevler` altinda ayni SOYDAN
# tanitilir; her turevin KENDI sha256'si vardir. Derlenmemis turevin ozeti bu
# yer tutucudur ve yer tutucu = DOGRULANMAMIS = RED (fail-closed). Gercek ozet
# `codes/model_registry.py --turev-kaydet <dosya>` ile yazilir.
MODEL_TUREV_SHA_YER_TUTUCU = "DERLENINCE_YAZILIR"

# ── T135 · `rota_bul(icerik=None)` LETTERBOX SUPHESI (yalniz NOT; karar DEGISMEZ) ──
# `rota_bul` `icerik=None`da tum tuvali icerik sayar. Cagiran letterbox tuvali
# (kare tuval, 16:9 icerik) verip `icerik`i GECIRMEZSE zemin saglamlik kapisi
# matematiksel olarak olur: kaplama <= 0,5625, kenar <= 0,2815 (results/t142
# /olcum.md §3) — sessiz fail-open. Davranis degistirilmez (geriye uyumluluk),
# ama supheli durum sebebe/loga bu notla islenir. Suphe kosulu: tuval KARE, en
# az bir maske pikseli var ve ust+alt (ya da sol+sag) bantlarin ikisi de tum
# maskelerde TAMAMEN bos. Bant orani 0,10: 4:3 icerik karede 0,125'lik, 16:9
# icerik 0,219'luk bos bant birakir; 0,10 ikisini de yakalar, mesru kare
# mozaikte (iha_haritala) zemin sinifi cerceveye dayanmasa bile her iki
# karsit bantin birden bos olmasi gerekir.
ICERIK_YOK_LETTERBOX_SUPHESI_NOTU = "ICERIK_YOK_LETTERBOX_SUPHESI"
LETTERBOX_SUPHE_BANT_ORANI = 0.10


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


# ════════════════════════════════════════════════════════════════════════════
# T72 · HB (HEDEF BOLGESI) DEDEKTORU — KATMAN 2   (CONTRACTS SS2 · SS5 · SS6.4)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (saha kuru kosusu): `hedef_konumu` halkasi SAHIPSIZ. HB'nin tek kaynagi
# Gazebo `meta.txt`; saha kod yolunda `--hb` girisi YOK ve uretim modeli 2
# siniflidir (kirmizi H'yi goren bilesen YOK). Sartname SS2.2.6: gorev, IKA'nin
# HB SINIRLARI ICINE girmesiyle basarili sayilir. Yani acik guzergahi bulsak ve
# rota kusursuz olsa bile VARIS NOKTASI uretilemedigi icin gorev tamamlanamaz.
#
# UCUNCU SINIF EKLENMEDI. nc=2 -> 3 sozlesme degisikligi, yeniden egitim ve
# sinif-id cakismasi riski getirir (S2'de yasandi: 2 = hedef mi arac mi).
# T67'de klasik KATMAN 2 dedektoru calisti; ayni desen kullanildi.
#
# SARTNAME SS2.1: "2 metre x 2 metre boyutlarinda uzerinde KIRMIZI H harfi
# bulunacagi bir bolgedir." Uc ayirt edici ozellik:
#   1. yuksek kroma KIRMIZI  -> esik T67 ile ORTAK (`BARIYER_KROMA_ESIGI`)
#   2. KARE  (en/boy ~ 1)    -> bariyerin TUMLEYENI
#   3. bilinen metrik kenar  -> 2,0 m  (`HB_KENAR_M`)
#
# T67 ILE SINIR PAYLASILIR VE TEK YERDEN OKUNUR (madde 16).
# T67 bariyeri UZUN-INCE diye ayirir (en/boy > BARIYER_EN_BOY_ORANI = 4,0).
# HB ise KAREDIR. Iki dedektorun ayni yapiyi secmesi MUMKUN OLMAMALIDIR:
#
#     HB kabul araligi : 1/HB_KARE_TOLERANSI .. HB_KARE_TOLERANSI
#     bariyer araligi  : BARIYER_EN_BOY_ORANI .. sonsuz
#     ARADA BOS BANT VAR: HB_KARE_TOLERANSI < BARIYER_EN_BOY_ORANI
#
# Bandin bosluğu `tests/test_hb_dedektoru.py` ile kilitlenir; biri degisip
# digeri kalamaz ve iki dedektor CAKISAMAZ.
HB_KENAR_M = 2.0                    # sartname SS2.1
HB_KARE_TOLERANSI = 1.6             # en/boy bu araligin disindaysa HB DEGIL
HB_ASGARI_ALAN_ORANI = 120.0 / (640.0 * 640.0)   # ~0,00029 · gurultu suzgeci
HB_KAPAMA_ORANI = 10.0 / 640.0      # cerceve + H harfini TEK parcaya birlestir


def hb_maskesi(bgr):
    """HB pedini isaretle: yuksek kromali KIRMIZI ve KARE yapi.

    Fail-closed: cozulemeyen girdide None doner (hicbir sey iddia etmez).
    MADDE 15: bu dedektor SERBEST ALANA DOKUNMAZ. HB'yi bulmak gecilebilir
    alani ne buyutur ne kucultur; yalnizca A* hedefini belirler.
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
    if h < 8 or w < 8:
        return _np.zeros((h, w), _np.uint8)

    lab = _cv2.cvtColor(im.astype(_np.uint8), _cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(_np.int16) - 128
    kirmizi = (a > BARIYER_KROMA_ESIGI).astype(_np.uint8)   # ORTAK esik

    # T67 ILE TUMLEYENLIK — OLCUMLE GEREKCELENDIRILDI.
    # Ilk surumde sekil filtresi TEK BASINA yetmedi: `sa_000170` karesinde bir
    # BARIYER PARCASI 37x32 px (en/boy 1,16 -> KARE) olarak kalmis ve gercek
    # HB'den (25,6 px) BUYUK oldugu icin secilmisti. Yani bariyer, kirilinca
    # HB'nin sekil bandina girebiliyor.
    # Cozum: T67'nin ENGEL dedigi piksel HB OLAMAZ. Iki dedektor artik gercek
    # anlamda TUMLEYENDIR; ayni yapiyi ikisi birden secemez.
    bar = ince_bariyer_maskesi(im)
    if bar is not None and bar.shape == kirmizi.shape and bar.any():
        genis = _cv2.dilate(bar, _cv2.getStructuringElement(
            _cv2.MORPH_RECT, (5, 5)))
        kirmizi = _cv2.bitwise_and(kirmizi, 1 - (genis > 0).astype(_np.uint8))

    kx = max(3, int(round(w * HB_KAPAMA_ORANI)) | 1)
    kirmizi = _cv2.morphologyEx(
        kirmizi, _cv2.MORPH_CLOSE,
        _cv2.getStructuringElement(_cv2.MORPH_RECT, (kx, kx)))

    n, lbl, st, _ = _cv2.connectedComponentsWithStats(kirmizi, 8)
    asgari_alan = max(1.0, HB_ASGARI_ALAN_ORANI * w * h)
    ped = _np.zeros((h, w), _np.uint8)
    for i in range(1, n):
        x, y, bw, bh, alan = st[i]
        if alan < asgari_alan:
            continue
        en_boy = float(bw) / max(1.0, float(bh))
        if not (1.0 / HB_KARE_TOLERANSI <= en_boy <= HB_KARE_TOLERANSI):
            continue                          # KARE degil -> HB degil
        # Kutunun kendisi isaretlenir: HB "bolge"dir, yalniz kirmizi pikseller
        # degil. Sartname SS2.2.6 IKA'nin BOLGE SINIRLARI ICINE girmesini ister.
        ped[y:y + bh, x:x + bw] = 1
    return ped


def hb_konumu(bgr):
    """HB merkezi, kutusu ve piksel kenari. Bulunamazsa None.

    Birden fazla aday varsa EN BUYUK secilir (sahnede tek HB vardir; coklu
    aday gurultudur ve en buyugu en guvenilir olandir).
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return None
    ped = hb_maskesi(bgr)
    if ped is None or not ped.any():
        return None
    n, lbl, st, mrk = _cv2.connectedComponentsWithStats(ped, 8)
    if n <= 1:
        return None
    i = 1 + int(_np.argmax(st[1:, 4]))
    x, y, bw, bh, alan = (int(v) for v in st[i][:5])
    return {
        "merkez": (float(mrk[i][0]), float(mrk[i][1])),
        "kutu": (x, y, bw, bh),
        "kenar_px": float((bw + bh) / 2.0),
        "alan_px": int(alan),
        "aday_sayisi": int(n - 1),
    }


def mpp_hb_pedinden(kenar_px, kenar_m=HB_KENAR_M):
    """CONTRACTS SS5(b): bilinen olcekli nesneden `mpp`.

    Bu, SS5'te "ucuncu sinif uretime girdiginde acilir" diye KAPALI birakilan
    yoldur. Klasik dedektor onu ucuncu sinif OLMADAN acar. Ama T70 canli
    telemetri olceginin YERINE GECMEZ — `olcek_capraz_kontrolu`'na bak.
    Fail-closed: olculemeyen kenar None doner.
    """
    try:
        k = float(kenar_px)
        m = float(kenar_m)
    except (TypeError, ValueError):
        return None
    if not (k > 0.0) or not (m > 0.0):
        return None
    if not math.isfinite(k) or not math.isfinite(m):
        return None
    return m / k


# CONTRACTS SS5.4: iki olcek kaynagi CELISIRSE ne olur. Bu bant, iki bagimsiz
# olcumun makul sayilacagi bagil fark siniridir; asilirsa olcek SUPHELIDIR ve
# fail-closed davranilir (uydurma ortalama ALINMAZ).
OLCEK_CAPRAZ_BANDI = 0.25


def olcek_capraz_kontrolu(mpp_telemetri, mpp_hb):
    """Iki olcek kaynagini kiyasla -> (secilen_mpp, durum, bagil_fark).

    KURAL (baglayici):
      - yalniz TELEMETRI varsa -> telemetri secilir (SS5 birincil kaynak)
      - yalniz HB varsa        -> HB secilir, durum "yalniz_hb"
      - IKISI de varsa ve bagil fark <= OLCEK_CAPRAZ_BANDI -> TELEMETRI secilir
        (birincil kaynak degismez; HB yalniz DOGRULAR)
      - IKISI de varsa ve fark BANDI ASIYORSA -> (None, "celiskili", fark)
        Ortalama ALINMAZ, biri secilmez: iki bagimsiz olcum celisiyorsa
        hangisinin dogru oldugunu bilmiyoruz demektir. Fail-closed.
    """
    def _gecerli(v):
        if isinstance(v, bool) or not isinstance(v, Real):
            return None
        f = float(v)
        return f if (math.isfinite(f) and f > 0.0) else None

    t = _gecerli(mpp_telemetri)
    hb = _gecerli(mpp_hb)
    if t is None and hb is None:
        return (None, "olcek_yok", None)
    if hb is None:
        return (t, "yalniz_telemetri", None)
    if t is None:
        return (hb, "yalniz_hb", None)
    fark = abs(t - hb) / max(t, hb)
    if fark > OLCEK_CAPRAZ_BANDI:
        return (None, "celiskili", fark)
    return (t, "dogrulandi", fark)


# ════════════════════════════════════════════════════════════════════════════
# T83 · OLCEK KAHINI HIYERARSISI            (CONTRACTS SS5.4 · REVIEW_LOG D-124)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR. `mpp` YALNIZ telemetriden turetilebiliyordu (`mpp_irtifadan`).
# Telemetrisiz goruntude `OLCEK_YOK` duser ve C-uzayi HIC kosmaz — 67 gercek
# otopark karesinin 67'sinde olan tam budur.
#
# UC KATMAN, her biri KAYNAGINI BEYAN EDER. Sessiz dusus YOKTUR: hangi katmanin
# uretttigi karar nesnesine yazilir ve KATMAN DUSTUKCE GUVEN DE DUSER.
#
# 🔴 GUVEN CARPANLARI UYDURULMADI — OLCULEN bagil belirsizlikten gelir:
#
#   telemetri     1.00  sozlesme OTORITESI (SS5.2); kiyas noktasi budur
#   arena_siniri  0.70  T65/D-94: gercek arena siniri PERSPEKTIF YAMUKTUR ve
#                       genisligi kare boyunca 730 px (ust) -> 950 px (alt)
#                       degisir. Tek skaler bu yuzden en az %30 hata tasir:
#                       1 - 0.30 = 0.70
#   arac_referansi 0.86 D-124: 24 kare · 1880 DOTA-OBB tespiti; kisa kenarin
#                       ceyrekler-arasi yayilim / medyan = 0.138.
#                       1 - 0.138 = 0.862 -> 0.86
#
# ⚠ OLCUM, EMIRDEKI SIRALAMAYI DOGRULAMIYOR — kayda gecer: katman 2 (arena)
# katman 3'ten (arac) DAHA BELIRSIZ olcumlendi (0.70 < 0.86). Siralama
# kullanicinin karari oldugu icin DEGISTIRILMEDI; carpanlar olculen gercegi
# yansitir, dolayisiyla arena kaynakli bir olcek arac kaynaklidan DAHA DUSUK
# guvenle sunulur. Siralamayi cevirme karari mimarindir.
OLCEK_KAYNAK_TELEMETRI = "telemetri"
OLCEK_KAYNAK_ARENA = "arena_siniri"
OLCEK_KAYNAK_ARAC = "arac_referansi"
OLCEK_KAYNAK_SIRASI = (OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                       OLCEK_KAYNAK_ARAC)
OLCEK_GUVEN_CARPANI = {
    OLCEK_KAYNAK_TELEMETRI: 1.00,
    OLCEK_KAYNAK_ARENA: 0.70,
    OLCEK_KAYNAK_ARAC: 0.86,
}

# T86: EKRANDA gorunen ad. Hakem `arac_referansi` gibi bir anahtar degil,
# okunabilir bir etiket gormeli; ama etiket de CIPLAK YAZILMAZ (madde 16) —
# tek kaynak burasidir, `comms/yks_gui.py` buradan okur.
OLCEK_KAYNAK_ETIKETI = {
    # 1. katman hem CANLI TELEMETRIYI hem cagiricinin BEYANINI (statik --mpp,
    # kume manifesti) kapsar; ikisi de SS5.2 uyarinca OTORITEDIR. Ekranda
    # "TELEMETRI" yazmak manifest olcegi icin yaniltici olurdu.
    OLCEK_KAYNAK_TELEMETRI: "TELEMETRİ/BEYAN",
    OLCEK_KAYNAK_ARENA: "ARENA SINIRI",
    OLCEK_KAYNAK_ARAC: "ARAÇ REFERANSI",
}

# Binek arac govde genisligi (ayna haric), TS/EU M1 tipik bandi (D-124).
ARAC_GENISLIGI_M = 1.80
ARAC_GENISLIGI_BANDI = (1.70, 1.90)

# 🔴 SENARYO BEYAN EDILIR, TAHMIN EDILMEZ. Yanlis senaryo 2,5 kat olcek
# hatasidir (50 m / 20 m). Bu yuzden `senaryo` bilinen bir anahtar degilse
# katman 2 DEVREYE GIRMEZ — "buyuk olan HTAB'dir" gibi bir varsayim YOKTUR.
SENARYO_BOYUTLARI_M = {"HTAB": 50.0, "IHA_IB": 30.0, "FDA": 20.0}


def mpp_arac_referansindan(kisa_kenar_px, arac_genisligi_m=ARAC_GENISLIGI_M):
    """DOTA-OBB kisa kenari (= tepeden gövde genisligi) -> m/px. Yoksa None."""
    if isinstance(kisa_kenar_px, bool) or not isinstance(kisa_kenar_px, Real):
        return None
    k = float(kisa_kenar_px)
    if not math.isfinite(k) or k <= 0.0:
        return None
    if (isinstance(arac_genisligi_m, bool)
            or not isinstance(arac_genisligi_m, Real)):
        return None
    g = float(arac_genisligi_m)
    if not math.isfinite(g) or g <= 0.0:
        return None
    return g / k


def mpp_arena_sinirindan(sinir_genislik_px, senaryo):
    """TESPIT EDILMIS arena sinir genisligi + BEYAN EDILEN senaryo -> m/px.

    ⚠ `sinir_genislik_px` GORUNTUDEN TESPIT EDILMIS olmalidir. "kare = arena"
    varsayimi bu fonksiyonun disinda da, icinde de YOKTUR: cagiran tespit
    edemediyse ``None`` gecer ve katman devreye girmez.
    """
    if senaryo not in SENARYO_BOYUTLARI_M:
        return None
    if (isinstance(sinir_genislik_px, bool)
            or not isinstance(sinir_genislik_px, Real)):
        return None
    s = float(sinir_genislik_px)
    if not math.isfinite(s) or s <= 0.0:
        return None
    return SENARYO_BOYUTLARI_M[senaryo] / s


def olcek_guveni_uygula(guven, kaynak):
    """Rota guvenini olcek KAYNAGINA gore indir (katman dustukce guven duser)."""
    if isinstance(guven, bool) or not isinstance(guven, Real):
        return 0.0
    g = float(guven)
    if not math.isfinite(g) or g <= 0.0:
        return 0.0
    return g * OLCEK_GUVEN_CARPANI.get(kaynak, 0.0)


def olcek_kahini(*, irtifa_m=None, goruntu_genislik_px=None,
                 yatay_fov_derece=None, odak_px=None,
                 arena_sinir_px=None, senaryo=None,
                 arac_kisa_kenar_px=None, arac_genisligi_m=ARAC_GENISLIGI_M):
    """Uc katmanli olcek kahini. -> dict (ASLA sessizce dusmez).

    Doner: ``{"mpp", "kaynak", "guven_carpani", "detay", "denenen"}``
    `denenen` her katman icin (kaynak, sonuc_metni) tasir — hangi katmanin
    neden devreye girmedigi KAYITLIDIR; bu alan ekranda ve gunlukte gosterilir.
    """
    denenen = []

    t = mpp_irtifadan(irtifa_m, goruntu_genislik_px,
                      yatay_fov_derece=yatay_fov_derece, odak_px=odak_px)
    if olcek_gecerli_mi(t):
        return {"mpp": float(t), "kaynak": OLCEK_KAYNAK_TELEMETRI,
                "guven_carpani": OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_TELEMETRI],
                "detay": f"irtifa {irtifa_m} m + FOV/odak",
                "denenen": [(OLCEK_KAYNAK_TELEMETRI, "URETTI")]}
    denenen.append((OLCEK_KAYNAK_TELEMETRI, "irtifa/FOV yok ya da gecersiz"))

    a = mpp_arena_sinirindan(arena_sinir_px, senaryo)
    if olcek_gecerli_mi(a):
        return {"mpp": float(a), "kaynak": OLCEK_KAYNAK_ARENA,
                "guven_carpani": OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_ARENA],
                "detay": (f"senaryo {senaryo} "
                          f"({SENARYO_BOYUTLARI_M[senaryo]:.0f} m) / "
                          f"tespit edilen sinir {float(arena_sinir_px):.1f} px"),
                "denenen": denenen + [(OLCEK_KAYNAK_ARENA, "URETTI")]}
    denenen.append((OLCEK_KAYNAK_ARENA,
                    "senaryo BEYAN EDILMEDI" if senaryo not in SENARYO_BOYUTLARI_M
                    else "arena siniri GORUNTUDEN TESPIT EDILEMEDI"))

    v = mpp_arac_referansindan(arac_kisa_kenar_px, arac_genisligi_m)
    if olcek_gecerli_mi(v):
        return {"mpp": float(v), "kaynak": OLCEK_KAYNAK_ARAC,
                "guven_carpani": OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_ARAC],
                "detay": (f"arac kisa kenari {float(arac_kisa_kenar_px):.1f} px "
                          f"= {arac_genisligi_m:.2f} m"),
                "denenen": denenen + [(OLCEK_KAYNAK_ARAC, "URETTI")]}
    denenen.append((OLCEK_KAYNAK_ARAC, "sahnede olculebilir arac YOK"))

    return {"mpp": None, "kaynak": None, "guven_carpani": 0.0,
            "detay": "hicbir katman olcek uretemedi", "denenen": denenen}


# ════════════════════════════════════════════════════════════════════════════
# T88 · ARENA SINIR DEDEKTORU — olcek kahininin 2. KATMANINI BESLER
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (mimar olctu): `mpp_arena_sinirindan` yazildi ve testleri var, ama
# uretim cagri yerleri `arena_sinir_px` GECIRMIYORDU — hep None. Katman 2
# uretimde HIC calisamiyordu.
#
# 🔴 UC YAKLASIM DENENDI, IKISI CURUDU (olcum REVIEW_LOG D-138'de):
#   1. Hough + aralik duzenliligi   -> arena cv 0,55; otopark 0,13-0,32. AYIRMADI.
#   2. Morfolojik cizgi + aralik CV -> ayni sonuc, olcut YON DEGISTIRIYOR.
#   3. Oziliski (periyodiklik)      -> arena 0,497; negatiflerin medyani 0,472,
#                                      maks 0,825. AYIRMADI.
# AYIRAN sey su oldu: sartname izgarasinin cizgileri kareyi BASTAN SONA kat
# eder. Cok uzun (>= %45 kisa kenar) ve IKI DIK AILEDE birden gorulen cizgi
# parcasi, molozun/park cizgisinin uretemedigi bir yapidir:
#
#     kaynak         n    min(dikey,yatay) parca   min/medyan/maks
#     arena_gercek   1                             11 / 11 / 11
#     drone         14                              0 /  0 /  0
#     kompozit       9                              0 /  0 /  0
#     arena_kadraj  13                              0 /  0 /  3
#     gemini        80                              0 /  0 /  6
#
# ⚠ ESIK SAYILARI GORDUKTEN SONRA SECILDI (8): negatif azami 6, pozitif 11.
# ⚠⚠ POZITIF ORNEK SAYISI **BIR**'dir (D-88/D-99: elimizde tek gercek arena
# karesi var). Tek ornekle ayarlanmis bir esik GENELLENEMEZ; bu dedektor
# DOGRULANMIS degil, YALNIZCA elimizdeki tek kare uzerinde OLCULMUSTUR.
#
# 🔴 SONUC — T88'IN ASIL SORUSU CEVAPSIZ KALDI. Bu yapi arenayi TANIYOR ama
# SINIRI YERELLESTIREMIYOR; katman 2'nin ihtiyaci olan sey ikincisidir.
# Olculen genislik 535 px, izgaranin gercek uzanimi ~840 px — hata
# EMNIYETSIZ yonde (`r_gerekli_px` %36 KUCUK). D-94 ayni imzayi 260 karede
# olcmus ve "guvenilir: HAYIR" yazmisti; bagimsiz olcum onu DOGRULUYOR.
# Bu yuzden asagidaki aciklik fonksiyonu HICBIR uretim yolundan cagrilmaz ve
# olcek kahini `arena_sinir_px`i almaya devam eder — ama BEYANLA, tespitle
# DEGIL. Kayit: REVIEW_LOG D-138.
ARENA_IZGARA_UZUNLUK_ORANI = 0.45   # kisa kenarin orani; cizgi BU kadar uzun
ARENA_IZGARA_ACI_TOLERANSI = 12.0   # derece; dik/yatay aileye kabul bandi
ARENA_IZGARA_ASGARI_PARCA = 8       # HER IKI ailede de gereken parca sayisi


def arena_izgara_parcalari(bgr):
    """(dikey_x_listesi, yatay_y_listesi) — cok uzun cizgi PARCALARI.

    Doner: iki liste (parca orta noktalarinin konumu). Cozulemeyen girdide
    ``([], [])``. Bunlar AYRI CIZGI DEGIL PARCADIR: Hough ayni cizgiyi birden
    cok parcayla dondurur; sayim bu yuzden "cizgi sayisi" diye okunmamalidir.
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return [], []
    im = _np.asarray(bgr)
    if im.ndim != 3 or im.shape[2] != 3 or im.size == 0:
        return [], []
    h, w = im.shape[:2]
    if min(h, w) < 32:
        return [], []
    gri = _cv2.GaussianBlur(_cv2.cvtColor(im.astype(_np.uint8),
                                          _cv2.COLOR_BGR2GRAY), (3, 3), 0)
    parcalar = _cv2.HoughLinesP(
        _cv2.Canny(gri, 40, 120), 1, _np.pi / 360, threshold=110,
        minLineLength=int(ARENA_IZGARA_UZUNLUK_ORANI * min(h, w)), maxLineGap=10)
    if parcalar is None:
        return [], []
    dikey, yatay = [], []
    for x1, y1, x2, y2 in parcalar.reshape(-1, 4):
        aci = abs(math.degrees(math.atan2(float(y2 - y1), float(x2 - x1))))
        aci = min(aci, 180.0 - aci)
        if abs(aci - 90.0) <= ARENA_IZGARA_ACI_TOLERANSI:
            dikey.append((float(x1) + float(x2)) / 2.0)
        elif aci <= ARENA_IZGARA_ACI_TOLERANSI:
            yatay.append((float(y1) + float(y2)) / 2.0)
    return sorted(dikey), sorted(yatay)


def arena_izgarasi_var_mi(bgr):
    """Karede sartname IZGARASI var mi? (True/False) — SINIFLANDIRICI.

    🔴 "KARE = ARENA" VARSAYIMI YOKTUR. Iki dik aile de esigi gecmezse False
    doner; olcek kahini katman 2'yi atlar ve sebep `denenen` dokumune yazilir.

    Bu fonksiyon YALNIZ VARLIK soyler, KONUM SOYLEMEZ. Ayrimi 118 negatif
    karede olculdu (yukaridaki tablo): negatif azami 6 parca, pozitif 11.
    ⚠ Pozitif ornek sayisi BIRDIR; esik genellenebilir DEGILDIR.
    """
    dikey, yatay = arena_izgara_parcalari(bgr)
    return (len(dikey) >= ARENA_IZGARA_ASGARI_PARCA
            and len(yatay) >= ARENA_IZGARA_ASGARI_PARCA)


def arena_izgara_acikligi_px(bgr):
    """Cok uzun DIKEY izgara parcalarinin yatay acikligi (px) — ya da None.

    🔴🔴 BU BIR ARENA SINIRI **DEGILDIR** VE OLCEK KAHINININ 2. KATMANINA
    BESLENMEZ. T88'de olculdu ve REDDEDILDI:

        gercek arena karesi (1059x634) · izgara acikligi  535 px
        ayni karede izgaranin gercek yatay uzanimi        ~840 px
        -> mpp %57 BUYUK, `r_gerekli_px` %36 KUCUK cikar (11,8 px / ~18,5 px)

    Hata YONU EMNIYETSIZDIR: gereken govde acikligi OLDUGUNDAN KUCUK gorunur,
    yani IKA'nin gecemeyecegi koridor gecilebilir sayilir.

    Sebep D-94'te 260 karede ZATEN olculmustu: molozun izgarayi GIZLEMESI. Sol
    kenar molozlu 118 karede dx0 medyan 79,0 px, molozsuz 102 karede 4,0 px —
    20 kat. D-94'un min/maks birlestirmesi gercek karede `[0, 1058]` yani TUM
    KAREYI verdi (sinir arenayi BUYUTUYORDU); buradaki "cok uzun parca" secimi
    ters yone kaciyor (sinir arenayi KUCULTUYOR). Iki uc da yanlis.

    Fonksiyon SILINMEDI cunku olcumun kendisi kayittir; ama adi ne olctugunu
    soyler ve hicbir uretim yolundan CAGRILMAZ.
    """
    dikey, yatay = arena_izgara_parcalari(bgr)
    if (len(dikey) < ARENA_IZGARA_ASGARI_PARCA
            or len(yatay) < ARENA_IZGARA_ASGARI_PARCA):
        return None
    aciklik = float(dikey[-1] - dikey[0])
    return aciklik if aciklik > 0 else None


def olcek_kaynak_metni(kahin):
    """Kahin sozlugunu EKRAN/GUNLUK satirina cevir (T86).

    🔴 SESSIZ DUSUS YASAK: olcek uretilemediginde bu metin hangi katmanin
    NEDEN devreye girmedigini tek tek sayar. Uretildiginde ise kaynak adi ve
    GUVEN CARPANI yazilir — katman 3'ten gelen bir olcek, telemetriyle ayni
    guvende sunulamaz (D-126).

    Ornek: ``ARAÇ REFERANSI · güven ×0,86 · arac kisa kenari 24.1 px = 1.80 m``
    """
    if not isinstance(kahin, dict):
        return "ölçek kaynağı BEYAN EDİLMEDİ"
    kaynak = kahin.get("kaynak")
    denenen = kahin.get("denenen") or []
    if kaynak is None:
        dokum = " · ".join(f"{OLCEK_KAYNAK_ETIKETI.get(k, k)}: {n}"
                           for k, n in denenen)
        return f"hiçbir katman ölçek üretemedi — {dokum}" if dokum else \
               "hiçbir katman ölçek üretemedi"
    carpan = kahin.get("guven_carpani", OLCEK_GUVEN_CARPANI.get(kaynak, 0.0))
    etiket = OLCEK_KAYNAK_ETIKETI.get(kaynak, kaynak)
    metin = f"{etiket} · güven ×{carpan:.2f}"
    detay = kahin.get("detay")
    return f"{metin} · {detay}" if detay else metin


# ════════════════════════════════════════════════════════════════════════════
# T79 · KORIDOR SECIMI: BERABERLIK BANDI + HISTEREZIS   (REVIEW_LOG D-122)
# ════════════════════════════════════════════════════════════════════════════
# OLCULEN KUSUR: Gauss sigma=2/255 (%0,8) gurultu altinda 260 karenin 9'unda
# secilen koridor DEGISIYOR (%3,46). %0,8 GERCEGIN ALT SINIRIDIR.
#
# 🔴 KOKEN OLCULDU VE ONERILEN CARE KISMEN CURUDU (T79 teshisi):
# ceviren 9 karenin YALNIZ 2'sinde beraberlik vardir. Kalan 7'de rota FIZIKSEL
# OLARAK yer degistirir — 4 karede her kosuda TEK serit doludur, yani
# kiyaslanacak ikinci aday YOKTUR:
#
#   sa_000081  ham --/15.00/-- -> serit 2   gurultulu --/--/15.00 -> serit 3
#              ACIKLIK AYNI (15.00), serit FARKLI: beraberlik degil, TASINMA
#   sa_000172  25.00/--/-- (1)  ->  --/--/24.00 (3)
#   sa_000176  --/--/95.00 (3)  ->  64.13/--/-- (1)   maske IoU 0,649
#
# Beraberlik bandi bu 7'yi COZMEZ; yalnizca gercek beraberligi determinize eder:
#   sa_000232 ham 23.00/23.00 -> bagil fark 0,0000
#   sa_000258 g2  18.00/17.98 -> bagil fark 0,0009
#
# BAND DEGERI CIPLAK DEGIL: projenin OLCULMUS gurultu tabani 0,04'tur
# (D-112: maske sd 0,025-0,032 ile birlikte kayitli). Bu bandin ALTINDAKI fark
# olcum degil GURULTUDUR; orada argmin gurultuyu izler.
BERABERLIK_BANDI = 0.04


def beraber_adaylar(acikliklar, band=BERABERLIK_BANDI):
    """En kucuk aciklikla GURULTU TABANI icinde kalan aday indisleri.

    `acikliklar`: indis -> aciklik (None = o serit rotada yok).
    Doner: artan indis sirali liste. Aday yoksa bos liste.
    """
    var = [(i, float(a)) for i, a in enumerate(acikliklar)
           if a is not None and isinstance(a, Real) and not isinstance(a, bool)
           and math.isfinite(float(a))]
    if not var:
        return []
    en_kucuk = min(a for _, a in var)
    return [i for i, a in var
            if (a - en_kucuk) / max(a, 1e-9) <= band]


def koridor_histerezisi(onceki_serit, aday_serit, gecilebilir_seritler,
                        onceki_aciklik=None, aday_aciklik=None,
                        band=BERABERLIK_BANDI):
    """Ardisik karelerde secimi SABIT tut — ama GUVENLIGI BOZMADAN.

    🔴 BAGLAYICI KURAL: onceki koridor ARTIK GECILEMEZSE aninda birakilir.
    Histerezis yalnizca "yeni aday BELIRGIN sekilde iyi degilse" onceki secimi
    korur; guvenligi geciktiren bir mekanizma DEGILDIR.

    `gecilebilir_seritler`: bu karede rota uretilebilen seritlerin kumesi.
    Doner: secilecek serit no.
    """
    gecilebilir = set(gecilebilir_seritler or ())
    if aday_serit not in gecilebilir:
        return aday_serit          # cagiran zaten aday uretmis; dokunma
    if onceki_serit is None or onceki_serit == aday_serit:
        return aday_serit
    if onceki_serit not in gecilebilir:
        return aday_serit          # 🔴 onceki artik GECILEMEZ -> ANINDA birak
    if onceki_aciklik is None or aday_aciklik is None:
        return aday_serit          # olculemiyorsa histerezis UYGULANMAZ
    try:
        o = float(onceki_aciklik)
        a = float(aday_aciklik)
    except (TypeError, ValueError):
        return aday_serit
    if not (math.isfinite(o) and math.isfinite(a)) or o <= 0.0 or a <= 0.0:
        return aday_serit
    # Aday BELIRGIN sekilde daha genis mi? Degilse onceki korunur.
    if (a - o) / max(a, 1e-9) > band:
        return aday_serit
    return onceki_serit


def hedef_yok_reddi(detay=None):
    """HB bulunamadi -> rota uretilmez. Kanonik `(sebep, detay)`."""
    return (HEDEF_YOK_SEBEBI,
            detay or ("HB (2 m x 2 m kirmizi H bolgesi) karede bulunamadi; "
                      "varis noktasi bilinmeden rota uretilmez."))
