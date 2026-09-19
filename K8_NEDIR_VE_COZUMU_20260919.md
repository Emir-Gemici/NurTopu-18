# K8 NEDİR, NEDEN DÜŞTÜ, NASIL ÇÖZÜLÜR

**Tarih:** 19 Eylül 2026 (gece) · **Yazan:** Claude 1 (mimar) · **Dal:** `master`
**Neden bu belge:** kullanıcı *"K8 nedir nasıl çözülür'e odaklanalım"* dedi.

> ## ⚠ REVİZYON 2 (19 Eyl ~04:00) — ilk sürümde CİDDİ BİR HATA VARDI
>
> Emir tarafının denetimi yedi kusur buldu; **yedisi de haklı**, kendim doğruladım. En ağırı:
> ilk sürümde "%43 kayıp birebir doğrulandı" dedim, ama o hesap **döngüseldi** — paket kaybı
> `p`'yi sonucu %43 verecek şekilde geri seçip sonra "uyuşuyor" diye sunmuşum. Bağımsız bir
> kaynaktan (K8a'nın ölçülen %3,5 kaybı) hesaplandığında model **%16** öngörüyor, yani
> **rastgele paket kaybı ölçülen %43'ü açıklamıyor.** Düzeltilmiş hâli §3'tedir.

---

## 0. ÖNCE BİR DÜZELTME: "drone testi" ile "İHA yarışması" aynı şey değil

Kullanıcı bu ayrımı yaptı ve **haklıydı** — ben şartnamenin İHA maddelerini yaklaşan uçuşa
uyguluyordum. Doğru şartname `Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf`
(⚠ repo kökündeki `2026_TEKNOFEST_TYDA_SARTNAME_...pdf` **bizim yarışmamız değil**, "Yapay Zeka
Dil Ajanları" şartnamesidir — ona bakan yanlış yerde arar).

| | **§5.3.2 Drone ile Görev Test Uçuşu** (yaklaşan) | **İHA + İKA yarışması** (asıl) |
|---|---|---|
| Alan | **20 × 20 m** simüle test alanı | İHA-UB **300 × 300 m** |
| Görev | "Başlangıç Alanı" ↔ "Hedef Alanı" arası **Açık Güzergâh** tespiti | tam senaryo (İKA, HB, mancınık) |
| İrtifa | asgari **30 m** | — |
| Süre | **maks 10 dk** (kalkış+tespit+aktarım+iniş) | ayrı |
| Puan | final notunun **%15'i** | — |
| Başarısızlık | yanlış güzergâh · süre aşımı · **hakem onayının alınamaması** | + **Alan İhlali** (İHA-UB dışı) |

**Sonuç:** "Alan İhlali" ve `--ub-referans` bu uçuşun konusu **değil** (asıl yarışmanın maddesi).
Bu uçuşta belirleyici olan **gerçek zamanlı aktarım + hakem onayı + 10 dk + 30 m irtifa**.

🔴 **Ve K8 tam da buraya çarpıyor.** ⚠ *Düzeltme:* ilk sürümde alıntıladığım *"veri akışının
sağlanamadığı durumlarda uçuş geçersiz sayılacaktır"* cümlesi **asıl yarışmanın** maddesidir,
§5.3.2'nin değil (Emir tarafı haklı olarak düzeltti). Ama sonuç değişmiyor, çünkü §5.3.2 kendi
metniyle aynı şeyi söylüyor: *"gerçek zamanlı güzergah tespitinin alan hakem heyeti tarafından
doğrulanıp onaylanması"* zorunlu ve *"kriterlerden herhangi birini sağlayamayan … takımlar 0 puan
alarak görevden başarısız sayılacaktır."* Rota yere geç/eksik ulaşırsa hakem onaylayamaz → **0 puan.**

---

## 1. K8 nedir (sade)

Jetson'ın bulduğu rota yere **telsizle** iniyor. Bugünkü saha düzeninde ayrı bir veri telsizi yok:
NAVITAS mesajları Pixhawk'ın içinden geçip **tek telsiz** üzerinden yere iniyor. Buna **tünel**
deniyor. **K8**, bu tünelin sahada gerçekten çalışıp çalışmadığını ölçen kapıdır:

| Kapı | Ne ölçer | Eşik |
|---|---|---|
| **K8a** | Ham tünel gidiş-dönüş süresi (hub kapalı, yalnız taşıyıcı) | p95 **< 200 ms** |
| **K8b** | Üretim yolu (tüm servisler açık) gidiş-dönüş | p95 **< 200 ms** |
| K8 çok parçalı | 473 B'lık **gerçek rota mesajının** kaybı | kapı dışı, zorunlu kayıt |

## 2. Ne ölçüldü (D-494, 18 Eylül, Emir tarafı)

| Ölçüm | Sonuç | Hüküm |
|---|---|---|
| K8a | kayıp %3,5 · p95 **268 ms** | eşik 200 ms → **DÜŞTÜ** |
| K8b | p95 **360 ms** | **DÜŞTÜ** |
| 473 B rota (4 parça) | **%43 kayıp** | 🔴 |

## 3. Üç kök neden — biri çözüldü, ikisi duruyor

**(a) TELEM2 doygunluğu — ÇÖZÜLDÜ.** Akış hızı isteği sıfırlanınca kayıp **%54 → %3,5**.

**(b) Telsizin kendi zamanlama penceresi (Max Window) — gecikmenin TABANI.** Pixhawk yolu hiç
yokken bile p95 **231 ms** ölçüldü; gecikme yazılımdan değil telsizin gönderim penceresinden
geliyor. Emir tarafının hesabı: pencere 33 ms'ye indirilirse tur süresi kısalır, beklenen p95
**170–180 ms**, verim ~%10 düşer, menzil değişmez.

⚠ **İlk sürümdeki iç çelişki düzeltildi:** "pencere şu an 62 ms" ile "131 → 33" aynı belgede
yazılıydı; ikisi farklı kaynaklardan gelmişti ve uzlaştırılmamıştı. Geçerli olan, sabah
uygulanacak prosedürün yazılı olduğu **saha kartı §1b.2**'dir (tünel dalı, `bff1f534`).

🔴 **VE BU AYAR DAHA ÖNCE BİR KEZ BAŞARISIZ OLDU — ön kayda bağlanmalı:** REVIEW_LOG (tünel dalı)
D-478 §2: *"A6 ikinci deneme (Max Window 131→33 ve Air Speed 64→128 **aynı anda**, port COM14).
200 prob, **0 ACK**, verdikt ÖLÇÜLEMEDİ."* Aynı sprintte D-479, "RTT ≈ 2 × Max Window"
açıklamasını **çürüttü**: A6'yı geçiren şey Air Speed 64→128'di, Max Window 131'de kalmıştı.
**Ders:** iki ayarı aynı anda değiştirmek ölçümü yok etti. Sabah Max Window **tek başına**
değiştirilmeli ve sonuç ön kayıtla karşılaştırılmalı.

**(c) Parça boyu telsizin taşıma sınırını aşıyor — ROTA KAYBININ ASIL SEBEBİ.** Telsiz bir MAVLink
çerçevesini ancak **payload ≤ 93 bayt** ise tek pakette taşıyor. Bizim tünel parçalarımız
**128 bayt** (`TUNEL_MAVLINK_YUK_B`), yani **her parça iki telsiz paketine bölünüyor**.

### 3.1 Çerçeve boyları (DÜZELTİLDİ) ve kayıp modelinin SINIRI

**İlk sürümün hatası (iki tane):**
1. Çerçeve boyları **iyimserdi**: yol noktalarını `[0,0], [1,2], [2,4]…` gibi kısa sayılarla
   ürettim. Gerçek koordinatlar ±15 m aralığında iki ondalıklıdır ve JSON'da daha uzun yer kaplar.
2. "%43 birebir doğrulandı" **döngüseldi** (yukarıdaki revizyon notu).

**Ölçülen gerçek boylar** (`comms/protocol.py`, ±15 m rastgele koordinat, `ref_xy` dolu):

| Yol noktası | Çerçeve | Tünel parçası (123 B yük) | Telsiz paketi (parça başına 2) |
|---|---|---|---|
| **30** | **529 B** (ilk sürümde yanlışlıkla 469) | **5** | **10** |
| 20 | 397 B | 4 | 8 |
| 10 | 275 B | 3 | 6 |

Emir tarafının bağımsız ölçümü (528 B / 5 parça) ile **uyuşuyor**.

**Kayıp modeli ölçüleni AÇIKLAMIYOR.** K8a'nın ölçülen tek-parçalı kaybı %3,5; tek parçalı çerçeve
2 telsiz paketi ettiğine göre paket başına kayıp `p ≈ %1,77`. Bununla:

| | Paket | Model P(tek) | Model kayıp |
|---|---|---|---|
| 30 wp | 10 | 0,837 | **%16,3** |
| 20 wp | 8 | 0,867 | %13,3 |
| 10 wp | 6 | 0,899 | %10,1 |

Sahada ölçülen ise **%43**. Aradaki fark rastgele kayıp değildir.

### 3.2 🔴 ASIL BULGU (Emir tarafı, ham JSON'dan): kaybın çoğu "GEÇ ACK"

`results/tunel_20260918/K8_cok_parca_473.json` okunduğunda: **%43'ün yaklaşık 30 puanı, 0,5 s
zaman aşımından SONRA gelen cevaplardır.** Gerçek kayıp ≈ **%13**, kalanı gecikmedir.

**Bu, sorunun niteliğini değiştirir:** mesele paketlerin yok olması değil, **çok parçalı bir
çerçevenin 8–10 paketinin telsizin TDM penceresinden sırayla geçmesi** ve toplam sürenin zaman
aşımını aşmasıdır. Dolayısıyla:

* "Kayıp" olarak sunulan sayı yanıltıcıdır; ölçülmesi gereken **gecikme dağılımıdır**.
* Parça sayısını azaltmak yine doğru yöndedir — ama gerekçesi "daha az paket kaybolur" değil,
  **"daha az pencere beklenir, toplam süre kısalır"**dır.

## 4. Çözümler ve ölçülebilir etkileri

| # | Çözüm | Etkisi | Kim / ne zaman |
|---|---|---|---|
| 1 | **MP telemetri hızlarını düşür** (Attitude 1, Position 2, Mode/Status 1, RC 0, Sensors 0, Extra 1) — `Config → Planner` ekranından. ⚠ `SR1_*` parametresini elle yazmak **tutmaz**: MP her bağlanışta kendi hızlarını yeniden ister | Paket kaybı `p` düşer → tüm satırlar iyileşir | Emir, sabah |
| 2 | **Max Window 131 → 33 ms** (iki telsizde birden, MP SiK ekranından) | p95 268 → **170–180 ms** (hesap) → K8 eşiği geçilebilir | Emir, sabah |
| 3 | ~~Air Speed 128 → 250~~ | **YAPILMAYACAK**: menzili düşürür, menzil hiç ölçülmedi (T271) | — |
| 4 | **Tünel parça boyu 128 → 88 B** (T287) | 30 noktalı rota: 8 → 6 paket, P 0,569 → **0,655** | Sözleşme+test değişikliği, **uçuş sonrası** |
| 5 | **Yol noktası sayısını azalt** (`WP_ARALIK_M` 2,0 → 4–5 m) | 30 → 10 nokta: **10 → 6 paket**, yani beklenen pencere sayısı %40 azalır (gecikme düşer) | ⚠ **KOD DEĞİŞİKLİĞİ — uçuş sonrasına**, T287'nin yanına (aşağıya bak) |
| 6 | **Tekrar** (`KararYayinci`, hâlihazırda 4 tekrar) | P 0,569 → **0,966** (en az biri ulaşır) | Zaten çalışıyor |

### 4.1 5 numara: gerekçesi geçerli, ZAMANLAMASI değil

⚠ **Düzeltme (Emir tarafı haklı):** T287 aynı gece "kod dondu" gerekçesiyle uçuş sonrasına
alınmıştı; **aynı kural bu öneriye de uygulanmalıdır**. Ayrıca `codes/test_rota_sentetik.py`
(genel kapı) bu sabiti kullanıyor — değiştirilirse kapı yeniden koşulmadan sahaya gidilemez.
Bu yüzden madde 5 **sabahın işi değil, uçuş sonrasının işidir.**

Gerekçesi ise geçerli ve kayıtta kalmalı:

Yol noktaları 2 m aralıkla üretiliyor (`costmap_path_finder.WP_ARALIK_M = 2.0`). Bu sıklık
**İKA'nın güzergâhı takip etmesi** için konmuştu. Ama **§5.3.2 test uçuşunda İKA yok** — güzergâh
yalnız YKİ'de gösterilip hakeme onaylatılıyor. Dolayısıyla bu uçuş için seyrek nokta yeterlidir
ve mesajı yarıya indirir. Asıl yarışmada (İKA varken) aynı gevşetme **yapılmamalıdır**.

### 4.2 Birleşik etki — PAKET SAYISI (kayıp olasılığı değil)

Geç ACK bulgusundan sonra doğru ölçüt **kaç telsiz paketi gönderildiğidir**; her paket bir TDM
penceresi bekler.

| Senaryo | Telsiz paketi | Değişim |
|---|---|---|
| Bugün (30 wp, 128 B parça) | **10** | — |
| + parça ≤ 93 B (T287) | 5–6 | ~%45 az |
| + 10 yol noktası | **3** | **%70 az** |

⚠ **P(4 tekrar) hesapları belgeden ÇIKARILDI.** İlk sürümde `1-(1-P)⁴` kullanmıştım; bu,
kayıpların **bağımsız** olduğunu varsayar. Geç ACK bulgusu tam tersini gösteriyor: gecikme
pencere doluluğuna bağlı, yani tekrarlar **korelasyonlu** olabilir. Ham JSON'larda prob başına
kayıt olmadığı için bağımsızlık doğrulanamıyor.

## 5. Önerilen sıra (sabah)

1. **MP telemetri hızlarını düşür** (`Config → Planner`) → **100 prob → YENİ BASELINE kaydet.**
   ⚠ Bu adım atlanırsa MP değişikliğinin etkisi MW33'ünkinden **ayrılamaz** — D-478 §2'de iki ayar
   birlikte değiştirilince ölçüm yorumlanamaz hâle gelmişti; aynı hataya düşülmemeli.
2. **Yalnız `MAX_WINDOW` 131 → 33** (iki telsizde de; Air Speed'e **dokunma**) → 100–200 prob.
3. **Karşılaştır:** p50 / p90 / p95 / p99 / maks / zaman aşımı sayısı — yalnız "kayıp %" değil.
   **Ön kayıt:** beklenen p95 **133–178 ms** (§7.1). 0 ACK gelirse ayar **derhal geri alınır**
   (saha kartı §1b.2).
4. **p95 hâlâ > 200 ms ise ayar değiştirmeyi BIRAK** → RTT'yi parçala: Jetson'da `seri_hub`'ın
   çerçeve alma / yanıt yollama zaman damgalarıyla işleme süresinin (`P`) hava yarısını ölç.
5. T287 (parça boyu) ve yol noktası seyrekleştirme → **uçuş sonrası**, birlikte, kapı koşularak.

**Eşik gevşetilmez** (ön kayıtlı). Hedef tutmasa bile uçuş yapılabilir: komutlar ve hakem onayı
20 tekrarla güvenilir, rota gecikmeli gelebilir, **tutanağa yazılır**.

## 6. Bu belgenin ölçüm dayanakları
- D-494 (tünel dalı) — saha ölçümü, K8a/K8b/473 B
- Bu oturum — `comms/protocol.py` ile gerçek çerçeve boyutları ve teslim olasılıkları
- `comms/mavlink_tunel.py` (tünel dalı) — `TUNEL_MAVLINK_YUK_B = 128`, parça yükü 123 B
- `codes/costmap_path_finder.py:117` — `WP_ARALIK_M = 2.0`
- Şartname §5.3.2 ve İHA-UB tanımı — `Ileri_Otonom_Sistemler_..._Sartname_TR_Ltktw.pdf`

---

## 7. 🆕 231 ms NEREDE OLUŞUYOR — bileşen bütçesi (HESAP, ölçümden önce yazıldı)

"Ayar kurcalamak yerine RTT'yi parçalara ayır" doğru yaklaşımdır; parçaların bir kısmı **ölçüm
gerektirmez**, baud'dan doğrudan çıkar.

> ⚠ **REVİZYON 3:** bu bölümün ilk hâli iki yerde yanlıştı, denetim yakaladı, ölçüp düzelttim.
> (a) Gidiş ve dönüşü 145'er bayt saymıştım; **ACK aslında çok daha küçük**. (b) Kalan süreyi
> tamamen TDM sayıp `MAX_WINDOW` ile orantılı küçültmüştüm; kalanın içinde **işleme süresi (P)**
> de var ve o pencereden etkilenmez.

**Gerçek çerçeve boyları (ölçüldü, `comms/protocol.py` + `mavlink_tunel.py:23` "paket = 17 + payload_length"):**

| Yön | NAVITAS çerçevesi | Tünel parçası | MAVLink2 paketi |
|---|---|---|---|
| Gidiş (prob, `CMD RF_PROBE`) | 123 B | 1 | **145 B** |
| Dönüş (`ACK`) | **77 B** | 1 | **99 B** |

**Varsayımlar:** seri hat 8N1 = 10 bit/bayt; yol `RFD(hava)→TELEM1` + `Pixhawk→TELEM2→Jetson`,
dönüşte aynısı = 4 seri geçiş; Pixhawk'ın dahili yönlendirmesi ihmal.

| Bileşen | Süre | `MAX_WINDOW`'dan etkilenir mi |
|---|---|---|
| **Seri hatlar** (gidiş 2×145 B + dönüş 2×99 B @57600) | **84,7 ms** | ❌ hayır |
| RF havada (244 B @128 kbps) | 15,2 ms | ❌ hayır |
| **Kalan = W + P** (TDM beklemesi **+ işleme**) | **131,0 ms** | kısmen (yalnız W) |
| **Ölçülen baseline p95** | **231 ms** | |

⚠ Kalanın **tam 131 ms** çıkması ile `MAX_WINDOW`'un 131 olması **rastlantı olabilir**; D-479 tam
böyle bir örtüşmeyi (262 ↔ 265) nedensellik sanmanın hatası olarak kaydetti. Buradan nedensellik
**çıkarılmıyor**.

### 7.1 ÖN KAYIT — TEK SAYI DEĞİL, ARALIK

`P` (işleme süresi: MAVProxy, `seri_hub`, çerçeve birleştirme, Pixhawk yönlendirme) **ölçülmedi**.
`MAX_WINDOW` yalnız `W`'yi küçültür, `P`'yi değil. Bu yüzden beklenti bir aralıktır:

`T(MW33) = 84,7 + 15,2 + P + (131,0 − P) × 33/131`

| Varsayılan `P` | Beklenen p95 | Eşik 200 ms |
|---|---|---|
| 0 ms (**iyimser alt sınır**) | ≈ **133 ms** | geçer |
| 20 ms | ≈ 148 ms | geçer |
| 40 ms | ≈ 163 ms | geçer |
| 60 ms | ≈ 178 ms | geçer |

**Yani 147 ms "beklenen değer" değil, P≈20 ms varsayımının değeridir.** Aralığın tamamı eşiği
geçiyor. Matematiksel sınır: `T = 132,9 + 0,748·P`, yani eşik **`P < 89,7 ms`** iken tutar;
güvenli marjla **`P < 85 ms`** kabul edilebilir.

**Sınama kuralı (düzeltildi):** ölçüm **133–180 ms** bandına düşerse model tutarlıdır.
**> 200 ms** çıkarsa ya `P` sandığımızdan büyüktür ya da TDM davranışı doğrusal değildir
(SiK'in TDM'i **uyarlamalıdır**, doğrusal küçülme garanti değil). O durumda sıradaki iş ayar
değiştirmek değil, **RTT'yi ölçerek parçalamaktır**: Jetson'da `seri_hub`'ın çerçeveyi alma ve
yanıtı yollama zaman damgaları kaydedilirse `P`'nin hava yarısı doğrudan çıkar.

### 7.1b ✅ ÇELİŞKİ ÇÖZÜLDÜ (19 Eyl ~05:00) — topoloji kayıtta bulundu

Belirsizliğin kaynağı **yanlış aktarımdı**: "Pixhawk yolu olmadan" denen ölçüm aslında
**Jetson olmadan** yapılmış. D-494 madde 3 (tünel dalı) aynen şöyle:

> *"**AYRIM 1 (18:56): PC→RFD→Pixhawk PARAM_REQUEST_READ** 120 prob: cevap 115/120 (%4 kayıp),
> RTT p50 154 / **p95 231 ms** → telsiz yolu sağlam; kayıp Pixhawk→TELEM2→Jetson legindedir."*

Yani Pixhawk testin **içinde** (cevabı veren o); yok olan **Jetson ve TELEM2 bacağı**. Dolayısıyla
o ölçümde **2 seri geçiş** var (TELEM1 gidiş+dönüş), 4 değil.

**İki testin bütçesi (aynı yöntem, farklı topoloji):**

| Test | Topoloji | Mesaj | Seri | RF | **Kalan = TDM + işleme** |
|---|---|---|---|---|---|
| AYRIM-1 · 231 ms | PC→RFD→Pixhawk (Jetson YOK) | 37/42 B | **13,7 ms** | 4,9 ms | **212 ms (%92)** |
| K8a · 268 ms | tam zincir (Jetson dahil) | 145/99 B | **84,7 ms** | 15,2 ms | **168 ms (%63)** |

**Görünürdeki tuhaflık:** küçük mesajlı testte "kalan" **daha büyük** (212 > 168). Bu, ikisini
uzlaştıran bir okuma veriyor — **kalan tek bir şey değil, TDM + o yola özgü işleme**:

* AYRIM-1'de işleme = **Pixhawk'ın PARAM_REQUEST_READ'i işleyip PARAM_VALUE üretmesi** (ArduPilot
  bunu anında değil kendi döngüsünde yapar);
* K8a'da işleme = MAVProxy + `seri_hub` + çerçeve birleştirme.

Ortak TDM'yi `W ≈ 150 ms` varsayarsak: 150 + 62 (param işleme) = 212 ✅ ve 150 + 18 (hub işleme)
= 168 ✅. **Hipotez iki bağımsız ölçümü de açıklıyor** — ama hâlâ hipotezdir, `W` doğrudan
ölçülmedi.

**Sonuç:** 84,7 ms'lik UART bütçesi **K8a'ya** aittir ve oraya doğru bağlanmıştır; 231 ms'ye
bağlanmamalıydı, artık bağlanmıyor. Her iki testte de **baskın bileşen TDM'dir** — yani
`MAX_WINDOW` doğru hedeftir.

**MW33 sonrası (kalan oranlı düşerse, iyimser):** AYRIM-1 ≈ 72 ms · K8a ≈ **142 ms**. Bu,
§7.1'deki 133–178 ms bandıyla tutarlı.

### 7.2 🔴 Yedek kaldıraç: TELEM baud (reddedilme gerekçesi eksikti)

Emir tarafı "TELEM2 baud yükseltme yapılmayacak: **TELEM2 artık doygun değil**" dedi. Doygunluk
gerçekten çözüldü (akış sıfırlama, %54 → %3,5) — ama **doygunluk ile gecikme aynı şey değildir**:

* **Doygunluk** = hat kapasitesinin dolması → paket düşmesi. Çözüldü.
* **Gecikme** = bir paketin bayt bayt hattan geçme süresi. 145 B @57600 = **25,2 ms**, hat boş
  olsa bile değişmez. Dört geçişte **101 ms**.

Yani baud yükseltmenin gerekçesi doygunluk değil, **bayt süresi**. Hat boşken de kazanç sağlar.
⚠ Karşı tarafta dikkat: `SERIAL1_BAUD`/`SERIAL2_BAUD` değişirse MAVProxy ve RFD'nin seri hızı da
eşitlenmeli; uyumsuzlukta bağlantı tamamen kesilir. Bu yüzden **MW33'ten sonra** sıra alır.

### 7.2b ⚠ ÜÇ KAVRAM KARIŞTIRILMAMALI (denetim düzeltmesi)

1. **K8 bir yarışma şartı DEĞİLDİR** — kendi iç kabul testimizdir. Ama şartnamenin gerçek
   gereksinimini (gerçek zamanlı aktarım + hakem onayı) temsil eder. "K8 düştü" demek "yarışma
   kuralı ihlal edildi" demek değil; "kendi eşiğimizi tutturamadık" demektir.
2. **`MAX_WINDOW = 131` "her paket 131 ms bekler" DEMEK DEĞİLDİR.** TDM'nin **azami gönderim
   penceresini** sınırlar ve SiK'in TDM'i **uyarlamalıdır**. Bu yüzden 131 → 33 yapınca
   gecikmenin tam 98 ms azalması **beklenmemelidir**; §7.1'deki oranlı model bir **yaklaşımdır**,
   fizik yasası değil.
3. **"Kaybolmadı, geç geldi" ≠ "sorun yok".** K8 açısından **zaman aşımından sonra gelen cevap da
   başarısız denemedir.** Geç ACK ayrımı **fiziksel teşhis** için kritiktir (RF sorunu mu, sıra
   beklemesi mi), ama kapı hükmünü yumuşatmaz.

### 7.3 Sonuçlar gelince NASIL OKUNACAK (yorumlama kuralları)

**Kapı ile model AYRI şeylerdir; karıştırılmamalı:**

| | Ölçüt | Anlamı |
|---|---|---|
| **KAPI** | p95 **< 200 ms** | K8 geçer/geçmez. Tek bağlayıcı eşik budur |
| **MODEL** | p95 **133–178 ms** bandı | Bileşen bütçesinin tutup tutmadığı |

→ Sonuç **bant dışı ama < 200 ms** ise: **K8 GEÇER**, model eksiktir. İkisi ayrı yazılır;
"model tutmadı" diye kapı düşürülmez, "kapı geçti" diye de model doğru sayılmaz.

**Üç şeye bakılacak:**

1. **Asıl etki = yeni baseline → MW33 farkı (delta).** MP hızları düşürüldükten sonraki baseline
   ile MW33 sonrası ölçümün farkı, `MAX_WINDOW`'un **tek başına** katkısıdır. 231 ms ile
   karşılaştırmak yanıltıcıdır (arada MP değişikliği var).
2. **p95 tek başına yetmez — p99 ve maks da.** Kuyrukta hâlâ 0,5 s'yi aşan sıçramalar varsa
   sorun çözülmemiştir: bu turun asıl bulgusu zaten "geç ACK" idi, yani dağılımın kuyruğu.
   `zaman_asimi` sayısı ayrıca yazılır.
3. **Model eksikse sıradaki iş ayar değil ölçüm:** `seri_hub` zaman damgalarıyla `P`'nin hava
   yarısı doğrudan çıkarılır (§7.1).
