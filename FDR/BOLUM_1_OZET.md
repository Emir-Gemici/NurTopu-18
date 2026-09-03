# BÖLÜM 1 — ÖZET (5 puan)

> **NAVITAS** · TEKNOFEST İleri Otonom Sistemler Tasarım ve Operasyon Yarışması
> Şartname §5.3.1, Tablo 4 — Bölüm 1. Bu bölüm raporun tamamının özetidir;
> içindeki her sayı Bölüm 3–7'de kaynağıyla birlikte tekrar geçer.

---

## 1.1 Sistem ne yapar

NAVITAS, afet sahasını simüle eden bir alanda **hangi güzergâhın açık olduğunu
havadan bulan** ve bu kararı **hakemin canlı doğrulayabileceği biçimde** yere
aktaran bir otonom sistemdir. Sistem üç birimden oluşur: hava aracı (İHA), yer
kontrol istasyonu (YKS) ve kara aracı (İKA).

Karar zincirinin tamamı hava aracının üstündeki görev bilgisayarında koşar:
kamera karesi → segmentasyon çıkarımı → geçilebilir/engel maskeleri → uçuş
kontrolcüsünden gelen **canlı irtifayla** türetilen ölçek (metre/piksel) →
serbest alanın en büyük bağlı bileşeni üzerinde A* tanık yolu → şerit kararı →
telsizle yayın. Yayın **her karede tam bir mesajdır**: ya `OPEN_ROUTE` ya
`NO_ROUTE`. Sessizlik yoktur; sessizlik hakem ekranında "belki" anlamına gelirdi.

Mimarinin değişmez kuralı şudur: **serbest alan otoritedir, nesne katmanı
yalnızca çıkarır.** Hiçbir işlem serbest alanı büyütemez. Bunun pratik sonucu,
sistemin her belirsizlikte **fail-closed** davranmasıdır: ölçek türetilemezse,
zemin maskesi şüpheliyse, koridor dar ya da güven eşiğinin altındaysa, karar
`NO_ROUTE`'a düşer ve ret **sebebiyle birlikte** hakem ekranına yazılır. Şartname
§5.3.2 yanlış güzergâh tespitine **0 puan** verdiği için bu asimetri bilinçlidir:
söylememek, yanlış söylemekten iyidir.

## 1.2 Görevi nasıl icra eder

**Hava tarafı.** İHA otonom uçuşta hedef tespit alanının üstüne gelir, asgari 30
metre irtifada (görev planında 32 m, 2 m barometre payı) tek pas tarama yapar.
Her karede karar üretilir; kararlar **histerezisten** geçer — farklı bir şerit
ancak arka arkaya K karede teyit edilirse yayına girer, ama `NO_ROUTE` **asla**
geciktirilmez. Karar ACK'li olarak YKS'ye ve İKA'ya gider; ayrı bir iş
parçacığından saniyede bir HEARTBEAT akar ve bu heartbeat son **algı kararının
yaşını** (`karar_yas`) taşır.

**Yer tarafı.** Hakem, YKS ekranında rotayı, güven değerini, model künyesini ve
tespitin tazelik damgasını görür. Onay **iki aşamalıdır**: birinci aşama tespitin
görüldüğünü, ikinci aşama güzergâhın İKA'ya ulaştığını teyit eder ve ACK ancak
ikinci aşamada gönderilir. Bayat bir tespit "canlı" gösterilemez; tazelik
penceresi sözleşmede 5 saniyedir.

**Kara tarafı.** İKA'nın hareketi üç koşula birden bağlıdır ve bu kilit koddadır:
`geçerli OPEN_ROUTE ∧ İHA inişi tamamlandı ∧ YKS'den IKA_GO geldi`. İniş sinyali
insan beyanı değil **uçuş kontrolcüsü kanıtıdır** (`EXTENDED_SYS_STATE.landed_state
== ON_GROUND` ve `relative_alt < 1 m`, aynı sysid, ardışık üç çift). Yer
istasyonundaki "İHA İNDİ" düğmesi bu kilidi **açamaz**.

