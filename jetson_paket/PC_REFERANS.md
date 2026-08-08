# Jetson Uctan Uca FPS Olcumu

NEDEN: Sayilar kare okuma + cikarim + get_masks + costmap Katman A yolunun gercek olcumudur.

Ortam: `Windows-11-10.0.26200-SP0`; Python `3.13.7`; CUDA `NVIDIA GeForce RTX 5080 Laptop GPU`.

| Model | imgsz | Ornek | Toplam p50 ms | Toplam p95 ms | Ortalama FPS | Durum |
|---|---:|---:|---:|---:|---:|---|
| PyTorch | 640 | 60 | 27.380 | 42.987 | 34.036 | OK |
| ONNX | 640 | 60 | 29.230 | 45.417 | 32.092 | OK |
| TensorRT FP16 | 640 | - | - | - | - | ATLANDI: model_dosyasi_yok |

Not: mpp=None olceksiz Katman-A performans kipidir; gercek mpp rota geometrisini degistirir.
TensorRT satiri yalniz Jetson'da derlenmis FP16 .engine ile gecerlidir.
