# Bölüm 5. Üretim Faaliyetleri (15 PUAN)

> **Bu bölümün yazım kuralı.** Aşağıdaki her sayı bir artefakttan gelir: dilimleyici proje
> dosyası, STL ikili başlığı, üretilmiş G-code, betik çıktısı ya da depo dosyası. Hangi
> dosyadan ve hangi komutla çıkarıldığı **§5.7 Kanıt dizini**'nde yazılıdır.
> **Ölçülmemiş hiçbir üretim değeri tahmin edilmemiştir**; ölçülmemiş olan "ÖLÇÜLEMEDİ" ya da
> **BEYAN GEREKLİ (insan)** diye yazılmıştır. Beyan ile artefaktın çeliştiği ya da kayıtla
> örtüşmediği üç yer vardır (§5.1.5 filament cinsi, §5.5.1 kol reçetesi, §5.2.8 bellek dosya
> sayısı); üçü de gizlenmeden, çelişkinin kendisi rapora yazılarak bırakılmıştır.

---

## Bu bölümün okunması — kapsam ve yönerge eşlemesi

### Hangi aracın üretimi anlatılıyor

Şartname §5.3.2 (FDA görev test uçuşu) **çoklu rotorlu** bir araç ister; şartname §6 (yarışma)
**sabit kanatlı** İHA + mancınık + paraşüt + İKA ister. Bunlar **iki ayrı fiziksel sistemdir**
ve üretim durumları farklıdır.

| | **FDA aracı — çoklu rotor** | **Yarışma aracı — sabit kanat + mancınık + paraşüt + İKA** |
|---|---|---|
| Üretim durumu (03.09.2026) | Gövde **basıldı ve monte edildi**; aviyonik kutuda, montaj **5 Eylül** | **Üretilmedi.** CAD parçaları var (§5.2.10), imalat başlamadı |
| Bu bölümdeki yeri | §5.1 – §5.5 (asıl anlatı) | §5.1.6 ve §5.2.10 (üretim planı) |

Bu bölüm ağırlıklı olarak FDA aracının **gerçekleşmiş** üretimini anlatır; §5.1.6 ve §5.2.10
final aracının üretim planını ve bugünkü olgunluk seviyesini verir.

### Yönergenin beş maddesi ve bu bölümdeki karşılıkları

Yönerge Bölüm 5 için **numaralı alt başlık vermez**; tek paragrafta beş husus ister. Aşağıdaki
beş alt başlık o beş cümleden **birebir** türetilmiştir (cümleler alt başlıkların altında
alıntıyla verilmiştir), yeni bir başlık şeması icat edilmemiştir.

| kimlik | yönergenin istediği | bu bölümde |
|---|---|---|
| `Y-5-M01` | tüm yapısal parçalar için olası **üretim yöntemleri** | §5.1 |
| `Y-5-M02` | seçilen yönteme göre **toplam imalat süresi** + **montaj planı** | §5.2 |
| `Y-5-M03` | her bir parça için **tahmini üretim süresi ve iş gücü ihtiyacı** | §5.3 |
| `Y-5-M04` | üretimde oluşabilecek **hatalar ve düzeltici işlem prosedürleri** | §5.4 |
| `Y-5-M05` | SGGS **tutarlılık kontrolü**; gerekliliği ispatlanmamış değişiklik = diskalifiye | §5.5 |

---

## Bölüm 5.1 — Tüm Yapısal Parçalar İçin Üretim Yöntemleri

> Yönerge (`Y-5-M01`): *"Final raporunda, tüm yapısal parçalar için olası üretim yöntemleri
> (kompozit yatırma, CNC işleme, sac şekillendirme, eklemeli imalat vb.) raporda belirtilmelidir."*

**Seçilen yöntem: eklemeli imalat (FDM / malzeme ekstrüzyonu).** FDA aracının **bütün yapısal
parçaları** — kol, üst çerçeve, alt çerçeve, kubbe, ayak, GNSS tutucu, TPU taban pedi — masaüstü
FDM yazıcılarda (Bambu Lab X1 Carbon ve Bambu Lab P2S, 0,4 mm nozul) basılmıştır. Kompozit
yatırma, CNC işleme ve sac şekillendirme FDA aracında **kullanılmamıştır**; final aracı için
yöntem seçimi henüz yapılmamıştır (§5.1.6).

### 5.1.1 Üretim mimarisi — üretilen / tedarik edilen ayrımı

Şartname §6: *"Yarışmaya dahil edilecek sistemlerin; tasarım, boyutlandırma ve imalat
süreçlerinin tamamının yarışmacı takımlar tarafından gerçekleştirilmesi esastır."*

