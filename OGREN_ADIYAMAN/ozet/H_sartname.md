# H — Şartname Olgusal Özeti (Jüri Hazırlığı, Yazılımcı Takım Üyesi İçin)

**Kaynaklar (depo kökü `/home/n4vitas/proje/navitas_tam/navitas/`):**

| Kısaltma | Dosya | Sayfa | Sürüm |
|---|---|---|---|
| **ŞART** | `Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf` | 30 (kapak + 1–28 + arka kapak) | V2, 13.04.2026 (V1: 02.03.2026) — ŞART s.4 |
| **FDR-Y** | `FDR_2_qNiVF.pdf` — Final Değerlendirme Raporu Hazırlama Yönergesi | 19 | V1, 15.06.2026 — FDR-Y s.4 |
| **DDR-Y** | `DDR_Sablon_TR_BhrGu.pdf` — Detay Değerlendirme Raporu Hazırlama Yönergesi | 17 | V1, 14.05.2026 — DDR-Y s.4 |
| **TYDA** | `2026_TEKNOFEST_TYDA_SARTNAME_Ucuncu_Senaryo_TR_2_NoDue.pdf` | 19 | sürüm tablosu yok |

Sayfa numaraları PDF'in kendi basılı numarasıdır (ŞART'ta kapak numarasızdır; "s.9" = basılı 9). Madde numaraları ŞART'ın başlık numaralarıdır. PDF'de olmayan hiçbir bilgi yazılmamıştır; belirsiz noktalar **"PDF'de bulunamadı"** olarak işaretlenmiştir.

