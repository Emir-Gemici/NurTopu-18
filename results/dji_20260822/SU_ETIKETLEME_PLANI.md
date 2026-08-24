# SU ETİKETLEME PLANI — ölçümle kurulmuş

> **Yazan:** Claude 2 (başamele) · 2026-08-22 · **karar mimarın/insanın (D-133)**
> **Tetikleyen:** kullanıcı talimatı *"suyu etiketle, planını çıkar"*.
> ⛔ Bu plan **uygulanmadı**. Etiketleme başlamadan önce §3'ün ön kaydı ve
> §4'ün şartname doğrulaması **zorunludur**.

---

## 1. ÖLÇÜM ZEMİNİ — plan neye dayanıyor

### 1a. 🔴 Su GERÇEKTEN sürülebilir sanılıyor (görsel + sayı, D-80)
Üretim modeli **v35**, yeni gündüz çekiminin su içeren karelerinde
`rpi_inference` üretim yolundan koşuldu (`results/dji_20260822/su_bindirme/`):

```text
kare                                zemin orani   gozle dogrulama
0039_t0000                             0,113      YESIL POLIGON SU KANALININ USTUNDE
0038_t0000                             0,024      YESIL POLIGON SU KENARI SAZLIGINDA
0038_t0231                             0,000      hic zemin yok
0039_t0078                             0,000      hic zemin yok
```
İki karede "sürülebilir" çıktısı **doğrudan suya ve su kenarına** düşüyor.
O maskeden üretilecek rota İKA'yı **kanala sokar**.

### 1b. ⚠ AMA su zaten ETİKETLİ — sorun YOKLUK değil AKTARIM
İlk raporumda *"karışımda su hiç etiketlenmemiş"* demiştim; **yanlıştı.**
`scripts/olcum/57_t54_engel_eslemesi.py:44` — T54/D-67 düzeltmesi:
```text
ESLEME = {0:0, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1}
             ^-- 2 water -> 1 blocked        ^-- 9 pool -> 1 blocked
```
RescueNet'in suyu **engel** olarak eğitimde var. Kusur o hâlde şudur:
**afet/sel görüntüsündeki geniş su, 30 m nadirden dar sulama kanalına
AKTARILMIYOR.** Plan bunu hedefler; "eksik sınıfı eklemeyi" değil.

### 1c. 🔴 İkinci ve DAHA BÜYÜK kusur: yol da görülmüyor
İlk belirti 4 karede zemin oranının **0,000–0,113** olmasıydı. **768 karenin
tamamında ölçüldü** (`uretim_yolu_olcumu.json`, üretim yolu, 2 model, ~1,8 saat):

```text
model            MASKE_YOK        rota URETTI      diger sebepler
v35 (uretim)   395/768  %51,4   238/768  %31,0   UC_BANT_TEMAS_YOK 132
v34 (yedek)    416/768  %54,2   253/768  %32,9   UC_BANT_TEMAS_YOK  92
```
🔴 **Üretim modeli bu domende karelerin YARISINDAN FAZLASINDA hiçbir zemin
maskesi üretmiyor.** Yedek v34 daha da kötü. Bu, planın şeklini değiştirir —
§3'e bakınız.
⚠ Bu bir **domain** ölçümüdür, arena performansı hakkında hiçbir şey söylemez;
arenayı bozup bozmadığı ancak kabul zinciriyle ölçülür (§6).

### 1d. Küme ve alan
768 kare (300 + 246 + 222), 1 fps, algısal hash ile dedup.
Parlaklık kapısı **ORTUSUYOR** (medyan 125,8 · referans 128,7).
GPS kutuları (hesaplandı, `du`/elle değil):
```text
0037 ∩ 0038 =     0 m²   (HIC ORTUSMUYOR)
0037 ∩ 0039 = 34.498 m²  (0037'nin %100'u 0039'un icinde -> AYNI ALAN)
0038 ∩ 0039 =    589 m²  (0038'in %1,5'i)
```

---

## 2. KARAR: su = **sınıf 1 (blocked)**, sözleşme DEĞİŞMEZ

