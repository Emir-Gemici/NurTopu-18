# GECE 7 EYLÜL 2026 — ÖN KAYIT (02:45, kullanıcı uyudu: "en mantıklı neler bulursan onu yap, durma")

> Ön kayıt kuralı (D-107): kapı ve beklenen sonuç **koşulmadan önce** yazılır; sonuç
> görülünce eşik gevşetilmez. Her iş bir amele ajanında (worktree), her çıktı bir
> çürütücüden geçer, sonra mimar kapıyı **kendi** koşar. Onaylayan mimar ≠ yazan ajan.
> Push yalnız `scripts/push_kapisi.py` ile (D-430).

## Seçim gerekçesi

Uçuşa 14 gün, FDR teslim 21 Eylül 17:00. Bu gece donanım yok (Jetson, saha, GPS
kilidi) → yalnız **yazılım ve belge** işleri. Yönergenin açıkça istediği ve **yazılımla
kapanabilen** kalemler öne alındı; ölçüm isteyen (arena karesi, RF, FPS) alınmadı.

> **03:05 EKİ — iki gelişme, dört yeni iş (koşmadan önce yazıldı):**
> (a) `GELISTIRICIYE_20260906/` paketi geldi: Jetson **Orin Nano Dev Kit 4 GB / JetPack 7.2.1 /
> Py 3.12** çıktı (Nano varsayımı yanlış), kurulum 6 Eylül'de yapıldı, FPS kapısı geçti, engine
> derlendi ama D-303 denkliği düştü → uçuş `.pt`. (b) 5005/5006'yı tutan süreçler **10.0.0.x yer
> tutucu IP'li** — test süitinin sızdırdığı süreçler; D-427/D-430 teşhisi eksikti.