> ⚠ **Önemli tespit (Bölüm 6'da ayrıntı):** "Üçüncü senaryo" dosyası (TYDA) **bu yarışmaya ait değildir**. Kapağı "Yapay Zekâ Dil Ajanları Yarışması Teknik Şartnamesi (3. Senaryo)"dır; Bilişim Vadisi yürütücülüğünde video analiz/LLM yarışmasıdır (TYDA s.2). İHA/İKA yarışmasının "Senaryo 3"ü ise ŞART s.24'teki K_zorluk = 2.0 (Zor güzergâh) senaryosudur.

---

## 1. Yarışma, amaç ve görev senaryosu

### 1.1 Ad, düzenleyici, kategori
- **Ad:** İleri Otonom Sistemler Tasarım ve Operasyon Yarışması, TEKNOFEST 2026 (ŞART kapak, s.7 §1).
- **Düzenleyen:** Türk Havacılık ve Uzay Sanayii (TUSAŞ); teknik kurallar ve değerlendirme TUSAŞ mühendislerinden oluşan **Danışma ve Değerlendirme Kurulu (DDK)** tarafından yürütülür (ŞART s.7 §1).
- **Hedef kitle:** ön lisans, lisans ve lisansüstü öğrencileri (ŞART s.7 §1; s.11 §4).
- **Amaç (tanım):** afet sonrası senaryoyu simüle eden ortamda İHA ve İKA'nın **koordineli** çalışarak lojistik/ulaşım problemini **otonom** çözmesi (ŞART s.7 §2).
- **Platform zorunluluğu:** hava aracı **sabit kanatlı** olmak zorundadır (ŞART s.19 §6, 1. madde). "Sistem" ifadesi İHA + İKA + fırlatma (mancınık) platformlarını bütünleşik kapsar (ŞART s.19 §6, 2. madde).

### 1.2 Alan ölçüleri (ŞART s.7–8 §2.1)
| Bölge | Kısaltma | Ölçü / Tanım |
|---|---|---|
| Hedef Tespit Alan Bölgesi | HTAB | **50 m × 50 m**; içinde afet bölgesini simüle eden moloz yığınları ve engeller |
| İHA Fırlatma Bölgesi | İHA-FB | Mancınık kurulacak ve kalkış yapılacak alan (ölçü verilmemiş) |
| İHA Uçuş Bölgesi | İHA-UB | **300 m × 300 m** — İHA'nın uçabileceği maksimum bölge |
| İKA Konumlanma Bölgesi | İKA-KB | **1 m × 1 m** — kara aracının başlangıç pozisyonu |
| Hedef Bölge | HB | **2 m × 2 m**, üzerinde **kırmızı H** harfi; İKA'nın varış noktası |
| İHA İniş Bölgesi | İHA-İB | **30 m × 30 m mavi** bölge; paraşütle iniş alanı |
| Güzergâhlar | — | HTAB içinde İKA-KB ile HB arasında moloz arasında **3 farklı yol**; yarışma günü yalnız **1'i açık**, diğer 2'si fiziki engelle kapalı; hangisinin açık olduğu **gizli** |

- Şekil 1 (ŞART s.8) alan görselidir; altyazı görselin tamamen yapay zekâ ile üretildiğini ve gerçek alanı yansıtmadığını belirtir.
- Operasyonel uçuş alanı boyutları ve saha konfigürasyonu, yarışma yerleşkesi belirlendikten sonra resmi kanallarla duyurulacaktır (ŞART s.19 §6).
- Güzergâhlar "Kolay", "Orta", "Zor" olmak üzere üç zorluk kategorisindedir; her biri farklı zorluk katsayısına sahiptir (ŞART s.19–20 §6).

### 1.3 Görev akışı — adım adım (ŞART s.8–10 §2.2)
Görevin başarılı sayılması için adımlar **sırasıyla** ve kurallara uygun icra edilmelidir (ŞART s.8 §2.2).

**2.2.1 Kalkış (s.8–9)**
- Sistemler görev sahasına **mühürlü kutularda** getirilir; kurulum süresi mühürlerin hakem nezaretinde açılmasıyla başlar.
- İHA, İHA-FB içinden **yalnızca mancınık** ile fırlatılır. Elden atış, pistten koşarak kalkış ve dikey kalkış **yasaktır**.

**2.2.2 Keşif ve Rota Tespiti (s.9)**
- Fırlatma sonrası İHA **tam otonom** moda geçer, İHA-UB içinde uçar.
- Üzerindeki algılayıcılar ve görüntü işleme algoritmalarıyla HTAB içindeki **açık güzergâhı** tespit eder.

**2.2.3 Veri Aktarımı (s.9)**
- İHA, tespit ettiği güzergâh bilgisini kablosuz haberleşme ile **yer istasyonuna ve İKA'ya** aktarır.
- Yer istasyonundaki **alan hakemi**, güzergâh bilgisinin canlı olarak tespit edildiğini ve İKA'ya aktarıldığını **onaylar**.
- Aktarım **İHA havadayken** tamamlanmalıdır.

**2.2.4 İniş (s.9)**
- Aktarım sonrası İHA, İHA-İB içine iniş prosedürünü başlatır; iniş **paraşüt sistemiyle** zorunludur.
- Paraşüt açma komutu otonom verilebilir; emniyet için yer istasyonundan **manuel tetikleme** de mümkündür; manuel tetiklenirse **ceza puanı** uygulanır (ceza: −50, ŞART s.26 Tablo 6).

**2.2.5 Kara Harekâtı (s.9)**
- İKA, İHA'nın **inişini tamamlamasını beklemek zorundadır**; İHA yere temas etmeden İKA hareket edemez. İHA iniş yapmadan hareket eden takımın görevi başarısızdır.
- İHA inişi tamamlandıktan sonra İKA'nın intikal süreci, yer kontrol istasyonundaki (YKS) görevli takım üyesi tarafından **manuel olarak tetiklenir** (bu tek izinli insan tetiklemesidir).
- İKA, İHA'dan aldığı güzergâh verisiyle **otonom** olarak HB'ye ilerler; otonom hareket etmeyen İKA'nın görevi başarısızdır.

**2.2.6 Görevin Tamamlanması (s.10)**
- İKA'nın **HB sınırları içine girmesi** görevin başarıyla icrası sayılır.
- Belirlenen sürede HB'ye ulaşamayan takımın görevi başarısızdır.
- İKA "teknik gereksinimler listesinde" tanımlı **yükleri** taşıyarak hedefe gitmelidir; hedefte yapısal bütünlüğünü korumalı ve yükü **eksiksiz** muhafaza etmelidir; aksi hâlde görev başarısızdır. **Not:** atıf yapılan "teknik gereksinimler listesi" bu PDF'lerin içinde yoktur → yük miktarı/tanımı **PDF'de bulunamadı**.

### 1.4 Süre sınırları
| Süre | Değer | Başlangıç / bitiş | Kaynak |
|---|---|---|---|
| Hazırlık süresi | **15 dk (900 s)** | Alan hakeminin giriş onayıyla başlar; kaptanın "Takım Hazır" komutuyla durur | ŞART s.22 §6.2; s.25 Tablo 6 |
| İHA görev (uçuş) süresi | **15 dk (900 s) maks.** | Mancınıktan ayrılma → güzergâh tespiti, veri aktarımı ve paraşütle inişin tamamlanması | ŞART s.22 §6.2; s.23 §6.4; s.25 |
| İKA görev süresi | **10 dk (600 s) maks.** | Tekerlerin dönmesiyle başlar, brandaya fiziksel temasla biter | ŞART s.22–23 §6.2; s.25 Tablo 6 |
| Tekrar fırlatma | Süre durdurulmaz; 15 dk'ya dahildir | — | ŞART s.22 §6.2 |
| Hazırlık sonrası müdahale | Geçen süre hazırlık süresine eklenir; toplam süre aşılırsa uçuş hakkı iptal | — | ŞART s.22 §6.2 |
| FDA drone test uçuşu | **10 dk maks.** (kalkış, tespit, aktarım, iniş) | — | ŞART s.18 §5.3.2 |

### 1.5 İrtifa kuralları
- Ana şartnamede İHA için **azami/asgari irtifa sınırı belirtilmemiştir** → **PDF'de bulunamadı**. Tek kısıt yatay: İHA-UB (300×300 m) dışına çıkmak "Alan İhlali"dir ve uçuş başarısız sayılır (ŞART s.22 §6.2; s.23 §6.4).
- **FDA drone test uçuşunda** (ana yarışmadan ayrı, 2026 Eylül–Ekim): drone "Başlangıç Alanı" ile "Hedef Alanı" arasında **asgari 30 m irtifadan** uçmalıdır (ŞART s.17 §5.3.2).

### 1.6 Uçuş hakları ve yarışma günleri (ŞART s.19–20 §6)
- Yarışma **6 gün** sürer; her biri ardışık 2 günden oluşan **3 görev periyodu**.
- Her periyotta 3 güzergâhtan yalnız 1'i açık; hangi periyotta hangi zorluk seviyesinin açılacağı **gizli**.
- Her periyot için **1 uçuş hakkı** → toplamda **3 uçuş hakkı**. Kullanılmayan hak devredilmez, yanar ve o tur için puan **0**'dır.

---

## 2. Puanlama (ŞART s.24–26 §7, Tablo 6) ve `simulation/score.py` karşılaştırması

### 2.1 Formüller (ŞART s.24)
```
Puan1 = 0.1·ÖDR + 0.25·DDR + 0.55·FDA + 0.1·UHDR
Puan2 = K_zorluk · [ P_görev + (25000 − m_İHA)/10 + (900 − t_İHA)/5 + (900 − t_hazırlık)/30
                     + (10000 − m_İKA)/15 + (m_yük · 0.01) + (600 − t_İKA)/15 − C_ceza ]
K_zorluk = 1.0 (Senaryo 1) | 1.5 (Senaryo 2) | 2.0 (Senaryo 3)
P     = P_TI + P_uçuş + P_centilmenlik
Puan  = 0.65·Puan2 + 0.20·P + 0.15·Puan1
```

### 2.2 Puan kalemleri (ŞART s.24–26 Tablo 6)
| Sembol | Kalem | Puan / koşul |
|---|---|---|
| **P_görev** | Görev başarısı | İKA hedef brandaya (H noktası) **fiziksel temas** ederse **600**, ulaşamazsa **0** |
| **m_İHA** | İHA hafiflik | 25000 g sınırının altındaki **her 10 g için 1 puan** |
| **t_İHA** | İHA görev süresi | 900 s'den tasarruf edilen **her 5 s için 1 puan**; mancınıktan fırlatma → paraşütle iniş |
| **t_hazırlık** | Hazırlık süresi | 900 s'den tasarruf edilen **her 30 s için 1 puan**; hakem işaretiyle başlar, "hazır" işaretiyle (Hands-Off) biter; sonra müdahale = ceza + süre eklenir |
| **m_İKA** | İKA hafiflik | 10000 g sınırının altındaki **her 15 g için 1 puan** |
| **m_yük** | İKA yük | Taşınan toplam yükün **her 100 g'ı için 1 puan** |
| **t_İKA** | İKA görev süresi | 600 s'den tasarruf edilen **her 15 s için 1 puan**; tekerler dönmeye başlar → brandaya temas |
| **P_TI** | Teknik muayene | İlk denemede geçerse **100**, ikinci denemede **50**, geçemezse **0** (geçemeyen uçamaz) |
| **P_uçuş** | Uçuş başarısı | Her başarılı senaryo uçuşu için **200**, başarısız **0**. Başarı koşulu: İHA kırıma uğramaması, hedefi tespit edebilmesi, İKA'nın hareket etmesi |
| **P_centilmenlik** | Centilmenlik | Takım çalışması ve centilmenlik; **maks. 50** |
| **C_ceza** | Cezalar | **İniş sapması:** İHA iniş alanı dışına çıkarsa uzaklaşılan **her metre için −5**. **Yeniden başlatma:** hands-off sonrası müdahale **−100**. **Manuel paraşüt tetikleme:** **−50** |
| ÖDR / DDR / FDA / UHDR | Rapor puanları | İlgili rapor değerlendirmesinden alınan puan (100 üzerinden tablolar: s.16 Tablo 2, s.16 Tablo 3, s.17 Tablo 4, s.19 Tablo 5) |
| **FDA** | Final Değerlendirme Aşaması | **FDA = FDR × 0.85 + Drone Görev Test Uçuşu × 0.15** (ŞART s.18 §5.3.2); drone testi **100 veya 0** |

### 2.3 `simulation/score.py` ile karşılaştırma
Dosya: `/home/n4vitas/proje/navitas_tam/navitas/simulation/score.py` (başlık: "Şartname V2 (13.04.2026) formülü").

**Tutarlı olanlar:**
- Puan2'nin 7 terimi ve bölenleri (10, 5, 30, 15, 0.01, 15) ŞART s.24 ile **birebir aynı**.
- Puan1 katsayıları (0.10/0.25/0.55/0.10), P toplamı, genel formül (0.65/0.20/0.15) **aynı**.
- Varsayılanlar P_TI=100, P_uçuş=200, P_centilmenlik=50 (maks.), P_görev=600 Tablo 6 ile uyumlu.
- Cezalar: `sapma_metre × 5` (−5/m) ve `manuel_parasut → +50` Tablo 6 ile uyumlu. Yeniden başlatma cezası (−100) ayrı bayrak olarak modellenmemiş; `C_ceza` alanına elle girilmesi gerekir (kod hatası değil, kullanıcıya not).

**Tutarsızlık / eksik noktalar:**
1. **Geçersiz uçuşta puan hesaplanmaya devam ediyor.** ŞART s.23 §6.4: süre aşımı (t_İHA > 900 s), manuel müdahale, hakem teyidi alınamaması, saha sınır ihlali, kırım, paraşüt açılmaması hâllerinde uçuş "Geçersiz"dir ve **o turdan puan alınamaz**. `score.py` bu durumlarda yalnızca `sorunlar` listesine uyarı ekler; `Puan2` yine hesaplanıp `TOPLAM`'a giriyor. Şartnameye göre Puan2 = 0 olmalıdır (hangi bileşenlerin sıfırlanacağı — P_uçuş dahil — PDF'de ayrıca yazılmıyor, ancak "puan alınamayacaktır" ifadesi mutlaktır).
2. **K_zorluk etiketi bir çıkarımdır.** ŞART s.24 formülde "Senaryo 1/2/3" der; s.19–20'de güzergâhlar "Kolay/Orta/Zor" olarak adlandırılır. "Senaryo 1 = Kolay … Senaryo 3 = Zor" eşleştirmesi PDF'de **açıkça yazılmamıştır**; `score.py` (`1.0=Kolay, 1.5=Orta, 2.0=Zor`) bunu varsayar. Makul ama jüriye "şartnamede böyle yazıyor" denmemeli.
3. **Üç uçuşun birleştirilmesi.** Takımın 3 uçuş hakkı vardır (ŞART s.20). Puan2'nin üç tur üzerinden **toplanacağı mı, en iyisinin mi alınacağı** PDF'de belirtilmiyor → **PDF'de bulunamadı**. `score.py` tek uçuş hesaplar; çok-turlu birleştirme yoktur.
4. **P_uçuş ile P_görev bağlantısı.** `score.py`'de bağımsız girdiler; örnek `basarisiz` senaryosunda P_uçuş=0 verilmiş. Şartname P_uçuş için "İHA kırıma uğramaması, hedefi tespit edebilmesi, İKA'nın hareket etmesi" der (s.25); yani İKA HB'ye ulaşamasa da P_uçuş=200 mümkün görünür. Kod bunu zorlamaz; kullanıcı doğru girmelidir.
5. **Negatif/aşım sınırlaması yok.** m_İHA > 25000 g durumunda kod uyarı verir ama negatif terimi hesaplar. Şartnameye göre 25 kg üstü araç teknik denetimde **değerlendirme dışı** bırakılır (ŞART s.19 §6) — puan hesabına hiç girmez.
6. `gecerlilik_kontrol`'deki "t_hazirlik > 900 → kural ihlali" mesajı ŞART s.22'nin "toplam sürenin aşılması durumunda uçuş hakkı iptal edilir" hükmüyle örtüşür; ancak yine sonuç hesaplanmaya devam eder (madde 1'deki sorun).

---

## 3. Zorunlu güvenlik gereksinimleri ve kısıtlar

| Konu | Kural | Kaynak |
|---|---|---|
| **Paraşüt** | İniş paraşütle **zorunlu**; otonom veya yer istasyonundan manuel tetiklenebilir; manuel = −50 puan; paraşüt açılmayıp sert iniş/kontrolsüz düşüş olursa uçuş **geçersiz** | ŞART s.9 §2.2.4; s.23 §6.4; s.26 Tablo 6 |
| **Mancınık** | Tek izinli kalkış yöntemi; elden atış, pistten koşma, dikey kalkış yasak | ŞART s.9 §2.2.1 |
| **Sabit kanat** | İHA sabit kanatlı olmak zorunda | ŞART s.19 §6 |
| **Ağırlık — İHA** | Operasyonel yükler **dahil** üst limit **25 kg**; üstü teknik denetimde değerlendirme dışı | ŞART s.19 §6 |
| **Ağırlık — İKA** | Operasyonel yükler **hariç** üst limit **10 kg**; üstü değerlendirme dışı | ŞART s.19 §6 |
| **Boyut sınırı** | Araç boyutu için sayısal sınır **PDF'de bulunamadı** (yalnızca alan ölçüleri var) | — |
| **Batarya** | Batarya tipi/gerilim/kapasite sınırı ana şartnamede **PDF'de bulunamadı**. DDR-Y §3.3.4 batarya kapasitesi (mAh) ve C değeri hesabı ister; FDR-Y §3.3.2 ölçülen akımla batarya uyumu kanıtı ister | DDR-Y s.15; FDR-Y s.16 |
| **Haberleşme frekansı** | 433 MHz veya herhangi bir frekans/bant kuralı **PDF'de bulunamadı**. FDR-Y §3.3.4 ve §4 haberleşme paket yapısı, veri hızı, gecikme ve **menzil testi** sonuçlarını ister | FDR-Y s.17 |
| **Failsafe / RTL** | Ana şartnamede "failsafe" veya "RTL" terimi yok. FDR-Y Bölüm 4: "arıza emniyet doğrulaması kapsamında … sistemin verdiği tepkilerin (**eve dönüş, motor kesme** vb.) sahada test edildiğini gösteren veriler" raporda sunulmalıdır. DDR-Y §3.3.1: arıza emniyet senaryolarının mantık şemaları | FDR-Y s.17–18; DDR-Y s.14 |
| **Kill switch** | Terim **PDF'de bulunamadı** (yakın kavram: FDR-Y'deki "motor kesme" tepkisi) | — |
| **Hakem ekranı / YKİ** | Güzergâh tespiti **gerçek zamanlı** Yer Kontrol İstasyonu'na aktarılmalı; Alan Hakemi **monitör üzerinden** izleyip **sözlü** onaylamalı; onaysız tespit geçersiz. Veri akışı sağlanamazsa uçuş geçersiz | ŞART s.9 §2.2.3; s.22 §6.2; s.23 §6.4 |
| **Güvenlik pilotu / manuel müdahale** | Herhangi bir aşamada Güvenlik Pilotu İHA'yı manuel moda alırsa uçuş **başarısız**. Hem İHA hem İKA fırlatma/başlangıçtan bitişe **tam otonom** olmalı (seyrüsefer, tespit, aktarım, sürüş) | ŞART s.23 §6.4; s.23 §6.2 son madde |
| **"Takım Hazır" sonrası müdahale** | Fiziksel müdahale yasak; teknik aksaklıkta kaptan **100 ceza puanı** kabul ederek müdahale edebilir; süre hazırlık süresine eklenir; toplam aşılırsa uçuş hakkı iptal | ŞART s.22 §6.2; s.26 Tablo 6 |
| **Tekrar fırlatma** | Mancınıktan sonra İHA airborne olamayıp yere temas ederse ve Alan Hakemi kaza/kırım/yapısal hasar olmadığını teyit ederse **tekrar fırlatma hakkı**; süre durmaz; yalnızca mancınık kurulumu ve sistemin yeniden başlatılması yapılabilir, tamir/parça değişimi yasak | ŞART s.22 §6.2 |
| **Mühürleme** | Teknik kontrolden "Uçuşa Uygundur" alan sistemlerin kutuları mühürlenir; mühür sonrası modifikasyon/demontaj/parça değişimi yasak; mühür uçuş öncesi hakem nezaretinde açılır | ŞART s.21 §6.1 |
| **Beyan tutarlılığı** | FDS, SGGS ve UHDR'de beyan edilen konfigürasyonla teknik kontrole girilir; dışına çıkmak kural ihlali | ŞART s.20 §6.1 |
| **Hasar sonrası denetim** | Uçuş öncesi/sırasında hasar alan İHA kapsamlı teknik denetime tabi; onay alamayan uçamaz | ŞART s.21 §6.2 |
| **Sahaya giriş** | En fazla **8 takım üyesi**; danışmanlar giremez; alan dışındaki danışmanla iletişim → diskalifiye; baret ve yelek zorunlu | ŞART s.21–22 §6.2 |
| **Hakem yetkisi** | Hakem heyeti risk durumunda operasyonu sonlandırabilir; güvenlik gerekçeli kararlara itiraz yok | ŞART s.21 §6.2 |
| **Geçersiz uçuş hâlleri (6 madde)** | Süre aşımı (15 dk), manuel müdahale, hakem teyidi/veri aktarımı sağlanamaması, saha sınır ihlali (İHA-UB), kırım ve yapısal bütünlük kaybı (pervane kırılması hariç), iniş ihlali (paraşüt açılmaması) | ŞART s.23 §6.4 |
| **Ceza puanları** | −5/m iniş sapması; −100 yeniden başlatma; −50 manuel paraşüt | ŞART s.26 Tablo 6 |

