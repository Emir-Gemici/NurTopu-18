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


def rota_serit_karari(rota_pikselleri, icerik_x0, icerik_w):
    """YAYINLANAN `road` — TEK TANIM (T155 · REVIEW_LOG D-296).

    Rotanin serit numarasi rotanin GOVDESINDEN okunur: her rota pikseli
    `serit_no()` ile bir seride sayilir, en cok piksel tasiyan serit kazanir.

    NEDEN (OLCULDU, 2026-08-26 · yer gercekli 15 sentetik sahne, T151 kumesi):
    eski yayin alani `darbogaz_serit` rotanin EN DAR noktasinin — yani TEK
    PIKSELIN — seridini yayinliyordu ve 15 sahnenin 9'unda YANLISTI (6/15).
    O tek piksel 15 sahnenin 13'unde rotanin UCUNDA olculdu (y=39 ya da
    y=460): KB/HB yakininda uc guzergah BIRLESIR, yani serit kimliginin
    TANIMSIZ oldugu yerde. Uc ornek (sayim = serit1/serit2/serit3 px):

        harita 1 kolay : 419/3/0   yer gercegi 1 -> darbogaz 2   (3 px, 422'de)
        harita 5 zor   : 7/416/0   yer gercegi 2 -> darbogaz 1   (7 px, 423'te)
        harita 3 zor   : 427/189/7 yer gercegi 1 -> darbogaz 3   (7 px, 623'te)

    Govdeden okunan karar AYNI 15 sahnenin 15'inde dogrudur ve `rota_bul`un
    bagimsiz kapi-tabanli etiketiyle 15/15 uyusur. Ortak nokta ILKEDIR:
    serit, rotanin AYIRT EDICI oldugu yerden okunur — bir uc degerden degil.
    `rota_bul` ayni ilkeyi yapisal olarak uygular (etiket, koridorlarin
    ayrildigi banttaki KAPI merkezinden gelir), bu yuzden iki yol ayni
    cevabi verir.

    ⚠ `darbogaz_serit` SILINMEZ: darbogaz ACIKLIGI guvenin girdisidir ve
    darbogazin hangi seritte olculdugu bir TANI bilgisidir. Yayin alani
    degisti, tani alani kalmadi.

    `rota_pikselleri`: (x, y) ikilileri — rasterlestirilmis rota (waypoint
      DUGUMLERI degil; ornekleme sayisi karara giremez, CONTRACTS SS6.4/5).
    Doner: ``(karar, sayim)`` — `karar` 1|2|3 ya da rota bossa ``None``;
      `sayim` serit basina piksel sayisi (n1, n2, n3).
    Beraberlik DETERMINISTIK bozulur: esit sayimda KUCUK serit indisi.
    """
    sayim = [0, 0, 0]
    for nokta in rota_pikselleri:
        x = int(nokta[0])
        sayim[serit_no(x, icerik_x0, icerik_w) - 1] += 1
    mevcut = [i for i in range(3) if sayim[i] > 0]
    if not mevcut:
        return None, tuple(sayim)
    return int(max(mevcut, key=lambda i: (sayim[i], -i)) + 1), tuple(sayim)


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

# K1 (sartname SS2.2.3 · CONTRACTS SS6.5): uretim algi yolu (rpi_inference)
# her karede telsize YA OPEN_ROUTE YA NO_ROUTE yazar; sessizlik yoktur.
# analyze_path "karar yok" (open_path None, sebep None) dondurdugunde bu
# YAYIN sebebi kullanilir. ROTA_RET_SEBEPLERI'ne GIRMEZ: o kume analiz
# katmaninin ret sebepleridir (test_rota_ret_nedenleri kumeyi kilitler);
# KARAR_YOK ise yayin katmaninin fail-closed varsayilanidir.
KARAR_YOK_SEBEBI = "KARAR_YOK"
# Piksel rota telsiz geometri sozlesmesine (iha_sender.rota_geometrisini_dogrula)
# cevrilemediginde yayinlanan NO_ROUTE sebebi.
ROTA_GEOMETRI_SEBEBI = "ROTA_GEOMETRI"
# HEARTBEAT aralığı (sn). ika_receiver hb_timeout=3.0 s ile SOZLESME: aralik
# zaman asiminin ucte biri — art arda 2 kayip HEARTBEAT baglantiyi dusurmez,
# 3. kayip dusurur. Bu sabit degisirse hb_timeout ile birlikte degisir.
IHA_HEARTBEAT_ARALIK_S = 1.0

# ── §6.2 · HAKEM EKRANINDA TESPIT TAZELIGI (T169 · ON_KAYIT SS36) ──────────
# Sartname: "acik yol guzergahi GERCEK ZAMANLI olarak YKS'ye aktarilmali ve
# Alan Hakemi tarafindan monitor uzerinden izlenmelidir... Hakem onayi
# alinmayan tespitler gecersiz sayilir."
# KUSUR (D-317): `comms/yks_gui.py` dugum canliligini izliyordu ama KARAR
# KUTUSUNUN tazelik korumasi YOKTU. Telsiz kesilse bile 36 puntoluk yesil
# "ACIK GUZERGAH — 2" ekranda kaliyor ve ONAY DUGMESI ETKIN kaliyordu; hakem
# dakikalar once uretilmis bir tespiti "canli" sanip sozlu onay verebilirdi.
# DEGER: heartbeat araligi 1 s; bu esik 5 kayip HEARTBEAT demektir. Baglanti
# dusme esigi (`ika_receiver.hb_timeout` = 3 s) ile AYNI AILEDENDIR ama ondan
# BUYUKTUR: hakem saniyelik guncellenen bir ekranda 3 s'lik bosluğu fark
# edemez, 5 s gorulebilir bir duraklamadir.
YKS_TESPIT_TAZELIK_S = 5.0
# Saha yayin referansi (CONTRACTS SS6.5): uretim yolunda dunya cercevesi
# YOKTUR; ref_xy her zaman yerel ankor [0, 0]'dir ve IKA saf oteleme yapar.
YAYIN_REF_XY = (0.0, 0.0)

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
# T204 (D-404 §8, KUCUK-2): ekransiz kipte 'q' yolu yoktur; tek kontrollu
# bitis SIGTERM/SIGINT'tir (`systemctl stop`). Bitis nedeni AYRI bir ad
# almalidir: "kullanici q'ya basti" ile "systemd durdurdu" saha gunlugunde
# ayni satira dusemez (KULLANICI_DURDURDU ekransiz kipte IMKANSIZDIR).
KAMERA_BITIS_SINYAL = "SINYAL_DURDURDU"

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


def rota_olcek_reddi(mpp):
    """Gorev yolunda olcek yoksa kanonik ``(sebep, detay)``; varsa ``None``.

    CONTRACTS SS11.3 Halka 5 olcutu: *"`mpp` turetilemiyorsa halka OLCEK_YOK
    dondurecek ve rota URETILMEYECEK."* Sessiz varsayilan YASAK.

    🔴 T171 (D-319): bu fonksiyonun `irtifa_m` parametresi ve icindeki
    "asgari irtifa" dali KALDIRILDI — cunku OLU KODDU: dalin IKI KOLU DA
    `return None` yapiyordu, yani sabit `SARTNAME_ASGARI_IRTIFA_M` burada
    ANILIYOR ama HICBIR SEY yapmiyordu. Ustelik hicbir cagiran `irtifa_m`
    GECMIYORDU. Sartname uyum raporumuz ise bu satiri kanit gostererek
    "irtifa aralik disi -> OLCEK_YOK" diye YANLIS bir uyum iddiasi tasiyordu.
    Asgari irtifa sarti (SS5.3.2) artik `asgari_irtifa_notu()` ile ve RET
    DEGIL GOSTERIM olarak ele alinir — gerekcesi orada yazili.
    """
    if not olcek_gecerli_mi(mpp):
        return (OLCEK_YOK_SEBEBI,
                f"Olcek (mpp) turetilemedi ({mpp!r}); irtifa+FOV/odak "
                "gerekli. Olceksiz kipte govde acikligi dogrulanamaz, "
                "rota yayinlanmaz.")
    return None


ASGARI_IRTIFA_SEBEBI = "ASGARI_IRTIFA_ALTI"


def asgari_irtifa_notu(irtifa_m, asgari_m=SARTNAME_ASGARI_IRTIFA_M):
    """SS5.3.2 asgari gorev irtifasi NOTU — ``(sebep, aciklama)`` ya da ``None``.

    Sartname SS5.3.2: *"...Acik Guzergah'i ASGARI 30 METRE IRTIFADAN ucarak,
    havadan goruntu isleme ... vasitasiyla tespit etmek..."* Yani asgari
    irtifanin ALTINDA yapilan bir tespit maddeyi KARSILAMAZ.

    🔴 NEDEN RET DEGIL: IHA kalkis ve inis sirasinda da kare uretir; bu
    karelerde rotayi REDDETMEK yanlis olurdu (gorev suresi bosa akar ve
    fail-closed yon burada KORUYUCU degil ZARARLIDIR). Ama hakem, asgari
    irtifanin ALTINDA uretilmis bir tespiti onaylarken bunu GORMEK ZORUNDADIR
    (T169 ile ayni mantik: ekran, maddeyi karsilamayan bir seyi karsiliyormus
    gibi gosteremez).

    IRTIFA BILINMIYORSA (None/gecersiz) NOT URETILMEZ: "bilinmiyor" ile
    "asgarinin altinda" ayni sey degildir; bilinmedigini soylemek CAGIRANIN
    isidir (sessiz sifir yasak).
    """
    if not olcek_gecerli_mi(irtifa_m):
        return None
    h = float(irtifa_m)
    if h >= float(asgari_m):
        return None
    return (ASGARI_IRTIFA_SEBEBI,
            f"Tespit {h:.1f} m irtifada uretildi; sartname SS5.3.2 ASGARI "
            f"{float(asgari_m):.0f} m ister. Bu bir ret DEGILDIR (kalkis/inis "
            "karesi olabilir) ama hakem onayi bu tespite verilirse madde "
            "KARSILANMAMIS sayilabilir.")


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
ZEMIN_KAPLAMA_TAVANI = 0.55      # T142 · D-286: v35 kalibrasyonu (0.67 v24 COKUSUNE gore konmustu, D-283)


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
ZEMIN_KENAR_DAYANMA_TAVANI = 0.40  # T142 · D-286: v35 mesru maks kenar 0.5004 (kaplama 0.494 < 0.55, AND kurtarir)


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
# 🔴 YUKARIDAKI OLCUM BAYATTIR — 2026-08-28'de YENIDEN OLCULDU (D-324).
# "model %0,0 goruyor" ARTIK DOGRU DEGIL. v36 ayni karede bariyer
# piksellerinin %99,9'unu ENGEL diyor. D-92 eski bir modelde olculmustu ve bu
# yorum guncellenmedi; bir sonraki okuyucuyu (mimarin kendisini) YANLIS
# YONLENDIRDI. Kod yorumu bir OLCUM DEGIL, bir olcumun TARIHIDIR.
#
# D-93 de ayni sekilde bayat: T68 bunu buyuk olcude kapatti — kabul kumesi
# manifestinde (n=260) 122 kare bariyer tasiyor ve 163 bariyer GECILEBILIR
# seride konmus. Kalan kusur dar: tek gecilebilir seritli sahnelerin
# %35,17'sinde havuz yine kapali seritlere geri dusuyor
# (`scripts/olcum/51_sentetik_arena.py:1202`).
#
# GERCEK KUSUR BASKA: model bariyeri YALNIZ YATAYA YAKIN acilarda goruyor.
# Sartname karesi dondurulup v36'ya verildi (bariyer maskesi AYNI donusumle
# tasindi):
#
#     aci     model ENGEL orani        aci     model ENGEL orani
#       0     %99,9                     60     %0,0     <- KOR
#      15     %99,8                     75     %100,0
#      30     %99,6                     90     %30,8
#      45     %69,2                    120     %0,0     <- KOR
#                                      135     %0,0     <- KOR
#
# Kok neden: `codes/runs/segment/gece_v7a_v35taban/args.yaml` -> degrees: 0.0
# ve flipud: 0.0. v36 HIC DONDURME ARTIRIMI GORMEDEN egitildi. Nadir (dik
# bakan) hava goruntusunde IHA'nin yonelimi KEYFIDIR.
#
# KATMAN 2 bu yuzden KALIR (ve T184'te acidan bagimsiz hale getirildi):
# model tek basina guvenilir degildir ve klasik dedektor yalniz ENGEL
# katmanina ekler -> serbest alan yalniz KUCULUR (madde 15).
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


