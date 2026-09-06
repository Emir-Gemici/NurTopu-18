# Bölüm 7. Bütçe Gerçekleme Analizi (10 PUAN)

> **Yönerge eşlemesi.** Yönerge (`results/fdr_sablon/fdr_yonerge_metin.txt`, Bölüm 7) bu bölümü
> **tek paragraf** hâlinde verir ve alt başlık numarası **tanımlamaz**. Aşağıdaki 7.1–7.5
> numaraları, o paragrafın **beş cümlesine birebir** karşılık gelir; başlık adları yönergenin
> kendi sözcükleriyle yazılmıştır. Kimlikler `FDR/YONERGE_HARITASI.md` §7'den alınmıştır.
>
> | başlık | yönergenin cümlesi | kimlik |
> |---|---|---|
> | 7.1 | *"Tüm satın alınacak veya satın alınmış malzeme ve bileşenleri içeren detaylı bir BOM tablosu hazırlanmalıdır. Bu tabloda her bir kalem için miktar, birim fiyat, toplam fiyat ve tedarik durumu açık bir şekilde belirtilmelidir."* | `Y-7-M01` |
> | 7.2 | *"Ayrıca her bir malzeme veya ekipman kalemi için planlanan maliyet ile gerçekleşen maliyet karşılaştırmalı olarak tablo hâlinde sunulmalıdır."* | `Y-7-M02` |
> | 7.3 | *"Toplam bütçenin hangi ana kalemlere harcandığı hem yüzdesel hem de sayısal olarak gösterilmeli ve bütçe dağılımı açık bir şekilde ortaya konulmalıdır."* | `Y-7-M03` |
> | 7.4 | *"Bunun yanında harcanmamış bütçenin hangi amaçlarla kullanılacağı (örneğin yedek parça alımı, ek test faaliyetleri vb.) kısa bir açıklama ile belirtilmelidir."* | `Y-7-M04` |
> | 7.5 | *"Planlanan bütçe ile gerçekleşen bütçe arasında bir fark oluşmuş ise bu farkın nedenleri de raporda açıkça açıklanmalıdır."* | `Y-7-M05` |

> **Bu bölümün yazım kuralı.** Bütçe gerçekleme, "ne planlandı / ne harcandı / fark neden"
> sorusunun sayılarla cevabıdır. Bu raporun kuralı gereği **var olmayan bir sayı uydurulmaz**.
> Aşağıda ölçülebilen her şey (kalem listesi, kütle, adet, malzeme tüketimi, hesaplama kaynağı,
> tedarik durumu) artefaktından çıkarılmış; **parasal sütunların tamamı BEYAN GEREKLİ (insan)**
> olarak bırakılmıştır. Gerekçesi aşağıdaki **Yöntem** başlığında ölçümle birlikte yazılıdır.

---

## Yöntem — bu bölümdeki her sayının kaynağı

### Y.1 Şartnamenin bu bölümden ve SGGS'ten istedikleri

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

### Y.2 🔴 Ölçüm: depoda parasal veri yoktur

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

**Bu ölçümün doğrudan sonucu:** yönergenin beş maddesinden **dördü** (7.2, 7.3, 7.4, 7.5)
parasal veri olmadan sayısal biçimde kapatılamaz. Bu bölüm bunları boş bırakmaz; **tablo
iskeletini kurar, hangi hücreyi kimin dolduracağını satır satır yazar** ve sayısal olmayan
(kalem, yön, adet, kaynak tüketimi) kısımlarını ölçülmüş hâliyle verir.

---

## 7.1 Detaylı BOM tablosu — miktar, birim fiyat, toplam fiyat, tedarik durumu (`Y-7-M01`)

Yönerge BOM'un **"tüm satın alınacak veya satın alınmış"** malzemeyi kapsamasını ister. Bu
kapsam bu raporda **beş tabloya** bölünmüştür; §7.1.6 hangi sistemin hangi tabloda olduğunu ve
**hangi sistemin kalem düzeyinde hâlâ eksik olduğunu** ölçümle gösterir.

### 7.1.1 Tablo A — FDA görev test uçuşu aracı (çoklu rotor) BOM'u

