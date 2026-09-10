**HÜKÜM: DÜZELTMELİ**

Tanı doğru ve kaynaklarına sadık. Sorun şu iki kök nedende: etiket kareye göre okunuyor, `ref_xy` sabit [0,0] ve İKA yalnız öteleme yapıyor. B1'in reddi, B2/B3'ün 2027'ye bırakılması ve H1 eşiklerine dokunulmaması da doğru. Ama Aşama 0'ın, yani FDA'ya yetişmesi gereken kısmın dayandığı üç olgu yanlış ya da eksik. Önerilen yaw kilidi de bugünkü parametreyle büyük olasılıkla etkisiz kalıyor.

## Bulgular (kanıtlı)

### 1. KRİTİK — FDA'da bekleme alan merkezinde değil, son köşede
- `config/pixhawk/fda_gorev.waypoints` satır 6: `19 60 … 0 0 32`, yani LOITER_TIME ve lat/lon 0,0.
- `config/pixhawk/README.md:84` bunu açıkça yazıyor: *"lat/lon 0,0 = bulunduğu yerde"*. `:97` ise 6. satırın koordinatını "isteğe bağlı" sayıyor.
- Sonuç: İHA 5. waypoint'te (GD köşesi) bekliyor. Tasarım §7/4'teki "satır 6'da HOME'da bekliyor" yanlış. Analiz B §4'teki "merkezdeki bekleme noktasında tek kareye sığıyor" da bugünkü plan için yanlış.
- Bugünkü planda alanın merkezine ortalanmış kare **hiç yok**. Köşe merkezli karede (32 m) alanın ancak 16,8 × 12,6 m'lik bir çeyreği görünür.
- T235-E'deki "bekleme alan merkezinde" önerisi doğru, ama isteğe bağlı değil **zorunlu**. Aşama 0'ın en büyük kaldıracı bu.

### 2. KRİTİK — `CONDITION_YAW`'ın yeri büyük olasılıkla yanlış
- Parametre `WP_YAW_BEHAVIOR,2` (`config/pixhawk/mevcut.param:1013`, `arducopter_fda_20260906.param:1013`).
- ArduCopter bir DO/CONDITION komutunu, kendisinden önceki NAV komutu sürerken koşar. Yeni NAV (LOITER_TIME → `wp_start`) başlayınca otomatik yaw, FIXED + `WP_YAW_BEHAVIOR=0` değilse varsayılana döner.
- Yani "LOITER_TIME **öncesine** CONDITION_YAW" 5. köşeye giden bacakta uygulanır, beklemede sıfırlanır.
- Doğrusu: komut LOITER_TIME'dan **sonra** konur ya da `WP_YAW_BEHAVIOR=0` yapılır.
- Bu ArduPilot kaynak bilgisidir, yerelde doğrulanmadı. SITL ya da Mission Planner simülasyonunda ölçülmeden uçuş planına girmemeli.

### 3. §0.3'teki iddia fazla genelleştirilmiş
- "Kare alana tam ortalansa bile bozuk" yargısını tasarımın kendi çıktısı çürütüyor. `fda_etiket_hesap_cikti.txt`'de yol aralığı 6 / 6,67 / 8 m iken kare-göreli sonuç **[1,2,3]**. Bozulma yalnız aralık 5,59 m'nin altındayken var.
- Asıl fark güvenlik payında (HESAP, 32 m, merkezli kare):

  | aralık | kare-göreli yan yol payı | alan-göreli pay |
  |---|---|---|
  | 6,67 m | 6,67 − 5,59 = **1,08 m** | **3,33 m** |
  | 5 m | negatif (etiketler bozuk) | 5 − 3,33 = **1,67 m** |

### 4. Atlanan daha basit seçenek (A0): A1'in ek kazancı küçük
- Hata ayrışımı (HESAP): e_s alan merkezinin ölçüm hatası, e_f uçuştaki GPS hatası, e_c bekleme kontrol hatası olsun.
  - Kare-göreli etiketin sapması: d = e_s − e_f + e_c.
  - A1'in hatası: e_f − e_s, artı yaw, eğim ve gecikme terimleri.
  - Yani A1 yalnız e_c'yi siler (iyi GPS'le merkezde beklerken ~1 m'nin altında) ve merkez dışı köşe karelerini düzeltir.
- **A0** şudur: üçte-bir sınırlarını içerik genişliği yerine içerik merkezinden ±(W/6)/mpp olarak al. Buna merkezde bekleme ve yaw kilidi eklenir.
  - `mpp` zaten var. Poz bağlama, `hdg`, lat/lon ya da kare damgası gerekmez.
  - Beklemede payı A1'le hemen hemen aynı (3,33 m − |e_c|).
