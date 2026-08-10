# NAVITAS — KULLANILAN VERİ SETLERİ VE SINIF EŞLEMELERİ

> **Bu dosya neden var:** *"Zemin sınıfını hangi veriden öğrendik?"* sorusunun tek
> yetkili cevabı. Bilgiler depodaki indirici/dönüştürücü betiklerden ve `data.yaml`
> dosyalarından **doğrulanarak** çıkarıldı; her satırın yanında kaynak dosya var.
> Doğrulanamayan şeyler **açıkça öyle işaretlendi** — tahmin yazılmadı.
>
> Son güncelleme: 2026-08-06

---

## 1. Özet — kısa cevap

**Zemin (`traversable`) sınıfı esas olarak RescueNet'ten gelir.** RescueNet'in
`road-clear` sınıfı bizim `0 = traversable` sınıfımıza eşlenir. FloodNet ikinci
kaynak olarak **yalnız v2 döneminde** kullanılmıştır. Güncel üretim modeli **v21**
RescueNet + kendi ürettiğimiz iki sentetik/melez küme ile eğitilmiştir.

| # | Veri seti | Rol | Güncel v21'de? |
|---|---|---|---|
| 1 | **RescueNet** (roads alt kümesi) | Ana gerçek afet verisi; **zemin sınıfının kaynağı** | ✅ evet |
| 2 | **FloodNet** (Track 1, segmentasyon) | İkinci gerçek kaynak, v2 döneminde | ❌ hayır |
| 3 | **Sentetik arena** (kendi ürettiğimiz) | Yarışma arenası benzetimi | ✅ evet |
| 4 | **copy_paste_gercek** (kendi ürettiğimiz) | Gerçek drone karesi + sentetik moloz | ✅ evet |
| 5 | Semantic Drone Dataset | İndirici yazıldı, **kullanılmadı** | ❌ |
| 6 | Dubai Aerial Segmentation | İndirici yazıldı, **kullanılmadı** | ❌ |

⚠ 5 ve 6 için `dataset/download_*.py` betikleri var ama **veri dizinleri diskte yok**
ve hiçbir `data.yaml` bunlara referans vermiyor — yani indirilmiş ama eğitime
girmemiş ya da hiç indirilmemiştir.

---

## 2. Kaynaklar ve erişim

| Veri seti | Kaynak | Depodaki betik |
|---|---|---|
| **RescueNet (roads)** | HuggingFace: `asolodin/rescuenet-roads` | `dataset/download_and_convert.py:4` |
| **FloodNet** | `github.com/BinaLab/FloodNet-Supervised_v1.0` (Track 1) | `dataset/download_floodnet.py`, `dataset/convert_floodnet.py` |
| Semantic Drone | `kaggle.com/datasets/bulentsiyah/semantic-drone-dataset` | `dataset/download_semantic_drone.py:5` |
| Dubai Aerial | HuggingFace: `gymprathap/Semantic-Segmentation-Aerial-Imagery-Dataset` | `dataset/download_extra_datasets.py:78` |

⚠ **LİSANS/ATIF DOĞRULANMADI.** Depoda bu veri setlerinin lisans metni veya
akademik atıfı **kayıtlı değildir**. Yarışma raporunda kullanılacaksa her kaynağın
kendi sayfasındaki lisans ve atıf koşulu **kontrol edilmelidir** — bu belge o
kontrolün yerine geçmez.

---

## 3. Sınıf eşlemeleri — zemin nereden geliyor

### 3.1 RescueNet → NAVITAS (ana yol)

`dataset/download_and_convert.py:72` — ham RescueNet sınıf kimlikleri:

```
RescueNet class IDs: 7 = road-clear, 8 = road-blocked, 0 = background
        ↓
    7  →  0 : traversable   ← ZEMİN SINIFIMIZ BURADAN
    8  →  1 : blocked
```

Yani **NAVITAS'ın "zemin" tanımı RescueNet'in "engelsiz yol" (road-clear)
tanımıdır** — genel bir "yürünebilir alan" değil, **yol yüzeyi**.

### 3.2 FloodNet → NAVITAS (v2 dönemi)

```
dataset/download_floodnet.py:18   5 (road-non-flooded) → 0 : traversable
dataset/convert_floodnet.py:17    4 (road-nonflooded)  → 0 : traversable
```

🔴 **TUTARSIZLIK — çözülmedi.** İki dönüştürücü FloodNet'in yol sınıfı için
**farklı indeks** kullanıyor (`5` ve `4`). Hangisinin v2 eğitiminde koştuğu
belirsizdir; dataset manifesti veya hash tutulmamıştır. Biri yanlışsa v2 eğitimine
yanlış sınıf girmiş olabilir. **v21 FloodNet kullanmadığı için güncel modeli
etkilemez**, ama FloodNet yeniden devreye alınırsa **önce bu çözülmelidir.**

