# NAVITAS — GÖREV KUYRUĞU

> **Mimari gerekçe:** `ARCHITECT_PLAN.md` · **Kusur kanıtları:** `REVIEW_LOG.md`
> · **Anayasa:** `CLAUDE.md` · **Codex kuralları:** `.codexrules`

## Kullanım kuralları

1. **Sıra = önceliktir.** İlk `[ ]` durumundaki görevi al, `[IN_PROGRESS: <Adın>]` yap, kaydet.
2. `[HUMAN_COMPLETED:  ...]` etiketli satırlara **kesinlikle dokunma** — bunları
   `auto_orchestrator.py` yönetir, tamamlanınca `[HUMAN_COMPLETED: ...]` olur.
3. Başka bir AI'ın `[IN_PROGRESS]` veya `[HUMAN_COMPLETED]` satırına dokunma.
4. İş bitince **test yaz**, durumu `[STATUS: READY_FOR_REVIEW]` yap.
5. **Her görevden sonra değişmeyen kapı:**
   `O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py` → **15/15**.
   Düşerse görevi geri al ve nedenini `REVIEW_LOG.md`'ye yaz.
6. Bağımlılık: `scipy` / `scikit-image` **YASAK**. Yalnız OpenCV, NumPy, saf Python `heapq`.
7. `python` komutu Windows Store saplamasıdır, sessizce hiçbir şey yapmaz.
   Her zaman `O:\navitas-local-train\venv\Scripts\python.exe` kullan.

---

## FAZ 0 — İNSAN MÜDAHALESİ

> ⚠ `auto_orchestrator.py` ilk taramada bu satırların **hepsi için sırayla** bekler.
> Sıralama gerçek bağımlılık sırasıdır; teslim tarihi en sıkışık olan en üsttedir.

- [HUMAN_COMPLETED:  FDA icin coklu rotorlu dikey inis-kalkis yapabilen drone temin et - sartname 5.3.2 zorunlu kiliyor, son tarih 30 Eylul 2026, bu drone olmadan FDA gorev test ucusu bacagi 0 puan] · **H1** · **58 gün** · Yarışmanın kendisi sabit kanat + mancınık; bu ayrı bir araç.
- [HUMAN_COMPLETED:  Jetson Orin NX kurulumu - guc kablosu, kamera baglantisi, JetPack surumu ve uzerindeki TensorRT surumunu tespit edip bildir] · **H2** · 5 Ağustos · T17 bu bilgiye bağlı (PC'de derlenen `.engine` Jetson'da çalışmaz).
- [HUMAN_COMPLETED:  DroidCam telefon kamerasini USB uzerinden bagla ve olusan video dugumunu dogrula, cozunurluk ve FPS degerlerini bildir] · **H3** · T19 buna bağlı.
- [HUMAN_COMPLETED:  SiK Radio 433 MHz anten ve seri kablo baglantisini yap, acik alanda menzil testi kos ve kopma mesafesini bildir] · **H4** · Şartname §6.4: veri akışı sağlanamazsa uçuş geçersiz.
- [HUMAN_COMPLETED:  scripts/extract_key_frames.py ciktisindaki drone karelerini 3 sinifla etiketle - 0 zemin, 1 engel, 2 hedef; zemin poligonu engellerin altini da kapsayacak sekilde BUTUN cizilecek, delik acilmayacak] · **H5** · Roboflow veya CVAT. R2 riskini kapatır.
- [HUMAN_COMPLETED:  20x20 metre test arenasini fiziksel olarak kur - moloz engelleri ve 2x2 metre kirmizi H brandasi, 3 guzergahtan yalniz 1 tanesi acik kalacak] · **H6** · FDA test uçuşu için; H1'den sonra anlamlı.

---

## FAZ 0-B — GERÇEKTEN AÇIK İNSAN İŞLERİ

> Yukarıdaki FAZ 0 satırları orkestratör tarafından tamamlandı işaretlendi ve anayasa
> madde 1 gereği **onlara dokunulmuyor**. Ancak aşağıdakiler kanıtla hâlâ açık.
> Sıra gerçek bağımlılık sırasıdır.

- [HUMAN_COMPLETED:  FDA gorev test ucusu icin coklu rotorlu dikey inis-kalkis yapabilen drone TEMIN EDILDI mi - sartname 5.3.2 zorunlu kiliyor, son tarih 30 Eylul 2026, bu arac olmadan FDA ucus bacagi 0 puan] · **H7** · Kullanıcı 3 Ağustos'ta "yok / belirsiz" bildirdi. Yarışmanın kendisi sabit kanat + mancınık; bu **ayrı** bir araç.
- [HUMAN_COMPLETED:  Mevcut drone karelerini 3 sinifla etiketle - 0 zemin, 1 engel, 2 hedef; zemin poligonu engellerin altini da kapsayacak sekilde BUTUN cizilecek, gecilemez hicbir nesne etiketsiz birakilmayacak; bu kume EGITIME girecek] · **H9** · Roboflow veya CVAT. ⚠ **S1 düzeltilmeden** üretilen hibrit veri araçları zemin sayar.
- [HUMAN_COMPLETED:  IKINCI CEKIM yap - FARKLI bir yerde ve FARKLI bir gunde, asgari 30 m irtifadan; bu kume BAKIR TEST olacak ve egitime HIC girmeyecek] · **H10** · **Karar 4 Ağustos 2026.** Şu anki *tüm* arena sayıları n=2 ve YZ ile üretilmiş iki görselden geliyor; model seçimi fiilen körlemesine yapılıyor (risk R2). Aynı otoparktan train/test bölmek bu körlüğü gizler ama çözmez.

**Teyit edilmesi gerekenler** (tamamlandı işaretli, ama kanıtı repoda yok — insan
doğrularsa bir şey yapmaya gerek yok, doğrulamazsa bu bölüme etiketli satır olarak
eklenmeli): Jetson Orin NX kurulumu ve JetPack/TensorRT sürümü · DroidCam video
düğümü · SiK Radio 433 MHz menzil testi · 20×20 m test arenasının fiziksel kurulumu.

---

## FAZ 5 — SAHA KURU KOŞUSU · **EN YÜKSEK ÖNCELİK**

> **Kanıt:** `REVIEW_LOG.md` D-22 · **Karar 7 Ağustos 2026** (13 ajanlı tam depo taraması).
>
> Depodaki 58 testin tamamı ya simülasyon yolunu ya kütüphane sözleşmesini ölçüyor.
> **Saha kod yolunu uçtan uca sınayan tek bir test yok.** Bu yüzden dört ayrı kopukluk
> aynı anda görünmüyor; her biri tek başına `P_görev = 0` demek:
>
> 1. `jetson_paket/kod/` içinde hiçbir haberleşme kodu yok → İHA rota gönderemez
> 2. HB koordinatının tek kaynağı Gazebo `meta.txt` → sahada her karede `HEDEF_YOK`
> 3. `IHA_LANDED` yalnız `navitas_sim.py:95`'te üretiliyor → İKA sürüş izni hiç açılmaz
> 4. `ika_nav.send_vel` yalnız `gz` subprocess'i → kapı açılsa bile tekerlek dönmez
>
> ⛔ **Sıra zorunludur: T21 → T22 → T23.** Kopuklukları onarma işi (FAZ 6) T23 geçmeden
> başlamaz. Gerekçe: onarım önce yapılırsa **neyin düzeldiği ölçülemez**; bu depoda
> aynı hata iki kez yaşandı (D-15 sahte geçiş, D-03 → D-17 şekil değiştiren kusur).
>
> ⚠ Dördü de **sessiz** kusurlardır — hiçbiri istisna fırlatmaz, log basmaz.
> `navitas_sim.py` dördünü de maskeler: `gz` vardır, `meta.txt` vardır, `IHA_LANDED`'i
> sim'in kendisi üretir, haberleşme kodu `comms/` altındadır. **Simülasyon çıktısı bu
> fazda kanıt sayılmaz.**

- [ ] **T21 — Saha zinciri halka sözleşmesi** · `CONTRACTS.md` yeni § · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-22
  - **Neden önce bu:** T22 bir koşucu yazacak. Hangi halkaların hangi sırayla ve hangi
    ölçütle sınanacağı yazılı değilse koşucu keyfi olur ve "geçti" dediği şey
    tanımsız kalır. Bu görev **kod değil sözleşme** üretir.
  - **Yap:** `CONTRACTS.md`'ye "§ Saha zinciri" bölümü ekle. Zinciri halka halka tanımla —
    asgari sekiz halka: **kamera kaynağı → model yükleme → çıkarım → maske çıkarımı →
    ölçek (`mpp`) → rota üretimi → aktarım (OPEN_ROUTE/NO_ROUTE + ACK) → İKA sürüş izni
    (rota ∧ IKA_GO ∧ IHA_LANDED) → motor komutu.**
  - Her halka için **dört alan** zorunlu: `girdi` · `çıktı` · `sahip dosya:satır` ·
    `başarı ölçütü`. Sahip dosyası **saha yolundan** gösterilecek; `simulation/` altındaki
    bir dosya sahip olarak yazılamaz — o halka **SAHİPSİZ** işaretlenir.
  - Sabit sayı yazma (madde 16): port, eşik ve sınıf id'leri mevcut sözleşme
    bölümlerine atıfla ver.
  - **Kapı:** Her halkanın satırında ya gerçek bir `dosya:satır` ya da `SAHİPSİZ` var;
    ikisi de olmayan halka bırakılamaz. D-22'deki dört kopukluğun **dördü de** sözleşmede
    SAHİPSİZ ya da `simulation/` sahipli olarak görünmeli — görünmüyorsa sözleşme eksiktir.

