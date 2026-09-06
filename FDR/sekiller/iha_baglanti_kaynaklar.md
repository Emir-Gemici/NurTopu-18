# İHA bağlantı şeması — hat başına kaynak

Şema: `iha_baglanti.svg` (çizim 2026-09-07; üreten `scripts/fdr_iha_baglanti_svg.py`, iki dosya aynı tablodan çıkar). Yönerge Y-3.3.1-M01.

**Kural:** kaynaksız hat çizilmez. **Düz çizgi** = bir D-kaydındaki saha ölçümü ya da `config/pixhawk/arducopter_fda_20260906.param` dökümü. **Kesik çizgi** = `DOĞRULANACAK`: yalnız plan/künyeden bilinen, sahada ölçülmemiş hat. `param:AD,DEĞER` atıfları dökümdeki satırın birebir kopyasıdır.

**Kaynak belgeler:** `REVIEW_LOG.md` D-426 (5 Eylül saha tutanağı), D-428 (6 Eylül akşam tutanağı), D-429 §4 (dökümden plan dışı değerler); `config/pixhawk/arducopter_fda_20260906.param` (6 Eylül 20:22 dökümü); `config/pixhawk/arducopter_fda.param` (şablon, SERIAL↔TELEM eşleme yorumları); `SAHA_HAZIRLIK_PLANI_20260903.md` §2.3; `FDR/BOLUM_5_URETIM_FAALIYETLERI.md` §5.2.3–§5.2.5; `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` §3.2.1.1; `jetson_paket/JETSON_NANO_KURULUM.md` §2.1, §2.4.

## Renk sözlüğü

| tür | renk | hex |
|---|---|---|
| `guc` | güç + (kırmızı) | `#c62828` |
| `guc_gnd` | güç − / GND (siyah) | `#212121` |
| `pwm` | PWM sinyal (turuncu) | `#ef6c00` |
| `uart` | UART (mavi) | `#1565c0` |
| `i2c` | I2C (mor) | `#6a1b9a` |
| `csi` | CSI şerit (yeşil) | `#2e7d32` |
| `rc` | RC iBUS (sarı) | `#f9a825` |
| `gpio` | emniyet düğmesi GPIO (gri) | `#616161` |

## Hatlar

