# 17 Eylül 2026 02:53 düşüşü — log analizi

**Log:** `2026-09-17 02-50-38.bin` (kopya bu klasörde). ArduCopter 4.5.7, Pixhawk 6C.
**Olay anı:** log t = 202,41 s ≈ 02:53 yerel (GPS saati; oturum saatleri `workflow_sonuc.json` → çürütücü 4).
**Yöntem:** mimar ön çıkarımı → Workflow `dusus-log-analizi-0250`:
- 3 bağımsız mercek: itki/mekanik, temas/pilot, sensör/elektrik
- 1 sentez
- 3 çürütücü: neden, sayılar, paylar

Sayıların hepsi bağımsız olarak yeniden ölçüldü. Kilit üç iddiayı mimar ayrıca doğruladı (§5). Betikler `betikler/`, tüm ajan çıktısı `workflow_sonuc.json`.
Motor eşlemesi: C9 = M4 arka-sağ CW, C10 = M2 arka-sol CCW, C11 = M1 ön-sağ CCW, C12 = M3 ön-sol CW. Karışım regresyonuyla da doğrulandı: roll r = 0,77, pitch r = 0,90. Pervane dönüş yönü bu yöntemle doğrulanamadı.

## 1. Oturumdaki arm pencereleri

| Pencere | Süre (s) | Ne oldu |
|---|---|---|
| W1 | ~49,6–61,5 | **Yerde devrilme.** Stabilize'da arm, gaz kısmen açık (C3 1157–1452), yerde Loiter'a geçildi. Yerdeyken denetleyici istenen roll'u 3 → 20°'ye biriktirdi, araç sağ taraf aşağı **27°**'ye yattı. Motorlar dönüyordu (M1 1150–1503 µs). Clip 0; güçlü darbe imzası yok. |
| W2 | 66,0–80,2 | Kısa sıçrama. Pilot havada gazı en alta çekti (C3 1683 → 1001, 78,6–79,0) → **sert yere değme** 79,45: \|a\| 31 m/s², Clip 0 → 10. VibeZ bu değmeden önce de ~17,6'ydı. |
| W3–W4 | 113–118, 120–124 | Kısa arm-disarm, kalkış yok |
| W5 | 134,2–150,7 | Kalkış 140,9. Yerden ~0,45 m askı, LAND ile iniş. Tutum hatası 1,41/1,07°, motor yayılımı 40 µs; gözle normal. Titreşim yüksek (VibeZ ~18). Havadaki son saniyede CCW−CW +85…+204 µs başlamıştı. |
| **W6** | 181,7–204,0 | **Düşüş** (§2) |

## 2. Son uçuş (W6)

| t (s) | Olay |
|---|---|
| 188,3 | Kalkış; ~0,7 m yer üstü askı |
| 188,6 → 202,4 | Denge bozucu büyüdü, çubuklar ortada. CCW−CW +16 → +144 (189,4) → +271 (194,4, VibeZ 29 ile) → **+520 µs** (202,4). Roll karışımı +10 → +74 µs, ROut 0,02 → 0,16. Yaw hatası 0,4 → **13,8°**. **M4 202,37'de 1202 µs, uçuşun en düşüğü** (sağ tarafın itki yedeği daraldı). Doyum yok. |
| 199,8–200,4 | **Pilot tam sağ roll** (C1 1607–1813), 13° yatış |
| 200,8 → 202,37 | Araç gövdenin sağına 0,71 m/s hızlandı. ~1 m kaydı; **olay anında hâlâ sağa gidiyordu (0,14 m/s)**, sağ taraf öndeydi. Pilot 201,2–202,4 arasında sola frenleme girişi (C1 1386–1436) verdi. |
| 202,37 | Son normal örnek: roll 1,5°, pitch −5,1°; M1 1602, M2 1788, M3 1577, M4 1202; 14,52 V / 43,5 A |
| **202,41** | **Başlangıç — ön-sağ köşe düştü.** GyrX +143 °/s (sağ aşağı), GyrY −104 °/s (burun aşağı). \|a\| 10,4 → **5,2** m/s²: itki kaybı, gövdeyi iten bir çarpma değil. Yaw adımı yok (ΔGyrZ +2 °/s). |
| 202,45–202,49 | Yüksek frekanslı darbe: \|a\| 27 → 57 m/s², Clip 10 → 32 / 6 → 26, VIBE 45–67. **Pervane darbesi imzası.** |
| 202,47 | FC M1'i tavana (1949) aldı; köşe toparlanmadı. Harici pusula ve GPS 202,47–202,57 arasında havada kesildi (sonuç). |
| 202,57–203,07 | Akım 120 A sensör tavanında, gerilim en düşük 9,42 V. 00:20 düşüşünde de aynı desende 115–120 A ölçüldü; mekanizmayı ayırt etmez. |
| 202,77 | Roll 124° (ters). Pilot: doğru yönde karşı-dümen + LAND anahtarı (etkisi yok) |
| 202,97 | Ters hâlde yere çarpma: \|a\| 53/73 m/s², Clip → 115. ERR COMPASS (zaman aşımı, sonuç) |
| 203,17 → 203,27 | Komutlar değişmeden akım 111,5 → 57,9 A: bir motorun yükü kalktı (hangisi belirsiz) |
| 203,77 / 203,97 | CH6 disarm (çarpmadan 0,8 s sonra; FS_CRASH_CHECK'in ≥2 s'sinden hızlı) |

