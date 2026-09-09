# NAVITAS — REVIEW_LOG.md'den Gelişim Tarihçesi ve Dersler

**Kaynak:** `/home/n4vitas/proje/navitas_tam/navitas/REVIEW_LOG.md` (30.393 satır, 441 `### D-` başlığı, D-01 → D-436).
**Hedef okuyucu:** projeyi jüriye anlatacak yazılımcı takım üyesi.
**Kural:** Bu belgede her iddia bir D-numarasına dayanır; başlıklar defterden aynen aktarılmıştır (defterin kendi yazımıyla — bir kısmı ASCII, bir kısmı Türkçe karakterli). Uydurma sayı yoktur; verilmeyen bir tarih, defterde de yoktur.

---

## 0. Defterin kapsamı — dürüstlük notu

Defter **3 Ağustos 2026**'da açılır (`## Kayıt 2026-08-03 · Codex Faz-2 teslimatlarının çekişmeli denetimi`). İlk `D-` numaralı kayıtlar 4 Ağustos'a aittir; son kayıtlar (D-433–D-436) 7 Eylül 2026 tarihlidir. Yani **Mayıs–Temmuz dönemi bu defterde yoktur**; o döneme yalnız dolaylı izler düşer:

- Projenin ilk commit'i `17258f8 start project` — D-349, kamerayı aynalayan satırın kökenini `git log -S` ile bu commit'e kadar sürer.
- `config/model_registry.json` "15 Temmuz'dan kalma `models/navitas_seg_v4_best.pt`" gösteriyordu (D-116); yani Temmuz ortasında üretimde v4 vardı.
- Gerçek drone kareleri "WhatsApp drone videolarından" 30 Temmuz 2026'da çekilmiş bir otopark sahnesidir (D-12, D-53; `whatsapp_video_2026_07_30_...`).
- 3 Ağustos girişi "Codex Faz-2 teslimatları"nı denetler; yani Ağustos'tan önce en az iki fazlık bir iş (Faz-1/Faz-2, T1–T13 görevleri) yapılmıştı.

Bu belge dolayısıyla **Ağustos başı → Eylül başı** aralığını ayrıntılı, öncesini yalnız bu izler kadar anlatır.

---

## 1. Dönemler hâlinde tarihçe

### 1.0 Mayıs–Temmuz (defter öncesi; yalnız dolaylı izler)
- Sentetik arena üreteci, RescueNet tabanlı 2 sınıflı segmentasyon (traversable/blocked) modelleri v2…v17, Gazebo simülasyonu, YKS/İKA/İHA UDP protokolü kuruldu (D-12, D-18, D-22, D-23 bunları "mevcut" olarak bulur).
- 30 Temmuz: otoparkta ilk gerçek drone çekimi (D-53).
- Model v4 üretim defterine 15 Temmuz'da girmiş (D-116).

