# NAVITAS — DEVİR PROTOKOLÜ

## Devir 2026-09-14 · 15 dakikalık teknik sunum

**Teslim:** `fdrtakim/NAVITAS_FDR_15_DAKIKA_TEKNIK_SUNUM.pptx` ve aynı adlı PDF.
17 slayt; kapak ilk, takım tanıtımı ikinci. İHA/İKA/mancınığa dörder slayt
ve 3:45'er dakika ayrıldı; toplam anlatım planı 15:00. 29 kaynak görsel
kullanımı ve dört düzenlenebilir nicel grafik var. Konuşmacı süreleri,
metinleri ve teknik kaynakları slayt notlarında; ayrıca
`fdrtakim/NAVITAS_FDR_SUNUM_KONUSMACI_NOTLARI.md` içinde.

Ana klasör sunum şablonu kullanıldı; özgün raporlar ve şablon değiştirilmedi.
Takım tanıtımı rol bazlıdır; kullanıcıdan istenen ad–görev–eğitim/fotoğraf
yanıtı gelirse ikinci slayta eklenebilir. Kaynaktaki eski 7,029 kg etiketli
V-n grafiği yerine güncel 7,05949 kg ile pozitif V-n hesabı çizildi.
İHA tahrik/BOM ve mancınık ortak kütle-hız çelişkileri gizlenmedi;
başarısız simülasyon sonuçları ve hesap/gerçek kayıt ayrımı korundu.

**Gerçek kapılar:** `test_fdr_teknik_sunum.py` 12/12; genel rota kapısı
kol1 15/15, kol2 15/15. Çıkışlar 0. PDF: 17 sayfa, boş slayt/taşma yok.
Kanıtlar `results/fdr_sunum_20260914/`: `TESLIM_NOTU.md`, `sunum_kunye.json`,
`pdf_denetim.json`, `test_sunum.txt`, `test_genel.txt`, `onizleme/`.
Üretici: `scripts/fdr_teknik_sunum_uret.py`; yardımcı python-pptx kullanıcı
onayıyla yalnız `results/fdr_sunum_20260914/python_deps` altına kuruldu.

PPTX SHA `437b09dd70361690578de6fb02b3a31e3502a69186c32f280a345332b35257b0`;
PDF SHA `e9ee9b70bdce55f2c626098bc8562f82fdc3e4d83d31bcd5fe05a562c42a9fe0`.
**Yazan:** Codex · **Denetleyen:** bağımsız mimar/ekip onayı bekleniyor.
Doğrudan kullanıcı sunum görevi; başka görev kilidi değiştirilmedi. Commit/push yok.

## Devir 2026-09-14 · Takım raporu birleşimi ve tablo yerleşimi

**Güncel birleşik teslim:** `fdrtakim/NAVITAS_FDR_BIRLESIK.docx` ve PDF
(168 sayfa). Yalnız yeni 1, 2, 4, 5, 6, 7 bölümleri:
`fdrtakim/NAVITAS_FDR_BOLUM_1_2_4_5_6_7.docx` ve PDF (12 sayfa).
Tekil bölümler de aynı klasördedir. Kaynak beş DOCX ve altı medya değişmedi;
5.390 metin parçası ve 114 kaynak görsel kullanımı eksiksiz korundu.

Son kullanıcı isteği tablolardaki dikey kelime yığılmasını düzeltmekti.
`scripts/fdr_takim_birlestir.py` artık 48 üst düzey tablonun yanında
`w:sdtContent` içindeki 88 tabloyu da işler: toplam 136 gerçek Word tablosu.
Girintiler, hücre/sütun genişlikleri, satır yükseklikleri, başlık tekrarları ve
yatay tablo sayfaları düzenlendi; gövde ve tablo metinleri Times New Roman 12.
Tablo başlığı tabloyla aynı bölüme alınır, boş ara bölüm üretilmez.

**Gerçek kontroller:** rapor testi 18/18, genel rota kapısı kol1 15/15 ve
kol2 15/15; çıkışlar 0. PDF 168/12 sayfa; boş sayfa ve sayfa dışına taşan
sözcük yok. İçindekilerin 17 başlangıç sayfası PDF ile doğrulandı.
Komutlar/ham çıktılar ve kaynak sınırları:
`results/fdr_bolum1_20260914/TESLIM_NOTU.md`, `test_birlestir.txt`,
`test_genel.txt`, `birlesim_kunye.json`, `pdf/denetim.json`.

DOCX SHA `e490ceab313235eab3d56f3a1036b27f1cc75eb68da817c40ef6466d8b8ccb91`;
PDF SHA `53cfa18de185b44b1e565a8446e6a0fd6a02773f98af6ab0af664023b67712a2`.
Paylaşılan Drive klasörü bu oturumda giriş sayfasına döndü; uzak dosyalar
incelenmedi (`drive_envanter.json`). Yerel kaynaklar kullanıldı.
Kaynak teknik konfigürasyon çelişkileri Bölüm 6.2'de, mali gerçekleşme sınırı
Bölüm 7'de korunur; koşulsuz jüri/bağımsız teknik onay iddiası yoktur.
**Yazan:** Codex · **Denetleyen:** bağımsız mimar/ekip onayı bekleniyor.
Doğrudan kullanıcı belge görevi; başka görev kilidine dokunulmadı. Commit/push yok.

## Devir 2026-09-14 18:28 · FINAL_REV6 güncel konfigürasyon ve ölçüm yöntemleri

**Güncel teslim:** `FDR/JURI/NAVITAS_FDR_3_3_FINAL_REV6.docx` ve aynı adlı PDF.
326 paragraf, 50 tablo, 63 görsel; PDF 49 sayfa. Önceki REV3/4/5 ve kullanıcının
`33.docx` kaynağı korunur. DOCX SHA
`a3c6f25f039cee9b03dd4068b4eed701d09f4756f63c7e0fac437d2f7c3d84fa`;
PDF SHA `fb33466192d5b1e9348ff1dd35b22807fb3996e2398dd98753618bfb340339d0`.
Künye `results/fdr_33_20260914/sunum_rev6/rev6_kunye.json`, PDF kanıtı
aynı dizindeki `pdf/denetim.json` dosyasıdır. Drive bağlantısı sayfa 38'de,
bağlı teker montajı ve yakın planı sayfa 34'tedir.

**Kullanıcı isteği:** REV3'ün sade anlatımı esas alındı; iki boş test tablosu,
17 “Ölçülmedi” hücresi, tekrarlanan yapılacak-test listeleri, eski kapasite
karşılaştırması ve arşiv GT koşusunun 44 noktalı tablosu çıkarıldı. Güncel video
ve YKS planının 42 model noktası, gerçek test sonuçları ve başarısız deneyler
korundu. FDA multirotor güncel kapasitesi 8 Ah / `BATT_CAPACITY=8000` olarak
verilir; geçmiş logların ham parametreleri değiştirilmez. DataFlash, enerji
integrali, piksel karşılaştırması, Jetson süre ölçümü, RF RTT/kayıp hesabı,
paket boyutu ve GNSS kayıt aktarımının yöntemleri açıklandı. Gerçek veri,
simülasyon, kuramsal hesap ve bütçe değerleri birbirine dönüştürülmedi.