def _bariyer_kollari(kirmizi, w, h, uzun_eksen):
    """Kroma maskesinden UZUN-INCE bilesenleri sec.

    `uzun_eksen=False` T67'nin OZGUN olcutudur (yalniz YATAY: `bw > 4*bh`,
    esik goruntu GENISLIGINE oranli). `uzun_eksen=True` ayni olcutu
    eksenden BAGIMSIZ uygular (`max > 4*min`, esik `max(w, h)`e oranli).
    """
    import numpy as _np
    import cv2 as _cv2
    n, lbl, st, _ = _cv2.connectedComponentsWithStats(kirmizi, 8)
    asgari_alan = max(1.0, BARIYER_ASGARI_ALAN_ORANI * w * h)
    olcu = max(w, h) if uzun_eksen else w
    asgari_gen = max(2.0, BARIYER_ASGARI_GENISLIK_ORANI * olcu)
    kol = _np.zeros((h, w), _np.uint8)
    for i in range(1, n):
        _x, _y, bw, bh, alan = st[i]
        if alan < asgari_alan:
            continue
        if uzun_eksen:
            # 🔴 EKSEN HIZALI KUTU EGIK CUBUGU KARE GOSTERIR. 45 derecelik
            # ince bir kolun (bw, bh) kutusu neredeyse KAREDIR ve en/boy
            # olcutu onu HB sanip ELER. Gercek uzun/kisa kenar DONDURULMUS
            # dikdortgenden (`minAreaRect`) okunur; boylece olcut her acida
            # ayni seyi olcer.
            noktalar = _cv2.findNonZero((lbl == i).astype(_np.uint8))
            if noktalar is None:
                continue
            (_mx, _my), (ma, mb), _aci = _cv2.minAreaRect(noktalar)
            uzun, kisa = max(ma, mb), min(ma, mb)
            if kisa <= 0.0:
                uzun, kisa = float(max(bw, bh)), float(min(bw, bh))
        else:
            uzun, kisa = bw, bh
        # UZUN ve INCE olmali: HB pedi KAREDIR ve buradan GECEMEZ.
        # Ayrim RENKLE DEGIL SEKILLE yapilir; bir KARE dondurulunce de
        # KAREDIR (dondurulmus dikdortgeni de karedir), bu yuzden acidan
        # bagimsiz olcut HB'yi hala eler.
        if uzun > BARIYER_EN_BOY_ORANI * max(1.0, kisa) and uzun > asgari_gen:
            kol[lbl == i] = 1
    return kol


def ince_bariyer_maskesi(bgr):
    """Uzun/ince/yuksek-kromali cubuk yapilari isaretle (KATMAN 2 engeli).

    Girdi BGR goruntu; cikti ayni (h, w) boyutunda uint8 ikili maske.
    Fail-closed: cozulemeyen girdide BOS maske doner — yani hicbir sey
    EKLEMEZ. Bu olcut hicbir kosulda serbest alani BUYUTEMEZ (madde 15).

    🔴 T184 (ON_KAYIT 2026-08-28 SS1a · REVIEW_LOG D-324): bu dedektor
    DONME KORUYDU. Bilesen olcutu `bw > 4*bh` idi ve serit araliklarini
    kapatan cekirdek YATAYDI — yani YALNIZ yatay kolu buluyordu.
    Sartname karesinde OLCULDU:

        dondurme      bariyer pikseli    bulunan kol
        0 derece            3644              2
        90 derece              0              0      <-- TAMAMEN KOR
        180 derece          3644              2
        270 derece             0              0      <-- TAMAMEN KOR

    IHA arenaya 90 derece farkli bir yonelimle girerse kapali koridorlar
    ACIK gorunur -> yanlis guzergah -> sartname SS2.1 uyarinca 0 PUAN.
    Model yardim edemez: bariyer piksellerinin %0,0'ini ENGEL diyor (D-92).

    MONOTONIKLIK KURGU GEREGIDIR: sonuc, OZGUN olcutun maskesi ile
    eksenden bagimsiz olcutun maskesinin BIRLESIMIDIR. Birlesim, ozgun
    maskenin her zaman UST KUMESIDIR; dolayisiyla engel katmani yalniz
    BUYUR, serbest alan yalniz KUCULUR (madde 15) — bu, olcumle degil
    INSAAT ile garantidir.
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
    # Cekirdek uzun eksene oranlidir; sabit piksel cozunurluk degisince kayar.
    kx = max(3, int(round(max(w, h) * BARIYER_KAPAMA_ORANI)) | 1)

    # (a) OZGUN yol: yatay kapama + yalniz-genislik olcutu (T67 birebir).
    kx0 = max(3, int(round(w * BARIYER_KAPAMA_ORANI)) | 1)
    ky0 = max(3, int(round(kx0 / 12.0)) | 1)
    ozgun = _bariyer_kollari(
        _cv2.morphologyEx(kirmizi, _cv2.MORPH_CLOSE,
                          _cv2.getStructuringElement(_cv2.MORPH_RECT, (kx0, ky0))),
        w, h, uzun_eksen=False)

    # (b) ACIDAN BAGIMSIZ yol: kapama CIZGI cekirdekleriyle ALTI ACIDA yapilir.
    # 🔴 Neden: gercek bariyer KIRMIZI-BEYAZ SERITLIDIR; kroma maskesi yalniz
    # kirmizi parcalari birakir ve kolu TEK PARCA yapmak icin bu araliklarin
    # KOL DOGRULTUSUNDA kapatilmasi gerekir. Eksen hizali (yatay/dikey)
    # cekirdek, 30-60 derecedeki bir kolun capraz araliklarina KOPRU KURMAZ;
    # olculdu: sartname karesinde 30/45/60/120/135/150 derecede 0 kol.
    # Cizgi cekirdekleri 15 derecelik adimlarla tarandiginda her dogrultu
    # kapsanir. Birlesim alindigi icin sonuc her tekil kapamanin UST KUMESIDIR.
    cizgiler = []
    for _derece in (0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165):
        cek = _np.zeros((kx, kx), _np.uint8)
        _t = _np.deg2rad(_derece)
        _yc = (kx - 1) / 2.0
        _dx, _dy = _np.cos(_t), _np.sin(_t)
        for _adim in _np.linspace(-_yc, _yc, kx * 2):
            _px = int(round(_yc + _adim * _dx))
            _py = int(round(_yc + _adim * _dy))
            if 0 <= _px < kx and 0 <= _py < kx:
                cek[_py, _px] = 1
        cizgiler.append(cek)
    coklu = _np.zeros_like(kirmizi)
    for cek in cizgiler:
        coklu = _np.maximum(coklu, _cv2.morphologyEx(kirmizi, _cv2.MORPH_CLOSE, cek))
    bagimsiz = _bariyer_kollari(coklu, w, h, uzun_eksen=True)

    return _np.maximum(ozgun, bagimsiz)


# T67: bariyer hangi maske katmanina EKLENIR. `sinif_semasi.ENGEL` ile ayni
# olmak ZORUNDADIR; ama `sinif_semasi` Jetson saha paketinde YOKTUR
# (`scripts/jetson_paket_hazirla.py` KOPYALAR listesi), bu yuzden buradan
# import EDILEMEZ — sahada ImportError olurdu. Iki degerin esitligi
# `tests/test_ince_bariyer.py` ile kilitlenir; biri degisip digeri kalamaz.
BARIYER_ENGEL_SINIFI = 1


# ════════════════════════════════════════════════════════════════════════════
# T153 · INCE BETON SERIT CIKARICISI — KATMAN 2   (ON_KAYIT §13 · D-289/D-290)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (gercek karede olculdu, results/gece_20260826/sizinti/rapor.md):
# v35'in engel->zemin sizintisi TEK kaynakli — yol kenarindaki BETON DRENAJ
# KANALI (acik gri/beyaz, ~5-15 px @960, uzun) zemin sayiliyor ve rota onun
# ustune dusuyor: val82'de 10 yanlis guzergahin 8'i bu kanal ustunde (D-290),
# test29'da uretim v35'in 6 rotasindan 5'i yol ustunde degil (196: beton
# kanal ustunde, D-289). Uc model de (v35/v3/v6) ayni sizintiyi veriyor;
# egitim verisinde kanal yeterince temsil edilmedigi icin bu tur icin cozum
# T67 kalibinda KATMAN 2 klasik dedektordur: yalniz ENGEL katmanina EKLER,
# serbest alan (`zemin AND NOT engel`) yalniz KUCULUR (madde 15, CONTRACTS SS2).
#
# AYIRT EDICI UC OZELLIK (T67'nin "kroma+sekil" kalibinin beton karsiligi):
#   1. ACIK RENK   : LAB L cok yuksek VE kroma dusuk. D-290 karelerinde
#                    olculdu (512 tuval, f157/f196/f213): kanal L 225-255
#                    (cogu doygunluga yakin), kroma 0-5; acik toprak yol
#                    L 180-230, kuru ot L 120-200 ama benekli. Beton/bordur
#                    gri-beyazdir; kirmizi bariyer ve HB kromayla T67/T72'ye
#                    kalir, buraya GIRMEZ (iki dedektor ayni yapiyi secemez).
#   2. DAR         : fiziksel ~0,3-1,2 m; 512 tuvalde 3-14 px (ON_KAYIT §13).
#                    Genislik ORAN olarak tutulur (CONTRACTS SS8), tuval
#                    genisligiyle carpilir; mutlak piksel cozunurlukte kayar.
#                    Genislik = bilesenin uzaklik donusumu maksimumunun 2 kati
#                    (egri seritte minAreaRect sisirir, bu sismez). ALT sinir
#                    kablo/tel/kenar cizgisi gibi 1-2 px yapilari, UST sinir
#                    YOLUN KENDISINI dislar — ust sinir kalkarsa genis acik
#                    yol da engel olur (tests/test_t153 mutasyonu bunu kanitlar).
#   3. UZUN        : uzunluk = alan/genislik; en/boy >= 4 (T67 ile ayni oran)
#                    VE asgari uzunluk (kisa parlak lekeler — tas, arac
#                    tavani, kuru ot demeti — uzun degildir; 40 px @512,
#                    kanal olceginde ~3 m).
#   4. DOLU ve KONTRASTLI: aday maske once kucuk bir ACMA'dan gecer (kuru ot
#                    benekleri ve 1-2 px zincirleri kirilir; 3 px'lik serit
#                    sag kalir), sonra KAPAMA ile seritteki 1-2 px kopukluklar
#                    koprulenir. Her bilesen cevresindeki halkadan (genislik
#                    ust siniri kadar) en az 30 L birimi parlak olmali —
#                    parlak yol ortasindaki daha parlak lekeler elenir.
# TOP-HAT KULLANILMADI: acma tabanli top-hat, benekli kuru otta (her 29 px
# pencerede koyu golge var) her yeri "parlak" gosterdi (kesif olcumu: L 170
# piksellerde top-hat 100+); ayrim mutlak parlaklik + sekil + halka
# kontrastiyla yapilir.
#
# 🔴 VARSAYILAN KAPALI (ON_KAYIT §13). Benimseme kurali sonuc gorulmeden
# yazildi: v35'te 111 karede YANLIS GUZERGAH >= %50 azalir VE mesru rota
# kaybi <= 1 VE yeni FP 0 VE sentetik K1-K6 birebir VE 67'de red <= 5.
# Biri tutmazsa KAPALI kalir. Acik/kapali secimi: `get_masks(...,
# ince_beton_serit=)` parametresi, yoksa ortam degiskeni, yoksa bu sabit.
INCE_BETON_SERIT_ETKIN = False
INCE_BETON_SERIT_ORTAM_DEGISKENI = "NAVITAS_INCE_BETON_SERIT"   # "1" acik, "0" kapali
INCE_BETON_L_ESIGI = 225                 # LAB L (0-255): kanal 225-255 olculdu; acik toprak yol cogunlukla altinda
INCE_BETON_KROMA_UST = 20                # sqrt(a^2+b^2) ust siniri (T67 kirmizi esigi 25'in altinda)
INCE_BETON_KONTRAST_ESIGI = 30           # bilesen ort. L - cevre halkasi ort. L alt siniri (L birimi)
INCE_BETON_GENISLIK_ALT_ORANI = 3.0 / 512.0     # ~0,00586 · 3 px @512
INCE_BETON_GENISLIK_UST_ORANI = 14.0 / 512.0    # ~0,02734 · 14 px @512 — YOLU DISLAR
INCE_BETON_EN_BOY_ORANI = 4.0            # uzunluk / genislik; T67 ile ayni
INCE_BETON_ASGARI_UZUNLUK_ORANI = 40.0 / 512.0  # ~0,078 · 40 px @512 (~3 m kanal olceginde)
INCE_BETON_KAPAMA_ORANI = 5.0 / 512.0    # serit icindeki <= 4 px kopuklugu koprule (5 px cekirdek @512)


def ince_beton_serit_maskesi(bgr):
    """Acik renkli, DAR ve UZUN beton seritleri isaretle (KATMAN 2 engeli).

    Girdi BGR goruntu; cikti ayni (h, w) boyutunda uint8 ikili maske.
    Fail-closed: cozulemeyen girdide None doner (cagiran hicbir sey
    EKLEMEZ); kucuk girdide bos maske. Hicbir kosulda serbest alani
    BUYUTEMEZ (madde 15) — yalniz ENGEL katmanina OR'lanmak icin vardir.
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
    L = lab[:, :, 0]
    a = lab[:, :, 1].astype(_np.int32) - 128
    b = lab[:, :, 2].astype(_np.int32) - 128
    kroma2 = a * a + b * b

    # Genislik sinirlari ORANDAN piksele (tuval genisligi uzerinden).
    ust = max(2, int(round(w * INCE_BETON_GENISLIK_UST_ORANI)))
    alt = max(1.0, w * INCE_BETON_GENISLIK_ALT_ORANI)
    asgari_uzunluk = max(2.0, w * INCE_BETON_ASGARI_UZUNLUK_ORANI)
    acma = max(1, int(round(alt)) | 1)                      # 3 px @512
    kapama = max(1, int(round(w * INCE_BETON_KAPAMA_ORANI)) | 1)

    aday = ((L >= INCE_BETON_L_ESIGI)
            & (kroma2 <= INCE_BETON_KROMA_UST * INCE_BETON_KROMA_UST)).astype(_np.uint8)
    if not aday.any():
        return _np.zeros((h, w), _np.uint8)
    aday = _cv2.morphologyEx(
        aday, _cv2.MORPH_OPEN,
        _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (acma, acma)))
    aday = _cv2.morphologyEx(
        aday, _cv2.MORPH_CLOSE,
        _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (kapama, kapama)))
    if not aday.any():
        return _np.zeros((h, w), _np.uint8)

    n, lbl, st, _ = _cv2.connectedComponentsWithStats(aday, 8)
    uzaklik = _cv2.distanceTransform(aday, _cv2.DIST_L2, 3)
    halka_cekirdek = _cv2.getStructuringElement(
        _cv2.MORPH_ELLIPSE, (2 * ust + 1, 2 * ust + 1))
    Lf = L.astype(_np.float32)
    out = _np.zeros((h, w), _np.uint8)
    for i in range(1, n):
        x, y, bw, bh, alan = (int(v) for v in st[i])
        if alan < alt * asgari_uzunluk:
            continue
        parca = (lbl[y:y + bh, x:x + bw] == i)
        genislik = 2.0 * float(uzaklik[y:y + bh, x:x + bw][parca].max())
        if genislik < alt or genislik > ust:
            continue
        uzunluk = alan / genislik
        if uzunluk < asgari_uzunluk or uzunluk < INCE_BETON_EN_BOY_ORANI * genislik:
            continue
        # Halka kontrasti: bilesen, cevresindeki (aday olmayan) halkadan parlak mi?
        x0, y0 = max(0, x - ust), max(0, y - ust)
        x1, y1 = min(w, x + bw + ust), min(h, y + bh + ust)
        pencere = _np.zeros((y1 - y0, x1 - x0), _np.uint8)
        pencere[y - y0:y - y0 + bh, x - x0:x - x0 + bw] = parca
        halka = (_cv2.dilate(pencere, halka_cekirdek) > 0) & (pencere == 0) \
            & (aday[y0:y1, x0:x1] == 0)
        if not halka.any():
            continue
        Lp = Lf[y0:y1, x0:x1]
        if float(Lp[pencere > 0].mean()) - float(Lp[halka].mean()) < INCE_BETON_KONTRAST_ESIGI:
            continue
        out[y:y + bh, x:x + bw][parca] = 1
    return out


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