Kalem listesi kullanıcı beyanından (`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül 2026);
tedarik durumu 03.09.2026 itibarıyladır; **5 Eylül kutu açılışında** üç kalem plandan farklı ya da
teyitli çıktı (ESC, güç modülü, RC alıcı — `REVIEW_LOG.md` D-426 §3, BEYAN) ve ilgili satırlara
tarihli not düşüldü. 5 Eylül tutanağında tartı satırı yoktur; "Ölçülen kütle" sütunu BEYAN GEREKLİ kalır.
`Ü` = takım üretimi, `S` = hazır satın alınan alt sistem.

| # | Kalem | Model / özellik | Adet | Tür | Üretim yöntemi | Üretim süresi | CAD kütlesi (g) | Ölçülen kütle (g) | Tedarik durumu | Birim fiyat | Toplam fiyat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Kol | `Drone_Arm` (ABS) | 4 | Ü | FDM 3B baskı — bkz. Bölüm 5 §5.1.4 (kol 1–2 ve 3–4 **farklı reçete**) | **ÖLÇÜLEMEDİ** (G-code yok) | BEYAN GEREKLİ | BEYAN GEREKLİ (5 Eyl tartı) | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A2 | Üst çerçeve | `Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid / 2 duvar | **1 sa 30 dk 16 sn** (ölçüldü) | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A3 | Alt çerçeve | `Lower_Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A4 | Kubbe | `Drone_Dome` (ABS, **destekli**) | 1 | Ü | FDM, X1C | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A5 | Ayak | `Drone_Legs` (ABS, **destekli**) | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A6 | GNSS tutucu | `GPS_Holder` (ABS, **destekli**) | 1 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A7 | Taban pedi | TPU 95A | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A8 | Motor | **5008 340KV** | 4 | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; motor testi koştu (ÖLÇÜM `starting motor test` → `finished motor test`, D-426 §1); sıra/yön 4/4 BEYAN, video BEYAN GEREKLİ | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A9 | Pervane | **12×10** | 4 (+ yedek set) | S | — | — | — | BEYAN GEREKLİ | Kutuda; **yedek set alınacak** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A10 | ESC | plan **80 A, DShot destekli**; 5 Eylül kutudan **"60 A V2"** çıktı (BEYAN, D-426 §3) — tam marka/model BEYAN GEREKLİ | 4 | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; ESC kalibrasyonu YAPILMADI | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A11 | Güç dağıtım kartı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A12 | Uçuş kontrolcüsü | **Pixhawk 6C** — fabrikadan PX4 ile geldi; ArduCopter **4.5.7** flash edildi ve sabitlendi (ÖLÇÜM `ArduCopter V4.5.7 (2a3dc4b7)`, D-424/D-425/D-426) | 1 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 59 g) | Kutu açıldı 5 Eylül; çalışıyor | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A13 | Güç modülü | plan **PM02** (Pixhawk kutusundan); 5 Eylül kutudan **PM06** çıktı (BEYAN, D-426 §3) — etiket BEYAN GEREKLİ | 1 | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; `POWER1`'e 6 pinli kabloyla bağlı, çalışıyor (ÖLÇÜM: pil PreArm uyarısı kayboldu, D-426 §1) | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A14 | GNSS / pusula | **Holybro M9N** | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de M10 için 32 g) | Kutuda | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A15 | RC kumanda + alıcı | **FlySky FS-i6** + FS-iA6B (iBUS) — FS-iA6B 5 Eylül'de teyit (B harfi, D-426 §3) | 1 set | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; **bind edildi** (BEYAN), `RCInput: decoding IBUS(1)` (ÖLÇÜM, D-426 §1); alıcı `i-BUS SERVO` portu | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A16 | Telemetri | **SiK 433 MHz** | 2 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 35 g/adet) | Kutuda | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A17 | Görev bilgisayarı | **Jetson Nano 4GB** (Dev Kit) | 1 | S | — | — | — | BEYAN GEREKLİ | **Kargoda — 4/5 Eylül teslim** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A18 | microSD | ≥ 64 GB UHS-I + okuyucu | 1 | S | — | — | — | — | **Henüz alınmadı** (alışveriş listesi) | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A19 | Kamera | **Raspberry Pi HQ** (IMX477, CSI) + standart lens | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de Arducam için 50 g) | Kutuda; **FOV ölçülmedi** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A20 | Jetson besleme | **UBEC 5 V / 5 A** | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A21 | Pil | **4S 10 Ah 25C** | 1 (2. pil öneri) | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A22 | Şarj cihazı | **iMAX B6** (50 W) | 1 | S | — | — | — | — | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A23 | Kablolama demeti | XT60/XT90, JST-GH 6-pin, jumper, silikon kablo | lot | Ü | Kesim + lehim + makaron + etiket | BEYAN GEREKLİ | — | BEYAN GEREKLİ | Kısmen kutuda, kısmen **alınacak** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A24 | Sarf | kablo bağı, ısı makaronu, çift taraflı bant/damper, vida-somun-pul | lot | S | — | — | — | BEYAN GEREKLİ | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A25 | Yedek kamera | USB webcam (UVC) | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A26 | Filament | ABS (X1C + P2S profilleri) | BEYAN GEREKLİ (kg) | S | — | — | — | ölçülen tüketim: **≥ 55,86 g** (yalnız A2 için) | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A27 | Filament | TPU 95A | BEYAN GEREKLİ (kg) | S | — | — | — | **ÖLÇÜLEMEDİ** | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| — | **TOPLAM** | | | | | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | | **BEYAN GEREKLİ** | **BEYAN GEREKLİ** |

⚠ **Satır sayısı düzeltmesi (2026-09-04).** Tablo A'nın gerçek satır sayısı **27**'dir
(A1…A27, atlanan numara yok). Bu raporun önceki sürümünde iki yerde "Tablo A: 26 satır"
yazıyordu; sayım yapıldı ve **27** bulundu (kanıt dizini #21). Düzeltme §7.3.3 ve
"BEYAN GEREKLİ toplu liste"ye işlendi. **26 satır** ifadesi yalnız **Tablo B (DDR BOM)** için
doğrudur ve orada korunmuştur.

⚠ **"Toplam fiyat" sütunu bu sürümde eklendi.** Yönerge Bölüm 7 birim fiyatın yanında **toplam
fiyatı** da açıkça ister; önceki sürümde yalnız birim fiyat sütunu vardı. Sütun eklenmiş, içeriği
**BEYAN GEREKLİ (insan)** bırakılmıştır — çünkü toplam fiyat birim fiyat × adet'tir ve çarpanın
biri yoktur.

⚠ **Kütle toplamı bilerek boştur.** Şartname §6 İHA için 25 kg, İKA için 10 kg sınırı koyar; bu
sınırın karşılandığı **ancak tartılmış kütlelerle** iddia edilebilir. 5 Eylül envanterinde her
parça tartılacak (`SAHA_HAZIRLIK_PLANI` §2.1) ve bu sütun o tutanaktan doldurulacaktır.

⚠ **Boyut sütunu** bu tabloda yer almamaktadır; satın alınan kalemlerin gabarileri
**BEYAN GEREKLİ (insan)** — üretici veri sayfalarından toplanacaktır. Üretilen parçaların
gabarileri **ölçülmüştür** ve Bölüm 5 §5.1.3'tedir.

### 7.1.2 Tablo B — DDR aviyonik BOM'u ve bugünkü durumu

DDR'de beyan edilen aviyonik BOM (**26 satır**; numaralandırma 25'i atladığı için DDR metni 27 der) (toplam **2293 g**) sabit kanat konfigürasyonu
içindir. Aşağıda her satırın FDR'deki karşılığı ve bütçeye etkisinin **yönü** verilmiştir
(tutarlar BEYAN GEREKLİ).

| No | DDR kalemi | Model (DDR) | Adet | Ağırlık (g) | FDR'deki durum | Bütçe etkisinin yönü |
|---|---|---|---|---|---|---|
| 1 | Autopilot | Pixhawk 6C | 1 | 59 | **Değişmedi** (A12) | — |
| 2 | İşlemci | Jetson **Orin NX** + carrier + soğutucu | 1 | 180 | **Jetson Nano 4GB** ile değişti (A17) | **azaltıcı** (Nano çok daha ucuz); teknik bedeli §7.5.2'de |
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
| 17 | ESC | Hobbywing FlyFun 40A V5 | 2 | 70 | plan **80 A DShot ×4**; 5 Eylül kutudan **"60 A V2" ×4** (A10; D-426 §3) | **artırıcı** |
| 18 | Power sensor | **Mauch PL-100** | 1 | 22 | **PM06** ile değişti (A13; plan PM02, 5 Eylül kutudan PM06 — D-426 §3) | azaltıcı |
| 19 | Pixhawk BEC | Mauch PL 4-6S BEC | 1 | 24 | **FCHUB-12S / PM06** karşılıyor (plan PM02; D-426 §3) | azaltıcı |
| 20 | Servo BEC | Matek BEC12S-PRO | 1 | 5 | FDA'da **yok** | ertelendi |
| 21 | Jetson güç reg. | 12 V 5 A buck | 1 | 25 | **5 V / 5 A UBEC** (A20) | nötr |
| 22 | PDB | Güç dağıtım kartı | 1 | 60 | **Matek XCLASS FCHUB-12S V2** (A11) | nötr/artırıcı |
| 23 | Kablolama | XT60/XT90, JST-GH vb. | lot | 150 | **Değişmedi** (A23) | — |
| 24 | Acil kesme şalterleri | Anahtarlı stop + röle | 1 | 30 | 🔴 **FDA aracında YOK** — pil fişi kullanılıyor | **açık borç** (final için satın alma gerekir) |
| 26 | Telemetri (YKS) | Holybro SiK 433 | 1 | 35 | **Değişmedi** (A16) | — |
| 27 | Jetson SSD | NVMe M.2 250 GB | 1 | 10 | ~~Nano'da NVMe yok → microSD~~ **DÜZELTME (3 Eylül, D-413):** taşıyıcı kartta **M.2 VAR**, microSD **YOK**. DDR'deki bu kalem doğruydu; azaltıcı sayılması hataydı | **gerçekleşecek** |
| | **DDR beyan toplamı** | | | **2293** | FDA aracının kütlesi **ÖLÇÜLEMEDİ** | |

⚠ DDR belgesinin kendi içinde bir tutarsızlığı vardır: BOM "Pixhawk 6C" derken aynı dönemin
mimari şeması (`navitas-teknofest/references/avionics_software.md`) "Pixhawk 6X" yazar. Gerçek donanım **6C**'dir;
tutarsızlık burada kapanır.

⚠ **Düzeltilen iç atıf (2026-09-04):** 2 no'lu satırın "teknik bedeli §6'da" ifadesi bayat bir
göndermeydi — hedef bölüm bu raporun **§7.5.2**'sidir ve atıf oraya çevrilmiştir. Satırın başka
hiçbir alanına dokunulmamıştır.

### 7.1.3 Tablo C — Üretim (3B baskı) maliyeti ve kaynak tüketimi

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

**Not (Bölüm 5 §5.1.5'e bağlı):** dilimleyici projeleri düz **ABS** gösterir, kullanıcı beyanı
**ABS-CF** der. ABS-CF filament fiyatı düz ABS'nin belirgin üstündedir; bu yüzden malzeme
maliyeti satırı, §4.3'teki çelişki çözülmeden doldurulamaz.
**BEYAN GEREKLİ (insan): kullanılan filamentin cinsi, makara adedi ve makara fiyatı.**

### 7.1.4 Tablo D — Tedarik listesi (alınacaklar) ve gerekçeleri

Aşağıdaki kalemler 4 Eylül'e kadar alınacaktır; her satırın **teknik gerekçesi** kayıtlıdır
(kaynak: `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B). Fiyatlar BEYAN GEREKLİ.

