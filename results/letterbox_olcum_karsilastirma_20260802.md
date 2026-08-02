# Letterbox Öncesi / Sonrası Ölçüm Karşılaştırması

Bu kayıt, `codes/test_accuracy.py` ölçüm yolundaki merkezi crop düzeltmesinin
kanıtıdır. Model: `models/navitas_seg_v20_best.pt`, eşik: `0.25`, karar
fonksiyonu: betikteki mevcut `analyze_path`.

## Doğruluk durumu

`dataset/test_labels.json` içindeki P001–P030 etiketlerine karşılık gelen
görseller depoda bulunmadığından **etiketli doğruluk yüzdesi hesaplanamaz**.
Bu nedenle aşağıdaki tabloya doğruluk adı verilmez: altı ham, etiketsiz
1600×900 drone fotoğrafında aynı modelle eski crop ve yeni üretim-letterbox
çıktıları karşılaştırılmıştır. Etiketli P001–P030 seti sağlandığında aynı
komutla gerçek doğruluk tablosu yeniden üretilmelidir.

| Metrik | Eski merkezi crop | Yeni letterbox | Değişim |
|---|---:|---:|---:|
| Görünen kaynak alanı | %56,25 | %100,00 | +43,75 puan |
| İncelenen ham fotoğraf | 6 | 6 | — |
| Kararı değişen fotoğraf | — | 5/6 | Beklenen: tam görüş alanı |

| Ham fotoğraf | Eski tuval / karar (güven) | Yeni tuval / karar (güven) |
|---|---|---|
| 11.44.48 | 900×900 / sol (0,507) | 1600×1600 / orta (0,457) |
| 11.44.50 (1) | 900×900 / sol (0,448) | 1600×1600 / sağ (0,370) |
| 11.44.50 (2) | 900×900 / sol (0,360) | 1600×1600 / orta (0,378) |
| 11.44.50 | 900×900 / sol (0,493) | 1600×1600 / sağ (0,353) |
| 11.44.51 (1) | 900×900 / sol (0,394) | 1600×1600 / orta (0,362) |
| 11.44.51 | 900×900 / orta (0,383) | 1600×1600 / orta (0,352) |

NEDEN: 1600×900 kaynağın eski merkezi crop'u yalnız x=[350,1250] bandını
ölçüyordu; iki yandaki rota bilgisi doğruluk raporuna hiç girmiyordu. Yeni yol,
`rpi_inference._preprocess()` ve `_maskeleri_icerige_kirp()` ile üretim
çıkarımıyla aynı tam-genişlikli tuvali kullanır.
