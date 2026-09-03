# BÖLÜM 7 — Bütçe Gerçekleme Analizi (10 puan)

> **Bu bölümün yazım kuralı.** Bütçe gerçekleme, "ne planlandı / ne harcandı / fark neden"
> sorusunun sayılarla cevabıdır. Bu raporun kuralı gereği **var olmayan bir sayı uydurulmaz**.
> Aşağıda ölçülebilen her şey (kalem listesi, kütle, adet, malzeme tüketimi, hesaplama kaynağı,
> tedarik durumu) artefaktından çıkarılmış; **parasal sütunların tamamı BEYAN GEREKLİ (insan)**
> olarak bırakılmıştır. Gerekçesi §2'de ölçümle birlikte yazılıdır.

---

## 1. Kapsam ve yöntem

### 1.1 Şartnamenin bu bölümden ve SGGS'ten istedikleri

FDR Tablo 4, Bölüm 7'yi **"Bütçe Gerçekleme Analizi"** olarak tanımlar (10 puan).
Şartname §5.4 ise BOM'un **parça/sistem bazında** hangi bilgilerle sunulacağını sayar; bu
bölümdeki tabloların sütun başlıkları doğrudan o hükümden alınmıştır:

| şartname §5.4'ün istediği | tablo sütunu |
|---|---|
| *"üretilen veya satın alınan tüm parça, alt sistem ve **sarf kalemlerini** (ör. yapıştırıcı/bağlayıcı) isim, adet ve temel bilgilerle listeleyen resmî malzeme dökümü"* | Kalem · Model · Adet |
| *"üretim yöntemi"* | Üretim yöntemi |
| *"üretim süresi"* | Üretim süresi |
| *"CAD model kütlesi"* | CAD kütlesi (g) |
| *"üretim/teslim sonrası ölçülen gerçek kütle"* | Ölçülen kütle (g) |
| *"üretim için ilave fikstür/tool ihtiyacı"* | Fikstür/tool |
| *"karşılaşılan üretim zorlukları"* | Üretim zorluğu |
| *"hazır satın alınan alt sistemlerde **tedarik durumu** (alındı / sipariş edildi / henüz aksiyon alınmadı)"* | Tedarik durumu |
| *"satın alınan kalemlerin **ağırlık ve boyut** bilgileri"* | Kütle / Boyut |

Şartname §5.4 ayrıca sunumun **"Başarılı / Başarısız"** ile değerlendirileceğini, ayrıca
puanlanmayacağını belirtir; SGGS son teslim tarihi **05.02.2027**'dir. Bu bölümdeki tablolar,
o sunumun BOM iskeletini şimdiden kurar.

### 1.2 Maddi destek dilimleri (şartname)

- DDR sonrası başarılı bulunan ve maddi destek başvurusu yapmış takımlar toplam bütçenin **%25**'ini,
- FDA sonrası başarılı bulunanlar **%75**'ini almaya hak kazanır (§5.2, §5.3).
- Başvuru **zorunlu değildir**; form KYS üzerinden iletilir, tarih Yarışmalar Komitesince belirlenir.

**BEYAN GEREKLİ (insan): takımın maddi destek başvurusu yapıp yapmadığı, onaylanan toplam bütçe
tutarı ve bugüne kadar alınan dilim(ler).** Bu üç bilgi olmadan "gerçekleme oranı" hesaplanamaz.

---

## 2. 🔴 Ölçüm: depoda parasal veri yoktur

Bu bölümün en dürüst cümlesi bir ölçümdür. Proje deposunun tamamı, Markdown/JSON/CSV
dosyaları üzerinde fiyat, fatura ve sipariş kaydı için tarandı:

```
grep -rInE "₺|fatura|birim fiyat|sipariş no" --include="*.md" --include="*.json" --include="*.csv" .
→  FDR/ klasörü dışında 0 eşleşme          (2026-09-03)
```

Yani proje **teknik kanıt açısından zengin, mali kayıt açısından boştur**: tek bir birim fiyat,
tek bir fatura numarası, tek bir sipariş kaydı depoda yoktur. Bu durumda iki seçenek vardı —
piyasa fiyatı "tahmin edip" tablo doldurmak ya da sütunları boş bırakıp kimin dolduracağını
yazmak. **İkincisi seçilmiştir.** Tahmini fiyat, bütçe gerçekleme analizi değildir; gerçekleme
ancak gerçek harcamayla ölçülür.

---

## 3. Tablo A — FDA görev test uçuşu aracı (çoklu rotor) BOM'u

