# FDR — AÇIK KALEMLER (kim · ne zaman · nasıl kapanır)

> Taslakta **197 satır** "BEYAN GEREKLİ" ya da "ÖLÇÜLEMEDİ" ile işaretli
> (ham liste: `ACIK_KALEMLER_HAM.md`). Bunlar eksiklik değil, **dürüstlük
> işaretidir**: rapor ölçülmemiş bir şeyi ölçülmüş gibi yazmaz. Aşağıda
> sahibine ve kapanma tarihine göre gruplanmış hâli var.
>
> Sıralama kapanma tarihine göredir; en üsttekiler rapor teslimini bekletir.

## 1. Cumartesi 5 Eylül — donanım geldiği gün kapanır (ÖLÇÜM)

⚠ **KOŞULSUZ DEĞİL.** Aşağıdaki kalemlerden **3, 4 ve 5 açılmış bir Jetson
gerektirir**. D-413'e göre kartta microSD yuvası yoktur (eMMC modül + M.2) ve
eMMC'nin **boş çıkma ihtimali vardır**; o durumda Ubuntu x86_64 host + SDK
Manager yolu (~20 GB indirme + NVIDIA hesabı + micro-USB) gerekir ve Jetson
cumartesi açılmayabilir. Ayrıca `python3.8` kurulumu **internet ister**
(`JETSON_NANO_KURULUM.md` §3.1).

Bu üç kalem için doğru okuma: **"Jetson açılırsa cumartesi kapanır; açılmazsa
`ÖLÇÜLEMEDİ` olarak taşınır."** Ölçülemeyen şey geçmiş sayılmaz.

| # | kalem | nasıl kapanır | bölüm |
|---|---|---|---|
| 1 | Kalkış kütlesi, ağırlık merkezi, **her parçanın gerçek tartısı** | tartı + tutanak; UHDR ve Bölüm 5/7 bunu ister | 3, 5, 7 |
| 2 | Kameranın **ölçülen** yatay görüş açısı | `codes/kamera_dogrula.py` (bugünkü 55–63° bir **lens hesabıdır**, ölçüm değil) | 3 |
| 3 | Gerçek Pixhawk üzerinde MAVLink akış kapısı | `scripts/mavlink_dogrula.py` üç uçta aynı anda: HEARTBEAT sysid · konum ≥ 4 Hz · iniş durumu ≥ 1 Hz | 3, 4, 6 |
| 4 | **Jetson Nano gerçek FPS** (p50/p95) | `scripts/jetson_fps.py`; kapı **0,61 FPS**, eşik gevşetilmez | 3, 4 |
| 5 | Çıkarım arka ucu kararı | `torch.cuda.is_available()` sonucu + seçilen yol (CUDA wheel / onnxruntime / CPU) | 3 |
| 6 | SiK 433 MHz RTT ve paket kaybı | `scripts/sik_rf_olc.py`; DDR'deki ">%98, 300 m" iddiasının kanıtı **yok** | 3, 4, 7 |
| 7 | ArduCopter sürümü, kalibrasyon çıktıları, pervanesiz motor testi | Mission Planner; sahada okunan parametre dökümü repoya işlenir | 3, 5, 6 |
| 8 | Uçuş kontrolcüsü parametrelerinin **sahada okunan** hâli | `config/pixhawk/arducopter_fda_20260905.param` (bugün yok, cumartesi üretilir) | 2, 5, 6 |

## 2. 6–19 Eylül uçuş testleri — ölçümle kapanır

| # | kalem | nasıl kapanır |
|---|---|---|
| 9 | Titreşim, pusula ofseti, GPS kalitesi | ilk hover logu (`VIBE`, EKF, HDOP) |
| 10 | İniş kanıtı canlı zinciri | `iha_inis_yayinci` → YKS'de IHA_LANDED ACK'li |
| 11 | Uçtan uca görev süresi (≤ 10 dk) | üç tam prova, video + hakem log |
| 12 | Asılı kalma akımı, tepe akım, gerçek uçuş süresi | PM02 telemetrisi (Bölüm 7 batarya hesabı bunu ister) |
| 13 | Adıyaman test alanının **gerçek koordinatları** | görev planı bugün yer tutucudur |

## 3. Kapanmayacak sınır — raporda böyle yazılır

