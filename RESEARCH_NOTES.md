# NAVITAS — ARAŞTIRMA NOTLARI

## Görüntü işleme stratejisi: A / B / C değerlendirmesi ve karar

| | |
|---|---|
| **Tarih** | 4 Ağustos 2026 |
| **Yazan** | Mimar (Claude / Opus 5) |
| **Karar durumu** | **VERİLDİ — Yaklaşım C, katı yapıyla** |
| **İlgili** | `ARCHITECT_PLAN.md` (K-6, K-7) · `TASK_QUEUE.md` FAZ 4 · `REVIEW_LOG.md` (S1, S2) |

> **Kanıt kuralı:** Bu dosyadaki her sayı ölçülmüştür ve kaynağı belirtilmiştir.
> Ölçülmemiş olan **BULUNAMADI** diye yazılır, tahmin edilmez.

---

## 0. Soru

Üç yaklaşım karşılaştırılacak:

- **A — Çoklu nesne segmentasyonu:** engelleri, araçları, molozları tek tek etiketle ve tespit et.
- **B — Sadece serbest alan:** yalnız sürülebilir zemini eğit; zemin dışındaki **her şeyi** doğal engel kabul et. `cv2.distanceTransform` ile İKA genişliği + emniyet marjı koridor filtresinden geçir.
- **C — Hibrit:** serbest alan + kritik nesne maskelemesi.

Değerlendirme eksenleri: **şartname**, **OpenCV kısıtları** (anayasa madde 4), **Jetson Orin NX FP16 performansı**.

---

## 1. KARAR

> ### Yaklaşım **C** — ama katı bir yapıyla:
> ## "Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR."

| Katman | İçerik | Rol |
|---|---|---|
| **1 — Otorite** | `0 = zemin` serbest alan segmentasyonu | Zemin olmayan **her şey** engeldir. Bilinmeyen → engel. Açık kümeye karşı **varsayılan güvenli**. |
| **2 — Emniyet ağı** | `1 = engel` (segmentasyon) + araç (**DOTA OBB**) | Sınırlı, kritik nesne kümesi. **Yalnız çıkarır, asla eklemez.** |
| **3 — Geometri** | `distanceTransform ≥ R_gerekli` → C-space + açıklık ağırlıklı A* | Zaten mevcut ve doğrulanmış (15/15 sentetik kapı) |

### Değişmez kural (invariant)

```
serbest(Katman1 ∧ ¬Katman2)  ⊆  serbest(Katman1)
```

Katman 2'ye eklenen **hiçbir dedektör serbest alanı büyütemez.** Bu sayede yeni bir
dedektör eklemek **monotonik olarak güvenlidir**: sistemi ancak daha güvenli yapabilir,
asla daha az. Kod bunu fiilen sağlıyor (`codes/costmap_path_finder.py:212-213`,
*"çıkarma en son, bundan sonra hiçbir genişletme yapılmaz"*) ama **hiçbir test bunu
doğrulamıyor** → görev **S3**.

### Yaklaşım A nerede yaşar

**Çıktı kafası olarak DEĞİL, yalnız ön-eğitim yardımcı görevi olarak.** Gerekçe §2.2 ve §2.3.

---

## 2. Karar gerekçesi — ölçümler

### 2.1 Şartname, A'yı yapısal olarak dışlıyor

Şartname §6:

> *"…diğer iki güzergâh ise fiziksel engeller (bariyer, enkaz simülasyonu **vb.**) ile tamamen kapatılacaktır."*

**"vb." = sayılamaz küme.** İçinde "vb." geçen bir listeyi etiketlemek mümkün değildir.
Yarışma günü eğitim kümesinde bulunmayan bir engel tipi çıkarsa:

| Yaklaşım | Bilinmeyen nesneye verdiği varsayılan | Sonuç |
|---|---|---|
| **A** | "tespit edilmedi → boş → geçilebilir" | **fail-dangerous** — araç içine girer |
| **B / C** | "zemin değil → engel" | **fail-safe** — araç etrafından dolaşır |

