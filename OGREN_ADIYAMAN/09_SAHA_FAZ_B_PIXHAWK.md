# 09 · SAHA, FAZ B VE PIXHAWK — kutu açılınca ne oldu (2–7 Eylül 2026)

> Kaynaklar: `SAHA_HAZIRLIK_PLANI_20260903.md` · `SAHA_RUNBOOK.md` · `FAZ_B_GUN_PLANI.md` · `SAHA_OLAY_SONRASI_MUAYENE.md` · `config/pixhawk/` (README, `arducopter_fda.param`,
> `fda_gorev.waypoints`, `arducopter_fda_20260906.param`) · `scripts/pixhawk_firmware_indir.py`, `saha_kuru_kosu.py`, `surum_dondur.py` · `REVIEW_LOG.md` D-403–D-407, D-410,
> D-412–D-414, D-421–D-436 · `results/ucus_loglari/20260906/` · `DEVAM.md` · `ozet/G_ika_sim_saha_pixhawk.md`, `ozet/E_review_log_tarihce.md`.
> Ön bilgi: **ArduPilot/ArduCopter** = Pixhawk üstünde koşan açık kaynak uçuş yazılımı; **parametre** = ArduCopter'ın davranışını belirleyen `AD,DEGER` çiftleri;
> **Mission Planner** = PC'deki yer istasyonu programı; **failsafe** = bir şey koptuğunda otomatik tepki (RTL = eve dön, Land = yerinde in).

---

## Seviye 1 — Bir cümle ve büyük resim

**Faz B** (2–7 Eylül) yazılımın kutudan çıkan gerçek donanımla buluşmasıdır. Yazılım tarafı önce hazırlandı: Pixhawk parametre şablonu ve FDA görev
planı testle kilitlendi, MAVLink çoğullayıcı ve SiK hub yazıldı, Jetson tek komut açılışı, sürüm mührü, paraşüt/ARM komut zinciri, saha runbook'u.
Sonra kutu açıldı ve **varsayımlar teker teker yanlışlandı**: Pixhawk PX4 ile geldi (D-424), ArduCopter 4.7 şablonun 9 parametresini tanımadı → 4.5.7 (D-425),
künye üç yerde yanlıştı (D-426), RC failsafe ölçüldü ve **düştü** (D-428), pervaneli üç devrilme (D-429), Jetson Nano değil Orin Nano (D-431), kumandadan arm
`RC6_OPTION=0` yüzünden olmuyordu (D-433), motor künyesi değişmişti (D-435). **Uçuş yapılmadı** (üç kez istendi, reddedildi). Ortak ders: **beyan ≠ ölçüm**.

## Seviye 2 — Nasıl işliyor

