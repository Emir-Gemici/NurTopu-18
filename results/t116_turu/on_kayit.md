# T116/T79 TURU · ON KAYIT — OLCUMLER KOSULMADAN once yazildi (D-107)
# Yazan: Claude 2 / Fable 5 (basamele) · 2026-08-20
# Kapsam: yalniz VERDIKT iceren iki lane (T116-A, T79-yeniden). T116-B, T91/T92,
# T101 lane'leri SAF TANIDIR — gecti/kaldi yorumu YAPILMAZ, yalniz sayi raporlanir.

## ⚠ BULASMA BEYANI (durustluk kaydi)
Bu on kayit yazilirken su sayilar ZATEN gorulmustu (D-184/T106 kosumu):
raw_frames HAVUZ ortalama zemin @conf 0,30 — v34 %45,67 · v30 %33,44.
GORULMEYENLER: v21/v22'nin bu 67-kare kumedeki degerleri · kare bazinda
dagilimlar · cati bolgesi gorselleri · v34'un kararlilik (68) ve ONNX
denklik (67) sayilari. Olcutler gorulmeyen alanlara baglanmistir.

## LANE 1 · T116-A — "OTOPARK KAPLAMASI BELIRGIN DUSTU" SAYISAL TANIMI

Taban: %80,6 (mimarin T54 metnindeki taban; B1/T58 kosumu 30 gercek drone
karesi, v21/v24, conf 0,30 ~%81,0 ile ayni mertebe). BU KOSUMDA taban yeniden
olculur: v21 (v21_gercek_doku/best.pt) ayni 67 karede, ayni zincirle.

  (A1) BELIRGIN DUSUS := v34'un KARE BAZLI MEDYAN kaplamasi, AYNI KOSUMDA
       olculen v21 medyanindan EN AZ 20 PUAN dusuk olacak.
       (20 puan: taban %80,6 ile bugunku havuz %45,7 arasindaki fark ~35
       puandir; 20 puan bunun yarisindan fazlasini kare-medyani duzeyinde de
       ister — havuz ortalamasinin tek tuk asiri kareyle susmesini engeller.)
  (A2) GORSEL KAPI (D-80, BAGLAYICI): bina catili en az bir karede v34
       maskesi catiyi YESIL BOYAMAYACAK. Sayi tutup gorsel tutmazsa SONUC
       "TUTMADI"dir — gorsel kazanir.
  (A3) v34 medyani v30 medyaninin ALTINDA olmak ZORUNDA DEGIL (havuzda ustte
       oldugu zaten biliniyor — bulasma beyani). A1 v21'e karsi tanimlidir;
       v30 kiyasi RAPORLANIR ama verdikte girmez.

## LANE 3 · T79-YENIDEN — "T54 KAZANCI KARARLILIKTA GORUNUYOR" TANIMI

Recete D-142 ile BIREBIR (sigma=2/255 · tekrar=3 · tohum=7 · kume t66 ·
conf 0,30 · 68_karar_kararliligi.py DEGISTIRILMEDEN):

  (B1) v34 CEVRILEN KARE < 8/260 ise "iyilesme GORUNUYOR";
       == 8 ise "DEGISMEDI"; > 8 ise "GERILEDI". Esik icat edilmedi:
       8/260, D-142'nin v30 kosumudur.
  (B2) 67_onnx_karar_denkligi.py v34 pt-vs-onnx: uyusmazlik sayisi RAPORLANIR
       ve betigin KENDI kapisiyla yorumlanir (betik ne diyorsa o); ayrica
       tarihsel 2/260 (D-119 donemi) yanina yazilir — o farkli modelin
       sayisidir, esik DEGILDIR.

## CURUTME KURALI (turun harnessi)
Her lane ana bulgusuna 3 bagimsiz curutucu (mercek: olcum dogru mu / yorum
dogru mu / ayni sayi baska sebeple cikar mi). 2/3 "refuted" derse bulgu DUSER
ve REVIEW_LOG'a "kuruldu ve DUSTU" diye yazilir — sonuc kaydi olarak DEGIL.

## SENTEZ KURALI
T79/T91/T92/T101 "ortak kok" hipotezi: lane'lerin kare kimlik kumelerinin
KESISIMI bosalirsa hipotez CURUMUS sayilir; kesisim buyukse (>= en kucuk
kumenin yarisi) "ortak kok OLASI" denir ama kanit sayilmaz (korelasyon).
