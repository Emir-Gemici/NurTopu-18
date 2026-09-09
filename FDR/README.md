# FDR — FİNAL DEĞERLENDİRME RAPORU (taslak v1 · 3 Eylül 2026)

> **NAVITAS** · TEKNOFEST İleri Otonom Sistemler Tasarım ve Operasyon Yarışması
> Şartname **§5.3.1**, Tablo 4. Final notundaki ağırlık:
> `FDA = FDR × 0,85 + Drone ile Görev Test Uçuşu × 0,15`
>
> Bu klasör **rapor kaynağıdır**; teslim dosyası bu bölümlerden derlenir.

---

## 📌 TAKIM ARKADAŞLARI — BURADAN BAŞLA

Bu klasör ortak sürücüde paylaşıldı. Sırayla üç şey yap:

1. **`TAKIM_PROMPT.md`** dosyasını aç, içindeki prompt'u kopyala, kendi yapay
   zekâna (**Claude Sonnet 5**) yapıştır.
2. Yanına **üç dosya** ekle: sorumlu olduğun `BOLUM_N_*.md`,
   **`YONERGE_HARITASI.md`** ve **`BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md`**.
3. AI sana soru soracak — cevapla. Sonra bölümünün **yamasını** üretecek.
   O çıktıyı olduğu gibi bana ilet; birleştirmeyi ben yapacağım.

**Üç kural, bunlar tartışmaya kapalı:**

- 🔴 **Rapora İSİM YAZILMAZ.** Yönerge Bölüm 2.1 kişisel veriyi (isim, görsel)
  yasaklıyor; anlatım **rol bazlı** olacak (R1 Kaptan, R2 Pilot, … R8).
- 🔴 **Bilmediğin sayıyı yazma.** `BEYAN GEREKLİ (insan): …` diye bırak.
  Açık kalması kusur değil; **uydurulmuş olması** kusur.
- 🔴 **Başlık icat etme.** Başlık adları ve numaraları **yönergeden birebir**
  gelir; hepsi `YONERGE_HARITASI.md` içinde `Y-…` kimlikleriyle listeli.

**Dosyayı doğrudan düzenleme** — yamayı bana gönder. Yedi kişi aynı dosyaya
yazarsa çakışır ve ölçüm bağlantıları kopar.

---

## Bu klasörde ne var

| dosya | ne işe yarar | rapora girer mi |
|---|---|---|
| `BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` | kapak, versiyon tablosu, tanımlar ve kısaltmalar | ✅ evet |
| `BOLUM_1…7_*.md` | yönergenin yedi puanlanan bölümü | ✅ evet |
| **`YONERGE_HARITASI.md`** | **zorunlu iskelet + boşluk analizi** — hangi gereksinim var, hangisi yok | ❌ çalışma belgesi |
| `TAKIM_PROMPT.md` | üyelerin kendi AI'larına yapıştıracağı prompt | ❌ çalışma belgesi |
| `ACIK_KALEMLER.md` | elle ayıklanmış açık kalemler | ❌ çalışma belgesi |
| `ACIK_KALEMLER_HAM.md` | betikle üretilen ham liste (elle yazılmaz) | ❌ çalışma belgesi |

Yönergenin kendisi: `FDR_2_qNiVF.pdf` (depo kökünde) ·
metni: `results/fdr_sablon/fdr_yonerge_metin.txt`

## 🔴 Resmî yarışma takvimi (şartname Tablo 1 — tek doğru kaynak)

| tarih | ne |
|---|---|
| **21.09.2026 · 17.00** | **FDR SON TESLİM** — bu raporun teslim anı |
| **30.09 – 03.10.2026** | **Final Değerlendirme Aşaması**: FDS sunumları + **Drone ile Görev Test Uçuşu** (§5.3.2, tek atış) |
| 04.10.2026 | FDR sonuçları ve maddi destek açıklaması |
| 05.02.2027 · 17.00 | SGGS son teslim |
| 16.04.2027 · 17.00 | UHDR son teslim |

⚠ **Sık yapılan hata (bu raporda bir kez yapıldı ve düzeltildi):** 21 Eylül
**uçuş günü değildir**; FDR'ın teslim günüdür. Takım o gün Adıyaman'da **kendi
provasını** yapar. Şartnamenin zorunlu görev test uçuşu 30 Eylül–3 Ekim
penceresindedir. Kaynak: `results/sartname_bosluk/sartname_metin.txt` satır 353–362.

## Bölümler ve puanlar

| bölüm | konu | puan | dosya | durum |
|---|---|---:|---|---|
| 1 | Özet | 5 | `BOLUM_1_OZET.md` | taslak |
| 2 | Organizasyonel Yapı ve Proje Takvimi | 5 | `BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` | taslak |
| 3 | Genel Sistem Spesifikasyonları | **40** | `BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` | taslak |
| 4 | Test Faaliyetleri | 15 | `BOLUM_4_TEST_FAALIYETLERI.md` | taslak |
| 5 | Üretim Faaliyetleri | 15 | `BOLUM_5_URETIM_FAALIYETLERI.md` | taslak |
| 6 | Gereksinim İzlenebilirliği ve Değerlendirme | 10 | `BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` | taslak |
| 7 | Bütçe Gerçekleme Analizi | 10 | `BOLUM_7_BUTCE_GERCEKLEME.md` | taslak |

## Bu raporun yazım kuralları (projenin kendi disiplini)

