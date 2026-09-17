# ONARIM-15 — Pixhawk 6C düşüş sonrası durum tespiti (salt okuma) + parametre yedeği

**Durum:** TESPİT TAMAM · parametre **değiştirilmedi** · insan/donanım işleri aşağıda
**Tarih:** 17 Eylül 2026 ~12:50 · Bağlantı: PC USB (`/dev/serial/by-id/usb-Holybro_Pixhawk6C_220044001451333531363238-if00`), yalnız USB gücü, pervanesiz
**Ham kanıt:** `results/onarim/pixhawk_20260917/pixhawk_param_yedek_20260917.param` (1025/1025 parametre), `pixhawk_durum_20260917.json`

## Ölçülen
| kalem | değer | yorum |
|---|---|---|
| Kalp atışı | sysid 1 · quadrotor · ArduPilot · disarm | ✅ kart düşüşten sağlam çıktı (iletişim/işlemci) |
| Firmware | **ArduCopter 4.5.7** | 15 Eylül ile aynı |
| Parametre | 1025/1025 okundu, yedeklendi | düşüş sonrası ilk tam yedek |
| TELEM2 (Jetson hattı) | `SERIAL2_PROTOCOL 2 · BAUD 57 · RTSCTS 0 · SR2_POSITION 8 · SR2_EXTRA3 2` | 15 Eylül ayarı **korunmuş** |
| Motor çıkışları | `SERVO9..12_FUNCTION = 36/34/33/35`, `FRAME quad X` | hover_kapisi varsayılanı (SERVO9–12) doğru |
| Sensör sağlığı (SYS_STATUS) | gyro/accel/mag/baro/GPS/AHRS/logging/batarya **ok**; **sağlıksız:** Z irtifa kontrolü, XY konum kontrolü, prearm | ilk ikisi GPS fix yokluğundan (iç mekân) beklenir |
| GPS | `fix_type 1`, 0 uydu | modül **algılanıyor** (0 olsaydı hiç yok demekti); iç mekânda fix beklenmez → **dışarıda test edilmeli** (kablo onarımı sonrası) |
| Pusulalar | `COMPASS_DEV_ID 658953` (harici, öncelik 1, `ORIENT 6`) · `DEV_ID2 658433` (dahili) | ikisi de algılanıyor |
| 🔴 Pusula tutarlılığı | 12 s ortalama: harici [131, −304, 355] mG (|486|) · dahili [89, 96, 643] mG (|656|) → vektörler arası **~49°** | PreArm **"Compasses inconsistent"**. Adaylar: GPS/pusula modülü tamirde **döndü/yeri değişti** (ORIENT artık yanlış) ya da masadaki manyetik kaynak (şarj cihazı, kablolar). **Kalibrasyon ve modül yönü kontrolü gerekir** |

## PreArm mesajları (tamamı)
`GPS 1: Bad fix` · `Battery 1 below minimum arming voltage` (USB gücü, `BATT_ARM_VOLT 9`) · `Fence requires position` (`FENCE_ENABLE 1`) · `RC not found` (alıcı bağlı değil) · `Hardware safety switch` · `Compasses inconsistent`.
Pusula dışındakiler bu tezgâh düzeninde **beklenen**dir.

## Yapılması gerekenler (insan / donanım — yazılımla yapılmaz)
1. GPS/pusula modülünün gövdedeki **yönü**: ok işareti ileri mi? Tamir sırasında döndüyse ya düzeltilir ya `COMPASS_ORIENT` güncellenir (değişiklik öncesi bu yedek var).
2. Gövde yeniden yapılınca, manyetik kaynaklardan uzakta, **dışarıda pusula kalibrasyonu** (Mission Planner → Compass → Onboard Mag Calibration) + GPS fix kontrolü.
3. Kalibrasyon sonrası bu betikle tekrar okuma: vektör açısı küçük olmalı, PreArm'da "Compasses inconsistent" kalmamalı.
4. İlk kısa hover sonrası `scripts/hover_kapisi.py <log.bin>` (ONARIM-01) — motor farkı tanımı Emir'den gelince hüküm geçerli.

## Güncelleme (17 Eylül ~13:10)
- Kullanıcı modülü yeniden yerleştirdi; yeniden ölçüm: harici [321, 192, 227] mG · dahili [93, 97, 646] mG → açı **47,4°**, PreArm "Compasses inconsistent" **sürüyor**.
- Kalibrasyon aracı hazır: `scripts/tezgah/pusula_kalibrasyonu.py` (MAV_CMD_DO_START_MAG_CAL, tüm pusulalar, autosave, reboot yok, 300 s tavan → iptal, JSONL kayıt). **Koşulmadı:** drone henüz toplanmadı (kullanıcı). Koşul: modül + Pixhawk gövdeye sabit, manyetik kaynaklardan uzak, pervanesiz.

## Güncelleme (17 Eylül ~14:35) — farklı GPS modülü takıldı
- Takılı hâlde (yeniden başlatma öncesi): `GPS_RAW_INT.fix_type 0` (GPS **algılanmıyor**; önceki modülde 1 idi), PreArm "Compass not healthy".
- `MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN` (disarm, ACK 0) sonrası: `fix_type 0` · **`COMPASS_DEV_ID 0`** (harici pusula bulunamadı; önceki 658953 — yedekte) · `COMPASS_DEV_ID2 658433` (dahili) · sağlıksız: 3D_MAG, Z/XY kontrol, prearm · `SCALED_IMU` (1. pusula) 0,0,0.
- Yorum: yeni modülün ne GPS UART'ı ne I2C pusulası Pixhawk'a ulaşıyor → **kablo/konnektör/port** (GPS1 10-pin, ya da modül-Pixhawk konnektör tipi uyumu) ya da modül beslemesi. Yazılımla çözülmez. Doğru bağlanınca yeniden başlatma + pusula kalibrasyonu gerekir (`scripts/tezgah/pusula_kalibrasyonu.py`).
- PC: kullanıcı `dialout` grubuna eklendi (+ setfacl) — yeniden başlatmadan sonra port izni kalıcı.
- 82 dataflash logu eksiksiz indirildi (`scripts/tezgah/pixhawk_log_indir.py`); 81 = 17 Eyl 02:54 düşüş logu.
