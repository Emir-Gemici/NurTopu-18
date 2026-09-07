# BÖLÜM 1 — ÖZET (5 puan)

> **NAVITAS** · TEKNOFEST 2026 İleri Otonom Sistemler Tasarım ve Operasyon Yarışması
> Yönerge dayanağı: *"Bölüm 1. Özet (5 PUAN)"* — `results/fdr_sablon/fdr_yonerge_metin.txt`
> (FDR Hazırlama Yönergesi, 19 sayfa) · şartname §5.3.1, Tablo 4 — Bölüm 1.
> Bu bölüm raporun tamamının özetidir; içindeki her sayı Bölüm 3–7'de kaynağıyla
> birlikte tekrar geçer.

⚠ **ÜRETİM SIRASI UYARISI — BU BÖLÜM HENÜZ NİHAİ DEĞİLDİR.**
Özet, tanımı gereği kendisinden sonraki bölümlerin türevidir. Bölüm 2–7
kesinleşmeden yazılan bir özet, o bölümler değiştiğinde **sessizce bayatlar** ve
rapor kendi "her sayı bir artefakttan gelir" kuralını ihlal eder. Bu bölüm,
**Bölüm 2, 3, 4, 5, 6 ve 7 kesinleştikten SONRA yeniden üretilecektir**; aşağıdaki
hâli o bölümlerin 3–4 Eylül 2026 tarihli durumunun özetidir. Yeniden üretim
yapılmadan bu bölüm tamamlanmış sayılmaz.

⚠ **İKİ AYRI ARAÇ VARDIR; bu özet ikisini karıştırmaz.**
**(a) FDA görev test uçuşu aracı** — çoklu rotorlu (quadcopter), 3B baskı gövde;
paraşüt, mancınık ve İKA **yoktur** (şartname §5.3.2). 30 Eylül – 3 Ekim'de uçacak
olan budur; provası 21 Eylül Adıyaman.
**(b) Yarışma final aracı** — sabit kanat + mancınık + paraşüt + İKA (şartname §2.2).
**HENÜZ ÜRETİLMEMİŞTİR.** Yönergenin 3.1 (uçuş bilimleri) ve 3.2.3 (mancınık)
başlıkları bu araca aittir.
Sözleşme dayanağı: `CONTRACTS.md` §6.7 (`--fda` görev kipi, D-407).

---

## Yönerge madde haritası — bu bölümün iskeleti

