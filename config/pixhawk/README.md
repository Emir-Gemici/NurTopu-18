# `config/pixhawk/` — ArduCopter parametre + görev şablonu (FDA görev test uçuşu)

> **NEDEN** (`SAHA_HAZIRLIK_PLANI_20260903.md` §1.6, §1.7, §2.4): Pixhawk 6C 5 Eylül'de
> **ilk kez** yapılandırılacak. Mission Planner'da elle tıklanan değerin tutanağı da testi de
> yoktur; bu klasördeki dosyalar repoda durur, `tests/test_faz_b_pixhawk_sablon.py` ile
> kilitlidir ve sahada **tek komutla** yüklenir. Sahada alınan gerçek parametre dökümü
> `arducopter_fda_20260905.param` adıyla **ayrıca** commit edilir (§2.4 son satır).

| dosya | ne | biçim |
|---|---|---|
| `arducopter_fda.param` | ArduCopter 4.x parametreleri, her satırın üstünde NEDEN yorumu | Mission Planner `.param` — `AD,DEGER`; `#` yorum |
| `fda_gorev.waypoints` | kalkış → 32 m → 20×20 m üstünde tek pas → loiter (ACK) → iniş | `QGC WPL 110` (sekmeyle ayrılmış 12 sütun) |
| `README.md` | bu dosya: yükleme, sahada değişecekler, TEYİT listesi, karar noktaları | — |

Değerlerin kaynağı: parametre adları ve değer tabloları **ArduPilot Copter-4.5 kaynak
kodundan** okundu (dosya adları `.param` başlığında). Sözleşme sabitleri
`codes/karar_sozlesmesi.py`'den: `SARTNAME_ASGARI_IRTIFA_M` (30), `SENARYO_BOYUTLARI_M["FDA"]`
(20), `MAVLINK_KONUM_ASGARI_HZ` (4), `MAVLINK_DURUM_ASGARI_HZ` (1), `SARTNAME_FDA_OPERASYON_SURESI_S`
(600). `SYSID_THISMAV` = `comms/iha_komut_alici.VARSAYILAN_HEDEF_SYSID`.

---

## 1. Nasıl yüklenir (Mission Planner, §2.4 · 13:00–14:30)

**Parametreler**

