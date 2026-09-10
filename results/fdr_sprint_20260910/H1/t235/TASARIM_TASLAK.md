# T235 — Rota dünya çerçevesi tasarımı (taslak)

> Bu bir tasarımcı taslağıdır; karar mimarındır. Kanıtın tamamı **SENTETİK** (MuJoCo), saha ölçümü yok. Depoda hiçbir dosyayı değiştirmedim.
>
> Tek yeni hesap betiği `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\fda_etiket_hesap.py`, çıktısı yanındaki `fda_etiket_hesap_cikti.txt`.
>
> Her sayının yanında etiketi var: **ÖLÇÜLDÜ**, **HESAP** ya da **TAHMİN**. Analiz A, B ve C'den alınan sayılar öyle anılıyor; `dosya:satır` atıflarını kendim yeniden okudum.

---

## 0. Karar özeti

1. **İki risk de kod hatası değil, sözleşmenin sonucu.**
   - (a) `road` rotanın karenin hangi üçte birinde olduğundan okunuyor: `karar_sozlesmesi.py:42-98`, `CONTRACTS.md:588-592`.
   - (b) `ref_xy` her zaman [0,0]; CONTRACTS "sahada dünya çerçevesi yoktur" diyor ve İKA rotayı yalnız öteleyerek oturtuyor: `CONTRACTS.md:185-188, :1048`, `iha_sender.py:271-298`, `ika_nav.py:203`.
2. **Takvim riskleri ayırıyor (yeni olgu).** Şartname takvimi `sartname_metin.txt:336-379`:
   - FDR teslimi 21.09.2026.
   - Final aşaması ve "Drone ile Görev Test Uçuşu" (FDA) 30.09–03.10.2026. FDA çoklu rotorla uçuluyor, alan 20×20 m, **İKA yok** (`:726-745`, `CONTRACTS.md` §6.7).
   - İKA'lı ana görevin yarışması **Ağustos–Eylül 2027**; uçuş testleri 21.05.2027.
   - Sonuç: (b) 2026'da sahada hiç sınanmıyor. (a) ise FDA puanını doğrudan etkiliyor; yanlış güzergâh tespiti 0 puan (`:742-745`).
3. **FDA'da kare-göreli etiket, kare alana tam ortalansa bile bozuk (HESAP, `fda_etiket_hesap_cikti.txt`).**
   - 32 m'de HQ 6 mm'nin karesi 33,5 m genişlikte; orta üçte-bir |x| < 5,59 m.
   - Yollar 5 m aralıklıysa üçü de "2" etiketi alır. Alanın 20 m genişliğine göre alınan üçte-birler 1/2/3 verir.
   - FDA'da yol aralığı bilinmiyor (TAHMİN).
4. **Kelime çakışması.** Şartname güzergâhları zorluğa göre "Kolay / Orta / Zor" diye adlandırıyor (`:830-844`). YKS ise konum etiketi olarak "2·ORTA" basıyor (`yks_gui.py:1357-1359`, `ROAD_LABEL`). Hakemin bunu "orta zorluktaki yol" diye okuması mümkün (TAHMİN; kelimenin aynı olduğu olgu).
5. **Dünya çerçeveli bir zincir zaten var ve ölçüldü: mozaik.**
   - Rotayı KB'den başlatıyor (`iha_haritala.py:370-371`, `:417`).
   - OPEN_ROUTE yayınladığı 9 koşumun 9'unda İKA HB'ye temassız vardı (README_T214A §4). Yanlış etiketi 0 (§1).
   - Darboğazı çerçeve değil, karar oranı: K3 6/15, düşüşün tamamı KAPALI_DAR / BELIRSIZ.
   - Uyarı: bu simde poz ve KB **yer gerçeğinden** geliyor; üretimde ikisi de yok.
6. **Öneri, aşamalı:**
   - **Aşama 0 (FDA için, en geç 25 Eylül):**
     - A3: hakemin birincil kanıtı görüntü olur; YKS'deki etiket nitelenir ve şematik şeritten ayrılır.
     - A1: alan-göreli etiket; bayrakla açılır, varsayılan kapalı (davranış bayt-eş).
     - FDA uçuş planına yaw kilidi.
   - **Aşama 1 (Ekim–Aralık 2026):** poz zinciri ve KBH çerçevesi sözleşmesi.
   - **Aşama 2 (Ocak–Nisan 2027):** B2 (KBH mozaik kararı) ile B3 (çapraz geçiş karar bacağı) aynı gürültü modeliyle simde, ön kayıtlı bir yarışta karşılaştırılır.
   - **B1 (tek kare + bağlantı bacağı) tek başına reddedilir** (madde 15).
7. **FDR'ye ne yazılır:** bugünkü DÜŞTÜ sonuçları, kök nedeni (sözleşme) ve planlanan düzeltme. Karşı-olgu sayıları "HESAP, ölçüm değil" etiketiyle girer. Aşama 0 kapıları 21 Eylül'den önce ölçülürse FDR'ye yalnız o ölçüm yazılır.

---

## 1. Olgular (kaynaklı)

