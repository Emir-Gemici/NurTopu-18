# Navitas v3 — Sınıf Bazlı Metrikler

Model: navitas_seg_v3_best.pt (YOLOv8s-seg)
Test seti: RescueNet val — 294 görüntü, 363 nesne (traversable 282, blocked 81)
Ölçüm: Ultralytics val (standart), RTX 5080, ultralytics 8.4.92
Kaynak: results/v3_test_20260712/konsol.log (satır 38501-38503), v3_val_sonuclari.json

## Segmentasyon (Mask) — asıl değerler

| Sınıf | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|
| traversable | 0,833 | 0,795 | 0,852 | 0,544 |
| blocked | 0,458 | 0,444 | 0,403 | 0,263 |
| Genel (all) | 0,645 | 0,620 | 0,627 | 0,404 |

## Tespit (Box)

| Sınıf | Precision | Recall | mAP@50 | mAP@50-95 |
|---|---|---|---|---|
| traversable | 0,822 | 0,784 | 0,833 | 0,643 |
| blocked | 0,471 | 0,457 | 0,459 | 0,294 |
| Genel (all) | 0,646 | 0,621 | 0,646 | 0,468 |

Hedef: mask mAP@50 ≥ 0,60 → 0,627 → geçildi.

## Görsel kanıtlar (aynı klasör, v3_val/)
- confusion_matrix.png / confusion_matrix_normalized.png (precision/recall'ın görsel hâli)
- MaskPR_curve.png, MaskP_curve.png, MaskR_curve.png (precision & recall eğrileri)
- val_batch*_pred.jpg (örnek tahminler)
