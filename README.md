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
navitas/
├── codes/
│   ├── rpi_inference.py        ← ANA KOD — inference, İKA haritası, RPi deployment
│   ├── test_accuracy.py        ← Görsel test & doğruluk (image/video/camera/--test)
│   ├── test_batch.py           ← Toplu test (roboflow/floodnet/rescuenet kaynakları)
│   ├── train_seg.py            ← YOLOv8-seg eğitim scripti
│   ├── download_roboflow.py    ← Roboflow test dataset'lerini indir (ROBOFLOW_API_KEY)
│   └── requirements_rpi.txt   ← RPi kurulum bağımlılıkları
│
├── models/
│   ├── best_ncnn_model/               ← En güncel model (aktif deployment)
│   │   ├── model.ncnn.bin
│   │   ├── model.ncnn.param
│   │   ├── metadata.yaml
│   │   └── model_ncnn.py
│   └── rescuenet_seg_v1_ncnn_model/   ← v1 referans modeli
│       ├── model.ncnn.bin
│       ├── model.ncnn.param
│       ├── metadata.yaml
│       └── model_ncnn.py
│
├── dataset/
│   ├── combined_data.yaml           ← Birleşik eğitim config (RescueNet + FloodNet)
│   ├── download_and_convert.py      ← RescueNet indir + YOLO formatına dönüştür
│   ├── download_floodnet.py         ← FloodNet indirme yardımcısı
│   ├── convert_floodnet.py          ← FloodNet → YOLO format dönüştürücü
│   ├── download_semantic_drone.py   ← Semantic Drone dataset
│   ├── download_extra_datasets.py   ← Ek dataset'ler
│   ├── augment_dataset.py           ← Dataset augmentasyonu (flip, rotate, renk)
│   ├── merge_datasets.py            ← Birden fazla dataset'i birleştir
│   ├── prompts_training.txt         ← 50 eğitici görsel üretim promptu (E001-E050)
│   ├── prompts_tricky.txt           ← 50 hileli görsel üretim promptu (H001-H050)
│   ├── test_labels.json             ← Eski 30 prompt etiketleri (P001-P030)
│   ├── test_labels_training.json    ← E001-E050 etiketleri
│   └── test_labels_tricky.json      ← H001-H050 etiketleri
│
├── simulation/                      ← Gazebo simülasyon ortamı
│   ├── worlds/                      ← .world dosyaları (kolay/orta/zor)
│   ├── models/                      ← Gazebo modelleri (iha, ika, catapult, debris)
│   ├── scripts/                     ← Simülasyon kontrol scriptleri
│   ├── launch/navitas.launch        ← ROS launch dosyası
│   ├── generate_world.py            ← Dinamik world oluşturucu
│   ├── score.py                     ← Şartname V2 puan hesaplayıcı
│   └── launch.sh                    ← Simülasyonu başlatma scripti
│
├── test_images/
│   └── gemini/                      ← 12 referans test görseli (Gemini üretimi)
│
└── doc/
    ├── model_analiz.md
    └── İleri_Otonom_Sistemler_...pdf
