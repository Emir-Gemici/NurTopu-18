# Navitas — Konteynerli Gazebo Simülasyon Video Kaydı

TEKNOFEST sunumu için İHA + İKA görevini Gazebo Classic 11'de oynatıp **mp4 video**
olarak kaydeden, tamamen otomatik kurulum. Host'a Gazebo/ROS kurmaya gerek yok;
her şey Podman konteynerinde, host'un masaüstüne dokunmadan çalışır.

## Hızlı kullanım

```bash
cd simulation
./docker/record.sh             # kolay, orta, zor → üç video
./docker/record.sh orta        # tek senaryo
./docker/record.sh kolay zor   # seçili senaryolar
```

Çıktı: `simulation/recordings/navitas_<senaryo>.mp4` (1280×720, ~45 sn)

İlk çalıştırmada imaj derlenir (~3-4 dk: Gazebo 11 imajı + plugin derlemesi).
Sonraki çalıştırmalar imajı yeniden kullanır.

## Ne gösteriyor

- **İHA** (mavi uçak) batıdan (Fırlatma Bölgesi) doğuya (İniş Bölgesi) geçer ve iner — ilk ~12 sn.
- **İKA** Kalkış Bölgesi'nden (güneybatı) Hedef Bölge'ye (kuzeydoğu) koridor boyunca navigate eder.
- İKA konumu, duvarların üzerine çıkan **camgöbeği işaret direği** ile net görünür
  (İKA gövdesi küçük; direk görünürlük içindir).
- Koridor rengi zorluğa göre değişir: kolay=yeşil, orta=sarı, zor=kırmızı.

## Nasıl çalışıyor

```
Podman konteyner (gazebo:libgazebo11, Ubuntu 20.04)
  ├─ Xvfb :99           sanal ekran (1280×720)
  ├─ openbox            fullscreen'in çalışması için minik WM
  ├─ gzserver --pause   dünya + kinematik animasyon plugin'i (libnavitas_anim.so)
  ├─ gzclient           sinematik kuş bakışı kamera (fullscreen)
  ├─ ffmpeg x11grab     ekranı mp4'e kaydeder (kayıt başlayınca sim devam ettirilir)
  └─ gz world -p 0      sim t=0'dan oynar → İHA + İKA otonom hareket eder
```

### Neden CLI kontrol yerine animasyon plugin'i?

Orijinal `iha_flight.py` / `ika_nav.py` her adımda `gz topic`/`gz model` CLI'ı çağırır;
her çağrı ~0.8 sn transport başlatma overhead'i taşır → akıcı/gerçek-zamanlı hareket
imkânsız (ve `timeout=1` ile aralıklı `TimeoutExpired`). Video için bunun yerine
**`libnavitas_anim.so` dünya plugin'i** her simülasyon adımında (1000 Hz) yol noktaları
arasında interpolasyon yapıp `SetWorldPose` çağırır → video fps'inden bağımsız,
pürüzsüz, deterministik, her zaman tamamlanan hareket. Trajectory'ler
`world_generator.py --record` tarafından senaryoya göre üretilir.

> Not: `iha_flight.py`/`ika_nav.py` (DiffDrive + kapalı-döngü nav) gerçek kontrol
> tasarımı olarak korunur; donanım/HIL testi içindir, otomatik video için değil.

## Render notu

Xvfb yazılımsal OpenGL (llvmpipe) kullanır — sahne geometrik olarak basit olduğu için
gölgeler kapalıyken ~45-60 FPS render eder (RTF ≈ 1.0), video akıcıdır. Donanım GPU
hızlandırması gerekmez. Gölgeler kayıt modunda otomatik kapatılır (FPS için).

## Kamera açısını değiştirme

```bash
# world_generator.py varsayılanı: "-40 -40 38 0 0.5 0.785"  (x y z roll pitch yaw)
GAZEBO_GUI_CAM="0 -55 50 0 0.7 1.5708" ./docker/record.sh orta
```
(record.sh bu env'i konteynere geçirir; world_generator okur.)

## Gereksinimler

- Podman (rootless yeterli)
- `simulation/` dizini (mount edilir)
- ~3.5 GB disk (imaj)
