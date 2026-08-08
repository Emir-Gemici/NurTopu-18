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

---

## 11. Saha zinciri sözleşmesi

> **Neden var:** `REVIEW_LOG.md` D-22 — saha kod yolunu uçtan uca sınayan tek bir
> test yok; dört ayrı kopukluk aynı anda görünmüyor. `TASK_QUEUE.md` T21.
>
> **Saha** = Jetson/Pi + kamera + SiK 433 MHz telsiz. **Gazebo YOK, ROS YOK, `gz` YOK.**

### 11.1 Sahiplik kuralı — bağlayıcı

Bir halkanın **sahibi**, o halkayı sahada gerçekten koşturan dosyadır.

1. `simulation/` altındaki hiçbir dosya sahip **yazılamaz**. Gerekçe: `navitas_sim.py`
   `gz` ikilisinin, `meta.txt`'in ve kendi ürettiği `IHA_LANDED`'in varlığını
   varsayar; sahada üçü de yoktur. Simülasyon çıktısı bu sözleşmede **kanıt sayılmaz**.
2. Sahibi yoksa halka **`SAHİPSİZ`** işaretlenir. Boş bırakılamaz.
3. Sahibi var ama sahada yanlış davranıyorsa **`KUSURLU`** + kusur kaydı numarası.
4. `jetson_paket/` altındaki bir dosya sahip olabilir — saha paketi odur. Ancak
   paket **eksikse** (bkz. §11.3 Halka 7) halka `SAHİPSİZ`'dir.

### 11.2 Halka tablosu

