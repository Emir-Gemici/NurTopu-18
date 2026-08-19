# FILO 1 · LANE 10/15 · T118 PAYDA SOZLESMESI TARAMASI
Kosum: 2026-08-20, statik kod incelemesi (dosya okuma + REVIEW_LOG izleme).
Girdi: filo1_adaylar.json grubu [10] — 3 dosya, 12 aday satir.
Not: Bu lane'de kod KOSULMADI; butun bulgular kaynak+belge izinden (K-07, T59/D-84/D-85 blogu).

| dosya:satir | PAYDA NE | ESIGE KARSI KULLANIM | ESIK HANGI PAYDADA KALIBRE | DURUM |
|---|---|---|---|---|
| codes/rpi_inference.py:1233 | ICERIK kutusu (`icerik_w*icerik_h`, rpi_inference.py:1232) | EVET — `min_area_ratio` (varsayilan 0.01, rpi_inference.py:1081) uzerinden `_koridor_alani_yeterli` (rpi_inference.py:769-771, o da `icerik_w*icerik_h` kullanir) | ICERIK: K-07 (REVIEW_LOG.md:288-312) esigin niyetini "gercek goruntu (icerik)" olarak sabitledi; letterbox-payda hali REGRESYON ilan edilip duzeltildi. 0.01 degerinin AMPIRIK kalibrasyon kosumu bulunamadi (varsayilan sabit) — deger BELIRSIZ, payda niyeti K-07 ile net | UYUMLU (payda-payda). Esik degerinin kokeni BELIRSIZ ama payda uyusmazligi YOK |
| codes/rpi_inference.py:1237 | Ayni degerin hata mesajinda basimi (alan_orani, ICERIK paydasi) | Ayni kapi (min_area_ratio) — yalniz raporlama satiri | 1233 ile ayni | UYUMLU |
| codes/rpi_inference.py:1453 | HAM goruntu (tum kare LAB L ortalamasi; kaplama orani DEGIL, parlaklik ortalamasi) | EVET — `DARK_L_MEAN = 80.0` (rpi_inference.py:1448) karanlik kapisi | HAM goruntu paydasi kodda BILINCLI korunuyor: `_preprocess` normalizasyonu DOLGUDAN ONCE cagiriyor, gerekce yorumda "gri dolgu LAB ortalamasini kaydirip is_dark() kararini bozardi" (rpi_inference.py:1491-1492). Tek cagiran `simulation/scripts/iha_perceive.py:99` de HAM img veriyor. 80.0 degerinin kalibrasyon kosumu/D-kaydi BULUNAMADI — BELIRSIZ | UYUMLU (deger ve kullanim ayni paydada: ham goruntu). Esik kokeni BELIRSIZ |
| codes/rpi_inference.py:1463 | HAM goruntu (normalize_light icinde ayni LAB L ortalamasi) | EVET — ayni `DARK_L_MEAN` esigi (gamma tetigi) | 1453 ile ayni (ham goruntu; koken BELIRSIZ) | UYUMLU. 1453 ile ayni buyukluk, ayni payda — ic tutarli |
| codes/test_rota_sentetik.py:61,63,98,100 | KAPLAMA-DEGIL: `moloz_orani` sentetik bariyer pikselinin SILINME kesridir (bozulma taramasi parametresi); hicbir esige karsi kiyaslanmaz | — | — | KAPSAM DISI (tek satirla elendi) |
| scripts/olcum/58_b1_bagimsiz.py:66 | ICERIK kutusu (`karar_sozlesmesi.zemin_kaplamasi(zemin, icerik)`, karar_sozlesmesi.py:426-443 — payda `iw*ih`) | HAYIR (bu betikte): kaplama yalniz ort/min/maks ISTATISTIK olarak basiliyor; betigin kapisi `bos maske == 0` (satir 116-117), kaplama esigiyle kiyas YOK. Not: ayni fonksiyonun uretimdeki esigi `ZEMIN_KAPLAMA_TAVANI = 0.67` (karar_sozlesmesi.py:423) | 0.67 tavani T59'da ICERIK paydasinda, uretim zinciriyle kalibre (karar_sozlesmesi.py:371-423; D-84/D-85/D-86 atiflari acik) — bu betigin olcum paydasiyla AYNI | UYUMLU / BILGILENDIRICI (esik kiyasi bu dosyada yok) |
| scripts/olcum/58_b1_bagimsiz.py:9,30,86 | Yukaridaki satirin docstring/import/baslik baglami (ayni ICERIK paydasi ilani) | 66 ile ayni | 66 ile ayni | UYUMLU |

## OZET
- 12 aday satirin 4'u kaplama-degil (test_rota_sentetik.py moloz_orani) — tek satirla elendi.
- Kalan 8 satirda [UYUSMAZLIK] YOK: alan kapisi ICERIK/ICERIK (K-07 duzeltmesi sonrasi), karanlik kapisi HAM/HAM (dolgu-oncesi cagri bilincli), kaplama olcumu ICERIK/ICERIK (T59 tavani ayni paydada).
- Iki esik degerinin AMPIRIK kokeni BELIRSIZ: `min_area_ratio=0.01` ve `DARK_L_MEAN=80.0` — payda uyusmazligi degil, kalibrasyon izi eksikligi.

ANA BULGU: Lane 10'daki 12 aday satirda payda uyusmazligi 0/12 — alan kapisi K-07 ile ICERIK'e sabitlenmis, karanlik esigi bilerek ham goruntude, 0.67 tavani ile olcum ayni ICERIK paydasinda; yalniz 0.01 ve 80.0 sabitlerinin kalibrasyon kokeni BELIRSIZ.
ETIKET: [BILGILENDIRICI]