| # | Kalem | Zorunlu / öneri | Teknik gerekçe (kayıtlı) | Birim fiyat | Toplam fiyat |
|---|---|---|---|---|---|
| D1 | microSD ≥ 64 GB (UHS-I) + kart okuyucu | zorunlu | JetPack imajı yazılacak | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D2 | UBEC 5 V / 5 A | zorunlu | FCHUB'ın küçük BEC'i Nano'yu besleyemez | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D3 | JST-GH 6-pin kablo + dişi-dişi jumper | zorunlu | TELEM1 (SiK) ve TELEM2 → Nano UART | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D4 | USB webcam | zorunlu | CSI kamera yolu açılmazsa yedek (`--kaynak 0`) | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D5 | XT60/XT90 fiş, kablo bağı, ısı makaronu, damper bant | zorunlu | kablolama demeti üretimi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D6 | **Yedek pervane seti (12×10, CW+CCW)** | zorunlu | ilk uçuşlarda en sık kırılan parça | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D7 | Küçük ekran + klavye + ethernet kablosu | zorunlu | Nano ilk açılış | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D8 | Multimetre, tartı, baret/yelek | zorunlu | kablolama kontrolü, **UHDR kütle ölçümü**, saha emniyeti | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D9 | 2. pil 4S 10 Ah + ≥ 150 W şarj | öneri | tek pil günde 2 uçuşa kilitliyor; prova sayısını ikiye katlar | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D10 | JetPack 4.6 / Py3.8 **GPU torch** tekerleği (indirme) | öneri | v36 YOLOv8m; CPU'da FPS kapısı düşebilir | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D11 | JetPack 4.6.x SD imajı (indirme) | zorunlu | Nano sistem imajı | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D12 | Taşınabilir bellek (≥ 2 GB boş) | zorunlu | saha paketi **1,27 GB** kopyalanacak | BEYAN GEREKLİ | BEYAN GEREKLİ |

**BEYAN GEREKLİ (insan): D1–D12 birim fiyatları, satın alma tarihleri ve fatura numaraları.**

⚠ **Çakışma uyarısı (çift sayım riski).** Tablo D'nin bazı satırları Tablo A'daki kalemlerle
**aynı fiziksel malzemedir**: D1↔A18, D2↔A20, D4↔A25, D5↔A23/A24, D6↔A9'un yedek seti,
D9↔A21'in ikinci pili. Bütçe toplanırken bu satırlar **bir kez** sayılır. §7.3.3'teki dağılım
tablosu bu nedenle Tablo A'yı esas alır, Tablo D'yi ayrı bir toplam olarak eklemez.

### 7.1.5 Tablo E — Satın alınacak (ertelenen) sistemler: final aracının açık BOM'u

Tablo B'de "ertelendi" yazan on satır bugün **harcanmamış ama harcanacak** kalemlerdir. Bunlar
bütçe gerçekleme tablosunda sıfır görünür; oysa şartname §6 bu sistemleri **zorunlu** kılar.
Bir bütçe raporunun en yanıltıcı olabileceği yer burasıdır, o yüzden ayrı tablo açılmıştır.
Yönergenin *"satın alınacak"* ifadesinin karşılığı bu tablodur.

| # | Ertelenen sistem | Şartname dayanağı | Bugünkü olgunluk (ölçülen) | Bütçe kalemi türü |
|---|---|---|---|---|
| E1 | **Sabit kanat gövde + kanat + kuyruk** | §6 *"sabit kanatlı İHA konfigürasyonunda olması zorunludur"* | CAD var (`Fuselage+Wing+Tail_CFD_Part.SLDPRT` + aileron/elevator/rudder parçaları, XFLR5 analiz dosyası); **imalat başlamadı** | üretim (malzeme + kalıp/kesim + işçilik) |
| E2 | **Mancınık (fırlatma platformu)** | §6, REQ-8, REQ-58 (ray geometrisi), REQ-59 (çift kademeli emniyet) | Depoda **CAD ve analiz yok** | üretim (profil, yay/lastik, tetik mekanizması) + test |
| E3 | **Paraşüt zinciri** (paraşüt, pod, servo, mekanizma, tether) | §6, REQ-9, REQ-186 (iniş dikey hız < 7 m/s) | DDR BOM'da tanımlı (kalem 12–16, 280 g); **temin/üretim kaydı yok**. Yazılım tarafı hazır (`CHUTE_*`, `iha_komut_alici` zinciri, YKS manuel yedek) | satın alma + mekanizma üretimi + atış testi |
| E4 | **İKA (insansız kara aracı)** | §2.2.6, §6 (≤ 10 kg, yük hariç), REQ-19 (tam otonom), R22 (yükü eksiksiz muhafaza) | Yazılım soyutlaması hazır ve testli; **gerçek motor sürücüsü YOK** — kuru koşuda `motor SAHIPSIZ` | satın alma (sürücü, motor, enkoder, IMU, GNSS) + şasi üretimi |
| E5 | **Çift acil güç kesme anahtarı (İHA)** | REQ-25…31 (DDR, takım kimliği) | 🔴 **Yok.** FDA aracında pil fişi kullanılıyor | satın alma (anahtar + röle) + kablolama |
| E6 | **Acil güç kesme (İKA)** | REQ-32…34 | Yok | satın alma |
| E7 | Pitot + airspeed sensörü | sabit kanat performansı, REQ-188 (V ≥ 1,15 × V_stall) | DDR BOM'da var; alınmadı | satın alma |
| E8 | Kanat/kuyruk servoları (×4) + servo BEC | sabit kanat kontrol yüzeyleri | DDR BOM'da var; alınmadı | satın alma |
| E9 | Sabit kanat için itki grubu (motor + ESC + pervane) | §6 | DDR'de SunnySky X2216 ×2 planlandı; FDA aracınınkinden **farklı** | satın alma |
| E10 | İkinci telemetri hattı (İKA) | §2.2.5 aktarım zinciri | Karar D-405'te açık bırakıldı (SiK/İKA hattı) | satın alma |

**BEYAN GEREKLİ (insan): E1–E10 için ayrılan bütçe ve tedarik takvimi.** Bu on satırın toplamı,
bugüne kadar harcanandan büyük olabilir; FDR'nin bütçe bölümü bunu görmezden gelemez.

⚠ **E1–E10 kalem düzeyinde değil, SİSTEM düzeyindedir.** Yönerge BOM'dan kalem başına miktar ve
fiyat ister; bu on satır o ayrıntıya henüz inmemiştir. Eksik olan tam olarak §7.1.6'da yazılıdır.

### 7.1.6 BOM kapsam denetimi — "tüm malzeme" şartı karşılandı mı

Yönerge *"tüm satın alınacak veya satın alınmış malzeme ve bileşenler"* der. Aşağıdaki tablo,
yarışmanın üç platformunun (İHA, İKA, Mancınık) BOM kapsamındaki durumunu **ölçümle** verir.

| platform / sistem | bu bölümde nerede | kalem düzeyinde BOM var mı | eksik olan |
|---|---|---|---|
| **FDA görev test uçuşu aracı** (çoklu rotor) | Tablo A (§7.1.1), 27 satır | **VAR** — kalem, model, adet, tedarik durumu tam | birim fiyat, toplam fiyat, kütle, boyut |
| **Yarışma final aracı — İHA aviyoniği** | Tablo B (§7.1.2), 26 satır | **VAR** (DDR beyanı) | fiyat sütunları hiç yok |
| **Yarışma final aracı — sabit kanat yapısı** | Tablo E, E1 | **YOK** — yalnız sistem satırı | parça listesi, malzeme miktarı, fiyat |
| **Paraşüt / kurtarma zinciri** | Tablo B 12–16 + Tablo E, E3 | **KISMEN** — DDR'de 5 kalem ve ağırlıkları var | fiyat, tedarikçi, temin kaydı |
| **İKA (insansız kara aracı)** | Tablo E, E4 | 🔴 **YOK** | şasi, motor, sürücü, enkoder, IMU, GNSS, pil kalemleri; adet; fiyat |
| **Mancınık (fırlatma platformu)** | Tablo E, E2 | 🔴 **YOK** | profil, yay/lastik, tetik mekanizması, ray kalemleri; adet; fiyat |
| **3B baskı sarfı** | Tablo A A26–A27 + Tablo C (§7.1.3) | **KISMEN** | makara adedi ve fiyatı; 7 plakanın gramajı |
| **Bağlantı elemanı ve yapıştırıcı** | Tablo A A24 (tek "lot" satırı) | 🔴 **YOK** — kalem dökümü yapılmamış | vida/somun/pul cinsi ve adedi, yapıştırıcı türü |

**Ölçüm (2026-09-04).** İKA ve Mancınık için depoda kalem düzeyinde bir BOM aranmıştır:

```
grep -rInE "İKA .*BOM|Mancınık .*BOM|BOM.*İKA|BOM.*Mancınık" --include="*.md" --include="*.json" --include="*.csv" .
→  3 eşleşme; üçü de BOM'un KENDİSİ değil, yokluğunun kaydı:
     FDR/ACIK_KALEMLER.md:87   → "İKA yapısal bölümü yok — … parça numaralandırma + BOM …"
     FDR/YONERGE_HARITASI.md:151 → Y-3.3.1-M02 gereksinim satırı
     SAHA_HAZIRLIK_PLANI_20260903.md:233 → "SGGS BOM" ileri tarihli iş kalemi
   (2026-09-04, `.claude/worktrees` hariç)
```

