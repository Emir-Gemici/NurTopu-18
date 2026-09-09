# G — İKA, Simülasyon, YKS, Pixhawk ve Saha Operasyonu: Kanıtlı Özet

> Depo: `/home/n4vitas/proje/navitas_tam/navitas` · Yazım tarihi: 10 Eylül 2026 · Okuyucu: Python bilen, drone/ArduPilot/Gazebo bilmeyen takım üyesi.
> Kural: her sayının yanında dosya yolu var. Depoda kanıtı olmayan her şey **DOĞRULANAMADI** diye işaretlendi. "BEYAN" = sözlü/etiketsiz bildirim; "ÖLÇÜM" = log satırı, dosya, sayı.
> Önemli tarih notu: depodaki son saha kaydı **D-436 (7 Eylül)**'dır (`REVIEW_LOG.md:30379`). 7 Eylül sonrası sahada ne olduğu bu depodan **DOĞRULANAMADI**.

---

## 0. Bir bakışta sistem

Görev zinciri üç istasyondur: **İHA** (drone üstünde Jetson) → **YKS** (yer istasyonu PC, `comms/yks_gui.py`) → **İKA** (kara aracı). Aralarındaki dil tek bir JSON protokolüdür (`comms/protocol.py`): `OPEN_ROUTE` (açık yol + waypoint), `NO_ROUTE`, `IHA_LANDED`, `IKA_GO`, `HEARTBEAT`, `ACK`. Bu belge İHA'nın algı tarafını **kapsamaz**; İHA-dışı her şeyi kapsar.

Bugünkü gerçeklik, tek cümleyle: **yazılım zinciri (protokol, YKS, İKA navigasyon mantığı, Jetson açılışı, mühür) kodda ve testte hazır; İKA donanımı yok, drone 6 Eylül'de üç kez devrildi ve henüz uçmadı.**

---

## 1. İKA (İnsansız Kara Aracı)

### 1.1 Donanım — ne var, ne yok

Depo İKA donanımı konusunda nettir:

- `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:52` — "İKA bilgisayarı | Raspberry Pi 5 | **tedarik edilmedi** — İKA hattı finale bırakıldı".
- Aynı dosya §3.2.2 (satır ~417): "İKA donanımı **tedarik edilmedi**; hat finale bırakıldı … Dolayısıyla İKA'nın **yapısal tasarımı yoktur.**"
- `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:961` — "**İKA aviyonik BOM'u yoktur**".
- `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:991` — kuru koşu halka 10 (**motor**): "🔴 SAHİPSİZ — gerçek motor sürücüsü **yok**".

Yani **motor sürücüsü, GNSS, IMU, encoder — hiçbiri gerçek İKA'da yoktur**, çünkü gerçek İKA yoktur. Bu terimlerin depoda geçtiği iki yer yanıltıcı olabilir, dikkat:

1. **Gazebo İKA modeli** (`simulation/models/ika/model.sdf`): `mass 8.0` kg (satır 18), 4 tekerlek (her biri 0,5 kg, satır 156–216), `front_camera` (satır 90), `lidar` (satır 103), `gps` (satır 121), `imu` (satır 134) sensör blokları. Bunlar **simülasyon SDF'idir**; gerçek sensör seçimi değildir. FDR bunu "CAD değil — `mesh` sayısı 0" diye işaretler (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:1100`).
2. **Hakem logu metni** (`simulation/scripts/hakem_log.py:199`): `"GNSS+IMU+encoder füzyonu → A* path planning → … (diferansiyel sürüş, PID, seyir 1.1 m/s)"`. Bu satır **log anlatısıdır**, koşan bir füzyon/PID kodu değildir (bkz. §1.2 — `ika_nav.py`'de ne A* ne PID var).

**`drone/` klasörü İKA değildir.** `drone/README_KURULUM.md`'deki Raspberry Pi 5, "hocanın dronuna" bantla takılan bir **kamera yükü**dür (README §2: "dron elektroniğine BAĞLANMAZ"): Ubuntu 26.04, imx708 kamera, kendi hotspot'u `NAVITAS` (RPi `10.42.1.1`), UDP 5599 kalp atışı / 5600 ham H.264 / 5601 AI overlay ~2–5 fps / 5602 telemetri (`drone/ortak.py:408-423`). README §5: "**test/gösterim** içindir, yarışma haberleşme mimarisinin yerine geçmez." `drone/test_uctan_uca.py` protokolü localhost'ta 16 kontrolle sınar; runbook bunu genel kapı dışında "H3 video" olarak tutar.

### 1.2 Yazılım — `simulation/scripts/ika_nav.py` gerçekte ne yapar

Dosya adı "simulation" altında olsa da mühürlenen "yarışan yazılım" listesindedir (`scripts/surum_dondur.py` `YKS_IKA` demeti). 650 satırlık modülün iskeleti:

**Kontrol yasası — A* değil, PID değil, oransal yön kontrolü.** `steer(heading_err)` (`ika_nav.py:100-112`): `delta = TURN_GAIN × err`, sağ teker = `base + delta`, sol = `base − delta`, her biri `±MAX_SPEED`'e kırpılır. Sabitler (`ika_nav.py:37-45`):

| sabit | değer | anlamı |
|---|---|---|
| `MAX_SPEED` | 2,0 m/s | tekerlek hız tavanı |
| `TURN_GAIN` | 1,8 | yön hatası → teker farkı katsayısı |
| `WP_RADIUS` | 0,5 m | ara waypoint'e "ulaştı" yarıçapı |
| `FINAL_WP_RADIUS` | 0,3 m | HB (hedef) son yaklaşım toleransı (D-391) |
| `CTRL_HZ` | 10 Hz | kontrol döngüsü |
| `MAX_WAYPOINTS` | 64 | rota uzunluğu tavanı |
| `MAX_SEGMENT_M` | 2,10 m | ardışık iki waypoint arası tavan (costmap 2,0 m + pay) |
| `MAX_LOCAL_EXTENT_M` | 60 m | HTAB sınırı |
| `SOURCE_TOLERANCE_M` | 0,15 m | ilk yerel waypoint [0,0]'dan sapabilir |

**Yön (yaw) kestirimi:** pusula/IMU okunmaz; `navigate()` içinde ardışık iki konum farkı 0,03 m'yi aşınca `atan2(ddy, ddx)` ile yön güncellenir (`ika_nav.py` ~satır 330). Yani yön, **hareket vektöründen** türetilir — araç durunca yön bilgisi donar.

**A* nerede?** İKA'da değil, İHA'da: `simulation/scripts/iha_haritala.py` `costmap_path_finder.rota_bul` (`codes/`) ile rotayı üretir; İKA yalnızca hazır waypoint listesini izler.

**Koordinat çerçevesi (`route_to_world_waypoints`, `ika_nav.py:143-205`):** `OPEN_ROUTE` mesajında `ref_xy` (İHA'nın ilan ettiği başlangıç referansı, metre) ve `waypoints` (bu referansa **göre yerel** [x,y] listesi) gelir (`comms/protocol.py:41-47`). İKA: ilk yerel nokta `[0,0]` olmalı (aksi hata), hiçbir yerel nokta 60 m'yi aşmamalı, `dünya = ref + yerel`. Sayısal `road` (1=sol 2=orta 3=sağ) tek başına **geometri değildir**; waypoint'siz mesaj hareketi tetiklemez (dosya başındaki docstring). Bu çerçeve **HTAB-yerel metre**dir; enlem/boylam yoktur. Gerçek İKA'nın kendi konumunu bu çerçeveye nasıl oturtacağı (GNSS→yerel dönüşüm) depoda **DOĞRULANAMADI** — çünkü konum kaynağı yok (`konum_al()` Gazebo'dan okur).

**Sürüş kapısı (fail-closed):** `ika_gorevi()` (`ika_nav.py:437-505`) sırayla bekler:
1. Geçerli `OPEN_ROUTE` (`wait_open_route_from_comms`), 
2. `IHA_LANDED` **ve** `IKA_GO` (YKS operatörünün manuel intikal izni) — `receiver.wait_surus_izni`,
3. sonra `navigate_route`. Sürüş sırasında her turda: sürüş süresi, sürücü sağlığı, `link_ok` (3,0 s heartbeat zaman aşımı, `comms/ika_receiver.py` `hb_timeout=3.0`), rota kapısı (`NO_ROUTE` gelirse anında `send_vel(0,0)`). Sıfır-dışı her motor komutu `receiver.run_if_route_valid` kilidi altında gider (`receiver_korumali_hiz_gonder`).

**İki ayrı son tarih (K5, şartname §6.2):** bekleme 900 s (`SARTNAME_IHA_GOREV_SURESI_S = 15*60`, `codes/karar_sozlesmesi.py:1979`) ve sürüş 600 s (`SARTNAME_IKA_GOREV_SURESI_S = 10*60`, `:1980`). Sürüş saati izin geldiği an başlar; beklemede geçen süre sürüşten düşülmez. Çıkış kodları: 0 başarı · 1 rota gelmedi · 2 `NO_ROUTE` · 3 izin gelmedi · 4 süre doldu/HB'ye ulaşılamadı.

**K8 — `--yks host:port`:** UDP'de `OPEN_ROUTE` ACK'i yalnız gönderene (İHA) döner; hakem ekranı "İKA'ya aktarıldı" kanıtını görsün diye ACK kopyası YKS'ye yansıtılır. `OPEN_ROUTE` sahada `IKA_GO`'dan **önce** geldiği için adres `IKA_GO`'dan öğrenilemez; verilmezse hakem 2/2 onayı UDP'de **hiç açılmaz** (`ika_nav.py` argparse yardımı; `SAHA_RUNBOOK.md` §1 uyarısı).

### 1.3 Sürücü katmanı — `simulation/scripts/ika_surucu.py` (D-390 / T149)

Sözleşme (CONTRACTS §7.2): `hiz_ver(sag, sol) -> bool` (istisna sızmaz, arıza = False), `konum_al() -> (x,y,z,yaw)` ya da dörtlü `None`, `durdur()`, `saglikli()`. `ARDISIK_HATA_TAVANI = 3` (`ika_surucu.py:37`): 10 Hz'de ~0,3 s süren arıza "sürücü yanıtsız" sayılır, `navigate` son bir durdurma dener ve `False` döner.

Üç uygulama:
- `GazeboSurucu`: `gz topic -p ~/ika/vel_cmd -m "position { x: <sağ> y: <sol> z: 0 }"` subprocess'i (bayt-eş korunmuş, T141) ve `gz model -m ika -p` ayrıştırması.
- `SahteSurucu`: test; komut kaydı + poz dizisi + arıza enjeksiyonu.
- `GercekSurucu(arka_uc=None)`: **arka uç verilmeden kurulamaz**, `IkaSurucuHatasi("DONANIM_YOK …")` fırlatır (`ika_surucu.py:181-196`). Docstring "5 Eylül'de doldurulacak" der.

🔴 **Önemli, kolayca gözden kaçan bulgu:** Gazebo İKA modelinde `libDiffDrivePlugin.so` **kaldırılmıştır** (`simulation/models/ika/model.sdf:233-237`: "komutsuzken tekerleri 0 hıza FRENLİYOR … Sim'de aracı `navitas_anim` sürer; tekerler serbest döner"). `GazeboSurucu`'nun yazdığı `~/ika/vel_cmd` topic'ini **bugünkü modelde tüketen plugin yok**; depoda başka tüketici de bulunamadı (`grep vel_cmd` yalnız bu yorum satırlarını verdi). Kayıt videolarında İKA'yı hareket ettiren şey `simulation/plugins/navitas_anim.cc` kinematik plugin'idir (`simulation/docker/README.md` "Neden CLI kontrol yerine animasyon plugin'i?"). Sonuç: `ika_nav` → Gazebo kapalı çevrimi bugün **DOĞRULANAMADI**; `ika_nav`'ın mantığı `SahteSurucu` ve birim testleriyle (`tests/test_p3_ika_surucu.py`, FDR §3.3.4.1.13) kanıtlıdır, fizik simülasyonuyla değil.

### 1.4 Sürücü kabul turu — `scripts/ika_surucu_kabul.py` (K1–K6)

Docstring'den (satır 12–27): her adım GEÇTİ/DÜŞTÜ/ATLANDI + ölçülen değer.

| adım | ne | ölçüt |
|---|---|---|
| K1 | `durdur()` | `True` |
| K2 | `konum_al()` | 4'lü demet; hepsi `None` ise "KONUM YOK" uyarısıyla kabul (GNSS/odometri bağlanana dek), sayısalsa hepsi sonlu |
| K3 | hız rampası 0 → 0,30 m/s, 5 adım, adım arası 0,2 s (`RAMPA_HEDEF_MS`, `RAMPA_ADIM`, `RAMPA_ADIM_SURESI_S`, satır 82–84) | her adımda `hiz_ver(v,v)` `True`; ilk `False`'ta rampa **kesilir**; gerçek/gazebo'da "GÖZLE TEYİT ET" satırı basılır (yazılım hareketi ölçemez) |
| K4 | `durdur()` + `saglikli()` | ikisi de `True` |
| K5 | fail-closed (yalnız sahte) | 3 ardışık arıza → `saglikli()` `False`; 2'de hâlâ `True` |
| K6 | sağlık sıfırlama | başarılı `hiz_ver` sonrası `ardisik_hata == 0` |

Çıkış: 0 tümü geçti · 1 zorunlu adım düştü · 2 sürücü kurulamadı (`gercek` + arka uç yok = **Faz B öncesi beklenen durum**). Kullanım: `--surucu sahte|gazebo|gercek [--arka-uc modul:Sinif] [--json]`.

`FAZ_B_GUN_PLANI.md` §2 saat 15:00 satırı "İKA sürücü arka ucu doldur → `ika_surucu_kabul.py --surucu gercek`" der; 5–6 Eylül tutanaklarında (D-426, D-428) İKA'ya ait **tek satır yoktur**. Gerçek sürücüyle kabul turu **koşulmadı** (DOĞRULANAMADI değil — koşulacak donanım yok).

### 1.5 T149 doğrulaması

`TASK_QUEUE.md:6444`: `- [ ] **T149 — 🔴 İNSAN+MİMAR · Gerçek İKA motor sürücüsü ve konum kaynağı YOK: send_vel/get_pose yalnız gz alt süreci …** KRİTİK (şartname §2.2.5 "otonom hareket etmeyen İKA'nın görevi başarısız")`. Kutu **açık**. D-390 (`REVIEW_LOG.md:27141`) "P3/T149 KAPANDI" der ama kapanan kısım **soyutlama katmanıdır** (çökme yerine güvenli duruş); FDR açık kalem listesi bunu A1 olarak taşır (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2241`: "Gerçek İKA motor sürücüsü — Donanım tedarik edilmedi… gerçek arka uç yok"). **Doğrulandı: gerçek motor sürücüsü yoktur.**

---

## 2. Simülasyon (`simulation/`)

### 2.1 Altyapı

Gazebo Classic 11, **host'a kurulu değil**; her şey Podman konteynerinde (`simulation/KULLANIM.md` §0; `simulation/docker/Containerfile`, `record.sh`, `record_in_container.sh`). Ana kullanım video kaydıdır: `./docker/record.sh --seed 7` → `recordings/v<id>/navitas.mp4` (1280×720). `simulation/launch.sh` yalnızca `launch/navitas.launch`'a yönlendiren sarmalayıcıdır ve doğrudan `gzserver`/`gzclient` çağırdığı için **yalnız host'ta Gazebo varsa** çalışır (KULLANIM §0 notu). `PROVA_SENARYOSU.md` §0: ana geliştirme PC'sinde gz/WSL yok (2 Eylül ölçümü).

### 2.2 İki dünya üreteci (karıştırılmasın)

- `simulation/generate_world.py` (eski): tek HTAB, **duvarlı koridor**; `CORRIDORS` kolay 4,5 / orta 3,2 / zor 2,2 m (satır 26–30), `IKA_KB=(-22,-22)`, `HB_CENTER=(18,21)`, çıktı `worlds/navitas.world`. KULLANIM §5: "şartname 50×50 moloz sahası istiyor, uyumsuzluk düzeltilecek".
- `simulation/scripts/world_generator.py` (yeni, 599 satır): tek 300×300 İHA-UB içinde **3 zon** — `ZONE_POS` kolay (−90,0) · orta (0,0) · zor (+90,0) (satır 29). Zorluk (`DIFF`, satır 33–37): şerit genişliği 6/5/4 m, moloz sayısı 130/170/210, tıkama 2/3/3. `IKA_SPEED = 1.1` m/s, `SCAN_Z = 30` m tarama irtifası, İHA faz hızları `PHASE_SPEED` (tarama 10 m/s — şartnamedeki 40–45 m/s seyir intikal içindir, arena üzerinde uygulanmaz; yorum satır 44–47). `--layout clean|field`.

Geometri tek kaynağı `simulation/scripts/arena.py`: `UB=300`, `HTAB=50`, 5 harita × 3 senaryo = 15 deterministik saha (`HARITA_N=5`), yol omurgaları `KORIDOR` −16/0/+16 m, kıvrım genliği `WIND_AMP` 3/4,5/5,5 m, `KB_Y=-23`, `HB_Y=21`, `START_Z=0.21`. **Hangi yolun açık olduğu seed'den türetilir ve gizlidir** (docstring). `worlds/` altında 7 hazır dünya: `navitas.world`, `navitas_orta.world`, `navitas_zor.world`, `navitas_arena*.world` (3), `navitas_multi.world` (225 KB, 3 zonlu). Modeller: `models/{catapult,debris,iha,ika}`; plugin'ler `plugins/navitas_anim.cc` (hareket) ve `navitas_scan_cam.cc` (İHA nadir kamera, 1 Hz kare + poz logu).

### 2.3 Dürüst haritalama zinciri

`simulation/scripts/iha_haritala.py` docstring'i tasarımı özetler: Gazebo'da İHA 30 m'de serpantin uçar, `scan_camera` 1 Hz kare + plugin 1 Hz poz yazar → host `.venv`'de (1) kareler poz ve yaw'a göre döndürülüp **kuzey-yukarı ortomozaik**e oturtulur (`MOZ_PX=1024`, `MOZ_M=56` m → `MPP≈0,055` m/px, `HFOV=1.3` rad), (2) `iha_perceive._infer` mozaikte koşar, (3) piksel → HTAB-yerel metre → dünya, (4) `route.txt`, `detection.json`. Docstring'in vurgusu: "**Model yanılırsa İKA yanlış/kapalı yola gider ve fizik onu durdurur — SONUÇ DÜRÜSTTÜR.** (Eski akış… sahte.)" `iha_perceive.py` ağırlığı `config/model_registry.json`'dan okur; kayıt defteri yoksa ad **uydurulmaz** (fail-closed, `varsayilan_model_yolu`).

### 2.4 Puanlama — `simulation/score.py`

Docstring "Şartname V2 (13.04.2026) formülü" der. Formül (satır 74–98):

```
C      = C_ceza + sapma_metre×5 + (manuel_paraşüt ? 50 : 0)
Puan2  = K_zorluk × ( P_gorev + (25000−m_iha)/10 + (900−t_iha)/5 + (900−t_hazirlik)/30
                      + (10000−m_ika)/15 + m_yuk×0,01 + (600−t_ika)/15 − C )
Puan1  = 0,10·ODR + 0,25·DDR + 0,55·FDA + 0,10·UHDR
P      = P_TI + P_ucus + P_centilmenlik          (100/50/0 · 200 · ≤50)
TOPLAM = 0,65·Puan2 + 0,20·P + 0,15·Puan1
```

`K_zorluk` 1,0 kolay / 1,5 orta / 2,0 zor; `P_gorev` 600 (HB'ye ulaştı) ya da 0. Geçersizlik kontrolleri (`gecerlilik_kontrol`): İHA > 25 kg, İKA > 10 kg, İHA süresi > 900 s, İKA > 600 s, hazırlık > 900 s. Dört örnek senaryo (`hedef_zor`, `hedef_orta`, `inis_sapma`, `basarisiz`). Bu formülün bugünkü şartname PDF'iyle birebir örtüştüğü bu belge için **DOĞRULANAMADI** (PDF okunmadı; betik 13.04.2026 sürümüne atıf yapar).

### 2.5 Hakem logu — `simulation/scripts/hakem_log.py`

Simülasyon için **metin** logu (`--out … hakem_log.txt`, `Log` sınıfı `[T+ss.ss] ETİKET mesaj`). Gerçek UDP loopback comms ile üretilir: `IhaSender.send_open_route` → `IkaReceiver` + sahte YKS thread'i ACK döner. Model künyesi (`_model_kunyesi`) elle yazılmaz: kayıt defterindeki ağırlığın adı, sha256'nın ilk 8 hanesi ve `rpi_inference.INFER_SIZE` **koşan modelden türetilir** (D-21 ailesi; yorumlar satır 40–60). Sonuç dürüsttür: model kararı `arena.open_road(level, harita_id)` ground-truth ile karşılaştırılır; yanlışsa "İKA kapalı koridorda molozda DURDU — BAŞARISIZ (P_görev=0)". `--realtime 1` `mission_time` ile 15/15/10 dk limitlerini basar. Uyarı: "GNSS+IMU+encoder … PID" satırı (satır 199) anlatıdır (§1.1).

`simulation/PROVA_SENARYOSU.md` görev zincirinin 8 fazını (fırlatma → tarama → tespit → YKS aktarım + onay → İKA'ya aktarım havadayken → iniş kanıtı → IKA_GO → HB teması < 0,3 m) hakem_log damgalarıyla tanımlar; "**Sim kanıtı saha kanıtı DEĞİLDİR** (CONTRACTS 11.1)" (§4).

### 2.6 Ne kadarı gerçek donanımla eşleniyor?

| katman | sim | gerçek | eşleme |
|---|---|---|---|
| Protokol/mesajlar | `comms/protocol.py`, `ika_receiver.py`, `iha_sender.py` | aynı dosyalar (mühür listesi `YKS_IKA`) | **birebir** |
| İKA karar mantığı | `ika_nav.py` | aynı dosya | **birebir** (`SahteSurucu` testleri) |
| İKA motor/konum | `GazeboSurucu` (topic'i tüketen plugin **yok**, §1.3) | `GercekSurucu` **boş** | **eşlenmiyor** |
| İHA algısı | `iha_perceive._infer` (aynı model) | `codes/rpi_inference.py` | model aynı, kamera/mozaik farklı |
| Fizik/geometri | `arena.py` 15 saha, mesh'siz kutular | Adıyaman 20×20 m FDA alanı | **eşlenmiyor** (FDR: "CAD değil", `ACIK_KALEMLER.md:51` #16 3B görev icra simülasyonu yeniden açıldı) |
| Puanlama | `score.py` | hakem | formül takımın okuması |

---

## 3. YKS — operatör/hakem ekranı (`comms/yks_gui.py`)

### 3.1 Ne gösterir (`SAHA_RUNBOOK.md` §2 operatör kartı)

- **HAM GNSS** satırı: canlı Pixhawk telemetrisinden enlem/boylam, fix, uydu, bağıl irtifa; bayat alan silinir. Uyarı: kalibre edilmiş arena dönüşümü olmadığı için bu **semantik harita konumu değildir**.
- **KAMERA**: Jetson RAW hakem görüntüsü (`http://<JETSON_IP>:8080`, `/kare.jpg`, `/durum`); `CANLI` + kare yaşı görünmeden güncel sayılmaz; `KARE_BAYAT` / `KAYNAK_KAPALI` / `BAĞLANAMADI` durumları. Video **SiK üzerinden taşınmaz**, ayrı Wi-Fi/LAN.
- **A** = ARM/DISARM: düğme yalnız taze Pixhawk heartbeat'iyle açılır; ekran ancak Pixhawk ACK **ve** yeni heartbeat aynı durumu gösterince ARM/DISARM yazar. Uçuşta DISARM iki adımlı teyit (T180).
- **FIRLATMA** yalnız ARM'dayken damga atar (D-393).
- **PARAŞÜT (manuel −50)**: iki adımlı; ACK gelene dek tekrarlar; ACK yoksa KIRMIZI.
- **R** = onay sıfırlama; **İKA BAŞLAT**: yalnız `IHA_LANDED` + hakem onayı sonrası (§2.2.5 kilidi).
- Tespit tazeliği: `YKS_TESPIT_TAZELIK_S = 5.0` s (`codes/karar_sozlesmesi.py:159`); tespit yaşı `HEARTBEAT`'te taşınır (`FDA_PLANI_20260829.md` A2 kararı).

### 3.2 Hangi kanıtları kaydeder — `hakem_log.jsonl`

`comms/hakem_kaydi.py`: her kayıt bir UTF-8 JSON satırı, **`flush` + `fsync`** ile diske itilir; dosya açılamazsa kurucu yükseltir (YKS **kanıtsız başlamaz**); koşarken yazma bozulursa kalkış/hakem onayı kapanır, ARM ve acil komutlar açık kalır (`SAHA_RUNBOOK.md` §1). Varsayılan yol `results/prova/<YYYYMMDD_HHMMSS>_<pid>/hakem_log.jsonl` (`varsayilan_hakem_log_yolu`), `--hakem-log` ile değiştirilir (`yks_gui.py:4372-4463`). Ortak alanlar: `v`, `ts` (ISO-8601 ms), `monotonic_s`, `oturum`, `olay`.

Olay kümesi (`CONTRACTS.md` §6.8, `yks_gui.KANIT_OLAYLARI`): `OTURUM_BASLADI/BITTI`, `YKS_ARAYUZ_HAZIR`, `ROTA_ALINDI` (seq, road, label, conf, waypoint, ankor), `ROTA_REDDEDILDI` (güven eşiği; ACK üretilmez), `ROTA_YOK`, `ACK_ALINDI`, `IKA_AKTARIM_KANITI` (K8), `HAKEM_ONAYI_1`, `HAKEM_ONAYI_2` (`fda_kipi`, dayanak), `HAKEM_ONAYI_REDDI` (`ANKOR_YOK` · `BAYAT_TESPIT` · `IKA_ACK_KANITI_YOK`), `IHA_INIS_KANITI`, `KAMERA_KANIT` ve `TELEMETRI_KANIT` (kenar olayı; değişmezse 30 s'de bir "hâlâ aynı" satırı = süreklilik kanıtı), `ACIL_SENARYO`, `KRONOMETRE_BASLADI/BITTI` (iha/ika/hazirlik, limit_s, asim), `UI_OLAYI`. `HEARTBEAT` başına satır yazılmaz.

### 3.3 `--fda` kipi (CONTRACTS §6.7, D-407)

Görev test uçuşu (çoklu rotor, 20×20 m, ≥30 m, ≤10 dk, İKA/paraşüt/mancınık **yok**) yarışma günü görevinden farklıdır. `--fda` verildiğinde:

| konu | yarışma kipi | FDA kipi |
|---|---|---|
| İHA süre bütçesi | 900 s | 600 s (`SARTNAME_FDA_OPERASYON_SURESI_S`, `karar_sozlesmesi.py:1994`) |
| hakem onayı 2/2 | İKA `OPEN_ROUTE` ACK kanıtı şart | **İKA kanıtı aranmaz**; dayanak = YKS'de canlı görüldü + hakem onayı; ACK İHA'ya `ref_tip` ile gider |
| PARAŞÜT | manuel yedek | **kapalı**, komut gönderilmez |
| FIRLATMA | mancınık damgası | etiket **KALKIŞ**, kronometre başlar, ARM kilidi aynen |
| İKA BAŞLAT | §2.2.5 zinciri | **kapalı**, `IKA_GO` gönderilmez |
| `IHA_LANDED` | zorunlu | **aynen zorunlu** |

Kilit: `tests/test_faz_b_yks_fda_kipi.py` (9 test, 4/4 mutant). Açılış: `scripts/saha_baslat.py yks --fda --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080`; `--fda` yalnız `yks` kipinde (`saha_baslat.py:81-82`). `--iha` verilmezse PARAŞÜT/ARM komutları `rpi_inference`'ın efemer portuna gider, alıcıya **hiç ulaşmaz** (D-403 KRİTİK-1; `IHA_EKSIK_UYARISI`). Portlar: YKS 5005, İKA 5006, İHA komut alıcı 5007.

---

## 4. Pixhawk 6C / ArduCopter

### 4.1 Firmware: **4.5.7 sabit** — neden 4.7 değil (D-425)

5 Eylül 14:52'de Mission Planner'ın quadcopter ikonu "en son kararlı" olan **4.7.1**'i yükledi; `arducopter_fda.param` yüklenince MP "**Missing 9 params**" dedi (`REVIEW_LOG.md:29713`). Sebep Copter-4.7 SI birim reformu: `SR1/SR2_POSITION`/`EXTRA3` → `MAV1/2_*`; `RTL_ALT` (cm) → `RTL_ALT_M`; `LAND_SPEED` (cm/s) → `LAND_SPD_MS`; `WPNAV_SPEED` 300 cm/s → `WP_SPD` m/s (300 kalırsa **300 m/s**); `ARMING_CHECK` → `ARMING_SKIPCHK` **anlam ters**. Karar (B): parametre dosyası, kapısı (`tests/test_faz_b_pixhawk_sablon.py`, 12 test) ve TEYİT listesi 4.5 anlambilimine yazılı ve ölçülü; uçuşa 16 gün kala ölçülmemiş bir 4.7 portu yerine 4.5.7. 15:08'de 4.5.7 flash edildi (`Messages: ArduCopter V4.5.7 (2a3dc4b7)`, D-426). İndirici `scripts/pixhawk_firmware_indir.py:74` `SURUM = "stable-4.5.7"`, board_id 56 kapısı; `arducopter.apj` 1.585.371 B. Kural: "**beyan edilen bağımlılık zorlanır**" (D-425 §6). Not: Pixhawk 6C fabrikadan **PX4** ile gelir (D-424).

### 4.2 Parametre dosyası mantığı — `config/pixhawk/arducopter_fda.param`

Mission Planner `.param` biçimi (`AD,DEGER`, `#` yorum). Her parametrenin üstünde **NEDEN** yorumu zorunlu (test zorlar); `# TEYIT:` işaretli parametreler README §3 listesiyle metin kilidi altında. Değer tabloları ArduPilot Copter-4.5 kaynak dosyalarından okundu (başlık, satır 203–208). Dosyada olmayan her parametre firmware varsayılanında kalır. Kritik satırlar:

| grup | parametre = değer | neden (kısa) |
|---|---|---|
| gövde | `FRAME_CLASS,1` `FRAME_TYPE,1` | Quad, X |
| motor | `MOT_PWM_TYPE,0` `RC_SPEED,400` | PWM; ESC Skywalker 60A V2 50–432 Hz (kart 6 Eyl dökümünde **490**'daydı, `arducopter_fda_20260906.param:659`) |
| çıkışlar | `SERVO9..12_FUNCTION = 36,34,33,35` | AUX1–4 = M4 (sağ arka), M2 (sol arka), M1 (sağ ön), M3 (sol ön) — 6 Eylül dökümünde ÖLÇÜLDÜ (satır 918/848/853/858) |
| çıkışlar | `SERVO1..8, 13..16 = 0` | dökümde boş çıkışlara başıboş motor fonksiyonu atanmıştı (D-428 §5d) |
| MAVLink | `SYSID_THISMAV,1` `SERIAL1/2_PROTOCOL,2` `SERIAL1/2_BAUD,57` `BRD_SER2_RTSCTS,0` | TELEM1 SiK 57600, TELEM2 Jetson 57600, 3 telli UART |
| akış | `SR1_POSITION,4` `SR1_EXTRA3,1` `SR2_POSITION,8` `SR2_EXTRA3,2` | `MAVLINK_KONUM_ASGARI_HZ=4`, `MAVLINK_DURUM_ASGARI_HZ=1` (`karar_sozlesmesi.py:2201,2205`) ×2 pay |
| RC | `RC_PROTOCOLS,4` | yalnız iBUS |
| pil | `BATT_MONITOR,4` `BATT_LOW_VOLT,14.4` `BATT_CRT_VOLT,14.0` `BATT_FS_LOW_ACT,2` (RTL) `BATT_FS_CRT_ACT,1` (Land) | 4S 3,60/3,50 V hücre |
| failsafe | `FS_THR_ENABLE,1` (RTL) `FS_GCS_ENABLE,1` (RTL) | |
| çit | `FENCE_ENABLE,1` `FENCE_TYPE,3` `FENCE_ALT_MAX,50` `FENCE_RADIUS,60` `FENCE_ACTION,1` | irtifa + daire; poligon sahada çizilince 7 |
| RTL/iniş/hız | `RTL_ALT,3500` (35 m) `LAND_SPEED,50` (0,5 m/s) `WPNAV_SPEED,300` (3 m/s) | |
| arm/log | `ARMING_CHECK,1` `LOG_BITMASK,176126` | tüm kontroller; .bin log = FDR kanıtı |

Bilinen risk (README §5): `EXTENDED_SYS_STATE` hiçbir `SR*` akışında yok, yalnız `SET_MESSAGE_INTERVAL` ile akar ve Pixhawk reboot'unda silinir → her pil değişiminden sonra `jetson_baslat.sh --kapi` tekrar.

### 4.3 6 Eylül gerçek dökümü — `arducopter_fda_20260906.param` (20:22, 1025 parametre)

5 Eylül dökümü **hiç alınmadı** (D-428 §5g). Bu dökümde şablondan sapanlar ve kritik değerler:

- **Failsafe:** `FS_THR_ENABLE,3` (Land — şablon 1 RTL; "kimse bilmeden değişmiş", D-428 §5b), `FS_THR_VALUE,975`, `FS_GCS_ENABLE,1`, `FS_GCS_TIMEOUT,5`, `FS_OPTIONS,16`, `FS_CRASH_CHECK,1`, `FS_EKF_ACTION,1`, `FS_VIBE_ENABLE,1`, `FS_DR_ENABLE,2`. D-429 §4 tlog'dan `FS_GCS_ENABLE=5` okuduğunu yazar; döküm 1 diyor — **çelişki, DOĞRULANAMADI** (döküm 20:22, tlog 21:56'ya kadar; sonradan değişmiş olabilir).
- **Pil:** `BATT_FS_LOW_ACT,1` (Land — şablon 2), `BATT_FS_CRT_ACT,1`, `BATT_LOW_VOLT,14.4`, `BATT_CRT_VOLT,14`, `BATT_VOLT_MULT,18.18`, `BATT_AMP_PERVLT,36.36` (multimetre 15,8 V = MP 15,8 V, D-428 §1), `BATT_CAPACITY,3300` — plan "4S 10 Ah" der (`SAHA_HAZIRLIK_PLANI_20260903.md:47`); 3300 mAh **uyumsuz, DOĞRULANAMADI** (varsayılan kalmış olabilir).
- **Paraşüt:** dökümde yalnız `CHUTE_ENABLED,0`; başka `CHUTE_*` yok (kapalıyken gizlenir).
- **RC:** `RC1..16_OPTION` hepsi **0**; `RC_PROTOCOLS,1`; `RC_SPEED,490`; `FLTMODE_CH,5`; `FLTMODE1-3 = 0` (Stabilize), `FLTMODE4 = 5` (Loiter), `FLTMODE5 = 0`, `FLTMODE6 = 9` (**Land**); `ARMING_RUDDER,2`; `DISARM_DELAY,10`.
- **Motor:** `MOT_THST_HOVER,0.35` (öğrenilmemiş varsayılan), `MOT_SLEW_UP_TIME,0`, `MOT_SPIN_ARM 0.1`, `MOT_SPIN_MIN 0.15`, `MOT_SPIN_MAX 0.95`.
- **Akış:** `SR1_POSITION,2` `SR1_EXTRA3,2` (şablon 4/1 — MP'nin "Telemetry Rates" isteğinin RAM'i ezmesi hipotezi, D-428 §5e), `SR2_POSITION,8` `SR2_EXTRA3,2` (şablonla aynı).
- **Kalibrasyon:** `INS_ACCOFFS` (0,018 / 0,003 / −0,291), `AHRS_TRIM_Y = −0,0257` rad (−1,5°), `COMPASS_DEV_ID3,0` (Mag3 yok), `LOG_DISARMED,0` (arm'sız motor koşuları **loglanmaz** — `SAHA_OLAY_SONRASI_MUAYENE.md` madde 0).

### 4.4 FDA görevi — `config/pixhawk/fda_gorev.waypoints`

`QGC WPL 110`, 8 satır (README §1 tablosu):

| # | komut | değer |
|---|---|---|
| 0 | HOME (16) | yer tutucu 0,0 |
| 1 | `NAV_TAKEOFF` (22) | **32 m** göreli — şartname ≥30 m + 2 m baro/EKF payı; `rpi_inference` 30 m altını `ASGARI_IRTIFA_ALTI` işaretler (`SARTNAME_ASGARI_IRTIFA_M = 30`, `karar_sozlesmesi.py:339`) |
| 2–5 | `NAV_WAYPOINT` ×4 | 20×20 m karenin köşeleri `±0.0000898315°` (= ±10 m), 32 m — **tek pas** |
| 6 | `NAV_LOITER_TIME` (19) | **60 s** — YKS'ye canlı aktarım + iki aşamalı onay + ACK penceresi |
| 7 | `NAV_LAND` (21) | |

Kaba süre: kalkış ~15 s + pas ~30 s + loiter 60 s + iniş ≤ 60 s ≈ **3–3,5 dk ≪ 10 dk**; test P7 kötü durum 221,5 s (`SAHA_HAZIRLIK_PLANI_20260903.md` 1.6). Sahada değişecek **tek şeyler**: koordinatlar (home + köşeler), fence poligonu, kalibrasyonlar, tarihli döküm (README §2). Şablon Null Island'dadır (0°,0°); Adıyaman'da kaptan gerçek köşeleri girer.

### 4.5 Paraşüt

- FDA görev uçuşunda **paraşüt yok** (çoklu rotor; CONTRACTS §6.7). Dökümde `CHUTE_ENABLED,0`.
- Yarışma zinciri hazır: YKS PARAŞÜT → `comms/iha_komut_alici.py` → `COMMAND_LONG DO_PARACHUTE` → yalnız `COMMAND_ACK ACCEPTED`'da YKS'ye ACK (D-393). Prova için `FAZ_B_GUN_PLANI.md` §2 13:30 satırı: `CHUTE_ENABLED=1`, `CHUTE_ALT_MIN` prova için 0 (uçuşta ≥10 m varsayılanı alçakta reddeder, §4b), servo **bağlı değilken**. Bu prova 5–6 Eylül'de **koşulmadı** (D-426/428'de yok).
- Manuel paraşüt cezası −50 (`score.py:78-79`). Sabit kanat + mancınık + paraşüt **final** işidir (`SAHA_HAZIRLIK_PLANI_20260903.md` §7).

### 4.6 Failsafe'ler — tasarım ve ölçüm

| failsafe | şablon | 6 Eyl döküm | ölçüm |
|---|---|---|---|
| RC (`FS_THR_ENABLE`) | 1 = RTL | **3 = Land** | 🔴 **DÜŞTÜ** (D-428 §2): kumanda kapatılınca barlar sabit kaldı, `Radio Failsafe` gelmedi — FS-iA6B iBUS'ta **son değerleri tutuyor**. Şablon yorumundaki "iBUS alıcısı çerçeve basmayı keser" varsayımı **yanlışlandı**. Çare: kumandada `RX Setup → Failsafe` (CH5 → Land, CH3 gaz altta); test ölçütü: TX kapanınca CH5 Land'e zıplar, HUD `Land`. Sabah tekrarı depoda **DOĞRULANAMADI** |
| Pil | LOW 14,4 V → RTL; CRT 14,0 V → Land | LOW → **Land** | gerilim ölçeği doğrulandı (±0,1 V) |
| GCS (`FS_GCS_ENABLE`) | 1 = RTL, 5 s | 1 (tlog: 5?) | Jetson'daki MAVProxy sysid 255 heartbeat bastığı için SiK kopsa da **tetiklenmez**; anlamı "Jetson-bağlantı failsafe'i" (D-406 C, README §4). Hop için 5 (Land) istendi — 35 m RTL tırmanışı gece 1 m hop'ta kabul edilemez |
| Çit | irtifa 50 m + daire 60 m | aynı | poligon Adıyaman'da |
| EKF/Crash/Vibe | varsayılan | 1/1/1 | — |

Mimar kararı bekleyenler (`DEVAM.md` §3): 30 m görev için şablon (RTL) mı, kart (Land) mı; `RC_PROTOCOLS` 4'ün iBUS çözmediği **kanıtlanmadı** (TX pili + fiş karıştı, D-428 §5a).

### 4.7 RC6_OPTION sorunu (D-433)

"Kumandadan arm/disarm olmuyor" tlog ile çözüldü (`results/ucus_loglari/20260906/2026-09-06 19-52-44.tlog`, `scripts/ucus_tlog_arm.py`): CH6 akşam boyunca **56 kez** çevrildi, ±3 s içinde **hiç** arm/disarm geçişi yok — sinyal kontrolcüye ulaşıyor; ama `RC6_OPTION=0` (hiçbir işlev atanmamış; şablonda da `RCx_OPTION` yok — anahtarla arm **hiç planlanmamıştı**). Çare tek parametre: `RC6_OPTION=153` (Arm/Disarm) — **öneri, uygulanmadı**. Dümenle arm (`ARMING_RUDDER=2`) **çalışıyor**: gaz ≤1030 PWM (RC3_MIN 1000 + DZ 30) ve yaw ≥~1947, **2 s**; 21:36:25'te gaz 1003'e inince 2 s sonra ARMED. 15 s boyunca gaz 1043–1107'de tutulduğu için "olmuyor" sanıldı. `DISARM_DELAY=10` yerde otomatik disarm. Yan bulgu: CH5 üst konum `FLTMODE6=9` **Land**; FDR Bölüm 3 "Stabilize/Loiter/RTL" beyanıyla **uyuşmuyor** (RTL isteniyorsa 6).

### 4.8 ESC / motor künyesi

- **ESC:** plan "80 A DShot ×4" dedi (`SAHA_HAZIRLIK_PLANI_20260903.md:39`); kutudan **Hobbywing Skywalker 60A V2** ×4 çıktı (etiket BEYAN, D-428 §1), BEC 5 V/5 A, 3 telli fiş; Pixhawk ile gelen PWM IN/OUT adaptörü üzerinden **AUX 1–4**. Gaz sinyali 50–432 Hz → `RC_SPEED` 490→400. 4 BEC paralel: 3 kırmızı tel çıkarılacak (D-428 §5f, ertelendi). Kalibrasyon yordamı (README §2.1, D-428 §3): "hepsi birden" iki kez tutmadı; tutan sıra: `POWER1` fişi çıkarılmış + pil yok → Pixhawk yalnız USB'de MP passthrough → düğme → **sonra** pil → yüksek gaz tonu → 2 bip → gaz alta → uzun bip. "5'te 5" **beyan**, video yok.
- **Güç modülü:** plan PM02, gerçek **PM06** (D-426 §3); 8 pinli kablo `POWER1`'e uymadı, 6 pinli bulundu.
- **Motor değişikliği (D-435):** 5008 340KV ×4 + 12×10 pervane **iade edildi**; araçta **SunnySky X2220-III KV980 (V3)** ×4 (BEYAN, etiket fotoğrafı yok) + **10×4,5 (1045)** pervane + 4S; motorlar 2 yıl önce kullanılmış. Veri sayfası ölçümü: 3–4S, **maks. sürekli 38 A / 30 s**, 4S+APC1047 tam gaz 2130 g @ **38,4 A** (sınırın üstünde, "90 ℃ 1 min"); 1045 satırı hiçbir sayfada **yok**. Montaj deseni 16×19 mm; kol delikleri 5008 (Ø25) için tasarlandı — nasıl monte edildiği **DOĞRULANMADI**. Depoda 12 dosya hâlâ 5008 der (T211 ile düzeltiliyor). Toplam kütle **ÖLÇÜLEMEDİ** (T10); itki bütçesi tartıdan önce seçilemez.
- **M1 (sağ ön) hasarlı** (D-429 §2 madde 4): P20'de 25 s boyunca 1949 PWM'de doygun, duman attı; "sağlam diyelim" beyanı geçersiz.
- **D-436 — "V3115 900KV" önerisi:** SunnySky'da böyle motor **yok**; V3115 KV900 **T-Motor VELOX** (sinematik FPV): 4S tam gaz 2820 g / 47,1 A, sınır 51,1 A/60 s ve 83 A/10 s → X2220'nin aksine sınırın altında; 2 pal 1045 verisi yok; montaj Ø19 (X2220 ve 5008'le uyuşmaz → kollar yeniden basılır/adaptör). Marka teyidi olmadan sipariş yok; motor değişimi D-434 (a) ailesini (itki asimetrisi) kapatır, (b) ailesini (CG/kol/ayak geometrisi) **kapatmaz**.

---

## 5. Saha yordamı

### 5.1 Takvim (iki tarih karıştırılmaz)

`SAHA_HAZIRLIK_PLANI_20260903.md` §0.1: **21.09 17:00 FDR son teslim** + aynı gün **Adıyaman provası** (hakem yok); **30.09–03.10 resmî Drone ile Görev Test Uçuşu** (tek atış, hakem önünde). CONTRACTS §6.7 başlığı aynı tarihleri verir. `FDA_PLANI_20260829.md` (29 Ağustos) "21–25 Eylül, uçuş 23–25" der — **eski**; 3 Eylül planı geçerlidir. FDA ağırlığı `FDR × 0,85 + Test Uçuşu × 0,15` (`FDA_PLANI_20260829.md` §0.2; kaynak TEKNOFEST duyurusu, bu depodan **DOĞRULANAMADI**). Test uçuşu ikilidir: yanlış güzergâh ya da süre aşımı = 0.

### 5.2 `SAHA_RUNBOOK.md` — adım adım, kim ne yapar

**§0 Sahaya çıkmadan (PC'de, her seferinde — AI/yazılım rolü):**

| ne | komut | ölçüt |
|---|---|---|
| Genel kapı | `<venv> -B codes/test_rota_sentetik.py` | 15/15 |
| Test paketi | `<venv> -B -m unittest discover -s tests -q` | OK |
| Kuru koşu | `<venv> -B scripts/saha_kuru_kosu.py --cikti results/saha_kuru_kosu_<tarih>` | kopuk halka yalnız `motor` |
| Paket aynası | `<venv> scripts/jetson_paket_hazirla.py` | "hepsi senkron" |
| Model pakette | `ls jetson_paket/models/` | `navitas_seg_v36_best.pt` **ve** `_512_fp16.onnx` |
| H3 video | `<venv> drone/test_uctan_uca.py --hizli` | exit 0 (genel kapıda değil) |

**§1 Açılış kartı (hazırlık ≤ 900 s, her 30 s +1 puan) — istasyon başına tek komut:**
- YKS rolü: `saha_baslat.py yks --fda --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080` (SiK'te `--serial COM5 --baud 57600`); yarışma günü yalnız `--fda` çıkarılır.
- İKA rolü: `saha_baslat.py ika --yks <YKS_IP>:5005` (UDP'de `--yks` **fiilen zorunlu**, K8).
- Jetson rolü: `jetson_baslat.sh` (§6).

**§3 İHA/Jetson:** önce çoğullayıcı (seri Pixhawk tek sahipli); `iha_komut_alici --izinli-kaynak <YKS_IP>:5005` **zorunlu** — verilmezse süreç argparse çıkış 2 ile hiç kalkmaz, zincir "yarı canlı" görünür. 🔴 `YKS_IP` `/etc/navitas.env`'de **elle beyan**; dizüstünün gerçek adresi farklıysa alıcı tüm ARM/DISARM/RTL/LAND/PARAŞÜT komutlarını **yalnız Jetson tarafında loglayarak** reddeder; YKS'de uyarı çıkmaz. Kapı: `ipconfig`/`ip -4 addr` ↔ `grep YKS_IP /etc/navitas.env` eşit; teşhis `journalctl -u navitas-komut -n 30 | grep "kaynagi RED"`. DHCP rezervasyonu/statik IP saha gününden önce.

**§4 Tekrar fırlatma:** `saha_baslat.py --reset` yordamı yazdırır: YKS'de R + gerekirse ARM; İKA süreci **öldürülmez**; Jetson yeniden başlatılmaz; kronometre yeni fırlatmada damgalanır; araca fiziksel müdahale yok (−100).

**§6 21 Eylül kesin-hazır kapısı (10 fiziksel madde):** Pixhawk üç MAVLink tüketicisi, GNSS canlılığı (anten kapatılınca alan kaybolmalı), ölçek/irtifa (`OLCEK_YOK`), ARM (ACK + heartbeat), DISARM (havada iki teyit), kamera ≥10 dk canlı, kamera kopma/yakalama, ağ ayrımı (SiK'te video yok), E-stop/paraşüt ACK ve red yolları, kayıt tek klasörde. "Bir madde düşerse uçuşa çıkılmaz."

### 5.3 Kuru koşu — `scripts/saha_kuru_kosu.py`

Gazebo'suz, ROS'suz, donanımsız uçtan uca zincir denetimi. CONTRACTS §11'deki **on halka** sırayla: `kamera, model_yukleme, cikarim, maske, olcek, hedef_konumu, rota, aktarim, surus_izni, motor` (satır 51–54); her biri GEÇTİ/DÜŞTÜ/SAHİPSİZ/ATLANDI; **düşen halkada durmaz** (amaç tüm kopuklukları aynı koşuda görmek). İkameler: kamera → `data/kuru_kosu_fikstur` (kare + o karenin mpp'si, T38), aktarım → loopback UDP, motor → çağrı sayan sahte sürücü. Halka `simulation/` altındaysa **SAHİPSİZ** sayılır (§11.1). Son ölçüm: **9 GEÇTİ / 1 SAHİPSİZ (`motor`)** (3 Eylül, `SAHA_HAZIRLIK_PLANI_20260903.md` 1.9; FDR §3.3.1.3.1 tablosu).

### 5.4 Kontrol listeleri (nerede ne var)

- `FAZ_B_GUN_PLANI.md` §0 cuma listesi (8 madde), §2 saat sırası (Jetson → engine → FPS → çoğullayıcı → `mavlink_dogrula` → iniş kanıtı → paraşüt/ARM provası → SiK RF → İKA sürücü → İKA zinciri → sabit kanat → kapanış).
- `SAHA_HAZIRLIK_PLANI_20260903.md` §2.1–2.6 montaj/kablolama/yapılandırma, §3 uçuş testleri 3.1–3.7, §5 "KESİN HAZIR", §6 21 Eylül dakika akışı.
- `jetson_paket/GUN1_KONTROL_LISTESI.md`, `config/pixhawk/README.md` §3 TEYİT listesi.
- `SAHA_OLAY_SONRASI_MUAYENE.md` — 15 madde (kanıt dondurma/DataFlash, motorlar, ESC, pervaneler, somun/vida, kollar, gövde, Pixhawk montajı, GPS direği, kablolar, pil/CG, RC/failsafe, kademeli yeniden güç verme, olay tutanağı). Kural: **madde 0–12 geçmeden güç verilmez**; önceden depoda olay-sonrası yordam sıfır satırdı.

### 5.5 5–6 Eylül saha günlerinde ne oldu

**5 Eylül (D-426, `REVIEW_LOG.md:29811`)** — operatör sahada tek (Halil), mimar uzaktan; kanıt = MP `Messages` satırı. Kronoloji: 14:52 4.7.1 flash (9 eksik param) → **15:08 4.5.7** (`Frame: QUAD/X`) → 15:38 GPS `u-blox … SPG 5.10` → 16:18 RC bind FS-i6↔FS-iA6B (beyan) → 18:03 `RCInput: decoding IBUS(1)` (alıcı yanlışlıkla **CH6**'ya takılıydı, `i-BUS SERVO` portuna alınınca çözüldü) → 18:03 PM06→POWER1 (6 pinli kablo) → 18:05 emniyet düğmesi → 18:06 motor testi (%5'te dönmedi, %10–15'te döndü) → ~18:30 motor sırası/yönü 4/4 (**beyan, video yok**) → ~18:45 SiK bağlandı (beyan). `RC_PROTOCOLS` 4→1 yapıldı, geri alınmadı. Künye üç yerde yanlış çıktı (ESC 60 A, PM06, FS-iA6B teyit). 18:5x "uçalım" → **reddedildi** (plan Paz sabah, ESC kal yok, failsafe yok, alacakaranlık). 5 Eylül parametre dökümü **alınmadı**.

**6 Eylül akşam (D-428, `REVIEW_LOG.md:29939`, 18:30–20:50)** — operatör kimliği belirsiz ("Halil" → "Emir'dim"). Ölçümle kapananlar: sürüm 4.5.7; "önce" dökümü 18:37 (28/31 uyan, 0 eksik; sonra üzerine yazıldı); pil 15,8 V = 15,8 V; accel/level **gerçekten** yapıldı (5 Eylül beyanı yanlıştı — flash sıfırlamıştı); ESC künyesi; ESC kalibrasyonu 3. denemede; pusula ×2 (ofsetler < 300); GPS 18 uydu, EKF3 GPS kullanıyor. 🔴 **RC failsafe ölçüldü ve düştü** (§4.6). Kumanda TX pili bitti → iki kez "kumanda gitti". Bilinçsiz değişen `FS_THR_ENABLE` 1→3, `BATT_FS_LOW_ACT` 2→1. Döküm 20:22 repoya (`arducopter_fda_20260906.param`, sha256 `4acc4476…`). Uçuş üç kez istendi, **reddedildi**; "pervane takılmadı, arm edilmedi".

**6 Eylül gece (D-429, `REVIEW_LOG.md:30061`, 20:45–21:34)** — D-428 oturumu kapandıktan sonra **başka bir oturum**, birbirinden habersiz (yordam kusuru → "tek aktif saha oturumu" kuralı). tlog `results/ucus_loglari/20260906/2026-09-06 19-52-44.tlog` (17,98 MB): 41 arm penceresi, 26 gerçek arm; **pervaneli üç devrilme**: P19 20:56 (gaz 1002→1446→1656 0,8 s içinde, pitch −0,7→**−43,8°**), P20 21:00 (32 s, M1 1949'da doygun ~25 s, M2 1150 tabanda, roll +8…+17°), P26 21:33 (gaz 1079→**2000** 0,5 s'de, pitch −36,9°). Hüküm: FC doğru yönde düzeltti (ön motorlara daha yüksek komut), mixer/yönelim ters değil; **fiziksel ön itki komut edilen itkiyi üretmedi**; ilk asimetri komut eşitken oluştu → CG önde / arka itki > ön / ön ayak takılması; **M1 hasarlı**; gaz "adımla" verildi (hover ~%35 varsayılan, %65–100'e 0,2–0,6 s'de sıçrama). Kurallar: kalkış = ≥2 s rampa, `MOT_SLEW_UP_TIME` 0→1,0 s; motor yönü videosuz "doğru" sayılmaz; olay = önce log (.bin indir). D-434: pilot kolu merkezdeydi (1500/1502), seviye temiz → kalan iki aile: (a) itki asimetrisi (ESC uç noktası, zayıf ön motor/ESC), (b) CG/geometri (kol 1–2 %15 grid/2 duvar, kol 3–4 %40 gyroid/6 duvar asimetrisi, `SAHA_OLAY_SONRASI_MUAYENE.md` madde 6).

**Jetson (D-431, 6 Eylül):** kart "Nano 4GB / JetPack 4.6" değil **Orin Nano Developer Kit 4 GB / JetPack 7.2.1 / Ubuntu 24.04 / Python 3.12** çıktı; kurulum `~/venv312`; FPS pt p50/p95 1,35/1,06, engine 1,58/1,33 ≥ 0,61 **GEÇTİ**; engine↔pt denkliği D-303 oransal eşiği 3/126 **DÜŞTÜ** → uçuş `.pt` ile. CSI kamera ve Pixhawk kapıları **ÖLÇÜLEMEDİ** (bağlı değildi).

### 5.6 Sonraki uçuş planı

`SAHA_HAZIRLIK_PLANI_20260903.md` §3–§4 sırası: **3.1 ilk hover** (Stabilize/AltHold, 2–3 m, 2 dk; VIBE, EKF yeşil, kırım yok; pervaneler ilk kez takılır) → 3.2 Loiter + kısa Auto (30 m) + geofence + iniş kanıtı canlı → 3.3 algı canlı (OPEN_ROUTE YKS'de) → 3.4 tam prova ×3 (≤10 dk, video + hakem_log) → 3.5 sıkı prova (kapalı kutu, kronometre, hands-off) → 3.6 sürüm dondurma (**Per 17 Eylül**) → Cum 18 KESİN HAZIR → Paz 20 yolculuk → **Pzt 21 Adıyaman provası** → 30 Eyl–3 Eki resmî test uçuşu. Devrilme sonrası ön koşul: `SAHA_OLAY_SONRASI_MUAYENE.md` madde 0–12 + `DEVAM.md` §5 sabah sırası (yeni piller, failsafe testi, `RC IN` sabitleme, 3 kırmızı tel, `SERVO1–8/13–16=0` + motor testi listesi, `RC_PROTOCOLS` tek değişkenli test, sabah dökümü, sonra ancak diz boyu hop). Tartı + motor kararı (X2220 kalır / 9×4,7 / V3115) kullanıcının. 7 Eylül sonrası ilerleme bu depoda **DOĞRULANAMADI**.

---

## 6. Jetson tek-komut açılış — `jetson_paket/jetson_baslat.sh` (619 satır)

**Neden:** şartname §6.2 hazırlık süresi (tek komut) + hands-off (ölen süreç kendi kalkar: `Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`) + CONTRACTS §7.4 seri Pixhawk **tek sahipli** (`/dev/ttyACM0`'ı yalnız MAVProxy açar).

**Kipler (`case` bloğu, satır 665–674):**

| kip | ne yapar | çıkış |
|---|---|---|
| `--kuru` | **hiçbir şey başlatmaz**; `/etc/navitas.env` içeriğini, birim başına koşulacak `ExecStart`'ı, paket denetimini (`[VAR]/[YOK]`), ana makine denetimini (kullanıcı, yorumlayıcı, seri cihaz, kurulu `.py`), beyan denetimini basar | herhangi `[YOK]`/`[EKSIK]` → `KURU SONUC: eksik`, **3** |
| `--kur` (varsayılan, `sudo -E`) | env dosyası + `/etc/systemd/system/navitas-*.service` (CR'siz, sed ile yol/kullanıcı işlenmiş), `daemon-reload`, `enable` + **`restart`** (beyan değişince canlı sürece uygulanır, D-405); thazırlık süresini basar | 0 / 1 |
| `--kapi` | kurar, **yalnız çoğullayıcıyı** (SiK'te hub, kamera köprüsü) kaldırır, üç uçta **aynı anda** `scripts/mavlink_dogrula.py --mavlink udp:127.0.0.1:1455N --sysid $SYSID` koşar (`results/jetson_log/kapi/<port>.log|.rc`); **3/3 GEÇTİ** değilse tüketiciler **başlatılmaz** (fail-closed) | 0 / 1 |
| `--dogrudan` | systemd'siz nohup + log; **gözcü yok** | — |
| `--durdur` | `disable --now` + nohup pid'leri | — |
| `--durum` | birim başına `is-active` + `NRestarts` (artıyorsa çökme döngüsü) | — |

**Altı systemd birimi (`jetson_paket/systemd/`):**

| birim | görev | MAVLink ucu | kip |
|---|---|---|---|
| `navitas-cogullayici` | MAVProxy `--master=/dev/ttyACM0 --baudrate 57600 --streamrate 8 --out udp:127.0.0.1:14550/14551/14552 --daemon` | üretir | udp+sik |
| `navitas-seri-hub` | SiK `/dev/ttyUSB0`'ın tek sahibi; `--bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007` | — | **yalnız sik** |
| `navitas-kamera-koprusu` | CSI `nvarguscamerasrc` → MJPEG `http://127.0.0.1:8080/video` (sistem Python + GStreamer) | — | `KAMERA=http://127.0.0.1:8080/video` verilince |
| `navitas-rpi-inference` | `rpi_inference.py --camera --ekransiz --mavlink udp:127.0.0.1:14550 --mav-sysid $SYSID …` (algı + OPEN_ROUTE/NO_ROUTE + HEARTBEAT) | 14550 okur | udp+sik |
| `navitas-iha-inis-yayinci` | `iha_inis_yayinci.py --mavlink udp:127.0.0.1:14551 --sysid $SYSID --kanit-timeout 900 …` (Pixhawk kanıtlı `IHA_LANDED`) | 14551 okur | udp+sik |
| `navitas-iha-komut-alici` | `iha_komut_alici.py --mavlink udp:127.0.0.1:14552 --sysid $SYSID --bind … --izinli-kaynak …` (YKS PARAŞÜT/ARM → `COMMAND_LONG`; ACK yalnız ACCEPTED) | 14552 yazar | udp+sik |

Tüketiciler `After=/Wants=navitas-cogullayici.service`; hiçbiri `/dev/tty*` açmaz (`tuketici_denetle` bunu hata sayar, satır 344). `sozlesme_denetle` birim dosyaları CONTRACTS §7.4'ten sapmışsa kalkmaz.

**Ortam değişkenleri (satır 132–161; `/etc/navitas.env`'e yazılır):** `KIP=udp|sik` · `YKS_IP`, `IKA_IP` (udp'de **zorunlu**, varsayılanı yok) · `FOV` ya da `ODAK` (kamera geometrisi, **beyan edilir, tahmin edilmez**) · `KAMERA` (indeks/`/dev/videoN`/URL; loopback http ise köprü kalkar) · `KAMERA_KOPRU_BIND` (varsayılan 127.0.0.1; `0.0.0.0` açık opt-in) · `SENARYO`, `UB_REFERANS` · `PIXHAWK_SERI=/dev/ttyACM0`, `PIXHAWK_BAUD=57600`, `SYSID=1` (= `SYSID_THISMAV`) · `SIK_SERI=/dev/ttyUSB0`, `SIK_BAUD=57600` · `KANIT_TIMEOUT=900` · `SERVIS_KULLANICI=${SUDO_USER:-$USER}` (birimlerde `User=`) · `NAVITAS_KOK`, `PYTHON3` (Orin'de `/home/n4vitas/venv312/bin/python`), `KAMERA_PYTHON=/usr/bin/python3`. Kip'e göre: udp → `--yks-hedef YKS:5005 --ika-hedef IKA:5006`, `--izinli-kaynak YKS:5005`; sik → yalnız `--yks-hedef 127.0.0.1:5100` (İKA'nın SiK hattı topolojiyle karara bağlı, **açık**).

**6 Eylül ölçümü (`JETSON_BASLAT.md` başı):** `--kuru` koşuldu: tüm dosya ve yorumlayıcılar `[VAR]`, `[YOK]` yalnız `/dev/ttyACM0` (Pixhawk bağlı değildi) → çıkış 3, beklenen; `--kapi` **ÖLÇÜLEMEDİ**.

---

## 7. Sürüm dondurma mührü — `scripts/surum_dondur.py`

**Neden:** şartname §6.1 yarışan yazılımın FDS/SGGS/UHDR beyanıyla **birebir aynı** olmasını ister; "aynı" iddiası sözle değil **ölçümle** kurulur (docstring). Dondurma anı kullanıcı kararı (plan ~17–18 Eylül).

**Ne mühürlenir (künye `config/DONDURMA_KUNYESI.json`, kategoriler `KUNYE_DOSYA_KATEGORILERI`):**
1. `paket` — `jetson_paket_hazirla.KOPYALAR` (Jetson'a giden kod aynası) ve `paket_kaynak` (aynı dosyaların depo kaynağı; iki kategori kasıtlı).
2. `paket_modelleri` — `jetson_paket/models/` (gitignore'lu `.pt`/`.onnx`; kanonik/defterle bayt-eş değilse **RED**).
3. `saha_yapilandirma` — `jetson_baslat.sh`, `systemd/*.service` (glob: diskte beliren ek birim `--dogrula`'da "BELİRDİ" ile düşer), `requirements_rpi.txt`, `requirements_nano.txt`, **`config/pixhawk/arducopter_fda.param`, `fda_gorev.waypoints`, `README.md`**, `kalibrasyon/*.yaml|json` (satır 133–154).
4. `yks_ika` — 9 dosya: `yks_gui.py`, `komut_tekrar.py`, `protocol.py`, `link.py`, `iha_sender.py`, `ika_receiver.py`, `ika_nav.py`, `ika_surucu.py`, `saha_baslat.py` (satır 161–171) — "yarışan yazılım" üç istasyondur.
5. Model kayıt defteri sha256'sı, `git_head`, `git_kirli`, `test_komutu` (üç suit: `test_faz_b_surum_dondurma`, `test_jetson_comms_paketi`, `test_uretim_modeli_hizasi`).

**Mekanizma:** `--dondur --etiket v36-yarisma --tarih YYYY-MM-DD` künyeyi yazar; kirli ağaçta **RED** (exit 2; `--kirli-bilerek` künyeye yazılır). Özet **içerik-kanonik** (`sha256 v2: metin lf-normalize | ikili ham`): Windows CRLF ve Linux/Jetson LF checkout'ları aynı özeti verir (v1'de 18/19 dosya sahte ihlal veriyordu, D-405 S6). `--dogrula` her farkı adıyla listeler ve **git'e bağlıdır**: künye HEAD'de değilse "KÜNYE COMMIT EDİLMEMİŞ", HEAD'dekiyle farklıysa "DEĞİŞTİRİLMİŞ", izlenen yollar kirliyse "KİRLİ" → exit 1. Etkin profilin TensorRT türevi kayıtsızsa `--dondur` "mühür erken" ile RED (`--engine-kayitsiz-bilerek` ile aşılır, künyeye yazılır). Mühür **sırası** (`FAZ_B_GUN_PLANI.md` §3): Jetson'da engine derle + `--turev-kaydet` → defter/aynayı PC'ye taşı, commit → **ancak sonra** `--dondur` → künye commit. Çıkış: 0 birebir · 1 fark · 2 red · 3 **DONDURULMADI** (künye yok). Son ölçüm: `--dogrula` exit 3 (3 Eylül, beklenen); bugünkü durum **DOĞRULANAMADI**.

**3B baskı gövde (`dronesolid/`):** STL: `Drone_Arm`, `Drone_Dome`, `Drone_Frame`, `Drone_Legs`, `GPS_Holder`, `Lower_Drone_Frame`; baskı plakaları (`files (3)/`): `Plaka1_Kol_1-2`, `Plaka2_Kol_3-4`, `Plaka3_Alt_Cerceve`, `Plaka4_Ust_Cerceve`, `Plaka5_Kubbe`, `Plaka_Ayak`, `Plaka_GPS_Holder`, `tpu_taban_pedi_x4` (.3mf); `NAVITAS-UAV-FDR-ZIP(Tamamlanmamis).zip` (10 MB). Muayene belgesinde anılan izlenmeyen `uzatılmış yeni drone kolu.STL` ve `gps kolu.STL` bu kopyada **yok** (DOĞRULANAMADI). CAD mühür kapsamında **değildir**.

---

## 8. 15 muhtemel jüri sorusu ve kanıta dayanan kısa cevap

1. **"İKA'nız otonom gidiyor mu?"** — Karar mantığı ve sürüş kilidi (rota + `IHA_LANDED` + `IKA_GO`, 900/600 s ayrı süreler, `NO_ROUTE`/bağlantı kaybında anında durma) kodda ve testte hazır (`ika_nav.py`, `ika_receiver.py`). **Gerçek İKA donanımı tedarik edilmedi**, motor sürücüsü yok (`TASK_QUEUE.md:6444` T149 açık; FDR §3.2.2). Görev test uçuşunda İKA zorunlu değil; finale bırakıldı.

2. **"İKA rotayı nasıl planlıyor — A* mı?"** — A* İHA tarafında (`costmap_path_finder.rota_bul`); İKA yalnız gelen waypoint listesini oransal yön kontrolüyle izler (`TURN_GAIN 1,8`, `MAX_SPEED 2 m/s`, 10 Hz; `ika_nav.py:37-45,100-112`). PID yok.

3. **"İKA konumunu nereden biliyor?"** — Bugün yalnız Gazebo'dan (`konum_al`). Gerçek konum kaynağı (GNSS/odometri) yok; kabul turu K2 bunu "KONUM YOK" uyarısıyla geçici kabul eder (`ika_surucu_kabul.py:14-15`).

4. **"Motor sürücüsü arızalanırsa?"** — 3 ardışık `hiz_ver` arızası (10 Hz'de ~0,3 s) → "sürücü yanıtsız", son bir durdurma, `navigate` `False` (`ika_surucu.py:37`). Eskiden subprocess istisnasıyla çökerdi (D-390).

5. **"Simülasyon sonucu gerçek mi?"** — Model gerçek `.pt` ile ortomozaikte koşar; yanlış karar verirse İKA kapalı yola gider, ground-truth ile karşılaştırılır ve BAŞARISIZ yazılır (`iha_haritala.py`, `hakem_log.py`). Ama Gazebo İKA'sını `navitas_anim` plugin'i sürer, `DiffDrivePlugin` kaldırıldı (`ika/model.sdf:233-237`); "sim kanıtı saha kanıtı değildir" (CONTRACTS 11.1).

6. **"Puanı nasıl hesaplıyorsunuz?"** — `simulation/score.py`: `TOPLAM = 0,65·Puan2 + 0,20·P + 0,15·Puan1`; Puan2 = K×(600 görev + hafiflik + hız + hazırlık + yük − ceza), sapma −5/m, manuel paraşüt −50. Şartname V2 (13.04.2026) okuması.

7. **"Hakem tespiti nasıl teyit edecek?"** — YKS'de canlı `OPEN_ROUTE` (seq, road, conf, waypoint, ankor) ekranda; iki aşamalı onay; her olay `hakem_log.jsonl`'e `fsync` ile yazılır (`hakem_kaydi.py`, CONTRACTS §6.8). Bayat tespit (>5 s) ve ankorsuz rota fail-closed reddedilir (`HAKEM_ONAYI_REDDI`).

8. **"Görev test uçuşunda İKA olmayacak; YKS bunu nasıl ele alıyor?"** — `--fda` kipi: hakem 2/2 onayı İKA kanıtı aramaz, PARAŞÜT ve İKA düğmeleri komut göndermez, bütçe 600 s, FIRLATMA → KALKIŞ (CONTRACTS §6.7; 9 test).

9. **"Neden ArduCopter 4.5.7, en yeni değil?"** — 4.7 SI reformu 31 parametrenin 9'unu adı/birimi/anlamı değişmiş hâle getirdi (`WPNAV_SPEED` 300 → 300 m/s, `ARMING_CHECK` tersi); dosya, kapı ve TEYİT listesi 4.5'e ölçülü; tek atışlık uçuştan 16 gün önce ölçülmemiş port yapılmadı (D-425). İndirici sürümü sabitler (`pixhawk_firmware_indir.py:74`).

10. **"Kumanda kapanırsa ne olur?"** — Tasarım RTL (`FS_THR_ENABLE,1`); 6 Eylül'de ölçüldü ve **düştü**: FS-iA6B iBUS'ta son değerleri tutuyor, failsafe tetiklenmiyor (D-428 §2). Çözüm kumandada failsafe kanal ayarı; test geçmeden pervane takılmaz. GCS failsafe SiK kopunca tetiklenmez (Jetson MAVProxy heartbeat basar) — bilinçli, "Jetson-bağlantı failsafe'i" (D-406 C).

11. **"Paraşüt var mı?"** — Görev test uçuşunda hayır (çoklu rotor; `CHUTE_ENABLED,0`). Final sabit kanat için YKS→`iha_komut_alici`→`DO_PARACHUTE` zinciri ve ACK-yalnız-ACCEPTED sözleşmesi hazır (D-393); manuel −50 (`score.py`).

12. **"6 Eylül'de drone neden devrildi?"** — tlog ölçümü: FC doğru yönde düzeltti; ön itki komut edilen itkiyi üretmedi; gaz 0,2–0,6 s'de %45–100'e sıçradı; M1 doygun ve hasarlı (D-429). Pilot kolu merkezdeydi, seviye temiz (D-434). Kalan aileler: itki asimetrisi (eski X2220 motorlar, 38 A/30 s sınırında) ve CG/kol geometrisi. Kural: ≥2 s rampa, `MOT_SLEW_UP_TIME 1,0`, video, muayene 0–12.

13. **"Hazırlık süresini nasıl tutuyorsunuz?"** — İstasyon başına tek komut (`saha_baslat.py yks|ika`, `jetson_baslat.sh`), systemd `Restart=always` (hands-off sonrası süreç ölse kendi kalkar), `--kapi` üç MAVLink ucunu **paralel** doğrular (sıralı +22..52 s eklerdi; 30 s = 1 puan).

14. **"Sahada koşan yazılımın rapordakiyle aynı olduğunu nasıl kanıtlıyorsunuz?"** — `surum_dondur.py`: kod aynası, modeller, Jetson yapılandırması, Pixhawk parametre/görev dosyaları ve YKS/İKA dosyalarının sha256'sı git HEAD'e bağlı künyede; `--dogrula` her farkı adıyla listeler, kapı her suit koşumunda kontrol eder. Henüz **dondurulmadı** (plan 17 Eylül).

15. **"Motor/ESC künyeniz ne?"** — ESC Hobbywing Skywalker 60A V2 ×4 (etiket beyanı), AUX 1–4, PWM 400 Hz. Motor SunnySky X2220-III KV980 ×4 + 10×4,5 + 4S (BEYAN, etiket fotoğrafı yok); veri sayfasında 1045 satırı yok, 4S+1047 tam gaz 38,4 A > 38 A/30 s sınırı; M1 hasarlı; kütle ölçülmeden pervane/motor kararı yok (D-435/436). Depodaki eski "5008 340KV" atıfları T211 ile düzeltiliyor.