**Önceki iki adım:** REV4'te 77 kaynak SHA'sı, 80 sayısal kontrol, 6 BIN,
13 tlog ve 105 simülasyon koşusu karşılaştırıldı. REV5'te elektronikçinin
`33.docx` düzeltmeleri birleştirildi: Pixhawk 6C + PM02 + M9N, Skywalker 60A
V2, Camera Module 3 Wide / IMX708, AS150 ve güncel kalem fiyatları. İHA alt
toplamı 1,543 kg / 141.407,57 TL'dir; kit ve kablaj kütleleri bütçe değeridir.
Kaynak belgedeki eski mimari çizimleri güncel bileşenlerle yeniden çizildi.
REV6, bu iki güncellemenin üstüne sunum sadeleştirmesidir.

**Gerçek kapılar:** `scripts/fdr_33_test_kaydi.py --final-rev6` → genel iki kol
15/15; REV6 13 test / REV5 11 test / REV4 12 test `OK`, tüm çıkışlar 0.
Ham kayıt `results/fdr_33_20260914/test_20260914_182755/`. Önceki gerçek YKS
259 test koşusu `test_20260914_161306/` altındadır; tam depo süiti değildir.
`scripts/fdr_33_final_rev6_pdf.py` → 49 sayfa, bağlantı/açıklamalar mevcut,
sayfa dışına taşan sözcük ve boş gövde sayfası yok, çıkış 0. Tüm 49 sayfa
küçültülmüş dizinde görsel olarak tarandı; her satırın tam çözünürlüklü veya
bağımsız denetçi kontrolü yapılmış sayılmaz.

**Mühendislik sınırları:** Boş ölçüm planının rapordan çıkarılması kabul
testlerinin yapıldığı anlamına gelmez. Fiziksel İKA motor arayüzü ve sabit
kanat saha kabulü bu belge işlemiyle doğrulanmadı. U45 AMS1117-5.0 / 3,3 V
etiketi ile XL4015 geri besleme/hedef gerilim farkları raporda kısa tasarım
kontrolü olarak korunur; şema onarılmış sayılmaz. Temsili fotoğraf/CAD
etiketleri, `plan=False` Jetson kapsamı ve gerçek RF donanım ayrımı korunur.
**Yazan:** Codex · **Denetleyen:** bağımsız mimar onayı bekleniyor ·
**Kapı çıktısı:** yukarıdaki gerçek komutlar ve ham kayıtlar. Commit/push yok.

## Devir 2026-09-14 14:24 · FINAL_REV3 gömülü CAD görsel düzeltmesi

**Güncel teslim:** `FDR/JURI/NAVITAS_FDR_3_3_FINAL_REV3.docx` ve aynı adlı PDF.
353 paragraf, 50 tablo, 63 görsel; PDF 50 sayfa. İKA genel montaj ve bağlantı
yakın planı PDF sayfa 34'tedir. REV2 ve orijinal FINAL değiştirilmedi.
DOCX SHA `3f01f2473c6c28020df635f17841f447af903d1189bc3fbfef06bac7ff5fea78`;
PDF SHA `97174011d00bd0f2842c47efbff78eb6fada5cc8434be9c62fb111ce57c5d072`.

**Kök neden:** Önceki video düzeltmesi, rapordaki üç eski gömülü CAD görseline
aktarılmamıştı. Eski görseller paket ilişkileriyle birlikte kaldırıldı. Aynı
video montajından MuJoCo ile dört yeni stüdyo karesi üretildi: İKA genel/bağlantı,
magenta İHA ve beyaz mancınık. Dört tekerin gövde-braket-redüktör-mil zinciri
görünür; kaynak CAD'de bulunmayan bağlantı parçaları açıkça TEMSİLİDİR.
Ek olarak yanlış 3B PCB başlığı 2B yapıldı, CAD kaynak zarfı ayrımı netleştirildi,
kaynak tablosu Kimlik sütunu ve ondalık ayırıcılar düzeltildi.

**Kanıt:** `scripts/fdr_33_test_kaydi.py --final-rev3` → genel iki kol 15/15,
6 REV3 testi / 7 arena montaj testi OK; tüm çıkışlar 0. Ham kayıt
`results/fdr_33_20260914/test_20260914_142111/`.
`scripts/fdr_33_final_rev3_pdf.py` → 50 sayfa; yeni açıklamalar ve tıklanabilir
Drive bağlantısı mevcut; sayfa dışına taşan sözcük yok, çıkış 0. Tüm sayfalar
küçültülmüş dizin olarak; 8/33/34/35/49 ayrıca büyük önizleme ile incelendi.
Künye ve önizlemeler `results/fdr_33_20260914/gorsel_rev3/` altındadır.

**Korunan sınırlar:** Video baytları/Drive bağlantısı, test sonuçları ve 42 rota
noktası değiştirilmedi. Bu görsel montaj düzeltmesi gerçek imalat veya fiziksel
entegrasyon kanıtı değildir. Önceki elektriksel şema/BOM/fiziksel test açıkları
raporda korunuyor. Tam depo süiti veya bağımsız denetçi onayı yok.
**Yazan:** Codex · **Denetleyen:** bağımsız mimar onayı bekleniyor ·
**Kapı çıktısı:** yukarıdaki gerçek komutlar ve ham kayıtlar.

## Devir 2026-09-14 13:52 · FINAL_REV2 DOCX/PDF ve Drive bağlantısı

**Kullanıcının yeni bilgisi:** `331-332.pdf` güncel şema kaynağıdır;
İHA/İKA yerleşim fotoğrafları **temsili** olarak kullanılacaktır. Drive bağlantısı
`https://drive.google.com/file/d/1xXzQdDCefh2u9UxndF86EfQE8nWI1fjH/view?usp=sharing`
videoya aittir. Onaylı ağ erişimiyle oturumsuz HTTP 200 ve
`navitas_cad_arena_rev1_1080p.mp4 - Google Drive` başlığı doğrulandı; uzak video
indirilip SHA karşılaştırılmadı. Link DOCX ve PDF'de tıklanabilir.

**Yeni teslim:** `FDR/JURI/NAVITAS_FDR_3_3_FINAL_REV2.docx` ve aynı adlı PDF.
351 paragraf, 50 tablo, 62 görsel; LibreOffice çıktısı 49 sayfa.
DOCX SHA `f4b16f21582bf87c3feccd6dd50206c14f8aab14cdc9af723a1bfc31b3f44007`;
PDF SHA `738fed2e8cf11071b911449f7ec736618b515a9119912a25d4b501064eb7d8c5`.
Orijinal Claude FINAL ve kullanıcının PDF'si değiştirilmedi.

