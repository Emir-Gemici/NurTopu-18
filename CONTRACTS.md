# NAVITAS — MODÜLLER ARASI SÖZLEŞMELER

> **Bu dosya neden var:** Bu projede ölçülmüş kusurların büyük kısmı algoritma hatası
> değil, **iki modülün aynı sayıya farklı anlam vermesiydi**. Sınıf `2` bir dosyada
> hedef, diğerinde araçtı. Şerit sınırları bir yerde tuvale, diğerinde içeriğe göreydi.
> Bu tür hatalar teste yakalanmaz çünkü her modül **kendi içinde tutarlıdır**.
>
> **Kural: bu dosyadaki hiçbir sabit koda çıplak sayı olarak yazılmaz.**
> Değer değişecekse **önce burası** değişir, sonra kod.

---

## 1. Sınıf id sözleşmesi

### 1.1 Eğitim sınıfları (model çıktısı)

| id | Ad | Anlam |
|---|---|---|
| `0` | `zemin` / `traversable` | Sürülebilir zemin. **Otorite katmanı.** |
| `1` | `engel` / `blocked` | Geçilemez engel (moloz, bariyer, enkaz) |
| `2` | `hedef` | **2 m × 2 m kırmızı H brandası** (şartname §2.1) |

Bu şema `dataset/*/data.yaml` ve `scripts/copy_paste_augmentation.py` çıktısının
sözleşmesidir. Üretimdeki 2 sınıflı modeller `{0, 1}` alt kümesini kullanır.

### 1.2 ⛔ ÇAKIŞMA — çözülene kadar geçerli uyarı

`simulation/scripts/iha_haritala.py` **çalışma anında** ayrı bir katman sözlüğü kuruyor:

```python
costmap_maskeleri = {0: masks[0], 1: masks[1], 2: arac}   # :300  -> 2 = ARAÇ
rota_bul(..., engel_sinif_idler=(1, 2), ...)              # :336
```

Yani **`2` orada araç**, eğitim şemasında **hedef**. 3 sınıflı bir model bu yola
verilirse **H brandası engel sayılır** → İKA hedefe hiç ulaşamaz → `P_görev = 0`.

**Doğru ayrım:**

| Kavram | Ad alanı | Kim üretir |
|---|---|---|
| **Eğitim sınıfı** | `0=zemin, 1=engel, 2=hedef` | model / etiket |
| **Costmap katmanı** | ayrı sözlük, model sınıfı **değil** | çalışma anı (araç dedektörü vb.) |

Araç maskesi bir **çalışma anı katmanıdır**, eğitim sınıfı değildir. İkisi aynı sayı
uzayını paylaşmamalıdır. Düzeltme görevi: `TASK_QUEUE.md` **S2**.

### 1.3 Costmap rolleri

```python
yol_sinif_idler   = (0,)        # serbest alanı OLUŞTURAN katmanlar
engel_sinif_idler = (1,)        # serbest alandan ÇIKARILAN katmanlar
```

`codes/costmap_path_finder.py:165, 730` varsayılanları. Sözlükte olmayan id **sessizce
atlanır** — bu yüzden yanlış id vermek hata üretmez, **sessizce güvenliği düşürür**.

---

## 2. Katman monotonluk sözleşmesi

```
serbest = zemin  AND NOT  engel          ← ÇIKARMA EN SON
serbest(K1 ∧ ¬K2)  ⊆  serbest(K1)        ← DEĞİŞMEZ KURAL
```

**Çıkarmadan sonra serbest alanı BÜYÜTEN hiçbir işlem eklenmez:**
`cv2.dilate` · `MORPH_CLOSE` · `MORPH_DILATE` · `bitwise_or` · `np.maximum` — hepsi yasak.
(Bağlı bileşen alan filtresi **silme** işlemidir; sorun değil.)

Bu sayede Katman 2'ye yeni bir dedektör eklemek **monotonik olarak güvenlidir** —
sistemi ancak daha güvenli yapabilir. Uygulama: `codes/costmap_path_finder.py:212-213`.

---

## 3. Koordinat çerçevesi sözleşmesi

Bu projede **üç ayrı çerçeve** var ve karıştırıldığında sessizce yanlış güzergâh üretilir.

| Çerçeve | Tanım | Nereden gelir |
|---|---|---|
| **Kaynak** | Ham kameranın kendi piksel uzayı (ör. 1600×900) | `cv2.imread` / kamera |
| **Tuval** | Letterbox sonrası **kare** uzay (`max(h,w)²`), kenarlar gri `114` dolgu | `_preprocess` |
| **İçerik** | Tuvalin içindeki gerçek görüntü dikdörtgeni `(x0, y0, w, h)` | `_preprocess` 3. dönüş değeri |