- `CONTRACTS.md:19-20` sözleşmesi `{0: traversable, 1: blocked}`; **nc=2 kalır.**
- Su **yeni sınıf id ALMAZ.** Gerekçe: etiketin beslediği karar *"rota buradan
  geçmesin"*dir; su bu açıdan moloz ile aynı kategoridedir. Yeni id
  `CONTRACTS.md` + registry + kabul zinciri + Jetson paketini birden değiştirir
  ve **mimar kararı** gerektirir; güvenlik için **gerekli değildir**.
- **Anayasa madde 15 uyumu:** suyu engel yazmak serbest alanı **KÜÇÜLTÜR**.
  `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` korunur. Büyüten hiçbir işlem yok.

---

## 3. 🔴 YALNIZ SUYU ETİKETLEMEK YETMEZ — ve tek başına ZARARLI olabilir

§1c ölçümü (768 kare): model bu domende karelerin **%51,4'ünde hiç zemin
maskesi üretmiyor** ve yalnız **%31'inde** rota çıkarıyor. Yalnız suyu "engel"
diye eklersek serbest alan **daha da** küçülür ve kalan %31 de kapanır.

Bu **güvenlidir** (fail-closed, D-277 §3) ama **işe yaramaz**: İKA duracaktır.

⇒ Etiketleme **iki sınıfı birden** üretmek zorundadır:
1. **sınıf 0** — gerçekten sürülebilir zemin (stabilize/toprak yol, sıkışmış
   düzlük). Otorite katmanı budur.
2. **sınıf 1** — su, su kenarı sazlık, şev, hendek, derin tekerlek izi.

⚠ Bu, talimatın kapsamını **genişletme** değil, talimatın **çalışabilmesi**
için gereken asgari kapsamdır. Ölçüm bunu göstermeseydi yazmazdım.

---

## 4. ŞARTNAME — planın EN KRİTİK parçası (D-273'ün dersi)

D-273 §2'de ölçüldü: üç ajan birbiriyle **0,88**, referansla **0,55** uyuştu —
ve ajanlar **haklıydı**; belirsiz olan şartnameydi. Su tanımı çatıdan **daha**
kaygandır. Bu yüzden şartname **önce yazılır, sonra sınanır, sonra ölçeklenir.**

### 4a. Şartnamenin cevaplamak ZORUNDA olduğu sorular
Her biri gerçek karelerde görüldü; cevapsız bırakılırsa ajanlar tutarlı ama
yanlış çözer:

| # | soru | neden kaygan |
|---|---|---|
| S1 | Su yüzeyi mi, **su + kıyı bitki örtüsü** mü? | 0038'de model tam sazlığa bastı; sazlık su kadar geçilemez |
| S2 | **Gölge** ile su nasıl ayrılır? | ikisi de koyu; 0039'da ağaç gölgesi kanala bitişik |
| S3 | Yoldaki **su birikintisi/ıslak çamur** hangi sınıf? | sığ birikinti geçilebilir, hendek değil — sınır nerede |
| S4 | **Menfez/köprü tabliyesi** hangi sınıf? | 0039_t0078'de beton tabliye suyun ÜSTÜNDE ve **geçilebilir** |
| S5 | Çözünürlük altı dar ark (< ~15 px) ne olur? | D-210 kuralı: **"olabilir" diye işaretlenmez**, etiketsiz bırakılır |
| S6 | Poligon **kapalı mı**, delik açılıyor mu? | insan görevindeki kural: zemin poligonu bütün çizilir, delik açılmaz |

### 4b. Şartname ÖNERİSİ (mimar onayına — ÖNER-BEKLE)
> **Sınıf 1 (engel) çizilir:** açık su yüzeyi **ve** su ile kara arasındaki
> geçilemez kıyı şeridi (sazlık, sık bitki, dik şev) **tek bütün poligon**
> olarak. Ayrım noktası: *"İKA buraya girerse çıkabilir mi?"* — çıkamıyorsa
> engeldir. Gölge, altındaki yüzey **okunabiliyorsa** o yüzeyin sınıfını alır;
> okunamıyorsa **etiketsiz** bırakılır (D-210). Menfez/köprü tabliyesi
> **sınıf 0**'dır; altındaki su görünse bile tabliye sürülebilir. Yol üstündeki
> su birikintisi, **çevresindeki yol dokusu kesintisiz devam ediyorsa**
> sınıf 0; kenarları çökmüş/oyulmuşsa sınıf 1.

