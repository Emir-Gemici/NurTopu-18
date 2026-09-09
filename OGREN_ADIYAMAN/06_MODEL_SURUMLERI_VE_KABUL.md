# 06 · MODEL SÜRÜMLERİ VE KABUL — v21'den v36'ya, kapılar, terfi kararı, export (Ağustos 2026)

> Kaynaklar: `config/model_registry.json` (tek doğruluk kaynağı: profil, sha, `_surum_karari`, `metrics`, `_yedek_surumler`) · `scripts/olcum/65_kabul_denetcisi.py`
> · `results/terfi_v36/rapor.md` · `results/gece_20260826/ON_KAYIT.md` · `results/fdr/GORUNTU_ISLEME_KANIT.md` · `CONTRACTS.md` §10, §12 ·
> `REVIEW_LOG.md` D-107, D-116, D-131, D-136, D-140, D-182, D-256, D-293/294, D-303, D-332/333, D-371, D-375–D-377 · `ozet/F_model_veri_egitim.md`.

---

## Seviye 1 — Bir cümle ve büyük resim

Ağustos'ta model her 1–4 günde bir değişti: **v21 (5 Ağu) → v24 (13) → v27 (14) → v30 (15) → v34 (19) → v35 (21) → v36 (26 Ağu)**. Her
terfi **ön kayıtlı kapılarla** (K0–K8) ölçüldü, kararı **insan** verdi (D-133 kuralı). Bugünkü üretim modeli **v36** (`navitas-seg-v36-512`,
YOLOv8m-seg, 512, sha `1d1caca6…6911`); yedekler v35, v34. v36 sentetik kabul zincirini 10/10 geçti ama gerçek kare kapısının **iki eşiğini
geçmeden** kullanıcı kararıyla terfi etti; bu istisna sözleşmeye yazıldı, eşikler değişmedi. Uçuş `.pt` ile; FP16 engine karar denkliğini
geçemedi.

## Seviye 2 — Sürüm sürüm ne oldu