| # | Halka | Girdi | Çıktı | Sahip `dosya:satır` | Durum |
|---|---|---|---|---|---|
| 1 | Kamera kaynağı | cihaz/URL | BGR kare | `codes/rpi_inference.py:505` — `cv2.VideoCapture(0)` **sabit** | **KUSURLU** · D-13 |
| 2 | Model yükleme | model yolu | YOLO nesnesi | `codes/rpi_inference.py:32-40,52-57` → `best_ncnn_model` | **KUSURLU** · D-13 |
| 3 | Çıkarım | BGR kare | `results` | `codes/rpi_inference.py:57` (`YOLO.predict`) | **GEÇERLİ** |
| 4 | Maske çıkarımı | `results` | `{0: zemin, 1: engel}` | `codes/rpi_inference.py:60-83` (`get_masks`) | **GEÇERLİ** |
| 5 | Ölçek (`mpp`) | irtifa + FOV | m/piksel | — | **SAHİPSİZ** · D-22 |
| 6 | Hedef konumu (HB) | kare / dış girdi | `hb_xy` | — (yalnız Gazebo `meta.txt`) | **SAHİPSİZ** · D-22, D-23 |
| 7 | Rota üretimi | maskeler + `mpp` + `hb_xy` | `road`, `waypoints`, `durum` | `codes/costmap_path_finder.py:729` (`rota_bul`) | **KUSURLU** · D-25 |
| 8 | Aktarım | rota | OPEN_ROUTE/NO_ROUTE + ACK | — (`jetson_paket/kod/` içinde yok) | **SAHİPSİZ** · D-22 |
| 9 | İKA sürüş izni | rota ∧ IKA_GO ∧ IHA_LANDED | izin `bool` | kapı: `comms/ika_receiver.py:119-121` · `IHA_LANDED` üreticisi: **yalnız `simulation/scripts/navitas_sim.py:95`** | **KUSURLU** · D-22 |
| 10 | Motor komutu | izin + waypoint | tekerlek hızı | — (`gz` subprocess'i sahip değil) | **SAHİPSİZ** · D-22 |

### 11.3 Halka başına başarı ölçütü ve kanıt

**Halka 1 — Kamera kaynağı.** Ölçüt: kaynak **parametrik** olacak (indeks / `/dev/videoN` /
`http://…:4747/video`) ve ilk kare `None` dönmeden okunacak.
Kanıt: `codes/rpi_inference.py:505` → `cap = cv2.VideoCapture(0)`; argparse'ta (`:551-559`)
kaynak argümanı **yok**. Çalışan referans kalıp `jetson_paket/kod/kamera_dogrula.py:57`'de
var (`--kaynak`) ama o bir doğrulama aracıdır, **üretim yolu değildir**.

**Halka 2 — Model yükleme.** Ölçüt: yüklenen ağırlık `config/model_registry.json`'daki
etkin profille **eşleşecek** ve SHA doğrulanacak.
Kanıt: `codes/rpi_inference.py:32-40` `MODEL_DIR`'i `best_ncnn_model`'e çözüyor —
11 Temmuz tarihli **v2 dönemi NCNN**. `--model` argümanı yok, `INFER_SIZE = 512`
sabit (`:44`). Üretimde olması gereken v21'dir. Ayrıca `config/model_registry.json`
"competition" profili `navitas_seg_v4_best.pt` gösteriyor — **kayıt defteri de bayat**.

**Halka 3 — Çıkarım.** Ölçüt: tek kare çıkarımı istisnasız tamamlanacak. Geçerli.

**Halka 4 — Maske çıkarımı.** Ölçüt: `{0, 1}` anahtarlı, kare boyutuna ölçeklenmiş
ikili maske. `get_masks` `sinif_idler` ile genişletilebilir. Geçerli.

**Halka 5 — Ölçek.** Ölçüt: `mpp` **irtifa + kamera FOV'undan türetilecek**; türetilemiyorsa
halka `ÖLÇEK_YOK` döndürecek ve **rota üretilmeyecek**.
Kanıt: sahada `mpp` üreten hiçbir kod yok. Simülasyonda `simulation/scripts/iha_haritala.py:66`
`MPP = MOZ_M / MOZ_PX` sabiti var — §11.1/1 gereği sahip sayılmaz.
`codes/costmap_path_finder.py:107` `m = 1.0 if mpp is None else float(mpp)` ile
**sessizce 1 m/piksel** varsayıyor; `r_gerekli_px` 20,11 yerine 1,10 oluyor ve
**hiçbir uyarı basılmıyor**. Bu, §5'in (Ölçek sözleşmesi) ihlalidir.

**Halka 6 — Hedef konumu (HB).** Ölçüt: hedef bölgesinin konumu **saha kaynağından**
gelecek — ya algıdan (kırmızı H tespiti) ya da açık bir dış girdiden (`--hb`).
Kanıt: `simulation/scripts/iha_haritala.py:507` → `hb_xy=_meta_xy(meta, "HB_XY")`.
`HB_XY`'yi yazan tek yer `simulation/scripts/world_generator.py:590`, yani **Gazebo
dünya üreteci**. argparse'ta (`:471-488`) `--hb` / `--kb` **yok**. Sahada `meta.txt`
olmadığı için `hb_xy=None` → `:296-306`:

    "rota_durum": "HEDEF_YOK",
    "rota_sebep": "HB koordinati bulunamadi; dinamik rota yayinlanmadi."

Yani sahada **her karede NO_ROUTE**. Kalıcı çözüm algı katmanındadır: üretim modeli
2 sınıflı (`{0: traversable, 1: blocked}`), 2×2 m kırmızı H'yi gören **hiçbir bileşen
yok** (D-23). §1.1 üçüncü sınıfı tanımlıyor ama üretim onu hiç üretmiyor.

**Halka 7 — Rota üretimi.** Ölçüt: letterbox'lı girdide de içerik kutusuna göre karar.
Kanıt: `grep -n "icerik" codes/costmap_path_finder.py` → **0 satır**. `_tohum_maske`
(`:232-242`) bandı tam maske yüksekliğinden hesaplıyor; pad'lenmiş karede tohum
tamamen gri dolguya düşüyor → `durum=KAPALI_DAR`. Aynı sahne kırpıkken `durum=ACIK`.

**Halka 8 — Aktarım.** Ölçüt: saha paketinden OPEN_ROUTE/NO_ROUTE gönderilebilecek
ve ACK alınabilecek; seri (SiK) yolu da çalışacak.

    ls jetson_paket/kod/
    costmap_path_finder.py  jetson_fps.py  kamera_dogrula.py
    karisim_arena.yaml  requirements_rpi.txt  rpi_inference.py
    -> protocol.py / iha_sender.py / link.py YOK

    jetson_paket/kod/requirements_rpi.txt: ultralytics, opencv-python, numpy
    -> pyserial YOK

`simulation/scripts/iha_detect_send.py` `--serial` destekliyor ama §11.1/1 gereği
sahip değildir; ayrıca `:30-34` `detect_open_road` hâlâ arena **yer gerçeği** okuyor
ve `--ika/--serial` yolu `--rota-json` zorunlu kılıyor — o dosyayı `iha_haritala`
(simülasyon) üretiyor.

**Halka 9 — İKA sürüş izni.** Ölçüt: üç koşul da **saha kaynağından** gelecek.
Kanıt: kapı doğru yazılmış — `comms/ika_receiver.py:119-121`
`if not self.ika_go or not self.iha_landed: return False`. Ama girdilerinden biri
sahipsiz: `send_iha_landed` çağrısı tüm depoda tek yerde, `simulation/scripts/navitas_sim.py:95`.
Yani **kapının kendisi sağlam, beslemesi kopuk**.

**Halka 10 — Motor komutu.** Ölçüt: gerçek sürücüye (seri/GPIO/PWM/MAVLink) komut
gidecek; `gz` yalnızca bir arka uç olacak.
Kanıt: `simulation/scripts/ika_nav.py:90-99` `subprocess.run(["gz","topic",…],
capture_output=True, timeout=1)`. Arenada `gz` yoktur → `FileNotFoundError` →
`capture_output=True` sayesinde **hata yutulur, uyarı basılmaz**.
`grep -E 'Serial|GPIO|pwm|arduino|pixhawk|mavlink|CAN'` → `ika_nav.py` içinde **0 eşleşme**.

### 11.4 Sözleşmenin doğrulanması

Bu tablo elle güncellenmez. `TASK_QUEUE.md` T22'nin ürettiği
`results/saha_kuru_kosu_<tarih>/ozet.json` tabloyla **birebir aynı halka adlarını**
kullanır; sapma varsa sözleşme değil koşucu düzeltilir (halka adı sözleşmede tanımlıdır).

Halka adları (koşucunun kullanacağı anahtarlar, değişmez):

    kamera · model_yukleme · cikarim · maske · olcek · hedef_konumu
    rota · aktarim · surus_izni · motor

**Bugünkü beklenen durum** (T22'nin üretmesi gereken tablo):

| Halka | Beklenen | Gerekçe |
|---|---|---|
| `kamera` | KUSURLU | kaynak sabit `VideoCapture(0)` |
| `model_yukleme` | KUSURLU | v21 yerine v2 dönemi NCNN |
| `cikarim` | GECTI | — |
| `maske` | GECTI | — |
| `olcek` | **SAHİPSİZ** | saha `mpp` üreticisi yok |
| `hedef_konumu` | **SAHİPSİZ** | yalnız Gazebo `meta.txt` |
| `rota` | KUSURLU | letterbox tohum bandı |
| `aktarim` | **SAHİPSİZ** | saha paketinde comms yok |
| `surus_izni` | KUSURLU | `IHA_LANDED` beslemesi kopuk |
| `motor` | **SAHİPSİZ** | gerçek sürücü yok |

Dört `SAHİPSİZ` halka D-22'nin dört kopukluğudur. **T22 bu tabloyu tek koşuda
üretmelidir**; ilk düşüşte çıkan bir koşucu bu görevi karşılamaz.
