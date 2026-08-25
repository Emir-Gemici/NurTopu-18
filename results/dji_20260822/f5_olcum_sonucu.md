# F5 ÖLÇÜM TURU — SONUÇ

> **Ön kayıt:** `f5_on_kayit.md` (etiketleme başlamadan yazıldı) ·
> **Ham çıktı:** `f5/{A,B,C}/` (12 maske + raporlar) · `f5_kapasite_kiyasi.json`
> ⛔ Bantlar **değiştirilmedi**. Eğitim yok · `dataset/`'e yazılmadı · push yok.

## 1. SORULAN SORU — cevaplandı

*"Sınıf 0'ı ve 'etiketsiz' ayrımını eklemek ne kadar pahalı?"*
Aynı 12 kare, iki şartnameyle, **eşleştirmeli**:

```text
Eslestirilen kare : 12/12   (elenen 0 — sinif 0 her karede FIILEN cizildi, %9-%80)
MEDYAN ORAN       : 1,20    (ortalama 1,35 — on kayit §3 geregi KULLANILMADI)
ON KAYITLI HUKUM  : <= 1,30 -> "SINIF 0 UCUZ, 14 Eylul yaklasik gecerli"
```

## 2. 🔴 AMA HÜKÜM KIRILGAN — sınırın 0,10 içinde

İki amele (A, B) *"ilk karemin süresi ortak araç inşasını da içeriyor"* diye
**kendiliğinden** bildirdi. Duyarlılık sınaması:

```text
TUM 12 kare                    medyan 1,20  -> "ucuz" bandi
her amelenin ILK karesi HARIC  medyan 1,39  -> "anlamli ek maliyet" bandi
```

⚠ **Ön kayıt "12 karenin medyanı" diyordu; kayıtlı hüküm 1,20'dir** ve öyle
kalır — sonuca göre ölçüt değiştirmek yasak. Ama hüküm **bandın 0,10 içinde**
ve dışlama onu öbür banda taşıyor.

⚠ Üstelik *"ilk kare araç inşası içerir"* iddiası **tek tip değil**:
```text
A: ilk 690 sn · kalan medyan 586 -> 1,18 kat
B: ilk 1023 sn · kalan medyan 607 -> 1,68 kat
C: ilk  753 sn · kalan medyan 784 -> 0,96 kat   <- CURUTUYOR
```
⇒ **Sonuç:** 14 Eylül ayakta, ama **payı neredeyse tükenmiş**. "Sınıf 0 bedava"
diye okunmamalıdır.

## 3. 🔴 ASIL BULGU — KAPASİTE DEĞİL, TUTARLILIK

Aynı 12 kare iki kez etiketlendi. Sınıf 1 alanı ne kadar oynadı:
```text
mutlak fark MEDYAN 0,0610 · MAKS 0,3833 (38 puan)
kat         MEDYAN 1,72   · MAKS 4,64
fark > 0,10 olan kare: 4/12
```
En büyük sapmalar ve **amelelerin kendi teşhisleri**:

| kare | F4 | F5 | kat | amelenin gerekçesi |
|---|---|---|---|---|
| `0037/frame_000086` | 0,131 | 0,514 | 3,93 | **ayakta kuru ot (tussock)** — B: *"madde (4)'te sayılmamış; karar tersine çevrilirse 0,52 → 0,15"* |
| `0039/frame_000206` | 0,056 | 0,258 | 4,64 | **gevşek taş boyutu** — B: *"7–50 cm kayaları sınıf 1 saydım"* |
| `0037/frame_000171` | 0,223 | 0,525 | 2,35 | aynı tussock kararı |
| `0039/frame_000177` | 0,216 | 0,472 | 2,18 | aynı |

🔴 Sapma **rastgele değil**: hepsi **madde (4)'ün KAPSAMI** belirsiz olduğu için.
*"Geçilemez örtü"* tanımı sık ağaçlık/çalılık için netti, ama **ayakta kuru ot**
ve **gevşek taş** için yazılmamıştı. Ameleler kendi içinde tutarlı, şartname
belirsiz — **D-273'ün deseni üçüncü kez.**

⚠ Tek başına tussock kararı bir karede sınıf 1'i **3,5 kat** değiştiriyor.
736 kare bu belirsizlikle etiketlenirse küme **kendi içinde çelişir**.

## 4. AMELELERİN AÇTIĞI YENİ BOŞLUKLAR (hepsi kayıtlı)
1. **Ayakta kuru ot (tussock)** — sınıf 1 mi 0 mı? *(en büyük tek kalem)*
2. **Gevşek taş/kaya** — boyut eşiği yok (7–50 cm aralığı tartışmalı)
3. **Dinamik nesneler (insan, araç)** — şartname anmıyor; kalıcı engel değiller
4. **Yol boyası** — madde (2) *"tanınan yapı"* diyor; boya tanınıyor ama **yapı
   değil**. B ayrımı kendi yaptı.
5. **Şev dikliği** — nadir tek kareden eğim okunamıyor
6. **Otlu ama düz zemin** — *"sınıf 0 = doğruladın"* ama bitki zemini gizlerken
   neyin doğrulama sayıldığı yazmıyor

## 5. 🔴 A'NIN AÇTIĞI YOL — eşikler PİKSELDE değil FİZİKSEL BİRİMDE yazılmalı

Amele A, `kareler_irtifa.json`'daki `rel_alt` (30,7–32,5 m) ile bir otomobil
lastiği çapından **GSD ≈ 1,25 cm/px ham ≈ 5 cm/px @960** tahmin etti.
⚠ **Tahmindir** — kamera FOV'u bilinmediği için bağımsız doğrulanmadı.

Ama sonucu önemli: şartnamenin **15 px** kuralı ≈ **75 cm**'ye karşılık geliyor.
Ve A'nın asıl teşhisi şu: *"ark ~90 cm, karar aslında ARACA BAĞLI."*

⇒ **Öneri (öner-bekle):** madde (2)/(3)/(4)'ün eşikleri pikselden **İKA'nın
fiili yeteneğine** çevrilsin — tekerlek çapı, karın boşluğu, aşabileceği taş
boyu. O zaman *"geçilemez"* bir yorum değil bir **ölçüm** olur. Bunun için
İKA'nın fiziksel ölçüleri gerekir; bende yok.

## 6. HÜKÜM

- **Kapasite sorusu KAPANDI:** sınıf 0'ın ek maliyeti medyan **1,20 kat**;
  14 Eylül ayakta ama payı tükenmiş (§2).
- 🔴 **F5 ÖLÇEĞİ (736 kare) BU HÂLİYLE BAŞLAMAMALI.** Kapasite yeterli, ama
  §3'teki tutarsızlık ölçekte **kendi içinde çelişen bir küme** üretir.
  Önce §4'ün ilk iki maddesi (tussock, taş boyu) karara bağlanmalı — bunlar
  ölçülen sapmanın **baskın kaynağı**.
