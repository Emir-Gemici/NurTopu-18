# `config/pixhawk/` — ArduCopter parametre + görev şablonu (FDA görev test uçuşu)

> **NEDEN** (`SAHA_HAZIRLIK_PLANI_20260903.md` §1.6, §1.7, §2.4): Pixhawk 6C 5 Eylül'de
> **ilk kez** yapılandırılacak. Mission Planner'da elle tıklanan değerin tutanağı da testi de
> yoktur; bu klasördeki dosyalar repoda durur, `tests/test_faz_b_pixhawk_sablon.py` ile
> kilitlidir ve sahada **tek komutla** yüklenir. Sahada alınan gerçek parametre dökümü
> tarihli adla **ayrıca** commit edilir (§2.4 son satır) — ilk döküm `arducopter_fda_20260906.param`
> (6 Eylül 20:22; 5 Eylül dökümü hiç alınmadı, D-428 §5g).

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
   **`RC_SPEED` 400** dosyayla gelir (7 Eylül, D-429 §4): kart 6 Eylül dökümünde **490**'daydı
   (`arducopter_fda_20260906.param` satır 659 — Copter-4.5 varsayılanı); ESC Hobbywing
   Skywalker 60A V2 gaz sinyali **50–432 Hz**, 490 spec dışı. Yükleme sonrası 400 görülsün.
   Aynı dosya **`SERVO1–8` / `SERVO13–16` = 0** yazar (dökümde boş çıkışlara motor fonksiyonu
   atanmıştı, D-428 §5d) ve ESC'lerin **AUX 1–4** eşlemesini (`SERVO9–12`, §3) korur →
   yüklemeden sonra **motor testi (pervanesiz) tekrar**, video (D-429 §6 madde 2).
3. **`Write Params`**. Ekranda çıkan "reboot required" uyarısı beklenir: `SERIAL*`, `SR*`,
   `BRD_*` yeniden başlatmada etkin olur → Pixhawk'a **güç kes-ver**.
4. Yeniden bağlan → **`Refresh Params`** → **`Compare Params`** ile dosyayla karşılaştır:
   fark listesi **boş** olmalı (fark varsa yazılmamış demektir; tekrar yükle).
5. TEYİT listesini (§3) tek tek işaretle.
6. `Config` → `Full Parameter List` → **`Save to file`** → `arducopter_fda_<YYYYMMDD>.param` → repoya (6 Eylül: `arducopter_fda_20260906.param`, D-428 §5g; ikinci pusula kalibrasyonu ve `FS_GCS_ENABLE` sonrası **üçüncü döküm** şart).

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
| **Tutanak dökümü** | `arducopter_fda_20260906.param` (6 Eylül 20:22, D-428 §5g); sonraki dökümler tarihli | §2.4 son satır; şablon dosyasına dokunulmaz |

Başka hiçbir değer sahada "gözle" değiştirilmez; zorunlu değişiklik = D-kaydı + bu README + test.

### 2.1 ESC kalibrasyonu — 6 Eylül'de ölçülen yordam (ESC: Hobbywing Skywalker 60A V2 — etiket beyanı; AUX 1–4 = `SERVO9–12`)

"Hepsi birden" kalibrasyonu 6 Eylül'de iki kez tutmadı; üçüncü deneme tuttu. `REVIEW_LOG.md` D-428 §3'ten alıntı:

> Deneme 1 (pil ile): Pixhawk LED döndü, düğme basıldı, ESC'ler **hızlı üçlü** bip = Hobbywing "gaz sıfırda değil" — ESC sinyali **normal modda** gördü, kalibrasyona girmedi. Deneme 2 (USB önce, sonra pil): "olmadı" — sebep muhtemelen pil takılınca PM06→POWER1 ile kartın **yeniden başlaması** (kanıt yok, çıkarım). Deneme 3 **başarılı**: POWER1 fişi çıkarıldı, Pixhawk USB'de ESC-kal passthrough'a alındı (MP `Messages` her 5 sn `Initialising ArduPilot` = `esc_calibration` bekleme döngüsü; `Restart board` satırı MP bağlanmadan önce gittiği için görülmedi), düğme basıldı, **sonra** pil → ESC'ler yüksek gazla açıldı → 2 bip → gaz alta → uzun bip. **Skywalker V2 kalibrasyon kararını kendi açılış anında verir**; pil-öncesi sinyal şart.