| # | kalem | neden kapanmıyor |
|---|---|---|
| 14 | **Gerçek arena karesi yok** | Kırmızı H brandası + moloz + bariyer içeren, ≥30 m irtifadan çekilmiş görüntümüz hiç olmadı. Kabul kapılarının tamamı sentetik kümede koşuldu; rapor bunu her bölümde tekrar eder ve saha başarımı **iddia etmez**. |
| 15 | TensorRT `.engine` denkliği | Nano 4GB'de 21 Eylül için derlenmesi planlanmıyor; PT/ONNX ile uçulacak, `.engine` **ÖLÇÜLEMEDİ** kalır |
| ~~16~~ | ~~Gazebo fiziksel temas koşusu — kapanmayacak sınır~~ → 🔴 **YENİDEN AÇILDI (3 Eylül, D-417).** Yönerge `Y-3.3.3` ve `Y-4-M07` **3B görev icra simülasyonunu PUANLANAN bir gereksinim** yapıyor: İHA ve İKA'nın CAD modelleriyle sanal görev icrası + başarı oranları + grafikler + **video linki**. "Simülasyon saha kanıtı değildir" doğru ama **yönerge saha kanıtı olarak istemiyor**, ayrı bir çıktı olarak istiyor. Kapanmaz sayılamaz |

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

| # | kalem | neden açık | bölüm |
|---|---|---|---|
| 23 | **Tek-yazar kilidinin koda genişletilmesi** — `rpi_inference` ve `iha_inis_yayinci` bugün `--mavlink /dev/tty*` kabul eder; kural yalnız `iha_komut_alici`'da kodludur, diğer ikisinde yordamla uygulanır | yazılım | 3 |
| 24 | **H1c damgası** — ön kayıttaki "sınıflandırılamayan yayımlanmış çevrilme = 0" ölçütü koşulmadı; H1 ön kaydı bu yüzden tam kapanmış sayılmaz (H1 kendisi DÜŞTÜ, eşik gevşetilmedi) | yazılım | 3 |
| 25 | **Hakem kanıt kaydının olay kümesi** — `YksArayuz` bugün yalnız `YKS_ARAYUZ_HAZIR` satırını yazar. `_kamera_kanit_durumu`, `_son_kamera_kanit_monotonic`, `_son_telemetri_kanit_monotonic` alanları kuruluyor ama **hiçbir yerde okunmuyor**; kamera ve telemetri kanıt olayları yazılmıyor. Olay kümesi sözleşmesi (`CONTRACTS`) yazılmadan uydurulmadı | yazılım | 3, 4 |

## 5. Rapor içi iş — bölümler kesinleşince

- **Bölüm 1 (Özet)** diğer altı bölüm sabitlendikten sonra son hâlini alır; bugünkü
  hâli taslaktır.
- **Bölüm 3 ile Bölüm 5/7 tutarlılığı:** donanım revizyon tablosu (Orin NX → Nano 4GB,
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
| 30 | **Üç boyutlu görev icra simülasyonu** — 3B ortam + başarı oranları/grafikler + **video linki** | `Y-3.3.3-M01…M03`, `Y-4-M07` | yazılım / simülasyon | 3, 4 |
| 31 | **Renk kodlu bağlantı şemaları** — İHA ve İKA için ayrı ayrı, sinyal (PWM/UART/I2C) ve güç hatları ayrı renkte | `Y-3.3.1-M01` | aviyonik | 3 |
| 32 | **Nihai kablaj hesapları** — AWG kesitleri, uzunluklar, akım taşıma, gerilim düşümü; **ölçülen** maks. akıma göre güncelleme; ekranlama/konnektör kilitleme görselleri | `Y-3.3.2-M01` | aviyonik | 3 |
| 33 | **Güç tüketimi doğrulaması** — tam yükte ölçülen akım ↔ batarya kapasitesi; teorik ↔ pratik karşılaştırma | `Y-3.3.2-M02` | aviyonik (5 Eylül) | 3 |
| 34 | **Ekipman kabul testleri** — İHA ve İKA'daki **tüm** ekipmanlar | `Y-4-M04` | aviyonik (5 Eylül) | 4 |
| 35 | **Kumanda ve telemetri menzil testleri** — sahada | `Y-4-M05` | pilot + aviyonik | 4 |
| 36 | **IMU / pusula / pitot kalibrasyon kanıtları** | `Y-4-M06` | aviyonik (5 Eylül) | 4 |
| 37 | 🔴 **Arıza emniyet doğrulaması sahada** — eve dönüş, motor kesme tepkilerinin gerçek test verisi | `Y-4-M12` | pilot (6–19 Eylül) | 4 |
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