Yani yönergenin *"tüm"* şartı bugün **karşılanmamıştır** ve bu rapor bunu gizlemez:
**iki platformun (İKA, Mancınık) BOM'u hiç yazılmamıştır.**

**BEYAN GEREKLİ (insan): İKA için kalem düzeyinde BOM** — şasi, tahrik motoru, motor sürücüsü,
enkoder, IMU, GNSS, pil, gövde malzemesi; her biri için adet, birim fiyat, toplam fiyat, tedarik
durumu.
**BEYAN GEREKLİ (insan): Mancınık için kalem düzeyinde BOM** — ray profili, enerji depolama
elemanı (yay/lastik), tetik mekanizması, taban/şase, emniyet elemanları; her biri için adet,
birim fiyat, toplam fiyat, tedarik durumu.

---

## 7.2 Planlanan maliyet ↔ gerçekleşen maliyet karşılaştırmalı tablosu (`Y-7-M02`)

Yönerge **her kalem için** iki sütunlu bir karşılaştırma ister. Önceki sürümde bu tablo yoktu —
BOM tablolarında tek bir "Birim fiyat" sütunu vardı ve karşılaştırma kurulmamıştı. Aşağıdaki
tablo o iskeleti kurar.

**Bu tablonun iki sütunu da bugün boştur ve nedeni ölçülmüştür (§Y.2):** deponun tamamında tek
bir fiyat kaydı yoktur. Bu, "gerçekleşen"in bilinmemesinden ibaret değildir — **"planlanan" da
kayıtlı değildir**; DDR'de kalem listesi ve ağırlıklar var, fiyat yok. Bu yüzden fark sütunu
`HESAPLANAMAZ`'dır: çıkarmanın iki terimi de eksiktir.

**Kolon sözleşmesi.** `Planlanan` = DDR'de beyan edilen kalem ve onun için ayrılmış tutar.
`Gerçekleşen` = FDA görev test uçuşu aracında fiilen kullanılan kalem ve ödenen tutar.
`Fark yönü` **ölçülmüş değil, kalem değişikliğinden çıkarılmış niteliksel yöndür** ve Tablo B'nin
"Bütçe etkisinin yönü" sütunuyla aynıdır.

### 7.2.1 DDR'de planlanmış kalemler (26 satır)

| DDR No | Kalem | Planlanan (DDR) | Planlanan maliyet | Gerçekleşen (FDA aracı) | Gerçekleşen maliyet | Fark tutarı | Fark yönü | Nedeni (§7.5) |
|---|---|---|---|---|---|---|---|---|
| 1 | Autopilot | Pixhawk 6C | BEYAN GEREKLİ | Pixhawk 6C (A12) | BEYAN GEREKLİ | HESAPLANAMAZ | değişmedi | — |
| 2 | Görev bilgisayarı | Jetson Orin NX + carrier | BEYAN GEREKLİ | Jetson Nano 4GB (A17) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 3 | Kamera | Arducam IMX477 | BEYAN GEREKLİ | RPi HQ IMX477 (A19) | BEYAN GEREKLİ | HESAPLANAMAZ | nötr/azaltıcı | S2 |
| 4 | Pitot tüpü | Pitot + hortum | BEYAN GEREKLİ | alınmadı — ertelendi (E7) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 5 | Airspeed | Holybro MS5525DSO | BEYAN GEREKLİ | alınmadı — ertelendi (E7) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 6 | Telemetri (uçak) | Holybro SiK 433 | BEYAN GEREKLİ | SiK 433 (A16) | BEYAN GEREKLİ | HESAPLANAMAZ | değişmedi | — |
| 7 | GNSS | Holybro M10 + pusula | BEYAN GEREKLİ | Holybro M9N (A14) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 8 | RC alıcı | TBS Crossfire Nano RX | BEYAN GEREKLİ | FlySky FS-i6 + FS-iA6B (A15) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 9 | Motor | SunnySky X2216 ×2 | BEYAN GEREKLİ | 5008 340KV ×4 (A8) | BEYAN GEREKLİ | HESAPLANAMAZ | artırıcı | S1 |
| 10 | Servo (kanat/kuyruk) | EMAX ES08MA II ×4 | BEYAN GEREKLİ | alınmadı — ertelendi (E8) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 11 | Pil | 4S 14–15 Ah Li-ion | BEYAN GEREKLİ | 4S 10 Ah 25C LiPo (A21) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S1/S2 |
| 12 | Paraşüt | Opale Rescue 2,5 m² | BEYAN GEREKLİ | alınmadı — ertelendi (E3) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 13 | Paraşüt pod | Rescue Pod | BEYAN GEREKLİ | alınmadı — ertelendi (E3) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 14 | Paraşüt servo | EMAX ES08MA II | BEYAN GEREKLİ | alınmadı — ertelendi (E3) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 15 | Paraşüt mekanizması | Servo kontrollü kapak | BEYAN GEREKLİ | üretilmedi — ertelendi (E3) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 16 | Paraşüt bağlantı | Nylon/Kevlar tether | BEYAN GEREKLİ | alınmadı — ertelendi (E3) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 17 | ESC | Hobbywing FlyFun 40A V5 ×2 | BEYAN GEREKLİ | "60 A V2" ×4 (A10; plan 80 A DShot, 5 Eylül kutudan 60 A V2 — D-426 §3) | BEYAN GEREKLİ | HESAPLANAMAZ | artırıcı | S1 |
| 18 | Power sensor | Mauch PL-100 | BEYAN GEREKLİ | PM06 (A13; plan PM02, 5 Eylül kutudan PM06 — D-426 §3) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 19 | Pixhawk BEC | Mauch PL 4-6S BEC | BEYAN GEREKLİ | FCHUB-12S / PM06 karşılıyor (A11/A13; plan PM02) | 0 (ayrı kalem alınmadı) | HESAPLANAMAZ | azaltıcı | S2 |
| 20 | Servo BEC | Matek BEC12S-PRO | BEYAN GEREKLİ | alınmadı — ertelendi (E8) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 21 | Jetson güç reg. | 12 V 5 A buck | BEYAN GEREKLİ | 5 V / 5 A UBEC (A20) — **henüz alınmadı** | BEYAN GEREKLİ | HESAPLANAMAZ | nötr | S2 |
| 22 | PDB | Güç dağıtım kartı | BEYAN GEREKLİ | Matek XCLASS FCHUB-12S V2 (A11) | BEYAN GEREKLİ | HESAPLANAMAZ | nötr/artırıcı | S2 |
| 23 | Kablolama | XT60/XT90, JST-GH vb. | BEYAN GEREKLİ | değişmedi (A23) — kısmen alınacak | BEYAN GEREKLİ | HESAPLANAMAZ | değişmedi | — |
| 24 | Acil kesme şalterleri | Anahtarlı stop + röle | BEYAN GEREKLİ | 🔴 alınmadı; FDA'da pil fişi (E5/E6) | 0 (harcanmadı) | HESAPLANAMAZ | açık borç | S1 |
| 26 | Telemetri (YKS) | Holybro SiK 433 | BEYAN GEREKLİ | SiK 433 (A16) | BEYAN GEREKLİ | HESAPLANAMAZ | değişmedi | — |
| 27 | Jetson SSD | NVMe M.2 250 GB | BEYAN GEREKLİ | alınacak — taşıyıcı kartta M.2 var (D-413) | BEYAN GEREKLİ | HESAPLANAMAZ | gerçekleşecek | S2 |

**Yön dağılımı (26 satır üzerinden sayıldı, 2026-09-04):** azaltıcı **6** · nötr/azaltıcı **1** ·
artırıcı **2** · nötr/artırıcı **1** · nötr **1** · ertelendi **9** · değişmedi **4** ·
açık borç **1** · gerçekleşecek **1**. Toplam **26**. Bu sayım Tablo B'nin "Bütçe etkisinin yönü"
sütunundan çıkarılmıştır ve **parasal değil, kalem sayısıdır**.

### 7.2.2 DDR'de planlanmamış, FDA aracında gerçekleşen kalemler