| olgu | değer | kaynak |
|---|---|---|
| K3, üretim kare-bazlı (kerteriz beslemesi) | **1/15 DÜŞTÜ**. OPEN_ROUTE yayınlanan kare 8/585. Rota dünyada açık yolu izliyor 8/8; etiket dünya yoluyla eşleşiyor **3/8** | `results/fdr_sprint_20260910/H1/README_T214A.md` §2 (ÖLÇÜLDÜ) |
| kosum_tur3'teki 20 OPEN_ROUTE karesi | Etiket = dünya yolu 6/20. 14 uyuşmazlığın 14'ü kare kaymasından. HTAB'a ortalanmış kare 20/20 | Analiz C §1 (ÖLÇÜLDÜ + yeniden üretim, geri dönüş hatası 0,000 m) |
| K5, üretim | **0/15**. Sürülen 12 koşumun 12'si temasla bitti. Rota başlangıcı–KB mesafesi: min 6,9 · medyan **17,84** · maks 20,19 m | README_T214A §4 (ÖLÇÜLDÜ) |
| KB ile HB aynı karede | **0/225** tarama karesi | README §2 (ÖLÇÜLDÜ). Nedeni geometri: iki kare merkezi arasında ancak 1,6 m'lik bir y penceresi var (Analiz C §2) |
| Kaymanın bileşenleri | Δy medyan 6,53 m: bant 3,65 m, artı KB'nin kare altında kalan 2,9–5,5 m. Δx medyan −14,3 m: açık yolun KB'den ayrışması | Analiz C §2 |
| Mozaik zinciri (GT poz, GT KB) | K3 6/15, yanlış etiket 0. K5 model 9/45; OPEN_ROUTE 9 → HB'de 9, temas 0 | README §1, §4 (ÖLÇÜLDÜ) |
| Karşı-olgu | Etiket dünya çerçevesinde okunsaydı: 8/8 ve 20/20; harita düzeyinde 1/15 → **5/15** (yine düşer). Bağlantı bacağı: temas öngörüsü 0/12, HB 10/12 | Analiz C §3 (**HESAP**, yalnız statik OBB) |
| Sim iyimser | ref = gerçek KB (`gorev_kosumu.py:312-313`). Kareler kuzey-yukarı döndürülüyor (`sim_karar_toplayici.py:172-184`). FOV 74,5°, gerçek kamera ~55° (A9'da 12 Eylül'de ölçülecek) | kod |
| Hedef tohumu HB'ye bağlı | HB bulunmazsa `HEDEF_YOK` ile ret | `rpi_inference.py:1684-1699` |
| Eksen parametresi bağlı değil | `rota_ekseni_derece` tanımlı ve korumalı (`rpi_inference.py:1356-1480`), ama `run_camera` bu parametreyi geçmiyor | `rpi_inference.py:1356`, Analiz A §1.1 |

---

## 2. Karar anında elimizdeki bilgi

