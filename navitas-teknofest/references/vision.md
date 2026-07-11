# Vision / ML Referans

## Model Durumu
- **Model**: YOLOv8-seg nano
- **Veri**: RescueNet (2365 train / 294 val)
- **Export**: NCNN ✓ — 27.6 FPS lokal
- **Zayıf alanlar**: dar/kırsal yollar, non-asphalt, gölge, açık alan FP

---

## Fine-tuning Stratejisi

### Öncelik Sırası (zayıf alanlara göre)
1. **Gölgeli yollar** → HSV augmentation (brightness/contrast jitter)
2. **Dar yollar** → mosaic + random crop (küçük obje görünürlüğü)
3. **Non-asphalt** → domain-specific veri toplama veya synthetic augment
4. **Açık alan FP** → negative sampling (yol olmayan açık alan görselleri)

### Augmentation Config (ultralytics)
```yaml
# data.yaml augmentations
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4         # gölge için artır (0.6+)
degrees: 10
translate: 0.1
scale: 0.5
flipud: 0.0
fliplr: 0.5
mosaic: 1.0
mixup: 0.1
copy_paste: 0.1    # küçük obje için etkili
```

### Fine-tune Komutu
```bash
yolo segment train \
  model=yolov8n-seg.pt \
  data=rescuenet_navitas.yaml \
  epochs=50 \
  imgsz=640 \
  batch=16 \
  lr0=0.001 \
  freeze=10 \         # backbone'u dondur, head'i eğit
  patience=20
```

---

## NCNN Export & Optimizasyon

```bash
# Export
yolo export model=best.pt format=ncnn imgsz=640

# RPi 5'te inference test
python3 inference_ncnn.py --model best_ncnn --img test.jpg --conf 0.35
```

### Confidence Threshold Tuning
Açık alan FP için önce threshold'u artır:
```python
conf_threshold = 0.40   # default 0.25 → önce bunu dene
iou_threshold  = 0.45
```

False negative artarsa veri topla; threshold tek başına yetmiyorsa negative sampling yap.

---

## Metrik Hedefleri

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| mAP50 (yol) | — | >0.75 |
| FPS @ RPi 5 (NCNN) | 27.6 | >25 (kabul) |
| Dar yol recall | zayıf | >0.65 |
| Açık alan precision | zayıf | >0.80 |