**Düzeltmeler:** temsili iki görselin başlık, açıklama, alternatif metinleri;
1,407 kg alt toplam ve eksik motor fiyatı; 250 g İKA kablaj tasarım bütçesi;
İHA ana döngü 0,60 m / ESC kolu başına 0,70 m (eşit paylaşım varsayımı açık)
ile yeniden direnç/kayıp hesapları; 30 V Jetson kademe girişi için hedef 12 V
ripple 0,851 A; güncel video ve başarısız eski koşuların ayrı sunumu;
videosuz tek-rota YKS görseli, gerçek GNSS gösteriminden ayrı tutuldu.
42 nokta yeni videonun ham rota.json dosyasıyla testte tek tek karşılaştırıldı;
referans (-4,48; -23,02) m ve 0–41 tablo / P1–P42 ekran indeks ayrımı yazıldı.

**Açık fiziksel hususlar:** güncel PDF'nin SHA'sı önceden incelenenle aynı:
`e880e266d3e9264c747c80036f3cf8a861213b2d2d4f4544f760a7916d00d090`.
Sayfa 4 şeması/sayfa 6 alt-BOM yine U45 12,4k/3,3k ve U4 10k/3,3k içeriyor;
12 V/5,3 V hedefleri nominal 5,947/5,038 V hesabıyla uyuşmuyor. Bu açıkça rapora
yazıldı, düzeltilmiş kart veya yükte test var sayılmadı. PDF'deki sarı ÖN
değerleri kaynakta gerçek ölçüm değil olarak tanımlanıyor; sonuç diye alınmadı.
Eksik nihai BOM kütle/fiyat ve fiziksel tam-yük/entegrasyon kabulü hâlâ açık.

**Gerçek kapı:** tam Python yolu + `-X utf8 -B scripts/fdr_33_test_kaydi.py
--final-rev2` → genel iki kol 15/15; `Ran 15 tests in 0.227s / OK`; tüm çıkışlar 0.
Kanıt `results/fdr_33_20260914/test_20260914_135031/`. Önceki tek başarısız testte
beklenen gerilim değeri yuvarlatılmıştı; kesin 0,069159744 V beklentisiyle düzeltildi.
`scripts/fdr_33_final_rev2_pdf.py` → `REV2_PDF_OK 49 sayfa; Drive bağlantısı var;
sayfa dışına taşan sözcük yok`, çıkış 0. 2/7/13/29/30/36/37/38/46/47/48/49
sayfaları görsel incelendi; tüm sayfalara bağımsız görsel onay verilmedi.

**Üreteçler:** `scripts/fdr_33_final_rev2.py`, `scripts/fdr_33_final_rev2_pdf.py`;
`scripts/fdr_33_test_kaydi.py` yeni `--final-rev2` seçeneği;
`tests/test_fdr_33_final_rev2.py`. Kanıt `son_kontrol/final_rev2_kunye.json`,
`son_kontrol/rev2_pdf/denetim.json`. Üreteç, kaynak SHA değişirse bilinçli durur.
**Yazan:** Codex · **Bağımsız denetleyen:** yok; kilit/görev kapatma/commit/push yok.

---

## Devir 2026-09-14 · Arena videosu tamam; kullanıcının FINAL.docx belgesi henüz teslim edilemez

**Yetki ve kapsam:** kullanıcının doğrudan video düzeltme ve Claude'un
`FDR/JURI/NAVITAS_FDR_3_3_FINAL.docx` belgesini denetleme talebi. Bu belge artık
esas kaynaktır; eski `BIRLESIK`/`REV1` raporları güncel FINAL yerine teslim edilmez.
FINAL DOCX/PDF değiştirilmedi. T107/T260 kilitlerine dokunulmadı; commit/push yok.

**Video teslimi:** `FDR/JURI/video/navitas_cad_arena_rev1_1080p.mp4`;
1920×1080, 25 FPS, 4.205 kare, 168,20 s, 81.082.874 bayt.
SHA-256: `e46a9dd5796bfdede20d0c067ebcbc2acde8fa3e69c2302292f7240c8d89177e`.
01:30 sonrası önce teker bağlantısı yakın planı, sonra arena içinde sürekli İKA
sürüşü var; sonuç ekranındaki başlangıç konumu hatası da düzeltildi. Açık model
rotası zemin üstünde ince yeşil şerit; İHA magenta, İKA Turan mavisi, mancınık beyaz.
Eksik CAD motor/braket/mil bağlantıları **temsili** ve çarpışmasız/kütlesizdir;
gerçek imalat kanıtı değildir. İKA teker hareketi qpos kaydından, İHA aktüatör
gösterimi temsili. TUR3 kayıtlı algı girdisiyle yeni fizik kaydının tekrar oynatımı;
canlı algı/saha testi değil. Eski NO_ROUTE koşusu korunuyor, GT model başarısı yapılmadı.

**Gerçek doğrulama:** `scripts/fdr_33_arena_video_rev1.py --render` →
`ARENA_VIDEO_OK 4205 KARE 168.2 s`, çıkış 0.
`scripts/fdr_33_arena_video_denetle.py --test` → genel kapı iki kol 15/15;
`Ran 7 tests in 2.837s / OK`, çıkış 0. `--video` →
`TESLIM_VIDEO_DOGRULANDI 4205 kare 13 sürüş örneği`, çıkış 0.
Kanıtlar: `results/fdr_33_20260914/cad_video_arena_rev1_v2/`.
90/120/166 s kareleri ayrıca görsel incelendi; insan görsel kabulünün yerine geçmez.
İlk `cad_video_arena_rev1/` dizinindeki yarım video eski WIP olarak korunuyor.

**FINAL denetimi:** `scripts/fdr_33_final_denetle.py` →
`FINAL_OKUMA_OK 348 paragraf 50 tablo 61 görsel 54 PDF sayfası` ve
`FINAL_DENETIM_KAYDEDILDI 10 bulgu; kurulu alt toplam 1.407 kg; TESLIME_HAZIR=False`,
çıkış 0. Kaynak ve bulgular: `results/fdr_33_20260914/son_kontrol/final_denetim.json`.
DOCX SHA: `f3120da5eff126ddb97eb6860ccf16f9ac1792d2d18d104951c94cfca16c6b9c`.
Sayısal alt toplam 1,876 değil 1,407 kg; 143.098,77 TL bütçe dahil doğrudur, motor
fiyatı da eksiktir. Şemada U45 hedef 12 V fakat bölücü nominal 5,947 V;
U4 hedef 5,3 V fakat nominal 5,038 V. Jetson son buck girişi şemada 30 V,
hesapta 16,8 V. Fiziksel çıkış ölçülmedi. İHA görseli kökteki Gemini adlı JPG ile
güçlü eşleşiyor; ham fotoğraf/temsili görsel kökeni kullanıcıya soruldu, yanıt yok.
İKA fotoğrafına yapay hükmü verilmedi. Kablaj boy/kütle çelişkileri, eski video
bağlantısı ve tasarım NX/SiK ile ölçülen Nano/RFD platform ayrımı da listede.