| katman | üretim türü | kanıt |
|---|---|---|
| **Yapısal (gövde, kol, alt/üst çerçeve, kubbe, ayak, GPS tutucu, TPU ped)** | **Takım üretimi** — SolidWorks'te modellendi, dilimlendi, 3B basıldı | Yerel `.SLDPRT` + `.SLDASM` parça dosyaları, türetilmiş `.STEP` ve `.STL` ihraçları, Bambu Studio `.3mf` plaka projeleri (§5.1.3, §5.1.4) |
| **Aviyonik (uçuş kontrolcüsü, GNSS, ESC, motor, güç, telsiz, kamera, görev bilgisayarı)** | **Hazır satın alınan alt sistem** — entegrasyonu takım yapar | Künye `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2; BOM Bölüm 7 |
| **Kablolama demeti** | **Takım üretimi** (kesim, lehim, makaron, etiket) | Yordam §5.2.4; kabul ölçütleri tabloda |
| **Uçuş kontrolcüsü yapılandırması** | **Takım üretimi** — parametre ve görev planı dosyası olarak üretildi ve testle kilitlendi | `config/pixhawk/` (§5.2.6) |
| **Görev yazılımı ve model** | **Takım üretimi** | `config/model_registry.json`, `tests/` (§5.2.8) |
| **Görev bilgisayarı sistem imajı** | **Takım kurulumu** — tedarikçi imajı üzerine çevrimdışı yığın | `jetson_paket/JETSON_NANO_KURULUM.md` (§5.2.7) |

### 5.1.2 Özgünlük kanıtı (§6 intihal hükmü karşısında)

Depoda parçaların **yerel SolidWorks kaynak dosyaları** durmaktadır — `Drone_Arm.SLDPRT`
(134 593 B), `Drone_Frame.SLDPRT` (161 748 B), `Lower_Drone_Frame.SLDPRT` (87 210 B),
`Drone_Dome.SLDPRT` (2 310 497 B), `Drone_Legs.SLDPRT` (204 294 B), `GPS_Holder.SLDPRT`
(153 510 B) ve bunları birleştiren `Drone_Assembly.SLDASM` (484 241 B) — ayrıca üç parçanın
nötr `.STEP` ihracı ve gövde için **çözülmüş bir sonlu elemanlar çalışması** (§5.6/E1). Rapora
giren STL'ler bu parçaların ihraçlarıdır; adları birebir eşleşir. Kaynak parametrik model +
montaj + analiz zincirinin bir arada bulunması, geometrinin hazır bir ticari platformdan
alınmadığının **belge düzeyinde** kanıtıdır.
**BEYAN GEREKLİ (insan): tasarımın takım üyelerince özgün olarak modellendiğine dair imzalı
beyan** — dosyaların varlığı yazarlığı kanıtlar ama beyan yerine geçmez.

### 5.1.3 CAD künyesi — üretime giren ölçülen geometri

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

### 5.1.4 Eklemeli imalat reçeteleri — plaka plaka ölçüldü

Üretim, **Bambu Studio** ile plaka plaka dilimlenmiş ve `.3mf` proje dosyaları saklanmıştır.
Aşağıdaki tablo bu proje dosyalarındaki `Metadata/project_settings.config` alanlarından
**okunmuştur** — hiçbiri elle yazılmamıştır.

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

⚠ İki kol plakasının reçeteleri birbirinden farklıdır ve bu farkın kayıtta gerekçesi yoktur.
Yönerge bu bölüm için **gerekliliği ispatlanmamış değişikliği diskalifiye sebebi** saydığından
bulgu **§5.5.1**'de ayrı ve öne çıkarılmış olarak işlenmiştir.

### 5.1.5 🔴 Malzeme — beyan ile artefaktın çeliştiği yer (ABS / ABS-CF)

Takım beyanı (`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül): *"GPS çubuğu + ayaklar
**ABS beyaz**, kalanı **ABS-CF siyah**."* Ancak **hiçbir dilimleyici projesinde ABS-CF
profili yoktur**: sekiz plakanın yedisinde `filament_type` = `ABS` (profiller
`Bambu ABS @BBL X1C`, `Bambu ABS @BBL P2S`, `Generic ABS @BBL P2S`), sekizincisi `TPU`.
Üretilmiş G-code'un filament satırı da düz ABS'i gösterir:
`type="ABS" color="#000000" tray_info_idx="GFB00"`.

Bu rapor çelişkiyi **çözmez, kaydeder**: dilimleyici artefaktları ABS, beyan ABS-CF diyor.
**BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi** (makara etiketi /
fatura ile). Yapısal hesaplar hangi malzemeyle yapılacaksa (Bölüm 3), o malzemenin adı
buradan gelmelidir; iki farklı malzemeyle iki farklı mukavemet çıkar.

### 5.1.6 Final (yarışma) aracı için üretim yöntemi — henüz seçilmedi

Sabit kanat gövde/kanat/kuyruk için depoda **CAD vardır**
(`Fuselage+Wing+Tail_CFD_Part.SLDPRT` ve `-2-`, `-3-` sürümleri; `Left/Right_Aileron`,
`Left/Right_Elevator`, `Rudder`; `NAVITIAS_XFLR5_Analysis.xfl` 905 868 B) ama **üretim yöntemi
seçilmemiştir**: kompozit yatırma mı, sıcak tel köpük kesim mi, eklemeli imalat mı olacağı
kayıtta yoktur. Mancınık için depoda **CAD/analiz dosyası yoktur**.
**BEYAN GEREKLİ (insan): final aracı yapısal parçaları için seçilecek üretim yöntemi**
(gövde/kanat/kuyruk ve mancınık ayrı ayrı) ve seçimin dayanağı. Olgunluk tablosu ve üretim
adımları §5.2.10'dadır.

---

## Bölüm 5.2 — Toplam İmalat Süresi ve Montaj Planı

> Yönerge (`Y-5-M02`): *"Seçilen üretim yöntemine göre toplam imalat süresi tahmin edilmeli ve
> buna bağlı bir montaj planı hazırlanmalıdır."*

