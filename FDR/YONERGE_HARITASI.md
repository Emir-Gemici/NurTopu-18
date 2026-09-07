# FDR YÖNERGE HARİTASI — zorunlu yapı ve gereksinim listesi

> **Bu dosya raporun İSKELETİDİR ve tek doğru kaynağı `FDR_2_qNiVF.pdf`
> (TEKNOFEST 2026 İleri Otonom Sistemler Tasarım ve Operasyon Yarışması,
> Final Değerlendirme Raporu Hazırlama Yönergesi, 19 sayfa).**
> Metni depoda: `results/fdr_sablon/fdr_yonerge_metin.txt` (pypdf ile çıkarıldı).
>
> Bölüm başlıkları, alt başlık numaraları ve puanlar **yönergeden alınmıştır,
> icat edilmemiştir**. Bir başlığı değiştirmek isteyen önce yönergeye bakar.
>
> Her gereksinime bir **kimlik** verildi (`Y-<bölüm>-<tip><no>`), böylece
> Bölüm 6 izlenebilirlik tablosu ve açık kalem listesi aynı kimliği kullanır.
> `T` = Yapısal Tasarım süreci, `A` = Yapısal Analiz süreci, `M` = madde.
>
> **DURUM sütunu:** `VAR` (yazıldı ve kanıtlı) · `KISMEN` (bir kısmı var) ·
> `YOK` (hiç yazılmadı) · `KAPSAM DIŞI` (gerekçesiyle).

---

## 0. Ön kısım — yönergede zorunlu, 3 Eylül'de `BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` olarak yazıldı

| kimlik | ne | durum |
|---|---|---|
| `Y-0-M01` | **Kapak sayfası**: TAKIM ADI / TAKIM ID / BAŞVURU ID | KISMEN (üç alan yazılı; KYS teyidi DOĞRULANACAK, logo BEYAN GEREKLİ) |
| `Y-0-M02` | **VERSİYONLAR** tablosu (Versiyon · Tarih · Açıklama) | KISMEN (V1 03.09.2026 satırı var; teslim sürümü BEYAN GEREKLİ) |
| `Y-0-M03` | **TANIMLAR ve KISALTMALAR** — yönergedeki liste (DDK, İHA, İKA, HTAB, İHA-FB, İHA-UB, İKA-KB, HB, İHA-İB, ÖDR, DDR, FDR, FDA, FDS, SGGS, UHDR, K_zorluk, m_İHA, t_İHA, t_hazırlık, m_İKA, m_yük, t_İKA, P_görev, P, P_TI, P_uçuş, P_centilmenlik, C_ceza) | VAR |
| `Y-0-M04` | **İÇİNDEKİLER** | VAR (bölüm düzeyi tablo; sayfa numaraları dizgide) |
| `Y-0-M05` | Her sayfada **TASNİF DIŞI** başlık/altlık + sayfa numarası | YOK (PDF dizgisinde) |

## 1. Bölüm 1 — Özet · **5 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-1-M01` | Projenin teknik hatlarını ve operasyonel kabiliyetini tanımlayan **sistematik ve bütüncül** özet | KISMEN |
| `Y-1-M02` | **İHA, İKA ve Mancınık** sistemlerinin proje gereksinimleri dikkate alınarak yapılan final tasarım faaliyetleri ve **özgün sistem mimarileri** | KISMEN (İKA/Mancınık zayıf) |
| `Y-1-M03` | ÖDR ve DDR'de tanımlanan gereksinimlerin ve tasarım kriterlerinin **nihai tasarım üzerinde doğrulandığı** | KISMEN |
| `Y-1-M04` | Gerçekleştirilen **revizyonların tamamlandığı** | KISMEN |
| `Y-1-M05` | Sistemin **görev tanımını karşılayacak olgunluğa ulaştığı** | KISMEN |
| `Y-1-M06` | Nihai **mekanik, aviyonik ve yazılım mimarileri**; alt sistem konfigürasyonları; sistemler arası **fiziksel ve fonksiyonel etkileşimler** teknik gerekçeleriyle | KISMEN |
| `Y-1-M07` | **Üretim yöntemleri, malzemeler, montaj süreçleri, saha kurulum prosedürleri** → üretilebilirlik, entegrasyon uygulanabilirliği, operasyonel kullanıma hazır olduğu | KISMEN |
| `Y-1-M08` | Görev icrasında karşılaşılabilecek **teknik riskler**, önleyici tedbirler, **risk azaltma stratejileri ve acil durum senaryoları** | KISMEN |
| `Y-1-M09` | **Operasyon planı, görev akışı, ekip organizasyonu, görev dağılımı ve kurulum süreçleri** → operasyonel hazırlık seviyesi | KISMEN |
| `Y-1-M10` | Bütünleşik sistemin görev gereksinimlerini karşılama düzeyi analizi; **tasarım doğrulama süreci özeti**; uçuş/operasyon/görev icrasına teknik olgunluk kanıtı | KISMEN |

