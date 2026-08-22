# JETSON ORIN NX — SAHA KILAVUZU

> Hazırlanma: 2026-08-05 · **ASIL MODEL: v35** (2026-08-21, D-249/D-255 · kullanıcı kararı; T130) · eskiler: v34 → v30 → v27 → v24 → v21 → v17/v20
>
> ⚠ **v34 SİLİNMEDİ — YEDEK adaydır** (T123). Farklı hata yapar: arena K2'de daha iyi (%4,65 vs %7,03) ve karar kararlılığında daha iyi (4/260 vs 9/260), ama gerçek karelerin 67/67'sini reddeder ve çatının %96'sını kaçırır (v35: %4,3). Saha gününde geçiş için **§6C** yordamı kullanılır.
> Paket: `O:\navitas\jetson_paket\`
>
> Bu kılavuz **ölçümle** hazırlandı. Her "şu olacak" cümlesinin altında ya bir sayı
> ya da açık bir *bilinmiyor* etiketi vardır.

---

## 0-T85. GÜNCELLEME 2026-08-15 — **asıl model v27 → v30** (çözünürlük 512, değişmedi)

> **Kullanıcı kararı** (T85). Mimar kabulü: `REVIEW_LOG.md` **D-132** (kabul kuralı,
> **sonuç görülmeden** yazıldı) + **D-133** (dört şartın hepsi sağlandı). Aşağıdaki
> v27/v24/v21/v17 bölümleri **silinmedi** — ölçüm kaydıdır. Ama **bugün derlenecek
> ve koşulacak model `navitas_seg_v35_best_512_fp16.onnx`**'tir.
>
> **v30 nedir:** v29 ile her şeyde aynı; tek fark gerçek otopark karelerinin
> çoğaltması **12 kat → 4 kat** (D-132). v29 tam bu dozdan reddedilmişti (D-131).
>
> | ölçüt | eşik | v27 | v30 |
> |---|---|---|---|
> | rota üretimi | ≥ 230 | 255/260 | **258/260** |
> | moloza basma | ≤ %15 | %7,06 | %8,53 |
> | ağır basma | ≤ %3 | %0,0 | **%0,0** |
> | arena dışı | ≤ %5 | %0,4 | %0,39 |
> | bariyer kesişimi | 0 px | 0 px | **0 px** (0/173 kare) |
> | körlük (K0) | körlük yok | %7,8 | %8,0 |
>
> ⚠ **Ağırlık `best.pt` (epoch 200/200).** Bu koşuda en iyi epoch **sonuncudur**.
> `best.pt` ile `last.pt` bayt-eş **değildir** (ayrı seri hale) ama **537/537
> ağırlık tensörü eşittir** — T85'te ölçüldü. D-113 kusuru **tekrarlamadı**;
> koşu grafikleri bu ağırlığı anlatır.
>
> 🔴 **KARAR KARARLILIĞINDA GERİLEME VAR.** v30'un karar çevrilmesi **8/260
> (%3,08)**; v28 **3/260 (%1,15)** ile **üç kat** daha kararlıydı (D-133/D-134).
> D-132 bu ölçütü taşımadı; mimar eksiği kendi kaydetti ve **sonucu gördükten
> sonra kurala eklemedi**. Sahada bunun anlamı: video akışında rota koridor
> değiştirebilir; İKA tek kare değil **akış** izler.
>
> 🔴 **"Gerçek karelerde 65/67 geçti" bir başarı olarak sunulmuyor** (D-133/D-134):
> v30'un gerçek karelerdeki zemin kaplaması **0,594**, etiketler **0,813** diyor —
> 22 puan az zemin. Kapıyı geçme sebebi doğru görmek değil **az zemin görmek**
> olabilir; otoparkta hangisinin (model mi etiket mi) gerçeğe yakın olduğu
> **ölçülemedi**.
>
> ⚠ **Mimar D-134'te "üretim modeli v28 kalır" önerisini yazdı.** İki kabul
> edilebilir model arasındaki sevk kararı ön-kayıtlarda çözülmez ve **insana
> aittir** (D-133); kullanıcı **v30**'u seçti. Bu satır, kararın hangi kanıta
> rağmen verildiğini sahadaki kişinin de görmesi için duruyor.
>
> 🔴 **Bu "sahada çalışır" demek DEĞİLDİR** (D-88/D-99, kalıcı kısıt). Arena
> ölçümlerinin tamamı **sentetiktir**; elimizde tek bir gerçek arena karesi yoktur.
>
> ⚠ **Sürüm adının TEK KAYNAĞI `config/model_registry.json`'dur** (§0-T76'da
> kurulan desen). Hakem ekranı adı oradan okur; bu kılavuz, paket manifesti ve
> saha kodu onunla **testle** kilitlidir (`tests/test_uretim_modeli_hizasi.py`,
> `tests/test_saha_parametrik.py`).

---

## 0-T76. GÜNCELLEME 2026-08-14 — **asıl model v24 → v27, çözünürlük 640 → 512** *(§0-T85 ile AŞILDI)*

> Mimar kabulü (`REVIEW_LOG.md` D-115) + kullanıcı emri T76. Aşağıdaki v24/v21/v17
> bölümleri **silinmedi** — ölçüm kaydıdır. Ama **bugün derlenecek ve koşulacak
> model `navitas_seg_v27_best_512_fp16.onnx`**'tir.
>
> **Neden v27** (T66 ada kadrajı, n=260; eşikler D-107'de **sonuç görülmeden**
> yazıldı, ölçüm D-115):
>
> | ölçüt | eşik | v24 | v27 |
> |---|---|---|---|
> | rota üretimi | ≥ 230 | 196 | **255/260** |
> | moloza basma | ≤ %15 | %31,1 | **%7,1** |
> | ağır basma | ≤ %3 | %20,4 | **%0,0** |
> | arena dışı | ≤ %5 | %13,3 | **%0,4** |
> | bariyer kesişimi | 0 px | 0 px | **0 px** |
>
> **Çözünürlük 640 → 512** (D-112): 640'ın ölçülebilir doğruluk üstünlüğü **yok**,
> Jetson maliyeti **var** (640²/512² = **1,56 kat** hesap). Üretim (`INFER_SIZE`)
> zaten 512'de koşuyordu; T76'dan beri export da 512 — uyuşmazlık kapandı.
>
> ⚠ **Ağırlık `last.pt` (epoch 200), `best.pt` DEĞİL** (D-113): `best.pt` epoch
> 43'te dondu ve **%21,5 daha kötü**. Koşu grafikleri (`results.png`, karışıklık
> matrisi) `best.pt`'ye aittir — **bu modeli anlatmazlar**.
>
> 🔴 **Bu "sahada çalışır" demek DEĞİLDİR** (D-88/D-99, kalıcı kısıt). Ölçümlerin
> tamamı **sentetiktir**; elimizde tek bir gerçek arena karesi yoktur.
>
> ⚠ **Sürüm adının TEK KAYNAĞI `config/model_registry.json`'dur.** Hakem ekranı
> adı oradan okur; bu kılavuz, paket manifesti ve saha kodu onunla **testle**
> kilitlidir (`tests/test_uretim_modeli_hizasi.py`, `test_saha_parametrik.py`).

---

## 0-T58. GÜNCELLEME 2026-08-13 — **asıl model v21 → v24_t57_doku** *(§0-T76 ile AŞILDI)*

> Kullanıcı kararı (`REVIEW_LOG.md` D-82/D-83). Aşağıdaki v21 ve v17 bölümleri
> **silinmedi** — ölçüm kaydıdır. Ama **bugün derlenecek ve koşulacak model
> `navitas_seg_v24_best_640_fp16.onnx`**'tir.
>
> **Neden v24** (kadraj zemini, n=60, D-82): rota **35/60 → 46/60** ·
> yer gerçeğiyle zemin IoU **0,580 → 0,810** · `MASKE_YOK` **9 → 1** ·
> `UC_BANT_TEMAS_YOK` **6 → 1**.
>
> **B1 bağımsız tekrarlandı** (T58 KAPI 2 · 30 gerçek drone karesi, eşit
> aralıklı · üretim zinciri · `conf=0,30`):
>
> | model | boş maske | ort zemin | min | maks |
> |---|---:|---:|---:|---:|
> | **v24** | **0/30** ✅ | %81,0 | %77,2 | %86,6 |
> | v21 | 0/30 | %81,0 | %76,7 | %86,3 |
> | v17 (kontrol) | **28/30** ❌ | %0,4 | %0,0 | %6,6 |
>
> ⚠ **B1 v24 ile v21'i AYIRMAZ** — ikisi de geçiyor, sayılar aynı. B1 yalnız
> "model kör mü" sorusunu sorar. v24'ün gerekçesi B1 değil, yukarıdaki karar
> düzeyi ölçümüdür.
>
> ⚠ **%81 kaplama bir OTOPARKTA ölçüldü ve bu ÇÖKMEDİR** (D-62): model orayı
> arena zemini sanıyor. Bu tabloda "geçti" demek **doğru görüyor** demek değil,
> **kör değil** demektir. Karar zincirinde bu kareler T48 kaplama tavanına
> (%55) takılıp reddedilir — beklenen davranış budur.
>
> ⚠ **v24'ün kazancı GERÇEK görüntüde ölçülmedi.** Otoparkta v21'e göre hiçbir
> fark yok; kazanç, v24 ile aynı dokuyla üretilmiş sentetik kadraj kümesinde
> ölçüldü ("ev sahibi avantajı", D-82'de açıkça yazılı). **Kamera yok** —
> arena başarımı hâlâ doğrulanamamıştır.
>
> **Paket içeriği artık `models/jetson_derleme_manifest.json` içinde sha256'lı
> listelenir** (`paket_icerigi`). Manifest 2026-08-05'ten beri bayattı: `pc_modeli`
> v17 diyordu, oysa pakette v21 ONNX vardı (D-83).

---

## 0-A. GÜNCELLEME 2026-08-08 — koşmadan önce bu dört maddeyi oku

> Kılavuzun geri kalanı 5 Ağustos'ta yazıldı. O günden beri kod değişti ve
> **varsayılan komutlar bu paket için yanlış**. Aşağıdakileri atlarsan test
> yanlış sonuç verir ya da hiç koşmaz.

### G1 · `jetson_fps.py` model varsayılanları üretim manifestine bağlıdır

Betik sürüm adını kendi içinde yazmaz; `models/jetson_derleme_manifest.json`
dosyasındaki `asil_model_pt` ve `asil_model` alanlarını okur:

| argüman | varsayılanın kaynağı | bugün çözülen değer |
|---|---|---|
| `--girdi` | `data/raw_frames` | **YOK**; görüntüler `test_goruntuleri/` altında, yol açıkça verilmeli |
| `--pt` | manifest `asil_model_pt` | `navitas_seg_v35_best.pt` (**VAR**) |
| `--onnx` | manifest `asil_model` | `navitas_seg_v35_best_512_fp16.onnx` (**VAR**) |
| `--engine` | manifest ONNX adıyla aynı gövde | Jetson'da derlenmiş dosya varsa kullanılır; bugün **YOK**, TensorRT vakası açıkça `ATLANDI` |
| `--conf` | `rpi_inference` üretim varsayılanı | `0.30` |
| `--imgsz` | manifest boyutu + üretim `INFER_SIZE` | `[512]`; T76'dan beri manifest ile üretim **aynı boyutta** (D-112) — ayrışacak boyut kalmadı |

Paket içinde argümansız koşuda yalnız girdi eksiktir. `--girdi` açıkça verilir;
PT/ONNX/conf/boyut varsayılanları manifest ve üretim yorumlayıcısından gelir.

### G2 · `rota_bul` durumu bu zincirde ANLAMSIZ — "KAPALI_DAR" görürsen panikleme

`kamera_dogrula.py:118` ve `jetson_fps.py:162` maskeleri `rota_bul`'a
**tuval boyutunda** veriyor. `_maskeleri_icerige_kirp` dolguyu sıfırlıyor ama
**boyutu küçültmüyor**; `rota_bul`'un tohum bantları (alt/üst %8) tam da o
sıfırlanmış dolguya düşüyor. Ölçüldü (`REVIEW_LOG.md` D-25):

```
letterbox'lı  -> durum=KAPALI_DAR
aynı maske kırpık -> durum=ACIK, yol_no=2
```

**Sonuç:** `--zincir` çıktısındaki `durum` ve FPS raporundaki "karar dağılımı"
bu koşumda **kanıt değildir**. Modeli ya da Jetson'u suçlama — bilinen depo kusuru.
FPS sayıları geçerli sayılır, ama tohum boş çıkınca `koridor_adaylari` erken
döndüğü için **bir miktar iyimser** olabilir; raporda böyle not düş.

### G3 · Haberleşme kodu pakette — canlı saha kanıtı yine donanım ister

`jetson_paket/kod/`, rota ve iniş yayını için kanonik `comms/` modüllerini;
`requirements_rpi.txt` ise `pyserial` ve `pymavlink` bağımlılıklarını taşır.
Kopyalar `scripts/jetson_paket_hazirla.py` ile depo kaynaklarından yenilenir.

Depo kapısı paket içeriğini ve loopback ACK yolunu doğrular. Buna rağmen bu
bilgisayarda Pixhawk/SiK donanımıyla canlı doğrulama yapılmadı. Jetson testi
İKA'nın fiziksel hareketini kanıtlamaz; gerçek motor sürücüsü ayrı saha halkasıdır.

### G4 · `rpi_inference.py` artık `costmap_path_finder.py` olmadan çalışmaz

T24 ile görüş hattı denetimi eklendi ve `_gorus_hatti` tek kaynaktan
alınıyor. İkisi de `jetson_paket/kod/` içinde — **aynı klasörde tuttuğun sürece
sorun yok.** Yalnız `rpi_inference.py`'yi kopyalarsan `ImportError` alırsın.

`analyze_path` artık engel maskesini de okuyabiliyor ve birbirine bağlı olmayan
waypoint üretmiyor; gerçek 67 karede ihlalli rota **13 → 0** oldu.

---

## 0. ÖNCE OKU — bugünün testini değiştiren üç bulgu

> ## ⚡ GÜNCELLEME 2026-08-05 akşamı — **v21 geldi, B1'i çözüyor**
>
> Aşağıdaki B1 bulgusu v17/v20 için hâlâ geçerli, ama artık **v21_gercek_doku**
> var ve pakete eklendi. Ölçülen fark (aynı 67 gerçek nadir kare, `conf=0,25`):
>
> | model | kullanılabilir kare | ort zemin | araç üstünde zemin* |
> |---|---:|---:|---:|
> | v17 | 10/67 | %1,04 | — (zaten kör) |
> | v5c | 58/67 | %48,65 | **%70,2** ❌ |
> | **v21** | **67/67** | %81,24 | **%2,0** ✅ |
>
> \* aynı karede DOTA OBB'nin araç dediği piksellerin yüzde kaçını model "zemin"
> sayıyor. Yüksek olması, İKA'nın araçların üstünden geçmeyi güvenli sanması demek.
>
> v21 arena kapısını da geçti: `MASKE_YOK %0`, karar dağılımı çeşitli
> (`BELIRSIZ_TEK_KAPI 15 · KAPALI_DAR 12 · BELIRSIZ_COKLU 2 · ACIK 1`).
> ONNX FP16 paritesi **30/30**, 4 farklı karar durumuyla (boş-doğru değil).
>
> **Bu 2026-08-05 ölçümünün tarihsel önerisiydi.** Bugünkü FPS/engine otoritesi
> §0-T58/T62'deki manifesttir ve **v24**'ü gösterir. v21 kapı raporu
> `jetson_paket/V21_KAPI_RAPORU.json` içinde ölçüm kaydı olarak korunur.

### B1 · v17 gerçek drone karelerinde KÖR (ölçüldü, 2026-08-05)

Aynı model, aynı zincir, üç domain — `conf=0.25`, 12'şer kare:

| model | sentetik arena | RescueNet | **drone kareleri** |
|---|---|---|---|
| **v17** | 59 kutu · %10,8 serbest | 17 kutu · %12,6 serbest | **1 kutu · 11/12 kare boş** |
| v20 | 57 kutu · %10,9 serbest | 15 kutu · %12,2 serbest | **3 kutu · 9/12 kare boş** |

`conf` 0,25 → 0,10 → **0,02**'ye indirildi; v17 üçünde de **sıfır** tespit verdi.
Yani eşik meselesi değil, **domain boşluğu**.

**Bugüne etkisi — atlanırsa test anlamsız olur:**
FPS ölçümünü drone kareleriyle yaparsan model boş maske döndürür, `costmap` neredeyse
boş ızgarada çalışır ve **FPS yanıltıcı yüksek** çıkar. Ölçüm gerçek yükü göstermez.

> **KURAL: FPS ölçümü `test_goruntuleri/sentetik_arena/` ile yapılır.**
> `drone_kareleri/` ayrıca koşulur ama **hız için değil**, domain boşluğunu Jetson'da
> da teyit etmek için.

### B2 · `rpi_inference.py` Jetson'da v17'yi YÜKLEYEMEZ

`codes/rpi_inference.py:32-40` model yolunu **sabit kodlu** arıyor:
```python
MODEL_DIR = next((p for p in [
    _here / "best_ncnn_model",
    _here.parent / "models" / "best_ncnn_model", ...
```
Yani her zaman **NCNN v2** modelini yükler; `--model` argümanı **yoktur**
(`:553-558` — yalnız `--fps --image --video --camera --no-save --conf`).
Ayrıca `INFER_SIZE = 512` sabit.

**Sonuç:** canlı demo için `rpi_inference.py` bugün v17 ile kullanılamaz.
Ölçüm için sorun yok — `jetson_fps.py` kendi modelini kurar, `rpi_inference`'tan
yalnız `_preprocess`/`get_masks`/`_maskeleri_icerige_kirp` fonksiyonlarını alır.

### B3 · H2 hâlâ kanıtsız — ilk iş bu

`TASK_QUEUE.md:46-49` bunu zaten yazıyor: Jetson kurulumu *"tamamlandı işaretli,
ama kanıtı repoda yok"*. **JetPack ve TensorRT sürümü bilinmiyor.**
T16 (engine derleme) bu bilgiye bağlı. Aşağıdaki Adım 1 tam olarak bunu kapatır.

---

## 1. Jetson elde — İLK 10 DAKİKA

Aç, ağa bağla, terminali aç. Sırayla koş, **çıktıları bana yapıştır**:

```bash
# 1a — JetPack ve L4T surumu
cat /etc/nv_tegra_release
head -n1 /etc/nv_tegra_release

# 1b — TensorRT surumu  (T16 bu sayiya bagli)
dpkg -l | grep -i tensorrt
python3 -c "import tensorrt; print('TensorRT', tensorrt.__version__)"

# 1c — CUDA / cuDNN
nvcc --version 2>/dev/null || echo "nvcc PATH'te yok (normal olabilir)"
python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"

# 1d — Ultralytics var mi
python3 -c "import ultralytics; print('ultralytics', ultralytics.__version__)"

# 1e — Donanim ve guc modu
sudo tegrastats --interval 1000 | head -3
sudo nvpmodel -q
jetson_release 2>/dev/null || true
```

**Neden bu sıra:** `.engine` dosyaları TensorRT sürümüne ve GPU mimarisine kilitlidir.
PC'de derlenen engine Jetson'da **çalışmaz** — bu yüzden pakette engine yok, ONNX var.

### ⚡ Güç modunu MAKSİMUM yap — yoksa ölçüm yalan söyler

```bash
sudo nvpmodel -m 0      # MAXN
sudo jetson_clocks      # saatleri kilitle
sudo nvpmodel -q        # dogrula: "NV Power Mode: MAXN"
```

Bunu yapmazsan Jetson düşük güç modunda ölçülür ve **FPS'i olduğundan düşük**
raporlarsın. Ölçümden önce yap, ölçüm boyunca `tegrastats` ile sıcaklığı izle.

---

## 2. Paketi Jetson'a taşı

`O:\navitas\jetson_paket\` klasörünü USB'ye kopyala → Jetson'a tak.

```
jetson_paket/
├── models/
│   ├── navitas_seg_v35_best_512_fp16.onnx   ← ASIL — bunu derle (D-181/D-182, üretim modeli)
│   ├── navitas_seg_v35_best.pt              ← v35 referans / hakem ekranının yüklediği dosya
│   ├── navitas_seg_v27_best_512_fp16.onnx   ← eski asıl (14-15 Ağu), karar kıyası için
│   ├── navitas_seg_v27_best.pt              ← v27 referans / karar kıyası
│   ├── navitas_seg_v24_best_640_fp16.onnx   ← eski asıl (13-14 Ağu), karar kıyası için
│   ├── navitas_seg_v24_best.pt              ← v24 referans / karar kıyası
│   ├── navitas_seg_v21_best_640_fp16.onnx   ← eski asıl (05-13 Ağu), karar kıyası için
│   ├── navitas_seg_v21_best.pt              ← v21 referans / karar kıyası
│   ├── navitas_seg_v17_best_640_fp16.onnx   ← eski asıl, karar kıyası için
│   ├── navitas_seg_v17_best_512_fp16.onnx   ← yedek, doğruluğu ÖLÇÜLMEDİ
│   ├── navitas_seg_v17_best.pt              ← referans karşılaştırma
│   ├── navitas_seg_v20_best.pt              ← yedek model
│   └── jetson_derleme_manifest.json
├── V21_KAPI_RAPORU.json                     ← v21'in geçtiği kapıların kanıtı
├── kod/
│   ├── jetson_fps.py            ← olcum betigi
│   ├── rpi_inference.py         ← _preprocess / get_masks kaynagi
│   ├── costmap_path_finder.py   ← Katman A karari
│   ├── karar_sozlesmesi.py      ← rota karar sabitleri
│   ├── protocol.py              ← ortak mesaj cercevesi
│   ├── link.py                  ← UDP / SiK seri tasiyicilari
│   ├── iha_sender.py            ← ACK'li rota ve olay yayini
│   ├── inis_kaniti.py           ← Pixhawk yerde + irtifa kaniti
│   ├── iha_inis_yayinci.py      ← saha IHA_LANDED yayincisi
│   ├── karisim_arena.yaml       ← INT8 kalibrasyonu icin
│   └── requirements_rpi.txt
└── test_goruntuleri/
    ├── sentetik_arena/    30 kare  ← FPS OLCUMU BUNUNLA
    └── drone_kareleri/    19 kare  ← domain kontrolu, hiz icin DEGIL
```

Jetson'da klasör yapısını koru:
```bash
mkdir -p ~/navitas/{codes,comms,scripts,models,data,config}
cp kod/rpi_inference.py kod/costmap_path_finder.py kod/karar_sozlesmesi.py ~/navitas/codes/
cp kod/protocol.py kod/link.py kod/iha_sender.py kod/inis_kaniti.py kod/iha_inis_yayinci.py ~/navitas/comms/
cp kod/jetson_fps.py ~/navitas/scripts/
cp models/* ~/navitas/models/
cp config/model_registry.json ~/navitas/config/
cp -r test_goruntuleri ~/navitas/data/
```

`jetson_fps.py` yolları `parents[1]/codes` üzerinden kurar — bu yapı şart.

> 🔴 **`config/model_registry.json` BİR ÖNERİ DEĞİL, ZORUNLULUKTUR** (T103 ·
> `REVIEW_LOG.md` D-177/D-178). `load_model` yüklediği ağırlığı kayıt
> defteriyle karşılaştırır ve **fail-closed**tur: defter yoksa
> `model_kayit_dogrula` `"kayit_defteri_yok"` der ve yükleme
> `RuntimeError: MODEL KAYIT DOGRULAMASI BASARISIZ` ile **düşer**. Bu koruma
> T73'te bilerek kuruldu — sahada yanlış ağırlıkla uçmayı engeller.
> Defteri kopyalamadan çalıştırmanın tek yolu `--kayit-dogrulamasiz`'dır ve
> **o bayrak tam bu korumayı kapatır**; saha koşumunda kullanılmaz.
> Defter ayrıca `imgsz`i de taşır: `INFER_SIZE` oradan türer (S5 · D-176).

---

## 3. Bağımlılıklar

```bash
python3 -c "import cv2, numpy, ultralytics, serial, pymavlink; print('hepsi var')"
```
Eksikse:
```bash
pip3 install ultralytics opencv-python numpy pyserial pymavlink
```

Saha iniş yayıncısında toplam kanıt süresi operatör tarafından açıkça verilir;
kod içinde gizli timeout yoktur:

```bash
cd ~/navitas/comms
python3 iha_inis_yayinci.py --mavlink udp:127.0.0.1:14550 --kanit-timeout 5 --serial /dev/ttyUSB0
```

⚠ **`pip install torch` YAPMA.** Jetson'da PyTorch NVIDIA'nın JetPack'e özel
wheel'i ile gelir; PyPI sürümü CUDA'sız kurulur ve her şey CPU'ya düşer.
Zaten kuruluysa dokunma. Değilse NVIDIA Jetson forumundaki JetPack sürümüne
uygun wheel gerekir — bunu bana bildir, birlikte hallederiz.

⚠ `jetson_fps.py:177-180` kasten şöyle yazılmış: `onnxruntime`/`tensorrt` yoksa
o vakayı **atlar**, sessizce pip çalıştırmaz. "ATLANDI: tensorrt_yok" görürsen
bu bir hata değil, o backend'in kurulu olmadığının dürüst raporudur.

---

## 4. TensorRT engine derle (T16)

**Jetson üzerinde**, ONNX'ten. **v30 ile derle** — üretim modeli o (§0-T85):

```bash
cd ~/navitas/models
yolo export model=navitas_seg_v35_best_512_fp16.onnx format=engine imgsz=512 half=True
```

⚠ **Birden çok modeli TensorRT'ye derleme.** v17, v20, v21, v24, v27 ve v30 aynı
mimaridir (YOLOv8m-seg, 27,2M parametre); ağırlık değerleri hızı değiştirmez.

⚠ **Ama girdi boyutu değiştirir.** v30 ONNX'i **512**, eskiler **640**. 512, 640'ın
**0,64 katı** hesaptır. Eski bir 640 engine ile v30'u FPS'te kıyaslarsan
boyut farkını modele yazarsın — bu ölçüm değil, karışıklıktır.
Üçünü derlersen ~45 dakika harcayıp üç kez aynı FPS'i ölçersin.

Modelleri ayıran şey hız değil **karar doğruluğu**. Onu ölçmek için derlemeye
gerek yok, `.pt` yeter (§5 sonundaki karar kıyası).

Bu 5–15 dakika sürebilir; TensorRT katman katman optimize eder. Sabret, kesme.

**Kapı (T16):** `.engine` dosyası oluştu **ve** tek kare çıkarım hatasız tamamlandı:
```bash
yolo predict task=segment model=navitas_seg_v30_best_512_fp16.engine \
  source=~/navitas/data/test_goruntuleri/sentetik_arena --imgsz 512
```

### `yolo export` hata verirse — `trtexec` yedeği
```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=navitas_seg_v35_best_512_fp16.onnx \
  --saveEngine=navitas_seg_v30_best_512_fp16.engine \
  --fp16 --workspace=4096
```

---

## 5. FPS ölçümü (T17) — ASIL TEST

```bash
cd ~/navitas
python3 scripts/jetson_fps.py \
  --girdi test_goruntuleri/sentetik_arena \
  --pt models/navitas_seg_v35_best.pt \
  --onnx models/navitas_seg_v35_best_512_fp16.onnx \
  --engine models/navitas_seg_v30_best_512_fp16.engine \
  --imgsz 512 \
  --isinma 15 --tekrar 120 --conf 0.30 --cihaz 0 \
  --cikti results/jetson_fps_v30_$(date +%Y%m%d_%H%M%S)
```

**PC referansı (RTX 5080, aynı zincir, karşılaştırman için):**
`çıkarım 14,00 ms · maske 2,23 ms · costmap 8,89 ms · toplam 27,38 ms · 36,5 FPS`
Jetson Orin NX bunun belirgin altında çıkacaktır; gerekli olan **0,9–2,6 FPS**.

Ölçülen zincir (yalnız model değil, **gerçek karar yolu**):
```
kare oku → letterbox/çıkarım → get_masks → costmap rota_bul(plan=False)
```

Çıktı: `results/.../ozet.json` + `rapor.md`. **İkisini de bana getir.**

### Ölçüm sırasında ayrı terminalde
```bash
sudo tegrastats --interval 1000 | tee ~/tegrastats_olcum.log
```
Sıcaklık ve GPU kullanımını görürsün. **Termal kısılma (throttle) olursa p95
şişer** — p50/p95 farkı bunu ele verir.

### Domain kontrolü (hız için değil)
```bash
python3 scripts/jetson_fps.py \
  --girdi data/test_goruntuleri/drone_kareleri \
  --pt models/navitas_seg_v17_best.pt \
  --onnx models/navitas_seg_v17_best_640_fp16.onnx \
  --engine models/navitas_seg_v17_best_640.engine \
  --imgsz 640 --isinma 5 --tekrar 40 --cihaz 0 \
  --cikti results/jetson_domain_kontrol_$(date +%Y%m%d_%H%M%S)
```
**Beklenen — model seçimine göre değişir:**
- `v17`/`v20` ile → ezici çoğunluk `MASKE_YOK`. Bu **B1'in Jetson'da teyididir**, arıza değil.
- **`v24` (asıl) ile → `MASKE_YOK` ÇIKMAMALI.** PC'de 30/30 karede zemin buldu
  (T58 KAPI 2, üretim zinciri, `conf=0,30`). v24 ile `MASKE_YOK` görürsen PC
  ölçümüyle çelişki var demektir — bana söyle.
- **`v21` ile de → `MASKE_YOK` ÇIKMAMALI** (0/30). Bu iki model B1'de ayırt
  edilemez; ayrım karar düzeyindedir (§0-T58).

### Karar kıyası — üç modeli ayıran asıl test (derleme gerekmez, ~5 dk/model)

FPS üç modelde de aynı çıkacağı için, onları ayıran şey **hangisi sahada karar
üretebiliyor**. `.pt` ile koş, `rota_durumlari` dağılımını karşılaştır:

```bash
for M in v21 v17 v20; do
  python3 scripts/jetson_fps.py \
    --girdi data/test_goruntuleri/drone_kareleri \
    --pt models/navitas_seg_${M}_best.pt \
    --onnx models/YOK --engine models/YOK \
    --imgsz 640 --isinma 5 --tekrar 40 --conf 0.25 --cihaz 0 \
    --cikti results/karar_${M}
done
```

Sonra üç `rapor.md`'yi yan yana koy. PC'de ölçülen beklenti:

| model | gerçek karede zemin bulunan | ort zemin |
|---|---:|---:|
| v17 | 10/67 | %1,04 |
| v20 | 10/67 | %4,11 |
| **v21** | **67/67** | **%81,24** |

---

## 6. FP16 mi INT8 mi — ikisini birden yapma, SIRAYLA yap

Sorunun cevabı: **evet ikisi de ölçülmeli, ama INT8 koşullu.** Gerekçe ölçülmüş.

### Neden FP16 önce

**PC referansı — 2026-08-05, sentetik arena 30 kare, 60 tekrar, RTX 5080:**

| aşama | PyTorch p50 | ONNX FP16 p50 | pay |
|---|---:|---:|---:|
| **çıkarım** | **14,00 ms** | **14,79 ms** | **~%51** |
| maske | 2,23 ms | 2,31 ms | ~%8 |
| costmap | 8,89 ms | 9,98 ms | ~%32 |
| **toplam** | **27,38 ms** | **29,23 ms** | |
| FPS (p50) | 36,52 | 34,21 | |

⚠ **Bu tablo `ARCHITECT_PLAN.md`'deki eski satırı çürütüyor.** Orada
*"darboğaz costmap (51,2 ms), çıkarımın ~2 katı"* yazıyor. Taze ölçümde costmap
**8,89 ms** ve darboğaz **çıkarım**. İki ölçüm farklı girdi kümesiyle yapıldı
(eski: `jetson_fps_pc_smoke`, yeni: sentetik arena) ve aradaki commit'ler
letterbox yolunu değiştirdi — bu yüzden kıyaslanabilir değiller. **Bugün geçerli
olan bu tablodur; planı Jetson sayıları gelince güncelleyeceğim.**

Sonuç: çıkarım baskın olduğu için **INT8'in getirisi eskiden sandığımdan yüksek**.
Yine de sıra değişmiyor — Jetson'daki oran bilinmiyor ve ölçmeden optimize edilmez.

### ONNX FP16 parite kapısı — GEÇTİ (gerçek kanıtla)

Aynı 60 karede PyTorch ve ONNX **birebir aynı** rota kararlarını verdi:
```
KAPALI_DAR 24 · BELIRSIZ_TEK_KAPI 22 · MASKE_YOK 6 · BELIRSIZ_COKLU 6 · ACIK 2
```
Beş farklı durum, hepsi eşleşiyor. FP16 dönüşümü kararı bozmuyor.

> Not: ilk parite denemem drone kareleriyle yapıldı ve IoU 1,0000 verdi — ama
> **her iki maske de boştu** (B1). Boş kümede IoU 1,0 çıkar; o kapı sahte geçmişti.
> Yukarıdaki sonuç sentetik arenayla, beş ayrı karar durumuyla alındı.

### Karar kuralı

```
FP16 engine ile ölç
   ├─ FPS ≥ 3   → INT8'e GİRME. Gereken hız 0,9–2,6 FPS (kapsama hesabı).
   │              INT8'in doğruluk riski bedava değil, karşılığında bir şey almıyorsun.
   └─ FPS < 3   → INT8 dene, AMA doğruluğu ayrıca ölç (aşağıdaki kapı).
```

15 FPS **şartname şartı değil**, takımın iç hedefi. Şartnamenin istediği kapsama
hesabından çıkan gerçek gereksinim **0,9–2,6 FPS**.

### INT8 gerekirse

```bash
cd ~/navitas/models
yolo export model=navitas_seg_v35_best_512_fp16.onnx format=engine imgsz=512 \
  int8=True data=~/navitas/codes/karisim_arena.yaml
```
⚠ `karisim_arena.yaml` içindeki yollar **Windows mutlak yolları** (`O:\navitas\...`).
Jetson'da çalışması için yolları düzenlemen gerekir — bunu birlikte yaparız,
kalibrasyon veri setinin Jetson'a da kopyalanması lazım.

**INT8 doğruluk kapısı — atlanamaz:** segmentasyon maskeleri INT8'de FP16'dan
farklı bozulur. INT8 engine'i ölçtükten sonra aynı 30 karede **serbest alan
maskesini FP16 ile karşılaştır**; serbest alan IoU **< 0,98** ise INT8 reddedilir.
Sebep mimari: *"serbest alan OTORİTEDİR"* — serbest alanı **büyüten** hiçbir
işlem kabul edilmez, INT8 gürültüsü dahil.

---

## 6B. DroidCam — telefonu kamera olarak bağla (H3)

### Neden ayrı bir araç gerekiyor

`rpi_inference.py:505` kamerayı şöyle açıyor:
```python
def run_camera(model, conf):
    cap = cv2.VideoCapture(0)          # ← SABIT indeks 0
```
Kaynak parametrik değil — DroidCam URL'si ya da farklı `/dev/videoN` verilemez.
Bu T18'in konusu. Bugün için pakete `kod/kamera_dogrula.py` koydum: kaynağı
parametre alır, akışı ölçer, istersen gerçek algı zincirini de koşar.

### Yol seçimi — WiFi'yi tercih et

| yol | nasıl | risk |
|---|---|---|
| **WiFi (MJPEG over HTTP)** ✅ | telefon ve Jetson aynı ağda; OpenCV URL'yi doğrudan açar | ağ gecikmesi; kernel modülü **gerekmez** |
| USB (adb forward) | `adb forward tcp:4747 tcp:4747` → `http://127.0.0.1:4747/video` | adb kurulumu; USB hata ayıklama açık olmalı |
| droidcam-cli + v4l2loopback | `/dev/videoN` düğümü üretir | ⚠ **kernel modülü derleme gerektirir**; Jetson'ın özel kernel'inde sorun çıkarır |

**Üçüncü yolu bugün deneme.** v4l2loopback Jetson'da kernel başlıkları ister ve
saha gününde açılacak bir kutu değil. İlk ikisi OpenCV'nin doğrudan desteklediği
HTTP akışıdır ve hiçbir sürücü kurulumu gerektirmez.

### WiFi yolu

1. Telefonda **DroidCam** uygulamasını aç, "Start" bas.
2. Uygulamanın gösterdiği **IP** ve **portu** (varsayılan 4747) not al.
3. Jetson ile telefon **aynı ağda** olsun.
4. Jetson'da:

```bash
# once erisim var mi
ping -c 3 <TELEFON_IP>

python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --kare 120 --isinma 15 \
  --kaydet ~/navitas/results/droidcam_ilk_kare.jpg
```

### USB yolu (WiFi olmazsa)

```bash
sudo apt install -y android-tools-adb        # yoksa
adb devices                                   # telefonda "izin ver" cikar
adb forward tcp:4747 tcp:4747

python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://127.0.0.1:4747/video" \
  --kare 120 --kaydet ~/navitas/results/droidcam_ilk_kare.jpg
```

### Ne bildireceksin (H3 tam olarak bunu istiyor)

Betiğin son bloğunu olduğu gibi getir:
```
okunan kare      : 120  (dusen: 0)
kare gecikmesi   : p50=... ms  p95=... ms
OLCULEN FPS      : ...
cozunurluk       : ...x...
```
Ayrıca `droidcam_ilk_kare.jpg`'ye **gözle bak** — görüntü gerçekten telefonun
kamerası mı, yoksa siyah/donmuş kare mi? Sürücünün bildirdiği çözünürlük ve FPS
yalan söyleyebilir; betik bu yüzden ikisini ayrı raporluyor.

### Algı zinciriyle canlı test

Akış doğrulandıktan sonra gerçek zinciri de koşabilirsin:
```bash
python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --zincir --model ~/navitas/models/navitas_seg_v17_best_640.engine \
  --imgsz 640 --kare 60
```
⚠ **Beklenti:** telefon kamerası gerçek sahneye bakıyorsa **B1 burada da geçerli** —
`rota_durumlari` büyük ihtimalle `MASKE_YOK` ağırlıklı çıkar. Bu modelin arızası
değil, domain boşluğunun canlı görüntüde de sürdüğünün kanıtıdır. Sayıyı yine de
kaydet; eğitim verisi kararı için değerli.

---

## 6C. BİRİNCİL→YEDEK MODEL GEÇİŞ YORDAMI (T123)

> 🔴 **NEDEN VAR:** Jetson saha kurulumuyla AYNI GÜN ele geçiyor (D-211 §5) —
> cihaz-öncesi doğrulama penceresi yok. Birincil aday sahada düşerse geçiş
> **el yordamıyla değil bu yordamla** yapılır. Kurulum yordamı T104 ile
> testli; bu bölüm de `tests/test_kilavuz_gecis_yordami.py` ile kilitlidir.
> ⚠ Aday ADLARI bu yordama T121+T123 kapanınca yazılır (T130'da dolduruldu: yedek = **v34**); yordamın mekaniği ada bağımlı değildir. **Geçiş KARARI
> İNSANINDIR (D-133)** — yordam yalnız mekaniktir.

### G1 · Tetik ve karar

🔴 **ÖNCE SENARYOYU AYIR — her arıza geçişle çözülmez** (D-277 §3-4).
Aşağıdaki tablo **bağlayıcıdır** ve `tests/test_t141_rota_yoksa_surme.py`
bunu kılavuzdan **okuyup kodda koşarak** doğrular (T104/T123 kalıbı).

```text
T141-KURAL
SENARYO (a) cok moloza basiyor        -> GECIS SERBEST
SENARYO (b) rota uretilmiyor          -> GECIS YASAK
SENARYO (c) teknik cokme / yuklenmiyor -> GECIS SERBEST
```

- **(a) ve (c) — geçiş meşru.** Tetik: **§5 "Karar kıyası"** (üç modeli ayıran
  test) veya **§5 "Domain kontrolü"**. Karar veren: takım (insan). Saat +
  gerekçe saha defterine yazılır. Yedek: **v34**; (c)'de doğrulanmış herhangi
  bir ağırlık yeter.
- 🔴 **(b) — GEÇİŞ YASAK.** Birincil "göremiyor" ise **sahne okunamıyor**
  demektir; okunamayan sahnede model değiştirmek *aynı körlüğü başka bir
  modelle denemektir* (D-277 §3). Yedek v34 bu eksende **daha kötüdür**:
  gerçek karelerin **67/67'sini** reddeder (D-249).
  **Yapılacak, aynen:**

  > **Rota üretilmiyorsa model değiştirilmez; İKA sürmez ve sebep kaydedilir.**

  Bu bir temenni değil, **kodda zorlanan** davranıştır: `ika_nav` NO_ROUTE
  boyunca sıfır-olmayan motor komutu vermez (ölçüldü: 3 komut, **0**
  sıfır-olmayan). Sebep saha defterine §G7 satırıyla yazılır.

### G2 · Yedeğin varlığı ve bütünlüğü
Yedeğin `.pt` ve `.onnx` dosyaları pakette olmalı ve sha256'ları
`models/jetson_derleme_manifest.json` → `paket_icerigi` ile eşleşmeli:
```bash
cd ~/navitas
python3 - <<'PY'
import hashlib, json, pathlib
kok = pathlib.Path.home() / "navitas"
man = json.loads((kok / "models/jetson_derleme_manifest.json").read_text(encoding="utf-8"))
# 🔴 T123'te KOSULARAK olculdu: onceki surum `man["paket_icerigi"].get("models/" + ad)`
#    diyordu ve SAHA GUNU `AttributeError: 'list' object has no attribute 'get'`
#    ile COKERDI. Iki hata bir satirda: (1) `paket_icerigi` SOZLUK DEGIL LISTE,
#    (2) anahtarlari CIPLAK dosya adi, "models/" oneki YOK. G2, "bozuk yedekle
#    gecme" KAPISIDIR; coktugunde operatör ya kapiyi atlar ya da tikanir.
kunye = {x["dosya"]: x["sha256"] for x in man["paket_icerigi"]}
for ad in ("navitas_seg_v34_best.pt", "navitas_seg_v34_best_512_fp16.onnx"):   # T130: yedek = v34
    yol = kok / "models" / ad
    beklenen = kunye.get(ad)
    ozet = hashlib.sha256(yol.read_bytes()).hexdigest()
    print(ad, "OK" if ozet == beklenen else f"UYUSMAZ ({ozet[:12]} != {str(beklenen)[:12]})")
PY
```
`UYUSMAZ` veya dosya yoksa **geçiş YAPILMAZ** — bozuk yedekle koşmak,
düşen birincille koşmaktan kötüdür.

### G3 · Yedek-dosya kopyaları (sahada git yok)
```bash
cp config/model_registry.json config/model_registry.json.oncesi
cp models/jetson_derleme_manifest.json models/jetson_derleme_manifest.json.oncesi
```

### G4 · Defteri yedeğe çevir (yalnız PAKET kopyası)
`config/model_registry.json` → `profiles.competition` altında **yalnız** şu
alanlar değişir: `model_id`, `path`, `sha256`, (gerekiyorsa) `imgsz`.
Yeni değerler yedeğin KENDİ defter kaydından alınır — elle uydurulmaz;
`imgsz` değişiyorsa `_imgsz_notu` disiplinine uyulur. Başka HİÇBİR alana
dokunulmaz. ⚠ **Deponun kök kopyası sahada DEĞİŞTİRİLMEZ**; dönüşte mimar
onayıyla senkronlanır — aksi iki defteri sessizce ayrıştırır (D-189 sınıfı).

### G5 · Paket künyesini çevir
`models/jetson_derleme_manifest.json` → `asil_model_pt` ve `asil_model`
alanları yedeğin dosya adlarına çevrilir. Künye paketin GERÇEĞİNİ anlatır;
defterle tutarlılığı `tests/test_saha_parametrik.py` sınıfı kilitler.

### G6 · Doğrulama zinciri (SIRALI — biri düşerse §G8)
1. **Yükleme + defter kapısı:** kısa koşum, `load_model` +
   `model_kayit_dogrula` zincirinden geçer (fail-closed; `--kayit-dogrulamasiz`
   sahada YASAK):
```bash
python3 scripts/jetson_fps.py \
  --girdi test_goruntuleri/sentetik_arena \
  --pt models/navitas_seg_v34_best.pt --onnx models/navitas_seg_v34_best_512_fp16.onnx \
  --imgsz 512 --isinma 1 --tekrar 3 --conf 0.30 --cihaz 0 \
  --cikti results/gecis_dogrulama_$(date +%Y%m%d_%H%M%S)
```
2. **Domain kontrolü:** §5 "Domain kontrolü" adımı yedek modelle tekrarlanır.
3. Süre varsa tam FPS ölçümü (§5); yoksa kısa koşumla yetinildiği saha
   defterine yazılır.

### G7 · Kayıt
Saha defterine: saat · gerekçe · G2/G6 çıktı yolları · kim karar verdi.
Dönüşte `REVIEW_LOG.md`'ye D-kaydı olarak işlenir — **kaydedilmeyen geçiş
tekrar tartışılır.**

### G8 · GERİ ALMA
```bash
cp config/model_registry.json.oncesi config/model_registry.json
cp models/jetson_derleme_manifest.json.oncesi models/jetson_derleme_manifest.json
```
Geri almadan sonra G6/1 doğrulaması birincil ile YENİDEN koşulur — geri
dönüşün de kanıtı olur.

---

## 7. Yaptığın her şeyde bana getireceklerin

Bunları toplarsan T16 ve T17'yi kanıtlı kapatabilirim:

| # | Ne | Nereden |
|---|---|---|
| 1 | JetPack + TensorRT + torch sürümleri | Adım 1 çıktıları |
| 2 | `nvpmodel -q` çıktısı | güç modu MAXN mi |
| 3 | `results/jetson_fps_v17_*/ozet.json` + `rapor.md` | Adım 5 |
| 4 | `results/jetson_domain_kontrol_*/rapor.md` | Adım 5 domain kontrolü |
| 5 | `tegrastats` logu | termal kısılma oldu mu |
| 6 | engine derleme çıktısı (başarı ya da hata) | Adım 4 |
| 7 | `kamera_dogrula.py` son bloğu + `droidcam_ilk_kare.jpg` | §6B — H3'ü kapatır |

---

## 8. Ters giderse

| Belirti | Sebep | Ne yap |
|---|---|---|
| `yolo export ... format=engine` çöküyor | TensorRT sürüm uyuşmazlığı / bellek | `trtexec` yedeğini dene (§4); `--workspace` düşür |
| Tüm vakalar `ATLANDI` | backend kurulu değil | §3'teki import kontrolünü koş, çıktıyı bana at |
| `torch.cuda.is_available() == False` | PyPI torch kurulmuş | **`pip install torch` yapma**, JetPack wheel'i gerekiyor — bana bildir |
| FPS beklenenden çok düşük | güç modu / termal kısılma | `nvpmodel -m 0` + `jetson_clocks`; `tegrastats`'ta sıcaklığa bak |
| `MASKE_YOK` her karede (sentetik arenada) | yanlış model ya da yanlış klasör | model dosyasını ve `--girdi` yolunu doğrula — sentetik arenada **olmaması gerekir** |
| `rpi_inference.py` v2 NCNN yüklüyor | B2 — model yolu sabit kodlu | Bugün ölçüm için `jetson_fps.py` kullan; bunu kuyruğa alıyorum |

---

## 9. Bugün YAPILMAYACAKLAR

- **Model yeniden eğitilmeyecek.** B1 (domain boşluğu) bir eğitim verisi sorunudur,
  Jetson'da çözülmez.
- **`rpi_inference.py` bugün elden geçirilmeyecek** — B2 kuyruğa girer, sahada
  aceleyle değiştirilmez.
- **INT8 körlemesine denenmeyecek** — §6 karar kuralı geçerli.
- **Commit atılmayacak** (sen ayrıca istemedikçe).
