# ÖN KAYIT — T101: gerçek kadrajda koridor sayısı ve `serit_no` sınır aşımı

**Tarih:** 2026-09-03 · **Yazan:** Claude 2 (Opus 5, amele) ·
**Direktif:** `MIMAR_DIREKTIFLERI_20260903.md` İş 2 ·
**Eşikler/yöntem SONUÇ GÖRÜLMEDEN yazıldı (D-107).**

## 0. Soru (görevden)

D-205 **sentetik** t66'da ölçtü: açık şeridin kutusu 260 karenin **77'sinde
(%29,6)** iki `serit_no` üçte-birine yayılıyor; açık+yayılan şeritlerde
merkez-sınır medyanı **6,99 px**. Görevin açık sorusu: *"gerçek karelerde
kadrajda kaç koridor görünüyor ve bir koridor `serit_no` sınırını ne sıklıkta
aşıyor?"* — çünkü sorun **sentetik kadrajın mı gerçeğin mi** olduğu BİLİNMİYOR.

## 1. Yöntem

**Vekil:** gerçek karelerde şerit kutusu etiketi YOK (T111 duvarı). Bu yüzden
koridorlar **üretimin kendi** `koridor_adaylari` çıktısından alınır ve
üretimin kendi `serit_yayilimi` alanı okunur — D-205'in sentetikte kullandığı
**aynı alan**, yani sayılar birebir kıyaslanabilir. Bu bir **VEKİL ÖLÇÜMDÜR**
(yer gerçeği değil, üretim çıkarımı) ve raporda öyle anılır.

**Zincir (üretim imzası):** `_preprocess` → `predict(imgsz=INFER_SIZE,
conf=0.30)` → `get_masks` → `_maskeleri_icerige_kirp` → `serbest_alan` →
`koridor_adaylari(dt_px, r_gerekli_px, icerik=icerik)`.