Aşağıdaki on alt başlık yönergenin Bölüm 1 paragrafından **birebir** türetilmiştir
(kimlikler `FDR/YONERGE_HARITASI.md` §1'den).

| kimlik | yönergenin istediği | bu bölümde |
|---|---|---|
| `Y-1-M01` | Projenin teknik hatlarını ve operasyonel kabiliyetini tanımlayan sistematik ve bütüncül özet | §Y-1-M01 |
| `Y-1-M02` | İHA, İKA ve Mancınık sistemlerinin final tasarım faaliyetleri ve özgün sistem mimarileri | §Y-1-M02 |
| `Y-1-M03` | ÖDR/DDR gereksinimlerinin ve tasarım kriterlerinin nihai tasarım üzerinde doğrulandığı | §Y-1-M03 |
| `Y-1-M04` | Gerçekleştirilen revizyonların tamamlandığı | §Y-1-M04 |
| `Y-1-M05` | Sistemin görev tanımını karşılayacak olgunluğa ulaştığı | §Y-1-M05 |
| `Y-1-M06` | Nihai mekanik, aviyonik ve yazılım mimarileri; alt sistem konfigürasyonları; fiziksel ve fonksiyonel etkileşimler | §Y-1-M06 |
| `Y-1-M07` | Üretim yöntemleri, malzemeler, montaj süreçleri, saha kurulum prosedürleri | §Y-1-M07 |
| `Y-1-M08` | Teknik riskler, önleyici tedbirler, risk azaltma stratejileri ve acil durum senaryoları | §Y-1-M08 |
| `Y-1-M09` | Operasyon planı, görev akışı, ekip organizasyonu, görev dağılımı ve kurulum süreçleri | §Y-1-M09 |
| `Y-1-M10` | Görev gereksinimlerini karşılama düzeyi analizi, tasarım doğrulama süreci özeti, teknik olgunluk kanıtı | §Y-1-M10 |

---

### Y-1-M01 — Projenin teknik hatlarını ve operasyonel kabiliyetini tanımlayan sistematik ve bütüncül özet

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

**Operasyonel kabiliyet — bugün kanıtlı olan.** Uçtan uca zincir (kamera → çıkarım →
maske → ölçek → hedef konumu → rota → aktarım → sürüş izni) yerde bütünleşik
koşturulmuş ve on halkanın dokuzu **GEÇTİ**, biri (motor) **SAHİPSİZ** raporlanmıştır;
kuru koşu çıkış kodu **1** verir, yani zincir kendini "hazır" ilan etmez
(`results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json`, 2026-09-02;
`results/saha_kuru_kosu_20260903_120254/ozet.json` ile 2026-09-03'te aynı sonuç
tekrar üretildi). Genel kapı (`codes/test_rota_sentetik.py`) 15 belirlenimci arena
sahnesinde iki kolda da **15/15** geçmektedir (son koşum 2026-09-04, RC=0).

### Y-1-M02 — İHA, İKA ve Mancınık sistemlerinin final tasarım faaliyetleri ve özgün sistem mimarileri

Yönerge üç platformu **ayrı ayrı** ister. Bugünkü olgunluk üç platformda eşit
değildir ve bu özet eşitmiş gibi yazmaz.

**(1) İHA — FDA görev test uçuşu aracı (çoklu rotor).** Final tasarım faaliyeti
tamamlanmış, donanım künyesi sabitlenmiştir: Pixhawk 6C + PM02, Holybro M9N,
5008 340KV ×4 motor / 12×10 pervane, 80 A ESC, FCHUB-12S V2 güç dağıtımı,
FlySky FS-i6 (iBUS), 2× SiK 433 MHz telemetri, görev bilgisayarı ~~**Jetson Nano 4GB** (JetPack 4.6)~~
→ **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12; 3 Eylül beyanı 'Nano 4GB' 6 Eylül'de kartla YANLIŞLANDI — D-431), kamera **Raspberry Pi HQ (IMX477, CSI)**, 4S 10 Ah pil
(`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 — **kullanıcı beyanı**, 5 Eylül'de kutu
açılarak teyit edilecek). Özgün olan taraf gövde değil **karar mimarisidir**:
serbest alan otoritesi + fail-closed + her karede tam mesaj (§Y-1-M01).

**(2) İHA — yarışma final aracı (sabit kanat).** Yapısal ve aerodinamik tasarım
DDR'de sunulmuştur; FDR seviyesindeki final tasarım faaliyetleri (ağırlık-denge,
boyut güncellemeleri, kontrol yüzeyi, aerodinamik/kararlılık/performans/yük
hesapları) **bu özetin kapsamı dışındadır ve Bölüm 3.1'e aittir**.
- **BEYAN GEREKLİ (insan):** Sabit kanat final aracının DDR sonrası tasarım
  güncellemeleri (kanat/gövde/kuyruk geometrisi, CG, atalet) — Bölüm 3.1'i
  yazacak tasarım ekibinden alınacaktır.

**(3) İKA.** Bugün kanıtlı olan **yazılım mimarisidir**, mekanik tasarım değil.
İKA hareket katmanı sürücü soyutlamasına ayrılmış, imza tekerlek hızlarıdır
(`hiz_ver(sag, sol)`); sağlık sözleşmesi ardışık hata tavanını **3** kabul eder
(10 Hz'de ~0,3 s) ve tavan aşılınca görev döngüsü **son bir durdurma denemesi
yapıp** başarısız döner; `GercekSurucu` arka uç verilmeden kurulmayı `DONANIM_YOK`
metinli istisnayla **reddeder** (sessiz iskelet yasaktır). Kabul turunun sekiz
ölçütü (T1–T8) koşulmuş ve **GEÇTİ** kaydedilmiştir
(`results/p3_ika_surucu/ON_KAYIT.md`, ön kayıt uygulamadan önce yazıldı;
kabul aracı `scripts/ika_surucu_kabul.py`).
İKA'nın hareket izni koddaki üçlü kilide bağlıdır: `geçerli OPEN_ROUTE ∧ İHA inişi
tamamlandı ∧ YKS'den IKA_GO geldi`.
- **BEYAN GEREKLİ (insan):** İKA şasi/tahrik mekanik tasarımı, malzeme seçimi ve
  yük bırakma düzeneği — DDR REQ-1 (≤ 10 kg, yük hariç) ve REQ-3 (≥ 200 g yük)
  ile birlikte Bölüm 3.2.2'ye girecektir.
- **ÖLÇÜLEMEDİ: gerçek İKA motor sürücüsü.** Arka uç donanımı seçilmediği için
  `GercekSurucu` boştur; kuru koşuda motor halkası `SAHİPSİZ` çıkar. Donanım
  kararı verildiğinde (final dalgası, 21 Eylül sonrası) kapanır.

**(4) Mancınık.** Bugün repoda mancınığa dair olan tek kanıt **arayüz
sözleşmesidir**: yarışma kipinde YKS'nin FIRLATMA düğmesi "mancınıktan ayrılma
damgası" üretir ve kronometreyi başlatır; FDA kipinde aynı düğme `KALKIŞ` etiketiyle
çalışır (`CONTRACTS.md` §6.7, D-393/D-407). Mekanizmanın kendisi (ray geometrisi,
yay sabiti, fırlatma enerjisi) **tasarlanmamıştır**.
- **BEYAN GEREKLİ (insan):** Mancınık ray geometrisi (DDR REQ-58), yay sabiti ve
  İHA'yı ne kadar uzağa fırlatabileceğinin **enerji denklemleriyle** gösterimi
  (yönerge `Y-3.2.3-A01`, `Y-3.2.3-A02`) — tasarım ekibinden alınacaktır.

### Y-1-M03 — ÖDR ve DDR'de tanımlanan gereksinimlerin ve tasarım kriterlerinin nihai tasarım üzerinde doğrulandığı

Rapor bu iddiayı toptan değil **satır satır** kurar. Bölüm 6, şartnamenin yazılıma
düşen **45 hükmünü** tek tek izler ve kapanmamış **12 gereksinimi** tarihleriyle
birlikte ayrı bir tabloda toplar. Bu raporun en güçlü iddiası bir yüzde değil, o
tablonun **var olmasıdır**.

DDR'nin operasyonel gereksinimlerinden yazılım tarafında **kod ve testle kilitli**
olanlar: HTAB'de güzergâh tespiti (REQ-13), güzergâhın İKA'ya aktarılması (REQ-15),
aktarımın İHA inişinden önce tamamlanması (REQ-16) ve İKA'nın izinsiz hareket
etmemesi (REQ-19 zinciri) — üçlü kilit ve ACK'li aktarım
(`navitas-teknofest/references/ddr_requirements.md`; kilit testleri
`tests/test_ika_go_ackli_tekrar.py`).

DDR'nin **yapısal ve uçuş bilimleri** gereksinimleri (REQ-7 sabit kanat, REQ-8
mancınık, REQ-9 paraşüt, REQ-137 T/W ≥ 0,20, REQ-158 MTOW ≤ 25 kg, REQ-185
havada kalış ≥ 0,5 saat, REQ-186 iniş dikey hızı < 7 m/s, REQ-188 fırlatma sonrası
≥ 1,15 × V_stall) bu özette **doğrulanmış diye yazılmaz**; doğrulama yöntemi
(analiz/test/gözle muayene/benzerlik) Bölüm 3.2 ve Bölüm 6'da tanımlanacaktır.
- **ÖLÇÜLEMEDİ: REQ-137, REQ-158, REQ-185, REQ-186, REQ-188.** Final aracı
  üretilmediği ve tartılmadığı için bu beş gereksinimin hiçbiri bugün ölçülmüş
  değildir; ölçüm final dalgasının üretim ve test turunda yapılacaktır.

### Y-1-M04 — Gerçekleştirilen revizyonların tamamlandığı

Bu raporun sunduğu revizyonlar, **bedelleri yazılarak** kapatılmıştır.

**(a) Algı modeli terfisi (v35 → v36).** Üretim modeli `navitas-seg-v36-512`, gerçek
uçuş karelerindeki iki **ön kayıtlı eşiği geçmeden** terfi etmiştir: ROTA ≥ 10
istenirken 8, MASKE_YOK ≤ 10 istenirken 16 ölçülmüştür. Terfi bu eşikler
gevşetilerek değil, **insan kararıyla** ve gerekçesi yazılarak yapıldı (gerçek
karede yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3; bedeli sentetik
arenada K3 0→1, K4 1→4, K6 5→7). Eşikler **değiştirilmedi** ve sonraki terfileri
bağlamaya devam ediyor; önceki model v35 silinmedi, yedek olarak tam özetiyle
defterde duruyor.

**(b) Gecikme ölçümünün düzeltilmesi.** İlk ölçümde toplam p95 **0,458 s** çıkmıştı
ve baskın kalem "telsiz + ACK ≈ 308 ms" görünüyordu. Bağımsız bir çürütücü, bu
308 ms'nin bir ölçüm değil bir **soket zaman aşımı sabitinin** yansıması olduğunu
buldu; düzeltmeden sonra telsiz payı ~2 ms'ye, toplam p95 **0,113 s**'ye indi.
Yanlış sayı silinmedi, üstü çizilip düzeltmesine işaret verildi.

**(c) FDA görev kipi (`--fda`).** Yer istasyonu yarışma görevine (§2.2) göre
yazıldığı için hakem onayının 2/2 adımı İKA aktarım kanıtı istiyordu; FDA uçuşunda
İKA olmadığından bu kanıt hiç gelmez ve **onay tamamlanamazdı** — uçuşu geçersiz
kılacak bir GUI kilidi. Kip eklendi: FDA'da İKA kanıtı aranmaz, süre bütçesi 600 s'ye
iner, paraşüt ve İKA düğmeleri **fiilen** kapatılır (yalnız UI durumu değil, eylemin
kendisi reddedilir), iniş kanıtı zorunlu kalır (`CONTRACTS.md` §6.7, D-407).

**(d) Güvenli uçuş sonlandırma komutları.** `RTL` ve `LAND`, `PARACHUTE`/`ARM`/`DISARM`
ile aynı tekrar ve kaynak-kimliği sözleşmesine bağlı olarak komut alıcısına eklendi
(`comms/iha_komut_alici.py`); kaynak pini olmayan hiçbir komut kabul edilmez.
Kilitler ölçülmüştür: `tests/test_iha_rtl_land.py` **6 test OK**,
`tests/test_iha_komut_guvenligi.py` **10 test OK** (2026-09-04).

**(e) Seri port çakışması.** Pixhawk'ı üç ayrı sürecin açmaya çalışması hem MAVLink
hem NAVITAS protokolü için çoğullayıcıya bağlanmış ve kapıya alınmıştır.

**(f) İKA sürücü soyutlaması.** Motor komutu doğrudan simülatör süreçlerine basılıyordu
ve zaman aşımı istisnası görev döngüsünü **çökertiyordu**; sürücü katmanı, ardışık hata
tavanı ve fail-loud `GercekSurucu` ile kapatıldı (§Y-1-M02(3)).

- **BEYAN GEREKLİ (insan):** DDR aviyonik BOM'u (28 kalem, toplam **2293 g**;
  `navitas-teknofest/references/ddr_requirements.md`) **final aracına** aittir ve
  bugünkü FDA aracı künyesiyle aynı değildir (DDR'de Jetson Orin NX + Arducam IMX477
  + Holybro M10 + TBS Crossfire; FDA aracında Jetson Orin Nano Developer Kit 4 GB (6 Eylül ölçüm, D-431; 3 Eylül beyanı 'Nano 4GB' yanlışlandı) + RPi HQ + M9N + FS-i6).
  Final aracının aviyonik BOM'unun DDR'ye göre revize edilip edilmediği beyan
  edilecek ve Bölüm 3.3.1'e DDR ↔ FDR karşılaştırmalı olarak girecektir.