## 2. Bölüm 2 — Organizasyonel Yapı ve Proje Takvimi · **5 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-2.1-M01` | **Bölüm 2.1 Organizasyonel Yapı** — takımın güncel organizasyonel yapılanması ve üyelerin/birimlerin **icra yetkileri şematize** edilmeli | VAR (7 Eylül: `sekiller/organizasyon.svg` §2.1.2'ye gömüldü; rol bazlı, isimsiz; nöbetçi `tests/test_gece_sekiller.py`) |
| `Y-2.1-M02` | 🔴 **İSİM YAZILMAZ.** *"üyelerin kişisel verilerinden (isim, görsel vb.) arındırılmış, tamamen rol bazlı ve profesyonel bir anlatım"* | **VAR** — rapor zaten rol bazlı (R1–R8) |
| `Y-2.2-M01` | **Bölüm 2.2 Proje Takvimi** — DDR'deki takvimin **termin planına uygunluğu teyit** edilmeli | KISMEN |
| `Y-2.2-M02` | İş takvimine **eklenen yeni iş akışları** varsa planlama analitik yaklaşımla **yeniden değerlendirilip güncellenmeli** | KISMEN |

## 3. Bölüm 3 — Genel Sistem Spesifikasyonları · **40 puan**

> Üç ana başlık: **3.1 Uçuş Bilimleri** · **3.2 Yapısal Tasarım ve Analiz** ·
> **3.3 Aviyonik & Yazılım**. Numaralandırma yönergeden birebirdir.

### 3.1 Uçuş Bilimleri — İHA Kavramsal Tasarım Esasları

> ⚠ Yönerge notu: *"DDR aşamasında sunulan analiz ve hesaplamalara ilişkin
> herhangi bir güncelleme veya revizyon bulunmaması durumunda bu bölüm için
> ilave açıklama yapılmasına gerek bulunmamaktadır."* — yani **DDR'den beri
> değişen bir şey yoksa** o alt başlıkta bunu **açıkça beyan etmek** yeterlidir.
> Bu, boş bırakmak DEĞİLDİR; "değişmedi" de bir beyandır.

| kimlik | alt başlık | ne isteniyor | durum |
|---|---|---|---|
| `Y-3.1.1` | **Ağırlık & Denge** | DDR sonrası güncellemeler: kütle dağılımı, ağırlık merkezi konumu, atalet özellikleri, hesap sonuçları — teknik dayanakla | YOK |
| `Y-3.1.2` | **Hava Aracı Boyut Güncellemeleri** | kanat, gövde, kuyruk takımı geometrileri — DDR sonrası değişiklikler + dayanak + nihai değerler | YOK |
| `Y-3.1.3` | **Kontrol Yüzeyi Tasarımı Güncellemeleri** | kontrol yüzeyi boyut, geometri, tasarım parametreleri — DDR sonrası | YOK |
| `Y-3.1.4` | **Aerodinamik Karakteristik** | analiz, katsayı, performans parametreleri — DDR sonrası; nihai aerodinamik karakteristik | YOK |
| `Y-3.1.5` | **Kararlılık Karakteristiği** | statik ve dinamik kararlılık — DDR sonrası | YOK |
| `Y-3.1.6` | **Performans Hesaplamaları** | performans analiz ve hesapları — DDR sonrası | YOK |
| `Y-3.1.7` | **Yük Hesaplamaları** | yapısal yük hesapları, yük durumları, analiz sonuçları — DDR sonrası | YOK |