### 5.2.1 Toplam imalat süresi — bugün hesaplanamıyor

Sekiz plakadan **yalnız birinin** dilimlenmiş G-code'u depodadır; kalan yedisinin baskı süresi
**ÖLÇÜLEMEDİ** (ayrıntı ve tek ölçülen plakanın değerleri §5.3.1–§5.3.2). Bu yüzden
**toplam imalat süresi tahmin edilmemiştir** — yönergenin istediği toplam, yedi eksik ölçüm
kapatıldığında §5.3.2'deki tablodan toplanarak yazılacaktır. Tahmin yazmak yerine boşluk
bırakılmıştır.
**ÖLÇÜLEMEDİ: FDA aracının toplam 3B baskı süresi** — sekiz plakadan yedisinin G-code'u
üretilmedi; her `.3mf` Bambu Studio'da aynı reçeteyle yeniden dilimlendiğinde kapanır.

Montaj tarafının süresi ise planlanmıştır: aviyonik entegrasyonu **5 Eylül 2026** günü
**09:00–12:30** aralığına bölünmüştür (§5.2.2–§5.2.4). Saha kurulumunun süre bütçesi ayrıdır ve
§5.2.9'da verilmiştir.

### 5.2.2 Montaj planı A — envanter ve doğrulama (5 Eylül, 09:00)

Aviyonik entegrasyonu **5 Eylül 2026** günü yapılacaktır. Yordam önceden yazılmış, her adıma
**kabul ölçütü** bağlanmıştır; "yapıldı" demek için ölçüt karşılanmalıdır. Kaynak:
`SAHA_HAZIRLIK_PLANI_20260903.md` §2.1–2.3.

| adım | kabul ölçütü / üretilecek kanıt |
|---|---|
| Kutu açılır; künye tablosu (§0.2) ile karşılaştırılır | eksik/fark listesi (tutanak) |
| **Her parça tartılır**, fotoğraflanır | tartı listesi — UHDR "gerçek kütle" sütununun kaynağı |
| Gövde kontrolü: kollar sıkı, ayaklar, kubbe, GPS çubuğu; motor delikleri 5008 ile uyumlu | fotoğraf; uyumsuzluk varsa **§5.5.1 kol reçetesi sorusu burada kapanır** |

### 5.2.3 Montaj planı B — mekanik yerleşim (09:30–11:00), pervanesiz

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

### 5.2.4 Montaj planı C — kablolama demeti üretimi (11:00–12:30), pervanesiz, pil takılı DEĞİL

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
güç kesicisi **pil fişidir** (XT60/XT90); ayrı acil kesme anahtarı **yoktur**. Bu bir şartname
maddesi değil, takımın kendi DDR gereksinimi REQ-25…31'e göre final aracında kapatılması gereken
bir **tasarım borcudur** (Bölüm 2 §2.2.5.1).

### 5.2.5 Kablaj hesabı — DDR taslağı, doğrulanmadı

DDR döneminde bir AWG/konnektör taslağı yazılmıştır (`navitas-teknofest/references/avionics_software.md`):
ana güç 40–50 A → 12 AWG / XT90; ESC→motor 30–40 A → 14 AWG; BEC çıkışı 5–8 A → 20 AWG;
Jetson 5 A @ 12 V → 20 AWG; Pixhawk 2 A @ 5 V → 24 AWG; veri hatları < 0,5 A → 26–28 AWG (JST-GH).
⚠ Bu tablo **sabit kanat konfigürasyonu için** ve **tahmini akımlarla** yazılmıştır (belgenin
kendi notu: *"Tüm değerler tahmini"*). Çoklu rotorda motor başına havada asılı akım 10–12 A,
tepe 30+ A beklenmektedir (takım beyanı) — **ölçülmedi**.
**BEYAN GEREKLİ (insan): gerçek kablo kesitleri ve konnektör tipleri** (5 Eylül'de kullanılan
kablo demeti üzerinden) ve **ölçülmüş akım değerleri** (ilk hover logunda `BATT_AMP`).

### 5.2.6 Montaj planı D — uçuş kontrolcüsü yapılandırmasının üretimi ve yüklenmesi

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

### 5.2.7 Montaj planı E — görev bilgisayarı ve kamera entegrasyonu

Bu, projenin en kırılgan üretim adımıdır ve bu yüzden **tamamı önceden kurulmuş, çevrimdışı
çalışacak biçimde paketlenmiştir**.

**Kısıt: kartın kendisi yığını dayatıyor.** Görev bilgisayarı **Jetson Nano 4GB**'tır (DDR'de
Orin NX'ti — Bölüm 2 §2.2.5.1). JetPack 4.6.x'in sistem Python'u **3.6**'dır; depo `ultralytics`
ister (Python ≥ 3.8). Bu yüzden üretim kararı: Nano'da **ayrı bir Python 3.8 sanal ortamı**
(`~/venv38`) kurulur ve paketler oraya konur.

**Çevrimdışı paket üretimi (ölçüldü).** `scripts/nano_tekerlek_indir.py` ile PC'de gerçek
indirme yapılmıştır:

