# FILO1 LANE 6/15 — T118 payda taramasi (grup indeksi 6)
# Kosum: statik kod incelemesi (dosya okuma), 2026-08-20. Hicbir model kosulmadi.
# Girdi: filo1_adaylar.json[6] — codes/test_rota_guvenlik.py + scripts/olcum/59_t60_uretec_sadakati.py
# Payda siniflari: ICERIK kutusu / LETTERBOX karesi / ham goruntu / maske toplami / kaplama-degil

| dosya:satir | PAYDA NE | esige/kapiya karsi mi | esik hangi paydada kalibre |
|---|---|---|---|
| codes/test_rota_guvenlik.py:395 | kaplama-degil (olcekli kare sayisi / toplam kare sayisi — kare sayimi) | hayir (yalniz raporlanir; TAM_OLCUM durumu 398'de n_olceksiz==0 ile belirlenir) | uygulanamaz |
| codes/test_rota_guvenlik.py:406 | kaplama-degil (ihlal eden kare sayisi / olcekli kare sayisi — kare sayimi, 387) | evet: >0.10 "test gucu" esigi (ayni dosya 417, 542, 552'de yazili) | ayni paydada (kare sayimi) tanimli; kalibrasyon izi yok — dosya ici sabit, D-atfi yok. Payda tutarli, UYUSMAZLIK YOK |
| codes/test_rota_guvenlik.py:407 | kaplama-degil (ihlal eden kare / olcekli kare — kare sayimi, 388) | evet: ==0.0 GECME sarti (525, 545, 549, 552) | ayni paydada (kare sayimi); sifir-esik kalibrasyon gerektirmez. UYUSMAZLIK YOK |
| codes/test_rota_guvenlik.py:415 | kaplama-degil (406'daki oranin okunmasi; cikis kodu) | evet: >0.10 (417) | 406 ile ayni — kare sayimi, dosya ici sabit, iz BELIRSIZ ama payda tutarli |
| codes/test_rota_guvenlik.py:506 | kaplama-degil (406'nin rapor okunmasi) | evet: 542'de <=0.10 uyari dali | 406 ile ayni |
| codes/test_rota_guvenlik.py:507 | kaplama-degil (407'nin rapor okunmasi) | evet: 545/549'da ==0.0 | 407 ile ayni |
| codes/test_rota_guvenlik.py:543 | kaplama-degil (uyari metni; 542 kosulunun ciktisi) | evet: <=0.10 dali | 406 ile ayni |
| codes/test_rota_guvenlik.py:545 | kaplama-degil (enj_oran==0.0 kosulu) | evet: ==0.0 | 407 ile ayni |
| codes/test_rota_guvenlik.py:552 | kaplama-degil (ham>0.10 VE enj==0.0 teshis dali) | evet: 0.10 ve 0.0 | 406/407 ile ayni |
| scripts/olcum/59_t60_uretec_sadakati.py:69 | kaplama-degil (LAB L ortalamasi; payda = doku ornegi maske pikselleri, 66) | dolayli: ZEMIN_L_BANDI (150,159) satir 23'te, 189'da kapi | bant ayni olcum yordamiyla (maske pikselleri uzerinden LAB) tanimli — payda tutarli |
| scripts/olcum/59_t60_uretec_sadakati.py:70 | kaplama-degil (LAB a ortalamasi, ayni maske paydasi) | dolayli: ZEMIN_A_BANDI (190) | ayni yordam, payda tutarli |
| scripts/olcum/59_t60_uretec_sadakati.py:71 | kaplama-degil (LAB b ortalamasi, ayni maske paydasi) | dolayli: ZEMIN_B_BANDI (191) | ayni yordam, payda tutarli |
| scripts/olcum/59_t60_uretec_sadakati.py:84 | kaplama-degil (kategori ortalamasi; payda = ornek sayisi n) | dolayli: 171/177 oran hesabinin girdisi | uygulanamaz (ara istatistik) |
| scripts/olcum/59_t60_uretec_sadakati.py:171 | kaplama-degil (doku_L oranlari: sonra/once; ayni kategori, ayni olcum yordami) | evet: DOKU_KORUMA_ORANI=0.75 (satir 29) | esik ayni dosyada, ayni once/sonra yordami paydasinda tanimli — payda tutarli; 0.75 degerinin dis kalibrasyon izi (D-atfi) yok, BELIRSIZ ama uyusmazlik degil |
| scripts/olcum/59_t60_uretec_sadakati.py:177 | kaplama-degil (banka_zemin doku_L orani, 171 ile ayni yapi) | evet: DOKU_KORUMA_ORANI=0.75 (179) | 171 ile ayni |
| scripts/olcum/59_t60_uretec_sadakati.py:319 | kaplama-degil (k-means palet yuzdesi; payda = ornekleme piksel sayisi say.sum()) | hayir (tanisal palet raporu) | uygulanamaz |
| scripts/olcum/59_t60_uretec_sadakati.py:475 | kaplama-degil (temas_orani = temas / pad_alani_tuval, 423; uretec geometri tanisi) | hayir (min..maks yalniz yazdirilir) | uygulanamaz |

## SONUC
- Bu grupta zemin_kaplamasi/ICERIK/LETTERBOX paydasina dokunan HICBIR satir yok:
  test_rota_guvenlik.py oranlari KARE SAYIMI paydasinda, 59_t60 oranlari DOKU/RENK
  olcum paydalarinda. T118 ICERIK-vs-LETTERBOX sozlesmesine temas eden satir: 0/17.
- UYUSMAZLIK: 0. Her esik, karsilastirildigi degerle ayni paydada tanimli.
- BELIRSIZ kalibrasyon izleri: test_rota_guvenlik.py'deki 0.10 (test gucu) ve
  59_t60'taki 0.75 (DOKU_KORUMA_ORANI) sabitlerinin D-kaydi/T-atfi dosyalarda yok;
  ama bunlar payda uyusmazligi degil, yalnizca gerekce izi eksikligidir.

ANA BULGU: Lane 6 grubundaki 17 aday satirin 17'si kaplama-disi payda (kare sayimi, doku/renk, palet, pad alani) kullaniyor; ICERIK/LETTERBOX payda uyusmazligi 0.
ETIKET: [BILGILENDIRICI]