Bağlı şartname maddeleri:
- **§2.2.6** — İKA hedefe ulaştığında *"yapısal bütünlüğünü koruyor olması ve taşıdığı yükü/yükleri eksiksiz muhafaza etmesi zorunludur; aksi takdirde ilgili görev başarısız sayılır."*
- **§5.3.2 / §6.2** — *"yanlış güzergah tespiti yapan takımlar 0 puan alarak görevden başarısız sayılacaktır."*
- **§2.1** — HTAB içinde *"afet bölgesini simüle eden moloz yığınları ve engeller"*.

Zemin etiketlemek ise **kapalı** bir problemdir: zemin zemindir, gerisi engeldir.

---

### 2.2 A, çıktı katmanı olarak ÖLÇÜLDÜ — sistem davranışına etkisi SIFIR

`blocked` sınıfının doğruluğu **0,4329 → 0,5371** (+%24) yükseltildi.
**Sistemin verdiği kararlar hiç değişmedi.**

Sebep — altı `analyze_path` çağrısının **tamamı** yalnız `masks[0]` (traversable) geçiriyor:

| Çağrı yeri | Geçen maske |
|---|---|
| `codes/rpi_inference.py:387` | `analyze_path(masks[0], icerik=icerik)` |
| `codes/rpi_inference.py:467` | `analyze_path(masks[0], icerik=icerik)` |
| `codes/rpi_inference.py:527` | `analyze_path(masks[0], icerik=icerik)` |
| `simulation/scripts/iha_perceive.py:106` | `analyze_path(masks[0])` |
| `codes/test_accuracy.py:239` | `analyze_path(masks[0])` |
| `comms/yks_gui.py:883` | `trav` — engel **dolaylı** oyulmuş (`:880` `trav[blok>0]=0`) |

`masks[1]` yalnız iki yerde geçiyor: `test_batch.py` (ekrana yüzde basıyor) ve
`iha_perceive.py:92` (sözlükte taşınıyor, kullanılmıyor).

> **Kaynak:** `BULGULAR_20260720.md` §11B — *"blocked AP50'yi 0,4329 → 0,5371'e çıkarmamız sistemin davranışını HİÇ değiştirmedi."*

**Sonuç:** Çoklu sınıf etiketleme emeğinin karar yoluna **nedensel bağı yok**.

---

### 2.3 A, ön-eğitim yardımcı görevi olarak KAZANDIRDI

| Model | Ön-eğitim | RescueNet mAP50 | **Arena moloza basma** |
|---|---|---|---|
| **v13** | yok | **0,6794** (en yüksek) | **%37,7** (en kötü) |
| **v15** | **10 sınıf → 2 sınıfa fine-tune** | 0,6550 | **%2,7** |

`dataset/rescuenet_11sinif/data.yaml` bu ön-eğitim kümesi olarak zaten mevcut
(`nc: 10` — traversable, blocked, water, building×4, vehicle, tree, pool).

> **Kaynak:** `40_surum_degerlendirme.py:161` — *"10 sınıflı yardımcı görev ön eğitimi (v15): mAP'te değil ARENADA kazandırdı."*

**Sonuç:** Çoklu sınıf, **temsil öğrenmeye** yarıyor; **çıktı kafasına** değil.

---

### 2.4 B'nin ölümcül zaafı ölçüldü: yanlış-pozitif zemin

Model molozu "zemin" sanarsa araç molozun içine sürer. İki sürümde ölçüldü:

