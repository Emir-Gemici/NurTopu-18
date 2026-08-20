# T122 ON KAYIT — egitimler KOSULMADAN once yazildi (D-107)
# Yazan: Claude 2 / Opus 5 (basamele) · 2026-08-20
# Dayanak: mimar T122 emri ("dort secenegi OLC ve ONER; secim MIMARIN"),
#          D-225 (T121 sonucu: cati DONDU, K0 TAKAS), D-219 (etiket istatistigi)

## NEDEN EGITIM KOSULUYOR
D-219'da dort secenek yalniz IZDUSUMLE (etiket dagilimi) kiyaslanmisti.
T121 yalnizca (c)'nin bir cesidini GERCEKTEN olctu. Kullanici GPU kosumuna
acik izin verdi; bu yuzden (a) ve (a)+(c) de OLCULEREK kiyasa girecek.
Boylece dort secenegin UCU olculmus, biri ((d)) kutle tablosuyla kalir.

## KOSULACAK IKI EGITIM (recete T121 ile BIREBIR AYNI)
Taban v34 · epochs 40 · patience 15 · imgsz 512 (56 zinciri RECETE'si;
101_t121_ft_kosumu.py ile AYNI cagri). Degisen TEK sey ETIKET:
  KOSUM A — secenek (a) "DOGRULANMIS ZEMINE DARALT":
      zemin = aday_v5c(conf 0,05) zemin maskesi   [uretecin KENDI kahini,
      manifest'teki zemin_model ve zemin_conf birebir]
      cati AYRICA isaretlenmez (etiketsiz kalir), engel/hedef DEGISMEZ.
  KOSUM B — secenek (a)+(c) "DARALT + CATI ENGEL":
      zemin = v5c zemin maskesi MINUS cati
      engel = mevcut engel + CATI (T121'in elle+homografi maskesi)
Karsilastirma kumesi (dort model): v34 (taban) · t121_ft ((c)) · A ((a)) ·
B ((a)+(c)).

## OLCULECEKLER (hepsi AYNI zincir, 102_t121_degerlendirme.py)
1. Cati diskleri (6 kare, diskler.json REV1): cati->engel, cati->zemin,
   zemin->zemin.
2. 67 karede kaplama IKI PAYDAYLA (ICERIK: karar_sozlesmesi zinciri /
   LETTERBOX: 65 denetcisi) + zemin_maskesi_reddi sayisi.
3. 65 kabul zinciri: K0 (figur orani) + K1..K4 + K5 durumu.

## KARAR KURALLARI (SONUC GORULMEDEN)
- "CATI DONDU" olcutu T121 ON KAYDIYLA AYNI ve DEGISMEZ:
  cati disklerinde ort. ENGEL >= 0,50 VE ort. ZEMIN <= 0,30.
- "ARENA BOZULMADI": K1 >= 230 (ESIK sozlugunden) VE K2/K3/K4 GECTI.
- K0: kabul edilebilir en kotu deger T121 on kaydiyla AYNI —
  K0_oran >= 0,5 (uretim tabaninin yarisi). ALTINDA kalan secenek
  "TAKAS" diye yazilir, KAZANDI diye YAZILMAZ.
- 🔴 K0 OLCUM NOTU (D-229 tanisi, EGITIMDEN ONCE yazildi): figurde v34 ile
  t121_ft'nin zemin maskeleri SIFIR piksel ortusuyor ve kaybolan zeminin
  %100'u HICBIR SINIFA gitmis (engel de dusmus). Yani K0 orani bu figurde
  iki modeli AYNI SEY uzerinden kiyaslamiyor olabilir. Bu bir ESIK
  DEGISIKLIGI GEREKCESI DEGILDIR (esik degistirmek yetkim disi, SS9.2);
  yalnizca RAPORDA her modelin figur ortusme oranini (IoU) da basacagim ki
  mimar sinyalin kararliligini gorebilsin.
- Secenek SIRALAMASI su sozlukle yazilir: her secenek icin
  (cati_dondu?, arena_bozulmadi?, K0_orani, gercek-kare ICERIK kaplama
  medyani). SECIM MIMARINDIR — ben siralar ve gerekcelendiririm.

## SIMDIDEN BILINEN SINIRLAR
- Dort model de AYNI 67 karenin kaynak kumesinde egitildi/olculuyor:
  bu ALAN-ICI etiket etkisidir, GENELLEME kaniti DEGILDIR.
- Kosum basina TEK tohum (seed=0, recetede sabit). Tohum gurultusu
  olculmedi (D-135); iki kosum arasindaki kucuk farklar tohum kaynakli
  olabilir ve boyle raporlanacak.
- v5c kahini acik-oluklu catida zayifti (0,50 sizinti, D-218) — (a) ve (b)
  bu zayifligi tasir; raporda yazilacak.
- (b) ve (d) EGITILMEYECEK: (b) icin D-219'da ultralytics kaynagindan
  olculen "etiketsiz = siniflandirma negatifi" bulgusu ve gercek-doku zemin
  denetiminin tamamen kaybolmasi riski var; (d) etiket degistirmiyor,
  kutle tablosu (97) zaten olculdu. Ikisi de "OLCULMEDI" diye yazilacak —
  DUSTU diye DEGIL (D-180).