## 3. Olaydan önce temiz olanlar

- Besleme: Vcc 5,02–5,12 V, VServo 5,12–5,24 V.
- Pil: 14,52–15,17 V / 33,5–46,5 A.
- RC kopukluğu yok.
- GPS ve EKF temiz; pusula ve GPS kesintisi olaydan sonra.
- Parametreler 00:20 loguyla aynı (14 farkın hepsi kalibrasyon ya da sayaç).
- **Elektrik, sensör ya da ayar kaynaklı başlatıcı yok.**

## 4. Hüküm

**Birincil neden (güven: düşük–orta):** 202,41 s'de havada, yerden ~0,7 m yüksekte, **ön-sağ köşede (M1 bölgesi) ani itki kaybı**. İmza pervane darbesiyle uyumlu.
Darbenin nereye olduğu **logdan ayrılamıyor**:

- **(A) İç:** gevşemiş kol ya da motor yatağı, pervanenin GPS direğine veya kabloya değmesi, W1/W2'de hasar görmüş pervane ya da motor. Destekleyen: 13 s boyunca büyüyen denge bozucu; W1'de sağ taraf aşağı yere yatma; W2 sert değme; 00:20 düşüşünde de temasın sağ taraftan olması (D-490, ÇIKARIM).
- **(B) Dış:** gece, ~0,7 m'de sağa kayarken M1 pervanesinin bir cisme (bitki, direk, kablo vb.) girmesi. Destekleyen: olay anında araç sağa gidiyordu ve sağ taraf öndeydi. "İtki kaybı + clip" imzası dış pervane darbesini dışlamaz.

**Katkı tablosu** — ⚠ **değerlendirmedir, ölçüm değil.** Ayrım muayeneye bağlı olduğu için iki dal ayrı yazıldı:

| Etken | (A) İç arıza ise | (B) Dış pervane darbesi ise |
|---|---|---|
| Mekanik (00:20 sonrası bozulmuş araç, M1 köşesi) | %60–75 | %30–45 |
| Pilotaj (W1 yerde Loiter devrilmesi, W2 gaz kesme, 0,7 m'de gece sağ manevra) | %0–5 | %20–35 |
| Operasyon kararı (00:20 düşüşünden 2,5 saat sonra, belgelenmiş muayene ve kabul testi olmadan, gece, düşük irtifada uçuş) | %15–25 | %15–25 |
| Ayar / sensör / elektrik | %0–5 | %0–5 |
| **Pilot + operasyon toplamı** | **~%15–30** | **~%35–60** |

Olay anındaki pilot tepkisi (karşı-dümen, 0,8 s'de disarm) doğruydu; düşüşü değiştirmedi. Dört motorlu araçta tek motor kaybı ArduCopter'da telafi edilemez (`AP_MotorsMatrix.cpp`: itki dengeleme ≥ 6 motor); 0,7 m irtifa düşüşün nedeni değil.

## 5. Mimar doğrulaması ve düzeltmeler

- Çürütücüler sentezin iki karşılaştırmasını geçersiz saydı:
  - "00:20 ile eşleşik askı: jiro RMS ×10–15, ThO −%22": pencereler farklı yükseklikte (1,6 m ile 0,45 m). Yere yakın eşleşik pencerelerle değişim daha küçük: ThO −%13…−19, VIBE ×2,5–3,2, GyrX std ×2,6.
  - "Temiz pervane kopması akımla çelişiyor": 120 A tavanına 00:20 düşüşünde de ulaşılmıştı; akım ayırt edici değil.

  Bu rapor ikisini de kullanmıyor.
- Mimar kendisi ölçtü: W1 yerde devrilme (DesRoll 3,4 → 20,1°, roll 27,2°, ThO 0, akım 8–16 A); 198,6–202,37 pilot sağ roll ve sağa kayma (gövde sağ hızı en fazla 0,71 m/s; 202,37'de 0,14).
- **D-490 düzeltmesi:** 00:20 raporunda "uçuş 1: Loiter, 4 kısa iniş-kalkış" yanlıştı. Bu, **pervanesiz yer koşusudur**: motorlar 1949 µs'ye kadar çıkıyor, ThO 0,89, akım en fazla 8,8 A. Askı için ~40 A gerekir. Düşüş hükmü değişmez.

## 6. Muayene (öncelik sırasıyla) — (A)/(B) ayrımı buradan çıkar

1. **M1 köşesi:** pervane (kırık/eksik kanat, göbek kayması), motor çanı (elle dönüş, stator sürtmesi, yatak), motor vidaları, kol (burulma, çatlak).
   **Ayırt edici:** M1 pervanesinde ve sağ kollarda **yabancı malzeme izi** (bitki özsuyu, ahşap, boya, toprak) mı, yoksa **GPS kablosu ya da direği plastiği izi** mi?
2. GPS direği ve kablosu: kopma, ezilme, pervane izi. Direğin ve kablonun M1 pervane diskine mesafesi.
3. M4 ve M3 kolları: eksen dikliği, vida torku (denge bozucu büyürken M4 1202 µs'ye indi).
4. M1 ESC'si, faz kabloları, lehimler; pil konnektörü, PM06, ana kablolar (≥120 A, 9,4 V).
5. Dört pervanenin tipi, boyu, yönü ve 00:20 öncesiyle aynılığı.
6. FC montajı ve sönümleyiciler (VIBE ×2,5–3).

**Kullanıcıdan istenen bilgiler:**
- (a) 00:20 ile 02:50 arasında hangi parçalar değişti?
- (b) W1'de sağ pervaneler yere değdi mi?
- (c) Düşüş noktasının 1 m çevresinde engel var mıydı; tanık anlatımı var mı?
- (d) W1/W2 sonrası görsel kontrol yapıldı mı?

## 7. Yeniden uçmadan önce (zorunlu)

- §6 muayenesi + değiştirilen parçaların kaydı.
- Pervanesiz motor testi, videolu (yol haritası Faz 2.6).
- **U1 kabul askısı** (yol haritası Faz 8): ~3 m, ≥ 30 s, açık alan, gündüz ya da iyi aydınlatma.
  - Motor yayılımı ≤ 40 µs, CCW−CW ≤ 60 µs, VibeZ p95 ≤ 16, tutum hatası ≤ 1,5°.
  - Bu uçuşta CCW−CW +520 µs'ye çıktı; bu değerlerle uçuşa çıkılmaz.
- **Kalkış ve iniş Stabilize'da;** yerdeyken Loiter'a geçilmez (W1'deki yerde devrilme).
- Hiçbir değer sahada yalnız gözle değerlendirilmez. Her uçuştan sonra log analizi yapılır ve bir sonraki uçuşa geçilmeden önce bakılır.

---

## 8. YENİDEN YORUM — kullanıcı beyanı (17 Eyl, sabah)

**Beyan (BEYAN, fotoğraf yok):** drone "kitap gibi ikiye katlandı". İki pervane birbirine girdi. GPS, telemetri "her şey" koptu. İki motor çalışmaz halde. Hasar büyük.

**Beyanı destekleyen log ölçümleri:**

| Ölçüm | Değer | Anlamı |
|---|---|---|
| GPS son örnek | 202,41 s; 5 Hz'de sıradaki (~202,61) gelmedi, sonraki kayıt 206,41 St 0 | GPS hattı **havada**, 202,41–202,61 arasında koptu |
| Harici pusula (GPS modülünde) | son güncelleme 202,47; 202,57'den itibaren donmuş | Aynı kablo **havada** 202,47–202,57 arasında koptu |
| Telemetri (MP tlog `2026-09-17 02-31-36.tlog`) | araçtan gelen son paket ATTITUDE, time_boot_ms **202,182 s** (PC 02:53:45,71); sıradaki paketler (~202,43 / 202,68 / 202,93) hiç gelmedi | Telsiz bağlantısı başlangıç anında (≤ ~0,25 s içinde) **havada** kesildi |
| Yere çarpma | 202,97 s | Kopmalar çarpmadan **0,4–0,5 s önce** |
| İtki kaybı sırası | \|a\| 10,4 → 5,2 (202,41), **sonra** clip patlaması 202,45–202,49 | Önce köşenin itkisi yön değiştirdi ya da kayboldu, sonra pervaneler çarpıştı |
| Öncül | 13 s boyunca CCW−CW +16 → +520 µs, roll karışımı +10 → +74 µs, yaw hatası 14°, M4 1202 µs; çubuklar büyük ölçüde ortada | Kol ya da gövde **uçuş sırasında giderek esniyor/burulyordu**: motor itki ekseni eğildikçe yaw ve roll torku doğar |
| Oturum titreşimi | Yere yakın eşleşik pencerelerde VIBE 00:20 öncesinin ×2,5–3,2'si; W2'de sert değmeden önce de yüksek | Gövde oturum başından beri daha az rijitti |

**Yeni hüküm (güven: orta–yüksek):** Başlatıcı **uçuşta yapısal çöküş**. Gövde ya da kol bağlantısı 13 s boyunca giderek esnedi (itki ekseni kaydı → artan motor dengesizliği). 202,41 s'de aniden katlandı. Ön-sağ köşe itkisini kaybetti. Katlanan yarımların pervaneleri birbirine girdi (clip patlaması). GPS direği ve telemetri kabloları **havada** koptu. Drone ters dönüp düştü.

- §4'teki (B) "dış cisme pervane darbesi" artık **düşük olasılık**. Kablo kopmaları çarpmadan önce, havada; öncül bozulma yapısal esnemeyle birebir uyumlu.
- (A)'nın alt adayı "pervanenin GPS kablosuna değmesi" de başlatıcı olarak zayıfladı: kopma, katlanmanın sonucu olarak açıklanıyor.
- Katlanma çizgisi logdan kesin çıkmıyor: ilk düşen köşe ön-sağ (M1). Hangi iki pervanenin çarpıştığı ve hangi iki motorun öldüğü fotoğrafla belirlenir.

**Neden zayıfladı (ÇIKARIM, logla kesinleşmez):**
- 3B baskı gövde ve kollar (`dronesolid/`).
- 00:20 düşüşünde sağ taraf temas etti (D-490).
- Bu oturumda ek yükler bindi: W1'de yerde, pervaneler dönerken sağ taraf aşağı 27° yatma; W2'de gaz kesilip 3,2 g sert iniş.
- Titreşimin oturum başından yüksek olması, çatlağın ya da gevşek bağlantının 02:50'den önce var olduğunu düşündürür.

**İkinci beyan (kullanıcı):** "Drone bir yere çarpmadı, dümdüz hover yapıyorduk." → §4 (B) dış temas **elendi**.
Log bununla uyumlu: olaydan 2 s önce 13°'lik kısa bir sağ düzeltme ve ~1 m kayma var, ama darbe ya da temas izi yok. Başlatıcı iç yapısal çöküş.

**Üçüncü beyan (kullanıcı):** "Muayene tamamen yapılmıştı ve doğrulanmıştı" (00:20 düşüşünden sonra, 02:50 uçuşlarından önce). Kabul edildi, BEYAN. "Muayenesiz uçuş" gerekçesi kaldırıldı.

**Bu beyanla log birlikte ne söylüyor (ÇIKARIM):**
- Oturumun başında, W1 yer yatması ve W2 sert inişten önce, W2 kısa sıçramasında VibeZ zaten ~17,6'ydı. Yere yakın eşleşik pencerelerde bu, 00:20 öncesinin ×2,5–3,2'si.
- Yani gövde muayeneden **geçmiş hâliyle** daha az rijitti. Görsel ya da elle yapılan muayenenin yakalayamadığı bir **gizli hasar** (baskı katmanları arası iç çatlak, bağlantı vidasının plastikte gevşemesi) ya da gövdenin **tasarım/malzeme dayanımının** bu yük için yetersizliği olası.
- W5 askısının logu bunu ölçümle gösteriyordu: VibeZ ~18; havadaki son saniyede CCW−CW +85…+204 µs. Sorun muayenenin eksikliği değil; **ölçümlü kabul kriterinin** (log kontrolü) sahada bulunmaması.

**Katkı değerlendirmesi (ÖLÇÜM DEĞİL; §4'ün yerine geçer):**

| Etken | Pay |
|---|---|
| Yapı / tasarım: gövde veya kol uçuşta katlandı; muayenede görülmeyen gizli hasar ya da yetersiz dayanım | %70–85 |
| Pilotaj: W1'de yerde Loiter'a geçme (27° yatma), W2'de gazı kesme (3,2 g sert iniş) — muayeneden SONRA gövdeye ek yük; son uçuşta pilotaj hatası yok | %5–15 |
| Operasyon: W1/W2 olaylarından sonra 30–60 s içinde yeniden kalkış (oturum saatleri: W2 değme 02:51:42, W5 kalkış 02:52:43); gece; ölçümlü kabul kontrolü yok | %5–15 |
| Sensör / elektrik / ayar | %0–5 |
| **Bu uçuş tek başına: pilot + operasyon** | **~%10–25** |
| **Zincir: gizli hasar 00:20 düşüşünden kaldıysa (ÇIKARIM; o düşüş ~%80–85 pilot/operasyon, D-490)** | **~%50–65** |
| **Zincir: gizli hasar değil, tasarım/malzeme yetersizliğiyse** | **~%10–25** |

**Önleme (ders):**
1. Düşüş yaşamış **3B baskı taşıyıcı parçalar yeniden kullanılmaz**; plaka ve kollar yenisiyle değiştirilir. Muayeneden geçse bile: baskı parçada katman arası çatlak gözle görülmeyebilir (bu düşüş, doğrulanmış muayeneye rağmen oldu).
2. Her uçuş öncesi **esneme/burulma testi**: kol ucunu elle yukarı-aşağı ve döndürerek zorla; gözle görülür esneme ya da çıtırtı varsa uçulmaz.
2b. **Görsel muayeneye ek olarak ölçümlü kabul:** ilk askıdan sonra log kontrolü (VibeZ p95 ≤ 16, motor yayılımı ≤ 40 µs, CCW−CW ≤ 60 µs) geçmeden bir sonraki uçuşa geçilmez. W5 bu kontrolden geçemezdi (VibeZ ~18, sonda CCW−CW +204 µs).
3. **Uçuşta erken uyarı:** motor çıkışları arasındaki fark büyüyor ya da drone yönünü tutamıyorsa (bu uçuşta 13 s boyunca açıkça görüldü) hemen iniş. MP'de Status sekmesinde `ch9out`–`ch12out` izlenebilir. YKİ'ye otomatik alarm eklenmesi ayrı iş olarak kuyruğa önerilir.
4. Yarışma takvimine göre gövde malzemesi kararı (karbon plaka/kol ya da baskı parametreleri: malzeme, doluluk, et kalınlığı) — insan kararı.
