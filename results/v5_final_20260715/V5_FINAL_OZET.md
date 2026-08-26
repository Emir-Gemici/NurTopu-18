# Navitas v5 GECE KOŞUSU — Final Özet
Tarih: 2026-07-15T07:53:06.677793
Kazanan: **v5a_s640** · SHA-256 3bff5c60aa47366b636981d170c958650132831f395cc1ac5ef94185d0bd8b80

| Model | mask mAP50 | traversable | blocked |
|---|---|---|---|
| v1 (512) | 0.619 | 0.874 | 0.363 |
| v2 (512) | 0.595 | 0.868 | 0.322 |
| v3 (512) | 0.627 | 0.852 | 0.403 |
| v5a_s640 @512 | 0.5643 | 0.8421 | 0.2865 |
| v5a_s640 @640 | 0.673 | 0.8576 | 0.4885 |
| v5a_s640 @640+TTA | 0.673 | 0.8576 | 0.4885 |
| v5b_s640_ft @512 | 0.5768 | 0.8259 | 0.3277 |
| v5b_s640_ft @640 | 0.66 | 0.8554 | 0.4646 |
| v5b_s640_ft @640+TTA | 0.66 | 0.8554 | 0.4646 |
| v5c_m640 @512 | 0.5748 | 0.821 | 0.3286 |
| v5c_m640 @640 | 0.6558 | 0.8503 | 0.4613 |
| v5c_m640 @640+TTA | 0.6558 | 0.8503 | 0.4613 |

Not: v1/v2/v3 referansları 512 ölçümüdür. TTA satırları saha modu adayıdır (çıkarım ~2×). Reçete farkları: A = pretrained ovs×2; B = v3'ten fine-tune ovs×3; C = yolov8m ovs×3; hepsi 640.
