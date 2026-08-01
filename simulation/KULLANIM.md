# Navitas Simülasyon — Kullanım Kılavuzu

Gazebo Classic 11 tabanlı İHA + İKA görev simülasyonu. Tekrarlanabilir kayıt ve plugin
derleme yolu izole `navitas-gazebo:11-six-scenarios` Podman imajını kullanır.

Altı karşılaştırmalı profil için [SENARYO_PAKETI.md](SENARYO_PAKETI.md) belgesine bakın.

---

## 0. Gereksinimler

- **Podman** (rootless yeterli) — kurulu ✓
- `simulation/` dizini (konteynere mount edilir)
- ~3.5 GB disk (Gazebo imajı, ilk derlemede bir kez)

> `simulation/launch.sh` yerel Gazebo kurulumunu kullanabilir; kanıt videosu ve CI için
> aşağıdaki container kayıt yolu tercih edilir.

---

## 1. Video kaydı alma (ANA KULLANIM)

```bash
cd simulation
./docker/record.sh zor --profile cx_comms_latency
./docker/record.sh orta --profile cc_wind_dust
```

- **Çıktı:** `simulation/recordings/v<id>/navitas.mp4` (1280×720). Her çalıştırma **yeni v<id>**
  (en yüksek vN → vN+1).
- Dünya: tek 300×300 İHA-UB içinde sabit, birbirinden ayrık **3 adet 50×50 HTAB**
  (kolay/orta/zor). Üçü de fiziksel olarak aynı dünyadadır; seçilen odak zonun İHA/İKA
  görevi aktiftir, diğer iki zon karşılaştırma/stres sahası olarak görünür.
- İlk çalıştırmada imaj derlenir (~3-4 dk). Sonraki çalıştırmalar imajı yeniden kullanır.

### Kamera açısını değiştirme
```bash
# Varsayılan: "-40 -40 38 0 0.5 0.785"  (x y z roll pitch yaw)
GAZEBO_GUI_CAM="0 -55 50 0 0.7 1.5708" ./docker/record.sh orta
```

---

## 2. Bir kareyi (foto) videodan çıkarma

```bash
cd simulation
podman run --rm -v "$(pwd)/recordings":/r:Z navitas-gazebo:11-six-scenarios \
  ffmpeg -y -ss 20 -i /r/navitas_kolay.mp4 -frames:v 1 /r/kare.png
```
`-ss 20` = 20. saniye. Çıktı: `recordings/kare.png`.

---

## 3. Dizin yapısı

```
simulation/
├── docker/
│   ├── record.sh              ← ANA: konteynerde çalıştır + mp4 kaydet
│   ├── record_in_container.sh ← konteyner içi orkestrasyon (Xvfb→gzserver→ffmpeg)
│   └── Containerfile          ← Gazebo 11 imaj tarifi (+ plugin derlemesi)
├── models/                    ← SDF modelleri (DÜZENLENECEK yer)
│   ├── iha/model.sdf          ← İHA (uçak)
│   ├── ika/model.sdf          ← İKA (kara aracı)
│   ├── catapult/ , debris/    ← mancınık, moloz
├── worlds/                    ← üretilen dünya dosyaları (.world)
├── scripts/
│   ├── world_generator.py     ← dünyayı/arenayı üreten kod (DÜZENLENECEK yer)
│   ├── iha_flight.py, ika_nav.py ← gerçek kontrol (HIL/donanım testi için)
│   └── navitas_sim.py
├── plugins/
│   └── navitas_anim.cc        ← kayıt için pürüzsüz hareket plugin'i (libnavitas_anim.so)
└── recordings/                ← çıktı mp4'ler (gitignore'da)
```

---

## 4. Modelleri düzenleme (İHA / İKA tasarımı)

Modeller **SDF** (XML) formatında, `simulation/models/<ad>/model.sdf` içinde.

- **Birim:** metre. Pozlar `<pose>x y z roll pitch yaw</pose>` (radyan).
- **Görsel şekil:** `<visual><geometry>` içinde `<box>`, `<cylinder>`, `<sphere>` veya
  `<mesh>` (harici .dae/.stl). **Renk:** `<material><ambient>` ve `<diffuse>` (R G B A).
- **Çarpışma:** her görselin bir `<collision>` eşi olmalı (fizik için).
- **Sensörler:** kamera/IMU/GPS/LiDAR `<sensor>` blokları.

**Örnek — İHA gövde rengini değiştir** (`models/iha/model.sdf`):
```xml
<material><ambient>0.2 0.2 0.8 1</ambient><diffuse>0.2 0.2 0.8 1</diffuse></material>
<!-- ↑ mavi. Kırmızı için: 0.8 0.1 0.1 1 -->
```

> Değişiklik sonrası ekstra adım yok: `record.sh` `GAZEBO_MODEL_PATH=models` ile çalışır,
> bir sonraki kayıtta yeni model otomatik kullanılır.

Mevcut İHA sabit-kanat gövde/kanat/kuyruk/pervane görselleştirmesine; İKA ise alçak
ağırlık merkezli dört teker rover, 200 g yük temsili, kamera/LiDAR/GPS/IMU sensörlerine
sahiptir. Kinematik İHA sunum yörüngesi aerodinamik uçuş modeli değildir.

---

## 5. Arenayı/senaryoyu düzenleme

`scripts/arena.py` kıvrımlı üç yolu ve tek-açık-yol ground-truth'unu üretir;
`scripts/world_generator.py` resmî boyutları, molozu, hava/ışığı ve görev animasyonunu
SDF dünyasına dönüştürür. `scenarios/*.json` yalnız veri profilleridir.

Tek başına dünya üretmek (kayıt almadan):
```bash
python3 scripts/world_generator.py --profile cc_night_fog --focus zor \
    --output /tmp/cc_night_fog.world --record
```

---

## 6. Görev kontrol komutları (Gazebo çalışırken, konteyner içinde)

| Komut | İşlev |
|-------|-------|
| `gz world -p 0` | ▶ Başlat |
| `gz world -p 1` | ⏸ Duraklat |
| `gz world -r`   | ↺ Sıfırla |
| `gz stats`      | İstatistik (RTF/FPS) |
| `gz model -m iha -p` | İHA pozisyonu |
| `gz model -m ika -p` | İKA pozisyonu |

---

## 7. Sık sorunlar

- **"gzserver: command not found" (host'ta):** Normal — Gazebo host'ta yok, `record.sh`
  (konteyner) kullan.
- **mp4 boş/çok kısa:** RTF düşükse render yavaşlamıştır; kamera/sahne sadeleştir.
- **"end-of-life" sarı yazısı:** Zararsız — Gazebo Classic 11 üretici desteği bitti (Ocak 2025).
