# Jetson Uctan Uca FPS Olcumu

NEDEN: Sayilar kare okuma + cikarim + get_masks + costmap Katman A yolunun gercek olcumudur.

Ortam: `Linux-6.8.12-1021-tegra-aarch64-with-glibc2.39`; Python `3.12.3`; CUDA `Orin`.

| Model | imgsz | Ornek | Toplam p50 ms | Toplam p95 ms | Ortalama FPS | Durum |
|---|---:|---:|---:|---:|---:|---|
| PyTorch | 512 | 120 | 739.076 | 942.150 | 1.361 | OK |
| ONNX | 512 | - | - | - | - | HATA: isinma/yukleme: Error in execution: Non-zero status code returned while running QuickGelu node. Name:'/model.0/act/Mul/QuickGeluFusion/' Status Message: CUDA error cudaErrorNoKernelImageForDevice:no kernel image is available for execution on the device |
| TensorRT FP16 | 512 | 120 | 634.722 | 751.405 | 1.621 | OK |

Not: mpp=None olceksiz Katman-A performans kipidir; gercek mpp rota geometrisini degistirir.
TensorRT satiri yalniz Jetson'da derlenmis FP16 .engine ile gecerlidir.