### 3.2 Yapısal Tasarım ve Yapısal Analiz

> Üç platform ayrı ayrı: **3.2.1 İHA** · **3.2.2 İKA** · **3.2.3 Mancınık**.
> Her birinde gereksinim izlenebilirliği ve **doğrulama yöntemi** (analiz, test,
> gözle muayene, benzerlik) tanımlanmalı.
>
> ⚠ Yönerge notu: *"İnsansız Kara aracı (DDR 3.2.2) ve Mancınık (DDR 3.2.3)
> alt sistemlerinin **hazır alınma koşulları DDR ile aynıdır**."*

#### 3.2.1 İnsansız Hava Aracı (İHA) — Yapısal Tasarım (18 madde)

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-3.2.1-T01` | Master geometride yapılan değişiklikler (var ise) revizyon öncesiyle **karşılaştırmalı** + gerekçe | YOK |
| `Y-3.2.1-T02` | Yapısal parçalarda yapılan değişiklikler (var ise) karşılaştırmalı + gerekçe | YOK |
| `Y-3.2.1-T03` | İHA'ya ait **tüm parçalar detay seviyesinde** tasarlanmış olmalı | KISMEN |
| `Y-3.2.1-T04` | İHA tasarımında kullanılan **tasarım kriterleri** ayrıntılı | KISMEN |
| `Y-3.2.1-T05` | Sistem yerleşimi tamamlanmış; aviyonik, itki, güç, haberleşme, faydalı yük, **paraşüt kurtarma sistemi ve fırlatma ara yüzü** dâhil **üç boyutlu model üzerinden** gösterilmeli | YOK |
| `Y-3.2.1-T06` | **İHA–İKA–Mancınık arası fonksiyonel ve fiziksel ara yüzler TABLO** | YOK |
| `Y-3.2.1-T07` | Tüm **bağlantı elemanları ve yapıştırıcılar** tablo | YOK |
| `Y-3.2.1-T08` | **Tedarikçiler ve tahmini teslim süreleri** dâhil satın alınacak parça listesi | KISMEN |
| `Y-3.2.1-T09` | **Parça numaralandırma ve revizyon sistemi** + nihai **BOM** | YOK |
| `Y-3.2.1-T10` | FDR seviyesinde **toplam hava aracı kütlesi** (aviyonik + yapısal) + **kütle dağılım tablosu** | KISMEN (tartı bekliyor) |
| `Y-3.2.1-T11` | **Malzeme seçimleri**: dayanım, ağırlık, üretilebilirlik, operasyonel gereksinim gerekçesiyle | KISMEN |
| `Y-3.2.1-T12` | Tüm yapısal parçalar için **üretim yöntemleri** (kompozit yatırma, CNC, sac şekillendirme, eklemeli imalat vb.) | KISMEN |
| `Y-3.2.1-T13` | Üretim yöntemine göre **toplam imalat süresi** tahmini + **montaj planı** | KISMEN |
| `Y-3.2.1-T14` | Parça başına **tahmini üretim süresi ve iş gücü ihtiyacı**; **fikstür ve aparat tasarımları** | YOK |
| `Y-3.2.1-T15` | Her ana üretim adımı sonrası **ara kontroller ve ölçümler** | YOK |
| `Y-3.2.1-T16` | Olası üretim hataları + **düzeltici işlem prosedürleri** | YOK |
| `Y-3.2.1-T17` | Tüm parçalar için **üretim resimleri ve teknik çizimler** | YOK |
| `Y-3.2.1-T18` | **Taşıma ve depolama** koruma yöntemleri | YOK |

#### 3.2.1 İHA — Yapısal Analiz (12 madde)

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-3.2.1-A01` | Yapısal malzemelerin **dayanım özellikleri tablosu** + **fiyat/performans oranları** | YOK |
| `Y-3.2.1-A02` | Gövde, kanat, kuyruk **topoloji optimizasyonu**; DDR ↔ FDR **karşılaştırmalı** ağırlık azaltma | YOK |
| `Y-3.2.1-A03` | Optimize İHA için **modal frekans ve kütle katılım tablosu** + pozitif/negatif **burkulma özdeğer tablosu** | YOK |
| `Y-3.2.1-A04` | Kanat tasarımında DDR sonrası **iterasyon ve optimizasyon sayısı** | YOK |
| `Y-3.2.1-A05` | Yerleşim/iç yapı değişikliği varsa **doğrulama sonuçları** | YOK |
| `Y-3.2.1-A06` | Nihai **burkulma özdeğerleri, mod frekansları, modal kütle katılım oranları** + **el hesapları** | YOK |
| `Y-3.2.1-A07` | Gövde optimizasyonu: **iterasyon sayısı, optimizasyon bölgesi**, üç analiz türü (statik, burkulma, modal) sayısal doğrulama | YOK |
| `Y-3.2.1-A08` | Final gövde analizi — **tüm yüklerin etkisi** | YOK |
| `Y-3.2.1-A09` | Kuyruk optimizasyonu: iterasyon, bölge, statik/burkulma/modal doğrulama | YOK |
| `Y-3.2.1-A10` | **Uçuş yüklerinin kuyruk yapısı üzerindeki etkileri** | YOK |
| `Y-3.2.1-A11` | Kontrol yüzeyi bağlantı elemanları ve yapısal parçalar için **tork ve dayanım hesapları** (üretim öncesi nihai) | YOK |
| `Y-3.2.1-A12` | Kontrol yüzeyleri **menteşe ve tork analizi karşılaştırmalı tablo** | YOK |

