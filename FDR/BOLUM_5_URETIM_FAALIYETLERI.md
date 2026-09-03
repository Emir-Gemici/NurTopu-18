# BÖLÜM 5 — Üretim Faaliyetleri (15 puan)

> **Bu bölümün yazım kuralı.** Aşağıdaki her sayı bir artefakttan gelir: dilimleyici proje
> dosyası, STL ikili başlığı, üretilmiş G-code, betik çıktısı ya da depo dosyası. Hangi
> dosyadan ve hangi komutla çıkarıldığı §13 Kanıt dizini'nde yazılıdır.
> **Ölçülmemiş hiçbir üretim değeri tahmin edilmemiştir**; ölçülmemiş olan "ÖLÇÜLEMEDİ" ya da
> **BEYAN GEREKLİ (insan)** diye yazılmıştır. Beyan ile artefaktın çeliştiği iki yer vardır
> (§4.3 ve §5.3); ikisi de gizlenmeden, çelişkinin kendisi rapora yazılarak bırakılmıştır.

---

## 1. Kapsam — hangi aracın üretimi anlatılıyor

Şartname §5.3.2 (FDA görev test uçuşu) **çoklu rotorlu** bir araç ister; şartname §6 (yarışma)
**sabit kanatlı** İHA + mancınık + paraşüt + İKA ister. Bunlar **iki ayrı fiziksel sistemdir**
ve üretim durumları farklıdır.

| | **FDA aracı — çoklu rotor** | **Yarışma aracı — sabit kanat + mancınık + paraşüt + İKA** |
|---|---|---|
| Üretim durumu (03.09.2026) | Gövde **basıldı ve monte edildi**; aviyonik kutuda, montaj **5 Eylül** | **Üretilmedi.** CAD parçaları var (§11), imalat başlamadı |
| Bu bölümdeki yeri | §3 – §10 (asıl anlatı) | §11 (üretim planı) |

Bu bölüm ağırlıklı olarak FDA aracının **gerçekleşmiş** üretimini anlatır; §11 final aracının
üretim planını ve bugünkü olgunluk seviyesini verir.

---

## 2. Üretim mimarisi — üretilen / tedarik edilen ayrımı

Şartname §6: *"Yarışmaya dahil edilecek sistemlerin; tasarım, boyutlandırma ve imalat
süreçlerinin tamamının yarışmacı takımlar tarafından gerçekleştirilmesi esastır."*

