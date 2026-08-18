# T95-B — `rota_bul` ACIKLIK KORUMASI, BUTCE BICIMINDE · ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-18 · OLCUM KOSULMADAN once yazildi (D-107)
# Dayanak: D-159 (amele olcumu) · D-160 (denetim) · D-161 (kendi gerekcemin curumesi)

## NEDEN IKINCI TUR

T95 birinci turda (4) "duzelt suresi <= 2 kat taban" olcutunden dustu
(3,07 kat). O olcutu ayakta tutarken kullandigim gerekce — "KATMAN B'nin
gercek girdisi ortomozaiktir, dugum sayisi cok daha buyuktur" — OLCULMEDEN
yazilmisti ve D-161'de CURUDU:

    girdi                    px    mpp     saha     ds   plan izgarasi
    kadraj (t66, olculen)   640  0,0781   50,0 m    6      106 x 106
    mozaik (URETIM)        1024  0,0547   56,0 m    8      128 x 128

Uretim girdisi test kumesinden %21 buyuk; kat kat DEGIL. Dolayisiyla (4)
YANLIS SEVIYEDE uygulanmis bir kisittir: bir BUTCEYI korumak icin yazildi ama
bir ALT BILESENIN ORANINI olcuyor. Toplamin kucuk bir yuzdesi olan alt bilesen
butceye dokunmadan uce katlanabilir.

⚠ BU BIR GEVSETME DEGILDIR. Yeni olcut SONUCU BILMEDEN yaziliyor ve iki yone
de dusebilir — asagidaki ayirt edici olguya bakiniz.

## OLCULECEKLER (birinci turdaki sozlesme AYNEN gecerli)

Kume `sentetik_arena_kadraj_t66` (n=260), TEMIZ kare, model kare basina TEK
kosum, taban ve koruma AYNI kosumda, ayni `mk`. Aciklik probu KAPALI
(`--yalniz-sure` kipi) — prob `sure_ms` penceresini KIRLETIR (D-159 §4).

  1. `rota_bul` TOPLAM suresi (cagri etrafinda duvar saati) — taban vs koruma
  2. `sure_ms` DOKUMU: costmap · koridor · astar · duzelt — taban vs koruma
  3. `_polyline_asgari_aciklik` CAGRI SAYISI kare basina — n=91'de maliyetin
     1,03-7,82 ms arasi oynamasi REDDETMELERDEN mi geliyor?
  4. `yol_duzelt`e giren dugum sayisi (girdi n) — dagilim, yalniz medyan degil

## KABUL — (4') YERINE GECIYOR, DIGERLERI AYNEN KALIYOR

    olcut                                      esik
    (4') rota_bul TOPLAM sure medyani          KORUMA <= 40 ms
         VE artis                              <= tabanin %20'si
    (1) rota_bul ACIK                          >= ayni kosumdaki TABAN
    (2) kayip medyani kazanci                  >= 1,00 px      [1. turda TUTTU]
    (3) pay < 3 px olan ACIK kare              <= TABAN        [1. turda TUTTU]
    (5') waypoint medyani                      <= taban + 2    [D-160'ta turetildi]
    (6) codes/test_rota_sentetik.py            15/15
    (7) unittest discover -s tests             >= 584 OK, HIC dusme yok

⚠ 40 ms nereden: `codes/costmap_path_finder.py:25` KATMAN B'yi *"mozaikte veya
~2 Hz'de, ~30-40 ms"* diye tanimlar. Ust uc alindi. Bu MODULUN KENDI YAZILI
SOZLESMESIDIR, benim uydurdugum bir sayi degildir.

⚠ %20 nereden: koruma bir EMNIYET PAYI iyilestirmesidir, yetenek eklemez.
Planlayici zamaninin bestebirinden fazlasini yiyorsa bedeli ayrica
tartisilmalidir (daha ucuz bicim aranir).

## 🔴 AYIRT EDICI OLGU (olcut rigged DEGILDIR)

Birinci turda olculen mutlak artis **+1,88 ms**. Toplam sure BILINMIYOR:

    toplam taban ~5 ms  -> +1,88 ms = %38  -> (4') DUSER, T95 YINE REDDEDILIR
    toplam taban ~30 ms -> +1,88 ms = %6   -> (4') TUTAR

Hangisi oldugunu bilmiyorum. Sayiyi gorunce olcut DEGISTIRILMEYECEK.

## RED KURALI

- Biri bile tutmazsa degisiklik URETIME YAZILMAZ, gorev `[ ]` kalir.
- (4') duserse: KABUL EDILEBILIR: "daha ucuz bicim" arastirmasi acilir
  (or. onek gecisinin yalniz REDDEDILEN kirislerde kosturulmasi). Kural
  DEGISTIRILMEDEN once yine ON KAYIT yazilir.
- Olcut sonuca gore GEVSETILMEZ. D-161'in kurali baglayicidir: bir olcutu
  ayakta tutan ya da dusuren GEREKCE bir OLGU iddiasi iceriyorsa, o olgu da
  EN AZ olcut kadar dogrulanmis olmalidir.
