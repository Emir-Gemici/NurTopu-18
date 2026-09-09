# 14 · ADIYAMAN SORU BANKASI — olası sorular, model cevaplar, kanıt yolu

> 120 soru, 12 başlık. Her cevap: **kısa cevap → kanıt (dosya / D-no / bölüm) → dikkat**. Cevaplar 10 Eylül 2026 durumuna göredir; sayı verirken tarihini söyle.
> Biçim bilinmediği için hem belge-jürisi (FDR üzerinden) hem saha-hakemi (prova/uçuş sırasında) soruları var. "Bilmiyoruz" cevapları 17'deki kalıpla verilir.
> Sorular ajan özetlerindeki (A–I) 100+ öneriden ve FDR açık kalemlerinden derlendi; tekrarlar birleştirildi.

---

## A. Görev ve şartname (01)

**A1. Sisteminiz ne yapıyor?** — İHA moloz alanının üstünden geçerken kamera görüntüsünde üç güzergâhtan açık olanı bulur, havadayken YKS ve İKA'ya yollar, hakem
onaylar, İHA iner, İKA açık güzergâhtan H brandasına gider. Kanıt: 01; FDR Bölüm 1 §Y-1-M01.

**A2. Yanlış güzergâh söylerseniz?** — 0 puan, görev sıfır (§5.3.2, §6.2). Bu yüzden tasarım fail-closed: çekimserlik ucuz, yanlış karar pahalı. Kanıt: `ARCHITECT_PLAN.md` §3.

**A3. İKA hangi koşullarda hareket eder?** — Şartname: İHA yere temas etmiş + YKS'den manuel tetik. Kodda üçüncü koşul: geçerli OPEN_ROUTE. `sür ⟺ OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO`.
Kanıt: CONTRACTS §7; `ika_receiver.py`.

**A4. 21 Eylül ne günü?** — FDR son teslim ve takımın Adıyaman provası; resmî uçuş 30 Eyl–3 Eki (tek atış). Dikkat: D-410'da bir kez yanlış sanıldı.

**A5. Görev test uçuşu ile yarışma görevi farkı?** — Quad/20×20 m/≥30 m/≤10 dk/İKA-paraşüt-mancınık yok vs sabit kanat+mancınık+paraşüt/50×50 HTAB/15+10 dk/İKA. Yazılım aynı, `--fda` bayrağı.

**A6. FDA puanı nasıl?** — FDR × 0,85 + uçuş × 0,15; uçuş 100 ya da 0 (hakem onayı + ≤ 10 dk; yanlış tespit 0). Kanıt: şartname §5.3.2.