| katman | üretim türü | kanıt |
|---|---|---|
| **Yapısal (gövde, kol, alt/üst çerçeve, kubbe, ayak, GPS tutucu, TPU ped)** | **Takım üretimi** — SolidWorks'te modellendi, dilimlendi, 3B basıldı | Yerel `.SLDPRT` + `.SLDASM` parça dosyaları, türetilmiş `.STEP` ve `.STL` ihraçları, Bambu Studio `.3mf` plaka projeleri (§3, §4) |
| **Aviyonik (uçuş kontrolcüsü, GNSS, ESC, motor, güç, telsiz, kamera, görev bilgisayarı)** | **Hazır satın alınan alt sistem** — entegrasyonu takım yapar | Künye `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2; BOM Bölüm 7 |
| **Kablolama demeti** | **Takım üretimi** (kesim, lehim, makaron, etiket) | Yordam §6; kabul ölçütleri tabloda |
| **Uçuş kontrolcüsü yapılandırması** | **Takım üretimi** — parametre ve görev planı dosyası olarak üretildi ve testle kilitlendi | `config/pixhawk/` (§7) |
| **Görev yazılımı ve model** | **Takım üretimi** | `config/model_registry.json`, `tests/` (§9) |
| **Görev bilgisayarı sistem imajı** | **Takım kurulumu** — tedarikçi imajı üzerine çevrimdışı yığın | `jetson_paket/JETSON_NANO_KURULUM.md` (§8) |

**Özgünlük kanıtı (§6 intihal hükmü karşısında).** Depoda parçaların **yerel SolidWorks
kaynak dosyaları** durmaktadır — `Drone_Arm.SLDPRT` (134 593 B), `Drone_Frame.SLDPRT`
(161 748 B), `Lower_Drone_Frame.SLDPRT` (87 210 B), `Drone_Dome.SLDPRT` (2 310 497 B),
`Drone_Legs.SLDPRT` (204 294 B), `GPS_Holder.SLDPRT` (153 510 B) ve bunları birleştiren
`Drone_Assembly.SLDASM` (484 241 B) — ayrıca üç parçanın nötr `.STEP` ihracı ve gövde için
**çözülmüş bir sonlu elemanlar çalışması** (§10.4). Rapora giren STL'ler bu parçaların
ihraçlarıdır; adları birebir eşleşir. Kaynak parametrik model + montaj + analiz zincirinin
bir arada bulunması, geometrinin hazır bir ticari platformdan alınmadığının **belge düzeyinde**
kanıtıdır.
**BEYAN GEREKLİ (insan): tasarımın takım üyelerince özgün olarak modellendiğine dair imzalı
beyan** — dosyaların varlığı yazarlığı kanıtlar ama beyan yerine geçmez.

---

## 3. CAD künyesi — ölçülen geometri

Aşağıdaki değerler **STL ikili dosyalarının kendisinden** hesaplanmıştır: üçgen sayısı ikili
başlığın 80–84. baytından, gabari (bounding box) tüm köşe noktalarının taranmasıyla, sha256
tüm dosya üzerinden (betik: bu raporun kanıt betiği, 2026-09-03).

| parça (STL) | üçgen | dosya (bayt) | gabari X×Y×Z (mm) | sha256 (ilk 12) | adet |
|---|---|---|---|---|---|
| `Drone_Arm_STL.STL` (kol) | 1 834 | 91 784 | 174,90 × 8,00 × 174,90 | `c1424c7898d7` | **4** |
| `Drone_Frame_STL.STL` (üst çerçeve) | 2 104 | 105 284 | 182,98 × 4,00 × 182,98 | `e1de7a7acaeb` | 1 |
| `Lower_Drone_Frame_STL.STL` (alt çerçeve) | 2 224 | 111 284 | 190,00 × 8,00 × 190,00 | `e852b687a4a7` | 1 |
| `Drone_Dome_STL.STL` (kubbe) | 18 456 | 922 884 | 182,98 × 78,00 × 182,98 | `be5d1cbe3c50` | 1 |
| `Drone_Legs_STL.STL` (ayak) | 3 790 | 189 584 | 50,00 × 150,00 × 157,50 | `0502673b0571` | **4** |
| `GPS_Holder_STL.STL` (GNSS tutucu) | 4 584 | 229 284 | 49,99 × 60,00 × 77,50 | `7a98ea44e89f` | 1 |
| TPU taban pedi | *(STL depoda ayrı yok)* | — | — | — | **4** |

⚠ **DOĞRULANACAK — kol gabarisi.** Kol, STL koordinat sisteminde **çapraz** yerleştirilmiştir
(X ve Z gabarileri birbirine eşit, kalınlık Y = 8 mm). Bu yüzden 174,90 mm **kolun boyu değildir**;
kolun gerçek boyu parametrik modelden (`Drone_Arm.SLDPRT`) okunmalıdır. Dilimleyicinin ölçtüğü
tabla izdüşüm alanı kol başına **8 607,19 mm²**'dir (kaynak: `Plaka1_Kol_1-2.3mf` →
`Metadata/plate_1.json`). Diğer parçaların tabla izdüşüm alanları: alt çerçeve **35 196,2 mm²**,
üst çerçeve **26 842,4 mm²**, kubbe **3 403,5 mm²**, ayak **189,0 mm²** (her biri), GPS tutucu
**10,5 mm²**, TPU ped **2 494,3 mm²**.

⚠ **STL birimi mm kabul edilmiştir** (ikili STL biriminde birim bilgisi taşımaz). Dilimleyici
projelerinin aynı geometriyi Bambu Lab X1C / P2S tablasına (256 × 256 mm) sığdırması bu kabulü
destekler, ancak nihai teyit CAD'den yapılmalıdır → **BEYAN GEREKLİ (insan): CAD birim ve ölçek teyidi**.

**BEYAN GEREKLİ (insan): CAD model kütlesi** (parça başına, g) — SGGS §5.4 bunu açıkça ister ve
depoda hesaplanmış bir CAD kütlesi yoktur.

---

## 4. 3B baskı üretimi — dilimleme reçeteleri (ölçüldü)

Üretim, **Bambu Studio** ile plaka plaka dilimlenmiş ve `.3mf` proje dosyaları saklanmıştır.
Aşağıdaki tablo bu proje dosyalarındaki `Metadata/project_settings.config` alanlarından
**okunmuştur** — hiçbiri elle yazılmamıştır.

### 4.1 Plaka reçeteleri

| plaka dosyası | içerik | yazıcı | malzeme | katman | dolgu | duvar | üst/alt kabuk | destek | brim |
|---|---|---|---|---|---|---|---|---|---|
| `Plaka1_Kol_1-2.3mf` | Kol ×2 | **Bambu Lab X1 Carbon** 0,4 | ABS (`Bambu ABS @BBL X1C - Kopyala`) | 0,20 mm | **%15 grid** | **2** | 5 / 3 | yok | auto |
| `Plaka2_Kol_3-4.3mf` | Kol ×2 | *(kayıtta yazıcı alanı yok)* | ABS | **0,16 mm** | **%40 gyroid** | **6** | **7 / 7** | yok | outer_only |
| `Plaka3_Alt_Cerceve.3mf` | Alt çerçeve ×1 | Bambu Lab X1 Carbon 0,4 | ABS (`Bambu ABS @BBL X1C`) | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | auto |
| `Plaka4_Ust_Cerceve.3mf` | Üst çerçeve (`Drone_Frame`) ×1 | Bambu Lab X1 Carbon 0,4 | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | auto |
| `Plaka5_Kubbe.3mf` | Kubbe ×1 | Bambu Lab X1 Carbon 0,4 | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | auto |
| `Plaka_Ayak.3mf` | Ayak ×3 | **Bambu Lab P2S** 0,4 | ABS (`Bambu ABS @BBL P2S - Kopyala`) | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | auto |
| `Plaka_GPS_Holder.3mf` | GPS tutucu ×1 + ayak ×1 | Bambu Lab P2S 0,4 | ABS (`Generic ABS @BBL P2S`) | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | auto |
| `tpu_taban_pedi_x4.3mf` | Taban pedi ×4 | Bambu Lab P2S 0,4 | **TPU 95A** (`Bambu TPU 95A @BBL P2S`) | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | auto |

Dilimleyici sürümü, proje dosyalarının başlığında yazılıdır: **Bambu Studio 02.07.01.62**
(`Metadata/slice_info.config` → `X-BBL-Client-Version`). Depoda ayrıca kurulum dosyası
`Bambu_Studio_win-v02.08.02.61.exe` bulunur; **projeler 02.07.01.62 ile dilimlenmiştir**, kurulum
dosyasının sürümüyle karıştırılmamalıdır.

### 4.2 🔴 Ölçülmüş üretim bulgusu — dört kol aynı reçeteyle basılmadı

`Plaka1` (kol 1–2) ile `Plaka2` (kol 3–4) reçeteleri **birbirinden farklıdır** ve fark
mukavemet yönündedir: katman 0,20 → **0,16 mm**, dolgu %15 grid → **%40 gyroid**, duvar 2 → **6**,
üst/alt kabuk 5/3 → **7/7**. Yani **kol 3 ve kol 4, kol 1 ve kol 2'den belirgin biçimde daha
sağlam bir reçeteyle basılmıştır.**

- Bu, dört kolun **yapısal olarak eşdeğer olmadığı** anlamına gelir; quadcopter kollarının
  simetrik yük taşıması beklendiğinden bu bir **açık maddedir**.
- **Kayıtta bunun gerekçesi yoktur.** İki olasılık (reçete iyileştirmesi sonrası ilk iki kolun
  yeniden basılmamış olması, ya da kasıtlı bir asimetri) artefaktlardan ayırt edilemez.
- **BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı** — üretilmiş fiziksel kolların
  hangi plakadan geldiği (kol 1–2 mi, 3–4 mü) ve gerekirse kol 1–2'nin `Plaka2` reçetesiyle
  **yeniden basılıp basılmayacağı** kararı. Bu satır 5 Eylül envanterinde kapatılmalıdır.

### 4.3 🔴 Beyan ile artefaktın çeliştiği yer — ABS-CF

Kullanıcı beyanı (`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül): *"GPS çubuğu + ayaklar
**ABS beyaz**, kalanı **ABS-CF siyah**."* Ancak **hiçbir dilimleyici projesinde ABS-CF
profili yoktur**: sekiz plakanın yedisinde `filament_type` = `ABS` (profiller
`Bambu ABS @BBL X1C`, `Bambu ABS @BBL P2S`, `Generic ABS @BBL P2S`), sekizincisi `TPU`.
Üretilmiş G-code'un filament satırı da düz ABS'i gösterir:
`type="ABS" color="#000000" tray_info_idx="GFB00"`.