- Alan merkezi, β ve W için yeni CLI girdisine gerek yok. Kaptan dört köşeyi zaten giriyor (`README.md:97`); bunlar köşelerden türetilir. Tek yeni insan bilgisi Başlangıç kenarının hangisi olduğu.
- Köşeler İHA'nın **kendi** GPS'iyle alınırsa e_s ile e_f'nin sabit sapması kısmen birbirini götürür.

### 5. İHA pozu kareye bağlı değil (kodda görüldü)
- `run_camera` (`rpi_inference.py:2335-2386`) kareyi `kamera_kareleri`'nden damgasız alıyor. Önce `model.predict`, sonra `kare_olcek_kahini` çağrılıyor; yani irtifa çıkarımdan **sonra** okunuyor.
- `CanliOlcekSaglayici.kare_mpp` (`:358-371`) yalnız `irtifa_m()` okuyor.
- `telemetri_snapshot`, yani lat, lon ve `yon`, yalnız `_telemetri_saglayici` üzerinden HEARTBEAT'e gidiyor (`:2644-2669`).
- Tasarım §2 bunu doğru yazıyor. Ama A1'deki "kare zamanı hover'da önemsiz" cümlesi eksik kalıyor:
  - Karar bekleme anında değil, köşe bacakları dahil **her karede** yayınlanıyor.
  - Köşe bacaklarında hız 3 m/s (`WPNAV_SPEED` 300 cm/s, FDR §2793). Kare başına 770–922 ms'lik süre 2,3–2,8 m kayma eder (HESAP).
  - Tazelik kapısı telemetrinin yaşına bakıyor, kare ile telemetrinin eşleşmesine bakmıyor (`inis_kaniti.py:386-391`). Bu yüzden bayat etiket "taze" diye geçer.
- Gereken: aynı snapshot'taki `hiz` ile bir hız kapısı. Hız eşiğin altındaysa KBH ya da A0 etiketi, üstündeyse KARE.

### 6. A3'ün kare paneli mevcut mesajla çizilemez
- `protocol.open_route` (`:54-85`) yalnız `road`, `label`, `conf`, `ref_xy`, `waypoints`, `seq`, `t` taşıyor.
- Waypoint'ler rotanın ilk pikseline göreli (`iha_sender.py:284-286`). Rotanın kare içindeki konumu (sol / orta / sağ) mesajda **yok**.
- "Rota görüntü eksenlerinde" çizilen bir panel yalnız rotanın biçimini gösterir, kare içindeki yerini gösteremez.
- Bu yüzden A3 yeni bir protokol alanı ister, örneğin rota başlangıcının içerik merkezine göre ofseti. O zaman `protocol.py`, `iha_sender.py` ve `rpi_inference.py`'ye de dokunur. "Yalnız `yks_gui`, S" boyutlaması tutmuyor.
- A3'ün birincil kanıtı T227'ye dayanıyor. T227 bugün RED: FPS kapısı %12,06 ve %6,51 ile %5'i geçti (`TASK_QUEUE.md:9667`). MK15 HDMI zinciri de donanımda doğrulanmadı.

