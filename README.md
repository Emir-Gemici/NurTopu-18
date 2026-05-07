# Navitas Autonomous Systems — TEKNOFEST 2026

**İleri Otonom Sistemler Tasarım ve Operasyon Yarışması**

---

## Sistem Mimarisi

```
İHA (UAV)                    İKA (UGV)                  Yer İstasyonu
─────────────────────        ─────────────────────        ─────────────
NVIDIA Jetson Orin NX        Raspberry Pi 5               Laptop
Geniş açı kamera             Pi Kamera                    MAVLink
YOLOv8-seg / NCNN            A* Path Planning             Telemetri
MAVLink TX (915MHz RF)       PID Motor Kontrolü           Monitör
Paraşüt sistemi              GNSS + IMU + Encoder
```

### Görev Senaryosu

```
İHA fırlatılır → 50×50m moloz alanı üzerinden geçer → 3 yoldan 1'i açık, 2'si kapalı
→ açık yolu tespit et → koordinatları İKA'ya gönder
→ İKA moloz alanında otonom navigate eder → hedefe ulaşır
```

---

## Dizin Yapısı

```
teknofest/
├── codes/
│   ├── rpi_inference.py        ← ANA KOD — inference, IKA haritası, RPi deployment
│   ├── test_accuracy.py        ← Görsel test & doğruluk (image/video/camera/--test)
│   ├── train_seg.py            ← YOLOv8-seg eğitim scripti
│   ├── image-test/             ← Test görselleri (gpt-images/, banana-images/)
│   │   ├── gpt-images/
│   │   └── banana-images/
│   └── requirements_rpi.txt    ← RPi kurulum bağımlılıkları
│
├── models/
│   └── rescuenet_seg_v1_ncnn_model/   ← Aktif NCNN modeli (RPi deployment)
│       ├── model.ncnn.bin
│       ├── model.ncnn.param
│       └── metadata.yaml
│
├── dataset/
│   ├── combined_data.yaml           ← Birleşik eğitim config (RescueNet + FloodNet)
│   ├── download_and_convert.py      ← RescueNet indir + YOLO formatına dönüştür
│   ├── convert_floodnet.py          ← FloodNet manuel dönüştürücü
│   ├── augment_dataset.py           ← Dataset augmentasyonu (flip, rotate, renk)
│   ├── merge_datasets.py            ← Birden fazla dataset'i birleştir
│   ├── prompts_training.txt         ← 50 eğitici görsel üretim promptu (E001-E050)
│   ├── prompts_tricky.txt           ← 50 hileli görsel üretim promptu (H001-H050)
│   ├── test_labels.json             ← Eski 30 prompt etiketleri (P001-P030)
│   ├── test_labels_training.json    ← E001-E050 etiketleri
│   └── test_labels_tricky.json      ← H001-H050 etiketleri
│
└── doc/
    └── model_analiz.md
```

> **Gitignore'da olanlar (büyük, yeniden üretilebilir):**
> `dataset/rescuenet_yolo/`, `dataset/floodnet_yolo/`, `dataset/floodnet_filtered/`,
> `dataset/rescuenet_yolo_aug/`, `codes/results/`, `runs/`, `models/*.pt`

---

## Kurulum

### Gereksinimler

```
Python 3.10+
```

```bash
pip install ultralytics opencv-python numpy tqdm datasets
```

> **Not:** `datasets` paketi sadece HuggingFace'den otomatik indirme için gerekli.
> Eğer dataset'leri manuel indirdiysen gerekmez.

### Wayland (Fedora) — kamera/video görüntüsü için

```bash
QT_QPA_PLATFORM=xcb python3 codes/rpi_inference.py --camera
```

---

## Hızlı Başlangıç

### Laptop'ta test

```bash
# Tek görsel
python3 codes/rpi_inference.py --image codes/images/4.jpg

# Klasördeki tüm görseller
python3 codes/rpi_inference.py --image codes/images/

# Video
python3 codes/rpi_inference.py --video video.mp4

# Canlı kamera
QT_QPA_PLATFORM=xcb python3 codes/rpi_inference.py --camera

# FPS ölçümü
python3 codes/rpi_inference.py --fps
```

Çıktılar `codes/results/` altına yazar:
- `*_result.jpg` — orijinal çözünürlükte, yeşil (traversable) + kırmızı (blocked) maske + centerline
- `*_ika_map.jpg` — İKA navigasyon haritası (waypoint koordinatları, hedef noktası)

### RPi'ye deploy

```bash
# Laptop'ta: gerekli dosyaları bir araya getir
mkdir -p navitas
cp codes/rpi_inference.py navitas/
cp -r models/rescuenet_seg_v1_ncnn_model navitas/

# RPi'ye gönder
scp -r navitas/ pi@<RPI_IP>:~/
scp codes/requirements_rpi.txt pi@<RPI_IP>:~/navitas/

# RPi'de
pip install -r requirements_rpi.txt
python3 rpi_inference.py --fps      # hedef: ≥10 FPS
python3 rpi_inference.py --camera
```