**A7. Puan formülünde yazılım neyi etkiler?** — P_görev 600 (K=2'de 1200), t_İHA (180), t_İKA (40), P_uçuş; ağırlık terimi (25000−m)/10 baskın ve yazılım dışı.

**A8. Kaç uçuş hakkınız var?** — 3 periyot × 1; kullanılmayan yanar. Yarışma 6 gün.

**A9. Cezalar?** — İniş sapması −5/m, hands-off sonrası müdahale −100 (+süre hazırlığa), manuel paraşüt −50.

**A10. Haberleşme frekansı şartnamede var mı?** — Hayır; 433 MHz takımın seçimi. Batarya/boyut/irtifa sınırı, kill switch, FDS formatı da şartnamede yok. Kanıt: `ozet/H_sartname.md`.

**A11. "Üçüncü senaryo" nedir?** — Zor güzergâh periyodu (K_zorluk 2,0). Depodaki TYDA PDF'si **başka bir yarışmanın** (LLM) şartnamesi; atıf yapılmaz.

**A12. Alan hakemi neyi onaylar?** — Tespitin canlı yapıldığını ve İKA'ya aktarıldığını, monitörden, sözlü; onaysız tespit geçersiz (§6.2).

**A13. Uçuşu geçersiz kılan altı hâl?** — Süre aşımı, manuel müdahale, hakem teyidi/veri aktarımı yok, İHA-UB ihlali, kırım, paraşüt açılmaması (§6.4).

## B. Mimari karar (03)

**B1. Neden nesne tespiti değil serbest alan segmentasyonu?** — Şartname engelleri "vb." ile açık küme bırakır; tespit bilinmeyeni "geçilebilir" sayar (fail-dangerous); zemin
dışı her şey engel (fail-safe). Kanıt: RESEARCH_NOTES §2.1.

**B2. "Serbest alan otoritedir, nesne katmanı yalnız çıkarır" ne demek?** — `serbest = zemin AND NOT engel`, çıkarma en son; hiçbir dedektör serbest alanı büyütemez; yeni dedektör
eklemek monotonik güvenli. Kanıt: CONTRACTS §2; anayasa madde 15.

**B3. Engel sınıfını modelden neden kullanmıyorsunuz?** — Kullanıyoruz ama karar yolu yalnız zemin maskesine bakar; blocked AP50'yi %24 artırınca karar hiç değişmedi (nedensel bağ yok).
Engel sınıfı ön-eğitimde işe yaradı (v15 moloza basma %2,7 vs v13 %37,7).

**B4. Neden mAP'e göre model seçmiyorsunuz?** — mAP arena sıralamasını tersine çeviriyor (v13 mAP lideri, %37,7 moloza basma); gürültü tabanı sd 0,03 → 0,04 altı fark gürültü.

**B5. Araç dedektörü neden DOTA OBB?** — COCO aynı nadir karede 2 araç, DOTA 93; eşik indirmek çözmedi (domain uyumsuzluğu, 30 m nadir).

**B6. Neden SciPy yok?** — Anayasa madde 4 (Jetson sadeliği); medial-axis yerine açıklık ağırlıklı A* (1 + 3u²), erozyon yerine `dt ≥ r` eşiği.

**B7. Sınıf 2 çakışması neydi?** — Üreteçte 2=hedef, costmap'te 2=araç; H brandası engel sayılıp P_görev=0 olacaktı; tek otorite `sinif_semasi.py`, `KATMAN_ARAC=10`, import anında doğrulama.

**B8. Neden ROS yok?** — K-1: 58 günde ROS2 sahada çalışan JSON/UDP hattını riske atar, puan getirmez.

**B9. Hız mı doğruluk mu?** — Gereken FPS 0,9–2,6 (kapsama), alt sınır 0,61; hedef 3, asgari 1; 15 FPS hiç şart değildi. A/B/C seçimi güvenlikle, hızla değil.

## C. Rota ve karar (04)

**C1. Maskeden karara adımlar?** — serbest alan → distance transform → C-uzayı (dist ≥ 1,10 m/mpp) → en büyük bileşen → K-A uç bant → A* tanık yol → şerit (gövde) → K-B güven → yayın.

**C2. `R_GEREKLI_M` neden 1,10?** — 0,70/2 + 0,25 maske hatası + 0,50 takip hatası. Dikkat: `TAKIP_HATA_M` kodda "tahmin" işaretli.

**C3. Ölçeği nereden alıyorsunuz?** — Pixhawk `relative_alt` + kamera FOV: `2·h·tan(FOV/2)/W`; tazelik 0,5 s; yoksa `OLCEK_YOK` → rota yok. İkinci kaynak HB 2 m kenarı, yalnız doğrular; çelişkide ortalama alınmaz.

**C4. Şerit numarasını nasıl seçiyorsunuz?** — Rotanın gövdesinin (en çok piksel) hangi üçte birde olduğu; eski darboğaz-pikseli tanımı 6/15 doğruydu, gövde 15/15 (D-296).

**C5. Kaç ret sebebi var?** — On: OLCEK_YOK, ZEMIN_MASKESI_SUPHELI, MASKE_YOK, BILESEN_YOK, UC_BANT_TEMAS_YOK, ALAN_YETERSIZ, GORUS_HATTI_KOPUK, KENAR_GUVENSIZ, DUSUK_GUVEN, KORIDOR_DEGIL (+HEDEF_YOK). Hakem ekranında ayrı metin.

**C6. Güven eşiği neden 0,20?** — 0,50 gerçek yolda %100 çekimserlik verdi; gerçek dağılım p50 0,307, std 0,03 (ayırt edici değil); 0,20 taban koruyucu (guven=0 yayınını engeller).

**C7. Kaplama kapısı ne yakalar?** — Modelin çatı/çim/toprak dahil her yeri zemin boyaması: kaplama > 0,55 ∧ kenar > 0,40 → ret. Eşik modele bağlı, her terfide yeniden kalibre (0,55→0,67→0,55/0,40).

**C8. Letterbox neden crop değil?** — Crop 1024×576'da genişliğin %56'sını atıyordu (kenar güzergâhlar yok oluyordu); her oran içerik dikdörtgenine göre.

**C9. Kameranın aynalanması olayı?** — D-349: `cv2.flip` ilk commit'ten; 16 karenin 15'i sol-sağ takas; hiçbir kapı `run_camera`'dan geçmiyordu; kaldırıldı, nöbetçi test, genel kapı üretim kolu.

**C10. Kararlar titrer mi?** — Histerezis K=3 kare (farklı şerit teyit ister), NO_ROUTE asla gecikmez; H1 özgün eşiği geçilmedi (dürüstçe yazılı). v36 çevrilme 14/260 (v35 9).

**C11. HB (kırmızı H) tespitini kullanıyor musunuz?** — Dedektör var (ölçek doğrulama, 260/260 sentetik), rota hedefi olarak bağlı (T150); ama gerçek iniş pedinde %0 isabet ölçüldü → sahada dikkat.

**C12. İnce bariyeri model görmüyorsa?** — LAB kroma + en/boy ≥ 4 dedektörü engele ekler; kalibrasyon tek YZ figüründen; gerçek arenada kırmızı olmayabilir → fail-safe (ateşlemez).

**C13. Arena sınırını nasıl biliyorsunuz?** — Bilmiyoruz; üç aday imza güvenilmez çıktı. Yerine "bu bir koridor mu": darboğaz > şerit genişliği → KORIDOR_DEGIL (kısmi çözüm, 5/10).

**C14. Çözünürlük neden 512?** — v36, 12 karede: 512 ROTA 12/12, şerit 8/12; 640 11/12; 1280 3/12; registry'den okunur, çıplak yazılmaz (T163: sözleşme bir kez kendi üretimini yasaklıyordu).

## D. Sözleşmeler ve kapılar (05)

**D1. CONTRACTS.md neden var?** — Kusurların çoğu iki modülün aynı sayıya farklı anlam vermesiydi; tek doğruluk kaynağı, çıplak sabit yasağı (madde 16).

**D2. Genel kapı nedir?** — 15 belirlenimci arena sahnesi; KOL 1 `rota_bul` 15/15, KOL 2 `analyze_path` rota ≥ 14/15 ∧ road ≥ 14/15; her görevden sonra; düşerse görev geri alınır.

**D3. Ön kayıt nedir?** — Eşik ve karar sırası sonuç görülmeden yazılır, gevşetilmez (D-107); 36 artefakt; 640 denemesini reddetti (D-377).

**D4. Mutasyon kontrolü?** — Kusuru geri koy, test düşsün; düşmüyorsa test vakum. Aracın kendisi de denetlendi (CRLF, D-370).

**D5. ÖLÇÜLEMEDİ ≠ GEÇTİ nerede kod?** — Kabul denetçisi üç durumlu; ÖLÇÜLEMEDİ terfiyi bloklar (D-197); FDR her bölümde.

**D6. Kabul kapıları K0–K8?** — K0 körlük, K1 rota ≥ 230/260, K2 moloza basma ≤ %15, K3 ağır ≤ %3, K4 arena dışı ≤ %5, K5/K5A bariyer 0 px, K6 yanlış güzergâh ≤ %5, K7 şerit ≥ %95 (88 kare), K8 gerçek figür.
v36 hepsi GEÇTİ. **Sentetik; saha başarımı iddia etmez.**

**D7. Gerçek kare kapısı?** — DJI 0038 test29: ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, YANLIŞ = 0; v36 8/16/1/0 — iki eşik geçilmedi, insan kararı.

**D8. Saha zinciri 10 halka?** — kamera, model, çıkarım, maske, ölçek, hedef, rota, aktarım, sürüş izni, motor; 9 GEÇTİ, motor SAHİPSİZ; `simulation/` sahip olamaz.

**D9. Test süiti kaç test?** — Tarihli: 1896 (3 Eyl) → 2104 (4) → 2138 (7, PC) → 2204 (9, Jetson; 32 ortam kırmızısı).

**D10. Push kuralı?** — Genel kapı + tam süit yeşilken; mimar iki kez kırmızıyken push etti → `push_kapisi.py`.

## E. Model ve veri (02, 06)

**E1. Hangi model?** — YOLOv8m-seg, 512, iki sınıf, PyTorch `.pt`, sha `1d1caca6…`; `navitas-seg-v36-512`.

**E2. Hangi veri?** — RescueNet (3 502, T54 eşlemesi), sentetik arena (~2 700), gerçek kare + sentetik moloz (t127, 344), DJI ×5 (2 065) = 8 611; val 73 gerçek DJI.

**E3. Sentetik veri uydurma değil mi?** — Arena kurallı geometri (50×50, 3 koridor); etiket piksel-kusursuz; dokular RescueNet'in gerçek maskelerinden; yalnız sentetik körleştirdi (v17 10/67) → gerçek doku eklendi.

**E4. Sızıntı önlemi?** — 0038 eğitime/erken durdurmaya girmez; etiketler kör; T127 kaynak düzeyinde bölüm (eski val %100 kirli); v17 6 452 görüntüde arena eşleşmesi 0.

**E5. Doğruluk?** — Sentetik: K7 %98,8, K6 %2,75; gerçek kırsal: ROTA 8/29, yanlış 0; karışıklık matrisi test29 IoU zemin 0,49 / engel 0,74; ışık/gölge ÖLÇÜLEMEDİ.

**E6. v36 neden terfi etti?** — Yanlış güzergâh 15/21 → 7/38; bedel K3/K4/K6 (kapı içinde), kaplama 0,51→0,42, val82 FP 0→2; eşik değişmedi, istisna sözleşmede, v35 yedek.

**E7. Model kör kalırsa?** — MASKE_YOK/ZEMIN_MASKESI_SUPHELI ile ret; 51 s kör aralık ölçüldü (hız değil model); heartbeat `karar_yas` taşır, hakem yaşı görür.

**E8. Eğitim reçetesi?** — v35 tabanı, RTX 5080 Laptop, 17 epoch (en iyi 2), 0,65 sa; degrees/flipud/copy_paste 0 (defter "t127 birebir" diyordu, yanlıştı) → bariyeri 60–135°'de görmüyor.

**E9. Model sürüm zinciri?** — v21 (5 Ağu) → v24 → v27 (ilk ön kayıtlı kabul) → v30 → v34 → v35 (ilk tam zinciri geçen) → v36 (26 Ağu); v37 geri alındı (K8 doğdu).

**E10. INT8 kullanmadınız mı?** — Hayır: FPS ≥ 3 → INT8'e girme; FP16 kararı (D-371). Engine denkliği düştüğü için uçuş `.pt`.

**E11. Yeni sürüm nasıl kabul edilir?** — `65_kabul_denetcisi` K0–K8 + gerçek kare + ONNX/engine denkliği + genel kapı + süit; sha registry'ye; terfi insan kararı.

**E12. Tohum?** — Ultralytics sabit tohum; v31 = v30 bit-bit (D-140); ≈ 14,8 saat sonuçsuz GPU (FDR Bölüm 7).

## F. Haberleşme, YKS, İKA (07, 08)

**F1. Protokol?** — Tek satır JSON + `\n`, `v:1`; OPEN_ROUTE / NO_ROUTE / HEARTBEAT / ACK(`ref_tip`) / CMD / IHA_LANDED; taşıyıcı UDP ya da SiK; CRC yok (bozuk satır atılır).

**F2. Paket kaybolursa?** — ACK gelene dek aynı seq ile tekrar: rota 8×0,25 s, IKA_GO/ARM 0,25×20, PARACHUTE 0,20×40; alıcı idempotent.

**F3. Hakem onayı nasıl?** — 2 aşama; 2/2 yalnız İKA'dan ACK(ref_tip=OPEN_ROUTE) görülünce; bayat (>5 s) ve ankorsuz ret; FDA'da İKA kanıtı aranmaz.

**F4. "İHA ALDI" ne zaman yeşil?** — Beş alanlı güçlü ACK + Pixhawk `COMMAND_ACK ACCEPTED`; ARM için taze heartbeat `armed`; paraşütün mekanik açıldığı bilinmez (sensör yok).

**F5. İniş kanıtı?** — Pixhawk `EXTENDED_SYS_STATE ON_GROUND` + `relative_alt < 1 m`, aynı sysid, 3 ardışık çift; insan düğmesi kilidi açamaz; yabancı sysid atlanır.

**F6. Aktarım havadayken tamamlandı mı?** — İKA ACK kopyası YKS'ye geldiği an `iha_havada` damgası; iniş kanıtı önce gelirse kırmızı ihlal.

**F7. Saat kilidi?** — Jetson'da RTC yok; sapma 30 dk'yı aşınca komutlar kalıcı reddediliyordu (D-422); ofset öğrenme; bedel ilk 2 basamak.

**F8. Seri port çakışması?** — Tek sahipli; çoğullayıcı (UDP 14550–14552) ve SiK hub (5100); doğrudan `/dev/tty*` reddedilir.

**F9. Gecikme?** — Uçtan uca p95 113 ms (loopback, 33 kare); 308 ms'lik ilk ölçüm soket sabitiymiş (D-383); SiK RTT ÖLÇÜLEMEDİ.

**F10. Kanıt kaydı?** — `hakem_log.jsonl`, satır başına fsync, 16 olay, oturum uuid, model sha, repo commit; yazılamazsa FIRLATMA/ONAY kilit, ARM/RTL/LAND açık.

**F11. İKA nasıl sürer?** — Oransal yön kontrolü (TURN_GAIN 1,8, 10 Hz), waypoint izleme, 0,3 m son yarıçap; A* İHA'da; motor sürücüsü yok (T149).

**F12. İKA konumu?** — Bugün yalnız Gazebo; gerçek GNSS/odometri yok.

**F13. Simülasyon sonucu gerçek mi?** — Model gerçek ağırlıkla mozaikte koşar, karar yer gerçeğiyle kıyaslanır; ama Gazebo İKA'sını animasyon plugin'i sürer; "sim kanıtı saha kanıtı değil".

**F14. Paraşüt?** — FDA'da yok; final zinciri hazır (DO_PARACHUTE, ACK yalnız ACCEPTED); manuel −50.

## G. Jetson (10)

**G1. Görev bilgisayarı?** — Orin Nano DevKit 4 GB, JetPack 7.2.1, Ubuntu 24.04, Py 3.12; plan "Nano" idi, kutu açılınca ölçüldü (D-431).

**G2. FPS?** — pt p50/p95 1,35/1,06; engine 1,58/1,33; eşik 0,61 → GEÇTİ; 10 dk düşüş yok, ≤ 56 °C.

**G3. Darboğaz?** — Model değil: get_masks + costmap CPU'da ~520 ms (%82); engine toplamda 104 ms kazandırır.

**G4. Neden `.pt`?** — Engine karar denkliği D-303 oransal 3/126 > 5/260 düştü; nihai karar T66 ile (henüz Jetson'da değil).

**G5. Tek komutla açılış?** — `jetson_baslat.sh --kur/--kapi/--kuru/--durum`; 6 systemd birimi, `Restart=always`; `--kapi` üç MAVLink ucunu paralel doğrular.

**G6. Kamera?** — IMX477 CSI, köprü sistem Python'unda (GStreamer), `rpi_inference` venv'de HTTP'den; CSI ve ayna testi ÖLÇÜLEMEDİ.

**G7. Jetson'da süit neden kırmızı?** — 32 ortam: PC Windows yolları, PC'deki kabul kümesi, kardeş depo, git yok, Py3.12; kod hatası yok (K10).

**G8. Kart yanlış çıkınca ne kaybettiniz, ne kazandınız?** — 246 MB tekerlek + Nano belgesi geçersiz; TensorRT/CUDA apt ile kuruldu, engine derlendi; kural "beyan ≠ ölçüm".

## H. Saha ve Pixhawk (09)

**H1. Uçuş kontrolcüsü yapılandırması?** — ArduCopter 4.5.7, 48 parametreli şablon, her satırda NEDEN, testle kilitli; failsafe RC→RTL, GCS→RTL, pil LOW→RTL/CRT→Land, çit 50 m/60 m, RTL 35 m.

**H2. Neden 4.5.7?** — 4.7 SI reformu 9 parametreyi kırıyor (WPNAV_SPEED 300 → 300 m/s); şablon 4.5'e ölçülü; 16 gün kala port yok.

**H3. Failsafe test ettiniz mi?** — RC failsafe: **düştü** (alıcı son değeri tutuyor); düzeltme kumandada; diğerleri sahada tetiklenmedi.

**H4. Görev planı?** — TAKEOFF 32 → 4 köşe 20×20 → LOITER 60 s → LAND; 221,5 s ≤ 600.

**H5. 6 Eylül'de ne oldu?** — 7 Pixhawk kalemi kapandı; RC failsafe düştü; uçuş 3 kez reddedildi; sonra habersiz oturumda pervaneli üç devrilme; M1 hasarlı.

**H6. Neden devrildi?** — FC doğru düzeltti, ön itki yetmedi, gaz adımla verildi; pilot/seviye temiz; kalan: itki asimetrisi / CG-geometri; kural ≥ 2 s rampa, `MOT_SLEW_UP_TIME 1,0`.

**H7. Kumandadan arm neden olmuyordu?** — `RC6_OPTION=0`; dümenle arm çalışıyor (gaz ≤ 1030, yaw sağ 2 s).

**H8. Motor künyeniz?** — X2220 980KV ×4 + 1045 + 4S (beyan, etiket yok); 38,4 A > 38 A/30 s sınırı; itki bütçesi kapısı ÖLÇÜLEMEDİ (tartı yok); T211 açık.

**H9. Hazırlık süresini nasıl tutuyorsunuz?** — İstasyon başına tek komut, systemd, paralel kapı; her 30 s = 1 puan.

**H10. Sahada koşan yazılım rapordakiyle aynı mı?** — Mühür (`surum_dondur.py`) sha künyesi git HEAD'e bağlı; 17 Eyl'de basılacak; bugün `DONDURULMADI`.

**H11. Jetson'daki YKS_IP yanlışsa?** — Komut alıcı tüm komutları sessizce reddeder; teşhis journalctl; DHCP rezervasyonu.

**H12. Pixhawk PX4 ile geldi, ne yaptınız?** — ArduCopter flash yordamı hiçbir belgede yoktu (D-424); yazıldı, 4.5.7 indirici sürümü sabitler.

## I. Süreç ve kalite (11, 12)

**I1. Yazılımı kim yazdı?** — Büyük ölçüde yapay zekâ ajanları, yazılı anayasa altında; mimar denetler; yazan onaylayamaz; kararlar (model terfisi, eşik, donanım) insanın.

**I2. Aynı model kendini nasıl denetler?** — Denetlemez: "iki tarafın anlaşması kanıt değildir, hakem ölçüm"; ön kayıt, mutasyon, çürütücü.

**I3. En büyük hatanız?** — Kamera aynalama (D-349); ölçüm yolu ≠ üretim yolu; genel kapıya üretim kolu.

**I4. Ölçüm aracınız yanıldı mı?** — Evet: grep kapısı hep 0 (D-15), kabul denetçisi None=düştü (D-180), mutasyon CRLF (D-370), FP16 half yok sayıldı (D-375); hepsi kural doğurdu.

**I5. Kusur defteri?** — 441 D-kaydı, yalnız eklenir, 80'i düzeltme/çürütme; "kendi hatam" 5.

**I6. İtiraz sistemi?** — 5 maddeli, "yanılıyorsam beni çürütecek ölçüm" zorunlu; ilk kullanım D-200 bir GPU gecesi kurtardı; Codex-2'nin itirazı ölçüm zemininin otopark olduğunu buldu.

**I7. Kesintilerde iş kaybı?** — Oldu (bayat kilit T14; 25+ ajan oturum limiti; 6 saat baştan yapılan görev D-33) → HANDOFF, DEVAM, otorite depo.

**I8. Kaç commit, kim?** — 606; Emir-Gemici 577, trs-1342 27; AI atfı yok (madde 17).

**I9. Neden "kutu açılmamış donanım" dört kez?** — microSD, PX4, künye, Orin Nano (+ motor); kural: ilk komut künyeyi ölçer, belge sonra.

**I10. TASK_QUEUE'de açık kritikler?** — T79, T199, T47, T149, T211.

## J. FDR ve izlenebilirlik (13)

**J1. Gereksinimlerin yüzde kaçı karşılandı?** — 45 satır: 32 KANITLI (%71), 4 kod-var-test-yok, 2 ÖLÇÜLEMEDİ, 7 insan-donanım; "%71 kanıtlı ≠ sahada çalıştı".

**J2. Açık gereksinimler?** — A1–A13 (A10 kapandı); yedisinin tarihi yok ("tarih uydurmadık").

**J3. Doğrulama yöntemleri?** — 66 atama: test 39, gözle 11, sim 7, hesap 5, analiz 4.

**J4. Bölüm 3.1/3.2 neden boş?** — Sabit kanat uçuş bilimleri ve yapısal analiz tasarım ekibinin işi; CAD/analiz artefaktı depoda yok; BEYAN GEREKLİ.

**J5. Bütçe?** — Depoda parasal kayıt yok; BOM var, fiyat yok; İKA/mancınık BOM'u yok.

**J6. Üretim değişiklikleri gerekçeli mi?** — Kol reçete farkı gerekçesiz (kendi işaretimiz: SGGS riski).

**J7. Simülasyon videosu?** — Yok; ÖLÇÜLEMEDİ.

**J8. Rapordaki sayılar güncel mi?** — Tarihli zincir; Bölüm 1 yeniden üretilecek; 7 bayat paragraf biliniyor.

**J9. Kim ne yapıyor?** — Rol bazlı R1–R8; isim yasağı; R2/R5 uçuş anı çakışması için ikinci kişi bekleniyor.

**J10. DDR'den FDR'ye ne değişti?** — Orin NX→Orin Nano, 6X→6C, M10→M9N, Crossfire→FS-i6, Arducam→RPi HQ, X2216×2→quad motor, YOLOv8n/NCNN→v8m/PyTorch; 26 BOM kaleminin 22'sinde değişiklik.

## K. Saha-hakemi anlık soruları (prova/uçuş sırasında)

**K1. "Ekranda ne görüyorum?"** — Harita + rota polyline, şerit numarası, güven, tespit yaşı, model künyesi (sha), düğüm tazeliği, ret sebebi kırmızı bant, kamera RAW.

**K2. "Bu tespit canlı mı?"** — Tespit yaşı ≤ 5 s ve `karar_yas` alanı geldiyse; bayat ise onay düğmesi kapalı.

**K3. "İKA'ya ulaştı mı?"** — İKA'nın rota ACK kopyası ekranda; 2/2 onay ancak o zaman açılır (FDA'da İKA yok, dayanak YKS canlı görüntü + hakem).

**K4. "İHA indi mi?"** — Pixhawk kanıtı: ON_GROUND + irtifa < 1 m, üç ardışık; ekranda `IHA_INIS_KANITI`; insan düğmesi kilit açmaz.

**K5. "Kayıt nerede?"** — `results/prova/<zaman>_<pid>/hakem_log.jsonl`, fsync'li; oturum künyesi ilk satırda.

**K6. "Rota yok diyor, bozuk mu?"** — Hayır, fail-closed; sebep kodu ekranda (OLCEK_YOK ise irtifa telemetrisi bayat; MASKE_YOK ise model görmedi; …).

**K7. "Sol mu sağ mı?"** — road 1 = sol, 2 = orta, 3 = sağ, içerik kutusunun üçte birleri; aynalama D-349'da kaldırıldı, nöbetçi test var.

**K8. "Kumanda koparsa?"** — Şablon RTL; 6 Eyl'de failsafe düştü, kumandada düzeltme yapılmadan uçulmaz.

**K9. "Süre?"** — YKS kronometreleri: hazırlık 15:00, İHA 15:00 (FDA 10:00), İKA 10:00; KALKIŞ damgasıyla başlar, iniş kanıtıyla biter.

**K10. "Model hangisi?"** — v36, sha ilk 8 hanesi ekranda; registry'den; uyuşmazsa yüklenmez.

## L. Tuzak sorular (17 ile birlikte çalış)

**L1. "Sahada çalışıyor mu?"** · **L2. "Doğruluğunuz yüzde kaç?"** · **L3. "Failsafe test edildi mi?"** · **L4. "Menzil?"** · **L5. "İKA?"** · **L6. "Simülasyon videosu?"** ·
**L7. "Bütçe?"** · **L8. "Neden uçmadınız?"** · **L9. "Modeliniz kapınızı geçmedi mi?"** · **L10. "Bu kodu yapay zekâ mı yazdı?"** — cevaplar 17 §3.

---

## Çalışma yöntemi
1. Her başlıktan 3 soruyu kapalı kitap cevapla; cevabı dosyayla karşılaştır.
2. Her cevaba **bir sayı + bir kanıt yolu** ekleyebiliyor musun? Ekleyemiyorsan o dosyaya dön.
3. "Bilmiyoruz" cevaplarını (17) yüksek sesle prova et; en zor kısım budur.
4. Bir arkadaşına L1–L10'u sordur; 30 saniyeyi aşma.