---

## 4. Rapor takvimi ve teslimler

### 4.1 Takvim (ŞART s.10 Tablo 1)
| Aşama | Tarih |
|---|---|
| Son başvuru (www.t3kys.com) | 10 Nisan 2026 |
| ÖDR son teslim | 26.04.2026 – 17:00 |
| ÖDR sonuçları | 04.05.2026 |
| DDR son teslim | 15.07.2026 – 17:00 |
| DDR sonuçları | 29.07.2026 |
| FDR son teslim | 21.09.2026 – 17:00 |
| Final Değerlendirme Aşaması (FDS sunumları + Drone ile Görev Test Uçuşu) | 30.09–03.10.2026 |
| FDR sonuçları ve maddi destek hak kazananların açıklanması | 04.10.2026 |
| SGGS son teslim | 05.02.2027 – 17:00 |
| SGGS sonuçları | 19.02.2027 |
| UHDR son teslim | 16.04.2027 – 17:00 |
| UHDR sonuçları | 30.04.2027 |
| Uçuş testleri | 21.05.2027 |
| Yarışma tarihi/yeri | Ağustos–Eylül 2027 |

Not: "Saha provası" ifadesi PDF'de yok; en yakın karşılık "Uçuş Testleri — 21.05.2027" satırıdır. Ayrı bir "video teslimi" tarihi yoktur; videolar UHDR (s.19) ve FDR-Y (§3.3.3 simülasyon ekran kaydı linki) içinde istenir.