**Önemli düzeltme:** 64 waypoint raporda bütünüyle yanlış sayı değildir;
planlayıcı için yumuşak hedef, `comms/iha_sender.py:62` için zorunlu gönderim
sınırıdır. 65/67 planlar göndericide geometri reddi alır; sınır kaldırılmadı.
RC olayının ham kayıtta bulunmadığı iddiası yanlış: 08-34-30 BIN'de olay var,
ama son ARM durumu 0; havada RC failsafe kanıtı sayılamaz.

**Diğer gerçek kapılar:** `scripts/fdr_33_test_kaydi.py --hedef` →
`Ran 259 tests in 50.718s / OK`, genel iki kol 15/15, çıkış 0
(`test_20260914_125633/`). Küçük pencere rota listesi ve görünüm testi hizalandı.
`scripts/yki_tek_rota_onizleme.py` → `YKI_ONIZLEME_OK 3 görsel 42 nokta`, çıkış 0;
kayıt etiketi korunuyor, sentetik canlı GNSS/ACK/onay yok.
`-m unittest discover -s tests -p test_fdr_33_final_denetle.py -v` →
`Ran 6 tests in 0.000s / OK`, çıkış 0.
Son `codes/test_rota_sentetik.py` → iki kol 15/15, çıkış 0
(`son_kontrol/final_genel_kapi.txt`). Yorumlayıcı tümünde
`O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`.
Tam süit son denemesi kesildi; tamamlanmış yeşil sonuç olarak raporlanamaz.

**Devralanın ilk işi:** kullanıcının video Drive linki ve görsel kökeni yanıtını
almak; elektronik sorumlusundan güncel şema/yükte çıkış doğrulaması istemek.
Yeni rapor hazırlanırsa FINAL'in ayrı revizyonu olmalı; eksik nihai donanım
kütle/fiyat/tam-yük ölçümleri veya saha testi uydurulmamalı. 2×SunnySky/4S13Ah
arkadaş listesi güncel; eski Excel 4×AT3520/6S16Ah tasarımına geri dönülmez.
8 Ah multirotor test aşamasıdır, sabit kanattan vazgeçilmedi.
**Yazan:** Codex · **Bağımsız denetleyen:** henüz yok; görev kapatılmadı.

---

## Devir 2026-09-11 · Onaylı birleşim tamam, tam süit yeşil

**Yetki:** kullanıcının "onay" mesajı, üç hazır dalın commit ve master'a
birleştirilmesi içindir. Push yapılmadı. Ara WIP geçmişi `--no-ff` ile korundu.

- Devir kayıtları: `307cb314`.
- T226-D2: dal commit'i `72e516f5`, master birleşimi `f80fec8d`.
- T228-D2: dal commit'i `6b9c862c`, master birleşimi `8d3c3fc2`.
- T221-D3: dal commit'i `fe63c69b`, master birleşimi `d02e3b63`.
- Birleşim doğrulaması düzenlemesi: `d812b1e2`. Atölye belgesindeki iki YKS
  satır atfı tazelendi; H1b testinde DPI açık kuruldu ve sabit uyku yerine
  gerçek çizim hazır koşulu beklendi. Ürün kodu/eşikler bu adımda değişmedi.