Kalem listesi kullanıcı beyanından (`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül 2026);
tedarik durumu 03.09.2026 itibarıyladır ve **5 Eylül kutu açılışında teyit edilecektir**.
`Ü` = takım üretimi, `S` = hazır satın alınan alt sistem.

| # | Kalem | Model / özellik | Adet | Tür | Üretim yöntemi | Üretim süresi | CAD kütlesi (g) | Ölçülen kütle (g) | Tedarik durumu | Birim fiyat |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Kol | `Drone_Arm` (ABS) | 4 | Ü | FDM 3B baskı — bkz. Bölüm 5 §4.1 (kol 1–2 ve 3–4 **farklı reçete**) | **ÖLÇÜLEMEDİ** (G-code yok) | BEYAN GEREKLİ | BEYAN GEREKLİ (5 Eyl tartı) | Üretildi | BEYAN GEREKLİ |
| A2 | Üst çerçeve | `Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid / 2 duvar | **1 sa 30 dk 16 sn** (ölçüldü) | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A3 | Alt çerçeve | `Lower_Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A4 | Kubbe | `Drone_Dome` (ABS, **destekli**) | 1 | Ü | FDM, X1C | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A5 | Ayak | `Drone_Legs` (ABS, **destekli**) | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A6 | GNSS tutucu | `GPS_Holder` (ABS, **destekli**) | 1 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A7 | Taban pedi | TPU 95A | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
| A8 | Motor | **5008 340KV** | 4 | S | — | — | — | BEYAN GEREKLİ | **Kutuda** (kutu açılmadı) | BEYAN GEREKLİ |
| A9 | Pervane | **12×10** | 4 (+ yedek set) | S | — | — | — | BEYAN GEREKLİ | Kutuda; **yedek set alınacak** | BEYAN GEREKLİ |
| A10 | ESC | **80 A, DShot destekli** | 4 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
| A11 | Güç dağıtım kartı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
| A12 | Uçuş kontrolcüsü | **Pixhawk 6C** | 1 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 59 g) | Kutuda | BEYAN GEREKLİ |
| A13 | Güç modülü | **PM02** (Pixhawk kutusundan) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
| A14 | GNSS / pusula | **Holybro M9N** | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de M10 için 32 g) | Kutuda | BEYAN GEREKLİ |
| A15 | RC kumanda + alıcı | **FlySky FS-i6** + FS-iA6B (iBUS) | 1 set | S | — | — | — | BEYAN GEREKLİ | Kutuda; **bind edilmedi** | BEYAN GEREKLİ |
| A16 | Telemetri | **SiK 433 MHz** | 2 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 35 g/adet) | Kutuda | BEYAN GEREKLİ |
| A17 | Görev bilgisayarı | **Jetson Nano 4GB** (Dev Kit) | 1 | S | — | — | — | BEYAN GEREKLİ | **Kargoda — 4/5 Eylül teslim** | BEYAN GEREKLİ |
| A18 | microSD | ≥ 64 GB UHS-I + okuyucu | 1 | S | — | — | — | — | **Henüz alınmadı** (alışveriş listesi) | BEYAN GEREKLİ |
| A19 | Kamera | **Raspberry Pi HQ** (IMX477, CSI) + standart lens | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de Arducam için 50 g) | Kutuda; **FOV ölçülmedi** | BEYAN GEREKLİ |
| A20 | Jetson besleme | **UBEC 5 V / 5 A** | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ |
| A21 | Pil | **4S 10 Ah 25C** | 1 (2. pil öneri) | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
| A22 | Şarj cihazı | **iMAX B6** (50 W) | 1 | S | — | — | — | — | Mevcut | BEYAN GEREKLİ |
| A23 | Kablolama demeti | XT60/XT90, JST-GH 6-pin, jumper, silikon kablo | lot | Ü | Kesim + lehim + makaron + etiket | BEYAN GEREKLİ | — | BEYAN GEREKLİ | Kısmen kutuda, kısmen **alınacak** | BEYAN GEREKLİ |
| A24 | Sarf | kablo bağı, ısı makaronu, çift taraflı bant/damper, vida-somun-pul | lot | S | — | — | — | BEYAN GEREKLİ | **Henüz alınmadı** | BEYAN GEREKLİ |
| A25 | Yedek kamera | USB webcam (UVC) | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ |
| A26 | Filament | ABS (X1C + P2S profilleri) | BEYAN GEREKLİ (kg) | S | — | — | — | ölçülen tüketim: **≥ 55,86 g** (yalnız A2 için) | Mevcut | BEYAN GEREKLİ |
| A27 | Filament | TPU 95A | BEYAN GEREKLİ (kg) | S | — | — | — | **ÖLÇÜLEMEDİ** | Mevcut | BEYAN GEREKLİ |
| — | **TOPLAM** | | | | | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | | **BEYAN GEREKLİ** |

⚠ **Kütle toplamı bilerek boştur.** Şartname §6 İHA için 25 kg, İKA için 10 kg sınırı koyar; bu
sınırın karşılandığı **ancak tartılmış kütlelerle** iddia edilebilir. 5 Eylül envanterinde her
parça tartılacak (`SAHA_HAZIRLIK_PLANI` §2.1) ve bu sütun o tutanaktan doldurulacaktır.

⚠ **Boyut sütunu** bu tabloda yer almamaktadır; satın alınan kalemlerin gabarileri
**BEYAN GEREKLİ (insan)** — üretici veri sayfalarından toplanacaktır. Üretilen parçaların
gabarileri **ölçülmüştür** ve Bölüm 5 §3'tedir.

---

## 4. Tablo B — DDR aviyonik BOM'u ve bugünkü durumu

DDR'de beyan edilen 27 kalemlik aviyonik BOM (toplam **2293 g**) sabit kanat konfigürasyonu
içindir. Aşağıda her satırın FDR'deki karşılığı ve bütçeye etkisinin **yönü** verilmiştir
(tutarlar BEYAN GEREKLİ).

| No | DDR kalemi | Model (DDR) | Adet | Ağırlık (g) | FDR'deki durum | Bütçe etkisinin yönü |
|---|---|---|---|---|---|---|
| 1 | Autopilot | Pixhawk 6C | 1 | 59 | **Değişmedi** (A12) | — |
| 2 | İşlemci | Jetson **Orin NX** + carrier + soğutucu | 1 | 180 | **Jetson Nano 4GB** ile değişti (A17) | **azaltıcı** (Nano çok daha ucuz); teknik bedeli §6'da |
| 3 | Kamera | **Arducam** IMX477 12MP | 1 | 50 | **RPi HQ** (aynı sensör) (A19) | nötr/azaltıcı |
| 4 | Pitot tüpü | Pitot + hortum | 1 | 10 | FDA aracında **yok**; finalde kalır | ertelendi |
| 5 | Airspeed | Holybro MS5525DSO | 1 | 20 | FDA aracında **yok**; finalde kalır | ertelendi |
| 6 | Telemetri (uçak) | Holybro SiK 433 | 1 | 35 | **Değişmedi** (A16) | — |
| 7 | GNSS | Holybro **M10** + pusula | 1 | 32 | **M9N** ile değişti (A14) | azaltıcı |
| 8 | RC alıcı | **TBS Crossfire** Nano RX | 1 | 10 | **FlySky FS-i6 / FS-iA6B (iBUS)** (A15) | **azaltıcı** |
| 9 | Motor | SunnySky X2216 1100KV | 2 | 138 | FDA aracında **5008 340KV ×4** (A8) | **artırıcı** (4 adet, daha büyük) |
| 10 | Servo (kanat/kuyruk) | EMAX ES08MA II | 4 | 48 | FDA aracında **yok**; finalde kalır | ertelendi |
| 11 | Pil | 4S 14–15 Ah Li-ion | 1 | 1000 | **4S 10 Ah 25C LiPo** (A21) | azaltıcı |
| 12 | Paraşüt | Opale Rescue 2,5 m² | 1 | 120 | FDA'da **yok**; finalde zorunlu (§6) | ertelendi |
| 13 | Paraşüt pod | Rescue Pod | 1 | 20 | aynı | ertelendi |
| 14 | Paraşüt servo | EMAX ES08MA II | 1 | 60 | aynı | ertelendi |
| 15 | Paraşüt mekanizması | Servo kontrollü kapak | 1 | 50 | aynı — **üretim gerekiyor** | ertelendi |
| 16 | Paraşüt bağlantı | Nylon/Kevlar tether | 1 | 30 | aynı | ertelendi |
| 17 | ESC | Hobbywing FlyFun 40A V5 | 2 | 70 | **80 A DShot ×4** (A10) | **artırıcı** |
| 18 | Power sensor | **Mauch PL-100** | 1 | 22 | **PM02** ile değişti (A13) | azaltıcı |
| 19 | Pixhawk BEC | Mauch PL 4-6S BEC | 1 | 24 | **FCHUB-12S / PM02** karşılıyor | azaltıcı |
| 20 | Servo BEC | Matek BEC12S-PRO | 1 | 5 | FDA'da **yok** | ertelendi |
| 21 | Jetson güç reg. | 12 V 5 A buck | 1 | 25 | **5 V / 5 A UBEC** (A20) | nötr |
| 22 | PDB | Güç dağıtım kartı | 1 | 60 | **Matek XCLASS FCHUB-12S V2** (A11) | nötr/artırıcı |
| 23 | Kablolama | XT60/XT90, JST-GH vb. | lot | 150 | **Değişmedi** (A23) | — |
| 24 | Acil kesme şalterleri | Anahtarlı stop + röle | 1 | 30 | 🔴 **FDA aracında YOK** — pil fişi kullanılıyor | **açık borç** (final için satın alma gerekir) |
| 26 | Telemetri (YKS) | Holybro SiK 433 | 1 | 35 | **Değişmedi** (A16) | — |
| 27 | Jetson SSD | NVMe M.2 250 GB | 1 | 10 | Nano'da **NVMe yok** → microSD (A18) | azaltıcı |
| | **DDR beyan toplamı** | | | **2293** | FDA aracının kütlesi **ÖLÇÜLEMEDİ** | |

⚠ DDR belgesinin kendi içinde bir tutarsızlığı vardır: BOM "Pixhawk 6C" derken aynı dönemin
mimari şeması (`navitas-teknofest/references/avionics_software.md`) "Pixhawk 6X" yazar. Gerçek donanım **6C**'dir;
tutarsızlık burada kapanır.

---

## 5. Tablo C — Üretim (3B baskı) maliyeti ve kaynak tüketimi

| kalem | ölçülen | kaynak |
|---|---|---|
| Basılan plaka sayısı | **8** (kol ×2 plaka, alt çerçeve, üst çerçeve, kubbe, ayak, GPS tutucu+ayak, TPU ped) | `dronesolid/files (3)/*.3mf` |
| Kullanılan yazıcı | **Bambu Lab X1 Carbon** (0,4 nozül) ve **Bambu Lab P2S** (0,4 nozül) | plaka proje ayarları |
| Kullanılan dilimleyici | Bambu Studio **02.07.01.62** | `slice_info.config` |
| Malzemeler | **ABS** (7 plaka) + **TPU 95A** (1 plaka) | `filament_type` alanları |
| Ölçülen filament tüketimi | **55,86 g / 22,33 m** — yalnız üst çerçeve plakası | `Plaka4_Ust_Cerceve_plate_1.gcode.3mf` |
| Ölçülen baskı süresi | **1 sa 30 dk 16 sn** — yalnız üst çerçeve plakası | aynı |
| Diğer 7 plakanın süresi/tüketimi | **ÖLÇÜLEMEDİ** (dilimlenmiş G-code depoda yok) | — |
| Toplam filament kütlesi | **HESAPLANAMAZ** — tahmin yazılmadı | — |
| Yazıcı amortismanı / kWh | **BEYAN GEREKLİ (insan)** | — |
| Fire / yeniden basım | **BEYAN GEREKLİ (insan)** | — |

**Not (Bölüm 5 §4.3'e bağlı):** dilimleyici projeleri düz **ABS** gösterir, kullanıcı beyanı
**ABS-CF** der. ABS-CF filament fiyatı düz ABS'nin belirgin üstündedir; bu yüzden malzeme
maliyeti satırı, §4.3'teki çelişki çözülmeden doldurulamaz.
**BEYAN GEREKLİ (insan): kullanılan filamentin cinsi, makara adedi ve makara fiyatı.**

---

## 6. Tablo D — Tedarik listesi (alınacaklar) ve gerekçeleri

Aşağıdaki kalemler 4 Eylül'e kadar alınacaktır; her satırın **teknik gerekçesi** kayıtlıdır
(kaynak: `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B). Fiyatlar BEYAN GEREKLİ.

| # | Kalem | Zorunlu / öneri | Teknik gerekçe (kayıtlı) |
|---|---|---|---|
| D1 | microSD ≥ 64 GB (UHS-I) + kart okuyucu | zorunlu | JetPack imajı yazılacak |
| D2 | UBEC 5 V / 5 A | zorunlu | FCHUB'ın küçük BEC'i Nano'yu besleyemez |
| D3 | JST-GH 6-pin kablo + dişi-dişi jumper | zorunlu | TELEM1 (SiK) ve TELEM2 → Nano UART |
| D4 | USB webcam | zorunlu | CSI kamera yolu açılmazsa yedek (`--kaynak 0`) |
| D5 | XT60/XT90 fiş, kablo bağı, ısı makaronu, damper bant | zorunlu | kablolama demeti üretimi |
| D6 | **Yedek pervane seti (12×10, CW+CCW)** | zorunlu | ilk uçuşlarda en sık kırılan parça |
| D7 | Küçük ekran + klavye + ethernet kablosu | zorunlu | Nano ilk açılış |
| D8 | Multimetre, tartı, baret/yelek | zorunlu | kablolama kontrolü, **UHDR kütle ölçümü**, saha emniyeti |
| D9 | 2. pil 4S 10 Ah + ≥ 150 W şarj | öneri | tek pil günde 2 uçuşa kilitliyor; prova sayısını ikiye katlar |
| D10 | JetPack 4.6 / Py3.8 **GPU torch** tekerleği (indirme) | öneri | v36 YOLOv8m; CPU'da FPS kapısı düşebilir |
| D11 | JetPack 4.6.x SD imajı (indirme) | zorunlu | Nano sistem imajı |
| D12 | Taşınabilir bellek (≥ 2 GB boş) | zorunlu | saha paketi **1,27 GB** kopyalanacak |

**BEYAN GEREKLİ (insan): D1–D12 birim fiyatları, satın alma tarihleri ve fatura numaraları.**

---

## 7. Sapma analizi — planlanan ile gerçekleşen arasındaki fark

### 7.1 Sapmaların niteliği

Bütçe sapması bu projede üç ayrı sebepten doğmuştur; üçü de teknik kayıtlarla izlenebilir:

| # | Sapma sebebi | Somut örnek | Bütçe yönü | Teknik bedeli |
|---|---|---|---|---|
| S1 | **Araç sınıfı farkı** — FDA'nın §5.3.2 çoklu rotor şartı DDR'de yoktu | 4× 5008 motor + 4× 80 A ESC + quad gövde eklendi; kanat servoları, pitot, airspeed, paraşüt zinciri ertelendi | net etki **BEYAN GEREKLİ** | yeni bir araç montaj/kalibrasyon hattı |
| S2 | **Tedarik zorunluluğu** — planlanan parça yerine bulunabilen parça | Orin NX → Nano 4GB; M10 → M9N; TBS Crossfire → FlySky; Mauch → FCHUB+PM02 | **azaltıcı** | Nano'da `ultralytics` için ayrı Python 3.8 yığını; **TensorRT `.engine` ölçülemez**; FPS kapısı riske girdi |
| S3 | **Üretim kararı revizyonu** | Ayak/GPS tutucu **PLA → ABS**; **TPU taban pedi** eklendi; kol 3–4 daha ağır reçeteyle basıldı | küçük artırıcı | ısı dayanımı ↑, baskı süresi ↑ |

### 7.2 En pahalı sapma parasal değil: Orin NX → Nano 4GB

Bu satır bütçeyi **düşüren** ama teknik riski **artıran** tek kalemdir ve raporda böyle yazılır:

- Kazanç: kart maliyeti belirgin biçimde düşer (tutar BEYAN GEREKLİ).
- Bedel 1: JetPack 4.6'nın sistem Python'u 3.6 → ayrı `venv38` + **çevrimdışı 14 paket / 51 dosya / 246 MB** tekerlek zinciri kurulmak zorunda kalındı.
- Bedel 2: `venv38` içinde `tensorrt` yok → **`.engine` ÖLÇÜLEMEDİ**, uçuş PT/ONNX ile yapılacak.
- Bedel 3: üretim modeli **YOLOv8m-seg**'dir; Nano CPU'da **0,61 FPS** kapısı düşebilir. Ölçülmedi, tahmin edilmedi.
- Karşı önlem maliyeti: yedek USB webcam, GPU tekerleği araştırması, ikinci pil önerisi (D9/D10).

### 7.3 Ayni (nakit dışı) kaynak tüketimi — ölçülen

Bütçenin nakit olmayan ama gerçek olan kalemi hesaplama gücüdür. Defterde **ölçülmüş** ve
sonuçsuz kalan GPU zamanı vardır; bu rapor bunu da gizlemez. (Üçüncü satır bir kusur değildir:
reddedilen aday da bir sonuçtur — ama bütçeye giren maliyeti aynıdır ve sayılmalıdır.)

| kalem | ölçülen | kayıt |
|---|---|---|
| `seed`/belirlenircilik sorusu — **v31 + T128 + T128-B**, cevap alınamadı (v31 v30'un bit-bit kopyasını üretti) | **8,6 saat GPU** toplam = 6,4 (v31) + 1,18 (T128) + 1,04 (T128-B) | D-138 / D-252 / **D-253** |
| v8 aday eğitimi — 124 epoch, kabul zinciri **RED** | **6,19 saat GPU** | D-331 |

**BEYAN GEREKLİ (insan): toplam GPU/elektrik gideri ve varsa bulut hesaplama faturası.**
**BEYAN GEREKLİ (insan): insan işgücü (kişi-saat) dökümü** — takım üyeleri rol bazında.

### 7.4 Ertelenen kalemler — final aracının açık bütçesi

Tablo B'de "ertelendi" yazan on satır bugün **harcanmamış ama harcanacak** kalemlerdir. Bunlar
bütçe gerçekleme tablosunda sıfır görünür; oysa şartname §6 bu sistemleri **zorunlu** kılar.
Bir bütçe raporunun en yanıltıcı olabileceği yer burasıdır, o yüzden ayrı tablo açılmıştır.

| # | Ertelenen sistem | Şartname dayanağı | Bugünkü olgunluk (ölçülen) | Bütçe kalemi türü |
|---|---|---|---|---|
| E1 | **Sabit kanat gövde + kanat + kuyruk** | §6 *"sabit kanatlı İHA konfigürasyonunda olması zorunludur"* | CAD var (`Fuselage+Wing+Tail_CFD_Part.SLDPRT` + aileron/elevator/rudder parçaları, XFLR5 analiz dosyası); **imalat başlamadı** | üretim (malzeme + kalıp/kesim + işçilik) |
| E2 | **Mancınık (fırlatma platformu)** | §6, REQ-8, REQ-58 (ray geometrisi), REQ-59 (çift kademeli emniyet) | Depoda **CAD ve analiz yok** | üretim (profil, yay/lastik, tetik mekanizması) + test |
| E3 | **Paraşüt zinciri** (paraşüt, pod, servo, mekanizma, tether) | §6, REQ-9, REQ-186 (iniş dikey hız < 7 m/s) | DDR BOM'da tanımlı (kalem 12–16, 280 g); **temin/üretim kaydı yok**. Yazılım tarafı hazır (`CHUTE_*`, `iha_komut_alici` zinciri, YKS manuel yedek) | satın alma + mekanizma üretimi + atış testi |
| E4 | **İKA (insansız kara aracı)** | §2.2.6, §6 (≤ 10 kg, yük hariç), REQ-19 (tam otonom), R22 (yükü eksiksiz muhafaza) | Yazılım soyutlaması hazır ve testli; **gerçek motor sürücüsü YOK** — kuru koşuda `motor SAHIPSIZ` | satın alma (sürücü, motor, enkoder, IMU, GNSS) + şasi üretimi |
| E5 | **Çift acil güç kesme anahtarı (İHA)** | REQ-25…31 | 🔴 **Yok.** FDA aracında pil fişi kullanılıyor | satın alma (anahtar + röle) + kablolama |
| E6 | **Acil güç kesme (İKA)** | REQ-32…34 | Yok | satın alma |
| E7 | Pitot + airspeed sensörü | sabit kanat performansı, REQ-188 (V ≥ 1,15 × V_stall) | DDR BOM'da var; alınmadı | satın alma |
| E8 | Kanat/kuyruk servoları (×4) + servo BEC | sabit kanat kontrol yüzeyleri | DDR BOM'da var; alınmadı | satın alma |
| E9 | Sabit kanat için itki grubu (motor + ESC + pervane) | §6 | DDR'de SunnySky X2216 ×2 planlandı; FDA aracınınkinden **farklı** | satın alma |
| E10 | İkinci telemetri hattı (İKA) | §2.2.5 aktarım zinciri | Karar D-405'te açık bırakıldı (SiK/İKA hattı) | satın alma |

**BEYAN GEREKLİ (insan): E1–E10 için ayrılan bütçe ve tedarik takvimi.** Bu on satırın toplamı,
bugüne kadar harcanandan büyük olabilir; FDR'nin bütçe bölümü bunu görmezden gelemez.

### 7.5 Risk bütçesi — teknik riskin parasal karşılığı

Bölüm 5 §8.3 ve §10.5'te ölçülemedi olarak işaretlenmiş üç kapı, düşerse **para gerektirir**.
Aşağıdaki tablo "eğer düşerse ne alınır" sorusunun önceden verilmiş cevabıdır; tutarlar
BEYAN GEREKLİ, ama **kalemler bugünden bellidir** — sahada karar verilecek bir şey kalmasın diye.

| risk (kapı) | düşerse ne olur | gereken satın alma | öncelik |
|---|---|---|---|
| **FPS < 0,61** (Nano CPU'da YOLOv8m) | Gerçek zamanlı tespit tazelik penceresine sığmaz | (a) yok — önce ONNX Runtime denenir (bedelsiz); (b) çare bulunamazsa **daha güçlü görev bilgisayarı** (Orin Nano/NX sınıfı) | **yüksek** — 5 Eylül'de belli olur |
| **CSI kamera yolu açılmaz** | Görüntü hiç gelmez | **USB webcam** (D4, zaten listede) | orta — ucuz sigorta |
| **Tek pil / 3 saat şarj** | Uçuş günü 2 uçuşla sınırlı; prova sayısı yetmez | **2. pil 4S 10 Ah + ≥ 150 W şarj** (D9) | orta |
| **Pervane kırılması** | Uçuş günü iptal | **Yedek pervane seti** (D6, zaten listede) | yüksek — en sık kırılan parça |
| **PM02 sürekli akım sınırı** | Sürekli tam gazda güç modülü zorlanır | Uçuş profili kısıtı (bedelsiz); gerekirse **ayrı akım sensörü** | düşük |
| **`.engine` derlenemiyor** | Hızlandırma yok — FPS riski (yukarıdaki satırla aynı kök) | — (yazılım çözümü aranır) | — |

---

## 8. Bütçe izleme yordamı — bu bölümün doldurulma biçimi

Bu raporun kuralı, sayının **nereden geldiğinin** yazılmasıdır. Bütçe için de aynı disiplin
kurulmuştur: fiyatlar rastgele hatırlanarak değil, tek bir kayıttan gelecektir.

**Önerilen kayıt şeması** (takım tarafından tutulacak, SGGS'e doğrudan aktarılabilir):

| sütun | ne yazılır |
|---|---|
| `kalem_no` | Tablo A / Tablo D / Tablo E numarası (A12, D6, E3 …) |
| `ad` · `model` · `adet` | BOM ile birebir |
| `tur` | Ü (takım üretimi) / S (satın alma) / sarf |
| `tedarik_durumu` | alındı · sipariş edildi · henüz aksiyon alınmadı — §5.4'ün sözcükleri |
| `tarih` | satın alma / teslim tarihi |
| `birim_fiyat` · `toplam` · `para_birimi` · `kdv_dahil_mi` | — |
| `belge_no` | fatura / fiş / sipariş numarası |
| `odeyen` | takım bütçesi · maddi destek · sponsor · ayni |
| `kutle_g` | ölçülen kütle (tartı tutanağıyla aynı sayı) |
| `boyut_mm` | satın alınan kalemler için gabari |
| `not` | üretim zorluğu / fikstür ihtiyacı / iade-fire |

**Üç kural:**
1. **Tek kaynak.** Fiyat yalnız bu kayıtta durur; rapora buradan kopyalanır. Rapora elle
   yazılan sayı bayatlar — bu projede bayat sayı taşıma kusuru birden çok kez kayda geçmiştir.
2. **Belge yoksa satır yok.** Fatura/fiş numarası olmayan harcama "tahmini" sütununda kalır ve
   gerçekleme toplamına **girmez**.
3. **Kütle ile fiyat aynı satırda.** SGGS §5.4 ikisini birlikte ister; ayrı tutulursa
   5 Eylül tartı tutanağı ile satın alma kaydı eşleşmez.

**BEYAN GEREKLİ (insan): bu kaydın tutulacağı dosya/konum ve sorumlu rol** (öneri: kaptan,
`FDR/butce_kaydi.csv` olarak depoda).

---

## 9. Bütçe gerçekleme özeti (bugünkü hâliyle)

| başlık | durum (03.09.2026) |
|---|---|
| Onaylanan toplam bütçe | **BEYAN GEREKLİ (insan)** |
| Alınan maddi destek dilimi (%25) | **BEYAN GEREKLİ (insan)** |
| Bugüne kadarki gerçekleşen harcama | **BEYAN GEREKLİ (insan)** |
| Gerçekleme oranı (%) | **HESAPLANAMAZ** — payı da paydası da yok |
| Kalemleri belirlenmiş, fiyatı belirlenmemiş BOM | **Tablo A: 27 satır · Tablo D: 12 satır** — hazır |
| Ölçülmüş üretim kaynağı | 8 plaka, 2 yazıcı, 2 malzeme; **1 plakanın** süresi ve gramajı |
| Ölçülmüş ayni kaynak | **≈ 14,8 saat** GPU — sonuçsuz kalan ya da reddedilen eğitim kalemleri (8,6 = 6,4 + 1,18 + 1,04 · ve 6,19); ikisi karşılıksız, biri (v8) *"RED"* hükmüyle sonuçlandı |
| Ölçülmüş kütle | **yok** — 5 Eylül tartısıyla gelecek |

Bu tablo bilerek çoğunlukla boştur. **Bir bütçe gerçekleme analizi, gerçekleşmemiş bir bütçeyi
gerçekleşmiş gibi gösteremez;** bu bölümün hakemlere verdiği taahhüt, boş sütunların kim
tarafından ve hangi kayıtla doldurulacağının satır satır belli olmasıdır.

---

## 10. BEYAN GEREKLİ (insan) — toplu liste

1. **Maddi destek başvurusu yapıldı mı; onaylanan toplam bütçe; alınan dilim(ler).**
2. **Tablo A'daki 27 satırın birim fiyatı, adedi, satın alma tarihi ve fatura numarası.**
3. **Tablo A'daki satın alınan kalemlerin ağırlık ve boyut bilgileri** (üretici veri sayfası).
4. **5 Eylül tartı tutanağı** — üretilen ve satın alınan her parçanın ölçülen kütlesi; toplam kütle.
5. **CAD model kütleleri** (parça başına) — SGGS §5.4 zorunlu sütunu.
6. **Filament cinsi (ABS / ABS-CF), makara adedi ve makara fiyatı** (§5, Bölüm 5 §4.3 çelişkisi).
7. **Kalan 7 plakanın baskı süresi ve filament gramajı** (yeniden dilimleyerek).
8. **Fire / yeniden basım kaydı; yazıcı amortismanı ve elektrik gideri.**
9. **Tablo D'deki 12 tedarik kaleminin fiyatları ve satın alma tarihleri.**
10. **Bağlantı elemanı (vida/somun/pul), yapıştırıcı ve sarf kalemlerinin dökümü** — §5.4 açıkça sarf kalemlerini ister.
11. **Toplam GPU/elektrik gideri; varsa bulut hesaplama faturası.**
12. **İnsan işgücü (kişi-saat) dökümü, rol bazında.**
13. **Tablo E (E1–E10) ertelenen sistemler için ayrılan bütçe ve tedarik takvimi** — bugün hiçbiri satın alınmamıştır.
14. **Çift acil güç kesme anahtarı** (DDR BOM No 24 / E5-E6) için satın alma kararı — FDA aracında yok, final için şartname zorunlu.
15. **Risk bütçesi kararı (§7.5)** — FPS kapısı düşerse daha güçlü görev bilgisayarı alınacak mı; kararın sınırı ve tavanı.
16. **Bütçe kayıt dosyasının konumu ve sorumlu rolü** (§8).

---

## 11. Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | Şartname §5.4 SGGS'in BOM'dan istedikleri (üretim yöntemi, süre, CAD kütlesi, gerçek kütle, fikstür, zorluk, tedarik durumu, ağırlık/boyut) | `results/sartname_bosluk/sartname_metin.txt` §5.4 | PyMuPDF metin çıkarımı (`results/sartname_bosluk/rapor_uret.py`) | 2026-08-26 |
| 2 | Maddi destek dilimleri %25 (DDR sonrası) / %75 (FDA sonrası); SGGS teslim 05.02.2027 | aynı dosya §5.2, §5.3, s.11 takvim | aynı | 2026-08-26 |
| 3 | FDR Tablo 4 — Bölüm 7 "Bütçe Gerçekleme Analizi" 10 puan | aynı dosya §5.3.1 | aynı | 2026-08-26 |
| 4 | **Depoda fiyat/fatura/sipariş kaydı yok** (FDR/ dışında 0 eşleşme) | `O:\navitas` (tüm `.md`/`.json`/`.csv`) | `grep -rInE "₺\|fatura\|birim fiyat\|sipariş no" --include=…` | 2026-09-03 |
| 5 | FDA aracı kalem listesi (Tablo A) ve tedarik durumları | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | kullanıcı beyanı, 3 Eylül 2026 | 2026-09-03 |
| 6 | DDR aviyonik BOM'u — 27 kalem, toplam 2293 g, kalem ağırlıkları | `navitas-teknofest/references/ddr_requirements.md` | DDR dönemi Excel aktarımı — **DOĞRULANACAK** | 2026-07 |
| 7 | DDR mimari şemasında Pixhawk 6X / Orin NX / M10 (BOM ile çelişki) | `navitas-teknofest/references/avionics_software.md` | — | 2026-07 |
| 8 | 8 plaka, 2 yazıcı (X1 Carbon, P2S), ABS + TPU 95A, dilimleyici 02.07.01.62 | `dronesolid/files (3)/*.3mf` → `project_settings.config`, `slice_info.config` | zip + JSON okuma (bu raporun kanıt betiği) | 2026-09-03 |
| 9 | Üst çerçeve: 1 sa 30 dk 16 sn · 55,86 g · 22 332,62 mm | `dronesolid/files (3)/Plaka4_Ust_Cerceve_plate_1.gcode.3mf` | zip okuma → `Metadata/plate_1.gcode` | 2026-09-03 |
| 10 | Kol 1–2 ile kol 3–4 reçete farkı (0,20/%15/2 duvar ↔ 0,16/%40/6 duvar) | `Plaka1_Kol_1-2.3mf`, `Plaka2_Kol_3-4.3mf` | aynı | 2026-09-03 |
| 11 | PLA → ABS revizyonu (`Plaka6_PLA_Ayak_GPS.3mf` eski kuşak) | `dronesolid/Yeni klasör/files (1)/` | `ls -la` | 2026-09-03 |
| 12 | Tedarik listesi D1–D12 ve gerekçeleri | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B | — (plan çıktısı) | 2026-09-03 |
| 13 | Çevrimdışı tekerlek: 14 paket · 51 dosya · 246 MB | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A | `scripts/nano_tekerlek_indir.py` | 2026-09-03 |
| 14 | Saha belleği 1,27 GB (D12 kapasite gerekçesi) | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A | `scripts/bellek_hazirla.py` | 2026-09-03 |
| 15 | v31 = v30 bit-bit kopyası, **6,4 saat GPU** | `REVIEW_LOG.md` D-138 (alıntı D-252) | eğitim koşumu kıyası | 2026-08-16 |
| 16 | T128/T128-B toplam **8,6 saat GPU**, cevap alınamadı | `REVIEW_LOG.md` D-252 / D-253 | — | 2026-08-21 |
| 17 | v8 adayı 124 epoch / **6,19 saat**, kabul zinciri RED | `REVIEW_LOG.md` D-331 | `scripts/olcum/65_kabul_denetcisi.py` | 2026-08-28 |
| 18 | `.engine` Nano'da derlenemiyor (bütçe sapmasının teknik bedeli) | `jetson_paket/JETSON_NANO_KURULUM.md` §0 | — (belge, testle kilitli) | 2026-09-03 |
| 19 | FPS kapısı 0,61 (türetilmiş eşik) — henüz ölçülmedi | `FAZ_B_GUN_PLANI.md` §2; `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 | D-374 / D-376 | 2026-09-01 |
| 20 | Şartname §6 ağırlık limitleri (İHA 25 kg / İKA 10 kg) | `results/sartname_bosluk/sartname_metin.txt` §6 | PyMuPDF çıkarımı | 2026-08-26 |
