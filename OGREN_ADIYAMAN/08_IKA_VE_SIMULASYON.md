# 08 · İKA VE SİMÜLASYON — kara aracının yazılımı, sürücü soyutlaması, Gazebo, puan hesabı

> Kaynaklar: `simulation/scripts/ika_nav.py`, `ika_surucu.py`, `iha_haritala.py`, `iha_perceive.py`, `hakem_log.py`, `world_generator.py`, `arena.py`, `score.py` ·
> `simulation/KULLANIM.md`, `PROVA_SENARYOSU.md`, `docker/README.md`, `models/ika/model.sdf` · `scripts/ika_surucu_kabul.py` · `drone/README_KURULUM.md` ·
> `CONTRACTS.md` §7, §7.1–7.3, §11.1 · `FDR/BOLUM_3` §3.2.2, §3.3.3 · `REVIEW_LOG.md` D-02, D-390, D-391 · `ozet/G_ika_sim_saha_pixhawk.md`.
> Dürüst özet: **İKA yazılım mantığı kodda ve testte hazır; İKA donanımı hiç tedarik edilmedi; Gazebo kapalı çevrim bugün kanıtlı değil.**

---

## Seviye 1 — Bir cümle ve büyük resim

İKA (kara aracı) yarışma görevinde İHA'nın bulduğu açık güzergâhı **otonom** izleyip 2×2 m kırmızı H brandasına **fiziksel temas** eder.
Yazılımı `simulation/scripts/ika_nav.py`: gelen `OPEN_ROUTE` waypoint'lerini oransal yön kontrolüyle izler; hareket edebilmek için üçlü
kilit (`OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO`) şarttır; `NO_ROUTE` ya da bağlantı kaybında anında durur. Motor komutu bir **sürücü arayüzünden**
geçer (`ika_surucu.py`): Gazebo arka ucu var, **gerçek arka uç yok** (`GercekSurucu` arka uçsuz kurulmayı reddeder). Görev test uçuşunda
(30 Eyl) İKA **zorunlu değil**; İKA finale (2027) bırakıldı. FDR bunu açıkça yazar: "İKA donanımı tedarik edilmedi, yapısal tasarımı yoktur".

## Seviye 2 — Nasıl çalışır

### 2.1 `ika_nav.py`: kontrol yasası ve kilitler
- **Kontrol:** A* değil, PID değil — **oransal yön kontrolü**: `delta = TURN_GAIN × yön_hatası`; sağ = taban + delta, sol = taban − delta;
  `±MAX_SPEED` kırpma. Sabitler: `MAX_SPEED` 2,0 m/s · `TURN_GAIN` 1,8 · `WP_RADIUS` 0,5 m · **`FINAL_WP_RADIUS` 0,3 m** (< HB kenarı/2 = 1,0 m,
  CONTRACTS §7.3: araç merkezi ped kenarından ≥ 0,7 m içeride durur → gövde pedin üstünde, D-391) · `CTRL_HZ` 10 · `MAX_WAYPOINTS` 64 ·
  `MAX_SEGMENT_M` 2,10 · `MAX_LOCAL_EXTENT_M` 60 · `SOURCE_TOLERANCE_M` 0,15.
- **Yön kestirimi:** pusula/IMU yok; ardışık iki konum farkı 0,03 m'yi aşınca `atan2` ile güncellenir (araç durunca yön donar).
- **Koordinat:** `OPEN_ROUTE.ref_xy` + yerel `waypoints` → dünya = ref + yerel (saf öteleme, dönme yok, CONTRACTS §3.2); ilk yerel nokta [0,0]
  olmalı; sayısal `road` (1/2/3) **geometri değildir**, waypoint'siz mesaj hareketi tetiklemez. Gerçek İKA'nın GNSS→yerel dönüşümü **yok**
  (konum kaynağı yok).
- **A\* nerede?** İHA tarafında (`costmap_path_finder.rota_bul` / `analyze_path`); İKA yalnız hazır listeyi izler.
- **Görev döngüsü `ika_gorevi`:** (1) geçerli `OPEN_ROUTE` bekle → (2) `IHA_LANDED` ∧ `IKA_GO` bekle (`wait_surus_izni`) → (3) `navigate_route`.
  Sürüşte her turda: süre, sürücü sağlığı, `link_ok` (heartbeat 3,0 s), rota kapısı (`NO_ROUTE` → `send_vel(0,0)`). Sıfır-dışı her motor komutu
  `receiver.run_if_route_valid` kilidi altında.
