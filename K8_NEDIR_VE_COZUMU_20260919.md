# K8 NEDİR, NEDEN DÜŞTÜ, NASIL ÇÖZÜLÜR

**Tarih:** 19 Eylül 2026 (gece) · **Yazan:** Claude 1 (mimar) · **Dal:** `master`
**Neden bu belge:** kullanıcı *"K8 nedir nasıl çözülür'e odaklanalım"* dedi. Aşağıdakiler
ölçümlere dayanır; her hesabın dayanağı yazılıdır.

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

🔴 **Ve K8 tam da buraya çarpıyor:** şartname *"veri akışının sağlanamadığı durumlarda uçuş
geçersiz sayılacaktır"* diyor. K8'deki rota kaybı teknik bir aksaklık değil, **doğrudan 0 puan**
riskidir.

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
yokken bile p95 **231 ms** ölçüldü. Yani gecikme yazılımdan değil, telsizin gönderim
penceresinden geliyor. Emir tarafının araştırması: pencere şu an **62 ms** (otomatik), 33 ms'ye
indirilirse gidiş-dönüş turu 132 → 73 ms, beklenen p95 **170–180 ms**. Verim ~%10 düşer,
**menzil değişmez**.

**(c) Parça boyu telsizin taşıma sınırını aşıyor — ROTA KAYBININ ASIL SEBEBİ.** Telsiz bir MAVLink
çerçevesini ancak **payload ≤ 93 bayt** ise tek pakette taşıyor. Bizim tünel parçalarımız
**128 bayt** (`TUNEL_MAVLINK_YUK_B`), yani **her parça iki telsiz paketine bölünüyor**.

### 3.1 Bu teşhis sayısal olarak DOĞRULANDI (bu oturumda, bağımsız)

Gerçek `open_route` çerçeveleri üretilip ölçüldü (`comms/protocol.py` ile, uydurma değil):

| Yol noktası | Çerçeve | Tünel parçası | Telsiz paketi | P(tek deneme) |
|---|---|---|---|---|
| **30** | **469 B** | 4 | **8** | **0,569** |
| 20 | 349 B | 3 | 6 | 0,655 |
| 14 | 277 B | 3 | 6 | 0,655 |
| 10 | 229 B | 2 | 4 | 0,755 |
| 6 | 185 B | 2 | 4 | 0,755 |

Paket başına kayıp `p = %6,8` alındığında 30 noktalı rota için teslim olasılığı **0,569**,
yani kayıp **%43,1** — **sahada ölçülen %43 ile birebir.** Teşhis doğru.

## 4. Çözümler ve ölçülebilir etkileri

| # | Çözüm | Etkisi | Kim / ne zaman |
|---|---|---|---|
| 1 | **MP telemetri hızlarını düşür** (Attitude 1, Position 2, Mode/Status 1, RC 0, Sensors 0, Extra 1) — `Config → Planner` ekranından. ⚠ `SR1_*` parametresini elle yazmak **tutmaz**: MP her bağlanışta kendi hızlarını yeniden ister | Paket kaybı `p` düşer → tüm satırlar iyileşir | Emir, sabah |
| 2 | **Max Window 131 → 33 ms** (iki telsizde birden, MP SiK ekranından) | p95 268 → **170–180 ms** (hesap) → K8 eşiği geçilebilir | Emir, sabah |
| 3 | ~~Air Speed 128 → 250~~ | **YAPILMAYACAK**: menzili düşürür, menzil hiç ölçülmedi (T271) | — |
| 4 | **Tünel parça boyu 128 → 88 B** (T287) | 30 noktalı rota: 8 → 6 paket, P 0,569 → **0,655** | Sözleşme+test değişikliği, **uçuş sonrası** |
| 5 | 🆕 **Yol noktası sayısını azalt** (`WP_ARALIK_M` 2,0 → 4–5 m) | 30 → ~10 nokta: 8 → **4 paket**, P 0,569 → **0,755** | Kod değişikliği; FDA için **düşük riskli** (aşağıya bak) |
| 6 | **Tekrar** (`KararYayinci`, hâlihazırda 4 tekrar) | P 0,569 → **0,966** (en az biri ulaşır) | Zaten çalışıyor |

### 4.1 5 numara neden düşük riskli — ve neden asıl yarışmada dikkat ister

Yol noktaları 2 m aralıkla üretiliyor (`costmap_path_finder.WP_ARALIK_M = 2.0`). Bu sıklık
**İKA'nın güzergâhı takip etmesi** için konmuştu. Ama **§5.3.2 test uçuşunda İKA yok** — güzergâh
yalnız YKİ'de gösterilip hakeme onaylatılıyor. Dolayısıyla bu uçuş için seyrek nokta yeterlidir
ve mesajı yarıya indirir. Asıl yarışmada (İKA varken) aynı gevşetme **yapılmamalıdır**.

### 4.2 Birleşik etki (hesap)

| Senaryo | Paket | P(tek) | P(4 tekrar) |
|---|---|---|---|
| Bugün (30 nokta, 128 B parça) | 8 | 0,569 | 0,966 |
| + parça 88 B (T287) | 6 | 0,655 | 0,986 |
| + 10 yol noktası | **3** | **0,810** | **0,999** |

Not: 1 ve 2 numara `p`'nin kendisini düşürdüğü için bu satırların **hepsini** ayrıca iyileştirir.

## 5. Önerilen sıra (sabah)

1. **MP hızları** → 100 problük kısa ölçüm
2. **Max Window 33** → 100 problük ölçüm (beklenti p95 170–180 ms, **ön kayıt**)
3. Hâlâ eşik tutmuyorsa → **yol noktası seyrekleştirme** (madde 5; FDA'da İKA yok, risksiz)
4. Parça boyu (T287) uçuş sonrasına kalsın — sözleşme + test + benzetim işi

**Eşik gevşetilmez** (ön kayıtlı). Hedef tutmasa bile uçuş yapılabilir: komutlar ve hakem onayı
20 tekrarla güvenilir, rota gecikmeli gelebilir, **tutanağa yazılır**.

## 6. Bu belgenin ölçüm dayanakları
- D-494 (tünel dalı) — saha ölçümü, K8a/K8b/473 B
- Bu oturum — `comms/protocol.py` ile gerçek çerçeve boyutları ve teslim olasılıkları
- `comms/mavlink_tunel.py` (tünel dalı) — `TUNEL_MAVLINK_YUK_B = 128`, parça yükü 123 B
- `codes/costmap_path_finder.py:117` — `WP_ARALIK_M = 2.0`
- Şartname §5.3.2 ve İHA-UB tanımı — `Ileri_Otonom_Sistemler_..._Sartname_TR_Ltktw.pdf`
