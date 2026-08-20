# DJI NEO VERİSİ — ETİKET HATTI YORDAMI (ÖNERİ · karar mimarın)

Yazan: Claude 2 / Opus 5 (başamele) · 2026-08-20 · ÖNER-BEKLE (§9.2: veri
sözleşmesi ve kapı kararları mimarın).
Dayanak ölçümler: D-210 (tam-kare zemin kusuru) · D-219 (etiket istatistiği +
ultralytics kayıp davranışı) · D-225 (T121 sonucu) · D-229 (K0 tanısı) ·
D-231 (K5 zemini) · D-232 (kâhin kıyası) · D-233 (bölüm sızıntısı).

---

## 0. NEDEN YAZILDI
Kullanıcı DJI Neo ile gimbal 90° videolar çekip verecek; etiketleme ve eğitim
bende. Elle etiketleme 56 karede sürdürülebildi (T121: üç görsel doğrulama
turu) — **yüzlerce karede sürdürülemez.** Bu yüzden hattın OTOMATİK ama
ÖLÇÜLMÜŞ olması gerekir. Aşağıdaki her adımın yanında hangi ölçüme dayandığı
yazılıdır; ölçülmemiş hiçbir adım yoktur.

## 1. ÇEKİM AYRIMI — veri gelmeden ÖNCE kararlaştırılmalı
- **Doğrulama oturumu ayrı çekilmeli** (farklı yer/gün) ve "yalnız doğrulama"
  diye işaretlenmeli. Gerekçe: bugün elimizde **bakir alan-dışı doğrulama
  kümesi YOK** (T111/D-198) ve bu duvar ancak çekim anında yıkılabilir.
- ⚠ Bu bir **insan görevidir**; açma yetkisi mimarındır (madde 9). Ben yalnız
  öneriyorum.

## 2. KARE ÇIKARMA — araç HAZIR, yeni kod gerekmez
`scripts/extract_key_frames.py` (mevcut): video → algısal-hash ile
tekilleştirilmiş TAM ÇÖZÜNÜRLÜK kareler + manifest.
```
venv\Scripts\python.exe -B scripts/extract_key_frames.py \
  --girdi <dji_video_dizini> --cikti data/dji_frames --aralik 1.0 --hash-esik 0.12
```
⚠ Orijinal dosyalar kullanılmalı; WhatsApp'tan geçmiş kopya KULLANILMAMALI —
mevcut 67 karenin doku kaybı buradan geliyor ve model zayıflığının ölçülen
ekseni tam olarak doku/görünüm (D-216: altı hipotezden hiçbiri açıklamadı,
kalan açıklama görünüm boşluğu).

## 3. ETİKETLEME — ölçülmüş kâhin sıralaması
Aynı yer gerçeğinde (T121'in üç turda doğrulanmış çatı maskeleri, 55 kare)
ölçülen çatı kaçağı (D-232):

| kâhin | çatı kaçağı | not |
|---|---|---|
| **aday_v5c @0,30** | **%12,1** | en iyi otomatik kâhin |
| aday_v5c @0,05 | %14,8 | üretecin bugünkü ayarı |
| v30 @0,30 | %30,5 | dairesel aday |
| 71 hattı (klasik CV) | %49,4 | gölgeli çatı yamacını zemin sayıyor |
| v34 @0,30 (ÜRETİM) | %96,1 | kâhin OLARAK KULLANILAMAZ |

**Öneri:** zemin = `v5c-zemin ∩ 71-zemin` (iki BAĞIMSIZ kanıt aynı anda
"zemin" demedikçe piksel zemin sayılmaz — fail-safe yön; madde 15'in veri
tarafındaki karşılığı). Bileşimin kaçağı ölçülüp rapora eklenecek.
**Asla:** üretim modelini kendi eğitim verisinin kâhini yapmak (dairesel ve
ölçülen en kötü seçenek).

## 4. GÖRSEL DOĞRULAMA — atlanamaz
Her partide bindirme sayfaları üretilip GÖZLE denetlenmeli (D-80). T121'de üç
tur gerekti ve **her turda gerçek hata bulundu** (kendi düzeltmemin yanlış
çıkıp geri alınması dâhil). Otomatik hat gözü ikame etmez, gözün iş yükünü
azaltır.

## 5. BÖLÜM AYRIMI — artık kilitli
`bolum_sec()` KAYNAK bazında ayırır (D-233 düzeltmesi); bir kaynağın tüm
varyantları aynı bölüme gider. Kapı: `tests/test_t122_bolum_ayrimi.py`.
⚠ Mevcut `copy_paste_gercek` kümesi düzeltmeden ÖNCE üretildi ve val'i
%100 kirli; yeniden üretim mimarın kararı.

## 6. EĞİTİM VE KABUL — hangi ölçütle
- Reçete: 56 zinciri RECETE'si (imgsz 512, D-112), taban = o günkü üretim.
- Kabul: 65 zinciri (K0..K5). ⚠ **K5 bugün hiçbir modelde ölçülemiyor**
  (D-231) — zemin sorunu; ölçülebilir alt küme ölçüldü ve mimarın onayı
  bekleniyor. K5 çözülmeden **hiçbir aday kabul zincirini geçemez**, yani
  T123'ün iki-aday hedefi buna bağlı.
- Kaplama raporlanırken **payda YAZILIR** (İÇERİK / LETTERBOX) — D-201/D-214.

## 7. BU YORDAMIN BİLİNEN SINIRLARI
- Tüm ölçümler tek bir otoparkın 67 karesinden türedi; yeni alan geldiğinde
  kâhin sıralaması **yeniden ölçülmeli** (v5c'nin üstünlüğü bu sahneye özgü
  olabilir).
- 71'in gölge istisnası düzeltilirse sıralama değişebilir; düzeltme önerisi
  D-232 §4'te, uygulama mimarın kararı.
