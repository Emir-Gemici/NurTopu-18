# ATÖLYE TEST GÜNÜ — 12 Eylül 2026 (T232 · D-444) — ekip mimar olmadan, sırayla uygular

> **Kural (D-444):** tahmin SONUÇ değildir. Her testte **BEKLENTİ** = sayı/aralık + dayanak (HESAP / ÜRETİCİ VERİSİ / BENZER ÖLÇÜM) + kaynak, "ölçüm değil" etiketli; **Kabul** önceden yazılı; **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** — kutu doldurulana dek. ÖLÇÜLEMEDİ, kabul demek değildir; boş kutu = ÖLÇÜLEMEDİ. Ekrandan okunup söylenen sayı tutanak değildir: çıktı dosyaya, ekran fotoğrafa/videoya.
> **Numaralar** A1–A13 FDR Bölüm 4 test programıyla (T231) aynıdır. Depoda sayısal eşiği olmayan testte kabul **bu kâğıtta ön kayıttır**; Bölüm 4 farklı yazarsa mimar birleştirmede tek değere indirir, eşik gevşetilmez. **Sonuç klasörü** `results/atolye_20260912/` (dosya adı `A<n>_…`), tablo `results/atolye_20260912/SONUC_SABLONU.md`.
> **PC (YKS dizüstü, Windows PowerShell, depo kökünde):** `$PY = "O:\navitas-local-train\venv\Scripts\python.exe"; $env:PYTHONIOENCODING = "utf-8"` — çıplak `python` sessizce hiçbir şey yapmaz; konsol cp1254 olduğundan `⚠`/`İ` basan betik boruda çöker. Dosyaya yazım `| Tee-Object -FilePath <dosya>`.
> **Jetson:** `cd ~/navitas && source ~/venv312/bin/activate && mkdir -p results/atolye_20260912` → `python` (6 Eylül'de depo `~/proje/NAVITAS_JETSON_20260906/navitas` idi — hangisi varsa oradan); kamera köprüsü sistem Python'uyla (`/usr/bin/python3`). Canlı izlenen çıktıda `-u` (tamponsuz).
> **Parametre atıfları** `config/pixhawk/arducopter_fda_20260906.param` satırlarıdır ("döküm :N"); kart bugün farklı okunursa kart değeri tutanağa yazılır, kabul değişmez.
> **Tek aktif saha oturumu** (D-429 §6.3): `DEVAM.md`'ye `saha oturumu: <kim>, <saat>`.

## 0. Getirilecekler (sabah kontrol; eksik kalem = ilgili test ÖLÇÜLEMEDİ)
- [ ] DC **pens ampermetre** (sıfırlanabilir) · multimetre · **ölçü şeridi** (≥ 3 m) · **iki işaret** (bant, 1,00 m aralık) · **telefon (60 fps video)**
- [ ] **İki SiK 433 telsizi** + iki USB kablo + antenler · **Pixhawk USB** kablosu · **dolu pil** (+ yedek) · kumandaya **4 yeni AA**
- [ ] **Jetson** Orin Nano + güç + **CSI kamera** (IMX477, 6 mm lens) + **15→22 pin CSI şerit** · klavye/fare
- [ ] **MK15 kumanda** + **Air Unit Mini** + **SIYI HDMI giriş dönüştürücü** + **DP→HDMI adaptör** + **mini HDMI kablo** + **12 V besleme** (İHA 12,2 V dönüştürücüsü — akımı BEYAN GEREKLİ — ya da tezgâh) · **USB HDMI yakalama kartı** + kumanda HDMI kablosu
- [ ] **Laptop YKS** (Mission Planner + depo + venv; `& $PY -B scripts/sik_rf_olc.py --help` açılıyor) · söndürücü · ip/kayış (A12)

## 1. Güvenlik (bağlayıcı)
- **A1–A4 ve A13 PERVANESİZ:** pervaneler sökülür, ayrı kutuya konur; pil takılıyken pervane takılmaz; motor dönerken herkes kolların dışında.
- **Hover (A12) yalnız ayrı adımda**, günün sonunda, **bağlı (ip/kayış) ya da açık alanda**; ön koşullar A12'de. Sağlanmazsa pervane takılmaz.
- Kâğıtta yazan dışında **parametre değiştirilmez** (yalnız A3 geçici eşik + geri alma, A4 `RC6_OPTION` kararı). 6 Eylül'de bilinçsiz iki değişiklik olmuştu (D-428 §5b).
- Arm için emniyet düğmesi basılı, PreArm boş. PreArm hatası (ör. `Check mag field`) arm'ı engellerse araç metalden ≥ 5 m uzağa alınır; `ARMING_CHECK` **değiştirilmez** — olmazsa o adım ÖLÇÜLEMEDİ (neden: PreArm satırı).
- Olay olursa güç vermeden önce log (.bin/tlog) alınır (D-429 §6.4); şişkin ya da sıcak pil kullanılmaz.

## 2. Sıra ve zaman bütçesi (09:00–14:00; gecikme sonraki testi kaydırır, test atlanmaz — atlanan ÖLÇÜLEMEDİ)
| saat | iş | kim |
|---|---|---|
| 09:00–09:15 | Hazırlık: güvenlik brifingi, `DEVAM.md` satırı, MP (USB) → `Config → Full Parameter List → Save to file` → `results/atolye_20260912/00_param_once.param` | kaptan + aviyonik |
| 09:15–09:30 | A8 Jetson ↔ Pixhawk MAVLink (MP KAPALI) | aviyonik + Jetson |
| 09:30–09:50 | A1 RC failsafe → LAND | pilot + aviyonik |
| 09:50–10:05 | A4 CH6 anahtarı: acil durdurma / disarm | pilot + kaptan |
| 10:05–10:20 | A3 pil failsafe (+ geri alma) | aviyonik |
| 10:20–10:35 | A2 GCS (SiK) failsafe | aviyonik + YKS |
| 10:35–10:50 | A13 PM06 akım ↔ pens ampermetre | aviyonik + ikinci kişi |
| 10:50–11:00 | mola · pil şarjı | — |
| 11:00–11:20 | A6 SiK RTT / kayıp / veri hızı | YKS |
| 11:20–11:40 | A5 YKS–İHA–İKA bağlantı kaybı | YKS + Jetson |
| 11:40–11:55 | A9 kamera yatay FOV | Jetson + kayıtçı |
| 11:55–12:10 | A10 Jetson canlı kamera FPS | Jetson |
| 12:10–12:40 | A11 MK15 video zinciri gecikmesi | YKS + Jetson |
| 12:40–12:55 | mola | — |
| 12:55–13:20 | A7 menzil (açık alan varsa) | YKS + Jetson |
| 13:20–13:50 | A12 hover logu (ayrı adım, bağlı/açık alan) | pilot + herkes |
| 13:50–14:00 | Gün sonu (§4) | kaptan |

## 3. Testler

**Ortak Mission Planner adımları (A1–A4, A13).** **M1** `Flight Data → Messages` açık; her testin `Messages` satırları ekran fotoğrafıyla. **M2** mod değişimi HUD'da (sol üst mod yazısı) ve `Messages`'ta; telefon videosu HUD'u ve kumandayı aynı karede tutar. Arm'dan sonra gaz 10 s dipte kalırsa kendiliğinden disarm (`DISARM_DELAY=10` (döküm :271)). **M3** `.bin` yalnız arm'lı koşumda yazılır (`LOG_DISARMED=0` (döküm :538)): disarm sonrası `Flight Data → DataFlash Logs → Download DataFlash Log Via Mavlink` → en son log → `results/atolye_20260912/A<n>_<saat>.bin` adıyla kopyala. **M4** (PC) `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A<n>_<saat>.bin` → `## 2. Olaylar` altında `EV` / `MODE` / `MSG` satırları; yanına `A<n>_<saat>_devrilme.txt` yazar.

### A1 — RC failsafe → LAND (kumanda kapatma, PERVANESİZ) · 20 dk
- **Amaç:** kumanda bağlantısı koparsa aracın Land'e geçişini .bin ve videoyla kanıtlamak. 6 Eylül tezgâh ölçümü **DÜŞTÜ** (barlar sabit kaldı, `Radio Failsafe` gelmedi — D-428 §2); 10 Eylül kullanıcı **BEYANI**: "failsafe'de Land'e geçiyor" (D-444). İkisi de yerinde kalır; bugün ölçülür.
- **Hazırlık:** kumandada 4 yeni AA; pervaneler sökülü; pil takılı; MP USB; `Setup → Mandatory Hardware → FailSafe` sayfası açık. `A1_kumanda.txt`'e yaz: kumanda açık + gaz dipte CH3 PWM, CH5 üç konum PWM; kart değerleri (dökümde `FS_THR_ENABLE=3` (döküm :411), `FS_THR_VALUE=975` (döküm :412), `RC_FS_TIMEOUT=1` (döküm :655), `FLTMODE6=9` (döküm :392)).
- **Adım 1 (disarm):** kumandayı kapat → 5 s içinde CH3 ve CH5 PWM'ini yaz (alıcı son değeri mi tutuyor, failsafe değerine mi iniyor) → aç. **Adım 2 (ArduPilot test #2):** Stabilize, dümenle arm (gaz ≤ 1030 + yaw ≥ 1947, 2 s — D-433), gaz **dipte**, kumandayı kapat. **Adım 3 (asıl ölçüm, test #3):** kumandayı aç, Stabilize, arm, gazı **ortaya** kaldır (motorlar döner), telefon 60 fps, kumandayı kapat; 3 tekrar; sonra M3–M4.
- **Beklenen görüntü:** adım 3'te HUD `Land`, `Messages`'ta `Radio Failsafe`; motorlar yavaşlar, iniş algılanınca kendiliğinden disarm olabilir. Adım 2'de hemen disarm.
- **Komut (PC, M4):** `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A1_<saat>.bin` → `MODE` satırında Land, `MSG`'de `Radio Failsafe`.
- **BEKLENTİ (HESAP + ArduPilot 4.5.7 kaynağı — ölçüm değil):** alıcı çerçeve basmayı keserse tetik `RC_FS_TIMEOUT` = 1 s sonra; CH3'ü 975'in altına indirirse 3 ardışık çerçevede (`FS_COUNTER 3`) → iki yolda da `Radio Failsafe` + Land ≤ ~1 s; alıcı son değeri tutarsa hiçbir yol tetiklenmez (6 Eylül). Gaz dipte / araç yerdeyken eylem Land değil **DISARM** (`Radio Failsafe - Disarming`, `should_disarm_on_failsafe`). Alıcı yalnız CH5'i Land konumuna atıyorsa HUD `Land` olur ama `Radio Failsafe` satırı **gelmez** (mod anahtarı, failsafe değil). 10 PWM kuralı: kumanda kapalı CH3 ≤ 975 − 10 = 965, açık + gaz dipte CH3 ≥ 975 + 10 = 985; ayar yöntemi kumanda kılavuzundan (BEYAN GEREKLİ). Kaynak: https://ardupilot.org/copter/docs/radio-failsafe.html · https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/ArduCopter/radio.cpp · https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/ArduCopter/events.cpp
- **Kabul (SAHA_KOSUM_KAGIDI_20260910.md:54):** adım 3'te kapatma → HUD `Land` ≤ 2 s ∧ `Messages` ya da .bin `MSG`'de `Radio Failsafe` satırı (her tekrar ayrı yazılır). Kabul yoksa A12'de pervane takılmaz.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A1_kumanda.txt` · `A1_failsafe.mp4` · `A1_<saat>.bin` · `A1_<saat>_devrilme.txt`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A2 — GCS (YKS/telemetri) failsafe · 15 dk
- **Amaç:** SiK telemetri hattı koparsa Pixhawk tepkisini ölçmek; `FS_GCS_ENABLE` çelişkisini (6 Eylül dökümü 1, aynı akşam tlog 5 — D-428 §5c, D-429 §4) kartın kendisinden okuyarak kapatmak.
- **Hazırlık:** pervaneler sökülü; hava SiK Pixhawk `TELEM1`'de (`SERIAL1_BAUD=57` (döküm :797)); MP **yer SiK'i üzerinden** (COMx, 57600) bağlı; Pixhawk USB'si PC'ye **takılı değil** (ikinci GCS olur); Jetson `TELEM2`'den **çıkarılmış** (MAVProxy sysid 255 heartbeat'i failsafe'i engeller — config/pixhawk/README.md:143). `A2_gcs.txt` + ekran fotoğrafı: kart `FS_GCS_ENABLE` (dökümde `FS_GCS_ENABLE=1` (döküm :408)), `FS_GCS_TIMEOUT=5` (döküm :409), `FS_OPTIONS=16` (döküm :410), `SYSID_MYGCS=255` (döküm :987). **Değiştirilmez** (mimar kararı, D-428 §5c).
- **Adımlar:** (a) Stabilize, arm, gaz **orta** → yer telsizinin USB'sini çek, kronometre, 15 s motorları filme al → tak, MP yeniden bağlanır → disarm. (b) aynısı gaz **dipte** arm'lıyken. Sonra M3–M4 (bağlantı yokken HUD görünmez; kanıt .bin `MSG`).
- **Beklenen görüntü:** (a) motorlar dönmeyi sürdürür; (b) motorlar ~5 s'de durur. .bin `MSG`'de `GCS Failsafe …` satırı.
- **Komut (PC, M4):** `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A2_<saat>.bin` → `MSG`'de `GCS Failsafe …`, `EV`'de (b) disarm.
- **BEKLENTİ (HESAP + ArduPilot 4.5.7 kaynağı — ölçüm değil):** tetik son GCS heartbeat'inden `FS_GCS_TIMEOUT` = 5 s sonra; MP heartbeat'i 1 Hz → çekmeden 5 − (0…1) = 4–5 s sonra. `FS_OPTIONS` = 16 = bit 4 "pilot kiplerinde GCS kaybında devam" → (a) mod **değişmez**, `GCS Failsafe - Continuing Pilot Control`; (b) `GCS Failsafe - Disarming` (10 s'lik otomatik disarmdan önce). `FS_GCS_ENABLE` eylemi (1 RTL / 5 Land) yalnız Auto/Guided'da görülür — tezgâhta sınanamaz. Kaynak: https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/ArduCopter/events.cpp (`failsafe_gcs_on_event`) · https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/ArduCopter/Parameters.cpp (FS_OPTIONS)
- **Kabul (bu kâğıtta ön kayıt — depoda sayısal eşik yok):** çekmeden ≤ 7 s (= 5 s + 2 s pay) içinde .bin `MSG`'de `GCS Failsafe` satırı ∧ (a)/(b) davranışı yukarıdakiyle aynı ∧ kart `FS_GCS_ENABLE` değeri tutanakta.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A2_gcs.txt` · `A2_gcs.mp4` · `A2_<saat>.bin` · `A2_<saat>_devrilme.txt`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A3 — Pil failsafe (geçici eşik + GERİ ALMA) · 15 dk
- **Amaç:** düşük gerilim failsafe'inin tetiklendiğini göstermek (`BATT_FS_LOW_ACT=1` (döküm :134) = Land); eşik geçici yükseltilir, test sonunda **eski değere döner**.
- **Hazırlık:** pervaneler sökülü; dolu pil; MP USB. Multimetreyle pil gerilimi `V_ölç` (balans dış pinler) + MP HUD gerilimi → `A3_pil.txt`. Kartın `BATT_LOW_VOLT` değerini oku, yaz (dökümde `BATT_LOW_VOLT=14.4` (döküm :138)); ayrıca `BATT_LOW_TIMER=10` (döküm :137), `BATT_CRT_VOLT=14` (döküm :131), `BATT_FS_VOLTSRC=0` (döküm :135, ham gerilim).
- **Adım 1:** Stabilize, arm, gaz **orta** (eşik disarm'da yükseltilirse arm reddedilir: PreArm `Battery 1 low voltage failsafe`).
- **Adım 2 (GEÇİCİ):** `Config → Full Parameter List` → `BATT_LOW_VOLT` = `V_ölç + 0,5` → `Write Params`; kronometre; HUD + `Messages` filme. Land → motorlar yavaşlar → disarm. M3–M4.
- **Adım 3 — GERİ AL (zorunlu, atlanamaz):** `BATT_LOW_VOLT` = **14.4** (ya da hazırlıkta okunan kart değeri) → `Write Params` → `Refresh Params` → değer görülür (ekran fotoğrafı `A3_geri_alma.png`) → Pixhawk'ı **yeniden başlat** (güç kes-ver; pil failsafe'i açılışa dek kilitli kalır) → PreArm'da `low voltage failsafe` yok. Geri alma bitmeden sonraki teste geçilmez.
- **Beklenen görüntü:** `Messages`: `Battery 1 is low …`, ardından `Battery Failsafe`; HUD `Land`.
- **Komut (PC, M4):** `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A3_<saat>.bin` → `MSG`'de `Battery 1 is low`, `MODE`'da Land.
- **BEKLENTİ (HESAP + ArduPilot 4.5.7 kaynağı — ölçüm değil):** gerilim eşiğin altında `BATT_LOW_TIMER` = 10 s kalınca `Battery 1 is low <V>V used <mAh> mAh` → gaz orta: `Battery Failsafe` + Land; gaz dipte / yerde: `Battery Failsafe - Disarming`. Denetim yalnız arm'lıyken; tetiklenen failsafe düşmez (`if (type <= state[i].failsafe) continue;`) → yeniden başlatma şart. Kaynak: https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/libraries/AP_BattMonitor/AP_BattMonitor.cpp · https://github.com/ArduPilot/ardupilot/blob/Copter-4.5.7/libraries/AP_BattMonitor/AP_BattMonitor_Backend.cpp
- **Kabul (bu kâğıtta ön kayıt):** yazımdan ≤ 12 s (= `BATT_LOW_TIMER` 10 s + 2 s pay) içinde `Battery 1 is low` satırı ∧ HUD `Land` ∧ geri alma kanıtı (`BATT_LOW_VOLT` 14.4 okunur + temiz PreArm).
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A3_pil.txt` · `A3_geri_alma.png` · `A3_pil.mp4` · `A3_<saat>.bin`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A4 — Motor acil durdurma / anahtarla disarm (`RC6_OPTION`) · 15 dk
- **Amaç:** kumanda CH6 anahtarıyla motorların durdurulabildiğini göstermek. Bugün `RC6_OPTION=0` (döküm :735): anahtara işlev atanmamış, 56 çevirmede 0 tepki (D-433).
- **KARAR (kaptan, `A4_rc6.txt`): [ ] 153 ArmDisarm  [ ] 31 Motor Emergency Stop** — CH6 iki konumlu {1000, 2000} (D-433); 165 üç konum ister. Risk: uçuşta yanlış çevirme iki seçenekte de motorları durdurur.
- **Adımlar:** pervaneler sökülü; MP `Full Parameter List` → `RC6_OPTION` → `Write Params` → `Refresh Params`. **153:** gaz dipte anahtar yukarı → arm; gazı biraz kaldır; anahtar aşağı. **31:** dümenle arm, gaz biraz; anahtar acil konuma; sonra gaz dipte dümenle disarm (yaw tam sol, 2 s — D-433). 3 tekrar; videoda anahtar ve motorlar aynı karede. M3–M4 (`EV` arm/disarm).
- **Beklenen görüntü:** anahtar çevrildiği anda motorlar durur; 153'te HUD `DISARMED`; `Messages` satırları fotoğraflanır (M1).
- **Komut (PC, M4):** `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A4_<saat>.bin` → `EV`'de arm/disarm satırları.
- **BEKLENTİ (ÜRETİCİ VERİSİ — ArduPilot belgesi, ölçüm değil):** 153 "yukarı → arm (arm denetimlerine bağlı), aşağı → koşulsuz disarm"; 31 "motorları hemen durdurur" (https://ardupilot.org/copter/docs/common-auxiliary-functions.html). Tepki süresi için sayısal kaynak yok → BİLİNMİYOR, videodan okunur.
- **Kabul (bu kâğıtta ön kayıt):** 3/3 denemede anahtar çevrildiği anda motorlar durur (video) ∧ 153'te HUD `DISARMED` ve .bin `EV` disarm satırı; seçilen değer `99_param_sonra.param`'da (şablon/README hizası mimarda, D-433).
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A4_rc6.txt` · `A4_anahtar.mp4` · `A4_<saat>.bin`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A5 — YKS–İHA–İKA bağlantı kaybı (gerçek SiK) · 20 dk
- **Amaç:** İHA heartbeat'i kesilince YKS'nin bağlantı kaybını göstermesi ve İKA'nın (sim) güvenli duruşa geçmesi — gerçek SiK 433 hattında.
- **Kurulum:** hava SiK → Jetson USB (`/dev/ttyUSB0`), yer SiK → PC USB (COMx); A6 SiK ekranında iki uç aynı Net ID.
- **(a) YKS — Komut (PC):** `& $PY -B comms/yks_gui.py --serial COMx --baud 57600 --hakem-log results/atolye_20260912/A5_hakem_log.jsonl`
- **Komut (Jetson):** `python -B -u comms/iha_sender.py --serial /dev/ttyUSB0 --baud 57600 --rota-json results/fdr_sprint_20260910/H1/k3b/v1/harita_4_kolay/iha_scan/rota.json --heartbeat-sure 600 | tee results/atolye_20260912/A5_iha.txt` → telefon 60 fps (Jetson terminali + YKS aynı karede) → Jetson'da **Ctrl+C**; 3 tekrar.
- **(b) İKA sim — YKS kapatılır; Komut (PC):** `& $PY -B -u comms/ika_receiver.py --serial COMx --baud 57600 | Tee-Object -FilePath results/atolye_20260912/A5_ika.txt` → Jetson'da (a)'daki gönderici yeniden → Ctrl+C → gönderici yeniden; 3 tekrar.
- **Beklenen görüntü:** YKS İHA satırı `hb 0.x sn` → kesince kırmızı `(BAĞLANTI KAYBI!)`; İKA `✓ Açık yol alındı` → `⚠ BAĞLANTI KAYIP (3 sn sessizlik) → GÜVENLİ DURMA` → `✓ Bağlantı geri geldi`.
- **BEKLENTİ (HESAP — ölçüm değil):** heartbeat aralığı `IHA_HEARTBEAT_ARALIK_S = 1.0` (codes/karar_sozlesmesi.py:145); İKA eşiği `hb_timeout=3.0` (comms/ika_receiver.py:27), YKS eşiği `canli = 0.0 <= yas < 3.0` (comms/yks_gui.py:4387) → son heartbeat kesmeden 0–1 s önce ⇒ gösterge kesmeden 3 − (0…1) = 2–3 s sonra (+ seri okuma zaman aşımı ve YKS ekran tazeleme — BİLİNMİYOR). Metinler: `(BAĞLANTI KAYBI!)` (comms/yks_gui.py:4428), `BAĞLANTI KAYIP` (comms/ika_receiver.py:359).
- **Kabul (bu kâğıtta ön kayıt; eşik koddaki 3 s + 1 s pay):** 3/3 tekrarda kesme → YKS `(BAĞLANTI KAYBI!)` ≤ 4 s ∧ İKA `GÜVENLİ DURMA` ≤ 4 s ∧ gönderici dönünce ikisi de geri gelir.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A5_hakem_log.jsonl` · `A5_iha.txt` · `A5_ika.txt` · `A5_kesme.mp4`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A6 — SiK RTT / kayıp / veri hızı · 20 dk
- **Amaç:** gerçek SiK 433 çiftinde RTT, kayıp ve veri hızını IKA_GO (0,25 s) ve PARAŞÜT (0,20 s) kadansında ölçmek; H2 ölçümü RADYOSUZDU (TCP-seri köprüsü).
- **Kurulum:** iki telsiz Pixhawk'tan ayrılır; ikisi aynı PC'de iki COM portu ya da yankı Jetson'da; antenler dik, 2–5 m. **SiK ayarı** (MP bağlı değilken): `Setup → Optional Hardware → SiK Radio → Load Settings` → Local/Remote: Baud, Air Speed, Net ID, Tx Power, ECC, Mavlink, Op Resend, Min/Max Freq, Num Channels, Duty Cycle, LBT RSSI → `A6_sik_mp_ekrani.png`, değerler `A6_sik_ayar.txt`.
- **Yankı — Komut (PC):** `& $PY -B scripts/sik_rf_olc.py --rol yanki --port COMy --baud 57600` · ya da **Komut (Jetson):** `python -B scripts/sik_rf_olc.py --rol yanki --port /dev/ttyUSB0 --baud 57600` (açık kalır).
- **Ölç — Komut (PC):** `& $PY -B scripts/sik_rf_olc.py --rol olc --port COMx --baud 57600 --n 200 --aralik 0.25 --cikti results/atolye_20260912/A6_sik_ikago.json` ve aynısı `--aralik 0.2 --cikti results/atolye_20260912/A6_sik_parasut.json`.
- **Beklenen görüntü:** `gonderilen : 200` · `ACK alinan` · `kayip` · `RTT p95` · `veri hizi` · `VERDIKT : tekrar tasarimiyla UYUMLU` (çıkış 0; 1 = UYARI, 2 = ÖLÇÜLEMEDİ).
- **BEKLENTİ (HESAP + BENZER ÖLÇÜM — ölçüm değil):** 57600 baud 8N1 = 10 bit/bayt → 10 / 57600 = 0,174 ms/bayt; çerçeve ≈ 80 B (16070 B / 200 prob, results/fdr_sprint_20260910/H2/ozet.json:139) → seri süre 80 × 0,174 = 13,9 ms her uçta; hava 64 kbps varsayılanı (https://ardupilot.org/copter/docs/common-3dr-radio-advanced-configuration-and-technical-information.html) → 80 × 8 / 64000 = 10 ms (ECC açıksa ≈ 2×); RTT alt sınırı 2 × (13,9 + 10 + 13,9) = 75,6 ms (ECC ile 95,6 ms) + SiK TDM dilim beklemesi (BİLİNMİYOR). BENZER ÖLÇÜM (RADYOSUZ köprü): RTT p50/p95 1,33/1,83 ms (results/fdr_sprint_20260910/H2/ozet.json:131-132), veri hızı 322,5 B/s (results/fdr_sprint_20260910/H2/ozet.json:143) ve 403 B/s (results/fdr_sprint_20260910/H2/ozet.json:189) → kayıpsız hatta ≈ 80 / 0,25 = 320 B/s ve 80 / 0,2 = 400 B/s.
- **Kabul (betik eşiği, scripts/sik_rf_olc.py:39):** iki kadansta da RTT p95 < min(`IKA_GO_TEKRAR_ARALIGI_S = 0.25` (codes/karar_sozlesmesi.py:2095), `PARASUT_TEKRAR_ARALIGI_S = 0.20` (codes/karar_sozlesmesi.py:2116)) = 200 ms, çıkış 0; kayıp ve veri hızı yalnız raporlanır (scripts/sik_rf_olc.py:43).
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A6_sik_ikago.json` · `A6_sik_parasut.json` · `A6_sik_ayar.txt` · `A6_sik_mp_ekrani.png`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A7 — Menzil: SiK + MK15 video (açık alan varsa; yoksa ÖLÇÜLEMEDİ — sahada) · 25 dk
- **Amaç:** SiK ve MK15 videonun görev için gereken mesafede çalışmasını göstermek.
- **Adımlar:** yankı ucu İHA'nın kendisi (Jetson İHA'daki 12,2 V hattından, pil takılı, **pervanesiz**; hava SiK Jetson USB'de, A6 yankı komutu) uzağa taşınır; iki uçta telefon GPS koordinatı (ekran görüntüsü `A7_konum_<m>.png`); ≈100 m'de ve ulaşılan en uzak noktada — **Komut (PC):** `& $PY -B scripts/sik_rf_olc.py --rol olc --port COMx --baud 57600 --n 200 --aralik 0.2 --cikti results/atolye_20260912/A7_sik_<mesafe>m.json`. A11 zinciri kuruluysa aynı mesafede YKS video panelinin ekran fotoğrafı `A7_mk15_<mesafe>m.png`.
- **Beklenen görüntü:** A6 ile aynı satırlar; YKS video panelinde CANLI görüntü (BAYAT değil).
- **BEKLENTİ (HESAP — ölçüm değil):** gereken mesafe: İHA-UB kenarı `SARTNAME_IHA_UB_KENAR_M = 300.0` (codes/karar_sozlesmesi.py:2017); YKS bir köşedeyse en uzak nokta karşı köşe 300 × √2 = 424,3 m, 32 m kalkış irtifasıyla (config/pixhawk/README.md görev tablosu) eğik √(424,3² + 32²) = 425,5 m; YKS kenar ortasındaysa √(300² + 150²) = 335,4 m. Cihaz menzili: bu çift için ölçüm yok (DDR ">%98, 300 m" iddiasının kanıtı yok — SAHA_KOSUM_KAGIDI_20260910.md:31), MK15 için depoda sayı yok → BİLİNMİYOR; AIR_SPEED düştükçe SiK menzili artar (A6'daki SiK belgesi).
- **Kabul (bu kâğıtta ön kayıt; RTT eşiği A6 ile aynı):** ölçülen mesafe ≥ 425,5 m'de `sik_rf_olc` çıkış 0 (p95 < 200 ms) ∧ aynı mesafede YKS videosu CANLI. Daha kısa mesafede ölçüldüyse sonuç "kısmi — d m" yazılır, menzil kabulü ÖLÇÜLEMEDİ.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A7_sik_<mesafe>m.json` · `A7_konum_<m>.png` · `A7_mk15_<mesafe>m.png`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A8 — Jetson ↔ Pixhawk MAVLink (`mavlink_dogrula` 3/3) · 15 dk
- **Amaç:** Jetson'un Pixhawk'tan HEARTBEAT, konum ve iniş durumunu sözleşme hızında aldığını ölçmek; 6 Eylül'de ÖLÇÜLEMEDİ (`/dev/ttyACM0` yoktu — D-431).
- **Hat — KARAR (insan): [ ] TELEM2 `/dev/ttyTHS1`  [ ] USB `/dev/ttyACM0`** (saha kâğıdı adım 1'de işaretlendiyse o; kablolama SAHA_KOSUM_KAGIDI_20260910.md:11). Pixhawk USB beslemeli; MP **kapalı** (SR akışlarını ezer).
- **Komut (Jetson):** `python -B scripts/mavlink_dogrula.py --mavlink <HAT> --baud 57600 --sysid 1 --json results/atolye_20260912/A8_mavlink.json | tee results/atolye_20260912/A8_mavlink.txt` · terminalin fotoğrafı `A8_ekran.jpg`. `DUSTU` ise `NEDEN:` satırı tutanağa; TELEM2'de TX/RX çapraz ve `BRD_SER2_RTSCTS` 0 mı bakılır.
- **Kart kanıtı (yedek) — Komut (PC):** Pixhawk USB'si PC'de, MP kapalı: `& $PY -B scripts/mavlink_dogrula.py --mavlink COMx --sysid 1 --json results/atolye_20260912/A8_mavlink_pc.json`.
- **Beklenen görüntü:** `HEARTBEAT: sysid=1 … autopilot=3` · `GLOBAL_POSITION_INT` ve `EXTENDED_SYS_STATE` satırları · `VERDIKT:` satırında `DUSTU` yok, çıkış 0.
- **BEKLENTİ (HESAP — ölçüm değil):** betik akışları asgari × `MAVLINK_AKIS_ISTEK_HIZ_CARPANI = 2` (codes/karar_sozlesmesi.py:2260) hızında ister → GLOBAL_POSITION_INT ≈ 4 × 2 = 8 Hz (dökümde de `SR2_POSITION=8` (döküm :952)), EXTENDED_SYS_STATE ≈ 1 × 2 = 2 Hz (SR akışında yok, yalnız istekle — config/pixhawk/README.md:154), HEARTBEAT ≈ 1 Hz; hat `SERIAL2_BAUD=57` (döküm :800) = 57600.
- **Kabul (betik eşiği):** Jetson hattında HEARTBEAT sysid 1 ≥ `MAVLINK_HEARTBEAT_ASGARI_HZ = 0.5` (codes/karar_sozlesmesi.py:2221) ∧ konum ≥ `MAVLINK_KONUM_ASGARI_HZ = 4.0` (codes/karar_sozlesmesi.py:2215) ∧ iniş durumu ≥ `MAVLINK_DURUM_ASGARI_HZ = 1.0` (codes/karar_sozlesmesi.py:2219) → 3/3, çıkış 0.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A8_mavlink.json` · `A8_mavlink.txt` · `A8_ekran.jpg` · (yedek) `A8_mavlink_pc.json`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A9 — Kamera yatay FOV · 15 dk
- **Amaç:** RPi HQ (IMX477) + 6 mm lensin gerçek yatay görüş açısını ölçmek (`FOV=` beyanı; rota ölçeği buna bağlı). Kablo 15→22 pin CSI şerit; bir kez `jetson-io` → IMX477 (SAHA_KOSUM_KAGIDI_20260910.md:17).
- **Komut (Jetson), köprü (açık kalır):** `/usr/bin/python3 scripts/kamera_koprusu.py --port 8080 --fps 5` · **kare:** `python -B codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --kaydet results/atolye_20260912/A9_kare.jpg | tee results/atolye_20260912/A9_kamera.txt`
- **Geometri:** kamera duvara dik, lens–duvar **d = 2,00 m** (ölçü şeridi); duvarda **s = 1,00 m** aralıklı iki işaret, karenin orta yarısında; `A9_kare.jpg`'de iki işaretin x-piksel farkı **p** (PC'de Paint: imleç koordinatı alt çubukta).
- **Komut (PC):** `& $PY -B scripts/kamera_fov_hesapla.py --genislik-px 1280 --isaret-px <p> --isaret-m 1.00 --mesafe-m 2.00 --yukseklik-px 720 | Tee-Object -FilePath results/atolye_20260912/A9_fov.txt`
- **Beklenen görüntü:** `cozunurluk : 1280x720` (kamera) · `ODAK=… px  FOV_yatay=… derece` (hesap).
- **BEKLENTİ (HESAP — ölçüm değil):** IMX477 etkin genişlik 6,287 mm (https://www.raspberrypi.com/documentation/accessories/camera.html), lens 6 mm (D-442 ek) → FOV = 2 · atan(6,287 / (2 · 6)) = 2 · atan(0,5239) = 55,3°; beklenen p = 1280 / (2 · 0,5239) · 1,00 / 2,00 = 610,8 px. Sensör kipi görüntüyü kırpıyorsa FOV daha dar (BİLİNMİYOR).
- **Kabul (SAHA_KOSUM_KAGIDI_20260910.md:20):** FOV_yatay 50–65°; dışındaysa d/s/p yeniden ölçülür.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A9_fov.txt` · `A9_kare.jpg` · `A9_kamera.txt`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A9-ek — Kamera kipi (4:3 / 16:9) ve kamera montaj yaw'ı · 10 dk  — *12 Eylül 01:2x, mimar (D-451 §T237-3, D-457)*
- **Amaç:** iki sayı FDA uçuş planını belirliyor. (1) **Kip:** sensör 4:3 mü veriyor, 16:9 kırpma mı — FDA irtifası (32 m / 40 m) ve yol etiketi kararı buna bağlı (D-457 ön kaydı: **4:3 ölçülürse** alan-ölçekli etiket koşullu açılır; **16:9 ölçülürse** kare-göreli etiket kalır). (2) **Montaj yaw'ı:** görüntünün yukarısı, İHA burnuna göre kaç derece — FDA'da `CONDITION_YAW` bu değerle düzeltilir.
- **Komut (Jetson), kip:** `v4l2-ctl --list-formats-ext -d /dev/video0 | tee results/atolye_20260912/A9e_kipler.txt` · ayrıca köprü açıkken `curl -s http://127.0.0.1:8080/durum | tee results/atolye_20260912/A9e_durum.json` (alanlar: `boyut`, `kamera_ayari`, `cozunurluk_eslesti`). nvargus kullanılıyorsa açılış günlüğündeki **sensor mode** satırları da aynı dosyaya eklenir.
- **Kip hükmü:** sensörün tam yüksekliğini veren mod kullanılıyorsa **4:3**; yalnız dikeyde kırpılmış mod varsa **16:9**. En/boy = genişlik/yükseklik olarak yazılır (ör. 4032×3040 → 4:3; 1920×1080 → 16:9 kırpma). Karar: `A9e_kipler.txt`'teki listeyle birlikte tek satır yazılır.
- **Montaj yaw'ı (ölçüm):** İHA'yı yere sabit bir çizgiye (ör. duvar kenarı) burnu bakacak şekilde koy; kamerayı normal uçuş konumunda çalıştır; `A9_kare.jpg` benzeri tek kare al (`A9e_yaw_kare.jpg`). Karede o çizgi **yukarı** doğruysa 0°, **sağa** doğruysa 90°, **aşağı** 180°, **sola** 270°. Ara açı varsa iletki ya da karedeki çizginin eğiminden hesapla (`derece = atan2` ile) ve nasıl ölçtüğünü yaz.
- **BEKLENTİ (TAHMİN — ölçüm değil):** montaj yaw'ı 0° ya da 180° (kamera gövdeye burun-kuyruk ekseninde bağlanıyorsa); kip, IMX477 nvargus varsayılanında genellikle tam sensör (4:3) — **ölçülmeden varsayılmaz**.
- **Kabul:** yok — bu iki kalem **ölçümdür**, kapı değildir. Ölçülemezse FDA planı 16:9 varsayımıyla (40 m) ve montaj yaw'ı **BEYAN GEREKLİ** ile yazılır.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A9e_kipler.txt` · `A9e_durum.json` · `A9e_yaw_kare.jpg` · `A9e_olcum.txt` (iki satır: `KIP=4:3|16:9` ve `MONTAJ_YAW_DERECE=<değer>`)
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A10 — Jetson canlı kamera FPS (köprü + algı zinciri) · 15 dk
- **Amaç:** algı zincirinin canlı CSI kaynağıyla kare hızını ölçmek (6 Eylül ölçümü dosya kaynağıydı, kamera bağlı değildi — D-431).
- **Komut (Jetson):** A9 köprüsü açıkken `python -B codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --zincir --model jetson_paket/models/navitas_seg_v36_best.pt --imgsz 512 | tee results/atolye_20260912/A10_canli_fps.txt` · terminalin fotoğrafı `A10_ekran.jpg`. Model yolu 6 Eylül koşumundaki dosyadır (results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json `vakalar[0].model`); yoksa `ls jetson_paket/models/*.pt` (manifest `asil_model_pt`).
- **Beklenen görüntü:** `okunan kare : 60 (dusen: 0)` · `kare gecikmesi : p50=… ms p95=… ms` · `OLCULEN FPS` · `rota durumlari`.
- **BEKLENTİ (BENZER ÖLÇÜM — ölçüm değil):** aynı kart, pt, imgsz 512, dosya kaynağı: p50/p95 739/942 ms = 1,35/1,06 FPS (results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json:69-70, D-431). Canlı kaynakta köprü okuma + JPEG çözme payı eklenir (BİLİNMİYOR) → beklenti ≤ 1,35 FPS.
- **Kabul (FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:915):** p50 ve p95 ayrı ayrı ≥ 0,61 FPS ⇔ kare gecikmesi p95 ≤ 1000 / 0,61 = 1639 ms (HESAP).
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A10_canli_fps.txt` · `A10_ekran.jpg`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A11 — MK15 video zinciri camdan cama gecikme · 30 dk
- **Amaç:** Jetson → MK15 → YKS video yolunun gecikmesini ölçmek (görsel kanıt; rota verisi ve hakem onayı SiK'te kalır — TASARIM §1).
- **Kurulum sırası:** (1) Jetson DP → DP→HDMI adaptör → (mini) HDMI kablo → SIYI HDMI giriş dönüştürücü; dönüştürücüye 12 V; Ethernet → Air Unit Mini. (2) Dönüştürücü IP **192.168.144.25** (varsayılan, `rtsp://192.168.144.25:8554/main.264`); **192.168.144.11 / .12 / .20 kullanılmaz** (hava/yer/Android sabit IP'leri — results/fdr_sprint_20260910/H9_MK15/TASARIM.md:15-16). (3) Kumanda → SIYI FPV → **Camera 1** tam ekran, OSD kapalı. (4) Kumanda HDMI → USB HDMI yakalama kartı → PC (port yoksa ÖLÇÜLEMEDİ, neden "kumanda HDMI yok"). (5) PC'de yakalama indeksi: `& $PY -B codes/kamera_dogrula.py --kaynak 1 --kare 30 --kaydet results/atolye_20260912/A11_indeks1.jpg` (0 çoğunlukla dizüstü kamerası; kareden anlaşılır). (6) `& $PY -B scripts/kamera_koprusu.py --kaynak <indeks> --port 8080` (açık kalır). (7) `& $PY -B comms/yks_gui.py --kamera-url http://127.0.0.1:8080 --gorunum kamera` (T226 birleşince `--kamera-etiket` bayrağı eklenir — bugün YOK, yazılmaz).
- **Jetson ekranı — Komut (Jetson):** `/usr/bin/python3 scripts/kamera_koprusu.py --port 8080 --fps 30` → tarayıcıda `http://127.0.0.1:8080/video` tam ekran (F11). T227 birleşince ikinci ölçüm işaretli karedeki UTC saatiyle.
- **Fotoğraflar (T230):** kumanda HDMI portu, Air Unit Mini etiketi (gerilim aralığı), MK15 `Link Status` (bant/güç) → `A11_foto_*.jpg`.
- **Ölçüm:** PC'de Windows **Saat → Kronometre**, YKS video panelinin yanında; Jetson kamerası bu kronometreye bakar; telefon 60 fps PC ekranını filme alır; videoda 5 farklı karede iki kronometre okunur: gecikme = canlı − videodaki → `A11_gecikme.txt` (5 satır + p50/maks).
- **Beklenen görüntü:** YKS video panelinde kronometrenin gecikmeli kopyası, yanında canlısı.
- **BEKLENTİ (ÜRETİCİ VERİSİ + BENZER ÖLÇÜM — ölçüm değil):** MK15 hattı 130–250 ms (üretici, QGC, H.265) + USB yakalama 49–85 ms (MS2130/MS2109, HyperHDR) (results/fdr_sprint_20260910/H9_MK15/TASARIM.md:18) → bilinen kısımlar 130 + 49 = 179 ms … 250 + 85 = 335 ms; Jetson ekran yolu, dönüştürücü H.264 kodlama, kumanda ekran aynası, PC köprüsü + YKS BİLİNMİYOR. İşaretli kare ≤ 2 Hz (T227) → karar görseli + ≤ 0,5 s eskir → 0,335 + 0,5 = 0,835 s + bilinmeyenler.
- **Kabul (results/fdr_sprint_20260910/H9_MK15/TASARIM.md:73):** camdan cama gecikme ≤ 1,0 s — 5 ölçümün **maksimumu** (istatistik bu kâğıtta ön kayıt).
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A11_gecikme.txt` · `A11_gecikme.mp4` · `A11_foto_*.jpg`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A12 — Hover logu (.bin) — AYRI ADIM, pervaneli, bağlı/açık alan · 30 dk
- **Amaç:** hover'da gaz, titreşim ve akımı .bin'den ölçmek ("şu an başarıyla hover yapabiliyoruz" — BEYAN, D-439; log/video yok).
- **Ön koşul (bağlayıcı; biri eksikse A12 ÖLÇÜLEMEDİ, pervane takılmaz):** A1 kabul ∧ A13 yapıldı ∧ `SAHA_OLAY_SONRASI_MUAYENE.md` madde 0–13 ∧ M1 motoru değişti (D-429) ∧ pervane eli doğru (MUAYENE madde 4) ∧ ip/kayış ya da açık alan, herkes ≥ 5 m.
- **Adımlar:** dolu pil (multimetre V → `A12_hover.txt`); Stabilize; gaz 0 → hover **≥ 2 s rampa** (D-429 §6.1); 1–2 m'de **≥ 30 s** hover; iniş, disarm; MP `Full Parameter List` → öğrenilen `MOT_THST_HOVER` (başlangıç `MOT_THST_HOVER=0.35` (döküm :580), `MOT_HOVER_LEARN=2` (döküm :565)) ekran fotoğrafı; video `A12_hover.mp4`; M3 → `A12_hover.bin`.
- **Komut (PC):** `& $PY -B scripts/tlog_akim_ozet.py results/atolye_20260912/A12_hover.bin --pencere 10 --json results/atolye_20260912/A12_akim.json | Tee-Object -FilePath results/atolye_20260912/A12_akim.txt` · `& $PY -B scripts/ucus_logu_devrilme.py results/atolye_20260912/A12_hover.bin`
- **Beklenen görüntü:** akım özetinde pencere başına `I_p50 / I_maks / V_min / PWM_maks`, `UYARI` yok; devrilme özetinde `## 4. VIBE (max): X … Y … Z …`.
- **BEKLENTİ (ÜRETİCİ VERİSİ + HESAP — ölçüm değil; kütle BİLİNMİYOR, tartı yok — D-439):** X2220 980KV, 4S + APC1047 (10×4,5 için DOĞRULANMADI); motor başına itki = m / 4: 2,0 kg → 500 g → 4,8 A · 2,5 kg → 625 g → ≈6,5 A · 3,0 kg → 750 g → ≈8,7 A (FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:318-320; http://en.rcsunnysky.com/x-fixedwingseries/53.html) → 4 motor 19,2–35 A + aviyonik; itki oranı = m / (4 × 2130 g) = %23,5 / %29,3 / %35,2. `MOT_THST_HOVER` bu orana yakın ama eşdeğer değil (itki eğrisi, pil gerilimi) — BİLİNMİYOR. VIBE için benzer ölçüm YOK.
- **Kabul (T211 kapısı — D-435 Ölçüm 2; titreşim eşiği ArduPilot belgesi):** öğrenilen `MOT_THST_HOVER` ≤ 0,50 ∧ VIBE X/Y/Z maks < 30 m/s² (https://ardupilot.org/copter/docs/common-measuring-vibration.html: "below 30m/s/s are normally acceptable") ∧ motor başına hover akımı (BAT.Curr / 4) ≤ 38 A (FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:315). Akım yalnız A13 kabul edildiyse ölçüm sayılır; `tlog_akim_ozet` `UYARI` basarsa akım ÖLÇÜLEMEDİ.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A12_hover.bin` · `A12_akim.json` · `A12_hover_devrilme.txt` · `A12_hover.mp4` · `A12_hover.txt`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

### A13 — PM06 akım kanalı ↔ pens ampermetre (PERVANESİZ, A12'den önce) · 15 dk
- **Amaç:** 6 Eylül'de PM06 akım kanalı ölçmüyordu: pervaneli 1949 PWM'de tepe 0,44 A, gerilim 9,35 V (D-440; results/fdr_sprint_20260910/saha_kosum/tlog_akim_ozet_20260906.txt) → bugün aynı anda pens ampermetreyle karşılaştırma.
- **Önce:** PM06 → `POWER1` oturmuş, ESC güç hattı PM06 şantından geçiyor (foto `A13_pm06.jpg`); `BATT_MONITOR=4` (döküm :139), `BATT_CURR_PIN=4` (döküm :132), `BATT_AMP_PERVLT=36.36` (döküm :126).
- **Adımlar:** pervaneler sökülü; pens DC kipinde **sıfırlanır** (DC ZERO/REL), pilin **tek** iletkenine takılır; MP USB (tlog kendiliğinden yazılır); `Setup → Optional Hardware → Motor Test` → `Test all motors` %30 5 s, sonra %50 5 s; her kademede pens ve MP HUD akımı aynı karede filme (`A13_akim.mp4`) → `A13_akim.txt` (kademe | pens A | PM06 A | fark % | pens çözünürlüğü); `Messages` fotoğrafı (M1).
- **Komut (PC):** `& $PY -B scripts/tlog_akim_ozet.py "<MP tlog>" --pencere 5 --json results/atolye_20260912/A13_akim.json | Tee-Object -FilePath results/atolye_20260912/A13_tlog_ozet.txt`
- **Beklenen görüntü:** MP HUD pil satırında akım motor testiyle yükselir; pens ile aynı mertebe.
- **BEKLENTİ (ÜRETİCİ VERİSİ — ölçüm değil):** pervanesiz motor ≈ yüksüz akım 0,7 A @ 10 V (veri sayfası, FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:304) → 4 motor tam devirde ≈ 4 × 0,7 = 2,8 A; 4S'te ve %30–50'de fark BİLİNMİYOR; + aviyonik. PM06 çalışıyorsa MP akımı pensle aynı mertebede; 6 Eylül gibi ~0 A okursa kanal hâlâ ölçmüyor.
- **Kabul (T232 görev tanımı — D-440 kapanışı; bu kâğıtta ön kayıt):** her kademede |PM06 − pens| ≤ %10 × pens; aksi hâlde PM06 akımı A12'de ölçüm sayılmaz.
- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A13_akim.txt` · `A13_akim.mp4` · `A13_akim.json` · `A13_pm06.jpg`
- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`

## 4. Gün sonu (13:50–14:00)
- MP (USB) `Config → Full Parameter List → Save to file` → `results/atolye_20260912/99_param_sonra.param`; `Compare Params` ile `00_param_once.param`'a karşı fark listesinin ekran fotoğrafı `99_param_fark.png` — beklenen tek fark `RC6_OPTION` (A4); başka fark varsa yazılır (A3 geri alınmamış olabilir).
- `results/atolye_20260912/SONUC_SABLONU.md` doldurulur (değer dosyadan; boş = ÖLÇÜLEMEDİ); `DEVAM.md` satırı kapatılır.
- Klasör mimara: **(a) git** — `git checkout -b atolye-20260912` → `git add results/atolye_20260912` → `git commit -m "12 Eylul atolye olcumleri"` → `git push -u origin atolye-20260912` (50 MB üstü video/log Drive'a, bağlantısı sonuç tablosuna) **ya da (b) USB/Drive** — klasör zip'lenir. Mimar dosyaları okumadan FDR sonuç sütunu (T231) doldurulmaz.

## 5. Sonuç tablosu
`results/atolye_20260912/SONUC_SABLONU.md` — A1–A13 satırı: ölçülen değer, dosya, ÖLÇÜLDÜ/ÖLÇÜLEMEDİ. Kâğıdın kapısı: `tests/test_atolye_test_gunu.py`.
