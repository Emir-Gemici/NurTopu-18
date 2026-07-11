# Model Test Planı

## Aşama 0 — Kimlik

Test öncesi beklenen hashler doğrulanmalı. Test komutunda açıkça `models/navitas_seg_v2_best.pt` veya `models/navitas_seg_v2_ncnn_model` verilmelidir; `best_ncnn_model` kullanılmamalıdır.

## Aşama 1 — Smoke ve model özeti

İzole `.venv` kullanılarak model sınıfları, task, input ve ilk tek görsel inference doğrulanır. Çıktılar ayrı tarihli dizine yazılır. Bu aşama accuracy değildir.

## Aşama 2 — Mevcut 14 görsel nitel testi

PT ve NCNN aynı görüntüler ve aynı preprocessing/conf değerleriyle çalıştırılır. Yol kararı, geometrik güven, traversable/blocked alanı, latency ve mask IoU karşılaştırılır. Label olmadığı için yalnız gözlem/parity raporu üretilir.

## Aşama 3 — Etiketli görev testi

Dosyalar P/E/H/TA kimlikleriyle eşleştirilir veya label JSON'a gerçek stem eklenir. Değişiklikten önce görsel ile prompt/etiket insan tarafından doğrulanır. Accuracy, “yok” oranı, yol confusion matrix ve koşul bazlı sonuç hesaplanır.

## Aşama 4 — Segmentasyon validation

V2 eğitimindeki tam dataset sürümü yeniden kurulup `.pt` üzerinde Ultralytics `val` çalıştırılır. Ardından NCNN destekliyorsa aynı set parity/test edilir. V1 ve v2 aynı split üzerinde karşılaştırılır.

## Aşama 5 — E2E

Gizli sim seed'i; kamera taraması; mozaik; gerçek model; OPEN_ROUTE; İKA'nın gönderilmiş waypoint'leri; skorlayıcı ground-truth. En az 30 bağımsız seed ve kolay/orta/zor katmanı önerilir. Başarı oranı için Wilson güven aralığı raporlanmalıdır.

## Başarı kapıları

- Model kimliği/hash uyumlu.
- PT–NCNN yol kararı eşitliği >= %99, mask IoU eşiği önceden belirlenmiş.
- Bağımsız görev setinde açık-yol doğruluğu hedefi ve “tespit yok” üst sınırı ayrı.
- Blocked sınıfı için güvenlik eşiği.
- RPi/Jetson p95 latency ve 15+ dakika termal kararlılık.
- E2E testte hiçbir ground-truth verisi algı/navigasyon prosesine aktarılmıyor.

Model çalıştırma, sonuç yazma ve gerekirse dataset indirme ayrı izinle yapılmalıdır.
