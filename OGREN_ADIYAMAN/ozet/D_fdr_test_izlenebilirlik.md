# D — FDR Test Faaliyetleri, İzlenebilirlik, Organizasyon/Takvim, Üretim ve Bütçe: Olgusal Özet

> Kaynak: `FDR/BOLUM_4_TEST_FAALIYETLERI.md`, `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md`, `FDR/BOLUM_2_ORGANIZASYON_VE_TAKVIM.md`, `FDR/BOLUM_5_URETIM_FAALIYETLERI.md`, `FDR/BOLUM_7_BUTCE_GERCEKLEME.md` ve depo kökündeki `TEST_SPECS.md` (tamamı okundu, 10 Eylül 2026).
> Kural: FDR'de olmayan hiçbir şey yazılmadı. Her sayı ve sonuç bölüm/başlık atfı taşır. Belirsiz olan yerde **DOĞRULANAMADI** yazılmıştır. FDR'nin kendi etiketleri (ÖLÇÜLEMEDİ, BEYAN, OLCUM, DOĞRULANACAK, BEYAN GEREKLİ) olduğu gibi korunmuştur.
> FDR'deki son güncelleme izleri 7 Eylül 2026 tarihlidir (D-435, karışıklık matrisi §4.8.4, SVG grafikler §6.6). 6 Eylül Jetson ölçümü (D-431) ve 5 Eylül tezgâh tutanağı (D-426) bölümlere işlenmiştir.

---

## 1. BÖLÜM 4 — Test Faaliyetleri (15 puan)

### 1.1 Bölümün iddiası ve iddia etmediği (§4 giriş)

- İddia: NAVITAS'ın "en olgun tarafı bir model ya da bir kart değil, **ölçüm yordamıdır**".
- İddia edilmeyen: "Hiçbir sayı 'sahada çalışır' demez. Arena ölçümlerinin tamamı sentetiktir; elimizde **gerçek arena/HTAB karesi yoktur** ve maket çekimi yapılmayacaktır." Uçuş testleri 6–19 Eylül planlıdır, rapor yazılırken hiçbiri koşulmamıştır. SiK 433 MHz RF menzili ölçülmemiştir.
- Jetson FPS: üstü çizili "ölçülmemiştir" → **6 Eylül'de ÖLÇÜLDÜ** (Orin Nano Developer Kit 4 GB; pt 1,35/1,06 · engine 1,58/1,33 FPS, eşik 0,61 — D-431).
- İki araç ayrımı: §5.3.2 görev test uçuşu (prova 21 Eylül Adıyaman · resmî uçuş 30 Eylül–3 Ekim) **çoklu rotor** ile; yarışma görevi (§2.2) **sabit kanat + mancınık + paraşüt + İKA** ile. Bölüm 4'teki testlerin tamamı algı–karar–haberleşme–YKS katmanına aittir; bu katman iki araçta aynıdır.

### 1.2 Yönerge eşlemesi (§4.0) — 12 gereksinim

| kimlik | konu | durum |
|---|---|---|
| Y-4-M01 | yer/fonksiyonel/entegrasyon testleri | KISMEN |
| Y-4-M02 | test yöntemleri ve altyapı | VAR |
| Y-4-M03 | sensörler, test takvimi, zaman bütçesi | KISMEN |
| Y-4-M04 | ekipman kabul testleri | YOK |
| Y-4-M05 | kumanda/telemetri menzil testleri | YOK |
| Y-4-M06 | IMU/pusula/pitot kalibrasyon kanıtı | YOK |
| Y-4-M07 | görev icra simülasyonu | YOK (sahibi Bölüm 3.3.3) |
| Y-4-M08 | görüntü işleme performansı, doğruluk matrisleri | KISMEN |
| Y-4-M09 | haberleşme paket yapısı, veri hızı, gecikme | KISMEN |
| Y-4-M10 | tüm yer testleri | KISMEN |
| Y-4-M11 | alt sistemlerin yerde bütünleşik çalışması | KISMEN |
| Y-4-M12 | arıza emniyet (sahada) | YOK |

Sayım: 1 VAR · 6 KISMEN · 5 YOK (tablo §4.0).

### 1.3 Test/kapı envanteri — tablo