### 4.2 Teslimlerin içeriği ve puan tabloları
- **ÖDR** (ŞART s.15–16 §5.1, Tablo 2, 8 bölüm): Özet 10, Organizasyonel Yapı 5, Proje Takvimi 5, Bütçe Analizi 5, **Kavramsal Tasarım Yaklaşımı 30**, Fayda Analizi 25, Üretim Planı 10, Sistem Entegrasyon ve Test Planı 10.
- **DDR** (ŞART s.16 §5.2, Tablo 3, 5 bölüm): Özet 10, Org. Yapı ve Takvim 10, **Genel Sistem Spesifikasyonları 60**, Test Faaliyetleri 10, Gereksinim İzlenebilirliği 10. Başarılı takımlar maddi destek başvurusu yaptıysa bütçenin **%25**'ini alır.
- **FDR** (ŞART s.17 §5.3.1, Tablo 4; FDR-Y s.7 "Tablo 1" aynı tablo): aşağıda §4.3.
- **Drone ile Görev Test Uçuşu** (ŞART s.17–18 §5.3.2): takımın **kendi özgün donanım ve yazılım mimarisiyle** entegre ettiği **çoklu rotorlu/dikey iniş-kalkış** drone; 20×20 m simüle engel/enkaz alanı; "Başlangıç Alanı"–"Hedef Alanı" arasında "Açık Güzergâh"ı asgari 30 m irtifadan havadan görüntü işleme/yapay zekâ ile tespit; uçuş sırasında YKİ'ye gerçek zamanlı aktarım; hakem doğrulaması; tüm süreç ≤ 10 dk → **100**, aksi hâlde **0**. FDA = FDR×0.85 + Test×0.15. FDA'da başarılı takımlar bütçenin **%75**'ini alır (maddi destek başvurusu zorunlu değil).
- **SGGS** (ŞART s.18 §5.4): BOM esaslı sunum; her parça için üretim yöntemi, süresi, CAD kütlesi ile ölçülen gerçek kütle, fikstür/tool ihtiyacı, üretim zorlukları; hazır alınan alt sistemlerde tedarik durumu, ağırlık ve boyut. Puanlanmaz; **"Başarılı / Başarısız"**.
- **UHDR** (ŞART s.18–19 §5.5, Tablo 5): Özet 5, Proje Takvimi 5, Bütçe Gerçekleme ve Sapma 10, **Genel Sistem Spesifikasyonları 40**, **Uçuş ve Otonom Harekât Videoları 40**. Montajı biten İHA/İKA'nın nihai görselleri, fiziksel özellikleri (boyut, ağırlık), bütçe; FDR takviminden sapmalar gerekçeli; İHA, İKA ve mancınığın otonom başarılı harekât videoları; kullanılacak algoritma ve modeller **nihai hâlleriyle** anlatılmalı.
- Takım üyesi ekleme/çıkarma **FDR son teslim tarihine** kadar (ŞART s.14 §4.3); FDS sonrasında takım listesi kesinleşir (s.12).

