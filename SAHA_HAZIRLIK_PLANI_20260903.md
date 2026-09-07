# SIFIRDAN GÖREV UÇUŞUNA — SAHA HAZIRLIK PLANI VE TAKVİM (3 Eylül 2026)

> **Yazan:** Claude 2 (Fable 5.1, mimar). **Kullanıcı isteği:** *"yazılım tarafında her şeyi
> cumartesine kadar bitir; cumartesi aviyonikleri gövdeye montelemek ve kablolamak dahil, sıfırdan
> 21 Eylül'deki görevi şartnameye göre yapacak hale gelmek; takıma atılacak bir takvim."*
> Her adımın bir kapısı vardır; "yapıldı" demek için kanıt gerekir (`ÖLÇÜLEMEDİ ≠ GEÇTİ`).
> Görevleri **rol** üstünden yazar, kişilere kaptan dağıtır.
>
> **Bağlı belgeler:** `YAZILIM_BITIRME_PLANI_20260901.md` · `FAZ_B_GUN_PLANI.md` (cumartesi saat planı)
> · `SAHA_RUNBOOK.md` · `jetson_paket/JETSON_KILAVUZ.md`, `GUN1_KONTROL_LISTESI.md`, `JETSON_BASLAT.md`
> · `simulation/PROVA_SENARYOSU.md` (8 faz) · `CONTRACTS.md` §6–7.

---

## 0. Çerçeve

### 0.1 Hedef: iki tarih — 21 Eylül **FDR teslimi + Adıyaman provası**, 30 Eylül–3 Ekim **resmî görev test uçuşu**

**İki tarih, karıştırılmaz (şartname Tablo 1):**

| tarih | ne | bizim işimiz |
|---|---|---|
| **21.09.2026 · 17.00** | **FDR son teslim** | rapor bitmiş ve gönderilmiş olmalı |
| **21.09.2026 (aynı gün)** | takımın **Adıyaman provası** | uçuş provası, hakem yok |
| **30.09 – 03.10.2026** | **resmî Drone ile Görev Test Uçuşu** (§5.3.2) | tek atış, hakem önünde |