Aşağıdaki tablo Bölüm 4'te sayıyla verilen kapıları toplar. "Kanıt" sütunu FDR'nin kendi kanıt yolunu (results/… ya da D-###) taşır.

| kapı / test | ne ölçer | eşik | ölçülen | sonuç | kanıt yolu (FDR atfı) |
|---|---|---|---|---|---|
| Genel kapı `codes/test_rota_sentetik.py` — KOL 1 (`rota_bul`, tanısal) | 15 deterministik sentetik sahnede doğru koridor + geçerli rota | 15/15, exit 0 (Anayasa madde 14) | 15/15 | GEÇTİ | stdout, 3 Eylül (§4.1.1, §4.14 #1) |
| Genel kapı — KOL 2 (`rpi_inference.analyze_path`, üretim yolu) | aynı 15 sahnede rota üretimi ve yayınlanan şerit | ≥ 14/15 (ON_KAYIT SS18-B) | rota 15/15 · şerit 15/15 | GEÇTİ | §4.1.1; Jetson'da 6 Eylül 15/15·15/15 (§4.4, D-431) |
| Tam test paketi `unittest discover -s tests` | tüm sözleşmeler | tümü OK | 1896 test OK (skipped 3), 390,534 s (3 Eyl) → 2104 OK (4 Eyl) → 2138 (5 Eyl; YKS açıkken 1 FAIL, kapalıyken OK) | GEÇTİ (ortam istisnası T209) | `results/faz_b_oncesi/cuma_kontrol/tam_suit.txt`; D-427 (§4.1.2, §4.10.3, §4.14 #2/#38/#40) |
| K0 körlük yok | boş maske üretmiyor | figür zemin > 0, boş maske 0 | figür zemin %2,66; raw 0/67, copy-paste 0/393 boş | GEÇTİ | `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json` (§4.8.1) |
| K1 rota üretilen kare | sentetik arena n=260 | ≥ 230/260 | 256/260 | GEÇTİ | aynı JSON (§4.8.1) |
| K2 rotanın molozdan geçmesi | | ≤ %15 | 6/256 (%2,3) | GEÇTİ | aynı |
| K3 ağır moloz teması | | ≤ %3 | 0/256 | GEÇTİ | aynı |
| K4 arena dışına taşma | | ≤ %5 | 2/256 | GEÇTİ | aynı |
| K5 bariyer kesişimi (dik) | | = 0 px | 0 px (ölçülebilir 178/181) | GEÇTİ; alt ölçüm `K5_figur_bilgi_px` **ÖLÇÜLEMEDİ** | aynı (§4.8.1) |
| K5A bariyer kesişimi (açılı, t189) | | = 0 px | 0 px (176/185) | GEÇTİ | aynı |
| K6 yanlış güzergâh | | ≤ %5 | 2/256 (%0,78) — `sa_000013`, `sa_000090` | GEÇTİ | aynı |
| K7 yayınlanan şerit doğruluğu | 88 karelik iyi koşullu alt küme | doğruluk ≥ %95 ve rota ≥ 80/88 | 84/85 = %98,8; rota 85/88 | GEÇTİ | `t150_baglama_v36_k7.json`, `config/k7_iyi_kosullu_kume.json` (§4.8.1, §4.14 #8) |
| K8 gerçek kare üzerinde karar yolu | `ZEMIN_MASKESI_SUPHELI` dönmemeli (n=1) | — | zemin kaplaması %4,44; ret `UC_BANT_TEMAS_YOK` | GEÇTİ | `scripts/olcum/155_gercek_kare_kapisi.py` (§4.8.1) |
| v36 gerçek-kare eşikleri (test29, `dji/DOGRULAMA/`) | ROTA / MASKE_YOK / FP / YANLIŞ | ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, YANLIŞ = 0 | ROTA **8**, MASKE_YOK **16**, FP 1, YANLIŞ 0 | **2 eşik GEÇİLMEDİ**; terfi kullanıcı kararıyla (D-293) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §3; `results/gece_20260826/ON_KAYIT.md` §15 (§4.8.2.1) |
| Çözünürlük 640 denemesi (D-377) | I2 sentetik gerileme, I3 en uzun körlük, I4 FPS | I2 fark ≤ 0,02; I3 < 5 s | I2 p_S 0,9846 → 0,7808 (−0,2038); I3 51 → 52 kare; I4 oran 1,300 | **RED** (I2 ve I3 DÜŞTÜ) | `results/b4_fps/infer_size_20260901.json`, `ON_KAYIT_INFER_SIZE.md` §5 (§4.8.2.2) |
| Sızıntı düzeltmesi (D-376) | geçerli rota yayınlama olasılığı p | — | sentetik 0,9846; gerçek DJİ sızıntısız (n=243) 0,3457; yalnız 0038: 0,326 | ölçüm; havuzun %62'si eğitim kümesindeydi | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 (§4.8.2.3) |
| Türetilmiş FPS eşiği | `GEREKLI_FPS ≥ 1/(5·p)` | 1/(5×0,326) = **0,61 FPS** | — | saha p'si ÖLÇÜLEMEDİ | `REVIEW_LOG.md`:26042 (§4.8.2.3, §4.14 #16) |
| Jetson FPS kapısı (6 Eylül, D-431) | p50 ve p95 ≥ 0,61 | ≥ 0,61 | PT 1,35/1,06; engine 1,58/1,33 (120 örnek); 10 dk 900 örnek gpu ≤ 56,3 °C | GEÇTİ; ONNX **HATA** (`cudaErrorNoKernelImageForDevice`) | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` (§4.4, §4.13.1 #2) |
| engine↔pt karar denkliği (Jetson) | D-303 oransal | — | F1 0 · F2 0,9953 · **D-303 oransal 3/126 DÜŞTÜ** | DÜŞTÜ → uçuş `.pt` | `results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json` (§4.13.1 #5, Bölüm 6 kanıt dizini) |
| FP16 karar denkliği (PC, D-375) | F1 zarar yönü, F2 uyuşma | F1 = 0; F2 ≥ 0,98 | F1 0/260; F2 631/633 = 0,9968 | GEÇTİ (ilk ölçüm vakumdu, bit-eş 1,0) | `results/b4_fps/fp16_denklik_20260901.json` (§4.8.3) |
| P5 yayın histerezisi H1 | toplam çevrilme | ≤ %40 (ön kayıt) | düştü ve düşük kaldı; H1a/H1b/H2 geçti; ham çevrilme 13→7, 24→11 | **H1 DÜŞTÜ** | `results/p5_histerezis/ON_KAYIT.md`, `olcum_20260903.json` (§4.8.2.4 #1; Bölüm 6 §6.3.3.2) |
| T61 iç tutarlılık (D-401) | dört aday ölçüt | eşiksiz keşif turu | DOĞRULANAMADI | — | `results/t61_ic_tutarlilik/ON_KAYIT.md` (§4.8.2.4 #2) |
| T52 ayırt edici ölçüt | | | DOĞRULANAMADI; köprü tavanı 0,55 | — | D-398 (§4.8.2.4 #3) |
| T101 W2 kapısı | sürüm kayması | | DÜŞTÜ; "iki sayı farklı popülasyon" | DÜŞTÜ, sebebi yazıldı | D-400 §3 (§4.8.2.4 #4) |
| D-379 şekil kapısı "H harfi" | | | 17 H-olmayan şeklin 16'sı geçti → kapı daraltıldı ("ped yapısı", harf değil) | DARALTILDI | D-383 §3 (§4.8.2.4 #5) |
| Karışıklık matrisi (7 Eylül) | piksel düzeyi, test29, CPU, CONF 0,30, imgsz 512 | — | IoU zemin 0,4922 · engel 0,7400 (etiketsiz FP sayılmadan; sayılarak 0,4313 · 0,6760); %39,6 piksel etiketsiz | ÖLÇÜLDÜ; ışık/gölge kesiti ÖLÇÜLEMEDİ | `results/gece_20260907/karisiklik/piksel_karisiklik_test29.{json,md,png}` (§4.8.4) |
| P1 MAVLink G1–G7 (sahte Pixhawk, gerçek çerçeve) | irtifa 30,0 ± 0,05 m, mpp, `yerde_mi`, sysid, tazelik | | hepsi GEÇTİ; BULGU A (`yerde_mi` 0,002 s'de False, IHA_LANDED hiç yayınlanmazdı) kapatıldı (D-389) | GEÇTİ | `results/p1_mavlink/ON_KAYIT.md`, `tests/test_p1_canli_mavlink.py` (14) (§4.9.1) |
| P2 SiK seri S1–S4 | çerçeveleme, ACK turu, gürültü | | GEÇTİ | GEÇTİ | `results/p2_seri/ON_KAYIT.md`, `tests/test_p2_seri_hat.py` (10) (§4.9.2) |
| P2 S5 tampon tavanı | ≤ 64 KiB | 65.536 B | **1.048.576 B** | **DÜŞTÜ** → düzeltildi, aynı eşikle yeniden koşuldu | D-388 (§4.9.2) |
| SiK hub UDP→seri gecikmesi | paraşüt tekrar aralığı 0,20 s altı | < 200 ms | A p95 31,0/31,2 ms; B (20 Hz HEARTBEAT) p95 70,8/76,8, maks 79,7 ms; C p95 16,2/15,2 ms; kayıp 0/50 | GEÇTİ (Windows `socket://`; Jetson/Linux ölçülmedi) | `results/faz_b_oncesi/curutucu_d405/` `r2_gecikme.py` (§4.9.3) |
| T207 akış isteği gerçek topoloji | `SET_MESSAGE_INTERVAL` yenileme + sessizlik alarmı | | A: proxy 25/25, ilk gecikme 0,30 s, 8 Hz + 2 Hz, alarm ✔; B: 50/50, alarm yok ✔ | GEÇTİ | `results/faz_b_oncesi/curutucu_d407/akis_istegi/r_topoloji2.py` (§4.9.4) |
| Uçtan uca kare gecikmesi | üretim zinciri + UDP loopback ACK, 33 kare (+3 ısınma) | tazelik 5,0 s | p50 0,085 s · **p95 0,113 s**; model yükleme 2,64 s (bütçe dışı) | GEÇTİ (UDP loopback yapılandırması); seri hat ÖLÇÜLMEDİ (üretim seri varsayılanlarıyla çevrim 1,0 s) | `results/fda_butce/olcum_20260901.json`; D-382/D-383 (§4.9.5) |
| Komut hattı K-1/K-2/K-3 (D-419/D-422) | ACK kaynağı, terminal durum, saat ofseti, replay | | `test_faz_b_iha_komut_alici` 23 OK; `test_iha_komut_saat_ve_tekrar` 18→42; replay: 40×/500×/200× ısrar → 1 COMMAND_LONG | GEÇTİ; mutasyon 17 + 5 düştü | `REVIEW_LOG.md`:28989–29055, 29449–29568 (§4.9.7) |
| Kamera köprüsü dayanıklılık | bellek, 40 istemci, kopma | | 0,48 MB sabit (tepe 0,74), RSS ~72 MB; `dusen_kare=0`, KIRMIZI log 0 | GEÇTİ; K5 vakum (yalnız söz dizimi) AÇIK | `results/faz_b_oncesi/curutucu_d407/kopru/` (§4.10.1) |
| Ekransız kip (`--ekransiz`) | karar yolu bayt-eş | | 6 kipte 23 kayıtlık iz birebir | KOŞULLU GEÇTİ (7/7 mutant, §4.2.2) | D-404 §2/§8 (§4.10.2) |
| Jetson açılış kuru koşuları | `jetson_baslat.sh --kuru` | udp/sik exit 0; eksik beyan exit 3 | 3 Eyl: udp exit 0, sik exit 0, EKSIK exit 3; 4 Eyl: `[YOK]` 7 / 9 → çıkış 3 (Windows'ta beklenen) | fail-closed çalıştı | `results/faz_b_oncesi/jetson_baslat_kuru_*.txt`, `cuma_kontrol/*_0904.txt` (§4.10.3) |
| Runbook komut kapısı (D-421) | runbook komutları gerçekten koşar | | eski `test_p4_runbook.py` 22/22 yeşilken komut EXIT=2 (`--izinli-kaynak` eksik); yeni `test_runbook_komutlari_kosuyor.py` 3 test, mutasyonda T1 düştü | kapatıldı | `REVIEW_LOG.md`:29299–29350 (§4.10.3, §4.2.4 #5) |
| Saha kuru koşusu `scripts/saha_kuru_kosu.py` (10 halka) | zincir sahipliği | tüm halkalar | GEÇTİ 9 · DÜŞTÜ 0 · **SAHİPSİZ 1 (motor)**; exit 1 (3 Eyl, 4 Eyl 01:00 ve 09:52 aynı) | zincir TAMAMLANMAZ | `results/saha_kuru_kosu_20260904_095222/ozet.json` (§4.11.1–§4.11.2) |
| 5 Eylül Pixhawk tezgâh testi | firmware, GPS, RC, güç, motor | | ÖLÇÜM: `ArduCopter V4.5.7 (2a3dc4b7)`, `Frame: QUAD/X`, `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10`, `RCInput: decoding IBUS(1)`, pil/emniyet PreArm kayboldu, `starting/finished motor test` | ÖLÇÜM/BEYAN karışık | `REVIEW_LOG.md` D-426 §1 (satır 29819–29829) (§4.10.4) |
| Menzil / RTT / paket kaybı (SiK 433) | | RTT p95 < 0,2 s | — | **ÖLÇÜLEMEDİ** (`scripts/sik_rf_olc.py` koşulmadı) | §4.5, §4.13.1 #3 |
| IMU / pusula / pitot kalibrasyonu | | pusula ofset < 300 | IMU BEYAN "yapıldı" (kart sabit değildi); pusula YAPILMADI; pitot kapsam dışı | **ÖLÇÜLEMEDİ** | D-426 §4; 6 Eylül dökümü `config/pixhawk/arducopter_fda_20260906.param` (§4.6) |
| Arıza emniyet (RTL, DISARM, geofence, RC failsafe) | sahada test | | hiçbiri tetiklenmedi; 6 Eylül dökümünde `FS_THR_ENABLE` 1→3, `BATT_FS_LOW_ACT` 2→1 bilinçsiz değişmiş (D-428 §5b); RC failsafe 6 Eylül'de ÖLÇÜLDÜ ve DÜŞTÜ (Bölüm 6 §6.1.5, D-428 §2) | **ÖLÇÜLEMEDİ** (saha) | §4.12; yazılım yolu `tests/test_iha_rtl_land.py` (6), `tests/test_iha_komut_guvenligi.py` (10) |
| Görev icra simülasyonu (CAD, video, başarı oranı) | | | YOK | **YOK** | §4.7 (sahibi Bölüm 3.3.3) |
| Uçuş testleri 3.1–3.6 | hover, Loiter/Auto, canlı algı, 3 prova, sıkı prova, mühür | ≤ 10 dk, 0 müdahale, yanlış güzergâh 0 | — | **ÖLÇÜLEMEDİ** (koşulmadı) | §4.3.3, §4.13.1 #4 |

**Ekipman kabul (§4.4):** hiçbir ekipmanın tam fiziksel kabul testi yoktur. Satır satır: Jetson → 6 Eylül ÖLÇÜM (GEÇTİ; CSI kamera bağlı değil, Pixhawk `/dev/ttyACM0` `[YOK]`); Pixhawk 6C KISMEN (firmware + parametre OLCUM, `mavlink_dogrula.py` koşulmadı); M9N KISMEN (alıcı tanındı, 3B fix kaydı yok); RPi HQ ÖLÇÜLEMEDİ (köprü dosya kaynağıyla açıldı); SiK KISMEN (bağlandı BEYAN); motor/ESC KISMEN (pervanesiz motor testi OLCUM, sıra/yön 4/4 BEYAN, ESC kalibrasyonu YAPILMADI, ESC "60 A V2" plan 80 A); pil KISMEN; FS-i6 KISMEN; İKA ekipmanı seçilmedi (gerçek motor sürücüsü YOK, R12/T149).

**Motor künyesi (7 Eylül, D-435):** ~~5008 340KV × 4, 12×10~~ → SunnySky X2220 980KV V3 × 4 + 10×4,5 pervane (BEYAN, etiket fotoğrafı yok; 5008'ler iade edildi; X2220'ler 2 yıl önce kullanılmış eski motorlar). 5 Eylül motor testinin hangi motorla koştuğu BEYAN GEREKLİ (§4.4).

### 1.4 "Ön kayıt" (pre-registration) kavramı — nasıl kullanılıyor (§4.2.1)

- **Kural:** Bir kapının eşiği **ve karar sırası**, ölçüm koşulmadan önce bir `ON_KAYIT` dosyasına yazılır; sonuç görüldükten sonra **değiştirilmez** (D-107, 2026-08-14).
- **Doğuş gerekçesi (D-107 alıntısı):** "Bu projede tekrarlanan hata olcutu SAYIYI GORDUKTEN SONRA yorumlamak oldu: D-85'te alt kumenin azamisine esik oturttum (D-86 curuttu), D-90'da tanima bagli bir olcutle %92,7 rapor etmek uzereydim, D-104'te kapiyi yanlis modelle olcturdum."
- **Hacim:** `results/` altında **36 ön kayıt artefaktı** (35 Markdown + 1 JSON), `find results -iname "*on_kayit*"` (3 ve 5 Eylül, değişmedi).
- **İş gördüğü dört olay (tablo §4.2.1):** (1) Çözünürlük 640 — "I2 düşerse → RED, I1 ne olursa olsun" önceden yazılıydı; I1 %21,6 umut vericiyken I2 −0,204 → RED; (2) P2 tampon tavanı ≤ 64 KiB — ölçülen 1.048.576 B → DÜŞTÜ, kod düzeltildi, **aynı eşikle** yeniden koşuldu; (3) P5 histerezis H1 ≤ %40 — düştü ve düşük kaldı, eşik gevşetilmedi, EK-1 ölçütleri (H1a/H1b) bileşim görülmeden yazıldı; (4) T61 — tur eşiksizdi, eşik üretmedi, dört aday DOĞRULANAMADI.
- **Kurtarmadığı olay:** `results/gece_20260826/ON_KAYIT.md` §15'te kullanıcı "izin veriyorum kurala rağmen" yazdı ve v36 kendi eşiklerini geçmeden terfi etti. FDR bunu "ön kaydın rolü olayı görünür kılmak oldu; sessiz gevşetme mümkün olmadı" diye yazar (§4.2.1, §4.8.2.1).
- Bölüm 6 §6.2.2'de ön kayıt, "bir satır nasıl KANITLI_TEST olur" zincirinin 4. adımıdır (sözleşme → kapı → mutasyon → ön kayıt → çürütme).
- Bölüm 2 §2.1.6 kural 1 olarak da yazılıdır ve R7 (yazılım) rolünün **eşik değiştirme yetkisinin olmaması** buna bağlanır (§2.1.2 kural 2).

### 1.5 Test altyapısı (§4.2.6) ve kapsamadıkları

Tek yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`; sahte Pixhawk `scripts/sahte_pixhawk.py` (gerçek MAVLink çerçeveleri UDP'ye); SiK köprüsü (TCP röle, iki `serial_for_url("socket://…")` ucu) `tests/test_p2_seri_hat.py`; kuru koşu fikstürü `data/kuru_kosu_fikstur/`; mutant koşucusu `results/faz_b_oncesi/ekransiz_denetim/mutant_kos.py`; loopback İKA `scripts/saha_kuru_kosu.py`. **Kapsamadığı dört şey:** gerçek RF, gerçek Pixhawk, gerçek Jetson, gerçek arena (§4.13.1). Beşinci sınır (D-427): `comms/test_comms.py:35-36` üretim portlarına (5005/5006) bind eder, YKS açıkken tam suit koşamaz (T209 açık).

### 1.6 Zaman bütçesi (§4.3.4) ve uçuş test takvimi (§4.3.3)

- Uçuş başına gerçek görev süresi **ÖLÇÜLEMEDİ**. Tek pil (4S 10 Ah) + iMAX B6 ⇒ **günde en fazla 2 uçuş**.
- Planlanan kapılar: 3.1 ilk hover (Stabilize/AltHold, 2–3 m, 2 dk; `VIBE`, EKF yeşil) · 3.2 Loiter + kısa Auto 30 m + geofence + iniş kanıtı canlı · 3.3 algı canlı, yanlış güzergâh 0 · 3.4 tam prova ×3, ≤ 10 dk · 3.5 sıkı prova, 0 müdahale · 3.6 sürüm dondurma (`--dogrula` 0).
- Ölçülmüş yer bütçeleri: tam suit 390,534 s; uçtan uca p95 0,113 s; model yükleme 2,64 s; rota üretimi 31 ms; hub p95 70,8/76,8 ms. Tazelik penceresi `YKS_TESPIT_TAZELIK_S = 5,0` s.

### 1.7 Kalan test borcu (§4.13)

- **§4.13.1 ölçülmemişler (18 kalem, 3'ü üstü çizili):** 1 gerçek arena karesi (21 Eylül'e kadar açık); ~~2 Jetson FPS~~ ÖLÇÜLDÜ; 3 SiK menzil/kayıp; 4 uçuş testleri; ~~5 engine↔pt~~ ÖLÇÜLDÜ ve DÜŞTÜ; 6 gerçek Pixhawk'ta `--kapi` (`mavlink_dogrula` 3/3); 7 `jetson_baslat.sh --kapi`; 8 gerçek İKA motor sürücüsü; 9 geofence parametreleri (6 Eylül dökümü var, üçüncü döküm bekleniyor); 10 K5 figür bilgi px; ~~11 Nano belgesi~~ konusuz; 12 RC failsafe; 13 ESC kalibrasyonu; 14 pusula; 15 accel teyidi; 16 parametre dökümü; 17 pil gerilimi ±0,1 V; 18 motor sırası/yönü videosu.
- **§4.13.2 kapı boşlukları:** 3 kapandı (seri_hub 24/25; RecursionError; tek sahiplik `exclusive=True`), 3 açık (kamera köprüsü K5 API adı; SIGTERM/T204, T205; `core.autocrlf=true` kırılganlığı — bir turda 11 test bu yüzden düştü).
- **§4.13.3 denetim borcu (madde 19):** D-407 düzeltmeleri, `jetson_baslat.sh` systemd kipleri, D-406 T207 kodu (bağımsız üçüncü göz yok), D-412 `_kanit_yaz` — hepsinde "yazan ile onaylayan aynı taraf".
- **§4.13.3.1 kendi hatası:** `ef02e19` belge commit'i `comms/yks_gui.py`'den 16 satır götürdü; `self._kanit_yaz(...)` çağrısı kaldı, tanımı yoktu → YKS her kurulumda `AttributeError`; aynı turda "1882 test OK" yazılmıştı ama koşum commit'ten önceydi. Sonraki suit koşumunda 6 hata olarak yakalandı (D-412).
- **§4.13.4 BEYAN GEREKLİ (insan):** donanım künyesi fotoğrafı; SiK RTT/menzil; uçuş testlerinin tarih/pilot/log; Adıyaman alan izni; mühür tarihi (planlı 17 Eylül); motor sırası videosu ve BEC teli.

### 1.8 Kanıt dizini (§4.14) ve bölümün sınırı (§4.15)

§4.14, 71 satırlık bir kanıt dizinidir (sayı/iddia · dosya yolu · üreten betik · tarih). §4.15: "Kanıtlanmamış olan tek şey en önemlisidir: gerçek arenada, gerçek Jetson üzerinde, gerçek telsizle çalıştığı. O ölçüm 5–21 Eylül arasındadır."

---

## 2. BÖLÜM 6 — Gereksinim İzlenebilirliği (10 puan)

### 2.1 Durum sözlüğü (§6.1.1)

| durum | anlam |
|---|---|
| **KANITLI_TEST** | üretim kodu var **ve** `tests/` altında koşan kapı var; çoğu mutasyonla ayırt edici |
| **KOD_VAR_TEST_YOK** | davranış kodda var, doğrudan zorlayan kapı yok |
| **ÖLÇÜLEMEDİ** | hüküm repo dışında ya da donanım/veri yok — "ÖLÇÜLEMEDİ, GEÇTİ demek değildir" |
| **İNSAN-DONANIM** | yazılıma düşmez (montaj, ağırlık, mühür, yük, hakem gözlemi) |

### 2.2 Üç kimlik sistemi (§6.1.7)

- **§…** = şartname maddesi; **R1–R22** = yükümlülük haritası `results/sartname_bosluk/rapor.md` (26–27 Ağustos; üç satırı bayat, §6.3.4'te düzeltildi: R13 HB bağlama KAPANDI D-386, R17 alan ihlali yazılım tarafı KAPANDI D-307, kuru koşu rota GEÇTİ); **Y-…** = FDR yönerge kimliği (`FDR/YONERGE_HARITASI.md`).
- **Eksik dördüncü liste:** ÖDR/DDR gereksinim numaraları. DDR kimliği ↔ R ↔ Y eşlemesi **yapılmamıştır** (`rapor/NAVITAS_DDR_Birlesik.docx` makine okunur değil); BEYAN GEREKLİ.

### 2.3 Matris ↔ sayılar (§6.6.1 — dört matris, 45 satır)

| matris | satır | KANITLI_TEST | KOD_VAR_TEST_YOK | ÖLÇÜLEMEDİ | İNSAN-DONANIM |
|---|---:|---:|---:|---:|---:|
| §6.1.3 — §2.1 / §2.2 (görev akışı) | 19 | 14 | 1 | 1 | 3 |
| §6.1.4 — §5.3.2 (görev test uçuşu) | 9 | 7 | 0 | 1 | 1 |
| §6.1.5 — §6.2 / §6.4 (yarışma sırası, geçersizlik) | 10 | 5 | 3 | 0 | 2 |
| §6.1.6 — §7 (puanlama parametreleri) | 7 | 6 | 0 | 0 | 1 |
| **toplam** | **45** | **32 (%71,1)** | **4 (%8,9)** | **2 (%4,4)** | **7 (%15,6)** |

- Sayım kuralı: satırın **baskın/birincil** etiketi alınır (§6.3.1); **dokuz satır** iki etiket taşır (örn. §2.2.2 R2 tam otonom uçuş: ÖLÇÜLEMEDİ birincil, şablon KANITLI_TEST ikincil; §5.3.2 kare hızı: KANITLI_TEST birincil, saha p'si ÖLÇÜLEMEDİ ikincil).
- 5 Eylül tutanakları sonrası yeniden sayım: **değişmedi** (32/4/2/7).
- **Önceki sürümle fark (§6.6.7):** önceki sürüm KOD_VAR_TEST_YOK 3 / İNSAN-DONANIM 8 veriyordu; satır satır sayımda 4 / 7 çıktı; hiçbir durum hücresi değiştirilmedi, "sayım hücrelere uyduruldu".
- **KOD_VAR_TEST_YOK (4):** §2.1 R1-ek üç güzergâh adayı denetimi (yalnız tanısal kolda) · §6.2 müdahale −100 · §6.2 tekrar fırlatma · §6.4 manuel moda alma (`mod` alanı üretilmiyor).
- **ÖLÇÜLEMEDİ birincil (2):** §2.2.2 R2 tam otonom uçuş · §5.3.2 20×20 m alanın tek karede görülmesi (kamera FOV ölçülmedi). Altı satır daha ikincil ÖLÇÜLEMEDİ taşır (R9 otonom paraşüt tetiği, R13-ek fiziksel temas, saha p'si, uçuş süresi, Pixhawk geofence, gerçek SiK).
- **İNSAN-DONANIM (7):** §2.2.1 mühür/mancınık · §2.2.5 R12 İKA sürücüsü · §2.2.6 R22 yük · §5.3.2 çoklu rotor künyesi · §6.4 kırım/iniş ihlali · §6 ağırlık/mühür · §7 kütleler.
- **Uyarı (§6.6.6):** "%71 'kanıtlı' demek 'sahada çalıştı' demek değildir" — ölçümlerin ezici çoğunluğu sentetik arena ve UDP loopback üzerindedir.

### 2.4 Doğrulama yöntemi dağılımı (§6.2.3 / §6.6.3)

45 satıra **66 yöntem ataması** (3 Eylül 65; R2 satırına 5 Eylül "gözle muayene" eklendi): test 39 (%86,7) · gözle muayene 11 (%24,4) · simülasyon 7 (%15,6) · hesaplama 5 (%11,1) · analiz 4 (%8,9). "test yok" yazan üç satır test sütununa sayılmaz (ham alt-dize sayımı 42, uygulanan 39). Yalnız gözle muayeneye dayanan 6 satırın 3'ü yazılım borcudur; **müdahale −100 cezasının testsiz olması açık kalem listesinde yoktur** — FDR bunu "listenin bir eksiği" diye kayda geçirir.

### 2.5 Gereksinim → tasarım kararı → kanıt (§6.4.1, 14 satır — özet)

R10 iniş kanıtı → fail-closed latch (`ON_GROUND` ∧ `relative_alt < 1 m`, aynı sysid, ardışık 3) → `test_inis_kaniti.py` (26), `test_iha_landed_gate.py` (12) · R10-ek → `AkisIstekcisi` (10 s yenileme, 5 s sessizlik KIRMIZI) → `test_faz_b_akis_istegi.py` (17) · §5.3.2 yanlış güzergâh 0 puan → fail-closed ret zinciri, son savunma `send_open_route` → K3 0/256 · gerçek zamanlılık → `karar_yas` alanı → `test_t169_tespit_tazeligi.py` (19) · 10 dk → `--fda` bütçe 600 s, kötü-durum 221,5 s → `test_t170_fda_sure_butcesi.py` (16) · 30 m → `SARTNAME_ASGARI_IRTIFA_M = 30,0`, plan 32 m (D-319: şart daha önce hiç uygulanmıyordu) → `test_t171_asgari_irtifa.py` (20) · R4 aktarım → her karede tam mesaj, latest-wins → `test_rpi_telsiz_yayin.py` (11) · R13 HB → ölçek+şekil çifti → 253/256 doğru ped, 259/260 HEDEF_YOK · R13-ek → `FINAL_WP_RADIUS < HB_KENAR_M/2` → `test_p9e_branda_temas.py` (5) · §6.2/§6.4 süre → iki ayrı son tarih → `test_k5_k6_sure_limitleri.py` (9, 4 mutasyon) · §6.4 veri akışı → heartbeat 1,0 s < 3,0 s · alan ihlali → aynı telemetri okuyucusu → `test_t162_alan_ihlali.py` (19) · R12 → `GercekSurucu` arka uçsuz kurulamaz (`DONANIM_YOK`) · hakem onayı İKA yokken → `--fda` bayrağı → `test_faz_b_yks_fda_kipi.py` (9, 4/4 mutant).

**Performansa maliyet (§6.4.2):** 640 reddi (p 0,9846→0,7808); v36 terfisi bedelle (K3 0→1, K4 1→4, K6 5→7, val82 FP 0→2); histerezis (çevrilme 13→7, 24→11; NO_ROUTE hiç geciktirilmez).

### 2.6 Açık gereksinimler (§6.5.1) — A1…A13

| # | şartname | açık olan | kapanma koşulu |
|---|---|---|---|
| A1 | §2.2.5 R12 | gerçek İKA motor sürücüsü yok (2026-07'den beri); donanım kararı verilmedi | arka uç + `scripts/ika_surucu_kabul.py` K1–K6; final dalgası |
| A2 | §2.2.3 R20 | gerçek SiK 433 hattı hiç ölçülmedi; DDR ">%98, 300 m" kanıtı yok | `sik_rf_olc.py --n 50`, p95 < 0,20 s; tarih BEYAN GEREKLİ |
| A3 | §2.2.2/§6.2 R2 | gerçek otonom uçuş hiç koşmadı | ilk hover → Loiter/Auto → tam prova |
| A4 | §5.3.2 | gerçek arena karesi yok; maket çekimi yapılmayacak | saha p'si 21 Eylül'de; **rapor tarihinde kapatılamaz** |
| A5 | §5.3.2 | gerçek uçuşta 45–51 s kör aralıklar (0038: 51 kare, 46'sı MASKE_YOK); tazelik penceresini 10 kat aşar; hız sorunu değil, model sorunu | arena benzeri veri / ikinci geçiş; açık |
| A6 | §2.1 R1-ek | üç-güzergâh adayı ve K2/K3 ihlal denetimi üretim yolunda yok | `analyze_path` koluna taşıma + mutasyon |
| A7 | §6.4 R21 | `mod` alanı üretim telemetrisinde yok | `send_heartbeat` alanı + kapı |
| A8 | §6.2 | tekrar fırlatma doğrudan testi yok | tek testlik iş |
| A9 | §2.2.6/§7 | Gazebo fiziksel temas koşusu ÖLÇÜLEMEDİ (`gz` yok) | Gazebo'lu makine |
| ~~A10~~ | §5.3.2 | ~~Nano FPS~~ → **KAPANDI 6 Eylül** (D-431) | — |
| A11 | §5.3.2 | `--fda` kipinin bağımsız denetimi yok (aynı el) | 21 Eylül öncesi gerçek provada hakem rolü |
| A12 | §2.2.4 R9 | otonom paraşüt tetiği ölçülmedi | final dalgası |
| A13 | §6.2/§6.4 | Pixhawk failsafe/geofence/parametre dökümü (5 Eylül açıldı); RC failsafe 6 Eylül ÖLÇÜLDÜ ve DÜŞTÜ (D-428 §2) | üçüncü döküm |

Sayım (§6.5.1 sonu): **11 açık** (A10 kapandı). §6.6.4 dağılımı 12 kalem üzerinden: donanım/veri bekliyor 4 (A1–A4, %33,3) · ölçüm bekleyen risk 3 (A5, A9, A13, %25,0) · yazılım borcu 3 (A6–A8, %25,0) · denetim/final borcu 2 (A11, A12, %16,7). **Yedi kalemin kapanma tarihi verilmemiştir:** A2, A5, A6, A7, A8, A9, A13 — "bu raporda tarih uydurulmamıştır".

### 2.7 Geçilmeyen üç kapı (§6.3.3)

1. v36, ROTA ≥ 10 (ölçülen 8) ve MASKE_YOK ≤ 10 (ölçülen 16) eşiklerini geçmeden 2026-08-26'da kullanıcı kararıyla terfi etti; eşikler değişmedi, `CONTRACTS.md §12`'ye istisna satırı yazıldı; v35 yedek olarak duruyor.
2. Histerezis H1 özgün eşiği düştü (`"H1_ozgun": false`).
3. Kuru koşuda `motor` halkası SAHİPSİZ, `cikis_kodu: 1` (2 Eylül ve 4 Eylül 09:52 aynı).

### 2.8 Görsel sunum (§6.6, Y-6-M06)

7 Eylül: `sekiller/uygunluk_pasta.svg` (halka) ve `sekiller/uygunluk_yontem.svg` (çubuk) `scripts/fdr_sekil_uret.py` ile tablolardan üretilir; `tests/test_gece_sekiller.py` (11 test; 5/5 mutasyon) sayıları tabloya karşı sınar. §6.6.4 için grafik üretilmedi (metin bar).

---

## 3. BÖLÜM 2 — Organizasyon ve Takvim (5 puan)

### 3.1 Takım künyesi ve isim yasağı

- Takım: **Navitas Autonomous Systems** · Takım ID **997827** · Başvuru no **5329027** (kaynak `navitas-teknofest/references/ddr_requirements.md`; **DOĞRULANACAK** — KYS teyidi yok).
- **İsim yoktur ve olmayacaktır.** Yönerge (Y-2.1-M02) "üyelerin kişisel verilerinden (isim, görsel vb.) arındırılmış, tamamen rol bazlı" anlatım şart koşar; FDR bunu karşılanmış gereksinim sayar, "isim eklemek gereksinimi kapatmaz, ihlal eder" der (§2.1.1; dayanak D-417). Dolayısıyla "kim ne yapıyor" sorusu FDR'de yalnız **rol kodlarıyla** (R1–R8) cevaplanır; rol → kişi eşlemesi takım içi kayıttır, rapora girmez. **Bu özette de isim yoktur — FDR'de isim bulunmadığı için.**

### 3.2 Roller ve icra yetkileri (§2.1.2–§2.1.3)

| rol | sorumluluk | yetkisi olan kararlar | ürettiği kanıt |
|---|---|---|---|
| R1 Takım Kaptanı | görev günü tutanağı, saha kararları, atama, tedarik onayı | "Takım Hazır" ilanı; uçuş/uçmama; koordinat girişi onayı | saha tutanağı |
| R2 Pilot | RC, arm/disarm ön kontrol, manuel kurtarma | uçuşu **kesme**; mod anahtarı | uçuş logu (`.bin`) |
| R3 Aviyonik | Pixhawk 6C, güç, kablolama, kalibrasyon, failsafe/geofence | parametre yükleme; kablo hattı kabulü | `config/pixhawk/arducopter_fda_20260906.param` |
| R4 Görev bilgisayarı/kamera | Jetson kurulumu, kamera köprüsü, FPS kapısı, model | sürüm/paket; kamera kaynağı | `jetson_fps.py`, `jetson_baslat.sh --kapi` çıktısı |
| R5 YKS operatörü | yer istasyonu, hakem ekranı, ACK, kronometreler | ekran düzeni; ACK'siz onayı **reddetme** | `hakem_log`, ekran kaydı |
| R6 İKA (final dalgası) | İKA hattı, sürücü entegrasyonu | İKA sürücü seçimi | `ika_surucu_kabul.py` çıktısı |
| R7 Yazılım/görüntü işleme | algı zinciri, rota kararı, sözleşmeler, testler | kod değişikliği (mühre kadar); **eşik değiştirme yetkisi YOK** | `tests/` çıktısı, D-kayıtları |
| R8 Kanıt-kalite (denetim) | bağımsız çürütme, ön kayıt tutma, kapı denetimi | bulguyu deftere yazma; kapıyı **geçersiz sayma** | çürütücü kayıtları |

- Üç bağlayıcı kural: tek karar mercii R1; yetki devri karar devri değildir (R7 eşik değiştiremez); denetim (R8) icra hattının **dışındadır**, hükmü R1'e döner. Şema: `sekiller/organizasyon.svg` (7 Eylül; nöbetçi `tests/test_gece_sekiller.py`).
- Bugün atanmış roller (kullanıcı beyanı, 3 Eylül): **R2 Pilot** ve **R5 YKS operatörü**. R5, YKS PC kurulumunu üstlenip uçtan uca koşturdu (D-414; `results/yks_kurulum/yks_acilis_20260903.png`).
- **Ölçülmüş rol çakışması (§2.1.5):** R2 ve R5 uçuş anında eşzamanlıdır; **BEYAN GEREKLİ: uçuş günü ikinci kişi.** Şartname §4: kaptan dâhil 6–10 kişi; üye sayısı ve oran BEYAN GEREKLİ (§2.1.7).
- Saha günü dağılımı (§2.1.4): 5 Eylül'de sahada **tek takım üyesi** vardı; pilot R2 ve takım lideri sahada değildi; mimar uzaktan yönlendirdi (Bölüm 4 §4.10.4).

### 3.3 Karar ve kanıt yordamı (§2.1.6)

Dört kural: (1) ön kayıt (D-107, D-377 örneği); (2) ÖLÇÜLEMEDİ ≠ GEÇTİ; (3) bağımsızlık — "bir iş, onu yapanın onayıyla kapanmaz" (D-405, D-407); (4) kanıt silinmez, üstü çizilir (D-373). Kanıt defteri `REVIEW_LOG.md`: üç okuma birbirini tutmuyor ve üçü de bırakıldı — A 414/408, B 420/414, C **424/418** (4 Eylül 00:06); A ve B'nin saati kayıtlı değil → ÖLÇÜLEMEDİ. (Bölüm 4/6'da 5 Eylül okuması 432/426, son kayıt D-427.)

### 3.4 Takvim — DDR uygunluğu, kilometre taşları, resmî tarihler

- **DDR termin planı (§2.2.1):** DDR teslim 15 Temmuz 2026 (depodan görülemez → ÖLÇÜLEMEDİ, KYS teyidi BEYAN GEREKLİ); DDR sonuçları 29 Temmuz 2026 (puan BEYAN GEREKLİ); **FDR 21 Eylül 2026 – 17.00 → UYGUN**, kapı `tests/test_fdr_takvim_kapisi.py` 4/4 OK (4 Eylül). DDR'de Gantt/iş paketi yok; yalnız üç tarih.
- **Depo geçmişi (§2.2.2):** ilk commit 2026-05-06 (`17258f8`); 3 Eylül okuması 551 commit (Ağustos 425) **yeniden üretilemedi**; 4 Eylül 00:05 yeniden ölçüm **560** (HEAD), 607 (`--all`); Ağustos 26 gün / 418 commit; en yoğun gün 26.08 (89). Eski okuma silinmedi, ÖLÇÜLEMEDİ olarak bırakıldı.
- **Kilometre taşları (§2.2.3, seçme):** 2026-06-24 model v2 · 07-11 haberleşme çekirdeği + simülasyon zinciri · 07-12 v3 (mask mAP50 0,627) · 08-16 `seed` kusuru (v31 = v30 bit-bit, 6,4 saat GPU, D-140) · 08-21 v35 üretimde · **08-26 v36 üretime alındı, iki eşik geçilmeden** · 08-27 K7 bağlandı · 08-28 v37 geri alındı (D-332), v8 RED (6,19 saat, D-331) · 09-01 uçtan uca p95 0,113 s · 09-02 çoğullayıcı zorunlu, `jetson_baslat.sh` + 6 systemd birimi, `--fda` kipi (D-408), suit 1827 · 09-03 genel kapı 15/15·15/15, suit 1875, kuru koşu 9/1, saha belleği 405 dosya·1,27 GB, **takvim kusuru D-410**, microSD/M.2 düzeltmesi D-413, YKS kurulumu D-414.
- **Model soyağacı (§2.2.4):** v36 ÜRETİM (`navitas-seg-v36-512`, sha `1d1caca6…c46911`); v34, v35 yedek aday; v37 geri alındı; v8 reddedildi. Damgaların saha paketine kopyalanma anı olduğu DOĞRULANACAK.
- **Şartname resmî takvimi (§2.2.5.3):** FDR son teslim **21.09.2026 17.00** · FDA (FDS + drone görev test uçuşu) **30.09–03.10.2026, tek atış** · FDR sonuçları 04.10.2026 · SGGS 05.02.2027 · UHDR 16.04.2027 · uçuş testleri 21.05.2027 · yarışma Ağustos–Eylül 2027. **Düzeltilen kusur (D-410):** 21 Eylül uçuş günü sanılıyordu; oysa FDR teslim günü ve takımın kendi Adıyaman genel provasıdır; hata plan/runbook/CONTRACTS/FDR'ye yayılmıştı; **FDA = FDR × 0,85 + test uçuşu × 0,15**.
- **Planlanan 3 → 30 Eylül (§2.2.6):** Per 3 Eyl Jetson yığını/köprü/şablon · Cum 4 Eyl bellek, YKS PC, kargo (microSD satırı D-413 ile yeniden yazıldı) · **Cmt 5 Eyl montaj günü** · Paz 6 Eyl pusula + ilk hover (2 uçuş) · 7–11 canlı algı, ilk tam prova · 12–13 tam prova ×2 · 14–16 sıkı prova · **Per 17 Eyl sürüm dondurma (mühür)** · 18 KESİN HAZIR · 19 yedek gün · 20 Adıyaman'a yolculuk · **Pzt 21 Eyl genel prova Adıyaman + FDR teslim 17.00** · 22–29 tutanak · **30.09–03.10 FDA**. Jetson satırları D-431 ile güncellendi (6 Eylül kurulum kartta yapıldı, FPS GEÇTİ). Gerçekleşme: 5 Eylül'de Jetson takılmadı, uçuş yapılmadı ("uçalım" reddedildi); ilk hover Pazar 6'ya bırakıldı (Bölüm 4 §4.10.4; Bölüm 6 §6.5.2). 6 Eylül sonrası uçuş logu FDR'de **yoktur** (BEYAN GEREKLİ, Bölüm 6 kanıt dizini).
- **Uçuş bütçesi hesabı (§2.2.5.5):** gerekli ≥ 7 uçuş, günde ≤ 2 ⇒ ≥ 4 uçuş günü; plan ≥ 6 gün ayırır; pay 2 gün. Kaybedilen gün sayısı öngörülmemiştir.

### 3.5 Revizyonlar (§2.2.5.1–§2.2.5.2, seçme)

Donanım: Pixhawk 6C (DDR şeması 6X ile çelişiyordu); Jetson Orin NX → ~~Nano 4GB~~ **Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Python 3.12; D-431); M10 → M9N; Arducam → RPi HQ (aynı IMX477); Mauch → FCHUB-12S V2 + PM02 (sahada PM06); TBS Crossfire → FlySky FS-i6/FS-iA6B (iBUS); motor sabit kanat X2216 ×2 → çoklu rotor (7 Eylül: X2220 980KV V3 ×4, BEYAN); ESC 80 A plan (sahada "60 A V2"); pil 4S 10 Ah (günde 2 uçuş); paraşüt/servo/pitot FDA aracında yok; **acil güç kesme anahtarı yok — pil fişi** (REQ-25…31 takımın kendi DDR gereksinimi, final için açık). Yazılım: YOLOv8-seg nano/NCNN → **YOLOv8m-seg v36, PyTorch, conf 0,30, imgsz 512**; iki karar yolu (`analyze_path` üretim, `rota_bul` tanısal); çoğullayıcı zorunlu (`CONTRACTS.md §7.4`); kamera köprüsü; HB dedektörü bağlandı (D-386); `--fda` kipi; süre sabitleri 900/600/600 s.

### 3.6 Riskler (§2.2.7) ve açık kalemler (§2.2.8)

Riskler: Nano yığını (0,61 FPS) → 6 Eylül'de kapandı (tablo satırı hâlâ "açık; 5 Eylül'de ölçülecek" yazar — bölüm bu satırı güncellememiştir, DOĞRULANAMADI); yanlış güzergâh = 0 puan → histerezis + hakem ekranı; 10 dk → 221,5 s bütçe; tek pil → 2. pil kararı kaptanda; gerçek arena görüntüsü yok → **kapanmadı**; acil kesme anahtarı yok → açık. Açık kalemler: DDR teslim/puan teyidi, DDR takvim sayfası, kutu açılış teyidi, Adıyaman izni, 551/425 kaynağı, defter saati, Nano FPS (kapandı).

---

## 4. BÖLÜM 5 ve BÖLÜM 7 — Üretim ve Bütçe

### 4.1 Üretim (Bölüm 5, 15 puan)

- **Yöntem:** FDA aracının tüm yapısal parçaları FDM 3B baskı (Bambu Lab X1 Carbon + P2S, 0,4 mm nozul); kompozit/CNC/sac kullanılmadı; final aracı için yöntem seçilmedi (§5.1, §5.1.6). Özgünlük: yerel `.SLDPRT/.SLDASM` (Drone_Arm 134 593 B, Drone_Dome 2 310 497 B, Assembly 484 241 B vb.); imzalı beyan BEYAN GEREKLİ (§5.1.2).
- **CAD künyesi (§5.1.3, STL'den ölçüldü):** Kol ×4 (1 834 üçgen, 174,90×8,00×174,90 mm — çapraz yerleşim, gerçek boy DOĞRULANACAK); üst çerçeve 182,98×4,00×182,98; alt çerçeve 190,00×8,00×190,00; kubbe 18 456 üçgen, 182,98×78,00×182,98; ayak ×4; GPS tutucu; TPU ped ×4 (STL depoda yok). CAD kütlesi BEYAN GEREKLİ.
- **Reçeteler (§5.1.4):** 8 plaka; 7'si ABS, 1'i TPU 95A; Bambu Studio 02.07.01.62. 🔴 **Malzeme çelişkisi (§5.1.5):** beyan "ABS-CF siyah", dilimleyici artefaktları düz ABS (`type="ABS"`); çözülmedi, kaydedildi.
- **İmalat süresi (§5.2.1, §5.3):** yalnız üst çerçeve plakasının G-code'u var: **1 sa 23 dk (model) / 1 sa 30 dk 16 sn (toplam), 55,86 g, 22,33 m**; diğer 7 plaka ÖLÇÜLEMEDİ; toplam süre ve iş gücü tahmin **yazılmadı**.
- **Montaj planı (§5.2.2–§5.2.4):** 5 Eylül 09:00–12:30; her adıma kabul ölçütü (VIBE < 30, pusula ofseti < 300, CG ± 1 cm, Pixhawk gücü 5,1–5,3 V, Jetson 5,0–5,2 V). Sahada: PM06 8 pin → 6 pinli kablo; RC alıcı `CH6` → `i-BUS SERVO`; ESC "60 A V2".
- **Pixhawk yapılandırması (§5.2.6):** `arducopter_fda.param` 31 parametre (Copter-4.5 kaynağından), `fda_gorev.waypoints` 8 satır (TAKEOFF 32 m → 4 köşe → LOITER 60 s → LAND); `tests/test_faz_b_pixhawk_sablon.py` 12 test; kötü-durum bütçesi 221,5 s ≤ 600 s; firmware **4.5.7** sabit (4.7.1'de 9 parametre yok); `RC_PROTOCOLS` 4 → 1 geri alınmadı; koordinatlar yer tutucu (Null Island) — Adıyaman'da girilecek.
- **Görev bilgisayarı (§5.2.7):** 3 Eylül planı Nano 4GB/venv38/14 cp38 tekerlek (51 dosya, 246 MB) → 6 Eylül kart Orin Nano çıktı, plan **uygulanmadı**; `~/venv312`, GPU torch 2.11.0+cu130; `.engine` derlendi (57 283 989 B) ama D-303 denkliği DÜŞTÜ → uçuş `.pt`; ONNX GPU HATA. Kamera FOV ÖLÇÜLMEDİ (`--fov 78` yapılandırma varsayılanı).
- **Yazılım üretim hattı (§5.2.8):** v36 `.pt` 54 788 636 B; paket aynası 18 dosya; 6 systemd birimi; saha belleği 405 dosya · 1,27 GB; **mühür basılmadı** (`DONDURULMADI`, exit 3; planlı 17 Eylül).
- **Üretim kapıları özeti (§5.2.9):** 9 kalem ölçüldü/geçti; ÖLÇÜLEMEDİ: FPS (6 Eylül kapandı), kamera FOV, t_hazırlık ≤ 900 s, gerçek kütle/CG, FEM sonucu, `.engine` (6 Eylül güncellendi).
- **Final aracı (§5.2.10):** sabit kanat CAD var, imalat başlamadı; **mancınık CAD/analiz yok**; paraşüt temin kaydı yok; **İKA gerçek motor sürücüsü yok**; çift acil güç kesme yok.
- **Hata prosedürleri (§5.4):** Y-5-M04 = **YOK**; beş artefakt sinyali (H1 `bed_temperature_too_high_than_filament`, H2 destekli üç plaka, H3 kol reçete farkı, H4 motor delik uyumu X2220 ile DOĞRULANMADI, H5 fire kaydı yok).
- 🔴 **Diskalifiye riski (§5.5.1):** kol 1–2 (0,20 mm / %15 grid / 2 duvar / 5-3 kabuk) ile kol 3–4 (0,16 mm / %40 gyroid / 6 duvar / 7-7) **farklı reçete**, gerekçe kayıtta **YOK**; SGGS'de "gerekliliği ispatlanmamış değişiklik" sayılabilir. Diğer gerekçesiz revizyonlar: PLA → ABS (ayak/GPS), TPU ped eklenmesi, plaka bölünmesi.
- **FEM (§5.6/E1):** 48 990 düğüm / 27 391 eleman / 146 970 DOF, 3 s; sonuç veri tabanı 33/32 bayt → **ÖLÇÜLEMEDİ**; "imbalanced force … inertia relief" uyarısı.
- 20 BEYAN GEREKLİ satırı (§5 sonu).

### 4.2 Bütçe (Bölüm 7, 10 puan) — yalnız ana rakamlar

- **Temel ölçüm (§Y.2):** `grep -rInE "₺|fatura|birim fiyat|sipariş no"` → FDR/ dışında **0 eşleşme** (3 Eylül). Depoda tek bir fiyat, fatura, sipariş kaydı yok; **parasal sütunların tamamı BEYAN GEREKLİ**, yüzdeler HESAPLANAMAZ. Yönergenin beş maddesinden dördü (7.2–7.5) sayısal olarak kapanamıyor.
- **Tablo A** (FDA aracı BOM): **27 satır** (A1–A27; önceki "26" hatası düzeltildi); tedarik durumu tam; kütle 5 Eylül'de tartılmadı.
- **Tablo B** (DDR aviyonik BOM): **26 satır** (numara 25 atlanmış), toplam **2293 g**; yön dağılımı: azaltıcı 6 · nötr/azaltıcı 1 · artırıcı 2 · nötr/artırıcı 1 · nötr 1 · ertelendi 9 · değişmedi 4 · açık borç 1 · gerçekleşecek 1. 26 kalemin **22'sinde** değişiklik (§7.5.4).
- **Tablo C:** 8 plaka, 2 yazıcı, ABS + TPU; ölçülen tüketim yalnız 55,86 g / 1 sa 30 dk 16 sn.
- **Tablo D** (tedarik listesi): 12 kalem (D10/D11 6 Eylül'de gereksizleşti); **Tablo E** (ertelenen zorunlu sistemler): 10 sistem, **bugün 0 harcandı**.
- **BOM kapsam denetimi (§7.1.6):** **İKA ve Mancınık için kalem düzeyinde BOM hiç yazılmamıştır** → yönergenin "tüm" şartı karşılanmadı.
- **Ana kalem grupları (§7.3.3):** G1–G7 örtüşmesiz (3+3+4+4+2+9+2 = 27); yapısal üretim 9 kalem (%33,3 kalem adedi payı — bütçe payı değil). G8–G12 Tablo A dışı.
- **Sapma sebepleri (§7.5.1):** S1 araç sınıfı farkı (çoklu rotor DDR'de yoktu); S2 tedarik zorunluluğu; S3 üretim revizyonu.
- **Ayni kaynak (§7.5.3):** **≈ 14,8 saat GPU** sonuçsuz/reddedilen eğitim (8,6 = 6,4 v31 + 1,18 T128 + 1,04 T128-B; ve 6,19 v8 RED).
- Şartname: maddi destek %25 (DDR sonrası) / %75 (FDA sonrası); SGGS 05.02.2027; Ek E.1 bütçe kayıt şeması; 21 BEYAN GEREKLİ.

---

## 5. TEST_SPECS.md — kapı tanımları

- **Temel kural:** "Çalıştırılmayan bir kapı geçti sayılmaz. Kanıt = komut + gerçek çıktı + çıkış kodu." Yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`; çıplak `python` Windows Store saplamasıdır, sessizce hiçbir şey yapmaz (§0).
- **Genel kapı (§1):** `codes/test_rota_sentetik.py` → `SONUC: 15/15 dogru`, exit 0; düşerse görev geri alınır, `REVIEW_LOG.md`'ye yazılır. 15 sahne = 5 harita × 3 senaryo (`simulation/scripts/arena.py`), maske kusursuz → düşüş **mantık** hatasıdır. Beş koşul: doğru `yol_no`, `durum == "ACIK"`, ≥ 2 waypoint ve ihlal yok, waypoint aralığı ≤ `wp_aralik_px + 1`, uçlar ankorlu. Ölçek MPP 0,10 m/px, tuval 500×500. Determinizm `zlib.crc32`.
- **Distance transform şartı (§2):** `R_GEREKLI_M = 0,70/2 + 0,25 + 0,50 = 1,10 m`; `DIST_MASK_PRECISE` zorunlu; doğrulama C-uzayında (ham maskeyle 15 rotanın tamamı geçersiz çıktı); `mpp=None` kare ölçüm dışı.
- **Kapı kayıt defteri (§3):** Genel (15/15, exit 0) · Test paketi (tümü OK) · Temiz klon (`git worktree` sonrası `--help` exit 0) · Bozulma dayanıklılığı (`--bozulma`, bariyerin %10'u görülse bile 15/15) · Rota güvenliği (`test_rota_guvenlik.py --hepsi`: enjekte kipte ihlal 0, ham kipte > 0,10) · Görsel kanıt (sıfır rota → `OLCUM_YOK` + exit 1) · Anayasa madde 4 (scipy/skimage/sklearn 0 eşleşme — ⚠ FDR §4.2.4 #1 bu komutun `-E` kipinde `\|` yüzünden kör olduğunu ölçmüştür, D-15) · Monotonluk `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` ihlal 0 · Kuyruk ayrıştırma.
- **Kapı tasarım kuralları (§4):** 4.1 boş kapı yasağı (mutasyon: düzeltmeyi geri al → test düşmeli; "11 görevin tamamına uygulandı, hiçbiri boş çıkmadı") · 4.2 çekimserlik kapısı (`enjekte_karar_var == 0 → OLCUM_YOK → exit 1`) · 4.3 güçsüz test uyarısı ve payda uyarısı (karar başına ihlal 1,00 iken havuz 0,24 raporlanmıştı) · 4.4 kâhin bağımsızlığı (mpp sızıntısı dâhil) · 4.5 kâhin domain'i DOTA OBB (COCO 2 araç ↔ DOTA 93 araç) · 4.6 "kapı var ama açan yok" · 4.7 ikiz dosya kontrolü.
- **Çözünürlük kilidi (§5):** "Çıkarım `imgsz` = 640" (v17: 640 IoU 0,861; 960 → 0,034, kaplama %96,1). ⚠ FDR üretim modeli **imgsz 512**'dir (`navitas-seg-v36-512`, Bölüm 6 kanıt dizini) ve 512 → 640 denemesi **RED** edilmiştir (§4.8.2.2). TEST_SPECS §5 ile FDR arasındaki bu fark FDR'de açıklanmamıştır → **DOĞRULANAMADI** (TEST_SPECS satırı bayat olabilir).
- **Model ölçütleri (§6):** 1. karar doğruluğu (yanlış güzergâh = 0 puan), 2. moloza basma oranı; mAP/blocked AP50 **REDDEDİLDİ**. Gürültü tabanı maske sd 0,025–0,032 → 0,04'ten küçük fark gürültü; eşleştirilmiş test n=40, ≥ 35/40. Körlük tuzağı, havuz metrik tuzağı.
- **Performans referansı (§7):** PC RTX 5080, v20: imgsz 640 toplam p50 84,5 ms (11,96 FPS), costmap 51,2 ms darboğaz; gerekli 0,9–2,6 FPS; "Jetson'da hiç ölçüm yok" — ⚠ bu satır FDR'nin 6 Eylül D-431 ölçümüyle **bayattır**.

---

## 6. Test kültürü ilkeleri — FDR'de nasıl anlatılıyor

1. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Bölüm 4 §4.2.5 kural 2 ("§4.13 kalan test borcu"); §4.2.2'de çıkış kodu düzeyine indirildi (uygulanmayan mutasyon `exit 1`, D-370); Bölüm 6 §6.1.1 sözlük ve §6.2.5 ("600 saniyeye sığar" hükmü bilerek verilmedi; ÖLÇÜLEMEDİ listesi boşsa nöbetçi test düşer); Bölüm 2 §2.1.6 kural 2; TEST_SPECS temel kural ve §4.2 çekimserlik kapısı.
2. **p50/p95 raporlama.** FPS kapısı "p50 **ve** p95 ≥ 0,61" (§4.4, §4.8.2.3); uçtan uca gecikme p50 0,085 / p95 0,113 s (§4.9.5, Bölüm 6 §6.4.3); hub gecikmesi p50/p95/maks üçlü (§4.9.3); SiK RTT hedefi p95 < 0,2 s (§4.5). TEST_SPECS §7 PC referansı p50.
3. **Mutasyon kontrolü.** §4.2.2: "Kapı kaldırılınca DÜŞMELİ"; 10 satırlık mutant tablosu (`if False:` → 3 ERROR; 7/7 mutant; T207 MUT-1/2 → 3 FAIL; `--streamrate 8` silindi → K1 düştü; `_kanit_yaz` → 6/6; `§6.99.7` → T1; `--izinli-kaynak` → T1; sapma tavanı → 17, `_yerel_saat_adimi` → 5); dosya `cmp` ile bayt-eş geri yüklenir. Dürüst skor: `seri_hub` 13/25 → 24/25, tek kaçan `l_arizada_ogrenmez` bilerek testsiz ve **açık**. Ölçen araç da ölçülür (D-370 CRLF: 658 CRLF / 0 LF, M2′ hiç uygulanmıyordu). Bölüm 6 §6.2.2 adım 3; §6.2.4 #2 genel kapı üretim kolu 15/15 → 6/15. TEST_SPECS §4.1.
4. **Çürütücü turu (bağımsız ajan, Anayasa madde 19).** §4.2.3: "Bir iş, onu yazanın onayıyla kapanmaz"; her bulgu koşulmuş komut + ham çıktı (repro) ile gelir, mimar yeniden üretir. Turlar: D-383 (3 ajan, 4 gerçek kusur: 308 ms soket sabiti, YKS duvar-saati asimetrisi, şekil kapısı, nihai ret gerçek pedi öldürüyor), D-405 (5 mercek: 1 KRİTİK + 16 ÖNEMLİ + 18 KÜÇÜK + 5 çürütülemedi; KRİTİK: mühür CRLF'ye bağlıydı, Jetson'da 18/19 "ihlal"), D-407 (2 kusur), D-411 (raporun taslağı: 71 bulgu, 6 KRİTİK — 21 Eylül uçuş sanılıyordu, K6 %1,17 → %0,78, hub skoru 13/25 kalmıştı; 30 KÜÇÜK kapatılmadı), D-421 (13 tıkayıcı: "Onaylayan tur hicbir sey bulmazdi"). Yordam dürüstlüğü: D-407'de kredi bitti, repro betikleri ana döngüde koşuldu — "Ajan sayısı değil koşulan ölçüm kanıttır". Bölüm 2 §2.1.2 kural 3 (R8 icra dışı), §2.1.6 kural 3; Bölüm 6 §6.2.4 #3, #5, #6 ("amele mimarı çürüttü", D-422 §3). CLAUDE.md madde 19 korelasyonlu kör nokta: "İki tarafın ANLAŞMASI kanıt değildir".
5. **Vakum denetimi.** §4.2.4: yeşil test bir şeyi kilitlemiyorsa vakumdur; 7 ölçülmüş vakum (D-15 `grep -E` kör kapı, pozitif kontrol 0 → 46; D-375 FP16 bit-eş 1,0 "FARKSIZLIK ≠ DENKLİK"; K8'in doğuşu — v37 zinciri geçti, gerçek kare reddetti; K7 alt kümesi %54 belirsiz etiket; D-421 runbook 22/22 yeşilken EXIT=2; D-423 wheels 51 ≠ 48; D-425 TEYİT listesi `Missing 9 params`). Her ölçüm betiğinde vakum kapıları (T99 V1/V3/V4). TEST_SPECS §4.2–4.3.
6. **Kapı düşünce görevi geri alma.** CLAUDE.md madde 14 / TEST_SPECS §1: genel kapı düşerse görev **geri alınır**, nedeni `REVIEW_LOG.md`'ye yazılır. FDR §4.1.1 "Anayasa madde 14: her görevden sonra bu kapı koşulur; düşerse görev geri alınır". Uygulama örnekleri FDR'de: v37 **geri alındı** (D-332; §2.2.3); 640 denemesi RED; P2 S5 kod düzeltilip aynı eşikle yeniden koşuldu. **Karşı örnek:** v36 terfisi eşikleri geçmeden kullanıcı kararıyla yapıldı, "terfi geri alınmadı; geri alma kullanıcı kararıdır" (§4.8.2.1). Push kuralı: kapı düşmüşken push yapılmaz (CLAUDE.md §5).
7. **Kanıt silinmez, üstü çizilir** (D-373): §4.8.2.3 sızıntı düzeltmesi; Bölüm 2 §2.2.2.b ve §2.1.6 üç defter okuması; §4.13.2 "bu tablo silinmez, üstü çizilir".
8. **Her sayı bir artefakttan gelir** (§4.2.5 kural 1): bölüm sonu kanıt dizinleri (Bölüm 4: 71 satır; Bölüm 6, 2, 5, 7 ayrı dizinler); FDR grafikleri tablodan üretilir ve testle kilitlenir (§6.6).
9. **Sentetik ölçüm saha başarımı diye sunulmaz** (§4.2.5 kural 4; §4.8.1 kayıt cümlesi: "K0..K6 SAHA BAŞARIMI İDDİA ETMEZ").
10. **ÖLÇÜM ↔ BEYAN ayrımı** (§4.10.4, D-426 §6): "sahadan gelen 'oldu' kanıt değildir, yapıştırılan satır kanıttır".

---

## 7. 15 muhtemel jüri sorusu ve FDR'ye dayanan kısa cevaplar

1. **"Sisteminiz sahada çalışıyor mu?"** — FDR bunu iddia etmez. §4 giriş ve §4.15: hiçbir sayı "sahada çalışır" demez; gerçek arena karesi yok (A4), gerçek SiK ölçümü yok (A2), gerçek otonom uçuş yok (A3). Kanıtlanan: karar geometrisi 15/15·15/15; sentetik kabul 10/10; haberleşme gerçek MAVLink ve seri bayt akışında koştu; Jetson FPS kapısı 6 Eylül'de GEÇTİ (D-431).

2. **"Görüntü işleme doğruluğunuz nedir?"** — İki çerçeve: sentetik arena (n=260) K0–K8 hepsi GEÇTİ, K7 yayınlanan şerit 84/85 = %98,8 (§4.8.1); gerçek DJİ (arenaya dağılım dışı) test29'da ön kayıtlı ROTA ≥ 10 ve MASKE_YOK ≤ 10 eşikleri **geçilmedi** (8 ve 16) (§4.8.2.1). Karışıklık matrisi 7 Eylül: IoU zemin 0,4922 / engel 0,7400 (§4.8.4). Işık/gölge kesiti ÖLÇÜLEMEDİ.

3. **"Üretim modeli eşiği geçmeden nasıl terfi etti?"** — 2026-08-26 kullanıcı kararıyla (D-293); gerekçe gerçek karede yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3; bedeli K3 0→1, K4 1→4, K6 5→7, val82 FP 0→2, karar kararlılığı v35'ten kötü (14/260 vs 9/260). Eşikler değişmedi, `CONTRACTS §12` istisna satırı yazıldı, v35 yedek (§4.8.2.1, §6.3.3.1, §2.2.5.4).

4. **"Ön kayıt nedir, işe yaradı mı?"** — Eşik ve karar sırası sonuç görülmeden `ON_KAYIT` dosyasına yazılır, değişmez (D-107). 36 artefakt. Dört olayda iş gördü (640 RED, P2 S5, P5 H1, T61); bir olayda kullanıcı "izin veriyorum kurala rağmen" yazdı — ön kayıt bunu görünür kıldı (§4.2.1).

5. **"Testleriniz gerçekten bir şey koruyor mu?"** — Mutasyon kontrolü: kod bozulunca test düşmeli; 10+ mutant örneği, `cmp` ile bayt-eş geri yükleme (§4.2.2). Dürüst skor seri_hub 13/25 → 24/25, tek kaçan açık. Vakum denetimi 7 örnek (§4.2.4); kendi ölçüm aletlerinin kör olduğu durumlar (D-15, D-375, D-421, D-423, D-425) yazılıdır.

6. **"Bağımsız denetim var mı?"** — Anayasa madde 19 çürütücü turları: D-383, D-405, D-407, D-411, D-421 (§4.2.3). R8 rolü icra hattı dışında (§2.1.2). Ancak §4.13.3'te dört kalemde "yazan ile onaylayan aynı taraf" ve A11 (`--fda` kipi) bağımsız denetim borcu açıkça yazılıdır.

7. **"Gereksinimlerin yüzde kaçı karşılandı?"** — 45 satır: KANITLI_TEST 32 (%71,1), İNSAN-DONANIM 7 (%15,6), KOD_VAR_TEST_YOK 4 (%8,9), ÖLÇÜLEMEDİ 2 (%4,4) (§6.6.1–§6.6.2). Uyarı: %71 "kanıtlı" = kapılar koştu ve ayırt edici; "sahada çalıştı" değil (§6.6.6). 11 açık gereksinim A1–A13 (§6.5.1).

8. **"Doğrulama yöntemleriniz?"** — 66 atama: test 39, gözle muayene 11, simülasyon 7, hesaplama 5, analiz 4 (§6.2.3). Yalnız gözle muayeneye dayanan 3 yazılım borcu (müdahale −100, tekrar fırlatma, manuel mod) KOD_VAR_TEST_YOK.

9. **"Haberleşme gecikmesi ve menzil?"** — Uçtan uca p50 0,085 / p95 0,113 s (UDP loopback, 33 kare; §4.9.5); hub p95 ≤ 76,8 ms, kayıp 0/50 (§4.9.3); T207 ilk gecikme 0,30 s (§4.9.4). **Menzil, RTT, paket kaybı ÖLÇÜLEMEDİ**; 5 Eylül'de SiK "bağlandı" (BEYAN); DDR'deki ">%98, 300 m" iddiası tekrarlanmıyor (§4.5, §4.9.6).

10. **"Arıza emniyeti (RTL, DISARM, geofence) test edildi mi?"** — Sahada hayır (§4.12 ÖLÇÜLEMEDİ). Yazılım yolu kapılı: `test_iha_rtl_land.py` (6), `test_iha_komut_guvenligi.py` (10). 6 Eylül dökümünde `FS_THR_ENABLE` 1→3 ve `BATT_FS_LOW_ACT` 2→1 bilinçsiz değişmiş (D-428 §5b); RC failsafe 6 Eylül'de ölçüldü ve **DÜŞTÜ** (D-428 §2; Bölüm 6 §6.1.5, A13). Üçüncü döküm bekleniyor.

11. **"Görev bilgisayarında FPS yeterli mi?"** — Eşik türetildi: `1/(5·p)`, en kötü uçuş p = 0,326 → 0,61 FPS (§4.8.2.3). 6 Eylül Orin Nano: PT 1,35/1,06, engine 1,58/1,33 ≥ 0,61 GEÇTİ; ONNX HATA; engine↔pt D-303 denkliği 3/126 DÜŞTÜ → uçuş `.pt` (§4.4, §4.13.1). Sınır: kareler diskten, CSI kamera bağlı değil.

12. **"Takviminiz DDR'ye uygun mu; 21 Eylül'de ne olacak?"** — FDR teslim 21.09.2026 17.00 uygun (`test_fdr_takvim_kapisi.py` 4/4). 21 Eylül aynı zamanda takımın Adıyaman genel provasıdır; resmî FDA uçuşu 30.09–03.10 (tek atış). D-410: 21 Eylül uçuş günü sanılıyordu, düzeltildi (§2.2.1, §2.2.5.3). Mühür 17 Eylül; tek pil günde 2 uçuş, ≥ 7 uçuş / ≥ 4 gün gerekli, plan 6 gün (§2.2.5.5).

13. **"Kim ne yapıyor?"** — Rol bazlı R1–R8 (§2.1.3); yönerge isim yasağı (Y-2.1-M02). Atanmış roller R2 pilot ve R5 YKS; R2/R5 uçuş anı çakışması için ikinci kişi BEYAN GEREKLİ (§2.1.5). Üye sayısı ve danışman bilgisi açık kalem (§2.1.7). 5 Eylül'de sahada tek üye vardı (§4.10.4).

14. **"Entegrasyon: alt sistemler yerde birlikte çalıştı mı?"** — Yazılım kuru koşusu 9 GEÇTİ / 1 SAHİPSİZ (motor), exit 1 (§4.11). 5 Eylül tezgâh: Pixhawk 4.5.7 flash, GPS, RC iBUS, güç, pervanesiz motor testi ÖLÇÜM; Jetson, kamera ve NAVITAS yazılımı tezgâha **bağlı değildi** (§4.10.4). Gerçek kamera + Pixhawk + telsizin aynı anda koştuğu yer entegrasyonu FDR'de **yoktur**.

15. **"Bütçe ve üretim kayıtlarınız?"** — Depoda parasal kayıt 0 (§Y.2); Tablo A 27 satır, B 26 satır/2293 g, D 12, E 10; İKA ve mancınık BOM'u yok (§7.1.6); ≈ 14,8 saat GPU sonuçsuz (§7.5.3). Üretim: 8 plaka FDM, yalnız 1 plaka G-code'u (1 sa 30 dk, 55,86 g); ABS/ABS-CF çelişkisi; **kol 1–2 ↔ 3–4 reçete farkı gerekçesiz — SGGS diskalifiye riski** (§5.5.1); FEM sonucu okunamıyor (§5.6).

---

## 8. Yazılımcı takım üyesi için kritik uyarılar (FDR'den türetilmiş, yeni iddia yok)

- Soru geldiğinde "sahada çalışır" demeyin; FDR'nin kendi cümlesi "Kanıtlanmamış olan tek şey en önemlisidir" (§4.15).
- Suit sayısı tarihe bağlıdır: 1896 (3 Eyl) → 2104 (4 Eyl) → 2138 (5 Eyl). Test dosyası 153 → 180. Defter 414/408 → 424/418 → 432/426. Hangi tarihi söylediğinizi belirtin.
- "ÖLÇÜM" ile "BEYAN" farkı FDR'de her yerde ayrıdır; 5 Eylül motor yönü 4/4, SiK bağlantısı, ESC/PM06 künyesi **BEYAN**dır.
- TEST_SPECS.md'nin "imgsz = 640" ve "Jetson'da hiç ölçüm yok" satırları FDR ile çelişir/bayattır (DOĞRULANAMADI); jüri önünde FDR'nin sayılarını (imgsz 512, 6 Eylül FPS) esas alın.
- Açık kalemler konuşulurken §6.5.1 A1–A13 ve §4.13.1'in 18 satırı ezbere bilinmelidir; FDR bunların hiçbirini "sorun çıkmadı" diye kapatmaz.
