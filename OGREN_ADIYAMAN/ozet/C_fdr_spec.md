# C — FDR Yapısı ve Bölüm 3 Sistem Spesifikasyonları: Olgusal Özet

> Kaynak dosyalar (tamamı okundu): `FDR/README.md`, `FDR/YONERGE_HARITASI.md`,
> `FDR/BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md`, `FDR/BOLUM_1_OZET.md`,
> `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` (2509 satır), `FDR/ACIK_KALEMLER.md`.
> Depo kökü: `/home/n4vitas/proje/navitas_tam/navitas/`.
> Kural: bu belgede FDR'de olmayan hiçbir sayı yoktur; belirsiz yerde "FDR'de yok" ya da
> "DOĞRULANAMADI" yazılmıştır. Her önemli iddianın yanında dosya ve başlık atfı vardır.
> FDR'nin kendi durum tarihi: taslak v1, 3 Eylül 2026; son ölçüm bandı 7 Eylül 2026 (D-435).

---

## 1. FDR'nin yapısı

### 1.1 Bölümler ve puanlar (`FDR/README.md` "Bölümler ve puanlar"; `BOLUM_0` Y-0-M04)

Rapor şartname §5.3.1 Tablo 4'e göre yedi puanlanan bölüm + ön kısımdan oluşur. Final
notundaki ağırlık `FDA = FDR × 0,85 + Drone ile Görev Test Uçuşu × 0,15` (`README.md` başlık).

| bölüm | konu | puan | dosya |
|---|---|---:|---|
| 0 | Kapak · Versiyonlar · Tanımlar ve Kısaltmalar | — | `BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` |
| 1 | Özet | 5 | `BOLUM_1_OZET.md` |
| 2 | Organizasyonel Yapı ve Proje Takvimi | 5 | `BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` |
| 3 | Genel Sistem Spesifikasyonları | **40** | `BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` |
| 4 | Test Faaliyetleri | 15 | `BOLUM_4_TEST_FAALIYETLERI.md` |
| 5 | Üretim Faaliyetleri | 15 | `BOLUM_5_URETIM_FAALIYETLERI.md` |
| 6 | Gereksinim İzlenebilirliği ve Değerlendirme | 10 | `BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` |
| 7 | Bütçe Gerçekleme Analizi | 10 | `BOLUM_7_BUTCE_GERCEKLEME.md` |

Rapora girmeyen çalışma belgeleri: `YONERGE_HARITASI.md` (zorunlu iskelet + boşluk analizi),
`TAKIM_PROMPT.md`, `ACIK_KALEMLER.md`, `ACIK_KALEMLER_HAM.md` (betikle üretilir). Yönergenin
kendisi `FDR_2_qNiVF.pdf` (19 sayfa); metni `results/fdr_sablon/fdr_yonerge_metin.txt`.

### 1.2 Yönerge ile eşleşme — `Y-` kimlikleri (`FDR/YONERGE_HARITASI.md`)

Her yönerge gereksinimine `Y-<bölüm>-<tip><no>` kimliği verilmiştir (`T` = yapısal tasarım
süreci, `A` = yapısal analiz süreci, `M` = madde). Bölüm 6 izlenebilirlik tablosu ve açık kalem
listesi aynı kimlikleri kullanır. Bölüm başlıkları ve numaraları yönergeden birebir alınmıştır;
README'nin üç tartışmasız kuralından biri "başlık icat etme"dir.

Bölüm 3'ün yönerge iskeleti üç ana başlıktır: **3.1 Uçuş Bilimleri** (7 alt başlık, Y-3.1.1…3.1.7),
**3.2 Yapısal Tasarım ve Analiz** (3.2.1 İHA 18 T + 12 A madde; 3.2.2 İKA 11 T + 3 A; 3.2.3
Mancınık 11 T + 2 A), **3.3 Aviyonik & Yazılım** (3.3.1 sistem mimarisi / BOM / entegrasyon;
3.3.2 kablaj / güç tüketimi; 3.3.3 üç boyutlu simülasyon / veriler / video; 3.3.4 algoritma akışı /
görüntü işleme başarımı / haberleşme paket yapısı).

3 Eylül taslağı kendi başlık şemasıyla yazılmıştı; `BOLUM_3` §3.0.3'te eski→yeni numara haritası
verilir (ör. eski 3.5.2 → §3.3.4.2.4; eski 3.7 → §3.3.1.1.12–16). Bölüm 6 hâlâ "Bölüm 3 §3.5.2"
diye atıf yapar; §3.0.3 bu atfın düzeltilmediğini açıkça söyler.

### 1.3 DURUM sayımı (`YONERGE_HARITASI.md` "Boşluk özeti", 7 Eylül 2026)

| bölüm | puan | VAR | KISMEN | YOK | en büyük boşluk |
|---|---|---:|---:|---:|---|
| Ön kısım | — | 2 | 2 | 1 | KYS künye teyidi + logo; TASNİF DIŞI sayfa düzeni |
| Bölüm 1 | 5 | 0 | 10 | 0 | İKA/Mancınık özeti zayıf |
| Bölüm 2 | 5 | 1 | 3 | 0 | organizasyon şeması (7 Eylül'de `Y-2.1-M01` VAR oldu) |
| Bölüm 3.1 | (40 içinde) | 0 | 0 | 7 | uçuş bilimleri hiç yok |
| Bölüm 3.2 | (40 içinde) | 0 | 8 | 48 | İKA ve Mancınık yapısal; analizler |
| Bölüm 3.3 | (40 içinde) | 0 | 7 | 4 | 3B görev simülasyonu + video; kablaj hesabı; güç tüketimi ölçümü |
| Bölüm 4 | 15 | 1 | 7 | 4 | menzil, kalibrasyon kanıtı, görev simülasyonu, arıza emniyet |
| Bölüm 5 | 15 | 0 | 3 | 1 | düzeltici prosedürler + reçete farkı gerekçesi |
| Bölüm 6 | 10 | 3 | 3 | 0 | pasta grafiği + ÖDR/DDR eşlemesi |
| Bölüm 7 | 10 | 0 | 1 | 4 | fiyatların tamamı |

Not: 3.3 satırındaki "VAR 0" tablo başlığındaki sayımdır; aynı dosyanın 3.3 tablosunda
`Y-3.3.4-M01` (akış diyagramları) 7 Eylül'de VAR yazılmıştır. Özet tablo "3.1/3.2 değişmedi"
notuyla 7 Eylül'de yeniden üretilmiş; 3.3 satırı için birebir doğrulama bu özette
yapılmadı (DOĞRULANAMADI — sayım tablonun kendi beyanıdır).

Haritanın okuması: raporun gücü **3.3, 4 ve 6** ekseninde; en büyük açık **3.1 ve 3.2** (40 puanlık
bölümün içinde). Kapanma yolu üçe ayrılır: bugün yazılabilir (3.3, Bölüm 4 yer testleri, 6, ön
kısım); 5–19 Eylül ölçümüyle kapanır (kütle/denge, kablaj, güç, menzil, kalibrasyon, arıza emniyet);
insan beyanı bekler (fiyatlar, tedarik, CAD/FEA çıktıları).

### 1.4 Ön kısım (`BOLUM_0`)

Kapak: TAKIM ADI "Navitas Autonomous Systems", TAKIM ID 997827, BAŞVURU ID 5329027 —
DDR dönemindeki `navitas-teknofest/references/ddr_requirements.md`'den alınmış; **KYS teyidi
DOĞRULANACAK**. Versiyon tablosu: yalnız `V 1 · 03.09.2026`. Tanımlar: yönergedeki 29 kısaltma
birebir (DDK, İHA, İKA, HTAB, İHA-FB, İHA-UB, İKA-KB, HB, İHA-İB, ÖDR, DDR, FDR, FDA, FDS,
SGGS, UHDR, K_zorluk, m_İHA, t_İHA, t_hazırlık, m_İKA, m_yük, t_İKA, P_görev, P, P_TI, P_uçuş,
P_centilmenlik, C_ceza) + takım kısaltmaları (YKS, ACK, OPEN_ROUTE/NO_ROUTE, IHA_LANDED,
HEARTBEAT, K0…K8/K5A, SiK, HB dedektörü, D-NNN, Ön kayıt, Mutasyon kontrolü). Uyarı: yönergedeki
**FDA** = Final Değerlendirme Aşaması; raporda `--fda` bir **yazılım bayrağıdır** (§5.3.2 görev
test uçuşu kipi). TASNİF DIŞI başlık/altlık PDF dizgisinde (18–20 Eylül) uygulanacak, henüz yok.

### 1.5 Raporun dört yazım kuralı (`README.md`; `BOLUM_3` §3.0)

1. Her sayı bir artefakttan gelir; bölüm sonunda "Kanıt dizini" yol + betik + tarih verir.
2. `ÖLÇÜLEMEDİ ≠ GEÇTİ` — kabul denetçisinde kod satırıdır (`scripts/olcum/65_kabul_denetcisi.py:456, 608, 636, 664`; alt betik çökerse kapı `OLCULEMEDI` döner ve terfiyi bloklar).
3. Geçilmeyen kapı geçilmedi diye yazılır (v36 terfisi, §3.3.4.2.5).
4. Sentetik ölçüm saha başarımı diye sunulmaz.

Ek kural (README): rapora **isim yazılmaz**; anlatım rol bazlı (R1 Kaptan … R8 Kanıt-kalite).

### 1.6 Takvim (`README.md` "Resmî yarışma takvimi", şartname Tablo 1)

21.09.2026 17.00 FDR son teslim (uçuş günü **değildir**; takım o gün Adıyaman'da kendi provasını
yapar) · 30.09–03.10.2026 Final Değerlendirme Aşaması (FDS + Drone ile Görev Test Uçuşu, tek atış) ·
04.10.2026 FDR sonuçları · 05.02.2027 SGGS · 16.04.2027 UHDR.

---

## 2. BÖLÜM 1 — Özet: görev senaryosu, sistem tarifi, ana iddialar

### 2.1 İki ayrı araç (`BOLUM_1` giriş; `BOLUM_3` §3.0.1)

| | Yarışma günü aracı (§2.2) | Görev test uçuşu aracı (§5.3.2) |
|---|---|---|
| platform | sabit kanat İHA + mancınık fırlatma | çoklu rotor (quadcopter), 3B baskı gövde |
| iniş | paraşüt | motorlu iniş (`NAV_LAND`) |
| ikinci araç | İKA (diferansiyel sürüş) zorunlu | İKA yok |
| alan | HTAB 50 × 50 m; İHA-UB rota uzunluğu 300 m | 20 × 20 m simüle test alanı |
| irtifa | görev planına göre | asgari 30 m |
| süre | İHA 900 s · İKA 600 s | tüm operasyon 600 s |
| aktarım hedefi | YKS **ve** İKA | yalnız YKS (hakem canlı onaylar) |

Yarışma final aracı (sabit kanat + mancınık + paraşüt + İKA) **henüz üretilmemiştir**
(`BOLUM_1` giriş). Algı, karar, haberleşme ve yer istasyonu katmanı iki araçta aynı koddur;
fark `yks_gui --fda` bayrağıyla tanınır (`CONTRACTS.md` §6.7, D-407).

### 2.2 Sistemin bir cümlelik tarifi (`BOLUM_1` §Y-1-M01)

"NAVITAS, afet sahasını simüle eden bir alanda hangi güzergâhın açık olduğunu havadan bulan ve
bu kararı hakemin canlı doğrulayabileceği biçimde yere aktaran bir otonom sistemdir." Üç birim:
İHA, YKS, İKA. Karar zinciri görev bilgisayarında koşar: kamera karesi → segmentasyon → geçilebilir/
engel maskeleri → canlı irtifadan türetilen ölçek (m/px) → serbest alanın en büyük bağlı bileşeni
üzerinde A* → şerit kararı → telsizle yayın. Her karede tam bir mesaj: `OPEN_ROUTE` ya da
`NO_ROUTE`; sessizlik yoktur. Değişmez kural: "serbest alan otoritedir, nesne katmanı yalnızca
çıkarır"; belirsizlikte fail-closed (`NO_ROUTE` + sebep). Gerekçe: şartname §5.3.2 yanlış
güzergâha 0 puan verir.

### 2.3 Görev akışı — FDA görev test uçuşu (`BOLUM_1` §Y-1-M09)

Hazırlık kronometresi → `KALKIŞ` damgası → otonom tırmanış (TAKEOFF 32 m) → 20×20 m alan
üzerinde tek pas tarama (asgari 30 m) → her karede karar → YKS'ye canlı aktarım → hakem onayı 2/2
(FDA kipinde İKA kanıtı aranmaz) → ACK → LOITER → LAND → iniş kanıtı (`IHA_LANDED`) ile süre biter.
Bütçe ≤ 600 s; hesaplanan kötü-durum 221,5 s.

### 2.4 Ana iddialar ve sayılar (`BOLUM_1` §Y-1-M10 tablosu)

| ne | ölçülen | çerçeve / tarih |
|---|---|---|
| Genel kapı `codes/test_rota_sentetik.py` | 15/15 tanısal · 15/15 üretim rotası · 15/15 yayınlanan şerit | 15 belirlenimci arena sahnesi, 3 Eylül; 4 Eylül tekrarı 15/15 · 15/15 RC=0 |
| Tam test süiti | 1896 test OK (3 atlandı, 390,5 s) | 3 Eylül — özet kendisi "bayat" der (test dosyası 155 → 169) |
| K0–K6 (terfi anı 26 Ağustos, n=260 sentetik) | 7/7 GEÇTİ — rota 255/260, bariyer 0, yanlış güzergâh 2,75 | sentetik |
| K0–K8 + K5A üretim kipi (1 Eylül) | 10/10 GEÇTİ — K1 256/260, K2 6/256, K3 0/256, K4 2/256, K5/K5A 0 px, K6 2/256, K7 84/85 | sentetik |
| K7 yayınlanan şerit doğruluğu | 84/85 (%98,8) | üretim kipi |
| Uçtan uca kare gecikmesi | p95 0,113 s (33 gerçek kare + 3 ısınma) | UDP loopback |
| Gereken kare hızı `1/(5·p)` | sentetik 0,20 · gerçek sızıntısız 0,58 · en kötü 0,61 FPS | türetildi |
| Saha kuru koşusu (10 halka) | GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor) · çıkış kodu 1 | 2 Eylül; 3 ve 4 Eylül tekrarı aynı |
| Kanıt defteri | 420 kayıt (3 Eylül) → 424 başlık / 418 benzersiz (4 Eylül) | `REVIEW_LOG.md` |
| Jetson FPS (6 Eylül, D-431) | pt p50/p95 1,35/1,06 · engine 1,58/1,33 FPS, eşik 0,61 → GEÇTİ | Orin Nano Developer Kit 4 GB |

