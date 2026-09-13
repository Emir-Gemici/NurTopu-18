# BÖLÜM 6 — GEREKSİNİM İZLENEBİLİRLİĞİ VE DEĞERLENDİRME (10 puan)

> **NAVITAS** · TEKNOFEST İleri Otonom Sistemler Tasarım ve Operasyon Yarışması
> Şartname §5.3.1, Tablo 4 — Bölüm 6. Kapsam: şartnamenin yazılıma ve sistem
> davranışına düşen **her hükmünün** tek tek izi; hangisinin kanıtı var,
> hangisinin yok, hangisi hâlâ açık ve **ne zamandan beri**.
>
> Bu bölüm bir uyum beyanı değil, bir **kapı dökümüdür**. Her satırın kanıt
> sütununda ya koşulan bir test dosyası ya da `results/` altında duran ham bir
> ölçüm çıktısı vardır. Kanıtı olmayan satır "karşılanıyor" yazılmaz.
>
> **Yönerge karşılığı:** FDR Hazırlama Yönergesi *Bölüm 6. Gereksinim
> İzlenebilirliği ve Değerlendirme (10 PUAN)*. Yönergenin bu başlık altında
> saydığı **altı hüküm** aşağıda altı alt başlıktır ve numaraları yönerge
> haritasındaki kimliklerle (`Y-6-M01` … `Y-6-M06`) eşlenmiştir
> (`FDR/YONERGE_HARITASI.md`, metin `results/fdr_sablon/fdr_yonerge_metin.txt`).

---

## 6.1 Gereksinimlerin hangi ölçüde ve ne şekilde karşılandığı

> `Y-6-M01` — *"Bu başlık altında sistem gereksinimlerinin hangi ölçüde ve ne
> şekilde karşılandığı ayrıntılı olarak açıklanmalıdır."*

### 6.1.1 Durum sözlüğü (dört değer, gevşetilmez)

| durum | anlamı | ne gerekir |
|---|---|---|
| **KANITLI_TEST** | Hükmü karşılayan üretim kodu var **ve** o davranışı sınayan, `tests/` altında koşan bir kapı var. Kapıların çoğu ayrıca **mutasyonla** ayırt ediciliğini göstermiştir (kod bozulunca test düşer). | koşulan test + ham çıktı |
| **KOD_VAR_TEST_YOK** | Davranış üretim kodunda var, ama o davranışı doğrudan zorlayan bir kapı yok; ya da yalnız birim düzeyinde sınanıyor, entegrasyon sınanmıyor. | — |
| **ÖLÇÜLEMEDİ** | Hüküm repo dışındadır (uçuş kontrolcüsü, gerçek telsiz, gerçek arena) ya da ölçüm için gereken donanım/veri henüz yoktur. **ÖLÇÜLEMEDİ, GEÇTİ demek değildir.** | ölçüm tarihi + neyin eksik olduğu |
| **İNSAN-DONANIM** | Hüküm yazılıma düşmez: fiziki montaj, ağırlık, mühür, yük, hakem gözlemi. Sorumlu insandır; yazılım en fazla kayıt tutar. | — |

### 6.1.2 İki araç, tek yazılım — izlenebilirlik hangi araca aittir

Şartname iki ayrı doğrulama ister ve bu bölüm ikisini **karıştırmaz**:

| | §5.3.2 Görev Test Uçuşu | §2.2 Yarışma görevi |
|---|---|---|
| tarih | **30 Eylül – 3 Ekim 2026** (şartname Tablo 1) · prova **21 Eylül** Adıyaman | final haftası |
| araç | **çoklu rotorlu drone** — 3B baskı quadcopter, Pixhawk 6C, Jetson Orin Nano Developer Kit 4 GB (6 Eylül ölçüm, D-431; 3 Eylül beyanı 'Nano 4GB' yanlışlandı), RPi HQ kamera | **sabit kanat** + mancınık + paraşüt + İKA |
| kapsam | kalkış → tespit → YKS'ye aktarım + hakem onayı → iniş, **≤ 10 dk** | tam görev akışı, İKA dâhil |

Algı, karar, haberleşme, yer istasyonu katmanı **iki araçta da aynı kod**tur;
değişen uçuş kontrolcüsü yapılandırması ve gövdedir. Yer istasyonu ayrımı
`--fda` bayrağıyla tanır (`CONTRACTS.md §6.7`). Tablolarda "FDA" işaretli
satırlar görev test uçuşunda (30 Eylül–3 Ekim; provası 21 Eylül) doğrulanacak olanlardır; "final" işaretliler final
dalgasına aittir.

### 6.1.3 İzlenebilirlik matrisi — §2.1 ve §2.2 (görev akışı)

> Son iki sütun bu sürümde eklendi: **doğrulama yöntemi** (`Y-6-M02`) ve
> **yönerge kimliği** (`Y-`), raporun hangi bölümünün o hükmü taşıdığını
> gösterir. Diğer sütunların hücre metinlerine dokunulmadı.