0. 🔴 **ÖN KOŞUL — KARTTA ArduCopter VAR MI?** Pixhawk 6C fabrikadan **PX4 yüklü** çıkar
   (D-424, 5 Eylül'de sahada ölçüldü: yeni kartta `Messages` sekmesi boştu).
   Teşhis: `Config` → `Full Parameter List` → `Refresh Params`.
   `FRAME_CLASS`/`WPNAV_SPEED`/`ATC_*` → ArduCopter var, devam.
   `MC_*`/`MPC_*`/`COM_*` → **PX4**; flash gerek.

   🔴 **SÜRÜM SABİTTİR: ArduCopter 4.5.7 — Mission Planner'ın önerdiği "en son
   kararlı" DEĞİL** (D-425). MP'nin quadcopter ikonu bugün **4.7.1** yükler ve
   bu dosyadaki **31 parametrenin 9'u 4.7'de yoktur** (Copter-4.7 SI birim
   reformu). 5 Eylül'de gerçek kartta ölçüldü: MP *"Missing 9 params"* dedi.

   **Doğru yol:** **Disconnect** → `Setup` → `Install Firmware` →
   **`Load custom firmware`** → `firmware/arducopter.apj` (4.5.7;
   `scripts/pixhawk_firmware_indir.py` indirir, saha belleğine kopyalanır —
   **sahada internet gerekmez**). İkona tıklama, dosyayı seç.

   Açılışta `ArduCopter V4.5.7` görülmelidir. **4.7.x görüyorsan yanlış sürüm.**
   ⚠ **Flash TÜM parametreleri sıfırlar.** Sıra: **firmware → param**, tersi değil.
1. Pixhawk'a USB ile bağlan, **Connect**. Firmware ArduCopter **kararlı** sürüm (sürüm numarası
   tutanağa; Messages sekmesinde ilk satır — **kart açıldıktan sonra bağlanırsan bu satırları
   kaçırırsın**, sürümü MP'nin üst durum çubuğundan da okuyabilirsin).
   ⚠ **Sürüm `4.5.7` olmalı.** Bu dosya Copter-4.5 kaynağından yazıldı ve
   `tests/test_faz_b_pixhawk_sablon.py` onu 4.5 anlambilimine göre kilitler.
   §3 TEYİT listesi yine de tek tek işaretlenir: yama sürümleri arasında bile
   değer tablosu değişebilir, ve **görülmeden yüklendi sayılmaz**.
2. `Config` → `Full Parameter List` → sağ sütunda **`Load from file`** → `arducopter_fda.param`.
   Liste yalnız dosyadaki satırları değiştirir; dosyada olmayan parametreler firmware
   varsayılanında kalır.
3. **`Write Params`**. Ekranda çıkan "reboot required" uyarısı beklenir: `SERIAL*`, `SR*`,
   `BRD_*` yeniden başlatmada etkin olur → Pixhawk'a **güç kes-ver**.
4. Yeniden bağlan → **`Refresh Params`** → **`Compare Params`** ile dosyayla karşılaştır:
   fark listesi **boş** olmalı (fark varsa yazılmamış demektir; tekrar yükle).
5. TEYİT listesini (§3) tek tek işaretle.
6. `Config` → `Full Parameter List` → **`Save to file`** → `arducopter_fda_20260905.param` → repoya.

**Görev planı**

1. `Flight Plan` sekmesi → sağ tık / sağ panel **`Load WP File`** → `fda_gorev.waypoints`.
2. Şablon **Null Island'da** (0°, 0°) 20 m'lik bir kare çizer: **her koordinat yer tutucudur**
   (§2). Adıyaman'da alan koordinatları girildikten sonra **`Write WPs`**, ardından
   **`Read WPs`** ile geri oku ve listede 8 satırı (0..7) gör.
3. Home: araç arm edildiği yeri home alır; MP'de "Set Home Here" ile de girilebilir.

**Sıra ve süre bütçesi (SS5.3.2: kalkış+tespit+aktarım+iniş ≤ 10 dk)**

| # | komut | değer | süre (kaba, `WPNAV_SPEED` 3 m/s · `LAND_SPEED` 0,5 m/s) |
|---|---|---|---|
| 0 | HOME | yer tutucu 0,0 | — |
| 1 | `NAV_TAKEOFF` | **32 m** göreli (şartname ≥ 30 m + 2 m baro/EKF payı; `rpi_inference` 30 m altını `ASGARI_IRTIFA_ALTI` işaretler) | ~15 s |
| 2–5 | `NAV_WAYPOINT` ×4 | 20×20 m karenin köşeleri (GB→KB→KD→GD), 32 m | ~30 s + köşe yavaşlamaları |
| 6 | `NAV_LOITER_TIME` | **60 s** — YKS'ye canlı aktarım + iki aşamalı onay + hakem ACK penceresi; lat/lon 0,0 = bulunduğu yerde | 60 s |
| 7 | `NAV_LAND` | | ≤ 60 s (tamamı `LAND_SPEED` ile) |

Toplam kötü durum ≈ 3–3,5 dk ≪ 10 dk. Test (`P7`) bu bütçeyi `.param` dosyasındaki hızlarla
**hesaplar** ve `SARTNAME_FDA_OPERASYON_SURESI_S` ile karşılaştırır. Hakem onayı 60 s'de gelmezse
pilot **Loiter** moduna alıp bekler; sonra `RTL`/`Land` — `Auto`'ya geri dönmek gerekmez.

---

## 2. Sahada değişecek TEK şeyler

| ne | nerede | not |
|---|---|---|
| **Koordinatlar** | `fda_gorev.waypoints` satır 0 (home) ve 2–5 (köşeler); 6 (loiter) isteğe bağlı | Şablonda 0,0 çevresinde `±0.0000898315°` (= ±10 m, `DUNYA_YARICAPI_M` ile) — kare şeklini korur; Adıyaman'da **kaptan** gerçek köşeleri girer (§1.7) |
| **Fence poligonu** | Mission Planner `Flight Plan` → `Fence` → poligon çiz → `Upload` | Poligon yüklenince `FENCE_TYPE` **3 → 7** (bit 2 = Inclusion/Exclusion Circles+Polygons); `FENCE_RADIUS` alan yerleşimine göre yeniden ölçülür |
| **Kalibrasyonlar** | Accel, level, pusula, radyo, ESC (§2.4) | Parametre dosyasında **yoktur**, dosya bunları ezmez |
| **Tutanak dökümü** | `arducopter_fda_20260905.param` | §2.4 son satır; şablon dosyasına dokunulmaz |

Başka hiçbir değer sahada "gözle" değiştirilmez; zorunlu değişiklik = D-kaydı + bu README + test.

---

## 3. TEYİT listesi — Pixhawk'ta doğrulanacak parametreler

`.param` dosyasında `# TEYIT:` ile işaretli adların **aynısı** (test `P5`: metin kilidi — biri
değişirse ikisi birden değişir). Her satır Mission Planner'da açılıp **görülmeden** "yüklendi"
denmez.

- `BRD_SER2_RTSCTS` — 0 (Disabled) görülsün. Jetson UART 3 telli; TELEM2'den HEARTBEAT gelmiyorsa **ilk** bakılacak parametre.
- `RC_PROTOCOLS` — 4 (bit 2 = IBUS). Radio Calibration'da kanallar oynamıyorsa 1 (All) yapıp tekrar dene; Messages'ta `RCInput: decoding IBUS`.
  ⚠ **5 Eylül sahada 1'e alındı** (teşhis sırasında; asıl sorun alıcının `CH6`'ya takılı olmasıydı, D-426). iBUS doğrulandı; **4'e geri alınıp alınmadığı** parametre dökümünde görülecek — geri almak tercih edilir (Emir kararı).