### 3.3 Üretim sınıf sözleşmesi

`CONTRACTS.md` §1.1 (bağlayıcı):

| id | ad | anlam |
|---|---|---|
| `0` | `traversable` / `zemin` | Sürülebilir zemin — **otorite katmanı** |
| `1` | `blocked` / `engel` | Geçilemez engel (moloz, bariyer, enkaz) |
| `2` | `hedef` | 2 m × 2 m kırmızı H brandası |

---

## 4. Türetilmiş kümeler (bizim ürettiklerimiz)

| Küme | Nasıl üretildi | `data.yaml` |
|---|---|---|
| `rescuenet_yolo` | RescueNet → YOLOv8-seg, 2 sınıf | `dataset/rescuenet_yolo/data.yaml` |
| `rescuenet_11sinif` | RescueNet 10 sınıf — **yardımcı görev ön eğitimi**; sınıf 0/1 indeksi korunur | `dataset/rescuenet_11sinif/data.yaml` |
| `rescuenet_1024`, `rescuenet_kirpik`, `rescuenet_yolo_256` | Çözünürlük/kırpma türevleri | ilgili `data.yaml` |
| `sentetik_arena` | `51_sentetik_arena.py` ile üretilen yarışma arenası benzetimi | `dataset/sentetik_arena/data.yaml` |
| **`copy_paste_gercek`** | **Gerçek drone karesi** (90° nadir, ~1024×576) üzerine etiketi bilinen moloz yapıştırılır. Görüntü gerçek, **yalnız moloz sentetiktir.** | `dataset/copy_paste_gercek/data.yaml` |

`copy_paste_gercek`'in gerekçesi `dataset/karisim_arena_gercek.yaml` başlığında
ölçümüyle yazılıdır: yalnız sentetik arena ile fine-tune edilen v17/v20 gerçek
drone karelerinde **körleşti** (67 karede kullanılabilir kare: v15 → 23, v17 → 10,
v20 → 10; arenayı hiç görmeyen v5c → 58). Model gerçek asfalt/gölge/araç dokusunu
görsün diye üçüncü kaynak eklendi.

---

## 5. Hangi model hangi veriyle eğitildi

| Model | Veri | Not |
|---|---|---|
| v2 | RescueNet + **FloodNet** | Colab, 100 epoch (`594e1b0`) |
| v3 | RescueNet + `blocked` oversampling | `blocked` örnekleri ~3,5× az olduğu için (`oversample_blocked.py:4`) |
| v5c | RescueNet (yolov8m) | **Arenayı hiç görmedi** — gerçek karelerde en iyi taban |
| v15 | RescueNet 11 sınıf ön-eğitim → 2 sınıfa fine-tune | Yardımcı görev yaklaşımı |
| v17, v20 | `karisim_arena.yaml` (RescueNet + sentetik arena) | Gerçek karelerde körleşti |
| **v21 (üretim)** | **`karisim_arena_gercek.yaml`** = RescueNet + sentetik arena + `copy_paste_gercek` | Güncel üretim modeli |

---

## 6. Bilinen sınırlar (dürüstlük notu)

1. **Ham veri depoda yok.** `.gitignore` büyük kümeleri dışlar (`rescuenet_ham` tek
   başına ~45 GB). GitHub deposunda `dataset/` altında yalnız yapılandırma dosyaları
   bulunur — **veri setlerinin kendisi GitHub'da değildir**, betiklerle yeniden
   indirilir/üretilir.
2. **Dataset manifesti/hash tutulmuyor.** Bir modelin tam olarak hangi dosya kümesiyle
   eğitildiği geriye dönük olarak **kanıtlanamaz**. FloodNet indeks tutarsızlığı
   (§3.2) bu boşluğun doğrudan sonucudur.
3. **`combined_data.yaml` yolu bayat:** `path:` alanı `/home/trs/trs/github/navitas/dataset`
   gösteriyor — eski Linux kurulumundan kalma, bu makinede çalışmaz.
4. **`blocked` sınıfı zayıf:** RescueNet'te `blocked` örnekleri `traversable`'a göre
   ~3,5× az; v1 raporunda `blocked` mAP50 = 0,363. Kapalı yolu yanlışlıkla
   `traversable` görmek araç güvenliği açısından kritiktir — bu yüzden mimari
   **serbest alanı otorite** sayar ve nesne katmanı yalnız **çıkarır**
   (`CLAUDE.md` madde 15).
