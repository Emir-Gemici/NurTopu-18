# 13 · FDR HARİTASI — raporun yedi bölümü, ne var ne yok, hangi sayı nereden

> Kaynaklar: `FDR/README.md` · `FDR/YONERGE_HARITASI.md` (Y-kimlikleri, DURUM sayımı) · `FDR/BOLUM_0…7_*.md` · `FDR/ACIK_KALEMLER.md` · `FDR_2_qNiVF.pdf` (yönerge, 19 s.) ·
> `ozet/C_fdr_spec.md` (Bölüm 1+3) · `ozet/D_fdr_test_izlenebilirlik.md` (Bölüm 2, 4, 5, 6, 7) · `ozet/H_sartname.md` §4.3.
> Jüri soruları FDR'den gelecek; bu dosya **hangi bölümde ne iddia edildiğini ve neyin iddia edilmediğini** gösterir. Taslak v1 3 Eylül; son güncelleme 7 Eylül (D-435).

---

## Seviye 1 — Bir cümle ve büyük resim

FDR (Final Değerlendirme Raporu) şartname Tablo 4'ün yedi puanlanan bölümüne göre yazıldı; final notundaki ağırlığı **%85** (`FDA = FDR × 0,85 + uçuş × 0,15`).
Raporun **gücü 3.3 (aviyonik/yazılım), 4 (test) ve 6 (izlenebilirlik)**: ölçülmüş, artefakta bağlı içerik. **En büyük açık 3.1 ve 3.2**: uçuş bilimleri ve yapısal
analiz hiç yazılmadı, İKA ve mancınık yapısal bölümleri boş (40 puanlık bölümün içinde). Rapor dört kurala uyar: her sayı bir artefakttan gelir; ÖLÇÜLEMEDİ ≠ GEÇTİ;
geçmeyen kapı geçmedi diye yazılır; sentetik ölçüm saha başarımı diye sunulmaz. **Rapora isim yazılmaz** (yönerge 2.1: rol bazlı R1–R8).

| bölüm | konu | puan | durum (7 Eyl) | en büyük boşluk |
|---|---|---:|---|---|
| 0 | Kapak · versiyon · tanımlar | — | VAR 2 / KISMEN 2 / YOK 1 | KYS teyidi + logo; TASNİF DIŞI dizgi (18–20 Eyl) |
| 1 | Özet | 5 | 10 KISMEN | İKA/mancınık özeti zayıf; 2–7 kesinleşince yeniden üretilecek |
| 2 | Organizasyon + takvim | 5 | 1 VAR / 3 KISMEN | org. şeması (7 Eyl VAR oldu); DDR takvim teyidi |
| 3.1 | Uçuş bilimleri (sabit kanat) | 40 içinde | **7 YOK** | hiç yazılmadı (CAD/analiz yok; tasarım ekibi işi) |
| 3.2 | Yapısal tasarım/analiz (İHA, İKA, mancınık) | 40 içinde | 8 KISMEN / **48 YOK** | İKA ve mancınık yapısal; FEM (sonuç veri tabanı 33 bayt → ÖLÇÜLEMEDİ) |
| 3.3 | Aviyonik & yazılım | 40 içinde | 7 KISMEN / 4 YOK (+ akış diyagramları VAR) | 3B görev simülasyonu + video; kablaj hesabı; güç tüketimi ölçümü |
| 4 | Test faaliyetleri | 15 | 1 VAR / 6 KISMEN / 5 YOK | menzil, kalibrasyon kanıtı, görev simülasyonu, **arıza emniyet sahada** |
| 5 | Üretim | 15 | 3 KISMEN / 1 YOK | düzeltici prosedürler; **kol reçete farkı gerekçesi (SGGS diskalifiye riski)** |
| 6 | Gereksinim izlenebilirliği | 10 | 3 VAR / 3 KISMEN | pasta grafiği (7 Eyl üretildi); ÖDR/DDR REQ eşlemesi |
| 7 | Bütçe | 10 | 1 KISMEN / 4 YOK | **fiyatların tamamı** (depoda parasal kayıt 0) |

