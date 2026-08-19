# FILO 1 · LANE 11/15 · T118 PAYDA SOZLESMESI TARAMASI
# Girdi: filo1_adaylar.json grup 11 (0-indeksli)
# Dosyalar: scripts/olcum/62_haritalama_gorseli.py · scripts/olcum/71_gercek_kare_etiketleyici.py · codes/costmap_path_finder.py
# Yontem: statik kod okumasi (kosum yok); esik kokeni karar_sozlesmesi.py yorum bloklarindan (T59, D-84/D-85) izlendi.
# Tarih: 2026-08-20 · Ajan: filo1-lane11

## Referans (esik kokeni)
ZEMIN_KAPLAMA_TAVANI = 0.67, tanim: codes/karar_sozlesmesi.py:423.
Kalibrasyon: T59 (karar_sozlesmesi.py:383-396), uretim zinciri v24 conf=0.30,
kaplama = zemin_kaplamasi(trav, icerik) -> PAYDA = ICERIK KUTUSU (iw*ih),
fonksiyon tanimi karar_sozlesmesi.py:426-443.

## Tablo

| dosya:satir | payda ne | esige/kapiya karsi mi | esik hangi paydada kalibre | uyum |
|---|---|---|---|---|
| scripts/olcum/62_haritalama_gorseli.py:35 | kaplama-degil (import satiri: zemin_kaplamasi, zemin_maskesi_reddi vd. karar_sozlesmesi'nden) | - | - | - |
| scripts/olcum/62_haritalama_gorseli.py:62 | ICERIK kutusu — `zemin_kaplamasi(trav, icerik)`; trav `_maskeleri_icerige_kirp` cikisi, icerik `_preprocess`'ten | Dogrudan degil: bu deger yalniz panel basligina yazilir (satir 115). Asil kapi ayni dosyada satir 64'te `zemin_maskesi_reddi(trav, icerik)` ile calisir; o fonksiyon ZEMIN_KAPLAMA_TAVANI'ni (karar_sozlesmesi.py:423, kullanim :556/:577) icerde ayni `zemin_kaplamasi(trav, icerik)` ile hesaplar | ICERIK kutusu (T59, karar_sozlesmesi.py:383-396) | UYUMLU |
| scripts/olcum/62_haritalama_gorseli.py:89 | LETTERBOX karesi — `gecilebilir.mean()`: gecilebilir tam kare (sq) boyutlu dizi, payda h*w (dolgu dahil); icerik kirpmasi maskede sifir olsa da paydada dolgu sayilir | HAYIR — yalniz gorsel altyazi (c-uzayi paneli bilgi satiri), hicbir esikle kiyaslanmaz | - (esik yok) | UYUMLU (bilgi amacli; ICERIK paydasina gore degeri sistematik DUSUK gosterir, karar etkisi yok) |
| scripts/olcum/62_haritalama_gorseli.py:115 | ICERIK kutusu (satir 62-63'teki kaplama/kenar degerlerinin panel basligina yazimi) | HAYIR — gorsel etiket; kapi karari satir 64'te ayrica alinmis | ICERIK kutusu | UYUMLU |
| scripts/olcum/71_gercek_kare_etiketleyici.py:184 | HAM goruntu — `engel.mean()`: maske ham kare (img) boyutunda uretilir, letterbox yok | HAYIR — ozet.json/etiket onerisi tanisi | - | UYUMLU |
| scripts/olcum/71_gercek_kare_etiketleyici.py:185 | HAM goruntu — `zemin.mean()` (zemin = 1 - engel, ham kare) | HAYIR — tani alani | - | UYUMLU |
| scripts/olcum/71_gercek_kare_etiketleyici.py:322 | HAM goruntu — satir 185'teki `zemin_orani` degerlerinin dizisi (medyan/min/maks ozeti icin) | HAYIR — konsol ozeti | - | UYUMLU |
| scripts/olcum/71_gercek_kare_etiketleyici.py:328 | Karsilastirma satiri: HAM-goruntu GT zemin_orani (satir 322) ile "v27 kaplamasi ~0,81" ve "kapi tavani 0,67" ayni print'te aniliyor | Evet ama yalniz BILGILENDIRICI print — kod hicbir esikle kiyas/karar yapmiyor; ~0,81 sayisi baska bir kosumdan aktarilmis yorum, kaynagi bu dosyada izlenemiyor (BELIRSIZ) | Tavan 0,67: ICERIK kutusu (T59). Buradaki zemin_orani: HAM goruntu. NOT: raw_frames karelerinde icerik kutusu ham goruntunun birebir olcekli izdusumu oldugundan iki oran matematiksel esdegerdir (dolgu icerik disinda kalir) — sayi kiyasi bu ozel durumda gecerli | UYUMLU (esdeger payda; yine de print katma-deger sayi ~0,81'in kosum kaynagi BELIRSIZ) |
| codes/costmap_path_finder.py:368 | kaplama-degil — `bant_yukseklik_orani=0.06` geometri parametresi: kapi bandinin yuksekligi, payda serbest-alan DIKEY bbox yuksekligi (bbox_h), kaplama orani degil | HAYIR — bant konumlandirma | - | - |
| codes/costmap_path_finder.py:429 | kaplama-degil — ayni parametrenin by0 hesabinda kullanimi | HAYIR | - | - |
| codes/costmap_path_finder.py:430 | kaplama-degil — ayni parametrenin by1 hesabinda kullanimi | HAYIR | - | - |

## UYUSMAZLIK sayimi
Bu grupta [UYUSMAZLIK] YOK (0/11 satir). Tek esik temasi olan zincir
(62_haritalama_gorseli -> zemin_maskesi_reddi -> ZEMIN_KAPLAMA_TAVANI) hem
olcumde hem kalibrasyonda ICERIK kutusu paydasini kullaniyor (T59 ile ayni yol).

Notlar (bilgilendirici, esik disi):
- 62:89 `gecilebilir.mean()` LETTERBOX paydasindadir; ICERIK paydasina gore
  dusuk okunur ama yalniz gorsel altyazidir, karara girmez.
- 71:328'deki "~0,81" sayisinin hangi kosumdan geldigi bu dosyadan
  izlenemiyor: BELIRSIZ (muhtemelen v27 raw_frames kosumu, atif yok).

ANA BULGU: Lane 11'in 11 aday satirinin hicbirinde payda uyusmazligi yok — tek gercek kapi kullanimi (62_haritalama_gorseli.py:62-64) ICERIK-kutusu paydasinda olup 0,67 tavaninin T59 kalibrasyon paydasiyla ayni, kalan satirlar esiksiz tani/gorsel/geometri (0/11 UYUSMAZLIK).
ETIKET: [BILGILENDIRICI]
