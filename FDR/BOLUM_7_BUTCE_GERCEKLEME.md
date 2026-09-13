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
**tedarik durumu kesim tarihi 13.09.2026**'dır. Ara kayıtlar: **5 Eylül kutu açılışında** üç kalem
plandan farklı ya da teyitli çıktı (ESC, güç modülü, RC alıcı — `REVIEW_LOG.md` D-426 §3, BEYAN);
**12 Eylül 23:55 kart dökümü** (`config/pixhawk/emir.param`) ise künyeyi **ölçümle** günceller:
`STAT_FLTTIME` **0 → 273 s** (döküm satır 980) → araç **toplam 4 dk 33 sn uçtu**; `STAT_BOOTCNT`
**48 → 96** (satır 979); pusula/ivmeölçer/jiroskop (`COMPASS_OFS/DIA/ODI`, `INS_ACC*`, `INS_GYR*`)
yeniden kalibre edildi (`config/pixhawk/PARAMETRE_KILAVUZU_1SAYFA.md`:6-9). Bu tek ölçüm
A8/A10/A12/A13/A14/A15 satırlarının **çalıştığı** hükmünü beyandan ölçüme taşır: yanlış bağlanmış
bir itki ya da seyrüsefer zinciriyle karta 273 s uçuş süresi yazılamaz.
⚠ **Ölçüm işlevi kanıtlar, kimliği değil** — hangi marka/model motorun, ESC'nin ya da güç modülünün
takılı olduğu hâlâ **BEYAN**dır (D-426 §3, D-435).
⚠ **Tartı sütunu kapandı:** 5 ve 12 Eylül tutanaklarının ikisinde de tartı satırı yoktur
ve kullanıcı 10 Eylül'de tartıyı gereksiz görmüştür (`REVIEW_LOG.md` D-439, satır 30425). Bu yüzden
"Ölçülen kütle" sütunu **tartıyla dolmayacaktır**; kütleler 3B basılan parçalar için **HESAP**
(3mf katı hacmi × malzeme yoğunluğu × ölçülü dolgu katsayısı), satın alınan alt sistemler için
**DDR BEYANI** — yalnız veri sayfası gerçekten okunan kalemlerde **ÜRETİCİ VERİSİ** — etiketiyle ve
türetmesiyle verilmiştir. Hiçbir hücre boş bırakılmamıştır.
`Ü` = takım üretimi, `S` = hazır satın alınan alt sistem.