# T198 · D-344: HB FIZIKSEL OLCEK BANDI. Yukaridaki asgari alan olcutu KAREYE
# ORANTILIDIR, fiziksel degil — uretim 512x512'de esik yalniz 77 px (~9x9) ve
# kare-kirmizi bir COP bu suzgecten gecebiliyor (D-338: yerdeki burusuk
# kirmizi-beyaz ambalaj 38x31 px kutuyla "ped" oldu). HB 2 m x 2 m'dir (SS2.1),
# yani `mpp` biliniyorsa pedin kenari ~ HB_KENAR_M / mpp olmalidir.
#
# BANT UYDURULMADI. ON_KAYIT D-344'teki kuralla OLCUMDEN turetildi: kabul
# kumesindeki (n=260) GERCEK pedlerin `bulunan_kenar / beklenen_kenar` orani
#     %0,5: 1,016 · medyan 1,055 · %99,5: 1,094      (260/260 ped BULUNDU)
# En dar simetrik log-bant [1,016 · 1,094]; guvenlik payi 1,15 ile:
HB_OLCEK_BANDI = (0.883, 1.258)      # bulunan_kenar / (HB_KENAR_M / mpp)
HB_KAPAMA_ORANI = 10.0 / 640.0      # cerceve + H harfini TEK parcaya birlestir


def _hb_ham_kirmizi(im):
    """HAM kirmizi katman: kroma esigi + bariyer cikarmasi — KAPAMA ve kutu
    doldurma UYGULANMAMIS. `hb_maskesi` bunun ustune bolgelestirme yapar;
    SEKIL bilgisi yalniz bu katmanda yasar (T198/D-379: `hb_maskesi` ciktisi
    bilerek kutu doldurur, poster onizlemesinde solidity 1,0 olctuk).
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return None
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
    return kirmizi


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

    kirmizi = _hb_ham_kirmizi(im)
    if kirmizi is None:
        return None

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


# ── T198 kalan is (D-379): HB SEKIL DOGRULAMASI ──────────────────────────
# Sablon geometrisi BASILI POSTERIMIZIN matbaa foyunden (results/hb_baski/
# OKUBENI.md) — onizleme PNG'sinden DEGIL (kendi kendini sinamak cevrimsel
# olurdu). Foydeki olculer uretecin kendi cizimimden alinmisti; yani 30 Eylul
# testindeki gercek ped bu sablonun kendisidir.
HB_SEKIL_CERCEVE_ORANI = 0.0458        # kirmizi cerceve kalinligi / kenar
HB_SEKIL_H_KUTU_ORANI = (0.405, 0.482)  # H dis kutusu (en, boy) / kenar
HB_SEKIL_KOL_ORANI = 0.0955             # H kol kalinligi / kenar
HB_SEKIL_TUVAL = 128                    # kanonik kiyas tuvali (px)
# ESIK — UYDURULMADI (D-379): ON_KAYIT'taki kuralla (pozitif %0,5 dilimi x
# 0,85 payi) t66'nin 260 pedinden turetildi (q=0,20772... x 0,85). TAM
# HASSASIYETLE yazilidir: 4 haneye yuvarlanan ilk surum, esikten 2e-5
# uzaktaki bir kareyi olcumden FARKLI degerlendiriyordu — sabit, turetilen
# degerin BIREBIR kendisi olmak zorundadir (nobetci JSON'la esitligi sinar).
# Olculen ayrisma: pozitifler 0,189-0,467 · otomobiller 0,076-0,178 (TAM
# ayrik ama pay ince, +0,011); sentetik 26 px ped puanin EN KOTU olcegi
# (posterin kendisi 0,918 verdi). KARE DUZEYI (uretim semantigi, sekil reddi
# NIHAI): 67 otomobil FP karesinin 64'u duser (%4,5 kalir), kirsal 15 -> 1.
# ⚠ BILINEN SINIR: KUSURSUZ dolu kirmizi kare ~0,29 alir ve GECER (gercek
# otomobiller puruzlu maskeyle dusuyor) — test_t198_hb_sekil kilitler.
# Sayiyi degistirmek YENI on kayit ister (D-107).
HB_SEKIL_ESIGI = 0.17656308851224103


def hb_sekil_sablonu(boy=HB_SEKIL_TUVAL):
    """Kanonik ped sablonu: cerceve halkasi + ortalanmis H. SAYILARDAN cizilir."""
    import numpy as _np
    s = _np.zeros((boy, boy), _np.uint8)
    t = max(1, int(round(boy * HB_SEKIL_CERCEVE_ORANI)))
    s[:t, :] = 1
    s[-t:, :] = 1
    s[:, :t] = 1
    s[:, -t:] = 1
    hw = int(round(boy * HB_SEKIL_H_KUTU_ORANI[0]))
    hh = int(round(boy * HB_SEKIL_H_KUTU_ORANI[1]))
    kol = max(1, int(round(boy * HB_SEKIL_KOL_ORANI)))
    x0 = (boy - hw) // 2
    y0 = (boy - hh) // 2
    s[y0:y0 + hh, x0:x0 + kol] = 1                      # sol kol
    s[y0:y0 + hh, x0 + hw - kol:x0 + hw] = 1            # sag kol
    cy = y0 + (hh - kol) // 2
    s[cy:cy + kol, x0:x0 + hw] = 1                      # capraz kol
    return s


def hb_sekil_puani(bgr, kutu):
    """Aday kutusundaki HAM kirmizinin ped sablonuyla IoU'su. Olculemezse None.

    ON_KAYIT (results/hb_sekil/ON_KAYIT.md §2, sonuc gorulmeden donduruldu):
    ham kirmizi -> minAreaRect ile ters dondur -> siki kirp -> 128x128 ->
    sablonla IoU; H'nin yonelim belirsizligi icin 0/90/180/270'in en buyugu.

    ⚠ MADDE 15: puan yalniz adayi REDDETMEKTE kullanilir (HEDEF_YOK yonu);
    serbest alana dokunmaz.
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return None
    im = _np.asarray(bgr)
    if im.ndim != 3 or im.shape[2] != 3 or im.size == 0:
        return None
    ham = _hb_ham_kirmizi(im.astype(_np.uint8))
    if ham is None:
        return None
    try:
        x, y, bw, bh = (int(v) for v in kutu)
    except (TypeError, ValueError):
        return None
    if bw <= 1 or bh <= 1:
        return None
    h, w = ham.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(w, x + bw), min(h, y + bh)
    parca = ham[y0:y1, x0:x1]
    if parca.size == 0 or not parca.any():
        return None
    pts = _cv2.findNonZero(parca)
    (mx, my), (mw, mh), aci = _cv2.minAreaRect(pts)
    if mw < 2 or mh < 2:
        return None
    # Dondurme KIRPMASIN: parca, kosegen boyutlu tuvale ORTALANIR ve tuval
    # merkezi etrafinda dondurulur — icerik hicbir acida disari tasamaz.
    ph, pw = parca.shape[:2]
    D = int(_np.ceil((pw * pw + ph * ph) ** 0.5)) + 4
    tuval = _np.zeros((D, D), _np.uint8)
    ox, oy = (D - pw) // 2, (D - ph) // 2
    tuval[oy:oy + ph, ox:ox + pw] = parca
    M = _cv2.getRotationMatrix2D((D / 2.0, D / 2.0), aci, 1.0)
    don = _cv2.warpAffine(tuval, M, (D, D), flags=_cv2.INTER_NEAREST)
    nz = _cv2.findNonZero(don)
    if nz is None:
        return None
    bx, by, bbw, bbh = _cv2.boundingRect(nz)
    if bbw < 2 or bbh < 2:
        return None
    kirp = don[by:by + bbh, bx:bx + bbw]
    aday = _cv2.resize(kirp, (HB_SEKIL_TUVAL, HB_SEKIL_TUVAL),
                       interpolation=_cv2.INTER_NEAREST)
    sb = hb_sekil_sablonu()
    en_iyi = 0.0
    a = aday
    for _ in range(4):
        kes = int(_np.count_nonzero((a > 0) & (sb > 0)))
        bir = int(_np.count_nonzero((a > 0) | (sb > 0)))
        if bir:
            en_iyi = max(en_iyi, kes / bir)
        a = _np.rot90(a)
    return float(en_iyi)


