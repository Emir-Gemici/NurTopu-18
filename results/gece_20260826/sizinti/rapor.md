# ON_KAYIT §12 — engel→zemin SIZINTI ölçümü + val82 "rota yol üstünde" (kapı DEĞİL)

Tarih: 2026-08-26 · kod DEĞİŞMEDİ (yalnız bu dizine yazıldı) · eşik yok, hüküm yok.
Referans: `t152_uzlasi/<govde>_uc.png` (111 kare, 960×540; 0 etiketsiz / 1 sınıf 0 / 2 sınıf 1). Kareler: `results/dji_20260822/kareler_1fps/dji_20260822172613_0038_d/<frame>.jpg` (3840×2160; dataset v3 kopyasıyla md5 eş).
Çıkarım: `_preprocess → predict(imgsz 512, conf 0,30) → get_masks → _maskeleri_icerige_kirp` (126 ile aynı), maske içerik kutusundan kesilip INTER_NEAREST ile 960×540. Model zemin = `mk[0] > 0`.
Betik: `sizinti_olc.py` (bu dizin). Ham: `olcum_sizinti.json`, `val82_<model>_142.log`, `val82_<model>_olcum.json`, `val82_143.log`, `val82_etiket_tavani.json`. Birleşik: `olcum.json`.

Tanımlar: sızıntı = |GT sınıf1 ∧ model zemin| / |GT sınıf1| · geri çağırma = |GT sınıf0 ∧ model zemin| / |GT sınıf0| · etiketsiz payı = |GT etiketsiz ∧ model zemin| / |model zemin|. "px" = toplam piksel oranı (paydalar toplanarak); "med" = kare başına payın medyanı (paydası 0 olan kareler dışarıda: sınıf1'siz 2 kare, sınıf0'sız 18 kare, model zemini boş kareler etiketsiz payında dışarıda).

## Tablo (model × ölçüt) — hepsi / test29 / val82

| model | sızıntı px (111/29/82) | sızıntı kare med | geri çağırma px (111/29/82) | geri çağ. kare med | etiketsiz payı px (111/29/82) | model zemin BOŞ kare (111) | val82 ROTA (tavan 43) | val82 YANLIŞ GÜZERGÂH | val82 FP (tavana göre) |
|---|---|---|---|---|---|---|---|---|---|
| v35 | 0,023 / 0,018 / 0,025 | 0,0000 | 0,091 / 0,119 / 0,083 | 0,000 | 0,179 / 0,234 / 0,158 | 65 | 15 | 10 | 0 |
| v3 | 0,023 / 0,017 / 0,026 | 0,0011 | 0,576 / 0,618 / 0,564 | 0,639 | 0,341 / 0,342 / 0,341 | 41 | 31 | 5 | 1 |
| v6 | 0,046 / 0,058 / 0,041 | 0,0040 | 0,643 / 0,655 / 0,639 | 0,736 | 0,391 / 0,392 / 0,391 | 28 | 35 | 8 | 2 |

val82 ayrıntı (142 --etiket-dizin, --atla-kabul, tavan = 143 val82: ROTA 43 · MASKE_YOK 13 · UC_BANT 26):
- v35: ROTA 15 · MASKE_YOK 49 · UC_BANT 18 · TP 15 FP 0 FN 28 · YANLIŞ GÜZERGÂH 10/15. Yanlış 10'un 8'inde rota çizgisinin engel payı 0,60–1,00 ve 5–8/8 waypoint sınıf 1 üstünde (130, 153, 157, 158, 159, 201, 203, 208, 230); 156'da yol payı 0,28.
- v3: ROTA 31 · MASKE_YOK 30 · UC_BANT 21 · TP 30 FP 1 (223) FN 13 · YANLIŞ 5/31 (72, 140, 144, 210, 223).
- v6: ROTA 35 · MASKE_YOK 20 · UC_BANT 22 · ZEMIN_MASKESI_SUPHELI 4 · GORUS_HATTI_KOPUK 1 · TP 33 FP 2 (108, 129) FN 10 · YANLIŞ 8/35 (75, 108, 129, 144, 157, 168, 208, 210).
- Kapı (ON_KAYIT §11(2), YANLIŞ GÜZERGÂH == 0): üçü de val82'de DÜŞTÜ. Bu kapı zaten test29'da düşmüştü; val82 sayıyı büyütür, hükmü değiştirmez.

## En kötü 5 sızıntı karesi — bindirme (`kotu5_<model>/`; üst: kare, alt: GT sınıf1 KIRMIZI, model zemin YEŞİL, kesişim SARI) — GÖZLE