### 3.1 Kural

> **Her oran, eşik ve bölge hesabı İÇERİK dikdörtgenine göre yapılır — tuvale göre asla.**

Ölçülmüş ihlaller (düzeltildi, tekrarlanmasın diye burada):

| Hata | Sonuç |
|---|---|
| Şerit sınırları tuval genişliğine bölünüyordu | 576×1024 portrede net **SAĞ** koridor için **ORTA** dönüyordu → şartname: **0 puan** |
| `min_area_ratio` tuval alanına göreydi | 16:9'da eşik %1 yerine fiilen **%1,78** |
| Tohum bandı tuvalin alt/üst %8'iydi | 16:9'da bantlar tamamen **gri dolguda** kalıyordu → 18/18 karede rota yok |

### 3.2 Yerel ↔ dünya

`OPEN_ROUTE` mesajında waypoint'ler `ref_xy`'ye **göreli metre** cinsindendir.
İKA kendi çerçevesine saf **öteleme** ile oturtur (`ika_nav.py:206`). Dönme yoktur.

---

## 4. Geometri sabitleri

`codes/costmap_path_finder.py` — **tek kaynak**.

| Sabit | Değer | Anlam |
|---|---|---|
| `IKA_GENISLIK_M` | `0.70` | İKA gövde genişliği |
| `MASKE_HATA_M` | `0.25` | Segmentasyon sınır belirsizliği |
| `TAKIP_HATA_M` | `0.50` | Sürüş takip hatası |
| **`R_GEREKLI_M`** | **`1.10`** | `0.70/2 + 0.25 + 0.50` — **geçilebilirlik yarıçapı** |
| `ALGI_PAYI_M` | `0.25` | Engel genişletme payı |
| `AC_M` / `KAPAT_M` | `0.30` / `0.40` | Zemin morfolojisi |
| `LAMBDA_ACIKLIK` | `3.0` | A* açıklık ceza katsayısı |
| `US_ACIKLIK` | `2.0` | A* açıklık ceza üssü |
| `WP_ARALIK_M` | `2.0` | Waypoint aralığı |
| `MAKS_WP` | `64` | Azami waypoint sayısı |

**Geçilebilirlik testi:**
```python
gecilebilir = dt_px >= r_gerekli_px          # r_gerekli_px = R_GEREKLI_M / mpp
```
Rota doğrulaması **C-space'te** yapılır (`dt_px` üzerinden), **ham maskede asla**.

**Medial-axis yerine açıklık ağırlıklı A\*:** `scipy.ndimage` ve `cv2.ximgproc` yasak/yok
olduğu için koridor merkezinden geçme davranışı `maliyet = 1.0 + λ·u^p` ile elde edilir.
Bilinçli ikamedir, eksiklik değil.

---

## 5. Ölçek (`mpp`) sözleşmesi

`mpp` = metre / piksel. **Kritik:** `olcek_px(None)` → `m = 1.0` varsayar ve
`r_gerekli_px` **1,10 piksele** çöker. Gerçek değer ~27,9 px olmalıyken.

> **`mpp=None` olan kare ölçüm dışıdır.** Ayrı sayaca yazılır, ihlal istatistiğine girmez.
> Ölçeksiz kipte ihlal kararı **verilmez**.

Bilinen kaynaklar: `iha_haritala.py` → `MOZ_M / MOZ_PX = 56.0 / 1024 ≈ 0.0547`

---

## 6. Mesaj protokolü sözleşmesi

`comms/protocol.py` — newline ile çerçevelenmiş JSON, taşıyıcıdan bağımsız
(UDP sim / SiK Radio 433 MHz saha).

| Tip | Üretici | Alan | Anlam |
|---|---|---|---|
| `OPEN_ROUTE` | İHA | `road` (1=sol, 2=orta, 3=sağ), `conf`, `ref_xy`, `waypoints` | Doğrulanmış açık güzergâh |
| `NO_ROUTE` | İHA | `sebep`, `detay` | Rota üretilemedi — **sessizlikten farklıdır** |
| `HEARTBEAT` | herkes | `node` | Bağlantı canlılığı |
| `ACK` | YKS / İKA | `ref` (seq) | Alındı onayı |
| `CMD` | YKS | `cmd`, `hedef` | Operatör komutu (`IKA_GO`, `ARM`, …) |

### 6.1 Alıcı davranışı — bağlayıcı