- **İki ayrı son tarih (K5, §7.1):** bekleme 900 s, sürüş 600 s; sürüş saati izin anında başlar, bekleme sürüşten düşülmez (eski tek `--timeout 60`
  yasak — sahada iniş dakikalar sonra gelir). Çıkış kodları: 0 başarı · 1 rota gelmedi · 2 NO_ROUTE · 3 izin gelmedi · 4 süre doldu.
- **K8 `--yks`:** UDP'de rota ACK'i yalnız gönderene döner; hakem "İKA'ya aktarıldı" kanıtını görsün diye kopya YKS'ye; OPEN_ROUTE IKA_GO'dan **önce**
  geldiği için adres IKA_GO'dan öğrenilemez → `--yks` fiilen zorunlu, yoksa 2/2 onay hiç açılmaz.

### 2.2 `ika_surucu.py`: sürücü soyutlaması (T149 / D-390, CONTRACTS §7.2)
Arayüz: `hiz_ver(sag, sol) -> bool` (istisna **sızmaz**, False = iletilemedi) · `konum_al() -> (x,y,z,yaw)` ya da dörtlü None · `durdur()` · `saglikli()`.
`ARDISIK_HATA_TAVANI = 3`: 10 Hz'de ~0,3 s süren arıza → "yanıtsız", `navigate` son bir durdurma dener, False döner (eski davranış: subprocess
istisnasıyla **çökmek**). Üç uygulama: `GazeboSurucu` (`gz topic` subprocess, bayt-eş korunmuş), `SahteSurucu` (test; arıza enjeksiyonu),
`GercekSurucu(arka_uc=None)` → **`DONANIM_YOK` istisnası** (sessiz iskelet yasak). Kabul turu `scripts/ika_surucu_kabul.py` K1–K6: durdur · konum
(hepsi None ise "KONUM YOK" uyarısıyla geçici kabul) · rampa 0→0,30 m/s 5 adım ("GÖZLE TEYİT ET") · durdur+sağlık · fail-closed 3 arıza (sahte) ·
sağlık sıfırlama. Çıkış 2 = sürücü kurulamadı (**gerçek + arka uç yok = bugünkü beklenen durum**). T1–T8 kabul turu ön kayıtla GEÇTİ (2 Eyl, sahte/Gazebo).

