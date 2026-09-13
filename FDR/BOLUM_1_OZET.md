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
tamamlanmış, donanım künyesi sabitlenmiştir: Pixhawk 6C + **PM06** güç modülü (~~PM02~~ — 5–6 Eylül kutu açımında **GÖZLENDİ**, D-426; kanıt sınıfı **GÖZLEM/BEYAN**, ölçüm değil. ⚠ `config/pixhawk/emir.param:126` `BATT_AMP_PERVLT,36.36` ve `:143` `BATT_VOLT_MULT,18.18` **Pixhawk 6C hwdef VARSAYILANIDIR** — deponun kendi şablonu bu iki sayıyı PM02 ölçeği diye kaydeder (`config/pixhawk/arducopter_fda.param:171`, `config/pixhawk/README.md:137`) ve değerler 6 Eylül dökümünden (`config/pixhawk/arducopter_fda_20260906.param:126,:143`) beri **birebir aynıdır, yani kartta hiç dokunulmamıştır**; dolayısıyla güç modülünün PM06 olduğuna **bağımsız kanıt DEĞİLDİR**. İkisi de **FABRİKA/VARSAYILAN değeridir ve DOĞRULANMAMIŞTIR** — pens ampermetre/multimetre karşılaştırması (A13) 12 Eylül'de yapılamadı, alet yoktu (D-473); planlanan ölçüm: **A13, 21 Eylül 2026**), Holybro M9N,
~~5008 340KV ×4 motor / 12×10 pervane~~ → **SunnySky X2220 980KV V3 ×4** motor (**BEYAN** — kullanıcı beyanı 7 Eylül 2026, D-435 ek; **etiket fotoğrafı 13 Eylül 2026 itibariyle hâlâ YOKTUR**, T211'in insan girdisi kapanmadı. 12 Eylül atölye adımlarının hiçbiri — A1, A2, A3, A4, A5, A12 — motor modelini bağımsız doğrulamaz; planlanan kanıt: **motor etiketi fotoğrafı, 14 Eylül 2026**) / **10×4,5 (1045)** pervane (**BEYAN**, aynı kayıt; ⚠ üreticinin hiçbir sayfasında 1045 satırı yoktur, en yakın üretici satırı APC1047 — D-435 ek 2) — 5008'ler iade edildi; itki bütçesi **ÖLÇÜLMEDİ, HESAPLANDI** (Bölüm 3 §3.2.1.1.1, T211): askı itkisi kartta öğrenilmemiştir — `config/pixhawk/emir.param:580` `MOT_THST_HOVER,0.35` **fabrika değeridir** ve 6 Eylül dökümünde de (`config/pixhawk/arducopter_fda_20260906.param:580`) aynıydı; `:565` `MOT_HOVER_LEARN,2` açık olmasına rağmen öğrenme **gerçekleşmemiştir**. ⚠ **Sebebi ÖLÇÜLMÜŞ değildir:** öğrenme yalnız irtifa denetimli kiplerde (AltHold / Loiter / PosHold / Guided) çalışır ve 12 Eylül'ün 15 s askısı **GUIDED** kipinde yapılmıştır (kullanıcı beyanı, 13 Eylül 2026) — yani kip engeli değildir; süre mi yetmedi başka bir şey mi, **BİLİNMİYOR**, çünkü uçuşun `.bin` logu SD karttan **silinmiştir**. Kesin olan tek şey `MOT_THST_HOVER`'ın 6 Eylül'den beri 0,35'te kalmasıdır (D-474 §4). Yerine **HESAP (üretici veri sayfası, ölçüm değil)**: SunnySky X2220-III KV980, **3S + APC1047** → motor başına tepe **1454 gf / 27 A**, dört motor tepe **5,82 kgf** (D-435 ek 2 aynı satırı **5,8 kg** diye yuvarlar); hover ≤ %50 kuralıyla azami araç kütlesi **≤ 2,90 kg**; üreticinin 3S çoklu rotor tasarım noktası 600 gf/motor → **2,40 kg** araçta hover oranı **%41,4**. ⚠ **Araçtaki pervane 10×4,5 (1045)'tir ve üreticide 1045 satırı YOKTUR** (D-435 ek 2 birebir: *"10×4,5 (1045) satırı hiçbir sayfada yok → 1045 için BİLİNMİYOR"*); 27 A **en yakın pervaneden (10×4,7) yapılmış bir YAKLAŞTIRMADIR**, bu pervanenin ölçümü değildir. Askı akımı **HESAP** (ideal itki diski, I ∝ T^1,5): 27 × (600/1454)^1,5 = **7,2 A/motor**, dört motor **28,8 A**; aviyonik ~1,4 A ile toplam **30,2 A** → 3S 6000 mAh pilde %80 kullanımla **uçuş süresi ≈ 9,5 dk (HESAP)**. 3S geçişinin hesaplanan kazancı: tam gaz akımı 27 A, motorun **38 A / 30 s** sürekli sınırının altında kalır (4S + APC1047'de 38,4 A ile sınır aşılıyordu — **D-435 ek 2**; D-436 başka bir motorun, T-Motor VELOX V3115 KV900'ün kaydıdır ve buraya kaynak değildir). **Bu sayıların hiçbiri ölçüm değildir**; kapatma yolu iki adımdır: (a) pilli araç tartısı (T10), (b) AltHold'da 30 s askı → `MOT_THST_HOVER` öğrensin (T261) — planlanan ölçüm **21 Eylül 2026**. **60 A ESC** (Hobbywing Skywalker 60A V2, etiket beyanı D-426; ~~80 A~~ değeri bayattı), FCHUB-12S V2 güç dağıtımı,
FlySky FS-i6 (iBUS), 2× SiK 433 MHz telemetri, görev bilgisayarı ~~**Jetson Nano 4GB** (JetPack 4.6)~~
→ **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12; 3 Eylül beyanı 'Nano 4GB' 6 Eylül'de kartla YANLIŞLANDI — D-431), kamera **Raspberry Pi HQ (IMX477, CSI)** — 90° nadir montaj **BEYANI** (D-471, kullanıcı; ⚠ **montaj açısı ÖLÇÜLMEDİ — kamera monte edilmemiştir**); ⚠ **kamera 13 Eylül 2026 itibariyle elde YOKTUR ve 14 Eylül teslimine yetişmemektedir** (D-473) —, ~~4S 10 Ah~~ → **3S 6000 mAh** pil (**kullanıcı BEYANI**, 12 Eylül 2026 kararı, gerekçe **stabilite**; 4S varsayımı **GEÇERSİZ**. Kart dökümü bu beyanla **TUTARLIDIR — doğrulama değildir**: `config/pixhawk/emir.param:138` `BATT_LOW_VOLT,10` ve `:131` `BATT_CRT_VOLT,9`, 6 Eylül dökümünde 14,4 ve 14 idi. ⚠ Bu iki parametre **insanın elle yazdığı failsafe eşikleridir; pilin hücre sayısını ÖLÇMEZLER** — değişmiş olmaları, birinin 3S varsayarak parametreyi değiştirdiğini gösterir, pilin 3S olduğunu değil. Pilin 3S 6000 mAh olduğu hâlâ yalnız **kullanıcı beyanıdır** (D-471 / D-474); bağımsız kanıt = pil etiketi fotoğrafı ya da şarj cihazının hücre sayımı — planlanan **14 Eylül 2026**)
(`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 — 3 Eylül **kullanıcı beyanı**; ~~5 Eylül'de kutu
açılarak teyit edilecek~~ → 5–6 Eylül'de kutu açıldı ve 12 Eylül 23:55'te **gerçek kart dökümü**
alındı: `config/pixhawk/emir.param`, 1025 satır).
🔴 **AÇIK RİSK — kullanıcı 13 Eylül'de kapattığını BEYAN etti, kartta DOĞRULANMADI:** 12 Eylül
dökümünde `emir.param:129` `BATT_CAPACITY,3300` iken pil **6000 mAh**'tir; bu hâliyle kapasite
sayacı **%45 düşük** okur, Mission Planner'ın "kalan kapasite" göstergesi ve mAh tabanlı uyarılar
geçersizdir. Uçuş emniyeti bugün korunuyor çünkü `BATT_LOW_MAH`/`BATT_CRT_MAH` = 0, yani failsafe
**yalnız gerilimle** çalışıyor (D-474 §3). 13 Eylül 2026'da kullanıcı karta **`BATT_CAPACITY,6000`**
ve **`BATT_CRT_VOLT,10.5`** yazdığını beyan etmiştir (T258) — **kanıt sınıfı BEYAN: yeni kart dökümü
alınmadığı için depodaki `emir.param` hâlâ 3300 / 9 okumaktadır.** ⚠ Beyan edilen
`BATT_CRT_VOLT,10.5` V, kartta duran `BATT_LOW_VOLT,10` V'un **ÜSTÜNDEDİR**; kritik eşik düşük
eşiğin üstünde olamaz. Bu kalem, **uçuş öncesi yeni bir tam döküm alınıp iki parametre birlikte
okunmadan KAPANMIŞ sayılmaz** — planlanan tarih **14 Eylül 2026**. Özgün olan taraf gövde değil **karar mimarisidir**:
serbest alan otoritesi + fail-closed + her karede tam mesaj (§Y-1-M01).

**(2) İHA — yarışma final aracı (sabit kanat).** Yapısal ve aerodinamik tasarım
DDR'de sunulmuştur; FDR seviyesindeki final tasarım faaliyetleri (ağırlık-denge,
boyut güncellemeleri, kontrol yüzeyi, aerodinamik/kararlılık/performans/yük
hesapları) **bu özetin kapsamı dışındadır ve Bölüm 3.1'e aittir**.
- **AÇIK — İNSAN BEYANI BEKLİYOR; planlanan beyan: 14 Eylül 2026 (FDR teslimi).** Sabit kanat
  final aracının DDR sonrası tasarım güncellemeleri (kanat/gövde/kuyruk geometrisi, CG, atalet)
  — Bölüm 3.1'i yazacak tasarım ekibinden alınacaktır.
  **Net hüküm (13 Eylül 2026):** final sabit kanat aracı **üretilmemiştir**. Depoda sabit kanada ait
  **tek** geometri/kütle/atalet artefaktı `simulation/models/iha/model.sdf`'tir (kütle **4,0 kg**,
  `ixx 0,0820` …); bu dosya kendi başlığında **"gelişmiş primitif tasarım"** olduğunu söyler,
  **TAHMİN**dir, sayılarının kaynağı gösterilmemiştir ve **final aracın CG/atalet verisi yerine
  geçmez**. Bunun dışında `dronesolid/` altındaki bütün CAD ve 3B dosyaları (kol, alt/üst çerçeve,
  kubbe, ayak, GPS tutucu, TPU taban pedi) **çoklu rotorlu FDA gövdesine** aittir. 12 Eylül atölye
  ölçümlerinin hiçbiri bu kalemi kapatmaz. Bu satıra final aracına ait sayı yazılmaz çünkü
  türetilecek girdi yoktur; girdi geldiği anda hesaplar Bölüm 3.1'de yapılır.

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
- **KISMEN KAPANDI (ölçüm) + AÇIK (insan beyanı; planlanan: 14 Eylül 2026).** İKA şasi/tahrik
  mekanik tasarımı, malzeme seçimi ve yük bırakma düzeneği — DDR REQ-1 (≤ 10 kg, yük hariç) ve
  REQ-3 (≥ 200 g yük) ile birlikte Bölüm 3.2.2'ye girecektir.
  **Kapanan kısım — ÖLÇÜLDÜ (12 Eylül 2026, ekip, şerit metre; D-472):** iz genişliği (sol ve sağ
  tekerin orta düzlemleri arası) **459,5 mm = 0,4595 m**; tekerlek çapı **Ø125 mm** (yarıçap
  0,0625 m — sözleşmeyle aynı, doğrulandı). Bu ölçüm iki sayıyı birden çürüttü: sözleşmedeki `0,39`
  bir **TAHMİN**di (%15 küçük), Gazebo URDF dışa aktarımındaki `0,319` ise **dışa aktarma artığıydı**
  (%31 küçük). Sabit `CONTRACTS.md` §4.1 (`IKA_IZ_GENISLIGI_M`) ve `codes/karar_sozlesmesi.py:1995`
  içinde güncellendi.
  ⚠ **Ölçüm depoya YAYILMAMIŞTIR ve bu kalem bu yüzden KAPANMIŞ sayılamaz (13 Eylül 2026):**
  (a) **uçuşa giden paket kopyası** `jetson_paket/kod/karar_sozlesmesi.py:1995` hâlâ
  `IKA_IZ_GENISLIGI_M = 0.39 # TAHMIN` okur; (b) MuJoCo gövde konumu **0,46** üretiyor ve tam süit
  bu yüzden düşüyor (`tests/test_sim_mujoco_arena.py` → `AssertionError: 0.46 != 0.4595`);
  (c) `simulation/mujoco/araclar.py:44` yorumu hâlâ "(TAHMİN — insan teyidine kadar)" diyor.
  Yani aynı büyüklüğün depoda **üç canlı değeri** vardır. ⚠ Bağlı borç: T213-B / T214-A İKA sürüş
  ölçümleri **eski** iz genişliğiyle koşuldu; **eşikler değişmez**, ölçümler yeni sabitle yeniden
  koşulur ve sonuç ne çıkarsa yazılır (T256).
  **Açık kalan üç başlık:** (a) şasi **malzemesi**, (b) **tahrik** (motor / redüktör / tekerlek
  bağlantısı) seçimi, (c) **yük bırakma düzeneği** — üçü için de depoda kanıt yoktur, üçü de yalnız
  insan beyanıyla kapanır.
- **ÖLÇÜLEMEDİ: gerçek İKA motor sürücüsü — durum 13 Eylül 2026'da yeniden ölçüldü.** Arka uç
  donanımı hâlâ **seçilmemiştir**; `GercekSurucu` boştur. Kuru koşu bugün yeniden koşuldu ve üçüncü
  kez aynı sonucu verdi: **GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor)**, çıkış kodu **1**
  (`results/saha_kuru_kosu_20260913_011108/ozet.json`, `scripts/saha_kuru_kosu.py`, 2026-09-13
  01:11:08). 12 Eylül atölye gününde İKA sürücüsüne dair **hiçbir test yapılmadı** — koşulan altı
  adımın (A1, A2, A3, A4, A5, A12) tamamı hava aracına aittir (D-473). Bu kalemde **ne ölçüm ne
  türetme** vardır: sürücü seçilmeden tekerlek hızına sayı yazılamaz. Kapanma koşulu donanım
  kararıdır — **21 Eylül 2026 uçuşundan sonra**, final dalgası.

**(4) Mancınık.** Bugün repoda mancınığa dair olan tek kanıt **arayüz
sözleşmesidir**: yarışma kipinde YKS'nin FIRLATMA düğmesi "mancınıktan ayrılma
damgası" üretir ve kronometreyi başlatır; FDA kipinde aynı düğme `KALKIŞ` etiketiyle
çalışır (`CONTRACTS.md` §6.7, D-393/D-407). Mekanizmanın kendisi (ray geometrisi,
yay sabiti, fırlatma enerjisi) **tasarlanmamıştır**.
- **AÇIK — TASARIM YOK, İNSAN BEYANI BEKLİYOR; planlanan tasarım + beyan: final dalgası,
  21 Eylül 2026 sonrası.** Mancınık ray geometrisi (DDR REQ-58), yay sabiti ve İHA'yı ne kadar
  uzağa fırlatabileceğinin **enerji denklemleriyle** gösterimi (yönerge `Y-3.2.3-A01`, `Y-3.2.3-A02`).
  **Net hüküm (13 Eylül 2026):** mekanizma **tasarlanmamıştır** (bir üstteki paragrafın kendi
  ifadesi) ve enerji denkleminin gerektirdiği **dört girdinin dördü de yoktur**: ray boyu L, yay
  sabiti k, çekiş mesafesi x ve İHA kütlesi m. Bu yüzden bu satıra **sayı uydurulmaz**. Girdi
  geldiği anda sayı tek satırda çıkar; denklem ve kısıtı bugünden sabittir:
  **½ k x² · η = ½ m v_çıkış² + m g h + F_sürtünme · L**, kısıt **v_çıkış ≥ 1,15 · V_stall**
  (DDR REQ-188) ve **m ≤ 25 kg** (DDR REQ-158), kaynak
  `navitas-teknofest/references/ddr_requirements.md`. Yay sabiti **beyan değil ölçümle** kapanır
  (tezgâhta F–x eğrisi).

### Y-1-M03 — ÖDR ve DDR'de tanımlanan gereksinimlerin ve tasarım kriterlerinin nihai tasarım üzerinde doğrulandığı

Rapor bu iddiayı toptan değil **satır satır** kurar. Bölüm 6, şartnamenin yazılıma
düşen **45 hükmünü** tek tek izler ve kapanmamış ~~12~~ **11 gereksinimi** tarihleriyle
birlikte ayrı bir tabloda toplar. Bu raporun en güçlü iddiası bir yüzde değil, o
tablonun **var olmasıdır**. (⚠ Bu iki sayının tazelik durumu §Y-1-M10'da ayrıca
işlenmiştir: **45** bugün doğrulandı; açık kalem sayısı **11**'dir — `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md`
§6.5.1'in sayım satırı birebir *"Açık satır sayımı: ~~12~~ **11** (A10 6 Eylül'de kapandı, D-431)"*
der; raporda daha önce yazan 12, 6 Eylül **öncesinin** sayısıdır. 12 Eylül atölye sonuçları ve
13 Eylül A6 ölçümü Bölüm 6'ya işlendiğinde bu 11 yeniden sayılacaktır.)

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
- **ÖLÇÜLEMEDİ: REQ-137, REQ-158, REQ-185, REQ-186, REQ-188 — beşi de final sabit kanat aracına
  aittir.** Araç **üretilmedi**, tasarım verisi gelmedi, **tartılmadı**; dolayısıyla hiçbirinin
  paydası yoktur. Eşik burada eşik olarak durur, sonuç hanesi boş bırakılmaz:
  REQ-137 T/W ≥ 0,20 → **ÖLÇÜLEMEDİ** · REQ-158 MTOW ≤ 25 kg → **ÖLÇÜLEMEDİ** · REQ-185 havada
  kalış ≥ 0,5 saat → **ÖLÇÜLEMEDİ** · REQ-186 iniş dikey hızı < 7 m/s → **ÖLÇÜLEMEDİ** ·
  REQ-188 fırlatma sonrası hız ≥ 1,15 × V_stall → **ÖLÇÜLEMEDİ**.
  ⚠ **12 Eylül 2026 atölye günü bu beş maddeye değmez:** koşulan altı adımın (A1, A2, A3, A4, A5,
  A12) tamamı **FDA çoklu rotoruna** aittir (D-473); FDA aracının 3S 6000 mAh / X2220 künyesinden
  türetilen itki bütçesi de (§Y-1-M02(1)) **final aracına taşınamaz** — iki ayrı araçtır.
  Planlanan ölçüm: final aracının üretim ve test turu; **tarihi 14 Eylül 2026'da tasarım ekibi
  beyan edecektir.**

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

- **AÇIK — İNSAN BEYANI BEKLİYOR; planlanan beyan: 14 Eylül 2026.** DDR aviyonik BOM'u
  (~~28~~ **26 kalem** — tabloda **No 25 atlanmıştır**: No 1–24 + 26 + 27; 13 Eylül 2026'da satır
  satır sayıldı —, toplam **2293 g**; `navitas-teknofest/references/ddr_requirements.md:61` TOPLAM
  satırı, ağırlık sütunu toplamı aynı gün yeniden hesaplandı = 2293 g) **final aracına** aittir ve
  bugünkü FDA aracı künyesiyle aynı değildir (DDR'de Jetson Orin NX + Arducam IMX477 + Holybro M10
  + TBS Crossfire; FDA aracında Jetson Orin Nano Developer Kit 4 GB (6 Eylül ölçüm, D-431; 3 Eylül
  beyanı 'Nano 4GB' yanlışlandı) + RPi HQ + M9N + FS-i6 + **PM06** güç modülü (GÖZLEM, D-426) +
  **3S 6000 mAh** pil (12 Eylül kullanıcı beyanı) + ESC **Hobbywing Skywalker 60A V2**).
  **Net hüküm (13 Eylül 2026):** FDA aracının künyesi yukarıdaki üç düzeltmeyle (PM06, 3S 6000 mAh,
  60 A ESC) **güncellenmiştir**; sorulan şey ise **final aracının** BOM'udur ve ona ait **hiçbir
  revizyon artefaktı depoda yoktur** — elimizdeki tek kaynak DDR dönemi belgesidir. Bu kalem FDA
  ölçümleriyle kapanmaz; Bölüm 3.3.1'e DDR ↔ FDR karşılaştırmalı olarak girecektir.

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
Bu kalem **13 Eylül 2026'da da kapanmamıştır** ve nedeni ölçülebilir biçimde bellidir: kamera
(RPi HQ + 6 mm lens) **elde değildir** ve 14 Eylül FDR teslimine yetişmemektedir; 12 Eylül atölye
gününde **A9 (gerçek görüş açısı)** ve **A10 (canlı kare hızı)** adımlarının **ikisi de YAPILMADI**
(D-473). Hedef alanda **kırmızı H'nin bulunduğu teyit edilmiştir** (D-471) — yani sahne artık
"H içermeyen kırsal DJİ çekimi" değildir, ama **tek bir gerçek arena karesi çekilmemiştir**.
**Planlanan ölçüm: 21 Eylül 2026 uçuşu**; saha `p` değeri ilk kez orada ölçülecek, o güne kadar
bu hücreye sayı yazılmayacaktır.

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

**(3) Üçüncüsü: gerçek SiK hattı 13 Eylül 2026'da İLK KEZ niceliksel olarak ölçüldü — ve ölçüm
DÜŞTÜ.** ~~"Gerçek SiK 433 MHz hattı hiç ölçülmemiştir; bugüne kadarki tüm aktarım kanıtı UDP
loopback üzerindedir; iki telsiz henüz kutudan çıkmamıştır."~~ — bu cümlelerin üçü de **artık
yanlıştır** ve ölçümle çürütülmüştür (D-476).

**ÖLÇÜM (13 Eylül 2026, 01:24 ve 01:25; iki SiK telsiz, antenli ve dik, aralarında 2–5 m; taşıyıcı
seri, COM7, 57 600 baud; `scripts/sik_rf_olc.py`, her kolda n = 200 prob):**

| kol (tekrar kadansı) | RTT p50 | **RTT p95** | min / maks | kayıp | veri hızı | hüküm |
|---|---|---|---|---|---|---|
| IKA_GO (0,25 s) | 208,3 ms | **265,2 ms** | 93,1 / 273,3 ms | **%0** (200/200 ACK) | 318,8 B/s | **DÜŞTÜ** |
| PARAŞÜT (0,20 s) | 229,2 ms | **229,6 ms** | 199,1 / 230,8 ms | **%0** (200/200 ACK) | 350,5 B/s | **DÜŞTÜ** |

Ham çıktı: `results/atolye_20260912/A6_sik_ikago.json` · `A6_sik_parasut.json` (her ikisinin
`verdikt` alanı *"UYARI: RTT p95 tekrar aralığını aşıyor"*, `cikis_kodu` **1**). Toplam **400/400
ACK, kayıp %0**; hat doluluğu **%4,4**.

⚠ **EŞİK GEVŞETİLMEMİŞTİR ve iki eşik birden yazılır:** ön kayıtlı kabul eşiği
**p95 < 0,20 s**'dir (`FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` §6.5.1, A2 satırı); ölçüm
harness'i ayrıca her kolun **kendi tekrar aralığını** (IKA_GO 0,25 s, PARAŞÜT 0,20 s) ikinci bir
eşik olarak raporlar. Ölçülen p95 değerleri (265,2 ms ve 229,6 ms) **her iki eşiği de aşmaktadır**
→ sonuç **DÜŞTÜ**. Sözleşme sabitleri `IKA_GO_TEKRAR_ARALIGI_S = 0,25` ve
`PARASUT_TEKRAR_ARALIGI_S = 0,20` **aynen durmaktadır**.

**TEŞHİS (ölçümden çıkarılan):** darbogaz **bant genişliği değildir** — kayıp %0 ve doluluk %4,4.
Darbogaz **SiK TDM dilim gecikmesidir**: 0,20 s kadansında RTT çakılı sabit çıkıyor (p95 − p50 =
**0,4 ms**), 0,25 s kadansında testere dişi (her probta −21 ms, sonra +90 ms sararak); seri payı
~28 ms. **Düzeltme sırası:** T263 Air Speed yükselt → T264 ECC kapat → yetmezse T265 tasarım
değişikliği.

⚠ **Ölçülmeyen ne kaldı:** ölçüm **2–5 m tezgâh mesafesindedir**; detay tasarım raporundaki
**">%98 teslim, 300 m"** iddiasına **kanıt değildir**. **Menzil (A7) hâlâ ÖLÇÜLEMEDİ**, planlanan
ölçüm 21 Eylül 2026.

✅ **Kazanç:** yönerge `Y-3.3.4-M03`'ün istediği "kullanılan veri hızı" artık **gerçek RF üzerinde
ölçülmüştür**: **318,8–350,5 B/s**. Önceki 322,5 B/s **radyosuz köprü** ölçümüydü; ikisi %1–9
içinde örtüşüyor, yani köprü ölçümü gerçeğe yakın çıktı.

⚠ **Bu ölçüm, daha önce bu raporda duran "RTT ≈ 112–157 ms (HESAP)" sayısını da çürütmüştür:**
hesap **SiK TDM çerçeve payını hariç tutuyordu** ve darbogazın tam da o olduğu ölçüldü. HESAP
kaldırılmadı, üstü çizilerek ölçülen değerle değiştirildi.

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

- **KAPANDI (çizim depodadır) — 13 Eylül 2026 düzeltmesi.** İHA ve İKA için renk kodlu (PWM /
  UART / I2C ve güç hatları ayrılmış) **bağlantı şemaları** — yönerge `Y-3.3.1-M01` bunları zorunlu
  kılıyor. **"Bugün metin var, çizim yok" ifadesi bayattır:** çizimler depodadır —
  `FDR/sekiller/iha_baglanti.svg` (7 Eylül 2026) ve `FDR/sekiller/ika_baglanti.svg` (10 Eylül 2026);
  üreteçleri `scripts/fdr_iha_baglanti_svg.py` ve `scripts/fdr_ika_baglanti_svg.py`; hat başına
  kaynak listeleri `FDR/sekiller/iha_baglanti_kaynaklar.md` ve `ika_baglanti_kaynaklar.md`;
  bayatlama kapısı `tests/test_gece_baglanti_semasi.py`. Çizimin kuralı da kayıtlıdır ve rapora
  aynen girer: **kaynaksız hat çizilmez** — düz çizgi bir D-kaydındaki saha ölçümü ya da kart
  dökümü, kesik çizgi `DOĞRULANACAK` (yalnız plandan bilinen, sahada ölçülmemiş hat).
  ⚠ **Kalan iş ölçüm değil yeniden üretimdir:** iki SVG 6 Eylül dökümüne
  (`config/pixhawk/arducopter_fda_20260906.param`) dayanıyor; **PM06** ve **3S 6000 mAh**
  düzeltmeleriyle 12 Eylül dökümünden (`config/pixhawk/emir.param`) yeniden üretilecek ve kalem
  tamamen kapanacaktır — planlanan tarih **14 Eylül 2026**, koşum tek komut (üreteç betikleri +
  kapı testi).

### Y-1-M07 — Üretim yöntemleri, malzemeler, montaj süreçleri ve saha kurulum prosedürleri

**Üretim (FDA aracı).** Gövde **eklemeli imalatla (3B baskı)** üretilmiştir.
- **KISMEN KAPANDI — reçeteler dilimleyici proje dosyalarından OKUNDU (13 Eylül 2026); açık kalan
  yalnız GEREKÇEDİR.** Baskı reçetesi (malzeme, katman yüksekliği, dolgu oranı, duvar sayısı) ve
  kolların hangi reçeteyle basıldığı — yönerge Bölüm 5 değişikliklerin **gerekçelendirilmesini** ister.

Kaynak: `dronesolid/files (3)/*.3mf` → `Metadata/project_settings.config` (Bambu Studio 02.07.01.62).
Kanıt sınıfı: **ÖLÇÜLDÜ (dosya içeriği)** — dosyanın taşıdığı reçete budur; parçanın **fiilen** bu
reçeteyle basıldığı ayrıca basan kişinin beyanıdır.

| plaka | malzeme | katman | dolgu | duvar | üst/alt kabuk | destek | yazıcı |
|---|---|---|---|---|---|---|---|
| Kol 1–2 | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | Bambu X1C 0,4 |
| **Kol 3–4** | ABS | **0,16 mm** | **%40 gyroid** | **6** | **7 / 7** | yok | (yazıcı alanı boş — dilimlenmemiş) |
| Alt çerçeve | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | Bambu X1C 0,4 |
| Üst çerçeve | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | Bambu X1C 0,4 |
| Kubbe | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | Bambu X1C 0,4 |
| Ayak | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | Bambu P2S 0,4 |
| GPS tutucu | ABS | 0,20 mm | %15 grid | 2 | 5 / 3 | **var** | Bambu P2S 0,4 |
| Taban pedi ×4 | **TPU 95A** (`Bambu TPU 95A @BBL P2S`) | 0,20 mm | %15 grid | 2 | 5 / 3 | yok | Bambu P2S 0,4 |

**Reçete farkı artık sayıyla bellidir:** kol 3–4, kol 1–2'ye göre **daha ince katman (0,16 vs
0,20 mm), 2,7 kat dolgu (%40 vs %15), 3 kat duvar (6 vs 2)** ve grid yerine **gyroid** dolguyla
tanımlanmıştır — yani belirgin biçimde **daha güçlü** bir reçete. ⚠ **Açık kalan tek şey bu farkın
GEREKÇESİDİR** (`FDR/YONERGE_HARITASI.md` `Y-5-M05` altında 🔴 RİSK): iki kol neden farklı basıldı,
hangi reçeteli kol araçta hangi konumda duruyor ve 6 Eylül'deki üç devrilmede hasar gören **M1 kolu**
(D-429) hangi reçeteydi. Bunu yalnız basan kişi beyan edebilir — planlanan beyan: **14 Eylül 2026**.
- **KISMEN HESAPLANDI (dilimleyici çıktısı) + AÇIK (iş gücü, insan beyanı).** Parça başına üretim
  süresi, iş gücü ihtiyacı ve toplam imalat süresi.
  **Depoda gerçek dilimleyici çıktısı olan tek plaka vardır ve sayısı buraya yazılır:**
  `dronesolid/files (3)/Plaka4_Ust_Cerceve_plate_1.gcode.3mf` → `Metadata/slice_info.config`
  `prediction=5416` s, `weight=55.86` g, `used_m=22.33` → **üst çerçeve: 1 sa 30 dk 16 sn · 55,86 g
  ABS · 22,33 m filament · 0,4 mm nozul · Bambu X1C**. Kanıt sınıfı **HESAP (dilimleyici tahmini,
  ölçüm değil)** — gerçek baskı süresi kronometreyle ölçülmedi.
  **Kalan yedi plakanın süresi HESAPLANMADI:** proje dosyaları depodadır (`Plaka1_Kol_1-2`,
  `Plaka2_Kol_3-4`, `Plaka3_Alt_Cerceve`, `Plaka5_Kubbe`, `Plaka_Ayak`, `Plaka_GPS_Holder`,
  `tpu_taban_pedi_x4`) ama **sekiz proje `.3mf` dosyasının hiçbiri** `slice_info.config` içinde
  `prediction`/`weight` alanı **taşımaz** (yalnız başlık) — yani G-kod çıktısı üretilmemiştir; sayı
  yalnız `_plate_1.gcode.3mf` uzantılı tek dosyadan gelmektedir. **Bu yüzden toplam imalat süresi
  bugün yazılmaz: sekiz plakanın yedisinin süresi ve ağırlığı yoktur.** Kapatma yolu insan beyanı
  değil **tek oturumluk bir koşumdur** — sekiz plaka Bambu Studio'da kendi reçeteleriyle dilimlenir
  ve `prediction` + `weight` alanları tabloya geçirilir; planlanan tarih **14 Eylül 2026**.
  **İş gücü ihtiyacı** (kişi-saat: kurulum, destek temizliği, montaj) dilimleyiciden türetilemez ve
  yalnız insan beyanıyla kapanır — planlanan beyan: **14 Eylül 2026**.

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

- **AÇIK — İNSAN BEYANI BEKLİYOR; planlanan beyan: 14 Eylül 2026.** Yapısal malzeme listesi,
  bağlantı elemanları ve yapıştırıcı tablosu, tedarikçi ve teslim süreleri (yönerge `Y-3.2.1-T07`,
  `Y-3.2.1-T08`).
  **Net hüküm (13 Eylül 2026):** depoda **vida / somun / pul tablosu, yapıştırıcı kaydı ya da
  tedarikçi-teslim süresi kaydı yoktur**; 12 Eylül atölye günü de bunu üretmedi (koşulan adımların
  hiçbiri envanter değildir — D-473). Türetilebilen tek başlık **gövde malzemesidir** ve o ölçüldü:
  dilimleyici proje dosyalarına göre gövde **ABS**, taban pedleri **TPU 95A**
  (`dronesolid/files (3)/*.3mf`, `Metadata/project_settings.config`). Bağlantı elemanları ve
  yapıştırıcı yalnız **fiziksel envanter çıkarımıyla** (insan) kapanır: araç sökülmeden, takılı
  vidalar ölçülerek listelenir.

### Y-1-M08 — Teknik riskler, önleyici tedbirler, risk azaltma stratejileri ve acil durum senaryoları

**Tasarımın taşıyıcı risk stratejisi fail-closed'dır.** Belirsizlik hâlinde sistem
susmaz, **`NO_ROUTE` der ve sebebini yazar** (§Y-1-M01). Şartname yanlış güzergâha
0 puan verdiği için asimetri bilinçlidir.

**Uçuş emniyeti — uçuş kontrolcüsü tarafında kilitli acil durum tepkileri.**
⚠ **13 Eylül 2026 düzeltmesi:** aşağıdaki tablo artık **şablonu değil gerçek kart dökümünü**
gösterir — `config/pixhawk/emir.param`, Pixhawk 6C'den **12 Eylül 2026 23:55**'te alınmış 1025
satırlık tam döküm. Şablon (`config/pixhawk/arducopter_fda.param`, satır satır gerekçeli,
`tests/test_faz_b_pixhawk_sablon.py` ile kilitli) ile kart **dört başlıkta ayrışmaktadır** ve bu
rapor **kartı esas alır**; şablon ↔ kart farkının tam dökümü Bölüm 3'e girer. Kartla **uyuşan**
satırlar: `FENCE_*` (`emir.param:358–365`) ve `RTL_ALT,3500` (`:780`).

| senaryo | parametre | tepki |
|---|---|---|
| Kumanda sinyali kaybı | `FS_THR_ENABLE,3` · `FS_THR_VALUE,975` (kart: `emir.param:411`, `:412`) | **LAND** (bulunduğu yere in) — ~~RTL~~; **A1 12 Eyl GEÇTİ** (BEYAN) |
| YKS heartbeat kaybı | `FS_GCS_ENABLE,5` · `FS_GCS_TIMEOUT,5` (kart: `emir.param:408`, `:409`) | **LAND** — ~~RTL~~; 5 = "Enabled always Land", `FS_THR_ENABLE,3` ile **tutarlı**. A2 12 Eyl **KISMİ** (test sırasında geçici 0 yapılmıştı; 12 Eyl 23:55 dökümünde **5** okunuyor → geri alma yapılmış, D-474 §2). ✅ **Karar verildi ve kayda geçti (D-474 §2): 5 (Land) sabittir, geri alma gerekmez** — D-406 C'nin "1 kalır" hükmü ArduCopter 4.5.7 seçenek listesi genişlediği için güncellendi. D-473'ün "`FS_GCS_ENABLE=0` kartta duruyor" açık riski 12 Eylül 23:55 dökümüyle **KAPANMIŞTIR** (kart 5 okuyor; 6 Eylül dökümünde 1 idi) |
| Düşük pil | `BATT_LOW_VOLT,10` (3S × 3,33 V) + `BATT_FS_LOW_ACT,1` (kart: `emir.param:138`, `:134`) | **LAND** — ~~RTL~~; 14,4 V değeri **4S varsayımının kalıntısıydı**, pil 3S 6000 mAh (BEYAN). **A3 12 Eyl GEÇTİ** (BEYAN) |
| Kritik pil | `BATT_CRT_VOLT,9` (3S × 3,00 V) + `BATT_FS_CRT_ACT,1` (kart: `emir.param:131`, `:133`) | **LAND** (bulunduğu yere in) — eylem doğruydu, **gerilim 14,0 → 9** düzeltildi. 🔴 Açık risk: `BATT_CAPACITY,3300` (`:129`) iken pil **6000 mAh**; `BATT_LOW_MAH`/`BATT_CRT_MAH` = 0 olduğu için failsafe bugün **yalnız gerilimle** çalışıyor, ama kalan-kapasite göstergesi **%45 yanlıştır** (T258). 13 Eylül 2026'da kullanıcı `BATT_CAPACITY,6000` **ve** `BATT_CRT_VOLT,10.5` yazdığını **beyan etti** — yeni döküm alınmadı, doğrulanmadı; ⚠ beyan edilen 10,5 V, kartta duran `BATT_LOW_VOLT,10` V'un **üstündedir** ve bu hâliyle tutarsızdır. Uçuş öncesi yeni dökümle birlikte okunacak |
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
| **PM06** akım sınırı (~~PM02~~ — D-426, GÖZLEM) | sürekli tam gaz yok, `BATT_AMP` ekranda, motor testi kısa. ⚠ `BATT_AMP_PERVLT,36.36` (`emir.param:126`) ve `BATT_VOLT_MULT,18.18` (`:143`) **Pixhawk 6C hwdef VARSAYILANIDIR** (şablonun kendi notu bunları PM02 ölçeği diye kaydeder — `arducopter_fda.param:171`), 6 Eylül dökümünden beri değişmemiştir ve **DOĞRULANMAMIŞTIR**; PM06'ya kanıt değildir. Pens ampermetreyle karşılaştırma (A13) 12 Eylül'de **YAPILMADI**, alet yoktu (D-473). 3S tam gaz akımı **HESAP ≈27 A/motor** — üretici tablosunda yalnız **3S + APC1047 (10×4,7)** satırı vardır (1454 g → 27 A; D-435 ek 2); araçtaki pervane **10×4,5 (1045)**'tir ve üreticide 1045 satırı **YOKTUR**, yani 27 A en yakın pervaneden bir **yaklaştırmadır**. Motor sınırı 38 A / 30 s; planlanan ölçüm **A13, 21 Eylül 2026** |

**Ölçülmüş, kapanmamış teknik risk:** modelin sahne bağıntılı **51 saniyelik kör
aralığı** (§Y-1-M05(1)). Bugünkü azaltma tedbiri gizlemek değil **göstermektir**:
heartbeat `karar_yas` taşır, hakem tespitin yaşını ekranda görür, bayat tespit
canlı sayılmaz.

- **KISMEN ÖLÇÜLDÜ — 12 Eylül 2026 atölye günü; "gerçek uçuşta tetiklenip ölçülmemiştir" ifadesi
  bayattır.** Yukarıdaki tepkilerin **dördü gerçek donanımda tetiklendi ve GEÇTİ**, biri **KISMİ**
  kaldı, biri hiç sınanmadı. Kanıt sınıfı **BEYAN** (kullanıcı beyanı; ham `.bin` / ekran dökümü yok,
  D-473):
  **A1** kumanda sinyali kaybı (RC failsafe) **GEÇTİ** · **A3** pil failsafe **GEÇTİ** ·
  **A4** anahtarla LAND **GEÇTİ** (`RC6_OPTION,153`, `emir.param:735`) · **A5** gerçek SiK hattında
  bağlantı kaybı **GEÇTİ** · **A2** YKS heartbeat failsafe **KISMİ** (tetikleme çalıştı; Mission
  Planner bağlantısı olmadığı için kodla uçurulamadı) · **coğrafi çit (FENCE) sahada hiç sınanmadı.**
  Ayrıca **A12**: **GUIDED** kipinde, kodla, 3 m'de 15 s askı ve ardından **kodla LAND** (kumanda
  müdahalesiz) — çok başarılı.
  ⚠ **Kanıt sınıfı düzeltmesi:** A12'nin `.bin` logu SD karttan **silinmiştir**; bağımsız tek iz
  parametre dökümüdür: `config/pixhawk/emir.param:980` `STAT_FLTTIME,273` (6 Eylül dökümünde **0**
  idi) ve `:979` `STAT_BOOTCNT` 48 → 96. **Ama bu sayı A12'yi doğrulamaz:** `STAT_FLTTIME`
  **kümülatiftir** — iki döküm arasındaki **48 açılış** boyunca biriken toplam uçuş/silahlı süredir,
  **tek bir uçuşun süresi değildir**; beyan edilen ~15 s askının dışında kalan **258 s
  açıklanmamıştır**. Kanıtladığı tek şey: 6 Eylül'den sonra kartta uçuş süresi **birikmiştir**
  (D-474 §1). Yani A12 **parametre dökümüyle desteklenen, ama doğrulanmamış bir beyandır**.
  **Kalan borç (yönerge `Y-4-M12`):** FENCE tepkisinin sahada tetiklenmesi ve dört GEÇTİ'nin **ham
  kanıtla** (tlog / ekran dökümü) belgelenmesi — planlanan ölçüm **21 Eylül 2026** uçuşu (T257).

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
- **AÇIK — İNSAN BEYANI BEKLİYOR; planlanan beyan: 14 Eylül 2026 (FDR teslimi).** Uçuş günü için
  R2 ve R5'ten birine ikinci kişi atanması; sekiz rolün üyelere ataması; şartname §4 kontenjan
  (6–10 kişi) teyidi.
  **Net hüküm (13 Eylül 2026):** depoda **üye ↔ rol eşlemesi yoktur** ve kaç kişi olduğumuz yazılı
  değildir. 12 Eylül atölye günü rolleri fiilen kullandı (kumandayı tutan, kartı süren, sonucu
  yazan) ama tutanağa **isim/rol eşlemesi kaydedilmedi** (D-473). R2/R5 eşzamanlılığı ölçülmüş bir
  organizasyon riskidir ve **ikinci kişi ataması 13 Eylül itibariyle yapılmamıştır** — bu, 21 Eylül
  uçuşu için açık bir operasyon riskidir. Yazılım tarafından türetilebilecek hiçbir sayı yoktur;
  kalem yalnız insan beyanıyla kapanır.