#### 3.2.2 İnsansız Kara Aracı (İKA)

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-3.2.2-T01…T11` | Master geometri · yapısal parça değişiklikleri · tüm parçalar detay · tasarım kriterleri · sistem yerleşimi · **ara yüz tablosu** · bağlantı elemanları tablosu · tedarikçi listesi · **parça numaralandırma + BOM** · **toplam kütle + dağılım tablosu** · malzeme seçimi gerekçesi | YOK |
| `Y-3.2.2-A01` | DDR analizleri sonrası **optimizasyon** yapıldıysa ayrıntılı | YOK |
| `Y-3.2.2-A02` | **Yük bırakma sistemi** varsa optimizasyon çalışmaları | YOK |
| `Y-3.2.2-A03` | Dinamik sistemlerde yapısal bütünlüğü etkileyen değişiklik varsa **analizler yeniden** | YOK |

#### 3.2.3 Mancınık

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-3.2.3-T01…T11` | Master geometri · yapısal parçalar · detay tasarım · tasarım kriterleri · sistem yerleşimi · **ara yüz tablosu** · bağlantı elemanları · tedarikçi listesi · **numaralandırma + BOM** · **kütle + dağılım tablosu** · malzeme gerekçesi | YOK |
| `Y-3.2.3-A01` | Fırlatıcı sistemde (varsa) **yay sabiti** | YOK |
| `Y-3.2.3-A02` | Mekanizmanın İHA'yı **ne kadar uzağa fırlatabileceği — enerji denklemleriyle** + **şematik gösterim** | YOK |

### 3.3 Aviyonik & Yazılım

> **Bizim en güçlü olduğumuz yer burası.** Mevcut Bölüm 3'ün ölçülmüş içeriğinin
> neredeyse tamamı buraya taşınır.

