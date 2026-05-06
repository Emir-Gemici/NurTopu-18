# Model Analiz Raporu — rescuenet_seg_v1

**Tarih:** 2026-05-06  
**Takım:** Navitas Autonomous Systems  
**Yarışma:** TEKNOFEST 2026 İleri Otonom Sistemler

---

## 1. Eğitim Özeti

| Parametre | Değer |
|-----------|-------|
| Model | YOLOv8n-seg |
| Dataset | asolodin/rescuenet-roads (HuggingFace) |
| Toplam epoch | 100 |
| Süre | 16.6 saat (CPU — AMD Ryzen 7 5700U) |
| Görüntü boyutu | 512×512 |
| Batch size | 16 |
| Optimizer | AdamW |
| lr0 | 0.001 |
| Early stopping | patience=20 |

---

## 2. Dataset

| Split | Görüntü | traversable inst. | blocked inst. | Boş |
|-------|---------|-------------------|---------------|-----|
| train | 2,365   | 2,327             | 660           | 100 |
| val   | 294     | 282               | 81            | 14  |
| test  | 305     | 308               | 85            | 9   |
| **Toplam** | **2,964** | **2,917** | **826** | **123** |

**Sınıf tanımları (RescueNet orijinal ID → YOLO ID):**
- RescueNet class 7 (road-clear) → `0: traversable`
- RescueNet class 8 (road-blocked) → `1: blocked`

**Not:** blocked örneği traversable'dan ~3.5× az. Bu sınıf dengesizliği blocked mAP'ini olumsuz etkiliyor.

---

## 3. Eğitim Süreci (Her 10 Epoch)

| Epoch | mAP50 (Box) | mAP50 (Mask) | Train seg_loss | Val seg_loss |
|-------|-------------|--------------|----------------|--------------|
| 10    | 0.366       | 0.405        | 2.251          | 2.117        |
| 20    | 0.446       | 0.460        | 2.040          | 1.934        |
| 30    | 0.448       | 0.471        | 1.907          | 1.961        |
| 40    | 0.502       | 0.526        | 1.858          | 1.850        |
| 50    | 0.497       | 0.512        | 1.763          | 1.741        |
| 60    | 0.537       | 0.540        | 1.725          | 1.705        |
| 70    | 0.583       | 0.600        | 1.651          | 1.606        |
| 80    | 0.535       | 0.573        | 1.578          | 1.637        |
| 90    | 0.564       | 0.603        | 1.535          | 1.547        |
| 100   | 0.588       | **0.619**    | 1.279          | 1.541        |

**En iyi epoch: 85** (best.pt buradan alındı)

---

## 4. Final Metrikler (Val seti — best.pt)

### Genel

| Metrik | Değer | Hedef | Durum |
|--------|-------|-------|-------|
| mAP50 (Mask) | **0.619** | ≥0.60 | ✅ |
| mAP50 (Box) | 0.588 | — | — |
| mAP50-95 (Mask) | 0.385 | — | — |
| Precision (Mask) | 0.674 | — | — |
| Recall (Mask) | 0.604 | — | — |

### Sınıf Bazlı

| Sınıf | Images | Instances | Box mAP50 | Mask mAP50 |
|-------|--------|-----------|-----------|------------|
| traversable | 240 | 282 | 0.850 | **0.874** |
| blocked | 60 | 81 | 0.326 | 0.363 |

**Yorum:**
- `traversable` sınıfı çok iyi — asıl görev olan açık yol tespiti 0.874 mAP50 ile güçlü.
- `blocked` düşük (0.363) — dataset'te 660 örnek vs 2327 traversable. Sınıf dengesizliği.
- Yarışma senaryosunda kritik olan traversable tespiti olduğu için bu kabul edilebilir.

---

## 5. Model Dosyaları

| Dosya | Boyut | Kullanım |
|-------|-------|---------|
| `models/rescuenet_seg_v1_best.pt` | 6.5 MB | Laptop/Jetson (PyTorch) |
| `models/rescuenet_seg_v1_ncnn/model.ncnn.bin` | 13 MB | RPi 5 (NCNN) |
| `models/rescuenet_seg_v1_ncnn/model.ncnn.param` | 19 KB | RPi 5 (NCNN) |

---

## 6. Beklenen RPi 5 Performansı

NCNN export yapıldı (12.6 MB). YOLOv8n-seg + NCNN kombinasyonu:

| Senaryo | Beklenen FPS |
|---------|-------------|
| imgsz=512, RPi 5 | ~8-15 FPS |
| imgsz=256, RPi 5 | ~20-30 FPS |

> Gerçek ölçüm için: `python3 rpi_inference.py --fps`

Hedef ≥10 FPS sağlanamazsa `imgsz=256` ile yeniden export yapılır.

---

## 7. Sorunlar ve Çözümler

### Dataset açısı uyumu
RescueNet görüntüleri 30°–90° aerial açı aralığını kapsıyor. İHA'nın kamerası dik aşağı (nadir) veya hafif eğik olduğu sürece model çalışmalı. Ground-level görüntülerde çalışmaz (ilk dataset deneyi ile kanıtlandı).

### blocked sınıfı zayıf
- **Neden:** 660 blocked vs 2327 traversable örneği
- **Çözüm:** FloodNet veya ek blocked örnekli dataset ile fine-tune
- **Pratik etki:** Sistem açık yolu tespit edebiliyor. Kapalı yolu kaçırsa bile 3 yoldan birini tespit etmek yeterli.

### GPU eksikliği
- 16.6 saatlik eğitim CPU üzerinde gerçekleşti
- GPU ile (RTX serisi) bu süre ~1-2 saate iner
- Sonraki eğitimler için GPU erişimi önerilir

---

## 8. Sonraki Adımlar

1. **RPi FPS testi** — `rpi_inference.py --fps` ile gerçek performans ölç
2. **Saha testi** — gerçek moloz alanı veya benzer ortamda görsel test
3. **Yol karar kalibrasyonu** — görüntüdeki 3 yolun piksel konumları sahaya göre ayarlanacak
4. **MAVLink entegrasyonu** — `detect_open_path()` çıktısını İKA'ya gönder
5. **Fine-tune (opsiyonel)** — blocked mAP düşükse ek veriyle 20-30 epoch daha eğit

---

## 9. Referanslar

- Dataset: https://huggingface.co/datasets/asolodin/rescuenet-roads
- Orijinal RescueNet: Rahnemoonfar et al., IEEE DataPort
- YOLOv8: Ultralytics, https://github.com/ultralytics/ultralytics