v35 (5'i de val82, 5'i de aynı motif):
1. f157 · 0,73 (13635/18583 px) — **beton drenaj kanalı** (sağdaki beyaz şerit) tümüyle zemin; toprak yolun kendisi HİÇ yakalanmamış.
2. f213 · 0,56 — yolun altındaki **beton kanal** + yol kenarı zemine dâhil; toprak yol kısmen yakalanmış.
3. f210 · 0,52 — **beton kanal** boyunca sarı şerit; sağ üstteki engel bloğu (kırmızı kutu) kısmen zemin.
4. f156 · 0,44 — **beton kanal** (sağ kenar) zemin; yol yok.
5. f158 · 0,41 — **beton kanal** zemin; yol yok. Kırmızı benekler = fidan/çalı (model onlara dokunmuyor).
→ v35'in sızıntısı tek kaynaklı: **beton kanal = zemin**. Val82'deki 10 yanlış güzergâhın 8'i bu kanal üstünde rota (engel payı ≥ 0,60).

v3 (5'i de val82):
1. f157 · 0,86 — toprak yol DOĞRU yakalanmış (yeşil), **beton kanal** da zemin (sarı).
2. f217 · 0,49 — yol yakalanmış; yol kenarındaki **beton kanal** zemin; sağdaki kanal ağzı/menfez (kırmızı) dokunulmamış.
3. f206 · 0,41 — kanalın kendisi (sarı şerit) zemin; asıl yol (üstteki toprak yol) HİÇ yakalanmamış; çalı ve direk (kırmızı) temiz.
4. f158 · 0,40 — yol doğru + **beton kanal** zemin.
5. f156 · 0,40 — yol doğru + **beton kanal** zemin.
→ v3: yol geri çağırması v35'e göre 6× (0,58 vs 0,09); sızıntı kaynağı v35 ile aynı (**beton kanal**), piksel oranı aynı (0,023).

v6:
1. f223 (val82) · 1,00 (52684/52890) — kare tümüyle **çorak yamaç/tarla** (GT etiketsiz) + alt banttaki **çalılık** (GT sınıf1) → hepsi zemin. Tarla yeşili etiketsize gidiyor (kapı dışı) ama çalılık sızıntısı tam. v3 ve v6'da 223 aynı zamanda tavana göre FP/yanlış rota.
2. f116 (test29) · 0,97 (334740/346124) — **uzun ot/çim + çalı** (GT sınıf1) neredeyse tamamen zemin; yalnız kamp eşyası (kırmızı) hariç.
3. f115 (val82) · 0,95 — aynı sahne: **çim ve çalılık** tümüyle zemin.
4. f157 (val82) · 0,89 — yol doğru + **beton kanal** zemin (v3 ile aynı).
5. f217 (val82) · 0,74 — tüm yamaç + **beton kanal** zemin; yalnız menfez ve insan (kırmızı) temiz.
→ v6: kanal sızıntısına ek olarak **bitki örtüsü (çim/çalı) → zemin** sızıntısı var; toplam piksel sızıntısı v3'ün 2×'i (0,046) ve etiketsiz payı en yüksek (0,39). Geri çağırma en yüksek (0,64) — bedeli bu.

## Gözlem (yorum değil, ölçümden okunan)
- Sızıntı toplam piksel oranı üçünde de düşük (%2–6) çünkü GT sınıf1 alanının büyük kısmı çalı/ağaç/yapı ve modeller oralara zemin demiyor; sızıntı **dar, uzun bir nesnede** (beton kanal) yoğunlaşıyor ve rota bu kanala düşünce YANLIŞ GÜZERGÂH üretiyor. Piksel oranı düşükken rota hatası yüksek (v35: 10/15).
- v35 geri çağırması 0,09, 111 karenin 65'inde zemin maskesi boş: model bu sahnede yolu çoğunlukla görmüyor; gördüğünde çoğu kez kanalı görüyor.
- v3 vs v6: v6 daha fazla rota (35 vs 31) ama daha fazla yanlış (8 vs 5), daha fazla FP (2 vs 1), 2× sızıntı ve bitki örtüsüne sızma. Seçim ON_KAYIT §12 gereği yeniden eğitim kararına girdi; bu turda eğitim yok.

## ÖLÇÜLEMEDİ / dikkat
- Bu dizinde 11:19–11:21 damgalı `sizinti_olc.log`, `143_val82.log`, `bindirme/` de var (PC çökmesi öncesi kesilen önceki koşum, commit 9886a05). Sayıları bu koşumla birebir aynı (v35 0,0228/0,0913/0,1794 vb.) — bağımsız tekrar. `olcum_sizinti.json` ve `val82_etiket_tavani.json` bu koşumca yeniden yazıldı (deterministik; 143 val82 tavanı iki koşumda da ROTA 43).
- `cv2.imread(..., IMREAD_GRAYSCALE)` `rpi_inference` içe aktarıldıktan sonra (540,960,1) döndürüyor; betikte `np.squeeze` ile giderildi. Kod değişmedi, yalnız ölçüm betiği.
- GT'de sınıf1 olmayan 2 kare ve sınıf0 olmayan 18 kare kare-başına medyanların dışında; toplam piksel oranı hepsini kapsar.
- "Kanal/bordür/ağaç/çim" hükümleri gözle bindirmeden okundu; piksel bazlı nesne sınıfı etiketi yok (GT ikili). Kanal genişliği 960×540'ta ~10 px olduğundan INTER_NEAREST kenar payı ±1 px.
