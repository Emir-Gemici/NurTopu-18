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

### 1.2 ✅ ÇAKIŞMA ÇÖZÜLDÜ — iki ad alanı ayrıldı (S2)

> *Bu bölüm 2026-08-10'a kadar "⛔ çözülene kadar geçerli uyarı" olarak duruyordu ve
> **çözülmüş** bir çakışmayı yürürlükteki kod gibi gösteriyordu. Madde 16 sözleşmeyi
> bu dosyadan okumayı emrettiği için bu, çakışmayı geri getirebilecek **aktif bir
> tuzaktı.** Kayıt: `REVIEW_LOG.md` D-35.*

**Eski kusur (ölçülmüş, KRİTİK).** `iha_haritala.py` çalışma anında
`{0: zemin, 1: moloz, 2: araç}` kuruyor ve `engel_sinif_idler=(1, 2)` veriyordu.
Eğitim şemasında `2 = hedef` olduğu için 3 sınıflı bir model bu yola verilseydi
**H brandası engel sayılacaktı** → İKA hedefe hiç ulaşamaz → `P_görev = 0`.

**Çözüm — tek otorite `codes/sinif_semasi.py`.** İki ad alanı ayrıldı, sayıları
artık çakışmıyor:

| Ad alanı | Sabitler | Kim üretir |
|---|---|---|
| **Eğitim sınıfı** | `ZEMIN=0` · `ENGEL=1` · `HEDEF=2` | model çıktısı / YOLO etiketi |
| **Costmap katmanı** | `KATMAN_ZEMIN=0` · `KATMAN_MOLOZ=1` · **`KATMAN_ARAC=10`** | çalışma anı; araç maskesi **ayrı** bir DOTA OBB modelinden gelir |

Araç katmanı **10**'dan başlar: eğitim sınıf uzayıyla (0..9) çarpışmasın diye seçildi.
Böylece 3 sınıflı bir model bu yola verilse bile `HEDEF (2)` hiçbir zaman bir costmap
engel katmanına denk gelmez.

`serbest_alan()` sözlük **anahtarlarını** kullanır (`if c in maskeler`); id'nin sayısal
değeri önemli değildir — yalnızca **çakışmaması** önemlidir.

**Doğrulama:** `codes/test_sinif_semasi.py` → **8 GEÇTİ / 0 DÜŞTÜ**, pozitif kontrol
dahil (*"eski şemada hedef ENGEL sayılıyordu"* testi kusuru yeniden üretiyor).
`sinif_semasi` **import anında** `dogrula()` koşar: sabitler çakışırsa modül yüklenmez.

### 1.3 Costmap rolleri — sabitler `sinif_semasi`'den okunur

```python
from sinif_semasi import COSTMAP_YOL_KATMANLARI, COSTMAP_ENGEL_KATMANLARI

yol_sinif_idler   = COSTMAP_YOL_KATMANLARI     # (KATMAN_ZEMIN,)              = (0,)
engel_sinif_idler = COSTMAP_ENGEL_KATMANLARI   # (KATMAN_MOLOZ, KATMAN_ARAC)  = (1, 10)
```

Yürürlükteki kullanım: `simulation/scripts/iha_haritala.py:60` (import), `:327` (çağrı).

⛔ **Çağrı yerlerine çıplak sayı yazılmaz** (madde 16). Yeni bir engel kaynağı
eklenecekse **yalnız** `COSTMAP_ENGEL_KATMANLARI` genişletilir — çağrı yerleri
değişmez.

Sözlükte olmayan id **sessizce atlanır**: yanlış id vermek hata üretmez,
**sessizce güvenliği düşürür.** Sabitten okumanın nedeni tam olarak budur.

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

### 2.1 Katman 2 dedektörü — ince bariyer (T67 · `REVIEW_LOG.md` D-92, D-93, D-99)

> **Neden var.** Şartname figüründe ölçüldü, **model kullanılmadan**: bariyerin
> 3644 pikselinin **%0,0**'ını model engel sayıyor, **%30,9**'unu zemin sayıyor;
> üretilen rota bariyeri **59 px** kesiyordu. Korumaların **hiçbiri**
> ateşlemiyordu (zemin kapısı susuyor, ret yok, güven 0,75). Rotayı yayından
> alıkoyan tek şey `OLCEK_YOK` idi — bir kapı değil, bir **eksiklik**.
>
> 🔴 **D-99 DÜZELTMESİ — ölçüm zemini gerçek arena DEĞİLDİR.** Şartname Şekil 1
> alt yazısı: *"Görsel tamamen yapay zeka ile oluşturulmuştur. Gerçek alanı
> doğrudan yansıtmamaktadır."* Dolayısıyla **bariyerin kırmızı-beyaz görünümü
> uydurmadır** ve bu dedektörün renk anahtarı (`a* > 25`) yapay bir görüntüden
> kalibre edilmiştir. Gerçek arenada fiziki engeller kırmızı **olmayabilir** —
> o durumda dedektör **hiç ateşlemez** (fail-safe: hiçbir şey eklemez, hiçbir
> şey çıkarmaz; sistem T67 öncesi davranışa döner).
> **Ayakta kalan gerekçe:** şartname **metni** (§2.1) kapalı güzergâhların
> *"fiziki engellerle kapatılacağını"* söyler — ince-engel riski **gerçektir**,
> yalnız görünümü bilinmiyor.
>
> **Model beklenmedi** (D-93): üreteç bariyeri **yalnız zaten kapalı** şeritlere
> koyuyor; açık zeminde bariyer oranı **%0,0**. Eğitim verisi bu örneği hiç
> içermiyor, dolayısıyla model bunu **öğrenemez**.

```python
BARIYER_KROMA_ESIGI            = 25          # LAB a*
BARIYER_EN_BOY_ORANI           = 4.0
BARIYER_ASGARI_GENISLIK_ORANI  = 60/1059     # ≈0,0567 · içerik genişliğinin oranı
BARIYER_ASGARI_ALAN_ORANI      = 300/(1059·634)
BARIYER_KAPAMA_ORANI           = 61/1059
```

**Neden kroma çalışır (bu figürde):** D-87 figürün renk künyesini ölçtü —
sahnenin **tamamında** `|a*| < 1`. Bariyer figürdeki **tek** yüksek kromalı
yapıdır; ölçülen tepe `a* = 44`. Eşik 25 iki tarafa da geniş pay bırakır.
⚠ Bu ayrışma **yapay zeka ürünü** bir görüntünün özelliğidir (D-99); gerçek
arenada geçerli olacağı **doğrulanmamıştır**.

🔴 **TUZAK — "kırmızı = engel" kuralı HEDEFİ ÖLDÜRÜR ve bu risk D-99 ile
KESİNLEŞTİ.** Şartname **metni** §2.1 hedefi *"2 m × 2 m … üzerinde **kırmızı
H harfi** bulunacağı bir bölge"* diye tanımlar. D-99 figürün yapay olduğunu
saptadıktan sonra **metin otoritedir**: HB gerçekten KIRMIZIDIR. D-87'nin
figüre dayanan "nötr ped" hükmü geçersizdir.
Naif bir kırmızı kuralı HB'yi engel yapar, İKA hedefe **hiçbir zaman** ulaşamaz,
`P_görev = 0`. Ayrım **renkle değil şekille**:

| yapı | en/boy (ölçülen) | sonuç |
|---|---:|---|
| HB pedi | **1,00** (T60, n=260) | KARE → **elenir** |
| bariyer kolu (kısa · uzun) | **7,0** · **14,2** | UZUN → engel |

Eşik `4,0` ikisinin ortasındadır. Sentetik **kırmızı** HB ile doğrudan sınandı
(`a*=65`, eşiği geçiyor): **0 engel pikseli**; aynı karede bariyer yakalandı.

**Ölçütler ORAN'dır, piksel değil** (§8). Referans ölçüm betiği çıplak piksel
kullanıyordu (kernel 61×5, alan 300, genişlik 60) ve **1059** genişliğindeki
kaynak karede kalibreydi; üretim zinciri tespiti **512×512** üzerinde yapar ve
orada o sabitler **kısa kolu kaçırır** (w=47 < 60). Orana çevrilince üç
çözünürlükte de aynı iki kol bulunur (w/W 0,093 · 0,215).

⚠ **Madde 15:** dedektör yalnız **engel katmanına ekler**; serbest alan
(`zemin AND NOT engel`) yalnız **küçülür**. `codes/rpi_inference.py`
`get_masks` içinde uygulanır — `r.masks is None` dalında da çalışır, çünkü
model hiçbir şey görmese bile bariyer engeldir.

🔴 **Kalibrasyon zemini: TEK bir YAPAY ZEKA GÖRÜNTÜSÜ** (D-88 + D-99).
Projenin elinde **hiçbir gerçek arena görüntüsü yoktur**; bu sabitler şartname
Şekil 1'den, yani bir illüstrasyondan türetildi. İlk gerçek arena karesi
geldiğinde **hepsi yeniden ölçülmelidir** ve renk anahtarının orada geçerli
olmaması **beklenebilir bir sonuçtur**.

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

> **Halka 5 artık SAHİPSİZ değil** (T43 · `REVIEW_LOG.md` D-59, D-22).
> Sahip: `codes/karar_sozlesmesi.py` — `mpp_irtifadan`, `rota_olcek_reddi`,
> `r_gerekli_piksel`. Sabitler oradan okunur; çağrı yerlerine çıplak sayı **yazılmaz**.

`mpp` = metre / piksel.

### 5.1 Üretim kaynakları — değerlendirildi, ölçüldü

