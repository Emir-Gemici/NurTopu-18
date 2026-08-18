# NAVITAS — MİMARİ PLAN

> **Rol:** Bu dosyayı mimar (Claude / Opus 5) yazar. Ameleler (Codex-X, yerel sürü)
> buradan **okur**, buraya yazmaz. İş kalemleri `TASK_QUEUE.md` dosyasındadır.
> Kusur ve mantık riski kayıtları `REVIEW_LOG.md` dosyasındadır.

| | |
|---|---|
| **Sürüm** | 1.0 |
| **Tarih** | 3 Ağustos 2026 |
| **Kaynak şartname** | `Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf` (V2, 13.04.2026) |
| **Anayasa** | `CLAUDE.md` |

---

## 1. Takvim gerçeği

DDR teslim edildi (15.07.2026) ve **sonuçları 29.07.2026'da açıklandı**. Proje artık
DDR fazında değil. Şartname Tablo 1'e göre kalan takvim:

| Aşama | Tarih | Bugüne kalan |
|---|---|---|
| **FDR — Final Değerlendirme Raporu son teslim** | 21.09.2026 17.00 | **49 gün** |
| **FDA — FDS + Drone ile Görev Test Uçuşu** | 30.09 – 03.10.2026 | **58 gün** |
| FDR sonuçları + maddi destek | 04.10.2026 | 62 gün |
| SGGS — Sistem Gözden Geçirme Sunumu | 05.02.2027 | — |
| UHDR — Uçuşa Hazırlık Değerlendirme Raporu | 16.04.2027 | — |
| Uçuş testleri | 21.05.2027 | — |
| **Yarışma** | Ağustos–Eylül 2027 | — |

**Sonuç:** Kuyruğun sıralaması FDA'ya (58 gün) göre yapılır. Yarışmanın kendisi
1 yıldan uzak; ona göre optimize etmek bugün yanlış önceliktir.

---

## 2. FDA test uçuşu, yarışmadan FARKLI donanım istiyor

Şartname §5.3.2 ile §6 arasındaki fark kolayca gözden kaçıyor; ikisi aynı sistem
değil:

| | **FDA Görev Test Uçuşu** (§5.3.2, 30 Eylül) | **Yarışma** (§6, 2027) |
|---|---|---|
| Hava aracı | **Çoklu rotorlu, dikey iniş-kalkış (VTOL)** | **Sabit kanatlı**, mancınıkla fırlatma zorunlu |
| Alan | **20 × 20 m** | HTAB **50 × 50 m**, İHA-UB 300 × 300 m |
| İrtifa | **Asgari 30 m** | belirtilmemiş |
| Süre | Tüm operasyon **≤ 10 dakika** | İHA ≤ 15 dk, İKA ≤ 10 dk |
| Ağırlık | — | İHA ≤ 25 kg, İKA ≤ 10 kg (yük hariç) |

FDA puanı: `FDA = FDR × 0.85 + Drone Görev Test Uçuşu × 0.15`

**100 tam puan koşulu (§5.3.2):** gerçek zamanlı güzergâh tespitinin **alan hakemi
tarafından doğrulanıp onaylanması** ve kalkış + tespit + veri aktarımı + iniş
sürecinin **10 dakika içinde** tamamlanması. Kriterlerden birini sağlamayan, süreyi
aşan **veya yanlış güzergâh tespiti yapan takım 0 puan alır.**

⚠ **Açık risk:** Çoklu rotorlu VTOL drone ekipte **yok / belirsiz**. 58 gün var ve bu
donanım olmadan FDA'nın %15'lik bacağı otomatik olarak 0'dır. `TASK_QUEUE.md`
FAZ 0'ın en üstündeki kalem budur.

---

## 3. Puanlama duyarlılığı — yazılım neyi etkiler, neyi etkilemez

```
Puan  = 0.65 × Puan₂ + 0.20 × P + 0.15 × Puan₁

Puan₂ = K_zorluk × [ P_görev + (25000−m_İHA)/10 + (900−t_İHA)/5 + (900−t_hazırlık)/30
                     + (10000−m_İKA)/15 + (m_yük × 0.01) + (600−t_İKA)/15 − C_ceza ]

K_zorluk = 1.0 (Kolay) | 1.5 (Orta) | 2.0 (Zor)
P     = P_TI + P_uçuş + P_centilmenlik
Puan₁ = 0.10×ÖDR + 0.25×DDR + 0.55×FDA + 0.10×UHDR
```

`simulation/score.py` bu formülü **birebir doğru** uyguluyor (Tablo 6 ile karşılaştırıldı,
geçerlilik eşikleri dâhil). Yeniden yazılmayacak — yeni işlerde bu modül çağrılacak.

