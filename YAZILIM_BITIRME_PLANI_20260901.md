# YAZILIM BİTİRME PLANI — 1 → 21 Eylül 2026 (v2, şartname-taramalı)

> **Emir (kullanıcı):** aviyonikler **5 Eylül Cumartesi** geliyor; şartnameye
> göre **21 Eylül'de KESİN HAZIR** olunacak; gerçek test **30 Eylül TEK ATIŞ**.
> Görüntü işleme DAHİL tüm yazılım kapsamda. **Yazan: Claude 2 — mimar.**
> Dayanak: 3 kollu workflow analizi (wf_5c5e6d65) — şartname yükümlülük
> çıkarımı (45 madde) + repo karşılık haritası + borç envanteri. v1'in P1–P7
> paketleri korunur; bu sürüm şartname 6.x katmanını ve Gazebo/sim paketini
> ekler. Her iş kapılıdır; kapısız iş "bitti" sayılmaz.

## 0. Şartnameden çıkan ve planda KARŞILIĞI OLMAYAN yükümlülükler (yeni)

| şartname | yükümlülük | plandaki yeri |
|---|---|---|
| §6 s.19 | Yarışma İHA'sı **SABİT KANAT** (mancınık kalkış + paraşüt iniş); FDA'daki VTOL ayrı konfigürasyon | bilgi — uçuş kontrolcüsü tarafı; yazılımımız platformdan bağımsız (algı/karar/haberleşme), Faz B |
| §2.2.4 + SS7 | Paraşüt birincil **otonom**; YKS'de **manuel yedek tetik** (−50 ceza bilgisiyle, onay diyaloglu) | **P9a** |
| §6.2 s.22 | Fırlatma hakem onayı sonrası: **arming/onay adımı** (erken fırlatma kilidi) | **P9b** |
| §2.2.3 | Güzergâh aktarımı **İHA havadayken** tamamlanmalı; iniş, aktarım teyidi olmadan başlamaz | **P9c** (kanıt: YKS'de "aktarım tamam + İHA havada" göstergesi; İKA ACK zinciri mevcut) |
| §6.2 s.22 | **thazırlık ≤ 900 s**; her 30 s tasarruf +1 puan → tek-komut açılış + ölçülmüş süre | **P9d** |
| §6.2 s.22 | Hands-off sonrası kararlılık (fiziksel müdahale −100) + **hızlı reset/tekrar fırlatma** durum sıfırlama | **P9d** kapsamında runbook + reset yordamı |
| SS7 Pgörev | İKA görevi **brandaya FİZİKSEL TEMAS** ile biter — sınırda durmak 0 puan | **P9e** (ika_nav varış davranışı) |
| §6.1 | Sürüm dondurma: yarışan yazılım FDS/SGGS/UHDR beyanıyla birebir; mühür sonrası müdahale yok | **Faz C** (dondurma yordamı, kayıt defteri künyesi zaten var) |
| §5.5 | UHDR: otonom harekât **video kanıtları** + nihai algoritma raporu (40 puan) | **Faz C** (hakem_log + saha provası kayıtları) |

**Muğlak maddeler → TEKNOFEST soru paketine eklenecek** (K3+K9'un yanına):
(1) görev bitişi "HB sınırına girme" (§2.2.6) mi "brandaya temas" (SS7) mı;
(2) İHA→İKA aktarımında YKS üzerinden **röle** kabul mü, doğrudan link mi zorunlu;
(3) manuel paraşüt (−50, §2.2.4) ile "manuel müdahale = uçuş başarısız" (§6.4) sınırı.
Cevap gelmezse **fail-safe yorum**: temas hedeflenir, doğrudan İHA→İKA linki kurulur,
manuel paraşüt yalnız emniyet için son çare kabul edilir.

## 1. Görev akışı ↔ yazılım durumu (harita ajanı doğrulamalı)

| adım | bileşen | durum |
|---|---|---|
| Mancınık fırlatma → otonom geçiş | Pixhawk (repo dışı) | **AVİYONİK** — Faz B'de yapılandırma + runbook |
| Telemetri (irtifa→mpp, karar_yas) | `inis_kaniti`, `rpi_inference` | kod+test var, canlı akış YOK (pymavlink kurulu değil) → **P1** |
| Algı→karar→telsiz | v36 + `analyze_path` + `KararYayinci` | ✅ kapılı (HB hedefli, p95 113 ms, zincir ÜRETİME ALINIR) |
| YKS hakem ekranı | `yks_gui` | ✅ kapılı · başlatma runbook'u YOK → **P4** · paraşüt/arming yok → **P9** |
| İniş kanıtı → İKA kilidi | `iha_inis_yayinci`, §2.2.5 latch | ✅ kapılı · Jetson yordamı yazılı değil → **P4** |
| İKA_GO → intikal → HB | `ika_receiver`, `ika_nav` | mantık ✅ · gerçek sürücü YOK (T149) → **P3** · temas davranışı → **P9e** |
| SiK telsiz | `SerialLink` | yalnız sahte seri; framing sınanmadı → **P2**, RF Faz B |
| Saha video (H3) | DroidCam / `rpi_yayin` | kılavuz ✅ · algı hattına bağlama → **P6** |
| Gazebo simülasyon | `simulation/` (temel: trs-1342, 11 Tem) | ika_nav/arena ✅ · 7 betik + iha_flight KAPISIZ, yks_monitor TEHLİKELİ → **P8** |

## 2. İş paketleri

### Faz A — aviyoniksiz yazılım (1–4 Eylül)

**P1 · MAVLink katmanı CANLI** — ✅ **KAPANDI (2026-09-02 gece · D-387 + D-389).** İki bulgu mimar kararıyla (A1+A2, B1) kapatıldı; özgün G3/G5(2) ölçütleri gevşetilmeden geçti. Gerçek Pixhawk Faz B.
Kuruldu ve `scripts/sahte_pixhawk.py` + 14 nöbetçiyle gerçek çerçeveler
üzerinden koştu: G1/G2/G3b/G4/G6/G7/G8 GEÇTİ. **Koşumun bulduğu, D-389'la
kapanan iki bulgu:** (A) `yerde_mi` alçalmada 10 s son tarihe rağmen 0,002 s'de düşüyordu,
yayıncı tek kez çağırıp exit 3 veriyor → İHA_LANDED hiç yayınlanmaz;
(B) yabancı sysid trafiği irtifayı tamamen kesiyor (0/193 okuma) → bütün uçuş
NO_ROUTE. Ayrıntı + seçenekler D-387. Aşağıdaki özgün tanım korunur:
pymavlink kur (pip freeze yedeğiyle);
`sahte_pixhawk.py` gerçek MAVLink çerçeveleri (HEARTBEAT + GLOBAL_POSITION_INT
+ EXTENDED_SYS_STATE) bassın; irtifa→mpp→rota ölçeği + iniş latch'i uçtan uca.
**Kapı:** kuru koşu `hedef_konumu/olcek` halkaları sahte akışla GEÇTİ; saat
atlaması + kaynak-kimlik senaryoları.

**P2 · SerialLink radiosuz** — ✅ **KAPANDI (2026-09-02 · D-388).** Gerçek
pyserial bayt akışında koştu (iki uçlu SiK köprüsü): S1 ACK turu, S2 bayt bayt
parçalanma, S3 birleşme, S4 bozuk bayt kurtarma GEÇTİ. **Bir kusur bulundu ve
düzeltildi:** `FrameReader` tamponu sınırsızdı (1 MiB çöp → 1 MiB tampon);
tavan sözleşmeye girdi. RF ölçümü Faz B'de. Özgün tanım: pyserial + `loop://`:
framing/parçalanma/ACK
turu, bozuk-bayt kurtarma. D-383 §1 uyarısı kapanır (B2-G2 yalnız UDP-loopback'ti).
**Kapı:** SerialLink üstünde mutlu_yol eşdeğeri + bozuk-bayt enjeksiyon testi.

**P3 · T149 İKA sürücü soyutlaması (KRİTİK)** — ✅ **KAPANDI (2026-09-02 gece · D-390);** GercekSurucu arka ucu Faz B. Ayrıca gerçek kusur kapandı: navigate, subprocess zaman aşımında ÇÖKÜYORDU; artık fail-closed durur. Özgün tanım: `ika_surucu.py`:
`hiz_ver(v,w)` / `konum_al()` / `durdur()`, fail-closed (cevap yoksa DUR);
`GazeboSurucu` (mevcut gz yolu) + `SahteSurucu` (test) + `GercekSurucu`
iskeleti (Faz B'de dolar; o güne dek açık `DONANIM_YOK` reddi).
**Kapı:** T141 zinciri Gazebo sürücüsüyle bayt-eş; §2.2.5 kilidi SahteSurucu
ile uçtan uca; "donanım sustu → İKA durdu" testi.

**P4 · Runbook + kapı koşucusu tazeleme** — ✅ **KAPANDI (2026-09-02 gece · D-394):** SAHA_RUNBOOK.md kanonik + belge kapılı; hedef halkası T150 bağlamasıyla GEÇTİ (kuru koşu 9/10, tek kopuk: motor); saha_baslat.py (P9d) eklendi. Özgün tanım:  `saha_gunu_kontrol_listesi.md`
(v35/v34→v36); `iha_inis_yayinci` Jetson başlatma yordamı; `yks_gui` saha
başlatma satırı (bugün yalnız `--demo` yazılı); **`saha_kuru_kosu.py`
halka_hedef ölçütü BAYAT** (T150'nin `goruntu=` bağlamasını tanımıyor —
bugün koşulsa hedef halkası SAHİPSİZ der) → tazele.
**Kapı:** T154-kalıbı belge kapısı + kuru koşu 10 halka bugünkü HEAD'de GEÇTİ.

**P5 · T79/T91/T92 karar kararlılığı** — ✅ **KAPANDI (2026-09-03 gece · D-396):** yayın histerezisi (K=3) — azınlık gürültü çevrilmesi yayına sızmıyor (0/0), NO_ROUTE asla geciktirilmiyor; T79 kökü + T91 Faz C'de. Özgün tanım:  ön kayıt ÖNCE: N-kare histerezis
(şerit ancak K ardışık karede aynıysa değişir; NO_ROUTE anında, fail-closed).
**Kapı:** çevrilme 14/260 ↓, p95 karar gecikmesi ≤ mevcut + K·kare-süresi;
tazelik penceresi 5 s içinde; tüm kapılar yeşil.

**P6 · T18 DroidCam (H3)** — telefonla; `--camera` kaynağı DroidCam URL;
`kamera_dogrula` + ayna testi telefonla koşulur.
**Kapı:** canlı telefonda uçtan uca karar + YKS görünümü + 10 dk kesintisiz.

**P8 · Gazebo/sim el atma (YENİ — temel trs-1342'nin)** —
- **`comms/yks_monitor.py` EMEKLİYE**: OPEN_ROUTE'a "HAKEM ONAYI: ✓ (otomatik)"
  basıp ACK dönüyor — sahada yanlışlıkla açılırsa iki aşamalı hakem onayını
  DELER. Silinmez (madde 18): dosyaya çalıştırma kilidi (`--legacy-bilerek`
  bayrağı olmadan exit 2 + uyarı) + README notu. **Kapı:** kilit testi.
- **`iha_flight.py` davranış testi**: bugün yalnız mock'lanıyor; kendi
  davranışını (faz sırası, iniş tetiği) sınayan test yazılır.
- **7 kapısız sim betiği** (world_generator, drive_ika, mission_demo,
  mission_time, harita_onizleme, iha_perceive_all, iha_detect_send):
  CONTRACTS 11.1 gereği sahada kanıt sayılmazlar → tek **duman testi**
  (import + --help exit 0) yeter; kırık olan varsa onar ya da arşiv işaretle.
- **`comms/test_comms.py` + `drone/test_uctan_uca.py`** genel kapının dışında
  elle koşulan testler → `tests/` altına sarmalayıcı ile bağla (exit 0 kanıtı
  otomatik olsun).
- **Gazebo tam prova senaryosu**: fırlatma→tarama→tespit→aktarım→iniş→
  İKA_GO→intikal→HB temas zinciri navitas_sim ile bir bütün koşu; Faz C
  provalarının şablonu. **Kapı:** hakem_log çıktısında zincirin 8 fazı da
  damgalı.

**P9 · Şartname yeni yükümlülükleri (YENİ)** — 🟢 **a/b/c/e KAPANDI (2026-09-02 gece · D-391+D-393);** kalan: P9d (saha_baslat + reset, P4 ile birlikte). Özgün tanım:
- **a)** YKS **manuel paraşüt** butonu: onay diyalogu + "−50 ceza" uyarısı +
  hakem_log kaydı; İHA tarafına PARASUT komutu (protokole mesaj tipi —
  CONTRACTS'a yazılır, ACK'li).
- **b)** **Arming adımı**: YKS'de "fırlatma onayı" durumu; onay verilmeden
  görev başlangıç damgası atılmaz (erken fırlatma kilidi yazılım tarafında
  loglanır; fiziksel mancınık tetiği insan+Faz B).
- **c)** **Aktarım-havada kilidi kanıtı**: YKS panosunda "güzergâh İKA'ya
  ulaştı (ACK) + İHA henüz havada" birleşik göstergesi; iniş kanıtı bu
  ACK'ten ÖNCE gelirse kırmızı ihlal uyarısı.
- **d)** **thazırlık tek-komut açılış**: YKS+İKA dinleyici+izleyiciyi tek
  betikle kaldır (`saha_baslat.py`), açılış süresi ölçülür ve yazılır;
  hızlı **reset yordamı** (tekrar fırlatma için durum sıfırlama) runbook'a.
- **e)** **İKA branda-temas varışı**: ika_nav hedef davranışı HB sınırında
  durmak değil ped merkezine temas edecek şekilde; Gazebo'da temas kanıtı.