**Son gerçek kapı** (`O:\navitas`, test edilen HEAD `d812b1e2`):
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1` ortamında
`O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B scripts/push_kapisi.py --kuru`
→ `Ran 2620 tests in 538.782s / OK (skipped=13)`;
`GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`;
`BIRLESIM_KAPI_EXIT=0`. Ham kanıt: `results/push_kapisi/20260911_161757/`.

İlk birleşim koşusu 3 başarısızlıkla kırmızıydı; ham kayıt
`results/push_kapisi/20260911_155724/` altında korunuyor. İki bayat atıf düzeldi;
ilk H1b sıfır-genişlik hatasının kesin tetikleyicisi saptanmadı. Son fikstür,
800 ms geciken çizimde geçti; Configure bağı kaldırılınca yine düştü.
Komutlar ve sınırlar: `results/birlesim_20260911/KANIT.md`, defter D-456.

**Durum:** üç görev `READY_FOR_REVIEW`; resmi bağımsız Claude denetimi bekliyor,
hiçbiri kendi üreticisinin onayıyla `[x]` yapılmadı. ArduPlane SITL ve fiziksel
MK15/Jetson ölçümü KOŞULMADI. Kullanıcının CAD, saha logu, rapor ve izlenmeyen
dosyaları korunuyor; T107 kilidine dokunulmadı.

**Devralanın ilk işi:** üç birleşimin bağımsız incelemesi; ardından aşağıdaki
önceki devirde listelenen **yedi kesinti işi**. O dallar bu birleşime alınmadı.
T236 sürüm/yaw kararı ile ATOLYE-2 kabul metni kararı hâlâ açık.

---

## Devir 2026-09-11 · Claude'un kesilen işi → Codex-1

**Yetki:** kullanıcının "claude un yarım bıraktığı işi devral" talebi. İlk devralma paketindeki
T226-D2, T228-D2, T221-D3 tamamlandı ve `READY_FOR_REVIEW` olarak kaydedildi. Resmi Claude
denetimi ve ana ağaca birleştirme yapılmadı. Kod/kanıt çalışma dallarında duruyor; ana ağaca
bu turda yalnız görev ve devir/inceleme kayıtları yazıldı. Commit/push yapılmadı.

**Tamamlanan üç çalışma ağacı** (ortak kök `O:\navitas\.claude\worktrees\`):

- `wf_61640005-665-1` / HEAD `73f62435`: T226-D2, önceki iki yarım değişiklik korunarak
  H2e/H4e/H2c ve semantik akış denetimi tamamlandı; d78/d83 ret çağrıları ve SVG tazelendi.
  `results/fdr_sprint_20260910/H9_MK15/t226/kapi_devralma_20260911_devam.md` tam kanıttır.
  YKS 233 test OK; MK15 39 test üç ardışık OK; yeni mutasyon 7/7; T202 gerçek tekrar 7/7.
- `wf_c1992b9f-d1a-1` / HEAD `5a597f99`: T228-D2, mevcut ürün/test WIP'i korundu;
  kanıt koşucularının hata çıkışı ve hedef assert sayımı tamamlandı. `H9_MK15/t228d/`
  altındaki `mutasyon_devralma_20260911.txt` ve `kapi_devralma_20260911*.txt` kanıttır.
  54/54 mutasyon; 14 kalıp 263 test (259 başarılı, 4 atlama); gerçek T202 tekrar 7/7.
- `wf_b9bb9db5-4d7-2` / HEAD `874ad16b`: T221-D3, yarım A18 ön kayıt sabitleri bağlandı;
  çizili/çelişkili hüküm ve ölçüt varyantları kilitlendi. `H8/T221/kapi_d3_20260911.md`
  ve `mutasyon_cikti_d3_20260911.txt` kanıttır. 43 ArduPlane + 16 Pixhawk test OK;
  38/38 mutasyon. ArduPlane SITL hâlâ KOŞULMADI/ÖLÇÜLEMEDİ.

Üç dalda da genel kapı gerçekten koşuldu: `O:\navitas-local-train\venv\Scripts\python.exe
-X utf8 -B codes/test_rota_sentetik.py` → `GENEL KAPI (madde 14): GECTI — kol1 15/15 ·
kol2 serit 15/15`, exit 0. Mutasyonlardan sonra asıl dosyaların bayt eşliği doğrulandı.
Tam depo süiti ve fiziksel MK15/Jetson ölçümü bu turda koşulmadı; platform/varlık atlamaları
kanıt dosyalarında açık. T226/T228'de ilk geniş koşudaki eksik varlık hataları korunuyor;
ana depodan yalnız eksik hedeflere gerçek dosyalar kopyalanarak testler tekrar geçirildi.
Ek disk: her dalda altı model 328.162.444 bayt; T226'da ayrıca 88 görsel 49.650.735 bayt.

**Kalan kesinti işleri — tamamlanmış sayılmayacak:** son `devam-3` journal'ı
`C:\Users\yunus\.claude-navitas\projects\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\subagents\workflows\wf_cf0ac6ff-d81\journal.jsonl`
(10 Eylül 22:26:58; 7 amele kesilmiş, 3 denetçi RED). Eski HANDOFF bu turu içermiyordu.

- **T235-E/T236**, `wf_d450cb9f-ba7-9`, HEAD `9dfc5e15`: gerçek SITL sonucu var.
  `H1/t235/sitl/ozet.json`: ArduCopter **4.7.1** ön kayıt planı (yaw LOITER sonrası)
  yaw 0/499 **DÜŞTÜ**; konum/irtifa 499/499. LOITER öncesi karşı deney 500/500 GEÇTİ.
  Üretim hedefi 4.5.7; kaynak sürüm karşılaştırması yarım, üreteç hâlâ LOITER sonrası
  yazıyor. Bu ölçüm ArduPlane T221 değildir; kararı ve üretim sürümünü doğrulamadan bağlanmaz.
- **T235-B/D**, `wf_d450cb9f-ba7-8`, HEAD `c559c97c`: dört yarım dosya; `DUY_JSON`
  yok, `readme_metni` argümanları testle uyuşmuyor. Mevcut sentetik ölçüm A0/A1 DÜŞTÜ;
  nominal A0 16:9@40 m %98,33 < %99, K1 28/28. T235-C'ye geçilmez.
- **ATOLYE-2**, `wf_290ebb2b-6b8-1`, HEAD `4cd13ce2`: RED, 8/13 mutasyon kaçmış;
  CH5→Land eşanlamlıları, A12 akım/VIBE, A10 p50, A7 video kilitleri açık.
  Master ile TASARIM.md çatışması ve A12 ikincil koşulları kararı bekliyor.
- **T227-D**, `wf_61640005-665-2`, HEAD `86550f7f`: README/zamanlama JSON'u yarım;
  yeni CPU zamanlama ölçümü geçse de **FPS v2 yok**. Eski FPS DÜŞTÜ sonucu korunur.
- **AKIS-D2**, `wf_61640005-665-3`, HEAD `6e4aa437`: RED; son dosya commit'i yanlış
  taban seçebiliyor, altı ek mutant kaçıyor. Düğüm bazında köken denetimi gerekli.
- **T229-D2**, `wf_c1992b9f-d1a-2`, HEAD `08cd8ea8`: RED; lot eşanlamlıları,
  GECTI tipografisi ve video kopması hükmüyle beş yeni mutant kaçıyor.
- **T214A-D2**, `wf_b9bb9db5-4d7-1`, HEAD `664df054`: test docstring'ine 13 satır
  plan eklenmiş; vaat edilen kilitler uygulanmamış.

**Devralanın ilk işi:** üç hazır dalın yukarıdaki kanıtlarını ve `git diff`lerini resmi
bağımsız incelemeye almak; kendi üretimini kendi onayıyla `[x]` yapmamak. Sonraki üretim
öncesinde T236 sürüm/yaw bulgusunu ve ATOLYE-2 kabul metni kararını çözmek. Hazır dallar
birleştirilirse kesinti WIP commit'leri korunur (D-454); birleştirme sonrası tam depo süiti
ana varlıklarla gerçekten koşulur. Ana ağaçta kullanıcının CAD, saha logu, rapor ve izlenmeyen
dosyaları var; korunmuştur. T107'nin başka ajana ait kilidine dokunulmadı.

---

> **Bu dosya neden var:** Bu projede iş defalarca **kota bitişiyle** yarıda kaldı.
> Bir Codex token'ı biterken bir görev zimmetli kaldı; denetim iş akışlarında 25'ten
> fazla ajan oturum limitine takıldı. Yarım kalan iş, **bırakıldığı yeri anlatmazsa**
> kaybolur; devralan sıfırdan keşfe başlar.
>
> **Kural: kotaya yaklaşan her ajan, durmadan önce bu dosyayı doldurur.**

---

## Devreden ajan için — doldurma sırası

1. **Kod yazmayı bırak.** Yarım bir düzeltme, hiç başlamamış bir düzeltmeden tehlikelidir.
2. **Genel kapıyı koş** ve sonucunu buraya yaz — ağacın sağlam olup olmadığı devralanın ilk bilmesi gereken şeydir.
3. Aşağıdaki şablonu **en üste** ekle (eski devirler altta kalsın).
4. Görevi `[IN_PROGRESS]` olarak **bırak**. Kilidi kendin **açma** — `AGENTS.md` §3.

---

## GECE KOSUMU · 2026-08-21 (KAPANIS) · Claude 2 (Opus 5, basamele)

**KOSAN IS YOK — tum zincirler bitti, GPU bosta.**

**BITEN ISLER (hepsi push edildi):**
- **T127** temiz bolum zinciri — D-249. On kayit kurali 1 SAGLANDI: kirli
  bolum kazanani SISMEMIS (cati kacagi 0,043 · 67 karede red 0 · K0-K5 gecti).
  Temiz val'de egitim 18 epoch'ta durdu, en iyi epoch 27 -> 10.
- **T115** ustabasi denetimi — D-247 (DOGRU AMA EKSIK; kapiyi ustabasi kostu)
  + D-250 (13 satirin 10'u guvenle onarilabilir). Onarim Codex'in isi;
  genisletilmis kural prompt'u verildi. Bagimsizlik geregi ben onarmiyorum.
- **T129** — D-248: cati korlugu KAYNAK KALITESINE bagli (v34 videoda %96,
  ham fotografta %46). Siralama DEGISMIYOR.
- **T128 / T128-B** — D-251, D-253: `--tohum` VE `deterministic=False`
  ikisi de ATIL; egitim hatti bu recetede TAM TEKRARLANABILIR (bit-es).
  Kosum-ici varyans HALA olculmedi. 🔴 UCUNCU DENEME KOSULMADI (D-253):
  bu soruya ~8,6 saat GPU gitti; yama gerekiyorsa once 2-3 epochluk kucuk
  kosuyla dogrulanmali — karar mimarin.
- **D-252** (kendi hatam): T128'i kosmadan once defteri aramadim, ayni deney
  v31'de zaten yapilmisti. Kalici duzeltme: her on kaydin ilk satiri
  "daha once olculdu mu" aramasi olacak (T128-B'de uygulandi).
- **Kanit dosyasi**: `results/uretim_adayi_kanit_dosyasi.md` — secim kanitlari
  tek yerde (karar DEGIL, derleme).

**KAPI DURUMU (tum degisikliklerden SONRA kosuldu):**
`codes/test_rota_sentetik.py` -> 15/15 ·
`unittest discover -s tests -q` -> Ran 715 · OK · olcum aynasi 77 cift senkron

**DISKTE DURAN AMA COMMIT EDILMEYEN (runs/ gitignore'da):**
`codes/runs/segment/t122ac_tohum42` ve `t122ac_belirsiz` (113'er MB) —
t122ac ile BIT-ES olduklari olculdu; D-251/D-253'un kaniti olarak duruyorlar.
Silinmediler; gerekirse silinebilir (uretim degeri yok).

**MIMARIN MASASINDA:** T122/T127 secim karari (D-237 -> D-239 -> D-240 ->
D-249 birlikte okunur, derleme kanit dosyasinda) · T126 denetimi (D-244) ·
T115 devami (Codex'te) · T124 sinir cumleleri (D-224) · T118 adlandirma
(D-214) · D-233 kume yeniden uretimi · D-245 kuyruk boslugu · D-253 yama karari.

**INSANI BEKLEYEN (madde 9, mimarin acmasi gerek):** DJI cekimi — alan-disi
genelleme sorusu bunsuz KAPANMIYOR (T111/D-198 duvari).

---

## Şablon

```markdown
## Devir <TARİH SAAT> · <Devreden AI> → <Devralan veya "belirsiz">