**Kümeler (mpp'si olanlar; mpp gerekli çünkü `r_gerekli_px` ondan türer):**
`data/arena_kompozit` (88) · `data/arena_kompozit_v2` (126) ·
`data/arena_kompozit_dji` (69). Toplam ≈ 283 gerçek-kaynaklı kare.
⚠ Bu kümelerde mpp **küme düzeyinde bir VARSAYIMDIR** (ör. 50/1280),
kare başına ölçüm değildir — manifestin kendi uyarısı. Rapora yazılır.

**Sentetik taban:** aynı betik `--kume` ile t66'da da koşulur; D-205'in
%29,6'sı bugünkü v36 ile yeniden üretilir (sürüm kayması görünür olsun).

## 2. Raporlanacaklar

1. `n_kapi` dağılımı (kadrajda kaç koridor görünüyor).
2. `serit_yayilimi`'nda **2+ şeride yayılan kapı oranı** — D-205 ile kıyas.
3. Kapı merkezinin en yakın üçte-bir sınırına **piksel uzaklığı** (medyan,
   p05) — D-205'in 6,99 px'i ile kıyas. Ayrıca **mpp ile metreye** çevrilmiş
   hali (gerçek ve sentetik farklı ölçekte; px kıyası tek başına yanıltır).
4. Küme başına ayrı tablo + birleşik.

## 3. Geçerlilik kapıları (sonuç görülmeden)

| # | kapı | GEÇTİ ölçütü |
|---|---|---|
| W1 | Vekil boş değil | Her kümede **en az %50** karede ≥1 kapı adayı üretilmeli; altındaysa o küme "ÖLÇÜLEMEDİ" damgalanır (algı gerçekte tutmuyor demektir) |
| W2 | Sentetik taban yeniden üretildi | t66'da yayılma oranı D-205'in %29,6'sına **±10 puan** içinde; dışındaysa sürüm kayması RAPORLANIR ve kıyas o notla yapılır |
| W3 | Tek çıkarım | Kare başına 1 segmentasyon çağrısı (sayaçla) |
| W4 | Ölçek şeffaflığı | Her kümenin mpp'si ve kare boyutu çıktıda yazılı |

## 4. KAPI (görevden, aynen)

**`serit_no` DEĞİŞMEZ** — sözleşme alanıdır (CONTRACTS §8) ve tüm karar yolu
ona bağlıdır. Bu tur **yalnız ölçüm + rapor**; "kapı bir açıklıktır" tanım
değişikliği ancak bu sayılarla, **ayrı bir ön kayıtla**, mimar kararıyla olur.


---

## SONUÇ (2026-09-03, ölçüm sonrası yazıldı) — v36, n=543

| küme | kare | kapılı kare | yayılan kapı | **açık kapılarda yayılan** | merkez–sınır medyan |
|---|---|---|---|---|---|
| `arena_kompozit` | 88 | %89,8 | %37,9 | **%48,3** (42/87) | 182 px = **7,12 m** |
| `arena_kompozit_v2` | 126 | %100 | %30,4 | **%44,7** (59/132) | 181 px = **7,08 m** |
| `arena_kompozit_dji` | 69 | %79,7 | %32,2 | **%42,9** (24/56) | 554 px = **7,21 m** |
| **SENTETİK t66** | 260 | %100 | %44,9 | **%49,0** (141/288) | 51 px = **3,96 m** |

### Görevin açık sorusuna cevap

Görev diyordu: *"SENTETİK KADRAJIN MI, GERÇEĞİN Mİ SORUNU: BİLİNMİYOR."*

**Cevap: gerçeğin de sorunu.** Açık kapıların **%42,9–48,3'ü** gerçek
kaynaklı üç kümede de iki şeride yayılıyor — sentetikteki %49,0 ile aynı
mertebede. Yani "kapı bir nokta değil bir açıklıktır" gerilimi sentetik bir
artefakt DEĞİL; gerçek kamera çerçevesinde de aynı sıklıkta oluşuyor.

### Ama metrik pay gerçekte ~1,8× daha büyük

Kapı merkezinin en yakın üçte-bir sınırına uzaklığı: gerçekte **~7,1 m**
(üç kümede de 7,08–7,21 m — ölçekten bağımsız tutarlı), sentetikte **3,96 m**.
p05 uçları: gerçek 11–66 px, sentetik **4,6 px**. Yani sentetik kadraj bu
soruda **daha zorludur**; gerçek karelerde sınıra çok yakın kapı seyrektir.

### W kapıları

| # | sonuç |
|---|---|
| W1 kapılı kare ≥ %50 | **GEÇTİ** — dört kümede de (%79,7–100) |
| W2 sentetik taban D-205'e ±10 puan | 🔴 **DEĞERLENDİRİLEMEDİ** (aşağıda) |
| W3 tek çıkarım | GEÇTİ — dört kümede de |
| W4 ölçek şeffaflığı | GEÇTİ — mpp + kare boyutu çıktıda |

**W2 neden değerlendirilemedi:** ön kayıt, bugünkü sentetik sayının D-205'in
%29,6'sıyla kıyaslanabilir olduğunu varsaymıştı. Ölçüm gösterdi ki **iki sayı
farklı popülasyonu sayıyor**: D-205 *üretecin şerit kutularını* (897 şerit /
260 kare ≈ 3,45 kare başına), bu ölçüm *üretimin kapı adaylarını* (479 kapı /
260 kare ≈ 1,84). Aynı tanımda olmadıkları için "%49,0 vs %29,6" bir sürüm
kayması KANITI DEĞİLDİR. Eşik gevşetilmedi; kapı **düştü ve sebebi yazıldı.**
Bu ölçümün kendi içinde (aynı tanım, iki zemin) kıyası geçerlidir ve asıl
soruyu o cevaplar.

### Sınır

Gerçek kümelerde mpp **küme düzeyinde bir varsayımdır** (50/1280 vb.), kare
başına ölçüm değil — manifestin kendi uyarısı. Metrik sayılar (7,1 m) bu
varsayıma dayanır; **oran** sayıları (%42,9–48,3) mpp'den bağımsızdır ve
daha sağlamdır.
