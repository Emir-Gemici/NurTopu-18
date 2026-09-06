# Jetson Uctan Uca FPS Olcumu

NEDEN: Sayilar kare okuma + cikarim + get_masks + costmap Katman A yolunun gercek olcumudur.

Ortam: `Linux-6.8.12-1021-tegra-aarch64-with-glibc2.39`; Python `3.12.3`; CUDA `Orin`.

| Model | imgsz | Ornek | Toplam p50 ms | Toplam p95 ms | Ortalama FPS | Durum |
|---|---:|---:|---:|---:|---:|---|
| PyTorch | 512 | 900 | 770.359 | 922.020 | 1.320 | OK |
| ONNX | 512 | - | - | - | - | ATLANDI: model_dosyasi_yok |
| TensorRT FP16 | 512 | 900 | 649.338 | 765.287 | 1.576 | OK |

Not: mpp=None olceksiz Katman-A performans kipidir; gercek mpp rota geometrisini degistirir.
TensorRT satiri yalniz Jetson'da derlenmis FP16 .engine ile gecerlidir.