### Yazılımın doğrudan etkilediği terimler

| Terim | Azami katkı (K=1.0) | Yazılımdaki karşılığı |
|---|---|---|
| **P_görev = 600** | **600** (K=2.0'da **1200**) | Doğru güzergâh + İKA'nın H brandasına fiziksel teması |
| `(900−t_İHA)/5` | 180 | Tespitin hızı — İHA ne kadar erken iner |
| `(600−t_İKA)/15` | 40 | Rota uzunluğu ve sürüş verimi |
| `P_uçuş` | 200 / senaryo | İHA kırıma uğramaması + hedefi tespit + İKA'nın hareket etmesi |

### Yazılımın etkilemediği ama BASKIN olan terim

`(25000 − m_İHA)/10` → 25 kg limitte **0 puan**, 10 kg'lık bir İHA'da **1500 puan**.
Aynı şekilde `(10000 − m_İKA)/15` → 5 kg İKA'da 333 puan.

**Bu, görev puanından (600) büyüktür.** Yani ağırlık düşürme, algoritma
iyileştirmesinden daha çok puan getirir. Yazılım tarafı bunu değiştiremez; kaptanın
donanım önceliklendirmesinde bilmesi gereken bir gerçektir.

### Mutlak kesiciler (puan değil, sıfırlama)

- **Yanlış güzergâh tespiti → 0 puan** (§5.3.2, §6.2)
- **Hakem onayı alınmayan tespit geçersiz** (§6.2)
- **Veri akışının sağlanamaması → uçuş geçersiz** (§6.4)
- **İHA yere temas etmeden İKA hareket ederse görev başarısız** (§2.2.5)
- **Otonom hareket etmeyen İKA'nın görevi başarısız** (§2.2.5)
- İHA-UB dışına taşan uçuş = alan ihlali = başarısız (§6.2)
- Paraşüt açılmaması nedeniyle sert iniş → geçersiz (§6.4)
- Süre aşımı (İHA 15 dk / İKA 10 dk) → geçersiz (§6.4)

---

## 4. Mevcut mimari — veri akışı

```
   ┌──────────────────────── İHA (havada) ────────────────────────┐
   │                                                              │
   │  kamera karesi                                               │
   │       │                                                      │
   │       ▼                                                      │
   │  codes/rpi_inference.py                                      │
   │    _preprocess()          → LETTERBOX (kırpma YOK) + ışık norm.
   │    YOLOv8-seg (512)       → models/navitas_seg_v20_best.*    │
   │    get_masks()            → {0: zemin, 1: engel}             │
   │    _maskeleri_icerige_kirp() → dolgu bölgesini sıfırla       │
   │       │                                                      │
   │       ▼                                                      │
   │  codes/costmap_path_finder.py                                │
   │    serbest_alan()   Serbest = Zemin AND NOT Engel  (çıkarma EN SON)
   │    distanceTransform(DIST_MASK_PRECISE) → dt_px              │
   │    astar()          açıklık ağırlıklı, köşe kesme yasak      │
   │    rota_dogrula()   C-space'te doğrula (ham maskede DEĞİL)   │
   │       │  → durum: ACIK | KAPALI_DAR | KAPALI_KOPUK |         │
   │       │            DOGRULAMA_BASARISIZ | HEDEF_YOK | MASKE_YOK
   │       ▼                                                      │
   │  comms/protocol.py                                           │
   │    ACIK  → open_route(road, conf, waypoints, ref_xy)         │
   │    diğer → rota_yok(sebep, detay)      [NO_ROUTE]            │
   └───────────────────────────┬──────────────────────────────────┘
                               │ UDP (sim) / SiK Radio 433 MHz (saha)
                               │ newline ile çerçevelenmiş JSON
              ┌────────────────┴────────────────┐
              ▼                                 ▼
   ┌──── YKS (yer kontrol) ────┐      ┌──── İKA (kara aracı) ────┐
   │  comms/yks_gui.py         │      │  comms/ika_receiver.py    │
   │   hakem monitörü          │      │    latest / last_no_route │
   │   yeşil rota | kırmızı    │      │       │                   │
   │   "ROTA YOK" bandı        │      │       ▼                   │
   │   ACK + IKA_GO gönderimi  │      │  simulation/scripts/      │
   └───────────────────────────┘      │    ika_nav.navigate_route │
                                      └───────────────────────────┘
```

### Görüntü işleme mimarisi — üç katman ve monotonluk kuralı

> **Karar (4 Ağustos 2026): Yaklaşım C.** Tam gerekçe ve ölçümler `RESEARCH_NOTES.md`.
> Özet ilke: **"Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR."**

| Katman | İçerik | Rol |
|---|---|---|
| **1 — Otorite** | `0 = zemin` serbest alan segmentasyonu | Zemin olmayan **her şey** engeldir. Bilinmeyen → engel. **Varsayılan güvenli.** |
| **2 — Emniyet ağı** | `1 = engel` (seg) + araç (**DOTA OBB**, K-6) | Sınırlı, kritik nesne kümesi. **Yalnız çıkarır, asla eklemez.** |
| **3 — Geometri** | `distanceTransform ≥ R_gerekli` → C-space + açıklık ağırlıklı A* | `R_GEREKLI_M = 0,70/2 + 0,25 + 0,50 = 1,10 m` |

**Değişmez kural (invariant):**

```
serbest(Katman1 ∧ ¬Katman2)  ⊆  serbest(Katman1)
```

Katman 2'ye eklenen **hiçbir dedektör serbest alanı büyütemez**. Bu sayede yeni bir
dedektör eklemek **monotonik olarak güvenlidir** — sistemi ancak daha güvenli yapabilir.
`codes/costmap_path_finder.py:212-213` bunu fiilen sağlıyor (*"çıkarma en son, bundan
sonra hiçbir genişletme yapılmaz"*) ama **hiçbir test doğrulamıyor** → görev **S3**.

**Neden A (çoklu nesne segmentasyonu) değil:** Şartname §6 kapalı güzergâhları
*"fiziksel engeller (bariyer, enkaz simülasyonu **vb.**)"* ile kapatıyor — **"vb." =
sayılamaz küme.** A'nın bilinmeyen nesneye verdiği varsayılan "tespit edilmedi → boş →
geçilebilir" (fail-dangerous); B/C'ninki "zemin değil → engel" (fail-safe).

**Neden saf B değil:** Ölümcül hata yönü ölçüldü — modelin molozu "zemin" sanması.
v13 %37,7, v16 %31,6 moloza basma. Saf B'nin buna karşı ikinci savunma hattı yok;
Katman 2 o hattır.

**Performans bu kararı belirlemiyor** (ölçüldü, §Ölçülmüş uçtan uca hız).

### Modül sahipliği ve doğrulama betiği

| Modül | Sorumluluk | Doğrulama |
|---|---|---|
| `codes/rpi_inference.py` | Algı, letterbox, maske, şerit kararı | `codes/test_accuracy.py` |
| `codes/costmap_path_finder.py` | Serbest alan + A* + rota doğrulama | `codes/test_rota_sentetik.py` (**15/15 kapı**) |
| `codes/test_rota_guvenlik.py` | Üretim-uyumlu DOTA OBB kâhini ile araca çarpma ölçümü (COCO-seg geriye uyumlu) | kendisi |
| `tests/test_costmap_on_images.py` | ÖNCE/SONRA görsel kanıt sayfası | kendisi |
| `comms/protocol.py` | Mesaj tipleri + çerçeveleme | `comms/test_comms.py` |
| `simulation/scripts/ika_nav.py` | Waypoint sürüşü, failsafe | `simulation/scripts/navitas_sim.py` |
| `simulation/score.py` | Şartname puan formülü | `python score.py hedef_zor` |
| `scripts/copy_paste_augmentation.py` | Hibrit eğitim verisi üretimi (etiket sözleşmesinin **kaynağı**) | `52_sentetik_denetim.py` |

### Ölçülmüş uçtan uca hız — darboğaç costmap, sinir ağı değil

`results/jetson_fps_pc_smoke/ozet.json` (PC, RTX 5080 Laptop, `navitas_seg_v20_best.pt`;
zincir: kare oku → letterbox/çıkarım → `get_masks` → `rota_bul`):

| imgsz | çıkarım p50 | maske p50 | **costmap p50** | toplam p50 | toplam p95 | FPS |
|---|---|---|---|---|---|---|
| 640 | 26,5 ms | 3,2 ms | **51,2 ms** | 84,5 ms | 93,6 ms | **11,96** |
| 512 | 21,0 ms | 2,9 ms | **39,3 ms** | 66,2 ms | 66,7 ms | **15,12** |

🔴 **BU TABLO ARTIK GEÇERLİ DEĞİL — 2026-08-05'te yeniden ölçüldü (REVIEW_LOG D-14).**

`results/pc_referans_v17_20260805/` · sentetik arena 30 kare · 60 tekrar · RTX 5080 ·
letterbox düzeltmeleri (`36ca360`, `5f05e28`) sonrası:

| aşama | PyTorch p50 | ONNX FP16 p50 | pay |
|---|---:|---:|---:|
| **çıkarım** | **14,00 ms** | **14,79 ms** | **~%51** |
| maske | 2,23 ms | 2,31 ms | ~%8 |
| costmap | **8,89 ms** | **9,98 ms** | ~%32 |
| toplam | 27,38 ms | 29,23 ms | |
| FPS (p50) | 36,52 | 34,21 | |

Costmap **51,2 → 8,89 ms**; darboğaz **çıkarıma geçti**. İki ölçüm farklı girdi
kümesiyle yapıldı (eski `jetson_fps_pc_smoke`, yeni sentetik arena) ve aradaki
commit'ler letterbox yolunu değiştirdi — kıyaslanabilir değiller, ancak yukarıdaki
eski satır artık hiçbir güncel koşumu temsil etmiyor.

**Sonuç:** *"sınıf sayısı optimizasyonu boşa emektir, hızlandırma costmap'te
yapılır"* gerekçesi zayıfladı. Çıkarım baskın olduğu için INT8/TensorRT'nin
getirisi eskiden sanıldığından yüksek. Yine de sıra değişmez: Jetson'daki oran
**ölçülmeden** optimize edilmez (T17).

### 🔴 K-8 · KARE HIZI HEDEFİ — **3 FPS hedef, 1 FPS kabul edilen minimum**
*(Karar: Yunus, 2026-08-18. Önceki "15 FPS iç hedefi" **KALDIRILDI**.)*

Gerekli hız kapsama hesabından **0,9–2,6 FPS** (30 m irtifa, %80 örtüşme,
5–15 m/s). 15 FPS hiçbir zaman şartname şartı değildi ve ölçüm bütçesini
gereksiz yere sıkıyordu; kapsama hesabının üst ucunun biraz üstü hedef alındı.

| | değer | dayanak |
|---|---|---|
| **hedef** | **3 FPS** | kapsama hesabı üst ucu (2,6) + pay |
| **kabul edilen asgari** | **1 FPS** | kapsama hesabı alt ucu (0,9) |

**ÖLÇÜLEN DURUM (PC, RTX 5080, imgsz 640):** toplam p50 **84,5 ms → 11,96 FPS**
— hedefin **4 katı**, asgarinin **12 katı**.
Modül başlığı Jetson için "~2×" der (⚠ **ölçülmedi**) → tahmini **~6 FPS**,
hedefin 2 katı.

**DOĞRUDAN SONUÇ:** hız artık **tıkayıcı bir kısıt değildir**. Bu, iki açık
işi doğrudan etkiler:
- **T98** (KATMAN A 1024²'de 83 ms → ~12 FPS tavanı) — 3 FPS hedefinin
  4 katı. **Optimizasyon gerekmiyor**; T98 ölçüm kaydıyla kapanır.
- **T16/T17** (Jetson TensorRT + gerçek FPS) — hâlâ gerekli, çünkü Jetson'da
  **hiçbir ölçüm yok**; ama artık "15 FPS'e yetişme" değil "1 FPS'in üstünde
  kalma" sorusudur. Kapı: **T17 ölçümü ≥ 1 FPS**, hedef ≥ 3 FPS.

**ONNX FP16 parite kapısı GEÇTİ:** aynı 60 karede PyTorch ve ONNX **birebir aynı**
rota kararı (`KAPALI_DAR 24 · BELIRSIZ_TEK_KAPI 22 · MASKE_YOK 6 ·
BELIRSIZ_COKLU 6 · ACIK 2`). Beş ayrı durum, hepsi eşleşiyor.

⚠ **Jetson'da hiç ölçüm yok** — `jetson_fps.py` yalnız PC'de koşmuş
(`"platform": "Windows-11"`). İki PC koşusu birbiriyle **~100× çelişiyor**
(11,96 FPS vs 0,713 FPS); ısınma kareleri şüpheli, T17'de çözülecek.

---

## 5. Anayasa kısıtları — ölçülmüş uyum durumu

`CLAUDE.md` madde 4: *"Kod yazarken sadece OpenCV, NumPy ve pure Python `heapq`
kullan. SciPy/scikit-image YASAKTIR."*

**Durum: İHLAL YOK.** 3 Ağustos 2026 taraması:

| Kütüphane | Sonuç |
|---|---|
| `scipy` | **0 eşleşme** |
| `scikit-image` / `skimage` | **0 eşleşme** |
| `sklearn` | **0 eşleşme** |
| `networkx` | **0 eşleşme** |
| `torch` | yalnız `models/*_ncnn_model/model_ncnn.py` (Ultralytics'in ürettiği dosyalar) + `scripts/jetson_fps.py:132` (fonksiyon içi tembel import, CUDA yoklaması) |
| `matplotlib` | yalnız `simulation/scripts/harita_onizleme.py` (fonksiyon içi tembel import, yalnız görselleştirme) |

`codes/costmap_path_finder.py` bağımlılıkları: `heapq`, `cv2`, `numpy`, `logging`.

> **Not:** Medial-axis / skeletonize gibi `scipy.ndimage` ve `cv2.ximgproc`
> fonksiyonları yasak/yok olduğu için, koridor merkezinden geçme davranışı
> **açıklık ağırlıklı A\*** ile elde edildi (`LAMBDA_ACIKLIK=3.0`, `US_ACIKLIK=2.0`).
> Bu bilinçli bir ikamedir, eksiklik değil.

---

## 6. Karar kayıtları

**K-1 — ROS2 kurulmayacak.** Mevcut `comms/protocol.py` JSON/UDP + SiK Radio hattı
güçlendirilecek. Gerekçe: 58 gün içinde ROS2 kurulumu, sahada çalışan bir hattı
riske atar ve puan getirmez.

**K-2 — Sınıf-id sözleşmesi TEK YERDE sabitlenir.** Sevk edilen model
`0=traversable, 1=blocked`. Yeni etiketlenecek drone verisi `0=zemin, 1=engel,
2=hedef`.

⛔ **CANLI KUSURDU — çakışma gerçekleşmişti:**

| Kaynak | Sınıf `2`'nin anlamı |
|---|---|
| `scripts/copy_paste_augmentation.py:318-321` | **`2 = hedef`** (H brandası) |
| `simulation/scripts/iha_haritala.py:300` | **`2 = araç`** |
| `simulation/scripts/iha_haritala.py:336` | `engel_sinif_idler=(1, 2)` |

3 sınıflı veriyle eğitilmiş bir model `iha_haritala` yoluna verilirse **H brandası
ENGEL sayılır** → İKA hedefe hiçbir zaman ulaşamaz → `P_görev = 0` (600–1200 puan).

✅ **KAPATILDI 2026-08-05 (S2).** Çözüm: **iki ayrı ad alanı**, sayıları çakışmaz.
Sözleşme `codes/sinif_semasi.py`'de tek yerde:

```
EĞİTİM SINIFLARI      ZEMIN=0   ENGEL=1   HEDEF=2      (veri seti / model çıktısı)
COSTMAP KATMANLARI    KATMAN_ZEMIN=0  KATMAN_MOLOZ=1  KATMAN_ARAC=10
COSTMAP_ENGEL_KATMANLARI = (KATMAN_MOLOZ, KATMAN_ARAC)
```

`serbest_alan()` sözlük anahtarı kullanır (`if c in maskeler`), id'nin sayısal
değeri önemli değildir — yalnızca **çakışmaması** önemlidir. `KATMAN_ARAC=10`
eğitim uzayının (0–9) dışındadır; modül import anında `dogrula()` ile kendini
sınar, biri ileride bunu bozarsa **import anında patlar**.

Kapı: `codes/test_sinif_semasi.py` **8/8**, pozitif kontrol dahil — eski şemada
hedefin gerçekten ENGEL sayıldığı yeniden üretilerek testin boş-doğru olmadığı
kanıtlandı.

---

**K-8 — Model seçimi ölçütü: arena IoU TEK BAŞINA yeterli değil.**
*(2026-08-05, REVIEW_LOG D-12/D-18)*

Ölçüldü — 67 gerçek nadir drone karesi, `conf=0,25`, "kullanılabilir" = zemin
maskesi kare alanının ≥%5'i:

| model | kullanılabilir | ort zemin | arena IoU | eğitim geçmişi |
|---|---:|---:|---:|---|
| **v17** | **10/67** | %1,04 | **0,861** | sentetik arena fine-tune |
| v20 | 10/67 | %4,11 | — | sentetik arena + multi_scale |
| v15_ft2sinif | 23/67 | %24,07 | — | 10 sınıf ön-eğitim → 2 sınıf |
| v3 | 25/67 | %21,57 | — | RescueNet |
| **v5c** | **58/67** | **%48,65** | düşük | arena **görmedi** |

**Arena şampiyonu, gerçek nadir karede en kötü model.** Körlük tabanda değil,
sentetik arena fine-tune **adımında** oluşuyor — `karisim_arena.yaml`'ın kendi
yorumunda uyardığı katastrofik unutma gerçekleşmiş; karışım yapılmış ama karışımdaki
"gerçek" veri RescueNet'ti (afet sahnesi), arena da otopark da değil.

**Ölçülmüş bedeli:** `copy_paste_augmentation.py` v20 kâhiniyle 201 denemeden
yalnız **36** örnek üretebildi (165'i `zemin=0 px`). Aynı betik v5c @ conf 0,05 ile
**448** örnek üretti.

⇒ **Bağlayıcı kural:** bir model sevk edilmeden önce **iki kapıdan** geçer:
1. arena başarımı (IoU / moloza basma), ve
2. **gerçek nadir karede zemin çıkarabilme** (`data/raw_frames`, ≥%5 zemin).
İkincisini geçemeyen model, birincisi ne olursa olsun aday değildir.
Düzeltme görevi: `TASK_QUEUE.md` **S2**.

**K-6 — Kritik nesne kâhini DOTA OBB'dir, COCO-seg DEĞİL.** Ölçüldü: aynı hava
fotoğrafında COCO `yolov8m-seg.pt` **2 araç**, DOTA `yolov8m-obb.pt` **93 araç**
buluyor. COCO güven eşiğini 0,35 → 0,02 indirmek 18 karede yine **sıfır** kesişim
verdi — eşik ayarı çözüm değil, **domain uyumsuzluğu** (COCO yer seviyesi; şartname
§5.3.2 asgari 30 m nadir görüntü istiyor). `iha_haritala.py:67-68` ve
`test_rota_guvenlik.py` bunu doğru yapıyor; `scripts/copy_paste_augmentation.py:37,151,340`
**hâlâ COCO kullanıyor** → görev **S1** (tıkayıcı).

**K-7 — Çoklu sınıf yalnız ÖN-EĞİTİM yardımcı görevidir, çıktı kafası değil.**
Ölçüldü: `blocked` AP50 0,4329 → 0,5371 (+%24) yükseltildi, **sistem davranışı hiç
değişmedi** (6 `analyze_path` çağrısının tamamı yalnız `masks[0]` geçiriyor). Buna
karşılık 10 sınıflı ön-eğitim → 2 sınıfa fine-tune (v15) arenada **kazandırdı**:
moloza basma %2,7 · aynı dönemde ön-eğitimsiz v13 %37,7. `dataset/rescuenet_11sinif/`
bu ön-eğitim kümesidir.

**K-3 — Model seçimi RescueNet mAP'ine göre YAPILMAZ.** Ölçüldü: mAP lideri v13
arenada **en kötü** model (%37,7 moloza basma), mAP'i en düşük v17 arenada en iyi.
mAP arena sıralamasını **tersine çeviriyor**. Geçerli ölçüt hiyerarşisi:

1. **Birincil:** karar doğruluğu (hangi güzergâhın açık olduğu) — şartname §5.3.2
   gereği yanlış güzergâh 0 puan.
2. **Sert kısıt:** moloza basma oranı — İKA'nın yapısal bütünlüğü §2.2.6 gereği
   görev şartı.
3. **Reddedilen:** genel mAP ve blocked AP50. `analyze_path`'in 6 çağrı yerinin
   tamamı yalnız `masks[0]` geçiriyor; `blocked` sınıfının sistem kararına
   **nedensel yolu yok**.
4. **Gürültü tabanı:** maske sd ≈ 0,029–0,032. **0,04'ten küçük farklar gürültüdür**,
   eşleştirilmiş test (McNemar) olmadan yorumlanmaz.

**K-4 — Ölçüm yolu üretim yolundan ayrışmayacak.** `test_accuracy.py` kendi
`analyze_path` kopyasını taşıdığı sürece raporlanan doğruluk sayıları sevk edilen
karar kuralını ölçmez. Bu bir "teknik borç" değil, **ölçüm geçersizliğidir**.

**K-5 — Kaptanın dosyaları silinmez.** `doc/` klasörü repoda tutulmaz.

---

## 7. Bilinen kusurlar — özet

Çekişmeli denetimden (bağımsız çürütme ajanlarıyla) **11 kusur ayakta kaldı, 0 tanesi
çürütüldü**. Tam kanıtlar (çalıştırılan komut + gerçek çıktı) `REVIEW_LOG.md`
dosyasındadır. Görev karşılıkları `TASK_QUEUE.md` FAZ 1'dedir.

| Görev | Dosya:satır | Şiddet |
|---|---|---|
| T0 | `auto_orchestrator.py:9` — emoji, Türkçe Windows'ta (cp1254) çıktı yönlendirilince `UnicodeEncodeError`; orkestratör çöküyor ve hiçbir manuel görev yüzeye çıkmıyor | **TIKAYICI** |
| T1 | `codes/rpi_inference.py` — letterbox commit'e girmemiş, temiz klon `ImportError` | KRİTİK |
| T2 | `simulation/scripts/ika_nav.py:319` — geçici NO_ROUTE görevi kalıcı iptal ediyor | KRİTİK |
| T3 | `codes/test_rota_guvenlik.py:117` — tohum bandı dolguya düşüyor, 0/18 karede ölçüm yok | KRİTİK |
| T4 | `tests/test_costmap_on_images.py:238` — çekimserlik kapısı yok, boş geçiş | KRİTİK |
| T5 | `codes/rpi_inference.py:151` — şerit sınırları dolgulu tuvale göre | ÖNEMLİ |
| T6 | `simulation/scripts/ika_nav.py:232` — sürüş sırasında NO_ROUTE yok sayılıyor | ÖNEMLİ |
| T7 | `codes/rpi_inference.py:138` — `min_area_ratio` dolgulu tuval alanına göre | ÖNEMLİ |
| T8 | `codes/test_accuracy.py:83` — ıraksak `analyze_path` kopyası | ÖNEMLİ |
| T9 | `codes/test_rota_guvenlik.py:170` — `mpp=None`'da eşik 27,9 px → 1,10 px | ÖNEMLİ |
| T10 | `simulation/scripts/navitas_sim.py:169` — erken `return`, çökmüş thread'de exit 0 | KÜÇÜK |
| T11 | `comms/iha_sender.py:87` — `--no-route` adres yokken `TypeError` | KÜÇÜK |

### Strateji araştırmasında bulunan kusurlar (4 Ağustos 2026)

Kanıtlar: `RESEARCH_NOTES.md` §4–§5 ve `REVIEW_LOG.md`. Görevler `TASK_QUEUE.md` FAZ 4.

| Görev | Dosya:satır | Şiddet |
|---|---|---|
| **S1** | `scripts/copy_paste_augmentation.py:37,151,340` — COCO kâhini araçların ~%98'ini kaçırıyor; kaçanlar **"zemin" olarak etiketleniyor** (sınıf 0 tam kare dikdörtgen). v16'yı %2,7→%31,6 çökerten *etiketsiz engel* hatasının aynısı | **TIKAYICI** |
| **S2** | `copy_paste_augmentation.py:318-321` (`2=hedef`) ↔ `iha_haritala.py:300,336` (`2=araç`, `engel_sinif_idler=(1,2)`) — H brandası engel sayılır, `P_görev=0` | KRİTİK |
| **S3** | Monotonluk invariantı (`K1∧¬K2 ⊆ K1`) hiçbir testte doğrulanmıyor | KRİTİK |
| **S4** | İki ıraksak karar yolu: `rpi_inference`/`iha_perceive` saf B (emniyet ağı **yok**), `iha_haritala` C | KRİTİK |
| **S5** | Çıkarım `imgsz` sabitlenmemiş — v17: 640→IoU 0,861, 960→0,034 (kaplama %96,1) | ÖNEMLİ |
| **S6** | `hedef` sınıfı hedef tohumu olarak `rota_bul`'a bağlı değil | ÖNEMLİ |
| **S7** | `48_arena_iou.py` / `54_arena_cozunurluk.py` yalnız `print` — makine-okunur çıktı yok, regresyon takibi imkânsız | ÖNEMLİ |
| **S8** | FDA profili (20×20 m, ≥30 m) sentetik üretece girmemiş | ÖNEMLİ |

---

## 8. Şartnameden çıkan, koda henüz yansımamış zorunluluklar

| § | Kural | Kodun durumu | Görev |
|---|---|---|---|
| 2.2.5 | İKA intikali **YKS'den manuel tetiklenir** | `IKA_GO` ACK'li kalıcı latch ve atomik motor kapısına bağlı; hedef test 9/9 | T12 · READY_FOR_REVIEW |
| 2.2.5 | **İHA yere temas etmeden İKA hareket edemez**; ihlali görevi başarısız kılar | Ayrı ACK'li `IHA_LANDED`; OPEN_ROUTE + IKA_GO + iniş kanıtı ortak deadline ve atomik motor kapısında zorunlu; hedef test 10/10 | T13 · READY_FOR_REVIEW |
| 5.3.2 | FDA: 20×20 m alan, ≥30 m irtifa | Sentetik arena ve ölçek sabitleri **50×50 m HTAB**'a göre kurulu | T14 |
| 5.3.2 | Tüm operasyon ≤ 10 dk | Uçtan uca bütçe ölçümü yok; tüm FPS sayıları **tahmin** | T15 |
| 2.2.3 / 6.2 | Aktarım İHA **havada iken** tamamlanmalı, hakem monitörden onaylamalı | `yks_gui` hakem ekranı + ACK **çalışıyor** (gerçek Tk penceresiyle doğrulandı) | ✔ |
| 6.4 | Veri akışının sağlanamaması uçuşu geçersiz kılar | NO_ROUTE zinciri **kuruldu ve tel üzerinde çalışıyor**; İKA tarafı hatalı (T2/T6) | kısmen |

---

## 9. Açık riskler

| # | Risk | Etki | Azaltım |
|---|---|---|---|
| R1 | **FDA için çoklu rotor VTOL drone yok** | FDA'nın %15'lik bacağı otomatik 0 | `TASK_QUEUE.md` FAZ 0 #1 — 58 gün, en yüksek öncelik |
| R2 | **Gerçek arena test kümesi yok** — tüm arena sayıları n=2 ve **YZ ile üretilmiş** iki görselden (`test_images/ai/`). `44_karar_kurali.md:110-114`: *"bu ayak yön verir, kanıtlamaz"* | Model seçimi fiilen **körlemesine** yapılıyor | Mevcut drone kareleri → **eğitim**; **farklı yer/günde ikinci çekim → bakır test** (karar 4 Ağu 2026, FAZ 0-B) |
| **R7** | **Eğitim verisi araçları zemin olarak etiketliyor** (S1) — COCO kâhini 93 aracın 2'sini buluyor | Bozuk veriyle eğitim GPU-gün israfı; v16 çöküşünün tekrarı | S1 düzeltilmeden **yeni eğitim koşulmaz** |
| **R8** | Sınıf `2` iki dosyada farklı anlamda (S2) | H brandası engel sayılırsa `P_görev=0` | Sözleşme tek yerde sabitlenir (K-2, S2) |
| R3 | Jetson'da TensorRT sürümü donanıma bağlı | PC'de üretilen `.engine` Jetson'da **çalışmaz** | İki aşamalı export; `.engine` derlemesi Jetson üzerinde (FAZ 3) |
| R4 | v17 modeli **çözünürlük kırılgan** — arena IoU 0,861 yalnız imgsz=640'ta; 960'ta %96 boyuyor. `multi_scale` (v20) düzeltmedi. FDA irtifası ≥30 m ve **değişken** | Yanlış çözünürlükte tam başarısızlık | Çıkarım `imgsz` sabitlenip testle korunur → **S5** |
| R5 | ~~3 sınıflı veri ↔ 2 sınıflı model id çakışması riski~~ → **GERÇEKLEŞTİ**, R8'e taşındı | — | bkz. R8 / S2 |
| R6 | Uzun eğitimler konsol kapanınca izsiz ölüyor | Saatlerce iş kaybı | `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` olmadan eğitim başlatılmaz |

---

## 10. Faz planı ve kapılar

| Faz | İçerik | Çıkış kapısı |
|---|---|---|
| **0** | İnsan müdahalesi: donanım temini, kurulum, etiketleme | Orkestratör tüm `[REQUIRES_HUMAN]` kalemlerini `[HUMAN_COMPLETED]` yapmış |
| **1** | 11 doğrulanmış kusur | `test_rota_sentetik.py` **15/15**; temiz klonda `test_accuracy.py --help` ve `test_batch.py --help` **exit 0**; `test_rota_guvenlik.py` ham kipte ihlal oranı **> 0,10** |
| **2** | Şartname uyumu (IKA_GO, iniş kapısı, FDA parametrizasyonu) | `navitas_sim.py` İHA inişi sinyallenmeden İKA'yı hareket ettirmiyor; 20×20 m profilinde 15/15 |
| **3** | Donanım entegrasyonu | Jetson'da uçtan uca **ölçülmüş** p50/p95 FPS; tahmin yok |
| **0-B** | Gerçekten açık insan işleri (drone temini, etiketleme, **ikinci çekim**) | Bakır test kümesi mevcut ve eğitime hiç girmemiş |
| **4** | **Serbest alan mimarisi** (S1–S8) | S1: veri üretecinde araç kâhini DOTA OBB · S2: sınıf-id sözleşmesi tek yerde · S3: monotonluk invariantı testi **geçiyor** · S5: `imgsz` sabit ve testle korunuyor |

**Eğitim sırası ZORUNLU:** `S1 → S2 → veri üretimi → eğitim`. S1 düzeltilmeden üretilen
veri araçları zemin sayar; bozuk veriyle eğitim GPU-gün israfıdır (R7).

**Değişmeyen genel kapı:** her görevden sonra
`O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py`
→ **15/15**. Düşerse o görev geri alınır ve nedeni `REVIEW_LOG.md`'ye yazılır.
