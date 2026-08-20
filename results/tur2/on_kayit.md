# TUR 2 · ON KAYIT — olcumler kosulmadan ONCE yazildi (D-107)
# Yazan: Claude 2 / Fable 5 (basamele) · 2026-08-20 · dayanak: mimarin TUR 2 emri (D-209)

## T119 · yayinlanan `road`a DAVRANISSAL kapi — KARAR KURALI
- Test, ayirt edici sahnede (darbogaz serit != baskin serit) YAYINLANAN road
  DEGERINI dogrudan assert eder (alan adini degil).
- KAPI SAYILIR <=> :1349 (darbogaz->baskin) mutasyonu uygulaninca test DUSER.
  Dusen testin ADI yazilir.
  [DUZELTME, olcum ONCESI: emirdeki :1349 `rpi_inference.py:1349`tur
   (`open_path = olcum["darbogaz_serit"]`); ilk yazimda dosyayi yanlis
   yazmistim (costmap_path_finder.py 1284 satir). Kural degismedi.]
- Bayt-kimligi testinin dusmesi KANIT SAYILMAZ (D-209).
- Rapor bicimi (yeni baglayici kural): "dosya: <dusen>/<toplam> · takim: <dusen>/<takim-toplami>"
- Mutasyon ASLA commit edilmez; geri alma yedek-dosya yontemiyle, kanit
  `git status --porcelain` uzerinden ILGILI dosyanin temiz oldugudur.

## T120 · tests/ kesif kapsami — KARAR KURALI
- tests/ altindaki HER .py icin "discover kac test topluyor" olculur
  (test_ onekli olmayanlar dahil).
- SIFIR toplayan her dosya BULGUDUR. Karar (cevir/tasi/birak) MIMARIN.
- Hicbir dosya silinmez/tasinmaz (kullanici dosyasi kurali).

## T118 kalan is · 6 dosya — KARAR KURALI
- 6 dosya (48:149/163/183 · 65:126-134 · 54:143 · 93:97 · 67:113 ·
  saha_kuru_kosu:543-549) icin soru: LETTERBOX/HAM paydali deger bir ESIKLE
  kiyaslaniyor mu, ya da bir rapora/karara giriyor mu?
- ESIGE/KARARA giriyorsa -> gorev onerisi acilir. Girmiyorsa -> "yalniz insan
  okumasi" diye kayda gecer. Kod DEGISTIRILMEZ (adlandirma karari mimarin).

## FILO 2/4 KAYIT ISLEME — KURAL
- Filo 2: 23 gorev karari REVIEW_LOG + kuyruk durum satirlarina islenir;
  guvenlik-siniflandiricisiz kosan 8 curutucu AYRICA isaretlenir (ham dosyadan
  mekanik cikarilir, elle liste yazilmaz).
- Filo 4: 6 hipotez sonucu islenir; "hicbiri aciklamiyor"sa oyle yazilir.
- Kapanma KARARI verilmez — kapanma ADAYI olarak mimara sunulur.

## GENEL
- [SONUC-DEGISTIREN] / [BILGILENDIRICI] ayrimi zorunlu, ilk 15 kurali gecerli.
- Kapilar: test_rota_sentetik 15/15 + discover (mevcut 655, T119 ile artar).
- codes/ altinda kod degisikligi YOK (T119/T120 tests/ isidir);
  config/model_registry.json'a dokunulmaz.