---

## Veri Seti

### Mevcut Kaynaklar

| Dataset | Görsel (train) | Kaynak |
|---------|---------------|--------|
| RescueNet-Roads | 2.365 | `asolodin/rescuenet-roads` (HuggingFace) |
| FloodNet Supervised v1.0 | 798 (filtered) | Manuel indirme |
| **Birleşik (combined)** | **3.163** | combined_data.yaml |

### Dataset İndirme / Hazırlama

```bash
# RescueNet (otomatik)
python3 dataset/download_and_convert.py

# FloodNet (manuel indirildikten sonra)
# 1. https://github.com/BinaLab/FloodNet-Supervised_v1.0 → Google Drive'dan indir
python3 dataset/convert_floodnet.py --src ~/Downloads/FloodNet/FloodNet-Supervised_v1.0

# Hangi dataset'ler hazır?
python3 dataset/merge_datasets.py --check

# Augmentasyon (mevcut dataset'i genişlet)
python3 dataset/augment_dataset.py --factor 4   # 2365 → ~11.825 görsel
```

---

## Eğitim

```bash
# Varsayılan (RescueNet + FloodNet, 150 epoch)
python3 codes/train_seg.py

# Seçenekler
python3 codes/train_seg.py --data dataset/rescuenet_yolo/data.yaml   # tek dataset
python3 codes/train_seg.py --model yolov8s-seg.pt                    # daha büyük model
python3 codes/train_seg.py --epochs 200 --no-export                  # export yapma
```

Eğitim bittikten sonra NCNN export otomatik yapılır, `models/navitas_seg_v2_ncnn_model/` altına kopyalanır.

### Eğitim Ayarları (Özet)

| Parametre | Değer | Neden |
|-----------|-------|-------|
| Model | YOLOv8n-seg | RPi'de ≥10 FPS |
| imgsz | 512 | Hız/doğruluk dengesi |
| epochs | 150 (patience=40) | CPU için yeterli |
| degrees | 45° | Hava fotoğrafı her açıdan gelir |
| hsv_v | 0.5 | Gölgeli görsel challengeine karşı |
| copy_paste | 0.15 | Nadir sınıf (blocked) için |
| cos_lr | True | Daha iyi convergence |

---

## Model

| Parametre | Değer |
|-----------|-------|
| Mimari | YOLOv8n-seg |
| Sınıflar | `traversable` (0), `blocked` (1) |
| Export | NCNN (RPi 5 için optimize) |
| Hedef FPS | ≥10 FPS (RPi 5, NCNN) |

### Algoritma

```
Girdi → merkezi kare crop → 512×512 inference
      → mask upscale (orijinal çözünürlüğe)
      → morphological clean
      → distance transform centerline
      → üst %40'ta hangi üçte birde daha fazla traversable px → open_path (1/2/3)
      → waypoint örnekleme (alt→üst, 8 nokta)
      → *_result.jpg  (görsel çıktı)
      → *_ika_map.jpg (navigasyon haritası)
      → JSON payload  (terminal)
```

### İKA Payload Formatı

```python
{
    "open_path": 2,            # 1=sol, 2=orta, 3=sag
    "confidence": 0.87,
    "waypoints": [[x,y], ...], # görüntü koordinatları, alt→üst
    "timestamp": 1234567890
}
```

---

## Model Doğruluk Testi

```bash
# Görsel klasörü test et (--test: doğruluk karşılaştırması + görsel çıktı)
python3 codes/test_accuracy.py --test codes/image-test/gpt-images/

# Tek görsel veya klasör
python3 codes/test_accuracy.py --image codes/image-test/gpt-images/

# Video
python3 codes/test_accuracy.py --video video.mp4

# Kamera
QT_QPA_PLATFORM=xcb python3 codes/test_accuracy.py --camera
```

Çıktılar `codes/test_results/` altına yazar.

### Prompt Setleri

| Dosya | Adet | Açıklama |
|-------|------|----------|
| `prompts_training.txt` | 50 (E001–E050) | Net görseller, sol/orta/sağ dengeli |
| `prompts_tricky.txt` | 50 (H001–H050) | Gölge, yan bakış, gece, bozuk yüzey |
| `test_prompts.txt` | 30 (P001–P030) | Eski set |

Her promptta **GPT** ve **nano-banana** formatları ayrı ayrı yazılmıştır.

---

## Haberleşme

- Protokol: MAVLink over UDP
- Frekans: 915 MHz RF modül
- Güncelleme süresi: ≤200ms
- Mesafe: 300m operasyon alanı

---

## Ekip

**Navitas Autonomous Systems** — TEKNOFEST 2026
