# Gazebo Altı Senaryo Paketi

Bu paket, TEKNOFEST 2026 İleri Otonom Sistemler görevini Gazebo Classic 11 içinde
karşılaştırmak için hazırlanmış altı deterministik stres senaryosudur. Her dünya aynı
`300 × 300 m` İHA uçuş bölgesi içinde, birbirinden ayrık üç adet `50 × 50 m` HTAB
barındırır. Her HTAB'da üç güzergâh bulunur; yalnız biri açık, ikisi fiziksel engellidir.

Resmî boyut sözleşmesi:

- İHA-UB: en fazla `300 × 300 m`
- HTAB: `50 × 50 m`
- İKA-KB: `1 × 1 m`
- HB: `2 × 2 m`, kırmızı `H`
- İHA-İB: `30 × 30 m`, mavi
- İKA, rota İHA havadayken teslim edilmiş olsa bile İHA inişi ve YKS manuel görev
  tetik olayı tamamlanmadan hareket etmez.

## Senaryolar

| Profil | Tasarımcı | Ana stres |
|---|---|---|
| `cc_night_fog` | Claude Code | Gece, yoğun sis, yüksek bina enkazı |
| `cc_wind_dust` | Claude Code | Güçlü yanal rüzgâr, toz görüşü, düşük tutuş |
| `cc_narrow_sensor` | Claude Code | Dar koridor, yoğun chicane ve fiziksel sıkışma |
| `cx_glare_perspective` | Codex | Aşırı parlama, açık zemin, eğik tarama |
| `cx_comms_latency` | Codex | Gecikme, deterministik paket düşümü, manuel tetik |
| `cx_aftershock_dynamic` | Codex | Görev sırasında düşen katı kiriş/dinamik engel |

Profil JSON'ları yalnız gerçekten uygulanan parametreleri içerir. Uygulanmamış GNSS/IMU
füzyonu, A* veya ölçülmeyen algı başarı yüzdeleri başarı gibi raporlanmaz.

## Üretim ve çalışma

Altı dünyayı ve SHA-256 manifestini üretmek:

```bash
python3 simulation/scripts/generate_scenario_suite.py
```

Tek profilin animasyonlu dünyasını üretmek:

```bash
python3 simulation/scripts/world_generator.py \
  --profile cx_comms_latency --record \
  --output /tmp/cx_comms_latency.world
```

Gerçek kayıt yolunu çalıştırmak:

```bash
cd simulation/docker
./record.sh zor --profile cx_comms_latency
```

Profil seed'i varsayılan olarak kullanılır. Yalnız bilinçli hata ayıklamada `--seed` veya
`--map` ile override yapılmalıdır; kullanılan gerçek seed/map, dünya stdout'una, meta
dosyasına ve hakem loguna yazılır.

## Doğrulama katmanları

```bash
python3 -m unittest discover -s simulation/tests -v
bash -n simulation/docker/record.sh simulation/docker/record_in_container.sh
```

`gazebo_manual_trigger_smoke.sh`, rota hazırken İKA'nın manuel tetik beklediğini;
`gazebo_aftershock_smoke.sh`, artçı kirişin 8 m'den 0,65 m'ye görev sırasında indiğini
gerçek Gazebo sürecinde doğrular. Plugin ayrıca 15 sim-saniye waypoint ilerlemesi yoksa
`durum=TIKANDI` üretir; güvenilir model rotası yoksa `durum=ROTA_YOK` ile güvenli
duruşta kalır. Yarışma profillerinde ground-truth fallback kapalıdır.

## Bilinen sınırlar

- İHA uçuşu sunum için kinematiktir; aerodinamik kuvvet modeli/HIL değildir.
- İKA ileri hareketi sınırlı fiziksel kuvvetle yapılır, fakat dönüşte hâlâ sınırlı
  `SetAngularVel` kullanılır; gerçek motor/teker kapalı döngüsünün yerine geçmez.
- LiDAR, GPS ve IMU SDF sensörleri mevcuttur; aktif navigasyon hâlâ Gazebo ground-truth
  pozunu kullanır. Sensör füzyonu uygulanmış gibi iddia edilmez.
- Üç ayrıntılı HTAB tek-zon dünyadan daha ağırdır; hızlı CI sözleşme/SDF testleri ile tam
  dinamik smoke ve video kayıtları ayrı katmanlarda tutulur.