Şartname iki ayrı doğrulama ister ve bu rapor ikisini karıştırmaz: **21 Eylül'deki
görev test uçuşu (§5.3.2) çoklu rotorlu bir drone ile**, İKA olmadan, YKS'ye
aktarım ve hakem onayı ekseninde yapılır; **finalin yarışma görevi (§2.2)** sabit
kanat + mancınık + paraşüt + İKA ile icra edilir. Algı, karar, haberleşme ve yer
istasyonu katmanı **iki araçta da aynı koddur**; yer istasyonu farkı `--fda`
bayrağıyla tanır.

## 1.3 Ölçülmüş başlıca sonuçlar

| ne | ölçülen | çerçeve |
|---|---|---|
| Genel kapı (`test_rota_sentetik.py`) — iki kol | **15/15** tanısal · **15/15** üretim rotası · **15/15** yayınlanan şerit | 15 belirlenimci arena sahnesi, 3 Eylül 2026 |
| Tam test süiti | **1896 test OK** (3 atlandı, 390,5 s) | 3 Eylül 2026 |
| Kabul kapıları K0–K6 (sentetik arena, n=260, **terfi anı 26 Ağustos**) | **7/7 GEÇTİ** — rota üretilen kare 255/260, bariyer kesişimi 0, yanlış güzergâh 2,75 | sentetik |
| Kabul kapıları **K0–K8 + K5A**, üretim kipinde (n=260, **1 Eylül**) | **10/10 GEÇTİ** — K1 256/260, K2 6/256, K3 0/256, K4 2/256, K5/K5A 0 px, K6 2/256, K7 84/85 | sentetik |
| K7 yayınlanan şerit doğruluğu | **84/85 (%98,8)** | üretim kipinde kabul koşusu |
| Uçtan uca kare gecikmesi | **p95 0,113 s** (33 ölçülen gerçek kare (+3 ısınma), üretim zinciri + gerçek yayıncı + ACK) | UDP loopback |
| Gereken kare hızı (türetildi, tahmin edilmedi) | `1/(5·p)` → sentetik **0,20 FPS** · gerçek sızıntısız **0,58 FPS** · en kötü uçuş **0,61 FPS** | iki ayrı çerçeve |
| Saha zinciri kuru koşusu (10 halka) | GEÇTİ 9 · DÜŞTÜ 0 · **SAHİPSİZ 1** (motor) · çıkış kodu 1 | 2 Eylül 2026 |
| Kanıt defteri | **420 kayıt** (`REVIEW_LOG.md`), çürütülmüş kendi iddialarımız dâhil | — |

Gecikme sayısının hikâyesi, sayının kendisinden önemlidir: ilk ölçümde toplam p95
**0,458 s** çıkmıştı ve baskın kalem "telsiz + ACK ≈ 308 ms" görünüyordu. Bağımsız
bir çürütücü, bu 308 ms'nin bir ölçüm değil bir **soket zaman aşımı sabitinin**
yansıması olduğunu buldu; düzeltmeden sonra telsiz payı ~2 ms'ye, toplam p95
**0,113 s**'ye indi. Yanlış sayı silinmedi, üstü çizilip düzeltmesine işaret
verildi. Bu rapordaki sayıların güvenilirliği, bu tür düzeltmelerin **kayıtta
durmasından** gelir.

**Geçmeyen kapılar da yazılır.** Üretim modeli `navitas-seg-v36-512`, gerçek uçuş
karelerindeki iki **ön kayıtlı eşiği geçmeden** terfi etmiştir: ROTA ≥ 10
istenirken 8, MASKE_YOK ≤ 10 istenirken 16 ölçülmüştür. Terfi bu eşikler
gevşetilerek değil, **insan kararıyla** ve gerekçesi yazılarak yapıldı (gerçek
karede yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3; bedeli sentetik
arenada K3 0→1, K4 1→4, K6 5→7). Eşikler **değiştirilmedi** ve sonraki terfileri
bağlamaya devam ediyor; önceki model v35 silinmedi, yedek olarak tam özetiyle
defterde duruyor.

## 1.4 Bilinen en büyük sınır

**Elimizde gerçek arena karesi yoktur.** K0–K7 kabul kapılarının tamamı sentetik
arena kümesi üzerinde ölçülmüştür (T66 ada kadrajı, n=260). Elimizdeki gerçek
doğrulama verisi kırsal bir DJİ çekimidir ve kırmızı H, moloz yığını ya da bariyer
**içermez**. Bu yüzden bu raporda hiçbir sentetik ölçüm "saha başarımı" diye
sunulmaz; saha `p` değeri **ÖLÇÜLEMEDİ** olarak durur ve iki çerçevenin (sentetik
0,98 / gerçek OOD 0,35) arası **tahmin edilmez**.

