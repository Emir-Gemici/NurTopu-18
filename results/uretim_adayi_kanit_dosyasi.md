# ÜRETİM ADAYI — KANIT DOSYASI (karar DEĞİL, kanıt derlemesi)

Hazırlayan: Claude 2 / Opus 5 (başamele) · 2026-08-21
Amaç: seçim kanıtları D-237…D-252 arasına dağıldı. Bu dosya onları **tek
yerde** toplar ki karar veren insan sayfalarca defter taramasın.

🔴 **BU BİR TERFİ ÖNERİSİ DEĞİLDİR.** Seçim ve sevk **insanındır** (D-133);
eşik yazma ve terfi yetkisi bende yok (AGENTS §9.2). Aşağıdaki her satır
ölçülmüş bir sayıdır ve kaynağı yazılıdır. Defter arandı: böyle bir derleme
daha önce yapılmamış (D-252 kuralı).

---

## 1. ADAYLAR

| aday | nedir |
|---|---|
| **v34** | bugünkü üretim modeli (registry `competition`) |
| **t122ac** | (a)+(c) reçetesi: zemin v5c kâhiniyle daraltıldı + çatı sınıf 1 |
| **t127_temiz** | aynı reçete, **temiz train/val bölümüyle** yeniden eğitildi |
| v30 | önceki üretim; farklı hata yaptığı için yedek değeri var (D-222 §3) |

## 2. ANA TABLO — kabul zinciri (hepsi aynı kümede, `sentetik_arena_kadraj_t66`)

| kapı | v30 | v34 | t122ac | t127_temiz |
|---|---|---|---|---|
| K0 körlük | GEÇTİ (oran 16,2 ⚠) | GEÇTİ (1,01) | GEÇTİ (3,17 ⚠) | GEÇTİ (18,4 ⚠) |
| K1 rota ≥230 | 258/260 | 258/260 | 257/260 | 256/260 |
| K2 basma ≤%15 | 14/258 | 12/258 | 16/257 | 18/256 |
| K3 ağır ≤%3 | 0/258 | 0/258 | 1/257 | 0/256 |
| K4 arena dışı ≤%5 | 1/258 | 1/258 | 0/257 | 1/256 |
| K5 bariyer =0 (T126 zemini) | GEÇTİ 0/173 | GEÇTİ 0/172 | GEÇTİ 0/172 | GEÇTİ 0/173 |
| **VERDİKT** | ÜRETİME ALINIR | ÜRETİME ALINIR | ÜRETİME ALINIR | ÜRETİME ALINIR |
⇒ **Kabul zinciri artık hiçbir adayı ayırt etmiyor** (D-244 §8). Ayrım
aşağıdaki gerçek-kare ölçümlerinden gelir.

## 3. GERÇEK KARELERDE DAVRANIŞ (asıl ayrım)

| ölçüt (kaynak) | v30 | **v34** | **t122ac** | **t127_temiz** |
|---|---|---|---|---|
| çatı kaçağı · 55 kare (D-232/D-237) | 0,305 | **0,961** | **0,020** | 0,043 |
| çatı kaçağı · 11 **bakir** kare (D-254) | 0,261 | **0,976** | **0,011** | 0,015 |
| çatı kaçağı · 6 **ham foto** (D-248) | 0,079 | **0,459** | 0,075 | ölçülmedi |
| kaplama İÇERİK (gerçek ≈ **0,47–0,52**, D-240) | 0,594 | **0,800** | 0,455 | **0,508** |
| 67 gerçek karede red | 2 | **67** | **0** | **0** |
| bakir 11 karede red | 0 | **11** | 0 | 0 |

**Okuma notları (hepsi ölçülmüş):**
- v34 elimizdeki **tek gerçek görüntü kümesinin 67/67'sini reddediyor** ve
  çatının %96'sını zemin sayıyor. t122ac/t127_temiz red vermiyor.
- t122ac'nin üstünlüğü **ezber değil**: eğitime hiç girmemiş 11 karede de
  duruyor (D-254).
- t122ac'nin sayıları **kirli bölümden gelmiyor**: temiz bölümle yeniden
  eğitilen t127_temiz aynı bandı tutturdu (D-249).
- v34'ün çatı kusuru **koşullu**: ham fotoğrafta %96 değil %46 (D-248).
  Yani WhatsApp video sıkıştırması kusuru büyütüyor; saha kamerası daha iyi
  olabilir — **ne kadar iyi olacağı ölçülmedi** (Jetson yok).

## 4. BEDELLER VE UYARILAR (dürüst taraf)

| konu | ölçüm | kaynak |
|---|---|---|
| t122ac çatı-dışı zemin kaybı | v34'e göre %39,7 (kaybın %88'i etiketsiz) | D-238 |
| …ama bu kaybın çoğu v34'ün HATASININ geri alınması | gerçek ≈0,47-0,52 · v34 0,80 | D-240 |
| kaybın nerede olduğu | araç güvenlik payı + kadraj kenarı; **koridorlar sağlam** | D-241 |
| K0 sapma yönü | v34 az zemin (1,01) · t122ac çok (3,17) · t127_temiz çok (18,4) | D-244/D-249 |
| K0 sinyalinin güvenilirliği | v34 ↔ ft figür maskeleri **sıfır piksel örtüşüyor** | D-229 |
| arena tarafında hafif geri | K2 %4,65 → %6,2 · K3 0 → 1/257 | D-242 §4 |
| tohum gürültüsü | `--tohum` **atıl**; bu kolla ölçülemez | D-251 |
| koşum-içi değişkenlik | ÖLÇÜLEMEDİ: hem tohum hem determinism kolu ATIL, eğitim bit-eş tekrarlanabilir | D-251/D-253 |

## 5. AÇIK KALAN — ve kapatılamayan
1. **ALAN-DIŞI genelleme.** Tüm ölçümler tek otoparkın karelerinden.
   Bakir kareler bile aynı saha/oturum. **DJI çekimi olmadan kapanmaz**
   (T111/D-198 duvarı; insan görevi, mimarın açması gerekir).
2. **Jetson/cihaz.** T16/T17/T15 hiç koşulmadı; cihaz 30 Eylül'de geliyor.
3. **Terfi kararı.** İnsanın (D-133).

## 6. MİMARIN SIRALAMASI (D-242 §5, değiştirmiyorum)
1. **t122ac** — ölçülebilir her kapıyı geçen tek aday *(o kayıt yazıldığında;
   T126'dan sonra dördü de geçiyor)*; gerçek karelerde ilk kez karar üretiyor.
2. **v34** — arena kapılarında en iyi, gerçek karelerde 67/67 red.
3. **v30** — farklı hata yaptığı için yedek değeri var.
**Bu dosyanın eklediği yeni kanıt:** t122ac'nin üstünlüğü (a) bakir karelerde
de duruyor, (b) temiz bölümde de duruyor, (c) v34'ün kusuru kaynak kalitesine
bağlı ama sıralamayı değiştirmiyor.