- `BATT_FS_LOW_ACT` — 2 = **RTL** olduğu MP açıklamasında görülsün (firmware 4.5 tablosu; farklı sürümde tablo tekrar okunur).
- `BATT_FS_CRT_ACT` — 1 = **Land** olduğu görülsün (aynı tablo).

---

## 4. Sahada ayrıca kontrol (parametre dışı, `mavlink_dogrula` kapısıyla)

- **`scripts/mavlink_dogrula.py` üç uçta GEÇTİ** (CONTRACTS §7.4): HEARTBEAT sysid 1,
  `GLOBAL_POSITION_INT ≥ 4 Hz`, `EXTENDED_SYS_STATE ≥ 1 Hz`. Bu ölçüm, `SR*` değerlerinin
  **gerçek etkisidir**; dosya yüklendi diye geçmiş sayılmaz.
- **PM02 ölçeği**: `BATT_VOLT_MULT` / `BATT_AMP_PERVLT` dosyada **yok** (Pixhawk 6C hwdef
  varsayılanı 18.18 / 36.36). MP'de okunan pil gerilimi multimetreyle ±0,1 V içinde olmalı;
  değilse D-kaydıyla düzeltilir.
- **Mission Planner "Telemetry Rates"** (`Config` → `Planner`): MP bağlanınca kendi hızlarını
  ister ve `SR1_*` değerlerini **ezer**. YKS haritası için `Position ≥ 4` seçili olsun
  (varsayılan değerleri sahada görülecek — burada sayı verilmez).
- **`FS_GCS_ENABLE` etkisi**: Jetson'daki MAVProxy `--source-system` varsayılanı 255 ile GCS
  heartbeat basar; SiK kopsa bile Jetson yaşarken GCS failsafe **tetiklenmez**. "YKS ekranı gitti"
  durumunun cevabı bu failsafe değil, pilot + `RTL` anahtarıdır (§2.4 mod anahtarı).
  **Mimar kararı (D-406 C): `FS_GCS_ENABLE=1` KALIR** ve anlamı "Jetson-bağlantı failsafe'i"dir:
  Jetson/MAVProxy ölürse (güzergâh tespiti yok) `RTL`/`Land` doğru davranıştır; SiK kopması
  görevi durdurmamalıdır.