### Y-1-M05 — Sistemin görev tanımını karşılayacak olgunluğa ulaştığı

**Olgunluk, iki uçlu yazılır: neyin hazır olduğu ve neyin olmadığı.**

Hazır olan: algı → karar → aktarım → hakem onayı zinciri uçtan uca koşuyor, kapılar
geçiyor (§Y-1-M10 tablosu), yer zinciri bütünleşik kuru koşuda 9/10 halkada GEÇTİ,
ArduCopter parametre şablonu ve QGC görev planı testle kilitli, Jetson yığını 6 Eylül'de
kartta (Orin Nano Developer Kit 4 GB) kuruldu ve kapıları koştu: genel kapı 15/15 · 15/15,
FPS kapısı GEÇTİ (pt 1,35/1,06 · engine 1,58/1,33 FPS, eşik 0,61) — D-431. (3 Eylül'deki
"Nano yığını çevrimdışı kurulabilir" hazırlığı kartla yanlışlandı: cp38 tekerlek zinciri bu kartta
kullanılamadı.)

Hazır **olmayan** üç şey vardır ve üçü de bu raporda açık durur:

**(1) Elimizde gerçek arena karesi yoktur.** K0–K7 kabul kapılarının tamamı sentetik
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

**(2) İkinci büyük sınır gerçek İKA motor sürücüsünün olmamasıdır.** Sürücü arayüzü,
kabul harnessı ve fail-closed davranış hazırdır; `GercekSurucu` arka uçsuz
kurulmayı **reddeder** (sessiz iskelet yasaktır). Kuru koşu bu halkayı `SAHİPSİZ`
olarak raporlar ve çıkış kodu 1 verir. Bu bir donanım kararıdır, final dalgasının
işidir ve görev test uçuşunu etkilemez (o uçuşta İKA yoktur).