⚠ Bu **öneridir**. Onaylanmadan pilot başlamaz.
**Kullanıcı 2026-08-22'de onayladı; F3 kapısı bu hâliyle geçti (U1 0,910 · U2 0,899).**

### 4b-EK · DÖRT CÜMLE NETLEŞTİRİLDİ (2026-08-23, kullanıcı talimatı)

F3'te **üç amele de bağımsız olarak aynı dört boşluğu** bildirdi. Kapı geçti ama
uyum şartname söylediği için değil **üçü de aynı akıl yürüttüğü için** çıktı;
8 karede tuttu, 200+ karede tutacağının garantisi yok. Dördü de **ölçümle**
kapatıldı:

**(1) Kıyı şeridinin DIŞ SINIRI — sabit genişlik değildir.**
> Sınır, geçilemez örtünün bittiği ve **sürülebilir zeminin başladığı** yerdir;
> gerekirse kare kenarına kadar uzar. **Mesafe ölçütü kullanılmaz.**

*Ölçüm:* A, şeridin sudan uzaklığını p50 **24–65 px**, maks **108–268 px**
buldu (960 ölçeği). Sabit genişlik varsayan bir amele bu karelerde bambaşka
maske üretirdi; üçü de mesafe yerine geçilebilirliği aldığı için uyuştular.

**(2) "< ~15 px" kuralı ETİKET ÖLÇEĞİNDE ölçülür.**
> Çözünürlük kuralı **960×540 etiket ölçeğinde** uygulanır, ham karede değil.
> Etiket ölçeğinde **15 pikselden dar** yapılar **etiketsiz** bırakılır.

*Gerekçe (ölçüldü):* aynı ark **6 px @960 · 24 px @3840** (C) ve
**13,7 px @960 · 54,7 px @3840** (A). Aynı kural bir ölçekte etiketsiz,
diğerinde etiketli yapıyordu. Etiket 512–768 piksel girdide eğitime giriyor;
960'ta 15 pikselin altındaki yapı orada **8 pikselin altına** düşer.

**(3) SU GÖRÜNMESE de geçilemez hendek/ark SINIF 1'dir.**
> Belirleyici ölçüt **geçilebilirliktir**, suyun görünürlüğü değil. Kenarları
> dik ve İKA'nın çıkamayacağı kuru ark/hendek **sınıf 1**'dir — ama ancak
> yapı **etiket ölçeğinde ≥15 px** ve kenar profili **okunabiliyorsa**;
> okunamıyorsa **etiketsiz**.

*Neden gerekliydi:* A'nın notu — bu karede çatışma **tesadüfen** çözüldü
(13,7 px < 15 px). Ark daha geniş olsaydı **şartnamenin cevabı yoktu.**
Madde 15 uyumu: geçilemezi engel yazmak serbest alanı **küçültür**.

**(4) SUYA BİTİŞİK OLMAYAN geçilemez örtü de SINIF 1'dir.**
> Sınıf 1'in tanımı *"suya bitişik olmak"* değil **"geçilememek"**tir.
> Sık ağaçlık, çalılık, dik şev — suya değmese de **sınıf 1**. Su bu turda
> yalnızca **öncelikli örnektir**, tanımın kendisi değil.

🔴 *Bu, mevcut veriyle TUTARLILIĞI GERİ GETİRİR:*
`scripts/olcum/57_t54_engel_eslemesi.py:44` → `ESLEME = {0:0, 1..9:1}` —
RescueNet'te **ağaç (8), bina, su (2), havuz (9) hepsi sınıf 1**. Yani mevcut
eğitim kümesinde geçilemez örtü zaten suya bitişiklikten bağımsız olarak
engeldir. İlk şartnamem bunu **istemeden daraltmıştı**; F3'te üç amele de
harfi harfine uyup ağaçlığı dışarıda bıraktı ve bunu **itiraz olarak** bildirdi.

⚠ **Bu (4) etiketleme yükünü ARTIRIR** (kare 133'ün ~%40'ı ağaçlık). Kapasite
tahmini bu yüzden F4'te **yeniden ölçülecek**; D-273'ün 19,9 kare/saat değeri
çatı etiketlemesinden geliyordu ve bu iş daha ağır olabilir.