**Sebep:** kota / çökme / oturum limiti / kullanıcı durdurdu

**Görev:** <T veya S numarası + başlık>
**Durum:** <ne bitti / ne bitmedi — somut>

**Dokunulan dosyalar:**
- `yol/dosya.py` — <ne değişti>

**Genel kapı son durumu:**
```
<komut>
<gerçek çıktı>
exit=<kod>
```

**Çalışma ağacı temiz mi:** evet / hayır — <hayırsa ne yarım kaldı>

**Devralanın İLK yapması gereken:**
<tek somut eylem>

**Tuzaklar:** <devralanın bilmezse zaman kaybedeceği şey>
```

---

## Devralan ajan için — açılış listesi

1. Bu dosyanın **en üstündeki** devir kaydını oku.
2. **Genel kapıyı kendin koş.** Devredenin yazdığına güvenme — ağaç arada değişmiş olabilir.
   ```
   O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
   ```
   Düşüyorsa **yeni görev alma**; önce onu onar.
3. `git status --porcelain` ile çalışma ağacını kontrol et. Yarım değişiklik varsa
   devir kaydıyla karşılaştır; kayıtta olmayan bir değişiklik varsa **dur ve bildir**.
4. Bayat kilit varsa **serbest bırakılmasını iste** — kendin açma (`AGENTS.md` §3).
5. Sonraki `[ ]` görevi al.

---

## Bayat kilit — bilinen olay

Codex-1 token'ı biterken **T14** görevi `[IN_PROGRESS: Codex-1]` durumunda kaldı.
Kod aşamasına hiç geçmemişti (yalnız zimmetlemişti), çalışma ağacı temizdi ve genel
kapı 15/15 geçiyordu — ama kilit hâlâ oradaydı ve kuyruğu tıkıyordu.

**Ders:** Zimmetlemek ile iş yapmak farklı şeylerdir. Devir kaydı, kilidin **arkasında
gerçekte ne olduğunu** söylemelidir.

---

# DEVİR KAYITLARI

*(en yeni en üstte)*

## Devir 2026-08-04 · Codex-1 → belirsiz

**Sebep:** kota (token bitti)

**Görev:** T14 — FDA parametrizasyonu: 20×20 m alan, ≥30 m irtifa
**Durum:** Görev zimmetlendi ama **kod aşamasına hiç geçilmedi.** FDA profiliyle ilgili
hiçbir dosyaya dokunulmadı. Son dokunulan kod dosyaları T13'e aittir; ardından yalnız
belgeler güncellenmiştir.

**Dokunulan dosyalar:** T14 kapsamında **yok**.

**Genel kapı son durumu:** *(mimar tarafından doğrulandı)*
```
O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI
exit=0