| # | Kalem | Model / özellik | Adet | Tür | Üretim yöntemi | Üretim süresi | CAD kütlesi (g) | Ölçülen kütle (g) | Tedarik durumu | Birim fiyat | Toplam fiyat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Kol | `Drone_Arm` (ABS) | 4 | Ü | FDM 3B baskı — kol 1–2 **0,20 mm / %15 / 2 duvar**, kol 3–4 **0,16 mm / %40 / 6 duvar** (ÖLÇÜLDÜ: `project_settings.config`, `Plaka1_Kol_1-2.3mf` / `Plaka2_Kol_3-4.3mf`) | **≈ 1 sa 53 dk** (kol 1–2 plakası: baskı kütlesi 69,9 g ÷ 37,1 g/sa) · **≈ 3,5–4,7 sa** (kol 3–4 plakası: 105–140 g ÷ 37,1 × 1,25) — **HESAP**: verim 37,1 g/sa ÖLÇÜLDÜ (55,86 g ÷ 1,504 sa, kanıt #9); ×1,25 = 0,16 mm katman düzeltmesi | **69,9 g/adet · 279,6 g (4 adet) — HESAP**: katı hacim **67,20 cm³**/adet (3mf üçgen ağı işaretli hacim toplamı, bu oturumda yeniden hesaplandı) × ABS **1,04 g/cm³** | **34,9 g/adet (kol 1–2) · 52–70 g/adet (kol 3–4) — HESAP**: k = **0,500** ölçülü dönüşüm (55,86 g gerçek / 111,66 g CAD, Plaka4 aynı reçete); kol 3–4 için k = 0,75–1,00 (6 duvar + %40). Tartı **yapılmayacak** (D-439) | Üretildi | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A2 | Üst çerçeve | `Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid / 2 duvar | **1 sa 30 dk 16 sn** (ölçüldü) | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A3 | Alt çerçeve | `Lower_Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A4 | Kubbe | `Drone_Dome` (ABS, **destekli**) | 1 | Ü | FDM, X1C | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A5 | Ayak | `Drone_Legs` (ABS, **destekli**) | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A6 | GNSS tutucu | `GPS_Holder` (ABS, **destekli**) | 1 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A7 | Taban pedi | TPU 95A | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A8 | Motor | ~~**5008 340KV**~~ → **SunnySky X2220 980KV V3** (BEYAN, etiket fotoğrafı yok; 7 Eylül beyanı, D-435) | 4 | S | — | — | — | **85 g/adet · 340 g (4 adet) — ÜRETİCİ VERİSİ** (kablo dâhil; veri sayfası http://en.rcsunnysky.com/x-fixedwingseries/53.html — `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md`:302) | Kutu açıldı 5 Eylül; motor testi koştu (ÖLÇÜM `starting motor test` → `finished motor test`, D-426 §1). **12 Eylül dökümü — sıra/yön için ÇIKARIM (doğrudan ölçüm değil):** `STAT_FLTTIME` 0 → **273 s** (`emir.param`:980) ve `FRAME_CLASS=1` / `FRAME_TYPE=1` (Quad-X, :395-396) → yanlış motor sırası ya da yanlış dönüş yönüyle bir Quad-X havalanamayacağından 4/4 sıra/yön **çıkarımla** doğrulanmış sayılır; doğrudan kanıt (sıra/yön videosu) hâlâ **BEYAN GEREKLİ**. ⚠ Bu iki parametre **motor modeli** hakkında hiçbir şey söylemez — model **BEYAN**dır. **7 Eylül:** 5008'ler iade edildi, X2220'ler 2 yıl önce kullanılmış eski motorlar (BEYAN, D-435) — **iade tutarı: KAYIT YOK** (§Y.2, 13.09.2026), tek parasal açık kalem budur | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A9 | Pervane | ~~**12×10**~~ → **10×4,5 (1045)** (7 Eylül beyanı, D-435) | 4 (+ yedek set) | S | — | — | — | BEYAN GEREKLİ | Kutuda; **yedek set alınacak** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A10 | ESC | plan **80 A, DShot destekli**; 5 Eylül kutudan **Hobbywing Skywalker 60 A V2** çıktı (etiket beyanı — `REVIEW_LOG.md`:29962, D-428; D-426 §3'te "60 A V2"). 🔴 **DShot yolu GERÇEKLEŞMEDİ — ÖLÇÜM:** `MOT_PWM_TYPE = 0` = *Normal PWM* (`emir.param`:569); araç 273 s'lik uçuşu **düz PWM** ile yaptı | 4 | S | — | — | — | **≈ 60 g/adet · 240 g (4 adet) — HESAP (benzetme, DOĞRULANMADI)**: tek taban DDR'nin **plan** tablosudur (`ddr_requirements.md`:51, FlyFun 40 A ×2 = 70 g → 35 g/adet, **BEYAN**); 40 A → 60 A sınıf farkı için uygulanan **×1,7 katsayısının kaynağı YOK**. Skywalker 60 A V2 veri sayfası okunmadı, ESC tartılmadı — hücre veri sayfası gelene ya da 4 ESC tartılana kadar **açıktır** | **Kalibre EDİLMEDEN uçuruldu (ÖLÇÜM, `emir.param` 12 Eyl):** `MOT_SPIN_ARM = 0,1` (:574) ve `MOT_SPIN_MIN = 0,15` (:576) **fabrika değerinde**, buna rağmen `STAT_FLTTIME = 273 s` (:980). Yani "ESC kalibrasyonu YAPILMADI" satırı artık bir plan eksiği değil, **ölçülmüş bir uçuş koşuludur** | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A11 | Güç dağıtım kartı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A12 | Uçuş kontrolcüsü | **Pixhawk 6C** — fabrikadan PX4 ile geldi; ArduCopter **4.5.7** flash edildi ve sabitlendi (ÖLÇÜM `ArduCopter V4.5.7 (2a3dc4b7)`, D-424/D-425/D-426) | 1 | S | — | — | — | **59 g — DDR BEYANI** (`ddr_requirements.md`:35; Holybro veri sayfası okunmadı, üretici verisi değildir) | Kutu açıldı 5 Eylül; **12 Eylül dökümüyle ÖLÇÜM:** `STAT_FLTTIME = 273 s`, `STAT_BOOTCNT = 96` (`emir.param`:980/:979), pusula+IMU yeniden kalibre → kart çalışıyor ve **uçtu** | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A13 | Güç modülü | plan **PM02** (Pixhawk kutusundan); 5 Eylül kutudan **PM06** çıktı (BEYAN, D-426 §3) — etiket BEYAN GEREKLİ | 1 | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; `POWER1`'e 6 pinli kabloyla bağlı, çalışıyor (ÖLÇÜM: pil PreArm uyarısı kayboldu, D-426 §1) | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A14 | GNSS / pusula | **Holybro M9N** | 1 | S | — | — | — | **≈ 32 g — BENZETME (HESAP, DOĞRULANMADI)**: `ddr_requirements.md`:41 **M10** için 32 g verir; takılı donanım **M9N**'dir ve kütlesi okunmadı — M9N veri sayfası gelene kadar bu bir benzetmedir, **üretici verisi değildir** | Kutuda ve **takılı**: pusula 12 Eylül'de yeniden kalibre edildi (ÖLÇÜM — `COMPASS_OFS/DIA/ODI` değerleri 6 Eylül dökümüne göre değişti; `config/pixhawk/PARAMETRE_KILAVUZU_1SAYFA.md`:8-9) ve 273 s'lik uçuş bu pusulayla yapıldı | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A15 | RC kumanda + alıcı | **FlySky FS-i6** + FS-iA6B (iBUS) — FS-iA6B 5 Eylül'de teyit (B harfi, D-426 §3) | 1 set | S | — | — | — | BEYAN GEREKLİ | Kutu açıldı 5 Eylül; **bind edildi** (BEYAN), `RCInput: decoding IBUS(1)` (ÖLÇÜM, D-426 §1); alıcı `i-BUS SERVO` portu | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A16 | Telemetri | ~~**SiK 433 MHz**~~ → 🔴 **RFD900A @ 915 MHz** (ÖLÇÜM, 13 Eylül: telsiz sürüm dizesi `RFD SiK 1.9 on RFD900A FREQ_915` — `HANDOFF_20260913.md`:11-24). Tüm önceki belgeler "SiK 433 MHz" diyordu; **künye yanlıştı**, düzeltme T267'de açık | 2 | S | — | — | — | **≈ 35 g/adet · 70 g (2 adet) — DDR BEYANI, FARKLI ÜRÜN İÇİN (DOĞRULANMADI)**: `ddr_requirements.md`:40 ve :59 **Holybro SiK 433** içindir; takılı telsiz **RFD900A**'dır ve kütlesi okunmadı. **Uçan kütleye giren yalnız 1 adet**, ikincisi YKS tarafındadır | Kutuda ve **çalıştı**: A5 bağlantı kaybı testi gerçek telsizle 12 Eylül'de GEÇTİ (BEYAN — `REVIEW_LOG.md`:30882, D-473) | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A17 | Görev bilgisayarı | ~~**Jetson Nano 4GB** (Dev Kit)~~ → **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12; 3 Eylül beyanı 'Nano 4GB' 6 Eylül'de kartla YANLIŞLANDI — D-431) | 1 | S | — | — | — | BEYAN GEREKLİ | Teslim alındı; **6 Eylül kuruldu**, genel kapı 15/15 ve FPS kapısı GEÇTİ (ÖLÇÜM, D-431) | BEYAN GEREKLİ | BEYAN GEREKLİ |
| ~~A18~~ | ~~microSD~~ | ~~≥ 64 GB UHS-I + okuyucu~~ → **KALEM DÜŞTÜ** | 0 | — | — | — | 0 g | **Gereksiz — ÖLÇÜM:** kartta **microSD yuvası yok**, kök **NVMe 233 GB** ile geldi ve JetPack 7.2.1 kurulu çıktı (`results/jetson_20260906/JETSON_KESIF_RAPORU_20260906.md`:45 "Kök **NVMe** 233 GB, 21 GB dolu · microSD yok, eMMC yok"; D-431 / D-413). Alışveriş listesinden çıkarıldı | **0** (harcanmadı) | **0** (harcanmadı) |
| A19 | Kamera | **Raspberry Pi HQ** (IMX477, CSI) + **6 mm lens**, montaj **nadir 90°** (kullanıcı cevabı, 12 Eylül — D-471) | 1 | S | — | — | — | **Kütle ÖLÇÜLEMEDİ — kamera elde değil.** `ddr_requirements.md`:37'deki 50 g **Arducam IMX477** içindir; takılacak ürün **Raspberry Pi HQ**'dur (farklı ürün, farklı kütle). Uçan kütleye bugün **0 g** girer | 🔴 **TEMİN EDİLMEDİ** — kamera elde değildir ve **14 Eylül FDR teslimine yetişmemektedir** (kullanıcı bildirimi, 13 Eylül; D-473: "A11 kamera 14 Eylül'e yetişmiyor"). **FOV artık hesapla biliniyor** (ölçüm gerekmez): IMX477 aktif alan **6,287 × 4,712 mm** (4056 × 3040 px × 1,55 µm), 6 mm lens → **FOV_yatay = 55,3° (HESAP)** = 2·atan(6,287/12) · **FOV_dikey = 42,9° (HESAP)** = 2·atan(4,712/12) · köşegen 66,4°. 30 m nadirde kare **31,4 × 23,6 m** → 20 × 20 m alan **sığar**; GSD = 30 000 × 0,00155 / 6 = **7,75 mm/px (HESAP)**. Bu, `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md`:283-285'teki 55–63° bandıyla tutarlıdır. Doğrulama ölçümü: `kamera_dogrula`, kamera temin edildiğinde | **KAYIT YOK** (§Y.2, 13.09.2026) | **0** (bugüne kadar harcanmadı) |
| A20 | Jetson besleme | **UBEC 5 V / 5 A** | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A21 | Pil | ~~**4S 10 Ah 25C**~~ → **3S 8000 mAh** (kullanıcı kararı, gerekçe **stabilite**; 12 Eylül). Kart eşikleri 6 Eylül'den 12 Eylül'e **4S değerlerinden 3S büyüklüğüne çekilmiştir** (`mevcut.param`:138/:131 = 14,4 / 14 → `emir.param`:138/:131 = **10 / 9**); bu, 3S kararıyla **tutarlı bir değişimdir**, kararın bağımsız kanıtı **değildir** — A3 pil failsafe testi "eşiklerle oynanarak" koşuldu (D-473, `REVIEW_LOG.md`:30882) ve geri alma satırları açıktır (:30885). 🟢 **13 Eylül'de kapandı (kullanıcı BEYANI):** 12 Eylül dökümünde **hatalı** olan `BATT_CAPACITY` (3300 — `emir.param`:129, olması gereken 6000: `PARAMETRE_KILAVUZU_1SAYFA.md`:15) **6000** yazıldı ve `BATT_CRT_VOLT` 9 → **10,5 V** (3S × 3,50 V/hücre) alındı — kılavuzun önerisi 9,9 V idi (:17), kullanıcı daha güvenli tarafı seçti. `BATT_LOW_VOLT = 10` doğrudur, dokunulmadı (:18) | 1 (2. pil öneri) | S | — | — | — | **≈ 460 g — HESAP (VARSAYIMLI)**: 11,1 V × 6,0 Ah = **66,6 Wh** (künyeden) ÷ **140–160 Wh/kg** *varsayılan* LiPo sınıf enerji yoğunluğu → 416–476 g. ⚠ Enerji yoğunluğu **kaynaklandırılmadı**, pil **tartılmadı** (D-439) ve marka/model kayıtlı olmadığı için veri sayfası da okunamadı | Kutuda ve **uçtu** (273 s kümülatif, `emir.param`:980) | **KAYIT YOK** (§Y.2, 13.09.2026) | **KAYIT YOK** (§Y.2, 13.09.2026) |
| A22 | Şarj cihazı | **iMAX B6** (50 W) | 1 | S | — | — | — | — | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A23 | Kablolama demeti | XT60/XT90, JST-GH 6-pin, jumper, silikon kablo | lot | Ü | Kesim + lehim + makaron + etiket | BEYAN GEREKLİ | — | BEYAN GEREKLİ | Kısmen kutuda, kısmen **alınacak** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A24 | Sarf | kablo bağı, ısı makaronu, çift taraflı bant/damper, vida-somun-pul | lot | S | — | — | — | BEYAN GEREKLİ | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A25 | Yedek kamera | USB webcam (UVC) | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A26 | Filament | ABS (X1C + P2S profilleri) | BEYAN GEREKLİ (kg) | S | — | — | — | ölçülen tüketim: **≥ 55,86 g** (yalnız A2 için) | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| A27 | Filament | TPU 95A | BEYAN GEREKLİ (kg) | S | — | — | — | **ÖLÇÜLEMEDİ** | Mevcut | BEYAN GEREKLİ | BEYAN GEREKLİ |
| — | **TOPLAM** | | | | | **≈ 14,0–15,2 sa (HESAP)** — 8 plaka; 495–530 g ÷ ölçülü **37,1 g/sa** (kanıt #9) + kol 3–4 plakasına 0,16 mm katman düzeltmesi ×1,25 | **920,3 g (HESAP)** — 3B basılan **8 plakanın KATI CAD kütlesi** (k = 1,00): ABS 862,79 cm³ × 1,04 + TPU 18,97 cm³ × 1,21. ⚠ **Baskı kütlesi DEĞİLDİR, yalnız üst sınırdır**; %15 dolgulu bir parça katı hacminin ağırlığında olamaz. Gerçek baskı kütlesi **495–530 g**'dır (ölçülü k = 0,500) ve kalkış kütlesine **o** girer | **≈ 2207 g ≈ 2,21 kg (HESAP — tartı YAPILMADI, D-439)** — tüm araç, dökümü aşağıdaki kütle notunda. **KAPI: İHA ≤ 25 kg → GEÇTİ** (%8,8 doluluk; tüm bantların üst ucu alınsa bile ≈ 2,4 kg, sınır 10 kat uzakta) | | **KAYIT YOK** (§Y.2 taraması 13.09.2026: gerçek fiyat/fatura kaydı 0) | **KAYIT YOK** (§Y.2 taraması 13.09.2026) |

⚠ **Satır sayısı düzeltmesi (2026-09-04).** Tablo A'nın gerçek satır sayısı **27**'dir
(A1…A27, atlanan numara yok). Bu raporun önceki sürümünde iki yerde "Tablo A: 26 satır"
yazıyordu; sayım yapıldı ve **27** bulundu (kanıt dizini #21). Düzeltme §7.3.3 ve
"BEYAN GEREKLİ toplu liste"ye işlendi. **26 satır** ifadesi yalnız **Tablo B (DDR BOM)** için
doğrudur ve orada korunmuştur.

⚠ **"Toplam fiyat" sütunu bu sürümde eklendi.** Yönerge Bölüm 7 birim fiyatın yanında **toplam
fiyatı** da açıkça ister; önceki sürümde yalnız birim fiyat sütunu vardı. Sütun eklenmiş, içeriği
**BEYAN GEREKLİ (insan)** bırakılmıştır — çünkü toplam fiyat birim fiyat × adet'tir ve çarpanın
biri yoktur.

⚠ **Kütle: tartı YAPILMADI ve kullanıcı kararıyla PLANLANMIYOR.** 5 Eylül tutanağında tartı satırı
yoktur (D-426, `grep -i tarti` → 0), 12 Eylül atölyesinde de tartılmadı ve kullanıcı 10 Eylül'de
*"tartılara gerek yok, şu an başarıyla hover yapabiliyoruz"* demiştir (`REVIEW_LOG.md` D-439, satır
30425). Bu yüzden kütle sütunu **hesapla** doldurulmuştur — uydurma değil, kaynaklı türetme; her
satırın etiketi ve türetmesi yanındadır ve **zayıf olan satırlar zayıf olduğunu söyler**:

| kütle kalemi | değer | etiket ve türetme |
|---|---|---|
| 3B basılan parçalar (**baskı** kütlesi, 8 plaka) | **≈ 512 g** (495–530 g) | **HESAP** — 3mf katı hacim (ABS 862,79 cm³ · TPU 18,97 cm³) × yoğunluk (1,04 / 1,21) × **ölçülü k = 0,500** (kanıt #9: 55,86 g basılı / 111,66 g CAD); bant yalnız kol 3–4 plakasının 0,16 mm/%40/6 duvar reçetesinden (k = 0,75–1,00). Katı CAD kütlesi **920,3 g**'dir ve **baskı kütlesi değildir** |
| Motor ×4 | **340 g** | **ÜRETİCİ VERİSİ** — 85 g/adet, veri sayfası okundu (`BOLUM_3`:302, http://en.rcsunnysky.com/x-fixedwingseries/53.html) |
| ESC ×4 | **≈ 240 g** | **HESAP (benzetme, DOĞRULANMADI)** — DDR *plan* tablosu 40 A ×2 = 70 g (`ddr_requirements.md`:51) → 35 g/adet; 60 A sınıfı için uygulanan ×1,7 **kaynaksızdır** |
| Pervane 1045 ×4 | **≈ 52 g** | **TAHMİN (kaynak YOK)** — 10 inç naylon pervane sınıfı 12–14 g/adet; ne tartıldı ne veri sayfası okundu |
| Pixhawk 6C 59 · PM06 ≈ 22 · M9N ≈ 32 · FS-iA6B ≈ 10 · telsiz ≈ 35 (uçakta 1 adet) | **≈ 158 g** | **DDR BEYANI / benzetme** — 59 g (`ddr_requirements.md`:35, **aynı ürün**); 22 g Mauch PL-100 satırından (:52, farklı ürün); 32 g M10 satırından (:41, farklı ürün); 10 g TBS Crossfire Nano RX satırından (:42, farklı ürün); 35 g Holybro SiK 433 satırından (:40, farklı ürün — takılı telsiz **RFD900A**) |
| FCHUB-12S (PDB) 60 · UBEC 5 V/5 A 25 | **85 g** | **DDR BEYANI** — PDB (:56) · 12 V 5 A buck (:55, farklı ürün) |
| Jetson Orin Nano Dev Kit (modül + taşıyıcı + soğutucu) | **≈ 180 g** | **DDR BEYANI / benzetme** — DDR'de **Orin NX** + carrier + soğutucu 180 g (:36); takılı kart **Orin Nano Dev Kit**'tir (`results/jetson_20260906/JETSON_KESIF_RAPORU_20260906.md`:41) ve tartılmadı |
| Pil 3S 8000 mAh | **≈ 460 g** | **HESAP (varsayımlı)** — 66,6 Wh ÷ **140–160 Wh/kg**; enerji yoğunluğu kaynaksız, pil tartılmadı |
| Kablolama + sarf | **≈ 180 g** | **DDR BEYANI** (:57, lot 150 g) + %20 sarf payı (**varsayım**) |
| Kamera (A19) | **0 g** | **ÖLÇÜM/BEYAN** — temin edilmedi, araçta yok |
| **TOPLAM kalkış kütlesi** | **≈ 2207 g ≈ 2,21 kg (HESAP)** | on kalemin toplamı; **tartı değildir** |

**KAPI — şartname §6, İHA ≤ 25 kg: GEÇTİ.** 2,21 kg, sınırın **%8,8**'idir; hesaptaki tüm bantların
üst ucu alınsa bile (≈ 2,4 kg) sınır 10 kat uzaktadır — bu hüküm ne tartıya ne de yukarıdaki üç
zayıf satıra (ESC, pervane, kablolama) duyarlıdır.

🔴 **Ama ikinci kapı SINIRDA (yeni bulgu, 13 Eylül).** Hover itki oranı = kütle ÷ (4 × T_max).
`BOLUM_3`:313'teki T_max = 2130 g, **4S 14,8 V + APC1047 (10×4,7)** veri sayfası satırıdır ve aynı
belge bu satırın takılan **10×4,5 için DOĞRULANMADIĞINI** açıkça yazar (:305-306). Pil **3S**'e
alındığı için devir ∝ KV × V ve itki ∝ devir² → T_max(3S) ≈ 2130 × (11,1/14,8)² = **1198 g/motor
(HESAP)**, 4 × 1198 = **4793 g**. Oran = 2207 / 4793 = **%46,0 (HESAP)** — %50 kapısının **hemen
altında**, 4S varsayımıyla hesaplanan %25,9'un neredeyse iki katı. ⚠ Bu **ölçüm değildir** ve iki
zayıf halkası vardır: (a) taban T_max başka bir pervaneye aittir, (b) `MOT_THST_HOVER` kartta hâlâ
**0,35 fabrika değerindedir** (`emir.param`:580 — 6 Eylül dökümünden beri değişmemiş,
`mevcut.param`:580) ve `MOT_HOVER_LEARN = 2` açık olmasına rağmen öğrenme tetiklenmemiştir (:565)
→ **askı itkisi ve itki payı ÖLÇÜLMEDİ** (`config/pixhawk/PARAMETRE_KILAVUZU_1SAYFA.md`:37-40;
D-474 §4). Bu iki parametre kütle hakkında hiçbir şey söylemez; burada yalnız **olumsuz kanıt**
olarak durur. Ölçüm: A12 hover logu (`.bin`, T257) SD karttan çekildiğinde `MOT_THST_HOVER` tek
satırda okunur — 21 Eylül uçuşundan önce.

⚠ **Boyut sütunu.** Şartname §5.4 ağırlık ve boyutu **birlikte** zorunlu kıldığı için sütun
**ÜRETİCİ VERİSİ** atfıyla açılır; ancak 13.09.2026 itibarıyla **hiçbir hücrenin veri sayfası
okunmamıştır** — depoda yalnız SunnySky X2220 için gerçek üretici künyesi ve URL'si vardır
(`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md`:300-302). Bu yüzden kural şudur: **her hücre kendi veri
sayfası URL'si ve okuma tarihiyle yazılır; URL'si yazılamayan hücre BEYAN GEREKLİ kalır, tahmini
gabari yazılmaz.** Toplanacak kalemler: Pixhawk 6C · Holybro M9N · telsiz (**RFD900A**, künye
13 Eylül'de düzeltildi — `HANDOFF_20260913.md`:11) · PM06 *(modül kimliği hâlâ **BEYAN**, A13 açık)*
· Matek FCHUB-12S V2 · SunnySky X2220 *(tek tamam olan)*. **Raspberry Pi HQ + 6 mm lens listeye
girmez** — temin edilmemiştir, uçan araçta yoktur. **AÇIK — sorumlu: kaptan, hedef
`FDR/butce_kaydi.csv`, tarih 20.09.2026** (uçuştan önce). Üretilen parçaların gabarileri
**ölçülmüştür** ve Bölüm 5 §5.1.3'tedir; 3B basılan kalemlerin katı hacimleri de bu bölümde
hesaplanmıştır (kol **67,20 cm³/adet** · üst çerçeve plakası 107,37 · alt çerçeve plakası 140,78 ·
kubbe plakası 119,85 · ayak **52,82/adet** · GPS tutucu **14,67/adet** · TPU ped plakası 18,97).

### 7.1.2 Tablo B — DDR aviyonik BOM'u ve bugünkü durumu

DDR'de beyan edilen aviyonik BOM (**26 satır**; numaralandırma 25'i atladığı için DDR metni 27 der) (toplam **2293 g**) sabit kanat konfigürasyonu
içindir. Aşağıda her satırın FDR'deki karşılığı ve bütçeye etkisinin **yönü** verilmiştir
(tutarlar BEYAN GEREKLİ).

| No | DDR kalemi | Model (DDR) | Adet | Ağırlık (g) | FDR'deki durum | Bütçe etkisinin yönü |
|---|---|---|---|---|---|---|
| 1 | Autopilot | Pixhawk 6C | 1 | 59 | **Değişmedi** (A12) | — |
| 2 | İşlemci | Jetson **Orin NX** + carrier + soğutucu | 1 | 180 | ~~**Jetson Nano 4GB**~~ **Jetson Orin Nano Developer Kit 4 GB** ile değişti (A17; 6 Eylül ölçüm, D-431 — modül **p3767-0004 (4 GB)**, taşıyıcı **p3768**, `results/jetson_20260906/JETSON_KESIF_RAPORU_20260906.md`:41) | **teknik yön: azaltıcı olabilir** — DDR'de **üç ayrı kalem** planlanmıştı (modül + taşıyıcı + soğutucu), gerçekleşen **tek geliştirme kitidir** ve Orin NX, Orin Nano 4 GB'ın bir üst ürün sınıfıdır. ⚠ **Parasal yön BEYAN GEREKLİ** — Orin Nano tutarı depoda yok (§Y.2, 13.09.2026); fiyatsız bir kalem sayısı karşılaştırması parasal yön üretmez. Teknik bedeli §7.5.2'de |
| 3 | Kamera | **Arducam** IMX477 12MP | 1 | 50 | **RPi HQ** (aynı sensör) (A19) | nötr/azaltıcı |
| 4 | Pitot tüpü | Pitot + hortum | 1 | 10 | FDA aracında **yok**; finalde kalır | ertelendi |
| 5 | Airspeed | Holybro MS5525DSO | 1 | 20 | FDA aracında **yok**; finalde kalır | ertelendi |
| 6 | Telemetri (uçak) | Holybro SiK 433 | 1 | 35 | **Değişmedi** (A16) | — |
| 7 | GNSS | Holybro **M10** + pusula | 1 | 32 | **M9N** ile değişti (A14) | azaltıcı |
| 8 | RC alıcı | **TBS Crossfire** Nano RX | 1 | 10 | **FlySky FS-i6 / FS-iA6B (iBUS)** (A15) | **azaltıcı** |
| 9 | Motor | SunnySky X2216 1100KV | 2 | 138 | FDA aracında ~~**5008 340KV ×4**~~ → **SunnySky X2220 980KV V3 ×4** (A8; (7 Eylül beyanı, D-435)) | ~~**artırıcı** (4 adet, daha büyük)~~ → 4 adet; X2220 küçük sınıf motor (85 g, veri sayfası), yön **BEYAN GEREKLİ** (5008 iadesi + X2220 tutarı) |
| 10 | Servo (kanat/kuyruk) | EMAX ES08MA II | 4 | 48 | FDA aracında **yok**; finalde kalır | ertelendi |
| 11 | Pil | 4S 14–15 Ah Li-ion | 1 | 1000 | ~~4S 10 Ah 25C LiPo~~ → **3S 8000 mAh** (A21; kullanıcı kararı, gerekçe stabilite, 12 Eylül). Kart eşikleri 3S büyüklüğüne çekildi: `BATT_LOW_VOLT = 10` · `BATT_LOW_VOLT` 10 → **10,5**, `BATT_CRT_VOLT` **9** (13 Eyl, D-481) (`emir.param`:138/:131 + 13 Eylül kullanıcı beyanı) | **enerji yönü azaltıcı (HESAP)** — 214,6 Wh (4S 14,8 V × 14,5 Ah) → **88,8 Wh**; kütle 1000 g → **≈ 460 g (HESAP, varsayımlı)**. ⚠ **Parasal yön BEYAN GEREKLİ** — depoda fiyat kaydı yok (§Y.2) |
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
| D6 | **Yedek pervane seti (~~12×10~~ → 10×4,5 / 1045, CW+CCW — 7 Eylül beyanı, D-435)** | zorunlu | ilk uçuşlarda en sık kırılan parça | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D7 | Küçük ekran + klavye + ethernet kablosu | zorunlu | Nano ilk açılış | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D8 | Multimetre, tartı, baret/yelek | zorunlu | kablolama kontrolü, **UHDR kütle ölçümü**, saha emniyeti | BEYAN GEREKLİ | BEYAN GEREKLİ |
| D9 | 2. pil ~~4S 10 Ah~~ 3S 8000 mAh + ≥ 150 W şarj | öneri | tek pil günde 2 uçuşa kilitliyor; prova sayısını ikiye katlar | BEYAN GEREKLİ | BEYAN GEREKLİ |
| ~~D10~~ | ~~JetPack 4.6 / Py3.8 **GPU torch** tekerleği (indirme)~~ → gereksiz: kart Orin Nano (JetPack 7.2.1), GPU torch 2.11.0+cu130 kartta kuruldu, FPS kapısı GEÇTİ (D-431) | — | 6 Eylül düzeltmesi | 0 (indirme gerekmedi) | 0 |
| ~~D11~~ | ~~JetPack 4.6.x SD imajı (indirme)~~ → gereksiz: kart JetPack 7.2.1 kurulu, NVMe kök ile geldi (D-431) | — | 6 Eylül düzeltmesi | 0 (indirme gerekmedi) | 0 |
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
| 2 | Görev bilgisayarı | Jetson Orin NX + carrier | BEYAN GEREKLİ | Jetson Orin Nano Developer Kit 4 GB (A17; D-431) | BEYAN GEREKLİ | HESAPLANAMAZ | BEYAN GEREKLİ (yön) | S2 |
| 3 | Kamera | Arducam IMX477 | BEYAN GEREKLİ | RPi HQ IMX477 (A19) | BEYAN GEREKLİ | HESAPLANAMAZ | nötr/azaltıcı | S2 |
| 4 | Pitot tüpü | Pitot + hortum | BEYAN GEREKLİ | alınmadı — ertelendi (E7) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 5 | Airspeed | Holybro MS5525DSO | BEYAN GEREKLİ | alınmadı — ertelendi (E7) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 6 | Telemetri (uçak) | Holybro SiK 433 | BEYAN GEREKLİ | SiK 433 (A16) | BEYAN GEREKLİ | HESAPLANAMAZ | değişmedi | — |
| 7 | GNSS | Holybro M10 + pusula | BEYAN GEREKLİ | Holybro M9N (A14) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 8 | RC alıcı | TBS Crossfire Nano RX | BEYAN GEREKLİ | FlySky FS-i6 + FS-iA6B (A15) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S2 |
| 9 | Motor | SunnySky X2216 ×2 | BEYAN GEREKLİ | ~~5008 340KV ×4~~ → SunnySky X2220 980KV V3 ×4 (A8; (7 Eylül beyanı, D-435); 5008 iadesi BEYAN GEREKLİ) | BEYAN GEREKLİ | HESAPLANAMAZ | ~~artırıcı~~ → yön BEYAN GEREKLİ | S1 |
| 10 | Servo (kanat/kuyruk) | EMAX ES08MA II ×4 | BEYAN GEREKLİ | alınmadı — ertelendi (E8) | 0 (harcanmadı) | HESAPLANAMAZ | ertelendi | S1 |
| 11 | Pil | 4S 14–15 Ah Li-ion | BEYAN GEREKLİ | ~~4S 10 Ah 25C LiPo~~ 3S 8000 mAh (A21) | BEYAN GEREKLİ | HESAPLANAMAZ | azaltıcı | S1/S2 |
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
| A9 | Pervane ~~12×10~~ → 10×4,5 (1045) ×4 + yedek set (7 Eylül beyanı, D-435) | yok (DDR'de itki grubu farklı) | 0 (planlanmadı) | kutuda; yedek set alınacak (D6) | BEYAN GEREKLİ | artırıcı | S1 |
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
| ~~**FPS < 0,61** (Nano CPU'da YOLOv8m)~~ → **6 Eylül ÖLÇÜLDÜ, GEÇTİ (D-431):** kart zaten Orin Nano Developer Kit 4 GB; GPU ile pt **1,35/1,06** · engine **1,58/1,33** FPS ≥ 0,61 | Gerçek zamanlı tespit tazelik penceresine sığmaz | (a) ONNX Runtime bu kartta GPU'da **çalışmadı** (sm_87 çekirdeği yok); (b) daha güçlü kart **gerekmedi** — satın alma yok | ~~yüksek~~ **kapandı** (6 Eylül) |
| **CSI kamera yolu açılmaz** | Görüntü hiç gelmez | **USB webcam** (D4, zaten listede) | orta — ucuz sigorta |
| **Tek pil / 3 saat şarj** | Uçuş günü 2 uçuşla sınırlı; prova sayısı yetmez | **2. pil ~~4S 10 Ah~~ 3S 8000 mAh + ≥ 150 W şarj** (D9) | orta |
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
| S1 | **Araç sınıfı farkı** — FDA'nın §5.3.2 çoklu rotor şartı DDR'de yoktu | 4× ~~5008~~ → SunnySky X2220 980KV V3 (7 Eylül beyanı, D-435) motor + 4× ESC (plan 80 A; 5 Eylül kutudan "60 A V2", D-426 §3) + quad gövde eklendi; kanat servoları, pitot, airspeed, paraşüt zinciri ertelendi | net etki **BEYAN GEREKLİ** | yeni bir araç montaj/kalibrasyon hattı |
| S2 | **Tedarik zorunluluğu** — planlanan parça yerine bulunabilen parça | Orin NX → ~~Nano 4GB~~ **Orin Nano Developer Kit 4 GB** (3 Eylül beyanı 6 Eylül'de kartla yanlışlandı — D-431); M10 → M9N; TBS Crossfire → FlySky; Mauch → FCHUB+PM06 (plan PM02; 5 Eylül kutudan PM06 — D-426 §3) | yön **BEYAN GEREKLİ** (Jetson tutarı yok) | ~~Nano'da `ultralytics` için ayrı Python 3.8 yığını; **TensorRT `.engine` ölçülemez**; FPS kapısı riske girdi~~ → 6 Eylül: Python 3.12 + GPU torch, `.engine` derlendi (denklik D-303 DÜŞTÜ → uçuş `.pt`), FPS kapısı **GEÇTİ** |
| S3 | **Üretim kararı revizyonu** | Ayak/GPS tutucu **PLA → ABS**; **TPU taban pedi** eklendi; kol 3–4 daha ağır reçeteyle basıldı | küçük artırıcı | ısı dayanımı ↑, baskı süresi ↑ |

### 7.5.2 En pahalı sapma parasal değil: Orin NX → Nano 4GB

Bu satır bütçeyi **düşüren** ama teknik riski **artıran** tek kalemdir ve raporda böyle yazılır:

- Kazanç: kart maliyeti belirgin biçimde düşer (tutar BEYAN GEREKLİ).
- Bedel 1: JetPack 4.6'nın sistem Python'u 3.6 → ayrı `venv38` + **çevrimdışı 14 paket / 51 dosya / 246 MB** tekerlek zinciri kurulmak zorunda kalındı.
- Bedel 2: `venv38` içinde `tensorrt` yok → **`.engine` ÖLÇÜLEMEDİ**, uçuş PT/ONNX ile yapılacak.
- Bedel 3: üretim modeli **YOLOv8m-seg**'dir; Nano CPU'da **0,61 FPS** kapısı düşebilir. Ölçülmedi, tahmin edilmedi.
- Karşı önlem maliyeti: yedek USB webcam, GPU tekerleği araştırması, ikinci pil önerisi (D9/D10).

⚠ **6 Eylül düzeltmesi (D-431):** yukarıdaki üç bedel **3 Eylül beyanına** (Nano 4GB) göre yazılmıştı. Kart açıldığında **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12) çıktı: Bedel 1 (venv38 + cp38 tekerlek zinciri) **kullanılmadı**; Bedel 2 — `.engine` **derlendi ve ölçüldü** (denklik D-303 oransal 3/126 DÜŞTÜ → uçuş `.pt`); Bedel 3 — FPS kapısı GPU ile **GEÇTİ** (pt 1,35/1,06 · engine 1,58/1,33 ≥ 0,61). D10/D11 indirmeleri gereksizleşti. Başlıktaki "Orin NX → Nano 4GB" sapması gerçekte **Orin NX → Orin Nano 4 GB**'tır; parasal yön BEYAN GEREKLİ (tutar yok). Kanıt `results/jetson_20260906/` (`ORTAM_KUNYESI.txt`, `jetson_fps_20260906_orin_nano/ozet.json`, `jetson_log_20260906/engine_karar_denkligi.json`).

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
| 18 | ~~`.engine` Nano'da derlenemiyor~~ **GEÇERSİZ (D-431):** Orin Nano'da `.engine` **derlendi** (TensorRT 10.16.2, 57 283 989 B) ama engine↔pt D-303 oransal denkliği 3/126 **düştü** → uçuş `.pt`; teknik bedel "derlenemez" değil "denklik düştü" | `jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §4, §8 | — (belge, testle kilitli) | 2026-09-06 |
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
