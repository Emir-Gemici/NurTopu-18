# T127 ON KAYIT — TEMIZ BOLUM egitimi BASLAMADAN once yazildi (D-107)
# Yazan: Claude 2 / Opus 5 (basamele) · 2026-08-21 · dayanak: mimar T127 emri, D-233

## AMAC (mimarin cumlesi, aynen)
"Bu bir BASARI turu degil, DURUSTLUK turudur. Amac t127'yi kazandirmak degil,
t122ac'nin sayilarinin KIRLI BOLUMDEN gelip gelmedigini OGRENMEK."

## BOLUM — SONUC DEGIL GIRDI, bu yuzden burada YAZILI
`bolum_sec` anahtari D-233'te kaynak duzeyine indirildi (`cesit` cikarildi).
Ayni tohum (20260802) ve val_oran 0,15 ile yeniden bolundu:
    ESKI : train 385 · val 55  · kaynagi egitimde de olan val 55/55 (%100 KIRLI)
    YENI : train 352 · val 96  · kaynagi egitimde de olan val 0/96  (TEMIZ)
    val kaynak 12 · train kaynak 44 · kesisim 0
Goruntuler YENIDEN URETILMEDI; yalniz hangi varyantin hangi bolume gittigi
degisti (mimarin sarti).

## 🔴 KUME KUCULMESI KARISIKLIGI — MIMARIN SORDUGU AYRIM
Temiz bolumde copy_paste bileseni 385 -> 352 egitim goruntusu (-33, %-8,6).
AMA karisim UC bilesenlidir: rescuenet_2sinif_engelli (3502) + sentetik_arena
(2700) + copy_paste (352). TOPLAM egitim kumesi 6587 -> 6554, yani **%-0,5**.
AYRIM SU SEKILDE YAPILIR (simdiden yazili):
  · Dusus %-0,5'lik kume kucuklugune bagliysa etkisi TUM olcutlerde kucuk ve
    YONSUZ olmali (gurultu mertebesinde).
  · Cati kacagi gibi copy_paste'e OZGU derslerde buyuk dusus olursa bu kume
    kucuklugunden DEGIL, o dersin kaynak CESITLILIGINDEN gelir: temiz bolumde
    12 kaynak kare (ve catilari) egitimden TAMAMEN cikti. Bu ikinci etki
    GERCEK ve raporlanacak — "kume kucuklugu" diye gecistirilmeyecek.
  · Bu iki etki n=1 kosumla TAM ayrilamaz. Ayrilamayan kisim "AYRILAMAZ"
    diye yazilacak (mimar bunu acikca kabul etti).

## KIYAS EKSENI (mimarin kisiti)
val mAP KIYASLANAMAZ (val kumesi degisti) — yazilmayacak; yazilirsa
"KIYASLANAMAZ" damgasiyla yazilacak. Kiyas KABUL ZINCIRI (65) ve gercek-kare
olcumleri uzerinden yapilir; `sentetik_arena_kadraj_t66` bolumden BAGIMSIZDIR.

## KARAR KURALLARI — SONUC GORULMEDEN
Taban: t122ac'nin BUGUNKU olculmus degerleri.
    K0 figur %1,55 (oran 3,17) · K1 257/260 · K2 16/257 · K3 1/257 · K4 0/257
    K5 GECTI 0/172 · cati kacagi 0,0201 · kaplama ICERIK 0,455 · 67'de red 0
    bakir 11 karede cati kacagi 0,0107 · kaplama 0,4196

1. "TEMIZ BOLUM KAZANANI GECERLI KILDI" sayilir <=>
   · K0..K5 kapilarinin HEPSI yine GECTI, VE
   · cati kacagi <= 0,10 (taban 0,020'nin bes kati; kume kucuklugune pay),
   · K1 >= 230 (ESIK sozlugu, degismez), K2/K3/K4 tavan altinda,
   · 67 gercek karede red <= 5.
2. "KAZANAN TEMIZ BOLUMDE COKTU" sayilir <=>
   · herhangi bir kapi DUSTU, VEYA
   · cati kacagi > 0,30 (yani (c)'nin bugunku 0,131'inden belirgin kotu),
   · VEYA 67 karede red >= 34 (yarisi).
3. Ikisi arasinda kalan her sonuc "KISMEN" diye yazilir ve sayilar oldugu gibi
   raporlanir. GEVSETME YOK: bantlar burada kilitlendi.
4. Bu kosum bir TERFI ONERISI DEGILDIR (D-133 · SS9.2).

## KOSUM
Recete t122ac ile BIREBIR AYNI (56 zinciri RECETE, taban v34, epochs 40,
patience 15, imgsz 512, seed 0). Degisen TEK sey: `karisim_t127.yaml`
(copy_paste_t127 = ayni goruntuler, TEMIZ bolum). Ad: `t127_temiz`.
Zincir TEK betikle kosar (`116_t127_temiz_bolum_zinciri.py`): kume kur ->
egit -> kabul zinciri (65) -> kiyas (109) -> gercek kare reddi -> JSON.

## SIMDIDEN BILINEN SINIRLAR
· n=1 tohum (D-135). Tohum gurultusu olcumu (T128) bu is icin DURDURULDU;
  yeniden kuyruga alinacak.
· Kume yine ALAN-ICI (D-242 §3); temiz bolum bunu COZMEZ, yalniz "val
  kirliligi sayilari sisirdi mi" sorusunu kapatir.
· Bakir 11 kare (T127/D-246) bu egitimde de kullanilMADI — bagimsiz kalmaya
  devam ediyor ve sonrasinda AYNI sekilde olculecek.