Bu sınırın en somut yüzü şudur: gerçek uçuş kayıtlarında modelin **51 saniye
boyunca hiç karar üretemediği**, sahne bağıntılı kör aralıklar ölçülmüştür (bir
uçuşta 51 ardışık kare, 46'sı `MASKE_YOK`; ikinci blok 45 kare). Tazelik penceresi
5 saniyedir — aralık pencereyi on kat aşmaktadır. Bu **bir hız sorunu değildir**:
gereken kare hızı 0,61, beklenen band 0,9–2,6'dır; 51 saniyelik bir blokta daha
hızlı örneklemek aynı köre daha çok bakmaktır. Kalan iş model tarafındadır ve
açık olarak kayıtlıdır. Sistemin bu duruma karşı savunması dürüstlüktür: heartbeat
`karar_yas` alanını taşır, hat canlılığı algı canlılığı sayılmaz, ve hakem ekranda
tespitin **kaç saniye önce** üretildiğini görür.

İkinci büyük sınır **gerçek İKA motor sürücüsünün olmamasıdır**. Sürücü arayüzü,
kabul harnessı ve fail-closed davranış hazırdır; `GercekSurucu` arka uçsuz
kurulmayı **reddeder** (sessiz iskelet yasaktır). Kuru koşu bu halkayı `SAHİPSİZ`
olarak raporlar ve çıkış kodu 1 verir. Bu bir donanım kararıdır, final dalgasının
işidir ve görev test uçuşunu etkilemez (o uçuşta İKA yoktur).

Üçüncüsü: **gerçek SiK 433 MHz hattı hiç ölçülmemiştir.** Bugüne kadarki tüm
aktarım kanıtı UDP loopback üzerindedir. Detay tasarım raporundaki ">%98 teslim,
300 m" iddiasının bugün kanıtı yoktur; ölçüm aracı yazılmış ve gerçek bayt
akışında sınanmıştır, ama iki telsiz henüz kutudan çıkmamıştır.

## 1.5 Görev test uçuşu hazırlığı (prova 21 Eylül · resmî uçuş 30 Eylül – 3 Ekim)

Uçuş **Adıyaman drone test alanında**, 3B baskı gövdeli bir quadcopter ile
yapılacaktır: Pixhawk 6C + PM02, Holybro M9N, 5008 340KV ×4 motor / 12×10 pervane,
80 A ESC, FCHUB-12S V2 güç dağıtımı, FlySky FS-i6 (iBUS), 2× SiK 433 MHz telemetri,
görev bilgisayarı **Jetson Nano 4GB** (JetPack 4.6), kamera **Raspberry Pi HQ
(IMX477, CSI)**, 4S 10 Ah pil.

Yazılım tarafında uçuşa hazırlık **tamamlanmıştır**: ArduCopter parametre şablonu
(31 parametre, her satırda gerekçe) ve QGC görev planı (TAKEOFF 32 m → 20×20 m
üzerinde tek pas → LOITER 60 s → LAND) repoda ve testle kilitlidir; kötü-durum
süre bütçesi **221,5 s ≤ 600 s** hesaplanmıştır. Yer istasyonunun `--fda` kipi,
görev test uçuşunda hakem onayını **imkânsız kılacak** bir kilidi (İKA aktarım kanıtı
şartı) kaldırır ve İKA'ya ait düğmeleri fail-closed kapatır. Jetson Nano yığını
çevrimdışı kurulabilecek biçimde hazırlanmıştır (14/14 paket aarch64/cp38 tekerlek,
246 MB). Seri port çakışması — Pixhawk'ı üç ayrı sürecin açmaya çalışması — hem
MAVLink hem NAVITAS protokolü için çoğullayıcıya bağlanmış ve kapıya alınmıştır.

Kalan işler **donanım ve insan** işleridir ve takvimlidir: 5 Eylül montaj ve
kablolama günü (kutu ilk kez açılacak), 6 Eylül ilk hover, 7–16 Eylül uçuş
provaları ve tam prova ×3, 17 Eylül **sürüm dondurma** (bundan sonra kod
değişmez), 18 Eylül "kesin hazır" tutanağı. Kamera gerçek görüş açısı, Nano'da
kare hızı ve gerçek telsiz gidiş-dönüş süresi **o günlerde ilk kez ölçülecektir**;
bu rapor onları bugün ölçülmüş gibi göstermez.

## 1.6 Bu raporun okuma sözleşmesi

Bu rapor dört kurala uyar ve bu kurallar rapor için icat edilmemiştir; projenin
420 kayıtlık ölçüm defterinden gelir:

1. **Her sayı bir artefakttan gelir.** Her bölümün sonundaki *Kanıt dizini*, geçen her sayının dosya yolunu, onu üreten betiği ve ölçüm tarihini verir.
2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Koşulmamış kapı "sorun çıkmadı" diye yazılmaz; paydası olmayan oran rapora girmez.
3. **Geçmeyen kapı geçmedi diye yazılır** — v36'nın iki eşiği ve histerezisin özgün H1 eşiği bu raporda açıkça geçmemiş olarak durur.
4. **Sentetik ölçüm saha başarımı diye sunulmaz.**

Bölüm 6, şartnamenin yazılıma düşen **45 hükmünü** tek tek izler ve kapanmamış
**12 gereksinimi** tarihleriyle birlikte ayrı bir tabloda toplar. Bu raporun en
güçlü iddiası bir yüzde değil, o tablonun **var olmasıdır**.

---

## Kanıt dizini

| sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|
| Genel kapı **15/15 · 15/15 · 15/15**, RC=0 | konsol çıktısı (bu bölümün yazımı sırasında koşuldu) | `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py` | **2026-09-03** |
| Tam süit **1896 test OK (skipped=3)**, 390,534 s | `results/faz_b_oncesi/cuma_kontrol/tam_suit.txt` | `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q` | **2026-09-03** |
| **155** test dosyası (`tests/*.py`) | `tests/` | `ls tests/*.py \| wc -l` | 2026-09-03 |
| Kanıt defteri **420 kayıt** (`### D-` başlığı; 414 ayrık numara) | `REVIEW_LOG.md` | `grep -o "^### D-[0-9]*" REVIEW_LOG.md \| wc -l` | 2026-09-03 |
| K0–K6 kabul kapıları **7/7** (K0…K6 yedi kapıdır; artefaktta `gecti` yedi anahtar taşır); K1 **255/260**, K5 **0**, K6 **2,75** (n=260) | `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json` → `results/fdr/GORUNTU_ISLEME_KANIT.md` §2 | `scripts/olcum/65_kabul_denetcisi.py`; belge üreteci `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-08-26 (belge 2026-09-01) |
| K7 yayınlanan şerit doğruluğu **84/85 (%98,8)** | `REVIEW_LOG.md` D-386 (kabul koşusu 65, üretim kipi) | `scripts/olcum/65_kabul_denetcisi.py` | 2026-09-01 |
| Uçtan uca kare gecikmesi **p95 0,113 s**; düzeltme öncesi 0,458 s ve "308 ms" soket sabiti | `results/fda_butce/olcum_20260901.json` · ön kayıt `results/fda_butce/ON_KAYIT.md` | `scripts/olcum/169_fda_butce_olcumu.py`; düzeltme kaydı D-383 | 2026-09-01 |
| Gereken FPS `1/(5·p)`: sentetik **0,203** · gerçek sızıntısız **0,579** · en kötü uçuş **0,61** | `results/b4_fps/p_ve_kosu_20260901.json` · ön kayıt `results/b4_fps/ON_KAYIT.md` | `scripts/olcum/163_b4_p_ve_kosu.py`; sızıntı düzeltmesi D-376 | 2026-09-01 |
| **51 saniyelik** kör aralık (51 kare, 46'sı `MASKE_YOK`; ikinci blok 45 kare) | `results/b4_fps/p_ve_kosu_20260901.json` | `scripts/olcum/163_b4_p_ve_kosu.py` (D-374 §2) | 2026-09-01 |
| Kuru koşu **GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor)**, çıkış kodu 1 | `results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json` | `scripts/saha_kuru_kosu.py` | **2026-09-02 23:59:54** |
| Üretim modeli `navitas-seg-v36-512`, imgsz 512, SHA `1d1caca6…6911` | `config/model_registry.json` · `profiles.competition` | `codes/model_registry.py` (fail-closed doğrulama) | terfi 2026-08-26 |
| v36 geçilmeyen eşikler: ROTA ≥ 10 → **8**; MASKE_YOK ≤ 10 → **16**; kazanç 15/21→7/38 ve 79→3; bedel K3 0→1, K4 1→4, K6 5→7 | `config/model_registry.json` · `_surum_karari` | `scripts/olcum/65_kabul_denetcisi.py`; karar dayanağı D-293/D-294 | 2026-08-26 |
| Histerezis: ham çevrilme 13→7 ve 24→11; bastırılan NO_ROUTE 0; **`H1_ozgun = false`** | `results/p5_histerezis/olcum_20260903.json` · ön kayıt `results/p5_histerezis/ON_KAYIT.md` | P5 histerezis ölçümü (D-396) | **2026-09-03** |
| Tazelik penceresi **5,0 s**; asgari irtifa **30 m**; FDA operasyon süresi **600 s**; İHA-UB kenarı **300 m** | `codes/karar_sozlesmesi.py` (`YKS_TESPIT_TAZELIK_S`, `SARTNAME_ASGARI_IRTIFA_M`, `SARTNAME_FDA_OPERASYON_SURESI_S`, `SARTNAME_IHA_UB_KENAR_M`) | `grep -n "SARTNAME_" codes/karar_sozlesmesi.py` | 2026-09-03 |
| Görev planı: TAKEOFF **32 m**, LOITER **60 s**, kötü-durum bütçe **221,5 s ≤ 600 s**; **31** parametre | `config/pixhawk/fda_gorev.waypoints` · `config/pixhawk/arducopter_fda.param` · `config/pixhawk/README.md` | `tests/test_faz_b_pixhawk_sablon.py` (12 test) | 2026-09-03 |
| Jetson Nano yığını **14/14** aarch64/cp38 tekerlek, 51 dosya, **246 MB** | `wheels/INDIRME_RAPORU.txt` | `scripts/nano_tekerlek_indir.py`; `tests/test_faz_b_nano_kurulum.py` (20 test) | 2026-09-03 |
| Donanım künyesi (quadcopter, Pixhawk 6C, Jetson Nano 4GB, RPi HQ, 4S 10 Ah, 2× SiK) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | kullanıcı beyanı; **5 Eylül'de kutu açılarak teyit edilecek** | 2026-09-03 (beyan) |
| Takvim (5 Eylül montaj → 17 Eylül sürüm dondurma → **21 Eylül FDR teslimi + Adıyaman provası** → 30 Eylül–3 Ekim görev test uçuşu) | `SAHA_HAZIRLIK_PLANI_20260903.md` §4 | — | 2026-09-03 |
| Şartname alıntıları (§2.2, §5.3.1 Tablo 4, §5.3.2, §6.2, §6.4, §7) | `results/sartname_bosluk/sartname_metin.txt` (PDF 30 sayfa) | PyMuPDF metin çıkarımı | 2026-08-26 |
| **45** izlenen gereksinim satırı, **12** açık gereksinim | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` §6.6, §6.9 | bu raporun Bölüm 6'sı | 2026-09-03 |

### BEYAN GEREKLİ (insan)

- **BEYAN GEREKLİ (insan):** Takım adı, takım numarası, kategori ve üniversite/kurum künyesi — bu bölümün başına eklenecek.
- **BEYAN GEREKLİ (insan):** Gerçek kütleler (İHA, İKA, yük) — 5 Eylül tartı listesi.
- **BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen kare hızı ve `torch.cuda.is_available()` sonucu.
- **BEYAN GEREKLİ (insan):** RPi HQ kamera gerçek yatay görüş açısı (`kamera_dogrula` ölçümü); rapordaki 55–63° aralığı lens beyanından türetilmiş **tahmindir**.
- **BEYAN GEREKLİ (insan):** Gerçek SiK 433 MHz hattında gidiş-dönüş süresi ve paket kayıp oranı.
- **DOĞRULANACAK:** Bu özetin sayıları rapor teslim edilmeden önce, teslim günündeki kapı koşusuyla **yeniden üretilmelidir**; bayat sayı taşımak bu projede birden çok kez kusur olarak kayda geçti.
