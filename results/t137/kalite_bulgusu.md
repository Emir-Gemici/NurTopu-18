# T137 · KALİTE — bağımsız uyum ölçüldü ve kusur YETENEKTE DEĞİL TANIMDA

> Ölçüm zemini **gündüz** kareleridir (`data/raw_frames`, medyan L ~129).
> Gece karelerinde ölçmek yasaktı ve ölçülmedi: boş kareyi etiketlemek kolaydır,
> sayı değersiz olurdu (D-271 §1).

## 1. BAĞIMSIZ YENİDEN ETİKETLEME UYUMU (ön kayıttaki 1. vekil ölçüt)

Üç ajan **birbirinden habersiz** aynı kareleri etiketledi (referansa ve
birbirlerinin çıktısına bakmaları yasaklandı).

| çift | IoU medyan | min |
|---|---|---|
| uyum-A ↔ uyum-B | **0,930** | 0,908 |
| uyum-A ↔ uyum-C | **0,912** | 0,912 |
| uyum-B ↔ uyum-C | **0,955** | 0,947 |

**Ajanlar arası uyum çok yüksek: IoU 0,91–0,96.**

| ajan | T121 REFERANSINA göre IoU |
|---|---|
| uyum-A | 0,587 |
| uyum-B | 0,578 |
| uyum-C | 0,577 |

🔴 **Örüntü çarpıcı: üçü birbiriyle 0,92 uyuşuyor ama referansla 0,58 — ve
üçü de AYNI YÖNDE sapıyor.** Bu ya ortak kör nokta (üçü de aynı model) ya da
referansın kendisidir. Ayırmak için **ölçüm + görsel** kullanıldı.

## 2. AYIRMA — alan ve görsel

```text
kare frame_000008_000001008.jpg
   ajan poligonu  29.621 px
   T121 referansı 43.042 px      -> referans ajanin 1,45 KATI
   kesisim        26.623 px      -> ajan poligonunun %90'i referansin ICINDE
```
Yani ajanlar **daha küçük** bir bölge çizdi ve bu bölge referansın içinde
kalıyor. Fark, çatının sağındaki **koyu şerit**.

**GÖRSEL DOĞRULAMA (D-80, ZORUNLU) — ustabaşı kendi gözüyle baktı.**
2,6× büyütülmüş kırpıkta koyu şeritte **pencere boşluğu**, altında **dış
merdiven**, üstünde **klima ünitesi** görünüyor. Yani o şerit gerçekten
**dikey DUVAR YÜZÜ**dür (paralaksla görünen doğu cephesi), çatı üst yüzeyi
değil. Ajanlar bunu 2×–10× kırpıklar üreterek buldu ve gerekçelerini yazdılar.

⇒ **Ajanlar "çatı" tanımında FİİLEN HAKLI.**

## 🔴 3. ASIL BULGU — KUSUR YETENEKTE DEĞİL, GÖREV TANIMINDA

Etiketin beslediği karar şudur: *rota buranın üzerinden geçmemeli.* Bu karar
açısından **duvar yüzü de çatı kadar geçilemezdir** — duvarın üstünden geçen
rota, binanın içinden geçen rotadır.

- Ajanlar **"çatı üst yüzeyi"** çizdi (literal olarak doğru).
- T121 referansı **binanın geçilemez bölgesini** çizdi (kararın istediği).
- Ajan `uyum-A` bunu kendi notunda **açıkça** yazmış:
  *"poligonlar yalnızca gerçek üst yüzeydir, bina ayak izi değil."*

**Sonuç:** 0,58'lik referans uyumu bir **kalite düşüklüğü değil, ŞARTNAME
BELİRSİZLİĞİDİR.** Üç ajanın da aynı yere düşmesi bunu kanıtlar: belirsizlik
**tutarlı** çözülüyor, yani **tek cümleyle** düzeltilebilir.

⚠ **Düzeltilmezse bedeli büyüktür:** 1500+ kare "yalnız üst yüzey" diye
etiketlenirse model duvar yüzünü **zemin** öğrenir ve rota bina duvarından
geçer. Bu, D-210'un (çatı = zemin) **kardeş kusurudur** ve ölçeklenerek gelir.

**ÖNERİLEN ŞARTNAME CÜMLESİ (öner-bekle, karar mimarın):**
> *"Çatı" değil **GEÇİLEMEZ BİNA BÖLGESİ** etiketlenir: üst yüzey **ve**
> paralaksla görünen cephe/duvar yüzleri dâhil; bitişikteki zemin (otopark,
> yol, toprak) hariç."*

## 4. AJANLARIN KENDİ BULDUĞU İKİ ŞEY (ikisi de bağımsız, ikisi de doğru)

1. **100 px ızgara bu içerik için KABA.** Bina orijinal koordinatta ~270 px,
   duvar şeridi ~30 px. `uyum-B`: *"büyütmeseydim duvar şeridini çatıya
   katardım, yani D-210 hatasını tekrarlardım."* İkisi de 2×–10× kırpık üretmek
   zorunda kaldı ve bu süreyi **~2 katına** çıkardı.
   → **ÖNERİ:** D-80 yordamına *"50 px ızgara + şüpheli kenarlarda büyütülmüş
   kırpık"* eklensin.
2. **Ortak TUZAK, ikisi de kaçındı:** parlak açık gri geniş alan (üzerinde
   park etmiş arabalar) **çatı değil zemindir**; ikisi de etiketlemedi.

## 5. USTABAŞININ KENDİ HATASI — ilk turda kare listesini ELLE yazdım

İlk fan-out turunda 8 uyum karesinin **5'i diskte yoktu**: `11_44_04/05/06`
diye dizinler **uydurmuştum**; gerçekleri `11_44_03/23/39/46`. Bir adım önce
`partiler.json`'a **türetip yazmıştım** ve onu kullanmak yerine elle liste
geçtim — bu projede dört kez bayatlayan **"elle liste"** kusurunun aynısı.
- Bedeli: 3 ajan × ~60 sn boşa doğrulama + 5 boş kayıt.
- Düzeltme: ajanlar artık atamalarını **diskten türetilmiş dosyadan** okuyor;
  atama üretilirken her ızgara dosyasının varlığı **doğrulanıyor** (eksik 0).
- ⚠ Ajanların bunu *"boş liste 'çatı yok' değil 'kare yok' demektir"* diye
  **ayrı ayrı** bildirmesi iyi davranıştı; sessizce boş dönselerdi ölçüm
  sahte bir "uyum" üretirdi.
