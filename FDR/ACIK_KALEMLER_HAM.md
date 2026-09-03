# FDR — AÇIK KALEMLER (ham çıkarım)

> `FDR/BOLUM_*.md` içinde **BEYAN GEREKLİ** ya da **ÖLÇÜLEMEDİ** geçen her
> satır. Bu dosya ELLE yazılmaz; `scripts/fdr_acik_kalem_cikar.py` ile
> çıkarılır ve bölümler değiştikçe yeniden üretilir.
> Derlenmiş hâli: `FDR/ACIK_KALEMLER.md`.

## BOLUM_1_OZET.md  (8 satır)
- `:97` sunulmaz; saha `p` değeri **ÖLÇÜLEMEDİ** olarak durur ve iki çerçevenin (sentetik
- `:152` 2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Koşulmamış kapı "sorun çıkmadı" diye yazılmaz; paydası olmayan oran rapora girmez.
- `:187` BEYAN GEREKLİ (insan)
- `:189` BEYAN GEREKLİ (insan):** Takım adı, takım numarası, kategori ve üniversite/kurum künyesi — bu bölümün başına eklenecek.
- `:190` BEYAN GEREKLİ (insan):** Gerçek kütleler (İHA, İKA, yük) — 5 Eylül tartı listesi.
- `:191` BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen kare hızı ve `torch.cuda.is_available()` sonucu.
- `:192` BEYAN GEREKLİ (insan):** RPi HQ kamera gerçek yatay görüş açısı (`kamera_dogrula` ölçümü); rapordaki 55–63° aralığı lens beyanından türetilmiş **tahmindir**.
- `:193` BEYAN GEREKLİ (insan):** Gerçek SiK 433 MHz hattında gidiş-dönüş süresi ve paket kayıp oranı.

## BOLUM_2_ORGANIZASYON_VE_TAKVIM.md  (13 satır)
- `:10` "geçmedi" diye yazılır (§4.4). Henüz atanmamış insan görevleri **BEYAN GEREKLİ (insan)**
- `:54` BEYAN GEREKLİ (insan): rol → isim ataması.** Bu tablo bilerek isimsizdir. Kaptan, sekiz rolü
- `:57` BEYAN GEREKLİ (insan): şartname §4 kontenjan ve oran kontrolü** — toplam üye sayısının 6–10
- `:59` BEYAN GEREKLİ (insan): danışman öğretim üyesi bilgisi.**
- `:85` 2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora girmez.
- `:205` Hızlandırma | TensorRT `.engine` (Jetson'da derlenir) | **Nano'da ÖLÇÜLEMEDİ** — venv38'de `tensorrt` modülü yok (JetPack 4.6 bağı Py3.6). PT/ONNX ile uçulur | `jetson_paket/JETSON_NANO_KURULUM.md` §0 |
- `:324` BEYAN GEREKLİ (insan) — bu bölümde kapatılacak boşluklar
- `:326` 1. **BEYAN GEREKLİ (insan): rol → isim ataması** (8 rol; ad-soyad, öğrenim düzeyi, yedek rol).
- `:327` 2. **BEYAN GEREKLİ (insan): takım üye sayısı ve şartname §4 oran kontrolü** (6–10 kişi; lisansüstü oranı).
- `:328` 3. **BEYAN GEREKLİ (insan): danışman öğretim üyesi** bilgisi.
- `:329` 4. **BEYAN GEREKLİ (insan): takım künyesinin KYS teyidi** (ID 997827 / başvuru 5329027).
- `:330` 5. **BEYAN GEREKLİ (insan): 5 Eylül kutu açılış teyidi** — §4.1'deki gerçek künye satırlarının
- `:332` 6. **BEYAN GEREKLİ (insan): 21 Eylül Adıyaman uçuş alanı izni** ve alan koordinatları.

## BOLUM_3_SISTEM_SPESIFIKASYONLARI.md  (25 satır)
- `:18` Ölçülmeyen "ölçülemedi"dir** | Ölçülmemiş hiçbir büyüklük "sorun çıkmadı" diye yazılmaz. `ÖLÇÜLEMEDİ ≠ GEÇTİ` bu projede bir slogan değil, kabul denetçisinin kod satırıdır: alt betik çökerse kapı `OLCULEMEDI` döner ve terfiyi **bloklar** (`scripts/olcum/65_kabul_denetcisi.py:456, 608, 636, 664`). |
- `:21` Emin olunmayan "DOĞRULANACAK"tır** | Kutudan çıkmamış donanımın hiçbir değeri ölçüm gibi sunulmaz; **BEYAN GEREKLİ (insan)** satırı bırakılır (§3.10). |
- `:213` BEYAN GEREKLİ (insan):** Sabit kanat İHA gövdesi, mancınık, paraşüt podu ve İKA şasisinin
- `:227` kalkış kütlesi (gerçek tartı) | **ÖLÇÜLEMEDİ** — 5 Eylül §2.1: her parça tartılır ve fotoğraflanır |
- `:228` ağırlık merkezi | **ÖLÇÜLEMEDİ** — 5 Eylül §2.2, ölçüt CG ± 1 cm |
- `:229` titreşim (`VIBE`) | **ÖLÇÜLEMEDİ** — ölçüt uçuşta `VIBE` < 30 |
- `:230` pusula ofseti | **ÖLÇÜLEMEDİ** — ölçüt < 300 |
- `:231` itki / asılı kalma akımı | **ÖLÇÜLEMEDİ** — PM02 telemetrisiyle ölçülecek |
- `:232` uçuş süresi (4S 10 Ah ile) | **ÖLÇÜLEMEDİ** — hesap yapılmadı, tahmin yazılmaz |
- `:298` koşulacaktır (`FAZ_B_GUN_PLANI.md` §1). `ÖLÇÜLEMEDİ ≠ GEÇTİ`.
- `:319` ÖLÇÜLEMEDİ** — bu sayılar seri köprü ölçümüdür, RF ölçümü değildir.
- `:815` BEYAN GEREKLİ (insan):** Arena benzeri gerçek saha görüntüsü (kırmızı H brandası + moloz +
- `:917` ⚠ Gazebo **fiziksel temas** koşusu geliştirme makinesinde **ÖLÇÜLEMEDİ** (gz yok);
- `:918` Gazebo'lu makinede koşulacaktır. `ÖLÇÜLEMEDİ ≠ GEÇTİ`.
- `:1022` `.engine` bu kart için **ÖLÇÜLEMEDİ** sayılır; **PT/ONNX ile uçulur.**
- `:1095` Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena görüntüsü yoktur. İki sayı alt/üst çerçevedir;
- `:1187` 3.8.4 🔴 ÖLÇÜLEMEDİ — haberleşmede kapatılmamış sayılar
- `:1191` Gerçek SiK 433 MHz RF üzerinde RTT / paket kaybı** | **ÖLÇÜLEMEDİ.** Araç `scripts/sik_rf_olc.py` **yazıldı** (`--rol yanki` / `--rol olc --n 50`), hedef **RTT p95 < 0,20 s**; radyolar kutudadır, koşum 5 Eylül'dedir. `results/` altında ölçüm dosyası **yoktur.** |
- `:1192` Menzil** | **ÖLÇÜLEMEDİ.** DDR'deki *">%98, 300 m"* iddiasının repoda kanıtı **yoktur** |
- `:1194` Gerçek kamera yakalama gecikmesi** | **ÖLÇÜLEMEDİ** (CSI köprüsü Nano'da koşulmadı) |
- `:1233` 3.10 Bilinen açıklar, denetim borçları ve BEYAN GEREKLİ satırları
- `:1240` A2 | **Gazebo fiziksel temas koşusu** (§7.3 İKA yarısı) | Geliştirme makinesinde `gz` yok — **ÖLÇÜLEMEDİ** |
- `:1241` A3 | **TensorRT `.engine` denkliği** | Nano venv38'de `tensorrt` modülü yok; `.engine` bu kart için **ÖLÇÜLEMEDİ** |
- `:1246` 3.10.2 BEYAN GEREKLİ (insan) — bu bölüme eklenecek ölçümler
- `:1294` 2. **`ÖLÇÜLEMEDİ ≠ GEÇTİ`.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora

## BOLUM_4_TEST_FAALIYETLERI.md  (10 satır)
- `:194` 2 | `ÖLÇÜLEMEDİ ≠ GEÇTİ` | §6 Kalan test borcu |
- `:356` ⚠ **K5 alt ölçümü ÖLÇÜLEMEDİ:** `K5_figur_bilgi_px = null`,
- `:452` `1 / (5 × 0,326) = 0,61 FPS`. **Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena
- `:731` 6.4 BEYAN GEREKLİ (insan)
- `:733` 1. **BEYAN GEREKLİ (insan):** 5 Eylül kutu açılışında donanım künyesinin fiziksel
- `:736` 2. **BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen p50/p95 FPS değerleri
- `:738` 3. **BEYAN GEREKLİ (insan):** SiK 433 MHz çift üzerinde ölçülen RTT p50/p95,
- `:740` 4. **BEYAN GEREKLİ (insan):** 6–19 Eylül uçuş testlerinin her biri için tarih,
- `:742` 5. **BEYAN GEREKLİ (insan):** 21 Eylül Adıyaman uçuş alanı izni ve alan
- `:744` 6. **BEYAN GEREKLİ (insan):** sürüm mührünün basıldığı tarih ve künye commit'i

## BOLUM_5_URETIM_FAALIYETLERI.md  (46 satır)
- `:6` Ölçülmemiş hiçbir üretim değeri tahmin edilmemiştir**; ölçülmemiş olan "ÖLÇÜLEMEDİ" ya da
- `:7` BEYAN GEREKLİ (insan)** diye yazılmıştır. Beyan ile artefaktın çeliştiği iki yer vardır
- `:51` BEYAN GEREKLİ (insan): tasarımın takım üyelerince özgün olarak modellendiğine dair imzalı
- `:82` destekler, ancak nihai teyit CAD'den yapılmalıdır → **BEYAN GEREKLİ (insan): CAD birim ve ölçek teyidi**.
- `:84` BEYAN GEREKLİ (insan): CAD model kütlesi** (parça başına, g) — SGGS §5.4 bunu açıkça ister ve
- `:124` BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı** — üretilmiş fiziksel kolların
- `:138` BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi** (makara etiketi /
- `:160` BEYAN GEREKLİ (insan): bu uyarının basımda nasıl ele alındığı** (tabla sıcaklığı düşürüldü mü,
- `:163` Diğer yedi plakanın baskı süresi ve filament tüketimi ÖLÇÜLEMEDİ** — bu plakaların
- `:166` BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** — Bambu Studio'da her
- `:181` BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (ısı dayanımı, kırılganlık, saha
- `:192` CAD model kütlesi (parça başına) | **BEYAN GEREKLİ (insan)** — depoda hesaplanmış değer yok |
- `:193` Üretim/teslim sonrası **ölçülen gerçek kütle** | **BEYAN GEREKLİ (insan)** — 5 Eylül envanterinde her parça tartılacak (`SAHA_HAZIRLIK_PLANI` §2.1) |
- `:194` Boyutsal tolerans / uyum ölçümü | **BEYAN GEREKLİ (insan)** — motor delik aralığı, kol geçmesi, dome oturması |
- `:195` İlave fikstür / tool ihtiyacı | **BEYAN GEREKLİ (insan)** — destek kullanılan üç plaka (kubbe, ayak, GPS tutucu) dışında kayıt yok |
- `:196` Karşılaşılan üretim zorlukları | Kısmen ölçüldü: tabla sıcaklığı uyarısı (§4.4); gerisi **BEYAN GEREKLİ (insan)** |
- `:197` Toplam basılan parça sayısı ve fire | **BEYAN GEREKLİ (insan)** — yeniden basım / atık kaydı yok |
- `:198` Montaj bağlantı elemanları (vida, somun, pul) dökümü | **BEYAN GEREKLİ (insan)** — BOM'da sarf kalemi olarak yer almalı (Bölüm 7) |
- `:256` BEYAN GEREKLİ (insan): gerçek kablo kesitleri ve konnektör tipleri** (5 Eylül'de kullanılan
- `:292` BEYAN GEREKLİ (insan): uçuş alanı gerçek koordinatları ve geofence poligonu.**
- `:331` TensorRT `.engine` bu kartta ÖLÇÜLEMEDİ sayılır**: `venv38` içinde `tensorrt` modülü yoktur
- `:415` provada tutulacaktır (`SAHA_HAZIRLIK_PLANI` §2.6). Bugün için **ÖLÇÜLEMEDİ**.
- `:469` ÖLÇÜLEMEDİ**. Sayısal sonuçlar Bölüm 3'e girecekse, çalışmalar yeniden çözülüp
- `:471` BEYAN GEREKLİ (insan): FEM yük durumu, mesnet tanımı, malzeme kartı ve sonuç değerleri.**
- `:486` FPS kapısı ≥ 0,61** | Nano'da gerçek çıkarım hızı | **ÖLÇÜLEMEDİ** — 5 Eylül |
- `:487` Kamera FOV** | ölçek zincirinin girdisi | **ÖLÇÜLEMEDİ** — 5 Eylül |
- `:488` thazırlık ≤ 900 s** | saha kurulum süresi | **ÖLÇÜLEMEDİ** — 5 Eylül |
- `:489` Gerçek kütle / CG** | UHDR ve ağırlık limiti | **ÖLÇÜLEMEDİ** — 5 Eylül |
- `:490` FEM sonucu** | yapısal emniyet | **ÖLÇÜLEMEDİ** (§10.4) |
- `:491` `.engine` (TensorRT)** | hızlandırma | **ÖLÇÜLEMEDİ** — Nano'da derlenemiyor (§8.3) |
- `:507` BEYAN GEREKLİ (insan): final aracı üretim takvimi ve atölye/tezgâh kaynakları** — 21 Eylül
- `:512` 12. Bu bölümdeki BEYAN GEREKLİ (insan) satırlarının toplu listesi
- `:514` 1. **BEYAN GEREKLİ (insan): tasarımın özgünlüğüne dair imzalı beyan** (§2).
- `:515` 2. **BEYAN GEREKLİ (insan): CAD birim/ölçek teyidi ve kolun gerçek boyu** (§3).
- `:516` 3. **BEYAN GEREKLİ (insan): parça başına CAD model kütlesi** (§3, §5).
- `:517` 4. **BEYAN GEREKLİ (insan): dört kolun hangi reçeteyle basıldığı; kol 1–2 yeniden basılacak mı** (§4.2).
- `:518` 5. **BEYAN GEREKLİ (insan): basılan parçaların gerçek filament cinsi (ABS mi ABS-CF mi)** (§4.3).
- `:519` 6. **BEYAN GEREKLİ (insan): tabla sıcaklığı uyarısının nasıl ele alındığı ve çarpılma gözlemi** (§4.4).
- `:520` 7. **BEYAN GEREKLİ (insan): plaka başına baskı süresi ve filament kütlesi** (§4.4) — yalnız üst çerçevenin verisi var.
- `:521` 8. **BEYAN GEREKLİ (insan): PLA→ABS geçişinin gerekçesi** (§4.5).
- `:522` 9. **BEYAN GEREKLİ (insan): ölçülen gerçek kütleler, tolerans/uyum ölçümleri, fikstür ihtiyacı, fire kaydı** (§5).
- `:523` 10. **BEYAN GEREKLİ (insan): bağlantı elemanı (vida/somun/pul) dökümü** (§5).
- `:524` 11. **BEYAN GEREKLİ (insan): gerçek kablo kesitleri, konnektörler ve ölçülmüş akımlar** (§6.4).
- `:525` 12. **BEYAN GEREKLİ (insan): uçuş alanı koordinatları ve geofence poligonu** (§7).
- `:526` 13. **BEYAN GEREKLİ (insan): FEM yük/mesnet/malzeme tanımı ve sonuç değerleri** (§10.4).
- `:527` 14. **BEYAN GEREKLİ (insan): final aracı üretim takvimi ve kaynakları** (§11).

## BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md  (24 satır)
- `:22` ÖLÇÜLEMEDİ** | Hüküm repo dışındadır (uçuş kontrolcüsü, gerçek telsiz, gerçek arena) ya da ölçüm için gereken donanım/veri henüz yoktur. **ÖLÇÜLEMEDİ, GEÇTİ demek değildir.** | ölçüm tarihi + neyin eksik olduğu |
- `:60` §2.2.2** (R2) | "Fırlatma sonrası İHA, tam otonom uçuş moduna geçerek… uçuşunu gerçekleştirecektir" | Uçuş kontrolcüsü: ArduCopter/ArduPlane. Repoda **parametre ve görev şablonu** olarak izlenir: `config/pixhawk/arducopter_fda.param` (31 parametre, her satırda gerekçe), `config/pixhawk/fda_gorev.waypoints` (QGC WPL 110: TAKEOFF 32 m → tek pas → LOITER 60 s → LAND) | `tests/test_faz_b_pixhawk_sablon.py` (12 test — dosya biçimi, kare geometrisi, süre bütçesi kilitli). **Gerçek uçuşta AUTO kipi hiç koşmadı** | **ÖLÇÜLEMEDİ** (şablon KANITLI_TEST) |
- `:68` §2.2.4** (R9) | "Paraşüt açma komutu otonom… manuel tetikleme ile de… manuel ise ceza" | Yazılım yarısı: YKS iki adımlı teyit → ACK'li tekrar → İHA'da `comms/iha_komut_alici.py` komutu Pixhawk'a `COMMAND_LONG` ile aktarır ve **yalnız aktarım başarılıysa** ACK döner. Ceza −50 kaydı YKS'de | `tests/test_faz_b_iha_komut_alici.py` (22 test), `tests/test_p9abc_yks.py` (13), `tests/test_yks_gui_komut_durustlugu.py` (6). **Otonom tetik** (`CHUTE_*` parametreleri, mekanik açma) repo dışıdır ve **hiç ölçülmedi** | **KANITLI_TEST** (manuel zincir) · **ÖLÇÜLEMEDİ** (otonom) |
- `:73` §2.2.6** (R13) | "İKA'nın… **HB sınırları içerisine** girmesi ile görev başarılı" — hedef = 2×2 m kırmızı H | HB dedektörü **üretime bağlandı**: üç üretim çağrısı `analyze_path(goruntu=…)` geçiyor; iç HB çağrısı **ölçek + şekil** çifti kullanıyor (`HB_SEKIL_ESIGI`; mpp yoksa açılmaz). Rotanın son waypoint'i HB pedinin kutusunda biter | `tests/test_t150_baglama.py` (6 nöbetçi), `tests/test_t198_hb_sekil.py` (14), `tests/test_hb_dedektoru.py` (25). Bağlama ölçümü: hedef **253/256** doğru pedde, ped örtülüyken **259/260 HEDEF_YOK** (fail-closed), maliyet **sıfır** (p eşit: 0,9846). Ham çıktı `results/t150/baglama_olcumu_20260901.json` | **KANITLI_TEST** ⚠ sentetik; gerçek pedde ÖLÇÜLEMEDİ |
- `:74` §2.2.6** (R13-ek) | Varış = **brandaya temas**, sınıra girmek değil | `simulation/scripts/ika_nav.py` son waypoint'te `FINAL_WP_RADIUS = 0,3 m`; bağlayıcı eşitsizlik `FINAL_WP_RADIUS < HB_KENAR_M/2` (1,0 m) → araç merkezi ped kenarından ≥ 0,7 m içeride durur. `CONTRACTS.md §7.3` | `tests/test_p9e_branda_temas.py` (5 test: geometri + kinematik + mutasyon). ⚠ Gazebo'lu **fiziksel temas** koşusu bu makinede ÖLÇÜLEMEZ (gz yok) | **KANITLI_TEST** (geometri) · **ÖLÇÜLEMEDİ** (fiziksel) |
- `:85` §5.3.2** | "20×20 metre boyutlarındaki simüle edilmiş test alanı" tek karede görülmeli | RPi HQ standart 6 mm lens, yatay FOV ≈ 55–63° → 30 m'de kare genişliği ≈ 31–37 m. `--fov` **beyan değil ölçüm** olacak: `kamera_dogrula` ile 5 Eylül'de ölçülür | Hesap ve gerekçe `SAHA_HAZIRLIK_PLANI_20260903.md §0.2`; çözünürlük sözleşmesi `CONTRACTS.md §8`, kilit `tests/test_t163_cozunurluk_sozlesmesi.py` | **ÖLÇÜLEMEDİ** (5 Eylül'de ölçülür) |
- `:86` §5.3.2** | "uçuş esnasında **gerçek zamanlı** olarak YKİ'ye aktarmak" | `KararYayinci` (R4) + tazelik damgası + `karar_yas` (R5-ek) | **Uçtan uca kare gecikmesi ölçüldü**: 33 ölçülen gerçek karede (+3 ısınma karesi, yüzdeliklere katılmaz), üretim zinciri + gerçek telsiz halkası (UDP loopback ACK) → **p50 **0,085 s** · p95 0,113 s**, tazelik penceresinin (5 s) çok altında. Adım kırılımı ve ham veri `results/fda_butce/olcum_20260901.json`; nöbetçi `tests/test_b2_fda_butcesi.py` (13). ⚠ **Seri (SiK) hat ÖLÇÜLEMEDİ** | **KANITLI_TEST** (UDP) |
- `:87` §5.3.2** | Gereken **kare hızı** — hakem onayı için tespit taze olmalı | Eşik **türetildi, tahmin edilmedi**: `GEREKLİ_FPS ≥ 1 / (5 · p)`, `p` = bir karenin geçerli rota yayınlama olasılığı | Sentetik arena `p = 0,9846` → 0,203 FPS; gerçek DJİ (sızıntısız, n=243) `p = 0,3457` → 0,579 FPS; en kötü uçuş 0,61 FPS. Ham çıktı `results/b4_fps/p_ve_kosu_20260901.json`; nöbetçi `tests/test_163_b4_olcum_nobetcisi.py` (13). **Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena karesi yok | **KANITLI_TEST** (iki çerçeve) · saha değeri **ÖLÇÜLEMEDİ** |
- `:89` §5.3.2** | "tüm operasyon sürecinin (kalkış, tespit, veri aktarımı ve iniş) **maksimum 10 dakika**" | `codes/karar_sozlesmesi.py::SARTNAME_FDA_OPERASYON_SURESI_S = 600`; YKS `--fda` kipinde bütçe 900 yerine 600 s | `tests/test_t170_fda_sure_butcesi.py` (16 test), `tests/test_b2_fda_butcesi.py` (13). Görev planı kötü-durum süre bütçesi **221,5 s ≤ 600 s** (`config/pixhawk/README.md`). ⚠ *"600 saniyeye sığar"* hükmü **bilerek verilmedi**: uçuş, kamera yakalama ve seri hat ölçülemedi ve toplama **0 olarak girmedi** | **KANITLI_TEST** (yazılım payı) · uçuş **ÖLÇÜLEMEDİ** |
- `:103` §6.2 / §6.4** | "İHA-UB sınırları içinde icra etmeli; dışına taşan uçuşlar **Alan İhlali**" (300×300 m) | `SARTNAME_IHA_UB_KENAR_M = 300,0`, `iha_ub_ihlali(x, y)`. Üretimde `--ub-referans LAT,LON` ile her HEARTBEAT yerel `x,y` taşır; konum **aynı telemetri okuyucusundan** gelir, ikinci yol açılmaz | `tests/test_t162_alan_ihlali.py` (19 test; üretim döngüsü gerçekten koşuluyor). ⚠ Bu kapı **sahada ölüydü**: GUI denetimi vardı ama üretimde `x,y` üreten yol **yoktu** (D-307). Geofence'in kendisi Pixhawk parametresidir: `FENCE_ENABLE=1`, `FENCE_ALT_MAX 50` (`config/pixhawk/arducopter_fda.param`) — **gerçek donanımda doğrulanmadı** | **KANITLI_TEST** (yazılım) · **ÖLÇÜLEMEDİ** (geofence) |
- `:145` A9** | §2.2.6 / §7 | **Gazebo fiziksel temas koşusu ÖLÇÜLEMEDİ** (bu geliştirme makinesinde `gz` yok) | 2026-09-02 (D-391) | Ortam eksik | Gazebo'lu makinede prova koşusu |
- `:207` R17 (alan ihlali ölçülemedi) | ÖLÇÜLEMEDİ | **yazılım tarafı KAPANDI** 2026-08-27 | D-307, `tests/test_t162_alan_ihlali.py` |
- `:222` Ve tersinden: **ÖLÇÜLEMEDİ ≠ GEÇTİ.** FDA süre bütçesi ölçümünde *"600 saniyeye
- `:225` test kilitler: ÖLÇÜLEMEDİ listesi boşsa test düşer.
- `:237` ÖLÇÜLEMEDİ** | 2 | %4,4 |
- `:242` 1. **Sayımda satırın *baskın* durumu alınmıştır.** Birçok satır iki yön taşır — §2.2.4'ün manuel paraşüt zinciri KANITLI_TEST, otonom tetiği ÖLÇÜLEMEDİ; §6.2 alan ihlalinin yazılım yarısı KANITLI_TEST, Pixhawk geofence'i ÖLÇÜLEMEDİ. İkinci yön her satırın kendi hücresinde yazılıdır ve bu sayım onu gizlemez.
- `:295` BEYAN GEREKLİ (insan)
- `:300` BEYAN GEREKLİ (insan):** Gerçek SiK 433 MHz çiftinde OPEN_ROUTE/IKA_GO/IHA_LANDED tur süresi (RTT p50/p95) ve paket kayıp oranı — `scripts/sik_rf_olc.py`, 5 Eylül. DDR'deki ">%98 teslim, 300 m" iddiasının bugün **kanıtı yoktur**.
- `:301` BEYAN GEREKLİ (insan):** Jetson Nano 4GB üzerinde `torch.cuda.is_available()` sonucu ve `scripts/jetson_fps.py` p50/p95 kare hızı (PT ve ONNX kolları) — 5 Eylül.
- `:302` BEYAN GEREKLİ (insan):** RPi HQ kamera gerçek yatay FOV değeri (`kamera_dogrula` ölçümü); rapordaki 55–63° **lens beyanından türetilmiş tahmindir**, ölçüm değildir.
- `:303` BEYAN GEREKLİ (insan):** Montaj sonrası gerçek kütleler (İHA, İKA, yük) — §7 `m_İHA`/`m_İKA`/`m_yük` parametreleri.
- `:304` BEYAN GEREKLİ (insan):** İKA gerçek motor sürücüsü seçimi (seri / PWM / GPIO / MAVLink) ve `scripts/ika_surucu_kabul.py` K1–K6 sonuçları.
- `:305` BEYAN GEREKLİ (insan):** Pixhawk üzerinde geofence (`FENCE_*`) ve failsafe parametrelerinin **gerçek donanımda** doğrulanmış hâli; 5 Eylül sonrası `config/pixhawk/arducopter_fda_20260905.param` olarak repoya alınacak.
- `:306` BEYAN GEREKLİ (insan):** İlk hover, Loiter/Auto ve tam prova uçuş logları (`VIBE`, EKF, pusula ofseti, IHA_LANDED damgası) — 6 Eylül ve sonrası.

## BOLUM_7_BUTCE_GERCEKLEME.md  (51 satır)
- `:6` tedarik durumu) artefaktından çıkarılmış; **parasal sütunların tamamı BEYAN GEREKLİ (insan)**
- `:41` BEYAN GEREKLİ (insan): takımın maddi destek başvurusu yapıp yapmadığı, onaylanan toplam bütçe
- `:72` A1 | Kol | `Drone_Arm` (ABS) | 4 | Ü | FDM 3B baskı — bkz. Bölüm 5 §4.1 (kol 1–2 ve 3–4 **farklı reçete**) | **ÖLÇÜLEMEDİ** (G-code yok) | BEYAN GEREKLİ | BEYAN GEREKLİ (5 Eyl tartı) | Üretildi | BEYAN GEREKLİ |
- `:73` A2 | Üst çerçeve | `Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid / 2 duvar | **1 sa 30 dk 16 sn** (ölçüldü) | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:74` A3 | Alt çerçeve | `Lower_Drone_Frame` (ABS) | 1 | Ü | FDM, X1C, 0,20 mm / %15 grid | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:75` A4 | Kubbe | `Drone_Dome` (ABS, **destekli**) | 1 | Ü | FDM, X1C | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:76` A5 | Ayak | `Drone_Legs` (ABS, **destekli**) | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:77` A6 | GNSS tutucu | `GPS_Holder` (ABS, **destekli**) | 1 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:78` A7 | Taban pedi | TPU 95A | 4 | Ü | FDM, P2S | **ÖLÇÜLEMEDİ** | BEYAN GEREKLİ | BEYAN GEREKLİ | Üretildi | BEYAN GEREKLİ |
- `:79` A8 | Motor | **5008 340KV** | 4 | S | — | — | — | BEYAN GEREKLİ | **Kutuda** (kutu açılmadı) | BEYAN GEREKLİ |
- `:80` A9 | Pervane | **12×10** | 4 (+ yedek set) | S | — | — | — | BEYAN GEREKLİ | Kutuda; **yedek set alınacak** | BEYAN GEREKLİ |
- `:81` A10 | ESC | **80 A, DShot destekli** | 4 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
- `:82` A11 | Güç dağıtım kartı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
- `:83` A12 | Uçuş kontrolcüsü | **Pixhawk 6C** | 1 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 59 g) | Kutuda | BEYAN GEREKLİ |
- `:84` A13 | Güç modülü | **PM02** (Pixhawk kutusundan) | 1 | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
- `:85` A14 | GNSS / pusula | **Holybro M9N** | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de M10 için 32 g) | Kutuda | BEYAN GEREKLİ |
- `:86` A15 | RC kumanda + alıcı | **FlySky FS-i6** + FS-iA6B (iBUS) | 1 set | S | — | — | — | BEYAN GEREKLİ | Kutuda; **bind edilmedi** | BEYAN GEREKLİ |
- `:87` A16 | Telemetri | **SiK 433 MHz** | 2 | S | — | — | — | BEYAN GEREKLİ (DDR beyanı 35 g/adet) | Kutuda | BEYAN GEREKLİ |
- `:88` A17 | Görev bilgisayarı | **Jetson Nano 4GB** (Dev Kit) | 1 | S | — | — | — | BEYAN GEREKLİ | **Kargoda — 4/5 Eylül teslim** | BEYAN GEREKLİ |
- `:89` A18 | microSD | ≥ 64 GB UHS-I + okuyucu | 1 | S | — | — | — | — | **Henüz alınmadı** (alışveriş listesi) | BEYAN GEREKLİ |
- `:90` A19 | Kamera | **Raspberry Pi HQ** (IMX477, CSI) + standart lens | 1 | S | — | — | — | BEYAN GEREKLİ (DDR'de Arducam için 50 g) | Kutuda; **FOV ölçülmedi** | BEYAN GEREKLİ |
- `:91` A20 | Jetson besleme | **UBEC 5 V / 5 A** | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ |
- `:92` A21 | Pil | **4S 10 Ah 25C** | 1 (2. pil öneri) | S | — | — | — | BEYAN GEREKLİ | Kutuda | BEYAN GEREKLİ |
- `:93` A22 | Şarj cihazı | **iMAX B6** (50 W) | 1 | S | — | — | — | — | Mevcut | BEYAN GEREKLİ |
- `:94` A23 | Kablolama demeti | XT60/XT90, JST-GH 6-pin, jumper, silikon kablo | lot | Ü | Kesim + lehim + makaron + etiket | BEYAN GEREKLİ | — | BEYAN GEREKLİ | Kısmen kutuda, kısmen **alınacak** | BEYAN GEREKLİ |
- `:95` A24 | Sarf | kablo bağı, ısı makaronu, çift taraflı bant/damper, vida-somun-pul | lot | S | — | — | — | BEYAN GEREKLİ | **Henüz alınmadı** | BEYAN GEREKLİ |
- `:96` A25 | Yedek kamera | USB webcam (UVC) | 1 | S | — | — | — | — | **Henüz alınmadı** | BEYAN GEREKLİ |
- `:97` A26 | Filament | ABS (X1C + P2S profilleri) | BEYAN GEREKLİ (kg) | S | — | — | — | ölçülen tüketim: **≥ 55,86 g** (yalnız A2 için) | Mevcut | BEYAN GEREKLİ |
- `:98` A27 | Filament | TPU 95A | BEYAN GEREKLİ (kg) | S | — | — | — | **ÖLÇÜLEMEDİ** | Mevcut | BEYAN GEREKLİ |
- `:99` — | **TOPLAM** | | | | | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | **ÖLÇÜLEMEDİ** | | **BEYAN GEREKLİ** |
- `:106` BEYAN GEREKLİ (insan)** — üretici veri sayfalarından toplanacaktır. Üretilen parçaların
- `:115` (tutarlar BEYAN GEREKLİ).
- `:145` DDR beyan toplamı** | | | **2293** | FDA aracının kütlesi **ÖLÇÜLEMEDİ** | |
- `:163` Diğer 7 plakanın süresi/tüketimi | **ÖLÇÜLEMEDİ** (dilimlenmiş G-code depoda yok) | — |
- `:165` Yazıcı amortismanı / kWh | **BEYAN GEREKLİ (insan)** | — |
- `:166` Fire / yeniden basım | **BEYAN GEREKLİ (insan)** | — |
- `:171` BEYAN GEREKLİ (insan): kullanılan filamentin cinsi, makara adedi ve makara fiyatı.**
- `:178` (kaynak: `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §B). Fiyatlar BEYAN GEREKLİ.
- `:195` BEYAN GEREKLİ (insan): D1–D12 birim fiyatları, satın alma tarihleri ve fatura numaraları.**
- `:207` S1 | **Araç sınıfı farkı** — FDA'nın §5.3.2 çoklu rotor şartı DDR'de yoktu | 4× 5008 motor + 4× 80 A ESC + quad gövde eklendi; kanat servoları, pitot, airspeed, paraşüt zinciri ertelendi | net etki **BEYAN GEREKLİ** | yeni bir araç montaj/kalibrasyon hattı |
- `:215` Kazanç: kart maliyeti belirgin biçimde düşer (tutar BEYAN GEREKLİ).
- `:217` Bedel 2: `venv38` içinde `tensorrt` yok → **`.engine` ÖLÇÜLEMEDİ**, uçuş PT/ONNX ile yapılacak.
- `:232` BEYAN GEREKLİ (insan): toplam GPU/elektrik gideri ve varsa bulut hesaplama faturası.**
- `:233` BEYAN GEREKLİ (insan): insan işgücü (kişi-saat) dökümü** — takım üyeleri rol bazında.
- `:254` BEYAN GEREKLİ (insan): E1–E10 için ayrılan bütçe ve tedarik takvimi.** Bu on satırın toplamı,
- `:261` BEYAN GEREKLİ, ama **kalemler bugünden bellidir** — sahada karar verilecek bir şey kalmasın diye.
- `:303` BEYAN GEREKLİ (insan): bu kaydın tutulacağı dosya/konum ve sorumlu rol** (öneri: kaptan,
- `:312` Onaylanan toplam bütçe | **BEYAN GEREKLİ (insan)** |
- `:313` Alınan maddi destek dilimi (%25) | **BEYAN GEREKLİ (insan)** |
- `:314` Bugüne kadarki gerçekleşen harcama | **BEYAN GEREKLİ (insan)** |
- `:327` 10. BEYAN GEREKLİ (insan) — toplu liste

---

**TOPLAM: 177 açık kalem satırı** (2 etiket: BEYAN GEREKLİ, ÖLÇÜLEMEDİ).