Bu rapor çelişkiyi **çözmez, kaydeder**: dilimleyici artefaktları ABS, beyan ABS-CF diyor.
**BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi** (makara etiketi /
fatura ile). Yapısal hesaplar hangi malzemeyle yapılacaksa (Bölüm 3), o malzemenin adı
buradan gelmelidir; iki farklı malzemeyle iki farklı mukavemet çıkar.

### 4.4 Ölçülmüş baskı süresi ve malzeme tüketimi — yalnız bir plaka için var

Depoda **tek bir plakanın dilimlenmiş G-code'u** saklanmıştır:
`Plaka4_Ust_Cerceve_plate_1.gcode.3mf`. Bu dosyadaki değerler doğrudan üretim çıktısıdır:

| büyüklük | değer | kaynak satır |
|---|---|---|
| Model baskı süresi | **1 sa 23 dk 00 sn** | `; model printing time: 1h 23m 0s` |
| Toplam tahmini süre (ısınma vb. dâhil) | **1 sa 30 dk 16 sn** | `; total estimated time: 1h 30m 16s` |
| Filament uzunluğu | **22 332,62 mm** (22,33 m) | `; total filament length [mm]` |
| Filament kütlesi | **55,86 g** | `; total filament weight [g]`; plaka üstverisi `weight="55.86"` |
| Dilimleyici tahmini süre (saniye) | **5 416 s** | `<metadata key="prediction" value="5416"/>` |
| İlk katman süresi | **700,95 s** | `<metadata key="first_layer_time" .../>` |

⚠ Aynı dosyada dilimleyicinin **3. seviye uyarısı** kayıtlıdır:
`bed_temperature_too_high_than_filament` (hata kodu `1000C001`) — tabla sıcaklığı seçilen
filamentin profiline göre yüksek bulunmuştur. Uyarı, baskının yapılmadığı anlamına gelmez;
**yapıştırma/çarpılma riski** açısından üretim tutanağına geçirilmelidir.
**BEYAN GEREKLİ (insan): bu uyarının basımda nasıl ele alındığı** (tabla sıcaklığı düşürüldü mü,
uyarı yok sayıldı mı) ve çıkan parçada çarpılma gözlenip gözlenmediği.

**Diğer yedi plakanın baskı süresi ve filament tüketimi ÖLÇÜLEMEDİ** — bu plakaların
dilimlenmiş G-code'u depoda yoktur, yalnız proje dosyaları vardır. Toplam baskı süresi ve
toplam filament kütlesi bu yüzden **hesaplanamaz**; tahmin yazılmamıştır.
**BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** — Bambu Studio'da her
`.3mf` yeniden dilimlenerek (aynı reçeteyle) tabloya işlenebilir; SGGS §5.4 "üretim süresi"
sütunu bunu ister.

### 4.5 Üretim revizyonu — PLA'dan ABS'ye geçiş

Depoda plakaların **iki kuşağı** durmaktadır. Eski kuşakta ayak ve GPS tutucu tek plakada ve
adı `Plaka6_**PLA**_Ayak_GPS.3mf`'tir (`dronesolid/Yeni klasör/files (1)/`, 23.08.2026 07:40).
Güncel kuşakta bu plaka ikiye ayrılmış ve **ABS** profilleriyle yeniden dilimlenmiştir
(`Plaka_Ayak.3mf`, `Plaka_GPS_Holder.3mf`, 23.08.2026 11:19–12:56). Ayrıca güncel kuşakta
**TPU taban pedi** (×4) yeni bir kalem olarak eklenmiştir.

Yani üretim sürecinde ölçülebilir iki revizyon vardır: **PLA → ABS** (ayak/GPS tutucu) ve
**TPU taban pedi eklenmesi** (iniş darbe sönümü). Bu revizyonlar Bölüm 2 §4'teki revizyon
listesini tamamlar.
**BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (ısı dayanımı, kırılganlık, saha
sıcaklığı vb.) — dosya adları geçişi kanıtlar, gerekçeyi kanıtlamaz.

---

## 5. Üretim sonrası ölçülmemişler — açıkça listelenir

SGGS §5.4'ün istediği sütunların bir kısmı bugün **doldurulamaz**. Uydurulmamıştır:

| istenen | durum |
|---|---|
| CAD model kütlesi (parça başına) | **BEYAN GEREKLİ (insan)** — depoda hesaplanmış değer yok |
| Üretim/teslim sonrası **ölçülen gerçek kütle** | **BEYAN GEREKLİ (insan)** — 5 Eylül envanterinde her parça tartılacak (`SAHA_HAZIRLIK_PLANI` §2.1) |
| Boyutsal tolerans / uyum ölçümü | **BEYAN GEREKLİ (insan)** — motor delik aralığı, kol geçmesi, dome oturması |
| İlave fikstür / tool ihtiyacı | **BEYAN GEREKLİ (insan)** — destek kullanılan üç plaka (kubbe, ayak, GPS tutucu) dışında kayıt yok |
| Karşılaşılan üretim zorlukları | Kısmen ölçüldü: tabla sıcaklığı uyarısı (§4.4); gerisi **BEYAN GEREKLİ (insan)** |
| Toplam basılan parça sayısı ve fire | **BEYAN GEREKLİ (insan)** — yeniden basım / atık kaydı yok |
| Montaj bağlantı elemanları (vida, somun, pul) dökümü | **BEYAN GEREKLİ (insan)** — BOM'da sarf kalemi olarak yer almalı (Bölüm 7) |

---

## 6. Montaj ve kablolama yordamı — üretim adımı olarak

Aviyonik entegrasyonu **5 Eylül 2026** günü yapılacaktır. Yordam önceden yazılmış, her adıma
**kabul ölçütü** bağlanmıştır; "yapıldı" demek için ölçüt karşılanmalıdır. Kaynak:
`SAHA_HAZIRLIK_PLANI_20260903.md` §2.1–2.3.

### 6.1 Envanter ve doğrulama (09:00)

| adım | kabul ölçütü / üretilecek kanıt |
|---|---|
| Kutu açılır; künye tablosu (§0.2) ile karşılaştırılır | eksik/fark listesi (tutanak) |
| **Her parça tartılır**, fotoğraflanır | tartı listesi — UHDR "gerçek kütle" sütununun kaynağı |
| Gövde kontrolü: kollar sıkı, ayaklar, kubbe, GPS çubuğu; motor delikleri 5008 ile uyumlu | fotoğraf; uyumsuzluk varsa **§4.2 kol reçetesi sorusu burada kapanır** |

### 6.2 Mekanik yerleşim (09:30–11:00) — pervanesiz

