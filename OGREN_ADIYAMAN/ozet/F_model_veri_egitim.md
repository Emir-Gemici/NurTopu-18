# F · MODEL – VERİ – EĞİTİM HATTI — tarihçe ve bugünkü hâl (kanıtlı özet)

**Hazırlanma tarihi:** 2026-09-10 · **Depo:** `/home/n4vitas/proje/navitas_tam/navitas` · **Okuyucu:** Python bilen, makine öğrenmesi bilmeyen takım üyesi (jüri sorularına cevap verecek kişi).

> **Kanıt kuralı:** Her sayının yanında dosya yolu (+satır) vardır. Depoda bulunamayan ya da çelişen şeyler **DOĞRULANAMADI** diye yazıldı; tahmin yazılmadı. Depoda ham veri ve ağırlık dosyaları (`.pt/.onnx/.engine`) yoktur (`.gitignore`; `dataset/VERI_KAYNAKLARI.md:153-156`); bu belge yalnız depodaki kayıt, log, JSON ve kod üzerinden yazıldı.

---

## 1. Problem tanımı — model tam olarak ne yapıyor?

**Görev (şartname):** İHA 30 m'den arenaya bakar; üç yoldan biri açık, ikisi moloz/bariyerle kapalıdır. Model, kameradaki her pikseli "sürülebilir zemin mi, engel mi" diye boyar; sonra klasik görüntü işleme bu maskeden **açık şeridin numarasını (1 = sol, 2 = orta, 3 = sağ)** ve İKA'nın izleyeceği waypoint'leri çıkarır (`README.md` "Algoritma" bölümü; şerit tanımı `codes/karar_sozlesmesi.py:42-54`, `serit_no()`).

**Model türü:** YOLOv8-seg (Ultralytics) — *örnek segmentasyonu*: nesne kutusu + piksel maskesi üretir. Üretim modeli **YOLOv8m-seg**, 27,24 M parametre, 104,7 GFLOP (`results/gece_20260826/egitim_v7a.log`, "YOLOv8m-seg summary: 192 layers, 27,240,806 parameters"). İlk sürümler YOLOv8n/s idi (`codes/train_seg.py:26`, `codes/train_seg_v3.py:36`).

**Sınıflar (üretim sözleşmesi):**

| id | ad | anlam | kaynak |
|---|---|---|---|
| 0 | `traversable` / zemin | sürülebilir zemin — **otorite katmanı** | `config/model_registry.json:43-46`; `codes/sinif_semasi.py:35-46` |
| 1 | `blocked` / engel | moloz, bariyer, enkaz, bina, ağaç… | aynı |
| 2 | `hedef` (H brandası) | **yalnız etiket üreteci ad alanında** vardır; üretim modeli `nc: 2`'dir | `codes/sinif_semasi.py:37`, `scripts/copy_paste_augmentation.py` docstring; tüm `dataset/karisim_*.yaml` `nc: 2` |

