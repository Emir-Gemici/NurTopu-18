# T8 — `analyze_path` Ölçüm Yolu Önce / Sonra

## NEDEN

`codes/test_accuracy.py` kendi karar kopyasını kullanırken raporlanan sayı sevk
edilen `codes/rpi_inference.py:analyze_path` davranışını ölçmüyordu. T8 yerel
kopyayı kaldırır, üretim fonksiyonunu doğrudan kullanır ve letterbox içerik kutusunu
aynı koordinat uzayında geçirir.

## Etiketli doğruluk durumu

`dataset/test_labels.json` P001–P030 etiketlerini içeriyor, fakat çalışma alanında
bu stemlere sahip görsel sayısı **0/30**. Önceki `accuracy_results.json` da repoda
ve git geçmişinde yok. Bu nedenle gerçek `GENEL DOGRULUK`, kolay ve kandırmaca
yüzdeleri **BULUNAMADI**; sayı uydurulmadı.

Etiketli set sağlandığında gerçek yeniden üretim komutu:

```powershell
& 'O:\navitas-local-train\venv\Scripts\python.exe' -B codes/test_accuracy.py --test '<P001-P030 klasoru>' --labels 'O:\navitas\dataset\test_labels.json' --model 'O:\navitas\models\navitas_seg_v20_best.pt' --conf 0.25
```

## Etiketsiz gerçek karelerde karar karşılaştırması — doğruluk değildir

Model iki tarafta da `models/navitas_seg_v20_best.pt`, eşik `0.25`, giriş yolu
letterbox'tır. “Önce” değerleri mevcut T1 ölçüm kaydındaki yerel karar kopyasından;
“sonra” değerleri T8 koduyla 4 Ağustos 2026'da aynı altı karede yeniden ölçüldü.

| Kare | Önce: yerel kopya | Sonra: üretim fonksiyonu | Karar değişti |
|---|---:|---:|---:|
| 11.44.48 | 2 / 0,457 | 2 / 0,452 | hayır |
| 11.44.50 (1) | 3 / 0,370 | 2 / 0,322 | **evet** |
| 11.44.50 (2) | 2 / 0,378 | 2 / 0,373 | hayır |
| 11.44.50 | 3 / 0,353 | 2 / 0,294 | **evet** |
| 11.44.51 (1) | 2 / 0,362 | 2 / 0,370 | hayır |
| 11.44.51 | 2 / 0,352 | 2 / 0,335 | hayır |

| Metrik | Önce | Sonra |
|---|---:|---:|
| İncelenen etiketsiz kare | 6 | 6 |
| Kararı değişen kare | — | 2/6 |
| Etiketli doğruluk | **BULUNAMADI** | **BULUNAMADI** |

## Deterministik karar regresyonu

Üç sahnenin beklenen davranışı üretim sözleşmesinden gelir: ana bağlı orta
koridor `2`, alan eşiği altındaki gürültü `None`, iki kollu tek bileşenin üst-band
centroid'i `2`.

| Sahne | Önce: yerel üç-bölge kopyası | Sonra: üretim fonksiyonu | Beklenen |
|---|---:|---:|---:|
| Orta koridor + sol kopuk gürültü | 1 | 2 | 2 |
| Yalnız küçük gürültü (~%0,3) | 1 | `None` | `None` |
| İki kollu tek bağlı bileşen | 3 | 2 | 2 |
| **Beklenen kararla uyum** | **0/3** | **3/3** | **3/3** |

Bu tablo model doğruluğu değildir; ölçüm kodunun üretim karar sözleşmesiyle yeniden
aynı davranışı verdiğinin deterministik kanıtıdır.
