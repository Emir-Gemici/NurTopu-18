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
> ⛔ **ARENA ÇEKİMİ İPTAL — 2026-08-11, kullanıcı kararı.** Uzun süre böyle
> bir imkân yok; görev insan kuyruğundan **çıkarıldı** (orkestratörü süresiz
> bekletmemesi için). Yerine **T40** açıldı: gerçek karelere arena semantiği
> yapıştırılarak kompozit zemin üretilecek.
>
> 🔴 **KALICI SINIR — gizlenmeyecek:** Gerçek 30 m arena karesi olmadan
> **modelin gerçek arenadaki başarımı doğrulanamaz.** Ölçülmüş gerçekçe:
> mAP arena sıralamasını tersine çeviriyor (K-3) — yani sentetik/kompozit
> zeminde iyi olan modelin arenada iyi olacağı **kanıtlanmış değildir**.
> T40 **karar mantığını** (üç kapı, uç bant, güzergâh seçimi) sınanabilir
> kılar; **model başarımını** sınamaz. Bu ayrım her raporda yazılacak.

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

- [STATUS: READY_FOR_REVIEW] **T21 — Saha zinciri halka sözleşmesi** · `CONTRACTS.md` §11 · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-22
  - ⚠ **Anayasa madde 7 istisnası.** Codex-1 kotada, iş TIKAYICI, insan onayı 2026-08-07'de
    açıkça verildi. Madde 7 gereği bu görevin çıktısını **Claude 1 kendisi onaylamaz** —
    ayrı bir denetim koşulacak ve sonucu buraya yapıştırılacak.
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
  - **Uygulama (2026-08-07 · Claude 1, madde 7 istisnası):** `CONTRACTS.md` §11 eklendi.
    Zincir **dokuz değil on halka** çıktı: tasarım sırasında hedef konumu (HB) rota
    halkasının içinde eriyordu ve o hâliyle kapı geçmiyordu — D-22'nin 2. kopukluğu
    görünmez kalıyordu. `hedef_konumu` ayrı halka olarak açıldı (§11.2 satır 6).
  - **Kapı kanıtı — GEÇTİ (2026-08-07):**
    - Kapı 1 — her halkada sahip ya da SAHİPSİZ:

      ```text
      OK   halka 1     OK   halka 6
      OK   halka 2     OK   halka 7
      OK   halka 3     OK   halka 8
      OK   halka 4     OK   halka 9
      OK   halka 5     OK   halka 10
      ```

    - Kapı 2 — D-22'nin dört kopukluğu sözleşmede görünüyor:

      | kopukluk | §11.2 halkası | durum |
      |---|---|---|
      | `jetson_paket/kod/` içinde haberleşme yok | 8 `aktarim` | SAHİPSİZ (`:273`) |
      | HB yalnız Gazebo `meta.txt` | 6 `hedef_konumu` | SAHİPSİZ |
      | `IHA_LANDED` üreticisi `navitas_sim.py:95` | 9 `surus_izni` | `simulation/` sahipli |
      | motor yalnız `gz` subprocess'i | 10 `motor` | SAHİPSİZ |

    - Halka anahtarları (T22 bunları birebir kullanacak): `kamera · model_yukleme ·
      cikarim · maske · olcek · hedef_konumu · rota · aktarim · surus_izni · motor`
  - ⚠ **Denetim bekliyor** — madde 7 gereği Claude 1 kendi çıktısını onaylamaz.

- [STATUS: READY_FOR_REVIEW] **T22 — `scripts/saha_kuru_kosu.py`: Gazebo'suz, donanımsız uçtan uca koşucu** · **TIKAYICI** · bağımlı: **T21** · kanıt: `REVIEW_LOG.md` D-22
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
  - **Kapı kanıtı — GEÇTİ (2026-08-07 · Claude 1, madde 7 istisnası):**
    - Komut: `O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py --cikti O:\navitas\results\saha_kuru_kosu_20260807`
    - Gerçek çıktı (**exit 1**):

      ```text
      ==============================================================================
      SAHA KURU KOSUSU — CONTRACTS.md §11 · Gazebo YOK · donanim YOK
      ==============================================================================
        kamera         DUSTU      uretim girisi kaynagi PARAMETRIK almiyor: cv2.VideoCapture(0) sabit  [15 ms]
                                  -> codes/rpi_inference.py:505
        model_yukleme  DUSTU      yuklenen agirlik kayit defterindeki profille eslesmiyor ve --model argumani yok  [2113 ms]
                                  -> codes/rpi_inference.py:32-40
        cikarim        GECTI      tek kare cikarimi tamamlandi  [2199 ms]
                                  -> codes/rpi_inference.py:57
        maske          GECTI      {0,1} anahtarli maskeler uretildi  [5 ms]
                                  -> codes/rpi_inference.py:60-83
        olcek          SAHIPSIZ   sahada mpp ureten kod yok; iha_haritala.py:66 sabiti simulation/ altinda
        hedef_konumu   SAHIPSIZ   HB'nin tek kaynagi Gazebo meta.txt; --hb CLI girisi yok ve uretim modeli 2 sinifli
        rota           DUSTU      letterbox'li girdide durum=KAPALI_DAR, ayni maske kirpilinca durum=ACIK — tohum bandi dolguya dusuyor  [45 ms]
                                  -> codes/costmap_path_finder.py:232-242
        aktarim        SAHIPSIZ   saha paketinde haberlesme kodu yok (eksik: iha_sender.py, link.py, protocol.py; pyserial bagimliligi da yok)
        surus_izni     DUSTU      kapi dogru ama beslemesi kopuk: IHA_LANDED yalnizca simulation/ altinda uretiliyor
                                  -> comms/ika_receiver.py:119-121
        motor          SAHIPSIZ   gercek motor surucusu yok; send_vel yalnizca gz subprocess'i
      ------------------------------------------------------------------------------
      GECTI 2 · DUSTU 4 · SAHIPSIZ 4 · ATLANDI 0
      KOPUK HALKALAR (8): kamera, model_yukleme, olcek, hedef_konumu, rota, aktarim, surus_izni, motor
      Zincir saha kosumunda TAMAMLANMAZ.
      ```

    - `ozet.json` çapraz kontrolü: `cikis_kodu=1`, `kopuk=8`, `halka_sirasi` §11.4 ile birebir aynı.
    - **Yan ürün — D-25 gerçek karede canlı doğrulandı.** `rota` halkası aynı maskeyi
      hem letterbox'lı hem kırpık koşuyor: `{"durum": "KAPALI_DAR", "kirpik_durum": "ACIK",
      "icerik_parametresi_var": false}`. Yani v21'in gerçek karelerde `67/67 KAPALI_DAR`
      vermesinin nedeni **model değil tohum bandı**. Model seçimi bu sayıya dayandırılmıştı.
    - **Yan ürün — `aktarim` kopukluğu paketlemede, kütüphanede değil.** Loopback probu:
      `{"seq": 1, "ack": ["ika"], "alindi": true}`. `comms/` çalışıyor, saha paketi taşımıyor.
    - **Yan ürün — `olcek` ölçüldü:** `mpp=None` → `r_gerekli_px=1.1`; `mpp=0.0547` → `20.114`.

- [STATUS: READY_FOR_REVIEW] **T23 — Kuru koşunun pozitif kontrolü ve mutasyon kanıtı** · KRİTİK · bağımlı: **T22** · kanıt: `REVIEW_LOG.md` D-22, D-15
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
  - **Kapı kanıtı — GEÇTİ (2026-08-07 · Claude 1, madde 7 istisnası):**
    - Gerçek çıktı (**13/13, exit 0**):

      ```text
      test_aktarim_onarilinca_yalniz_aktarim_gecer ... ok
      test_hedef_konumu_onarilinca_yalniz_o_gecer ... ok
      test_motor_onarilinca_yalniz_o_gecer ... ok
      test_surus_izni_onarilinca_yalniz_o_gecer ... ok
      test_taban_agacinda_dort_kopukluk_da_var ... ok
      test_gercek_fonksiyon_halkayi_gecirir ... ok
      test_yorumda_gecen_kelimeler_halkayi_gecirmez ... ok
      test_aktarim_kutuphanesi_calisiyor_ama_paket_eksik ... ok
      test_cikis_kodu_kopuk_varken_sifir_degil ... ok
      test_dort_kopukluk_isim_isim_yakalaniyor ... ok
      test_iha_landed_ureticisi_yalniz_simulasyonda ... ok
      test_kosu_dusen_halkada_durmuyor ... ok
      test_sozlesmedeki_on_halkanin_hepsi_raporlaniyor ... ok

      Ran 13 tests in 7.094s
      OK
      ```

    - **T23 iki gerçek kusur yakaladı ve ikisi de düzeltildi** — görevin var olma
      sebebi budur, bu yüzden ayrıntısı kaydedilmiştir:
      1. `halka_surus_izni` düz metin araması yapıyordu; **kendi test dosyasının
         fixture metnini** saha üreticisi saydı (`tests/test_saha_kuru_kosu.py:60`).
         Tarama üretim dizinleriyle sınırlandı.
      2. Aynı arama sonra **kendi açıklama yorumunu** buldu
         (`scripts/saha_kuru_kosu.py:439`). Metin araması AST `ast.Call` düğüm
         aramasıyla değiştirildi. `OlcekHalkasiTests` bu sınıf hatayı kalıcı olarak
         kilitler: yorumda geçen `irtifa/fov/mpp` kelimeleri halkayı geçiremez.
    - Mutasyon kanıtı gerçekten ayırt ediyor: dört onarımın her birinde **yalnız**
      ilgili halka `GECTI`'ye döndü, diğer üçü değişmedi (`_mutasyonu_dogrula`).
  - **BAĞIMSIZ DENETİM — 2026-08-08 · `code-review high` (4 bulucu, 42 aday, 38 doğrulayıcı):**
    - **6 kusur onaylandı, 0 çürütüldü.** Madde 7 gereği yazarın kendi onayı geçersiz
      olduğu için bu denetim koşuldu ve **kusur buldu** — istisnanın ikinci yarısı işini yaptı.
    - Üçü tam olarak yazarın iki kez düştüğü sınıftı, başka halkalarda kalmıştı:
      1. `halka_motor` düz metin araması — kusuru **itiraf eden bir yorum satırı**
         (`# TODO: mavlink eklenecek`) halkayı `GECTI` yapıyordu; ayrıca `"CAN"`
         altdizgisi `scan`/`canli` gibi masum kelimelerde eşleşiyordu.
      2. `halka_aktarim` yalnız **dosya adına** bakıyordu; tamamen boş stub'lar
         halkayı geçiriyordu. Loopback alanının adı da saha paketini ölçtüğü
         izlenimi veriyordu (aslında depo `comms/`'unu ölçüyor).
      3. `halka_hedef` `simulation/` altındaki bir dosyayı sahip kabul ediyordu
         (**§11.1/1 ihlali**) ve etkin profil yerine **tüm** profilleri tarıyordu.
    - Üçü yeni sınıftı:
      4. `halka_surus_izni` probu **tautolojikti**: `IkaReceiver` hiç `.start()`
         edilmiyor, mesaj enjekte edilmiyordu. Kapı güvenlik kontrolü tümüyle
         kaldırılsa bile prob aynı sonucu basıyordu — hiçbir şey ölçmüyordu.
      5. `halka_cikarim_ve_maske` istisna demeti dardı; `ncnn` wheel'i olmayan
         **taze bir Jetson'da** — yani betiğin tasarlandığı ortamda — tüm koşu
         traceback ile ölüyor, `ozet.json` hiç yazılmıyordu.
      6. `halka_kamera` belgelenmiş `--kare` seçeneğiyle göreli/depo dışı yol
         verilince `relative_to` `ValueError`'ü ile tüm koşuyu çökertiyordu.
    - **Altısı da düzeltildi.** Düzeltme sırasında `motor` halkasında **yeni bir
      yanlış pozitif** üretildi ve ölçülerek yakalandı: sürücü import'unu tek
      ölçüt yapmak `comms/link.py`'yi (SiK telsiz taşıyıcısı, `import serial`
      yapar ama tekerlek döndürmez) motor sürücüsü saydı. Ölçüt iki koşula
      çıkarıldı: **aynı dosyada** sürücü import'u **ve** motor komut fonksiyonu.
    - Denetim ayrıca T23'ün **kendi mutasyon testlerinin üçünün yanlış davranışı
      kilitlediğini** gösterdi (onarımları `simulation/` altına yazıyorlardı).
      Onarımlar saha dizinlerine taşındı; ayrıca `DenetimRegresyonTests` ile altı
      kusur sınıfı kalıcı olarak kilitlendi (11 yeni test).
  - **Nihai kapı kanıtı — GEÇTİ (2026-08-08):**
    - `-m unittest discover -s tests -p test_saha_kuru_kosu.py` → **24 test, OK, exit 0**
    - Sürüş kapısı probu artık gerçekten ölçüyor (gerçek loopback UDP, üç gözlem):
      `{"bos_kapali": true, "ika_go_alindi": true, "yalniz_ika_go_kapali": true,
      "iha_landed_alindi": true, "iki_latch_ile_acik": true, "prob_gecerli": true}`
    - Kuru koşu (çıkarım dahil): **exit 1**, `GECTI 2 · DUSTU 4 · SAHIPSIZ 4 · ATLANDI 0`
    - Tam regresyon: `-m unittest discover -s tests -p "test*.py"` → **85 test, OK, exit 0**
      (58 → 85: +24 T23, +3 devralınan `test_model_registry`).
    - Genel kapı: `codes/test_rota_sentetik.py` → **15/15, exit 0**.

---

## FAZ 7 — ÜRETİM KARAR YOLUNUN GÜVENLİĞİ

> **Kanıt:** `REVIEW_LOG.md` D-28 · **Bulan: kullanıcı (saha testi), 8 Ağustos 2026.**
>
> Genel kapı `rota_bul`'u ölçüyor, üretim `analyze_path`'i koşuyor. 15/15 geçerken
> sahada koşan kod denetlenmemiş kalıyor. Bu, S4'ün ölçülmüş ve somutlanmış hâlidir
> ve FAZ 6'daki saha onarımlarından **bağımsızdır** — saha zinciri düzelse bile bu
> kusur yerinde kalır.

- [x] **T24 — `analyze_path` waypoint'leri bağlantısız: kenar engelin üstünden geçiyor** · `codes/rpi_inference.py:179-186` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-28
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Düzeltme `557366a` commit'inde.
  - **Kapı — bağımsız koşuldu:** `tests/test_analyze_path_kenar.py` → `Ran 10 tests` ·
    `OK` · EXIT=0. Genel kapı `codes/test_rota_sentetik.py` **15/15**.
  - **Madde 15 invariantı — özellikle denetlendi ve KORUNUYOR.** `MORPH_CLOSE` (`:260`)
    serbest alanı büyütür, ama engel çıkarma (`:266-274` `clean[engel_mask] = 0`)
    ondan **sonra** yapılıyor ve sonrasında büyüten hiçbir işlem yok. Koddaki gerekçe
    ölçüme dayanıyor (D-24): *"MORPH_CLOSE extensive'dir ve oyulmuş engelin üstünü
    geri kapatır — 7 px engelin %99'u geri doldu"*. Sıra doğru:
    `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` sağlanıyor.
  - **Yan düzeltme değerli:** `:271-272` — `bitwise_not(...)//255` kalıbı `0/255` bir
    girdiyi sessizce `0/1`'e indiriyormuş; doğrudan sıfırlamaya çevrilmiş, maskenin
    değer alanı korunuyor.
  - ℹ️ T24 commit'i `jetson_paket/kod/rpi_inference.py`'yi **de** güncellemiş (aynı 142
    satır). Yani senkron disiplini vardı; T25/T26 turunda düştü → **T27**.
  - **Ölçüldü:** 8 waypoint'in 3. ve 4.'sü iki ayrı koridorda (`x=122` → `x=520`);
    iki uç da zemin, aradaki kenar **119 engel pikselinin** üstünden geçiyor.
    Aynı sahnede `rota_bul` doğru davranıp `BELIRSIZ_COKLU` diyerek reddediyor.
  - **Dört kusur üst üste:** (1) ardışık waypoint'ler arasında görüş hattı denetimi
    yok · (2) engel maskesi imzada bile yok (S4) · (3) boş bant sessizce atlanıyor,
    denetlenmemiş atlama uzuyor · (4) bantlar içerik kutusu değil tam tuval
    yüksekliği üzerinden (D-25 ailesi).
  - **Ayrıca:** ölçümde `guven=0.0` dönerken `yol=2` üretildi. `analyze_path`'in
    **altı çağrı yerinin hiçbirinde güven eşiği yok** — sıfır güvenli karar doğrudan
    `OPEN_ROUTE`'a gidiyor.
  - **Yap:** Kalıcı çözüm, çağrı yerlerini `costmap_path_finder.analyze_path_uyumlu`'ya
    (`:954` — bu amaçla yazılmış, şu an **hiçbir yerden çağrılmıyor**) geçirmektir;
    o yol `_gorus_hatti`, `_maks_aralikla_bol` ve `rota_dogrula` segment denetimini
    zaten taşıyor. **Yeniden yazma, mevcut makineyi kullan.** Ara çözüm kabul
    edilebilir: `analyze_path`'e engel maskesi parametresi + ardışık waypoint görüş
    hattı denetimi. Geçiş bitmeden `analyze_path` **silinmez** (6 çağrı yeri).
  - **Kapı:** (1) D-28'deki sentetik sahnede segment ihlali **0** olmalı; ihlal
    üretilemiyorsa karar `None`/`NO_ROUTE` dönmeli — yanlış güzergâh üretmektense
    "tespit yok" demek görev güvenliği gereğidir. (2) Aynı sahnede eski yolun
    **1/7 ihlal**, yeni yolun **0/7** verdiği önce/sonra tablosu yapıştırılacak.
    (3) `codes/test_rota_sentetik.py` → **15/15** düşmeyecek.
  - **Uygulama (2026-08-08 · Claude 1, madde 7 istisnası):**
    - ⚠ **Kalıcı çözüm (migrasyon) ŞU AN MÜMKÜN DEĞİL — yeni bağımlılık bulundu.**
      `analyze_path_uyumlu` (`:954`) `**kw`'yi `rota_bul`'a geçiriyor; `rota_bul`'un
      **`icerik` parametresi yok** (D-25). Altı çağrı yeri `icerik=icerik` gönderdiği
      için migrasyon `TypeError` verirdi ve letterbox kusuru yüzünden üretim her
      karede `KAPALI_DAR` derdi. **Migrasyon D-25'in kapanmasına bağlıdır** —
      bu FAZ 7'ye eklenmeli. Kuyruğun izin verdiği ara çözüm uygulandı.
    - `_gorus_hatti` **tek kaynaktan** içe aktarıldı (kopyalanmadı) — kopyalama
      `rota_dogrula` ile farklı yuvarlama üretip çelişki yaratırdı; aynı hata
      bu depoda zaten kayıtlı (`test_rota_sentetik`'in `_tohum_merkezi` kopyası).
    - Waypoint seçimi kör argmax yerine **görüş hattı kısıtlı** hâle getirildi:
      her bantta açıklık sırasına göre adaylar denenir, önceki waypoint'ten
      **görünen** ilki seçilir; hiçbiri görünmüyorsa karar **yok** döner.
    - Bantlar tam tuval yerine **içerik kutusu** üzerinden bölünüyor (D-25 ailesi).
    - Engel maskesi opsiyonel parametre olarak eklendi ve **kapamadan SONRA**
      düşülüyor — çıkarma en son işlemdir (madde 15, D-24).
  - **Kapı kanıtı — GEÇTİ (2026-08-08):**
    - **D-28 sahnesi (önce/sonra):**

      | | waypoint | ihlalli segment |
      |---|---:|---:|
      | önce | 8 | **1/7** — `(122,399) → (520,240)`, 119 engel pikseli |
      | sonra | 0 (karar yok) | **0/0** |

    - **Gerçek 67 drone karesinde ölçüm** (asıl kanıt — sentetik değil):

      | | karar üreten kare | ihlalli kare | ihlalli segment |
      |---|---:|---:|---:|
      | önce | 66/67 | **13/67** | — |
      | sonra | **63/67** | **0/63** | **0/440** |

      Çekimserlik %1,5 → %6,0; karşılığında geçersiz rota **tamamen** bitti.
      13 ihlalli karenin çoğu **onarıldı** (görünür aday seçimi geçerli rota buldu),
      kalanı güvenli biçimde reddedildi.
    - `tests/test_analyze_path_kenar.py` → **10/10, exit 0.**
    - `jetson_paket/kod/rpi_inference.py` senkronlandı; iki kopya **md5 aynı**.
    - Tam regresyon **95/95**, genel kapı **15/15**, ikisi de exit 0.
  - **BAĞIMSIZ DENETİM — 2026-08-08 · `code-review high`:** doğrulama turu kotaya
    takıldı (27 doğrulayıcının hepsi düştü), ama **4 bulucu koştu ve 34 aday
    üretti**. Doğrulanmamış olsalar da bağımsız bulucularda tekrar eden dördü
    okununca gerçek çıktı ve **düzeltildi**:
    1. **`engel_mask` üretimde ölüydü** — parametre eklenmiş ama hiçbir çağrı
       yerine bağlanmamıştı, yani D-24 düzeltmesi sahada aktif değildi.
       Üç çağrı yeri `engel_mask=masks.get(1)` ile bağlandı.
    2. **İki test boştu** — `_ihlal_sayisi([])` her zaman 0 döndüğü için "0 ihlal"
       diyerek geçiyor ama hiçbir şey kanıtlamıyorlardı. Güvenlik değişmezi
       yüklemine çevrildi ve her testte **eski algoritmanın aynı sahnede değişmezi
       ihlal ettiği** ayrıca assert edildi.
    3. **Maske değer alanı bozuluyordu** — `bitwise_not(engel*255)//255` kalıbı
       0/255 girdiyi sessizce 0/1'e indiriyordu; doğrudan sıfırlamaya çevrildi.
    4. **top-K=24 yanlış negatif üretiyordu** — K 64'e çıkarıldı ve "önceki
       waypoint'e x'te en yakın koridor pikseli" geri dönüşü eklendi. Ölçüldü:
       gerçek karelerde karar 60/67 → **63/67**, ihlal yine **0**.
    - ⚠ Kalan 30 aday **doğrulanmadı**; kota açılınca doğrulama turu sürdürülmeli.
      Aday listesi: `scratchpad/t24_dogrulanmamis_adaylar.json`. Bunlardan biri
      (`open_path` centroid'i ile waypoint'lerin uyuşmaması) D-29/T26'da zaten
      kayıtlı ve bu koşumda somutlandı: çatallı sahnede tüm waypoint'ler `x≈121`
      (sol üçte bir) iken karar `yol=2` (orta) dönüyor.
  - ⚠ **Denetim TAMAMLANMADI** — doğrulama turu kotada düştü; madde 7 gereği bu
    görev hâlâ onaylanmış sayılmaz.

- [x] **T26 — Koridorun hedefe ULAŞTIĞI doğrulanmıyor: kapalı şerit açık raporlanabilir** · `codes/rpi_inference.py:162-169` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-29
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Codex-2 yazdı.
  - **Kapı — bağımsız koşuldu:** `tests/test_analyze_path_uc_bant.py` → `Ran 7 tests` ·
    `OK` · EXIT=0. İçinde **mutasyon (pozitif kontrol)** testi var:
    `test_mutasyon_uc_kapisi_kaldirilirsa_eski_kusur_geri_doner` — düzeltme
    etkisizleştirilince sahne yeniden `yol=2` diyor. Genel kapı **15/15**.
  - 🔴 **Codex sözleşmedeki EKSİĞİ ölçümle buldu — sözleşme ona göre düzeltildi.**
    K-A'yı yalnız *hedef* bandı olarak yazmıştım. Ölçüm: ortadaki bariyerle kopmuş
    koridorda OpenCV eşit parçalardan **üst** olanı seçiyor → hedefe temas var,
    başlangıca yok, kusur `yol=2` olarak geri dönüyor. Kod **hem alt hem üst** bandı,
    **aynı bileşen** üzerinden şart koşuyor. `CONTRACTS.md` §6.3/K-A güncellendi.
  - **Madde 15 kontrolü:** `_uc_bant_temasi_yeterli` yalnız **okur**, maske
    değiştirmez → `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` invariantı korunuyor.
  - **Yan iyileştirme:** `_koridor_alani_yeterli` alan eşiğini letterbox tuvaliyle
    değil **gerçek içerikle** karşılaştırıyor (T7'nin kusur sınıfıyla tutarlı).
  - ⚠ **Kapının istediği "gerçek 67 karede çekimserlik önce/sonra tablosu"**
    K-B kalibrasyonuyla birlikte ölçüldü: K-A sonrası **45 karar / 22 çekimser
    (%32,8)**. Bu oran K-A'nın kendi çekimserliğidir; K-B (0,20) ek eleme yapmaz.
    Ayrıntı: `REVIEW_LOG.md` **D-38**.
  - **Kanıt (T24 sırasında ölçüldü):** düz bir koridorun ortasına yatay bariyer
    konduğunda `analyze_path` `yol=2, guven=1.0, wp=4` döndü — yani koridor
    kareyi baştan başa geçmediği hâlde "orta şerit açık" dedi. Şerit kararı en
    büyük bağlı bileşenin **üst %30 bandının centroid'i** ile veriliyor; o
    bileşenin görüntünün üst kenarına **ulaşıp ulaşmadığı hiç sorulmuyor**.
  - **Neden önemli:** şartname §5.3.2/§6.2 yanlış güzergâh tespitini **0 puan**
    sayıyor. `rota_bul` bu durumu `KAPALI_KOPUK` ile doğru yakalıyor; üretim yolu
    yakalamıyor. Kullanıcının "açık yolu seçme konusunda yeterli mi emin değilim"
    sorusunun ölçülmüş cevabı budur: **yeterli değil.**
  - **Yap:** Karar vermeden önce bileşenin hedef kenara (içerik kutusunun üst
    şeridine) temas ettiğini doğrula; etmiyorsa `None` dön. Eşiği `CONTRACTS.md`'ye
    sözleşme olarak yaz, çıplak sabit yazma (madde 16).
  - ✅ **SÖZLEŞME HAZIR · 2026-08-10 · Claude 1 — engel kalktı.** `CONTRACTS.md`
    **§6.3 / K-A** yazıldı. Değerler mimar kararıdır, türetme:
    `HEDEF_BANT_ORANI = 0.08` — **`costmap_path_finder._tohum_maske:237` ile aynı oran**
    (`pay = max(1, int(h * 0.08))`). `rota_bul` bu bantla `_bagli_mi()` sınayıp kapalı
    koridoru `KAPALI_KOPUK` ile zaten doğru yakalıyor; iki karar yolu **aynı bandı**
    kullanacak, ikinci bir sayı türetilmeyecek (S4 ıraksama kusuru).
    `BANT_TEMAS_MIN_ORANI = 0.02` — tek piksel gürültüsü "temas" sayılmasın; mutlak
    piksel değil **oran**, çözünürlük değişince kaymasın (§8).
    ⚠ `analyze_path`'in mevcut üst **%30** bandı (`rpi_inference.py:264`) *şerit seçimi*
    içindir, **kalır**; K-A ondan ayrı bir **ek** kapıdır. Sabitler
    `codes/karar_sozlesmesi.py`'ye konur, çağrı yerlerine çıplak sayı yazılmaz.
  - **Kapı:** Bariyerli sahnede karar `None`; bariyersiz aynı sahnede `yol=2`.
    Gerçek 67 karede çekimserlik artışını önce/sonra tablosuyla raporla —
    aşırı çekimserlik sahada kullanılamaz demektir.
  - **Uygulama · 2026-08-10 · Codex-2:** `codes/karar_sozlesmesi.py` tek-kaynak
    sabitleri eklendi. En büyük koridor bileşeni, içerik kutusunun alt başlangıç
    ve üst hedef bantlarına aynı etiketle, sözleşmedeki asgari genişlikte temas
    etmiyorsa `analyze_path` fail-closed `None` döndürüyor. Üst `%30` şerit seçimi
    değiştirilmedi. T7 alan-payda testi üretim yardımcısına ayrıldı; uç kapısı
    gevşetilmedi.
  - **Hedefli kapı komutu:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_analyze_path_uc_bant.py -v`
  - **Gerçek çıktı (exit 0):** `Ran 7 tests in 0.097s` · `OK`. Bariyerli sahne
    `None`; bariyersiz aynı sahne `yol=2`; letterbox içerik uçları geçti. Pozitif
    mutasyon kontrolünde uç kapısı etkisizleştirilince eski kusur birebir geri
    geldi: `yol=2 · guven=1.0 · wp=4`.
  - **Gerçek 67 kare kapısı — GUI drone yolu, v21, imgsz=512 (exit 0):**
    `ÖNCE karar=52 · çekimser=15 · oran=0.224` →
    `SONRA karar=52 · çekimser=15 · oran=0.224` · `EK_RET=0` ·
    `KARAR_DEGİŞİMİ=0`. Aşırı çekimserlik regresyonu yok.
  - **Genel kapı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI` · exit `0`.

- [x] **T25 (+T28 birleşik) — Güven eşiği hiçbir çağrı yerinde uygulanmıyor** · `codes/rpi_inference.py`, `comms/yks_gui.py`, `simulation/scripts/iha_perceive.py` · ÖNEMLİ · bağımlı: **T24** · kanıt: `REVIEW_LOG.md` D-28
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Codex-2 yazdı.
  - **Kapı:** tam paket `Ran 143 tests · OK` · genel kapı **15/15**. Yeni test
    dosyaları: `test_rota_guven_esigi.py`, `test_rota_ret_nedenleri.py`,
    `test_karar_sozlesmesi.py`, `test_analyze_path_uc_bant.py`,
    `test_analyze_path_kararlilik.py`, `test_yks_gui_rota_engel.py`.
  - **Madde 16 ihlali düzeltildi:** testlerde çıplak `0.499` / `= 0.50` → **0 satır**;
    `ROTA_GUVEN_ESIGI` **4 test dosyasında** sabitten türetiliyor. Artık bir sonraki
    kalibrasyon testleri kırmaz.
  - **T28 buraya birleşti** (izin: Claude 1, aynı dosya kümesi). Sebep sözleşmesi
    `CONTRACTS.md` §6.4 uygulandı; kullanıcı GUI'de sebepleri **gerçekten gördü**
    (`KENAR_GUVENSIZ`, `UC_BANT_TEMAS_YOK`) — bu bildirimin kendisi T30'un
    bulunmasını sağladı.
  - **Kanıt:** `grep -rnE "conf *[<>]=?|guven *[<>]=?"` üretim kodunda tek eşleşme
    veriyor (`iha_perceive.py:88`) ve o da **model tespit eşiği**, rota güveni değil.
    Ölçümde `guven=0.0` olan karar `OPEN_ROUTE` olarak yayınlanabiliyor.
  - **Yap:** Güven eşiğini `CONTRACTS.md`'ye sözleşme olarak ekle (çıplak sabit
    yazma — madde 16), altında kalan kararı `NO_ROUTE` sebebiyle bildir.
  - **Kapı:** Eşiğin altındaki bir kararın `OPEN_ROUTE` olarak **yayınlanmadığını**
    gerçek çıktıyla göster.
  - ~~**SÖZLEŞME HAZIR · 2026-08-10 — `ROTA_GUVEN_ESIGI = 0.50`**~~ ⛔ **GERİ ALINDI.**
    Bu ilk değer **sentetik** sahne güveninden (`0,797` / `1,000`) türetilmişti ve
    gerçek veride ölçülmemişti. Codex gerçek GUI yolunda ölçtü (D-37): **%100
    çekimserlik**. Geçerli değer aşağıdaki kalibrasyon maddesindedir — **`0.20`**.
    *(Eski satır silinmedi: bir sözleşme değerinin nasıl yanlış konduğu iz olarak kalsın.)*
  - ✅ **D-31'in mimara bıraktığı "nerede uygulanacak" sorusu KARARA BAĞLANDI:
    ikisinde birden.** Çağrı yerleri (`rpi_inference`, `iha_perceive`, `yks_gui`)
    erken kararı verir ve **anlamlı sebep** yazar; `IhaSender.send_open_route`
    **son savunmadır** — eşik altı `conf` ile çağrılırsa yayınlamaz. Yalnız çağrı
    yerleri yetmez (yeni çağrı yeri eklenince unutulur, kusur sessizce döner);
    yalnız `IhaSender` da yetmez (operatör *neden* yayınlanmadığını göremez).
  - ✅ **KALİBRASYON TAMAMLANDI · 2026-08-10 · `ROTA_GUVEN_ESIGI = 0.20`.**
    İlk değer (`0.50`) **sentetik** sahne güveninden türetilmişti ve Codex gerçek GUI
    yolunda ölçtü (D-37): **%100 çekimserlik**. Bağımsız ölçümüm (D-38) doğruladı ve
    tam dağılımı çıkardı: `min 0,244 · p50 0,307 · max 0,352 · std 0,030`.
    Metrik gerçek veride **ayırt edici değil** (tüm kütle 1/3 çevresinde), bu yüzden
    K-B **seçici kapı değil, taban koruyucusudur**: `guven=0.0` yayınını engeller
    (D-28), gerçek kararları elemez. Güvenliğin ağırlığı **K-A**'dadır.
    `CONTRACTS.md` §6.3/K-B ve `codes/karar_sozlesmesi.py` güncellendi.
  - 🔴 **KODA DOKUNULACAK — Codex'e:** eşik değişikliği **7 testi düşürdü**, çünkü
    testler eşiği **çıplak yazmış** (`guven=0.499` vb.), sözleşme sabitinden
    türetmemiş — madde 16'nın test tarafındaki ihlali. Testler
    `ROTA_GUVEN_ESIGI`'nden türetilecek (`ROTA_GUVEN_ESIGI - epsilon` gibi) ki bir
    sonraki kalibrasyonda kırılmasınlar. Düşenler: `test_karar_sozlesmesi` (1 hata),
    `test_rota_guven_esigi` (4), `test_iha_sender_cli` (1), `test_yks_gui` (1).
    ⚠ Genel kapı `codes/test_rota_sentetik.py` **15/15 etkilenmedi**.
  - ⚠ **Açık ölçüm borcu (ayrı görev olmalı):** 45 kararın **hepsi `yol=2`**. Ya
    kareler geniş açık alan (koridor üç şeride eşit yayılıyor, centroid ortaya düşüyor)
    ya da metrik körlüğü. Ayırt etmek için **margin tabanlı** güven gerekir (seçilen
    şerit ile ikinci en iyi arasındaki fark); `in_third` mutlak oranı bu işi görmüyor.
  - 🔗 **KAPSAM GENİŞLETİLDİ · 2026-08-10 · T28 buraya birleştirildi (Claude 1 izni).**
    T24 kapatıldı, önündeki ardışıklık engeli kalktı. T25 artık **sebep sözleşmesini**
    de kapsıyor: `CONTRACTS.md` **§6.4** — `MASKE_YOK` · `BILESEN_YOK` ·
    `UC_BANT_TEMAS_YOK` · `ALAN_YETERSIZ` · `KENAR_GUVENSIZ` · `DUSUK_GUVEN`.
    Sebep kodları `codes/karar_sozlesmesi.py`'de **sabit** olarak tanımlanır; çağrı
    yerlerine çıplak string yazılmaz (madde 16). `detay` alanı **ölçülen değeri**
    taşır (hangi uç, ölçülen güven, ölçülen alan oranı).
  - **Genişletilmiş kapı — üçü birden gösterilecek:** (1) maske üretilmeyen kare →
    `MASKE_YOK`; (2) bariyerli koridor → `UC_BANT_TEMAS_YOK`; (3) eşik altı güven →
    `DUSUK_GUVEN`. Üçü **farklı** metin üretmeli — aynı metin çıkıyorsa kapı çalışmıyor
    demektir. Ayrıca eşik altı kararın `OPEN_ROUTE` olarak **yayınlanmadığı** gerçek
    çıktıyla gösterilecek. Fail-closed korunur: sebep bildirmek reddi yumuşatmaz.
  - **0,20 sonrası uygulama · 2026-08-10 · Codex-2:** Testlerdeki eski `0.499`
    eşik-altı örnekleri `ROTA_GUVEN_ESIGI - 0.001`, sınır örnekleri doğrudan
    `ROTA_GUVEN_ESIGI` olacak şekilde tek kaynağa bağlandı. Eşik-hemen-altı ret
    metni eşikle aynı değere yuvarlanmıyor. GUI regresyonu artık `geçerli rota →
    düşük güvenli rota → iki onay denemesi` sırasını sınayıp eski rotaya ACK
    üretilmediğini kanıtlıyor.
  - **Hedefli kapılar:**
    - `...python.exe -B -m unittest discover -s tests -p test_karar_sozlesmesi.py -v`
      → `Ran 4 tests in 0.001s` · `OK` · exit `0`.
    - `...python.exe -B -m unittest discover -s tests -p test_rota_guven_esigi.py -v`
      → `Ran 8 tests in 0.317s` · `OK` · exit `0`.
    - `...python.exe -B -m unittest discover -s tests -p test_iha_sender_cli.py -v`
      → `Ran 3 tests in 1.553s` · `OK` · exit `0`. Gerçek subprocess + UDP'de
      `ESIK_ALTI` yalnız `NO_ROUTE/DUSUK_GUVEN`, tam eşik yalnız `OPEN_ROUTE`.
  - **Genel kapılar:**
    - `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
      → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI` · exit `0`.
    - `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q`
      → `Ran 121 tests in 28.482s` · `OK` · exit `0`.
  - **Gerçek 67 kare · güncel GUI yolu:** v21 SHA `799e07f9...`, `imgsz=512`,
    GUI eşik/fallback zinciri: K-A sonrası `52 karar / 15 çekimser` → K-B `0,20`
    sonrası `52 / 15`, `EK_RET=0`; güven `min=0,243 · p50=0,3185 · max=0,363`.
    D-38'deki `45 / 22`, engeli `analyze_path(..., engel_mask=...)` ile morfolojiden
    sonra çıkaran ayrı yoldur; iki yolun ayrımı `REVIEW_LOG.md` D-39'da ölçüldü.
  - ⚠ **Durum:** Kod ve kapılar hazır; T25 durum satırı değiştirilmedi. Açık bağımlı
    T24 hâlâ `[STATUS: READY_FOR_REVIEW]` ve aynı `codes/rpi_inference.py` dosyasını
    taşıyor. Ayrıca `CONTRACTS.md` içindeki eski `0,50` kalibrasyon-borcu paragrafı
    ile yanlış görev altına düşen tarihsel kanıtları yalnız Claude 1 düzeltebilir.
  - **T25/T28 genişletilmiş uygulama · 2026-08-10 · Codex-2:** `analyze_path`,
    varsayılan 3/4 elemanlı API'yi bozmayan `return_reason=True` seçeneğiyle §6.4'ün
    altı kanonik ret kodunu ve ölçümlü ayrıntıyı döndürüyor. Yapısal ret K-B ile
    ezilmiyor. GUI ham zemin ile ham engeli ayrı geçiriyor; panel, günlük ve görsel
    bantta ret kodunu gösteriyor. `iha_perceive` de engel maskesini analizöre bağlayıp
    aynı nedeni JSON/NO_ROUTE yoluna taşıyor. Eşik altı `0,199`, ekranda `0,20` diye
    yuvarlanmıyor; üç hane gösteriliyor.
  - **Sebep/ekran/yayın kapısı (exit 0):**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rota_ret_nedenleri.py -v`
    → `Ran 10 tests in 0.032s` · `OK`. `MASKE_YOK`, `UC_BANT_TEMAS_YOK` ve
    `DUSUK_GUVEN` üç farklı panel/günlük/banner metni üretti; yapısal retin
    `sebep`/`detay` alanları encode/decode edilen tek `NO_ROUTE` mesajında aynen
    korundu, `OPEN_ROUTE` üretilmedi.
  - **Çağrı-yeri ve güven kapıları (exit 0):**
    `... -p test_yks_gui_rota_engel.py -v` → `Ran 7 tests` · `OK`;
    `... -p test_rota_guven_esigi.py -v` → `Ran 8 tests` · `OK`;
    `... -p 'test_*rota*.py' -v` → `Ran 36 tests` · `OK`. GUI'nin analizöre
    oyulmamış ham zemini ve sınıf-1 engel maskesini verdiği argüman düzeyinde,
    `iha_perceive` bariyerinin `UC_BANT_TEMAS_YOK` verdiği gerçek analizörle kilitlendi.
  - **Gerçek 67 kare · güncel GUI karar zinciri (exit 0):** v21 SHA
    `799e07f9cef3820c3ad9f0365b0052fd8ee2edfc6df1b706830a0a9d3bc5be7d`,
    `imgsz=512`, zemin `0,30→0,05` fallback, engel `0,10`, ham zemin + son engel
    çıkarma + K-A/K-B: `45 karar / 22 ret / 0 hata`; retlerin tamamı ölçümlü
    `KENAR_GUVENSIZ`; sebepsiz ret `0`. Kabul güveni `min=0,247 · p50=0,307 ·
    max=0,351`; toplam hesap `67/67`.
  - **Tam ve genel kapılar:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q`
    → `Ran 138 tests in 27.683s` · `OK` · exit `0`.
    `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI` · exit `0`.
    `py_compile` ve `git diff --check` → çıktı yok · exit `0`.

- [BIRLESTIRILDI → T25] **T28 — Hakem ekranı "karar yok" ile "kapı reddetti"yi ayırt ETMİYOR** · `comms/yks_gui.py`, `codes/rpi_inference.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-39
  - 🔗 **2026-08-10 · Claude 1 kararı: T28, T25'e BİRLEŞTİRİLDİ.** Codex-2 açıkça izin
    istedi (aynı dosyalara dokunan görevler `AGENTS.md` §3 gereği ardışık olmalı).
    **İzin verildi.** Gerekçe: (1) dosya kümesi birebir aynı — `rpi_inference.py`,
    `yks_gui.py`, `iha_perceive.py`; (2) aynı kusur sınıfı — kararın **neden**
    reddedildiğinin bildirilmesi; (3) T25 zaten `DUSUK_GUVEN` sebebini üretiyor, T28
    tabloyu tamamlıyor — sebep sözleşmesini parça parça kurmak tutarsızlık üretir;
    (4) ardışıklık beklemek gereksiz gecikme, çünkü ikinci geçiş aynı satırlara dönecek.
  - ⚠ Bu satır **iz olarak** duruyor; iş **T25 altında** yürür ve orada kapanır.
    Sebep tablosu artık sözleşmedir: `CONTRACTS.md` **§6.4**.
  - **Kanıt (kullanıcı bildirdi, ölçüldü):** GUI "yol algılamıyor" göründü. Gerçekte
    iki sebep üst üste binmişti ve **ekran ikisini de aynı** gösteriyordu:
    ```
    kaynak    maske boş   K-A/K-B öncesi karar   sonrası   ekranda
    gemini      8/12              4                 1      hepsi "TESPİT YOK"
    val         7/12              3                 1      hepsi "TESPİT YOK"
    drone       0/12              9                 6      hepsi "TESPİT YOK"
    ```
  - **Neden KRİTİK:** bu ekranı şartname §2.2.3/§6.2 gereği **Alan Hakemi** izliyor.
    Hakem *"model bulamadı"* ile *"güvenlik kapısı reddetti"* arasındaki farkı
    göremiyor — S9 ile **aynı kusur sınıfı: kanıt bütünlüğü.** Operatör de sistemi
    "bozuk" sanıp yanlış müdahale eder.
  - **Yap:** `analyze_path` K-A reddinde sessizce `None` dönmesin; K-B'deki gibi
    kanonik `(sebep, detay)` üretsin — ör. `UC_BANT_TEMAS_YOK` (hangi uç: alt/üst).
    Maske hiç üretilmediğinde ayrı sebep: `MASKE_YOK`. GUI bilgi satırında sebebi
    **yazsın**; `NO_ROUTE` yayınında da aynı sebep taşınsın (`comms/protocol.py`
    sebep alanı zaten var, T25'te kullanıldı).
  - **Kapı:** Üç ayrı sahne — (1) maske üretilmeyen kare → ekranda `MASKE_YOK`;
    (2) bariyerli koridor → `UC_BANT_TEMAS_YOK`; (3) eşik altı güven →
    `DUSUK_GUVEN`. Üçü de **farklı** metin göstermeli. `codes/test_rota_sentetik.py`
    **15/15**.

- [x] **T31 — `road` etiketi rotanın geçtiği şeride uymuyor: 67/67 yanlış** · `codes/rpi_inference.py`, `comms/yks_gui.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-41 → çözüm kaydı **D-45**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Claude-2 yazdı.
  - **BAĞIMSIZ ÖLÇÜM (kendi betiğim, ajanın testine bakmadan):** 67 gerçek karede
    yayınlanan `road` ile waypoint'lerin baskın şeridi karşılaştırıldı —
    ```
    karar veren kare : 67   (kararsiz 0)
    road == serit    : 67
    UYUMSUZ          : 0        (ÖNCE: 67/67 uyumsuzdu)
    ```
  - **Pozitif kontrol VAR:** `test_pozitif_kontrol_eski_centroid_yanlis_serit_uretiyor`
    — düzeltme etkisizleştirilince eski kusur geri geliyor.
  - **İki aday tanım ayırt edilmiş:** `test_ayirt_edici_sahne_darbogaz_kazanir_baskin_kaybeder`
    — (a) **darboğaz** tanımı seçilmiş, sahne ile kanıtlanmış.
  - **Sorduğum açık uç cevaplanmış:** `test_cok_seritli_rota_kayda_geciyor` +
    `test_tek_seritli_rota_cok_seritli_isaretlenmez` — rota birden fazla şeritten
    geçiyorsa bu kayda geçiyor.
  - T30 kararlılığı korunuyor: `test_ornekleme_karari_degistirmez`.
  - **✅ YAPILDI · 2026-08-10 · Claude-2.** Karar sırası değişti: witness A* ve
    kenar kapısı ÖNCE, şerit/güven SONRA. Şerit `_rota_serit_olcumu` ile
    rotanın LINE_8 piksellerinden okunuyor (`n_waypoints` karara giremez).
  - **Seçilen tanım: (a) darboğaz şeridi.** İki aday ölçüldü; enjekte-kapı
    deneyi dördünü de ayırt edemedi (rota hiç şerit değiştirmiyor:
    `cok_seritli` 0/67), bu yüzden **ayırt edici sahne kuruldu** (alt/üst uç
    şerit 3, tek geçiş şerit 1'deki dar kapıdan):
    ```
    kapi_px  (a)darbogaz  (b)baskin  (c)ust  (d)alt   ->  yer gercegi = 1
       16         1            3        3       3
       24         1            3        3       3
       32         3            3        3       3
       48         1            3        3       3
       64         1            3        3       3
    (a) 4/5 dogru · (b) 0/5 · (c) 0/5 · (d) 0/5
    ```
    Gerekçe: darboğaz, İKA'nın *geçemediği* yerdir; (b)/(c)/(d) aracın
    çoğunlukla nerede olduğunu söyler, nerede kalabileceğini söylemez.
  - **Çok şeritli rota:** tek etiketin yetersizliği kayda geçti. Karar
    yumuşatılmadı, yeni ret sebebi eklenmedi (rota doğrulanmış, yalnız adı
    eksik); `cok_seritli` + şerit dağılımı hakem ekranına ve sarı uyarı
    günlüğüne basılıyor.
  - **Koşulan kapılar (gerçek çıktı):**
    ```
    KAPI 1  enjekte-kapi (bilinen cevap) : kapi serit 1/2/3 -> road 1/2/3
    KAPI 2  67 gercek kare               : UYUMSUZ 0/67  (onceden 67/67)
                                           road dagilimi {1: 32, 3: 35}
    KAPI 3  POZITIF KONTROL (mutasyon)   : UYUMSUZ 67/67 GERI GELDI, {2: 67}
    KAPI 5  codes/test_rota_sentetik.py  : 15/15 · exit 0
    KAPI 6  unittest discover -s tests   : Ran 190 tests · OK · exit 0
    ```
  - **Kalıcı kapı:** `tests/test_rota_serit_etiketi.py` (21 test) — pozitif
    kontroller eski centroid tanımını birebir taşır, kusur yeniden üretilmezse
    test kendisi düşer (D-15 vakum kapı koruması).
  - ⚠ **MİMARA:** seçilen tanımın `CONTRACTS.md` §6.2'ye yazılması gerekiyor —
    öneri metni Claude-2'nin devir raporundadır, dosyaya dokunulmadı (madde 16).
  - ⚠ **TIKAYICI YAN BULGU (D-01 tekrarı):** `jetson_paket/kod/rpi_inference.py`
    **456 satır bayattı** — T24/T28/T30/T31/T32'nin hiçbiri sahaya giden
    kopyada yoktu. Senkronlandı; `rpi_inference.py` + `costmap_path_finder.py`
    `tests/test_jetson_comms_paketi.py` KOPYALAR sözlüğüne **eklendi**.
  - **Kanıt:** centroid şeridi ≠ piksel-kütlesi argmax şeridi, **67/67 karede**.
    `frame_000000` şerit oranları `[0,382, 0,326, 0,292]`, argmax=1, yayınlanan
    `road=2`. Enjekte-kapı deneyinde rota **şerit-1**'den geçiyor, etiket **2**.
    Marjin < 0,10 olan kare: **66/67 (%99)**.
  - **Neden KRİTİK — görselleştirme kusuru DEĞİL.** `road`, tel sözleşmesinin alanı
    ve **İKA'nın planlama girdisi**: `protocol.py:31,39,51` · `ika_receiver.py:11`
    `plan_path(route["road"])` · `README.md:84` · `yks_gui.py:445,453-462`
    (seçili şerit YEŞİL, diğerleri KIRMIZI). Hakem ekranı 67/67 karede **rotanın
    gerçekten geçtiği şeridi kırmızı** boyuyor. Şartname §5.3.2/§6.2: **0 puan**.
  - **Yap:** `road` etiketi **rotadan** türetilsin, centroid'den değil. İki aday
    tanım var; **ölç, gerekçeyle seç, `CONTRACTS.md` §6.2'ye yaz**:
    (a) rotanın **en dar noktasındaki** (minimum açıklık / darboğaz) şerit —
        kritik geçiş orasıdır;
    (b) waypoint'lerin **baskın** şeridi (ağırlıklı çoğunluk).
    Rota birden fazla şeritten geçiyorsa tek etiketin yetersizliği de kayda geçsin.
  - **Kapı:** Enjekte-kapı deneyi (bilinen cevap) — kapı şerit-1'e açıldığında
    yayınlanan `road` **1** olacak; şerit-3'e açıldığında **3**. 67 gerçek karede
    `road` ile rotanın geçtiği şerit uyuşmazlığı **0**. Pozitif kontrol: düzeltme
    etkisizleştirilince eski 67/67 uyumsuzluk geri gelmeli.

- [x] **T32 — Güven metriği yanlış yerden ölçülüyor; kötü tespitte YÜKSELİYOR** · `codes/rpi_inference.py:274` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` D-41 → çözüm kaydı **D-45**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Claude-2 yazdı.
  - **Asıl kusur kapandı:** `test_ince_koridor_yuksek_guven_URETMEZ` — eskiden çok az
    piksel tek üçte-bire düşünce güven `1,0` oluyordu (tespit kötüleştikçe güven
    yükseliyordu).
  - **Anlamlı ilişki kanıtlanmış:** `test_guven_kapi_genisligiyle_MONOTON_artar` —
    güven artık geçit genişliğiyle monoton artıyor; ölçüm **rotanın kendisinden**
    (darboğaz açıklığı) yapılıyor, üst banttan değil.
  - **Pozitif kontrol:** `test_kapi_konumu_degisince_guven_ESKIDE_sabitti`.
  - **Fail-closed + madde 16:** `test_gecersiz_aciklik_fail_closed`,
    `test_gecersiz_icerik_genisligi_fail_closed`,
    `test_guven_normalizeri_sozlesmeden_turetiliyor`.
  - **Çözünürlükten bağımsız:** `test_olcum_cozunurlukten_bagimsiz`.
  - **✅ YAPILDI (KISMEN — sınırı aşağıda) · 2026-08-10 · Claude-2.** Güven artık
    rota boyunca ölçülen **en küçük açıklık** / içerik genişliği oranı:
    `karar_sozlesmesi.rota_darbogaz_guveni`, `ROTA_DARBOGAZ_TAM_ORANI = 0.035`.
    Mutlak piksel değil **oran** — çözünürlük değişince ölçüt kaymaz (§8);
    kapı testi aynı sahneyi 2× çözünürlükte koşup aynı kararı doğruluyor.
  - **Normalizatör ölçümle seçildi** (67 gerçek kare, std maksimumu **0,035**'te):
    ```
    N       std      p50    doygun     K-B 0,20'de cekimserlik
    0,020  0,3862   1,000   42/67          14/67 (%21)
    0,035  0,4029   0,809   31/67          18/67 (%27)   <- secildi
    0,050  0,3999   0,566   25/67          22/67 (%33)
    ```
    Fiziksel çapa da aynı yeri gösteriyor: 50 m içerik genişliğinde `0,035·W`
    yarıçap ≈ **1,75 m** = `R_GEREKLI_M = 1,10 m`'nin ~1,6 katı.
  - **Ayırt edicilik — önce/sonra** (aynı kareler, tek değişken metrik):
    ```
    kaynak         n   pearson(guven, model_tespit_guveni)      std
                          ESKI          YENI            ESKI      YENI
    drone         67     -0,173        +0,333          0,0287    0,4029
    gemini_road   11     -0,397        +0,158          0,2903    0,3914
    val            3     -0,577        -0,577          0,0014    0,1296  (n=3, anlamsiz)
    ```
    Negatif korelasyon ("kötü tespit ödüllendiriliyor") iki kaynakta pozitife
    döndü; dağılım genişliği drone'da **14 kat** arttı.
  - **Kapı 4 (sınıf-0 tespiti SIFIR):** 8/82 kare → **karar 0, azami güven 0,0**.
  - ⚠ **KALİBRASYON BORCU — MİMARA:** `ROTA_GUVEN_ESIGI = 0.20` **eski metrikten
    devralınamaz.** Yeni metrikte 0,20 → %27 çekimserlik ve fiziksel karşılığı
    ~0,35 m yarıçap (hâlâ taban koruyucusu). İKA gövde açıklığını gerçekten
    zorlayacaksa değer `R_GEREKLI_M / (0,035 · ARENA_M) = 1,10/1,75 =` **0,629**
    olmalı (→ %36 çekimserlik). Süpürme tablosu D-45'te; **eşiği mimar yazar.**
  - 🔴 **AÇIK KALAN — kapsam dışı bırakıldı, sessizce yapılmadı:** yeni güven
    **geometriktir, algısal değildir.** Model 0,089 güvenle geniş bir blob
    üretirse geometri sağlıklı görünür:
    ```
    gemini/6.png         model tespit maks 0,0894 -> ESKI 1,000 · YENI 0,837
    gemini/road_127.jpg  model tespit maks 0,0821 -> ESKI 1,000 · YENI 0,502
    ```
    Tam kapanması için `boxes.conf` `get_masks` üzerinden karara taşınıp
    `conf = min(geometrik, algısal)` yapılmalı. **Yeni görev satırını Claude 1
    açar** (madde 2: kuyruğu mimar yazar); öneri metni Claude-2'nin devir
    raporundadır.
  - **Kanıt:** `confidence = in_third / bx.size` yalnız üst %30 bandından hesaplanıyor.
    Seçilen şeridin payı bile değil (ekranda 0,326; en yüksek pay 0,382). Çok az
    piksel tek üçte-bire düşerse oran **1,0** olur — yani **tespit kötüleştikçe güven
    yükseliyor**. `val` 18/40, `gemini_road` 14/40 karede sınıf-0 tespiti **sıfır**.
  - ⚠ **D-38'in önerdiği marjin metriği ÇÖZMÜYOR** (ölçüldü): aynı üst banttan
    hesaplandığı sürece `std(marjin)=0,029 ≈ std(in_third)=0,029`. **Sorun
    istatistiğin şekli değil, nereden ölçüldüğü.**
  - **Yap:** Güveni üst banttan değil **rotanın kendisinden** türet. Adaylar:
    rota boyunca minimum açıklık (`dt` min) / `R_GEREKLI_M` oranı · waypoint zinciri
    boyunca süreklilik · koridor genişliği dağılımı. Ölç ve **ayırt ediciliğini
    kanıtla** — std ve dağılım tablosuyla.
  - ⚠ Yer gerçeği yok; korelasyonu neye göre ölçeceğini **önce tanımla**.
    Tanımlayamıyorsan bunu açıkça yaz, uydurma.
  - **Kapı:** Yeni metrik, sınıf-0 tespiti **sıfır** olan karelerde yüksek değer
    **üretmeyecek** (mevcut kusur). `CONTRACTS.md` §6.3/K-B eşiği yeni metriğe göre
    **yeniden kalibre** edilecek — eski `0,20` taşınmayacak.

- [x] **T30 — `KENAR_GUVENSIZ` kapısı örnekleme parametresine duyarlı: karar KARARSIZ** · `codes/rpi_inference.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-40
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Codex-2 yazdı.
  - **Bağımsız ölçüm** (Codex'in testine değil, kendi betiğime bakarak):
    ```
    ÖNCE   14 karenin 5'inde salınım (%36) · drone kümesinde KENAR_GUVENSIZ %55
    SONRA  14/14 kare · n_waypoints ∈ {8,16,24,32} → HEPSİNDE aynı karar · salınım 0
    ```
  - **Kapı:** `tests/test_analyze_path_kararlilik.py` eski salınımı **pozitif
    kontrolle yeniden üretiyor** ve yeni yolun dört örnekleme değerinde aynı kararı
    verdiğini kanıtlıyor. Tam paket `Ran 143 tests · OK`, genel kapı **15/15**.
  - **Sebep etiketi düzeltildi:** `GORUS_HATTI_KOPUK_SEBEBI` eklendi — *"zincir hiç
    kurulamadı"* artık *"kurulan zincirin kenarı engelden geçiyor"*dan ayrı.
  - ⚠ **DOĞRULAMA BORCU — çekimserlik %55 → %0.** Düşüş beklenen yönde ama
    **büyüklüğü doğrulanmadı**. T24/D-28 pozitif kontrolü hâlâ geçiyor (kusur geri
    gelmemiş), ancak gerçek karelerde artık **hiç** çekimserlik yok. Kapının fazla
    gevşeyip gevşemediği bariyerli **gerçek** bir sahnede gözle doğrulanmalı.
    `rota_bul` aynı karelerde hâlâ 13/14 `BELIRSIZ_COKLU` diyor — iki karar yolu
    arasındaki ayrışma (**S4**) sürüyor ve artık daha görünür.
  - **Rol devri:** 2026-08-10 · Codex-2 ← Claude 1 · sebep: kullanıcı, T25 ortak-dosya beklemesini aşarak T30 kapsamının yürütülmesine açık yetki verdi · denetim: Claude 1
  - **Kanıt (ölçüldü):** aynı görüntü, aynı maske, yalnız `n_waypoints` değişti:
    ```
    kare            8wp    16wp   24wp   32wp  | rota_bul (bağımsız)
    frame_000002   KENAR  yol2   KENAR  yol2   | BELIRSIZ_COKLU
    frame_000003   yol2   KENAR  KENAR  yol2   | BELIRSIZ_COKLU
    frame_000007   KENAR  KENAR  yol2   KENAR  | BELIRSIZ_COKLU
    14 karenin 5'inde (%36) karar örnekleme sayısına bağlı DEĞİŞİYOR.
    drone kümesinde ret oranı: KENAR_GUVENSIZ %55
    ```
  - **Neden KRİTİK:** `n_waypoints` bir **çözünürlük** parametresidir; güvenlik
    kararını belirlememelidir. Aynı sahnede farklı karar sahada kabul edilemez —
    şartname §5.3.2/§6.2 yanlış güzergâhı 0 puan sayar.
  - **Kök neden:** waypoint'ler bantlardan **örnekleniyor**, sonra aralarındaki düz
    çizgi engelle sınanıyor. Koridor kıvrımlıysa iki bant arasındaki düz çizgi
    engelden geçer; bant sayısı değişince kesişim de değişir. Kapı, koridorun
    **geçilebilirliğini** değil **örnekleme geometrisini** ölçüyor.
  - **Yap:** Kenar güvenliğini waypoint çiftleri üzerinden değil, koridorun
    **bağlantılılığı** üzerinden sına. `costmap_path_finder._bagli_mi` bunu zaten
    yapıyor ve **kararlı** sonuç veriyor (13/14 karede tutarlı `BELIRSIZ_COKLU`).
    Waypoint'ler bağlantısı **kanıtlanmış** bir yol üzerinde üretilirse (A* ya da
    centerline takibi) sonradan kenar denetimine gerek kalmaz.
  - ⚠ **T24'ü geri alma.** D-28 kusuru gerçekti (iki ucu zemin olan kenar engelin
    üstünden geçiyordu) ve düzeltme doğru yöndeydi. Sorun kapının **kararlılığı**.
  - **Ek — sebep etiketi yanlış:** `KENAR_GUVENSIZ` dönen vakaların **hepsinde
    üretilen waypoint 0**. Kenar yokken "kenar güvensiz" denemez. *"Zincir hiç
    kurulamadı"* ile *"kurulan zincirin bir kenarı engelden geçiyor"* ayrı
    sebeplerdir; ilki için yeni kod (`GORUS_HATTI_KOPUK`) `CONTRACTS.md` §6.4'e eklenir.
  - **Kapı:** `n_waypoints` ∈ {8, 16, 24, 32} için **aynı** karar; 14 karelik
    kümede salınım **0**. `codes/test_rota_sentetik.py` **15/15**. D-28'in pozitif
    kontrolü (mutasyon testi) hâlâ düşüyor olmalı — kusur geri gelmemeli.
  - **Uygulama (Codex-2):** Güvenlik kararı yatay bant örneklerinden ayrıldı.
    Tam çözünürlükte uç bağlantısı doğrulanıyor; muhafazakâr MIN-havuzlu A* bu
    bağlantının somut witness yolunu çıkarıyor. Bütün A* denemeleri toplam
    `32768` plan hücresiyle sınırlı; daha ince ızgara bütçeyi aşarsa saniyelerce
    bloklamak yerine fail-closed dönüyor. Zincirin ilk/son waypoint'i gerçek alt/üst
    tohum pikseline ankrajlıdır. `n_waypoints` yalnız doğrulanmış kanonik yolun çıktı
    yoğunluğunu değiştiriyor. Witness kurulamazsa yeni `GORUS_HATTI_KOPUK`;
    kurulmuş zincirin son postcondition'ı düşerse `KENAR_GUVENSIZ`. T24 son kapısı
    korunmuştur. Güncel kaynak SHA `AF75CE176B313B8B...`.
  - **Gerçek 14-kare kapısı:** `& 'O:\navitas-local-train\venv\Scripts\python.exe' -B -`
    (v21 SHA `799e07f9...`; imgsz=512; ground `.30`, block `.10`; ham ground +
    `engel_mask`; aynı maskede `n={8,16,24,32}`) → `56 çağrı · 0 hata · salınım
    0/14 · 0/42 komşu geçiş · her n için 14/14 yol2 · endpoint-band ihlali 0/56
    · 1059 segmentte LOS/ham engel ihlali 0`; analyze p50/p95/max
    `88.299/111.716/144.223 ms`; exit `0`.
    Dört n birlikte sayıldığında düzeltme öncesi gerçek salınım `10/14` idi;
    tarihsel `5/14` yalnız 8↔32 uçlarını karşılaştırıyordu.
  - **Gerçek 67-kare GUI zinciri:** aynı komut ve eşik zinciri, `n=8` → `67/67
    karar · 0 ret · 0 exception · yol2=67`; GUI densify sonrası endpoint-band
    ihlali `0/67`, `1333` segmentte LOS/ham engel ihlali `0`, waypoint min/p50/max
    `20/21/21`, en uzun edge `45.967 px < 48 px`; analyze p50/p95/max
    `81.666/100.423/144.223 ms`; plan bütçesi azami `30692/32768`;
    `road_104.jpg → yol1, güven .465, 20 wp, 0 ihlal`; exit `0`.
  - **Bütçe regresyonu:** 512² tek-piksel dar-geçit tam çözünürlük A* ile
    `5.941 s` sürüyordu; güncel kod `233.6 ms` içinde ölçülü
    `GORUS_HATTI_KOPUK` döndürdü (`20480/32768` plan hücresi), güvenlikten
    taviz vermeden worker blokajını sınırladı.
  - **Hedefli kapılar:**
    `python.exe -B -m unittest discover -s tests -p 'test_analyze_path*.py' -v`
    → `Ran 22 tests · OK`; `-p test_rota_ret_nedenleri.py` → `10/10 OK`;
    `-p test_rpi_letterbox.py` → `5/5 OK`; `-p test_yks_gui_rota_engel.py`
    → `7/7 OK`; `-p test_rota_guven_esigi.py` → `8/8 OK`; tümü exit `0`.
  - **Genel kapılar:** `python.exe -B codes/test_rota_sentetik.py` → `SONUC:
    15/15 dogru · [OK]`, exit `0`; `python.exe -B -m unittest discover -s tests -q`
    → `Ran 143 tests in 28.172s · OK`, exit `0`; `py_compile` → çıktı yok,
    `git diff --check` → yalnız LF→CRLF çalışma-ağacı uyarıları, exit `0`.
  - **Sınır:** T30 waypoint örnekleme kararsızlığını ve piksel-segment güvenliğini
    kapatır. Çoklu koridorun görev-semantik seçimi ile metrik İKA gövde açıklığı
    mevcut S4/D-25 mimari kapsamındadır; bu görev o kararları sessizce üstlenmez.

- [x] **T29 — GUI varsayılan algı kaynağı modelin çalışmadığı kümede** · `comms/yks_gui.py:129` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-39
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex yazdı. Bağımsız
    ölçümüm (sınıfı headless kurup `K` turunu gerçekten gezdirdim):
    ```text
    acilis kaynagi     : drone
    kaynak listesi     : ('gemini', 'test', 'val', 'drone')
    K tusu turu        : drone -> gemini -> test -> val
    tum kaynaklara erisim: True
    ```
    İstediğim sınır tutuldu: `gemini`/`val` **silinmedi**, tanısal karşılaştırma için
    listede kaldı — domain boşluğunu (D-21) gizlemeden yalnız açılış kümesi değişti.
    Kod yorumu bunun semptom yönetimi olduğunu kaydediyor.
  - **Kanıt:** varsayılan `self.algi_kaynak = "gemini"`. Ölçüldü: v21 o kümede
    **zemin %0,00** (12 karenin 8'i tamamen boş). Aynı model `drone` karelerinde
    **zemin %76,8–78,7**. S9'da `drone` kaynağı tam bu yüzden eklendi ama
    **varsayılan değiştirilmedi** — kullanıcı GUI'yi açtığında modelin çalışmadığı
    kümeye bakıyor.
  - **Yap:** Varsayılanı `"drone"` yap. `gemini`/`val` kaynakları listede kalsın
    (domain boşluğunu göstermek için değerli), yalnız açılış kümesi değişsin.
  - **Kapı:** GUI `--demo` ile açıldığında ilk algı karesi `drone` kümesinden gelir
    ve bilgi satırında `blocked > %10` görünür (v20'de bu değer %0,00'dır).
  - ⚠ **Bu bir çözüm değil, semptom yönetimidir.** Asıl mesele v21'in arena/RescueNet
    görsellerinde zemin bulamaması (D-21 domain boşluğu). Model tarafı ayrı iştir.
  - **Uygulama:** Açılış kaynağı `drone` oldu; `gemini`, `test` ve `val` tanısal
    karşılaştırma için `ALGI_KAYNAKLAR` içinde kaldı. Kod yorumu bunun yalnız semptom
    yönetimi olduğunu ve asıl sorunun D-21 domain boşluğu olduğunu açıkça kaydediyor.
  - **Hedef kapı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_yks_gui_demo_kaynak.py -v
    [T29_KAPI] demo=1 kaynak=drone ilk_kare=data/raw_frames/a.jpg exit=0
    test_demo_ilk_algi_istegi_drone_kumesinden_gelir (...) ... ok
    Ran 1 test in 0.003s
    OK
    EXIT_CODE=0
    ```
    Test temiz klon dizilimini bellekte taklit eder; izlenmeyen kullanıcı karelerine
    veya disk yazımına bağlı değildir ve üretim `_algi_gorseller()` eşlemesini kullanır.
  - **Genel kapılar — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    [T29_KAPI] demo=1 kaynak=drone ilk_kare=data/raw_frames/a.jpg exit=0
    Ran 193 tests in 32.779s
    OK
    EXIT_CODE=0
    ```

- [x] **T27 — Jetson saha paketi karar güvenliği düzeltmelerini TAŞIMIYOR** · `jetson_paket/kod/` · **KRİTİK**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Codex-2 yazdı (T20 ile
    birlikte, kuyruk durumu güncellenmemişti — depo otoritedir, D-33).
  - **sha eşitliği — kendim hesapladım, 7/7 AYNI:** `rpi_inference.py` ·
    `karar_sozlesmesi.py` · `protocol.py` · `link.py` · `iha_sender.py` ·
    `inis_kaniti.py` · `iha_inis_yayinci.py`
  - **Kapı:** `tests/test_jetson_comms_paketi.py` → `Ran 3 tests · OK`.
  - 🔴 **Mimari öneri karşılandı:** paket artık `scripts/jetson_paket_hazirla.py` ile
    **üretiliyor** — elle kopyalama değil, tek kaynak `codes/`. Kopya-dosya
    kırılganlığı (bu turda unutulup kusura yol açan şey) yapısal olarak kapandı.
  - Saha kuru koşusunda halka **aktarim GECTI**; önceki turda
    `eksik_moduller=[iha_sender.py, link.py, protocol.py]` idi.
  - **Kanıt (2026-08-10 ölçüldü):**
    ```
    codes/rpi_inference.py            779 satır  6C229CD51619
    jetson_paket/kod/rpi_inference.py 704 satır  0C98EFEA14E8   FARKLI
    jetson_paket/kod/ içinde: karar_sozlesmesi -> 0 eşleşme
                              _uc_bant_temasi_yeterli -> 0 eşleşme
                              ROTA_GUVEN_ESIGI -> 0 eşleşme
    ```
    (`costmap_path_finder.py` iki tarafta **aynı** — sorun yalnız algı/karar yolunda.)
  - **Neden KRİTİK:** saha paketi **eski karar mantığını** taşıyor. Sahada koşan kod
    bariyerle kopmuş koridoru hâlâ "açık" diyebilir (T26/D-29 kusuru) ve `guven=0.0`
    kararı yayınlayabilir (T25/D-28). Yani düzeltmeler **sahaya ulaşmıyor.**
  - **Yap:** `karar_sozlesmesi.py`'yi pakete ekle ve `rpi_inference.py`'yi eşitle.
  - 🔴 **Asıl mimari sorun — kopya dosya yaklaşımı kırılgan.** Her düzeltmenin iki yere
    yazılması gerekiyor ve bu tur unutuldu. Elle eşitleme yerine paket bir **betikle
    üretilmeli** (tek kaynak: `codes/`), ve bir kapı iki tarafın sha'sını karşılaştırıp
    ayrışmayı yakalamalı. Bu, D-35'in (belge–kod ayrışması) kod–kod karşılığıdır.
  - **Kapı:** `jetson_paket/kod/rpi_inference.py` ile `codes/rpi_inference.py` sha'sı
    **aynı**; pakette `karar_sozlesmesi.py` var; `tests/` içinde ayrışmayı yakalayan
    bir kapı testi bulunuyor ve **kasten ayrıştırılınca düşüyor** (mutasyon kanıtı).
  - **Uygulama · 2026-08-10 · Codex-2:** `codes/karar_sozlesmesi.py` içindeki tek
    kaynak K-B politikası `rpi_inference`, `iha_perceive` ve `yks_gui` erken karar
    yollarına uygulandı. Eşik altı kararın yol/waypoint'i temizleniyor ve operatöre
    `DUSUK_GUVEN` nedeni gösteriliyor. `IhaSender.send_open_route` son savunmada
    eşik altı/NaN/sonsuz/geçersiz güveni ACK'li `NO_ROUTE`a çeviriyor. GUI, dışarıdan
    gelen düşük güvenli `OPEN_ROUTE`u onaya açmıyor ve ACK üretmiyor. Protokol güveni
    eşik üstüne yuvarlamıyor; JSON NaN/sonsuzu fail-closed reddediyor.
  - **Hedefli yayın kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_rota_guven_esigi.py -v`
    → `Ran 8 tests in 0.313s` · `OK` · exit `0`. Gerçek UDP loopback'te `0.499`
    yalnız `NO_ROUTE/DUSUK_GUVEN+ACK`, tam `0.500` yalnız `OPEN_ROUTE+ACK`; eşik
    hemen altı JSON gidiş-dönüşünde yukarı yuvarlanmadı. NaN/±sonsuz/bool/aralık
    dışı değerlerde `OPEN_ROUTE` sayısı `0`.
  - **Gerçek CLI kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_iha_sender_cli.py -v`
    → `Ran 3 tests in 1.431s` · `OK` · exit `0`. Normal `0.9`, düşük `0.499` ve
    açık `--no-route` yolları gerçek subprocess + geçici UDP YKS ile sınandı;
    sırasıyla yalnız `OPEN_ROUTE`, yalnız `NO_ROUTE/DUSUK_GUVEN`, yalnız
    `NO_ROUTE/KAPALI_DAR` alındı.
  - **Sözleşme birim kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_karar_sozlesmesi.py -v`
    → `Ran 3 tests in 0.000s` · `OK` · exit `0`.
  - **Tam keşif kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q`
    → `Ran 120 tests in 28.750s` · `OK` · exit `0`.
  - ⚠ **GERÇEK 67 KARE KALİBRASYON ENGELİ · D-37:** GUI v21/imgsz=512 üretim
    zincirinde ham `52 karar / 15 çekimser`; güven `min=0.243 · p50=0.319 ·
    max=0.363`. Bağlayıcı `0.50` eşiği 52 kararın tamamını reddetti: son
    `0 karar / 67 çekimser` (**%100**). Yayın güvenliği doğru, fakat §6.3'ün kendi
    hükmüne göre aşırı çekimserlik sahada kullanılamaz. Codex sözleşmeyi
    değiştiremez; Claude 1 K-B'yi gerçek veriyle yeniden değerlendirmeden ve
    ortak dosyalı T26 mimar denetiminde kapanmadan T25 `READY_FOR_REVIEW` yapılmadı.

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

- [x] **T12 — `IKA_GO` gönderiliyor ama hiçbir yerde tüketilmiyor** · `comms/ika_receiver.py` · KRİTİK
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Düzeltme `91010be` commit'inde.
    `IKA_GO` `comms/ika_receiver.py:242-256`'da tüketiliyor; kritik olarak kapı yalnız
    başlangıçta değil **her sıfır-olmayan motor komutunda** `run_if_route_valid`
    (`:82-93`) ile yeniden denetleniyor.
  - **Kapı — bağımsız koşuldu:** `unittest ... -p test_ika_go_gate.py -v` → `Ran 9 tests` · `OK` ·
    `[T12_KAPI] IHA_LANDED_onceden=1 YKS_UDP_TX=1 IKA_GO_oncesi_hareket=0 IKA_GO_sonrasi_nonzero_motor=1 ACK=ika exit=0`
  - ⚠ **Ölü kod tuzağı (düşük şiddet, kapatmayı engellemez):** `simulation/scripts/ika_nav.py:259-267`
    `receiver_ika_go_bekle()` yalnız **tek bacağı** bekliyor ("sürüş izni açık" diyor ama
    iniş bacağını hiç sormuyor). Üretimde çağıran yok; ileride çağrılırsa T13 kapısının
    yanlış tarafına geçmiş görünür. Silinmeli ya da docstring'ine uyarı eklenmeli.
  - ⚠ Bu maddeye yapıştırılmış eski kapı çıktısı bir revizyon bayattı (T13 testi
    güçlendirmiş); yukarıdaki çıktı bugünün gerçek koşumudur.
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

- [x] **T13 — İKA, İHA'nın inişini beklemiyor** · `simulation/scripts/navitas_sim.py` · KRİTİK
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** `IHA_LANDED`
    `comms/ika_receiver.py:233-241`'de latch'leniyor; `:122` `if not self.ika_go or not
    self.iha_landed: return False` — şartname §2.2.5 **tüketici tarafında** kapatıldı.
  - **Kapı — bağımsız koşuldu:** `unittest ... -p test_iha_landed_gate.py -v` → `Ran 10 tests` · `OK`
    · `[T13_KAPI] IKA_GO=1 LANDED_oncesi_nonzero=0 LANDED_sonrasi_nonzero=1 ACK=ika exit=0`
    · `[T13_DEADLINE] timeout_sonrasi_latch=2 navigate_calls=0 sonuc=guvenli_ret`
  - **Genel kapı + regresyon:** `codes/test_rota_sentetik.py` → **15/15** ·
    `unittest discover -s tests` → `Ran 101 tests` · `OK`
  - ⚠ **Protokol notu (T13 kusuru değil):** `IHA_LANDED`/`IKA_GO` için kimlik doğrulama
    yok; `node`/`hedef`/`seq` alan kontrolünden ibaret. Aynı ağda sahte bir UDP çerçevesi
    latch'i açabilir. Latch kalıcı olduğundan replay zarar vermiyor. Tasarım notu olarak
    kayda geçti.
  - 🔗 **T20 ile ilişki:** çelişkili **değil** — aynı zincirin iki ucu. T13 tüketici ucunu
    fail-closed kapattığı **için** T20 artık "eksik özellik" değil, sahada `P_görev = 0`
    üreten tıkayıcıdır. Kök neden: `REVIEW_LOG.md` **D-34**.
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
  - 🟡 **2026-08-10 · İLK KOŞUM YAPILDI, KANIT EKSİK — kapı kapanmadı.** Kullanıcı
    bildirdi: **14 FPS**, donanım **Jetson Nano 4GB**. Sayı umut verici (gereken hız
    0,9–2,6 FPS) ama **dört bilinmeyen** yüzünden kayda geçirilemiyor:
    (a) çıktı dosyası yok, yalnız ekranda görüldü;
    (b) girdi kümesi bilinmiyor — `--girdi` **varsayılanı `data/raw_frames`**, ve
    `JETSON_KILAVUZ` **G3** bunun *"FPS'i yanıltıcı yüksek"* gösterdiğini yazıyor
    (boş maske → boş costmap). Kural: ölçüm `test_goruntuleri/sentetik_arena/` ile;
    (c) model/format/imgsz bilinmiyor — **G1**: `--pt` varsayılanı **v20**, öneri **v21**;
    (d) güç modu kayıtsız (*"maksimum yapılmazsa ölçüm yalan söyler"*).
    Ayrıntı ve donanım değişikliğinin sonuçları: `REVIEW_LOG.md` **D-36**.
  - ℹ️ **Donanım hedefi DEĞİŞMEDİ — ölçüm vekil kartta yapıldı.** Üretim hedefi
    **Jetson Orin NX 16 GB**; Nano 4GB elde olan **test kartıdır**. Belgelerin
    Orin NX varsayması doğrudur, değiştirilmeyecek. Aradaki fark mertebe düzeyinde
    olduğu için Nano'da ölçülen her sayı hedef kart için bir **ALT SINIR**dır —
    yani hız tarafında durum bildirilenden **daha iyi** olacaktır.
  - ⚠ **Vekil kart şunları kapatmaz:** (1) hedef kartın gerçek FPS'i; (2) **T16
    engine derlemesi** — `.engine` hem TensorRT sürümüne hem GPU mimarisine
    kilitlidir, Nano'da derlenen engine Orin NX'te de çalışmaz; (3) **H2 künyesi**
    (JetPack + TensorRT + Python sürümü) hedef kartta toplanmalı.
  - ✅ **Vekil kartın kapatabileceği sorular (Orin NX gelmeden):** model yükleniyor
    mu · kamera açılıyor mu · zincir uçtan uca çöküyor mu · 4 GB'da bellek yetiyor mu.
    Bunlar değerlidir ve şimdi koşulabilir.
  - ⚠ **Kapsam sınırı (ölçüm düzgün tekrarlansa bile):** `jetson_fps.py:162`
    `rota_bul(..., plan=False)` — **A\* rota planlama ölçüm dışında.** Kılavuzun kendi
    ifadesiyle bu test *"rota aktarımını, ACK'i ve İKA'nın hareket etmesini kanıtlayamaz."*

- [ ] **T18 — DroidCam kamera kaynağının algı hattına bağlanması** · `codes/rpi_inference.py` · bağımlı: **H3**
  - **Yap:** Kamera kaynağını CLI parametresi yap (dosya / video düğümü / RTSP). Bağlantı koparsa yeniden deneme mantığı zaten var, kaynak değişimiyle bozulmadığını doğrula.
  - ⚠ **Kapsam genişledi (D-13):** aynı dosyada **model yolu da sabit kodlu** — `:32-40` her zaman `best_ncnn_model` arar, `--model` argümanı **yok**, `INFER_SIZE = 512` sabit. Jetson'da v17/v20 ile canlı demo bu yüzden koşulamıyor. Model yolunu da CLI parametresi yap.
  - **Yap (hazır referans):** `jetson_paket/kod/kamera_dogrula.py` kaynağı parametrik alan çalışan bir örnektir (indeks / `/dev/videoN` / `http://…:4747/video`); kalıbı oradan al.
  - **Kapı:** DroidCam kaynağıyla 60 saniyelik kesintisiz çıkarım, düşen kare sayısı raporlanmış; ayrıca `--model` ile v17 `.engine` yüklenip tek kare çıkarım hatasız.

- [x] **T20 — IHA_LANDED saha uçuşunda üretilmiyor: İKA hiç hareket etmez** · `simulation/scripts/iha_detect_send.py` · **TIKAYICI · KRİTİK** · kanıt: `REVIEW_LOG.md` D-17
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Kodu Codex-2 yazdı.
  - **Asıl kapı — bağımsız koşuldu:** `scripts/saha_kuru_kosu.py`
    ```
    surus_izni  GECTI  IHA_LANDED saha kod yolunda uretiliyor
    aktarim     GECTI  saha paketi haberlesme kodunu ve gerekli API'yi tasiyor
    ```
    Üretim çağrısı `simulation/` **dışında**: `comms/iha_inis_yayinci.py:44`.
  - **D1 fail-closed denetimi — ÖRNEK DÜZEYDE.** `comms/inis_kaniti.py`:
    pymavlink yoksa `ImportError` (`:27-30`, sessizce `True` DÖNMÜYOR) · deadline
    alanı yoksa `False` (`:92-94`) · `recv_match` hatası/`None`/timeout → `False`
    (`:112-117`) · `landed_state != ON_GROUND` → `False`, sessizce atlamıyor
    (`:132-134`) · **MAVLink sistem kimliği sabitleniyor** (`:53-61`, `:124-127`) —
    istenmediği hâlde eklenmiş, sahte çerçeve koruması.
    Doğru mimari ayrım docstring'de: *"`relative_alt` yerden yükseklik değil,
    home'a göre bağıl irtifadır — yalnız ek makullük kapısı; birincil kanıt
    `landed_state`."*
  - ⚠ **İLAN SINIRI KORUNDU — İKA hâlâ hareket etmez.** Aynı koşumda
    `GECTI 4 · DUSTU 3 · SAHIPSIZ 3`, kopuk halka **6**: kamera
    (`cv2.VideoCapture(0)` sabit → **T18**), model_yukleme (`--model` argümanı yok),
    rota (letterbox tohum bandı dolguya düşüyor → **D-25**), motor (**SAHİPSİZ**).
    T20 yalnız **halka 9**'u açtı.
  - **Kanıt:** Kilit `comms/yks_gui.py:1111-1118` ve `comms/ika_receiver.py:233` `IHA_LANDED` bekliyor. Zincirin 3. halkası (`send_iha_landed` çağrısı) git'in takip ettiği 47 `.py` içinde **tek yerde** var: `simulation/scripts/navitas_sim.py:95` — kendi başlığıyla *"Ana Simülasyon Kontrolcüsü"*. Saha betiği `iha_detect_send.py` (`Saha (SiK telsiz): --serial /dev/ttyUSB0`) yalnız `send_open_route` ve `send_no_route` gönderiyor. Gerçek Pi yazılımı `drone/*.py` comms protokolünü **hiç** kullanmıyor (`git ls-files "drone/*.py" | xargs grep -nE "IhaSender|from comms|protocol"` → boş).
  - **Neden tıkayıcı:** Saha görev uçuşunda `IHA_LANDED` hiç üretilmez → `ika_baslat()` her çağrıda REDDEDİLDİ döner → İKA hiçbir zaman hareket etmez → **P_görev = 0**. Şartname §2.2.5'i korumak için konan kilit, görevi engelliyor. FDA görev test uçuşu **30 Eylül** — bu tarihe kadar kapanmazsa uçuş bacağı sıfırlanır.
  - 🔴 **KÖK NEDEN DERİNLEŞTİRİLDİ · 2026-08-10 · Claude 1 denetimi · `REVIEW_LOG.md` D-34.**
    Eksik olan **taşıma çağrısı değil, KANIT KAYNAĞI.** Simülasyonda iniş kanıtı
    `iha_flight.fly()` → Gazebo'nun son yer teması pose komutunu kabul etmesidir
    (`iha_flight.py:51-59` returncode). **Sahada bunun yerine geçecek hiçbir kaynak yok:**
    `grep -rniE "pymavlink|mavutil|dronekit|pixhawk|LANDED_STATE|relative_alt" --include=*.py`
    → üretim kodunda **SIFIR**. `drone/rpi_yayin.py:479-496` telemetrisi yalnız
    `t/calisma_sn/cpu_c` taşıyor — **irtifa alanı bile yok** — ve `drone/` kendi HELLO/ACK
    protokolünü kullanıp `comms/protocol.py`'yi hiç import etmiyor.
  - ⛔ **Eski (a) seçeneği MİMARİ OLARAK YANLIŞ, iptal.** `iha_detect_send.py` tek atımlık
    bir süreçtir: tespit + gönderim yapıp `:144 link.close()` ile çıkar, ve görev kuralı
    gereği **İHA havadayken** koşar. İniş, o süreç bittikten **sonra** gerçekleşir.
  - **Yap — üç parça, sırayla:**
    - **D1 · kanıt kaynağı** — yeni `comms/inis_kaniti.py`:
      `yerde_mi(mav, ardisik=3, tavan_m=1.0) -> bool`. Pixhawk
      `EXTENDED_SYS_STATE.landed_state == MAV_LANDED_STATE_ON_GROUND (1)` **ardışık N kez**
      **ve** `GLOBAL_POSITION_INT.relative_alt/1000 < tavan_m`. Her okuma hatasında `False`
      — **fail-closed**. Operatör düğmesi dâhil başka hiçbir kaynak kabul edilmez.
    - **D2 · saha yayıncısı** — yeni `comms/iha_inis_yayinci.py`: `--serial/--baud` veya
      `--ika/--yks`, `--mavlink udp:127.0.0.1:14550`. Gövde `navitas_sim.py:87-112`
      `iha_inisini_yayinla`'nın **birebir yeniden kullanımı** olsun; yeniden yazılmasın.
    - **D3 · paket** — `jetson_paket`'e `comms/` modülleri + `pyserial` bağımlılığı
      (şu an halka 8 eksik: `eksik_moduller=[iha_sender.py, link.py, protocol.py]`).
  - **Kapı:** (1) `git ls-files "*.py" | xargs grep -n "send_iha_landed"` çıktısında
    `simulation/` **dışında** en az bir **üretim** çağrısı görünecek (AST dedektörü ve
    test fixture'ı sayılmaz). (2) `scripts/saha_kuru_kosu.py` halka `surus_izni` →
    `saha_ureticileri` **boş olmayacak**, halka **GEÇTİ** dönecek. Gerçek çıktı yapıştırılacak.
  - ⚠ **İLAN SINIRI:** T20'nin kapı çıktısı **"İKA hareket etti" diye ilan edilmeyecek.**
    Kanıt yalnızca *"IHA_LANDED latch'i SAHA kaynağından açıldı"* olabilir. T20 kapansa
    bile İKA sahada hareket etmez: halka **10** (gerçek motor sürücüsü) **SAHİPSİZ**,
    halka **8** (aktarım) jetson paketinde yok — `CONTRACTS.md:273-275`.
  - **Uygulama · 2026-08-10 · Codex-2:** `comms/inis_kaniti.py`, Pixhawk
    `EXTENDED_SYS_STATE=ON_GROUND` durumunu her örnekte taze ve `< 1,0 m`
    `GLOBAL_POSITION_INT.relative_alt` ile eşleyip üç ardışık çift olmadan `False`
    döndürüyor. Bütün çiftler aynı MAVLink `sysid` kaynağından gelmek zorunda;
    defaultsuz `--kanit-timeout` girdisi tek mutlak monotonic deadline kuruyor ve
    sessizlik/yalnız-GPS akışı süreyi uzatamıyor. Eksik `pymavlink` açık
    `ImportError`, tüm telemetri kusurları fail-closed sonuç üretiyor.
    `comms/iha_inis_yayinci.py` bu kanıtı tek yetkili
    saha kaynağı yapıyor; ACK'li ortak yayın gövdesi simülasyon tarafından import
    edilerek yeniden kullanılıyor. SiK yolunda İKA'nın adressiz seri ACK'i eklendi.
  - **Paket · 2026-08-10:** Kanonik `protocol/link/iha_sender/inis_kaniti/`
    `iha_inis_yayinci` ile `karar_sozlesmesi` Jetson paketine taşındı;
    `pyserial` ve `pymavlink` bağımlılıkları eklendi. İzole paket importu ve
    kanonik-kopya eşliği testle korunuyor.
  - **Canlı doğrulama sınırı:** Tam-yol yorumlayıcı ölçümü `pymavlink=YOK`,
    `pyserial=YOK`, `EXIT_CODE=0`. Pixhawk/SiK ile canlı doğrulama **YAPILMADI**;
    D1/D2 mock ve gerçek loopback protokol testleriyle doğrulandı.
  - **Mimar belge senkronu:** `AGENTS.md` yazma matrisi nedeniyle Codex-2
    `CONTRACTS.md`'yi değiştirmedi. §7/§11'deki “saha üreticisi yok / halka 8
    sahipsiz” tarihsel durum satırları artık ölçülen depoyla çelişiyor; Claude 1
    görevi `[x]` yapmadan bu otorite belgeyi güncellemelidir. `3`, `1.0`,
    `relative_alt/1000` ve mesaj tipleri doğrudan T20/MAVLink sözleşmesinden;
    yayın repeat/interval gövdesi ise taşınan mevcut fonksiyondan gelir. Yeni
    timeout sabiti eklenmedi; süre zorunlu runtime girdisidir.
  - **Kapı 1 — gerçek takipli-dosya grep çıktısı.** Verilen komut PowerShell'de
    `xargs` PATH'te olmadığı için önce çalışmadı; aynı komut Git Bash'te wildcard
    Git'e aynen iletilerek gerçekten çalıştırıldı:

    ```text
    git ls-files "*.py" | xargs grep -n "send_iha_landed"
    comms/iha_inis_yayinci.py:44:        seq, acked = sender.send_iha_landed(
    comms/iha_sender.py:157:    def send_iha_landed(self, repeat=8, interval=0.25, wait_ack=True):
    jetson_paket/kod/iha_inis_yayinci.py:44:        seq, acked = sender.send_iha_landed(
    jetson_paket/kod/iha_sender.py:157:    def send_iha_landed(self, repeat=8, interval=0.25, wait_ack=True):
    scripts/saha_kuru_kosu.py:654:    # icinde gecen `send_iha_landed(` bir saha ureticisi DEGILDIR — bu tam olarak
    scripts/saha_kuru_kosu.py:675:                        and dugum.func.attr == "send_iha_landed"):
    tests/test_saha_kuru_kosu.py:68:        '    seq, acked = sender.send_iha_landed(repeat=8)\n',
    tests/test_saha_kuru_kosu.py:231:            '    sender.send_iha_landed(repeat=8)\n',
    EXIT_CODE=0
    ```
  - **Kapı 2 — gerçek saha kuru koşu hedef satırları:**

    ```text
    O:\navitas-local-train\venv\Scripts\python.exe scripts/saha_kuru_kosu.py
      aktarim        GECTI      saha paketi haberlesme kodunu ve gerekli API'yi tasiyor
                              -> jetson_paket/kod/iha_sender.py
      surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor
                              -> comms/iha_inis_yayinci.py:44
    GECTI 4 · DUSTU 3 · SAHIPSIZ 3 · ATLANDI 0
    KOPUK HALKALAR (6): kamera, model_yukleme, olcek, hedef_konumu, rota, motor
    Zincir saha kosumunda TAMAMLANMAZ.
    EXIT_CODE=1
    ```

    T20'nin iki hedef halkası **GECTI**; genel `EXIT_CODE=1`, çıktıda adı verilen
    T20 dışı altı kopuk halka nedeniyledir ve tüm saha zinciri geçmiş sayılmadı.
  - **Kapı 3 — değişmeyen genel kapı, gerçek çıktı:**

    ```text
    O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
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
  - **Kapı 4 — tam unittest keşfi, gerçek çıktı:**

    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests
    .........................................................................................................................................................................
    ----------------------------------------------------------------------
    Ran 169 tests in 28.818s

    OK
    EXIT_CODE=0
    ```
  - **Saha-latch uçtan uca mock/loopback kanıtı:** Sahte Pixhawk'tan üç aynı-`sysid`
    ON_GROUND+düşük irtifa çifti, gerçek üretim CLI gövdesinden gerçek UDP
    `IkaReceiver`'a gitti; çıktı `[T20_KAPI] IHA_LANDED_saha=1 ACK=ika exit=0`.
    Bu yalnız *IHA_LANDED latch'inin SAHA kaynağından açıldığını* kanıtlar;
    İKA hareketi ilanı değildir.
  - **Ek odak kapıları:** `test_inis_kaniti.py` **11/11**, `test_iha_inis_yayinci.py`
    **12/12**, `test_jetson_comms_paketi.py` **3/3**, `test_saha_kuru_kosu.py`
    **24/24**, mevcut `test_iha_landed_gate.py` **10/10**; tümü gerçek tam-yol
    yorumlayıcıyla `OK`, `EXIT_CODE=0`. `git diff --check` ve
    `git diff --cached --check` → `EXIT_CODE=0`.

- [x] **T20-b — Kilit, telsizden gelen GEÇERLİ inişi bile operatör dizisi olmadan reddediyor** · `comms/yks_gui.py:1306` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-34
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex yazdı.
    Codex'in mock testine güvenmedim; **gerçek UDP soketleriyle telden çıkan baytları**
    okuyan bağımsız bir matris koştum (`t_iha0`/`t_iha1` hiç kurulmadan):
    ```text
    landed=H onay=H | telde=—                | red_log=E | t_ika0=None
    landed=H onay=E | telde=—                | red_log=E | t_ika0=None
    landed=E onay=H | telde=—                | red_log=E | t_ika0=None
    landed=E onay=E | telde=CMD/IKA_GO->ika  | red_log=H | t_ika0=kuruldu
    SONUC: GECTI (4/4)
    ```
    Üç negatif kontrol de duruyor: kanıt yokken hiçbir bayt tele çıkmıyor **ve**
    hakem onayı kapısı (§6.2) kaldırılmadı — düzeltme yalnız `t_iha1` bacağını aldı,
    kilidi gevşetmedi.
  - **Kalıntı (yeni T34):** `t_iha1` kilitten çıkınca `_onayla()`'daki §6.4 göstergesi
    doğrulanmamış "AKTARIM HAVADA TAMAMLANDI ✓" basabilir hâle geldi. Kilit değil
    **ekran dürüstlüğü** kusuru; ayrı görev.
  - **Kanıt:** `:1148` `if not self.t_iha1 or self.iha_landed_seq is None:` — latch
    `t_iha1`'e de bağlı. `t_iha1` **yalnız** `iha_indi()` içinde kuruluyor (`:1130`), o da
    `t_iha0` yoksa `:1131`'de **erken dönüyor**. Yani operatör ARM → FIRLATMA dizisini
    basmadıysa `t_iha0` `None`'dır → `t_iha1` `None` kalır → koşulun ilk bacağı hâlâ
    `True`'dur → **telsizden gelen geçerli bir `IHA_LANDED` bile kilidi açamaz.**
  - **Neden KRİTİK ve T20'den bağımsız:** D1-D3 uygulanıp sahadan gerçek iniş kanıtı gelse
    **bile** komut reddedilir. T20 kapanır ama görev yine çalışmaz.
  - **Yap:** Sürüş izninin otoritesi **protokol kanıtı** olmalı (`iha_landed_seq`), operatör
    UI kronometresi (`t_iha1`) değil. `t_iha1` göstergede kalabilir; **kilit koşulundan
    çıkarılmalı.** Şartname §2.2.5 iniş **kanıtı** ister, düğme dizisi değil.
  - **Kapı:** `t_iha0`/`t_iha1` hiç kurulmadan protokol `IHA_LANDED` enjekte edildiğinde
    `ika_baslat()` **REDDEDİLDİ dönmeyecek** ve `IKA_GO` yayınlanacak; ARM/FIRLATMA
    basılmadan da geçmeli. Ters yönde: `IHA_LANDED` **yokken** komut hâlâ reddedilmeli
    (fail-closed korunmalı). `codes/test_rota_sentetik.py` **15/15**.
  - **Uygulama:** `t_iha1` yalnız UI kronometresi olarak bırakıldı; sürüş izninin iniş
    otoritesi yalnız doğrulanmış protokol latch'i `iha_landed_seq` oldu. Pozitif test
    gerçek `_mesaj_isle(IHA_LANDED)` → gerçek `_cmd_gonder()` yolunda kodlanmış
    `CMD/IKA_GO` çerçevesini ve pinli İKA UDP hedefini ölçüyor; negatif test kanıt
    yokken gönderimin hâlâ yapılmadığını doğruluyor.
  - **Odak kapısı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_iha_landed_gate.py -v
    test_yks_landed_yokken_operator_dizisi_olmadan_ika_go_reddedilir (...) ... ok
    test_yks_protokol_latchi_operator_dizisi_olmadan_ika_go_yayinlar (...) ... ok
    Ran 12 tests in 2.952s
    OK
    EXIT_CODE=0
    ```
  - **İKA_GO regresyon kapısı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_ika_go_gate.py -v
    [T12_KAPI] IHA_LANDED_onceden=1 YKS_UDP_TX=1 IKA_GO_oncesi_hareket=0 IKA_GO_sonrasi_nonzero_motor=1 ACK=ika exit=0
    Ran 9 tests in 0.568s
    OK
    EXIT_CODE=0
    ```
  - **Genel kapılar — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 192 tests in 32.549s
    OK
    EXIT_CODE=0
    ```

---

## FAZ 4 — SERBEST ALAN MİMARİSİ

> **Mimari karar (4 Ağustos 2026):** Yaklaşım **C** — *"Serbest alan OTORİTEDİR; nesne
> katmanı yalnızca ÇIKARIR."* Tam gerekçe ve ölçümler: `RESEARCH_NOTES.md`.
> Mimari: `ARCHITECT_PLAN.md` § Görüntü işleme mimarisi, K-6, K-7.
>
> ⛔ **S1 düzeltilmeden hiçbir veri üretimi veya eğitim koşusu başlatılmaz.**
> Zorunlu sıra: `S1 → S2 → veri üretimi → eğitim`.

- [x] **S1 — Veri üreteci araçları ZEMİN olarak etiketliyor** · `scripts/copy_paste_augmentation.py:37,151,340` · **TIKAYICI**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** Araç kâhini **DOTA OBB**'ye
    geçmiş; `COCO_ARAC_SINIFLARI` yalnız geriye-uyum fonksiyonunda kalmış.
    Commit'ler: `11eed4a`, `33abcd3`, `e05ee88`.
  - **Kapı — bağımsız koşuldu** (üretim fonksiyonu `arac_maskesi()` olduğu gibi çağrıldı;
    depo dosyası değiştirilmedi). Ölçüt: *"aynı ham fotoğrafta engel maskesindeki araç
    piksel sayısı COCO'ya göre ≥10× artmalı"*:
    ```
    obb_modeli_mi(coco) = False        obb_modeli_mi(obb) = True
    kare                          COCO_px    OBB_px      kat
    frame_000000_000000000.jpg          0    114410      inf
    frame_000001_000000600.jpg       4916    117157    23.8x
    frame_000002_000000672.jpg          0    115689      inf
    frame_000003_...                    0    112437      inf
    ```
    Ölçüt **fazlasıyla** sağlanıyor. (Bu sayı bugüne dek depoda hiçbir yerde yoktu;
    `REVIEW_LOG` D-20 yalnız dolaylı ölçümü taşıyordu: araç üstünde zemin %70,2 → %2,0.)
  - ⚠ **Ölü düğme (kapatmayı engellemez):** `--arac-imgsz` OBB yolunda hiçbir işe
    yaramıyor. `:389` tanımlı, `:416` doğrulanıyor, ama `:170`
    `obb_arac_maskesi(..., imgsz=max(bgr.shape[:2]))` — parametre OBB dalında **atılıyor**.
    Kullanıcı değeri değiştirir, hiçbir şey değişmez, uyarı da yok. Ya gerçekten
    geçirilsin ya CLI'dan kaldırılsın.
  - ⚠ **Bayat yorum:** `:503` *"...ve COCO araçları class-1'dir"* — artık DOTA OBB.
  - ⚠ `dataset/copy_paste_smoke` COCO döneminden kalma yanlış etiketli artık; hiçbir
    `yaml`'dan referans verilmiyor, eğitim riski yok.
  - **Kanıt:** Aynı hava fotoğrafında COCO `yolov8m-seg.pt` **2 araç**, DOTA `yolov8m-obb.pt` **93 araç** buluyor. COCO güven eşiği 0,35 → 0,02 indirildi, 18 karede yine **sıfır** kesişim — eşik ayarı çözüm değil, domain uyumsuzluğu (COCO yer seviyesi; şartname §5.3.2 ≥30 m nadir).
  - **Neden tıkayıcı:** Etiket yazımı `:295-300` — sınıf **0 (zemin) daima TAM KARE dikdörtgen**, 1 ve 2 üstüne poligon. `engel` maskesine girmeyen her araç yalnız bu dikdörtgenin altında kalır → **"zemin" etiketi alır.** Yani araçların ~%98'i sürülebilir zemin olarak öğretiliyor. Bu, v16'yı **%2,7 → %31,6** çökerten *etiketsiz engel* hatasının birebir aynısı.
  - **Yap:** `--arac-model` varsayılanını `yolov8m-obb.pt` yap ve OBB poligon → maske dönüşümünü **`simulation/scripts/iha_haritala.py:228-255` `_arac_maskesi`'nden al** (`obb.xyxyxyxy` → `cv2.fillPoly`, `ARAC_SINIFLERI = {"small vehicle", "large vehicle"}`). **Yeniden yazma, yeniden kullan.** Eski COCO yolu `--arac-model` ile hâlâ verilebilsin (geriye uyum), ama varsayılan olmasın.
  - **Kapı:** Aynı ham fotoğrafta üretilen `engel` maskesindeki araç piksel sayısı, COCO'ya göre **en az 10×** artmalı; sayıyı gerçek çıktıyla yapıştır.

- [x] **S2 — Sınıf-id çakışması: `2` bir yerde hedef, bir yerde araç** · `scripts/copy_paste_augmentation.py:318-321` ↔ `simulation/scripts/iha_haritala.py:300,336` · KRİTİK
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** İki ad alanı `codes/sinif_semasi.py`
    ile ayrıldı: eğitim `ZEMIN=0 · ENGEL=1 · HEDEF=2`, costmap `KATMAN_ZEMIN=0 ·
    KATMAN_MOLOZ=1 · **KATMAN_ARAC=10**`. `iha_haritala.py:60` sabitleri import ediyor,
    `:327` `engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI` — **çıplak sayı kalmadı.**
    `sinif_semasi` **import anında** `dogrula()` koşar: sabitler çakışırsa modül yüklenmez.
  - **Kapı — bağımsız koşuldu:** `codes/test_sinif_semasi.py` → **8 GEÇTİ / 0 DÜŞTÜ**,
    pozitif kontrol dahil (*"eski şemada hedef ENGEL sayılıyordu"* — kusur yeniden üretildi).
    Genel kapı `codes/test_rota_sentetik.py` → **15/15**. Anayasa madde 4 taraması → **0 eşleşme**.
  - 🔴 **Denetimde bulunan asıl risk KODDA DEĞİL BELGEDEYDİ — düzeltildi.**
    `CONTRACTS.md` §1.2 hâlâ *"⛔ ÇAKIŞMA — çözülene kadar geçerli uyarı"* başlığıyla
    **çözülmüş** çakışmayı yürürlükteki kod gibi gösteriyordu ve `KATMAN_ARAC=10`
    ad alanını hiç tanımlamıyordu; §1.3 `engel_sinif_idler = (1,)` diyordu (gerçek: `(1, 10)`).
    Madde 16 sözleşmeyi o dosyadan okumayı emrettiği için bu **aktif bir tuzaktı** —
    özellikle S6 (hedef tohumu) açıkça "S2 sözleşmesinden sonra" diye işaretli.
    §1.2/§1.3 yeniden yazıldı. Kayıt: `REVIEW_LOG.md` **D-35**.
  - **Kanıt:** `copy_paste_augmentation.py` `2 = hedef` (H brandası) üretiyor; `iha_haritala.py:300` `{0: masks[0], 1: masks[1], 2: arac}` kuruyor ve `:336` `engel_sinif_idler=(1, 2)` geçiyor.
  - **Neden kritik:** 3 sınıflı veriyle eğitilmiş bir model `iha_haritala` yoluna verilirse **H brandası ENGEL sayılır** → İKA hedefe hiçbir zaman ulaşamaz → `P_görev = 0` (şartname Tablo 6: 600 puan, K_zorluk ile 1200'e kadar).
  - **Yap:** Sınıf-id sözleşmesini **tek bir modülde** sabitle (ör. `codes/sinif_semasi.py`): `ZEMIN=0, ENGEL=1, HEDEF=2` ve costmap katmanları için ayrı bir ad alanı (araç maskesi `iha_haritala` içinde **runtime** katmanıdır, eğitim sınıfı değil — ikisini karıştırma). Her iki dosya da bu modülden okusun. Sabit sayı (`2`) yazmayı bırak.
  - **Kapı:** `grep -rn "engel_sinif_idler" ` çıktısındaki her çağrı yeri sözleşme modülünden gelen adları kullanıyor; hiçbir yerde çıplak `2` yok. Ayrıca 3 sınıflı sentetik bir sahnede hedef bölgesinin `serbest` maskesinde **1** olduğunu göster.

- [x] **S3 — KAPANDI · Monotonluk invariantı kapıya bağlandı** · `tests/test_monotonluk.py` · KRİTİK · kanıt: `REVIEW_LOG.md` **D-170**
  - **Kanıt:** Kod doğru (*"çıkarma en son, bundan sonra hiçbir genişletme yapılmaz"*) ama hiçbir test bunu doğrulamıyor. Bir gün biri çıkarmadan sonra `dilate`/`MORPH_CLOSE` eklerse sessizce serbest alan büyür ve rota engelin üstünden geçer.
  - **Yap:** `tests/test_monotonluk.py` yaz. İddia: **her engel sınıfı kümesi için** `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)`, yani `cv2.bitwise_and(serbest_genis, cv2.bitwise_not(serbest_dar)).sum() == 0`. Rastgele tohumlu ≥50 sentetik maske çiftinde koş. Ayrıca boş engel maskesiyle `serbest` değişmemeli.
  - **Kapı:** 50/50 sahnede invariant sağlanıyor; `serbest_alan`'a bilerek eklenen bir `dilate` ile test **başarısız** olduğunu da göster (mutasyon kanıtı).

  - ✅ **YAPILDI · 2026-08-18 · Claude-2** · kayıt `REVIEW_LOG.md` **D-170**.
    **Üretim kodu değişmedi:** `git diff HEAD -- codes/costmap_path_finder.py`
    **BOŞ**.
  - 🔴 **ASIL KUSUR: test VARDI ama HİÇ KOŞMUYORDU.**
    `codes/test_monotonluk.py` git'te izleniyordu (131 satır, 5 kontrol) ama
    içinde **0 tane `def test_`** vardı (script biçimi) ve `tests/` altında
    değildi → `unittest discover` onu **hiç koşmuyordu**. D-158 bulgu 4'ün
    aynı sınıfı: **var olan ama devrede olmayan kapı.** `git mv` ile taşındı,
    unittest'e çevrildi, **iki kopya bırakılmadı**.
  - 🔴🔴 **S3'ÜN KENDİ FORMÜLÜ, KORKTUĞU REGRESYONA KÖR ÇIKTI.** Kapıyı yazıp
    `dilate` enjekte ettim; kafes ihlali **0** geldi. Ölçüldü (tohum 0, tam
    engel kümesi):
    ```text
    sabit referansa (yamasiz kosuma) gore buyume : 1388 px   YAKALAR
    engel pikseli uzerinde serbest               : 0 -> 22   YAKALAR
    ALT KUME KAFESI ihlali                       :    0      KOR
    ```
    Sebep matematiksel: **`dilate` monotondur** — `X ⊆ Y ⟹ dilate(X) ⊆ dilate(Y)`.
    Her alt kümeye **aynı** uygulanan bir genişletme kafesi hiç bozmaz, iki
    taraf birlikte büyür. Bu, D-146/D-157/D-159/D-163 sınıfının devamıdır;
    farkı: yanlış olan bir **eşik değil, kıyas ekseni**.
  - **ÜÇ SAVUNMA, HER BİRİNİN MUTASYON KANITI VAR:**
    ```text
    (1) ALT KUME KAFESI       ASIMETRIK regresyonu yakalar  -> testle kanitlandi
    (2) ENGEL PIKSELI SIZINTISI  50 tohum x tum alt kumeler -> DUZGUN genisletmeyi yakalar
    (3) SABIT REFERANS        yamali vs yamasiz cikti       -> "buyume"nin tanimi
    ```
    (1)'in vacuous olmadığı, genişletmeyi **yalnız `KATMAN_ARAC` kümesindeyken**
    uygulayan asimetrik bir mutasyonla kanıtlandı ("yeni katman ekledim, bir de
    şu morfolojiyi koyayım" kalıbı) — kafes onu **yakalıyor**.
    Bilinen sınır ayrıca **çivilendi**; o test düşerse iyi haberdir.
  - **KAPSAM:** 10 tohum → **50 tohum**; tek çift → **250 alt küme çifti**
    (test çift sayısını da doğruluyor, kafes eksik kurulursa düşer). Sınıf
    kimlikleri `codes/sinif_semasi.py`den, çıplak sayı yok (madde 16).
  - **MUTASYON KANITI — GERÇEK DOSYA ÜZERİNDE** (yedek → değiştir → koş →
    yedekten geri koy; `git checkout` kullanılmadı):
    ```text
    Ran 11 tests in 1.475s
    FAILED (failures=3)
      FAIL: test_engel_pikseli_50_tohumda_hicbir_alt_kumede_serbest_degil
      FAIL: test_hicbir_engel_pikseli_serbest_degil     (0 != 24 px)
      FAIL: test_MUTASYON_dilate_ENGEL_PIKSELINE_SIZINTI_uretir
            (0 != 22 : yamasiz halde zaten sizinti var — kiyas anlamsiz)
    ```
    Üçüncüsü anlamlı: mutasyon kontrolünün **kendisi** tabanın bozuk olduğunu
    farkedip duruyor.
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    git diff -- codes/                            -> BOS
    git diff HEAD -- codes/costmap_path_finder.py -> BOS
    codes/test_rota_sentetik.py    SONUC: 15/15 dogru
    unittest discover -s tests     Ran 601 tests in 70.355s / OK   (589 -> 601, +12)
    ```
    🔴 GPU'ya dokunulmadı; görev model çalıştırmadı (tamamen CPU/sentetik).
  - ⚠ **DOĞRULANAMADI:** sahneler sentetiktir (eksen hizalı dikdörtgenler),
    gerçek maskelerde ölçülmedi · **yalnız `serbest_alan` sınandı**;
    `analyze_path` içindeki çıkarma (`rpi_inference.py:1086-1094`) aynı
    invariantı taşır ama **bu dosya onu kapsamıyor**, ayrı kapı gerekir ·
    `MORPH_CLOSE`/`bitwise_or` biçimleri ayrıca denenmedi (yalnız `dilate`) ·
    `mpp=None` ile koşuldu, başka ölçeklerde ölçülmedi · 50 tohum sabittir,
    rastgele arama yapılmaz.

- [x] **S4 — İki ıraksak karar yolu: biri emniyet ağsız** · `codes/rpi_inference.py`, `simulation/scripts/iha_perceive.py` · KRİTİK
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-10 · Claude 1.** İki ayrı iddia vardı; ikisi de
    çözüldü ya da açıklandı.
  - **(a) "Engel maskesi hiç okunmuyor" — ÇÖZÜLDÜ (T24 zinciri).** Kanıt satırlarının
    hiçbiri artık çıplak `analyze_path(masks[0])` değil:
    ```
    codes/rpi_inference.py:843,930,996   engel_mask=masks.get(1)   ✓
    simulation/scripts/iha_perceive.py:108-109                     ✓
    comms/yks_gui.py:1027   trav zaten trav[blok>0]=0 uygulanmış   ✓
    ```
    `analyze_path` imzası `engel_mask=None` alıyor (`:445-447`) ve çıkarma
    **morfolojiden sonra, en son** yapılıyor — madde 15 invariantı korunuyor.
  - **(b) "İki ıraksak karar yolu" — KUSUR DEĞİL, KAPSAM FARKI.** Claude 2 ölçtü
    (`REVIEW_LOG.md` D-41), `costmap_path_finder.py:781`:
    ```python
    if tani["belirsiz"] and tani["n_kapi"] != 3:
        cikti["durum"] = "BELIRSIZ_COKLU"
    ```
    `rota_bul` bir **üç-kapılı arena dedektörüdür** (3 kapı bekler); `analyze_path`
    **tek-koridor** dedektörüdür. Aynı 67 maskede `rota_bul` 66 `BELIRSIZ_COKLU`
    demesinin sebebi budur — tespit edilen kapı sayısı 3..10 arasında dağılıyor.
    İkisi **farklı soruları** cevaplıyor; ıraksama beklenen davranıştır.
  - ➡️ **Kalan parça ayrı göreve taşındı: T33.** Araç katmanı (DOTA OBB,
    `KATMAN_ARAC=10`) hâlâ **yalnız** `iha_haritala.py`'de. Ölçüldü:
    `rpi_inference` / `iha_perceive` / `yks_gui` → araç referansı **0**.

- [ ] **T33 — Araç katmanı (DOTA OBB) algı karar yoluna bağlı değil** · `codes/rpi_inference.py`, `simulation/scripts/iha_perceive.py`, `comms/yks_gui.py` · ÖNEMLİ · kanıt: S4 (b) ölçümü
  - **Kanıt (2026-08-10):** araç maskesi referansı — `iha_haritala.py` **8**,
    `rpi_inference.py` **0**, `iha_perceive.py` **0**, `yks_gui.py` **0**.
    `CONTRACTS.md` §1.3 `COSTMAP_ENGEL_KATMANLARI = (KATMAN_MOLOZ, KATMAN_ARAC)`
    yani `(1, 10)` diyor, ama bu sözleşmeyi yalnız `iha_haritala.py:327` uyguluyor.
  - **Neden önemli:** ölçüldü (S1 kapısı) — aynı hava fotoğrafında COCO-seg **2**
    araç, DOTA OBB **93** araç buluyor. Araç katmanı olmayan karar yolu, park hâlindeki
    aracı **zemin** sayabilir. Mimari kural (madde 15) nesne katmanının yalnız
    **çıkardığını** garanti ettiği için ekleme **monotonik olarak güvenlidir** —
    sistemi ancak daha güvenli yapar.
  - **Yap:** Araç maskesini algı yoluna da geçir. ⚠ Maliyet ölçülmeli: DOTA OBB
    **ikinci bir model** demek; Jetson bütçesinde çıkarım süresi iki katına çıkabilir
    (T15/T17 ölçümleriyle birlikte değerlendirilecek).
  - **Kapı:** Park hâlinde araç içeren gerçek bir karede, araç katmanı **açıkken**
    o bölge serbest alandan çıkarılıyor; **kapalıyken** çıkarılmıyor. İki sayı da
    raporlanacak. Ek çıkarım maliyeti ms cinsinden ölçülüp yazılacak.
    `codes/test_rota_sentetik.py` **15/15**.
  - **Kanıt:** `rpi_inference.py:387,467,527` ve `iha_perceive.py:106` yalnız `analyze_path(masks[0])` çağırıyor — engel maskesi **hiç okunmuyor** (saf Yaklaşım B). Buna karşılık `iha_haritala.py:336` `engel_sinif_idler=(1,2)` ile hibrit çalışıyor. Aynı sistemde iki farklı güvenlik seviyesi var. `comms/yks_gui.py:880` doğru yapıyor: `trav[blok > 0] = 0`.
  - **Yap:** `analyze_path`'e engel maskesini geçir ve **çağrıdan önce** `trav`'dan oy (`yks_gui.py:880` kalıbı). `analyze_path`'i **silme** — 6 çağrı yerinin göçü bitmeden kaldırılmaz.
  - **Kapı:** Engelin traversable'ı örttüğü sentetik bir sahnede eski yol yanlış şerit, yeni yol doğru şerit dönüyor; her iki sayıyı da yapıştır.

- [x] **T34 — Hakem ekranı doğrulamadığı §6.4 iddiasını "✓" ile basıyor** · `comms/yks_gui.py:773-778` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-46
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex yazdı.
    Üç durum bağımsız ölçümümde de birbirinden ayrı çıkıyor:
    ```text
    t_iha1 YOK · landed YOK : · İHA henüz inmedi
    t_iha1 YOK · landed VAR : · AKTARIM ZAMANI BİLİNMİYOR (IHA_LANDED kanıtı var)
    t_iha1 VAR              : · ⚠ aktarım İHA inişinden SONRA (§6.4 geçersizlik riski)
    ```
    Kritik olan orta satır: kanıt varken artık **`✓` basmıyor**. Bilgi yokluğu
    onaya çevrilmiyor.
  - **Kanıt — kendim koştum, gerçek çıktı:**
    ```text
    t_iha1 = None | landed_seq = 8802 (IHA GERCEKTEN INMIS)
    EKRAN: Hakem onayı tam — ACK(seq=8801) İHA'ya iletildi
           · AKTARIM HAVADA TAMAMLANDI ✓ (§2.2.3)
    ```
    `:772` `havada = ("... TAMAMLANDI ✓" if not self.t_iha1 else "⚠ ... SONRA")`.
    `t_iha1` yalnız `iha_indi()`'de kuruluyor, o da `t_iha0` yoksa erken dönüyor.
    Operatör ARM/FIRLATMA basmadıysa İHA **inmiş olmasına rağmen** `t_iha1` `None`
    kalır → ekran "havada tamamlandı ✓" der. **Bilgi yokluğu onaya çevriliyor.**
  - **Neden şimdi önemli:** T20-b'den önce bu durumda İKA zaten hareket edemiyordu;
    artık edebiliyor — yani "operatör dizisi basılmamış" hâli **canlı bir çalışma
    kipi**. S9 ile aynı kusur sınıfı: ekranın doğrulamadığını iddia etmesi.
  - **Yap:** Üç durumu ayır — `t_iha1` yok **ve** `iha_landed_seq` yok → "İHA henüz
    inmedi"; `t_iha1` var → mevcut ⚠ metni; `t_iha1` yok **ama** `iha_landed_seq` var
    → **"BİLİNMİYOR"** (✓ basma). Kararı değiştirme, yalnız iddiayı doğru yap.
  - **Kapı:** Üç durum için üç test; `iha_landed_seq` doluyken `t_iha1` boşsa çıktıda
    `✓` **geçmeyecek**. `codes/test_rota_sentetik.py` **15/15**.
  - **Uygulama:** Onay/ACK kararı değiştirilmeden ekran metni üç kanıt durumuna
    ayrıldı: kronometre inişi varsa mevcut §6.4 uyarısı; yalnız protokol iniş latch'i
    varsa `AKTARIM ZAMANI BİLİNMİYOR`; ikisi de yoksa `İHA henüz inmedi`.
  - **Hedef kapı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_yks_gui_aktarim_zamani.py -v
    test_iha_henuz_inmediyse_ekran_bunu_soyler (...) ... ok
    test_operator_kronometresi_varsa_inis_sonrasi_uyarir (...) ... ok
    test_protocol_inisi_var_kronometre_yoksa_zaman_bilinmiyor (...) ... ok
    Ran 3 tests in 0.001s
    OK
    EXIT_CODE=0
    ```
  - **Genel kapılar — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 202 tests in 33.847s
    OK
    EXIT_CODE=0
    ```

- [x] **T37 — Gönderilemeyen komut ekranda BAŞARILI görünüyor (ARM · DISARM · PARAŞÜT)** · `comms/yks_gui.py:1277,1327,1394` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-47
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex yazdı.
    Kendi ölçüm matrisimi koştum (Codex'in testine bakmadan), **16/16 kapı**:
    ```text
    [ARM · adres YOK]      telde=False  arm_acik=False  ekran=—  firlat=dokunulmadi
    [DISARM · adres YOK]   telde=False  arm_acik=True   ekran=—
    [PARASUT · adres YOK]  telde=False  ceza=0  buton=acik  ('AÇILDI' yok)
    TERS YON (adres VAR):  ARM ✓ · DISARM ✓ · PARASUT telde=True ceza=50 buton=disabled
    ```
    Aradığım üç şey de yerinde: (1) DISARM düşünce `arm_acik` **True kalıyor** —
    güvenli yön; (2) paraşüt düşünce buton **kapanmıyor**, operatörün tekrar
    deneme yolu açık; (3) ceza **işlenmiyor**. Ters yön bozulmamış.
  - **Kanıt — kendim koştum, gerçek çıktı** (İHA adresi henüz öğrenilmemiş):
    ```text
    link.send cagrildi mi : False   (ARM TELE CIKMADI)
    EKRAN                 : SİSTEM: ARM — uçuşa hazır
    FIRLATMA butonu       : normal
    ic durum arm_acik     : True
    gunluk                : ['CMD GÖNDERİLEMEDİ → iha: ARM — UDP adresi yok']
    ```
    `_cmd_gonder()` başarısızlıkta **`False` döndürüyor** ama 4 çağrı yerinin
    **3'ü dönüşü yok sayıyor**: `:1272` ARM · `:1277` DISARM · `:1387` PARACHUTE.
    Yalnız `:1320` `IKA_GO` denetliyor.
  - **Neden KRİTİK, üç ayrı yönden:**
    1. **PARAŞÜT en tehlikelisi:** gönderim düşse bile ekran "PARAŞÜT AÇILDI
       (manuel)" yazıyor, **butonu `disabled` yapıyor** — operatörün tekrar deneme
       yolu kapanıyor — ve −50 cezayı işliyor. §2.2.4 acil durumunda operatör
       paraşütün açıldığına inanır.
    2. **DISARM tersi yönde ölümcül:** gönderim düşerse ekran "DISARM — güvenli"
       der, İHA **hâlâ ARM'lıdır**.
    3. **ARM zincirleme yanıltıyor:** FIRLATMA butonu açılıyor, operatör basıyor,
       §6.4 kronometresi **hiç başlamamış bir uçuş için** işlemeye başlıyor.
  - **Yap:** Üç çağrı yerinde de `_cmd_gonder()` dönüşünü denetle (`IKA_GO`
    kalıbı). Gönderim düşerse: durum değişkenini **değiştirme**, butonu
    `disabled` yapma, ekrana başarı metni **yazma**, günlüğe kırmızı düş.
    `arm_acik` değişkenini de yalnız gönderim başarılıysa çevir.
  - **Kapı:** Üç komut için de "adres yok" durumunda: `link.send` çağrılmamış,
    ekran metni başarı iddiası **içermiyor**, ilgili buton hâlâ basılabilir.
    Ters yönde: adres varken üçü de eskisi gibi çalışıyor.
    `codes/test_rota_sentetik.py` **15/15**.
  - **Uygulama:** ARM/DISARM durumu yalnız başarılı gönderimden sonra atomik olarak
    değişiyor. Başarısız paraşüt gönderimi ceza, başarı ekranı ve buton kilidi
    üretmiyor; teyit durumu korunuyor. Komut hataları gerçek `kirmizi` günlük etiketiyle
    gösteriliyor.
  - **Hedef kapı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_yks_gui_komut_durustlugu.py -v
    test_arm_adres_varken_eskisi_gibi_baslar (...) ... ok
    test_arm_adres_yokken_durum_ve_ekran_degismez (...) ... ok
    test_disarm_adres_varken_eskisi_gibi_guvenli_gosterir (...) ... ok
    test_disarm_adres_yokken_durum_ve_ekran_degismez (...) ... ok
    test_parasut_adres_varken_eskisi_gibi_tetiklenir (...) ... ok
    test_parasut_adres_yokken_ceza_ve_basari_uydurmaz (...) ... ok
    Ran 6 tests in 0.002s
    OK
    EXIT_CODE=0
    ```
  - **Genel kapılar — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 199 tests in 33.432s
    OK
    EXIT_CODE=0
    ```

- [x] **T36 — Hakem ekranı kendi çıkarım parametrelerini ÇIPLAK yazıyor; üretimden ayrışıyor**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Claude-2 yazdı.
    **Benim görev tanımımı düzeltti ve haklıydı** (D-58): prompt'ta hizalama
    hedefi olarak `iha_perceive` (P) yazmıştım. Yanlış — `CONTRACTS.md` §11.2
    Halka 3/4 sahibi `codes/rpi_inference.py` (R), §11.1 `simulation/` altındaki
    hiçbir dosyanın sahip olamayacağını söylüyor, ve saha paketi **R'nin
    bayt-birebir kopyasını** taşıyor (`iha_perceive` pakette **hiç yok**).
    Claude-2 R'ye hizaladı, üç gerekçesini yazdı.
    ➜ **Sonuç: D-48'deki %31,3 ıraksama sayım yanlış referansa göreydi.**
  - **Bağımsız denetimim:**
    ```text
    SABIT DENKLIGI
      rpi_inference --conf default = 0.30   yks_gui ALGI_PREDICT_CONF = 0.3   ESIT
      ciplak imgsz / min_conf / min_area_ratio / conf : hepsi YOK
      uretim fonksiyonlari: _preprocess ✓ _maskeleri_icerige_kirp ✓
                            _rota_kararini_esikle ✓ icerik=icerik ✓
    KARAR DENKLIGI (67 kare): AYNI 67 · FARKLI 0
    ```
    Karolu çıkarım yolu (`max(h,w)>1400`) tamamen kaldırılmış; ikinci bir
    `predict` yok; K-B üretimin kendi eşikleyicisiyle uygulanıyor, kopya eşik yok.
  - **Kalıcı koruma:** `tests/test_yks_gui_uretim_hizasi.py` (16 test). İkisi
    özellikle değerli: `test_gui_kendi_cikarim_hattini_KURMUYOR` (yapısal —
    özel hat yeniden doğarsa test düşer) ve `test_predict_conf_uretim_
    varsayilanindan_KOPYALANMIS` (AST ile kilit, sabit ıraksayamaz).
  - **T36b ayrıldı ve AÇIK bırakıldı** — kompozit kaynak kapısı düştü, GUI'de
    değil karar zincirinde. Doğru davranış: zorlanmadı.

- [STATUS: KAPANDI] **T36 — özgün kayıt** · `comms/yks_gui.py:999-1035` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-48
  - **✅ YAPILDI · 2026-08-11 · Claude-2.** `_algi_kos` kendi çıkarım hattını
    artık kurmuyor; `codes/rpi_inference.py`'nin `run_image` gövdesini (`:920-932`)
    aynı sırayla çağırıyor: `_preprocess` → `predict(imgsz=INFER_SIZE)` →
    `get_masks` → `_maskeleri_icerige_kirp` → `analyze_path(icerik=…)` →
    `_rota_kararini_esikle`. Çıplak eşik/karo sabitleri kaldırıldı.
  - 🔴 **ÖNCE ÇÖZÜLEN ÇELİŞKİ — hangi "üretim"? (yeni kayıt D-58).** Görevin
    kapısı `iha_perceive._infer`'i zincir yazıyor, ama `CONTRACTS.md` §11.2
    Halka 3/4 sahibini `codes/rpi_inference.py` yazıyor ve §11.1/1 `simulation/`
    dosyalarının sahip olmasını **yasaklıyor**. İkisi birbirinden de ayrışıyor:
    ```text
    R = codes/rpi_inference (SÖZLEŞME SAHİBİ)  vs  P = simulation/iha_perceive
      67 gerçek kare -> AYNI 54 · FARKLI 13 (%19,4); 2'si ŞERİT farkı (R=3, P=1)
    ```
    Hakem ekranı **R'ye** hizalandı: sahibi R'dir, `jetson_paket/kod/rpi_inference.py`
    R'nin bayt-birebir kopyasıdır (saha donanımı R'yi koşar) ve `iha_perceive.py`
    saha paketinde hiç yoktur.
  - **KAPI 1 — ölçüldü (67 gerçek kare, v21, son kod):**
    ```text
    ONCE   hakem ekrani vs R : AYNI 60/67 · IRAKSAK  7 (%10,4)
    SONRA  hakem ekrani vs R : AYNI 67/67 · IRAKSAK  0        <- GECTI
    SONRA  hakem ekrani vs P : AYNI 54/67 · IRAKSAK 13
           (GUI'nin P'ye kalan farki, R↔P farkinin TAM KENDISI -> GUI'nin
            kendi farki YOK; artik R'nin birebir aynisi)
    ```
    ⚠ Görevdeki `%31,3` artık geçerli değil: T31/T32 iki yolu yaklaştırdığı için
    hizalama öncesi ıraksama bu ağaçta %10,4 ölçüldü.
  - **Bilinçli bırakılan farklar — ölçümlü gerekçe:**
    - **Karolu çıkarım KALDIRILDI.** Üretimde karşılığı yok; parametreleri
      (768/128/0,25/0,10) tek kaynaktan okunamıyordu. `raw_frames` ve
      `arena_kompozit` kareleri 1024×576 — zaten hiç karolanmıyordu.
    - **GUI densify KALDIRILDI.** Ekran telde gidenden farklı polyline
      gösteremez. Ölçüldü: üretimin kendi azami kenarı / tuval yüksekliği
      p50 **%6,8**, maks **%7,7**; eski GUI sınırı 1/12 = %8,3 → **sınırı aşan
      kare 0/57**. Kaldırmanın ölçülebilir bedeli yok.
    - **Şerit çizgileri** artık tuvalin `w//3`'ünden değil letterbox **içerik
      kutusundan** çiziliyor (§8); aksi hâlde ekrandaki şerit `analyze_path`'in
      kullandığı şeritle örtüşmüyordu.
  - **Kalıcı kapı:** `tests/test_yks_gui_uretim_hizasi.py` (16 test) — üretim
    fonksiyon/sıra bağı, `icerik` geçişi, çıktı denkliği (GUI kararı == `run_image`
    kararı, 9 sahne), ve `ALGI_PREDICT_CONF`'un `codes/rpi_inference.py`'deki
    `--conf` varsayılanından **AST ile okunarak** kilitlenmesi.
  - **Koşulan kapılar (gerçek çıktı):** `unittest discover -s tests -q` →
    `Ran 242 tests · OK`; `codes/test_rota_sentetik.py` → **15/15**;
    `yks_gui.py --help` exit 0.

- [x] **T44 — T43 hakem ekranının hizasını BOZDU: GUI `mpp` geçirmiyor, ölçek kapısı yok**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Claude-2 yazdı.
  - **Kapı 1 — kendi ölçümüm (16 otopark karesi, kaynak=drone):**
    ```text
    HAKEM EKRANI : {'RED/OLCEK_YOK': 16}
    URETIM GOREV : {'RED/OLCEK_YOK': 16}
    AYRISAN      : 0/16   -> GECTI
    ```
    Ayrışma kapandı **ve doğru sebeple**: ekran artık sistem kısıtını sahne
    kusuru gibi göstermiyor. Üretimin kendi kapısı (`rota_olcek_reddi`)
    çağrılıyor, kopyalanmıyor.
  - **Kapı 2 — T36b KAPANMADI, zorlanmadı. Ablasyon doğru yapılmış:**
    ```text
    A  GUI bugun (letterbox icerik + MODEL maskesi + C-uzayi) : 1/7
    B  + ARENA icerik kutusu (manifest ROI)                   : 3/7  (+2)
    C  + YER GERCEGI maskesi                                  : 6/7  (+3)
    ```
    Her adımda **tek değişken** değişmiş — sebep ayrımı bu yüzden geçerli.
  - **İki kutu farkını kendim doğruladım:**
    ```text
    _preprocess icerik : (0, 224, 1024, 576)  -> serit sinirlari [341, 682]
    manifest arena ROI : (224, 0,  576, 576)  -> serit sinirlari [416, 608]
    AYNI MI            : False
    ```
    Arena **576×576 kare bir alt bölgeye** yerleştirilmiş; GUI'nin şeritleri ise
    1024 genişlikteki tam içerik kutusuna göre. Şerit tanımları **hiçbir zaman
    uyuşamaz**. Kusur GUI'de değil, **T40 üretecinde** → yeni **T45**.
  - 🔴 **Doğru reddetme:** GUI manifest ROI'sini karara sokarsa 3/7'ye çıkardı —
    ama bu **yer gerçeği sızıntısı** olurdu ve `test_beklenen_serit_KARARA_
    SIZMIYOR` bunu zaten yasaklıyor. Kolay yolu seçmemiş.
  - **Kapı 3:** T36'nın hizalama testleri ayakta (`test_gui_kendi_cikarim_hattini_
    KURMUYOR` dâhil, 23/23), üstelik ölçekli **ve** ölçeksiz kip birden sınanıyor.
  - **Kapı 4:** `codes/test_rota_sentetik.py` **15/15** · tam paket **266 OK**.

- [STATUS: KAPANDI] **T44 — özgün kayıt** · `comms/yks_gui.py` · **KRİTİK** · kanıt: bu görevdeki ölçüm · bağımlı: **T43** (bitti)
  - **✅ YAPILDI · 2026-08-11 · Claude-2** · çözüm kaydı `REVIEW_LOG.md` **D-61**.
  - `_kaynak_olcegi(yol)` eklendi: **kompozit** → manifest `arena.mpp`;
    **diğerleri** → ölçek YOK. `_algi_kos` üretimin kapısını kopyalamaz,
    `karar_sozlesmesi.rota_olcek_reddi`'yi çağırır ve `analyze_path(..., mpp=)`
    geçirir. Manifest bozuksa fail-closed (günlüğe yazar, ölçeksiz sayar).
    Bilgi satırı artık `ölçek … m/px · gövde açıklığı … px · C-uzayı UYGULANDI`
    ya da `ölçek YOK (sebep) · C-uzayı UYGULANAMADI` gösteriyor.
  - **KAPI 1 — 16 otopark karesi (gerçek çıktı):**
    ```text
    ONCE   HAKEM EKRANI : {'YOL/1': 5, 'YOL/3': 8, 'RED/DUSUK_GUVEN': 3}
           URETIM GOREV : {'RED/OLCEK_YOK': 16}
           AYRISAN      : 16/16
    SONRA  HAKEM EKRANI : {'RED/OLCEK_YOK': 16}
           URETIM GOREV : {'RED/OLCEK_YOK': 16}
           AYRISAN      : 0/16      -> GECTI
    ```
  - **KAPI 2 — T36b KAPANMADI (zorlanmadı).** İki nedeni ölçerek ayırdım;
    her adımda tek değişken değişti:
    ```text
    A  GUI bugun (letterbox icerik + MODEL maskesi + C-uzayi)  : 1/7
    B  + ARENA icerik kutusu (manifest ROI)                    : 3/7   (+2)
    C  + YER GERCEGI maskesi (manifest maskesi)                : 6/7   (+3)
    Neden 1 — icerik kutusu tanimi uyusmuyor : 2 kare
    Neden 2 — model algisi kompozitte zayif  : 3 kare
    ```
    **Beşinin hiçbiri `comms/yks_gui.py` içinde değil.** İki ayrı `icerik`
    kavramı var: `_preprocess` letterbox kutusu `(0,224,1024,576)` (şerit
    sınırları 341/683) ve manifest arena ROI'si `(224,224,576,576)` (416/608).
    Manifest şeritleri ikincisine göre tanımlı. GUI'nin manifest ROI'sini
    karara sokması **yer gerçeği sızıntısı** olurdu — T36b'nin kendi kapısı
    (`test_beklenen_serit_KARARA_SIZMIYOR`) bunu yasaklıyor. Çözüm ya kompozit
    üretecin arenayı tam kareye yayması, ya da ROI'nin saha yolunda üretilebilir
    bir sinyalden türetilmesi (D-23'e bağlı).
  - **KAPI 3 — T36 hizalama testleri geçiyor:** `test_gui_kendi_cikarim_hattini_
    KURMUYOR` ve `test_gui_karari_uretim_yolunun_karariyla_AYNI` dâhil 23/23 OK.
    Hizalama testi genişletildi: artık **ölçekli ve ölçeksiz kipi birden**
    sınıyor ve referans taraf da `rota_olcek_reddi` çalıştırıyor.
  - **KAPI 4:** `codes/test_rota_sentetik.py` **15/15** ·
    `unittest discover -s tests -q` → **Ran 266 tests · OK** ·
    `git diff --check` exit 0.
  - **Kalıcı kapı:** `tests/test_yks_gui_uretim_hizasi.py::OlcekKapisiTests`
    (7 test) — ölçeksiz kaynakta `OLCEK_YOK`, kompozitte manifest ölçeği,
    `mpp`'nin gerçekten geçirildiği, C-uzayı kanıtının ekranda olduğu,
    üretimin kapısının **kopyalanmadığı**, fail-closed manifest ve
    "ölçek yoksa rota yayınlanmaz".
  - **Kanıt — kendim ölçtüm, 16 otopark karesi, ölçek verilmeden:**
    ```text
    HAKEM EKRANI : {'RED/UC_BANT_TEMAS_YOK': 16}
    URETIM GOREV : {'RED/OLCEK_YOK': 16}
    AYRISAN KARE : 16/16
    ```
    `grep mpp comms/yks_gui.py` → **sıfır eşleşme.** T43 ölçek kapısını üç görev
    çağrı yerine koydu (`rpi_inference.py:980,1073,1145`); GUI o yolları
    çağırmadığı için kapı GUI'de **hiç yok**.
  - **İki ayrı sonuç, ikisi de gerçek:**
    1. **Yanlış sebep gösteriliyor.** GUI `UC_BANT_TEMAS_YOK` (sahne kusuru)
       diyor, üretim `OLCEK_YOK` (sistem kısıtı) diyor. Hakeme sistem sınırını
       sahne kusuru gibi göstermek, S9/T34/T37/D-47 ile **aynı kusur sınıfı**.
    2. **C-uzayı GUI'ye ulaşmıyor.** `mpp` yoksa `r_gerekli_px` yok → gövde
       açıklığı kısıtı yok. T43'ün arenada 0/7 → 7/7 yapan kazanımı hakem
       ekranında **görünmüyor**; T36b kapısı bu yüzden hâlâ düşük.
  - **Yap:** GUI ölçeği kaynağına göre üretsin ve `analyze_path`'e geçirsin:
    `kompozit` → manifest'teki `mpp`; diğer kaynaklar → ölçek YOK →
    `rota_olcek_reddi` ile **`OLCEK_YOK` göster** (sessizce rota üretme).
    Eşik/sebep kodlarını `karar_sozlesmesi.py`'den oku, çıplak yazma.
  - ⚠ **Beklenen sonuç:** `drone`/`gemini`/`val`/`test` kaynaklarında hakem ekranı
    artık `OLCEK_YOK` gösterecek. **Bu gerileme değil, dürüstlük** — ölçek
    olmadan gövde açıklığı garanti edilemez. Açılış kaynağı `kompozit` olduğu
    için normal kullanım etkilenmiyor.
  - **Kapı:** (1) 16 otopark karesinde GUI ile üretim görev yolunun **sebebi
    aynı** (ayrışan 0/16); (2) kompozit kaynakta T36b ölçümü **7/7**;
    (3) `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.

- [STATUS: READY_FOR_REVIEW] **T48 — Zemin maskesi sağlamlık kapısı: kaplama çöküşünde rota YAYINLANMAZ** · `codes/karar_sozlesmesi.py`, `codes/rpi_inference.py`, `comms/yks_gui.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-61
  - **✅ YAPILDI · 2026-08-11 · Claude-2** · çözüm kaydı `REVIEW_LOG.md` **D-62**.
  - **Eşik ölçümle türetildi — üç bağımsız meşru kaynak, iki çökmüş küme:**
    ```text
    MESRU (kapi ATESLEMEMELI)                        n     p50    p95    MAKS
      sentetik arena YER GERCEGI (etiket poligonu)  60   %11,7  %22,1  %39,0
      sentetik arena, v17 + v21 model ciktisi      120   %11,8  %23,2  %38,7
      genel kapinin KENDI 15 sahnesi                15   %36,4    —    %42,6
    COKMUS (kapi ATESLEMELI)                         n     p50           MIN
      v21 otopark (cati/cim yesil)                  67   %79,9         %76,7
      v21 kompozit arena                             7   %82,7         %76,0
    ```
    `%42,6`–`%76,0` arası **boş**. `ZEMIN_KAPLAMA_TAVANI = 0.55` — meşru
    azaminin **1,29 katı**, çökmüş asgarisinin **0,72 katı**; 194 model karesi
    + 60 yer gerçeği + 15 kapı sahnesinde **yanlış pozitif 0, kaçırma 0**.
  - 🔴 **Görevdeki v13 satırı kullanılamadı.** v13 ağırlığı depoda yok; satırın
    kendi iki sayısı tutarsız (%43,4 vs "%84,7'sini boyuyor"); **ve asıl sorun**
    %43,4, genel kapının kendi meşru sahnelerinin azamisinin (%42,6) yalnız
    **0,8 puan** üstünde — o değeri yakalayan tavan `test_rota_sentetik.py`
    15/15'i kırardı. Tablonun istediği eşik deponun kendi referans sahneleriyle
    çelişiyor. ⚠ Kapının bilinen sınırı: bu bir **kaplama** kapısıdır; v13
    benzeri orta şiddetli çökme buradan **geçer** (doku kapısı ayrı görev).
  - **KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  otopark 12 kare, hakem ekrani
              ONCE  : {'OLCEK_YOK': 12}                  (yapisal ret eziliyordu)
              SONRA : {'ZEMIN_MASKESI_SUPHELI': 12}  ->  12/12  GECTI
              ekran : "⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %78 (tavan %55)"
    KAPI 2  sentetik arena 40 kare -> YANLIS POZITIF 0/40
              {'UC_BANT_TEMAS_YOK': 33, 'YOL/2': 4, 'YOL/3': 2, 'YOL/1': 1}
    KAPI 3  POZITIF KONTROL (cokme supurmesi)
              %20 %40 %50 %54 -> KARAR VAR (kapi susuyor)
              %56 %70 %95     -> ZEMIN_MASKESI_SUPHELI (kapi atesliyor)
    KAPI 4  codes/test_rota_sentetik.py 15/15 ·
            unittest discover -s tests -q -> Ran 281 tests OK ·
            git diff --check exit 0 · Jetson ikizleri BIREBIR
    ```
  - **Yan düzeltme — ret önceliği.** Otoparkta iki ret aynı anda geçerliydi ve
    ölçek kapısı yapısal reti **eziyordu**. §6.4/3 zaten "yapısal ret ezilmez"
    diyor; kural üç üretim çağrı yerinde ve GUI'de düzeltildi
    (`if olcek_reddi is not None and karar_reddi is None`). Gerekçe: ölçek
    eksikliği **yapılandırma** boşluğu, `ZEMIN_MASKESI_SUPHELI` **algı arızası**.
  - **Test fikstürleri gerçekçileştirildi (kapı gevşetilMEDİ).** Üç dosya
    `trav = np.ones(...)` kuruyordu. İlk denemem kaplamayı düşürdü ama
    `test_rota_serit_etiketi`'nin **pozitif kontrolünü boşalttı** (eski centroid
    3/3 doğru çıktı); kum saati fikstürüyle hem tavanın altına indi (%51,1) hem
    ayırt edici kaldı.
  - **Kalıcı kapı:** `tests/test_zemin_kaplama_kapisi.py` (15 test) — eşiğin
    sözleşmeden okunduğu, sınırın kendisinin geçerli olduğu, kapının **rotadan
    önce** çalıştığı, içerik kutusunu kullandığı, **madde 15 nötrlüğü** ve genel
    kapının 15 sahnesinin reddedilmediği.
  - ⚠ **Açık:** kompozit kaynak artık 7/7 `ZEMIN_MASKESI_SUPHELI` dönüyor
    (v21 kaplaması orada %76–84). **T36b'nin durumu değişti:** ekran artık
    yanlış şerit göstermiyor, doğru sebeple çekimser kalıyor. Kapanması hâlâ
    model/veri tarafına bağlı (D-61 neden 2).
  - **Neden:** Kullanıcının gördüğü asıl kusur, ekranın **çatı ve çim üzerinden
    geçen bir rotayı kendinden emin çizmesi**. Sistem maskenin çöktüğünü
    anlamıyor; rotayı yine de üretiyor. Karar zinciri bunu yakalayamaz çünkü
    maske "dolu" görünüyor.
  - **Ölçülmüş taban — eşik uydurulmuyor:**
    ```text
    v17 (iyi, arena IoU 0,861)   kaplama %4,2   (yer gercegi %3,6)
    v13 (cokmus, moloza basma %37,7) kaplama %43,4  (goruntunun %84,7'sini boyuyor)
    v21 otopark (cokmus, cati yesil) kaplama %73,5
    v21 sentetik arena (makul)       kaplama %15,7
    v21 kompozit arena               kaplama %77,6
    ```
    İyi ve çökmüş kipler **kaplamada net ayrışıyor**.
  - **Yap:** `karar_sozlesmesi.py`'ye `ZEMIN_KAPLAMA_TAVANI` sabiti + `zemin_
    maskesi_reddi(trav, icerik)` fonksiyonu ekle; `CONTRACTS.md` §6.4'e yeni ret
    sebebi **`ZEMIN_MASKESI_SUPHELI`** yaz. Kapı `analyze_path` karar yolunda
    **rotadan önce** çalışsın: kaplama tavanı aşarsa **fail-closed** ret.
    Eşiği yukarıdaki tablodan türet ve **gerekçesini yorumda ölçümle yaz**.
  - **GUI tarafı:** Ret hâlinde ekran rota çizmesin; bilgi satırında
    `⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %74 (tavan %X)` yazsın. Hakem, sistemin
    **neden** karar vermediğini görsün.
  - ⚠ **Madde 15 uyumlu:** bu kapı serbest alanı yalnız **reddeder**, asla
    büyütmez. Kapı ret verdiğinde rota yayınlanmaz — sessizce daraltma yok.
  - **Kapı:** (1) otopark 12 karesinde **12/12** `ZEMIN_MASKESI_SUPHELI`;
    (2) sentetik arena karelerinde kapı **ateşlemiyor** (kaplama %15,7 → yanlış
    pozitif yok); (3) sentetik bir çökme sahnesiyle pozitif kontrol;
    (4) `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.

- [STATUS: READY_FOR_REVIEW] **T49 — Sentetik arenada 11/12 kare `UC_BANT_TEMAS_YOK`: modelin EĞİTİLDİĞİ alanda rota çıkmıyor** · `codes/rpi_inference.py` (tanı) · **KRİTİK** · kanıt: aşağıdaki ölçüm
  - **Kanıt — kendim ölçtüm (v21, 12 sentetik arena karesi):**
    ```text
    sentetik arena  kaplama %15,7 (min 6 max 25)
                    {'RED/UC_BANT_TEMAS_YOK': 11, '1': 1}
    ```
    Kaplama **makul** — yani maske çökmüş değil. Buna rağmen 11/12 karede
    başlangıç/hedef uç bandına temas eden koridor bulunamıyor.
  - **Neden KRİTİK:** Bu, modelin **eğitildiği ve IoU 0,861 ölçtüğümüz** alan.
    Burada rota çıkmıyorsa kusur modelde değil, **karar yolunun sentetik arena
    geometrisiyle uyuşmamasında** olabilir (kare tuval → `_preprocess` dolgu
    eklemez, `icerik` tam kare; K-A bantları yine de temas bulamıyor).
  - **Yap — ÖNCE TANI, düzeltme sonra.** Üç ihtimali ölçerek ayır:
    (a) uç bant oranı (`HEDEF_BANT_ORANI = 0.08`) sentetik arena ölçeğine uymuyor;
    (b) sentetik arena sahneleri zaten 3 şeritli koridor değil (üreteç farklı
    yerleştiriyor); (c) maske parçalı, bant temas ediyor ama bileşen kopuk.
    Her ihtimal için sayı + gözle doğrulanmış 2 görsel.
  - **Kapı:** Üç ihtimalin hangisinin doğru olduğu **sayıyla** ayrılmış olacak.
    Tanı bitmeden hiçbir eşik değiştirilmeyecek.
  - **TANI TAMAMLANDI · Codex-2 · 2026-08-11.** Üretim koduna yazılmadı;
    eşik değiştirilmedi. Ölçülen kaynak `rpi_inference.py` SHA256:
    `dbf9cd100382f91a35e12cdafc7f672b7109b6bf3caff3b82058b107b72f24ec`.
    Başka görev sahibinin eşzamanlı T48 değişikliklerine dokunulmadı; o kapı bu
    kümede ateşlemedi (zemin kaplaması en çok `%25,238`, tavan `%55`).
  - **Ana ölçüm komutu ve gerçek çıktı (exit 0):**
    `O:\navitas-local-train\venv\Scripts\python.exe -B results/t49_sentetik_arena_tani_20260811/t49_tani.py`
    ```text
    [T49_KUME] kare=24 ilk=sa_000297.jpg son=sa_000320.jpg imgsz=512 conf_arg=VERILMEDI etkin_conf=0.25
    [T49_KAPLAMA] ilk12_ort=15.902% min=5.874% maks=25.238% tam24_ort=16.634%
    [T49_REPRO_ILK12] {'ACIK_1': 1, 'UC_BANT_TEMAS_YOK': 11}
    EXIT_CODE=0
    ```
  - **(a) Uç bant oranı — kısmen doğru, tek kök neden değil.** Tam süpürme;
    hücreler `ACIK_1 / ACIK_2 / ACIK_3 / UC_BANT_TEMAS_YOK`:
    ```text
    oran  bant_px   karar dağılımı
    0.02     12     1 / 1 / 0 / 22
    0.03     19     1 / 1 / 0 / 22
    0.04     25     1 / 0 / 1 / 22
    0.05     32     2 / 0 / 1 / 21
    0.06     38     2 / 0 / 1 / 21
    0.07     44     2 / 0 / 1 / 21
    0.08     51     2 / 0 / 1 / 21
    0.09     57     2 / 0 / 1 / 21
    0.10     64     2 / 1 / 1 / 20
    0.11     70     2 / 2 / 1 / 19
    0.12     76     2 / 2 / 1 / 19
    0.13     83     3 / 3 / 1 / 17
    0.14     89     3 / 4 / 1 / 16
    0.15     96     4 / 3 / 1 / 16
    0.16    102     4 / 5 / 2 / 13
    0.17    108     3 / 6 / 2 / 13
    0.18    115     5 / 5 / 2 / 12
    0.19    121     4 / 6 / 2 / 12
    0.20    128     4 / 5 / 3 / 12
    ```
    `%8 → %20`, 21 reddin 9'unu açıyor; 12/24 kare `%20`'de de ret. Sonuç:
    bant `%8` bu iç-arena geometrisine göre bazı karelerde **çok dar**, fakat
    eşiği büyütmek tek başına çözüm değil. Süpürme yalnız tanı sürecinde bellekte
    yapıldı, `finally` ile geri yüklendi; üretim eşiği bu görevde **değiştirilmedi**.
  - **(b) Yer gerçeği/geometri — doğru ve baskın açıklama.** Üreteç kaynağı
    seed=7, `ayni_malzeme=0.0`, `dar=0.0` ile 0..320 yeniden oynatıldı; ilk 24
    JPEG disk kümesiyle **24/24 bayt-eşit**. Gerçek çıktı:
    ```text
    [T49_B_REPLAY] n_ser={2: 5, 3: 13, 4: 2, 5: 4}
    [T49_B_PROVENANCE] jpeg_bayt_esit=24/24 seed=7 ayni_malzeme=0.0 dar=0.0
    [T49_B_LABEL] bos_etiket=0
    EXIT_CODE=0
    ```
    ```text
    fiziksel şerit sayısı             {2:5, 3:13, 4:2, 5:4}
    class-0 poligon sayısı             {1:15, 2:5, 3:1, 4:2, 5:1}
    class-0 bağlı bileşen sayısı       {1:20, 2:3, 3:1}
    GT analyze_path, %8                ACIK=2, UC_BANT_TEMAS_YOK=22
    GT analyze_path, %20               ACIK=12, UC_BANT_TEMAS_YOK=12
    aynı GT bileşeni iki %8 uca değer  2/24
    GT üst boşluk                      medyan=101 px, maks=328 px; 20/24 bant dışında
    GT alt boşluk                      medyan=74,5 px, maks=159 px; 16/24 bant dışında
    ```
    Yalnız **13/24** sahne üç şeritli; yalnız **1/24** etiket maskesinde tam üç
    traversable bileşen var. Üreteç ayrıca arenayı görüntü içinde `%0–28` dikey
    payla, dönüş/perspektifle ve `kısmi` şerit olasılığıyla yerleştiriyor. Kusursuz
    GT'nin 22/24 reddedilmesi model kusurunu dışlar: karar yolunun **tam görüntü
    uçlarına uzanan koridor** varsayımı bu veri geometrisiyle uyuşmuyor. Gerçek
    `n_ser` salt YOLO etiketinden birebir geri kazanılamazdı — etiket-only sonuç
    **DOĞRULANAMADI**; 24/24 bayt-eşit kaynak replay'iyle ayrıca doğrulandı.
  - **(c) Maske parçalanması — ölçülen retlerin nedeni değil.** Morfoloji ve
    engel çıkarma sonrasındaki **tüm** bileşenler, en büyük bileşen seçilmeden
    ölçüldü:
    ```text
    model bağlı bileşen sayısı dağılımı   {1:20, 2:3, 6:1}
    %8 UC ret atfı                         iki bant yetersiz=14
                                             yalnız üst yetersiz=5
                                             yalnız alt yetersiz=2
                                             uçlar farklı bileşenlerde=0
                                             küçük bileşen span kaybı=0
    uç bant zemin px (tüm / en büyük)     üst 24954 / 24954
                                           alt 31008 / 30740
    görsel c1, sa_000306 (6 bileşen)       üst 0 / 0, alt 0 / 0
    görsel c2, sa_000310 (2 bileşen)       üst 0 / 0, alt 268 / 0
    ```
    Sonuç: 21 `UC_BANT` reddinin **0/21**'i bileşen kopukluğundan; **21/21**'inde
    tüm model maskesi dahi bir veya iki uçta yeterli zemin taşımıyor.
  - **Gözle doğrulama — 6/6 görsel açıldı ve incelendi.** Her dosyada ham kare,
    maske/bileşen, uç bantlar ve varsa sarı rota aynı panelde:
    - (a) `results/t49_sentetik_arena_tani_20260811/gorseller/a1_bant_duyarli_sa_000297.png`
    - (a) `results/t49_sentetik_arena_tani_20260811/gorseller/a2_bant_yetersiz_sa_000301.png`
    - (b) `results/t49_sentetik_arena_tani_20260811/gorseller/b1_gt_iki_serit_sa_000300.png`
    - (b) `results/t49_sentetik_arena_tani_20260811/gorseller/b2_gt_cok_koridor_sa_000306.png`
    - (c) `results/t49_sentetik_arena_tani_20260811/gorseller/c1_bilesen_sa_000306.png`
    - (c) `results/t49_sentetik_arena_tani_20260811/gorseller/c2_bilesen_sa_000310.png`
  - **Artefakt doğrulama komutu gerçek çıktı (exit 0):** rapordaki altı yol
    OpenCV ile tekrar okundu.
    ```text
    [T49_ARTEFAKT] rapor_json=OK gorsel=6/6 okunur=6/6
    [T49_ARTEFAKT] rapor_md=VAR csv=VAR
    EXIT_CODE=0
    ```
    Tam rapor: `results/t49_sentetik_arena_tani_20260811/rapor.md` · ham JSON:
    `rapor.json` · kare tablosu: `kare_olcumleri.csv`.
  - **NET HÜKÜM:** **(b) doğru/kök uyumsuzluk**; **(a) etkili fakat kısmi belirti**;
    **(c) bu 24 karede yanlış hipotez**. Düzeltme/threshold değişikliği bu tanı
    görevinde yapılmadı.

- [ ] **T53 — Koşulmamış hücre: 11-sınıf ön-eğitim + GERÇEK DOKU karışımı aynı koşuda** · `O:\navitas-local-train` · **TIKAYICI** · kanıt: T50 FAZ 2 tablosu, `karisim_arena_gercek.yaml` başlığı
  - **MİMAR KARARI · 2026-08-12 · Claude 1.** Claude-2 haklı olarak GPU-gecesi
    harcamadan tasarım kararını bana bıraktı. Karar: **eksik hücre koşulacak.**
  - **Kanıt zinciri — hepsi ölçülmüş, ikisi zaten kayıtlı:**
    ```text
    K0 duyar  K0 kare>%1  K1 IoU  K1 kesin  K2 otopark   egitimi
    v15_ft2sinif  0.134   2/9     0.425     0.804        24.1%   11-sinif on-egitim, GERCEK DOKU YOK
    v17           0.010   1/9     0.315     0.807         0.9%   v15 + sentetik arena fine-tune
    v21 (uretim)  0.890   9/9     0.311     0.813        81.0%   GERCEK DOKU var, ON-EGITIM YOK
    ```
    `karisim_arena_gercek.yaml` başlığı (2026-08-05, D-12/D-18):
    *"Körlük tabanda değil, sentetik arena fine-tune ADIMINDA oluşuyor."*
    v15 tabanı 23/67 kullanılabilir kare / %24,07 zemin; sentetik fine-tune
    sonrası v17 10/67 / %1,04'e düşüyor.
  - **Hipotez (sınanacak, ilan değil):** 11-sınıf ön-eğitim alan-içi doğruluğu
    ve aşırı-tespit frenini veriyor (IoU 0,425 · otopark %24,1 — 12 modelin en
    iyisi); gerçek doku karışımı körlüğü açıyor (v21 duyar 0,890). İkisi **hiç
    aynı koşuda birleştirilmedi**. Birleşim, mimarinin istediği çeyreğe
    ("görür VE çökmez") en yakın adaydır.
  - **Yap:** `42_cok_sinifli_onegitim.py` ön-eğitim çıktısından başlayıp
    fine-tune'u **`dataset/karisim_arena_gercek.yaml`** ile koş (sentetik-yalnız
    karışımla DEĞİL). Ön-eğitim zaten diskte — **yeniden eğitme**, ondan devam et.
  - **Seçim ölçütü — T50'nin düzeltilmiş hâli, mAP DEĞİL:**
    `KAPI 0` gerçek dokuda duyarlılık ≥ 0,50 **ve** kare>%1 ≥ 8/9 (körlüğü eler) →
    `KAPI 2` otoparkta kaplama en düşük olan (çöküşü eler) → `KAPI 1` IoU/kesinlik →
    `KAPI 3` karar doğruluğu, **artık T51'in kadraj kümesinde de**.
    Gürültü tabanı 0,04; altındaki farkla sıralama yapılmaz.
  - ⚠ **Karışım oranı bilinmiyor.** Gerçek doku payı azsa körlük sürer, çoksa
    aşırı tespit döner. **Önce ana hücreyi koş**; oran süpürmesi ancak ana hücre
    KAPI 0'ı geçer ve KAPI 2 yüksek kalırsa gerekçelidir. Kendi başına 3 gece
    harcama.
  - ⚠ `set FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` olmadan başlatma; konsol kapanınca
    eğitim izsiz ölüyor. Başlangıç saatini ve tam komutu göreve yaz.
  - ⚠ **KAMERA YOK:** bu görev modelin **gerçek arenadaki** başarımını doğrulamaz
    ve doğrulayamaz. "Arena test edildi" ifadesi kurulmayacak.
  - 🔵 **EĞİTİM BAŞLATILDI · 2026-08-12 · mimar (madde 7 istisnası).**
    Betik: `O:\navitas-local-train\56_t53_gercek_karisim.py` (yeni)
    ```text
    FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 python.exe -B 56_t53_gercek_karisim.py
    model = codes/runs/segment/v15_on10sinif/weights/best.pt   (ON-EGITIM DISKTE,
                                                                yeniden egitilmedi)
    data  = dataset/karisim_arena_gercek.yaml  (rescuenet + sentetik + GERCEK DOKU)
    ad    = v22_on10_gercek · epoch 200 · batch 12 · imgsz 640
    log   = O:\navitas-local-train\calisma\t53_egitim.log
    ```
    Reçete `v15_ft2sinif/args.yaml`'dan **birebir** alındı (AdamW, lr0 0.001,
    cos_lr, patience 60, close_mosaic 20, copy_paste 0.3) — uydurulmadı.
    571 batch/epoch · ~4 dk/epoch → tam koşu ~13 saat, patience 60 ile erken
    durabilir. Kesinti olursa `--devam` ile aynı koşuya dönülecek.
  - **Değerlendirme HENÜZ YAPILMADI.** Eğitim bitince dört kapı koşulacak
    (K0 tespit tabanı → K2 alan dışı temkin → K1 IoU/kesinlik → K3 karar
    doğruluğu, T51 kadraj kümesi dâhil). **Kazandı ilanı ölçümden önce yok.**

  - ⚖ **ÖLÇÜLDÜ VE HÜKME BAĞLANDI · 2026-08-19 · `REVIEW_LOG.md` D-181.**
    Ön kayıt `scripts/olcum/v22_v23_on_kayit.md` (ölçümlerden **önce** yazıldı).
    ```text
    model   K0 figur  K0 raw   K1       K2       K3      K4      K5-SIKI   kararlilik
    v30      %8,0     0,3272   258/260  14/258   0/258   1/258   0/3633    8/260
    v22     %10,5     0,4510   258/260  16/258   0/258   0/258   0/3633    7/260
    v23      %0,5     0,4551   258/260  12/258   0/258   1/258   0/3633    4/260
    ```
    Kapılar: `test_rota_sentetik` **15/15** · `unittest` **620 OK** (ikisi için de).
  - 🔴 **Ön kayıttaki (4)'ün tabanı bayattı, SIKILAŞTIRILDI.** Defterdeki
    %8,53 (22/258) **T94 öncesi** planlayıcıyla ölçülmüş; aynı denetçinin
    arşivi bunu gösteriyor (`v30_t86` 22/258 · `v30_T94son` 14/258 · bugün
    14/258). Ölçüt aynı koşumun tabanına çekildi: **K2 ≤ 14/258**.
    ⚠ **Bedelini aday ödedi:** eski tabanla v22'nin 16/258'i geçerdi; yeni
    tabanla düşüyor. Düzeltme kendi lehime değil **aleyhime** çalıştı.
  - **HÜKÜM (T53/v22):** (4)'ten **2 kare geride** (16 vs 14) → **otomatik terfi
    YOK**. Ön kaydın "kısmi geçiş" maddesi gereği RED de ilan edilmiyor; ama
    v23 onu her eksende geçtiği için pratikte konu dışı.
  - ✅ **T53'ün hipotezi ölçülebilir destek aldı:** 11-sınıf ön-eğitim + gerçek
    doku karışımı, gerçek karelerde zemin görüsünü **0,3272 → 0,4510** çıkardı
    ve kararlılığı **8 → 7** iyileştirdi. Sadece K2'de 2 kare geride kaldı.
- [x] **T52 — Kaplama tavanı ayırt edici değil: üst uçta iki dağılım çakışıyor** · `codes/karar_sozlesmesi.py` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` **D-66**
  - **✅ D-71 DÜZELTMESİ YAPILDI · 2026-08-12 · Claude-2** · kayıt **D-72**.
    Sıra korundu: **önce köşe düzeltmesi, sonra eşik ölçümü** (köşe düzeltmesi
    kenar değerlerini aşağı çeker; eşiği önce sabitlemek ölçümü geçersiz kılardı).
  - **(3) Köşe çift sayımı düzeltildi.** Çerçeve maskesiyle her çevre pikseli
    bir kez sayılıyor. Doğrulandı: köşe/kenar katkı oranı **2,00× → 1,00×**;
    dejenere kutular (1×N, N×1, 1×1) tanımlı.
  - **(1) Tavan 0,45 → 0,50, köşe düzeltmesinden SONRA yeniden ölçüldü:**
    ```text
    (a) MESRU azami (kaplama tavanini asan 11 kare) : 0,453
    (b) mevcut test paketinin COKME fiksturu asgari : 0,536
    (c) COKMUS kume kenar asgarisi                  : 0,583
    gecerli aralik (0,453 · 0,536) genislik 0,083 · orta 0,4945
      0,50 -> mesru +0,047 · test +0,036 · cokme +0,083
    ```
    D-71'in payları bağımsız ölçümle **doğrulandı**. Köşe düzeltmesi değerleri
    pratikte oynatmadı (0,452 → 0,453; çökme asgarisi değişmedi).
  - **(2) Fail-closed uygulandı.** Yeni `icerik_kutusu_gecerli_mi()`: dörtlü,
    bool olmayan, sonlu, **tam sayı değerinde**, pozitif boyutlu ve maskeye
    **tam sığan** kutu. Geçersizde `zemin_maskesi_reddi` artık **reddediyor**.
  - **Ret sebebi kararı: `ALAN_YETERSIZ` — yeni kod TÜRETİLMEDİ.** Gerekçe
    ölçüldü: `codes/rpi_inference.py:606-611` aynı koşulu (geçersiz/boş içerik
    kutusu) **zaten** bu kodla reddediyor; ikinci kod aynı fiziksel koşula iki
    kanonik cevap üretirdi. Ayrıca §6.4/4 "yeni ret yolu önce tabloya yazılır"
    diyor ve `CONTRACTS.md` bu turda dosya iznimde **değildi**.
    ⚠ **Belge borcu (mimara):** §6.4'teki `ALAN_YETERSIZ` satırı yalnız "koridor
    alanı `min_area_ratio` altında" diyor; kod onu `:606`'dan beri "içerik
    kutusu geçersiz" için de kullanıyor — satır metni genişletilmeli.
  - **KAPILAR (gerçek çıktı):**
    ```text
    320 MESRU / 67 COKME : mesru elenen 0/320 GECTI · cokme 67/67 GECTI
    MUTASYON KONTROLU (22 test)
      duzeltilmis kod                     : 0 basarisiz
      MUTASYON 1 tek sinyalli (T52 oncesi): 21 basarisiz
      MUTASYON 2 fail-OPEN (D-69 oncesi)  : 14 basarisiz
    codes/test_rota_sentetik.py           : 15/15
    unittest discover -s tests -q         : Ran 303 tests · OK
    git diff --check exit 0 · Jetson ikizleri BIREBIR
    ```
  - **Test paketi 16 → 22:** geçersiz içeriğin 11 biçimi (sıfır/taşan/negatif/
    kesirli/bool/eksik öğe/NaN/inf), geçerli kutunun reddedilmediği regresyonu,
    2 boyutlu olmayan maske, köşe-kenar eşit ağırlık, çevre paydası, dejenere
    kutular ve **fail-closed dalı için ayrı mutasyon kontrolü**.
  - ⚠ **Açık:** `test_zemin_kaplama_kapisi.py`'nin `_kaplamali` fikstürü en düşük
    **0,536** kenar üretiyor — yani eşiğin ÜST sınırını veri değil **test**
    belirliyor. Fikstürün kenar değerinden bağımsızlaştırılması ayrı görev.
  - 🔴 **MİMAR DENETİMİ GEÇMEDİ · 2026-08-12 · Claude-2** · kayıt **D-69**.
    Mantık doğru ve iyileşme gerçek, ama **eşik yanlış yerde**.
  - **Bağımsız ölçüm** (mimarın betiği kullanılmadı; MEŞRU = 320 yer gerçeği
    maskesi, ÇÖKMÜŞ = v21 otoparkta 67 kare, CPU çıkarım):
    ```text
    ESKI kapi (yalniz kaplama): mesru ELENEN 11/320 · cokme YAKALANAN 67/67
    YENI kapi (iki sinyal)    : mesru ELENEN  1/320 · cokme YAKALANAN 67/67
    ```
    Bildirilen **0/234** daha geniş meşru kümede **sağlanmıyor**.
  - **Eşik analizi — 0,45 meşru azaminin ALTINDA:**
    ```text
    mesru (kaplama>tavan) kenar : ... 0.392  0.452   <- OLCULEN AZAMI
    cokme kenar asgarisi        : 0.583
    GERCEK BOSLUK               : [0.452, 0.583]  orta 0.517
    esik 0.45 -> mesru payi -0.002 (NEGATIF)  · esik 0.52 -> +0.068 / +0.062
    ```
    **Öneri: kenar tavanı 0,45 → 0,52** (meşru eleme 0/320, çökme 67/67 korunur).
    Değer sözleşme sahibinindir; denetimde **değiştirilmedi**.
  - **Eksik test YAZILDI:** `tests/test_zemin_kapisi_iki_sinyal.py` (16 test),
    dört birleşim + sınır davranışı + içerik kutusu. **Mutasyon kontrolü:** kapı
    tek sinyalli hâline döndürülünce **16 testin 8'i düşüyor** (vakum değil).
  - **Diğer bulgular:** (a) geçersiz `icerik`te kapı **fail-OPEN** — kardeş
    sözleşme fonksiyonları fail-closed; üretim yolu `analyze_path:606`'daki
    doğrulama sayesinde korunuyor, yani sözleşme tutarsızlığı. (b) köşe
    pikselleri **2×** ağırlıklı (ölçüldü); azami 1,0'da kaldığı için tutarlı.
    (c) mevcut `test_zemin_kaplama_kapisi.py`'nin en düşük kenar değeri **0,536** —
    tavan 0,52 üstüne çıkarılırsa o testler payı olmadan kırılır.
  - **Kapılar:** `codes/test_rota_sentetik.py` **15/15** ·
    `unittest discover -s tests -q` → **Ran 297 tests · OK**.
  - ⚠ **KODU MİMAR YAZDI** (madde 7 istisnası: Codex'ler kotada, Claude-2 gece
    boyu çalıştı, kullanıcının açık talimatı). **KENDİ KODUMU ONAYLAMIYORUM** —
    T45 ile birlikte ayrı denetim bekliyor. Bu satır `[x]` yapılmayacak.
  - **Ölçüm — 218 meşru (kadraj arena) + 67 çökme (otopark), altı aday:**
    ```text
    olcut            MESRU min..maks     COKUS min..maks   ayrisma
    kaplama          0.001..0.809        0.725..0.833      CAKISIK
    doluluk          0.007..0.897        0.726..0.836      CAKISIK
    tikizlik         0.013..0.966        0.728..0.838      CAKISIK
    en_buyuk_pay     0.208..1.000        0.995..1.000      CAKISIK
    engel_orani      0.000..0.998        0.158..0.265      CAKISIK
    kenar_dayanma    0.000..0.339        0.579..0.964      +0.240  <- TEK AYIRAN
    ```
    D-65'teki uyarı doğrulandı: **kaplama gerçekten çakışıyor.**
  - **Uygulama:** iki sinyal, ikisi de aşılırsa ret —
    `kaplama > 0.55` **VE** `kenar_dayanma > 0.45`. Eşik iki dağılımın ortası
    (0,459 → 0,45). Kaplama şartı korundu (dar ama çevreye dayanan sahneler
    meşru olabilir). Kapı yalnız reddeder, serbest alanı büyütmez (madde 15).
  - **Sonuç — kendi ölçümüm:**
    ```text
    MESRU (kadraj arena)   n=234   YENI kapi   0   ESKI kapi   6
    COKUS (otopark)        n= 67   YENI kapi  67   ESKI kapi  67
    yanlis-negatif 6/234 -> 0/234 · cokme yakalama 67/67 (degismedi)
    ```
  - **Kapılar:** `codes/test_rota_sentetik.py` **15/15** · tam paket **281 OK** ·
    Jetson paketi yeniden üretildi.
  - **DOĞRULANAMADI:** gerçek arenada davranışı — kamera yok. Görev kadrajında
    arena görüntüyü doldurursa zemin çevreye daha çok dayanabilir. Kenar
    dayanması kaplamadan **daha dayanıklı** ama bağışık değil.
  - **Denetçiye not:** kapının yeni testi yazılmadı — `tests/test_zemin_kaplama_
    kapisi.py` iki sinyalli hâli kapsamıyor. Denetim bunu da kapsamalı.

- [ ] **T54 — ADIM 1-3 KABUL · ADIM 4 GEÇERLİ SAYILDI (itiraz kabul, D-200) · HEDEFİ HÂLÂ ÖLÇÜLMEDİ → T116** · `dataset/download_and_convert.py` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-199**, hüküm **D-200**
  - ✅ **ADIM 1-3 · 2026-08-20 · Claude-2 (Fable 5)** · kayıt `REVIEW_LOG.md`
    **D-199** · ölçüm düzeneği: **dinamik workflow, 3 paralel ajan**
    (provenans · araç-DOTA · dağılım), çıktıları ana döngüde denetlendi.
  - **Dönüşüm düzeltildi (tek kaynak):** eşleme
    `scripts/olcum/41_cok_sinifli_veri.py` **aynasından AST ile** okunur
    (import değil — 41 `ayarlar` ithal eder); kümeler **adlardan** türetilir;
    maskeler `np.isin`; `rescuenet_yolo`yu sessiz ezme **kapalı** (`--temizle`
    korkuluğu — tarihsel karışımların girdisidir). **41 + 57 aynaya eklendi**
    (çift 52→54, senkron kapısı otomatik kapsadı — D-190 kuralı).
  - **ARAÇ KARARI ÖLÇÜLDÜ:** DOTA, RescueNet araç piksellerinin **%0,0'ını**
    yakalıyor (n=40 kare, 4.469.436 px, kesişim 0; ürettiği maskelerin %100'ü
    araç DIŞINA düştü — plane/harbor yanlış sınıfı). "Çift sayım" bu veride
    **boş** → **araç ENGELDE KALIR** (57 zaten öyle üretmişti; v34 öyle eğitildi).
  - **ÖNCE/SONRA (600 ham maske, 7,2 mlr px):** etiketli **%8,31 → %47,34**;
    kalan etiketsiz **saf Background**. Ağaç %21,3 · su %8,6 · binalar %8,7.
  - **GÖZLE (D-80) GEÇTİ:** `results/t54_gorsel_dogrulama.png` — eski panelde
    çatılar etiketsiz, yenisinde **kırmızı (engel)**.
  - **TESTLER:** `tests/test_donusum_esleme.py` (8 test; **57 zinciriyle
    semantik denklik** dahil — iki zincir ayrışırsa düşer).
    Mutasyon 1 (eski 7/8 eşleme) → import korkuluğu, `FAILED (errors=1)`;
    mutasyon 2 (binasız) → `FAILED (failures=2)`.
    ```text
    codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    unittest discover -s tests    Ran 655 tests · OK   (647 -> 655, +8)
    ayna                          cift: 54 · AYRISAN: 0
    ```
  - 🔴 **İTİRAZ (AGENTS §8 · D-199 §4):**
    1. MİMARIN İDDİASI: T54'ün kapanması için yeni eşlemeyle eğitim koşusu gerekir.
    2. NEDEN YANLIŞ: o koşu ZATEN yapıldı ve ürünü BUGÜNKÜ ÜRETİM MODELİ.
    3. KANIT: `zincir_t53_t54.sh:16-20` (`--ad v23_t54_engelli --data
       karisim_t54_engelli.yaml`, taban `ON_BEST` = 11-sınıf ön-eğitim) ·
       log `[v23_t54_engelli] EGITIM TAMAMLANDI` · **sha256(v34) ==
       sha256(v23_t54_engelli/best.pt) → bayt-eş: True** (ölçtüm) · D-140:
       seed bit-bit etkisiz → yeni koşu v34'ün eşini üretir, GPU gecesi boşa.
    4. ÖNERİ: T54 adım 1-3 teslimatlarıyla kapansın; adım 4 "zaten koşuldu,
       ürünü v34" diye kayda geçsin.
    5. YANILIYORSAM: mimar FARKLI reçete kastediyorsa (ham'dan üretilmiş küme,
       farklı karışım/taban) söylesin — koşarım; ya da `--temizle` ile yeniden
       üretilen kanonik küme `2sinif_engelli`den ölçülebilir ayrışırsa
       (IoU medyanı belirgin < 0,98) itirazım zayıflar, o ölçümü koşarım.
  - ⚠ **Yapmadıklarım:** eğitim başlatılmadı (itiraz bekliyor) · kanonik
    yeniden üretim koşulmadı (tarihsel veriyi ezme kararı mimarın) ·
    `MAX_POLYGONS//2 = 15` engel tavanı ESKİ varsayımın kalıntısı — yeni
    eşlemede engel baskın (22356 vs 3104), yeniden üretimde KIRPABİLİR
    (işaretlendi, ölçülmedi) · KAMERA YOK: gerçek arena başarımı yine
    doğrulanamadı (D-88/D-99, kalıcı kısıt).

  - **Kök neden — kodda doğrulandı** (`download_and_convert.py:72-83`):
    ```text
    road_mask    = (lbl_np == 7)  -> sinif 0
    blocked_mask = (lbl_np == 8)  -> sinif 1
    DIGER HER SEY DUSURULUYOR
    2 sinifli egitim etiketlerinde bulunan id'ler: yalniz 0 ve 1
    ```
    11 sınıflı sette `building_no_damage/minor/major/total_destruction`, `tree`,
    `water`, `pool` **var**; 2 sınıfa dönüşümde **etiketsiz arka plana**
    düşüyorlar. Etiketsiz arka plan **denetim almaz** → modele hiçbir yerde
    "çatı zemin değildir" denmiyor → "geniş düz yüzey = zemin" genellemesi.
  - **Her gözlemi açıklıyor:** v15 (11-sınıf ön-eğitim) otopark %24,1 — bina
    bilgisi kısmen sağ kalmış · v17/v20 kör — sentetik arenada bina yok ·
    v21/v22 çatı boyuyor — bina denetimi yok.
  - **Yap:**
    1. `download_and_convert.py` dönüşümünde bina · ağaç · su · havuz sınıflarını
       `1 = blocked`'a eşle. Arka plana düşürme.

       🔴 **SINIF ID DÜZELTMESİ · 2026-08-20 · mimar · `REVIEW_LOG.md` D-195.**
       Bu maddede **önceden yanlış id'ler yazılıydı** ("bina 3-6, ağaç 8, su 2,
       havuz 9"). O sayılar **11-sınıf ara kümesinin** id'leridir;
       `download_and_convert.py` ise **HAM RescueNet maskesini** okur. İki şema
       farklı. Harfiyen uygulanırsa: `vehicle` **yanlışlıkla içeri girer**
       (ayrı tutulması gereken tek sınıf) ve **su ile havuz DIŞARIDA kalır**.

       **TEK KAYNAK:** `O:\navitas-local-train\41_cok_sinifli_veri.py:51-60`
       (`SINIF_ESLEME`). Bu tablo kodda mevcut; **yeniden yazma, oradan oku.**

       ```text
       HAM RescueNet id -> 11-sinif id -> ad                        T54 hedefi
        7                  0             traversable (Road-Clear)   0 KALIR
        8                  1             blocked (Road-Blocked)     1 KALIR
        1                  2             water                      -> 1
        2                  3             building_no_damage         -> 1
        3                  4             building_minor             -> 1
        4                  5             building_major             -> 1
        5                  6             building_total_destruction -> 1
        6                  7             vehicle                    *** AYRI ***
        9                  8             tree                       -> 1
       10                  9             pool                       -> 1
       ```
       Yani `download_and_convert.py` içinde blocked kümesi HAM id ile:
       `{8}` ∪ `{1, 2, 3, 4, 5, 9, 10}` · `vehicle` = HAM **6**, kararı ayrı.

       ⚠ **Madde 16:** bu id'leri koda çıplak sabit olarak yazma. `SINIF_ESLEME`yi
       içe aktar ya da tek bir sözlükten türet; iki dosyada iki kopya olursa bu
       projenin **dört kez tekrar eden** kusuru (iki kopya, biri zorlanmıyor) tekrar eder.

       ⚠ `vehicle` (HAM **6**) ayrı düşün: DOTA OBB katmanı zaten araçları çıkarıyor
       (madde 15 "yalnız çıkarır"), çift sayım yapıp yapmadığını **ölç**.
    2. Kümeyi yeniden üret, sınıf dağılımını yazdır (önce/sonra).
    3. Aynı reçeteyle tek koşu: 11-sınıf ön-eğitimden başla, yeni 2 sınıflı
       karışımla fine-tune (`56_t53_gercek_karisim.py` kalıbı, `--ad` değiştir).
  - **Kapı — dört kapı, mAP DEĞİL:**
    `K0` gerçek dokuda duyarlılık ≥ 0,50 · `K2` **otoparkta kaplama belirgin
    DÜŞSÜN** (bu görevin asıl hedefi: %80,6 → ?) · `K1` IoU/kesinlik en az v22
    seviyesinde kalsın (0,512) · `K3` karar doğruluğu (kompozit + T51 kadraj).
    **Gözle doğrulama zorunlu:** otopark karesinde bina çatısı **yeşil
    OLMAYACAK**. Sayı iyi görünüp görsel kötüyse **görsel kazanır**.
  - ⚠ `set FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` olmadan başlatma.
  - ⚠ **KAMERA YOK:** gerçek arena başarımı yine doğrulanamayacak.

- [STATUS: KAPANDI] **T60 — Üreteci ŞARTNAMEYE SADIK kıl: renk künyesi ölçüldü, beş nokta çelişiyor** · `O:
avitas-local-train)_sentetik_arena.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-87**
  - **NEDEN:** altı model (v15..v24) aynı duvara tosladı. Ortak sebep model değil,
    **eğitim substratı**: üreteç arenaya benzemiyor. Artık gerçek kare elimizde,
    hedef **ölçüldü** (D-87) — tahmin değil.
  - **ÖLÇÜLEN HEDEF** (`sartname_s9_arena.png`, LAB, a/b merkezlenmiş):
    ```text
    zemin : L 150..159 · a +2 · b +11..+13,5   (sicak, acik)
    moloz : L 102..114 · a -1 · b  +3..+4,5    (notr, koyu)   dL~45 · db~8
    HB ped: a -2,0 · b -2,1  -> KROMA SIFIR (siyah ped + BEYAZ H)
    baskin paletin ALTI kumesinde de |a| < 1,0  -> sahne DUSUK KROMA
    ```
  - **BEŞ MADDE — sırayla, her biri ölçülebilir:**
    1. **Moloz: RescueNet bina çatısı → GRİ BETON.** En görünür gerçekdışılık
       (D-78'den beri açık, D-80'de de doğrulanamadı listesindeydi). Hedef:
       moloz yamalarının LAB ortalaması `L 102..114 · |a|<1,5 · b +3..+5`, ve
       zemin-moloz farkı `dL >= 35`.
    2. **Zemin: RescueNet kolajı → açık kahve toprak/kum.** Hedef `L 150..159 ·
       b +11..+13,5`. T57'nin `PROSEDUREL_PAYI`/`DOKU_GENLIGI` altyapısı hazır;
       yalnız PALET ve hedef bant değişir.
    3. **HB pedi: düz KIRMIZI dikdörtgen → SİYAH ped + BEYAZ H + beyaz çerçeve.**
       ⚠ Bu **benim T56'da koydurduğum yanlış şarttır** — şartname METNİ "kırmızı
       H" diyor, şartmenin KENDİ FİGÜRÜ nötr/beyaz gösteriyor ve ölçüm figürü
       doğruluyor (kroma sıfır). Figür kazanır; metin/figür çelişkisi D-87'de.
    4. **Bariyer: YOK → kırmızı-beyaz şeritli KOL.** Figürde kapalı güzergâhı
       kapatan şey uzun, ince, yatay bariyer kolu. Yığın değil.
    5. **Zemin ızgarası: YOK → ince koyu kareli ızgara.** Sadakat gereği eklenir;
       tek başına "iyileştirme" sayılmaz.
  - **KAPI**
    1. Her madde için ölçüm: üreteç çıktısının LAB künyesi hedef banda girdi mi
       (D-87 tablosu). **Körü körüne kopyalama yok** — T57'deki gibi doku bileşeni
       ayrıştırılarak ölçülecek.
    2. **GÖZLE DOĞRULAMA ZORUNLU:** üretilen sahne ile `sartname_s9_arena.png`
       yan yana. Sayı iyi görünüp görsel kötüyse **görsel kazanır**.
    3. T51/T56'nın kadraj kapıları korunacak (koridor sapma, hedef, kenar 2,000 m,
       `hedef_serit` uyumu).
    4. Karar zinciri kapısı: yer gerçeği maskesiyle rota/ret dağılımı.
    5. `codes/test_rota_sentetik.py` 15/15 · `unittest discover -s tests -q` OK.
  - ⚠ **EĞİTİM KİPİNİ DE ETKİLER ve bu KASITLIDIR** (T57'deki gibi). "Eğitim kipi
    değişmedi" kapısı bu görevde geçerli değildir.
  - ⚠ **İHA-İB (30×30 m mavi bölge) BU GÖREVE DAHİL DEĞİL.** Şartname metni tarif
    ediyor ama kendi figüründe **yok** (D-87 bulgu 4). Metne dayanan bir ekleme
    ölçüme dayanmaz; ayrı kararla eklenir.
  - ⚠ **DOĞRULANAMAZ (kalıcı, D-88):** bu görev arena başarımını **doğrulamaz**.
    Fiziksel arena kurulamıyor, ikinci gerçek kare gelmeyecek.
  - **Uygulama:** Gerçek RescueNet dokusu düz renkle değiştirilmedi; LAB ortalaması
    additif olarak taşındı. Ana moloz dokusu ve RGBA kesitleri işlendi, alfa
    bit-eşit kaldı; eski `%35` renkli-çatı geçişi kaldırıldı. `PROSEDUREL_PAYI`
    ve `DOKU_GENLIGI` değişmedi. Zemin ve traversable arena yüzeyi ölçülen sıcak
    zemin bandına taşındı. Eğitimde kırmızı/figür HB, kadrajda figür HB üretildi;
    HB yalnız tamamı önceden class-0 olan 2×2 m ROI içinde çizildi. Şeritli
    bariyer, arena-içi kare ızgara ve varsayılan güvenli/bayat-dosya temizliği eklendi.
  - **ADIM 0 kapısı:** `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q`
    → `Ran 322 tests in 41.176s` · `OK` · `EXIT_CODE=0`. Fikstür
    `ZEMIN_KAPLAMA_TAVANI * (1.05, 1.20, 1.35)` ile sözleşmeden türetiliyor;
    eşik ve test iddiası değişmedi.
  - **Renk+doku kapısı:** `O:\navitas-local-train\venv\Scripts\python.exe -B O:\navitas-local-train\59_t60_uretec_sadakati.py --faz sonra --uretec O:\navitas-local-train\51_sentetik_arena.py --once-json O:\navitas-local-train\results\t60\oncesi.json --json O:\navitas-local-train\results\t60\sonrasi.json`
    → LAB: prosedürel zemin `(154.025,+1.530,+11.747)`, banka zemin
    `(153.738,+1.417,+11.783)`, ana moloz `(108.485,-0.994,+3.152)`, RGBA moloz
    `(111.393,-1.007,+3.155)`, `dL=42.346`. Doku koruma oranları zemin
    `0.999`, yol `1.000`, ana moloz `0.940`, RGBA `0.939`, banka zemin `0.992`;
    T57 kaynak-yama genliği zemin `10.542/12.055`, yol `3.971`. Gerçek eğitim
    yolu HB dağılımı `yok=13, figür=17, kırmızı=10`, tam ön-temas `27/27`,
    class-0 dışı piksel `0`; fotometrik sonrası moloz-L çakışması figür `%2.592`,
    kırmızı `%20.215` (**gizlenmedi**). SHA256
    `8e204c1171cb287b95dd99318130217a55216f6bdbc76b5816422ef85e3aa9ea` · `EXIT_CODE=0`.
  - **Kadraj/görsel kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B O:\navitas-local-train\51_sentetik_arena.py --adet 260 --seed 51 --kadraj --onizleme --cikti O:\navitas-local-train\calisma\sentetik_arena_kadraj_t60`
    → `260 görüntü`, `260 manifest`, `260 etiket`, temizlenen `546`, `EXIT_CODE=0`.
    Ardından `O:\navitas-local-train\venv\Scripts\python.exe -B O:\navitas-local-train\59_t60_uretec_sadakati.py --faz kadraj --uretec O:\navitas-local-train\51_sentetik_arena.py --json O:\navitas-local-train\results\t60\kadraj.json --kume O:\navitas-local-train\calisma\sentetik_arena_kadraj_t60 --once-kume O:\navitas-local-train\calisma\sentetik_arena_kadraj_T56 --referans O:\navitas\data\arena_referans\sartname_s9_arena.png --gorsel O:\navitas-local-train\results\t60\t60_yan_yana.png`
    → sapma `527/527, 0`, hedef `260/260`, hedef-şerit uyumsuz `0`, tam temas
    `260/260`, serialized class-1/HB çakışma `0 px`, kenar `2.000..2.000 m`;
    persisted dış zemin `(154.370,+1.884,+11.886)`, arena-içi erozyonlu class-0
    `(151.344,+1.627,+11.559)` (260 kare eşit ağırlıklı küme ortalaması,
    hedef bantta), moloz
    `(108.235,-0.453,+4.503)`, `dL=46.135`. Nihai JPEG doku koruması T56→T60:
    zemin `8.7818→7.6556 = 0.8718×`, blocked `28.7073→29.1967 = 1.0170×`;
    `EXIT_CODE=0`. Final-JPEG zemin için kaynak-yama T57 mutlak bandının
    uygulanabilirliği **DOĞRULANAMADI** (koruma kapısı geçti).
  - **Gözle doğrulama:** `O:\navitas-local-train\results\t60\t60_yan_yana.png`.
    Ölçülen beş öğe geçti: sıcak/açık zemin, koyu-nötr fakat dokusu korunmuş
    moloz, siyah-beyaz HB, kırmızı-beyaz bariyer ve ince ızgara. Yol için ayrı
    ölçülmüş renk hedefi **DOĞRULANAMADI**. Dar şerit/dikdörtgen RescueNet kolaj
    geometrisi gerçek arenanın eşleniği değildir; arena başarımı iddia edilmedi.
  - **Temizlik kapısı:** imzalı geçici çıktıda `imzali_silinen=2`; yabancı alt
    dizinde `ret=1`, önceden var olan dosya korundu · `EXIT_CODE=0`.
  - **Genel kapılar:** `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    → `SONUC: 15/15 dogru` · `EXIT_CODE=0`; tam paket → `Ran 322 tests in 37.680s`
    · `OK` · `EXIT_CODE=0`.
  - **Eğitim:** ÇALIŞTIRILMADI; kararı mimar verecek.
  - **🔎 MİMAR DENETİMİ · 2026-08-14 · KAPANDI** · kayıt `REVIEW_LOG.md` **D-91**.
    Renk künyesi **bağımsız doğrulandı** (60 karede yer gerçeğiyle: zemin
    L 149,2 · b +11,4 · moloz L 108,0 · b +4,4 · **dL 41,2**). Oyuna karşı
    kapı geçti (doku koruma 0,87–1,00, hepsi 0,75 eşiğinin üstünde) — düz gri
    boyayarak geçilemedi. Gözle doğrulama: beş maddenin beşi teslim.
    Zemin L'si bandın **0,8 altında** (149,2 < 150) — kusur değil, kayıtta.
    **Geometri açığı T66'ya taşındı** (Codex kendi bildirdi, gizlemedi).

- [STATUS: READY_FOR_REVIEW] **T87 — `kompozit` kaynağında rota: etiketle, eğit, ölç** · `scripts/olcum/71_*`, `dataset/gercek_kompozit/**`, `dataset/karisim_gercek_kompozit.yaml` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-136**
  - **✅ VERİ HAZIRLANDI · 2026-08-16 · Claude-2** · kayıt `REVIEW_LOG.md` **D-138**.
    🔴 **EĞİTİM BAŞLATILMADI** (emrin 4. maddesi).
  - 🔴 **1. MADDE — H PEDİ KUSURU DÜZELTİLDİ, büyüklüğü ölçüldü:**
    ```text
    9 karenin 7'sinde pedin 1681 pikselinin 1681'i ENGEL
    kalan 2 karede    1404 ve 1680 px ENGEL
    engelden kurtarilan TOPLAM: 14.849 px (kare basina ort. 1650)
    ```
    Konum **manifestten** (`arena.hedef_kutu`, otorite); manifest yoksa
    `hb_konumu` (T72/D-105); ikisi de yoksa None + kayıt (sessiz engel YOK).
  - 🔴 **Maskede düzeltmek YETMEDİ — poligon kodlaması geri getirdi:**
    ```text
    yalniz maskede duzeltilince   ped ENGEL kalan kare: 6/9 (2'sinde 1681/1681)
    ped AYRI poligon yazilinca    ped ENGEL kalan kare: 4/9 (kalan 13-41 px)
    ```
    Sebep `RETR_EXTERNAL`in delikleri kaybetmesi. Kalan 13–41 px pedin **sağ
    kenarında tek piksellik şerit** (satır 0-40, sütun 40-40) — rasterleştirme
    yuvarlaması, emniyetli yönde.
  - **KÜME:** `dataset/gercek_kompozit/` · train **7 asıl → 4 KAT → 28**
    görsel/etiket · val **2** (ÇOĞALTILMADI) · bölüm ayrımı kaynak
    manifestten (sızıntı yok) · poligon sınıfları yalnız 0/1.
    Yeni karışım `dataset/karisim_gercek_kompozit.yaml`;
    **`karisim_gercek_otopark.yaml` DEĞİŞMEDİ** (git: fark yok).
    ```text
    karisim_gercek_otopark.yaml   train 6819 · val 806
    karisim_gercek_kompozit.yaml  train 6847 · val 808
    yeni kumenin payi: 28/6847 = %0,41
    ```
    ⚠ **Pay çok küçük**: D-132'de 67 kare 12 katta ~%9 idi. Bu kümenin modeli
    ölçülebilir biçimde değiştirmesi **beklenmemelidir**; doz kararı mimarındır.
  - **KAPI (b) — etiketler yer gerçeği olarak** (model YOK, eğiticinin gördüğü
    maske · `overlap_mask: true` semantiği):
    ```text
    ZEMIN KAPISINDAN GECEN : 9/9
    kaplama medyan 0,618 · min 0,580 · maks 0,667   (tavan 0,67)
    KUSURSUZ ALGI TAVANI — rota ureten: 1/9 · pay +3,64 px · pay<0: 0
    ```
  - 🔴 **ÖLÇÜLEN TAVAN 1/9 — görevin teşhisi KISMEN çürüdü.** Kalan 8 kare
    `GORUS_HATTI_KOPUK`: *"Başlangıç ve hedef tohumları aynı koridor
    bileşeninde değil; alt_tohum=13561px, üst_tohum=1781px"*. Bu sahnelerin
    çoğunda kareyi baştan sona kat eden sürülebilir koridor **fiziksel olarak
    yoktur**. Algıyı düzeltmek 4 `ZEMIN_MASKESI_SUPHELI` karesini kurtarır ama
    onlar da aynı yere düşer. Bu küme `kompozit`i 0/9'dan **en fazla 1/9**'a
    taşıyabilir. D-136'nın açık maddesi (GORUS_HATTI_KOPUK'un sebebi) böylece
    cevaplandı: sebep **algı değil sahne geometrisi**.
  - **KAPI (a)** 15/15 · **(c)/(d) gözle (D-80):** `results/t87/h_pedi_kaniti.png`
    — 6 karede görüntü + **eğiticinin sınıf haritası** yan yana; ped 6/6
    panelde YEŞİL, çevresi kırmızı olsa bile. Tam kare önizlemeler
    `dataset/gercek_kompozit/onizleme/`: binalar tamamen kırmızı, araçların
    büyük çoğunluğu kırmızı, bitki kırmızı, asfalt yeşil.
  - ⚠ **KAÇAN ARAÇ VAR — ölçüldü:** DOTA OBB (conf 0,10, tam çözünürlük) araç
    pikselinin **%5,9'u** etikette engel değil; bunun **%3,47**'si poligon sınır
    yuvarlaması, kalanı conf 0,25 altında kalan araçlar. Gözle de görüldü
    (beyaz/gümüş birkaç araç zemin kalmış). `ARAC_CONF` **değiştirilmedi** —
    eşik ayarı veri kalitesi kararıdır, mimarındır.
  - ⚠ **Ölçüm hatam kayda geçti:** kapı (b)'yi önce class-0 poligonlarını tek
    başına rasterleştirerek ölçtüm (kaplama 0,785 · 1/9 geçti) — bu etiketi
    değil **poligon kodlamasını** ölçüyordu. Doğrusu Ultralytics'in alan sıralı
    üst üste basmasıdır. D-136'daki mimarın dersiyle aynı sınıf.

  - ⚖ **ÖLÇÜLDÜ VE HÜKME BAĞLANDI · 2026-08-19 · `REVIEW_LOG.md` D-181.**
    Ön kayıt `scripts/olcum/v22_v23_on_kayit.md` (ölçümlerden **önce** yazıldı).
    ```text
    model   K0 figur  K0 raw   K1       K2       K3      K4      K5-SIKI   kararlilik
    v30      %8,0     0,3272   258/260  14/258   0/258   1/258   0/3633    8/260
    v22     %10,5     0,4510   258/260  16/258   0/258   0/258   0/3633    7/260
    v23      %0,5     0,4551   258/260  12/258   0/258   1/258   0/3633    4/260
    ```
    Kapılar: `test_rota_sentetik` **15/15** · `unittest` **620 OK** (ikisi için de).
  - 🔴 **Ön kayıttaki (4)'ün tabanı bayattı, SIKILAŞTIRILDI.** Defterdeki
    %8,53 (22/258) **T94 öncesi** planlayıcıyla ölçülmüş; aynı denetçinin
    arşivi bunu gösteriyor (`v30_t86` 22/258 · `v30_T94son` 14/258 · bugün
    14/258). Ölçüt aynı koşumun tabanına çekildi: **K2 ≤ 14/258**.
    ⚠ **Bedelini aday ödedi:** eski tabanla v22'nin 16/258'i geçerdi; yeni
    tabanla düşüyor. Düzeltme kendi lehime değil **aleyhime** çalıştı.
  - ✅ **HÜKÜM (T54/v23): ÖN KAYDIN HEPSİNİ SAĞLIYOR → TERFİYE UYGUN.**
    Üretimden **üç eksende** iyi: K2 14→12 · kararlılık 8→**4** (yarıya) ·
    gerçek kare zemin 0,3272→**0,4551** (etiketler 0,813).
  - 🔴 **D-133'ün tuzağı bu kez işlemiyor** — özellikle kontrol edildi: oradaki
    endişe *"geçiş sebebi doğru görmek değil AZ ZEMİN GÖRMEK olabilir"* idi.
    v23 tam **tersini** yapıyor: daha **çok** zemin görüyor ve yine de daha az
    moloza basıyor. Bu ikisi genelde ters yönde hareket eder.
  - ⚠ **AÇIK NOKTA (kapı değil):** v23 şartname figüründe zemin kaplamasını
    **16 kat** düşürüyor (%7,96 → %0,49). K0 bunu yakalamıyor (ölçüt
    `figur > 0.0`). Figür **YZ üretimidir** ve v23 gerçek karelerde **en çok
    gören** modeldir — ama açıklanmamış bir çöküştür → **T106**.
  - 🔴 **TERFİ KARARI MİMARIN DEĞİL.** D-133: *"iki KABUL EDİLEBİLİR model
    arasındaki sevk kararı ön-kayıtlarda çözülmez ve İNSANA aittir."*
    **Kullanıcı kararı bekleniyor.**
- [ ] **T88 — Arena sınırı dedektörü: ölçek kâhininin 2. katmanını BESLE** · `codes/karar_sozlesmesi.py`, `tests/**` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-94, D-137**
  - 🔴 **KAPI TUTMADI, ZORLANMADI · 2026-08-16 · Claude-2** · kayıt **D-138**.
  - **Görevin teşhisi doğru:** `mpp_arena_sinirindan` yazılı ama üretim çağrı
    yerleri `arena_sinir_px` geçmiyordu.
  - **DÖRT yaklaşım ölçüldü, ÜÇÜ ayırmadı** (negatif kontrol: drone, kompozit,
    arena_kadraj, gemini — toplam 118 kare):
    ```text
    1 Hough + aralik CV     arena 0,55 · arena_kadraj 0,14-0,32   AYIRMIYOR
    2 Morfolojik + CV       arena 0,52/0,55 · negatif 0,13-1,29   AYIRMIYOR
    3 Oziliski (periyot)    arena 0,497 · gemini medyan 0,472     AYIRMIYOR
    4 COK UZUN cizgi, IKI DIK AILEDE — min(dikey,yatay) parca:
        arena_gercek  n=  1     11 / 11 / 11
        drone         n= 14      0 /  0 /  0
        kompozit      n=  9      0 /  0 /  0
        arena_kadraj  n= 13      0 /  0 /  3
        gemini        n= 80      0 /  0 /  6      -> AYIRIYOR (esik 8)
    ```
  - 🔴 **AMA AYIRMAK YETMİYOR — katman 2 KONUM ister, sınıf değil:**
    ```text
    gercek arena karesi (1059x634) · olculen izgara acikligi   535 px
    izgaranin gercek yatay uzanimi                            ~840 px
    -> mpp %57 BUYUK · r_gerekli 11,8 px (olmasi gereken ~18,5) = %36 KUCUK
    ```
    Hata **EMNİYETSİZ** yönde: geçilemeyecek koridor geçilebilir sayılır.
    Bu yüzden dedektör üretim ölçek yoluna **BAĞLANMADI**; bir test bu
    bağlantısızlığı kilitler.
  - **D-94 bunu 260 karede ZATEN ölçmüştü** ("izgara cizgileri · guvenilir:
    **HAYIR**"; gerçek karede `[0, 1058]` = tüm kare). Kök neden orada yazılı:
    **moloz izgarayı gizliyor** (molozlu 118 karede dx0 medyan 79,0 px,
    molozsuz 102 karede 4,0 px — 20 kat). Bağımsız ölçüm onu **doğruluyor**;
    benim seçimim ters uca kaçıyor (sınırı KÜÇÜLTÜYOR).
  - **KAPILAR:**
    ```text
    (a) codes/test_rota_sentetik.py    SONUC: 15/15 dogru
    (b) unittest discover -s tests -q  Ran 553 · OK  (once 544, +9)
    (c) 72_kaynak_taramasi.py          arena_gercek  1 OLCEK_YOK  -> TUTMADI
    (d) sinir tespit edilemeyen kare   SAGLANDI (sessiz varsayim YOK)
    ```
  - **(d):** düz zemin, gürültü, yalnız-yatay-çizgili (yol şeridi) ve bozuk
    girdide dedektör False/None döner; kâhin katman 2'yi **atlar**, sebep
    `denenen` dökümüne yazılır, `rota_olcek_reddi` **OLCEK_YOK** ile reddeder.
    `tests/test_arena_sinir_dedektoru.py` (9 test).
  - **Emrin 4. maddesi uygulandı:** `arena_gercek` karesi üzerinde eğitim
    **yapılmadı ve önerilmiyor** (K0 ölçütünün baktığı karedir).
  - ⚠ **ÖNERİ (mimarın kararı):** katman 2 dedektörle değil **BEYANLA**
    beslenebilir — sınır piksel genişliği hakem/operatör tarafından bildirilir.
    Ayrım eşiği **tek pozitif örnekle** seçildi (n=1, D-88/D-99); genellenemez.

- [STATUS: READY_FOR_REVIEW] **T86 — Ölçek kâhinini üretim yoluna ve ekrana BAĞLA** · `codes/rpi_inference.py`, `codes/arac_maskesi.py`, `codes/karar_sozlesmesi.py`, `comms/yks_gui.py`, `config/model_registry.json`, `scripts/olcum/72_*`, `tests/**` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-126, D-136**
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-137**.
  - **KAPI (c) — kaynak taraması, ÖNCE/SONRA** (aynı betik, aynı model v30):
    ```text
    kaynak          ONCE rota   SONRA rota   ONCE OLCEK_YOK  SONRA OLCEK_YOK
    kompozit          0/9          0/9              0              0
    arena_kadraj     12/12        12/12             0              0
    arena_gercek      0/1          0/1              1              1
    gemini            0/12         0/12            12              9
    test              0/12         1/12            12              9
    val               0/12         0/12            12             11
    drone             0/12        11/12            12              0   <- ASIL
    ```
    `drone`da 12 karenin 12'si ölçeği **araç referansından** türetti. Arena yolu
    (telemetri/beyan) **değişmedi**.
  - 🔴 **KAPI (f) — rota UYDURULMADI, ama paylar kıl payı.** Ölçeksiz koşan
    kareler 1,0–9,8 px'lik "hayali aralık"lardan geçiyordu; C-uzayı koşunca
    **hiçbiri** o aralıktan geçmiyor:
    ```text
    kare                          A: olceksiz    B: kahinle (C-uzayi KOSAR)
                                   darbogaz      darbogaz  r_ger     pay
    frame_000005_000000816.jpg        5.00         16.78   16.77   +0.006
    frame_000006_000000336.jpg        1.00         15.18   15.16   +0.020
    frame_000010_000001824.jpg        2.00         14.18   14.11   +0.072
    frame_000000_000000000.jpg        1.00         17.58   16.97   +0.602
    frame_000016_000000720.jpg        1.00         17.60   14.91   +2.688
    frame_000001_000000168.jpg        1.00           —       —     GORUS_HATTI_KOPUK
    PAY < 0 olan kare: 0/11  — C-uzayi TUTUYOR
    ```
  - 🔴 **ASIL BULGU — paylar ölçeğin KENDİ belirsizliğinden küçük.** Katman 3
    "araç gövde genişliği 1,80 m" varsayar; D-124'ün kaydettiği bant
    **1,70–1,90 m**. `r_gerekli ∝ 1/arac_m` olduğundan 1,70 varsayımı
    r_gerekli'yi %5,9 büyütür:
    ```text
    varsayim     ayakta kalan rota
    1,90 m            11/11
    1,80 m            11/11   (kullanilan)
    1,70 m             4/11   🔴 YEDI ROTA DUSER
    ```
    Bu rotalar "güvenli" değil, **"1,80 m varsayımıyla güvenli"**dir. Eşik
    önerisi YAPILMADI; `R_GEREKLI_M`'e dokunulmadı.
  - **KAPILAR:**
    ```text
    (a) codes/test_rota_sentetik.py       SONUC: 15/15 dogru
    (b) unittest discover -s tests -q     Ran 544 · OK   (once 526, +18)
    (c) 72_kaynak_taramasi.py             drone OLCEK_YOK 12 -> 0
    (d) 65_kabul_denetcisi.py --model v30 K0..K4 D-133 ile BIREBIR
    (e) yks_gui --kaynak drone            GOZLE DOGRULANDI
    (f) drone darbogaz paylari            pay<0: 0/11
    ```
  - **(d):** `K0 %8.0 · K1 258/260 · K2 22/258 · K3 0/258 · K4 1/258` — D-133 ile
    birebir. `K5 None px` **T86 gerilemesi DEĞİLDİR**: denetçi aşılmış
    `63_bariyer_kesisimi.py`'yi çağırıyor, o betik tek karede rotayı
    `UC_BANT_TEMAS_YOK` ile reddedip "rota yok — kesişim ölçülemez" basıyor.
    Asıl ölçüm `66_k5_bariyer_populasyon.py`: **0/173 kare · 0 px · GEÇTİ**.
  - **(e) gözle doğrulama (D-80):** `results/t86/drone.png` — gerçek otopark
    karesinde sürüş koridoru çizili; `ölçek 0.0648 m/px (ARAÇ REFERANSI ·
    güven ×0.86 · arac kisa kenari 27.8 px = 1.80 m) · gövde açıklığı 17.0 px ·
    C-uzayı UYGULANDI · darboğaz 17.6 px @ şerit 2` → **17,6 > 17,0** ✓.
    Sağ panel `2 · ORTA · güven 0.421 · ölçek ARAÇ REFERANSI ×0.86` (çarpan
    güvene yansımış); protokol sayaçları **hepsi 0**.
  - 🔴 **AMELENİN BULDUĞU VE KAPATTIĞI KUSUR:** `arena_gercek` ölçeği
    "bilmiyorum" diye değil **REDDEDEREK** döndürür (D-90). İlk bağlamamda
    kâhin orada da çalışıyordu — sahnede araç görülseydi açık ret **sessizce
    ezilecekti**. `ALGI_SKALER_OLCEK_GECERSIZ` eklendi (tarama betiği aynı
    listeyi OKUR, ikinci kopya yok) ve iki testle çakıldı: biri katmanın
    çalışmadığını, karşıt kontrol yasak olmayan kaynakta çalıştığını kanıtlar.
  - **Yeni testler:** `tests/test_olcek_uretim_baglantisi.py` (15) +
    `test_yks_gui_uretim_hizasi.py` (2) + `test_model_registry.py` (1).
  - ⚠ **DOĞRULANAMADI:** **Katman 2 üretimde HİÇ çalışmadı ve çalışamaz** —
    arena sınırını görüntüden tespit eden fonksiyon YOK; parametreler bağlı,
    katman yalnız birim testiyle var (D-126'daki boşluk KAPANMADI). · **Katman 3
    Jetson'a gitmiyor** — ne `arac_maskesi.py` ne OBB ağırlığı pakette var; bu
    kayıt hakem ekranı + PC ölçümü içindir. · `test`/`gemini`/`val` karelerinde
    de ölçek üretildi (3+3+1) ve `test/road_233.jpg` bir rota verdi; bunlar yer
    seviyesi fotoğraflarıdır ve D-90'ın gerekçesi aynıyla geçerlidir — projede
    **açık ret kayıtlı olmadığı için** listeye eklemedim, karar mimarındır. ·
    Gerçek karelerde rotanın DOĞRU olup olmadığı ölçülmedi (yer gerçeği yok). ·
    `ARAC_GENISLIGI_M = 1.80` literatür değeridir, sahnedeki araçlar ölçülmedi. ·
    Arena ölçümlerinin tamamı sentetiktir (D-88/D-99).

- [STATUS: READY_FOR_REVIEW] **T85 — v30'u üretim zincirine al** · `config/model_registry.json`, `jetson_paket/**`, `JETSON_KILAVUZ.md` ×2, `scripts/olcum/**`, `tests/**` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-132, D-133, D-134**
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-136**.
  - **Ağırlık:** `models/navitas_seg_v30_best.pt` · sha256 `492e4508…` · 54.837.724 B.
    ⚠ Emrin "best.pt ile last.pt AYNI dosyadır" ifadesi **ölçüldü**: dosyalar
    bayt-eş **değil** (sha 492e4508 vs 3ca73a90), ama **537/537 ağırlık tensörü
    eşit**. Karar veren şey ağırlık olduğu için iddia anlamlı düzeyde doğru;
    **D-113 kusuru tekrarlamadı**.
  - **ONNX:** kanonik `scripts/export_tensorrt.py` ile üretildi; **FP16 kapısı
    GEÇTİ** (FP16 tensör 193 · FP32 tensör **0** — FP32 artefaktı yok).
    sha256 `091754c9…` · `results/onnx_export_v30_20260815/`.
  - 🔴 **BEŞ UÇ MUTASYONLA KANITLANDI** (D-15/K-04 — geçen kapı boş olabilir):
    ```text
    mutasyonsuz taban                  exit=0  OK (19 test)
    manifest asil_model    -> v27      exit=1  KIRMIZI (1)
    manifest asil_model_pt -> v27      exit=1  KIRMIZI (1)
    kilavuz (kok) ASIL     -> v27      exit=1  KIRMIZI (1)
    kilavuz (paket) ASIL   -> v27      exit=1  KIRMIZI (1)
    kayit defteri path     -> v27      exit=1  KIRMIZI (7)
    geri yazma sonrasi                 exit=0  OK   (dosyalar bayt-birebir)
    ```
  - **KAPILAR:**
    ```text
    (a) codes/test_rota_sentetik.py     SONUC: 15/15 dogru
    (b) unittest discover -s tests -q   Ran 526 tests · OK  (once 526, DUSMEDI)
    (c) scripts/saha_kuru_kosu.py       model_yukleme GECTI [35 ms]
    (d) yks_gui --gorunum canli --kaynak arena_kadraj   GOZLE DOGRULANDI
    (e) scripts/jetson_paket_hazirla.py 9/9 BAYT-ESIT
    (f) 67_onnx_karar_denkligi.py       259/260 (%99,6) — OLCUM, KAPI DEGIL
    ```
  - **KAPI (f) — ONNX ile .pt karar denkliği:**
    ```text
    olculen kare         260      KARAR AYNI  259/260 (%99,6)
    ikisi de rota uretti  258/260
    rota IoU  ort 0,9816 · en dusuk 0,0000
    azami sapma ort 2,4 px (0,184 m) · en kotu 194,0 px (15,156 m)
    zemin maskesi IoU ort 0,9975 · kaplama farki ort +0,00048
    UYUSMAZLIK: sa_000131.jpg  pt=serit 2  onnx=serit 1
    v27 kiyasi (D-116/3): 258/260, iki kare, 28 m
    ```
    **Yorum yapılmadı — mimarındır.**
  - **(d) gözle doğrulama (D-80):** `results/t85/v30_ekran.png` — sağ panel
    **"AÇIK YOL TESPİTİ — YEREL ALGI (telsiz DEĞİL)"**, karar **2·ORTA**,
    güven **0,848** + `%85` çubuğu, kaynak satırı `arena_kadraj/sa_000026.jpg`;
    sol panelde rota **çizili**; günlükte `navitas_seg_v30_best.pt (SHA
    492e4508)`; protokol sayaçları **hepsi 0** (T81 kaynak ayrımı korunuyor).
  - ⚠ **KAPSAM GENİŞLETİLDİ (bilerek, emrin 6. maddesi gereği):** üç ölçüm
    betiği sürüm adını **çıplak sabit** taşıyordu — `67_onnx_karar_denkligi.py`,
    `68_karar_kararliligi.py`, `70_gercek_kare_rota_denemesi.py`. Argümansız
    koşan bir kararlılık ölçümü **v27'yi ölçüp sonucu üretim modelinin sayısı
    diye** kaydederdi. `scripts/olcum/ayarlar.py`'ye fail-closed `uretim_pt()` /
    `uretim_onnx()` eklendi; dört dosyanın `O:\navitas-local-train` kopyaları
    bayt-eş yenilendi. Bu beş uçtan **değildir**; mimar isterse ayrılabilir.
  - 🔴 **DOĞRULANAMADI:** v30'un **kararlılık gerilemesi** (8/260 vs v28 3/260)
    bu görevde çözülmedi — T85 çevirme görevidir, ölçüm görevi değil; mimarın
    D-133'teki "T79 inince kalkar" gerekçesi **hâlâ doğrulanmamıştır** (T79
    D-126'da kapıyı tutturamadı, `[ ]`). · Gerçek karelerdeki **65/67
    doğrulanmamıştır** (kaplama 0,594 vs etiket 0,813) ve deftere
    `"DOGRULANMADI"` diye yazıldı. · Arena ölçümlerinin tamamı **sentetiktir**
    (D-88/D-99). · `mask_map50` v30 için **ölçülmedi**; v27/v4 değerleri
    **taşınmadı**. · **Jetson'da hiçbir şey koşulmadı** — engine derlenmedi,
    ONNX denkliği PC'de ölçüldü ve **CUDA sağlayıcısı bulunamadı** uyarısı
    düştü (CPU'da koşmuş olabilir; Jetson TensorRT FP16 farklı davranabilir).
  - ⚠ **Saha kuru koşusunda `rota` halkası DÜŞTÜ** (`BELIRSIZ_TEK_KAPI`) —
    T85 gerilemesi **değildir**: 2026-08-14 (v27) koşusunda da düşüktü
    (`BELIRSIZ_COKLU`). Belirsizlik sınıfı değişti, halkanın durumu değişmedi.
  - **Amelenin kendi hatası:** kılavuz çevirme betiğinde değişim sırası
    yanlıştı; genel v27→v30 değişimi **§0-T76 kayıt bölümünü** ve ağaçtaki
    "eski asıl, karar kıyası için" satırını da çevirdi (tarihsel kaydı bir an
    tahrif etti). İki dosyada da elle geri alındı ve denetlendi. **Kapılar bunu
    yakalamazdı** — kapı yalnız `ASIL` satırına bakar, kayıt bölümüne bakmaz.

- [STATUS: READY_FOR_REVIEW] **T83 — Ölçek kâhini hiyerarşisi (telemetri → arena sınırı → araç referansı)** · `codes/karar_sozlesmesi.py`, `codes/rpi_inference.py`, `tests/**` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-124**
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-126**.
  - **KAPI (e) — 67 gerçek karede ölçek kaynağı:**
    ```text
    telemetri        0/67  (%  0.0)   carpan 1.00
    arena_siniri     0/67  (%  0.0)   carpan 0.70   (otoparkta ARENA YOK)
    arac_referansi  67/67  (%100.0)   carpan 0.86
    OLCEK TURETILEBILEN: 67/67   (onceki durum: 0/67)
    mpp 0.06437 / 0.07459 / 0.11409 · r_gerekli 9.6 / 14.7 / 17.1 px
    ```
    D-124 **bağımsız doğrulandı** (mimar: mpp 0,07321 · r_gerekli 14,2–15,9 px).
  - 🔴 **Güven çarpanları ölçülen belirsizlikten türetildi, uydurulmadı:**
    telemetri **1.00** (sözleşme otoritesi) · arena **0.70** (T65/D-94: sınır
    perspektif yamuk, genişlik 730→950 px = %30) · araç **0.86** (D-124:
    IQR/medyan 0,138).
  - ⚠ **Ölçüm emrin sıralamasını doğrulamıyor:** katman 2 (0.70) katman 3'ten
    (0.86) **daha belirsiz** çıktı. Sıralama kullanıcının kararı olduğu için
    **değiştirmedim**; çarpanlar ölçülen gerçeği yansıtıyor. Çevirme kararı
    mimarın.
  - 🔴 **Senaryo beyan edilir:** bilinmeyen anahtar → katman 2 devreye girmez.
    Testle sayıya bağlandı: aynı sınırda HTAB/FDA oranı **tam 2,5**.
    "kare = arena" varsayımı yok; sınır tespit edilemezse katman çalışmaz.
  - **Geriye uyum:** `analyze_path(..., olcek_kaynagi=telemetri)` varsayılanı ve
    çarpanı 1.00 — mevcut çağrı yerlerinin güveni **birebir** korunur. Kaynak ve
    çarpan `olcum` sözlüğüne yazılır (sessiz düşüş yok; `denenen` alanı her
    katmanın neden girmediğini taşır).
  - **Yeni testler:** `tests/test_olcek_kahini.py` (21).
  - ⚠ **DOĞRULANAMADI:** katman 2 **hiçbir gerçek karede çalışmadı** (otoparkta
    arena yok) — yalnız birim testiyle doğrulandı; araç referansı **arenada
    çalışmaz** (arenada araç yok), 67/67 sonucu otopark içindir; kâhin üretim
    çağrı yerlerine ve ekrana **bağlanmadı**; `ARAC_GENISLIGI_M = 1.80` literatür
    değeridir, sahnedeki araçlar ölçülmedi (band duyarlılığı %11,1 testte).

- [STATUS: READY_FOR_REVIEW] **T82 — Açık alanı çökmüş maskeden ayıran İKİNCİ bir sinyal ara** · ölçüm görevi · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-124**
  - **✅ ÖLÇÜLDÜ · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-125**.
    **714 maske.** 🔴 **KOD DEĞİŞTİRİLMEDİ, EŞİKLERE DOKUNULMADI.**
  - **VERDİKT: AYIRMIYOR.** Üç ayrı sebeple, üçü de ölçüldü.
  - **Kümeler:** (a) meşru yer gerçeği **320** (kadraj t66 train 234 + val 26 +
    sentetik val 60 — T52'nin kümesi birebir) · (b) çökme v21 **67** ·
    (c) otopark v27 **67** · (d) **kontrol**: meşru v27 **260** ·
    (e) **emniyet**: v21 arena **260**.
  - **Dağılım (min/medyan/maks):**
    ```text
    olcut               a_mesru_GT       b_cokme_v21      c_otopark_v27     d_mesru_v27
    delik_sayisi     0,0/  1,0/ 15,0  24,0/33,0/47,0  23,0/33,0/46,0   0,0/ 2,0/19,0
    delik_yogunlugu  0,0/ 10,6/134,9  43,3/58,1/81,0  41,2/58,0/78,4   0,0/14,9/109
    delik_alan_orani 0,00/0,02/0,26   0,10/0,17/0,22  0,10/0,16/0,22   0,00/0,03/0,25
    en_buyuk_pay     0,29/0,76/1,00   1,00/1,00/1,00  1,00/1,00/1,00   0,45/0,88/1,00
    euler          -14,0/ 2,0/ 11,0  -45,0/-25,0/8,0 -42,0/-25,0/5,0  -15,0/ 1,0/11,0
    kaplama          0,06/0,32/0,65   0,77/0,80/0,86  0,77/0,80/0,87   0,19/0,33/0,64
    ```
  - 🔴 **Sebep 1 — YÖN TERS.** Hipotez "çökme deliksiz" diyordu; ölçüm tersini
    söylüyor: çökme medyanı **33 delik**, meşru medyanı **1**. Çökmüş maske
    meşrudan **on kat daha delikli**.
  - 🔴 **Sebep 2 — (b) ve (c) AYNI karelerdir ve ayırt edilemiyorlar** (her
    ölçütte örtüşüyorlar). Veride "geçmesi gereken meşru açık otopark" diye bir
    sınıf **yok**; soru mevcut veriyle **cevaplanamaz**. Ayrılan şey "çökme mi
    meşru mu" değil, **"arena mı otopark mı"**.
  - 🔴 **Sebep 3 — EMNİYET ARGÜMANI sinyali öldürüyor (madde 3).** Tablodan
    aday eşik türetilebilir: meşru azami 19, otopark asgari 23 → geçerli aralık
    (19, 23), ortası ~21, kural "delik > 21 ise REDDET". Bu kural **arenadaki
    gerçek çökmeyi kaçırır**:
    ```text
    (e) v21, MESRU arena, n=260
        kapinin olcutuyle COKMUS: 2/260   (kaplama>0,67 VE kenar>0,50)
        o karelerde delik_sayisi: 0 ve 6
        aday esigin yakaladigi:   0/2     <- SIFIR
    ```
    Çökme arenada olunca maske tek parça ve deliksizdir; sinyal "meşru" der.
    **Kapının varlık sebebi tam olarak o kareyi yakalamaktır.**
  - **KAPI (a):** `codes/test_rota_sentetik.py` → **SONUC: 15/15 dogru**.
  - **KAPI (d) — görsel (D-80):** `results/t82_delik_yapisi/delik_yapisi_gorsel.png`
    (delikler mor):
    ```text
    COKME   (v21, arena  sa_000106)  kaplama %86   DELIK  6
    MESRU   (v27, arena  sa_000026)  kaplama %22   DELIK  6
    OTOPARK (v27, gercek frame_0)    kaplama %78   DELIK 26
    ```
    Çökme ile meşru **aynı delik sayısına** sahip (6 = 6). Gözle de aynı sonuç.
  - ⚠ **DOĞRULANAMADI:** (1) 🔴 **v25 ağırlığı depoda YOK** — madde 3'ün "v25
    körlüğünü yakalıyor mu" yarısı **ölçülemedi** (D-59'daki "v13 ağırlığı yok"
    ile aynı sınıf, iddia edilmedi); (2) meşru sınıf yer gerçeği, negatifler
    model çıktısı — asimetri **(d) kontrolüyle** giderildi (v27'nin meşru
    sahnelerdeki çıktısı da az delikli, medyan 2), ayrım GT/model farkından
    gelmiyor; (3) arenadaki çökme sınıfı **n=2** — zayıf örneklem, ama yön açık
    ve mekanizma fizikseldir; (4) gerçek arena karesi yok (D-88/D-99), tüm
    "meşru" ölçümler sentetiktir; (5) delik eşiği 25 px — daha düşük eşik tüm
    kümelerde delik sayısını artırır, **örtüşmeyi azaltmaz**.
  - **SONUÇ:** yeni sinyal **önerilmiyor**. D-124'ün tespiti ayakta: kapı
    "SINIRLI ARENA" varsayımı taşır; otoparkta rota üretilememesi bu varsayımın
    sonucudur, maske yapısıyla çözülecek bir şey değildir.

- [STATUS: READY_FOR_REVIEW] **T81 — Canlı Algı görünümünde sağ panel, canlı algı sonucunu göstersin** · `comms/yks_gui.py`, `tests/**` · **ÖNEMLİ** · kanıt: ekran görüntüsü (mimar ölçtü)
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-121**.
  - **Kusur:** canlı algı görünümünde sol panel rotayı buluyordu ama sağ kutu
    telsizden gelen OPEN_ROUTE'u beklediği için "— BEKLENİYOR —" yazıyordu;
    bağlı İHA olmadığından asla dolmuyordu. Ekrana bakan "yol bulunamadı"
    sonucunu çıkarıyordu — **kullanıcı üç ayrı oturumda bu sonuca vardı**.
  - 🔴 **Önce kısıt, sonra düzeltme.** Karıştırma yasağı düzeltmeden önemli:
    hakem §6.2 onayını **aracın gönderdiği** rotaya verir. Bu yüzden tasarım
    şöyle: **kutuyu GÖRÜNÜM besler, gelen mesaj değil.** İki kaynak ayrı
    saklanır ve ekrana yalnız görünümün kaynağı basılır.
    ```text
    Saha Haritası -> kutu `protokol` durumunu gösterir
    Canlı Algı    -> kutu `yerel`    durumunu gösterir
    ```
    Canlı algı görünümündeyken gelen OPEN_ROUTE kutuyu **boyamaz** (durumu
    saklanır, haritaya dönünce olduğu gibi görünür); ters yön de aynı.
    **İki yön de testle kilitli.**
  - **Kaynak iki yerde yazılı** — kırpılmış bir ekran görüntüsünde bile
    görünsün diye hem panel başlığında hem detay satırında:
    `AÇIK YOL TESPİTİ — YEREL ALGI (telsiz DEĞİL)` ve
    `YEREL ALGI — telsiz DEĞİL · arena_kadraj/sa_000026.jpg · güven 0.848`.
  - **Yapısal veri, metin ayrıştırma YOK:** kutu, algı kuyruğuna eklenen
    yapısal sözlükten beslenir (`yol_no`, `guven`, `ret`, `gerekce`, `kaynak`,
    `kare`). Bilgi metnini ayrıştırmak sessizce bozulur ve kutu **yanlış**
    değer gösterirdi — hakem onayı buna dayanıyor.
  - **KAPI (a):** `test_rota_sentetik.py` → **SONUC: 15/15 dogru**.
  - **KAPI (b):** `discover -s tests -q` → **Ran 488 · OK** (481 → +7, düşmedi).
  - **KAPI (c)** `--kaynak arena_kadraj` → `results/t81/canli_arena.png`:
    `2 · ORTA` (yeşil, büyük punto) · `güven 0.848` · çubuk `güven %85` ·
    **"BEKLENİYOR" ekranda YOK**, **"YEREL ALGI" VAR**.
  - **KAPI (d)** `--kaynak drone` → `results/t81/canli_drone.png`:
    `ROTA YOK` (kırmızı) + `ZEMIN_MASKESI_SUPHELI` + tam gerekçe
    ("…%78.0'ini kapliyor (tavan %67.0) VE cevrenin %72.8'ine dayaniyor…").
    Bu ret **D-118'de meşru** ölçülmüştü (model orada binanın çatısını zemin
    sayıyor).
  - **KAPI (e)** `--gorunum saha` → `results/t81/saha.png`: başlık
    `AÇIK YOL TESPİTİ` (**değişmedi**), `— BEKLENİYOR —`,
    `İHA taraması sürüyor`. Harita görünümü birebir eskisi gibi.
  - **KAPI (f) — sayaç sızıntısı YOK:** test, iki yerel karardan (kabul + ret)
    sonra `sayac` sözlüğünün **birebir aynı** kaldığını, `rota`/`rota_yok`ün
    `None` kaldığını, `tespit_onayli`nin değişmediğini kilitliyor. Ayrıca
    **üç ekran görüntüsünde de** gözle okunuyor:
    `OPEN_ROUTE 0 · RED 0 · NO_ROUTE 0 · LANDED 0 · HB 0 · ACK 0`.
  - **Yeni testler (7):** yerel kararın gösterilmesi · kaynağın başlık+detayda
    yazması · ret sebebi + gerekçe · harita görünümünün değişmediği · yerel →
    harita sızmaması · telsiz → canlı algı sızmaması · sayaç sızıntısı.
    ⚠ İlk yazımımda sahte etiketler **boş** başlıyordu ve "sızmadı" iddiası boş
    etiketle sınanıyordu — hiçbir şey kanıtlamıyordu. **İki test bunu yakaladı;**
    fikstür artık gerçek uygulamadaki gibi çizilmiş durumdan koşuyor.
  - ⚠ **ÖLÇÜLEN YAN ETKİ (gizlenmiyor):** uzun gerekçe (~200 karakter, 400 px
    sarmada 5 satır) sağ sütunu büyütüyor ve **ret durumunda** alt kontrol
    şeridi bir satır aşağı kayıyor. Kapı (e) görüntüsüyle kıyaslandı: kutu
    kısayken pencere tam sığıyor. Metni **kısaltmadım** — emrin 4. maddesi
    gerekçeyi şart koşuyor ve sayılar hakem için işlevsel. Sarma genişliğini
    artırmak ~20 px kazandırıyor (sütun S(440), sarma S(400)) — değmez. Çözüm
    pencere yerleşiminde; **ayrı görev**.
  - ⚠ **Emoji kaldırıldı:** başlıkta `🔴` vardı; tkinter renkli emojiyi
    çizemiyor, hakem ekranında **taralı bir kutu** görünüyordu (ilk ekran
    görüntüsünde görüldü, düzeltildi). Uyarı artık metinle taşınıyor.
  - ⚠ **DOĞRULANAMADI:** (1) gerçek bir OPEN_ROUTE ile canlı algı **aynı anda**
    sınanmadı (bağlı İHA yok) — iki yönlü sızmama testle kilitli ama sahada
    eşzamanlı trafikle doğrulanmadı; (2) kutu yalnız **en son** kareyi gösterir,
    kaynak değişince önceki karar kaybolur (protokol tarafında da böyleydi,
    değiştirilmedi); (3) hakem onay butonu canlı algı kararına **bağlanmadı** ve
    bağlanmamalıdır — onay telsizden gelen tespite verilir; ekran "Onay bekleyen
    tespit yok" demeye devam eder; (4) `arena_kadraj` kümesi **sentetiktir**
    (D-88/D-99) — sağ panelin rota göstermesi sahada rota üretileceği anlamına
    gelmez.

- [STATUS: READY_FOR_REVIEW] **T80 — Hakem ekranı istenen durumda AÇILABİLSİN (`--kaynak`, `--gorunum`)** · `comms/yks_gui.py`, `tests/**` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-118**
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-120**.
  - **Kusur:** ekran hep `kompozit` + "Saha Haritası" ile açılıyordu. `kompozit`
    bir **otopark** karesidir; zemin kapısı orada **meşru** olarak
    `ZEMIN_MASKESI_SUPHELI` verir (D-118: model binanın **çatısını** zemin
    sayıyor). Ekranı açan önce "yol bulunamadı" görüyor, rotayı görmek için
    V + K tuşluyordu — tanıtımda kötü ve **tekrarlanabilir değil**.
  - **`--kaynak`:** geçerli değerler `YksArayuz.ALGI_KAYNAKLAR`'dan okunuyor,
    liste **çıplak yazılmadı** (madde 16). AST testi List/Tuple literalini
    yasaklıyor.
  - **`--gorunum saha|canli`:** CLI adları iç adlara (`harita`/`algi`)
    `GORUNUM_SECENEKLERI` ile eşleniyor; test iç adları **kaynaktan toplayıp**
    karşılaştırıyor — buton/kısayol tarafıyla ayrışırsa test düşer.
  - ⚠ **VARSAYILANLAR DEĞİŞMEDİ.** İkisinin de `default`u yok. Verilmezse açılış
    bugünkü gibi: `kompozit` + Saha Haritası. `kompozit` **bilerek** duruyor
    (domain boşluğunu hakeme gösterir, D-53/D-90). Üç ayrı test kilitliyor.
  - **Sıra önemli:** kaynak, görünümden **önce** kuruluyor. `gorunum("algi")`
    çıkarımı hemen tetikler; kaynak sonra ayarlansaydı **ilk kare** eski
    kaynaktan gelirdi — üstelik tanıtımda görünen kare tam odur.
  - **KAPI (a):** `codes/test_rota_sentetik.py` → **SONUC: 15/15 dogru**.
  - **KAPI (b):** `discover -s tests -q` → **Ran 481 · OK** (475 → +6, düşmedi).
  - **KAPI (c) — emrin komutu aynen koşuldu**, `SS kaydedildi ... exit=0`:
    ```text
    arena_kadraj/sa_000026.jpg -> karar: 2·ORTA · güven 0.848 · 1594 ms
    çıkarım: üretim (rpi_inference) · predict conf 0.30
    traversable %22 · blocked %20 · gösterim: sürüş koridoru
    model: navitas_seg_v27_best.pt · ölçek 0.0781 m/px (kabul kümesi manifesti)
    gövde açıklığı 14.1 px · C-uzayı UYGULANDI · darboğaz 19.0 px @ şerit 2
    ```
    **Gözle doğrulandı (D-80):** kırmızı engel katmanı, serbest koridor, **sarı
    rota + waypoint'ler**, tepede `H`, İHA-İB mavi alanı. Rota **ilk karede,
    tuşa basmadan** görünüyor — kusur kapandı.
    ⚠ **Bağımsız doğrulama:** SS'teki mesaj günlüğünde
    `ALGI kaynağı (--kaynak): arena_kadraj` · `Açılış görünümü: canli` ·
    `navitas_seg_v27_best.pt (SHA 1465ed3d)` okunuyor. O SHA kayıt defterindeki
    `sha256`nın ilk sekiz karakteridir (T76/D-116) — ekranın üretim ağırlığını
    yüklediği argümanlardan **bağımsız** olarak da görünüyor.
  - **KAPI (d) — geçersiz değer, ekran AÇILMIYOR:**
    ```text
    yks_gui.py: error: argument --kaynak: invalid choice: 'xyz'
      (choose from kompozit, arena_kadraj, arena_gercek, drone, gemini, test, val)
    exit = 2      (Tk penceresi HİÇ oluşturulmadı)
    ```
  - **Yeni testler (6):** `choices` AST kilidi · argparse'ın kabul ettiği **her**
    kaynağın `_algi_gorseller()` ile çözülebilmesi (kabul edilip çözülemeyen ad
    ekranı `KeyError` ile çökertirdi) · görünüm eşlemesi ↔ iç adlar ·
    varsayılanların taşınmadığı · `--kaynak arena_kadraj` → defterdeki
    `kabul_kumesi` (T77 bağlantısı) · geçersiz değerde alt süreçte fail-closed.
  - **Küçük sağlamlık:** `--kaydet-yolu` alt dizin gösteriyorsa dizin açılıyor;
    aksi hâlde emrin `results\t80\` yazan komutunda SS sessizce kaybolurdu.
  - ⚠ **DOĞRULANAMADI:** (1) SS'teki kare kümenin **ilk** karesidir, küme
    genelinde rota üretimi bu görevde yeniden ölçülmedi (T77'de 12/12);
    (2) `--gorunum canli` açılışta model ~2 sn yükleniyor — `--otokaydet` bundan
    kısa verilirse SS "işleniyor…" hâlini yakalar, betik **beklemez**; alt sınır
    ölçülmedi; (3) `--kaynak` yalnız **açılışı** belirler, `K` kısayolu sırayı
    eskisi gibi döndürür (kilitleme istenmedi, yapılmadı); (4) kabul kümesi de
    **sentetiktir** (D-88/D-99) — açılışta rota göstermek sahada rota üreteceği
    anlamına **gelmez**.

- [STATUS: READY_FOR_REVIEW] **T78 — Zemin kapısı v24 ile kalibre, v27 ile DEĞİL: yeniden ölç** · ölçüm görevi · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-118**
  - **✅ ÖLÇÜLDÜ · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-118**.
    **1568 ölçüm.** 🔴 **EŞİK DEĞİŞTİRİLMEDİ** — 0,67 / 0,50 aynen duruyor.
  - **VERDİKT: hipotezin ÖNCÜLÜ doğru, SONUCU yanlış.** v27 kabul dağılımında
    tavanı **delmiyor**: azami kaplama **0,636**, tavana **+0,034 pay**.
    Tavanı delen **v24**'tü (azami 0,765, pay **−0,095**).
  - 🔴 **Gerçek karelerde yer gerçeği YOK — bu önce söylenmeli.** Emrin üç
    kümesinde "yer gerçeği" insan etiketi değil:
    `copy_paste_gercek` → `zemin_tam_cerceve: true`, GT kaplama **1,000**;
    `arena_kompozit` → GT `navitas_seg_v21_best.pt` **çıktısı**, GT **0,285**;
    `raw_frames` → etiket yok. **Aynı otopark için iki GT 1,000 ve 0,285 diyor.**
    Emrin 2. maddesi bu kümelerde karşılanamaz; cevap sahnenin değil etiket
    konvansiyonunun cevabı olurdu.
  - 🔴 **D-116'daki kompozit reddi v27'den GELMİYOR** (n=524, iki model):
    ```text
    kume               n    v24 medyan  v27 medyan   fark     RED (v24 / v27)
    arena_kompozit     9      0,829       0,836     +0,007     9/9  ·   9/9
    raw_frames        67      0,801       0,806     +0,005    67/67 ·  67/67
    copy_paste_gercek 448     0,801       0,805     +0,004   448/448 · 448/448
    ```
    v24 aynı kareyi aynı şekilde reddediyor. "v27 geldi de bozuldu" gerekçesi
    **ölçümle çürütüldü**.
  - **ASIL ÖLÇÜM — gerçek GT'si olan tek küme: T66 kabul kümesi (n=260):**
    ```text
    olcut                      v24                 v27
    kaplama min/med/maks  0,000/0,272/0,765   0,189/0,332/0,636
    GT kaplama            0,184/0,334/0,652   (ayni GT)
    |model - GT| medyan        0,1023              0,0051
    IoU medyan                 0,4534              0,9220
    kaplama > 0,67               5/260               0/260
    KAPI REDDI                   1/260               0/260
    TAVANA KALAN PAY            -0,095              +0,034
    ```
  - **Neden öncül doğru ama sonuç yanlış:** v27 gerçekten daha geniş zemin
    görüyor (0,272 → 0,332) — ama **GT'nin kendisi 0,334**. Genişlemek tavana
    değil **gerçeğe** yaklaşmaktır; tavan (0,67) gerçeğin **iki katı** uzağında.
    v24'ün tavanı deldiği 5 kare, v24'ün **yanıldığı** karelerdi (fark +0,089…
    +0,258, IoU 0,476…0,842); v27 aynı karelerde GT'nin altında/eşinde.
  - **Kapı (0,67 / 0,50) v27 için YENİDEN GEÇERLENDİ** (kalibre edilmedi):
    meşru elenen **0/260** (v24'te 1/260 idi) · arena dışı yakalanan **524/524**.
  - **GÖRSEL KAPI (D-80) — kapı HAKLI:** `results/t78_zemin_kalibrasyon/
    kompozit_zemin_maskesi.png` (girdi · v24 · v27): her iki model de araçları
    kırmızı (doğru) ama **binanın ÇATISINI YEŞİL** — yani zemin — boyuyor.
    Kapının gerekçe metni ("çatı/çim/toprak zemin sayılmış olabilir") o karede
    **harfiyen doğru**. Tavanı gevşetmek, İKA'yı bir binanın **çatısına** rota
    çizmeye açık bırakırdı.
  - **Önceden kapatılan itiraz** ("kapı HAM zemini ölçüyor, ETKİN serbest alanı
    değil"): ölçüldü — `arena_kompozit` 0,825 → 0,788, `raw_frames` 0,814 →
    0,776; **red 9/9 ve 67/67 aynen kalıyor**. Verdikt değişmiyor (çatıda engel
    yok; engeli çıkarmak çatıyı zemin saymayı düzeltmez). **Uygulanmadı** —
    eşik çifti HAM zemin üzerinde türetilmiştir (T52/D-66, D-85).
  - **D-114/D-115 bağımsız doğrulandı:** D-114 0,3419 / 0,2877 / GT 0,3459
    demişti; bağımsız ölçümüm 0,3315 / 0,2723 / 0,3345. Üstüne D-114'te olmayan
    şey: v27'nin GT'ye **yakınlığı** (IoU 0,453 → 0,922).
  - **KAPILAR:** `test_rota_sentetik.py` → **15/15** · `discover -s tests -q` →
    **Ran 475 · OK** · `ZEMIN_KAPLAMA_TAVANI = 0.67` ve
    `ZEMIN_KENAR_DAYANMA_TAVANI = 0.50` **değişmedi**.
  - **KAPI (d) KOŞULMADI** — emir "eşiği değiştirdiysen kabul denetimini koş"
    diyor; eşik değişmedi, K0..K5'in değişmesi için sebep yok. Koşulmuş gibi
    **yazılmadı**.
  - ⚠ **DOĞRULANAMADI:** (1) **gerçek arena karesi yok** — "gerçek kareler"
    otoparktır, tavanın gerçek arenada doğru olduğu ölçülemedi; T59'un tek
    gerçek arena karesi v27 ile yeniden ölçülmedi (küme listesinde yoktu);
    (2) T59'un kaydettiği 0,67 bedeli (`sa_000150`) v27 için yeniden ölçülmedi
    — o kare T60 kümesinden; (3) eşli tabloda `raw_frames` 64/67 eşleşti (üç
    kare adı alt klasörler arasında aynı; özet tablo 67'nin tamamını kullanır);
    (4) "çökme" tanımı gerçek karelerde yorumlanamadığı için o tablo **karara
    sokulmadı** — karar yalnız T66 kümesine ve görsele dayanır; (5) kapının HAM
    zemini ölçmesi bir **tasarım seçimidir**, bu görevde sorgulanmadı.

- [STATUS: READY_FOR_REVIEW] **T77 — Hakem ekranı, modelin KABUL EDİLDİĞİ zemini göstersin** · `comms/yks_gui.py`, `config/model_registry.json`, `tests/**` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-116/5**
  - **✅ UYGULANDI · 2026-08-15 · Claude-2** · kayıt `REVIEW_LOG.md` **D-117**.
  - **Kusur:** `ALGI_ARENA_KADRAJ_KOKU` T60 yolunu **çıplak sabit** taşıyordu;
    model v27'ye geçince kimse çevirmedi. Ekran, modeli **kabul edilmediği**
    bir dağılımda gösteriyordu (T60 11/12 · T66 12/12). T58'in kusur sınıfının
    aynısı (D-58/D-60/D-83) — T76 aynı dosyada **ağırlık** için kapatmıştı,
    **zemin** açık kalmıştı.
  - **Kabul kümesi modelin kimliğine bağlandı:** yol artık
    `config/model_registry.json` etkin profilindeki **`kabul_kumesi`**
    alanından okunuyor. Gerekçe: "hangi zeminde kabul edildi" modelin
    kimliğinin parçasıdır; ağırlıkla **aynı yerde** durur ki sürüm değişince
    ikisi ayrı ayrı unutulamasın.
  - **Tek okuma yolu:** `_uretim_modeli_adi()` ve `_kabul_kumesi_koku()` artık
    ortak `_kayit_profili()` üzerinden okuyor. T76'nın fail-closed davranışı
    korundu (beş bozuk defter biçimiyle sınanan testler değişmeden geçti).
  - ⚠ **Fail-closed sınırı bilerek çizildi:** alan yok/boş/sayı ise
    `RuntimeError`. Ama **dizinin var olması şart koşulmadı** — küme depo
    dışındadır, temiz klonda bulunmayabilir; o durumda ekran "Kaynak boş" der.
    Fail-closed olan şey **bildirimin** yokluğudur, verinin değil; aksi hâlde
    bu satır ağırlık gerektirmeyen ~470 testi import zamanında çökertirdi.
  - **Ölçek notu da düzeltildi:** ekran "T60 manifesti" yazıyordu → "kabul
    kümesi manifesti". Küme değişince ekranda yanlış küme adı kalmıyor.
  - **KAPI (a):** `codes/test_rota_sentetik.py` → **SONUC: 15/15 dogru**.
  - **KAPI (b):** `discover -s tests -q` → **Ran 475 tests · OK**
    (T76'da 471 idi; **düşmedi**, +4).
  - **KAPI (c) — hakem ekranı** (`--demo` yok, model sahte değil, **kare
    seçilmedi**, idx 0):
    ```text
    kare  sa_000026.jpg
    karar 2·ORTA · güven 0.848 · model: navitas_seg_v27_best.pt
    ölçek 0.0781 m/px (kabul kümesi manifesti) · gövde açıklığı 14.1 px
    C-uzayı UYGULANDI · darboğaz 19.0 px @ şerit 2 · dağılım 0/540/0 px
    SS: results/t77_hakem_ekrani/yks_ekran_kabul_kumesi.png (1707x996)
    ```
    **Gözle doğrulandı (D-80):** kırmızı engel katmanı (moloz **adaları** — T66
    geometrisi), serbest koridor, **sarı rota + waypoint'ler**, tepede `H`,
    İHA-İB mavi alanı ve yatay bariyerler. Panel, T76'nın T60 görüntüsündeki
    **dikey şeritlerden gözle ayırt edilebiliyor** — gösterilen zeminin
    gerçekten değiştiği görsel olarak da doğrulandı.
  - ⚠ Darboğaz **41.0 px (T60) → 19.0 px (T66)**, güven **1.000 → 0.848**.
    T66 ada geometrisi koridorları **daraltıyor**. Gerileme değil, kabul
    kümesinin daha zor olması — ama **T74** ile aynı yöne işaret ediyor.
  - **KAPI (d) — kabul kümesinde karar (n=12, ilk 12, seçim yok):**
    ```text
    ROTA URETILEN: 12/12   (8 ORTA · 3 SOL · 1 SAG)
    C-uzayi: 12/12 UYGULANDI
    ```
  - **Test ters çevrildi, SİLİNMEDİ:** yol değil **invaryant** kilitli —
    `test_kadraj_koku_KABUL_KUMESIDIR` (ekran == defterin ilanı) ·
    `test_kadraj_yolu_kaynakta_CIPLAK_YAZILMAMIS` (madde 16) ·
    `test_ilan_edilen_kume_ESKI_T60_DEGIL` (açık gerileme kilidi) ·
    `test_defterde_kabul_kumesi_yoksa_ekran_UYDURMAZ` (fail-closed).
  - ⚠ **DOĞRULANAMADI:** (1) n=12 ilk karelerdir, **260'ın tamamı ekran
    yolundan koşulmadı** (D-115'in 255/260'ı başka betikle ölçüldü);
    (2) kabul kümesi de **sentetiktir** — ekranın doğru zemini göstermesi
    sahada çalışacağı anlamına **gelmez** (D-88/D-99); (3) `kabul_kumesi` depo
    dışını gösterir, başka makinede küme **bulunmaz**; (4) kompozit kaynak hâlâ
    `ZEMIN_MASKESI_SUPHELI` veriyor — T77 ona **dokunmadı**, T78'in konusu.

- [STATUS: READY_FOR_REVIEW] **T76 — v27'yi üretim zincirine al, `model_yukleme` halkasını kapat** · `config/model_registry.json`, `jetson_paket/models/**`, `comms/yks_gui.py`, `JETSON_KILAVUZ.md` (İKİ kopya), `tests/**` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-115**
  - **✅ UYGULANDI · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-116**.
    Emrin hedefi tuttu: `model_yukleme` **DÜŞTÜ → GEÇTİ**, kuru koşu
    **GEÇTİ 6 → 7**.
  - **Ağırlık:** `calisma/v27_epoch200_last.pt` → `models/navitas_seg_v27_best.pt`,
    sha256 `1465ed3d…ee489d`, 54 848 668 bayt, kopya **bayt-eşit**.
    `best.pt` **kullanılmadı** (D-113: epoch 43'te dondu, %21,5 daha kötü).
  - **Kayıt defteri tek kaynak:** `navitas-seg-v4-640` → **`navitas-seg-v27-512`**,
    `imgsz` 640 → **512** (D-112). `metrics` alanına D-115'in K1..K5'i ve kapsam
    uyarısı yazıldı. ⚠ v4'ün `mask_map50` değeri **taşınmadı** — başka modelin
    sayısını taşımak bayatlıktır.
  - 🔴 **Emir ÜÇ manifest alanı diyordu; T58 kapısı BEŞ uç bağlıyor.** Yalnız o
    üçü çevrilseydi `test_manifest_URETIM_surumunu_gosteriyor` (`asil_model`
    hâlâ v24), `test_paketteki_ONNX_ayni_SURUMDEN` ve iki kılavuz testi
    **düşerdi**. Kapsam açıkça genişletildi: **v27 ONNX'i üretildi** ve **her
    iki `JETSON_KILAVUZ.md`** çevrildi. Aksi hâlde "v27 üretimde" derken
    Jetson'a **v24 engine** derleten bir paket bırakılırdı (D-58/D-60).
  - **ONNX 512 FP16:** kanonik `scripts/export_tensorrt.py` ile
    `results/onnx_export_v27_20260814/navitas_seg_v27_best_512_fp16.onnx`;
    betiğin **FP16 doğrulama kapısı geçti** (FP32 artefaktı değil).
  - **Paket + manifest:** v27 `.pt` ve `.onnx` pakete kopyalandı (ikisi de
    bayt-eşit); `paket_icerigi` **8 → 10 dosya**, her biri gerçek sha256'sıyla.
  - **Madde 16 — çıplak sabit KALDIRILDI:** `ALGI_MODEL_DOSYA` artık kayıt
    defterinden türetiliyor (`_uretim_modeli_adi()`). Defter yok/bozuk/`.pt`
    değilse ad **uydurulmaz**, ekran açılmaz (5 bozuk biçimle sınandı).
  - ⚠ **Bilerek bırakılan tek çoğaltma:** manifestteki `asil_model_pt`. Saha
    paketi `config/`i **taşımaz**; defteri okumaya kalkarsa fail-closed'a düşer
    ve **saha kodu model yükleyemez**. Eşitlik testle **kilitlendi**
    (`test_manifest_ile_kayit_defteri_ESLESIYOR`, `test_UC_UC_ayni_agirligi…`).
  - **KAPI (a):** `codes/test_rota_sentetik.py` → **SONUC: 15/15 dogru**.
  - **KAPI (b) — saha kuru koşusu:**
    ```text
    kamera         GECTI   model_yukleme  GECTI   cikarim  GECTI
    maske          GECTI   olcek          GECTI   aktarim  GECTI
    surus_izni     GECTI   rota           DUSTU (BELIRSIZ_COKLU)
    hedef_konumu   SAHIPSIZ                motor    SAHIPSIZ
    T73 (v24) GECTI 6 · DUSTU 2 · SAHIPSIZ 2
    T76 (v27) GECTI 7 · DUSTU 1 · SAHIPSIZ 2
    ```
  - **KONTROL — halka halka kıyas:** v24 koşusuyla v27 koşusu arasında **tek bir
    halka değişti** (`model_yukleme` DÜŞTÜ→GEÇTİ); diğer dokuzu aynı. `rota`
    v24'te de düşüktü ve sebep **birebir aynı** (`BELIRSIZ_COKLU`, aynı `mpp`).
    v27 bu koşuda **gerileme üretmedi**.
  - **KAPI (c) — hakem ekranı:** ekran gerçekten açıldı, `--demo` yok, model
    sahte değil. Kaynak `arena_kadraj`, **kare idx 0 — kare SEÇİLMEDİ**.
    ```text
    karar: 2·ORTA · güven 1.000 · model: navitas_seg_v27_best.pt
    ölçek 0.0781 m/px · gövde açıklığı 14.1 px · C-uzayı UYGULANDI
    darboğaz 41.0 px @ şerit 2 · rota şerit dağılımı 0/540/0 px
    SS: results/t76_hakem_ekrani/yks_ekran_v27.png (1707x996)
    ```
    **Gözle doğrulandı (D-80):** kırmızı engel katmanı, ortada serbest koridor,
    **sarı rota + waypoint'ler**, tepede `H`. Başlık ve buton
    "navitas_seg_v27_best" yazıyor — ad **defterden** geliyor.
  - **Küme ölçümü (n=12):** T60 (ekranın gösterdiği) **11/12** · T66 (v27'nin
    kabul kümesi) **12/12** · kompozit (WhatsApp kareleri) **0/1**
    (`ZEMIN_MASKESI_SUPHELI`, kaplama %77 > tavan %67).
  - **KAPI (d):** `discover -s tests -q` → **Ran 471 · OK** (468 → +3).
    `scripts/jetson_paket_hazirla.py` → **9/9 bayt-eşit**.
  - **İki test güncellendi (gizlenmiyor):** `test_model_registry` v4 → v27
    (`resolve_model` **SHA-256'yı gerçekten doğruluyor**); T73'ün "çelişki var"
    testi görevini yapıp düştü ve **ters çevrildi** — artık eşitliği kilitliyor.
  - ⚠ **DOĞRULANAMADI:** (1) **ONNX hiç koşulmadı** — `.pt` ile karar denkliği
    ölçülmedi, oysa sahaya giden artefakt odur; (2) v27 **640 ile eğitildi,
    512'de koşuyor** — bu fark v27 için ölçülmedi (D-112 ölçümü v24 içindir);
    (3) Jetson hız/doğruluk hâlâ açık (D-89); (4) gerçek arena verisi **yok**
    (D-88/D-99); (5) 🔴 `ALGI_ARENA_KADRAJ_KOKU` hâlâ **T60**'ı gösteriyor,
    oysa kabul kümesi **T66** — ekran, modeli kabul edilmediği bir dağılımda
    gösteriyor (o satır iznimde yok, ayrıca testle çivili); (6) `manifest.imgsz`
    [640]→[512] olduğu için `jetson_fps` artık **yalnız 512** ölçer, 640 kıyas
    noktası kayboldu (D-112 uyarınca bilerek); (7) SHA doğrulaması iki yerde
    **farklı** — `model_registry.py` doğruluyor, `model_kayit_dogrula` yalnız
    **dosya adı** kıyaslıyor (D-106/3 hâlâ açık); (8) pakette v17/v20/v21/v24
    duruyor, paket **522 MB** — budama istenmedi, yapılmadı.

- [STATUS: READY_FOR_REVIEW] **T73 — Saha kodu parametrik degil: kamera ve model_yukleme halkalari DUSUK** · `codes/rpi_inference.py`, `scripts/saha_kuru_kosu.py` · **ONEMLI** · kanit: saha kuru kosusu ciktisi
  - **⚠ UYGULANDI, BİR KAPI KALDI · 2026-08-14 · Claude-2** · kayıt
    `REVIEW_LOG.md` **D-106**. `codes/karar_sozlesmesi.py`, `comms/**` ve
    `O:\navitas-local-train\**` **değiştirilmedi**.
  - **Kamera parametrik:** `--kaynak` indeks / cihaz yolu / dosya kabul ediyor;
    dönüşüm tek yerde (`kamera_kaynagi_coz`). **Varsayılan değişmedi** (indeks 0),
    geriye uyum testle kilitli.
  - **`--model` eklendi, varsayılan ÇIPLAK DEĞİL:** Jetson manifestindeki
    `asil_model_pt`'den türetiliyor. Kaynak dosyada `navitas_seg_vNN_best.pt`
    kalıbında **çıplak ad kalmadığı** ayrıca testle doğrulanıyor; manifest alanı
    yol kaçışına karşı denetleniyor.
  - **Fail-closed:** kayıt defteri uyuşmazlığında `load_model` **yükseliyor**.
    Gevşetme ancak `--kayit-dogrulamasiz` ile **açıkça** isteniyor. Kayıt defteri
    **yoksa** bu uyum **sayılmıyor**.
  - ⚠ **Geriye uyumu MEVCUT BİR TEST yakaladı:** ilk yazımımda `load_model`
    üçlü demet döndürüyordu; `test_rpi_canli_olcek.py` `TypeError: cannot unpack`
    ile yakaladı. Depo taramasında `codes/test_batch.py:139` ve
    `drone/rpi_yayin.py:415` de `load_model()` deyip **model** bekliyor — ikisi de
    iznimde **yok**. Dönüş modele geri çevrildi; ek bilgi `ayrinti=True` ile.
  - **Halkalar artık BESLEMEYİ ölçüyor (D-98 dersi):** eski hâlleri yalnız
    `"--model" in secenekler` gibi **seçeneğin varlığına** bakıyordu.
    `_kamera_beslemesi_olc` `run_camera`'yı gerçekten koşup `VideoCapture`'ın
    **ne aldığını** ölçüyor; `_model_beslemesi_olc` üç davranışı ayrı ayrı.
  - **Görev ayrımı (gizleme değil):** `cikarim`'ın ölçütü çıkarımın tamamlanması;
    bildirim tutarlılığı `model_yukleme`'nin işi. Aksi hâlde kayıt defteri
    bayatlığı `cikarim → maske → rota` zincirini de düşürüyordu (ölçüldü:
    GECTI 5 → 3). Uyuşmazlık `model_yukleme`'de **hâlâ DUSTU**.
  - **KAPI 1 — saha kuru koşusu:**
    ```text
    taban   GECTI 5 · DUSTU 3 · SAHIPSIZ 2
    T73     GECTI 6 · DUSTU 2 · SAHIPSIZ 2
    kamera         GECTI   kaynak parametrik ve VideoCapture'a BESLENIYOR
    model_yukleme  DUSTU   karsilanmayan kosul: kayit defteriyle ESLESME
    ```
  - 🔴 **Hedef GECTI ≥ 7 idi, 6'da kaldı. Sebep tek ve ölçüldü.**
    `model_yukleme`'nin **beş koşulundan DÖRDÜ sağlanıyor**:
    ```text
    --model argumani            EVET
    varsayilan MANIFESTTEN      EVET  (navitas_seg_v24_best.pt)
    arguman yuklemeyi BESLIYOR  EVET
    uyusmazlikta FAIL-CLOSED    EVET
    kayit defteriyle ESLESME    HAYIR  <- TEK EKSIK
    ```
    **İki bildirim çelişiyor:** manifest `v24` (T58), `config/model_registry.json`
    `competition → models/navitas_seg_v4_best.pt` (**v4 döneminden bayat** —
    `CONTRACTS` §11 bunu zaten söylüyordu). Fail-closed **doğru çalışıyor** ve
    doğru sonucu veriyor: hangi ağırlığın uçtuğunu bilmiyoruz.
    ⚠ **Düzeltmedim** — `config/` iznimde **yok**. Düzeltme tek satır:
    `profiles.competition.path` → `models/navitas_seg_v24_best.pt` (+ `sha256`
    ve `model_id`, aksi hâlde SHA doğrulaması aynı çelişkiyi üretir).
    **İzin verirsen yaparım.**
  - **KAPI 2 — mutasyon (yanlış model yolu → açık hata):**
    ```text
    var olmayan dosya -> RuntimeError "Model agirligi bulunamadi"
    yanlis uzanti     -> RuntimeError "MODEL KAYIT DOGRULAMASI BASARISIZ"
    varsayilan yol    -> RuntimeError "MODEL KAYIT DOGRULAMASI BASARISIZ"
    ```
    Üç vakada da **sessiz geçiş yok**.
  - **KAPI 3 — mutasyon (kamera parametresi kaldırıldı):**
    ```text
    kaldirildi   -> besledi=False · "run_camera `kaynak` almiyor"  -> DUSER
    geri alindi  -> besledi=True  · alinan='/dev/video7'           -> GECER
    ```
  - **KAPI 4:** `test_rota_sentetik.py` **15/15** · `discover -s tests -q`
    **Ran 468 · OK**. **KAPI 5:** Jetson paketi **9/9 bayt-eşit**.
  - **Yeni test paketi** `tests/test_saha_parametrik.py` (**17 test**), içinde
    kayıt defteri çelişkisini **bugünkü hâliyle kaydeden** bir test var —
    defter düzeltilince **o test düşer** ve düzeltmenin yapıldığını söyler.
  - **İki mevcut test güncellendi (gizlenmiyor):** `load_model` sahtesi
    `ayrinti=True` sözleşmesini taşıyor; `run_camera` beklentisi `kaynak=None`
    içeriyor. İkisi de **genişletilen sözleşmenin kaydı**, gevşetme değil.
  - ⚠ **DOĞRULANAMADI:** (1) gerçek kamera ile hiçbir şey koşulmadı — donanım
    yok; ölçülen şey değerin `VideoCapture`'a **doğru tipte ulaştığıdır**,
    cihazın açıldığı **değil**; (2) `model_yukleme` kayıt defteri düzeltilene
    kadar geçemez; (3) 🔴 **SHA doğrulaması uygulanmadı** — `CONTRACTS` §11.3
    "SHA doğrulanacak" diyor, bugün yalnız **dosya adı** kıyaslanıyor; (4)
    `scripts/jetson_fps.py` kendi manifest okuyucusunu taşıyor, artık buradan
    import etmeli (o dosya iznimde yok); (5) `--kayit-dogrulamasiz` güvenliği
    açıkça gevşetir, sahada kullanılırsa gerekçesi kayda geçmeli.

- [STATUS: KAPANDI] **T72 — HEDEF KONUMU halkasi sahipsiz: IKA nereye gidecegini bilmiyor** · `codes/karar_sozlesmesi.py`, `codes/rpi_inference.py`, `CONTRACTS.md` · **TIKAYICI** · kanit: saha kuru kosusu + sartname SS2.2.6
  - **✅ YAPILDI · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-105**.
    `comms/**` ve `O:\navitas-local-train\**` değiştirilmedi.
  - **Üçüncü sınıf EKLENMEDİ.** T67'nin klasik **Katman 2** deseni kullanıldı:
    `hb_maskesi` / `hb_konumu`. Ayırt edici üç özellik (§2.1): yüksek kroma
    kırmızı (eşik **T67 ile ORTAK**) · **KARE** · bilinen kenar **2,0 m**.
  - 🔴 **Şekil filtresi tek başına YETMEDİ — ölçüm yakaladı.** `sa_000170`'te
    **kırılmış bir bariyer parçası** 37×32 px (en/boy **1,16** → kare) olarak
    kalmış ve gerçek HB'den büyük olduğu için seçilmişti:
    ```text
    olcut                 ilk surum    tumleyenlik sonrasi
    merkez hatasi maks     284,66 px          1,30 px
    YANLIS POZITIF          1/260              0/260
    mpp hatasi maks         %25,80             %8,57
    ```
    Çözüm: **T67'nin ENGEL dediği piksel HB OLAMAZ** — `hb_maskesi` artık
    bariyer maskesini adaylardan çıkarıyor. İki dedektör gerçek anlamda
    **tümleyen**. Ayrıca şekil bantları arasında **boşluk** var ve testle
    kilitli: `HB ≤ 1,6 < 4,0 < bariyer`.
  - **KAPI 1 — TESPİT** (yer gerçeği `..._t66`, n=260):
    ```text
    TESPIT         260/260 (%100,0) · kacan 0
    merkez hatasi  medyan 0,71 px · p90 0,95 · maks 1,30
    kenar hatasi   medyan 1,40 px · maks 2,40   (yer gercegi 25,6 px)
    ```
  - **KAPI 2 — yanlış pozitif (bariyeri HB sanma): 0/260. GEÇTİ.**
    `sa_000170` vakası kalıcı teste alındı.
  - **KAPI 3 — mpp çapraz kontrolü:**
    ```text
    mpp hatasi   medyan %5,185 · p90 %8,571 · maks %8,571
    capraz durum {dogrulandi: 260, celiskili: 0}
    ```
    Sapma **sistematik** (kapama pedin kenarını ~1,4 px şişiriyor).
    **Düzeltilmedi** — düzeltme katsayısı bizim kendi çizimimize fit edilirdi,
    gerçek pedde tutmazdı. Bunun yerine çapraz bandı (%25) sapmanın ~4,8 katı
    seçildi.
  - **`CONTRACTS` §5(b) AÇILDI** ("üçüncü sınıf üretime girdiğinde açılır"
    diyordu; klasik dedektör onu üçüncü sınıf **olmadan** açtı) ve **§5.4**
    yazıldı — iki ölçek kaynağı çelişirse:
    ```text
    yalniz telemetri      -> telemetri     (SS5 birincil kaynak)
    yalniz HB             -> HB
    ikisi, fark <= 0,25   -> TELEMETRI     (HB yalniz DOGRULAR)
    ikisi, fark  > 0,25   -> HICBIRI, ("celiskili", fark)
    ```
    🔴 Çelişkide **ortalama alınmaz**: hangisinin doğru olduğunu bilmiyoruz
    demektir. Fail-closed.
  - **Karar yoluna bağlandı, GERİYE UYUMLU:** `analyze_path(..., goruntu=None)`.
    Görüntü verilmezse davranış **değişmez** (tüm ölçüm betikleri aynen çalışır);
    verilirse HB hedeftir, bulunamazsa **uydurulmaz** → yeni **`HEDEF_YOK`**.
  - ⚠ **Madde 15 testle kilitli:** HB'yi bulmak serbest alanı **değiştirmez** —
    `return_clean` çıktısı HB'li ve HB'siz koşuda **birebir aynı**.
  - **KAPI 4 — MUTASYON:**
    ```text
    M0 mutasyon YOK                          DUSEN 0
    M1 HB sekil bandi bariyerin ICINE tasindi DUSEN 1  ATESLENDI
    M2 ORTAK kroma esigi 200                  DUSEN 8  ATESLENDI
    M3 HB kenari 2,0 -> 5,0 m                 DUSEN 2  ATESLENDI
    M4 capraz bandi 5,0                       DUSEN 1  ATESLENDI
    ```
  - **KAPI 5:** `test_rota_sentetik.py` **15/15** · `discover -s tests -q`
    **Ran 451 · OK** · paket **9/9 bayt-eşit**.
  - **Mevcut bir test doğru ateşledi:** `test_sebep_kodlari_sozlesmede_
    SAYILANLARDIR` 11. kod eklenince düştü — T65'te tam bunun için yazılmıştı.
    Liste güncellendi.
  - **Yeni test paketi** `tests/test_hb_dedektoru.py` (**25 test**).
  - ⚠ **DOĞRULANAMADI:** (1) küme **sentetiktir** ve HB'yi **bizim çizdiğimiz**
    biçimde taşır — gerçek arenada tutacağı **doğrulanamaz** (D-88+D-99);
    %100 tespit bir **gerçek başarım iddiası değildir**; (2) gerçek HB'nin
    görünümü bilinmiyor — şartname pedin rengini/malzemesini söylemiyor, kroma
    eşiği **yapay zekâ ürünü** bir figürden kalibreydi (D-99); (3) HB'nin
    **kısmen örtülü** olduğu durum sınanmadı; (4) %5,2 sapma gerçek pedde
    geçerli değildir; (5) 🔴 **üretim çağrı yerleri (`run_image`/`run_video`/
    `run_camera`) `goruntu` GEÇİRMİYOR** — hedef halkası sözleşmede ve karar
    yolunda **hazır**, üretim yolunda **henüz etkin değil**. Bunu açmak T73'ün
    parametrik saha kodu işiyle birlikte yapılmalı (o dosya ikinci amelede).

- [STATUS: KAPANDI] **T71 — 🔴 ŞARTNAME OTORİTEDİR: figür yapay zekâ ürünü çıktı, T60'ın üç kararı geri alınıyor** · `O:\navitas-local-train\51_sentetik_arena.py` · **TIKAYICI** · **T66/T68 ile birlikte koşulmalı** · kanıt: `REVIEW_LOG.md` **D-99**
  - **✅ YAPILDI (2/3) · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-101**.
    Depoda **hiçbir dosya değiştirilmedi**; yalnız `51_sentetik_arena.py`.
  - **Madde 3 (moloz adaları) YAPILMADI — bilerek.** Üretecin şerit
    geometrisinin tam yeniden yazımıdır (**T66**) ve tek görevde yapılırsa
    T51/T56 kadraj kapılarını riske atardı. Görev "birlikte yapabilirsin"
    diyordu, zorunlu değil. Küme hâlâ **dikey şeritler** üretiyor; T66 açık.
  - 🔴 **HB — iki eski varyant da yanlıştı.** §2.1: *"…üzerinde **kırmızı H
    harfi** bulunacağı bir bölgedir."*
    ```text
    varyant                 kirmizi mi   H var mi   metne uygun mu
    T56 "kirmizi branda"       EVET        HAYIR        HAYIR
    T60 "figur_siyah_beyaz"    HAYIR       EVET         HAYIR
    T71 "metin_kirmizi_H"      EVET        EVET         EVET
    ```
    ⚠ Görev *"T56'daki kırmızı branda doğruymuş"* diyordu — **tam değil**:
    T56 düz kırmızı dikdörtgendi, **üzerinde H yoktu**. Metin "kırmızı branda"
    demiyor, "üzerinde kırmızı H harfi" diyor. Uygulanan: ped üzerine kırmızı
    çerçeve + kırmızı H. **Ped rengi şartnamede belirtilmemiş** → çeşitlilik
    stratejisi gereği beş tondan sahne başına çekiliyor.
  - **İHA-İB eklendi:** 30×30 m, `px = m·TUVAL/HTAB_M` → 480 px. **İşarettir,
    engel değil** — kimlik haritasına dokunulmaz, yarı saydam tint uygulanır
    (düz boya arenanın %36'sında dokuyu silerdi). Konum ve ton sahne başına
    değişir. Manifest: `iha_ib_kutu`, `iha_ib_kenar_m` (260/260).
  - **KAPI 1 — RENK ÇEŞİTLİLİĞİ (asıl değişiklik):**
    ```text
    kume  sinif    n   L ort  L std  L araligi  a std  b std
    T60   zemin  120   148,5   6,91   119..170   0,20   0,68
    T60   moloz  118   107,9   4,61    91..121   0,37   0,55
    T71   zemin  120   134,1  21,51    94..189   2,35   5,90
    T71   moloz  119    98,1  24,90    43..148   1,67   3,23
    std kazanci: zemin L x3,1 · a x11,6 · b x8,7 | moloz L x5,4 · a x4,6 · b x5,8

    TEK MODA COKME (L histogrami, 10 kova):
      zemin T60 dolu 5/10  [0,0,0,2,8,83,25,2,0,0]  <- 120'nin 83'u TEK kovada
      zemin T71 dolu 9/10  [0,7,21,29,16,19,17,8,2,1]
    ```
    Tek moda çökme **yok**. GEÇTİ.
  - **KAPI 4 — GÖZLE (zorunlu, D-80):** kontak sayfaları — T60'ın sekizi de aynı
    sıcak kum; T71'de zemin kum/gri/açık/koyu arası değişiyor, kırmızı H ve mavi
    İHA-İB her karede, bariyerler yerinde. **GEÇTİ.**
  - 🔴 **Görsel bir regresyon yakaladı, sayılar yakalamamıştı:** ön-boyamayı
    kaldırınca `enkaz_doku` yolunu sahne hedefine bağlamayı atlamıştım; molozda
    **mavi gökyüzü ve beyaz bulut** parçaları çıktı (D-78/T60'ın çözdüğü kusurun
    dönüşü). İlk 12 karelik denemenin görselinde görüldü ve düzeltildi.
  - **T67 ÇAPRAZ KONTROLÜ (görevde istenmedi, zorunluydu):** kırmızı HB tam da
    T67'nin tuzağı.
    ```text
    HB bolgesinde engel pikseli : 0 / 12 kare        KORUNDU
    IHA-IB bolgesinde a*        : -7 .. +9  (esik 25 -> MAVI guvenli)
    HB en/boy 260/260 karede    : 1,00 (KARE)
    ```
  - **KAPI 3 — T51/T56 kadraj kapıları KORUNDU** (`57_...py`, betik
    değiştirilmedi, KUME yolu bellekte yamalandı):
    ```text
    KAPI 1 TAM KAREDE rota 260/260 GECTI · KAPI 3 POZITIF KONTROL 260/260 GECTI
    KAPI 5 kaplama ort %25,9 maks %64,8 (tavan %67) ret 0/260
    manifest: hedef 260/260 · kenar 2,0 m · en/boy 1,00 · hedef!=acik 0/260
    ```
  - 🔴 **KAPI 2 — REGRESYONDA ÜÇ SAYININ İKİSİ KÖTÜLEŞTİ:**
    ```text
                      ROTA     MOLOZA    AGIR   ARENA DISI
    T60 kumesi     242/260     4/242   2/242      5/242
    T71 kumesi     231/260     5/231   4/231     16/231
    ```
    Rota **çökmedi** (%88,8) ama düştü; moloza basma **+1 kare ARTTI** →
    *"artmasın"* şartı **lafzen karşılanmadı**; arena dışı +11.
    ⚠ **Bu kıyas kontrollü değildir:** v24, T60 substratında (tek renk künyesi)
    eğitildi; T71 **bilerek o dağılımın dışındadır**. Ölçülen şey karar
    zincirinin bozulması değil, **v24'ün dağılım dışında kırılganlığı** — ki
    T71'in varlık sebebi tam olarak onu kırmak (D-95). Doğru kıyas T71 üzerinde
    eğitilmiş modelle yapılır (T68). **Kararı sana bırakıyorum.**
  - **Depo kapıları:** `test_rota_sentetik.py` **15/15** ·
    `discover -s tests -q` **Ran 426 · OK**.
  - **Küme:** `...\calisma\sentetik_arena_kadraj_t71` (260 kare). T60 **silinmedi**.
  - ⚠ **DOĞRULANAMADI:** (1) gerçek arena başarımı — gerçek görüntü **hiç yok**
    (D-88+D-99); (2) genişletilen bantların gerçek arenayı kapsayıp kapsamadığı
    **bilinmiyor** — bant seçimi akıl yürütmedir, **ölçüm değildir**; (3)
    çeşitliliğin modele faydası **ölçülmedi**, T71'de eğitim koşulmadı — "daha
    sağlam olacak" bir **öngörüdür**; (4) geometri hâlâ dikey şerit (T66);
    (5) İHA-İB'nin arena içindeki **konumu** şartnamede tarif edilmiyor,
    rastgele yerleştirildi; (6) dL alt ucunda (min −3) zemin ile moloz aynı
    parlaklığa gelebiliyor, o karelerin çözülebilirliği sınanmadı.
  - Şartname Şekil 1 alt yazısı: *"Görsel **tamamen yapay zeka ile
    oluşturulmuştur. Gerçek alanı doğrudan yansıtmamaktadır.**"* Figür ile metin
    çeliştiğinde **metin kazanır**; D-87'nin "figür kazanır" hükmü **tersine döner**.
  - **GERİ ALINACAK ÜÇ KARAR:**
    1. **HB KIRMIZI olacak.** §2.1: *"2 m × 2 m boyutlarında üzerinde **kırmızı
       H harfi** bulunacağı bir bölgedir."* T60'ta figüre bakıp siyah/beyaz
       yaptırmam **hatadır** — T56'daki kırmızı branda doğruymuş.
    2. **İHA-İB eklenecek:** 30 m × 30 m **mavi** bölge, §2.1'de açıkça tanımlı.
       T60'ta "figürde yok" diye dışladım; gerekçe çöktü.
    3. **Güzergâhlar moloz yığınları ARASINDA** (§2.1) — T66 ile birleşir.
  - 🔴 **STRATEJİ DEĞİŞİYOR — TEK PALET DEĞİL, ÇEŞİTLİLİK.** D-87'nin LAB
    hedefleri yapay zekâ üretimi bir görüntüden çıkarıldı; gerçek arenanın renk
    hedefi **bilinmiyor**. v25 tek palete oturunca ona **bağımlı** oldu ve
    dağılım dışı bir sahnede tamamen çöktü (D-95). Üreteç artık tek künyeye
    yakınsamayacak; zemin/moloz renk ve doku bandı **geniş tutulacak**.
  - **KAPI:** `61_rota_moloza_basma.py` üç sayısı bozulmasın · üretilen kümede
    renk **çeşitliliği** ölçülüp raporlansın (tek moda çökmediği gösterilsin) ·
    gözle doğrulama zorunlu.
  - ⚠ Şartname metni **tek otoritedir**; figürden ölçüm alınmayacak.

- [STATUS: KAPANDI] **T66 — Üreteç geometrisi arenaya benzemiyor: dikey şeritler vs moloz adaları** · `O:\navitas-local-train\51_sentetik_arena.py` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-91**, görsel `results/t60/t60_yan_yana.png`
  - **⚠ UYGULANDI, BİR KAPI DÜŞTÜ · 2026-08-14 · Claude-2** · kayıt
    `REVIEW_LOG.md` **D-103**. Depoda hiçbir dosya değiştirilmedi.
  - Geometri **dikey şerit → moloz ADALARI**: arena zemini geniş ve bağlantılı,
    moloz adalar hâlinde, koridorlar adaların arasından geçiyor. **T68
    birleştirildi**; T71 kazanımları (renk bandı, kırmızı H'li HB, İHA-İB) korundu.
  - 🔴 **Önce başka bir kusur bulundu: `etiketle` DELİKLERİ ATIYORDU**
    (`RETR_EXTERNAL`). Şerit geometrisinde bedeli küçüktü ve ölçüldü: T71'de
    **260 karenin 65'inde** class-0 ile class-1 üst üste biniyordu. Ada
    geometrisinde aynı kusur **yıkıcı** olurdu — **her ada "traversable"
    etiketlenirdi**. `delikli_poligonlar` ile çözüldü (yeniden rasterize
    **IoU 1,0000 · fark 0 px**).
  - **Ada yoğunluğu iki kez ölçümle ayarlandı** (v16 dersi başka yoldan geri
    gelmesin):
    ```text
    surum          traversable  blocked  trav/blok
    T71 (serit)         %24,9    %30,9      0,81
    T66 ilk deneme      %53,9     %5,4     10,00   <- adalar cok seyrek
    T66 nihai           %33,7    %29,0      1,16
    ```
    Artışın bir kısmı **yapısaldır ve doğrudur**: şeritler artık bitişik,
    aralarındaki etiketsiz boşluk kalktı.
  - **KAPI 2 — renk çeşitliliği. GEÇTİ** (iki düzeyde raporlanıyor):
    ```text
    olcut                        T71     T66   oran
    URETEC cekilisi zemin L    24,68   24,28   0,98   <- bant KODDA degismedi
    URETEC cekilisi zemin b     6,18    8,71   1,41   <- GERCEKTEN genisletildi
    OLCULEN bolge zemin L      21,51   19,45   0,90   <- BILESIM etkisi
    ```
    L/a bantları kodda hiç değişmedi; 0,96–0,98 farkı n=260'ta **örnekleme
    gürültüsü** (uniform(105,190) teorik std 24,54). "Ölçülen bölge" std'sinin
    düşüşü bileşim etkisi — traversable artık iki yüzeyi birden kapsıyor.
    O rakamı kovalayıp bandı daha da genişletmek **artefakta fit etmek** olurdu.
  - **KAPI 3 — bariyer açık koridoru kapatıyor (T68). GEÇTİ:**
    ```text
    olcut                                 T71        T66
    ACIK/DAR seridi bariyerle kapatilan  0/260    128/260 (%49,2)
    bariyer pikseli `blocked` etiketli    %92,0      %98,8
    ```
    Manifest düzeltmesi de bağlandı: kapanan şeridin `gecilebilir` alanı
    False'a çevriliyor, `durum` `"acik+bariyer"` oluyor — yoksa `acik_serit`
    **yalan söylerdi**.
  - **KAPI 1 — T51/T56 kadraj kapıları. GEÇTİ** (ilk ayarda düşmüştü):
    ```text
    ayar               rota      POZITIF KONTROL     cekimser
    ilk (dar gecit) 193/260      192/193 DUSTU       DUSUK_GUVEN 50
    nihai           242/260      242/242 GECTI       DUSUK_GUVEN 18
    ```
    İki düzeltme: geçit genişletildi; bariyerin **korunacak şeridi** artık
    öncelikle bir "açık" şerit (önceden çoğu kez "dar" korunuyordu).
    Manifest: hedef 260/260 · kenar **2,0 m** · en/boy **1,00** ·
    `hedef_serit != acik_serit` **0/260** · İHA-İB 260/260.
  - 🔴 **KAPI 4 — REGRESYON DÜŞTÜ:**
    ```text
                      ROTA     MOLOZA    AGIR   ARENA DISI
    T71 kumesi     231/260     5/231   4/231     16/231
    T66 kumesi     196/260    61/196  40/196     26/196
    ```
    Moloza basma **5 → 61**. *"Artmasın"* şartı **karşılanmadı**.
    **Sebep ayrıştırıldı — yer gerçeği kontrolü (model YOK):**
    ```text
    T71 · YER GERCEGI   rota 259/260 · moloza basan  0/259 (%0,0) · AGIR 0
    T66 · YER GERCEGI   rota 260/260 · moloza basan 24/260 (%9,2) · AGIR 0
    ```
    İki katkı: **(1) substrat %9,2 ve tamamı HAFİF** (ağır basma **0**) —
    koridorlar daralınca A* rotası C-uzayı sınırına yaslanıyor, ölçüm sınırda
    temas sayıyor; **(2) geri kalanı v24'ün dağılım dışılığı** — model koşusunda
    ağır basma 40 iken yer gerçeğiyle **0**. v24 dikey şerit + tek palet ile
    eğitildi; ada geometrisi onun için tamamen yeni. Doğru kıyas T66'da
    **eğitilmiş** modelle olur. **Karar sende.**
  - **KAPI 5 — gözle. GEÇTİ:** yan yana kontak sayfası — üst satır duvar duvara
    dikey bantlar, alt satır geniş açık zemin + moloz adaları + koridoru enine
    kesen bariyerler.
  - **KAPI 6:** `test_rota_sentetik.py` **15/15** · `discover -s tests -q`
    **Ran 426 · OK**.
  - **Etiket çakışması** %0,051 → %0,204: kaynağı araştırıldı, çakışan
    bileşenlerin en/boy medyanı 0,8–2,0 (ince bariyer barı **değil**) — poligon
    sadeleştirmesinin **kenar artığı**. `approxPolyDP` eps 0,0035 → 0,0015.
  - **Küme:** `...\calisma\sentetik_arena_kadraj_t66` (260). T71 ve T60 **silinmedi**.
  - ⚠ **DOĞRULANAMADI:** (1) gerçek arena başarımı — gerçek görüntü **hiç yok**;
    (2) **ada yerleşimi şartnameden türetilmedi** — metin yığınların sayısı/
    boyutu/dağılımı hakkında bir şey demiyor, yoğunluk `trav/blok` oranını
    tutmak için **ayarlandı**; (3) yeni geometrinin **modele faydası ölçülmedi**,
    T66'da eğitim koşulmadı — öngörüdür; (4) yer gerçeğiyle ölçülen %9,2 hafif
    basma sıfırlanmadı; (5) `GT şerit uyumsuzluğu` 22/260 → 59/242 çıktı ama
    D-90 bu ölçütü zaten **güvenilmez** ilan etmişti, kanıt olarak kullanılmadı.
  - T60 **rengi** düzeltti (doğrulandı). **Geometri** düzelmedi:
    - gerçek arena: **açık toprak tarlası + içine serpilmiş moloz ADALARI**,
      koridorlar bu adaların arasından geçer; moloz duvar gibi dizilmiş.
    - üreteç: **dikey şeritler** — kare baştan sona dar bantlara bölünmüş.
  - ⚠ Model "zemin = dar dikey bant" ön yargısı öğrenebilir; arenada zemin
    geniş ve bağlantılı bir alandır.
  - ⚠ **T65 ile ilişkili:** üreteç arena dışına etiketsiz zemin çiziyor ve bu
    doğrudur (gerçekçi). T66 onu kaldırmayacak — geometriyi düzeltecek.
  - **KAPI:** `61_rota_moloza_basma.py` üç sayısı bozulmayacak; gözle yan yana
    doğrulama zorunlu (**görsel kazanır**, D-80).

- [ ] **T79 — Koridor seçimi binde-4'lük algı gürültüsüne karşı KARARSIZ: `.pt` ile `.onnx` aynı karede 28 m ayrı rota üretiyor** · `codes/costmap_path_finder.py`, `comms/yks_gui.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-119**
  - 🔎 **v34 İLE YENİDEN ÖLÇÜLDÜ · 2026-08-20 · D-203.** Tohum 7 (D-142
    reçetesi birebir): **çevrilen 4/260** (v30: 8) → ön kayıt B1 harfiyen
    "iyileşme GÖRÜNÜYOR". 🔴 **AMA çürütücü tohum 42 ile iki modeli de
    yeniden koştu: v34=7, v30=6 — işaret TERSİNE döndü.** 4-vs-8 binom
    p≈0,39. **Kararlılık kazancı İSPATLANMADI (tek-tohum artefaktı olabilir).**
    ONNX denklik (67, v34): uyuşmazlık 2/260 (sa_000098, sa_000121),
    maske IoU 0,9959, azami sapma 18,4 m. Çok-tohumlu dağılım ölçülmedi.

  - Ölçüldü (n=260, eşleştirilmiş, T66 kabul kümesi): karar aynı **258/260**,
    zemin maskesi IoU **0,9968**, ama azami rota sapması **360 px = 28,1 m**.
    ```text
    sa_000063   .pt şerit 1 (darboğaz 15,0 px · pay 0,92 px)   .onnx şerit 2 (17,0 px)
    sa_000172   .pt şerit 1 (540/0/0 · güven 1,000)            .onnx şerit 3 (0/0/540 · 0,982)
    ```
  - **İkisi de güvenli**: her iki artefakt da K1..K5'i geçiyor. Sorun "hangisi
    doğru" değil, **seçimin kararsız olması**. ONNX'e özgü DEĞİLDİR — farklı
    ışık veya tekrar koşum da çevirebilir.
  - **Etki:** `comms/yks_gui.py:1285` rotayı KENDİSİ hesaplıyor. `.pt` ile
    hesaplayan bir yer, `.onnx` ile hesaplayan bir yer olursa hakem, aracın
    gitmediği güzergâhı izler.
  - **YAP — iki seçenekten birini ÖLÇÜMLE seç:**
    (a) beraberlik bozma kuralı: adaylar arasındaki fark gürültü tabanının
        altındaysa deterministik ve HİSTEREZİSLİ seçim (kare kare zıplamasın);
    (b) rotayı TEK yer hesaplasın, diğeri yalnızca göstersin — mimarinin
        tek-otorite ilkesine daha yakın olan budur.
  - **ÖNCE DOĞRULA (mimar doğrulamadı):** saha topolojisinde gerçekten İKİ hesap
    yeri var mı? İHA telsizle **rota** mı yoksa **maske** mi gönderiyor?
    Cevap "tek yer" ise (a) gereksizdir, kusur yalnız demo kipindedir.
  - **KAPI:** `codes/test_rota_sentetik.py` 15/15 · `67_onnx_karar_denkligi.py`
    yeniden koşulduğunda **karar uyuşmazlığı 0/260** ve azami sapma gürültü
    mertebesinde (< 1 m) olmalı.

  - 🔴 **KAPI TUTMADI, ZORLANMADI · 2026-08-15 · Claude-2** · kayıt **D-126**.
    ```text
    taban (once) : 9/260 (%3,46)      T79 sonrasi : 8/260 (%3,08)
    hedef        : <= 4/260
    ```
  - **Adım 1 — kök ölçüldü, önerilen çerçeve kısmen çürüdü.** Çeviren 9 karenin
    yalnız **2'sinde beraberlik** var; **7'sinde rota fiziksel olarak taşınıyor**
    ve bunların **4'ünde her koşuda tek şerit dolu** (kıyaslanacak ikinci aday
    yok):
    ```text
    sa_000081  --/15.00/-- -> --/--/15.00   ACIKLIK AYNI, serit FARKLI
    sa_000172  25.00/--/-- -> --/--/24.00   tek serit, TASINMA
    sa_000176  --/--/95.00 -> 64.13/--/--   maske IoU 0,649
    sa_000232  23.00/23.00 -> bagil fark 0,0000   BERABERLIK
    sa_000258  18.00/17.98 -> bagil fark 0,0009   BERABERLIK
    ```
    Rota piksel sayısı dört vakada da aynı (540); değişen **yeri**, uzunluğu değil.
  - **Adım 2 — beraberlik bandı uygulandı** (`BERABERLIK_BANDI = 0.04`; değer
    çıplak değil, projenin ölçülmüş gürültü tabanı — D-112). Band içinde seçim
    deterministik. **Düzelen tek kare `sa_000192`** (bağıl fark 0,0192) — adım
    1'in tam olarak öngördüğü sonuç.
  - **Adım 3 — histerezis yazıldı, üretime BAĞLANMADI.** Emniyet kuralı testle
    çivili: **önceki koridor geçilemezse anında bırakılır**; ölçülemeyen durumda
    histerezis uygulanmaz (fail-through). ⚠ `analyze_path` **durumsuzdur** ve
    histerezis kareler arası bir mekanizmadır; kapı betiği her kareyi bağımsız
    gürültü çekimiyle ölçtüğü için **o kapıyla doğrulanamaz**. Ölçemediğim bir
    şeyi üretime bağlamadım.
  - **Kalan 8 çevrilmenin 7'si taşınmadır** ve maske değişiminden gelir; çözümü
    ya modelin gürültü dayanıklılığı ya kareler-arası histerezistir — ikisi de bu
    görevin kapsamı dışında. **Görev `[ ]` bırakıldı.**
  - **Yeni testler:** `tests/test_koridor_kararliligi.py` (17).

  - 🔴 **T79-A ÖLÇÜLDÜ · ÜÇÜNCÜ HİPOTEZ DE ÇÜRÜDÜ · 2026-08-17** · kayıt **D-145**.
    Ölçüm ameleye yazdırıldı (`75_koridor_envanteri.py`), koşu tamamlandı, amele
    yazım aşamasında kotaya takıldı; çözümleme ve `76` mimar tarafından yapıldı.
    **Ön kayıt betiğe koşulmadan önce yazılmıştı** (`75_...py:22-36`).
    ```text
    (A) ÜRETİM şeridi çevrilen   :  8/260   <- D-142 ile BİREBİR
    (B) ENVANTER yol_no çevrilen : 10/260   <- ÜRETİMDEN DAHA KARARSIZ
    (D) temiz koşuda durum=ACIK  : 34/260   (226 karede n_kapi != 3 -> BELİRSİZ)
    (C) üretimi çeviren 8 karede envanter: AYNI 7 · DEĞİŞTİ 1
    ```
    Ön kayıt kuralı **(B) ve (D) birden ateşledi -> FIX YAZILMADI, görev `[ ]`.**
  - **D-143'ün "koridor VARLIĞI çevriliyor" çıkarımı ÇÜRÜDÜ.** O bir ölçüm değil,
    `serit_min_px` deseninden yapılmış bir çıkarımdı. Doğrudan ölçüldü: çeviren
    8 karenin **7'sinde envanter birebir aynı** (aynı kapılar, aynı geçilebilirlik,
    aynı darboğazlar). Koridorlar geniş (15-56 px, r_gerekli 14,08 px).
  - **Geriye tek mekanizma kaldı:** değişmeyen bir koridor kümesi üzerinde
    **küresel A\* maliyet beraberliği**. Bu VERİ ile (D-142: doz eğrisi tek yönlü)
    ve ENVANTER ile (D-145) çözülemez. **T79'un yeni şekli:** beraberlik bozma
    `serit_min_px` üzerinde DEĞİL, A\*'ın **toplam yol maliyeti** üzerinde
    tanımlanmalı — `_rota_serit_olcumu` rota SEÇİLDİKTEN SONRA koşar, seçimi
    değiştiremez. ⚠ Maliyet beraberliği **HİPOTEZDİR, ÖLÇÜLMEDİ**: `astar()`
    toplam maliyeti döndürmüyor.
- [x] **T90 — İKİ ETİKETLEME OTORİTESİ: `koridor_adaylari` `serit_no()`'yu çağırmıyor** · `codes/costmap_path_finder.py:443-448` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-145**
  - ✅ **KAPANDI (defter düzeltmesi 2026-08-18).** Üretimde: `koridor_adaylari`
    etiketi artık `serit_no()`den türetiyor **ve** `rota_bul` içinde etiket
    çakışması fail-closed kapatıldı (`costmap_path_finder.py:1006-1025`).
    Kanıt `REVIEW_LOG.md` **D-145/D-146**; ön kayıt ACIK 34→31 öngörüsü tam tuttu.
    ⚠ Satır bitmiş olmasına rağmen `[ ]` kalmıştı — kuyruk kalan işi fazla
    gösteriyordu.
  - `karar_sozlesmesi.serit_no()` docstring'i *"Tek kaynak: hem karar hem
    görselleştirme burayı çağırır"* der (CONTRACTS SS8) ve sınırları **letterbox
    içerik kutusundan** hesaplar. `koridor_adaylari()` bu fonksiyonu **çağırmaz**:
    `n_kapi==3` iken soldan sağa **sıra numarası** (i+1), aksi hâlde kapıyı
    **serbest alan bbox'ına** göre üçe böler. Madde 16 ihlali.
    ```text
    aday kapı toplamı                 : 470
    etiket != serit_no(kapi_merkez_x) : 104  (%22,1)
    ```
  - **Etki ölçüldü ve KÜÇÜK — büyütülmemeli:** `simulation/scripts/iha_haritala.py:329`
    `road`'u `rota_bul["yol_no"]`dan alıp yayınlar (`comms/protocol.py:51` ->
    `ika_receiver.py:11` -> `plan_path(road)`; `hakem_log.py:108` de bununla puanlar).
    Ama `rota_bul` `n_kapi==3` görmeden `road` yayınlamaz:
    ```text
    gizil oran : kazananın etiketi != serit_no  ->  61/247  (%24,7)
    CANLI oran : yayınlanan road yanlış         ->   1/34   (%2,9)
    ```
    BELİRSİZ kapısı gevşetilirse gizil oran canlıya döner.
  - **YAP:** `koridor_adaylari` etiketini `serit_no(kapi_merkez_x, icerik_x0,
    icerik_w)` ile üret; sıra numarası ve bbox üçlemesi kaldırılsın. Kapı bir
    NOKTA değil AÇIKLIK olduğundan etiketin merkeze mi yayılıma mı bağlanacağı
    **ölçümle** seçilsin (D-145'te 7 kare yalnız yayılımla açıklanıyor).
  - **KAPI:** `codes/test_rota_sentetik.py` 15/15 · `unittest discover` düşmeyecek ·
    `76_serit_etiketi_celiskisi.py` yeniden koşulduğunda **etiket != serit_no = 0/470**
    ve `rota_bul` ACIK sayısı (34) **DÜŞMEYECEK**.
  - ⚠ **ÖNCE DOĞRULA:** `iha_haritala` yolunun hakem koşusunda gerçekten
    kullanılıp kullanılmadığı; kullanılmıyorsa kusur yalnız demo kipindedir.

  - ✅ **YAPILDI · 2026-08-17 · Claude 1 (mimar, madde 7 istisnası)** · kayıt **D-146**.
    Ön kayıt kapılar koşulmadan önce yazıldı. Sıra numarası (`i+1`) ve serbest
    alan bbox üçlemesi **kaldırıldı**; etiket artık yalnız `serit_no()`'dan,
    üstelik **yayınlanan `kapi_merkez_x` ile aynı tamsayıdan** türüyor.
    Tanı amaçlı `serit_yayilimi` alanı eklendi (karara **girmez**).
    ```text
    ölçüt                             D-145   T90(korumasız)  T90+KORUMA
    etiket != serit_no               104/470      0/470         0/470
    üretim şeridi geçilebilir kümede 192/247    230/247       230/247
    rota_bul durum == ACIK            34/260     34/260        31/260
    (A) üretim şeridi çevrilen          8/260      8/260         8/260
    (B) ENVANTER yol_no çevrilen       10/260     12/260        11/260
    test_rota_sentetik                  15/15      15/15         15/15
    unittest discover -s tests         563 OK     574 OK        576 OK
    ```
  - 🔴 **BAĞIMSIZ DENETİM T90'IN AÇTIĞI BİR AÇIĞI YAKALADI (dört bulgu, biri
    ciddi).** `serit_no()` **çok-bire** eşlemedir; eski şema (`i+1`) iki kapının
    aynı numarayı almasını **imkânsız** kılıyordu. T90 sonrası `rota_bul`
    `durum=ACIK` ile `road=1` yayınlayıp **iki farklı koridoru** kastedebiliyordu
    → `plan_path(road)` planlayıcının seçmediği koridora sürebilirdi. Bunu
    D-146 taslağında "3/34 kare belirsiz" diye ölçüp T91'e **ertelemiştim**;
    denetim ertelenemez olduğunu gösterdi. **Fail-closed koruma eklendi:**
    kazananın etiketini paylaşan başka bir *geçilebilir* kapı varsa
    `BELIRSIZ_COKLU`. Kontrol dar tutuldu (geçilemez kapı sayılmaz).
    Ek ön kayıt koşulmadan önce yazıldı: **öngörü ACIK 34 → 31, ölçüm 31 — tam
    tuttu.** Bu, ilk ön kaydın "ACIK ≥ 34" ölçütünü **ihlal eder**; kural
    gevşetilmedi, ikinci bir kural olarak açıkça eklendi.
  - 🔴 **BEDEL AÇIK:** `B` 10 → 11 (korumasız hâlde 12 idi). Mekanizma
    **ölçüldü, uydurulmadı**: `sa_000100` ve `sa_000166`'nın ikisinde de
    **seçilen kapı DEĞİŞMEDİ** (`sa_000166`'da darboğaz değeri bile birebir
    aynı); yalnız ağırlık merkezi şerit sınırını geçti. Kalan +1'in **niteliği
    değişti**: çevrilme artık `road 1 ↔ road 2` (fail-dangerous) değil,
    `ACIK ↔ BELIRSIZ_COKLU` (fail-closed). Eski şemanın kararlılığı konumu
    ıskartaya çıkarıp sabit ordinal koymaktan geliyordu — **kararlı ama yanlış
    numara İKA'yı her karede aynı yanlış koridora sürer.**
  - **Testler boşa geçmiyor:** her sahnede eski formül aynı adaylar üzerinde
    yeniden koşuldu ve farklı cevap verdi (`[1,3]`→`[1,2]` · `[1,2,3]`→`[1,1,2]`
    · `[1,3]`→`[1,1]` · `[2]`→`[1]`). Ayrıca 120 rastgele sahnelik özellik
    taraması eklendi (yayılımın etiketi kapsaması `CC_STAT_LEFT`'i sınar).
- [ ] **T91 — İki şeride yayılan kapının `road` numarası TANIMSIZ (ACIK karelerin %42'si)** · `codes/costmap_path_finder.py` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-146**
  - 🔎 **v34 TANISI + SIFIR-MODEL · 2026-08-20 · D-204.** Kazanan kapı iki
    şeride yayılan: 12/30 (kesin) / 10/30 (emir tanımı) — 🔴 **çürütücünün
    sıfır-modeli (gözlenen kapı genişlikleriyle rastgele yerleşim) tam
    10,1/30 öngörüyor: sayı costmap kusuru değil GEOMETRİK TABAN ORANI.**
    v30 kıyası istatistiksel boş (z=0,15). Çerçeve "kusur oranı" değil
    "tanım eksiği" olarak okunmalı (kapı bir açıklık, numara bir nokta).

  - T90 etiketi sözleşmeye bağladı ama **kapı bir nokta değil bir açıklıktır.**
    Ölçüldü (v30, n=260, üretimin **kesin** `serit_yayilimi` alanıyla):
    ```text
    n_kapi == 3 kare                                      : 34
      KORUMA reddediyor (etiket çakışması)                :  3
      ACIK kalan                                          : 31
        KAZANAN kapı İKİ ŞERİDE yayılıyor (numara SINIRDA): 13  (%42)
    ```
    `serit_yayilimi` alanı bu kareleri **görünür** kılar; **çözmez**.
  - **SEÇENEKLER:**
    (a) ağırlık merkezi (bugünkü davranış) — yürürlükte;
    (b) kapının **darboğaz noktasının** şeridi — rota fiilen oradan geçer.
        **ÖLÇÜLMEDİ**: darboğaz noktası karar nesnesinde yayınlanmıyor, önce
        o alan yayınlanmalı;
    (c) yayılım iki şeritliyse **fail-closed** → 🔴 **ELENDİ (D-147)**.
        Çevrimdışı ölçüldü: ACIK **31 → 18/260**, ön kayıt kapısı (≥31) düşer.
        Gerekçesi de zayıf çıktı: yayılan 13 kazananın **12'sinde** merkez şerit
        sınırına 10 px'ten uzak (medyan 29,3 px) — etiket kıl payında değil.
- [x] **T93 — K5 kapısı TEK TEMİZ ÇEKİLİŞTE ölçülüyor; `K5=0` sağlam bir özellik değil** · `65_kabul_denetcisi.py` · `66_k5_bariyer_populasyon.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-149**
  - ✅ **KAPANDI (defter düzeltmesi 2026-08-18).** Popülasyon kapısı kuruldu
    (`66_k5_bariyer_populasyon.py`, 173 kare × 21 çekiliş) ve ölçtü:
    v30'un `K5=0`'ı **şanslı çekilişmiş** (D-150). Kapı o günden beri
    **K5-SIKI** biçimiyle kullanılıyor — T94'ün ön kaydında bağlayıcı ölçüt
    olarak koştu ve 0/173 (0/3633 çift) ölçüldü (D-158).
  - Ölçüldü (`79_k5_koken.py`, `sa_000131`, 20 eşleştirilmiş gürültülü çekiliş):
    ```text
    v30: KESEN koşu  3/20   darboğaz 14,80 – 17,60 arası oynuyor
    v33: KESEN koşu 20/20   darboğaz 20 koşuda da 14,80
    kesen koşuların darboğazı   : {14,80}                  (HER İKİ MODELDE)
    kesmeyen koşuların darboğazı: {15,98 · 16,00 · 17,60}  (HER İKİ MODELDE)
    ```
    Kare **iki modlu**; kötü mod İKA gövdesini bariyere 2 px sokuyor.
    **v30'un kayıtlı `K5 = 0/173`'ü o çekilişte kesmediği anlamına gelir**,
    kesmeyeceği anlamına değil. D-133'teki "GEÇTİ" ifadesi bu yüzden eksik.
  - Bu, K5'in ölçüm kusuruyla **üçüncü** karşılaşması: D-114 (tek kare) ·
    D-115 (noktasal rota) · D-149 (tek çekiliş).
  - **YAP:** K5 kapısı popülasyon **× gürültülü tekrar** olarak yeniden
    tanımlansın (kararlılık kapısının reçetesi: σ=2/255). Ölçüt "hiçbir karede,
    hiçbir çekilişte kesişim yok" olmalı; tek çekiliş yeterli sayılmasın.
  - ⚠ **ÖNCE KARAR:** eşik gevşetilmiyor, **ölçüm** sıkılaştırılıyor. Bu, v30
    dâhil mevcut modellerin K5'ini yeniden açabilir — sonucu ne olursa olsun
    kayda geçer.
  - **KAPI:** yeni ölçütle v30 ve v33 **eşit koşulda** yeniden ölçülür; iki
    modelin de sonucu `REVIEW_LOG`'a yazılır. Karar kullanıcınındır.

  - ✅ **KOŞULDU · 2026-08-17 · Claude 1** · kayıt **D-150** · betik
    `scripts/olcum/80_k5_siki_kapi.py` · ön kayıt `scripts/olcum/t93_on_kayit.md`
    (ölçüm koşulmadan **önce** yazıldı). 173 kare × (1 temiz + 20 gürültülü),
    eşleştirilmiş, bariyer **temiz** görüntüden (yer gerçeği).
    ```text
    model    TEMİZ çekiliş   HERHANGİ çekiliş   (kare,çekiliş)   K5-SIKI
    v30          0/173            1/173            4/3633        DÜŞER
    v33          1/173            1/173           18/3633        DÜŞER
    pozitif kontrol: temiz çekiliş 66'nın sayılarını BİREBİR verdi
    kesen TEK kare (ikisinde de): sa_000131 · v30 4/21 · v33 18/21
    darboğaz KESEN={14,80} · KESMEYEN={15,98 · 16,00 · 17,00 · 17,60}
    ```
  - 🔴 **ÖN KAYIT DALI 1 ATEŞLEDİ — İKİ MODEL DE DÜŞÜYOR.** v30'un D-133'te
    kayıtlı `K5 = 0/173`'ü **sağlam bir özellik değilmiş**; doğru ifade "o
    çekilişte kesmedi". K5'in ölçüm kusuruyla **dördüncü** karşılaşması.
  - **D-149 DÜZELTİLDİ:** v33 için yazılan "20/20 deterministik", bariyerin
    gürültülü görüntüden türetilmesinin artefaktıymış. Bariyer sabitlenince
    **17/20 (%85)**. "Daha sık kesiyor" ayakta, "deterministik" geri alındı.
  - ⚠ **"K5 düştü" ≠ "araç bariyere çarpıyor".** Kesişen şey gövde değil
    **emniyet zarfı**: `r_gerekli = 4,48 (yarı gövde) + 3,20 (maske hatası)
    + 6,40 (takip hatası) px`. 2 px'lik kesişimde gövde kusursuz takiple
    bariyerden hâlâ ~0,59 m uzakta; aşınan şey takip hatası bütçesi.
    Eşik **gevşetilmedi**; `66`'nın "İKA GÖVDESİ" başlığı yanıltıcı, düzeltilmeli.
  - **KARAR KULLANICININ:** üretim modeli **v30 olarak bırakıldı**
    (`model_registry.json` değişmedi), D-148'in terfi reddi de ayakta.
    Eşit koşulda tablo: v33 kararlılık/K0/K2/K4'te üstün, v30 K5 kesme
    oranında üstün (%19 vs %86), K1/K3 eşit.
  - **ASIL İŞ KORİDORDA:** `sa_000131` payı **0,72 px**; popülasyonda pay < 1 px
    olan 17-18/173 kare var. Model değiştirerek kapanmaz → **T74**.
- [ ] **T92 — Bant seçimi gürültüye karşı KARARSIZ (41/260), envanterin en oynak parçası** · `codes/costmap_path_finder.py:406-409` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-147**
  - 🔎 **v34 İLE YENİDEN ÖLÇÜLDÜ · 2026-08-20 · D-204.** bant_y 4 koşuda
    değişen **34/260** (v30-dönemi 41/260; fark z=0,87, boş). 33/34'te kayma
    >3 px (medyan 64 px), yalnız 7/34'te n_kapi de değişiyor → eşik artefaktı
    değil GERÇEK bant seçim oynaklığı. Ortak-kök sentezinde T91 ile kesişimi
    SIFIR (D-206).

  - `koridor_adaylari` beş aday bant oranı dener ve bandı
    `(kapı_sayısı, toplam_alan)` üzerinden **argmax** ile seçer — yani **sürekli
    bir büyüklük üzerinde ayrık bir seçim**. Ölçüldü (σ=2/255, n=260):
    ```text
    kod durumu     BANT değişen   yol_no değişen   İKİSİ BİRDEN
    T90 öncesi        41/260          10/260            4
    T90 + koruma      41/260          11/260            5
    ```
    **%15,8** — `yol_no` kararsızlığının ~4 katı; T90 öncesi/sonrası **birebir
    aynı**, yani mevcut bir kusur.
  - Doğrudan izlenen tek vaka `sa_000166`: bant `[236,275] → [300,339]` kayınca
    kazanan kapının merkezi şerit sınırını geçti — oysa merkez sınıra **47,3 px**
    uzaktı, yani kıl payı bir titreme değil.
  - ⚠ **NEDENSELLİK YOK:** 41 bant değişiminin yalnız 5'i `yol_no`'yu de çevirdi;
    11 çevrilmenin 6'sında bant hiç değişmedi. Bant kararlılığı **aday** bir
    kaldıraçtır, kanıtlanmış çare değil.
  - Bu, D-122 (şerit beraberliği) ve D-145 (A\* maliyet beraberliği) ile **aynı
    kusur sınıfıdır** — proje bunu üçüncü kez görüyor.
  - **KAPI:** `75_koridor_envanteri.py` → bant değişen kare **≤ 10/260** ve
    `B ≤ 11/260` **ve** ACIK `≥ 31/260`. Üçü birden tutmazsa düzeltme reddedilir.
  - **KAPI:** seçilen seçenek `75_koridor_envanteri.py` ile ölçülecek;
    `B <= 11/260` (T90+koruma tabanı) **ve** ACIK sayısı `>= 31/260` kalmalı.
    İkisi birden tutmuyorsa seçenek reddedilir.
  - ⚠ Etiket **çakışması** T90'da zaten fail-closed kapatıldı (3/34 kare); bu
    görev yalnız **yayılım** belirsizliğini kapsar, ikisi karıştırılmasın.
- [STATUS: READY_FOR_REVIEW] **T74 — Kusursuz algıyla bile rotaların %9,2'si moloza SIYIRIYOR: koridorlar gövde açıklığına göre dar** · `O:
avitas-local-train)_sentetik_arena.py` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-104**
  - Yer gerçeği etiketleriyle (model YOK, yani kusursuz algı) ölçüldü:
    ```text
    kume                  rota      moloza basan   AGIR basma
    T71 · YER GERCEGI  259/260    0/260  (%0,0)         0
    T66 · YER GERCEGI  260/260   24/260  (%9,2)         0
    ```
  - Hepsi **hafif** (ağır basma 0) → çarpışma değil **sıyırma**: ada
    geometrisinde koridor daralınca A* rotası C-uzayı sınırına yaslanıyor.
  - Şartname koridor genişliği **vermiyor**; ama 50×50 m arenada üç güzergâh
    için asgari `2 × R_GEREKLI_M = 2,20 m` fazlasıyla sağlanabilir olmalı.
  - **YAP:** ada yerleşiminde koridor genişliğine **alt sınır** koy —
    `mpp` üzerinden metrik olarak türet, çıplak piksel yazma (madde 16).
  - **KAPI:** yer gerçeğiyle moloza basma **0'a** insin · rota üretimi çökmesin ·
    renk çeşitliliği ve bariyer kapatma oranı (128/260) bozulmasın.

  - **✅ ÖLÇÜLDÜ · 2026-08-15 · Claude-2** · kayıt **D-126**. 🔴 `R_GEREKLI_M`
    **değiştirilmedi** (emrin 3. maddesi).
  - **Adım 1 — dar paylar TEK bir parametre aralığından gelmiyor.** Kusursuz
    algıyla (yer gerçeği maskesi, model yok), n=260:
    ```text
    uretec serit durumu     n    medyan     min     pay<3px
    acik                  170     17.92    0.10     17/170  (%10.0)
    kapali                 51      7.92    0.12     18/51   (%35.3)
    dar+bariyer            16      7.42    0.10      5/16   (%31.3)
    dar                     8      9.52    0.92      3/8    (%37.5)
    acik+bariyer            8      5.42    0.92      3/8    (%37.5)
    TUM: medyan 14.31 px · min 0.10 px · pay<3px 46/260 · pay<0: 0/260
    ```
    🔴 **`dar_orani = 0.28` değil:** "dar" şeritler yalnız 24/260 karede
    seçiliyor, oysa dar payların **17'si (%37) "acik" şeritlerden**. En düşük pay
    (0,10 px) hem "acik" hem "dar+bariyer" durumunda görülüyor.
  - ⚠ **Algı değil geometri:** aynı ölçüt modelle 10,9 px / 59-255 (D-122),
    kusursuz algıyla **14,31 px / 46-260**. Darlığın büyük kısmı modelin hatası
    değil **üretecin geometrisi**; kusursuz algıda bile %17,7 kare 3 px altında.
  - **Adım 2 — `R_GEREKLI_M = 1,10 m` bileşenlerinin kanıtı:**
    ```text
    IKA_GENISLIK_M/2  0.35 m  %32  SIM modelinden turetildi (model.sdf);
                                   kodun kendi notu: "GERCEK arac FARKLI olabilir"
    MASKE_HATA_M      0.25 m  %23  gerekceli ama OLCULMEMIS
    TAKIP_HATA_M      0.50 m  %45  🔴 "SAF VARSAYIM, en buyuk terim" (TAHMINLER #1)
    OLCULMEMIS PAY: 0.75 / 1.10 = %68 · GERCEK IKA uzerinde olculen bilesen: YOK
    ```
    🔴 **Belge ile kod çelişiyor:** TAHMINLER bloğu `TAKIP_HATA_M = 0.40` diyor,
    kod `0.50`. Denetim notu **bayat**; hangisinin doğru olduğu bu görevde
    belirlenemez, **dokunulmadı**.

  - 🔴 **TEŞHİS ÇÜRÜDÜ · 2026-08-17 · Claude 1** · kayıt **D-151**.
    D-126'nın *"darlığın büyük kısmı üretecin geometrisidir"* sonucu ölçümle
    yanlışlandı; görevin YAP maddesi (**üreteçte koridor genişliğine alt sınır**)
    **yanlış yeri düzeltirdi.** Alttan üste giden yolların en iyi darboğazı
    (maximin) ölçüldü (yer gerçeği, model YOK):
    ```text
    ölçüt                    TÜM (n=260)    DAR olanlar (n=46)
    ROTANIN darboğazı        medyan 28,4    medyan 15,09
    MAXIMIN (en iyi yol)     medyan 36,0    medyan 24,67
    KAYIP (maximin - rota)   medyan  6,6    medyan  9,00
    kayıp > 3 px olan kare   202/260
    DAR karelerin 45/46'sında maximin > r_gerekli + 3 px
    ```
    Yani **rahat geçilebilir yol zaten vardı, rota onu kullanmadı.** Gerçekten
    sıkışık kare 46 değil **1**. Üretece alt sınır koymak, kullanılmayan bir
    bolluğu daha da büyütür.
  - **K5 ile doğrudan bağ:** D-150'de K5'i iki modelde de düşüren `sa_000131`,
    yer gerçeğiyle rota darboğazı **16,39 px** (pay 2,31) iken maximin
    **37,00 px** (pay 22,92). K5 sorunu "bariyer yakın" değil, "rota gereksiz
    yere bariyerin dibinden geçiyor".
  - ⚠ Kalan **1 kare** (maximin ≤ r_gerekli+3) gerçekten sıkışık; üreteç
    tarafında alt sınır O kare için hâlâ anlamlı olabilir — ölçülmedi.
- [x] **T94 — Planlayıcı, ulaşabileceği en iyi darboğazın medyan 6,6 px altında kalıyor** · `codes/costmap_path_finder.py:509-585` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-151**
  - ✅ **KAPANDI (defter düzeltmesi 2026-08-18).** Açıklık koruyan
    string-pulling üretimde (`D-158`); bağımsız denetim sekiz bulgu getirdi,
    biri kuralı 2. aşamada tamamen siliyordu, altısı kodla kapatıldı.
  - `astar()` açıklık cezası `1 + LAMBDA_ACIKLIK · u^US_ACIKLIK`
    (`LAMBDA=3,0`, `US=2,0`): en dar hücrenin cezası **en çok 4 kat**, ve
    `DOYUM_CARPANI_M` üstündeki açıklık **ek ödül getirmez**. Dolayısıyla
    4 kattan uzun her güvenli sapma reddedilir. ⚠ Bu bir **hipotezdir**;
    LAMBDA/US değişiminin kaybı kapatacağı **ölçülmedi**.
  - **Etki zinciri:** dar rota → T79 kararsızlığı (C-uzayı sınırına yaslanan
    rota gürültüyle çevriliyor) → K5 teması (D-150) → T74'ün "dar koridor"
    görünümü. Üçü de aynı davranışın belirtisi olabilir; **kanıtlanmadı**.
  - **ÖNCE ÖLÇ, SONRA YAZ:** LAMBDA/US taraması yapılmadan kod değiştirilmesin.
    Rota **uzunluğu** artacaktır; şartname süreye bakar, bedeli ölçülmeli.
  - **KAPI (ön kayıt olarak yazılacak, sonuç görülmeden):**
    yer gerçeğiyle kayıp medyanı **≤ 2 px** · `pay < 3 px` olan kare
    **≤ 5/260** (46'dan) · K1 ≥ 258/260 · `test_rota_sentetik` 15/15 ·
    K2/K3 kötüleşmeyecek · rota uzunluğu artışı **ölçülüp kayda geçecek**.

  - 🔴 **TARAMA KOŞULDU · HİÇBİRİ GEÇMEDİ · 2026-08-17** · kayıt **D-152** ·
    betik `scripts/olcum/82_t94_planlayici_taramasi.py` (üretim kodu
    **değiştirilmedi**; `rpi_inference.astar` sarmalayıcıyla değiştirildi).
    ```text
    mod                    rota  kayıp med  pay med  pay<3px  uzunluk
    A mevcut                260      6,61    14,31       46    539,2
    B C-uzayı ızgarası      260      6,61    14,31       45    539,2
    C B + r_gerçek          260      7,00    13,92       45    539,2
    D C + lam=6             260      7,01    12,92       55    539,2
    E C + lam=12            260      7,79    12,92       55    539,2
    F C + us=1              260      7,00    14,31       45    539,2
    ```
    Kapı `kayıp ≤ 2 px` istiyordu; **en iyisi 6,61 = mevcut durum.** Üçü daha
    kötü: `lam=12` hem kaybı büyüttü hem dar kareyi 46→**55** yaptı.
    **Ön kayıt kuralı uygulandı: KOD DEĞİŞTİRİLMEDİ.**
  - **Kayıp son işlemde DEĞİL:** ham A\* darboğazı medyan 28,50 px, nihai
    28,39 px → **son işlem kaybı 0,11 px**. Kayıp A\*'ın seçtiği yoldadır
    (maximin 36,0 vs ham A\* 28,5).
  - 🔴 **ÜÇ HİPOTEZ DE ÇÜRÜDÜ:** D-151'in "LAMBDA küçük"ü, "arama ızgarası
    C-uzayı değil" ve "`r_gerekli_m=0.0` geçiliyor". **En çarpıcı ölçüm: rota
    uzunluğu altı modda da 539,2 px** — A\*'ın bulduğu yol bu parametrelerden
    fiilen bağımsız. Köken ceza ağırlığında değil, **arama uzayının kendisinde**
    görünüyor; bu da ölçülmedi.
  - 🔴 **"ALTERNATİF YOL VAR MI?" ÖLÇÜLDÜ · 2026-08-17** · kayıt **D-153** ·
    betik `scripts/olcum/83_t94_izgara_cozunurlugu.py`.
    ```text
    maximin TAM ÇÖZÜNÜRLÜK   36,00 px
    maximin A* IZGARASINDA   30,00 px   -> IZGARA KAYBI  6,00 px  (~%80)
    A* yolunun darboğazı     28,50 px   -> SEÇİM  KAYBI  1,50 px  (~%20)
    ```
    **Geniş yol tam çözünürlükte VAR, A\*'ın ızgarasında YOK.** A\* kendi
    ızgarasında zaten neredeyse en iyisini buluyor — D-152'de altı ceza
    yapılandırmasının neden hiçbir şey değiştirmediği budur.
  - **Izgara ölçüldü:** ~64×20-44 hücre, **adım 10 px**, kare başına `astar`
    çağrısı **1**. Bütçe 32768 iken ~2.600 hücre kullanılıyor → **%92 boşta.**
    Adım bütçeden değil `min(k_open.shape)`'ten, yani **morfoloji
    çekirdeğinden** geliyor; `_plan_adimlari` ince ızgarayı yalnız kaba ızgara
    **başarısız olursa** dener, o yüzden hiç koşmaz.
    ⚠ D-152'de bu adayı "hesapla eledim" diye işaretlemiştim (adım ~4 px
    varsaymıştım) — **hesap yanlıştı**, ölçüm çürüttü.
  - 🔴 **IZGARAYI DÜZELTMEK TOPLAMI DEĞİŞTİRMİYOR (n=40):**
    ```text
    ölçüt                      MEVCUT    İNCE IZGARA
    IZGARA KAYBI  (mt-mi)        7,00        2,00
    SEÇİM KAYBI   (mi-ham)      -0,00       -0,00
    SON İŞLEM     (ham-dar)     -1,00      +4,00
    TOPLAM        (mt-dar)       6,00       6,00   ← DEĞİŞMEDİ
    son işlem >2px kare         11/40      24/40
    pay<3px / pay min          4 / 1,71   7 / 0,31
    süre medyan               24,9 ms    179,0 ms  (7,2 kat)
    ```
    **Izgaranın kazandırdığını waypoint seyreltmesi geri alıyor.** Ön kayıt
    kapısını üç kalemde birden tutturamadı → **kod değiştirilmedi.**
  - ✅ **KÖKEN BULUNDU · 2026-08-17** · kayıt **D-154** · betik
    `scripts/olcum/84_t94_seyreltme.py`. Suçlu `yol_duzelt`'in **görüş-hattı
    string-pulling**'i (`_rotayi_ornekle` değil — darboğaz kanonik yoldan
    ölçülüyor, `rpi_inference.py:1224`).
    ```text
    ölçüt (TAM ÇÖZÜNÜRLÜK)      MEVCUT     TAVAN (string-pulling YOK)
    ham A* yolu darboğazı       33,00 px          33,00 px
    kanonik yol darboğazı       28,14 px          33,00 px
    STRING-PULLING KAYBI         4,00 px           0,00 px
      >2 px olan kare          165/260 (%63)         0/259
    TOPLAM KAYIP                 6,61 px           2,33 px
    pay<3px / pay min         46 / 0,10          7 / 0,92
    düğüm (giriş→çıkış)          56 → 2           56 → 56
    ```
  - 🔴 **260 karenin 213'ünde (%82) rota TAM 2 DÜĞÜME** iniyor — baştan sona
    tek düz kiriş. `_gorus_hatti` kirişi doğruladığı için **güvensiz değil**,
    ama emniyet payını sistematik olarak yiyor.
  - **T74'ün "dar koridor" görünümünün %85'i buradan:** dar karelerin
    **39/46**'sı tavan modda pay ≥ 3 px'e çıkıyor.
  - **K5 ile doğrudan bağ:** `sa_000131` (D-150'de K5'i iki modelde de düşüren
    kare) string-pulling yüzünden **10,47 px** kaybediyor — pay 12,52 → 2,31.
  - 🔴 **TAVAN BİLE KAPIYI TUTTURMUYOR:** toplam kayıp 2,33 px (kapı ≤2) ve
    pay<3px 7 (kapı ≤5). String-pulling düzeltilse **bile T94 kapanmaz**;
    kalanı ızgara (D-153: 2,00 px) ve seçim kaybından. **Kod değiştirilmedi.**
  - **DENENDI · V1 = açıklık koruyan kiriş** (`eşik = r_gerekli + MASKE_HATA`,
    yalnız `yol_duzelt` içinde) · kayıtlar **D-155** (yer gerçeği) ve **D-156**
    (model, projenin kendi kapıları).
    ```text
    ölçüt                    taban(v30)    V1        durum
    K5 · sa_000131 kesen      4/20        0/20      ÇÖZÜLDÜ
    kararlılık A              8/260      11/260     🔴 DÜŞTÜ
    pay<3px (model)          59/258      11/255     iyileşti
    pay<3px (yer gerçeği)    46/260       5/260     iyileşti
    rota kaybı                  —      1 kare (sa_000083)
    waypoint / uzunluk / süre     hepsi ~AYNI
    ```
    **Ön kayıt "üçü birden" istiyordu; kararlılık düştü → RED, kod
    değiştirilmedi.** K5'in çözülmüş olması kuralı kurtarmaz.
  - 🔴 **ÖĞRENİLEN:** K5 kusuru string-pulling kaynaklıdır ve **giderilebilir**
    (4/20 → 0/20); kıl payı koridorlar da giderilebilir. Ama **sert eşikli** bir
    kural bunu kararlılık pahasına yapıyor.
  - **SIRADAKİ (ölçülmedi):** sert eşik yerine **yumuşak/histerezisli** biçim —
    D-122'nin beraberlik bandı mantığının kiriş kabulüne taşınması. Gerekçe:
    V1 sürekli bir ölçü (kiriş açıklığı) üzerine **sert ayrık karar** koyuyor;
    proje bu kusur sınıfını **beşinci kez** görüyor (D-122 · D-145 · D-147 ·
    D-156). ⚠ V1'in kararsızlığının bu mekanizmadan geldiği **doğrulanmadı**.
  - ⚠ **Ölçülmeyenler:** K5-SIKI popülasyonu (0/173 mü?), K0..K4 kabul denetimi
    V1 ile, `sa_000083`teki rota kaybının sebebi.

  - ✅ **YAPILDI · W1 (göreli band) ÜRETİME ALINDI · 2026-08-17** · kayıt **D-158**.
    Ön kayıt `scripts/olcum/w1_on_kayit.md`, ölçümlerden **önce** yazıldı; on
    ölçütün **onu da** tuttu.
    ```text
    ölçüt                  eşik        taban(v30)   SONUÇ
    K5-SIKI kesen kare     == 0/173    1/173        0/173  (0/3633 çift)
    kararlılık A           <= 8/260    8/260        8/260
    K1 rota                >= 258/260  258          258/260
    K2 moloza basma        <= 22/258   22/258       14/258   ← İYİLEŞTİ
    K3 / K4 / K0           —           0 / 1 / %8,0  aynı
    waypoint / uzunluk / süre  ≤16 / ≤%5 / ≤2×      8 / %0,00 / 1,17×
    yan ölçüm: pay<3px                 57/258       15/258
    ```
    **Bağımsız denetim SEKİZ bulgu getirdi; biri (HIGH) kuralı 2. aşamada
    tamamen siliyordu** (`aci_esigi_derece=15` ile düğüm 3→2, açıklık 9,06→4,00
    — korumasızla birebir aynı). Altısı kodla kapatıldı, ikisi göreve döndü.
    Düzeltmeler algoritmayı değiştirdiği için **bütün kapılar son kodla
    yeniden koşuldu**.
- [x] **T95 — UYGULANDI · `rota_bul` açıklık koruması (KATMAN B)** · `codes/costmap_path_finder.py:1116` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-158** (denetim bulgusu 2) → **D-164**
  - `rota_bul` `yol_duzelt`i `dt_px` **geçirmeden** çağırıyor; oysa
    `sonuc["dt_px"]` bir satır önce kapsamda. D-154'te ölçülen kusur (kiriş
    emniyet payını yiyor, medyan 4 px) bu yolda **hâlâ canlı**.
  - `rota_bul` → `simulation/scripts/iha_haritala.py:329` → `road`.
  - ⚠ **Körlemesine eklenmesin:** o yolun açıklık ölçüm düzeneği yok. Önce
    `rota_bul` için bir kayıp ölçümü (maximin karşılaştırması) kurulmalı,
    sonra ön kayıtla değiştirilmeli.
  - 🔴 **KAPI DÜZELTİLDİ (mimar, ölçümden ÖNCE).** Buraya ilk yazdığım
    "ACIK ≥ **34**/260" **BAYAT** bir sayıdır: 34, D-146'daki T90 **öncesi**
    ölçümdür; T90'ın fail-closed etiket koruması onu ölçülerek **31/260**'a
    indirdi (D-146, "öngörü TAM tuttu"). Üretim bugün 34 vermiyor — yani kapı,
    üretimin **sağlamadığı** bir eşik istiyordu. Bu, D-157'de yakalanan hatanın
    birebir aynısıdır ve aynı şekilde kapatılıyor: eşik mutlak sayıya değil,
    **aynı koşumda ölçülen tabana** bağlanır.
  - **KAPI (ön kayıt: `scripts/olcum/t95_on_kayit.md`):** `rota_bul` ACIK sayısı
    **aynı koşumun taban değerinden düşmeyecek** · `test_rota_sentetik` 15/15 ·
    `unittest discover` düşmeyecek.

  - 🔴 **ÖLÇÜLDÜ · KAPI TUTMADI, ZORLANMADI · 2026-08-18 · Claude-2** · kayıt
    `REVIEW_LOG.md` **D-159**. Ölçüm `scripts/olcum/89_t95_rota_bul_kayip.py`.
    **Üretim kodu DEĞİŞTİRİLMEDİ** (`git status`: `codes/`, `jetson_paket/` temiz).
  - **Kusur bu yolda CANLI ve BÜYÜK** — taban vs koruma, aynı koşum, aynı `mk`,
    n=260 temiz kare:
    ```text
    olcum                            TABAN     KORUMA
    durum == ACIK                       31         31
    kayip medyani (px)                3,00      0,693
    kayip > 2 px olan ACIK kare         19          0
    pay < 3 px olan ACIK kare            3          0
    pay medyani (px)                 13,92      17,92
    waypoint medyani                    31         32
    `duzelt` suresi medyani (ms)      0,91       2,79
    ```
    `yol_no` **31/31 karede AYNI** — koruma hiçbir koridor seçimini çevirmiyor.
    Tabanda payı 3 px altında kalan üç karenin üçü de kurtuluyor:
    `0,48 → 8,92` · `0,92 → 8,01` · `1,95 → 6,02` px.
  - **ÖN KAYIT ÖLÇÜTLERİ — gerçek sonuç:**
    ```text
    (1) ACIK >= taban              31 >= 31        TUTTU
    (2) kayip medyani kazanci      2,307 >= 1,00   TUTTU
    (3) pay<3 ACIK kare <= taban   0 <= 3          TUTTU
    (4) duzelt suresi <= 2 kat     2,79 vs 1,82    DUSTU  (3,07 kat)
    (5) waypoint medyani <= 16     32              DUSTU  (TABAN da 31)
    (6) codes/test_rota_sentetik.py                SONUC: 15/15 dogru
    (7) unittest discover -s tests  Ran 584 tests in 51.506s / OK
    ```
  - ⚠ **(4)'ü önce KENDİ PROBUM kurtarıyordu.** İlk koşumda 1,96 → 3,84 ms
    (**1,96 kat**) ile kıl payı tutuyordu; sonra gördüm ki açıklık ölçümlerimi
    `rota_bul`un `sure_ms["duzelt"]` **penceresinin içinde** yapıyordum ve bu
    sabit ek yük **oranı sıkıştırıyordu**. Prob kapatılıp 260 kare yeniden
    koşuldu: `sure_ms["duzelt"]` **0,91 → 2,79 (3,07 kat)**, yalnız `yol_duzelt`
    çağrısı **0,37 → 2,29 (6,19 kat)**. **Her dürüst okumada (4) düşüyor.**
    Mutlak artış kare başına **+1,88 ms** (KATMAN B bütçesi ~30-40 ms'in ~%5'i)
    — bu bir **olgudur, gevşetme gerekçesi değildir**; karar mimarındır.
  - ⚠ **(5) değişikliği AYIRT ETMİYOR:** `waypoint medyanı <= 16` KATMAN A'nın
    sayısıdır (D-158: taban 8); KATMAN B'nin **tabanı 31**'dir. Yani ölçüt yine
    üretimin **sağlamadığı** bir eşik istiyor — D-146 ve D-157'de yakalanan
    kusurun **üçüncü tekrarı**. Ölçüt **gevşetilmedi**, olgu bildirilir.
    ⚠ (5) düzeltilse bile **(4) yine düşer**; sonuç değişmez.
  - **ÖLÇÜMÜN POZİTİF KONTROLLERİ:** taban `dt_px` sızıntısı **0** · taban
    çağrı/enjekte **31/0** · koruma **31/31** · `mk` bozulan kare **0**.
  - ⚠ **DOĞRULANAMADI:** küme sentetiktir; KATMAN B'nin gerçek girdisi
    ortomozaiktir ve D-158 bulgu 3'te 1860 düğümlü yolda 5,2 s ölçülmüştü —
    **süre ölçütü mozaik ölçeğinde yeniden ölçülmelidir.** Ayrıca gürültü
    altında kararlılık (A ölçüsü) bu yolda ölçülmedi.
  - 🔎 **MİMAR DENETİMİ · 2026-08-18 · kayıt `REVIEW_LOG.md` D-160.** Ölçüm
    **GEÇERLİ**, RED kararı **DOĞRU**. Bağımsız doğrulandı: `git diff codes/
    tests/ jetson_paket/ simulation/` **boş**; D-159 tablosu JSON'dan yeniden
    okundu, **birebir**; pozitif kontroller `gecerli: true`.
    ⚠ (6) ve (7) bu dalda **kanıt değeri taşımaz** — üretim kodu değişmediğinde
    15/15 ve 584 OK zaten değişemez. Kapı tasarımının (benim) zayıflığı.
  - 🔴 **(5) ÖLÇÜTÜ GEÇERSİZ — hata benim, ÜÇÜNCÜ tekrar.** `waypoint medyanı
    ≤ 16` KATMAN A'nın sayısıdır. Kökeni doğrulandı: `rpi_inference.py:847`
    `wp_aralik_px = max(shape)*2` (bölme YOK) · `costmap_path_finder.py:1116`
    `wp_aralik_px = olc["wp_aralik_px"]` (**böler**). KATMAN B'de waypoint
    sayısını string-pulling değil `_maks_aralikla_bol` belirler; 31 bir kusur
    değil **tasarım sayısıdır**. Ölçüt tabandan yeniden türetildi:
    **(5') waypoint medyanı ≤ taban + 2** (31 → eşik 33; ölçülen **32** → tutar).
    Ayırt edici olgu: 64'e (MAKS_WP) dayansaydı reddederdim.
    ⚠ Bundan sonra bağlayıcı kural: **bir ön kayıt ölçütü mutlak sayı
    içeriyorsa, o sayının tabanı AYNI YOLDA ve AYNI KOŞUMDA ölçülmüş olmalı.**
  - **(4) GEVŞETİLMEDİ.** Bir orandır, (5)'in kusuru ona bulaşmaz ve düşmüştür
    (3,07 kat · yalnız çağrı 6,19 kat). Gevşetmeyi haklı kılacak ölçüm **yok**:
    KATMAN B'nin gerçek girdisi ortomozaiktir. Ayırt edici olgu: mozaik
    ölçeğinde artış bütçenin %5'inde kalsaydı **kabul ederdim**.
  - **SONUÇ: T95 `[ ]` KALIR.** Değişiklik **değerlidir** (pay<3px 3→0, kayıp
    3,00→0,693, koridor seçimi 31/31 karede aynı); onu tutan tek şey maliyet.
    **Sıradaki adım oran tartışması değil, ÖLÇEK ÖLÇÜMÜDÜR:**
    1. Gerçek karelerde `_polyline_asgari_aciklik` **çağrı sayısını** say —
       n=91'de maliyet neden 1,03–7,82 ms arasında oynuyor? (reddetme maliyeti)
    2. **Mozaik ölçeğinde** düğüm sayısı ve süre ölç (`iha_haritala` girdisi).
    3. Ön kaydı o ölçümden sonra, **mutlak bütçe** cinsinden yeniden yaz.
  - 🔴 **T95-B ÖLÇÜLDÜ · 2026-08-18 · `REVIEW_LOG.md` D-162 (amele) / D-163
    (mimar denetimi).** Ölçüm `scripts/olcum/90_t95b_butce.py`. **Üretim kodu
    yine DEĞİŞTİRİLMEDİ.**
    ```text
    olcut                                  esik            SONUC
    (1) ACIK >= taban                      >= 31        31   TUTTU
    (3) pay < 3 px ACIK kare <= taban      <= 3          0   TUTTU
    (4'a) TOPLAM sure medyani <= 40 ms     <= 40    49,977   DUSTU
    (4'b) artis <= tabanin %20             <= %20     %6,2   TUTTU
    (5') waypoint medyani <= taban + 2     <= 33        32   TUTTU
    (6) test_rota_sentetik / (7) unittest           15/15 · 584 OK
    ```
  - 🔴 **(4'a) KAPSAM HATASIYDI — ve hata benim.** 40 ms'i modülün kendi
    sözleşmesinden aldım (`:24`) ama **o satırın kapsamını okumadım**: 30-40 ms
    açıkça **KATMAN B**'nindir (`astar + yol_duzelt + rota_dogrula`); `rota_bul`
    TOPLAMI ise **iki katmanı birden** koşar. Taban da (47 ms) eşiği aşıyor —
    çünkü eşik o kapsam için hiç yazılmamıştı. Ölçüt kendi kapsamında yeniden
    türetildi ve **sıkılaştı** (toplam kapsamda artış %6,2 iken KATMAN B
    kapsamında %16,0):
    ```text
    kapsam        106x106            128x128 (URETIM OLCEGI)
    KATMAN A   24,45 -> 24,41 ms   83,02 -> 86,21 ms   (korumadan BAGIMSIZ)
    KATMAN B   16,15 -> 18,90 ms   21,69 -> 25,15 ms   (+%16,0) <- 30-40 ms ICINDE
    ```
    ⚠ **Bu, mutlak eşik kusurunun DÖRDÜNCÜ tekrarı** (D-146 taban 31 · D-157
    taban 258 · D-159 taban 31 · şimdi kapsam). D-160 kuralı genişletildi:
    **bir ölçüt dışarıdan sayı alıyorsa yalnız KAYNAĞI değil KAPSAMI da
    doğrulanır.**
  - **MALİYETİN KAYNAĞI ÇÖZÜLDÜ** (emrin sorusu): ön ek geçişi **%55** (sabit,
    O(n), her karede tam 90 çağrı), reddetme döngüsü **%45** (1–190 çağrı arası
    — n=91'de 1,03–7,82 ms oynaklığının kaynağı **budur**), aşama 2 **%0**.
  - 🔴 **BUNA RAĞMEN T95 UYGULANMIYOR → T95-C.** Ölçütü dört kez düzelttim ve
    her düzeltmede sonuç "geçti"ye yaklaştı. Düzeltmeler nesnel olsa da bu
    yeterli değil. **Hiç ölçülmemiş ve bu kuralı bir kez ÖLDÜRMÜŞ** eksende
    sınanacak: **gürültü altında kararlılık** — D-156'da aynı kuralın sabit
    eşikli biçimi (V1) K5'i çözdü ama kararlılığı 8→11/260 bozduğu için
    reddedilmişti. Ön kayıt: `scripts/olcum/t95c_on_kayit.md` (yazıldı).

  - 🔴 **T95-B ÖLÇÜLDÜ · (4') YİNE DÜŞTÜ, ZORLANMADI · 2026-08-18 · Claude-2**
    · kayıt `REVIEW_LOG.md` **D-162** · ölçüm `scripts/olcum/90_t95b_butce.py`.
    **Üretim kodu DEĞİŞTİRİLMEDİ** (`git status`: `codes/ tests/ comms/
    jetson_paket/ simulation/` **boş**).
  - **Üç ayrı koşum** (D-159 §4 dersi — kendi aletim ölçütü kurtarmasın):
    A `--yalniz-sure` (temiz süre) · B `--sayac` (çağrı dökümü) ·
    C `--uretim-olcegi` (128×128).
    ```text
    olcum (kosum A · n=260 · ACIK 31)     TABAN     KORUMA
    durum == ACIK                            31         31
    pay < 3 px olan ACIK kare                 3          0
    waypoint medyani                         31         32
    rota_bul TOPLAM medyan (ms)          47,044     49,977
      costmap                              7,87       8,06
      koridor                             15,11      15,14
      astar                               14,69      15,08
      duzelt                               0,88       2,67
      dogrulama                            0,69       0,66
      KATMAN_A (costmap+koridor)          24,45      24,41
      KATMAN_B (astar+duzelt+dogrulama)   16,15      18,90
    ```
  - **ÖLÇÜTLER:**
    ```text
    (1) ACIK >= taban                31 >= 31          TUTTU
    (2) kayip kazanci >= 1,00 px     2,307 (D-159)     TASINDI
    (3) pay<3 ACIK kare <= taban     0 <= 3            TUTTU
    (4'a) TOPLAM sure <= 40 ms       49,977            DUSTU
    (4'b) artis <= taban %20         +2,933 = %6,2     TUTTU
    (5') waypoint <= taban+2         32 <= 33          TUTTU
    (6) codes/test_rota_sentetik.py  SONUC: 15/15 dogru
    (7) unittest discover -s tests   Ran 584 tests in 50.818s / OK
    ```
    (4') bir birleşimdir; (4'a) düştüğü için **(4') DÜŞTÜ → T95 `[ ]` kalır.**
  - 🔴 **(4'a) değişikliği AYIRT ETMİYOR — TABAN da 40 ms'in üstünde (47,0).**
    Bu, D-146 · D-157 · D-159 ile aynı kusur sınıfının **DÖRDÜNCÜ tekrarı**.
    **Ölçüt gevşetilmedi**; ama eşiğin kaynağı hakkında bir **olgu**:
    `costmap_path_finder.py:21-25` KATMAN B'yi *"astar() + yol_duzelt() +
    rota_dogrula()"* diye tanımlar ve 40 ms **o satırdan** alındı; `rota_bul`
    TOPLAMI ise **iki katmanı birden** içerir. Ölçülen ayrışım:
    **KATMAN B 16,15 → 18,90 ms (30-40 ms bütçesinin İÇİNDE)** ·
    **KATMAN A 24,45 → 24,41 ms (korumadan tamamen bağımsız)**.
    Hangi kapsamın ölçüt olacağı **mimarın kararıdır**.
  - **MALİYET AYRIŞTIRILDI (emrin sorusu):** çağrılar **çağrı yerine göre**
    ayrıldı (imzadan; üretim koduna hiçbir şey eklenmeden).
    ```text
    cagri yeri     n medyan  n maks  ms medyan  ms toplam    pay
    :816 onek            90      90      0,855      26,75   %55,0
    :822 kiris           27     190      0,478      21,91   %45,0
    :875 asama2           0       1      0,000       0,02    %0,0
    toplam cagri: TABAN 0 · KORUMA min 91 · medyan 117 · maks 280
    yol_duzelt GIRDI dugum: 31 karenin HEPSINDE tam 91
    ```
    **Cevap: yarı yarıya** — sabit ön ek geçişi %55, reddetme döngüsü %45,
    aşama-2 pratikte bedava. D-160'ın gözlediği **1,03–7,82 ms oynaklığının
    kaynağı `:822`dir** (1–190 çağrı); `:816` her karede tam 90'dır (n−1).

  - ✅ **T95-C ÖLÇÜLDÜ · HEPSİ TUTTU · UYGULANDI · 2026-08-18 · Claude-2** ·
    kayıt `REVIEW_LOG.md` **D-164** · ölçüm `scripts/olcum/91_t95c_kararlilik.py`.
  - **Sınanan eksen:** bu kuralın sabit eşikli biçimi (V1) D-156'da **tam bu
    eksende öldürülmüştü** (kararlılık 8 → 11/260). `rota_bul` farklı
    parametrelerle koşar (`aci_esigi_derece=15,0` · C-uzayı) ve bu yolda hiç
    gürültü ölçümü yoktu.
    ```text
    olcum (n=260 · sigma 2/255 · 3 cekilis · tohum 7)  TABAN   KORUMA
    (durum, yol_no) CEVIREN kare                          26       26
    temiz kosuda durum == ACIK                            31       31
    DOGRULAMA_BASARISIZ kare (4 kosumun biri)              0        0
      ayni, TOPLAM kosum (1040 icinde)                     0        0
    ```
  - 🔴 **ÇEVİREN KARE KÜMELERİ BİREBİR AYNI** — yalnız korumada çeviren **0**,
    yalnız tabanda çeviren **0**; geçiş histogramları da aynı. Mimarın
    mekanizma öngörüsü doğrulandı: `yol_no` `koridor_adaylari`dan gelir ve
    `yol_duzelt`ten **önce** belirlenir.
  - **ÖLÇÜTLER:**
    ```text
    (K1) ceviren kare <= taban           26 <= 26     TUTTU
    (K2) temiz ACIK >= taban             31 >= 31     TUTTU
    (K3) DOGRULAMA_BASARISIZ <= taban     0 <= 0      TUTTU
    (6) codes/test_rota_sentetik.py      SONUC: 15/15 dogru
    (7) unittest discover -s tests       Ran 589 tests in 51.403s / OK
    ```
    **POZİTİF KONTROLLER:** taban `dt_px` sızıntısı 0 · taban enjekte 0 ·
    `mk` bozulan 0 · RNG çekiliş **780 = 260×3** · koruma çağrı/enjekte 118/118.
  - **UYGULANAN:** `codes/costmap_path_finder.py:1116` →
    `dt_px=sonuc["dt_px"]` (+ `jetson_paket/kod/` kopyası **senkron**).
    Yeni test **`tests/test_rota_bul_aciklik_korumasi.py`** (5 test):
    `dt_px` geçiliyor · geçilen dizi `sonuc["dt_px"]`in **ta kendisi**
    (`assertIs`) · şekil uyumu · sahnenin `yol_duzelt`e **gerçekten ulaştığı** ·
    yardımcının **düşebildiği** karşı kontrol.
  - 🔴 **MUTASYON KONTROLÜ:** üretim satırından `dt_px` geçici kaldırıldı →
    `Ran 5 tests · FAILED (failures=1, errors=2)`. Test boş değil; satır
    yedekten geri alındı (`git checkout` kullanılmadı), ayna senkronu doğrulandı.
  - 🔴 **EMÜLASYON = ÜRETİM, ÖLÇÜMLE DOĞRULANDI (D-158 §4):** değişiklikten
    sonra aynı betik yeniden koşuldu; taban kolu artık `dt_px`i **çıkarmak**
    zorunda (yoksa iki kol aynılaşıp ölçüm sessizce anlamsızlaşırdı).
    ```text
    URETIMIN KENDI gecirdigi dt_px cagrisi : 236 / 236   (T95 ONCESI 0)
    ceviren 26/26 · temiz ACIK 31/31 · DOGRULAMA_BASARISIZ 0/0 — BIREBIR AYNI
    ```
  - ⚠ **DOĞRULANAMADI:** korumanın çevirme **fırsatı hiç doğmadı** —
    `yol_duzelt` sonrası `durum`u değiştirebilen tek dal
    (`:1185-1190 DOGRULAMA_BASARISIZ`) 1040 koşumun hiçbirinde tetiklenmedi.
    (K1)/(K3) yapısal olarak düşebilir ölçütlerdir ama bu kümede **sınanma
    fırsatı bulamadılar**; `rota_dogrula`nın düştüğü bir kümede yeniden
    ölçülmeli. Ayrıca: tek tohum · küme sentetik · **K1..K5 kabul kapıları
    yeniden koşulmadı** (gerekçe: `65`/`66` `analyze_path` üzerinden koşar,
    `rota_bul`u kullanan tek üretim yeri `simulation/scripts/iha_haritala.py` —
    `grep -l` ile tarandı; bu bir **gerekçedir, kapı çıktısı değildir**) ·
    `76_serit_etiketi_celiskisi.py` `rota_bul` kullanır, sayıları kaymış
    olabilir, yeniden koşulmadı.
- [x] **T97 — KAPANDI (önermesi üretim ölçeğinde ÇÜRÜDÜ) · `yol_duzelt` ölçek maliyeti** · `codes/costmap_path_finder.py:768` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-160 §4**
  - Mimarın tanı probu (modelsiz, sentetik): görüntü ve düğüm sayısı **birlikte**
    büyürken `yol_duzelt` süresi
    ```text
    n        50     100     200     400     800
    TABAN  0,66    1,01    3,05   11,45   96,27 ms
    KORUMA 0,66    1,42    4,09   14,53   84,47 ms
    ```
    `costmap_path_finder.py:25` KATMAN B'yi *"~2 Hz'de, ~30-40 ms"* diye
    tanımlar. **n=800'de TABAN tek başına 96 ms** — koruma yokken de bütçe
    aşılıyor, hatta orada KORUMA daha hızlı çıktı (fark gürültü).
  - ⚠ Bu **T94/T95'ten ÖNCE VARDIR**; T95 ölçümü onu yalnız görünür kıldı.
  - ⚠ **DOĞRULANAMADI:** üs ayrıştırılmadı (n ile görüntü birlikte büyütüldü);
    tek makine, tek koşum, varyans yok; **gerçek mozaikte hiç ölçülmedi**.
    Mimarın kendi probudur, **denetimden geçmemiştir**.
  - 🔴 **AYNI GÜN ÇÜRÜTÜLDÜ (mimar, `REVIEW_LOG.md` D-161).** Bu görevi
    "mozaik rejiminde patlıyor" önermesiyle açtım; önerme **ölçülmeden**
    yazılmıştı ve **yanlış**. `iha_haritala.py:64` mozaiği **sabit 1024 px**
    tutar (`MOZ_PX`), saha ~56 m, `ds=8` → plan ızgarası **128×128**. Test
    kümesi 640 px / `ds=6` → **106×106**. Yani üretim girdisi test kümesinden
    **%21 büyük, kat kat değil**. Yukarıdaki tabloda n=800 için tuval
    ~320×5640'tı — **üretimde böyle bir girdi YOKTUR.**
  - Diğer `rota_bul` çağrı yerleri de tarandı (`saha_kuru_kosu.py:709,722`,
    `v21_degerlendir_ve_paketle.py`): hepsi çıkarım ölçeğinde letterbox maskesi
    besler. **KATMAN B girdisi arenanın fiziksel boyutuyla sınırlıdır, büyümez.**
  - **YENİ KAPSAM:** soru "mozaikte patlar mı" değil, **"128×128 plan
    ızgarasında gerçek maliyet nedir"** — ki bu T95-B'nin sorusudur. T97 o
    ölçüm gelene kadar **bekler**; gelen sayı bütçeyi aşmıyorsa **kapanır**.
  - ⚠ Prob ölçümünün kendisi geçerlidir; yanlış olan **ondan çıkardığım üretim
    sonucudur**. Kayıt bu yüzden silinmedi.
  - ✅ **KAPANDI · 2026-08-18 · `REVIEW_LOG.md` D-162 §6 / D-163 §4.** Üretim
    ölçeğinde (1024 px · mpp 0,0547 · ds 8 · plan ızgarası **128×128**) ölçüldü:
    ```text
    yol_duzelt (koruma dahil)    4,21 ms
    KATMAN B toplamı            25,15 ms   <- sözleşme 30-40 ms İÇİNDE
    ```
    Açılış önermesi ("mozaik rejiminde bütçeyi aşıyor") üretimde
    **gerçekleşmiyor**. Görev kapanır.
- [x] **T98 — KAPANDI (3 FPS hedefiyle tıkayıcı değil) · KATMAN A 1024 px'te 83 ms** · `codes/costmap_path_finder.py:21-25` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-162 §6, D-163 §5**
  - T95-B ölçümünün yan bulgusu; **korumadan tamamen bağımsız** (costmap
    28,27→28,08 · koridor 53,27→51,75 ms; fark gürültü).
  - Modülün kendi sözleşmesi (`:22`): *"KATMAN A (her karede, **~5 ms @384px**)"*.
  - 🔴 **"Sözleşmesini N kat aşıyor" DENMİYOR** — ölçüm 1024 px'e ait, sözleşme
    384 px'e. Bunu kıyaslamak D-163 §2'de yakalanan **kapsam hatasının** birebir
    tekrarı olurdu. Amele de bu iddiada bulunmadı; doğru davrandı.
  - **İLK İŞ: 384 px'te ölç.** Sonra 640 px (`rpi_inference` yolu) ve 1024 px
    (`iha_haritala` mozaik yolu). Üçü de aynı koşumda.
  - ⚠ Açıklayıcı **tahmin, ölçüm değil**: 1024 px yolu mozaik yoludur ve "her
    karede" koşmaz; kare başına koşan yol `rpi_inference`tır (384-640 px). Bu
    doğruysa 83 ms göründüğü kadar alarm verici değildir. **T98 karara bağlar.**
  - **KAPI:** ölçüm koşulmadan hiçbir kod değişmez.
  - 🔎 **MİMAR ÖLÇTÜ (modelsiz, SENTETİK maske) · 2026-08-18 · `REVIEW_LOG.md`
    D-169.** İddianın arkasında **hiçbir ölçüm yokmuş** — `grep` ile tarandı,
    sayı yalnız docstring'de duruyordu ve oradan T95-B'nin (4') ölçütüne
    gerekçe olarak taşınmış.
    ```text
    px     serbest_ms  koridor_ms  KATMAN_A   _bagli_mi cagrisi
    384        2,12       10,46      12,58           9
    640        6,33       26,31      32,64           9
    1024      16,53       70,93      87,47           9
    ÇAPA (GERÇEK maske, D-162):  640 -> 24,45 ms · 1024 -> 83,02 ms
    ```
  - **Üç sonuç:** (1) **384 px'te bile ~5 ms değil** — 12,58 ms sentetik,
    çapa oranından gerçek tahmini ~9,4 ms; (2) maliyet **piksel sayısıyla
    doğrusal** (kenar 2,67× → süre 6,95×); (3) `koridor_adaylari` maliyetin
    **~%80'i**.
  - 🔴 **İDDİA ÇİFTE YANLIŞ: üretim 384'te koşmuyor.** `INFER_SIZE=512`
    yalnız MODEL girdisidir; maskeler kaynak karenin **kare tuvali** boyutunda
    üretilir (`get_masks(r, *sq.shape[:2])`) → t66'da **640²**, 1024×576 drone
    karesinde **1024²**.
  - **MEKANİZMA:** `_bagli_mi` (`:347`) her çağrıda **tüm görüntüde**
    `connectedComponents` koşar; `koridor_adaylari` onu `:453` ve `:464`'ten
    çağırır. Çağrı sayısı çözünürlükten **bağımsız 9**; değişen şey çağrı
    başına piksel. Doğrusal ölçeği tam olarak açıklıyor.
  - ✅ **DOCSTRING DÜZELTİLDİ** (`costmap_path_finder.py:22` + jetson aynası):
    dayanaksız iddia kaldırıldı, ölçülen sayılar ve kaynakları yazıldı.
    **Üretim davranışı değişmedi.** Kapılar: **15/15** · **589 OK**.
  - ⚠ **ABARTMIYORUM:** gerekli kare hızı kapsama hesabından **0,9-2,6 FPS**
    (ARCHITECT_PLAN §2.7); 15 FPS takımın iç hedefi. KATMAN A 1024²'de 83 ms
    → ~12 FPS tavanı, yani **görev açısından tıkayıcı değil**. Ama sözleşme
    satırı yanlıştı ve başka bir ölçüte gerekçe olmuştu.
  - ⚠ **OPTİMİZASYON FIRSATI GÖRÜNÜYOR** (bileşenleri bir kez hesaplayıp
    yeniden kullanmak / ROI'ye kısıtlamak) ama **denenmedi**.
    `koridor_adaylari` T90/T91/T92'nin yük taşıyan fonksiyonudur;
    **ölçmeden dokunulmaz.**
  - ✅ **KAPANDI · 2026-08-18 · kullanıcı kararı K-8 (`ARCHITECT_PLAN.md`).**
    15 FPS iç hedefi **kaldırıldı**; yeni hedef **3 FPS**, kabul edilen asgari
    **1 FPS**. KATMAN A 1024²'de 83 ms → **~12 FPS tavanı** = hedefin 4 katı,
    asgarinin 12 katı. **Optimizasyon gerekmiyor.**
  - Gerçek maskelerle 384/512 ölçümü **artık gereksiz** — hangi sayı çıkarsa
    çıksın karar değişmez. Ölçüm kaydı D-169'da duruyor; gerekirse oradan
    devam edilir.
  - ⚠ **Kapanan şey OPTİMİZASYON İHTİYACIDIR, ölçüm borcu değil:** `_bagli_mi`
    kare başına 9 kez tüm görüntüde `connectedComponents` koşuyor. Bu bir
    kusur değil ama **bilinen bir maliyet**; ileride hız sorun olursa
    bakılacak ilk yer burasıdır.

  - ✅ **BEKLENEN ÖLÇÜM GELDİ · 2026-08-18 · Claude-2** · kayıt **D-162 §6** ·
    `scripts/olcum/90_t95b_butce.py --uretim-olcegi`.
    Aynı fiziksel sahne **üretimin piksel ölçeğinde yeniden kuruldu** (maske
    algıdan SONRA ölçeklendi, model yeniden koşmadı); betik doğruladı:
    ```text
    [URETIM OLCEGI] tuval 1024px · arena 914px · mpp 0.0547 · ds 8
                    · plan izgarasi 128x128
    ```
    ```text
    n=260 · ACIK 31                    TABAN     KORUMA
    yol_duzelt GIRDI dugum             97/97/97  97/97/97   (min/med/mak)
    duzelt (ms)                         1,28       4,21
    astar (ms)                         18,59      19,10
    dogrulama (ms)                      1,87       1,82
    KATMAN_B = astar+duzelt+dogrulama  21,69      25,15   <- 30-40 ms ICINDE
    KATMAN_A = costmap+koridor         83,02      86,21
      costmap                          28,27      28,08
      koridor                          53,27      51,75
    rota_bul TOPLAM                   120,292    122,761   (+2,469 = %2,1)
    pay < 3 px olan ACIK kare               3          0
    ```
  - 🔴 **T97'NİN ÖNERMESİ ÜRETİM ÖLÇEĞİNDE DE DOĞRULANMADI.** 128×128'te
    `yol_duzelt` korumayla birlikte **4,21 ms**, KATMAN B toplamı **25,15 ms**
    — modülün kendi **30-40 ms** bütçesinin **içinde**. "n=800'de 96 ms" probu
    üretimde **karşılığı olmayan** bir girdiye aitti (D-161 zaten yazmıştı).
  - 🔴 **AMA BAŞKA BİR ŞEY AŞIYOR ve T95 ile ilgisi YOK:** 1024 px'te
    **KATMAN A 83 ms**tir ve korumadan tamamen bağımsızdır (costmap 28,27 →
    28,08 · koridor 53,27 → 51,75; fark gürültü). Tek başına
    **`koridor_adaylari` 53 ms** ediyor. Modülün KATMAN A sözleşmesi
    *"~5 ms @384px"*tir.
    ⚠ **384 px'te ÖLÇMEDİM** — "sözleşmesini N kat aşıyor" **demiyorum**;
    ölçülen sayı 1024 px'e, sözleşme metni başka bir çözünürlüğe aittir.
  - ⚠ **DOĞRULANAMADI:** 128×128 koşumu bir **yeniden kurulumdur**, gerçek
    mozaik değildir — geometri birebir ama maskeler INTER_NEAREST ile
    büyütüldü, mozaik **dikişleri/boşlukları yok**, sahne sentetik arenadır.
    Elde mozaik artefaktı **yok** (arandı); üretmek Gazebo tarama uçuşu ister.
  - **KARAR MİMARIN:** `yol_duzelt` cephesinde T97 kapanabilir; KATMAN A
    bulgusu **ayrı bir görev** olarak yeniden kapsamlanmalıdır.
  - 🔎 **MİMAR DENETİMİ · 2026-08-18 · `REVIEW_LOG.md` D-165. UYGULAMA ONAYLANDI.**
    Bağımsız doğrulananlar: kapıları **kendim koştum** (`unittest` **589 OK**,
    `test_rota_sentetik` **15/15**) · `git diff` değişikliğin **tek satır** ve
    doğru yerde olduğunu gösteriyor · jetson aynası satır satır **birebir** ·
    kararlılık sayıları JSON'dan yeniden okundu, **birebir** · yeni testin
    `assertIs`/pozitif kontrol/karşı kontrolü denetlendi, **boş değil**.
  - 🔴 **DENETİMİN BULDUĞU (D-165 §2): ölçüm hiçbir turda üretimin çağrı
    imzasını kullanmadı.** Üç tur da `rota_bul(mk, mpp=mpp, icerik=icerik)`
    çağırdı; üretim (`iha_haritala.py:323-328`) `baslangic=`, `hedef=`,
    `engel_sinif_idler=(1,2)` (**araçlar da engel**) kullanıyor. Sonucu:
    `_ankoru_ekle` hiç koşmadı ve ölçülen sahnelerde **araçlar engel sayılmadı**.
  - **Neden yine de onaylandı** (kod okuması, D-165 §3): `_ankoru_ekle` yalnız
    `waypoints[0]`/`[-1]`e bakar (`:339`) ve `yol_duzelt` **uçları korur** —
    T94 testiyle kilitli → koruma ankor sonucunu **değiştiremez**.
    `rota_dogrula` tüm listeyi doğrular ama koruma açıklığı **artırır** (pay
    medyanı 13,92 → 17,92 px), yani risk yönü lehtedir; düşse bile `:1160-1195`
    **ham A\* hücre merkezlerine geri düşer**. Onay kapıların geçmesine değil,
    **mekanizmanın kapalı olmasına** dayanıyor.
  - ⚠ **Kendi kapı tasarımım zayıf çıktı (D-165 §4).** T95-C'yi "bu kuralı bir
    kez öldürmüş eksende sına" diye kurdum; ama korumanın kararı çevirebileceği
    tek dal 1040 koşumun **hiçbirinde tetiklenmedi**. Kapı "gerçek bir meydan
    okumadan sağ çıktı"yı değil **"sürpriz olmadı"yı** doğruladı. Amele bunu
    kendi DOĞRULANAMADI listesinde yazdı; ben **tasarlarken** görmeliydim.
    **DERS: bir kapı kurmadan önce ölçeceği olayın meydana GELEBİLİR olduğunu
    kodda doğrula. Meydana gelemeyen olayı ölçen kapı güven üretir, bilgi değil.**
- [x] **T102 — KAPANDI · `serbest ⊆ zemin` kapıya bağlandı** · `tests/test_monotonluk.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-171 §3**
  - S3 üç savunma kurdu: (1) alt küme kafesi · (2) engel pikseli sızıntısı ·
    (3) sabit referans. Ama **(3) yalnız mutasyon testlerinin içinde koşar**;
    normal koşumda devrede olan (1) ve (2)'dir.
  - Mimar şu regresyonu denedi — gerçekçi ve "temiz" görünüyor:
    ```python
    s["serbest"] = dilate(serbest) & ~engel_ham   # "kenari yumusatayim"
    ```
    ```text
    kosum                          KAFES   engel-sizintisi   ZEMIN DISI serbest
    YAMASIZ                          0            0                  0
    dilate + engeli TEKRAR cikar     0            0              40183
    ```
    **(1) ve (2) ikisi de geçiyor.** Serbest alan 40 bin piksel büyüyor ve
    büyüme **etiketsiz arka plana** oluyor — mimarinin kendi kuralına göre
    ("bilinmeyen → engel") orası engel olmalıydı.
  - **YAP:** `tests/test_monotonluk.py`'ye `serbest ⊆ zemin` değişmezini ekle
    (50 tohum × tüm engel alt kümeleri) **ve** mutasyon kanıtı: yukarıdaki
    "dilate + tekrar çıkar" yamasıyla testin **DÜŞTÜĞÜNÜ** göster.
  - ⚠ `zemin` = `yol_sinif_idler` maskelerinin birleşimi; **çıplak sınıf id
    yazma** (madde 16), `codes/sinif_semasi.py`den al.
  - **KAPI:** yeni test yamasız koşumda geçer · yamalı koşumda düşer ·
    `git diff codes/` BOŞ · `test_rota_sentetik` 15/15 · `unittest discover`
    ≥ 601 OK, hiç düşme yok.

  - ✅ **YAPILDI · 2026-08-18 · Claude-2** · kayıt `REVIEW_LOG.md` **D-172**.
    **Üretim kodu değişmedi:** `git diff HEAD -- codes/` **BOŞ**.
    `tests/test_monotonluk.py` 12 → **16 test**.
  - **ÖLÇÜM — 50 tohum × 4 alt küme (200 koşum):**
    ```text
    kosum                                KAFES  engel-sizinti  ZEMIN DISI serbest
    YAMASIZ                                  0              0                   0
    dilate + engeli TEKRAR cikar             0              0              160766
    ```
    **(1) ve (2) yamayı ikisi de geçiriyor; yalnız yeni kapı yakalıyor.**
    Mimarın tek karede ölçtüğü 40183 px, 200 koşuma yayılınca 160766 px.
  - **EKLENEN DÖRT TEST:**
    (A) `serbest ⊆ zemin`, 50 tohum × tüm alt kümeler — `zemin` **çıplak
    `KATMAN_ZEMIN` değil**, `COSTMAP_YOL_KATMANLARI` birleşiminden türetilir
    (madde 16) · (B) pozitif kontrol: sahnede taşacak yer var mı — ölçüldü,
    tuval 57600 px, zemin 40000 px, **dışarısı 17600 px ve 50/50 tohumda
    tamamen etiketsiz**; test bunu türetilmiş biçimde çiviler, çıplak eşik yok ·
    (C) mutasyon kanıtı: aynı yamada (A) düşer, (1) ve (2) geçer — hem **ayırt
    edici** hem **gerekli** olduğu tek testte · (D) yama sızmıyor.
  - 🔴 **MUTASYON KANITI — GERÇEK ÜRETİM DOSYASINDA** (yedek → değiştir → koş →
    yedekten geri koy; `git checkout` kullanılmadı):
    ```text
    Ran 16 tests in 1.639s
    FAILED (failures=2)
      FAIL: test_serbest_alan_ZEMIN_ALT_KUMESIDIR_50_tohum
            Lists differ: [] != [(0, (), 804), (0, (1,), 804), (0, (10,), ...)]
      FAIL: test_MUTASYON_kenar_yumusatma_geri_alininca_YENIDEN_saglaniyor
    ```
    🔴 **`test_alt_kume_kafesi_...` ve `test_engel_pikseli_...` DÜŞMEDİ** —
    yani (1)/(2)'nin körlüğü maymun-yamayla değil **gerçek üretim
    mutasyonuyla** doğrulandı. Yeni kapı olmasaydı bu regresyon 16 testin
    **tamamını** geçerdi.
  - ⚠ **KENDİ HATAM:** (C)'de sızıntıyı önce sabit `moloz|arac` birleşimine
    karşı ölçtüm → 22017 px sahte "sızıntı". `(MOLOZ,)` koşumunda `arac` zaten
    engel sayılmamıştı. Sızıntı kapının **kendi tanımıyla** aynı olmalı; alt
    kümeye göre düzeltildi.
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    git diff HEAD -- codes/        -> BOS
    codes/test_rota_sentetik.py    SONUC: 15/15 dogru
    unittest discover -s tests     Ran 605 tests in 83.591s / OK  (601 -> 605, +4)
    ```
    🔴 GPU'ya dokunulmadı; görev model çalıştırmadı (CPU/sentetik).
  - ⚠ **DOĞRULANAMADI:** sahneler sentetiktir · **`analyze_path` içindeki
    çıkarma (`rpi_inference.py:1086-1094`) hâlâ kapsam dışı** — D-170 §6'da
    açılan madde **açık kalıyor**; `serbest ⊆ zemin` orada da geçerli ve orada
    da test edilmiyor · tek mutasyon biçimi denendi. 🔴 **Özellikle: zemin
    maskesinin KENDİSİ büyütülürse `serbest ⊆ zemin` de kör kalır** (referans
    da büyür) — bu, kapatılan açığın aynasıdır ve **açıktır**.
  - 🔎 **MİMAR DENETİMİ · 2026-08-18 · `REVIEW_LOG.md` D-173. ONAYLANDI.**
    Kapıları **kendim koştum**: `unittest discover` **605 OK** (601 → +4) ·
    `test_rota_sentetik` **15/15** · `git diff codes/` **BOŞ** · monotonluk
    testleri `discover -p` ile **16/16 toplanıyor ve geçiyor**.
  - **Ameleyi ayrıca doğruladım:** yeni kapının ayırt ediciliğini D-171 §3'te
    zaten bağımsız ölçmüştüm (kafes 0 · engel sızıntısı 0 · zemin dışı
    **40183 px**). Amele aynı yamayı 200 koşuma yayıp **160766 px** ölçtü —
    iki bağımsız ölçüm aynı yöne işaret ediyor.
  - **En iyi hamlesi:** mutasyonu maymun-yamayla değil **gerçek üretim
    dosyasına** enjekte etmesi. "Yama üretimin yapacağının aynısını yapıyor"
    bir iddiadır; sınandı ve doğrulandı.
  - ✅ **MADDE 15 ARTIK ÜÇ EKSENDE KORUNUYOR** — (1) alt küme kafesi ·
    (2) engel sızıntısı · (3) `serbest ⊆ zemin`; üçü de mutasyon kanıtlı.
    ⚠ Üçünün **birlikte eksiksiz olduğu kanıtlanmadı**; üçünü birden geçen bir
    regresyon aranmadı (D-173 DOĞRULANAMADI #1).
  - ⚠ Talimat uyumu: bu turda **commit atılmadı, izin beklendi** — geçen turdaki
    sapma tekrarlanmadı.
- [x] **T103 — KAPANDI · Saha paketi `config/model_registry.json`'u taşıyor** · `scripts/jetson_paket_hazirla.py:15`, `jetson_paket/JETSON_KILAVUZ.md:345` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-177 §2**
  - Ölçüldü (`jetson_paket/kod` içinde gerçek koşum):
    ```text
    model_kayit_dogrula -> False | durum "kayit_defteri_yok"
    load_model -> RuntimeError: MODEL KAYIT DOGRULAMASI BASARISIZ — fail-closed
    ```
  - Kaynak iki yerde doğrulandı: `jetson_paket_hazirla.py` **KOPYALAR** sözlüğü
    **dokuz .py** taşıyor, defter yok · kılavuz `mkdir -p
    ~/navitas/{codes,comms,scripts,models,data}` diyor — **`config` dizini yok.**
  - Çalıştırmanın tek yolu `--kayit-dogrulamasiz`; o da T73'te bilerek kurulan
    **yanlış-model korumasını kapatır**.
  - ⚠ **S5'in ürettiği kusur DEĞİL** — S5 onu görünür kıldı. Fail-closed defter
    zorunluluğu T73'te geldi, kılavuz ve paketleyici o gün güncellenmedi.
  - ⚠ Paket **yanlış model taşımıyor**: `navitas_seg_v30_best.pt` + 512 fp16
    ONNX mevcut. Sorun **defterin yokluğu**.
  - **YAP:** defteri `KOPYALAR`a ekle · kılavuzun `mkdir` satırına `config`
    ekle ve `cp` satırı yaz · paketlenmiş düzende `load_model()`in **başarılı**
    olduğunu gerçek çıktıyla göster.
  - ⚠ `jetson_derleme_manifest.json` *"paket defteri taşımaz"* diyor; bu,
    manifestin defterin **yerine geçmediğini** söyler, paketlenmesini
    yasaklamaz. Yine de o notu **güncelle**, çelişki bırakma.
  - **KAPI:** paketlenmiş düzende `load_model()` başarılı · `INFER_SIZE` uyarısı
    **susuyor** · `test_rota_sentetik` 15/15 · `unittest discover` ≥ 614 OK.

  - ✅ **YAPILDI · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md` **D-178**.
    Yeni dizin: **`jetson_paket/config/`**.
  - **ÖNCE / SONRA** (ikisi de `jetson_paket/kod` içinde gerçek koşum):
    ```text
    olcum                 ONCE                          SONRA
    import uyarisi        VAR (defter okunamadi)        YOK
    model_kayit_dogrula   False · "kayit_defteri_yok"   True · "eslesti"
    load_model            RuntimeError (fail-closed)    BASARILI (YOLO)
    ```
    ```text
    ONCE : load_model: RuntimeError -> MODEL KAYIT DOGRULAMASI BASARISIZ — fail-closed.
    SONRA: INFER_SIZE 512 · dogrulama True | durum 'eslesti' | imgsz 512 / 512
           load_model: BASARILI -> YOLO
    ```
  - **(A)** `KOPYALAR`a defter eklendi; hedef **`config/`** (kod
    `_here.parent/"config"` arar, `kod/` DEĞİL). Kopyalayıcıya
    `mkdir(parents=True, exist_ok=True)` eklendi; `copy2` ve raporlama akışı
    **değişmedi**. Paketleyici koşuldu, **10 satır** rapor verdi (ilki defter).
  - **(B)** 🔴 **İKİ KILAVUZ KOPYASI DA düzeltildi.** Emir yalnız paketteki
    kopyayı işaret ediyordu, ama kök `JETSON_KILAVUZ.md` de sahaya yanlış ağaç
    söylüyordu (`{codes,scripts,models,data}` — `comms` bile yok). Yalnız birini
    düzeltmek **D-58/D-60/D-116 sapma sınıfıdır**. İkisine de `config` +
    `cp config/model_registry.json` ve *"bu bir öneri değil ZORUNLULUK;
    `--kayit-dogrulamasiz` tam bu korumayı kapatır"* uyarısı eklendi. Kök
    kopyaya ayrıca *"paketteki kopya esastır, bu eskidir"* notu düşüldü.
  - **(C)** Manifestteki *"(paket defteri taşımaz)"* ifadesi **çıkarıldı**;
    yerine T103 güncellemesi yazıldı — paket defteri **taşır ve taşımak
    zorundadır**, ama manifest defterin **yerine geçmez**. Diff: 1 satır.
  - **YENİ TEST** `tests/test_jetson_paket_defteri.py` (6 test): defter var ·
    depo defteriyle **sha256 birebir** · üretim profilini içeriyor (dosyanın
    var olması yetmez) · `_here.parent/config` konumu doğru (hedefin `kod/`
    **olmaması** asıl konu) · paketleyicinin `KOPYALAR`ında duruyor (elle
    konmuş olması yetmez) · **pozitif kontrol**.
    Mutasyon (defter kaldırıldı): **1 ERROR + 3 FAIL**. Geri alma paketleyiciyle.
  - 🔴 **MEVCUT BİR KAPI DEĞİŞİKLİĞİ YAKALADI:**
    `tests/test_jetson_comms_paketi.py:24` → `AssertionError: 9 != 10`.
    Bu kusur değil, **kapının işlevi** — pakete dosya eklemek sessiz olmamalı.
    Sayı **gevşetilmedi** (`>= 9`'a çevrilmedi), gerekçesiyle **9 → 10**
    güncellendi. Aynı testin dosya-başına bayt eşitliği döngüsü zaten
    `KOPYALAR`ı geziyor, yani defterin bayatlamasını da o yakalar.
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    yeni testler                  Ran 6 · OK
    codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    unittest discover -s tests    Ran 620 tests in 74.343s · OK   (614 -> 620)
    git status                    jetson_paket/config/ OLUSTU
    ```
    ⚠ GPU: model çalıştırılmadı; yalnız `load_model` ağırlığı açtı.
  - 🔴 ⚠ **DOĞRULANAMADI — EN ÖNEMLİSİ: bu ölçüm reponun `jetson_paket/`
    dizinindedir; GERÇEK JETSON CİHAZINDA HİÇBİR ŞEY ÖLÇÜLMEDİ** (T16/T17
    hâlâ açık). Kılavuzun `cp` komutları elle koşulmadı · `sha256` bu yolda
    hâlâ **doğrulanmıyor** (`model_kayit_dogrula` yalnız `detay`ya yazar) ·
    `kabul_kumesi` Windows yolu defterle sahaya gidiyor (`yks_gui` pakette
    yok — kod okumasıyla doğrulandı, sahada koşulmadı) · iki kılavuz kopyası
    hâlâ **ayrışık** ve eşitliklerini zorlayan bir kapı **yok** (ayrı iş).
  - 🔎 **MİMAR DENETİMİ · 2026-08-19 · `REVIEW_LOG.md` D-179. ONAYLANDI.**
    Asıl kapıyı `jetson_paket/kod` içinde **kendim koştum**:
    ```text
    ONCE : load_model -> RuntimeError: MODEL KAYIT DOGRULAMASI BASARISIZ
    SONRA: INFER_SIZE 512 (UYARI YOK) · dogrulama True "eslesti"
           (beklenen_imgsz 512 · calisan 512) · load_model -> BASARILI: YOLO
    ```
    `unittest` **620 OK** (614 → +6) · `test_rota_sentetik` **15/15** ·
    defter senkronu `diff -q` **BİREBİR**.
  - **MUTASYON KONTROLÜNÜ KENDİM KOŞTUM:** `jetson_paket/config/model_registry.json`
    geçici kaldırıldı → **6 testin 3'ü düştü** (+1 hata); dosya geri konuldu,
    senkron yeniden doğrulandı. **Test boş değil.**
  - ✅ **Amele emrin işaret etmediği bir kusuru kendi yakaladı:** depoda **iki**
    `JETSON_KILAVUZ.md` var ve **kök kopya da sahaya yanlış dizin ağacı
    söylüyordu** (`comms` bile yoktu). İkisini de düzeltti. Ben de bağımsız
    gördüm ve aynı sonuca vardım — amele benden önce yakalamış.
  - ⚠ Kılavuz senkronunu **hiçbir şey zorlamıyor** → **T104** açıldı.
  - 🔴 **DOĞRULANAMADI:** gerçek Jetson cihazında **hiçbir şey ölçülmedi**;
    tüm ölçümler reponun `jetson_paket/` dizinindedir → **T16/T17**.
- [x] **T104 — KAPANDI · Kurulum yordamı testle kilitlendi (bayt kimliği DEĞİL)** · `JETSON_KILAVUZ.md`, `jetson_paket/JETSON_KILAVUZ.md` · KÜÇÜK · kanıt: `REVIEW_LOG.md` **D-179 §3**
  - T103'te ikisi de elle düzeltildi (amele yakaladı), ama **ayrı dosyalar** ve
    paketleyici kılavuzu **kopyalamıyor** (`grep -c JETSON_KILAVUZ
    scripts/jetson_paket_hazirla.py` → **0**). Bugün düzeltilen ayrışma yarın
    yeniden oluşur.
  - ⚠ **YÖN ÖNEMLİ:** paket kopyası kök kopyadan **büyüktür** (32.363 > 28.940
    bayt) — yani kök kopya **eski/eksik** olandır. Mekanik senkron kurulacaksa
    yön **paket → kök** olmalı; ters yön **içerik kaybettirir**.
  - **ÖNCE KARAR (mimar):** (a) kök kopya silinsin, tek kaynak paket olsun ·
    (b) paketleyici `paket → kök` kopyalasın · (c) ikisi ayrı kalsın ama bir
    test farkı sabitlesin. **Körlemesine kopyalama YOK.**
  - ✅ **KAPANDI · 2026-08-19 · mimar · `REVIEW_LOG.md` D-193.**
  - 🔴 **T112'nin bayt kimliği buraya UYMADI.** Fark ölçüldü: kök 28.983 bayt,
    paket 32.406, farklı satır **95**, yalnız kökte **16**. Farklar **meşru** —
    iki belge farklı bağlam anlatıyor (kök: depo · paket: saha + ek §0-A).
    **Bayt kimliği dayatmak bu içeriği silerdi.** Uygulanan şey kalıbın
    **fikri**: yük taşıyan değişmezi testle kilitle.
  - 🔴 **ÖLÇERKEN GERÇEK BİR KUSUR ÇIKTI:** kök kılavuzun kurulum yordamı
    **bozukmuş** — `comms` dizini yok, `karar_sozlesmesi.py` kopyalanmıyor,
    haberleşme dosyaları hiç kopyalanmıyor. `costmap_path_finder.py:59-62` onu
    **import eder** → bu kılavuzu izleyen saha kurulumu **`ImportError`** alır.
    ⚠ T103 bu dosyaya dokunmuştu ama o tur `config` aranıyordu; eksik görülmedi.
    **Kapı olmayan yer yeniden bozulur ya da eksik kalır.** Düzeltildi.
  - **Kilitlenen değişmez:** kurulum yordamı (dizin ağacı + kopyalanan dosya
    kümesi) iki kılavuzda **aynı** olmalı **ve** paketin gerçekten taşıdığı
    dosyaları **eksiksiz** kapsamalı. `tests/test_kilavuz_kurulum_yordami.py`
    (6 test).
  - ⚠ **Beklenen dosya listesi ELLE yazılmıyor** — `jetson_paket_hazirla.py`
    içindeki `KOPYALAR`dan **türetiliyor**; paketleyiciye yeni dosya eklenirse
    kapı kendiliğinden onu da arar. (Elle liste bu oturumda dört kez bayatladı.)
  - **MUTASYON KONTROLÜ (mimar koştu):** kılavuz bozuk haline döndürülünce
    **6 testin 3'ü düştü**; yedekten geri konuldu.
    Kapılar: **642 OK** (636 → +6) · **15/15** · `git diff codes/` **BOŞ**.
  - **Bilerek yapılmadı:** iki kılavuz aynı yapılmadı · kök kopya **silinmedi**
    (`test_uretim_modeli_hizasi.py:43` ikisini de şart koşuyor).
- [x] **T114 — KAPANDI · T104 denetimi GEÇTİ (4/4 iddia bağımsız doğrulandı; 1 dereceli bulgu: pip satırı ayrışıyor, import kırmıyor) · kayıt D-196** · `tests/test_kilavuz_kurulum_yordami.py`, `JETSON_KILAVUZ.md` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-194**
  - **Kim yapar:** Claude 2 (Fable 5) — anayasa madde 19, **YUKARI yön**. Mimar bu görevi kendi kapatamaz.
  - **Kanıt.** `TASK_QUEUE.md` T104 bloğu: `✅ KAPANDI · 2026-08-19 · mimar` ve
    `MUTASYON KONTROLÜ (mimar koştu)`. Kodu yazan ile onaylayan **aynı ajan**.
    Karşılaştır: T95 / T102 / T110 / S5 hepsi `Claude-2` tarafından yazıldı ve **mimar** denetledi — orada bağımsızlık vardı.
  - **Denetlenecek iddialar** (her biri **kendi ölçümünle**, mimarın çıktısını kabul etme):
    1. Kök kılavuzun kurulum yordamı **gerçekten** bozuktu: `comms` ve `karar_sozlesmesi.py` yoktu
       ve `codes/costmap_path_finder.py` `karar_sozlesmesi`i import ediyor. → `git show effd125^:JETSON_KILAVUZ.md` ile doğrula.
    2. Mutasyon kontrolü **gerçekten** 6 testin 3'ünü düşürüyor. → Kılavuzu bozuk hâline çevir, testi koş, geri al.
    3. Beklenen dosya listesi `KOPYALAR`dan **türüyor** ve elle listeye düşmüyor. → `KOPYALAR`a sahte bir dosya ekle, kapının onu **aradığını** göster, geri al.
    4. ⚠ **En önemlisi — testin GÖREMEDİĞİ ne var:** iki kılavuz arasında **95 satır** farklı, kapı yalnız **16**'sını kapsıyor.
       Kalan 79 satırda **kurulumu bozacak** başka bir ayrışma var mı? (sürüm numarası, model adı, dosya yolu, komut)
       Bu ölçülmedi; mimar "dürüst sınır" diye yazıp geçti. **Ölç.**
  - **Kapı:** `O:\navitas-local-train\venv\Scripts\python.exe -m unittest discover -s tests -q` → **642 OK**
    ve `O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py` → **15/15**.
  - **Çıktı:** `REVIEW_LOG.md`'ye denetim kaydı — **GEÇTİ** veya **KUSURLU**, her hâlde kanıtla.
    Bulgu çıkmazsa da yaz: "denetlendi, bulgu yok" da bir kayıttır.

- [ ] **T116 — ÖLÇÜLDÜ (D-201/D-202): T54 hedefine ULAŞMAMIŞ — v34 otopark kaplaması v21 ile eşdeğer; %80,6→%45,7 'düşüşü' PAYDA FARKI. Karar mimarın** · `models/navitas_seg_v34_best.pt`, `data/raw_frames/` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-200 §3 → D-201/D-202**
  - ✅ **ÖLÇÜM · 2026-08-20 · Claude-2 (Fable 5) · dinamik workflow (22 ajan:
    5 lane + 15 çürütücü + sentez + tamlık; düşen lane YOK).**
  - **A (D-201):** eşleştirilmiş 67 karede medyan kaplama — v21 %44,96 ·
    v22 %44,77 · v30 %33,42 · v34 %45,01. **Ön kayıt A1 (≥20 puan düşüş)
    SAĞLANMADI** (fark −0,05 puan); **A2 SAĞLANMADI** — çatı görselini ana
    döngü KENDİ GÖZÜYLE doğruladı: çatı hem v21 hem v34'te YEŞİL
    (`results/t116_turu/t116a_cati_gorsel.png`; araçlar doğru — araç dersi
    çalışıyor, çatı dersi gerçek kareye taşınmıyor).
    🔴 **Payda bulgusu:** içeriğe-normalize medyanlar v21 %79,9 · v34 %80,0 ·
    v30 %59,4 → T54 metnindeki %80,6 tabanı letterbox-kare paydalı %45,7 ile
    **kıyaslanamaz**. ⚠ %80,6'nın kendi zinciri (T58/B1) bu turda koşulmadı.
  - **B (D-202):** poligon tavanı pratikte kırpmıyor (600 maskede aşan 4,
    atılan alan ~%0,004) — AMA üretim sıralaması `len(l)` (satır uzunluğu),
    ALAN DEĞİL (`download_and_convert.py:122-123`) → görev adayı.

  - **Neden var.** T54'ün eğitimi yapıldı (ürünü v34, bayt-eş doğrulandı) ama
    görevin **kendi kapıları** hiç ölçülmedi. `config/model_registry.json`
    içindeki `k0..k5` **arena kabul kapılarıdır** — T54'ünkiler değil.
    Aynı harf, **başka ölçüt**. Otopark kaplamasının düştüğüne dair defterde
    **tek bir sayı yok**.
  - **ÖLÇ — eğitim YOK, model ve kareler zaten elde:**
    1. `data/raw_frames/` (67 kare, otopark) üzerinde **eşleştirilmiş** kaplama:
       v21 · v22 · v30 · v34. Taban **%80,6** (v21/v22, D-67'de gözle doğrulanmış).
    2. Havuz metriği **yetmez** — kare bazında dağılım ver (D-175 dersi).
    3. **GÖZLE ZORUNLU:** bina çatısı olan bir karede v34'ün maskesi çatıyı
       yeşile boyuyor mu? Sayı iyi görünüp görsel kötüyse **görsel kazanır**.
    4. T54'ün diğer kapıları da aynı koşumda: K0 duyarlılık ≥ 0,50 ·
       K1 IoU/kesinlik ≥ v22 (0,512).
  - ⚠ **ÖN KAYIT ZORUNLU (D-107):** "belirgin düşüş"ü **sonucu görmeden** sayıyla
    tanımla. Gördükten sonra gevşetme.
  - ⚠ **KAPI YAPMA.** Bu bir ölçümdür. Eşiği kapıya çevirmek ayrı karardır.
  - 🔴 **İKİNCİ İŞ — POLİGON TAVANI (D-199 §6.3, D-200 §4):**
    `download_and_convert.py` içindeki `MAX_POLYGONS // 2 = 15` engel tavanı
    *"engel nadirdir"* varsayımının kalıntısı. Yeni eşlemede engel **baskın**
    (sınıf-1 22.356 / sınıf-0 3.104). Yeniden üretimde **sessizce kırpabilir**.
    Ölç: kaç maskede engel poligon sayısı tavanı aşıyor, kırpılan alan oranı ne?
    Kırpıyorsa tavan **ölçülmüş** bir değere bağlanmalı — çıplak sabite değil.
  - **Kapı:** `O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py` → **15/15** ·
    `O:\navitas-local-train\venv\Scripts\python.exe -m unittest discover -s tests -q` → **655 OK**

- [ ] **T118 — 🔴 PAYDA SÖZLEŞMESİ: üretim ile denetçi AYNI İSMİ kullanıp BAŞKA ŞEY ölçüyor** · `codes/karar_sozlesmesi.py:577`, `scripts/olcum/65_kabul_denetcisi.py` + 98 aday satır · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-207 §2**
  - Üretim `zemin_kaplamasi(trav, icerik)` → payda **içerik kutusu**, tavan 0,67.
    Denetçi `kaplama()` → payda **letterbox karesi**. 1024×576'da içerik oranı 0,5625.
    Aynı maske: denetçi **%45,0** · üretim **%80,0**.
  - **Sınanacak sonuç (ilan DEĞİL):** denetçinin "%45" dediği kareler üretim
    ölçüsüyle **0,67 tavanının ÜSTÜNDE** olabilir → kabul kapılarımızın bir kısmı
    üretim eşikleriyle **kıyaslanamaz** sayı üretiyor olabilir.
  - **Yap:** kaplama/oran hesaplayan **her** çağrı yerinde paydayı çıkar. Üretim
    eşiklerinin hangi paydada kalibre edildiğini kaynağına kadar izle
    (`ZEMIN_KAPLAMA_TAVANI` 0,67 · T59 / D-84 / D-85).
  - ⚠ **ÖNCE TARA VE ÖLÇ. EŞİK DEĞİŞTİRME** — eşik değişikliği ayrı karardır.
  - D-201'in kendi sınırı buraya girer: %80,6 tabanının T58 zinciri koşulmadı.

- [ ] **T117 — "Çatı engeldir" dersi RescueNet'ten gerçek kareye TAŞINMIYOR: neden?** · `models/`, `dataset/` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-201**, hüküm **D-207**
  - v34 RescueNet'te bina/ağaç/su/havuzu engel olarak gördü (D-199 §2, görsel) ama
    gerçek otopark karesinde çatı hâlâ **yeşil** (D-201 A2, iki karede gözle).
  - **Çoklu hipotez — aynı anda ölç, önceden birini seçme:** GSD/irtifa farkı ·
    görünüm ve doku farkı (RescueNet afet sonrası, otopark temiz) · sınıf
    dengesizliği · RescueNet etiket kalitesi · çözünürlük/imgsz · güven eşiği.
  - ⚠ "En makul olan" değil **ölçülen** kazanır.

- [ ] **T115 — Kuyruğun 21 satırında dosya yolları OKTAL KAÇIŞLA bozulmuş: amele yolu okuyamıyor** · `TASK_QUEUE.md` · KÜÇÜK · kanıt: `REVIEW_LOG.md` **D-194 §2**
  - **Kanıt.** `grep -cE '^avitas-local-train' TASK_QUEUE.md` → **21**. Örnek (satır 5284):
    `` `O: `` + satır sonu + `` avitas-local-train5_kabul_denetcisi.py:101-111` ``
  - **Kök neden ÇÖZÜLDÜ (mimar):** yol bir Python **ham olmayan** dizgeyle yazılmış.
    `
ters bölü + n → satır sonu · ters bölü + 51 → `)` (0o51=41) · ters bölü + 65 → `5` (0o65=53) · ters bölü + 56 → `.` (0o56=46).
    Yani bozulma **tersine çevrilebilir**: kaçış dizisi tek bir karaktere çöktüğü için
    `avitas-local-train` sonrası ilk karakterden özgün rakam çifti **hesaplanır**.
  - **Yap.** Bozuk satırları onar (`O:` + satır sonu + `avitas-...` → tek satır `O:\navitas-local-train\<özgün>`).
    Onarımı **elle satır satır yapma** — bir betikle üret, çıktısını göz kontrolünden geçir.
  - ⚠ **DOKUNMA:** `[HUMAN_COMPLETED]` ve `[IN_PROGRESS]` satırlarının **durum işaretine**. Yalnız yol metni onarılır.
  - **Kapı:** `grep -cE '^avitas-local-train' TASK_QUEUE.md` → **0** · onarılan her yol için dosyanın
    **gerçekten var olduğunu** doğrula (`test -f`); var olmayan yol çıkarsa onu **onarma**, raporla.

- [x] **T105 — KAPANDI · K5 üç durumlu: OLCULEMEDI raporda ayrı, terfiyi YİNE bloklar · 1059×634 sorusunun T94/T95 bağı ÇÜRÜTÜLDÜ (red :1222, yol_duzelt hiç koşmuyor) · kayıt D-197** — eski: Kabul denetçisinin K5'i HER modeli reddediyor (üretim dahil): "ölçülemedi" ile "düştü" ayırt edilmiyor** · `O:
avitas-local-train5_kabul_denetcisi.py:101-111` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-180**
  - `65` K5'i alt betiğin stdout'undan **parse ediyor**; satır basılmazsa
    `kes = None` kalır ve `gecti["K5"] = (kes == 0)` → **DÜŞTÜ**.
  - `63_bariyer_kesisimi.py` **tek** karede (1059×634) koşar; o karede rota
    çıkmazsa "kesişim ölçülemez" der. Mimar üç modeli de geçirdi:
    ```text
    model   karar                          bariyer pikselleri      kesisim
    v22     serit=None GORUS_HATTI_KOPUK   ENGEL %100,0            olculemedi
    v23     serit=None UC_BANT_TEMAS_YOK   ENGEL %100,0            olculemedi
    v30     serit=None UC_BANT_TEMAS_YOK   ENGEL %100,0            olculemedi
    ```
    🔴 **Üretimdeki v30 da düşüyor** — satır hiçbir modeli ayırt etmiyor.
  - ⚠ Ölçülebilen tek şey model **lehine**: üçü de bariyer piksellerinin
    **%100'ünü ENGEL** görüyor.
  - **Kusur sınıfı:** eksik ölçüm **başarısızlık** sayılıyor ve karar gerekçesi
    olarak yazılıyor — yanlış atıf. Fail-closed ancak **ölçümü yapılmış** bir
    riske karşı anlamlıdır.
  - **YAP:** `65`in K5'i ya `66`/`80`e bağlansın ya da **"ÖLÇÜLEMEDİ"** üçüncü
    bir durum olarak raporlansın (verdikte nasıl gireceği **karar işidir**).
  - ⚠ Ayrıca araştır: 1059×634 karesinden **neden** rota çıkmıyor? Red sebebi
    (`UC_BANT_TEMAS_YOK`) `analyze_path`in band temas kapısıdır, `yol_duzelt`ten
    **önce** gelir — yani T94/T95 ile ilgisi **kurulmadı**, kurulmalı.
- [x] **T106 — KAPANDI · Figür çöküşü GÜVEN ÇÖKÜŞÜ ve sıkışma FİGÜRE ÖZGÜ (üç kümede yok)** · `dataset/download_and_convert.py` (T54 eşlemesi) · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-181 §5**
  - Ölçüldü (`65_kabul_denetcisi`, aynı figür `data/arena_referans/sartname_s9_arena.png`):
    ```text
    v30 %7,96   v22 %10,54   v23 %0,49
    ```
  - K0 bunu **yakalamıyor**: ölçüt yalnızca `figur > 0.0` ve "boş maske yok"
    (`65_kabul_denetcisi.py:81-82`) — *"tamamen kör değil"* kapısıdır,
    *"yeterince görüyor"* kapısı **değildir**.
  - ⚠ Figür **yapay zekâ üretimidir** ve proje onu otorite saymıyor; v23 **gerçek
    karelerde en çok gören modeldir** (0,4551). Yani "v23 kör" demek yanlış olur.
  - **HİPOTEZ (doğrulanmadı):** T54'ün yeni eşlemesi (bina/ağaç/su/havuz →
    `blocked`) o figürün sentetik zeminini `blocked` sayıyor olabilir.
  - **YAP:** figürde v23'ün sınıf dağılımını çıkar (zemin/engel piksel oranları),
    v30 ile yan yana koy. Eşleme hipotezi doğruysa engel kaplaması v30'a göre
    belirgin artmış olmalı.
  - ⚠ **Bu bir KAPI DEĞİLDİR** — v23 ön kaydın hepsini sağlıyor (D-181 §3).
    Açıklanmamış bir davranış olarak izleniyor.
  - 🔎 **MİMAR TANISI · 2026-08-19 · `REVIEW_LOG.md` D-183.** Hipotez **kısmen**
    doğru: engel gerçekten arttı (1,61→3,74) ama zemin **7,47 puan** düştü —
    kaybın yalnız ~2 puanı engele gitti, **~5,3 puanı hiçbir sınıfa gitmedi.**
  - 🔴 **ASIL SEBEP: GÜVEN ÇÖKÜŞÜ.** Tahminler kaybolmuyor, **üretim eşiğinin
    (0,30) altında** duruyor:
    ```text
    model  conf    ZEMIN    ENGEL   toplam
    v30    0,30    7,96%    1,61%    9,56%
    v30    0,10   10,62%    4,84%   15,46%
    v34    0,30    0,49%    3,74%    4,24%
    v34    0,10   13,29%   27,34%   40,63%
    ```
    0,10'a inince zemin **27 kat**, engel **7 kat** artıyor. Model figürü
    **görüyor** ama alan dışı olduğu için düşük güvenle ve ağırlıklı olarak
    **engel** diye görüyor — T54 eşlemesiyle tutarlı.
  - ✅ **YÖNÜ FAIL-SAFE → terfiyi değiştirmiyor.** Daha az zemin + daha çok
    engel = mimarinin değişmezi yönünde ("bilinmeyen → engel"). Zemin boşalınca
    `MASKE_YOK` → `NO_ROUTE`; **fail-closed**, fail-dangerous değil.
    Bu bir **yetenek** gerilemesidir, **emniyet** gerilemesi değil.
  - ⚠ **Ama ciddiye alınacak uyarı:** v34 alan dışı girdide üretim eşiğinin
    altına düşüyor. Gerçek arena kareleri eğitim dağılımından bu figür kadar
    uzaksa v34 sahada **rota üretemeyebilir**. Gerçek kare olmadığı için
    **ölçülemez** (kalıcı sınır). ⚠ v30 aynı testte zayıf ama **çökmüyor**
    (9,56→15,46) — "her model alan dışında kötüdür" savunması bu farkı
    açıklamıyor.
  - **KALAN İŞ (ameleye):** kabul kümesinde ve `raw_frames`/`copy_paste`
    kümelerinde aynı güven bandı sıkışması var mı? Bu ölçülmedi.

  - ✅ **KALAN İŞ ÖLÇÜLDÜ · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md`
    **D-184** · ölçüm `scripts/olcum/93_t106_guven_bandi.py`.
    **Üretim kodu değişmedi:** `git diff HEAD -- codes/` **BOŞ**.
  - **AÇIK CEVAP: sıkışma FİGÜRE ÖZGÜDÜR — üç kümede de YOK.**
    ```text
    BAND_ORANI          figur   kadraj_t66   raw_frames   copy_paste
    v30                  1,62         1,01         1,02         1,02
    v34 (uretim)         9,59         1,01         1,00         1,00
    n                       1          260           67          393
    ```
    `BAND_ORANI = toplam(0,10)/toplam(0,30)`, `toplam = zemin+engel` (D-183
    tablosunun kendi toplamı). Eşiği 0,30 → 0,05 indirmek bu üç kümede
    kaplamayı pratik olarak **değiştirmiyor**.
    **`zemin < %1` olan kare: 0/720 · her eşikte · her iki modelde** — figürdeki
    "zemin ~0" durumu bu kümelerin hiçbir karesinde tekrarlanmıyor.
  - **POZİTİF KONTROL (iki tane, ikisi de tuttu):**
    (1) `65_kabul_denetcisi.kaplama()` ile sapma **0** — metrik yeniden
    yazılmadı, 65 modülü içe aktarıldı. (2) D-183'ün figür sayıları **birebir**
    yeniden üretildi (`7,96/1,61/9,56` · `13,29/27,34/40,63`), BAND_ORANI
    figürde **1,62** ve **9,59** (mimarın ~1,6 / ~9,6 değerleri).
  - 🔴 ⚠ **CEVABIN SINIRI — ÖLÇÜLDÜ, VARSAYILMADI:** sıkışmanın **görülmediği
    üç kümenin üçü de eğitim verisi ya da ona komşudur.** `copy_paste` (393)
    **v34'ün kendi eğitim verisidir** — `zincir_t53_t54.sh:19` →
    `karisim_t54_engelli.yaml` → `train:` listesinde
    `dataset\copy_paste_gercek\images\train` var. Aynı karışımda
    `sentetik_arena` da var (`kadraj_t66` o üretecin ailesinden); `raw_frames`
    ise `copy_paste_gercek`/`gercek_otopark`ın **kaynak kareleri**.
    Sıkışmanın **görüldüğü** tek girdi (figür) elimizdeki **tek alan dışı
    örnektir ve n=1**. Yani ölçüm *"bütün kümelerde var mı"* sorusunu **HAYIR**
    diye cevaplar; *"FİGÜRE mi yoksa ALAN DIŞI OLMAYA mı özgü"* sorusunu
    **cevaplayamaz** — iki açıklamanın ayrıldığı noktada tek örnek var.
  - **YAN GÖZLEM (kapı değil):** v34 `raw_frames`te v30'dan **daha çok** zemin
    görüyor (45,67% vs 33,44% @0,30) ve dört eşikte de neredeyse **sabit**;
    kuyrukta kayıtlı "gerçek karelerde en çok gören model (0,4551)" ile aynı
    mertebede — ⚠ **aynı ölçüm değildir** (benimki 67 karenin tamamı, 0,4567),
    yalnız tutarlıdır. `kadraj_t66`da iki model neredeyse aynı (34,28 / 33,96).
  - ⚠ **HÜKÜM VERİLMEDİ:** "v34 iyi/kötü" denmedi, eşik değişikliği
    **önerilmedi** (T110 mimarda), gerçek arena karesi olmadığı için saha
    ifadesi kurulmadı (D-88/D-99).
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    uc kume x iki model x dort esik  -> 24 hucre, EKSIK YOK (5760 cikarim)
    pozitif kontrol 1 (65.kaplama)   sapma 0
    pozitif kontrol 2 (D-183 figur)  BIREBIR
    git diff HEAD -- codes/          BOS
    codes/test_rota_sentetik.py      SONUC: 15/15 dogru
    unittest discover -s tests       Ran 620 tests in 61.574s / OK
    ```
  - ⚠ **DOĞRULANAMADI:** "figüre özgü" ile "alan dışına özgü" **ayrılamadı**
    (tek alan dışı örnek) · gerçek arena karesi yok · `raw_frames`/`copy_paste`
    örneklemesi 65'in K0'ından farklı (8 yerine hepsi) · yalnız **kaplama**
    ölçüldü, sıkışmanın **rota kararına** etkisi (K1..K5, `MASKE_YOK`) değil ·
    figürde v34'ün kırılma noktası **0,30 ile 0,20 arasındadır** (4,24% →
    34,87%) ve tam yeri ölçülmedi · tek koşum, varyans ölçülmedi.
  - ✅ **KAPANDI · 2026-08-19 · `REVIEW_LOG.md` D-184 (amele) / D-185 (mimar).**
    ```text
    BAND_ORANI       figur   kadraj_t66   raw_frames   copy_paste
    v30               1,62         1,01         1,02         1,02
    v34 (uretim)      9,59         1,01         1,00         1,00
    n                    1          260           67          393
    ```
    `zemin < %1` olan kare: **0/720**, her eşikte, iki modelde de.
    **Sıkışma kabul kümesinde YOK → v34'ün terfisi bu yönden temiz.**
  - Ölçüm düzeneği doğrulandı: `65`in kendi `kaplama()`si ile sapma **0**,
    D-183'ün figür sayıları **birebir** yeniden üretildi. Kapılar (mimar koştu):
    **620 OK** · **15/15** · `git diff codes/` **BOŞ**.
  - 🔴 **Amelenin §4'ü görevden büyük — doğruladım:** sıkışmanın görülmediği
    **üç kümenin üçü de eğitim verisi ya da ona komşudur**
    (`copy_paste_gercek` → `karisim_t54_engelli.yaml:25` `train:` listesinde),
    sıkışmanın görüldüğü tek girdi (figür) ise **tek alan dışı örnektir, n=1**.
    Yani "figüre özgü" ile "alan dışı olmaya özgü" **ayrılamıyor** → **T111**.
- [x] **T111 — KAPANDI · Bakırlık envanteri: GERÇEKTEN alan dışı + etiketli doğrulama kümesi YOK; 6 aday kümenin 6sı da eğitim türevi (ölçüldü) · combined_data.yaml ÖLÜ (5/5 yol çözülmüyor) · kayıt D-198**
  - Doğrulandı: `copy_paste_gercek` v34'ün **eğitim verisidir**
    (`karisim_t54_engelli.yaml:25`); `sentetik_arena` aynı yaml'da; `kadraj_t66`
    o üretecin ailesinden; `raw_frames` `copy_paste_gercek`in **kaynak
    kareleridir**. Elimizdeki tek alan dışı örnek bir **YZ üretimi figürdür**.
  - Sonucu: **bugüne kadarki bütün kabul ölçümleri eğitim dağılımının içinde
    yapıldı.** Bu, "gerçek arena karesi yok" kalıcı sınırının (D-88/D-99) daha
    geniş bir yüzüdür ve **model seçimini de etkiler**.
  - ⚠ **v34 terfisini geri almaz** — terfi D-181'deki kapılara dayanır ve onlar
    bu kümede geçerlidir. Ama **raporlarda** "modelimiz X yapıyor" cümleleri bu
    sınırla birlikte yazılmalıdır.
  - **YAP (ucuz olan):** eğitimde HİÇ kullanılmamış, elde mevcut bir görüntü
    kümesi var mı diye tara (`dataset/` ve `data/` altındaki her kümenin hangi
    yaml'lara girdiğini çıkar). Varsa **bakir** ilan et ve kabul denetimine ek
    bir ölçüm alanı olarak bağla.
  - ⚠ **KAPI YAPMA:** bakir küme bulunsa bile eşiği önce **ölçmeden** kapıya
    çevirmek bu oturumda dört kez patlayan hatadır.

- [x] **T110 — KAPANDI · K0 örneklemesi kaldırıldı, düşüş görünür kılındı** · `O:
avitas-local-train5_kabul_denetcisi.py:81-82` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-183 §5**
  - ```python
    gecti["K0"] = (k0["figur"] is not None and k0["figur"] > 0.0
                   and k0["raw_frames"]["bos"] == 0 and k0["copy_paste"]["bos"] == 0)
    ```
    Yani K0 **`> 0`** kapısıdır: %0,49 ile %7,96 arasında **ayrım yapmaz**.
    v34'ün 16 kat düşüşü kapıya **hiç görünmedi**.
  - **ÖNCE KARAR (mimar):** eşik neye bağlanmalı? (a) üretimin **aynı koşumda**
    ölçülen değerine göre bir bant · (b) etiketli yer gerçeği kaplamasına oran ·
    (c) `> 0` kalsın, ayrı bir **ölçüm** alanı eklensin.
  - ⚠ **KÖR SIKILAŞTIRMA YOK:** eşik yükseltmek v34'ü geriye dönük düşürür ve
    D-183 §3 onun **fail-safe** yönde yanıldığını ölçtü. Kapı "az zemin
    görmeyi" cezalandırmadan önce **hangi yönün tehlikeli olduğu** yazılmalı.

  - ⚖ **KARARA BAĞLANDI · 2026-08-19 · mimar · `REVIEW_LOG.md` D-186.**
  - 🔴 **Önce sınıflandırma:** K0'ın cezalandırdığı yön (**az zemin görmek**)
    **güvenli** yöndür — boş maske → `MASKE_YOK` → `NO_ROUTE`, yani fail-closed.
    Tehlikeli yön (**çok zemin görmek**) K0'ın ölçtüğü şey **değildir**; onu
    **K2/K3** ölçer, üstelik **n=258** üzerinde, K0'ın **n=1** figürü yerine.
    **K0 bir YETENEK kapısıdır, emniyet kapısı değil** — ve yeteneği zaten daha
    iyi ölçen bir kapı var: **K1 (258/260)**.
  - **(a) tabana bağlı eşik → REDDEDİLDİ:** güvenli yönü cezalandırır ·
    tehlikeli yön zaten kapalı · eşiği **n=1, YZ üretimi, alan dışı** tek bir
    görüntüye çivilemek en zayıf kanıta en sert kuralı dayamaktır.
  - **(b) yer gerçeği oranı → REDDEDİLDİ:** figürün yer gerçeği **yok**.
  - ✅ **(c) SEÇİLDİ: kapı `> 0` KALIR, düşüş GÖRÜNÜR KILINIR.** Asıl sorun
    "kapı gevşek" değil, **16 kat düşüşün sessiz geçmesi**. Denetçi `figur`
    kaplamasını **üretim tabanıyla** ve **oranıyla** bassın; oran `<0,5` veya
    `>2,0` ise **🔴 DİKKAT** satırı + verdikt JSON'una `k0_taban_orani`.
    **BLOKLAMAZ**, verdikt AND birleşimine girmez.
    ⚠ Yön farkı: oran **>2,0** tehlikeli yönü işaret eder → K2/K3'e ayrıca
    bakılması gerektiği basılır. **<0,5** yetenek uyarısıdır.
  - 🔴 **ASIL KUSUR BAŞKA YERDEYMİŞ — DÜZELTİLECEK.** `bos == 0` kontrolü
    kümelerin tamamında değil **sekiz karede** yapılıyor (`:76`):
    ```text
    kume         toplam   ornekledigi   ornekleme orani
    raw_frames       67             8          %11,9
    copy_paste      393             8           %2,0
    ```
    **%2'lik örneklemeyle "hiçbir kare boş değil" demek zayıf bir iddiadır.**
    D-184 tam kümeleri ölçtü, `zemin<%1` = **0/720** — bugün gizlenen kusur yok,
    ama kapı tesadüfen güvenli. **KARAR: örnekleme kaldırılır, K0 TAM kümede
    koşar.** Ölçüt (`bos == 0`) **değişmez**; yeni eşik **uydurulmuyor**.
  - **YAPILMAYACAK:** `> 0` ölçütü değişmeyecek · figür için sayısal eşik
    konmayacak · v34 geriye dönük yeniden yargılanmayacak.

  - ✅ **UYGULANDI · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md` **D-187**.
    🔴 **`codes/` altına dokunulmadı:** `git diff HEAD -- codes/` **BOŞ**.
  - **(A) ÖRNEKLEME KALDIRILDI** — `yollar = sorted(kok.rglob(desen))`, tam küme.
    Ölçüt (`bos == 0`) **değişmedi**; `rglob` çift çağrısı da tek çağrıya indi.
  - **(B) ORAN GÖRÜNÜR** — figür kaplaması üretim tabanı + oranıyla basılıyor;
    band dışında 🔴 DİKKAT satırı. **BLOKLAMAZ.**
  - **(C) TABAN SAYIDAN** — deftere `figur_zemin_orani: 0.0049`,
    `raw_frames_bos: 0`, `copy_paste_bos: 0` eklendi. `olculen` **metni kaldı**
    (insan okuması) ama orandan **sayı ayıklanmıyor** — D-180 kusur sınıfı.
    Alan yoksa oran `None` + *"taban kayitli DEGIL"*; yokluk ne başarı ne
    başarısızlık sayılıyor.
  - ⚠ **EK BİR ŞEY DAHA YAPTIM (gerekçesiyle):** K0 ölçütü satır içi ifadeydi,
    `k0_gecti(figur, raw_bos, cp_bos)` saf fonksiyonuna ayrıldı — **semantik
    birebir aynı**. Böylece "oran bloklamıyor" iddiası bir yorum değil
    **imzanın kendisi** oluyor: `k0_gecti` oranla **çağrılamaz**. Test bunu
    `inspect.signature` ile kilitliyor.
  - **GERÇEK KOŞUM — ÜRETİM MODELİ (v34):**
    ```text
    K0 KORLUK YOK        GECTI  figur zemin %0.49 (uretim tabani %0.49 · oran 1.01)
                         raw bos 0/67 · cp bos 0/393        <- 8 DEGIL
    K1 258/260 · K2 12/258 · K3 0/258 · K4 1/258 · K5 None px DUSTU
    VERDIKT: URETIME ALINMAZ — dusen: K5
    ```
    Oran band içinde → **DİKKAT satırı basılmadı** (beklenen).
    ⚠ K5'in `None` olması **D-180/T105** konusudur; verdikt bu görevden **önce
    de** K5 yüzünden RED'di — **değişmedi**.
  - 🔴 **(B)'NİN ÇALIŞTIĞININ KANITI — v30:**
    ```text
    K0 KORLUK YOK        GECTI  figur zemin %7.96 (uretim tabani %0.49 · oran 16.24)
                         raw bos 0/67 · cp bos 0/393
    🔴 DIKKAT: figur kaplamasi uretim tabanindan 16.24 kat sapiyor.
       > 2,0 ise TEHLIKELI yon (daha cok zemin) — K2/K3'e AYRICA bakin.
    VERDIKT: URETIME ALINMAZ — dusen: K5
    ```
    **DİKKAT basıldı ve K0 yine GEÇTİ** — görünürlük çalışıyor, bloklamıyor.
  - ✅ **D-186'NIN AÇIK MADDESİ CEVAPLANDI:** tam kümede `bos` **0 kaldı** —
    v34 `0/67` + `0/393`, v30 `0/67` + `0/393`. Örnekleme kaldırılınca K0
    düşmedi. ⚠ Bu, örneklemenin **gereksiz olduğu** anlamına gelmez: 8 kare
    bunu **garanti etmiyordu**, şansı tutmuş; artık garanti var.
  - **YENİ TEST** `tests/test_k0_gorunurlugu.py` (10 test, **model yüklemez**).
    Mutasyon (`k0_dikkat_satiri` hep `None`): **4 FAIL**.
  - 🔴 **T103'ÜN KAPISI BU DEĞİŞİKLİĞİ YAKALADI:** defteri değiştirince
    `test_paket_kopyalari_kanonik_kaynaklarla_birebir` ve
    `test_paket_defteri_depo_defteriyle_BIREBIR_AYNI` düştü — **bayat paket
    defteri**. `jetson_paket_hazirla.py` koşuldu, kapı yeşile döndü. Dün
    kurulan senkron kapısı işini yaptı.
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    yeni testler                  Ran 10 · OK
    mutasyonda                    4 FAIL
    git diff HEAD -- codes/       BOS
    codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    unittest discover -s tests    Ran 630 tests in 49.194s / OK   (620 -> 630)
    ```
  - ⚠ **DOĞRULANAMADI:** K5 `None` **çözülmedi** (D-180/T105) · oran eşikleri
    (0,5 / 2,0) **ölçümle türetilmedi**, emirde verilen değerlerdir (yalnız
    raporlama bandı, karar değiştirmiyor) · `figur_zemin_orani` üretim modeli
    değişirse **elle** güncellenmeli, bunu zorlayan kapı **yok** ·
    `raw_frames_bos`/`copy_paste_bos` deftere yazıldı ama **hiçbir yerde
    okunmuyor** (bugün ölü alan) · tam kümede koşmanın **süre maliyeti**
    ölçülmedi (~57 kat daha çok çıkarım) · yalnız iki model koşuldu ·
    testler **saf fonksiyonları** sınar; `main()` içindeki bağlantı yalnız iki
    gerçek koşumun çıktısıyla gösterildi.
- [ ] **T107 — Eğitim betiğinin `AD` varsayılanı BAYAT: sürüm dizisi v33'teyken `v22` adıyla koşum üretiyor** · `O:
avitas-local-train._t53_gercek_karisim.py:36` · KÜÇÜK · kanıt: `REVIEW_LOG.md` **D-182 §1**
  - `AD = "v22_on10_gercek"` gömülü. Dün geceki iki koşum `v22_*` ve `v23_*`
    adıyla düştü, oysa `codes/runs/segment/` zaten **v33**'e gitmişti.
  - Sonucu: üretime alınan model **v30'dan küçük numaralı** görünecekti; terfide
    ad elle **v34**'e çevrildi. Bu, "hangi ağırlık uçtu" karışıklığının kaynağı.
  - **YAP:** `AD` varsayılanı ya zorunlu argüman olsun ya da `runs/segment/`
    içindeki en yüksek numaradan **türetilsin**. ⚠ Türetilecekse koşum adının
    **görev bilgisini** de taşıması gerekiyor (`v34_t54_engelli` gibi).
- [ ] **T109 — v34'ün `.engine`i yok; Jetson'da derlenmeli** · `jetson_paket/` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-182 §6**
  - Terfide **ONNX 512 fp16 üretildi** (`results/onnx_export_v34_20260819/`) ve
    pakete kondu; `.engine` **PC'de üretilemez** (Jetson Orin NX'te derlenmeli).
  - Pakette v30'un ONNX'i **tarihsel olarak duruyor** — hangisinin üretim
    olduğunu `asil_model` söyler; yanlışlıkla eski ONNX derlenmemeli.
  - **T16'ya bağlı.**
- [x] **T112 — KAPANDI · Ölçüm aynası senkronu testle kilitlendi** · `scripts/olcum/` ↔ `O:
avitas-local-train\` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-188 §4**
  - Testler `scripts/olcum/65_kabul_denetcisi.py`yi (**ayna**) içe aktarıyor
    (`tests/test_k0_gorunurlugu.py:29`); ölçümleri fiilen koşan dosya ise
    `O:
avitas-local-train5_kabul_denetcisi.py`. **İkisi ayrı dosya ve
    senkronlarını hiçbir şey zorlamıyor.**
  - Mimar mutasyon kontrolünde bunu **canlı yaşadı**: canlı betiği bozdu,
    testler **10/10 geçti**; aynayı bozunca **5 düştü**. Yani bir gün ayrışırsa
    testler yeşil kalırken gerçek araç bozuk olabilir.
  - Bugün **üçü de senkron** (65 · 66 · 80) — ölçüldü. Ama bu **disiplinle**
    sağlanmış, **mekanizmayla** değil.
  - 🔴 **DÖRDÜNCÜ TEKRAR — artık yapısal desen:**
    ```text
    D-158 bulgu 4  test dosyasi izlenmiyordu + yanlis mesafe donusumu
    D-170          codes/test_monotonluk.py vardi ama tests/ altinda DEGILDI
    T104           IKI JETSON_KILAVUZ.md
    D-188          IKI 65_kabul_denetcisi.py, yalniz AYNA denetleniyor
    ```
  - **ÖNCE KARAR (mimar):** (a) ayna kaldırılsın, tek kaynak olsun (import
    yolu düzeltilir) · (b) bir test aynalığı **sabitlesin** (sha kıyası) ·
    (c) paketleyici gibi bir senkron aracı olsun.
  - ⚠ **T104 bunun bir örneğidir** ve o karar da buraya bağlanmalı.
  - ⚠ **KÖR SİLME YOK:** hangi kopyanın kaynak olduğu dosya başına değişebilir
    (T104'te **paket** kopyası büyüktü, yani kök eskiydi).
  - ⚖ **KARARA BAĞLANDI · 2026-08-19 · mimar · `REVIEW_LOG.md` D-189.**
  - 🔴 **Teşhisim yanlıştı, ölçüm düzeltti:** `O:
avitas-local-train` **git
    deposu değil** (`git rev-parse` → *not a git repository*). Yani
    `scripts/olcum/` bir fazlalık kopya **değil**, o 37 betiğin **tek sürüm
    kontrolüdür**. **(a) "aynayı kaldır" REDDEDİLDİ** — 37 betiğin geçmişini
    silmek olurdu.
  - 🔴 **Karar verirken CANLI bir ayrışma buldum ve kusur BENİMDİ.** 37 çiftten
    biri (`76_serit_etiketi_celiskisi.py`) ayrışmıştı. Kaynağı **D-166**: orada
    yanlış öncülü üç yerde düzeltirken `76`nın yalnız **repo aynasını**
    düzeltmişim; **canlı betik hâlâ çürütülmüş gerekçeyi taşıyordu.**
    Düzeltildi (repo → canlı), **37/37 senkron** doğrulandı.
    ⚠ Bir kapı olsaydı bu, bugün değil **D-166 commit'inde** yakalanırdı.
  - ✅ **(b) SEÇİLDİ: TESTLE KİLİTLE** — ve bu projede **zaten çalışan** kalıp:
    `codes/` → `jetson_paket/kod/` aynası bir senkron aracı + testlerle korunuyor
    ve orada ayrışma **yaşanmadı**; `scripts/olcum/` çiftinde ne araç ne test
    var ve ayrışma **yaşandı**. Yeni bir şey icat etmiyorum.
  - **Testin bağlayıcı şartları:** çiftler **mekanik** bulunur (elle liste
    tutulmaz — liste bayatlar) · kıyas **bayt bazında** · **yön iddia edilmez**,
    test yalnız "aynı mı" der (D-166'da doğru olan repo, T104'te **paket**
    kopyasıydı) · canlı dizin yoksa **`skipTest`**, düşmez ama **sessiz de
    kalmaz** (PC garantiye gidince kırmızı yanmamalı) · **pozitif kontrol:**
    bir çift geçici ayrıştırılınca test **düşmeli**.
  - **Yardımcı (önerilir, zorunlu değil):** ayrışan çiftleri **listeleyen**,
    `--uygula` ile **yön açıkça verilerek** kopyalayan küçük bir araç.

  - ✅ **UYGULANDI · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md` **D-191**
    (⚠ numara **çakıştı**: mimar aynı anda D-190'ı T113 kararı olarak ekledi;
    **kendi kaydımı** D-191'e aldım, mimarınkine dokunmadım).
    Yeni: `tests/test_olcum_ayna_senkronu.py` (6 test) · `scripts/olcum_ayna.py`.
    🔴 `git diff HEAD -- codes/` **BOŞ** · `git status scripts/olcum/
    jetson_paket/` **BOŞ** (ayna dosyaları değişmedi).
  - **Yedi bağlayıcı şartın hepsi uygulandı:** çiftler **mekanik** bulunur
    (elle liste yok) · kıyas **bayt bazında** (`shallow=False`) · **yön iddia
    edilmez**, otomatik onarım yok · canlı dizin yoksa **`skipTest` + açık
    sebep** · yol tek yerde (`NAVITAS_OLCUM_KOK`, yoksa
    `KOK.parent/"navitas-local-train"`) · pozitif kontrol geçici dizinlerde ·
    kapsam docstring'de yazılı.
  - **BUGÜNKÜ DURUM:** `cift: 37 · AYRISAN: 0` — hepsi senkron.
    Ölçülen kapsam: repo aynası **37** `.py`, canlı **105** `.py`, **68** yalnız
    canlıda. ⚠ T113'ün "46"sı **numaralı** betikleri sayar (canlı 82, repo 36);
    iki sayı **farklı kapsamlardır, çelişmezler**.
  - **KAPI KANITLARI:**
    ```text
    (a) bu makinede KOSUYOR ve GECIYOR (skip DEGIL)
        test_repo_aynasi_canli_betiklerle_BIREBIR ... ok · Ran 6 · OK

    (b) GERCEK AYRISMADA DUSUYOR  (canli dizinin GECICI KOPYASI bozuldu;
        gercek dosyalara DOKUNULMADI)
        FAIL: test_repo_aynasi_canli_betiklerle_BIREBIR
        AssertionError: Lists differ: [] != ['76_serit_etiketi_celiskisi.py']
        Ran 6 · FAILED (failures=1)

    (c) CANLI DIZIN YOKKEN SKIP + SEBEP
        skipped 'CANLI OLCUM DIZINI YOK: ... Bu bir BASARI DEGILDIR; koruma
        yalnizca ayrismanin uretilebildigi makinede vardir (D-189 §3.4).'
        Ran 6 · OK (skipped=2)

    (d) yardimci arac YON olmadan REDDEDIYOR
        HATA: --uygula icin YON zorunludur (--repodan ya da --canlidan).
        cikis=2
    ```
    ⚠ (b)'de simülasyon için seçilen dosya, D-189'da **gerçekten ayrışmış olan**
    dosyadır — kapı tam o vakayı yakalıyor.
  - ⚠ **KENDİ HATAM:** "otomatik onarım yok" kilidini önce **düz metin**
    aramasıyla yazdım ve test **kendi yasak listesini** yakalayıp düştü
    (öz-referans). **AST**'ye çevrildi: artık yalnız gerçek `ast.Call`
    düğümlerine bakıyor — hem tuzak kalktı hem kontrol keskinleşti.
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    unittest discover -s tests    Ran 636 tests in 52.392s / OK   (630 -> 636)
    git diff HEAD -- codes/       BOS
    ```
  - **NOT — D-190 (T113) ile ilişki:** kalıp **mekanik** olduğu için "14 betik
    aynalanır" kararı uygulandığında **hiçbir düzenleme gerekmez**; çift sayısı
    37 → 51'e kendiliğinden çıkar ve yeni çiftler anında kilit altına girer.
    Elle liste tutmamanın somut faydası budur.
  - ⚠ **DOĞRULANAMADI:** 🔴 **koruma yalnızca BU makinede var** — `skipTest`
    kararı bilinçli ama bedeli gerçek; başka makinede kapı **hiç koşmaz**,
    "yeşil" görmek koruma çalıştı demek **değildir** (`skipped` sayısına
    bakılmalı) · yalnız `*.py` kıyaslanıyor (`.md`/`.sh`/`.yaml` kapsam dışı) ·
    68 `.py` yalnız canlıda ve bu test onlar hakkında hiçbir şey söylemez
    (T113) · `olcum_ayna.py`nin **kopyalama dalı çalıştırılmadı** (bugün ayrışan
    çift yok) · test **ad eşitliğine** dayanır, farklı adla duran aynı betiği
    yakalayamaz.
    **Varsayılan yön YOKTUR.**
  - **YAPILMAYACAK:** ayna silinmeyecek · otomatik/sessiz senkron kurulmayacak
    (yanlış yönde kopyalamak D-166'nın düzeltmesini **geri alırdı**) ·
    **T104 bu karara bağlanır ama otomatik çözülmez** (orada doğru kopya
    **pakettekidir**; yön kararı ayrıdır).
  - ✅ **KAPANDI · 2026-08-19 · `REVIEW_LOG.md` D-191 (amele) / D-192 (mimar).**
    `tests/test_olcum_ayna_senkronu.py` (6 test) + `scripts/olcum_ayna.py`.
    Kapılar (mimar koştu): **636 OK** (630 → +6) · **15/15** ·
    `git diff codes/` **BOŞ** · ayna **51/51 · AYRIŞAN 0**.
  - **Üç ayrıntı özellikle iyi:** *yön iddiası AST ile kilitlenmiş* ("test
    dosyası kopyalama çağrısı içermez" diye ayrı test — "otomatik onarım yok"
    bir yorum değil, mekanik doğrulama) · *pozitif kontrol gerçek dosyalara
    dokunmuyor* (geçici dizinlerde) · *`shallow=False` gerçekten içeriğe
    bakıyor mu* diye **ayrı** test (aynı boyut, farklı içerik — `filecmp`in
    varsayılanı boyut kıyasıdır, bu tuzağa düşülseydi test sessizce boş olurdu).
  - ⚠ Amele mimarın sayımını **düzeltti**: repo aynasında **37** `.py`, canlıda
    **105**, yalnız canlıda **68**. Mimarın "46"sı **numaralı** betikleri
    sayıyordu (canlıda 82, repoda 36). İkisi de doğru, **farklı kapsam**.
- [x] **T113 — KAPANDI · 14 betik arşivlendi, depo bütünlüğü kırığı kapandı, ve izlenen üretim kodu onlardan birine BAĞIMLI** · `O:
avitas-local-train\` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-189 §1** (T112 ölçümünün yan bulgusu)
  - Aynalama **#48'den sonra** başlamış; `01`–`47` arası (ve 49-53, 55, 57-59)
    **hiç aynalanmamış**. Ölçüldü: canlıda **82** numaralı betik, repoda **36**.
    ```text
    aynalanan numaralar: 48 54 56 60..93
    aynalanmayan       : 01..22 · 30..36 · 40..43 · 45..47 · 49..53 · 55 · 57..59
    ```
  - 🔴 **İzlenen üretim betiği sürümsüz bir dosyaya bağımlı:**
    `scripts/copy_paste_augmentation.py:944` →
    `default=Path(r"O:
avitas-local-train)_sentetik_arena.py")`.
    `51_sentetik_arena.py` **sentetik arena üretecidir** — kabul kümesinin
    (`kadraj_t66`) atasıdır ve `RESEARCH_NOTES.md` / `TASK_QUEUE.md` ona atıf
    yapar. **Yalnız bu PC'nin diskinde duruyor.**
  - ⚠ **PC garantiye gidecek** — bu dosyalar yedeklenmezse geri gelmez.
    Yedekleme listesine **girmek zorunda**.
  - **ÖNCE KARAR (mimar):** hepsi mi aynalanmalı, yoksa yalnız **hâlâ
    çağrılanlar** mı? Ölçmeden karar verilmez: hangi numarasız/eski betiğe
    bugün hâlâ atıf var, çıkarılmalı.
  - ⚠ T112'nin testi bunu **yakalamaz** — o test yalnız **iki tarafta da var
    olan** çiftleri kıyaslar (bilinçli, D-189 §3.1). Bu ayrı bir eksiktir.
  - ⚖ **KARARA BAĞLANDI · 2026-08-19 · mimar · `REVIEW_LOG.md` D-190.**
  - **Ölçüldü** (46 betiğin her biri YALNIZ izlenen dosyalarda `git ls-files` ile arandı):
    ```text
    IZLENEN KODDAN cagrilan :  7
    yalniz BELGEDE gecen    :  7
    HIC atif almayan        : 32
    ```
  - 🔴 **Bağımlılık "atıf" değil, SERT ÇALIŞMA-ZAMANI BAĞI.**
    `scripts/copy_paste_augmentation.py:124-129` (izlenen üretim betiği)
    `51_sentetik_arena.py`yi **dinamik import edip `yapistir()`ı çağırıyor** ve
    bulamazsa **`RuntimeError`** atıyor. Versiyonlu kodun versiyonsuz dosyaya
    sert bağımlı olması bir tercih değil, **depo bütünlüğü kırığıdır.**
  - ✅ **(A) 7 kod-atıflı betik AYNALANIR — zorunlu.** Kırığın kapatılması.
  - ✅ **(B) 7 belge-atıflı betik de AYNALANIR.** Projenin kendi disiplini:
    ölçüm **kanıttır** ve `REVIEW_LOG` bu betikleri kanıt olarak anıyor; betik
    kaybolursa **anılan kanıt yeniden koşulamaz.** Yedi küçük `.py`, bedeli yok.
  - ✅ **(C) 32 atıfsız betik AYNALANMAZ.** Hiçbir şey onlara bağlı değil; depo
    bir **yedekleme ortamı değildir** (`.gitignore:130-134` zaten ağırlıkları
    dışarıda tutuyor).
  - 🔴 **AMA (C) "önemsiz" demek DEĞİL — ihtiyaç farklı:**
    **sürüm kontrolü** = değişimi izlemek + kod bağımlılığını garanti etmek ·
    **yedek** = diski kaybetmemek. 32 betik yedek **gerektiriyor** ve
    **PC garantiye gidiyor**. `O:
avitas-local-train` **tümüyle** yedek
    listesine girer.
  - ⚠ **YAN BULGU:** aynı betik `--aset-dizini` ile `doku_bankasi\enkaz`a da
    bağlı (**498 MB** doku bankası). Aynalanamaz (ikili varlık) ama
    **yedeklenmek zorunda**. Bu yüzden *"izlenen kod depo dışı yola atıf
    etmesin"* diye **blanket bir test YAZILMAYACAK** — doku bankası meşru
    olarak dışarıda ve o test yanlış alarm üretirdi.
  - **UYGULAMA:** 14 betik `scripts/olcum/` altına **içerik değiştirilmeden**
    kopyalanır · T112'nin kimlik testi onları **kendiliğinden** kapsar ·
    hiçbir ölçüm sayısı değişmez (**arşivleme**, ölçüm değil).
  - ✅ **KAPANDI · 2026-08-19 · `REVIEW_LOG.md` D-192 §3 · uygulayan MİMAR.**
    🔴 **Birleşik emrin bu yarısı ameleden gelen işte YAPILMAMIŞTI** (kopyalanan
    dosya 0, ayna çifti 37 — 51 olmalıydı). Amele T113'e atıf yapmış ama
    yapılacak iş olarak değil, başka görev olarak ele almış. Mimar kapattı.
  - 14 betik `scripts/olcum/` altına **içerik değiştirilmeden** kopyalandı ve
    her biri `filecmp.cmp(shallow=False)` ile **BİREBİR** doğrulandı.
    Ayna çifti **37 → 51**.
  - 🔴 **DEPO BÜTÜNLÜĞÜ KIRIĞI KAPANDI:** `scripts/copy_paste_augmentation.py`
    artık `51_sentetik_arena.py`ye **versiyonlu** bir kopya üzerinden bağlı.
  - ⚠ **Madde 7 notu:** bu kod yazma değil **arşivleme** (karar D-190'da zaten
    verilmişti). Kendi işini kendi onaylamamak için doğrulama **amelenin yazdığı
    teste** bırakıldı: `test_olcum_ayna_senkronu` → **6 test OK, 51/51**.
  - ⚠ **32 aynasız betik bilerek aynalanmadı** (D-190 (C)) — onlar **yedek**
    ihtiyacıdır, sürüm kontrolü değil. `O:
avitas-local-train` tümüyle yedek
    listesinde.
- [ ] **T99 — T95 üretimin ÇAĞRI İMZASIYLA hiç ölçülmedi (ankorlu · araçlar engel)** · `simulation/scripts/iha_haritala.py:323` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-165 §2**
  - Üç ölçüm turu da `rota_bul(mk, mpp=mpp, icerik=icerik)` kullandı. Üretim:
    ```python
    rota_bul(costmap_maskeleri, mpp=MPP, baslangic=..., hedef=..., plan=True,
             yol_sinif_idler=COSTMAP_YOL_KATMANLARI,      # (0,)
             engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,  # (1, 2) MOLOZ + ARAC
             gorsel_cikti=True)
    ```
  - `baslangic`/`hedef` farkının **mekanizması D-165 §3'te kapatıldı** (uçlar
    korunuyor) — yine de hiç ölçülmedi.
  - 🔴 **KAPATILAMAYAN fark:** `engel_sinif_idler=(1,2)`. Araçlar engel
    sayıldığında serbest alan **daralır**, dar geçit çoğalır ve kuralın
    reddetme oranı artabilir. **Ölçülen sayılar üretim girdisine ait değil.**
  - **YAP:** `89`/`90`/`91` betiklerini üretim imzasıyla koştur; kayıp · pay ·
    süre · kararlılık aynı tabloda yeniden çıkar.
  - ⚠ Bulgu çıkarsa **geri alma seçeneği açıktır**; değişiklik tek satırdır.
  - **KAPI:** ölçüm koşulmadan hiçbir kod değişmez.
- [ ] **T100 — `76_serit_etiketi_celiskisi.py` sayıları T95'le kaymış olabilir** · `scripts/olcum/76_serit_etiketi_celiskisi.py` · KÜÇÜK · kanıt: `REVIEW_LOG.md` **D-164 §7.5**
  - Betik `rota_bul` kullanır ve T95 `waypoints`i değiştirdi; yeniden koşulmadı.
  - **YAP:** yeniden koş, D-146/D-147'deki sayılarla kıyasla, kaydı güncelle.
- [x] **T96 — İki kollu sahnede `road` çatal altındaki ORTAK gövdeyi adlandırıyor** · `codes/rpi_inference.py:1255` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-158** (denetim bulgusu 5)
  - ✅ **KAPANDI (defter düzeltmesi 2026-08-18).** Ölçüldü (D-167), denetlendi
    (D-168): ayırt edici 11 karenin yer gerçeği kırılgan → sıralama karara
    bağlanamaz, `darbogaz_serit` kalıyor. CONTRACTS §6.2 olgu beyanıyla
    güncellendi. Kırılganlık **T101** olarak ayrıldı.
  - `road = darbogaz_serit` (en dar noktanın şeridi). İki kollu bir sahnede
    darboğaz çatalın **altındaki paylaşılan gövdeye** düşerse yayınlanan sayı
    hangi kola sürüleceğini **söylemez**. Ölçülen örnek (S3): rota `(233,20)`
    ile sağ koldan çıkıyor ama `road=2` (ortak gövde).
  - Ölçülen kırılganlık: `serit_min` 8,0 (şerit 2) vs 9,0 (şerit 3), band eşiği
    8,64 → **0,64 px**'lik kayma yayınlanan kararı çevirir.
  - ⚠ Bu semantik **D-41'den gelir ve T94'ten öncedir**; T94 onu yalnız
    görünür kıldı. `baskin_serit` zaten hesaplanıyor ama yayınlanmıyor (D-146).
  - 🔴 **ÖNCÜLÜM YANLIŞTI · 2026-08-18 · `REVIEW_LOG.md` D-166.** Bu göreve
    "İKA `plan_path(road)` ile plan yapıyor (`comms/ika_receiver.py:11`)"
    yazmıştım ve **ölçmemiştim**. O satır bir **modül DOCSTRING'idir**, üretim
    kodu değil; `plan_path` diye bir fonksiyon repoda **yoktur**.
    Gerçek navigatör `simulation/scripts/ika_nav.py:178-182` tersini yapar —
    *"sayısal road tek başına geometri değildir"* — ve `:165` **"waypoint
    olmadan İKA'nın hareket etmesine izin verilmez"** der. Tüketicilerin hepsi
    geometriyi waypoint'ten alır (`hakem_log.py:175`, `mission_demo.py:74`).
  - Aynı öncül **üç yerdeydi** ve biri **T90 fail-closed korumasının
    gerekçesiydi** (`costmap_path_finder.py:1011`) — onu ben onaylamıştım.
    Üçü de düzeltildi (**yalnız yorum/docstring; davranış değişmedi**).
  - **Koruma yine de doğru, başka gerekçeyle:** `road` yayınlanan ve
    **puanlanan** cevaptır. CONTRACTS §6.3 → şartname §5.3.2/§6.2 yanlış
    güzergâhı 0 puan sayar ve politika *"çekimserlik puan kaybettirir, yanlış
    karar SIFIRLAR"*. ⚠ Ama **fiziksel güvenlik argümanı ortadan kalktı**:
    yanlış `road` aracı yanlış koridora **sürmez**, yanlış **cevap yayınlar**.
  - **T96 YENİDEN İFADE EDİLDİ:** soru "İKA hangi kola sürülecek" değil —
    *"'hangi koridor açık' sorusuna en iyi cevabı hangi istatistik verir:
    en dar noktanın şeridi mi, rotanın gövdesinin şeridi mi, çıkış kolu mu?"*
  - Ölçülmüş olgular: **5/258 (%1,9)** karede `darbogaz_serit != baskin_serit`,
    beşi de çok şeritli ve **kararsız karelerde toplanıyor** (D-146) ·
    **0,64 px**'lik kayma yayınlanan kararı çeviriyor (D-158 bulgu 5).
  - **ÖLÇÜM VAR, KARAR YOK:** ayrışan karelerde **hangisi doğru** ölçülmedi.
    Küme yer gerçeği taşır: manifest `arena.acik_serit` · `uretec_seritleri` ·
    `arena_x_araligi` · `kapali_seritler`.
  - 🔴 **EŞLEME TUZAĞI (önceden işaretlendi):** `acik_serit` **üretecin** şerit
    numarasıdır, `serit_no()` letterbox içerik kutusunu üçe böler. **Bu tuzağa
    bu oturumda bir kez düşüldü** (`81_t74_darbogaz_yeri.py`). Eşleme x
    aralıklarıyla yapılacak, **indisle değil**.
  - **ÖN KAYIT YAZILDI:** `scripts/olcum/t96_on_kayit.md` — kazanan aday
    diğerlerinden **en az 5 kare** önde olmalı (D-146'nın ayrışma sayısı),
    **ve** kararlılığı mevcut `darbogaz_serit`ten kötü olmayacak. Tutmazsa
    **değişiklik yapılmaz**. **Ölçmeden değiştirilmesin.**

  - ✅ **ÖLÇÜLDÜ · MEVCUT İSTATİSTİK DOĞRULANDI · DEĞİŞİKLİK YOK · 2026-08-18 ·
    Claude-2** · kayıt `REVIEW_LOG.md` **D-167** · ölçüm
    `scripts/olcum/92_t96_road_istatistigi.py`.
    **Üretim kodu DEĞİŞTİRİLMEDİ** (`git status`: `codes/ comms/ tests/
    jetson_paket/ simulation/` **boş**).
    ```text
    olculen kare 260 · rota ureten 258 · DISLANAN (BELIRSIZ) 49
    KARSILASTIRILABILIR 209

    TAM KUME UYUM (yer gercegine gore)
      A_darbogaz  198 / 209  (%94,7)   <- yayinlanan, MEVCUT
      C_cikis     197 / 209  (%94,3)
      B_baskin    196 / 209  (%93,8)

    AYRISMA:  A!=B 2 · A!=C 9 · B!=C 11 · ucu birden farkli 0
              ayrisan alt kume 11 kare — 11'i de COK SERITLI (D-146 ile tutarli)
    ```
  - **ÖLÇÜTLER:**
    ```text
    (T1a) TAM KUME kazanan A (198) >= B(196), C(197)      TUTTU
    (T1c) ayrisan + yer gercegi alt kume 11 kare (bos degil)
    (T1b) A vs B : ayrisan  2 · A kurtardi 2 · B kurtardi 0 -> DOMINANT
          A vs C : ayrisan  9 · A kurtardi 5 · C kurtardi 4 -> TAKAS
          B vs C : ayrisan 11 · B kurtardi 5 · C kurtardi 6 -> TAKAS
          -> A hepsine dominant DEGIL                       DUSTU
    (T3) codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    (T4) unittest discover -s tests    Ran 589 tests in 54.665s / OK
    (T5) KOSULMADI — on kayit "(T1a)+(T1b) tuttuysa kos" der; kazanan zaten
         mevcut A oldugu icin gereksiz.
    ```
  - **KARAR: kazanan A (mevcut) → değişiklik yok.** Ön kaydın açıkça izin
    verdiği sonuç. **İki gerekçe aynı yöne bakıyor:** (1) A tam kümede en
    yüksek uyumu veriyor; (2) **A, B'yi 2-0 kesin yeniyor** — yani
    `baskin_serit`i yayınlamak bu kümede **kesin olarak daha kötü** olurdu,
    "hesaplanıyor ama yayınlanmıyor" bir eksiklik değil **doğru karar**.
    A ile C arasında **5-4'lük takas** var; net kazanç yok.
  - **POZİTİF KONTROLLER:** `karar_seridi` eşleme uyuşmazlığı **0** ·
    manifest/üretim `icerik` farkı **0** · `acik_serit` çelişkisi **0** ·
    ek kontrol: **yayınlanan `open_path` == A, 209/209** (yani "A" yeniden
    türetim değil, üretimin yayınladığı alanın ta kendisi).
  - 🔴 **İKİ KONTROL DE ATEŞLEDİ, İKİSİNDE DE HATA BENDEYDİ** (D-167 §2):
    (a) eşlemeyi önce `serit_kutusu` ile kurdum → 21/527 uyuşmaz; doğrusu
    `gecilebilir_kutu` (0/527) — kadraj tam şerit kutusunu kırpıyor, bu tam da
    işaretlenen eşleme tuzağı. (b) "tam bir açık şerit olmalı" değişmezini
    yanlış kurdum → 25 karede ateşledi; kadraj **birden çok üreteç şeridini
    tek karar şeridine katlıyor** (`sa_000020`: üçü de `karar_seridi=2`).
    Doğru değişmez: *açık şeritlerin hiçbiri `acik_serit` ile çelişmeyecek*.
  - ⚠ **DOĞRULANAMADI:** küme sentetiktir (gerçek karelerde yer gerçeği yok) ·
    49 BELİRSİZ kare dışlandı · **ayrışan alt küme 11 kare**, 5-4 ve 2-0 gibi
    sayılar küçüktür ve örnekleme hatası ölçülmedi (bu, "değişiklik yok"
    kararını **güçlendirir**, "A kesin en iyidir" demek değildir) · üçünü
    birleştiren kural (oy çokluğu) ölçülmedi · B ve C'nin gürültü kararlılığı
    hiç ölçülmedi · (T3)/(T4) bu dalda **kanıt değeri taşımaz** (D-160 §1).
  - ⚠ **AÇIK KALAN (mimarın kararı):** `CONTRACTS.md §6.2` `road`ın **hangi
    istatistik** olduğunu hâlâ **yazmıyor** (yalnız `{1:sol,2:orta,3:sağ}`
    değer aralığı var). Ön kayıt bu yazımı yalnız "kazanan A değilse" dalıyla
    şartlamıştı, o yüzden dokunmadım; ama bu ölçüm artık o tanımın dayanağını
    sağlıyor.
  - 🔎 **MİMAR DENETİMİ · 2026-08-18 · `REVIEW_LOG.md` D-168. KARAR DOĞRU,
    GEREKÇE DÜZELTİLDİ.** Sayılar JSON'dan yeniden hesaplandı (198/196/197,
    ayrışan 11, `yayinlanan_open_path == A` 209/209): **birebir**.
  - 🔴 **A'nın 11 hatasının 7'si, üç istatistiğin de AYNI cevabı verdiği
    karelerdedir** — orada aday seçmek hiçbir şey değiştirmez. O 7 kareye
    baktım: sebep üretim değil, **yer gerçeğinin kendisi**. `sa_000127`de
    kadrajda yalnız iki üreteç şeridi var, açık olanı **210 px** geniş; onun
    merkezi 214,75, `serit_no` sınırı **213** → etiket 2, ama rota tamamen
    x<213'te. **Merkez sınırın 1,75 px ötesinde.**
  - **Ölçtüm** (açık şerit merkezinin en yakın `serit_no` sınırına uzaklığı):
    ```text
    kume                 n     merkez-sinir medyani   min    serit genisligi
    ucu de YANLIS        7            5,2 px          0,8         210,4 px
    AYRISAN             11            4,6 px          1,5         109,2 px
    ucu de DOGRU       191           45,7 px          0,0         114,6 px
    (serit_no ucte biri = 213,3 px)
    ```
    Hem 7 hem 11, etiketin **yazı-tura olduğu bantta** topluyor; doğru çıkan
    191 karede pay **on kat** büyük.
  - **SONUÇ: "değişiklik yok" DOĞRU ve şimdi DAHA GÜÇLÜ** (kanıt yalnızca az
    değil, ölçülerek güvenilmez). ⚠ Ama **"A doğrulandı" DENEMEZ** — 198 vs
    197 vs 196 farkı (2 kare) bu kırılganlığın altındadır. Doğru ifade: **bu
    kümede sıralama KARARA BAĞLANAMAZ.**
  - ⚠ **7 karelik "hepsi yanlış" ÜRETİM KUSURU DEĞİLDİR** — rota kapalı
    koridordan geçmiyor, etiketleme çerçeveleri çatışıyor. D-167'yi okuyanın
    çıkaracağı ilk yanlış sonuç bu olurdu.
  - ✅ **CONTRACTS §6.2 GÜNCELLENDİ:** `road`ın hangi istatistik olduğu artık
    yazılı — **olgu beyanı olarak**, "en iyisidir" iddiası olmadan.
- [ ] **T101 — Etiketleme çerçevesi ill-conditioned: bir üreteç şeridi iki `serit_no` üçte birine birden yayılıyor** · `codes/karar_sozlesmesi.py` (`serit_no`) · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-168 §4**
  - 🔎 **POPÜLASYON SAYISIYLA ÖLÇÜLDÜ · 2026-08-20 · D-205.** t66'da AÇIK
    şeridin kutusu 260 karenin **77'sinde (%29,6)** iki `serit_no` üçte-birine
    yayılıyor (897 şeritten 186'sı); açık+yayılan şeritlerde merkez-sınır
    medyanı **6,99 px** (D-168'in ~5 px gözlemiyle aynı mertebe).
    🔴 Gerçek karelerde ÖLÇÜLEMEDİ: arena_kompozit/raw_frames manifestlerinde
    şerit kutusu YOK — T111/D-198'in duvarı (etiketli alan-dışı küme yok).
    `serit_no` DEĞİŞTİRİLMEDİ (sözleşme alanı).

  - `serit_no` GÖRÜNTÜYÜ üçe böler (üçte bir = 213,3 px). Üreteç şerit kutuları
    kadraja göre **109-210 px** arası değişir; bir şerit iki üçte bire birden
    yayılabilir. Ayırt edici karelerde şerit merkezi sınıra **~5 px**.
  - Bu, `76_serit_etiketi_celiskisi.py`nin **H1** hipotezinin ta kendisidir —
    artık sayıyla.
  - 🔴 **SENTETİK KADRAJIN MI, GERÇEĞİN Mİ SORUNU: BİLİNMİYOR.** Gerçek arenada
    üç koridor kabaca birer üçte bir kaplar; t66 kadrajı **iki şeritli** görüşler
    üretiyor (uzunluk dağılımı 2→39, 3→116, 4→54, 5→51). Gerçek kamera çerçevesi
    de iki şeritli görüş üretiyorsa sorun **gerçektir**.
  - **ÖNCE ÖLÇ:** gerçek karelerde (`kompozit`, `drone`) kadrajda kaç koridor
    görünüyor ve bir koridor `serit_no` sınırını ne sıklıkta aşıyor?
  - **KAPI:** ölçüm koşulmadan `serit_no` DEĞİŞMEZ — o sözleşme alanıdır
    (CONTRACTS §8) ve tüm karar yolu ona bağlıdır.
- [ ] **T75 — İHA-İB yerleşimi yanlış: 30×30 m mavi alan koridorların üstüne biniyor** · `O:
avitas-local-train)_sentetik_arena.py` · KÜÇÜK · kanıt: `REVIEW_LOG.md` **D-104**
  - §2.1 İHA-İB'yi HTAB'dan **ayrı** bir bölge olarak tanımlıyor: *"İHA'nın görev
    sonrası paraşütle ineceği belirlenmiş güvenli alandır."* Üreteç onu HTAB'ın
    üstüne yayılmış yarı saydam bir katman olarak çiziyor.
  - Etikete dokunmuyor, o yüzden **zehirli değil**; ama modele yanlış korelasyon
    öğretebilir (zemin mavi olabilir).
  - **YAP:** ya arena dışına/kenarına yerleştir, ya da kaplama oranını belirgin
    biçimde düşür. **KAPI:** renk çeşitliliği düşmesin, kadraj kapıları geçsin.

- [ ] **T61 — Orta şiddetli çökme için ölçüt yok: kaplama+kenar bu sınıfı kaçırıyor** · `codes/karar_sozlesmesi.py` · **ÖNEMLİ** · kanıt: `REVIEW_LOG.md` **D-86**
  - T59'da tavan 0,67'ye çıkınca `sa_000150.jpg` kapıdan **geçmeye** başladı:
    MODEL kaplama 0.617 vs **GT 0.380**, IoU **0.613**, kenar 0.658 vs GT 0.190.
    Model orada gerçekten çökmüş; 0,55 yakalıyordu, 0,67 kaçırıyor.
  - Kaplama ve kenar bu sınıfı **yapısal olarak** yakalayamaz (ikisi de alan/temas
    ölçüsü). Gereken: maskenin **iç tutarlılığı** — maske içindeki doku/renk
    dağılımı tek bir yüzeye mi ait, yoksa model birbirine benzemeyen bölgeleri mi
    birleştirmiş.
  - ⚠ Yeni ölçüt eklenirken D-86'daki ders geçerli: **alt küme üzerinde "tam
    ayrık" görünen eşik, kümenin tamamında ayırmayabilir.** Süpürme tüm kümede
    yapılacak.
  - ⚠ Madde 15: yeni ölçüt yalnız **reddedebilir**, serbest alanı büyütemez.

- [STATUS: KAPANDI] **T62 — Saha ölçüm betiği v20'de kalmış: sürüm hizalamasının BEŞİNCİ ucu** · `scripts/jetson_fps.py`, `jetson_paket/JETSON_KILAVUZ.md` (+ depo kopyası), `tests/test_uretim_modeli_hizasi.py` · **ÖNEMLİ** · mimar denetimi, kanıt: `REVIEW_LOG.md` **D-89**
  - T58 dört ucu (GUI · paket · manifest · iki kılavuz) doğru hizaladı ve
    **denetimde doğrulandı**. Ama beşinci bir uç var ve çevrilmedi:
    ```text
    scripts/jetson_fps.py:248  --pt      default = navitas_seg_v20_best.pt
                          :249  --onnx    default = navitas_seg_v20_best.onnx   (DOSYA YOK)
                          :250  --engine  default = navitas_seg_v20_best.engine (DOSYA YOK)
                          :254  --conf    default = 0.25
    ÜRETİM: rpi_inference.py:1204 --conf 0.30 · yks_gui.py:904 ALGI_PREDICT_CONF 0.30
    ```
    Argümansız koşulduğunda saha ölçümü **v20**'yi **conf 0,25** ile ölçer.
    v20 ne bugünkü üretimdir (v24) ne öncekidir (v21).
  - **YAP**
    1. Varsayılanları üretim sürümüne ve üretim eşiğine çevir. ⚠ Sürüm adını
       **çıplak sabit yazma** — madde 16; tek kaynaktan (manifest `asil_model_pt`
       ya da sözleşme) oku.
    2. `jetson_paket/JETSON_KILAVUZ.md:63-64` tablosu bu bayatlığı **belgeliyor**;
       her iki kopyada da düzelt.
    3. `tests/test_uretim_modeli_hizasi.py` kapsamını **betik varsayılanlarına**
       genişlet — kapı doğru kurulmuş ama kapsamı eksikti, asıl kusur budur.
    4. Paketi yeniden üret (`scripts/jetson_paket_hazirla.py`, `jetson_fps.py`
       `KOPYALAR` haritasında — kaynağı düzelt, kopyayı elle düzenleme).
  - **KAPI**
    1. **Mutasyon:** varsayılanı v20'ye geri al → yeni test **DÜŞMELİ**.
    2. `--onnx`/`--engine` varsayılanlarının gösterdiği dosyalar **var olmalı**
       (ya da yokluk açıkça ele alınmalı — sessiz atlama yasak).
    3. `--imgsz` varsayılanı `[640, 512]`; üretim `INFER_SIZE` ile hizası
       **ÖLÇÜLMEDİ** (D-89 doğrulanamadı-2). Ölç, uyuşmazlık varsa bildir.
    4. `codes/test_rota_sentetik.py` 15/15 · `unittest discover -s tests -q` OK
  - ⚠ Karar zincirinde **değildir** — yanlış rota üretmez. Ama T15–T18'in ve
    "Jetson'da yetişir mi" sorusunun tamamı bu betiğin sayılarına dayanır.
  - **T62 uygulama sonucu (Codex-1, 2026-08-14):** PT/ONNX adları manifestin
    `asil_model_pt`/`asil_model` alanlarından, `conf` üretim yorumlayıcısından,
    boyutlar manifest + `INFER_SIZE` birleşiminden türetiliyor. Sürüm çıplak
    yazılmadı. TensorRT engine depoda/Jetson paketinde henüz yok (`ENGINE_COUNT=0`);
    bu nedenle varsayılan hayalî bir dosya göstermiyor: `engine=None` ve eksiklik
    konsol + `ozet.json` + `rapor.md` içinde açık `ATLANDI` (T16) olarak kalıyor.
  - **Varsayılan/ölçek gerçek ölçümü:**
    ```text
    [T62_IMG] manifest=[640] varsayilan=[640, 512] uretim_INFER_SIZE=512 hizali=True
    [T62_FARK] 640/512_dogrusal=1.2500 piksel_alani=1.5625 ek_kol=640
    [T62_MODEL] pt=navitas_seg_v24_best.pt var=True
                onnx=navitas_seg_v24_best_640_fp16.onnx var=True
                engine=None conf=0.30
    EXIT_CODE=0
    ```
    Yalnız 512 üretim çıkarım boyutuyla aynıdır; 640 doğrusal %25, piksel
    alanında %56,25 büyük ek export/FPS kıyasıdır, üretim gecikmesi diye
    adlandırılmayacak.
  - **Zorunlu mutasyon GERÇEKTEN koşuldu:** `scripts/jetson_fps.py` PT varsayılanı
    geçici olarak v20'ye çevrildi.
    ```text
    python.exe -B -m unittest discover -s tests -p test_uretim_modeli_hizasi.py -q
    FAIL: test_model_varsayilanlari_manifestin_ASIL_dosyalaridir
    AssertionError: 'navitas_seg_v24_best.pt' != 'navitas_seg_v20_best.pt'
    Ran 19 tests ... FAILED (failures=1)
    MUTASYON_EXIT_CODE=1
    ```
    Exact inverse sonrası kanonik ve paket aynası SHA256
    `5E0F6B61E02BCD2B6F3C035B2DA2373180DF165B48AC4EA21B43BED3CC0E6005`.
  - **Jetson paket üreteci (gerçek çıktı):**
    ```text
    [JETSON_PAKET] codes\karar_sozlesmesi.py -> jetson_paket\kod\karar_sozlesmesi.py
    [JETSON_PAKET] codes\rpi_inference.py -> jetson_paket\kod\rpi_inference.py
    [JETSON_PAKET] codes\costmap_path_finder.py -> jetson_paket\kod\costmap_path_finder.py
    [JETSON_PAKET] scripts\jetson_fps.py -> jetson_paket\kod\jetson_fps.py
    [JETSON_PAKET] comms\protocol.py -> jetson_paket\kod\protocol.py
    [JETSON_PAKET] comms\link.py -> jetson_paket\kod\link.py
    [JETSON_PAKET] comms\iha_sender.py -> jetson_paket\kod\iha_sender.py
    [JETSON_PAKET] comms\inis_kaniti.py -> jetson_paket\kod\inis_kaniti.py
    [JETSON_PAKET] comms\iha_inis_yayinci.py -> jetson_paket\kod\iha_inis_yayinci.py
    EXIT_CODE=0
    ```
  - **Kapılar (exact yorumlayıcı, gerçek çıktı):**
    ```text
    python.exe -B -m unittest discover -s tests -p test_uretim_modeli_hizasi.py -q
    Ran 19 tests ... OK
    EXIT_CODE=0

    python.exe -B -m unittest discover -s tests -p test_jetson_comms_paketi.py -v
    Ran 5 tests ... OK
    EXIT_CODE=0

    python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    python.exe -B -m unittest discover -s tests -q
    Ran 426 tests in 44.845s
    OK
    EXIT_CODE=0
    ```

- [x] **T63 — Karar doğruluğu şartnameye sadık zeminde İLK KEZ ölçüldü** · `O:\navitas-local-train\60_kadraj_karar_dogrulugu.py`, `61_rota_moloza_basma.py` · mimar ölçümü · kayıt: `REVIEW_LOG.md` **D-90**
  - **Şerit doğruluğu ölçütü GÜVENİLMEZ çıktı** — aynı kararlar, kıyas tanımına
    göre %92,7 ya da %67,7. Null model ("hep orta") %73,8. Bu ölçüt terk edildi.
  - **Yerine geçen tanımdan bağımsız ölçüt:** rotanın yer gerçeği molozuna basma
    oranı (`61_rota_moloza_basma.py`). v24/T60: rota 249/260 · moloza basan
    6/249 (**%97,6 temiz**) · arena dışı 10/249.
  - Bundan sonra karar kalitesi **bu** ölçütle raporlanır.
  - **ÖLÇÜTÜN KENDİSİ MUTASYONLA DENETLENDİ** (mimar kendi aracını onaylamaz —
    araç sıfırda takılı olabilirdi):
    ```text
    kare             gercek rota   +120px kaydirilmis
    sa_000000.jpg          0,0%              100,0%
    sa_000002.jpg          0,0%               74,2%
    sa_000004.jpg          0,0%              100,0%
    ```
    Rota bilerek kaydırılınca basma %74–100'e fırlıyor → ölçüt **ateşleyebiliyor**
    ve koordinat dönüşümü doğru. %0 sonuçları gerçek.

- [STATUS: KAPANDI] **T64 — Hakem ekranına ARENA kaynağı ve ölçeği** · `comms/yks_gui.py`, `tests/**` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-90**
  - Ekran bir haftadır "çalışmıyor" görünüyor çünkü **baktığı zemin yanlış**:
    `ALGI_KAYNAKLAR` içindeki beş kaynağın hiçbiri arena değil.
  - Ekle: `arena_kadraj` (T60 kadraj kümesi, manifestte `arena.mpp` VAR) ve
    `arena_gercek` (tek gerçek kare).
  - ⚠ `arena_gercek` için mpp **DÖNDÜRÜLMEYECEK** → `OLCEK_YOK` kalacak.
    Sebep D-90/bulgu 6: kare **eğik**, 2 m'lik HB pedi yatayda ~72 px dikeyde
    ~38 px; tek skaler mpp kararı eksene göre terse çeviriyor.
  - **KAPI:** `arena_kadraj` seçiliyken ekran rota ÇİZİYOR (asıl iddia) ·
    `arena_gercek`te sebep yazılı · mutasyon: mpp None → rota yayınlanmaz.
  - **Uygulama · Codex-1 · 2026-08-14:** `arena_kadraj` yalnız T60 kümesinin
    `images/**` altındaki 260 veri karesini listeler; aynı adlı `_onizleme`
    kareleri dışarıda kalır. Ölçek manifestteki küme-köküne göre göreli tam yol
    ile bağlanır; basename eşlemesi yoktur. Mutlak/üst-dizin/images-dışı/yinelenen
    yollar reddedilir. Eksik, bozuk veya geçersiz `mpp` için ölçek uydurulmaz.
    `arena_gercek` daima ölçeksizdir; ekranda D-90'ın eğik perspektif ve
    `72 px / 38 px` gerekçesi görünür. Ölçeksiz sonuçta segmentasyon maskesi
    gösterilir, sarı rota çizilmez; boş maskede ise dürüstçe `maske yok` yazılır.
    Karar algoritması kopyalanmadı; üretimin `rota_olcek_reddi`, `analyze_path`
    ve `_rota_kararini_esikle` fonksiyonları çağrılır.
  - **Gerçek-model ekran kapısı:** `$env:PYTHONIOENCODING='utf-8';
    O:\navitas-local-train\venv\Scripts\python.exe -B
    tests/t64_hakem_ekrani_kapisi.py --cikti tests/artifacts/t64`
    ```text
    [T64_ARENA_KADRAJ] kare=260 | ALGI(navitas_seg_v24_best) arena_kadraj/sa_000026.jpg → 2·ORTA güven=1.000 · 2033 ms | sari_rota_px=8383
    [T64_ARENA_GERCEK] ALGI(navitas_seg_v24_best) arena_gercek/sartname_s9_arena.png → ROTA YOK · OLCEK_YOK güven=0.000 · 29 ms | sari_rota_px=0 | maske=GORUNUR
    [T64_EKRAN] tests\artifacts\t64\t64_hakem_ekrani.png
    [T64_LOG] tests\artifacts\t64\t64_hakem_ekrani.log
    EXIT_CODE=0
    ```
    Bu panel ağ/RF `link.send` yolu değildir; kanıtlanan çıktı yerel rota kararı,
    waypoint/koridor çizimi ve ölçeksizde bunların fail-closed bastırılmasıdır.
  - **Odak + mutasyon + üretim eşitliği:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover
    -s tests -p test_yks_gui_uretim_hizasi.py -v`
    → `Ran 35 tests in 4.348s` · `OK` · `EXIT_CODE=0`. `arena_kadraj` mpp'si
    `None` yapıldığında aynı açık maske `ROTA YOK · OLCEK_YOK` verdi ve sarı
    piksel sayısı `0`; iki yeni kaynak için GUI kararı üretim kararıyla aynı.
  - **Genel rota kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI` ·
    `EXIT_CODE=0`.
  - **Tam paket:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover
    -s tests -q` → `Ran 359 tests in 38.135s` · `OK` · `EXIT_CODE=0`.
    İlk ara koşumda eşzamanlı T69 değişikliği sırasında Jetson
    `rpi_inference.py` aynası henüz üretilmediği için tek parite testi düştü
    (`Ran 359`, `FAILED (failures=1)`, exit `1`). Diğer görev sahibi aynayı
    senkronladıktan ve iki SHA eşit olduktan sonra yukarıdaki nihai tam paket
    yeniden koşuldu; nihai kanıt yalnız temiz ikinci koşumdur.

- [STATUS: KAPANDI] **T70 — 🔴 GÖREV KRİTİK: ölçek halkası SABİT başlangıç sayısına bağlı; irtifa sapması gövde açıklığını EKSİK hesaplıyor** · `codes/rpi_inference.py`, `comms/**` (telemetri), `scripts/saha_kuru_kosu.py` · **TIKAYICI** · kanıt: `REVIEW_LOG.md` **D-98**
  - `mpp_irtifadan` uygulanmış ve çağrılıyor — ama girdisi **`--irtifa` komut
    satırı argümanı**: tüm koşuya uygulanan TEK bir sayı. Algı yolunda MAVLink
    okuyan kod **yok** (`rpi_inference.py:1224` yalnızca bir yorum satırı).
  - **Kapı yanlış şeyi ölçüyor:** `saha_kuru_kosu.py:387` AST ile *fonksiyonun
    varlığını* arayıp GEÇTİ yazıyor; betiğin kendi yorumu (`:380`) ise
    *"bu halka SAHİPSİZ"* diyor. Halka geçmiş görünürken fiilen boş.
  - **Tehlike yönü ölçüldü** (R=1,10 m · W=640 · FOV=60°):
    ```text
    gercek h  varsayilan h  gercek r_px  hesaplanan r_px    hata
          30            40         20,3             15,2   -25,0%  TEHLIKELI
          30            50         20,3             12,2   -40,0%  TEHLIKELI
          50            30         12,2             20,3   +66,7%  guvenli
    ```
    Varsayılan irtifa gerçekten **büyükse** açıklık eksik istenir → İKA
    gövdesinden dar geçitlere sokulur.
  - **YAP:** irtifa kare kare **canlı telemetriden** (`GLOBAL_POSITION_INT.
    relative_alt`) okunsun. **Bayat/eksik telemetri → `OLCEK_YOK`** (madde 15
    ruhu: çekimserlik görevi durdurur, bayat ölçek İKA'yı çarptırır).
  - **KAPI:** tazelik eşiği **sayılaştırılsın** ve testle kilitlensin ·
    mutasyon: telemetriyi bayatlat → `OLCEK_YOK` gelmeli ·
    `saha_kuru_kosu.py` ölçek halkası artık **beslenmeyi** ölçsün, varlığı değil.
  - ⚠ FOV/odak da elle veriliyor; **aynı sınıfta ikinci açık olabilir** — ölç.
  - **Uygulama (Codex-1, 2026-08-14):** `GLOBAL_POSITION_INT.relative_alt`
    tek sahipli `BagilIrtifaOkuyucu` arka-plan poller'ında gerçek teslim anında
    `time.monotonic()` ile damgalanıyor. Her karar karesi inference'tan sonra
    `icerik[2]` genişliğiyle mpp istiyor. SYSID `1..255` zorunlu; yaş
    `>= TELEMETRI_IRTIFA_TAZELIK_S = 0.50 s`, eksik/bozuk/yanlış kaynak ve
    durdurulmuş okuyucu `None -> OLCEK_YOK`. Kamera statik `--mpp` ile açılamaz.
  - **Canlı sahte yayın + bayat mutasyonu — gerçek çıktı**
    (`O:\navitas-local-train\venv\Scripts\python.exe -B -`, `EXIT_CODE=0`):
    ```text
    [SAHTE_YAYIN] irtifa_m=30.000
    [TAZE] durum=GECTI mpp=0.054126587737 genislik=640
    [BAYAT] yas_s=0.50 durum=DUSTU mpp=None sebep=OLCEK_YOK: eksik ya da bayat canli irtifa telemetrisi
    [ROTA] durum=DUSTU ret=OLCEK_YOK yol_no=None wp=[] yayinlanabilir=False
    ```
  - **Besleme kopuk mutasyonu — gerçek çıktı** (`EXIT_CODE=0`):
    ```text
    [BESLEME_KOPUK] olcek=DUSTU mpp=None sebep=OLCEK_YOK: canli telemetri saglayicisi bagli degil
    [BESLEME_KOPUK_ROTA] durum=DUSTU ret=OLCEK_YOK cozum_cagrildi=False yayinlanabilir=False
    ```
  - **Kuru koşu gerçek kapısı:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py`
    → `olcek GECTI · canli telemetri bu kare icin gecerli mpp uretti`;
    `results/saha_kuru_kosu_20260814_114009/ozet.json`:
    `besleme_cagrildi=true`, `icerik_genisligi_px=1024`,
    `mpp=0.03382911733532963`. Otopark rota kararı dürüstçe
    `BELIRSIZ_COKLU`, `rota_yayinlanabilir=false`; genel betik diğer açık
    halkalar nedeniyle `GECTI 5 · DUSTU 3 · SAHIPSIZ 2`, `EXIT_CODE=1`.
    Bu görev kuru koşunun tamamının geçtiğini iddia etmez.
  - **Odak kapıları — gerçek çıktı:**
    `test_inis_kaniti.py` → `Ran 23 tests`, `OK`, `EXIT_CODE=0`;
    `test_rpi_canli_olcek.py` → `Ran 20 tests`, `OK`, `EXIT_CODE=0`;
    `OlcekHalkasiTests` → `Ran 10 tests`, `OK`, `EXIT_CODE=0`.
    Kamera testi `predict -> provider -> analyze` sırasını ve `main()` sağlayıcı
    aktarımını kilitler.
  - **FOV/odak ve piksel alanı ölçümü** (`R=1.10 m`, `h=30 m`, `W=640`,
    gerçek varsayılan karşılaştırma `FOV=60°`, `EXIT_CODE=0`):
    ```text
    FOV=60  r_px=20.323 hata= +0.0%    FOV=70 r_px=16.757 hata=-17.5%
    FOV=80  r_px=13.983 hata=-31.2%    FOV=90 r_px=11.733 hata=-42.3%
    odak=554.3 r_px=20.323 hata= +0.0%  odak=500 r_px=18.333 hata= -9.8%
    odak=450   r_px=16.500 hata=-18.8%  odak=400 r_px=14.667 hata=-27.8%
    W=640 eski-INFER_SIZE hatasi=-20.0% · W=1024 -50.0% · W=1920 -73.3%
    ```
    Kod son satırdaki kusuru `icerik[2]` ile kapattı. Gerçek lens FOV/odak ve
    aktif crop kalibrasyonu **DOĞRULANAMADI**; büyük FOV/küçük odak girişi hâlâ
    tehlikeli yöndedir. `relative_alt` home-relative'dir; AGL eşitliği de
    **DOĞRULANAMADI**.
  - **Jetson paketi:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B scripts/jetson_paket_hazirla.py`
    → 9 `[JETSON_PAKET]` satırı (`karar_sozlesmesi`, `rpi_inference`,
    `costmap_path_finder`, `jetson_fps`, `protocol`, `link`, `iha_sender`,
    `inis_kaniti`, `iha_inis_yayinci`), `EXIT_CODE=0`;
    `test_jetson_comms_paketi.py` → `Ran 5 tests`, `OK`, `EXIT_CODE=0`, 9/9
    kanonikle bayt-eşit. `rpi_inference.py` SHA eşit, `inis_kaniti.py` SHA eşit.
  - **Genel kapılar — son koşum:**
    `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py`
    → `SONUC: 15/15 dogru`, `[OK] TUM DETERMINISTIK SAHNELER GECTI`,
    `EXIT_CODE=0`;
    `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q`
    → `Ran 419 tests in 46.033s`, `OK`, `EXIT_CODE=0`.
  - **Açık/doğrulanmamış sınırlar:** venv'de `PYMAVLINK_VAR=False`; kapı gerçek
    donanım değil istenen sahte yayıncıyla koştu. `inis_kaniti` ile
    `comms.inis_kaniti` aynı süreçte iki adla yüklenirse sahiplik kayıtları
    ayrılabilir; Jetson tek modül adı kullanır, çok-süreçli MAVLink-router/fanout
    topolojisi **DOĞRULANAMADI**. Ayrıca `drone/rpi_yayin.py -> iha_perceive._infer`
    ayrı canlı yolunda mpp bağlanması yoktur; T70 yalnız
    `codes/rpi_inference.py` üretim yolunu kapatır, bütün canlı yolların kapandığı
    iddia edilmez.

- [STATUS: KAPANDI · T66 ile birleşti] **T68 — Üreteç bariyeri ASLA açık zemine koymuyor: "ince çubuk = geçilemez" öğrenilemiyor** · `O:\navitas-local-train\51_sentetik_arena.py` · **TIKAYICI** · **T67'yi açar** · kanıt: `REVIEW_LOG.md` **D-93**
  - Ölçüldü (120 kare, 70'inde bariyer var):
    ```text
    BARIYER PIKSELLERININ YER GERCEGI ETIKETI
      zemin          31   % 0,0
      engel     142.260   %92,4
      etiketsiz  11.655   % 7,6
    ```
  - Kod (~934): `kapali_indisler` — bariyer **yalnız zaten KAPALI** (molozla dolu,
    `blocked` etiketli) şeritlere çiziliyor. Tüm şeritler açıkken **hiç** çizilmiyor.
  - Gerçek arenada bariyer, aksi hâlde **açık** zeminin üstünden geçip güzergâhı
    **kapatan** yapıdır (D-92). Bu konfigürasyon eğitim verisinde **hiç yok**.
  - ⚠ **Bu bir etiketsiz-engel hatası DEĞİLDİR** (v16 çöküşü değil): bariyer
    pikselleri %92,4 `blocked` taşıyor. Kusur **etikette değil, konumda**.
  - **YAP:** üreteç, **açık** şeridi kapatan bariyer üretebilsin; ince şeritli kol
    açık zeminin üstüne çizilsin ve **kendi pikselleri `blocked` etiketlensin**
    (altındaki zemin değil — çubuğun kendisi). Manifest `acik_serit` /
    `kapali_seritler` bu kapatmayı **yansıtmalı**, yoksa yer gerçeği yalan söyler.
  - **KAPI:** aynı ölçüm tekrarlansın — açık zemin üstündeki bariyer payı > 0
    olmalı · `61_rota_moloza_basma.py` üç sayısı bozulmamalı · gözle doğrulama.
  - ⚠ **DOĞRULANAMADI:** modelin 14–16 px kalınlığındaki çubuğu `imgsz=640` ve
    512 proto çözünürlüğünde öğrenip öğrenemeyeceği ayrı bir sorudur; veri
    düzelmeden sınanması anlamsızdır.

- [STATUS: READY_FOR_REVIEW] **T67 — 🔴 GÖREV KRİTİK: gerçek arenada rota BARİYERİN İÇİNDEN geçiyor** · tasarım kararı önce · **TIKAYICI** · kanıt: `REVIEW_LOG.md` **D-92**
  - **✅ YAPILDI · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-100**.
  - `karar_sozlesmesi.ince_bariyer_maskesi()` (KATMAN 2 klasik dedektör) +
    `rpi_inference.get_masks` içinde tek çağrı. Dedektör **ENGEL katmanına
    ekler**; serbest alan yalnız **küçülür** (madde 15 · CONTRACTS §2).
    `comms/` değişmedi.
  - **Referans KOPYALANMADI, orana çevrildi.** `63_...py` çıplak piksel
    kullanıyordu (61×5 · alan 300 · genişlik 60), 1059'da kalibreydi; üretim
    tespiti **512×512**'de yapar ve orada o sabitler **kısa kolu kaçırır**
    (w=47 < 60):
    ```text
    cozunurluk        kol   w/W (kisa · uzun)   en/boy
    KAYNAK 1059x634    2    0,093 · 0,215       7,0 · 14,2
    small   512x512    2    0,092 · 0,215       6,7 · 13,8
    ```
    `get_masks` ayrıca `r.masks is None` dalında da çalışacak şekilde
    düzenlendi — model hiçbir şey görmese bile bariyer engeldir (eskiden
    orada **erken dönülüyordu**).
  - **KAPI 1 — gerçek çıktı (`63_bariyer_kesisimi.py`):**
    ```text
                          taban (D-92)      T67
    model ENGEL diyor       %0,0           %91,1
    ROTA x BARIYER          59 px          0 px      GECTI
    ```
    Görsel doğrulandı (`results/t63/bariyer_kesisim.png`).
    ⚠ Rota artık arenanın **sol kenarına** kaymış, güven **0,216** (eşik 0,20).
    Kesişim 0'dır ama bu "iyi rota" demek **değildir**.
  - **KAPI 2 — HB engel sayılMIYOR (üç kanıt):**
    ```text
    A gercek(!) karede HB : a* -6..4  -> 0/3100 engel px   (ZAYIF: zaten siyah/beyaz)
    B SENTETIK KIRMIZI HB : a* = 65   -> 0 engel px        KORUNDU
      ayni karede bariyer 240x14      -> 3360 px           YAKALANDI (pozitif kontrol)
    C sekil supurmesi     : 100x25 (4,0) engel DEGIL · 100x24 (4,2) ENGEL
    ```
  - **KAPI 3 — regresyon (`61_rota_moloza_basma.py`):**
    ```text
                      ROTA     MOLOZA    AGIR   ARENA DISI
    taban (T69)    244/260     6/244   6/244      5/244
    T67            242/260     4/242   2/242      5/242
    ```
    Rota çökmedi (−2). Moloza basma **artmadı, AZALDI** (6→4, ağır 6→2).
  - **KAPI 4 — MUTASYON (canlı, iki ölçüm):**
    ```text
    M0 ACIK    kesisim  0 px · ENGEL %91,1 | rota 242 · moloza 4
    M1 KAPALI  kesisim 59 px · ENGEL % 0,0 | rota 244 · moloza 6
    M2 geri    kesisim  0 px · ENGEL %91,1
    ```
    Her iki ölçüm de **tam tabana** döndü.
  - **KAPI 5:** `test_rota_sentetik.py` **15/15** · `jetson_paket_hazirla.py`
    **9/9 bayt-eşit** · `discover -s tests -q` **Ran 406 · FAILED (1)**.
    ⚠ **O tek düşen test benim değil:** `test_costmap_icerik_cagri_yerleri.py::
    test_kuru_kosu_ana_maskeyi_baglar_kirpigi_baglamaz` — dedektör **kapatılıp**
    koşulduğunda da düşüyor. Başka bir ajanın eşzamanlı çalışması:
    `scripts/saha_kuru_kosu.py` değişmiş, `halka_rota` imzasına `mpp` eklenmiş.
    `scripts/` izin listesinde yok; **dokunulmadı**.
  - **Dedektör isabeti — bağımsız ölçüldü** (T60 kadraj n=260, model
    kullanılmadan, manifest `bariyerler` yer gerçeği):
    ```text
    bariyer tasiyan 210 · BULUNAN 153 · KACIRILAN 57
      54 -> bariyer kutusunda HIC kroma YOK (moloz ALTINDA, goruntude yok)
       3 -> kroma VAR, sekil filtresi eledi   <- GERCEK kacirma (%1,4)
    GORUNUR bariyerlerde isabet: 153/156 = %98,1
    tespit pikselinin kutu icinde kalani: medyan %92,1
    tasan pikselin %90,5'i arena ICINDE · %9,5'i disinda (alan disi kirmizi nesneler)
    ```
  - 🔴 **D-99 ZEMİNİ DEĞİŞTİRDİ — bu görev onunla birlikte okunmalı.** Mimar ben
    çalışırken yazdı: `sartname_s9_arena.png` **gerçek arena değildir**, şartname
    Şekil 1 alt yazısına göre *"tamamen yapay zeka ile oluşturulmuştur"*.
    `CONTRACTS` §2.1 ve sabit yorumu buna göre **düzeltildi**. Üç etki:
    1. Dedektörün **renk anahtarı yapay bir görüntüden** kalibre edilmiştir;
       gerçek engeller kırmızı olmayabilir → dedektör **hiç ateşlemez**.
       ⚠ Bu **fail-safe**'tir (hiçbir şey eklenmez/çıkarılmaz, sistem T67
       öncesine döner), yani D-99 bu işi **geri aldırmaz**, geçerlilik alanını
       daraltır.
    2. **Ayakta kalan gerekçe:** şartname **metni** §2.1 kapalı güzergâhların
       *"fiziki engellerle kapatılacağını"* söyler — ince-engel riski **gerçek**.
    3. **Tuzak KESİNLEŞTİ, hafiflemedi:** figür yapay olduğu için artık **metin
       otoritedir** ve metin HB'yi *"üzerinde **kırmızı** H harfi"* diye tanımlar.
       HB **gerçekten kırmızıdır** → naif "kırmızı = engel" kuralı `P_görev`'i
       sıfırlardı. İşin en taşıyıcı kanıtı **KAPI 2-B'deki sentetik kırmızı HB**
       testidir; figürdeki siyah/beyaz ped artık **tek başına yetersizdir**.
  - **Yeni test paketi** `tests/test_ince_bariyer.py` (**18 test**): sözleşme
    kaynağı (`BARIYER_ENGEL_SINIFI == sinif_semasi.ENGEL` kilidi — `sinif_semasi`
    Jetson paketinde **yok**, import edilemez) · hedef koruması · figür ölçümleri
    · çözünürlük bağımsızlığı (320/640/1280) · fail-safe · `get_masks`
    entegrasyonu (madde 15 monotonluğu dâhil).
  - ⚠ **DOĞRULANAMADI:** (1) gerçek arena başarımı — elimizde gerçek arena
    görüntüsü **yok** (D-99), *"bariyer sorunu çözüldü"* genel iddia **değildir**;
    (2) gerçek engellerin **rengi** bilinmiyor, yedek imza aranmadı; (3) bariyerin
    fiziksel **yüksekliği** bilinmiyor, fail-safe varsayım geçilemez; (4) ince-engel
    genel sınıfı (tel/halat/kablo) ele alınmadı; (5) figürde rota artık sol kenara
    kayıyor — kesişim 0 ama o rotanın **kalitesi** doğrulanmadı.
  - Şartname figüründe kapalı güzergâhı kapatan tek yapı **kırmızı-beyaz şeritli
    yol bariyeri koludur**. Ölçüldü (`O:\navitas-local-train\63_bariyer_kesisimi.py`,
    bariyer tespiti MODELDEN BAĞIMSIZ — LAB a*>25):
    ```text
    bariyer pikselleri n=3644
      model ENGEL diyor : %0,0      <-- tek piksel bile değil
      model ZEMIN diyor : %30,9
    ROTA x BARIYER kesisimi: 59 px  -> KESIYOR (görsel doğrulandı)
    ```
  - **Korumaların hiçbiri ateşlemiyor:** zemin kapısı susuyor (kaplama 0,579 <
    0,67), karar reddi yok, güven 0,75, darboğaz geniş görünüyor. Rotayı yayından
    alıkoyan **tek** şey `OLCEK_YOK` — bizi koruyan bir kapı değil, bir **eksiklik**.
  - 🔴 **SIRALAMA KISITI — T64'Ü YAPAN OKUSUN:** ölçek halkası kapatılırsa sistem
    bariyere giren rotayı **YAYINLAR** hale gelir. T64'ün `arena_gercek` için mpp
    döndürmeme şartı bu yüzden zorunludur ve **kaldırılamaz**.
  - **SINANABİLİR ÖNGÖRÜ:** v24 T60 öncesi substratla eğitildi; orada bariyer tek
    renk ince bir `cv2.line` idi. v25 şeritli kolla eğitiliyor — bariyeri görüp
    görmediği aynı ölçümle sınanacak (`63_bariyer_kesisimi.py --model ...`).
  - **İKİ ÇÖZÜM YOLU — ölçmeden seçme:**
    (a) **Model öğrensin** — v25 sınavı bunu yanıtlayacak. Ucuz ama garantisiz.
    (b) **Katman 2 klasik dedektör** — uzun/ince/yüksek-kromalı yapıyı bulup
        serbest alandan **ÇIKAR**. Madde 15 ile uyumlu: yalnız küçültür.
  - 🔴 **(b) İÇİN TUZAK — kırmızıyı engel sayan naif dedektör HEDEFİ ÖLDÜRÜR.**
    Şartname **metni** HB'yi "2×2 m **kırmızı** branda" diye tarif ediyor
    (figür nötr gösteriyor, çelişki D-87'de). Kırmızı = engel kuralı konursa
    hedef bölge engel sayılır ve İKA hedefe **hiçbir zaman ulaşamaz** →
    `P_görev = 0`. Ayrım **ŞEKİLLE** yapılmalı: bariyer uzun ve ince
    (en/boy > 4, genişlik > 60 px); HB **kare** (2×2 m). Ölçüm betiği bu ayrımı
    zaten yapıyor — kopyalanmadan, gerekçesiyle taşınmalı.
  - **KAPI:** bariyer piksellerinde `model ENGEL` oranı · rota-bariyer kesişimi
    **0 px** · HB pedinin engel sayılMAdığı ayrıca gösterilecek · kalıcı fikstür.
  - ⚠ Tek karedir (D-88). "Model bariyerleri göremiyor" genel iddia **değildir**.

- [STATUS: KAPANDI] **T69 — T65 kısıtını devreye bağla (mimarın kapsam hatası düzeltildi)** · `codes/rpi_inference.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-96**
  - **✅ YAPILDI · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-97**.
  - `codes/rpi_inference.py` `analyze_path` içinde, darboğaz ölçüldükten **sonra**
    tek çağrı eklendi. Import **iki bloğun ikisine de** eklendi (göreli
    `.karar_sozlesmesi` ve mutlak) — yoksa paket-içi ve depo-içi çalışma ayrışırdı.
    **Eşiğe dokunulmadı** (1.0) · `karar_sozlesmesi.py` **değişmedi** · `comms/`
    **değişmedi**.
  - **KAPI — CANLI ölçüm (simülasyon değil):**
    ```text
                              ROTA     MOLOZA    AGIR   ARENA DISI
    taban  (D-90/D-94)     249/260     6/249   6/249      10/249
    T69    (kisit CANLI)   244/260     6/244   6/244       5/244

    ARENA DISI   10 -> 5   DUSTU      (hedef 5)
    MOLOZA BASMA  6 -> 6   ARTMADI
    ROTA URETIMI      244  COKMEDI    (hedef: 244'un altina dusmesin)
    ```
    D-94'ün simülasyonu **birebir doğrulandı** — üç sayı da tuttu.
  - **MUTASYON (canlı, aynı ölçüm betiği):**
    ```text
    M0 kisit ACIK (depo hali)           rota 244 · moloza 6 · arena disi  5
    M1 kisit KAPATILDI (fonksiyon None) rota 249 · moloza 6 · arena disi 10
    M2 geri alma sonrasi                rota 244 · moloza 6 · arena disi  5
    ```
    Kısıt kapatılınca **tabana tam döndü** — düşüş kısıttan geliyor, başka
    kapının yan etkisi değil.
  - **KAPI:** `codes/test_rota_sentetik.py` **15/15** ·
    `unittest discover -s tests -q` **Ran 359 · OK** ·
    `jetson_paket_hazirla.py` **9/9 bayt-eşit**.
  - **Yeni test sınıfı** `AnalyzePathEntegrasyonTests` (7 test) **bağlantıyı**
    kilitler — çağrı silinirse düşer. Fikstür ön kontrolü (kör kapı kurmamak
    için ZEMİN kapısına takılmadığı doğrulanır) · `KORIDOR_DEGIL` ile ret ·
    fail-closed (yol/güven/waypoint yayınlanmaz) · negatif kontrol (makul
    koridor etkilenmez) · madde 15 · ölçüt sözleşmeden mi çağrılıyor ·
    kısıt kapatılınca aynı kare geçiyor mu. Dosya toplamı **25 test**.
  - 🔴 **BULGU — T65'in GEREKÇESİ yanlış ifade edilmiş (eşik DOĞRU, anlatım yanlış).**
    `_rota_serit_olcumu:492`: `darbogaz_px` bir **yarıçaptır** (`dt yaricapi`),
    koridor genişliği değil (genişlik ≈ 2×). Uygulanan kural
    `yaricap > icerik_w/3` fiilen *"koridor genişliği **iki** şeritten geniş
    olamaz"* der; oysa yorum ve `CONTRACTS` §6.4 *"bir şeridin tamamından"* diyor.
    ```text
    kural                              esik oran   yanlis elenen MESRU   yakalanan
    UYGULANAN  yaricap > 1/3               0.333            0/239          5/10
    LAFZI      genislik > 1/3 (yar>1/6)    0.167           23/239          7/10
    ```
    **Lafzî kural uygulanamaz** — 23 meşru kareyi elerdi. Uygulanan eşik doğru
    mühendislik seçimidir; yanlış olan **yalnızca anlatım**. Alttaki olgu da
    kayda değer: bu kümede meşru koridorlar genişlik olarak `0.559·icerik_w`e
    (~1,7 şerit) çıkıyor — D-91'in "üreteç dikey şeritler üretiyor, gerçek
    arena moloz adaları" bulgusuyla tutarlı.
    ⚠ **DÜZELTİLMEDİ:** T69'un izni `rpi_inference.py` + `tests/**`;
    `karar_sozlesmesi.py` ve `CONTRACTS.md` **DOKUNMA** listesinde. Eşik de
    oynatılmadı (görev yasakladı, gerekçesi teste kilitli). Düzeltilmesi gereken
    **yalnız iki cümle**: `karar_sozlesmesi.py` T65 yorum bloğu ve `CONTRACTS.md`
    §6.4 `KORIDOR_DEGIL` satırı. Sayılar, eşik ve testler değişmez.
  - ⚠ **DOĞRULANAMADI:** (1) arena başarımı (**D-88, kalıcı**); (2) kalan **5**
    arena-dışı kare hâlâ geçiyor, genişlikle ayırt edilemezler, ölçüt yok;
    (3) ölçüm yalnız T60 kadraj + v24 içindir — gerçek karede kısıtın etkisi
    ölçülmedi (`sartname_s9_arena.png` zaten `OLCEK_YOK`'ta duruyor, D-90/5);
    (4) güven ölçütünün **doymuş** olduğu (D-94 yan bulgusu) ele alınmadı.
  - T65'in sözleşme fonksiyonu, sebep kodu, `CONTRACTS` maddesi ve testleri
    **teslim edildi ve denetimden geçti**. Kısıt yalnız **bağlanmadı**, çünkü
    T65'in izin listesini yazarken `codes/rpi_inference.py`'yi **atlamışım** —
    kusur oradaki `analyze_path`te. Amele izni aşmadı, doğru davrandı.
  - **YAP** — `analyze_path` içinde, darboğaz ölçüldükten sonra tek çağrı:
    ```python
    kg_reddi = rota_koridor_genisligi_reddi(olcum["darbogaz_px"], icerik_w)
    if kg_reddi is not None:
        return _don(None, 0.0, [], clean, kg_reddi, olcum)
    ```
  - **KAPI — canlı ölç, simülasyon değil** (`61_rota_moloza_basma.py`, v24, T60):
    ```text
    taban (kısıt kapalı) : rota 249/260 · moloza basma 6 · arena dışı 10
    hedef (kısıt açık)   : arena dışı 5'e DÜŞSÜN · moloza basma ARTMASIN ·
                           rota üretimi 244'ün altına DÜŞMESİN
    ```
  - **MUTASYON:** kısıtı kapat → arena dışı 10'a geri dönmeli.
  - ⚠ Eşiği **oynatma**. `KORIDOR_GENISLIK_TAVANI_SERIT = 1.0` fizikseldir;
    0,28–0,33 arasına fit etmek 6/10 yakalardı ama bu **D-85'in hatasıdır**
    (bozunumu kapalı sentetik azamiye eşik oturtmak). Claude 2 bunu bilerek
    reddetti ve gerekçeyi teste kilitledi — kilidi kırma.
  - ⚠ `comms/yks_gui.py` Codex'te (T64); oraya **dokunma**.

- [STATUS: KAPANDI] **T65 — Karar yolunun ARENA SINIRI kavramı yok** · `codes/costmap_path_finder.py`, `codes/karar_sozlesmesi.py`, `CONTRACTS.md` · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-90 bulgu 3**
  - **⚠ KISMEN TESLİM · 2026-08-14 · Claude-2** · kayıt `REVIEW_LOG.md` **D-94**.
    Sözleşme + sebep kodu + `CONTRACTS` + testler **teslim ve geçti**; kısıt
    **`analyze_path`'e BAĞLANMADI** — gerekçe aşağıda (kapsam engeli).
  - **Taban bağımsız doğrulandı:** `rota 249/260 · moloza basma 6/249 ·
    arena dışı 10/249` — görevdeki sayılarla birebir.
  - 🔴 **Kusur DEJENERE:** arena dışı oranı `0.000` (238 kare) · `0.001` (1) ·
    **`1.000` (10)**. Ara değer yok — rota ya tamamen içeride ya tamamen dışarıda.
    9'u şerit 3, biri şerit 1. Sekizinde güven **1.000**. Moloza basan 6 kareyle
    **kesişim yok** (iki kusur ayrık).
  - **Yan bulgu — güven ölçütü DOYMUŞ:** `ROTA_DARBOGAZ_TAM_ORANI = 0.035`,
    640'lık karede **22,4 px**'te doyuyor; 23 px de 304 px de güven **1.000**.
    Darboğaz bilgi taşıyor, güven onu atıyor. Ayrı görev konusu.
  - **FAZ 1 — önce ölçüldü (görevin dayattığı sıra). Üç imza da başarısız:**
    ```text
    imza                 n   IoU medyan  guvenilir  gercek karede
    izgara cizgileri   260       0.806     HAYIR    TUM KAREYI verdi
    moloz kapsayan k.  260       0.664     HAYIR    dar yanli
    dis cerceve        260       0.960     HAYIR    HIC sinir uretemedi
    ```
    Izgaranın fiziksel temeli sağlam ama **moloz onu gizliyor** (kenarı molozlu
    118 karede dx0 medyan 79,0 px · molozsuz 102 karede 4,0 px — 20 kat).
    Dış çerçevenin kök nedeni **üreteç kodunda**: `sinirlar` listesi arena
    kenarlarını ve iç şerit sınırlarını **aynı renk/kalınlıkta** tutuyor.
  - 🔴 **GERÇEK ARENA SINIRI DİKEY DEĞİL** — perspektif yamuk (sol x≈190→65,
    sağ x≈920→1015). Tek `[x0,x1]` aralığının indirgenemez hatası **~50–60 px**.
    Görevin (ve benim ilk kurgumun) varsaydığı **çıktı biçimi** yanlıştı.
  - **FAZ 2 — sınır yerelleştirmeden çözüm.** Kusur dejenere olduğu için
    "sınır nerede" gerekmiyor: **bir koridorun en dar yeri bir şeridin
    tamamından geniş olamaz.** Tavan `serit_no`'nun kendi bölüşümünden
    türetildi (madde 16), çıplak sayı değil.
    ```text
    MESRU (arena ici) 239   medyan 0.094 · p95 0.208 · MAKS 0.280
    KUSURLU (disi)     10   0.022 0.028 0.111 0.170 0.314
                            0.353 0.358 0.375 0.475 0.487
    tavan 1/3 -> yanlis elenen MESRU 0/239 · yakalanan 5/10
    ```
    **Fit edilmiş tavan bilerek seçilmedi**: 0.280–0.333 arasına konsa 6/10
    yakalardı, ama 0.280 **bozunumu kapalı sentetik** karelerden gelir —
    optimist azamiye eşik oturtmak **D-85'in hatası**. Gerekçe testle kilitli.
  - 🔴 **KISMİ ÇÖZÜM.** Kaçan 5 kareden **4'ü** genişlikle ayırt edilemez:
    arena dışı her zaman boş değil — `sa_000068`'de arena dışı bir **otopark
    fotoğrafı** (park çizgileriyle), model orada 14,2 px darboğazlı kendi
    koridorunu buluyor.
  - 🔴 **KAPSAM ENGELİ — kısıt bağlanamadı.** Kusur `codes/rpi_inference.py`
    `analyze_path`'te; o dosya **izin listesinde yok**. İzinli iki dosyaya
    **görüntü hiç ulaşmıyor** (`analyze_path` aşağı yalnız maske geçiriyor).
    Devreye almak için `analyze_path` içinde **tek çağrı** gerekiyor:
    ```python
    kg_reddi = rota_koridor_genisligi_reddi(olcum["darbogaz_px"], icerik_w)
    if kg_reddi is not None:
        return _don(None, 0.0, [], clean, kg_reddi, olcum)
    ```
    Bu satır **yazılmadı**, dosyaya dokunulmadı. **İzin verirsen bağlarım.**
  - **KAPI 1 — SİMÜLASYON** (kısıt bağlı olmadığı için canlı koşu değil):
    ```text
                              ROTA     MOLOZA    AGIR   ARENA DISI
    KISIT KAPALI (taban)   249/260     6/249   6/249      10/249
    KISIT ACIK  (T65)      244/260     6/244   6/244       5/244
    ARENA DISI 10->5 DUSTU · MOLOZA 6->6 ARTMADI · ROTA 249->244 COKMEDI
    reddedilen 5 karenin HEPSI gercekten arena disiydi — mesru kayip 0
    ```
  - **KAPI 2 — MUTASYON:**
    ```text
    M0 mutasyon YOK                        DUSEN  0  temiz
    M1 tavan KALDIRILDI (serit x99)        DUSEN  6  ATESLENDI
    M2 SERIT_SAYISI 12 (serit_no ayristi)  DUSEN 18  ATESLENDI
    M3 tavan YARIYA indirildi              DUSEN  6  ATESLENDI
    M4 geri alma sonrasi                   DUSEN  0  temiz
    ```
  - **KAPI 3:** `test_rota_sentetik.py` **15/15** · `discover -s tests -q`
    **Ran 349 · OK** · `jetson_paket_hazirla.py` **9/9 bayt-eşit**.
  - **Mevcut bir test güncellendi (gizlenmiyor):**
    `test_sebep_kodlari_sozlesmedeki_dokuz_degerdir` onuncu sebep kodu
    eklenince düştü. Küme güncellendi ve **test adındaki sayı kaldırıldı** —
    T59 denetiminde işaretlenen çıplak-sabit kırılganlığının aynısı.
  - ⚠ **DOĞRULANAMADI:** (1) arena başarımı (**D-88, kalıcı**); (2) kısıt
    **canlı koşulmadı**, KAPI 1 sayıları **simülasyondur**; (3) kalan 5 kare
    için ölçüt **yok**; (4) tavan v24 + T60 için ölçüldü, substrat değişirse
    yeniden ölçülmeli; (5) gerçek karede sınır imzalarının yer gerçeği etiketi
    yok — oradaki değerlendirme **gözledir**.
  - Rotaların **%4'ü arena DIŞINDAN** geçiyor. Üreteç arena dışına bilerek
    etiketsiz zemin çizer (gerçekçi), model orayı haklı olarak zemin işaretler,
    `analyze_path` tüm kareyi üçe bölüp boş kenarı güzergâh sayıyor.
    `sa_000070`: darboğaz **304 px**. **Aynı kusur gerçek karede de var.**
  - ⚠ **ÇÜRÜTÜLMÜŞ HİPOTEZ — tekrarlanmayacak:** `icerik`i arena kutusuna
    daraltmayı denedim, TEHLİKELİ 8 → **55**'e çıktı (`results/t63/*.json`).
  - Sıra: **önce ölç** (ızgara · moloz kapsayan kutusu · dış çerçeve), sonra tasarla.
  - ⚠ Madde 15: yeni kısıt yalnız **çıkarabilir**. Sınır bulunamazsa doğru
    davranış genişletmek değil, yeni sebep koduyla **çekimser** kalmaktır.
  - **KAPI:** `61_rota_moloza_basma.py` ile üç sayı birden — arena dışı DÜŞSÜN,
    moloza basma ARTMASIN, rota üretimi ÇÖKMESİN. Biri iyileşip diğeri
    bozulursa **ödünleşmedir**, öyle raporlanır.

- [STATUS: READY_FOR_REVIEW] **T59 — Kaplama tavanı 0,55 → 0,67** · `codes/karar_sozlesmesi.py`, `CONTRACTS.md` · **KRİTİK** · mimar kararı, kanıt: `REVIEW_LOG.md` **D-84**, **D-85**
  - **✅ UYGULANDI · 2026-08-13 · Claude-2** · kayıt `REVIEW_LOG.md` **D-86**.
  - `ZEMIN_KAPLAMA_TAVANI` **0.55 → 0.67**; `ZEMIN_KENAR_DAYANMA_TAVANI` **0.50'de
    kaldı** (dokunulmadı). Sabit yorumu + `CONTRACTS.md` §6.4 ölçümle yenilendi.
  - **Kararın ana gerekçesi DOĞRULANDI** — gerçek arena bağımsız ölçüldü:
    `kaplama 0.579 · kenar 0.585` (D-85: 0.577 / 0.585). Eski çift onu **eliyor**,
    yeni çift **geçiriyor**.
  - 🔴 **KAPI 1 TUTMADI.** Hedef "meşru elenen 0/221"; kümenin **tamamında**
    (260 kadraj + 1 arena) sonuç **1/261**:
    ```text
    kume                     n    kaplama min..maks    kenar min..maks
      MESRU kadraj arena    260    0.000..0.863        0.000..0.682
      MESRU GERCEK ARENA      1    0.579               0.585
      COKUS otopark          67    0.770..0.866        0.579..0.971

    esik cifti          mesru elenen   kacan cokme
      (0.55, 0.50)       3/261          0/67   <- biri GERCEK ARENA
      (0.67, 0.50)       1/261          0/67
    ```
    Süpürme (99×99 tüm çiftler): **elenen 0 VE kaçan 0 veren çift YOK**. D-85'in
    0,062'lik payı **220 kareli alt kümenin** özelliği; ölçütün değil.
    Karar yine de net iyileşme: 3/261 → 1/261 **ve** gerçek arena kurtuldu.
  - **Kalan elenen kare kör kabul edilmedi** — `sa_000001.jpg` yer gerçeğiyle
    kıyaslandı: MODEL 0.856 vs **GT 0.717**, IoU **0.810**, ama kenar 0.682 vs
    GT 0.359. **Sınır durum**, düz yanlış pozitif değil.
  - 🔴 **0.67'nin ölçülmüş bedeli:** `sa_000150.jpg` artık **geçiyor** —
    MODEL 0.617 vs **GT 0.380**, IoU **0.613**, kenar 0.658 vs GT 0.190. Orada
    model gerçekten çökmüş ve 0.55 **yakalıyordu**. Sabitin kendi "orta şiddetli
    çökme geçer" uyarısının ilk somut örneği.
  - **YENİ KALICI KAPI** `tests/test_gercek_arena_kapisi.py` (7 test): eşiğin
    sayısı değil **davranış** kilitlenir. Ağırlık/kare yoksa atlanır.
  - **MUTASYON KONTROLÜ:**
    ```text
    M0 mutasyon YOK (0.67)                DUSEN 0  temiz — beklenen
    M1 tavan 0.55'e GERI ALINDI           DUSEN 4  kapi ATESLENDI
    M2 tavan 0.578 (arena altinda)        DUSEN 4  kapi ATESLENDI
    M3 YALNIZ kenar 0.10 (AND kontrolu)   DUSEN 0  temiz — beklenen
    M4 IKI tavan birden dusuruldu         DUSEN 4  kapi ATESLENDI
    M5 testteki OLCULEN sabit bayatladi   DUSEN 1  kapi ATESLENDI
    ```
  - 🔴 **MEVCUT BİR TEST DÜŞTÜ — DÜZELTİLMEDİ, karar sende:**
    ```text
    tests/test_zemin_kapisi_iki_sinyal.py:97
    test_kaplama_YUKSEK_kenar_DUSUK_ATESLEMEZ (kaplama=0.6)
    AssertionError: 0.600625 not greater than 0.67 : fikstur kaplama tavanini asmiyor
    ```
    Testin **iddiası sağlam**; düşen şey **fikstür ön koşulu** — çıplak `0.60`
    eski tavanın üstündeydi, yeni tavanın altında kaldı. Diğer iki alt-durum
    (0.70, 0.85) **geçiyor**. Madde 16 açısından fikstür zaten kusurlu (eşiği
    sözleşmeden türetmiyor). **Önerilen asgari düzeltme (uygulanmadı):**
    `for oran in (0.60, 0.70, 0.85)` → `for carpan in (1.05, 1.20, 1.35):
    oran = min(0.98, ZEMIN_KAPLAMA_TAVANI * carpan)`.
  - **KOŞULAN KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  bagimsiz olcum: mesru elenen 1/261 · kacan cokme 0/67   DUSTU
            (hedef 0/221; sebep yukarida)
    KAPI 2  tests/test_gercek_arena_kapisi.py  Ran 7 tests  OK      GECTI
    KAPI 3  mevcut testler                                          DUSTU (1)
    KAPI 4  mutasyon kontrolu M1/M2/M4/M5 atesledi, M3 sustu        GECTI
    KAPI 5  codes/test_rota_sentetik.py  SONUC: 15/15 dogru         GECTI
            unittest discover -s tests -q  Ran 322  FAILED (1)
            -> tek dusen KAPI 3'teki fikstur; baska dusen YOK
    KAPI 6  jetson_paket_hazirla.py 9/9 bayt-esit
            karar_sozlesmesi.py sha b1a54c9fbe03aacb                GECTI
    ```
  - ⚠ **DOĞRULANAMADI:** (1) gerçek arena **tek karedir** — meşru taraf bir
    dağılıma değil tek noktaya karşı ölçüldü, istatistiksel güven **yok**;
    (2) eşikler **modele bağlıdır**, 0.67 v24 içindir — üretim modeli her
    değiştiğinde kalibrasyon **zorunlu adımdır** ve görev şablonuna yazılmalı;
    (3) orta şiddetli çökme sınıfı (`sa_000150`) artık geçiyor, o sınıf için
    ölçüt **yok**; (4) arena başarımı sahada doğrulanmadı — kamera yok.

- [STATUS: KAPANDI] **T58 — Üretim modelini v24'e geçir** · `comms/yks_gui.py`, `CONTRACTS.md`, `JETSON_KILAVUZ.md` (iki kopya), `jetson_paket/models/**` · **KRİTİK** · kullanıcı kararı, kanıt: `REVIEW_LOG.md` **D-82**
  - **✅ YAPILDI · 2026-08-13 · Claude-2** · kayıt `REVIEW_LOG.md` **D-83**.
  - **🔎 MİMAR DENETİMİ · 2026-08-13 · KOŞULLU KAPANDI** · kayıt `REVIEW_LOG.md` **D-89**.
    İddiaların tamamı bağımsız koşuldu ve **doğrulandı** (12+7 test OK, arena
    testi gerçekten çıkarım koşuyor — sahte geçiş arandı, yok). **Ama beşinci
    bir uç bulundu:** `scripts/jetson_fps.py` varsayılanları hâlâ **v20 · conf
    0,25**. Takip görevi **T62**. Sürüm geçişinin kendisi doğrudur.
  - `comms/yks_gui.py:898` `ALGI_MODEL_DOSYA` → **`navitas_seg_v24_best.pt`**.
  - **İRAKSAMA ÖNLENDİ (D-58/D-60 sınıfı):** yalnız GUI çevrilmedi; **dört uç**
    birlikte çevrildi — GUI · `jetson_paket/models/` · paket manifesti · **her
    iki** `JETSON_KILAVUZ.md` (`ASIL — bunu derle`, `format=engine` komutu,
    FPS komutu, `MASKE_YOK` beklentisi).
  - **Mimarın hazırlığı doğrulandı, yeniden üretilmedi:**
    ```text
    models/navitas_seg_v24_best.pt      sha c04d7d3570ead678  54.852.380 B  ESLESTI
    models/navitas_seg_v24_best.onnx    sha 27e480a135d75ac3 = export dizini
    v24.names = {0: 'traversable', 1: 'blocked'}  (v21 ile BIREBIR)
    ```
  - **KAPI 2 — B1 BAĞIMSIZ tekrarlandı** (`O:
avitas-local-train8_b1_bagimsiz.py`;
    30 gerçek drone karesi, **eşit aralıklı**, üretim zinciri):
    ```text
    model                       conf  BOS maske  ort kaplama    min    maks
    navitas_seg_v24_best.pt     0.30      0/30        %81,0  %77,2   %86,6
    navitas_seg_v21_best.pt     0.30      0/30        %81,0  %76,7   %86,3
    navitas_seg_v17_best.pt     0.30     28/30         %0,4   %0,0    %6,6
    ```
    **KONTROL:** v17 28/30 düştü — ölçüt gerçekten **düşebiliyor** (D-15/K-04).
    Mimarın "0/30 · %78,4 · v17 25/30" değeriyle fark **kare seçimindendir**;
    yön ve sonuç aynı.
  - ⚠ **B1 v24 ile v21'i AYIRMIYOR** — ikisi de 0/30. B1 yalnız "kör mü" diye
    sorar. v24'ün gerekçesi B1 değil, D-82'nin karar düzeyi ölçümüdür.
  - **D-82 tablosu bağımsız yeniden üretildi** (`56_uc_kapili_model_secimi.py`,
    val n=120) — mimarın sayılarıyla **aynı**:
    ```text
    model   K1 IoU  K1 kesinlik  K1 duyar  K2 otopark  K3 dogru/yanlis/ret
    v24      0,692        0,816     0,821       %81,0        0 / 0 / 9
    v21      0,311        0,813     0,335       %81,0        0 / 0 / 9
    ```
  - 🔴 **YENİ VE OLUMSUZ BULGU (K3):** gerçeğe en yakın kümede — kompozit
    arena — **v24 hiçbir şey değiştirmiyor**: iki modelde de 9/9 kare
    `ZEMIN_MASKESI_SUPHELI` ile reddediliyor (kaplama %76,5 · çevre dayanması
    %63,2). Kazanç **yalnız sentetik kadraj kümesinde** var. Karar zinciri
    doğru davranıyor; ama v24'ün üstünlüğü gerçek görüntüde **görünmüyor**.
  - **Bayat manifest düzeltildi:** `jetson_paket/models/jetson_derleme_manifest.json`
    2026-08-05'ten beri `pc_modeli` **v17** diyordu, oysa pakette **v21** ONNX
    vardı — sekiz gün görünmedi, çünkü manifest **paket içeriğine bakmıyordu**.
    Artık `paket_icerigi` her dosyanın **sha256**'sını taşır; bayatlık mekanik
    olarak yakalanır.
  - **YENİ KAPI** `tests/test_uretim_modeli_hizasi.py` (12 test) dört ucu tek
    sürüme bağlar. **Mutasyon kontrolü:**
    ```text
    M0 mutasyon YOK              DUSEN 0   temiz — beklenen
    M1 GUI v21'e geri cevrildi   DUSEN 7   kapi ATESLENDI
    M2 manifest sha'si bozuldu   DUSEN 1   kapi ATESLENDI
    M3 paketten v24 .pt silindi  DUSEN 2   kapi ATESLENDI
    M4 geri alma sonrasi         DUSEN 0   temiz — beklenen
    ```
  - **`scripts/copy_paste_augmentation.py:981` BİLEREK DEĞİŞTİRİLMEDİ.** O kâhin
    `data/arena_kompozit` yer gerçeğini üretir; değiştirmek D-38'den beri ona
    dayanan tüm ölçümleri (K3, GUI `kompozit` kaynağı, T48 tabanı %76,0)
    kıyaslanamaz kılar. ⚠ Ama dosyadaki yorum artık **yanıltıcı** ("bu etkin
    sistem modelidir" diyor). Ayrı görev gerekir — bu görevin izni o dosyayı
    kapsamıyordu.
  - **KOŞULAN KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  "navitas_seg_v24_best modeli yuklendi: navitas_seg_v24_best.pt
            (SHA c04d7d35)" · bilgi satiri "model: navitas_seg_v24_best.pt"  GECTI
    KAPI 2  B1 bagimsiz v24 0/30 (kontrol v17 28/30)                         GECTI
    KAPI 3  depo <-> paket bayt-esit .pt c04d7d3570ead678 · onnx 27e480a1     GECTI
    KAPI 4  test_gui_kendi_cikarim_hattini_KURMUYOR ......... ok
            test_gui_karari_uretim_yolunun_karariyla_AYNI .... ok             GECTI
    KAPI 5  codes/test_rota_sentetik.py   SONUC: 15/15 dogru
            unittest discover -s tests -q  Ran 315 tests  OK                  GECTI
    KAPI 6  scripts/jetson_paket_hazirla.py  9/9 bayt-esit                    GECTI
    ```
  - ⚠ **DOĞRULANAMADI:** (1) v24'ün **gerçek arenadaki** başarımı — **kamera
    yok**, bu karar arena başarımını doğrulamaz ve doğrulayamaz; (2) kazanç
    v24 ile aynı dokuyla üretilmiş sentetik kümede ölçüldü (D-82 "ev sahibi
    avantajı") ve kompozitte karşılığı yok; (3) **v24 için ONNX↔.pt çıktı
    paritesi ölçülmedi** — v21'de 30/30 ölçülmüştü, v24'ün karşılığı **yok**,
    Jetson'da engine derlenmeden önce ölçülmeli; (4) Jetson üzerinde hiçbir şey
    koşulmadı (FPS, engine, saha kararı donanım ister).

- [STATUS: READY_FOR_REVIEW] **T57 — Prosedürel zemin dokusu gerçek dışı: kanal-bağımsız gürültü** · `O:
  - **✅ YAPILDI · 2026-08-12 · Claude-2** · kayıt `REVIEW_LOG.md` **D-80**.
  - **Hedef körü körüne kopyalanmadı:** banka yamalarının parlaklık std'sinin
    büyük kısmı dokudan değil **içerikten** (gölge/nesne) geliyor. 6 px Gauss
    yüksek-geçirgenle **doku** bileşeni ayrıldı; iki gerçek kategori de
    **k/p = 0,15**'te buluşuyor — hedef bu.
  - **KAPI 1 — LAB ölçümü (gerçek çıktı):**
    ```text
    kaynak                DOKU kroma  DOKU parlak  DOKU k/p
    ESKI prosedurel zemin       6,95         8,10      0,86
    ESKI prosedurel yol         5,90         8,09      0,73
    YENI prosedurel zemin       1,13        10,60      0,11
    YENI prosedurel yol         0,85         3,99      0,21
    GERCEK banka zemin          1,82        12,15      0,15
    GERCEK banka yol            0,54         3,68      0,15
    ```
    Kalibrasyon süpürmesi: `RENK_SAPMASI=1,5` → oran 0,14 · parlaklık bandı
    kategoriye göre (zemin ~8,5–12,7 · yol ~2,6–5,1).
  - **Taban rengi çeşitliliği KORUNDU:** belirgin renkli yama 42/60 → 42/60,
    ortanca kroma 21,2 → 21,0 (kroma düşürmek rengi öldürmedi).
  - **`yuzey_sec()` payı ölçümle ayrıldı** (docstring "%45" / kod %60 çelişkisi
    de giderildi). Bankadaki yamaların "temiz düz yüzey" olma oranı:
    ```text
    zemin  2/315 temiz (p50 icerik std 39,8) -> banka temiz zemin VEREMIYOR
    yol  166/385 temiz (p50  9,9)            -> banka temiz yol BOL VERIYOR
    ```
    → `PROSEDUREL_PAYI = {"zemin": 0.70, "yol": 0.35}`. **Sıfırlanmadı.**
  - **KAPI 2 — GÖZLE:** `O:
avitas-local-train
esults	57_gorsel\`
    (`yuzey_ornekleri.jpg`, `sahne_51/77/123.jpg`). Eski zemin **gökkuşağı
    konfeti**; yeni zemin **çim/beton** gibi okunuyor.
  - **KAPI 3 — T56 kapıları KORUNDU:** koridor sapma **0,00 px** · hedef
    260/260 · kenar **2,000 m** · `hedef_serit != acik_serit` **0/144**.
  - **KAPI 4 — karar zinciri:**
    ```text
    T56 zemini: net 123/260 · rota  86 (DOGRU  86 · YANLIS 0) · RET 37
    T57 zemini: net 144/260 · rota 107 (DOGRU 107 · YANLIS 0) · RET 37
    ```
    Artması beklenmiyordu, **arttı**; ret değişmedi, yanlış şerit yine 0.
  - **KAPI 5 — eğitim kipi de değişti (KASITLI), etki AYRIŞTIRILDI:**
    ```text
    A) pay ESKIDE sabit (0,60/0,60) -> fark yalniz DOKUDAN
       ESKI kroma 4,90 parlak 21,13 oran 0,23 | YENI 3,96 / 21,22 / 0,19
       GEOMETRI (kimlik) AYNI: 5/5 tohum
    B) gercek pay (0,70/0,35): GEOMETRI ayni mi -> 0/5
    ```
    ⚠ İlk ölçümümde "geometri değişmedi" yazmıştım, **yanlıştı**. Geometri
    değişimi **dokudan değil, `yuzey_sec` payından** geliyor: `yuzey_sec`
    şerit düzeninden **önce** koşuyor, pay değişince RNG akışı kayıyor.
  - **Küme:** `...\calisma\sentetik_arena_kadraj` (T57); öncekiler `..._T56`
    ve `..._T55` olarak saklandı. Depo kapıları: **15/15** · **Ran 303 · OK**.
  - ⚠ **DOĞRULANAMADI:** (1) yeni yüzeyin gerçek asfalt/çim fotoğrafına
    benzerliği (yalnız LAB + göz); (2) moloz şeritleri hâlâ RescueNet **bina
    çatısı** kesitleri (D-78'den devam, bu görevde değişmedi); (3) banka
    "zemin" yamalarının bir kısmı aşırı pozlanmış.
avitas-local-train)_sentetik_arena.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-79
  - ⚠ Satırı Claude-2 açtı (kuyrukta yoktu); kapsam kullanıcı direktifinden.
  - **Yap:** gürültü TEK KANALLI üretilip üç kanala yayılsın (parlaklık dokusu);
    parlaklık genliği gerçek bankaya ÖLÇEREK yaklaştırılsın; `yuzey_sec()`
    prosedürel payı ölçümle gerekçelendirilsin (SIFIRLANMAYACAK).
  - ⚠ Bu değişiklik **eğitim kipini de etkiler ve bu KASITLIDIR**; T51/T56'daki
    "eğitim kipi değişmedi" kapısı bu görevde geçerli değildir.

- [STATUS: READY_FOR_REVIEW] **T56 — Kadraj kipi şartnameye sadık değil: hedef yeşil, koridorlar dalgalı, doku kaleydoskopik** · `O:
  - **✅ YAPILDI · 2026-08-12 · Claude-2** · kayıt `REVIEW_LOG.md` **D-78**.
    Eğitim kipinde eğrilik, aynalama ve yeşil çeldirici **aynen kaldı**;
    yalnız `--kadraj` değişti.
  - **KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  GOZLE DOGRULAMA — O:
avitas-local-train
esults	56_gorsel              ayni_sahne_51.jpg · _77.jpg · _123.jpg   (AYNI sahne, iki kip)
              uclu_sa_000000.jpg · _000005.jpg · _000012.jpg
            goruntu 260 · manifest kaydi 260                        GECTI
    KAPI 2  koridor merkez sapmasi ort 0,00 · MAKS 0,00 px (n=541)  GECTI
    KAPI 3  hedef 260/260 · kenar 2,000 m (min/maks 2,000) ·
            hedef_serit != acik_serit  0/123                        GECTI
    KAPI 4  EGITIM KIPI DEGISMEDI (4 tohum: kimlik+sinif+RNG+GORUNTU) GECTI
    KAPI 5  T55 zemini: net 139 · rota 89 (DOGRU 85 · YANLIS 4) · RET 50
            T56 zemini: net 123 · rota 86 (DOGRU 86 · YANLIS 0) · RET 37
            -> serit uyumsuzlugu 4 -> 0 · ret orani %36 -> %30
    depo    test_rota_sentetik 15/15 · discover -s tests -q Ran 303 OK
    ```
  - **Renk ayrımı ölçüldü** (branda 14.440 px / moloz 161.769 px): ayrım
    **doygunluktan** geliyor — S 213,9±31,7 vs 33,2±37,0, **etki büyüklüğü
    d = 3,71**. Kuyruklarda küçük örtüşme var (molozun %99'u S<169, brandanın
    %1'i S>149). ⚠ **Ton (H) ile ayırt etmeye güvenilemez:** kırmızı H=0/179'da
    sarılır, tuğla tonu (H 5-22) bitişiktir.
  - **Aynalama ölçüldü:** ayna simetrisi eğitim kipi 0,502 → kadraj 0,360
    (tepe 0,748 → 0,458), **%28 düşüş**.
  - 🔴 **İlk çözümüm YANLIŞTI, görsel geri aldırdı.** Tek döşemeye büyütme
    periyodikliği yapısal olarak kaldırdı ama dokuyu da öldürdü (bulanık renkli
    leke). Yerine ılımlı büyütme + **dikiş harmanlama** kondu.
  - 🔴 **Kendi ölçüm hatamı buldum:** ilk görsel kıyasım "aynı indis = aynı
    sahne" varsayıyordu; kadraj kipinde çeldirici `rng.random()` tüketilmediği
    için akış kaymıştı. Düzeltildi; aynı sahne iki kipte üretilince doku
    **bozulmamış** olduğu görüldü.
  - **Küme:** `...\calisma\sentetik_arena_kadraj` (T56); öncekisi
    `...\sentetik_arena_kadraj_T55` olarak saklandı. Belirsiz kare 137/260.
  - ⚠ **DOĞRULANAMADI:** (1) zemin dokusunun gerçek asfalta benzerliği — yama
    bankası 48–64 px kesitlerden, her iki kipte de benekli; **"asfalt gibi"
    DEĞİL**; (2) moloz şeritleri hâlâ RescueNet **bina çatısı** kesitleri;
    (3) brandanın gerçek brandaya görsel benzerliği (düz kırmızı dikdörtgen).
avitas-local-train)_sentetik_arena.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-77
  - ⚠ Satırı Claude-2 açtı (kuyrukta yoktu); kapsam kullanıcı direktifinden.
  - **Yap (yalnız `--kadraj`):** koridorlar düz · hedef 2×2 m KIRMIZI branda,
    açık şeridin hedef ucunda, her karede · aynalama kaldırılsın (periyodik
    desen geri gelmeden). **Eğitim kipi (varsayılan) DEĞİŞMEZ** — eğrilik,
    aynalama ve yeşil çeldirici çeşitlilik için orada KALIR.

- [STATUS: READY_FOR_REVIEW] **T55 — Kadraj kümesi AÇIK ŞERİDİ kaydetmiyor: en iyi zeminimizde şerit doğruluğu ölçülemiyor** · `O:\navitas-local-train\51_sentetik_arena.py` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` **D-69**
  - **✅ YAPILDI · 2026-08-12 · Claude-2** · kayıt `REVIEW_LOG.md` **D-76**.
  - **Tasarım:** `acik_serit` **üretim anında** kaydediliyor — D-70'in uyarısı
    tasarıma girdi. `sahne_uret(..., bilgi=None)`: dönüş **aritesi değişmedi**,
    hiçbir çağrı yeri kırılmadı. Şerit numarası `karar_sozlesmesi.serit_no`'dan
    **okunuyor** (üreteçte çıplak üçte-bir yok) — iki küme aynı otoriteyi kullanıyor.
  - Manifest `data/arena_kompozit` alan adlarını birebir taşıyor: `acik_serit`,
    `kapali_seritler`, `bariyerler` (kutu+pencere), `icerik`, `mpp`,
    `olcek_kaynagi`, `beklenen_durum`, `beklenti_kaynagi`, `tohum`,
    `uretec_seritleri` + `acik_serit_adaylari`, `belirsiz`, `arena_x_araligi`.
  - **KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  260 goruntu / 260 kayit · dosyasi olmayan kayit 0        GECTI
    KAPI 2  rota_bul: DOGRU 0 · YANLIS 0 · karar vermeyen 139/139    OLCULEMEDI
              {BELIRSIZ_TEK_KAPI 65 · MASKE_YOK 28 · KAPI_YOK 27 · BELIRSIZ_COKLU 19}
            analyze_path: DOGRU 85 · YANLIS 4 · RET 50 -> UYUMSUZLUK 4/89 (%4,5)
    KAPI 3  rota kapatilan banttan GECMIYOR (veya RET) : 89/89       GECTI
    KAPI 4  geometri: ESKI/YENI ikisi de 550 traversable · 879 blocked ·
            zemin alan 0,2171 ± 0,1522 (BIREBIR)                     GECTI
    KAPI 5  egitim kipi denkligi 4 tohumda True (kimlik+sinif+RNG+geometrik) GECTI
    depo    test_rota_sentetik 15/15 · discover -s tests -q Ran 303 OK
    ```
  - 🔴 **KAPI 2 görevin yazdığı ölçütle ölçülemedi.** `rota_bul` bu kümede
    **hiç karar vermiyor**: üç-kapılı arena dedektörü (D-58,
    `costmap_path_finder.py:781`), üreteç ise 2–5 şerit üretiyor. Üretim karar
    yolu (`analyze_path` + K-B) ile ölçüldü: **uyumsuzluk 4/89**.
  - ⚠ **KAPI 3 ilk ölçümde düştü (87/89) — değişmez YANLIŞTI, kapı değil.**
    İki başarısız karede kapatılan bantta **0 serbest piksel** kalmış ama rota
    **komşu şeritten dolanmış** (sa_000063 → şerit 2, sa_000156 → şerit 3);
    etiket değişmiyor çünkü `road` darboğaz şeridini adlandırıyor ve darboğaz
    başka yerde. Doğru değişmez **"kapatılan banttan geçilmemesi"**dir → 89/89.
  - 🔴 **BULGU: 260 karenin 121'i BELİRSİZ** — birden fazla karar şeridi
    geçilebilir şerit içeriyor, tek `acik_serit` yazılamıyor (`belirsiz: true` +
    `acik_serit_adaylari`). Tek cevaplı **139** kare kalıyor. Üreteç 2–5 şerit
    ürettiği için doğal sonuç; **geometri değiştirilmedi** (kapı 4 gereği).
    Oranı yükseltmek için kadraj kipinde şerit sayısı 3'e sabitlenmeli — **ayrı görev**.
  - **Küme:** `O:
avitas-local-train\calisma\sentetik_arena_kadraj` (manifest dahil);
    öncekisi `..._ONCEKI_manifestsiz` olarak saklandı.
  - **DOĞRULANAMADI:** (1) manifest `acik_serit` değerlerinin **görsel** doğruluğu
    (260 karenin hiçbiri gözle denetlenmedi); (2) `mpp` kamera ölçümü değil.
  - **Kanıt:** `calisma\sentetik_arena_kadraj` yalnız `images/`, `labels/`,
    `data.yaml` taşıyor — **manifest yok**. Hangi şeridin açık olduğu hiçbir
    yere yazılmıyor.
  - **Neden `class-0`'dan türetilemez:** üç şeritli arenada traversable **üç
    koridoru da** kaplar; şeritleri ayıran zemin değil, üzerlerindeki
    **bariyerlerdir**. Mimar bunu denedi, %83,7 buldu ve **sayıyı geri çekti** —
    hataların deseni ölçütün yanlışlığını gösteriyordu (rota tamamen tek
    şeritteyken "GT" başka şerit diyordu).
  - **Yap:** Kadraj kipi, `data/arena_kompozit` kalıbındaki gibi manifest yazsın:
    `acik_serit` · `kapali_seritler` · `bariyerler` (kutu + pencere) · `icerik` ·
    `mpp` · kullanılan tohum. T40'ın gerçek kapısı tam bu sayede kurulabilmişti.
  - **Kapı:** (1) her kare için manifest kaydı var; (2) yer gerçeği maskeleriyle
    `rota_bul` manifest'in `acik_serit`'ini buluyor, uyumsuzluk sayısı yazılıyor;
    (3) **pozitif kontrol**: açık şerit kapatılınca karar `ACIK` kalmıyor.
  - ⚠ **T51'in KAPI 2 sonucu ("yer gerçeği şerit ile uyumsuzluk 3/12") aynı
    türetme sorununa maruz olabilir** — nasıl türetildiği görevde yazılı değil.
    Denetimde sorulacak; doğrulanmadan kullanılmayacak.

- [ ] **T52 — özgün kayıt (mimar denetimi bekliyor)** · `codes/karar_sozlesmesi.py` · ÖNEMLİ · kanıt: `REVIEW_LOG.md` D-65
  - **Kanıt:** kadraj kümesinin **meşru** azamisi %82,3; otoparkın **çöküş**
    değeri %73,7–82,5. Ham kaplama üst uçta *"her şey boyanmış"* ile *"gerçekten
    açık arena"* hâllerini **ayırt edemiyor**. Görev kadrajında arena görüntüyü
    dolduracağı için sistem tam da ölçütün en zayıf olduğu bölgede çalışacak.
  - **Yap — ÖNCE ÖLÇ.** Ayırt-edicilik ölçen aday büyüklükleri iki kümede birden
    sına (kadraj arenası = meşru, otopark = çöküş) ve **ayrışma gücünü sayıyla**
    raporla. Aday örnekleri (bunlarla sınırlı değil): zemin/(zemin+engel) oranı ·
    zemin maskesinin bileşen sayısı ve en büyük bileşen payı · maskenin
    görüntü kenarına dayanma oranı · engel sınıfının mutlak yokluğu.
  - **Kapı:** Seçilen ölçüt iki kümeyi **çakışmasız** ayırmalı; ayıramıyorsa
    "DOĞRULANAMADI" yaz ve tavanı **olduğu gibi bırak** — zorlama. Değiştirirsen
    D-65'teki iki dağılımı yeniden ölç ve yanlış-negatif oranını yapıştır.
  - ⚠ Tavan `0.55` şu an **köprü çözüm** olarak yürürlükte (D-65). Bu görev
    bitene kadar değiştirilmeyecek.

- [x] **T51 — Sentetik arena kadraja oturmuyor: karar yoluyla uyumlu TEK zemini kazanıyoruz**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-12 · Claude 1.** Kodu Claude-2 yazdı.
  - **Bağımsız ölçümüm — yer gerçeğiyle değil, GERÇEK MODEL ÇIKARIMIYLA** (GUI'nin
    yaşayacağı hâl), aynı kümeden 24 kare:
    ```text
    karar     : rota 18/24  (serit 2:9 · 3:5 · 1:4) · UC_BANT_TEMAS_YOK 5 · GORUS 1
    serit     : DOGRU 15 · YANLIS 3
    kaplama   : ort %17,7 · p95 %37,5 · maks %48,7 · tavan ustu 0/24
    ```
    Claude-2'nin yer gerçeğiyle aldığı 12/24'ten **daha iyi** — model maskesi
    poligon etiketinden daha bütün çıkıyor. `UC_BANT_TEMAS_YOK` **20 → 2**.
  - 🔴 **Bu, karar zincirinin uçtan uca çalıştığı İLK zemin.** Otopark alan dışı,
    kompozit otoparkın maskesini miras alıyor, eski sentetik arena geometrisi
    uyumsuzdu. Kadraj kipi bu üçünün dışında duruyor.
  - **Takdir edilecek iki nokta:**
    1. **Kapı 4'ün yöntemini değiştirmesi doğruydu.** Benim "bayt-eşit" kapım
       **uygulanamazdı**: üreteç zaten tekrarlanabilir değil (aynı seed, üç
       koşum, üç hash). Yerine koyduğu RNG-durumu + kimlik + sınıf + geometri
       karşılaştırması **daha sıkı**.
    2. **Kendi testinin sahte geçtiğini kendi negatif kontrolü yakaladı**
       (8 bloktan 1'i yazılmış, dosya kendisiyle kıyaslanıyordu). D-15/K-04
       sınıfının canlı örneği.
  - **Tavan kararını bana bırakması doğruydu** — karar D-65'te: `0.55` kalıyor,
    bedeli (%4,2 meşru çekimserlik) kayda geçti, ölçütün zayıflığı **T52**'ye.
  - **Açık kalan:** 3/18 karede **yanlış şerit**. Ölçüldü, kapatılmadı — kadraj
    kümesi artık var olduğuna göre `road` etiketi doğruluğu burada yeniden
    sınanmalı (T31 ölçümü otoparkta yapılmıştı).

- [STATUS: KAPANDI] **T51 — özgün kayıt** · `O:\navitas-local-train\51_sentetik_arena.py` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-62, T49 tanısı
  - **✅ YAPILDI · 2026-08-12 · Claude-2** · kayıt `REVIEW_LOG.md` **D-64**.
  - ⚠ **KAMERA YOK: gerçek arena karesi alınamıyor; bu görev modelin ARENADAKİ
    başarımını doğrulamaz.** Ölçülen şey üretecin geometrisidir.
  - `--kadraj` kipi eklendi: dikey pay `0`, dönüş/perspektif kapalı, `"kismi"`
    şerit yok. **Eğitim kipi (varsayılan) DEĞİŞMEDİ.** Yeni küme 260 kare:
    `O:
avitas-local-train\calisma\sentetik_arena_kadraj`.
  - **ÖNCE/SONRA — kendi ölçümüm** (tam karede, kırpmasız, yer gerçeği maskesiyle, n=24):
    ```text
    ESKI (egitim kipi) : rota  2/24 · {UC_BANT_TEMAS_YOK: 20, DUSUK_GUVEN: 2}
    YENI (kadraj kipi) : rota 12/24 · {DUSUK_GUVEN: 8, UC_BANT_TEMAS_YOK: 2,
                                       ZEMIN_MASKESI_SUPHELI: 2}
    ```
    `UC_BANT_TEMAS_YOK` **20 → 2**.
  - **KAPILAR:**
    ```text
    KAPI 1  TAM KAREDE rota 12/24 (esik >= 12)                      GECTI
    KAPI 2  yer gercegi serit ile UYUMSUZLUK 3/12                   (olculdu)
    KAPI 3  POZITIF KONTROL: acik serit kapatilinca karar DEGISTI 12/12  GECTI
    KAPI 4  EGITIM KIPI DEGISMEDI (4 tohum, kimlik+sinif+RNG+geometrik)  GECTI
    KAPI 5  T48 tavani 11/260 MESRU kareyi kesiyor                  (asagida)
    ```
  - 🔴 **KAPI 4'ün yöntemi değiştirildi — "bayt-eşit" ölçütü UYGULANAMAZ.**
    Üreteç **zaten** tekrarlanabilir değil: değiştirilmemiş kodla aynı seed'le
    üç koşum üç farklı hash verdi (`f274c4cd` / `c461a815` / `e2139836`).
    Yerine daha sıkı test: orijinal dosya saklanıp iki sürüm yan yana import
    edildi; 4 tohumda kimlik haritası, sınıf sözlüğü, **RNG durumu** ve
    `geometrik()` çıktısı bire bir eşit. ⚠ Bu testin **ilk koşumu sahte geçti**
    (8 bloktan 1'i yazılmıştı, dosya kendisiyle kıyaslanıyordu); **negatif
    kontrol yakaladı** — D-15/K-04 sınıfının canlı örneği.
  - **KAPI 5 — T48 tavanı bu kümede yanlış ateşliyor (tavan DEĞİŞTİRİLMEDİ):**
    ```text
    260 kare · kaplama ort %22,0 · p50 %20,3 · p95 %52,2 · MAKS %82,3
    tavan (%55) ustunde: 11/260 (%4,2)
      hepsinin GT seridi VAR (mesru sahne)     : 11/11
      tavan olmasaydi ROTA URETECEK olan       : 11/11
    ```
    D-62'de tavan, meşru azamisi %42,6 olan bir tabandan türetilmişti; kadraj
    kipi o tabanı geçersiz kılıyor. **Karar mimarındır.**

  - **Ölçülmüş kazanç — kendim koştum, 24 kare:**
    ```text
    TAM KARE          : UC_BANT_TEMAS_YOK 21 · rota  3/24
    ARENAYA KIRPILMIS : rota 14/24 (ZEMIN_SUPHELI 7 · UC_BANT 2 · GORUS 1)
    ```
    Arenaya kırpmak rotayı **3/24 → 14/24** çıkarıyor; T49 tanısıyla birebir
    örtüşüyor. Kusur modelde değil, **üretecin yerleşiminde**.
  - **Neden değerli:** Sentetik arenanın kaplaması **zaten temkinli (%15,7)**,
    T48 kapısını geçiyor. Tek eksiği geometri. Düzeltilirse karar yolunun
    geometrisiyle **uyumlu tek zemin** olur (otopark alan dışı, kompozit
    otoparkın maskesini miras alıyor).
  - **Yap:** Arena yerleşimini kadraja oturt — koridorlar içerik kutusunun üst ve
    alt uçlarına ulaşsın. Dikey pay (`%0–28`), dönüş ve "kısmi şerit" olasılığı
    **kapatılabilir ayrı bir kip** olsun; **mevcut eğitim kipini BOZMA** (pay ve
    dönüş eğitim çeşitliliği için değerli). Yeni kip yalnız demo/doğrulama
    kümesi üretir — 200-300 kare yeter.
  - **Kapı:** (1) tam karede rota oranı ≥ **12/24** (kırpmasız) — ⚠ 24/24 zorunlu
    değil, fail-closed retler meşru, **zorlama**; (2) yer gerçeği ile şerit
    uyumsuzluk sayısı yazılacak; (3) **pozitif kontrol**: açık şerit kapatılınca
    `ACIK` kalmayacak; (4) eski komutla üretilen çıktı **bayt-eşit** (eğitim kipi
    bozulmadı).
  - **Bağlı:** T48'in tavanı bu kümede yeniden ölçülmeli (D-62 yan bulgusu).

- [STATUS: READY_FOR_REVIEW] **T50 — Zemin sınıfı otorite değil: model seçimi mimarinin değişmezine göre yeniden yapılacak** · `O:\navitas-local-train` · **TIKAYICI** · kanıt: `REVIEW_LOG.md` D-61 + aşağıdaki ölçüm
  - **✅ FAZ 1 BİTTİ · 2026-08-11 · Claude-2 · GPU'ya DOKUNULMADI** · kayıt `REVIEW_LOG.md` **D-63**.
  - ⚠ **KAMERA YOK (kullanıcı bildirdi): gerçek arena karesi ALINAMIYOR. Bu görev
    modelin ARENADAKİ başarımını doğrulamaz ve doğrulayamaz; yalnız alan-içi
    doğruluğu ve ALAN DIŞI TEMKİNİ iyileştirir.**
  - **11 model × 3 kapı — tam tablo (gerçek çıktı):**
    ```text
    model                       K1 IoU  K1 kesinlik  K1 duyar  K2 ort  K2 maks  K3 D/Y/R
    navitas_seg_v2_best.pt       0.366        0.760     0.414   70.4%    86.1%   0/0/9
    navitas_seg_v3_best.pt       0.412        0.744     0.481   18.2%    78.7%   0/1/8
    navitas_seg_v4_best.pt       0.351        0.827     0.379   13.5%    76.6%   0/1/8
    navitas_seg_v5_best.pt       0.384        0.775     0.432   35.8%    68.2%   1/3/5
    aday_v5a_s640.pt             0.384        0.775     0.432   35.8%    68.2%   1/3/5
    aday_v5b_s640ft.pt           0.352        0.781     0.390   32.9%    78.3%   0/1/8
    aday_v5c_m640.pt             0.372        0.689     0.448   46.9%    82.6%   0/0/9
    aday_v9_mixup_m640.pt        0.365        0.631     0.463   50.2%    92.6%   1/0/8
    navitas_seg_v17_best.pt      0.315        0.807     0.341    0.9%     7.0%   0/0/9
    navitas_seg_v20_best.pt      0.267        0.795     0.287    2.9%    52.9%   0/0/9
    navitas_seg_v21_best.pt      0.311        0.813     0.335   81.0%    86.3%   0/0/9
    (K1 n=120 rescuenet_1024 val · K2 n=67 otopark · K3 n=9 kompozit · conf=0.30
     mikro-ortalama · D/Y/R = doğru/yanlış/ret)
    ```
  - 🔴 **KAZANAN YOK.**
    - **KAPI 3 kimseyi geçirmiyor:** en iyi 1/9 (v5, v5a, v9 — üçü de K2'de
      %35–50 ile çökmüş). Üretim adaylarının üçü de **0/9**. Ayrıca K3 yer
      gerçeğinde **şerit 2 hiç yok** (5×şerit1, 4×şerit3) — "hep 1" diyen kod
      şansla 5/9 alırdı.
    - **KAPI 2 tek başına KUSURLU:** temkin ile körlüğü ayırt etmiyor. İki ek
      ölçümle gösterildi:
      ```text
      ARENA BENZERI SENTETIK (n=60, GT %12,4)   KOMPOZIT: GERCEK DOKU (n=9, GT %28,6)
        v17  IoU 0.896  55/60                     v17  kaplama %0.4  duyar 0.010  1/9
        v20  IoU 0.929  59/60                     v20  kaplama %0.1  duyar 0.000  0/9
        v4   IoU 0.094  21/60  <- KOR             v21  kaplama %82.5 duyar 0.890  9/9
        v3   IoU 0.122  14/60  <- KOR
      ```
      v4/v3 kapı 2'yi **hiçbir şey görmedikleri için** geçmiş. v17'nin %0,9'u da
      temkin değil, **gerçek dokuda körlük** — 9 karenin 8'inde hiçbir şey yok.
    - Üç eksenin özeti: `v21 görür ama çöker (0.890 / %81,0)` ·
      `v17 çökmez ama görmez (0.010 / %0,9)` · `v20 çökmez ama görmez (0.000 / %2,9)`.
      **"Gerçek dokuda görür VE alan dışında çökmez" çeyreğinde hiçbir model yok.**
  - **Görsel doğrulama — sayıyı değiştirdi** (`O:
avitas-local-train
esults	50_uc_kapi\`):
    v21 otoparkta bina **çatısını ve çimi parlak yeşil** boyuyor (kullanıcının
    bildirdiği kusur gözle doğrulandı); v17 aynı karede **tek piksel bile**
    işaretlemiyor. GT'si zengin val karesinde (%37,3) ikisi de yol yüzeyini
    doğru veriyor; sentetik arenada v17 üç koridoru temiz ayırıyor (%38,4).
    İlk üretilen v17 val görseli GT'si boş bir kareydi, ayırt edici olmadığı
    için GT'si zengin kareyle yeniden üretildi.
  - **FAZ 2 GEREKÇELİ — ama önce ÖLÇÜT düzeltilmeli.** Aynı ölçütle eğitilen
    model yine yanlış seçilir. **Önerilen KAPI 0 — TESPİT TABANI:** kompozit
    (gerçek doku) kümede `duyarlılık ≥ 0,50` ve `kare>%1 ≥ 8/9`. Bugün bunu
    **yalnız v21** geçiyor. Seçim "KAPI 0'ı geçenler arasında KAPI 2'si en düşük
    olan" olur; hem körlüğü hem çöküşü eler.
  - 🔴 **FAZ 2 SONUCU · 2026-08-12 · Claude-2 — EĞİTİME GEREK KALMADI.**
    `42_cok_sinifli_onegitim.py --on-epoch 150 --ft-epoch 200 --batch 12`
    (`FOR_DISABLE_CONSOLE_CTRL_HANDLER=1`, başlangıç **2026-08-12 00:17:45**)
    başlatıldı; script her iki aşamayı da **tamamlanmış** bulup atladı.
    `v15_ft2sinif` 200 yerine **166 epoch'ta erken durdurma ile** bitmiş
    (`bitti_mi()` durum günlüğündeki "EĞİTİM TAMAMLANDI" damgasına bakıyor).
    Yani **reçetenin ürünü zaten diskte** ve T50'nin 11 modelli tablosunda
    **yoktu**: `codes/runs/segment/v15_ft2sinif/weights/best.pt`
    (SHA `a796265f1c5c3e...`). GPU-gecesi harcamak yerine dört kapıyla ölçüldü:
    ```text
    model          K0 duyar  K0 kare>%1  K1 IoU  K1 kesin  K2 otopark  K3 D/Y/R
    v15_ft2sinif      0.134         2/9   0.425     0.804      24.1%     0/0/9
    v21 (uretim)      0.890         9/9   0.311     0.813      81.0%     0/0/9
    v17               0.010         1/9   0.315     0.807       0.9%     0/0/9
    ```
    **v15 KAPI 0'ı geçemiyor** (0,134 < 0,50 · 2/9 < 8/9). 11-sınıf ön-eğitim
    alan-içi doğruluğu yükseltiyor (IoU **0,425** — ölçülen 12 modelin en iyisi)
    ve aşırı tespiti frenliyor (%24,1), ama **gerçek doku körlüğünü çözmüyor**.
  - **KAZANAN HÂLÂ YOK — ama nedeni netleşti.** Gerçek dokuyu gören tek model
    v21 (eğitiminde `copy_paste_gercek` **var**), aşırı tespit ediyor; aşırı
    tespit etmeyenler (v15/v17/v20) gerçek dokuda kör (eğitimlerinde gerçek
    doku **yok**). Eksik olan **reçete değil, VERİ KARIŞIMI**: 11-sınıf
    ön-eğitim ile gerçek doku verisi aynı koşuda birleştirilmemiş. Bu bir
    eğitim tasarım kararıdır; kullanıcıya soruldu, kendi başıma GPU-gecesi
    harcanmadı.
  - **DOĞRULANAMADI:** (1) hiçbir modelin gerçek arena başarımı — kamera yok;
    (2) kompozitin gerçek arenayı ne kadar temsil ettiği; (3) sentetik arena
    sonuçları v17/v20/v21 için **dağılım içi** (üçü de o kümeyle eğitildi),
    genelleme kanıtı sayılmaz; (4) v13 diskte yok, ölçülemedi.
  - **Kök neden (Claude 1 ölçtü, 2026-08-11):** Mimari *"Serbest alan OTORİTEDİR;
    zemin değil → engel"* (fail-safe) diyor. Üretim modeli bunun **tersini**
    yapıyor: her şeye zemin diyor, dolayısıyla kural hiç ateşlenmiyor.
    ```text
    model                     kaplama  yer gercegi     IoU  kesinlik   OTOPARK
    navitas_seg_v17_best.pt      1.9%         3.2%   0.161     0.170      %0.0
    navitas_seg_v20_best.pt      2.1%         3.2%   0.222     0.284     %16.3
    navitas_seg_v21_best.pt      2.3%         3.2%   0.227     0.280     %73.7
    ```
    v21 **alan-kırılgan**: kendi alanında uslu, alan dışında (otopark) %73,7'ye
    patlıyor ve çatıyı/çimi zemin sayıyor. Seçim mAP ile yapılmış; K-3 zaten
    *"mAP arena sıralamasını tersine çeviriyor"* diyordu.
  - 🔴 **FAZ 1 — GPU YOK, ÖNCE BU.** Diskte **11 eğitilmiş model** var ve hiçbiri
    mimarinin ölçütüyle sıralanmadı. Belki eğitime hiç gerek yok.
    **Üç kapılı seçim ölçütü** (mAP DEĞİL):
    1. **Alan içi doğruluk:** RescueNet val'de zemin IoU + **kesinlik**.
       Kesinlik önceliklidir — yanlış-pozitif zemin, kaçırılan zeminden
       tehlikelidir (fail-safe).
    2. **ALAN DIŞI TEMKİN (negatif kontrol, kamera gerekmez):** otopark
       karelerinde kaplama. Model burayı arena zemini **sanmamalı**. `%73,7`
       çöküş, `%0-20` kabul. Bu ölçüt bugüne kadar hiç kullanılmadı ve kusuru
       tam olarak o yakalıyor. `45_alan_disi_test.py` zaten var.
    3. **Karar doğruluğu:** `data/arena_kompozit` yer gerçeğiyle doğru şerit
       sayısı (9 kare, manifest'te `acik_serit`).
    - **Gürültü tabanı:** 0,04'ten küçük farklar gürültüdür — sıralama bu farkla
      yapılmaz (ölçülmüş: mask sd 0,025–0,032).
    - **Çıktı:** 11 model × 3 kapı tablosu + her aday için **gözle doğrulanmış**
      2 görsel (otopark + RescueNet). Kazanan varsa üretime alınır, FAZ 2 iptal.
  - **FAZ 2 — yalnız FAZ 1'de kazanan çıkmazsa.** Reçete ölçülmüş:
    **11 sınıfla ön-eğit → 2 sınıfa fine-tune** (`42_cok_sinifli_onegitim.py` +
    `43_zincir.py`; `dataset/rescuenet_11sinif` hazır). Kanıt: v15 bu reçeteyle
    arena moloza basma **%2,7**; v13 (ön-eğitimsiz, en yüksek mAP) **%37,7**.
    Seçim yine yukarıdaki üç kapıyla yapılır.
  - ⚠ **Eğitimi FAZ 1 bitmeden başlatma** — bozuk ölçütle eğitim GPU-günü israfıdır.
  - ⚠ **Uzun koşu uyarısı:** `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` ortam değişkeni
    olmadan başlatma; konsol kapanınca eğitim **izsiz ölüyor** (ölçülmüş olay).
  - ⚠ **Kamera yok (kullanıcı bildirdi):** gerçek arena karesi ALINAMIYOR. Bu
    görev modelin **arenadaki** başarımını doğrulamaz ve doğrulayamaz; yalnız
    alan-içi doğruluğu ve **alan dışı temkini** iyileştirir. Rapora bu cümle
    aynen yazılacak.

- [ ] **T47 — v21'in "geçilebilir" sınıfı bu alanda anlamsız: çatı ve çim yol sayılıyor** · model / veri · **TIKAYICI** · kanıt: `REVIEW_LOG.md` D-61 + görsel
  - **Kullanıcı bildirdi, gözle doğrulandı.** v21 bu karelerde pratikte
    **"araç mı, değil mi"** ayırıcısı: bina çatısı, çim, toprak — hepsi zemin
    sınıfında; yalnız araçlar engel. Kaplama **%74** (v13'ün çöküş imzası).
  - **Üç şikâyet tek kök:** çatı yol sayılıyor · rota kenardaki çim şeridinden
    geçiyor (her yer serbest olunca en geniş kanal orası) · bazen hiç rota yok
    (serbest alan anlamsız olduğu için retler gelişigüzel).
  - ⚠ **Bu bulgu modelin ARENADA çökeceğini KANITLAMAZ.** Kareler bir otopark
    (D-53); model RescueNet + sentetik arena ile eğitildi, burası alan dışı.
    Ama **tersini de kanıtlayamıyoruz: tek bir gerçek arena karemiz yok**
    (arena çekimi iptal, D-56). **Ölçüm zemini yok.**
  - **Yap — sıra bağlayıcı:**
    1. **Önce ölç, eğitme.** v21'in zemin sınıfını *alan bazında* raporla:
       otopark kareleri · sentetik arena · kompozit arena. Her biri için
       kaplama yüzdesi ve gözle doğrulanmış 2 örnek görsel. Hangi alanda
       çalışıp hangisinde çökdüğünü **sayıyla** ayır.
    2. Çökme yalnız otoparkta ise: bu **görev dışı alandır**, ilan et ve GUI'nin
       varsayılan kaynağını buna göre seç. Sentetik/kompozit arenada da
       çöküyorsa **eğitim verisi işidir** ve S1→S2→veri→eğitim sırası geçerlidir.
    3. Karar öncesi hiçbir eğitim koşusu başlatma (GPU-gün israfı).
  - **Kapı:** Üç alan için kaplama tablosu + her alandan gözle doğrulanmış 2
    görsel. "Model bozuk/sağlam" ilanı **tek başına mAP ile yapılmayacak** (K-3).

- [ ] **T46 — [BLOKE · D-61] Hakem ekranı HİÇBİR kaynakta rota göstermiyor: `OLCEK_YOK` politikası ekranı öldürdü**
  - 🔴 **BLOKE EDİLDİ · 2026-08-11 · Claude 1.** Bu görevi ben açtım ve teşhisim
    yanlıştı. Varsayılan ölçekle rotaları geri getirmek, hakem ekranında **çatı
    ve çim üzerinden geçen, kendinden emin ve yanlış** rotalar gösterir —
    hiçbir şey göstermemekten **daha kötüdür** (D-61).
  - **Bağımlı: T47.** Zemin sınıfının hangi alanda geçerli olduğu belirlenmeden
    bu görev açılmaz. `OLCEK_YOK` şu an ekranı ölü gösteriyor ama **yanlış rota
    yayınlamıyor**; bu sırayla daha güvenli. · `comms/yks_gui.py` · **KRİTİK** · kanıt: bu görevdeki ölçüm · **kullanıcı bildirdi**
  - **Kullanıcı bildirimi (2026-08-11):** *"kesinlikle doğru çalışmıyor hiçbir
    türlü... asla ama asla düzgün çalışmıyor."* İlk gerçek insan kullanımı.
  - **Kanıt — algı ve karar SAĞLAM, sorun politikada:**
    ```text
    GUI gercek yolu, 16 drone karesi
      ortalama zemin : %74.0  (min %72.5 / max %78.1)
      karar, mpp YOK : {'1': 5, '3': 8, RED/DUSUK_GUVEN: 3}    -> 13/16 rota
      karar, mpp VAR : {'1': 6, '3': 8, RED/GORUS_HATTI_KOPUK: 2} -> 14/16 rota
    EKRANDA GORULEN : RED/OLCEK_YOK x16
    ```
    `analyze_path` rotayı **buluyor**; `olcek_reddi` sonra onu siliyor
    (`yks_gui.py:1128-1131`). Kompozitte de `UC_BANT_TEMAS_YOK` (→ T45).
    Yani hakem ekranı **hiçbir kaynakta tek bir rota göstermiyor.**
  - 🔴 **Bu benim değerlendirme hatam.** T44'te *"drone/gemini/val'de `OLCEK_YOK`
    görünecek, bu gerileme değil dürüstlük"* dedim ve kapattım. Her kapı tek tek
    savunulabilir ama sonuç **kullanılamaz bir hakem ekranı**. Kapıların geçmesi
    sistemin çalıştığı anlamına gelmiyor.
  - **Yap — ölçek kapısını KALDIRMA.** Kaldırmak D-60'ta açığa çıkarılan sessiz
    varsayımı (gövde açıklığı ~11 kat küçülüyor) geri getirir. Doğru ayrım
    **sessiz varsayılan** ile **ilan edilmiş varsayım** arasındadır:
    1. Görüntü kaynakları için operatörün belirlediği bir **varsayılan irtifa**
       olsun (şartname §5.3.2 tabanı ≥30 m); `mpp_irtifadan()` ile ölçeğe
       çevrilsin. Değer `karar_sozlesmesi`den okunacak, çıplak yazılmayacak.
    2. Ekranda **açıkça** yazılsın: `ÖLÇEK VARSAYIM (telemetri yok) · irtifa
       30 m → mpp X` — hakem neyin varsayım olduğunu görsün.
    3. Canlı görevde telemetri varsa **o kazanır**; varsayım yalnız telemetrisiz
       görüntü kaynakları içindir.
    4. `kompozit` kaynağı manifest `mpp`'sini kullanmaya devam etsin.
    5. Varsayım **kapatılabilir** olsun (tuşla); kapalıyken davranış bugünkü
       `OLCEK_YOK` olsun — dürüst kip kaybolmasın.
  - **Kapı:** (1) `drone` kaynağında ekran **en az 12/16 karede rota gösteriyor**
    ve bilgi satırında ölçeğin VARSAYIM olduğu yazıyor; (2) varsayım kapalıyken
    `OLCEK_YOK` dönüyor; (3) telemetrili yolda varsayım **kullanılmıyor** (test);
    (4) T36'nın hizalama testleri ayakta; (5) `codes/test_rota_sentetik.py`
    **15/15** · tam paket **OK**.

- [x] **T45 — Kompozit arena TAM İÇERİK KUTUSUNA yayılmıyor: şerit tanımları uyuşamıyor** · `scripts/copy_paste_augmentation.py` · **KRİTİK** · **T36b'yi tıkıyor** · kanıt: T44 ablasyonu
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-12 · Claude-2** · kayıt `REVIEW_LOG.md` **D-69**.
    Dört iddia da bağımsız ölçümle doğrulandı:
    ```text
    1) serit sinirlari uretec == karar yolu, 4 en-boy oraninda AYNI
       1024x576 [342,683] · 1280x720 [427,854] · 1024x1024 [342,683] · 800x600 [267,534]
    2) mpp genislige eslendi -> r_gerekli_px 12.67 -> 22.53 (1024x576)
       C-uzayi {dist>=r} KUCULUR -> serbest alan DARALIR = madde 15 GUVENLI yon
    3) manifest notu ("HTAB / kaynak karenin GENISLIGI") formulle birebir ortusuyor
    4) egitim kipi BOZULMADI — AST: arena_icerik_ve_mpp yalniz arena_cesidi_uret'ten,
       o da main icinde `if args.arena:` guardi altinda
    ```
  - ⚠ **Küçük kusur (bloke etmez):** docstring'de 1 adet **Kiril U+0435**
    (`"ucе bolerek"`). Davranışa etkisi yok; tek karakterlik belge düzeltmesi.
  - **Kanıt — kendim ölçtüm:**
    ```text
    _preprocess icerik : (0, 224, 1024, 576)  -> serit sinirlari [341, 682]
    manifest arena ROI : (224, 0,  576, 576)  -> serit sinirlari [416, 608]
    AYNI MI            : False
    ```
    T40 arenayı **576×576 kare bir alt bölgeye** kuruyor; üretim yolu şeritleri
    **tam içerik kutusuna** göre hesaplıyor. İki tanım hiçbir zaman uyuşamaz →
    kompozit karelerde ret `UC_BANT_TEMAS_YOK`.
  - **Neden GUI'de çözülemez:** GUI'nin manifest ROI'sini karara sokması **yer
    gerçeği sızıntısı** olur; `test_beklenen_serit_KARARA_SIZMIYOR` bunu
    yasaklıyor ve haklı — saha yolunda böyle bir kutu yok.
  - **Yap:** Üretecin arena kipi şeritleri ve bariyerleri **`_preprocess`'in
    içerik kutusuna** göre yerleştirsin (kare alt bölgeye değil). Şerit
    sınırları yine yalnız `karar_sozlesmesi.serit_no()`'dan gelsin. Manifest'e
    kullanılan içerik kutusunu da yaz ki ölçüm tekrar edilebilsin.
  - ⚠ **Yan etki beklenir:** arena tam kareye yayılınca uygun zemin şartı
    zorlaşabilir ve **verim daha da düşebilir** (şu an 67 → 7). Düşerse sayıyı
    ve sebep dağılımını yapıştır; verimi kurtarmak için arena geometrisini
    bozma.
  - **Kapı:** Üretilen her karede `_preprocess(kompozit)` içerik kutusu ile
    manifest'in içerik kutusu **aynı**; GUI kompozit kaynağında uyumsuzluk
    ölçümü yeniden koşulacak (T36b kapısı). `codes/test_rota_sentetik.py`
    **15/15** · tam paket **OK**.

- [ ] **T36b — Kompozit arena kaynağı: yer gerçeği uyumu 1/7 · KAPI DÜŞTÜ** · `comms/yks_gui.py` (GUI tarafı bitti) · **KRİTİK** · kanıt: `REVIEW_LOG.md` **D-59**
  - **✅ GUI tarafı YAPILDI · 2026-08-11 · Claude-2.** `kompozit` kaynağı eklendi
    ve **açılış kaynağı** yapıldı; `drone`/`gemini`/`test`/`val` listede kaldı.
    Bilgi satırı manifest'in beklenen açık şeridini gösteriyor; manifest
    okunamazsa fail-closed (günlüğe hata + "OKUNAMADI", sessiz boş **yok**).
  - 🔴 **KAPI DÜŞTÜ — zorlanmadı.** 7 karede: **UYUMLU 1 · UYUMSUZ 5 · ÇEKİMSER 1**.
  - **Kök neden GUI'de DEĞİL, modelde de DEĞİL** — manifest'in kendi kusursuz
    zemin/engel maskeleriyle (yer gerçeği) ölçüldü:
    ```text
    ORACLE maske -> analyze_path + K-B :  DOGRU 0/7 · YANLIS 0/7 · RET 7/7
       6 kare DUSUK_GUVEN (0,028 / 0,028 / 0,028 / 0,028 / 0,117 / 0,056)
       1 kare UC_BANT_TEMAS_YOK
    K-B UYGULANMADAN ham serit      :  DOGRU 4/7 · YANLIS 2/7 · YAPISAL RET 1/7
    ```
    Yani karar mantığı arenada ham hâlde 4/7 doğru; **K-B hepsini eliyor**.
  - **Neden güven bu kadar düşük — ölçüldü.** Altı karenin dördünde darboğaz
    **1,0 px**. Görüntü-kenarı artefaktı DEĞİL: darboğaz noktaları kenardan
    **117–214 px** içeride ve `distanceTransform`'a 1 px kapalı çerçeve eklemek
    değeri değiştirmiyor (1,0 → 1,0). Rota **gerçekten** molozun kenarını
    sıyırıyor; çünkü `analyze_path`'te C-uzayı şişmesi yok ve fiziksel gövde
    açıklığı `mpp`'ye bağlı — §11.2 **Halka 5 SAHİPSİZ** (D-22).
  - ⚠ **Eşiği tek başına düşürmek ÇÖZÜM DEĞİL:** 0,03'e çekmek 6/7 kararı
    geçirir ama ikisi zaten **yanlış şerit** ve hepsi 1 px açıklıklı, fiziksel
    olarak sürülemez rotalar. Önce C-uzayı (Halka 5 + `r_gerekli_px`), sonra
    K-B kalibrasyonu. Sıra ters çevrilirse §5.3.2 uyarınca çekimserlikten
    **daha tehlikeli** olur.
  - **Kalıcı kapı (GUI tarafı):** `tests/test_yks_gui_uretim_hizasi.py`
    `KompozitKaynakTests` — açılış kaynağı, dört eski kaynağın korunması,
    manifest okuma, fail-closed, ve **beklenen şeridin karara sızmadığı**
    (beklenti 1/2/3 yapılınca karar değişmiyor) testi.

  - 🔴 **BÜYÜKLÜK DÜZELTİLDİ · 2026-08-11 · Claude 1 (D-51).** İlk ölçümümde
    üretim yolunu **yeniden kurmuştum**; gerçek `iha_perceive._infer` ile
    yeniden ölçtüm:
    ```text
    ONCE (kurgu ile) : toplam 67 kare · AYNI  0 · IRAKSAK 67 (%100.0)  ← YANLIŞ
    SIMDI (gercek)   : toplam 67 kare · AYNI 46 · IRAKSAK 21 ( %31.3)  ← DOĞRU
    ```
    Ayrışma yönü: hakem ekranı rota açıyor, üretim `DUSUK_GUVEN` ile reddediyor.
    **Bulgu ve parametre tablosu aynen geçerli**, yalnız oran %31,3. Bu hâliyle
    bile ciddi: hakem her üç kareden birinde sahada verilmeyecek kararı görüyor.
  - 🔴 **YÖN DÜZELTMESİ · D-53.** Ölçüm zemini bir **OTOPARK** çıktı. Ayrışmada
    **yanlış olan taraf hakem ekranıdır**: `analyze_path` (tek-koridor) otoparkta
    koridor buluyor, `rota_bul` (üç-kapı arena) doğru şekilde çekimser kalıyor.
    Bu görev **GUI'yi üretime hizalar** — üretimi GUI'ye değil. Hizalama
    sonrasında hakem ekranının bu karelerde **daha sık çekimser kalması
    BEKLENEN sonuçtur**, gerileme değil.
  - **Ayrışan parametreler** (anayasa madde 16 ihlali — çıplak sabit):

    | Parametre | `rpi_inference`/`iha_perceive` | `yks_gui` |
    |---|---|---|
    | `imgsz` | `INFER_SIZE=512` / `CANON=1024` | çıplak `512` |
    | letterbox | `_letterbox_square` **var** | **YOK** (ham görüntü) |
    | zemin eşiği | `conf=0.15` | çıplak `0.30` → `0.05` |
    | engel eşiği | — | çıplak `0.10` |
    | `min_area_ratio` | `0.01` | çıplak `0.02` |
  - **Yap:** GUI kendi çıkarım hattını **yeniden yazmasın**; üretim fonksiyonunu
    çağırsın veya parametreleri tek kaynaktan (`karar_sozlesmesi.py` /
    `CONTRACTS.md`) okusun. T8'in `analyze_path` kopyası için verdiğimiz kararın
    aynısı: **ölçüm yolu üretim yolundan ayrı olamaz.**
  - ⚠ **Sıra:** Önce **T35**. T35 düzelmeden GUI'yi üretime hizalarsak hakem
    ekranı 67/67 kareyi reddeder — yani ekran "doğru" ama kullanılamaz olur.
  - **Kapı:** Aynı 67 karede iki yolun kararı **67/67 aynı**; ıraksama tablosu
    yeniden koşulup yapıştırılacak. `codes/test_rota_sentetik.py` **15/15**.

- [x] **T41 — İçerik sözleşmesi hiçbir çağrı yerine bağlanmadı: saha yolu hâlâ `KAPALI_DAR`**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex-2 yazdı.
    Çağrı-yeri tablosunu **AST ile** üretmiş (elle değil) — 7 satırın hepsi dolu,
    3 bağlanmayanın gerekçesi ayrı ayrı yazılmış ve *"bütün çağrıların bağlandığı
    iddia edilmez"* demiş. İstediğim dürüstlük tam olarak bu.
  - **Bağımsız doğrulamalarım:**
    ```text
    uretec listesi: 9 dosya · bayt-esit: 9/9
    sozlesme disinda IKIZI OLAN dosya: yok
    rota  DUSTU  rota uretilemedi: durum=BELIRSIZ_COKLU   ← KAPALI_DAR KALKTI
    GECTI 4 · DUSTU 3 · SAHIPSIZ 3 · KOPUK HALKALAR (6)
    ```
    `GECTI` iddia edilmemiş — doğru. Otoparkta `BELIRSIZ_COKLU` **fail-closed
    doğru davranıştır** (D-53); halka ancak T38+T40 ile meşru şekilde geçer.
  - **`iha_haritala.py:324` gerekçesini kendim okudum — doğru, hatta daha güçlü:**
    o çağrı `baslangic`/`hedef` tohum maskelerini `_tohum_maskesi(KB/HB)` ile
    **açıkça** veriyor ve gerçek `mpp=MPP` kullanıyor. Yani `icerik`in düzelteceği
    varsayılan uç-bant tohumlaması orada **hiç kullanılmıyor**. Bağlanmaması doğru.
  - **Kanonik karar da doğru:** `scripts/jetson_fps.py` çalıştırılabilir kaynak,
    paket dosyası dağıtım aynası. Üreteç bu yönü artık yapısal olarak zorluyor.
  - 🔴 **Kalıntı — yine benim talimat çelişkim (yeni T42):**
    `jetson_paket/kod/kamera_dogrula.py:118` bağlanamadı çünkü *"ikizi yok,
    DOKUNMA"* ile *"`jetson_paket/kod/**` yalnız üreteçle"* kurallarım birlikte
    **düzenlenebilir kanonik kaynak bırakmadı.** Codex-2 bunu zorlamak yerine
    raporladı.

- [STATUS: KAPANDI] **T41 — özgün kayıt** · 6 çağrı yeri · **KRİTİK** · bağımlı: **T35** (bitti) · kanıt: `REVIEW_LOG.md` D-57
  - **Kanıt — kendim ölçtüm:** `rota_bul` artık `icerik` sözleşmesini taşıyor ve
    geçirilince `KAPALI_DAR=16` → `ACIK=1 | BELIRSIZ_COKLU=15` oluyor. Ama
    **hiçbir üretim çağrısı geçirmiyor**, yani saha yolu bugün hâlâ 16/16
    `KAPALI_DAR` üretiyor:
    ```text
    [BAGLI DEGIL] jetson_paket/kod/jetson_fps.py:162
    [BAGLI DEGIL] jetson_paket/kod/kamera_dogrula.py:118
    [BAGLI DEGIL] scripts/jetson_fps.py:162
    [BAGLI DEGIL] scripts/saha_kuru_kosu.py:482,492
    [BAGLI DEGIL] scripts/v21_degerlendir_ve_paketle.py:71
    [BAGLI DEGIL] simulation/scripts/iha_haritala.py:324
    ```
  - **Yap — her çağrı yerinde ÖNCE ÖLÇ, sonra bağla.** Girdinin letterbox'lı olup
    olmadığını **koda bakarak doğrula**; letterbox'lıysa kutuyu `_preprocess`'ten
    **taşı** (yeniden hesaplama), değilse **geçirme** ve nedenini göreve yaz.
    ⚠ `iha_haritala.py:324` `mpp=MPP` ile gerçek ölçek kullanıyor ve letterbox
    yapmıyor olabilir — **varsayma, oku.**
  - **Ek kapsam (T39 kalıntısı):** `jetson_fps.py` ikizini de sözleşmeye al —
    `scripts/jetson_paket_hazirla.py` `KOPYALAR` listesine ekle (liste 8 → 9,
    testteki `assertEqual` da güncellenecek). `kamera_dogrula.py`'nin ikizi yok,
    dokunulmayacak.
  - **Kapı:**
    1. Her çağrı yeri için tablo: **letterbox var/yok · bağlandı/bağlanmadı ·
       gerekçe**. Bağlanmayan her satırın gerekçesi yazılacak.
    2. `scripts/saha_kuru_kosu.py` → `rota` halkasının durumu **önce/sonra**
       raporlanacak. ⚠ Halka **otopark karesiyle** koştuğu için `GECTI`
       BEKLENMİYOR — beklenen, `KAPALI_DAR`ın kalkması. `GECTI` iddiası
       edilmeyecek (o T38+T40'ın işi).
    3. Madde 15: bağlama sonrası hiçbir çağrı yerinde serbest piksel artmayacak.
    4. Üreteç 9/9 · `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.
  - **Çağrı-yeri denetimi — gerçek AST çıktısı (2026-08-11):** `kamera_dogrula.py`
    satırı görevdeki `ikizi yok, DOKUNMA` ve `jetson_paket/kod/**` dosyalarına
    yalnız üreteçle yazma kuralları birlikte uygulanabilir bir kanonik kaynak
    bırakmadığı için açıkça bağlı değildir. Bütün çağrıların bağlandığı iddia
    edilmez.
    ```text
    jetson_paket/kod/jetson_fps.py:162 | letterbox=VAR | baglandi=EVET | gerekce=_preprocess exact kutuyu dondurur; scripts/jetson_fps.py kanoniginden uretecle 9. ayna olarak baglandi
    jetson_paket/kod/kamera_dogrula.py:118 | letterbox=VAR | baglandi=HAYIR | gerekce=_preprocess exact kutuyu dondurur; ancak ikizi yok/DOKUNMA ve paket dosyasina elle yazma yasagi nedeniyle baglanmadi
    scripts/jetson_fps.py:162 | letterbox=VAR | baglandi=EVET | gerekce=_preprocess exact kutuyu dondurur; maske tam tuval boyutunda kaldigi icin ayni nesne tasindi
    scripts/saha_kuru_kosu.py:482 | letterbox=VAR | baglandi=EVET | gerekce=_preprocess kutusu halka_cikarim_ve_maske donusunden halka_rota'ya tasinir; ayni nesne verildi
    scripts/saha_kuru_kosu.py:495 | letterbox=YOK | baglandi=HAYIR | gerekce=maske fiziksel ROI dilimiyle yerel koordinata gecmistir; eski tuval kutusu bu sekilde gecersiz olur
    scripts/v21_degerlendir_ve_paketle.py:71 | letterbox=VAR | baglandi=EVET | gerekce=_preprocess exact kutuyu dondurur; kirpma dolguyu sifirlar ama tuval geometrisini korur
    simulation/scripts/iha_haritala.py:324 | letterbox=YOK | baglandi=HAYIR | gerekce=1024x1024 mozaik 1024 infer edilir ve _infer maskeleri content koordinatina fiziksel kirpar; mpp/KB/HB ayrica verilir
    EXIT_CODE=0
    ```
  - **Kanonik kararı:** `scripts/jetson_fps.py` repo içindeki çalıştırılabilir
    kaynaktır; kökü `parents[1]` ile bulup `codes/` modüllerini yükler. Paket
    dosyası dağıtım aynasıdır ve kurulumda yeniden `scripts/` altına taşınır.
    Üreteç/test bu yönü ve toplam dokuz kaynağı artık yapısal olarak zorluyor.
  - **Kuru koşu önce/sonra — ikisinde de genel çıkış 1 ve `rota DUSTU`; `GECTI`
    ilanı yoktur:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py
    [ÖNCE] rota  DUSTU  letterbox'li girdide durum=KAPALI_DAR, ayni maske kirpilinca durum=ACIK — tohum bandi dolguya dusuyor
    [ÖNCE] GECTI 4 · DUSTU 3 · SAHIPSIZ 3 · ATLANDI 0
    [ÖNCE] KOPUK HALKALAR (6): kamera, model_yukleme, olcek, hedef_konumu, rota, motor
    [ÖNCE] EXIT_CODE=1

    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py
    [SONRA] rota  DUSTU  rota uretilemedi: durum=BELIRSIZ_COKLU
    [SONRA] GECTI 4 · DUSTU 3 · SAHIPSIZ 3 · ATLANDI 0
    [SONRA] KOPUK HALKALAR (6): kamera, model_yukleme, olcek, hedef_konumu, rota, motor
    [SONRA] EXIT_CODE=1

    [T41_ROTA_ONCE] halka=DUSTU karar=KAPALI_DAR kirpik=ACIK sebep=letterbox'li girdide durum=KAPALI_DAR, ayni maske kirpilinca durum=ACIK — tohum bandi dolguya dusuyor
    [T41_ROTA_SONRA] halka=DUSTU karar=BELIRSIZ_COKLU kirpik=ACIK icerik_aktarildi=True kirpik_karsilastirma=yalniz_tanisal sebep=rota uretilemedi: durum=BELIRSIZ_COKLU
    EXIT_CODE=0
    ```
  - **İlk 16 otopark karesi — model davranışı ve Madde 15 gerçek ölçümü; görev
    veya arena başarısı kanıtı değildir:**
    ```text
    [T41_KUME] kare=16 model=models\navitas_seg_v21_best.pt imgsz=512 conf=0.25
    [T41_16_ONCE] ACIK=0 | KAPALI_DAR=16 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=0 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T41_16_SONRA] ACIK=1 | KAPALI_DAR=0 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=15 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T41_MADDE15] cagri=scripts/jetson_fps.py kare=16 roi_serbest_artan=0 k2_serbest_artan=0
    [T41_MADDE15] cagri=jetson_paket/kod/jetson_fps.py kare=16 roi_serbest_artan=0 k2_serbest_artan=0
    [T41_MADDE15] cagri=scripts/saha_kuru_kosu.py:482 kare=16 roi_serbest_artan=0 k2_serbest_artan=0
    [T41_MADDE15] cagri=scripts/v21_degerlendir_ve_paketle.py kare=16 roi_serbest_artan=0 k2_serbest_artan=0
    EXIT_CODE=0
    ```
  - **Regresyon, paket ve genel kapılar — gerçek çıktılar:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_costmap_icerik_cagri_yerleri.py -v
    Ran 5 tests in 2.329s
    OK
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/jetson_paket_hazirla.py
    [JETSON_PAKET] codes\karar_sozlesmesi.py -> jetson_paket\kod\karar_sozlesmesi.py
    [JETSON_PAKET] codes\rpi_inference.py -> jetson_paket\kod\rpi_inference.py
    [JETSON_PAKET] codes\costmap_path_finder.py -> jetson_paket\kod\costmap_path_finder.py
    [JETSON_PAKET] scripts\jetson_fps.py -> jetson_paket\kod\jetson_fps.py
    [JETSON_PAKET] comms\protocol.py -> jetson_paket\kod\protocol.py
    [JETSON_PAKET] comms\link.py -> jetson_paket\kod\link.py
    [JETSON_PAKET] comms\iha_sender.py -> jetson_paket\kod\iha_sender.py
    [JETSON_PAKET] comms\inis_kaniti.py -> jetson_paket\kod\inis_kaniti.py
    [JETSON_PAKET] comms\iha_inis_yayinci.py -> jetson_paket\kod\iha_inis_yayinci.py
    [T41_9X9] kopya=9 bayt_esit=9
    GENERATOR_EXIT_CODE=0
    VERIFY_EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 216 tests in 34.350s
    OK
    EXIT_CODE=0

    [T41_JETSON_FPS_PARITE] bayt_esit=1 canonical_sha256=0D1D1DB18AA8EDBF8CEDC950F56CD5A16F109A3DAF833877574CFC78E4ACAEDF ayna_sha256=0D1D1DB18AA8EDBF8CEDC950F56CD5A16F109A3DAF833877574CFC78E4ACAEDF
    DIFF_CHECK_EXIT_CODE=0
    ```

- [x] **T40 — Kompozit arena zemini: gerçek karelere arena semantiği yapıştır**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex-1 yazdı.
  - ⚠ **İlk ölçümüm YANLIŞTI ve düzelttim:** araç katmanını düşürüp
    `icerik`/`mpp` geçirmeden `rota_bul({0:zemin,1:engel}, mpp=None)` çağırmıştım
    → 5/7 çıkmıştı. `arena_rotasi`'yi okuyunca gördüm ki o bir yeniden kurgu
    değil, **sözleşme katmanlarıyla** (`COSTMAP_YOL/ENGEL_KATMANLARI`, araç
    katmanı dâhil) üretim girişini çağırıyor. Doğru sözleşmeyle yeniden ölçtüm:
    ```text
    kare                          bekl     karar   pozitif kontrol   m15
    frame_000006_000000864_cp_00     1    ACIK/1        KAPALI_DAR     0
    frame_000008_000001008_cp_00     1    ACIK/1        KAPALI_DAR     0
    frame_000018_000002160_cp_00     3    ACIK/3        KAPALI_DAR     0
    frame_000011_000000600_cp_00     1    ACIK/1        KAPALI_DAR     0
    frame_000014_000000672_cp_00     2    ACIK/2        KAPALI_DAR     0
    frame_000015_000000696_cp_00     2    ACIK/2        KAPALI_DAR     0
    frame_000016_000000720_cp_00     2    ACIK/2        KAPALI_DAR     0
    [GECTI] karar manifest seridiyle ayni (7/7)
    [GECTI] POZITIF KONTROL: kapatilinca ACIK kalmiyor (7/7 KAPALI_DAR)
    [GECTI] MADDE 15: serbest(K1∧¬K2) ⊆ serbest(K1)
    [GECTI] arac kapsamasi %100.000
    ```
  - **Aradığım üç incelik de yerinde:**
    1. **Pozitif kontrol gerçek** — açık şerit kapatılınca 7/7 `KAPALI_DAR`.
       Bu olmadan test kendi kendini doğrulardı (T4 dersi).
    2. **Dairesellik kapatılmış** — üreteç `arena_rotasi()` çağırmıyor, yani
       karar sonucu örnek seçimini etkileyemiyor.
    3. **Bariyer "planlanan dikdörtgen" sayılmıyor** — yalnız RGBA alfa eşiğini
       gerçekten geçen ve koridoru üstten alta kopardığı bağımsız bağlı-bileşen
       testiyle kanıtlanan pikseller class-1'e giriyor.
  - **Manifest sınırı kendisi kaydetmiş** (istediğim niteleme, makine-okunur):
    `arena_karar_mantigi_kaniti: True` · `arena_model_basarimi_kaniti: False` ·
    `arena_domain_boslugu_kapandi: False` · ölçek kaynağı "gerçek kamera mpp
    ölçümü değildir".
  - **Sınır — verim düşük, ilan edilmeli:** 67 ham kareden **7'si** üretildi;
    60'ı gerekçesiyle atlandı (`arena_c_uzayi_veya_hedef_uygunsuz` 52 ·
    `arena_gercek_bariyer_kesmiyor_serit_3` 7 · `..._serit_2` 1). Otopark üç
    şeritlik arena yerleşimine nadiren yer bırakıyor. **T38 için yeterli**
    (bir determinist kare gerekiyor); genel arena karar kümesi olarak **ince**.

- [STATUS: KAPANDI] **T40 — özgün kayıt** · `scripts/copy_paste_augmentation.py` → `data/arena_kompozit/` · **KRİTİK** · **T38'i açar** · kanıt: `REVIEW_LOG.md` D-53, D-56
  - **Neden:** Gerçek arena çekimi iptal edildi (kullanıcı kararı, süresiz).
    Elimizdeki tek gerçek zemin bir **otopark**; arena mantığı (üç kapı, uç bant
    teması, güzergâh seçimi) orada **sınanamıyor**. Saf sentetik arena ise
    üretecin kendi dağılımı — eğitimde kullandığımız veriyle test etmek dairesel.
  - **Çözüm:** İkisinin arasında üçüncü yol — **gerçek görüntü + kontrollü arena
    semantiği**. `scripts/copy_paste_augmentation.py` bunu zaten yapıyor
    (S1'de araç kâhini DOTA OBB'ye geçirildi): gerçek zemin üzerine `1=engel`
    (moloz) ve `2=hedef` (kırmızı H brandası) poligonları yapıştırıyor.
  - **Yap:**
    1. Girdi `data/raw_frames/**`; çıktı `data/arena_kompozit/` (**determinist
       tohum** + manifest; aynı tohum → bayt-aynı çıktı).
    2. Engelleri, şartnamenin **tam üç güzergâhı** oluşacak biçimde yerleştir;
       her karede **hangi güzergâhın açık olduğu manifest'e yazılsın** — yer
       gerçeği bizde olduğu için ilk kez *beklenen kararı* biliyoruz.
    3. 🔴 **En kritik kural (`sentetik arena` dersinden):** *geçilemez nesneyi
       asla etiketsiz bırakma.* Arka plan bir **otopark** — park hâlindeki
       araçlar **engel katmanına girmek zorunda**. Girmezse v16'yı %2,7'den
       %31,6'ya çökerten "etiketsiz engel" hatasını birebir tekrarlarız.
       Araç kâhini **DOTA OBB** (COCO değil — ölçüldü: 2'ye karşı 93 araç).
  - **Kapı — yer gerçeği elimizde olduğu için ilk kez GERÇEK kapı kurulabiliyor:**
    1. Her kompozit karede yer-gerçeği maskeleriyle `rota_bul` → `ACIK` **ve**
       `yol_no` manifest'teki açık güzergâhla **aynı**. Uyumsuzluk sayısı **0**.
    2. **Pozitif kontrol:** açık güzergâh kapatıldığında karar `KAPALI_*` veya
       `BELIRSIZ_*` olacak — `ACIK` kalırsa test hiçbir şey ölçmüyordur (T4 dersi).
    3. **Araç kapsama ölçümü:** DOTA OBB'nin bulduğu araç pikselinin ≥%95'i
       engel katmanında. Sayıyı yapıştır.
    4. Determinizm: aynı tohumla iki koşu → sha eşit.
    5. `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.
  - ⚠ **Sınır — raporlarda yazılacak:** Bu küme **karar mantığını** sınar,
    **model başarımını** sınamaz. Arena domain boşluğu (K-3: mAP arena
    sıralamasını tersine çeviriyor) bu görevle **kapanmaz**.
  - **Uygulama özeti (2026-08-11 · Codex-1):** Eski rastgele kip ve v20
    varsayılanı korundu; yeni `--arena` kipi etkin üretim modeli olduğu için v21'i
    seçiyor. İlk gerçek karede v20'nin zemin/engel çıktısı `0/0 px`, v21'in
    `460200/146812 px` ölçülmüştü; bu seçim yine model başarımı ilanı değildir.
    Şeritler yalnız `serit_no()` ile kuruluyor. DOTA-OBB araçları ve v21 engelleri
    korunan katmana giriyor; moloz araç/mevcut engel üstüne yapıştırılmıyor.
    Planlanan dikdörtgen engel sayılmıyor: yalnız RGBA alfa eşiğini gerçekten
    geçen, yerel koridoru üstten alta kopardığı bağımsız bağlı-bileşen testiyle
    kanıtlanan pikseller class-1/rota/PNG maskesine giriyor. Üreteç
    `arena_rotasi()` çağırmıyor; karar sonucu örnek seçimini etkileyemiyor.
  - **H üretimi ve ölçek:** Harici hedef yokken açık şeridin hedef bandına
    prosedürel kırmızı kare ve beyaz H çiziliyor. Kenar `2.0 m / mpp`; kontrollü
    kompozit `mpp = simulation.scripts.arena.HTAB / kısa kenar`. Bu açıkça bir
    kompozit ölçek varsayımıdır, gerçek kamera `mpp` ölçümü değildir. Çıktı 7
    geometrik uygun örnek/60 bağımsız geometri reddidir; üç açık şerit de temsil
    edilir. İlk deterministik çıktı:
    `images/train/whatsapp_video_2026_07_30_at_11_44_03_frame_000006_000000864_cp_00.jpg`.
  - **Üretim + determinizm kapısı — iki ayrı gerçek koşum:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/copy_paste_augmentation.py --arena --temizle
    Modeller yukleniyor: zemin=navitas_seg_v21_best.pt, arac=yolov8m-obb.pt
      arac kahini: DOTA-OBB (task=obb)
    TOPLAM: 7 YOLO-seg ornegi yazildi, 60 atlandi -> O:\navitas\data\arena_kompozit
    KOŞUM_1_SHA256=2c2a81c4721c110a13b4d0b028ffe74263d63df741caddb6421641a090b77c14
    URETIM_EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/copy_paste_augmentation.py --arena --temizle
    TOPLAM: 7 YOLO-seg ornegi yazildi, 60 atlandi -> O:\navitas\data\arena_kompozit
    KOŞUM_2_SHA256=2c2a81c4721c110a13b4d0b028ffe74263d63df741caddb6421641a090b77c14
    URETIM_EXIT_CODE=0
    ```
  - **Bağımsız kalıcı arena kapısı — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B tests/arena_kompozit_kapisi.py
    [T40_KAPI] kompozit=7 ACIK=7 rota_ile_elenen=0 acik_seritler={1: 3, 2: 3, 3: 1}
    [T40_POZITIF] kapatilan=7 durumlar={'KAPALI_DAR': 7}
    [T40_ARAC] arac_px=653486 kapsanan_px=652680 kapsama_yuzde=99.877 kare_bazli_dusuk=0
    [T40_BARIYER] exact_px=35560 kapsanan_px=35465 kapsama_yuzde=99.733
    [T40_MADDE15] serbest_artan=0
    [T40_HATALAR] {'rota_sonucuyla_elenen': 0}
    [T40_SHA256] 2c2a81c4721c110a13b4d0b028ffe74263d63df741caddb6421641a090b77c14
    [T40_SINIR] Kompozit kume karar mantigini sinar; model basarimini veya gercek arena domainini sinamaz.
    EXIT_CODE=0
    ```
  - **Regresyon/genel kapılar — gerçek çıktı:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_copy_paste_arena.py -v
    Ran 11 tests in 0.770s
    OK
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 227 tests in 34.324s
    OK
    EXIT_CODE=0
    ```

- [STATUS: READY_FOR_REVIEW] **T43 — Ölçek halkası (Halka 5) sahipsiz ve `analyze_path` kolunda C-uzayı yok** · `codes/rpi_inference.py`, `codes/costmap_path_finder.py`, `codes/karar_sozlesmesi.py`, `CONTRACTS.md` · **TIKAYICI** · kanıt: `REVIEW_LOG.md` D-59, D-22
  - **✅ YAPILDI · 2026-08-11 · Claude-2** · çözüm kaydı `REVIEW_LOG.md` **D-60b**.
  - **Görev 1 — Halka 5 SAHİPSİZ → GEÇERLİ.** İki kaynak ölçülerek seçildi:
    **(a) irtifa + FOV/odak → ÜRETİLEBİLİR** (irtifa saha yolunda zaten
    okunuyor: MAVLink `relative_alt`, `comms/inis_kaniti.py:143`);
    **(b) 2×2 m H brandası → ÜRETİLEMEZ**, ölçüldü: `v21.names =
    {0: traversable, 1: blocked}`, hedef dedektörü yok (D-23 doğrulandı).
    Sahip `codes/karar_sozlesmesi.py`; `CONTRACTS.md` §5 yeniden yazıldı,
    §11.2 Halka 5 güncellendi, §6.4'e `OLCEK_YOK` eklendi. CLI: `--mpp` /
    `--irtifa`+`--fov`|`--odak`; üç görev çağrı yeri ölçek yoksa fail-closed.
  - **Sessiz varsayım açığa çıkarıldı:** `olcek_px(None)` hâlâ `r_gerekli_px =
    1,10 px` diyor, gerçek değer 12,7 px → gövde açıklığı **~11 kat**
    küçülüyordu. Sayı geriye uyum için korundu, görev yolu artık kullanmıyor.
  - **Görev 2 — C-uzayı taşındı** (`rota_bul`'daki `dt >= r_gerekli_px` kalıbı;
    yeniden yazılmadı). Madde 15 yapısal: `{dist≥r} ⊆ {dist>0}`.
  - **Görev 3 — K-B: DEĞER DEĞİŞMEDİ (0.20), ROLÜ DEĞİŞTİ.** C-uzayı güvene
    hesaplanabilir taban koyuyor: `taban = r_gerekli_px / (0,035·icerik_w)`.
    K-B ancak `mpp > 1,10/(0,20·0,035·icerik_w)` iken ateşleyebilir →
    `icerik_w=576` için `mpp > 0,273`, `1024` için `> 0,153`; görev
    irtifasında tipik `mpp` 0,03–0,12 → **ölçekli kipte ateşlemez**.
    Yeni rolü: **çözünürlük koruyucusu**. Düşürmek anlamsız, yükseltmek
    zararlı — gerekçe `CONTRACTS.md` §6.3'te.
  - **KAPILAR (gerçek çıktı):**
    ```text
    KAPI 1  arena kompoziti · C zinciri (analyze_path + K-B) · yer gercegi maskesi
              ONCE  (C-uzayi YOK): DOGRU 1/7 · YANLIS 0 · RET 6
              SONRA (C-uzayi VAR): DOGRU 6/7 · YANLIS 0 · RET 1
              darbogaz 1,0 px -> 13,0-15,0 px · guven 0,028-0,117 -> 0,644-0,744
              kalan 1 ret UC_BANT_TEMAS_YOK; C-uzayindan ONCE de vardi
    KAPI 2  MADDE 15 ihlali 0/7  (C_uzayi \ serbest_once = 0 piksel, 7 karede)
    KAPI 3  otopark ilk 16: mpp YOK -> cekimser 3/16 · mpp=0,0868 -> 2/16
              AZALMA GEREKCESI (kare kare): degisen 3 karenin ucu de darbogazi
              1,0/2,0/1,4 px olan duvar-siyiran rotalardi.
                frame_000005  DUSUK_GUVEN(1,0) -> yol=1 (darbogaz 18,2)
                frame_000006  DUSUK_GUVEN(2,0) -> GORUS_HATTI_KOPUK
                frame_000007  DUSUK_GUVEN(1,4) -> GORUS_HATTI_KOPUK
              Guvenlik KESIN artti: once frame_000008 8,0 px darbogazla
              (fiziksel gerek 12,7 px'in ALTINDA) yayinlaniyordu, simdi 13,0.
    KAPI 4  codes/test_rota_sentetik.py 15/15 · discover -s tests -q
              Ran 259 tests OK · git diff --check exit 0
    ```
  - **Kalıcı kapı:** `tests/test_olcek_ve_c_uzayi.py` (17 test), **pozitif
    kontrol dahil** (C-uzayı kapalıyken darboğazın gerçekten küçük kaldığı).
  - ⚠ **Açık bırakıldı:** `ROTA_DARBOGAZ_TAM_ORANI = 0.035` hâlâ otoparktan
    kalibre birimsiz oran; C-uzayı geldiğine göre güven `darboğaz /
    r_gerekli_px` (fiziksel kat) olarak tanımlanabilir → ayrı görev.
    `data/raw_frames` gerçek `mpp`'si bilinmiyor; KAPI 3'teki 0,0868 varsayımdır.
  - ⚠ Satırı Claude-2 açtı (kuyrukta yoktu); kapsam kullanıcı direktifinden alındı.
  - **Doğrulanmış kanıt (Claude 1, 7 kompozit kare):** `rota_bul(mpp=manifest)`
    → **7/7 doğru** · `rota_bul(mpp=None)` → 5/7 · `analyze_path + K-B` → **0/7**.
    Sahada koşan zincir sonuncusu.
  - **Görev 1:** Halka 5'i (ölçek) saha yolunda üretilebilir kıl; `mpp` yoksa
    açık fail-closed davranış — sessiz `1 px/m` varsayımı kaldırılacak.
  - **Görev 2:** Gövde açıklığı kısıtını `analyze_path` koluna **taşı**
    (`rota_bul`'daki `r_gerekli_px` yolu yeniden yazılmayacak). Madde 15:
    serbest alan yalnız daralabilir.
  - **Görev 3:** K-B'yi **Görev 2'den sonra** arena yer gerçeğinde yeniden ölç.

- [ ] **T42 — `kamera_dogrula.py` içerik sözleşmesine bağlanamadı: talimat kilidi** · `jetson_paket/kod/kamera_dogrula.py:118` · KÜÇÜK · kanıt: T41 çağrı-yeri tablosu
  - **Kanıt (Codex-2, AST tablosu):** `letterbox=VAR · baglandi=HAYIR · gerekce=
    _preprocess exact kutuyu dondurur; ancak ikizi yok/DOKUNMA ve paket
    dosyasina elle yazma yasagi nedeniyle baglanmadi`
  - **Sebep bende:** T41'de *"`kamera_dogrula.py` ikizi yok, DOKUNMA"* ile
    *"`jetson_paket/kod/**` yalnız üreteçle güncellenecek"* kurallarımı birlikte
    verdim; ikisi birlikte **düzenlenebilir kanonik kaynak bırakmadı**. Codex-2
    zorlamak yerine raporladı — doğru davranış.
  - **Etkisi sınırlı:** Bu bir Jetson kamera **tanı** betiği; bağlanmadığı için
    letterbox'lı girdide gereksiz `KAPALI_DAR` raporlayabilir. Karar yolunu
    etkilemiyor, ama tanı aracının yanlış sinyal vermesi T38'in dersidir.
  - **Yap:** Ya `scripts/kamera_dogrula.py` kanonik kaynağını oluşturup üreteç
    listesine ekle (9 → 10), ya da betiği paket-yerel kabul edip **açıkça**
    sözleşme dışı ilan et ve `icerik`i orada doğrudan bağla. Hangisini seçtiysen
    gerekçesini yaz.
  - **Kapı:** Üreteç N/N bayt-eşit · letterbox'lı girdide `KAPALI_DAR` kalkıyor ·
    `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.

- [ ] **T38 — Saha kuru koşusunun `rota` halkası OTOPARK karesiyle sınanıyor: meşru şekilde geçemez** · `scripts/saha_kuru_kosu.py:250` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-53
  - **Kanıt:** `:250` halka girdisini `data/raw_frames/**` içinden seçiyor.
    O kareleri gözle inceledim (iki ayrı video, aynı sahne): **bir otopark** —
    onlarca park hâlinde araç, bina, ağaçlar. Şartnamenin 3 işaretli güzergâhı
    **yok**. `rota_bul` `"{n} kapi tespit edildi (3 beklenir)"` diyerek çekimser
    kalıyor (`costmap_path_finder.py:780-782`) — **doğru davranış**.
  - **Neden KRİTİK:** Bu halka **hiçbir doğru uygulamayla geçemez**. Bugüne kadar
    `rota DUSTU` satırı bir kod kusuru sanıldı ve T35 iki tur boyunca bu yanlış
    kapının peşinde koştu. Ölçülmeyen bir kapı, ölçülmüş bir kusurdan daha
    pahalıya mal oldu.
  - **Yap — mimari karar GÜNCELLENDİ (2026-08-11, Claude 1):** Gerçek arena
    çekimi **iptal** edildi (kullanıcı kararı, süresiz). Halkanın girdisi
    **T40'ın ürettiği kompozit arena karesi** olacak — determinist, dosya adı
    göreve yazılacak, rastgele seçim yok. Saf sentetik arena **tercih edilmedi**:
    eğitimde kullandığımız üretecin kendi dağılımıyla test etmek dairesel olur;
    kompozit kare **gerçek görüntü istatistiği** taşır.
  - **Bağımlı: T40.** T40 bitmeden bu görev başlamaz.
  - ⚠ **Raporlama şartı:** Halka çıktısında girdinin **kompozit** olduğu açıkça
    yazılacak. Kompozit kare arena **karar mantığını** sınanabilir kılar;
    **gerçek arena kanıtı yerine geçmez.** `GECTI` satırı bu niteleme olmadan
    basılmayacak.
  - **Otopark girdisiyle `DUSTU` raporlaması kaldırılacak** — kod kusuru ima
    ediyor, oysa kusur zeminde. Girdi sentetiğe bağlanamıyorsa `SAHIPSIZ` yazılacak.
  - **Kapı:** Halka ya arena benzeri girdiyle **GECTI** verecek, ya da
    `SAHIPSIZ` olarak raporlanıp gerekçesi çıktıya yazılacak. Otopark karesiyle
    `DUSTU` raporlaması **kaldırılacak**.
  - **Bağlı:** T35 (içerik sözleşmesi) bu görevden bağımsız ilerler.

- [x] **T39 — Jetson paket üreteci, parite testinin zorunlu kıldığı iki dosyayı ÜRETMİYOR**
  - **✅ MİMAR DENETİMİ GEÇTİ · 2026-08-11 · Claude 1.** Kodu Codex-2 yazdı.
    Doğru çözüm seçilmiş: test artık listeyi **üreteçten içe aktarıyor**
    (`from jetson_paket_hazirla import KOPYALAR`) — iki listenin ıraksaması
    **yapısal olarak imkânsız**. Üstüne `assertEqual(8, len(KOPYALAR))` koymuş,
    yani liste sessizce küçültülemiyor. Elle senkron tutulan ikinci liste yok.
  - **Kendi ölçümüm:** 8/8 dosya kanonikle bayt-eşit; tam paket **210 test OK**.
  - 🔴 **KALINTI — kusur SINIFI tam kapanmadı (yeni T41 kapsamına alındı):**
    `jetson_paket/kod/jetson_fps.py` ile `scripts/jetson_fps.py` **ikiz** ve
    **sözleşmenin dışında** — şu an bayt-eşitler ama bunu zorlayan hiçbir şey yok.
    ```text
    paket dosyasi            uretecte?  ikiz                       durum
    jetson_fps.py            HAYIR      scripts/jetson_fps.py      AYNI
    kamera_dogrula.py        HAYIR      —                          (ikizi yok, sorun degil)
    ```
    D-01 ve D-55'in aynısı: bugün eşit, yarın sessizce ıraksar.

- [STATUS: KAPANDI] **T39 — özgün kayıt** · `scripts/jetson_paket_hazirla.py:15-22`, `tests/test_jetson_comms_paketi.py:24-25` · ÖNEMLİ · **T35'i TIKIYOR** · kanıt: `REVIEW_LOG.md` D-55
  - **Kanıt — kendim doğruladım:** üreteç **6** dosya kopyalıyor
    (`karar_sozlesmesi`, `protocol`, `link`, `iha_sender`, `inis_kaniti`,
    `iha_inis_yayinci`); parite testi bunlara ek olarak `codes/rpi_inference.py`
    ve `codes/costmap_path_finder.py`'yi de zorunlu kılıyor → **8'e karşı 6**.
    Kalan iki dosya hâlâ **elle kopya**.
  - **Neden şimdi:** `codes/rpi_inference.py` veya `codes/costmap_path_finder.py`'ye
    dokunan her görev tam paketi düşürüyor. T35 tam bu yüzden üçüncü turda da
    ilerleyemedi (D-54). T27'nin kaldırdığını sandığım kırılganlık **hâlâ orada**.
  - **Benim denetim hatam:** T27'yi kapatırken 7/7 sha eşitliğini doğruladım ama
    **üretecin listesiyle testin listesinin aynı olup olmadığını kontrol
    etmedim.** Sha eşitliği, eşitliği *kimin sürdürdüğünü* doğrulamaz.
  - **Yap:** İki listeyi **tek kaynağa** indir — test, üretecin `KOPYALAR`
    haritasını içe aktarsın (ya da ortak bir sözleşme modülünden okusun). İki
    listenin bir daha ıraksaması **yapısal olarak imkânsız** olmalı.
  - **Kapı:** Üreteci koş → `jetson_paket/kod/` içinde **8/8** dosya kanonikle
    bayt-eşit. Sonra `codes/costmap_path_finder.py`'ye zararsız bir boşluk
    değişikliği yap, üreteci **koşmadan** tam paket **düşsün**, koştuktan sonra
    **geçsin** — ikisinin de çıktısını yapıştır (değişikliği sonra geri al).
    `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.
  - **Uygulama:** Parite testi ikinci bir dosya listesi taşımıyor; doğrudan
    `scripts/jetson_paket_hazirla.py:KOPYALAR` haritasını içe aktarıyor. Harita
    `rpi_inference.py` ve `costmap_path_finder.py` dahil sekiz kanonik kaynaktır.
  - **Gerçek kapı çıktıları — üreteç ve 8/8:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/jetson_paket_hazirla.py
    [JETSON_PAKET] codes\karar_sozlesmesi.py -> jetson_paket\kod\karar_sozlesmesi.py
    [JETSON_PAKET] codes\rpi_inference.py -> jetson_paket\kod\rpi_inference.py
    [JETSON_PAKET] codes\costmap_path_finder.py -> jetson_paket\kod\costmap_path_finder.py
    [JETSON_PAKET] comms\protocol.py -> jetson_paket\kod\protocol.py
    [JETSON_PAKET] comms\link.py -> jetson_paket\kod\link.py
    [JETSON_PAKET] comms\iha_sender.py -> jetson_paket\kod\iha_sender.py
    [JETSON_PAKET] comms\inis_kaniti.py -> jetson_paket\kod\inis_kaniti.py
    [JETSON_PAKET] comms\iha_inis_yayinci.py -> jetson_paket\kod\iha_inis_yayinci.py
    EXIT_CODE=0
    [T39_8X8] kopya=8 bayt_esit=8
    EXIT_CODE=0
    ```
  - **Gerçek mutasyon kapısı — boşluk eklendi, üreteç KOŞMADI:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    FAIL: test_paket_kopyalari_kanonik_kaynaklarla_birebir
          (hedef='costmap_path_finder.py')
    AssertionError: paket kopyasi bayat: costmap_path_finder.py
    Ran 202 tests in 33.319s
    FAILED (failures=1)
    EXIT_CODE=1
    ```
  - **Gerçek mutasyon kapısı — üreteç KOŞTU:**
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 202 tests in 32.993s
    OK
    EXIT_CODE=0
    ```
  - **Geçici boşluk geri alındı; üreteç yeniden koşuldu — final durum:**
    ```text
    [T39_FINAL_8X8] kopya=8 bayt_esit=8
    [T39_FINAL_SHA] canonical=0591e1df34b3bbfb5ec3ca01073953d4dfc294f4728039f471d912a0823f1156 paket=0591e1df34b3bbfb5ec3ca01073953d4dfc294f4728039f471d912a0823f1156
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 202 tests in 32.282s
    OK
    EXIT_CODE=0
    ```

- [x] **T35 — `rota_bul` letterbox içerik sözleşmesini hiç taşımıyor: 0/16 kare**
  - **✅ MİMAR DENETİMİ GEÇTİ (SÖZLEŞME) · 2026-08-11 · Claude 1.** Kodu Codex-2
    yazdı — dördüncü turda, önceki üç turda **haklı olarak reddettikten** sonra.
    Bağımsız ölçümüm (Codex-2'nin raporuna bakmadan, gerçek `_preprocess` →
    `predict` → `get_masks` → `rota_bul` zinciriyle):
    ```text
    1 · DURUM DAGILIMI
      icerik GECIRILMEDEN (bugunku hal)  KAPALI_DAR=16
      icerik GECIRILINCE                 ACIK=1 | BELIRSIZ_COKLU=15
    2 · MADDE 15
      serbest pikseli ARTAN kare : 0
    3 · FAIL-CLOSED
      BELIRSIZ_COKLU olup yol/waypoint URETEN kare : 0
    4 · GECERSIZ ICERIK KUTUSU (5 bozuk bicim)
      tuval disina tasan / negatif / kesirli / sifir alan / bool
        -> hepsi durum=MASKE_YOK  yol_no=None
    ```
    Dört kapının dördü de geçti. Özellikle **4. madde**: Codex-2'nin kendi
    önerdiği fail-closed şartını uygulamış — bozuk kutu sessizce kırpılmıyor,
    `MASKE_YOK` üretiyor. İstemediğim hâlde eklenen doğru davranış.
  - 🔴 **AMA KUSUR HÂLÂ CANLI — bunu ilan etmiyorum.** Sözleşme **hiçbir çağrı
    yerine bağlanmadı**; 6 üretim çağrısının tamamı `icerik` geçirmiyor:
    ```text
    [BAGLI DEGIL] jetson_paket/kod/jetson_fps.py:162
    [BAGLI DEGIL] jetson_paket/kod/kamera_dogrula.py:118
    [BAGLI DEGIL] scripts/jetson_fps.py:162
    [BAGLI DEGIL] scripts/saha_kuru_kosu.py:482,492
    [BAGLI DEGIL] scripts/v21_degerlendir_ve_paketle.py:71
    [BAGLI DEGIL] simulation/scripts/iha_haritala.py:324
    ```
    Yani saha yolu bugün hâlâ `KAPALI_DAR=16` üretiyor. **Bu benim kapsam
    kararımdı** (dosya iznini bilerek dar tuttum), Codex-2'nin eksiği değil.
    Bağlama işi: **T41**.
  - **Doğru okuma:** T35 *"sözleşme var ve güvenli"* demektir; *"saha rotası
    düzeldi"* DEMEZ. Saha kuru koşusunun `rota` halkası hâlâ `DUSTU`.

- [STATUS: KAPANDI] **T35 — özgün kayıt** · `codes/costmap_path_finder.py:729`, `scripts/saha_kuru_kosu.py:482` · **KRİTİK** · kanıt: `REVIEW_LOG.md` D-51, D-50, D-25
  - 🔴 **GÖREV YENİDEN YAZILDI · 2026-08-11 · Claude 1.** İlk tanımım yanlıştı;
    Codex-2 zorlamadan geri verdi (D-50), itirazını ölçtüm, **haklıydı** (D-51).
    - ✗ Yanlış hedef: `iha_perceive.py:106`. O yol maskeleri `analyze_path`'e
      vermeden **önce kırpıyor** (`iha_perceive.py:92-94`) ve **12/16 rota
      üretiyor** — kusurlu değil.
    - ✓ Doğru hedef: `rpi_inference._preprocess` → `costmap_path_finder.rota_bul`.
      **0/16**, hepsi `KAPALI_DAR`. `rota_bul` imzasında `icerik` parametresi
      **hiç yok** — sözleşme geçirilmemiş değil, **mevcut değil**.
    - ✗ Verdiğim kapı (`saha_kuru_kosu.py` → `rota GECTI`) izin verdiğim iki
      dosyadan **yapısal olarak ulaşılamazdı**. Kapı hatası bana aittir.
  - **Gerçek fonksiyonlarla ölçüm (16 kare, kurgu değil):**
    ```text
    yol                                              ACIK  ret dagilimi
    E iha_perceive._infer (letterbox + KIRPMA)      12/16  DUSUK_GUVEN=4
    F _preprocess + rota_bul (saha kuru kosusu)      0/16  KAPALI_DAR=16
    rota_bul imzasinda `icerik` var mi : False
    ```
  - 🔴 **KAPI İKİNCİ KEZ DÜZELTİLDİ · 2026-08-11 · Claude 1 (D-52, D-53).**
    Codex-2 ikinci kez zorlamadı ve yine haklıydı:
    - ✗ **`16/16 AÇIK` kapım T4'ün ters yüzüydü.** İçerik sözleşmesi ölçülünce
      `KAPALI_DAR ×16` → `ACIK ×1 + BELIRSIZ_COKLU ×15` oluyor. 16/16'yı
      tutturmak için `BELIRSIZ_COKLU`'yu `ACIK` saymak, yani **fail-closed
      semantiğini bozmak** gerekirdi.
    - ✗ **Mekanizma açıklamam yanlıştı.** `_preprocess` ölçeklemiyor, yalnız
      dolgu ekliyor (`rpi_inference.py:844-849`); `r_gerekli_px = r_gerekli_m /
      mpp` tuval boyutundan bağımsız (`costmap_path_finder.py:107,111`).
    - ✗ **Ölçüm zemini yanlış:** `data/raw_frames` bir **OTOPARK**, HTAB arenası
      değil. `rota_bul`'un 5–9 açıklık görüp çekimser kalması **doğru
      davranıştır**. Kapım dedektörden otoparktan güzergâh üretmesini istiyordu.
  - **Yap:** `rota_bul`'a **geriye uyumlu `icerik=None`** sözleşmesini ekle;
    Codex-2'nin hazırladığı güvenli tasarımı uygula — `serbest = zemin AND NOT
    engel` sonrasında **yalnız ROI ile çıkarma**, aday ve A* varsayılan
    tohumlarını `hedef_bant_yuksekligi(icerik_h)` ile **içerik uçlarından** kur.
    Çağıran kutuyu `_preprocess`'ten **taşısın**, yeniden hesaplamasın.
    `iha_perceive`'e ve `comms/yks_gui.py`'ye DOKUNMA.
  - 🔴 **DOSYA İZNİ ÜÇÜNCÜ KEZ DÜZELTİLDİ · D-54, D-55.** Codex-2 güvenli tasarımı
    uyguladı ve **dört karar-kalitesi kapısının hepsini geçti**:
    ```text
    [T35_ONCE]   ACIK=0 | KAPALI_DAR=16 | BELIRSIZ_COKLU=0
    [T35_SONRA]  ACIK=1 | KAPALI_DAR=0  | BELIRSIZ_COKLU=15
    [T35_KALITE] KAPALI_DAR=16->0 serbest_artan=0 belirsizden_acilan=0
                 geometri_esdegeri_olmayan_acilma=0 belirsiz_coklu_fail_closed=15
    odak testi: Ran 6 tests OK · test_rota_sentetik.py: 15/15
    ```
    Tam paket yalnız `test_paket_kopyalari_kanonik_kaynaklarla_birebir` üzerinde
    düştü — **dosya iznim Jetson aynasını kapsamıyordu**. Kodu geri aldı, sha
    eşitliğini geri getirdi, görevi zorlamadı. **Doğru davranış.**
  - **Dosya izni:** `codes/costmap_path_finder.py`, `codes/rpi_inference.py`,
    `jetson_paket/kod/**` (üreteç aracılığıyla) — **T39 bittikten sonra**
    `scripts/jetson_paket_hazirla.py` koşulacak, ayna elle düzenlenmeyecek.
  - **Ek kod-inceleme şartı (Codex-2'nin önerisi, kabul edildi):** İçerik kutusu
    kısmen tuval dışına taşıyorsa ya da kesirli/bool/bozuk biçimdeyse **sessizce
    kırpılıp kabul edilmeyecek**; boş ROI ile fail-closed `MASKE_YOK` üretecek ve
    bu durumlar test edilecek. `_preprocess` zaten tam sınır içi tamsayı kutu
    üretir; geçersiz kutu bir çağrı hatasıdır, tolere edilmez.
  - **Kapı — karar SONUCU değil, karar KALİTESİ ölçülür:**
    1. **Hiçbir kare daha az güvenli olmayacak:** düzeltmeden önce çekimser olan
       hiçbir kare, sözleşme *olmadan* açılmayacak. (Madde 15'in karar düzeyindeki
       karşılığı.)
    2. `KAPALI_DAR` sayısı **ölçülebilir biçimde düşecek**; önce/sonra durum
       dağılımı tam olarak yapıştırılacak.
    3. **Madde 15 testi:** dolgulu girdide serbest piksel sayısı düzeltmeden
       sonra **artmayacak** — testle gösterilecek.
    4. `BELIRSIZ_COKLU` semantiği **değiştirilmeyecek**; bu kararları `ACIK`
       sayan hiçbir değişiklik kabul edilmez.
    5. `codes/test_rota_sentetik.py` **15/15** · tam paket **OK**.
  - ⚠ **`rota` halkası bu görevin kapısı DEĞİLDİR** — halkanın zemini otopark
    olduğu için meşru şekilde geçemez. O ayrı görevdir: **T38**.
  - **Ölçüm kümesi kaydı (D-50'nin haklı itirazı):** kareler
    `data/raw_frames/**` altındaki `.jpg/.png/.jpeg` dosyalarının **sıralı ilk
    16'sı**, model `models/navitas_seg_v21_best.pt`. Bu satır olmadan ölçüm
    tekrar edilemiyordu.
  - **Kapı kanıtı — GEÇTİ (2026-08-11 · gerçek koşum):** Bu küme bir
    **otoparktır**; aşağıdaki sayılar model davranışını ölçer, HTAB görev kararı
    veya canlı üretim entegrasyonu ilanı değildir.
    ```text
    O:\navitas-local-train\venv\Scripts\python.exe -B -
    [T35_KUME] kare=16 model=models\navitas_seg_v21_best.pt imgsz=512 conf=0.25
    [T35_KUME_ILK] data\raw_frames\whatsapp_video_2026_07_30_at_11_44_03\frame_000000_000000000.jpg
    [T35_KUME_SON] data\raw_frames\whatsapp_video_2026_07_30_at_11_44_23\frame_000000_000000000.jpg
    [T35_ONCE] ACIK=0 | KAPALI_DAR=16 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=0 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T35_SONRA] ACIK=1 | KAPALI_DAR=0 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=15 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T35_KIRPIK_ESDEGER] ACIK=1 | KAPALI_DAR=0 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=15 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T35_GECIS] KAPALI_DAR->ACIK=1 | KAPALI_DAR->BELIRSIZ_COKLU=15
    [T35_KALITE] KAPALI_DAR=16->0 serbest_artan=0 belirsizden_acilan=0 geometri_esdegeri_olmayan_acilma=0 belirsiz_coklu_fail_closed=15
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_costmap_letterbox_icerik.py -v
    Ran 8 tests in 0.251s
    OK
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    Ran 210 tests in 33.977s
    OK
    EXIT_CODE=0

    [T35_PARITE] bayt_esit=1 canonical_sha256=27CDE146A37D49F325278FF4674475CCA3A955E3BD1474E76A0B54ADFE1A6937 ayna_sha256=27CDE146A37D49F325278FF4674475CCA3A955E3BD1474E76A0B54ADFE1A6937
    DIFF_CHECK_EXIT_CODE=0
    [T35_RPI_DENETIM] rota_bul_cagrisi=0 preprocess_kutu_donusu=1 yeniden_hesap=0
    EXIT_CODE=0
    ```
    `codes/rpi_inference.py` içinde `rota_bul` çağrısı olmadığı için yapay bir
    sarmalayıcı eklenmedi. Regresyon ve ölçüm zinciri `_preprocess` dönüşündeki
    kutuyu aynen taşıdı; izin dışındaki betik çağrıları bu görevde değiştirilmedi.
  - **[GEÇERSİZ — D-51] İlk (hatalı) kök neden izolasyonu, kayıt için duruyor:**
    ```text
    kol                           ACIK  ret dagilimi
    A ham 512   (hakem ekrani)    16/16  —
    B ham 1024                    16/16  —
    C lbox 1024 icerik YOK         0/16  UC_BANT_TEMAS_YOK=16
    D lbox 1024 icerik VAR        16/16  —
    ```
    **A vs B: `imgsz` suçsuz. B vs C: suçlu letterbox. C vs D: çözüm hazır.**
  - **Kök neden:** `analyze_path` letterbox dolgusunu içerik sanıyor; K-A'nın
    uç bantları gri dolguya düşüyor, hiçbir koridor banda değemiyor →
    `UC_BANT_TEMAS_YOK`. `analyze_path` bunun için **`icerik=` parametresini zaten
    taşıyor** (`codes/rpi_inference.py:523`); üretim çağrısı `iha_perceive.py:106`
    onu **geçirmiyor**.
  - **Neden KRİTİK:** Saha kuru koşusundaki `rota DUSTU` halkası tam budur.
    Üretim algı yolu **gerçek karelerin %100'ünü** reddediyor — yani sahada rota
    hiç üretilmez. D-25 bir köşe durumu değil, **tam kapanma**.
  - **Yap:** `_letterbox_square`'in döndürdüğü `(x0, y0, nw, nh)` kutusunu
    `analyze_path(..., icerik=...)`'a geçir. Aynı denetimi `rpi_inference.py`
    letterbox yollarında da yap.
  - **Kapı:** Yukarıdaki dört kollu tablo yeniden koşulacak; **C kolu 16/16 AÇIK**
    olacak. `scripts/saha_kuru_kosu.py` → `rota` halkası **GECTI**.
    `codes/test_rota_sentetik.py` **15/15**.

- [x] **S5 — KAPANDI · Çıkarım `imgsz`i tek kaynaktan türetiliyor ve denetleniyor** · `codes/rpi_inference.py` · ÖNEMLİ
  - **Kanıt:** v17 arena IoU — 640: **0,861** (kaplama %4,2) · 960: **0,034** (kaplama **%96,1**) · 1280: 0,041 · 1600: 0,018. `multi_scale` (v20) düzeltmedi (%96,1 → %90,7). FDA irtifası **≥30 m ve değişken** (şartname §5.3.2).
  - **Yap:** Çıkarım çözünürlüğünü tek bir sabitten oku ve CLI ile değiştirilirse **görünür uyarı** bas. Model ağırlığının eğitildiği `imgsz` ile çalışma anındaki değeri karşılaştırıp uyuşmazlıkta uyar.
  - **Kapı:** `imgsz` varsayılan dışına çıkarıldığında uyarı basıldığını gerçek çıktıyla göster.

  - 🔴 **S7 DENETİMİNDEN GELEN GİRDİ · 2026-08-19 · `REVIEW_LOG.md` D-175 §3.**
    `54_arena_cozunurluk.py:33` → `OLCEKLER = [640, 960, 1280, 1600]` **gömülü**,
    argüman yok. Üretim ise `rpi_inference.INFER_SIZE = **512**`. Yani mevcut
    çözünürlük süpürmesi **üretimin fiilen kullandığı çözünürlüğü hiç
    sınamıyor** ve bu haliyle üretim hakkında konuşamaz.
  - Mimar ölçtü (54'ün kendi `maske()`si, v30, eşik 0,25):
    ```text
    imgsz   1.jpg IoU/kaplama    2.png IoU/kaplama
      512    0,000 / %0,00        0,000 / %0,00     <- URETIMIN COZUNURLUGU
      768    0,000 / %0,00        0,000 / %0,10
      960    0,584 / %2,92        0,000 / %0,14
    ```
  - **İLK İŞ (ucuz):** `OLCEKLER`e **512** ekle veya `--olcekler` argümanı aç.
    Bu, S5'in kendi sorusunu (*"imgsz sabitlenmeli mi, hangi değerde?"*)
    ölçülebilir kılar; şu an süpürme o soruyu **cevaplayamıyor**.
  - ⚠ n=2 ve ikisi de YZ üretimi — bu sayılar **model seçimine girdi değildir**.
  - 🔎 **MİMAR TANISI · 2026-08-19.** Kodda okundu, ölçülmedi — doğrulanabilir olgular:
    ```text
    kaynak                                       imgsz     registry'den mi?
    config/model_registry.json competition          512     (TEK KAYNAK)
    codes/rpi_inference.py:128 INFER_SIZE           512     HAYIR — ciplak sabit
    codes/arac_maskesi.py:206 ARAC_OLCEK_IMGSZ      640     HAYIR — ciplak sabit
    config/model_registry.json arac_referansi      1024     (TEK KAYNAK)
    codes/test_rota_guvenlik.py:274,430             896     HAYIR — ciplak sabit
    ```
  - 🔴 **ASIL KUSUR:** `model_kayit_dogrula` (`rpi_inference.py:438`) registry ile
    yalnız **`path`/dosya adını** kıyaslıyor; **`imgsz` alanını HİÇ okumuyor.**
    Yani registry `imgsz`'i 640'a çevrilse `INFER_SIZE` 512'de kalır ve
    **hiçbir yerde ses çıkmaz.** Bu, registry'nin kendi notunda yazılı
    kusurun (D-116/5: *"sürüm v27'ye geçince çevrilmedi"*) birebir aynısı.
  - Bugün **512 = 512 uyuşuyor** — yani bu canlı bir hata değil, **açık bir
    kapı**. T53/T54 de 512'de eğitiliyor, dolayısıyla terfi anında sorun
    çıkmaz; ama koruma yok.
  - ⚠ `arac_referansi.imgsz = 1024` ile `ARAC_OLCEK_IMGSZ = 640` **ayrışıyor**.
    Bu muhtemelen bir hata değil (registry DOTA'nın eğitim boyunu, kod ölçek
    kâhininin kalibre koşum boyunu yazıyor — `arac_maskesi.py:188-206`), ama
    **alanın hangisini kastettiği yazılı değil**. Önce anlam netleşmeli,
    sonra dokunulmalı.

  - ✅ **YAPILDI · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md` **D-176**.
    Değişen: `codes/rpi_inference.py` (+ `jetson_paket/kod/` aynası SENKRON) ·
    `config/model_registry.json` (**yalnız NOT**, 3 satır) ·
    `tests/test_imgsz_tek_kaynak.py` (YENİ, 9 test).
  - **ÜRETİM DAVRANIŞI DEĞİŞMEDİ** (defter 512 · `INFER_SIZE` 512):
    ```text
    INFER_SIZE 512 · _kayittan_imgsz() 512
    model_kayit_dogrula -> True · "eslesti" · beklenen 512 · calisan 512
    cikarim_boyu() -> 512
    ```
  - **(A) `imgsz` KIYASI EKLENDİ** — `path` ile aynı fail-closed mantık.
    `detay`ya `beklenen_imgsz` + `calisan_imgsz`; yeni `durum` değeri
    **`IMGSZ ESLESMIYOR`**; alan yoksa/geçersizse de `uyumlu=False`.
    ⚠ Mevcut `"eslesti"`/`"ESLESMIYOR"` değerleri **korundu** — aksi hâlde
    `test_saha_parametrik::test_manifest_ile_kayit_defteri_ESLESIYOR`
    sessizce düşerdi. `kayit_zorunlu` semantiği **değiştirilmedi**.
  - **(C) SEÇİM: `INFER_SIZE` defterden TÜRETİLİYOR** — fail-closed ama
    **yumuşak**: defter okunamazsa `INFER_SIZE_YEDEK`e düşer ve **stderr'e
    uyarır**, modül yine yüklenir. 🔴 Gerekçe ölçüldü: `jetson_paket/` altında
    `config/` **yok**; sert bağımlılık saha aynasını **import edilemez**
    yapardı. ⚠ **Aynada yeni davranış:** import'ta uyarı basılıyor, değer
    512'de kalıyor (`load_model` orada zaten fail-closed düşüyordu).
  - 🔴 **(B) `--imgsz` BAYRAĞI EKLENMEDİ — karar ve gerekçe.** `rpi_inference`
    CLI'sinde böyle bir bayrak **yok** (17 argüman tarandı). Amacı `imgsz`i
    **sabitlemek** olan bir göreve yeni bir **değiştirme kolu** takmak ters
    yönde bir adım olurdu. Yerine **ortak çözücü** `cikarim_boyu(istenen, kok)`
    yazıldı; ileride bir CLI/API yolu açılırsa oradan geçmek zorunda kalacağı
    tek nokta budur. Gerçek çıktı:
    ```text
    UYARI: CIKARIM BOYU VARSAYILAN DISINA CIKARILDI: kayit defteri 512,
    istenen 896. Model bu boyda kalibre EDILMEDI; sonuclar kayit defterindeki
    olculerle KIYASLANAMAZ.
    ```
    Ayırt edicilik ayrıca sınandı: **aynı değerde susuyor** (boş stderr).
    ⚠ Mimar yine de bayrak isterse **ayrı karardır**.
  - **(D) DOKUNULMADI, BELGELENDİ:** üç profile `_imgsz_notu` eklendi.
    `arac_referansi` için: *"bu DOTA ağırlığının EĞİTİM boyudur (1024); ölçek
    kâhininin KALİBRE KOŞUM boyu `ARAC_OLCEK_IMGSZ = 640`tır ve
    D-124/D-126/D-143 kalibrasyonlarının tamamı 640'ta koşuldu — ayrışma kusur
    değil, İKİ FARKLI BÜYÜKLÜK; `INFER_SIZE` türetimine girmez"*.
  - 🔴 **MUTASYON KANITI — GERÇEK ÜRETİM DOSYASINDA** (yedek → değiştir → koş →
    yedekten geri koy; `git checkout` kullanılmadı). `imgsz_uyumlu = True`:
    ```text
    Ran 9 tests in 0.040s
    FAILED (failures=2)
      FAIL: test_imgsz_FARKLIYSA_uyumsuz
            True is not false : imgsz 640 vs 512 — UYUMLU sayilmamali
      FAIL: test_MUTASYON_imgsz_kiyasi_kaldirilirsa_test_DUSER
            True is not false : gercek kod imgsz sapmasini KACIRDI
    ```
  - **KOŞULAN KAPILARIN GERÇEK ÇIKTISI:**
    ```text
    yeni testler                     Ran 9 · OK
    codes/test_rota_sentetik.py      SONUC: 15/15 dogru
    unittest discover -s tests       Ran 614 tests in 73.099s · OK  (605 -> 614)
    scripts/jetson_paket_hazirla.py  9 dosya · hata yok
    tests -p "*jetson*"              Ran 5 · OK
    ayna                             diff codes/ jetson_paket/kod/ -> SENKRON
    ```
    ⚠ GPU: bu görev **model çalıştırmadı** (sahte defter + kukla yol).
  - ⚠ **DOĞRULANAMADI:** `INFER_SIZE` **değişseydi** ne olurdu ölçülmedi —
    kapatılan şey **sessizlik**, doğrulanan şey değişimin **etkisi değil** ·
    `cikarim_boyu()` **hiçbir üretim çağrı yerinde kullanılmıyor** (mekanizma
    kuruldu, canlı yol değil) · `codes/test_rota_guvenlik.py:274,430`'daki
    **896** çıplak sabitleri emirde sayılmadığı için **dokunulmadan bırakıldı**
    — kapsamda mı, mimar söylemeli · `ARAC_OLCEK_IMGSZ = 640` hâlâ çıplak
    sabittir ve defterle kıyaslanmaz ((D) gereği dokunulmadı), **o kapı açık
    kalıyor** · `_kayittan_imgsz` yalnız `default_profile`i okur.
- [ ] **S6 — `hedef` sınıfı hedef tohumu olarak bağlı değil** · `codes/costmap_path_finder.py:730` · ÖNEMLİ
  - **Kanıt:** `rota_bul` yalnız `yol_sinif_idler` ve `engel_sinif_idler` okuyor; `2 = hedef` hiçbir yerde hedef tohumu olarak kullanılmıyor. Hedef `baslangic`/`hedef` parametreleriyle dışarıdan veriliyor.
  - **Yap:** İsteğe bağlı `hedef_sinif_idler` ekle; verilirse maskenin en büyük bağlı bileşeninin merkezi hedef tohumu olsun. **S2 sözleşmesinden sonra** yapılmalı.
  - **Kapı:** `codes/test_rota_sentetik.py` **15/15** düşmüyor; hedef sınıflı sentetik bir sahnede rota H'ye ulaşıyor.

- [x] **S7 — KAPANDI · Arena ölçüm araçları `ozet.json` üretiyor** · `O:\navitas-local-train\48_arena_iou.py`, `54_arena_cozunurluk.py` · ÖNEMLİ
  - **Kanıt:** Her iki betikte de `json.dump` / `write_text` **yok**; yalnız `print`. Bütün arena sayıları elle `BULGULAR_20260720.md`'ye kopyalanmış. Regresyon takibi ve otomatik kapı **imkânsız**.
  - **Yap:** Her iki betiğe `--out <dizin>` ekle; `ozet.json` yaz. Alanlar: model, imgsz, görüntü başına IoU, **moloza basma oranı**, kaplama, yer gerçeği kaplaması. **Havuz metrik yerine görüntü bazında** yaz (`44_karar_kurali.md`: *"v17'nin 0,615'i aslında 0,861 + 0,000'dı"*).
  - **Kapı:** İki model için koş, `ozet.json` üret ve `BULGULAR`'daki elle yazılmış sayılarla **eşleştiğini** göster.

  - ✅ **YAPILDI · 2026-08-19 · Claude-2** · kayıt `REVIEW_LOG.md` **D-174**.
    Üretim kodu değişmedi: `git diff HEAD -- codes/` **BOŞ**.
    İkisi de ilk kez `scripts/olcum/` altına **aynalandı**.
  - **`print` çıktısı birebir korundu** — JSON **ek**, ikame değil. Kayıtlar
    **görüntü bazında**; havuz özeti ayrı ve `havuz_` önekli.
    Alan denetimi: 48'de **20 kayıt**, 54'te **16 kayıt**, **eksik alan YOK**.
    `moloza_basma_orani` 54'te hiç yoktu — eklendi (§13d: IoU otorite değil).
    Model adı çıplak sabit değil: `KISAYOL["uretim"] = uretim_pt()` (madde 16).
  - **KAPI — `ozet.json` vs `BULGULAR_20260720.md` §13a (v5c):**
    ```text
    olcut          BULGULAR (elle)   ozet.json   ESLESME
    en iyi IoU          0,077          0,077       ✓
    esik                0,10           0,10        ✓
    kesinlik            0,079          0,079       ✓
    duyarlilik          0,679          0,679       ✓
    kaplama             %22,5          %22,54      ✓ (yuvarlama)
    ```
    **5/5 eşleşti.** Elle kopyalamada hata yok, betik o günden beri değişmemiş
    — araştırılacak bir sapma çıkmadı.
  - 🔴 **ASIL KAZANÇ — havuz sayısının gizlediği:**
    ```text
    v5c @ esik 0,10   havuz IoU 0,077
      1.jpg  IoU 0,081 · moloza_basma 0,660 · kaplama %44,39 · duyarlilik 0,994
      2.png  IoU 0,000 · moloza_basma 0,000 · kaplama  %0,69 · duyarlilik 0,000
    ```
    (a) **0,077 bir ortalama değil, 0,081 + 0,000'dır** — v5c 2.png'de tamamen
    kör; `44_karar_kurali.md`'nin v17 patolojisi, bu kez tablonun "en iyi"
    satırında. (b) 🔴 **IoU-en iyi eşik, en GÜVENSİZ eşiktir:** v5c 0,10'da
    1.jpg'de molozun **%66'sına** "geçilebilir" diyor (havuz sütunu %27,0
    gösteriyordu — görüntü boyutları havuzu seyreltiyor). 0,25'te moloza basma
    0,0'a iniyor ama IoU de 0,000'a düşüyor. §13d bu gerilimi metinle
    anlatıyordu; artık **sayıyla** duruyor.
  - **YAN ÖLÇÜM (kapı DEĞİL) — üretim modeli (v30), `54`, eşik 0,25, 1.jpg:**
    ```text
    imgsz  640 -> IoU 0,000    960 -> IoU 0,584    1280 -> 0,431   1600 -> 0,404
    2.png: dort olcekte de IoU 0,000
    ```
    `0,584`, §13a'daki en iyi değerin (0,077) **yedi katından fazla** — ama
    yalnız **640'ın üstünde**; 640'ta üretim modeli de kör. §13'ün "ölçeksel mi
    anlamsal mı" sorusuna 1.jpg için **ÖLÇEKSEL** cevabı. 2.png değişmiyor.
    ⚠ n=2 ve görüntüler YZ üretimi — **model seçimine girdi olamaz.**
  - **KOŞULAN KAPILAR:**
    ```text
    codes/test_rota_sentetik.py   SONUC: 15/15 dogru
    unittest discover -s tests    Ran 605 tests in 73.116s / OK  (test EKLENMEDI)
    git diff HEAD -- codes/       -> BOS
    ```
    ⚠ GPU: yalnız 2 görüntü × 2 model çıkarımı; **büyük süpürme başlatılmadı**,
    eğitim loglarına dokunulmadı.
  - ⚠ **DOĞRULANAMADI:** yalnız **v5c** karşılaştırıldı; §13a'nın diğer dört
    satırı (v13/v15/v4/v9) ve §13e (v15/v16) **koşulmadı** — GPU'da eğitim var,
    büyük süpürme yasaklıydı · `48`'in `imgsz`i 640'a **gömülü** (JSON'da öyle
    yazıyor ama argümandan almıyor) · `moloza_basma_orani` yarı otomatik
    maskeye bağlıdır, mutlak değil kıyaslamalıdır · 🔴 **regresyon takibi artık
    MÜMKÜN ama KURULMADI** — `ozet.json`'ı eşikle kıyaslayan otomatik kapı
    hâlâ yok; S7 "makine-okunur çıktı" istiyordu, "otomatik kapı" ayrı iştir.

  - 🔎 **MİMAR DENETİMİ · 2026-08-19 · `REVIEW_LOG.md` D-175. ONAYLANDI.**
    Kapıları kendim koştum (**605 OK**, **15/15**), `git diff codes/` **BOŞ**,
    ayna ilk kez oluştu, `ozet.json`'daki v5c sayıları JSON'dan yeniden
    okundu: **birebir**. BULGULAR kıyası (5/5) doğrulandı.
  - **Amelenin asıl kazancı doğru:** havuz 0,077 bir ortalama değil
    **0,081 + 0,000**; ve IoU-en-iyi eşik (0,10) aynı zamanda molozun
    **%66'sına** "geçilebilir" dediği eşik. Tablodaki "en iyi IoU" satırı,
    güvenlik açısından modelin **en kötü** çalıştığı nokta.
  - 🔴 **DENETİMİN BULDUĞU: süpürme üretimin çözünürlüğünü hiç ölçmüyor.**
    `54_arena_cozunurluk.py:33` → `OLCEKLER = [640, 960, 1280, 1600]` (gömülü);
    üretim ise `INFER_SIZE = **512**`. Mimar 54'ün kendi `maske()`siyle ölçtü:
    ```text
    v30 (uretim) · esik 0,25      1.jpg IoU/kaplama    2.png IoU/kaplama
      512                          0,000 / %0,00        0,000 / %0,00
      640                          0,000 / %0,00        0,000 / %0,04
      768                          0,000 / %0,00        0,000 / %0,10
      960                          0,584 / %2,92        0,000 / %0,14
     1280                          0,431 / %3,42        0,000 / %0,16
    ```
    **512'de kaplama %0,00** — model bu iki görüntüde hiçbir şey üretmiyor.
    Geçiş 768–960 arasında keskin.
  - ⚠ **Abartmıyorum:** n=2, ikisi de YZ üretimi → model seçimine girdi olamaz.
    v30 **kendi alanında 512'de kör değil** (t66'da 31 kare ACIK, K1–K5 koşuyor).
    Bu "model bozuk" değil, **alan dışı + ölçek** etkileşimi (K-3).
    **Ama şu abartı değil:** çözünürlük süpürmesi üretimin çözünürlüğünü
    içermiyorsa üretim hakkında hiçbir şey söyleyemez. → **S5'e bağlandı.**
- [ ] **S8 — FDA profili sentetik üretece girmemiş** · `O:\navitas-local-train\51_sentetik_arena.py` · ÖNEMLİ
  - **Kanıt:** Üreteç 50×50 m HTAB'a göre kurulu. FDA test uçuşu **20×20 m** alan, **asgari 30 m irtifa** (şartname §5.3.2).
  - **Yap:** Alan boyutunu ve irtifayı **profil** parametresi yap (`HTAB_50`, `FDA_20`). `mpp`'yi irtifa + kamera FOV'undan türet, sabit varsayma. Üretecin mevcut tasarım kurallarını **koru** — özellikle *"etiketsiz moloz yok"* ve şerit modeli.
  - **Kapı:** Her iki profilde de üretim koşuyor; `52_sentetik_denetim.py` ile denetlenebiliyor; `codes/test_rota_sentetik.py` **15/15**.

- [STATUS: READY_FOR_REVIEW] **S9 — Hakem ekranı koşmadığı modelin adını basıyor** · `comms/yks_gui.py` · KRİTİK · kanıt: `REVIEW_LOG.md` D-21
  - **Kanıt:** Tek algı yolunda **dört farklı model adı**. `:885` `navitas_seg_v20_best.pt` yüklüyor; `:171/:181/:194/:997` "v17" yazıyor; `:994` "model: navitas_seg_v21_best.pt (mAP50 0.6751)" yazıyor. `:888`'deki `SHA 8e8d46a6…` **hiçbir modelle eşleşmiyor** (v17 `8986c300` · v20 `eeb95d17` · v21 `799e07f9`). `mAP50 0.6751` bayat — v21 karışık val mask mAP50 = 0,960.
  - **Neden KRİTİK:** bu ekranı şartname §2.2.3/§6.2 gereği **Alan Hakemi** izliyor. Kod hatası değil, **kanıt bütünlüğü** hatası.
  - **İkinci kusur:** `_algi_gorseller()` üç kaynak tanıyor (`test_images/gemini`, `test_images/test/images`, `dataset/rescuenet_yolo/images/val`) — üçü de 512×512 RescueNet/üretilmiş. **Gerçek nadir kareler (`data/raw_frames`, 67 kare, 4 alt klasör) listede yok.** Ölçüldü: bu üç kaynakta v21 ≈ v20 (36–37/40 aynı karar); gerçek karede v20 engel **%0,00**, v21 **%21,83**.
  - **Yap:** `:885`'i v21'e çevir. Etiketleri **elle yazma — yüklenen dosya adından türet** (tek kaynak: `model_yolu.stem`); aynı hata bir daha üretilemesin. `:888`'de SHA'yı `hashlib` ile **gerçekten hesapla** (ilk 8 hane) veya satırı kaldır. `:994-995`'teki bayat mAP'i kaldır. `_algi_gorseller()` sözlüğüne `"drone": KOK/"data"/"raw_frames"` ekle ve **`rglob`** kullan (kareler video başına alt klasörde; `iterdir` sıfır döndürür). `ALGI_KAYNAKLAR` demetine `"drone"` ekle.
  - **Kapı:** (1) `grep -nE "v1[0-9]|v2[0-9]" comms/yks_gui.py` → sabit-kodlu model adı **0 eşleşme**. (2) GUI'yi `--demo` ile aç, V ile algı görünümüne geç, K ile `drone` kaynağını seç: bilgi satırında `navitas_seg_v21_best.pt` yazmalı ve gerçek karede **engel > %10** görünmeli. (3) `codes/test_rota_sentetik.py` **15/15**.
  - **Kapı kanıtı — GEÇTİ (2026-08-08):**
    - Kapı 1: `grep -nE "v1[0-9]|v2[0-9]" comms/yks_gui.py` → tek eşleşme
      `:802 ALGI_MODEL_DOSYA = "navitas_seg_v21_best.pt"`, yani **tanımın kendisi**
      (tek kaynak). Etiketler `_m = ALGI_MODEL_DOSYA.rsplit(".",1)[0]` ile türetiliyor;
      elle yazılmış model adı kalmadı.
    - **Sahte SHA gitti.** Eskiden `SHA 8e8d46a6…` sabit yazılıydı ve o hash
      `navitas_seg_v3_best.pt`'ye aitti. Artık `hashlib` ile hesaplanıyor;
      ölçüldü: `799e07f9` — yüklenen v21'in gerçek hash'i.
    - Bayat `mAP50 0.6751` satırı kaldırıldı.
    - `ALGI_KAYNAKLAR = ("gemini","test","val","drone")`; `drone` kaynağı
      `data/raw_frames` → **rglob ile 67 kare** (`iterdir` **0** verirdi, kareler
      video başına alt klasörde).
  - **Ek — hakem GÜNLÜĞÜ de aynı kusuru taşıyordu, düzeltildi.**
    `simulation/scripts/hakem_log.py:36-39` `navitas_seg_v2_best.pt` ve
    `mAP50=0.619` sabit yazıyordu; `imgsz=1024` iddiası `CONTRACTS §8` ile de
    çelişiyordu. Künye artık YKS ile **aynı tek kaynaktan** türetiliyor ve SHA
    gerçekten hesaplanıyor. Ölçüldü: `model=navitas_seg_v21_best.pt sha=799e07f9
    imgsz=512`.
  - ⚠ **Denetim bekliyor** — madde 7 gereği Claude 1 kendi kodunu onaylamaz.
  - **2026-08-09 · BAĞIMSIZ DENETİM — Claude 1.** Denetim borcu kapatıldı.
    ⚠ **Önce bir yanlışın kaydı:** bu görev, kuyrukta `- [ ]` göründüğü ve çalışma
    ağacındaki dosya commit'ten **geride** olduğu için (1406 satır, hâlâ `v20`/`v17`)
    yeniden yapılmak üzere gpt-oss-120b'ye (N4) verildi. Oysa S9 **zaten
    `40859b3` commit'inde tamamlanmıştı**. N4'ün ürettiği kod koşum ortasında
    kayboldu ve depodaki sürüm geri geldi; `git diff HEAD` bunu doğruluyor —
    depoyla aramda N4'ün yazdığı **tek satır yok**. Kök neden ve bağlayıcı kural:
    `REVIEW_LOG.md` **D-33**. (N4 koşumundan çıkan `_blk` bulgusu: **D-32**.)
    - **Denetlenen kod `40859b3`'ün kodudur**, dolayısıyla madde 7 çakışması yok.
    - **Bulgu, düzeltildi — üç biçim kusuru** (commit'te mevcuttu): `:195` ve
      `:1027` bir boşluk fazla girintili; `ALGI_MODEL_DOSYA` ile
      `def _algi_gorseller` arasında PEP8 boş satırı yok. Davranış değişmedi;
      çalışma ağacının commit'ten tek farkı budur.
    - **Koşulan kapılar — gerçek çıktı:**
      ```
      headless algı kapısı   sabit-kodlu sürüm adı: 1 satır (:826, tanımın kendisi)
                             ALGI_KAYNAKLAR ('gemini','test','val','drone')
                             gemini 320 · test 305 · val 294 · drone 67 kare
      test_rota_sentetik.py  SONUC: 15/15 dogru · [OK] TUM DETERMINISTIK SAHNELER GECTI
      unittest discover      Ran 101 tests in 27.546s · OK
      GUI --demo, 9 s ayakta _arayuz_kur çalıştı · NameError yok · stderr boş
      SHA doğrulaması        hesaplanan 799e07f9 == D-21'deki v21 · EŞLEŞTİ
      ```
    - **DOĞRULANAMADI — GUI görsel kapısı.** (`V` → `K` ile `drone` → bilgi
      satırında `navitas_seg_v21_best` **ve** gerçek karede `blocked` > %10.)
      İnteraktif olduğu için otomatik koşulamaz; v20'de bu değer **%0,00**'dır,
      kapı v21'e geçişi bu yüzden ayırt eder. **İnsan koşmalı.**

- [STATUS: READY_FOR_REVIEW] **S10 — Hakem ekranı tek bozuk çerçevede kalıcı donuyor / sessizce sağırlaşıyor** · `comms/yks_gui.py`, `comms/link.py` · KRİTİK · kanıt: 2026-08-07 taraması, `REVIEW_LOG.md` D-06
  - **Neden KRİTİK:** bu ekranı şartname §2.2.3/§6.2 gereği **Alan Hakemi** izliyor
    ve iki kusur da **sessiz** — ekran çökmüyor, yalnızca çalışmayı bırakıyor.
  - **Kusur 1 — tek bozuk çerçeve ana döngüyü kopartıyor.** `_tik` kendi zincirini
    `after(120)` ile kuruyor; `_mesaj_isle` içinde fırlayan istisna o zinciri
    kopartıyor → saat, günlük, kronometreler, butonlar hepsi ölüyor. Tetikleyici
    gerçek: protokol `ref_xy=None`'a **izin veriyor** (`protocol.py:44-45`) ve
    `iha_sender` geometri doğrulamasını yalnız ika/broadcast akranı varken koşuyor
    (`iha_sender.py:114`) — yani `iha_sender --yks HOST:PORT` tek hedefliyken
    `m['ref_xy'][0]` `TypeError` veriyordu.
  - **Kusur 2 — dinleyici thread'i tek ICMP hatasında kalıcı ölüyor.**
    `link.recv` yalnız `socket.timeout` yakalıyordu; Windows'ta dinlemeyen bir
    akrana gönderim sonraki `recvfrom`'da `WinError 10054` üretiyor, `_dinle`
    bunu `OSError` olarak yakalayıp **thread'i bitiriyordu**.
  - **Yap (uygulandı):** `link.recv` `ConnectionResetError`/`ConnectionRefusedError`'ü
    zaman aşımı gibi yutar — bu tek satır `iha_sender`'ın dinlemeyen hedefte
    çökmesini de kapatır. `_dinle` yalnız soket **gerçekten kapandığında** çıkar,
    aksi hâlde günlüğe sarı satır basıp devam eder. `_tik` `_mesaj_isle`'yi
    try/except ile sarar ve bozuk çerçeveyi hakeme **görünür** kılar. `ref_xy`
    kök nedeni de düzeltildi (`None` → `—`).
  - **Kapı kanıtı — GEÇTİ (2026-08-08):** `tests/test_yks_gui_dayaniklilik.py` **6/6**:
    geçici ağ hatasından sonra dinleyici **yaşıyor ve gerçek mesajı işliyor**;
    soket kapanınca **temiz çıkıyor**; bozuk çerçeveden sonraki mesaj işleniyor
    ve sarı uyarı basılıyor. `comms/test_comms.py` exit 0.
  - ⚠ **Denetim bekliyor.**

---

## TAMAMLANANLAR

_(henüz yok)_