def hb_konumu(bgr, mpp=None, sekil_esigi=None):
    """HB merkezi, kutusu ve piksel kenari. Bulunamazsa None.

    Birden fazla aday varsa EN BUYUK secilir (sahnede tek HB vardir; coklu
    aday gurultudur ve en buyugu en guvenilir olandir).

    mpp verilirse (T198 · ON_KAYIT D-344) FIZIKSEL OLCEK DENETIMI uygulanir:
    HB 2 m x 2 m oldugundan kenari ~ `HB_KENAR_M / mpp` px olmalidir;
    `HB_OLCEK_BANDI` disinda kalan aday HB SAYILMAZ.

    sekil_esigi verilirse (T198 kalan is · D-379) SEKIL DENETIMI uygulanir:
    adayin ham kirmizisi ped sablonuyla kiyaslanir (`hb_sekil_puani`);
    esigin altindaki aday HB SAYILMAZ. D-295'in olctugu boslugu kapatir:
    dogru BOYUTTAKI kirmizi otomobil olcek denetiminden gecer, sekilden
    gecemez.

    ⚠ GERIYE DONUK UYUM: `mpp`/`sekil_esigi` VERILMEZSE davranis AYNEN
    eskisi gibidir. Mevcut butun cagri yerleri etkilenmez; her denetim
    yalniz onu BILEN cagiran icin acilir. Uretime baglama T150'dir ve
    MIMAR KARARIDIR.

    ⚠ Bu denetimler serbest alani BUYUTMEZ: yalnizca aday REDDEDEBILIR.
    Reddedilirse `analyze_path` HEDEF_YOK ile cekimser kalir — fail-closed.
    """
    import numpy as _np
    try:
        import cv2 as _cv2
    except ImportError:                      # pragma: no cover
        return None
    # ── Parametre korumalari (D-383, curutucu bulgusu) — FAIL-CLOSED ──────
    # Onceden gecersiz mpp (NaN / negatif) olcek denetimini SESSIZCE
    # atlatiyordu ("mpp > 0" False -> denetimsiz kabul), gecersiz sekil_esigi
    # (NaN) sekil kapisini SESSIZCE kapatiyordu (puan < NaN daima False).
    # Istenen denetim uygulanamiyorsa cevap HEDEF_YOK cekimserligidir.
    if mpp is not None and (not isinstance(mpp, Real) or isinstance(mpp, bool)
                            or not math.isfinite(float(mpp))
                            or float(mpp) <= 0.0):
        return None
    if sekil_esigi is not None and (not isinstance(sekil_esigi, Real)
                                    or isinstance(sekil_esigi, bool)
                                    or not math.isfinite(float(sekil_esigi))):
        return None
    # 🔴 SEKIL KAPISI OLCEKSIZ ACILMAZ (D-383): sekil puani tek basina kucuk
    # kirmizi lekeleri de gecirebilir (26x18 px blob 0,18-0,21 aldi, olculdu);
    # uretim yapilandirmasi HER ZAMAN olcek+sekil CIFTIDIR (T150). Yarim
    # yapilandirma fail-closed reddedilir.
    if sekil_esigi is not None and mpp is None:
        return None

    ped = hb_maskesi(bgr)
    if ped is None or not ped.any():
        return None
    n, lbl, st, mrk = _cv2.connectedComponentsWithStats(ped, 8)
    if n <= 1:
        return None
    # Adaylar BUYUKTEN kucuge; olcek denetimi acikken banda uyan aday(lar)
    # degerlendirilir. Denetim kapaliyken (mpp yok) davranis eskisiyle
    # AYNIDIR: en buyuk aday.
    sira = sorted(range(1, n), key=lambda k: -int(st[k, 4]))
    banda_uyan = []
    for i in sira:
        x, y, bw, bh, alan = (int(v) for v in st[i][:5])
        if mpp is not None:
            beklenen = HB_KENAR_M / float(mpp)
            if beklenen > 0:
                o = ((bw + bh) / 2.0) / beklenen
                if not (HB_OLCEK_BANDI[0] <= o <= HB_OLCEK_BANDI[1]):
                    continue          # fiziksel olcege uymuyor -> HB DEGIL
        banda_uyan.append(i)
        if sekil_esigi is None:
            break                     # eski davranis: ilk (en buyuk) yeter
    if not banda_uyan:
        return None                   # aday var ama HICBIRI 2 m'lik ped degil
    secilen = banda_uyan[0]
    secilen_puan = None
    if sekil_esigi is not None:
        # 🔴 SECIM EN YUKSEK SEKIL PUANIYLA (D-383). Onceki iki semantik de
        # curutuldu: (a) dusme, buyuk otomobil reddedilince kucuk lekelerden
        # 59/67 kare FP uretiyordu; (b) NIHAI ret, sahnede GERCEK ped
        # dururken banda giren daha buyuk bir sahtekar yuzunden pedi de
        # olduruyordu — ustelik dolu kare (0,290) esigi GECTIGI icin buyuk-
        # once siralama hedefi CALDIRIYORDU (ped 0,935'ken!). Banda uyan tum
        # adaylar puanlanir; esigi gecen EN YUKSEK puanli secilir.
        en_iyi = None
        for i in banda_uyan:
            x, y, bw, bh = (int(v) for v in st[i][:4])
            puan = hb_sekil_puani(bgr, (x, y, bw, bh))
            # OLCULEMEDI != GECTI: puani uretilemeyen aday yarisamaz.
            if puan is None or puan < float(sekil_esigi):
                continue
            if en_iyi is None or puan > en_iyi[1]:
                en_iyi = (i, puan)
        if en_iyi is None:
            return None               # banda uyanlarin HICBIRI ped gibi degil
        secilen, secilen_puan = en_iyi
    i = secilen
    x, y, bw, bh, alan = (int(v) for v in st[i][:5])
    sonuc = {
        "merkez": (float(mrk[i][0]), float(mrk[i][1])),
        "kutu": (x, y, bw, bh),
        "kenar_px": float((bw + bh) / 2.0),
        "alan_px": int(alan),
        "aday_sayisi": int(n - 1),
    }
    if secilen_puan is not None:
        sonuc["sekil_puani"] = float(secilen_puan)
    return sonuc


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

# ════════════════════════════════════════════════════════════════════════════
# T188 · ZEMIN KAPAMASININ FIZIKSEL TAVANI  (ON_KAYIT 2026-08-28 SS8 · D-326)
# ════════════════════════════════════════════════════════════════════════════
# 🔴 KUSUR (olculdu): `rpi_inference` zemin maskesine morfolojik KAPAMA
# uyguluyor ve cekirdek `max(7, w // 30)` — yani goruntu GENISLIGININ ORANI,
# METRIK DEGIL. 512 px'te 17 px, 3840 px'te 128 px olur. mpp 0,05'te 17 px =
# 0,85 m: bir DUBADAN buyuk ve arac yaricapiyla kiyaslanabilir.
#
# SONUC: duba sirasi zemin maskesinde yalniz DELIK birakirsa (model onlari
# ENGEL sinifina koymayi kacirirsa) kapama delikleri GERI DOLDURUYOR ve serit
# ACIK cikiyor. Sentetik olcum, dort duba yapilandirmasinin DORDUNDE de:
#
#   duba capi/araligi     ENGEL sinifinda     yalniz ZEMIN DELIGI
#   0,40 m / 1,00 m       KAPALI (dogru)      yol=2  guven 1.00  <- YANLIS
#   0,60 m / 1,20 m       KAPALI (dogru)      yol=2  guven 1.00  <- YANLIS
#   0,30 m / 0,80 m       KAPALI (dogru)      yol=2  guven 1.00  <- YANLIS
#
# ⚠ KAPAMA, SERBEST ALANI BUYUTEN TEK ISLEMDIR — madde 15 tam olarak bunu
# yasaklar. Bu yuzden fiziksel bir TAVAN konur: kapama yalnizca ALGI
# GURULTUSU olcegindeki delikleri kapatabilir, GERCEK bir engeli degil.
#
# TAVAN `costmap_path_finder.ALGI_PAYI_M` ile AYNI degerdir (0,25 m): o sabit
# "engel maskesinin gercek engelden ic kalma payi"dir, yani algi belirsizligi
# olcegidir. Kapama bundan buyuk bir bosluga DOKUNAMAZ.
#
# UYGULAMA KURALI — cekirdek yalnizca KUCULEBILIR:
#     cekirdek = min(eski_cekirdek, ceil(KAPAMA_AZAMI_M / mpp))
# Boylece serbest alan yalniz KUCULUR ve madde 15 olcumle degil INSA ile
# korunur. `mpp` bilinmiyorsa davranis DEGISMEZ (olculemeyen durumda
# degisiklik yapilmaz — fail-safe).
KAPAMA_AZAMI_M = 0.25