Şartname §5.3.1 raporun **kanıt sunmasını** ister. Bu klasördeki her bölüm aynı
dört kurala uyar; kurallar rapor için icat edilmedi, projenin ölçüm defterinden
(`REVIEW_LOG.md`, **420 kayıt**) gelir:

1. **Her sayı bir artefakttan gelir.** Bölüm sonundaki *Kanıt dizini* her sayının
   dosya yolunu ve onu üreten betiği verir. Elle kopyalanan sayı bayatlar; bu
   projede bayat sayı taşıma kusuru birden çok kez kayda geçti.
2. **Ölçülemedi ≠ Geçti.** Koşulmamış bir kapı "sorun çıkmadı" diye yazılmaz;
   paydası olmayan oran rapora girmez.
3. **Geçilmeyen kapı geçilmedi diye yazılır.** Üretim modeli v36, gerçek uçuş
   karelerinde kendi ön kayıtlı eşiklerinin ikisini **geçmeden** terfi etti; bu
   rapor bunu gizlemez, gerekçesini ve bedelini yazar.
4. **Sentetik ölçüm saha başarımı diye sunulmaz.** Arena ölçümlerinin tamamı
   sentetiktir; elimizde gerçek arena karesi yoktur ve bu sınır her bölümde
   tekrar edilir.

## İki ayrı araç — karıştırılmaz

| | görev test uçuşu (§5.3.2) | yarışma görevi (§2.2) |
|---|---|---|
| tarih | **30 Eylül – 3 Ekim 2026** (şartname Tablo 1) · takım provası **21 Eylül**, Adıyaman | final haftası |
| araç | **çoklu rotorlu drone** (3B baskı quadcopter) | **sabit kanat** + mancınık + paraşüt |
| yer aracı | yok | İKA |
| süre | kalkış→iniş **≤ 10 dk** | İHA 15 dk · İKA 10 dk |
| aktarım | YKS'ye canlı + hakem onayı | YKS **ve** İKA'ya, İHA havadayken |

Algı, karar, haberleşme ve yer istasyonu katmanı **iki araçta da aynıdır**;
değişen uçuş kontrolcüsü yapılandırması ve gövdedir. Yer istasyonu bu ayrımı
`--fda` bayrağıyla tanır (CONTRACTS §6.7).

## Sayı künyesi (bu taslağın ölçüm anı)

| ölçüt | değer | ölçüm |
|---|---|---|
| genel kapı `codes/test_rota_sentetik.py` | **15/15 · 15/15** | 3 Eylül 2026 |
| tam test süiti | **1896 test OK** (3 atlandı, 390,5 s) | 3 Eylül 2026 |
| kanıt defteri kaydı | **420** (`REVIEW_LOG.md`, `### D-` sayımı) | 3 Eylül 2026 |
| üretim modeli | `navitas-seg-v36-512` (PyTorch, 512 px) | `config/model_registry.json` |
| Jetson paketi | 18 dosya, kanonik kaynakla bayt-eş | `scripts/jetson_paket_hazirla.py` |
| Jetson kartı ve FPS kapısı | **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Python 3.12) — 3 Eylül beyanı 'Nano 4GB' yanlışlandı; `scripts/jetson_fps.py` 120 örnek: pt p50/p95 **1,35/1,06 FPS** · engine **1,58/1,33 FPS**, eşik 0,61 → GEÇTİ; engine↔pt denkliği D-303 oransal 3/126 **DÜŞTÜ** → uçuş `.pt` | 6 Eylül 2026 — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`, `results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json` (D-431) |

⚠ Bölüm içindeki tablolar **yazıldıkları andaki** koşumu gösterir (ör. Bölüm 3 ve 4'te
1875, D-408 anının sayısıdır; aradaki 7 test saha belleği kapılarıdır). Sayı ilerlemesi
Bölüm 2'de tarihli olarak izlenir — bu bir tutarsızlık değil, ölçüm zinciridir.

## Kaynaklar

`REVIEW_LOG.md` (kanıt defteri) · `CONTRACTS.md` (bağlayıcı sözleşmeler) ·
`results/` (ölçüm çıktıları, ham) · `results/fdr/GORUNTU_ISLEME_KANIT.md`
(üreteç: `scripts/olcum/167_fdr_kanit_paketi.py`) ·
`SAHA_HAZIRLIK_PLANI_20260903.md` (donanım künyesi ve takvim) ·
`results/sartname_bosluk/rapor.md` (yükümlülük haritası).

## Açık kalemler (rapor teslimden önce kapanacak)

- **BEYAN GEREKLİ (insan):** ~~ekip isimleri ve rol ataması~~ (kalem #17 **düştü** —
  yönerge Bölüm 2.1 kişisel veriyi yasaklar, rapor rol bazlıdır; D-417, 10 Eylül
  düzeltmesi), birim fiyatlar ve
  tedarik durumu, 3B baskı süreleri, ölçülen gerçek kütleler.
- **ÖLÇÜLECEK (cumartesi ve sonrası):** ~~Jetson Nano gerçek FPS~~ (6 Eylül'de Orin Nano üzerinde ÖLÇÜLDÜ, GEÇTİ — D-431), SiK RF menzili,
  uçuş testleri, gerçek arena/HTAB karesi.
- Bölüm 1 özeti, diğer altı bölüm kesinleştikten **sonra** son hâlini alır.