| sürüm | tarih | değişen | ölçülen | karar |
|---|---|---|---|---|
| **v21** gerçek doku | 5 Ağu (141 dk) | v17 + copy_paste_gercek 393 | 67/67 kullanılabilir; ONNX parite 30/30 | üretim 5–13 Ağu |
| v22/v23 | 19 Ağu hüküm | 11 sınıf ön-eğitim + gerçek karışım / `rescuenet_2sinif_engelli` (T54) | v23 K0 %0,5 · K2 12/258 | v23 → v34 |
| v24 doku | 13 Ağu | doku değişikliği | T66'da rota 196/260, moloza basma %31,1 (dağılım dışı) | üretim 13–14 Ağu |
| v25 renk | 14 Ağu | renk sadakati | sentetikte kusursuz, gerçek figürde **tam kör** | RED (D-95) |
| **v27** | 14 Ağu | T66 ada geometrisi; 640 eğitim, 512 çıkarım (D-112) | K0–K5 hepsi GEÇTİ — **ilk ön kayıtlı kabul** (D-107) | üretim 14–15 Ağu (`last.pt`: `best.pt` epoch 43'te donmuş, D-113) |
| v28 | 15 Ağu | 512 eğitim | kararlılık 9→3/260, K2 %8,2 | kabul, sevk edilmedi |
| v29 | 15 Ağu | gerçek otopark ×12 | gerçek 0/67→64/67 **ama K5 3 px** (ezber) | RED (ön kayıt) |
| **v30** | 15 Ağu | gerçek otopark ×4, 200 epoch, 386 dk | K1 258 · K2 %8,5 · K5 0 · gerçek 65/67 · kararlılık 8/260 | üretim 15–19 Ağu (kullanıcı) |
| v31 | 15 Ağu | tohum 1 | v30 ile **bit-bit aynı** (seed etkisiz, ultralytics) | ölçüm (D-140) |
| v32/v33 | 15–16 Ağu | ×2 / gürültü dayanıklı | kararlılık iyi ama K5 düştü | RED |
| **v34** | 19 Ağu | = v23 (T54 engel eşlemesi) | K0 %0,49 (güven çöküşü) · çatı kaçağı 0,96 | üretim 19–21 Ağu; terfi yarım kalınca 8 test düştü (hizalama paketi) |
| **v35** | 21 Ağu | t127 temiz: çatı yamalı + kaynak düzeyi temiz bölüm | **ilk kez tam zinciri geçen model** (D-255); çatı kaçağı 0,043 | üretim 21–26 Ağu; bugün **1. yedek** |
| **v36** | 26 Ağu | gece_v7a: v35 + DJI ×5, val 73 gerçek kare | aşağıda | **üretim** |
| v37 | 28 Ağu | bariyer degrees=180, ep105 | K0–K7 **geçti**, figürde kaplama %4,4→%56,1 → `ZEMIN_MASKESI_SUPHELI` | **GERİ ALINDI**; K8 doğdu |
| T199 ep27 | 28 Ağu | arena zemin profili | G11 31/88 < 45 | RED |

### 2.1 Terfi kalıbı (D-182, D-256, D-294): "altı hizalama noktası tek commit'te"
Registry (sha, imgsz, kabul kümesi) · Jetson paket aynası · manifest · iki kılavuz · ONNX türevi · testler (`test_model_registry`,
`test_uretim_modeli_hizasi`). v34 terfisinde yalnız defter güncellenince 8 test düştü: "sistem tasarlandığı gibi çalıştı".

### 2.2 v36 karnesi (registry `metrics`, `65_kabul_denetcisi`, 1 Eyl üretim kipi)
| kapı | eşik | v36 |
|---|---|---|
| K0 körlük | figür > 0; boş maske 0/67, 0/393 | %2,66 · 0 · 0 ✓ |
| K1 rota üretilen | ≥ 230/260 | 255 (terfi anı) · 256 ✓ |
| K2 moloza basma | ≤ %15 | %5,88 · 6/256 ✓ |
| K3 ağır basma | ≤ %3 | %0,39 · 0 ✓ |
| K4 arena dışı | ≤ %5 | %1,57 · 2 ✓ |
| K5 / K5A bariyer kesişimi | = 0 px | 0 · 0 ✓ |
| K6 yanlış güzergâh | ≤ %5 | %2,75 · 2/256 ✓ |
| K7 yayınlanan şerit (88 kare) | ≥ %95 ∧ rota ≥ 80/88 | **84/85 = %98,8** · 85/88 ✓ |
| K8 gerçek figür | `ZEMIN_MASKESI_SUPHELI` yok | zemin 0,044, ret `UC_BANT_TEMAS_YOK` ✓ |
| **Gerçek kare (test29)** | ROTA ≥ 10 · MASKE_YOK ≤ 10 · FP ≤ 1 · YANLIŞ = 0 | **8 ✗ · 16 ✗** · 1 ✓ · 0 ✓ |
| ONNX karar denkliği (D-303) | ≤ 5/260 uyuşmazlık | 259/260 ✓ |
| Kararlılık (kapı değil) | — | 14/260 çevrilme (v35 9) — daha kötü, yön fail-closed |
| Genel kapı + süit | 15/15, OK | 15/15, 962 test (terfi günü) |

**Terfi kararı (`_surum_karari`, D-293):** gerçek karede yanlış güzergâh v35 15/21 (%71) → v36 **7/38** (%18); engel üstünde waypoint 79 → 3.
Bedel: K3 0→1, K4 1→4, K6 5→7 (kapı içinde); gerçek kaplama 0,51 → 0,42 (daha az görüyor); val82 FP 0→2 (biri çorak tarlada rota).
Ön kayıtlı iki eşik geçilmedi; kullanıcı "izin veriyorum kurala rağmen" (ON_KAYIT §15); eşik **değişmedi**, `CONTRACTS.md` §12'ye istisna satırı;
üç lensli çürütücü terfi engeli bulmadı. **v35 farklı hata yapar**: arena K3/K4/K6'da daha iyi (0/1/5), val82'de FP üretmez ama gerçek karede
rotayı beton kanal üstünden geçirir.

### 2.3 Kabul zincirinin büyümesi
K0–K5 (D-107, 14 Ağu) → K5 üç durumlu GEÇTİ/DÜŞTÜ/ÖLÇÜLEMEDİ, ÖLÇÜLEMEDİ terfiyi bloklar (D-197: `None`, "düştü" sayılıyordu, kabul denetçisi
her modeli reddediyordu) → K5 popülasyon zemini, **bariyer modelden gelmeyecek** (D-243: aksi hâlde bariyere kör model kapıyı bedava geçer) →
K6 rota yol üstünde (D-290) → K7 yayınlanan şerit (D-316) → K8 gerçek kare (D-333: v37 zinciri geçip figürde çöktü; "zincirin dışında kalan
her kapı bir gün atlanır").

### 2.4 Doğrulama kümesi ve gerçek kare kapısı (`CONTRACTS.md` §12)
`dji/DOGRULAMA/` = DJI 0038 (22 Ağu), 0037/0039 ile GPS örtüşmesi 0; test29 + val82; **eğitime ve erken durdurmaya girmez**; etiket düzeltmeleri
yalnız model çıktısı görülmeden (kör). Terfi ölçütleri: ROTA ≥ 10/29, MASKE_YOK ≤ 10/29, FP ≤ 1, YANLIŞ GÜZERGÂH = 0 (rota çizgisinin sınıf-0 payı ≥ 0,90
∧ sınıf-1 üstünde 0 waypoint). Sınır (bilerek kabul): aynı gün, aynı kamera, kırsal yol — **arena değil**, kırmızı H/moloz/bariyer içermez.

### 2.5 Neden karar ölçülüyor, IoU/mAP değil (`CONTRACTS.md` §10)
1 karar doğruluğu (yanlış güzergâh 0 puan) · 2 moloza basma (İKA bütünlüğü §2.2.6) · mAP/AP50 **reddedildi** · gürültü tabanı sd 0,025–0,032 →
0,04'ten küçük fark gürültü; eşleştirilmiş test n=40, ≥ 35/40 olmadan fark iddia edilmez · "kör model %0 moloza basar — bedava sıfır, başarı değil" (K0).
Maske IoU 0,9975 iken bile karar değişebilir (ONNX 259/260). İki ölçüm hattı (K0): tuval paydası 0,0266 vs içerik paydası 0,0444 — çelişmez, fark
paydadır (`test_k0_iki_olcum_hatti`).

### 2.6 Export hattı
`.pt` → ONNX (PC, `export_tensorrt.py`, imgsz 512, half, opset 17; engine PC'de **bilerek** üretilmez) → `model_registry.py --turev-kaydet` (türevin kendi
sha'sı + `kaynak_sha256`; yer tutucu/yetim = RED) → engine **Jetson'da `.pt`'den** (10 §2.6). **INT8 kararı D-371 (31 Ağu):** sahada FP16; kural "FPS ≥ 3 →
INT8'e girme"; kalibrasyon kümesi hazır, kullanılmıyor. FP16 karar denkliği PC'de (D-375): ilk ölçüm **vakumdu** (`half` sessizce uygulanmadı, 893/893 bit-eş
→ "FARKSIZLIK ≠ DENKLİK"); gerçek ölçüm F1 0, F2 0,9968 GEÇTİ. Jetson engine: F1 0, F2 0,9953, D-303 oransal 3/126 **DÜŞTÜ** → uçuş `.pt` (10 §3.3).

## Seviye 3 — Sayılar, çelişkiler, dürüst sınırlar

- **v36 eğitim:** v35 tabanı; 8 611 train (RescueNet 3 502 + sentetik ~2 700 + t127 344 + DJI ×5 2 065); val 73 gerçek DJI; RTX 5080 Laptop; 17 epoch,
  en iyi epoch 2, 0,654 sa; val mask mAP50 0,387 (kararda kullanılmadı). Reçete kusuru: degrees/flipud/copy_paste 0, lr0 sessizce 0,001667 (D-324).
  Sonuç: bariyeri 0–30°'de %99+, 60–135°'de **%0,0** görüyor → v8/v37 denemesi (degrees 180, 11 saat) figürde taşırdı, geri alındı.
- **Kapı olmayan ölçümler (v36):** çatı kaçağı 0,023 (v34 0,96, v35 0,043); gerçek 67 karede kaplama 0,2346 (tuval) / 0,4171 (içerik); gerçek
  sürülebilir oran tahmini %47–52 → v36 "daha az görüyor"; 51 saniyelik kör aralık (51 kare, 46'sı MASKE_YOK; ikinci blok 45) — hız sorunu değil, model.
- **Çözünürlük 640 denemesi (D-377):** sentetik p 0,9846 → 0,7808, en uzun körlük 51 → 52 kare; ön kayıt "I2 düşerse RED" → RED.
- **Sızıntı (D-376):** gerçek kare havuzunun %62'si eğitim kümesindeydi; sızıntısız p 0,3457 (0038: 0,326) → gereken FPS 0,58–0,61.
- **Tohum (D-140):** ultralytics sabit tohum; v31 = v30 bit-bit; 1,18 saat GPU aynı deney bilmeden tekrarlandı (D-252). Sonuçsuz/reddedilen eğitim
  toplamı ≈ 14,8 saat GPU (FDR Bölüm 7).
- **DOĞRULANAMADI:** sentetik train sayısı 3 003 (yaml yorumu) vs 2 700 (VERI_KAYNAKLARI; log toplamına uyan); FloodNet yol indeksi; v1 reçetesi;
  kabul kümesi ve ağırlıklar depo dışında (`O:\navitas-local-train`), Jetson'da yeniden ölçülemez (K2 için T66 getirilmeli).
- **Registry alanları bilmen gerekenler:** `default_profile: competition` · `model_id` · `path` · `backend: pytorch` · `imgsz 512` · `sha256` · `classes` ·
  `kabul_kumesi` (T66, `O:/…` çıplak PC yolu — K10) · `kabul_kumesi_acili` · `turevler` (engine sha gerçek; FP32 yer tutucu 7 Eyl'de çıkarıldı) ·
  `_surum_karari` · `_yedek_surumler` · `arac_referansi` profili (DOTA OBB, karar modeli değil) · `rpi_ncnn` `legacy-fallback`.

---

## Jüriye 30 saniyede

> "Ağustos'ta yedi üretim modeli değiştirdik; her biri sonuç görülmeden yazılmış kapılarla ölçüldü. Bugünkü v36 sentetik kabul zincirini
> on kapıda geçti, yayınlanan şerit doğruluğu yüzde 98,8. Gerçek kırsal karelerde iki eşiğimizi geçemedi; onu yine de seçtik çünkü
> yanlış güzergâh oranını yüzde 71'den 18'e indirdi ve şartnamede yanlış güzergâh sıfır puan. Bu istisnayı sözleşmeye adıyla yazdık,
> eşikleri değiştirmedik, önceki modeli yedek tuttuk. Kapılarımız sentetik; saha başarımı iddia etmiyoruz."

## Kendini sına

1. Üretim modelinin kimliği (id, mimari, imgsz, sha başı)? Yedekler?
2. Ağustos'taki terfi zincirini tarihleriyle say.
3. v29 neden reddedildi, v30 neden kabul? Ne farkı var?
4. K5 için "bariyer modelden gelmeyecek" neden şart?
5. K7 neden 88 karede; sonucu?
6. v36 hangi eşikleri geçmedi, ne kazandırdı, bedeli ne?
7. v37 nasıl geçip nasıl döndü; hangi kapıyı doğurdu?
8. FP16 denkliğinin ilk ölçümü neden vakumdu?
9. "Altı hizalama noktası" nedir?
10. v36'nın reçete kusuru ve ölçülen sonucu?

<details><summary>Cevaplar</summary>

1. `navitas-seg-v36-512`, YOLOv8m-seg, 512, `1d1caca6…`; v35 (1.), v34 (2.). 2. v21 5 Ağu → v24 13 → v27 14 → v30 15 → v34 19 → v35 21 → v36 26 Ağu. 3. v29 gerçek otopark ×12: gerçek 64/67 ama K5 3 px (ezber) → ön kayıt RED; v30 ×4: K5 0, gerçek 65/67, dört şart sağlandı. 4. Aksi hâlde bariyere kör model kesişim üretmez ve kapıyı bedava geçer; referans sınanan sistemden bağımsız olmalı (D-243). 5. Kabul kümesinin %54'ü koridor kapısı şerit sınırına denk gelip tanım gereği belirsiz; dondurulmuş iyi koşullu 88 karede referans kesin; 84/85 = %98,8. 6. ROTA ≥10 (8), MASKE_YOK ≤10 (16); yanlış güzergâh 15/21→7/38, engel üstü waypoint 79→3; K3/K4/K6 bedeli, kaplama 0,51→0,42, val82 FP 0→2. 7. K0–K7 geçti; şartname figüründe kaplama %56'ya çıkıp `ZEMIN_MASKESI_SUPHELI`; K8 gerçek kare kapısı. 8. Ultralytics predictor ilk çağrıda kurulur, sonraki `half` yok sayılır; iki kol FP32 koşmuş, 893/893 bit-eş → "farksızlık ≠ denklik". 9. Registry, paket aynası, manifest, iki kılavuz, ONNX türevi, testler — tek commit'te. 10. degrees/flipud/copy_paste 0 (defter "t127 birebir" diyordu, yanlış); bariyeri 60–135°'de %0 görüyor.
</details>

## Kaynaklar
`config/model_registry.json` · `scripts/olcum/65_kabul_denetcisi.py` · `results/terfi_v36/rapor.md` · `results/gece_20260826/` · `results/fdr/GORUNTU_ISLEME_KANIT.md` ·
`CONTRACTS.md` §10, §12 · `dataset/VERI_KAYNAKLARI.md` · `ozet/F_model_veri_egitim.md` (139 ölçüm betiğinin listesi §8).
