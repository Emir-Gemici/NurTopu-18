# FDR — AÇIK KALEMLER (kim · ne zaman · nasıl kapanır)

> Taslakta **188 satır** "BEYAN GEREKLİ" ya da "ÖLÇÜLEMEDİ" ile işaretli
> (ham liste: `ACIK_KALEMLER_HAM.md`). Bunlar eksiklik değil, **dürüstlük
> işaretidir**: rapor ölçülmemiş bir şeyi ölçülmüş gibi yazmaz. Aşağıda
> sahibine ve kapanma tarihine göre gruplanmış hâli var.
>
> Sıralama kapanma tarihine göredir; en üsttekiler rapor teslimini bekletir.

## 1. Cumartesi 5 Eylül — donanım geldiği gün kapanır (ÖLÇÜM)

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
| 16 | Gazebo fiziksel temas koşusu | Gazebo'lu makine yok; simülasyon zaten saha kanıtı sayılmıyor |

## 4. İnsan beyanı — rapor teslimine kadar (ÖLÇÜM DEĞİL, BİLGİ)

| # | kalem | kim | bölüm |
|---|---|---|---|
| 17 | **Ekip isimleri ve rol ataması** (rapor rolle yazıldı, isim yok) | kaptan | 2 |
| 18 | **Birim fiyatlar, tedarik durumu, fatura/teklif kayıtları** | kaptan | 7 |
| 19 | 3B baskı süreleri, filament tüketimi, ölçülen parça kütleleri | üretim | 5 |
| 20 | Üretim zorlukları, revizyon gerekçeleri (SGGS de ister) | üretim | 5 |
| 21 | Yarışma günü aracının (sabit kanat + mancınık + paraşüt) ve İKA'nın nihai mekanik künyesi | kaptan | 3, 5, 7 |
| 22 | Montaj/entegrasyon fotoğrafları ve otonom harekât videoları | herkes | 4, 5 |

## 5. Rapor içi iş — bölümler kesinleşince

- **Bölüm 1 (Özet)** diğer altı bölüm sabitlendikten sonra son hâlini alır; bugünkü
  hâli taslaktır.
- **Bölüm 3 ile Bölüm 5/7 tutarlılığı:** donanım revizyon tablosu (Orin NX → Nano 4GB,
  6X → 6C, M10 → M9N, Crossfire → FS-i6) üç bölümde de **aynı** olmalı; teslimden önce
  tek kaynaktan doğrulanır.
- **Denetim borcu:** FDA kipi sözleşmesini (§6.7) yazan ile uygulayan aynı el; bağımsız
  denetim ya Fable 5 döndüğünde ya da 21 Eylül öncesi provada hakem rolü oynanarak
  kapanır (D-408).