| kimlik | alt başlık / madde | ne isteniyor | durum |
|---|---|---|---|
| `Y-3.3.1-M01` | **Sistem Mimarisi** | İHA ve İKA için **ayrı ayrı**; tüm elektronik bileşenlerin bağlantısı, sinyal (PWM, UART, I2C) ve güç hatları **renk kodlarıyla ayrılmış**, okunabilir bağlantı şemaları | KISMEN (İHA metin var, şema ve İKA yok) |
| `Y-3.3.1-M02` | **Nihai Aviyonik BOM Listesi** | İHA ve İKA için ayrı: ad, marka/model, adet, birim ağırlık, toplam ağırlık, boyut, **tahmini maliyet** tablosu; **DDR ↔ FDR karşılaştırmalı**; kablo ve konnektörler dâhil nihai ağırlık ve maliyet | KISMEN |
| `Y-3.3.1-M03` | **Entegrasyon Planı** | İHA ve İKA aviyonik entegrasyonunda izlenecek plan | KISMEN (İHA planı rapora girdi: §3.3.1.3.1 kuru koşu zinciri 9/10 + §3.3.1.3.2 kapı özeti; İKA planı §3.3.1.3.3 BEYAN GEREKLİ) |
| `Y-3.3.2-M01` | **Nihai Kablaj Hesapları** | kablo **kesitleri (AWG)** ve uzunlukları, **akım taşıma kapasitesi ve gerilim düşümü hesapları**, **ölçülen** maksimum akıma göre güncelleme; kablo düzenlemesi, ekranlama, konnektör kilitleme **görsellerle** | YOK |
| `Y-3.3.2-M02` | **Güç Tüketimi Doğrulaması** | tam yükte **ölçülen akım** ↔ batarya kapasitesi uyumu; **teorik hesap ile pratik ölçüm karşılaştırması** | YOK (5 Eylül ölçümü) |
| `Y-3.3.3-M01` | 🔴 **Üç Boyutlu Simülasyon Ortamı** | İHA ve İKA'nın **3B CAD modelleriyle** sanal görev icrası: kalkış, görüntü işleme ile rota tespiti, **verinin İKA'ya aktarılması**, İKA'nın **otonom sürüşü** | KISMEN (Gazebo iskeleti var: 7 dünya + İHA/İKA/mancınık SDF + görev betikleri; CAD yok — mesh 0, koşum yok) |
| `Y-3.3.3-M02` | 🔴 **Simülasyon Verileri** | otonom karar verme **başarı oranları**, **sanal görev süresi**, sistem tepkileri — **grafiklerle** | YOK |
| `Y-3.3.3-M03` | 🔴 **Video Kanıtı** | simülasyonun ekran kaydı videosunun **linki** | YOK |
| `Y-3.3.4-M01` | **Detaylı Algoritma Akışı** | İHA ve İKA otonom davranışlarını yöneten ana döngüler ve karar mekanizmalarının **akış diyagramları** | VAR (7 Eylül: 5 diyagram koddan, `FDR/sekiller/akis_a..e.svg` + düğüm tabloları `akis_<x>_dugumler.md`, 337/337 düğüm dosya:satır tam; nöbetçi `tests/test_gece_akis_diyagramlari.py` 13/13) |
| `Y-3.3.4-M02` | **Görüntü İşleme Başarımı** | yarışma sahasına **benzer koşullarda** (farklı ışık açıları, gölgeler) test sonuçları ve **doğruluk matrisleri** | KISMEN (doğruluk matrisi 7 Eylül'de DOĞRULAMA kümesinde ölçüldü — §3.3.4.2.8 (b), §4.8.4; arena ve ışık/gölge kesiti yok) |
| `Y-3.3.4-M03` | **Haberleşme Paket Yapısı** | İHA↔İKA ve yer istasyonu↔araçlar arasında aktarılan paketlerin **nihai yapısı, veri hızı ve gecikme test sonuçları** | KISMEN (yapı var, gecikme ölçümü kısmi) |

## 4. Bölüm 4 — Test Faaliyetleri · **15 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-4-M01` | Planlanan **yer testleri, fonksiyonel testler ve entegrasyon testleri** ile tasarımın gereksinimlere uygunluğunun doğrulanması | KISMEN |
| `Y-4-M02` | ÖDR/DDR'de tanımlanan testlerin **uygulama yöntemleri ve test altyapısı gereksinimlerinin nihai hâli** | VAR |
| `Y-4-M03` | Testlerde kullanılacak **sensör gereksinimleri, sensör yerleşimleri, test takvimi ve detaylı test zaman bütçe planlaması** | KISMEN (§4.3.1 sensör tablosu + §4.3.3 takvim 3.1–3.6 + §4.3.4 yer bütçeleri var; yerleşim BEYAN GEREKLİ, uçuş süresi ÖLÇÜLEMEDİ) |
| `Y-4-M04` | **Ekipman kabul testleri** — İHA ve İKA'da kullanılacak **tüm ekipmanların** kabul testleri yapılmış ve sonuçlar sunulmuş olmalı | KISMEN (5 Eylül tezgâh: firmware 4.5.7 / GNSS / iBUS / PM06 / motor testi ÖLÇÜM; Jetson, kamera, RF, tam yük ÖLÇÜLEMEDİ; İKA ekipmanı seçilmedi) |
| `Y-4-M05` | **Kumanda ve telemetri menzil testleri** — sahada | YOK (5–19 Eylül) |
| `Y-4-M06` | **IMU, pusula ve pitot tüpü kalibrasyonu** kanıtları | YOK (5 Eylül) |
| `Y-4-M07` | 🔴 **Görev icra simülasyonu** (3.3.3 ile aynı) + başarı oranları + grafikler + **video linki** | YOK |
| `Y-4-M08` | **Görüntü işleme performansı** — benzer koşullarda test sonuçları ve **doğruluk matrisleri** | KISMEN |
| `Y-4-M09` | **Haberleşme testi** — paket yapısı, veri hızı, **iletişim gecikmesi** test sonuçları | KISMEN |
| `Y-4-M10` | Sistem üzerinde gerçekleştirilen **tüm yer testleri** | KISMEN |
| `Y-4-M11` | Entegrasyon öncesi tüm alt sistemlerin **bir arada ve yerde bütünleşik çalıştığını** gösteren kanıtlar | KISMEN (kuru koşu var) |
| `Y-4-M12` | 🔴 **Arıza emniyet doğrulaması** — arıza durumlarında sistemin verdiği tepkilerin (**eve dönüş, motor kesme** vb.) **sahada test edildiğini** gösteren veriler | YOK (5–19 Eylül) |

## 5. Bölüm 5 — Üretim Faaliyetleri · **15 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-5-M01` | Tüm yapısal parçalar için **üretim yöntemleri** (kompozit yatırma, CNC, sac şekillendirme, eklemeli imalat vb.) | KISMEN |
| `Y-5-M02` | Üretim yöntemine göre **toplam imalat süresi** tahmini + **montaj planı** | KISMEN |
| `Y-5-M03` | Her parça için **tahmini üretim süresi ve iş gücü ihtiyacı** | KISMEN |
| `Y-5-M04` | Üretimde oluşabilecek hatalar ve **düzeltici işlem prosedürleri** | YOK |
| `Y-5-M05` | ⚠ *"Şubat 2027'de gerçekleşecek **Sistem Gözden Geçirme Sunumu**'nda tutarlılık kontrolü yapılacaktır. **Gerekliliği ispatlanmamış değişiklikler diskalifiye sebebi** sayılabilecektir."* → her üretim değişikliği **gerekçeli** olmalı | 🔴 **RİSK**: kol 1–2 ile kol 3–4 farklı reçetelerle basıldı, gerekçesi kayıtta YOK |

## 6. Bölüm 6 — Gereksinim İzlenebilirliği ve Değerlendirme · **10 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-6-M01` | Sistem gereksinimlerinin **hangi ölçüde ve ne şekilde karşılandığı** ayrıntılı | KISMEN |
| `Y-6-M02` | Her gereksinimin **doğrulama yöntemi** açıkça (analiz, hesaplama, test, simülasyon, gözle muayene) | VAR |
| `Y-6-M03` | Her gereksinim için **uygunluk durumu** ve gereksinimlerin **tasarım kararlarıyla ilişkisi** | VAR |
| `Y-6-M04` | Gereksinimlerin tasarım sürecinde alınan kararları **nasıl etkilediği**, sistem mimarisi ve performansa **katkısı** | VAR |
| `Y-6-M05` | **Karşılanamayan veya kısmen karşılanan** gereksinimlerin nedenleri + giderme önlemleri / planlanan iyileştirmeler | VAR (bu raporun güçlü yanı) |
| `Y-6-M06` | 🔴 Tüm gereksinimlerin **genel uygunluk durumu ÖZET TABLO veya PASTA GRAFİĞİ** ile **görsel** | KISMEN (§6.6.1–§6.6.4 özet tablolar + metin bar var; pasta grafiği dizgide, BEYAN GEREKLİ) |

## 7. Bölüm 7 — Bütçe Gerçekleme Analizi · **10 puan**

| kimlik | gereksinim | durum |
|---|---|---|
| `Y-7-M01` | Satın alınacak/alınmış tüm malzeme ve bileşenleri içeren **detaylı BOM tablosu**: her kalem için **miktar, birim fiyat, toplam fiyat, tedarik durumu** | KISMEN (fiyat yok) |
| `Y-7-M02` | Her kalem için **planlanan maliyet ↔ gerçekleşen maliyet karşılaştırmalı tablo** | YOK |
| `Y-7-M03` | Toplam bütçenin hangi ana kalemlere harcandığı — **hem yüzdesel hem sayısal**; bütçe dağılımı | YOK |
| `Y-7-M04` | **Harcanmamış bütçenin** hangi amaçlarla kullanılacağı (yedek parça, ek test vb.) kısa açıklama | YOK |
| `Y-7-M05` | Planlanan ↔ gerçekleşen bütçe **farkı varsa nedenleri** | YOK |

---

## Boşluk özeti (7 Eylül 2026 — Y-satırları sayılarak yeniden üretildi; 3.1/3.2 değişmedi)

| bölüm | puan | VAR | KISMEN | YOK | en büyük boşluk |
|---|---|---|---|---|---|
| Ön kısım | — | 2 | 2 | 1 | KYS künye teyidi + logo; TASNİF DIŞI sayfa düzeni (dizgi 18–20 Eylül) |
| Bölüm 1 | 5 | 0 | 10 | 0 | İKA/Mancınık özeti zayıf |
| Bölüm 2 | 5 | 1 | 3 | 0 | organizasyon **şeması** |
| Bölüm 3.1 | *(40'ın içinde)* | 0 | 0 | 7 | **uçuş bilimleri hiç yok** |
| Bölüm 3.2 | *(40'ın içinde)* | 0 | 8 | 48 | **İKA ve Mancınık yapısal; analizler** |
| Bölüm 3.3 | *(40'ın içinde)* | 0 | 7 | 4 | **3B görev simülasyonu + video**; kablaj hesabı ve güç tüketimi ölçümü |
| Bölüm 4 | 15 | 1 | 7 | 4 | menzil, kalibrasyon kanıtı, görev simülasyonu, **arıza emniyet** |
| Bölüm 5 | 15 | 0 | 3 | 1 | düzeltici prosedürler + **reçete farkı gerekçesi** |
| Bölüm 6 | 10 | 3 | 3 | 0 | **pasta grafiği** (dizgi) + ÖDR/DDR gereksinim eşlemesi + açık kalem kapanma tarihleri |
| Bölüm 7 | 10 | 0 | 1 | 4 | **fiyatların tamamı** |

**Okuma:** raporun bugünkü gücü **3.3 (aviyonik/yazılım)**, **4 (test)** ve
**6 (izlenebilirlik)** eksenindedir — orada ölçülmüş, artefakta bağlı içerik var.
En büyük açık **3.1 ve 3.2**: uçuş bilimleri ve yapısal analiz hiç yazılmadı,
İKA ve Mancınık yapısal bölümleri boş. Bu ikisi 40 puanlık bölümün içindedir.

**Kapanma yolu üçe ayrılır:**
1. **Bugün yazılabilir** (veri var, sadece yönerge yapısına taşınmadı): 3.3'ün
   büyük kısmı, Bölüm 4'ün yer testleri, Bölüm 6, ön kısım.
2. **5–19 Eylül ölçümüyle kapanır**: kütle/denge, kablaj ölçümü, güç tüketimi,
   menzil, kalibrasyon, arıza emniyet, görüntü işleme gerçek kare.
3. **İnsan beyanı bekler**: fiyatlar, tedarik, üretim süreleri, CAD/analiz
   çıktıları (uçuş bilimleri ve yapısal analiz **mühendislik işidir**, ölçüm
   değil — bunları takımın tasarım tarafı üretecek).