## Seviye 2 — Bölüm bölüm: ne iddia ediliyor

### Bölüm 0 — Kapak, versiyon, tanımlar
Takım "Navitas Autonomous Systems", ID 997827, başvuru 5329027 (DDR döneminden; **KYS teyidi DOĞRULANACAK**). Versiyon V1 03.09.2026. 29 yönerge kısaltması + takım
kısaltmaları (YKS, ACK, OPEN/NO_ROUTE, IHA_LANDED, HEARTBEAT, K0…K8/K5A, SiK, D-NNN, ön kayıt, mutasyon). **FDA** yönergede Final Değerlendirme Aşaması; raporda `--fda`
yazılım bayrağı — aynı harfler, farklı şeyler.

### Bölüm 1 — Özet (10 madde Y-1-M01…M10; ayrıntı `ozet/C_fdr_spec.md` §2)
İki araç ayrımı başa yazılı (FDA quad / yarışma sabit kanat; **yarışma aracı henüz üretilmedi**). Sistem bir cümle: "hangi güzergâhın açık olduğunu havadan bulan ve bu kararı
hakemin canlı doğrulayabileceği biçimde yere aktaran otonom sistem". Y-1-M04 revizyonlar bedelleriyle: v35→v36 eşik geçmeden (ROTA 8, MASKE_YOK 16), gecikme 0,458→0,113 s,
`--fda`, RTL/LAND, çoğullayıcı, İKA sürücü. Y-1-M05 olgunluk iki uçlu: hazır olan (algı→karar→aktarım→onay zinciri, kapılar, Jetson 6 Eyl) ve **hazır olmayan üç şey**:
gerçek arena karesi yok (51 s kör aralık), gerçek İKA sürücüsü yok, SiK hattı hiç ölçülmedi. Y-1-M08 failsafe tablosu (RTL/LAND/çit) "yalnız parametre ve testle kilitli,
sahada test edilmedi". Y-1-M10 ölçülmüş sonuçlar tablosu (genel kapı, süit 1896 → bayat, K0–K8 10/10, p95 0,113 s, gereken FPS 0,61, kuru koşu 9/1, defter 420 → 424).
Sonunda **kanıt dizini** (her sayı: dosya · betik · tarih) ve BEYAN GEREKLİ listesi.

### Bölüm 2 — Organizasyon ve takvim
Roller R1 Kaptan · R2 Pilot · R3 Aviyonik · R4 Görev bilgisayarı/kamera · R5 YKS operatörü · R6 İKA · R7 Yazılım/görüntü işleme (**eşik değiştirme yetkisi yok**) · R8 Kanıt-kalite
(icra dışı). Kural: kanıt üreten ile onaylayan aynı kişi olamaz. Ölçülmüş çakışma: R2 ve R5 uçuş anında eşzamanlı → ikinci kişi BEYAN GEREKLİ. Takvim: FDR 21.09 17:00 UYGUN
(`test_fdr_takvim_kapisi` 4/4); D-410 düzeltmesi; kilometre taşları (24 Haz v2 … 26 Ağu v36 … 3 Eyl D-410/413/414); 560 commit (4 Eyl; "551" sayısı yeniden üretilemedi,
ÖLÇÜLEMEDİ bırakıldı); 5 Eyl → 30 Eyl plan; uçuş bütçesi ≥ 7 uçuş / ≥ 4 gün; DDR→FDR revizyon tablosu (Pixhawk 6X→6C, Orin NX→Orin Nano, M10→M9N, Crossfire→FS-i6, …);
riskler; açık kalemler. Kanıt defteri üç okuması (414/408 · 420/414 · 424/418) üçü de bırakıldı.