| adım | ölçüt |
|---|---|
| Motorlar kollara; vida boyu stator'a değmeyecek; **quad-X yerleşimi**: 1 sağ ön CCW, 2 sol arka CCW, 3 sol ön CW, 4 sağ arka CW | şema fotoğrafı |
| ESC'ler kollara; motor kabloları kısa ve burulmuş (EMI) | kablo boyu ölçümü |
| FCHUB-12S gövde ortasına; PM02 pil hattına | — |
| Pixhawk 6C ağırlık merkezine, **ok ileri**, damper/köpük üstünde, kablolar gergin değil | uçuşta `VIBE` **< 30** |
| M9N GNSS direk üstünde, ok ileri, güç hatlarından uzak | pusula ofseti **< 300** |
| Jetson Nano hava alan yerde, ısı emici açık; **HQ kamera nadir (tam aşağı)**, pervane kadrajda değil, şerit kablo kilitli | yerde çekilen kare temiz |
| SiK anteni dikey, gövde dışında, ESC'den **≥ 5 cm**; FS alıcısı anteni ayrı | RSSI |
| Pil yuvası kayışlı, CG ortada (iki parmak testi) | **CG ± 1 cm** |

### 6.3 Kablolama demeti üretimi (11:00–12:30) — pervanesiz, pil takılı DEĞİL

| hat | bağlantı | kabul ölçütü |
|---|---|---|
| Ana güç | pil (XT60/XT90) → **PM02** → **FCHUB-12S** → 4× ESC | polarite doğru; ohmmetre ile kısa devre yok |
| Pixhawk gücü | PM02 6-pin → `POWER1` | **5,1–5,3 V**; `BATT_MONITOR=4` |
| Jetson gücü | FCHUB pad → **5 V / 5 A UBEC** → Nano barrel jack (J25), **`J48` jumper takılı**, ortak GND | yük altında **5,0–5,2 V** |
| ESC sinyal | ESC PWM → `MAIN OUT 1–4` (motor sırasına göre) | pervanesiz motor testi |
| RC | FS-iA6B **iBUS** → Pixhawk `RCIN`/`PPM`; kumanda bind edilir | kanallar ekranda, uçlar 1000–2000 |
| Telemetri | SiK → `TELEM1` (JST-GH 6 pin, TX↔RX çapraz), 57600 | YKS'de HEARTBEAT |
| **Jetson ↔ Pixhawk** | `TELEM2` → Nano 40-pin **pin 10 RX / pin 8 TX / pin 6 GND** (3,3 V; **5 V hattı bağlanmaz**) | `mavlink_dogrula` HEARTBEAT `sysid=1` |
| Kamera | HQ kamera CSI → Nano CSI (mavi taraf dışa), kilit kapalı | `jetson-io` sonrası `nvarguscamerasrc` görüntü verir |
| Etiketleme + çekme testi | her konnektör etiketli | hiçbiri çıkmadı |
| **İlk güç** | pil takılır; LED / boot tonu; 60 s koku-ısı gözlemi | Pixhawk + Nano açıldı |

**Emniyet kuralı (üretim yordamının parçasıdır):** *pervaneler en son, pil en son*. Aracın tek
güç kesicisi **pil fişidir** (XT60/XT90); ayrı acil kesme anahtarı **yoktur**. Bu, şartname
Takımın kendi DDR gereksinimi REQ-25…31'e göre (şartname maddesi değil) final aracında kapatılması gereken bir **tasarım borcudur** (Bölüm 2 §4.1).

### 6.4 Kablaj hesabı — DDR taslağı, doğrulanmadı

DDR döneminde bir AWG/konnektör taslağı yazılmıştır (`navitas-teknofest/references/avionics_software.md`):
ana güç 40–50 A → 12 AWG / XT90; ESC→motor 30–40 A → 14 AWG; BEC çıkışı 5–8 A → 20 AWG;
Jetson 5 A @ 12 V → 20 AWG; Pixhawk 2 A @ 5 V → 24 AWG; veri hatları < 0,5 A → 26–28 AWG (JST-GH).
⚠ Bu tablo **sabit kanat konfigürasyonu için** ve **tahmini akımlarla** yazılmıştır (belgenin
kendi notu: *"Tüm değerler tahmini"*). Çoklu rotorda motor başına havada asılı akım 10–12 A,
tepe 30+ A beklenmektedir (kullanıcı beyanı) — **ölçülmedi**.
**BEYAN GEREKLİ (insan): gerçek kablo kesitleri ve konnektör tipleri** (5 Eylül'de kullanılan
kablo demeti üzerinden) ve **ölçülmüş akım değerleri** (ilk hover logunda `BATT_AMP`).

---

## 7. Uçuş kontrolcüsü yapılandırmasının üretimi

Mission Planner'da elle tıklanan bir değerin ne tutanağı ne testi olur. Bu yüzden Pixhawk
yapılandırması **dosya olarak üretilmiş** ve testle kilitlenmiştir.

| ürün | içerik | kilit |
|---|---|---|
| `config/pixhawk/arducopter_fda.param` | **31 parametre satırı**, her satırın üstünde NEDEN yorumu; değerler **ArduPilot Copter-4.5 kaynak kodundan** okundu | `tests/test_faz_b_pixhawk_sablon.py` — **12 test** |
| `config/pixhawk/fda_gorev.waypoints` | QGC WPL 110, **8 satır (0…7)**: HOME → `NAV_TAKEOFF` 32 m → 20×20 m karenin 4 köşesi → `NAV_LOITER_TIME` 60 s → `NAV_LAND` | aynı test dosyası; kare şekli testle kilitli |
| `config/pixhawk/README.md` | yükleme yordamı, sahada değişecek tek şeyler, **TEYİT listesi** | — |

**Bilerek verilmiş iki sapma ve gerekçesi:**
- Görev irtifası **32 m** seçilmiştir (şartname ≥ 30 m; 2 m baro/EKF payı). Üretim yazılımı
  30 m'nin altını `ASGARI_IRTIFA_ALTI` diye işaretler.
- Loiter **60 s** — YKS'ye canlı aktarım + iki aşamalı hakem onayı + ACK penceresi için.

**Süre bütçesi hesaplandı, tahmin edilmedi:** `.param` dosyasındaki hızlarla
(`WPNAV_SPEED` 3 m/s, `LAND_SPEED` 0,5 m/s) kötü-durum toplam **221,5 s ≤ 600 s**
(`SARTNAME_FDA_OPERASYON_SURESI_S`). Bu hesap testin içindedir, metne elle yazılmamıştır.