| Model | **Moloza basma @0,25** | Kaplama | Not |
|---|---|---|---|
| **v13** | **%37,7** | %43,4 (görüntünün %84,7'sini boyuyor) | mAP lideri |
| **v16** | **%31,6** | %39,6 (arenanın %79'unu boyuyor) | etiketsiz moloz → **11× kötüleşme** (v15'te %2,7 idi) |
| **v15** | %2,7 | %17,7 | 10 sınıf ön-eğitimli |
| **v17** | **%0,0** (gerçek, körlük değil) | **%4,2** (yer gerçeği %3,6) · kesinlik **0,863** | arena IoU `1.jpg` **0,861** |
| v9 | %0,0 — **TAM KÖR**, çıktı üretmiyor | %<1 | sıfır bedava, başarı değil |

> **Kaynak:** `BULGULAR_20260720.md` §13a/13e/13f · `44_karar_kurali.md:75-84`

**Saf B'nin bu hataya karşı ikinci savunma hattı yoktur.** C'de Katman 2 vardır: seg
modeli molozu kaçırsa bile araç dedektörü aracı yakalar ve serbest alandan çıkarır.

---

### 2.5 mAP, arena sıralamasını TERSİNE çeviriyor

> `44_karar_kurali.md:75-84` (aynen):
> *"mAP'e göre seçseydik arenada en kötü modeli üretime alacaktık."*

| Model | mAP50 | Moloza basma |
|---|---|---|
| v13 | **0,6794** (en yüksek) | **%37,7** (en kötü) |
| v9 | 0,6787 | %0 — ama **tam kör** |
| v15 | 0,6550 | %2,7 |
| **v17** | **0,6355** (en düşük) | **%0,0** + `1.jpg` IoU **0,861** |

**Ölçüm gürültüsü tabanı:** mask mAP50 standart sapması **0,025–0,032**
(`44_karar_kurali.md:14-28`) → **0,04'ten küçük farklar gürültüdür**, eşleştirilmiş
test (n=40, galibiyet ≥35/40) olmadan yorumlanamaz.

**Sonuç:** Bu araştırmadaki hiçbir karar mAP'e dayandırılmadı.

---

### 2.6 Katman 2'nin kâhini: COCO değil **DOTA OBB** — ölçüldü

Aynı hava fotoğrafı (896×896), aynı kare:

| Kâhin | Bulunan araç |
|---|---|
| COCO `yolov8m-seg.pt` | **2** |
| DOTA `yolov8m-obb.pt` | **93** (small vehicle + large vehicle) |

Eşik ayarı **çözüm değil**: COCO güven eşiği 0,35 → **0,02**'ye indirildi, 18 karede
yine **sıfır** kesişim çıktı.

**Kök neden:** domain uyumsuzluğu. COCO yer seviyesi fotoğraflarla eğitilmiştir;
şartname §5.3.2 **asgari 30 m irtifadan nadir** görüntü istiyor.

Üretim algı hattı bunu zaten doğru yapıyor:
```python
# simulation/scripts/iha_haritala.py:67-68
DEFAULT_ARAC_MODEL = ROOT / "yolov8m-obb.pt"
ARAC_SINIFLERI = {"small vehicle", "large vehicle"}
```

> **Kaynak:** `REVIEW_LOG.md` — *"T3 asıl 18-kare kapı ve kâhin teşhisi · 2026-08-04"*

⚠ **Ama veri üreteci hâlâ COCO kullanıyor** → bkz. §4, görev **S1**.

---

### 2.7 Jetson performansı bu kararı BELİRLEMİYOR

Ölçülmüş — `results/jetson_fps_pc_smoke/ozet.json` (PC, RTX 5080 Laptop, model
`navitas_seg_v20_best.pt`, zincir: kare oku → letterbox/çıkarım → `get_masks` → `rota_bul`):

| imgsz | çıkarım p50 | maske p50 | **costmap p50** | toplam p50 | toplam p95 | FPS |
|---|---|---|---|---|---|---|
| 640 | 26,5 ms | 3,2 ms | **51,2 ms** | 84,5 ms | 93,6 ms | **11,96** |
| 512 | 21,0 ms | 2,9 ms | **39,3 ms** | 66,2 ms | 66,7 ms | **15,12** |

> ### Darboğaz sinir ağı DEĞİL, costmap — çıkarımın ~2 katı.

Gerekli hız, kapsama hesabından (30 m irtifa, %80 örtüşme, 5–15 m/s):
**0,9–2,6 FPS** (`BULGULAR §7`). 15 FPS **şartname şartı değil**, takımın iç hedefi.

**Sınıf sayısının (nc = 1 / 2 / 3) maliyeti: hiçbir yerde ÖLÇÜLMEMİŞ.**
Yapısal olarak YOLOv8-seg mask prototiplerini sınıflar arasında **paylaşır**; sınıf
sayısı yalnız tespit kafasının çıktı boyutunu değiştirir. Beklenen fark ölçüm
gürültüsünün altındadır — **ama bu bir ölçüm değil, mimari çıkarımdır ve öyle
işaretlenmiştir.**

> **Sonuç: A/B/C seçimi performansla gerekçelendirilemez. Güvenlikle gerekçelendirilir.**

⚠ **Jetson'da hiç ölçüm yok.** `scripts/jetson_fps.py` yalnız PC'de koşmuş
(`"platform": "Windows-11"`, `"cuda_adi": "RTX 5080 Laptop GPU"`). Ayrıca iki PC koşusu
birbiriyle **~100× çelişiyor** (`jetson_fps_pc_smoke` 11,96 FPS vs
`jetson_fps_pc_smoke_dogrulanmis` 0,713 FPS) — ısınma karelerinin ölçüme dâhil
edilmesinden şüpheleniliyor; T17'de çözülecek.

---

### 2.8 OpenCV kısıtı (anayasa madde 4) — üç yaklaşımda da sağlanıyor

Tarama sonucu: `scipy` / `scikit-image` / `sklearn` / `networkx` → **0 eşleşme**.

`codes/costmap_path_finder.py` bağımlılıkları: `heapq`, `cv2`, `numpy`, `logging`.

Medial-axis / skeletonize (`scipy.ndimage`, `cv2.ximgproc`) yasak/yok olduğu için
koridor merkezinden geçme davranışı **açıklık ağırlıklı A\*** ile elde edildi:
```
maliyet = 1.0 + LAMBDA_ACIKLIK * (u ** US_ACIKLIK)     # 3.0, 2.0
```
Bu bilinçli bir ikamedir, eksiklik değil. **Üç yaklaşım da bu kısıt altında
uygulanabilir**; kısıt ayırt edici değildir.

Güvenlik yarıçapı:
```
R_GEREKLI_M = IKA_GENISLIK_M/2 + MASKE_HATA_M + TAKIP_HATA_M
            = 0,70/2 + 0,25 + 0,50 = 1,10 m
```

---

## 3. Yaklaşım karşılaştırma tablosu

| Ölçüt | **A — Çoklu nesne** | **B — Serbest alan** | **C — Hibrit (SEÇİLEN)** |
|---|---|---|---|
| Bilinmeyen engele varsayılan | boş → **geçilebilir** ⛔ | zemin değil → engel ✅ | zemin değil → engel ✅ |
| Şartname "vb." açık kümesi | **kapsayamaz** ⛔ | kapsar ✅ | kapsar ✅ |
| Yanlış-pozitif zemine karşı savunma | dolaylı | **yok** ⚠ | **var** (Katman 2) ✅ |
| Etiketleme maliyeti | **en yüksek** (sınıf başına) | **en düşük** (tek sınır) | düşük + sınırlı nesne kümesi |
| Nadir sınıflarda AP düşüşü | **evet** ⛔ | yok | sınırlı |
| Karar yoluna nedensel bağ | **ölçüldü: yok** ⛔ | var | var |
| Ön-eğitim değeri | **ölçüldü: var** ✅ | — | ✅ (A'yı burada kullanır) |
| Jetson FP16 maliyeti | ölçülmedi ~eşit | ölçülmedi ~eşit | ölçülmedi ~eşit |
| OpenCV kısıtı | uyumlu | uyumlu | uyumlu |
| Mevcut kodla uyum | uyumsuz | kısmen | **zaten kurulu** ✅ |

**C zaten üretimde kısmen çalışıyor:** `iha_haritala.py:300,336`
```python
costmap_maskeleri = {0: masks[0], 1: masks[1], 2: arac}
plan_sonucu = rota_bul(costmap_maskeleri, ..., engel_sinif_idler=(1, 2), ...)
```

---

## 4. Araştırma sırasında bulunan iki TIKAYICI kusur

Bunlar strateji kararından **daha acildir**; düzeltilmeden yeni eğitim koşulmamalıdır.

### S1 · TIKAYICI · Veri üreteci araçları ZEMİN olarak etiketliyor

`scripts/copy_paste_augmentation.py`

```python
COCO_ARAC_SINIFLARI = (2, 3, 5, 7)                                    # :37
maskeler = get_masks(sonuc, ..., sinif_idler=COCO_ARAC_SINIFLARI)     # :151
ayrac.add_argument("--arac-model", type=Path,
                   default=KOK / "yolov8m-seg.pt")                    # :340
```

Etiket yazımı (`:295-300`):
```python
satirlar = ["0 0.000000 0.000000 1.000000 0.000000 1.000000 1.000000 0.000000 1.000000"]
satirlar.extend(poligon_satirlari(1, engel, min_alan))
satirlar.extend(poligon_satirlari(2, hedef, min_alan))
```
**Sınıf 0 (zemin) daima TAM KARE dikdörtgen.** `engel` maskesine girmeyen her nesne
yalnız bu dikdörtgenin altında kalır → **"zemin" etiketi alır**.

§2.6'daki ölçümle birleştirince: COCO 93 aracın **2'sini** buluyor →
**üretilen eğitim verisinde araçların ~%98'i "sürülebilir zemin" olarak etiketleniyor.**

Bu, v16'yı %2,7'den **%31,6'ya** çökerten *"etiketsiz engel"* hatasının birebir aynısıdır
ve sentetik üretecin en kritik tasarım kuralının ihlalidir:

> `51_sentetik_arena.py` — *"Moloz her zaman blocked şeridin içindedir → **ETİKETSİZ MOLOZ YOK.**"*

**Düzeltme:** kâhini DOTA OBB'ye çevir (`yolov8m-obb.pt`, `small vehicle`/`large vehicle`).
`iha_haritala._arac_maskesi` (`:228-255`) bu dönüşümü zaten uyguluyor — **yeniden yazma, kullan.**

---

### S2 · KRİTİK · Sınıf-id çakışması canlı (K-2 riski gerçekleşti)

| Kaynak | Sınıf `2`'nin anlamı |
|---|---|
| `scripts/copy_paste_augmentation.py:318-321` | **`2 = hedef`** (H brandası) |
| `simulation/scripts/iha_haritala.py:300` | **`2 = araç`** |
| `simulation/scripts/iha_haritala.py:336` | `engel_sinif_idler=(1, 2)` |

3 sınıflı veriyle eğitilmiş bir model `iha_haritala` yoluna verilirse
**H brandası ENGEL sayılır** → İKA hedefe hiçbir zaman ulaşamaz → `P_görev = 0`
(şartname Tablo 6: 600 puan, K_zorluk ile 1200'e kadar).

**Düzeltme:** sınıf-id sözleşmesini **tek bir yerde** sabitle ve her iki tarafı oradan oku.

---

## 5. Diğer boşluklar

| # | Boşluk | Kanıt |
|---|---|---|
| **S3** | Monotonluk invariantı test edilmiyor | `serbest_alan` doğru; hiçbir test `K1∧¬K2 ⊆ K1` iddiasını sınamıyor |
| **S4** | İki ıraksak karar yolu | `rpi_inference`/`iha_perceive` = **saf B** (emniyet ağı yok); `iha_haritala` = **C** |
| **S5** | `imgsz` sabitlenmemiş | v17: 640 → IoU **0,861** (kaplama %4,2) · 960 → **0,034** (kaplama **%96,1**) · 1280 → 0,041 · 1600 → 0,018. `multi_scale` (v20) **düzeltmedi** (%96,1 → %90,7). FDA irtifası ≥30 m ve **değişken** |
| **S6** | `hedef` sınıfı hedef tohumu olarak bağlı değil | `rota_bul` yalnız `yol_sinif_idler` + `engel_sinif_idler` okuyor |
| **S7** | Arena ölçüm araçları makine-okunur çıktı üretmiyor | `48_arena_iou.py` / `54_arena_cozunurluk.py` sadece `print`; sayılar elle `BULGULAR_20260720.md`'ye kopyalanmış → **regresyon takibi imkânsız** |
| **S8** | FDA profili sentetik üretece girmemiş | Üreteç 50×50 m HTAB'a göre; FDA **20×20 m, ≥30 m irtifa** |

---

## 6. Veri seti stratejisi (kullanıcı kararı, 4 Ağustos 2026)

| Veri | Kullanım |
|---|---|
| Mevcut drone kareleri (4 video + 6 foto) | **EĞİTİM** — 3 sınıfla etiketlenecek (zemin / engel / hedef) |
| **Farklı yer ve günde ikinci çekim** | **BAKIR TEST** — eğitime hiç girmeyecek |

**Neden ikinci çekim şart:** Şu anki **tüm** arena sayıları n=2 ve **yapay zekâ ile
üretilmiş** iki görselden geliyor (`test_images/ai/1.jpg`, `2.png`). `44_karar_kurali.md:110-114`
bunu açıkça sınırlıyor: *"bu ayak **yön verir, kanıtlamaz**."* Model seçimi fiilen
**körlemesine** yapılıyor (risk R2).

Aynı otoparktan train/test bölmek bu körlüğü **gizler ama çözmez** — bölümler aynı
sahneden geldiği için bağımsız olmaz.

---

## 7. BULUNAMADI — ölçülmemiş, tahmin edilmedi

- **Jetson (veya herhangi bir gömülü donanım) üzerinde ölçülmüş FPS** — yok.
- **TensorRT `.engine` ölçümü** — yok (`model_dosyasi_yok`).
- **ONNX Runtime ölçümü** — yok (`onnxruntime` kurulu değil).
- **nc = 1 / 2 / 3 çıkarım maliyeti karşılaştırması** — yok. §2.7'deki değerlendirme
  mimari çıkarımdır, ölçüm değildir.
- **Gerçek saha fotoğrafında model-sürümü bazlı arena IoU / moloza basma** — yok.
  Tüm arena sayıları n=2, YZ üretimi görseller üzerinde.
- **Arena üzerinde model bazında karar doğruluğu** — yok. Mevcut karar doğruluğu
  sayıları (v13 %67,8 · v15 %71,8 · v17 %71,2 · v20 %68,8, n=500) **RescueNet bakır
  testinde** ölçülmüştür, arenada değil.
- **v3, v5a, v5b, v12, v20 için moloza basma oranı** — ölçülmemiş.

---

## 8. Sonraki adımlar

Sıra **zorunludur** — S1 düzeltilmeden üretilen veri araçları zemin sayar; bozuk veriyle
eğitim GPU-gün israfıdır.

```
S1 (kâhin COCO→DOTA)  →  S2 (sınıf-id sözleşmesi)  →  veri üretimi  →  eğitim
                       ↘  S3 (invariant testi)
                       ↘  S4 (karar yollarını birleştir)
```

Görev ayrıntıları ve kapıları: `TASK_QUEUE.md` **FAZ 4**.