### Bölüm 3 — Sistem spesifikasyonları (193 KB; `ozet/C_fdr_spec.md` §3)
- **3.0.2 DDR→FDR:** Orin NX 16 GB → Orin Nano DevKit 4 GB (D-431); YOLOv8-seg nano/NCNN/640 → **YOLOv8m-seg v36, 512**; İKA RPi 5 tedarik edilmedi.
- **3.1:** sabit kanat; depoda artefakt yok; hepsi BEYAN GEREKLİ ("DDR'den beri değişmedi" beyanı bile eksik).
- **3.2.1.1 FDA aracı künyesi** (09 §2.1); **3.2.1.1.1 itki bütçesi** (D-435, T211): X2220 4S+1047 tam gaz 2130 g @ 38,4 A (sınır 38 A/30 s), 4× = 8520 g; kapı ÖLÇÜLEMEDİ.
- **3.2.2 İKA / 3.2.3 mancınık:** donanım tedarik edilmedi; yapısal tasarım yok; mancınık primitif SDF.
- **3.3.1 mimari:** İHA bağlantı şeması 7 Eyl (`sekiller/iha_baglanti.svg`); İKA şeması yok; protokol, mesajlar, K1, `ref_tip`, `karar_yas`; güç/sinyal topolojisi; **5 Eylül kutu**
  (PM06, PX4→4.5.7, motor testi beyan); çoğullayıcı §7.4 (gerçek Pixhawk'ta koşulmadı); SiK hub; T207 akış isteği; FC yapılandırması 48 parametre (Bölüm 1 "31" der —
  tutarsızlık); Jetson yığını D-431; kamera köprüsü; systemd; FPS 1/(5·p) → 0,61; 6 Eyl FPS; mühür v2 (17 Eyl); BOM ağırlık/maliyet boş; kuru koşu 9/10.
- **3.3.2 kablaj/güç:** AWG/uzunluk/akım/gerilim düşümü **YOK**; tam yük/hover akımı ÖLÇÜLEMEDİ.
- **3.3.3 simülasyon:** Gazebo iskeleti var; CAD yok, koşum yok, video yok → **ÖLÇÜLEMEDİ**.
- **3.3.4.1 algoritma akışı:** zincir (`run_camera`), değişmez, ince bariyer, üç çerçeve, ölçek, sabitler, C-uzayı 1/7→6/7, histerezis, 15 ret kodu, ARM kilidi, onay 1/2–2/2,
  İKA kilidi, varış, süreler, FDA kipi, 5 akış diyagramı 337/337 düğüm (Y-3.3.4-M01 VAR).
- **3.3.4.2 görüntü işleme:** v36 künyesi; ONNX 259/260; K0–K8 10/10; geçilmeyen gerçek-kare eşikleri; karışıklık matrisi 7 Eyl (test29: IoU zemin 0,4922, engel 0,7400;
  %39,6 piksel etiketsiz); ışık/gölge kesiti ÖLÇÜLEMEDİ.
- **3.3.4.3 haberleşme:** tek satır JSON, CRC yok; heartbeat alanları; hakem kaydı 16 olay; tekrar aralıkları; komut hattı 42 test (sahte Pixhawk); gecikme 84,8/113,2 ms;
  ÖLÇÜLEMEDİ: SiK RTT/kayıp/menzil, gerçek COMMAND_ACK, kamera gecikmesi.
- **Beyan/ölçüm ayrımı:** motor, pervane, ESC, PM06, pil 25C, motor testi 4/4, accel/level, ESC kal., uçuş modları, SiK bağlantısı, FOV — **BEYAN**; ArduCopter 4.5.7, QUAD/X,
  M9N, IBUS, Jetson kimliği/CUDA/FPS/denklik, karışıklık matrisi, RC_SPEED 490 — **ÖLÇÜM**. Belge içinde 7 bayat paragraf (6 Eyl sonrası güncellenmemiş) — dikkat.