**(3) Üçüncüsü: gerçek SiK 433 MHz hattı hiç ölçülmemiştir.** Bugüne kadarki tüm
aktarım kanıtı UDP loopback üzerindedir. Detay tasarım raporundaki ">%98 teslim,
300 m" iddiasının bugün kanıtı yoktur; ölçüm aracı yazılmış ve gerçek bayt
akışında sınanmıştır, ama iki telsiz henüz kutudan çıkmamıştır.

### Y-1-M06 — Nihai mekanik, aviyonik ve yazılım mimarileri; alt sistem konfigürasyonları; fiziksel ve fonksiyonel etkileşimler

**Yazılım mimarisi ve fonksiyonel etkileşimler.** Üç birim arasındaki iş bölümü
sabittir ve kodda kilitlidir:

*Hava tarafı.* İHA otonom uçuşta hedef tespit alanının üstüne gelir, asgari 30
metre irtifada (görev planında 32 m, 2 m barometre payı) tek pas tarama yapar.
Her karede karar üretilir; kararlar **histerezisten** geçer — farklı bir şerit
ancak arka arkaya K karede teyit edilirse yayına girer, ama `NO_ROUTE` **asla**
geciktirilmez. Karar ACK'li olarak YKS'ye ve İKA'ya gider; ayrı bir iş
parçacığından saniyede bir HEARTBEAT akar ve bu heartbeat son **algı kararının
yaşını** (`karar_yas`) taşır.

*Yer tarafı.* Hakem, YKS ekranında rotayı, güven değerini, model künyesini ve
tespitin tazelik damgasını görür. Onay **iki aşamalıdır**: birinci aşama tespitin
görüldüğünü, ikinci aşama güzergâhın İKA'ya ulaştığını teyit eder ve ACK ancak
ikinci aşamada gönderilir. Bayat bir tespit "canlı" gösterilemez; tazelik
penceresi sözleşmede 5 saniyedir.

*Kara tarafı.* İKA'nın hareketi üç koşula birden bağlıdır ve bu kilit koddadır:
`geçerli OPEN_ROUTE ∧ İHA inişi tamamlandı ∧ YKS'den IKA_GO geldi`. İniş sinyali
insan beyanı değil **uçuş kontrolcüsü kanıtıdır** (`EXTENDED_SYS_STATE.landed_state
== ON_GROUND` ve `relative_alt < 1 m`, aynı sysid, ardışık üç çift). Yer
istasyonundaki "İHA İNDİ" düğmesi bu kilidi **açamaz**.

**Fiziksel etkileşimler ve alt sistem konfigürasyonu (FDA aracı).** Görev
bilgisayarı (Jetson Orin Nano Developer Kit 4 GB — D-431) CSI hattından kamerayı (RPi HQ, IMX477), UART
hattından uçuş kontrolcüsünü (Pixhawk 6C) ve telsiz hattından YKS'yi görür. Aynı
seri portu üç sürecin açmaya çalışması ölçülmüş bir çakışmaydı; hem MAVLink hem
NAVITAS protokolü **çoğullayıcıya** bağlanmış ve kapıya alınmıştır (§Y-1-M04(e)).