Sınıf-id çakışması (üreteçte 2 = hedef, costmap'te 2 = araç) ölçülmüş bir kusurdu (S2); çözüm `codes/sinif_semasi.py`: costmap katmanları 10'dan başlar (`KATMAN_ARAC = 10`, satır 61) ve `dogrula()` import anında çakışmayı patlatır (satır 85-106).

**Mimari ilke (RESEARCH_NOTES.md §1):** "Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR." Bilinmeyen her şey engel sayılır (fail-safe). Şartname engel listesini "vb." ile açık bıraktığı için nesne-tek-tek-tespit yaklaşımı (A) reddedildi; hibrit C seçildi (`RESEARCH_NOTES.md` §2.1, §3). Araç katmanı ayrı bir hazır ağırlıktan gelir: DOTA `yolov8m-obb.pt` (aynı karede COCO 2 araç / DOTA 93 araç; `RESEARCH_NOTES.md` §2.6; `config/model_registry.json:276-288` `arac_referansi` profili — karar modeli DEĞİL, ölçek referansı).

**Giriş çözünürlüğü:** `imgsz = 512` — hem eğitim hem çıkarım (`config/model_registry.json:9`; karar D-112, `REVIEW_LOG.md:7480-7520`: 384–768 arasında IoU yayılımı 0,027, gürültü tabanı 0,04'ün altında → doğruluk farkı ölçülemedi; 512 Jetson maliyeti 640'ın 0,64 katı olduğu için seçildi). Görüntü önce kare tuvale letterbox'lanır, 512'ye küçültülür (`codes/rpi_inference.py:1915`). `INFER_SIZE` kayıt defterinden türetilir, çıplak sabit değildir (`codes/rpi_inference.py:167-206`).

**Çıktı:** iki maske (`masks[0]` zemin, `masks[1]` engel) → `analyze_path` → `open_path` (1/2/3), `confidence`, `waypoints` (JSON payload; `README.md` "İKA Payload Formatı"). Ölçülmüş olgu: karar yolu yalnız `masks[0]`'ı kullanır; `blocked` AP50'yi 0,4329 → 0,5371'e çıkarmak sistem davranışını hiç değiştirmedi (`RESEARCH_NOTES.md` §2.2).

**Güvenlik yarıçapı (C-uzayı):** `R_GEREKLI_M = 0,70/2 + 0,25 + 0,50 = 1,10 m` (`codes/costmap_path_finder.py:74-87`). Rota, zemin maskesinin bu yarıçapla aşındırılmış hâlinde aranır.

---

## 2. Veri kaynakları — her biri nerede, ne kadar, ne işe yaradı

Yetkili belge: `dataset/VERI_KAYNAKLARI.md` (son güncelleme 2026-08-28, `tests/test_t191_veri_kaynaklari_taze.py` ile kayıt defterine bağlı; satır 8-15).

| # | Kaynak | Boyut | Rol | Depodaki yer | v36'da? |
|---|---|---|---|---|---|
| 1 | **RescueNet** (roads alt kümesi, HuggingFace `asolodin/rescuenet-roads`) | 2.365 train / 294 val / 305 test (`README.md` "Veri Seti" tablosu; `scripts/olcum/11_capraz_dogrulama.py` docstring) | Ana gerçek afet verisi; **zemin sınıfının kaynağı** (`road-clear`=7 → 0, `road-blocked`=8 → 1; `dataset/download_and_convert.py:72` via `VERI_KAYNAKLARI.md:62-72`) | `dataset/download_and_convert.py`, `dataset/rescuenet_yolo/` (diskte yok) | ✅ `rescuenet_2sinif_engelli` biçimiyle: 3.502 train (`VERI_KAYNAKLARI.md:128`) |
| 1b | **RescueNet 11 sınıf** (`rescuenet_11sinif`) | `nc: 10` | Yardımcı görev **ön-eğitimi** (v15) ve "zemin değil → engel" eşlemesi: bina/ağaç/su/havuz/araç → sınıf 1; engel poligonu 850 → 22.356 (26,3×) (`dataset/karisim_t54_engelli.yaml:13-15`; `scripts/olcum/57_t54_engel_eslemesi.py` docstring) | `scripts/olcum/41_cok_sinifli_veri.py` | ✅ |
| 2 | **FloodNet** Track-1 | 798 filtreli train / 257 val (`dataset/combined_data.yaml:2-3`) | Yalnız **v2** döneminde | `dataset/download_floodnet.py`, `convert_floodnet.py` | ❌ — 🔴 iki dönüştürücü yol sınıfı için farklı indeks kullanıyor (5 ve 4), hangisinin koştuğu **DOĞRULANAMADI** (`VERI_KAYNAKLARI.md:74-85`) |
| 3 | Semantic Drone (Kaggle), Dubai Aerial (HF) | — | İndirici yazıldı, **hiç kullanılmadı**; dizin yok, hiçbir yaml referans vermiyor | `dataset/download_semantic_drone.py`, `download_extra_datasets.py:78` | ❌ |
| 4 | **Roboflow** | — | Yalnız **test görselleri** indirme (`README.md` "Roboflow test dataset'leri", `codes/download_roboflow.py`, `codes/test_batch.py --source roboflow`); hiçbir eğitim yaml'ında geçmiyor | `test_images/roboflow/` (gitignore) | ❌ (eğitimde kullanıldığına dair kanıt yok) |
| 5 | **Sentetik arena** (kendi üreteç) | 3.003 train (`dataset/karisim_arena_gercek.yaml:34`) — `VERI_KAYNAKLARI.md:128` **2.700** yazıyor; iki sayı çelişiyor, hangisinin v36 koşumuna girdiği **DOĞRULANAMADI** (toplam 8.611 train, `egitim_v7a.log`) | Şartname geometrisi (HTAB 50×50 m, HB 2×2 m, 3 koridor, biri açık); zemin/engel etiketi piksel-kusursuz; **"etiketsiz moloz yok"** kuralı | `scripts/olcum/51_sentetik_arena.py` (çıktı 640 px, satır 19; HTAB_M 50, satır 24; HEDEF_KENAR_M 2.0, satır 37) | ✅ |
| 5b | Sentetik türevleri | `sentetik_arena_bariyer_acili` 2.160 (`VERI_KAYNAKLARI.md:129`), `sentetik_arena_PROFIL_t199` | v8/v37 ve T199 denemeleri (bariyer ±45°, arena zemin dokusu) | `scripts/olcum/152_…`, `157_arena_zemin_dokusu.py`, `158_…` | ❌ (v36 sonrası) |
| 6 | **copy_paste_gercek** → t121 → t122a/ac → **t127** | 67 kaynak kare (`data/raw_frames`, 67 jpg — yerel sayım) → 393 train (`karisim_arena_gercek.yaml:35`) → t127 344 train (`VERI_KAYNAKLARI.md:128`) | **Gerçek** 90° nadir drone karesi (~1024×576, WhatsApp videosundan) üzerine etiketi bilinen sentetik moloz; gerçek asfalt/gölge/araç dokusu. v17/v20 körlüğünü açan bileşen (`karisim_arena_gercek.yaml:3-21`) | `scripts/copy_paste_augmentation.py`; etiket yaması `scripts/olcum/100_t121_etiket_yamasi.py`, `104_t122_secenek_kumeleri.py`, temiz bölüm `116_t127_temiz_bolum_zinciri.py` | ✅ (t127) |
| 7 | **gercek_otopark / gercek_kompozit** | 67 kare yarı-otomatik etiket (`scripts/olcum/71_gercek_kare_etiketleyici.py`); 12× / 4× / 2× çoğaltma denemeleri | v29 (12×, RED), v30 (4×), v32 (2×) | `dataset/karisim_gercek_otopark*.yaml`, `karisim_gercek_kompozit.yaml` | ❌ (v34'ten itibaren t54/t127 hattına geçildi) |
| 8 | **DJI gerçek çekim 2026-08-22 (gündüz, kırsal)** | Klip 0037: 300 kare/290 etiketli · 0039: 222/196 · **0038: 246 → DOĞRULAMA** (`VERI_KAYNAKLARI.md:133-139`). `dji_v7` = 486 etiketli kare (F5 101 + dalga 2/3 108 + dalga 4 277; `config/model_registry.json:50`); `dji_v7_x5` = 2.065 kopya (**413 benzersiz**, `VERI_KAYNAKLARI.md:141`); val = 73 kare | v36'nın gerçek-dünya bileşeni; etiketler **kör** toplandı (56 amele + 7 tutarlılık denetçisi; `model_registry.json:50`), **üç durumlu maske** biçimiyle (0 etiketsiz / 1 zemin / 2 engel; `scripts/olcum/132_uc_durumlu_maske.py`) | `dataset/dji_v7/labels` (486 txt yerel), `dataset/dji_v7_x5` (2.065 txt) | ✅ |
| 8b | **0038 doğrulama kümesi** | test29 + val82 = 111 kare (`dataset/dji_kirsal_0038_bolum_v3`, 111 txt yerel); GPS örtüşmesi 0037 ile 0 m² | İki bağımsız kör etiket geçişinin uzlaşısı (sınıf 0 = A∧B, sınıf 1 = A∨B); **eğitime ve erken durdurmaya GİRMEZ** (`CONTRACTS.md:1442-1465` §12) | `dji/DOGRULAMA/`, `scripts/olcum/146_t152_uzlasi.py` | test |
| 9 | `data/dji_prova_kareler` (2026-08-20, gece) | 569 kare (yerel sayım) | **Hiç eğitime girmedi**; medyan parlaklık 19, arena yok (`VERI_KAYNAKLARI.md:145-147`) | — | ❌ |
| 10 | **Şartname arena figürü** | 1 kare, 1059×634, PDF s.9 | Tek "arena benzeri" kare; **YZ ürünü** (D-99); eğitime **girmez**, K0/K8 kapılarında kullanılır | `data/arena_referans/sartname_s9_arena.png`, `KAYNAK.md` | test |
| 11 | `test_images/ai/1.jpg, 2.png` | 2 kare, YZ üretimi arena | v13–v20 döneminde arena IoU/moloza basma ölçümü (n=2, "yön verir, kanıtlamaz") | `scripts/olcum/46-48_*` | test |
| 12 | **Kabul kümesi T66** | n=260 sentetik kadraj (547 dosya, parmak izi sha `604c037f…`) | K0–K7 kapıları | `O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66` (`model_registry.json:10-11`; PC'de, depoda yok) | test |
| 12b | **ACILI_t189** | n=260, bariyer 90° | K5'in ikinci kolu (dönme körlüğü) | `model_registry.json:12-13` | test |
| 12c | `data/arena_kompozit` / `_v2` | 528 / 756 görsel, 88 / 126 etiket (yerel sayım) | Hakem ekranı ve Jetson karar denkliği S kümesi | `data/arena_kompozit_v2` | test |

**Copy-paste üretecinin kritik kuralı** (`scripts/copy_paste_augmentation.py` docstring, satır 1-17): zemin satırı tam kare dikdörtgendir, engeller üstüne poligon olarak yazılır; bu yüzden engel maskesine girmeyen her nesne "zemin" etiketi alır. COCO kâhini araçların ~%98'ini zemin öğretiyordu (S1); DOTA OBB'ye geçildi (`RESEARCH_NOTES.md` §4 S1). Tam-kare zemin kuralının ikinci bedeli **çatı**: v21/v22/v34 çatıyı zemin sayıyordu (`karisim_t54_engelli.yaml:10-11`; D-232: v34 çatının %96'sını zemin sayıyor). Çözüm etiket yaması: çatı → sınıf 1 (T121/T122), sonra kaynak düzeyinde temiz train/val bölümü (T127; D-233: eski val'in 55/55 karesinin kaynağı eğitimde de vardı — %100 sızıntı).

**Etiketleme kalite kapısı (U1/U2):** Bunlar **model kapısı değil, etiket şartnamesi kapısıdır**: U1 ameleler arası IoU medyanı ≥ 0,75, U2 referansa göre ≥ 0,70 (`results/dji_20260822/su_on_kayit.md` §2; `scripts/olcum/131_su_sartname_kapisi.py` docstring). Ölçülen: **U1 0,910 · U2 0,899 → geçti**, F4 pilot başladı (`results/dji_20260822/SU_ETIKETLEME_PLANI.md:124`).

---

## 3. Model sürüm tarihçesi v1 → v37

Kaynaklar: `scripts/olcum/40_surum_degerlendirme.py` (KUNYE tablosu ve özet, satır 144-200), `results/capraz_dogrulama_*` dizin tarihleri, `REVIEW_LOG.md` D-kayıtları, `config/model_registry.json`. Tarihler dizin/kayıt tarihleridir.

| Sürüm | Tarih | Mimari · veri · değişen | Sonuç | Karar |
|---|---|---|---|---|
| v1 | ≤2026-07-11 | RescueNet | mask mAP50 0,619; blocked 0,363 (`codes/train_seg_v3.py:20`; `VERI_KAYNAKLARI.md:164`) | taban |
| v2 | 2026-07-11 (`results/v2_val_20260711`) | YOLOv8n-seg, RescueNet+FloodNet, 512, Colab 100 epoch (`VERI_KAYNAKLARI.md:121`); reçete `codes/train_seg.py` (degrees 45, copy_paste 0,15, NCNN export RPi için) | blocked **geriledi** 0,363 → 0,322 (`train_seg_v3.py:11`) | NCNN türevi `rpi_ncnn` profilinde `legacy-fallback` (`model_registry.json:290-303`) |
| v3 | 2026-07-12 | YOLOv8s, degrees 15, copy_paste 0,30, 200 epoch, blocked oversampling (`codes/train_seg_v3.py` docstring; `dataset/oversample_blocked.py`) | — | ara |
| v4 | 2026-07-15 | v3'ten ft, imgsz 512→640 | val kümesinde en iyi; test split'i o güne dek hiç kullanılmamıştı (`11_capraz_dogrulama.py` docstring) | ara |
| v5a/b/c | 2026-07-15 | v5c = **YOLOv8m@640**, COCO'dan 200 epoch | v4→v5c: mAP +0,043, blocked +0,076 (`40_surum…` "ÇALIŞAN KALDIRAÇLAR") | v5c gerçek karelerde en iyi taban (58/67; arena görmemiş) |
| v6/v7 | 07-20 | native 1024 | mAP artmadı, FPS düştü | RED |
| v8 serisi | 07-26 | cls_pw / mixup pilotları | "adil değil" (metodoloji hatası) | RED |
| **v9_mixup_full** | 07-27 | v5c + copy_paste_mode=mixup | bakir test mAP50 **0,6787**, blocked 0,5371 — RescueNet içi kazanan | arenada TAM KÖR → aday değil |
| v12 | 07-27 | warmup_bias_lr=0 | val +0,013, test −0,013 (val'e aşırı uyum) | RED |
| v13 | 07-27 | box=10 | mAP50 **0,6794** (en yüksek) · moloza basma **%37,7** (en kötü) | mAP sıralaması arenayı tersine çeviriyor |
| v15 | 07-28 | **10 sınıf ön-eğitim → 2 sınıf ft** (`42_cok_sinifli_onegitim.py`) | mAP 0,6550 · moloza basma **%2,7** | kazanç mAP'te değil arenada |
| v16 | 07-29 | v15 + sentetik arena v1 | %31,6 (etiketsiz moloz → 11× kötü) | üreteç düzeltildi |
| v17 | 07-29 | v15 + sentetik arena v2 (şerit modeli) | 1.jpg IoU 0,077 → **0,861**, moloz %0; mAP 0,6355 | ama gerçek drone karesinde **kör**: 10/67 (D-12) |
| v18/v19/v20 | 07-30 | dar / dar-kontrastlı / çok ölçekli (multi_scale) | S5 (imgsz duyarlılığı) düzelmedi (`RESEARCH_NOTES.md` §5 S5) | — |
| **v21_gercek_doku** | 2026-08-05 (141 dk) | v17 reçetesi + `copy_paste_gercek` 393 (`karisim_arena_gercek.yaml`) | 67/67 kullanılabilir, ONNX parite 30/30 (`jetson_paket/V21_KAPI_RAPORU.json`) | **üretim** 08-05 → 08-13 |
| v22 / v23 | 08-19 hüküm (D-181) | v22 = 11-sınıf ön-eğitim + gerçek karışım (T53); v23 = `rescuenet_2sinif_engelli` (T54) | v23: K0 %0,5 · K2 12/258 · kararlılık 4/260 | v23 → **v34** olarak üretime |
| v24_t57_doku | 08-13 (D-83) | doku değişikliği | T66 kadrajında rota 196/260, moloza basma %31,1 — "dağılım dışı" (D-107 tabanları) | üretim 08-13 → 08-14 |
| v25_t60_renk | 08-14 (D-95) | renk sadakati | sentetikte kusursuz, gerçek arenada **tam kör** | RED |
| v26 | 08-14 | — | durduruldu (D-104) | — |
| **v27** | 2026-08-14 (D-115/D-116) | T66 ada geometrisi; 640 eğitim, **512 çıkarım** (D-112) | K0–K5 hepsi GEÇTİ (ilk ön kayıtlı kabul, D-107) | **üretim** 08-14 → 08-15 |
| v28 | 08-15 (D-130) | v27 aynı, imgsz 512'de eğitim | kararlılık 9→3/260; K2 %8,20 | kabul edildi ama sevk edilmedi |
| v29 | 08-15 (D-131) | + gerçek otopark 12× | gerçek 0/67 → 64/67 **ama K5 3 px** (ezber) | RED |
| **v30** | 2026-08-15 (D-133/D-136) | gerçek otopark 4×, 200 epoch, 386 dk | K1 258 · K2 %8,53 · K3 %0 · K4 %0,39 · K5 0 px · gerçek 65/67 · kararlılık 8/260 | **üretim** 08-15 → 08-19 |
| v31 | 08-15 (D-140) | v30 tohum 1 | v30 ile **bit-bit aynı** — seed etkisiz | ölçüm |
| v32 | 08-15 (D-142) | gerçek veri 2× | kararlılık 6/260, eşik tutmadı | RED |
| v33 | 08-16 (D-148) | gürültü dayanıklılığı eğitimi | kararlılık 3/260 **ama K5 2 px** | RED |
| **v34** | 2026-08-19 (D-182) | = v23_t54_engelli ("zemin değil → engel" eşlemesi) | K0 %0,49 (güven çöküşü, D-183) · K2 %4,65 · kararlılık 4/260 · çatı kaçağı 0,9606 | **üretim** 08-19 → 08-21 |
| **v35** | 2026-08-21 (D-256) | t127_temiz: çatı etiketi yamalı + temiz bölüm | K2 %7,03 · K3 0 · K4 0,39 · kararlılık 9/260 · çatı kaçağı 0,043 | **üretim** 08-21 → 08-26; bugün **birinci yedek** |
| **v36** | 2026-08-26 (D-293/D-294) | gece_v7a: v35 tabanı + DJI ×5, val = 73 gerçek DJI karesi | §4'e bakınız | **üretim (bugün)** |
| v37 | 2026-08-28 (D-332) | bariyer_v8 degrees=180, epoch105 | K0–K7 **geçti**, ama gerçek arena figüründe zemin %4,4 → **%56,1** (`ZEMIN_MASKESI_SUPHELI`) | **GERİ ALINDI**; K8 kapısı doğdu |
| T199 aday (ep27) | 2026-08-28 | v36 + arena zemin profili | G4 12/12, G5 geçti, **G11 31/88 < 45** (`results/gece_20260828/aday_ep27_hukum.json`) | RED, v36 kaldı |

**Neden v36 üretim modeli?** (`config/model_registry.json:245` `_surum_karari`; `results/terfi_v36/rapor.md:7-12`)

- Gerçek karelerde **yanlış güzergâh** v35'in 15/21'inden (%71) v36'da **7/38**'e (%18) indi; engel üstündeki waypoint toplamı **79 → 3** (`model_registry.json:199`).
- Bedel: K3 0→1, K4 1→4, K6 5→7 (kapı içinde); gerçek kare zemin kaplaması 0,51 → 0,42 (model **daha az** görüyor); val82'de FP 0→2 (biri çorak tarlada rota — gerçek risk).
- 🔴 **Kural dışı terfi:** ön kayıtlı gerçek-kare eşikleri ROTA ≥ 10/29 (ölçülen **8**) ve MASKE_YOK ≤ 10/29 (ölçülen **16**) **geçilmedi**; kullanıcı "izin veriyorum kurala rağmen" dedi; eşikler değiştirilmedi ve sonraki terfileri bağlar (`CONTRACTS.md` §12 istisna satırı; `terfi_v36/rapor.md:7-12`).

**Yedekler:** v35 (`sha e00f6b8e…`) — arena K3/K4/K6'da daha iyi (0/1/5) ve val82'de FP üretmez, ama gerçek karelerde rotayı beton kanal üstünden geçirir; v34 ikinci yedek (`model_registry.json:255-274` `_yedek_surumler`). Geçiş yordamı `JETSON_KILAVUZ.md` §6C.

---

## 4. Kabul kümesi ve kapılar — v36'nın karnesi

**Kabul kümesi:** `sentetik_arena_kadraj_t66`, n=260 sentetik kadraj karesi (547 dosya), üretim modeli **bu küme üzerinde kabul edilir** (`config/model_registry.json:10-11`). Kümenin parmak izi `sha256:604c037f…` (`model_registry.json:247-252`). İkinci kol `sentetik_arena_kadraj_ACILI_t189` (bariyer 90°; ayırt ediciliği mutasyonla ölçüldü: T184 öncesi dedektör 185/260 → 48/260 düşüyor; `model_registry.json:12-13`).

**Kabul denetçisi:** `scripts/olcum/65_kabul_denetcisi.py` — D-107 ölçütlerini mekanik koşar; eşikler `ESIK` sözlüğünde (satır 116-142), CONF 0,30 (satır 113), kabul kümesi yolu registry'den okunur (fail-closed, satır 48-72). Her ölçüt GEÇTİ/DÜŞTÜ; verdikt AND birleşimi. Ön kayıt disiplini: eşikler **sonuç görülmeden** yazıldı (D-107, `REVIEW_LOG.md:7242-7290`).

| Kapı | Tanım | Eşik | **v36 ölçümü** | Kaynak |
|---|---|---|---|---|
| **K0 körlük** | şartname figüründe zemin kaplaması > 0; `data/raw_frames` (67) ve copy_paste (393) karelerinde boş maske 0 | > 0 · 0/67 · 0/393 | figür **%2,66** · raw 0/67 · cp 0/393 → GEÇTİ (v35 %9,03; oran 0,294 — "yetenek yönü", tehlike uyarısı değil) | `model_registry.json:51-55`; `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json` |
| **K1 rota üretimi** | 260 karede rota üretilen | ≥ 230 | **255/260** | aynı |
| **K2 moloza basma** | kalınlaştırılmış rota ∩ yer gerçeği engel > 0 olan kare oranı (`61_rota_moloza_basma.py`) | ≤ %15 | **15/255 = %5,88** (v35 %7,03) | `model_registry.json:128-133` |
| **K3 ağır basma** | basma oranı > %5 olan kare | ≤ %3 | **1/255 = %0,39** (v35 0) | `:134-139` |
| **K4 arena dışı** | rota arenanın dışına taşan kare | ≤ %5 | **4/255 = %1,57** (v35 1/256) | `:140-145` |
| **K5 bariyer kesişimi** | gövde yarıçapıyla kalın rota ∩ bariyer kolu (LAB a* dedektörü, **modelden bağımsız**, `63_bariyer_kesisimi.py`) | = 0 px | **0/172 ölçülebilir kare, 0 px** (bariyerli 173) | `:146-151`; `66_k5_bariyer_populasyon.py` |
| **K5A açılı** | aynı ölçüt, ACILI_t189 kümesi | = 0 px | 185 bariyerli, 176 rotalı, **0 kesen** | `scripts/olcum/results/t63/v36_K5A_dogrulama_k5a_acili.json` |
| **K6 rota yol üstünde** | rota çizgisinin sınıf-0 payı ≥ 0,90 VE sınıf-1 üstünde 0 waypoint; tutmayan kare = yanlış güzergâh (`rota_yol_olcumu.py`) | ≤ %5 | **7/255 = %2,75** | `:152-157` |
| **K7 yayınlanan şerit doğruluğu** | dondurulmuş 88 karelik iyi-koşullu alt kümede `road` == referans şerit (`151_k7_serit_dogrulugu.py`) | ≥ %95 VE rota üretilen ≥ 80/88 | **84/85 = %98,8 · 85/88** | `CONTRACTS.md:1466-1500`; `t63/v36_k7_baglama_k7.json` |
| **K8 gerçek kare** | şartname figüründe üretim yolu `ZEMIN_MASKESI_SUPHELI` döndürmemeli (n=1; "sahada çalışır" demez) | red yok | zemin 0,0444, kenar 0,0, red `UC_BANT_TEMAS_YOK` → **GEÇTİ** | `155_gercek_kare_kapisi.py`; `t63/v36_K8_dogrulama_k8.json` |
| **Gerçek-kare kapısı (CONTRACTS §12)** | test29 (0038): ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, YANLIŞ GÜZERGÂH = 0 | — | ROTA **8** ✗ · MASKE_YOK **16** ✗ · FP 1 ✔ · yanlış 0 ✔ · val82: rota 30, FP 2, yanlış 7 | `model_registry.json:158-199` |
| **D-303 ONNX/engine karar denkliği** | `.pt` ↔ türev aynı karar (şerit/red) | ≤ 5/260 uyuşmazlık | ONNX **259/260** (1 uyuşmazlık `sa_000215`, maske IoU 0,9975) | `results/t79/onnx_denklik_v36.json`; `REVIEW_LOG.md:22523` |
| Karar kararlılığı (**kapı değil**) | Gauss σ=2/255, 3 tekrar, tohum 7 — karar çevrilen kare | (v34 terfisinde ≤ 8/260 kapıydı) | v36 **14/260** (v35 9/260) — fazlalık "rota var/yok" çevrilmesi, fail-closed yönde | `model_registry.json:217-227`; `results/karar_cevrilmesi_v36/` |
| Genel kapı | `codes/test_rota_sentetik.py` deterministik sahneler + tam süit | 15/15 · süit OK | 15/15 · 962 test OK (terfi günü), 2121 test (Jetson, 6 Eylül) | `terfi_v36/rapor.md:282-291`; `REVIEW_LOG.md:30182` |

**Ölçülen, kapıya bağlanmayan diğer sayılar (v36):** çatı kaçağı 0,023 (v34 0,9606 · v35 0,0428); gerçek 67 karede zemin kaplaması tuval paydasıyla 0,2346 / içerik paydasıyla 0,4171 — bağımsız tahmine göre gerçek sürülebilir oran %47-52, yani v36 "daha az görüyor" (`model_registry.json:201-213`).

**Kabul zincirinin kapsam sınırı (defterin kendi cümlesi):** "ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR (T66, n=260); gerçek ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ" (`model_registry.json:49`). 0038 kümesi kırsal yoldur; kırmızı H, moloz, bariyer içermez (T111/D-198 açık).

---

## 5. Değerlendirme yöntemi — neden IoU/mAP değil KARAR ölçülüyor?

1. **mAP arena sıralamasını tersine çeviriyor** (`RESEARCH_NOTES.md` §2.5): v13 mAP lideri (0,6794) arenada en kötü (%37,7 moloza basma); v17 mAP en düşük (0,6355) arenada en iyi (%0). Mask mAP50 standart sapması 0,025-0,032 → **0,04'ten küçük farklar gürültüdür** (`44_karar_kurali.md` üzerinden; `65_kabul_denetcisi` ve `56_uc_kapili_model_secimi.py` docstring "GURULTU TABANI 0,04"). Bu yüzden "bu araştırmadaki hiçbir karar mAP'e dayandırılmadı"; registry `_mask_map50_notu`: "ÖLÇÜLMEDİ ve karara girmedi (K-3)" (`model_registry.json:214`).
2. **Ölçülen şey karar:** görevi belirleyen `analyze_path`'in döndürdüğü şerit numarası ve red sebebidir; "maskeler %99 örtüşüp karar değişebilir" (`scripts/olcum/67_onnx_karar_denkligi.py` docstring). Projenin standart ölçütü rota × yer gerçeği molozu (`61_rota_moloza_basma.py`: "IoU gizli varsayım taşır; asıl ölçüt moloza basma oranıdır"). Şerit-tabanlı "doğru mu" ölçümü tanıma bağımlı çıktığı için terk edildi (`60_kadraj_karar_dogrulugu.py`, README tablosu: "terk edildi").
3. **Kör tarafı ayrıca ölçülür:** K0 bir *emniyet* değil *yetenek* kapısıdır (az zemin görmek güvenli yön; çok zemin görmek K2/K3 ile yakalanır; `65_kabul_denetcisi.py:145-155`). v25 "sentetikte kusursuz, gerçek arenada tam kör" olduğu için reddedildi (D-95) — sıfır moloza basma tek başına başarı sayılmaz ("v9 tam kör, sıfır bedava", `RESEARCH_NOTES.md` §2.4).
4. **İki ölçüm hattı (K0 için):** aynı adla iki farklı payda vardır — (1) `65_kabul_denetcisi.kaplama()`: letterbox **tuvali** paydası (v36 figür 0,0266); (2) `109_t122_kiyas.py`: **içerik dikdörtgeni** paydası (0,0444). Oran 0,0266/0,0444 = 0,599 = 634·1059/1059² → çelişmezler, fark paydadır; kilit `tests/test_k0_iki_olcum_hatti.py` (`model_registry.json:119`).
5. **Ön kayıt (pre-registration):** eşikler ölçümden **önce** yazılır ve sonuca göre değiştirilmez (D-107; `results/gece_20260826/ON_KAYIT.md`; `scripts/olcum/*_on_kayit.md`). "ÖLÇÜLEMEDİ ≠ GEÇTİ": K5 üç durumludur (GEÇTİ / DÜŞTÜ / ÖLÇÜLEMEDİ) ve ÖLÇÜLEMEDİ terfiyi bloklar (D-197).
6. **Eşli ölçüm ve tohum:** kararlılık kıyasları aynı oturumda, aynı gürültü gerçekleştirmeleriyle yapılır; tohum duyarlılığı ikinci tohumla sınanır (`model_registry.json:226`). Bayat sayı taşınmaz (D-256 §3).
7. **p50/p95:** hız ölçümleri medyan ve %95 ile raporlanır (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` `metrikler_ms`); FDA süre bütçesi p95 ile kapatılır (`169_fda_butce_olcumu.py`).
8. **Bağımsız çürütücü:** her terfi sonrası ayrı bir ajan sayıları kırmaya çalışır (`results/gece_20260826/v7a_curut/`; `terfi_v36/rapor.md:5`).
9. **Sızıntı denetimi:** v17 için 6.452 eğitim görüntüsü arena görselleriyle eşleştirildi (0 eşleşme); T127 temiz bölüm; 0038 kümesi eğitime hiç girmedi (`CONTRACTS.md` §12).

---

## 6. Export hattı — .pt → ONNX → TensorRT

| Adım | Nerede | Komut / parametre | Kanıt |
|---|---|---|---|
| 1. ONNX (PC) | `scripts/export_tensorrt.py` | `model.export(format="onnx", imgsz=512, half=True, opset=17)`; FP16 gerçekten var mı denetlenir (`fp16_dogrula`, satır 77-86); engine PC'de **bilerek** üretilmez (docstring satır 1-11) | `results/onnx_export_v36_20260826/jetson_derleme_manifest.json` (fp16 true, opset 17, imgsz [512]) |
| 2. Kayıt | `codes/model_registry.py --turev-kaydet <dosya> --kaynak-pt models/navitas_seg_v36_best.pt` | Türevin **kendi** sha256'sı + `kaynak_sha256` yazılır; yer tutucu = RED, yabancı/yetim türev = RED (fail-closed) | `config/model_registry.json:15-41`; `codes/model_registry.py:1-12` |
| 3. Engine (Jetson) | `yolo export model=navitas_seg_v36_best.pt format=engine imgsz=512 half=True device=0 batch=1 workspace=2` — **`.pt`'den** (ultralytics ONNX'ten engine üretmez; kılavuz 2026-09-07'de düzeltildi) | 530 s, 57.283.989 B, sha `bb9bd868…0300`; Orin Nano 4 GB, JetPack 7.2.1, TensorRT 10.16 | `jetson_paket/JETSON_KILAVUZ.md:460-478`; `REVIEW_LOG.md:30182` (D-431) |
| 4. INT8 kararı | D-371 (2026-08-31): **sahada FP16**; kural "FPS ≥ 3 → INT8'e girme; gereken hız 0,9–2,6 FPS" (`JETSON_KILAVUZ.md:642-650`). Kalibrasyon kümesi (80 sentetik + 40 DJI) hazır ama kullanılmıyor (`161_q8_kalibrasyon_kumesi.py`) | `REVIEW_LOG.md:25820-25860` |
| 5. FP16 karar denkliği (PC) | `164_fp16_karar_denkligi.py` | F1 (FP32 doğruyken FP16 yanlış şerit) **0** · F2 uyuşma **0,9968** (n=633) → GEÇTİ | `results/b4_fps/fp16_denklik_20260901.json` |
| 6. Engine ↔ pt denkliği (Jetson) | `170_engine_karar_denkligi.py` | F1 0 · F2 0,9953 → geçti; **D-303 oransal 3/126 (%2,38) > 5/260 (%1,92) → DÜŞTÜ** → **uçuş `.pt` ile**; S kümesi T66 değil `arena_kompozit_v2` (nihai karar T66 ile) | `results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json` |
| 7. FPS (Jetson, 120 örnek, `data/raw_frames`) | `scripts/jetson_fps.py` | pt p50/p95 **1,35/1,06 FPS** · engine **1,58/1,33** · eşik 0,61 → GEÇTİ; 10 dk sürekli koşuda termal bayrak yok (gpu ≤ 56 °C, VDD_IN ≤ 9,4 W) | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`; D-431 §3 |
| Darboğaz | — | model değil: `get_masks` ~311 ms + costmap ~208 ms = toplamın %82'si, CPU'da; engine toplamda 104 ms kazandırır (D-431 §4/6). PC referansı (RTX 5080, 640): 34-36 FPS (`JETSON_KILAVUZ.md:610-620`) | — |
| Eski hat | `codes/train_seg.py:111-131` `export_ncnn` | NCNN (Raspberry Pi 5) — v2 dönemi; bugün `rpi_ncnn` profili `legacy-fallback` | `model_registry.json:290-303` |

Not: FP32 `.engine` yer tutucusu 2026-09-07'de profilden çıkarıldı (derlenmedi, gerekmiyor; `model_registry.json:42`). `.engine` dosyası `.gitignore`'da değil, commit'e alınmadı (D-431 mimar notu).

---

## 7. Eğitim reçetesi — v36 nasıl eğitildi (log ile)

Kaynak: `results/gece_20260826/egitim_v7a.log` (ilk satır RECETE sözlüğü; ultralytics `trainer` argüman satırı; son satırlar) ve `results/gece_20260826/ON_KAYIT.md` §3, §14.

| Parametre | Değer | Not |
|---|---|---|
| Donanım | **NVIDIA GeForce RTX 5080 Laptop GPU, 16.303 MiB** · Python 3.13.7 · torch 2.11.0+cu128 · Ultralytics 8.4.92 · Windows (`O:\navitas`) | log satır 3 |
| Taban ağırlık | `models/navitas_seg_v35_best.pt` (YOLOv8m-seg) | `model=…v35_best.pt` |
| Veri | `dataset/karisim_gece_v7a.yaml`: rescuenet_2sinif_engelli + sentetik_arena + copy_paste_t127 + dji_v7_x5 → **8.611 train**; val = `dji_v7/images/val` **73 gerçek DJI karesi** (378 örnek) | yaml; log "8611"; log sonu "all 73 378" |
| epochs / patience | 40 / 15 → **17 epoch** koşuldu, **en iyi epoch 2** | log sonu "EarlyStopping… Best results observed at epoch 2" |
| Süre | **0,654 saat (2.402 s)** | log "17 epochs completed in 0.654 hours"; "EGITIM BITTI 2402 sn" |
| imgsz / batch / workers | 512 / 12 / 8 | RECETE |
| seed / deterministic / amp | 0 / True / True | trainer satırı |
| optimizer / lr0 / lrf / warmup | `auto` / 0,001 / 0,01 / 5 epoch — 🔴 `optimizer=auto` yüzünden lr0 ultralytics tarafından **0,001667'ye sessizce ezildi** | `model_registry.json:50`; `152_bariyer_aci_egitimi.py` docstring |
| Augmentasyon (fiilen) | degrees **0,0** · flipud **0,0** · fliplr 0,5 · hsv_h 0,015 · hsv_s 0,7 · hsv_v 0,4 · scale 0,5 · translate 0,1 · shear 0 · mosaic 1,0 · close_mosaic 10 · copy_paste **0,0** · erasing 0,4 · mixup 0 · cos_lr **False** | trainer satırı |
| Kayıp ağırlıkları | box 7,5 · cls 0,5 · dfl 1,5 · overlap_mask True · mask_ratio 4 | trainer satırı |
| Sonuç (val 73) | mask mAP50 **0,387**, mAP50-95 **0,155** (traversable 0,469/0,219 · blocked 0,305/0,091); box mAP50 0,501 | log sonu |

🔴 **Kayıt defterindeki "reçete t127 birebir" iddiası yanlıştı** (D-324 §5): t127'de degrees 15, flipud 0,5, copy_paste 0,3, cos_lr true, close_mosaic 20, AdamW vardı; `139_gece_egitim.py` bunları geçirmedi. Sonuç: v36 **hiç döndürme artırımı görmeden** eğitildi → bariyeri yalnız yataya yakın açılarda görüyor (0-30°'de %99+, 60-135°'de **%0,0**; `152_bariyer_aci_egitimi.py` docstring). Bu, v8/v37 denemesinin (degrees 180, AdamW, cos_lr, copy_paste 0,3, 600 epoch/11 saat; `results/gece_20260828/bariyer_v8_v36taban_recete.json`) sebebidir; v37 gerçek arena figüründe taşırdığı için geri alındı (D-332).

**Önceki reçeteler (kanıtlı):**
- v2: CPU (Ryzen 7 5700U), YOLOv8n, 150 epoch, batch 8, AdamW lr0 0,001, degrees 45, hsv_v 0,5, copy_paste 0,15, cos_lr (`codes/train_seg.py:36-95`).
- v3: YOLOv8s, 200 epoch, patience 60, degrees 15, copy_paste 0,30 (`codes/train_seg_v3.py:44-108`).
- v21: v15 tabanı, imgsz 640, 60 epoch, batch 12, mixup, 141,1 dk (D-20, `REVIEW_LOG.md:1163-1170`).
- v27: 640, 200 epoch, ~5,9 saat; v28: 512, ~3,8 saat (D-123, `REVIEW_LOG.md:8527-8535`).
- v30: 200 epoch, en iyi epoch 200, 386 dk, batch 12, cache=disk, workers 16, taban `v15_on10sinif` (D-133; `78_gurultu_dayanikli_egitim.py` docstring).
- t121/t122/t127 (v35): v34 tabanı, epochs 40, patience 15, imgsz 512 (`101_t121_ft_kosumu.py` docstring; ON_KAYIT §3).

**Eğitim koşulmadı**: Jetson'da hiçbir eğitim yok; tüm eğitimler PC'de (`O:\navitas-local-train`, git deposu değil — `scripts/olcum/README.md:8-16`).

---

## 8. `scripts/olcum/` betikleri — numaralı liste (139 `.py`: 136 numaralı + `ayarlar.py`, `rota_yol_olcumu.py`, `s2_yonelim_olcum.py`)

Kaynak: her betiğin ilk 30 satırı (docstring). Numara sırası tarihsel sırayı yaklaşık verir (11 → Temmuz 2026; 40-54 → Temmuz sonu; 56-99 → Ağustos ortası; 100-176 → 19 Ağustos – 7 Eylül).

| No | Ad | Amaç (tek cümle) |
|---|---|---|
| — | `ayarlar.py` | Ortak ayarlar; depo kökünü `__file__`'dan türetir (T161, çıplak yol yok). |
| — | `rota_yol_olcumu.py` | "Rota yol üstünde mi" ölçümünün tek tanımı (K6 ve gerçek-kare kapısı ortak). |
| — | `s2_yonelim_olcum.py` | Üç-bant kapısını rota eksenine göre kurmanın kazancını/kaybını ölçer. |
| 11 | `capraz_dogrulama` | Modeli hem val294 hem bakir test305'te ölçer (aynı val'de seçim → aşırı uyum riski). |
| 40 | `surum_degerlendirme` | v4'ten bugüne tüm modellerin toplu karnesi; "mAP arenaya transfer olmuyor" uyarısı. |
| 41 | `cok_sinifli_veri` | RescueNet 11 sınıfını YOLO-seg'e çevirir (ön-eğitim kümesi). |
| 42 | `cok_sinifli_onegitim` | 10 sınıf ön-eğitim → 2 sınıf fine-tune (v15). |
| 43 | `zincir` | GPU boşalınca sıradaki eğitimi başlatır. |
| 45 | `alan_disi_test` | RescueNet dışı gerçek görüntülerde niteliksel model kıyası. |
| 46 | `arena_esik` | YZ arena görsellerinde güven eşiği taraması. |
| 47 | `arena_yer_gercegi` | 2 YZ arena görseli için yarı otomatik yol maskesi. |
| 48 | `arena_iou` | Arena görsellerinde IoU/kesinlik/duyarlılık ile model kıyası. |
| 51 | `sentetik_arena` | Sentetik arena üreteci (şartname geometrisi, gerçek enkaz dokuları). |
| 52 | `sentetik_denetim` | Sentetik veriyi eğitime sokmadan önce etiket/poligon denetimi. |
| 53 | `drone_kare` | Drone videosundan zemin doku bankası kareleri çıkarır (pHash ile yakın kopya eleme). |
| 54 | `arena_cozunurluk` | 2.png'nin çözülememesinin ölçek sorunu olup olmadığını imgsz taramasıyla sınar. |
| 56 | `t53_gercek_karisim` | Eğitim koşucusu: 11-sınıf ön-eğitim + gerçek doku karışımı (RECETE tek kaynağı). |
| 56 | `uc_kapili_model_secimi` | 11 modeli mAP'siz üç kapıyla sıralar (alan içi doğruluk, alan dışı temkin, karar). |
| 57 | `t51_kadraj_kapilari` | Üreteç geometrisini yer gerçeğiyle sınar (model yok). |
| 57 | `t54_engel_eslemesi` | 11-sınıf etiketleri "zemin değil → engel" eşlemesiyle 2 sınıfa indirir. |
| 58 | `b1_bagimsiz` | Gerçek drone karelerinde boş maske ölçümünü bağımsız tekrarlar (v17 negatif kontrol). |
| 59 | `t60_uretec_sadakati` | Üreteç renk düzeltmesinin doku istatistiğini koruduğunu ölçer. |
| 60 | `kadraj_karar_dogrulugu` | Kadraj kümesinde model tabanlı şerit kararı (terk edildi — tanıma bağlı). |
| 61 | `rota_moloza_basma` | **Standart ölçüt:** kalın rota ∩ yer gerçeği molozu (K2/K3). |
| 62 | `haritalama_gorseli` | 4 panelli harita: özgün / segmentasyon / C-uzayı / rota. |
| 63 | `bariyer_kesisimi` | Modelden bağımsız bariyer dedektörü (LAB a*>25) ile rota kesişimi. |
| 64 | `surum_kiyasi` | İki modeli aynı dört ölçütle karşılaştıran koşucu. |
| 65 | `kabul_denetcisi` | **D-107 kabul ölçütlerini (K0..K8) mekanik koşar; verdikt üretir.** |
| 66 | `k5_bariyer_populasyon` | K5'i gövde yarıçapıyla ~172 karede ölçer. |
| 67 | `onnx_karar_denkligi` | `.pt` ↔ `.onnx` **karar** denkliği (maske değil). |
| 68 | `karar_kararliligi` | Algılayıcı gürültüsü (σ=2/255) altında karar çevrilme oranı. |
| 69 | `arac_referans_olcegi` | Telemetrisiz ölçek kâhini: araç OBB kısa kenarından metre/piksel. |
| 70 | `gercek_kare_rota_denemesi` | Gerçek karelerde ölçek verilince rota çıkıyor mu, neden çıkmıyor. |
| 71 | `gercek_kare_etiketleyici` | Gerçek karelerin yarı otomatik, görsel onaylı etiketlenmesi (kanıtsız piksel = engel). |
| 72 | `kaynak_taramasi` | Hakem ekranının her kaynağında ret sebebi dökümü. |
| 73 | `serit_payi` | Kararsızlık mekanizması: şeritler arası darboğaz farkı. |
| 74 | `olcek_kahini_gecerlilik` | Araç ölçeğinin eğik bakışta ateşlenmemesi için geçerlilik ölçütü arar. |
| 75 | `koridor_envanteri` | Koridor envanteri küresel A*'dan daha kararlı mı (yalnız ölçüm). |
| 76 | `serit_etiketi_celiskisi` | İki etiketleme otoritesinin aynı koridora farklı numara verip vermediği. |
| 78 | `gurultu_dayanikli_egitim` | v33: v30 reçetesi + piksel gürültüsü augmentasyonu. |
| 79 | `k5_koken` | v33'ün K5 düşüşünün kare kare kökeni (rota taşındı mı, bariyer duyarlılığı düştü mü). |
| 80 | `k5_siki_kapi` | K5'i gürültülü tekrarlarla (tek çekiliş yetmez) ölçer. |
| 81 | `t74_darbogaz_yeri` | Darboğazı moloz adası mı koridor sınırı mı daraltıyor. |
| 82 | `t94_planlayici_taramasi` | Rota neden ulaşabileceği en iyi darboğazın altında kalıyor. |
| 83 | `t94_izgara_cozunurlugu` | Kayıp plan ızgarasından mı (adım 10 px). |
| 84 | `t94_seyreltme` | String-pulling'in emniyet payını ne kadar yediği. |
| 85 | `t94_aciklik_koruyan_kiris` | Kirişi dar boğazdan geçirmeyen string-pulling kuralı. |
| 86 | `t94_v1_kapi_kosumu` | V1 kuralını projenin kendi kapılarıyla sınar. |
| 87 | `t94_yumusak_kiris` | Sabit eşik yerine göreli kiriş kabulü (W1/W2/W3). |
| 88 | `w1_maliyet` | W1 kuralının waypoint/uzunluk/süre bedeli. |
| 89 | `t95_rota_bul_kayip` | `rota_bul` katmanında açıklık koruması kayıp ölçümü (D-402: bugün geçersiz, tarihsel). |
| 90 | `t95b_butce` | Aynı korumanın süre bütçesi (tarihsel). |
| 91 | `t95c_kararlilik` | Aynı korumanın gürültü altında kararlılığı (tarihsel). |
| 92 | `t96_road_istatistigi` | Yayınlanan `road` hangi istatistik olmalı (darboğaz / baskın / çıkış şeridi). |
| 93 | `t106_guven_bandi` | Güven bandı sıkışması (conf 0,10 / 0,30 kaplama oranı) kabul kümesinde var mı. |
| 94 | `t111_bakirlik_envanteri` | Hangi küme hangi yaml'a girmiş; alan dışı etiketli küme var mı (envanter). |
| 95 | `t121_kahin_sondasi` | Hangi model çatıyı zeminden ayırıyor (kâhin adayları). |
| 96 | `t121_etiket_istatistigi` | Etiket seçeneklerinin önce/sonra sınıf piksel payları. |
| 97 | `t121_karisim_kutlesi` | Karışım bileşenlerinin piksel kütlesi tablosu. |
| 98 | `t121_cati_adaylari` | Çatı aday maskeleri + görsel doğrulama sayfaları. |
| 99 | `t121_cati_yayilimi` | Elle çizilen çatı poligonlarını homografiyle komşu karelere taşır. |
| 100 | `t121_etiket_yamasi` | copy_paste_gercek → copy_paste_t121 (çatı → sınıf 1). |
| 101 | `t121_ft_kosumu` | v34'ten yamalı etiketlerle fine-tune başlatıcı. |
| 102 | `t121_degerlendirme` | T121 ön kayıt ölçütlerini ölçer. |
| 103 | `t122_k0_tanisi` | K0 düşüşü aşırı genelleme mi güven çökmesi mi. |
| 104 | `t122_secenek_kumeleri` | (a) daralt ve (a)+(c) daralt+çatı etiket kümelerini üretir. |
| 105 | `t122_ft_kosumu` | T122 seçenekleri için fine-tune başlatıcı. |
| 106 | `t126_k5_olculebilir_zemin` | K5'in kabul kümesinde ölçülebilir olup olmadığı. |
| 107 | `t122_71_capraz_denetimi` | 71 etiketleyicisinin çatı kaçağı (%49,4). |
| 108 | `t122_kahin_kiyasi` | Aday çatı kâhinlerini aynı yer gerçeğiyle kıyaslar. |
| 109 | `t122_kiyas` | Dört/beş modelin tek tabloda kıyası (çatı kaçağı, kaplama, figür). |
| 110 | `t122_golge_kurali_denemesi` | Gölge istisnası düzeltme adayının iki yönlü ölçümü. |
| 111 | `t122_cati_buyutme_denemesi` | Kenar güdümlü (watershed) çatı büyütme denemesi. |
| 112 | `t118_tavan_gercekligi` | Gerçek otoparkın sürülebilir oranı 0,67 tavanını aşıyor mu. |
| 113 | `t126_sart1_kaniti` | Bariyer dedektörünün modelsiz çalıştığının kanıtı. |
| 114 | `t127_bakir_kare_kumesi` | Eğitime hiç girmemiş 11 gerçek kare + çatı maskeleri. |
| 115 | `t127_bakir_kiyas` | Bakir karelerde dört aday kıyası. |
| 116 | `t127_temiz_bolum_zinciri` | Küme kur → eğit → ölç zinciri (temiz train/val bölümü). |
| 117 | `t129_cozunurluk_etkisi` | Çatı körlüğü kaynak kalitesine bağlı mı (video vs ham fotoğraf). |
| 118 | `t131_kayma_defteri` | Registry git geçmişinde taban alanlarının terfi terfi kayması. |
| 119 | `t131_k0_taban_gecmisi` | K0 figür tabanını üretim soyağacı boyunca tek aletle yeniden ölçer. |
| 120 | `t118_tavan_payi` | Kaplama tavanı redlerinin payı. |
| 121 | `t133_triyaj_envanteri` | READY_FOR_REVIEW görev envanteri (mekanik). |
| 122 | `t133_bekleme_yasi` | Görevlerin ne zamandan beri beklediği (git geçmişi). |
| 123 | `t133_triyaj_tablosu` | Triyaj + çürütücü sonuçlarını tabloya çevirir. |
| 124 | `t134_kapi_etkisi` | Kapı `rota_bul` içine konsaydı ne reddedilirdi. |
| 125 | `t137_etiket_olcumu` | Etiketleme kapasitesi/kalitesi ölçüm aleti (ızgara, maske, IoU). |
| 126 | `t138_gece_kumesi` | DJI gece kareleri eğitime uygun mu; üretim yolu rota üretiyor mu. |
| 127 | `t139_kanit_paketi` | Rota üreten kareleri kalıcı kanıt olarak repoya koyar. |
| 128 | `t139_doz_yanit` | Görünürlük (parlaklık) doz-yanıt eğrisi. |
| 129 | `t141_mutasyon_olcumu` | Kilidin mutasyon ölçümü (İKA no_route). |
| 130 | `su_referans` | Su/koridor referans maskesi (otomatik öneri + elle düzeltme). |
| 131 | `su_sartname_kapisi` | Etiket şartnamesi kapısı U1/U2/U3 (amele uyumu). |
| 132 | `uc_durumlu_maske` | Üç durumlu maske biçimi (0 etiketsiz / 1 zemin / 2 engel) ve YOLO'ya çevrim. |
| 133 | `f5_kapasite_kiyasi` | Sınıf 0 çizmenin ek etiketleme maliyeti. |
| 134 | `gsd_olcumu` | GSD'yi GPS ötelenmesi + faz korelasyonuyla ölçer. |
| 135 | `dji_kirsal_zincir` | DJI kırsal eğitim zinciri (küme → yaml → eğit → ölç). |
| 136 | `bant_temasi_tanisi` | `UC_BANT_TEMAS_YOK` parçalılık mı yapısal mı. |
| 137 | `bant_bosluk_tanisi` | Hangi karede bant tamamlaması işe yarar. |
| 138 | `kare_uygunluk_denetimi` | Etiketlenen karelerin keskinlik/pozlama/nadir uygunluğu. |
| 139 | `gece_egitim` | Gece eğitim koşumu (lr0/warmup açıkça geçirilir; DJI ×20). |
| 140 | `uc_maske_araci` | Etiketleme amelesi için deterministik maske aracı. |
| 141 | `etiket_secimi` | Etiket dalgası için en-uzak-nokta kare seçimi. |
| 142 | `gece_olcum` | Aday model için K0..K5 + gerçek kare (test29) kapılarını tek komutla koşar. |
| 143 | `etiket_tavani` | Elle etiketin üretim yolundan geçirilmesi → model için tavan. |
| 144 | `dalga2_kume` | Etiket dalga 2 → YOLO kümesi + ×20. |
| 145 | `test29_referans` | test29 referans tamamlama (v2 küme). |
| 146 | `t152_uzlasi` | İki kör etiket geçişinin uzlaşısı → 0038_bolum_v3. |
| 147 | `v7_kume` | 0037/0039'un tüm etiketli kareleri → dji_v7 (+×5), 0038 hariç. |
| 148 | `gui_kaynak_teshis` | YKS GUI kaynak başına rota üretilmeme sebebi. |
| 149 | `kompozit_tavan` | Kompozit kümede tavan (etiket) vs model. |
| 150 | `cikarim_geometrisi` | Letterbox/imgsz kiplerinin rota sonucuna etkisi (tanısal). |
| 151 | `k7_serit_dogrulugu` | K7: yayınlanan şerit doğruluğu (88 karelik dondurulmuş alt küme). |
| 152 | `bariyer_aci_egitimi` | v8: bariyer açısı eğitimi (degrees 180; v36 reçete tespiti). |
| 153 | `v8_degerlendirme` | v8 adayı için G4/G5/G11 kapıları. |
| 154 | `egitim_egilimi` | Eğitim sürerken checkpoint'lerde G4/kompozit gidişatı. |
| 155 | `gercek_kare_kapisi` | K8: gerçek arena karesinde üretim yolu kırılmasın. |
| 156 | `t189_bariyer_aci_kanit` | ACILI kümesinin ayırt ediciliği (mutasyon). |
| 157 | `arena_zemin_dokusu` | Yordamsal sıkıştırılmış toprak dokusu (figürden ölçülen istatistikle). |
| 158 | `t199_arena_profil_egitimi` | T199 arena profili eğitimi. |
| 159 | `t192_figur_rota` | Şartname figüründe rota üretiliyor mu (ikili). |
| 160 | `t199_verdikt` | T199 ön kaydını mekanik uygular. |
| 161 | `q8_kalibrasyon_kumesi` | INT8 kalibrasyon kümesi (80 sentetik + 40 DJI). |
| 162 | `yaw_kadraj_zarfi` | Yaw/kadraj bozulma zarfı. |
| 163 | `b4_p_ve_kosu` | Kare başına geçerli rota olasılığı `p` ve gerekli FPS türetimi. |
| 164 | `fp16_karar_denkligi` | FP16 ↔ FP32 karar denkliği (F1/F2). |
| 165 | `trt_pc_provasi` | ONNX grafiğinin TensorRT'ye dönüştüğünün PC provası. |
| 166 | `infer_size_640` | INFER_SIZE 512 vs 640 kör aralığı kapatıyor mu. |
| 167 | `fdr_kanit_paketi` | FDR kanıt paketini artefaktlardan üretir. |
| 168 | `hb_sekil_olcumu` | HB şekil puanı ve eşik türetimi. |
| 169 | `fda_butce_olcumu` | FDA 10 dk bütçesi: algı+karar+telsiz süre ölçümü. |
| 170 | `engine_karar_denkligi` | TensorRT engine ↔ pt karar denkliği (Jetson). |
| 170 | `t150_baglama_olcumu` | HB hedeflemesi bağlanırsa ne olur. |
| 171 | `histerezis_kararliligi` | Yayına sızan çevrilme vs ham çevrilme. |
| 172 | `t52_ayirt_edicilik` | "Her şey boyanmış" çöküşünü gerçek açık arenadan ayıran ölçüt. |
| 173 | `t99_uretim_imzasi` | 89/90/91 ölçümlerini üretim çağrı imzasıyla yeniden. |
| 174 | `t101_gercek_kadraj` | Gerçek kadrajda koridor sayısı ve şerit sınır aşımı. |
| 175 | `t61_ic_tutarlilik` | Doku/renk iç tutarlılık adayları (keşif). |
| 176 | `piksel_karisiklik_matrisi` | test29'da 3×3 piksel karışıklık matrisi (etiketsiz ayrı sütun). |

---

## 9. 15 muhtemel jüri sorusu ve kanıta dayanan cevaplar

1. **Hangi modeli kullanıyorsunuz, neden?** YOLOv8m-seg, 512 px, iki sınıf (zemin/engel). Segmentasyon seçildi çünkü şartname engelleri "vb." ile açık küme bırakıyor; zemin dışı her şeyi engel saymak fail-safe'tir (`RESEARCH_NOTES.md` §2.1). "m" boyutu v4→v5c geçişinde ölçülen kazançla seçildi (mAP +0,043, blocked +0,076); "l" ve 1024 px FPS hedefini karşılamadığı için elendi (`40_surum_degerlendirme.py`).
2. **Hangi veriyle eğittiniz?** v36 = RescueNet (3.502, "zemin değil → engel" eşlemesiyle) + sentetik arena + gerçek drone karesi üstüne sentetik moloz (copy_paste_t127, 344) + kendi DJI çekimimiz (486 kare ×5) — toplam 8.611 eğitim görüntüsü; doğrulama 73 gerçek DJI karesi (`dataset/karisim_gece_v7a.yaml`; `egitim_v7a.log`).
3. **Doğruluğu ne?** mAP'i kararımıza sokmadık (mAP arena sıralamasını tersine çeviriyor, §5). Kabul kümesinde (n=260): rota 255/260, moloza basma %5,88, ağır basma %0,39, bariyer kesişimi 0 px, yanlış güzergâh %2,75, yayınlanan şerit doğruluğu %98,8 (84/85). ONNX ile karar denkliği 259/260. Gerçek kırsal karelerde (test29) rota 8/29, yanlış güzergâh 0 (`config/model_registry.json` `metrics`).
4. **Bu sayılar sahada geçerli mi?** Hayır — defterin kendi cümlesiyle "arena ölçümlerinin tamamı sentetiktir; K0..K6 saha başarımı iddia etmez" (`model_registry.json:49`). Gerçek doğrulama kümesi (0038) kırsal yoldur, arena değildir; arena benzeri saha çekimi hâlâ açık insan görevidir (T111/D-198).
5. **Neden mAP/IoU değil karar ölçüyorsunuz?** v13 mAP lideriyken arenada molozun %37,7'sine "geçilebilir" dedi; v17 mAP en düşükken %0. Maske IoU 0,9975 iken bile karar değişebildi (ONNX denkliği). Görevi belirleyen şerit numarasıdır; yanlış güzergâh 0 puan (`61_rota_moloza_basma.py`, `67_onnx_karar_denkligi.py`).
6. **Sentetik veri uydurma değil mi?** Arena kurallarla tanımlı bir alandır (50×50 m, 3 koridor, biri açık); geometri ve etiket piksel-kusursuzdur; enkaz dokuları RescueNet'in gerçek maskelerinden kesilir (`51_sentetik_arena.py` docstring). Yalnız sentetikle eğitim gerçek karede körleştirdi (v17: 10/67), bu yüzden gerçek doku bileşeni eklendi (`karisim_arena_gercek.yaml:3-21`).
7. **Aşırı uyum / sızıntı önlemi?** 0038 uçuşu eğitime ve erken durdurmaya hiç girmedi; etiketler kör toplandı; T127'de val'in %100 kirli olduğu ölçülüp kaynak düzeyinde bölüm yapıldı (D-233); v17 için 6.452 görüntüde arena eşleşmesi 0 (`CONTRACTS.md` §12; `40_surum…`).
8. **Eşikleri sonuçtan sonra mı belirlediniz?** Hayır: ön kayıt disiplini (D-107): eşikler ölçümden önce yazılır; v36 terfisinde iki eşik geçilemedi ve bu **gizlenmedi**, "kural dışı, kullanıcı kararı" diye kayda geçti (`terfi_v36/rapor.md:7-12`).
9. **Model bir engeli kaçırırsa?** Mimari invariant: `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` — nesne katmanı (DOTA OBB araç) yalnız çıkarır, ekleyemez (`codes/sinif_semasi.py:22-25`). Bariyer için modelden bağımsız LAB a* dedektörü de vardır (K5). Rota, 1,10 m güvenlik yarıçapıyla aşındırılmış alanda aranır (`costmap_path_finder.py:87`).
10. **Model kör olursa?** Fail-closed: boş maske → `MASKE_YOK`, şüpheli kaplama → `ZEMIN_MASKESI_SUPHELI` ile rota reddedilir; v37 tam bu kapıda düştü (%56,1 kaplama) ve geri alındı (D-332). Gece kareleri (569) hiç eğitime girmedi.
11. **Jetson'da kaç FPS?** Orin Nano 4 GB'de `.pt` 1,35 FPS (p50), FP16 engine 1,58 FPS; gereksinim kapsama hesabından 0,9–2,6 FPS (eşik 0,61 geçildi). Darboğaz ağ değil, CPU'daki maske çözme + costmap (%82) (`results/jetson_20260906/…/ozet.json`; D-431).
12. **INT8 kullanmadınız mı?** Hayır; kural "FPS ≥ 3 → INT8'e girme" ve kullanıcı kararı FP16 (D-371). Kalibrasyon kümesi hazır, gerekirse tekrar yapılmaz.
13. **Engine mi .pt mi uçuyor?** `.pt`. Engine karar denkliği F1/F2'yi geçti ama D-303 oransal eşiğini (3/126 > 5/260) geçemedi; kayıt defteri `path` `.pt`'dir (D-431 §4).
14. **Bilinen zayıflıklar?** (a) v36 döndürme artırımı görmedi → bariyeri 60-135°'de görmüyor (D-324); (b) gerçek karede kaplama düşük (0,42; gerçek ~0,47-0,52) ve karar kararlılığı 14/260 (v35 9); (c) val82'de 2 FP (biri tarlada rota); (d) arena benzeri gerçek kare yok. Hepsi defterde yazılı (`model_registry.json:199-227`).
15. **Yeni sürümü nasıl kabul edersiniz?** `65_kabul_denetcisi.py` K0–K8 + K5A + gerçek-kare kapısı + ONNX/engine denkliği + genel kapı 15/15 + tam süit; verdikt AND; sha256 ölçülerek registry'ye yazılır; yedek yordamı §6C. Terfi kararı insana aittir (D-133).

---

## 10. DOĞRULANAMADI / çelişki listesi

- Sentetik arena train sayısı: 3.003 (`karisim_arena_gercek.yaml:34`) vs 2.700 (`VERI_KAYNAKLARI.md:128`); log toplamı 8.611 = 3.502 + X + 344 + 2.065 → X = 2.700 olur; yaml yorumundaki 3.003 muhtemelen eski üretim sayısıdır — kesin kayıt yok.
- FloodNet yol sınıfı indeksi (4 mü 5 mi) — çözülmemiş (`VERI_KAYNAKLARI.md:81-85`).
- Roboflow'un herhangi bir eğitime girdiğine dair kanıt yok; yalnız test indirici var.
- `50_doku_bankasi.py` (sentetik üretecin doku kaynağı) depoda yok; yalnız `51_sentetik_arena.py` atfı var.
- Semantic Drone / Dubai kümeleri hiç indirilmemiş olabilir (dizin yok).
- Kabul kümesi (`sentetik_arena_kadraj_t66`) ve tüm ağırlık dosyaları depo dışında (`O:\navitas-local-train`, PC); bu makinede yeniden ölçüm yapılamaz.
- v1 eğitim tarihi ve reçetesi için depoda ayrı kayıt bulunamadı (yalnız 0,619 mAP atfı).
- Veri seti lisans/atıf bilgisi kayıtlı değil (`VERI_KAYNAKLARI.md:51-54`).