### 2.1 FDA aracı künyesi (SAHA_HAZIRLIK_PLANI §0.2, kutu sonrası düzeltmelerle)
| kalem | plan (3 Eyl beyan) | kutudan çıkan / ölçülen |
|---|---|---|
| Gövde | 3B baskı quad (ABS/ABS-CF; kol 1–2 ve 3–4 **farklı reçete**, gerekçesiz — SGGS diskalifiye riski) | basıldı, monte |
| Uçuş kontrolcüsü | Pixhawk 6C + PM02 | 6C, **PX4 yüklü geldi** → ArduCopter **4.5.7** flash; güç modülü **PM06** (8 pin kablo uymadı, 6 pin) |
| GNSS | Holybro M9N | ölçüldü: u-blox ROM SPG 5.10, 18 uydu |
| RC | FlySky FS-i6 + FS-iA6B (iBUS) | ölçüldü `decoding IBUS(1)` (alıcı yanlışlıkla CH6'ya takılıydı, `i-BUS SERVO` portuna alındı) |
| ESC | "80 A DShot ×4" | **Hobbywing Skywalker 60A V2 ×4** (etiket beyanı), PWM AUX1–4, `RC_SPEED` 490 → 400 |
| Motor | 5008 340KV ×4 + 12×10 | **iade edildi** → SunnySky X2220-III 980KV V3 ×4 + 10×4,5 (**BEYAN**, etiket fotoğrafı yok, 2 yıllık eski motorlar; **M1 hasarlı**) |
| Pil | 1 × 4S 10 Ah 25C | dökümde `BATT_CAPACITY 3300` (uyumsuz, DOĞRULANAMADI) |
| Telemetri | 2 × SiK 433 MHz | "bağlandı" (beyan), RTT **ÖLÇÜLEMEDİ** |
| Görev bilgisayarı | Jetson Nano 4 GB | **Orin Nano DevKit 4 GB** (10) |
| Kamera | RPi HQ IMX477 CSI, 6 mm | CSI yolu ÖLÇÜLEMEDİ; FOV 55–63° **hesap** |
| Güç kesme | — | anahtar yok, XT60/XT90 fişi (DDR REQ-25–31 çift acil kesme final için açık) |
| Paraşüt | FDA aracında **yok** (çoklu rotor) | `CHUTE_ENABLED,0` |

### 2.2 Pixhawk parametre şablonu (`config/pixhawk/arducopter_fda.param`, README, `test_faz_b_pixhawk_sablon.py` 16 test)
Her parametrenin üstünde NEDEN yorumu zorunlu; `# TEYIT:` işaretliler README §3 listesiyle kilitli; değerler Copter-4.5 kaynak dosyalarından.
| grup | değer | neden |
|---|---|---|
| gövde | `FRAME_CLASS 1`, `FRAME_TYPE 1` | Quad X |
| motor | `MOT_PWM_TYPE 0`, `RC_SPEED 400` | Skywalker 50–432 Hz |
| çıkışlar | `SERVO9..12_FUNCTION = 36,34,33,35` (AUX1–4 = M4,M2,M1,M3); `SERVO1–8, 13–16 = 0` | 6 Eyl dökümünde başıboş motor fonksiyonları vardı (D-428 §5d) |
| MAVLink | `SYSID_THISMAV 1`; `SERIAL1/2_PROTOCOL 2`, `BAUD 57` | TELEM1 SiK, TELEM2 Jetson 57600 |
| akış | `SR1_POSITION 4`, `SR1_EXTRA3 1`, `SR2_POSITION 8`, `SR2_EXTRA3 2` | asgari 4 Hz konum, 1 Hz durum, ×2 pay |
| RC | `RC_PROTOCOLS 4` (yalnız iBUS) | sahada 1'e çevrildi, geri alınmadı |
| pil | `BATT_MONITOR 4`, `LOW 14,4 V → RTL (FS_LOW_ACT 2)`, `CRT 14,0 V → Land (1)` | 4S 3,60/3,50 V hücre |
| failsafe | `FS_THR_ENABLE 1` (RC kaybı → RTL), `FS_GCS_ENABLE 1` (YKS heartbeat kaybı → RTL) | |
| çit | `FENCE_ENABLE 1`, `TYPE 3`, `ALT_MAX 50`, `RADIUS 60`, `ACTION 1` | poligon Adıyaman'da |
| RTL / iniş / hız | `RTL_ALT 3500` (35 m: görev 30 m üstü, çit 50 altı), `LAND_SPEED 50`, `WPNAV_SPEED 300` | |
| arm / log | `ARMING_CHECK 1`, `LOG_BITMASK 176126` | .bin log FDR kanıtı |
Bilinen risk (README §5): `EXTENDED_SYS_STATE` hiçbir `SR*` akışında yok; `SET_MESSAGE_INTERVAL` ile istenir ve Pixhawk reboot'unda (pil değişimi) silinir →
her pil değişiminden sonra `jetson_baslat.sh --kapi`.

### 2.3 Neden ArduCopter 4.5.7, en yeni değil (D-425)
5 Eyl 14:52 Mission Planner 4.7.1 yükledi; şablon yüklenince "**Missing 9 params**". Copter-4.7 SI reformu: `SR*` → `MAV1/2_*`; `RTL_ALT` (cm) → `RTL_ALT_M`;
`LAND_SPEED` → `LAND_SPD_MS`; `WPNAV_SPEED 300 cm/s` → `WP_SPD` m/s (300 kalırsa **300 m/s**); `ARMING_CHECK` → `ARMING_SKIPCHK` **anlam ters**. Dosya, kapı ve TEYİT
listesi 4.5 anlambilimine ölçülü; tek atışlık uçuştan 16 gün önce ölçülmemiş port yapılmadı → 15:08 4.5.7 flash. İndirici `pixhawk_firmware_indir.py`
`stable-4.5.7`, board_id 56 kapısı. Kural: **beyan edilen bağımlılık zorlanır**.

### 2.4 FDA görev planı (`fda_gorev.waypoints`, QGC WPL 110, 8 satır)
HOME (yer tutucu 0,0) → `NAV_TAKEOFF` **32 m** (şartname ≥ 30 + 2 m baro payı) → 4 × `NAV_WAYPOINT` 20×20 m köşeler (±10 m) **tek pas** → `NAV_LOITER_TIME` **60 s**
(canlı aktarım + 2 aşamalı onay + ACK penceresi) → `NAV_LAND`. Kaba süre 3–3,5 dk; kötü-durum bütçesi **221,5 s ≤ 600 s** (test yarı bütçe 300 s arar).
Sahada değişecek tek şeyler: koordinatlar, çit poligonu, kalibrasyonlar, tarihli döküm. Şablon Null Island'da (0°,0°); Adıyaman'da kaptan girer.

### 2.5 Failsafe'ler — tasarım ve ölçüm
| failsafe | şablon | 6 Eyl dökümü | ölçüm |
|---|---|---|---|
| RC kaybı | `FS_THR_ENABLE 1` RTL | **3 Land** ("kimse bilmeden değişmiş") | 🔴 **DÜŞTÜ** (D-428 §2): TX kapatılınca barlar sabit kaldı, `Radio Failsafe` gelmedi — FS-iA6B iBUS'ta **son değerleri tutuyor**; çare kumandada `RX Setup → Failsafe` (CH5 → Land, gaz altta); ölçüt: TX kapanınca CH5 Land'e zıplar, HUD `Land`. **Test geçmeden pervane takılmaz** |
| Pil | LOW → RTL, CRT → Land | LOW → **Land** (`BATT_FS_LOW_ACT 1`) | gerilim ölçeği ±0,1 V doğrulandı (15,8 = 15,8) |
| GCS | RTL, 5 s | 1 (tlog'da 5?) — çelişki | Jetson'daki MAVProxy sysid 255 heartbeat bastığı için SiK kopsa da **tetiklenmez** → "Jetson-bağlantı failsafe'i" (D-406 C) |
| Çit | 50 m / 60 m | aynı | poligon yok |
Mimar kararı bekleyen: 30 m görev için RTL mi Land mi; `RC_PROTOCOLS 4`'ün iBUS çözmediği kanıtlanmadı (TX pili + fiş karıştı).

### 2.6 D-433: kumandadan arm neden olmuyordu
tlog (`2026-09-06 19-52-44.tlog`, `scripts/ucus_tlog_arm.py`): CH6 akşam boyunca **56 kez** çevrildi, hiç arm/disarm geçişi yok — sinyal ulaşıyor ama
**`RC6_OPTION = 0`** (işlev atanmamış; şablonda da yok: anahtarla arm hiç planlanmamıştı). Çare `RC6_OPTION = 153` (öneri, uygulanmadı). Dümenle arm
(`ARMING_RUDDER 2`) **çalışıyor**: gaz ≤ 1030 PWM ve yaw ≥ ~1947, 2 s; 21:36:25'te gaz 1003'e inince ARMED. 15 s boyunca gaz 1043–1107'de tutulduğu için
"olmuyor" sanıldı. Yan bulgu: CH5 üst = `FLTMODE6 9` **Land**; FDR "Stabilize/Loiter/RTL" beyanıyla **uyuşmuyor**.

### 2.7 D-429/D-434: pervaneli üç devrilme (6 Eyl 20:45–21:34)
D-428 oturumu kapandıktan sonra **başka bir oturum**, birbirinden habersiz (→ "tek aktif saha oturumu" kuralı). tlog 41 arm penceresi, 26 gerçek arm.
P19 20:56: gaz 1002→1656 0,8 s'de, pitch −0,7 → **−43,8°** · P20 21:00: 32 s, **M1 1949'da doygun ~25 s**, M2 1150 tabanda, duman · P26 21:33: gaz 1079 → **2000**
0,5 s'de, pitch −36,9°. Hüküm: FC doğru yönde düzeltti (ön motorlara yüksek komut), mixer ters değil; **fiziksel ön itki komut edileni üretmedi**;
gaz "adımla" verildi (hover ~%35 varsayılan, %65–100'e 0,2–0,6 s'de). D-434: pilot kolu merkezde (1500/1502), seviye kalibrasyonu temiz (trim −1,5°) →
kalan aileler: (a) komut başına itki asimetrisi (ESC uç noktası, zayıf/eski ön motor-ESC), (b) CG önde / kol 1–2 vs 3–4 reçete asimetrisi / ön ayak takılması.
Kurallar: kalkış ≥ 2 s rampa, `MOT_SLEW_UP_TIME` 0 → 1,0 s; motor yönü videosuz "doğru" sayılmaz; olay = önce log (.bin indir; `LOG_DISARMED 0` — arm'sız
koşular loglanmaz); `SAHA_OLAY_SONRASI_MUAYENE.md` madde 0–12 geçmeden güç verilmez.

### 2.8 D-435/D-436: motor künyesi
5008 340KV iade; X2220-III 980KV (BEYAN) + 1045 + 4S: veri sayfası maks. sürekli **38 A / 30 s**, 4S+1047 tam gaz 2130 g @ **38,4 A** (sınırın üstünde), 1045 satırı
hiçbir sayfada yok; montaj 16×19 mm (kollar Ø25 için tasarlandı — nasıl monte edildiği doğrulanmadı). **İtki bütçesi kapısı** (hover ≤ %50 ∧ I_hover ≤ I_sürekli)
**ÖLÇÜLEMEDİ**: kütle tartılmadı, akım ölçülmedi; "bütçe kapanmadan güç verme yok". "SunnySky V3115 900KV" önerisi: böyle motor **yok**; V3115 KV900 **T-Motor
VELOX** (4S tam gaz 2820 g / 47 A, sınır 51 A/60 s → sınırın altında; 2 pal 1045 verisi yok; montaj Ø19 → kollar yeniden). Marka teyidi olmadan sipariş yok.
Depoda 12 dosya hâlâ 5008 der → **T211 (İNSAN: etiket fotoğrafı, veri sayfası, tartı)**.

### 2.9 Saha yordamı (`SAHA_RUNBOOK.md`)
**§0 PC'de her seferinde:** genel kapı 15/15 · tam süit OK · kuru koşu (yalnız `motor` sahipsiz) · paket aynası senkron · model pakette · H3 video.
**§1 Açılış (≤ 900 s, her 30 s +1 puan), istasyon başına tek komut:** YKS `saha_baslat.py yks --fda --ika IKA:5006 --iha JETSON:5007 --kamera-url http://JETSON:8080`;
İKA `saha_baslat.py ika --yks YKS:5005`; Jetson `jetson_baslat.sh`. **§3 Jetson:** çoğullayıcı önce; `iha_komut_alici --izinli-kaynak YKS:5005` zorunlu; 🔴 `YKS_IP`
`/etc/navitas.env`'de elle beyan — dizüstünün gerçek IP'si farklıysa **tüm komutlar Jetson'da sessizce reddedilir** (teşhis `journalctl -u navitas-komut | grep "kaynagi RED"`);
DHCP rezervasyonu/statik IP. **§4 tekrar fırlatma:** `--reset` yordamı; İKA süreci öldürülmez; kronometre yeni fırlatmada; fiziksel müdahale −100.
**§6 21 Eylül kesin-hazır kapısı (10 madde):** üç MAVLink tüketicisi · GNSS canlılığı · ölçek/irtifa · ARM (ACK + heartbeat) · DISARM iki teyit · kamera ≥ 10 dk
canlı · kopma/yakalama · ağ ayrımı · E-stop/paraşüt ACK ve red yolları · kayıt tek klasörde. "Bir madde düşerse uçuşa çıkılmaz."

### 2.10 Sürüm dondurma mührü (`scripts/surum_dondur.py`, D-404/405)
Şartname §6.1: yarışan yazılım beyanla birebir aynı olmalı → sha256 künyesi `config/DONDURMA_KUNYESI.json`: paket aynası + kaynak, paket modelleri, saha yapılandırması
(`jetson_baslat.sh`, systemd, `arducopter_fda.param`, `fda_gorev.waypoints`, kalibrasyon), `yks_ika` 9 dosya, registry sha, `git_head`, `git_kirli`. Kirli ağaçta RED;
özet içerik-kanonik (CRLF/LF eş; v1'de 18/19 sahte ihlal, D-405 S6); `--dogrula` git'e bağlı; engine kayıtsızsa "mühür erken". Sıra: engine derle + `--turev-kaydet` →
PC'ye taşı, commit → `--dondur` → künye commit. Planlanan dondurma **17 Eylül**; bugün `DONDURULMADI` (exit 3).

## Seviye 3 — 2–7 Eylül kronolojisi ve açık kalemler

| tarih | ne oldu | kayıt |
|---|---|---|
| 2 Eyl | Faz B araçları: `iha_komut_alici`, `mavlink_dogrula`, `sik_rf_olc`, `ika_surucu_kabul`; SiK hub; `jetson_baslat.sh` + 6 systemd; sürüm mührü; `--fda` kipi; kamera köprüsü; çoğullayıcı **zorunlu** (iki süreç Pixhawk'ı ayrı açıyordu); paraşüt zinciri iki KRİTİK kusurla doğdu ve kapatıldı (komut alıcıya hiç ulaşmıyordu) | D-403–D-408 |
| 3 Eyl | FDR yönergeye taşındı (isim yasağı bulundu, D-417); **D-410** 21 Eylül uçuş günü değil FDR teslim; D-412 mimarın belge commit'i `_kanit_yaz` tanımını süpürdü (YKS her kurulumda ölüyordu); D-413 Nano'da microSD yok; D-414 YKS PC kurulumu; Codex 2200 satır, 21 kritik bulgu (D-418) | |
| 4 Eyl | "Cumartesiye hazır mıyız" çürütme turu: 13 tıkayıcı (runbook kopyala-yapıştır bloğu ölüydü) (D-421); saat kilidi (D-422); kapı yanlış sayıyla (D-423); tam süit 2104 OK; saha kapıları yeşil | |
| **5 Eyl** (sahada tek üye, mimar uzaktan) | 14:52 4.7.1 → 15:08 **4.5.7** · GPS · RC bind · 18:03 iBUS (CH6 → i-BUS SERVO) · PM06 → POWER1 · 18:06 motor testi (%10–15'te döndü) · 4/4 yön **beyan, video yok** · SiK bağlandı (beyan) · "uçalım" **reddedildi** · döküm **alınmadı** | D-424, D-425, D-426 |
| **6 Eyl** 17:05–19:30 | Jetson: Orin Nano çıktı, kurulum, kapılar, engine, FPS, denklik (10) | D-431 |
| **6 Eyl** 18:30–20:50 | Pixhawk 7 kalem ölçümle kapandı (sürüm, pil ölçeği, accel/level, ESC kal. 3. denemede, pusula ×2, GPS 18 uydu); **RC failsafe DÜŞTÜ**; TX pili bitti; bilinçsiz değişen `FS_THR_ENABLE` 1→3, `BATT_FS_LOW_ACT` 2→1; döküm 20:22 (`arducopter_fda_20260906.param`); uçuş 3 kez istendi, reddedildi | D-428 |
| **6 Eyl** 20:45–21:34 | habersiz ikinci oturum: pervaneli **üç devrilme**, M1 hasarlı, gaz adımla | D-429 |
| 7 Eyl | D-431 master'a; push kapısı betiğe (D-430); süit süreç sızıntısı kökü (D-432); D-433 RC6_OPTION; D-434 pilot/seviye temiz; **D-435 motor künyesi değişmiş**, T211 açıldı; D-436 V3115 | |

**Sonraki plan (SAHA_HAZIRLIK_PLANI §3–§4, DEVAM.md §5):** muayene 0–12 → yeni piller, failsafe testi, `RC IN` sabitleme, 3 kırmızı BEC teli, `SERVO1–8/13–16 = 0` + motor
testi listesi, `RC_PROTOCOLS` tek değişkenli test, sabah dökümü → **3.1 ilk hover** (Stabilize/AltHold 2–3 m, 2 dk; VIBE < 30, EKF yeşil; pervaneler ilk kez) → 3.2 Loiter + kısa
Auto 30 m + çit + iniş kanıtı canlı → 3.3 algı canlı → 3.4 tam prova ×3 (≤ 10 dk) → 3.5 sıkı prova (hands-off) → **17 Eyl mühür** → 18 KESİN HAZIR → 20 yolculuk → **21 Eyl
Adıyaman provası + FDR teslim** → **30 Eyl–3 Eki resmî uçuş**. Tek pil → günde ≤ 2 uçuş; gerekli ≥ 7 uçuş / ≥ 4 gün, plan 6 gün. 7 Eylül sonrası ilerleme depoda **yok**.

**Açık kalemler (yazılımcıya sorulabilecekler):** T211 motor künyesi/itki bütçesi (insan) · RC failsafe düzeltme ve tekrar testi · `RC6_OPTION` · FLTMODE6 beyanı ·
mimar kararı RTL/Land · `BATT_CAPACITY` 3300 vs 10 Ah · SiK RTT/menzil (`sik_rf_olc.py`) · gerçek Pixhawk'ta `mavlink_dogrula` 3/3 ve `jetson_baslat.sh --kapi` ·
kamera CSI + ayna testi · İKA sürücü (final) · mühür · ArduPlane parametre seti (final sabit kanat).

---

## Jüriye 30 saniyede

> "Kutu açılınca beyanlarımızın çoğu yanlışlandı ve hepsini kayda geçirdik: Pixhawk PX4 ile geldi, en yeni ArduCopter şablonumuzun dokuz
> parametresini tanımadığı için ölçülü olduğumuz 4.5.7'de kaldık; RC failsafe'i test ettik ve düştü, alıcı son değerleri tutuyor, bu
> düzelmeden pervane takmıyoruz; pervaneli üç devrilmeyi uçuş logundan analiz ettik, uçuş kontrolcüsü doğru tepki vermiş, ön itki yetmemiş,
> bir motor hasarlı. Uçmadık, çünkü kapılar geçmedi. Uçuş kontrolcüsü parametrelerimizin her satırının gerekçesi yazılı ve testle kilitli."

## Kendini sına

1. Faz B nedir, hangi tarihler?
2. Neden 4.5.7? 4.7'de neler değişti, ne riski var?
3. FDA görev planının adımları ve süreleri; kötü-durum bütçesi?
4. RC failsafe testi nasıl düştü; çare ne; kural ne?
5. `FS_GCS_ENABLE` neden SiK kopunca tetiklenmez?
6. Devrilmelerde hüküm ne; kalan iki aile?
7. Kumandadan arm neden olmuyordu; dümenle arm koşulları?
8. Motor künyesinde ne değişti, hangi kapı ölçülemedi?
9. `YKS_IP` yanlışsa sahada ne olur, nasıl anlaşılır?
10. Mühür ne mühürler, ne zaman basılır?

<details><summary>Cevaplar</summary>

1. Yazılımın gerçek donanımla buluşması; 2–7 Eylül (hazırlık 2–4, kutu 5–6, analiz 7). 2. 4.7 SI reformu 9 parametrenin adını/birimini/anlamını değiştirdi (`WPNAV_SPEED` 300 → 300 m/s, `ARMING_CHECK` tersi); şablon/kapı/TEYİT 4.5'e ölçülü; tek atışlık uçuştan 16 gün önce ölçülmemiş port yapılmadı. 3. TAKEOFF 32 m → 4 köşe 20×20 tek pas → LOITER 60 s → LAND; ~3–3,5 dk; 221,5 s ≤ 600. 4. TX kapatılınca barlar sabit kaldı, failsafe gelmedi (iBUS son değeri tutuyor); kumandada failsafe kanalı ayarı (CH5 → Land, gaz altta); test geçmeden pervane yok. 5. Jetson'daki MAVProxy sysid 255 heartbeat basıyor; bu yüzden anlamı "Jetson-bağlantı failsafe'i". 6. FC doğru yönde düzeltti, ön itki yetmedi, gaz adımla verildi, M1 hasarlı; kalan: itki asimetrisi (ESC/eski motor) ve CG/kol geometrisi. 7. `RC6_OPTION 0` (işlev atanmamış); gaz ≤ 1030 PWM + yaw sağda 2 s. 8. 5008 iade → X2220 980KV (beyan) + 1045; itki bütçesi kapısı (hover ≤ %50, akım ≤ 38 A) tartı ve akım ölçülmediği için ÖLÇÜLEMEDİ. 9. `iha_komut_alici` tüm komutları kaynak pinine uymadığı için reddeder, YKS'de uyarı çıkmaz; `journalctl -u navitas-komut | grep "kaynagi RED"`. 10. Paket aynası + kaynak, modeller, saha yapılandırması (Pixhawk dosyaları dâhil), YKS/İKA 9 dosya, registry sha, git HEAD; engine kaydından sonra, planlanan 17 Eylül.
</details>

## Kaynaklar
`config/pixhawk/README.md`, `arducopter_fda.param`, `arducopter_fda_20260906.param`, `fda_gorev.waypoints` · `SAHA_RUNBOOK.md` · `SAHA_HAZIRLIK_PLANI_20260903.md` · `FAZ_B_GUN_PLANI.md` ·
`SAHA_OLAY_SONRASI_MUAYENE.md` · `DEVAM.md` · `results/ucus_loglari/20260906/` · `scripts/ucus_tlog_*.py` · `REVIEW_LOG.md` D-403–D-436 · `ozet/G_ika_sim_saha_pixhawk.md`.
