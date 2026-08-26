# SAHA ZİNCİRİ TAZELEME — 2026-08-26 (ÖLÇÜM; kod DEĞİŞMEDİ)

**Görev:** bugün kapanan işlerin (T146, T147, T148, T151, T152, T153, T155, D-294)
`CONTRACTS.md §11.2` halka tablosunda ve `results/sartname_bosluk/rapor.md`'de bıraktığı
**bayatlığı ölçümle kapatmak**; 30 Eylül saha günü kontrol listesini üretmek.

**Kapsam kuralı:** üretim kodu **değiştirilmedi**. Yalnız belge + rapor + ölçüm.
GPU **koşulmadı** (bu ajan için yasak; PC bugün BSOD verdi — `results/pc_cokme_20260826/rapor.md`).

---

## 1 · KOŞULAN KOMUTLAR VE GERÇEK ÇIKTILAR

### 1.1 Kuru koşu — GPU gizlenerek (asıl ölçüm)

```
> CUDA_VISIBLE_DEVICES=-1 O:\navitas-local-train\venv\Scripts\python.exe -B \
    scripts/saha_kuru_kosu.py --cikti results/saha_zinciri_20260826/kosu_cpu

Kamera acilamadi (kaynak='/dev/video7').
Kamera acilamadi (kaynak=3).
==============================================================================
SAHA KURU KOSUSU — CONTRACTS.md §11 · Gazebo YOK · donanim YOK
==============================================================================
  kamera         GECTI      kaynak parametrik ve VideoCapture'a BESLENIYOR
                            (cihaz yolu str, indeks int olarak cozuluyor)     [1743 ms]
                            -> codes/rpi_inference.py:run_camera
  model_yukleme  GECTI      agirlik manifestten turetiliyor, --model besliyor,
                            uyusmazlikta fail-closed ve kayit defteriyle eslesiyor [34 ms]
                            -> codes/rpi_inference.py:load_model
  cikarim        GECTI      tek kare cikarimi tamamlandi                       [1621 ms]
                            -> codes/rpi_inference.py:57
  maske          GECTI      {0,1} anahtarli maskeler uretildi                  [264 ms]
                            -> codes/rpi_inference.py:60-83
  olcek          GECTI      canli telemetri bu kare icin gecerli mpp uretti
                            -> codes/rpi_inference.py
  hedef_konumu   SAHIPSIZ   HB'nin tek kaynagi Gazebo meta.txt; saha kod yolunda
                            --hb girisi yok ve etkin model profili 2 sinifli
  rota           DUSTU      rota uretilemedi: durum=BELIRSIZ_TEK_KAPI          [51 ms]
                            -> codes/costmap_path_finder.py:729
  aktarim        GECTI      saha paketi haberlesme kodunu tasiyor; uretim yolu
                            run_camera karari loopback IKA'ya OPEN_ROUTE olarak yazdi
                            -> codes/rpi_inference.py:run_camera
  telsiz halkasi GECTI      run_camera -> KararYayinci -> loopback IKA:
                            {'open_route_alindi': True, 'heartbeat': 1,
                             'ack': ['ika'], 'hata': None}
  surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor
                            -> comms/iha_inis_yayinci.py:60
  motor          SAHIPSIZ   gercek motor surucusu yok; send_vel yalnizca gz
                            subprocess'i ve ika_nav simulation/ altinda
------------------------------------------------------------------------------
GECTI 7 · DUSTU 1 · SAHIPSIZ 2 · ATLANDI 0
KOPUK HALKALAR (3): hedef_konumu, rota, motor
Zincir saha kosumunda TAMAMLANMAZ.
Cikti: O:\navitas\results\saha_zinciri_20260826\kosu_cpu
CIKIS=1
```

Ham çıktı: `results/saha_zinciri_20260826/kuru_kosu_cpu.txt`
Makine özeti: `results/saha_zinciri_20260826/kosu_cpu/ozet.json`
Kare: `data/raw_frames/whatsapp_video_2026_07_30_at_11_44_03/frame_000000_000000000.jpg` (576×1024)
Model: `navitas_seg_v36_best.pt` (kayıt defteriyle eşleşti)

### 1.2 GPU gerçekten koşmadı — kanıt

