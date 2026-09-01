# ÖN KAYIT — T52: "her şey boyanmış" çöküşü ile gerçek açık arenayı ayıran ölçüt

**Tarih:** 2026-09-03 (gece) · **Yazan/karar: Claude 2 — Fable 5, mimar** ·
**Eşikler ve karar kuralı SONUÇ GÖRÜLMEDEN yazıldı (D-107).**

## 0. Sorun (D-65/D-284 zinciri)

Ham kaplama oranı üst uçta ayırt etmiyor: kadraj kümesinin **meşru** azamisi
%82,3; otoparkın **çöküş** değeri %73,7–82,5 (D-65). D-215'in v34 "boşluk
var" bulgusunu D-284 çürüttü (yalnız kaplama ekseni ölçülmüş; kenar hiç
sınanmamış; v35'te kenar 0,5004 > 0,50 tavan). Köprü tavan 0,55 yürürlükte
ve **bu görev bitmeden değiştirilmeyecek**.

## 1. Ölçüm tasarımı

- **Kümeler:** meşru = kabul kümesi (registry `kabul_kumesi`, n=260, kendi
  manifest mpp'siyle) · çöküş = `data/raw_frames` otopark kareleri (n≈67).
- **İmza:** üretimin KENDİSİ — `_preprocess → predict(imgsz=INFER_SIZE,
  conf=0.30) → get_masks → _maskeleri_icerige_kirp`; büyüklükler İÇERİK
  kutusu içinde hesaplanır (T99 dersi: ölçüm üretim imzasıyla yapılır).
- **Model:** kayıt defteri etkin profili (v36). Betik: `scripts/olcum/172`.

## 2. Aday büyüklükler (görev tanımından; bunlarla sınırlı)

| aday | tanım | çöküşte beklenen yön |
|---|---|---|
| A1 | zemin / (zemin + engel) piksel oranı | yüksek (engel az) |
| A2 | zemin maskesinin bağlı bileşen sayısı | düşük (tek yekpare leke) |
| A3 | en büyük bileşenin zemin alanı payı | yüksek |
| A4 | içerik-kenarına dayanma oranı (üretim `zemin_kenar_dayanmasi`) | yüksek |
| A5 | engel pikselinin içerik alanına oranı | ~0 (mutlak yokluk) |

## 3. Karar kuralı (şimdi yazıldı)

1. Bir aday **çakışmasız ayırıyor** sayılır ⇔ meşru kümenin en KÖTÜ değeri
   ile çöküş kümesinin en İYİ değeri arasında işaretli boşluk **> 0**
   (yön tabloya göre).
2. Birden çok aday ayırıyorsa **göreli boşluğu** (boşluk / iki kümenin
   birleşik açıklığı) en büyük olan seçilir ve **eşik önerisi = boşluğun orta
   noktası** olarak RAPORLANIR (uygulama AYRI karar + ayrı ön kayıttır;
   köprü tavan 0,55 bu koşumla DEĞİŞMEZ).
3. Hiçbir aday ayırmıyorsa görev tanımının istediği kayıt yazılır:
   **"DOĞRULANAMADI"** — tavan olduğu gibi kalır, zorlanmaz.
4. Seçilen adayın yanlış-negatif raporu zorunlu: önerilen eşikle meşru
   kümede reddedilecek kare sayısı (çakışmasızlıkta 0 olmalı) ve çöküş
   kümesinde kaçırılacak kare sayısı.

## 4. Ne KANITLAMAZ

Otopark, "her şey boyanmış" çöküşünün TEK örneklemidir (tek mekân, 67 kare);
ayıran bir ölçüt bulunsa bile genellemesi sınırlıdır ve üretime alınması
ayrı ön kayıt + kabul zinciri turu ister.
