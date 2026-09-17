# ONARIM-01 — Hover log kapısı: yalnız hover dilimi, uçuşsuz log TAMAM alamaz

**Durum:** KISMEN KAPANDI — fail-open kusuru ve hover dilimi **düzeltildi** (gerçek `.bin` ile doğrulandı) · 🔴 **"motor çıkış farkı" tanımı BEKLİYOR (Emir'in yöntemi)**
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 01 · **Ham kanıt:** `results/onarim/onarim01_hover_kapisi/`

## Sorun (kanıt — Emir'in push'ladığı 4 gerçek `.bin`, `results/ucus_zaman_senkronsuz/`)
Eski `scripts/hover_kapisi.py` (Jetson oturumu yazdı, D-493) tüm dosyanın tepe değerine bakıyordu:
| log | eski hüküm | gerçek |
|---|---|---|
| `1980-01-06 07-59-23` | **KAPI: TAMAM** (VibeZ 3,88 · motor fark 0) | uçuş yok (yerde) → **fail-open** |
| `1980-01-12 15-45-52` | **KAPI: TAMAM** (VibeZ 0,06 · motor fark 0) | uçuş yok → **fail-open** |
| `1980-01-06 08-07-20` | BAŞARISIZ (VibeZ 33,72 · 396 µs) | kalkış/iniş dahil |
| `1980-01-12 20-17-44` | BAŞARISIZ (VibeZ 25,38 · 359 µs) | kalkış/iniş dahil |

## Düzeltme
- `HoverDurumu`: yalnız **arm'lı · irtifa > 0,3 m · |dikey hız| < 0,3 m/s** anındaki VIBE/PWM örnekleri sayılır (**ön kayıt**). DataFlash: `ARM.ArmState`, `CTUN.Alt` (m), `CTUN.CRt` (cm/s). tlog: `HEARTBEAT.base_mode & 128` (GCS heartbeat'i yok sayılır), `GLOBAL_POSITION_INT.relative_alt` (mm), `vz` (cm/s).
- Durum mesajı yoksa hover **sayılmaz** → hover örneği yoksa **OLCULEMEDI** (çıkış 2), dışlanan örnek sayısı basılır.
- Eşikler (VibeZ ≤ 16, motor fark ≤ 60 µs) **değişmedi**. Çıktıya tanım uyarısı eklendi.

## Sonrası (aynı 4 log)
| log | yeni hüküm |
|---|---|
| `07-59-23` | **OLCULEMEDI** (hover yok; dışlanan VIBE 2556 / PWM 1278) |
| `15-45-52` | **OLCULEMEDI** (dışlanan 616 / 308) |
| `08-07-20` | BAŞARISIZ — yalnız hover: VibeZ 30,76 · motor fark 344 µs |
| `20-17-44` | BAŞARISIZ — yalnız hover: VibeZ 25,38 · motor fark 359 µs |

## 🔴 Açık: "motor çıkış farkı" tanımı
Ölçüm (motor kanalları SERVO9–12 = fonksiyon 36/34/33/35, logdaki PARM'dan doğrulandı):
- Hover diliminde **anlık max−min** medyanı **~75–95 µs**, p95 **150–280 µs** (iki uçuş). 2 s pencere medyanları 35–145 µs.
- Yani max−min tanımıyla **≤ 60 µs kuralını normal hover'lar da geçemez**. Ekibin analizindeki "+16 µs → +520 µs" **işaretli** bir değer → muhtemelen farklı bir tanım (tek motorun ortalamadan sapması, çapraz çift farkı ya da filtrelenmiş bir değer).
- **Yapılmadı:** tanımı tahmin edip kapıya koymak. Emir'in yöntemi (hangi kanallar, hangi işlem, hangi filtre) gelince betik o tanımla güncellenir ve bu loglarda +16 başlangıç değeri **yeniden üretilerek** doğrulanır.
- Uçuş dosyalarında VibeZ hover diliminde de 25–31 → iki uçuş da titreşim kuralından ayrıca düşüyor (tanımdan bağımsız).

## Değişen dosyalar
- `scripts/hover_kapisi.py` — `HoverDurumu`, `DURUM_TIPLERI`, hover sabitleri, `pencereleri_hesapla(..., sayac=)`, çıktı/JSON.
- `tests/test_hover_kapisi.py` — 9 → 15 test (uçuşsuz log TAMAM alamaz, durum yoksa hover yok, kalkış/iniş dışlanır, hover içi bozulma yakalanır, disarm sonrası dışlanır, GCS heartbeat arm'ı ezmez).

## Kanıt
```
test_hover_kapisi Ran 15 OK
mutasyon: hover_mi() -> her zaman True : FAILED (failures=4); geri alınca OK
```