```
> CUDA_VISIBLE_DEVICES=-1 <venv> -B -c "import torch;print('cuda_available',torch.cuda.is_available(),'count',torch.cuda.device_count())"
cuda_available False count 0

> nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv
memory.used [MiB], utilization.gpu [%]
14 MiB, 0 %
```

### 1.3 İlk denemem YANLIŞTI — kayda geçiyor

`--atla-cikarim` kullanmak yerine GPU'yu gizlemeyi seçtim; ilk denemede
`CUDA_VISIBLE_DEVICES=""` verdim ve ultralytics'in cihaz doğrulayıcısı bunu reddetti:

```
  cikarim        DUSTU      cikarim istisna verdi: AssertionError: Invalid device id
  maske          ATLANDI    onceki halka dustu: cikarim
  olcek          DUSTU      OLCEK_YOK: kare icerik genisligi yok
GECTI 4 · DUSTU 2 · SAHIPSIZ 2 · ATLANDI 2
```

Bu **zincir kopukluğu değil, ölçüm aygıtının kendi hatasıdır.** Ultralytics'in CPU
için kendi kullandığı değerle (`-1`) tekrar koşuldu. **Yanlış koşum silinmedi:**
`results/saha_zinciri_20260826/kuru_kosu_tam.txt` ve `kosu_tam/` repoda duruyor.
(Ham çıktının saklanması bu projede bir kez yanlış hükmü zaten engellemişti — D-209 §4.)

### 1.4 Kapılar (kod değişmedi, yine de koşuldu)

```
> <venv> -B codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI          RC=0

> <venv> -B -m unittest discover -s tests -q
Ran 1002 tests in 82.606s
OK (skipped=2)                                  RC=0
```
Belge değişikliklerinden **sonra** ikinci kez koşuldu (`CONTRACTS.md` ve `REVIEW_LOG.md`
kapılarca denetlenen belgelerdir):

```
> <venv> -B -m unittest discover -s tests -q
Ran 1007 tests in 92.645s
OK (skipped=2)                                  RC=0
```
Ham çıktılar: `kapi_rota_sentetik.txt`, `kapi_unittest.txt`, `kapi_unittest_son.txt`.

