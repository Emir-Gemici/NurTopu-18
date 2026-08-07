# NAVITAS — TEST VE DOĞRULAMA PARAMETRELERİ

> Sözleşmeler: `CONTRACTS.md` · Protokol: `AGENTS.md`
> **Temel kural:** Çalıştırılmayan bir kapı **geçti sayılmaz.**
> Kanıt = komut + **gerçek çıktı** + **çıkış kodu**.

---

## 0. Yorumlayıcı

```
O:\navitas-local-train\venv\Scripts\python.exe
```

⚠ `python` komutu Windows Store saplamasıdır. **Sessizce hiçbir şey yapmaz**, hata bile
vermez. Onunla koşulan test "geçti" görünür ama **hiç koşmamıştır**.

---

## 1. GENEL KAPI — her görevden sonra, istisnasız

```bash
O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
```

| | |
|---|---|
| **Geçme ölçütü** | `SONUC: 15/15 dogru` · çıkış kodu **0** |
| **Düşerse** | Görevi **geri al**, nedenini `REVIEW_LOG.md`'ye yaz |

### 15/15 nedir

`simulation/scripts/arena.py` **tam yer gerçeğini** üretir: 5 harita × 3 senaryo
(kolay/orta/zor) = **15 belirlenimci sahne**. Her sahnede 3 güzergâh poligonu, KB, HB
ve **gizli** `open` cevabı vardır. Yollar ve bariyerler piksel piksel rasterleştirilir.

**Maske KUSURSUZDUR.** Bu yüzden bir sahne düşerse bu bir **MANTIK** hatasıdır,
algı (model) hatası değildir. Model bu kapıya hiç girmez.

Her sahne için doğruluk **beş** koşulun tamamını ister:

```python
cikti["yol_no"] == H["open"]                                    # doğru güzergâh
cikti["durum"] == "ACIK"
len(waypoints) >= 2  and  not cikti["ihlaller"]
en_uzun_adim_px <= olcek_px(MPP)["wp_aralik_px"] + 1.0          # waypoint aralığı
waypoints[0] == baslangic_ankor  and  waypoints[-1] == hedef_ankor
```

Yani yalnız "doğru yolu seçti" yetmez: rota **geçerli**, **ihlalsiz**, **düzgün
aralıklı** ve **doğru uçlara ankorlu** olmalıdır.

**Ölçek:** `MPP = 0.10` m/piksel · `EKSTENT_M = 25.0` (HTAB 50×50 m yarısı) · tuval 500×500 px.

**Determinizm:** Bozulma taraması `zlib.crc32` tabanlı sabit tohum kullanır — Python'ın
hash tuzu süreçler arasında değiştiği için `hash()` kullanılmaz.

---

## 2. Distance Transform genişlik şartı

Bu, güvenliğin **matematiksel çekirdeğidir**.

```python
r_gerekli_px = R_GEREKLI_M / mpp
gecilebilir  = dt_px >= r_gerekli_px
```

```
R_GEREKLI_M = IKA_GENISLIK_M / 2  +  MASKE_HATA_M  +  TAKIP_HATA_M
            =      0.70 / 2       +      0.25      +      0.50
            =                    1.10 m
```

| Terim | Değer | Neden var |
|---|---|---|
| `IKA_GENISLIK_M / 2` | 0,35 m | Aracın yarı genişliği — merkez hattan gövde kenarına |
| `MASKE_HATA_M` | 0,25 m | Segmentasyon sınırının belirsizliği |
| `TAKIP_HATA_M` | 0,50 m | Aracın rotayı takip ederken sapması |

**Bağlayıcı kurallar:**

1. `cv2.distanceTransform` **`DIST_MASK_PRECISE`** ile çağrılır. Yaklaşık maskeler
   (3×3, 5×5) güvenlik payını sessizce eksiltir.
2. Rota doğrulaması **C-space'te** yapılır — `dt_px >= r_gerekli_px` üzerinden.
   **Ham `serbest` maskesiyle doğrulama YASAKTIR.** (Ölçüldü: ham maskeyle doğrulanınca
   15 sentetik rotanın **tamamı** geçersizdi.)
