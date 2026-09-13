# PIXHAWK 6C — PARAMETRE KILAVUZU (1 SAYFA)
**ArduCopter 4.5.7 · Quad-X · 3S 8000 mAh · NAVITAS İHA**
**Kaynak döküm: `config/pixhawk/emir.param` (12 Eylül 2026, 23:55) — ÖLÇÜLDÜ, beyan değil**

## 0. DÖKÜMÜN KANITLADIĞI İKİ ŞEY
- **`STAT_FLTTIME = 273 s`** (6 Eylül'de 0'dı) → hava aracı **4 dk 33 sn uçtu**. `.bin` logu silinmiş olsa da
  **uçuş gerçekleşti ve karta yazıldı** — A12'nin bağımsız kanıtı budur. `STAT_BOOTCNT 48 → 96`.
- **Pusula + ivmeölçer + jiroskop yeniden kalibre edildi** (`COMPASS_OFS/DIA/ODI`, `INS_ACC*`, `INS_GYR*` hepsi
  değişmiş) → D-428 §5g'deki "ikinci pusula kalibrasyonu" borcu **kapandı**.

## 1. DEĞİŞTİRİLECEK — 3S 8000 mAh kararının sonucu

| # | Parametre | ŞU AN | OLMALI | Neden |
|---|---|---|---|---|
| ✅ 1 | `BATT_CAPACITY` | ~~3300~~ | **8000** (13 Eyl) | Pil 6000 mAh oldu. Düzeltilmezse MP "kalan %" ve mAh sayacı **yanlış** — yakıt göstergesi bozuk uçarsın. |
| 🟡 2 | `BATT_ARM_VOLT` | **0** | **11.1** | 3S × 3,70 V. Yarı boş pille arm'ı engeller (şu an hiçbir kontrol yok). |
| ✅ 3 | `BATT_CRT_VOLT` | **9** | **9** (13 Eyl, kaptan kararı) | 9 V = 3S × **3,00 V/hücre** — yük altında hücre hasarı sınırı. 9,9 V = 3,30 V/hücre güvenli taraf. *Senin kararın; 9 V çalışır ama pili yorar.* |
| ✅ 4 | `BATT_LOW_VOLT` | ~~10~~ | **10,5** (13 Eyl) | 3S × 3,33 V — doğru, dokunma. |

## 2. DOĞRU — dokunma, sadece bil

| Parametre | Değer | Anlamı |
|---|---|---|
| `FS_THR_ENABLE` / `FS_THR_VALUE` | **3 / 975** | Kumanda kaybı → **LAND**. A1 ✅ |
| `FS_GCS_ENABLE` | **5** | **"Enabled always Land"** — Jetson/YKS bağlantısı kesilirse **LAND**. Kapalı **değil**; A2'de kapattığını sandığımız ayar aslında 5'e alınmış. `FS_THR_ENABLE=3` ile **tutarlı** — böyle kalsın. |
| `FS_GCS_TIMEOUT` | **5** | 5 s sessizlik |
| `BATT_FS_LOW_ACT` / `BATT_FS_CRT_ACT` | **1 / 1** | İkisi de LAND. A3 ✅ |
| `RC6_OPTION` | **153** | A4'te sen atadın ✅. MP'de `Config → Extended Tuning`/`Servo` ekranında **adını gözle doğrula** — ArduPilot listesinde 153 = **ArmDisarm**. Havada disarm'ı ArduPilot zaten reddeder, güvenli. |
| `FLTMODE6` | **9** | LAND kipi |
| `FENCE_ENABLE/ACTION/ALT_MAX` | **1 / 1 / 50** | Çit açık, tavan 50 m |
| `ARMING_CHECK` | **1** | Tüm kontroller. **0 yapılmaz.** |
| `LOG_BITMASK` | **176126** | Loglama **açık** — silinen log ayar hatası değil, kart/kullanıcı kaynaklı |
| `FRAME_CLASS/TYPE` | **1 / 1** | Quad-X |

## 3. ÖLÇÜLMEMİŞ — farkında ol

- **`MOT_THST_HOVER = 0.35`** hâlâ fabrika değeri. `MOT_HOVER_LEARN = 2` (öğren+kaydet) açık olmasına rağmen
  değişmemiş → 15 s hover **öğrenmeyi tetiklemedi** (muhtemelen Stabilize'da uçuldu; öğrenme yalnız irtifa
  denetimli kiplerde çalışır: AltHold / Loiter / PosHold / Guided). **Sonuç: askı itkisi ve dolayısıyla
  itki payı henüz ÖLÇÜLMEDİ.** Bir sonraki uçuşta **AltHold**'da 30 s askıda kal → değer kendi oturur.
- **`BATT_AMP_PERVLT = 36.36`, `BATT_VOLT_MULT = 18.18`** — ikisi de PM06 **fabrika** değeri, doğrulanmadı (A13).

## 4. UÇUŞ ÖNCESİ 4 DAKİKA
1. MP → `Config → Full Parameter List` → ara: **`BATT_CAPACITY`** → **6000** yaz.
2. Ara: **`BATT_ARM_VOLT`** → **11.1** · **`BATT_CRT_VOLT`** → **9.9** (kabul edersen).
3. **`Write Params`** → Pixhawk'ı yeniden başlat → değerleri **tekrar oku**.
4. Yeni döküm: `Save to file` → `config/pixhawk/arducopter_fda_20260913.param`.
5. Pervanesiz sağlama: kumandayı kapat → HUD'da **`LAND`**; aç → eski kip. (30 sn)

## 5. TEHLİKE
`ARMING_CHECK=0`, `FS_THR_ENABLE=0`, `FENCE_ENABLE=0`, `BATT_FS_*_ACT=0` — biri sıfırsa **uçulmaz**.
Şu anki dökümde **dördü de doğru**; test için kapatılan her failsafe aynı oturumda geri açılır.