### 1.1 Ağustos başı (3–10 Ağustos): "hiçbir şey ölçülmemiş" keşfi
Defterin ilk haftası, sistemin **çalıştığı sanılan ama hiç kanıtlanmamış** halkalarını sıralar:
- **D-02 (4 Ağu)** İKA_GO tek UDP paketi, ACK'siz; **D-03 (4 Ağu)** İHA_LANDED kilidini açan taraf yok — "kapı eklendiğinde onu AÇACAK tarafın da var olduğu kanıtlanmalı" dersi TEST_SPECS'e işlendi.
- **D-12 (5 Ağu)** üretim modeli v17 gerçek drone karelerinde tamamen kör (11/12 kare boş); **D-18** sebep: sentetik arena eğitimi gerçek dokuyu unutturdu; **D-20** v21 gerçek doku eklenince 67/67 kare kullanılabilir.
- **D-15 (5 Ağu)** Anayasa madde 4 kapısı hiç çalışmamış: `grep -E` içinde `\|` düz karakterdi, komut hep 0 dönüyordu — "sahte geçiş".
- **D-17 (5 Ağu)** D-03 kapanmadı, şekil değiştirdi: İHA_LANDED yalnız simülasyonda üretiliyor.
- **D-22 (7 Ağu)** 13 ajanlı tam depo taraması: saha kod yolu DÖRT yerden kopuk (paket haberleşme kodu taşımıyor, HB koordinatı yalnız Gazebo meta.txt'ten, İHA_LANDED sahada yok, İKA aktüasyonu Gazebo'ya çakılı) ve 58 testin hiçbiri bunu görmüyor.
- **D-23, D-24, D-25, D-26 (7 Ağu)** üretim modeli hedefi (kırmızı H) göremiyor; `MORPH_CLOSE` oyulmuş engeli geri kapatıyor (madde 15 ihlali); `rota_bul` letterbox dolgusunu bilmiyor (her pad'li kare KAPALI_DAR); v21'in "gerçek kare kapısı" kendi eğitim verisinde koşuluyor, val %100 sızıntılı.
- **D-28 (8 Ağu)** kullanıcı sahada buldu: waypoint'ler arasındaki kenar engelin üstünden geçiyor (119 px ihlal).
- **D-33 (9 Ağu)** zaten commit edilmiş bir görev çalışma ağacı geride olduğu için 6 saat boyunca baştan yapıldı — "görevin yapılıp yapılmadığının otoritesi kuyruk değil depodur".
- **D-36 (10 Ağu)** ilk Jetson FPS sayısı (14 FPS) vekil donanımda ve kanıtsız.

### 1.2 Ağustos ortası-1 (11–16 Ağustos): ölçüm zemini krizi, T66, v27→v30
- **D-49 → D-51 → D-53 (11 Ağu)** D-25'in kökü aranırken mimar iki kez yanıldı; Codex-2 görevi zorlamayıp itiraz yazdı (D-50, D-52) ve haklı çıktı: kusurlu yol `rota_bul`. Asıl bulgu: **ölçüm zemini `data/raw_frames` HTAB arenası değil, bir OTOPARK**.
- **D-56 (11 Ağu)** arena çekimi iptal; kompozit zemin (gerçek otopark + yapıştırılmış moloz/hedef) kararı; "kapanmayan sınır: gerçek arena başarımı doğrulanamaz" açıkça yazıldı.
- **D-59, D-61, D-63 (11 Ağu)** karar zinciri kusursuz yer-gerçeği maskesiyle bile 7/7 reddediyor; kullanıcı GUI'de "çatıyı yol sanıyor" dedi, doğrulandı — v21 pratikte "araç mı değil mi" ayırıcısı; 11 model üç kapıyla sıralandı, kazanan yok ve Kapı 2'nin kendisi kusurlu.
- **D-67** kök neden: 2 sınıflı dönüşüm çatı/ağaç/su sınıflarını etiketsiz arka plana düşürüyor; modele "çatı zemin değildir" hiç denmiyor.
- **D-84 (~13 Ağu)** "gerçek arena karesi bulundu" (şartname s.9 figürü): v21 orada tek piksel zemin bulamıyor. **D-92 (14 Ağu)** rota bariyer kolunun içinden geçiyor. **D-95 (14 Ağu)** v25 üretime girmiyor.
- **D-99 (14 Ağu)** BÜYÜK DÜZELTME: figür şartnamenin kendi altyazısıyla "tamamen yapay zekâ ile oluşturulmuştur" — kullanıcı sordu, mimar okumamıştı. D-84/87/88/92/95 zincirinin geçerlilik alanı daraltıldı, hiçbiri silinmedi.
- **D-103/D-104 (14 Ağu)** üreteç geometrisi dikey şeritten moloz adalarına geçti (T66); `RETR_EXTERNAL` delik atma kusuru yakalandı; düşen kapı "geçersiz bir kıyas"tı (v24 ile ölçtürmek mimarın hatası); **v27 T66 üzerinde koşacak**.
- **D-107 (14 Ağu)** İLK ÖN KAYIT: v27 kabul ölçütleri K0–K5 sonuç görülmeden yazıldı ("sabah tartışılmayacak").
- **D-109, D-113 (14 Ağu)** `--devam` hiç çalışmıyor ve `results.csv` siliyor; `best.pt` ulaşılamaz bir `best_fitness` tavanına kilitlenmiş (epoch 43'te donmuş) — v27 `last.pt` ile kabul edildi (**D-115**), üretime alındı (**D-116**), ONNX altı kapıyı geçti ama koridor seçimi binde-4 gürültüye kararsız (**D-119, 15 Ağu**).
- **D-123 → D-130** v28 (512) ön kayıtlı kuralı sağladı; **D-129 → D-131 (15 Ağu)** v29 (gerçek veri 12 kat) gerçek karede 0/67→64/67 ama arenada K5 düştü: ezberleme, RED; **D-132 → D-133/D-134** v30 (4 kat) dört şartı sağladı, mimar "öneri v30" cümlesini aynı gün tutarsız bulup geri aldı; **D-136 (15 Ağu)** kullanıcı kararıyla üretim v27→v30, beş uç mutasyonla doğrulandı.
- **D-140 (16 Ağu)** `seed` eğitimi hiç etkilemiyor: v31, v30'un bit-bit aynısı (ultralytics sabit tohum).

### 1.3 Ağustos ortası-2 (17–22 Ağustos): kararsızlık, K5, çatı, v34→v35
- **D-150 (17 Ağu)** K5 sıkı kapıda iki model de düşüyor; v30'un `K5 = 0/173`'ü şanslı bir çekilişmiş. **D-151–D-157** koridor darlığı planlayıcıdan değil `yol_duzelt` string-pulling'inden (**D-154**); beş varyant ön kayıt gereği reddedildi; **D-164 (18 Ağu)** `rota_bul` açıklık koruması üretime alındı (kararlılık ekseninde sıfır fark).
- **D-180 (19 Ağu)** kabul denetçisinin K5'i HER modeli reddediyor: `None` "düştü" sayılıyor. **D-197 (20 Ağu)** K5 üç durumlu oldu: GEÇTİ / DÜŞTÜ / ÖLÇÜLEMEDİ — ÖLÇÜLEMEDİ terfiyi yine bloklar.
- **D-182 (19 Ağu)** üretim v30→v34 (kullanıcı kararı); terfi yarım kalınca 8 test düştü — "sistem tasarlandığı gibi çalıştı".
- **D-201, D-210 (20 Ağu)** v34 otopark kaplaması v21 ile eşdeğer ("düşüş" payda farkıymış); model çatıyı öğrenmiş (recall %96,6) ama gerçek karede görmüyor çünkü o karelerin kendi etiketi "zemin" diyor (448/448 dosya tam kare zemin).
- **D-225, D-233, D-237/D-238/D-239/D-240 (20 Ağu)** yamalı etiketle çatı döndü (0,011→0,989); copy_paste val kümesi %100 kirli (55/55); kazanan (a)+(c) çatı kaçağını %96→%2'ye indirdi, dürüst bedeli %39,7 zemin kaybı; sıralama iki kez düzeltildi.
- **D-243 (20 Ağu)** K5 zemini popülasyona taşındı; en kritik şart: **bariyer modelden gelmeyecek**.
- **D-255 (21 Ağu)** İLK KEZ bir model tam kabul zincirini geçti (t127_temiz); **D-256/D-257 (21 Ağu)** üretim v34→v35, altı hizalama noktası tek commit'te, mimar tek tek doğruladı.
- **D-270, D-272 (21 Ağu)** ilk DJI çekimi gece yapılmış (569/569 kare referansın altında); ama sistem gece karesinde `YOL=2 · güven=1,000` yayınladı — ön kayıttaki ağır hüküm ateşledi.

### 1.4 Ağustos sonu (25–31 Ağustos): gerçek saha verisi, K6–K8, v36, saha yolu kusurları
- **D-279, D-281 (25 Ağu)** etiketleme kapasitesi 5,1 kare/saat (19,9 değil); üç çürütücü: betimleme doğru, iki nedensel iddia yanlış.
- **D-284 (26 Ağu)** 10 kapatma adayının 8'i çürütüldü — "triyaj tek başına güvenilmez"; kalıp: "Yap satırı sınandı, ASIL İDDİA sınanmadı".
- **D-289 (27 Ağu)** uzlaşı referansı + "rota yol üstünde" kapısıyla hiçbir aday geçmedi, üretim v35 de geçmiyor (6 rotasının 5'i yol üstünde değil). **D-290** K6 kabul zincirine girdi.
- **D-294 (26 Ağu)** üretim v35→v36 (gece_v7a) — **kullanıcı kararı, ön kayıtlı eşikler GEÇİLMEDİ**, istisna CONTRACTS §12'ye yazıldı; gerekçe: 111 gerçek karede yanlış güzergâh %71→%18.
- **D-295/D-296 (27 Ağu)** yayınlanan şerit numarası 9/15 yanlıştı: `road` rotanın en dar TEK pikselinden okunuyordu; tek tanım (`rota_serit_karari`) ile 15/15.
- **D-303 (27 Ağu)** v36 `.pt`↔`.onnx` karar denkliği 259/260; oransal eşik (≤ 5/260) daha sonra Jetson engine'e de uygulandı.
- **D-309 → D-313 → D-314/D-316 (27 Ağu)** yayınlanan şerit 43/50; 5 yanlışın 4'ü etiket kusuru; iyi koşullu 88 karede 84 doğru (eşik tam 84 — "sınırda geçti"); **K7 kapısı** zincire girdi.
- **D-317–D-323 (27 Ağu)** hakem ekranı bayat tespiti canlı gösteriyordu; 10 dk FDA limiti sistemde yoktu; "asgari 30 m irtifa" şartı hiç uygulanmıyordu ve uyum raporu uygulandığını iddia ediyordu (**D-319**); düzeltirken mimar heartbeat'i susturan kusur üretti, süit 20 dk kilitlenince yakalandı (**D-320**).
- **D-324, D-328–D-333 (28 Ağu)** "duba" bariyer koludur, model `degrees=0` ile eğitilmiş; v8 RED; v37'ye geçiş denendi ve geri alındı (zincir geçti, gerçek kare reddetti) → **K8 gerçek kare kapısı** eklendi.
- **D-339 → D-341 → D-342 (28 Ağu)** sentetik arena arenaya benzemiyor; "çıplak toprak bankada yok" iddiası mimarın kendi ölçümüyle çürüdü (kestiği yamayı 640 px'e büyütmüştü).
- **D-349 (28 Ağu)** 🔴🔴 saha kamera yolu her kareyi aynalıyor (`cv2.flip(frame, 1)`, ilk commit'ten kalma): açık yol 1↔3 takas, 16 karenin 15'i; §2.1 → 0 puan. Hiçbir kapı `run_camera` döngüsünden geçmiyordu.
- **D-352–D-360 (28 Ağu)** Jetson kurulum bloğu kılavuzun komutlarını beslemiyordu; amiral komut `data/` öneki eksik; `jetson_fps.py` kayıt defterini sormuyordu; kendi hatalar dizisi (git add -A ile 1589 dosya, yanlış e-posta, kapı kırmızıyken push, koşum dizini üst üste).
- **D-366–D-368 (29 Ağu)** T199 arena profili adayı reddedildi (OOD'yi mutlaklaştırdı); şartname PDF'ten yeniden okundu: görev "rota üretmek" değil "üç yoldan açık olanı tespit etmek", §6.4 hakem teyidi uçuşu geçersiz kılabilir.
- **D-370, D-371 (31 Ağu)** mutasyon betiği CRLF'e takılıyordu (mutasyon uygulanmadan "ölçüldü"); **sahada FP16 kararı**, INT8 yolu kapandı — ama "FP16 gereken hızı veriyor" kanıtı henüz yok.

### 1.5 Eylül (1–7 Eylül): haberleşme gerçek bayt akışında, Faz B, saha günleri
- **D-374–D-377 (1 Eyl)** FPS sorusu kapandı (gerekli 0,41 ≪ band 0,9); FP16 denkliğinin ilk ölçümü VAKUMDU (`half` sessizce uygulanmadı); R katmanının %62'si eğitim kümesi çıktı; INFER_SIZE 640 reddedildi (sızıntı faydayı 4 kat şişirmiş).
- **D-383 (1 Eyl)** çürütücü hasadı: telsiz 308 ms bir soket sabitiymiş (p50 307,6→2,3 ms).
- **D-387/D-388 (2 Eyl)** MAVLink katmanı ve SiK seri taşıyıcı İLK KEZ gerçek çerçeve/bayt akışında koştu (`KOD_VAR != KOSUYOR` sınıfının kapanışı).
- **D-403–D-407 (3 Eyl)** paraşüt komut zinciri iki KRİTİK kusurla doğdu ve kapatıldı (komut alıcıya hiç ulaşmıyordu); SiK hub, systemd açılış, sürüm mührü; çürütücü turu 1 KRİTİK + 14 ÖNEMLİ (mühür CRLF'ye bağlı, hub RecursionError).
- **D-406, D-413** Jetson "Nano 4GB / JetPack 4.6" varsayımıyla 14 aarch64 cp38 wheel paketi; microSD yuvası yok çıktı.
- **D-410** 21 Eylül FDR TESLİM günü, uçuş günü değil (kusur yayılmıştı; diskalifiye riski). **D-412** mimarın kendi commit'i yarım işi süpürdü: YKS her gerçek kurulumda `AttributeError` ile ölüyordu. **D-417** resmî FDR yönergesi okundu: rapor yanlış iskelette, isim yasağı bilinmiyordu. **D-418** Codex ana ağaca 2200 satır yazdı, 21 kritik bulgu.
- **D-421 (4 Eyl)** "cumartesiye hazır mıyız" çürütme turu: 13 tıkayıcı, runbook'un kopyala-yapıştır bloğu ölüydü. **D-422** saat kilidi: sapma 30 dk'yı aşınca kritik komutlar kalıcı ölüyordu. **D-423** kapı yanlış sayıyla (48 vs 51) yazıldı.
- **D-424/D-425 (5 Eyl, sahada canlı)** Pixhawk 6C PX4 ile gelir, ArduCopter flash yordamı hiçbir belgede yoktu; 4.7.1'de 31 parametrenin 9'u yok → 4.5.7'ye dönüldü. **D-426** 5 Eylül tutanağı: motor testi 4/4, künye üç yerde yanlış.
- **D-427, D-430, D-432 (5–7 Eyl)** `test_comms` üretim portlarına bind ediyor; mimar süit kırmızıyken push etti; gerçek kök: süit yer tutucu IP'li `yks_gui/ika_nav` süreçlerini sızdırıyor — iki teşhis de eksikti.
- **D-428 (6 Eyl akşam)** 7 kalem ölçümle kapandı, RC failsafe ölçüldü ve DÜŞTÜ, uçuş yok (üç kez istendi, reddedildi). **D-429 (6 Eyl 20:45–21:34)** pervaneli üç devrilme tlog ile ölçüldü: FC doğru yönde düzeltti, ön itki yetmedi, M1 hasarlı, gaz "adımla" verildi.
- **D-431 (6 Eyl)** Jetson kartı "Nano 4GB / JetPack 4.6" değil **Orin Nano 4GB / JetPack 7.2.1** çıktı; kurulum kartta yapıldı, engine derlendi, `.pt` FPS 1,35/1,06 p50/p95 (eşik 0,61) GEÇTİ; engine karar denkliği 3/126 ile D-303 eşiğini aştı → uçuş `.pt` ile.
- **D-433–D-436 (7 Eyl)** kumandadan arm olmuyor çünkü `RC6_OPTION=0`; devrilmelerde pilot kolu merkezdeydi; motor künyesi değişmiş (5008 340KV iade, "2207 980KV" beyan); "SunnySky V3115" diye ürün yok, T-Motor VELOX V3115 veri sayfası ölçüldü.

---

## 2. En önemli 40 kayıt

Biçim: **D-no · tarih · başlık (aynen)** → ne bulundu / ne karar verildi / ders / kanıt yolu.

**1. D-03 · 2026-08-04 · `KRITIK · Uretim zincirinde IHA_LANDED ureticisi yok`**
Şartname §2.2.5 kilidi doğru kurulmuş ama açan taraf yok; `P_gorev = 0`. Ders TEST_SPECS 4.6'ya işlendi: kilit eklenirken onu açacak tarafın varlığı kanıtlanır. Kanıt: `simulation/scripts/navitas_sim.py:218`. D-17'de kusurun şekil değiştirdiği (yalnız simülasyonda üretiliyor) görüldü; D-22 Kopukluk 3 aynı şeyi doğruladı.

**2. D-12 · 2026-08-05 · `KRITIK · v17 gercek drone karelerinde tamamen kor`**
Üç domain × 12 kare: v17 drone karelerinde 11/12 boş; `conf` 0,02'ye kadar sıfır tespit — eşik değil domain boşluğu. Karar: "gerçek nadir karede zemin çıkarabiliyor mu" ayrı kapı olmalı (D-18). Ders: arena IoU tek başına model seçemez. Kanıt: `data/raw_frames/` (67 kare), scratchpad `neden_bos.py`.

**3. D-15 · 2026-08-05 · `KRITIK · Anayasa madde 4 kapisi hicbir zaman calismadi (sahte gecis)`**
`grep -rnE "...(import\|from)..."` içinde `\|` düz karakterdi, komut her zaman 0 dönüyordu; pozitif kontrol (numpy/cv2) de 0 verdi. Ders: bir kapı "temiz" demeden önce pozitif kontrolle yakalayabildiği gösterilir. Kanıt: tablo D-15 içinde; doğru kapı `git ls-files "*.py" | xargs grep -nE ...`.

**4. D-18 · 2026-08-05 · `KRITIK · Sentetik arena egitimi modeli gercek dunyada korlestirdi`**
Beş model × 67 gerçek kare: sentetik arenayla eğitilen v17/v20 10/67, arena görmemiş v5c 58/67. Arena IoU 0,031→0,861 yükselirken gerçek dokuda katastrofik unutma. Karar: gerçek doku eğitime eklendi → D-20 v21 67/67. Kanıt: `scratchpad/v5c_gozle.jpg`, D-20 `codes/runs/segment/v21_gercek_doku`.

**5. D-22 · 2026-08-07 · `TIKAYICI · Saha kod yolu DORT ayri yerden kopuk ve hicbir test bunu gormuyor`**
58 testin tamamı simülasyon yolunu ölçüyor; saha paketi haberleşme kodu ve pyserial taşımıyor; HB koordinatı yalnız Gazebo `meta.txt`'ten; İHA_LANDED sahada yok; İKA aktüasyonu `gz topic`'e çakılı. Ders: ölçülen yol ile sahada koşan yol aynı olmalı — bu ders D-349'da bir kez daha, çok pahalı biçimde öğrenildi. Kanıt: `ls jetson_paket/kod/`, `simulation/scripts/iha_haritala.py:507`, `ika_nav.py:90-100`.

**6. D-24 · 2026-08-07 · `KRITIK · analyze_path MORPH_CLOSE oyulmus engeli geri kapatiyor — madde 15 ihlali`**
Kapama extensive: 3 px engelin %99'u geri kapatılıyor; hakemin gördüğü koridor tespit edilmiş molozun üstünden geçebilir. `costmap_path_finder.serbest_alan()` hattı temiz; sorun iki hattın bir arada yaşaması. Ders: monotonluk (serbest alan yalnız küçülebilir) kapıya bağlanmalı → D-170/D-172 üç eksende korundu. Kanıt: `codes/rpi_inference.py:139`, `codes/test_monotonluk.py`.

**7. D-25 · 2026-08-07 · `TIKAYICI · rota_bul() letterbox dolgusunu bilmiyor: pad'lenmis her kare KAPALI_DAR`**
Tohum bandı tam tuval yüksekliğinden hesaplanıyor, dolgu içine düşüyor; kırpılınca ACIK. Model kıyası (K-8) bu kusurlu sayıya dayanmıştı. Genel kapı 15/15 kare sahne kullandığı için yakalamıyordu. Kanıt: `codes/costmap_path_finder.py:232-242`; kök D-51'de netleşti.

**8. D-26 · 2026-08-07 · `TIKAYICI · v21'in "gercek kare kapisi" kendi egitim verisinde kosuluyor + val %100 sizintili`**
`bolum_sec` anahtarına kopya indeksi giriyor: train 56 / val 41 / kesişim 41. `best.pt` sızıntılı val ile seçildi. Ders: bölüm anahtarı kaynak kare düzeyinde olmalı; D-233 aynı satırı 13 gün sonra tekrar buldu ve kapattı, D-347 train/val sızıntısı yok diye ölçtü. Kanıt: `scripts/copy_paste_augmentation.py:327-331`, `dataset/copy_paste_gercek/manifest.json`.

**9. D-33 · 2026-08-09 · `KRITIK · ZATEN COMMIT EDILMIS bir gorev, calisma agaci geride oldugu icin bastan yapildi`**
S9 dün commit edilmiş (`40859b3`), kuyruk `[ ]` gösteriyordu, çalışma ağacı commit'ten geriydi; N4 ~6 saat boşa çalıştı, ürettiği kod kayboldu. Ders: görevin yapılıp yapılmadığının otoritesi depodur, kuyruk değil. Kanıt: `git show 40859b3:comms/yks_gui.py` sayımları.

**10. D-51 · 2026-08-11 · `DÜZELTME · D-48 ve D-49 yanlıştı: kusurlu yol iha_perceive değil rota_bul`**
Mimar ölçümde üretim yolunu "yeniden kurmuş", gerçek fonksiyonu çağırmamıştı; Codex-2 görevi zorlamayıp itiraz yazdı (D-50). Gerçek fonksiyonla: `iha_perceive` 12/16 rota, `_preprocess + rota_bul` 0/16. Ders: "T8'in dersini kendim ihlal ettim: ölçüm yolu üretim yolundan ayrı olamaz." Kanıt: `simulation/scripts/iha_perceive.py:92-94`.

**11. D-53 · 2026-08-11 · `KRİTİK · Ölçüm zemini yanlış: data/raw_frames HTAB arenası değil, OTOPARK`**
Codex-2 ikinci itiraz; mimar üç noktada yanlıştı ("üçüncü kez"); asıl bulgu: tek gerçek ölçüm zemini bir otopark, şartnamenin 3 güzergâhı yok. Karar D-56: kompozit zemin. Ders: ölçmeden önce zemine bak — D-99 bu dersin tekrarıdır. Kanıt: `whatsapp_video_2026_07_30_...` kareleri.

**12. D-61 (ikinci) · 2026-08-11 · `TIKAYICI · v21'in "geçilebilir" sınıfı bu alanda anlamsız: çatı, çim ve toprak yol sayılıyor`**
Kullanıcı GUI'de "çatıyı yol sanıyor" dedi; mimar %74 kaplamayı sağlık sanmıştı, oysa v13/v16 kaydı yüksek kaplama = yanlış-pozitif çöküşü diyordu. Üç şikâyet tek kök neden. Ders: "model suçsuz" çıkarımı geri alındı; ölçek kapısı daha kötü sorunu örtüyordu. Kanıt: `gorunum_0.png / gorunum_1.png`.

**13. D-67 · (tarih yok; D-63 ile D-84 arası, ~12 Ağu) · `KÖK NEDEN BULUNDU · 2 sınıflı veri kümesi modele "çatı zemin değildir" demiyor`**
v22 alan-içi IoU 0,311→0,512 ama otopark çöküşü değişmedi. `download_and_convert.py:72-83` yalnız 7 ve 8'i alıyor; bina/ağaç/su etiketsiz arka plana düşüyor, denetim almıyor. Karar: T54 (engelli dönüşüm). Kanıt: `dataset/download_and_convert.py`, `dataset/rescuenet_11sinif/data.yaml`.

**14. D-84 · (~13 Ağu) · `DÖNÜM NOKTASI · Gerçek arena karesi bulundu: v21 KÖR, kapı YANLIŞ ATEŞLİYOR`**
Şartname s.9 figüründe v21 zemin %0,0; v24 %57,7 ve doğru segmentliyor; T52 kapısı gerçek arenayı reddediyor. Karar: v24 geçişi güçlendi. Ancak D-99 bu kaydın "gerçek" sıfatını düşürdü. Kanıt: `data/arena_referans/sartname_s9_arena.png` (sha `1f109df6...`).

**15. D-99 · 2026-08-14 · `🔴 BUYUK DUZELTME · "Gercek arena karesi" GERCEK DEGIL: sartname figuru YAPAY ZEKA URUNU; D-84/D-87/D-88/D-92/D-95 zinciri yeniden degerlendirildi`**
Kullanıcı "şartnameyi incele" dedi; Şekil 1 altyazısı "tamamen yapay zekâ ile oluşturulmuştur". Beş kaydın geçerlilik alanı daraltıldı, silinmedi; D-95 kararı yeni gerekçeyle ayakta (v25 dağılım-yakını sahnede tam çöküyor). Ders: kaynağı kullanmadan önce kaynağın kendi sayfasını oku. Kanıt: şartname PDF s.8.

**16. D-104 · 2026-08-14 · `DENETIM + KARAR · T66 KABUL: dusen kapi GECERSIZ bir kiyastir; v26 durduruldu, v27 T66 uzerinde kosacak`**
Mimar kapıyı yanlış modelle (v24, ada geometrisi dağılım dışı) ölçtürmüştü; yer gerçeğiyle ölçüm: T71 0/259, T66 24/260 (%9,2 sıyırma) — gerçek sinyal koridor darlığı (T74 açıldı). Ders: substrat değişince sabit modelle ölçmek modelin OOD'sini ölçer. Kanıt: D-103 `51_sentetik_arena.py`, `delikli_poligonlar`.

**17. D-107 · 2026-08-14 · `ONCEDEN KAYIT · v27 kabul olcutleri — SONUC GORULMEDEN yazildi`**
K0–K5 eşikleri (K1 ≥230/260, K2 ≤%15, K3 ≤%3, K4 ≤%5, K5 = 0 px) eğitim bitmeden yazıldı; gerekçe: D-85/D-90/D-104'te ölçüt sonuçtan sonra rasyonalize edilmişti. Bu, projenin **ön kayıt** kuralının doğduğu kayıttır; sonraki her terfi/ret bu kalıpla yapıldı (D-123, D-129, D-132, D-135, D-141, D-334, D-340, D-344, D-355). Kanıt: kayıt metni; `scripts/olcum/*_on_kayit.md` dosyaları.

**18. D-113 · 2026-08-14 · `🔴 KUSUR · best.pt YANLIS MODELI TUTUYOR: best_fitness ULASILAMAZ bir tavana kilitlenmis`**
`best.pt` epoch 43'te donmuş; `best_fitness=1,318` bu veride hiç ölçülmemiş; epoch 112 `last.pt` %21,5 daha iyi. Karar: v27 `last.pt` ile kabul (D-115), kayıt defterine `last.pt` girdi (D-116). Ders: kontrol noktasını ad değil ölçüm seçer; D-331'de "model seçimi kapıyla, val mAP ile değil" kuralı aynı köktendir. Kanıt: fitness formülü ultralytics 8.4.92 kaynağından, `v27_t66_adalar/weights`.

**19. D-119 · 2026-08-15 · `🔴 OLCUM · Sahaya giden ONNX ALTI KAPIYI DA GECIYOR — ama koridor SECIMI binde-4'luk gurultuye karsi KARARSIZ`**
ONNX/.pt maske IoU 0,9968; karar 258/260 aynı ama 2 karede rota 28 m sapıyor. Ders: kabul kaydı uçacak artefakta ait olmalı; kararsızlık ayrı bir eksen (D-122: %3,46). Bu eksen v28/v30 tartışmasını (D-134) ve K5 sıkı kapısını (D-150) doğurdu. Kanıt: `navitas_seg_v27_best_512_fp16.onnx` karşılaştırması.

**20. D-131 · 2026-08-15 · `🔴 RED · v29 (gercek otopark verisi) — GERCEKTE 0/67 -> 64/67, AMA ARENADA K5 DUSTU: EZBERLEME`**
12 kat çoğaltma gerçek karede 64/67 verdi ama K5 bariyer 3 px, K3 %0,78. Ön kayıtlı kural gereği RED. D-133: 4 kat (v30) dört şartı sağladı. Ders: doz eğrisi tek yönlü değil; ön kayıt olmasa 64/67 cazibesiyle terfi olurdu. Kanıt: `karisim_gercek_otopark.yaml`, D-129 ön kaydı.

**21. D-134 · 2026-08-15 · `🔴 DUZELTME · D-133'teki "oneri: v30" TUTARSIZDI; kanit v28'i gosteriyor`**
Aynı kayıtta "doğrulanmadı" yazdığı 65/67 sayısına dayanıp v30 önermişti; v28'in kararlılık üstünlüğü (3/260 vs 8/260, üç kat) ölçülmüştü. Karar: sevk kararı insana bırakıldı; kullanıcı v30 dedi (D-136). Ders: kanıt durumunu "ölçülmüş/zayıf" diye ayır; ve **sevk kararı kullanıcınındır** (D-133 kuralı, D-182/D-256/D-294'te tekrar).

**22. D-140 · 2026-08-16 · `🔴 KUSUR + OLCUM · seed EGITIMI HIC ETKILEMIYOR: v31, v30'un BIT-BIT AYNISI`**
537/537 tensör aynı; ultralytics `build_dataloader` sabit tohum. D-251/D-253 aynı deneyi (bilmeden) tekrarladı ve 1,18 saat GPU boşa gitti (D-252: "koşmadan önce defteri aramadım"). Ders: gürültü ölçmek için tohum değil ayrı çekiliş gerekir; defter koşumdan önce aranır.

**23. D-150 · 2026-08-17 · `🔴 T93 · K5 SIKI KAPIDA **IKI MODEL DE DUSUYOR** — v30'un K5 = 0/173'u SANSLI BIR CEKILISMIS · D-149 DUZELTILDI`**
Kare başına 1 temiz + 20 gürültülü çekiliş: sa_000131 v30'da %19, v33'te %86 kesiyor. Ders: tek çekilişte ölçülen bir sıfır, sıfır değildir; kapı popülasyon üzerinde ölçülmeli (D-243/D-244 K5 zemini popülasyona taşındı). Kanıt: `80_k5_siki_kapi.py`, `scripts/olcum/t93_on_kayit.md`.

**24. D-154 · 2026-08-17 · `🔴 T94 KOKENI BULUNDU · yol_duzelt STRING-PULLING'i rotayi TEK DUZ KIRISE indiriyor; dar karelerin 39/46'si BUNDAN dar`**
Ham A* darboğazı 33 px, kanonik yol 28,14 px; suçlu `_rotayi_ornekle` değil `yol_duzelt`. Önce D-151/152/153'te üç hipotez çürüdü. Karar: açıklık koruyan kiriş varyantları ön kayıtla sınandı, çoğu RED (D-155/156/159), sonunda `rota_bul` katmanına W1 biçimi girdi (D-164). Kanıt: `84_t94_seyreltme.py`, `rpi_inference.py:1224`.

**25. D-180 · 2026-08-19 · `🔴 KABUL DENETCISININ K5'i HER MODELI REDDEDIYOR — URETIM MODELI DAHIL; "olculemedi" ile "dustu" AYIRT EDILMIYOR`**
`kes = None` → `None == 0` False → "K5 DÜŞTÜ". Karar D-197: üç durum GEÇTİ/DÜŞTÜ/ÖLÇÜLEMEDİ, ÖLÇÜLEMEDİ terfiyi yine bloklar; D-226 K1–K4'e de yayıldı. Ders: **ÖLÇÜLEMEDİ ≠ GEÇTİ, ama ÖLÇÜLEMEDİ ≠ DÜŞTÜ de** — rapor doğru atıf yapmalı. Kanıt: `65_kabul_denetcisi.py:101-111`.

**26. D-182 · 2026-08-19 · `✅ URETIM MODELI v30 -> **v34** (KULLANICI KARARI) · terfi YARIM KALAMAZ: hiza paketi kusuru yakaladi`**
Koşum adı `v23`, üretim adı v34 (küçük numara karışıklığı önlendi). Yalnız defter güncellenince 8 test düştü (registry sha, iki kılavuz, manifest, ONNX aynı sürüm). Ders: terfi altı hizalama noktasıdır, tek commit'te yapılır (D-256, D-294 aynı kalıp). Kanıt: `test_model_registry`, `test_uretim_modeli_hizasi`.

**27. D-210 · 2026-08-20 · `🔴 T117 CEVAPLANDI (KÖK NEDEN) · Model çatıyı ÖĞRENMİŞ (recall %96,6) — gerçek karede görmüyor çünkü O KARELERİN KENDİ ETİKETİ "ZEMİN" DİYOR`**
Altı hipotezin beşi çürüdü; RescueNet val'de hasarsız bina recall 0,966; otopark karelerinin copy_paste etiketi 448/448 tam-kare zemin. Karar T121: 56 kaynağa elle çatı etiketi → D-225 çatı 0,011→0,989. Ders: model değil etiket suçlu olabilir; "veri tek kaldıraç" öncülü tashih edildi (D-211). Kanıt: `f4_doku.json`, `dataset/copy_paste_t121`.

**28. D-238 · 2026-08-20 · `🔴 D-237'YE EK · Kazanan adayın DÜRÜST BEDELİ ölçüldü: t122ac, v34'ün çatı-DIŞI zemininin **%39,7'sini** kaybediyor ve kaybın **%88'i etiketsiz** kalıyor`**
Gözle kontrol (D-80 zorunlu) gri bölgeleri işaret etti, ölçüm karara bağladı. Yön fail-safe ama yetenek kaybı; D-239/D-240 sıralamayı iki kez düzeltti (gerçek otopark %47–52 sürülebilir; 0,67 tavanı gerçeğin üstünde). Ders: kazanç bedelsiz raporlanmaz. Kanıt: `results/t122/yetenek_bedeli.json`.

**29. D-243 · 2026-08-20 · `⚖ MİMAR KARARI · K5'in ZEMİNİ TAŞINIYOR (öneri KABUL) — ama dört şartla, ve en önemlisi: **bariyer MODELDEN GELMEYECEK**`**
Bariyer değerlendirilen modelin maskesinden okunursa bariyere kör model kapıyı trivial geçer. Ölçüt: kör model düşmeli. D-244/D-246 dört şart testle kilitlendi; D-255'te ilk model tam zinciri geçti. Ders: kapının referansı sınanan sistemden bağımsız olmalı. Kanıt: `results/t126/k5_zemin_*.json`.

**30. D-255 · 2026-08-21 · `⚖ MİMAR DENETİMİ · T127 GEÇTİ · **İLK KEZ bir model tam kabul zincirini geçti** (kendi koşumumla doğruladım) — ve K2'de ÜÇ MODEL BOYUNCA TEK YÖNLÜ bir sürüklenme var`**
t127_temiz: K0–K5 altısı birden; temiz bölümle eğitilince sayılar korunuyor (çatı kaçağı 0,043, 67 karede red 0). Karar D-256: v35. Ders: "aynı model uyuşması kanıt değil; kanıt kendi koşumum." Kanıt: `65_kabul_denetcisi` canlı koşum çıktısı.

**31. D-272 · 2026-08-21 · `🔴 T138 · GECE KARELERİ EĞİTİME UYGUN DEĞİL (8/569, eşik 30) — ama **ÖN KAYITTAKİ AĞIR HÜKÜM ATEŞLEDİ: sistem gece karesinde YOL=2 · güven=1,000 yayınladı**`**
Karanlıkta zemin maskesi %87 boş (D-270) ama sistem güvenle rota yayınlayabildi. Ders: ön kayıt yalnız kabul değil, tehlike sinyali de tanımlar; görünürlük doz-yanıtı ölçüldü (D-275: karanlıkta modeller arası IoU 0,000). Kanıt: `results/t138/gece_kumesi.json`.

**32. D-284 · 2026-08-26 · `🔴 VEKİL KAPATMA ÇÜRÜTMESİ · 10 kapatma adayının **8'i YIKILDI** · triyaj tek başına güvenilmez — ve dördü aynı kalıp: *"Yap" satırı sınandı, ASIL İDDİA sınanmadı*`**
T54 için mutasyon: kök-neden satırı geri getirilince 8/8 test yeşil kaldı — testler kümeyi çiviliyor, uygulamasını değil. Ders: görev "yapıldı" demek hipotezinin sınandığı anlamına gelmez; kapatmadan önce çürütücü. Kanıt: `results/t133/kapatma_curutme_10.json`.

**33. D-294 · 2026-08-26 · `✅ ÜRETİM MODELİ **v35 → v36** (gece_v7a) · **kullanıcı kararı, ön kayıtlı eşikler GEÇİLMEDİ** · altı hizalama noktası tek commit'te (c1826f1)`**
ROTA ≥10 (v7a 8), MASKE_YOK ≤10 (16) geçilmedi; eşik değiştirilmedi, CONTRACTS §12'ye istisna yazıldı. Gerekçe: yanlış güzergâh %71→%18 (şartname §6.2: yanlış güzergâh 0 puan). Karşı kalemler gizlenmedi. Ders: kuralı esnetmek yerine istisnayı adıyla kaydet. Kanıt: `models/navitas_seg_v36_best.pt` sha `1d1caca6…`.

**34. D-296 · (27 Ağu) · `✅ T155 KAPANDI · **yayınlanan road düzeltildi: 6/15 → 15/15** — ve düzeltme bir SÖZLEŞME ÇELİŞKİSİNİ açığa çıkardı (T119, mimara açık soru)`**
`road` rotanın en dar TEK pikselinin şeridinden okunuyordu; o piksel 13/15 sahnede rotanın ucundaydı (güzergâhlar KB/HB'de birleşir). Tek tanım `karar_sozlesmesi.rota_serit_karari` (madde 16: tek doğruluk kaynağı). Kanıt: `results/t155/`.

**35. D-313 · 2026-08-27 · `✅ T165 KAPANDI — üretim, referansın KESİN olduğu 88 karede **84 doğru şerit**; ön kayıtlı eşik **tam olarak** karşılandı`**
Eşik ≥84/88, ölçülen 84: "marj sıfırdır … sınırda geçti." D-309/310/311 zinciri önce 43/50 ölçmüş, sonra 5 yanlışın 4'ünün etiket kusuru olduğunu bulmuştu. D-314/D-316 K7 kapısı zincire girdi; D-315/D-378 tek düşen karenin etiket kapsamı farkı/gerçek pozitif olduğu görüldü. Kanıt: `results/t165/iyi_kosullu_uretim.json`.

**36. D-319 · 2026-08-27 · `🔴 T171 — §5.3.2'nin "asgari 30 m irtifa" şartı HİÇ UYGULANMIYORDU; üstelik uyum raporumuz **uygulandığını iddia ediyordu**`**
`rota_olcek_reddi` irtifa dalının iki kolu da `return None`; 10 çağrı yerinin hiçbiri `irtifa_m` geçmiyordu. D-320: düzeltirken heartbeat susturma kusuru üretildi, süit kilitlenince yakalandı — ders: failsafe döngüsünde yayın ile yayına eklenen bilgi aynı `try` içinde olamaz. Kanıt: `tests/test_t171_asgari_irtifa.py` 16/16.

**37. D-332 · 2026-08-28 · `🔴 v37'ye GEÇİŞ DENENDİ VE GERİ ALINDI — kabul zinciri GEÇTİ, gerçek arena karesi REDDETTİ`**
ep105 K0–K7 hepsini geçti (K7 %100); ama figürde kaplama %4,4→%56,1 `ZEMIN_MASKESI_SUPHELI`, K0 geçişi küçük bozmalarda kararsız. Yakalayan test zincirin dışındaydı → D-333 K8 gerçek kare kapısı (yeni eşik uydurulmadı, üretimdeki kapı kullanıldı). Ders: zincirin dışında kalan her kapı bir gün atlanır.

**38. D-349 · 2026-08-28 · `🔴🔴 SAHA KAMERA YOLU HER KAREYİ AYNALIYOR — açık yol 1 ile 3 TAKAS oluyor, §2.1 → 0 PUAN`**
`cv2.flip(frame, 1)` ilk commit'ten kalma; 16 karenin 15'i takas. Kabul zincirinin tamamı `analyze_path`'i doğrudan çağırıyordu, hiçbiri `run_camera`'dan geçmiyordu. 53 ajanlı şartname risk taramasının en üst bulgusu; ajana güvenilmedi, ölçüldü. Karar: satır kaldırıldı, asimetrik kare nöbetçi testi. Ders: D-22/D-51'in "ölçüm yolu = üretim yolu" dersinin en pahalı tekrarı. Kanıt: `codes/rpi_inference.py:2162`, `git log -S`.

**39. D-368 · 2026-08-29 · `🔴 ŞARTNAME KAYNAĞINDAN OKUNDU — HEDEF YENİDEN HİZALANDI`**
§2.1: görev üç yoldan açık olanı tespit etmek (K6/K7 tam bunu ölçer, K1 ön koşul); §6.4: hakem teyidi olmazsa uçuş geçersiz — hafife alınmıştı. D-410 (takvim) ve D-417 (FDR yönergesi, isim yasağı) aynı sınıf: resmî belge vekil belgeden değil kaynağından okunur.

**40. D-375 · 2026-09-01 · `🔴 FP16 DENKLİĞİNİN İLK ÖLÇÜMÜ VAKUMDU — half SESSİZCE UYGULANMADI · yakalandı, düzeltildi, gerçek ölçümle **F1/F2 GEÇTİ**`**
893/893 kare bit-eş çıkınca aracın kendisinden şüphelenildi: ultralytics predictor ilk çağrıda kurulur, sonraki `half` yok sayılır; iki kol da FP32 koşmuştu. Sınıf adı: `FARKSIZLIK != DENKLIK` (kardeşi D-370: CRLF yüzünden uygulanmayan mutasyon "ölçüldü" sayılıyordu). Ders: A/B kıyasında %100 eşlik önce aracı şüpheli kılar. Kanıt: `results/b4_fps/fp16_denklik_20260901.json`.

**Ek — saha/donanım dönemi (Eylül) için üç kayıt daha:**

**D-403 · 2026-09-03 · `FAZ B HAZIRLIGI: dort arac + curutucu turu — parasut aktarim zinciri iki KRITIK kusurla dogdu, olculdu, kapatildi`** — PARACHUTE çerçevesi `rpi_inference`'in efemer soketine düşüyordu, alıcı 0 komut gördü; `yks_gui --iha HOST:PORT` eklendi; CONTRACTS §7.4 MAVLink çoğullayıcı zorunlu. **D-422 · (4 Eyl) · `SAAT KILIDI: sapma 30 dk'yi asinca kritik komutlar KALICI oluyordu`** — RTC pilsiz Jetson 1970'e açılır; ofset örneği tavanın kendisi tarafından eleniyordu; gerçek nesneyle üç senaryo yeniden üretildi. **D-431 · 2026-09-06 · `JETSON KARTI "NANO 4GB / JetPack 4.6" DEĞİL, **ORIN NANO 4GB / JetPack 7.2.1** ÇIKTI`** — 246 MB cp38 wheel + Nano belgesi geçersiz; `.pt` FPS kapısı geçti, engine denkliği 3/126 ile D-303 eşiğini aştı → uçuş `.pt` ile. Mimar notu: kutusu açılmamış donanım varsayımının DÖRDÜNCÜ tekrarı.

---

## 3. Tekrarlayan örüntüler ve projenin kurduğu kurallar

### 3.1 "Ölçüm yolu ≠ üretim yolu" (en pahalı sınıf)
- D-22 (saha yolu test görmüyor) → D-48/D-49 mimar yolu yeniden kurdu, D-51 düzeltti → D-58 iki üretim hattı 13/67 ayrışıyor → D-165 "ölçüm hiçbir turda üretimin çağrı imzasını kullanmadı" → **D-349** `run_camera`'daki `flip` hiçbir kapıdan geçmiyordu (0 puan riski) → D-299 genel kapı üretim yolunu da zorluyor.
- **Kural:** kabul zinciri ve genel kapı `run_camera` birebir çağrı sırasıyla koşar (D-298/D-299/D-349 nöbetçi testi); "üretim yolu" tek tanımlıdır (D-58/D-60b, T43 Halka 5).

### 3.2 Doğrulayıcı/kapı yalan söyledi ("sahte geçiş", "vakum ölçüm")
- D-15 (grep kapısı hep 0), D-32 (sözdizimi geçen ama çalışmayan `_h.update`), D-180 (`None` = DÜŞTÜ), D-284 T54 (mutasyon geri gelince 8/8 yeşil), D-335 (K7 mutasyon testi sessizce etkisizleşmiş), D-357 (verdikt betiğinde üç kusur), D-370 (CRLF, mutasyon uygulanmadı, exit 0), **D-375** (`half` yok sayıldı, 893/893 bit-eş), D-412 (YKS her kurulumda ölüyordu, belge commit'i süpürmüştü), D-415 (çıkarıcı ASCII etiketi görmedi, 188→177 yanlış yöne "düzeltme"), D-423 (48 vs 51).
- **Kurallar:** (a) **pozitif kontrol** — kapı bir şeyi yakalayabildiğini göstermeden "temiz" diyemez (D-15); (b) **mutasyon kontrolü** — 4 Ağustos'tan itibaren her denetimde kusur enjekte edilip testin düştüğü gösterilir (`## Kayit 2026-08-04 · Mimar denetimi: Codex-1 T3-T13 (mutasyon testiyle)`, D-136 beş uç, D-212, D-228, D-242, D-259, D-269); (c) `FARKSIZLIK != DENKLIK` — %100 eşlik önce aracı şüpheli kılar (D-375); (d) **ÖLÇÜLEMEDİ ≠ GEÇTİ** ve ≠ DÜŞTÜ — üç durumlu kapılar (D-197, D-226, D-333).

### 3.3 Ölçüt sonuçtan sonra seçildi → **ön kayıt**
- D-85/D-86 (eşik alt kümenin azamisine oturtuldu), D-90 (tanıma bağlı %92,7), D-104 (yanlış modelle kapı) → **D-107** ön kayıt doğdu. Sonra: D-123, D-129, D-132, D-135, D-141, D-157 ("3. ölçütü ben yanlış çiviledim"), D-160/D-163 (ölçüt kapsam hatası, "üçüncü/dördüncü tekrar"), D-334/D-336 (ön kayıt düzeltmesi mutant koşulmadan), D-340, D-344/D-345 ("ön kaydım eksik yazılmıştı"), D-355, D-374–D-377.
- **Kural:** eşik, karar sırası ve "hangi dal ateşlerse ne olur" koşumdan önce yazılır; sonuç geldikten sonra eşik gevşetilmez; kural ihlal edilecekse istisna adıyla sözleşmeye yazılır (D-294).

### 3.4 Ölçüm zemini/kaynağı yanlış
- D-53 (otopark, arena değil), D-62 (üç ölçüm zemini de geçersiz), D-99 (figür yapay zekâ), D-201 (payda farkı), D-233 (val %100 kirli), D-339/D-341/D-342 (sentetik arena arenaya benzemiyor; kendi testim geçersizdi), D-346 (189 gizli kopya), D-376 (R katmanının %62'si eğitim kümesi), D-377 (sızıntı faydayı 4 kat şişirdi).
- **Kurallar:** eğitim/doğrulama ayrıklığı her ölçümde beyan edilir (D-233 "bulaşma beyanı", D-347); şartname/yönerge kaynağından okunur (D-99, D-368, D-410, D-417); "bakir küme" tanımı yazılıdır (D-198, D-292).

### 3.5 Kutusu açılmamış donanım hakkında varsayım
- D-36 (vekil kartta kanıtsız FPS), D-413 (microSD yok), D-424 (Pixhawk PX4 ile gelir), D-425 (firmware sürümü sabitlenmemiş), D-426 §3 (künye üç yerde yanlış), **D-431** (Orin Nano çıktı), D-435 (motor künyesi değişmiş), D-436 ("SunnySky V3115" yok).
- **Kural (D-424 §5, D-431):** "üzerinde ne var?" sorusu ön kayıtla sorulur; **beyan ≠ ölçüm** — kutu açılır açılmaz ilk komut künyeyi ölçen komuttur (`/proc/device-tree/model`, Mission Planner `Messages`), belge ondan sonra yazılır; sahada her adımda "ne göreceksin" yazılıp sayı istenir (D-426 §6, D-428).

### 3.6 İki kopya, yalnız biri denetleniyor / ayna bayatlığı
- D-01 (ikiz dosyada düzeltme yapılmadı), D-55, D-89 (beşinci uç çevrilmedi), D-106/D-116 (registry v4'te kalmış), D-188 ("dördüncü örnek"), D-189–D-192 (ayna testle kilitlendi, 37/37 çift), D-352 (kurulum bloğu kılavuzu beslemiyor), D-418 (8 bulgu ayna bayatlığı), D-421 (runbook ölü blok).
- **Kural:** ayna silinmez, testle kilitlenir (D-189); `KOPYALAR` listesi ve `test_jetson_comms_paketi` (D-403/D-404); terfi = altı hizalama noktası tek commit (D-182/D-256/D-294); **tek doğruluk kaynağı** (madde 16: registry `resolve_model()`, `imgsz` tek kaynaktan D-176, `rota_serit_karari` D-296, K0 tabanı kimlikli D-264).

### 3.7 Fail-closed / fail-dangerous
- Fail-closed kararı: `load_model` fail-closed (D-116), K-B çekimserlik (D-37/D-38), zemin sağlamlık kapısı (D-62, D-72 "fail-closed · köşe tek sayım"), `rota_bul`'a kapı (D-268), OLCULEMEDI blokluyor (D-197), engine kayıt defteri (D-354, D-431).
- Fail-dangerous yakalananlar: D-92 ("bizi koruyan şey bir güvenlik kapısı değil, bir EKSİKLİK"), D-146 (T90 fail-dangerous açık), D-272 (gece karesinde güven 1,000), D-320 (heartbeat susturma), D-349 (ayna), D-422 (saat kilidi komutları kalıcı öldürüyor — ters yönde fail), D-428 (RC failsafe düştü: link kopunca son değerleri tutuyor).
- **Kural:** kilit eklenirken açan taraf kanıtlanır (D-03); failsafe döngüsünde yayın zorunlu, bilgi ek (D-320); kapı bir modelin "kör" olduğu durumda düşmelidir (D-243).

### 3.8 Süreç: çürütücü turu, öner-bekle, itiraz, kayıt silinmez
- **Çürütücü turu** defterin ilk gününden beri var (3 Ağustos: her kritik bulguya "savunma avukatı" ajanı; 11 bulgu ayakta, 0 çürüdü). Sonra: D-281 (üç refuter), D-284 (10 aday, 8 yıkıldı), D-383 (dört gerçek kusur), D-405/D-407/D-411/D-415/D-421 ("onaylayan tur hiçbir şey bulmazdı, çürüten tur 13 tıkayıcı buldu").
- **Öner-bekle / itiraz protokolü:** Codex-2 görevi zorlamayıp `[ ]` bıraktı ve haklı çıktı (D-50/D-51/D-53); D-200 "İTİRAZ KABUL (protokolün ilk kullanımı)"; D-224, D-231/D-243.
- **Kayıt silinmez, düzeltme eklenir:** D-33, D-36, D-51, D-60, D-99, D-134, D-161, D-239/D-240, D-310/D-311, D-342, D-351, D-373 ("çürütülmüş kayıt geri işaretlenmeli" yapısal kusuru), D-432. Başlıklarda `DUZELTME/YANLIŞ/ÇÜRÜ/KENDİ HATAM` geçen kayıt sayısı: **80/441**.
- **Numara çakışması:** eşzamanlı ajanlar aynı numarayı aldı; kural "kendi kaydını taşı, başkasınınkine dokunma" (D-95 "beşinci", D-140 "yedinci", D-258 tarama, D-431 D-428→D-431). Bu yüzden D-39, D-40, D-41, D-61, D-62 ikişer kez vardır; D-60b vardır; **D-416 yoktur**.
- **Aynı model uyuşması kanıt değildir:** yazan denetleyemez (AGENTS §9.3), kanıt denetleyenin kendi koşumudur (D-255, D-257, D-269).
- **Kural insana değil betiğe:** push kapısı (D-360 "kapı kırmızıyken push ettim", D-430 aynı ihlal, → `scripts/push_kapisi.py`, D-432 port sızıntısı nöbetçisi).

---

## 4. Sayılar

- Toplam `### D-` başlığı: **441**; benzersiz D-numarası: **435 + D-60b** (D-39/40/41/61/62 ikişer kez; D-416 yok).
- Başlık/gövdesinde ISO tarih taşıyan kayıt: 293 (Ağustos 267, Eylül 26); 148 kayıtta ISO tarih yok (bunlar bölüm başlığı `## Kayit 2026-08-0x` altında ya da "5 Eylul"/"7 Eylül" gibi metin tarihli).
- Tarih taşımayan kayıtlara bir önceki kaydın tarihi devredilerek (defter kronolojiktir) yapılan sayım: **Ağustos 379 · Eylül 62** (`grep -n "^### D-"` + awk; ±birkaç kayıt hata payı).
- Aynı yöntemle günlük zirveler: **20 Ağustos 52 kayıt** (filo turları, T121/T122), 28 Ağustos 40, 3 Eylül 32, 27 Ağustos 28, 14 Ağustos 27, 21 Ağustos 27.
- Haftalık (ISO hafta): 32. hafta 33 · 33. hafta 117 · 34. hafta 133 · 35. hafta 92 · 36. hafta 66.
- Başlığında `ONCEDEN KAYIT / ÖN KAYIT` geçen kayıt: 17; gövdede "ön kayıt/on kayit" geçen satır: 279. "çürüt/curut" geçen satır: 182. "mutasyon": 248. "ÖLÇÜLEMEDİ/OLCULEMEDI": 130.
- Başlığında `KAPANDI/COZULDU/UYGULANDI` geçen kayıt: 79; `DENETIM` geçen: 48.
- Üretim modeli zinciri (defterden): v4 (15 Temmuz) → v20/v21 (D-20, 5 Ağu) → v24 (D-83) → **v27** (D-116, 14 Ağu) → **v30** (D-136, 15 Ağu) → **v34** (D-182, 19 Ağu) → **v35** (D-256, 21 Ağu) → **v36** (D-294, 26 Ağu); reddedilenler: v25 (D-95), v29 (D-131), v32 (D-142), v33 (D-148), v8 (D-331), v37 adayı (D-332), T199 adayı (D-366).
- Kabul zinciri büyümesi: K0–K5 (D-107) → K5 üç durumlu (D-197) → K5 popülasyon zemini (D-244) → K6 rota yol üstünde (D-290) → K7 şerit numarası (D-316) → K8 gerçek kare (D-333).
- Test süiti büyümesi (defterde geçen sayılar): 58 test (D-22, 7 Ağu) → 702 (D-233) → 728 (D-256) → 793 (D-270) → 962 (D-294) → 1157 (D-320) → 1947 (D-418) → 2121 (D-431, Jetson'da) / 2138 (D-427).

---

## 5. Muhtemel jüri soruları ve kayıtlara dayanan cevaplar

**1. En büyük hatanız neydi, nasıl yakaladınız?**
Saha kamera yolunun her kareyi aynalaması (D-349): ilk commit'ten kalma `cv2.flip(frame, 1)`, açık yolu 1↔3 takas ediyordu — şartname §2.1'de yanlış güzergâh 0 puan. Hiçbir kabul kapısı `run_camera` döngüsünden geçmediği için yakalanmamıştı. 53 ajanlı şartname risk taramasının en üst bulgusuydu; ajana güvenilmedi, kabul kümesinde her kare özgün ve aynalı koşularak ölçüldü (16 karenin 15'i takas), satır kaldırıldı, asimetrik kare nöbetçi testi eklendi ve genel kapı üretim yolunu zorlar hâle getirildi (D-299).

**2. Modelinizin gerçek arenada çalışacağını nereden biliyorsunuz?**
Bilmiyoruz; bunu defter açıkça yazar. D-56 "kapanmayan sınır: gerçek 30 m arena karesi olmadan başarım doğrulanamaz" der; D-99 tek "gerçek" sanılan figürün yapay zekâ ürünü olduğunu buldu; D-88 kısıtı "gerçekte daha ağır" diye güncelledi. Elimizdeki kanıt: sentetik kabul zinciri K0–K8 (D-107 → D-333), 111 gerçek DJI karesinde yanlış güzergâh %71→%18 (D-294), K7 iyi koşullu 88 karede 84 doğru şerit (D-313), ve figürde v36'nın "çekimser" kaldığı (D-339: karenin %80,9'u hiçbir sınıfa girmiyor). Bunu "geçti" değil "ölçülemedi" olarak raporlarız (D-197 kuralı).

**3. Neden v36'yı kendi eşiklerinizi geçmediği hâlde üretime aldınız?**
D-294: ön kayıtlı ROTA ≥10 (v7a 8) ve MASKE_YOK ≤10 (16) geçilmedi; eşik değiştirilmedi, CONTRACTS §12'ye adıyla istisna yazıldı. Gerekçe şartname §6.2'dir: yanlış güzergâh 0 puandır ve v36 111 gerçek karede yanlış güzergâhı %71'den %18'e, engel üstünde waypoint'i 79'dan 3'e indirdi. Sevk kararı D-133 kuralı gereği insanındır; karşı kalemler (val82 FP 0→2) registry'ye yazıldı. Kuralı gizlice esnetmek yerine istisnayı kayda geçirdik.

**4. "Her şey ölçüldü" diyorsunuz; ölçüm araçlarınız yanılmadı mı?**
Yanıldı ve bunu da kaydettik. D-15 grep kapısı hep 0 dönüyordu; D-180 kabul denetçisi `None`'ı "düştü" sayıyordu; D-370 mutasyon betiği CRLF yüzünden mutasyonu uygulamadan exit 0 veriyordu; D-375 FP16 kıyası iki kolu da FP32 koşmuştu (893/893 bit-eş). Kurallar bunlardan çıktı: pozitif kontrol, mutasyon kontrolü, "%100 eşlik önce aracı şüpheli kılar", üç durumlu kapılar.

**5. Sentetik veriyle eğitmek sizi yanılttı mı?**
Evet, iki kez ters yönde. D-18: sentetik arena eğitimi gerçek dokuyu unutturdu (v17 10/67). D-131: gerçek otopark verisini 12 kat çoğaltmak arenada K5'i düşürdü (ezberleme); 4 kat (v30) dengeyi tuttu (D-133). D-339–D-342: sentetik arenamızın arenaya benzemediğini gördük, "çıplak toprak yok" hipotezimizi kendi ölçümümüzle çürüttük; T199 arena profili adayı OOD boşluğunu kapatmadı (D-367). Bugünkü tutum: sentetik zemin kabul zincirinin ölçülebilir kısmıdır, gerçek başarımın kanıtı değildir.

**6. Kararlarınızı sonuçtan sonra rasyonalize etmediğinizi nasıl garanti ediyorsunuz?**
Ön kayıt (D-107): eşikler, karar sırası ve "hangi dal ateşlerse ne olur" koşumdan önce, `scripts/olcum/*_on_kayit.md` ve `ON_KAYIT.md` dosyalarına yazılır. Bu kural v29'u (D-131), v32'yi (D-142), beş T94 varyantını (D-155/156/159), INFER_SIZE 640'ı (D-377) reddetti; D-313'te eşik tam 84/88 karşılandığında "marj sıfırdır, sınırda geçti" diye yazdık. Ön kaydın kendisinin yanlış yazıldığı durumlar da kayıtlıdır (D-157, D-163, D-345).

**7. Haberleşme güvenliğini nasıl sınadınız?**
Ağustos boyunca yalnız sahte nesnelerle; 2 Eylül'de MAVLink katmanı gerçek çerçevelerle (D-387) ve SiK seri taşıyıcı gerçek bayt akışında (D-388) ilk kez koştu. Çürütücü turları paraşüt komutunun alıcıya hiç ulaşmadığını (D-403 KRİTİK-1), 308 ms'nin soket sabiti olduğunu (D-383), saat sapması 30 dk'yı aşınca kritik komutların kalıcı öldüğünü (D-422) ve test süitinin üretim portlarına bind ettiğini (D-427/D-432) buldu. Heartbeat/failsafe kalıbı D-320'de sözleşmeye girdi.

**8. Jetson'da hız yeterli mi? INT8 kullanıyor musunuz?**
Gerekli FPS kapsama hesabından 0,41 (en kötü uçuşta 0,61) çıktı (D-374); INT8 yolu D-371'de kapatıldı (kural: FPS ≥3 ise INT8'e girme; kullanıcı kararı FP16). Kart kutudan Orin Nano 4GB / JetPack 7.2.1 çıktı (D-431); `.pt` p50/p95 1,35/1,06 FPS ile eşik 0,61'i geçti, 10 dk sürekli koşuda termal bayrak yok; TensorRT engine karar denkliği 3/126 ile D-303'ün oransal eşiğini aştığı için uçuş `.pt` ile yapılacak. İlk FPS sayısı (14 FPS, D-36) kanıtsızdı ve kullanılmadı.

**9. Takım içinde denetimi nasıl kurdunuz; aynı ajan kendi işini onaylıyor mu?**
Hayır. Yazan denetleyemez (AGENTS §9.3); "aynı model uyuşması kanıt değildir, kanıt denetleyenin kendi koşumudur" (D-255/D-257/D-269). Çürütücü turu defterin ilk gününden itibaren standarttır (3 Ağustos: 11 bulgu ayakta, 0 çürüdü; D-284: 10 kapatma adayının 8'i yıkıldı; D-421: onaylayan tur sıfır, çürüten tur 13 tıkayıcı). İtiraz protokolü var ve işledi (D-50/D-51, D-200). Kayıtlar silinmez; 441 başlığın 80'inde düzeltme/çürütme/kendi hatam ibaresi vardır.

**10. Saha günlerinde ne öğrendiniz?**
5–6 Eylül: Pixhawk 6C PX4 ile geldi ve ArduCopter flash yordamı hiçbir belgede yoktu (D-424); 4.7.1 parametre uzayı 4.5'ten farklıydı, 4.5.7'ye dönüldü (D-425); RC alıcısı yanlış porttaydı, motor testi 4/4 (D-426); RC failsafe ölçüldü ve düştü (D-428); pervaneli üç devrilme tlog ile ölçüldü — FC doğru yönde düzeltti, ön itki yetmedi, M1 hasarlı, gaz adımla verilmişti (D-429); kumandadan arm `RC6_OPTION=0` olduğu için olmuyordu (D-433); motor künyesi belgelerdekinden farklıydı (D-435). Ortak ders D-431'in mimar notundadır: kutusu açılmamış donanım hakkında varsayım dört kez tekrarladı; **beyan ≠ ölçüm** — ilk komut künyeyi ölçen komuttur.