### 4c. Şartname DOĞRULAMASI — kapı
3 ajan, **birbirinden habersiz**, **aynı 8 kare**. Ölçülür:
```text
ajanlar arasi IoU medyan  (D-273'te 0,88 cikti)
USTABASI REFERANSINA gore IoU  (D-273'te 0,55 cikti -> SARTNAME KUSURU)
```
🔴 **Kapı kuralı:** ajanlar birbiriyle yüksek, referansla düşük uyuşuyorsa
**şartname hâlâ belirsizdir** → cümle düzeltilir, **ölçeklenmez**.
⚠ Referansı **ben** çizerim ve **ajanlardan önce** çizerim; sonra çizersem
onların yorumuna kayarım.

---

## 5. FAZLAR

| faz | iş | kim | çıktı | kapı |
|---|---|---|---|---|
| **F0** | Ön kayıt yaz (D-107): başarı/başarısızlık ölçütleri, bantlar | başamele | `results/su_on_kayit.md` | eğitim öncesi yazılmış olacak |
| **F1** | Şartname §4b onaylanır | **mimar** | onaylı cümle | — |
| **F2** | Referans: 8 kare **ustabaşı** çizer | başamele | referans maskeler | görsel doğrulama (D-80) |
| **F3** | Şartname sınaması: 3 ajan × aynı 8 kare | ameleler | IoU tablosu | §4c kapısı |
| **F4** | Pilot: 24 kare, **dengeli** dağıtım | ameleler | maskeler + kapasite | 19,9 kare/saat teyidi |
| **F5** | Ölçek: onaylı sayıda kare | ameleler | küme | her partide örneklem denetimi |
| **F6** | Küme + eğitim | başamele | aday | kabul zinciri K0–K5 |
| **F7** | Ölçüm | başamele | rapor | §6 |

⚠ **F4'ün dağıtımı dengeli olacak.** D-273'te 7 ajanın süreleri
`[150, 1150, 12137, 799, 649, 470, 2150]` — **81 kat** yayılım; faz duvar
saatini tek geç kalan belirledi (33,1 → 19,9 kare/saat). Partiler **kare
sayısına göre değil, tahmini poligon yüküne göre** bölünecek.

⚠ **Ajanların kendi önerisi uygulanacak** (D-273 §1, öner-bekle): **25 px
ızgara + kenar vurgulu ön işleme**. Ajanlar 100 px ızgarada gözle x=118 okuyup
piksel profilinde x=170 buldu — **52 px hata** — ve her kenarı OpenCV ile
ölçmek zorunda kaldı. Bir ajan *"25 px + kenar vurgusuyla iş en az 2 kat hızlı
olurdu"* dedi.

---

## 6. 🔴 DOĞRULAMA SORUNU — dürüstçe

Kullanıcı **üç uçuşun da aynı saha** olduğunu bildirdi ⇒ `DOGRULAMA` oturumu
**yoktur**, hat aday **üretemez** (`dji_hatti.py` oturum kapısı, D-256 §5).

Bunun ölçüm sonucu şudur ve saklanmaz:
> Bu veriyle eğitilen bir modelin **arenayı BOZUP BOZMADIĞI** ölçülebilir
> (kabul zinciri K0–K5 + 67 gerçek kare). Ama **kırsal domende İYİLEŞTİRİP
> İYİLEŞTİRMEDİĞİ ÖLÇÜLEMEZ** — o domende bakır küme yok.

**ÖNER-BEKLE (karar mimarın):** §1d ölçümü 0038'in eğitim alanıyla örtüşmesini
**%1,5** buldu; 0037 ile **hiç** örtüşmüyor. 0038'i **alan-ayrımlı ölçüm
kümesi** olarak ayırmak, "sonradan rastgele bölmek"le aynı şey **değildir**.
- ✔ Lehine: gerçek mekânsal ayrım, ölçülmüş (%1,5).
- ✘ Aleyhine: **aynı gün, aynı kamera, aynı ışık, aynı operatör.** Ayrı bir
  doğrulama uçuşunun yerini **tutmaz** ve öyle sunulmaz.
