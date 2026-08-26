# Jetson Uctan Uca FPS Olcumu

NEDEN: Sayilar kare okuma + cikarim + get_masks + costmap Katman A yolunun gercek olcumudur.

Ortam: `Windows-11-10.0.26200-SP0`; Python `3.13.7`; CUDA `NVIDIA GeForce RTX 5080 Laptop GPU`.

| Model | imgsz | Ornek | Toplam p50 ms | Toplam p95 ms | Ortalama FPS | Durum |
|---|---:|---:|---:|---:|---:|---|
| PyTorch | 640 | 3 | 84.535 | 93.574 | 11.961 | OK |
| PyTorch | 512 | 3 | 66.240 | 66.726 | 15.116 | OK |
| ONNX | 640 | - | - | - | - | HATA: isinma/yukleme: No module named 'onnxruntime' |
| ONNX | 512 | - | - | - | - | HATA: isinma/yukleme: No module named 'onnxruntime' |
| TensorRT FP16 | 640 | - | - | - | - | ATLANDI: model_dosyasi_yok |
| TensorRT FP16 | 512 | - | - | - | - | ATLANDI: model_dosyasi_yok |

Not: mpp=None olceksiz Katman-A performans kipidir; gercek mpp rota geometrisini degistirir.
TensorRT satiri yalniz Jetson'da derlenmis FP16 .engine ile gecerlidir.