Yordam (sıra bağlayıcıdır): **(1)** pervane yok, `POWER1` fişi çıkarılmış, pil takılı değil; **(2)** Pixhawk yalnız USB ile MP'ye bağlı → ESC kalibrasyon passthrough'u başlat, `Messages`'ta `Initialising ArduPilot` döngüsü görülsün; **(3)** düğmeye bas; **(4)** **sonra** pil → yüksek gaz tonu → 2 bip → gaz alta → uzun bip = tamam; **(5)** pil çıkar, `POWER1` tak. Sonuç "5'te 5" ve dört motorun birlikte dönmesi 6 Eylül'de **beyandır** (video yok, D-428 §1).

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
- `SERVO9_FUNCTION` — **36 (Motor4, sağ arka) = AUX1.** ESC'ler AUX 1–4'te (D-428 §5d; 6 Eylül dökümü ile ÖLÇÜLDÜ). Motor testi bu eşlemeyle geçti; eşlemeyi değiştirmek = motor testini baştan almak. Dördü yüklendikten sonra motor testi (pervanesiz) **tekrar**, A-B-C-D sırası **videoyla** (D-429 §6 madde 2).
- `SERVO10_FUNCTION` — **34 (Motor2, sol arka) = AUX2.**
- `SERVO11_FUNCTION` — **33 (Motor1, sağ ön) = AUX3.** M1 6 Eylül devrilmesinde hasarlı (D-429 §2 madde 4); motor/ESC değişse de eşleme aynı kalır, yeni kablo aynı porta.
- `SERVO12_FUNCTION` — **35 (Motor3, sol ön) = AUX4.** Ayrıca `SERVO1–8` ve `SERVO13–16` = **0** görülsün (§1 adım 2; test `P10`).

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

---

## 6. ArduPlane final — sabit kanat + mancınık + paraşüt (T221 · K11)