```

> **Gitignore'da olanlar (büyük / yeniden üretilebilir):**
> `FloodNet/` (13GB), `codes/results-zip.zip` (20GB), `test_images/roboflow/` (500MB+),
> `dataset/*_yolo/`, `codes/results/`, `runs/`, `models/*.pt`, `models/*.zip`

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

### Wayland (Fedora) — kamera/video görüntüsü için

```bash
QT_QPA_PLATFORM=xcb python3 codes/rpi_inference.py --camera
```

---

## Hızlı Başlangıç

### Laptop'ta test

```bash
# Tek görsel
python3 codes/rpi_inference.py --image test_images/gemini/1.png

# Klasördeki tüm görseller
python3 codes/rpi_inference.py --image test_images/gemini/

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
mkdir -p navitas_deploy
cp codes/rpi_inference.py navitas_deploy/
cp -r models/best_ncnn_model navitas_deploy/
cp codes/requirements_rpi.txt navitas_deploy/

# RPi'ye gönder
scp -r navitas_deploy/ pi@<RPI_IP>:~/

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
| **Birleşik (combined)** | **3.163** | `combined_data.yaml` |

### Dataset İndirme / Hazırlama

```bash
# RescueNet (otomatik)
python3 dataset/download_and_convert.py

# FloodNet (manuel indirildikten sonra)
# https://github.com/BinaLab/FloodNet-Supervised_v1.0 → Google Drive'dan indir
python3 dataset/convert_floodnet.py --src ~/Downloads/FloodNet/FloodNet-Supervised_v1.0

# Hangi dataset'ler hazır?
python3 dataset/merge_datasets.py --check

# Augmentasyon (mevcut dataset'i genişlet)
python3 dataset/augment_dataset.py --factor 4   # 2365 → ~11.825 görsel

# Roboflow test dataset'leri (API anahtarı gerekli)
export ROBOFLOW_API_KEY=<api_key>
python3 codes/download_roboflow.py
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

Eğitim bittikten sonra NCNN export otomatik yapılır, `models/best_ncnn_model/` altına kopyalanır.

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

## Toplu Test

```bash
# Tüm kaynakları test et
python3 codes/test_batch.py --all

# Belirli kaynak
python3 codes/test_batch.py --source roboflow
python3 codes/test_batch.py --source floodnet
python3 codes/test_batch.py --source rescuenet
```

---

## Simülasyon (Gazebo)

```bash
# Simülasyonu başlat (host'ta Gazebo Classic gerektirir)
cd simulation && bash launch.sh

# Puan hesapla (şartname V2)
python3 simulation/score.py
```

Simülasyon ortamı üç zorluk seviyesinde world dosyası içerir: kolay, orta, zor.

### Video kaydı (Podman — Gazebo kurulumu gerektirmez)

İHA + İKA görevini oynatıp **mp4 video** olarak kaydeder. Host'a Gazebo/ROS kurmaya
gerek yoktur; her şey Podman konteynerinde çalışır (Gazebo Classic 11 + sanal ekran +
ffmpeg). Ayrıntı: `simulation/docker/README.md`.

```bash
cd simulation
./docker/record.sh             # kolay, orta, zor → üç video
./docker/record.sh orta        # tek senaryo
```

Çıktı: `simulation/recordings/navitas_<senaryo>.mp4` (1280×720, ~45 sn).
Hareket, kinematik animasyon plugin'i (`simulation/plugins/navitas_anim.cc`) ile
sürülür — `world_generator.py --record` senaryoya göre trajectory üretir.

---

## Model Doğruluk Testi

```bash
# Görsel klasörü test et (--test: doğruluk karşılaştırması + görsel çıktı)
python3 codes/test_accuracy.py --test test_images/gemini/

# Tek görsel veya klasör
python3 codes/test_accuracy.py --image test_images/gemini/

# Kamera
QT_QPA_PLATFORM=xcb python3 codes/test_accuracy.py --camera
```

### Prompt Setleri

| Dosya | Adet | Açıklama |
|-------|------|----------|
| `prompts_training.txt` | 50 (E001–E050) | Net görseller, sol/orta/sağ dengeli |
| `prompts_tricky.txt` | 50 (H001–H050) | Gölge, yan bakış, gece, bozuk yüzey |
| `test_prompts.txt` | 30 (P001–P030) | Eski set |

---

## Haberleşme

- Protokol: MAVLink over UDP
- Frekans: 433 MHz RF modül (SiK; şartname bant belirtmez, BTK uyumlu)
- Güncelleme süresi: ≤200ms
- Mesaje: 300m operasyon alanı

---

## Ekip

**Navitas Autonomous Systems** — TEKNOFEST 2026