| büyüklük | ölçülen |
|---|---|
| Çözümlenen paket | **14 / 14** (aarch64 · cp38 tekerlek) |
| İndirilen dosya | **51** |
| Toplam boyut | **246 MB** |
| Kaynak paketi (sdist) | **0** — hepsi hazır tekerlek |
| Sürümler | torch 2.4.1 (**CPU**), torchvision 0.19.1, ultralytics 8.4.118, onnxruntime 1.19.2, MAVProxy 1.8.70 |

Nano'da kurulum **tek komuttur**: `pip install --no-index --find-links . -r requirements_nano.txt`.
Belge ve tekerlek listesi testle kilitlidir: `tests/test_faz_b_nano_kurulum.py`.

**🔴 Kapanmamış üretim riski — FPS kapısı.** Üretim modeli **v36 = YOLOv8m-seg**'dir (nano
değil). Nano **CPU**'da 512 girdi boyutunda türetilmiş FPS kapısı **0,61 FPS** (p50 **ve** p95)
tutturulamayabilir. Bu **ölçülmemiştir** ve tahmin edilmemiştir.

- Denenecek sıra: (1) JetPack 4.6 / Py3.8 için **CUDA torch** topluluk tekerleği, (2)
  `onnxruntime` ile `.onnx` (CPU'da torch'tan hızlı olabilir), (3) CPU torch.
- **Eşik gevşetilmez.** Kapı düşerse "düştü" yazılır ve sebep deftere geçer.
- **TensorRT `.engine` bu kartta ÖLÇÜLEMEDİ sayılır**: `venv38` içinde `tensorrt` modülü yoktur
  (JetPack 4.6'nın TensorRT bağı sistem Python 3.6'ya bağlıdır). Uçuş **PT ya da ONNX** ile yapılır.
  Kayıt defterinde `.engine` türevlerinin sha256 alanları `DERLENINCE_YAZILIR` yer tutucusundadır
  ve yer tutucu **fail-closed reddedilir** — yani derlenmemiş bir motor sessizce üretime giremez.

**Kamera yolu — iki Python'lu köprü.** Nano'da CSI kamerası yalnız GStreamer
`nvarguscamerasrc` ile açılır; ancak `venv38` içindeki pip `opencv-python` tekerleği
**GStreamer'sızdır**. Bu yüzden üretim çözümü **kamera köprüsüdür**:

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
**ÖLÇÜLEMEDİ: kamera gerçek FOV'u** — 5 Eylül'de `kamera_dogrula` ile kapanır.

**Güç ve veri hattı üretim kararları:**

| karar | gerekçe (ölçülmüş / belgelenmiş) |
|---|---|
| Jetson için **ayrı 5 V / 5 A UBEC** → barrel jack (J25) + `J48` jumper | FCHUB'ın 2 A BEC'i Nano'nun MAXN modunu besleyemez; micro-USB'den besleme MAXN'de çöker (kart belgesi) |
| Pixhawk ↔ Jetson **TELEM2 → 40-pin UART** (`/dev/ttyTHS1`), MAVLink2 57600 | Tek kablo, USB hub yok; yedek yol micro-USB → `/dev/ttyACM0` |
| 3,3 V mantık; **5 V hattı bağlanmaz** | Nano GPIO 3,3 V'tur |

### 5.2.8 Montaj planı F — yazılım üretim hattı ve sürüm mühürleme

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
defter kaydı + kapı + ayrı denetim). Bu mühür aynı zamanda §5.5.3'teki değişiklik-gerekçe
disiplininin **teknik dayanağıdır**.

### 5.2.9 Saha kurulumu ve montaj sonrası doğrulama kapıları

**Tek komutla açılış — t_hazırlık bütçesi.** Şartname §6.2 hazırlık süresini **15 dakika (900 s)**
ile sınırlar. Bu yüzden her istasyon **tek komutla** açılacak biçimde üretilmiştir; komut süreyi
kendisi ölçüp yazar.

| istasyon | komut |
|---|---|
| YKS | `saha_baslat.py yks --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080` |
| YKS (SiK) | `saha_baslat.py yks --serial COM5 --baud 57600` |
| İKA | `saha_baslat.py ika --yks <YKS_IP>:5005` |
| İHA / Jetson | `jetson_baslat.sh` (systemd birimleri; `--kuru`, `--kapi`, `--durum`) |
| 21 Eylül görev kipi | YKS `--fda` ile açılır (paraşüt ve İKA kapalı, bütçe 10 dk) |

⚠ **t_hazırlık kronometresi henüz ölçülmedi.** "Kutudan Takım Hazır'a" süresi 5 Eylül'de
provada tutulacaktır (`SAHA_HAZIRLIK_PLANI` §2.6). Bugün için **ÖLÇÜLEMEDİ**.

