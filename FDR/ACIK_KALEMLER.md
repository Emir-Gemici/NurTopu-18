# FDR — AÇIK KALEMLER (kim · ne zaman · nasıl kapanır)

> Taslakta ~~**197 satır**~~ ~~**530 satır**~~ ~~**550 satır** (10 Eylül 2026 öğle, T217 sonrası `scripts/fdr_acik_kalem_cikar.py` sayımı; sabah birleştirmeleriyle 533'tü, T217 +17 — §3.3.1.3.3/§3.3.1.3.4'ün fiziksel-arayüz BEYAN ve RF/Pixhawk ÖLÇÜLEMEDİ satırları)~~ **556 satır** (10 Eylül 2026 akşamı, T214-B sonrası aynı betik; +6 — görev icra simülasyonu video linki BEYAN satırları: `BOLUM_3` §3.3.3 kapı tablosu ve §3.3.3.3, `BOLUM_4` Y-4-M07 satırı, §4.7 özet tablosu, §4.13.1 madde 19, §4.13.4 madde 8; 3 Eylül simülasyon metninin ÖLÇÜLEMEDİ satırları üstü çizili durduğu için sayımda kalır) "BEYAN GEREKLİ" ya da "ÖLÇÜLEMEDİ" ile işaretli
> (ham liste: `ACIK_KALEMLER_HAM.md`). Bunlar eksiklik değil, **dürüstlük
> işaretidir**: rapor ölçülmemiş bir şeyi ölçülmüş gibi yazmaz. Aşağıda
> sahibine ve kapanma tarihine göre gruplanmış hâli var.
>
> Sıralama kapanma tarihine göredir; en üsttekiler rapor teslimini bekletir.

## 0. 🔴 12 Eylül — RAPORU BEKLETEN, en öncelikli (T255, D-470)

> **Arena "3 güzergâh" mı "1 güzergâh" mı?** Bu rapordaki ve tüm mimarideki 3-güzergâh
> varsayımı (`§3.3.1.3` arena tablosu, README.md, K3 rota-tespit ölçümleri) kullanıcının
> bir toplantıda aktardığı "artık 1 güzergâh" resmi bilgisiyle çelişiyor. Kaynak henüz
> **yazılı doğrulanmadı** (yalnız BEYAN — muhtemel kayıt `İleri_Otonom_Yarı_Finaller-soru-cevap-oturumu.mp4`,
> transkript çıkarılmadı). Doğrulanıp kapsam kararı verilmeden ne rapor "3 güzergâh" diye
> eskisi gibi bırakılır (bilinen çelişki sessizce gizlenmiş olur) ne de sessizce "1 güzergâh"a
> çevrilir (doğrulanmamış BEYAN ölçülmüş gibi yazılmış olur) — **kanıt: `REVIEW_LOG.md` D-470, `TASK_QUEUE.md` T255.**

## 1. Cumartesi 5 Eylül — donanım geldiği gün kapanır (ÖLÇÜM)

> 🧾 **Saha koşum kâğıdı (10 Eylül, T219 · ON_KAYIT H6):** kalem 2, 3, 6 ve 12 ekibin mimar olmadan koşacağı tek sayfa `SAHA_KOSUM_KAGIDI_20260910.md` ile kapanır (tartı kullanıcı kararıyla kâğıt dışı, D-439 — kütle BEYAN); sonuçlar `results/fdr_sprint_20260910/saha_kosum/` altına yazılır (kapı `tests/test_saha_kosum_kagidi.py`). ⚠ 6 Eylül tlog'unda PM06 akım kanalı motorlar 1949 PWM'deyken en fazla 0,44 A okudu (`scripts/tlog_akim_ozet.py`; kanıt `results/fdr_sprint_20260910/saha_kosum/tlog_akim_ozet_20260906.txt`) — kalem 12 için önce akım hattı doğrulanır.