**Kapı:** her alt madde için test + CONTRACTS güncellemesi; genel kapı yeşil.

**P7 · Kapanışlar** — kuyruk hijyeni (T198/T190 bayat kutucuklar, T109 v34
metni); FDR sayfası son tazeleme (T150/D-386, p95 113 ms); mimar denetim
borcu (D-373..D-386 "Denetleyen: mimar bekleniyor" damgaları — Fable 5
oturumunda topluca denetlenir).

### Faz B — donanım günleri (5–6 Eylül, aviyonik + Jetson)

Gün-1 listesi (Jetson): `.engine` derleme (T16/T109) + gerçek FPS (T17,
eşik 0,61 türetilmiş) + `.engine`-PT karar denkliği. Aviyonik: gerçek
Pixhawk MAVLink akışı (P1'in sahtesi yerine), SiK 433 MHz RF ölçümü (P2'nin
gerçeği), İKA `GercekSurucu` doldurma (P3 iskeleti), mancınık/paraşüt/geofence
Pixhawk yapılandırması + sabit kanat görev planı (insan+mimar), arming
fiziksel zinciri.

### Faz C — entegrasyon, model, prova, dondurma (7–20 Eylül)

| iş | içerik |
|---|---|
| Saha provaları | Gazebo tam senaryo (P8) → gerçek donanımla tekrarlı prova; her prova hakem_log + video (UHDR kanıtı) |
| Model döngüsü | DJI Neo nadir çekim (İNSAN, kuyruk R-görevi) → T197 etiket → T153 ince beton şerit + T47 çim/toprak eğitim turu → kabul zinciri v37 adayı (K4c ön kayıtlı korluk kararıyla) |
| Arena üreteci | T199 kalan 2 deneme (K8 kararı) — model döngüsünü beslerse |
| Ölçek 2. katman | T88 arena sınırı dedektörü (mpp çapraz kontrol) — model turundan sonra |
| Karar iyileştirme | T101 serit_no çerçevesi, T61 orta çökme ölçütü, T52 özgün kayıt denetimi, T99 üretim imzalı ölçüm, S6 hedef tohumu — P5 sonuçlarına göre önceliklenir |
| Sürüm dondurma | §6.1: yarışan sürüm = beyan; künye kaydı + değişiklik yasağı başlangıcı (mimar kararıyla ~18 Eylül) |
| FDR/UHDR | Kanıt sayfaları final; algoritma raporu nihai model künyesiyle |

