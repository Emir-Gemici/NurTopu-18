# Navitas v3 Test — Özet (yerel eğitim)
Tarih: 2026-07-12T03:00:58.207431
Model SHA-256: 8e8d46a6fc32b20c65c64234066c696c529ba9df7a62eba756a07fef8b9e43e5
Ortam: NVIDIA GeForce RTX 5080 Laptop GPU · ultralytics 8.4.92 · torch 2.11.0+cu128

## Kıyas (aynı 294 RescueNet val)
| Model | mask mAP50 | traversable | blocked |
|---|---|---|---|
| v1 (rescuenet_seg_v1) | 0.619 | 0.874 | 0.363 |
| v2 (navitas_seg_v2) | 0.595 | 0.868 | 0.322 |
| v3 (navitas_seg_v3) ⭐ | 0.6273 | 0.8521 | 0.4026 |

HEDEF ≥ 0,60 → v3 = 0.6273 → GEÇTİ

Dosyalar: konsol.log · ortam.json · v3_model_kimlik.json · v3_val_sonuclari.json ·
kiyas.json · v3_val/ (confusion, PR eğrileri, örnek kareler)