**Sahada teyit edilecek dört değer** (`config/pixhawk/README.md` §3 TEYİT listesi):
`BRD_SER2_RTSCTS=0`, `RC_PROTOCOLS=4` (iBUS), `BATT_FS_LOW_ACT`, `BATT_FS_CRT_ACT`.
Ayrıca kutudan çıkanla teyit edilecekler: `FRAME_CLASS=1`, `FRAME_TYPE` (X), `MOT_PWM_TYPE=0`,
`SYSID_THISMAV=1`, `SERIAL1`/`SERIAL2` (57600 MAVLink2), `SRx_POSITION` 4 Hz, `SRx_EXTRA3` 1 Hz,
`BATT_MONITOR=4`, `FENCE_ENABLE=1` + `FENCE_ALT_MAX 50`, `RTL_ALT 3500`, `LAND_SPEED 50`,
`FS_THR_ENABLE 1`, `FS_GCS_ENABLE 1`, `BATT_FS_LOW/CRT` (4S: 14,4 / 14,0 V), `ARMING_CHECK=1`.

**Üretim çıktısı olarak sahada alınacak kanıt:** yapılandırma bittikten sonra
`Save to file` → `config/pixhawk/arducopter_fda_20260905.param` → depoya işlenecektir.
Görev koordinatları **Adıyaman'da** girilecektir; şablon şu an Null Island'da (0°, 0°)
20 m'lik bir kare çizer ve **her koordinat yer tutucudur**.
**BEYAN GEREKLİ (insan): uçuş alanı gerçek koordinatları ve geofence poligonu.**

---

## 8. Görev bilgisayarı ve kamera entegrasyonu — üretim zinciri

Bu, projenin en kırılgan üretim adımıdır ve bu yüzden **tamamı önceden kurulmuş, çevrimdışı
çalışacak biçimde paketlenmiştir**.

### 8.1 Kısıt: kartın kendisi yığını dayatıyor

Görev bilgisayarı **Jetson Nano 4GB**'tır (DDR'de Orin NX'ti — Bölüm 2 §4.1). JetPack 4.6.x'in
sistem Python'u **3.6**'dır; depo `ultralytics` ister (Python ≥ 3.8). Bu yüzden üretim kararı:
Nano'da **ayrı bir Python 3.8 sanal ortamı** (`~/venv38`) kurulur ve paketler oraya konur.

### 8.2 Çevrimdışı paket üretimi (ölçüldü)

`scripts/nano_tekerlek_indir.py` ile PC'de gerçek indirme yapılmıştır:

| büyüklük | ölçülen |
|---|---|
| Çözümlenen paket | **14 / 14** (aarch64 · cp38 tekerlek) |
| İndirilen dosya | **51** |
| Toplam boyut | **246 MB** |
| Kaynak paketi (sdist) | **0** — hepsi hazır tekerlek |
| Sürümler | torch 2.4.1 (**CPU**), torchvision 0.19.1, ultralytics 8.4.118, onnxruntime 1.19.2, MAVProxy 1.8.70 |

Nano'da kurulum **tek komuttur**: `pip install --no-index --find-links . -r requirements_nano.txt`.
Belge ve tekerlek listesi testle kilitlidir: `tests/test_faz_b_nano_kurulum.py`.

### 8.3 🔴 Kapanmamış üretim riski — FPS kapısı

Üretim modeli **v36 = YOLOv8m-seg**'dir (nano değil). Nano **CPU**'da 512 girdi boyutunda
türetilmiş FPS kapısı **0,61 FPS** (p50 **ve** p95) tutturulamayabilir. Bu **ölçülmemiştir** ve
tahmin edilmemiştir.

- Denenecek sıra: (1) JetPack 4.6 / Py3.8 için **CUDA torch** topluluk tekerleği, (2)
  `onnxruntime` ile `.onnx` (CPU'da torch'tan hızlı olabilir), (3) CPU torch.
- **Eşik gevşetilmez.** Kapı düşerse "düştü" yazılır ve sebep deftere geçer.
- **TensorRT `.engine` bu kartta ÖLÇÜLEMEDİ sayılır**: `venv38` içinde `tensorrt` modülü yoktur
  (JetPack 4.6'nın TensorRT bağı sistem Python 3.6'ya bağlıdır). Uçuş **PT ya da ONNX** ile yapılır.
  Kayıt defterinde `.engine` türevlerinin sha256 alanları `DERLENINCE_YAZILIR` yer tutucusundadır
  ve yer tutucu **fail-closed reddedilir** — yani derlenmemiş bir motor sessizce üretime giremez.

### 8.4 Kamera yolu — iki Python'lu köprü

Nano'da CSI kamerası yalnız GStreamer `nvarguscamerasrc` ile açılır; ancak `venv38` içindeki
pip `opencv-python` tekerleği **GStreamer'sızdır**. Bu yüzden üretim çözümü **kamera köprüsüdür**:

```
RPi HQ (IMX477, CSI) → sistem python3.6 + sistem cv2 (GStreamer)
      → scripts/kamera_koprusu.py → HTTP/MJPEG :8080
      → rpi_inference --kaynak http://127.0.0.1:8080/video (venv38, pip cv2 + FFmpeg)
```

Köprü `/video` (MJPEG), `/kare.jpg` ve `/durum` (JSON) uçlarını sunar; kaynak düşerse
**fail-visible** davranır ve yeniden açmayı dener. Testler: köprü **7**, `jetson_baslat` **42**,
paket **18 dosya**. Yedek yol: **USB webcam (UVC)** → `--kaynak 0`.

⚠ **Kamera FOV'u ÖLÇÜLMEDİ.** Systemd biriminde bugün `--fov 78` yazılıdır; bu bir
**yapılandırma varsayılanıdır, ölçüm değildir**. Gerçek değer 5 Eylül'de `kamera_dogrula`
ile ölçülecektir. Ölçek (`mpp`) zinciri bu değere bağlı olduğu için ölçüm yapılmadan
üretim beyanı verilmez.

### 8.5 Güç ve veri hattı üretim kararları

| karar | gerekçe (ölçülmüş / belgelenmiş) |
|---|---|
| Jetson için **ayrı 5 V / 5 A UBEC** → barrel jack (J25) + `J48` jumper | FCHUB'ın 2 A BEC'i Nano'nun MAXN modunu besleyemez; micro-USB'den besleme MAXN'de çöker (kart belgesi) |
| Pixhawk ↔ Jetson **TELEM2 → 40-pin UART** (`/dev/ttyTHS1`), MAVLink2 57600 | Tek kablo, USB hub yok; yedek yol micro-USB → `/dev/ttyACM0` |
| 3,3 V mantık; **5 V hattı bağlanmaz** | Nano GPIO 3,3 V'tur |