**İki aracın ortak yazılımı.** Algı, karar, haberleşme ve yer istasyonu katmanı
**iki araçta da aynı koddur**; yer istasyonu farkı `--fda` bayrağıyla tanır.
Şartname iki ayrı doğrulama ister ve bu rapor ikisini karıştırmaz: **21 Eylül'deki
prova ve 30 Eylül – 3 Ekim'deki görev test uçuşu (§5.3.2) çoklu rotorlu bir drone ile**,
İKA olmadan, YKS'ye aktarım ve hakem onayı ekseninde yapılır; **finalin yarışma
görevi (§2.2)** sabit kanat + mancınık + paraşüt + İKA ile icra edilir.

- **BEYAN GEREKLİ (insan):** İHA ve İKA için renk kodlu (PWM / UART / I2C ve güç
  hatları ayrılmış) **bağlantı şemaları** — yönerge `Y-3.3.1-M01` bunları zorunlu
  kılıyor; bugün metin var, çizim yok.

### Y-1-M07 — Üretim yöntemleri, malzemeler, montaj süreçleri ve saha kurulum prosedürleri

**Üretim (FDA aracı).** Gövde **eklemeli imalatla (3B baskı)** üretilmiştir.
- **BEYAN GEREKLİ (insan):** Baskı reçetesi (malzeme, katman yüksekliği, dolgu
  oranı, duvar sayısı) ve kolların hangi reçeteyle basıldığı — yönerge Bölüm 5
  değişikliklerin **gerekçelendirilmesini** ister; bugün kol 1–2 ile kol 3–4
  arasındaki reçete farkının gerekçesi kayıtta yoktur (`FDR/YONERGE_HARITASI.md`
  `Y-5-M05` altında 🔴 RİSK olarak işaretli).
- **BEYAN GEREKLİ (insan):** Parça başına üretim süresi, iş gücü ihtiyacı ve
  toplam imalat süresi.

**Yazılım tarafı üretime hazır.** ArduCopter parametre şablonu (**31** parametre, her
satırda gerekçe) ve QGC görev planı (TAKEOFF 32 m → 20×20 m üzerinde tek pas →
LOITER 60 s → LAND) repoda ve testle kilitlidir; kötü-durum süre bütçesi
**221,5 s ≤ 600 s** hesaplanmıştır. Jetson Nano yığını çevrimdışı kurulabilecek
biçimde hazırlanmıştır (14/14 paket aarch64/cp38 tekerlek, 246 MB) — sahada
internet varsayımı yoktur.
⚠ **6 Eylül düzeltmesi (D-431):** kart Jetson Orin Nano Developer Kit 4 GB (Python 3.12) çıktı; cp38 tekerlek zinciri bu kartta kullanılamadı, kurulum kartta apt/pip ile (internetle) yapıldı ve kapılar geçti (genel kapı 15/15, FPS kapısı GEÇTİ). Çevrimdışı hazırlık tarihli kayıt olarak durur.

**Saha kurulum prosedürü yazılıdır.** Kanonik saha yordamı `SAHA_RUNBOOK.md`
(P4 · D-394) altında altı kart hâlinde durur: sahaya çıkmadan PC kontrolü,
açılış kartı (hazırlık ≤ 900 s, §6.2 — her 30 s +1 puan), YKS operatör kartı,
İHA/Jetson kartı, tekrar fırlatma/reset kartı, prova ve kanıt kartı, ve 21 Eylül
**kesin-hazır kapısı**. Montaj günü akışı saat saat planlanmıştır: kutu ve envanter
(09:00) → mekanik yerleşim (09:30–11:00) → kablolama (11:00–12:30, pervanesiz ve
pil takılı değil) → Pixhawk yapılandırması (13:00–14:30) → Jetson Nano kurulumu
(14:30–17:00) → yer zinciri (17:00–18:30, pervanesiz)
(`SAHA_HAZIRLIK_PLANI_20260903.md` §2).

- **BEYAN GEREKLİ (insan):** Yapısal malzeme listesi, bağlantı elemanları ve
  yapıştırıcı tablosu, tedarikçi ve teslim süreleri (yönerge `Y-3.2.1-T07`,
  `Y-3.2.1-T08`).

### Y-1-M08 — Teknik riskler, önleyici tedbirler, risk azaltma stratejileri ve acil durum senaryoları

**Tasarımın taşıyıcı risk stratejisi fail-closed'dır.** Belirsizlik hâlinde sistem
susmaz, **`NO_ROUTE` der ve sebebini yazar** (§Y-1-M01). Şartname yanlış güzergâha
0 puan verdiği için asimetri bilinçlidir.

**Uçuş emniyeti — uçuş kontrolcüsü tarafında kilitli acil durum tepkileri.**
Aşağıdakiler `config/pixhawk/arducopter_fda.param` içinde satır satır gerekçelidir
ve `tests/test_faz_b_pixhawk_sablon.py` ile kilitlidir:

| senaryo | parametre | tepki |
|---|---|---|
| Kumanda sinyali kaybı | `FS_THR_ENABLE,1` | **RTL** (eve dön) |
| YKS heartbeat kaybı | `FS_GCS_ENABLE,1` | **RTL** |
| Düşük pil | `BATT_LOW_VOLT,14.4` + `BATT_FS_LOW_ACT,2` | **RTL** |
| Kritik pil | `BATT_CRT_VOLT,14.0` + `BATT_FS_CRT_ACT,1` | **LAND** (bulunduğu yere in) |
| Coğrafi çit ihlali (irtifa/yarıçap) | `FENCE_ENABLE,1` · `FENCE_TYPE,3` · `FENCE_ALT_MAX,50` · `FENCE_RADIUS,60` · `FENCE_ACTION,1` | **RTL ya da iniş** |
| Dönüş irtifası | `RTL_ALT,3500` (35 m) | Görev irtifasının (30 m) üstü, çitin (50 m) altı — RTL çit ihlali üretmez |

Buna ek olarak yer istasyonu, uçuşu **elle sonlandırma** yolunu da açık tutar:
`RTL` ve `LAND` komutları kaynak-kimliği ve tekrar sözleşmesine bağlı olarak
gönderilir; kaynak pini olmayan komut kabul edilmez
(`comms/iha_komut_alici.py`; `tests/test_iha_rtl_land.py` 6 test OK,
`tests/test_iha_komut_guvenligi.py` 10 test OK, 2026-09-04).

**Görev riskleri ve önlemleri** (`SAHA_HAZIRLIK_PLANI_20260903.md` §8):

| risk | önleyici tedbir |
|---|---|
| Nano yığını kurulamaz (Py3.8 / torch / kamera) | çevrimdışı tekerlekler (14/14), **CPU torch garanti yolu**, **USB webcam yedeği**, kurulum bitmezse ertesi sabah devam |
| Yanlış güzergâh = 0 puan | histerezis, tek pas, hakem ekranında güven değeri + ret sebebi |
| 10 dakikalık operasyon süresinin aşılması | kısa görev planı (bütçe 221,5 s), loiter ACK tavanı, YKS kronometresi |
| Tek pil | günde ≤ 2 uçuş; ikinci pil / şarj kararı kaptanda |
| Görev bilgisayarında çökme döngüsü (hands-off) | ekransız kip, `Restart=always`, seri port çoğullayıcı |
| Pusula / GPS / titreşim | direk montaj, açık alanda kalibrasyon, damper, ilk hover logunun incelenmesi |
| PM02 akım sınırı | sürekli tam gaz yok, `BATT_AMP` ekranda, motor testi kısa |

**Ölçülmüş, kapanmamış teknik risk:** modelin sahne bağıntılı **51 saniyelik kör
aralığı** (§Y-1-M05(1)). Bugünkü azaltma tedbiri gizlemek değil **göstermektir**:
heartbeat `karar_yas` taşır, hakem tespitin yaşını ekranda görür, bayat tespit
canlı sayılmaz.

- **ÖLÇÜLEMEDİ: arıza emniyet tepkilerinin sahada test edilmesi.** Yukarıdaki
  RTL/LAND/çit tepkileri bugün yalnız parametre ve testle kilitlidir; gerçek
  uçuşta tetiklenip ölçülmemiştir. Yönerge `Y-4-M12` bunu zorunlu kılar; ölçüm
  5–19 Eylül uçuş testlerinde yapılacaktır.

### Y-1-M09 — Operasyon planı, görev akışı, ekip organizasyonu, görev dağılımı ve kurulum süreçleri

**Görev akışı (FDA görev test uçuşu).** Hazırlık kronometresi → `KALKIŞ` damgası
(kronometre burada başlar) → otonom tırmanış (TAKEOFF 32 m) → 20×20 m alan üzerinde
tek pas tarama (asgari irtifa 30 m) → her karede karar → YKS'ye canlı aktarım →
hakem onayı 2/2 (FDA kipinde İKA kanıtı aranmaz) → ACK → LOITER → LAND → iniş
kanıtı (`IHA_LANDED`) ile görev süresi biter. Toplam bütçe **≤ 600 s**; hesaplanan
kötü-durum süresi **221,5 s**.

**Ekip organizasyonu — rol bazlı, isimsiz.** Yönerge Bölüm 2.1 kişisel verilerden
arındırılmış anlatım istediği için organizasyon **yalnız rol kodlarıyla** yazılır:
R1 Takım Kaptanı, R2 Pilot, R3 Aviyonik sorumlusu, R4 Görev bilgisayarı/kamera,
R5 YKS operatörü, R6 İKA sorumlusu, R7 Yazılım/görüntü işleme, R8 Kanıt-kalite
(bağımsız denetim). Rol tanımları, yetkileri ve her rolün **ürettiği kanıt**
Bölüm 2 §2.1.3'te tablodadır. Bağlayıcı kural: **kanıt üreten rol ile o kanıtı
onaylayan rol aynı kişi olamaz.**

**Ölçülmüş organizasyon riski (kayda geçirildi):** R2 (kumandayı tutar, gözü araçta)
ile R5 (hakem ekranını sürer) uçuş anında **eşzamanlıdır**; tek kişi ikisini birden
yapamaz. Montaj gününde ve yer provalarında çakışma yoktur.
- **BEYAN GEREKLİ (insan):** Uçuş günü için R2 ve R5'ten birine ikinci kişi
  atanması; sekiz rolün üyelere ataması; şartname §4 kontenjan (6–10 kişi) teyidi.

