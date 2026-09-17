# dusus_0253.mp4 — 17 Eylül 2026 02:53 düşüşü, log canlandırması (2. sürüm)

Bu klasördeki her şey `log_video.py` ile üretilir; elle düzenlenmiş kare ya da elle girilmiş log sayısı yoktur. Bu dosya da betik tarafından yazılır. (`denetim/` klasörü betiğin değil, dış denetimin çıktısıdır.)

## Üretim

- Komut: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 O:\navitas\results\ucus_20260917b\video\log_video.py`
- Üretim süresi (veri okuma + işleme + kodlama + doğrulama): **28,1 s**
- Kodlayıcı: **libx264**
- ffprobe: codec **h264** (High), **1920×1080**, r_frame_rate **30/1**, pix_fmt **yuv420p**, kare **1422**, süre **47,400 s**, boyut 5,3 MB
- Yeniden üretim: `O:\navitas-local-train\venv\Scripts\python.exe log_video.py` (bu klasörde); yalnız işaret testleri için `--test-isaret`.

## 2. sürüm: denetim bulguları ve yapılan düzeltmeler

1. **Telemetri durumu:** HUD artık son paketten (202,182 s) hemen sonra ‘KOPTU’ yazmıyor. Son paket ile sıradaki beklenen ATTITUDE (son ATTITUDE 202,182 + periyot 0,25 = 202,432 s) arasında nötr ‘son 202,18 s · bekleniyor’ yazıyor. ‘KOPTU’ ancak bu andan sonra, yani başlangıçtan (202,410 s) sonra görünüyor. GPS'teki zaman aşımı kuralıyla aynı mantık.
2. **Çubuklar ‘ortada’ ifadesi:** ölçüm yalnız roll/pitch/yaw (C1/C2/C4) için geçerli. Gaz ayrı hesaplanıyor: ArduCopter Loiter ölü bandı THR_DZ=100, RC3_DZ=30, RC3_MIN/MAX=1000/2000 ile 0–1000 ölçeğinde 484±100 → bandın üstü **C3 ≥ 1598 µs**. Gaz 187,97–192,77 s bandın üstünde (C3 en çok 1612 µs; CTUN DCRt en çok +38 cm/s). Kalkış başlığı ‘yavaş tırmanışla ~0,5 m askı (olay öncesi +0,68 m)’ oldu. Basamak açıklamaları o andaki gaz durumunu ve DCRt'yi yazıyor. Sonuç kartındaki madde de buna göre düzeltildi.
3. **Olay şeridi çakışması:** etiket satırı seçimi bağlantı çizgilerini de engel sayıyor. Bir etiketin çizgisi alt satırlardaki yazıları kesemez; üst satırlardan inen çizgi de yeni etiketin içinden geçemez. ‘CH6 disarm’ artık ‘Olay …’ etiketini bölmüyor.
4. **3B motor etiketleri:** yerleşim, aday konumları 24 yön × 12 mesafede tarayıp en kısa çizgili ve en az cezalı konumu seçiyor. Sert koşullar: kutu–kutu çakışması yok; hiçbir bağlantı çizgisi başka bir kutudan (ÖN dahil) geçmez; kutular rozet ve dipnot bandına girmez. Yumuşak cezalar: kutunun disk/gövde üstüne binmesi, dıştan içe ters yön, çizginin başka disk üstünden geçmesi. Önce tüm çizgiler, sonra opak kutular çiziliyor.
5. **Yazı boyu:** veri taşıyan yazılar en az 18 px, yardımcı dipnotlar en az 16 px. `maxw` küçültmesi bu sınırların altına inmiyor; sığmayan yazı uyarı üretiyor. Yer açmak için düzen değişti: motor çubukları yatay, grafikler 4 ayrı eksen, HUD iki sütun + çubuk kutuları, şeritte 2 satırlık açıklama.
6. **|a| grafiği:** VibeZ'den ayrıldı; kendi ekseni 0–60 m/s² (66 px), 1 g kesik referans çizgisi ve sağda ‘1 g’ etiketi var. Eksen etiketleri kırpılmıyor, gerçek değerin hizasında yazılıyor.
7–8. **Çıkarım etiketleri:** başlıklar ‘ölçülen olgu (ölçüm) — yorum (çıkarım[+ beyan])’ biçiminde. ‘Başlangıç: ön-sağ köşe düştü (ölçüm: GyrX/GyrY) — itki kaybı (çıkarım)’, ‘GPS ve pusula verisi HAVADA kesildi (ölçüm) — kablo kopması (çıkarım + beyan)’, ‘Titreşim/clip patlaması (ölçüm) — pervaneler birbirine girdi (çıkarım + kullanıcı beyanı)’, ‘Motor dengesizliği basamakla büyüyor (ölçüm) — gövde esniyor (çıkarım)’. Geçmiş satırları da aynı başlıkları taşıyor.
9. **Yerleşim denetimi ifadesi:** eski ‘uyarı 0’ yalnız panel sınırına bakıyordu. Betik artık her karede yazı–yazı, çizgi–yazı, şekil–yazı ve çizgi–etiket kutusu kesişimlerini sayıyor; sonuç aşağıdaki bölümde. Kapsam dışı olanlar orada yazılı.
10. **Şerit imleci:** yalnız eksen bandında çiziliyor (etiket satırlarının altında); yazıları bölmüyor.
11. **İşaret testi kareleri:** çağrı kutularının (AŞAĞI/YUKARI) konumu ve çizgisi önce hesaplanıp 3B etiketlere engel olarak veriliyor. Yaw testinde ayrı ‘BURUN’ çağrısı kaldırıldı; burun, ÖN etiketinin kendisi (‘ÖN = BURUN (yaw +45°)’). Sağ alttaki 2B çizgi şemasının yerine aynı `drone_ciz` fonksiyonu ikinci bir kameradan (pitch: sağdan, roll: arkadan, yaw: yukarıdan) çiziliyor.
12. **Yaw hatası rengi:** mor (M3'e çok yakındı) yerine nötr açık gri (214, 219, 228).

## Bölümler

| Bölüm | Video (s) | Log zamanı (s) | Kare |
|---|---|---|---|
| 1 · Başlık kartı | 0,00–3,00 | — | 90 |
| 2 · Oturum özeti | 3,00–9,00 | — | 180 |
| 3 · Son uçuş (gerçek hız) | 9,00–25,20 | 186,00 → 202,20 | 486 |
| 4 · Olay (ağır çekim ×0,1) | 25,20–37,20 | 202,20 → 203,40 | 360 |
| 5 · Sonrası (gerçek hız) | 37,20–40,40 | 203,40 → 206,60 | 96 |
| 6 · Sonuç kartı | 40,40–47,40 | — | 210 |

Ekran: sol 3B tutum (temsili) ve dipnot bandı; sağ üst motor çubukları (yatay, 1150/1949 çizgili), CCW−CW ve yaw hatası; sağ orta 4 zaman grafiği: motorlar, CCW−CW, VibeZ, |a|. Grafik ekseni 3. ve 5. bölümde 186–207 s, 4. bölümde 202,0–203,4 s; imlecin sağı soluk. Sağ alt HUD ve pilot çubukları (Mode 2). Alt şerit: olay çizgisi, en yeni olayın büyük başlığı, en çok 2 satır ölçüm açıklaması ve önceki olaylar.

## Veri kaynakları

- Log: `O:\navitas\results\ucus_20260917b\2026-09-17 02-50-38.bin` — ArduCopter V4.5.7 (2a3dc4b7), Pixhawk6C. Okunan mesaj sayıları: ATT 1548, RCOU 1547, RCIN 1565, CTUN 1548, BAT 1545, VIBE 3094, IMU 7738, GPS 694, MAG 3090, MODE 11, EV 40, ERR 4, ARM 11, PARM 1042, MSG 25.
- **ATT** Roll/Pitch/Yaw/DesYaw: 3B tutum. Açılar `np.unwrap(period=360)` ile sarmalamadan arındırılıp kareye doğrusal ara değerlenir; yazılan ATT sayıları ara değer değil, son örnektir. Yaw hatası = (DesYaw − Yaw) ±180'e sarılır.
- **RCOU** C9..C12: M1=C11, M2=C10, M3=C12, M4=C9; `SERVO9..12_FUNCTION` (36, 34, 33, 35; 33+k−1 = Motor k) ile doğrulandı. Çubuk/disk rengi son örnektir (örnekle-tut). CCW−CW = (M1+M2) − (M3+M4); ‘1 s ort.’ = son 10 örneğin (1 s) ortalaması.
- PWM taban/tavan parametrelerden: MOT_PWM_MIN + MOT_SPIN_MIN/MAX × aralık → **1150 / 1949 µs**.
- **RCIN** C1..C6: pilot çubukları (Mode 2; normalizasyon RCx_MIN/TRIM/MAX parametrelerinden) ve CH5/CH6 anahtarları. Roll/pitch/yaw ‘ortada’ = |Cx − RCx_TRIM| ≤ RCx_DZ. Gaz ölü bandı ArduCopter `get_pilot_desired_climb_rate()` ile hesaplanır: `RC_Channel::pwm_to_range_dz()` → control_in = ⌊1000·(C3 − (RC3_MIN+RC3_DZ)) / (RC3_MAX − (RC3_MIN+RC3_DZ))⌋; bant = `get_control_mid()` ± THR_DZ. Doğrulama olarak CTUN **DCRt** (istenen tırmanma hızı) okunur.
- **CTUN** Alt: yerden yükseklik = Alt − kalkış öncesi ortalama (186,30–188,25 s, 19 örnek, 1,42 m). Pencere EV 28 zamanından türetilir: [kalkış − 2,00; kalkış − 0,05]. **DCRt**: gaz isteği doğrulaması.
- **BAT** Volt/Curr, **VIBE** (IMU 0) VibeZ/Clip, **IMU** (I=0) Gyr/Acc (|a| = √(Ax²+Ay²+Az²)), **GPS** NSats/Status, **MAG** (I=0, harici pusula; COMPASS_EXTERNAL=1) `S` son güncelleme alanı (HUD'da ‘Pusula’), **MODE**, **EV**, **ERR**, **ARM**.
- Telemetri: `C:\Users\yunus\OneDrive\Belgeler\Mission Planner\logs\2026-09-17 02-31-36.tlog` — SYSID_THISMAV=1 kaynaklı, time_boot_ms taşıyan paketler; **yalnız bu .bin açılışına ait olanlar** (PC zamanı − time_boot_ms ile GPS'ten hesaplanan açılış anı farkı < 30 s). Eşleşen 2627 paket; son paket **ATTITUDE**, time_boot_ms **202,182 s**, PC 02:53:45,71. ATTITUDE periyodu (medyan) 0,250 s. Filtresiz ‘son paket’ yanlış olurdu: tlog'da 3 başka açılışın paketleri de var.
- Yerel saat: GPS haftası/ms − 18 artık saniye → UTC. Saat dilimi, tlog dosya adındaki yerel saat ile ilk paketin UTC damgasından: **UTC+3**.

## Logdan hesaplanan olay zamanları ve rapor karşılaştırması

| Olay | Yöntem | Logdan (s) | Rapor/görev (s) | Fark (s) | >0,05 s |
|---|---|---|---|---|---|
| kalkis | W6 içindeki EV 28 (NOT_LANDED) | **188,300** | 188,30 | +0,000 | hayır |
| basamak1 | CCW−CW adım istatistiği (1 s sonra ort. − 1 s önce ort.), kalkış+1 s … roll/pitch/yaw çubuk çıkışı−1 s aralığında en büyük 2 tepe (≥2 s arayla) | **189,570** | 189,50 | +0,070 | **EVET** |
| basamak2 | aynı yöntem, ikinci tepe | **194,770** | 194,40 | +0,370 | **EVET** |
| sag | kalkış–başlangıç arası en büyük C1'i içeren C1 > RC1_TRIM+RC1_DZ bitişik dizisinin başı | **199,770** | 199,80 | −0,030 | hayır |
| telemetri | tlog: bu açılışa ait son paketin time_boot_ms'i | **202,182** | 202,18 | +0,002 | hayır |
| baslangic | kalkıştan sonra ilk IMU0 örneği, max(\|GyrX\|,\|GyrY\|) > 100 °/s | **202,410** | 202,41 | +0,000 | hayır |
| pervane | başlangıçtan sonra ilk IMU0 \|a\| > 2 g | **202,450** | 202,45 | +0,000 | hayır |
| pervane_bitis | başlangıç–ters arası IMU0 \|a\| tepesi | **202,490** | 202,49 | +0,000 | hayır |
| kopma | MAG I=0 `S` alanının donduğu değer (son güncelleme) | **202,470** | 202,47 | +0,000 | hayır |
| kopma_bitis | MAG I=0 `S`'nin ilk tekrarlandığı örnek (donuk) | **202,570** | 202,57 | +0,000 | hayır |
| ters | başlangıçtan sonra ilk ATT \|Roll\| > 90° | **202,770** | 202,77 | +0,000 | hayır |
| carpma | ters–disarm arası IMU0 \|a\| tepesi | **202,970** | 202,97 | +0,000 | hayır |
| disarm | W6'yı kapatan ARM (ArmState 0) | **203,970** | 203,97 | +0,000 | hayır |
| W1 başlangıç | log bloğu başı (ARM kaydı yok) | **49,571** | 49,60 | −0,029 | hayır |
| W1 bitiş | ARM kaydı | **61,470** | 61,50 | −0,030 | hayır |
| W2 başlangıç | ARM kaydı | **65,970** | 66,00 | −0,030 | hayır |
| W2 bitiş | ARM kaydı | **80,170** | 80,20 | −0,030 | hayır |
| W5 başlangıç | ARM kaydı | **134,170** | 134,20 | −0,030 | hayır |
| W5 bitiş | ARM kaydı | **150,655** | 150,70 | −0,045 | hayır |
| W6 başlangıç | ARM kaydı | **181,670** | 181,70 | −0,030 | hayır |
| W6 bitiş | ARM kaydı | **203,970** | 204,00 | −0,030 | hayır |
| W2 sert iniş | W2 içinde IMU0 \|a\| tepesi | **79,450** | 79,45 | +0,000 | hayır |
| telemetri kesilmesi belli | son ATTITUDE + medyan periyot (HUD ‘KOPTU’ bundan sonra) | **202,432** | ≤ ~0,25 s içinde (§8) | — | — |

Değer karşılaştırması:

| Büyüklük | Logdan | Rapor/görev | Not |
|---|---|---|---|
| W1 en büyük roll | +27,9° (61,37 s) | 27° | pencere içi \|Roll\| tepesi; rapor §5 27,2° diyor |
| Sağ düzeltme roll | +14,2° (200,27 s) | 13° | C1 girişi + 0,5 s içinde ATT Roll tepesi; videoda logdaki değer yazılır |
| Ters roll | +124,4° | 124° | |
| Askı yüksekliği | medyan (kalkış+3 s … başlangıç) +0,53 m; olay öncesi son örnek +0,68 m; kalkış+3 s +0,35 m | ~0,7 m, ‘düz hover’ | ‘~0,7 m’ olay anındaki değer; yükseklik pilotun gaz isteğiyle yavaşça arttı, başlık bu yüzden ‘yavaş tırmanışla ~0,5 m askı’ |
| Gaz ölü bandın üstünde | 187,97–192,77 s; C3 en çok 1612 µs (bant üstü ≥1598); DCRt en çok +38 cm/s | ‘çubuklar ortada’ | rapor §8 ‘büyük ölçüde ortada’ |
| Roll/pitch/yaw çubuk çıkışı | 198,97 s | — | kalkıştan sonra ilk \|Cx − TRIM\| > DZ (C1, C2, C4) |
| CCW−CW 1 s ort. | +15 (kalkış+1 s) → +520 µs (202,37 s) | +16 → +520 µs | ilk değerin penceresi raporda belirtilmemiş |
| Basamaklar | +22 → +152 µs; +154 → +318 µs | +144 (189,4), +271 (194,4) | rapor anlık/farklı pencere değerleri |
| Başlangıç öncesi uçuştaki en büyük max(\|GyrX\|,\|GyrY\|) | 72,8 °/s | — | 100 °/s eşiğinin payı |
| GPS | son örnek 202,41 s, periyot 0,20 s, sonraki kayıt 206,41 s durum 0 | 202,41 / 206,41 | |
| CH6 düşük / CH5 değişimi / mod Land | 203,77 / 202,77 / 202,95 s | 203,77 / — / — | |

## Örnek kareler (`kareler/`)

Her PNG, ffmpeg'e giden kare tamponunun kendisinden yazılır. Doğrulama: mp4 çözülüp aynı kare numarası (ve komşuları) PNG ile karşılaştırıldı; N'deki küçük ortalama fark H.264/yuv420p kaybıdır.

| Dosya | Kare no | Video anı (s) | Log zamanı (s) | mp4 kare N ↔ PNG: ort. fark / büyük fark % | N−1 | N+1 |
|---|---|---|---|---|---|---|
| kare_00_baslik.png | 45 | 1,500 | — | **1,79 / %0,185** | 1,79 / %0,185 | 1,79 / %0,185 |
| kare_01_oturum_ozeti.png | 180 | 6,000 | — | **1,93 / %0,214** | 1,93 / %0,214 | 1,93 / %0,214 |
| kare_02_t186_50s_canli.png | 285 | 9,500 | 186,500 | **1,72 / %0,150** | 2,25 / %0,590 | 1,86 / %0,257 |
| kare_03_t190_00s_canli.png | 390 | 13,000 | 190,000 | **1,81 / %0,201** | 2,97 / %1,197 | 2,61 / %0,861 |
| kare_04_t195_00s_canli.png | 540 | 18,000 | 195,000 | **1,81 / %0,237** | 2,91 / %1,154 | 2,43 / %0,791 |
| kare_05_t200_20s_canli.png | 696 | 23,200 | 200,200 | **1,87 / %0,273** | 2,57 / %0,869 | 2,46 / %0,829 |
| kare_06_t202_30s_agir.png | 786 | 26,200 | 202,300 | **1,87 / %0,367** | 2,07 / %0,488 | 2,35 / %0,675 |
| kare_07_t202_43s_agir.png | 825 | 27,500 | 202,430 | **1,92 / %0,384** | 2,74 / %1,070 | 2,53 / %0,953 |
| kare_08_t202_52s_agir.png | 852 | 28,400 | 202,520 | **1,98 / %0,460** | 2,90 / %1,174 | 2,91 / %1,195 |
| kare_09_t202_62s_agir.png | 882 | 29,400 | 202,620 | **2,01 / %0,473** | 3,04 / %1,320 | 3,12 / %1,378 |
| kare_10_t202_77s_agir.png | 927 | 30,900 | 202,770 | **2,01 / %0,476** | 6,86 / %4,130 | 2,49 / %0,891 |
| kare_11_t202_97s_agir.png | 987 | 32,900 | 202,970 | **2,05 / %0,520** | 5,29 / %3,357 | 2,76 / %1,166 |
| kare_12_t204_50s_sonra.png | 1149 | 38,300 | 204,500 | **1,86 / %0,270** | 2,04 / %0,365 | 1,96 / %0,319 |
| kare_13_sonuc.png | 1297 | 43,233 | — | **1,94 / %0,190** | 1,94 / %0,189 | 1,94 / %0,190 |

Büyük fark oranı: herhangi bir renk kanalında fark > 48 olan piksellerin yüzdesi. Doğru eşleşmede N sütunu ≈ 0; komşu karelerdeki değer, o anda görüntünün ne kadar değiştiğini gösterir (kartlarda komşu kareler aynıdır).

İşaret testleri (video dışı; `--test-isaret` ile ayrıca üretilebilir; hüküm çizim fonksiyonunun dünya geometrisinden hesaplanır):

- `test_roll+30.png`: roll +30°, pitch +0°, yaw +0° → **SAĞ TARAF AŞAĞI**; beklenenle uyum: **EVET**; yerleşim denetimi: yazı×yazı 0, çizgi×yazı 0, şekil×yazı 0, çizgi×etiket kutusu 0
- `test_pitch-30.png`: roll +0°, pitch −30°, yaw +0° → **BURUN AŞAĞI**; beklenenle uyum: **EVET**; yerleşim denetimi: yazı×yazı 0, çizgi×yazı 0, şekil×yazı 0, çizgi×etiket kutusu 0
- `test_yaw+45.png`: roll +0°, pitch +0°, yaw +45° → **SAAT YÖNÜ (yukarıdan)**; beklenenle uyum: **EVET**; yerleşim denetimi: yazı×yazı 0, çizgi×yazı 0, şekil×yazı 0, çizgi×etiket kutusu 0

## Yerleşim denetimi (betiğin kendi ölçümü)

Denetlenen kare: **1422** (videonun tamamı; kartlar dahil). Karelerdeki yazı sayısı 5–121.

| Ölçüt | Toplam kesişim | Etkilenen kare |
|---|---|---|
| yazı × yazı | **0** | 0 |
| çizgi × yazı (bağlantı/imleç/eşik/ölçek çizgileri) | **0** | 0 |
| şekil × yazı (grafik, gösterge, çubuk, rozet, etiket kutusu) | **0** | 0 |
| bağlantı çizgisi × başka etiket kutusu | **0** | 0 |
| alt sınırın altındaki yazı (veri <18 px, yardımcı <16 px) | **0** | 0 |

- En küçük yazı boyu: veri taşıyan **18 px**, yardımcı dipnot **16 px**.
- Panel sınırı taşması / sığmama / küçültme uyarısı: **0**.
- Kapsam: yazıların sınır kutuları (PIL `textbbox`, 1 px içeri), kayıtlı çizgiler (3B bağlantı çizgileri, şerit etiket çizgileri, grafik imleci, 1150/1949 çizgileri, gösterge sıfır/eşik çizgileri, işaret testindeki çağrı ve referans çizgileri), kayıtlı şekiller. **Kapsam dışı:** veri eğrileri, 3B sahnenin kendisi (ızgara, gövde, disk, gölge; etiket kutuları opak olduğu için yazının altında kalır) ve renk kontrastı. Bu yüzden ‘0’ bir kanıt değil, yalnız bu ölçütlerin sonucudur.

## Sınırlar

- **3B çizim temsilidir.** Gövde ölçüleri (kol 0,25 m, pervane yarıçapı 0,115 m) gerçek değildir. Katlanma, kopan parça ve yatay kayma çizilmez; araç yatayda sabittir, yalnız tutum ve yükseklik değişir.
- Tutum ATT'den 10 Hz: iki örnek arası doğrusal ara değer. 202,37 → 202,77 s arasında roll +1,5° → +124,4° yalnız 4 örnek aralığıdır; aradaki hareketin biçimi bilinmez. Ağır çekimde bu, dönüşü olduğundan düzgün gösterir.
- ATT bir EKF/AHRS kestirimidir; clip başladıktan sonra (202,45 s) ve çarpmadan sonra tutumun güvenilirliği düşer.
- Yükseklik (CTUN Alt) de EKF kestirimidir. Clip başladıktan sonra bozulur ve çarpmadan sonra −11,1 m'ye kadar iner (202,97–206,60 s aralığının en küçüğü). HUD bu aralıkta değeri ‘(güvenilmez)’ etiketiyle yazar. 3B çizimde yükseklik 0'da kırpılır ve en alçak nokta zemine gömülmesin diye çizim kaldırılır.
- Motor çubukları, sayılar ve disk renkleri RCOU komutudur (µs); gerçek itki ya da devir değildir. Olaydan sonraki tavan değerleri de komuttur, pervanenin döndüğünü göstermez.
- Log hızları (medyan örnek aralığından): IMU 25 Hz, ATT 10 Hz, RCOU 10 Hz, VIBE 10 Hz, CTUN 10 Hz, GPS 5 Hz. 202,41–202,45 s arasındaki sıralama bu örnek aralıkları kadar belirsizdir.
- Örnekle-tut değerleri ve olay metinleri, kare zamanı HUD'daki 1 ms çözünürlüğe yuvarlanarak seçilir (t + 0,5 ms). Örneğin 202,77 s karesi, 202,770183 s damgalı ATT örneğini gösterir.
- Telemetri: HUD son paketten (202,182 s) sonra ‘son … · bekleniyor’, sıradaki beklenen ATTITUDE anından (202,432 s) sonra ‘KOPTU’ yazar. Gerçek kesilme anı bu iki zaman arasındadır ve logdan daha kesin belirlenemez. GPS ‘VERİ YOK’ ise son örnekten sonra en büyük normal GPS aralığı (0,24 s) geçince yazılır.
- Gaz ölü bandı ArduCopter kaynak formülüyle parametrelerden hesaplandı (ölçüm değil, türetme); CTUN DCRt'nin aynı aralıkta pozitif olması (en çok +38 cm/s) bunu doğruluyor.
- ‘Pervaneler birbirine girdi’ ve ‘kablo kopması’ nedensellik yorumları kullanıcı beyanı + çıkarımdır; logdaki ölçüm |a|/clip patlaması ve veri kesilmesidir. Başlıklarda ölçüm ve (çıkarım)/(beyan) ayrı yazılır.
- Katkı payları (Gövde/tasarım %70–85 · Pilotaj+operasyon %10–25) DUSUS_ANALIZI §8 değerlendirmesidir, ölçüm değildir. Sonuç kartındaki ‘elektrik/sensör/ayar başlatıcı yok’ maddesi §3'e dayanır; bu betikte yeniden hesaplanmadı.
- Kamera sabittir; referans yön kalkış öncesi yaw ortalamasıdır (314,1°). Çizimdeki yaw dönüşü bu referansa göredir.
- Zaman ekseni tam görünümde 186–207 s'dir (görevdeki 186–206 yerine). Nedeni: 5. bölüm 206,6 s'ye kadar sürüyor ve imlecin eksende kalması gerekiyor.
- Olay çizgisinin tam görünümünde başlangıç…çarpma işaretleri tek etikette (‘Olay …’) toplanır; ayrı etiketler ağır çekimdeki yakın eksende görünür.
- 3B etiketler her kare için bağımsız yerleştirilir; tutum hızla değişirken bir etiket kareler arasında yer değiştirebilir.
- W1'in başlangıcında ARM kaydı yoktur (log disarm iken kapalı); başlangıç, disarm öncesindeki son log boşluğunun sonu alınır.
