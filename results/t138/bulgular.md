# T138 · DJI GECE KARELERİ — ölçüm sonucu

> Ön kayıt: `results/t138/on_kayit.md` (ölçümlerden **önce** yazıldı, D-107).
> Ölçütler sonucu görünce **gevşetilmedi**.

## A) EĞİTİME UYGUNLUK — **DÜŞTÜ**, küme kurulmaz, etiketleme YAPILMAZ

Ön kayıttaki U2 bandı (`0,05 < zemin oranı < 0,95`, iki yönlü) ve eşik
(**≥ 30 kare VE ≥ 2 ayrı klip**):

| model | U2 bandında | ayrı klip | eşik (≥30) |
|---|---|---|---|
| v35 | **8**/569 | 5 | ❌ |
| v34 | **4**/569 | 1 | ❌ |
| v30 | **7**/569 | 1 | ❌ |

**Hüküm (ön kayıt §4):** geçen kare < 30 → **küme oluşturulmaz, etiketleme
yapılmaz.** Kullanıcının yargısı (*"çoğunu kullanmazdım"*) **doğrulandı** ve
ölçüm onu **aşıyor**: "çoğu" değil, **fiilen tamamı**.

⛔ *"Az da olsa etiketleyelim"* YAPILMADI (D-210).

## B) 🔴 BAŞKA BİR İŞE YARIYOR MU — EVET, VE ÖN KAYITTAKİ AĞIR HÜKÜM ATEŞLEDİ

569 kare, üç model, üretim yolu (`analyze_path`, üretimdeki çağrının aynısı):

| model | MASKE_YOK | UC_BANT_TEMAS_YOK | BILESEN_YOK | ZEMIN_MASKESI_SUPHELI | **ROTA ÜRETİLDİ** |
|---|---|---|---|---|---|
| **v35** | 546 | 20 | 1 | 0 | **2** |
| v34 | 542 | 20 | 3 | 1 | **3** |
| v30 | 538 | 23 | 3 | 0 | **5** |

🔴 **Ön kayıtta yazılıydı:** *"rota üretilen kare sayısı sıfır değilse bu CİDDİ
BİR BULGUDUR — sistem, görmesi mümkün olmayan bir görüntüde karar üretiyor
demektir."* **Sıfır değil.**

**6 benzersiz kare** rota üretti; biri (`0033/frame_000094`) **üç modelde de**.
Hepsi **8 waypoint** ve **yayınlanmış bir `yol` numarası** üretti.

### En ağır örnek — ve dürüst okuması
```text
0032/frame_000064_000004740.jpg   L=18,4   ->  YOL=2  guven=1,000  wp=8
```
**GÖRSEL (D-80, ustabaşı baktı):** rota **saçma değil**. Nadir gece karesinde
şeritli bir yol var; model zemin maskesini **asfaltın üstüne doğru oturtmuş**
ve 8 waypoint yolun ortasından geçiyor.

**Tam da bu yüzden ciddi:**
1. Sistem, insanın zor seçtiği bir karede (**L=18,4**, referans min 118,7)
   kararı **güven 1,000** ile yayınlıyor. **Güven, girdinin alan dışı
   olduğuna dair hiçbir sinyal taşımıyor.**
2. Sahne yarışma arenası değil — üzerinde **motosiklet** duran halka açık yol.
   Model "yol benzeri şerit"e genelledi; makul bir davranış ama **alan
   geçerliliğiyle ilgisiz.**
3. İkinci örnek `0033/frame_000094` **güven 0,298** ile geldi — yani güven
   bazen düşük, ama **kural olarak değil**.

### Ama tasarımın büyük kısmı TUTUYOR
**v35 için 567/569 kare reddedildi.** Fail-closed davranış ezici çoğunlukta
çalışıyor; sızan 2 kare **istisna**, kural değil.

### 🔴 MODELLER ARASI SIRALAMA — ölçülmüş ve üretim modeli lehine
```text
rota sizdiran kare (olceksiz):   v35 = 2   <   v34 = 3   <   v30 = 5
```
**v35 üçünün en güvenli çökeni.** Bu, terfi kararını destekleyen **bağımsız**
bir eksendir (kabul zinciri sentetik arenada ölçer; bu ölçüm alan dışıdır).

## C) ÖNERİ — "gece kümesi" bir EMNİYET DOĞRULAMA kümesi olur (ÖNER-BEKLE)

T111 duvarı: **alan dışı etiketli doğrulama kümemiz yok**; bugüne kadarki her
kabul ölçümü eğitim dağılımının **içinde** yapıldı (D-198). Bu 569 kare
**tanım gereği alan dışıdır** ve ölçüm **6 somut karşı-örnek** üretti —
sentetik hiçbir kümenin üretemeyeceği türden.

**Önerilen kullanım (karar MİMARINDIR, kapı DEĞİL):**
> `dji_gece` = **emniyet doğrulama kümesi**. Ölçüt: *"bu kümede rota üretilen
> kare sayısı"*. Etiket **gerekmez** — çünkü doğru cevap **"karar verme"**dir
> ve bu, yer gerçeği olmadan ölçülebilen **nadir** bir ölçüttür.

⚠ Bu bir **öneridir**. Kabul kümesine ekleme, eşik koyma ve terfi kuralına
bağlama kararı **mimarındır** (§9.2).

## D) ÜÇ AYRI PROBLEM — "gündüz çek" gerekli ama YETERLİ DEĞİL
Görsel doğrulamada (D-80) üç bağımsız kusur çıktı:

| klip | L | ne görünüyor | model çıktısı |
|---|---|---|---|
| 0020 | 76,2 | 🔴 **ufuk çizgisi, gökyüzü, tarla — NADİR DEĞİL** | engel %97,4 (gökyüzü dâhil) |
| 0022 | 20,6 | nadir ama neredeyse siyah, sürülmüş toprak | engel %96,6 |
| 0032 | 21,0 | gece yolda yürüyen iki kişi | zemin 0 · engel 0 |

1. **Gece** (569/569).
2. **Gimbal 90° değil** — en az bir klip yatay çekim.
3. **İçerik alan dışı**: tarla, toprak yol, halka açık yol, yayalar. Hedef alan
   **otopark benzeri, araçlı/molozlu** sahnedir.

👤 **İNSAN İŞİ (madde 9):** çekim **gündüz** + **gimbal 90° (nadir)** +
**otopark/moloz sahnesi** olmalı. Üçünden biri eksikse veri yine kullanılamaz.

## E) ALET KUSURU — bulundu ve düzeltildi
İlk sürümde `analyze_path` yalnız `return_reason=True` ile çağrılmıştı; demet
kısaldığı için sebep **yanlış indeksten** okunuyor ve 12/12 kare `None`
görünüyordu. Üretimdeki çağrının (`61_rota_moloza_basma.py:96`) aynısına
hizalandı; gerçek sebepler ancak ondan sonra çıktı. **Ölçüm değil aletin
kusuruydu** ve sayı yayımlanmadan yakalandı.