> **NEDEN:** Yarışma final aracı (şartname: sabit kanat, yalnız mancınıkla fırlatma, paraşütle
> zorunlu iniş — `OGREN_ADIYAMAN/ozet/H_sartname.md:25,47,59`) için parametre seti yoktu; Jetson
> geliştiricisi istedi (`JETSON_OTURUM_DURUMU_20260909.md` §5 madde 4; D-431 §4(10): *"ArduPlane ile
> ölçülmedi"*). §1–§5 FDA quad'ınındır (`arducopter_fda.param`); bu bölüm yalnız aşağıdaki dosyalar
> içindir. Bölüm §4 yerine **§6** numarasını aldı: `SAHA_KOSUM_KAGIDI_20260910.md:10` mevcut §4'e
> ("Sahada ayrıca kontrol") atıf yapıyor, yeniden numaralama o atfı kırardı.

| dosya | ne | durum |
|---|---|---|
| `arduplane_final.param` | ArduPlane **4.5.7**, 62 parametre; her satırın üstünde NEDEN + tanımlandığı kaynak dosya; 14 `# TEYIT:`, 18 `# BEYAN:` | kaynakta 62/62 bulundu, 0 geçersiz · `BRD_SER2_RTSCTS` **kart koşullu** (yalnız ChibiOS hwdef'le derlenir; 4.5.7 SITL ikilisinde yok — §6.6 ölçüt 1) |
| `arduplane_sitl_prova.waypoints` | **yalnız SITL provası** (ArduPilot SITL varsayılan konumu CMAC) — saha görevi DEĞİL | kuru prova ÖLÇÜLEMEDİ (§6.6) |
| `results/fdr_sprint_20260910/H8/T221/plane457_param_kaynak.json` | `scripts/ardupilot_param_kaynak.py` çıktısı: her ad Plane-4.5.7 kaynağında dosya + satır numarasıyla, değer `@Values`/`@Bitmask`/`@Range` denetimiyle | çıkış 0 |
| `results/fdr_sprint_20260910/H8/T221/sitl_yoklama.txt` | `sitl_yokla.py` çıktısı: bu makinede SITL koşulabilir mi; §6.1 ek tarama (T221-D, `--ek`): SITL ikilisinde `SER2_RTSCTS` 0 · `SAFETY_DEFLT` 1, `features.txt` satır numaraları, kaynak satırları | `HUKUM: OLCULEMEDI` |

Kilit: `tests/test_faz_b_arduplane_sablon.py` (A1–A19 + 14 mutasyon; A18 SITL kabul ölçütü 1'in sayısını `.param`'dan hesaplar). Kanıt yenileme (ağ gerekir):

```bash
python -B scripts/ardupilot_param_kaynak.py --param config/pixhawk/arduplane_final.param --etiket Plane-4.5.7 --cikti results/fdr_sprint_20260910/H8/T221/plane457_param_kaynak.json
```

`.param`'da bir değer değişip bu komut koşulmazsa test A14 düşer (kanıt bayat, mutasyon M7).

### 6.1 Sürüm SABİT: ArduPlane 4.5.7 (D-425 dersi)

- Etiket `Plane-4.5.7`, commit `0358a9c210bc6c965006f5d6029239b7033616df` — GitHub etiket API'si ve
  firmware sunucusundaki `Pixhawk6C/git-version.txt` aynı commit'i verir (10 Eylül okundu).
- Firmware: `https://firmware.ardupilot.org/Plane/stable-4.5.7/Pixhawk6C/arduplane.apj`
  (`features.txt`: `HAL_PARACHUTE_ENABLED` var). Mission Planner'ın "en son kararlı" önerisi bugün
  **Plane 4.7.1**'dir (`Plane/stable/Pixhawk6C/git-version.txt`, 10 Eylül): 5 Eylül'de Copter'da
  yaşanan *"Missing 9 params"* (D-425) aynen tekrarlanır. İkona tıklanmaz: **`Load custom firmware`**
  → `arduplane.apj`.
- `.apj` içindeki `board_id` **56** olmalı (Pixhawk 6C; `scripts/pixhawk_firmware_indir.py`'deki
  kapı). ⚠ O betik bugün **yalnız Copter** indirir (`SURUM`/`TABAN` Copter'a sabit); Plane dosyası
  elle indirilip saha belleğine kopyalanır (§6.7 madde 7).
- Açılışta `ArduPlane V4.5.7` görülmeli. Copter → Plane flash'ı **tüm parametreleri sıfırlar**;
  `arducopter_fda.param`'dan hiçbir şey taşınmaz, bu dosya tek başına yüklenir.

### 6.2 Yükleme sırası (Mission Planner)

0. Firmware (§6.1) → açılış satırı `ArduPlane V4.5.7`.
1. `Config` → `Full Parameter List` → **`Load from file`** → `arduplane_final.param` → **`Write Params`**.
2. Pixhawk'a güç kes-ver: `SERIAL*`, `SR*`, `BRD_*`, `SERVOn_FUNCTION`, `Q_ENABLE` yeniden başlatma ister.
3. `Refresh Params` → `Compare Params`: fark listesi **boş** olmalı.
4. Kalibrasyonlar (dosya bunları ezmez): ivmeölçer, pusula, radyo, hava hızı sensörü (model BEYAN, §6.4).
5. Kontrol yüzeyleri `FBWA`'da tek tek: yön + `SERVOn_REVERSED`/`MIN`/`MAX`/`TRIM` uçakta ayarlanır
   (dosyada yok) — **videoyla**.
6. §6.3 TEYİT listesini tek tek işaretle.
7. Kalkış yer testi (**pervanesiz**, `AUTO` + görev yüklü + arm): elle hafif itmek `Triggered AUTO`
   üretmemeli (eşik `TKOFF_THR_MINACC` 15 m/s²).
8. `Save to file` → `arduplane_final_<YYYYMMDD>.param` repoya; şablona dokunulmaz.

### 6.3 TEYİT listesi (ArduPlane) — `.param` `# TEYIT:` ile metin kilidi (test A16)

- `BRD_SER2_RTSCTS` — 0 görülsün; TELEM2'den HEARTBEAT gelmiyorsa ilk bakılacak yer.
- `RC_PROTOCOLS` — `Messages`'ta `RCInput: decoding <protokol>`; Radio Calibration'da 4 ana kanal oynasın.
- `SERVO1_FUNCTION` — 4 (sol kanatçık, MAIN1); `FBWA`'da sağa yatışta sol kanatçık AŞAĞI.
- `SERVO2_FUNCTION` — 19 (elevator, MAIN2); burun aşağı eğilince elevator YUKARI.
- `SERVO3_FUNCTION` — 70 (sol ESC, MAIN3); motor testi pervanesiz, iki motor birlikte, video.
- `SERVO4_FUNCTION` — 21 (rudder, MAIN4); sağ pedal → rudder SAĞA.
- `SERVO5_FUNCTION` — 4 (sağ kanatçık, MAIN5); yönü SERVO1'in tersi.
- `SERVO6_FUNCTION` — 70 (sağ ESC, MAIN6).
- `SERVO7_FUNCTION` — 27 (paraşüt, MAIN7); yerde servo `CHUTE_SERVO_OFF`'ta, kapak kilitli.
- `TKOFF_THR_MINACC` — 15 m/s/s; elle hafif itmek tetiklememeli (§6.2 adım 7).
- `CHUTE_ENABLED` — 1; arm öncesi `Chute has no channel` **olmamalı**.
- `FS_LONG_ACTN` — MP açıklamasında 0 = Continue (Plane tablosu).
- `BATT_FS_LOW_ACT` — 1 = RTL (Plane tablosu; **Copter'da 1 = Land**).
- `BATT_FS_CRT_ACT` — 5 = Parachute.

### 6.4 BEYAN gereken (insan) — `.param` `# BEYAN:` ile metin kilidi (test A16)

Araç **üretilmedi** (FDR BOLUM_3 §3.2.1.2); aşağıdaki değerler DDR tasarımından ya da firmware
varsayılanından gelir ve beyan/ölçüm olmadan **tahmindir**:

- `RC_PROTOCOLS` — final alıcı: DDR BOM TBS Crossfire Nano RX (CRSF, bit 9) · eldeki FlySky FS-iA6B (iBUS, bit 2) · SIYI MK15 "3 in 1" (D-442; uçuş kartına çıkış protokolü bildirilmedi). Beyan gelince tek bite daraltılır.
- `SERVO1_FUNCTION` — sol kanatçık servosunun MAIN1'e takıldığı.
- `SERVO2_FUNCTION` — elevator servosunun MAIN2'ye takıldığı.
- `SERVO3_FUNCTION` — sol ESC sinyal kablosunun MAIN3'e takıldığı.
- `SERVO4_FUNCTION` — rudder servosunun MAIN4'e takıldığı.
- `SERVO5_FUNCTION` — sağ kanatçık servosunun MAIN5'e takıldığı.
- `SERVO6_FUNCTION` — sağ ESC sinyal kablosunun MAIN6'ya takıldığı.
- `SERVO7_FUNCTION` — paraşüt tetik servosunun MAIN7'ye takıldığı.
- `TKOFF_THR_MINACC` — gerçek mancınığın ivme profili (DDR ortalaması 46,3 m/s²; ilk atışın `.bin` IMU kaydı).
- `TKOFF_THR_DELAY` — gerçek ray süresi ve çıkış hızı (DDR 0,39 s / 18 m/s); değişirse §6.5 hesabı yeniden.
- `AIRSPEED_MIN` — DDR stall 15,86 m/s × 1,2 (XFLR5 / CLmax hesabı, uçulmadı).
- `AIRSPEED_CRUISE` — DDR seyir 25 m/s; tarama hızı kamera kare aralığıyla birlikte kararlaştırılır.
- `AIRSPEED_MAX` — DDR VH 35 m/s altı, VA 27,47 m/s üstü (§6.7 madde 2).
- `CHUTE_TYPE` — paraşüt mekanizması servo tetikli mi (DDR: model ve tedarik boş).
- `CHUTE_SERVO_ON` — mekanizmanın açtığı PWM (yerde ölçülür).
- `CHUTE_SERVO_OFF` — mekanizmanın kilitli kaldığı PWM.
- `CHUTE_OPTIONS` — servonun sürekli ON konumunda tutulmaya uygunluğu.
- `BATT_MONITOR` — güç modülü ve ölçekleri: DDR PM02 · kutudan PM06 çıktı (D-426 §3) · 6 Eylül'de akım kanalı ölçmedi (D-440) · DDR tepe akımı 122 A Matek PDB'den geçer.

Dosyada **olmayan** ama beyan isteyenler (parametresi yazılmadı, firmware varsayılanı kalır):

- **Motor modeli:** FDR BOLUM_2 (:403) ve BOLUM_7 (:151) sabit kanat motorunu *SunnySky X2216 ×2*
  yazar, DDR itki seçimi *T-Motor AT3520 KV850 ×2*'dir. Dosyada motora bağlı değer yok; çelişki FDR'de çözülür.
- **Hava hızı sensörü:** DDR "hava hızı sensörü I²C" der, model yok → `ARSPD_TYPE`/`ARSPD_USE` dosyada
  yok (yanlış tip arm öncesi kontrolde düşer; doğru tip beyanla eklenir).
- **Mod anahtarı** (`FLTMODE_CH`, `FLTMODE1..6`): güvenlik pilotunun `MANUAL`/`FBWA`/`AUTO` konumları sahada.
- **Kütle, CG, kontrol yüzeyi uçları:** FDR §3.1.1–3.1.3 beyanları.

### 6.5 Mancınık kalkışı ve paraşüt — Plane-4.5.7 kaynağından okunan davranış

| konu | kaynak | davranış → dosyadaki karşılık |
|---|---|---|
| kalkış tetiği | `ArduPlane/takeoff.cpp` `auto_takeoff_check` | AUTO + arm + GPS 3D fix; ileri ivme ≥ `TKOFF_THR_MINACC` → `TKOFF_THR_DELAY` × 0,1 s → o anki 100 ms pencerede GPS hızı > `TKOFF_THR_MINSPD` ise **gaz açılır**; pencere kaçarsa `Timeout AUTO`, motor açılmaz → `TKOFF_THR_MINSPD 0` |
| kötü atış | aynı | pitch ≤ −30° / ≥ 45° ya da \|roll\| > 30° → `Bad launch AUTO`; ray 15° kapının içinde |
| tırmanış pitch'i | `takeoff.cpp` `takeoff_calc_pitch` | `TKOFF_ROTATE_SPD 0` iken görevin `NAV_TAKEOFF` param1'i, en az 5° |
| paraşüt → gaz | `ArduPlane/servos.cpp` `suppress_throttle` | bırakma başlar başlamaz **oto-gaz kiplerinde** (AUTO/RTL) gaz bastırılır; `MANUAL`/`FBWA`'da bastırılmaz (pilot keser) |
| görev bırakması | `AP_Mission_Commands.cpp` `start_command_parachute` | `AP_Parachute::release()` — **irtifa sorulmaz** |
| YKS/RC bırakması | `ArduPlane/GCS_Mavlink.cpp` `handle_MAV_CMD_DO_PARACHUTE` → `parachute.cpp` `parachute_manual_release` | uçtuktan sonra `CHUTE_ALT_MIN` altında `Parachute: Too low` → `MAV_RESULT_FAILED` (`iha_komut_alici` bunu RED görür); uçmadan önce (yer testi) izinli |
| pil kritik | `events.cpp` `handle_battery_failsafe` | `BATT_FS_CRT_ACT 5` → `parachute_release()` |
| RC/GCS kaybı AUTO'da | `events.cpp`, `system.cpp` `check_long_failsafe` | `FS_SHORT_ACTN 0` kip değişmez, `FS_LONG_ACTN 0` devam → görev İB üstünde `DO_PARACHUTE` ile biter; elle kiplerde CIRCLE → RTL |

**DDR kinematiği (BEYAN, sabit ivme varsayımı):** 3,5 m ray, 18 m/s çıkış → ortalama ivme 46,3 m/s²,
raydaki süre 0,39 s; 15° tırmanışta itkisiz yavaşlama g·sin 15° + D/m (D = 6,0 N × (18/25)²,
m = 8,542 kg) → stall'a (15,86 m/s) 0,74 s. `TKOFF_THR_DELAY 5` (0,5 s): ray süresinden uzun, ray +
stall süresinden (1,13 s) kısa. ArduPilot açıklamasının bungee için önerdiği *"such as 30"* (3 s)
bu uçakta stall demektir (test mutasyonu M6).

### 6.6 SITL provası — ÖLÇÜLEMEDİ (bu makine, 10 Eylül)

**Ölçüm** (`results/fdr_sprint_20260910/H8/T221/sitl_yoklama.txt`, üretici aynı dizindeki
`sitl_yokla.py`; hiçbir şey kurmaz, hiçbir ikili çalıştırmaz): `sim_vehicle.py`, `arduplane`,
`mavproxy.py`, `dronekit-sitl`, docker, podman **YOK**; `wsl.exe` yalnız System32 saplaması, kayıtlı
WSL dağıtımı **YOK**; venv'de yalnız `pymavlink` var. Firmware sunucusunda 4.5.7 SITL ikilisi **yalnız
Linux** için (`SITL_x86_64_linux_gnu`, `SITL_arm_linux_gnueabihf`); Windows yerel ikili yok.
`dronekit-sitl` kurulu değil; kurulsa bile 4.5.7 dışı bir sürümle prova D-425'in sürüm dersine
aykırıdır. **Sonuç: ArduPlane SITL provası KOŞULMADI.** Adların 4.5.7'de var olduğu ve değerlerin
tablolara uyduğu kaynaktan kanıtlıdır (§6 tablo); uçuş mantığının uçtan uca davranışı **ÖLÇÜLEMEDİ**.

⚠ Çelişki (ölçüldü): SITL x86_64 `features.txt` `!HAL_PARACHUTE_ENABLED` der; aynı ikilide `CHUTE_` ve
`AP_Parachute` dizgeleri var (çalıştırılmadan bayt taraması, sha256 `639a8381…`). SITL'de `CHUTE_*`
parametrelerinin gerçekten var olduğu ancak koşumda görülür — provanın ilk kapısı budur.

**Satırlar ve oran (ölçüldü — `sitl_yoklama.txt` §6.1, 10 Eylül, T221-D):**
`SITL_x86_64_linux_gnu/features.txt:139` `!HAL_PARACHUTE_ENABLED` der; ama o dosyanın 167 satırının
**164'ü** `!` ile başlar (`Pixhawk6C/features.txt:196` `HAL_PARACHUTE_ENABLED`; orada 308 satırın 72'si
`!`). Aynı SITL ikilisinde **yalnız paraşütle derlenen** iki mesaj var: `Chute has no channel` 1 kez
(`libraries/AP_Parachute/AP_Parachute.cpp:216`; dosya `:3` `#if HAL_PARACHUTE_ENABLED` … `:273`
`#endif` bloğunda) ve `Parachute: Too low` 1 kez (`ArduPlane/parachute.cpp:55`; `:15`
`#if PARACHUTE == ENABLED` … `:68` `#endif`; `ArduPlane/config.h:219` `#define PARACHUTE
HAL_PARACHUTE_ENABLED`). `CHUTE_` grup öneki `ArduPlane/Parameters.cpp:767`'dedir (`:764`
`#if PARACHUTE == ENABLED`). İki kaynak birbirini yalanlar: dizge sayımı parametre tablosunu
kanıtlamaz, SITL `features.txt`'i ise neredeyse her özelliği `!` yazar. **Hakem koşumdur**; sonuç
ölçütlerin altındaki önceden yazılmış ön hükümle kaydedilir.

**Linux / WSL2 yordamı** (Ubuntu; A yolu x86_64 hazır ikili, B yolu kaynaktan — Jetson aarch64 dahil):

A) Hazır 4.5.7 ikilisi (`<DEPO>` = bu deponun kökü):

```bash
python3 -m venv ~/sitl && . ~/sitl/bin/activate && pip install MAVProxy pymavlink
mkdir -p ~/sitl/p457 && cd ~/sitl/p457
wget https://firmware.ardupilot.org/Plane/stable-4.5.7/SITL_x86_64_linux_gnu/arduplane && chmod +x arduplane
sha256sum arduplane      # beklenen 639a8381c1d8805a2e252a679f22d72473232ac813c810216d99aaba55e160e9 (10 Eyl)
wget https://raw.githubusercontent.com/ArduPilot/ardupilot/Plane-4.5.7/Tools/autotest/models/plane.parm
./arduplane --model plane --home -35.363261,149.165230,584,353 --defaults plane.parm,<DEPO>/config/pixhawk/arduplane_final.param -I0 &
mavproxy.py --master tcp:127.0.0.1:5760 --console
```

B) Kaynaktan (her Linux; Jetson Orin Nano dahil — kurulum betiği JetPack 7.2.1 / Ubuntu 24.04'te ÖLÇÜLMEDİ):

```bash
git clone --branch Plane-4.5.7 --depth 1 --recurse-submodules --shallow-submodules https://github.com/ArduPilot/ardupilot.git
cd ardupilot && Tools/environment_install/install-prereqs-ubuntu.sh -y && . ~/.profile
./waf configure --board sitl && ./waf plane
Tools/autotest/sim_vehicle.py -v ArduPlane -f plane -L CMAC --add-param-file=<DEPO>/config/pixhawk/arduplane_final.param --console --map
```

`sim_vehicle.py -f plane` önce `Tools/autotest/models/plane.parm`'ı, sonra `--add-param-file`
dosyasını yükler (`--defaults a,b`; sonraki kazanır). Her iki yolda MAVProxy'de:

```text
param set SIM_PARA_ENABLE 1
param set SIM_PARA_PIN 7
wp load <DEPO>/config/pixhawk/arduplane_sitl_prova.waypoints
mode AUTO
arm throttle
param set SIM_SHOVE_X 46
param set SIM_SHOVE_TIME 390
```

`SIM_PARA_PIN 7` = paraşüt servosu (MAIN7): `libraries/SITL/SIM_Parachute.cpp` bu çıkış ≥ 1250 PWM
olunca `BANG!  Parachute deployed` basar (`CHUTE_SERVO_ON` 1300, `OFF` 1100). `SIM_SHOVE_X/TIME` gövde
x ivmesini verilen ms boyunca ekler (`SIM_Aircraft.cpp` `add_shove_forces`): 46 m/s² × 0,39 s ≈ 18 m/s
= DDR mancınığı. Önce `SHOVE_X`, sonra `SHOVE_TIME` (süre yazılınca itiş başlar ve sonunda 0'a döner).

**Kabul ölçütleri (önceden yazıldı; biri tutmazsa prova DÜŞER, eşik gevşetilmez):**
1. ~~Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1 ve dosyadaki 62 adın 62'si yüklü.~~
   *(10 Eylül, ölçümden önce, D-449: `BRD_SER2_RTSCTS` 4.5.7 SITL'de derlenmez — bu ölçüt SITL'de hiç
   tutamazdı.)*
   Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1; dosyadaki **62** addan SITL'de **61**'i
   yüklü (N − |beklenen-yok|; her ad `param show <AD>` ile sayılır). Önceden yazılmış **beklenen-yok**
   listesi = {`BRD_SER2_RTSCTS`}. Gerekçe (Plane-4.5.7 kaynağı):
   `libraries/AP_BoardConfig/AP_BoardConfig.cpp:124` `#ifdef HAL_HAVE_RTSCTS_SERIAL2` (tanım `:131`;
   dış blok `:113` `#if AP_FEATURE_RTSCTS`). Bu makroyu ChibiOS hwdef üreteci yazar:
   `libraries/AP_HAL_ChibiOS/hwdef/scripts/chibios_hwdef.py:1899-1903` UART'ın `_RTS` hattı varsa
   `#define HAL_HAVE_RTSCTS_SERIAL<n>` (`:1929-1930` `AP_FEATURE_RTSCTS 1`); Pixhawk 6C'de
   `libraries/AP_HAL_ChibiOS/hwdef/Pixhawk6C/hwdef.dat:57-58` `UART5_RTS`/`UART5_CTS`, `:37`
   `SERIAL_ORDER` → SERIAL2 = UART5. Ölçüm (ikili çalıştırılmadan): 4.5.7 SITL ikilisi
   (sha256 `639a8381c1d8805a2e252a679f22d72473232ac813c810216d99aaba55e160e9`) `SER2_RTSCTS`
   dizgesini **0** kez içerir; aynı tablonun koşulsuz adı `SAFETY_DEFLT` (`:171`) 1 kez
   (`sitl_yoklama.txt` §6.1). SITL bu adı **sessizce** atlar: `libraries/AP_Param/AP_Param.cpp:2313-2316`
   uyarıyı yalnız `#if ENABLE_DEBUG` ile basar, ikilide `Ignored unknown param` 0 kez — eksik ad
   günlükten değil `param show` ile görülür. Bu listenin dışındaki her eksik ad **DÜŞER**; liste
   ölçümden sonra genişletilmez (test A18 README listesini testteki önceden yazılmış kümeyle kilitler).
2. Arm öncesi mesajlarda `Chute has no channel` yok.
3. İtiş öncesi 60 s boyunca `Triggered AUTO` yok; itişten sonra `Armed AUTO, xaccel = …` ve 0,6 s içinde `Triggered AUTO`.
4. Bırakma noktasından (satır 4) sonra `Parachute: Released`, ardından `BANG!  Parachute deployed`.
5. Bırakmadan sonra `.bin` RCOU'da SERVO3 gaz çıkışı minimumda (`servos.cpp` `suppress_throttle`).
6. `.bin` + `mavlogdump.py --types MSG,RCOU,CTUN` çıktısı `results/<tarih>_sitl_plane457/` altına.

**Ön hüküm — SITL'de `CHUTE_*` yoksa (10 Eylül, ölçümden önce, D-449):** koşumda `param show
CHUTE_ENABLED` boş dönerse prova *"SITL paraşütsüz derlenmiş — paraşüt zinciri ÖLÇÜLEMEDİ"* diye
kaydedilir. Ölçüt 1 **DÜŞER** (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez);
ölçüt 2'nin *"mesaj yok"* koşulu paraşütsüz ikilide kendiliğinden sağlanır → ÖLÇÜLEMEDİ; ölçüt 4 ve 5
ÖLÇÜLEMEDİ; ölçüt 3 (kalkış kapısı) yine ölçülür. Yukarıdaki `features.txt` ↔ ikili çelişkisi bu
kaydı değiştirmez.

⚠ SITL `plane` modeli bizim uçağın aerodinamiği değildir (`models/plane.parm` küçük model; bizim
dosya `AIRSPEED_*`'ı ezer, `ROLL_LIMIT_DEG 65` gibi değerleri o dosyadan kalır): prova **mantığı**
sınar (kalkış kapısı, paraşüt zinciri, failsafe), performansı sınamaz. SITL plane modelinin kendi
fırlatıcısı (`SIM_Plane.cpp`: `-catapult`/`-bungee` çerçevelerinde 7. çıkış > 1700 PWM) **kullanılmaz**:
7. çıkış bizde paraşüttür; mancınık `SIM_SHOVE_*` ile benzetilir.

### 6.7 Karar noktaları (mimara)

1. **`BATT_LOW_TIMER` 10 s** (firmware varsayılanı): DDR 2 s dedi. 2 s + paraşüt eylemi, tam gaz
   tırmanıştaki gerilim çökmesinde yanlış bırakma riskidir (FDA aracında tam gazda 9,35 V ölçüldü, D-440).
2. **`AIRSPEED_MAX` 30 m/s:** ArduPilot açıklaması "AIRSPEED_MIN'in en az %50 üstü" (≥ 30) ister; DDR
   manevra hızı VA 27,47 m/s bunun altındadır (VA üstünde tam kumanda sapması +3 g'yi aşabilir;
   otopilot yatış sınırı `ROLL_LIMIT_DEG` varsayılanı 45° → 1/cos 45° = 1,41 g). 30 (TECS) mi, ≤ 27 (yapı) mı?
3. **`CHUTE_CRT_SINK` 0** (kapalı): otomatik kritik alçalma bırakması uçuş verisi ister; normal
   alçalmayla karışan eşik yanlış bırakmadır (İB dışı iniş, −5 puan/m).
4. **`BATT_FS_LOW_ACT` 1 = RTL:** düşük pilde görev bırakılıp eve dönülür (FDR yönergesi "eve dönüş"
   tepkisini ister); görev puanı için alternatif 0 (görev sürer, kritikte paraşüt).
5. **`FS_GCS_ENABL` 1:** Copter'daki D-406 C gerekçesi (Jetson-bağlantı failsafe'i) sabit kanatta AUTO'da
   eylemsizdir (`FS_LONG_ACTN 0` → devam). DDR'nin "açık güzergâh tespit edildiyse arama deseni
   sürdürülür" dallanması parametreyle ifade edilemez (görev ya da companion mantığı).
6. **İniş kanıtı ArduPlane'de ÖLÇÜLMEDİ:** Plane akışlarında da `EXTENDED_SYS_STATE` yok
   (`ArduPlane/GCS_Mavlink.cpp` grep 0); `landed_state()` Plane'de ayrı yazılmış (`:1539`) —
   `iha_inis_yayinci`/`inis_kaniti`'nın paraşütle inişte `ON_GROUND`'u ne zaman göreceği bilinmiyor.
7. **`scripts/pixhawk_firmware_indir.py` yalnız Copter indirir:** Plane 4.5.7 `.apj`'nin saha belleğine
   çevrimdışı konması için aynı `board_id` 56 kapısıyla bir `--arac plane` seçeneği önerilir.