### 7. Kamera kipi riski Aşama 0'da yok
- Köprü varsayılanı 1280×720 (`kamera_koprusu.py:84-85`, "Cumartesi ölçülür").
- Tam genişlikte 16:9 kırpma varsa 32 m'de dikey iz 33,53·9/16 = **18,86 m**, alanın 20 m'sinden kısa.
- T235-E'nin seçtiği yön (görüntünün yukarısı = Başlangıç→Hedef) alanı bu kısa eksene koyar. Hedef kenarı ya da alt bant kareden taşar ve `HEDEF_YOK` riski doğar.
- İki seçenek var:
  - Rota eksenini görüntünün uzun kenarına çevir ve `rota_ekseni_derece`'yi bağla. Parametre var (`:1356`) ama `run_camera` onu geçirmiyor.
  - Ya da h ≥ 36,5–38,5 m uç (`FENCE_ALT_MAX` 50'nin altında).
- Bu seçim 12 Eylül A9/A10 ölçümüne bağlı. K3 tezgâhına en-boy oranı eklenmeli.

### 8. Ön kayıt: eşik gevşetme yok, ama kapılar zayıf
- H1-K3/K5 ≥ 12/15 aynen duruyor (`ON_KAYIT.md:43,45`; `:115` "eşik değişmez"). Gevşetme **yok**.
- **K3 belirsiz:** "drone ofseti ±3 m". Tezgâh yer gerçeği pozuyla koşarsa A1 ofseti tam telafi eder ve N/N sonucu anlamsız olur. Ofset, poz **kestirim** hatası (e_f − e_s, σ ile), yaw ve eğim olarak tanımlanmalı.
- **K3'ün sonucu önceden bağlanmamış:** "FDA'da açılır mı" kararı mimara bırakılmış, ölçüme bağlanmamış.
- **K2 yanlış yerde:** sim geometrisinde, ±8,33 m sınırla koşuluyor. FDA payı ise 1,67–3,33 m. K2 FDA hakkında bilgi vermez.
- **K1 bağımsız kanıt değil:** 28/28, Analiz C'nin aynı geometriyle yaptığı HESAP'ın yeniden koşumu. Uygulama testi sayılmalı.

### 9. Anayasa: ihlal yok
- A1, A0 ve A3 yalnız etiketi ve görüntülemeyi değiştiriyor. B2'nin AND dikişi ve "alan dışı = engel" kuralı çıkarma işlemi.
- B1'in reddi `ika_nav.py:152-153` ve `iha_haritala.py:414-416` ile tutarlı.
- `findTransformECC`, ORB ve `calibrateCamera` OpenCV'de. SciPy ve scikit-image yok.

### 10. Takvim: tasarım kendi dediği gibi yetişmez
- `rpi_inference.py` üç işin ortak dosyası: T227-D (GPU v2 ölçümü bekliyor), T233 ve T235-C. A3 de T226-D'yi bekliyor.
- Kullanıcının kısıtı: "tek insan görevi bu son testtir" (bellek: saha-plani-kisitlari). Tasarım buna karşın üç yeni insan girdisi ekliyor.
- `CONTRACTS.md:438,441` "prova: 21 Eylül Adıyaman" diyor. Tasarımdaki "en geç 25 Eylül" bu tarihi hesaba katmıyor; mimar teyit etmeli.
- 21 Eylül'den önce gerçekçi olanlar:
  - T235-E: merkezde bekleme ve doğru yerde yaw komutu.
  - T235-B: saf çekirdek.
  - YKS'de etiket niteleyicisi, ofset alanı olmadan.
  - FDR metni.
- T235-C'nin, yani poz bağlamanın, tek atışlık gerçek testten 10 gün önce hiç saha testi olmadan uçuş yoluna girmesi yüksek riskli.

### 11. Aritmetiğin yeniden hesabı (hepsi HESAP)
Tutanlar:

| iddia | yeniden hesap |
|---|---|
| 5° @ 45 m | 45·tan5° = 3,94 m |
| hover eğimi 2–3° @ 32 m | 1,12–1,68 m |
| roll 5° @ 30 m / @ 50 m | 2,62 m / 4,37 m |
| yaw 3° @ 20 m | 1,05 m |
| W(32 m), W/6, 20/6 | 33,53 m, 5,59 m, 3,33 m |
| B3 uzun eksen | 47,3/1,0478 = 45,1 · 51,5/1,0478 = 49,15 · 72,2/1,0478 = 68,9 m |
| kısa eksen | 46/0,7853 = 58,6 · 51,5/0,7853 = 65,6 m |
| FDA sığma payı | 2,57 m / 6,77 m |
| alt bant (4:3, 32 m) | 2,01 m |
| KB–HB ortak pencere | 45,61 − 44 = 1,61 m |
| GSD | 9,2 / 10,2 cm/px |

Küçük sapmalar:
- **Rüzgâr penceresi:** sürüklenme açısı asin(5/15) = 19,47°. Pencere 39,27 − 46·sin19,47° − 2 ≈ **21,9 m**; tasarım ~23 m diyor, biraz iyimser.
- **B3 çit payı:** D = 50 m'de h = 49,1 m, çite (50 m) yalnız 0,9 m pay bırakır. Tasarım yalnız 70,7 m'yi çit üstü sayıyor. Not: `arducopter_fda.param:212` FDA helikopterinin parametresi; ArduPlane çiti henüz belirsiz.

### 12. Küçük bulgular
- **§3 KBH gerekçesi fazla iddialı:** İKA'yı HB'ye bakacak şekilde elle koymak, pusula hatasıyla aynı açısal mekanizmayı taşır (5° → 3,9 m). HB molozun ardından görünmeyebilir. Hata ortadan kalkmıyor, insana taşınıyor.
- **"Yeni olgu" değil:** FDA'da İKA olmadığı `CONTRACTS.md` §6.7'de (D-407) zaten kayıtlı.
- **Atıf kayması:** "2·ORTA" metni `yks_gui.py:1354`'te; `:1357-1359` "✕ KAPALI" satırı.
- **FDR taslağı (§10):** "hakem rotayı işaretli görüntü üzerinde görecek" cümlesi olgu kipinde yazılmış. T227 RED olduğu için "planlanan, ÖLÇÜLMEDİ" diye etiketlenmeli (D-444).

### Yeniden okunan ve doğru bulunan kaynaklar
- Şartname: `:336-379`, `:726-745`, `:830-844`, `:940-942`, `:963-972`, `:1001-1010`.
- `karar_sozlesmesi.py:42-98, 160-162`; `CONTRACTS.md:187-188` ve §6.5'teki `ref_xy` satırı.
- `iha_sender.py:271-298`; `inis_kaniti.py:24-27, 291-313`; `iha_inis_yayinci.py:90-99`.
- `rpi_inference.py:1356/1412/1423` (`run_camera` içinde `rota_ekseni_derece` yok), `:1684-1699`.
- README_T214A: 1/15, 3/8, 8/585, 0/225, 17,84; mozaik 9 OPEN_ROUTE → 9 HB'de, temas 0.
- `gorev_kosumu.py:312-313` (ref = KB), `sim_karar_toplayici.py:184` (`rot90`), `ika_nav.py:203`.

## Tasarımda değişmesi gerekenler
1. §7/4 ve Analiz B §4 düzeltilmeli: bugün bekleme 5. köşede. T235-E zorunlu olmalı ve 6. satıra merkez koordinatı (köşelerin ortalaması) yazılmalı.
2. `CONDITION_YAW` LOITER_TIME'ın **arkasına** konmalı ya da `WP_YAW_BEHAVIOR=0` yapılmalı. Kabul kapısı SITL'de ölçülen yaw olmalı. Mutasyon hedefi: komutun LOITER öncesine taşınması.
3. **A0** (merkez referanslı, alan ölçekli üçte-bir; yalnız `mpp` ve W) seçenek olarak eklenmeli ve A1'in önüne konmalı. A1 ancak A0'a karşı ölçülmüş bir kazanç gösterirse gelir. Alan merkezi, β ve W köşe waypoint'lerinden türetilmeli; yeni CLI girdisi eklenmemeli.
4. Hangi etiket kullanılırsa kullanılsın hız kapısı eklenmeli: `hiz` eşiğin üstündeyse `road_cerceve = "KARE"`. Mutasyon hedefi: kapının kaldırılması.
5. A3 için rota başlangıcının içerik merkezine göre ofsetini taşıyan isteğe bağlı bir protokol alanı tanımlanmalı. Dosya listesi ve boyut buna göre düzeltilmeli. T227 düşerse YKS panelinin tek kanıt olacağı yazılmalı.
6. Kamera kipi (4:3 ya da 16:9 kırpma) Aşama 0'a bağlanmalı. 16:9 çıkarsa rota ekseni görüntünün uzun kenarına alınmalı ve `rota_ekseni_derece` CLI'ye bağlanmalı, ya da irtifa 38–40 m yapılmalı. K3 tezgâhına en-boy oranı eklenmeli.
7. Ön kayıt:
   - K3'teki ofset, kestirim hatası (σ_GPS, σ_yaw, eğim) olarak tanımlanmalı. A0, A1 ve kare-göreli aynı çekilişlerle karşılaştırılmalı.
   - **Kural önceden yazılmalı:** FDA'da yalnız K3'ü geçen ve kare-göreliden kötü olmayan etiket açılır; hiçbiri geçmezse KARE kalır ve yalnız A3 uygulanır.
   - K2 FDA geometrisine taşınmalı. K1 "uygulama testi" diye etiketlenmeli.
8. Takvim yeniden kurulmalı:
   - Önce "21 Eylül Adıyaman provası" teyit edilmeli.
   - 21 Eylül'den önceki işler: T235-E, T235-B, A3 niteleyicisi, FDR metni.
   - T235-C (poz bağlama) FDA uçuş yoluna ancak K3 geçer ve bir tezgâh ya da SITL koşusu yapılırsa girmeli.
   - İnsan girdileri kullanıcının "tek insan görevi" kısıtına karşı mimarca yeniden değerlendirilmeli; montaj yaw'ı A9 karesinden türetilebilir mi, bakılmalı.
9. FDR §10 taslağında görüntü ve hakem cümlesi "planlanan, ÖLÇÜLMEDİ" diye etiketlenmeli. B3'e rüzgâr penceresi ~22 m ve çit payı 0,9 m notları eklenmeli.

Depoda hiçbir dosyayı değiştirmedim ve yeni hesap betiği yazmadım. Yukarıdaki hesaplar elle yeniden yapıldı. Yeniden okunan tasarım dosyaları:
- `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\fda_etiket_hesap.py`
- `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\fda_etiket_hesap_cikti.txt`
- `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\etiket_uretim_20kare.csv`
- `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\ek_sayimlar.json`