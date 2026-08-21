# T138 · ÖN KAYIT — "kullanılabilir" ne demek, SONUCU GÖRMEDEN yazıldı

> ⚠ **D-107.** Bu dosya ölçümlerden **ÖNCE** yazıldı. Aşağıdaki ölçütler sonucu
> görünce **gevşetilmeyecek**. Kullanıcı *"çoğunu kullanmazdım"* dedi; benim
> işim onu **doğrulamak değil ÖLÇMEK** — çıkarsa çıkar, çıkmazsa çıkmaz.

## 0. Defter araması (D-252)
`D-270` (kendi provam) ve `D-271` (mimar denetimi) bu kareleri **parlaklık**
ekseninde ölçtü. **Ölçülmemiş olan:** kare kare "eğitime uygunluk" ve
üretim yolundaki davranışın **model bazında** dökümü. Bu tekrar değildir.

## 1. GİRDİ
`data/dji_prova_kareler` — 569 kare, 7 klipten (T136'da çıkarıldı, dedup'lı).
Klip medyan parlaklıkları (ölçüldü, D-270): 70,2 · 55,0 · 23,5 · 21,3 · 17,5 ·
13,1 · 19,0. **Parlaklık çekim sırasıyla düşüyor — bu bir DEĞİŞKEN**, ve
kullanıcının işaret ettiği "ilk iki klip farklı" hipotezi burada sınanır.

## 2. BİR KARE "EĞİTİME UYGUN" SAYILMAK İÇİN NE SAĞLAMALI
🔴 **Parlaklık TEK BAŞINA ölçüt DEĞİLDİR.** Üç şart da sağlanmalı:

| # | şart | nasıl ölçülür | neden |
|---|---|---|---|
| U1 | **Kâhin etiket üretebiliyor** | (a)+(c) hattının zemin kâhini kareyi *"zemin poligonu üretilemedi"* diye ELEMİYOR | etiketlenemeyen kare eğitime giremez |
| U2 | **Zemin maskesi dejenere değil** | zemin oranı **> 0,05** ve **< 0,95** (içerik paydası) | 0 = körlük · 1 = tam-kare zemin, D-210'un ta kendisi |
| U3 | **Görsel olarak zemin/engel ayırt edilebiliyor** | D-80: ızgaralı tam boy görünümde **gözle** | sayı iyi görünüp görsel kötüyse **GÖRSEL KAZANIR** |

⚠ U2'nin iki yönü de gerekli: alt sınır körlüğü, üst sınır D-210'un
tam-kare zemin kusurunu eler. Tek yönlü eşik bu projede iki kez patladı.

## 3. KAÇ KARE GEÇERSE "KÜME OLUŞTURMAYA DEĞER"
🔴 **Eşik: ≥ 30 kare VE ≥ 2 ayrı klip.** Sonucu görmeden yazıyorum.

**Gerekçe (ölçülmüş dayanaklarla):**
- Bugünkü gerçek-kare kümesi **67 ayrı kare**dir ve çalışan modelleri üretti.
  30 kare, onun **%45'i** — anlamlı bir katkı için alt sınır.
- 30'un altı **kazanç değil RİSK**: farklı oturum/ışık koşulundan gelen az
  sayıda kare dağılımı kirletir, ve D-233'ün dersi taze — küçük bir kirli
  bileşen bütün val metriğini yanıltabilir.
- **≥ 2 ayrı klip** şartı: tek klipten 30 kare, dedup'a rağmen **aynı sahnenin**
  30 görünümüdür; çeşitlilik değil tekrar olur.

## 4. HANGİ SONUÇTA "HİÇBİRİ UYGUN DEĞİL" DENİR
- Geçen kare **< 30** → küme oluşturulmaz, **etiketleme YAPILMAZ.**
- Geçen kare ≥ 30 ama **tek klipten** → küme oluşturulmaz (çeşitlilik yok).
- U3 (görsel) düşerse, U1/U2 geçse bile → **küme oluşturulmaz.**
⛔ *"Az da olsa etiketleyelim"* YAPILMAZ (D-210).

## 5. MİMARIN EK SORUSU — BU KARELER BAŞKA BİR İŞE YARIYOR MU
Eğitime uygun çıkmasalar bile **atılmaz**. T111 duvarı: **alan dışı etiketli
doğrulama kümemiz YOK** ve bugüne kadarki her kabul ölçümü eğitim dağılımının
**içinde** yapıldı (D-198). Bu kareler **tanım gereği alan dışıdır**.

**Ölçülecek (v35 · v34 · v30, aynı 569 kare):**
- kaç kare **reddedildi**, hangi **sebeple** (MASKE_YOK · ZEMIN_MASKESI_SUPHELI ·
  UC_BANT_TEMAS_YOK · …)
- kaç karede **rota ÜRETİLDİ**

🔴 **ÖNCEDEN YAZILAN HÜKÜM:** rota üretilen kare sayısı **sıfır değilse bu
CİDDİ BİR BULGUDUR** — sistem, görmesi mümkün olmayan bir görüntüde karar
üretiyor demektir. Sıfırsa, fail-closed tasarımın **ilk gerçek veri üzerindeki
kanıtıdır** ve "gece kümesi" bir **emniyet doğrulama kümesi** olarak önerilir.
⚠ Bu bir **ÖNERİDİR, kapı değil.** Kabul kümesine ekleme kararı **mimarındır**.

## 6. YETKİM OLMAYANLAR
`dataset/` altına **kalıcı küme yazılmaz** · `config/model_registry.json`a
**dokunulmaz** · eşik **değiştirilmez** (§9.2) · `codes/` altında kod
**değiştirilmez** · **push YOK**.