### 4.3 FDR Yönergesi (FDR-Y) — bölümler ve puanlar
Tablo (FDR-Y s.7 "Tablo 1" = ŞART s.17 "Tablo 4"): **1 Özet 5 · 2 Org. Yapı ve Takvim 5 · 3 Genel Sistem Spesifikasyonları 40 · 4 Test Faaliyetleri 15 · 5 Üretim Faaliyetleri 15 · 6 Gereksinim İzlenebilirliği ve Değerlendirme 10 · 7 Bütçe Gerçekleme Analizi 10** (toplam 100).

Yazılımcıyı ilgilendiren alt başlıklar:
- **Bölüm 3.3 Aviyonik & Yazılım** (FDR-Y s.15–17):
  - 3.3.1 Nihai Donanım ve Sistem Mimarisi: İHA ve İKA için ayrı ayrı; sinyal (PWM, UART, I2C) ve güç hatları renk kodlu bağlantı şemaları; nihai aviyonik BOM (ad, marka/model, adet, birim/toplam ağırlık, boyut, maliyet); DDR'de planlanan ile FDR'de gerçekleşen BOM karşılaştırması; entegrasyon planı.
  - 3.3.2 Elektriksel Tasarım ve Kablolama: nihai kablaj/konnektör tablosu, AWG ve uzunluklar, **ölçülen** maksimum akıma göre akım taşıma ve gerilim düşümü; güç tüketimi doğrulaması (tam yükte ölçülen akım ↔ batarya kapasitesi; teorik ↔ pratik).
  - 3.3.3 Görev İcra Simülasyonu: İHA ve İKA CAD modelleriyle 3B simülasyon ortamında görevin sanal icrası (kalkış, görüntü işleme ile rota tespiti, İKA'ya aktarım, otonom sürüş); otonom karar verme başarı oranları, sanal görev süresi, sistem tepkileri grafikleri; **ekran kaydı video linki**.
  - 3.3.4 Görev Algoritması ve Yazılım Detayları: İHA/İKA otonom ana döngülerinin ve karar mekanizmalarının **akış diyagramları**; rota tespiti model/YZ'sinin **sahaya benzer koşullarda (farklı ışık açıları, gölgeler) test sonuçları ve doğruluk matrisleri**; İHA–İKA ve YKİ–araç **haberleşme paket yapısı, veri hızı, gecikme test sonuçları**.
- **Bölüm 4 Test Faaliyetleri (15)** (FDR-Y s.17–18): yer/fonksiyonel/entegrasyon testleri; sensör gereksinimleri ve yerleşimleri; ekipman kabul testleri; **kumanda ve telemetri menzil testleri**; **IMU, pusula, pitot kalibrasyon kanıtları**; simülasyon (yukarıdaki); görüntü işleme performansı; haberleşme testleri; yerde bütünleşik çalışma kanıtları; **arıza emniyet tepkilerinin (eve dönüş, motor kesme) sahada test verileri**.
- **Bölüm 5 Üretim (15)** (FDR-Y s.18): üretim yöntemleri, imalat süresi, montaj planı; **Şubat 2027 SGGS'de tutarlılık kontrolü** yapılacak; gerekliliği ispatlanmamış değişiklikler **diskalifiye sebebi** olabilir.
- **Bölüm 6 İzlenebilirlik (10)** (FDR-Y s.18): her gereksinim için doğrulama yöntemi (analiz, hesaplama, test, simülasyon, gözle muayene); karşılanmayanların nedeni ve iyileştirme planı; özet tablo veya **pasta grafiği**.
- **Bölüm 7 Bütçe (10)** (FDR-Y s.19): BOM ile planlanan/gerçekleşen maliyet, yüzdesel dağılım, harcanmamış bütçenin kullanım amacı.
- FDR-Y s.15 Not: İKA (DDR 3.2.2) ve Mancınık (DDR 3.2.3) hazır alınma koşulları DDR ile aynıdır.

### 4.4 DDR Yönergesi (DDR-Y) — yazılımcıyı ilgilendiren başlıklar
Tablo (DDR-Y s.7): Özet 10, Org. 10, **Genel Sistem 60**, Test 10, İzlenebilirlik 10.
- 3.1.3 Kısıt diyagramı: seçilen W/S, W/P, P/W değerleri gerekçeli (DDR-Y s.9). 3.1.10 Uçuş zarfı gust çizgileriyle, **CS-VLA** denklemleri (s.10); 3.1.12 yük hesaplamalarında CS-VLA (s.11).
- 3.2.2 / 3.2.3: İKA ve mancınık **tasarlanacaksa** vs. **hazır alınacaksa** ayrı gereksinim listeleri (DDR-Y s.12–14); mancınık için yay sabiti ve fırlatma mesafesi enerji denklemleri.
- 3.3.1 Sistem mimarisi ve görev akış şemaları + **arıza emniyet senaryolarının mantık şemaları** (s.14).
- 3.3.4 Güç sistemi: ortalama/tepe akım tablosu, mAh hesabı, C değeri uygunluğu (s.15).
- 3.3.5 Yazılım Mimarisi ve Görüntü İşleme (s.15–16): **Yazılım altyapısı** (programlama dilleri Python/C++, kütüphaneler OpenCV/ROS/TensorFlow, işletim sistemleri; seçim gerekçeleri); **Görüntü işleme algoritması** (İHA rota tespiti için YZ/ML modelinin çalışma prensibi, **veri seti hazırlığı, eğitim süreci, başarı oranları**, blok şemalar); **Haberleşme protokolü** (İHA–İKA veri haberleşme mimarisi, veri bütünlüğü ve güvenliği için protokoller).
- Bölüm 5: MoC (Means of Compliance) metodolojisi, izlenebilirlik matrisi (s.16–17).

---

## 5. Jüri/hakem değerlendirme ölçütleri ve sunum formatı

- **Raporlar** DDK tarafından tablolardaki bölüm puanlarıyla değerlendirilir (ŞART s.7 §1; Tablo 2–5). Rapor puanları Puan1'e girer (ağırlıklar §2.1).
- **Final Değerlendirme Sunumu (FDS)**: Takvimde "Final Değerlendirme Sunumları (FDS) ve Drone ile Görev Test Uçuşu — 30.09–03.10.2026" (ŞART s.10). FDS sonucundaki başarı sıralaması **uçuş sırası seçme önceliğini** belirler (ŞART s.21 §6.2). Sunum süresi, slayt formatı, soru-cevap süresi ve puanlama ağırlığı → **PDF'de bulunamadı** (ŞART §5.3 FDA'yı yalnız FDR + drone testi olarak tanımlar).
- **Sözlü sorgu**: Sahada Alan Hakemi'nin canlı tespit/aktarım **sözlü onayı** vardır (ŞART s.22); ayrı bir jüri sözlü sınavı formatı **PDF'de bulunamadı**.
- **Teknik muayene**: Teknik Kontrol Çadırı; ilk denemede 100, ikinci 50, geçemezse 0 ve uçuş yok; TUSAŞ yetkilileri ve hakem kararları kesin (ŞART s.20 §6.1; s.25).
- **Centilmenlik**: yarışma boyunca takım çalışması ve centilmenlik, maks. 50 (s.26). Yetkililere sözlü/fiili müdahale → diskalifiye (s.23 §6.3).
- **İtiraz**: Gruplama/uçuş sırasına ve güvenlik gerekçeli kararlara itiraz yok (s.21); diskalifiye olanların itiraz hakkı yok (s.12).
- **Ödüller** (ŞART s.26 Tablo 7): 1. 750.000 TL (danışman 50.000), 2. 600.000 TL (40.000), 3. 500.000 TL (30.000); ilk 3 takım üyelerine TUSAŞ Ankara yaz stajı hakkı (stajyer kabul kriterleri kaydıyla) (§8.1).
- **Katılım koşulları** (ŞART s.11–13 §4, §4.1): takım 6–10 kişi (danışman hariç), lisansüstü oranı ≤ %20, üniversite öğrencisi 1 takım kaptanı zorunlu, en fazla 1 danışman (zorunlu değil), aynı kişi birden fazla takımda olamaz; hazır ticari platform veya intihal → diskalifiye (s.19 §6); geçmiş yıl projesi ancak geliştirilerek sunulabilir (s.12).