| # | Kaynak | Formül | Bugün üretilebilir mi |
|---|---|---|---|
| **(a)** | **İrtifa + kamera FOV / odak** | `mpp = 2·h·tan(FOV_yatay/2) / W_px` · `mpp = h / f_px` | ✅ **EVET** — irtifa saha yolunda zaten okunuyor: MAVLink `GLOBAL_POSITION_INT.relative_alt` (`comms/inis_kaniti.py:143`). İkinci bir telemetri yolu türetilmez. |
| (b) | Bilinen ölçekli nesne (**2×2 m, üzerinde kırmızı H**, §2.1) → px/m | `mpp = HB_KENAR_M / pedin piksel kenarı` | ✅ **EVET (T72'den beri)** — üçüncü sınıf **eklenmeden** açıldı: `karar_sozlesmesi.hb_konumu` klasik **Katman 2** dedektörüdür (T67 deseni). Ölçüldü (n=260 sentetik kadraj): tespit **260/260**, merkez hatası medyan **0,71 px**, `mpp` medyan sapma **%5,2**. ⚠ **İKİNCİL kaynaktır** — §5.4'e bak. |

**Seçim: (a).** Gerekçe kolaylık değil, **üretilebilirlik**: (b)'nin dayandığı
tespit bileşeni sahada mevcut değil ve bir sınıf eklemeden ölçüm yapılamaz.

`SARTNAME_ASGARI_IRTIFA_M = 30.0` (§5.3.2) ve `IRTIFA_MAKUL_UST_M = 200.0`
makullük bandıdır; bandın dışındaki telemetri **ölçek üretmez** (fail-closed).

### 5.1.1 Canlı irtifa ve tazelik — bağlayıcı

Görev yolunda irtifa sabit bir başlangıç/CLI değeri değildir. Her kare için
`GLOBAL_POSITION_INT.relative_alt` kaynağının en güncel doğrulanmış örneği
`comms/inis_kaniti.py` içindeki tek okuyucudan alınır. Örneğin yaşı yalnız host
`time.monotonic()` saatiyle ölçülür; Pixhawk saati host saatine çevrilmez.

`TELEMETRI_IRTIFA_TAZELIK_S = 0.50` saniye azami güvenlik yaşıdır. Yaş bu
sınıra ulaşır ya da aşarsa, hiç örnek yoksa veya kaynak sistem kimliği
değişirse irtifa **yok** sayılır ve `OLCEK_YOK` üretilir. Aynı/eski
`time_boot_ms` paketi son geçerli örneğin geliş yaşını yenileyemez.
Bayat son değer tekrar kullanılmaz. Bu sayı telemetri yayın hızının saha
ölçümü değildir: gerçek Pixhawk mesaj hızı/gecikmesi henüz **DOĞRULANAMADI**;
akış bu sınırı sağlayamıyorsa sistem rota üretmeyerek fail-closed kalır.

`mpp` her karede karar maskesinin yatay içerik genişliği `icerik[2]` ile
hesaplanır. Model giriş boyutu (`INFER_SIZE`) bu formülün piksel alanı değildir;
onu kullanmak 640 px karede gerekli açıklık yarıçapını %20 eksik hesaplar.

### 5.4 İki ölçek kaynağı ÇELİŞİRSE — bağlayıcı (T72 · `REVIEW_LOG.md` D-105)

Artık `mpp`'nin **iki bağımsız kaynağı** var: (a) irtifa telemetrisi,
(b) HB pedinin bilinen 2,0 m kenarı. İkisi aynı anda varsa ne olacağı
**kodda değil burada** tanımlıdır; tek uygulama `olcek_capraz_kontrolu`.

| durum | seçilen `mpp` | gerekçe |
|---|---|---|
| yalnız telemetri | **telemetri** | §5.1'in birincil kaynağı |
| yalnız HB | **HB** | tek ölçüm; yoklukdan iyidir |
| ikisi var, bağıl fark ≤ `OLCEK_CAPRAZ_BANDI` (**0,25**) | **telemetri** | hiyerarşi değişmez; HB yalnız **doğrular** |
| ikisi var, fark bandı **aşıyor** | **hiçbiri** → `("celiskili", fark)` | 🔴 **ortalama ALINMAZ** |

🔴 **Çelişkide ortalama alınmaz ve biri seçilmez.** İki bağımsız ölçüm
çelişiyorsa *hangisinin doğru olduğunu bilmiyoruz* demektir; uydurma bir orta
değer, ölçülmemiş bir ölçeği ölçülmüş gibi gösterir. Fail-closed: ölçek yok
sayılır ve §5.2 işler.

**Bant neden 0,25:** HB'den türetilen `mpp`'nin ölçülen sistematik sapması
**%5,2** (medyan; p90 %8,6) — pedin piksel kenarı morfolojik kapamayla ~1,4 px
şişiyor. Bant bunun ~4,8 katıdır: gerçek bir çelişkiyi yakalayacak kadar dar,
dedektörün kendi sapmasını çelişki saymayacak kadar geniş. Ölçüldü: n=260'ta
**260 "doğrulandı" · 0 "çelişkili"**.

⚠ Bu sapma **sentetik** kümede ölçüldü ve HB'yi bizim çizdiğimiz biçimde
taşıyor; gerçek arenada geçerliliği **doğrulanamaz** (D-88 + D-99).

### 5.2 `mpp` YOKSA ne olur — bağlayıcı

1. **Görev yolunda rota ÜRETİLMEZ.** `rota_olcek_reddi(mpp)` kanonik
   `("OLCEK_YOK", detay)` döner; `run_image` / `run_video` / `run_camera`
   bu reddi yayınlar (§6.4 tablosu).
2. **`r_gerekli_piksel(None, …)` → `None`.** Bu *"kısıt yok"* demek **değil**,
   *"kısıt UYGULANAMAZ"* demektir. Çağıran ya ölçeksiz olduğunu açıkça
   kaydeder ya da reddeder — sessiz varsayılan **yasak**.
3. **Ölçeksiz kip** (`mpp=None`) yalnız sentetik kapılar ve yer-gerçeği
   ölçümleri içindir; `analyze_path` dönüşünde `olcum["olceksiz"] = True`
   olarak **işaretlenir** ve ekrana basılır.

🔴 **Kapatılan sessiz varsayım.** `costmap_path_finder.olcek_px(None)` hâlâ
`m = 1.0` alıp `r_gerekli_px = 1,10 piksel` döndürür. Bu *"ölçek yok"* değil
*"ölçek 1 metre/piksel"* demektir. Kompozit arenada gerçek değer
`1,10 / 0,0868 = 12,7 px` — yani gövde açıklığı sessizce **~11 kat** küçülüyordu
ve hiçbir uyarı basılmıyordu. Sayı geriye uyum için korundu; **görev yolu artık
onu kullanmıyor** (madde 1) ve `tests/test_olcek_ve_c_uzayi.py` farkı kilitliyor.

### 5.3 C-uzayı — gövde açıklığı `analyze_path` kolunda da uygulanır

`analyze_path`, rotayı **C-uzayında** kurar: `gecilebilir = (dist >= r_gerekli_px)`.
Bu, `costmap_path_finder.py:313`'teki kalıbın **taşınmışıdır**, kopyası değil.

- **Madde 15 uyumu yapısaldır:** `{dist ≥ r} ⊆ {dist > 0}` — serbest alan yalnız
  **daralır**. Ölçüldü: 7 kompozit karede fazla piksel **0**.
- Ölçek yoksa C-uzayı **uygulanmaz** ve `olceksiz` işaretlenir (§5.2/3).

**Ölçülen etki** (arena kompoziti, kusursuz yer gerçeği maskesi, tek değişken `mpp`):

| | doğru şerit | yanlış şerit | ret | rota darboğazı | güven |
|---|---:|---:|---:|---|---|
| C-uzayı **yok** | 1/7 | 0 | 6 | **1,0 px** (4 karede) | 0,028–0,117 |
| C-uzayı **var** | **6/7** | **0** | 1 | **13,0–15,0 px** | 0,644–0,744 |

Kalan 1 ret `UC_BANT_TEMAS_YOK`'tur ve C-uzayından **önce de** vardı — K-A'nın
kendi fail-closed reddidir.

---

## 6. Mesaj protokolü sözleşmesi

`comms/protocol.py` — newline ile çerçevelenmiş JSON, taşıyıcıdan bağımsız
(UDP sim / SiK Radio 433 MHz saha).

| Tip | Üretici | Alan | Anlam |
|---|---|---|---|
| `OPEN_ROUTE` | İHA | `road` (1=sol, 2=orta, 3=sağ), `conf`, `ref_xy`, `waypoints` | Doğrulanmış açık güzergâh |
| `NO_ROUTE` | İHA | `sebep`, `detay` | Rota üretilemedi — **sessizlikten farklıdır** |
| `HEARTBEAT` | herkes | `node`; İHA ayrıca `karar_yas` | Bağlantı canlılığı. `karar_yas` (A2/D-381): İHA'nın son **ALGI KARARININ** yaşı (sn, monotonik saat). Alan **YOKSA** yaş BİLİNMİYOR demektir; alıcı **TAZE SAYMAZ** — hat canlılığı algı canlılığı değildir (D-374: 45–51 s körlükte heartbeat akmaya devam eder) |
| `ACK` | YKS / İKA | `ref` (seq) | Alındı onayı |
| `CMD` | YKS | `cmd`, `hedef` | Operatör komutu (`IKA_GO`, `ARM`, …) |

### 6.1 Alıcı davranışı — bağlayıcı

- **Bilinmeyen tip sessizce yok sayılır.** Geriye uyumluluk bunun üzerine kuruludur.
- `NO_ROUTE`, `latest` içindeki **son geçerli rotayı EZMEZ**; ayrı alana yazılır.
- `NO_ROUTE` **geçici** bir durumdur, kalıcı başarısızlık değildir. İHA kare kare tarar;
  bir karede rota bulunamaması görevi iptal etmez. Alıcı **dinlemeye devam eder**.
- Sürüş sırasında `NO_ROUTE` gelirse araç **güvenli duruşa** geçer; yeni geçerli
  `OPEN_ROUTE` gelince devam eder.

### 6.6 ACK bağlama ve `IKA_GO` tekrar sözleşmesi — bağlayıcı (K4+K8, şartname §2.2.5 / §2.2.3)

**Gerekçe (ölçüldü, `results/sartname_bosluk/rapor.md` K4/K8):** `IKA_GO` tek paketti,
ACK beklenmiyordu, düğme kilitleniyordu — tek paket kaybı görevi geri dönülmez bitiriyordu
(`REVIEW_LOG` D-02). YKS, İKA'nın `ACK`'ını hiç işlemiyordu; hakem "İKA'ya aktarıldı" onayını
ekranda kanıt görmeden veriyordu.

- **`ACK.ref_tip` (isteğe bağlı alan):** onaylanan mesajın `type`'ı (`"OPEN_ROUTE"`, `"NO_ROUTE"`,
  `"CMD"`, `"IHA_LANDED"`). NEDEN: `seq` sayaçları **düğüm başınadır**; YKS'nin `IKA_GO` seq'i ile
  İHA'nın `OPEN_ROUTE` seq'i çakışabilir. Alıcı, `ref_tip` varsa `ref` **ve** tiple eşler; yoksa
  yalnız `ref` ile (geriye uyumlu — eski ACK'lar reddedilmez). Üretici: `protocol.ack(ref, node, ref_tip)`.
  **Kural her alıcı için geçerlidir (D-405 Q4 / T206):** YKS tarafı (`AckliTekrar.ack_geldi`)
  **ve** İHA tarafı (`IhaSender._tekrarli_gonder`) — hub fan-out'unda her tüketici herkesin
  ACK'ini gördüğü için tipsiz eşleme çapraz kabul üretebiliyordu (ölçüldü). YKS'nin ürettiği
  `OPEN_ROUTE`/`NO_ROUTE`/`IHA_LANDED` ACK'leri `ref_tip` **taşır**.
- **`IKA_GO` tekrar gönderimi (YKS):** aynı `seq` ile, `IKA_GO_TEKRAR_ARALIGI_S` aralıkla, en çok
  `IKA_GO_TEKRAR_UST_SINIRI` kez (`codes/karar_sozlesmesi.py`, gerekçeli). İKA'dan `ACK(ref=seq,
  ref_tip="CMD")` gelince durur. Üst sınır aşılırsa ekranda **KIRMIZI "İKA ONAY VERMEDİ"**, düğme
  yeniden aktif, İKA kronometresi başlamamış sayılır — **görev kaybedilmez**. Durum makinesi
  `comms/komut_tekrar.py` (Tk'dan bağımsız).
- **İKA idempotentliği:** mükerrer `IKA_GO` latch'i yeniden kurmaz (`ika_go_monotonic` ilk alımda
  sabitlenir) ama **her alım ACK'lanır** — YKS'nin tekrarı ancak böyle durur.
- **`PARACHUTE` (P9a · D-393, şartname §2.2.4 + SS7 Cceza):** YKS'nin manuel paraşüt yedeği,
  `CMD(cmd="PARACHUTE", hedef="iha")`. İki adımlı teyitle tetiklenir (T180 kalıbı, modal yok),
  tetiklendiği anda `PARASUT_MANUEL_CEZA_PUANI` (−50) işlenir ve komut `PARASUT_TEKRAR_ARALIGI_S`
  × `PARASUT_TEKRAR_UST_SINIRI` ile **ACK gelene dek tekrarlanır** (İHA düğümünden
  `ACK(ref_tip="CMD")`). Üst sınırda KIRMIZI görünür hata + düğme yeniden açılır.
  ⚠ **İHA tarafı alım/Pixhawk aktarımı AVİYONİK-BLOKLU** (Faz B, 5 Eylül): bugün İHA'da CMD
  dinleyen uç yok — ACK gelmez ve ekran bunu DÜRÜSTÇE kırmızı gösterir; sessiz başarı yalanı yok.
- **Aktarım kanıtı (K8):** İKA, `OPEN_ROUTE`/`NO_ROUTE` ACK'ını gönderene (İHA) **ve** bildiği YKS
  adresine (`--yks` ya da ilk geçerli `IKA_GO`'nun kaynağı) gönderir.
  ⚠ **`--yks` UDP'de fiilen ZORUNLUDUR** (dalga 2 çürütücüsü, 2026-08-26, ölçüldü): şartname
  sırasında `OPEN_ROUTE` `IKA_GO`'dan **önce** gelir, yani YKS adresi `IKA_GO`'dan öğrenilmeden
  rota ACK'ı üretilir; `--yks` yoksa kopya **hiç** gitmez. Bu yüzden `ika_nav.py --yks` ve
  `navitas_sim.py --landed-yks` aynı adresi `IkaReceiver(yks_peer=…)`'e bağlar.
  **Seri (SiK) hatta** `addr` daima `None`'dır: ACK **ortam yayını** olarak tek hatta yazılır, YKS
  ve İHA aynı paketi duyar — kopya gerekmez ama **asıl ACK üretilmek zorundadır**
  (`_rota_ack` seri dalı `_kontrol_mesaji_ack` ile aynı kuralı izler; eski kod seri hatta rota
  ACK'ını **hiç** üretmiyordu — dalga 2 ölçümü: yalnız `['CMD']`).
  YKS hakem düğmesi **fail-closed**: geçerli rota `seq`'i için İKA'dan
  `ACK(ref_tip="OPEN_ROUTE")` ekranda görünmeden 2. onay ("İKA'ya aktarıldı") **verilemez**; düğme
  pasif, gerekçe metni görünür; kanıt gelince düğme açılır ve zaman damgası yazılır.
  ⚠ UDP kurulumunda İKA `--yks host:port` ile başlatılmazsa kanıt YKS'ye ulaşmaz ve 2. onay
  **hiç açılmaz** — bu bilinçli bir seçimdir (kanıtsız onay yerine görünür ret).
- **YKS kronometresi / HB TEMAS (K4 küçük, dalga 2):** kronometre `IKA_GO` gönderildiği an başlar
  (hakem saati de komutla başlar); `VAZGECILDI`'de **her iki** damga (`t_ika0`, `t_ika1`) sıfırlanır
  (kronometre başlamamış sayılır, yeniden IKA_GO sonrası HB TEMAS kilitli kalmaz). `HB TEMAS`
  düğmesi yalnız `IKA_GO` ACK'ı ("İKA ALDI") gelince açılır — İKA komutu almadan HB teması olamaz.
- **`KararYayinci.stop()` (K1, dalga 2):** durma kontrolü yuvayı **boşaltmadan** bakar; gönderim
  sırasında yazılıp `stop()` ile yakalanan karar **atılmaz**, bir sonraki turda gönderilir.
- **İKA görevi çıkış kodu (K5, dalga 2):** `ika_gorevi` sürüş süresi dolunca **4** döner ve
  `navitas_sim.dinamik_ika_gorevi` yalnız **0**'ı başarı sayar — testle kilitli
  (`tests/test_dalga2_k1_k5_k8_kusurlari.py`).
- Kilit: `tests/test_ika_go_ackli_tekrar.py` (paket düşürme gerçek UDP loopback, ACK yok → üst
  sınır, mükerrer IKA_GO, kanıtsız düğme pasif; 5 mutasyonun tamamı yakalandı).

### 6.2 `road` sözleşmesi

`{1: "sol", 2: "orta", 3: "sag"}` — `open_route()` bu aralık dışında `ValueError` fırlatır.
Rota yoksa `NO_ROUTE` gönderilir; `open_route`'a `None` geçilmez.

**`road` HANGİ İSTATİSTİKTİR** (🔴 T155 · 2026-08-26 · `REVIEW_LOG.md` D-296):

    road = olcum["serit_karari"]          # rpi_inference.py — yayınlanan alan
         = karar_sozlesmesi.rota_serit_karari(rota_pikselleri, icerik_x0, icerik_w)
         = rotanın GÖVDESİNİ taşıyan şerit (en çok rota pikseli olan `serit_no()`)

Tanım **TEK YERDEDİR** (`karar_sozlesmesi.rota_serit_karari`, madde 16); hem
üretim yolu (`analyze_path`) hem `rota_bul` onu çağırır. `rota_bul`daki çağrı
**çapraz denetimdir** (`cikti["rota_serit"]`, `cikti["serit_uyumu"]`): o yolun
otoritesi kapıdır, `yol_no` DEĞİŞTİRİLMEZ.

`darbogaz_serit` (rotanın en dar noktasının şeridi) **hesaplanır ama artık
YAYINLANMAZ** — ölçüm sözlüğünde **tanı** alanı olarak kalır ve hakem ekranında
kanıt satırında "(tanı)" etiketiyle görünür. Darboğaz **açıklığı** güvenin
girdisi olmaya devam eder (değişmedi).

**ÖLÇÜM — neden değişti** (`results/t155/`, yer gerçekli 15 arena sahnesi;
yer gerçeği = üretecin açık bıraktığı güzergâh, karar yoluna HİÇ verilmez):

| yayınlanan alan | doğru | not |
|---|---|---|
| `darbogaz_serit` (T155 öncesi) | **6/15** | 9 sahnede yanlış |
| `serit_karari` (T155 sonrası) | **15/15** | ön kayıt §17 eşiği ≥ 14/15 |
| `rota_bul` `yol_no` (bağımsız referans) | 15/15 | aynı maske, aynı sahneler |

**Mekanizma:** `darbogaz_serit` şeridi **tek pikselden** okuyordu ve o piksel 15
sahnenin **13'ünde rotanın UCUNDA** ölçülüyordu (y=39 ya da y=460) — KB/HB
yakınında üç güzergâh **birleşir**, yani şerit kimliğinin **tanımsız** olduğu
yerde. Örnek (şerit başına rota pikseli):

    harita 1/kolay : 419/3/0    yer gerçeği 1 -> yayın 2   (422 pikselin 3'ü karar verdi)
    harita 5/zor   : 7/416/0    yer gerçeği 2 -> yayın 1   (423 pikselin 7'si)
    harita 3/zor   : 427/189/7  yer gerçeği 1 -> yayın 3   (623 pikselin 7'si)

**Bozulmama (ön kayıt §17 ek şartı, ölçüldü):** aynı 15 sahnede waypoint
listeleri, ret sebepleri, güven ve tüm tanı alanları **BAYT-EŞ** aynı kaldı
(142 waypoint, 0 fark — `results/t155/bozulmama_kiyas.py`). Değişen tek şey
yayınlanan sayıdır; 9 sahnenin 9'u da **düzeldi**, hiçbiri bozulmadı.

**D-167/D-168 NOTU KALIR (tarih).** T96'da (n=209, kadraj kümesi) üç aday
ölçülmüştü — `darbogaz_serit` 198/209 · `cikis_serit` 197 · `baskin_serit` 196 —
ve o kayıt farkı belirleyen 11 karenin yer gerçeğinin **kırılgan** olduğunu
(açık şeridin merkezi `serit_no` sınırına medyan **4,6 px**) açıkça yazmıştı;
"daha iyi olduğu **gösterilmemiştir**" hükmü oradan geliyordu. T155 o soruyu
**yer gerçeği sağlam** bir kümede kapatmıştır.

⚠ **DÜZELTME (2026-08-26, çürütücü bulgusu · D-296):** yukarıdaki paragrafın ilk
sürümü *"198→196 sıralamasının yeni tanımla ne olacağı ÖLÇÜLMEDİ"* diyordu —
**yanlıştı.** `rota_serit_karari` master'ın `baskin_serit` formülünün **birebir
aynısıdır** (en çok rota pikseli taşıyan şerit, beraberlikte küçük indis;
`rpi_inference.py` eski `:1246` ile metin olarak özdeş, 20.000 rastgele girdide
0 ayrışma ölçüldü). Yani yeni yayınlanan alan **T96'nın B adayıdır** ve o
kümedeki skoru zaten defterdedir: **`B_baskin` 196/209 (%93,8)** — `A_darbogaz`
198/209'un **2 kare** altında. İki küme birlikte okunur:

| küme | yer gerçeği | `darbogaz` (eski yayın) | `baskin` = yeni yayın |
|---|---|---:|---:|
| T96 kadraj (n=209) | **kırılgan** (ayrışan 11 karede merkez `serit_no` sınırına medyan 4,6 px) | 198 | 196 |
| T151 arena (n=15) | **sağlam** (üç koridor paralel, üreteç yer gerçeği) | **6** | **15** |

D-167 o 2 karelik farkı zaten *"karara bağlanamaz"* diye yazmıştı; 9 karelik
fark ise yer gerçeği sağlam kümededir. Karar bu iki sayıya birlikte dayanır.

⚠ **T119'un yeni pozitif kontrolü DAR MARJA dayanıyor (çürütücü ölçtü, D-296):**
`_zikzak` şerit dağılımı **(389, 600, 640)** — kazanan şerit 3, şerit 2'yi 1.629
pikselde yalnız **40 px (%2,5)** geçiyor. `test_zikzak_sahne_gecerliligi_govde_hala_uc`
sabit **3** assert ediyor; sahne geometrisinde 40 piksellik bir oynama kararı 2'ye
çevirir ve o kapı kırmızı yanar. Bu bir kusur değil **kırılganlık kaydıdır**: sahne
değişirse önce bu marj ölçülmelidir.

🔴 **AÇIK ÇELİŞKİ — mimarın kararına bırakıldı (T155 raporu, açık soru).**
`tests/test_t119_yayinlanan_road_kapisi.py`nin `_zikzak` sahnesinde alt/üst
dikeyler şerit 3'te, tek geçiş şerit 1'deki dar kapıdadır: "hangi güzergâh
açık" (gövde, **3**) ile "darboğaz hangi şeritte" (kapı, **1**) **ayrışır**.
Şartnamenin sorduğu soru birincisidir ve arena üç koridoru **paraleldir**
(açık rota gövdesiyle tek şeritte kalır); `_zikzak` gibi üç şeride dengeli
yayılan bir rota arena geometrisinde **oluşmaz**. Ayrıca ölçüldü: **`rota_bul`
bu sahnelerin hiçbirinde karar vermiyor** (`BELIRSIZ_TEK_KAPI`, `yol_no=None`),
yani bağımsız karar yolu bu çelişkide **hakemlik yapamıyor**. T119 yeni
sözleşmeye nişanlandı ve çelişki o dosyanın başlığında **kayıtlı** tutuldu.
Önerilen takip (ayrı ön kayıt ister, bu turda **GİRMEDİ**): rota gerçekten üç
şeride dengeli yayıldığında tek etiket yayınlamak yerine **fail-closed** durmak
— `rota_bul`un bu sahnelerde zaten yaptığı şey. Gerçek karede ret oranını
değiştireceği için GPU'lu ölçüm olmadan bağlanmaz.

📜 **TARİHÇE — D-41 geri ALINMADI.** T31/T32 (D-41) şeridi koridorun üst %30
bandından değil **rotanın kendisinden** okutmuştu; o düzeltme yerinde duruyor.
T155 yalnızca rotanın **hangi noktasından** okunacağını değiştirdi: tek uç
değerden (darboğaz) **gövdeye**. T151/D-295 kusuru ölçüp belgeledi
(`results/t151/iki_yol_kiyasi.json`, mimar vekili bağımsız yeniden koştu);
T155 kapattı.

⚠ `road` **İKA'nın sürüş girdisi DEĞİLDİR** (D-166). Sürüş `waypoints`+`ref_xy`
ile olur (`simulation/scripts/ika_nav.py:178-182` sayısal `road`'u geometri
saymayı açıkça reddeder). `road` **yayınlanan ve puanlanan etikettir**.

### 6.3 Karar geçerliliği sözleşmesi — uç-band teması ve güven eşiği

> Bir `OPEN_ROUTE` yayınlanmadan önce **iki bağımsız kapıdan** geçer. İkisi de
> **fail-closed**: şüphe varsa `NO_ROUTE`. Gerekçe: şartname §5.3.2/§6.2 yanlış
> güzergâhı **0 puan** sayar. Çekimserlik puan kaybettirir, yanlış karar **sıfırlar**.
>
> Sabitler `codes/karar_sozlesmesi.py`'de tanımlanır; çağrı yerlerine çıplak sayı
> **yazılmaz** (madde 16).

#### K-A · Uç-band teması (T26 · `REVIEW_LOG.md` D-29)

Seçilen koridor bileşeni **HEM başlangıç (alt) HEM hedef (üst) uç bandına** yeterli
genişlikte temas etmelidir. Etmiyorsa koridor kareyi baştan başa geçmiyor demektir →
karar `None`. Temas ölçütü **aynı bileşen** üzerinden değerlendirilir.

> ⚠ **Bu madde bir kez EKSİK yazıldı.** İlk sürümde yalnız *hedef* bandı şart
> koşuluyordu. Codex ölçtü: ortadaki bariyerle kopmuş bir koridorda OpenCV eşit
> parçalardan **üst** olanı seçiyor → *hedefe temas VAR, başlangıca temas YOK*, ve
> kusur `yol=2` olarak geri dönüyor. Tek uç yetmez; **iki uç birden** şarttır.

```python
HEDEF_BANT_ORANI     = 0.08   # içerik kutusu yüksekliğinin üst %8'i
BANT_TEMAS_MIN_ORANI = 0.02   # bileşenin bant içindeki genişliği ≥ içerik genişliğinin %2'si
```

**`0.08` neden bu değer:** `costmap_path_finder._tohum_maske` **aynı** oranı kullanıyor
(`:237` `pay = max(1, int(h * 0.08))`). `rota_bul` o bantla `_bagli_mi()` sınayıp kapalı
koridoru `KAPALI_KOPUK` ile **doğru** yakalıyor; `analyze_path` yakalamıyordu. İki karar
yolu **aynı bandı** kullanır — ikinci bir sayı türetilmez (S4'ün ıraksama kusuru).

**`0.02` neden:** tek piksellik gürültü "temas" sayılmasın. Mutlak piksel değil **oran** —
çözünürlük değişince ölçüt kaymasın (§8).

⚠ `analyze_path`'in mevcut üst **%30** bandı (`rpi_inference.py:264`) *şerit seçimi*
içindir ve **kalır**. K-A ondan ayrı, **ek** bir geçerlilik kapısıdır.

#### K-B · Güven eşiği (T25 · `REVIEW_LOG.md` D-28, D-31, **D-37**, **D-38**)

```python
ROTA_GUVEN_ESIGI = 0.20
```

Bu eşiğin **altındaki** karar `OPEN_ROUTE` olarak **yayınlanmaz**; `NO_ROUTE` sebebiyle
bildirilir.

> ⚠ **Bu değer bir kez YANLIŞ konuldu.** İlk sürümde `0.50` yazılmıştı ve dayanağı
> **sentetik** sahnelerin güveniydi (`0,797` / `1,000`). Codex gerçek GUI yolunda ölçtü
> (D-37): eşik **52 kararın tamamını** reddetti → **%100 çekimserlik**. Sözleşmeyi
> ölçmediğim bir dağılıma göre yazmıştım. Aşağıdaki değer **ölçümden** türetilmiştir.

**Gerçek 67 karede ölçülen dağılım** (v21, `imgsz=512`, GUI zinciri; D-38):

| min | p25 | p50 | p90 | max | ortalama | **std** |
|---|---|---|---|---|---|---|
| 0,2440 | 0,2790 | 0,3070 | 0,3386 | 0,3520 | 0,3018 | **0,0304** |

**Eşik süpürmesi** (67 kare):

| eşik | geçen | çekimserlik |
|---|---:|---:|
| **0,20** | **45** | **%32,8** ← K-A'nın kendi çekimserliği; K-B ek eleme yapmaz |
| 0,28 | 33 | %50,7 |
| 0,3333 | 9 | %86,6 |
| 0,50 | 0 | %100 |

**`0.20` neden — ve K-B'nin gerçek rolü.** Metriğin gerçek veride **ayırt edici gücü
yok**: `std = 0,030`, tüm kütle 1/3 çevresinde. Buraya seçici bir eşik koymak kötü kararı
elemek değil, **rastgele kare elemek** olur — süpürme tablosundaki sert düşüş bunu
gösteriyor. Bu yüzden K-B **seçici bir kapı değil, taban koruyucusudur**:

- ölçülen en düşük geçerli karar `0,244`'ün **altında** → gerçek kararları elemez;
- `0,0` ve yakınını **eler** → D-28'de ölçülen *"`guven=0.0` olan karar `OPEN_ROUTE`
  yayınlanabiliyor"* kusurunu kapatır;
- sentetik yol (`0,797`) etkilenmez;
- `karar_sozlesmesi.rota_guven_reddi` ayrıca **bool / NaN / sonsuz / `[0,1]` dışı**
  değerleri fail-closed reddeder — asıl bozuk-değer koruması budur.

🔴 **T43 · K-B'nin rolü DEĞİŞTİ — ölçüldü, değer değişmedi.**

C-uzayı (§5.3) geldikten sonra rota üzerindeki her piksel `dist ≥ r_gerekli_px`
sağlar. `guven = min(1, darboğaz / (ROTA_DARBOGAZ_TAM_ORANI · icerik_w))` olduğu
için güvenin **hesaplanabilir bir TABANI** oluşur:

```
guven_tabani = r_gerekli_px / (ROTA_DARBOGAZ_TAM_ORANI · icerik_w)
```

Yani K-B **ancak** şu koşulda ateşleyebilir:

```
mpp  >  R_GEREKLI_M / (ROTA_GUVEN_ESIGI · ROTA_DARBOGAZ_TAM_ORANI · icerik_w)
     =  1,10 / (0,20 · 0,035 · icerik_w)