- **Bilinmeyen tip sessizce yok sayılır.** Geriye uyumluluk bunun üzerine kuruludur.
- `NO_ROUTE`, `latest` içindeki **son geçerli rotayı EZMEZ**; ayrı alana yazılır.
- `NO_ROUTE` **geçici** bir durumdur, kalıcı başarısızlık değildir. İHA kare kare tarar;
  bir karede rota bulunamaması görevi iptal etmez. Alıcı **dinlemeye devam eder**.
- Sürüş sırasında `NO_ROUTE` gelirse araç **güvenli duruşa** geçer; yeni geçerli
  `OPEN_ROUTE` gelince devam eder.

### 6.2 `road` sözleşmesi

`{1: "sol", 2: "orta", 3: "sag"}` — `open_route()` bu aralık dışında `ValueError` fırlatır.
Rota yoksa `NO_ROUTE` gönderilir; `open_route`'a `None` geçilmez.

---

## 7. Görev kapısı sözleşmesi (şartname §2.2.5)

İKA'nın hareket edebilmesi **iki** koşula birden bağlıdır:

```
sür  ⟺  (geçerli OPEN_ROUTE)  ∧  (İHA inişi tamamlandı)  ∧  (YKS'den IKA_GO geldi)
```

- *"İHA yere temas etmeden İKA hareket edemez. İHA iniş yapmadan harekete geçen
  takımların görevi başarısız sayılacaktır."*
- *"İKA'nın intikal süreci yer kontrol istasyonunda görevli takım üyesi tarafından
  manuel olarak tetiklenir."*

⚠ **Denetimde bulundu:** Kapı kurulu ama **üretim zincirinde iniş sinyalini üreten
yok** — varsayılan koşumda kilit hiç açılmıyor. Ayrıca `IKA_GO` tek atışlık ve ACK'siz;
tek paket kaybı görevi geri dönülmez bitiriyor. Kayıt: `REVIEW_LOG.md`.

---

## 8. Çözünürlük sözleşmesi

> **Çıkarım `imgsz` = 640. Değiştirmek güvenli DEĞİLDİR.**

Ölçüldü (v17, arena `1.jpg`):

| imgsz | IoU | kaplama |
|---|---|---|
| **640** | **0,861** | %4,2 (yer gerçeği %3,6) |
| 960 | 0,034 | **%96,1** — her yeri boyuyor |
| 1280 | 0,041 | %79,7 |
| 1600 | 0,018 | %65,2 |

`multi_scale` eğitimi (v20) bunu **düzeltmedi** (%96,1 → %90,7). FDA irtifası ≥30 m ve
**değişken** olduğu için bu gerçek bir saha riskidir.

---

## 9. Orkestratör sözleşmesi (`auto_orchestrator.py`)

Ayrıştırıcı `TASK_QUEUE.md`'yi **satır satır** okur. Sözleşme kodun kendisinden türetildi:

| Kural | Sebep |
|---|---|
| İnsan görevi **tek satırda** olmalı | Ayrıştırıcı satır bazlı |
| Etiket metni **`]` içeremez** | `line.find("]", start)` ilk `]`'de keser |
| Etiket `TASK_QUEUE.md`'de **yalnız gerçek görev satırlarında** geçebilir | Düz yazıdaki örnek **hayalet görev** üretir ve operatörü bloke eder |
| Etiket metni **saf ASCII** tutulmalı | Orkestratör Türkçe Windows'ta (cp1254) çıktı yönlendirilince zaten kırılgan |

⚠ Bilinen kusur: `auto_orchestrator.py` emoji basıyor; çıktı boruya yönlendirilince
`UnicodeEncodeError` ile **çöküyor** (dönüş kodu 1). Çözüm kalıbı
`simulation/scripts/navitas_sim.py:22-26`'da hazır.

---

## 10. Ölçüt hiyerarşisi (model seçimi)

| Sıra | Ölçüt | Not |
|---|---|---|
| 1 | **Karar doğruluğu** — hangi güzergâh açık | Yanlış güzergâh = **0 puan** |
| 2 | **Moloza basma oranı** — sert kısıt | İKA yapısal bütünlüğü §2.2.6 |
| 3 | ~~Genel mAP~~, ~~blocked AP50~~ — **REDDEDİLDİ** | mAP arena sıralamasını **tersine çeviriyor** |
| 4 | Gürültü tabanı: maske sd ≈ **0,025–0,032** | **0,04'ten küçük farklar gürültüdür** |

Eşleştirilmiş test olmadan (n=40, galibiyet ≥35/40) fark iddia edilmez.
Kör bir model %0 moloza basar — **bu bedava bir sıfırdır, başarı değildir.**
