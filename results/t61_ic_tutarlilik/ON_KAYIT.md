# ÖN KAYIT — T61: iç-tutarlılık adayları (KEŞİF turu, EŞİK YAZILMAZ)

**Tarih:** 2026-09-03 · **Yazan:** Claude 2 (Opus 5, amele) ·
**Direktif:** `MIMAR_DIREKTIFLERI_20260903.md` İş 3 ·
**Yöntem SONUÇ GÖRÜLMEDEN yazıldı (D-107).**

## 0. Sorun (D-86 → T61)

Kaplama ve kenar ölçütleri **yapısal olarak** orta şiddetli çökmeyi
yakalayamaz (ikisi de alan/temas ölçüsü). Gereken: maskenin **iç
tutarlılığı** — maske içindeki doku/renk dağılımı tek bir yüzeye mi ait,
yoksa model birbirine benzemeyen bölgeleri mi birleştirmiş.
D-398 (dün gece) beş "alan" adayını ölçtü ve **hiçbiri ayırmadı**; bu tur
farklı bir eksene, **doku/renk iç tutarlılığına** bakar.

## 1. Adaylar (mimar direktifinden; bu turda sabit)

| # | ölçüt | OpenCV karşılığı (madde 4: yalnız cv2 + NumPy) |
|---|---|---|
| **B1** | maske-içi HSV kanal varyansı | `cvtColor(BGR2HSV)` + `meanStdDev(mask=…)` → S ve V std |
| **B2** | bileşen-bazlı ortalama renk sapması | `cvtColor(BGR2LAB)` + `connectedComponentsWithStats` → bileşen LAB ortalamaları arasındaki ağırlıklı yayılım |
| **B3** | maske-içi Laplacian enerji dağılımı | `Laplacian(CV_32F)` → enerji; **maske ERODE edilerek** örneklenir (kenar sızıntısı korunur) |

## 2. Çöküş tanımı — EŞİKSİZ

Çökme "vekildir": `gercek_kare_etiket_v1` (67 kare, YOLO-seg poligon,
sınıf 0 = zemin) üzerinde **IoU(model zemin, GT zemin)** hesaplanır.
**Kesme noktası SEÇİLMEZ.** Bunun yerine:

1. Her adayın IoU ile **sıra korelasyonu** (Spearman = sıralar üzerinde
   Pearson; saf NumPy) — "ölçüt çökmeyi izliyor mu?"
2. IoU **çeyrekleri** bazında adayların dağılımı (betimsel).
3. Referans olarak kabul kümesi t66 (260 kare) dağılımı.

Böylece bu tur bir eşik ÜRETMEZ; eşik ancak ikinci bir ön kayıtla,
**tüm kümede süpürülerek** yazılır (D-86 dersi: alt kümede "tam ayrık"
görünen eşik tümde ayırmaz).

## 3. Geçerlilik kapıları (sonuç görülmeden)

| # | kapı | GEÇTİ ölçütü |
|---|---|---|
| X1 | GT okunabildi | 67/67 karede poligon→maske dönüşümü ve IoU hesaplandı |
| X2 | Sayısal sağlamlık | Hiçbir adayda NaN/sonsuz yok |
| X3 | Tek çıkarım | Kare başına 1 segmentasyon çağrısı (sayaçla) |
| X4 | Kenar sızıntısı korumalı | B3 maskesi erode edilerek örneklendi (yapısal kanıt: erode çağrısı çıktıda) |
| X5 | Vekil dürüstlüğü | IoU dağılımı raporlanır; çöküş vekili tek mekân/67 karedir ve öyle anılır |

## 4. Madde 15

Bu turda **hiçbir ölçüt üretime bağlanmaz.** İleride bağlanırsa yalnız
**REDDEDEBİLİR** — serbest alanı büyütemez.


---

## SONUÇ (2026-09-03, ölçüm sonrası yazıldı) — n=67 GT + 260 referans, v36

GT IoU dağılımı: medyan **0,412** · min 0,228 · maks 0,588 (Q1 0,370 · Q3 0,492).

| aday | IoU ile sıra korelasyonu | t (df=65) | p (iki yönlü) | hüküm |
|---|---|---|---|---|
| B1 S std | +0,097 | +0,79 | 0,435 | anlamsız |
| **B1 V std** | **−0,345** | −2,96 | **0,0042** | **Bonferroni'yi geçer** (α=0,01) |
| B2 LAB yayılım | −0,007 | −0,05 | 0,957 | anlamsız |
| B3 Laplacian ort. | +0,106 | +0,86 | 0,393 | anlamsız |
| B3 Laplacian std | +0,003 | +0,02 | 0,981 | anlamsız |

Çeyrek medyanları hiçbir adayda tekdüze eğilim göstermiyor (B1 V hariç ve
onda da zayıf: 37,4 → 35,9 → 32,9 → 34,1).

### 🔴 Bu turun EN ÖNEMLİ bulgusu: D-86'nın dersi canlı tekrarlandı

Aynı betik **6 karelik** duman koşusunda şu korelasyonları vermişti:
B1 S **−0,829** · B2 **+0,943** · B3 std **−0,943**. Tam kümede (67) bu
sayılar sırasıyla **+0,097 · −0,007 · +0,003**'e çöktü — hatta **işaret
değiştirdiler**. Yani küçük örneklemle bakılsaydı "üç aday da güçlü ayırıyor,
hatta B2 ve B3 mükemmele yakın" denecekti. D-86'nın uyarısı (*"alt küme
üzerinde tam ayrık görünen eşik, kümenin tamamında ayırmayabilir"*) bu turda
**birebir gerçekleşti.**

### Hüküm (bu tur eşik ÜRETMEZ — direktif)

- **B1 S std · B2 LAB yayılım · B3 Laplacian (ort ve std): DOĞRULANAMADI.**
  Çökmeyi (GT IoU'sunu) izlemiyorlar.
- **B1 V std: ZAYIF ama anlamlı sinyal** (r = −0,345; p = 0,0042; 5 adaylık
  Bonferroni düzeltmesini geçer). Yön beklenen yönde: IoU düştükçe maske-içi
  **parlaklık (V) varyansı artıyor** — model birbirine benzemeyen parlaklıkta
  bölgeleri tek zemin sayıyor.
  ⚠ Etki büyüklüğü küçüktür (r² ≈ %12); **kapı yapılamaz.** Eşik ancak ikinci
  bir ön kayıtla ve tüm kümede süpürülerek yazılır.

### X kapıları

X1 GT okunabildi 67/67 **GEÇTİ** · X2 sayısal sağlamlık **GEÇTİ** ·
X3 tek çıkarım (327/327) **GEÇTİ** · X4 kenar sızıntısı koruması
**GEÇTİ** (erode r=3) · X5 vekil dürüstlüğü: çöküş vekili tek mekân,
67 kare — genellemesi sınırlıdır.
