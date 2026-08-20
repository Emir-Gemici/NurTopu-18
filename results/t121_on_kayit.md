# T121 ON KAYIT — belirleyici GPU kosumu ONCE yazildi (D-107)
# Yazan: Claude 2 / Fable 5 (basamele) · 2026-08-20 · dayanak: mimar T121 emri + D-210/D-211

## Deney (mimar tasarimi, D-211 §4)
>=20 catili kaynak karede cati bolgesi SINIF 1 etiketlenir (tam-kare zemin
poligonu o bolgeden CIKARILIR — copy_paste_gercek kompozitlerinin etiketleri
yamalanir, GORSEL degismez, YENI VERI YOK). AYNI receteyle fine-tune, TEK gece.
Etiket yontemi: v30 engel maskesi BASLANGIC (buyuk-blob suzgeciyle), her kare
GOZLE dogrulanir/duzeltilir (D-80); kirmizi kiremit ELLE (v30 kiremitte 0,53 —
results/t121/kahin_sondasi.json). Etiketlenen kaynak sayisi n raporda yazilir;
n<20 cikarsa kosum ISTATISTIKI ZAYIF diye isaretlenir (bugunku envanterle
56/56 kaynak catili — n<20 riski dusuk).

## Egitim recetesi (onceden sabit)
- Taban agirlik: models/navitas_seg_v34_best.pt (uretim; D-211 "ayni recete").
- Veri: karisim_t54_engelli.yaml'in KOPYASI, copy_paste_gercek yerine yamali
  kopya kume (dataset/copy_paste_t121/). Diger iki bilesen AYNEN.
- epochs=40 · imgsz=512 · batch/hyp: 56 zinciri RECETE'si birebir
  (56_t53_gercek_karisim.py:40-53; imgsz=512 D-112 karari — ilk yazimda 640
  yazmistim, RECETE kaynagi 512 diyor; DUZELTME GPU kosumundan ONCE islendi).
  Tek gece hedefi; erken kesilirse son epoch raporlanir, olcut GEVSETILMEZ.

## "CATI ENGELE DONDU" — sayiyla tanim (sonuc gorulmeden)
Olcum zinciri: uretim (_preprocess -> conf 0,30 -> get_masks -> icerik kirp),
sonda diskleri = results/t121/diskler.json REV1 (6 kare, cati-ici diskler).
- BASARI: cati disklerinde ort. ENGEL orani >= 0,50 VE ort. ZEMIN orani <= 0,30.
  (Esik kaynagi: v30'un BUGUN olculen 0,776/0,286'si — mevcut bir modelin
   ulastigi seviyenin yarisi taban alinir; 95_t121_kahin_sondasi.json.
   Ciplak sayi degildir.)
- Ayrica 67 karede kaplama IKI PAYDAYLA da yazilir (ICERIK: karar_sozlesmesi
  zinciri / LETTERBOX: 65 denetcisi) + zemin_maskesi_reddi tetik sayisi.
  Beklenti yonu: ICERIK-paydali kaplama medyani 0,80'den asagi iner
  (D-201 v34 taban: ICERIK ~0,800 / LETTERBOX ~0,45).

## K0 (korluk) — kabul edilebilir en kotu deger (sonuc gorulmeden)
65 kabul denetcisi zinciri k0: figur/zemin orani, v34 taban 0,0049 (registry,
T110). KABUL: K0_ft >= 0,5 x K0_v34 (yani oran 0,00245'in altina duserse
secenek KAZANMAMIS, TAKAS yapmistir — 65:120-124'un kendi 0,5 uyari bandi;
ciplak sayi degil). K1 (65 zinciri) ayrica kosulur ve raporlanir.

## Hangi sonuc hangi secenegi kazandirir (onceden)
1. Cati DONDU + K0 KORUNDU  -> kaldirac ETIKET (D-211 tashihi dogrulanir).
   Siralama onerisi: (c)-elle/kahinli ve (a) one gecer; "yeni veri tek
   kaldirac" onculu "gerekli ama tek basina yeterli degil"e iner.
2. Cati DONDU + K0 COKTU    -> TAKAS: etiket duzeltmesi cati kazandirip
   figur kaybettiriyor; (a) (engel eklemeyen daraltma) yeniden tartilir,
   takas SAYIYLA yazilir.
3. Cati DONMEDI             -> mimar tashihi DUSER, "veri tek kaldirac"
   onculu ayakta kalir; (a)-(d) yalniz veri-hijyeni duzeltmesi olarak kalir.
Iki ara sonuc (yalniz biri saglanirsa) KISMEN diye yazilir; esik GEVSETILMEZ.

## Simdiden bilinen sinirlar (sonuc gorulmeden yazildi)
- 67 kare = kompozitlerin KAYNAK karelerinin kumesi (56'si egitimde) —
  bu olcum GENELLEME degil, ALAN-ICI etiket-duzeltme etkisidir; rapor boyle der.
- Fine-tune v34'ten basladigi icin "cati zemindir" on-ogrenmesini tasir;
  DONMEZSE bunun recete-mi/etiket-mi ayrimi TEK geceyle yapilamaz — yazilir.
- Sonda diskleri 6 karedir; 67-kare kaplama olcumu tamamlar.
