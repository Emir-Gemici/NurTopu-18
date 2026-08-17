# v33 (GURULTU DAYANIKLILIGI) — ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-17 · SONUC GORULMEDEN yazildi (D-107 disiplini)
# Bu dosya egitim BASLAMADAN once yazilmistir. Kural sonuca gore DEGISTIRILMEZ.

## HIPOTEZ (iddia DEGIL, sinanacak)

T79'un kalan mekanizmasi: DEGISMEYEN bir koridor kumesi uzerinde kuresel A*'in
maliyet BERABERLIGI (D-145). Maliyet `dt_px`ten, o da MASKEDEN gelir. Maske
gurultuye karsi ne kadar degismezse, beraberligi ceviren tedirginlik o kadar
kucuk kalir.

D-142 "kararsizlik VERI tarafindan cozulemez" dedi; ama o olcum DOZ ekseninde
(gercek kare cogaltmasi 0x/2x/4x) yapildi. GURULTU DAYANIKLILIGI AYRI EKSENDIR
ve HIC denenmedi — v30 recetesinde HSV/dondurme/olcek/erasing var, PIKSEL
GURULTUSU YOK.

## TEK DEGISKEN

v33 = v30 recetesi (`56_t53_gercek_karisim.py`, v30 args.yaml ile dogrulandi)
+ egitim orneklerinin YARISINA Gauss piksel gurultusu (sigma ~ U(0, 6)/255).
Val'e gurultu VERILMEZ. Baska hicbir sey degismez.

## KABUL KURALI — SONUC GORULMEDEN

### BIRINCIL OLCUT (hipotezin kendisi)
`68_karar_kararliligi.py` (sigma=2/255, tekrar=3, tohum=7, n=260):

    A <= 4/260   -> HIPOTEZ DOGRULANDI. T79'un hedefi tutturuldu.
    4 < A < 8    -> KISMI. Hipotez yonu dogru ama hedef tutmadi. TERFI YOK.
    A == 8       -> ETKISIZ. Gurultu augmentasyonu kararliligi DEGISTIRMEDI.
    A > 8        -> HIPOTEZ CURUDU. Gurultu augmentasyonu KOTULESTIRDI.

⚠ v30 tabani A = 8/260'tir ve iki bagimsiz kosuda tekrarlandi (D-142, D-145).

### GERI ALINAMAZ SART — KABUL DENETIMI (65_kabul_denetcisi.py)
Bunlar projenin YURURLUKTEKI kapilaridir (D-132), gevsetilmez:

    K0  korluk yok
    K1  rota >= 230/260
    K2  moloza basma <= %15
    K3  agir basma   <= %3
    K4  alan disi    <= %5
    K5  bariyer kesisimi 0

### TERFI KURALI (uretim modelinin degismesi)
v33 uretime ANCAK su UCU BIRDEN saglanirsa alinir:
  1. A <= 4/260
  2. K0..K5 kapilarinin HEPSI gecer
  3. K1 >= 250/260  (v30 = 258/260; buyuk bir yetenek kaybiyla kararlilik
     satin alinmaz)

Ucunden biri bile tutmazsa v33 TERFI ETMEZ; sonuc yine de kayda gecer.
"Neredeyse tuttu" diye terfi ettirilmez.

## ONCEDEN YAZILAN UYARILAR

1. Gurultu augmentasyonu maskeyi YUMUSATABILIR: model kenarlarda daha
   temkinli olup serbest alani KUCULTEBILIR. Bu K1'i dusurur. Olculecek.
2. sigma araligi (0,6) egitimde, kapi ise sigma=2'de olcer. Kapi araligin
   ICINDEDIR — yani bu bir "test setine uydurma" degildir ama araligin
   tamamina genelleme de IDDIA EDILMEZ.
3. Bu TEK kosudur. D-135 tek-kosu uyarisi gecerlidir; ancak D-140 `seed`in
   Ultralytics'te HIC etkisi olmadigini olctu, yani ayni recete ayni sonucu
   verir — tekrar bir sey eklemez.
4. Gurultu her epoch YENIDEN uretilir (cache=disk temiz goruntu tutar), yani
   model ayni gurultu ornegini ezberleyemez.
5. A'nin dusmesi T79'u KAPATMAZ: T79 kod tarafinda (A* maliyet beraberligi)
   bir duzeltme olarak durur. Bu egitim yalnizca VERI tarafinin kalan tek
   eksenini sinar.