---

## 9. Yazılım üretim hattı ve sürüm mühürleme

Yazılım da bir üretim kalemidir ve konfigürasyon yönetimi altındadır.

| ürün | ölçülen |
|---|---|
| Üretim modeli | `navitas-seg-v36-512`, imgsz 512, PyTorch, sha256 `1d1caca6…c46911` |
| Saha paketindeki model dosyaları | `navitas_seg_v36_best.pt` **54 788 636 B**, `navitas_seg_v36_best_512_fp16.onnx` **54 569 673 B** |
| Saha paketi aynası | **18 dosya senkron** (`scripts/jetson_paket_hazirla.py`) |
| Systemd birimleri | **6 adet**: çoğullayıcı, kamera köprüsü, `rpi_inference`, iniş yayıncısı, komut alıcısı, seri hub |
| Taşınabilir saha belleği | **405 dosya · 1,27 GB**, `MANIFEST.txt` her dosyanın sha256'sı + git HEAD ile (`scripts/bellek_hazirla.py`; fail-closed: zorunlu parça eksikse çıkış 3) |
| Genel kapı | **15/15 · 15/15** |
| Tam test paketi | **1896 test OK** (skipped 3) |

⚠ Depo içinde küçük bir tutarsızlık vardır: plan belgesi belleği **405 dosya**, kontrol kartı
**405 dosya** diye yazar (ikisi de 1,27 GB). Fark **DOĞRULANACAK** — `MANIFEST.txt` satır sayısı
hakemdir.

**Sürüm mühürü (üretim dondurma).** `scripts/surum_dondur.py` üretim kodunun ve model
dosyalarının kanonik özetini alıp `config/DONDURMA_KUNYESI.json` üretir; `--dogrula` mühürden
sonra herhangi bir dosyanın değişip değişmediğini söyler. Bugün mühür **basılmamıştır** ve
araç bunu doğru biçimde bildirir:

```text
[DONDURMA] DONDURULMADI: kunye yok (O:\navitas\config\DONDURMA_KUNYESI.json) - henuz muhur basilmadi
exit=3
```

Mühür **17 Eylül**'de basılacaktır; ondan sonra üretim kodu değişmez (zorunlu değişiklik =
defter kaydı + kapı + ayrı denetim).

---

## 10. Saha kurulum süreci ve üretim doğrulama kapıları

### 10.1 Tek komutla açılış — thazırlık bütçesi

Şartname §6.2 hazırlık süresini **15 dakika (900 s)** ile sınırlar. Bu yüzden her istasyon
**tek komutla** açılacak biçimde üretilmiştir; komut süreyi kendisi ölçüp yazar.

| istasyon | komut |
|---|---|
| YKS | `saha_baslat.py yks --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080` |
| YKS (SiK) | `saha_baslat.py yks --serial COM5 --baud 57600` |
| İKA | `saha_baslat.py ika --yks <YKS_IP>:5005` |
| İHA / Jetson | `jetson_baslat.sh` (systemd birimleri; `--kuru`, `--kapi`, `--durum`) |
| 21 Eylül görev kipi | YKS `--fda` ile açılır (paraşüt ve İKA kapalı, bütçe 10 dk) |

⚠ **thazırlık kronometresi henüz ölçülmedi.** "Kutudan Takım Hazır'a" süresi 5 Eylül'de
provada tutulacaktır (`SAHA_HAZIRLIK_PLANI` §2.6). Bugün için **ÖLÇÜLEMEDİ**.

### 10.2 Jetson açılışının kuru koşusu (PC'de, 2026-09-03)

`jetson_baslat.sh --kuru` PC'de koşturulduğunda birim komut satırlarını **doğru** üretmekte,
Jetson'a özgü yolların eksikliğini ise **fail-closed** bildirmektedir:

```text
navitas-cogullayici.service: mavproxy.py --master=/dev/ttyACM0 --baudrate 57600 --streamrate 8
    --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551 --out udp:127.0.0.1:14552
navitas-kamera-koprusu.service: /usr/bin/python3 .../scripts/kamera_koprusu.py --port 8080
navitas-rpi-inference.service: ... rpi_inference.py --camera --ekransiz --mavlink udp:127.0.0.1:14550
    --mav-sysid 1 --fov 78 --kaynak http://...
navitas-iha-inis-yayinci.service: ... --mavlink udp:127.0.0.1:14551 --sysid 1 --kanit-timeout 900
navitas-iha-komut-alici.service: ... --mavlink udp:127.0.0.1:14552 --sysid 1 --bind 0.0.0.0:5007
KURU SONUC: eksik (beyan: tam · [YOK]: 9) — gercek kosum DURUR (cikis 3)
```

Dokuz `[YOK]` satırının tamamı **Jetson'da bulunacak** yollardır (MAVProxy, `navitas` kullanıcısı,
`/dev/ttyACM0`, kopyalanacak dosyalar). PC'de çıkış **3** beklenen sonuçtur; asıl anlamı,
**eksik kurulumla gerçek koşumun başlamayacağıdır**.

### 10.3 Zincir kuru koşusu — 9 GEÇTİ / 1 SAHİPSİZ

`scripts/saha_kuru_kosu.py` (2026-09-03, CPU):

```text
GECTI 9 · DUSTU 0 · SAHIPSIZ 1 · ATLANDI 0
KOPUK HALKALAR (1): motor
```