3. `mpp` yoksa `olcek_px(None)` → `m = 1.0` varsayar ve `r_gerekli_px` **1,10 piksele**
   çöker (gerçekte ~27,9 px olmalı). **`mpp=None` olan kare ölçüm dışıdır** —
   ayrı sayaca yazılır, ihlal istatistiğine girmez, ihlal kararı verilmez.

---

## 3. Kapı kayıt defteri

| Kapı | Komut | Geçme ölçütü |
|---|---|---|
| **Genel** | `codes/test_rota_sentetik.py` | **15/15**, exit 0 |
| **Test paketi** | `-B -m unittest discover -s tests` | Tümü OK |
| **Temiz klon** | `git worktree add --detach <tmp> HEAD` sonrası `codes/test_accuracy.py --help` ve `test_batch.py --help` | Her ikisi **exit 0** |
| **Bozulma dayanıklılığı** | `codes/test_rota_sentetik.py --bozulma` | Bariyerin %10'u görülse bile 15/15 |
| **Rota güvenliği** | `codes/test_rota_guvenlik.py --hepsi` | Enjekte kipte ihlal **0**; ham kipte **> 0,10** |
| **Görsel kanıt** | `tests/test_costmap_on_images.py` | Ölçüm yapılmışsa GEÇTİ; sıfır rota varsa **OLCUM_YOK + exit 1** |
| **Anayasa madde 4** | `grep -rnE "^\s*(import\|from)\s+(scipy\|skimage\|sklearn)" --include=*.py .` | **0 eşleşme** |
| **Monotonluk** | `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` | İhlal **0** |
| **Kuyruk ayrıştırma** | Orkestratörü **kopya** dosyada, `input` yamalı koş | Her insan görevi **tam metniyle** yakalanır; 2. geçişte tetiklenmez |

---

## 4. Kapı tasarım kuralları

Bu kurallar **ölçülmüş başarısızlıklardan** türetildi.

### 4.1 Boş kapı yasağı (mutasyon testi)

> Bir test yazdığında kendine sor: **"Düzeltmeyi geri alsam bu test DÜŞER Mİ?"**

Düşmüyorsa test **boştur**. Kanıtlama yöntemi:

1. Geçici `git worktree` aç.
2. O kopyada düzeltmeyi **geri al** (kusuru yeniden üret).
3. Testi koş — **başarısız olmalı**.
4. `git worktree remove --force` ile sil.

*Bu yöntem denetimde 11 görevin tamamına uygulandı; hiçbiri boş çıkmadı.*

### 4.2 Çekimserlik kapısı

Sıfır ölçüm **başarı değildir.** Hiç rota üretilmemişken "ihlal yok" demek vakumdur.

```
enjekte_karar_var == 0  →  durum = OLCUM_YOK  →  çıkış kodu 1
```

*Ölçüldü: bu kapı yokken 0/18 karar üretilmişken `durum=GECTI`, exit 0 üretiliyordu.*

### 4.3 Güçsüz test uyarısı

Ham kipte ihlal oranı **> 0,10** çıkmalıdır. Çıkmıyorsa test **"temiz" değil,
GÜÇSÜZDÜR** — hiçbir şey ölçmüyordur ve bunu ekrana yazmalıdır.

⚠ **Payda uyarısı:** İhlal oranının paydası, rota **üretilen** kareler olmalıdır.
Tüm kareler paydaya girerse rota üretilmeyen kareler "temiz" sayılır ve oran
yapay olarak düşer. *(Ölçüldü: karar başına ihlal 1,00 iken havuz oranı 0,24 raporlandı.)*

### 4.4 Kâhin bağımsızlığı

Puanlamada kullanılan kâhin (araç maskesi) **planlayıcıya verilmez** — verilirse test
döngüsel olur ve hiçbir şey ölçmez.