```

| `icerik_w` | K-B'nin ateşleyebildiği eşik | görev irtifasında tipik `mpp` | K-B ateşler mi |
|---|---|---|---|
| 576 | `mpp > 0,273 m/px` | 0,03–0,12 | **hayır** |
| 1024 | `mpp > 0,153 m/px` | 0,03–0,12 | **hayır** |

**Sonuç — üç rol, ikisi hâlâ geçerli:**

1. ~~Seçici kapı~~ — **değil** ve olamaz: ölçekli kipte yapısal olarak erişilemez.
2. **Ölçeksiz kipin tek tabanı** — `mpp` yokken C-uzayı uygulanamaz; `guven=0,0`
   yayınını engelleyen tek şey K-B'dir (D-28'in kapattığı kusur).
3. **Çözünürlük koruyucusu (YENİ)** — ateşlediği tek durum, ölçeğin araç gövdesini
   ~4 pikselden ince gösterdiği haldir. Orada geometri doğru olsa bile piksel
   ızgarası kararı taşıyamaz; reddetmek doğrudur.

**Değer `0.20`'de BIRAKILDI — gerekçe ölçümden:**
- *Düşürmek* anlamsız: ölçekli kipte zaten hiç ateşlemiyor.
- *Yükseltmek* zararlı: C-uzayının **zaten** garanti ettiği fiziksel kısıtı ikinci
  kez, üstelik birimsiz bir oranla sayardı; ve tam da C-uzayının en güvenilir
  olduğu ince ölçeklerde geçerli rotaları elerdi.
- Arena yer gerçeğinde ölçülen güven **0,644–0,744**; eşik oraya dokunmuyor.

⚠ **Açık ölçüm borcu (T43 sonrası):** `ROTA_DARBOGAZ_TAM_ORANI = 0.035` hâlâ
otopark karelerinden kalibre edilmiş **birimsiz** bir orandır. C-uzayı geldiğine
göre güven doğrudan `darboğaz / r_gerekli_px` (yani **fiziksel kat**) olarak
tanımlanabilir ve o zaman `icerik_w`'den bağımsızlaşır. Ayrı görev.

### 6.4 Karar reddi sebep sözleşmesi (T28 · `REVIEW_LOG.md` D-39)

> **Neden var:** `analyze_path` reddi sessizce `None` dönüyordu. Ekranda *"model
> bulamadı"*, *"uç-bant kapısı reddetti"* ve *"güven eşiği reddetti"* **aynı**
> görünüyor — hakem ayırt edemiyor, operatör sistemi bozuk sanıyor. Ölçülmüş olay:
> kullanıcı GUI'yi "yol algılamıyor" diye bildirdi; gerçekte 12 karenin 8'inde maske
> yoktu, kalan 4'ün 3'ünü kapı elemişti. **S9 ile aynı sınıf: kanıt bütünlüğü.**

Ret üreten her yol, kanonik bir `(sebep, detay)` çifti döndürür. `sebep` kodları
`codes/karar_sozlesmesi.py`'de sabit olarak tanımlanır — **çağrı yerlerine çıplak
string yazılmaz** (madde 16).

| `sebep` | Ne zaman | Nerede |
|---|---|---|
| `OLCEK_YOK` | **Halka 5**: `mpp` türetilemedi — görev yolunda rota üretilmez (§5.2) | `rota_olcek_reddi` |
| `ZEMIN_MASKESI_SUPHELI` | **T48**: zemin maskesi içeriğin `ZEMIN_KAPLAMA_TAVANI`'ndan fazlasını kaplıyor — maske sahneyi ayırt etmiyor | `zemin_maskesi_reddi` |
| `MASKE_YOK` | Zemin maskesi hiç üretilmedi (`trav.sum() == 0`) | `analyze_path` girişi |
| `BILESEN_YOK` | Maske var, bağlı bileşen yok | bileşen etiketleme sonrası |
| `UC_BANT_TEMAS_YOK` | **K-A**: koridor alt ve/veya üst uç bandına temas etmiyor | `_uc_bant_temasi_yeterli` |
| `ALAN_YETERSIZ` | Koridor alanı `min_area_ratio` altında | `_koridor_alani_yeterli` |
| `GORUS_HATTI_KOPUK` | Başlangıç–hedef bağlantısı veya bu bağlantı üzerinde doğrulanmış waypoint zinciri kurulamıyor | `_bagli_mi` / A* rota üretimi |
| `KENAR_GUVENSIZ` | **T24**: ardışık waypoint'ler arası görüş hattı engelden geçiyor | `_kenarlar_guvenli` |
| `DUSUK_GUVEN` | **K-B**: güven `ROTA_GUVEN_ESIGI` altında | `rota_guven_reddi` |
| `KORIDOR_DEGIL` | **T65**: rota darboğazı **bir şeridin tamamından** geniş — bu bir güzergâh değil açık arazidir | `rota_koridor_genisligi_reddi` |
| `HEDEF_YOK` | **T72**: HB (2×2 m kırmızı H bölgesi) karede bulunamadı — varış noktası bilinmeden rota üretilmez (§2.2.6) | `hedef_yok_reddi` |

#### `ZEMIN_MASKESI_SUPHELI` — kaplama tavanı (T48)

> **Neden var:** üretim modeli bu alanda pratikte *"araç mı, değil mi"* ayırıcısıdır;
> **çatı, çim ve toprak** zemin sınıfına düşer. Maske "dolu" göründüğü için K-A,
> C-uzayı ve K-B'nin **hiçbiri** bunu yakalayamaz — hakem ekranı bina çatısı
> üzerinden geçen bir rotayı kendinden emin çizebiliyordu.

`kaplama` := zemin (sınıf 0) maskesinin **içerik kutusundaki** piksel oranı; ham
maske üzerinde, morfoloji ve engel çıkarmadan **önce** ölçülür.

```python
ZEMIN_KAPLAMA_TAVANI = 0.55      # T142 · D-286 · önceki 0.67 (T59, v24 dönemi) · 0.55 (v21 dönemi)
```

**Ölçüm** (üretim zinciri, `conf=0.30`) — üç bağımsız meşru kaynak, iki çökmüş küme:

| küme | n | p50 | p95 | **maks / min** |
|---|---:|---:|---:|---:|
| sentetik arena **yer gerçeği** (etiket poligonları) | 60 | %11,7 | %22,1 | **maks %39,0** |
| sentetik arena, v17 + v21 **model çıktısı** | 120 | %11,8 | %23,2 | **maks %38,7** |
| genel kapının **kendi 15 sahnesi** | 15 | %36,4 | — | **maks %42,6** |
| v21 **otopark** (çatı/çim yeşil) — çökmüş | 67 | %79,9 | — | **min %76,7** |
| v21 **kompozit arena** — çökmüş | 7 | %82,7 | — | **min %76,0** |

Bu tablo **v21 çıktılarıyla** kuruldu ve `0.55` oradan türetildi.

#### T59 · yeniden kalibrasyon — `0.55 → 0.67` (D-84, D-85, **D-86**)

İki şey birden değişti: üretim modeli **v24** oldu (T58) ve elimize **gerçek
arena karesi** geçti — `data/arena_referans/sartname_s9_arena.png`, şartname
s.9, projenin **tek** gerçek arena görüntüsü. v24 onu doğru segmentliyor, ama
kapı reddediyordu:

```text
gercek arena  kaplama 0.579 > 0.55  VE  kenar 0.585 > 0.50  ->  RET
```

**Bağımsız ölçüm** (T59, v24, kümenin **tamamı**):

| küme | n | kaplama min..maks | kenar min..maks |
|---|---:|---|---|
| MEŞRU kadraj arena | 260 | 0.000..0.863 | 0.000..0.682 |
| MEŞRU **gerçek arena** | 1 | 0.579 | 0.585 |
| ÇÖKÜŞ otopark | 67 | 0.770..0.866 | 0.579..0.971 |

**Hiçbir sinyal tek başına ayırmıyor** (kaplama: meşru maks 0.863 > çöküş min
0.770; kenar: 0.682 > 0.579). Kapı bu yüzden **AND** birleşimidir.

| eşik çifti | meşru elenen | kaçan çöküş |
|---|---:|---:|
| `(0.55, 0.50)` eski | **3/261** — biri **gerçek arena** | 0/67 |
| `(0.67, 0.50)` yeni | **1/261** | 0/67 |

⚠ **Tam ayrık çift yoktur.** D-85 220 kareli bir alt kümede `(0.67, 0.50)` için
tam ayrım (0/221, pay 0,062) bildiriyordu; kümenin tamamında bu **doğrulanmadı**.

⚠ **Kapının bilinen sınırı — artık ölçülmüş bir örneği var.** Bu bir *kaplama*
kapısıdır, doku kapısı değil. Orta şiddetli çökme **geçer**: `sa_000150.jpg`'de
model kaplaması 0.617 (< 0.67 → geçiyor) iken **yer gerçeği 0.380**; IoU 0.613,
model kenarı 0.658'e karşı gerçek 0.190. Yakalamak için maskenin **yapısı**
(doku/renk tutarlılığı) gerekir — ayrı görev.

🔴 **Eşikler MODELE BAĞLIDIR.** v21 için türetilen `0.55`, v24'te yanlıştı ve
gerçek arenayı eliyordu. **Üretim modeli her değiştiğinde bu kalibrasyon zorunlu
adımdır.** Meşru taraf ayrıca **tek** gerçek kareye dayanıyor; ikinci bir gerçek
arena karesi geldiğinde eşik yeniden ölçülmelidir.

Regresyon kilidi: `tests/test_gercek_arena_kapisi.py` — eşik ileride yeniden
oynatılır ve gerçek arenayı tekrar elerse bu paket düşer.

Kapı madde 15 açısından nötrdür: yalnız reddeder, hiçbir piksel eklemez.

#### T142 · yeniden kalibrasyon — `(0.67, 0.50) → (0.55, 0.40)` (D-283, D-286 · 2026-08-26)

D-283 ölçtü: T59'un "geçmesi gereken" gerçek arena maskesi (v24, kaplama 0.579)
**çökmüş** bir maskeydi (sahnenin tamamı yeşil); 0.67 tavanı bir çöküşü geçirmek
için gevşetilmişti. Üretim v35 ile **dört kümede** yeniden kalibre edildi
(`results/t142/olcum.md`, kutu paydası, conf 0,30, imgsz 512):

| çift K/E | v35 meşru sentetik RET (260) | v35 otopark RET (67) | v35 DJI RET (59) | v35 arena RET (1) | v24 otopark ÇÖKÜŞ yakalama (67) | v24 arena ÇÖKÜŞ yakalama (1) |
|---|---:|---:|---:|---:|---:|---:|
| `(0.67, 0.50)` eski | 0 | 0 | 0 | 0 | 67/67 | **0/1** |
| `(0.60, 0.45)` | 0 | 0 | 0 | 0 | 67/67 | 0/1 |
| **`(0.55, 0.40)` yeni** | **0** | **0** | **0** | **0** | **67/67** | **1/1** |
| `(0.50, 0.35)` | 0 | **6** | 0 | 0 | 67/67 | 1/1 |

**Karar (mimar vekili 2):** `(0.55, 0.40)` — meşru v35 kümelerinde **0 ret** ile
v24 arena çöküşünü de yakalayan en muhafazakâr çift. Pay dar: v35 meşru sentetikte
8 kare kaplama kolunu tek başına aşıyor, `sa_000176` kenar 0.5004 > 0.40 ama
kaplama 0.494 < 0.55 — **AND** birleşimi kurtarıyor (pay 0,056).

⚠ **Sınırlar:** çöküş sınıfı **v24 vekilidir** — v35'in kendi ölçülmüş çöküşü yok;
gerçek arena n=1. **T135:** `icerik=None` + 16:9 letterbox paydasında **iki kol da
ölüdür** (kenar tavanı 2h/(4w−4) = 0.2815 — D-268 §6'nın "kenar kolu çalışır"
cümlesi kırpık maske için yanlış); kapı yalnız gerçek içerik kutusu geçirilince
çalışır. Çağıranlar `icerik` geçirmek **zorundadır**.

#### `KORIDOR_DEGIL` — koridor genişlik tavanı (T65)

> **Neden var** (`REVIEW_LOG.md` D-90 bulgu 3, D-94): karar yolunun **arena
> sınırı kavramı yok**. Üreteç arena dışına bilerek etiketsiz düz zemin çizer
> (gerçekçidir — dronun gördüğü arazi arena ile bitmez), model orayı **haklı
> olarak** zemin işaretler, karar yolu ise tüm kareyi üçe bölüp o boş kenarı
> geçerli güzergâh sayar. `sa_000070`: darboğaz **304 px**. **Aynı kusur gerçek
> karede de var** — `sartname_s9_arena.png`'de ızgaralı arenanın dışındaki
> toprak da zemin işaretleniyor.

⚠ **Sınır yerelleştirilemedi ve bu bilinçli bir karardır.** Üç aday imza ölçüldü
(260 kadraj karesi + gerçek kare); **üçü de** güvenilmez çıktı ve **üçü de
gerçek karede çöktü**:

| aday imza | n | IoU medyan | güvenilir mi | gerçek karede |
|---|---:|---:|---|---|
| ızgara çizgileri | 260 | 0,806 | **hayır** | **tüm kareyi** verdi (arenayı büyütür) |
| moloz kapsayan kutusu | 260 | 0,664 | **hayır** | dar yanlı; moloz arenayı doldurmuyor |
| dış çerçeve | 260 | 0,960 | **hayır** | **hiç sınır üretemedi** |

Ve daha temelde: **gerçek arena sınırı dikey değil.** Perspektif nedeniyle
yamuk (sol kenar x≈190 üst → x≈65 alt; sağ x≈920 → x≈1015). Tek bir `[x0,x1]`
aralığının indirgenemez hatası **~50–60 px**'dir.

**Bu yüzden sınır yerelleştirilmiyor.** Kusurun ölçülen yapısı buna izin veriyor:
hata **dejeneredir** — rota ya tamamen arena içinde ya tamamen dışında
(`arena_disi` oranı: 238 kare `0.000` · 1 kare `0.001` · 10 kare `1.000`; ara
değer yok). Dolayısıyla *"sınır nerede"* sorusu değil, *"bu bir koridor mu"*
sorusu yanıtlanır.

```python
SERIT_SAYISI = 3
KORIDOR_GENISLIK_TAVANI_SERIT = 1.0        # bir koridor EN ÇOK bir şerit kadar geniş
```

Şartname arenada **üç güzergâh** tanımlar ve bunlar molozla ayrılır. Bir şeridin
tamamından geniş bir "koridor" üç güzergâhtan biri **değildir**. Tavan
`serit_no`'nun kendi bölüşümünden türetilir — çıplak sayı değildir (madde 16) —
ve ikisinin uyumu `tests/test_koridor_genisligi.py` ile kilitlenir.

**Ölçüm** (v24 · T60 kadraj · n=260 · üretim zinciri · rota üretilen 249):

| küme | n | `darbogaz / icerik_w` |
|---|---:|---|
| **meşru** (arena içi) | 239 | medyan 0,094 · p95 0,208 · **maks 0,280** |
| **kusurlu** (arena dışı) | 10 | 0,022 · 0,028 · 0,111 · 0,170 · **0,314** · **0,353 · 0,358 · 0,375 · 0,475 · 0,487** |

Tavan `1/3 = 0,333`: **yanlış elenen meşru 0/239**, yakalanan **5/10**. Meşru
tarafa pay **0,053**, kusurlu tarafa **0,020**.

⚠ **Bu KISMİ bir çözümdür.** Kaçan 5 kareden **4'ü** meşru azaminin (0,280)
altındadır — genişlikle **ayırt edilemezler**: arena dışı bölge her zaman boş
değildir (`sa_000068` arena dışında bir **otopark fotoğrafı** taşır, park
çizgileriyle; model orada 14 px darboğazlı kendi koridorunu bulur). Kalan
1 kare (0,314) meşru azaminin üstündedir; `(0,280 · 0,333)` aralığına konacak
**fit edilmiş** bir tavan onu da yakalardı — bilerek yapılmadı: (i) fiziksel
değil fit edilmiş olurdu; (ii) 0,280 **sentetik** karelerden gelir ve üreteç
kadraj kipinde geometrik + fotometrik bozunumu **kapatır**, yani gerçek meşru
dağılım daha geniştir — optimist bir azamiye eşik oturtmak D-85'in hatasıdır;
(iii) payı ±0,017'ye inerdi.

⚠ **Madde 15**: bu ölçüt yalnız **reddeder**. Serbest alanı büyütmez, maskeye
dokunmaz, tek piksel eklemez.

**`detay`** insan-okur ve **ölçülen değeri taşır** — hangi uç (`alt`/`üst`), ölçülen
güven, ölçülen alan oranı. Örnek: `"Rota guveni 0.180; gereken >= 0.200."`

**Bağlayıcı kurallar:**

1. **Yayın yolu:** `NO_ROUTE` mesajının `sebep` alanı bu tablodan gelir (`protocol.py`
   `sebep`'i zaten zorunlu tutuyor, boş kabul etmiyor); `detay` opsiyonel alana yazılır.
2. **Ekran yolu:** hakem ekranı `TESPİT YOK` yerine **sebebi** gösterir. Üç farklı ret
   üç farklı metin üretmelidir — aynı metin görünüyorsa kapı çalışmıyor demektir.
3. **Fail-closed korunur:** sebep bildirmek reddi yumuşatmaz. Ret yine `yol=None`,
   `waypoints=[]`.
4. Yeni bir ret yolu eklenirse **önce bu tabloya** satır eklenir, sonra kod yazılır.
5. **Örnekleme kararı değiştirmez:** `n_waypoints` yalnız doğrulanmış rota üzerindeki
   çıktı yoğunluğudur. Aynı maske ve aynı karar parametrelerinde `n_waypoints`
   değişince `yol`/ret sebebi değişemez. Koridor bağlantısı `_bagli_mi` ile,
   yayınlanan zincir ise bağlantısı kanıtlanmış A* yolu üzerinde doğrulanır.
6. **Planlama bütçesi:** `ROTA_PLAN_MAKS_HUCRE = 32768`, bir `analyze_path`
   çağrısındaki bütün witness A* denemelerinin toplam plan-hücresi bütçesidir.
   Bütçeyi aşan daha ince ızgara denenmez; doğrulanmış zincir kurulamıyorsa
   `GORUS_HATTI_KOPUK` ile fail-closed dönülür. Tam çözünürlük A*'a koşulsuz
   düşüp GUI worker'ını saniyelerce bloke etmek yasaktır. A* zincirinin ilk
   waypoint'i alt başlangıç tohumu, son waypoint'i üst hedef tohumu içinde olmalıdır.

#### Nerede uygulanır — **ikisinde birden** (D-31'in mimara bıraktığı karar)

| katman | rol |
|---|---|
| **Çağrı yerleri** — `rpi_inference`, `iha_perceive`, `yks_gui` | Erken karar: operatöre ve günlüğe **anlamlı sebep** yazar |
| **`IhaSender.send_open_route`** | **Son savunma.** Eşik altı `conf` ile çağrılırsa yayınlamaz — kaçak imkânsız |

Yalnız çağrı yerlerinde uygulamak **yetmez**: yeni bir çağrı yeri eklendiğinde unutulur
ve kusur sessizce geri gelir — D-31'in tam da uyardığı şey. Yalnız `IhaSender`'da
uygulamak da **yetmez**: operatör *neden* yayınlanmadığını göremez.

⚠ **Kalibrasyon borcu.** `0.50` sentetik sahne ölçümünden türetildi. Gerçek **67 karede**
güven dağılımı ölçülüp eşik yeniden değerlendirilecek — *aşırı çekimserlik sahada
kullanılamaz demektir* (T26 kapısının istediği önce/sonra tablosu). Değer değişecekse
**önce burası** değişir, sonra kod.

### 6.5 Üretim algı yolu yayın sözleşmesi — K1 (şartname §2.2.3, 2026-08-26)

> **Neden var:** `results/sartname_bosluk/rapor.md` K1 — `codes/rpi_inference.py`
> `run_camera`/`run_video` telsize **hiç** yazmıyordu; OPEN_ROUTE/NO_ROUTE üreticisi
> yalnız Gazebo betiğiydi (§11.1/1 gereği sahip sayılmaz). Sahada İHA kararı YKS'ye
> ve İKA'ya ulaşmıyordu.

**Üretici:** `comms/iha_sender.py` `KararYayinci` (jetson paketinde aynı dosya).
Kurulum yalnız `--yks-hedef ip:port` / `--ika-hedef ip:port` / `--telsiz-seri PORT`
verilince; **hedef yoksa gönderici hiç yüklenmez, davranış bayt-eş aynıdır**.

| kural | değer / davranış | kaynak |
|---|---|---|
| Her karede **tam bir** mesaj | `OPEN_ROUTE` **veya** `NO_ROUTE` — sessizlik yok | `rpi_inference._karari_yayinla` |
| Ret sebepli karar | `NO_ROUTE(sebep, detay)`; **hiçbir koşulda** OPEN_ROUTE | `KararYayinci._karari_gonder` |
| `open_path is None`, sebep yok | `NO_ROUTE(KARAR_YOK)` | `karar_sozlesmesi.KARAR_YOK_SEBEBI` |
| Güven kapısı (K-B) | **çoğaltılmaz**: OPEN_ROUTE yalnız `IhaSender.send_open_route` üzerinden geçer, eşik altı orada NO_ROUTE olur | `iha_sender.py:128-132` |
| `ref_xy` | daima `[0, 0]` — sahada dünya çerçevesi yoktur, İKA saf öteleme yapar (§3.2) | `YAYIN_REF_XY` |
| waypoint çerçevesi | tuval-piksel → **yerel metre**: `x=(px−px₀)·mpp`, `y=(py₀−py)·mpp` (piksel y aşağı, yerel y **ileri**; `iha_haritala.piksel_to_dunya` ile aynı yön kuralı); ilk nokta `[0,0]`; kenar `MAX_SEGMENT_M`'i aşarsa **mevcut kenar bölünür**, yeni geometri eklenmez; sonuç `rota_geometrisini_dogrula`'dan geçer | `iha_sender.piksel_rotayi_yerele_cevir` |
| çevrim düşerse | `NO_ROUTE(OLCEK_YOK)` (mpp geçersiz) ya da `NO_ROUTE(ROTA_GEOMETRI)` | `ROTA_GEOMETRI_SEBEBI` |
| `HEARTBEAT` | ayrı iş parçacığı, aralık `IHA_HEARTBEAT_ARALIK_S = 1.0 s` < `IkaReceiver.hb_timeout = 3.0 s` (2 ardışık kayıp bağlantıyı düşürmez) | `karar_sozlesmesi` |
| Kuyruk | **latest-wins** tek yuva: kamera döngüsü ACK beklemez; ACK'li gönderim ayrı iş parçacığındadır; `stop()` bekleyen son kararı gönderip durur | `KararYayinci` |
| Telsiz hatası | kamera döngüsünü düşürmez; `yayinci.hata`'ya yazılır ve çıkışta basılır | |

`KARAR_YOK` ve `ROTA_GEOMETRI` **`ROTA_RET_SEBEPLERI` kümesine girmez** — o küme analiz
katmanının ret sebepleridir (`test_rota_ret_nedenleri` kilitler); bunlar yayın katmanının
fail-closed varsayılanlarıdır.

Doğrulama: `tests/test_rpi_telsiz_yayin.py` (gerçek loopback UDP, `IkaReceiver` ACK'li);
`scripts/saha_kuru_kosu.py` halka 8 artık **üretim yolunu** ölçer (`uretim_yolu_telsiz`).

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
> *(2026-08-26 güncelleme: iniş sinyalini `comms/iha_inis_yayinci.py` üretir —
> `inis_kaniti.yerde_mi` Pixhawk kanıtı; şartname boşluk denetimi K5/K6 raporu.)*

### 7.1 Süre limitleri sözleşmesi (şartname §6.2 / §6.4 · K5+K6 · 2026-08-26)

Sabitler `codes/karar_sozlesmesi.py` sonunda, PDF alıntılarıyla:

| sabit | değer | şartname |
|---|---|---|
| `SARTNAME_IHA_GOREV_SURESI_S` | 900 | §6.2 *"Bu işlemler için tanınan maksimum süre 15 dakikadır."* (fırlatma → paraşütle iniş) |
| `SARTNAME_IKA_GOREV_SURESI_S` | 600 | §6.2 *"İKA'nın HB'ye ulaşması için verilen maksimum süre 10 dakikadır."* |
| `IKA_BEKLEME_SURESI_S` | = İHA süresi | `ika_nav`: rota + IHA_LANDED + IKA_GO beklemesi |
| `IKA_SURUS_SURESI_S` | = İKA süresi | `ika_nav`: izin anından HB'ye |
| `IHA_INIS_HEARTBEAT_SURESI_S` | = İKA süresi | `iha_inis_yayinci` CLI iniş sonrası heartbeat |
| `IHA_INIS_HEARTBEAT_ARALIGI_S` | 0,5 | < `IkaReceiver.hb_timeout` (3 s) |

**Bağlayıcı kurallar:**
1. İKA'da **iki ayrı son tarih** vardır: bekleme ve sürüş. Sürüş saati izin
   geldiği **anda** başlar; beklemede geçen süre sürüşten düşülmez. Tek ortak
   deadline (eski `--timeout 60`) **yasaktır** — sahada iniş dakikalar sonra gelir.
2. Sürüş süresi dolunca İKA `send_vel(0,0)` ile durur, `navigate` False döner
   (çıkış kodu 4). Serbest alan/rota kararına dokunulmaz (madde 15).
3. `IHA_LANDED` yayıncısı iniş sonrası heartbeat'i en az İKA görev süresi kadar
   sürdürür; alıcıdaki `link_lost` **yalnız heartbeat gerçekten kesilince** oluşur.
4. Simülasyon (`navitas_sim.py --route-timeout 60`) bekleme süresini kısa tutabilir;
   sürüş süresi orada da sözleşmeden gelir (`--surus-suresi`).

Testler: `tests/test_k5_k6_sure_limitleri.py` (sahte saat + gerçek UDP loopback;
4 mutasyonla düştüğü gösterildi).
✅ **`IKA_GO` kısmı kapatıldı (K4, §6.6):** ACK'lı, aynı-seq tekrar gönderimi + üst sınırda
görünür hata ve yeniden tetiklenebilir düğme; İKA mükerrer alımı idempotent işler.

### 7.2 İKA sürücü arayüzü (T149 · P3 · D-390 · 2026-09-02)

Motor/konum erişimi `simulation/scripts/ika_surucu.py` arayüzünden geçer;
`ika_nav.send_vel/get_pose` bu arayüze delege eder (imzaları değişmedi).

| üye | sözleşme |
|---|---|
| `hiz_ver(sag, sol) -> bool` | Tekerlek hızları (m/s, DiffDrive uyumu). **False = iletilemedi; istisna SIZMAZ.** |
| `konum_al()` | `(x, y, z, yaw)` ya da `(None, None, None, None)` |
| `durdur() -> bool` | Sıfır hız; arıza sayacına tabidir |
| `saglikli() -> bool` | ardışık hata < `ARDISIK_HATA_TAVANI` (3) |

**Bağlayıcı kurallar:**
1. **Fail-closed:** ardışık `ARDISIK_HATA_TAVANI` arızada `navigate` son bir
   durdurma dener ve **False** döner (eski davranış: subprocess istisnasıyla
   çökmekti). Tavan 3'tür: tek geçici aksama görevi durdurmaz, süreğen arıza
   10 Hz'de ~0,3 s içinde güvenli duruşa çevrilir.
2. **Bayt-eşitlik:** `GazeboSurucu` eski `send_vel`/`get_pose` komut ve
   ayrıştırmasının birebir taşınmasıdır (T141 zinciri değişmez) — kilit:
   `tests/test_p3_ika_surucu.py::T1BaytEsitlik`.
3. `GercekSurucu` arka uçsuz **kurulamaz** (`DONANIM_YOK` istisnası) — Faz
   B'de (5 Eylül) seri/PWM arka ucuyla doldurulacak; sessiz iskelet yasak.
4. §2.2.5 kilidi sürücü yolunun da üstündedir: izinler gelmeden sürücüye
   sıfır-dışı komut düşmez — kilit: `test_p3_ika_surucu.py::T6`.

### 7.3 Varış = brandaya TEMAS (şartname SS7 Pgörev · P9e · D-391 · 2026-09-02)

SS7: görev **"branda üzerine fiziksel temas"** ile biter — sınıra girmek 0
puan. Zincir iki yarımdan oluşur ve ikisi de kilitlidir:

1. **İHA yarısı (T150/D-386, ölçüldü):** rotanın son waypoint'i HB pedinin
   kutusunda biter (253/256; ped görünmezken HEDEF_YOK).
2. **İKA yarısı:** `navigate` son waypoint'te `FINAL_WP_RADIUS` (0,3 m)
   kullanır ve **`FINAL_WP_RADIUS < HB_KENAR_M/2`** (1,0 m) esitsizliği
   bağlayıcıdır: araç merkezi ped kenarından ≥ 0,7 m içeride durur → gövde
   pedin üstündedir. Pay 0,5 m'nin altına indirilecekse önce ped-içi
   waypoint dağılımı ölçülür (D-107).
   Kilit: `tests/test_p9e_branda_temas.py` (geometri + kinematik + mutasyon).

⚠ Gazebo fiziksel temas koşusu bu geliştirme makinesinde ÖLÇÜLEMEZ (gz yok);
Faz C provasında Gazebo'lu makinede koşulacak — `OLCULEMEDI != GECTI`.

### 7.4 MAVLink çoğullayıcı — Jetson'da ZORUNLU (Faz B · D-403 · 2026-09-03)

**Ölçülen olgu:** Pixhawk'ı **iki** üretim süreci ayrı ayrı açıyor
(`codes/rpi_inference.py:314` irtifa okuyucu · `comms/iha_inis_yayinci.py:170`
iniş kanıtı); üçüncüsü `comms/iha_komut_alici.py` (paraşüt/ARM aktarımı, D-393'ün
İHA yarısı). Seri port (`/dev/ttyACM0`) **tek sahiplidir**: ikinci süreç ya
açılamaz ya ilkinin akışını çalar — `inis_kaniti._mav_sahiplen` süreç İÇİ
sahipliği korur, süreçler ARASI koruma yoktur. Kılavuzlarda çoğullayıcı hiç
yoktu (grep: 0).

**Bağlayıcı kural:** Jetson'da seri portu **yalnız çoğullayıcı** açar
(mavlink-router ya da MAVProxy `--out udp:127.0.0.1:1455N`); her tüketici kendi
UDP ucundan bağlanır:

| tüketici | uç | yön |
|---|---|---|
| `rpi_inference --mavlink` | `udp:127.0.0.1:14550` | okur |
| `iha_inis_yayinci --mavlink` | `udp:127.0.0.1:14551` | okur |
| `iha_komut_alici --mavlink` | `udp:127.0.0.1:14552` | **yazar** (`command_long`) |

Hiçbir üretim süreci `--mavlink /dev/tty*` ile DOĞRUDAN açılmaz (kod kilidi:
`iha_komut_alici --mavlink` seri cihazı reddeder; `--seri-pixhawk-bilerek`
ile aşılır). Kapı: `scripts/mavlink_dogrula.py` üç uçta da aynı anda GEÇTİ
(HEARTBEAT sysid, `GLOBAL_POSITION_INT ≥ MAVLINK_KONUM_ASGARI_HZ`,
`EXTENDED_SYS_STATE ≥ MAVLINK_DURUM_ASGARI_HZ` — sabitler `karar_sozlesmesi`).
Plan: `FAZ_B_GUN_PLANI.md` §1.

### 7.5 SiK hub — NAVITAS-çerçeve seri çoğullayıcı (Faz B · D-404 · 2026-09-03)

**Olgu:** SiK (433 MHz) kipinde Jetson'daki üç NAVITAS süreci
(`rpi_inference --telsiz-seri`, `iha_inis_yayinci --serial`,
`iha_komut_alici --serial`) aynı `/dev/ttyUSB0`'ı ister — seri port tek
sahiplidir (§7.4'ün NAVITAS-protokol ikizi). Çözüm `comms/seri_hub.py`:
portu **yalnız hub** açar, tüketiciler kendi UDP kiplerinde kalır
(**tüketici kodu değişmez**).

| yön | davranış |
|---|---|
| tüketici → seri | Tüketici çerçeveyi hub'ın UDP soketine (`--bind`, varsayılan `127.0.0.1:5100`) yollar; hub datagramı olduğu gibi seriye yazar ve göndereni "öğrenilen" kümesine ekler |
| seri → tüketiciler | Hub gelen baytları kalıcı `FrameReader` ile **tam çerçeveye** toparlar; her çerçeveyi `encode(decode(...))` ile tek satır yapıp (statik `--tuketici` listesi ∪ öğrenilenler) adreslerinin **hepsine** yayınlar — datagram = çerçeve (D-403 KÜÇÜK-4 ile uyumlu) |
| yalnız-dinleyen tüketici | `--tuketici HOST:PORT` statik listede olmalı (ör. `iha_komut_alici` 5007) — hiç göndermeden de alsın |
| uzun ömürlü tüketici | **KURAL (D-405):** öğrenilen küme sayı tavanlıdır (`OGRENILEN_TAVANI`, en az tazelenen düşer, KIRMIZI log); uzun ömürlü her tüketici (`rpi_inference`, `iha_inis_yayinci`) **statik `--tuketici` ile de verilir** — öğrenme yalnız emniyettir |
| tek sahiplik | Hub UDP ucunu `SO_REUSEADDR`'sız açar (ikinci hub exit 3); seri port `exclusive=True` (Linux flock; ikinci süreç `SerialException`) — çift başlatma **sessiz olamaz** |
| dayanıklılık | Hiçbir çerçeve hub'ı öldürmez: derin iç içe JSON (`RecursionError`), 4096 B üstü datagram, fan-out `OSError` → sayaç + KIRMIZI log, süreç yaşar; `SIGTERM` → `durdur()` (son sayaç satırı journal'a düşer) |
| zamanlama | `SERI_OKUMA_ZAMAN_ASIMI_S ≤ 0,05`, `UDP_OKUMA_ZAMAN_ASIMI_S ≤ 0,01` testle kilitli; UDP→seri p95 < `PARASUT_TEKRAR_ARALIGI_S` (ölçüldü: boşta p50 10,6 / p95 31 ms; 20 Hz seri girişiyle p50 45 ms — Windows) |
| seri arızası | Seri kapatılır, KIRMIZI log, 1 s'de bir yeniden açma; UDP tarafı YAŞAR; arızada UDP'den gelen çerçeveler **düşürülür ve sayılır** (kuyruklanmaz — bayat rota yayınlanmasın) |

**Topoloji (SiK kipi, Jetson — `jetson_baslat.sh KIP=sik` ile AYNI, test K2
kilitler):** `seri_hub --port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici
127.0.0.1:5007` · `rpi_inference --yks-hedef 127.0.0.1:5100` · `iha_inis_yayinci
--yks 127.0.0.1:5100` · `iha_komut_alici --bind 127.0.0.1:5007`. **Tek hatta
bir kez:** SiK hattında hedef YKS'dir; `--ika-hedef`/`--ika` hub'a VERİLMEZ
(ölçüldü, D-405: İKA ACK'i SiK'ten hiç gelmediği için `IhaSender` 8 tekrar /
2,11 s boşa tekrar ediyordu). İKA'nın hattı (SiK çok-noktalı mı, WiFi
`--ika-hedef <IKA_IP>:5006` mi) **topolojiyle karara bağlanır** (cumartesi).
ACK'ler §6.6'daki "ortam yayını" semantiğini korur: YKS'nin ACK'i seriden
gelir, hub öğrenilen/statik tüketicilere yayınlar; her tüketici yalnız kendi
`ref`'ini eşler. UDP kipinde (WiFi) hub **kullanılmaz**; süreçler doğrudan
YKS/İKA adresine konuşur. Kilit: `tests/test_faz_b_seri_hub.py` (uçtan uca:
YKS-seri → hub → gerçek `IhaKomutAlici` → ACK → seri).

---

## 8. Çözünürlük sözleşmesi

> **Çıkarım `imgsz` = `config/model_registry.json → profiles.competition.imgsz`
> (bugün **512**). Bu dosyada ÇIPLAK SAYI YAZILMAZ — kilit:
> `tests/test_t163_cozunurluk_sozlesmesi.py`.**

🔴 **BU BÖLÜM 2026-08-27'DE DÜZELTİLDİ (T163 · D-308).** Önceki hâli kalın harflerle
**"`imgsz` = 640; değiştirmek güvenli DEĞİLDİR"** diyordu — oysa üretim **v27'den beri
512**'de koşuyordu. Yani sözleşme **kendi üretimini yasaklıyordu**; sahadaki bir kişi bu
satırı okuyup 640'a çevirseydi **kabul edilmemiş** bir çözünürlükte koşacaktı. Bayatlık
JETSON kılavuzunda T154/T157/T158 kapılarıyla kapatılmıştı; **bu dosyaya bakan kapı yoktu**,
artık var.

### 8.1 Bugünkü ölçüm (v36, kabul kümesinden 12 kare, ön kayıt §29)

Ölçek her koşumda manifestten (kare başına); karar üretim zincirinin kendisi.
Kanıt: `results/t163/{olcum.json,olc.py}`.

| imgsz | sınıf 0 IoU (medyan) | kaplama (medyan / azami) | ROTA | doğru şerit |
|---|---:|---:|---:|---:|
| **512 (ÜRETİM)** | **0,9063** | 0,309 / 0,609 | **12/12** | **8/12** |
| 640 | 0,8903 | 0,296 / 0,573 | 11/12 | 7/12 |
| 768 | 0,9099 | 0,263 / 0,602 | 9/12 | 6/12 |
| 960 | 0,8890 | 0,280 / 0,566 | 9/12 | 6/12 |
| 1280 | 0,7422 | 0,222 / 0,364 | 3/12 | 2/12 |

**Hüküm (ön kayıtlı kural, sonuca göre değiştirilmedi):** 512 hem **ROTA** hem **doğru
şerit** ekseninde en yüksek; IoU'da en iyi 768'dir ama fark **+0,0036** ve ön kayıttaki
**±0,02 beraberlik bandının** içindedir. Dolayısıyla **512 tazelenerek yazıldı**; üretim
`imgsz` **DEĞİŞTİRİLMEDİ**.

### 8.2 v17 dönemi ölçümü — TARİHSEL, SİLİNMEDİ

| imgsz | IoU | kaplama |
|---|---|---|
| **640** | **0,861** | %4,2 (yer gerçeği %3,6) |
| 960 | 0,034 | **%96,1** — her yeri boyuyor |
| 1280 | 0,041 | %79,7 |
| 1600 | 0,018 | %65,2 |

`multi_scale` eğitimi (v20) bunu **düzeltmedi** (%96,1 → %90,7).

⚠ **v17'nin "her yeri boyuyor" çöküşü v36'da TEKRARLANMIYOR:** 8.1'de hiçbir
çözünürlükte kaplama %90'ı geçmedi (azami %61). Yani o tarihsel risk **modele
özgüydü**; bugünkü risk farklıdır ve **büyük çözünürlükte kararın çökmesidir**
(1280'de ROTA 12/12 → 3/12). FDA irtifası ≥30 m ve **değişken** olduğu için
çözünürlüğü keyfî büyütmek hâlâ **saha riskidir** — ama gerekçe artık ölçülmüş
olan budur, 2026-08 öncesinin gerekçesi değil.

⚠ **AÇIK GÖZLEM (hüküm değil):** üretim çözünürlüğünde bile **doğru şerit 8/12**.
T155 aynı ölçütü yer gerçekli 15 sahnede **15/15** ölçmüştü; bu iki küme aynı
değildir (orası `results/t151` sahneleri, burası kabul kümesi val). Fark
**ölçülmedi**, uydurulmuş bir açıklama da yazılmadı — ayrı iş.

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

> 🔄 **TAZELENDİ 2026-08-26 (saha zinciri tazeleme koşusu).** Her satır o günün **ÖLÇÜLEN** kuru koşusundan
> gelir; elle tahmin yazılmaz. Ölçüm: `scripts/saha_kuru_kosu.py`, ham çıktı
> `results/saha_zinciri_20260826/kuru_kosu_cpu.txt`, makine özeti
> `results/saha_zinciri_20260826/kosu_cpu/ozet.json`, çözümleme
> `results/saha_zinciri_20260826/rapor.md`.
> Koşum ortamı: PC, **GPU KAPALI** (`CUDA_VISIBLE_DEVICES=-1`; `torch.cuda.is_available()`
> `False`, `nvidia-smi` 0 % — PC aynı gün BSOD verdiği için, `results/pc_cokme_20260826/`).
> Kare: `data/raw_frames/whatsapp_video_2026_07_30_at_11_44_03/frame_000000_000000000.jpg`
> (576×1024). Sayım: **GEÇTİ 7 · DÜŞTÜ 1 · SAHİPSİZ 2 · ATLANDI 0.**

| # | Halka | Girdi | Çıktı | Sahip `dosya:satır` | Durum | Kanıt |
|---|---|---|---|---|---|---|
| 1 | Kamera kaynağı | cihaz/URL | BGR kare | `codes/rpi_inference.py:2114` (`run_camera`) + `--kaynak` argümanı | **GEÇTİ** (eski **KUSURLU** · D-13 — `VideoCapture(0)` sabiti kalktı; cihaz yolu `str`, indeks `int` olarak çözülüp `VideoCapture`'a **beslendiği** ölçüldü) | `kosu_cpu/ozet.json` `kamera.detay.besleme_*` |
| 2 | Model yükleme | model yolu | YOLO nesnesi | `codes/rpi_inference.py:684` (`load_model`) → `codes/model_registry.py` | **GEÇTİ** (eski **KUSURLU** · D-13 — `best_ncnn_model` sabiti kalktı; yüklenen `navitas_seg_v36_best.pt`, kayıt defteriyle **eşleşti**, uyuşmazlıkta fail-closed) | `ozet.json` `model_yukleme.detay`; D-294 (v36 terfisi) |
| 3 | Çıkarım | BGR kare | `results` | `codes/rpi_inference.py:2143` (`run_camera` içindeki `model.predict`) | **GEÇTİ** (1621 ms; CPU'da, `imgsz=512`, tuval 1024×1024) | `ozet.json` `cikarim` |
| 4 | Maske çıkarımı | `results` | `{0: zemin, 1: engel}` | `codes/rpi_inference.py:727` (`get_masks`) | **GEÇTİ** (`{0,1}`; piksel oranı 0:0,1947 · 1:0,2123) | `ozet.json` `maske` |
| 5 | Ölçek (`mpp`) | irtifa + FOV/odak | m/piksel | `codes/rpi_inference.py:281` (`CanliOlcekSaglayici`) ← `comms/inis_kaniti.py` `BagilIrtifaOkuyucu` · sözleşme `codes/karar_sozlesmesi.py` (`mpp_irtifadan`, `rota_olcek_reddi`) | **GEÇTİ** — canlı telemetri **enjekte edilmiş sahte yayından gerçekten geçirilerek** `mpp=0,0338` üretildi. ⚠ **Gerçek Pixhawk üzerinde ÖLÇÜLMEDİ**; telemetri gelmezse her kare `OLCEK_YOK` → NO_ROUTE (fail-closed, T43) | `ozet.json` `olcek.detay` |
| 6 | Hedef konumu (HB) | kare / dış girdi | `hb_xy` | **SAHİPSİZ** — dedektör (`codes/karar_sozlesmesi.py` `hb_maskesi`/`hb_konumu`) VAR ama **üretim çağrısı yok**: `analyze_path`'in üretim çağrılarının hiçbiri `goruntu=` geçmiyor; `--hb` CLI yok; etkin profil 2 sınıflı | **SAHİPSİZ** · D-22, D-23 · **T150** | `ozet.json` `hedef_konumu.detay`; D-295 §2: HB dedektörü gerçek pedde **%0**, kırmızı arabada %100 → bağlanması **ölçüme bağlı**, insan kararı |
| 7 | Rota üretimi | maskeler + `mpp` + `hb_xy` | `road`, `waypoints`, `durum` | 🔴 **ÜRETİM: `codes/rpi_inference.py:1335` (`analyze_path`)** — §11.2-EK/D-295. `codes/costmap_path_finder.py:985` (`rota_bul`) **TANISALDIR** | ✅ **GEÇTİ** (`yol_no=2`, T38/D-301: kuru koşu artık kabul dağılımından kare + O KARENİN ölçeğiyle koşuyor; otopark karesi `--kare` ile negatif kontrol olarak DÜŞÜYOR) — ✅ **T160 KAPANDI (2026-08-27, D-298 §5b):** halkanın HÜKMÜ artık ÜRETİM yolundan gelir (`analyze_path` + yapısal-ret önceliği + `_rota_kararini_esikle`, `run_camera` birebir sırası); `rota_bul` sonucu `detay.tanisal_rota_bul` altında **tanısal** olarak durur ve hükmü **çeviremez** (iki yönlü mutasyon: `tests/test_saha_kuru_kosu_uretim_yolu.py` 8/8). Halka hâlâ DÜŞÜYOR — hüküm sonuca göre gevşetilmedi; sebep artık üretimin **kendi** sebebi | `ozet.json` `rota.detay` (`rota_bul_cagrildi: true`); D-296 (`road` 6/15 → 15/15 düzeltildi) |
| 8 | Aktarım | rota | OPEN_ROUTE/NO_ROUTE + ACK + HEARTBEAT | `codes/rpi_inference.py:2114` (`run_camera`) → `comms/iha_sender.py:198` (`KararYayinci`), §6.5 · K1 | **GEÇTİ** — üretim algı yolunun telsize yazdığı **ayrıca** ölçüldü: `open_route_alindi=True, heartbeat=1, ack=['ika'], hata=None`. ⚠ **SiK seri hattı ÖLÇÜLMEDİ** (yalnız UDP loopback) | `ozet.json` `aktarim.detay.uretim_yolu_telsiz`; T146, D-287 §2 |
| 9 | İKA sürüş izni | rota ∧ IKA_GO ∧ IHA_LANDED | izin `bool` | kapı: `comms/ika_receiver.py:127` (`_surus_izni_gecerli_unlocked`) · `IHA_LANDED` **saha üreticisi**: `comms/iha_inis_yayinci.py:35` (← `comms/inis_kaniti.py` Pixhawk kanıtı) | **GEÇTİ** (eski **KUSURLU** · D-22 — üretici artık `simulation/` altında **değil**; kapı probu: boş kapalı, yalnız IKA_GO kapalı, iki latch ile açık) | `ozet.json` `surus_izni.detay.kapi_probu`; T147/T148, §6.6 |
| 10 | Motor komutu | izin + waypoint | tekerlek hızı | **SAHİPSİZ** — `simulation/scripts/ika_nav.py:97` (`send_vel` = `gz topic` subprocess); `codes/ comms/ drone/ jetson_paket/ scripts/` altında saha sürücü importu **0** | **SAHİPSİZ** · D-22 · **T149** (insan+mimar, donanım) | `ozet.json` `motor.detay.saha_surucu_importlari: []` |

**Kuru koşunun kendi bayat etiketleri (2026-08-26'da ölçüldü, kod bugün DEĞİŞMEDİ):**
`scripts/saha_kuru_kosu.py` halka 3'ü `codes/rpi_inference.py:57`, halka 4'ü `:60-83`
diye etiketliyor; ikisi de bugün **import bloğunun içine** düşüyor (gerçek sahipler
`:2143` ve `:727`). Etiket bayat, **ölçüm değil** — ama sözleşmede doğru satır yukarıdadır.
Düzeltme **açık kusurdur** (`REVIEW_LOG.md` D-297 §2); numaralı görevi mimar açar.

#### 11.2-EK · KARAR YOLU BEYANI — T151 kararı (mimar vekili, 2026-08-26 · D-295)

> Halka 7'nin sahibi **`codes/rpi_inference.py::analyze_path`**tır (`run_camera` → K1 telsiz
> halkası → `iha_sender.KararYayinci`). `costmap_path_finder::rota_bul` **üretim değildir**;
> saha gününde yalnız **TANISAL** koşar (`kamera_dogrula`, `jetson_fps`) ve PC'de kuru koşuda.
> Bu satır fiilî durumu **beyan eder** — davranış değiştirilmedi (Seçenek C).
>
> 🔴 Bu beyanın ortaya çıkardığı iki boşluk **açık görevdir**, gizlenmez:
> 1. ~~**Genel kapı (15/15, madde 14) yalnız `rota_bul`u zorluyor.**~~ → **T156 KAPANDI**
>    (2026-08-26, aşağıdaki "Genel kapının kapsamı" bloğu).
> 2. **`koridor_adaylari` üç-güzergâh kapısı üretim yolunda YOKTUR**; `rota_dogrula`nın K2/K3
>    ihlal denetimi ve T90 etiket-çakışması fail-closed'ı da yalnız `rota_bul`dadır → **T155/T156**.
>    (T156 üretim yolunun **kararını** kapıya soktu; K2/K3 ihlal denetiminin üretim yoluna
>    taşınması **hâlâ açıktır** — bu boşluk kapanmadı.)
>
> ##### Genel kapının kapsamı — madde 14 (T156 · 2026-08-26)
>
> **Anayasa madde 14'ün genel kapısı `codes/test_rota_sentetik.py` artık İKİ KOL koşar.**
> Aynı 15 belirlenimci arena sahnesi (`simulation/scripts/arena.py` → `sahne_uret`,
> kusursuz maske), iki karar yolu:
>
> | kol | çağrılan | şart | kaynak |
> |---|---|---|---|
> | **KOL 1** (tanısal) | `costmap_path_finder.rota_bul` | **15/15 tam puan** (değişmedi) | madde 14 |
> | **KOL 2** (**ÜRETİM**) | `rpi_inference.analyze_path` | (a) rota **üretiliyor** (ret yok, karar var, ≥ 2 waypoint) **ve** (b) **yayınlanan** `road` yer gerçeğiyle uyuşuyor — her ikisi de **≥ 14/15** | ÖN KAYIT §18-B |
>
> - Eşik tek yerde tanımlıdır: `test_rota_sentetik.URETIM_KAPI_ESIGI` (madde 16 — çıplak sayı yok).
>   Ölçülen taban **15/15 · 15/15** (`results/t156/rapor.md`).
> - **Çıkış kodu** `test_rota_sentetik.kapi_karari()` ile tek yerden döner ve **iki kola da**
>   bağlıdır. `SONUC: 15/15 dogru` satırı ve `[OK] TUM DETERMINISTIK SAHNELER GECTI` cümlesi
>   **KOL 1'in çıktısı olarak aynen durur** — dış okuyucuların sözleşmesi bozulmadı.
> - Kilit: `tests/test_t156_genel_kapi_uretim_kolu.py` (değer + çıkış kodu sözleşmesi +
>   mutasyon muhafızı). Mutasyon ölçüldü: yayın hattı `serit_karari` → `darbogaz_serit`
>   çevrilince KOL 2 **6/15**'e düşer ve kapı DÜŞER, KOL 1 ise **15/15 yeşil kalır** —
>   yani T155'in girdiği delik artık kapıdadır.
>
> `rota_bul`un ret sözlüğü (`BELIRSIZ_TEK_KAPI`, `KAPALI_DAR`, …) `ROTA_RET_SEBEPLERI`de
> **yoktur** (§6.4, `tests/test_rota_ret_nedenleri.py` kilitli): üretimi `rota_bul`a çevirmek
> sözlük genişletmesi ya da eşleme katmanı gerektirir — bu yüzden Seçenek B seçilmedi.

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
sabit (`:44`). Üretimde olması gereken **v24**'tür (T58, 2026-08-13; önceki v21).
Ayrıca `config/model_registry.json`
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
| `model_yukleme` | KUSURLU | v24 (T58 üretim modeli) yerine v2 dönemi NCNN |
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

---

## 12. DOĞRULAMA kümesi ve gerçek-kare kapısı (kullanıcı kararı 2026-08-26 · D-292)

> **Neden var:** T111/D-198'den beri her kabul ölçümü eğitim dağılımının içindeydi ve "alan
> dışı doğrulama DJI çekimi olmadan kapanmaz" deniyordu. Kullanıcı 2026-08-26'da mevcut
> karelerden bir DOĞRULAMA kümesi ayrılmasını kabul etti.

**Küme:** `dji/DOGRULAMA/` = **DJI_20260822172613_0038_D** (sabit bağlantı; `KAYNAK.md`).
0037/0039 ile GPS örtüşmesi 0 m² / %1,5 (alan ayrık); hiçbir eğitim kararına girmez —
`dataset/dji_kirsal_0038_bolum_v3/{test,val}` (29 + 82 kare, iki bağımsız **kör** etiket
geçişinin uzlaşısı: sınıf 0 = A∧B, sınıf 1 = A∨B; D-289). ⚠ **Sınır (bilerek kabul edildi):**
aynı gün, aynı kamera, aynı saha türü (kırsal), **arena değil** — "alan dışı" sorusunu
**kısmen** kapatır; arena benzeri saha + kırmızı H çekimi hâlâ ayrı bir insan görevidir.

**Bağlayıcı kural:** 0038 kareleri (test **ve** val) **eğitime ve erken durdurmaya girmez**
(ON_KAYIT §2'deki "val erken durdurmada" istisnası bu maddeyle **kalkar**); ölçek/etiket
düzeltmeleri yalnız **model çıktısı görülmeden** (kör) yapılır.

**Gerçek-kare kapısı** (`scripts/olcum/142_gece_olcum.py --test-dizin … --etiket-dizin … --tavan …`,
üretim yolu `126`/`analyze_path`): her aday için test29 **ve** val82 ayrı raporlanır; terfi
için ON_KAYIT §4(b), §4(b-ek) ve §11(2) ölçütleri (ROTA ≥ 10/29, MASKE_YOK ≤ 10/29, FP ≤ 1,
**YANLIŞ GÜZERGÂH = 0**: rota çizgisinin sınıf 0 payı ≥ 0,90 ∧ sınıf 1 üstünde 0 waypoint —
tanım `rota_yol_olcumu.py`, sentetik eşdeğeri K6 ≤ %5). Sentetik kabul zinciri (§10, K0–**K7**)
**bu kapıyı ikame etmez**: sentetik arena kanal/çim/tarla içermez (D-290).

### 12.1 K7 · YAYINLANAN ŞERİT DOĞRULUĞU (2026-08-27 · D-314 · ON_KAYIT §34)

Şartname §2.1/§5.3.2 **yanlış güzergâha 0 puan** verir ve hakem **numarayı** canlı
onaylar (§2.2.3). K1 rota **üretimini**, K6 rotanın **yol üstünde** olmasını ölçer —
**numarayı hiçbiri ölçmüyordu**. K7 bu boşluğu kapatır.

**🔴 Ölçüm YALNIZ dondurulmuş bir alt kümede yapılır** (`config/k7_iyi_kosullu_kume.json`,
**88 kare**). Sebep: şerit numarası içerik genişliğinin **üçte birlerinden** hesaplanır
(`karar_sozlesmesi.serit_no`); koridor kapısı bir sınıra denk geldiğinde etiket **tanım
gereği** belirsizdir (**T101**). Ölçüldü (D-312): kabul kümesinin **%54'ü (105/193)** böyle
ve şerit ayrışmasının **%100'ü** oradan geliyor. Dondurulmuş alt kümede manifest ile koridor
envanteri **%100** uyuşur — yani referans **kesindir**. Kötü koşullu 105 ve `acik_serit`
beyansız 49 kare **dışlanır**; aksi hâlde kapı, tanım gereği belirsiz olan bir şeyi
ölçüyormuş gibi yapar (D-15 sınıfı vakum kapı).

| alan | değer |
|---|---|
| ölçüt | yayınlanan `road` == referans şerit |
| payda | alt kümede **rota üretilen** kare (üretilememe **şerit hatası değildir**, onu K1 ölçer) |
| eşik 1 | doğruluk **≥ %95** |
| eşik 2 (**payda oyunu yasağı**) | rota üretilen **≥ 80/88** |
| ölçülen taban (v36) | doğruluk **84/85 = %98,8** · rota üretilen **85/88** → **GEÇTİ** |
| üretici | `scripts/olcum/151_k7_serit_dogrulugu.py` |
| kapı | `65_kabul_denetcisi.k7_durumu` · `tests/test_k7_serit_dogrulugu.py` (18) |

🔴 **REFERANSIN SEMANTİĞİ — bir K7 düşüşü "model yanlış gördü" diye OKUNAMAZ.**
Referans, kümenin YOLO etiketinden rasterlenen maskeyle üretilir ve **etiketsiz alan
GEÇİLEMEZ** sayılır (üçüncü durum yok). Sonucu: bir şeridin **yüzeyi etiketlenmemişse**
o şerit referansta **kapalı** görünür. Ölçüldü (D-315, `sa_000090`): model şerit 3'te
**89.913 px** serbest görürken yer gerçeği **18.042 px** görüyor; **engel** pikselleri
ise neredeyse **aynı** (42.123 ↔ 43.781). Yani fark bariyeri kaçırmak **değil**, etiket
**kapsamı**dır. K7 düşerse **önce etiket kapsamı denetlenir**.

⚠ **K7 bu turda VERDİKT'e bağlanmadı** — ölçüt ve testleri kuruldu, zincire bağlamak terfi
yordamını etkiler ve ayrı bir karardır (D-133). ⚠ Alt küme listesi **kanonik özetle kilitli**;
değişirse test düşer ve değişiklik ön kayıtla gerekçelendirilmek zorundadır.

**Ölçülmüş taban (2026-08-27, referans v3):** v35 test29 ROTA 6 · TP 5 · FP 1 · YANLIŞ 5/6;
val82 ROTA 15 · YANLIŞ 10 (D-289/D-290). Üretim modeli bu kapıyı **geçmiyor** — kullanıcı
kararıyla üretimde kalır; kapı **gelecek terfileri** bağlar.

> 🔴 **İSTİSNA (2026-08-26):** **v36 terfisi ROTA/MASKE_YOK eşiklerini geçmeden kullanıcı
> kararıyla yapıldı; eşikler DEĞİŞMEDİ, sonraki terfileri bağlar.**
> Ölçülen: v36 (koşum `gece_v7a_v35taban`) test29 ROTA **8** (eşik ≥ 10) · MASKE_YOK **16**
> (eşik ≤ 10) · TP 7 · FP 1 (eşik ≤ 1 ✔) · YANLIŞ GÜZERGÂH **0** (eşik = 0 ✔); val82 ROTA 30 ·
> TP 28 · FP 2 · YANLIŞ 7. Karar dayanağı `REVIEW_LOG.md` **D-293**, ön kayıt
> `results/gece_20260826/ON_KAYIT.md` §15 ("izin veriyorum kurala rağmen"), üç lensli çürütücü
> `results/gece_20260826/v7a_curut/` (terfi engeli bulunmadı).
> ⚠ Bu satır bir **muafiyet değil, bir kayıttır**: eşikler gevşetilmedi, yeniden yazılmadı ve
> bir sonraki aday yine ROTA ≥ 10 ∧ MASKE_YOK ≤ 10 ∧ FP ≤ 1 ∧ YANLIŞ = 0 ile ölçülür. Eşiği
> geçmeyen bir adayın üretime alınması **ancak insanın açık kararıyla** olur (D-133) ve her
> defasında buraya yazılır.