### 2.3 🔴 Gazebo kapalı çevrim bugün kanıtlı değil
`simulation/models/ika/model.sdf:233-237`: `libDiffDrivePlugin.so` **kaldırılmış** ("komutsuzken tekerleri 0 hıza frenliyor; sim'de aracı
`navitas_anim` sürer"). `GazeboSurucu`'nun yazdığı `~/ika/vel_cmd` topic'ini tüketen plugin **yok**. Kayıt videolarında İKA'yı `plugins/navitas_anim.cc`
kinematik animasyonu hareket ettirir. Sonuç: `ika_nav` mantığı **`SahteSurucu` + birim testleriyle** (`tests/test_p3_ika_surucu.py`) kanıtlı,
fizik simülasyonuyla değil. CONTRACTS §11.1: "`simulation/` altındaki hiçbir dosya saha halkasına sahip yazılamaz; sim çıktısı kanıt sayılmaz".

### 2.4 Simülasyon altyapısı
- Gazebo Classic 11, **host'a kurulu değil**; Podman konteynerinde (`docker/record.sh` → 1280×720 mp4). Ana PC'de gz/WSL yok (2 Eyl).
- İki dünya üreteci: `generate_world.py` (eski, tek HTAB, duvarlı koridor 4,5/3,2/2,2 m) ve `scripts/world_generator.py` (300×300 İHA-UB içinde 3 zon;
  şerit 6/5/4 m, moloz 130/170/210, `IKA_SPEED 1,1`, `SCAN_Z 30`). Geometri tek kaynağı `scripts/arena.py`: 5 harita × 3 senaryo = **15 deterministik saha**
  (genel kapının sahneleri buradan), koridor omurgaları −16/0/+16 m, `KB_Y −23`, `HB_Y 21`; açık yol seed'den, gizli.
- **Dürüst haritalama zinciri** `iha_haritala.py`: 30 m serpantin, 1 Hz kare + poz → kuzey-yukarı ortomozaik (1024 px, 56 m, mpp ≈ 0,055) →
  `iha_perceive._infer` (registry'den model, fail-closed) → piksel → dünya → `route.txt`. "Model yanılırsa İKA kapalı yola gider, fizik durdurur —
  sonuç dürüsttür."
- `hakem_log.py`: metin log, gerçek loopback comms ile; model künyesi koşan modelden türetilir; karar `arena.open_road` yer gerçeğiyle karşılaştırılır.
  Uyarı: "GNSS+IMU+encoder füzyonu → A* → PID" satırı **anlatıdır**, koşan kod değil.
- Eşleme: protokol/mesajlar ve `ika_nav` mantığı sim ↔ gerçek **birebir** (mühür `YKS_IKA` listesi); motor/konum ve fizik/geometri **eşlenmiyor**;
  FDR 3.3.3 "3B görev icra simülasyonu + video" **YOK** (CAD yok, mesh 0, koşum yok; açık kalem #16).

### 2.5 `score.py` — puan formülü (01 §2.3 ile aynı)
Tablo 6 ile birebir (`ARCHITECT_PLAN.md` doğruladı); dört örnek senaryo (`hedef_zor`, `hedef_orta`, `inis_sapma`, `basarisiz`); geçerlilik kontrolleri
(İHA > 25 kg, İKA > 10 kg, süreler). Bilinen sınırlar (şartname özetinden): §6.4 geçersiz uçuşta `Puan₂`'yi sıfırlamaz, üç turu birleştirmez,
"Senaryo 1/2/3 = Kolay/Orta/Zor" eşlemesi koddaki varsayım.

### 2.6 `drone/` klasörü İKA değildir
`drone/README_KURULUM.md`: "hocanın dronuna" bantla takılan RPi 5 **kamera yükü** (dron elektroniğine bağlanmaz; hotspot `NAVITAS` 10.42.1.1; UDP 5599 kalp
atışı / 5600 H.264 / 5601 AI overlay / 5602 telemetri); "test/gösterim içindir, yarışma mimarisinin yerine geçmez". `drone/test_uctan_uca.py` runbook'ta
"H3 video", genel kapı dışında.

## Seviye 3 — Sayılar ve açık kalemler

| konu | değer / durum | kaynak |
|---|---|---|
| Gazebo İKA modeli | kütle 8,0 kg, 4 teker 0,5 kg, sensör blokları (camera/lidar/gps/imu) — **SDF, gerçek seçim değil** | `models/ika/model.sdf` |
| DDR İKA planı | RPi 5 + Pi kamera, A* + PID, GNSS+IMU+encoder, ≤ 10 kg, ≥ 200 g yük (REQ-1, REQ-3) | `README.md`, DDR |
| Varış | son waypoint pedin kutusunda 253/256 (İHA yarısı); `FINAL_WP_RADIUS 0,3 < 1,0` (İKA yarısı); Gazebo fiziksel temas **ÖLÇÜLEMEDİ** (gz yok) | CONTRACTS §7.3 |
| Kabul turu | T1–T8 GEÇTİ (ön kayıt), ardışık hata tavanı 3 | `results/p3_ika_surucu/ON_KAYIT.md` |
| Kuru koşu | 10 halka: 9 GEÇTİ, **motor SAHİPSİZ**, çıkış 1 | `results/saha_kuru_kosu_20260904_095222/ozet.json` |
| T149 | açık, İNSAN+MİMAR: gerçek sürücü ve konum kaynağı yok; şartname §2.2.5 "otonom hareket etmeyen İKA'nın görevi başarısız" | `TASK_QUEUE.md:6444` |
| FDR açık kalem | A1 (İKA sürücüsü), A9 (Gazebo temas ÖLÇÜLEMEDİ), #16 (3B simülasyon yeniden açıldı, D-417) | Bölüm 6 §6.5.1 |
| Mühür | `ika_nav.py`, `ika_surucu.py`, `saha_baslat.py` "yarışan yazılım" listesinde | `scripts/surum_dondur.py` |
| Şartname | İKA ≤ 10 kg (yük hariç), yük eksiksiz taşınmalı, yapısal bütünlük (§2.2.6); m_İKA her 15 g = 1 puan; m_yük her 100 g = 1 puan | 01 |

---

## Jüriye 30 saniyede

> "İKA yazılımı hazır: açık güzergâhın waypoint'lerini izler, ancak üç koşul birden sağlanınca hareket eder: geçerli rota, İHA'nın Pixhawk
> kanıtlı inişi ve yer istasyonundan manuel başlatma. Rota yok ya da bağlantı kesik dendiği an durur; motor sürücüsü üst üste üç kez
> yanıt vermezse güvenli duruşa geçer. Dürüst olalım: İKA donanımı henüz alınmadı, gerçek motor sürücüsü yok; bu yüzden sürücü arayüzü
> arka uç verilmeden kurulmayı reddeder, sessizce 'hazır' demez. Görev test uçuşunda İKA zorunlu değil; final için açık kalem."

## Kendini sına

1. İKA'nın hareket edebilmesi için üç koşul? Hangisi Pixhawk'tan gelir?
2. `ika_nav` A* kullanır mı? Kontrol yasası ne?
3. `FINAL_WP_RADIUS` neden 0,3 m; hangi eşitsizlik bağlayıcı?
4. Bekleme ve sürüş süreleri neden ayrı?
5. `GercekSurucu` arka uçsuz ne yapar, neden?
6. Ardışık hata tavanı ve sonucu?
7. Gazebo'da İKA neden bugün `ika_nav` ile sürülmüyor?
8. "Sim çıktısı kanıt sayılmaz" kuralı nerede yazılı, neden?
9. `--yks` neden fiilen zorunlu?
10. `drone/` klasörü ne, ne değil?

<details><summary>Cevaplar</summary>

1. Geçerli OPEN_ROUTE, IHA_LANDED, IKA_GO; IHA_LANDED (Pixhawk EXTENDED_SYS_STATE + relative_alt). 2. Hayır; oransal yön kontrolü, `TURN_GAIN 1,8`, 10 Hz. 3. HB kenarı 2 m; `FINAL_WP_RADIUS < HB_KENAR_M/2 = 1,0` → merkez ped kenarından ≥ 0,7 m içeride, gövde pedin üstünde (temas SS7). 4. Sahada iniş dakikalar sonra gelir; tek deadline bekleme süresini sürüşten yerdi; 900 s bekleme, 600 s sürüş (§6.2). 5. `DONANIM_YOK` istisnası; sessiz iskelet yasak, kuru koşuda motor SAHİPSİZ görünür. 6. 3 ardışık `hiz_ver` arızası (~0,3 s) → son bir durdurma, `navigate` False (çökme yerine). 7. `libDiffDrivePlugin.so` kaldırılmış; `vel_cmd` topic'ini tüketen yok; İKA'yı `navitas_anim` sürer. 8. CONTRACTS §11.1; `navitas_sim.py` gz/meta.txt/kendi IHA_LANDED'ını varsayar, sahada üçü de yok. 9. UDP'de rota ACK'i gönderene döner, OPEN_ROUTE IKA_GO'dan önce gelir, YKS adresi öğrenilemez; kopya gitmezse 2/2 onay hiç açılmaz. 10. Hocanın dronuna takılan RPi kamera yükü, test/gösterim; İKA değil, yarışma mimarisi değil.
</details>

## Kaynaklar
`simulation/scripts/ika_nav.py`, `ika_surucu.py`, `arena.py`, `iha_haritala.py`, `hakem_log.py`, `score.py` · `scripts/ika_surucu_kabul.py` · `simulation/models/ika/model.sdf` ·
`CONTRACTS.md` §7–§7.3, §11.1 · `tests/test_p3_ika_surucu.py`, `test_p9e_branda_temas.py`, `test_k5_k6_sure_limitleri.py`, `test_ika_go_ackli_tekrar.py` · `ozet/G_ika_sim_saha_pixhawk.md`.