def kapama_cekirdegi_px(mevcut_px, mpp):
    """Zemin kapama cekirdegini FIZIKSEL tavanla sinirla.

    `mevcut_px` cagiranin cozunurluk oranindan hesapladigi cekirdek.
    `mpp` gecerli degilse `mevcut_px` AYNEN doner (davranis degismez).
    Donen deger hicbir kosulda `mevcut_px`ten BUYUK olamaz.
    """
    from numbers import Real as _Real
    import math as _math
    try:
        mevcut = int(mevcut_px)
    except (TypeError, ValueError):
        return mevcut_px
    if isinstance(mpp, bool) or not isinstance(mpp, _Real):
        return mevcut
    m = float(mpp)
    if not (m > 0.0) or _math.isinf(m) or _math.isnan(m):
        return mevcut
    tavan = int(_math.ceil(KAPAMA_AZAMI_M / m))
    return max(1, min(mevcut, tavan))


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


# ── Sartname sure limitleri (§6.2 / §6.4) — K5+K6 (2026-08-26) ───────────────
# Kaynak: Ileri_Otonom_Sistemler_Tasarim_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf
# (venv fitz ile okundu, sayfa 23-24):
#   §6.2 "Ucus suresi, IHA'nin mancinik sisteminden ayrilmasi (firlatma) ile
#        baslar. Guzergah tespiti, veri aktarimi ve IHA'nin parasutle inisini
#        tamamlamasi ile sona erer. Bu islemler icin taninan maksimum sure
#        15 dakikadir."
#   §6.2 "... IKA'nin HB'ye ulasmasi icin verilen maksimum sure 10 dakikadir.
#        Bu surenin asilmasi durumunda IKA gorevi basarisiz kabul edilecektir."
#   §6.4 "Sure Asimi: IHA gorev suresi ... Bu surecler icin tanimlanan azami
#        sure 15 dakikadir."
# (sayfa 19, §5 FDR gorev test ucusu: tum operasyon "maksimum 10 dakika" —
#  bu final sahasi icin degil, FDR test ucusu icindir; saha degeri §6.2'dir.)
#
# NEDEN IKI AYRI DEADLINE (K5): ika_nav eskiden TEK 60 s deadline ile
# rota + IHA_LANDED + IKA_GO bekliyordu. Sahada inis firlatmadan dakikalar
# sonra gelir; 60 s'de IKA gorevi birakirdi. Bekleme suresi IHA gorev suresine
# (15 dk), surus suresi IKA gorev suresine (10 dk) baglanir; surus saati izin
# geldigi ANDA baslar, beklemeye harcanan sure surusten dusulmez.
SARTNAME_IHA_GOREV_SURESI_S = 15 * 60.0   # §6.2 / §6.4 · firlatma -> inis
SARTNAME_IKA_GOREV_SURESI_S = 10 * 60.0   # §6.2 · HB'ye ulasma
IKA_BEKLEME_SURESI_S = SARTNAME_IHA_GOREV_SURESI_S   # rota+inis+IKA_GO beklemesi
IKA_SURUS_SURESI_S = SARTNAME_IKA_GOREV_SURESI_S     # izin -> HB

# ── IKA KINEMATIK SABITLERI — TEK KAYNAK (T213 · CONTRACTS SS4 · D-438 f) ──
# NEDEN: `ika_nav.MAX_SPEED = 2.0`, `navitas_anim.cc` 1,1 ve kabul harnessi
# 0,30 — uc kopya, hicbiri CONTRACTS'ta degildi (D-438 olcum 2f). DDR fiziksel
# tavani 1,3 m/s'dir; 2,0 m/s komutu IKA'nin veremeyecegi hizi ister ve
# costmap'in TAKIP_HATA_M (0,50) varsayimini gecersiz kilar.
# Kaynak: rapor/NAVITAS_IKA_DDR.docx — 4x Keskinler KGX38 24 V 200 rpm
# redukturlu motor, O125 mm TPU teker, skid-steer.
#   azami hiz = 200 rpm x pi x 0,125 m / 60 = 1,309 m/s  -> DDR beyani 1,3 m/s
# Bu modul SAF Python'dur; `ika_nav` (IKA'da kosar) buradan okur, cv2 almaz.
# `costmap_path_finder` ayni adlari BURADAN alir, yeniden tanimlamaz.
IKA_TEKER_YARICAP_M = 0.0625          # O125 mm / 2 (DDR)
IKA_IZ_GENISLIGI_M = 0.4595           # OLCULDU 12 Eylul (ekip, serit metre; D-472). Onceki 0.39 TAHMIN'di;
                                      # URDF disa aktarimi 0.319 diyordu, ikisi de yanlis cikti.
IKA_AZAMI_HIZ_MS = 1.3                # DDR: 200 rpm x pi x O0,125 / 60 = 1,309 -> 1,3

# ── SS5.3.2 · DRONE ILE GOREV TEST UCUSU (FDA) — T170 · ON_KAYIT SS37 ──────
# Sartname: "Gorev test ucusunun basarili sayilabilmesi ... icin; gercek
# zamanli guzergah tespitinin alan hakem heyeti tarafindan dogrulanip
# onaylanmasi ve TUM OPERASYON SURECININ (kalkis, tespit, veri aktarimi ve
# inis) MAKSIMUM 10 DAKIKA icerisinde tamamlanmasi zorunludur. ... sureyi asan
# ... takimlar 0 PUAN alarak gorevden basarisiz sayilacaktir."
# 🔴 BU SS6.2'NIN SURESI DEGILDIR: SS6.2 yarisma gunune ait (IHA 15 dk, IKA
# 10 dk); burasi FDA test ucusunun TEK ve daha SIKI butcesidir. Sistemde
# SS5.3.2'nin diger iki parametresi zaten vardi (SENARYO_BOYUTLARI_M["FDA"]
# = 20,0 ve SARTNAME_ASGARI_IRTIFA_M = 30,0); eksik olan YALNIZ sureydi.
SARTNAME_FDA_OPERASYON_SURESI_S = 10 * 60.0
# SS6.2 hazirlik suresi — GUI'de CIPLAK yaziliydi (madde 16).
SARTNAME_HAZIRLIK_SURESI_S = 15 * 60.0

# ── §6.2 / §6.4 · IHA-UB ALAN IHLALI (T162 · ON_KAYIT SS28) ────────────────
# Sartname IHA'nin ucus bolgesini (IHA-UB) 300x300 m olarak tanimlar ve disina
# tasmayi ALAN IHLALI sayar. Bu sayi `comms/yks_gui.py` icinde UC YERDE CIPLAK
# yaziliydi (:735, :737, :941) — madde 16 ihlali; sartname degisirse kimse
# ceviremezdi. Tek tanim burasidir.
SARTNAME_IHA_UB_KENAR_M = 300.0
ALAN_IHLALI_SEBEBI = "ALAN_IHLALI"

# Dunya yaricapi — eşdikdörtgen (equirectangular) izdusum icin. Arena olcegi
# (yuzlerce metre) icinde bu yaklasim santimetre altinda hata verir; SciPy /
# pyproj GEREKMEZ (anayasa madde 4).
DUNYA_YARICAPI_M = 6_378_137.0


def yerel_konum_m(ref_lat, ref_lon, lat, lon):
    """(lat, lon) -> referans noktasina GORE yerel (x_dogu_m, y_kuzey_m).

    FAIL-CLOSED: gecersiz/eksik/bool/NaN/sonsuz girdi ya da |enlem| > 90 ise
    ``None`` doner. "Yaklasik konum" DONMEZ — konum bilinmiyorsa yayinlanmaz,
    cunku yayinlanan her x,y hakemin ALAN IHLALI kararini besler.
    """
    def _sayi(x):
        if isinstance(x, bool) or not isinstance(x, Real):
            return None
        try:
            d = float(x)
        except (OverflowError, TypeError, ValueError):
            return None
        return d if math.isfinite(d) else None

    rl, rn, l, n = (_sayi(ref_lat), _sayi(ref_lon), _sayi(lat), _sayi(lon))
    if None in (rl, rn, l, n):
        return None
    if abs(rl) > 90.0 or abs(l) > 90.0 or abs(rn) > 180.0 or abs(n) > 180.0:
        return None
    ortalama_enlem = math.radians((rl + l) / 2.0)
    x = math.radians(n - rn) * DUNYA_YARICAPI_M * math.cos(ortalama_enlem)
    y = math.radians(l - rl) * DUNYA_YARICAPI_M
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    return (x, y)


def iha_ub_ihlali(x, y, kenar_m=SARTNAME_IHA_UB_KENAR_M):
    """IHA-UB disina tasma varsa ``(sebep, aciklama)``, yoksa ``None``.

    Cerceve: koordinat sistemi IHA-UB'nin bir KOSESINDEN baslar (0..kenar),
    `comms/yks_gui.py` mini genel-sahasiyla ayni (`px / kenar * b`).
    Konum bilinmiyorsa (None) ihlal ILAN EDILMEZ — bilinmemek ihlal degildir;
    bilinmedigi ekranda AYRICA gorunur (sessiz sifir yasak).
    """
    if x is None or y is None:
        return None
    if isinstance(x, bool) or isinstance(y, bool):
        return None
    if not (isinstance(x, Real) and isinstance(y, Real)):
        return None
    x, y = float(x), float(y)
    if not (math.isfinite(x) and math.isfinite(y)):
        return None
    if 0.0 <= x <= kenar_m and 0.0 <= y <= kenar_m:
        return None
    return (ALAN_IHLALI_SEBEBI,
            f"IHA-UB ({kenar_m:.0f}x{kenar_m:.0f} m) disina cikildi; "
            f"olculen x={x:.1f} m y={y:.1f} m (sartname SS6.2/SS6.4)")


# NEDEN (K6): iha_inis_yayinci CLI IHA_LANDED'i yayinlayip cikiyordu; alici
# hb_timeout (3 s) sonra link_lost'a dusup IKA'yi guvenli durusta kilitliyordu.
# Inis sonrasi heartbeat en az IKA gorev suresi kadar surdurulur; link_lost
# ancak heartbeat GERCEKTEN kesilince olusur.
IHA_INIS_HEARTBEAT_SURESI_S = SARTNAME_IKA_GOREV_SURESI_S
IHA_INIS_HEARTBEAT_ARALIGI_S = 0.5        # < ika_receiver hb_timeout (3 s)
# ── K4 (sartname SS2.2.5): IKA_GO ACK'li tekrar gonderimi ─────────────────
# NEDEN: IKA_GO tek UDP/seri paketiydi; tek paket kaybi gorevi geri donulmez
# bitiriyordu (REVIEW_LOG D-02). YKS, IKA'dan ACK gelene dek AYNI seq ile
# tekrar gonderir; IKA tarafi latch oldugu icin mukerrer alim idempotenttir.
#   aralik   : SiK 433 MHz 57600 baud'da ~200 B cerceve + ACK gidis-donusu
#              < 100 ms; 0,25 s hem RTT'yi asar hem hatti bogmaz (4 pkt/s).
#   ust sinir: 20 deneme x 0,25 s = 5 s. IKA'nin baglanti-kaybi esigi
#              (`ika_receiver.hb_timeout` = 3 s) asildiktan sonra da 2 s
#              beklenir; sonra ekran KIRMIZI "IKA ONAY VERMEDI" der ve dugme
#              yeniden acilir — gorev kaybedilmez, operator tekrar tetikler.
IKA_GO_TEKRAR_ARALIGI_S = 0.25
IKA_GO_TEKRAR_UST_SINIRI = 20