**Çoklu rotorlu drone** ile görev test uçuşu (FDA'nın %15'i): 20×20 m simüle alanda, **≥ 30 m**
irtifadan açık güzergâhın havadan tespiti, **YKS'ye canlı aktarım + alan hakemi onayı**,
**kalkış → tespit → aktarım → iniş ≤ 10 dakika**. Yanlış güzergâh ya da süre aşımı = **0 puan**.
İKA bu uçuşta **zorunlu değildir** (aktarım YKS'ye); İKA hattı finale kalır.
Sabit kanat + mancınık + paraşüt **finalin** işidir (§7), bu planın kapsamı dışında.

### 0.2 Donanım künyesi (kullanıcı beyanı, 3 Eylül) — cumartesi kutudan çıkanla teyit

| kalem | değer | not |
|---|---|---|
| Gövde | **Quadcopter, 3B baskı** (`dronesolid/`: kol, gövde, alt gövde, bacak, dome, GPS tutucu) — **basıldı ve monte**; GPS çubuğu + ayaklar ABS beyaz, kalanı ABS-CF siyah | aviyonik **kutuda**, kutu açılmadı |
| Motor / pervane | **5008 340KV ×4**, **12×10** pervane | 4S'te yaklaşık 10–12 A/motor havada asılı; tepe 30+ A/motor |
| ESC | **80 A, DShot destekli** ×4 | ilk uçuşlarda **PWM 400 Hz** (MAIN 1–4); DShot sonra, isteğe bağlı |
| Güç dağıtımı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | ESC'ler buradan |
| Uçuş kontrolcüsü | **Pixhawk 6C** + kutusundan çıkan **PM02** güç modülü | PM02: pil → PM02 → FCHUB; POWER1 beslemesi + V/I ölçümü (fabrika kalibreli). ⚠ PM02 sürekli akım sınırı — sürekli tam gaz yok |
| GNSS / pusula | **Holybro M9N** | direk üstü (ABS beyaz çubuk) |
| RC | **FlySky FS-i6** kumanda + alıcı (FS-iA6B beklenir, **iBUS**) — **bind edilmedi** | **pilot: kullanıcı** |
| Telemetri | **2× SiK 433 MHz** (drone, YKS) | İKA hattı finale kalır |
| Yer bilgisayarı | 🔴 **GEÇERSİZ (D-431)** ~~Jetson Nano 4GB — cumartesi geliyor, kurulumu YOK~~ → **ölçüldü (6 Eylül): Jetson Orin Nano Developer Kit 4 GB** (modül p3767-0004), **kurulum yapıldı** | ~~JetPack 4.6.x (Ubuntu 18.04, Python 3.6 sistem)~~ → **JetPack 7.2.1** (L4T R39.2.1, Ubuntu 24.04, Python 3.12.3, kök NVMe); tutanak `jetson_paket/JETSON_ORIN_NANO_KURULUM.md`; §1.3'teki venv38/cp38 planı tarihçedir |
| Kamera | **Raspberry Pi HQ (IMX477, CSI)**, **standart lens** (kullanıcı: RPi'nin standart 6 mm geniş açı lensi ise yatay FOV ≈ 55–63° → 30 m'de kare genişliği ≈ 31–37 m, **20×20 m alan tek karede sığar**; 16 mm olsaydı ≈ 12 m ile sığmazdı). `--fov` değeri cumartesi `kamera_dogrula` ile **ölçülür**, beyan ölçümdür | Nano'da `jetson-io` ile IMX477; GStreamer ister — bkz. §1.4 |
| Pil / şarj | **1× 4S 10 Ah 25C** · **iMAX B6** (50 W → ~3 A → dolum ~3 saat) | **günde en fazla 2 uçuş**; 2. pil "ayarlanmaya çalışılır" |
| Güç kesme | Anahtar yok — **pil fişi çekilir** (XT60/XT90) | yordam: pervane en son, pil en son |
| Pixhawk ↔ Jetson | **Öneri (§1.3):** `TELEM2` → Nano 40-pin UART (`/dev/ttyTHS1`, pin 8 TX / 10 RX / 6 GND, 3,3 V), MAVLink2 57600; yedek: micro-USB → `/dev/ttyACM0` | tek kablo, USB hub yok. ⚠ D-431: kart Orin Nano DevKit; 40-pin UART eşlemesi bu kartta **DOĞRULANACAK** (6 Eylül'de Pixhawk bağlı değildi, ÖLÇÜLEMEDİ) |
| Jetson gücü | **Öneri:** ayrı **5 V / 5 A UBEC** (FCHUB pil pad'lerinden) → Nano barrel jack (J25) + `J48` jumper takılı; **FCHUB'ın 2 A BEC'i yetmez** | ortak GND. ⚠ D-431: Orin Nano DevKit'te **J48 yok** (tutanak §0 tablosu); besleme gereksinimi Orin için **DOĞRULANACAK** |

### 0.3 Puanı belirleyen dört şey

1. **Doğru güzergâh** (yanlış = 0): v36 + `analyze_path` + histerezis (D-396); HB dedektörü üretime bağlı **değil** (K3).
2. **Hakem canlı görüyor, onaylıyor**: `yks_gui`, iki aşamalı onay, ACK'li aktarım (CONTRACTS §6.6).
3. **≤ 10 dakika**: kısa görev planı, tek pas tarama, loiter'da ACK, iniş.
4. **Sıfır müdahale**: "Takım Hazır"dan sonra el yok; çökme döngüsü yok (`Restart=always`, ekransız kip).

---

## 1. YAZILIM — cumartesiye kadar (Çar 2 akşam · Per 3 · Cum 4)

> **Durum (3 Eylül gecesi):** yazılım tarafındaki **12 kalemin 12'si kapandı**; kalan iki satır (🧑) yalnız insan işidir: microSD'ye JetPack imajı yazmak ve YKS bilgisayarını kurmak. Alışveriş ve bellek kopyalama için basılacak kart: `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md`.

| ✓ | adım | rol | kapı |
|---|---|---|---|
| ✅ | **1.1 D-405 kapanışı — YAPILDI (3 Eylül):** hub sertleştirme + mühür v2 (✅ birleşti) + `jetson_baslat` düzeltmeleri; genel kapı 15/15 + tam suit; D-405 §3; commit | AI | suit OK |
| ✅ | **1.2 Push — YAPILDI (3 Eylül):** uzak adres `yazilim-takimi/navitas` olarak güncellendi (kullanıcı onayı ile), **25 commit** itildi (`096a672..f6179c1`); sonraki turlar da itildi | AI ✅ | `git status -sb` uzakla eşit |
| ✅ | 🔴 **GEÇERSİZ (D-431, 6 Eylül):** kart **Orin Nano / JetPack 7.2.1 / Python 3.12** çıktı; venv38 + cp38 tekerlekler **kullanılmadı**, kurulum `~/venv312` + çevrimiçi pip ile yapıldı (`jetson_paket/orin_nano_venv_kurulum.sh`; torch 2.11.0+cu130, CUDA **çalışıyor**); FPS **ölçüldü**: pt p50/p95 **1,35/1,06** · engine **1,58/1,33** FPS ≥ 0,61 GEÇTİ (`jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §5). Aşağıdaki metin 3 Eylül tarihçesidir → **1.3 Jetson Nano 4GB yığını (EN KRİTİK) — YAZILIM TARAFI BİTTİ:** repo `ultralytics` ister (Python ≥ 3.8), Nano'nun sistem Python'u 3.6. **Karar:** Nano'da Python 3.8 venv + `torch` + `ultralytics` + `opencv-python` + `numpy pyserial pymavlink onnxruntime MAVProxy`. ✅ **Yapıldı (3 Eylül, D-406):** `jetson_paket/JETSON_NANO_KURULUM.md` + `scripts/nano_tekerlek_indir.py` — PC'de gerçek indirme: **14/14 paket aarch64/cp38 wheel** (torch 2.4.1 **CPU**, torchvision 0.19.1, ultralytics 8.4.118, onnxruntime 1.19.2, MAVProxy 1.8.70; 51 dosya, 246 MB, kaynak paketi yok), Nano'da tek komut `pip install --no-index --find-links . -r requirements_nano.txt`. ⚠ **Dürüst risk:** v36 **YOLOv8m-seg**'dir (n değil); Nano **CPU**'da 512'de kapı 0,61 FPS **düşebilir** — sıra: (1) JetPack 4.6 için Python 3.8 **CUDA torch** topluluk wheel'i (Qengineering) elle indirilip belleğe konur (**insan**), (2) `onnxruntime` ile `.onnx` (CPU'da torch'tan hızlı olabilir), (3) CPU torch. Eşik gevşetilmez; cumartesi ölçülür. `.engine` bu kartta 21 Eylül için **ÖLÇÜLEMEDİ** sayılır | AI ✅ · **insan: GPU wheel + bellek** | `wheels/INDIRME_RAPORU.txt`; test `test_faz_b_nano_kurulum.py` 19 |
| ✅ | **1.4 Kamera köprüsü — YAPILDI (D-406 K/K2):** `scripts/kamera_koprusu.py` (paket `kod/`, Python 3.6 uyumlu; `nvarguscamerasrc` / sayı / dosya kaynağı; `/video` MJPEG, `/kare.jpg`, `/durum` JSON; kaynak düşünce fail-visible + yeniden açma), `navitas-kamera-koprusu.service` (`KAMERA_PYTHON=/usr/bin/python3`), `jetson_baslat.sh` `KAMERA=http://127.0.0.1:8080/video` ile `rpi_inference --kaynak`; çoğullayıcıya `--streamrate 8` (D-406 B). Testler: köprü 7, `jetson_baslat` 42, paket 18 dosya. **Yedek:** USB webcam (UVC) `--kaynak 0` | AI ✅ | `test_faz_b_kamera_koprusu.py` |
| ✅ | 🔴 **GEÇERSİZ (D-431, 6 Eylül):** kart **JetPack 7.2.1 kurulu** geldi (Orin Nano DevKit, kök NVMe) — flash / SDK Manager / Ubuntu host **gerekmedi**; `cat /etc/nv_tegra_release` → `R39 (release), REVISION: 2.1`. Aşağıdaki metin tarihçedir → **1.5 Sistem imajı — DEĞİŞTİ (3 Eylül, D-413)**: kartta **microSD yuvası yok** (Nano üretim modülü + taşıyıcı, M.2 SSD). SD imajı yolu **geçersiz**. Yeni yordam: cumartesi **önce aç ve bak** — eMMC'de JetPack kurulu gelmiş olabilir (`JETSON_NANO_KURULUM.md` §1.1). Boşsa **Ubuntu x86_64 host + SDK Manager** gerekir (§1.2); **Windows'ta yapılamaz**. Yazılım yığını değişmedi: JetPack 4.6.x / Py3.6 varsayımı ve `wheels/` **aynen geçerli** | **insan** | açılış ekranı + `cat /etc/nv_tegra_release` |
| ✅ | **1.6 ArduCopter parametre dosyası — YAPILDI (D-406):** `config/pixhawk/arducopter_fda.param` 31 parametre (Copter-4.5 kaynak dosyalarından doğrulandı, her satırda NEDEN; 4 **TEYİT** işaretli: `BRD_SER2_RTSCTS=0`, `RC_PROTOCOLS=4` iBUS, `BATT_FS_LOW_ACT/CRT_ACT`), `config/pixhawk/README.md` (yükleme + sahada değişecek tek şeyler + TEYİT listesi), `tests/test_faz_b_pixhawk_sablon.py` 12. Sapmalar bilerek: görev irtifası **32 m** (2 m baro payı; 30 altı `ASGARI_IRTIFA_ALTI` işaretlenir), loiter 60 s; kötü-durum süre bütçesi 221,5 s ≤ 600 s. Aşağıdaki değerler cumartesi kutudan çıkanla teyit: `FRAME_CLASS=1` (quad), `FRAME_TYPE` (X), `MOT_PWM_TYPE=0`, `SYSID_THISMAV=1`, `SERIAL1` (TELEM1 SiK 57600 MAVLink2), `SERIAL2` (Jetson 57600 MAVLink2), `SRx_POSITION 4 Hz`, `SRx_EXTRA3 1 Hz`, `RC_PROTOCOLS` iBUS, `BATT_MONITOR=4` (PM02), `FENCE_ENABLE=1` (irtifa + poligon), `FENCE_ALT_MAX 50`, `RTL_ALT 3500`, `LAND_SPEED 50`, `FS_THR_ENABLE 1`, `FS_GCS_ENABLE 1`, `BATT_FS_LOW/CRT` (4S: 14,4 / 14,0 V), `ARMING_CHECK=1`, `LOG_BITMASK` | AI hazırlar · değerler cumartesi teyit | dosya repoda |
| ✅ | **1.7 Görev planı şablonu — YAPILDI (D-406):** `config/pixhawk/fda_gorev.waypoints` (QGC WPL 110): home → TAKEOFF 32 m → 20×20 m üstünde tek pas (köşeler yer tutucu, kare şekli testle kilitli) → LOITER 60 s (ACK) → LAND; **koordinatlar Adıyaman'da girilir** (README §"sahada değişecek") | AI ✅ · **kaptan koordinat** | test 12/12; Mission Planner'da açılıyor |
| ✅ | **1.8a YKS FDA kipi — YAPILDI (3 Eylül, D-407):** `yks_gui --fda` artık yalnız süre bütçesi değil: hakem 2/2 onayı İKA kanıtı aramaz (o kilit 21 Eylül'de onayı imkânsız kılıyordu), paraşüt ve İKA düğmeleri fail-closed kapalı, FIRLATMA → KALKIŞ. `CONTRACTS §6.7`; `tests/test_faz_b_yks_fda_kipi.py` 9 test, 4/4 mutant yakalandı | AI ✅ | test + mutasyon |
| 🧑 | **1.8 YKS PC — İNSAN**: venv, SiK COM portu, güvenlik duvarı, `saha_baslat.py yks --serial COMx` denemesi; hakem ekran düzeni | **YKS rolü** + AI | kart + açılış süresi |
| ✅ | **1.9 Cuma akşamı §0 listesi — KOŞULDU (3 Eylül gecesi):** genel kapı 15/15 · tam suit **1896 OK** (3 Eylül 11:13 koşumu; 1875 D-412 düzeltmesinden öncekiydi) · kuru koşu **9 GEÇTİ / 1 SAHİPSİZ** (yalnız `motor`) · paket aynası 18 · model dosyaları yerinde · `jetson_baslat.sh --kuru` udp+sik doğru · mühür `--dogrula` exit 3. Ham çıktı: `results/faz_b_oncesi/cuma_kontrol/`. Cuma yalnız **tekrar** koşulacak (kod değiştiyse). Basılacak kart: `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` | AI ✅ | çıktı klasörü |
| ✅ | **1.10 Taşınabilir bellek — HAZIRLANDI (3 Eylül):** `scripts/bellek_hazirla.py` (fail-closed: zorunlu parça eksikse çıkış 3 + `EKSIKLER.txt`; `MANIFEST.txt` her dosyanın sha256'sı + git HEAD) koşuldu → **405 dosya · 1,27 GB** → `O:
avitas_bellek` (jetson_paket, wheels 14/14, Pixhawk şablonları, basılacak belgeler). **İnsan: klasörü USB'ye kopyalar.** `tests/test_faz_b_bellek_hazirla.py` 7 | AI ✅ · insan kopyalar | MANIFEST |
| ✅ | **1.11 Alışveriş listesi — YAZILDI:** `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B (**zorunlu 12 + öneri 2** kalem; 3 Eylül'de microSD çıktı, Ubuntu host ve kurtarma pini girdi — D-413, her birinin nedeni yazılı; belleğe de kopyalandı). **Satın alma insanda.** | AI ✅ · insan alır | |
| ✅ | **1.12 FDR/UHDR kanıt sayfası — YAPILDI (3 Eylül):** sayaçlar tazelendi (**420 kayıt · 1896 test**, 3 Eylül son ölçüm) + "Aviyonik gelmeden kapatılan zincir" bölümü (dört gerçek kusur ve çürütülemeyenler) | AI ✅ | artifact yeniden yayınlandı |

**Kural:** cumartesiden itibaren üretim kodu **değişmez** (mühür yakın); zorunlu değişiklik = D-kaydı + kapı + ayrı denetim.

---

## 2. CUMARTESİ 5 EYLÜL — sıfırdan montaj, kablolama, yapılandırma

Roller: **kaptan** (tutanak/karar) · **aviyonik** (Pixhawk/güç/kablo) · **Jetson/kamera** · **YKS** · **pilot**.
Pervaneler **en son**, pil **en son**; pil fişi = tek güç kesici.

### 2.1 Kutu ve envanter (09:00)
| ✓ | adım | kanıt |
|---|---|---|
| ☐ | Kutuyu aç; künye tablosu (§0.2) ile karşılaştır; **PM02**, kablolar, anten, alıcı, pervaneler | eksik/fark listesi |
| ☐ | Her parça **tartılır** (UHDR gerçek kütle), fotoğraflanır | tartı listesi |
| ☐ | Gövde kontrolü: kollar sıkı, bacaklar, dome, GPS çubuğu; motor delikleri 5008 ile uyumlu | fotoğraf |

### 2.2 Mekanik yerleşim (09:30–11:00)
| ✓ | adım | ölçüt |
|---|---|---|
| ☐ | **Motorlar** kollara (vida boyu stator'a değmesin), CW/CCW yerleşimi (ArduCopter quad-X: 1 sağ ön CCW, 2 sol arka CCW, 3 sol ön CW, 4 sağ arka CW) | şema fotoğrafı |
| ☐ | **ESC'ler** kollara, motor kabloları kısa, burulmuş | kablo boyu |
| ☐ | **FCHUB-12S** gövde ortasına; **PM02** pil hattına | — |
| ☐ | **Pixhawk 6C** ağırlık merkezine, **ok ileri**, damper/köpük üstünde, kablolar gergin değil | uçuşta `VIBE` < 30 |
| ☐ | **M9N** GPS çubuğu üstünde, ok ileri, güç hatlarından uzak | pusula ofseti < 300 |
| ☐ | **Jetson Nano** hava alan yerde, ısı emici açık; **HQ kamera** nadir (tam aşağı), sabit, pervane kadrajda değil; şerit kablo kilitli | yerde kare temiz |
| ☐ | **SiK** anteni dikey, gövde dışı, ESC'den ≥ 5 cm; **FS alıcısı** anteni ayrı | RSSI |
| ☐ | **Pil** yuvası kayışlı, CG ortada (iki parmak testi) | CG ± 1 cm |

### 2.3 Kablolama (11:00–12:30) — pervanesiz, pil takılı DEĞİL
| ✓ | hat | bağlantı | ölçüt |
|---|---|---|---|
| ☐ | Ana güç | pil (XT60/XT90) → **PM02** → **FCHUB-12S** → 4× ESC | polarite; ohm ile kısa devre yok |
| ☐ | Pixhawk güç | PM02 6-pin → `POWER1` | 5,1–5,3 V; `BATT_MONITOR=4` |
| ☐ | Jetson güç | FCHUB pad → **5 V/5 A UBEC** → Nano barrel (J25), **J48 jumper takılı**; ortak GND | 5,0–5,2 V yük altında. ⚠ D-431: Orin Nano DevKit'te J48 yok — besleme Orin için **DOĞRULANACAK** |
| ☐ | ESC sinyal | ESC PWM → `MAIN OUT 1–4` (motor sırasına göre) | motor testi (pervanesiz) |
| ✅ | RC | FS-iA6B'nin **`i-BUS SERVO`** portu (🔴 `CH1`–`CH6` DEĞİL — tek kanal PWM, Pixhawk görmez; 5 Eylül'de `CH6`'ya takılıydı, D-426) → Pixhawk **`PPM/SBUS RC`** (5-pin JST-GH, Holybro kablosu; `DSM/SBUS RC` değil). Bind: alıcı `B/VCC` fişi + kumanda **BIND KEY** (ön yüz, sol alt) basılıyken aç. Kapı: `RCInput: decoding IBUS` | 5 Eylül 18:03 ✅ |
| ☐ | Telemetri | SiK → `TELEM1` (JST-GH 6 pin, TX↔RX çapraz), 57600; YKS SiK → USB | YKS'de HEARTBEAT |
| ☐ | Jetson ↔ Pixhawk | `TELEM2` (TX/RX/GND) → Nano 40-pin **pin 10 RX / pin 8 TX / pin 6 GND** (3,3 V; **5 V hattı bağlanmaz**) | `mavlink_dogrula` HEARTBEAT sysid=1 |
| ☐ | Kamera | HQ kamera CSI → Nano CSI (mavi taraf dışa), kilit kapalı | `jetson-io` sonrası `nvarguscamerasrc` görüntü |
| ☐ | Etiket + çekme testi | her konnektör etiketli | hiçbiri çıkmadı |
| ☐ | **İlk güç** | pil tak; LED/boot tonu; 60 s koku/ısı | Pixhawk + Nano açıldı |

### 2.4 Pixhawk yapılandırması (13:00–14:30, Mission Planner)
| ✓ | adım | kanıt |
|---|---|---|
| ☐ | 🔴 **ÖNCE FİRMWARE:** kart **PX4 ile gelir** (D-424). `Config → Full Parameter List → Refresh` → `MC_*`/`MPC_*` görüyorsan PX4'tür. **Disconnect** → `Setup → Install Firmware` → **`Load custom firmware`** → `firmware/arducopter.apj` — 🔴 **sürüm 4.5.7 SABİT, MP'nin önerdiği "en son kararlı" (4.7.x) DEĞİL**: 4.7 SI birim reformu parametre dosyamızın 9 satırını kırar (D-425). Saha belleğinde, internet gerekmez | açılışta `ArduCopter V4.5.7` görüldü; `FRAME_CLASS` var |
| ☐ | ArduCopter kararlı sürüm; `FRAME_CLASS/TYPE`; §1.6 parametre dosyasını yükle ⚠ **flash TÜM parametreleri sıfırlar — sıra: firmware → param** | sürüm tutanağa |
| ☐ | **Accel** (6 yön) + **level**; **pusula** (dışarıda, metalden uzak) | ofset < 300 |
| ☐ | **Radyo** kalibrasyonu; mod anahtarı (Stabilize · AltHold · Loiter · Auto · RTL · Land); RC failsafe (kumanda kapatınca `RTL`) | uçlar 1000–2000 |
| ☐ | **ESC** kalibrasyonu; **motor testi pervanesiz**: sıra A-B-C-D, yönler | video |
| ☐ | Failsafe'ler (RC/GCS/pil), **geofence** (irtifa 50 m + prova alanı poligonu), `ARMING_CHECK=1` | arm mesajları temiz |
| ☐ | `SERIAL1/2` MAVLink2, `SR` hızları, `SYSID_THISMAV=1` | `mavlink_dogrula` 3/3 |
| ☐ | Parametreleri kaydet → `config/pixhawk/arducopter_fda_20260905.param` → repo | commit |

### 2.5 Jetson Nano kurulumu (14:30–17:00) — `JETSON_NANO_KURULUM.md` — 🔴 GEÇERSİZ (D-431): 6 Eylül'de Orin Nano'ya `jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §1–2 ile kuruldu; aşağıdaki adımlar Nano tarihçesidir
| ✓ | adım | kapı |
|---|---|---|
| ✅ | ~~SD kart tak,~~ ilk açılış (klavye/ekran), kullanıcı ~~`navitas`~~ **`n4vitas` (6 Eylül ölçümü, D-431; `jetson_baslat.sh` `SUDO_USER`'dan türetir)**, ethernet | açıldı (JetPack 7.2.1 kurulu geldi) |
| ☐ | `jetson-io` → **IMX477** kamera; `nvarguscamerasrc` ile görüntü | görüntü var |
| ✅ | ~~Python 3.8 venv + bellekten tekerlekler (§1.3)~~ **GEÇERSİZ (D-431)** → `~/venv312` + çevrimiçi pip (6 Eylül): `import torch, ultralytics, cv2` OK, `torch.cuda.is_available()` **True** | import OK; `torch.cuda.is_available()` sonucu tutanağa (True/False ikisi de kabul; FPS ölçülür) |
| ☐ | **Kopyalama dizinleri belgeye birebir** (D-407): `kamera_koprusu.py` → `~/navitas/**scripts**/` (codes/ değil — `jetson_baslat.sh` orada arar, yanlışı `--kur` HATA ile durdurur); `mavlink_dogrula.py` → `~/navitas/scripts/` | `jetson_baslat.sh --kuru` → `[VAR]` satırları |
| ☐ | Paket kopyalama (`JETSON_KILAVUZ` §2 + `seri_hub`, `mavlink_dogrula`, `kamera_koprusu`), kayıt defteri, model | `model_kayit_dogrula` True |
| ☐ | **Kamera köprüsü** çalışıyor: `http://127.0.0.1:8080/video` → `kamera_dogrula --kaynak http://...` | kare doğru yön, `--fov` beyanı (lens) |
| ☐ | **FPS** (`jetson_fps.py`, PT/ONNX) ≥ **0,61** p50/p95 | GUN1 §5 |
| ☐ | `pip install MAVProxy`; `jetson_baslat.sh --kuru` → `--kapi` (çoğullayıcı + 3 uçta `mavlink_dogrula`) → birimler; `--durum` 0 restart; **ekransız** 10 dk | journal |

### 2.6 Yer zinciri (17:00–18:30) — pervanesiz
| ✓ | adım | kapı |
|---|---|---|
| ☐ | YKS: `saha_baslat.py yks --serial COMx` (SiK) ya da `--iha <NANO_IP>:5007` (WiFi) | HEARTBEAT + karar canlı |
| ☐ | SiK RF: `sik_rf_olc --rol yanki` / `--rol olc --n 50` → RTT p95 < 0,20 s | ölçüm dosyası |
| ☐ | ARM/DISARM aktarımı YKS → `iha_komut_alici` → COMMAND_ACK | "✓ (İHA ACK)" |
| ☐ | **thazırlık provası**: kutudan "Takım Hazır"a kronometre | süre |
| ☐ | Gün kapanışı: `results/faz_b_20260905/` + `REVIEW_LOG` | eksik = ÖLÇÜLEMEDİ |

---

## 3. UÇUŞ TESTLERİ — 6–19 Eylül (pilot: kullanıcı; tek pil → günde ≤ 2 uçuş)

> ⚠ **Rol çakışması (3 Eylül beyanı):** kullanıcı hem **R2 Pilot** hem
> **R5 YKS operatörü**. Uçuş anında ikisi eşzamanlı olduğu için (kumanda ↔ hakem
> ekranı) uçuş günü bu rollerden biri ikinci bir kişiye geçmelidir. Montaj ve yer
> provalarında çakışma yoktur.

| ✓ | adım | kapı |
|---|---|---|
| ☐ | **3.1 İlk hover** (Stabilize/AltHold, 2–3 m, 2 dk): titreşim, pusula, GPS, motor ısısı; **pervaneler ilk kez takılır** | log `VIBE`, EKF yeşil, kırım yok |
| ☐ | **3.2 Loiter + kısa Auto** (30 m) + geofence testi; **iniş kanıtı canlı** (`iha_inis_yayinci` IHA_LANDED ACK'li) | YKS "İNİŞ" |
| ☐ | **3.3 Algı canlı**: 30 m'de alan üstünde OPEN_ROUTE YKS'de; kare kaydı; yanlış güzergâh 0 | `results/prova/` |
| ☐ | **3.4 Tam prova ×3** (8 faz, İKA fazları isteğe bağlı): kalkış → tarama → tespit → hakem onayı (rol) → iniş → IHA_LANDED; **≤ 10 dk**; video + `hakem_log` | 3 temiz prova |
| ☐ | **3.5 Sıkı prova**: kapalı kutudan başla, thazırlık kronometre, hands-off; tekrar kalkış provası | 0 müdahale |
| ☐ | **3.6 Sürüm dondurma** (mühür sırası D-405: türev kaydı → commit → `--dondur` → künye commit) | künye repoda, `--dogrula` 0 |
| ☐ | **3.7 UHDR**: otonom harekât videoları, algoritma/model künyesi, gerçek kütle/boyut, takvim sapması (M10→M9N, Mauch→FCHUB, Orin NX→~~Nano~~ **Orin Nano 4 GB** — 6 Eylül ölçümü, D-431) | rapor |

---

## 4. TAKVİM (ekibe) — 3 → 21 Eylül (provaya ve FDR teslimine kadar)

| gün | ne | kim (rol) | kapı |
|---|---|---|---|
| **Çar 2 (akşam)** | D-405 kapanışı; plan + takvim | AI, kaptan | — |
| **Per 3** | **Jetson Nano yığını** (§1.3): tekerlek listesi/betik, `JETSON_NANO_KURULUM.md`; **kamera köprüsü** (§1.4) + test; ArduCopter param + waypoint şablonu; çürütücü ikinci tur; **alışveriş listesi kesinleşir** (§1.11) | AI · kaptan alışveriş | suit yeşil; dosyalar repoda |
| **Cum 4** | ~~microSD flash~~ **→ Ubuntu'lu host ayarla (eMMC boş çıkarsa gerekecek, D-413)**; tekerlekler + paket belleğe; YKS PC hazır (§1.8); cuma akşamı §0 listesi; basılı listeler; alışveriş tamam; **kargo teslim alınır** | insan (Jetson/kamera, YKS, kaptan) · AI | `results/faz_b_oncesi/`; bellek hazır |
| **Cmt 5** | **MONTAJ GÜNÜ** (§2.1–2.6): kutu → mekanik → kablo → Pixhawk → Nano kurulumu → yer zinciri; **pervanesiz** | herkes; pilot yapılandırmada | `mavlink_dogrula` 3/3; HEARTBEAT YKS'de; FPS ölçüldü |
| **Paz 6** | Sabah: eksikler + pusula kalibrasyonu dışarıda; **ilk hover** (3.1), ikinci uçuş: Loiter/Auto + iniş kanıtı (3.2) — 2 uçuş, arada şarj | pilot, aviyonik, YKS | log + IHA_LANDED |
| **Pzt 7 – Cum 11** | Uçuş günlerini kaptan seçer (≥ 2 gün): **algı canlı** (3.3), ilk **tam prova** (3.4/1); hafta içi akşamları: log analizi, `hakem_log`, kare kaydı; yazılım tarafında **yalnız** kusur kaydı | pilot, YKS, Jetson, AI (analiz) | 1 tam prova ≤ 10 dk |
| **Cmt 12 – Paz 13** | **Tam prova ×2** (3.4/2–3) — günde 2 uçuş; 2. pil varsa 3 | herkes | 3 temiz prova toplam |
| **Pzt 14 – Çar 16** | **Sıkı prova** (3.5): kapalı kutu, kronometre, hands-off; tekrar kalkış; eksik onarımları (mühürden önce son kod değişikliği penceresi) | herkes, AI | 0 müdahale |
| **Per 17** | **Sürüm dondurma** (3.6): türev kaydı → commit → `--dondur` → künye commit; Jetson'da `--dogrula` 0; **bundan sonra kod değişmez** | AI, kaptan | künye repoda |
| **Cum 18** | **KESİN HAZIR** (§5 listesi baştan sona); UHDR videoları/bölümleri (3.7); yedek pervane/kablo/pil paketi; taşıma kutusu | herkes | tutanak |
| **Cmt 19** | Yedek gün: son prova (isteğe bağlı, kod değişmeden), pil tam şarj, ekipman listesi | pilot, kaptan | — |
| **Paz 20** | **Adıyaman'a yolculuk**; akşam otelde: YKS PC + Jetson kuru koşu (`--durum`), pil şarj | herkes | — |
| **Pzt 21** | **GÖREV TEST UÇUŞU — Adıyaman** (§6 akışı) | herkes | kanıt klasörü |
| 22–30 | Tutanak, UHDR son hali; final dalgası (§7) başlar | — | — |

**Pil kuralı:** iMAX B6 ile ~3 saat dolum → uçuş günü en fazla 2 uçuş; 2. pil + ≥150 W şarj cihazı prova sayısını ikiye katlar (kaptan kararı).

---

## 5. "KESİN HAZIR" tanımı (18 Eylül) — hepsi aynı anda doğru

- ☐ Drone: 3 tam prova ≤ 10 dk, sıfır kırım; geofence/failsafe'ler test edildi; pil sağlığı; yedek pervane.
- ☐ Jetson: mühürlü sürüm (`--dogrula` 0), FPS ≥ 0,61, ekransız birimler `--durum` 0 restart, kamera köprüsü + FOV beyanı.
- ☐ Pixhawk: parametre dosyası repoda, `mavlink_dogrula` 3/3, `SYSID_THISMAV=1`; fence/görev koordinatları Adıyaman'da girilecek (**tek izinli değişiklik**, tutanakla).
- ☐ YKS: tek komut açılış, hakem ekranı, ACK'li onay, kronometreler (10 dk uyarısı).
- ☐ Telsiz: SiK RTT p95 < 0,2 s; anten yerleşimi.
- ☐ İnsan: roller belli, basılı listeler, yedek parça, taşıma kutusu.
- ☐ Kanıt: `results/prova/` (3 klasör), `REVIEW_LOG` kayıtları, UHDR videoları.

---

## 6. 21 EYLÜL — Adıyaman akışı

| t | rol | ne | kanıt |
|---|---|---|---|
| −90 dk | kaptan, pilot | alan keşfi; fence poligonu + görev waypoint'leri **gerçek koordinatlarla** (tutanak) | ekran görüntüsü |
| −45 dk | Jetson | Nano açık, `jetson_baslat.sh --durum` 0 restart, kamera köprüsü canlı. ⚠ **Pil değişimi = Pixhawk reboot = `EXTENDED_SYS_STATE` akış isteği silinir** (D-406 A): pil takıldıktan sonra `jetson_baslat.sh --kapi` **yeniden** koşulur (3/3 GEÇTİ); T207 ile yayıncı isteği kendisi periyodik yeniler, yine de `--kapi` kanıttır | YKS'de HEARTBEAT; `--kapi` 3/3 |
| −30 dk | YKS | `saha_baslat.py yks ...`; hakem ekranı | karar akıyor |
| −15 dk | aviyonik, pilot | pil tam, pervaneler, CG, arm ön kontrol mesajları temiz, RC/failsafe | tutanak |
| 0 | kaptan | **"Takım Hazır"** → hands-off | kronometre |
| +1 | hakem | uçuşa uygunluk → YKS'den ARM (ACK) | ✓ |
| +1–2 | otonom | Auto: kalkış, 30 m (**10 dk kronometresi başlar**) | YKS |
| +2–5 | otonom | tarama; OPEN_ROUTE yayını; **hakem ekranda onaylar** (YKS iki aşamalı onay) | hakem_log |
| +5–7 | otonom | loiter → iniş noktası → **iniş** (IHA_LANDED) | YKS "İNİŞ" |
| +7 | kaptan | tutanak: süre, onay, log/video kopyası | `results/gorev_20260921/` |

**Sıra değişmez:** aktarım ve hakem onayı inişten **önce**; manuel müdahale = uçuş başarısız.

---

## 7. FİNAL için ek dalga (görev test uçuşundan sonra) — sabit kanat + mancınık + paraşüt + İKA

ArduPlane (`TKOFF_*` mancınık, airspeed, servo/CG) · paraşüt (`CHUTE_*`, otonom tetik + YKS manuel yedek −50; `iha_komut_alici` zinciri hazır) · mancınık testleri · İKA (gerçek sürücü, IHA_LANDED+IKA_GO kilidi, temas, yük) · SiK/İKA hattı kararı (D-405) · mühürlü kutu tatbikatı · ağırlık tutanakları (25 kg / 10 kg) · SGGS BOM.

---

## 8. En büyük riskler

| risk | önlem |
|---|---|
| ~~**Nano yığını kurulamaz** (Py3.8/torch/kamera)~~ **KAPANDI (D-431):** Orin Nano yığını 6 Eylül'de kuruldu, FPS GEÇTİ; kamera CSI ÖLÇÜLEMEDİ (kamera bağlı değildi) | perşembe hazırlık + çevrimdışı tekerlekler; **CPU torch garanti yolu**; **USB webcam yedek**; cumartesi §2.5 bitmezse pazar sabahı devam |
| **Yanlış güzergâh = 0** | histerezis, tek pas, hakem ekranında güven + sebep |
| **10 dk aşımı** | kısa görev planı; loiter ACK tavanı; YKS kronometre |
| **Tek pil** | uçuş planı günde 2; 2. pil/şarj kararı kaptanda |
| **Çökme döngüsü hands-off'ta** | ekransız kip, `Restart=always`, çoğullayıcı |
| **Pusula/GPS/titreşim** | direk montaj, dışarıda kalibrasyon, damper, ilk hover logu |
| **PM02 akım sınırı** | sürekli tam gaz yok; `BATT_AMP` ekranda; motor testi kısa |

## 9. Bu belgenin sınırı
Hiçbir adım yapılmış sayılmaz; her satır koşulup kanıtı klasöre düşünce deftere geçer. Lens/FOV ve Nano'da CUDA durumu cumartesi ölçülür. Kişi ataması kaptanındır.
