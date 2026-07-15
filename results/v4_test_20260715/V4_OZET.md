# Navitas v4 (temiz 640) — Özet
Tarih: 2026-07-15T09:32:19.168648
SHA-256: 6b93f20024b9a9b6b774346ebba286e6088261aad014d7c64499940e2f618ec4
Reçete: v3 birebir + v3'ten fine-tune; tek fark 512→640.

| Model | mask mAP50 | traversable | blocked |
|---|---|---|---|
| v3 (512, referans) | 0.627 | 0.852 | 0.403 |
| v4 @640 (doğal) | 0.6751 | 0.8566 | 0.4937 |
| v4 @512 (kıyas) | 0.6072 | 0.8427 | 0.3716 |
| v4 @640+TTA | 0.6751 | 0.8566 | 0.4937 |
| v5 kazananı @640 (v5a_s640) | 0.673 | 0.8576 | 0.4885 |