| hat | ad | nereden → nereye | tür | durum | kaynak |
|---|---|---|---|---|---|
| H01 | Ana güç: pil → PM06 | 4S LiPo 10 Ah (fiş XT60/XT90 — hangisi olduğu BEYAN GEREKLİ) → PM06 güç modülü girişi | `guc + guc_gnd` | ÖLÇÜLDÜ (pil takılı; PreArm pil uyarısı kayboldu) | D-426 §1 (18:03 pil takıldı, `PreArm: Battery 1 low voltage failsafe` listeden kayboldu); fiş tipi: FDR BOLUM_5 §5.2.4 ve BOLUM_3 §3.2.1.1 'XT60/XT90' — tek tip beyan edilmedi |
| H02 | PM06 → Pixhawk POWER1 (6-pin: 5 V · GND · V/I sens) | PM06 → Pixhawk 6C `POWER1` | `guc + guc_gnd` | ÖLÇÜLDÜ (6 pinli kablo; pil gerilimi MP ↔ multimetre 15,8 V) | D-426 §1 (18:03 satırı: pil takıldı, PM06 → POWER1 çalışıyor), D-426 §2 (8 pinli kablo uymadı, 6 pinli takıldı, uydurma adaptör yapılmadı); D-428 §1 (MP 15,8 ↔ multimetre 15,8 V); param:BATT_MONITOR,4 · param:BATT_VOLT_PIN,8 · param:BATT_CURR_PIN,4 |
| H03 | PM06 çıkışı → FCHUB-12S V2 (PDB) | PM06 çıkış → FCHUB-12S V2 pil pad'leri | `guc` | DOĞRULANACAK — D-426/428/429'da FCHUB anılmıyor; PM06 çıkışının ESC'lere yolu ölçülmedi | SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Ana güç' satırı; FDR BOLUM_5 §5.2.4 'Ana güç' satırı (plan, ölçüm değil) |
| H04 | FCHUB → ESC ×4 güç (+/−) | FCHUB-12S V2 → 4× ESC güç girişi | `guc` | DOĞRULANACAK — motor testi koştu (D-426 §1 18:06) ama ESC'lerin hangi noktadan beslendiği tutanakta yok | SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Ana güç' satırı; FDR BOLUM_5 §5.2.4; BOLUM_3 §3.3.2.1 'doğrulanacak bağlantılar' (künyeden, ölçüm değil) |
| H05 | FCHUB pil pad'i → UBEC 5 V / 5 A | FCHUB-12S V2 pad → UBEC girişi | `guc` | DOĞRULANACAK — Jetson ve UBEC sahada takılı değil (D-426 §4 'Jetson takılı DEĞİL') | SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson güç' satırı; FDR BOLUM_3 §3.2.1.1 'Jetson beslemesi'; D-426 §4 (Jetson takılı değil) |
| H06 | UBEC → Jetson Nano J25 barrel (+ J48 jumper) | UBEC 5 V / 5 A çıkışı → Nano `J25` barrel jack; `J48` jumper takılı; ortak GND | `guc` | DOĞRULANACAK — Nano kurulumu ve güç ölçümü yok | jetson_paket/JETSON_NANO_KURULUM.md §2.1 (barrel 5 V/≥ 4 A + J48); FDR BOLUM_3 §3.2.1.1; SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson güç' (5,0–5,2 V yük altında — ÖLÇÜLEMEDİ) |
| H07 | ESC sinyal ×4 → Pixhawk AUX1–4 (adaptör kartı üzerinden) | 4× ESC sinyal teli → Pixhawk 6C FMU PWM OUT `AUX1..AUX4` = `SERVO9..12` | `pwm` | ÖLÇÜLDÜ (döküm + pervanesiz motor testi + tlog) | D-428 §1 ESC künyesi (3 telli fiş, Pixhawk ile gelen 'PWM IN / PWM OUT' adaptörü üzerinden AUX); D-428 §5d (AUX 1–4 = M4, M2, M1, M3); D-429 §1 (tlog: AUX1=M4 sağ arka · AUX2=M2 sol arka · AUX3=M1 sağ ön · AUX4=M3 sol ön); param:SERVO9_FUNCTION,36 · param:SERVO10_FUNCTION,34 · param:SERVO11_FUNCTION,33 · param:SERVO12_FUNCTION,35 · param:MOT_PWM_TYPE,0 · param:RC_SPEED,490 (D-429 §4: 400 yazılacak) |
| H08 | ESC BEC 5 V ×4 → Pixhawk servo rayı (paralel) | 4× ESC kırmızı tel (BEC 5 V / 5 A) → Pixhawk AUX servo rayı (+5 V) | `guc` | ÖLÇÜLDÜ (4 kırmızı tel rayda paralel) — karar: 3'ü çıkarılacak, yapılmadı | D-428 §1 (3 telli fiş, BEC 5 V/5 A); D-428 §5f (4 BEC paralel, ertelendi); D-429 §4 'ESC BEC: 4 kırmızı tel rayda paralel — 3'ü çıkar' |
| H09 | ESC → motor 3 faz ×4 (5008 340 KV) | 4× ESC → M1 sağ ön · M2 sol arka · M3 sol ön · M4 sağ arka (quad-X) | `guc` | ÖLÇÜLDÜ (motor testi koştu); sıra/yön 4/4 BEYAN — video yok; M1 hasarlı | D-426 §1 (18:06 `starting motor test` → `finished motor test`; ~18:30 sıra/yön 4/4 BEYAN, video BEYAN GEREKLİ); D-429 §2 madde 4 (M1 sağ ön hasarlı) ve §6 madde 2 (motor yönü videosuz doğru sayılmaz); yerleşim: FDR BOLUM_5 §5.2.3 (1 sağ ön CCW, 2 sol arka CCW, 3 sol ön CW, 4 sağ arka CW); param:FRAME_CLASS,1 · param:FRAME_TYPE,1 |
| H10 | M9N GPS → Pixhawk GPS1 (UART) | Holybro M9N u-blox → Pixhawk 6C `GPS1` seri hattı | `uart` | ÖLÇÜLDÜ (modül tanındı; 18 uydu, EKF GPS kullanıyor) | D-426 §1 (15:38 `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10`); D-428 §1 GPS/EKF satırı (18 uydu, `EKF3 IMU0/IMU1 is using GPS`); param:GPS_TYPE,1 · param:SERIAL3_PROTOCOL,5 |
| H11 | M9N pusula → Pixhawk GPS1 (I2C, harici) | M9N üstündeki pusula → Pixhawk 6C `GPS1` I2C hattı | `i2c` | ÖLÇÜLDÜ (harici pusula dökümde; iki kalibrasyon, ofset < 300) | param:COMPASS_EXTERNAL,1 · param:COMPASS_DEV_ID,658953 (dev-id 0xA0E09, düşük 3 bit = 1 = I2C veri yolu — ArduPilot DeviceId kodlaması, hesap); D-428 §1 pusula satırı (OFS/OFS2 < 300, ikinci kalibrasyon PreArm temiz); D-429 §4 (`COMPASS_ORIENT` 6, direkte 90° dönük) |
| H12 | Emniyet düğmesi (M9N üstü) → Pixhawk GPS1 (GPIO) | M9N üstündeki emniyet düğmesi → Pixhawk 6C `GPS1` düğme/LED hattı | `gpio` | ÖLÇÜLDÜ (düğme fiziksel olarak çözüldü; PreArm satırı kayboldu) | D-426 §1 (18:05 `PreArm: Hardware safety switch` kayboldu; öncesinde 12× `Motor Test: Safety switch`); D-426 §2 (düğme M9N üstünde, `BRD_SAFETY_DEFOFF` değiştirilmedi); param:BRD_SAFETY_DEFLT,1 |
| H13 | Pixhawk GPS1 → M9N besleme (5 V) | Pixhawk 6C `GPS1` 5 V → M9N | `guc` | ÖLÇÜLDÜ dolaylı: modül yalnız GPS1 kablosuyla bağlıyken tanındı; ayrı besleme yok | D-426 §1 (15:38 modül tanındı); SAHA_HAZIRLIK_PLANI_20260903.md §2.3 ve FDR BOLUM_3 §3.3.1.1.7 (M9N için ayrı güç satırı yok) |
| H14 | Pixhawk TELEM1 → SiK 433 MHz (UART, MAVLink2 57600) | Pixhawk 6C `TELEM1` (= SERIAL1) → SiK telemetri modülü (RF ↔ YKS SiK, USB) | `uart` | DÖKÜM (SERIAL1) · fiziksel bağlantı BEYAN — RTT / paket kaybı ÖLÇÜLEMEDİ | param:SERIAL1_PROTOCOL,2 · param:SERIAL1_BAUD,57; şablon config/pixhawk/arducopter_fda.param yorumu 'SERIAL1 = UART7 = TELEM1'; D-426 §1 (~18:45 SiK bağlandı, BEYAN); SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Telemetri' (JST-GH 6 pin, TX↔RX çapraz) |
| H15 | Pixhawk TELEM2 → Jetson Nano UART (3 tel, 3,3 V; 5 V BAĞLI DEĞİL) | Pixhawk 6C `TELEM2` (= SERIAL2) TX/RX/GND → Nano 40-pin `/dev/ttyTHS1`: pin 8 TX · pin 10 RX · pin 6 GND | `uart` | DOĞRULANACAK — parametre dökümde hazır; Jetson sahada takılmadı | param:SERIAL2_PROTOCOL,2 · param:SERIAL2_BAUD,57 · param:BRD_SER2_RTSCTS,0; şablon config/pixhawk/arducopter_fda.param yorumu 'SERIAL2 = UART5 = TELEM2'; FDR BOLUM_3 §3.2.1.1 'Pixhawk ↔ Jetson bağlantısı'; SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson ↔ Pixhawk'; D-426 §4 (Jetson takılı DEĞİL) |
| H16 | FS-iA6B `i-BUS SERVO` → Pixhawk `PPM/SBUS RC` (iBUS) | FS-iA6B alıcı `i-BUS SERVO` portu (CH1–CH6 DEĞİL) → Pixhawk 6C `PPM/SBUS RC` | `rc` | ÖLÇÜLDÜ (`RCInput: decoding IBUS(1)`) — ⚠ RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ | D-426 §1 (18:03 `RCInput: decoding IBUS(1)`); D-426 §2 (alıcı önce `CH6`'daydı, `i-BUS SERVO`'ya alındı); SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'RC' satırı (5-pin JST-GH, `PPM/SBUS RC`); param:RC_PROTOCOLS,1; D-428 §2 (kumanda kapatılınca `Radio Failsafe` gelmedi) |
| H17 | RPi HQ kamera → Jetson Nano CSI (IMX477 şerit) | Raspberry Pi HQ kamera (IMX477) → Nano CSI konnektörü (mavi taraf dışa, kilit kapalı) | `csi` | DOĞRULANACAK — Nano kurulumu ve `jetson-io` overlay'i yapılmadı | jetson_paket/JETSON_NANO_KURULUM.md §2.4 (IMX477 overlay, şerit yönü); SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Kamera' satırı; FDR BOLUM_3 §3.2.1.1 kamera satırı |

