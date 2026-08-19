# FILO1 TARAMA · LANE 13/15 (T118 payda sozlesmesi)
Kosum: 2026-08-20 · statik kod incelemesi (dosya + baglami okundu; kod KOSULMADI
— bu lane'in isi payda tespiti, sayisal olcum degil). Girdi: filo1_adaylar.json
grup 13 (0-indeksli), 8 dosya / 10 aday satir.

| dosya:satir | payda ne | esige karsi mi (hangi esik, nerede) | esik hangi paydada kalibre |
|---|---|---|---|
| scripts/olcum/63_bariyer_kesisimi.py:85 | KAPLAMA-DEGIL: `blok[ust]` — payda = LAB a*'dan turetilen BARIYER maskesi pikselleri (tuval cercevesine tasinmis), kare/icerik degil | HAYIR — yalnizca print (bariyer duyarliligi raporu); karar `analyze_path` icinde, bu sayiya bagli degil | esik yok |
| scripts/olcum/63_bariyer_kesisimi.py:86 | KAPLAMA-DEGIL: `trav[ust]` — ayni bariyer-maskesi paydasi | HAYIR — yalnizca print | esik yok |
| scripts/v21_degerlendir_ve_paketle.py:70 | ICERIK kutusu: `mk[0][y0:y0+yuk, x0:x0+gen].sum() / (gen*yuk)` — letterbox seritleri paydada YOK; ICERIK kutusu = ham kare icerigi oldugu icin ham-goruntu paydasina esdeger | EVET — satir 89 `oran >= ASGARI_ZEMIN_ORANI` (0.05, ayni dosya satir 47; kaynak ARCHITECT_PLAN K-8 kapisi, satir ~355 "≥%5 zemin") | K-8 metni payda TANIMLAMAZ ("kare alaninin %5'i", REVIEW_LOG:1117 / D-18); kalibrasyon kosumu D-18/D-20 (67 raw_frames karesi, "ayni zincir") ve v17_referans=10 D-20 KAPI-1 tablosuyla birebir — ayni zincir ICERIK paydasi kullanir. ICERIK = ham kare icerigi oldugundan UYUM VAR; uyusmazlik yok. (K-8 metninin payda sessizligi not edildi, ama iz D-18/D-20'ye cikiyor: BELIRSIZ degil.) |
| scripts/v21_degerlendir_ve_paketle.py:73 | (satir 70'in return'u) ayni ICERIK paydasi + `rota["durum"]` (kaplama-degil) | 70 ile ayni kapi | 70 ile ayni |
| scripts/olcum/52_sentetik_denetim.py:86 | ham/normalize ETIKET alani: ayakkabi-bagi formulu normalize koordinatlarda → payda = ham goruntu alani (=1.0); letterbox/icerik ayrimi yok (etiket uzayi) | HAYIR — yalnizca print (veri seti denetim raporu) | esik yok |
| scripts/olcum/53_drone_kare.py:43 | KAPLAMA-DEGIL: algisal hash esiklemesi `g > g.mean()` (parlaklik medyani-vari), alan orani degil; 46'daki 0.12 Hamming mesafesidir, kaplama esigi degil | dolayli — hash farki 0.12'ye karsi ama bu goruntu-benzerlik esigi | kaplama esigi yok |
| scripts/olcum/66_k5_bariyer_populasyon.py:108 | KAPLAMA-DEGIL: `blok[ust]` — payda = bariyer maskesi pikselleri (63 ile ayni yontem) | HAYIR — `duyar` yalnizca ozet print (satir 142); K5 karari kesisim=0 px olcutune dayanir (D-107), duyarlilik degil | esik yok |
| scripts/olcum/69_arac_referans_olcegi.py:124 | KAPLAMA-DEGIL: `iqr_orani` = IQR/medyan (arac kisa kenari px dagilimi), alan orani degil; dosya kendini "OLCER, KARAR VERMEZ" ilan eder | HAYIR — JSON'a yazilir; 74'te D-124 referansi 0.138 TARTISILIR ama 69'da esik yok | esik yok |
| scripts/olcum/74_olcek_kahini_gecerlilik.py:110 | KAPLAMA-DEGIL: dairesel ortalama (cos/sin, yonelim sd hesabi) | HAYIR — betik acikca "ayirici esik varsa bosluk olmali, yoksa boyle yazilir" der; kapi yok | esik yok |
| scripts/olcum/80_k5_siki_kapi.py:100 | KAPLAMA-DEGIL: `blok[ust]` — bariyer maskesi paydasi (66 ile ayni hesap) | HAYIR — `duyarlilik` kayit alani; K5 karari kesisim px uzerinden | esik yok |

## Ozet
- 10 aday satirin 8'i KAPLAMA-DEGIL (bariyer-duyarliligi maske-alt-kumesi oranlari,
  hash, IQR/medyan, dairesel istatistik, etiket-alani denetimi) ve HICBIRI bir
  kapiya/esige karsi kullanilmiyor.
- Tek esikli satir: v21_degerlendir_ve_paketle.py:70 → ASGARI_ZEMIN_ORANI=0.05
  (K-8). Payda ICERIK kutusu; kalibrasyon kosumu (D-18/D-20, ayni zincir) da ayni
  paydayi kullanmis. ICERIK = ham kare icerigi → paydalar ortusuyor.
- [UYUSMAZLIK] BULUNAMADI bu grupta. Not: ARCHITECT_PLAN K-8 metni ("kare
  alaninin %5'i") paydayi ACIKCA tanimlamiyor — kod ve kalibrasyon tutarli ama
  sozlesme metni sessiz; T118 sozlesmesine "K-8 paydasi = ICERIK" satiri
  eklenmesi onerilir (karar mimarindir).

ANA BULGU: Lane 13'un 10 aday satirindan yalniz 1'i esige karsi kullaniliyor (v21:70, ICERIK paydasi vs K-8 %5) ve kalibrasyon paydasiyla UYUMLU — 0 uyusmazlik.
ETIKET: [BILGILENDIRICI]