**21 Eylül: KESİN HAZIR** — dondurulmuş sürüm, tüm kapılar yeşil, runbook'lar
final, prova zinciri en az 3 temiz koşu. (30 Eylül tek atışa 9 gün tampon.)

## 3. Gün planı (Faz A)

| gün | işler |
|---|---|
| **Salı akşam** | ✅ T150/D-386 kapandı · plan v2 · pymavlink/pyserial kurulum |
| **Salı→Çarşamba GECESİ** | ✅ **VARDİYA (D-387→D-398):** P1+P2+P3+P4+P5+P8+P9a-e KAPANDI · mimar denetimi (10/10) · T42/T52/T190/T198 kapandı · SAHA_RUNBOOK + saha_baslat · kuru koşu 9/10 (tek kopuk: motor) · 1559 test |
| **Çarşamba** | T99 (üretim imzalı ölçüm hizası) · T61/T101 tasarım · TEKNOFEST sorularını İLET (paket hazır: `results/sartname_bosluk/TEKNOFEST_SORULARI_20260903.md`) · DJI çekim planla |
| **Perşembe** | Model döngüsü hazırlığı (T197 etiket aracı) · T75 kalan yarım · tampon |
| **Cuma** | P6 (DroidCam, kullanıcıyla) · TAM PROVA (kuru koşu + bütün kapılar + Gün-1 son kontrol) |
| **Cumartesi** | Faz B: DONANIM — Gün-1 (.engine T16/T109 · gerçek FPS T17 · denklik) + aviyonik (gerçek Pixhawk'la D-389 canlı doğrulama, SiK RF, GercekSurucu doldurma, İHA-CMD alıcısı/paraşüt aktarımı, sabit kanat görev planı + geofence + arming zinciri) |

## 4. İnsan görevleri (kullanıcıdan)

- K3+K9 sorusu TEKNOFEST'e (metin hazır) + **bu planın muğlak-3'ü eklenir** (§0).
- Cuma: telefon + DroidCam (P6, ~30 dk, birlikte).
- DJI Neo nadir çekim (Faz C model döngüsünün kilidi — ne kadar erken o kadar iyi).
- Cumartesi: donanım günü. Faz C'de saha provası günleri (tarihler birlikte).

## 5. Mimar kararları (bu planla; gerekçeli)

1. **pymavlink + pyserial kurulur** — bu katman bunlarsız sınanamaz; kurulum
   öncesi `pip freeze` yedeği. (Madde 4 üretim koduna dairdir; bunlar sınama
   ve telemetri katmanı bağımlılığıdır, `analyze_path` çekirdeğine girmez.)
2. **İKA sürücü arayüzü** sözleşmeye girer (fail-closed: cevap yoksa DUR).
3. **T79 histerezis** ön kayıt şartıyla; eşik sonuç görülmeden yazılır.
4. **yks_monitor emekliye** (silinmez, kilitle) — iki aşamalı hakem onayını
   deldiği ölçüldü; sahada yanlışlıkla açılma riski kapatılır.
5. **Sim betikleri duman-testi seviyesinde** tutulur (CONTRACTS 11.1: sim
   sahada kanıt değildir) — kapı enflasyonu yapılmaz.
6. **Muğlak maddelerde fail-safe yorum** (§0) cevap gelene dek bağlayıcıdır.
7. Model geçişi: Faz A/C ameleliği **Opus 5**; ön kayıt/eşik/sözleşme/dondurma
   kararlarında kullanıcıya **"Fable 5'e al"** denir.