# YKI ARM/DISARM — fiziksel eyleyici durumu gonderimde degil, yalniz IHA'nin
# Pixhawk COMMAND_ACK(ACCEPTED) kanitinda degisir. SiK tur suresi IKA_GO ile
# aynidir; 20 x 0,25 s = 5 s pencere tek paket kaybini tolere eder ama ACK yoksa
# dugmeyi sonsuza dek kilitlemez. Her tekrar AYNI seq ile gider.
ARM_TEKRAR_ARALIGI_S = 0.25
ARM_TEKRAR_UST_SINIRI = 20
# Ucus sirasinda yanlislikla DISARM tek tusa bagli olamaz. Deger degismedi;
# yalnizca GUI icindeki ciplak sabit karar sozlesmesinin tek kaynagina tasindi.
DISARM_TEYIT_SURESI_S = 4.0

# P9a (D-393) — sartname §2.2.4: "Parasut acma komutu, otonom sistem
# tarafindan verilebilecegi gibi ... yer istasyonundan manuel tetikleme ile de
# gerceklestirilebilir ... manuel olarak tetiklenmesi durumunda ... ceza puani
# yaptirimi uygulanir." SS7 Cceza tablosu: manuel parasut = -50.
#   aralik   : ACIL komut — IKA_GO'dan daha sik (5 pkt/s); parasut gecikmesi
#              dogrudan yapisal butunluk riskidir (§6.4 kirim = ucus gecersiz).
#   ust sinir: 40 x 0,20 s = 8 s israrli tekrar; ACK yoksa ekran KIRMIZI
#              uyarir ve dugme yeniden acilir (komut kaybi sessiz kalamaz).
PARASUT_TEKRAR_ARALIGI_S = 0.20
PARASUT_TEKRAR_UST_SINIRI = 40
PARASUT_MANUEL_CEZA_PUANI = 50      # SS7 Cceza — ciplak sayi yazilmaz (m.16)

# Faz B (D-403, curutucu ONEMLI-3): IHA komut alicisi YKS'ye ACK'i yalniz
# Pixhawk'in MAVLink COMMAND_ACK(MAV_RESULT_ACCEPTED) cevabindan SONRA doner.
# "command_long_send istisnasiz" tek basina kanit degildir: pymavlink udp:
# sunucusu olu akrana yazip hatayi yutar; router/Pixhawk olmusken de
# "aktarildi" gorunurdu. Tavan: ArduPilot COMMAND_ACK tipik < 100 ms;
# 0,5 s pay. YKS tekrar penceresi (0,20 s x 40 = 8 s) bunu rahat tasir.
MAVLINK_KOMUT_ACK_TAVANI_S = 0.5

# P5 (D-396) — YAYIN HISTEREZISI. Serit secimi surekli buyuklukler uzerinde
# ayrik bir karardir; binde-4 algi gurultusu kararlari kareler arasinda
# cevirebiliyor (68 olcumu: tohuma gore 4-7/260; T92 bant oynakligi 34/260).
# Yayimlanan serit zikzak yaparsa IKA'nin hedefi zikzak yapar. Cozum yayin
# katmanindadir: analiz katmanina DOKUNULMAZ (madde 15), NO_ROUTE ASLA
# geciktirilmez. K=3: tek-kare cevrilmelerin tamami bastirilir; gecikme
# tavani 3 kare (p95 uctan uca 0,113 s -> ~0,34 s ≪ YKS_TESPIT_TAZELIK_S/2).
# Esik degisikligi YENI on kayit ister (results/p5_histerezis/ON_KAYIT.md).
KARAR_HISTEREZIS_KARE = 3


class KararYumusatici:
    """Yayimlanan seridin gurultuyle zikzak yapmasini engeller (D-396).

    ``suz(yol, red) -> bool``: bu karenin karari TELSIZE yazilsin mi?
      - NO_ROUTE/ret ANINDA yayimlanir ve durum sifirlanir (fail-closed
        asla geciktirilmez, asla bastirilmaz).
      - Ilk rota ve NO_ROUTE-sonrasi ilk rota ANINDA yayimlanir.
      - Yayimlanan seritle AYNI serit aninda yayimlanir (tazelik yenilenir).
      - FARKLI serit ancak ``esik`` ARDISIK karede ayni yeni seritle
        gorulurse yayina gecer; o ana dek bu karenin OPEN_ROUTE'u
        gonderilmez (onceki yayin ayakta; IKA rota onbellegi korunur).
      - **H5 tavani:** bastirma ``esik - 1`` ardisik kareye dayaninca bir
        SONRAKI kare ne olursa olsun yayimlanir ve benimsenir — yayin bundan
        fazla bayatlayamaz. (H5 birim testi ilk tasarimda bunu yakaladi:
        yayimlanan 2 iken analiz 1/3 arasinda salinirsa tavansiz surum
        SURESIZ bastiriyordu; tazelik olurdu.)

    Bastirma en fazla ``esik - 1`` ardisik kare surebilir (H5).
    """

    def __init__(self, esik=KARAR_HISTEREZIS_KARE):
        if isinstance(esik, bool) or not isinstance(esik, int) or esik < 1:
            raise ValueError("esik pozitif tamsayi olmali")
        self._esik = esik
        self._yayimlanan = None
        self._aday = None
        self._aday_sayac = 0
        self._bastirilan_ardisik = 0

    def _sifirla_aday(self):
        self._aday = None
        self._aday_sayac = 0

    def suz(self, yol, red) -> bool:
        if yol is None or red is not None:
            # Fail-closed: ret/rotasizlik ANINDA gecer; yayin durumu sifirlanir
            # ki toparlanan ilk rota da ANINDA yayimlansin (erisilebilirlik).
            self._yayimlanan = None
            self._sifirla_aday()
            self._bastirilan_ardisik = 0
            return True
        if self._yayimlanan is None or yol == self._yayimlanan:
            self._yayimlanan = yol
            self._sifirla_aday()
            self._bastirilan_ardisik = 0
            return True
        if yol == self._aday:
            self._aday_sayac += 1
        else:
            self._aday = yol
            self._aday_sayac = 1
        if (self._aday_sayac >= self._esik
                or self._bastirilan_ardisik >= self._esik - 1):
            # Ya K ardisik teyit ya H5 tavani: yayin daha fazla bayatlayamaz.
            self._yayimlanan = yol
            self._sifirla_aday()
            self._bastirilan_ardisik = 0
            return True
        self._bastirilan_ardisik += 1
        return False


# ════════════════════════════════════════════════════════════════════════════
# FAZ B · PIXHAWK ON-UCUS AKIS HIZI ESIKLERI   (scripts/mavlink_dogrula.py)
# ════════════════════════════════════════════════════════════════════════════
# NEDEN: uretim (comms/inis_kaniti.BagilIrtifaOkuyucu ve yerde_mi) iki MAVLink
# akisina bagli: GLOBAL_POSITION_INT (irtifa/konum) ve EXTENDED_SYS_STATE
# (landed_state). ArduPilot EXTENDED_SYS_STATE'i VARSAYILAN akitmaz; istenmesi
# gerekir. Gercek Pixhawk ilk kez baglandiginda "akislar yeterli hizda mi"
# sorusu goz karariyla degil, bu esiklere karsi OLCUMLE cevaplanir. Esikler
# akisin tuketicisinin sozlesmesinden TURETILIR; bagimsiz varsayim degildir.
#
# GLOBAL_POSITION_INT: TELEMETRI_IRTIFA_TAZELIK_S = 0,50 s -> irtifa ornegi
# 0,5 s'den yasliysa OLCEK_YOK (rota fail-closed durur). Pencereyi surekli
# dolu tutmak icin Nyquist 2 Hz; paket kaybi/jitter icin 2x pay -> 4 Hz.
# Altinda irtifa penceresi araliklarla bosa duser, rota kesik kesik OLCEK_YOK.
MAVLINK_KONUM_ASGARI_HZ = 4.0
# EXTENDED_SYS_STATE: yerde_mi 3 ARDISIK (ON_GROUND + dusuk irtifa) cifti
# ister; 1 Hz'de kanit <= 3 s'de olusur. Daha yavasi inis kanitini sartname
# suresi icinde uretemez.
MAVLINK_DURUM_ASGARI_HZ = 1.0
# HEARTBEAT: MAVLink standardi 1 Hz; yari toleransi (baglanti canli mi kapisi).
MAVLINK_HEARTBEAT_ASGARI_HZ = 0.5
# Aracin surekli ARM gercegi COMMAND_ACK'ten degil MAVLink HEARTBEAT'ten gelir.
# En yavas kabul edilen heartbeat periyodu (1 / 0,5 Hz = 2 s) ustune canli
# telemetri jitter payi (0,50 s) eklenir. Daha yasli durum BILINMIYOR sayilir;
# son bilinen ARM degeriyle arayuzu acik tutmak fail-open olur.
ARAC_DURUM_TAZELIK_S = (1.0 / MAVLINK_HEARTBEAT_ASGARI_HZ
                         + TELEMETRI_IRTIFA_TAZELIK_S)
# GUI'nin alan-ozel adi; tek otorite ARAC_DURUM_TAZELIK_S'tir.
ARM_DURUM_TAZELIK_S = ARAC_DURUM_TAZELIK_S
# Olcum penceresi: 10 s'de 1 Hz akis icin sayim hatasi ±1 (%10) — esiklerin
# 2x payinin icinde kalir; daha kisa pencere faz kaynakli yanlis DUSTU uretir.
MAVLINK_DOGRULAMA_SURESI_S = 10.0

# ── T207 (D-406 A, KRITIK) · URETIM AKIS ISTEGI VE SESSIZLIK BEKCISI ────────
# OLGU: ArduCopter EXTENDED_SYS_STATE'i HICBIR `SR*` akisinda vermez
# (Copter-4.5 GCS_Mavlink.cpp STREAM_* dizileri); yalniz
# MAV_CMD_SET_MESSAGE_INTERVAL ile akar. Istek BAGLANTIYA OZELDIR ve Pixhawk
# yeniden basladiginda (pil degisimi) SILINIR. 2026-09-02'ye dek isteyen
# YALNIZ scripts/mavlink_dogrula.py (on-ucus araci) idi; uretim sureci
# comms/iha_inis_yayinci.py istemiyordu -> reboot sonrasi inis kaniti SESSIZCE
# olurdu (EXTENDED gelmez, yerde_mi sure dolunca False, IHA_LANDED asla yok).
#
# Istek yenileme araligi. NEDEN: istek reboot/link kaybinda silinir; periyodik
# yenileme kayip istegi en gec bu sure icinde geri getirir. 10 s: pymavlink
# udp sunucusu akrani HEARTBEAT (1 Hz) ile <= 1 s'de ogrenir, EXTENDED asgari
# 1 Hz -> yenileme sonrasi ilk mesaj <= 1 s; toplam kor sure (sessizlik tavani
# + yenileme) inis kaniti penceresinin (--kanit-timeout) cok altinda kalir.
# Daha sik istek Pixhawk komut kuyrugunu bosuna doldurur.
MAVLINK_AKIS_ISTEK_ARALIGI_S = 10.0
# Sessizlik tavani. NEDEN: EXTENDED_SYS_STATE asgari 1 Hz
# (MAVLINK_DURUM_ASGARI_HZ); 5 s sessizlik = 5 ardisik kayip mesaj = akis YOK
# (jitter ya da tek paket kaybi degil). Asilirsa KIRMIZI log + aninda yeniden
# istek (fail-visible); durum degisince loglanir, her turda degil.
MAVLINK_AKIS_SESSIZLIK_TAVANI_S = 5.0
# Istenen hiz = asgari x carpan; aralik_us = 1e6 / (asgari_hz x carpan).
# NEDEN: asgarinin tam kendisini istemek jitter'da esigin hemen altina
# dusurur; 2x pay. scripts/mavlink_dogrula.ISTEK_HIZ_CARPANI (2.0) ile AYNI
# DEGER — T207'de o araca dokunulmadi; oradaki sabitin buraya BAGLANMASI
# onerilir (tests/test_faz_b_akis_istegi.py esitligi kilitler).
MAVLINK_AKIS_ISTEK_HIZ_CARPANI = 2