### Bölüm 4 — Test faaliyetleri (`ozet/D_fdr_test_izlenebilirlik.md` §1)
İddia: "en olgun tarafımız ölçüm yordamıdır"; iddia edilmeyen: "hiçbir sayı sahada çalışır demez". 12 gereksinim: 1 VAR, 6 KISMEN, 5 YOK (ekipman kabul, menzil, kalibrasyon,
görev simülasyonu, arıza emniyet). Kapı envanteri: genel kapı iki kol; tam süit tarihli zincir 1896 → 2104 → 2138; K0–K8; gerçek-kare eşikleri geçilmedi; 640 RED; sızıntı; FPS
eşiği; Jetson FPS GEÇTİ; engine denkliği DÜŞTÜ; FP16 PC GEÇTİ (ilk ölçüm vakumdu); histerezis H1 DÜŞTÜ; karışıklık matrisi; P1 MAVLink G1–G7; P2 seri S1–S5 (S5 tampon 1 MiB
DÜŞTÜ → düzeltildi, aynı eşik); hub gecikmesi; T207; uçtan uca p95 0,113 s; komut hattı; kamera köprüsü dayanıklılık; ekransız kip 7/7 mutant; Jetson kuru koşuları; runbook
kapısı (22/22 yeşilken komut EXIT=2 — vakum); saha kuru koşusu 9/1; 5 Eyl tezgâh (ÖLÇÜM/BEYAN karışık); **ÖLÇÜLEMEDİ:** menzil/RTT, IMU/pusula/pitot, arıza emniyet sahada,
görev simülasyonu, uçuş testleri 3.1–3.6. §4.2.1 ön kayıt: 36 artefakt; işe yaradığı 4 olay; kurtarmadığı 1 (v36 "izin veriyorum kurala rağmen" → görünür kıldı).
§4.2.2 mutasyon tablosu (10+ mutant; seri_hub dürüst skor 13/25 → 24/25). §4.2.3 çürütücü turları (D-383, D-405, D-407, D-411, D-421). §4.2.4 vakum denetimi 7 örnek.
§4.13 kalan test borcu (18 kalem; 3'ü 6 Eyl'de kapandı) ve **denetim borcu** ("yazan ile onaylayan aynı taraf": D-407, jetson_baslat, T207, `_kanit_yaz`). §4.13.3.1 kendi hatası
(belge commit'i 16 satır götürdü, D-412). §4.14 kanıt dizini 71 satır. §4.15: "Kanıtlanmamış olan tek şey en önemlisidir: gerçek arenada, gerçek Jetson'da, gerçek telsizle."

### Bölüm 5 — Üretim
FDM 3B baskı (Bambu X1C + P2S), 8 plaka (7 ABS, 1 TPU); ABS vs ABS-CF **çelişkisi** çözülmedi; yalnız 1 plaka G-code'u (1 sa 30 dk, 55,86 g); toplam süre/iş gücü **yazılmadı**;
montaj planı 5 Eyl; Pixhawk yapılandırması; Jetson (D-431 güncel); saha belleği 405 dosya 1,27 GB; **mühür basılmadı** (17 Eyl); final aracı: sabit kanat CAD var, imalat yok,
mancınık CAD/analiz yok; hata prosedürleri **YOK** (Y-5-M04); 🔴 **kol 1–2 (0,20 mm/%15 grid/2 duvar) vs kol 3–4 (0,16 mm/%40 gyroid/6 duvar) reçete farkı gerekçesiz →
SGGS "gerekliliği ispatlanmamış değişiklik" diskalifiye riski**; FEM sonucu okunamıyor; 20 BEYAN GEREKLİ.

### Bölüm 6 — Gereksinim izlenebilirliği (`ozet/D_…` §2)
Durum sözlüğü: KANITLI_TEST / KOD_VAR_TEST_YOK / ÖLÇÜLEMEDİ / İNSAN-DONANIM. Üç kimlik sistemi: § (şartname), R1–R22 (yükümlülük haritası), Y-… (yönerge); **eksik dördüncü**:
ÖDR/DDR REQ eşlemesi yapılmadı. **45 satır: 32 KANITLI (%71,1) · 4 KOD_VAR_TEST_YOK (%8,9) · 2 ÖLÇÜLEMEDİ (%4,4) · 7 İNSAN-DONANIM (%15,6)**; dokuz satır iki etiket taşır;
"%71 kanıtlı = sahada çalıştı **değil**". Doğrulama yöntemi 66 atama: test 39, gözle muayene 11, simülasyon 7, hesaplama 5, analiz 4; müdahale −100 testsiz (listenin eksiği,
kaydedildi). Gereksinim → karar → kanıt 14 satır. **Açık gereksinimler A1–A13** (A10 kapandı): A1 İKA sürücü · A2 SiK hattı · A3 gerçek otonom uçuş · A4 gerçek arena karesi
(rapor tarihinde kapatılamaz) · A5 51 s kör aralık · A6 üç-güzergâh adayı üretim yolunda yok · A7 `mod` alanı · A8 tekrar fırlatma testi · A9 Gazebo temas · A11 `--fda`
bağımsız denetim · A12 otonom paraşüt · A13 Pixhawk failsafe/döküm (RC failsafe DÜŞTÜ). Yedi kalemin kapanma tarihi **verilmedi** ("tarih uydurulmadı"). Geçilmeyen üç kapı:
v36 eşikleri, histerezis H1, motor halkası. Grafikler tablodan üretilir, testle kilitli (`test_gece_sekiller` 11 test, 5/5 mutasyon).

### Bölüm 7 — Bütçe
Depoda parasal kayıt **0** (`grep ₺|fatura|birim fiyat` → 0) → tüm parasal sütunlar BEYAN GEREKLİ, yüzdeler hesaplanamaz; Tablo A FDA BOM 27 satır (kütle tartılmadı); Tablo B
DDR aviyonik 26 satır / 2293 g, 22'sinde değişiklik; Tablo C 8 plaka; Tablo D tedarik 12; Tablo E ertelenen 10 sistem (0 harcandı); **İKA ve mancınık BOM'u hiç yazılmadı**;
ayni kaynak ≈ 14,8 saat sonuçsuz GPU; maddi destek %25 (DDR) / %75 (FDA).

## Seviye 3 — Jüri sorusu geldiğinde hangi bölüme koşacaksın

| soru | bölüm | dosya |
|---|---|---|
| "Model doğruluğunuz?" | 3.3.4.2, 4.8 | `BOLUM_3` §3.3.4.2, `BOLUM_4` §4.8 |
| "Kalite güvenceniz?" | 4.2 (ön kayıt, mutasyon, çürütücü, vakum), 6.2 | `BOLUM_4` §4.2, `BOLUM_6` §6.2 |
| "Gereksinimlerin yüzde kaçı?" | 6.6 | `BOLUM_6` §6.6 |
| "Haberleşme gecikme/menzil?" | 3.3.4.3, 4.9 | |
| "Arıza emniyeti test ettiniz mi?" | 4.12, 1 §Y-1-M08, 6 A13 | "sahada hayır" |
| "Jetson FPS?" | 3.3.1.1.12/15, 4.4 | D-431 |
| "İKA?" | 3.2.2, 6 A1, 4.11 | "donanım tedarik edilmedi" |
| "Takvim / 21 Eylül?" | 2.2 | D-410 |
| "Kim ne yapıyor?" | 2.1 (rol bazlı) | isim yok |
| "Bütçe?" | 7 | "depoda parasal kayıt yok, BEYAN GEREKLİ" |
| "Üretim değişikliklerini nasıl gerekçelendirdiniz?" | 5.5 | kol reçete farkı **gerekçesiz** — dürüst söyle |
| "Simülasyon videonuz?" | 3.3.3, 4.7 | YOK |

**Bilinen metin içi tutarsızlıklar (jüri yakalayabilir; sen önce bil):** Bölüm 1 "31 parametre" ↔ 3.3.1.1.11 "48"; §3.3.1.1.8 kilit ↔ ACIK #23; H1c paragrafı ↔ ACIK #24; §3.4.1 A3
engine ↔ §3.3.1.1.12; kanıt dizini K4/K6 3/256 ↔ tablo 2/256; harita 3.3 "VAR 0" ↔ Y-3.3.4-M01 VAR; TEST_SPECS §5 "imgsz 640" ↔ üretim 512; Bölüm 1 süit 1896 bayat (7 Eyl 2138);
`FDA_PLANI_20260829` "21–25 Eylül uçuş" ↔ 3 Eylül planı; Bölüm 2 risk tablosu "Nano FPS 5 Eylül'de ölçülecek" güncellenmemiş.

---

## Jüriye 30 saniyede

> "Raporumuz yönergenin yedi bölümüne birebir oturur ve dört kurala uyar: her sayı bir artefakttan gelir, ölçemediğimizi geçti saymayız,
> geçmeyen kapıyı geçmedi diye yazarız, sentetik ölçümü saha başarımı diye sunmayız. Güçlü olduğumuz yer aviyonik-yazılım, test ve
> izlenebilirlik: 45 yükümlülüğün 32'si testle kanıtlı, 11 açık gereksinim tarihleriyle listeli. Zayıf olduğumuz yer uçuş bilimleri ve yapısal
> analiz: o bölümler tasarım ekibinin beyanını bekliyor. Bütçede parasal kayıt henüz yok, bunu da öyle yazdık."

## Kendini sına

1. FDR'nin yedi bölümü ve puanları? FDA'daki ağırlığı?
2. Raporun dört yazım kuralı?
3. Rapora neden isim yazılmaz? Roller?
4. 45 satırlık matrisin dağılımı; "%71" ne demek, ne demek değil?
5. A1–A13'ten hangileri kapandı, hangi yedisinin tarihi yok?
6. Bölüm 3.1 ve 3.2'nin durumu; kimin işi?
7. Bölüm 5'teki diskalifiye riski nedir?
8. Bölüm 7'de neden yüzde hesaplanamıyor?
9. İki "FDA" ne?
10. Üç metin içi tutarsızlık say.

<details><summary>Cevaplar</summary>

1. Özet 5, Org+takvim 5, Sistem spesifikasyonları 40, Test 15, Üretim 15, İzlenebilirlik 10, Bütçe 10; FDA = FDR × 0,85 + uçuş × 0,15. 2. Her sayı artefakttan; ÖLÇÜLEMEDİ ≠ GEÇTİ; geçmeyen kapı geçmedi diye yazılır; sentetik saha başarımı değil. 3. Yönerge 2.1 kişisel veriyi yasaklar (D-417); R1 Kaptan … R8 Kanıt-kalite. 4. 32 KANITLI_TEST, 4 KOD_VAR_TEST_YOK, 2 ÖLÇÜLEMEDİ, 7 İNSAN-DONANIM; kapılar koştu ve ayırt edici demek, sahada çalıştı demek değil. 5. A10 (Nano FPS) kapandı; tarihsizler A2, A5, A6, A7, A8, A9, A13. 6. 3.1 7 YOK, 3.2 48 YOK; sabit kanat/yapısal analiz tasarım ekibinin mühendislik işi. 7. Kol 1–2 ile 3–4 farklı baskı reçetesi, gerekçe kayıtta yok; SGGS'de "gerekliliği ispatlanmamış değişiklik". 8. Depoda tek bir fiyat/fatura kaydı yok. 9. Yönergede Final Değerlendirme Aşaması; kodda `--fda` görev test uçuşu kipi. 10. Bölüm 1 "31" vs "48" parametre; TEST_SPECS "imgsz 640" vs 512; süit 1896 (bayat) vs 2138; kanıt dizini K4/K6 3 vs 2; harita 3.3 VAR 0 vs akış diyagramları VAR.
</details>

## Kaynaklar
`FDR/README.md` · `FDR/YONERGE_HARITASI.md` · `FDR/BOLUM_0…7` · `FDR/ACIK_KALEMLER.md` · `results/fdr/GORUNTU_ISLEME_KANIT.md` · `ozet/C_fdr_spec.md` · `ozet/D_fdr_test_izlenebilirlik.md`.
