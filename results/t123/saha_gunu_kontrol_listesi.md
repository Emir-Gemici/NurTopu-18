# SAHA GÜNÜ KONTROL LİSTESİ — 30 Eylül sabahı

> **Tek sayfa, elle okunur.** Jetson o gün geliyor; cihaz-öncesi deneme
> penceresi **yok** (D-211 §5). Model ve paket **30 Eylül'den ÖNCE** bitmiş
> olmalı; o gün yalnız `.engine` derlemesi (T109) ve geçiş provası kalır.

## A · ELDE NE OLMALI (kutu kutu işaretle)

| ✓ | ne | nerede | doğrulama |
|---|---|---|---|
| ☐ | **Saha paketi** | `~/navitas/` (kopyalanmış) | `ls ~/navitas/models ~/navitas/kod` |
| ☐ | **Birincil ağırlık** `.pt` | `models/navitas_seg_v35_best.pt` | G2 betiği → `OK` |
| ☐ | **Birincil** `.onnx` | `models/navitas_seg_v35_best_512_fp16.onnx` | G2 betiği → `OK` |
| ☐ | **Yedek ağırlık** `.pt` | `models/navitas_seg_v34_best.pt` | G2 betiği → `OK` |
| ☐ | **Yedek** `.onnx` | `models/navitas_seg_v34_best_512_fp16.onnx` | G2 betiği → `OK` |
| ☐ | **Künye** | `models/jetson_derleme_manifest.json` | `asil_model_pt` = birincil mi |
| ☐ | **Defter** | `config/model_registry.json` | `model_id` = `navitas-seg-v35-512` |
| ☐ | **Test görüntüleri** (30 kare) | `test_goruntuleri/sentetik_arena/` | `ls | wc -l` → **30** |
| ☐ | **`.engine` × 2** | T109 · **cihazda derlenir** | 30.09 sabahı üretilecek |

⚠ `.engine` dosyaları **PC'de derlenmez** — Jetson'da üretilir (T109). Bu
listenin tek "o gün yapılacak" kalemi budur.

## B · SIRAYLA ÇALIŞTIRILACAK (kopyala-yapıştır)

**1. Bütünlük** — `JETSON_KILAVUZ §6C/G2` bloğunu çalıştır.
Beklenen: her satır `OK`. **`UYUSMAZ` görürsen DUR** — bozuk yedekle koşmak,
düşen birincille koşmaktan kötüdür.

**2. Birincille doğrulama koşumu**
```bash
cd ~/navitas
python3 kod/jetson_fps.py \
  --girdi test_goruntuleri/sentetik_arena \
  --pt models/navitas_seg_v35_best.pt \
  --onnx models/navitas_seg_v35_best_512_fp16.onnx \
  --imgsz 512 --isinma 1 --tekrar 3 --conf 0.30 --cihaz 0 \
  --cikti results/saha_dogrulama_$(date +%Y%m%d_%H%M%S)
```
Beklenen: `exit=0` ve özet dosyası yazılır. **`--kayit-dogrulamasiz` SAHADA YASAK.**

**3. `.engine` derlemesi** — T109 yordamı (bu listenin dışında).

## C · GEÇİŞ KARARI — HANGİ ARIZADA HANGİ MODEL

🔴 **Karar İNSANINDIR** (D-133). Yordam yalnız mekaniktir.

| gördüğün | senaryo | ne yap |
|---|---|---|
| Ekran **rota çizmiyor**, `road` yayınlanmıyor | (b) göremiyor | 🔴 **MODEL DEĞİŞTİRİLMEZ.** → aşağıdaki kutu |
| İKA **moloza basıyor** | (a) çok basıyor | v34 bu eksende daha iyi (%4,65 vs %7,03) → §6C geçişi meşru |
| Süreç **çöküyor / model yüklenmiyor** | (c) teknik | G2 → geçiş; herhangi bir doğrulanmış ağırlık |

### 🔴 (b) SENARYOSUNUN CEVABI MODEL DEĞİL, PROSEDÜRDÜR (D-277 §3-4)

> **Rota üretilmiyorsa model değiştirilmez; İKA sürmez ve sebep kaydedilir.**

**Neden geçmiyoruz:** birincil "göremiyor" ise sahne **okunamıyor** demektir.
Model değiştirmek *aynı körlüğü başka bir modelle denemektir*. Yedek v34 bu
eksende **daha kötüdür** — gerçek karelerin **67/67'sini** reddeder (D-249).
t122ac ve v35-`last.pt` de yedek **değildir**: aynı arıza ailesinden gelirler.
**Yedeklilik farklı DOSYA değil, farklı ARIZA demektir.**

**Ne yapılır (sırayla):**
1. **İKA'yı sürdürme.** Bu davranış kodda zorlanır (`ika_nav`, NO_ROUTE boyunca
   sıfır-olmayan motor komutu vermez) — ama operatör de **bilerek** uygular.
2. **Sebebi saha defterine yaz:** saat · ne görüldü · İHA irtifa/açı · sahne.
3. Sahneyi düzelt: **irtifa/açı/aydınlatma** — model değil. `NO_ROUTE`
   sözleşmede **geçici** bir durumdur (`CONTRACTS.md §6`), kalıcı arıza değil.
4. Rota gelirse İKA **aynı waypoint'ten** devam eder; ek işlem gerekmez.

⚠ **(b) için sabitlenmiş bir yedek model YOKTUR ve aranmayacaktır** — gerekçe
`REVIEW_LOG.md` **D-277 §3-4**. Bu bir eksik değil, **karardır**.

## D · GEÇİŞ (yalnız karar verildiyse)
`JETSON_KILAVUZ §6C` → **G2 → G3 → G4 → G5 → G6 → G7**.
Ölçülen süre (PC'de): **~6 saniye**; Jetson'da G6 daha yavaş, kalan adımlar
cihazdan bağımsız.
**Geri alma: G8** (`.oncesi` dosyaları yerine kopyalanır) + G6/1 birincille
**yeniden** koşulur — dönüşün de kanıtı olur.

## E · HER GEÇİŞTE SAHA DEFTERİNE
`saat · gerekçe · G2 çıktısı · G6 çıktı yolu · kim karar verdi`
**Kaydedilmeyen geçiş dönüşte yeniden tartışılır** (§G7).