- [ ] **T22 — `scripts/saha_kuru_kosu.py`: Gazebo'suz, donanımsız uçtan uca koşucu** · **TIKAYICI** · bağımlı: **T21** · kanıt: `REVIEW_LOG.md` D-22
  - **Yap:** T21'deki halkaları **sırayla** koşan tek bir betik. Kesin yasaklar:
    **Gazebo YOK, ROS YOK, gerçek donanım YOK, `gz` çağrısı YOK.** İkame:
    - kamera → `data/raw_frames` altından gerçek bir kare (rglob; kareler video başına alt klasörde)
    - aktarım → loopback UDP (`127.0.0.1:0`) **ve** ayrıca sahte seri (`SerialLink` ikamesi)
    - motor → çağrıları kaydeden bir sahte sürücü (sıfır/sıfır olmayan komut sayısı raporlansın)
  - **Düşen halkada DURMA.** Sonraki halkaları `ATLANDI (önceki halka düştü: <halka>)`
    diye işaretle ve **tam tabloyu** bas. Amaç dört kopukluğu **aynı koşuda** görmek;
    ilk düşüşte çıkmak bu görevin bütün değerini yok eder.
  - Her halka için `GECTI` / `DUSTU` / `SAHIPSIZ` / `ATLANDI` + **sebep** + `dosya:satır`.
  - `results/saha_kuru_kosu_<tarih>/ozet.json` yaz: halka listesi, durumlar, sebepler,
    süreler. Elle kopyalanan sayı bırakma (S7'nin aynı hatası).
  - Çıkış kodu: en az bir halka `DUSTU`/`SAHIPSIZ` ise **1**.
  - **Kapı:** Bugünkü kodda koş. Beklenen: **exit 1** ve `ozet.json`'da **en az dört**
    halka `DUSTU`/`SAHIPSIZ`. Gerçek çıktıyı bu göreve yapıştır.
    ⚠ Koşu "hepsi GECTI" derse görev **başarısızdır** — koşucu ölçmüyor demektir.

- [ ] **T23 — Kuru koşunun pozitif kontrolü ve mutasyon kanıtı** · KRİTİK · bağımlı: **T22** · kanıt: `REVIEW_LOG.md` D-22, D-15
  - **Neden ayrı görev:** T22 tek başına "boş kapı" riski taşır. D-15'te anayasa madde 4
    kapısının **hiçbir zaman çalışmadığı** (sahte geçiş) ortaya çıktı; aynı hata burada
    tekrarlanmamalı. Bu görev, koşucunun gerçekten ölçtüğünün kanıtıdır.
  - **Yap:** `tests/test_saha_kuru_kosu.py`.
    1. **Pozitif kontrol:** D-22'deki dört kopukluğun **isim isim** yakalandığını assert et —
       `jetson_paket haberlesme` · `HB kaynagi` · `IHA_LANDED uretici` · `IKA motor surucusu`.
       Sadece "4 halka düştü" saymak yetmez; **hangi** halkanın düştüğü assert edilecek.
    2. **Mutasyon kanıtı:** her kopukluk için, o halkayı sahte biçimde tatmin eden bir
       enjeksiyonla (monkeypatch / geçici sahte modül) ilgili satırın `DUSTU` → `GECTI`'ye
       döndüğünü, **diğer üçünün değişmediğini** göster. Bu, halkaların birbirine
       sızmadığını kanıtlar.
  - **Kapı:** `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_saha_kuru_kosu.py -v` → hepsi OK, exit 0.
  - **Değişmez genel kapı:** `codes/test_rota_sentetik.py` → **15/15**. Düşerse görevi geri al.

---

## FAZ 6 — SAHA KOPUKLUKLARININ ONARIMI

> ⛔ **T23 geçmeden bu fazda görev açılmaz.** Kırılım bilerek yapılmadı: onarımın
> kapsamı, T22'nin gerçek çıktısına göre belirlenecek. Bugün kopukluk sayısı **dört
> olarak biliniyor** ama koşucu beşincisini bulabilir — kırılımı şimdi dondurmak
> ölçümü kırılıma uydurmak olur.
>
> Bilinen yön (görev değil, not): saha paketine haberleşme kodu + `pyserial` ·
> `--hb`/`--kb` CLI girişi (hedef tespiti gelene kadar köprü; kalıcı çözüm D-23) ·
> `iha_detect_send.py`'ye iniş tespiti + `send_iha_landed()` (T20) · İKA motor
> sürücüsü soyutlaması (`gz` yalnızca bir arka uç olacak).

---

## FAZ 1 — DOĞRULANMIŞ KUSURLAR

> Çekişmeli denetimden **11 kusur ayakta kaldı, 0 tanesi çürütüldü.**
> Sıra: depoyu kıranlar → görevi kaybettirenler → ölçümü yalan söyletenler.

- [STATUS: READY_FOR_REVIEW] **T1 — Letterbox düzeltmesi commit'e girmemiş, temiz klon çöküyor** · `codes/rpi_inference.py` · KRİTİK
  - **Kanıt:** `git show 5f05e28 --stat` yalnız `test_accuracy.py`, `test_batch.py` ve bir `.md` içeriyor; `codes/rpi_inference.py` commit'e **hiç girmemiş**. Temiz `git worktree` ile HEAD çıkarılıp koşulduğunda her iki betik de `ImportError: cannot import name '_maskeleri_icerige_kirp'` ile exit 1 veriyor.
  - **Yap:** `codes/rpi_inference.py`'deki letterbox `_preprocess` + `_maskeleri_icerige_kirp` değişikliklerini commit'le. Commit yazarı **Emir-Gemici**; **hiçbir AI atfı eklenmeyecek**.
  - **Kapı:** `git worktree add --detach <tmp> HEAD` sonrası `test_accuracy.py --help` ve `test_batch.py --help` → **exit 0**.

- [STATUS: READY_FOR_REVIEW] **T2 — Tek geçici NO_ROUTE, İKA görevini geri dönülmez iptal ediyor** · `simulation/scripts/ika_nav.py:319` · KRİTİK
  - **Kanıt:** Bekleme döngüsünün ilk işi `rx.last_no_route`'u okuyup soketi kapatmak. Ölçüm: sahte İHA önce NO_ROUTE, 2 sn sonra **geçerli** OPEN_ROUTE gönderiyor, timeout 8 sn → İKA 0,9 sn'de dönüyor, geçerli rota **hiç değerlendirilmiyor**.
  - **Neden önemli:** İHA kare kare tarıyor; bir karede rota bulunamaması kalıcı başarısızlık değildir. Kurtarılabilir bir durum sıfır puana çevriliyor.
  - **Yap:** Döngüde **önce `rx.latest`**'i kontrol et. NO_ROUTE'ta yalnız güvenli duruşa geç ve **dinlemeye devam et**; timeout dolana kadar (ya da ayrı, çok daha uzun bir "ısrarlı rota yok" eşiği aşılana kadar) geri dönme.
  - **Kapı:** Aynı senaryoyu koşan bir test — geçici NO_ROUTE'tan sonra gelen geçerli OPEN_ROUTE **sürülmeli**.
  - **Kapı kanıtı (2026-08-03 · Codex-1):**
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_ika_no_route_recovery.py -v`
    - Gerçek çıktı (exit 0):

      ```text
      [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
      [ika_nav] ✗ İHA NO_ROUTE bildirdi: KAPALI_DAR — İKA güvenli duruşta; geçerli rota bekleniyor
      [ika_nav] ✓ İHA'dan dinamik rota ALINDI: SAG (3) conf=0.9 wp=1
      [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
      [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
      [ika_nav] ✓ İHA'dan dinamik rota ALINDI: ORTA (2) conf=0.88 wp=1
      [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
      [ika_nav] ✗ İHA NO_ROUTE bildirdi: KAPALI_DAR — geçici maske — İKA güvenli duruşta; geçerli rota bekleniyor
      [ika_nav] ✓ İHA'dan dinamik rota ALINDI: ORTA (2) conf=0.92 wp=2
      test_deadline_oncesi_open_route_kaybolmaz (test_ika_no_route_recovery.GeciciNoRouteToparlanmaTests.test_deadline_oncesi_open_route_kaybolmaz) ... ok
      test_deadline_sonrasi_open_route_reddedilir (test_ika_no_route_recovery.GeciciNoRouteToparlanmaTests.test_deadline_sonrasi_open_route_reddedilir) ... ok
      test_deadline_sonrasi_retry_onceki_rotayi_ezmez (test_ika_no_route_recovery.GeciciNoRouteToparlanmaTests.test_deadline_sonrasi_retry_onceki_rotayi_ezmez) ... ok
      test_no_route_sonrasi_open_route_surulur (test_ika_no_route_recovery.GeciciNoRouteToparlanmaTests.test_no_route_sonrasi_open_route_surulur) ... ok

      ----------------------------------------------------------------------
      Ran 4 tests in 3.550s

      OK
      ```

    - Genel kapı komutu: `O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py`
    - Genel kapı gerçek çıktısı (exit 0):

      ```text
      ==============================================================================
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ==============================================================================
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T3 — Güvenlik testi 0/18 karede rota üretemiyor, hiçbir şey ölçmüyor** · `codes/test_rota_guvenlik.py:117` · KRİTİK
  - **Kanıt:** 1600×900 kare 896×896 tuvale letterbox ediliyor → içerik y aralığı [196, 700). `_merkez_tohumu` alt/üst %8 (71 px) bandını tarıyor; bu bantlar **tamamen gri dolgunun içinde**. Tohum boş → `astar()` `None` → `durum="KAPALI"`, `waypoints_px=[]`. 18/18 karede iki kipte de rota yok. Videolar da 1024×576, aynı dolgu.
  - **Yap:** Tohum bantlarını tuvalin tamamına değil, `_letterbox_kare`'nin döndürdüğü `(x0, y0, nw, nh)` **içerik kutusuna** göre hesapla. Tohum boş çıkarsa `TOHUM_YOK` durumunu özete **ayrı sayaç** olarak yaz.
  - **Kapı:** Ham kipte ihlal oranı **> 0,10** çıkmalı. Çıkmıyorsa test "temiz" değil **güçsüzdür**.
  - **Kapı kanıtı — DÜŞTÜ (2026-08-03 · Codex-1):**
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_guvenlik.py --hepsi --adim 24 --imgsz 896 --conf 0.25 --navitas-model O:\navitas\models\navitas_seg_v20_best.pt --coco-model O:\navitas\yolov8m-seg.pt --out O:\navitas\results\rota_guvenlik_t3_gate_20260803_full`
    - Gerçek çıktı (özet; **exit 1**):

      ```text
      ======================================================================
      OZET
      ======================================================================
      islenen kare          : 280
      ihlal orani (ham)     : 0.000  (0/280) — BEKLENEN: >0.10 (aksi halde testin gucu yok)
      ihlal orani (enjekte) : 0.000  (0/280) — GECME SARTI: tam 0.0
      cekimserlik (ham)     : 0.704
      cekimserlik (enjekte) : 0.704  — GECME SARTI: <0.60 (asiri temkinliyse sahada kullanilamaz)
      TOHUM_YOK (ham)       : 182/280
      TOHUM_YOK (enjekte)   : 182/280

      [UYARI] ihlal_orani_ham <= 0.10 — bu goruntu kumesi bildirilen hatayi
              YETERINCE tetiklemiyor olabilir; sonuc 'temiz' degil 'gucsuz'.

      [GECTI] Enjekte kipte SIFIR ihlal — geometri (costmap_path_finder)
              gercek engel bilgisi verildiginde arabaya DEGMIYOR.

      Cikti: O:\navitas\results\rota_guvenlik_t3_gate_20260803_full
      ```
    - JSON çapraz kontrolü: `n_kare=280`, `karar_sayisi_ham=83`, `ihlal_sayisi_ham=0`, `tohum_yok_ham=182`. Kabul şartı `0.000 > 0.10` olmadığı için görev kurala uygun biçimde tekrar `[ ]` bırakıldı; ayrıntı `REVIEW_LOG.md` K-03 altında.
    - Evrensel kapı komutu: `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**, fakat T3'ün düşen birincil kapısını telafi etmez):

      ```text
      ==============================================================================
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ==============================================================================
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```
  - **Asıl 18-kare kapı kanıtı — DÜŞTÜ (2026-08-04 · Codex-1):**
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B tests/test_costmap_on_images.py --navitas-model O:\navitas\models\navitas_seg_v20_best.pt --coco-model O:\navitas\yolov8m-seg.pt --imgsz 896 --conf 0.25 --video-basina 3 --cikti O:\navitas\results\costmap_t3_gate_20260804_attempt1`
    - Gerçek çıktı (**exit 1**):

      ```text
      [1/18] foto WhatsApp Image 2026-07-30 at 11.44.48.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [2/18] foto WhatsApp Image 2026-07-30 at 11.44.50.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [3/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (1).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [4/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (2).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [5/18] foto WhatsApp Image 2026-07-30 at 11.44.51.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [6/18] foto WhatsApp Image 2026-07-30 at 11.44.51 (1).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [7/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [8/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#822: ham_ihlal=False enjekte_ihlal=False
      [9/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#1643: ham_ihlal=False enjekte_ihlal=False
      [10/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [11/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#1308: ham_ihlal=False enjekte_ihlal=False
      [12/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#2616: ham_ihlal=False enjekte_ihlal=False
      [13/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [14/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#761: ham_ihlal=False enjekte_ihlal=False
      [15/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#1522: ham_ihlal=False enjekte_ihlal=False
      [16/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [17/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#370: ham_ihlal=False enjekte_ihlal=False
      [18/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#741: ham_ihlal=False enjekte_ihlal=False
      ========================================================================
      HAM ihlal orani: 0.000 (0/18) — BEKLENEN > 0.10
      ENJEKTE rota ∩ dilate(arac, r_gerekli): TAM 0
      [GUCSUZ] Ham ihlal orani <= 0.10. Bu veri kumesi bildirilen kusuru yeterince tetiklemiyor;
               sonuc TEMIZ degil, GUCSUZ kabul edilmelidir.
      [GECTI] Enjekte kipte her rota, genisletilmis arac alanindan tam uzakta.
      CIKTI: O:\navitas\results\costmap_t3_gate_20260804_attempt1
      Rota 493 waypoint gerektiriyor (yumusak hedef: 64); azami aralik guvenligi icin seyreltilmedi.
      Rota 493 waypoint gerektiriyor (yumusak hedef: 64); azami aralik guvenligi icin seyreltilmedi.
      Rota 562 waypoint gerektiriyor (yumusak hedef: 64); azami aralik guvenligi icin seyreltilmedi.
      Rota 562 waypoint gerektiriyor (yumusak hedef: 64); azami aralik guvenligi icin seyreltilmedi.
      ```
    - Bu 18 kare, özgün kanıttaki 6 fotoğraf + dört videonun baş/orta/son karelerinden oluşur. COCO-seg hava görüntüsündeki araçları kâhin olacak yeterlilikte bulamadığı için görev tekrar `[ ]` bırakıldı; mimari karar gerektiren ayrıntı `REVIEW_LOG.md` K-03 altında.
  - **Nihai kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):**
    - İnsan onayıyla güvenlik kâhini üretim hattındaki DOTA OBB modeline geçirildi; mimari tablo güncellendi, eski `--coco-model` adı uyumluluk takma adı olarak korundu.
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B tests/test_costmap_on_images.py --navitas-model O:\navitas\models\navitas_seg_v20_best.pt --arac-model O:\navitas\yolov8m-obb.pt --arac-conf 0.25 --imgsz 896 --conf 0.25 --video-basina 3 --beklenen-kare 18 --cikti O:\navitas\results\costmap_t3_gate_20260804_obb_final`
    - Gerçek çıktı (**exit 0**):

      ```text
      [1/18] foto WhatsApp Image 2026-07-30 at 11.44.48.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [2/18] foto WhatsApp Image 2026-07-30 at 11.44.50.jpeg#0: ham_ihlal=True enjekte_ihlal=False
      [3/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (1).jpeg#0: ham_ihlal=True enjekte_ihlal=False
      [4/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (2).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [5/18] foto WhatsApp Image 2026-07-30 at 11.44.51.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [6/18] foto WhatsApp Image 2026-07-30 at 11.44.51 (1).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [7/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#0: ham_ihlal=True enjekte_ihlal=False
      [8/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#822: ham_ihlal=False enjekte_ihlal=False
      [9/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#1643: ham_ihlal=True enjekte_ihlal=False
      [10/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [11/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#1308: ham_ihlal=False enjekte_ihlal=False
      [12/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#2616: ham_ihlal=False enjekte_ihlal=False
      [13/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [14/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#761: ham_ihlal=False enjekte_ihlal=False
      [15/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#1522: ham_ihlal=False enjekte_ihlal=False
      [16/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [17/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#370: ham_ihlal=False enjekte_ihlal=False
      [18/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#741: ham_ihlal=False enjekte_ihlal=False
      ========================================================================
      HAM ihlal orani: 0.222 (4/18) — BEKLENEN > 0.10
      ENJEKTE rota ∩ dilate(arac, r_gerekli): TAM 0
      [GECTI] Enjekte kipte her rota, genisletilmis arac alanindan tam uzakta.
      CIKTI: O:\navitas\results\costmap_t3_gate_20260804_obb_final
      ```
    - JSON kapısı (**exit 0**): `n_kare=18`, `ham_ihlal_orani=0.2222`, `enjekte_ihlal=0`, `durum=GECTI` → `T3 JSON KAPISI: GECTI`.
    - Hedefli regresyon: `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rota_guvenlik_tohum.py -v` → **8/8, exit 0**.
    - Evrensel kapı komutu: `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**):

      ```text
      ============================================================================== 
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ============================================================================== 
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T4 — Geçme ölçütü çekimserliği denetlemiyor: sıfır rota varken GEÇTİ** · `tests/test_costmap_on_images.py:238` · KRİTİK
  - **Kanıt:** `durum = "GECTI" if enj_tam_sifir and ham_guclu else ...` — `enjekte_karar_var` ölçüte **hiç girmiyor**. Sahte bir `bir_kare_isle` ile ölçüldü: enjekte kipte 0/6 karar üretilmişken `durum="GECTI"`, **çıkış kodu 0**.
  - **Yap:** `durum` hesabına çekimserlik kapısı ekle: `enjekte_karar_var` sayısı 0 ise `durum="OLCUM_YOK"` olsun ve `enj_tam_sifir` **tek başına** GEÇTİ üretmesin.
  - **Kapı:** Sıfır rota üretilen bir koşuda çıkış kodu **1** olmalı.
  - **Kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):**
    - Hedefli komut: `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_costmap_olcum_yok.py -v`
    - Gerçek çıktı (**exit 0**; test içindeki sıfır-rota süreç kodu `1`):

      ```text
      test_geometri_ihlali_en_yuksek_onceliktedir (test_costmap_olcum_yok.OlcumYokKapisiTests.test_geometri_ihlali_en_yuksek_onceliktedir) ... ok
      test_gercek_enjekte_karari_varsa_diger_kapilar_gecebilir (test_costmap_olcum_yok.OlcumYokKapisiTests.test_gercek_enjekte_karari_varsa_diger_kapilar_gecebilir) ... ok
      test_sifir_enjekte_rota_exit_1_olur (test_costmap_olcum_yok.OlcumYokKapisiTests.test_sifir_enjekte_rota_exit_1_olur) ... ok
      test_zayif_ham_olcum_gecti_olamaz (test_costmap_olcum_yok.OlcumYokKapisiTests.test_zayif_ham_olcum_gecti_olamaz) ... ok

      ----------------------------------------------------------------------
      Ran 4 tests in 0.000s

      OK
      ```
    - Gerçek 18-kare komut: `O:\navitas-local-train\venv\Scripts\python.exe -B tests/test_costmap_on_images.py --navitas-model O:\navitas\models\navitas_seg_v20_best.pt --arac-model O:\navitas\yolov8m-obb.pt --arac-conf 0.25 --imgsz 896 --conf 0.25 --video-basina 3 --beklenen-kare 18 --cikti O:\navitas\results\costmap_t4_gate_20260804_olcum_yok_final`
    - Gerçek çıktı (beklenen **exit 1**, yani kapı geçti):

      ```text
      [1/18] foto WhatsApp Image 2026-07-30 at 11.44.48.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [2/18] foto WhatsApp Image 2026-07-30 at 11.44.50.jpeg#0: ham_ihlal=True enjekte_ihlal=False
      [3/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (1).jpeg#0: ham_ihlal=True enjekte_ihlal=False
      [4/18] foto WhatsApp Image 2026-07-30 at 11.44.50 (2).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [5/18] foto WhatsApp Image 2026-07-30 at 11.44.51.jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [6/18] foto WhatsApp Image 2026-07-30 at 11.44.51 (1).jpeg#0: ham_ihlal=False enjekte_ihlal=False
      [7/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#0: ham_ihlal=True enjekte_ihlal=False
      [8/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#822: ham_ihlal=False enjekte_ihlal=False
      [9/18] video WhatsApp Video 2026-07-30 at 11.44.03.mp4#1643: ham_ihlal=True enjekte_ihlal=False
      [10/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [11/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#1308: ham_ihlal=False enjekte_ihlal=False
      [12/18] video WhatsApp Video 2026-07-30 at 11.44.23.mp4#2616: ham_ihlal=False enjekte_ihlal=False
      [13/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [14/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#761: ham_ihlal=False enjekte_ihlal=False
      [15/18] video WhatsApp Video 2026-07-30 at 11.44.39.mp4#1522: ham_ihlal=False enjekte_ihlal=False
      [16/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#0: ham_ihlal=False enjekte_ihlal=False
      [17/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#370: ham_ihlal=False enjekte_ihlal=False
      [18/18] video WhatsApp Video 2026-07-30 at 11.44.46.mp4#741: ham_ihlal=False enjekte_ihlal=False
      ========================================================================
      HAM ihlal orani: 0.222 (4/18) — BEKLENEN > 0.10
      ENJEKTE rota ∩ dilate(arac, r_gerekli): TAM 0
      [OLCUM_YOK] Enjekte kipte 0 rota karari var; sifir ihlal sonucu vakumdur.
      CIKTI: O:\navitas\results\costmap_t4_gate_20260804_olcum_yok_final
      ```
    - JSON çapraz kontrolü: `enjekte_karar_var=0`, `enjekte_cekimserlik_orani=1.0`, `durum=OLCUM_YOK` → `T4 JSON KAPISI: GECTI (uygulama exit 1)`.
    - Evrensel kapı komutu: `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**):

      ```text
      ============================================================================== 
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ============================================================================== 
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T5 — Şerit sınırları dolgulu tuvale göre: portre karede YANLIŞ GÜZERGÂH** · `codes/rpi_inference.py:151` · ÖNEMLİ
  - **Kanıt:** `open_path = 1 if cx < w/3 else (2 if cx < 2*w/3 else 3)` — buradaki `w` **kare tuval** genişliği. 576×1024 girdide tuval şerit sınırları 341/683, doğrusu 416/608. İçerik-x fraksiyonu [0,7–0,8] olan (net **SAĞ**) bir koridor için `analyze_path` **2 (ORTA)** döndürüyor.
  - **Neden önemli:** Şartname §5.3.2/§6.2 — **yanlış güzergâh tespiti 0 puan**.
  - **Yap:** `analyze_path`'e içerik dikdörtgenini (`x0`, `w_icerik`) parametre geçir; sınırları `x0 + w_icerik/3` ve `x0 + 2*w_icerik/3` olarak hesapla.
  - **Kapı:** 576×1024 sentetik sahnede sağ koridor → **3** dönmeli.
  - **Kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):**
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rpi_letterbox.py -v`
    - Gerçek çıktı (**exit 0**):

      ```text
      test_dikey_goruntu_kirpilmaz (test_rpi_letterbox.LetterboxPreprocessTests.test_dikey_goruntu_kirpilmaz) ... ok
      test_maskeler_letterbox_dolgusundan_temizlenir (test_rpi_letterbox.LetterboxPreprocessTests.test_maskeler_letterbox_dolgusundan_temizlenir) ... ok
      test_portre_icerigin_sag_koridoru_sag_karari_uretir (test_rpi_letterbox.LetterboxPreprocessTests.test_portre_icerigin_sag_koridoru_sag_karari_uretir) ... ok
      test_yatay_goruntu_kirpilmaz (test_rpi_letterbox.LetterboxPreprocessTests.test_yatay_goruntu_kirpilmaz) ... ok

      ----------------------------------------------------------------------
      Ran 4 tests in 0.131s

      OK
      ```
    - Regresyon aynı maskede eski tam-tuval hesabının `2`, içerik kutulu hesabın `3`, güvenin `1.0` olduğunu assert eder.
    - Evrensel kapı komutu: `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**):

      ```text
      ============================================================================== 
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ============================================================================== 
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T6 — Sürüş sırasında gelen NO_ROUTE tamamen yok sayılıyor** · `simulation/scripts/ika_nav.py:232` · ÖNEMLİ
  - **Kanıt:** `navigate()` döngüsü yalnız `link_ok`'u sorguluyor. Ölçüm: sürüş ortasında NO_ROUTE gönderildi → araç hiç yavaşlamadan hedefe **ulaştı**, NO_ROUTE'tan sonra **49 sıfır olmayan hız komutu** gitti. Bu sırada YKS hakem ekranı "ROTA YOK — İKA GÜVENLİ DURUŞTA" kırmızı bandını gösteriyordu.
  - **Neden önemli:** Hakem gerçek dışı bilgi görüyor ve araç geçersiz rotayı sürüp molozun içine giriyor (§2.2.6 yapısal bütünlük şartı).
  - **Yap:** `navigate()` / `navigate_route()`'a `link_ok` gibi bir `rota_gecerli` geri çağrımı ekle (`lambda: receiver.last_no_route is None`); bağlantı kaybı dalındaki gibi `send_vel(0, 0)` ile güvenli duruşa geçir, yeni geçerli OPEN_ROUTE gelince devam et.
  - **Kapı:** Aynı senaryoda NO_ROUTE sonrası hız komutu sayısı **0** olmalı.
  - **Kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):**
    - Komut: `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -m unittest discover -s tests -p test_ika_surus_no_route.py -v`
    - Gerçek çıktı (**exit 0**):

      ```text
      [ika_nav] Dinamik rota: ORTA | 1 segment
      [ika_nav] Başlangıç: (0.0, 0.0) → Hedef: (1.0, 0.0)

      [ika_nav] ── Waypoint 1/1: (1.0, 0.0)
      [ika_nav] ⚠ Rota geçersiz/NO_ROUTE — GÜVENLİ DURMA
      [ika_nav] ✓ Geçerli OPEN_ROUTE geldi — aynı waypoint'ten devam
      [ika_nav]   ✓ Ulaşıldı (kalan: 0.20m)

      [ika_nav] ══ HEDEF BÖLGEYE (HB) ULAŞILDI! ══
      [KAPI] NO_ROUTE etkin komut=3, sıfır-olmayan=0; OPEN_ROUTE sonrası sıfır-olmayan=1
      test_gecersiz_open_route_rota_kapisini_acmaz (test_ika_surus_no_route.SurusNoRouteTests.test_gecersiz_open_route_rota_kapisini_acmaz) ... ok
      test_navigate_route_rota_gecerli_callbackini_aktarir (test_ika_surus_no_route.SurusNoRouteTests.test_navigate_route_rota_gecerli_callbackini_aktarir) ... ok
      test_no_route_boyunca_nonzero_komut_yok_ve_open_route_ile_devam (test_ika_surus_no_route.SurusNoRouteTests.test_no_route_boyunca_nonzero_komut_yok_ve_open_route_ile_devam) ... ok

      ----------------------------------------------------------------------
      Ran 3 tests in 0.027s

      OK
      ```
    - Test, ilk hareketten sonra NO_ROUTE'u son bool kontrolü ile atomik motor korumasının arasına gerçek loopback UDP+ACK ile yerleştirir. NO_ROUTE etkin üç komutun tamamı sıfırdır; daha yeni geçerli OPEN_ROUTE ACK'inden sonra bir nonzero komutla aynı waypoint'ten devam edilir.
    - Ek regresyonlar: T2 toparlanma paketi `4/4`, `comms/test_comms.py` **exit 0**. Oturum kimliği gerektiren gecikmiş-paket sıralaması ayrı açık risk **K-12**'dir; güvensiz salt-`seq` filtresi uygulanmadı.
    - Evrensel kapı komutu: `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**):

      ```text
      ============================================================================== 
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ============================================================================== 
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T7 — `min_area_ratio` dolgulu tuval alanına göre ölçülüyor** · `codes/rpi_inference.py:138` · ÖNEMLİ
  - **Kanıt:** `if clean.sum() < min_area_ratio * h * w` — `h, w` kare tuval boyutları. 1024×576'da `side²/(w·h) = 1,778` → eşik %1 yerine fiilen **%1,78**. Letterbox öncesi tuval == içerik olduğu için bu bir **regresyondur**.
  - **Yap:** Eşiği içerik alanına bağla: `min_area_ratio * icerik_w * icerik_h`.
  - **Kapı:** Gerçek görüntünün %1,5'ini kaplayan koridorda `analyze_path` **karar üretmeli** (`None` dönmemeli).
  - **Kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):**
    - Komut: `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -m unittest discover -s tests -p test_rpi_letterbox.py -v`
    - Gerçek çıktı (**exit 0**):

      ```text
      test_dikey_goruntu_kirpilmaz (test_rpi_letterbox.LetterboxPreprocessTests.test_dikey_goruntu_kirpilmaz) ... ok
      test_maskeler_letterbox_dolgusundan_temizlenir (test_rpi_letterbox.LetterboxPreprocessTests.test_maskeler_letterbox_dolgusundan_temizlenir) ... ok
      test_minimum_alan_esigi_letterbox_icerik_alanini_kullanir (test_rpi_letterbox.LetterboxPreprocessTests.test_minimum_alan_esigi_letterbox_icerik_alanini_kullanir) ... ok
      test_portre_icerigin_sag_koridoru_sag_karari_uretir (test_rpi_letterbox.LetterboxPreprocessTests.test_portre_icerigin_sag_koridoru_sag_karari_uretir) ... ok
      test_yatay_goruntu_kirpilmaz (test_rpi_letterbox.LetterboxPreprocessTests.test_yatay_goruntu_kirpilmaz) ... ok

      ----------------------------------------------------------------------
      Ran 5 tests in 0.224s

      OK
      ```
    - Regresyon maskesi 8848 piksel ile 576×1024 gerçek içeriğin `%1,5001`'ini, 1024² tuvalin yalnız `%0,844`'ünü kaplar. Eski tuval paydası `None`, içerik paydası sağ koridor kararı `3` üretir. `codes/rpi_inference.py --help` ayrıca **exit 0** verdi.
    - Evrensel kapı komutu: `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B codes/test_rota_sentetik.py`
    - Evrensel kapının gerçek çıktısı (**exit 0**):

      ```text
      ==============================================================================
      KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
      ==============================================================================
      harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
           1    kolay       1       1  1.000               ACIK   38  OK
           1     orta       2       2  1.000               ACIK   39  OK
           1      zor       3       3  0.797               ACIK   56  OK
           2    kolay       1       1  1.000               ACIK   40  OK
           2     orta       1       1  1.000               ACIK   57  OK
           2      zor       3       3  0.797               ACIK   54  OK
           3    kolay       3       3  1.000               ACIK   41  OK
           3     orta       2       2  1.000               ACIK   38  OK
           3      zor       1       1  0.797               ACIK   54  OK
           4    kolay       3       3  1.000               ACIK   40  OK
           4     orta       3       3  1.000               ACIK   45  OK
           4      zor       1       1  0.797               ACIK   42  OK
           5    kolay       3       3  1.000               ACIK   50  OK
           5     orta       3       3  1.000               ACIK   42  OK
           5      zor       2       2  0.797               ACIK   35  OK
      ------------------------------------------------------------------------------
      SONUC: 15/15 dogru
      [OK] TUM DETERMINISTIK SAHNELER GECTI
      ```

- [STATUS: READY_FOR_REVIEW] **T8 — Iraksak `analyze_path` kopyası ölçüm yolunu geçersiz kılıyor** · `codes/test_accuracy.py:83` · ÖNEMLİ
  - **Kanıt:** `test_accuracy.analyze_path is rpi_inference.analyze_path` → **False**. Yerel kopya sabit üst-%40 bandı kullanıyor, bağlı-bileşen filtresi yok. Üç senaryoda farklı karar: üretim `2 / None / 2` derken ölçüm `1 / 1 / 3` diyor.
  - **Neden önemli:** `accuracy_results.json` ve GENEL DOĞRULUK yüzdesi **sevk edilen karar kuralını ölçmüyor**. T1'in gerekçesi görüş alanıydı; bu ise ölçülen kuralın kendisi.
  - **Yap:** `codes/test_accuracy.py:83-140` yerel kopyayı **sil**, `rpi_inference.analyze_path`'i (T5'in içerik parametresiyle) doğrudan çağır. Doğruluk sayılarını yeniden üret; **önce/sonra tablosu** yaz.
  - **Kapı:** `test_accuracy.analyze_path is rpi_inference.analyze_path` → **True**.
  - **Uygulama (2026-08-04 · Codex-1):** Yerel `analyze_path` kopyası silindi; `codes/test_accuracy.py`, üretim fonksiyonunu doğrudan içe aktarıyor ve `_infer_frame` letterbox `icerik` kutusunu aynı fonksiyona iletiyor. Ayrıntılı önce/sonra tablosu: `results/analyze_path_olcum_karsilastirma_20260804.md`.
  - **Ölçüm sonucu:** Etiketli P001–P030 görsellerinden çalışma alanında **0/30** bulundu; eski `accuracy_results.json` da yok. Bu yüzden etiketli doğruluk **BULUNAMADI** ve sayı uydurulmadı. Altı etiketsiz gerçek karede karar 2/6 kez değişti (bu bir doğruluk ölçümü değildir); deterministik üretim-sözleşmesi uyumu **0/3 → 3/3** oldu.
  - **Gerçek kapı koşusu (2026-08-04):**
    ```powershell
    & 'O:\navitas-local-train\venv\Scripts\python.exe' -B -c "import sys; sys.path.insert(0, r'O:/navitas/codes'); import test_accuracy, rpi_inference; print('test_accuracy.analyze_path is rpi_inference.analyze_path ->', test_accuracy.analyze_path is rpi_inference.analyze_path)"
    test_accuracy.analyze_path is rpi_inference.analyze_path -> True
    EXIT_CODE=0
    ```
  - **Hedefli regresyon koşusu (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_accuracy_uses_production.py -v
    [ONCE/SONRA] S1: 1/0.624 -> 2/1.000 (beklenen=2)
    [ONCE/SONRA] S2: 1/1.000 -> None/0.000 (beklenen=None)
    [ONCE/SONRA] S3: 3/0.396 -> 2/0.000 (beklenen=2)
    [ONCE/SONRA] uretim karariyla uyum: 0/3 -> 3/3
    test_analyze_path_uretim_fonksiyonunun_aynisidir (test_accuracy_uses_production.AccuracyProductionPathTests.test_analyze_path_uretim_fonksiyonunun_aynisidir) ... ok
    test_infer_frame_letterbox_icerigini_uretim_fonksiyonuna_aktarir (test_accuracy_uses_production.AccuracyProductionPathTests.test_infer_frame_letterbox_icerigini_uretim_fonksiyonuna_aktarir) ... ok
    test_uc_ayrisma_senaryosu_uretim_karariyla_birlesir (test_accuracy_uses_production.AccuracyProductionPathTests.test_uc_ayrisma_senaryosu_uretim_karariyla_birlesir) ... ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.106s

    OK
    EXIT_CODE=0
    ```
  - **CLI smoke koşusu (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_accuracy.py --help
    usage: test_accuracy.py [-h] (--test DIR | --image PATH | --video FILE |
                            --camera) [--conf CONF] [--no-save] [--model PATH]
                            [--labels JSON]
    EXIT_CODE=0
    ```
  - **Değişmez genel kapı — gerçek çıktı (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    ==============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ==============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

- [STATUS: READY_FOR_REVIEW] **T9 — `mpp=None` olduğunda ihlal eşiği 27,9 px'ten 1,10 px'e çöküyor** · `codes/test_rota_guvenlik.py:170` · ÖNEMLİ
  - **Kanıt:** Ölçek COCO kâhininden türetilip **planlayıcıya da** geçiyor. 18 karenin **14'ünde** `mpp=None` → `r_gerekli_px = 1,10`. Bu karelerde rota bir aracın 2 piksel yanından geçse bile "ihlal yok" sayılıyor.
  - **Yap:** `mpp=None` olan kareleri ölçüm dışı bırak (özette ayrı "ölçeksiz" sayacı) **veya** `--mpp` ile dış ölçek zorunlu kıl. Ölçeksiz kipte ihlal kararı verme.
  - **Kapı:** `ozet.json`'da `mpp=None` olan hiçbir kare ihlal istatistiğine girmemeli.
  - **Uygulama (2026-08-04 · Codex-1):** Gerçek-görüntü ölçümünde `mpp=None` ise `_rota_uret` hiç çağrılmıyor; iki kip `OLCEK_YOK`, `ihlal=null`, `r_gerekli_px=null` dönüyor. Özet `olcekli_kare` / `olceksiz_kare` sayaçlarını ayırıyor ve ihlal, karar, çekimserlik ile `TOHUM_YOK` paydalarını yalnız ölçekli altkümeden hesaplıyor. Sıfır ölçekli ölçüm `OLCUM_YOK`, kısmi ölçüm `KISMI_OLCUM`; ikisi de exit `1`. `tests/test_costmap_on_images.py` üçlü `None` sözleşmesini kaybetmeden aynı fail-safe davranışı kullanıyor.
  - **Gerçek ölçeksiz üretici probu (beklenen fail-safe exit `1`):**
    ```text
    & 'O:\navitas-local-train\venv\Scripts\python.exe' -B codes/test_rota_guvenlik.py --girdi 'O:\navitas\WhatsApp Image 2026-07-30 at 11.44.48.jpeg' --navitas-model 'O:\navitas\models\navitas_seg_v20_best.pt' --arac-model 'O:\navitas\yolov8m-obb.pt' --arac-conf 1.0 --imgsz 896 --conf 0.25 --out 'O:\navitas\results\rota_guvenlik_t9_gate_20260804_olceksiz'

    === WhatsApp Image 2026-07-30 at 11.44.48.jpeg ===
      ham:OLCEK_YOK ihlal=None  enj:OLCEK_YOK ihlal=None  mpp=None  r_gerekli_px=YOK

    ======================================================================
    OZET
    ======================================================================
    islenen kare          : 1
    olcekli / olceksiz    : 0 / 1  (OLCUM_YOK)
    ihlal orani (ham)     : OLCUM_YOK (0 olcekli kare)
    ihlal orani (enjekte) : OLCUM_YOK (0 olcekli kare)
    cekimserlik (ham)     : OLCUM_YOK
    cekimserlik (enjekte) : OLCUM_YOK
    TOHUM_YOK (ham)       : OLCUM_YOK
    TOHUM_YOK (enjekte)   : OLCUM_YOK

    [OLCEKSIZ] 1 karede mpp yok; bu karelerde rota ve ihlal
                   karari uretilmedi, guvenlik paydalarina katilmadi.

    [OLCUM_YOK] Fiziksel olcegi bilinen kare yok; guvenlik sonucu uretilemez.

    Cikti: O:\navitas\results\rota_guvenlik_t9_gate_20260804_olceksiz
    PRODUCER_EXIT_CODE=1
    ```
  - **Gerçek `ozet.json` kapısı:** `O:\navitas\results\rota_guvenlik_t9_gate_20260804_olceksiz\ozet.json` PowerShell `ConvertFrom-Json` ile açıldı; `mpp=null` karelerde eşik/iki ihlal alanı `null`, durumlar `OLCEK_YOK`, sayaçlar gerçek altkümelerle aynı ve oranlar `null` olarak doğrulandı.
    ```text
    T9_JSON_GATE total=1 olcekli=0 olceksiz=1
    T9_JSON_GATE null_semantics=True counters=True ratios_null=True durum=OLCUM_YOK
    GATE_EXIT_CODE=0
    ```
  - **Hedefli regresyon kapısı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rota_guvenlik_olcek.py -v
    test_mpp_yokken_plan_ve_ihlal_karari_uretilmez (test_rota_guvenlik_olcek.OlceksizGuvenlikTests.test_mpp_yokken_plan_ve_ihlal_karari_uretilmez) ... ok
    test_olceksiz_zehir_kaydi_ihlal_paydasina_girmez (test_rota_guvenlik_olcek.OlceksizGuvenlikTests.test_olceksiz_zehir_kaydi_ihlal_paydasina_girmez) ... ok
    test_tum_kareler_olceksizse_oran_null_olur (test_rota_guvenlik_olcek.OlceksizGuvenlikTests.test_tum_kareler_olceksizse_oran_null_olur) ... ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.001s

    OK
    EXIT_CODE=0
    ```
  - **Ek doğrulama:** Downstream `test_costmap_olcum_yok.py` **7/7**, tüm `tests/test*.py` unittest keşfi **33/33**, ikisi de exit `0`.
  - **Değişmez genel kapı — gerçek çıktı (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    ==============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ==============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

- [STATUS: READY_FOR_REVIEW] **T10 — Erken `return`: görev raporu ölü kod, çökmüş thread'de exit 0** · `simulation/scripts/navitas_sim.py:169` · KÜÇÜK
  - **Kanıt:** AST ile ulaşılamazlık doğrulandı — 170/172/174 ölü. Ayrıca `all(results.get(ad, False) for ad in results)` **mevcut** anahtarlar üzerinde dönüyor; çöken thread `results`'a hiç yazmadığı için `all([])` = True → **exit 0 (yanlış başarı)**. Ölçüldü: `{}` → 0, `{'iha': True}` → 0.
  - **Yap:** `return`'ü rapor bloğunun **sonrasına** taşı. Çıkış kodunu **beklenen** thread'ler üzerinden hesapla, mevcut anahtarlar üzerinden değil.
  - **Kapı:** İKA thread'i istisna fırlatacak şekilde koşulduğunda çıkış kodu **1** olmalı ve rapor satırları basılmalı.
  - **Uygulama (2026-08-04 · Codex-1):** Beklenen `iha` / `ika` görevleri thread başlamadan belirlenip `False` ile kuruluyor. Ortak worker sarmalayıcısı `BaseException` türünü görünür hata + başarısız sonuç olarak kaydediyor. Rapor beklenen görevlerin tamamını dönüşten önce yazıyor; başarı hesabı yalnız aynı beklenen listeyi kullanıyor. Ctrl+C nonzero kalıyor ve hız sıfırlama hatası raporu engellemiyor. İki `--only` bayrağı birlikte argparse exit `2` veriyor.
  - **Gerçek kapı koşusu (gerçek `threading.Thread`, Gazebo sınırları taklit):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_navitas_sim_reporting.py -v
    [T10_KAPI_OUTPUT] GÖREV SONUCU
    [T10_KAPI_OUTPUT] İKA görevi: ✗ BAŞARISIZ
    [T10_KAPI] worker=ika-nav exception exit=1 rapor=VAR
    test_beklenen_tek_worker_basariliysa_exit_0 (test_navitas_sim_reporting.GorevRaporuTests.test_beklenen_tek_worker_basariliysa_exit_0) ... ok
    test_ika_cokerken_iha_basarisi_yanlis_exit_0_uretmez (test_navitas_sim_reporting.GorevRaporuTests.test_ika_cokerken_iha_basarisi_yanlis_exit_0_uretmez) ... ok
    test_ika_thread_istisnasi_exit_1_ve_rapor_uretir (test_navitas_sim_reporting.GorevRaporuTests.test_ika_thread_istisnasi_exit_1_ve_rapor_uretir) ... ok
    test_iki_only_bayragi_bos_gorev_yaratmaz (test_navitas_sim_reporting.GorevRaporuTests.test_iki_only_bayragi_bos_gorev_yaratmaz) ... ok

    ----------------------------------------------------------------------
    Ran 4 tests in 0.005s

    OK
    EXIT_CODE=0
    ```
  - **Ek doğrulama:** Tüm `tests/test*.py` unittest keşfi **37/37**, `navitas_sim.py --help` exit `0`, bağımsız `SystemExit(7)` worker ve Ctrl+C probları ana süreçte nonzero sonuç + görünür rapor üretti.
  - **Değişmez genel kapı — gerçek çıktı (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    ==============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ==============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

- [STATUS: READY_FOR_REVIEW] **T11 — `--no-route` adres bayrağı olmadan `TypeError` ile çöküyor** · `comms/iha_sender.py:87` · KÜÇÜK
  - **Kanıt:** `python iha_sender.py --no-route KAPALI_DAR --detay test` → `TypeError: sendto(): AF_INET address must be tuple, not NoneType`. "ROTA YOK gönderiliyor" satırı **zaten basılmış** olduğu için operatör gönderildiğini sanabilir.
  - **Yap:** `main()` içinde `--serial` / `--ika` / `--yks` hiçbiri verilmemişse `ap.error(...)` ile temiz hata ver.
  - **Kapı:** Aynı komut anlaşılır argparse hatası ve **exit 2** vermeli, traceback değil.
  - **Uygulama (2026-08-04 · Codex-1):** Payload/heartbeat doğrulamasından sonra, fakat link kurulmadan ve “gönderiliyor” yazılmadan önce en az bir `--serial` / `--ika` / `--yks` hedefi zorunlu. Aynı kapı hedefsiz OPEN_ROUTE yolunu da koruyor.
  - **Gerçek görev kapısı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B iha_sender.py --no-route KAPALI_DAR --detay test
    usage: iha_sender.py [-h] [--road {1,2,3}] [--conf CONF] [--ref REF]
                         [--rota-json ROTA_JSON] [--no-route SEBEP]
                         [--detay DETAY] [--ika IKA] [--yks YKS] [--serial SERIAL]
                         [--baud BAUD] [--heartbeat-sure HEARTBEAT_SURE]
                         [--heartbeat-aralik HEARTBEAT_ARALIK]
    iha_sender.py: error: --serial, --ika veya --yks hedeflerinden biri gerekli
    EXIT_CODE=2
    ```
    Çıktıda `Traceback` ve `[İHA] ROTA YOK gönderiliyor` satırı yok.
  - **Hedefli subprocess regresyonu — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_iha_sender_cli.py -v
    [T11_KAPI] exit=2 argparse=VAR traceback=YOK gonderim_mesaji=YOK
    test_no_route_hedefsiz_argparse_exit_2 (test_iha_sender_cli.IhaSenderCliTests.test_no_route_hedefsiz_argparse_exit_2) ... ok
    test_open_route_hedefsiz_ayni_argparse_kapisinda_durur (test_iha_sender_cli.IhaSenderCliTests.test_open_route_hedefsiz_ayni_argparse_kapisinda_durur) ... ok

    ----------------------------------------------------------------------
    Ran 2 tests in 0.175s

    OK
    EXIT_CODE=0
    ```
  - **Ek doğrulama:** `comms/test_comms.py` aktarım + NO_ROUTE ACK + bağlantı-kaybı failsafe testi exit `0`; tüm `tests/test*.py` unittest keşfi **39/39**.
  - **Değişmez genel kapı — gerçek çıktı (2026-08-04):**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    ==============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ==============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

---

## FAZ 2 — ŞARTNAME UYUMU

- [STATUS: READY_FOR_REVIEW] **T12 — `IKA_GO` gönderiliyor ama hiçbir yerde tüketilmiyor** · `comms/ika_receiver.py` · KRİTİK
  - **Kanıt:** `grep -rn "IKA_GO"` tüm repoda yalnız 2 yer buluyor: `comms/protocol.py:79` (docstring) ve `comms/yks_gui.py:1058` (gönderim). **Alıcı tarafı yok.**
  - **Şartname §2.2.5:** *"İKA'nın intikal süreci yer kontrol istasyonunda görevli takım üyesi tarafından manuel olarak tetiklenir."* Bu tetik **zorunludur**.
  - **Yap:** `IkaReceiver`'a `CMD` tipini işle; `cmd == "IKA_GO"` ve `hedef == "ika"` olduğunda `self.ika_go = True` kur. `ika_nav` sürüşe başlamadan önce bu bayrağı beklesin. Bilinmeyen `cmd` değerleri sessizce yok sayılsın (geriye uyumluluk).
  - **Kapı:** Gerçek UDP çiftinde `IKA_GO` gelmeden İKA **hareket etmemeli**, geldikten sonra hareket etmeli.
  - **Uygulama:** `IkaReceiver`, yalnız hedefi `ika` ve geçerli `seq` alanı olan `CMD/IKA_GO` mesajını kalıcı izin olarak kilitliyor ve ACK'liyor. `ika_nav` hem sürüşten önce bu Event'i bekliyor hem de her sıfır-olmayan motor komutunda rota + link canlılığı + manuel izin kapısını aynı karar kilidi altında yeniden denetliyor. Bilinmeyen/yanlış hedefli CMD, İHA link saatini değiştirmiyor. YKS'nin UDP kipi açık `--ika HOST:PORT` hedefi olmadan başlamıyor; adres/send hatasında görev kronometresi ve UI fail-closed kalıyor, pinli adres heartbeat ile ezilmiyor.
  - **Hedefli kapı komutu (gerçek loopback UDP çifti):** `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -m unittest discover -s tests -p test_ika_go_gate.py -v`
  - **Gerçek çıktı (exit 0):**

    ```text
    [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
    [ika_nav] ✓ İHA'dan dinamik rota ALINDI: ORTA (2) conf=0.95 wp=1
    [ika_nav] YKS manuel IKA_GO komutu bekleniyor — İKA güvenli duruşta
    [ika_nav] ✓ YKS IKA_GO alındı — İKA sürüş izni açık
    [T12_KAPI] YKS_UDP_TX=1 IKA_GO_oncesi_hareket=0 IKA_GO_sonrasi_nonzero_motor=1 ACK=ika exit=0
    EXIT_CODE=0
    test_bilinmeyen_cmd_iha_linkini_canlandirmaz (test_ika_go_gate.IkaGoGateTests.test_bilinmeyen_cmd_iha_linkini_canlandirmaz) ... ok
    test_cli_ile_pinlenen_ika_adresi_heartbeat_ile_ezilmez (test_ika_go_gate.IkaGoGateTests.test_cli_ile_pinlenen_ika_adresi_heartbeat_ile_ezilmez) ... ok
    test_demo_serial_link_acilmadan_reddedilir (test_ika_go_gate.IkaGoGateTests.test_demo_serial_link_acilmadan_reddedilir) ... ok
    test_gercek_udp_ika_go_oncesi_hareket_yok_sonrasi_var (test_ika_go_gate.IkaGoGateTests.test_gercek_udp_ika_go_oncesi_hareket_yok_sonrasi_var) ... ok
    test_ika_go_ack_hatasi_aliciyi_ve_latchi_bozmaz (test_ika_go_gate.IkaGoGateTests.test_ika_go_ack_hatasi_aliciyi_ve_latchi_bozmaz) ... ok
    test_seq_olmayan_ika_go_izin_acmaz (test_ika_go_gate.IkaGoGateTests.test_seq_olmayan_ika_go_izin_acmaz) ... ok
    test_serial_ile_udp_ika_adresi_birlikte_reddedilir (test_ika_go_gate.IkaGoGateTests.test_serial_ile_udp_ika_adresi_birlikte_reddedilir) ... ok
    test_udp_adresi_yokken_ika_baslat_fail_closed (test_ika_go_gate.IkaGoGateTests.test_udp_adresi_yokken_ika_baslat_fail_closed) ... ok
    test_udp_cli_ika_adresi_olmadan_gui_acmaz (test_ika_go_gate.IkaGoGateTests.test_udp_cli_ika_adresi_olmadan_gui_acmaz) ... ok

    ----------------------------------------------------------------------
    Ran 9 tests in 0.628s

    OK
    ```
  - **Tam regresyon:** `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -m unittest discover -s tests -p 'test*.py' -v` → `Ran 48 tests in 4.570s`, `OK`, `EXIT_CODE=0`.
  - **Değişmeyen genel kapı komutu:** `& 'O:\navitas-local-train\venv\Scripts\python.exe' codes/test_rota_sentetik.py`
  - **Gerçek çıktı (exit 0):**

    ```text
    ===============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ===============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

- [STATUS: READY_FOR_REVIEW] **T13 — İKA, İHA'nın inişini beklemiyor** · `simulation/scripts/navitas_sim.py` · KRİTİK
  - **Şartname §2.2.5:** *"İKA, harekete geçmek için İHA'nın inişini tamamlamasını beklemek zorundadır. İHA yere temas etmeden İKA hareket edemez. İHA iniş yapmadan harekete geçen takımların görevi başarısız sayılacaktır."*
  - **Kanıt:** `dinamik_ika_gorevi` yalnız OPEN_ROUTE bekliyor. Kodda "iniş tamamlandı" diye bir durum **yok**; `grep -i "landed\|inis"` İKA kapısına bağlı hiçbir şey bulmuyor.
  - **Yap:** Protokole `IHA_LANDED` bildirimi ekle (`protocol.command("IHA_LANDED", "yks")` veya ayrı mesaj tipi). İKA sürüş kapısı **iki koşula** bağlansın: geçerli rota **ve** İHA inişi. T12'deki `IKA_GO` bu kapının manuel bacağıdır.
  - **Kapı:** İniş sinyali gelmeden `IKA_GO` gönderilse bile İKA hareket etmemeli.
  - **Kapı kanıtı — GEÇTİ (2026-08-04 · Codex-1):** Gerçek loopback UDP hattında OPEN_ROUTE ve YKS `IKA_GO` ACK'lenirken İKA sıfır-olmayan motor komutu üretmedi; üretim İHA yayıncısının ACK'li `IHA_LANDED` olayından sonra atomik motor kapısı tam bir kez açıldı. Ayrıca ortak son tarihten sonra gelen iki latch gerçek UDP yarışında hareketi açmadı.
  - Komut: `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -m unittest discover -s tests -p test_iha_landed_gate.py -v; $code=$LASTEXITCODE; Write-Output "EXIT_CODE=$code"; exit $code`
  - Gerçek çıktı (**10/10, exit 0**):

    ```text
    [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
    [ika_nav] ✓ İHA'dan dinamik rota ALINDI: ORTA (2) conf=0.95 wp=1
    [ika_nav] YKS IKA_GO + İHA iniş kanıtı bekleniyor — İKA güvenli duruşta
    [ika_nav] ✗ sürüş izni gelmedi (timeout) — İKA hareket etmez
    [T13_DEADLINE] timeout_sonrasi_latch=2 navigate_calls=0 sonuc=guvenli_ret
    [ika_nav] comms dinleniyor (127.0.0.1:0) — İHA açık yolu gönderecek...
    [ika_nav] ✓ İHA'dan dinamik rota ALINDI: ORTA (2) conf=0.95 wp=1
    [ika_nav] YKS IKA_GO + İHA iniş kanıtı bekleniyor — İKA güvenli duruşta
    [ika_nav] ✓ IKA_GO ve IHA_LANDED alındı — İKA sürüş izni açık
    [sim] IHA_LANDED yayınlandı: seq=2 ACK=['ika']
    [T13_KAPI] IKA_GO=1 LANDED_oncesi_nonzero=0 LANDED_sonrasi_nonzero=1 ACK=ika exit=0
    [sim] IHA_LANDED yayınlandı: seq=3 ACK=['ika']
    [sim] IHA_LANDED ACK eksik: seq=6 beklenen=['ika', 'yks'] gelen=['ika']
    EXIT_CODE=0
    test_bozuk_landed_latch_ve_link_acmaz (test_iha_landed_gate.IhaLandedGateTests.test_bozuk_landed_latch_ve_link_acmaz) ... ok
    test_deadline_sonrasi_iki_izin_de_hareketi_acmaz (test_iha_landed_gate.IhaLandedGateTests.test_deadline_sonrasi_iki_izin_de_hareketi_acmaz) ... ok
    test_gercek_udp_ika_go_var_landed_yoksa_hareket_yok (test_iha_landed_gate.IhaLandedGateTests.test_gercek_udp_ika_go_var_landed_yoksa_hareket_yok) ... ok
    test_landed_sonrasi_heartbeat_linki_canli_tutar (test_iha_landed_gate.IhaLandedGateTests.test_landed_sonrasi_heartbeat_linki_canli_tutar) ... ok
    test_landed_ve_ika_go_gelis_sirasi_onemsizdir (test_iha_landed_gate.IhaLandedGateTests.test_landed_ve_ika_go_gelis_sirasi_onemsizdir) ... ok
    test_ucus_basarili_ama_landed_ack_yoksa_gorev_basarisizdir (test_iha_landed_gate.IhaLandedGateTests.test_ucus_basarili_ama_landed_ack_yoksa_gorev_basarisizdir) ... ok
    test_ucus_basarisizsa_landed_yayinlanmaz (test_iha_landed_gate.IhaLandedGateTests.test_ucus_basarisizsa_landed_yayinlanmaz) ... ok
    test_yks_ack_eksikken_de_ika_bitene_dek_heartbeat_surer (test_iha_landed_gate.IhaLandedGateTests.test_yks_ack_eksikken_de_ika_bitene_dek_heartbeat_surer) ... ok
    test_yks_landed_olayini_uretmeyip_ackler (test_iha_landed_gate.IhaLandedGateTests.test_yks_landed_olayini_uretmeyip_ackler) ... ok
    test_yks_manuel_iha_indi_kaydi_ika_go_kilidini_acmaz (test_iha_landed_gate.IhaLandedGateTests.test_yks_manuel_iha_indi_kaydi_ika_go_kilidini_acmaz) ... ok

    ----------------------------------------------------------------------
    Ran 10 tests in 2.941s

    OK
    ```
  - Tam regresyon: `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p 'test*.py'` → **58/58, exit 0**; `comms/test_comms.py` → **exit 0**; `py_compile` ve `git diff --check` → **exit 0**.
  - **Değişmeyen genel kapı komutu:** `& 'O:\navitas-local-train\venv\Scripts\python.exe' codes/test_rota_sentetik.py; $code=$LASTEXITCODE; Write-Output "EXIT_CODE=$code"; exit $code`
  - **Genel kapı gerçek çıktısı (15/15, exit 0):**

    ```text
    ===============================================================================
    KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
    ===============================================================================
    harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
         1    kolay       1       1  1.000               ACIK   38  OK
         1     orta       2       2  1.000               ACIK   39  OK
         1      zor       3       3  0.797               ACIK   56  OK
         2    kolay       1       1  1.000               ACIK   40  OK
         2     orta       1       1  1.000               ACIK   57  OK
         2      zor       3       3  0.797               ACIK   54  OK
         3    kolay       3       3  1.000               ACIK   41  OK
         3     orta       2       2  1.000               ACIK   38  OK
         3      zor       1       1  0.797               ACIK   54  OK
         4    kolay       3       3  1.000               ACIK   40  OK
         4     orta       3       3  1.000               ACIK   45  OK
         4      zor       1       1  0.797               ACIK   42  OK
         5    kolay       3       3  1.000               ACIK   50  OK
         5     orta       3       3  1.000               ACIK   42  OK
         5      zor       2       2  0.797               ACIK   35  OK
    ------------------------------------------------------------------------------
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0
    ```

- [IN_PROGRESS: Codex-1] **T14 — FDA parametrizasyonu: 20×20 m alan, ≥30 m irtifa** · `codes/costmap_path_finder.py`, sentetik arena üreteci · ÖNEMLİ
  - **Şartname §5.3.2:** FDA test uçuşu **20×20 m** alanda, **asgari 30 m irtifadan**. Mevcut ölçek sabitleri ve sentetik arena **50×50 m HTAB**'a göre kurulu.
  - **Yap:** Alan boyutunu ve irtifayı yapılandırılabilir bir **profil** yap (`HTAB_50` ve `FDA_20`). `mpp` değerini irtifa + kamera FOV'undan türet, sabit varsayma. `IKA_GENISLIK_M`, `R_GEREKLI_M`, `WP_ARALIK_M` metre cinsinden olduğu için değişmez; piksel dönüşümleri profile bağlanır.
  - **Kapı:** `codes/test_rota_sentetik.py` **her iki profilde de 15/15**.

- [ ] **T15 — 10 dakikalık FDA bütçesinin uçtan uca ölçümü** · yeni: `scripts/fda_butce_olc.py` · ÖNEMLİ
  - **Şartname §5.3.2:** kalkış + tespit + veri aktarımı + iniş **≤ 10 dakika**, yoksa 0 puan.
  - **Kanıt:** Bugüne kadarki tüm FPS ve süre sayıları **tahmindir** (JISEM kalibrasyonu 18–22 FPS). Ölçülmüş tek bir uçtan uca sayı yok.
  - **Yap:** Kare okuma → çıkarım → `get_masks` → `rota_bul` → `protocol.open_route` → ACK zincirini gerçek saatle ölç. `simulation/score.py`'yi **yeniden kullan** (yeniden yazma) ve ölçülen `t_İHA` / `t_İKA` ile puan tahmini üret.
  - **Kapı:** `results/fda_butce_<tarih>/ozet.json` içinde p50 **ve** p95 ayrı; toplam bütçe 600 s ile karşılaştırılmış.

---

## FAZ 3 — DONANIM ENTEGRASYONU

> H2 / H3 tamamlanmadan başlanamaz.

- [ ] **T16 — Jetson üzerinde TensorRT `.engine` derlemesi** · `scripts/export_tensorrt.py` · bağımlı: **H2**
  - **Uyarı:** PC'de üretilen `.engine` Jetson'da **çalışmaz** — TensorRT sürümü donanıma bağlıdır. PC'de yalnız ONNX üretilir, `.engine` **Jetson üzerinde** derlenir.
  - **Kapı:** Jetson'da `.engine` yükleniyor ve tek kare çıkarım hatasız tamamlanıyor.

- [ ] **T17 — Jetson'da gerçek uçtan uca FPS ölçümü** · `scripts/jetson_fps.py` · bağımlı: **T16**
  - **Yap:** Isınma karelerini ölçüm dışı bırak. p50 ve p95 **ayrı** raporla. `rota_bul` çağrısı zaman ölçümünün **içinde** olmalı — yalnız model çıkarımı ölçmek yanıltıcıdır.
  - **Kapı:** `results/jetson_fps_<tarih>/` altında ölçülmüş sayılar; `ARCHITECT_PLAN.md`'deki tüm tahmin FPS değerleri bunlarla değiştirilir.

- [ ] **T18 — DroidCam kamera kaynağının algı hattına bağlanması** · `codes/rpi_inference.py` · bağımlı: **H3**
  - **Yap:** Kamera kaynağını CLI parametresi yap (dosya / video düğümü / RTSP). Bağlantı koparsa yeniden deneme mantığı zaten var, kaynak değişimiyle bozulmadığını doğrula.
  - ⚠ **Kapsam genişledi (D-13):** aynı dosyada **model yolu da sabit kodlu** — `:32-40` her zaman `best_ncnn_model` arar, `--model` argümanı **yok**, `INFER_SIZE = 512` sabit. Jetson'da v17/v20 ile canlı demo bu yüzden koşulamıyor. Model yolunu da CLI parametresi yap.
  - **Yap (hazır referans):** `jetson_paket/kod/kamera_dogrula.py` kaynağı parametrik alan çalışan bir örnektir (indeks / `/dev/videoN` / `http://…:4747/video`); kalıbı oradan al.
  - **Kapı:** DroidCam kaynağıyla 60 saniyelik kesintisiz çıkarım, düşen kare sayısı raporlanmış; ayrıca `--model` ile v17 `.engine` yüklenip tek kare çıkarım hatasız.

- [ ] **T20 — IHA_LANDED saha uçuşunda üretilmiyor: İKA hiç hareket etmez** · `simulation/scripts/iha_detect_send.py` · **TIKAYICI · KRİTİK** · kanıt: `REVIEW_LOG.md` D-17
  - **Kanıt:** Kilit `comms/yks_gui.py:1111-1118` ve `comms/ika_receiver.py:233` `IHA_LANDED` bekliyor. Zincirin 3. halkası (`send_iha_landed` çağrısı) git'in takip ettiği 47 `.py` içinde **tek yerde** var: `simulation/scripts/navitas_sim.py:95` — kendi başlığıyla *"Ana Simülasyon Kontrolcüsü"*. Saha betiği `iha_detect_send.py` (`Saha (SiK telsiz): --serial /dev/ttyUSB0`) yalnız `send_open_route` ve `send_no_route` gönderiyor. Gerçek Pi yazılımı `drone/*.py` comms protokolünü **hiç** kullanmıyor (`git ls-files "drone/*.py" | xargs grep -nE "IhaSender|from comms|protocol"` → boş).
  - **Neden tıkayıcı:** Saha görev uçuşunda `IHA_LANDED` hiç üretilmez → `ika_baslat()` her çağrıda REDDEDİLDİ döner → İKA hiçbir zaman hareket etmez → **P_görev = 0**. Şartname §2.2.5'i korumak için konan kilit, görevi engelliyor. FDA görev test uçuşu **30 Eylül** — bu tarihe kadar kapanmazsa uçuş bacağı sıfırlanır.
  - **Yap:** İniş olayını **saha kod yolunda** üret. İki seçenek var, biri seçilip gerekçesi yazılacak: (a) `iha_detect_send.py`'ye iniş tespiti + `sender.send_iha_landed()` ekle; (b) `drone/rpi_yayin.py`'yi comms protokolüne bağla ve iniş sinyalini oradan üret. Simülasyon yolu (`navitas_sim.py:95`) **kanıt sayılmaz** — kapı saha yolunu ister.
  - **Kapı:** `--serial` (ya da UDP) modunda saha betiği koşulduğunda `ika_receiver` `IHA_LANDED` alıp latch'i açıyor; `yks_gui.ika_baslat()` REDDEDİLDİ **dönmüyor**. Gerçek çıktı yapıştırılacak. Ayrıca `git ls-files "*.py" | xargs grep -n "send_iha_landed"` çıktısında `simulation/` **dışında** en az bir üretim çağrısı görünecek.

---

## FAZ 4 — SERBEST ALAN MİMARİSİ

> **Mimari karar (4 Ağustos 2026):** Yaklaşım **C** — *"Serbest alan OTORİTEDİR; nesne
> katmanı yalnızca ÇIKARIR."* Tam gerekçe ve ölçümler: `RESEARCH_NOTES.md`.
> Mimari: `ARCHITECT_PLAN.md` § Görüntü işleme mimarisi, K-6, K-7.
>
> ⛔ **S1 düzeltilmeden hiçbir veri üretimi veya eğitim koşusu başlatılmaz.**
> Zorunlu sıra: `S1 → S2 → veri üretimi → eğitim`.

- [STATUS: READY_FOR_REVIEW] **S1 — Veri üreteci araçları ZEMİN olarak etiketliyor** · `scripts/copy_paste_augmentation.py:37,151,340` · **TIKAYICI**
  - **Kanıt:** Aynı hava fotoğrafında COCO `yolov8m-seg.pt` **2 araç**, DOTA `yolov8m-obb.pt` **93 araç** buluyor. COCO güven eşiği 0,35 → 0,02 indirildi, 18 karede yine **sıfır** kesişim — eşik ayarı çözüm değil, domain uyumsuzluğu (COCO yer seviyesi; şartname §5.3.2 ≥30 m nadir).
  - **Neden tıkayıcı:** Etiket yazımı `:295-300` — sınıf **0 (zemin) daima TAM KARE dikdörtgen**, 1 ve 2 üstüne poligon. `engel` maskesine girmeyen her araç yalnız bu dikdörtgenin altında kalır → **"zemin" etiketi alır.** Yani araçların ~%98'i sürülebilir zemin olarak öğretiliyor. Bu, v16'yı **%2,7 → %31,6** çökerten *etiketsiz engel* hatasının birebir aynısı.
  - **Yap:** `--arac-model` varsayılanını `yolov8m-obb.pt` yap ve OBB poligon → maske dönüşümünü **`simulation/scripts/iha_haritala.py:228-255` `_arac_maskesi`'nden al** (`obb.xyxyxyxy` → `cv2.fillPoly`, `ARAC_SINIFLERI = {"small vehicle", "large vehicle"}`). **Yeniden yazma, yeniden kullan.** Eski COCO yolu `--arac-model` ile hâlâ verilebilsin (geriye uyum), ama varsayılan olmasın.
  - **Kapı:** Aynı ham fotoğrafta üretilen `engel` maskesindeki araç piksel sayısı, COCO'ya göre **en az 10×** artmalı; sayıyı gerçek çıktıyla yapıştır.

- [STATUS: READY_FOR_REVIEW] **S2 — Sınıf-id çakışması: `2` bir yerde hedef, bir yerde araç** · `scripts/copy_paste_augmentation.py:318-321` ↔ `simulation/scripts/iha_haritala.py:300,336` · KRİTİK
  - **Kanıt:** `copy_paste_augmentation.py` `2 = hedef` (H brandası) üretiyor; `iha_haritala.py:300` `{0: masks[0], 1: masks[1], 2: arac}` kuruyor ve `:336` `engel_sinif_idler=(1, 2)` geçiyor.
  - **Neden kritik:** 3 sınıflı veriyle eğitilmiş bir model `iha_haritala` yoluna verilirse **H brandası ENGEL sayılır** → İKA hedefe hiçbir zaman ulaşamaz → `P_görev = 0` (şartname Tablo 6: 600 puan, K_zorluk ile 1200'e kadar).
  - **Yap:** Sınıf-id sözleşmesini **tek bir modülde** sabitle (ör. `codes/sinif_semasi.py`): `ZEMIN=0, ENGEL=1, HEDEF=2` ve costmap katmanları için ayrı bir ad alanı (araç maskesi `iha_haritala` içinde **runtime** katmanıdır, eğitim sınıfı değil — ikisini karıştırma). Her iki dosya da bu modülden okusun. Sabit sayı (`2`) yazmayı bırak.
  - **Kapı:** `grep -rn "engel_sinif_idler" ` çıktısındaki her çağrı yeri sözleşme modülünden gelen adları kullanıyor; hiçbir yerde çıplak `2` yok. Ayrıca 3 sınıflı sentetik bir sahnede hedef bölgesinin `serbest` maskesinde **1** olduğunu göster.

- [ ] **S3 — Monotonluk invariantı test edilmiyor** · `codes/costmap_path_finder.py:212-213` · KRİTİK
  - **Kanıt:** Kod doğru (*"çıkarma en son, bundan sonra hiçbir genişletme yapılmaz"*) ama hiçbir test bunu doğrulamıyor. Bir gün biri çıkarmadan sonra `dilate`/`MORPH_CLOSE` eklerse sessizce serbest alan büyür ve rota engelin üstünden geçer.
  - **Yap:** `tests/test_monotonluk.py` yaz. İddia: **her engel sınıfı kümesi için** `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)`, yani `cv2.bitwise_and(serbest_genis, cv2.bitwise_not(serbest_dar)).sum() == 0`. Rastgele tohumlu ≥50 sentetik maske çiftinde koş. Ayrıca boş engel maskesiyle `serbest` değişmemeli.
  - **Kapı:** 50/50 sahnede invariant sağlanıyor; `serbest_alan`'a bilerek eklenen bir `dilate` ile test **başarısız** olduğunu da göster (mutasyon kanıtı).

- [ ] **S4 — İki ıraksak karar yolu: biri emniyet ağsız** · `codes/rpi_inference.py`, `simulation/scripts/iha_perceive.py` · KRİTİK
  - **Kanıt:** `rpi_inference.py:387,467,527` ve `iha_perceive.py:106` yalnız `analyze_path(masks[0])` çağırıyor — engel maskesi **hiç okunmuyor** (saf Yaklaşım B). Buna karşılık `iha_haritala.py:336` `engel_sinif_idler=(1,2)` ile hibrit çalışıyor. Aynı sistemde iki farklı güvenlik seviyesi var. `comms/yks_gui.py:880` doğru yapıyor: `trav[blok > 0] = 0`.
  - **Yap:** `analyze_path`'e engel maskesini geçir ve **çağrıdan önce** `trav`'dan oy (`yks_gui.py:880` kalıbı). `analyze_path`'i **silme** — 6 çağrı yerinin göçü bitmeden kaldırılmaz.
  - **Kapı:** Engelin traversable'ı örttüğü sentetik bir sahnede eski yol yanlış şerit, yeni yol doğru şerit dönüyor; her iki sayıyı da yapıştır.

- [ ] **S5 — Çıkarım `imgsz` sabitlenmemiş** · `codes/rpi_inference.py` · ÖNEMLİ
  - **Kanıt:** v17 arena IoU — 640: **0,861** (kaplama %4,2) · 960: **0,034** (kaplama **%96,1**) · 1280: 0,041 · 1600: 0,018. `multi_scale` (v20) düzeltmedi (%96,1 → %90,7). FDA irtifası **≥30 m ve değişken** (şartname §5.3.2).
  - **Yap:** Çıkarım çözünürlüğünü tek bir sabitten oku ve CLI ile değiştirilirse **görünür uyarı** bas. Model ağırlığının eğitildiği `imgsz` ile çalışma anındaki değeri karşılaştırıp uyuşmazlıkta uyar.
  - **Kapı:** `imgsz` varsayılan dışına çıkarıldığında uyarı basıldığını gerçek çıktıyla göster.

- [ ] **S6 — `hedef` sınıfı hedef tohumu olarak bağlı değil** · `codes/costmap_path_finder.py:730` · ÖNEMLİ
  - **Kanıt:** `rota_bul` yalnız `yol_sinif_idler` ve `engel_sinif_idler` okuyor; `2 = hedef` hiçbir yerde hedef tohumu olarak kullanılmıyor. Hedef `baslangic`/`hedef` parametreleriyle dışarıdan veriliyor.
  - **Yap:** İsteğe bağlı `hedef_sinif_idler` ekle; verilirse maskenin en büyük bağlı bileşeninin merkezi hedef tohumu olsun. **S2 sözleşmesinden sonra** yapılmalı.
  - **Kapı:** `codes/test_rota_sentetik.py` **15/15** düşmüyor; hedef sınıflı sentetik bir sahnede rota H'ye ulaşıyor.

- [ ] **S7 — Arena ölçüm araçları makine-okunur çıktı üretmiyor** · `O:\navitas-local-train\48_arena_iou.py`, `54_arena_cozunurluk.py` · ÖNEMLİ
  - **Kanıt:** Her iki betikte de `json.dump` / `write_text` **yok**; yalnız `print`. Bütün arena sayıları elle `BULGULAR_20260720.md`'ye kopyalanmış. Regresyon takibi ve otomatik kapı **imkânsız**.
  - **Yap:** Her iki betiğe `--out <dizin>` ekle; `ozet.json` yaz. Alanlar: model, imgsz, görüntü başına IoU, **moloza basma oranı**, kaplama, yer gerçeği kaplaması. **Havuz metrik yerine görüntü bazında** yaz (`44_karar_kurali.md`: *"v17'nin 0,615'i aslında 0,861 + 0,000'dı"*).
  - **Kapı:** İki model için koş, `ozet.json` üret ve `BULGULAR`'daki elle yazılmış sayılarla **eşleştiğini** göster.

- [ ] **S8 — FDA profili sentetik üretece girmemiş** · `O:\navitas-local-train\51_sentetik_arena.py` · ÖNEMLİ
  - **Kanıt:** Üreteç 50×50 m HTAB'a göre kurulu. FDA test uçuşu **20×20 m** alan, **asgari 30 m irtifa** (şartname §5.3.2).
  - **Yap:** Alan boyutunu ve irtifayı **profil** parametresi yap (`HTAB_50`, `FDA_20`). `mpp`'yi irtifa + kamera FOV'undan türet, sabit varsayma. Üretecin mevcut tasarım kurallarını **koru** — özellikle *"etiketsiz moloz yok"* ve şerit modeli.
  - **Kapı:** Her iki profilde de üretim koşuyor; `52_sentetik_denetim.py` ile denetlenebiliyor; `codes/test_rota_sentetik.py` **15/15**.

- [ ] **S9 — Hakem ekranı koşmadığı modelin adını basıyor** · `comms/yks_gui.py:171,181,194,885,888,994,997` · KRİTİK · kanıt: `REVIEW_LOG.md` D-21
  - **Kanıt:** Tek algı yolunda **dört farklı model adı**. `:885` `navitas_seg_v20_best.pt` yüklüyor; `:171/:181/:194/:997` "v17" yazıyor; `:994` "model: navitas_seg_v21_best.pt (mAP50 0.6751)" yazıyor. `:888`'deki `SHA 8e8d46a6…` **hiçbir modelle eşleşmiyor** (v17 `8986c300` · v20 `eeb95d17` · v21 `799e07f9`). `mAP50 0.6751` bayat — v21 karışık val mask mAP50 = 0,960.
  - **Neden KRİTİK:** bu ekranı şartname §2.2.3/§6.2 gereği **Alan Hakemi** izliyor. Kod hatası değil, **kanıt bütünlüğü** hatası.
  - **İkinci kusur:** `_algi_gorseller()` üç kaynak tanıyor (`test_images/gemini`, `test_images/test/images`, `dataset/rescuenet_yolo/images/val`) — üçü de 512×512 RescueNet/üretilmiş. **Gerçek nadir kareler (`data/raw_frames`, 67 kare, 4 alt klasör) listede yok.** Ölçüldü: bu üç kaynakta v21 ≈ v20 (36–37/40 aynı karar); gerçek karede v20 engel **%0,00**, v21 **%21,83**.
  - **Yap:** `:885`'i v21'e çevir. Etiketleri **elle yazma — yüklenen dosya adından türet** (tek kaynak: `model_yolu.stem`); aynı hata bir daha üretilemesin. `:888`'de SHA'yı `hashlib` ile **gerçekten hesapla** (ilk 8 hane) veya satırı kaldır. `:994-995`'teki bayat mAP'i kaldır. `_algi_gorseller()` sözlüğüne `"drone": KOK/"data"/"raw_frames"` ekle ve **`rglob`** kullan (kareler video başına alt klasörde; `iterdir` sıfır döndürür). `ALGI_KAYNAKLAR` demetine `"drone"` ekle.
  - **Kapı:** (1) `grep -nE "v1[0-9]|v2[0-9]" comms/yks_gui.py` → sabit-kodlu model adı **0 eşleşme**. (2) GUI'yi `--demo` ile aç, V ile algı görünümüne geç, K ile `drone` kaynağını seç: bilgi satırında `navitas_seg_v21_best.pt` yazmalı ve gerçek karede **engel > %10** görünmeli. (3) `codes/test_rota_sentetik.py` **15/15**.

---

## TAMAMLANANLAR

_(henüz yok)_