---

## 6. "Üçüncü senaryo" belgesi (TYDA) ile ana şartnamenin farkı

**Bu belge farklı bir yarışmaya aittir.** Olgusal karşılaştırma:

| Başlık | ŞART (İleri Otonom Sistemler) | TYDA ("3. Senaryo") |
|---|---|---|
| Yarışma adı | İleri Otonom Sistemler Tasarım ve Operasyon Yarışması (kapak) | **Yapay Zekâ Dil Ajanları Yarışması Teknik Şartnamesi (3. Senaryo)** (kapak) |
| Yürütücü | TUSAŞ / DDK (s.7) | **Bilişim Vadisi** (TYDA s.2 §1) |
| Konu | İHA + İKA otonom afet lojistiği | Video verisini analiz eden, Türkçe özet/aksiyon önerisi üreten, yerel (offline, vLLM) LLM tabanlı karar destek sistemi (TYDA s.3 §3) |
| Çıktı | Fiziksel uçuş/sürüş | JSON formatında olay listesi, özet, risk, aksiyon (TYDA s.7 §5 örnek) |
| Takım | 6–10 kişi | **4 üye** (TYDA s.10 §9) |
| Takvim | 2026–2027 (Tablo 1) | Başvuru 12 Haz.–12 Tem.; online süreç 27 Tem.–26 Ağu.; final Ağustos; TEKNOFEST Şanlıurfa 30 Eyl.–4 Ekim (TYDA s.9 Tablo 1) |
| Değerlendirme | Puan formülü (§7) | Fonksiyonellik %35, Teknik İmplementasyon ve Mimari %35, Otonomi ve Zekâ %20, Yenilikçilik %10; 100'lük sistem (TYDA s.8 §7, s.13 §12) |
| Sunum | FDS (format yok) | Sunum 4 dk + demo videosu 1 dk; Bilişim Vadisi Kocaeli'de son 24 saat fiziki (TYDA s.12–13 §11) |
| Ödül | 750/600/500 bin TL | 120/100/80 bin TL (TYDA s.14 Tablo 2) |
| Açık kaynak | Hüküm yok | GitHub'da Apache 2.0, "BilisimVadisi2026" etiketi zorunlu (TYDA s.11–12 §9–10) |