⚠ **KOŞULSUZ DEĞİL.** Aşağıdaki kalemlerden **3, 4 ve 5 açılmış bir Jetson
gerektirir**. D-413'e göre kartta microSD yuvası yoktur (eMMC modül + M.2) ve
eMMC'nin **boş çıkma ihtimali vardır**; o durumda Ubuntu x86_64 host + SDK
Manager yolu (~20 GB indirme + NVIDIA hesabı + micro-USB) gerekir ve Jetson
cumartesi açılmayabilir. Ayrıca `python3.8` kurulumu **internet ister** — ⚠ **GEÇERSİZ (D-431, 6 Eylül ölçümü):** kart Jetson Orin Nano Developer Kit 4 GB / JetPack 7.2.1 **kurulu** / Python 3.12 çıktı; eMMC-flash-`python3.8` zinciri düştü, kurulum `~/venv312` + çevrimiçi pip ile yapıldı (`jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §1–2)
(`JETSON_NANO_KURULUM.md` §3.1).

Bu üç kalem için doğru okuma: **"Jetson açılırsa cumartesi kapanır; açılmazsa
`ÖLÇÜLEMEDİ` olarak taşınır."** Ölçülemeyen şey geçmiş sayılmaz.

> ⚠ **6 Eylül düzeltmesi (D-431):** Jetson 5 Eylül'de değil **6 Eylül'de** açıldı ve yukarıdaki varsayımların tamamı kartla yanlışlandı: kart **Jetson Orin Nano Developer Kit 4 GB** (p3767-0004), JetPack **7.2.1** (L4T R39.2.1), Ubuntu 24.04, Python **3.12.3**, kök **NVMe** — eMMC/microSD, `python3.8`, cp38 tekerlek ve venv38 kısıtları bu kartta geçersiz (`results/jetson_20260906/ORTAM_KUNYESI.txt`). Kalem 4 ve 5 aşağıda ÖLÇÜLDÜ olarak kapatıldı; kalem 3 (Pixhawk MAVLink kapısı) açık — 6 Eylül'de Pixhawk Jetson'a bağlı değildi (`jetson_baslat.sh --kuru`: `[YOK]` yalnız `/dev/ttyACM0`, çıkış 3).

| # | kalem | nasıl kapanır | bölüm |
|---|---|---|---|
| 1 | Kalkış kütlesi, ağırlık merkezi, **her parçanın gerçek tartısı** | tartı + tutanak; UHDR ve Bölüm 5/7 bunu ister | 3, 5, 7 |
| 2 | Kameranın **ölçülen** yatay görüş açısı | `codes/kamera_dogrula.py` (bugünkü 55–63° bir **lens hesabıdır**, ölçüm değil) | 3 |
| 3 | Gerçek Pixhawk üzerinde MAVLink akış kapısı | `scripts/mavlink_dogrula.py` üç uçta aynı anda: HEARTBEAT sysid · konum ≥ 4 Hz · iniş durumu ≥ 1 Hz | 3, 4, 6 |
| ~~4~~ | ~~**Jetson Nano gerçek FPS** (p50/p95)~~ → **ÖLÇÜLDÜ 6 Eylül (D-431)** — kart Orin Nano Developer Kit 4 GB; `scripts/jetson_fps.py` 120 örnek, imgsz 512, `data/raw_frames`, mpp=None: **pt p50/p95 1,35/1,06 FPS** (739/942 ms) · **engine 1,58/1,33 FPS** (635/751 ms) · eşik **0,61** → **GEÇTİ**; 10 dk sürekli (900 örnek): pt 770/922 ms · engine 649/765 ms, tegrastats gpu ≤ 56,3 °C. ONNX kolu **HATA** (`cudaErrorNoKernelImageForDevice`). Sınır: mpp=None ölçeksiz Katman-A kipidir; kamera bağlı değildi | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` · `results/jetson_20260906/jetson_fps_20260906_orin_nano_10dk/ozet.json` · `results/jetson_20260906/jetson_fps_20260906_orin_nano_10dk/tegrastats.log` | 3, 4 |
| ~~5~~ | ~~Çıkarım arka ucu kararı~~ → **ÖLÇÜLDÜ 6 Eylül (D-431)**: `torch.cuda.is_available()` **True** (`cuda_adi: Orin`, torch 2.11.0+cu130); **uçuş `.pt` GPU ile** (kayıt defteri `path` `.pt`, FPS kapısı geçiyor). TensorRT `.engine` derlendi ve deftere kaydedildi ama engine↔pt denkliği D-303 oransal **3/126 DÜŞTÜ** → üretime alınmadı (§3 kalem 15). ONNX GPU: `onnxruntime-gpu` 1.29 sm_87 çekirdeği yok (**HATA**) → ONNX yolu bu kartta **DOĞRULANMAMIŞ** | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` (`ortam`, `vakalar[onnx].sebep`) | 3 |
| 6 | SiK 433 MHz RTT ve paket kaybı | `scripts/sik_rf_olc.py`; DDR'deki ">%98, 300 m" iddiasının kanıtı **yok** | 3, 4, 7 |
| 7 | ArduCopter sürümü, kalibrasyon çıktıları, pervanesiz motor testi | Mission Planner; sahada okunan parametre dökümü repoya işlenir → **KISMEN KAPANDI:** sürüm `ArduCopter V4.5.7 (2a3dc4b7)` ÖLÇÜM (D-426 §1); accel/level ve pusula ofsetleri 6 Eylül dökümünde (D-428 §1); ESC kalibrasyonu 6 Eylül'de başarılı yordamla yapıldı (D-428 §3, beyan); motor testi 4/4 **BEYAN**, video yok; döküm `config/pixhawk/arducopter_fda_20260906.param` (D-428 §5g); **10 Eylül:** kalibrasyon çıktıları §4.6'da dosya:satır tablosu (accel/gyro/level/Mag1/Mag2), 2. pusula kalibrasyonu dökümü ve MP ekran görüntüsü açık; RC failsafe ÖLÇÜLDÜ ve **DÜŞTÜ** (D-428 §2, §4.12) | 3, 5, 6 |
| 8 | Uçuş kontrolcüsü parametrelerinin **sahada okunan** hâli | `config/pixhawk/arducopter_fda_20260905.param` (bugün yok, cumartesi üretilir) → **AÇIK (5 Eylül akşamı, D-426 §4): dosya YOK** — `config/pixhawk/README.md` §1 adım 6 (`Full Parameter List` → `Save to file`) sahada yapılmadı. Döküm alındığında bakılacak: `RC_PROTOCOLS` sahada 4 → 1 yapıldı ve geri alınmadı (D-426 §2); `BRD_SAFETY_DEFOFF` değiştirilmedi. Bu satır kapanmadan Bölüm 2/5/6'daki döküm atıfları açık kalır → **KISMEN KAPANDI (6 Eylül 20:22, D-428 §5g; 10 Eylül işlendi):** `config/pixhawk/arducopter_fda_20260906.param` repoda (5 Eylül dökümü hiç alınmadı, ad bu yüzden 06); `RC_PROTOCOLS,1` (:658), `FS_THR_ENABLE,3` (:411) ve `BATT_FS_LOW_ACT,1` (:134) şablondan sapmış (D-428 §5b), `RC_SPEED,490` (:659), boş çıkışlarda motor fonksiyonu (D-428 §5d); 2. pusula kalibrasyonu ve `FS_GCS_ENABLE` (tlog sonu 5) dökümde yok → **üçüncü döküm açık** | 2, 5, 6 |

## 2. 6–19 Eylül uçuş testleri — ölçümle kapanır

| # | kalem | nasıl kapanır |
|---|---|---|
| 9 | Titreşim, ~~pusula ofseti, GPS kalitesi~~ | ilk hover logu (`VIBE`, EKF, HDOP) → **10 Eylül:** pusula ofseti 6 Eylül dökümünde **ÖLÇÜLDÜ** (Mag1 15,4 / Mag2 129,5 < 300, §4.6); GPS 18 uydu + `EKF3 IMU0/IMU1 is using GPS` (D-428 §1, yapıştırılan satır; HDOP kaydı yok); **titreşim (`VIBE`) hâlâ açık** — hover yok, DataFlash `.bin` indirilmedi (D-429 §5) |
| 10 | İniş kanıtı canlı zinciri | `iha_inis_yayinci` → YKS'de IHA_LANDED ACK'li |
| 11 | Uçtan uca görev süresi (≤ 10 dk) | üç tam prova, video + hakem log |
| 12 | Asılı kalma akımı, tepe akım, gerçek uçuş süresi | PM02 telemetrisi (Bölüm 7 batarya hesabı bunu ister) |
| 13 | Adıyaman test alanının **gerçek koordinatları** | görev planı bugün yer tutucudur |

## 3. Kapanmayacak sınır — raporda böyle yazılır

| # | kalem | neden kapanmıyor |
|---|---|---|
| 14 | **Gerçek arena karesi yok** | Kırmızı H brandası + moloz + bariyer içeren, ≥30 m irtifadan çekilmiş görüntümüz hiç olmadı. Kabul kapılarının tamamı sentetik kümede koşuldu; rapor bunu her bölümde tekrar eder ve saha başarımı **iddia etmez**. |
| 15 | TensorRT `.engine` denkliği | ~~Nano 4GB'de 21 Eylül için derlenmesi planlanmıyor; PT/ONNX ile uçulacak, `.engine` **ÖLÇÜLEMEDİ** kalır~~ → **6 Eylül (D-431):** Orin Nano'da FP16 engine derlendi ve **ÖLÇÜLDÜ** (p50/p95 1,58/1,33 FPS) ama D-303 karar denkliği **3/126 DÜŞTÜ** (eşik 1/52) → uçuş `.pt` (GPU) ile; kalem "ölçülemedi" değil "denklik düştü" olarak sınırda kalır — `results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json` |
| ~~16~~ | ~~Gazebo fiziksel temas koşusu — kapanmayacak sınır~~ → 🔴 **YENİDEN AÇILDI (3 Eylül, D-417).** Yönerge `Y-3.3.3` ve `Y-4-M07` **3B görev icra simülasyonunu PUANLANAN bir gereksinim** yapıyor: İHA ve İKA'nın CAD modelleriyle sanal görev icrası + başarı oranları + grafikler + **video linki**. "Simülasyon saha kanıtı değildir" doğru ama **yönerge saha kanıtı olarak istemiyor**, ayrı bir çıktı olarak istiyor. Kapanmaz sayılamaz → **10 Eylül 2026 (T214-A/B): MuJoCo'da koşuldu** (SENTETİK; Gazebo önceki tasarım, koşulmadı): 105 koşum, 4 grafik, HUD'lu video (yerel); H1-K5 YER GERÇEĞİ 45/45 GEÇTİ, ÜRETİM MODELİ 9/45 **DÜŞTÜ**; H1-K3 6/15 · 1/15 **DÜŞTÜ** (`BOLUM_3` §3.3.3). **Açık:** video linki (insan, T222) — kalem 30 |

## 4. İnsan beyanı — rapor teslimine kadar (ÖLÇÜM DEĞİL, BİLGİ)

| # | kalem | kim | bölüm |
|---|---|---|---|
| ~~17~~ | ~~Ekip isimleri ve rol ataması~~ → **KALEM DÜŞTÜ (3 Eylül, D-417).** Yönerge Bölüm 2.1 kişisel veriyi (isim, görsel) **yasaklıyor**: *"tamamen rol bazlı"*. Rapor zaten rol bazlı yazılmıştı — **gereksinim karşılanmış durumda** (`Y-2.1-M02`). Bu satır bir eksik değil, bir **yanlış anlamaydı** | — | 2 |
| 18 | **Birim fiyatlar, tedarik durumu, fatura/teklif kayıtları** | kaptan | 7 |
| 19 | 3B baskı süreleri, filament tüketimi, ölçülen parça kütleleri | üretim | 5 |
| 20 | Üretim zorlukları, revizyon gerekçeleri (SGGS de ister) | üretim | 5 |
| 21 | Yarışma günü aracının (sabit kanat + mancınık + paraşüt) ve İKA'nın nihai mekanik künyesi | kaptan | 3, 5, 7 |
| 22 | Montaj/entegrasyon fotoğrafları ve otonom harekât videoları | herkes | 4, 5 |


## 4b. Yazılım — kod kilidi/damga eksikleri (ÖLÇÜM, insan girdisi değil)

> Bunlar saha ölçümü beklemez; bugün yazılabilir ama **yazılmadı** ve
> yazılmış gibi de gösterilmedi. Her biri bir kaydın tam kapanmasını engeller.
>
> **5 Eylül durumu:** üçü de yazıldı (D-419 birleştirmesi, 4 Eylül) ve koda
> karşı doğrulandı; kapılar bu tur koşuldu: `test_seri_pixhawk_kilidi` 13/13 ·
> `test_p5_h1c_damgasi` 23/23 · `test_yks_hakem_kanit_olaylari` 22/22 ·
> `test_yks_hakem_kanit_yolu` 6/6. Satırlar aşağıda kapanış kanıtıyla durur.

| # | kalem | neden açık | bölüm |
|---|---|---|---|
| ~~23~~ | ~~**Tek-yazar kilidinin koda genişletilmesi** — `rpi_inference` ve `iha_inis_yayinci` bugün `--mavlink /dev/tty*` kabul eder; kural yalnız `iha_komut_alici`'da kodludur, diğer ikisinde yordamla uygulanır~~ → **KAPANDI (D-419 §3–4, `wf_b0f33806-4ba-1`).** Üç süreç aynı kilidi `comms/inis_kaniti.py:101-140`'tan okur (`seri_pixhawk_bayragini_ekle` / `seri_pixhawk_kilidini_uygula`): `codes/rpi_inference.py:2539,2684` · `comms/iha_inis_yayinci.py:432,475` · `comms/iha_komut_alici.py:855,899`. `/dev/tty*`, `COM*`, `serial:` → `parser.error` çıkış 2, tek red metni; yalnız `--seri-pixhawk-bilerek` aşar; `iha_inis_yayinci` kılavuzu artık `udp:127.0.0.1:14551` gösterir. `iha_komut_alici --serial` de reddedilir (`iha_komut_alici.py:891`, D-421 §1). Kapı `tests/test_seri_pixhawk_kilidi.py` **13/13** | yazılım | 3 |
| ~~24~~ | ~~**H1c damgası** — ön kayıttaki "sınıflandırılamayan yayımlanmış çevrilme = 0" ölçütü koşulmadı; H1 ön kaydı bu yüzden tam kapanmış sayılmaz (H1 kendisi DÜŞTÜ, eşik gevşetilmedi)~~ → **KAPANDI (D-419 §3, `wf_b0f33806-4ba-4`).** Ölçüt aynı model/küme/tohumla (7, 42; σ=2; kare başına 4 kopya) koşuldu: sınıflandırılamayan yayımlanmış çevrilme **0/0**, sınıflar yayımlananı tam örter (tohum 7: (i) 6 + (ii) 1 = 7 · tohum 42: (i) 9 + (ii) 2 = 11; (iii) hiç oluşmadı) — `results/p5_histerezis/ON_KAYIT.md` "H1c — KOŞULDU", `olcum_20260903.json` (`H1c: true`), ikinci koşum `olcum_h1c_tekrar_20260903.json` (ham 13/24, yayımlanan 7/11 birebir). H1 %40 hükmü **DÜŞTÜ** kalır (`H1_ozgun: false`); eşik ve K değişmedi. Kapı `tests/test_p5_h1c_damgasi.py` **23/23** (GPU'suz çekirdek + 2 mutasyon testi) | yazılım | 3 |
| ~~25~~ | ~~**Hakem kanıt kaydının olay kümesi** — `YksArayuz` bugün yalnız `YKS_ARAYUZ_HAZIR` satırını yazar. `_kamera_kanit_durumu`, `_son_kamera_kanit_monotonic`, `_son_telemetri_kanit_monotonic` alanları kuruluyor ama **hiçbir yerde okunmuyor**; kamera ve telemetri kanıt olayları yazılmıyor. Olay kümesi sözleşmesi (`CONTRACTS`) yazılmadan uydurulmadı~~ → **KAPANDI (D-412 + D-419 §2, `wf_dce95c66-485`).** `CONTRACTS.md` §6.8 yazıldı (16 olay / ne zaman yazılır / zorunlu alanlar); `comms/yks_gui.py:127` `KANIT_OLAYLARI` **16 olay**; kamera/telemetri alanları artık `_kanit_durumu_yaz` tarafından okunur (`yks_gui.py:2610`, `:3980`) — `KAMERA_KANIT`/`TELEMETRI_KANIT` kenar olayı + 30 s tekrar (`KANIT_TEKRAR_ARALIGI_S`, fsync yükü kapandı). Kapılar: `tests/test_yks_hakem_kanit_olaylari.py` **22/22** (sözleşme ↔ sabit ↔ AST üç yönlü küme eşitliği, gerçek `HakemKaydi` ile diske yazım, 6 mutasyon yakalandı — D-419 §2) · `tests/test_yks_hakem_kanit_yolu.py` **6/6** (D-412). Uçtan uca `--demo --fda`: `hakem_log.jsonl` 18 satır / 9 farklı olay (D-419 §2) | yazılım | 3, 4 |

## 5. Rapor içi iş — bölümler kesinleşince

- **Bölüm 1 (Özet)** diğer altı bölüm sabitlendikten sonra son hâlini alır; bugünkü
  hâli taslaktır.
- **Bölüm 3 ile Bölüm 5/7 tutarlılığı:** donanım revizyon tablosu (Orin NX → ~~Nano 4GB~~ **Orin Nano Developer Kit 4 GB** (6 Eylül ölçüm, D-431),
  6X → 6C, M10 → M9N, Crossfire → FS-i6) üç bölümde de **aynı** olmalı; teslimden önce
  tek kaynaktan doğrulanır.
- **Denetim borcu:** FDA kipi sözleşmesini (§6.7) yazan ile uygulayan aynı el; bağımsız
  denetim ya Fable 5 döndüğünde ya da 21 Eylül öncesi provada hakem rolü oynanarak
  kapanır (D-408).

---

## 6. YÖNERGEDEN GELEN YENİ AÇIK KALEMLER (3 Eylül 2026, D-417)

> Resmî yönerge (`FDR_2_qNiVF.pdf`) 3 Eylül'de okundu. Rapor yapısı ona
> taşındı; aşağıdakiler o taşımada **açığa çıkan** kalemlerdir. Tam liste ve
> kimlikler: `YONERGE_HARITASI.md`.

| # | kalem | yönerge kimliği | kim üretir | bölüm |
|---|---|---|---|---|
| 26 | **Uçuş bilimleri hiç yazılmadı** — ağırlık & denge, boyut, kontrol yüzeyi, aerodinamik, kararlılık, performans, yük hesapları (DDR sonrası güncellemeler) | `Y-3.1.1…3.1.7` | tasarım / CAD | 3 |
| 27 | **İHA yapısal analiz yok** — malzeme dayanım tablosu (fiyat/performans dâhil), topoloji optimizasyonu, modal frekans + kütle katılım, burkulma özdeğerleri, tork/menteşe analizleri | `Y-3.2.1-A01…A12` | yapısal analiz | 3 |
| 28 | **İKA yapısal bölümü yok** — master geometri, parça numaralandırma + BOM, kütle dağılımı, malzeme gerekçesi, yük bırakma sistemi optimizasyonu | `Y-3.2.2-T01…T11`, `A01…A03` | tasarım | 3 |
| 29 | **Mancınık yapısal bölümü yok** — aynı liste + **yay sabiti** ve **fırlatma menzilinin enerji denklemleriyle** açıklanması + şematik | `Y-3.2.3-T01…T11`, `A01…A02` | tasarım | 3 |
| 30 | **Üç boyutlu görev icra simülasyonu** — 3B ortam + başarı oranları/grafikler + **video linki** → **KISMEN KAPANDI (10 Eylül 2026, T214-A/B):** 3B ortam MuJoCo (BASİTLEŞTİRİLMİŞ modeller, İHA kinematik), başarı oranları + 4 grafik (`BOLUM_3` §3.3.3.2), HUD'lu video yerelde (`results/fdr_sprint_20260910/video/OKUBENI.md`, sha256 `35ffc33e2f99c833…`); kalan: **video linki — BEYAN GEREKLİ (insan)**, T222; ekip CAD STL'i (insan girdisi) | `Y-3.3.3-M01…M03`, `Y-4-M07` | ~~yazılım / simülasyon~~ yazılım (yapıldı) · link insan (T222) | 3, 4 |
| 31 | **Renk kodlu bağlantı şemaları** — İHA ve İKA için ayrı ayrı, sinyal (PWM/UART/I2C) ve güç hatları ayrı renkte → **KISMEN KAPANDI:** İHA şeması 7 Eylül (ölçülen topoloji, 6 hat DOĞRULANACAK), İKA şeması 10 Eylül (T217, **DDR tasarımından**, 16/16 hat "tedarik yok", ölçülmüş 0 — `BOLUM_3` §3.3.1.1); kalan: İKA hatlarının ölçümü (tedarikle), SiK bağlanma noktası kararı (K13) | `Y-3.3.1-M01` | ~~aviyonik~~ çizim mimar (10 Eylül) · ölçüm aviyonik (tedarikle) | 3 |
| 32 | **Nihai kablaj hesapları** — AWG kesitleri, uzunluklar, akım taşıma, gerilim düşümü; **ölçülen** maks. akıma göre güncelleme; ekranlama/konnektör kilitleme görselleri | `Y-3.3.2-M01` | aviyonik | 3 |
| 33 | **Güç tüketimi doğrulaması** — tam yükte ölçülen akım ↔ batarya kapasitesi; teorik ↔ pratik karşılaştırma | `Y-3.3.2-M02` | aviyonik (5 Eylül) | 3 |
| 34 | **Ekipman kabul testleri** — İHA ve İKA'daki **tüm** ekipmanlar | `Y-4-M04` | aviyonik (5 Eylül) | 4 |
| 35 | **Kumanda ve telemetri menzil testleri** — sahada | `Y-4-M05` | pilot + aviyonik | 4 |
| 36 | **IMU / pusula / pitot kalibrasyon kanıtları** → **KISMEN KAPANDI (6 Eylül dökümü, 10 Eylül işlendi):** §4.6 ofset tablosu dosya:satır ile; pitot kapsam dışı (`ARSPD_ENABLE,0`); kalan: MP ekran görüntüsü, 2. pusula kalibrasyonu dökümü, Jetson takılı kalibrasyon | `Y-4-M06` | ~~aviyonik (5 Eylül)~~ aviyonik (6 Eylül ÖLÇÜLDÜ; üçüncü döküm bekliyor) | 4 |
| 37 | 🔴 **Arıza emniyet doğrulaması sahada** — eve dönüş, motor kesme tepkilerinin gerçek test verisi → **AÇIK (10 Eylül):** RC failsafe 6 Eylül'de tezgâhta ÖLÇÜLDÜ ve **DÜŞTÜ** (alıcı son değeri tutuyor, D-428 §2); düzeltme kumanda failsafe ayarı + tekrar ölçüm (kayıt yok); RTL/Land/geofence/motor kesme sahada hiç tetiklenmedi → "sahada" şartı **karşılanmadı** (§4.12) | `Y-4-M12` | ~~pilot (6–19 Eylül)~~ pilot (uçuş öncesi; ilk hover D-429 §5 muayenesi sonrası) | 4 |
| 38 | **Sensör gereksinimleri, yerleşimleri, test takvimi, test zaman bütçesi** | `Y-4-M03` | yazılım + aviyonik | 4 |
| 39 | **Üretim hataları ve düzeltici işlem prosedürleri** | `Y-5-M04` | üretim | 5 |
| 40 | 🔴 **Kol 1–2 / kol 3–4 reçete farkının gerekçesi** — yönerge: *"gerekliliği ispatlanmamış değişiklikler **diskalifiye sebebi** sayılabilecektir"* (SGGS tutarlılık kontrolü, Şubat 2027) | `Y-5-M05` | üretim | 5 |
| 41 | **Gereksinim uygunluk pasta grafiği / özet görsel** | `Y-6-M06` | mimar (dizgide) | 6 |
| 42 | **Planlanan ↔ gerçekleşen maliyet karşılaştırması**, bütçe dağılımı (%+sayısal), harcanmamış bütçe planı, fark gerekçesi | `Y-7-M02…M05` | kaptan | 7 |
| 43 | **Kapak alanlarının KYS teyidi** — takım adı / takım ID / **başvuru ID** | `Y-0-M01` | kaptan | 0 |
| 44 | **Organizasyon şeması** — icra yetkilerini gösteren şema (isimsiz, rol bazlı) | `Y-2.1-M01` | kaptan | 2 |

⚠ **26–29 ve 31 bir beyanla kapanmaz.** Bunlar **üretilecek mühendislik
çıktısıdır** (CAD, FEA, şema). Takvim açısından en riskli grup budur: 21 Eylül'e
kadar üretilemezse ilgili satırlar `ÖLÇÜLEMEDİ` olarak teslim edilir ve
40 puanlık bölümde puan kaybı olur.