-B -m unittest discover -s tests
Ran 58 tests in 7.569s
OK
```

**Çalışma ağacı temiz mi:** evet — T14 açısından. (Diğer görevlerin commit edilmemiş
değişiklikleri mevcut, bu beklenen durumdur.)

**Devralanın İLK yapması gereken:** T14 kilidinin serbest bırakılmasını iste
(`AGENTS.md` §3). Kilit açıldıktan sonra T14 **temiz devralınabilir** — hiçbir yarım
iş yoktur.

**Tuzaklar:**
- T1–T13 `READY_FOR_REVIEW` durumunda ve mimar denetiminden geçti. **6'sı KISMİ** —
  ayrıntı `REVIEW_LOG.md`'de. Yeni iş almadan önce oraya bak, aynı kusuru tekrar üretme.
- `S1` görevi **TIKAYICI**: veri üreteci araçları "zemin" olarak etiketliyor.
  **S1 düzeltilmeden hiçbir veri üretimi veya eğitim koşusu başlatılmaz.**

---

## 14 Eylül 2026 — Kullanıcının doğrudan istediği FDR Bölüm 3.3 teslimi

- **Yazan:** Codex · **Bağımsız denetleyen:** henüz yok; görev kapatma/onay yapılmadı.
- **Teslim:** `FDR/JURI/NAVITAS_FDR_3_3_HAKEM.docx`, aynı adlı PDF ve Markdown. Yalnız Bölüm 3.3; 21 PDF sayfası, 22 tablo, 14 görsel. Eski HTML ve bölüm 4/6 belgeleri pakete alınmadı; silinmedi.
- **Kanıt ZIP'i:** `FDR/JURI/NAVITAS_FDR_3_3_KANIT_PAKETI.zip`; 542 dosya, 540 kaynak arşiv içinden SHA-256 ile doğrulandı. Özet: `5ef663e9955661095853552f2f659d87e4281ef857267263ac23d2b06300dde2`.
- **Veri:** 6 DataFlash, 13 Mission Planner tlog, 14 ARM penceresi, 105 simülasyon, 6 gerçek RF probu, Jetson kısa/uzun ölçümleri, gerçek 29 kare matrisi, video ve 42 simülasyon waypoint'i. Çıkarımlar `results/fdr_33_20260914/` altında.
- **YKS:** gerçek GNSS kaydı `demo=False` ile gösterildi; canlı uçuş/İKA/ACK/rota uydurulmadı. İrtifa referansı ve fix kökeni düzeltildi; bilinmeyen hız/uydu ölçüm sayılmadı. Rota analizinde tüm noktaların yerel koordinatı ve `ref_xy + waypoint` toplamı var. RFD900A etiketleri güncel. Önceden mevcut video-yok UI değişiklikleri korundu.
- **Genel kapı:** `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B codes/test_rota_sentetik.py` → `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`, çıkış 0.
- **Tam süit:** aynı yorumlayıcıyla `-X utf8 -B -m unittest discover -s tests -v` → `Ran 2925 tests in 603.169s`, `FAILED (failures=7, skipped=13)`, çıkış 1. Son hedefli `-p test_yks_*.py -v` → `Ran 240 tests in 38.953s`, `OK`, çıkış 0. Tam komut/zaman/çıktı: `test_kosum_envanteri.json` ve tarihli test dizinleri.
- **Belge/paket:** aynı yorumlayıcıyla `-X utf8 -B scripts/fdr_33_paketle.py` → `BELGE_OK 22 TABLO 14 GÖRSEL 21 SAYFA`; `PAKET_OK 542 DOSYA 194.87 MiB`; çıkış 0. PDF görsel olarak incelendi; kontrol kayıtları `belge_dogrulama.json`, `paket_dogrulama.json`.
- **Açık doğrulamalar:** fiziksel İKA yok; tam yük güç/kablaj, nihai tartım/maliyet, gerçek arena ışığı, menzil ve erişilebilir video URL'si yok. Başarısız testler raporda açık; tam süit geçti denmedi.
- T107/T260 ve diğer ajan kilitleri değişmedi. Commit/push yapılmadı. Kullanıcının diğer dosyaları silinmedi.

## 14 Eylül 2026 09:06 — Yakın kamera / 1080p CAD videosu

- **Yazan:** Codex · **Denetleyen:** bağımsız denetim bekleniyor. Kullanıcının doğrudan isteği; görev kapatma yok.
- Yeni teslim: `FDR/JURI/video/navitas_cad_sinematik_1080p.mp4`; 1920×1080, 25 FPS, 4300 kare, 172 s, 73.116.073 bayt. SHA-256 `e79fafd41a8462a21fa575cdb9976afe111e5d18b220075d0a4abb17a5afd44d`. Tüm kareler yeniden okunarak doğrulandı.
- Üretim komutu: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B scripts/fdr_33_sinematik_video.py --render` → `SINEMATIK_VIDEO_OK 4300 KARE 172.0 s`, çıkış 0. Künye ve yeni qpos/qvel kayıtları `results/fdr_33_20260914/cad_video_sinematik/` altında.
- Magenta İHA yakın takip, 150° dönen üç CAD incelemesi, orijinal 1 Hz nadir görüntüsü, İKA yerel koordinat/GT rota paneli eklendi. Işık/kamera değişikliği sunum içindir; algı girdisi özgün kayıttır. İHA kinematik, İKA basitleştirilmiş fizik; CAD atalet/aerodinamik doğrulaması değildir.
- Yeni model koşusu NO_ROUTE / başarısız; GT koşusu başarılı, 63,5 s sürüş, 100,68 s görev, sıfır temas, HB 0,211 m. GT model başarısı sayılmadı. Eski test/video sonuçları değiştirilmedi.
- `scripts/fdr_33_test_kaydi.py --sinematik` izinli tekrar: genel iki kol 15/15; yeni 5 test `OK` (1,431 s), CAD 10 test `OK` (2,221 s), mevcut video 13 test `OK` (0,581 s); her biri çıkış 0. Ham kayıt: `test_20260914_090018/`. İlk sandbox denemesinde video testi izin hatası verdi; kayıt `test_20260914_085621/` altında korunur.
- Önceki birleşik DOCX/PDF ve ZIP bu 1080p videoya henüz güncellenmedi. Kullanıcı video bitince durup devam mesajını beklemeyi istedi; rapor çalışmasına devam edilmedi. Eski 60 MB video sınırı bu yüksek çözünürlüklü teslimde karşılanmıyor; karşılandı denmedi.

## 14 Eylül 2026 — CAD hareketli parça onarımı / video tamamlandı

- **Yazan:** Codex · **Denetleyen:** bağımsız denetim bekleniyor; görev kapatma yapılmadı. Kullanıcının doğrudan eklem/CAD hata bildirimi ele alındı.
- **Teslim:** `FDR/JURI/video/navitas_cad_eklemli_1080p.mp4`; 1920×1080, 25 FPS, 4300 kare, 172 s, 71.320.847 bayt. SHA-256 `ffc79cd8b3db9537bb39b7cbdf0ea43e6fc78c32b44adedb62c00e8d18000a10`. Tüm kareler yeniden okundu; teslimden kanatçık/teker yakın planları ayrıca incelendi. Önceki videolar korunur.
- **Kök nedenler:** CAD görselleri gövdeye sabit eklenmişti; İKA'nın dört teker STL'si ve kamera STL'si ayrı ayrı 26.594 mükerrer gövde üçgeni içeriyordu. Bağlı bileşen seçimiyle lastik/jant/kamera ayrıldı; kaynak STL/URDF değiştirilmedi. MuJoCo derleyicisinin `geom_sameframe=BODYROT` kısayolu ikinci pervanenin dönüşünü ayrıca engelliyordu; hareketli görsellerde kısayol kaldırıldı.
- **Hareket kökeni:** 2 pervane + 4 kumanda yüzeyi + 4 teker = 10 bağımsız eklem, jantlarla 14 hareketli mesh. URDF pivot/eksenleri kullanılır. İKA sürüş açısı özgün `cad_video_sinematik/kosum` qpos kaydıdır. İHA pervane/servo ve stüdyo hareketleri TEMSİLİDİR; gerçek RPM/servo telemetrisi, aerodinamik doğrulama veya yeni fizik koşusu değildir. Görüntüde açıkça yazılıdır.
- **Model teşhisi:** `scripts/fdr_33_model_teshis.py` aynı v36 SHA, imgsz=512, eşik=0,15 ve aynı 15 kare ile tekrarlandı. Mozaik SHA eşleşir; 269.752 zemin / 359.404 engel pikseli, 0 waypoint, `BELIRSIZ_TEK_KAPI` birebir tekrarlandı. Algı başarısızlığı düzeltilmiş sayılmadı; GT yerine konmadı. Komut çıkışı 0 yalnız teşhis betiğinin tamamlanmasıdır, görev başarısı değildir.
- **Kapı:** `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B scripts/fdr_33_test_kaydi.py --eklemli` → genel iki kol 15/15; 11 hareket testi `OK` (3,965 s), 5 sinematik testi `OK` (1,450 s), 10 CAD testi `OK` (2,041 s); her biri çıkış 0. Ham kayıt `results/fdr_33_20260914/test_20260914_093849/`. İlk denemedeki ikinci-pervane testi başarısızlığı `test_20260914_093050/` altında korunur; kusur onarıldıktan sonra tekrar geçti. Tam süit yeniden koşulmadı.
- **Video komutu:** aynı yorumlayıcıyla `-X utf8 -B scripts/fdr_33_sinematik_video.py --eklemli --render` → `SINEMATIK_VIDEO_OK 4300 KARE 172.0 s`, çıkış 0. Önizleme ve 14 mesh hareket kanıtı `cad_video_eklemli/eklem_kaniti.json`; uçuş görünürlüğü 50 örneğin 46'sında eşiği geçti.
- `simulation/mujoco/cad_hareket.py`, `scripts/fdr_33_cad_teshis.py`, `scripts/fdr_33_model_teshis.py`, `tests/test_fdr_33_cad_hareket.py` eklendi; sinematik betik ve test kayıt betiği güncellendi. DOCX/PDF/ZIP güncellenmedi. Video tamamlandığından kullanıcının devam mesajı beklenir. Commit/push ve kilit değişikliği yok; 60 MB eski sınır hâlâ karşılanmıyor.