| şartname maddesi | gereksinim | karşılayan bileşen | kanıt (dosya / test) | durum | doğrulama yöntemi | yönerge kimliği (Y-) |
|---|---|---|---|---|---|---|
| **§2.1** (R1) | "üç yoldan yalnızca bir tanesi açık bırakılacak… hangi yolun açık olduğu gizli" — açık şeridi görüntüden bulmak | `codes/rpi_inference.py::analyze_path` (en büyük bağlı bileşen + K-A uç-bant teması + A* tanık yol; yayınlanan `road` = darboğaz şeridi). Üretim yolu ilanı: `CONTRACTS.md §11.2-EK` | `codes/test_rota_sentetik.py` — **iki kol**, bugün koşuldu: KOL 1 (`rota_bul`, tanısal) **15/15**, KOL 2 (**üretim** `analyze_path`) rota üretimi **15/15** · yayınlanan şerit **15/15** (ön kayıt eşiği ≥ 14/15). Kilit: `tests/test_t156_genel_kapi_uretim_kolu.py` (15 test); şerit ekseni: `tests/test_k7_serit_dogrulugu.py` (27 test), `tests/test_t119_yayinlanan_road_kapisi.py` (5 test) | **KANITLI_TEST** | test + simülasyon (sentetik arena) | `Y-3.3.4-M01` · `Y-3.3.4-M02` |
| **§2.1** (R1-ek) | Üç güzergâh **adayının** ayrıştırılması ve K2/K3 ihlal denetimi | `codes/costmap_path_finder.py::koridor_adaylari` + `rota_dogrula` | `tests/test_koridor_etiketi.py`, `tests/test_koridor_genisligi.py` — ⚠ bu iki denetim **yalnız tanısal kolda** (`rota_bul`) koşar, üretim yoluna taşınmadı. Bu bir **yazılım borcudur**, ölçüm eksiği değil: türetilebilecek bir sayı yoktur — `koridor_adaylari` + `rota_dogrula` denetiminin `analyze_path` koluna taşınması ve **mutasyonla** ayırt ediciliğinin gösterilmesi gerekir (§6.5.1 A6). **Planlanan iş: 14 Eylül FDR teslimi sonrası, 21 Eylül 2026 uçuşu öncesi** | **KOD_VAR_TEST_YOK** | test (yalnız tanısal kolda) | `Y-3.3.4-M01` |
| **§2.2.1** | Mühürlü kutu, mancınıkla fırlatma, elden/dikey kalkış yasağı | Mekanik/idari. Yazılım tarafındaki karşılığı **sürüm mührüdür**: `scripts/surum_dondur.py` (künye + doğrulama) | `tests/test_faz_b_surum_dondurma.py` (49 test); ham koşum `results/faz_b_oncesi/surum_dondur_dogrula.txt` | **İNSAN-DONANIM** (yazılım mührü KANITLI_TEST) | gözle muayene (mühür, montaj) + test (sürüm mührü kapısı) | `Y-3.2.1-T05` · `Y-3.2.3-T01…T11` |
| **§2.2.2** (R2) | "Fırlatma sonrası İHA, tam otonom uçuş moduna geçerek… uçuşunu gerçekleştirecektir" | Uçuş kontrolcüsü: ArduCopter/ArduPlane. Repoda **parametre ve görev şablonu** olarak izlenir: `config/pixhawk/arducopter_fda.param` (31 parametre, her satırda gerekçe; Copter-4.5 kaynağından), `config/pixhawk/fda_gorev.waypoints` (QGC WPL 110: TAKEOFF 32 m → tek pas → LOITER 60 s → LAND). **Firmware sürümü sabit:** `scripts/pixhawk_firmware_indir.py:74` `SURUM = "stable-4.5.7"`, `:54` `BOARD_ID = 56` (Pixhawk6C) — kart fabrikadan **PX4** ile gelir (D-424); 4.7.1'de 31 parametrenin **9'u yok** (SI birim reformu, D-425) | `tests/test_faz_b_pixhawk_sablon.py` (12 test — dosya biçimi, kare geometrisi, süre bütçesi kilitli) · `tests/test_pixhawk_firmware_yolu.py` (10; `firmware/` yoksa iki test **atlanır ve söyler**). **5 Eylül ÖLÇÜM** (D-426 §1, MP Messages): 14:52 `ArduCopter V4.7.1 (dbe79216)` + "Missing 9 params" → 15:08 `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` · `PreArm: Check frame class` kayboldu; indirilen `firmware/arducopter.apj` 1.585.371 B, git 2a3dc4b7 (D-425 §4) ile aynı. ~~**Gerçek uçuşta AUTO kipi hiç koşmadı** — 5 Eylül'de de uçulmadı (D-426 §5)~~ → **Uçuldu, ama AUTO kipi hâlâ hiç koşmadı.** 12 Eylül 23:55 kart dökümü **ÖLÇÜM**: `config/pixhawk/emir.param:980` → `STAT_FLTTIME,273` (6 Eylül dökümü `config/pixhawk/mevcut.param:980` → `0`) · `:979` → `STAT_BOOTCNT,96` (6 Eylül 48). ⚠ **`STAT_FLTTIME` kümülatiftir:** iki döküm arasındaki **48 açılış** boyunca biriken toplam uçuş/silahlı süredir, **tek bir uçuşun süresi değildir** ve 12 Eylül'de BEYAN edilen ~15 s hover'ı **doğrulamaz** — aradaki **258 s açıklanmamıştır**. Kanıtladığı tek şey: 6 Eylül'den sonra kartta uçuş süresi **birikmiştir**. ⚠ Aynı dökümde `MOT_HOVER_LEARN,2` (öğrenme AÇIK, `:565`) olmasına rağmen `MOT_THST_HOVER` **her iki dökümde de 0,35 fabrika değerinde** (`emir.param:580` = `mevcut.param:580`) → kart hover gazını **öğrenmemiştir**; bu, kararlı hover'ın **aleyhine** kanıttır ve itki payı **ÖLÇÜLMEDİ**. Uçuşun kipi AUTO **değildi**: 12 Eylül atölyesinde **GUIDED** kipinde, kodla, 3 m'de 15 s hover + **kodla LAND** yapıldı, kumanda müdahalesiz (**BEYAN** — uçuşun `.bin` logu SD karttan **silinmiştir**, bağımsız doğrulama yok). AUTO görev uçuşu **hâlâ ölçülmedi** (§6.5.1 A3); planlanan ölçüm **21 Eylül 2026 uçuşu** | **ÖLÇÜLEMEDİ** (AUTO uçuş) · şablon ve firmware sürümü KANITLI_TEST · yükleme 5 Eylül ÖLÇÜM | analiz (parametre ve görev şablonu incelemesi) + test (şablon ve firmware sürüm kapıları) + gözle muayene (5 Eylül MP Messages satırı: firmware ve parametre yüklendi); uçuş testi **yapılmadı** | `Y-3.3.4-M01` · `Y-4-M10` · `Y-4-M12` |
| **§2.2.2** (R3) | "görüntü işleme algoritmaları vasıtasıyla HTAB içindeki açık olan güzergâhı tespit edecektir" | `codes/rpi_inference.py::run_camera` zinciri: `_preprocess` → `model.predict` (v36, imgsz 512) → `get_masks` → `CanliOlcekSaglayici` (mpp) → `analyze_path` → `_rota_kararini_esikle`. Model kaydı fail-closed (`codes/model_registry.py`) | Kabul kapıları K0–K8 + K5A, sentetik arena (n=260), **üretim kipinde** (1 Eylül, `t150_baglama_v36_kabul_verdikt.json`): **10/10 GEÇTİ** — K1 256/260 · K2 6/256 · K3 0/256 · K4 2/256 · K5/K5A 0 px · K6 2/256 · K7 84/85. Terfi anının (26 Ağustos) sayıları Bölüm 3 §3.3.4.2.4'te üç sütunlu tabloda durur; silinmemiştir. Kuru koşu 10 halkanın 9'u GEÇTİ. Testler: `tests/test_rota_guven_esigi.py` (8), `tests/test_zemin_kaplama_kapisi.py`, `tests/test_olcek_uretim_baglantisi.py` | **KANITLI_TEST** ⚠ ölçüm **sentetik** | test (kabul kapıları K0–K8) + simülasyon (sentetik arena, n=260) | `Y-3.3.4-M02` · `Y-4-M08` |
| **§2.2.3** (R4) | "tespit ettiği güzergâh bilgisini kablosuz haberleşme sistemleri üzerinden yer istasyonuna **ve İKA'ya** aktaracaktır" | `comms/iha_sender.py::KararYayinci` — her karede **tam bir** mesaj (`OPEN_ROUTE` **veya** `NO_ROUTE`; sessizlik yok), ACK'li tekrar, latest-wins kuyruk, ayrı HEARTBEAT iş parçacığı. Sözleşme: `CONTRACTS.md §6.5` | `tests/test_rpi_telsiz_yayin.py` (11 test, **gerçek loopback UDP** + gerçek `IkaReceiver` ACK'i). Kuru koşu halka 8: `uretim_yolu_telsiz.open_route_alindi=True, heartbeat=1, ack=['ika']` | **KANITLI_TEST** (UDP) · gerçek SiK için R20 | test (gerçek UDP loopback halkası) | `Y-3.3.4-M03` · `Y-4-M09` |
| **§2.2.3** (R5) | "alan hakemi, canlı olarak güzergâh bilgisinin tespit edildiğini onaylamalıdır" | `comms/yks_gui.py`: rota polyline + ref_xy çizimi, ret sebebi kanonik kodla kırmızı bant, güven-altı OPEN_ROUTE reddi ekranda, hakem künyesinde model SHA, **iki aşamalı** onay. Onayın **diske düşen dayanağı** hakem kanıt kaydı: `comms/hakem_kaydi.py` (JSONL), olay kümesi `yks_gui.KANIT_OLAYLARI` (16 olay, `comms/yks_gui.py:127`), sözleşme `CONTRACTS.md §6.8`; kanıt yazılamıyorsa fırlatma ve onay düğmeleri **kilitli** (fail-closed, fail-visible) | `tests/test_yks_gui_rota_engel.py`, `tests/test_rota_ret_nedenleri.py` (10), `tests/test_hakem_kunye_algi_hizasi.py`, `tests/t64_hakem_ekrani_kapisi.py`. Hakem kanıt kaydı: `tests/test_yks_hakem_kanit_yolu.py` (6; D-412 — `_kanit_yaz` çağrısı commit'lenmiş, tanımı commit'lenmemişti, YKS her gerçek kurulumda düşüyordu; 6/6 mutasyon), `tests/test_yks_hakem_kanit_olaylari.py` (22; D-419 §2 — kanıt kilidi **fail-open'dı**, tek-yazar kilidiyle kapatıldı; 6 mutasyon; CONTRACTS tablosu ↔ sabit ↔ AST üç yönlü küme eşitliği). Gerçek oturum kaydı `results/prova/20260905_142958_15092/hakem_log.jsonl` (5 Eylül, YKS `--fda` PC'de; 1115 satır, 5 olay adı: KAMERA_KANIT 554 · TELEMETRI_KANIT 554 · UI_OLAYI 5 · OTURUM_BASLADI 1 · YKS_ARAYUZ_HAZIR 1 — İHA bağlı değildi, ROTA_*/HAKEM_ONAYI_* olayı **yok**) | **KANITLI_TEST** (sözlü onay insan işidir) | test + gözle muayene (hakem ekranı) | `Y-3.3.4-M01` · `Y-4-M11` |
| **§2.2.3 / §6.2** (R5-ek) | "**gerçek zamanlı** olarak… monitör üzerinden izlenmeli" — bayat tespit canlı gösterilemez | Tazelik damgası `YKS_TESPIT_TAZELIK_S = 5,0 s`; HEARTBEAT'te `karar_yas` alanı (son **algı kararının** yaşı). Alan **yoksa** yaş bilinmiyor demektir ve alıcı taze saymaz | `tests/test_t169_tespit_tazeligi.py` (19 test), `tests/test_a2_karar_yasi.py` (22 test), `tests/test_k1_tazelik_damgasi.py`. Gerekçesi ölçümdür: D-374, gerçek uçuşta **51 saniyelik** karar üretmeyen aralık ölçüldü, heartbeat o sırada akmaya devam ediyordu | **KANITLI_TEST** | test | `Y-3.3.4-M03` · `Y-4-M09` |
| **§2.2.3** (R6) | "alan hakemi… güzergâh bilgisinin **İKA'ya aktarıldığını** onaylayacaktır" | İKA ACK'i yalnız gönderene değil **YKS'ye de** gider (`ika_nav --yks`); "İKA ALDI" gelmeden 2. onay düğmesi açılmaz. Sözleşme `CONTRACTS.md §6.6` (K8) | `tests/test_ika_go_ackli_tekrar.py` (11 test); ham çıktı `results/k4_k8_ika_go_ack/rapor.md`. ⚠ 21 Eylül'de İKA yoktur: `--fda` kipinde bu koşul **aranmaz** ve ekranda dayanağı basılır (`CONTRACTS §6.7`) — `tests/test_faz_b_yks_fda_kipi.py` (9 test, 4/4 mutant yakalandı) | **KANITLI_TEST** | test | `Y-3.3.4-M03` · `Y-4-M09` |
| **§2.2.3** (R7) | "Bu aktarımın İHA **havada iken** tamamlanması gerekmektedir" | YKS onay anında iniş damgasıyla karşılaştırma: "inişten SONRA / zaman bilinmiyor / henüz inmedi" uyarısı | `tests/test_yks_gui_aktarim_zamani.py` (3 test), `tests/test_p9abc_yks.py` (13 test — §2.2.3 sıra denetimi) | **KANITLI_TEST** (uyarı; zorlama doğası gereği yok) | test | `Y-4-M11` |
| **§2.2.3 / §2.2.5** (R8) | Aktarımın tamamlanması — `IKA_GO` kayıpsız iletilmeli | ACK'li, **aynı-seq** tekrar gönderimi; üst sınırda görünür hata; ACK gelmezse düğme **yeniden açılır**; alıcıda idempotent latch. `CONTRACTS.md §6.6` (K4) | `tests/test_ika_go_ackli_tekrar.py` (11), `tests/test_ika_go_gate.py` (9). Ham çıktı `results/k4_k8_ika_go_ack/` — **5 mutasyonun 5'i yakalandı** | **KANITLI_TEST** | test (mutasyonlu) | `Y-3.3.4-M03` · `Y-4-M09` |
| **§2.2.4** (R9) | "Paraşüt açma komutu otonom… manuel tetikleme ile de… manuel ise ceza" | Yazılım yarısı: YKS iki adımlı teyit → ACK'li tekrar → İHA'da `comms/iha_komut_alici.py` komutu Pixhawk'a `COMMAND_LONG` ile aktarır ve **yalnız aktarım başarılıysa** ACK döner. Ceza −50 kaydı YKS'de | `tests/test_faz_b_iha_komut_alici.py` (23 test; 3 Eylül'de 22 — D-419 §1: ACK bileşen kümesi `_ack_basabilen_bilesenler`, sonuç önbelleği ve saat ofseti üç kritik kapatıldı, ayna `jetson_paket/kod/iha_komut_alici.py` güncellendi), `tests/test_iha_komut_saat_ve_tekrar.py` (42; D-419'da 18 → D-422'de 42: saat sapması 30 dk'yi aşınca ARM/DISARM/RTL/LAND/PARACHUTE **kalıcı reddediliyordu** — RTC'siz Jetson'da garantili saha ölümü; onarım sonrası 2 saat sapmada 7. basamakta geçer, ileri adım sonrası ölü pencere 60,00 s → 0,25 s; mutasyon 17 + 5 test düştü), `tests/test_p9abc_yks.py` (13), `tests/test_yks_gui_komut_durustlugu.py` (13; 3 Eylül'de 6, D-419 §3 birleştirmesi `bb832a2`). ⚠ D-422 §4: saat kapısı sahtecilik savunması **değildir**; gerçek çevre `--izinli-kaynak` adres pinidir. **Otonom tetik** (`CHUTE_*` parametreleri, mekanik açma) repo dışıdır. Karttan okunan **tek ölçüm**: `CHUTE_ENABLED,0` (`config/pixhawk/emir.param:194`, 12 Eylül) — otonom tetik bugün **kapalıdır**; bu bir ölçümdür ama hükmü **karşılamaz**. Mekanik açma düzeneği ve sabit kanat platformu henüz yok. **Planlanan ölçüm: final dalgası** (`SAHA_HAZIRLIK_PLANI §7`) — `CHUTE_*` açılıp yer testinde tetiklenecek, 30 Eylül–3 Ekim öncesi (§6.5.1 A12) | **KANITLI_TEST** (manuel zincir) · **ÖLÇÜLEMEDİ** (otonom) | test (manuel zincir); otonom tetik **doğrulanmadı** | `Y-3.2.1-T05` · `Y-4-M12` |
| **§2.2.5** (R10) | "İHA yere temas etmeden İKA hareket edemez… iniş yapmadan harekete geçen takımların görevi başarısız" | Üretici: `comms/iha_inis_yayinci.py` ← `comms/inis_kaniti.py::yerde_mi` (Pixhawk `EXTENDED_SYS_STATE.landed_state == ON_GROUND` **ve** `GLOBAL_POSITION_INT.relative_alt < 1 m`, aynı sysid, ardışık 3 çift, mutlak son tarih). Kapı: `comms/ika_receiver.py::_surus_izni_gecerli_unlocked` | `tests/test_inis_kaniti.py` (26), `tests/test_iha_landed_gate.py` (12), `tests/test_iha_inis_yayinci.py` (12). Manuel "İHA İNDİ" düğmesi latch'i **açmaz** (test ile kilitli). Kuru koşu `surus_izni GECTI` | **KANITLI_TEST** | test | `Y-3.3.4-M01` · `Y-4-M11` |
| **§2.2.5** (R10-ek) | İniş kanıtı sahada **sessizce ölmemeli** | ArduCopter `EXTENDED_SYS_STATE`'i hiçbir `SR*` akışında vermez; yalnız `SET_MESSAGE_INTERVAL` ile akar ve istek Pixhawk reboot'unda (pil değişimi) silinir. `AkisIstekcisi`: başlangıçta ve her 10 s'de istek yeniler, 5 s sessizlikte KIRMIZI uyarı | `tests/test_faz_b_akis_istegi.py` (17 test, 2 mutant yakalandı). Bulgu kaynağı: Copter-4.5 `GCS_Mavlink.cpp` akış dizileri okundu; `grep SET_MESSAGE_INTERVAL comms/` → **0** idi | **KANITLI_TEST** | analiz (ArduCopter kaynak akış dizileri) + test | `Y-3.3.4-M03` · `Y-4-M11` |
| **§2.2.5** (R11) | "İKA'nın intikal süreci YKS'de görevli takım üyesi tarafından **manuel** olarak tetiklenir" | YKS `IKA_GO` komutu → `comms/ika_receiver.py` latch | `tests/test_ika_go_gate.py` (9 test; gerçek UDP çiftinde IKA_GO **öncesi hareket yok**, sonrası var) | **KANITLI_TEST** | test | `Y-3.3.4-M01` |
| **§2.2.5** (R12) | "İKA; **otonom olarak** açık olan güzergâhı takip ederek HB'ye ilerleyecektir… otonom hareket etmeyen İKA'nın görevi başarısız" | Sürücü **arayüzü** var: `simulation/scripts/ika_surucu.py` (`hiz_ver / konum_al / durdur / saglikli`), fail-closed ardışık hata tavanı 3; `CONTRACTS.md §7.2`. **`GercekSurucu` arka uçsuz kurulamaz** (`DONANIM_YOK` istisnası) — sessiz iskelet yasak | `tests/test_p3_ika_surucu.py` (14 test; bayt-eşitlik + fail-closed + §2.2.5 kilidi), kabul harnessı `scripts/ika_surucu_kabul.py`, `tests/test_faz_b_ika_surucu_kabul.py`. **Kuru koşu halka 10 hâlâ `SAHİPSİZ`**: `saha_surucu_importlari: []` | 🔴 **İNSAN-DONANIM** (açık) | analiz (sürücü sözleşmesi) + test (kabul harness'ı); gerçek sürücü **doğrulanmadı** | `Y-3.2.2-T01…T11` · `Y-3.3.3-M01` · `Y-4-M07` |
| **§2.2.6** (R13) | "İKA'nın… **HB sınırları içerisine** girmesi ile görev başarılı" — hedef = 2×2 m kırmızı H | HB dedektörü **üretime bağlandı**: üç üretim çağrısı `analyze_path(goruntu=…)` geçiyor; iç HB çağrısı **ölçek + şekil** çifti kullanıyor (`HB_SEKIL_ESIGI`; mpp yoksa açılmaz). Rotanın son waypoint'i HB pedinin kutusunda biter | `tests/test_t150_baglama.py` (6 nöbetçi), `tests/test_t198_hb_sekil.py` (14), `tests/test_hb_dedektoru.py` (25). Bağlama ölçümü: hedef **253/256** doğru pedde, ped örtülüyken **259/260 HEDEF_YOK** (fail-closed), maliyet **sıfır** (p eşit: 0,9846). Ham çıktı `results/t150/baglama_olcumu_20260901.json` | **KANITLI_TEST** ⚠ sentetik; gerçek pedde ÖLÇÜLEMEDİ — hedef alanda **kırmızı H'nin var olduğu** teyit edildi (BEYAN, D-471), ama gerçek pedde HB tespiti hiç ölçülmedi ve maket çekimi **yapılmayacaktır** (kullanıcı kararı, kalıcı). **Planlanan ilk ölçüm: 21 Eylül 2026** (uçuş tarihi kesin) | test + simülasyon (sentetik arena) | `Y-3.3.4-M02` · `Y-3.3.3-M01` |
| **§2.2.6** (R13-ek) | Varış = **brandaya temas**, sınıra girmek değil | `simulation/scripts/ika_nav.py` son waypoint'te `FINAL_WP_RADIUS = 0,3 m`; bağlayıcı eşitsizlik `FINAL_WP_RADIUS < HB_KENAR_M/2` (1,0 m) → araç merkezi ped kenarından ≥ 0,7 m içeride durur. `CONTRACTS.md §7.3` | `tests/test_p9e_branda_temas.py` (5 test: geometri + kinematik + mutasyon). ⚠ ~~Gazebo'lu **fiziksel temas** koşusu bu makinede ÖLÇÜLEMEZ (gz yok)~~ → **10 Eylül 2026: fiziksel temas MuJoCo'da KOŞULDU (SENTETİK, Bölüm 3 §3.3.3).** Sonuç gizlenmiyor, **üç kol ayrı ayrı**: YER GERÇEĞİ rotayla **45/45** (harita 15/15, **GEÇTİ**); **ÜRETİM MODELİ (mozaik)** rotasıyla **9/45**, harita **0/15** (**DÜŞTÜ**); **ÜRETİM BORU HATTI (kare-bazlı)** **0/15**, harita 0/5 koşulan (**DÜŞTÜ**) — ön kayıtlı H1-K5 eşiği ≥ 12/15, **gevşetilmedi** (`FDR/BOLUM_3` satır 1252-1254 ve 1375-1377). **Sahaya giden kol üçüncüsüdür.** Ham çıktı `results/fdr_sprint_20260910/`. ⚠ **Bu ölçümün dayanağı 13 Eylül itibarıyla kırmızıdır:** (a) koşum eski `IKA_IZ_GENISLIGI_M = 0,39` ile yapıldı, 12 Eylül'de iz genişliği **0,4595 m** ölçüldü (D-472, şerit metre); (b) arena üretecinin **kilit SHA'sı ve mutasyon nöbetçisi tam süitte DÜŞÜYOR** (`test_sim_mujoco_arena` — üretilen `3ba496df…` ≠ kilit `d2c3127b…`; ayrıca model iz genişliği 0,46 ≠ sabit 0,4595). Yani bugün üretilen arena, ölçümün koşulduğu arenayla **bayt-eş değildir** ve nöbetçi ayırt ediciliğini **gösteremiyor**. Sayılar olduğu gibi bırakıldı; **yeniden koşum T256'dır ve 14 Eylül teslimine AÇIK girer.** Gerçek İKA ile fiziksel temas hâlâ ÖLÇÜLEMEDİ (sürücü yok, §6.5.1 A1) | **KANITLI_TEST** (geometri) · **ÖLÇÜLEMEDİ** (fiziksel) | hesaplama (geometrik eşitsizlik) + test; fiziksel temas simülasyonu ~~**ÖLÇÜLEMEDİ: Gazebo bu makinede yok**~~ → **MuJoCo'da KOŞULDU (10 Eylül, sentetik)** — üç kol ayrı ayrı: YER GERÇEĞİ rota **45/45** · harita 15/15 **GEÇTİ**; **ÜRETİM MODELİ (mozaik) 9/45 · harita 0/15 DÜŞTÜ**; **ÜRETİM BORU HATTI (kare-bazlı) 0/15 · harita 0/5 koşulan DÜŞTÜ** (eşik ≥ 12/15, gevşetilmedi; `FDR/BOLUM_3` satır 1252-1254 ve 1375-1377). **Sahaya giden kol üçüncüsüdür.** ⚠ Dayanağı 13 Eylül itibarıyla kırmızıdır (eski iz genişliği ↔ ölçülen 0,4595 m; arena kilit SHA'sı ve mutasyon nöbetçisi tam süitte düşüyor) — ayrıntı kanıt sütununda. Gerçek İKA ile saha koşusu hâlâ **ÖLÇÜLEMEDİ** (§6.5.1 A1) | `Y-3.3.3-M01` · `Y-4-M07` |
| **§2.2.6** (R22) | "İKA'nın belirlenen **yükleri taşıyarak** hedef bölgeye intikal etmesi esastır… yapısal bütünlüğünü koruyor olması ve taşıdığı yükü eksiksiz muhafaza etmesi zorunludur" | Yazılıma düşmez. Yük bağlantısı, kasa ve tartı tutanağı final dalgasının işidir | Kayıt: bu hüküm yükümlülük haritasında **hiç yoktu**, 2026-08-26 taramasında bulundu ve eklendi | **İNSAN-DONANIM** | gözle muayene — **yapılmadı**; İKA yük bağlantısı ve tartı tutanağı **yok**, bu hükmün yeni ölçülmüş gerçekler arasında karşılığı **bulunmuyor**. **Planlanan muayene: final dalgası** — yük bağlantısı + yapısal bütünlük + yük tartısı tek tutanakta, 30 Eylül–3 Ekim öncesi | `Y-3.2.2-T10` · `Y-3.2.2-A02` |

### 6.1.4 İzlenebilirlik matrisi — §5.3.2 (Drone ile Görev Test Uçuşu · 30 Eylül–3 Ekim)

| şartname maddesi | gereksinim | karşılayan bileşen | kanıt (dosya / test) | durum | doğrulama yöntemi | yönerge kimliği (Y-) |
|---|---|---|---|---|---|---|
| **§5.3.2** | "çoklu rotorlu ve dikey iniş-kalkış yapabilen bir insansız hava aracı" | 3B baskı quadcopter (dronesolid gövde), ~~5008 340KV ×4, 12×10 pervane~~ → SunnySky X2220 980KV V3 ×4 (BEYAN, etiket yok) + 10×4,5 (1045) pervane (7 Eylül beyanı, D-435), 80 A DShot ESC, FCHUB-12S V2, Pixhawk 6C + PM02, Holybro M9N, FS-i6 (iBUS), 2× SiK 433 MHz, ~~**Jetson Nano 4GB**~~ **Jetson Orin Nano Developer Kit 4 GB** (6 Eylül'de kartta ÖLÇÜLDÜ, D-431), RPi HQ (IMX477) | Künye: `SAHA_HAZIRLIK_PLANI_20260903.md §0.2`. **Montaj 5 Eylül** — kutu açıldı, ESC/güç modülü plandan farklı çıktı (D-426 §3); Jetson künyesi 6 Eylül'de kartta ölçüldü (`results/jetson_20260906/ORTAM_KUNYESI.txt`) | **İNSAN-DONANIM** | gözle muayene — künyenin **ölçülen** kısmı: Jetson **Orin Nano Developer Kit** (D-431; bellek boyutu künyede yok, "4 GB" BEYAN), ESC **Skywalker 60 A V2 ×4** (AUX1–4), güç modülü **PM06**, pil **3S 6000 mAh** (12 Eylül kararı), kart tarafı `FRAME_CLASS,1` / `FRAME_TYPE,1` = **QUAD/X** (`config/pixhawk/emir.param:395`, `:396`). **Açık kalan:** motor marka/KV doğrulaması — **SunnySky X2220 980KV V3 hâlâ yalnız BEYAN**, motorda etiket fotoğrafı yok. **Planlanan insan işi: 21 Eylül 2026 uçuşu öncesi** — motor etiketinin fotoğraflanması. ⚠ M1 motoru 6 Eylül'de hasar gördü (D-429), uçuştan önce değişecek | `Y-3.3.1-M02` · `Y-3.2.1-T10` |
| **§5.3.2** | "**asgari 30 metre** irtifadan uçarak" tespit | `codes/karar_sozlesmesi.py::SARTNAME_ASGARI_IRTIFA_M = 30,0`; `asgari_irtifa_notu()` her karede irtifayı damgalar, 30 m altı `ASGARI_IRTIFA_ALTI` işaretlenir. Görev planı **32 m** (2 m baro payı) | `tests/test_t171_asgari_irtifa.py` (20 test). ⚠ Kaydın kendi cümlesi: bu şart daha önce sistemde **hiç uygulanmıyordu** ve uyum raporumuz uygulandığını **iddia ediyordu** (D-319) — düzeltildi ve kilitlendi | **KANITLI_TEST** | test | `Y-3.3.4-M01` · `Y-4-M10` |
| **§5.3.2** | "20×20 metre boyutlarındaki simüle edilmiş test alanı" tek karede görülmeli | **FOV_yatay = 55,3° (HESAP)** — IMX477 etkin sensör alanı **6,287 × 4,712 mm** (üretici veri sayfası), lens **6 mm** → `2·atan(6,287 / (2·6)) = 55,3°`; düşey `2·atan(4,712 / 12) = 42,9°`. **30 m'de kare = 31,4 m × 23,6 m (HESAP)**: `2·30·tan(27,65°) = 31,4` ve `2·30·tan(21,44°) = 23,6` → 20×20 m alan **her iki eksende sığar** (yatayda 1,57×, düşeyde 1,18× pay). Aynı geometri (`2·atan(W / 2f)`) `scripts/kamera_fov_hesapla.py::fov_derece` içindedir. Önceki **55–63°** aralığı lens beyanından türetilmiş **TAHMİN**di ve bırakıldı; sayı artık tek ve kaynaklıdır. `--fov` sahada **ölçüm** olacak | Hesap ve gerekçe `SAHA_HAZIRLIK_PLANI_20260903.md §0.2`; çözünürlük sözleşmesi `CONTRACTS.md §8`, kilit `tests/test_t163_cozunurluk_sozlesmesi.py`. **Ölçüm yapılamadı ve 14 Eylül FDR teslimine yetişmiyor:** RPi HQ + 6 mm lens **elde yok**; 5 Eylül'de de ölçülmedi (D-426 §4), `results/` altında `kamera_dogrula` çıktısı yok (13 Eylül'de arandı). Kamera **nadir (90°)** bakacak şekilde konumlanacak (12 Eylül kararı, D-471). **Planlanan ölçüm: 21 Eylül 2026 uçuşu** — `codes/kamera_dogrula.py --kaydet` + `scripts/kamera_fov_hesapla.py`; ölçülen FOV hesaptan saparsa **hesap değil sonuç** yazılır | **ÖLÇÜLEMEDİ** (hüküm **HESAP**la karşılanıyor: 31,4 × 23,6 m ≥ 20 × 20 m; ölçüm **21 Eylül 2026**) | hesaplama (veri sayfası sensör boyutu + lens odağı → FOV → kare genişliği, iki eksende); ölçüm `codes/kamera_dogrula.py` + `scripts/kamera_fov_hesapla.py` ile — **planlanan: 21 Eylül 2026** | `Y-3.3.4-M02` · `Y-4-M03` |
| **§5.3.2** | "uçuş esnasında **gerçek zamanlı** olarak YKİ'ye aktarmak" | `KararYayinci` (R4) + tazelik damgası + `karar_yas` (R5-ek) | **Uçtan uca kare gecikmesi ölçüldü**: 33 ölçülen gerçek karede (+3 ısınma karesi, yüzdeliklere katılmaz), üretim zinciri + gerçek telsiz halkası (UDP loopback ACK) → **p50 **0,085 s** · p95 0,113 s**, tazelik penceresinin (5 s) çok altında. Adım kırılımı ve ham veri `results/fda_butce/olcum_20260901.json`; nöbetçi `tests/test_b2_fda_butcesi.py` (13). ⚠ ~~**Seri (SiK) hat ÖLÇÜLEMEDİ**~~ → **13 Eylül 2026: gerçek RF hattı ÖLÇÜLDÜ ve DÜŞTÜ** (D-476) — `results/atolye_20260912/A6_sik_ikago.json` · `A6_sik_parasut.json` (`scripts/sik_rf_olc.py`, seri COM7 @57600, n=200×2): kayıp **%0**, RTT p95 **265,2 ms** (eşik 250) ve **229,6 ms** (eşik 200) → **ikisi de AŞILDI**, `cikis_kodu 1`. Eşik **gevşetilmedi**; düzeltme sırası T263 (Air Speed) → T264 (ECC) → T265 (tasarım kararı). Yukarıdaki **0,113 s** p95 hâlâ **UDP loopback** çerçevesindedir ve seri hattı **kapsamaz**: gerçek zincirin bugünkü tur süresi bunun **iki katından fazladır** (§6.5.1 A2) | **KANITLI_TEST** (UDP) | test (uçtan uca gecikme ölçümü) | `Y-3.3.4-M03` · `Y-4-M09` |
| **§5.3.2** | Gereken **kare hızı** — hakem onayı için tespit taze olmalı | Eşik **türetildi, tahmin edilmedi**: `GEREKLİ_FPS ≥ 1 / (5 · p)`, `p` = bir karenin geçerli rota yayınlama olasılığı | Sentetik arena `p = 0,9846` → 0,203 FPS; gerçek DJİ (sızıntısız, n=243) `p = 0,3457` → 0,579 FPS; en kötü uçuş 0,61 FPS. Ham çıktı `results/b4_fps/p_ve_kosu_20260901.json`; nöbetçi `tests/test_163_b4_olcum_nobetcisi.py` (13). **Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena karesi yok ve maket çekimi **yapılmayacaktır** (kullanıcı kararı, kalıcı). ⚠ Jetson FPS kapısının geçmesi bu boşluğu **kapatmaz**: FPS bir **hız** ölçüsüdür, `p` bir **sahne** ölçüsüdür; ikisi aynı sayı değildir. **Planlanan ilk ölçüm: 21 Eylül 2026 uçuşu**; rapor tarihinde (14 Eylül) kapanmaz. **Eşiğin Jetson'da karşılığı 6 Eylül'de ÖLÇÜLDÜ (D-431):** Orin Nano Developer Kit 4 GB, `scripts/jetson_fps.py` 120 örnek → pt p50/p95 **1,35/1,06 FPS** · engine **1,58/1,33 FPS** ≥ 0,61, **GEÇTİ**; `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` | **KANITLI_TEST** (iki çerçeve + Jetson FPS kapısı) · saha değeri **ÖLÇÜLEMEDİ** | hesaplama (eşik türetimi) + test (`p` ölçümü) + simülasyon (sentetik `p`) | `Y-3.3.4-M02` · `Y-4-M08` |
| **§5.3.2** | "gerçek zamanlı güzergah tespitinin alan hakem heyeti tarafından **doğrulanıp onaylanması**" | YKS hakem ekranı + iki aşamalı onay + `--fda` kipi (İKA kanıtı aranmaz; ACK `ref_tip` ile İHA'ya gider) | `tests/test_faz_b_yks_fda_kipi.py` (9 test; **M1–M4 mutasyonlarının 4'ü de yakalandı**), `tests/test_faz_b_ack_ref_tip.py` (14). ⚠ Bu kip **mimar tarafından yazıldı ve aynı el tarafından denetlendi**; bağımsız denetim borcu **açıktır ve 14 Eylül teslimine açık girer**. ⚠ Gerekçe güncellendi: "denetleyen ajan kotada" artık geçerli değil (kota bol); kalan engel **korelasyonlu kör noktadır** — bir iş onu yazanın onayıyla kapanmaz, iki tarafın anlaşması kanıt değildir, hakem **ölçümdür** (`CLAUDE.md §19`). Kapanışı: hakem rolü oynanan gerçek prova; **planlanan tarih: 21 Eylül 2026** (takvime bağlandı, §6.5.1 A11 — bu numara *atölye kâğıdındaki A11 video gecikmesiyle* karıştırılmamalıdır) | **KANITLI_TEST** (denetim borcu açık) | test (9 test, 4/4 mutant) + gözle muayene (hakem ekranı) | `Y-4-M11` |
| **§5.3.2** | "tüm operasyon sürecinin (kalkış, tespit, veri aktarımı ve iniş) **maksimum 10 dakika**" | `codes/karar_sozlesmesi.py::SARTNAME_FDA_OPERASYON_SURESI_S = 600`; YKS `--fda` kipinde bütçe 900 yerine 600 s | `tests/test_t170_fda_sure_butcesi.py` (16 test), `tests/test_b2_fda_butcesi.py` (13). Görev planı kötü-durum süre bütçesi **221,5 s ≤ 600 s** (`config/pixhawk/README.md`). ⚠ *"600 saniyeye sığar"* hükmü **bilerek verilmedi**: uçuş ve kamera yakalama ölçülemedi ve toplama **0 olarak girmedi**. Seri hat 13 Eylül'de ölçüldü ama sonucu bu hükmü **kolaylaştırmıyor**: RTT p95 265,2/229,6 ms, eşikleri aşıyor (D-476). ⚠ **Yanlış kapatma riski, açıkça yazılıyor:** 12 Eylül dökümündeki `STAT_FLTTIME,273` s **kümülatiftir** (48 açılış boyunca birikti), tek bir operasyonun süresi **değildir** ve 600 s hükmünü **kapatmaz**. Kapanışı tek koşumda kronometre ister: kalkış → tespit → YKS'ye aktarım + hakem onayı → iniş. **Planlanan ölçüm: 21 Eylül 2026 uçuşu** | **KANITLI_TEST** (yazılım payı) · uçuş **ÖLÇÜLEMEDİ** | hesaplama (süre bütçesi) + test (sabit kapıları) | `Y-4-M03` |
| **§5.3.2** | "**yanlış güzergah tespiti** yapan takımlar 0 puan" | Fail-closed katmanlar: `rota_guven_reddi`, `rota_olcek_reddi`, `zemin_maskesi_reddi`, `rota_koridor_genisligi_reddi`, K-A uç-bant, `_rota_kararini_esikle`; **son savunma** `iha_sender.send_open_route` (eşik altı → NO_ROUTE); YKS eşik altı OPEN_ROUTE'a ACK vermez | `tests/test_rota_guven_esigi.py` (8), `tests/test_rota_ret_nedenleri.py` (10), `tests/test_koridor_genisligi.py`, `tests/test_zemin_kaplama_kapisi.py`, `tests/test_t141_rota_yoksa_surme.py` | **KANITLI_TEST** | test + simülasyon (kabul kapıları) | `Y-3.3.4-M02` · `Y-4-M08` |
| **§5.3.2** | Yanlış güzergâhın **gürültüden** doğmaması — kare kare çevrilme | Yayın histerezisi (`KararYumusatici`): NO_ROUTE **asla** geciktirilmez; farklı şerit ancak K ardışık karede teyitlenirse yayına geçer; bastırma en fazla K−1 kare sürer | `tests/test_p5_histerezis.py` (12 test). Ölçüm (`results/p5_histerezis/olcum_20260903.json`, iki tohum, n=260×5): ham çevrilme **13 → yayın 7** (tohum 7), **24 → 11** (tohum 42); bastırılanların **hiçbiri** NO_ROUTE değil. ⚠ Ön kayıttaki özgün eşik **H1 DÜŞTÜ** ve öyle kayıtlı; H1a/H1b/H2 geçti | **KANITLI_TEST** (bir alt eşik düştü, gizlenmiyor) | test (ön kayıtlı) + simülasyon (n=260×5, iki tohum) | `Y-3.3.4-M01` · `Y-4-M08` |

### 6.1.5 İzlenebilirlik matrisi — §6.2 (yarışma sırası) ve §6.4 (geçersizlik)

| şartname maddesi | gereksinim | karşılayan bileşen | kanıt (dosya / test) | durum | doğrulama yöntemi | yönerge kimliği (Y-) |
|---|---|---|---|---|---|---|
| **§6.2** | "15 dakikalık Hazırlık Süresi… 'Takım Hazır' ile durdurulur" | `SARTNAME_HAZIRLIK_SURESI_S = 900` (~~`codes/karar_sozlesmesi.py:1996`~~ `codes/karar_sozlesmesi.py:2010`; 3 Eylül'de `:1991`, 10 Eylül öğlene dek `:1996` idi — T213-B İKA kinematik sabitleri eklendi, dosya büyüdü; 10 Eylül T214-B okuması); YKS hazırlık kronometresi | Sabit tek yerde; ekran metni ondan türer. ⚠ Bu sayı 2026-08-26'da kodda **beş yerde çıplak `"15:00"`** olarak duruyordu ve kayda geçirildi (D-297); sabit sonradan eklendi | **KANITLI_TEST** | test | `Y-4-M03` |
| **§6.2** | "müdahale → **100 ceza puanı** + süre hazırlığa eklenir" | `comms/yks_gui.py::mudahale` — −100 ceza + hazırlık kronometresinin devamı **kodda var** | ⚠ **−100 müdahale cezasının doğrudan/mutasyonlu testi YOK.** ~~Kanıt olarak "`grep mudahale tests/` boş" yazılıydı — **komut koşulunca boş DEĞİL**, 13 Eylül'de düzeltildi.~~ Gerçek kanıt: `grep -rn "\-100" tests/*.py` içinde müdahale/ceza/puan bağlamında **tek eşleşme yok**. `mudahale` adı `tests/` altında **geçiyor** (5 dosya, 7 satır; `tests/test_yks_hakem_kanit_olaylari.py:284` `g.mudahale()`'yi gerçekten çağırıyor) ama yalnız **olay akışı içinde**: çağrının **−100 kaydı ürettiği** ve **hazırlık kronometresinin durmadığı** hiçbir yerde `assert` edilmiyor. Kilitli olan tek ceza manuel paraşüt −50'dir (`tests/test_yks_gui_komut_durustlugu.py`). Bu bir **yazılım borcudur**, ölçüm eksiği değil — türetilecek sayı yok; 13 Eylül'e kadar açık kalem listesinde de yoktu, **§6.5.1 A14** olarak eklendi. **Planlanan iş: 14 Eylül FDR teslimi sonrası, 21 Eylül uçuşu öncesi** | **KOD_VAR_TEST_YOK** | gözle muayene (kod okuması); **test yok** | `Y-3.3.4-M01` |
| **§6.2** | "Tekrar fırlatma süreci… süre **durdurulmaz**, 15 dakikaya dâhil" | YKS `firlatma()` kronometreyi **yeniden başlatmıyor** (`if self.t_iha0: return`), düğme kilitleniyor | Davranış kodda doğru; **doğrudan tekrar-fırlatma testi yok** (durum 2026-08-26'dan beri aynı). Yazılım borcu; türetilebilecek sayı yok — `firlatma()` iki kez çağrılıp kronometrenin **yeniden başlamadığı** mutasyonla gösterilecek. **Planlanan iş: 14 Eylül FDR teslimi sonrası, 21 Eylül 2026 uçuşu öncesi** (§6.5.1 A8). 4 Eylül'de eklenen `tests/test_yks_monotonik_kronometre.py` (3, commit `1b94dca`) kronometreyi duvar saatinden bağımsız kilitler, `firlatma()`'yı bir kez çağırır — **tekrarı sınamaz** | **KOD_VAR_TEST_YOK** | gözle muayene (kod okuması); **test yok** | `Y-3.3.4-M01` |
| **§6.2 / §6.4** | "İHA görev süresi… azami **15 dakika**" · "İKA'nın HB'ye ulaşması için **10 dakika**" | `SARTNAME_IHA_GOREV_SURESI_S = 900`, `SARTNAME_IKA_GOREV_SURESI_S = 600`; İKA'da **iki ayrı son tarih** (bekleme / sürüş) — tek ortak deadline yasak. `CONTRACTS.md §7.1` | `tests/test_k5_k6_sure_limitleri.py` (9 test; sahte saat + gerçek UDP loopback, **4 mutasyonla düştüğü gösterildi**) | **KANITLI_TEST** | test (mutasyonlu) | `Y-4-M03` |
| **§6.2 / §6.4** | "İHA-UB sınırları içinde icra etmeli; dışına taşan uçuşlar **Alan İhlali**" (300×300 m) | `SARTNAME_IHA_UB_KENAR_M = 300,0`, `iha_ub_ihlali(x, y)`. Üretimde `--ub-referans LAT,LON` ile her HEARTBEAT yerel `x,y` taşır; konum **aynı telemetri okuyucusundan** gelir, ikinci yol açılmaz | `tests/test_t162_alan_ihlali.py` (19 test; üretim döngüsü gerçekten koşuluyor). ⚠ Bu kapı **sahada ölüydü**: GUI denetimi vardı ama üretimde `x,y` üreten yol **yoktu** (D-307). Geofence'in kendisi Pixhawk parametresidir: `FENCE_ENABLE=1`, `FENCE_ALT_MAX 50` (`config/pixhawk/arducopter_fda.param:140,:148`) — **kart değerleri 12 Eylül'de ÖLÇÜLDÜ**: `config/pixhawk/emir.param` (12 Eylül 23:55) → `FENCE_ENABLE,1` (`:361`) · `FENCE_ACTION,1` (`:358`) · `FENCE_ALT_MAX,50` (`:359`) · `ARMING_CHECK,1` (`:28`). ⚠ Parametreyi okumak, davranışı **tetiklemek değildir**: sınır ihlali sahada hiç denenmedi, planlanan ölçüm 21 Eylül 2026. Önceki dökümler: 5 Eylül'de alınamadı (D-426 §4); 6 Eylül 20:22 dökümü `arducopter_fda_20260906.param` repoda — `FENCE_ENABLE,1` · `FENCE_ALT_MAX,50` kart değeri olarak okunuyor (D-428 §5g); RC failsafe 6 Eylül'de **ÖLÇÜLDÜ ve DÜŞTÜ** (D-428 §2) → §6.5.1 A13 | **KANITLI_TEST** (yazılım) · **ÖLÇÜLEMEDİ** (geofence) | test (üretim döngüsü koşuluyor); Pixhawk geofence'i gözle muayene ile — 5 Eylül'de **yapılmadı** (§6.5.1 A13) | `Y-4-M12` |
| **§6.2** | "fırlatma/başlangıçtan görev bitimine kadar tüm süreçleri (seyrüsefer, tespit, veri aktarımı, sürüş) **tam otonom**" | Tespit otonom (R3) · aktarım otonom (R4) · seyrüsefer uçuş kontrolcüsünde (R2) · **sürüş açık** (R12) | Zincirin dört yarısından üçü kanıtlı, biri donanım bekliyor | **kısmen KANITLI_TEST** · sürüş **İNSAN-DONANIM** | analiz (zincir bütünlüğü) + test | `Y-3.3.4-M01` · `Y-3.3.3-M01` |
| **§6.4** | "Aktarılan verinin doğruluğunun Alan Hakemi tarafından **teyit edilemediği** veya **veri akışının sağlanamadığı** durumlarda uçuş geçersiz" | `IkaReceiver.poll` `hb_timeout` → `link_lost` → güvenli duruş; `send_heartbeat` 1,0 s aralık < 3,0 s zaman aşımı (iki ardışık kayıp bağlantıyı düşürmez); iniş sonrası heartbeat en az İKA görev süresi kadar sürer | `tests/test_iha_landed_gate.py` (12), `tests/test_ika_no_route_recovery.py`, `tests/test_k5_k6_sure_limitleri.py` (9) | **KANITLI_TEST** | test | `Y-3.3.4-M03` · `Y-4-M12` |
| **§6.4** | "Güvenlik Pilotunun… İHA'yı **manuel moda** alması → uçuş başarısız" | YKS `mod != AUTO` uyarısı var (`comms/yks_gui.py:1254`, `:3083`) | ⚠ **Üretim HEARTBEAT'i `mod` alanını ÜRETMİYOR.** ~~Kanıt olarak "`grep mod comms/iha_sender.py` → yalnız `karar_yas`" yazılıydı; komut koşulunca **hiçbir şey** veriyor (`karar_yas` dizesi zaten `mod` içermez) — 13 Eylül'de düzeltildi.~~ Gerçek kanıt: `grep -ci "mod" comms/iha_sender.py` → **0** (dosyada `mod` dizesi hiç geçmiyor); HEARTBEAT'e yazılan alanların tamamı `grep -n "alanlar\[" comms/iha_sender.py` ile listelenir: `x` (`:481`) · `y` (`:482`) · `alt` (`:489`) · `karar_yas` (`:503`). Alanı yazan tek yer YKS'nin kendi demo üreticisidir; sahada manuel-mod tespiti **hakem/pilot gözlemine** dayanır. Bugün ölçülecek bir sayı yok: alan MAVLink `HEARTBEAT.custom_mode`'dan **türetilebilir** ama üretilmediği için okunamaz; iş `CONTRACTS §6` sözleşme değişikliği + kapı ister. Kart tarafı hazır: `FLTMODE6,9` (LAND) ve `RC6_OPTION,153` (`config/pixhawk/emir.param:392`, `:735`). **Planlanan iş: 14 Eylül sonrası, 21 Eylül 2026 uçuşu öncesi** (§6.5.1 A7) | **KOD_VAR_TEST_YOK** | gözle muayene (kod okuması); **test yok** | `Y-4-M12` |
| **§6.4** | "**Kırım ve Yapısal Bütünlük**" · "**İniş İhlali** (paraşüt açılmaması, sert iniş)" | Mekanik/emniyet. Yazılım kaydı: iniş kanıtı ve paraşüt komut zinciri (R9/R10) | Paraşüt mekaniği ve kırım denetimi repo dışıdır | **İNSAN-DONANIM** | gözle muayene (final dalgası) | `Y-3.2.1-T05` |
| **§6** | Ağırlık limitleri (İHA 25 kg / İKA 10 kg), 3 uçuş hakkı, güzergâh zorluk katsayısı, mühür | İdari/mekanik. Zorluk katsayısı **açık olan** güzergâha aittir, bizim yayınladığımıza değil → yeni yazılım gereksinimi doğurmaz | Tartı tutanakları 5 Eylül montaj gününde alınacaktı (`SAHA_HAZIRLIK_PLANI §2.1`); **5 Eylül'de de 12 Eylül'de de alınmadı** — tartı hâlâ yok. Hücre boş bırakılmıyor ama iki kütle **aynı sınıfta değildir**: **m_İKA ≈ 9400 g — DDR ÖLÇÜSÜ** (`FDR/BOLUM_3:1309`, İKA fizik gövdesi: 488×440×310 mm, 9,40 kg) → 10 000 g sınırının altında, payı **yalnız 600 g**, yani İKA limiti asıl risktir. **m_İHA — ÖLÇÜLEMEDİ** (tartı yok, T10): `FDR/BOLUM_3 §3.2.1.1.1` yalnız bir **ÖRNEK** satır verir — %50 hover itki oranına denk kütle **4260 g** (= 0,5 × 4 × 2130 g), etiketi birebir "türetilmiş; **tartı bunun altında çıkmalı**", yani bir **hedef tavandır, aracın ölçülmüş bir özelliği değildir**. ⚠ Üstelik 2130 g/motor değeri **4S 14,8 V + APC1047** veri sayfasındandır; **12 Eylül'de pil 3S 6000 mAh'e geçti (D-471/D-474) → 4S varsayımı GEÇERSİZDİR** ve 4260 g tavanı da geçersizdir (3S için üretici verisi yok → **BİLİNMİYOR**). ⚠ Ölçülmüş karşı kanıt: 6 Eylül'de üç devrilme, tlog hükmü **"ön itki yetmedi"**, M1 hasarlı (D-429); `MOT_THST_HOVER` 6 ve 12 Eylül dökümlerinde **değişmeden 0,35 fabrika değerinde** (`emir.param:580` = `mevcut.param:580`, `MOT_HOVER_LEARN,2` açık olmasına rağmen) → itki payı **ÖLÇÜLMEDİ**. **Planlanan tartı: 21 Eylül 2026** — İHA, İKA ve yük ayrı ayrı, fotoğraflı tutanak (T10 — TIKAYICI) | **İNSAN-DONANIM** | test (tartı; 5 Eylül'de **yapılmadı**, tarih BEYAN GEREKLİ) | `Y-3.2.1-T10` · `Y-3.2.2-T10` |

### 6.1.6 İzlenebilirlik matrisi — §7 (değerlendirme ve puanlama parametreleri)

Şartname §7, `Puan₂ = K_zorluk × [P_görev + (25000−m_İHA)/10 + (900−t_İHA)/5 + (900−t_hazırlık)/30 + (10000−m_İKA)/15 + (m_yük×0,01) + (600−t_İKA)/15 − C_ceza]`
formülüyle puanlar. Yazılıma düşen parametreler ve izleri:

| parametre | şartname anlamı | karşılayan bileşen | kanıt | durum | doğrulama yöntemi | yönerge kimliği (Y-) |
|---|---|---|---|---|---|---|
| `P_görev` | Görevin başarısı — **brandaya fiziksel temas** | `FINAL_WP_RADIUS` + `HB_KENAR_M` eşitsizliği; `CONTRACTS.md §7.3` | `tests/test_p9e_branda_temas.py` (5) | **KANITLI_TEST** (geometri) | hesaplama (geometrik eşitsizlik) + test | `Y-3.3.3-M02` |
| `t_İHA` | 900 s'den tasarruf edilen her 5 s | YKS İHA kronometresi, `SARTNAME_IHA_GOREV_SURESI_S` | `tests/test_k5_k6_sure_limitleri.py` (9) | **KANITLI_TEST** | test | `Y-4-M03` |
| `t_İKA` | 600 s'den tasarruf edilen her 15 s | İKA sürüş son tarihi (bekleme süresinden **ayrı**) | `tests/test_k5_k6_sure_limitleri.py` (9) | **KANITLI_TEST** | test | `Y-4-M03` |
| `t_hazırlık` | 900 s'den tasarruf edilen her 30 s | `SARTNAME_HAZIRLIK_SURESI_S`, YKS hazırlık kronometresi | kod sabiti + YKS; hazırlık provası 5 Eylül'de **yapılmadı** (D-426 tutanağında hazırlık provası satırı yok; tarih BEYAN GEREKLİ) | **KANITLI_TEST** (süre ölçümü) | test | `Y-4-M03` |
| `C_ceza` | Manuel paraşüt −50 · müdahale −100 | YKS ceza kaydı | `tests/test_yks_gui_komut_durustlugu.py` (13; 3 Eylül'de 6 — D-419 §3 birleştirmesi `bb832a2`), `tests/test_p9abc_yks.py` (13) | **KANITLI_TEST** | test | `Y-3.3.4-M01` |
| `m_İHA`, `m_İKA`, `m_yük` | Kütleler (g) | Tartı — yazılıma düşmez | Tartı **alınmadı** (5 Eylül D-426; 12 Eylül atölyesinde de yapılmadı). Hücre boş bırakılmıyor, üç terim ayrı ayrı ve **etiketleriyle** veriliyor: **m_İKA ≈ 9400 g — DDR ÖLÇÜSÜ** (`FDR/BOLUM_3:1309`) → `(10000−9400)/15` = **40 puan**; **m_İHA — ÖLÇÜLEMEDİ**, `(25000−m_İHA)/10` terimi **boş bırakılmıştır; 0 sayılmaz, hesaplanmaz** (tek mevcut sayı `FDR/BOLUM_3 §3.2.1.1.1`'in **ÖRNEK** 4260 g tavanıdır; 4S varsayımından türetilmiştir, pil 3S'e geçtiği için **geçersizdir** — ÖRNEK ≠ ölçüm); **m_yük ÖLÇÜLMEDİ** — İKA yük bağlantısı final dalgasının işidir (R22 / A1). Üçü de tartı değildir | **İNSAN-DONANIM** | test (tartı) — **planlanan ölçüm: 21 Eylül 2026**, üç kütle ayrı tutanak | `Y-3.2.1-T10` · `Y-3.2.2-T10` |
| `K_zorluk` | Açık güzergâhın zorluk katsayısı | Hakem tayin eder; bizim yayınladığımız şerit **numarasının doğruluğu** ilgilidir | `tests/test_k7_serit_dogrulugu.py` (27) | **KANITLI_TEST** | test | `Y-3.3.4-M02` |

### 6.1.7 Gereksinim kimlikleri — üç liste, tek bağ

Bu bölümde üç ayrı kimlik sistemi yan yana durur ve birbirine karıştırılmaz:

| kimlik | kaynağı | ne adlandırır | örnek |
|---|---|---|---|
| **§…** | yarışma şartnamesi | hükmün şartnamedeki yeri | §2.2.5 |
| **R1–R22** | yükümlülük haritası `results/sartname_bosluk/rapor.md` | şartname hükmünün bu projedeki yükümlülük numarası | R10 (iniş kanıtı) |
| **Y-…** | FDR yönergesi, `FDR/YONERGE_HARITASI.md` | **raporun** hangi bölümünün o gereksinimi taşıdığı | `Y-3.3.4-M03` |

§6.1.3–§6.1.6 matrislerinin son sütunu bu bağı kurar: bir şartname hükmünün
FDR'de hangi bölümde savunulduğu oradan okunur; ters yön yönerge haritasındadır.

⚠ Dördüncü liste **eksiktir**: ÖDR/DDR gereksinim numaraları. DDR metni depoda
`rapor/NAVITAS_DDR_Birlesik.docx` olarak durur ama makine okunur bir gereksinim
kütüğü değildir; bu yüzden DDR kimliği ↔ R ↔ Y eşlemesi bu bölümde **yapılmamıştır**.

- **YAPILABİLİR İŞ (ölçüm değil, belge çıkarımı) — hedef 14 Eylül 2026:** ÖDR/DDR gereksinim numaraları ↔ R1–R22 eşlemesi. Kaynak belgeler depoda **vardır** ve dizin 13 Eylül'de listelendi — diskteki adlar birebir: `rapor/NAVITAS_DDR_Birlesik.docx`, `rapor/NAVITAS_IKA_DDR.docx`, `rapor/NAVITAS_DDR_Bolum1_Ozet.docx`, `rapor/NAVITAS_DDR_Bolum2_Organizasyon_Takvim.docx`, **`rapor/NAVITIAS_DDR_2026_Bolum3_Only (5) (3).docx`** (adın boşluk ve parantezleri dâhil; "…_Only.docx" diye bir dosya **yoktur**), ayrıca `rapor/3.3.1-2-3-4_SON.docx` ve **`rapor/3.3.5_Yazilim_Mimarisi_MERGED_duzeltmeler.docx`** (R1–R22 eşlemesinin birincil kaynağı). Eksik olan makine okunur gereksinim kütüğüdür, belgenin kendisi değil; iş **bir tablo kurmaktan** ibarettir ve donanım/ölçüm beklemez. ⚠ Çıkarım betiğinde yollar **tırnaklanmalıdır** (ad boşluk/parantez içeriyor) ve `rapor/~$VITAS_DDR_Birlesik.docx` kilit artığı temizlenmelidir. Yönergenin `Y-1-M03` hükmü (*"ÖDR ve DDR'de tanımlanan gereksinimlerin nihai tasarım üzerinde doğrulandığı"*) FDR teslimine puan taşıdığı için **bugün yapılmalıdır**. Yetişmezse bu satır boş bırakılmaz: eşlemenin **neden** yapılamadığı ve yeni tarih buraya tarihli olarak yazılır.

---

## 6.2 Doğrulama yöntemleri

> `Y-6-M02` — *"Her bir gereksinimin doğrulanmasında kullanılan yöntemler açıkça
> belirtilmeli ve bu doğrulama süreçlerinde analiz, hesaplama, test, simülasyon
> veya gözle muayene gibi hangi tekniklerin kullanıldığı ifade edilmelidir."*

Yöntem, §6.1 matrislerinin **doğrulama yöntemi** sütununda satır satır yazılıdır.
Bu alt başlık o sütunun sözlüğünü, üretim yordamını ve dağılımını verir.

### 6.2.1 Yöntem sözlüğü — yönergenin beş yöntemi bu projede ne demek

| yöntem | bu projede karşılığı | ne zaman yeter | ne zaman yetmez |
|---|---|---|---|
| **test** | `tests/` altında koşan, ham çıktısı `results/` altına düşen ve çoğunda **mutasyonla** ayırt ediciliği gösterilmiş kapı | davranış repoda ve gözlenebilir olduğunda | davranış repo dışındaysa (uçuş kontrolcüsü, telsiz donanımı, gerçek arena) |
| **simülasyon** | sentetik arena (n=260) ve UDP loopback halkası | girdi dağılımının denetlenmesi gerektiğinde | gerçek sahne istatistiği gerektiğinde (§6.5 A4) |
| **hesaplama** | sözleşmeye yazılmış eşitsizlik veya türetim: gereken FPS `1/(5·p)`, süre bütçesi toplamı, `FINAL_WP_RADIUS < HB_KENAR_M/2` | sonuç aritmetik/geometrik olarak bağlayıcı olduğunda | fiziksel doğrulama gerektiğinde |
| **analiz** | kaynak, şartname ve parametre incelemesi (ör. Copter-4.5 `GCS_Mavlink.cpp` akış dizilerinin okunması) | bir davranışın **var olmadığını** göstermek dâhil | ölçümün yerine geçmez |
| **gözle muayene** | kod okuması, ekran gözlemi, montaj ve mühür kontrolü, hakem gözlemi | hüküm insana düştüğünde | yazılım davranışının **tek** dayanağı olduğunda |

⚠ **"gözle muayene" tek başına kaldığı her satır bir borçtur**, bir başarı değil.
§6.1.5'in üç satırı (müdahale −100, tekrar fırlatma, manuel mod) yalnız kod
okumasıyla doğrulanmıştır ve durum hücrelerinde **KOD_VAR_TEST_YOK** yazar.

### 6.2.2 Kanıt zinciri — bir satır nasıl "KANITLI_TEST" olur

1. **Sözleşme** `CONTRACTS.md` içinde yazılır (çıplak sabit yasak; sayı tek yerde durur).
2. **Kapı** `tests/` altına yazılır ve **gerçekten koşulur**; ham çıktı `results/` altına düşer.
3. **Mutasyon** uygulanır: ilgili kod satırı bozulur, kapının **düştüğü** gösterilir. Düşmeyen kapı ayırt edici değildir ve kanıt sayılmaz.
4. **Ön kayıt**: eşik, sonuç görülmeden yazılır (`ON_KAYIT` dosyaları) ve sonradan gevşetilmez.
5. **Çürütme**: yanlış çıkan iddia silinmez; üstü çizilir ve düzeltmesine işaret verilir (`REVIEW_LOG.md`).

3 Eylül sayımında defterde `^### D-` başlıklı **414 kanıt kaydı** (408 ayrık kayıt numarası) vardı. 5 Eylül tutanakları işlendikten sonra (son kayıt **D-427**): **432** başlık, **426** ayrık numara (`grep -c "^### D-" REVIEW_LOG.md` · `grep -o "^### D-[0-9]*" REVIEW_LOG.md | sort -u | wc -l`).

### 6.2.3 Doğrulama yöntemi dağılımı

45 gereksinim satırına toplam **66 yöntem ataması** yapılmıştır (3 Eylül sayımı 65; 5 Eylül
tutanağı §6.1.3 R2 satırına *gözle muayene* — MP Messages satırıyla firmware/parametre
yükleme teyidi — ekledi); bir satır birden
çok yöntem taşıyabildiği için oranlar toplamı %100'ü aşar. Sayılar §6.1.3–§6.1.6
matrislerinin doğrulama yöntemi sütunundan sayılmıştır. **Sayım kuralı:** hücrede
yöntem adı geçen satır o yönteme sayılır; **test yok** yazan üç satır (§6.1.5'in
müdahale, tekrar fırlatma ve manuel mod satırları) test sütununa sayılmaz. Ham
alt-dize sayımı 42 verir; uygulanan test 39'dur. Yeniden sayım betikle yapıldı:
dört matrisin 19 + 9 + 10 + 7 veri satırı, yöntem hücresinde ad arama.

| yöntem | satır | 45 satırın oranı | dağılım (1 blok = 1 satır) |
|---|---:|---:|---|
| **test** | 39 | %86,7 | ███████████████████████████████████████ |
| **gözle muayene** | 11 | %24,4 | ███████████ |
| **simülasyon** | 7 | %15,6 | ███████ |
| **hesaplama** | 5 | %11,1 | █████ |
| **analiz** | 4 | %8,9 | ████ |
| **toplam atama** | **66** | — | 45 satır |

**Okuma.** 39 satırda doğrulama koşulmuş bir kapıya dayanır. Simülasyon 7 satırda
**testin girdisidir**: o yedi satırın kanıtı sentetik sahneye bağlıdır (§6.5 A4).

Yalnız gözle muayeneye dayanan **6 satır** vardır ve ikiye ayrılır:

- **Üçü insana düşen hükümdür** ve yazılım borcu değildir: §2.2.6 (R22) yük taşıma · §5.3.2 çoklu rotorlu araç künyesi · §6.4 kırım ve iniş ihlali.
- **Üçü yazılım borcudur** ve durum hücrelerinde KOD_VAR_TEST_YOK yazar: §6.2 müdahale −100 · §6.2 tekrar fırlatma · §6.4 manuel moda alma.

Bu üç borcun ikisi §6.5.1'de açık kalem olarak sayılıdır (A8 tekrar fırlatma, A7
manuel mod). Üçüncüsü — **müdahale −100 cezasının testsiz olması** — 13 Eylül'e
kadar açık kalem listesinde **yoktu**; bu, bulunan bir eksiğin listeye işlenmemesiydi,
yani bölümün kendi kuralının ihlaliydi. **Düzeltildi:** §6.5.1'e **A14** satırı olarak
girdi ve §6.6.4 sayımına dâhil edildi. Ölçüm gerektirmeyen, tek testlik bir borçtur.

### 6.2.4 Yordamın işe yaradığı ölçülmüş altı an

Bu bölümün asıl iddiası bir uyum yüzdesi değil, **yordamdır**. Yordamın somut
işe yaradığı ölçülmüş altı an (5 ve 6 bu hafta eklendi):

1. **Ön kayıt (D-107).** Eşik sonuç görülmeden yazılır. Çözünürlük artırma denemesinde (`512 → 640`) umut verici bir ara sayı, önceden yazılmış bir RED kuralıyla karşılaştı ve **reddedildi** (sentetik arenada `p` 0,9846 → 0,7808).
2. **Mutasyon kontrolü.** Kapı, ilgili kod bozulduğunda **düşerek** ayırt ediciliğini kanıtlar. Genel kapının üretim kolunda yayın hattı bozulduğunda kol **15/15 → 6/15** düşer ve kapı düşer; tanısal kol aynı koşumda yeşil kalır — yani T155'in açtığı delik artık kapıdadır.
3. **Bağımsız çürütücü.** Uçtan uca gecikme ölçümünde raporlanan "telsiz + ACK ≈ 308 ms" kaleminin bir **soket zaman aşımı sabiti** olduğu bağımsız bir çürütücü tarafından bulundu; düzeltmeden sonra telsiz payı ~2 ms, toplam p95 **0,458 s → 0,113 s**. Yanlış sayı silinmedi, üstü çizilip düzeltmesine işaret verildi.
4. **Sızıntı denetimi.** Gerçek-kare `p` ölçümünde kullanılan havuzun **%62'sinin modelin eğitim kümesinde** olduğu bulundu; kirli okuma daha iyimserdi. Rapordaki sayı (`p = 0,3457`) **sızıntı ayıklandıktan sonrasıdır**.
5. **Çürüten tur (D-421, 4 Eylül).** "Cumartesiye hazır mıyız" sorusuna onaylayan tur hiçbir şey bulmazdı; çürüten tur **13 tıkayıcı** buldu. En ağırı: `SAHA_RUNBOOK.md §3`'teki `iha_komut_alici` komutu `--izinli-kaynak` eksik olduğu için `EXIT=2` ile ölüydü ve bunu kilitlediğini ilan eden `tests/test_p4_runbook.py` **22/22 yeşildi** — sabit jeton listesiyle alt-dize arıyordu ("Komut OLUYKEN kapi yesil"). Yeni kapı komutu **gerçekten koşar**: `tests/test_runbook_komutlari_kosuyor.py` (3 test; bayrak runbook'tan silinince T1 düştü, dosya `cmp` ile bayt-eş geri yüklendi).
6. **Amele mimarı çürüttü (D-422 §3, 4 Eylül).** Saat adımını **trafikten** ölçen mimar tasarımı önce uygulandı, sonra ölçüldü: ısrarlı bayat bir gönderici 2 saat sapmalı kurulumda "10. israrda kapidan GECTI ve MAVLink'e ULASTI" (ofset −7200,000 → −7191,750). Tasarım atıldı; adım **yerel** olarak (`duvar_farki − monotonik_farki`) ölçülüyor, reddedilen alternatif modül başlığına ve teste yazıldı. Kapı 18 → 42 test; mutasyon 17 + 5 düşük.

### 6.2.5 Ölçülemeyen ile geçen aynı şey değildir

Ve tersinden: **ÖLÇÜLEMEDİ ≠ GEÇTİ.** FDA süre bütçesi ölçümünde *"600 saniyeye
sığar"* hükmü **verilmedi**, çünkü uçuş, İKA intikali, seri telsiz ve gerçek
kamera yakalama ölçülemedi ve toplama sıfır olarak girmedi. Bunu bir nöbetçi
test kilitler: ÖLÇÜLEMEDİ listesi boşsa test düşer.

---

## 6.3 Uygunluk durumu ve gereksinimlerin tasarım kararlarıyla ilişkisi

> `Y-6-M03` — *"Her bir gereksinim için uygunluk durumu açık şekilde belirtilmeli
> ve gereksinimlerin tasarım kararları ile olan ilişkisi açıklanmalıdır."*

### 6.3.1 Uygunluk durumunun okunma kuralı — baskın durum

Her satırın uygunluk durumu §6.1 matrislerinin **durum** sütunundadır ve §6.1.1'deki
dört değerden biridir. **Dokuz satır iki durum etiketi taşır**; sayımda (§6.6)
birincil etiket alınır, ikincil etiket hücrede yazılı kalır ve gizlenmez:

| satır | birincil | ikincil |
|---|---|---|
| §2.2.1 mühür / mancınıkla fırlatma | İNSAN-DONANIM | KANITLI_TEST (yazılım mührü) |
| §2.2.2 (R2) tam otonom uçuş | ÖLÇÜLEMEDİ | KANITLI_TEST (parametre/görev şablonu) |
| §2.2.3 (R4) güzergâh aktarımı | KANITLI_TEST (UDP) | gerçek SiK için açık kalem (R20 / §6.5 A2) |
| §2.2.4 (R9) paraşüt | KANITLI_TEST (manuel zincir) | ÖLÇÜLEMEDİ (otonom tetik) |
| §2.2.6 (R13-ek) brandaya temas | KANITLI_TEST (geometri) | ÖLÇÜLEMEDİ (fiziksel koşu) |
| §5.3.2 gereken kare hızı | KANITLI_TEST (iki çerçeve) | ÖLÇÜLEMEDİ (saha `p`'si) |
| §5.3.2 azami 10 dakika | KANITLI_TEST (yazılım payı) | ÖLÇÜLEMEDİ (uçuş) |
| §6.2/§6.4 alan ihlali | KANITLI_TEST (yazılım) | ÖLÇÜLEMEDİ (Pixhawk geofence) |
| §6.2 tam otonom icra | kısmen KANITLI_TEST | İNSAN-DONANIM (İKA sürüşü) |

### 6.3.2 Gereksinim ↔ tasarım kararı bağı

Yönergenin bu maddesi uygunluk durumunun yanında **ilişkiyi** de ister: hangi
gereksinim hangi tasarım kararını doğurdu. O bağ §6.4'te on dört satırlık bir
tabloda verilmiştir; §6.1 matrislerinin *karşılayan bileşen* sütunu ile §6.4'ün
*alınan tasarım kararı* sütunu aynı bileşenleri iki farklı eksende okur.

### 6.3.3 Geçilmeyen kapılar — raporun bilerek gizlemediği yer

Şartname §5.3.1 "gereksinimlerin **doğrulandığını**" ister. Doğrulama, geçen
kapıları saymak kadar **geçmeyeni yazmakla** olur. Bu projede geçmeyen üç kapı
vardır ve hiçbiri sonradan gevşetilmemiştir.

#### 6.3.3.1 Üretim modeli v36, iki ön kayıtlı eşiği GEÇMEDEN terfi etti

Kayıt defterinin kendi cümlesiyle:

```text
🔴 ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8;
   MASKE_YOK <= 10 istendi, olculen 16.
   GECILEN: FP <= 1 (1) ve YANLIS GUZERGAH = 0 (0).
   Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi.
   ESIKLER DEGISMEDI ve sonraki terfileri baglar.
```

- **Terfi tarihi:** 2026-08-26 · **karar:** kullanıcı (insan) · **dayanak:** D-293/D-294.
- **Gerekçe:** gerçek karede yanlış güzergâh **15/21 → 7/38**, engel üstü waypoint **79 → 3**.
- **Bedeli açıkça yazıldı:** sentetik arenada K3 0→1, K4 1→4, K6 5→7 (hepsi kapı içinde kaldı); doğrulama kümesinde FP 0→2.
- **Kural nasıl korundu:** eşikler **değiştirilmedi, gevşetilmedi**; `CONTRACTS.md §12`'ye bir **istisna satırı** yazıldı ve aynı eşikler sonraki terfileri bağlamaya devam ediyor. Önceki üretim modeli v35 **silinmedi**, yedek olarak defterde tam SHA'sıyla duruyor ve geri dönüş yordamı yazılı.

#### 6.3.3.2 Yayın histerezisinin özgün eşiği (H1) düştü

`results/p5_histerezis/ON_KAYIT.md` içinde uygulamadan **önce** yazılan H1
eşiği ölçümde **sağlanmadı** (`"H1_ozgun": false`). Alt hipotezler H1a, H1b ve
H2 geçti. Ön kayıt kuralı gereği H1 gevşetilmedi; ölçüm dosyasında `false`
olarak duruyor ve raporda da öyle geçiyor.

#### 6.3.3.3 Kuru koşuda bir halka hâlâ sahipsiz

Saha zinciri kuru koşusunun **son** çalışması (2026-09-02 23:59:54):

```text
GECTI 9 · DUSTU 0 · SAHIPSIZ 1 · ATLANDI 0
kopuk_halkalar: ["motor"]
cikis_kodu: 1
```

Çıkış kodu **1**'dir, yani koşucu kendi hükmünü "başarılı" diye vermemiştir.
Sahipsiz halka İKA motor sürücüsüdür (A1).

Yeniden koşum **2026-09-04 09:52:22** (`results/saha_kuru_kosu_20260904_095222/ozet.json`):
`sayim {"GECTI": 9, "DUSTU": 0, "SAHIPSIZ": 1, "ATLANDI": 0}` · `kopuk_halkalar ["motor"]` ·
`cikis_kodu 1` · `saha_surucu_importlari []` — 2 Eylül ile aynı; 5 Eylül'de İKA
sürücüsüne dokunulmadı.

### 6.3.4 Bu raporun kaynak belgesindeki bayat satırlar

Yükümlülük haritası `results/sartname_bosluk/rapor.md` **2026-08-26/27** tarihlidir
ve bugün üç yerde **bayattır**; bu bölüm haritayı değil bugünkü ölçümü esas alır:

| harita satırı | haritada | bugün | kanıt |
|---|---|---|---|
| R13 (HB üretime bağlı değil) | AÇIK, KRİTİK | **KAPANDI** 2026-09-01 | D-386, `tests/test_t150_baglama.py` |
| R17 (alan ihlali ölçülemedi) | ÖLÇÜLEMEDİ | **yazılım tarafı KAPANDI** 2026-08-27 | D-307, `tests/test_t162_alan_ihlali.py` |
| Kuru koşu "rota DÜŞTÜ" | DÜŞTÜ | **GEÇTİ** (2026-09-02 koşusu) | `results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json` |

### 6.3.5 Kapıların bugünkü toplam durumu

Kapıların bugünkü toplam durumu (bu bölümün yazımı sırasında koşuldu, 3 Eylül 2026):

| kapı | sonuç |
|---|---|
| Genel kapı — `codes/test_rota_sentetik.py` | **GEÇTİ** · KOL 1 (tanısal) 15/15 · KOL 2 (üretim) rota 15/15 · şerit 15/15 · RC=0 |
| Tam test süiti — `python -B -m unittest discover -s tests -q` | **OK** · **1896 test**, 3 atlandı, 390,5 s · 155 test dosyası |
| Kabul kapıları K0–K6 (sentetik arena, n=260) | **7/7 GEÇTİ** (K0…K6 yedi kapıdır; artefaktın `gecti` alanında yedi anahtar vardır) |
| K7 yayınlanan şerit doğruluğu (üretim kipinde kabul koşusu) | **84/85 (%98,8)** — tek yanlış bilinen gerçek-pozitif |
| Saha zinciri kuru koşusu (10 halka) | GEÇTİ 9 · DÜŞTÜ 0 · **SAHİPSİZ 1** (motor) · çıkış kodu 1 |

**5 Eylül tutanakları işlendikten sonra** (kaynak D-419…D-427; bu düzenlemede GPU
koşumu ve tam süit koşulmadı — YKS açıkken süit koşamaz, aşağıda — sayılar
kayıtlardan alındı):

| kapı | sonuç | kaynak |
|---|---|---|
| Genel kapı — `codes/test_rota_sentetik.py` | **GEÇTİ** 15/15 · 15/15 — son kayıtlı koşum 4 Eylül (D-422 §6 regresyonu); 5 Eylül'e ait ayrı artefakt yok | `REVIEW_LOG.md:29567` |
| Tam test süiti | **2138 test**, 5 Eylül'de üç koşum: ~14:5x **1 FAIL** · ~19:1x **OK** · ~19:5x **1 FAIL**. Düşen tek test `test_p8_sim_katmani.test_comms_loopback_gecer`; sebep **ortam**: `comms/test_comms.py:35-36` üretim portlarına (5005/5006) bind ediyor, YKS canlıyken `WinError 10013` (`comms/link.py:34`); kod değişmedi. ~~Açık iş **T209**~~ → **T209 ve T210 KAPANDI** (`TASK_QUEUE.md:9600` ve `:9613`, ikisi de `- [x]`). Kök neden "ortam kusuru" değil **süreç sızıntısıydı**: `test_runbook_komutlari_kosuyor` zaman aşımında yalnız doğrudan çocuğunu öldürüyor, `yks_gui`/`ika_nav` torunları 5005/5006'yı tutuyordu (D-432, `REVIEW_LOG.md:30208`); nöbetçi `tests/test_zz_nobetci_surec_sizintisi.py` eklendi. **13 Eylül 2026 koşumu (YKS açıkken):** süit artık koşuyor — **2925 test, 603,223 s** (`results/tam_suit_20260913/tam_suit.txt:583`), ama `FAILED (failures=20, skipped=12)` (`:585`) → süit **KIRMIZIDIR** ve gevşetilmiyor. Düşen 20 testin **14'ü** belge ↔ kod aynasıdır; **kalan 6'sı belge aynası DEĞİLDİR ve üçü kapı niteliğindedir** (arena kilit SHA'sı + mutasyon nöbetçisi, İKA DDR ölçüsü, Jetson'a giden paket kopyası) — tam döküm Kanıt dizininde | D-427, `REVIEW_LOG.md:29893–29895` |
| Kabul kapıları K0–K6 · K7 (sentetik arena, n=260) | 1 Eylül koşumu geçerli: **7/7** · **84/85** — bu hafta GPU koşumu **yok**, sayı değişmedi | D-386, `t150_baglama_v36_kabul_verdikt.json` |
| Saha zinciri kuru koşusu (10 halka) | 4 Eylül 09:52:22: GEÇTİ 9 · DÜŞTÜ 0 · **SAHİPSİZ 1** (motor) · çıkış kodu 1 — 2 Eylül ile aynı | `results/saha_kuru_kosu_20260904_095222/ozet.json` |
| Pixhawk kabulü (saha, 5 Eylül) | ÖLÇÜM (MP Messages): `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` · `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` · `RCInput: decoding IBUS(1)` · pil ve emniyet düğmesi PreArm'ları kayboldu · `starting motor test` → `finished motor test`. **5 Eylül'de yapılmadı; dördün üçü sonradan kapandı:** (1) parametre dökümü **VAR** — `config/pixhawk/mevcut.param` (6 Eylül 20:22) ve `config/pixhawk/emir.param` (12 Eylül 23:55); (2) pusula/ivmeölçer/jiroskop **yeniden kalibre edildi** — iki döküm karşılaştırıldı, **ÖLÇÜM**: `COMPASS_OFS_X` 6,960523 → **−1,143088** (`:246`) · `COMPASS_DIA_X` 1,139482 → **1,050505** (`:210`) · `INS_GYROFFS_X` −0,01052934 → **−0,001136862** (`:500`) · `INS_ACC2OFFS_X` 0,04864864 → **0,04014116** (`:462`); (3) RC failsafe 6 Eylül'de ÖLÇÜLDÜ ve **DÜŞTÜ** (D-428 §2), 12 Eylül atölyesinde **GEÇTİ** (BEYAN, ham dosya yok). **Açık kalan tek kalem: pil gerilimi MP↔multimetre** — planlanan ölçüm 21 Eylül 2026 (§6.5.1 A13) | D-426 §1, §4 |

**Bu hafta eklenen kapılar** (sayım `grep -c "    def test" tests/<dosya>`, bu düzenleme sırasında):

| kapı | test | kayıt | ne kilitler |
|---|---:|---|---|
| `tests/test_yks_hakem_kanit_yolu.py` | 6 | D-412 | `_kanit_yaz` tanımlı; `comms/*.py` içinde tanımsız `self._X` çağrısı yok (AST) |
| `tests/test_yks_hakem_kanit_olaylari.py` | 22 | D-419 §2 | 16 olaylık küme: `CONTRACTS.md §6.8` ↔ `KANIT_OLAYLARI` ↔ AST eşitliği; kanıt kilidi fail-closed |
| `tests/test_iha_komut_saat_ve_tekrar.py` | 42 | D-419 §1 (18) → D-422 §6 (42) | ACK bileşen kümesi, sonuç önbelleği, saat ofseti + yerel adım |
| `tests/test_runbook_komutlari_kosuyor.py` | 3 | D-421 §2 | runbook'taki her depo komutu **gerçekten koşar**; alt-dize aramaz |
| `tests/test_wheels_sayisi_belgelerle_tutarli.py` | 4 | D-423 | belgeye yazılan tekerlek sayısı dosya sisteminden doğrulanır |
| `tests/test_pixhawk_firmware_yolu.py` | 10 | D-424 (6) + D-425 (4) | firmware 4.5.7 sabit, board_id 56, firmware → param sırası; `firmware/` yoksa **atlanır ve söyler** |
| `tests/test_yarisma_adi_kapisi.py` | 3 | D-417 | yarışma adı |
| `tests/test_fdr_sarkan_atif_kapisi.py` | 7 | D-420 | FDR içi sarkan atıf |
| `tests/test_yks_harita_yerlesimi.py` | 3 | D-kaydı yok | YKS harita yerleşimi |
| `tests/test_yks_monotonik_kronometre.py` | 3 | commit `1b94dca` (4 Eylül; D-kaydı yok) | YKS kronometreleri duvar saatinden bağımsız |

Test dosyası sayısı 155 → **182** (`ls tests/*.py | wc -l`; 180'i `test_*.py`).

**Kapı yazan elin kendi kusurları — bu hafta iki kez.** Geçilmeyen kapı kadar
yanlış yazılmış kapı da yazılır; ikisi de düzeltme turunun ürünüdür ve kayıt
defterinin kendi cümleleriyle:

- **D-423 (4 Eylül)** — `ls ~/wheels | wc -l` **51** basar, kapı **48** bekliyordu (48 yalnız `.whl`, 3 metin dosyası sayılmamıştı):

  > Kusuru mimar kendi "duzeltmesi" ile uretti. … Iki sayi da gercek, ama ayni seyi olcmuyorlar … DOGRU bir kopyada duserdi.

  Kural (`REVIEW_LOG.md:29617`): "bir belgeye sayi yazan her duzeltme, o sayiyi ureten komutun gercekten o sayiyi bastigini gostermek zorundadir." Kapı: `tests/test_wheels_sayisi_belgelerle_tutarli.py` (4).
- **D-425 (5 Eylül)** — firmware boşluğunu kapatan D-424 "stable" (= 4.7.1) indirdi; 4.7'de 31 parametrenin **9'u yok** (`RTL_ALT`, `WPNAV_SPEED`, `LAND_SPEED` birim, `ARMING_CHECK` anlam tersi):

  > D-424'un kendisi bu kusuru URETTI … Yani D-424, kendi onarimini olcmeden kapatti.

  Sahada 14:52'de `Missing 9 params` ile ölçüldü, 15:08'de 4.5.7 ile kapandı (D-426 §1). Kural (D-425 §6): beyan edilen bağımlılık **zorlanır**. Kapı: `tests/test_pixhawk_firmware_yolu.py` +4 (`SurumKilidiTests`).

---

## 6.4 Gereksinimlerin tasarım kararlarına etkisi; mimari ve performansa katkısı

> `Y-6-M04` — *"belirlenen gereksinimlerin tasarım sürecinde alınan kararları
> nasıl etkilediği ve sistem mimarisi ile performans üzerinde ne tür katkılar
> sağladığı detaylı biçimde ifade edilmelidir."*

### 6.4.1 Şartname hükmü → tasarım kararı → etki

Aşağıdaki her satır, mimarinin bir şartname hükmü **yüzünden** aldığı şekildir.
Kanıt sütunundaki her dosya §6.1 matrislerinde de geçer: bu tablo yeni bir iddia
getirmez, mevcut kanıtı neden–karar–etki ekseninde okur.

| # | gereksinim | alınan tasarım kararı | mimari / performans etkisi | kanıt |
|---|---|---|---|---|
| 1 | §2.2.5 (R10) İHA yere temas etmeden İKA hareket edemez | Sürüş izni **fail-closed latch**; iniş kanıtı iki bağımsız MAVLink alanının birlikte doğrulanması (`landed_state == ON_GROUND` **ve** `relative_alt < 1 m`, aynı sysid, ardışık 3 çift) | Tek alanın yanlış okunması görevi düşürmüyor; manuel "İHA İNDİ" düğmesi latch'i **açamıyor** | `tests/test_inis_kaniti.py` (26), `tests/test_iha_landed_gate.py` (12) |
| 2 | §2.2.5 (R10-ek) iniş kanıtı sahada sessizce ölmemeli | `AkisIstekcisi`: `SET_MESSAGE_INTERVAL` isteği başlangıçta ve her 10 s'de yenilenir, 5 s sessizlikte KIRMIZI uyarı | Pil değişiminde Pixhawk reboot'u akışı silse bile zincir kendini onarıyor; sessiz başarısızlık **görünür** oldu | `tests/test_faz_b_akis_istegi.py` (17 test, 2 mutant) |
| 3 | §5.3.2 yanlış güzergâh tespiti 0 puan | Çok katmanlı **fail-closed** ret zinciri; son savunma `iha_sender.send_open_route` (eşik altı → NO_ROUTE) | Sistem "emin değilsem sus" tarafına yaslandı: sentetik arenada yanlış güzergâh (K3) 0/256; bedeli `MASKE_YOK` oranıdır | `tests/test_rota_guven_esigi.py` (8), `tests/test_rota_ret_nedenleri.py` (10) |
| 4 | §2.2.3 / §6.2 gerçek zamanlılık | HEARTBEAT'e `karar_yas` alanı; **alan yoksa** alıcı taze saymaz | Bayat tespit canlı gösterilemiyor; gerçek uçuştaki 51 s'lik kör aralık ölçülebilir ve raporlanabilir hâle geldi | `tests/test_t169_tespit_tazeligi.py` (19), `results/b4_fps/p_ve_kosu_20260901.json` |
| 5 | §5.3.2 operasyon azami 10 dakika | YKS `--fda` kipinde süre bütçesi 900 → **600 s**; görev planı tek pas + 60 s loiter | Kötü-durum süre bütçesi **221,5 s**; kalan pay ölçülemeyen kalemler için bırakıldı, sıfır sayılmadı | `tests/test_t170_fda_sure_butcesi.py` (16), `config/pixhawk/README.md` |
| 6 | §5.3.2 asgari 30 m irtifa | `SARTNAME_ASGARI_IRTIFA_M = 30,0` sözleşmeye alındı; görev planı **32 m** (2 m baro payı) | Şart daha önce **hiç uygulanmıyordu** (D-319); şimdi her kare irtifa damgası taşıyor, 30 m altı işaretleniyor | `tests/test_t171_asgari_irtifa.py` (20) |
| 7 | §2.2.3 (R4) güzergâh aktarımı | Her karede **tam bir** mesaj (`OPEN_ROUTE` veya `NO_ROUTE`), sessizlik yok; latest-wins kuyruk; ayrı HEARTBEAT iş parçacığı | Alıcı "sessizlik = rota yok" çıkarımı yapmıyor; kuyruk şişmiyor, en yeni karar kazanıyor | `tests/test_rpi_telsiz_yayin.py` (11) |
| 8 | §2.2.6 (R13) hedef 2×2 m kırmızı H | HB dedektörü **ölçek + şekil** çiftiyle çalışır; mpp yoksa açılmaz | Ped örtülüyken 259/260 `HEDEF_YOK` (fail-closed) ve maliyet sıfır: `p` KİP A/B eşit (0,9846) | `results/t150/baglama_olcumu_20260901.json` |
| 9 | §2.2.6 (R13-ek) varış = brandaya temas | Bağlayıcı eşitsizlik sözleşmeye yazıldı: `FINAL_WP_RADIUS < HB_KENAR_M/2` | Araç merkezi ped kenarından ≥ 0,7 m içeride durur; "sınıra değdi" yorumu mimaride mümkün değil | `tests/test_p9e_branda_temas.py` (5) |
| 10 | §6.2 / §6.4 süre limitleri | İKA'da **iki ayrı son tarih** (bekleme / sürüş); tek ortak deadline yasaklandı | Bekleme süresi sürüş bütçesini yemiyor; §7'deki `t_İKA` parametresi doğru ölçülebiliyor | `tests/test_k5_k6_sure_limitleri.py` (9 test, 4 mutasyon) |
| 11 | §6.4 veri akışı sağlanamazsa uçuş geçersiz | Heartbeat aralığı 1,0 s < zaman aşımı 3,0 s; iniş sonrası heartbeat en az İKA görev süresi kadar sürer | İki ardışık paket kaybı bağlantıyı düşürmüyor, gerçek kopma düşürüyor; güvenli duruş yanlış tetiklenmiyor | `tests/test_iha_landed_gate.py` (12), `tests/test_ika_no_route_recovery.py` |
| 12 | §6.2 / §6.4 alan ihlali (300×300 m) | Konum **aynı telemetri okuyucusundan** alınır; ikinci yol açılmadı | GUI'nin gördüğü `x,y` ile üretimin gördüğü aynı; D-307'deki "sahada ölü kapı" örüntüsü tekrarlanmıyor | `tests/test_t162_alan_ihlali.py` (19) |
| 13 | §2.2.5 (R12) İKA otonom sürüş | `GercekSurucu` arka uçsuz **kurulamaz** (`DONANIM_YOK`); sessiz iskelet yasaklandı | Eksik donanım kuru koşuda `SAHİPSİZ` görünüyor, yeşil görünmüyor; koşucunun çıkış kodu 1 | `tests/test_p3_ika_surucu.py` (14), `results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json` |
| 14 | §5.3.2 hakem onayı (İKA yokken) | `--fda` bayrağı: İKA kanıtı aranmaz, dayanağı ekranda basılır; ayrım kodda **tek yerde** (`CONTRACTS.md §6.7`) | 21 Eylül provasında İKA olmadan hakem onayı akışı tıkanmıyor; iki araç tek kod tabanında kalıyor | `tests/test_faz_b_yks_fda_kipi.py` (9 test, 4/4 mutant) |

### 6.4.2 Gereksinimin performansa maliyeti — ölçülmüş üç örnek

Gereksinim her zaman performansı **artırmaz**; bu projede üç kez performansı
bilerek geri verdi ve üçünün de bedeli ölçülüp yazıldı:

1. **Çözünürlük artırma reddedildi.** "Yanlış güzergâh yok" hükmü `512 → 640` denemesini reddetti: sentetik `p` 0,9846 → 0,7808, FPS maliyeti 1,302 (`results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1, D-377). Karar performans lehine değil, hüküm lehine verildi.
2. **v36 terfisi bedelle alındı.** Gerçek karede yanlış güzergâh 15/21 → 7/38 ve engel üstü waypoint 79 → 3 kazanıldı; karşılığında sentetik arenada K3 0→1, K4 1→4, K6 5→7 ve doğrulama kümesinde FP 0→2 ödendi (§6.3.3.1).
3. **Histerezis gecikme karşılığında kararlılık aldı.** Yayın çevrilmesi 13→7 ve 24→11'e indi; bedeli en fazla K−1 karelik bastırmadır ve NO_ROUTE **hiç** geciktirilmez (`results/p5_histerezis/olcum_20260903.json`).

### 6.4.3 Katkının sayısal karşılığı

| ölçüt | değer | kaynak |
|---|---|---|
| uçtan uca kare gecikmesi p50 / p95 | 0,085 s / 0,113 s | `results/fda_butce/olcum_20260901.json` |
| gereken kare hızı (en kötü uçuş) | 0,61 FPS | `results/b4_fps/p_ve_kosu_20260901.json` |
| görev süresi kötü-durum bütçesi | 221,5 s ≤ 600 s | `config/pixhawk/README.md` |
| yayınlanan şerit doğruluğu (üretim kipi) | 84/85 (%98,8) | kabul koşusu, D-386 |
| yanlış güzergâh (sentetik arena, K3) | 0/256 | `t150_baglama_v36_kabul_verdikt.json` |
| HB hedefi doğru pedde | 253/256 | `results/t150/baglama_olcumu_20260901.json` |

⚠ Bu satırların **hiçbiri gerçek arenada ölçülmemiştir** (§6.5 A4); ölçüm çerçevesi
sentetik arena ve UDP loopback'tir. Sayılar bu çerçevenin dışına taşınamaz.

---

## 6.5 Karşılanamayan ve kısmen karşılanan gereksinimler

> `Y-6-M05` — *"Karşılanamayan veya yalnızca kısmi olarak karşılanan gereksinimler
> bulunması durumunda, bu durumun nedenleri açıkça belirtilmeli ve söz konusu
> eksikliklerin giderilmesine yönelik alınan önlemler veya planlanan iyileştirme
> çalışmaları raporda açıklanmalıdır."*

### 6.5.1 Açık gereksinimler — kapanmamış olanların tam listesi

Aşağıdaki satırlar bugün itibarıyla **kapanmamıştır**. Her birinin ne zamandan
beri açık olduğu ve neyin eksik olduğu yazılıdır. Bu tablo raporun en önemli
tablosudur: kapanmış işleri saymak kolaydır, açık kalanı yazmak zordur.

⚠ **İki ayrı A-numaralaması vardır ve birbirine çevrilmez.** Bu tablodaki **A1–A14
açık gereksinim kalemleridir**; `ATOLYE_TEST_GUNU_20260912.md`'deki A1–A14 ise
**atölye test adımlarıdır**. Çakışan numaralar:

| numara | bu tabloda (açık kalem) | atölye kâğıdında (test adımı) |
|---|---|---|
| **A6** | üretim yolunda K2/K3 ihlal denetimi | SiK RTT/kayıp ölçümü — 13 Eylül 01:2x'te koşuldu ve **DÜŞTÜ** (D-476); bu tablodaki karşılığı **A2**'dir |
| **A11** | `--fda` kipinin bağımsız denetim borcu | camdan cama video gecikmesi — `results/atolye_20260912/A11_gecikme_HESAP.md`, **HESAP** 328/482/675 ms ≤ 1000 ms eşiği (ölçüm değil) |
| **A12** | otonom paraşüt tetiği | hover (12 Eylül, GUIDED, 3 m, ~15 s + kodla LAND) |
| **A13** | Pixhawk failsafe / geofence / parametre dökümü | PM06 ↔ pens ampermetre akım doğrulaması — **pens ampermetre elde olmadığı için yapılmadı** (D-473) |

| # | şartname maddesi | açık olan | ne zamandan beri | neden kapanmadı | kapanma koşulu | yönerge kimliği (Y-) |
|---|---|---|---|---|---|---|
| **A1** | §2.2.5 (R12) | **Gerçek İKA motor sürücüsü yok.** Arayüz, kabul harnessı ve fail-closed davranış hazır; `GercekSurucu` arka uçsuz kurulmuyor (`DONANIM_YOK`). Kuru koşu halka 10 `SAHİPSİZ`, saha sürücü importları `[]` | **2026-07** (D-22'nin dört kopukluğundan biri); arayüz 2026-09-02'de eklendi | **Donanım kararıdır**: hangi sürücüye (seri / PWM / GPIO / MAVLink) bağlanacağı seçilmedi. Yazılım kendi kendine kapatamaz | Arka uç bağlanıp `scripts/ika_surucu_kabul.py` K1–K6 GEÇTİ; İKA hattı **final dalgası** | `Y-3.3.3-M01` · `Y-4-M07` |
| **A2** | §2.2.3 (R20) | ~~**Gerçek SiK hattı hiç ölçülmedi.** Bugüne kadarki tüm aktarım kanıtı UDP loopback'tir~~ → **13 Eylül 2026 01:24–01:25: gerçek RF hattı ÖLÇÜLDÜ ve eşiği AŞTI — ölçüm VAR, hüküm DÜŞTÜ; eşik gevşetilmedi** (D-476). Kaynak: `results/atolye_20260912/A6_sik_ikago.json` · `A6_sik_parasut.json` (`scripts/sik_rf_olc.py`, `"tasiyici":"seri"`, `"port":"COM7"`, `"baud":57600` — **gerçek telsiz, UDP değil**; her koşum n=200, iki koşum tekrarlandı ve sayılar yeniden üretildi). **Paket kaybı %0** (200/200 ACK, geç ACK 0). RTT — İKA_GO kadansı (0,25 s): p50 **208,3** · p95 **265,2** · min 93,1 · maks 273,3 ms, eşik `IKA_GO_TEKRAR_ARALIGI_S` = **250 ms** (`codes/karar_sozlesmesi.py:2096`) → **AŞILDI**; paraşüt kadansı (0,20 s): p50 **229,2** · p95 **229,6** · min 199,1 · maks 230,8 ms, eşik `PARASUT_TEKRAR_ARALIGI_S` = **200 ms** (`:2117`) → **AŞILDI**. Betiğin kendi hükmü: `"verdikt": "UYARI: RTT p95 tekrar araligini asiyor"` · `"cikis_kodu": 1`. Anlamı: ACK daha yoldayken komut yeniden gönderilir → hat şişer; **tekrar tasarımı bugünkü hat gecikmesiyle geçersizdir**. Teşhis: kayıp %0, doluluk %4,4 → darboğaz **bant genişliği değil, SiK TDM dilim gecikmesi** (0,20 s'de RTT çakılı sabit, p95−p50 = 0,4 ms; 0,25 s'de testere dişi; seri payı ≈28 ms). **Kazanç:** `Y-3.3.4-M03`'ün istediği "kullanılan veri hızı" artık gerçek RF üzerinde ölçüldü — **318,8 B/s** (0,25 s) ve **350,5 B/s** (0,2 s); önceki 322,5 B/s radyosuz köprü ölçümüydü, ikisi %1–9 içinde örtüşüyor. ⚠ **DDR'deki ">%98 paket teslimi, 300 m" iddiasının kanıtı HÂLÂ YOKTUR:** bu ölçüm masa mesafesindedir ve menzil hakkında hiçbir şey söylemez; menzil koşusu (atölye A7) **yapılmadı** (D-473) | **2026-08-26**'dan beri açık olarak kayıtlı; RTT/kayıp **2026-09-13**'te ölçüldü ve **DÜŞTÜ** | ~~5 Eylül: iki SiK bağlandı (BEYAN, D-426 §1), RTT/kayıp ölçülmedi~~ → Kapanmama nedeni artık **ölçüm eksiği değil, sonucun eşiği aşmasıdır**. Menzil ise hâlâ hiç ölçülmedi (açık alan ve ikinci operatör gerekiyor) | Açık kalan iş ölçüm değil **düzeltmedir**: **T263** SiK Air Speed yükseltilip A6 yeniden ölçülür → yetmezse **T264** ECC kapatılıp yeniden ölçülür → o da yetmezse **T265** tekrar aralıkları ayrı bir **tasarım kararıyla** büyütülür (eşik gevşetme değil: sözleşme değişikliği + görev zamanlaması etkisi + yeniden doğrulama). Ölçülmemiş kalanlar: SiK firmware/AirSpeed/ECC künyesi ve **menzil** — ön kayıtlı kabul, eğik **≥ 425,5 m**'de `sik_rf_olc` çıkış 0 ∧ YKS videosu CANLI (`ATOLYE_TEST_GUNU_20260912.md:133`); daha kısa mesafede ölçülürse "kısmi — d m" yazılır ve menzil kabulü **ÖLÇÜLEMEDİ** kalır. **Planlanan: 21 Eylül 2026 uçuşu öncesi** | `Y-3.3.4-M03` · `Y-4-M05` · `Y-4-M09` |
| **A3** | §2.2.2 / §6.2 (R2) | ~~**Gerçek otonom uçuş hiç koşmadı**… hiçbir motor dönmedi~~ → **İlk hover ve kodla LAND yapıldı (12 Eylül, GUIDED); AUTO görevi hâlâ uçmadı.** ÖLÇÜM: `config/pixhawk/emir.param:980` `STAT_FLTTIME,273` s (6 Eylül `mevcut.param:980` = 0) · `:979` `STAT_BOOTCNT,96` (48). BEYAN: 12 Eylül atölyesi — **GUIDED** kipinde kodla 3 m'de 15 s hover + **kodla LAND**, kumanda müdahalesiz. Açık kalan: Loiter/AUTO görev uçuşu ve 30 m tam prova | **2026-07** (proje başından); hover kolu **2026-09-12'de kapandı** | ⚠ `STAT_FLTTIME` **kümülatiftir** (48 açılış boyunca birikti), tek uçuşun süresi değildir; BEYAN edilen ~15 s ile arasındaki **258 s açıklanmamıştır**. Uçuşun `.bin` logu SD karttan **silinmiş** → `VIBE`/EKF/pusula ofseti/`IHA_LANDED` damgası analiz edilemedi, hover kanıt sınıfı **BEYAN** kalır. Ayrıca `MOT_THST_HOVER,0.35` (`emir.param:580`) `MOT_HOVER_LEARN,2` (`:565`) açık olmasına rağmen **her iki dökümde de fabrika değerinde** → askıda öğrenme tetiklenmemiş; bu hover'ın **aleyhine karşı kanıttır**, **itki payı ÖLÇÜLMEDİ**. AUTO için ayrıca 30 m'lik saha ve tam prova gerekiyor | AUTO görev uçuşu + `.bin` logunun saklanması + `MOT_THST_HOVER`'ın öğrenmesi; **planlanan ölçüm: 21 Eylül 2026 uçuşu** (SD kart silme yasağı `SAHA_RUNBOOK`'a girer) | `Y-4-M10` · `Y-4-M12` |
| **A4** | §5.3.2 / §2.2.2 | **Gerçek arena karesi yok.** K0–K6 kabul kapılarının tamamı sentetiktir (T66 ada kadrajı, n=260). Gerçek doğrulama kümesi (DJİ 0038) kırsal bir yol çekimidir: kırmızı H, moloz yığını, bariyer **içermez** | **2026-08-26** (D-290) | Maket çekimi yapılmayacak (kullanıcı kararı); gerçek arena yalnız yarışma günü görülecek | Saha `p`'si 21 Eylül'de ilk kez ölçülür. Bu boşluk rapor tarihinde **kapatılamaz** | `Y-3.3.4-M02` · `Y-4-M08` |
| **A5** | §5.3.2 (gerçek zamanlılık) | **Gerçek uçuşta 45–51 saniyelik, sahne bağıntılı kör aralıklar** ölçüldü: model bitişik bloklar boyunca hiç karar üretmiyor (0038'de 51 kare, 46'sı `MASKE_YOK`). Tazelik penceresi 5 s → aralık pencereyi **10 kat** aşıyor | **2026-09-01** (D-374) | Bu bir **hız** sorunu değildir (gereken FPS 0,61, band 0,9–2,6): daha hızlı örneklemek aynı köre daha çok bakmaktır. Kalan iş **model tarafındadır** | Arena benzeri veriyle eğitim/ince ayar; ya da uçuş planında aynı bölgeden ikinci geçiş. **Açık** | `Y-3.3.4-M02` · `Y-4-M08` |
| **A6** | §2.1 (R1-ek) | **Üç-güzergâh adayı kapısı ve K2/K3 ihlal denetimi üretim yolunda yok.** `koridor_adaylari` + `rota_dogrula` yalnız tanısal kolda (`rota_bul`) koşar | **2026-08-26** (`CONTRACTS §11.2-EK`, ikinci boşluk) | T156 üretim yolunun **kararını** kapıya soktu, **ihlal denetimini taşımadı** | Denetimin `analyze_path` koluna taşınması + mutasyonla ayırt ediciliğin gösterilmesi | `Y-3.3.4-M01` |
| **A7** | §6.4 (R21) | **Uçuş kipi (`mod`) üretim telemetrisinde yok.** YKS "manuel moda alındı" uyarısını gösterebiliyor ama alanı üreten üretim kodu yok | **2026-08-26**'dan beri kayıtlı | Alan MAVLink `HEARTBEAT.custom_mode`'dan türetilebilir; iş küçük ama sözleşme (`CONTRACTS §6`) değişikliği ister | `iha_sender.send_heartbeat` alanı taşısın + kapı | `Y-3.3.4-M03` · `Y-4-M12` |
| **A8** | §6.2 (tekrar fırlatma) | Davranış doğru (kronometre yeniden başlamıyor) ama **doğrudan testi yok** | 2026-08-26 | Küçük kapsam; sırası gelmedi | Tek testlik iş | `Y-4-M01` |
| **A9** | §2.2.6 / §7 | ~~**Gazebo fiziksel temas koşusu ÖLÇÜLEMEDİ** (bu geliştirme makinesinde `gz` yok)~~ → **10 Eylül: MuJoCo'da koşuldu (SENTETİK, Bölüm 3 §3.3.3)** — Gazebo iskeleti önceki tasarımdır, koşulmadı; İKA fizik sürüşü YER GERÇEĞİ rotayla 45/45, ÜRETİM MODELİ rotayla 9/45 (harita 0/15 → H1-K5 DÜŞTÜ) | 2026-09-02 (D-391) | ~~Ortam eksik~~ ortam MuJoCo (D-438) | ~~Gazebo'lu makinede prova koşusu~~ açık: video linki **BEYAN GEREKLİ (insan)** (T222) | `Y-3.3.3-M01` · `Y-3.3.3-M02` · `Y-3.3.3-M03` · `Y-4-M07` |
| ~~**A10**~~ | §5.3.2 (Jetson) | ~~**Nano'da FPS ve CUDA durumu ölçülmedi.** v36 YOLOv8m-seg'dir; Nano **CPU** torch ile 512'de kapının (0,61 FPS) altına düşebilir~~ → **KAPANDI 6 Eylül (D-431):** kart **Orin Nano Developer Kit 4 GB** (Nano değil); `torch.cuda.is_available()` **True**; `scripts/jetson_fps.py` p50/p95: pt **1,35/1,06** · engine **1,58/1,33** FPS ≥ 0,61 → **GEÇTİ**, eşik gevşetilmedi. Sınır: mpp=None, kareler diskten, kamera bağlı değil; ONNX kolu HATA | **2026-09-03** (D-406) → kapanış **2026-09-06** | 5 Eylül'de Jetson takılmadı (D-426 §4); 6 Eylül'de kartta ölçüldü — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` | — (koşul karşılandı) | `Y-4-M04` |
| **A11** | §5.3.2 (denetim) | **`--fda` kipinin bağımsız denetimi yok**: sözleşmeyi (`CONTRACTS §6.7`) de uygulamayı da aynı el yazdı | 2026-09-03 (D-408, borç açıkça kaydedildi) | Denetleyen ajan kotada | Hakem rolü oynanarak gerçek provada doğrulama (21 Eylül öncesi) | `Y-4-M11` |
| **A12** | §2.2.4 (R9) | **Otonom paraşüt tetiği ölçülmedi**; mekanik açma sistemi ve `CHUTE_*` parametreleri final dalgasının işidir. Kart tarafında **ölçülen tek değer** `CHUTE_ENABLED,0` (`config/pixhawk/emir.param:194`) — otonom tetik bugün **kapalıdır**; bu bir ölçümdür ama hükmü karşılamaz | Proje başından | Sabit kanat platformu ve mekanik açma düzeneği henüz yok | Mekanik düzenek + `CHUTE_*` açılıp yer testinde tetikleme; **planlanan ölçüm: final dalgası, 30 Eylül–3 Ekim öncesi** (`SAHA_HAZIRLIK_PLANI §7`) | `Y-3.2.1-T05` · `Y-4-M12` |
| **A13** | §6.2 / §6.4 (Pixhawk failsafe · geofence · parametre dökümü) | ~~Kart dökümü yok, failsafe/geofence doğrulanmadı~~ → **büyük ölçüde KAPANDI (12 Eylül).** ÖLÇÜM (`config/pixhawk/emir.param`, 12 Eylül 23:55): `FENCE_ENABLE,1` (`:361`) / `FENCE_ACTION,1` (`:358`) / `FENCE_ALT_MAX,50` (`:359`) · `FS_THR_ENABLE,3` (`:411`) · `FS_THR_VALUE,975` (`:412`) · `FS_GCS_ENABLE,5` (`:408`) · `FS_GCS_TIMEOUT,5` (`:409`) · `BATT_FS_LOW_ACT,1` (`:134`) · `BATT_FS_CRT_ACT,1` (`:133`) · `ARMING_CHECK,1` (`:28`) · `LOG_BITMASK,176126` (`:536`); pusula/ivmeölçer/jiroskop yeniden kalibre (`COMPASS_*`, `INS_*` değerleri 6 Eylül dökümüne göre değişti). BEYAN (12 Eylül atölyesi): RC failsafe, pil failsafe, anahtarla LAND ve bağlantı kaybı **GEÇTİ**; GCS failsafe **KISMİ** — tetikleme çalıştı, MP bağlantısı olmadığı için kodla uçurulamadı (D-473). **Açık kalan iki şey:** (1) pil gerilimi MP↔multimetre; (2) pil künyesi 3S 6000 mAh'e geçtiği hâlde 12 Eylül dökümünde `BATT_CAPACITY,3300` (`:129`) ve `BATT_CRT_VOLT,9` (`:131`) duruyordu — 13 Eylül'de karta **6000** ve **10,5 V** yazıldığı BEYAN edildi (kullanıcı), **yeni döküm alınmadı** → dosyayla doğrulanmadı (T258) | **2026-09-05** (D-426 §4) | 12 Eylül atölyesinin ham dosyası yok (BEYAN); failsafe'ler **tetiklenerek** değil parametre olarak okundu | Pil gerilimi ölçümü + 13 Eylül parametre dökümünün alınması (T258) + failsafe tetikleme kaydı; **planlanan ölçüm: 21 Eylül 2026 uçuşu öncesi** | `Y-4-M12` |
| **A14** | §6.2 (müdahale −100) | **Müdahale −100 cezasının ve hazırlık kronometresinin devamının doğrudan testi yok**; davranış `comms/yks_gui.py::mudahale` içinde kodda var. §6.2.3'te kayda geçmişti ama 13 Eylül'e kadar bu listeye **işlenmemişti** — listenin kendi kusuru | 2026-08-26 (listeye giriş 2026-09-13) | Kapsam küçük, sırası gelmedi; ölçüm değil **yazılım borcu** | Tek testlik iş: −100 kaydı **ve** kronometrenin durmaması mutasyonla kilitlenir; **planlanan iş: 14 Eylül FDR teslimi sonrası, 21 Eylül uçuşu öncesi** | `Y-3.3.4-M01` · `Y-4-M01` |

**Açık satır sayımı:** ~~12~~ ~~11~~ **13** (13 Eylül). Sayım daha önce **iki farklı değer** veriyordu — burada 11, §6.6.4'te 12 — çünkü **A13 sayılıyor ama satırı yazılmamıştı**; satır yazıldı ve **A14** (müdahale −100, §6.2.3'ün bulup listeye işlemediği borç) eklendi. A10 6 Eylül'de kapandı (D-431).
Bunların **4'ü donanım/veri beklemektedir** (A1, A2, A3, A4), **3'ü ölçüm bekleyen risktir** (A5, A9, A13),
**4'ü yazılım borcudur** (A6, A7, A8, A14), **2'si denetim/final borcudur** (A11, A12).
4 + 3 + 4 + 2 = **13**; aynı sayı §6.6.4'te tekrarlanır ve iki yer artık çelişmez.

### 6.5.2 Kapanma penceresi ve tarihi verilmemiş kalemler

3 Eylül sürümünde §6.5.1'in *kapanma koşulu* sütununda **yedi kalemin tarihi
yazılıydı**: A2 ve A10 (5 Eylül) · A3 (montaj sonrası ilk hover → Loiter/Auto →
tam prova) · A11 (21 Eylül öncesi) · A4 (ilk ölçüm 21 Eylül; **rapor tarihinde
kapatılamaz**) · A1 ve A12 (final dalgası).

**5 Eylül geçti; A2 ve A10 kapanmadı** (D-426): SiK bağlandı ama RTT/kayıp
ölçülmedi, Jetson takılmadı. **A10 6 Eylül'de kapandı** (D-431): Jetson araca değil tezgâha
alındı, kart Orin Nano Developer Kit 4 GB çıktı, FPS kapısı GEÇTİ. A3'ün montaj adımı yapıldı (firmware, parametre,
GPS, RC, güç, motor testi — ÖLÇÜM); ilk hover plana göre Pazar 6 Eylül'e bırakıldı
(D-426 §5), AUTO uçuş yok. **A13** 5 Eylül'de açıldı. Tarihi hâlâ yazılı olanlar:
A3 (ilk hover → tam prova) · A11 (21 Eylül öncesi) · A4 (21 Eylül) · A1 ve A12
(final dalgası).

**~~Sekiz~~ ~~Yedi~~ Hiçbir kalem tarihsiz bırakılmadı (13 Eylül).** İki çıpa kesinleşti —
**FDR teslimi 14 Eylül 2026**, **uçuş 21 Eylül 2026** (ikisi farklı tarihtir) — ve her açık
kalem bu iki tarihe göre konumlandırıldı. Tarih **uydurulmadı**: aşağıdaki sütun *planlanan*
ölçüm/iş tarihidir, hiçbir satırı "kapandı" saymaz.

| kalem | planlanan ölçüm / iş | tarih | kim |
|---|---|---|---|
| **A2** gerçek SiK RTT/kayıp | ~~ölçüm~~ → **ölçüldü ve DÜŞTÜ** (13 Eylül, p95 265,2/229,6 ms vs eşik 250/200); kalan iş **düzeltme**: T263 Air Speed → T264 ECC → gerekirse T265 tasarım kararı. Menzil (≥ 425,5 m) ayrıca ölçülecek | **21 Eylül uçuşu öncesi** | insan + yazılım |
| **A5** kör aralıklar | saha `p`'si ile birlikte ilk gözlem | **21 Eylül 2026** | ölçüm |
| **A6** üretim yolunda ihlal denetimi | `analyze_path` koluna taşıma + mutasyon kanıtı | **14 Eylül sonrası, 21 Eylül öncesi** | yazılım |
| **A7** `mod` alanı | `CONTRACTS §6` değişikliği + `send_heartbeat` + kapı | **14 Eylül sonrası, 21 Eylül öncesi** | yazılım |
| **A8** tekrar fırlatma testi | tek testlik iş | **14 Eylül sonrası** | yazılım |
| **A9** fizik koşusu + video | yeni iz genişliğiyle (0,4595 m) yeniden koşum (T256) · video linki (T222) | **13–14 Eylül** · video: insan | yazılım + insan |
| **A13** pil gerilimi · parametre dökümü | MP↔multimetre + 13 Eylül dökümünün alınması (T258; `BATT_CAPACITY` 6000 ve `BATT_CRT_VOLT` 10,5 V yazıldığı BEYAN edildi, dosyayla doğrulanmadı) | **21 Eylül uçuşu öncesi** | insan |
| **A14** müdahale −100 testi | tek testlik iş, mutasyonlu | **14 Eylül sonrası** | yazılım |

⚠ Bu tablo bir **plandır, ölçüm değildir**. Tarihi kaçan satır, kaçtığı gün
gerekçesiyle birlikte buraya yazılır; silinmez.

- ~~**BEYAN GEREKLİ (insan):** … kapanma tarihi — hangisi 21 Eylül provasından önce, hangisi sonra kapanacak.~~ → **Yukarıdaki plan tablosuyla yanıtlandı (13 Eylül).** İnsan onayı bekleyen şey artık tarih değil, tarihi **tutan işler**: A2'nin düzeltilip sahada yeniden ölçülmesi (T263/T264) ve A9 videosunun çekilmesi (T222). A10 6 Eylül'de kapandı (D-431).

İki kalem hakkında bu bölümün açık hükmü vardır ve gizlenmez:

- **ÖLÇÜLEMEDİ:** A4 — gerçek arena karesi yoktur ve maket çekimi yapılmayacaktır; saha `p`'si ilk kez 21 Eylül provasında ölçülür. Bu boşluk **rapor tarihinde kapanmaz**.
- ~~**ÖLÇÜLEMEDİ:** A2 — gerçek SiK hattının gecikme ve paket kaybı ölçümü~~ → **ÖLÇÜLDÜ ve DÜŞTÜ (13 Eylül 2026, D-476).** `scripts/sik_rf_olc.py` gerçek seri hatta (COM7 @57600, n=200×2) koşuldu: kayıp **%0**, RTT p95 **265,2 ms** (eşik 250) ve **229,6 ms** (eşik 200) → **ikisi de aşıldı**, `cikis_kodu 1`. Eşik **gevşetilmedi**, sonuç yazıldı. 3 Eylül'de "5 Eylül'de kapanır" yazılıydı; 5 Eylül'de SiK yalnız **bağlandı** (BEYAN, D-426 §1). **Hâlâ ÖLÇÜLEMEDİ olan: menzil** — ön kayıtlı kabul eğik ≥ 425,5 m'dir ve o koşu yapılmadı, dolayısıyla DDR'nin ">%98 teslim, 300 m" iddiası **kanıtsız** kalır.

---

## 6.6 Genel uygunluk durumu — özet tablo ve pasta grafiği

> `Y-6-M06` — *"Son olarak tüm gereksinimlerin genel uygunluk durumu özet bir tablo
> veya pasta grafiği ile görsel olarak sunulmalıdır."*

> **Grafik notu (7 Eylül 2026).** §6.6.2 halka grafiği ve §6.6.3 çubuk grafiği artık
> markdown'a gömülü SVG'dir (`sekiller/uygunluk_pasta.svg`, `sekiller/uygunluk_yontem.svg`);
> ikisi de `scripts/fdr_sekil_uret.py` ile **bu bölümdeki tablolardan okunarak** üretilir,
> sayılar `tests/test_gece_sekiller.py` ile tabloya karşı her koşuda sınanır. Metin tabanlı
> barlar, grafiği açamayan okur için korunmuştur. §6.6.4 yalnız tablodur (aşağıda not).
> PDF dizgisi (`scripts/fdr_pdf_uret.py`) aynı SVG dosyalarını basar.

### 6.6.1 Durum sayımı — matris matris döküm

Bu bölümde izlenen **45 gereksinim satırı** (§2.1–§2.2: 19 · §5.3.2: 9 · §6.2/§6.4: 10 · §7: 7):

| matris | satır | KANITLI_TEST | KOD_VAR_TEST_YOK | ÖLÇÜLEMEDİ | İNSAN-DONANIM |
|---|---:|---:|---:|---:|---:|
| §6.1.3 — §2.1 / §2.2 | 19 | 14 | 1 | 1 | 3 |
| §6.1.4 — §5.3.2 | 9 | 7 | 0 | 1 | 1 |
| §6.1.5 — §6.2 / §6.4 | 10 | 5 | 3 | 0 | 2 |
| §6.1.6 — §7 | 7 | 6 | 0 | 0 | 1 |
| **toplam** | **45** | **32** | **4** | **2** | **7** |

Sayım kuralı §6.3.1'dedir (baskın/birincil etiket). Döküm burada verilmiştir ki
sayı kontrol edilebilsin: her satırın durumu kendi hücresinden okunur.

**Yeniden sayım (5 Eylül tutanakları işlendikten sonra):** 45 satır · KANITLI_TEST 32 ·
KOD_VAR_TEST_YOK 4 · ÖLÇÜLEMEDİ 2 · İNSAN-DONANIM 7 — **değişmedi**. Yöntem: dört
matrisin her veri satırında *durum* hücresindeki ilk kalın etiket alındı ("kısmen
KANITLI_TEST" → KANITLI_TEST), satırlar betikle sayıldı (19 + 9 + 10 + 7 = 45). Bu
hafta işlenen kayıtlar (D-412, D-419, D-421, D-422, D-424, D-425, D-426) hücrelerin
**kanıt** ve **yöntem** sütunlarını değiştirdi, hiçbirinin birincil durumunu
değiştirmedi: R2 hâlâ ÖLÇÜLEMEDİ (AUTO uçuş yok), müdahale ve tekrar fırlatma hâlâ
KOD_VAR_TEST_YOK (yeni testler cezayı ve tekrarı sınamıyor), `mod` alanı hâlâ
üretilmiyor (`comms/iha_sender.py` yalnız `karar_yas`), künye satırı hâlâ
İNSAN-DONANIM (kutu açıldı, üç fark BEYAN).

### 6.6.2 Genel uygunluk dağılımı (pasta grafiği verisi)

| durum | satır | oran | dağılım (50 blok = %100) |
|---|---:|---:|---|
| **KANITLI_TEST** | 32 | %71,1 | ████████████████████████████████████ |
| **İNSAN-DONANIM** | 7 | %15,6 | ████████ |
| **KOD_VAR_TEST_YOK** | 4 | %8,9 | ████ |
| **ÖLÇÜLEMEDİ** | 2 | %4,4 | ██ |
| **toplam** | **45** | **%100,0** | 50 blok |

Yeniden sayım 5 Eylül sonrası: **aynı** (32 / 7 / 4 / 2; yöntem §6.6.1). Pasta grafiği
verisi bu dört satırdır; dizgide yüzdeler ve etiketler aynen taşınır.

![Genel uygunluk dağılımı — 45 gereksinim satırı, §6.6.2 verisinden](sekiller/uygunluk_pasta.svg)

*Halka grafiği §6.6.2 tablosundan üretildi (`scripts/fdr_sekil_uret.py`, 7 Eylül 2026). Renk: yeşil
kanıtlı · gri yazılım kapsamı dışı (insan/donanım) · sarı kısmen (kod var, test yok) · kırmızı açık
(ölçülemedi). Dilim sayıları, oranları ve yay açıları `tests/test_gece_sekiller.py` ile tabloya karşı
sınanır; tablo değişirse grafik yeniden üretilmeden kapı düşer.*

### 6.6.3 Doğrulama yöntemi dağılımı (ikinci grafik verisi)

Sayılar §6.2.3'ten; bir satır birden çok yöntem taşıdığı için toplam 45'i aşar.
Sayım kuralı ve **test yok** istisnası §6.2.3'te yazılıdır. Yeniden sayım 5 Eylül
sonrası: toplam atama 65 → **66** (gözle muayene 10 → 11); diğer dört yöntem aynı.

| yöntem | satır | 45 satırın oranı | dağılım (1 blok = 1 satır) |
|---|---:|---:|---|
| test | 39 | %86,7 | ███████████████████████████████████████ |
| gözle muayene | 11 | %24,4 | ███████████ |
| simülasyon | 7 | %15,6 | ███████ |
| hesaplama | 5 | %11,1 | █████ |
| analiz | 4 | %8,9 | ████ |

![Doğrulama yöntemi dağılımı — 45 satır, 66 yöntem ataması, §6.6.3 verisinden](sekiller/uygunluk_yontem.svg)

*Çubuk grafiği §6.6.3 tablosundan üretildi (`scripts/fdr_sekil_uret.py`, 7 Eylül 2026). Bir satır
birden çok yöntem taşıdığı için halka değil çubuk: oranlar 45 satıra göredir ve toplamı %100'ü aşar;
halka bu tabloyu yanlış anlatırdı.*

### 6.6.4 Açık kalem dağılımı (üçüncü grafik verisi)

Sayılar §6.5.1'in **on üç** satırından (3 Eylül: on iki, 4 / 3 / 3 / 2; 5 Eylül'de **A13** açıldı ama **satırı yazılmadı** — bu tablo onu sayarken §6.5.1 saymıyordu, iki yer aylarca çelişti, D-426 §4; 6 Eylül'de **A10** kapandı, D-431; **13 Eylül'de A13 satırı yazıldı ve A14 eklendi** → on üç); gruplama §6.5.1 sonundaki
sayımdadır. Oranlar bir ondalığa yuvarlanmıştır; dört dilimin yuvarlanmış toplamı **%100,1**'dir, fark yuvarlamadandır ve kapatılmamıştır.

| küme | kalem | oran | dağılım (1 blok = 1 kalem) |
|---|---:|---:|---|
| donanım / veri bekliyor (A1, A2, A3, A4) | 4 | %30,8 | ████ |
| ölçüm bekleyen risk (A5, A9, A13) | 3 | %23,1 | ███ |
| yazılım borcu (A6, A7, A8, A14) | 4 | %30,8 | ████ |
| denetim / final borcu (A11, A12) | 2 | %15,4 | ██ |
| **toplam** | **13** | **%100,0** *(yuvarlanmış dilimlerin toplamı %100,1)* | |

- ~~**BEYAN GEREKLİ (insan):** Bu üç tablonun PDF dizgisinde pasta/halka grafiğine çevrilmesi — yönergenin `Y-6-M06` hükmü **görsel** sunum ister; markdown kaynağında yalnız veri ve metin bar vardır.~~
  **7 Eylül 2026 — üçte ikisi kapandı, beyan gerekmiyor:** §6.6.2 halka grafiği (`sekiller/uygunluk_pasta.svg`) ve §6.6.3 çubuk grafiği (`sekiller/uygunluk_yontem.svg`) markdown'a gömüldü; `scripts/fdr_sekil_uret.py` tabloları okur, `tests/test_gece_sekiller.py` sayıları tabloya karşı sınar (11 test; 5/5 mutasyon yakalandı). **§6.6.4 için grafik üretilmedi:** on üç kalemlik dört küme metin barla okunur; ayrı bir halka bilgi eklemez. Görsel istenirse aynı betiğe üçüncü tablo eklenir.

### 6.6.5 Bu bölümün yönerge maddelerine karşılığı

| yönerge kimliği | ne isteniyor | bu bölümde nerede | durum |
|---|---|---|---|
| `Y-6-M01` | gereksinimlerin hangi ölçüde ve ne şekilde karşılandığı | §6.1 — dört matris, 45 satır | VAR |
| `Y-6-M02` | doğrulama yöntemi (analiz · hesaplama · test · simülasyon · gözle muayene) | §6.1 matrislerinin *doğrulama yöntemi* sütunu + §6.2 | VAR |
| `Y-6-M03` | her gereksinim için uygunluk durumu + tasarım kararlarıyla ilişkisi | §6.1 *durum* sütunu + §6.3 | VAR |
| `Y-6-M04` | gereksinimlerin tasarım kararlarına etkisi, mimari ve performansa katkısı | §6.4 — 14 satırlık karar tablosu + 3 maliyet örneği | VAR |
| `Y-6-M05` | karşılanamayan/kısmi gereksinimler, nedenleri, giderme planı | §6.5 — **A1–A14**; A13 satırı 13 Eylül'de **yazıldı** (5 Eylül'den beri §6.6.4'te sayılıyordu ama tablosu yoktu — yapısal kusur, düzeltildi), A14 (müdahale −100) aynı gün eklendi | VAR |
| `Y-6-M06` | genel uygunluk durumunun **görsel** sunumu | §6.6.2 halka grafiği (`sekiller/uygunluk_pasta.svg`) + §6.6.3 çubuk grafiği (`sekiller/uygunluk_yontem.svg`) + §6.6.4 veri tablosu; metin barlar korundu | VAR (7 Eylül 2026; grafikler tablodan üretilir, nöbetçi `tests/test_gece_sekiller.py`) |

### 6.6.6 Bu tablo okunurken bilinmesi gereken üç şey

⚠ **Bu tablo okunurken üç şey bilinmelidir:**

1. **Sayımda satırın *baskın* durumu alınmıştır.** Birçok satır iki yön taşır — §2.2.4'ün manuel paraşüt zinciri KANITLI_TEST, otonom tetiği ÖLÇÜLEMEDİ; §6.2 alan ihlalinin yazılım yarısı KANITLI_TEST, Pixhawk geofence'i ÖLÇÜLEMEDİ. İkinci yön her satırın kendi hücresinde yazılıdır ve bu sayım onu gizlemez.
2. **%71 "kanıtlı" demek "sahada çalıştı" demek değildir.** Bu oran, kapıların **koştuğu ve ayırt edici olduğu** oranıdır. Ölçümlerin ezici çoğunluğu **sentetik arena** ve **UDP loopback** üzerindedir; gerçek arena karesi (A4), gerçek telsiz (A2) ve gerçek uçuş (A3) yoktur.
3. **İNSAN-DONANIM satırları eksik iş değil, doğru sınıflandırmadır** — mühür, tartı, yük ve kırım hükümleri yazılıma düşmez. Ama içlerinden **biri** (R12, İKA sürücüsü) yazılımın da bekleyen işidir ve §6.5.1 A1'de açık olarak sayılmıştır.

### 6.6.7 Sayım düzeltmesi — önceki sürümle fark

Bu bölümün önceki sürümü özet sayımda **KOD_VAR_TEST_YOK 3 (%6,7)** ve
**İNSAN-DONANIM 8 (%17,8)** veriyordu. Satır satır yeniden sayımda (§6.6.1 dökümü)
bu iki hücre **4** ve **7** çıktı; toplam (45), KANITLI_TEST (32) ve
ÖLÇÜLEMEDİ (2) değişmedi. Hiçbir **durum hücresi** değiştirilmemiştir:
sayım hücrelere uyduruldu, hücreler sayıma değil.

Farkın hangi satırdan doğduğu, önceki sürümde satır dökümü yayımlanmadığı için
**kesinleştirilemez**. Bu sürümde döküm §6.6.1'de matris matris verilmiştir ve
sayılan satırlar burada tek tek yazılıdır:

- **KOD_VAR_TEST_YOK (4):** §2.1 (R1-ek) üç güzergâh adayı denetimi · §6.2 müdahale −100 · §6.2 tekrar fırlatma · §6.4 manuel moda alma (`mod` alanı).
- **İNSAN-DONANIM (7):** §2.2.1 mühür ve mancınıkla fırlatma · §2.2.5 (R12) İKA sürücüsü · §2.2.6 (R22) yük taşıma · §5.3.2 çoklu rotorlu araç · §6.4 kırım ve iniş ihlali · §6 ağırlık limitleri ve mühür · §7 kütleler.
- **ÖLÇÜLEMEDİ (2):** §2.2.2 (R2) tam otonom uçuş · §5.3.2 20×20 m alanın tek karede görülmesi.

⚠ ÖLÇÜLEMEDİ sütunundaki **2** sayısı, ölçülemeyen şeylerin sayısı DEĞİLDİR:
yalnız *birincil* etiketi ÖLÇÜLEMEDİ olan satırları sayar. §6.3.1'e göre altı
satır daha ikincil etiket olarak ÖLÇÜLEMEDİ taşır (R9 otonom tetik, R13-ek
fiziksel temas, saha `p`'si, uçuş süresi, Pixhawk geofence'i, gerçek SiK hattı).
Ölçülemeyen kalemlerin tam listesi §6.5.1'dedir (12 satır; A13 5 Eylül'de eklendi, A10 6 Eylül'de kapandı — D-431).

---

## Kanıt dizini

> **Yönerge dışı ek kanıt.** Yönerge Bölüm 6 böyle bir dizin istemez; bu depo
> her sayının kaynağını göstermeyi kendi kuralı saydığı için tutulur ve PDF
> dizgisinde bölüm sonu eki olarak kalır.

Bu bölümde geçen **her sayının** kaynağı: dosya yolu · üreten betik/komut · ölçüm tarihi.

| sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|
| Genel kapı: KOL 1 **15/15**, KOL 2 rota **15/15** · şerit **15/15**, RC=0 | konsol çıktısı (bu bölümün yazımı sırasında koşuldu) | `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py` | **2026-09-03** |
| ~~Tam süit **1896 test OK (skipped=3)**, 390,534 s~~ → **13 Eylül 2026: `Ran 2925 tests in 603.223s` (`:583`) · `FAILED (failures=20, skipped=12)` (`:585`)** — süit **KIRMIZIDIR** ve gevşetilmiyor. Düşen 20 testin **14'ü** belge ↔ kod aynasıdır: `test_atolye_test_gunu` — K1 bölümleri A1–A5 ve A12 (6), K2 yasak kelime (1), K5 `codes/karar_sozlesmesi.py` satır atıfları :2095/:2116/:2017/:2260/:2221/:2215/:2219 (7). **Kalan 6'sı belge aynası DEĞİLDİR ve üçü kapı niteliğindedir:** (a) `test_sim_mujoco_arena.AcikYolKoridoru.test_mutasyon_pay_sifir_olunca_duser` ve `Varyantlar.test_varsayilan_v1_ve_taban_kilit_sha_es` — arena üretecinin **mutasyon nöbetçisi ve kilit SHA'sı kırmızı** (üretilen `3ba496df…` ≠ kilit `d2c3127b…`), yani §3.3.3 ölçümlerinin koşulduğu arena ile bugünkü üretecin çıktısı **bayt-eş değildir**; (b) `test_sim_mujoco_arena.OnBesHarita.test_ika_ddr_olculeri` — model 0,46 m, ölçülen sabit **0,4595 m**: D-472 sabite işlendi, **MuJoCo modeline işlenmedi**; (c) `test_jetson_comms_paketi.test_paket_kopyalari_kanonik_kaynaklarla_birebir` + `test_t135_kamera_dogrula_icerik.test_paket_aynalari_ikiz` — Jetson'a giden `karar_sozlesmesi.py` kopyası kanonik kaynaktan **ayrışmış** (uçuşa giden kod ≠ repodaki kod); (d) `test_gece_akis_diyagramlari` (düğüm tablosu ↔ `.mmd`). Bunlar T256 kapsamındadır ve **14 Eylül teslimine AÇIK girer**. 5 Eylül'ün "2138 test / ortam kusuru" tablosu T209-T210 ile kapandı; süit artık YKS açıkken de koşuyor | `results/tam_suit_20260913/tam_suit.txt` (ham çıktı, 587 satır) | `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q` | **2026-09-13** |
| ~~**155** / **153**~~ → **209** test dosyası (`tests/*.py`), bunların **204**'ü `test_*.py` (3 Eylül: 155 / 153 · D-427 sonrası: 182 / 180) | `tests/` | `ls tests/*.py \| wc -l` · `ls tests/test_*.py \| wc -l` | **2026-09-13** |
| Defterde **414** `### D-` başlığı, **408** ayrık kayıt numarası | `REVIEW_LOG.md` | `grep -o "^### D-[0-9]*" REVIEW_LOG.md \| sort -u \| wc -l` | 2026-09-03 |
| Her test dosyasının test sayısı (11 / 12 / 19 / 22 / 27 …) | `tests/test_*.py` | `grep -c "    def test" tests/<dosya>.py` | 2026-09-03 |
| Kabul kapıları K0–K6: K1 255/260 · K2 5,88 · K3 0,39 · K4 1,57 · K5 0 · K6 2,75 (n=260) | `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json` → `results/fdr/GORUNTU_ISLEME_KANIT.md` §2 | `scripts/olcum/65_kabul_denetcisi.py`; belge üreteci `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-08-26 (belge 2026-09-01) |
| Üretim modeli künyesi: `navitas-seg-v36-512`, imgsz **512**, SHA `1d1caca6…6911` | `config/model_registry.json` · `profiles.competition` | `codes/model_registry.py` (fail-closed doğrulama) | terfi 2026-08-26 |
| v36 terfisi: ön kayıtlı **ROTA ≥ 10 → ölçülen 8**; **MASKE_YOK ≤ 10 → ölçülen 16**; geçilen FP ≤ 1 (1), yanlış güzergâh = 0 (0) | `config/model_registry.json` · `_surum_karari` | `scripts/olcum/65_kabul_denetcisi.py`; karar dayanağı D-293/D-294 | 2026-08-26 |
| v36 terfi bedeli: K3 0→1, K4 1→4, K6 5→7, val82 FP 0→2; kazanç: yanlış güzergâh 15/21→7/38, engel üstü wp 79→3 | `config/model_registry.json` · `_surum_karari` | aynı | 2026-08-26 |
| K7 yayınlanan şerit doğruluğu **84/85 (%98,8)** üretim kipinde | `REVIEW_LOG.md` D-386; kabul koşusu 65 | `scripts/olcum/65_kabul_denetcisi.py` (üretim kipi, 3. koşum) | 2026-09-01 |
| HB bağlama: hedef **253/256** doğru pedde · ped örtülüyken **259/260 HEDEF_YOK** · `p` KİP A/B eşit **0,9846** | `results/t150/baglama_olcumu_20260901.json` · ön kayıt `results/t150/ON_KAYIT_BAGLAMA.md` | T150 bağlama ölçümü (D-386) | 2026-09-01 |
| Uçtan uca kare gecikmesi **p95 0,113 s** (33 ölçülen gerçek kare (+3 ısınma), üretim zinciri + gerçek `KararYayinci` + UDP loopback ACK); ilk okuma p95 0,458 s idi ve 308 ms'i **soket sabiti** çıktı | `results/fda_butce/olcum_20260901.json` · ön kayıt `results/fda_butce/ON_KAYIT.md` | `scripts/olcum/169_fda_butce_olcumu.py`; düzeltme D-383 | 2026-09-01 |
| Gereken FPS türetimi: `1/(5·p)`; sentetik `p = 0,9846` → 0,203 · gerçek sızıntısız `p = 0,3457` → 0,579 · en kötü uçuş 0,61 | `results/b4_fps/p_ve_kosu_20260901.json` · ön kayıt `results/b4_fps/ON_KAYIT.md` (+EK-1, EK-2) | `scripts/olcum/163_b4_p_ve_kosu.py`; sızıntı düzeltmesi D-376 | 2026-09-01 |
| **51 saniyelik** kör aralık (0038, t=18–85 s, ~32,5 m sabit, 46 karesi `MASKE_YOK`); ikinci blok 45 kare | `results/b4_fps/p_ve_kosu_20260901.json` | `scripts/olcum/163_b4_p_ve_kosu.py` (D-374 §2) | 2026-09-01 |
| Çözünürlük denemesi reddi: sentetik `p` **0,9846 → 0,7808**, FPS maliyeti 1,302 | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1 | `scripts/olcum/167_fdr_kanit_paketi.py` (D-377) | 2026-09-01 |
| FP16 karar denkliği: zarar yönü **0**, karar uyuşması **0,9968** (eşik 0,98) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.2 | `scripts/olcum/167_fdr_kanit_paketi.py` (D-375) | 2026-09-01 |
| Histerezis ölçümü: ham çevrilme **13→7** (tohum 7) ve **24→11** (tohum 42); bastırılan NO_ROUTE **0**; `H1_ozgun = false` | `results/p5_histerezis/olcum_20260903.json` · ön kayıt `results/p5_histerezis/ON_KAYIT.md` | P5 histerezis ölçümü (D-396) | **2026-09-03** |
| Kuru koşu: **GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor)** · `cikis_kodu: 1` · `saha_surucu_importlari: []` | `results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json` | `scripts/saha_kuru_kosu.py` | **2026-09-02 23:59:54** |
| Genel kapı mutasyonu: üretim kolu **15/15 → 6/15**, tanısal kol yeşil kalır | `results/t156/rapor.md` | `tests/test_t156_genel_kapi_uretim_kolu.py` (mutasyon muhafızı) | 2026-08-26 |
| IKA_GO ACK kapısı: **5 mutasyonun 5'i yakalandı** | `results/k4_k8_ika_go_ack/rapor.md` | `tests/test_ika_go_ackli_tekrar.py` | 2026-08-26 |
| K1 telsiz halkası: `open_route_alindi=True`, `heartbeat=1`, `ack=['ika']` | `results/K1_telsiz_halkasi/rapor.md`; kuru koşu `ozet.json` `aktarim.detay.uretim_yolu_telsiz` | `tests/test_rpi_telsiz_yayin.py` + `scripts/saha_kuru_kosu.py` | 2026-08-26 / 2026-09-02 |
| `--fda` kipi: **9 test**, **4/4 mutant** (M1–M4) yakalandı; regresyon süiti 1882 test OK (D-408 sonrası; bugünkü süit 1896) | `REVIEW_LOG.md` D-408 §3 | `tests/test_faz_b_yks_fda_kipi.py` | 2026-09-03 |
| Süre sabitleri: İHA **900 s**, İKA **600 s**, hazırlık **900 s**, FDA operasyonu **600 s**, İHA-UB kenarı **300 m**, asgari irtifa **30 m** | ~~`codes/karar_sozlesmesi.py:339, :1974–1998, :1989, :1991`~~ ~~`:339, :1979-1982, :2008, :2010, :2017`~~ → **13 Eylül ÖLÇÜMÜ**: `codes/karar_sozlesmesi.py:339` (asgari irtifa) · `:1979` (İHA 900 s) · `:1980` (İKA 600 s) · `:2009` (FDA 600 s) · `:2011` (hazırlık 900 s) · `:2018` (İHA-UB 300 m). Önceki üç satır da yanlıştı: `:2008`, `:2010` **ve** `:2017` **üçü de yorum satırıdır**, hiçbiri sabit tanımlamaz (`:2017` = `# ceviremezdi. Tek tanim burasidir.`; "boş" değildir). Sayıyı üreten komut gerçekten bu satırları basar (D-423 kuralı) | `grep -n "SARTNAME_" codes/karar_sozlesmesi.py` | **2026-09-13** |
| Görev planı kötü-durum süre bütçesi **221,5 s ≤ 600 s**; görev irtifası **32 m**; loiter **60 s** | `config/pixhawk/README.md` · `config/pixhawk/fda_gorev.waypoints` | `tests/test_faz_b_pixhawk_sablon.py` (12 test) | 2026-09-03 |
| ArduCopter parametre şablonu **31 parametre**, 4'ü **TEYİT** işaretli | `config/pixhawk/arducopter_fda.param` | Copter-4.5 kaynak dosyalarından doğrulandı (D-406) | 2026-09-03 |
| ~~Jetson Nano yığını: **14/14 paket** aarch64/cp38 wheel, 51 dosya, 246 MB~~ → **GEÇERSİZ VARSAYIM, KULLANILMADI.** Tekerlekler JetPack 4.6 / **Python 3.8 (cp38)** için indirilmişti; kartın **ölçülen** künyesi (`results/jetson_20260906/ORTAM_KUNYESI.txt`) **NVIDIA Jetson Orin Nano Developer Kit** · **L4T R39 (release), REVISION 2.1** · **Ubuntu 24.04.4 LTS** · **Python 3.12.3** · `nvidia-jetpack 7.2.1-b49` (D-431) → cp38 tekerlekleri bu kartta **kurulamaz**, kurulmadı. Kurulum çevrimiçi yapıldı: `torch 2.11.0`, `tensorrt 10.16.2.10`, `onnxruntime-gpu 1.29.0`, `ultralytics 8.4.142`. ⚠ **Bellek boyutu bu künyede YOKTUR** — Orin Nano Dev Kit 4 GB ve 8 GB olarak satılır, dosyada bellek/RAM satırı yok; raporun "4 GB"ı bir **BEYAN**dır, tek satırlık ölçümle (`free -h` / `tegrastats`) 21 Eylül öncesi kapatılmalıdır | ~~`wheels/INDIRME_RAPORU.txt`~~ → `results/jetson_20260906/ORTAM_KUNYESI.txt` | ~~`scripts/nano_tekerlek_indir.py`~~ → kartta `python3 -V` · `pip freeze` · `dpkg -l nvidia-jetpack` | 2026-09-03 (geçersiz) → **2026-09-06** (kart künyesi) |
| Donanım künyesi (quadcopter, Pixhawk 6C, ~~Jetson Nano 4GB~~ **Jetson Orin Nano Developer Kit** *(bellek boyutu künyede YOK — "4 GB" BEYAN'dır, `free -h`/`tegrastats` ile ölçülecek)*, RPi HQ, ~~4S 10 Ah~~ **3S 6000 mAh**) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | kullanıcı beyanı, 3 Eylül; ~~**5 Eylül'de kutu açılarak teyit edilecek**~~ → 5–6 Eylül'de kutu açıldı: Jetson **Orin Nano Developer Kit 4 GB** (beyan yanlışlandı, D-431), ESC **Skywalker 60 A V2 ×4** (Pixhawk AUX1–AUX4), güç modülü **PM06** (D-426). **Pil kararı 12 Eylül'de değişti: 4S 10 Ah → 3S 6000 mAh** (kullanıcı kararı, gerekçe **stabilite**; 4S varsayımı GEÇERSİZ). Kart tarafı bu kararla tutarlı: `BATT_LOW_VOLT,10` (`config/pixhawk/emir.param:138`) · `BATT_CRT_VOLT,9` (`:131`) 3S eşikleridir. ⚠ Aynı dökümde `BATT_CAPACITY,3300` (`:129`) **HATALI**; 13 Eylül'de karta **6000** ve `BATT_CRT_VOLT` **10,5 V** yazıldığı **BEYAN** edildi (kullanıcı) — **yeni döküm alınmadığı için dosyayla doğrulanmadı** (T258, §6.5.1 A13) | 2026-09-03 (beyan) → 2026-09-06 (Jetson ölçümü) → **2026-09-12** (pil kararı + kart dökümü) → **2026-09-13** (kapasite/eşik yazımı, BEYAN) |
| Jetson kartı **Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Python 3.12.3) — 'Nano 4GB' beyanı yanlışlandı; `torch.cuda.is_available()` True; `jetson_fps.py` pt **1,35/1,06** · engine **1,58/1,33** FPS (eşik 0,61, GEÇTİ); engine↔pt D-303 oransal **3/126 DÜŞTÜ** → uçuş `.pt`; kartta genel kapı 15/15 · 15/15 | `results/jetson_20260906/ORTAM_KUNYESI.txt` · `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` · `results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json`, `genel_kapi.log` | kartta koşum (D-431) | **2026-09-06** |
| Sözleşme numaraları (§6.5 K1, §6.6 K4/K8, §6.7 FDA kipi, §7.1 süre, §7.2 sürücü, §7.3 temas, §7.4 çoğullayıcı, §7.5 SiK hub, §8 çözünürlük, §11.2 halka tablosu, §12 gerçek-kare kapısı) | `CONTRACTS.md` | — | güncel |
| Şartname alıntıları ve madde numaraları (§2.1, §2.2.1–2.2.6, §5.3.1 Tablo 4, §5.3.2, §6, §6.1–6.4, §7) | `results/sartname_bosluk/sartname_metin.txt` (1314 satır; PDF 30 sayfa, PyMuPDF ile çıkarıldı) | `fitz` (PyMuPDF) metin çıkarımı | 2026-08-26 |
| Yükümlülük haritası R1–R22 (**bu bölümün başlangıç noktası; üç satırı bayat, §6.3.4'te düzeltildi**) | `results/sartname_bosluk/rapor.md` | şartname boşluk denetimi | 2026-08-26 / 27 |
| Tam süit **2138 test** — 5 Eylül üç koşum: ~14:5x **1 FAIL** · ~19:1x **OK** · ~19:5x **1 FAIL**; düşen tek test `test_p8_sim_katmani.test_comms_loopback_gecer`, sebep ortam (`comms/test_comms.py:35-36` 5005/5006'ya bind, `WinError 10013`); süre ve `skipped` sayısı için `results/` altında çıktı dosyası **yok** | `REVIEW_LOG.md` D-427 satır 29893–29895 | `O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q` (YKS kapalıyken) | **2026-09-05** |
| Genel kapı **15/15 · 15/15** (D-422 §6 regresyonu, 4 Eylül); 5 Eylül'e ait ayrı artefakt yok | `REVIEW_LOG.md:29567` · önceki: `results/faz_b_oncesi/cuma_kontrol/genel_kapi.txt` (3 Eylül, HEAD baeca14) | `O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py` | 2026-09-04 |
| ~~**182** / **180**~~ → **209** test dosyası (`tests/*.py`), bunların **204**'ü `test_*.py` (3 Eylül: 155 / 153 · 5 Eylül: 182 / 180) | `tests/` | `ls tests/*.py \| wc -l` · `ls tests/test_*.py \| wc -l` | **2026-09-13** |
| Defterde **432** `### D-` başlığı, **426** ayrık kayıt numarası (3 Eylül: 414 / 408); son kayıt D-427 | `REVIEW_LOG.md` | `grep -c "^### D-" REVIEW_LOG.md` · `grep -o "^### D-[0-9]*" REVIEW_LOG.md \| sort -u \| wc -l` | D-427 sonrası |
| Bu hafta eklenen kapıların test sayıları: `test_yks_hakem_kanit_yolu` **6** · `test_yks_hakem_kanit_olaylari` **22** · `test_iha_komut_saat_ve_tekrar` **42** · `test_runbook_komutlari_kosuyor` **3** · `test_wheels_sayisi_belgelerle_tutarli` **4** · `test_pixhawk_firmware_yolu` **10** · `test_yarisma_adi_kapisi` **3** · `test_fdr_sarkan_atif_kapisi` **7** · `test_yks_harita_yerlesimi` **3** · `test_yks_monotonik_kronometre` **3**; değişenler: `test_faz_b_iha_komut_alici` 22 → **23**, `test_yks_gui_komut_durustlugu` 6 → **13** | `tests/test_*.py` · D-412, D-419, D-421, D-422, D-423, D-424, D-425, D-417, D-420; commit `1b94dca` | `grep -c "    def test" tests/<dosya>.py` · `git show b4df3f1:tests/test_yks_gui_komut_durustlugu.py \| grep -c "    def test"` | D-427 sonrası |
| Firmware sabitlemesi: `SURUM = "stable-4.5.7"`, `BOARD_ID = 56`; indirilen `arducopter.apj` **1.585.371 B**, git **2a3dc4b7**; `firmware-version.txt` = `4.5.7-FIRMWARE_VERSION_TYPE_OFFICIAL`; 4.7.1'de 31 parametrenin **9'u yok** | `scripts/pixhawk_firmware_indir.py:54, :74` · `firmware/` (saha belleği; ikili dosya repoya girmez) · `REVIEW_LOG.md` D-425 §1, §4 (satır 29787) | `scripts/pixhawk_firmware_indir.py`; kapı `tests/test_pixhawk_firmware_yolu.py` (10) | **2026-09-05** |
| 5 Eylül Pixhawk kabulü — ÖLÇÜM (Mission Planner Messages): `ArduCopter V4.7.1 (dbe79216)` + "Missing 9 params" (14:52) · `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` (15:08) · `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` (15:38) · `RCInput: decoding IBUS(1)` (18:03) · pil ve emniyet PreArm'ları kayboldu (18:03/18:05) · `starting motor test` → `finished motor test` (18:06). BEYAN: motor sıra/yön 4/4, SiK bağlandı, uçuş modları SwC | `REVIEW_LOG.md` D-426 §1 satır 29819–29829 | takım üyesinin yapıştırdığı MP satırları (sözlü bildirim BEYAN olarak ayrıldı) | **2026-09-05** |
| Künye farkı (BEYAN): ESC **"60 A V2" ×4** (plan 80 A) · güç modülü **PM06** (plan PM02) · FS-iA6B **teyit**; tam marka/model BEYAN GEREKLİ | `REVIEW_LOG.md` D-426 §3 satır 29852–29854 · plan `SAHA_HAZIRLIK_PLANI_20260903.md:39, :41` | kutu açılışı, gözle | 2026-09-05 (beyan) |
| 5 Eylül'de **yapılmayan / ölçülemeyen**: RC failsafe testi (sonuç gelmedi) · ESC kalibrasyonu · pusula kalibrasyonu (Jetson takılı değil) · parametre dökümü (**dosya YOK**; 6 Eylül'de alındı: `arducopter_fda_20260906.param`, D-428 §5g) · pil gerilimi MP↔multimetre · tartı · kamera FOV · SiK RTT · Nano FPS (6 Eylül'de Orin Nano'da ÖLÇÜLDÜ, D-431) | `REVIEW_LOG.md` D-426 §4 satır 29863–29869; `ls config/pixhawk/` | — | 2026-09-05 |
| Kuru koşu **2026-09-04 09:52:22**: GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor) · `cikis_kodu: 1` · `saha_surucu_importlari: []` — 2 Eylül ile aynı | `results/saha_kuru_kosu_20260904_095222/ozet.json` | `scripts/saha_kuru_kosu.py` | **2026-09-04** |
| Hakem kanıt kaydı olay kümesi: **16 olay** (`KANIT_OLAYLARI`), kenar + `KANIT_TEKRAR_ARALIGI_S = 30.0`; gerçek oturum `hakem_log.jsonl` (5 Eylül, YKS `--fda`, 14:29 → 19:07): **1115 satır, 5 olay adı** — KAMERA_KANIT 554 · TELEMETRI_KANIT 554 · UI_OLAYI 5 · OTURUM_BASLADI 1 · YKS_ARAYUZ_HAZIR 1 (İHA bağlı değil: ROTA_*/HAKEM_ONAYI_* yok) | `comms/yks_gui.py:127–151` · `CONTRACTS.md §6.8` (satır 444) · `results/prova/20260905_142958_15092/hakem_log.jsonl` | `comms/hakem_kaydi.py`; kapılar `tests/test_yks_hakem_kanit_olaylari.py` (22), `tests/test_yks_hakem_kanit_yolu.py` (6) | 2026-09-05 |
| Süre ve mesafe sabitlerinin güncel satırları: `SARTNAME_ASGARI_IRTIFA_M :339` · `SARTNAME_IHA_GOREV_SURESI_S :1979` · `SARTNAME_IKA_GOREV_SURESI_S :1980` · ~~`SARTNAME_FDA_OPERASYON_SURESI_S :1994` · `SARTNAME_HAZIRLIK_SURESI_S :1996` · `SARTNAME_IHA_UB_KENAR_M :2003`~~ → **13 Eylül ÖLÇÜMÜ:** `SARTNAME_FDA_OPERASYON_SURESI_S :2009` · `SARTNAME_HAZIRLIK_SURESI_S :2011` · `SARTNAME_IHA_UB_KENAR_M :2018` (3 Eylül: :339, :1974–1998, :1989, :1991; 10 Eylül okumaları :1994/:1996/:2003 ve :2008/:2010/:2017 **ikisi de bayattı ve birbiriyle çelişiyordu**) | `codes/karar_sozlesmesi.py` | `grep -n "SARTNAME_" codes/karar_sozlesmesi.py` | **2026-09-13** |

### BEYAN GEREKLİ (insan)

Aşağıdaki satırlar **ölçülmemiştir** ve bu raporda sayı olarak geçmemektedir.
Rapor teslim edilmeden önce insan tarafından ölçülüp doldurulmalıdır:

- ~~**BEYAN GEREKLİ (insan):** Gerçek SiK çiftinde tur süresi (RTT p50/p95) ve paket kayıp oranı~~ → **ÖLÇÜLDÜ 13 Eylül 2026 (D-476) ve DÜŞTÜ:** `results/atolye_20260912/A6_sik_ikago.json` · `A6_sik_parasut.json` — seri COM7 @57600, n=200×2, kayıp **%0**, RTT p95 **265,2 / 229,6 ms** (eşikler 250 / 200 ms) → `"cikis_kodu": 1`. Eşik gevşetilmedi; düzeltme T263 → T264 → T265. **Açık kalan: menzil** (eğik ≥ 425,5 m koşusu yapılmadı) — DDR'deki ">%98 teslim, 300 m" iddiasının bugün **kanıtı yoktur**.
- ~~**BEYAN GEREKLİ (insan):** Jetson Nano 4GB üzerinde `torch.cuda.is_available()` sonucu ve `scripts/jetson_fps.py` p50/p95 kare hızı (PT ve ONNX kolları) — Jetson 5 Eylül'de takılmadı (D-426 §4); tarih BEYAN GEREKLİ.~~ → **ÖLÇÜLDÜ 6 Eylül (D-431):** kart Jetson Orin Nano Developer Kit 4 GB; `torch.cuda.is_available()` **True**; PT **1,35/1,06** · engine **1,58/1,33** FPS (≥ 0,61); ONNX kolu **HATA** (`cudaErrorNoKernelImageForDevice`) — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`.
- **HESAP (ölçüm 21 Eylül 2026):** RPi HQ yatay FOV = **55,3°**, düşey **42,9°** — IMX477 etkin alan **6,287 × 4,712 mm** (üretici veri sayfası) ÷ **6 mm** lens: `2·atan(6,287/12)` ve `2·atan(4,712/12)`. 30 m'de kare **31,4 × 23,6 m** → 20×20 m alanı iki eksende de kapsar. Rapordaki eski **55–63°** aralığı lens beyanından türetilmiş **TAHMİN**di, bırakıldı. Kamera elde olmadığı için 14 Eylül teslimine **ölçüm yetişmiyor**; `codes/kamera_dogrula.py` + `scripts/kamera_fov_hesapla.py` 21 Eylül uçuşunda koşulur ve çıkan sayı hesabın yerine geçer — **hesap, sonucu değiştirmek için kullanılmaz**.
- **BEYAN GEREKLİ (insan):** Montaj sonrası gerçek kütleler (İHA, İKA, yük) — §7 `m_İHA`/`m_İKA`/`m_yük` parametreleri.
- **BEYAN GEREKLİ (insan):** İKA gerçek motor sürücüsü seçimi (seri / PWM / GPIO / MAVLink) ve `scripts/ika_surucu_kabul.py` K1–K6 sonuçları.
- ~~**BEYAN GEREKLİ (insan):** Pixhawk geofence (`FENCE_*`) ve failsafe parametrelerinin gerçek donanımda doğrulanmış hâli~~ → **KISMEN KAPANDI — parametreler ÖLÇÜLDÜ, davranış ÖLÇÜLMEDİ (12 Eylül 23:55 dökümü, `config/pixhawk/emir.param`):** `FS_GCS_ENABLE,5` (*Enabled always Land* — kapalı değil, `:408`) · `FS_GCS_TIMEOUT,5` (`:409`) · `FS_THR_ENABLE,3` (LAND, `:411`) · `FS_THR_VALUE,975` (`:412`) · `BATT_FS_LOW_ACT,1` (`:134`) · `BATT_FS_CRT_ACT,1` (`:133`) · `FENCE_ENABLE,1` (`:361`) / `FENCE_ACTION,1` (`:358`) / `FENCE_ALT_MAX,50` (`:359`) · `ARMING_CHECK,1` (`:28`) · `RC6_OPTION,153` (`:735`) · `FLTMODE6,9` (LAND, `:392`) · `LOG_BITMASK,176126` (`:536`) · `FRAME_CLASS,1`/`FRAME_TYPE,1` = QUAD/X (`:395`, `:396`). ⚠ **İzah edilmemiş değişim:** 6 Eylül dökümünde bu parametre `FS_GCS_ENABLE,1` idi (`config/pixhawk/mevcut.param:408`), 12 Eylül atölyesinde **geçici olarak 0** yapıldı (D-473, 🔴 uçuş engelleyici risk kaydı) ve 23:55 dökümünde **5** çıktı. 1 → 0 → 5 zincirindeki son adımı kimin, ne zaman, hangi gerekçeyle yazdığı **kayıtlı değildir**; değer emniyetli tarafta olsa da provenansı yoktur ve uçuş öncesi teyit edilmelidir. ⚠ Parametreyi okumak davranışı **tetiklemek değildir**: GCS kaybı failsafe'i sahada kodla hiç uçurulamadı (A2 atölye adımı KISMİ, D-473). Tarihçe: 5 Eylül'de döküm alınmadı (D-426 §4); 6 Eylül 20:22 dökümü `config/pixhawk/arducopter_fda_20260906.param` repoda (D-428 §5g) — `FENCE_*`/`FS_*` kart değerleri oradan okunur, RC failsafe 6 Eylül'de ÖLÇÜLDÜ ve **DÜŞTÜ** (D-428 §2), ESC ve pusula kalibrasyonu 6 Eylül'de yapıldı (D-428 §1, §3 — beyan); üçüncü döküm 12 Eylül 23:55'te alındı (`config/pixhawk/emir.param`). ⚠ **Açık kalan:** parametreler okundu ama **tetiklenmiş davranış** (fence ihlali, GCS kaybı) sahada hiç ölçülmedi; RC failsafe 6 Eylül'de DÜŞTÜ (D-428 §2), 12 Eylül atölyesinde GEÇTİ (BEYAN, ham dosya yok). Ayrıca 13 Eylül'de yapılan `BATT_CAPACITY`/`BATT_CRT_VOLT` yazımı için **dördüncü döküm alınmadı** (T258). Planlanan ölçüm: **21 Eylül 2026 uçuşu öncesi** (§6.5.1 A13).
- ~~**BEYAN GEREKLİ (insan):** ESC ve güç modülünün tam marka/modeli~~ → **KAPANDI (12 Eylül):** ESC **Skywalker 60 A V2 ×4**, Pixhawk **AUX1–AUX4** çıkışlarına bağlı (plan 80 A idi); güç modülü **PM06** (plan PM02 idi). FDR Bölüm 3/5/7 künyesi buna göre düzeltilir.
- **AÇIK — DOĞRULANACAK (ölçüm, 21 Eylül uçuşu öncesi):** PM06'nın akım/gerilim **kalibrasyonu**. Karttaki `BATT_AMP_PERVLT,36.36` (`config/pixhawk/emir.param:126`) ve `BATT_VOLT_MULT,18.18` (`:143`) **PM06 fabrika değerleridir**, bu kartta doğrulanmamıştır; akım kanalının doğrulanması (atölye A13) **pens ampermetre olmadığı için yapılamadı** (D-473). `BATT_CAPACITY,3300` (`:129`) 12 Eylül dökümünde yeni pille (**3S 6000 mAh**) çelişiyordu; 13 Eylül'de **6000** ve `BATT_CRT_VOLT` **10,5 V** yazıldığı BEYAN edildi, **döküm alınmadı** (T258). Kapanışı: pil gerilimi MP↔multimetre karşılaştırması + pens ampermetreyle akım + yeni döküm (§6.5.1 A13).
- ~~RC failsafe testinde `Radio Failsafe` satırı ve CH3 değeri~~ → **KAPANDI — ÖLÇÜM (12 Eylül):** `config/pixhawk/emir.param` → `FS_THR_VALUE,975` (`:412`, CH3 eşiği) · `FS_THR_ENABLE,3` (`:411`, eylem **LAND**). RC failsafe testi 12 Eylül atölyesinde **GEÇTİ** (BEYAN — MP ekran görüntüsü/ham dosya yok; 6 Eylül'de aynı test DÜŞMÜŞTÜ, D-428 §2).
- **AÇIK — BEYAN GEREKLİ (insan), kayıt 21 Eylül 2026:** Motor sırası/yön testinin **videosu**. 4/4 doğru hâlâ yalnız **BEYAN**'dır (D-426 §1); 12 Eylül hover uçuşu dolaylı destektir ama sıra/yön kanıtı **değildir**.
- **BEYAN GEREKLİ (insan):** İlk hover, Loiter/Auto ve tam prova uçuş logları (`VIBE`, EKF, pusula ofseti, IHA_LANDED damgası) — 6 Eylül ve sonrası.
- **DOĞRULANACAK:** `--fda` kipinin bağımsız denetimi (A11); aynı el hem sözleşmeyi hem uygulamayı yazdı.
