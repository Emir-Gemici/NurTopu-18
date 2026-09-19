# 04 — Pixhawk: parametreler, pusula, failsafe

Kanıtlar: defter D-505 (+ekler), D-508 ölçüm 4, D-510, D-513 ek (4), D-515. ArduCopter 4.5.7, Pixhawk 6C.

## 3115 900KV + 9×5×3 + 4S başlangıç ayarı

Dosya: `config/pixhawk/3115_baslangic_20260919.param`.
Taban 18 Eyl dökümü `results/saha_20260918/15.03.param`; dosyada yalnız değişen satırlar var.
Kaynak ArduPilot başlangıç parametresi hesaplayıcısı (9 inç, 4S).

| Grup | Değerler |
|---|---|
| Filtreler | `INS_GYRO_FILTER 46`, `ATC_RAT_*_FLTD/FLTT 23`, `INS_ACCEL_FILTER 10` |
| İvme sınırları | `ATC_ACCEL_R/P_MAX 125900`, `ATC_ACCEL_Y_MAX 27900` |
| Hız döngüsü | roll/pitch P=I 0,07, D 0,002 (fabrika değerinin yarısı); yaw P 0,18 |
| İtki | `MOT_THST_EXPO 0,63`, hover öğrenme açık (`MOT_HOVER_LEARN 2`) |
| ESC | `RC_SPEED 400` (Skywalker 60A V2) |
| Pil | `BATT_CAPACITY 13000`, `BATT_ARM_VOLT 14,4`, dosyada `BATT_LOW 14,0 / CRT 13,2` |

- **Karttaki durum (12:59 logu):** dosya uygulanmış. Hover öğrenildi: `MOT_THST_HOVER 0,3465`.
- Sapma: kartta `BATT_LOW_VOLT 13,2 / CRT 12,8`. Bu kullanıcı seçimi ve kayda geçti.
- ESC kalibrasyonu tutmuş: dört çıkış da 1000'den başlıyor.
- **Uçuş kalitesi (12:59 ve 14:09 logları, kaza dışı):**

| Ölçü | Değer |
|---|---|
| roll RMS | 1,2–1,5° |
| pitch RMS | 1,3–1,7° |
| VibeZ ortalama | 1,4–3,5 |
| clip | 0 |
| askı akımı | 43–45 A |

  Ayar tarafı 21 Eyl için **yeterli**.
- Çentik filtresi önerisi (isteğe bağlı): `INS_HNTCH_ENABLE 1`, `MODE 1`, `REF 0,35`, `FREQ 122`, `BW 61`, `HMNCS 7`.
  Tepe frekans askıda 120–126 Hz ölçüldü. 46 Hz filtre bu tepeyi zaten bastırıyor.
  Önerinin karta yazılıp yazılmadığı kayıtlı değil.

## 19 Eyl'de karta yazılanlar (kullanıcı onayıyla, D-510)

| Parametre | Önce → sonra | Neden |
|---|---|---|
| `SERVO1..8_FUNCTION` | motor kopyaları → 0 | motorlar AUX1–4'te; MAIN çıkışlarda kopya motor işlevi vardı |
| `RC_PROTOCOLS` | 1 → 4 | IBUS. Kumanda açıkken Mesajlar'da "RC Protocol: IBUS" görülmeli |
| `BRD_SER1_RTSCTS` | 2 → 0 | telsizde RTS/CTS yok |
| `COMPASS_USE3` | 1 → 0 → **1 (geri alındı)** | bkz. pusula bölümü |

Motor kanalları: `SERVO9–12_FUNCTION` = 36 / 34 / 33 / 35.

| Kanal | Motor | Konum |
|---|---|---|
| C9 | M4 | arka-sağ |
| C10 | M2 | arka-sol |
| C11 | M1 | ön-sağ |
| C12 | M3 | ön-sol |

Log okurken RCOU **C9–C12** okunur. C1–C4'e bakmak yanlış sonuç verir; D-505'teki ilk "18 µs" değeri bu hatadan geldi.

## Pusula ⚠ (D-505 düzeltme, D-515)

- **Slot 2** harici IST8310'dur: bus 1, adres 0x0E, M9N'nin pusulası. `PRIO1` odur, kalibreli.
- **Slot 3** kartın dâhili pusulasıdır.
- MP "3 pusula, 2 harici" gösteriyor. Aynı harici cihaz iki kez listeleniyor.
- Dâhili pusula motor akımıyla **%44 bozuluyor**. Harici pusula %2 bozuluyor.
- **Harici pusula ARALIKLI geliyor.** Aynı gün bir açılışta var, sonraki açılışta yok. GPS UART aynı fişte çalışıyor.
  Sorun GPS1 kablosunda ya da konnektörde, yani I2C tellerinde.
- `COMPASS_USE3 0` önerisi mimarındı ve yanlış çıktı. Harici pusula düşünce yedek kalmadı ve arm imkânsızlaştı. Kullanıcı 1'e geri aldı.
- **UÇUŞ ÖNCESİ KURAL:** MP Mesajlar'da son açılışta **"EKF3 IMU0/1 MAG0 initial yaw alignment complete"** görülmeli.
  - "MAG2" ya da "switching to compass 2" görülürse harici pusula yok demektir. Kabloyu oturt, Pixhawk'ı yeniden başlat.
  - Uçuşta "switching to compass 2" görülürse harici pusula koptu demektir. Yaw hatası ve kayma riski başlar; iniş düşünülmeli.
- **İNSAN işi:** GPS1 kablosunu iki ucundan oturt, gerilimsiz sabitle.

## GCS failsafe (D-505 ek 2, D-508)

- Ayarlar: `FS_GCS_ENABLE 5` (LAND), `FS_GCS_TIMEOUT 5`, `FS_OPTIONS 16`.
  `FS_OPTIONS 16` pilot kiplerinde (Loiter) uçuşu sürdürür, **GUIDED'ı korumaz**.
- Bugün iki kez yaşandı: 12:59 logunda 456 s'de, 14:09 logunda 125,8 s'de. Mission Planner telsizden doğrudan bağlıydı ve heartbeat'i 5 s koptu. Araç GUIDED'dan LAND'a düştü.
- **Jetson açıkken olmaz.** MAVProxy sysid 255 ile heartbeat gönderir. Yerde 25 s heartbeat boşluğunda failsafe çıkmadı.
- Jetson ya da MAVProxy ölürse LAND devreye girer. İstenen davranış budur.
- Yazılımla uçuşta komut kaynağı Jetson'dır (TELEM2, kablolu).

## Eğim ve kayma (D-505 ek 3–4)

- Gövdeye bağlı ~1,4–2° **burun aşağı** eğim 12 Eyl'den beri var. Loiter bunu telafi ediyor; sorun değil.
- Sabahki sola roll eğimi ve "hep sağa kayma" **rüzgârdan** kaynaklandı. Öğleden sonraki uçuşlarda yoktu.
  Motor montaj eğikliği hipotezi çürüdü.
- Loiter'da 1–2 m gezinme RTK'sız GPS için olağan: HDop 0,6–0,8, HAcc ~1 m.

## PreArm'da bugün görülenler

- `RC not found`: kumanda kapalıydı.
- `safety switch`, `GPS bad fix` (kapalı alan), `fence`.
- `Compass not healthy`: harici pusula yoktu.
- `Potential Thrust Loss`: pervanesiz arm yapılıp gaz verildiğinde çıkar, beklenen.