## Çizilmeyenler (bilerek)

- **İKA bağlantı şeması** — İKA aviyoniği tedarik edilmedi (FDR BOLUM_3 §3.2.2); çizilecek ölçülmüş topoloji yok.
- **Pixhawk USB** (SERIAL0) — yalnız tezgâh/ESC kalibrasyonu (D-428 §3), uçuş bağlantısı değil.
- **Kablo kesitleri, uzunlukları, konnektör tipleri** — ÖLÇÜLMEDİ (FDR BOLUM_5 §5.2.5, BEYAN GEREKLİ).
- **Pixhawk MAIN 1–8 ve AUX 5–8** — fiziksel bağlantı yok; dökümde başıboş motor fonksiyonları var, 0'lanacak (D-428 §5d, D-429 §4).
- **GPS1 kablosundaki LED / buzzer telleri** — tutanakta ölçüm yok.

## Bilinen metin tutarsızlıkları (şema dökümü esas alır)

- FDR BOLUM_3 §3.3.1.1.7 ASCII topolojisi ve BOLUM_5 §5.2.4 'ESC sinyal' satırı **`MAIN 1..4`** yazar; döküm ve D-428 §5d **AUX 1–4 (`SERVO9–12`)** diyor. Bu şema dökümü esas alır; metinler düzeltilmelidir.
- SAHA_HAZIRLIK_PLANI_20260903.md §2.3 ve §0.2 hâlâ **PM02** ve **`MAIN OUT 1–4`** yazar (D-426 §3: PM06; D-428 §5d: AUX).
- Şablon config/pixhawk/arducopter_fda.param `RC_SPEED` yorumu 'PWM 400 Hz (MAIN 1-4)' — döküm 490, karar 400 (D-429 §4).

## Sayım

- Hat: **17** · düz (ölçüm/döküm): **11** · kesik (DOĞRULANACAK): **6**
- İKA şeması: **çizilmedi** (aviyonik yok).