**Sonuç:** TYDA belgesindeki hiçbir kural İHA/İKA yarışması için bağlayıcı değildir. Ana şartnamede geçen "Senaryo 3" ifadesi K_zorluk = 2.0 olan güzergâh senaryosudur (ŞART s.24); onunla ilgili ayrı bir belge bu depoda **yoktur**. Jüri "üçüncü senaryo" derse kastedilen büyük olasılıkla ŞART s.19–20'deki "Zor" güzergâh periyodudur; TYDA belgesine atıf yapılmamalıdır.

---

## 7. Muhtemel 20 jüri sorusu ve cevabın yeri

| # | Soru | Cevabın arandığı yer |
|---|---|---|
| 1 | Açık güzergâhı nasıl tespit ediyorsunuz? Model, sahaya benzer ışık/gölge koşullarında hangi doğruluğu verdi? | FDR-Y §3.3.4 (s.16: doğruluk matrisleri); DDR-Y §3.3.5 (s.15: veri seti, eğitim, başarı oranı); ŞART §2.2.2 s.9 |
| 2 | Güzergâh bilgisini İKA'ya ve yer istasyonuna hangi paket yapısıyla, hangi gecikmeyle aktarıyorsunuz? Aktarım İHA havadayken tamamlanıyor mu? | ŞART §2.2.3 s.9; FDR-Y §3.3.4 "Haberleşme Paket Yapısı" s.17; DDR-Y §3.3.5 "Haberleşme Protokolü" s.16 |
| 3 | Alan hakemi tespiti monitörde nasıl görüp onaylayacak? Hakem onayı alınamazsa ne olur? | ŞART s.22 §6.2; s.23 §6.4 "Hakem Teyidi ve Veri Aktarımı" |
| 4 | İHA'nın uçuş süresi neyle başlar, neyle biter; 15 dakika aşılırsa? | ŞART s.22 §6.2; s.23 §6.4 "Süre Aşımı"; s.25 t_İHA |
| 5 | İKA neden İHA inmeden hareket edemiyor; başlangıç tetiklemesi otonom mu manuel mi? | ŞART §2.2.5 s.9 (YKS görevlisi manuel tetikler; sonrası tam otonom); s.23 §6.2 son madde |
| 6 | Paraşüt otonom mu açılıyor? Manuel tetiklerseniz ceza ne? Açılmazsa? | ŞART §2.2.4 s.9; Tablo 6 s.26 (−50); §6.4 s.23 "İniş İhlali" |
| 7 | İniş bölgesi dışına düşerseniz puan nasıl etkilenir? | Tablo 6 s.26 "İniş Sapması −5/m"; İHA-İB 30×30 m s.8 |
| 8 | Hands-off sonrası sisteme müdahale etmek zorunda kalırsanız? | ŞART s.22 §6.2 (100 ceza + süre eklenir); Tablo 6 s.26 "Yeniden başlatma −100" |
| 9 | Güvenlik pilotu manuel moda alırsa uçuş ne olur? Failsafe/eve dönüş davranışınızı sahada test ettiniz mi? | ŞART §6.4 s.23 "Manuel Müdahale"; FDR-Y Bölüm 4 s.17–18 (eve dönüş, motor kesme test verileri) |
| 10 | Toplam puan formülünde uçuş performansının ağırlığı nedir; K_zorluk hangi senaryoda kaç? | ŞART §7 s.24 (0.65·Puan2; K = 1.0/1.5/2.0) |
| 11 | İHA'nızın kalkış kütlesi kaç gram; hafiflik puanı nasıl hesaplanıyor; 25 kg aşılırsa? | Tablo 6 s.25 (her 10 g = 1 puan); ŞART s.19 §6 (25 kg dahil yükler → aşan değerlendirme dışı) |
| 12 | İKA ne kadar yük taşıyor, yük puanı nedir, 10 kg limiti yükü kapsıyor mu? | Tablo 6 s.25 (m_yük: 100 g = 1 puan); s.19 §6 (10 kg **hariç** operasyonel yük); §2.2.6 s.10 (yük eksiksiz muhafaza) |
| 13 | Üç uçuş hakkınızı nasıl kullanacaksınız; kullanılmayan hak devreder mi? | ŞART s.20 §6 (her periyot 1 hak, devretmez, yanar → 0) |
| 14 | Mancınıktan sonra İHA havalanamazsa ne olur; tekrar fırlatma sırasında ne yapabilirsiniz? | ŞART s.22 §6.2 (hasar yoksa tekrar hak; süre durmaz; yalnızca mancınık kurulumu ve yeniden başlatma) |
| 15 | İHA-UB (300×300 m) sınırını yazılımınız nasıl garanti ediyor? İhlalde sonuç? | ŞART s.8 §2.1; s.22 §6.2 "Alan İhlali"; s.23 §6.4 "Saha Sınır İhlali" |
| 16 | Uçuş öncesi hazırlık süresinde neler yapılır, süre puanı nasıl hesaplanır? | ŞART s.22 §6.2 (İHA montajı, mancınık yerleşimi, İKA-KB'ye yerleşim, YKİ kurulumu; 15 dk); Tablo 6 s.25 t_hazırlık (30 s = 1 puan) |
| 17 | Görev simülasyonunu hangi ortamda yaptınız; otonom karar başarı oranları ve video linki nerede? | FDR-Y §3.3.3 s.16; Bölüm 4 s.17 |
| 18 | Aviyonik BOM'da DDR'den FDR'ye ne değişti; SGGS'de tutarlılık nasıl sağlanacak? | FDR-Y §3.3.1 s.15–16; Bölüm 5 s.18 (Şubat 2027 SGGS tutarlılık kontrolü; ispatlanmamış değişiklik → diskalifiye riski); ŞART §5.4 s.18 |
| 19 | Kumanda/telemetri menzil testleri ve IMU-pusula-pitot kalibrasyon kanıtlarınız nerede? | FDR-Y Bölüm 4 s.17 |
| 20 | Drone ile Görev Test Uçuşu'nda (FDA) ne yaptınız; 30 m irtifa, 10 dk ve gerçek zamanlı aktarım koşulları sağlandı mı; FDA puanı nasıl hesaplanır? | ŞART §5.3.2 s.17–18 (FDA = FDR×0.85 + Test×0.15) |

**Ek soru ihtimalleri (cevap PDF'de yok — "şartnamede belirtilmemiştir" denmeli):** haberleşme frekansı/bandı, batarya kimyası/gerilim sınırı, boyut sınırı, İHA irtifa sınırı, kill switch, FDS sunum süresi, üç turun puan birleştirme yöntemi, İKA yük tanımı ("teknik gereksinimler listesi" ekte yok).

---

## 8. Yazılımcı için kısa hatırlatma listesi (yalnızca PDF'den türetilmiş)
1. İHA + İKA zinciri **fırlatmadan HB'ye kadar tam otonom**; tek izinli insan tetiklemesi İKA intikal başlatma (ŞART s.9, s.23).
2. Tespit → **YKİ monitöründe canlı** → **hakem sözlü onayı** → İKA'ya aktarım, hepsi **İHA havadayken** (s.9, s.22).
3. Zaman bütçesi: hazırlık 900 s, İHA 900 s, İKA 600 s; her 5 s İHA / 15 s İKA / 30 s hazırlık = 1 puan (s.25).
4. Görev başarı puanı **600**; başarısız uçuşta 0; üç senaryoda K = 1.0/1.5/2.0 (s.24–25).
5. Rapor kanıtları: doğruluk matrisleri, farklı ışık/gölge testleri, haberleşme gecikme ölçümleri, simülasyon videosu, failsafe saha testi (FDR-Y s.16–18).
6. Uçuşu geçersiz kılan 6 hâl (s.23 §6.4) yazılımda tasarım kısıtı olarak ele alınmalı: süre, manuel müdahale, hakem teyidi, alan sınırı, kırım, paraşüt.
7. `simulation/score.py` formülü doğru; ancak **geçersiz uçuşta Puan2'yi sıfırlamaz** ve **üç turu birleştirmez** (bkz. §2.3).