**Kurulum süreçleri ve takvim.** Kalan işler **donanım ve insan** işleridir ve
takvimlidir ve **gerçekleşen / planlanan ayrımıyla** yazılır (13 Eylül 2026 durumu):
**Gerçekleşen —** 5 Eylül montaj ve kablolama günü (kutu ilk kez açıldı; Jetson **Orin Nano
Developer Kit 4 GB**, ESC **Skywalker 60A V2**, **PM06** — D-426 / D-431) · 6 Eylül ilk
pervaneli denemeler: **üç devrilme**; tlog'a göre uçuş kontrolcüsü doğru çalıştı, **ön itki
yetmedi**, **M1 motoru hasar gördü** (D-429) · 6 Eylül Jetson yığını kartta kuruldu, genel kapı
15/15 · 15/15 ve FPS kapısı **GEÇTİ** (D-431) · **12 Eylül atölye günü:** A1/A3/A4/A5 **GEÇTİ**,
A2 **KISMİ**, **A12 askı ÇOK BAŞARILI** (GUIDED, 3 m, 15 s, kodla LAND) — kanıt sınıfı BEYAN ·
12 Eylül İKA iz genişliği **459,5 mm ÖLÇÜLDÜ** (D-472) · **13 Eylül: gerçek SiK hattı ilk kez
ölçüldü ve DÜŞTÜ** (RTT p95 265,2 / 229,6 ms, kayıp %0 — D-476).
**Planlanan (D-471, kullanıcı kararı 12 Eylül — önceki takvim GEÇERSİZ):** **13 Eylül sürüm mührü**
(17 Eylül'den öne çekildi, T246) · **14 Eylül 2026 FDR teslimi** (21 Eylül değil) · **21 Eylül 2026
uçuş — kesin tarih** · 30 Eylül – 3 Ekim resmî görev test uçuşu penceresi (şartname).
**Uçuş öncesi kapanması zorunlu kalemler:** M1 motorunun değişimi, `BATT_CAPACITY` 3300 → 6000 ve
`BATT_CRT_VOLT` tutarlılığının **kart dökümüyle doğrulanması** (T258), AltHold'da 30 s askı ile
`MOT_THST_HOVER` öğrenmesi (T261), FENCE tepkisinin sahada tetiklenmesi, SiK RTT'nin eşiğe
çekilmesi (T263 Air Speed → T264 ECC → T265). Üç "ilk kez ölçülecek" kalemin **ikisi kapandı, biri açık kaldı** — cümle bugün üçe bölünür:
**(a) Görev bilgisayarında kare hızı ÖLÇÜLDÜ** (6 Eylül 2026, Jetson Orin Nano Developer Kit 4 GB,
120 örnek): pt **p50 1,35 / p95 1,06 FPS**, TensorRT engine **1,58 / 1,33 FPS**; eşik 0,61 FPS →
**GEÇTİ** (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`, `scripts/jetson_fps.py`,
D-431; `torch.cuda.is_available()` **True**, `cuda_adi: Orin`).
**(b) Kamera gerçek görüş açısı ÖLÇÜLEMEDİ** — kamera 13 Eylül itibariyle elde değildir, A9 adımı
12 Eylül'de yapılamadı. Bugünkü değer **HESAP**'tır: **FOV_yatay = 55,3°** — IMX477 etkin sensör
genişliği 6,287 mm (raspberrypi.com kamera belgesi), lens 6 mm → 2 · atan(6,287 / 12)
(`ATOLYE_TEST_GUNU_20260912.md:154`); sensör kipi kırparsa **daha dar** çıkar. Planlanan ölçüm:
**A9, 21 Eylül 2026**.
**(c) Gerçek telsiz gidiş-dönüş süresi ÖLÇÜLDÜ — ve DÜŞTÜ** (13 Eylül 2026, iki SiK telsiz, 2–5 m,
COM7 / 57 600 baud, `scripts/sik_rf_olc.py`, n = 200 + 200): **RTT p95 265,2 ms** (IKA_GO kadansı
0,25 s) ve **229,6 ms** (paraşüt kadansı 0,20 s); **kayıp %0** (400/400 ACK); veri hızı
318,8–350,5 B/s. Ön kayıtlı eşik **p95 < 0,20 s** (§6.5.1 A2) ve kolun kendi tekrar aralığı —
**ikisi de aşıldı** → **DÜŞTÜ** (`results/atolye_20260912/A6_sik_ikago.json`, `A6_sik_parasut.json`;
D-476). Eşik **gevşetilmedi**; düzeltme sırası T263 → T264 → T265. Daha önce bu satırda duran
~~RTT ≈ 112–157 ms (HESAP)~~ ölçümle çürütülmüştür (hesap SiK TDM çerçeve payını hariç tutuyordu).
**Menzil (A7) hâlâ ÖLÇÜLEMEDİ.**
Bu rapor üçünü de bugün ölçülmüş gibi göstermez: (a) ve (c) **ÖLÇÜM**dür — (c) geçmedi ve öyle
yazıldı —, (b) **HESAP** etiketiyle durur.

### Y-1-M10 — Görev gereksinimlerini karşılama düzeyi analizi, tasarım doğrulama süreci özeti ve teknik olgunluk kanıtı

#### Ölçülmüş başlıca sonuçlar

| ne | ölçülen | çerçeve |
|---|---|---|
| Genel kapı (`test_rota_sentetik.py`) — iki kol | **15/15** tanısal · **15/15** üretim rotası · **15/15** yayınlanan şerit | 15 belirlenimci arena sahnesi, 3 Eylül 2026 |
| Tam test süiti | ~~1896 test OK (3 atlandı, 390,5 s)~~ → **13 Eylül 2026'da yeniden koşuldu: 2925 test · 603,2 s · 20 BAŞARISIZ · 12 atlandı → SÜİT YEŞİL DEĞİL** (ham çıktı `results/tam_suit_20260913/tam_suit.txt:583`; düşen 20 testin kök nedeni ve tam dökümü aşağıdaki uyarı kutusunda) | 13 Eylül 2026, `-m unittest discover -s tests -q` |
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
| Donanım künyesi (quadcopter, Pixhawk 6C, ~~Jetson Nano 4GB~~, RPi HQ, 4S 10 Ah, 2× SiK) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | kullanıcı beyanı; ~~**5 Eylül'de kutu açılarak teyit edilecek**~~ → 5–6 Eylül'de kutu açıldı: Jetson **Orin Nano Developer Kit 4 GB** (beyan yanlışlandı, D-431), ESC Skywalker 60A V2, PM06 (D-426) | 2026-09-03 (beyan) → 2026-09-06 (ölçüm) |
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
- **BEYAN GEREKLİ (insan):** Gerçek ~~SiK 433 MHz~~ RFD900A 915–928 MHz hattında gidiş-dönüş süresi ve paket kayıp oranı.
- **DOĞRULANACAK:** Bu özetin sayıları rapor teslim edilmeden önce, teslim günündeki kapı koşusuyla **yeniden üretilmelidir**; bayat sayı taşımak bu projede birden çok kez kusur olarak kayda geçti.
- **DOĞRULANACAK:** Tam test süiti (3 Eylül: 1896 test OK) teslimden önce yeniden koşulacaktır; test dosyası sayısı 155 → 169 değiştiği için 1896 sayısı bugün bayattır.
- **DOĞRULANACAK:** Bu bölüm, Bölüm 2–7 kesinleştikten sonra **yeniden üretilecektir** (bölüm başındaki üretim sırası uyarısı).