# ════════════════════════════════════════════════════════════════════════════
# T235-B · ALAN-OLCEKLI YOL ETIKETI (A0) + KBH IZDUSUMU (A1) + HIZ KAPISI
#          (D-451 · results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md SS1, SS5)
# ════════════════════════════════════════════════════════════════════════════
# NEDEN: yayinlanan `road` (`rota_serit_karari`) rotanin KARENIN hangi ucte
# birinde oldugundan okunur. Kare alana ortali degilse ya da kare alandan
# genisse etiket DUNYA yoluyla eslesmez (OLCULDU, SENTETIK: kerteriz 3/8,
# kosum_tur3 6/20 — H1/README_T214A.md SS2, H1/t235/analiz/analiz_c.md SS1).
# FDA'da (sartname :726-745, 20x20 m) HQ 6 mm ile 32 m'de kare 33,5 m
# genisliktedir; yol araligi 5,59 m'nin altindaysa kare-goreli ucte-birler uc
# yola da "2" verir (HESAP, H1/t235/analiz/fda_etiket_hesap.py).
#
# 🔴 BU BOLUM YALNIZ SAF FONKSIYON TASIR, URETIME BAGLI DEGILDIR:
# `rpi_inference` bunlari CAGIRMAZ -> yayin davranisi bayt-es. Uretime
# baglanmak T235-C'nin isidir ve ON_KAYIT SS2 karar kuralina baglidir
# (A0 ancak tezgah kapisini gecerse, bayrakla; A1 yalniz tezgah/karsilastirma).
#
# Cerceve (TASARIM_TASLAK SS3, "KBH"): orijin alan merkezi (FDA; ana gorevde
# KB), +y = Baslangic -> Hedef yatay dogrultusu (kerteriz, pusula, saat yonu),
# +x = Hedef'e bakan gozlemcinin SAGI. Etiket: x < -W/6 -> 1 · |x| <= W/6 -> 2
# · x > W/6 -> 3. "Sol/orta/sag, Baslangic'tan Hedef'e bakan gozlemciye gore"
# sartnamenin tanimi DEGIL, proje sozlesmesidir.

# Alan genislikleri — sartname beyanidir, olcum degil. `SENARYO_BOYUTLARI_M`
# ile AYNI degerlerdir; esitlik tests/test_t235_alan_etiketi.py ile kilitlidir
# (biri degisip digeri kalamaz).
FDA_ALAN_GENISLIK_M = 20.0     # sartname :726-745 FDA alani 20x20 m · ON_KAYIT SS1
HTAB_ALAN_GENISLIK_M = 50.0    # sartname HTAB 50x50 m · simulation/scripts/arena.py HTAB

# HIZ KAPISI (ON_KAYIT SS5 · CURUTUCU_HUKMU bulgu 5): alan-goreli etiket
# yalniz yer hizi <= 1,0 m/s iken kullanilir. NEDEN: kare zaman damgasi YOK
# (protocol.py yayin anini yazar); kose bacaklarinda 3 m/s (WPNAV_SPEED
# 300 cm/s) x kare basina 770-922 ms = 2,3-2,8 m kayma (HESAP) FDA'nin
# 3,33 m'lik payini yer. Beklemede (hiz ~ 0) bu terim kaybolur.
ALAN_ETIKETI_HIZ_ESIGI_M_S = 1.0
# Tazelik (ON_KAYIT SS5): hiz ornegi karar anindaki telemetri anlik
# goruntusunden en fazla bu kadar eski olabilir. `TELEMETRI_IRTIFA_TAZELIK_S`
# (0,50 s) ile ayni ailedendir ama ON KAYITLI esiktir: o sabit degisse bile
# bu DEGISMEZ (esik gevsetilmez); deger testle kilitlidir.
ALAN_ETIKETI_TAZELIK_S = 0.5


def _t235_sayi(x):
    """Sonlu gercek sayi -> float; bool/None/NaN/sonsuz/metin -> ``None``."""
    if isinstance(x, bool) or not isinstance(x, Real):
        return None
    d = float(x)
    return d if math.isfinite(d) else None


def alan_serit_yari_genisligi_m(alan_genislik_m):
    """ORTA seridin YARI genisligi = W/6 (m); gecersiz W -> ``None``.

    W alan uc esit serite bolunur (SERIT_SAYISI); orta serit merkezden
    ±W/(2*SERIT_SAYISI) = ±W/6'dir. A0 ve A1 AYNI siniri buradan okur.
    """
    w = _t235_sayi(alan_genislik_m)
    if w is None or w <= 0.0:
        return None
    return w / (2.0 * SERIT_SAYISI)


def _t235_x_dizisi(rota_pikselleri):
    """Rota pikselleri -> (n, >=2) float dizi; bos, sayisal olmayan, duzensiz
    ya da sonlu olmayan girdi -> ``None`` (FAIL-CLOSED: istisna FIRLATMAZ)."""
    import numpy as _np
    try:
        if not isinstance(rota_pikselleri, _np.ndarray):
            rota_pikselleri = list(rota_pikselleri)
        n = len(rota_pikselleri)
        if n == 0:
            return None
        dizi = _np.asarray(rota_pikselleri, dtype=float).reshape(n, -1)
    except (TypeError, ValueError):
        return None
    if dizi.shape[1] < 2 or not _np.all(_np.isfinite(dizi[:, :2])):
        return None
    return dizi


def _t235_cogunluk(seritler):
    """1..3 serit dizisi -> ``(karar, sayim)``; `rota_serit_karari` KURALI:
    en cok piksel tasiyan serit, beraberlikte KUCUK serit indisi."""
    import numpy as _np
    sayim = tuple(int(v) for v in _np.bincount(
        _np.asarray(seritler, dtype=_np.int64) - 1, minlength=3)[:3])
    mevcut = [i for i in range(3) if sayim[i] > 0]
    if not mevcut:
        return None, sayim
    return int(max(mevcut, key=lambda i: (sayim[i], -i)) + 1), sayim


def alan_serit_karari(rota_pikselleri, icerik_x0, icerik_w, mpp,
                      alan_genislik_m=FDA_ALAN_GENISLIK_M):
    """A0 — ALAN-OLCEKLI, MERKEZ REFERANSLI yol etiketi (T235 · ON_KAYIT SS1).

    Sinirlar icerik kutusunun MERKEZINDEN ±(W/6)/mpp pikseldir
    (W = alan genisligi, m; mpp = kare olcegi, `mpp_irtifadan`):
        x < merkez - b -> 1 (sol) · x <= merkez + b -> 2 (orta) · aksi 3 (sag)
    Orta serit KAPALI araliktir: `kbh_serit_karari` (|x| <= W/6 -> 2) ile
    ayni ve piksel basina serit atamasi merkeze gore x-aynasi SIMETRIKTIR
    (tam sinirdaki piksel iki yanda da 2). Karar `rota_serit_karari` ile AYNI
    kuraldir: rota GOVDESI piksel cogunlugu, beraberlikte KUCUK serit (bu
    beraberlik kurali tanim geregi ayna-simetrik degildir). x float kiyaslanir.

    Varsayim (ON_KAYIT SS1, T235-E): IHA alan MERKEZINDE bekler ve goruntunun
    yukarisi Baslangic -> Hedef'tir. Poz, hdg, enlem/boylam GEREKMEZ.
    Varsayim tutmuyorsa (IHA hareket halinde) cagiran
    `alan_etiketi_kullanilabilir_mi` ile KARE'ye duser.

    Doner ``(karar, sayim, pay)``:
      karar : 1|2|3; rota bos ya da olcek/icerik/W gecersiz -> ``None``
              (``None`` = alan etiketi URETILEMEZ; cagiran KARE'ye duser)
      sayim : serit basina piksel (n1, n2, n3)
      pay   : ``None`` ya da sozluk —
              sol_sinir_px, sag_sinir_px : iki serit sinirinin x'i
              medyan_x_px : rota piksellerinin x medyani
              pay_m : medyanin SECILEN seridin en yakin sinirina uzakligi (m);
                      pozitif = serit ICINDE, negatif = medyan baska seritte
    """
    import numpy as _np
    bos = (None, (0, 0, 0), None)
    x0 = _t235_sayi(icerik_x0)
    w = _t235_sayi(icerik_w)
    if x0 is None or w is None or w <= 0.0 or not olcek_gecerli_mi(mpp):
        return bos
    yari_m = alan_serit_yari_genisligi_m(alan_genislik_m)
    if yari_m is None:
        return bos
    dizi = _t235_x_dizisi(rota_pikselleri)
    if dizi is None:
        return bos
    m = float(mpp)
    merkez = x0 + w / 2.0
    b = yari_m / m
    sol, sag = merkez - b, merkez + b
    xs = dizi[:, 0]
    karar, sayim = _t235_cogunluk(
        _np.where(xs < sol, 1, _np.where(xs <= sag, 2, 3)))
    medyan = float(_np.median(xs))
    if karar == 1:
        pay_px = sol - medyan
    elif karar == 2:
        pay_px = min(medyan - sol, sag - medyan)
    else:
        pay_px = medyan - sag
    return karar, sayim, {"sol_sinir_px": sol, "sag_sinir_px": sag,
                          "medyan_x_px": medyan, "pay_m": pay_px * m}


def kbh_donustur(px, py, *, merkez_px, mpp, iha_dogu_m, iha_kuzey_m,
                 hdg_derece, montaj_yaw_derece, kerteriz_derece):
    """A1 — kare pikseli -> KBH (alan) cercevesi, metre (T235 · ON_KAYIT SS1).

    ⚠ YALNIZ TEZGAH/KARSILASTIRMA; URETIME BAGLANMAZ (T235-C, ON_KAYIT SS2).
    Nadir, egimsiz, duz zemin varsayimi (ATTITUDE yok; egim tezgahta ayri
    hata terimidir). Adimlar:
      1. goruntu-yukari kerterizi  t = hdg + montaj_yaw  (pusula, saat yonu)
      2. piksel ofseti  sag = (px - cx) * mpp ; ileri = (cy - py) * mpp
      3. ENU ofseti  dogu = sag*cos t + ileri*sin t ; kuzey = -sag*sin t + ileri*cos t
      4. ENU nokta = IHA (dogu, kuzey) + ofset — IHA konumu alan ORIJININE
         gore metre (`yerel_konum_m(orijin_enlem, orijin_boylam, enlem, boylam)`)
      5. KBH  x = dogu*cos k - kuzey*sin k ; y = dogu*sin k + kuzey*cos k
         (k = kerteriz: Baslangic -> Hedef dogrultusunun pusula acisi)
    `montaj_yaw_derece`: goruntu-yukarisinin BURNA gore saat yonu acisi
    (goruntu-yukari = burun ise 0). `merkez_px`: icerik kutusu merkezi (cx, cy).
    `px`, `py` skaler ya da dizi olabilir (NumPy yayilimi): skalerde
    ``(x, y)`` float ikilisi, dizide iki dizi doner.
    FAIL-CLOSED: gecersiz olcek/aci/konum/merkez -> ``None``.
    """
    import numpy as _np
    if not olcek_gecerli_mi(mpp):
        return None
    try:
        cx, cy = merkez_px
    except (TypeError, ValueError):
        return None
    degerler = [_t235_sayi(v) for v in (cx, cy, iha_dogu_m, iha_kuzey_m,
                                         hdg_derece, montaj_yaw_derece,
                                         kerteriz_derece)]
    if None in degerler:
        return None
    cx, cy, e0, n0, hdg, montaj, kerteriz = degerler
    m = float(mpp)
    skaler = _np.ndim(px) == 0 and _np.ndim(py) == 0
    sag = (_np.asarray(px, dtype=float) - cx) * m
    ileri = (cy - _np.asarray(py, dtype=float)) * m
    t = math.radians(hdg + montaj)
    dogu = e0 + sag * math.cos(t) + ileri * math.sin(t)
    kuzey = n0 - sag * math.sin(t) + ileri * math.cos(t)
    k = math.radians(kerteriz)
    x = dogu * math.cos(k) - kuzey * math.sin(k)
    y = dogu * math.sin(k) + kuzey * math.cos(k)
    if skaler:
        return float(x), float(y)
    return x, y