**Jetson açılışının kuru koşusu (PC'de, 2026-09-03).** `jetson_baslat.sh --kuru` PC'de
koşturulduğunda birim komut satırlarını **doğru** üretmekte, Jetson'a özgü yolların eksikliğini
ise **fail-closed** bildirmektedir:

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

**Zincir kuru koşusu — 9 GEÇTİ / 1 SAHİPSİZ.** `scripts/saha_kuru_kosu.py` (2026-09-03, CPU):

```text
GECTI 9 · DUSTU 0 · SAHIPSIZ 1 · ATLANDI 0
KOPUK HALKALAR (1): motor
```

Tek kopuk halka **`motor`**'dur: gerçek İKA motor sürücüsü henüz yoktur. Bu, FDA görev test
uçuşunu **etkilemez** (o uçuşta İKA yoktur) ama final için açık bir donanım kararıdır.
Geçen halkalar arasında üretim yolunun kendisi vardır: `rota GECTI (yol_no=2, 31 ms)`,
`aktarim GECTI` (`run_camera` kararı loopback İKA'ya `OPEN_ROUTE` yazdı), `telsiz halkasi GECTI`
(`{'open_route_alindi': True, 'heartbeat': 1, 'ack': ['ika']}`).

**Üretim kapıları özeti:**

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
| **t_hazırlık ≤ 900 s** | saha kurulum süresi | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **Gerçek kütle / CG** | UHDR ve ağırlık limiti | **ÖLÇÜLEMEDİ** — 5 Eylül |
| **FEM sonucu** | yapısal emniyet | **ÖLÇÜLEMEDİ** (§5.6/E1) |
| **`.engine` (TensorRT)** | hızlandırma | **ÖLÇÜLEMEDİ** — Nano'da derlenemiyor (§5.2.7) |

### 5.2.10 Final (yarışma) aracının üretim ve montaj planı

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
**BEYAN GEREKLİ (insan): final aracı için toplam imalat süresi tahmini ve montaj planı** —
yöntem seçilmeden (§5.1.6) süre tahmini yazılamaz; tahmin yazılmamıştır.

---

## Bölüm 5.3 — Her Bir Parça İçin Tahmini Üretim Süresi ve İş Gücü İhtiyacı

> Yönerge (`Y-5-M03`): *"Her bir parça için tahmini üretim süresi ve iş gücü ihtiyacı
> hesaplanmalıdır."*

### 5.3.1 Ölçülen tek veri — üst çerçeve plakası

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

### 5.3.2 Diğer yedi plaka — ölçülmedi, tahmin de yazılmadı

**Diğer yedi plakanın baskı süresi ve filament tüketimi ÖLÇÜLEMEDİ** — bu plakaların
dilimlenmiş G-code'u depoda yoktur, yalnız proje dosyaları vardır. Toplam baskı süresi ve
toplam filament kütlesi bu yüzden **hesaplanamaz**; tahmin yazılmamıştır.
**BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** — Bambu Studio'da her
`.3mf` yeniden dilimlenerek (aynı reçeteyle) tabloya işlenebilir; SGGS §5.4 "üretim süresi"
sütunu bunu ister.

Doldurulacak tablonun iskeleti (bugün yalnız ilk satırı doludur):

| plaka | baskı süresi | filament kütlesi | durum |
|---|---|---|---|
| `Plaka4_Ust_Cerceve.3mf` | 1 sa 23 dk 00 sn (model) / 1 sa 30 dk 16 sn (toplam) | 55,86 g | **ölçüldü** (§5.3.1) |
| `Plaka1_Kol_1-2.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `Plaka2_Kol_3-4.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `Plaka3_Alt_Cerceve.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `Plaka5_Kubbe.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `Plaka_Ayak.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `Plaka_GPS_Holder.3mf` | — | — | **ÖLÇÜLEMEDİ** |
| `tpu_taban_pedi_x4.3mf` | — | — | **ÖLÇÜLEMEDİ** |

### 5.3.3 İş gücü ihtiyacı — hiç kaydedilmemiş

Yönerge parça başına **iş gücü ihtiyacı** da ister. Depoda ne adam-saat kaydı, ne operatör
görev dağılımı, ne de destek temizleme / son işlem süresi vardır. Baskı süresi makine süresidir;
iş gücü süresi değildir ve makine süresinden türetilmemiştir.
**BEYAN GEREKLİ (insan): parça başına iş gücü ihtiyacı (rol ve adam-saat)** — plaka yükleme,
destek temizleme, çapak alma, delik açma/rayba, montaj öncesi kontrol adımları ayrı ayrı.
Destek kullanılan üç plaka (kubbe, ayak, GPS tutucu — §5.1.4) için son işlem süresi ayrıca
istenmelidir.

### 5.3.4 Üretim sonrası ölçülmemiş kalemler — açıkça listelenir

SGGS §5.4'ün istediği sütunların bir kısmı bugün **doldurulamaz**. Uydurulmamıştır:

| istenen | durum |
|---|---|
| CAD model kütlesi (parça başına) | **BEYAN GEREKLİ (insan)** — depoda hesaplanmış değer yok |
| Üretim/teslim sonrası **ölçülen gerçek kütle** | **BEYAN GEREKLİ (insan)** — 5 Eylül envanterinde her parça tartılacak (`SAHA_HAZIRLIK_PLANI` §2.1) |
| Boyutsal tolerans / uyum ölçümü | **BEYAN GEREKLİ (insan)** — motor delik aralığı, kol geçmesi, dome oturması |
| İlave fikstür / tool ihtiyacı | **BEYAN GEREKLİ (insan)** — destek kullanılan üç plaka (kubbe, ayak, GPS tutucu) dışında kayıt yok |
| Karşılaşılan üretim zorlukları | Kısmen ölçüldü: tabla sıcaklığı uyarısı (§5.4.2); gerisi **BEYAN GEREKLİ (insan)** |
| Toplam basılan parça sayısı ve fire | **BEYAN GEREKLİ (insan)** — yeniden basım / atık kaydı yok |
| Montaj bağlantı elemanları (vida, somun, pul) dökümü | **BEYAN GEREKLİ (insan)** — BOM'da sarf kalemi olarak yer almalı (Bölüm 7) |

---

## Bölüm 5.4 — Üretimde Oluşabilecek Hatalar ve Düzeltici İşlem Prosedürleri

> Yönerge (`Y-5-M04`): *"Üretim sırasında oluşabilecek hatalar ve bunlara yönelik düzeltici
> işlem prosedürleri tanımlanmalıdır."*

### 5.4.1 Bugünkü durum — prosedür YAZILMAMIŞTIR

Bu madde için depoda **hiçbir belge yoktur**: ne hata modu listesi, ne kabul/ret ölçütü, ne de
düzeltici işlem yordamı. Yönerge haritasındaki durumu `Y-5-M04` = **YOK**'tur ve bu rapor onu
"var" göstermez. Aşağıda yalnız **artefakta bağlı hata sinyalleri** listelenmiştir; bunlara
karşılık gelen düzeltici işlem yordamları **yazılacaktır**.

**BEYAN GEREKLİ (insan): üretim hata modu listesi ve düzeltici işlem prosedürleri** — her hata
modu için (a) tespit yöntemi, (b) kabul/ret ölçütü, (c) düzeltici işlem, (d) yeniden basım
kararını verecek rol, (e) kaydın tutulacağı yer. Bu, §5.5'teki SGGS tutarlılık kontrolünün
girdisidir: düzeltici işlemle yapılan her değişikliğin gerekçesi de kayda geçmelidir.

### 5.4.2 Artefakta bağlı hata sinyalleri (bugün elde olan)

| # | sinyal | kanıt (artefakt) | işaret ettiği hata | düzeltici işlem |
|---|---|---|---|---|
| H1 | Dilimleyici **3. seviye uyarısı** `bed_temperature_too_high_than_filament` (hata kodu `1000C001`) | `Plaka4_Ust_Cerceve_plate_1.gcode.3mf` → `slice_info.config` | tabla sıcaklığı seçilen filament profiline göre yüksek → **yapıştırma/çarpılma riski** | **BEYAN GEREKLİ (insan)** |
| H2 | Üç plakada `support` = **var** (kubbe, ayak, GPS tutucu) | §5.1.4 reçete tablosu | destek izi, yüzey bozulması, destek temizleme hasarı | **BEYAN GEREKLİ (insan)** |
| H3 | Kol 1–2 ile kol 3–4 **farklı reçete** | §5.1.4 ve §5.5.1 | dört kolun yapısal olarak eşdeğer olmaması | **BEYAN GEREKLİ (insan)** — §5.5.1 |
| H4 | Montaj kabul ölçütü: "motor delikleri 5008 ile uyumlu" | `SAHA_HAZIRLIK_PLANI_20260903.md` §2.1 | boyutsal sapma / delik uyumsuzluğu | **BEYAN GEREKLİ (insan)** — uyumsuzlukta rayba mı, yeniden basım mı |
| H5 | Fire / yeniden basım kaydı **yok** | §5.3.4 | başarısız baskıların izlenmemesi | **BEYAN GEREKLİ (insan)** |

H1 için ek not: uyarı, baskının yapılmadığı anlamına gelmez; **yapıştırma/çarpılma riski**
açısından üretim tutanağına geçirilmelidir.
**BEYAN GEREKLİ (insan): bu uyarının basımda nasıl ele alındığı** (tabla sıcaklığı düşürüldü mü,
uyarı yok sayıldı mı) ve çıkan parçada çarpılma gözlenip gözlenmediği.

### 5.4.3 Kapanma yolu

H1–H5 satırlarının düzeltici işlem sütunu **5 Eylül envanterinde** (§5.2.2) fiziksel parçalar
elde tutularak doldurulabilir: çarpılma gözlemi, destek izi, delik uyumu ve kol kimliği o gün
görülecektir. O tarihe kadar bu alt bölüm **açık** kalır ve "geçti" sayılmaz.

---

## Bölüm 5.5 — Değişikliklerin Gerekçelendirilmesi (SGGS Tutarlılık Kontrolü)

> Yönerge (`Y-5-M05`): *"Bu bölümde belirtilen hususlar için Şubat 2027'de gerçekleşecek
> Sistem Gözden Geçirme Sunumu'nda tutarlılık kontrolü yapılacaktır. **Gerekliliği
> ispatlanmamış değişiklikler diskalife sebebi sayılabilecektir.**"*

Bu madde bir belgeleme isteği değil, bir **diskalifiye şartıdır**. Aşağıda depodaki her
üretim değişikliği, **gerekçesinin kayıtta olup olmadığıyla birlikte** verilmiştir. Gerekçesi
olmayan değişiklik gizlenmemiş, ilk sıraya konmuştur.

### 5.5.1 🔴 AÇIK DİSKALİFİYE RİSKİ — dört kol iki farklı reçeteyle basıldı, gerekçe kayıtta YOK

**Bulgu.** `Plaka1_Kol_1-2.3mf` (kol 1–2) ile `Plaka2_Kol_3-4.3mf` (kol 3–4) reçeteleri
**birbirinden farklıdır** ve fark mukavemet yönündedir:

| parametre | `Plaka1_Kol_1-2` (kol 1–2) | `Plaka2_Kol_3-4` (kol 3–4) |
|---|---|---|
| katman yüksekliği | 0,20 mm | **0,16 mm** |
| dolgu | %15 **grid** | **%40 gyroid** |
| duvar sayısı | 2 | **6** |
| üst / alt kabuk | 5 / 3 | **7 / 7** |
| brim | auto | outer_only |
| yazıcı alanı | Bambu Lab X1 Carbon 0,4 | *(kayıtta yazıcı alanı yok)* |

Yani **kol 3 ve kol 4, kol 1 ve kol 2'den belirgin biçimde daha sağlam bir reçeteyle
basılmıştır.**

**Neden risk.**
- Bu, dört kolun **yapısal olarak eşdeğer olmadığı** anlamına gelir; quadcopter kollarının
  simetrik yük taşıması beklendiğinden bu bir **açık maddedir**.
- Bir yapısal parçanın reçetesinin değiştirilmesi, yönergenin diliyle bir **değişikliktir**;
  değişikliğin **gerekliliği ispatlanmamışsa** SGGS'de diskalifiye sebebi sayılabilir.
- **Kayıtta bunun gerekçesi yoktur.** İki olasılık (reçete iyileştirmesi sonrası ilk iki kolun
  yeniden basılmamış olması, ya da kasıtlı bir asimetri) artefaktlardan ayırt edilemez.
- Yapısal analiz bu soruyu bugün çözemez: gövde FEM çalışmasının sonuç veri tabanı okunamaz
  durumdadır (§5.6/E1), dolayısıyla "iki reçete de yeter" denecek sayısal dayanak yoktur.

**Kapanmazsa ne olur.** Şubat 2027 SGGS'de reçete farkı görülür ve gerekçe sunulamazsa
madde `Y-5-M05` kapsamında **diskalifiye gerekçesi** olarak değerlendirilebilir. Ayrıca dört kol
eşdeğer değilse Bölüm 3'ün yapısal iddiaları ve Bölüm 6'nın uygunluk beyanı da dayanaksız kalır.

**BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı** — üretilmiş fiziksel kolların
hangi plakadan geldiği (kol 1–2 mi, 3–4 mü), reçete değişikliğinin **teknik gerekçesi**, ve
gerekirse kol 1–2'nin `Plaka2` reçetesiyle **yeniden basılıp basılmayacağı** kararı. Bu satır
5 Eylül envanterinde (§5.2.2) kapatılmalıdır; kapanma iki yoldan biriyle olur:
(a) dört kolun da `Plaka2` reçetesiyle basıldığı belgelenir, ya da (b) fark kabul edilip
**gerekçesi yazılır** ve gerekiyorsa kol 1–2 yeniden basılır.

### 5.5.2 Ölçülmüş diğer üretim revizyonları ve gerekçe durumu

Depoda plakaların **iki kuşağı** durmaktadır. Eski kuşakta ayak ve GPS tutucu tek plakada ve
adı `Plaka6_**PLA**_Ayak_GPS.3mf`'tir (`dronesolid/Yeni klasör/files (1)/`, 23.08.2026 07:40).
Güncel kuşakta bu plaka ikiye ayrılmış ve **ABS** profilleriyle yeniden dilimlenmiştir
(`Plaka_Ayak.3mf`, `Plaka_GPS_Holder.3mf`, 23.08.2026 11:19–12:56). Ayrıca güncel kuşakta
**TPU taban pedi** (×4) yeni bir kalem olarak eklenmiştir.

Yani üretim sürecinde ölçülebilir iki revizyon vardır: **PLA → ABS** (ayak/GPS tutucu) ve
**TPU taban pedi eklenmesi** (iniş darbe sönümü). Bu revizyonlar Bölüm 2 §2.2.5'teki revizyon
listesini tamamlar.

| # | değişiklik | kanıt (artefakt) | gerekçe kayıtta var mı |
|---|---|---|---|
| R1 | Kol reçetesi 0,20/%15/2 duvar → 0,16/%40/6 duvar (kol 3–4) | `Plaka1_Kol_1-2.3mf` ↔ `Plaka2_Kol_3-4.3mf` | 🔴 **YOK** — §5.5.1 |
| R2 | Ayak + GPS tutucu **PLA → ABS** | `Plaka6_PLA_Ayak_GPS.3mf` (23.08 07:40) ↔ `Plaka_Ayak.3mf` + `Plaka_GPS_Holder.3mf` (23.08 11:19–12:56) | **YOK** — dosya adları geçişi kanıtlar, gerekçeyi kanıtlamaz |
| R3 | **TPU taban pedi ×4** eklenmesi | `tpu_taban_pedi_x4.3mf` | **YOK** — amaç (iniş darbe sönümü) metinde yazılı, karar kaydı yok |
| R4 | Ayak+GPS tek plakadan **iki ayrı plakaya** bölünmesi | eski/yeni kuşak plaka dosyaları | **YOK** |
| R5 | Görev bilgisayarı Orin NX → **Jetson Nano 4GB** | Bölüm 2 §2.2.5.1; `jetson_paket/JETSON_NANO_KURULUM.md` | **VAR** (Bölüm 2'de kayıtlı; üretim etkisi §5.2.7) |

**BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (ısı dayanımı, kırılganlık, saha
sıcaklığı vb.) — dosya adları geçişi kanıtlar, gerekçeyi kanıtlamaz.
**BEYAN GEREKLİ (insan): R3 ve R4 değişikliklerinin gerekçe kaydı** — TPU ped eklenmesi ve
plaka bölünmesi için karar tarihi, sebep ve karar veren rol.

### 5.5.3 Değişiklik kaydı disiplini — bundan sonrası

R1–R4'ün gerekçesiz olmasının sebebi, üretim döneminde bir **değişiklik kaydı yordamının
bulunmamasıdır**. Bugünden itibaren geçerli olan mekanizma:

- **Sürüm mühürü** (§5.2.8): `scripts/surum_dondur.py` 17 Eylül'de basılır; sonrasında üretim
  kodu ve model dosyaları değişmez, zorunlu değişiklik = defter kaydı + kapı + ayrı denetim.
- **Yapısal parça değişiklikleri** için aynı disiplin geçerli olmalıdır: her yeni `.3mf`
  reçetesi bir **karar kaydıyla** birlikte depoya girmelidir (ne değişti, neden, karar veren rol).
- SGGS'ye götürülecek kanıt paketi: `.3mf` proje dosyaları + G-code + karar kayıtları.

**BEYAN GEREKLİ (insan): yapısal parça değişikliği için karar kaydı yordamının kabulü** —
mühürün yazılım tarafındaki karşılığının donanım/üretim tarafında da işletileceğinin teyidi.

---

## 5.6 Yönerge dışı ek kanıt

> Bu başlık altındaki içerik Bölüm 5'in beş maddesinden birine girmez ama **ölçülmüştür ve
> artefakta bağlıdır**; kaybolmaması için burada tutulur. İlgili yönerge başlığı her satırda
> yazılıdır.

### E1 — Yapısal doğrulama: FEM çalışmaları (ilgili yönerge başlığı: `Y-3.2.1-A01…A12`)

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

Bu kalemin Bölüm 5'e bakan yüzü şudur: FEM sonucu okunamadığı için §5.5.1'deki kol reçete farkı
**analizle savunulamaz**; savunma ancak beyan ve/veya yeni analizle gelir.

---

## Bu bölümdeki BEYAN GEREKLİ (insan) satırlarının toplu listesi

1. **BEYAN GEREKLİ (insan): tasarımın özgünlüğüne dair imzalı beyan** (§5.1.2).
2. **BEYAN GEREKLİ (insan): CAD birim/ölçek teyidi ve kolun gerçek boyu** (§5.1.3).
3. **BEYAN GEREKLİ (insan): parça başına CAD model kütlesi** (§5.1.3, §5.3.4).
4. **BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi (ABS mi ABS-CF mi)** (§5.1.5).
5. **BEYAN GEREKLİ (insan): final aracı yapısal parçaları için üretim yöntemi seçimi** (§5.1.6).
6. **BEYAN GEREKLİ (insan): gerçek kablo kesitleri, konnektörler ve ölçülmüş akımlar** (§5.2.5).
7. **BEYAN GEREKLİ (insan): uçuş alanı koordinatları ve geofence poligonu** (§5.2.6).
8. **BEYAN GEREKLİ (insan): final aracı üretim takvimi ve kaynakları** (§5.2.10).
9. **BEYAN GEREKLİ (insan): final aracı toplam imalat süresi tahmini ve montaj planı** (§5.2.10).
10. **BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** (§5.3.2) — yalnız üst çerçevenin verisi var.
11. **BEYAN GEREKLİ (insan): parça başına iş gücü ihtiyacı (rol ve adam-saat)** (§5.3.3).
12. **BEYAN GEREKLİ (insan): ölçülen gerçek kütleler, tolerans/uyum ölçümleri, fikstür ihtiyacı, fire kaydı** (§5.3.4).
13. **BEYAN GEREKLİ (insan): bağlantı elemanı (vida/somun/pul) dökümü** (§5.3.4).
14. **BEYAN GEREKLİ (insan): üretim hata modu listesi ve düzeltici işlem prosedürleri** (§5.4.1).
15. **BEYAN GEREKLİ (insan): tabla sıcaklığı uyarısının nasıl ele alındığı ve çarpılma gözlemi** (§5.4.2).
16. **BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı, reçete farkının gerekçesi; kol 1–2 yeniden basılacak mı** (§5.5.1).
17. **BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (§5.5.2).
18. **BEYAN GEREKLİ (insan): TPU ped eklenmesi ve plaka bölünmesi için karar kaydı** (§5.5.2).
19. **BEYAN GEREKLİ (insan): yapısal parça değişikliği için karar kaydı yordamının kabulü** (§5.5.3).
20. **BEYAN GEREKLİ (insan): FEM yük/mesnet/malzeme tanımı ve sonuç değerleri** (§5.6/E1).

Ölçüm bekleyen (beyanla kapanmayan) kalemler: **ÖLÇÜLEMEDİ** etiketiyle §5.2.1 (toplam baskı
süresi), §5.2.7 (kamera FOV, FPS kapısı, `.engine`), §5.2.9 (t_hazırlık, gerçek kütle/CG),
§5.3.2 (yedi plaka) ve §5.6/E1 (FEM sonucu).

---

## 5.7 Kanıt dizini

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
| 28 | Yönerge Bölüm 5'in beş maddesinin birebir metni (bu bölümün başlık şeması) | `results/fdr_sablon/fdr_yonerge_metin.txt`; `FDR/YONERGE_HARITASI.md` §5 | pypdf çıkarımı | 2026-09-03 |
