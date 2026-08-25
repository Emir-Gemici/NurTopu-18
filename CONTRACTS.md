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

### 6.5 ACK bağlama ve `IKA_GO` tekrar sözleşmesi — bağlayıcı (K4+K8, şartname §2.2.5 / §2.2.3)

**Gerekçe (ölçüldü, `results/sartname_bosluk/rapor.md` K4/K8):** `IKA_GO` tek paketti,
ACK beklenmiyordu, düğme kilitleniyordu — tek paket kaybı görevi geri dönülmez bitiriyordu
(`REVIEW_LOG` D-02). YKS, İKA'nın `ACK`'ını hiç işlemiyordu; hakem "İKA'ya aktarıldı" onayını
ekranda kanıt görmeden veriyordu.

- **`ACK.ref_tip` (isteğe bağlı alan):** onaylanan mesajın `type`'ı (`"OPEN_ROUTE"`, `"NO_ROUTE"`,
  `"CMD"`, `"IHA_LANDED"`). NEDEN: `seq` sayaçları **düğüm başınadır**; YKS'nin `IKA_GO` seq'i ile
  İHA'nın `OPEN_ROUTE` seq'i çakışabilir. Alıcı, `ref_tip` varsa `ref` **ve** tiple eşler; yoksa
  yalnız `ref` ile (geriye uyumlu — eski ACK'lar reddedilmez). Üretici: `protocol.ack(ref, node, ref_tip)`.
- **`IKA_GO` tekrar gönderimi (YKS):** aynı `seq` ile, `IKA_GO_TEKRAR_ARALIGI_S` aralıkla, en çok
  `IKA_GO_TEKRAR_UST_SINIRI` kez (`codes/karar_sozlesmesi.py`, gerekçeli). İKA'dan `ACK(ref=seq,
  ref_tip="CMD")` gelince durur. Üst sınır aşılırsa ekranda **KIRMIZI "İKA ONAY VERMEDİ"**, düğme
  yeniden aktif, İKA kronometresi başlamamış sayılır — **görev kaybedilmez**. Durum makinesi
  `comms/komut_tekrar.py` (Tk'dan bağımsız).
- **İKA idempotentliği:** mükerrer `IKA_GO` latch'i yeniden kurmaz (`ika_go_monotonic` ilk alımda
  sabitlenir) ama **her alım ACK'lanır** — YKS'nin tekrarı ancak böyle durur.
- **Aktarım kanıtı (K8):** İKA, `OPEN_ROUTE`/`NO_ROUTE` ACK'ını gönderene (İHA) **ve** bildiği YKS
  adresine (`--yks` ya da ilk geçerli `IKA_GO`'nun kaynağı) gönderir. Seri (SiK) hatta ortam yayın
  olduğundan kopya gerekmez. YKS hakem düğmesi **fail-closed**: geçerli rota `seq`'i için İKA'dan
  `ACK(ref_tip="OPEN_ROUTE")` ekranda görünmeden 2. onay ("İKA'ya aktarıldı") **verilemez**; düğme
  pasif, gerekçe metni görünür; kanıt gelince düğme açılır ve zaman damgası yazılır.
  ⚠ UDP kurulumunda İKA `--yks host:port` ile başlatılmazsa kanıt YKS'ye ulaşmaz ve 2. onay
  **hiç açılmaz** — bu bilinçli bir seçimdir (kanıtsız onay yerine görünür ret).
- Kilit: `tests/test_ika_go_ackli_tekrar.py` (paket düşürme gerçek UDP loopback, ACK yok → üst
  sınır, mükerrer IKA_GO, kanıtsız düğme pasif; 5 mutasyonun tamamı yakalandı).

### 6.2 `road` sözleşmesi

`{1: "sol", 2: "orta", 3: "sag"}` — `open_route()` bu aralık dışında `ValueError` fırlatır.
Rota yoksa `NO_ROUTE` gönderilir; `open_route`'a `None` geçilmez.

**`road` HANGİ İSTATİSTİKTİR** (T96 · `REVIEW_LOG.md` D-167/D-168 · olgu beyanı):

    road = olcum["darbogaz_serit"]        # rpi_inference.py:1255
         = rotanın EN DAR geçtiği noktanın `serit_no()` şeridi

`baskin_serit` (en çok rota pikseli taşıyan şerit) **hesaplanır ama yayınlanmaz**.
Bu bir eksiklik değildir: ölçüldü (n=209, yer gerçekli sentetik küme),
`darbogaz_serit` `baskin_serit`i ayrıştıkları 2 karenin **2'sinde de** yeniyor.

⚠ **"En iyi istatistik budur" DİYE OKUNMAMALIDIR.** Üç aday ölçüldü —
`darbogaz_serit` 198/209 · `cikis_serit` 197 · `baskin_serit` 196 — ama farkı
belirleyen 11 karenin **yer gerçeği kırılgandır**: o karelerde açık şeridin
merkezi `serit_no` sınırına medyan **4,6 px** uzaklıktadır (şerit genişliği
109-210 px; doğru çıkan 191 karede pay 45,7 px). Yani sıralama bu kümede
**karara bağlanamaz**; yayınlanan istatistik `darbogaz_serit`tir çünkü
**öyle yazılmıştır** (D-41), daha iyi olduğu **gösterilmemiştir**.

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
✅ **`IKA_GO` kısmı kapatıldı (K4, §6.5):** ACK'lı, aynı-seq tekrar gönderimi + üst sınırda
görünür hata ve yeniden tetiklenebilir düğme; İKA mükerrer alımı idempotent işler.

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
| 5 | Ölçek (`mpp`) | irtifa + FOV/odak | m/piksel | `codes/karar_sozlesmesi.py` — `mpp_irtifadan`, `rota_olcek_reddi` | **GEÇERLİ** · T43 |
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