---

## 5. Karar noktaları ve bilinen riskler (mimara)

1. **`EXTENDED_SYS_STATE` hiçbir `SR*` akışında yok** (Copter-4.5 `ArduCopter/GCS_Mavlink.cpp`
   `STREAM_*_msgs` dizilerinin tamamı okundu). Yalnız `MAV_CMD_SET_MESSAGE_INTERVAL` ile istenince
   akar; istek **bağlantıya özeldir ve Pixhawk yeniden başlayınca silinir**. Bugün bu isteği yalnız
   `scripts/mavlink_dogrula.py` gönderiyor; `comms/iha_inis_yayinci.py` / `comms/inis_kaniti.py` /
   `codes/rpi_inference.py` **istemiyor** (grep: 0). Sonuç: pil değişimi (= Pixhawk reboot)
   sonrası `mavlink_dogrula` tekrar koşulmazsa iniş kanıtı **hiç oluşmaz**. Öneri: tüketici
   süreçler açılışta kendi `SET_MESSAGE_INTERVAL` isteğini göndersin (üretim kodu; bu görevin
   kapsamı dışında, D-kaydı ister). Bu dosya `SR2_EXTRA3` ile bunu **çözmez**, çözüyormuş gibi de
   yazmaz. **→ D-406 A / T207:** `iha_inis_yayinci` isteği kendisi periyodik yeniler (amele);
   o güne dek **saha kuralı**: her Pixhawk reboot'undan (pil değişimi) sonra
   `jetson_baslat.sh --kapi` tekrar (3/3 GEÇTİ) — `SAHA_HAZIRLIK_PLANI` §6, `FAZ_B_GUN_PLANI` §2.
2. **MAVProxy `--streamrate` varsayılanı 4**: `navitas-cogullayici` bağlanınca
   `REQUEST_DATA_STREAM(ALL, 4 Hz)` gönderir → TELEM2'de `SR2_POSITION=8` yerine **4 Hz** ister
   (= `MAVLINK_KONUM_ASGARI_HZ`, jitter payı sıfır). `mavlink_dogrula`'nın `SET_MESSAGE_INTERVAL`
   isteği (8 Hz) bunu o oturum için düzeltir. Kalıcı çözüm `jetson_baslat.sh`/birim dosyasında
   `--streamrate 8` (mimar kararı; bu görevin dosyası değil). **→ D-406 B:**
   `navitas-cogullayici.service` ExecStart'ına `--streamrate 8` eklendi (K2 kolu, test kilidi).
3. **`FS_OPTIONS` varsayılanda** (bit 4: pilot kontrolündeyken GCS kaybında devam). `Auto`'da SiK
   kopar ve Jetson de susarsa RTL — görev iptal. "Auto'da devam" (bit 1) **bilerek açılmadı**:
   YKS'ye canlı aktarım şartname gereği; bağlantı yoksa görevin devamı puan getirmez.
4. **Kalkış irtifası 32 m** (plan §1.7 "30 m" der): 2 m pay, `asgari_irtifa_notu` 30 m altını
   işaretlediği için. Kamera 30–32 m'de 20×20 m alanı tek karede görür (§0.2 FOV notu).
   Kaptan 30'a çekmek isterse test yine geçer (`≥ SARTNAME_ASGARI_IRTIFA_M`), pay biter.
5. **Loiter 60 s** için `karar_sozlesmesi`'nde birebir sabit **yok** (IKA_GO tekrar penceresi
   5 s, paraşüt 8 s, FDA bütçesi 600 s). Test bunu üst sınırla bağlar
   (`≤ SARTNAME_FDA_OPERASYON_SURESI_S / 5`) ve bütçe hesabına katar.
6. `MOT_PWM_TYPE=0` (PWM): DShot, PWM ile uçuş doğrulanmadan **açılmaz** (§0.2).