⚠ **Ölçekten sızıntıya dikkat:** Maske verilmese bile kâhinden **türetilen `mpp`**
planlayıcıya geçerse sızıntı vardır.

### 4.5 Kâhin domain'i

Hava görüntüsü (nadir, ≥30 m) için **DOTA OBB** kullanılır, COCO-seg değil.

*Ölçüldü: aynı fotoğrafta COCO `yolov8m-seg.pt` **2 araç**, DOTA `yolov8m-obb.pt`
**93 araç**. Güven eşiğini 0,35 → 0,02 indirmek çözmedi — sorun eşik değil, domain.*

### 4.6 Kapı var ama açan yok

Bir kilit/kapı eklendiğinde, onu **açacak tarafın da var olduğu** kanıtlanmalıdır.

*Ölçüldü: İHA iniş kapısı eklendi ama üretim zincirinde sinyali **üreten yok** —
varsayılan koşumda kilit hiç açılmıyor, görev hiç başlamıyor.*

### 4.7 İkiz dosya kontrolü

Bir kusur düzeltildiğinde aynı mantığın **kardeş dosyada** da olup olmadığı aranır.

*Ölçüldü: aynı kusur bir dosyada düzeltildi, ikizinde kaldı; **aynı girdide** biri
exit 1, diğeri exit 0 verdi.*

---

## 5. Çözünürlük kilidi

> **Çıkarım `imgsz` = 640. Değiştirmek güvenli DEĞİLDİR.**

| imgsz | arena IoU (v17) | kaplama |
|---|---|---|
| **640** | **0,861** | %4,2 (yer gerçeği %3,6) |
| 960 | 0,034 | **%96,1** |
| 1280 | 0,041 | %79,7 |
| 1600 | 0,018 | %65,2 |

`multi_scale` eğitimi (v20) düzeltmedi (%96,1 → %90,7). FDA irtifası **≥30 m ve
değişken** olduğu için bu gerçek bir saha riskidir.

---

## 6. Model değerlendirme ölçütleri

| Sıra | Ölçüt | Not |
|---|---|---|
| 1 | **Karar doğruluğu** | Yanlış güzergâh = **0 puan** (şartname §5.3.2, §6.2) |
| 2 | **Moloza basma oranı** | Sert kısıt — İKA yapısal bütünlüğü §2.2.6 |
| 3 | ~~mAP~~, ~~blocked AP50~~ | **REDDEDİLDİ** — arena sıralamasını tersine çeviriyor |

**Gürültü tabanı:** maske sd ≈ **0,025–0,032** → **0,04'ten küçük farklar gürültüdür.**
Eşleştirilmiş test (n=40, galibiyet **≥35/40**) olmadan fark iddia edilmez.

**Körlük tuzağı:** Kör bir model %0 moloza basar. **Bu bedava bir sıfırdır, başarı
değildir.** Kaplama oranı yer gerçeğiyle birlikte okunur.

**Havuz metrik tuzağı:** Görüntü bazında raporla. *(v17'nin "0,615"i aslında
0,861 + 0,000'dı.)*

---

## 7. Performans referansı

Ölçülmüş — PC (RTX 5080 Laptop), `navitas_seg_v20_best.pt`:

| imgsz | çıkarım p50 | maske p50 | **costmap p50** | toplam p50 | FPS |
|---|---|---|---|---|---|
| 640 | 26,5 ms | 3,2 ms | **51,2 ms** | 84,5 ms | 11,96 |
| 512 | 21,0 ms | 2,9 ms | **39,3 ms** | 66,2 ms | 15,12 |

**Darboğaz costmap, sinir ağı değil** (~2 katı). Hızlandırma yapılacaksa orada yapılır.

Gerekli hız kapsama hesabından **0,9–2,6 FPS**. 15 FPS **şartname şartı değil**, iç hedef.

⚠ **Jetson'da hiç ölçüm yok.** İki PC koşusu birbiriyle ~100× çelişiyor (ısınma kareleri
şüpheli). Jetson sayısı üretilene kadar hiçbir FPS iddiası yapılmaz.
