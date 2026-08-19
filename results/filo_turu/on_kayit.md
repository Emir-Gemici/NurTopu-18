# DORT FILO TURU · ON KAYIT — olcumler kosulmadan ONCE yazildi (D-107)
# Yazan: Claude 2 / Fable 5 (basamele) · 2026-08-20 · dayanak D-207 (mimar hukmu)

## FILO 1 · T118 PAYDA — SINANACAK IDDIA (ilan degil)
Iddia (mimarin verdigi, sinanacak): "denetcinin ~%45 dedigi otopark kareleri,
URETIMIN KENDI olcusuyle (zemin_kaplamasi -> ICERIK paydasi) 0,67 tavaninin
USTUNDEDIR ve zemin_maskesi_reddi tetiklenir."
KARAR KURALI (sonuc gorulmeden):
  - Olcum: 67 raw_frames karesi, v34, uretim zinciri (_preprocess -> predict
    conf 0,30 -> get_masks -> kirp -> zemin_maskesi_reddi(trav, icerik)).
  - Iddia DOGRU sayilir <=> karelerin >= %80'inde red ZEMIN_KAPLAMA_TAVANI
    kaynakli doner. %20-%80 arasi: KISMEN (dagilimi yaz). < %20: iddia YANLIS.
  - HER SONUC yazilir; "tavan hic tetiklenmiyor" da SONUC-DEGISTIRENDIR.
ESIK DEGISTIRILMEZ; tarama-olcum-rapor turudur.

## FILO 2 · BAYATLIK — KARAR KURALI
Gorev basina 1 dogrulayici + 2 curutucu. Kanit cumlesi bugunku kod/modelle
yeniden uretilir. SONUC uc degerli: HALA GECERLI · SAYI KAYMIS (yeni sayi
verilir) · ARTIK YOK. 2/3 curutucu "gercek degil" derse gorev yalnizca
KAPANMA ADAYI olarak isaretlenir — kapatma karari MIMARINDIR.
OLCULEMEDI ayri kategoridir ve DUSTU/ARTIK-YOK sayilmaz (D-180).

## FILO 3 · MUTASYON SUPURMESI — KARAR KURALI
Dosya basina TEK ajan, KENDI git worktree'sinde (ana agaca dokunulmaz).
"KORUMASIZ TEST DOSYASI" := hedefli en kucuk mutasyonda O DOSYANIN testlerinden
SIFIR test dusuyor. Mutasyon secimi ajanin; ama dosyanin docstring/adinin ilan
ettigi korumayi hedeflemeli. Dusen>0 ise KORUYOR. Ajan mutasyonu geri alir ve
`git status --porcelain` BOS ciktisini kanit olarak verir. Mutasyonlar ASLA
commit edilmez. Worktree icinde yedek-al/geri-koy serbesttir (ana agacin
"git checkout yasak" kurali kullanicinin izlenmeyen dosyalarini korur; temiz
worktree'de o risk yoktur — yine de yontem yedek dosyasidir).

## FILO 4 · T117 — KARAR KURALI
Alti hipotez esit statuyle olculur: GSD/irtifa · gorunum-doku · sinif
dengesizligi · etiket kalitesi · cozunurluk/imgsz · guven esigi.
Hipotez DESTEKLENDI sayilir <=> olcumu yon olarak dogru VE 2/3 curutucudan
sag cikar. Birden fazlasi desteklenebilir (dislayici degil). HICBIRI
desteklenmezse sonuc "aciklama bulunamadi — yeni hipotez gerekir" diye
yazilir; uydurulmaz.

## GENEL
Butun bulgular [SONUC-DEGISTIREN] / [BILGILENDIRICI] olarak ikiye ayrilir;
rapor basina en cok 15 SONUC-DEGISTIREN. 2/3 curutulen bulgu DUSER ve
"kuruldu ve DUSTU" olarak yazilir.