Tek kopuk halka **`motor`**'dur: gerçek İKA motor sürücüsü henüz yoktur. Bu, FDA görev test
uçuşunu **etkilemez** (o uçuşta İKA yoktur) ama final için açık bir donanım kararıdır.
Geçen halkalar arasında üretim yolunun kendisi vardır: `rota GECTI (yol_no=2, 31 ms)`,
`aktarim GECTI` (`run_camera` kararı loopback İKA'ya `OPEN_ROUTE` yazdı), `telsiz halkasi GECTI`
(`{'open_route_alindi': True, 'heartbeat': 1, 'ack': ['ika']}`).

### 10.4 Yapısal doğrulama — çalışma tanımlı, sonuç paket dışında

Gövde için bir **SolidWorks Simulation statik çalışması** yapılmıştır
(`Drone_Frame-Static 1`): **48 990 düğüm · 27 391 eleman · 146 970 serbestlik derecesi**,
lineer analiz, iteratif çözücü, çözüm süresi **3 s**. Sabit kanat gövde/kanat/kuyruk parçası
için ikinci bir çalışma vardır (`Fuselage+Wing+Tail_CFD_Part2-Static 1`: 48 650 düğüm ·
28 656 eleman · 145 950 DOF, sparse çözücü, 2 s). Ayrıca bir **XFLR5** analiz dosyası
(`NAVITIAS_XFLR5_Analysis.xfl`, 905 868 B) pakette durur.

🔴 **Ama sonuçlar bu pakette yoktur.** Her iki çalışmanın sonuç veri tabanı (`.gsz`) yalnız
**33 ve 32 bayttır**; gerilme, deplasman ve emniyet katsayısı değerleri okunamaz. Dahası her iki
çözücü günlüğünde aynı uyarı vardır: *"significant external imbalanced force in Y-direction …
balanced by the application of opposing inertia forces"* — yani yük/mesnet kümesi dengede
değildi ve çözücü **atalet rahatlaması** uygulamıştır. Bu, sonucun karakterini değiştirebilecek
bir uyarıdır.

**Hüküm:** yapısal analiz **yapılmıştır ama bu paketten doğrulanamamaktadır** → sonuç
**ÖLÇÜLEMEDİ**. Sayısal sonuçlar Bölüm 3'e girecekse, çalışmalar yeniden çözülüp
gerilme/deplasman/emniyet katsayısı değerleri ekran görüntüsü ve rapor çıktısıyla eklenmelidir.
**BEYAN GEREKLİ (insan): FEM yük durumu, mesnet tanımı, malzeme kartı ve sonuç değerleri.**

### 10.5 Üretim kapıları özeti

| kapı | ne ölçer | durum (03.09.2026) |
|---|---|---|
| Genel kapı `codes/test_rota_sentetik.py` | karar zinciri | **15/15 · 15/15 GEÇTİ** |
| Tam test paketi | tüm sözleşmeler | **1896 OK** (skipped 3) |
| Kuru koşu | saha zinciri bütünlüğü | **9 GEÇTİ / 1 SAHİPSİZ** (`motor`) |
| Paket aynası | saha paketi ile depo eşitliği | **18 dosya senkron** |
| Çevrimdışı tekerlekler | Nano yığını | **14/14 · 51 dosya · 246 MB** |
| Pixhawk şablonu | parametre + görev planı | **12 test GEÇTİ** |
| Kamera köprüsü | CSI → MJPEG | **7 test GEÇTİ** |
| Nano kurulum belgesi | belge–betik tutarlılığı | test dosyası mevcut |
| Mühür | sürüm dondurma | **DONDURULMADI** (exit 3, beklenen; 17 Eylül) |
| **FPS kapısı ≥ 0,61** | Nano'da gerçek çıkarım hızı | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **Kamera FOV** | ölçek zincirinin girdisi | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **thazırlık ≤ 900 s** | saha kurulum süresi | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **Gerçek kütle / CG** | UHDR ve ağırlık limiti | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **FEM sonucu** | yapısal emniyet | **ÖLÇÜLEMEDİ** (§10.4) |
| **`.engine` (TensorRT)** | hızlandırma | **ÖLÇÜLEMEDİ** — Nano'da derlenemiyor (§8.3) |

---

## 11. Final (yarışma) aracının üretim planı

Sabit kanat + mancınık + paraşüt + İKA hattı **üretilmemiştir**. Bugünkü olgunluk:

| kalem | olgunluk (ölçülen) | üretim adımı |
|---|---|---|
| Gövde/kanat/kuyruk | **CAD var**: `Fuselage+Wing+Tail_CFD_Part.SLDPRT` (+ `-2-`, `-3-` sürümleri), `Left/Right_Aileron`, `Left/Right_Elevator`, `Rudder`; XFLR5 analiz dosyası | Kalıp/kesim yöntemi seçimi → prototip → yapısal test |
| Mancınık | Depoda CAD/analiz **yok** | Ray geometrisi, enerji hesabı, çift kademeli emniyet (REQ-58/59) |
| Paraşüt | Donanım DDR BOM'unda tanımlı, **temin/üretim kaydı yok**; yazılım tarafı hazır (`CHUTE_*`, `iha_komut_alici` zinciri) | Pod + servo mekanizması üretimi + atış testi |
| İKA | Yazılım soyutlaması hazır, **gerçek motor sürücüsü YOK** (kuru koşuda `motor SAHIPSIZ`) | Sürücü seçimi (donanım kararı) → `scripts/ika_surucu_kabul.py` kabul turu → şasi üretimi |
| Çift acil güç kesme | **Yok** (FDA aracında pil fişi) | DDR gereksinimi REQ-25…31 için anahtar + röle tasarımı ve üretimi |

**BEYAN GEREKLİ (insan): final aracı üretim takvimi ve atölye/tezgâh kaynakları** — 21 Eylül
sonrası açılacak dalga için tarih, sorumlu rol ve tedarik kalemleri.

---

## 12. Bu bölümdeki BEYAN GEREKLİ (insan) satırlarının toplu listesi

1. **BEYAN GEREKLİ (insan): tasarımın özgünlüğüne dair imzalı beyan** (§2).
2. **BEYAN GEREKLİ (insan): CAD birim/ölçek teyidi ve kolun gerçek boyu** (§3).
3. **BEYAN GEREKLİ (insan): parça başına CAD model kütlesi** (§3, §5).
4. **BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı; kol 1–2 yeniden basılacak mı** (§4.2).
5. **BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi (ABS mi ABS-CF mi)** (§4.3).
6. **BEYAN GEREKLİ (insan): tabla sıcaklığı uyarısının nasıl ele alındığı ve çarpılma gözlemi** (§4.4).
7. **BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** (§4.4) — yalnız üst çerçevenin verisi var.
8. **BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (§4.5).
9. **BEYAN GEREKLİ (insan): ölçülen gerçek kütleler, tolerans/uyum ölçümleri, fikstür ihtiyacı, fire kaydı** (§5).
10. **BEYAN GEREKLİ (insan): bağlantı elemanı (vida/somun/pul) dökümü** (§5).
11. **BEYAN GEREKLİ (insan): gerçek kablo kesitleri, konnektörler ve ölçülmüş akımlar** (§6.4).
12. **BEYAN GEREKLİ (insan): uçuş alanı koordinatları ve geofence poligonu** (§7).
13. **BEYAN GEREKLİ (insan): FEM yük/mesnet/malzeme tanımı ve sonuç değerleri** (§10.4).
14. **BEYAN GEREKLİ (insan): final aracı üretim takvimi ve kaynakları** (§11).

---

## 13. Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | STL üçgen sayıları, dosya boyutları, gabariler, sha256 | `dronesolid/*.STL` | bu bölümün kanıt betiği (ikili STL başlığı + köşe taraması), `O:\navitas-local-train\venv\Scripts\python.exe` | 2026-09-03 |
| 2 | STL dosya damgaları (23.08.2026 06:51–06:55) | `dronesolid/` | `ls -la dronesolid/` | 2026-09-03 |
| 3 | Plaka reçeteleri (malzeme, katman, dolgu, duvar, kabuk, destek, brim, yazıcı) | `dronesolid/files (3)/*.3mf` → `Metadata/project_settings.config` | zip okuma + JSON ayrıştırma | 2026-09-03 |
| 4 | Dilimleyici sürümü 02.07.01.62 | aynı `.3mf` → `Metadata/slice_info.config` | aynı | 2026-09-03 |
| 5 | Tabla izdüşüm alanları (kol 8 607,19 mm² vb.) | aynı `.3mf` → `Metadata/plate_1.json` | aynı | 2026-09-03 |
| 6 | Plaka nesne dağılımı (kol ×2 + ×2, ayak ×3 + ×1, GPS tutucu, TPU ped ×4) | aynı `.3mf` → `Metadata/model_settings.config` | aynı | 2026-09-03 |
| 7 | Üst çerçeve baskı süresi 1 sa 23 dk / 1 sa 30 dk 16 sn; 22 332,62 mm; **55,86 g** | `dronesolid/files (3)/Plaka4_Ust_Cerceve_plate_1.gcode.3mf` → `Metadata/plate_1.gcode` + `slice_info.config` | zip okuma | 2026-09-03 |
| 8 | Dilimleyici uyarısı `bed_temperature_too_high_than_filament` (kod `1000C001`) | aynı dosya → `slice_info.config` | aynı | 2026-09-03 |
| 9 | Eski plaka kuşağı `Plaka6_PLA_Ayak_GPS.3mf` (PLA → ABS revizyonu) | `dronesolid/Yeni klasör/files (1)/` | `ls -la` | 2026-09-03 |
| 10 | Yerel CAD parçaları + montaj + STEP ihraçları (dosya boyutlarıyla) | `dronesolid/NAVITAS-UAV-FDR-ZIP(Tamamlanmamis).zip` | zip listeleme | 2026-09-03 |
| 11 | FEM çalışmaları: 48 990 düğüm / 27 391 eleman / 146 970 DOF / 3 s; ikinci çalışma 48 650 / 28 656 / 145 950 / 2 s; atalet rahatlaması uyarısı; `.gsz` 33 ve 32 bayt | aynı zip → `*-Static 1.LOG`, `*.MFC`, `*.gsz` | zip okuma | 2026-09-03 |
| 12 | Montaj ve kablolama yordamı, kabul ölçütleri | `SAHA_HAZIRLIK_PLANI_20260903.md` §2.1–2.3 | — (plan belgesi) | 2026-09-03 |
| 13 | Pixhawk parametre dosyası **31 satır**; görev planı **8 satır**; 12 test | `config/pixhawk/arducopter_fda.param`, `fda_gorev.waypoints`, `README.md` | `grep -c "^[A-Z_0-9]*," …`; `tests/test_faz_b_pixhawk_sablon.py` | 2026-09-03 |
| 14 | Kötü-durum süre bütçesi 221,5 s ≤ 600 s | `config/pixhawk/README.md` §"Sıra ve süre bütçesi" | test içinde hesaplanır (P7) | 2026-09-03 |
| 15 | Çevrimdışı tekerlek: 14/14 paket · 51 dosya · 246 MB; sürüm listesi | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A; `wheels/INDIRME_RAPORU.txt` | `scripts/nano_tekerlek_indir.py` | 2026-09-03 |
| 16 | Nano yığını kararları (venv38, GStreamer'sız pip cv2, `.engine` yok, MAXN 10 W, J48) | `jetson_paket/JETSON_NANO_KURULUM.md` §0–§2 | — (belge, testle kilitli: `tests/test_faz_b_nano_kurulum.py`) | 2026-09-03 |
| 17 | Kamera köprüsü uçları ve test sayıları (köprü 7, `jetson_baslat` 42, paket 18) | `scripts/kamera_koprusu.py`, `SAHA_HAZIRLIK_PLANI_20260903.md` §1.4 | `tests/test_faz_b_kamera_koprusu.py` | 2026-09-03 |
| 18 | Systemd birim komut satırları, `--fov 78` varsayılanı, `[YOK]` 9 satır, exit 3 | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §6 | `jetson_paket/jetson_baslat.sh --kuru` | 2026-09-03 |
| 19 | Kuru koşu 9 GEÇTİ / 1 SAHİPSİZ, `rota GECTI yol_no=2 [31 ms]` | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §5 + `kuru_kosu/` | `scripts/saha_kuru_kosu.py` | 2026-09-03 |
| 20 | Mühür durumu `DONDURULMADI`, exit 3 | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §4 | `scripts/surum_dondur.py --dogrula` | 2026-09-03 |
| 21 | Model dosya boyutları (54 788 636 B / 54 569 673 B) ve paket aynası 18 dosya | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §2–3 | `scripts/jetson_paket_hazirla.py` | 2026-09-03 |
| 22 | Genel kapı 15/15 · 15/15; tam suit 1875 OK (skipped 3) | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §1; `CUMA_KONTROL_KARTI.md` §A | `codes/test_rota_sentetik.py`; `unittest discover -s tests -q` | 2026-09-03 |
| 23 | Saha belleği 405 dosya · 1,27 GB (plan belgesinde 405 — tutarsızlık) | `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A; `SAHA_HAZIRLIK_PLANI_20260903.md` §1.10 | `scripts/bellek_hazirla.py` | 2026-09-03 |
| 24 | Üretim modeli künyesi ve `.engine` yer tutucu reddi | `config/model_registry.json` | `codes/model_registry.py` | 2026-08-26 / 2026-09-01 |
| 25 | Saha açılış kartı komutları (thazırlık ≤ 900 s) | `results/faz_b_oncesi/saha_baslat_komutlar.txt`; `SAHA_RUNBOOK.md` §1 | `scripts/saha_baslat.py --komutlar` | 2026-09-03 |
| 26 | Kablaj/AWG taslağı (tahmini olduğu notuyla) | `navitas-teknofest/references/avionics_software.md` | — (DDR dönemi taslağı) | 2026-07 |
| 27 | Şartname §6 özgünlük ve ağırlık hükümleri; §6.2 hazırlık 15 dk | `results/sartname_bosluk/sartname_metin.txt` | PyMuPDF çıkarımı | 2026-08-26 |
