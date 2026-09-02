# FDR — FİNAL DEĞERLENDİRME RAPORU (taslak v1 · 3 Eylül 2026)

> **NAVITAS** · TEKNOFEST İleri Otonom Sistemler Tasarım ve Operasyon Yarışması
> Şartname **§5.3.1**, Tablo 4. Final notundaki ağırlık:
> `FDA = FDR × 0,85 + Drone ile Görev Test Uçuşu × 0,15`
>
> Bu klasör **rapor kaynağıdır**; teslim dosyası bu bölümlerden derlenir.

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
(`REVIEW_LOG.md`, 413 kayıt) gelir:

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
| tarih | **21 Eylül 2026**, Adıyaman | final haftası |
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
| tam test süiti | **1882 test OK** (3 atlandı, 375,5 s) | 3 Eylül 2026 |
| kanıt defteri kaydı | **414** (`REVIEW_LOG.md`, `### D-` sayımı) | 3 Eylül 2026 |
| üretim modeli | `navitas-seg-v36-512` (PyTorch, 512 px) | `config/model_registry.json` |
| Jetson paketi | 18 dosya, kanonik kaynakla bayt-eş | `scripts/jetson_paket_hazirla.py` |

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

- **BEYAN GEREKLİ (insan):** ekip isimleri ve rol ataması, birim fiyatlar ve
  tedarik durumu, 3B baskı süreleri, ölçülen gerçek kütleler.
- **ÖLÇÜLECEK (cumartesi ve sonrası):** Jetson Nano gerçek FPS, SiK RF menzili,
  uçuş testleri, gerçek arena/HTAB karesi.
- Bölüm 1 özeti, diğer altı bölüm kesinleştikten **sonra** son hâlini alır.
