# SAHA KOŞUM KÂĞIDI — 10 Eylül 2026 (T219 · ON_KAYIT H6) — ekip mimar olmadan, sırayla koşar

> **Kural:** ÖLÇÜLEMEDİ ≠ GEÇTİ. Her komutun çıktısı `| tee` ile dosyaya; ekrandan okunup söylenen sayı tutanak değildir. Boş kutu = ÖLÇÜLEMEDİ.
> **Sonuç klasörü:** `results/fdr_sprint_20260910/saha_kosum/` (adım numarasıyla `01_…`, `02_…`); `FDR/ACIK_KALEMLER.md` kalem 1–3, 6, 12 buradan kapanır.
> **Yorumlayıcı:** Jetson `source ~/venv312/bin/activate` → `python` (depo `~/navitas`, `GERI_AKTARIM.md` §2); PC `O:\navitas-local-train\venv\Scripts\python.exe` (`python` PC'de sessizce hiçbir şey yapmaz).
> **Tek aktif saha oturumu** (D-429 §6.3): `DEVAM.md`'ye `saha oturumu: <kim>, <saat>`. **Sıra bağlayıcı:** 7–8 geçmeden pervane takılmaz; 6 pervanelidir, `SAHA_OLAY_SONRASI_MUAYENE.md` madde 0–13 bitmeden yapılmaz.

## 1. Tartı — pilli tam araç + her parça (T10 · kalem 1) · kaptan + üretim · 30 dk
- **Alet:** dijital tartı (≥ 5 kg, 1 g), telefon (her tartım fotoğraflı). Önce pervanesiz araç + pil = **kalkış kütlesi**; sonra parçalar: pil · Jetson · Pixhawk 6C · PM06 · M9N + direk · IMX477 + lens · SiK + anten · FS-iA6B · 4× motor · 4× ESC · 4× pervane · 4× kol · plakalar · kubbe · 4× ayak · kablolar.
- **Tutanak:** `01_tarti.md` tablo `parça | adet | g | fotoğraf` + pil merkezinin gövde merkezine ön/arka uzaklığı cm (CG, D-434 b).
- **Eşik (FDR Bölüm 3 itki bütçesi):** pilli kütle **≤ 4260 g** (hover ≤ %50); 3,0 kg üstüyse kaptan pervane/pil kararına döner (D-435 ek 2). Tahmin yazılmaz.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 2. Jetson ↔ Pixhawk TELEM2 — `mavlink_dogrula` 3/3 (kalem 3) · aviyonik + Jetson · 10 dk
- **Kablo:** Pixhawk `TELEM2` → Jetson 40-pin: TX → **pin 10** (RX), RX → **pin 8** (TX), GND → **pin 6**; **5 V bağlanmaz**. Pixhawk USB'den besli (pil yok). Mission Planner bağlı **olmasın** (SR* akışını ezer, `config/pixhawk/README.md` §4). `ls -l /dev/ttyTHS1` görülsün (dialout üyeliği).
- **Komut (Jetson):** `python -B scripts/mavlink_dogrula.py --mavlink /dev/ttyTHS1 --baud 57600 --sysid 1 --json results/fdr_sprint_20260910/saha_kosum/02_mavlink_telem2.json | tee results/fdr_sprint_20260910/saha_kosum/02_mavlink_telem2.txt`
- **Beklenen:** `HEARTBEAT: sysid=1 … autopilot=3 (MAV_AUTOPILOT_ARDUPILOTMEGA)` · `GLOBAL_POSITION_INT … GECTI` · `EXTENDED_SYS_STATE … GECTI` · `VERDIKT: GECTI` (çıkış 0). **Eşik:** sysid 1 · konum ≥ 4 Hz · iniş durumu ≥ 1 Hz. `DUSTU` ise `NEDEN:` satırı tutanağa; sırayla `BRD_SER2_RTSCTS=0`, `SERIAL2_PROTOCOL=2`, `SERIAL2_BAUD=57`, TX/RX çapraz, `sudo systemctl stop nvgetty` (varsa). Yedek: micro-USB → `--mavlink /dev/ttyACM0`.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 3. IMX477 CSI — köprü + `kamera_dogrula` + ölçülen yatay FOV (kalem 2) · Jetson · 20 dk
- **Kablo:** CSI şerit (mavi taraf dışa, kilit kapalı). Bir kez: `sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → yeniden başlat → `gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! fakesink` hatasız (`jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §6).
- **Komut A (sistem Python, ayrı terminal, açık kalır):** `/usr/bin/python3 scripts/kamera_koprusu.py --port 8080 --fps 5` → `http://127.0.0.1:8080/durum` içinde `"kaynak_acik": true`.
- **Komut B:** `python -B codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --kaydet results/fdr_sprint_20260910/saha_kosum/03_kare.jpg | tee results/fdr_sprint_20260910/saha_kosum/03_kamera.txt` → `okunan kare : 60  (dusen: 0)` · `OLCULEN FPS : 4.9x` · `cozunurluk : 1280x720`. **Eşik:** FPS ≥ 4 (tavan 5), düşen ≤ %5; ayna testi: el sallanırken alınan ikinci karede el görünür (D-349).
- **FOV:** kamera duvara dik, lens–duvar **d = 2,00 m**; duvarda **s = 1,00 m** aralıklı iki bant (kare ortasındaki yarıda); karede iki bandın x-piksel farkı **p**; `python -B scripts/kamera_fov_hesapla.py --genislik-px 1280 --isaret-px <p> --isaret-m 1.00 --mesafe-m 2.00 | tee results/fdr_sprint_20260910/saha_kosum/03_fov.txt` → `ODAK=… px  FOV_yatay=… derece`. **Eşik:** 50–65° (lens hesabı 55–63°; dışındaysa d/s/p yeniden ölçülür). Bu FOV, adım 4'te `FOV=` beyanıdır.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 4. `jetson_baslat.sh --kapi` — üç uçta aynı anda (kalem 3 · CONTRACTS 7.4) · Jetson · 10 dk
- **Ön koşul:** adım 2–3 geçti; adım 3'ün köprüsü **kapatıldı** (Ctrl+C; 8080 çakışır). Değişkenler (IP'ler saha ağından, FOV adım 3'ten):
  `export PATH=$HOME/.local/bin:$PATH KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<derece> KAMERA=http://127.0.0.1:8080/video PIXHAWK_SERI=/dev/ttyTHS1 PIXHAWK_BAUD=57600 NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python`
