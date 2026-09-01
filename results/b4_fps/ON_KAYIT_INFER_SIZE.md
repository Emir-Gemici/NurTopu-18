# D-374 kaldıraç 1 — `INFER_SIZE` 512 → 640 · ön kayıt

Tarih: **2026-09-01** — hiçbir 640 sonucu üretilmeden önce yazıldı (D-107).

## 0. Soru ve niçin şimdi

D-374 ölçtü: R'nin ≥30 m katmanında en uzun başarısız koşu **51 s** (tazelik
eşiği 5 s) ve hüküm **SAHNE_BAGINTILI** — *FPS artırmak çözmez*. Ön kayıt §6'da
kaldıraçlar önceden yazılmıştı; **kaldıraç 1** çözünürlüktür.

FPS payı var: gereken **0,41** (en kötü uçuşta 0,61), beklenen band 0,9–2,6.
640'ın maliyeti bu payı yiyebilir — bu yüzden fayda **ve** maliyet birlikte
ölçülür.

⚠ Bu bir **ölçümdür, karar değildir.** 640'a geçmek üretim sözleşmesini
(kayıt defteri `imgsz`) değiştirir; **mimar kararıdır**. Burada yalnız kanıt
üretilir.

## 1. Kümeler

| ad | ne | n |
|---|---|---:|
| **K** | D-374'te koşu uzunluğu ≥5 olan **kör kareler** (`kor_kareler.json`) | 250 |
| **R** | gerçek DJİ, ≥30 m katman (D-374 ile aynı) | 633 |
| **S** | sentetik arena kabul kümesi | 260 |

K, hedefli tanı kümesidir: 512'de **tanım gereği hepsi başarısız**. Bu yüzden
K'da 512 kolunun `p`'si **sıfırdır ve ölçülmez** — kıyas tabanı sabittir.

## 2. Dondurulan yöntem

- Zincir D-374 ile birebir aynı (`163`'ün karar halkası); tek değişen
  `model.predict(..., imgsz=…)`.
- Ölçek **değişmez**: `mpp` içerik genişliğinden hesaplanır ve `imgsz`'den
  bağımsızdır. FOV **67,3** (EK-1'de donduruldu).
- ⚠ **Maskeler `sq` çerçevesine geri ölçeklenir**; `analyze_path` her iki kolda
  da aynı tuval çözünürlüğünde çalışır. Yani ölçülen fark **algıdan** gelir,
  karar geometrisinin çözünürlüğünden değil.
- Model **v36** (defterden). 640, defterde **kayıtlı değildir**; bu koşum
  kayıt dışı bir yapılandırmanın ölçümüdür ve öyle raporlanır.

## 3. Eşikler — SONUÇ GÖRÜLMEDEN yazıldı

- **I1 · AYIRT EDİCİ TANI (K):** 640'ın kör karelerde ürettiği `p_K`.
  - `p_K = 0` → hüküm **COZUNURLUK_KALDIRAC_DEGIL**: körlük çözünürlükten
    değil **alan dışılıktan** (OOD) geliyor; kaldıraç 2/3'e geçilir.
  - `p_K > 0` → çözünürlük kısmen çalışıyor; ölçülen değer raporlanır.
  - ⚠ Bu bir kapı değil **tanıdır**; "yüksek çıkarsa iyi" diye eşik
    gevşetilmez.
- **I2 · GERİLEME YASAĞI (S):** `p_S(640) ≥ p_S(512) − 0,02`. Ayrıca S'te yer
  gerçeği var: **doğru→yanlış** çeviren kare sayısı ayrıca sayılır ve
  raporlanır (F1 kalıbı). I2 düşerse 640 **reddedilir**, I1 ne olursa olsun.
- **I3 · ASIL KAPI (R):** ≥30 m katmanında en uzun koşu **< 5 s** ise G1
  geçer ve 640 tek başına yeterlidir. Aksi hâlde **yetmez** — ölçülen yeni
  koşu uzunluğu raporlanır.
- **I4 · FPS BÜTÇESİ:** çıkarım-yalnız süre iki kolda ölçülür (aynı kareler,
  aynı süreç). Maliyet oranı `c = t640 / t512`. Jetson bandının alt ucu
  0,9 FPS varsayımıyla 640'ın etkin FPS'i `0,9 / c`; bu değer D-374'ün
  **gerekli 0,41** eşiğinin altına inerse hüküm **FPS_BUTCESI_YETMEZ**.
  ⚠ `c` PC'de ölçülür; Jetson'da aynı olacağı **varsayılmaz**, oran bir
  **gösterge**dir ve Gün-1'de gerçek sayıyla değişir.

## 4. ÖLÇÜLEMEDİ kuralları

- Bir kümede kare okunamazsa o küme **OLCULEMEDI**; eksik payda sessizce
  geçişe çevrilmez.
- `p_K` yorumu K kümesinin **kendi kapsamıyla** sınırlıdır: bunlar 512'nin
  başarısız olduğu kareler; **seçilmiş bir alt kümedir** ve genel `p`
  yerine geçmez.

## 5. Karar sırası (sonuç ne çıkarsa çıksın)

I2 düşerse → **RED**. I2 geçer ve I3 geçerse → mimara **öneri** (sözleşme
değişikliği + kayıt defteri + yeniden kabul zinciri gerekir). I3 düşerse →
640 tek başına yetmez; kaldıraç 2 (ikinci geçiş) ve 3 (tazelik damgası)
birlikte değerlendirilir.

---

# EK-1 — 🔴 R KÜMESİNDE EĞİTİM KARESİ SIZINTISI (2026-09-01, **166 sonucu görülmeden** yazıldı)

## E1.1 Bulgu

R'nin ≥30 m katmanı (633 kare) `kareler_irtifa.json`'dan kurulmuştu; **eğitim
kümesiyle kesişimi denetlenmemişti.** Denetledim (girdi metaverisi, model
çıktısı değil):

```text
dji_v7 (v36'nin gercek-kare egitim kumesi) : 486 benzersiz kare
katmandaki 633 karenin 390'i (%62) BU KUMEDE
  egitimde  n=390  p=0,574  MASKE_YOK %8
  disinda   n=243  p=0,346  MASKE_YOK %44
```

CONTRACTS §12 zaten 0038'i ayırıyordu; kusur bende: R'yi kurarken bu ayrımı
**uygulamadım**. D-280'in *"ortak kaynak 0 (fail-closed geçti)"* disiplini
vardı ve ben kullanmadım.

## E1.2 Bu ön kayıt için sonucu

- **R_TEMIZ** tanımlanır: katmandaki kareler **eksi** `dataset/dji_v7`
  (train+val) kareleri → **n = 243** (0038'in 230'u + 0037'den 6 + 0039'dan 7).
- **I1, I3 ve I4 hükümleri R_TEMIZ üzerinde verilir.** Kirli havuz (633)
  yalnız **bağlam** olarak raporlanır, hükme katılmaz — EK-2'deki katman
  kuralının aynı kalıbı.
- **I2 değişmez** (S kümesi sentetiktir, sızıntı sorusu orada yoktur).
- 166 koşumu **yeniden koşulmaz**: JSON kare kare kayıt tutuyor; hüküm
  kayıtlardan **yeniden hesaplanır**.

## E1.3 Kapsam uyarısı

R_TEMIZ'in %95'i (230/243) tek uçuştan — **0038**'den — gelir. Yani R_TEMIZ
pratikte *"tek sahne-ayrık uçuş"* demektir; uçuşlar arası değişkenlik
**ÖLÇÜLEMEDİ** kalır ve tek sayı bir dağılım gibi okunmaz.