## 21 Eylül 2026 07:4x — SAHA DEVRİ (Adıyaman, yarışma günü) · mimar

- **Yazan:** mimar (Claude 1) · **Denetleyen:** bağımsız denetim BEKLİYOR. Görev kapatma yapılmadı, üretim kodu değiştirilmedi.
- **Bağlam:** takım sahada. Yarışma 21–25 Eylül, Adıyaman Üniversitesi Stadyumu. Takımın kendi slotu hâlâ insan teyidi bekliyor (D-517).

### Nerede çalışılıyor

**Dal: `saha-kanit-20260921`** (= eski yerel `master` + iki commit). `O:\navitas` bu dalda. Uzağa itildi: `origin/saha-kanit-20260921`.
`origin/master`'a **dokunulmadı**. Yerel/uzak iraksaması duruyor: `origin/master` 110 ileri, bu dal 83 ileri. Birleştirme **yapılmadı** — kullanıcı kararı ("şimdilik dokunma").

### Bu oturumda yapılanlar

1. `31294606` — iki takipsiz kanıt dizini kayıt altına alındı:
   `results/yks_baglanti_20260920_205239/` (20 Eyl 67 dakikalık gerçek saha oturumu) ve
   `results/jetson_20260919/` (Jetson'a **fiilen kurulan** dosyalar). `.gitattributes`'a `-text`:
   kanıt değeri sha256'da olduğu için satır sonu dönüşümü yasaklandı. Blob sha == disk sha doğrulandı
   (`6fe5819b`, `3bc18e5d`). `REVIEW_LOG.md` D-505…D-516 de bu commit'te.
2. `a4129a79` — saha dizini tamamlandı. Önceden hiçbir git çizgisi tam FDA zincirini içermiyordu.
   Getirilenler: `scripts/yer_yonlendirici.py`, `SAHA_YKI_BASLAT.cmd`, `scripts/fda_gorev_uret.py`,
   `scripts/kamera_odak_olcer.py`, `codes/kare_keskinligi.py`, `scripts/tezgah/odak_onizleme.py`,
   `SAHA_20260920/`, iki nöbetçi test.
3. `REVIEW_LOG.md` **D-524** — bu oturumun tüm ölçümleri, çürütücü ölçümleriyle birlikte.

### Koşulan kapılar (gerçek çıktı)

- `codes/test_rota_sentetik.py` → **GENEL KAPI: GEÇTİ — kol1 15/15 · kol2 şerit 15/15**, çıkış 0
- `tests/test_t235e_fda_gorev_ureteci.py` → Ran 7, OK
- `tests/test_yer_yonlendirici_yeniden_baglanti.py` → Ran 6, OK
- `SAHA_20260920/test_rota_testi_yeniseq.py` → Ran 5 in 65,5 s, OK
- Yedi saha aracı `--help` ile çalıştırıldı, rc=0 (eksik import yok)
- **Tam süit KOŞULMADI.** Geçti sayılmaz.

### Açık durum — uçuştan önce bilinmesi gerekenler

- 🔴 **Kamera odağı BULANIK.** Depodaki tek gerçek saha karesi: keskinlik **3,6** (NET eşiği 100), Canny kenar oranı %0,00000. 20 Eyl oturumunda 4112 kare `MASKE_YOK`. Kullanıcı bu maddeyi **"geç"** dedi; kapanmadı.
- 🔴 **Odak tek sebep değil.** NET bir karede (2139,9) bile üretim eşiği `conf=0.30` ile zemin %0; aynı karede `conf=0.05` zemin %20,2 veriyor ama güvenler 0,126–0,202. Kabul kümesinde aynı model 0,92 veriyor. **Eşik gevşetilmez** (madde 15: serbest alan büyütülemez).
- 🟠 **YKS→İHA komut bacağı** 20 Eyl'de 12/12 düştü (11 ARM, 1 RTL: "güçlü ACK gelmedi"). Kullanıcı bu maddeyi **"yapıldı"** olarak bildirdi; depoda doğrulayıcı yeni kanıt YOK.
- 🟠 **Hakem onayı canlı provası** kullanıcı tarafından **"yapıldı"** bildirildi; depoda kanıt YOK. `UYGUNLUK_OLCUMU.md` L5 hâlâ AÇIK yazıyor.
- 🟡 **T18** çalışma ağacında commit'siz duruyor ve `67467c4f`'in daha zayıf ikinci uygulamasıdır (493 satır fark). Jetson'da `67467c4f` sürümü koşuyor. **Karar verilmedi.**
- 🟡 Bu çizginin inference'ı görev kaydına `keskinlik` yazmıyor (Jetson'a kurulu sürüm yazıyor) → odak teşhisi canlı kayıttan izlenemez.

### Saha komutları (internetsiz çalışır)

```
odak:     O:\navitas-local-train\venv\Scripts\python.exe scripts\kamera_odak_olcer.py --url http://127.0.0.1:8080/kare.jpg
görev:    ...\python.exe scripts\fda_gorev_uret.py --kose LAT LON (x4) --montaj-yaw <OK TESTİ> --cikti gorev.waypoints
          ⚠ 21 Eyl REVİZYON: +90 GEÇERSİZ. Açı döndürülmüş videoda ok testiyle ölçülür (üst → 0, alt → 180).
          Ayrıntı: SAHA_20260920/MONTAJ_YAW.md REVİZYON 3 ve REVIEW_LOG D-524 ek 7.
YKİ:      SAHA_YKI_BASLAT.cmd        (ÖNCE Mission Planner'ı COM portundan AYIR)
kapı:     ...\python.exe -X utf8 -B codes\test_rota_sentetik.py
```

### Sıradaki iş

- 8 alanlık tam yazılım taraması başlatıldı, **7 alan oturum limitinde düştü** (algı · rota/ölçek · taşıma · YKS · Jetson dağıtımı · uçuş parametreleri · kapılar/testler). Yalnız `saha` alanı tamamlandı; bulguları D-524'te. Tarama önbellekli, `resumeFromRunId` ile kaldığı yerden sürer.
- Gerçek stadyum zemininden **NET** bir kare alınıp modelin çevrimdışı koşulması — D-524 Kanıt 5'in çürütücü ölçümü budur ve L1 hükmü buna bağlıdır.