def kbh_serit_karari(rota_pikselleri, *, merkez_px, mpp, iha_dogu_m,
                     iha_kuzey_m, hdg_derece, montaj_yaw_derece,
                     kerteriz_derece, alan_genislik_m=FDA_ALAN_GENISLIK_M):
    """A1 — rota piksellerinin KBH x'inden yol etiketi (T235 · ON_KAYIT SS1).

    ⚠ YALNIZ TEZGAH/KARSILASTIRMA; URETIME BAGLANMAZ (ON_KAYIT SS1: ancak
    SS2 karar kurali + T235-C poz kolu). Her piksel `kbh_donustur` ile KBH'ye
    izdusurulur; x < -W/6 -> 1 · |x| <= W/6 -> 2 · x > W/6 -> 3; cogunluk,
    beraberlikte KUCUK serit (`rota_serit_karari` kurali).
    Doner ``(karar, sayim)``; rota bos ya da olcek/poz/W gecersiz ->
    ``(None, (0, 0, 0))``.
    """
    import numpy as _np
    bos = (None, (0, 0, 0))
    yari = alan_serit_yari_genisligi_m(alan_genislik_m)
    if yari is None:
        return bos
    dizi = _t235_x_dizisi(rota_pikselleri)
    if dizi is None:
        return bos
    sonuc = kbh_donustur(dizi[:, 0], dizi[:, 1], merkez_px=merkez_px, mpp=mpp,
                         iha_dogu_m=iha_dogu_m, iha_kuzey_m=iha_kuzey_m,
                         hdg_derece=hdg_derece,
                         montaj_yaw_derece=montaj_yaw_derece,
                         kerteriz_derece=kerteriz_derece)
    if sonuc is None:
        return bos
    x = _np.asarray(sonuc[0], dtype=float)
    if not _np.all(_np.isfinite(x)):
        return bos
    return _t235_cogunluk(_np.where(x < -yari, 1, _np.where(x <= yari, 2, 3)))


def alan_etiketi_kullanilabilir_mi(hiz_m_s, tazelik_s):
    """HIZ KAPISI (ON_KAYIT SS5): alan-goreli etiket (A0/A1) bu karede
    kullanilabilir mi?

    ``True`` YALNIZ: yer hizi <= ALAN_ETIKETI_HIZ_ESIGI_M_S VE hiz orneginin
    yasi <= ALAN_ETIKETI_TAZELIK_S (karar anindaki telemetri anlik
    goruntusu). Aksi halde cagiran KARE etiketini yayinlar ve
    `road_cerceve = "KARE"` yazar (T235-C). FAIL-CLOSED: None/bool/NaN/
    sonsuz/negatif hiz ya da yas -> ``False`` (bilinmeyen hiz "beklemede"
    SAYILMAZ).
    """
    v = _t235_sayi(hiz_m_s)
    yas = _t235_sayi(tazelik_s)
    if v is None or yas is None or v < 0.0 or yas < 0.0:
        return False
    return v <= ALAN_ETIKETI_HIZ_ESIGI_M_S and yas <= ALAN_ETIKETI_TAZELIK_S


# ── KAMERA BEKLE + YENIDEN AC (2026-09-19, Jetson olcumu) ────────────────────
# T143 kamera sozlesmesinin (KAMERA_DUSEN_KARE_* / KAMERA_BITIS_*, yukarida)
# devamidir. ⚠ Dosya SONUNDADIR, bilerek: FDR/atolye belgeleri bu dosyaya
# `karar_sozlesmesi.py:<satir>` ile atif yapar (tests/test_fdr_sarkan_atif_kapisi,
# test_atolye_test_gunu); ortaya eklenen her satir o atiflari kaydirir.
# NEDEN: ekransiz servis kipinde kamera acilamayinca (CSI kamera yok -> kopru
# /video 503) ya da hat koptugunda (30 ardisik dusen kare) `run_camera` donuyor,
# surec CIKIYOR, systemd 2-60 s sonra yeniden kaldiriyordu (sayac 32'yi buldu).
# Her yeniden baslatma YOLO'yu ~4,5 s CPU ile yeniden yukluyor ve telsiz
# halkasini (1 Hz HEARTBEAT) yikiyordu: YKS ucagin kalp atisini dakikada yalniz
# birkac saniye goruyor, hub her yeni UDP tuketicisini sayip "ogrenilen tavani
# (32) asildi" diyordu. Servis kipinde surec artik CIKMAZ: bekler, yeniden acar.
# ⚠ T143'un "kamerasiz sonsuz bekleme YOK" kurali KARAR icindir ve BOZULMAZ:
# beklerken kare yoktur, karar URETILMEZ/YAYINLANMAZ; HEARTBEAT `karar_yas`
# buyur ve YKS bayatligi GORUR (fail-visible). Karar yolu bayt-es aynidir.
#  * GERI CEKILME: 1 -> 2 -> 5 s, son deger TAVANDIR. CSI yeniden oturtulup
#    Jetson yeniden baslatilana dek kamera donmez; 5 s tavan acma denemesini
#    seyrek tutar, kamera dondugunde de en gec ~5 s'de yakalanir.
#  * TANI ARALIGI: [KAMERA_BEKLIYOR] satiri kesintinin ILK aninda ve sonra en
#    fazla 30 s'de bir basilir — journal'i doldurmadan "hala bekliyor"u gosterir.
#  * SINYAL YOKLAMA: beklemeler 0,5 s dilimlerle yapilir; SIGTERM en gec bir
#    dilim gecikir (systemd TimeoutStopSec=5'in cok altinda).
#  * /durum ZAMAN ASIMI: kopru tanisi (yalniz log; karar DEGIL) 1 s'den uzun
#    bekletemez — tani, durdurma cevabini geciktirmemeli.
KAMERA_YENIDEN_ACMA_BEKLEMELERI_S = (1.0, 2.0, 5.0)  # sirayla; son deger tavan
KAMERA_TANI_ARALIGI_S = 30.0          # [KAMERA_BEKLIYOR] tekrar araligi (s)
KAMERA_SINYAL_YOKLAMA_S = 0.5         # bekleme dilimi = azami SIGTERM gecikmesi (s)
KAMERA_DURUM_ZAMAN_ASIMI_S = 1.0      # kopru /durum GET zaman asimi (s)
# Kamera koprusunun (scripts/kamera_koprusu.py `DURUM_YOLU`) durum ucu. Kopru
# ayri Python'da kosar (import edilmez); esitlik tests/test_kamera_bekleme.py'de.
KAMERA_KOPRU_DURUM_YOLU = "/durum"


# ── HEARTBEAT TELEMETRI GECERLILIK KAPISI (2026-09-19, YKI kanit gunlugu) ────
# ⚠ Dosya SONUNDADIR, bilerek (yukaridaki KAMERA blogu ile ayni gerekce:
# `karar_sozlesmesi.py:<satir>` atiflari kaymasin).
# NEDEN: 19 Eyl telsiz uzerinden YKI kaniti — Pixhawk yeniden baslatildiktan
# hemen sonra (GPS fix YOK) HEARTBEAT lat/lon ~ 0/0 tasidi ve YKI ucagi
# ~4.500 km uzaga koydu (19:42:11); reboot sonrasi `alt` 890,6 m geldi,
# saniyeler sonra -3,8 m (19:21:48). YKI bu `alt` ile SS5.3.2 "asgari 30 m
# saglaniyor" gostergesini kurar: sahte irtifa SAHTE UYUM gosterir. Protokol
# kurali: bilinmeyen alan YAZILMAZ, asla "0,0". Kapi YALNIZ heartbeat
# yayinindadir (`rpi_inference._heartbeat_telemetri_kapisi`); inis kaniti
# (`comms/inis_kaniti.py`) ve olcek yolu (`mpp_irtifadan` + IRTIFA_MAKUL_UST_M,
# yukarida) DEGISMEZ — olcek yolu 890 m'yi ve <=0'i zaten reddediyor.
#  * FIX: MAVLink GPS_FIX_TYPE_3D_FIX = 3. `gps_fix` VARSA ve 3'ten kucukse
#    (ya da tamsayi degilse) lat/lon ve turetilen IHA-UB x/y YAZILMAZ.
#    `gps_fix` YOKSA (bilinmiyor) konum yalniz sayi/aralik/0-0 kurallariyla
#    gecer. NEDEN: 19 Eyl prova3/4/5 ve yki_uctan_uca hakem gunluklerinde
#    lat VAR ama gps_fix HIC yok (GPS_RAW_INT Jetson okuyucusunda taze degil);
#    "fix yoksa konum yok" kurali YKI'de ucagin konumunu tamamen silerdi.
#    Gozlenen kotu durum (reboot) 0/0'dir ve SIFIR KONUM kurali onu yakalar.
#  * SIFIR KONUM: |lat| ve |lon| ikisi de 1e-6 dereceden (~0,1 m) kucukse
#    fix ne olursa olsun bu bir konum degil "henuz konum yok" isaretidir.
#  * IRTIFA BANDI (bagil, home'a gore; kapali aralik): alt -50 m, yerde
#    olculen baro kaymasini (19 Eyl hakem gunlukleri: -2,9 .. -4,5 m) rahat
#    kapsar; UST sinir olcek yolunun IRTIFA_MAKUL_UST_M'sidir (200 m) — YKI
#    gostergesi ile olcek yolu ayni irtifayi "telemetri hatasi" sayar;
#    890,6 m boot sicramasi disarida kalir.
#  * HIZ TAVANI 40 m/s (144 km/h, dahil): FDA multirotoru fiziksel olarak
#    asamaz. ⚠ BILINEN SINIR: elde tasirken gorulen 10-13 m/s (pusula gecisinde
#    EKF hiz copu) bu bandin ICINDEDIR; bu kapi onu AYIKLAYAMAZ.
#  * GUNLUK: bastirilan alanlar sayilir; neden en fazla 30 s'de bir satirla
#    basilir (journal'i 1 Hz satirla doldurmamak icin).
TELEMETRI_GPS_ASGARI_FIX = 3                  # GPS_FIX_TYPE_3D_FIX
TELEMETRI_SIFIR_KONUM_ESIGI_DERECE = 1e-6     # |lat|,|lon| ikisi de altinda -> 0/0
TELEMETRI_IRTIFA_ALT_SINIRI_M = -50.0         # bagil irtifa alt siniri (m), dahil;
                                              # ust sinir: IRTIFA_MAKUL_UST_M (dahil)
TELEMETRI_HIZ_TAVANI_MS = 40.0                # yer hizi tavani (m/s), dahil
TELEMETRI_BASTIRMA_LOG_ARALIGI_S = 30.0       # [TELEMETRI] satiri en sik bu aralikla