⇒ Önerim: 0038 **ölçüm** kümesi olsun, ama raporlarda **"alan-ayrımlı, oturum-
ayrımlı DEĞİL"** diye etiketlensin. Terfi kararına **tek başına** dayanak olmaz.

**İNSAN GÖREVİ (kuyruğa yalnız mimar ekler — madde 5/9):** farklı bir sahada,
gündüz, gimbal 90°, tek doğrulama uçuşu; `dji/DOGRULAMA/` altına konacak.

---

## 7. TAKVİM — 🔴 F4'te YENİDEN ÖLÇÜLDÜ: **5,1 kare/saat** (19,9 DEĞİL)

D-273'ün 19,9 kare/saat değeri **çatı** etiketlemesinden geliyordu. Madde (4)
(*"suya bitişik olmayan geçilemez örtü de sınıf 1"*) yükü artırdı ve F4'te
yeniden ölçüldü:

```text
OLCULEN kare        : 14  (kalan 10 kare kesintide sure kaybetti)
toplam ajan-saniye  : 9.910
kare basina         : 708 sn   -> ajan basina 5,1 kare/saat
D-273 (cati)        : 261 sn   -> ajan basina 13,8 kare/saat
                                  ORAN: bu is 2,7 KAT AGIR
```

🔴 **Dengeleme yine tutmadı.** Yük vekilim (koridor benzeri piksel oranı)
gerçek etiketleme süresini **öngörmedi**:
```text
A: 8 kare · 7.031 sn · min 117 · maks 3.152  -> 26,9 KAT yayilim
B: 2 kare · 1.357 sn                          C: 4 kare · 1.522 sn
```
D-273'te 81 kat vardı, vekil dengelemeyle 26,9 kata indi ama **hâlâ faz duvar
saatini tek kare belirliyor**. Paralel verim bu yüzden 3×5,1=15,3 değil,
**7,2 kare/saat** (14 kare / A'nın 7.031 sn'si).

**Ölçülen değerle takvim:**
```text
 24 kare (F4)   :   3,3 saat   (olculdu: ~2 saat, kismen onceki oturumdan)
200 kare        :  27,8 saat   (7,2 kare/saat, 3 amele)
768 kare (tumu) : 106,7 saat = 4,4 gun kesintisiz
```
⚠ Plan §7'nin ilk hâli 200 kare için **10,1 saat** diyordu; ölçüm **27,8 saat**
gösteriyor — **2,7 kat**. Bu, T137/D-273'ün **19 Eylül** son güvenli tarihini
doğrudan etkiler ve o tarih **yeniden hesaplanmalıdır** (öner-bekle).
⚠ Dengeleme düzeltilirse tavan 15,3 kare/saat; ama bu **projeksiyondur**,
plana **ölçülen 7,2** kondu.

## 8. RİSKLER

| risk | ölçülen dayanak | karşılık |
|---|---|---|
| Şartname belirsiz kalır, 200 kare yanlış etiketlenir | D-273: ajanlar 0,88 uyuşup 0,55 sapmıştı | §4c kapısı; ölçeklenmeden önce durdurulur |
| Kırsal veri arenayı bozar | karışım ~6.546 kare; 768 kare **%10,5** ekler | kabul zinciri K0–K5 + 67 gerçek kare; bozarsa aday düşer |
| Su etiketi rota üretimini tamamen kapatır | §1c: zemin oranı zaten 0,000–0,113 | §3: iki sınıf birden etiketlenir |
| İyileşme ölçülemez | §6: bakır kırsal küme yok | 0038 alan-ayrımı (öner-bekle) + insan görevi |
| Domain yarışma sahasına uymayabilir | sahne kırsal, istenen "otopark+moloz"du | mimar kararı: bu küme **ek** mi, **yerine** mi |

---

## 9. YETKİ SINIRI — bu turda yapılmayacaklar

`dataset/` altına **kalıcı küme yazılmaz** (mimar onayı olmadan) ·
`config/model_registry.json`'a **dokunulmaz** · eşik **değiştirilmez** ·
`CONTRACTS.md` **değiştirilmez** (§2: gerek yok) · terfi **yok** ·
`codes/` altına **girilmez** · **push YOK** · insan görevi kuyruğa
**başamele tarafından eklenmez** (madde 5/9).