- **Kuru:** `bash jetson_paket/jetson_baslat.sh --kuru | tee results/fdr_sprint_20260910/saha_kosum/04_kuru.txt` → son satır `KURU SONUC: tamam` (çıkış 0; `[YOK]`/`[EKSIK]` yok). Değilse `--kapi` koşulmaz.
- **Kapı:** `sudo -E bash jetson_paket/jetson_baslat.sh --kapi | tee results/fdr_sprint_20260910/saha_kosum/04_kapi.txt` → `[GECTI] udp:127.0.0.1:14550` · `…14551` · `…14552`, `[active] navitas-*.service  yeniden-baslatma=0`, `thazirlik (bu betik, kapi dahil): NN s`; uç logları `results/jetson_log/kapi/1455N.log` → `04_kapi/`. **Eşik:** 3/3 ∧ thazırlık ≤ 900 s; 2/3 ise tüketiciler kalkmaz. Her Pixhawk yeniden başlatmasında (pil değişimi) `--kapi` tekrar; 2 dk sonra `--durum` → yeniden-başlatma 0.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 5. İki SiK 433 MHz — RTT/kayıp (+ T216 veri hızı) ve MP SiK ekranı (kalem 6 · Y-4-M05) · YKS + aviyonik · 30 dk
- **Cihaz:** iki telsiz geçici olarak USB'yle iki bilgisayara (Pixhawk `TELEM1`'den ayrılır, sonra geri): Jetson `/dev/ttyUSB0`, YKS PC `COMx`. Antenler dik; üç mesafe **10 / 100 / 300 m** görüş hattı (DDR ">%98, 300 m" iddiasının kanıtı yok).
- **Yankı (Jetson, açık kalır):** `python -B scripts/sik_rf_olc.py --rol yanki --port /dev/ttyUSB0 --baud 57600` · **Ölç (PC):** `O:\navitas-local-train\venv\Scripts\python.exe -B scripts/sik_rf_olc.py --rol olc --port COMx --baud 57600 --n 50 --aralik 0.25 --cikti results/fdr_sprint_20260910/saha_kosum/05_sik_rtt_<mesafe>m.json` (mesafe başına bir dosya; T216 sayacı girince **aynı komut** bayt/s ve paket/s de basar).
- **Beklenen:** `gonderilen : 50` · `ACK alinan : 50` · `kayip : 0 (%0.0)` · `RTT p95 : xx ms` · `VERDIKT : tekrar tasarimiyla UYUMLU` (çıkış 0). **Eşik:** p95 < 200 ms (paraşüt tekrar aralığı); kayıp yalnız raporlanır (ilk ölçüm); çıkış 2 = ÖLÇÜLEMEDİ.
- **MP SiK ekranı (PC, MP bağlı değilken):** `Setup → Optional Hardware → SiK Radio → Load Settings`; **Local/Remote**: Version, Format, Baud, Air Speed, Net ID, Tx Power, ECC, Mavlink, Op Resend, Min/Max Freq, Num Channels, Duty Cycle, LBT RSSI, RSSI — iki sütun aynı; ekran görüntüsü `05_sik_mp_ekrani.png`, değerler `05_sik_ayar.txt`.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 6. PM06 pervaneli tezgâh akım kaydı (kalem 12 · Y-3.3.2-M02) · aviyonik + pilot + ikinci kişi · 30 dk
- ⚠ **Ölçülen (10 Eylül, `scripts/tlog_akim_ozet.py`, 6 Eylül tlog'u):** motorlar pervaneli **1949 PWM**'deyken PM06 akımı en fazla **0,44 A**, gerilim **9,35 V**'a çöktü → akım kanalı ölçmüyordu (`results/fdr_sprint_20260910/saha_kosum/tlog_akim_ozet_20260906.txt`). Önce: PM06 → `POWER1` oturmuş, ESC güç hattı PM06 şantından geçiyor, `BATT_MONITOR=4`, `BATT_AMP_PERVLT=36.36`; Motor Test %10'da MP HUD `Current` artıyor mu (sayı tutanağa).
- **Düzen (MUAYENE madde 13):** araç kayışla tezgâha sabit, pervaneli, ikinci kişi + **pens ampermetre (DC)** pil hattında, söndürücü; adım 7–8 geçmiş. Gaz 0 → hover **≥ 2 s rampa** (D-429 §6.1), tam gaz **≤ 30 s** (motor 38 A/30 s). MP bağlıyken tlog **kendiliğinden** yazılır (`<MP>\logs\QUADROTOR\1\*.tlog`); `LOG_DISARMED=0` → `.bin` yalnız **ARM'lı** koşumda (Motor Test → yalnız tlog).
- **.bin indirme:** MP `Flight Data → DataFlash Logs → Download DataFlash Log Via Mavlink` → olay saatinin satırı; alternatif (pil yokken) Pixhawk microSD → `APM/LOGS/*.BIN`. Dosyalar `06_` önekiyle klasöre.
- **Komut (PC):** `O:\navitas-local-train\venv\Scripts\python.exe -B scripts/tlog_akim_ozet.py "<tlog ya da bin>" --pencere 10 --json results/fdr_sprint_20260910/saha_kosum/06_akim.json | tee results/fdr_sprint_20260910/saha_kosum/06_akim.txt` → pencere başına `I_p50 / I_maks / V_min / PWM_maks`, `TOPLAM: akim tepe … A`, **UYARI yok**. **Eşik:** hover penceresinde pens ↔ telemetri ±%10; motor başına hover akımı (toplam/4) ≤ 38 A ∧ hover itki ≤ %50 (kütle adım 1); `UYARI:` varsa akım ÖLÇÜM SAYILMAZ → ÖLÇÜLEMEDİ.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 7. ESC kalibrasyonu (README §2.1 sırası) + motor yönü videosu + pervane eli (D-429 §6.2) · pilot + aviyonik + kayıtçı · 30 dk
- **ESC kalibrasyonu — sıra bağlayıcı (`config/pixhawk/README.md` §2.1):** (1) pervane yok, `POWER1` fişi çıkık, pil yok; (2) Pixhawk yalnız USB → MP `Setup → Optional Hardware → ESC Calibration`; `Messages`'ta her 5 s `Initialising ArduPilot`; (3) emniyet düğmesi; (4) **sonra** pil → yüksek gaz tonu → 2 bip → gaz alta → uzun bip; (5) pil çıkar, `POWER1` tak. Tutanak `07_esc_kal.txt`: saat, kim, bip sırası (4/4 aynı).
- **Motor yönü videosu (videosuz "doğru" sayılmaz):** her motora bant ucu; MP `Setup → Optional Hardware → Motor Test` %10, 3 s, tek tek **A → B → C → D**; yavaş çekim `07_motor_yonu.mp4` (bağlantı insan). Beklenen (quad-X): **A = M1 sağ ön CCW · B = M4 sağ arka CW · C = M2 sol arka CCW · D = M3 sol ön CW**; AUX eşlemesi `SERVO9=36 (M4)`, `SERVO10=34 (M2)`, `SERVO11=33 (M1)`, `SERVO12=35 (M3)`; `SERVO1–8`, `SERVO13–16` = 0 (README §3).
- **Pervane eli:** CW motora CW pervane, yazı yukarı, kalın ön kenar dönüş yönünde; yere değmiş pervane ıskarta (MUAYENE madde 4). Tutanak `07_pervane.txt`: konum | motor | dönüş | yazı. **Eşik:** 4/4 konum-yön, 4/4 pervane eli; yanlış varsa düzelt, video **tekrar**. Pervane adım 8 geçmeden takılmaz.
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 8. Kumanda — `RC6_OPTION` kararı + RC failsafe ayarı ve ölçümü (D-433 · D-428 §2 · Y-4-M12) · pilot + kaptan · 20 dk
- **Ön koşul:** kumandaya **4 yeni AA** (6 Eylül'de TX pili bitti); pervane yok; `RC IN` fişi oturmuş; MP `Radio Calibration` barları 1000–2000; `Messages`: `RCInput: decoding IBUS`.
- **Karar (kaptan, tutanağa):** FS-i6'da tek boş anahtar kanalı **CH6** (D-433): `RC6_OPTION` = **153** (Arm/Disarm) **ya da** **31** (Motor Emergency Stop). MP `Config → Full Parameter List` → `Write Params` → pervanesiz dene: 153 ise anahtar yukarı → HUD `ARMED` (gaz dipte, emniyet basılı, PreArm boş). Dümenle arm: gaz **≤ 1030** + yaw **≥ 1947**, **2 s**. Sonuç `08_kumanda.txt`.
- **Failsafe ayarı (kumandada):** FS-i6 `RX Setup → Failsafe` → **CH5 = SwC üst konum (LAND; `FLTMODE6=9`)**, **CH3 = gaz altta**. Karttaki `FS_THR_ENABLE=3 (Land)` ve `FS_GCS_ENABLE` 30 m görev öncesi **mimar kararıdır** (D-428 §5b/c) — burada değiştirilmez.
- **Ölçüm:** MP `Setup → Mandatory Hardware → FailSafe` sayfası açık, araç USB'de, kumanda **kapatılır** → ≤ 2 s içinde CH5 barı Land'e zıplar, HUD `Land`, `Messages`: `Radio Failsafe`. 6 Eylül'de **DÜŞTÜ** (barlar sabit kaldı, D-428 §2): aynıysa alıcı son değeri tutuyordur, failsafe yeniden kurulur; geçmeden pervane **takılmaz**. Kanıt: ekran videosu `08_failsafe.mp4`, `Messages` satırı `08_kumanda.txt`; sonra üçüncü parametre dökümü `config/pixhawk/arducopter_fda_<YYYYMMDD>.param` (README §1 adım 6).
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

---
Bitince klasör ve `DEVAM.md` satırı commit edilir; sonuç bu kâğıda değil `results/fdr_sprint_20260910/saha_kosum/`'a yazılır. Kapı: `tests/test_saha_kosum_kagidi.py`.
