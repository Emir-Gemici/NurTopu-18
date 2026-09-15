# SUNUM KANIT HAVUZU — 13 Eylül 2026

> **Ne bu dosya:** FDR'nin **ölçülmüş çekirdeği**, sunum yazımı için tek yerde.
> **Ne DEĞİL:** sunum metni değil. İçerik mimar tarafından bu havuzdan türetilir.
>
> **Kurallar (uygulandı):** hiçbir sayı uydurulmadı; her satır `dosya:satır` atfı taşır ve
> atıf `sed -n 'Np'` ile okunarak doğrulandı; etiketler (**ÖLÇÜLDÜ / ÖLÇÜLEMEDİ / BEYAN**)
> FDR'de nasıl yazıldıysa aynen taşındı, terfi ettirilmedi.
>
> **Teslim:** FDR + SUNUM **14.09.2026 – 17.00** (`FDR/sablon/OKUBENI.md:22`). Sunum
> **15 dakika**, "görselden ziyade **teknik ve ayrıntılı**" (`REVIEW_LOG.md:30945`, `:30947`).

---

## 1. Sistem künyesi

> **Sunumda ne işe yarar:** "ne yaptık" slaytının donanım tarafı; DDR'den sapmaları
> göstermek zorunlu (şartname §5.3.1 revizyonların FDR'de sunulmasını ister).

| # | kalem | değer | etiket | atıf |
|---|---|---|---|---|
| 1.1 | Araç ayrımı — **iki ayrı araç** | (a) FDA görev test uçuşu aracı: çoklu rotor, paraşüt/mancınık/İKA **yok**; (b) yarışma final aracı: sabit kanat + mancınık + paraşüt + İKA, **henüz üretilmedi** | ÖLÇÜLDÜ (kapsam beyanı) | `FDR/BOLUM_1_OZET.md:17-23` |
| 1.2 | Görev bilgisayarı | **Jetson Orin Nano Developer Kit 4 GB** (p3767-0004), JetPack **7.2.1**, Ubuntu 24.04, Python 3.12.3, kök NVMe | ÖLÇÜLDÜ (6 Eylül, kartta) | `results/jetson_20260906/ORTAM_KUNYESI.txt:6-8` · `FDR/ACIK_KALEMLER.md:41` |
| 1.3 | Yazılım yığını (kartta ölçülen) | torch 2.11.0, tensorrt 10.16.2.10, ultralytics 8.4.142, opencv 4.11.0.86, pymavlink 2.4.49, MAVProxy 1.8.74 | ÖLÇÜLDÜ | `results/jetson_20260906/ORTAM_KUNYESI.txt:9-26` |
| 1.4 | Uçuş kontrolcüsü | **Pixhawk 6C**, **ArduCopter V4.5.7 (2a3dc4b7)**, `Frame: QUAD/X` | ÖLÇÜLDÜ (5–6 Eylül, MP Messages + tlog) | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1472` · `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:61` |
| 1.5 | Firmware sürüm kilidi | `SURUM = "stable-4.5.7"`, `BOARD_ID = 56`; kart fabrikadan **PX4** ile gelir; 4.7.1'de 31 parametrenin **9'u yok** (SI birim reformu) | ÖLÇÜLDÜ (D-424/D-425) | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:61` |
| 1.6 | Motor / pervane | ~~5008 340KV / 12×10~~ → **SunnySky X2220 980KV V3 ×4 / 10×4,5 (1045)**; 5008'ler iade edildi | **BEYAN** (etiket fotoğrafı yok) | `FDR/BOLUM_1_OZET.md:86` |
| 1.7 | İtki bütçesi | **ÖLÇÜLEMEDİ** — motor değişikliği bütçeyi geçersiz kıldı, gerçek akım ölçülmedi (T211 tıkayıcı) | ÖLÇÜLEMEDİ | `FDR/BOLUM_1_OZET.md:385` |
| 1.8 | Güç zinciri | pil (XT60/XT90) → **PM06** (plan PM02'ydi) → FCHUB-12S → 4× ESC (plan 80 A; kutudan **"60 A V2"** çıktı) | ÖLÇÜLDÜ (kutu açılışı, D-426 §3) · marka/model BEYAN GEREKLİ | `FDR/BOLUM_5_URETIM_FAALIYETLERI.md:215` |
| 1.9 | Pixhawk beslemesi | PM06 → `POWER1`, **5,1–5,3 V**; PM06'nın 8 pinli kablosu 6 pinli POWER1'e uymadı, uydurma adaptör **yapılmadı** | ÖLÇÜLDÜ | `FDR/BOLUM_5_URETIM_FAALIYETLERI.md:216` |
| 1.10 | Kamera | Raspberry Pi HQ (IMX477, CSI); yatay görüş açısı **55–63°** bir **lens hesabıdır, ölçüm değil** | BEYAN / ÖLÇÜLEMEDİ | `FDR/BOLUM_1_OZET.md:538` |
| 1.11 | Telemetri / kumanda | 2× SiK 433 MHz; FlySky FS-i6 (iBUS) — `RCInput: decoding IBUS(1)` | ÖLÇÜLDÜ (RC hattı) | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:82` · `:341` |
| 1.12 | Gövde | 3B baskı (eklemeli imalat); reçete farkının gerekçesi **kayıtta yok** (yönerge: gereksiz değişiklik diskalifiye sebebi olabilir) | BEYAN GEREKLİ | `FDR/BOLUM_1_OZET.md:318-323` · `FDR/ACIK_KALEMLER.md:118` |
| 1.13 | Kütle / CG | **ÖLÇÜLEMEDİ** — araç tartılmadı; DDR aviyonik BOM 26 satır / **2293 g** final aracınındır, FDA aracı değil | ÖLÇÜLEMEDİ | `FDR/BOLUM_7_BUTCE_GERCEKLEME.md:137` · `:169` |

---

## 2. Algı ve karar

> **Sunumda ne işe yarar:** projenin özgün iddiası burada — "serbest alan otoritedir,
> fail-closed" mimarisi + kapıların ölçülmüş sonuçları + **geçilmeyen kapının açıkça
> söylenmesi** (organizasyon "teknik ve ayrıntılı" istedi; dürüstlük burada avantaj).

### 2.1 Mimari ilke

| # | kalem | içerik | etiket | atıf |
|---|---|---|---|---|
| 2.1.1 | Değişmez kural | **"Serbest alan otoritedir, nesne katmanı yalnızca çıkarır."** Hiçbir işlem serbest alanı büyütemez | tasarım ilkesi | `FDR/BOLUM_1_OZET.md:62-63` |
| 2.1.2 | Fail-closed | Ölçek türetilemezse / maske şüpheliyse / koridor darsa → `NO_ROUTE`, **sebebiyle birlikte** hakem ekranına | tasarım ilkesi | `FDR/BOLUM_1_OZET.md:64-66` |
| 2.1.3 | Gerekçe | Şartname yanlış güzergâha **0 puan** verir; "söylememek, yanlış söylemekten iyidir" | tasarım ilkesi | `FDR/BOLUM_1_OZET.md:67-68` |
| 2.1.4 | Yayın sözleşmesi | Her karede **tam mesaj**: ya `OPEN_ROUTE` ya `NO_ROUTE`; sessizlik yok | tasarım ilkesi | `FDR/BOLUM_1_OZET.md:59-60` |
| 2.1.5 | Karar zinciri | kamera → segmentasyon → geçilebilir/engel maskesi → **canlı irtifadan** ölçek (m/px) → serbest alanın en büyük bağlı bileşeninde A* → şerit kararı → telsiz | tasarım | `FDR/BOLUM_1_OZET.md:55-59` |

### 2.2 Model künyesi

| # | kalem | değer | etiket | atıf |
|---|---|---|---|---|
| 2.2.1 | Üretim modeli | `navitas-seg-v36-512`, imgsz 512, SHA `1d1caca6…6911`; kayıt defteri fail-closed doğrular | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:504` |
| 2.2.2 | Yedek model | `navitas-seg-v35-512` (sha `e00f6b8e…`) **silinmedi**; arena K3/K4/K6'da daha iyi (0/1/5), gerçek karede daha kötü — seçim bir **ödünleşim** | ÖLÇÜLDÜ | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2159-2161` |

### 2.3 Kabul kapıları K0–K8 + K5A (sentetik arena, n = 260, üretim kipi, 1 Eylül 2026)

> Toplu verdikt **10/10 GEÇTİ**. Kaynak: `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json`
> (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2091-2093`). Eşiklerin tamamı **sonuç görülmeden** yazıldı.

| kapı | ne ölçer | eşik | ölçülen | sonuç | atıf |
|---|---|---|---|---|---|
| K0 | körlük yok (boş maske üretmiyor) | figür > 0, boş maske yok | figür zemin %2,66 · ham boş 0/67 · copy-paste boş 0/393 | **GEÇTİ** | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2080` |
| K1 | rota üretilen kare | ≥ 230/260 | **256/260** | **GEÇTİ** | `:2081` |
| K2 | rotanın molozdan geçmesi | ≤ %15 | **6/256 = %2,34** | **GEÇTİ** | `:2082` |
| K3 | **ağır** moloz teması | ≤ %3 | **0/256 = %0,00** | **GEÇTİ** | `:2083` |
| K4 | arena dışına taşma | ≤ %5 | **2/256 = %0,78** | **GEÇTİ** | `:2084` |
| K5 | bariyer kesişimi | = 0 px | **0/178** ölçülebilir kare · 0 px | **GEÇTİ** | `:2085` |
| K5A | bariyer kesişimi — **açılı** küme | K5 ile birebir aynı | **0/176** · 0 px | **GEÇTİ** | `:2086` |
| K6 | yanlış güzergâh | ≤ %5 | **2/256 = %0,78** | **GEÇTİ** | `:2087` |
| K7 | **yayınlanan şerit doğruluğu** (88 karelik alt küme) | ≥ %95 ve payda ≥ 80/88 | **84/85 = %98,82** | **GEÇTİ** | `:2088` |
| K8 | tek figür kapısı (şartname Şekil 1, n = 1) | `ZEMIN_MASKESI_SUPHELI` dönmemeli | zemin kaplaması 0,0444 · ret `UC_BANT_TEMAS_YOK` | **GEÇTİ** | `:2089` |

**Kapıların kendi ayırt ediciliği ölçülmüştür:** K5A kümesinde T184 öncesi dedektör
**185/260 → 48/260** düşüyor (52,7 puan), yatay kümede **181/260 → 181/260** hiç düşmüyor —
yani K5A gerçekten **dönme körlüğünü** ölçüyor (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2097-2102`).

### 2.4 🔴 GEÇİLMEYEN kapı — sunumda gizlenmeyecek

| # | kalem | içerik | etiket | atıf |
|---|---|---|---|---|
| 2.4.1 | Kayıt defterinin kendi cümlesi | *"ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8; MASKE_YOK <= 10 istendi, olculen 16. Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi. ESIKLER DEGISMEDI ve sonraki terfileri baglar."* | ÖLÇÜLDÜ (ve DÜŞTÜ) | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2138-2142` |
| 2.4.2 | Terfi gerekçesi | Gerçek karede yanlış güzergâh **15/21 → 7/38**, engel üstü waypoint **79 → 3** | ÖLÇÜLDÜ | `:2153-2154` |
| 2.4.3 | Kabul edilen bedel | K3 0→1, K4 1→4, K6 5→7; figür zemin oranı düştü; val82 FP 0→2 | ÖLÇÜLDÜ | `:2154-2155` |
| 2.4.4 | Gerçek kare kümesi | `test29` n=29: rota 8 (eşik ≥10 ❌), maske yok 16 (eşik ≤10 ❌), FP 1 (≤1 ✅), yanlış güzergâh 0 (=0 ✅) | ÖLÇÜLDÜ | `:2150` |

### 2.5 Ölçülmüş ama kapı OLMAYAN büyüklükler (dürüstlük gereği)

| # | büyüklük | ölçülen | not | atıf |
|---|---|---|---|---|
| 2.5.1 | karar çevrilmesi (kararsızlık) | v36 **14/260** (tohum 7) · **15/260** (tohum 11) | 🔴 **v35'ten KÖTÜ** (9/260 · 11/260) — histerezisin var olma nedeni | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2194` |
| 2.5.2 | çatı kaçağı | **0,0230** (medyan 0,0119) | v34 0,9606 → v35 0,0428 → v36 0,0230 | `:2195` |
| 2.5.3 | gerçek kare zemin kaplaması | tuval 0,2346 · içerik 0,4171 | Bağımsız tahmin %47–52; v36 **altına düştü** = "daha az görüyor" | `:2196` |
| 2.5.4 | `mask mAP50-95` | 0,155 (val) | **ÖLÇÜM DEĞİL KARAR GİRDİSİ DEĞİL** — kıyaslanamaz, karara girmedi | `:2197` |

### 2.6 Histerezis

| # | kalem | ölçülen | etiket | atıf |
|---|---|---|---|---|
| 2.6.1 | Ham → yayın çevrilme | 13 → 7 (tohum 7) · 24 → 11 (tohum 42); bastırılanların **hiçbiri NO_ROUTE değil** | ÖLÇÜLDÜ | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:90` |
| 2.6.2 | Özgün eşik | ⚠ **H1 DÜŞTÜ** ve öyle kayıtlı (`H1_ozgun: false`); H1a/H1b/H2 geçti; eşik ve K değişmedi | ÖLÇÜLDÜ (DÜŞTÜ) | `FDR/BOLUM_1_OZET.md:506` |

### 2.7 Bilinen zayıflıklar (model tarafı, açık)

| # | kalem | içerik | etiket | atıf |
|---|---|---|---|---|
| 2.7.1 | 🔴 Kör aralık | Gerçek uçuşta **51 saniyelik** sahne bağıntılı kör blok (51 kare, 46'sı `MASKE_YOK`; ikinci blok 45 kare). Tazelik penceresi 5 s → aralık pencereyi **10 kat** aşıyor | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:502` · `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:450` |
| 2.7.2 | Bu bir hız sorunu **değil** | Gereken FPS 0,61, band 0,9–2,6; "daha hızlı örneklemek aynı köre daha çok bakmaktır" — kalan iş **model tarafında** | ÖLÇÜLDÜ (yorum kayıtlı) | `FDR/BOLUM_1_OZET.md:256-258` |
| 2.7.3 | Bugünkü savunma | Gizlemek değil **göstermek**: heartbeat `karar_yas` taşır, hakem tespitin **yaşını** ekranda görür, bayat tespit canlı sayılmaz | tasarım | `FDR/BOLUM_1_OZET.md:390-393` |
| 2.7.4 | Kapsam sınırı (denetçinin kendi uyarısı) | *"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR (T66 ada kadrajı, n=260); gerçek ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ."* | ÖLÇÜLDÜ (kalıcı kısıt) | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2177-2178` |
| 2.7.5 | Çözünürlük denemesi reddedildi | `512 → 640`: sentetik `p` 0,9846 → **0,7808**, FPS maliyeti 1,302 → **ön kayıtlı RED kuralıyla reddedildi** (karar performans lehine değil, hüküm lehine) | ÖLÇÜLDÜ | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:411` · `:214` |

---

## 3. Jetson başarımı

> **Sunumda ne işe yarar:** "gerçek donanımda koştu mu?" sorusunun tek net cevabı;
> FPS kapısı **gerçek kartta GEÇTİ** — raporun en güçlü donanım kanıtlarından biri.

| # | kalem | değer | etiket | atıf |
|---|---|---|---|---|
| 3.1 | Eşik (türetildi, tahmin edilmedi) | `GEREKLİ_FPS ≥ 1/(5·p)` → sentetik **0,203** · gerçek sızıntısız **0,579** · en kötü uçuş **0,61 FPS** | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:443` · `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:86` |
| 3.2 | PyTorch (120 örnek, imgsz 512) | p50 **739,076 ms** · p95 **942,150 ms** → **1,361 FPS** ortalama | ÖLÇÜLDÜ (6 Eylül) | `results/jetson_20260906/jetson_fps_20260906_orin_nano/rapor.md:9` |
| 3.3 | TensorRT FP16 (120 örnek) | p50 **634,722 ms** · p95 **751,405 ms** → **1,621 FPS** | ÖLÇÜLDÜ | `results/jetson_20260906/jetson_fps_20260906_orin_nano/rapor.md:11` |
| 3.4 | ONNX kolu | **HATA** — `cudaErrorNoKernelImageForDevice` (sm_87 çekirdeği yok) → ONNX yolu bu kartta **doğrulanmadı** | ÖLÇÜLEMEDİ | `results/jetson_20260906/jetson_fps_20260906_orin_nano/rapor.md:10` |
| 3.5 | 10 dakika sürekli (900 örnek) | pt p50/p95 **770,359 / 922,020 ms** (1,320 FPS) · engine **649,338 / 765,287 ms** (1,576 FPS) | ÖLÇÜLDÜ | `results/jetson_20260906/jetson_fps_20260906_orin_nano_10dk/rapor.md:9-11` |
| 3.6 | Termal | tegrastats gpu ≤ **56,3 °C** | ÖLÇÜLDÜ | `FDR/ACIK_KALEMLER.md:41` |
| 3.7 | Kapı hükmü | pt 1,35/1,06 · engine 1,58/1,33 FPS ≥ eşik 0,61 → **GEÇTİ** | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:240` |
| 3.8 | GPU | `torch.cuda.is_available()` **True** (`cuda_adi: Orin`, torch 2.11.0+cu130) → uçuş **`.pt` GPU ile** | ÖLÇÜLDÜ | `FDR/ACIK_KALEMLER.md:42` |
| 3.9 | 🔴 Engine denkliği | `.engine` derlendi ama D-303 karar denkliği **3/126 DÜŞTÜ** (eşik 1/52) → üretime **alınmadı** | ÖLÇÜLDÜ (DÜŞTÜ) | `FDR/ACIK_KALEMLER.md:61` |
| 3.10 | Genel kapı kartta | **15/15 · 15/15** (`genel_kapi.log`), tam süit kartta koştu, kayıt defteri v36 `.pt` eşleşti | ÖLÇÜLDÜ | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1779-1781` |
| 3.11 | Sınır | mpp=None **ölçeksiz Katman-A** kipidir; kamera bağlı değildi | kapsam notu | `FDR/ACIK_KALEMLER.md:41` |

---

## 4. Haberleşme

> **Sunumda ne işe yarar:** "canlı aktarım gerçek mi?" sorusuna ölçülmüş cevap
> (organizasyon `[19:17]` real-time aktarımı **zorunlu** saydı); ve neyin hâlâ
> ölçülmediğinin dürüst sınırı.

| # | kalem | ölçülen | etiket | atıf |
|---|---|---|---|---|
| 4.1 | MAVLink P1 kapıları (G1–G7) | irtifa 30,0 ± 0,05 m; canlı `mpp`; `yerde_mi` ardışık 3; IN_AIR'de False; yabancı sysid 99 red; donuk `time_boot_ms` yaşı yenilemez; yayın durunca bayatlar — **7/7 GEÇTİ** | ÖLÇÜLDÜ | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1007-1015` |
| 4.2 | 🔴 P1 BULGU A (kapandı) | Alçalan akışta `yerde_mi` **0,002 s'de False** dönüyordu → `IHA_LANDED` **hiç yayınlanmazdı**; şartname §2.2.5 zinciri buradan kırılırdı. Kapanış D-389 | ÖLÇÜLDÜ + düzeltildi | `:1017-1027` |
| 4.3 | Seri hat P2 (S1–S4) | iki uçlu köprüde ACK turu · bayt bayt gönderimde birebir toparlama · tek okumada 3 çerçeve · RF gürültüsünde sonraki geçerli çerçeve ayrışır — **GEÇTİ** | ÖLÇÜLDÜ | `:1040-1044` |
| 4.4 | 🔴 S5 **DÜŞTÜ** | Tampon ≤ 64 KiB eşiği; ölçülen **1.048.576 bayt** (sınırsız büyüme). Düzeltme: `CERCEVE_TAMPON_TAVANI = 64*1024` sözleşmeye girdi, **aynı eşikle** yeniden koşuldu | ÖLÇÜLDÜ (DÜŞTÜ→kapandı) | `:1045` · `:1050` |
| 4.5 | Uçtan uca kare gecikmesi | **p95 0,113 s** (33 gerçek kare + 3 ısınma); tazelik penceresi 5,0 s'nin çok altında; model yükleme 2,64 s bütçe dışı | ÖLÇÜLDÜ (UDP loopback) | `:1124` |
| 4.6 | 🔴 Gecikme düzeltmesi | İlk ölçüm ~0,46 s; ~0,3 s'si bir **soket zaman aşımı sabiti** çıktı (bağımsız çürütücü buldu); düzeltme sonrası telsiz payı ~2 ms (p50 307,6 → 2,3 ms). Yanlış sayı **silinmedi** | ÖLÇÜLDÜ | `:1126-1129` |
| 4.7 | RTT / veri hızı (n=200 prob) | UDP loopback IKA_GO: 200/200, %0 kayıp, RTT p50/p95 **0,27/0,38 ms** · TCP-seri köprüsü IKA_GO: 200/200, **1,33/1,83 ms** | ÖLÇÜLDÜ (RF DEĞİL) | `:1150-1153` |
| 4.8 | 🔴 SiK 433 MHz RF | **ÖLÇÜLEMEDİ** — RTT, kayıp, veri hızı, menzil hiçbiri yok. 5 Eylül'de "bağlandı" bir **BEYAN**'dır, ölçüm değil. DDR'deki ">%98 teslim, 300 m" iddiasının **kanıtı yok** | ÖLÇÜLEMEDİ | `:1155` · `:1161-1168` · `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:449` |
| 4.9 | 🔴 Seri hat üzerinden uçtan uca gecikme | **ÖLÇÜLMEDİ**; p95 0,113 s yalnız UDP loopback'indir. Üretim seri varsayılanlarıyla çevrim **1,0 s** ölçülmüştü | ÖLÇÜLEMEDİ | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1169-1171` |
| 4.10 | 🔴 İHA↔İKA gerçek hat | İki gerçek araç arasında **hiç koşulmadı**; bugünkü kanıt loopback İKA'dır | ÖLÇÜLEMEDİ | `:1173-1175` |
| 4.11 | Akış isteği (T207) | Üretim akışı `MAV_CMD_SET_MESSAGE_INTERVAL` ile **kendisi ister**; ölçülen dönüş 511/33 @125000 µs (**8 Hz**) ve 511/245 @500000 µs (**2 Hz**); `--streamrate 8` systemd biriminde kilitli | ÖLÇÜLDÜ | `:1136-1142` |
| 4.12 | Seri port çakışması | Pixhawk'ı üç sürecin açması ölçülmüş bir çakışmaydı → MAVLink ve NAVITAS protokolü **çoğullayıcıya** bağlandı, kapıya alındı | ÖLÇÜLDÜ + kapandı | `FDR/BOLUM_1_OZET.md:183-184` · `:301-303` |
| 4.13 | 🔴 Waypoint bütçesi | Rota sözleşme tavanına (64 wp, 847 B) çıkarsa ortak ortam ~%71; **ECC açıkken ham bütçe aşılır (%143)** → T250 | ÖLÇÜLDÜ (risk) | `FDR/BOLUM_1_OZET.md:388` · `REVIEW_LOG.md:30821` |
| 4.14 | Karar yayın tavanı | 🔴 **≈ 1 karar/s ve besleme hızlandırılınca DEĞİŞMİYOR** — hat değil, **gönderim tasarımı** | ÖLÇÜLDÜ (D-466) | `REVIEW_LOG.md:30821` |

---

## 5. Uçuş ve yer testleri

> **Sunumda ne işe yarar:** yönerge `Y-4-M12` sahada arıza emniyet testi ister; bizde
> sonuç **olumsuz** ve bu raporda öyle yazılı. Sunumda gizlenirse rapor ile sunum
> çelişir — çelişki puandan daha pahalıdır.

| # | kalem | sonuç | etiket | atıf |
|---|---|---|---|---|
| 5.1 | Kuru koşu (10 halka) | GEÇTİ **9** · DÜŞTÜ 0 · **SAHİPSİZ 1 (motor)** · çıkış kodu **1** (zincir kendini "hazır" ilan etmiyor) | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:444` · `:503` |
| 5.2 | Genel kapı | **15/15 tanısal · 15/15 üretim rotası · 15/15 yayınlanan şerit**, RC=0 | ÖLÇÜLDÜ (3–4 Eylül) | `FDR/BOLUM_1_OZET.md:437` · `:519` |
| 5.3 | Tam test süiti | **1896 test OK** (skipped=3), 390,534 s | ÖLÇÜLDÜ (3 Eylül) — ⚠ **BAYAT**, §9.2 | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:112` |
| 5.4 | Pixhawk tezgâh (5 Eylül) | `ArduCopter V4.5.7` yüklendi · `Frame: QUAD/X` · u-blox GPS · `RCInput: decoding IBUS(1)` · motor testi başladı-bitti | ÖLÇÜLDÜ | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:341` |
| 5.5 | Pil gerilimi | multimetre **15,8 V** ↔ MP 15,8 (±0,1 V kapısı **geçti**) | ÖLÇÜLDÜ | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1473` |
| 5.6 | GPS / EKF | **18 uydu**; `EKF3 IMU0/IMU1 is using GPS` | ÖLÇÜLDÜ | `:1476` |
| 5.7 | Pusula ofsetleri | Mag1 **15,4** / Mag2 **129,5** (< 300) | ÖLÇÜLDÜ | `FDR/ACIK_KALEMLER.md:52` |
| 5.8 | 🔴 **RC failsafe** | **ÖLÇÜLDÜ — DÜŞTÜ**: kumanda kapatıldı, barlar **sabit kaldı**, `Radio Failsafe` gelmedi. Alıcı link kopunca **son değerleri tutuyor** → kontrolcü arızayı **görmez**, RTL/Land hiç başlamaz | ÖLÇÜLDÜ (DÜŞTÜ) | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1477` · `:1657-1668` |
| 5.9 | 🔴 `Y-4-M12` hükmü | *"sahada test edildiğini gösteren veri" şartı **KARŞILANMADI**.* Elde olan tek ölçüm bir **tezgâh alıcı testidir** ve sonucu olumsuz | ÖLÇÜLEMEDİ | `:1670-1672` |
| 5.10 | 🔴 Üç devrilme (6 Eylül) | 20:56 / 21:00 / 21:34; pilot kolu **merkezde** (roll 1500, pitch 1502); pitch **−43,8° / −19,3° / −38,8°**; tlog'da 41 arm penceresi | ÖLÇÜLDÜ (tlog) | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1487-1494` |
| 5.11 | Devrilme hükmü | (1) FC **doğru yönde** düzeltti, mixer ters değil; (2) fiziksel ön, komut edilen itkiyi **üretmedi**; (3) ilk asimetri komut **eşitken** oluştu → kaynak FC değil; (4) **M1 (sağ ön) hasarlı**, 1949'da tutuluyor | ÖLÇÜLDÜ | `:1496-1503` |
| 5.12 | Gaz rampası | Gaz **adımla** verildi: 0,2–0,6 s'de 1000 → 1446/1656/1821/2000; `MOT_THST_HOVER,0.35` öğrenilmemiş; `MOT_SLEW_UP_TIME,0`. Kural: kalkış ≥ 2 s rampa | ÖLÇÜLDÜ | `:1502-1503` · `:1530-1532` |
| 5.13 | Kumandadan arm | Anahtar sinyali ulaşıyor (CH6, **56 çevirme**) ama arm geçişi **0/56**: `RC6_OPTION,0` — anahtarla arm hiç **planlanmamıştı**. Dümenle arm **çalışıyor** (`ARMING_RUDDER,2`) | ÖLÇÜLDÜ | `:1509-1512` |
| 5.14 | 🔴 Hover | **BEYAN** — "hover yapabiliyoruz" (10 Eylül); tarih, log, video **yok** (T223). tlog irtifa/akım taşımaz; `VIBE` için DataFlash `.bin` **indirilmedi** | BEYAN | `:1534-1538` |
| 5.15 | 🔴 Jetson ↔ Pixhawk | 6 Eylül'de Jetson ve NAVITAS yazılımı Pixhawk'a **bağlı değildi**; MAVLink akış kapısı gerçek kartta **koşulmadı** | ÖLÇÜLEMEDİ | `:1538` · `FDR/ACIK_KALEMLER.md:57` |
| 5.16 | ESC kalibrasyonu | 3. denemede başarılı (POWER1 çıkarılmış + USB passthrough + **sonra** pil) | BEYAN (yordam kayıtlı) | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1474` |
| 5.17 | Motor testi | "motorlar doğru" — A/B/C/D konum+yön listesi ve **video gelmedi** (kural: videosuz "doğru" sayılmaz) | BEYAN | `:1475` |

---

## 6. Simülasyon

> **Sunumda ne işe yarar:** yönerge 3B görev icra simülasyonunu **puanlanan** çıktı yapıyor;
> ama organizasyon `[26:26]` "simülasyon gerçek ekipman testinin yerine geçmez" dedi.
> İkisi birlikte doğru: ayrı bir çıktı olarak sunulur, saha kanıtı diye **değil**.

| # | kapı | ölçülen | eşik | hüküm | atıf |
|---|---|---|---|---|---|
| 6.1 | H1-K3 (üretim modeli, mozaik) | doğru etiket **6/15** (yanlış 0) | ≥ 12/15 | 🔴 **DÜŞTÜ** | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:1253` |
| 6.2 | H1-K3 (kare-bazlı boru hattı) | doğru **1/15** | ≥ 12/15 | 🔴 **DÜŞTÜ** | `:1254` |
| 6.3 | H1-K4 (aktarım ACK) | 45/45 · 45/45 | 15/15 | **GEÇTİ** | `:1255` |
| 6.4 | H1-K5 (YER GERÇEĞİ rota) | başarı **45/45** · harita 15/15 | ≥ 12/15 × 3 tohum | **GEÇTİ** | `:1256` |
| 6.5 | H1-K5 (ÜRETİM MODELİ rota) | başarı **9/45** · harita 0/15 | ≥ 12/15 × 3 tohum | 🔴 **DÜŞTÜ** | `:1257` |
| 6.6 | H1-K5 (ÜRETİM BORU HATTI) | başarı **0/15** · harita 0/5 | ≥ 12/15 × 3 tohum | 🔴 **DÜŞTÜ** | `:1258` |
| 6.7 | H1-K6 (grafikler) | 105 koşum tablosu + 4 grafik | 45 koşum + 4 grafik | **ÜRETİLDİ** | `:1259` |
| 6.8 | H1-K7 (video) | **177,88 s** · 25 FPS · 1280×720 · üç kamera + HUD | ≥ 90 s · ≥ 24 FPS | **GEÇTİ** — link **BEYAN GEREKLİ** | `:1260` |
| 6.9 | Motor | **MuJoCo 3.13** (Gazebo değil; bu makinede `gz`/`podman` yok — ölçüldü). Gazebo ağacı silinmedi ama **hiç koşulmadı**; bu bölümdeki **hiçbir sayı Gazebo'dan gelmez** | ÖLÇÜLDÜ | `:1245-1246` · `:1270-1274` |
| 6.10 | Yorum | YER GERÇEĞİ oranı **sürüş + fizik** halkasını ölçer, görüntü işlemeyi ölçmez; uçtan uca zincir ÜRETİM satırlarıdır — **ikisi de eşiğin altında** | kapsam notu | `:1262-1263` |
| 6.11 | SITL (ArduCopter 4.5.7) | İkili indi ve açıldı (sha256 `b9035c08f003ab29…`), pymavlink bağlandı, HEARTBEAT geldi, GPS 3D fix ~2 s'de; `scripts/fda_gorev_uret.py` görev üretiyor, nöbetçi **7/7 OK** | ÖLÇÜLDÜ (12 Eylül) | `TASK_QUEUE.md:9711` |
| 6.12 | SITL kalan iş | Görev yükleme + ARM + AUTO + ölçüm **KOŞULAMADI** (insan işi, T236) | ÖLÇÜLEMEDİ | `TASK_QUEUE.md:9711` |

---

## 7. Üretim, bütçe, gereksinim izlenebilirliği

> **Sunumda ne işe yarar:** "raporun en güçlü iddiası bir yüzde değil, o tablonun
> **var olması**" cümlesi buradan gelir — izlenebilirlik tablosu sunumun kapanış kozudur.

| # | kalem | değer | etiket | atıf |
|---|---|---|---|---|
| 7.1 | İzlenen gereksinim | **45 gereksinim satırı** (§2.1–§2.2: 19 · §5.3.2: 9 · §6.2/§6.4: 10 · §7: 7) | ÖLÇÜLDÜ | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:505` |
| 7.2 | Uygunluk dağılımı | toplam **45** → **32** / **4** / **2** / **7** (sütun başlıkları §6.5'te) | ÖLÇÜLDÜ | `:513` |
| 7.3 | Yöntem ataması | 45 satıra **66 yöntem ataması** (analiz / test / gözle muayene / benzerlik) | ÖLÇÜLDÜ | `:178` · `:195` |
| 7.4 | Açık gereksinimler | A1 İKA sürücü · A2 SiK RF · A3 gerçek otonom uçuş · A4 gerçek arena karesi · A5 kör aralık · A9 sim … tam liste §6.5.1 | ÖLÇÜLEMEDİ | `:438-450` |
| 7.5 | Kanıt defteri | **420 kayıt** (3 Eylül) → **424 başlık / 418 benzersiz** (4 Eylül) | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:445` · `:454` |
| 7.6 | BOM (FDA aracı) | Tablo A 27 satır: kalem/model/adet/tedarik **VAR**; birim fiyat, toplam fiyat, kütle, boyut **ÖLÇÜLEMEDİ / BEYAN GEREKLİ** | ÖLÇÜLEMEDİ | `FDR/BOLUM_7_BUTCE_GERCEKLEME.md:114` · `:259` |
| 7.7 | DDR aviyonik BOM | **26 satır**, toplam **2293 g** (final aracı); FDA aracının kütlesi **ÖLÇÜLEMEDİ** | BEYAN (DDR) | `:137` · `:169` |
| 7.8 | 3B baskı süresi | Sekiz plakadan **yedisinin** G-code'u yok → **toplam baskı süresi ÖLÇÜLEMEDİ**; tahmin de yazılmadı | ÖLÇÜLEMEDİ | `FDR/BOLUM_5_URETIM_FAALIYETLERI.md:179` · `:495` |
| 7.9 | İş gücü | **hiç kaydedilmemiş** | ÖLÇÜLEMEDİ | `FDR/BOLUM_5_URETIM_FAALIYETLERI.md:517` |
| 7.10 | Malzeme çelişkisi | 🔴 ABS / ABS-CF — **beyan ile artefakt çelişiyor**; filament cinsi BEYAN GEREKLİ | çelişki kayıtlı | `FDR/BOLUM_5_URETIM_FAALIYETLERI.md:140` · `:150` |
| 7.11 | Görev planı | TAKEOFF **32 m** → 20×20 m tek pas → LOITER **60 s** → LAND; kötü durum bütçe **221,5 s ≤ 600 s**; **31** parametre, her satırda gerekçe | ÖLÇÜLDÜ (hesap + test kilidi) | `FDR/BOLUM_1_OZET.md:508` |
| 7.12 | Sözleşme sabitleri | tazelik **5,0 s** · asgari irtifa **30 m** · FDA süresi **600 s** · İHA-UB kenarı **300 m** | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:507` |
| 7.13 | Arıza emniyet parametreleri | `FS_THR_ENABLE,1` (RTL) · `FS_GCS_ENABLE,1` (RTL) · `BATT_LOW_VOLT,14.4`+`BATT_FS_LOW_ACT,2` (RTL) · `BATT_CRT_VOLT,14.0`+`BATT_FS_CRT_ACT,1` (LAND) · `FENCE_*` · `RTL_ALT,3500` | ÖLÇÜLDÜ (şablon + test) · saha **ÖLÇÜLEMEDİ** | `FDR/BOLUM_1_OZET.md:524` · `:359-366` |
| 7.14 | İKA kilidi | Hareket izni üçlü kilit: `geçerli OPEN_ROUTE ∧ İHA inişi tamamlandı ∧ YKS'den IKA_GO`; iniş sinyali **insan beyanı değil uçuş kontrolcüsü kanıtı** (`ON_GROUND` + `relative_alt < 1 m` + aynı sysid + ardışık 3) | ÖLÇÜLDÜ (kod + test) | `FDR/BOLUM_1_OZET.md:293-297` |
| 7.15 | İKA sürücü kabulü | T1–T8 **GEÇTİ**; ardışık hata tavanı **3**; `GercekSurucu` arka uçsuz kurulumda `DONANIM_YOK` | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:525` |
| 7.16 | Komut güvenliği | `RTL`/`LAND` **6 test OK**; komut güvenliği **10 test OK**; kaynak pini olmayan komut kabul edilmez | ÖLÇÜLDÜ | `FDR/BOLUM_1_OZET.md:522` |

---

## 8. 🔴 AÇIK / ÖLÇÜLEMEDİ listesi — sunumda dürüstçe söylenecekler

> **Sunumda ne işe yarar:** organizasyon `[09:28]` "teknik ve ayrıntılı" istedi ve
> `[26:26]` simülasyonun ölçüm yerine geçmediğini söyledi. Bu liste, sunumun
> **"kalan iş"** slaytıdır; rapordaki etiketlerle birebir aynı kalmalıdır.

| # | açık kalem | sahibi | nasıl kapanır | atıf |
|---|---|---|---|---|
| 8.1 | **Gerçek arena karesi yok** — K0–K8'in tamamı sentetik; kırmızı H + moloz + bariyer içeren ≥30 m görüntümüz **hiç olmadı**. Maket çekimi **yapılmayacak** | kapanmaz (rapor tarihinde) | Saha `p`'si yarışma günü ilk kez ölçülür | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:450`(A4 satırı) · `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2180-2187` |
| 8.2 | **Gerçek İKA motor sürücüsü yok** — arayüz ve fail-closed hazır, arka uç seçilmedi; kuru koşu halka 10 `SAHİPSİZ` | donanım (final dalgası) | Arka uç bağlanıp `ika_surucu_kabul.py` K1–K6 GEÇTİ | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:447`(A1) |
| 8.3 | **SiK 433 MHz RF hiç ölçülmedi** — RTT/kayıp/menzil yok; DDR'nin ">%98, 300 m" iddiasının kanıtı yok | ekip (telsiz takılınca) | `scripts/sik_rf_olc.py --rol olc`; hedef p95 < 0,20 s | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:449`(A2) |
| 8.4 | **Gerçek otonom uçuş hiç koşmadı** — hiçbir AUTO görevi uçmadı | pilot | İlk hover → Loiter/Auto → 30 m tam prova | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:451`(A3) |
| 8.5 | **Arıza emniyet sahada doğrulanmadı**; RC failsafe tezgâhta **DÜŞTÜ**, düzeltme kumandadadır, tekrar ölçümü yok | pilot + aviyonik | FS-i6 `RX Setup → Failsafe`, CH5 → Land; tekrar ölçüm | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1657-1672` |
| 8.6 | **Jetson ↔ Pixhawk MAVLink kapısı gerçek kartta koşulmadı** (6 Eylül'de bağlı değildi) | ekip | `mavlink_dogrula.py` üç uçta aynı anda 3/3 | `FDR/ACIK_KALEMLER.md:57` |
| 8.7 | **`jetson_baslat.sh` systemd kipleri koşulmadı** (`--kur`/`--kapi`/`--dogrudan`); yalnız `--kuru` koştu | ekip | Kartta koşum | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1786-1789` |
| 8.8 | **Kütle, CG, parça tartıları** ölçülmedi; itki bütçesi geçersiz (T211 **tıkayıcı**) | insan (tartı) | Tartı + veri sayfası itki tablosu | `FDR/ACIK_KALEMLER.md:50` · `FDR/BOLUM_1_OZET.md:385` |
| 8.9 | **Kamera gerçek FOV ölçülmedi** (55–63° lens hesabı) | ekip | `codes/kamera_dogrula.py` | `FDR/BOLUM_1_OZET.md:538` |
| 8.10 | **Titreşim (`VIBE`) ölçülmedi** — DataFlash `.bin` indirilmedi | pilot | İlk hover logu | `FDR/ACIK_KALEMLER.md:52` |
| 8.11 | **Uçuş bilimleri / yapısal analiz / mancınık bölümleri yazılmadı** (ağırlık-denge, aerodinamik, FEA, yay sabiti, enerji denklemi) | tasarım / CAD | Mühendislik çıktısı üretilecek — **beyanla kapanmaz** | `FDR/ACIK_KALEMLER.md:110-114` · `:134-136` |
| 8.12 | **Bütçe: birim fiyat, toplam fiyat, tedarik durumu** yok | kaptan | Fatura/teklif kayıtları | `FDR/ACIK_KALEMLER.md:101` |
| 8.13 | **Simülasyon video linki** (YouTube liste dışı + Drive) | insan (T222) | Yükleme + link bildirimi | `FDR/ACIK_KALEMLER.md:63` |
| 8.14 | **Kapak alanları** — takım adı / takım ID / **başvuru ID** | kaptan | KYS teyidi | `FDR/ACIK_KALEMLER.md:137` |
| 8.15 | **Denetim borcu** (Anayasa madde 19: yazan onaylamaz) — D-407 mühür kapsamı, D-406 K2/T207, D-412 `_kanit_yaz`; üçünde de bağımsız üçüncü göz yok | mimar / bağımsız denetçi | Bağımsız denetim | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1774-1799` |
| 8.16 | **T260 — "3 yola kilitli tasarım"** organizasyonca kusur sayıldı; bugünkü `OPEN_ROUTE.road ∈ {1,2,3}` tam o kilit. Ölçümsüz kod değişikliği **yapılmadı** | mimar kararı | madde 15 denetimi + ön kayıt | `REVIEW_LOG.md:30969-30974` · `TASK_QUEUE.md:9745` |

---

## 9. ⛔ Sunumda SÖYLENMEMESİ gerekenler

> **Sunumda ne işe yarar:** bunlar raporda **üstü çizili, geri alınmış ya da bayat**
> bilgilerdir. Sunuma girerse rapor ile sunum çelişir; değerlendirme ikisini yan yana
> okuyacak (`[04:16]` sunum önceden ellerinde olacak).

| # | söylenmeyecek | neden | doğrusu | atıf |
|---|---|---|---|---|
| 9.1 | ❌ "FDR teslimi **21.09.2026**" | Organizasyon tarihi **bir hafta öne çekti** | **14.09.2026 – 17.00** (şartname PDF'i eski) | `FDR/sablon/OKUBENI.md:22-30` |
| 9.2 | ❌ "Tam süit **1896 test OK**" (bugünkü durum diye) | **BAYAT** — o koşum 3 Eylül; test dosyası sayısı 155 → 169 → 180 arttı | Teslimden önce **yeniden koşulacak**; rapor bunu kendi *DOĞRULANACAK* kalemi olarak yazıyor | `FDR/BOLUM_1_OZET.md:456-458` · `:541` |
| 9.3 | ❌ Bu Linux makinesinin süit sonucunu ölçüm diye sunmak | 🔴 **Bu makine kanonik ortam DEĞİL**: `push_kapisi.py --kuru` tam süiti **KIRMIZI** verdi (2612 test, 51 hata + 57 çürük), sebep **ortam farkı** | Kanonik yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`; madde 14 genel kapısı etkilenmedi | `REVIEW_LOG.md:30881` |
| 9.4 | ❌ "Arena artık **1 güzergâh**, mimari değişti" | D-470 **geri alındı** (D-472): iki ayrı etkinlik var | **Adıyaman provası** tek yol · **final** 3 güzergâh; sistem 3'e **kilitli olmamalı** (T260) | `REVIEW_LOG.md:30890` · `:30969-30974` |
| 9.5 | ❌ "Görev bilgisayarı **Jetson Nano 4GB** / JetPack 4.6" | 3 Eylül beyanı 6 Eylül'de kartla **yanlışlandı** | **Orin Nano Developer Kit 4 GB**, JetPack 7.2.1 | `FDR/BOLUM_1_OZET.md:87-88` |
| 9.6 | ❌ "Motor **5008 340KV**, pervane 12×10" | 5008'ler **iade edildi** | SunnySky X2220 980KV V3 / 10×4,5 — **BEYAN**, etiket fotoğrafı yok | `FDR/BOLUM_1_OZET.md:86` |
| 9.7 | ❌ "Uçtan uca gecikme **0,458 s**" | İlk ölçüm **yanlıştı** (soket zaman aşımı sabiti); silinmedi, üstü çizildi | **p95 0,113 s** (yalnız UDP loopback) | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1126-1129` |
| 9.8 | ❌ "Çevrimdışı **14/14 cp38 tekerlek** ile Jetson kuruldu" | Kart Orin Nano / Py3.12 çıktı; cp38 zinciri bu kartta **kullanılamadı** | Kurulum kartta apt/pip ile (internetle) yapıldı | `FDR/BOLUM_1_OZET.md:333` |
| 9.9 | ❌ Gazebo ölçümü diye sunmak | Gazebo **hiç koşulmadı**; ağaç önceki tasarım | Tüm sim sayıları **MuJoCo 3.13** | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:1270-1274` |
| 9.10 | ❌ "**Hover yapabiliyoruz**" (kanıt gibi) | **BEYAN** — tarih/log/video yok | Üç devrilme **ölçüldü**; hover kanıtı T223'te bekliyor | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1534-1538` |
| 9.11 | ❌ "SiK telsiz **çalışıyor / bağlandı**" (ölçüm gibi) | "Bağlandı" bir **BEYAN**'dır; `sik_rf_olc` koşulmadı | RF **ÖLÇÜLEMEDİ** | `FDR/BOLUM_4_TEST_FAALIYETLERI.md:1163-1168` |
| 9.12 | ❌ "TensorRT `.engine` ile uçuyoruz" | Engine derlendi ama **karar denkliği DÜŞTÜ** (3/126) | Uçuş **`.pt` (GPU)** ile | `FDR/ACIK_KALEMLER.md:61` |
| 9.13 | ❌ Sentetik kapı sonucunu "saha başarımı" diye sunmak | Denetçi her koşumda kendi uyarısını basar | "Bu ölçümlerin tamamı **SENTETİKTİR**" | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2173-2178` |
| 9.14 | ❌ Raporun **isimsiz/rol bazlı** kuralını sunuma taşımak | İki belgenin kuralı **farklı**: şablon slayt 2'de isim + eğitim bilgisi **istiyor** | Sunumda şablon ne istiyorsa o doldurulur | `FDR/sablon/OKUBENI.md:44-47` |
| 9.15 | ❌ K0–K6 "7/7" ile K0–K8 "10/10" sayılarını karıştırmak | Farklı tarih ve **farklı karar katmanı** (terfi anı 26 Ağu · üretim kipi 1 Eyl) | "Bugünkü zincir" = **1 Eylül, 10/10** | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:2111-2121` |

---

## Havuz istatistiği

| bölüm | madde |
|---|---|
| 1. Sistem künyesi | 13 |
| 2. Algı ve karar | 26 (5 ilke + 2 künye + 10 kapı + 4 geçilmeyen + 4 kapı-olmayan + 2 histerezis + 5 zayıflık → 32 satır, 26 ayrık kalem) |
| 3. Jetson başarımı | 11 |
| 4. Haberleşme | 14 |
| 5. Uçuş ve yer testleri | 17 |
| 6. Simülasyon | 12 |
| 7. Üretim / bütçe / izlenebilirlik | 16 |
| 8. Açık-ÖLÇÜLEMEDİ | 16 |
| 9. Söylenmeyecekler | 15 |
| **toplam** | **140** |
