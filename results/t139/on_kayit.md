# T139 · ÖN KAYIT — görünürlük DOZ-YANIT ölçümü (sonuç görülmeden yazıldı)

> ⚠ **D-107.** Ölçümlerden **ÖNCE** yazıldı. Aşağıdaki hükümler sonuca göre
> **gevşetilmeyecek**. ⛔ **Bu tur EŞİK KOYMAZ ve EŞİK ÖNERMEZ** — D-186'nın
> reddettiği kalıp odur. Bu bir **GÖRÜNÜRLÜK** turudur (§9.2).

## 0. DEFTER ARAMASI (D-252) — ARANDI, **BULUNDU**, YENİDEN KULLANILIYOR
Yeni ölçüt **icat etmedim**. Depoda hazır vekil var:
- `scripts/olcum/93_t106_guven_bandi.py` ·
  **`BAND_ORANI = toplam_kaplama(conf 0,10) / toplam_kaplama(conf 0,30)`**
- Defterde kullanılmış: **D-184** — *"güven bandı sıkışması üç kümede de yok;
  sıkışma figüre özgü"*; ölçülen figür değerleri **v30 = 1,62 · v34 = 9,59**.
- `kaplamalar(model, p, conf)` fonksiyonu **içe aktarılacak**, kopyalanmayacak.

## 1. BOŞLUĞUN TAM HÂLİ (mimarın çerçevesi, aynen)
```text
maske BOS       -> MASKE_YOK -> fail-closed        ✅ ZATEN CALISIYOR
maske BOS DEGIL -> sistem ona KOSULSUZ GUVENIYOR   🔴 BOSLUK BURADA
```
Soru: **boş olmayan ama güvenilmez maske nerede başlıyor?**

## 2. DOZ EKSENİ
`L` = LAB L kanalı ortalaması (0–255). Doğal aralık:
- **569 gece karesi** (`data/dji_prova_kareler`): L ≈ 5,8 – 73,2
- **67 gündüz karesi** (`data/raw_frames`): L ≈ 118,7 – 132,1

🔴 **ÖNCEDEN İLAN EDİLEN SINIR:** **L ≈ 73 ile 118 arasında HİÇ KARE YOK.**
Eğri bu aralıkta **boşluk** taşıyacak ve oraya **çizgi çekilmeyecek**;
ara bölge hakkında hüküm **verilmeyecek**. (Alacakaranlık verisi yok.)

## 3. YANIT EKSENİ — İKİ ÖLÇÜT, İKİSİ DE ÖNCEDEN SEÇİLDİ

**Y1 · BAND_ORANI (BİRİNCİL, yeniden kullanım).**
`kaplama(conf 0,10) / kaplama(conf 0,30)`. Maske sağlamsa güveni düşürmek çok
şey eklemez → oran **1'e yakın**. Tahminler 0,10–0,30 bandında sıkışmışsa →
oran **büyük**. (D-184'te tam bu anlamda kullanıldı.)

**Y2 · MODELLER ARASI IoU (İKİNCİL, çapraz kontrol).**
Aynı karede v35 ↔ v34 ↔ v30 zemin maskelerinin IoU'su. İki bağımsız eğitilmiş
model aynı maskede anlaşıyorsa sinyal, anlaşmıyorsa gürültü olma ihtimali yüksek.
⚠ **Korelasyonlu kör nokta uyarısı:** üçü de aynı mimari ve akraba verilerle
eğitildi; anlaşmaları **zayıf kanıttır**, anlaşmamaları **güçlü işarettir**.

## 4. HÜKÜM KURALLARI (önceden yazıldı)
- **H1:** L düştükçe `BAND_ORANI` **artıyorsa** → düşük L'de boş olmayan maske
  **gösterilebilir biçimde daha güvenilmezdir**. Doz-yanıt VARDIR.
- **H2:** L düştükçe modeller arası IoU **düşüyorsa** → aynı sonuç, bağımsız
  eksenden.
- 🔴 **İKİSİ DE ÇIKMAZSA:** boşluk parlaklıkla **açıklanmıyor** demektir ve
  bunu **açıkça yazarım**. O zaman "görünürlük" başka bir eksende aranmalıdır
  ve bu turun sonucu **"ölçtüm, ilişki yok"** olur. Bu bir başarısızlık değil,
  ölçümdür.
- **Rota üreten 6 kare** eğrinin neresine düşüyor — ayrıca işaretlenir.

## 5. NE YAPILMAYACAK
- ⛔ **Karanlık eşiği KONMAYACAK ve ÖNERİLMEYECEK.** Eşik/kapı kararı
  **mimarındır** ve ancak eğri görüldükten sonra verilir (§9.2).
- ⛔ `codes/` altında kod değiştirilmeyecek · registry'ye dokunulmayacak ·
  `dataset/` altına kalıcı küme yazılmayacak · **push YOK**.
- Sayı iyi görünüp görsel kötüyse **GÖRSEL KAZANIR** (D-80).

## 6. ÖRNEKLEM
- **Y1 (BAND_ORANI):** 569 gece + 67 gündüz = **636 karenin TAMAMI**, v35 ile.
- **Y2 (modeller arası IoU):** L aralığına yayılmış **~150 kare**, v35/v34/v30.
  Alt örneklem sebebi: 3 model × 636 kare ≈ 20 dk GPU; ikincil ölçüt için
  gereksiz. Seçim **rastgele değil**, L'ye göre eşit aralıklı yapılacak ve
  seçilen kareler kayda yazılacak.
