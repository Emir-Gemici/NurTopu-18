# Model Adli Analizi

## Kimlikler ve hashler

| Artefakt | SHA-256 | Yorum |
|---|---|---|
| `models/navitas_seg_v2_best.pt` | `c7ce71...9d2d0c` | Güncel v2 PT |
| `navitas_model/navitas_seg_v2_best.pt` | aynı | Birebir kopya |
| `models/navitas_seg_v2_ncnn_model/model.ncnn.bin` | `16a397...2a7f` | Güncel v2 NCNN |
| `navitas_model/.../model.ncnn.bin` | aynı | Birebir kopya |
| `models/rescuenet_seg_v1_ncnn_model/model.ncnn.bin` | `ecba18...997ae` | V1 |
| `models/best_ncnn_model/model.ncnn.bin` | `dec3ff...f51` | Ayrı/eski ağırlık; v2 değil |

Üç NCNN modelinin `.param` dosyası aynıdır; mimari aynı, ağırlıklar farklıdır. Param yapısı 228 layer/272 blob; 76 convolution, 65 Swish, 23 Split, 19 Concat, 12 Reshape, 12 BinaryOp ve segmentasyon başına uygun deconvolution/interpolation içerir. Metadata 2 sınıf, stride 32, batch 1, 3 kanal ve 512×512 girdi gösterir.

V2 metadata: Ultralytics 8.4.76, export tarihi 24 Haziran 2026. PT ve NCNN aynı committe eklenmiştir; ancak sayısal parity raporu yoktur. Aynı committe bulunmaları aynı çıktıyı verdiklerini kanıtlamaz.

## Eğitim provenance sorunu

V2 notebook'unda 19 hücre vardır fakat hiçbir execution count veya output bulunmaz. Eğitim CSV'si, args.yaml, confusion matrix, PR eğrileri, validation sonuçları ve environment lock depoda değildir. Notebook eğitim sonunda `glob(...best.pt)` sonuçlarını sıralayıp `hits[0]` kopyalar; birden fazla run varsa ilk alfabetik checkpoint'in yanlış seçilmesi mümkündür. Run adı/commit/dataset hash bağlama yoktur.

`navitas_model/best/` dizini bir PyTorch zip arşivinin açılmış içeriğine benzer ve pickle taşır. Güvenilmeyen `.pt` dosyaları kod çalıştırabilecek pickle içerebildiği için yalnız güvenilir kaynaktan, izole ortamda yüklenmelidir.

## Metrik ayrımı

Depoda kanıtlanabilen mAP raporu v1 içindir: mask mAP50 0.619, traversable 0.874, blocked 0.363, precision 0.674, recall 0.604. V2 DDR metni açıkça “v2 metrikleri FDR'de raporlanacaktır” der. Buna rağmen sim logları v2 model adıyla v1 metriklerini yan yana basmaktadır. Bu yanlış ilişkilendirme düzeltilmelidir.

## Lisans

NCNN metadata dosyası Ultralytics AGPL-3.0 lisansını belirtir. Yarışma demosu için çoğu durumda sorun olmayabilir; ancak kapalı kaynak veya ticari dağıtım düşünülürse Ultralytics lisans koşulları ayrıca hukuk/uyum incelemesine alınmalıdır.
