# Test Metodolojisi Denetimi

## Mevcut testlerin anlamı

`test_batch.py` “detection rate” ölçer: traversable veya blocked maskesi görüntünün %1'inden fazlaysa detected sayar. Ground truth ile karşılaştırmadığı için doğruluk değildir. Yanlış maske de başarı sayılır.

`test_accuracy.py` beklenen açık yol ile post-processing yol kararını karşılaştırır; bu görev-level classification accuracy olabilir. Fakat isim eşleşmezliği nedeniyle mevcut görsellerde sonuç üretmez, varsayılan v1 modeldir, güncel inference pipeline'ını kullanmaz ve her görseli iki kez çalıştırır.

`rpi_inference --fps` sentetik sıfır görüntü üzerinde warm-up ve runtime ölçümü yapar; gerçek görüntü, preprocessing, termal throttling ve uzun süreli performans ayrıca ölçülmelidir.

## Mevcut video artefaktları

| Video | İşlenen kare | Sol | Orta | Sağ | Yok | Süre |
|---|---:|---:|---:|---:|---:|---:|
| 0_05_48... | 10.447 | 258 | 616 | 637 | 8.936 | 6.305,5 sn |
| WhatsApp 2.23 | 69 | 19 | 9 | 21 | 20 | 38,4 sn |
| WhatsApp 4.56 | 9.532 | 867 | 3.143 | 2.381 | 3.141 | 4.663,5 sn |

İlk videonun ortalama işlem süresi yaklaşık 604 ms/kare (1,65 FPS), üçüncünün 489 ms/kare (2,04 FPS)'dir; bunlar mevcut makine/ayar koşularıdır, RPi veya Jetson benchmark'ı değildir. Yüksek geometrik güvene rağmen karar dağılımının değişken olması `confidence` değerinin doğruluk olasılığı olmadığını gösterir.

## Geçerli ölçüm paketi

1. Dondurulmuş bağımsız segmentasyon test seti: mask mAP50/mAP50-95, precision, recall, IoU ve sınıf bazlı confusion.
2. Dondurulmuş görev test seti: her sahne için açık yol ground truth; accuracy, macro-F1, confusion matrix ve “tespit yok”.
3. Koşul katmanları: aydınlık/karanlık, gölge, irtifa, yaw/pitch, blur, yağmur, sentetik/gerçek.
4. Confidence sweep: detection threshold ve karar kabul eşiğini ayrı tarama.
5. PT–NCNN parity: aynı preprocessed tensor, mask IoU ve yol karar eşitliği.
6. Uzun süre benchmark: warm-up sonrası p50/p95/p99 latency, FPS, RAM, sıcaklık ve throttling.
7. Tek resmi E2E: saha seed'i algı sürecinden saklı; rota yalnız model mozaiğinden; İKA OPEN_ROUTE waypoint'lerini gerçekten tüketir; ground-truth sadece skorlayıcıda.
