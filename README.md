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
│   ├── test_accuracy.py        ← Model doğruluk testi (30 etiketli görsel)
│   ├── train_seg.py            ← RescueNet ile YOLOv8-seg eğitimi
│   ├── images/                 ← Hızlı test görselleri
│   └── requirements_rpi.txt    ← RPi kurulum bağımlılıkları
│
├── models/
│   └── rescuenet_seg_v1_ncnn_model/   ← Aktif NCNN modeli (RPi deployment)
│       ├── model.ncnn.bin
│       ├── model.ncnn.param
│       └── metadata.yaml
│
├── dataset/
│   ├── download_and_convert.py ← RescueNet indir + YOLO formatına dönüştür
│   ├── test_prompts.txt        ← 30 image-gen prompt (15 kolay + 15 kandırmaca)
│   └── test_labels.json        ← test_accuracy.py için GT etiketleri
│
└── doc/
    └── model_analiz.md
```

---

## Hızlı Başlangıç

### Laptop'ta test

```bash
pip install ultralytics opencv-python numpy

# Tek görsel
python3 codes/rpi_inference.py --image codes/images/4.jpg

# Klasördeki tüm görseller
python3 codes/rpi_inference.py --image codes/images/

# Canlı kamera (Wayland)
QT_QPA_PLATFORM=xcb python3 codes/rpi_inference.py --camera
```

Çıktılar `codes/results/` altına yazar:
- `*_result.jpg` — orijinal çözünürlükte, yeşil (traversable) + kırmızı (blocked) maske
- `*_ika_map.jpg` — İKA navigasyon haritası (centerline + waypoint koordinatları)

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
python3 rpi_inference.py --fps      # hız testi (hedef: ≥10 FPS)
python3 rpi_inference.py --camera   # canlı
```

---

## Model

| Parametre | Değer |
|---|---|
| Mimari | YOLOv8n-seg |
| Dataset | RescueNet-Roads (HuggingFace: `asolodin/rescuenet-roads`) |
| Eğitim görseli | 2370 aerial |
| Sınıflar | `traversable` (0), `blocked` (1) |
| Export | NCNN (RPi 5 için optimize) |
| Hedef FPS | ≥10 FPS (RPi 5, NCNN) |

### Modeli yeniden eğitmek

```bash
# Dataseti indir (ilk seferinde)
python3 dataset/download_and_convert.py

# Eğit
python3 codes/train_seg.py

# NCNN export
python3 -c "
from ultralytics import YOLO
m = YOLO('runs/segment/rescuenet_seg_v1/weights/best.pt')
m.export(format='ncnn', imgsz=512)
"
```

---

## rpi_inference.py — Algoritma

```
Girdi → merkezi kare crop → 512×512 inference
      → mask upscale (orijinal çözünürlüğe)
      → morphological clean (gürültü temizle)
      → distance transform centerline
      → üst %40'ta hangi üçte birde daha fazla traversable px → open_path
      → waypoint örnekleme (alt→üst, 8 nokta)
      → *_result.jpg  (görsel)
      → *_ika_map.jpg (navigasyon haritası)
      → JSON payload  (terminal çıktısı)
```

### İKA Payload Formatı

```python
{
    "open_path": 2,           # 1=sol, 2=orta, 3=sag
    "confidence": 0.87,
    "waypoints": [[x,y], ...], # görüntü koordinatları, alt→üst
    "timestamp": 1234567890
}
```

---

## Model Doğruluk Testi

30 etiketli görsel seti için (`dataset/test_prompts.txt` promptlarıyla üretilir):

```bash
# Görselleri image-gen AI ile üret, P001.jpg ... P030.jpg olarak kaydet
python3 codes/test_accuracy.py --images test_images/
```

| Prompt grubu | Adet | Amaç |
|---|---|---|
| CORRECT (P001–P015) | 15 | Net 3-yol, 1 açık — model doğru bilmeli |
| TRICKY (P016–P030) | 15 | Gölge, benzer doku, gece, duman — model yanılabilir |

---

## Haberleşme

- Protokol: MAVLink over UDP
- Frekans: 915 MHz RF modül
- Güncelleme süresi: ≤200ms
- Mesafe: 300m operasyon alanı

---

## Gereksinimler

**Laptop (eğitim/test):**
```
Python 3.10+
ultralytics
opencv-python
numpy
torch
```

**Raspberry Pi 5 (deployment):**
```
ultralytics
opencv-python (veya opencv-python-headless)
numpy
```

---

## Ekip

**Navitas Autonomous Systems** — TEKNOFEST 2026