| # | iş | neden şimdi | kapı (önceden yazıldı) |
|---|---|---|---|
| G0a | **Jetson paketi mekanik birleştirme**: registry engine sha (tek satır), manifest + K5 komut düzeltmesi, FP32 engine girdisi defterden çıkar (K4), `test_t143` yer tutucu ↔ gerçek sha (K3), yeni belgeler/betikler/kanıt → `jetson_paket/`, `results/jetson_20260906/`; paketin "D-428"i **D-431** olarak deftere | Ölçülmüş kanıt (FPS, engine, 10 dk) depoya girmeli; numara çakışması var | `test_t143`, `test_uretim_modeli_hizasi`, `test_model_registry`, `test_faz_b_surum_dondurma`, `test_t202`, `test_jetson_paket_defteri`, defter bütünlüğü — OK; engine sha256 = `bb9bd868…0300`; paket aynası bayt-eş |
| G0b | **Künye düzeltmesi, operasyon belgeleri** (K1/K9/K10): plan, gün planı, kart, runbook, Nano belgesine GEÇERSİZ bandı, `bellek_hazirla` insan parçaları, `test_faz_b_nano_kurulum` | Sahaya giden her belge yanlış kartı anlatıyor | ilgili test dosyaları OK; kalan "Nano 4GB/JetPack 4.6" satırları ya bant altında ya tarihli tarihçe (liste) |
| G0c | **FDR + açık kalemler + README**: künye; kalem 4 (FPS ÖLÇÜLDÜ), 5 (arka uç .pt GPU), 15 (engine denkliği DÜŞTÜ), 7–8 (`20260906.param`); Y-4-M04 Jetson satırı; README sayı künyesi; ESC kalibrasyon yordamı (D-428 §3) | Rapor yanlış kartı ve ÖLÇÜLEMEDİ'yi taşıyor; ölçüm var | FDR kapıları 3/3; her sayı `results/jetson_20260906/…` artefaktından; "arena değil / T66 değil" sınırları korunur |
| G1b | **Test süiti süreç sızdırıyor**: runbook kapısı yer tutucu IP'lerle `yks_gui`/`ika_nav` başlatıp öldürmüyor → sonraki süit 5005/5006'da düşüyor | Push kilidinin gerçek kökü; iki gecedir yanlış teşhis | `test_runbook_komutlari_kosuyor` OK **ve** koşum sonrası 5005/5006/5007 boş; nöbetçi test (süreç sayısı artmaz); mutasyon: kill kaldırılınca düşer; T210 |
| G1 | **T209** — `comms/test_comms.py` loopback'i 5005/5006 yerine ephemeral porta bind etsin | YKS açıkken tam süit koşamıyor; bu gece iki kez push kilitlendi, bir kez kural ihlali (D-430) | `test_p8_sim_katmani` 5005'i tutan sahte soket açıkken **geçer**; assert silinmez; mutasyon: ephemeral geri alınınca **düşer**; tam süit YKS açıkken **OK** |
| G2 | **Parametre şablonu**: `RC_SPEED,400` (plan §0.2 "PWM 400 Hz"; Skywalker 60A V2 spec ≤ 432 Hz; kart 490'daydı) + başıboş `SERVO1–8/13–16` motor fonksiyonları **0** + ölçülen AUX eşlemesi `SERVO9–12 = 36,34,33,35` **TEYİT** olarak | D-429 §4 kararı; 4 ESC BEC paralel rayda + spec dışı PWM iki gerçek risk | `test_faz_b_pixhawk_sablon` yeni satırları kilitler (NEDEN'siz satır yok, TEYİT ↔ README metin kilidi); mutasyon: `RC_SPEED` silinince **düşer**; README §3 TEYİT listesi güncel |
| G3 | **Sınıf bazlı karışıklık matrisi** (Y-3.3.4-M02 / Y-4-M08 "doğruluk matrisleri") — DOĞRULAMA kümesinde (CONTRACTS §12) **CPU** çıkarımla, piksel düzeyi, v36 | Yönergenin açık isteği, bugün ÖLÇÜLEMEDİ; hesapla kapanır, GPU gerekmez | `results/gece_20260907/karisiklik/` altında `.json` + `.png` + üreten komut; satır/sütun toplamları küme boyutuyla **tutar**; FDR §3.3.4.2 ve §4.8.4'e tarihli satır; **"gerçek arena karesi yok" sınırı kalır** (bu küme DOĞRULAMA kümesidir, saha değil) |
| G4 | **Akış diyagramları** (Y-3.3.4-M01) — İHA ana döngü, komut alıcı, iniş kanıtı, YKS, İKA; **koddan**, her düğüm fonksiyon + dosya:satır; Mermaid → SVG (Chrome headless) → `FDR/sekiller/` | Yönerge "detaylı akış diyagramları" ister; bugünkü tur 2 düzenlemeyi satır numarası tutmadığı için reddetti | çürütücü her düğümün dosya:satır'ını **açıp** doğrular (≥ %95 tutmalı, tutmayan düğüm silinir); SVG'ler PDF'e giriyor (`fdr_pdf_uret` `<img>`); "koddan türetildi (commit)" notu |
| G5 | **Görseller**: (a) Y-6-M06 uygunluk **pasta grafiği** — §6.6.2 verisinden (32/7/4/2) SVG; (b) Y-2.1-M01 **organizasyon şeması** — R1–R8 rol bazlı, isimsiz, icra yetkileri §2.1.3'ten | İkisi de YOK/KISMEN, ikisi de veri hazır | SVG sayıları §6.6 tablosuyla **birebir**; şemada isim **0**; PDF'te görünür |
| G6 | **Renk kodlu bağlantı şeması** (Y-3.3.1-M01) — İHA, **ölçülen** topolojiden: PM06→POWER1, ESC×4→AUX1–4 (M4,M2,M1,M3), M9N→GPS1 (pusula/düğme), SiK→TELEM1, Nano UART→TELEM2, iBUS→PPM/SBUS RC, kamera CSI; güç/UART/PWM/I2C/CSI ayrı renk | Yönerge ister; topoloji D-426/428/429 + `arducopter_fda_20260906.param` ile ölçüldü | her bağlantı D-kaydı ya da param satırıyla **kaynaklı**; kaynaksız bağlantı çizilmez; ölçülmeyen (Jetson güç, kablo kesitleri) "DOĞRULANACAK" etiketiyle; İKA şeması **çizilmez** (aviyonik yok) |
| G7 | **Belge tutarlılığı**: `arducopter_fda_20260905.param` atıfları → `20260906` (dosya artık var); README sayı künyesi → `results/push_kapisi/<ts>/tam_suit.txt` artefaktı; ACIK_KALEMLER §1 kalem 7–8 | Bayat atıf = raporun kendi kuralının ihlali | `test_fdr_sarkan_atif_kapisi` 7/7; grep `20260905.param` → 0 |

**Yapılmayacaklar (bilerek):** simülasyon (gz yok), Jetson, RF, arena karesi, Bölüm 1
özeti (diğerleri kesinleşmeden), `MOT_SLEW_UP_TIME`/failsafe parametre kararları (Emir).

**Kapanış kapısı (mimar koşar):** genel kapı 15/15 · 15/15; tam süit OK; FDR kapıları
(yarışma adı, sarkan atıf, takvim); isim taraması 0; `scripts/push_kapisi.py` ile push.
Her G-iş ayrı commit; düşen G-iş **atlanır, gizlenmez** — bu dosyanın sonuna sonuç tablosu.

## Sonuç (sabah doldurulur)

| iş | durum | kanıt |
|---|---|---|
| G1 | | |
| G2 | | |
| G3 | | |
| G4 | | |
| G5 | | |
| G6 | | |
| G7 | | |