⚠ **Üç ayrı sayı — üçü de açıklandı, hiçbiri gevşetme değil:**
- Brifing **988** diyordu (master'ın sabahki hâli).
- İlk koşumumda **1002** — fark bugün kapanan T146/T147/T148/T155 testleri.
- İkinci koşumumda **1007** — aradaki **+5 BENİM DEĞİL**: eşzamanlı çalışan
  `conf_supurme` ajanı `tests/test_conf_esigi_supurmesi.py` dosyasını 22:55'te
  ekledi (`git status` → `?? tests/test_conf_esigi_supurmesi.py`, dosya zaman damgası
  iki koşumun **arasında**). O dosya **bu commit'e dâhil edilmedi.**
- Üç koşumda da `skipped=2` **aynı**, `FAILED` **yok**.

### 1.5 `jetson_paket` aynaları

```
> diff -q codes/<x>.py jetson_paket/kod/<x>.py   (rpi_inference, costmap_path_finder,
                                                  karar_sozlesmesi, arac_maskesi)
> diff -q comms/<x>.py jetson_paket/kod/<x>.py   (protocol, link, iha_sender,
                                                  inis_kaniti, iha_inis_yayinci)
> diff -q config/model_registry.json jetson_paket/config/model_registry.json
```
**10/10 diff BOŞ.** Kod değişmediği için ayna tazelemeye gerek olmadı; **doğrulandı**.

---

## 2 · HANGİ HALKA GEÇTİ / DÜŞTÜ / SAHİPSİZ

| # | halka | durum | değişim (sabahki kayda göre) |
|---|---|---|---|
| 1 | kamera | **GEÇTİ** | KUSURLU (D-13) → GEÇTİ · `VideoCapture(0)` sabiti kalktı |
| 2 | model_yükleme | **GEÇTİ** | KUSURLU (D-13) → GEÇTİ · v36, kayıt defteri fail-closed |
| 3 | çıkarım | **GEÇTİ** | ATLANDI → GEÇTİ (sabah `--atla-cikarim` idi) |
| 4 | maske | **GEÇTİ** | ATLANDI → GEÇTİ |
| 5 | ölçek | **GEÇTİ** | DÜŞTÜ → GEÇTİ · `mpp=0,0338` (sahte yayın **gerçekten** okuyucudan geçirildi) |
| 6 | hedef_konumu | **SAHİPSİZ** | değişmedi · **T150** |
| 7 | rota | **DÜŞTÜ** | `BELIRSIZ_TEK_KAPI` — **aşağıdaki uyarıyı oku** |
| 8 | aktarım | **GEÇTİ** | + **telsiz halkası GEÇTİ** (T146/K1, yeni) |
| 9 | sürüş_izni | **GEÇTİ** | KUSURLU (D-22) → GEÇTİ · üretici artık `simulation/` altında değil |
| 10 | motor | **SAHİPSİZ** | değişmedi · **T149** (insan/donanım) |

### 🔴 Halka 7 aldatıcıdır — en önemli bulgu

`scripts/saha_kuru_kosu.py:709` → `rota_bul(maskeler, mpp=mpp, icerik=icerik)`.

Ama **D-295/T151** ile bugün ilan edildi (CONTRACTS §11.2-EK):
**`analyze_path` ÜRETİM, `rota_bul` TANISAL.**

Yani bugünkü tek `DUSTU` satırı **tanısal yolun** sonucudur ve **üretim karar yolu
kuru koşuda hiç koşmuyor.** İki yönlü hata üretir:

- `DUSTU` görünce üretimin düştüğünü sanabiliriz (sanmıyoruz — ölçüldü, yazıldı);
- `GECTI` görsek bile üretim hakkında **hiçbir şey** öğrenmiş olmayız.

Bu, **T156**'nın (genel kapı 15/15 yalnız `rota_bul`u zorluyor) kuru-koşu ikizidir.
CONTRACTS §11.2 halka 7 satırı bunu **açıkça** yazar; uydurulmadı, gizlenmedi.

### Kuru koşunun kendi etiketleri de bayat

Betik halka 3'ü `codes/rpi_inference.py:57`, halka 4'ü `:60-83` diye etiketliyor.
Bugün ölçüldü — ikisi de **import bloğunun içine** düşüyor:

```
> sed -n '55,62p' codes/rpi_inference.py     → import devamı (bant_temasi_yeterli_mi, …)
> sed -n '60,64p' codes/rpi_inference.py     → import devamı (BARIYER_ENGEL_SINIFI, …)
```
Gerçek sahipler: `model.predict` `codes/rpi_inference.py:2143` (`run_camera` içinde),
`get_masks` `:727`. CONTRACTS §11.2 **doğru satırlarla** tazelendi; betiğin etiketi
açık kusurdur (D-297 §2).

---

## 3 · DEĞİŞEN BELGELER

| dosya | ne yapıldı |
|---|---|
| `CONTRACTS.md` §11.2 | Halka tablosu **ölçülen** duruma göre yeniden yazıldı: her satırda sahip `dosya:satır`, durum ve **kanıt dosyası**. Koşum ortamı (GPU kapalı, kare, sayım) tablo başına yazıldı. Halka 7'nin ölçüm boşluğu açıkça bırakıldı. |
| `results/sartname_bosluk/rapor.md` | Sabahki §0–§4 **silinmedi** (kanıt zinciri); üstüne **T0–T4 tazeleme bölümü** eklendi: 21 hüküm satırının bugünkü durumu + yeni **R22**. |
| `results/saha_zinciri_20260826/saha_gunu.md` | 30 Eylül kontrol listesi (10 adım, her adımda **başarı ölçütü** ve **düşerse ne yapılacak**). |
| `REVIEW_LOG.md` | **D-297** eklendi (5 alt başlık, ÖLÇÜLEMEDİ kaydıyla). |

---

## 4 · ŞARTNAME YENİDEN TARAMASI (§2.2 ve §6, `venv` + `fitz`)

PDF 30 sayfa · **56 418 karakter** →
`results/saha_zinciri_20260826/sartname_metin_20260826.txt`.
(Sabah 56 919 yazılmıştı; fark **metin birleştirme** farkı, PDF aynı dosya.)

**Bir hüküm atlanmış bulundu → R22 (İNSAN/DONANIM):** §2.2.6 son maddesi —
*"İKA'nın belirlenen yükleri taşıyarak hedef bölgeye intikal etmesi esastır… yapısal
bütünlüğünü koruyor olması ve taşıdığı yükü/yükleri eksiksiz muhafaza etmesi
zorunludur; aksi takdirde ilgili görev başarısız sayılır."*
Yazılıma düşmez, ama **"görev başarısız"** yaptırımlı bir hüküm 21 satırlık tabloda
hiç görünmüyordu.

**Sabahki tabloda BAYAT çıkan iki satır (bugün karşılandığı ölçüldü):**
- §6.2 hazırlık 15 dk + "Takım Hazır" + müdahale **−100 ceza** ve sürenin hazırlığa
  eklenmesi → `comms/yks_gui.py:1976 _ceza_ekle`, `:1985`, `:2001-2011`. R16 "yalnız
  gösterge + log" diyordu; **yanlış.**
- §6.2 tekrar fırlatma "süre durdurulmaz" → `yks_gui.py:1889 firlatma()`
  `if self.t_iha0: return` ile kronometre **yeniden başlamıyor**. Tabloda hiç yoktu;
  davranış **doğru**, ama **doğrudan tekrar-fırlatma testi YOK**.

**Yeni açık kusur (madde 16):** `comms/yks_gui.py`'de `"15:00"` beş yerde **çıplak**
(`:494, :519, :1893, :2090, :2094`); `SARTNAME_HAZIRLIK_SURESI_S` sabiti **yok**
(`grep` → 0). İHA limiti sabitten geliyor ama ekran metni ondan türemiyor.
Bugün kod değiştirilmediği için **düzeltilmedi, kayda geçti**.

**K2 ve K3 insan/donanım kararı olarak KALIR:**
- **K2 · İKA motor sürücüsü (T149):** kuru koşu bugün de `motor SAHİPSİZ`;
  saha sürücü importu **0**. Mimar/AI kapatamaz.
- **K3 · HB dedektörü (T150):** artık yalnız "test yok" değil, **ölçülmüş risk** —
  gerçek iniş pedinde **%0** isabet (D-295 §2). Bağlamak her kareyi `HEDEF_YOK`'a
  düşürebilir. Karar insandadır.

---

## 5 · 18 Mİ 21 Mİ — SAYI DÜZELTMESİ

Görev metni "18 hüküm satırı" diyordu. `results/sartname_bosluk/rapor.md`'nin hüküm
tablosu **R1–R21 = 21 satırdır**; §3'teki "KRİTİK boşluklar" listesi ise **8** madde.
18 hiçbirine karşılık gelmiyor. Tazelemede **21 satırın hepsi** ele alındı ve **R22**
eklendi → **22**. Sayıyı görevden değil **dosyadan** aldım.

---

## 6 · ÖLÇÜLEMEDİ (dürüstlük kaydı)

- **Üretim rota yolu (`analyze_path`) kuru koşuda** — betik `rota_bul` çağırıyor;
  kod değiştirmeden ölçülemez (T156).
- **SiK 433 MHz seri hattı** — donanım yok; halka 8 yalnız UDP loopback ile GEÇTİ.
- **Gerçek Pixhawk `mpp`** — halka 5 sahte yayınla geçti.
- **Gerçek İKA motoru** — halka 10 SAHİPSİZ.
- **`.engine` derlemesi / Jetson FPS / kamera akışı** — cihaz 30 Eylül'de (D-211 §5);
  `saha_gunu.md`'deki ADIM 1/3/5/9 **hiçbiri bugün koşulmadı**, komutları kılavuzdan
  aynen alındı.
- **`iha_inis_yayinci` ve `ika_nav` için kılavuz komutu** — kılavuzda **YOK** (EKSİK).
  `saha_gunu.md` ADIM 6/8'de bu açıkça işaretlendi; oradaki arayüz kılavuzdan değil,
  modülün `--help` çıktısından **koşularak** alındı.
- **v36'nın DroidCam görüntüsündeki davranışı** — kılavuz §6B'nin kendi kaydı; ölçülmedi.