Özetin kendi sınırları (§Y-1-M05): (1) gerçek arena karesi yok — kırmızı H, moloz, bariyer içeren
görüntü hiç olmadı; saha `p` ÖLÇÜLEMEDİ; gerçek uçuş kaydında **51 saniyelik** kör aralık (51 ardışık
kare, 46'sı `MASKE_YOK`; ikinci blok 45 kare), tazelik penceresi 5 s. (2) Gerçek İKA motor sürücüsü
yok. (3) Gerçek SiK 433 MHz hattı hiç ölçülmedi; DDR'deki ">%98, 300 m" iddiasının kanıtı yok.

Revizyonlar (§Y-1-M04): (a) v35 → v36 terfisi iki ön kayıtlı eşiği geçmeden (ROTA ≥10 → 8;
MASKE_YOK ≤10 → 16), kazanç gerçek karede yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3;
bedel K3 0→1, K4 1→4, K6 5→7. (b) Gecikme düzeltmesi p95 0,458 → 0,113 s (308 ms soket zaman aşımı
sabitiydi). (c) `--fda` kipi. (d) `RTL`/`LAND` komutları (`tests/test_iha_rtl_land.py` 6 OK,
`tests/test_iha_komut_guvenligi.py` 10 OK). (e) Seri port çoğullayıcı. (f) İKA sürücü soyutlaması.

Bölüm 1, Bölüm 2–7 kesinleştikten sonra yeniden üretilecek (dosya başındaki uyarı); bugünkü hâli
3–4 Eylül durumudur.

---

## 3. BÖLÜM 3 — alt alt özet

### 3.0 Okunma kuralı ve DDR → FDR revizyonu (§3.0, §3.0.2)

DDR beyanı ile fiilen tedarik edilen donanım farklıdır (§3.0.2 tablosu): görev bilgisayarı Jetson
Orin NX 16 GB → **Jetson Orin Nano Developer Kit 4 GB** (3 Eylül beyanı "Nano 4GB" 6 Eylül'de kartla
yanlışlandı, D-431); Pixhawk 6X → **Pixhawk 6C + PM02** (kutudan PM06 çıktı); Holybro M10 → **M9N**;
Arducam IMX477 → **Raspberry Pi HQ (IMX477, CSI)**; TBS Crossfire → **FlySky FS-i6 / FS-iA6B (iBUS)**;
İKA bilgisayarı Raspberry Pi 5 → **tedarik edilmedi**; model YOLOv8-seg nano/NCNN/640 →
**YOLOv8m-seg `navitas-seg-v36-512`, PyTorch/ONNX, 512**. DDR'nin güç/batarya tabloları FDR'ye
taşınmadı (DOĞRULANACAK).

### 3.1 Uçuş Bilimleri (§3.1, 7 alt başlık)

Konu yarışma final aracıdır (sabit kanat). Depoda uçuş bilimleri artefaktı **yoktur**: `find`
araması (`*.step, *.stp, *.inp, *.odb, *.rst, *.SLDPRT, *.iges`) hiçbir dosya döndürmedi. Tek 3B
geometri quadcopter STL'leridir (`dronesolid/` altı parça). Rol boşluğu: Bölüm 2 rol tablosunda
uçuş bilimleri / yapısal / CAD rolü tanımlı değil. Yedi alt başlığın (3.1.1 ağırlık-denge, 3.1.2
boyut, 3.1.3 kontrol yüzeyi, 3.1.4 aerodinamik, 3.1.5 kararlılık, 3.1.6 performans, 3.1.7 yük)
hepsi **BEYAN GEREKLİ (insan)**; "DDR'den beri güncelleme yoktur" beyanı da eksik. 3.1.1'de test
aracı için kalkış kütlesi / CG **ÖLÇÜLEMEDİ** (ölçüt CG ± 1 cm). Uyarı: §3.3.1.1.11'deki 221,5 s
çoklu rotor plan hesabıdır, sabit kanat performansı değildir.

### 3.2 Yapısal Tasarım ve Analiz (§3.2)

Dürüst özet (§3.2 giriş): ölçülmüş yapısal veri yalnız görev test aracında ve künye seviyesinde;
yapısal **analiz** (statik, burkulma, modal, topoloji) hiçbir araç için yapılmadı; FEA çıktısı yok.

#### 3.2.1.1 Görev test uçuşu aracı künyesi (3B baskı quadcopter)

Kaynak: kullanıcı beyanı 3 Eylül, `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2; 5–6 Eylül kutu açılışı
düzeltmeleri (D-426/D-428/D-431/D-435).

| kalem | değer | durum |
|---|---|---|
| Gövde | Quadcopter, 3B baskı (`dronesolid/`: kol, gövde, alt gövde, bacak, dome, GPS tutucu); GPS çubuğu + ayaklar ABS beyaz, kalanı ABS-CF siyah | basıldı ve monte |
| Motor | ~~5008 340 KV ×4~~ → **SunnySky X2220 980KV V3 ×4** (7 Eylül, D-435) — **BEYAN**, etiket fotoğrafı yok; 5008'ler iade edildi; X2220'ler 2 yıl önce kullanılmış eski motorlar (BEYAN) | araçta takılı; itki bütçesi ÖLÇÜLEMEDİ |
| Pervane | ~~12×10~~ → **10×4,5 (1045)** (BEYAN, D-435); veri sayfasında 10×4,5 satırı YOK, en yakın APC1047 | araçta takılı (BEYAN) |
| ESC | plan 80 A DShot ×4 → kutudan **Hobbywing Skywalker 60A V2** çıktı (D-428 §1, etiket BEYAN); ESC'ler **AUX 1–4** (`SERVO9–12` = M4, M2, M1, M3); kartta `RC_SPEED` 490 ölçüldü (ESC spec 50–432 Hz dışı) → şablona `RC_SPEED,400` | — |
| Güç dağıtımı | Matek XCLASS FCHUB-12S V2 | kutuda |
| Uçuş kontrolcüsü | **Pixhawk 6C** + plan PM02 → kutudan **PM06** (POWER1, 6-pin kablo) | ÖLÇÜM: ArduCopter V4.5.7 (2a3dc4b7), `Frame: QUAD/X` |
| GNSS / pusula | **Holybro M9N**, direk üstü | ÖLÇÜM: `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` |
| RC | **FlySky FS-i6** + FS-iA6B (iBUS); alıcının `i-BUS SERVO` portu → Pixhawk `PPM/SBUS RC` | ÖLÇÜM: `RCInput: decoding IBUS(1)` |
| Telemetri | **2 × SiK 433 MHz** (drone + YKS) | 5 Eylül bağlandı (BEYAN); RTT/kayıp ÖLÇÜLEMEDİ |
| Görev bilgisayarı | **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12) | kuruldu 6 Eylül; araca takılmadı, Pixhawk/kamera bağlı değil |
| Kamera | **Raspberry Pi HQ (IMX477, CSI)**, standart 6 mm lens | kutuda; CSI yolu ÖLÇÜLEMEDİ |
| Pil / şarj | **1 × 4S 10 Ah 25C** · iMAX B6 (50 W → ~3 A → ~3 saat dolum) | günde en çok 2 uçuş |
| Güç kesme | anahtar yok — pil fişi çekilir (XT60/XT90) | yordam |

Jetson beslemesi: FCHUB'ın 2 A BEC'i yetmez; ayrı **5 V / 5 A UBEC** FCHUB pil pad'lerinden
(3 Eylül planı Nano J25/J48; Orin Nano'da besleme yolu DOĞRULANACAK, D-431). Pixhawk ↔ Jetson:
`TELEM2` → 40-pin UART (`/dev/ttyTHS1`, 3,3 V), MAVLink2 57600; yedek micro-USB `/dev/ttyACM0`.
Kamera optiği **hesaptır, ölçüm değil**: 6 mm lenste yatay FOV ≈ 55–63°; 30 m'de kare genişliği
≈ 31–37 m; 20×20 m alan tek karede sığar (16 mm lens ≈ 12 m, sığmazdı); `--fov` `kamera_dogrula`
ile ölçülecek.

**Paraşüt:** FDA aracında paraşüt **yoktur** (çoklu rotor). Yarışma aracının paraşüt podu
tasarlanmamış, BEYAN GEREKLİ (§3.2.1.2, T05). Yazılımda `PARACHUTE` komutu var (0,20 s × 40 tekrar,
ceza sabiti `PARASUT_MANUEL_CEZA_PUANI = 50`), FDA kipinde düğme fiilen kapalı (§3.3.4.1.15).

#### 3.2.1.1.1 İtki bütçesi (7 Eylül, D-435 · T211) — veri sayfası, ölçüm değil

Motor veri sayfası (SunnySky X2220-III KV980): 85 g, 3–4S, maks. sürekli akım **38 A / 30 s**,
638 W, önerilen ESC 40 A, iç direnç 51 mΩ, 12N14P. 4S + APC1047 satırı: `T_max` **2130 g** @ 38,4 A ·
568,3 W · 10 476 rpm; 4 × T_max = **8520 g**; %50 eşiğine denk kütle **4260 g**. Tam gaz 38,4 A,
38 A/30 s sınırında ("SINIRDA/AŞIYOR"). ÖRNEK satırlar: 2,0 kg → 4 motor 19,2 A; 2,5 kg → ≈26 A;
3,0 kg → ≈35 A (ÖRNEK ≠ ölçüm). Pil 25C → 250 A boşalma ↔ 4 × 38,4 = 153,6 A (BEYAN'a bağlı).
**KAPI** (hover itki oranı ≤ %50 ∧ `I_hover` ≤ `I_sürekli`) **ÖLÇÜLEMEDİ**: kütle tartılmadı (T10),
akım ölçülmedi; "bütçe kapanmadan bir sonraki güç verme yok" (TIKAYICI). Logla tutarlılık: P19'da
ilk eğilme gaz PWM %45'te; P20'de M1 25 s boyunca 1949'da doygun, duman atan motor M1 (D-434/D-435).
Kapanış üç insan girdisi ister: motor etiketi fotoğrafı, pilli tam araç tartısı, ilk hover'da güç
modülü akımı.

#### 3.2.1.3 Ölçülmemiş mekanik büyüklükler

Kalkış kütlesi, ağırlık merkezi (ölçüt CG ± 1 cm), titreşim (`VIBE` < 30), pusula ofseti (< 300),
itki / asılı kalma akımı, uçuş süresi ("hesap yapılmadı, tahmin yazılmaz") — hepsi **ÖLÇÜLEMEDİ**.

#### 3.2.1.4 / 3.2.1.5 Yönerge T01–T18 ve A01–A12

T maddelerinde yalnız T03 (altı STL parçası tasarlandı, basıldı, monte), T08 (künye var, tedarikçi/
teslim süresi boş), T11 (ABS / ABS-CF seçimi yazılı, gerekçe yok), T12 (FDM 3B baskı) KISMEN; T10
kütle ÖLÇÜLEMEDİ; kalanı BEYAN GEREKLİ. T05: repodaki tek 3B gösterim `simulation/models/iha/model.sdf`
CAD değil (`mesh` sayısı 0). T16'ya bağlı risk: kol 1–2 ile kol 3–4 farklı baskı reçetesiyle
basıldı, gerekçe kayıtta yok (`Y-5-M05` 🔴 RİSK — yönerge: "gerekliliği ispatlanmamış değişiklikler
diskalifiye sebebi"). A01–A12 tamamen BEYAN GEREKLİ (FEA yok).

#### 3.2.2 İKA ve 3.2.3 Mancınık

İKA: donanım **tedarik edilmedi**, hat finale bırakıldı; yapısal tasarım yok. DDR planında RPi 5
vardı (§3.0.2). Yazılım tarafı ayrı: `comms/ika_receiver.py`, `simulation/scripts/ika_nav.py`,
`ika_surucu.py`; İKA gövde genişliği yazılımda **0,70 m** varsayımı (`IKA_GENISLIK_M`) — fiziksel araç
doğrulamalı. Gerçek motor sürücüsü sahipsiz; `GercekSurucu` arka uçsuz kurulamaz (`DONANIM_YOK`).
Sensör listesi FDR'de **yok** (İKA aviyonik BOM'u yok, §3.3.1.2). Mancınık: üretilmedi, tasarımı
yok; tek dosya `simulation/models/catapult/model.sdf` (görselleştirme primitifi). Yay sabiti ve
enerji denklemleri BEYAN GEREKLİ.

### 3.3.1 Nihai Donanım ve Sistem Mimarisi

#### 3.3.1.1 Sistem mimarisi ve istasyonlar (§3.3.1.1.1–6)

İHA bağlantı şeması 7 Eylül'de çizildi (`sekiller/iha_baglanti.svg`; ölçülmeyen hatlar kesik çizgi;
nöbetçi `tests/test_gece_baglanti_semasi.py`). İKA şeması yok. Üç istasyon: İHA görev bilgisayarı
(`codes/rpi_inference.py`, `comms/iha_sender.py`, `comms/iha_inis_yayinci.py`, `comms/iha_komut_alici.py`),
YKS (`comms/yks_gui.py`, `comms/kamera_istemci.py`, Tk arayüzü), İKA (`comms/ika_receiver.py`,
`ika_nav.py`, `ika_surucu.py`). Tek mesaj sözleşmesi: `\n` ile çerçevelenmiş JSON, taşıyıcıdan
bağımsız (UDP / SiK); `CONTRACTS.md` §6, kod `comms/protocol.py`.

Mesaj tipleri: `OPEN_ROUTE` (`road` 1=sol/2=orta/3=sağ, `conf`, `ref_xy`, `waypoints`), `NO_ROUTE`
(`sebep`, `detay`), `HEARTBEAT` (`node`; İHA'da `karar_yas`), `ACK` (`ref`, `ref_tip`), `CMD`
(`cmd`, `hedef`), `IHA_LANDED`. Yayın kuralı K1: her karede tam bir mesaj; güven kapısı tek yerde
(`comms/iha_sender.py:145`). ACK bağlama: `seq` düğüm başına; `ref_tip` çapraz kabulü önler (D-405
Q4 / T206), geriye uyumlu. Yarışma kipinde İKA ACK'i hem gönderene hem YKS'ye gider; 2. hakem onayı
`ACK(ref_tip="OPEN_ROUTE")` ekranda görünmeden verilemez (§6.6). Alıcı kuralları: `NO_ROUTE` son
geçerli rotayı ezmez; sürüşte `NO_ROUTE` gelirse güvenli duruş; `karar_yas` yoksa taze sayılmaz
(D-374: 45–51 s körlükte heartbeat akmaya devam etti).

#### 3.3.1.1.7 Güç ve sinyal topolojisi

4S 10 Ah LiPo → XT60/XT90 → PM06 → Pixhawk 6C POWER1 (5,1–5,3 V, `BATT_MONITOR=4`); TELEM1 → SiK
→ YKS; TELEM2 → Jetson UART; AUX 1–4 → ESC Skywalker 60A V2 ×4 → motor; RCIN ← FS-iA6B `i-BUS
SERVO`; GPS1 ← M9N; FCHUB-12S V2 → ESC güç + 5V/5A UBEC → Jetson; CSI ← RPi HQ. 5 Eylül plan ↔ kutu
tablosu (D-426): PM02→PM06 (8 pinli kablo 6 pinli POWER1'e uymadı, 6 pinli kablo takıldı); ESC
"60 A V2"; FS-iA6B teyit; Pixhawk fabrikadan PX4 ile geldi, ArduCopter 4.5.7 flash edildi; emniyet
düğmesi `PreArm: Hardware safety switch` kayboldu (18:05); motor testi `starting motor test` →
`finished motor test` (18:06), sıra ve yönler 4/4 doğru (**BEYAN**, video yok); Jetson takılmadı.
Ağırlık/boyut sütunları için tartı satırı yok.

#### 3.3.1.1.8 MAVLink çoğullayıcı (ZORUNLU, `CONTRACTS.md` §7.4 · D-403)

Ölçülmüş kusur: Pixhawk'ı iki üretim süreci ayrı açıyordu (`rpi_inference.py:314`,
`iha_inis_yayinci.py:170`), üçüncüsü eklenmek üzereydi; kılavuzlarda çoğullayıcı geçişi 0. Kural:
Jetson'da seri portu yalnız çoğullayıcı açar (mavlink-router / MAVProxy); uçlar `udp:127.0.0.1:14550`
(`rpi_inference`, irtifa → mpp), `14551` (`iha_inis_yayinci`, `landed_state`), `14552`
(`iha_komut_alici`, `COMMAND_LONG` yazar). Kapı `scripts/mavlink_dogrula.py`: HEARTBEAT sysid,
`GLOBAL_POSITION_INT ≥ 4,0 Hz`, `EXTENDED_SYS_STATE ≥ 1,0 Hz`; eşikler `TELEMETRI_IRTIFA_TAZELIK_S =
0,50 s` (Nyquist 2 Hz × 2 pay) ve `yerde_mi` 3 ardışık çiftten türetildi. **Gerçek Pixhawk'ta kapı
koşulmadı** (5–6 Eylül'de Jetson–Pixhawk bağlı değil). Metin tutarsızlığı: bu alt bölüm "kural yalnız
`iha_komut_alici`'da kodla kilitli" der, ama `ACIK_KALEMLER.md` #23 ve Kanıt dizini kilidin 4 Eylül'de
üç sürece genişletildiğini (`tests/test_seri_pixhawk_kilidi.py` 13/13, D-419 §3–4) yazar — §3.3.1.1.8
paragrafı bayat.

#### 3.3.1.1.9 SiK hub (`CONTRACTS.md` §7.5 · D-404/D-405)

`comms/seri_hub.py`: `/dev/ttyUSB0`'ı yalnız hub açar; tüketiciler UDP'de kalır (bind
`127.0.0.1:5100`, `--tuketici 127.0.0.1:5007`). Tek sahiplik (`SO_REUSEADDR`'sız, `exclusive=True`),
seri arızasında çerçeveler düşürülür ve sayılır (bayat rota yayınlanmasın). Ölçülen zamanlama
(Windows geliştirme makinesi): UDP→seri boşta p50 10,6 ms / p95 31 ms; 20 Hz girişte p50 45 ms —
`PARASUT_TEKRAR_ARALIGI_S` 0,20 s altında. **Gerçek SiK radyoda ÖLÇÜLEMEDİ.** SiK hattında
`--ika-hedef` verilmez (İKA ACK'i gelmediği için 8 tekrar / 2,11 s boşa gidiyordu).

#### 3.3.1.1.10 Akış isteği (T207, KRİTİK)

Üretim kodu `EXTENDED_SYS_STATE`'i hiç istemiyordu → iniş kanıtı sahada hiç oluşmayabilirdi.
Kapatma: `AkisIstekcisi` başta ve her `MAVLINK_AKIS_ISTEK_ARALIGI_S = 10 s`'de `SET_MESSAGE_INTERVAL`
(çarpan 2); `MAVLINK_AKIS_SESSIZLIK_TAVANI_S = 5 s` sessizlikte bir kez KIRMIZI uyarı. pymavlink `udp:`
sunucu kipinde akran görülmeden yazma hatayı yutar → istek ertelenir. Kilit
`tests/test_faz_b_akis_istegi.py` 17 test; MUT-1/MUT-2 her biri 3 test düşürdü.

#### 3.3.1.1.11 Uçuş kontrolcüsü yapılandırması, uçuş kipleri, kalibrasyon

`config/pixhawk/arducopter_fda.param`: **48 parametre** (7 Eylül: 31 + `RC_SPEED` + 16
`SERVOn_FUNCTION`; her satırda NEDEN yorumu) — Bölüm 1 hâlâ "31 parametre" der (bayat). Görev
`fda_gorev.waypoints` (QGC WPL 110): HOME yer tutucu (0°, 0° — Adıyaman koordinatları girilmedi)
→ `NAV_TAKEOFF` 32 m (≥30 m + 2 m baro/EKF payı) → 4 × `NAV_WAYPOINT` (20×20 m köşeleri, 32 m) →
`NAV_LOITER_TIME` 60 s → `NAV_LAND`. `WPNAV_SPEED = 300 cm/s`, `LAND_SPEED = 50 cm/s`; kötü-durum
**221,5 s** ≤ 600 s (test ayrıca 300 s yarı bütçeyi arar). Kilit `tests/test_faz_b_pixhawk_sablon.py`
16 test. Kaynak: ArduPilot Copter-4.5 kodu.

Failsafe parametreleri (`BOLUM_1` §Y-1-M08 tablosu; `BOLUM_3` §3.3.1.1.11 listesi): `FS_THR_ENABLE,1`
(RC kaybı → RTL), `FS_GCS_ENABLE,1` (YKS heartbeat kaybı → RTL), `BATT_LOW_VOLT,14.4` +
`BATT_FS_LOW_ACT,2` (RTL), `BATT_CRT_VOLT,14.0` + `BATT_FS_CRT_ACT,1` (LAND), `FENCE_ENABLE,1` ·
`FENCE_TYPE,3` · `FENCE_ALT_MAX,50` · `FENCE_RADIUS,60` · `FENCE_ACTION,1`, `RTL_ALT,3500` (35 m: görev
30 m üstü, çit 50 m altı), `ARMING_CHECK=1`, `MOT_PWM_TYPE=0`, `SYSID_THISMAV=1`, SERIAL1/2 57600
MAVLink2, `SRx_POSITION` 4 Hz, `SRx_EXTRA3` 1 Hz. Uçuş modları SwC: Stabilize / Loiter / RTL —
**BEYAN**, kanal uçları tutanakta yok.

5 Eylül–6 Eylül durumu: `FRAME_CLASS=1`/`FRAME_TYPE X` teyit (ÖLÇÜM); iBUS teyit (ÖLÇÜM); `RC_PROTOCOLS`
sahada 4 → 1 yapıldı ve geri alınmadı; PM06 → POWER1 çalışıyor; RC failsafe ÖLÇÜLEMEDİ; accel + level
BEYAN teyitsiz; pusula kalibrasyonu YAPILMADI (Jetson takılı değil); ESC kalibrasyonu 5 Eylül
YAPILMADI (ACIK_KALEMLER #7: 6 Eylül'de yapıldı, D-428 §3, beyan); pil gerilimi MP ↔ multimetre
ÖLÇÜLEMEDİ. Sahada okunan döküm 6 Eylül 20:22: `config/pixhawk/arducopter_fda_20260906.param`
(`RC_PROTOCOLS=1`, `FS_THR_ENABLE=3`, `BATT_FS_LOW_ACT=1`; `FS_GCS_ENABLE` yok → üçüncü döküm şart).
Firmware: 4.7.1'de 9 parametre eksik çıktı → 4.5.7'ye sabitlendi (D-425); çevrimdışı yol
`tests/test_pixhawk_firmware_yolu.py` 10/10.

#### 3.3.1.1.12 Görev bilgisayarı yığını (6 Eylül düzeltmesi, D-431)

Kart: Jetson Orin Nano Developer Kit 4 GB (p3767-0004), JetPack 7.2.1 (L4T R39.2.1), Ubuntu 24.04,
Python 3.12.3, kök NVMe (`results/jetson_20260906/ORTAM_KUNYESI.txt`). Kurulum `nvidia-jetpack`
(CUDA 13.2, TensorRT 10.16.2) + `~/venv312` (torch 2.11.0+cu130, ultralytics 8.4.142, pymavlink
2.4.49). `torch.cuda.is_available()` True (`cuda_adi: Orin`). Kartta genel kapı 15/15 · 15/15.
3 Eylül'deki "JetPack 4.6 / Py3.8 venv38 / 14/14 cp38 tekerlek, 51 dosya, 246 MB" hazırlığı bu kartta
uygulanmadı; tarihli kayıt olarak durur. `.engine` `.pt`'den derlendi (530 s; 57 283 989 B), ama
engine↔pt karar denkliği **DÜŞTÜ** (F1 0 · F2 0,9953 · D-303 oransal 3/126 > 5/260) → engine üretime
alınmadı, **uçuş `.pt` GPU ile**. ONNX GPU `onnxruntime-gpu` 1.29: `cudaErrorNoKernelImageForDevice`
(sm_87 çekirdeği yok) → ONNX yolu bu kartta doğrulanmamış. §3.4.1 A3 satırı ("Nano venv38'de tensorrt
yok, ÖLÇÜLEMEDİ") bayat; güncel hüküm "denklik düştü".

#### 3.3.1.1.13–14 Kamera köprüsü ve systemd

`scripts/kamera_koprusu.py` CSI'yi sistem cv2 (GStreamer) ile açıp HTTP sunar (`/video` MJPEG,
`/kare.jpg`, `/durum`); `rpi_inference --kaynak http://127.0.0.1:8080/video`; yedek USB webcam
`--kaynak 0`. 6 Eylül: köprü kartta **dosya kaynağında** açıldı (`fps_tavani=5.0`, :8081); CSI kamera
bağlı değildi → `nvarguscamerasrc` yolu ÖLÇÜLEMEDİ. `jetson_baslat.sh` altı systemd birimi
(`Restart=always`, `RestartSec=2`): `navitas-cogullayici`, `navitas-seri-hub` (yalnız `KIP=sik`),
`navitas-kamera-koprusu`, `navitas-rpi-inference` (`--camera --ekransiz --mavlink udp:127.0.0.1:14550`),
`navitas-iha-inis-yayinci`, `navitas-iha-komut-alici`. Kipler `--kuru` (eksikte çıkış 3), `--kapi`,
`--durum`, `--dogrudan`. `--ekransiz` ölçülmüş çökmeyi kapatır (D-404: DISPLAY'siz `cv2.imshow`).
Testler: köprü 7, `jetson_baslat` 42, paket 18 dosya.

#### 3.3.1.1.15 FPS kapısı

`GEREKLI_FPS ≥ 1/(5·p)`: sentetik arena (260) p=0,9846 → 0,203; gerçek DJİ sızıntısız (243) p=0,3457
→ 0,579; yalnız 0038 (230) p=0,3261 → 0,613. Kapı **0,61 FPS**, p50 ve p95 ayrı. D-376: ilk havuzun
%62'si eğitim kümesindeydi (kirli p=0,4866). Çözünürlük artırımı REDDEDİLDİ (D-377: p 0,9846 → 0,7808).
Jetson 6 Eylül (`scripts/jetson_fps.py --cihaz 0`, imgsz 512, conf 0,3, 15 ısınma + 120 örnek,
mpp=None): `.pt` 739/942 ms → **1,35/1,06 FPS** GEÇTİ; `.engine` FP16 635/751 ms → **1,58/1,33 FPS**
GEÇTİ; `.onnx` HATA. 10 dk (900 örnek): pt 770/922 ms, engine 649/765 ms; tegrastats gpu en yüksek
56,3 °C. Darboğaz model değil: engine çıkarım 87 ms, `get_masks` ~311 ms + Katman A ~208 ms CPU.
Sınır: kareler diskten, saha `p` ÖLÇÜLEMEDİ.

#### 3.3.1.1.16 Sürüm mührü

`surum_dondur --dogrula` (v2, 49 test); ilk sürümde CRLF kusuru (KRİTİK, D-405) düzeltildi.
17 Eylül sürüm dondurmasından itibaren üretim kodu değişmez.

#### 3.3.1.2 Aviyonik BOM

Dolu sütunlar: ad, marka/model, adet (§3.2.1.1). Boş: birim ağırlık, toplam ağırlık, boyut, tahmini
maliyet. DDR ↔ FDR karşılaştırması 7 kalem (§3.0.2). İKA BOM'u yok. Fiyatlar Bölüm 7 ile aynı
tablodan beslenmeli.

#### 3.3.1.3 Entegrasyon planı — kuru koşu

`scripts/saha_kuru_kosu.py` on halka, gerçek kodu çağırarak: kamera, model yükleme, çıkarım, maske,
ölçek, hedef konumu, rota (`yol_no = 2`), aktarım (loopback İKA'ya `OPEN_ROUTE`), sürüş izni
(`IHA_LANDED`, `comms/iha_inis_yayinci.py:386`) **GEÇTİ**; **motor SAHİPSİZ**. Son koşum 4 Eylül
09:52:22 (`results/saha_kuru_kosu_20260904_095222/ozet.json`, `cikis_kodu: 1`).

Kapı özeti üç tarihte (§3.3.1.3.2): 3 Eylül — genel kapı 15/15, tam süit 1896 OK, K0–K8+K5A 10/10,
defter 414. 5 Eylül — tam süit **2138 test**, 1 FAIL ×2 (`test_p8_sim_katmani.test_comms_loopback_gecer`,
ortam: canlı YKS/İKA 5005/5006 portlarını tutuyor, D-427); defter 432. 6 Eylül kartta — genel kapı
15/15 · şerit 15/15; tam süit `Ran 2121` F5 E30 S8 (26'sı ortam: `O:\` yolları). İKA entegrasyon
planı BEYAN GEREKLİ (R6).

### 3.3.2 Elektriksel tasarım ve kablolama

§3.3.2.1 Kablaj hesapları: **tamamen açık** — AWG kesit, uzunluk, akım taşıma, gerilim düşümü yok;
girdi olan ölçülen maksimum akım yok. §3.3.2.2 Güç tüketimi: tam yük akımı, hover akımı, tepe akım,
uçuş süresi **ÖLÇÜLEMEDİ**; PM06 telemetrisi (`BATT_MONITOR=4`) ile ilk hover'da ölçülecek.
Beyan: sürekli tam gaz yapılmaz; günde en çok 2 uçuş.

### 3.3.3 Görev icra simülasyonu

Var olan: Gazebo Classic 11, 7 dünya (`simulation/worlds/`), İHA/İKA/mancınık SDF (mesh 0, CAD değil,
`<static>true</static>`), görev betikleri (`iha_flight.py`, `iha_detect_send.py`, `ika_nav.py`,
`score.py`, `hakem_log.py`), kayıt yolu `simulation/docker/record.sh` → `navitas.mp4` 1280×720.
Yok: `simulation/recordings/` dizini, `results/` altında simülasyon çıktısı, geliştirme makinesinde
`gz`/`podman`. Üç alt madde (3B ortam, veriler/grafikler, video linki) **ÖLÇÜLEMEDİ**. Karıştırma
yasağı: K0–K8 ölçümleri simülasyon verisi değildir. Kapsam sınırı: simülasyon rotası `rota_bul`,
üretim yolu `run_camera → analyze_path → KararYayinci`.

### 3.3.4.1 Detaylı algoritma akışı

Üretim zinciri `codes/rpi_inference.py:run_camera` (5 Eylül commit `64cd543`: `run_camera` 2298):
[1] `_preprocess` (kare tuval, gri 114) → [2] `model.predict(imgsz=512)` (kayıt defterinden) → [3]
`get_masks` `{0: zemin, 1: engel}` + ince bariyer dedektörü → [4] `kare_olcek_kahini` → mpp (yoksa
`NO_ROUTE(OLCEK_YOK)`) → [5] `analyze_path` (en büyük bağlı bileşen, uç-bant teması, C-uzayı `dist ≥
r_gerekli_px`, açıklık ağırlıklı A* maliyet `1,0 + λ·u^p`, λ=3,0 p=2,0; HB pedi görünürse hedef) →
[6] `_rota_kararini_esikle` (`ROTA_GUVEN_ESIGI` 0,20) → [7] `KararYumusatici.suz` (K=3) → [8]
`_karari_yayinla`. Aynı zincir `run_video` ve `run_image`'da.

Değişmez kural `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)`; `dilate`, `MORPH_CLOSE`, `bitwise_or`,
`np.maximum` yasak (`codes/costmap_path_finder.py:212-213`). İnce bariyer dedektörü (T67): şartname
figüründe bariyerin 3644 pikselinin %0,0'ı engel, %30,9'u zemin sayılıyordu, rota 59 px kesiyordu;
renk anahtarı `BARIYER_KROMA_ESIGI = 25` (LAB a*) yapay figürden kalibre — gerçek arenada kırmızı
olmayabilir, o zaman dedektör ateşlemez (fail-safe).

Üç koordinat çerçevesi (Kaynak / Tuval / İçerik); ölçülmüş üç ihlal: 576×1024 portrede SAĞ yerine
ORTA; `min_area_ratio` %1 → fiilen %1,78; 18/18 karede rota yok. Waypoint'ler `ref_xy = [0,0]`'a
göreli metre; İKA saf ötelemeyle oturtur (`ika_nav.py:206`).

Ölçek (mpp): (a) irtifa + FOV birincil (`comms/inis_kaniti.BagilIrtifaOkuyucu`); (b) HB pedi 2,0 m
kenarı yalnız doğrular — n=260'ta tespit 260/260, merkez hatası medyan 0,71 px, sapma medyan %5,2
(p90 %8,6). Çapraz bant `OLCEK_CAPRAZ_BANDI = 0,25` (sapmanın ~4,8 katı); çelişkide ortalama alınmaz
(260 doğrulandı / 0 çelişkili). `TELEMETRI_IRTIFA_TAZELIK_S = 0,50 s`; makullük bandı 30–200 m.
Kapatılan tuzak: `olcek_px(None)` → `m = 1.0` → `r_gerekli_px = 1,10 px` (gerçek 12,7 px, ~11 kat).

Geometri sabitleri: `IKA_GENISLIK_M` 0,70 · `MASKE_HATA_M` 0,25 · `TAKIP_HATA_M` 0,50 → **`R_GEREKLI_M`
1,10** · `ALGI_PAYI_M` 0,25 · `AC_M/KAPAT_M` 0,30/0,40 · `WP_ARALIK_M/MAKS_WP` 2,0/64. C-uzayı etkisi
(kompozit, 7 kare): doğru şerit 1/7 → 6/7, darboğaz 1,0 px → 13,0–15,0 px, güven 0,028–0,117 →
0,644–0,744. SciPy/scikit-image yasak; medial-axis yerine açıklık ağırlıklı A* bilinçli ikame.

Histerezis K=3 (`KARAR_HISTEREZIS_KARE`, `KararYumusatici`): `NO_ROUTE` anında; farklı şerit 3 ardışık
karede; H5 tavanı. Ölçüm (σ=2/255, n=260): tohum 7 ham 13 → yayımlanan 7; tohum 42 24 → 11; bastırılan
`NO_ROUTE` 0. Gecikme tavanı ≈ 0,34 s. **H1 ön kaydı GEÇİLMEDİ** (%40 istendi; %53,8 ve %45,8),
`H1_ozgun: false`; H1a 0/0, H1b geçti; H1c bu paragrafta "damgalanmadı" yazar ama `ACIK_KALEMLER.md`
#24 kapandığını yazar (`tests/test_p5_h1c_damgasi.py` 23/23) — paragraf bayat.

Fail-closed tablosu (§3.3.4.1.10): ölçek yok → rota üretilmez; kaynaklar çelişik → ölçek yok; güven
< 0,20 → yol None + yayın katmanında ikinci savunma; `ZEMIN_MASKESI_SUPHELI` (kaplama tavanı 0,55,
kenar 0,40); model kaydı uyuşmazsa yüklenmez; kamera 30 ardışık düşük kare → kontrollü bitiş; İKA
sürücü 3 ardışık arıza → durdur; ölçüm alt betiği çökerse `OLCULEMEDI`. 15 kanonik ret kodu
(`OLCEK_YOK`, `ZEMIN_MASKESI_SUPHELI`, `MASKE_YOK`, `BILESEN_YOK`, `UC_BANT_TEMAS_YOK`, `ALAN_YETERSIZ`,
`GORUS_HATTI_KOPUK`, `KENAR_GUVENSIZ`, `DUSUK_GUVEN`, `KORIDOR_DEGIL`, `HEDEF_YOK`, `ALAN_IHLALI`,
`ASGARI_IRTIFA_ALTI`, `KARAR_YOK`, `ROTA_GEOMETRI`).

ARM kilidi: düğme durumu emniyet sinyali değildir (D-393 §2). İki aşamalı hakem onayı: 1/2 canlı
görüldü; 2/2 İKA ACK ekranda; `IHA_LANDED` geldiğinde ACK yoksa "İHLAL RİSKİ". `IKA_GO` ACK'li tekrar
0,25 s × 20 (tek atış kusuru D-02); `tests/test_ika_go_ackli_tekrar.py` 5 mutasyon yakalandı. İKA
hareket kilidi `sür ⟺ OPEN_ROUTE ∧ İHA indi ∧ IKA_GO`; iniş kanıtı `EXTENDED_SYS_STATE.landed_state ==
ON_GROUND` + `relative_alt < 1 m`, aynı sysid, 3 ardışık çift; manuel "İHA İNDİ" düğmesi latch'i
açmaz (`tests/test_iha_landed_gate.py:313`). Varış = brandaya temas: son waypoint ped kutusunda
253/256; `FINAL_WP_RADIUS = 0,3 m < HB_KENAR_M/2 = 1,0 m` → ≥ 0,7 m içeride; Gazebo fiziksel temas
ÖLÇÜLEMEDİ. Süre sabitleri: İHA 900 s, İKA 600 s, FDA 600 s, hazırlık 900 s; İKA'da bekleme ve sürüş
ayrı deadline (`tests/test_k5_k6_sure_limitleri.py`, 4 mutasyon).

FDA kipi (§3.3.4.1.15): süre 600 s; 2/2 onay İKA kanıtı aranmaz; PARAŞÜT kapalı (komut gönderilmez);
FIRLATMA → `KALKIŞ`; İKA BAŞLAT kapalı; iniş kanıtı zorunlu. `tests/test_faz_b_yks_fda_kipi.py` 9 test,
2 pozitif kontrol, 4/4 mutant. Denetim borcu: sözleşme ve uygulama aynı el (21 Eylül provasında hakem
rolüyle kapatılacak). Tazelik (§3.3.4.1.16): `karar_yas` yoksa taze değil; D-383 §2'de üç kaçak
(duvar saati asimetrisi, NaN, ekran çelişkisi) kapatıldı.

Akış diyagramları (§3.3.4.1.17, 7 Eylül): (a) İHA ana döngüsü 51 düğüm, (b) komut alıcısı 68, (c)
iniş kanıtı 62, (d) YKS 86, (e) İKA sürüş 70 — toplam 337/337 düğüm `dosya:satır` doğrulandı
(`scripts/akis_diyagram_dogrula.py`); `tests/test_gece_akis_diyagramlari.py` 13/13; `FDR/sekiller/akis_a..e.svg`.

### 3.3.4.2 Görüntü işleme başarımı

Model künyesi (§3.3.4.2.1): `navitas-seg-v36-512`, YOLOv8m-seg (27,2 M parametre), imgsz 512, arka uç
pytorch, SHA-256 `1d1caca6…6911`, sınıflar `{0: traversable, 1: blocked}`, ONNX `f4c9f5fe…`, `.engine`
yer tutucu = RED (bu tablo 3 Eylül; 6 Eylül'de engine deftere `turev_eslesti` yazıldı, §3.3.1.3.2).
Türev doğrulaması fail-closed (D-284). ONNX↔PT karar denkliği 259/260 (CPU EP), IoU 0,9975, azami sapma
172,1 px = 13,443 m; FP16 zarar yönü 0, uyuşma 0,9968.

Kapı tablosu (§3.3.4.2.3; `t150_baglama_v36_kabul_verdikt.json`, 1 Eylül, 10/10): K0 figür zemin %2,66,
boş maske 0/67 ve 0/393; K1 256/260 (≥230); K2 6/256 = %2,34 (≤%15); K3 0/256 (≤%3); K4 2/256 = %0,78
(≤%5); K5 0/178 ölçülebilir kare, 0 px; K5A açılı küme 0/176; K6 2/256 = %0,78 (≤%5); K7 84/85 = %98,82
(≥%95, payda ≥80/88; yanlış `sa_000090.jpg` 2→3); K8 tek figür `UC_BANT_TEMAS_YOK` (zemin kaplaması
0,0444). Eşikler üç ön kayıtta: K0–K5 D-107 (14 Ağustos), K6–K7 `results/gece_20260826/ON_KAYIT.md`,
K8/K5A D-332/D-334. K5A ayırt ediciliği: T184 öncesi dedektör açılı kümede 185 → 48 (52,7 puan),
yatayda 181 → 181. İki ölçüm hattı (§3.3.4.2.4): terfi anı (26 Ağu) K2 %5,88 / K4 %1,57 / K6 %2,75 vs
üretim kipi (1 Eyl) %2,34 / %0,78 / %0,78 — fark zincirden (T150/T184/T198), modelden değil.

Geçilmeyen kapı (§3.3.4.2.5): `test29` (n=29, kör etiket uzlaşısı, eğitime girmedi): rota 8 (≥10 ❌),
maske yok 16 (≤10 ❌), TP 7, FP 1 (≤1 ✅), FN 5, yanlış güzergâh 0 (=0 ✅); `val82`: rota 30, maske yok
35, TP 28, FP 2, FN 15, yanlış güzergâh 7. Terfi kullanıcı kararıyla; eşikler değişmedi; v35
(`e00f6b8e…`) yedek olarak durur. Kapsam sınırı (§3.3.4.2.6): denetçi her koşumda "tamamı SENTETİKTİR"
basar; arena benzeri saha kanıtı yok; maket çekimi yapılmayacak. Kapı olmayan ölçümler (§3.3.4.2.7):
karar çevrilmesi v36 14/260 · 15/260 (v35 9 · 11 — **v35'ten kötü**); çatı kaçağı 0,0230; gerçek kare
zemin kaplaması tuval 0,2346 / içerik 0,4171 (bağımsız tahmin %47–52'nin altında); mask mAP50-95 0,155
(karar girdisi değil).

"Benzer koşullar" ve doğruluk matrisi (§3.3.4.2.8): farklı ışık/gölge ÖLÇÜLEMEDİ (üreteçte ışık
parametresi yok). Karışıklık matrisi 7 Eylül'de `test29` üzerinde piksel düzeyinde ÖLÇÜLDÜ
(`scripts/olcum/176_piksel_karisiklik_matrisi.py`, `results/gece_20260907/karisiklik/`, 240 537 600 px,
CPU, CONF 0,30): zemin→zemin 0,509, engel→engel 0,759; IoU zemin **0,4922**, engel **0,7400**
(etiketli payda); etiketsiz pay %39,6; 16/29 karede zemin tahmini hiç yok. Örnek düzeyi (`model.val`):
maske P 0,7196 · R 0,2114 · mAP50 0,1860 · mAP50-95 0,0672. Eğitim-val matrisi (n=73, conf 0,25):
68/0/22 · 0/108/55 · 70/132 — yönergenin istediği matris DEĞİL. Sınır: küme doğrulama kümesidir,
arena değildir.

### 3.3.4.3 Haberleşme paket yapısı

Çerçeve: tek satır JSON, UTF-8 (`comms/protocol.py:216 encode / :222 decode`), `allow_nan=False`;
tampon tavanı 64 KiB; bozuk satır atılır; **CRC/checksum YOK** (bilinçli, ölçülmemiş risk). Ortak
alanlar `v` (=1), `type`, `seq`, `t`. HEARTBEAT telemetri alanları: `x, y, alt, hiz, yon, bat, bat_yuzde,
uydu, karar_yas, lat, lon, gps_fix, armed, mod, pixhawk_canli`. Hakem kanıt kaydı (`CONTRACTS.md`
§6.8, `comms/hakem_kaydi.py`, JSONL, satır başına fsync): 16 olay (`YKS_ARAYUZ_HAZIR`, `ROTA_ALINDI`,
`ROTA_REDDEDILDI`, `ROTA_YOK`, `ACK_ALINDI`, `IKA_AKTARIM_KANITI`, `HAKEM_ONAYI_1/2`, `HAKEM_ONAYI_REDDI`,
`IHA_INIS_KANITI`, `KAMERA_KANIT`, `TELEMETRI_KANIT`, `ACIL_SENARYO`, `KRONOMETRE_BASLADI/BITTI`,
`UI_OLAYI`); tekrar aralığı 30 s; 22 test. 5 Eylül saha kaydı: 1115 satır, 277 dk, rota/onay olayı yok
(İHA hatta değildi).

ACK'li tekrar (§3.3.4.3.2): `OPEN_ROUTE`/`NO_ROUTE`/`IHA_LANDED` 0,25 s × 8 (2,0 s); `IKA_GO` 0,25 × 20
(5,0 s); `PARACHUTE` 0,20 × 40 (8,0 s); `ARM/DISARM/RTL/LAND` 0,25 × 20 (5,0 s), DISARM teyit 4,0 s;
Pixhawk `COMMAND_ACK` tavanı 0,5 s. Kritik komut ACK'i güçlü biçim (`ref_cmd`, `sonuc="ACCEPTED"`).
Komut hattı (D-419/D-422): `COMMAND_ACK` yalnız yetkili bileşenlerden; saat ofseti iki kademeli eşik
(bant içi 2 örnek, bant dışı 6; pencere 60 s; adım eşiği 8 s); replay savunması `(oturum, seq, cmd)` +
adres pini. Replay çürütmesi: aynı anahtar 40 kez → 1 `COMMAND_LONG`; 2 saat sapma / 1970 Jetson 7.
basamakta geçer; ileri adım ölü penceresi 60,00 s → 0,25 s. `tests/test_iha_komut_saat_ve_tekrar.py` 42
test. **Tamamı `scripts/sahte_pixhawk.py` ile PC'de**; gerçek Pixhawk'ta ÖLÇÜLEMEDİ.

Ölçülen gecikmeler (§3.3.4.3.3, `results/fda_butce/olcum_20260901.json`, 33 kare): önişleme 5,0/7,1 ·
çıkarım 12,3/14,9 · maske 17,5/24,1 · karar 49,7/68,6 · telsiz+ACK 2,3/2,6 · **TOPLAM 84,8/113,2 ms**
(p50/p95). Model yükleme 2,64 s (bütçe dışı). Düzeltme: ilk 307,6 ms `link.recv` soket zaman aşımı
sabitiydi (loopback RTT 0,06 ms). Seri köprü ACK turu 622,6 ms → 0,8 ms (D-403 §3). Hiçbiri RF ölçümü
değildir. ÖLÇÜLEMEDİ (§3.3.4.3.4): SiK RTT/paket kaybı (`scripts/sik_rf_olc.py` yazıldı, hedef RTT p95
< 0,20 s), veri hızı, menzil (DDR ">%98, 300 m" kanıtsız), SiK firmware/baud, gerçek `COMMAND_ACK`,
gerçek kamera yakalama gecikmesi.

### 3.4 Yönerge dışı ek kanıt

Yazılım açıkları (§3.4.1): A1 gerçek İKA motor sürücüsü; A2 Gazebo temas koşusu; A3 TensorRT denkliği
(bayat — bkz. §3.3.1.1.12); A4 karar kararsızlığı kök nedeni modelde; A5 `min()` duvar saati zayıflığı;
A6 FDA kipi denetim borcu. §3.4.3 iddiası: ön kayıt, `ÖLÇÜLEMEDİ ≠ GEÇTİ`, mutasyon kontrolü, çürütme
kaydı (yanlış sayılar silinmez, üstü çizilir).

---

## 4. "Beyan" ile "ölçüldü" ayrımı

FDR üç etiket kullanır (`BOLUM_3` §3.0 tablosu; §3.3.1.1.7 tablosu "tür" sütunu):
- **ÖLÇÜM**: bir artefakt (JSON/log/Mission Planner `Messages` satırı) ve üreten betik var.
- **BEYAN / BEYAN GEREKLİ (insan)**: takım üyesinin sözlü/yazılı bildirimi; artefakt yok. "Etiket
  fotoğrafı gelene kadar BEYAN kalır, ÖLÇÜM değildir" (§3.2.1.1.1).
- **ÖLÇÜLEMEDİ**: ölçüm yapılmadı; geçmiş sayılmaz. **DOĞRULANACAK**: emin olunmayan.
Etiketli satırlar `scripts/fdr_acik_kalem_cikar.py` ile çıkarılıp sayılır (197 satır, `ACIK_KALEMLER.md`).

Hâlâ BEYAN olan kalemler (Bölüm 3'te açıkça işaretli):
- Motor künyesi **SunnySky X2220 980KV V3 ×4** — BEYAN, etiket fotoğrafı yok (D-435, §3.2.1.1, §3.2.1.1.1).
- Pervane **10×4,5 (1045)** — BEYAN; veri sayfasında satır yok (§3.2.1.1).
- ESC **Hobbywing Skywalker 60A V2** — BEYAN, etiket (§3.2.1.1, D-428 §1); "80 A DShot" planı geçersiz.
- Güç modülü **PM06** (plan PM02) — BEYAN, etiket BEYAN GEREKLİ (§3.3.1.1.7).
- Pil **4S 10 Ah 25C** — C değeri DOĞRULANMADI (§3.2.1.1.1).
- Motor testi 4/4 doğru yön — test koştu ÖLÇÜM, 4/4 BEYAN, video yok (§3.3.1.1.7).
- Accel + level kalibrasyonu "yapıldı" — BEYAN teyitsiz; ESC kalibrasyonu 6 Eylül — beyan (D-428 §3).
- Uçuş modları SwC Stabilize/Loiter/RTL — BEYAN (§3.3.1.1.11).
- SiK hattı 5 Eylül'de bağlandı — BEYAN; RTT/kayıp/menzil ÖLÇÜLEMEDİ (§3.3.4.3.4).
- Kamera FOV 55–63° — lens hesabı, ölçüm değil (§3.2.1.1, §3.4.2).
- Tüm donanım künyesi kaynağı `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 — "kullanıcı beyanı" (Kanıt dizini).
- Pixhawk ↔ Jetson UART pinleri ve UBEC besleme yolu — DOĞRULANACAK (§3.3.2.1).
- Yarışma aracı, mancınık, paraşüt, İKA mekanik künyesi — BEYAN GEREKLİ (§3.2.1.2, §3.2.2, §3.2.3).

ÖLÇÜM'e dönüşenler: ArduCopter V4.5.7 (2a3dc4b7), `Frame: QUAD/X`, u-blox M9N satırı, `RCInput: decoding
IBUS(1)`, PreArm satırlarının kaybolması (D-426 §1); Jetson kartı kimliği, CUDA, FPS, engine denkliği
(D-431); karışıklık matrisi (7 Eylül); `RC_SPEED` 490 dökümü (D-428).

---

## 5. Yazılımın anlatıldığı yerler ve kanıt yolları

| madde | ne | kanıt yolu | D-kaydı |
|---|---|---|---|
| §3.3.1.1.2–3, §3.3.4.3.1 | mesaj sözleşmesi, ACK `ref_tip` | `CONTRACTS.md` §6, §6.6; `comms/protocol.py`; `tests/test_faz_b_ack_ref_tip.py` (14) | D-405, D-406 |
| §3.3.1.1.8 | MAVLink çoğullayıcı, 4 Hz / 1 Hz kapı | `CONTRACTS.md` §7.4; `scripts/mavlink_dogrula.py`; `tests/test_seri_pixhawk_kilidi.py` 13/13 | D-403, D-419 |
| §3.3.1.1.9 | SiK hub | `comms/seri_hub.py`; `tests/test_faz_b_seri_hub.py` (31) | D-404, D-405 |
| §3.3.1.1.10 | akış isteği | `tests/test_faz_b_akis_istegi.py` (17) | D-406 |
| §3.3.1.1.11 | Pixhawk şablonu, 221,5 s | `config/pixhawk/arducopter_fda.param`, `fda_gorev.waypoints`; `tests/test_faz_b_pixhawk_sablon.py` (16) | D-424/425/426/428/429 |
| §3.3.1.1.12, 15 | Jetson yığını, FPS | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`, `…_10dk/ozet.json`, `tegrastats.log`, `jetson_log_20260906/engine_karar_denkligi.json`, `genel_kapi.log` | D-431 |
| §3.3.1.3.1 | kuru koşu 9/10 | `results/saha_kuru_kosu_20260904_095222/ozet.json`; `scripts/saha_kuru_kosu.py` | — |
| §3.3.4.1.1 | algı zinciri | `codes/rpi_inference.py` satır numaraları (commit `64cd543`) | — |
| §3.3.4.1.5 | ölçek / HB doğrulama | `CONTRACTS.md` §5.1/§5.4; `tests/test_olcek_ve_c_uzayi.py` | D-105 |
| §3.3.4.1.7 | histerezis | `results/p5_histerezis/olcum_20260903.json`, `ON_KAYIT.md`; `tests/test_p5_h1c_damgasi.py` 23/23 | D-396, D-419 |
| §3.3.4.1.9 | sınıf şeması | `codes/sinif_semasi.py`; `codes/test_sinif_semasi.py` 8/8 | — |
| §3.3.4.1.12–13 | hakem onayı, İKA kilidi | `tests/test_ika_go_ackli_tekrar.py`, `tests/test_iha_landed_gate.py:313`, `tests/test_p9e_branda_temas.py` | D-02, D-386, D-391, D-393 |
| §3.3.4.1.15 | FDA kipi | `CONTRACTS.md` §6.7; `tests/test_faz_b_yks_fda_kipi.py` (9, 4/4 mutant) | D-407, D-408 |
| §3.3.4.1.17 | akış diyagramları | `FDR/sekiller/akis_a..e.svg`, `_dugumler.md`; `tests/test_gece_akis_diyagramlari.py` 13/13 | — |
| §3.3.4.2.1 | model künyesi | `config/model_registry.json`; `results/t79/onnx_denklik_v36.json` | D-284, D-375 |
| §3.3.4.2.3 | K0–K8 | `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json`; `65_kabul_denetcisi.py` | D-107, D-332, D-334, D-386 |
| §3.3.4.2.5 | geçilmeyen eşikler | `results/gece_20260826/gece_v7a_olcum.json`, `ON_KAYIT.md` §15, `v7a_curut/` | D-293, D-294 |
| §3.3.4.2.8 | karışıklık matrisi | `results/gece_20260907/karisiklik/piksel_karisiklik_test29.{json,md,png}`; `tests/test_gece_karisiklik_matrisi.py` (10) | D-315 |
| §3.3.4.3.1 | hakem kanıt kaydı | `comms/hakem_kaydi.py`; `results/prova/20260905_142958_15092/hakem_log.jsonl`; `tests/test_yks_hakem_kanit_olaylari.py` 22/22 | D-412, D-419 §2, D-427 |
| §3.3.4.3.2 | komut hattı, replay | `comms/iha_komut_alici.py`; `tests/test_iha_komut_saat_ve_tekrar.py` (42) | D-419 §1, D-422 |
| §3.3.4.3.3 | gecikme p95 113,2 ms | `results/fda_butce/olcum_20260901.json`; `scripts/olcum/169_fda_butce_olcumu.py` | D-382, D-383 |
| §3.3.1.1.15 | FPS eşiği 0,61 | `results/b4_fps/p_ve_kosu_20260901.json`; `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 | D-374, D-376, D-377 |

---

## 6. ACIK_KALEMLER.md — kısa liste

197 etiketli satır; gruplar:
1. **5 Eylül ölçümü** (#1–8): kalkış kütlesi/CG/parça tartısı; kamera FOV ölçümü; gerçek Pixhawk
   MAVLink kapısı (açık — Pixhawk Jetson'a bağlı değildi); ~~#4 Jetson FPS~~ ve ~~#5 arka uç kararı~~
   6 Eylül'de ÖLÇÜLDÜ (D-431, `.pt` GPU); SiK RTT/kayıp; ArduCopter sürüm/kalibrasyon (KISMEN — 4.5.7
   ÖLÇÜM, motor testi BEYAN); parametre dökümü (6 Eylül alındı, üçüncü döküm şart).
2. **6–19 Eylül uçuş testleri** (#9–13): titreşim/pusula/GPS; canlı iniş kanıtı zinciri; uçtan uca
   ≤ 10 dk (üç prova); hover/tepe akımı ve uçuş süresi; Adıyaman gerçek koordinatları.
3. **Kapanmayacak sınır** (#14–16): gerçek arena karesi yok; TensorRT engine "denklik düştü" (6 Eylül);
   ~~#16 Gazebo temas~~ yeniden AÇILDI (yönerge 3B simülasyonu puanlıyor, D-417).
4. **İnsan beyanı** (#17–22): ~~ekip isimleri~~ düştü (yönerge isim yasaklıyor); birim fiyatlar/tedarik;
   3B baskı süreleri/filament/kütleler; üretim zorlukları ve revizyon gerekçeleri; yarışma aracı ve
   İKA mekanik künyesi; montaj fotoğrafları ve videolar.
4b. **Yazılım kilit/damga** (#23–25): üçü de 4 Eylül'de KAPANDI — tek-yazar seri kilidi (13/13), H1c
   damgası (23/23), hakem kanıt olay kümesi 16 olay (22/22 + 6/6).
5. **Rapor içi iş**: Bölüm 1 sonradan yeniden üretilecek; donanım revizyon tablosu Bölüm 3/5/7'de aynı
   olmalı; FDA kipi denetim borcu.
6. **Yönergeden gelen yeni kalemler** (#26–44): uçuş bilimleri (26), İHA yapısal analiz (27), İKA
   yapısal (28), mancınık yapısal + yay sabiti/enerji (29), 3B görev simülasyonu + video (30), renk
   kodlu şemalar (31), kablaj hesapları (32), güç tüketimi (33), ekipman kabul testleri (34), menzil
   testi (35), IMU/pusula/pitot kalibrasyon kanıtı (36), 🔴 arıza emniyet sahada (37), sensör/test
   takvimi (38), üretim hataları prosedürü (39), 🔴 kol reçete farkı gerekçesi (40), pasta grafiği
   (41), maliyet karşılaştırması (42), KYS teyidi (43), organizasyon şeması (44). 26–29 ve 31 beyanla
   kapanmaz; mühendislik çıktısıdır.

---

## 7. Muhtemel 15 jüri sorusu ve FDR metnine dayanan cevaplar

1. **"Görev test uçuşunda hangi aracı uçuracaksınız; yarışma aracı nerede?"** — Görev test uçuşu
   (§5.3.2, 30 Eylül–3 Ekim) 3B baskı quadcopter ile; yarışma aracı (sabit kanat + mancınık + paraşüt +
   İKA) henüz üretilmemiştir; 3.1 ve 3.2.3 başlıkları o araca aittir ve BEYAN GEREKLİ durumundadır
   (`BOLUM_1` giriş; `BOLUM_3` §3.0.1, §3.2.1.2).

2. **"Modeliniz nedir, hangi çözünürlükte, hangi donanımda kaç FPS?"** — `navitas-seg-v36-512`,
   YOLOv8m-seg 27,2 M parametre, imgsz 512, PyTorch GPU; Jetson Orin Nano Developer Kit 4 GB'de 120
   örnekte p50/p95 1,35/1,06 FPS (`.pt`), engine 1,58/1,33; eşik 0,61 → GEÇTİ (§3.3.4.2.1, §3.3.1.1.15,
   D-431). Sınır: kareler diskten, kamera bağlı değildi.

3. **"0,61 FPS eşiği nereden geliyor?"** — `GEREKLI_FPS ≥ 1/(5·p)`; tazelik 5 s, en kötü gerçek küme
   p=0,3261 → 0,613; sızıntı ayıklandıktan sonra (D-376) (§3.3.1.1.15).

4. **"Neden TensorRT engine ile uçmuyorsunuz, daha hızlı?"** — Engine derlendi (1,58 FPS) ama engine↔pt
   karar denkliği D-303 oransal 3/126 ile DÜŞTÜ (eşik 5/260); üretime alınmadı; uçuş `.pt` GPU ile
   (§3.3.1.1.12, §3.3.1.3.2 6 Eylül tablosu).

5. **"Görüntü işleme doğruluğunuz nedir; karışıklık matrisi var mı?"** — Sentetik arenada K7 şerit
   doğruluğu 84/85 (%98,82); kör `test29` üzerinde piksel matrisi IoU zemin 0,4922 / engel 0,7400;
   örnek düzeyi maske P 0,7196 · R 0,2114 · mAP50 0,1860. Farklı ışık/gölge kesiti ÖLÇÜLEMEDİ; küme
   arena değil (§3.3.4.2.3, §3.3.4.2.8).

6. **"Üretim modeli kabul kapılarını geçti mi?"** — Sentetik K0–K8 + K5A 10/10 GEÇTİ; ama gerçek kare
   ön kayıtlı iki eşiği (ROTA ≥10 → 8; MASKE_YOK ≤10 → 16) geçmeden kullanıcı kararıyla terfi etti;
   eşikler değişmedi; gerekçe yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3 (§3.3.4.2.5).

7. **"Sahada model kör kalırsa ne olur?"** — Gerçek kayıtta 51 s'lik kör aralık ölçüldü (46/51 kare
   `MASKE_YOK`); her karede `NO_ROUTE` + sebep yayınlanır; HEARTBEAT `karar_yas` taşır, hakem tespitin
   yaşını görür; hat canlılığı algı canlılığı sayılmaz (`BOLUM_1` §Y-1-M05; §3.3.4.1.16, D-374).

8. **"Yanlış güzergâh 0 puan; buna karşı tasarım nedir?"** — Fail-closed: ölçek yoksa rota üretilmez,
   güven < 0,20 ret, zemin maskesi şüpheliyse ret, ölçek kaynakları çelişirse ortalama alınmaz; 15
   kanonik ret kodu; serbest alanı büyüten işlem yasak (§3.3.4.1.2, §3.3.4.1.5, §3.3.4.1.10).

9. **"Uçtan uca gecikme nedir?"** — p50 84,8 / p95 113,2 ms (33 gerçek kare, UDP loopback); ilk
   ölçümdeki 457,8 ms'nin 307,6 ms'si soket zaman aşımı sabitiydi, düzeltildi ve kayıtta üstü çizili
   (§3.3.4.3.3, D-382/D-383). RF üzerinde hiçbir sayı ölçülmedi (§3.3.4.3.4).

10. **"Telemetri hattınızın menzili ve paket kaybı?"** — ÖLÇÜLEMEDİ. 2 × SiK 433 MHz; `scripts/sik_rf_olc.py`
    yazıldı (hedef RTT p95 < 0,20 s), koşulmadı; DDR'deki ">%98, 300 m" kanıtsız (§3.3.4.3.4, ACIK #6).

11. **"İKA nasıl hareket izni alıyor; İHA inmeden hareket riski?"** — `sür ⟺ OPEN_ROUTE ∧ İHA indi ∧
    IKA_GO`; iniş kanıtı Pixhawk `EXTENDED_SYS_STATE ON_GROUND` + `relative_alt < 1 m`, aynı sysid, 3
    ardışık çift; manuel "İHA İNDİ" düğmesi latch'i açmaz (§3.3.4.1.13). Gerçek İKA motor sürücüsü yok,
    donanım tedarik edilmedi (§3.2.2, §3.3.1.3.1 halka 10).

12. **"Arıza emniyeti (RTL, motor kesme) sahada test edildi mi?"** — Hayır. `FS_THR_ENABLE,1`,
    `FS_GCS_ENABLE,1`, `BATT_LOW/CRT 14,4/14,0 V`, `FENCE 50 m / 60 m`, `RTL_ALT 35 m` parametre ve
    testle kilitli; gerçek uçuşta tetiklenmedi (`BOLUM_1` §Y-1-M08 "ÖLÇÜLEMEDİ"; `Y-4-M12` YOK); RC
    failsafe 5 Eylül'de ÖLÇÜLEMEDİ (§3.3.1.1.11).

13. **"Motor/ESC/pil bütçeniz uçuşu karşılıyor mu; kütle ne?"** — Kütle tartılmadı (T10 ÖLÇÜLEMEDİ);
    motor SunnySky X2220 980KV V3 BEYAN (etiket yok); veri sayfası 4 × 2130 g = 8520 g, tam gaz 38,4 A
    motor başına 38 A/30 s sınırında; hover akımı ÖLÇÜLEMEDİ; kapı (≤ %50 ∧ I_hover ≤ I_sürekli)
    kapanmadan güç verme yok (§3.2.1.1.1, T211). 6 Eylül'de devrilmeler ve M1'de duman kaydı (D-429,
    D-434/D-435).

14. **"Üç boyutlu görev simülasyonunuz ve videosu nerede?"** — ÖLÇÜLEMEDİ: Gazebo iskeleti (7 dünya,
    SDF primitifler, mesh 0) var; koşum, ölçüm ve `simulation/recordings/` yok; `gz`/`podman` bu
    makinede yok; CAD sabit kanat/İKA için yok (§3.3.3.1–3).

15. **"Sayılarınız güncel mi; hangi tarihe ait?"** — Her tablo yazıldığı andaki koşumu gösterir; ilerleme
    tarihli izlenir: tam süit 1875 (D-408) → 1896 (3 Eylül) → 2138 (5 Eylül, 1 ortam FAIL) → kartta 2121
    (F5 E30 S8); defter 414 → 420 → 424/418 → 432. Bölüm 1 teslim öncesi yeniden üretilecek (README
    "Sayı künyesi"; `BOLUM_1` DOĞRULANACAK satırları; §3.3.1.3.2).

### Ek: metin içi tutarsızlıklar (jüri sorusu olabilir)

- `BOLUM_1` §Y-1-M07 "31 parametre" ↔ `BOLUM_3` §3.3.1.1.11 "48 parametre" (7 Eylül).
- §3.3.1.1.8 "kilit yalnız `iha_komut_alici`'da" ↔ ACIK #23 "üç sürece genişletildi, 13/13".
- §3.3.4.1.7 "H1c damgalanmadı" ↔ ACIK #24 "H1c KAPANDI 23/23".
- §3.4.1 A3 "engine ÖLÇÜLEMEDİ" ↔ §3.3.1.1.12 "engine ölçüldü, denklik DÜŞTÜ".
- §3.3.4.2.1 `.engine` = RED yer tutucu ↔ 6 Eylül `turev_eslesti`.
- Kanıt dizini ilk K0–K8 satırı K4 3/256 · K6 3/256 (28 Ağustos) ↔ kapı tablosu 2/256 (1 Eylül) —
  §3.3.4.2.4 iki hattı açıklar.
- `YONERGE_HARITASI` özet tablosu 3.3 için VAR 0 ↔ aynı dosyada `Y-3.3.4-M01` VAR.