| bilgi | bugün | nereden gelir | hangi seçenek ister |
|---|---|---|---|
| Bağıl irtifa | VAR, yalnız mpp hesabına giriyor | `inis_kaniti` | hepsi |
| lat/lon, yaw (`hdg`) | VAR, ama yalnız HEARTBEAT'e gidiyor | `inis_kaniti.py:291-313` | A1, B2, B3 |
| Kare yakalama zaman damgası | **YOK** (`protocol.py:82` yayın anını yazıyor) | köprü ve `run_camera` | B2, B3 (hover'da gerekmez) |
| Roll/pitch (ATTITUDE) | **YOK** | `inis_kaniti.py:24` listesinde yok; akış isteğinde yok (`iha_inis_yayinci.py:90-99`) | B2, B3; A1 için kapı olarak |
| Kamera HFOV | beyan; A9 ölçümü 12 Eylül'de | `ATOLYE_TEST_GUNU_20260912.md:138-146` | hepsi |
| Kameranın montaj yaw'ı (görüntü-yukarı ↔ burun) | **YOK**, 12 Eylül listesinde de yok | — (insan ölçümü) | A1, B2, B3 |
| KB konumu | **YOK** | beyan ya da görüntüde tespit | B2, B3 |
| Alan merkezi, kerteriz β, alan genişliği W | **YOK**. `UB_REFERANS` yalnız İHA-UB köşesi ve yalnız heartbeat için (`jetson_baslat.sh:101,226`) | CLI ve başlatıcı | A1, B3 |
| İKA konum çerçevesi | tanımsız; donanım yok (`ika_surucu.py:186-206`). DDR tasarımında enkoder, M8N, pusula, MPU6050 var; pusula ±5° testi planlı ama yapılmadı (`FDR/sekiller/ika_baglanti_kaynaklar.md:33-37`) | 2027 | B2, B3 |

---

## 3. Ortak tanım: KBH çerçevesi (önerilen sözleşme)

- **Çerçeve:**
  - Orijin: KB merkezi (FDA'da Başlangıç Alanı merkezi).
  - **+y:** KB'den HB'ye yatay doğrultu (FDA'da Başlangıç'tan Hedef'e).
  - **+x:** HB'ye bakan gözlemcinin sağı.
  - Birim metre; zemin düz varsayılır.
- **Neden bu çerçeve:**
  - İki fiziksel işaretle tanımlı, pusula ya da mutlak GPS doğruluğu gerektirmiyor.
  - İKA'yı KB'ye takım yerleştiriyor (şartname `:940-942`). HB'ye bakacak şekilde konursa İKA'nın gövde çerçevesi başlangıç anında KBH'nin kendisi olur. Dönmeyi İHA yapar; CONTRACTS §3.2'deki "İKA'da dönme yoktur" kuralı korunur.
  - İki ayrı pusulanın göreli hatasından kaçınılır: 5° hata 45 m'de 45·tan5° = **3,9 m** yanal kaymaya denk (HESAP).
- **Etiket (KBH):**
  - Rota gövdesi piksellerinin KBH x değerlerine bakılır, alan genişliği W'ya göre bölünür: x < −W/6 → 1, |x| ≤ W/6 → 2, x > W/6 → 3.
  - Karar, `rota_serit_karari`'ndaki gibi çoğunlukla verilir.
  - W beyan edilir: HTAB 50, FDA 20. Değerler `karar_sozlesmesi` sabiti ve CONTRACTS alanı olur; kodda çıplak sayı yazılmaz (madde 16).
  - Anlamı: "sol / orta / sağ, KB'den HB'ye bakan gözlemciye göre". Şartname böyle bir tanım vermiyor; bu proje sözleşmesidir.
  - Sim arenasında yollar x = −16 / 0 / +16'da (`arena.py:36`), sınırlar ±8,33 m'de; yani üç yol ayrışır.
- **Protokol alanları (isteğe bağlı; yoksa bugünkü anlam geçerli):**
  - `road_cerceve`: "KARE" ya da "KBH".
  - `wp_cerceve`: "KAMERA" ya da "KBH".
  - İKA, `wp_cerceve` beklediğinden farklıysa rotayı reddeder (fail-closed).

---

## 4. Seçenekler — (a) etiket

### A1 — Alan-göreli etiket, tek kare, "hafif poz izdüşümü"

- **Ne yapar:**
  - Her karede şu hesaplanır: İHA'nın ENU konumu → KBH, artı R(ψ)·(piksel ofseti · mpp). Burada ψ = hdg + montaj yaw.
  - Etiket KBH üçte-birlerinden okunur.
  - Girdi eksik ya da bayatsa `road_cerceve = "KARE"` gönderilir, yani bugünkü değer. OPEN_ROUTE engellenmez, çünkü etiket sürüşe hiç girmiyor (`ika_nav.py:149-160`; D-166).
- **Gereken bilgi:**
  - lat/lon ve hdg: VAR.
  - Alan merkezi, β, W: YOK; CLI ve `jetson_baslat` ile verilir.
  - Montaj yaw: YOK; insan ölçer.
  - Kare zamanı: FDA hover'ında önemsiz.
  - Ana görevde zaman kayması uçuş yönünde (y) hata üretir, etiket x'ten okunur. Bacaklar KB→HB eksenine paralel olduğu sürece etiket bu hatadan etkilenmez (HESAP; sim bacakları kuzey-güney yönünde).
- **Değişen dosyalar ve sözleşmeler:**
  - `codes/karar_sozlesmesi.py`: saf fonksiyonlar `enlem_boylam_enu`, `kbh_donustur`, `kbh_serit_karari`; W sabitleri.
  - `codes/rpi_inference.py`: `run_camera` telemetri örneğini karara bağlar; yeni CLI argümanları `--alan-merkezi LAT,LON`, `--alan-kerteriz DEG`, `--alan-genislik M`, `--kamera-montaj-yaw DEG`.
  - `comms/protocol.py` ve `comms/iha_sender.py`: `road_cerceve` alanı.
  - `comms/yks_gui.py`.
  - `jetson_paket/` aynası ve `jetson_baslat.sh`.
  - CONTRACTS §6.2 (`road` tanımı ve `road_cerceve`), §6.5 tablo satırı.
- **Anayasa:** yalnız etiket değişiyor, serbest alana dokunulmuyor (madde 15 açısından nötr). Yalnız NumPy ve math. Bayrak verilmezse davranış bayt-eş (`rota_ekseni_derece` kalıbıyla aynı).
- **Risk:**
  - GPS 1,5–2,5 m ve yaw 3–5° hata (TAHMİN), FDA'daki ±3,33 m sınıra karşı.
  - Hover eğimi 2–3°: 32 m'de 1,1–1,7 m kayma (HESAP).
  - Montaj yaw'ı ters işaretle girilirse etiket sistematik olarak ters çıkar (mutasyon hedefi).
  - FDA'da yol aralığı bilinmiyor.
- **Büyüklük ve takvim:** S–M, 2–3 amele günü artı çürütücü. 21 Eylül'den önce ölçülebilir. FDA'da açılıp açılmayacağına mimar karar verir.
- **Simde ölçüm:** render gerekmez; T214-A kareleri ve `poses` yeterli. Beklenen kapılar T235-K1/K2/K3 (TAHMİN: 28/28 geçer).

### A2 — KBH mozaik etiketi

Etiket, mozaik rotasından KBH çerçevesinde okunur; B2'nin yan ürünüdür. Simde ÖLÇÜLDÜ: mozaik zincirinin yanlış etiketi 0, doğru 6/6. Tam B2 gerektirdiği için 2027 işi.

### A3 — Hakemin birincil kanıtı görüntü; YKS etiketi nitelenir

- **Görüntü tarafı:** T227'nin Jetson işaretli karesi (MK15 HDMI) ve T226'nın aynı ekranı hakemin birincil kanıtı olur. Hakem rotayı gerçek görüntünün üzerinde çizili görür.
- **YKS tarafı:** `road_cerceve ≠ "KBH"` olduğu sürece:
  - `SERIT_CIZIM_TABLOSU` (`yks_gui.py:102-106`) yeşil/kırmızı boyanmaz.
  - Rota şerit girişinden çizilmez (`rota_gosterim_geometrisi`, `:212-236`).
  - Onların yerine bir "kare paneli" çizilir: rota görüntü eksenlerinde, yanında "KAREYE GÖRE KONUM" niteleyicisi.
  - Metin çıplak "ORTA" olmaz; şartnamenin Kolay/Orta/Zor adlarıyla karışmayacak bir biçim kullanılır.
- **Onay kapısı:** anlamı değişmez, yalnız ankorun kaynağı değişir (bugün `:1614-1615` şerit tablosundan türüyor). Bu güvenlikle ilgili bir değişiklik; mimar onayı gerekli.
- **Değişen dosyalar:** `comms/yks_gui.py`, CONTRACTS §6.2 ve §6.8, `tests/test_yks_*`.
- **Anayasa ve risk:** yalnız görüntüleme, madde 15 açısından nötr. T226-D ile aynı dosyaya dokunduğu için sıralama gerekiyor.
- **Büyüklük ve takvim:** S; FDA'ya yetişir.
- **Ölçüm:** birim test ve mutasyon (T235-K5).

---

## 5. Seçenekler — (b) rota ile KB arasındaki kayma

### B1 — Tek kare + KBH izdüşümü + bağlantı bacağı → **REDDEDİLİR (yalnız bileşen olarak kalır)**

- **Ne yapar:** `ref_xy` = KB'den rota başlangıcına vektör (KBH), waypoint'ler KBH'de; İKA KB'den ref noktasına düz gider.
- **Neden reddediliyor:**
  - KB, rota başlangıcının 2,9–5,5 m **altında ve kare dışında** (Analiz C §2). Bu yüzden bacak, hiçbir karede doğrulanmamış bir alandan geçer; bu serbest alanı büyütmek demek (madde 15).
  - `ika_nav.py:149-160` "İKA doğrulanmamış bir referans→rota segmenti EKLEMEZ" diyor; `iha_haritala.py:417` de aynı ilkeyi yazıyor.
  - 0/12'lik temas öngörüsü GT poz ve statik OBB ile yapılmış bir HESAP.
  - KB'nin göründüğü karelerden (105) tohumlamak da HB'ye ulaşmaz (0/225). Bu yol ister istemez mozaiğe, yani B2'ye döner.
- **Hata bütçesi (TAHMİN):**

  | kaynak | hata |
  |---|---|
  | İHA GPS | 1,5–2,5 m |
  | KB beyanı (başka alıcı, başka zaman) | 1–5 m |
  | Kare–poz zaman artığı (10 m/s × 0,1–0,7 s) | 1–7 m |
  | Roll 5° @ 30 m | 2,6 m |
  | Yaw 3° @ 20 m | 1,0 m |

  Toplam birkaç metre; koridor payından (sim 1,45 m; `R_GEREKLI` 1,10 m) çok büyük.
- **Kalan değeri:** poz ve izdüşüm modülü A1, B2 ve B3'ün ortak temeli.

### B2 — KBH mozaik kararı (mozaik üretime taşınır)

- **Ne yapar:**
  - Tarama kareleri, kare anındaki pozla (GPS + hdg + ATTITUDE) KBH mozaiğine dizilir.
  - İsteğe bağlı görüntü tabanlı ince hizalama: `cv2.findTransformECC` ya da ORB + RANSAC.
  - Tohum KB'dir: 2a'da beyan edilen konumun izdüşümü, 2b'de görüntüde tespit (ölçüme bağlı).
  - Hedef HB tespitidir.
  - `analyze_path` mozaik üzerinde koşar; `rota_ekseni_derece` mozaikteki KB→HB yönüdür.
  - OPEN_ROUTE: waypoint'ler KBH'de, `ref = [0,0]`. Rota KB'den başladığı için **ika_nav sözleşmesi değişmez**: ilk nokta [0,0], tolerans ≤ 0,15 m. `wp_cerceve = "KBH"`.
  - İKA KB'ye HB'ye bakacak şekilde konur.
- **Gereken bilgi:** ATTITUDE, kare zamanı, montaj yaw, KB, İKA odometrisi (donanım 2027).
- **Değişen dosyalar ve sözleşmeler:**
  - Yeni `codes/mozaik_karar.py` ve `codes/yer_izdusumu.py`. `iha_haritala`'nın mantığı üretime taşınır; sim dosyası üretimde "sahip" sayılamaz (`saha_kuru_kosu.py:683-685`, §11.1/1).
  - `comms/inis_kaniti.py`: ATTITUDE, zaman damgalı halka tampon, enterpolasyon.
  - `comms/iha_inis_yayinci.py`: akış isteği.
  - `scripts/kamera_koprusu.py`: yakalama damgası.
  - `rpi_inference.py`: `--mozaik` kipi.
  - `protocol.py` / `iha_sender.py`: `wp_cerceve`.
  - `ika_nav.py`: `wp_cerceve` kabulü.
  - `yks_gui.py`: gerçek KBH haritası.
  - CONTRACTS: §3.2, §6.2, §6.5 (`:1048`'deki "sahada dünya çerçevesi yoktur" cümlesi değişir) ve yeni **§3.3 KBH**.
- **Anayasa:**
  - Mozaik dikişi serbest alanı büyütmemeli: bir piksel yalnız "onu kaplayan tüm karelerde serbest" ise serbest sayılır (AND). Hangi kuralın kullanılacağı ön kayıtta seçilir; `son_yazar` yalnız TEŞHİS olarak koşar.
  - Alanın dışı engel sayılır; bu bir çıkarmadır, madde 15'e uygun.
  - Yalnız OpenCV, NumPy ve heapq.
- **Kanıt:** 9/9 koşullu başarı (GT poz, SENTETİK). Gürültülü pozla **ÖLÇÜLMEDİ**.
- **Risk:**
  - Yalnız GPS'le yapılan kayıtta bacaklar arasında 1–3 m kayma olabilir; dikişlerde koridor kopar, KAPALI_DAR artar (TAHMİN).
  - Jetson'da bellek ve süre.
  - KB tespiti yanlış pozitif verebilir; D-295'teki kırmızı otomobil emsali.
  - Karar oranını K-A sınırlıyor (6/15); T235 bunu çözmez.
- **Büyüklük ve takvim:** L; 4–6 görev, 3–5 hafta. 2027'nin ilk çeyreği.

### B3 — Çapraz geçiş karar bacağı (KB ve HB tek karede)

- **Ne yapar:**
  - Beyan edilen kerterizle KB–HB eksenine **dik** tek bir düz bacak uçulur; eksen görüntünün uzun (yatay) kenarına düşer.
  - `rota_ekseni_derece = ±90`.
  - KB tohumu izdüşümle bulunur; bant şansına kalmaz.
- **Gereken irtifa (Analiz B, uzun eksen):**

  | KB–HB (D) | h ≥ |
  |---|---|
  | 45 m | 43,9–45,1 m |
  | 50 m | 49,1 m |
  | 70,7 m (HTAB köşegeni) | 68,9 m — proje tavanı `FENCE` 50 m'nin üstünde (`FDR/BOLUM_3:789`) |

- **Artısı (HESAP):**
  - KB ile HB'nin aynı karede kaldığı pencere, uçuş yönünde kare yüksekliği kadar: 50 m'de 39,3 − 2 ≈ 37 m. Bu da 3–5 kare eder. Analiz B'deki kısa-eksen penceresi en çok 6,3 m idi.
  - GSD 9,2–10,2 cm/px (512); kanıt bandına (7,8–8,2) daha yakın.
  - Mozaik gerekmiyor.
- **Kısıtlar:**
  - Eksen boyunca pay yaklaşık ±3 m (h = 50, D = 45).
  - Roll 5° @ 50 m = 4,4 m kayma, bu payı aşar; ATTITUDE kapısı şart.
  - Rüzgâr sürüklenmesi (örneğin 5 m/s yan rüzgârda 15 m/s hava hızı → ~19°) pencereyi ~23 m'ye düşürür (TAHMİN).
  - D bilinmiyor.
  - KB ve HB koordinatlarının 15 dakikalık hazırlık süresinde beyan edilmesi gerekiyor (insan).
- **Anayasa:** tohum koridorla kesiştirilir (`hb_tohumu` kalıbı, `rpi_inference.py:1060-1068`); serbest alan büyümez.
- **Büyüklük:** M. v36'nın 9–10 cm/px ölçekteki başarımı simde ölçülebilir.

**Seçenek dışı:** kısa eksende irtifayı 58,6–65,6 m'ye çıkarmak. Bu 12–13 cm/px verir ve KB bant penceresi kare aralığından kısa kalır; reddedilir. B3 bunun düzeltilmiş hâli.

---

## 6. Karşılaştırma

| | A1 | A2 | A3 | B1 | B2 | B3 |
|---|---|---|---|---|---|---|
| Neyi çözer | etiket | etiket | hakemin yanılma yolu | kayma | kayma + etiket | kayma + etiket |
| Poz zinciri | hafif (hover) | tam | yok | tam | tam | tam |
| Madde 15 | nötr | uyumlu (AND dikiş) | nötr | **ihlal** | uyumlu | uyumlu |
| İş | S–M | (B2) | S | M | L | M |
| 21 Eylül / FDA 30 Eylül | ✓ / ✓ (bayrakla) | ✗ | ✓ / ✓ | ✗ | ✗ | ✗ |
| Bugünkü kanıt | HESAP 8/8, 20/20 | ÖLÇÜLDÜ 0 yanlış (GT) | — | HESAP | ÖLÇÜLDÜ 9/9 koşullu (GT) | yok |

---

## 7. Öneri ve gerekçe

**Aşamalı birleşim: Aşama 0 (A3 + A1 + FDA yaw kilidi) → Aşama 1 (poz temeli + KBH sözleşmesi) → Aşama 2 (B2 ile B3'ün ön kayıtlı yarışı).**

1. **Takvim:** (a) FDA'yı ilgilendiriyor, (b) 2027'yi. Kıt olan doğrulama kapasitesi FDA'nın tek atışlık testine harcanır.
2. **A3 her durumda gerekli:** etiket sürüşe hiç girmiyor; zarar verebildiği tek yer hakem ekranı. En ucuz ve en kesin kapatma bu.
3. **A1 bayrak arkasında gelir:** FDA geometrisinde kare-göreli tanım merkezlemeyle de düzelmiyor (HESAP). Tek geometrik düzeltme alan-göreli tanım; hover pozu zaman eşlemesi olmadan da yeterli.
4. **FDA uçuş planı:** alan merkezinde `LOITER_TIME` öncesine `MAV_CMD_CONDITION_YAW(β)` eklenir. Bugünkü plan `config/pixhawk/fda_gorev.waypoints` satır 6'da HOME'da bekliyor ve yaw serbest. Montaj yaw'ı 0 ise görüntünün yukarısı Başlangıç'tan Hedef'e bakar; A1 kapalıyken bile görüntü düzgün hizalı olur.
5. **(b) için:**
   - B1, madde 15 ve hata bütçesi yüzünden reddediliyor.
   - B2, ölçülmüş tek dünya çerçeveli zincir.
   - B3 daha küçük ama D'ye ve sabit kanat yatışına bağlı.
   - Aralarında seçimi tartışma değil, aynı gürültü modeliyle yapılan **ön kayıtlı ölçüm** verir. İki modelin anlaşması kanıt sayılmaz (madde 19).
6. **T235 dışında kalan FDA riskleri (mimara; ayrı görev önerisi):**
   - Hedef tohumu HB tespitine bağlı (`rpi_inference.py:1684-1699`). FDA'da "Hedef Alanı"nın nasıl işaretlendiği şartnamede tanımlı değil; kırmızı H yoksa her kare `HEDEF_YOK` verebilir (TAHMİN).
   - 32 m hover'da alt bant (2,0 m) alanın 2,5 m dışına düşüyor; rota alan dışındaki zeminden başlayabilir ya da alanı dolanabilir (HESAP + TAHMİN). A1'in izdüşümüyle "alan dışı = engel" çıkarması bunu kapatabilir; bu da ayrıca ön kayıt ister.

---

## 8. Ön kayıt taslağı

Ölçümden önce `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` dosyasına yazılır.

- **H1-K3 (≥ 12/15) ve H1-K5 (≥ 12/15 harita × 3 tohum) aynen kalır** (`ON_KAYIT.md:43,45,115`).
- T235 kapıları bunlara eklenir; kendi hükümlerini verir ve H1 hükmünü çeviremez.

**Aşama 0 (21 Eylül'den önce):**

| kapı | ölçüm | eşik | beklenti (TAHMİN) |
|---|---|---|---|
| T235-K1 · etiket–dünya eşleşmesi (GT poz, algı sabit) | 8 kerteriz OPEN_ROUTE karesi + 20 kosum_tur3 karesi | **28/28** | geçer |
| T235-K1b · görünür yol–kare çiftleri (74,5°) | 646 çift | ≥ **640/646** | geçer |
| T235-K1n · negatif kontrol | aynı tezgâhta bugünkü tanım | 3/8 ve 411/646 **yeniden üretilmeli**; üretilmezse tezgâh boş sayılır | üretilir |
| T235-K2 · gürültü dayanımı | 28 kare × 200 çekiliş; σ_xy 2,0 m, σ_yaw 5° | her karede ≥ %95 doğru; **28/28 kare** | geçer (sınır ±8,33 m) |
| T235-K3 · FDA geometri tezgâhı (sentetik maske) | yol aralığı {5; 6,67; 8} m × drone ofseti ±3 m × yaw ±5° × h {30, 32} m; HFOV 55,3° | alan-göreli tanım **N/N**; kare-göreli tanım 5 m aralıkta [2,2,2] üretmeli (negatif kontrol) | 5 m aralık + 3 m ofset sınırda (±3,33 m) → **düşebilir**; sonuç olduğu gibi yazılır |
| T235-K4 · bayt-eşlik | bayrak verilmeden 1170 kare (kosu1 karar izi) | fark **0** | geçer |
| T235-K5 · hakem ekranı | `road_cerceve = "KARE"` iken şerit boyanmaz; çıplak "ORTA" yok | test OK; mutasyon yakalanır | geçer |

Mutasyon hedefleri (en az 5, hepsi yakalanmalı):
- montaj yaw işareti
- β işareti
- x ekseninin aynalanması
- W/6 yerine W/3
- bayat telemetriyle KBH yazılması
- KARE çerçeveli rotanın şerit boyaması

**Aşama 2 (2027, simde; ayrı ön kayıt `results/t235_rota_dunya/ON_KAYIT.md`):**

| kapı | eşik | beklenti (TAHMİN) |
|---|---|---|
| T235-K6 · rota başlangıcı ↔ KB | GT pozla maks ≤ **1,0 m**. G1 gürültüsüyle (σ_xy 1,5 m, σ_yaw 3°, zaman artığı ≤ 0,1 s, roll ≤ 3°) medyan ≤ **1,5 m**, maks ≤ **3,0 m** | bugün medyan 17,84 m |
| T235-K7 · koşullu sürüş (OPEN_ROUTE alan koşumlar) | başarı ≥ **%90** | mozaik GT 9/9; üretim bugün 0/12 |
| T235-K8 · yanlış yol yayını | **0** | — |
| T235-K9 · madde 15 | mozaik serbest ⊆ kaplayan her karenin serbesti; ihlal **0** (15 harita) | — |
| H1-K3 / H1-K5 | aynen | **DÜŞER**: karar oranı K-A'ya bağlı (mozaik GT 6/15) |

**B2 ile B3 arasında seçim kuralı (önceden yazılır):**
- K6–K8'i geçen seçilir.
- İkisi de geçerse işi ve uçuş riski daha düşük olan (B3) seçilir.
- İkisi de düşerse sonuç olduğu gibi yazılır; eşik gevşetilmez.

---

## 9. İş kırılımı (amele görevleri)

| görev | aşama | dosyalar | test / kapı | mutasyon hedefi | büyüklük | bağımlılık |
|---|---|---|---|---|---|---|
| T235-A · YKS niteleyici (A3) | 0 | `comms/yks_gui.py`; CONTRACTS §6.2/§6.8 (mimar yazar) | `tests/test_yks_rota_cercevesi.py`, K5 | KARE rotası şerit boyar; çıplak ORTA | S | T226-D birleştikten sonra |
| T235-B · KBH saf çekirdeği | 0 | `codes/karar_sozlesmesi.py` | `tests/test_t235_kbh_etiket.py` (tur-dönüş, 28 kare, FDA ızgarası) | yaw işareti, x ayna, W/6 | S | — |
| T235-C · A1'in üretime bağlanması | 0 | `rpi_inference.py` (`run_camera` + CLI); `protocol.py`, `iha_sender.py` (`road_cerceve`); `jetson_paket/` aynası; `jetson_baslat.sh` | K4 bayt-eşlik; bayat telemetri → KARE; `test_jetson_comms_paketi` | telemetri yaş kapısının kaldırılması | S–M | T227-D ve T233 birleştikten sonra (aynı dosya) |
| T235-D · Aşama 0 ölçümü | 0 | `simulation/mujoco/t235_etiket_olcum.py` (render yok) → `H1/t235/` | K1, K1b, K1n, K2, K3 | tezgâh boşluğu (K1n) | S | B |
| T235-E · FDA uçuş planı | 0 | `config/pixhawk/fda_gorev.waypoints` (`CONDITION_YAW` 115, bekleme alan merkezinde); `config/pixhawk/README.md`; saha kâğıdı satırı | waypoint ayrıştırma testi | yaw komutunun silinmesi | S | insan: β ve merkez sahada girilir |
| T235-F · poz zinciri | 1 | `comms/inis_kaniti.py` (ATTITUDE, tampon, enterpolasyon); `iha_inis_yayinci.py`; `kamera_koprusu.py` (damga) | sahte MAVLink ile gecikme enjeksiyonu | enterpolasyon yönü | M | — |
| T235-G · yer izdüşümü + kalibrasyon | 1 | `codes/yer_izdusumu.py`; `cv2.calibrateCamera` betiği | sentetik tur-dönüş ≤ 1 cm | roll/pitch işareti | M | F |
| T235-H · CONTRACTS §3.3 KBH, §6.5 değişikliği | 1 | CONTRACTS (**mimar**) | — | — | S | — |
| T235-I · üretim mozaiği | 2 | `codes/mozaik_karar.py` | K9 | dikişte OR'a geçiş | L | F, G, H |
| T235-J · `--mozaik` kipi + `wp_cerceve` | 2 | `rpi_inference.py`, `protocol.py`, `iha_sender.py` | K6 | ref ≠ [0,0] sızması | M | I |
| T235-K · İKA tarafı | 2 | `ika_nav.py` (`wp_cerceve` fail-closed); İKA yerleştirme yordamı | K7 | çerçeve denetiminin kaldırılması | S | J |
| T235-L · B3 uçuş planı + KB tohumu | 2 | görev üreteci (ArduPlane), `rpi_inference` | K6–K8 | tohum–koridor kesişiminin kaldırılması | M | F, G |
| T235-M · gürültü modeli + yarış | 2 | `simulation/mujoco/` | K6–K9 (B2 ile B3) | — | M | I, L |
| T235-N · YKS gerçek KBH haritası | 2 | `yks_gui.py` | test | — | M | J |

- **İnsan girdileri (madde 9 gereği kuyruğa yalnız mimar ekler):**
  1. Montaj yaw'ı ölçümü (görüntünün yukarısı ↔ burun), 12 Eylül A9'un yanına.
  2. FDA'da Başlangıç ve Hedef alanlarının nasıl işaretlendiği (şartname sorusu).
  3. FDA günü β ve alan merkezi koordinatının girilmesi.
- **Belge kaymaları (T234 sınıfı):**
  - `CONTRACTS.md:188` `ika_nav.py:206` diyor; doğrusu 203.
  - `CONTRACTS.md:682` `:178-182` diyor; doğrusu 174–177.
  - `analyze_path` docstring'inin Returns bölümü hâlâ "EN DAR şerit" (T31) diyor; tanım T155'te gövde çoğunluğuna değişti.
  - `rpi_inference.py:1218` ve `comms/ika_receiver.py:11` `road`'u planlama girdisi diye anlatıyor; D-166'ya aykırı.

---

## 10. FDR'de nasıl yazılır (§3.3.3 ve §4.13 için taslak metin; ölçüm değil, plan)

> **Üretim boru hattında rota çerçevesi — ölçülen sonuç, kök neden, planlanan düzeltme.**
>
> MuJoCo simülasyonunda (SENTETİK) üretim kare-bazlı boru hattı H1-K3'te **1/15**, H1-K5'te **0/15** ile ön kayıtlı eşiğin (≥ 12/15) altında kaldı; eşik değiştirilmedi.
>
> Teşhis iki kök nedene işaret ediyor. İkisi de algı hatası değil, rota sözleşmesinin sonucu:
> 1. Yayınlanan yol etiketi, rotanın **kare genişliğinin** hangi üçte birinde olduğundan okunuyor. Tarama bacakları HTAB'a ortalı olmadığı için, OPEN_ROUTE yayınlanan karelerin 8/8'inde rota dünyada açık yolu izlerken etiket dünya yoluyla yalnız **3/8** eşleşti.
> 2. Rota karenin alt bandından başlıyor ve İKA'ya başlangıcı [0,0] olan yerel metre olarak gidiyor; İKA bunu yalnız öteleyerek oturtuyor. İKA-KB ile HB hiçbir tarama karesinde birlikte görülmediği için (**0/225**), rota KB'den medyan **17,84 m** (n = 12; 6,9–20,19 m) kaymış sürüldü ve 12 koşumun 12'si temasla bitti.
>
> Aynı simülasyonda dünya çerçeveli mozaik zinciri, yayınladığı 9 OPEN_ROUTE'un 9'unda İKA'yı HB'ye temassız ulaştırdı ve yanlış etiket üretmedi. Ancak bu zincir poz ve KB konumunu **yer gerçeğinden** alıyor; bu girdiler sahada henüz yok. Darboğazı karar oranı (6/15).
>
> **Planlanan düzeltme (ÖLÇÜLMEDİ):**
> - Rota, KB merkezli ve KB→HB yönlü bir çerçevede (KBH) ifade edilecek.
> - Yol etiketi kareye göre değil, alanın genişliğine göre KBH çerçevesinde okunacak.
> - Rota, KB'den tohumlanan pozlu bir mozaik üzerinde (ya da KB–HB eksenine dik bir karar geçişinde) üretilecek.
> - İKA, KB'ye HB'ye bakacak şekilde yerleştirilecek.
>
> Geometrik karşı-olgu (HESAP, ölçüm değil): etiket dünya çerçevesinde okunsaydı 8/8 karede doğru olurdu, ama harita düzeyinde sonuç 1/15'ten 5/15'e çıkar ve kapı yine düşerdi. Etiket düzeltmesi tek başına yetmez; karar oranı ayrı bir iş kalemi.
>
> Drone ile Görev Test Uçuşunda (30.09–03.10.2026; İKA yok) kareye göreli etiket hakem ekranında dünya şeridi gibi gösterilmeyecek; hakem rotayı işaretli görüntü üzerinde görecek.
>
> Sınır: simülasyon kamerasının FOV'u 74,5°, gerçek kameranınki ~55° (ÖLÇÜLMEDİ). Bu fark sonuçları iyimser tarafa çeker.

Aşama 0 kapıları 21 Eylül'den önce ölçülürse FDR'ye yalnız ölçülen kapı ve sonucu eklenir. "Düzeltildi" ya da "GEÇTİ", ancak ilgili ön kayıtlı kapı gerçekten koşulduktan sonra yazılır.

---

## 11. Açık sorular

- KB–HB mesafesi (D) ve yol aralığı: şartnamede yok. B3'ün uygulanabilirliği ve A1'in FDA payı bunlara bağlı.
- FDA'da hedef alanında kırmızı H var mı? Yoksa üretim her karede `HEDEF_YOK` verir (§7/6).
- Hakem "sol / orta / sağ" mı doğruluyor, yoksa "görüntüdeki güzergâh" mı? Şartname yalnız "tespitin doğruluğu" diyor (`:967-970`, `:1005-1008`).
- İKA donanımı ve yerleştirme yordamı (HB'ye bakış açısının doğruluğu), 2027.

---

## Kaynaklar

- **Kod:**
  - `codes/karar_sozlesmesi.py:13, 42-98, 160-162, 395-429`
  - `codes/rpi_inference.py:972-984, 1060-1068, 1356-1480, 1684-1699`
  - `comms/iha_sender.py:271-298`
  - `comms/protocol.py:54-85`
  - `comms/inis_kaniti.py:24, 291-313`
  - `comms/iha_inis_yayinci.py:90-99`
  - `comms/yks_gui.py:102-106, 212-236, 1320-1383`
  - `simulation/scripts/ika_nav.py:47-48, 149-203`
  - `simulation/scripts/ika_surucu.py:186-206`
  - `simulation/scripts/iha_haritala.py:119-160, 198-207, 370-371, 417`
  - `simulation/scripts/arena.py:27-45`
  - `simulation/mujoco/iha_ucus.py:80-90`
  - `simulation/mujoco/gorev_kosumu.py:312-313`
  - `simulation/mujoco/sim_karar_toplayici.py:172-184`
  - `jetson_paket/jetson_baslat.sh:101, 226`
  - `config/pixhawk/fda_gorev.waypoints`
- **Belge:**
  - `CONTRACTS.md:185-188, 355-365, 440-457, 580-596, 1031-1048`
  - `results/fdr_sprint_20260910/ON_KAYIT.md:31-49, 115`
  - `results/fdr_sprint_20260910/H1/README_T214A.md` §1, §2, §4, §6, §7
  - `REVIEW_LOG.md:30520` (D-449)
  - `TASK_QUEUE.md:9664-9667, 9690`
  - `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:1330-1356`
  - `FDR/sekiller/ika_baglanti_kaynaklar.md:33-37`
  - `ATOLYE_TEST_GUNU_20260912.md:138-146`
- **Şartname** (`results/sartname_bosluk/sartname_metin.txt`): `259-274`, `286-305`, `313-330`, `336-379` (takvim), `726-745` (FDA), `805-807`, `830-844`, `936-944`, `965-972`, `1003-1010`.
- **Analizler ve betikler** (hepsi `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\` altında):
  - `geometri_hesap_cikti.txt` (Analiz B)
  - `analiz_c_sonuc.json`, `etiket_uretim_20kare.csv`, `ankor_uretim_20kare.csv`, `surus_karsi_olgu_12.csv` (Analiz C)
  - `ozet.py` (Analiz A)
  - `fda_etiket_hesap.py`, `fda_etiket_hesap_cikti.txt` (bu taslak)