**Kurulum süreçleri ve takvim.** Kalan işler **donanım ve insan** işleridir ve
takvimlidir: 5 Eylül montaj ve kablolama günü (kutu ilk kez açılacak), 6 Eylül ilk
hover, 7–16 Eylül uçuş provaları ve tam prova ×3, 17 Eylül **sürüm dondurma**
(bundan sonra kod değişmez), 18 Eylül "kesin hazır" tutanağı, 21 Eylül FDR teslimi
ve Adıyaman provası, 30 Eylül – 3 Ekim resmî görev test uçuşu. Kamera gerçek görüş
açısı, Nano'da kare hızı ve gerçek telsiz gidiş-dönüş süresi **o günlerde ilk kez
ölçülecektir**; bu rapor onları bugün ölçülmüş gibi göstermez.

### Y-1-M10 — Görev gereksinimlerini karşılama düzeyi analizi, tasarım doğrulama süreci özeti ve teknik olgunluk kanıtı

#### Ölçülmüş başlıca sonuçlar

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

**4 Eylül 2026'da yeniden ölçülenler** (aşağıdaki üç satır bu bölümün yazımı
sırasında koşulmuştur; yukarıdaki tablo 3 Eylül durumudur ve tarihleri korunmuştur):

| ne | ölçülen | komut |
|---|---|---|
| Genel kapı, iki kol | **15/15 · 15/15**, RC=0 | `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py` |
| Test dosyası sayısı | **169** (3 Eylül'de 155) | `ls tests/*.py \| wc -l` |
| Kanıt defteri | **424** `### D-` başlığı · **418** benzersiz numara (3 Eylül'de 420 / 414) | `grep -cE "^### D-[0-9]+" REVIEW_LOG.md` |

⚠ **Tam süit bu bölümün yazımında yeniden koşulmadı.** 3 Eylül'deki 1896 test
sayısı, o günden bu yana test dosyası sayısı 155 → 169'a çıktığı için **bayattır**;
teslimden önce yeniden koşulacaktır (aşağıdaki *DOĞRULANACAK* kalemi).

#### Tasarım doğrulama sürecinin özeti

Bu rapor dört kurala uyar ve bu kurallar rapor için icat edilmemiştir; projenin
420 kayıtlık ölçüm defterinden gelir:

1. **Her sayı bir artefakttan gelir.** Her bölümün sonundaki *Kanıt dizini*, geçen her sayının dosya yolunu, onu üreten betiği ve ölçüm tarihini verir.
2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Koşulmamış kapı "sorun çıkmadı" diye yazılmaz; paydası olmayan oran rapora girmez.
3. **Geçmeyen kapı geçmedi diye yazılır** — v36'nın iki eşiği ve histerezisin özgün H1 eşiği bu raporda açıkça geçmemiş olarak durur.
4. **Sentetik ölçüm saha başarımı diye sunulmaz.**

Bu kuralların işlediği ölçülebilir: gecikme sayısının hikâyesi, sayının kendisinden
önemlidir (§Y-1-M04(b)) — yanlış çıkan 0,458 s defterden silinmedi, üstü çizilip
düzeltmesine işaret verildi. Bu rapordaki sayıların güvenilirliği, bu tür
düzeltmelerin **kayıtta durmasından** gelir.

#### Karşılama düzeyi ve teknik olgunluk

Bölüm 6, şartnamenin yazılıma düşen **45 hükmünü** tek tek izler ve kapanmamış
**12 gereksinimi** tarihleriyle birlikte ayrı bir tabloda toplar. Bu raporun en
güçlü iddiası bir yüzde değil, o tablonun **var olmasıdır**.

Bugünkü teknik olgunluk özeti: **yazılım ve karar zinciri uçuşa hazır kabul
edilebilecek kapı kanıtına sahiptir; donanım entegrasyonu ve saha ölçümleri
başlamamıştır.** Bu ikisi arasındaki fark, bu raporun her bölümünde iki açık kalem
etiketiyle (insan beyanı bekleyen ve ölçüm bekleyen kalemler) görünür tutulmuştur;
etiketli satırlar `scripts/fdr_acik_kalem_cikar.py` ile bölümlerden **çıkarılıp
sayılır**, elle tutulmaz.

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
| **45** izlenen gereksinim satırı, **12** açık gereksinim | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` §6.5.1, §6.6.1 | bu raporun Bölüm 6'sı | 2026-09-03 |

### Kanıt dizini — yönergeye taşıma sırasında eklenenler (2026-09-04)

| sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|
| Genel kapı **15/15 · 15/15**, RC=0 (yeniden koşum) | konsol çıktısı | `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py` | **2026-09-04** |
| **169** test dosyası (`tests/*.py`) — 3 Eylül'de 155 idi | `tests/` | `ls tests/*.py \| wc -l` | **2026-09-04** |
| Kanıt defteri **424** `### D-` başlığı · **418** benzersiz numara | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+" REVIEW_LOG.md`; `grep -oE "^### D-[0-9]+" REVIEW_LOG.md \| sort -u \| wc -l` | **2026-09-04** |
| Güvenli uçuş sonlandırma kilitleri: `RTL`/`LAND` **6 test OK**; komut güvenliği **10 test OK** | `tests/test_iha_rtl_land.py` · `tests/test_iha_komut_guvenligi.py` · uygulama `comms/iha_komut_alici.py` | `... -m unittest discover -s tests -p "test_iha_rtl_land.py" -q` (ve `test_iha_komut_guvenligi.py`) | **2026-09-04** |
| Kuru koşu **GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor)**, çıkış kodu 1 — 2 Eylül sonucunun tekrarı | `results/saha_kuru_kosu_20260903_120254/ozet.json` | `scripts/saha_kuru_kosu.py` | **2026-09-03 12:02:54** |
| Arıza emniyet parametreleri: `FS_THR_ENABLE,1` · `FS_GCS_ENABLE,1` · `BATT_LOW_VOLT,14.4` + `BATT_FS_LOW_ACT,2` (RTL) · `BATT_CRT_VOLT,14.0` + `BATT_FS_CRT_ACT,1` (LAND) · `FENCE_ENABLE,1` · `FENCE_TYPE,3` · `FENCE_ALT_MAX,50` · `FENCE_RADIUS,60` · `FENCE_ACTION,1` · `RTL_ALT,3500` | `config/pixhawk/arducopter_fda.param` | `grep -n "FS_\|RTL\|FENCE\|BATT" config/pixhawk/arducopter_fda.param`; kilit `tests/test_faz_b_pixhawk_sablon.py` | **2026-09-04** |
| İKA sürücü kabul turu **T1–T8 GEÇTİ**; ardışık hata tavanı **3**; `GercekSurucu` arka uçsuz kurulumda `DONANIM_YOK` istisnası | `results/p3_ika_surucu/ON_KAYIT.md` (ön kayıt uygulamadan önce yazıldı, D-107) · kabul aracı `scripts/ika_surucu_kabul.py` | P3 kabul turu (2026-09-02 gece) | 2026-09-02 |
| FDA görev kipi sözleşmesi (`--fda`): süre 600 s, hakem onayında İKA kanıtı aranmaz, paraşüt/İKA düğmeleri fiilen kapalı, iniş kanıtı zorunlu | `CONTRACTS.md` §6.7 (D-407) · uygulama `comms/yks_gui.py` | `tests/test_faz_b_yks_fda_kipi.py` | 2026-09-02 |
| DDR aviyonik BOM **28 kalem / toplam 2293 g** (final aracı) ve DDR operasyonel gereksinimleri (REQ-1, REQ-3, REQ-7…REQ-9, REQ-13, REQ-15, REQ-16, REQ-19, REQ-20, REQ-58, REQ-137, REQ-158, REQ-185, REQ-186, REQ-188) | `navitas-teknofest/references/ddr_requirements.md` | DDR dönemi belgesi (kaynak metin) | DDR dönemi |
| Saha yordamı: açılış kartı, YKS kartı, İHA/Jetson kartı, reset kartı, prova kartı, 21 Eylül kesin-hazır kapısı | `SAHA_RUNBOOK.md` (P4 · D-394) | — | 2026-09-02 |
| Montaj günü saat planı (09:00 envanter → 18:30 yer zinciri) ve risk tablosu (7 risk) | `SAHA_HAZIRLIK_PLANI_20260903.md` §2, §8 | — | 2026-09-03 |
| Rol kodları R1–R8, yetkileri ve ürettikleri kanıt; R2/R5 uçuş anı çakışması | `FDR/BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` §2.1.3, §2.1.4, §2.1.5 | bu raporun Bölüm 2'si | 2026-09-03 |
| Yönerge Bölüm 1 madde kimlikleri `Y-1-M01…M10` | `FDR/YONERGE_HARITASI.md` §1 · yönerge tam metni `results/fdr_sablon/fdr_yonerge_metin.txt` | pypdf metin çıkarımı | 2026-09-03 |

### BEYAN GEREKLİ (insan)

- **BEYAN GEREKLİ (insan):** Takım adı, takım numarası, kategori ve üniversite/kurum künyesi — bu bölümün başına eklenecek.
- **BEYAN GEREKLİ (insan):** Gerçek kütleler (İHA, İKA, yük) — 5 Eylül tartı listesi.
- ~~**BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen kare hızı ve `torch.cuda.is_available()` sonucu.~~ → **ÖLÇÜLDÜ 6 Eylül (D-431):** kart Jetson Orin Nano Developer Kit 4 GB; `torch.cuda.is_available()` **True** (`cuda_adi: Orin`); `scripts/jetson_fps.py` 120 örnek: pt p50/p95 **1,35/1,06 FPS** · engine **1,58/1,33 FPS**, eşik 0,61 → GEÇTİ; ONNX kolu HATA (`cudaErrorNoKernelImageForDevice`) — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`.
- **BEYAN GEREKLİ (insan):** RPi HQ kamera gerçek yatay görüş açısı (`kamera_dogrula` ölçümü); rapordaki 55–63° aralığı lens beyanından türetilmiş **tahmindir**.
- **BEYAN GEREKLİ (insan):** Gerçek SiK 433 MHz hattında gidiş-dönüş süresi ve paket kayıp oranı.
- **DOĞRULANACAK:** Bu özetin sayıları rapor teslim edilmeden önce, teslim günündeki kapı koşusuyla **yeniden üretilmelidir**; bayat sayı taşımak bu projede birden çok kez kusur olarak kayda geçti.
- **DOĞRULANACAK:** Tam test süiti (3 Eylül: 1896 test OK) teslimden önce yeniden koşulacaktır; test dosyası sayısı 155 → 169 değiştiği için 1896 sayısı bugün bayattır.
- **DOĞRULANACAK:** Bu bölüm, Bölüm 2–7 kesinleştikten sonra **yeniden üretilecektir** (bölüm başındaki üretim sırası uyarısı).