Bu satırların **planlanan maliyeti sıfırdır**, çünkü DDR'de karşılıkları yoktu; FDA aracının
çoklu rotor olması zorunluluğu (§7.5.1, S1) bunları doğurmuştur.

| BOM | Kalem | Planlanan (DDR) | Planlanan maliyet | Gerçekleşen | Gerçekleşen maliyet | Fark yönü | Nedeni |
|---|---|---|---|---|---|---|---|
| A1 | Kol ×4 (ABS, FDM) | yok | 0 (planlanmadı) | üretildi | BEYAN GEREKLİ (filament + makine) | artırıcı | S1/S3 |
| A2 | Üst çerçeve (ABS) | yok | 0 (planlanmadı) | üretildi | BEYAN GEREKLİ | artırıcı | S1 |
| A3 | Alt çerçeve (ABS) | yok | 0 (planlanmadı) | üretildi | BEYAN GEREKLİ | artırıcı | S1 |
| A4 | Kubbe (ABS) | yok | 0 (planlanmadı) | üretildi | BEYAN GEREKLİ | artırıcı | S1 |
| A5 | Ayak ×4 (ABS) | yok | 0 (planlanmadı) | üretildi — **PLA'dan ABS'ye revizyon** | BEYAN GEREKLİ | artırıcı | S3 |
| A6 | GNSS tutucu (ABS) | yok | 0 (planlanmadı) | üretildi — **PLA'dan ABS'ye revizyon** | BEYAN GEREKLİ | artırıcı | S3 |
| A7 | Taban pedi ×4 (TPU 95A) | yok | 0 (planlanmadı) | üretildi — **yeni eklendi** | BEYAN GEREKLİ | artırıcı | S3 |
| A9 | Pervane 12×10 ×4 + yedek set | yok (DDR'de itki grubu farklı) | 0 (planlanmadı) | kutuda; yedek set alınacak (D6) | BEYAN GEREKLİ | artırıcı | S1 |
| A18 | microSD ≥ 64 GB + okuyucu (D1) | yok (Orin'de NVMe planlanmıştı) | 0 (planlanmadı) | **henüz alınmadı** | BEYAN GEREKLİ | artırıcı | S2 |
| A22 | Şarj cihazı iMAX B6 | yok | 0 (planlanmadı) | mevcut (yeni alım yok) | 0 (harcanmadı) | nötr | — |
| A24 | Sarf (bağ, makaron, damper, vida) (D5) | yok (ayrı kalem olarak) | 0 (planlanmadı) | **henüz alınmadı** | BEYAN GEREKLİ | artırıcı | S1 |
| A25 | Yedek USB webcam (D4) | yok | 0 (planlanmadı) | **henüz alınmadı** | BEYAN GEREKLİ | artırıcı | S2 (risk önlemi) |
| A26 | ABS filament | yok | 0 (planlanmadı) | mevcut; tüketim ≥ 55,86 g ölçüldü | BEYAN GEREKLİ | artırıcı | S1/S3 |
| A27 | TPU 95A filament | yok | 0 (planlanmadı) | mevcut; tüketim **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | artırıcı | S3 |
| D7 | Ekran + klavye + ethernet | yok | 0 (planlanmadı) | **henüz alınmadı** | BEYAN GEREKLİ | artırıcı | S2 |
| D8 | Multimetre, tartı, baret/yelek | yok | 0 (planlanmadı) | **henüz alınmadı** | BEYAN GEREKLİ | artırıcı | test/emniyet |
| D9 | 2. pil + ≥ 150 W şarj (öneri) | yok | 0 (planlanmadı) | karar verilmedi | BEYAN GEREKLİ | artırıcı | risk önlemi (§7.4.2) |

### 7.2.3 Bu tablonun kapatılma koşulu

Karşılaştırma tablosu, **iki kayıt** geldiğinde tek seferde sayısal hâle gelir:

1. **Planlanan sütunu** — DDR döneminde kalemlere ayrılmış tutarlar. Depoda yok
   (`navitas-teknofest/references/ddr_requirements.md` yalnız kalem, adet ve ağırlık taşır).
   **BEYAN GEREKLİ (insan): DDR bütçe planı — kalem başına planlanan tutar.**
2. **Gerçekleşen sütunu** — **Ek E.1**'de tanımlanan bütçe kaydından kopyalanır.

Bu iki kayıt gelene kadar tablonun **satırları** doğrudur, **hücreleri** boştur; bu ayrım
raporun kuralı gereği açıkça yazılmıştır.

---

## 7.3 Toplam bütçenin ana kalemlere dağılımı — yüzdesel ve sayısal (`Y-7-M03`)

### 7.3.1 Bütçenin kaynağı ve dilimleri (şartname)

- DDR sonrası başarılı bulunan ve maddi destek başvurusu yapmış takımlar toplam bütçenin **%25**'ini,
- FDA sonrası başarılı bulunanlar **%75**'ini almaya hak kazanır (§5.2, §5.3).
- Başvuru **zorunlu değildir**; form KYS üzerinden iletilir, tarih Yarışmalar Komitesince belirlenir.

**BEYAN GEREKLİ (insan): takımın maddi destek başvurusu yapıp yapmadığı, onaylanan toplam bütçe
tutarı ve bugüne kadar alınan dilim(ler).** Bu üç bilgi olmadan "gerçekleme oranı" hesaplanamaz.

### 7.3.2 Neden yüzdesel dağılım bugün hesaplanamıyor

Yüzdesel dağılım bir **bölme** işlemidir: `ana kalem harcaması / toplam bütçe`. Bugün **payı da
paydası da** yoktur (§Y.2 ölçümü). Bu yüzden §7.3.3'teki tablonun parasal sütunları
`BEYAN GEREKLİ`, yüzde sütunu `HESAPLANAMAZ`'dır.

Buna karşılık dağılımın **hangi ana kalemlere** yapılacağı bugün bellidir ve gruplama
ölçülebilir bir şeydir: Tablo A'nın 27 satırının her biri **tam olarak bir** ana kaleme
düşürülmüştür (örtüşme yok, açıkta satır yok — 3+3+4+4+2+9+2 = 27).

### 7.3.3 Ana kalem dağılımı — FDA görev test uçuşu aracı (Tablo A esas)

| # | Ana kalem grubu | Kapsadığı BOM satırları | Kalem adedi | Kalem adedi payı (%) | Harcanan tutar | Bütçe payı (%) |
|---|---|---|---|---|---|---|
| G1 | İtki grubu (motor, ESC, pervane) | A8, A9, A10 | 3 | 11,1 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G2 | Uçuş kontrol ve seyrüsefer | A12, A13, A14 | 3 | 11,1 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G3 | Görev bilgisayarı ve görüntüleme | A17, A18, A19, A25 | 4 | 14,8 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G4 | Güç ve enerji | A11, A20, A21, A22 | 4 | 14,8 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G5 | Haberleşme ve kumanda | A15, A16 | 2 | 7,4 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G6 | Yapısal üretim (3B baskı + filament) | A1–A7, A26, A27 | 9 | 33,3 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G7 | Kablolama, bağlantı ve sarf | A23, A24 | 2 | 7,4 | BEYAN GEREKLİ | HESAPLANAMAZ |
| | **TOPLAM (Tablo A)** | A1–A27 | **27** | **100** (yuvarlamayla 99,9) | **BEYAN GEREKLİ** | **HESAPLANAMAZ** |

⚠ **"Kalem adedi payı" bir bütçe payı DEĞİLDİR.** Bu sütun yalnız BOM satırlarının sayımıdır ve
bir motorun bir kablo bağıyla aynı ağırlıkta sayıldığı yerdir. Buraya konmasının tek nedeni,
grupların **tam ve örtüşmesiz** olduğunu gösterilebilir kılmaktır. Parasal pay ancak §7.3.5'teki
girdiler geldiğinde yazılır.

### 7.3.4 Tablo A dışındaki ana kalemler

| # | Ana kalem grubu | Kaynak | Harcanan tutar | Bütçe payı (%) |
|---|---|---|---|---|
| G8 | Saha ve test ekipmanı, emniyet donanımı | Tablo D: D7, D8, D11, D12 | BEYAN GEREKLİ | HESAPLANAMAZ |
| G9 | Yedek parça | Tablo D: D6 (pervane), D4 (webcam), D9 (2. pil) — Tablo A ile çakışır, bir kez sayılır | BEYAN GEREKLİ | HESAPLANAMAZ |
| G10 | Ertelenen zorunlu sistemler (final aracı) | Tablo E: E1–E10 — **bugün 0 harcandı** | BEYAN GEREKLİ (ayrılacak) | HESAPLANAMAZ |
| G11 | Ayni (nakit dışı) kaynak — hesaplama gücü | §7.5.3: ölçülen **≈ 14,8 saat GPU** | BEYAN GEREKLİ (elektrik/bulut) | HESAPLANAMAZ |
| G12 | Ayni (nakit dışı) kaynak — insan işgücü | rol bazlı kişi-saat | BEYAN GEREKLİ | HESAPLANAMAZ |

### 7.3.5 Bu dağılımın kapatılma koşulu

Yüzde sütunları **tek bir sayı** geldiğinde hesaplanabilir hâle gelir: **onaylanan toplam bütçe**
(payda). Kalem tutarları (pay) **Ek E.1**'deki bütçe kaydından gelir.

**BEYAN GEREKLİ (insan): onaylanan toplam bütçe tutarı ve para birimi** — bu sayı gelmeden
§7.3.3 ve §7.3.4'ün yüzde sütunları yazılmaz; tahminle doldurulmaz.

---

## 7.4 Harcanmamış bütçenin hangi amaçlarla kullanılacağı (`Y-7-M04`)

### 7.4.1 Harcanmamış bütçe bugün ölçülebiliyor mu

Hayır. `harcanmamış bütçe = onaylanan bütçe − gerçekleşen harcama`; iki terim de yoktur (§Y.2).
Bu yüzden **tutar HESAPLANAMAZ**'dır. Ancak yönergenin istediği şey tutar değil,
*"hangi amaçlarla kullanılacağı"*dır — ve **amaçlar bugün kalem kalem bellidir**. Aşağıdaki dört
başlık, para geldiğinde nereye gideceğinin önceden verilmiş cevabıdır; sahada karar verilecek bir
şey kalmasın diye yazılmıştır.

| # | Kullanım amacı | Somut kalemler (BOM referanslı) | Öncelik | Ayrılacak tutar |
|---|---|---|---|---|
| K1 | **Yedek parça** | Yedek pervane seti (D6 / A9) · yedek USB webcam (D4 / A25) · yedek ESC ve motor **BEYAN GEREKLİ (insan): alınacak mı** | yüksek | BEYAN GEREKLİ |
| K2 | **Ek test faaliyeti** | 2. pil + ≥ 150 W şarj (D9) — prova uçuşu sayısını ikiye katlar · menzil testi ve arıza emniyet testi saha gideri (Bölüm 4) · saha ulaşım/konaklama **BEYAN GEREKLİ (insan)** | yüksek | BEYAN GEREKLİ |
| K3 | **Ertelenen zorunlu sistemler** | Tablo E: E1–E10 (sabit kanat, mancınık, paraşüt zinciri, İKA, çift acil kesme, pitot/airspeed, servo, itki grubu, ikinci telemetri) | **zorunlu** — şartname §6 | BEYAN GEREKLİ |
| K4 | **Risk bütçesi** (kapı düşerse) | §7.4.2 tablosu | koşullu | BEYAN GEREKLİ |

⚠ K3, bu bölümün en büyük parasal kalemidir ve bugün **sıfır** harcanmıştır. "Harcanmamış bütçe"
sorusuna verilecek en dürüst cevap şudur: harcanmamış olan, **henüz üretilmemiş yarışma final
aracının tamamıdır**.

### 7.4.2 Risk bütçesi — teknik riskin parasal karşılığı

Bölüm 5 §5.2.7 ve §5.2.9'da ölçülemedi olarak işaretlenmiş üç kapı, düşerse **para gerektirir**.
Aşağıdaki tablo "eğer düşerse ne alınır" sorusunun önceden verilmiş cevabıdır; tutarlar
BEYAN GEREKLİ, ama **kalemler bugünden bellidir** — sahada karar verilecek bir şey kalmasın diye.

| risk (kapı) | düşerse ne olur | gereken satın alma | öncelik |
|---|---|---|---|
| **FPS < 0,61** (Nano CPU'da YOLOv8m) | Gerçek zamanlı tespit tazelik penceresine sığmaz | (a) yok — önce ONNX Runtime denenir (bedelsiz); (b) çare bulunamazsa **daha güçlü görev bilgisayarı** (Orin Nano/NX sınıfı) | **yüksek** — 5 Eylül'de belli olur |
| **CSI kamera yolu açılmaz** | Görüntü hiç gelmez | **USB webcam** (D4, zaten listede) | orta — ucuz sigorta |
| **Tek pil / 3 saat şarj** | Uçuş günü 2 uçuşla sınırlı; prova sayısı yetmez | **2. pil 4S 10 Ah + ≥ 150 W şarj** (D9) | orta |
| **Pervane kırılması** | Uçuş günü iptal | **Yedek pervane seti** (D6, zaten listede) | yüksek — en sık kırılan parça |
| **PM06 sürekli akım sınırı** (plan PM02; 5 Eylül kutudan PM06 çıktı, D-426 §3 — sınır değeri etiketten BEYAN GEREKLİ) | Sürekli tam gazda güç modülü zorlanır | Uçuş profili kısıtı (bedelsiz); gerekirse **ayrı akım sensörü** | düşük |
| **`.engine` derlenemiyor** | Hızlandırma yok — FPS riski (yukarıdaki satırla aynı kök) | — (yazılım çözümü aranır) | — |

### 7.4.3 Harcanmamış bütçenin kullanımını kilitleyen karar

Risk bütçesinin en pahalı satırı (**daha güçlü görev bilgisayarı**) bir tavana ihtiyaç duyar.

**BEYAN GEREKLİ (insan): FPS kapısı düşerse daha güçlü görev bilgisayarı alınacak mı; kararın
sınırı ve tavanı.**
**BEYAN GEREKLİ (insan): harcanmamış bütçenin K1–K4 arasındaki dağılımı ve onay merci.**

---

## 7.5 Planlanan ↔ gerçekleşen bütçe farkı ve nedenleri (`Y-7-M05`)

### 7.5.1 Sapmaların niteliği

Bütçe sapması bu projede üç ayrı sebepten doğmuştur; üçü de teknik kayıtlarla izlenebilir:

| # | Sapma sebebi | Somut örnek | Bütçe yönü | Teknik bedeli |
|---|---|---|---|---|
| S1 | **Araç sınıfı farkı** — FDA'nın §5.3.2 çoklu rotor şartı DDR'de yoktu | 4× 5008 motor + 4× ESC (plan 80 A; 5 Eylül kutudan "60 A V2", D-426 §3) + quad gövde eklendi; kanat servoları, pitot, airspeed, paraşüt zinciri ertelendi | net etki **BEYAN GEREKLİ** | yeni bir araç montaj/kalibrasyon hattı |
| S2 | **Tedarik zorunluluğu** — planlanan parça yerine bulunabilen parça | Orin NX → Nano 4GB; M10 → M9N; TBS Crossfire → FlySky; Mauch → FCHUB+PM06 (plan PM02; 5 Eylül kutudan PM06 — D-426 §3) | **azaltıcı** | Nano'da `ultralytics` için ayrı Python 3.8 yığını; **TensorRT `.engine` ölçülemez**; FPS kapısı riske girdi |
| S3 | **Üretim kararı revizyonu** | Ayak/GPS tutucu **PLA → ABS**; **TPU taban pedi** eklendi; kol 3–4 daha ağır reçeteyle basıldı | küçük artırıcı | ısı dayanımı ↑, baskı süresi ↑ |

### 7.5.2 En pahalı sapma parasal değil: Orin NX → Nano 4GB

Bu satır bütçeyi **düşüren** ama teknik riski **artıran** tek kalemdir ve raporda böyle yazılır:

- Kazanç: kart maliyeti belirgin biçimde düşer (tutar BEYAN GEREKLİ).
- Bedel 1: JetPack 4.6'nın sistem Python'u 3.6 → ayrı `venv38` + **çevrimdışı 14 paket / 51 dosya / 246 MB** tekerlek zinciri kurulmak zorunda kalındı.
- Bedel 2: `venv38` içinde `tensorrt` yok → **`.engine` ÖLÇÜLEMEDİ**, uçuş PT/ONNX ile yapılacak.
- Bedel 3: üretim modeli **YOLOv8m-seg**'dir; Nano CPU'da **0,61 FPS** kapısı düşebilir. Ölçülmedi, tahmin edilmedi.
- Karşı önlem maliyeti: yedek USB webcam, GPU tekerleği araştırması, ikinci pil önerisi (D9/D10).

### 7.5.3 Ayni (nakit dışı) kaynak tüketimi — ölçülen

Bütçenin nakit olmayan ama gerçek olan kalemi hesaplama gücüdür. Defterde **ölçülmüş** ve
sonuçsuz kalan GPU zamanı vardır; bu rapor bunu da gizlemez. (Üçüncü satır bir kusur değildir:
reddedilen aday da bir sonuçtur — ama bütçeye giren maliyeti aynıdır ve sayılmalıdır.)

| kalem | ölçülen | kayıt |
|---|---|---|
| `seed`/belirlenircilik sorusu — **v31 + T128 + T128-B**, cevap alınamadı (v31 v30'un bit-bit kopyasını üretti) | **8,6 saat GPU** toplam = 6,4 (v31) + 1,18 (T128) + 1,04 (T128-B) | **D-140** / D-252 / **D-253** |
| v8 aday eğitimi — 124 epoch, kabul zinciri **RED** | **6,19 saat GPU** | D-331 |

**BEYAN GEREKLİ (insan): toplam GPU/elektrik gideri ve varsa bulut hesaplama faturası.**
**BEYAN GEREKLİ (insan): insan işgücü (kişi-saat) dökümü** — takım üyeleri rol bazında.

### 7.5.4 Farkın büyüklüğü: bugün ne biliniyor, ne bilinmiyor

| soru | cevap | dayanak |
|---|---|---|
| Fark **oluştu mu**? | **Evet** — 26 DDR kaleminin 22'sinde kalem düzeyinde değişiklik var (yalnız 4'ü "değişmedi") | §7.2.1 yön sayımı |
| Farkın **nedenleri** yazıldı mı? | **Evet** — üç sebep (S1, S2, S3) ve her DDR kalemi bir sebebe bağlandı | §7.5.1 + §7.2.1 son sütun |
| Farkın **yönü** biliniyor mu? | **Kısmen** — kalem başına niteliksel yön kayıtlı; net yön **HESAPLANAMAZ** (artırıcı ve azaltıcı kalemler tartılamıyor) | §7.2.1 |
| Farkın **tutarı** biliniyor mu? | **Hayır — HESAPLANAMAZ.** Planlanan da gerçekleşen de kayıtlı değil | §Y.2 ölçümü |

Yönergenin bu maddesi *"fark oluşmuş ise nedenleri açıkça açıklanmalıdır"* der. **Nedenler
yazılmıştır** ve kalem düzeyinde izlenebilir; eksik olan yalnız **tutar**dır, o da tahminle
değil kayıtla kapanır (**Ek E.1**).

---

## Yönerge dışı ek kanıt

> Aşağıdaki üç başlık yönerge Bölüm 7'nin beş maddesinden birine birebir düşmez, ama bu bölümün
> boş hücrelerinin **kim tarafından, hangi kayıtla** doldurulacağını tanımlar. Bu yüzden
> silinmemiş, ayrı başlık altında tutulmuştur.

### Ek E.1 Bütçe izleme yordamı — bu bölümün doldurulma biçimi

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
| `planlanan_tutar` | DDR bütçe planındaki karşılık — §7.2'nin "Planlanan" sütununu besler |
| `ana_kalem` | G1…G12 — §7.3.3 / §7.3.4 dağılımını besler |
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

⚠ Şema iki sütunla genişletildi (`planlanan_tutar`, `ana_kalem`): bunlar olmadan §7.2'nin
karşılaştırma tablosu ve §7.3'ün dağılım tablosu kayıttan **türetilemez**, elle yazılmak zorunda
kalır — yani 1. kural çiğnenir.

### Ek E.2 Bütçe gerçekleme özeti (bugünkü hâliyle)

| başlık | durum (03.09.2026) |
|---|---|
| Onaylanan toplam bütçe | **BEYAN GEREKLİ (insan)** |
| Alınan maddi destek dilimi (%25) | **BEYAN GEREKLİ (insan)** |
| Bugüne kadarki gerçekleşen harcama | **BEYAN GEREKLİ (insan)** |
| Gerçekleme oranı (%) | **HESAPLANAMAZ** — payı da paydası da yok |
| Kalemleri belirlenmiş, fiyatı belirlenmemiş BOM | **Tablo A: 27 satır · Tablo D: 12 satır · Tablo E: 10 sistem** — hazır |
| Kalem düzeyinde BOM'u hiç yazılmamış platform | **İKA ve Mancınık** (§7.1.6 ölçümü) |
| Planlanan ↔ gerçekleşen karşılaştırma tablosu | **iskelet hazır** (§7.2, 26 + 17 satır); hücreler boş |
| Ana kalem dağılımı | **gruplar hazır** (G1–G12, örtüşmesiz); yüzde **HESAPLANAMAZ** |
| Ölçülmüş üretim kaynağı | 8 plaka, 2 yazıcı, 2 malzeme; **1 plakanın** süresi ve gramajı |
| Ölçülmüş ayni kaynak | **≈ 14,8 saat** GPU — sonuçsuz kalan ya da reddedilen eğitim kalemleri (8,6 = 6,4 + 1,18 + 1,04 · ve 6,19); ikisi karşılıksız, biri (v8) *"RED"* hükmüyle sonuçlandı |
| Ölçülmüş kütle | **yok** — 5 Eylül tartısıyla gelecek |

Bu tablo bilerek çoğunlukla boştur. **Bir bütçe gerçekleme analizi, gerçekleşmemiş bir bütçeyi
gerçekleşmiş gibi gösteremez;** bu bölümün hakemlere verdiği taahhüt, boş sütunların kim
tarafından ve hangi kayıtla doldurulacağının satır satır belli olmasıdır.

### Ek E.3 BEYAN GEREKLİ (insan) — toplu liste

1. **Maddi destek başvurusu yapıldı mı; onaylanan toplam bütçe; alınan dilim(ler).**
2. **Tablo A'daki 27 satırın birim fiyatı, toplam fiyatı, adedi, satın alma tarihi ve fatura numarası.**
3. **Tablo A'daki satın alınan kalemlerin ağırlık ve boyut bilgileri** (üretici veri sayfası).
4. **5 Eylül tartı tutanağı** — üretilen ve satın alınan her parçanın ölçülen kütlesi; toplam kütle.
5. **CAD model kütleleri** (parça başına) — SGGS §5.4 zorunlu sütunu.
6. **Filament cinsi (ABS / ABS-CF), makara adedi ve makara fiyatı** (§7.1.3, Bölüm 5 §5.1.5 çelişkisi).
7. **Kalan 7 plakanın baskı süresi ve filament gramajı** (yeniden dilimleyerek).
8. **Fire / yeniden basım kaydı; yazıcı amortismanı ve elektrik gideri.**
9. **Tablo D'deki 12 tedarik kaleminin fiyatları ve satın alma tarihleri.**
10. **Bağlantı elemanı (vida/somun/pul), yapıştırıcı ve sarf kalemlerinin dökümü** — §5.4 açıkça sarf kalemlerini ister.
11. **Toplam GPU/elektrik gideri; varsa bulut hesaplama faturası.**
12. **İnsan işgücü (kişi-saat) dökümü, rol bazında.**
13. **Tablo E (E1–E10) ertelenen sistemler için ayrılan bütçe ve tedarik takvimi** — bugün hiçbiri satın alınmamıştır.
14. **Çift acil güç kesme anahtarı** (DDR BOM No 24 / E5-E6) için satın alma kararı — FDA aracında yok, final için şartname zorunlu.
15. **Risk bütçesi kararı (§7.4.2)** — FPS kapısı düşerse daha güçlü görev bilgisayarı alınacak mı; kararın sınırı ve tavanı.
16. **Bütçe kayıt dosyasının konumu ve sorumlu rolü** (Ek E.1).
17. **DDR bütçe planı — kalem başına planlanan tutar** (§7.2.1'in "Planlanan maliyet" sütunu). Bu kayıt olmadan yönergenin `Y-7-M02` maddesi sayısal olarak kapanmaz.
18. **İKA için kalem düzeyinde BOM** (şasi, motor, sürücü, enkoder, IMU, GNSS, pil) — adet, birim fiyat, toplam fiyat, tedarik durumu (§7.1.6).
19. **Mancınık için kalem düzeyinde BOM** (ray profili, yay/lastik, tetik mekanizması, taban, emniyet elemanları) — adet, birim fiyat, toplam fiyat, tedarik durumu (§7.1.6).
20. **Harcanmamış bütçenin K1–K4 arasındaki dağılımı ve onay mercii** (§7.4.1).
21. **Saha ulaşım, konaklama ve test günü giderleri** (§7.4.1 K2) — ek test faaliyeti bütçesi.

---

## Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | Şartname §5.4 SGGS'in BOM'dan istedikleri (üretim yöntemi, süre, CAD kütlesi, gerçek kütle, fikstür, zorluk, tedarik durumu, ağırlık/boyut) | `results/sartname_bosluk/sartname_metin.txt` §5.4 | PyMuPDF metin çıkarımı (`results/sartname_bosluk/rapor_uret.py`) | 2026-08-26 |
| 2 | Maddi destek dilimleri %25 (DDR sonrası) / %75 (FDA sonrası); SGGS teslim 05.02.2027 | aynı dosya §5.2, §5.3, s.11 takvim | aynı | 2026-08-26 |
| 3 | FDR Tablo 4 — Bölüm 7 "Bütçe Gerçekleme Analizi" 10 puan | aynı dosya §5.3.1 | aynı | 2026-08-26 |
| 4 | **Depoda fiyat/fatura/sipariş kaydı yok** (FDR/ dışında 0 eşleşme) | `O:\navitas` (tüm `.md`/`.json`/`.csv`) | `grep -rInE "₺\|fatura\|birim fiyat\|sipariş no" --include=…` | 2026-09-03 |
| 5 | FDA aracı kalem listesi (Tablo A) ve tedarik durumları | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | kullanıcı beyanı, 3 Eylül 2026 | 2026-09-03 |
| 6 | DDR aviyonik BOM'u — **26 satır** (numara 25 atlanmış), toplam 2293 g, kalem ağırlıkları | `navitas-teknofest/references/ddr_requirements.md` | DDR dönemi Excel aktarımı — **DOĞRULANACAK** | 2026-07 |
| 7 | DDR mimari şemasında Pixhawk 6X / Orin NX / M10 (BOM ile çelişki) | `navitas-teknofest/references/avionics_software.md` | — | 2026-07 |
| 8 | 8 plaka, 2 yazıcı (X1 Carbon, P2S), ABS + TPU 95A, dilimleyici 02.07.01.62 | `dronesolid/files (3)/*.3mf` → `project_settings.config`, `slice_info.config` | zip + JSON okuma (bu raporun kanıt betiği) | 2026-09-03 |
| 9 | Üst çerçeve: 1 sa 30 dk 16 sn · 55,86 g · 22 332,62 mm | `dronesolid/files (3)/Plaka4_Ust_Cerceve_plate_1.gcode.3mf` | zip okuma → `Metadata/plate_1.gcode` | 2026-09-03 |
| 10 | Kol 1–2 ile kol 3–4 reçete farkı (0,20/%15/2 duvar ↔ 0,16/%40/6 duvar) | `Plaka1_Kol_1-2.3mf`, `Plaka2_Kol_3-4.3mf` | aynı | 2026-09-03 |
| 11 | PLA → ABS revizyonu (`Plaka6_PLA_Ayak_GPS.3mf` eski kuşak) | `dronesolid/Yeni klasör/files (1)/` | `ls -la` | 2026-09-03 |
| 12 | Tedarik listesi D1–D12 ve gerekçeleri | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B | — (plan çıktısı) | 2026-09-03 |
| 13 | Çevrimdışı tekerlek: 14 paket · 51 dosya · 246 MB | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A | `scripts/nano_tekerlek_indir.py` | 2026-09-03 |
| 14 | Saha belleği 1,27 GB (D12 kapasite gerekçesi) | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A | `scripts/bellek_hazirla.py` | 2026-09-03 |
| 15 | v31 = v30 bit-bit kopyası, **6,4 saat GPU** | `REVIEW_LOG.md` D-140 (alıntı D-252) | eğitim koşumu kıyası | 2026-08-16 |
| 16 | T128/T128-B toplam **8,6 saat GPU**, cevap alınamadı | `REVIEW_LOG.md` D-252 / D-253 | — | 2026-08-21 |
| 17 | v8 adayı 124 epoch / **6,19 saat**, kabul zinciri RED | `REVIEW_LOG.md` D-331 | `scripts/olcum/65_kabul_denetcisi.py` | 2026-08-28 |
| 18 | `.engine` Nano'da derlenemiyor (bütçe sapmasının teknik bedeli) | `jetson_paket/JETSON_NANO_KURULUM.md` §0 | — (belge, testle kilitli) | 2026-09-03 |
| 19 | FPS kapısı 0,61 (türetilmiş eşik) — henüz ölçülmedi | `FAZ_B_GUN_PLANI.md` §2; `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 | D-374 / D-376 | 2026-09-01 |
| 20 | Şartname §6 ağırlık limitleri (İHA 25 kg / İKA 10 kg) | `results/sartname_bosluk/sartname_metin.txt` §6 | PyMuPDF çıkarımı | 2026-08-26 |
| 21 | Tablo A'nın gerçek satır sayısı **27** (A1…A27, atlanan numara yok); önceki metindeki "26 satır" hatalıydı | `FDR/BOLUM_7_BUTCE_GERCEKLEME.md` | satır sayımı, regex `^\| A\d+ \|` | 2026-09-04 |
| 22 | **İKA ve Mancınık için kalem düzeyinde BOM depoda YOK** — 3 eşleşmenin üçü de yokluk kaydı/gereksinim satırı | `FDR/ACIK_KALEMLER.md`:87 · `FDR/YONERGE_HARITASI.md`:151 · `SAHA_HAZIRLIK_PLANI_20260903.md`:233 | `grep -rInE "İKA .*BOM\|Mancınık .*BOM\|BOM.*İKA\|BOM.*Mancınık" --include="*.md" --include="*.json" --include="*.csv" .` | 2026-09-04 |
| 23 | Tablo A'nın 27 satırı G1–G7 ana kalem gruplarına **örtüşmesiz** dağılıyor (3+3+4+4+2+9+2 = 27) | bu dosya §7.3.3 | grup ataması + toplama | 2026-09-04 |
| 24 | Tablo B'nin 26 satırında bütçe yönü dağılımı: azaltıcı 6 · nötr/azaltıcı 1 · artırıcı 2 · nötr/artırıcı 1 · nötr 1 · ertelendi 9 · değişmedi 4 · açık borç 1 · gerçekleşecek 1 | bu dosya §7.1.2 "Bütçe etkisinin yönü" sütunu | satır sayımı | 2026-09-04 |
| 25 | Yönerge Bölüm 7'nin beş gereksinimi (`Y-7-M01…M05`) ve birebir cümleleri | `results/fdr_sablon/fdr_yonerge_metin.txt` Bölüm 7; `FDR/YONERGE_HARITASI.md` §7 | pypdf metin çıkarımı | 2026-09-04 |
| 26 | Tablo A/B künye farkı 5 Eylül: ESC "60 A V2" ×4 (plan 80 A DShot), güç modülü PM06 (plan PM02), FS-iA6B teyit — fiyat etkisi BEYAN GEREKLİ | `REVIEW_LOG.md` D-426 §3 (satır 29852–29854) | takım üyesi beyanı (kutu açılınca), ölçüm değil | 2026-09-05 |
| 27 | A12 Pixhawk 6C: PX4 ile geldi, ArduCopter 4.5.7 flash (`ArduCopter V4.5.7 (2a3dc4b7)`); A8 motor testi `starting/finished motor test`; A13 PM06 → `POWER1` pil PreArm uyarısı kayboldu; A15 `RCInput: decoding IBUS(1)` | `REVIEW_LOG.md` D-426 §1 (satır 29819–29826); D-424 (29622); D-425 (29711) | Mission Planner `Messages` satırları | 2026-09-05 |
| 28 | 5 Eylül'de tartı yapılmadı (tutanakta tartı satırı yok) — "Ölçülen kütle" sütunu BEYAN GEREKLİ | `REVIEW_LOG.md` D-426 (satır 29809–29886, `grep -i tarti` → 0) | — | 2026-09-05 |
