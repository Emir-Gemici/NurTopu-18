# Dataset ve Eğitim Analizi

## Veri iddiası

Birleşik YAML 3.163 train (2.365 RescueNet + 798 FloodNet), 551 validation ve RescueNet test split'i iddia eder. Ham/dönüştürülmüş datasetler gitignore'dadır ve bu çalışma kopyasında bulunmaz; sayımlar doğrudan doğrulanamamıştır.

RescueNet dönüşümü sınıf 7 road-clear -> 0 traversable ve sınıf 8 road-blocked -> 1 blocked eşlemesi yapar. V1 raporuna göre blocked örnek sayısı traversable'dan yaklaşık 3,5 kat düşüktür ve blocked mAP50 0.363'tür. Açık yol başarısına odaklanmak bu zayıflığı güvenli hale getirmez; kapalı yolu yanlışlıkla traversable görmek araç güvenliği açısından kritiktir.

FloodNet için birden fazla indirici/dönüştürücü bulunur ve `combined_data.yaml` `floodnet_filtered` beklerken Colab notebook `floodnet_yolo` yazar. Hangi dönüştürücü ve filtre sürümünün v2 eğitiminde kullanıldığı dataset manifesti/hash olmadığı için kesinleşmez.

## Eğitim ayarları

YOLOv8n-seg, 512, AdamW, lr0 0.001, cosine LR, 45 derece rotation, flip, scale 0.5, mosaic, HSV value 0.5, copy-paste 0.15 ve early stopping kullanılır. CPU script batch 8/device cpu; notebook bunu metin `sed` ile batch 16/device 0 yapar ve 100 epoch çalıştırır.

Riskler:

- Seed/deterministic ayarı açıkça kaydedilmemiştir.
- Paket sürümleri eğitim zamanında lock edilmemiştir.
- `perspective=0.0` iken saha görüntüsü perspektif/irtifa/kamera açısı değişimlerine açıktır.
- Copy-paste'in segmentasyon ve sınıf dengesine gerçek etkisi ablation ile gösterilmemiştir.
- Dataset/label kalite raporu, duplicate ve near-duplicate taraması yoktur.
- Test split bağımsız olsa bile model geliştirme kararlarında görülüp görülmediği kayıtlı değildir.

## Sentetik test etiketleri

JSON dengeleri genel olarak iyidir: P seti 30 ve her yol 10; eğitim seti 50; tricky seti 50; takım seti 30. Ancak depodaki 14 görselin stem'leri label kimlikleriyle eşleşmez. Sentetik görüntüler eğitim/validation metriklerinin yerine geçemez; görev-level robustness için ayrı bir challenge set olarak kullanılmalıdır.
