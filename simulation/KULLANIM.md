# Navitas Simülasyon — Kullanım Kılavuzu

Gazebo Classic 11 tabanlı İHA + İKA görev simülasyonu. Bu makinede Gazebo **host'a
kurulu değil** — her şey **Podman konteyneri** içinde çalışır (host masaüstüne dokunmaz).

---

## 0. Gereksinimler

- **Podman** (rootless yeterli) — kurulu ✓
- `simulation/` dizini (konteynere mount edilir)
- ~3.5 GB disk (Gazebo imajı, ilk derlemede bir kez)

> Not: `simulation/launch.sh` doğrudan `gzserver`/`gzclient` çağırır → **sadece Gazebo
> host'a kuruluysa** çalışır. Bu makinede Gazebo native yok, o yüzden **kayıt için
> aşağıdaki `record.sh` (konteyner) yolunu kullan.**

---

## 1. Video kaydı alma (ANA KULLANIM)

```bash
cd simulation
                # 3-zonlu 300×300 dünyayı kaydeder → recordings/v<id>/
./docker/record.sh --seed 7       # farklı zon yerleşimi (rastgele 50×50 konumları)
```

- **Çıktı:** `simulation/recordings/v<id>/navitas.mp4` (1280×720). Her çalıştırma **yeni v<id>**
  (en yüksek vN → vN+1).
- Dünya: TEK 300×300 İHA-UB içinde rastgele konumlu **3 adet 50×50 HTAB** (kolay/orta/zor),
  her biri kendi 3-yol moloz challenge'ı. İHA sol→sağ tarar; her zonun İKA'sı alttan üste
  açık yolu kıvrılarak izler.
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
podman run --rm -v "$(pwd)/recordings":/r:Z navitas-gazebo:11 \
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
│   │       ika_nav: --bekleme-suresi (900, eski --timeout) ve --surus-suresi (600)
│   │       AYRI deadline'lar — şartname §6.2, CONTRACTS §7.1 (K5)
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

**Mevcut durum (iyileştirme bekliyor):**
- İHA = mavi kutulardan kaba uçak; İKA = yeşil kutu + silindir tekerlekler.
- Şartname hedefi: İHA fixed-wing (gövde+kanat+kuyruk+pervane), İKA 4-6 tekerlekli rover.

---

## 5. Arenayı/senaryoyu düzenleme

`scripts/world_generator.py` dünyayı üretir. Önemli sabitler (başta):
- `IHA_FB / IHA_IB` — İHA fırlatma/iniş; `IKA_KB / HB` — İKA kalkış/hedef.
- `CORRIDORS` — senaryo başına koridor genişliği/duvar yüksekliği/renk.
- `IKA_WAYPOINTS` — İKA'nın izlediği rota noktaları.

> ⚠️ Şu an arena, İKA rotası boyunca **duvarlı koridor (labirent)** üretiyor. Şartname
> **50×50m moloz sahası** istiyor (3 yol: 1 açık 2 kapalı). Bu uyumsuzluk düzeltilecek.

Tek başına dünya üretmek (kayıt almadan):
```bash
python3 scripts/world_generator.py --difficulty orta --seed 42 \
    --output worlds/test.world --record
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
