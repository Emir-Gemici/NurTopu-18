# Parametre zaman çizgisi ve olay dökümü — 12–15 Eylül 2026 uçuş logları

Üretim: `scripts/ucus_parm_zaman_cizgisi.py` · 2026-09-15T12:23:36 · girdi 37 dosya → **27 benzersiz** (sha256; 10 kopya atlandı). Yorumlayıcı: venv python + pymavlink.

**Kurallar.** Her sayı logdan. Kronoloji **STAT_BOOTCNT** (parametre, her açılışta +1) ile kurulur; dosya adındaki tarihe güvenilmez. Duvar saati GPS `GWk/GMS`'den (UTC, −18 s sıçrama, +3 h yerel); `GWk=0` loglarda hafta BOOTCNT komşusundan alınır ve STAT_RUNTIME/STAT_FLTTIME monotonluğu ile çapraz doğrulanır. Pil/pervane/kütle **logda yok** — `beyan` sütunu 15 Eylül kullanıcı beyanıdır.

## 1. Kronoloji (27 benzersiz log, STAT_BOOTCNT sırası)

| # | BOOT | hesaplanan başlangıç (yerel) | dosya | MP no | kopya | süre s | GWk | hücre / V_ilk | beyan | uçuş / kısa | RUNTIME_ilk s | FLTTIME_ilk s | ThH_ilk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 75 | 2026-09-12 16:45:10 | `2026-09-12 16-45-10.bin` | — | — | 25.8 | 2435 | 3S / 12.11 | A | 0 / 0 | 44680 | 128 | 0.35 |
| 2 | 76 | 2026-09-12 16:45:45 ⚠ilk fix GWk=0→hafta logun kendi GPS'inden ✓komşularla tutarlı | `1980-01-12 15-45-52.bin` | — | — | 217.1 | 0 | 3S / 12.11 | A* | 0 / 0 | 44711 | 128 | 0.35 |
| 3 | 77 | 2026-09-12 16:50:08 | `2026-09-12 16-50-10.bin` | — | — | 414.0 | 2435 | 3S / 11.95 | A | 2 / 0 | 44958 | 128 | 0.35 |
| 4 | 78 | 2026-09-12 17:15:12 | `2026-09-12 17-15-12.bin` | — | — | 93.8 | 2435 | 3S / 11.27 | A | 0 / 3 | 45636 | 169 | 0.35 |
| 5 | 79 | 2026-09-12 17:31:18 | `2026-09-12 17-31-18.bin` | — | — | 54.9 | 2435 | 3S / 11.17 | A | 0 / 1 | 45790 | 173 | 0.35 |
| 6 | 80 | 2026-09-12 17:35:39 | `2026-09-12 17-35-39.bin` | — | — | 108.2 | 2435 | 3S / 11.07 | A | 0 / 2 | 45852 | 173 | 0.35 |
| 7 | 81 | 2026-09-12 17:42:37 | `2026-09-12 17-42-38.bin` | — | — | 51.6 | 2435 | 3S / 11.05 | A | 0 / 1 | 45975 | 175 | 0.35 |
| 8 | 82 | 2026-09-12 17:47:06 | `2026-09-12 17-47-06.bin` | — | — | 34.5 | 2435 | 3S / 10.96 | A | 0 / 1 | 46097 | 175 | 0.35 |
| 9 | 88 | 2026-09-12 18:38:39 | `2026-09-12 18-48-07.bin` | — | — | 791.4 | 2435 | 4S / 16.3 | B | 0 / 0 | 46279 | 179 | 0.35 |
| 10 | 89 | 2026-09-12 18:59:07 | `2026-09-12 18-59-08.bin` | — | — | 55.9 | 2435 | 3S / 10.92 | A | 0 / 1 | 47114 | 179 | 0.35 |
| 11 | 90 | 2026-09-12 19:13:58 | `2026-09-12 19-13-58.bin` | — | — | 316.3 | 2435 | 3S / 10.76 | A | 0 / 0 | 47391 | 181 | 0.35 |
| 12 | 91 | 2026-09-12 19:41:52 | `2026-09-12 19-41-52.bin` | — | — | 437.4 | 2435 | 3S / 11.08 | A | 0 / 3 | 47730 | 181 | 0.35 |
| 13 | 94 | 2026-09-12 20:51:26 | `2026-09-12 20-51-26.bin` | — | — | 1565.0 | 2435 | 3S / 12 | A | 2 / 0 | 49303 | 181 | 0.35 |
| 14 | 95 | 2026-09-12 21:17:38 ⚠ilk fix GWk=0→hafta logun kendi GPS'inden ✓komşularla tutarlı | `1980-01-12 20-17-44.bin` | — | — | 708.0 | 0 | 3S / 11.36 | A | 2 / 0 | 50884 | 206 | 0.35 |
| 15 | 96 | 2026-09-12 23:47:27 | `2026-09-12 23-47-27.bin` | — | — | 1546.0 | 2435 | 4S / 16.29 | B | 2 / 1 | 51596 | 254 | 0.35 |
| 16 | 115 | 2026-09-13 08:34:10 | `2026-09-13 08-34-30.bin` | 58 | 58 13.09.2026 08-57-10.bin | 1379.0 | 2436 | 3S / 12.09 | A | 1 / 0 | 64655 | 301 | 0.381312 |
| 17 | 116 | 2026-09-13 08:57:44 | `2026-09-13 08-57-45.bin` | 59 | 59 13.09.2026 08-59-04.bin | 79.1 | 2436 | 3S / 11.07 | A | 0 / 0 | 66049 | 334 | 0.447916 |
| 18 | 117 | 2026-09-13 08:59:21 ⚠ilk fix GWk=0→hafta logun kendi GPS'inden ✓komşularla tutarlı | `1980-01-06 07-59-23.bin` | 60 | 60 13.09.2026 09-06-12.bin | 406.5 | 0 | 3S / 11.05 | A | 0 / 0 | 66141 | 334 | 0.447916 |
| 19 | 118 | 2026-09-13 09:07:18 ⚠ilk fix GWk=0→hafta logun kendi GPS'inden ✓komşularla tutarlı | `1980-01-06 08-07-20.bin` | 61 | 61 13.09.2026 09-14-22.bin | 424.0 | 0 | 3S / 10.99 | A | 1 / 0 | 66605 | 334 | 0.447916 |
| 20 | 119 | 2026-09-13 09:26:58 | `2026-09-13 09-26-58.bin` | 62 | 62 13.09.2026 09-38-02.bin | 665.0 | 2436 | 4S / 16.69 | B | 0 / 6 | 67038 | 370 | 0.472593 |
| 21 | 120 | 2026-09-13 09:42:25 | `2026-09-13 09-42-26.bin` | 63 | 63 13.09.2026 09-53-04.bin | 639.0 | 2436 | 3S / 11.99 | A | 3 / 0 | 67716 | 392 | 0.472593 |
| 22 | 121 | 2026-09-13 09:53:44 | `2026-09-13 09-53-45.bin` | 64 | 64 13.09.2026 09-56-14.bin | 149.0 | 2436 | 3S / 11.3 | A | 1 / 0 | 68398 | 493 | 0.46451 |
| 23 | 122 | 2026-09-13 09:59:29 | `2026-09-13 09-59-30.bin` | 65 | 65 13.09.2026 10-19-20.bin | 1190.9 | 2436 | 3S / 11.55 | A | 6 / 0 | 68552 | 521 | 0.459637 |
| 24 | 132 | 2026-09-14 19:43:06 | `2026-09-14 19-43-06.bin` | 68 | 68 14.09.2026 19-45-46.bin | 160.9 | 2436 | 3S / 12.44 | C | 2 / 0 | 95446 | 748 | 0.532559 |
| 25 | 134 | 2026-09-14 21:10:33 | `2026-09-14 21-10-34.bin` | 69 | 69 14.09.2026 21-13-14.bin | 159.9 | 2436 | 3S / 12.09 | C | 1 / 0 | 100384 | 804 | 0.49768 |
| 26 | 138 | 2026-09-15 11:14:32 | `2026-09-15 11-14-33.bin` | — | — | 204.7 | 2436 | 4S / 16.29 | D | 1 / 0 | 109544 | 834 | 0.506167 |
| 27 | 139 | 2026-09-15 11:18:16 | `2026-09-15 11-18-16.bin` | — | — | 202.0 | 2436 | 4S / 16.12 | D | 2 / 1 | 109760 | 878 | 0.506167 |

> Dosya adı (Mission Planner) = logdaki **ilk 3B GPS fix** anı; `hesaplanan başlangıç` = fix saati − (TimeUS_fix − TimeUS_ilk) = logun gerçek başı. Fark büyükse (ör. #9: ad 18:48:07, başlangıç 18:38:39) fix log açıldıktan sonra gelmiştir. `GWk=0` loglarda hafta, logun **kendi** sonraki GPS mesajlarından alınır (sütun GWk_set).

| # | GWk_set (hafta: mesaj n) | ilk fix t s | saat kaynağı |
|---|---|---|---|
| 1 | {2435: 129} | 0.2 | logun kendi GWk (ilk 3B fix); GMS=567928600 ms; sicrama -18 s; yerel UTC+3 |
| 2 | {0: 3, 2435: 120} | 6.3 | ilk fix GWk=0 → logun kendi sonraki GPS mesajlarindan hafta 2435 (120/123 mesaj); GMS=567970200 ms; sicrama -18 s; yerel UTC+3 |
| 3 | {2435: 841} | 1.3 | logun kendi GWk (ilk 3B fix); GMS=568228000 ms; sicrama -18 s; yerel UTC+3 |
| 4 | {2435: 397} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=569730600 ms; sicrama -18 s; yerel UTC+3 |
| 5 | {2435: 242} | 0.2 | logun kendi GWk (ilk 3B fix); GMS=570696600 ms; sicrama -18 s; yerel UTC+3 |
| 6 | {2435: 378} | 0.0 | logun kendi GWk (ilk 3B fix); GMS=570957400 ms; sicrama -18 s; yerel UTC+3 |
| 7 | {2435: 259} | 0.0 | logun kendi GWk (ilk 3B fix); GMS=571376000 ms; sicrama -18 s; yerel UTC+3 |
| 8 | {2435: 172} | 0.2 | logun kendi GWk (ilk 3B fix); GMS=571644600 ms; sicrama -18 s; yerel UTC+3 |
| 9 | {2435: 267} | 568.1 | logun kendi GWk (ilk 3B fix); GMS=575305800 ms; sicrama -18 s; yerel UTC+3 |
| 10 | {2435: 199} | 0.0 | logun kendi GWk (ilk 3B fix); GMS=575966000 ms; sicrama -18 s; yerel UTC+3 |
| 11 | {2435: 396} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=576856200 ms; sicrama -18 s; yerel UTC+3 |
| 12 | {2435: 1155} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=578530600 ms; sicrama -18 s; yerel UTC+3 |
| 13 | {2435: 669} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=582704800 ms; sicrama -18 s; yerel UTC+3 |
| 14 | {0: 3, 2435: 765} | 6.5 | ilk fix GWk=0 → logun kendi sonraki GPS mesajlarindan hafta 2435 (765/768 mesaj); GMS=584282800 ms; sicrama -18 s; yerel UTC+3 |
| 15 | {2435: 1611} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=593265400 ms; sicrama -18 s; yerel UTC+3 |
| 16 | {0: 15, 2436: 978} | 19.4 | logun kendi GWk (ilk 3B fix); GMS=20088197 ms; sicrama -18 s; yerel UTC+3 |
| 17 | {2436: 306} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=21483000 ms; sicrama -18 s; yerel UTC+3 |
| 18 | {0: 1, 2436: 631} | 1.3 | ilk fix GWk=0 → logun kendi sonraki GPS mesajlarindan hafta 2436 (631/632 mesaj); GMS=21581200 ms; sicrama -18 s; yerel UTC+3 |
| 19 | {0: 2, 2436: 788} | 2.4 | ilk fix GWk=0 → logun kendi sonraki GPS mesajlarindan hafta 2436 (788/790 mesaj); GMS=22058800 ms; sicrama -18 s; yerel UTC+3 |
| 20 | {2436: 1107} | 0.5 | logun kendi GWk (ilk 3B fix); GMS=23236800 ms; sicrama -18 s; yerel UTC+3 |
| 21 | {2436: 959} | 0.0 | logun kendi GWk (ilk 3B fix); GMS=24164000 ms; sicrama -18 s; yerel UTC+3 |
| 22 | {2436: 407} | 1.4 | logun kendi GWk (ilk 3B fix); GMS=24843600 ms; sicrama -18 s; yerel UTC+3 |
| 23 | {2436: 1899} | 0.2 | logun kendi GWk (ilk 3B fix); GMS=25188000 ms; sicrama -18 s; yerel UTC+3 |
| 24 | {2436: 592} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=146604200 ms; sicrama -18 s; yerel UTC+3 |
| 25 | {2436: 445} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=151852000 ms; sicrama -18 s; yerel UTC+3 |
| 26 | {2436: 762} | 0.1 | logun kendi GWk (ilk 3B fix); GMS=202491000 ms; sicrama -18 s; yerel UTC+3 |
| 27 | {2436: 827} | 0.2 | logun kendi GWk (ilk 3B fix); GMS=202714800 ms; sicrama -18 s; yerel UTC+3 |

**STAT monotonluk denetimi** (ardışık loglar arası artış; negatif = sıralama hatası):

- BOOTCNT artışları: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 6.0, 1.0, 1.0, 1.0, 3.0, 1.0, 1.0, 19.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 10.0, 2.0, 4.0, 1.0]
- RUNTIME artışları (s): [31.0, 247.0, 678.0, 154.0, 62.0, 123.0, 122.0, 182.0, 835.0, 277.0, 339.0, 1573.0, 1581.0, 712.0, 13059.0, 1394.0, 92.0, 464.0, 433.0, 678.0, 682.0, 154.0, 26894.0, 4938.0, 9160.0, 216.0]
- FLTTIME artışları (s): [0.0, 0.0, 41.0, 4.0, 0.0, 2.0, 0.0, 4.0, 0.0, 2.0, 0.0, 0.0, 25.0, 48.0, 47.0, 33.0, 0.0, 0.0, 36.0, 22.0, 101.0, 28.0, 227.0, 56.0, 30.0, 44.0]
- hesaplanan saat artışları (s): [35.3, 262.9, 1503.8, 966.0, 260.9, 418.6, 268.5, 3093.3, 1228.3, 890.2, 1674.2, 4174.2, 1571.7, 8988.9, 31603.6, 1414.0, 97.0, 476.5, 1179.9, 927.7, 678.3, 345.6, 121416.2, 5247.8, 50639.0, 223.8]
- **ihlal sayısı: 0** (üç sayaç ve GPS saati aynı sırayı veriyor)

**Loglar arası GÖRÜNMEYEN süre** (önceki log SONU → bu log BAŞI; STAT_RUNTIME = açık kalma, STAT_FLTTIME = uçuş sayacı; boşlukta FLTTIME artmışsa o aralıkta **logu bu sette olmayan uçuş** vardır. Dikkat: AP_Stats sayaçları ~30 s'de bir kaydedilir; 30 s'den kısa bir uçuş boşlukta görünmeyebilir):

| # | önceki log | bu log | BOOT atlaması | görünmeyen RUNTIME s | görünmeyen FLTTIME s | takvim boşluğu s |
|---|---|---|---|---|---|---|
| 2 | `2026-09-12 16-45-10` | `1980-01-12 15-45-52` | 0 | 0 | 0 | 9.5 |
| 3 | `1980-01-12 15-45-52` | `2026-09-12 16-50-10` | 0 | 31 | 0 | 45.8 |
| 4 | `2026-09-12 16-50-10` | `2026-09-12 17-15-12` | 0 | 247 | 0 | 1089.8 |
| 5 | `2026-09-12 17-15-12` | `2026-09-12 17-31-18` | 0 | 30 | 0 | 872.2 |
| 6 | `2026-09-12 17-31-18` | `2026-09-12 17-35-39` | 0 | 0 | 0 | 206 |
| 7 | `2026-09-12 17-35-39` | `2026-09-12 17-42-38` | 0 | 0 | 0 | 310.4 |
| 8 | `2026-09-12 17-42-38` | `2026-09-12 17-47-06` | 0 | 61 | 0 | 216.9 |
| 9 | `2026-09-12 17-47-06` | `2026-09-12 18-48-07` | 5 | 152 | 0 | 3058.8 |
| 10 | `2026-09-12 18-48-07` | `2026-09-12 18-59-08` | 0 | 30 | 0 | 436.9 |
| 11 | `2026-09-12 18-59-08` | `2026-09-12 19-13-58` | 0 | 215 | 0 | 834.3 |
| 12 | `2026-09-12 19-13-58` | `2026-09-12 19-41-52` | 0 | 30 | 0 | 1357.9 |
| 13 | `2026-09-12 19-41-52` | `2026-09-12 20-51-26` | 2 | 1143 | 0 | 3736.8 |
| 14 | `2026-09-12 20-51-26` | `1980-01-12 20-17-44` | 0 | 0 | 0 | 6.7 |
| 15 | `1980-01-12 20-17-44` | `2026-09-12 23-47-27` | 0 | 0 | 0 | 8280.9 |
| 16 | `2026-09-12 23-47-27` | `2026-09-13 08-34-30` | 18 | 11510 | 0 | 30057.6 |
| 17 | `2026-09-13 08-34-30` | `2026-09-13 08-57-45` | 0 | 0 | 0 | 35 |
| 18 | `2026-09-13 08-57-45` | `1980-01-06 07-59-23` | 0 | 0 | 0 | 17.9 |
| 19 | `1980-01-06 07-59-23` | `1980-01-06 08-07-20` | 0 | 124 | 0 | 70 |
| 20 | `1980-01-06 08-07-20` | `2026-09-13 09-26-58` | 0 | 0 | 0 | 755.9 |
| 21 | `2026-09-13 09-26-58` | `2026-09-13 09-42-26` | 0 | 0 | 0 | 262.7 |
| 22 | `2026-09-13 09-42-26` | `2026-09-13 09-53-45` | 0 | 32 | 0 | 39.3 |
| 23 | `2026-09-13 09-53-45` | `2026-09-13 09-59-30` | 0 | 0 | 0 | 196.6 |
| 24 | `2026-09-13 09-59-30` | `2026-09-14 19-43-06` | 9 | 25686 | 0 | 120225 |
| 25 | `2026-09-14 19-43-06` | `2026-09-14 21-10-34` | 1 | 4752 | 0 | 5086.9 |
| 26 | `2026-09-14 21-10-34` | `2026-09-15 11-14-33` | 3 | 8975 | 0 | 50479.1 |
| 27 | `2026-09-15 11-14-33` | `2026-09-15 11-18-16` | 0 | 0 | 0 | 19.1 |

### 1a. `1980-*` (GWk=0) logların yerleşimi

- **`1980-01-12 15-45-52.bin`** → BOOTCNT **76**, hesaplanan başlangıç **2026-09-12 16:45:45** (GPS hafta-içi gün 6, NSats 20); komşular: önceki `2026-09-12 16-45-10.bin` (bitişi 2026-09-12 16:45:36) → sonraki `2026-09-12 16-50-10.bin` (2026-09-12 16:50:08); saat tutarlı: True. Parametre farkı (STAT/otomatik hariç): BOOTCNT-öncekiyle **0**, BOOTCNT-sonrakiyle **1**; hipotez konumu (65↔68) için `2026-09-13 09-59-30` ile **20**, `2026-09-14 19-43-06` ile **20**.
  - BOOTCNT_sonraki farkları (ad, bu log, komşu): BATT_LOW_VOLT: 14.4→10
- **`1980-01-12 20-17-44.bin`** → BOOTCNT **95**, hesaplanan başlangıç **2026-09-12 21:17:38** (GPS hafta-içi gün 6, NSats 22); komşular: önceki `2026-09-12 20-51-26.bin` (bitişi 2026-09-12 21:17:31) → sonraki `2026-09-12 23-47-27.bin` (2026-09-12 23:47:27); saat tutarlı: True. Parametre farkı (STAT/otomatik hariç): BOOTCNT-öncekiyle **0**, BOOTCNT-sonrakiyle **1**; hipotez konumu (65↔68) için `2026-09-13 09-59-30` ile **20**, `2026-09-14 19-43-06` ile **20**.
  - BOOTCNT_sonraki farkları (ad, bu log, komşu): FS_GCS_ENABLE: 5→0
- **`1980-01-06 07-59-23.bin`** → BOOTCNT **117**, hesaplanan başlangıç **2026-09-13 08:59:21** (GPS hafta-içi gün 0, NSats 16); komşular: önceki `2026-09-13 08-57-45.bin` (bitişi 2026-09-13 08:59:03) → sonraki `1980-01-06 08-07-20.bin` (2026-09-13 09:07:18); saat tutarlı: True. Parametre farkı (STAT/otomatik hariç): BOOTCNT-öncekiyle **0**, BOOTCNT-sonrakiyle **1**; hipotez konumu (65↔68) için `2026-09-13 09-59-30` ile **17**, `2026-09-14 19-43-06` ile **18**.
  - BOOTCNT_sonraki farkları (ad, bu log, komşu): BATT_VOLT_MULT: 17.0946→17.02
- **`1980-01-06 08-07-20.bin`** → BOOTCNT **118**, hesaplanan başlangıç **2026-09-13 09:07:18** (GPS hafta-içi gün 0, NSats 17); komşular: önceki `1980-01-06 07-59-23.bin` (bitişi 2026-09-13 09:06:08) → sonraki `2026-09-13 09-26-58.bin` (2026-09-13 09:26:58); saat tutarlı: True. Parametre farkı (STAT/otomatik hariç): BOOTCNT-öncekiyle **1**, BOOTCNT-sonrakiyle **3**; hipotez konumu (65↔68) için `2026-09-13 09-59-30` ile **17**, `2026-09-14 19-43-06` ile **18**.
  - BOOTCNT_onceki farkları (ad, bu log, komşu): BATT_VOLT_MULT: 17.02→17.0946
  - BOOTCNT_sonraki farkları (ad, bu log, komşu): BATT_LOW_VOLT: 9→10; BATT_VOLT_MULT: 17.02→18.7267; MOT_THST_HOVER: 0.447916→0.472593

> Mission Planner `1980-01-12 15-45-52` adını, ilk 3B fix mesajında GWk=0 olduğu için üretmiştir (GPS hafta-içi ms + 1980 Ocak saat dilimi UTC+2); aynı logun sonraki GPS mesajları GWk=2435/2436 taşır (yukarıdaki GWk_set sütunu). Aynı GMS gerçek haftaya oturtulunca yerel saat (UTC+3) 1 saat ileri çıkar; 1 saatlik fark saat dilimi kuralıdır (yorum). Bu loglar **GPS'siz değildir** — 3B fix ve 16–22 uydu vardır; yalnız ilk fix mesajının hafta alanı 0'dır.

**Tek yönlü işaretçi parametrelerle yerleşim** (değerin geçerli olduğu # aralığı, §3a segmentlerinden):

| log | COMPASS_OFS_X | COMPASS_OFS2_X | BATT_CAPACITY | BATT_ARM_VOLT | BATT_CRT_VOLT | MOT_THST_HOVER |
|---|---|---|---|---|---|---|
| `1980-01-12 15-45-52.bin` | -1.14309 (#1–#21) | 29.7806 (#1–#21) | 3300 (#1–#15) | 0 (#1–#15) | 14 (#1–#3) | 0.35 (#1–#15) |
| `1980-01-12 20-17-44.bin` | -1.14309 (#1–#21) | 29.7806 (#1–#21) | 3300 (#1–#15) | 0 (#1–#15) | 0 (#4–#15) | 0.35 (#1–#15) |
| `1980-01-06 07-59-23.bin` | -1.14309 (#1–#21) | 29.7806 (#1–#21) | 6000 (#16–#23) | 9 (#16–#27) | 9 (#15–#27) | 0.447916 (#16–#19) |
| `1980-01-06 08-07-20.bin` | -1.14309 (#1–#21) | 29.7806 (#1–#21) | 6000 (#16–#23) | 9 (#16–#27) | 9 (#15–#27) | 0.447916 (#16–#19) |

## 2. "Parametre sıfırlaması" hipotezi

| # | BOOT | log | PARM n | default-dışı n | ΔPARM (önceki logdan, STAT/otomatik/SR/DEC hariç) | RC1_MIN | INS_ACCOFFS_X | AHRS_TRIM_X | COMPASS_OFS_X | BATT_CAPACITY | BATT_ARM_VOLT | STAT_RESET | ThH |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 75 | `2026-09-12 16-45-10.bin` | 1025 | 113 | — | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 2 | 76 | `1980-01-12 15-45-52.bin` | 1025 | 107 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 3 | 77 | `2026-09-12 16-50-10.bin` | 1025 | 112 | 1 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 4 | 78 | `2026-09-12 17-15-12.bin` | 1025 | 112 | 2 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 5 | 79 | `2026-09-12 17-31-18.bin` | 1025 | 107 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 6 | 80 | `2026-09-12 17-35-39.bin` | 1025 | 107 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 7 | 81 | `2026-09-12 17-42-38.bin` | 1025 | 107 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 8 | 82 | `2026-09-12 17-47-06.bin` | 1025 | 111 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 9 | 88 | `2026-09-12 18-48-07.bin` | 1025 | 111 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 10 | 89 | `2026-09-12 18-59-08.bin` | 1025 | 112 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 11 | 90 | `2026-09-12 19-13-58.bin` | 1025 | 112 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 12 | 91 | `2026-09-12 19-41-52.bin` | 1025 | 107 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 13 | 94 | `2026-09-12 20-51-26.bin` | 1025 | 112 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 14 | 95 | `1980-01-12 20-17-44.bin` | 1025 | 106 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 15 | 96 | `2026-09-12 23-47-27.bin` | 1025 | 106 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 3300 | 0 | 1 | 0.35 |
| 16 | 115 | `2026-09-13 08-34-30.bin` | 1025 | 110 | 2 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 10.5 | 1 | 0.381312 |
| 17 | 116 | `2026-09-13 08-57-45.bin` | 1025 | 117 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 9 | 1 | 0.447916 |
| 18 | 117 | `1980-01-06 07-59-23.bin` | 1025 | 111 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 9 | 1 | 0.447916 |
| 19 | 118 | `1980-01-06 08-07-20.bin` | 1025 | 111 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 9 | 1 | 0.447916 |
| 20 | 119 | `2026-09-13 09-26-58.bin` | 1025 | 111 | 1 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 9 | 1 | 0.472593 |
| 21 | 120 | `2026-09-13 09-42-26.bin` | 1025 | 112 | 0 | 1000 | 0.0181906 | -0.00420208 | -1.14309 | 6000 | 9 | 1 | 0.472593 |
| 22 | 121 | `2026-09-13 09-53-45.bin` | 1025 | 116 | 0 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 6000 | 9 | 1 | 0.46451 |
| 23 | 122 | `2026-09-13 09-59-30.bin` | 1025 | 117 | 0 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 6000 | 9 | 1 | 0.459637 |
| 24 | 132 | `2026-09-14 19-43-06.bin` | 1025 | 117 | 1 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 8000 | 9 | 1 | 0.532559 |
| 25 | 134 | `2026-09-14 21-10-34.bin` | 1025 | 112 | 0 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 8000 | 9 | 1 | 0.49768 |
| 26 | 138 | `2026-09-15 11-14-33.bin` | 1025 | 117 | 0 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 8000 | 9 | 1 | 0.506167 |
| 27 | 139 | `2026-09-15 11-18-16.bin` | 1025 | 117 | 0 | 1000 | 0.0181906 | -0.00420208 | 6.03067 | 8000 | 9 | 1 | 0.506167 |

Default-dışı parametre sayısı aralığı: **106–117**. Bir fabrika sıfırlaması bu sayıyı ~0'a, RC*_MIN'i 1100'e, INS_ACC*OFFS/AHRS_TRIM/COMPASS_OFS'u 0'a ve **STAT_BOOTCNT'yi 0'a** çekerdi (STAT_* de parametredir). Bulgu §7'de.

## 3. İzlenen parametreler — log başındaki değer (kısa tablo)

| # | BOOT | log | MOT_THST_HOVER | BATT_CAPACITY | BATT_LOW_VOLT | BATT_CRT_VOLT | MOT_SPIN_MIN | MOT_SPIN_ARM | MOT_THST_EXPO | INS_HNTCH_ENABLE | INS_GYRO_FILTER | INS_ACCEL_FILTER | ATC_RAT_RLL_P | ATC_RAT_PIT_P | ATC_RAT_YAW_P | ATC_ANG_RLL_P | ATC_ANG_PIT_P | FS_THR_ENABLE | FS_GCS_ENABLE | FS_EKF_ACTION | ARMING_CHECK | LOG_BITMASK |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 75 | `2026-09-12 16-45-10` | 0.35 | 3300 | 14.4 | 14 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 2 | 76 | `1980-01-12 15-45-52` | 0.35 | 3300 | 14.4 | 14 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 3 | 77 | `2026-09-12 16-50-10` | 0.35 | 3300 | 10→14.5 | 14 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 4 | 78 | `2026-09-12 17-15-12` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 5 | 79 | `2026-09-12 17-31-18` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 6 | 80 | `2026-09-12 17-35-39` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 7 | 81 | `2026-09-12 17-42-38` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 8 | 82 | `2026-09-12 17-47-06` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 9 | 88 | `2026-09-12 18-48-07` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 10 | 89 | `2026-09-12 18-59-08` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 11 | 90 | `2026-09-12 19-13-58` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 12 | 91 | `2026-09-12 19-41-52` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 13 | 94 | `2026-09-12 20-51-26` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 14 | 95 | `1980-01-12 20-17-44` | 0.35 | 3300 | 0 | 0 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5→0 | 1 | 1 | 176126 |
| 15 | 96 | `2026-09-12 23-47-27` | 0.35→0.381312 | 3300 | 0→10 | 0→9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 0→5 | 1 | 1 | 176126 |
| 16 | 115 | `2026-09-13 08-34-30` | 0.381312→0.447916 | 6000 | 10→9 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 17 | 116 | `2026-09-13 08-57-45` | 0.447916 | 6000 | 9 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 18 | 117 | `1980-01-06 07-59-23` | 0.447916 | 6000 | 9 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 19 | 118 | `1980-01-06 08-07-20` | 0.447916→0.472593 | 6000 | 9 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 20 | 119 | `2026-09-13 09-26-58` | 0.472593 | 6000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 21 | 120 | `2026-09-13 09-42-26` | 0.472593→0.46451 | 6000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 22 | 121 | `2026-09-13 09-53-45` | 0.46451→0.459637 | 6000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 23 | 122 | `2026-09-13 09-59-30` | 0.459637→0.532559 | 6000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 24 | 132 | `2026-09-14 19-43-06` | 0.532559→0.49768 | 8000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 25 | 134 | `2026-09-14 21-10-34` | 0.49768→0.506167 | 8000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 26 | 138 | `2026-09-15 11-14-33` | 0.506167 | 8000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |
| 27 | 139 | `2026-09-15 11-18-16` | 0.506167→0.501742 | 8000 | 10 | 9 | 0.15 | 0.1 | 0.65 | 0 | 20 | 20 | 0.135 | 0.135 | 0.18 | 4.5 | 4.5 | 3 | 5 | 1 | 1 | 176126 |

`a→b`: değer log içinde değişti (zaman damgalı kayıt §4'te).

### 3a. İzlenen parametrelerin değer segmentleri (yalnız en az bir kez değişenler)

- `BATT_ARM_VOLT`: **0** (#1–#15) → **10.5** (#16) → **9** (#16–#27)
- `BATT_CAPACITY`: **3300** (#1–#15) → **6000** (#16–#23) → **8000** (#24–#27)
- `BATT_CRT_VOLT`: **14** (#1–#3) → **0** (#4–#15) → **9** (#15–#27)
- `BATT_LOW_VOLT`: **14.4** (#1–#2) → **10** (#3) → **14.5** (#3) → **0** (#4–#15) → **10** (#15–#16) → **9** (#16–#19) → **10** (#20–#27)
- `COMPASS_OFS2_X`: **29.7806** (#1–#21) → **43.9044** (#21–#27)
- `COMPASS_OFS2_Y`: **-159.516** (#1–#21) → **-84.3424** (#21–#27)
- `COMPASS_OFS2_Z`: **98.9213** (#1–#21) → **7.48364** (#21–#27)
- `COMPASS_OFS_X`: **-1.14309** (#1–#21) → **6.03067** (#21–#27)
- `COMPASS_OFS_Y`: **-3.03732** (#1–#21) → **12.2718** (#21–#27)
- `COMPASS_OFS_Z`: **16.3172** (#1–#21) → **16.621** (#21–#27)
- `FS_GCS_ENABLE`: **5** (#1–#14) → **0** (#14–#15) → **5** (#15–#27)
- `MOT_THST_HOVER`: **0.35** (#1–#15) → **0.381312** (#15–#16) → **0.447916** (#16–#19) → **0.472593** (#19–#21) → **0.46451** (#21–#22) → **0.459637** (#22–#23) → **0.532559** (#23–#24) → **0.49768** (#24–#25) → **0.506167** (#25–#27) → **0.501742** (#27)
- `STAT_BOOTCNT`: **75** (#1) → **76** (#2) → **77** (#3) → **78** (#4) → **79** (#5) → **80** (#6) → **81** (#7) → **82** (#8) → **88** (#9) → **89** (#10) → **90** (#11) → **91** (#12) → **94** (#13) → **95** (#14) → **96** (#15) → **115** (#16) → **116** (#17) → **117** (#18) → **118** (#19) → **119** (#20) → **120** (#21) → **121** (#22) → **122** (#23) → **132** (#24) → **134** (#25) → **138** (#26) → **139** (#27)
- `STAT_FLTTIME`: **128** (#1–#3) → **169** (#3–#4) → **173** (#4–#6) → **175** (#6–#8) → **179** (#8–#10) → **181** (#10–#13) → **206** (#13–#14) → **254** (#14–#15) → **301** (#15–#16) → **334** (#16–#19) → **370** (#19–#20) → **392** (#20–#21) → **493** (#21–#22) → **521** (#22–#23) → **748** (#23–#24) → **804** (#24–#25) → **834** (#25–#26) → **878** (#26–#27) → **942** (#27)
- `STAT_RUNTIME`: **44680** (#1) → **44711** (#1–#2) → **44927** (#2) → **44958** (#3) → **45389** (#3) → **45636** (#4) → **45760** (#4) → **45790** (#5) → **45852** (#5–#6) → **45975** (#6–#7) → **46036** (#7) → **46097** (#8) → **46127** (#8) → **46279** (#9) → **47084** (#9) → **47114** (#10) → **47176** (#10) → **47391** (#11) → **47700** (#11) → **47730** (#12) → **48160** (#12) → **49303** (#13) → **50884** (#13–#14) → **51596** (#14–#15) → **53145** (#15) → **64655** (#16) → **66049** (#16–#17) → **66141** (#17–#18) → **66481** (#18) → **66605** (#19) → **67038** (#19–#20) → **67716** (#20–#21) → **68366** (#21) → **68398** (#22) → **68552** (#22–#23) → **69760** (#23) → **95446** (#24) → **95632** (#24) → **100384** (#25) → **100569** (#25) → **109544** (#26) → **109760** (#26–#27) → **109976** (#27)

**Tüm loglarda sabit kalan izlenen parametreler:** `AHRS_TRIM_X=-0.00420208`, `AHRS_TRIM_Y=-0.0120333`, `AHRS_TRIM_Z=0`, `ARMING_CHECK=1`, `ATC_ANG_PIT_P=4.5`, `ATC_ANG_RLL_P=4.5`, `ATC_ANG_YAW_P=4.5`, `ATC_RAT_PIT_D=0.0036`, `ATC_RAT_PIT_I=0.135`, `ATC_RAT_PIT_P=0.135`, `ATC_RAT_RLL_D=0.0036`, `ATC_RAT_RLL_I=0.135`, `ATC_RAT_RLL_P=0.135`, `ATC_RAT_YAW_D=0`, `ATC_RAT_YAW_I=0.018`, `ATC_RAT_YAW_P=0.18`, `BATT_CRT_MAH=0`, `BATT_FS_CRT_ACT=1`, `BATT_FS_LOW_ACT=1`, `BATT_LOW_MAH=0`, `BATT_MONITOR=4`, `COMPASS_LEARN=0`, `COMPASS_OFS3_X=0`, `COMPASS_OFS3_Y=0`, `COMPASS_OFS3_Z=0`, `COMPASS_USE=1`, `COMPASS_USE2=1`, `FRAME_CLASS=1`, `FRAME_TYPE=1`, `FS_CRASH_CHECK=1`, `FS_DR_ENABLE=2`, `FS_DR_TIMEOUT=30`, `FS_EKF_ACTION=1`, `FS_EKF_FILT=5`, `FS_EKF_THRESH=0.8`, `FS_GCS_TIMEOUT=5`, `FS_OPTIONS=16`, `FS_THR_ENABLE=3`, `FS_THR_VALUE=975`, `FS_VIBE_ENABLE=1`, `INS_ACCEL_FILTER=20`, `INS_GYRO_FILTER=20`, `INS_HNTC2_ENABLE=0`, `INS_HNTCH_ENABLE=0`, `LOG_BITMASK=176126`, `LOG_DISARMED=0`, `MOT_BAT_VOLT_MAX=0`, `MOT_BAT_VOLT_MIN=0`, `MOT_HOVER_LEARN=2`, `MOT_PWM_MAX=2000`, `MOT_PWM_MIN=1000`, `MOT_SPIN_ARM=0.1`, `MOT_SPIN_MAX=0.95`, `MOT_SPIN_MIN=0.15`, `MOT_THST_EXPO=0.65`, `PILOT_THR_BHV=0`, `PSC_ACCZ_D=0`, `PSC_ACCZ_D_FF=0`, `PSC_ACCZ_FF=0`, `PSC_ACCZ_FLTD=0`, `PSC_ACCZ_FLTE=20`, `PSC_ACCZ_FLTT=0`, `PSC_ACCZ_I=1`, `PSC_ACCZ_IMAX=800`, `PSC_ACCZ_NEF=0`, `PSC_ACCZ_NTF=0`, `PSC_ACCZ_P=0.5`, `PSC_ACCZ_PDMX=0`, `PSC_ACCZ_SMAX=0`, `PSC_ANGLE_MAX=0`, `PSC_JERK_XY=5`, `PSC_JERK_Z=5`, `PSC_POSXY_P=1`, `PSC_POSZ_P=1`, `PSC_VELXY_D=0.5`, `PSC_VELXY_FF=0`, `PSC_VELXY_FLTD=5`, `PSC_VELXY_FLTE=5`, `PSC_VELXY_I=1`, `PSC_VELXY_IMAX=1000`, `PSC_VELXY_P=2`, `PSC_VELZ_D=0`, `PSC_VELZ_FF=0`, `PSC_VELZ_FLTD=5`, `PSC_VELZ_FLTE=5`, `PSC_VELZ_I=0`, `PSC_VELZ_IMAX=1000`, `PSC_VELZ_P=5`, `STAT_RESET=1`, `WPNAV_SPEED=300`, `WPNAV_SPEED_DN=150`, `WPNAV_SPEED_UP=250`

## 4. Ardışık loglar arasında ve log içinde DEĞİŞEN parametreler

Toplam 834 değişim kaydı. Sınıf dağılımı: GCS_AKIS=86, KALIBRASYON=14, KULLANICI=23, OGRENME=14, OTOMATIK=261, SAYAC=436. İzlenen listede: KALIBRASYON=6, KULLANICI=14, OGRENME=14, SAYAC=436.

### 4a. Kullanıcı / öğrenme / kalibrasyon değişimleri (SAYAC, OTOMATIK, GCS_AKIS hariç)

| # | BOOT | log | yer | t s | saat | parametre | eski → yeni | default | sınıf | kim |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 77 | `2026-09-12 16-50-10` | LOGLAR_ARASI | — | 2026-09-12 16:50:08 (log basi) | `BATT_LOW_VOLT` | 14.4 → 10 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 3 | 77 | `2026-09-12 16-50-10` | LOG_ICI | 159.6 | 2026-09-12 16:52:31 | `BATT_LOW_VOLT` | 10 → 14.5 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 4 | 78 | `2026-09-12 17-15-12` | LOGLAR_ARASI | — | 2026-09-12 17:15:12 (log basi) | `BATT_CRT_VOLT` | 14 → 0 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 4 | 78 | `2026-09-12 17-15-12` | LOGLAR_ARASI | — | 2026-09-12 17:15:12 (log basi) | `BATT_LOW_VOLT` | 14.5 → 0 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 14 | 95 | `1980-01-12 20-17-44` | LOG_ICI | 409.4 | 2026-09-12 21:24:23 | `FS_GCS_ENABLE` | 5 → 0 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 15 | 96 | `2026-09-12 23-47-27` | LOG_ICI | 285.3 | 2026-09-12 23:51:58 | `BATT_LOW_VOLT` | 0 → 10 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 15 | 96 | `2026-09-12 23-47-27` | LOG_ICI | 305 | 2026-09-12 23:52:17 | `BATT_CRT_VOLT` | 0 → 9 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 15 | 96 | `2026-09-12 23-47-27` | LOG_ICI | 482.6 | 2026-09-12 23:55:15 | `FS_GCS_ENABLE` | 0 → 5 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 15 | 96 | `2026-09-12 23-47-27` | LOG_ICI | 1138.8 | 2026-09-13 00:06:11 | `MOT_THST_HOVER` | 0.35 → 0.349373 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 15 | 96 | `2026-09-12 23-47-27` | LOG_ICI | 1245.8 | 2026-09-13 00:07:58 | `MOT_THST_HOVER` | 0.349373 → 0.381312 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 16 | 115 | `2026-09-13 08-34-30` | LOGLAR_ARASI | — | 2026-09-13 08:34:10 (log basi) | `BATT_ARM_VOLT` | 0 → 10.5 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 16 | 115 | `2026-09-13 08-34-30` | LOGLAR_ARASI | — | 2026-09-13 08:34:10 (log basi) | `BATT_CAPACITY` | 3300 → 6000 | 3300 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 16 | 115 | `2026-09-13 08-34-30` | LOG_ICI | 207.2 | 2026-09-13 08:37:22 | `MOT_THST_HOVER` | 0.381312 → 0.447916 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 16 | 115 | `2026-09-13 08-34-30` | LOG_ICI | 468.5 | 2026-09-13 08:41:44 | `BATT_ARM_VOLT` | 10.5 → 9 | 0 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 16 | 115 | `2026-09-13 08-34-30` | LOG_ICI | 468.6 | 2026-09-13 08:41:44 | `BATT_LOW_VOLT` | 10 → 9 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 16 | 115 | `2026-09-13 08-34-30` | LOG_ICI | 1129.8 | 2026-09-13 08:52:45 | `BATT_VOLT_MULT` | 18.18 → 17.1058 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 16 | 115 | `2026-09-13 08-34-30` | LOG_ICI | 1269.7 | 2026-09-13 08:55:05 | `BATT_VOLT_MULT` | 17.1058 → 17.0946 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 18 | 117 | `1980-01-06 07-59-23` | LOG_ICI | 407.1 | 2026-09-13 09:05:55 | `BATT_VOLT_MULT` | 17.0946 → 17.02 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 19 | 118 | `1980-01-06 08-07-20` | LOG_ICI | 104.1 | 2026-09-13 09:08:52 | `BATT_VOLT_MULT` | 17.02 → 19.5279 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 19 | 118 | `1980-01-06 08-07-20` | LOG_ICI | 214.5 | 2026-09-13 09:10:43 | `BATT_VOLT_MULT` | 19.5279 → 18.7267 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 19 | 118 | `1980-01-06 08-07-20` | LOG_ICI | 340.9 | 2026-09-13 09:12:49 | `MOT_THST_HOVER` | 0.447916 → 0.472593 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 20 | 119 | `2026-09-13 09-26-58` | LOGLAR_ARASI | — | 2026-09-13 09:26:58 (log basi) | `BATT_LOW_VOLT` | 9 → 10 | 10.5 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 20 | 119 | `2026-09-13 09-26-58` | LOG_ICI | 387.2 | 2026-09-13 09:33:11 | `BATT_VOLT_MULT` | 18.7267 → 18.0829 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 20 | 119 | `2026-09-13 09-26-58` | LOG_ICI | 389.6 | 2026-09-13 09:33:13 | `BATT_VOLT_MULT` | 18.0829 → 17.9415 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 211.2 | 2026-09-13 09:45:45 | `MOT_THST_HOVER` | 0.472593 → 0.466202 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 305 | 2026-09-13 09:47:19 | `MOT_THST_HOVER` | 0.466202 → 0.46451 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 565.9 | 2026-09-13 09:51:40 | `COMPASS_OFS2_X` | 29.7806 → 43.9044 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 565.9 | 2026-09-13 09:51:40 | `COMPASS_OFS2_Y` | -159.516 → -84.3424 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 565.9 | 2026-09-13 09:51:40 | `COMPASS_OFS2_Z` | 98.9213 → 7.48364 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 565.9 | 2026-09-13 09:51:40 | `COMPASS_SCALE2` | 0.926882 → 1.07267 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_OFS_X` | -1.14309 → 6.03067 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_OFS_Y` | -3.03732 → 12.2718 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_OFS_Z` | 16.3172 → 16.621 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_DIA_X` | 1.0505 → 0.998981 | 1 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_DIA_Y` | 0.954777 → 0.912364 | 1 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_DIA_Z` | 1.06572 → 1.0298 | 1 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_ODI_X` | 0.0190427 → 0.0120302 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_ODI_Y` | 0.0329281 → 0.0316082 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_ODI_Z` | -0.00544452 → -0.00129337 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 21 | 120 | `2026-09-13 09-42-26` | LOG_ICI | 634.7 | 2026-09-13 09:52:49 | `COMPASS_SCALE` | 1.02004 → 1.06647 | 0 | KALIBRASYON | kalibrasyon (pusula; COMPASS_LEARN=0.0 → kullanici tetikledi) |
| 22 | 121 | `2026-09-13 09-53-45` | LOG_ICI | 123.7 | 2026-09-13 09:55:10 | `MOT_THST_HOVER` | 0.46451 → 0.459637 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 23 | 122 | `2026-09-13 09-59-30` | LOG_ICI | 83.8 | 2026-09-13 10:00:36 | `MOT_THST_HOVER` | 0.459637 → 0.460352 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 23 | 122 | `2026-09-13 09-59-30` | LOG_ICI | 520.7 | 2026-09-13 10:07:53 | `BATT_VOLT_MULT` | 17.9415 → 18.3417 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 23 | 122 | `2026-09-13 09-59-30` | LOG_ICI | 523.6 | 2026-09-13 10:07:55 | `BATT_VOLT_MULT` | 18.3417 → 18.3878 | 18.18 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 23 | 122 | `2026-09-13 09-59-30` | LOG_ICI | 756 | 2026-09-13 10:11:48 | `MOT_THST_HOVER` | 0.460352 → 0.532062 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 23 | 122 | `2026-09-13 09-59-30` | LOG_ICI | 872.1 | 2026-09-13 10:13:44 | `MOT_THST_HOVER` | 0.532062 → 0.532559 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 24 | 132 | `2026-09-14 19-43-06` | LOGLAR_ARASI | — | 2026-09-14 19:43:06 (log basi) | `BATT_CAPACITY` | 6000 → 8000 | 3300 | KULLANICI | kullanici (GCS/Mission Planner ile yazildi) |
| 24 | 132 | `2026-09-14 19-43-06` | LOG_ICI | 132.8 | 2026-09-14 19:44:23 | `MOT_THST_HOVER` | 0.532559 → 0.515692 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 24 | 132 | `2026-09-14 19-43-06` | LOG_ICI | 185.3 | 2026-09-14 19:45:15 | `MOT_THST_HOVER` | 0.515692 → 0.49768 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 25 | 134 | `2026-09-14 21-10-34` | LOG_ICI | 151.9 | 2026-09-14 21:12:40 | `MOT_THST_HOVER` | 0.49768 → 0.506167 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |
| 27 | 139 | `2026-09-15 11-18-16` | LOG_ICI | 177.9 | 2026-09-15 11:21:00 | `MOT_THST_HOVER` | 0.506167 → 0.501742 | 0.35 | OGRENME | Copter ogrenme (MOT_HOVER_LEARN=2: askida ogrenir, DISARM'da kaydeder) |

### 4b. Otomatik / sayaç / GCS-akış değişimleri (özet)

- `BARO1_GND_PRESS` (OTOMATIK): 39 kez
- `COMPASS_DEC` (OTOMATIK): 15 kez
- `INS_GYR1_CALTEMP` (OTOMATIK): 25 kez
- `INS_GYR2OFFS_X` (OTOMATIK): 26 kez
- `INS_GYR2OFFS_Y` (OTOMATIK): 26 kez
- `INS_GYR2OFFS_Z` (OTOMATIK): 26 kez
- `INS_GYR2_CALTEMP` (OTOMATIK): 26 kez
- `INS_GYROFFS_X` (OTOMATIK): 26 kez
- `INS_GYROFFS_Y` (OTOMATIK): 26 kez
- `INS_GYROFFS_Z` (OTOMATIK): 26 kez
- `SR1_EXTRA1` (GCS_AKIS): 12 kez
- `SR1_EXTRA2` (GCS_AKIS): 12 kez
- `SR1_EXTRA3` (GCS_AKIS): 14 kez
- `SR1_EXT_STAT` (GCS_AKIS): 12 kez
- `SR1_POSITION` (GCS_AKIS): 12 kez
- `SR1_RAW_SENS` (GCS_AKIS): 12 kez
- `SR1_RC_CHAN` (GCS_AKIS): 12 kez
- `STAT_BOOTCNT` (SAYAC): 26 kez
- `STAT_FLTTIME` (SAYAC): 62 kez
- `STAT_RUNTIME` (SAYAC): 348 kez

## 5. Olay dökümü (ERR / MSG / MODE / EV / ARM) — kronolojik

Sınıf sayıları (tüm loglar): **arm**=234, **arm_ret**=282, **banner**=440, **compass**=2, **diger**=26, **ekf**=152, **ev**=380, **failsafe**=107, **gps**=133, **kip**=171, **kip_red**=2, **motor_test**=29, **prearm**=340, **thrust_loss**=2.

Tür sayıları: ARM=117, ERR=111, EV=519, MODE=178, MSG=1375.

### 5a. Kritik olaylar özeti — tüm ERR, failsafe nedenli MODE, failsafe/thrust-loss/crash/vibe/EKF-varyans/kip-red/motor-test MSG

| # | log | t s | saat | tür | sınıf | olay | n |
|---|---|---|---|---|---|---|---|
| 2 | `1980-01-12 15-45-52` | 6.2 | 2026-09-12 16:45:46 | MSG | ekf | AHRS: EKF3 active | 1 |
| 3 | `2026-09-12 16-50-10` | 381.6 | 2026-09-12 16:56:13 | MSG | ekf | EKF3 lane switch 1 | 1 |
| 3 | `2026-09-12 16-50-10` | 381.6 | 2026-09-12 16:56:13 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 1(1) | 1 |
| 3 | `2026-09-12 16-50-10` | 381.6 | 2026-09-12 16:56:13 | MSG | ekf | EKF primary changed:1 | 1 |
| 3 | `2026-09-12 16-50-10` | 383.2 | 2026-09-12 16:56:14 | ERR | thrust_loss | THRUST_LOSS_CHECK(25) / TETIKLENDI(1) | 1 |
| 3 | `2026-09-12 16-50-10` | 383.2 | 2026-09-12 16:56:14 | MSG | thrust_loss | Potential Thrust Loss (3) | 1 |
| 3 | `2026-09-12 16-50-10` | 383.3 | 2026-09-12 16:56:14 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 0(0) | 1 |
| 3 | `2026-09-12 16-50-10` | 383.3 | 2026-09-12 16:56:14 | MSG | ekf | EKF primary changed:0 | 1 |
| 9 | `2026-09-12 18-48-07` | 23.1–805.7 | 2026-09-12 18:38:40 | MSG | motor_test | starting motor test | 29 |
| 11 | `2026-09-12 19-13-58` | 532.6 | 2026-09-12 19:19:10 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 126.6 | 2026-09-12 19:43:21 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 174 | 2026-09-12 19:44:09 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 199.2 | 2026-09-12 19:44:34 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 268.1 | 2026-09-12 19:45:43 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 268.1 | 2026-09-12 19:45:43 | MSG | ekf | EKF variance | 1 |
| 12 | `2026-09-12 19-41-52` | 268.1 | 2026-09-12 19:45:43 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 12 | `2026-09-12 19-41-52` | 269.8 | 2026-09-12 19:45:44 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 269.8 | 2026-09-12 19:45:44 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 272.9 | 2026-09-12 19:45:48 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 272.9 | 2026-09-12 19:45:48 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 12 | `2026-09-12 19-41-52` | 274.7 | 2026-09-12 19:45:49 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 274.7 | 2026-09-12 19:45:49 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 319.7 | 2026-09-12 19:46:34 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 12 | `2026-09-12 19-41-52` | 319.7 | 2026-09-12 19:46:34 | MSG | ekf | EKF variance | 1 |
| 12 | `2026-09-12 19-41-52` | 319.7 | 2026-09-12 19:46:34 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 12 | `2026-09-12 19-41-52` | 323.3 | 2026-09-12 19:46:38 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 323.3 | 2026-09-12 19:46:38 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 334 | 2026-09-12 19:46:49 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 12 | `2026-09-12 19-41-52` | 471.4 | 2026-09-12 19:49:06 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 13 | `2026-09-12 20-51-26` | 292 | 2026-09-12 20:53:16 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 13 | `2026-09-12 20-51-26` | 292 | 2026-09-12 20:53:16 | MSG | failsafe | GCS Failsafe | 1 |
| 13 | `2026-09-12 20-51-26` | 1285.9 | 2026-09-12 21:09:50 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 13 | `2026-09-12 20-51-26` | 1285.9 | 2026-09-12 21:09:50 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 13 | `2026-09-12 20-51-26` | 1333.7 | 2026-09-12 21:10:38 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 13 | `2026-09-12 20-51-26` | 1333.7 | 2026-09-12 21:10:38 | MSG | failsafe | GCS Failsafe | 1 |
| 14 | `1980-01-12 20-17-44` | 5.2 | 2026-09-12 21:17:39 | MSG | ekf | AHRS: EKF3 active | 1 |
| 14 | `1980-01-12 20-17-44` | 54.1 | 2026-09-12 21:18:28 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 14 | `1980-01-12 20-17-44` | 54.1 | 2026-09-12 21:18:28 | MSG | failsafe | GCS Failsafe | 1 |
| 14 | `1980-01-12 20-17-44` | 70.7 | 2026-09-12 21:18:44 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 14 | `1980-01-12 20-17-44` | 70.7 | 2026-09-12 21:18:44 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 14 | `1980-01-12 20-17-44` | 580.1 | 2026-09-12 21:27:14 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 289 | 2026-09-12 23:52:02 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 331.8 | 2026-09-12 23:52:44 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 364.8 | 2026-09-12 23:53:17 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 371.4 | 2026-09-12 23:53:24 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 669 | 2026-09-12 23:58:22 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 747.4 | 2026-09-12 23:59:40 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 753.4 | 2026-09-12 23:59:46 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1113.2 | 2026-09-13 00:05:46 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 1132.1 | 2026-09-13 00:06:05 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1132.1 | 2026-09-13 00:06:05 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) | 1 |
| 15 | `2026-09-12 23-47-27` | 1132.1 | 2026-09-13 00:06:05 | MSG | failsafe | Radio Failsafe | 1 |
| 15 | `2026-09-12 23-47-27` | 1132.1 | 2026-09-13 00:06:05 | MODE | failsafe | → LAND (9), neden RADIO_FAILSAFE(3) | 1 |
| 15 | `2026-09-12 23-47-27` | 1140 | 2026-09-13 00:06:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1143.3 | 2026-09-13 00:06:16 | ERR | failsafe | FAILSAFE_RADIO(5) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 1143.3 | 2026-09-13 00:06:16 | MSG | failsafe | Radio Failsafe Cleared | 1 |
| 15 | `2026-09-12 23-47-27` | 1211 | 2026-09-13 00:07:24 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 1236.8 | 2026-09-13 00:07:49 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1238.7 | 2026-09-13 00:07:51 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1238.7 | 2026-09-13 00:07:51 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) | 1 |
| 15 | `2026-09-12 23-47-27` | 1238.7 | 2026-09-13 00:07:51 | MSG | failsafe | Radio Failsafe | 1 |
| 15 | `2026-09-12 23-47-27` | 1238.7 | 2026-09-13 00:07:51 | MODE | failsafe | → LAND (9), neden RADIO_FAILSAFE(3) | 1 |
| 15 | `2026-09-12 23-47-27` | 1396.2 | 2026-09-13 00:10:29 | ERR | failsafe | FAILSAFE_RADIO(5) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 1396.2 | 2026-09-13 00:10:29 | MSG | failsafe | Radio Failsafe Cleared | 1 |
| 15 | `2026-09-12 23-47-27` | 1406.5 | 2026-09-13 00:10:39 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) | 1 |
| 15 | `2026-09-12 23-47-27` | 1406.5 | 2026-09-13 00:10:39 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) | 1 |
| 15 | `2026-09-12 23-47-27` | 1406.5 | 2026-09-13 00:10:39 | MSG | failsafe | Radio Failsafe - Disarming | 1 |
| 15 | `2026-09-12 23-47-27` | 1437.2 | 2026-09-13 00:11:10 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 15 | `2026-09-12 23-47-27` | 1560.2 | 2026-09-13 00:13:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 195.7 | 2026-09-13 08:37:11 | MSG | failsafe | Battery 1 is low 9.75V used 216 mAh | 1 |
| 16 | `2026-09-13 08-34-30` | 195.7 | 2026-09-13 08:37:11 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 195.7 | 2026-09-13 08:37:11 | MSG | failsafe | Battery Failsafe | 1 |
| 16 | `2026-09-13 08-34-30` | 195.7 | 2026-09-13 08:37:11 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) | 1 |
| 16 | `2026-09-13 08-34-30` | 371.2 | 2026-09-13 08:40:06 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 499 | 2026-09-13 08:42:14 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 499 | 2026-09-13 08:42:14 | MSG | ekf | EKF variance | 1 |
| 16 | `2026-09-13 08-34-30` | 499 | 2026-09-13 08:42:14 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 500.4 | 2026-09-13 08:42:16 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 500.4 | 2026-09-13 08:42:16 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 620.6 | 2026-09-13 08:44:16 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 620.6 | 2026-09-13 08:44:16 | MSG | ekf | EKF variance | 1 |
| 16 | `2026-09-13 08-34-30` | 620.6 | 2026-09-13 08:44:16 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 631.7 | 2026-09-13 08:44:27 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 631.7 | 2026-09-13 08:44:27 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 781.5 | 2026-09-13 08:46:57 | MSG | ekf | EKF3 lane switch 1 | 1 |
| 16 | `2026-09-13 08-34-30` | 781.6 | 2026-09-13 08:46:57 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 781.6 | 2026-09-13 08:46:57 | MSG | ekf | EKF variance | 1 |
| 16 | `2026-09-13 08-34-30` | 781.6 | 2026-09-13 08:46:57 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 784.4 | 2026-09-13 08:47:00 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 784.4 | 2026-09-13 08:47:00 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 870 | 2026-09-13 08:48:25 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 870 | 2026-09-13 08:48:25 | MSG | ekf | EKF variance | 1 |
| 16 | `2026-09-13 08-34-30` | 870 | 2026-09-13 08:48:25 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 877.1 | 2026-09-13 08:48:32 | MSG | ekf | EKF3 IMU0 stopped aiding | 1 |
| 16 | `2026-09-13 08-34-30` | 877.1 | 2026-09-13 08:48:32 | MSG | ekf | EKF3 IMU1 stopped aiding | 1 |
| 16 | `2026-09-13 08-34-30` | 877.1 | 2026-09-13 08:48:32 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 1373.9 | 2026-09-13 08:56:49 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 1373.9 | 2026-09-13 08:56:49 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) | 1 |
| 16 | `2026-09-13 08-34-30` | 1373.9 | 2026-09-13 08:56:49 | MSG | failsafe | Radio Failsafe - Disarming | 1 |
| 16 | `2026-09-13 08-34-30` | 1391.7 | 2026-09-13 08:57:07 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 16 | `2026-09-13 08-34-30` | 1392.6 | 2026-09-13 08:57:08 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 1392.6 | 2026-09-13 08:57:08 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 16 | `2026-09-13 08-34-30` | 1393.1 | 2026-09-13 08:57:08 | ERR | gps | GPS(11) / temizlendi(0) | 1 |
| 19 | `1980-01-06 08-07-20` | 319.7 | 2026-09-13 09:12:28 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 19 | `1980-01-06 08-07-20` | 319.7 | 2026-09-13 09:12:28 | MSG | failsafe | GCS Failsafe - Continuing Pilot Control | 1 |
| 19 | `1980-01-06 08-07-20` | 320.7 | 2026-09-13 09:12:29 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 19 | `1980-01-06 08-07-20` | 320.7 | 2026-09-13 09:12:29 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 19 | `1980-01-06 08-07-20` | 325.6 | 2026-09-13 09:12:34 | MSG | failsafe | Battery 1 is low 9.73V used 227 mAh | 1 |
| 19 | `1980-01-06 08-07-20` | 325.6 | 2026-09-13 09:12:34 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) | 1 |
| 19 | `1980-01-06 08-07-20` | 325.6 | 2026-09-13 09:12:34 | MSG | failsafe | Battery Failsafe | 1 |
| 19 | `1980-01-06 08-07-20` | 325.6 | 2026-09-13 09:12:34 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) | 1 |
| 19 | `1980-01-06 08-07-20` | 401.6 | 2026-09-13 09:13:50 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 20 | `2026-09-13 09-26-58` | 405.5 | 2026-09-13 09:33:29 | MSG | kip_red | Mode change to STABILIZE failed: throttle too high | 1 |
| 20 | `2026-09-13 09-26-58` | 405.5 | 2026-09-13 09:33:29 | ERR | kip_red | FLIGHT_MODE(10) / kip STABILIZE reddedildi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 174.1 | 2026-09-13 09:45:08 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 174.1 | 2026-09-13 09:45:08 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 179 | 2026-09-13 09:45:13 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 179 | 2026-09-13 09:45:13 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 198 | 2026-09-13 09:45:32 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 198 | 2026-09-13 09:45:32 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 198 | 2026-09-13 09:45:32 | MODE | failsafe | → LAND (9), neden GCS_FAILSAFE(5) | 1 |
| 21 | `2026-09-13 09-42-26` | 201 | 2026-09-13 09:45:35 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 201 | 2026-09-13 09:45:35 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 206 | 2026-09-13 09:45:40 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 206 | 2026-09-13 09:45:40 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 209.6 | 2026-09-13 09:45:44 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 209.6 | 2026-09-13 09:45:44 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 217.6 | 2026-09-13 09:45:52 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 217.6 | 2026-09-13 09:45:52 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 244.9 | 2026-09-13 09:46:19 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 244.9 | 2026-09-13 09:46:19 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 288.4 | 2026-09-13 09:47:02 | MSG | failsafe | Battery 1 is low 9.85V used 696 mAh | 1 |
| 21 | `2026-09-13 09-42-26` | 288.4 | 2026-09-13 09:47:02 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 288.4 | 2026-09-13 09:47:02 | MSG | failsafe | Battery Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 288.4 | 2026-09-13 09:47:02 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) | 1 |
| 21 | `2026-09-13 09-42-26` | 310 | 2026-09-13 09:47:24 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 310 | 2026-09-13 09:47:24 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 424.8 | 2026-09-13 09:49:19 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 424.8 | 2026-09-13 09:49:19 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 21 | `2026-09-13 09-42-26` | 550.1 | 2026-09-13 09:51:24 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 21 | `2026-09-13 09-42-26` | 550.1 | 2026-09-13 09:51:24 | MSG | failsafe | GCS Failsafe | 1 |
| 21 | `2026-09-13 09-42-26` | 550.4 | 2026-09-13 09:51:24 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 21 | `2026-09-13 09-42-26` | 550.4 | 2026-09-13 09:51:24 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 22 | `2026-09-13 09-53-45` | 81.4 | 2026-09-13 09:54:27 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 22 | `2026-09-13 09-53-45` | 81.4 | 2026-09-13 09:54:27 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 22 | `2026-09-13 09-53-45` | 108.9 | 2026-09-13 09:54:55 | MSG | failsafe | Battery 1 is low 9.78V used 133 mAh | 1 |
| 22 | `2026-09-13 09-53-45` | 108.9 | 2026-09-13 09:54:55 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) | 1 |
| 22 | `2026-09-13 09-53-45` | 108.9 | 2026-09-13 09:54:55 | MSG | failsafe | Battery Failsafe | 1 |
| 22 | `2026-09-13 09-53-45` | 108.9 | 2026-09-13 09:54:55 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) | 1 |
| 23 | `2026-09-13 09-59-30` | 222.2 | 2026-09-13 10:02:54 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 23 | `2026-09-13 09-59-30` | 222.2 | 2026-09-13 10:02:54 | MSG | failsafe | GCS Failsafe | 1 |
| 23 | `2026-09-13 09-59-30` | 238.2 | 2026-09-13 10:03:10 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 23 | `2026-09-13 09-59-30` | 238.2 | 2026-09-13 10:03:10 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 23 | `2026-09-13 09-59-30` | 301.7 | 2026-09-13 10:04:14 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 23 | `2026-09-13 09-59-30` | 301.7 | 2026-09-13 10:04:14 | MSG | failsafe | GCS Failsafe | 1 |
| 23 | `2026-09-13 09-59-30` | 369.2 | 2026-09-13 10:05:21 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 23 | `2026-09-13 09-59-30` | 369.2 | 2026-09-13 10:05:21 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 23 | `2026-09-13 09-59-30` | 416.1 | 2026-09-13 10:06:08 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 23 | `2026-09-13 09-59-30` | 416.1 | 2026-09-13 10:06:08 | MSG | failsafe | GCS Failsafe | 1 |
| 23 | `2026-09-13 09-59-30` | 426.1 | 2026-09-13 10:06:18 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 23 | `2026-09-13 09-59-30` | 426.1 | 2026-09-13 10:06:18 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |
| 23 | `2026-09-13 09-59-30` | 869 | 2026-09-13 10:13:41 | MSG | ekf | EKF3 lane switch 1 | 1 |
| 23 | `2026-09-13 09-59-30` | 869 | 2026-09-13 10:13:41 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 1(1) | 1 |
| 23 | `2026-09-13 09-59-30` | 869 | 2026-09-13 10:13:41 | MSG | ekf | EKF primary changed:1 | 1 |
| 23 | `2026-09-13 09-59-30` | 872.1 | 2026-09-13 10:13:44 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 0(0) | 1 |
| 23 | `2026-09-13 09-59-30` | 872.1 | 2026-09-13 10:13:44 | MSG | ekf | EKF primary changed:0 | 1 |
| 23 | `2026-09-13 09-59-30` | 1089.4 | 2026-09-13 10:17:21 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 23 | `2026-09-13 09-59-30` | 1089.4 | 2026-09-13 10:17:21 | MSG | failsafe | GCS Failsafe | 1 |
| 23 | `2026-09-13 09-59-30` | 1200.9 | 2026-09-13 10:19:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 24 | `2026-09-14 19-43-06` | 197.7 | 2026-09-14 19:45:28 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 24 | `2026-09-14 19-43-06` | 206.9 | 2026-09-14 19:45:37 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) | 1 |
| 24 | `2026-09-14 19-43-06` | 206.9 | 2026-09-14 19:45:37 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) | 1 |
| 24 | `2026-09-14 19-43-06` | 206.9 | 2026-09-14 19:45:37 | MSG | failsafe | Radio Failsafe - Disarming | 1 |
| 25 | `2026-09-14 21-10-34` | 161.8 | 2026-09-14 21:12:50 | ERR | gps | GPS(11) / GPS_GLITCH(2) | 1 |
| 25 | `2026-09-14 21-10-34` | 178.7 | 2026-09-14 21:13:07 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) | 1 |
| 25 | `2026-09-14 21-10-34` | 178.7 | 2026-09-14 21:13:07 | MSG | ekf | EKF variance | 1 |
| 25 | `2026-09-14 21-10-34` | 178.7 | 2026-09-14 21:13:07 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) | 1 |
| 25 | `2026-09-14 21-10-34` | 182.8 | 2026-09-14 21:13:11 | ERR | ekf | EKFCHECK(16) / temizlendi(0) | 1 |
| 25 | `2026-09-14 21-10-34` | 182.8 | 2026-09-14 21:13:11 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) | 1 |
| 27 | `2026-09-15 11-18-16` | 63.7 | 2026-09-15 11:19:06 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) | 1 |
| 27 | `2026-09-15 11-18-16` | 63.7 | 2026-09-15 11:19:06 | MSG | failsafe | GCS Failsafe | 1 |
| 27 | `2026-09-15 11-18-16` | 64.1 | 2026-09-15 11:19:06 | MSG | failsafe | GCS Failsafe Cleared | 1 |
| 27 | `2026-09-15 11-18-16` | 64.1 | 2026-09-15 11:19:06 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) | 1 |

Kritik olay sayıları: ERR EKFCHECK tetik=8, ERR EKF_PRIMARY tetik=2, ERR FAILSAFE_BATT tetik=4, ERR FAILSAFE_EKFINAV tetik=8, ERR FAILSAFE_GCS tetik=15, ERR FAILSAFE_RADIO tetik=5, ERR GPS tetik=18, ERR RADIO tetik=5, ERR THRUST_LOSS_CHECK tetik=1, MODE failsafe→LAND (BATTERY_FAILSAFE)=4, MODE failsafe→LAND (GCS_FAILSAFE)=1, MODE failsafe→LAND (RADIO_FAILSAFE)=2, MSG failsafe=44, MSG kip_red=1, MSG motor_test=29, MSG thrust_loss=1.

### #1 · BOOT 75 · `2026-09-12 16-45-10.bin` · 2026-09-12 16:45:10 · 25.8 s · 3S/12.11 V · beyan A · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | ChibiOS: 6a85082c |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | Param space used: 875/5376 |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | RC Protocol: IBUS |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | RCOut: PWM:1-16 |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | New mission |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | New rally |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | New fence |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | Frame: QUAD/X |
| 130.1 | 2026-09-12 16:45:10 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 130.1 | 2026-09-12 16:45:10 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 130.1 | 2026-09-12 16:45:10 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 133.7 | 2026-09-12 16:45:14 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 137.4 | 2026-09-12 16:45:17 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 140.9 | 2026-09-12 16:45:21 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 153.7 | 2026-09-12 16:45:34 | MSG | prearm | PreArm: Battery 1 low voltage failsafe |

### #2 · BOOT 76 · `1980-01-12 15-45-52.bin` · 2026-09-12 16:45:45 · 217.1 s · 3S/12.11 V · beyan A* · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | ChibiOS: 6a85082c |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | Param space used: 875/5376 |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | RC Protocol: IBUS |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | RCOut: PWM:1-16 |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | New mission |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | New rally |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | New fence |
| 5.3 | 2026-09-12 16:45:45 | MSG | banner | Frame: QUAD/X |
| 5.3 | 2026-09-12 16:45:45 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 6.2 | 2026-09-12 16:45:46 | MSG | ekf | EKF3 IMU0 initialised |
| 6.2 | 2026-09-12 16:45:46 | MSG | ekf | EKF3 IMU1 initialised |
| 6.2 | 2026-09-12 16:45:46 | MSG | ekf | AHRS: EKF3 active |
| 7.6 | 2026-09-12 16:45:48 | MSG | ekf | EKF3 IMU0 tilt alignment complete |
| 7.6 | 2026-09-12 16:45:48 | MSG | ekf | EKF3 IMU1 tilt alignment complete |
| 7.7 | 2026-09-12 16:45:48 | MSG | ekf | EKF3 IMU0 MAG0 initial yaw alignment complete |
| 7.7 | 2026-09-12 16:45:48 | MSG | ekf | EKF3 IMU1 MAG0 initial yaw alignment complete |
| 7.7 | 2026-09-12 16:45:48 | EV | ekf | EKF_YAW_RESET(62) |
| 11.6 | 2026-09-12 16:45:52 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 207.4 | 2026-09-12 16:49:07 | MSG | arm_ret | Arm: Battery 1 critical voltage failsafe |
| 216.2 | 2026-09-12 16:49:16 | MSG | prearm | PreArm: Battery 1 critical voltage failsafe |

### #3 · BOOT 77 · `2026-09-12 16-50-10.bin` · 2026-09-12 16:50:08 · 414.0 s · 3S/11.95 V · beyan A · uçuş 2/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | ChibiOS: 6a85082c |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | Param space used: 875/5376 |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | RC Protocol: IBUS |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | RCOut: PWM:1-16 |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | New mission |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | New rally |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | New fence |
| 17.2 | 2026-09-12 16:50:08 | MSG | banner | Frame: QUAD/X |
| 17.2 | 2026-09-12 16:50:08 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 18.4 | 2026-09-12 16:50:09 | MSG | arm_ret | Arm: Accels inconsistent |
| 18.4 | 2026-09-12 16:50:09 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 18.4 | 2026-09-12 16:50:09 | MSG | arm_ret | Arm: Battery 1 critical voltage failsafe |
| 18.4 | 2026-09-12 16:50:09 | MSG | arm_ret | Arm: Fence requires position |
| 18.4 | 2026-09-12 16:50:09 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 19.7 | 2026-09-12 16:50:11 | MSG | arm_ret | Arm: Accels inconsistent |
| 19.7 | 2026-09-12 16:50:11 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 19.7 | 2026-09-12 16:50:11 | MSG | arm_ret | Arm: Battery 1 critical voltage failsafe |
| 19.7 | 2026-09-12 16:50:11 | MSG | arm_ret | Arm: Fence requires position |
| 28.4 | 2026-09-12 16:50:20 | MSG | ekf | EKF3 IMU1 origin set |
| 28.4 | 2026-09-12 16:50:20 | EV | ev | SET_HOME(25) |
| 28.5 | 2026-09-12 16:50:20 | MSG | diger | Field Elevation Set: 101m |
| 28.6 | 2026-09-12 16:50:20 | MSG | ekf | EKF3 IMU0 origin set |
| 30.1 | 2026-09-12 16:50:21 | MSG | prearm | PreArm: Gyros inconsistent |
| 30.1 | 2026-09-12 16:50:21 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.1 | 2026-09-12 16:50:21 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3C8 |
| 30.1 | 2026-09-12 16:50:21 | MSG | prearm | PreArm: Battery 1 critical voltage failsafe |
| 33.2 | 2026-09-12 16:50:24 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 91.1 | 2026-09-12 16:51:22 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 150.2 | 2026-09-12 16:52:21 | MSG | arm_ret | Arm: Battery 1 critical voltage failsafe |
| 151 | 2026-09-12 16:52:22 | MSG | arm_ret | Arm: Battery 1 critical voltage failsafe |
| 152.1 | 2026-09-12 16:52:23 | MSG | prearm | PreArm: Battery 1 critical voltage failsafe |
| 183.1 | 2026-09-12 16:52:54 | MSG | prearm | PreArm: Battery 1 low voltage failsafe |
| 184 | 2026-09-12 16:52:55 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 185.2 | 2026-09-12 16:52:56 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 186.5 | 2026-09-12 16:52:58 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 191.3 | 2026-09-12 16:53:02 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 192.2 | 2026-09-12 16:53:03 | MSG | arm_ret | Arm: Battery 1 low voltage failsafe |
| 307.7 | 2026-09-12 16:54:59 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 309.7 | 2026-09-12 16:55:01 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 310.4 | 2026-09-12 16:55:02 | EV | ev | AUTO_ARMED(15) |
| 310.6 | 2026-09-12 16:55:02 | EV | ev | NOT_LANDED(28) |
| 318.2 | 2026-09-12 16:55:09 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 318.8 | 2026-09-12 16:55:10 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 318.8 | 2026-09-12 16:55:10 | EV | arm | DISARMED(11) |
| 318.8 | 2026-09-12 16:55:10 | EV | ev | LAND_COMPLETE(18) |
| 318.8 | 2026-09-12 16:55:10 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 334.9 | 2026-09-12 16:55:26 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 345.5 | 2026-09-12 16:55:37 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 345.5 | 2026-09-12 16:55:37 | EV | arm | ARMED(10) |
| 345.5 | 2026-09-12 16:55:37 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 347.5 | 2026-09-12 16:55:39 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 347.9 | 2026-09-12 16:55:39 | EV | ev | AUTO_ARMED(15) |
| 350.2 | 2026-09-12 16:55:41 | EV | ev | NOT_LANDED(28) |
| 366.5 | 2026-09-12 16:55:58 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 366.5 | 2026-09-12 16:55:58 | EV | ekf | EKF_YAW_RESET(62) |
| 366.6 | 2026-09-12 16:55:58 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 381.6 | 2026-09-12 16:56:13 | MSG | ekf | EKF3 lane switch 1 |
| 381.6 | 2026-09-12 16:56:13 | EV | ekf | EKF_YAW_RESET(62) |
| 381.6 | 2026-09-12 16:56:13 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 1(1) |
| 381.6 | 2026-09-12 16:56:13 | MSG | ekf | EKF primary changed:1 |
| 382.1 | 2026-09-12 16:56:13 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 383.2 | 2026-09-12 16:56:14 | ERR | thrust_loss | THRUST_LOSS_CHECK(25) / TETIKLENDI(1) |
| 383.2 | 2026-09-12 16:56:14 | MSG | thrust_loss | Potential Thrust Loss (3) |
| 383.3 | 2026-09-12 16:56:14 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 383.3 | 2026-09-12 16:56:14 | EV | arm | DISARMED(11) |
| 383.3 | 2026-09-12 16:56:14 | EV | ev | LAND_COMPLETE(18) |
| 383.3 | 2026-09-12 16:56:14 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 383.3 | 2026-09-12 16:56:14 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 383.3 | 2026-09-12 16:56:14 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 0(0) |
| 383.3 | 2026-09-12 16:56:14 | MSG | ekf | EKF primary changed:0 |

### #4 · BOOT 78 · `2026-09-12 17-15-12.bin` · 2026-09-12 17:15:12 · 93.8 s · 3S/11.27 V · beyan A · uçuş 0/kısa 3

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | ChibiOS: 6a85082c |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | Param space used: 875/5376 |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | RC Protocol: IBUS |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | RCOut: PWM:1-16 |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | New mission |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | New rally |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | New fence |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | Frame: QUAD/X |
| 277.5 | 2026-09-12 17:15:12 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 277.5 | 2026-09-12 17:15:12 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 277.5 | 2026-09-12 17:15:12 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 279.4 | 2026-09-12 17:15:14 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 280 | 2026-09-12 17:15:15 | EV | ev | AUTO_ARMED(15) |
| 281.1 | 2026-09-12 17:15:16 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 281.1 | 2026-09-12 17:15:16 | EV | arm | DISARMED(11) |
| 281.1 | 2026-09-12 17:15:16 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 288.1 | 2026-09-12 17:15:23 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 288.1 | 2026-09-12 17:15:23 | EV | arm | ARMED(10) |
| 288.1 | 2026-09-12 17:15:23 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 288.1 | 2026-09-12 17:15:23 | EV | ev | AUTO_ARMED(15) |
| 290.1 | 2026-09-12 17:15:25 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 293.8 | 2026-09-12 17:15:28 | EV | ev | NOT_LANDED(28) |
| 294.7 | 2026-09-12 17:15:29 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 294.7 | 2026-09-12 17:15:29 | EV | arm | DISARMED(11) |
| 294.7 | 2026-09-12 17:15:29 | EV | ev | LAND_COMPLETE(18) |
| 294.7 | 2026-09-12 17:15:29 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 294.7 | 2026-09-12 17:15:29 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 316 | 2026-09-12 17:15:51 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 316 | 2026-09-12 17:15:51 | EV | arm | ARMED(10) |
| 316 | 2026-09-12 17:15:51 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 317.1 | 2026-09-12 17:15:52 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 317.1 | 2026-09-12 17:15:52 | EV | arm | DISARMED(11) |
| 322.3 | 2026-09-12 17:15:57 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 322.3 | 2026-09-12 17:15:57 | EV | arm | ARMED(10) |
| 322.3 | 2026-09-12 17:15:57 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 324.3 | 2026-09-12 17:15:59 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 325.9 | 2026-09-12 17:16:00 | EV | ev | AUTO_ARMED(15) |
| 329 | 2026-09-12 17:16:04 | EV | ev | NOT_LANDED(28) |
| 329 | 2026-09-12 17:16:04 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 329 | 2026-09-12 17:16:04 | EV | arm | DISARMED(11) |
| 329 | 2026-09-12 17:16:04 | EV | ev | LAND_COMPLETE(18) |
| 329 | 2026-09-12 17:16:04 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 329 | 2026-09-12 17:16:04 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 330.2 | 2026-09-12 17:16:05 | MSG | prearm | PreArm: Accels inconsistent |
| 342.1 | 2026-09-12 17:16:17 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 342.1 | 2026-09-12 17:16:17 | EV | arm | ARMED(10) |
| 342.1 | 2026-09-12 17:16:17 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 343.9 | 2026-09-12 17:16:19 | EV | ev | NOT_LANDED(28) |
| 344.1 | 2026-09-12 17:16:19 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 345.2 | 2026-09-12 17:16:20 | EV | ev | AUTO_ARMED(15) |
| 345.5 | 2026-09-12 17:16:20 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 348.3 | 2026-09-12 17:16:23 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 348.3 | 2026-09-12 17:16:23 | EV | arm | DISARMED(11) |
| 348.3 | 2026-09-12 17:16:23 | EV | ev | LAND_COMPLETE(18) |
| 348.3 | 2026-09-12 17:16:23 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 348.3 | 2026-09-12 17:16:23 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #5 · BOOT 79 · `2026-09-12 17-31-18.bin` · 2026-09-12 17:31:18 · 54.9 s · 3S/11.17 V · beyan A · uçuş 0/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | ChibiOS: 6a85082c |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | Param space used: 875/5376 |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | RC Protocol: IBUS |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | RCOut: PWM:1-16 |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | New mission |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | New rally |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | New fence |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | Frame: QUAD/X |
| 37.7 | 2026-09-12 17:31:18 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 37.7 | 2026-09-12 17:31:18 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 37.7 | 2026-09-12 17:31:18 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 39.8 | 2026-09-12 17:31:20 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 39.8 | 2026-09-12 17:31:20 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 43.3 | 2026-09-12 17:31:24 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 43.3 | 2026-09-12 17:31:24 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 44.6 | 2026-09-12 17:31:25 | MSG | ekf | EKF3 IMU1 is using GPS |
| 45 | 2026-09-12 17:31:25 | MSG | ekf | EKF3 IMU0 is using GPS |
| 47.6 | 2026-09-12 17:31:28 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 47.6 | 2026-09-12 17:31:28 | EV | arm | ARMED(10) |
| 47.6 | 2026-09-12 17:31:28 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 49.6 | 2026-09-12 17:31:30 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 52.6 | 2026-09-12 17:31:33 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 52.6 | 2026-09-12 17:31:33 | EV | arm | DISARMED(11) |
| 52.6 | 2026-09-12 17:31:33 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 58.8 | 2026-09-12 17:31:39 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 58.8 | 2026-09-12 17:31:39 | EV | arm | ARMED(10) |
| 58.8 | 2026-09-12 17:31:39 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 60.8 | 2026-09-12 17:31:41 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 61.7 | 2026-09-12 17:31:42 | EV | ev | AUTO_ARMED(15) |
| 63.8 | 2026-09-12 17:31:44 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 63.8 | 2026-09-12 17:31:44 | EV | arm | DISARMED(11) |
| 63.8 | 2026-09-12 17:31:44 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 64.8 | 2026-09-12 17:31:45 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 64.8 | 2026-09-12 17:31:45 | EV | arm | ARMED(10) |
| 64.8 | 2026-09-12 17:31:45 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 64.8 | 2026-09-12 17:31:45 | EV | ev | AUTO_ARMED(15) |
| 66.8 | 2026-09-12 17:31:47 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 71 | 2026-09-12 17:31:51 | EV | ev | NOT_LANDED(28) |
| 71.1 | 2026-09-12 17:31:51 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 71.1 | 2026-09-12 17:31:51 | EV | arm | DISARMED(11) |
| 71.1 | 2026-09-12 17:31:51 | EV | ev | LAND_COMPLETE(18) |
| 71.1 | 2026-09-12 17:31:51 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 71.1 | 2026-09-12 17:31:51 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #6 · BOOT 80 · `2026-09-12 17-35-39.bin` · 2026-09-12 17:35:39 · 108.2 s · 3S/11.07 V · beyan A · uçuş 0/kısa 2

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | ChibiOS: 6a85082c |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | Param space used: 875/5376 |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | RC Protocol: IBUS |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | RCOut: PWM:1-16 |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | New mission |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | New rally |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | New fence |
| 24.4 | 2026-09-12 17:35:39 | MSG | banner | Frame: QUAD/X |
| 24.4 | 2026-09-12 17:35:39 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 24.4 | 2026-09-12 17:35:39 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 27.3 | 2026-09-12 17:35:42 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 28.9 | 2026-09-12 17:35:43 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 28.9 | 2026-09-12 17:35:43 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 30.2 | 2026-09-12 17:35:45 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-12 17:35:45 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 30.8 | 2026-09-12 17:35:45 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 31.3 | 2026-09-12 17:35:46 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 31.3 | 2026-09-12 17:35:46 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 32.6 | 2026-09-12 17:35:47 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 33.3 | 2026-09-12 17:35:48 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 33.3 | 2026-09-12 17:35:48 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 36.4 | 2026-09-12 17:35:51 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 36.4 | 2026-09-12 17:35:51 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 41.1 | 2026-09-12 17:35:56 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 41.1 | 2026-09-12 17:35:56 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 44.3 | 2026-09-12 17:35:59 | MSG | ekf | EKF3 IMU1 is using GPS |
| 44.7 | 2026-09-12 17:35:59 | MSG | ekf | EKF3 IMU0 is using GPS |
| 49.7 | 2026-09-12 17:36:04 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 49.7 | 2026-09-12 17:36:04 | EV | arm | ARMED(10) |
| 49.7 | 2026-09-12 17:36:04 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 51.7 | 2026-09-12 17:36:06 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 53 | 2026-09-12 17:36:08 | EV | ev | AUTO_ARMED(15) |
| 57.7 | 2026-09-12 17:36:12 | EV | ev | NOT_LANDED(28) |
| 58.6 | 2026-09-12 17:36:13 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 58.6 | 2026-09-12 17:36:13 | EV | arm | DISARMED(11) |
| 58.6 | 2026-09-12 17:36:13 | EV | ev | LAND_COMPLETE(18) |
| 58.6 | 2026-09-12 17:36:13 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 58.6 | 2026-09-12 17:36:13 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 64.3 | 2026-09-12 17:36:19 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 106.3 | 2026-09-12 17:37:01 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 106.3 | 2026-09-12 17:37:01 | EV | arm | ARMED(10) |
| 106.3 | 2026-09-12 17:37:01 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 108.3 | 2026-09-12 17:37:03 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 109.7 | 2026-09-12 17:37:04 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 109.7 | 2026-09-12 17:37:04 | EV | arm | DISARMED(11) |
| 109.7 | 2026-09-12 17:37:04 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 111 | 2026-09-12 17:37:06 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 111 | 2026-09-12 17:37:06 | EV | arm | ARMED(10) |
| 111 | 2026-09-12 17:37:06 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 113 | 2026-09-12 17:37:08 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 115.3 | 2026-09-12 17:37:10 | EV | ev | AUTO_ARMED(15) |
| 115.5 | 2026-09-12 17:37:10 | EV | ev | NOT_LANDED(28) |
| 116.1 | 2026-09-12 17:37:11 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 117.3 | 2026-09-12 17:37:12 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 117.6 | 2026-09-12 17:37:12 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 117.6 | 2026-09-12 17:37:12 | EV | arm | DISARMED(11) |
| 117.6 | 2026-09-12 17:37:12 | EV | ev | LAND_COMPLETE(18) |
| 117.6 | 2026-09-12 17:37:12 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #7 · BOOT 81 · `2026-09-12 17-42-38.bin` · 2026-09-12 17:42:37 · 51.6 s · 3S/11.05 V · beyan A · uçuş 0/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | ChibiOS: 6a85082c |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | Param space used: 875/5376 |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | RC Protocol: IBUS |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | RCOut: PWM:1-16 |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | New mission |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | New rally |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | New fence |
| 19.3 | 2026-09-12 17:42:37 | MSG | banner | Frame: QUAD/X |
| 19.3 | 2026-09-12 17:42:37 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 19.3 | 2026-09-12 17:42:37 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 20.1 | 2026-09-12 17:42:38 | MSG | arm_ret | Arm: Gyros inconsistent |
| 20.1 | 2026-09-12 17:42:38 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 20.1 | 2026-09-12 17:42:38 | MSG | arm_ret | Arm: Fence requires position |
| 21.5 | 2026-09-12 17:42:40 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 22.3 | 2026-09-12 17:42:40 | MSG | arm_ret | Arm: Gyros inconsistent |
| 22.3 | 2026-09-12 17:42:40 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 22.3 | 2026-09-12 17:42:40 | MSG | arm_ret | Arm: Fence requires position |
| 22.9 | 2026-09-12 17:42:41 | MSG | ekf | EKF3 IMU0 origin set |
| 22.9 | 2026-09-12 17:42:41 | EV | ev | SET_HOME(25) |
| 22.9 | 2026-09-12 17:42:41 | MSG | ekf | EKF3 IMU1 origin set |
| 22.9 | 2026-09-12 17:42:41 | MSG | diger | Field Elevation Set: 94m |
| 23.8 | 2026-09-12 17:42:42 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 24.4 | 2026-09-12 17:42:43 | MSG | arm_ret | Arm: Gyros inconsistent |
| 24.4 | 2026-09-12 17:42:43 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 24.4 | 2026-09-12 17:42:43 | MSG | gps | GPS 1: u-blox solution rate configuration 0x388 |
| 27.3 | 2026-09-12 17:42:45 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.2 | 2026-09-12 17:42:48 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-12 17:42:48 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 32.9 | 2026-09-12 17:42:51 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 32.9 | 2026-09-12 17:42:51 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 34.3 | 2026-09-12 17:42:52 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 34.3 | 2026-09-12 17:42:52 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 44 | 2026-09-12 17:43:02 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 44 | 2026-09-12 17:43:02 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 44.3 | 2026-09-12 17:43:02 | MSG | ekf | EKF3 IMU1 is using GPS |
| 44.7 | 2026-09-12 17:43:03 | MSG | ekf | EKF3 IMU0 is using GPS |
| 48.7 | 2026-09-12 17:43:07 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 48.7 | 2026-09-12 17:43:07 | EV | arm | ARMED(10) |
| 48.7 | 2026-09-12 17:43:07 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 50.7 | 2026-09-12 17:43:09 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 53.3 | 2026-09-12 17:43:11 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 55.1 | 2026-09-12 17:43:13 | EV | ev | AUTO_ARMED(15) |
| 60.5 | 2026-09-12 17:43:19 | EV | ev | NOT_LANDED(28) |
| 65.4 | 2026-09-12 17:43:24 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 65.4 | 2026-09-12 17:43:24 | EV | arm | DISARMED(11) |
| 65.4 | 2026-09-12 17:43:24 | EV | ev | LAND_COMPLETE(18) |
| 65.4 | 2026-09-12 17:43:24 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 65.4 | 2026-09-12 17:43:24 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #8 · BOOT 82 · `2026-09-12 17-47-06.bin` · 2026-09-12 17:47:06 · 34.5 s · 3S/10.96 V · beyan A · uçuş 0/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | ChibiOS: 6a85082c |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | Param space used: 875/5376 |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | RC Protocol: IBUS |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | RCOut: PWM:1-16 |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | New mission |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | New rally |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | New fence |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | Frame: QUAD/X |
| 69.8 | 2026-09-12 17:47:06 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 69.8 | 2026-09-12 17:47:06 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 69.8 | 2026-09-12 17:47:06 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 71.7 | 2026-09-12 17:47:08 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 74.9 | 2026-09-12 17:47:11 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 75.5 | 2026-09-12 17:47:12 | EV | ev | AUTO_ARMED(15) |
| 84.6 | 2026-09-12 17:47:21 | EV | ev | NOT_LANDED(28) |
| 86.1 | 2026-09-12 17:47:22 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 89.2 | 2026-09-12 17:47:25 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 89.2 | 2026-09-12 17:47:25 | EV | arm | DISARMED(11) |
| 89.2 | 2026-09-12 17:47:25 | EV | ev | LAND_COMPLETE(18) |
| 89.2 | 2026-09-12 17:47:25 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 89.2 | 2026-09-12 17:47:25 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #9 · BOOT 88 · `2026-09-12 18-48-07.bin` · 2026-09-12 18:38:39 · 791.4 s · 4S/16.3 V · beyan B · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | ChibiOS: 6a85082c |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | Param space used: 875/5376 |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | RC Protocol: None |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | RCOut: PWM:1-16 |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | New mission |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | New rally |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | New fence |
| 22.9 | 2026-09-12 18:38:39 | MSG | banner | Frame: QUAD/X |
| 22.9 | 2026-09-12 18:38:39 | MODE | kip | → STABILIZE (0), neden INITIALISED(26) |
| 22.9 | 2026-09-12 18:38:39 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 23.1 | 2026-09-12 18:38:40 | MSG | motor_test | starting motor test |
| 23.1 | 2026-09-12 18:38:40 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 23.2 | 2026-09-12 18:38:40 | MSG | motor_test | starting motor test |
| 23.2 | 2026-09-12 18:38:40 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 23.5 | 2026-09-12 18:38:40 | MSG | motor_test | starting motor test |
| 23.5 | 2026-09-12 18:38:40 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 27.3 | 2026-09-12 18:38:44 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.2 | 2026-09-12 18:38:47 | MSG | prearm | PreArm: RC not found |
| 30.2 | 2026-09-12 18:38:47 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 30.2 | 2026-09-12 18:38:47 | MSG | prearm | PreArm: Fence requires position |
| 590.8 | 2026-09-12 18:48:07 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 591.2 | 2026-09-12 18:48:08 | MSG | motor_test | starting motor test |
| 591.2 | 2026-09-12 18:48:08 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 591.7 | 2026-09-12 18:48:08 | MSG | motor_test | starting motor test |
| 591.7 | 2026-09-12 18:48:08 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 592.2 | 2026-09-12 18:48:09 | MSG | motor_test | starting motor test |
| 592.2 | 2026-09-12 18:48:09 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 592.4 | 2026-09-12 18:48:09 | MSG | motor_test | starting motor test |
| 630 | 2026-09-12 18:48:46 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 630.2 | 2026-09-12 18:48:47 | MSG | motor_test | starting motor test |
| 630.2 | 2026-09-12 18:48:47 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 630.5 | 2026-09-12 18:48:47 | MSG | motor_test | starting motor test |
| 630.5 | 2026-09-12 18:48:47 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 630.9 | 2026-09-12 18:48:47 | MSG | motor_test | starting motor test |
| 630.9 | 2026-09-12 18:48:47 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 766.1 | 2026-09-12 18:51:03 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 766.4 | 2026-09-12 18:51:03 | MSG | motor_test | starting motor test |
| 766.4 | 2026-09-12 18:51:03 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 766.7 | 2026-09-12 18:51:03 | MSG | motor_test | starting motor test |
| 766.7 | 2026-09-12 18:51:03 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 766.9 | 2026-09-12 18:51:03 | MSG | motor_test | starting motor test |
| 766.9 | 2026-09-12 18:51:03 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 771.3 | 2026-09-12 18:51:08 | MSG | motor_test | starting motor test |
| 791.8 | 2026-09-12 18:51:28 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 792.3 | 2026-09-12 18:51:29 | MSG | motor_test | starting motor test |
| 792.3 | 2026-09-12 18:51:29 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 792.7 | 2026-09-12 18:51:29 | MSG | motor_test | starting motor test |
| 792.7 | 2026-09-12 18:51:29 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 793.2 | 2026-09-12 18:51:30 | MSG | motor_test | starting motor test |
| 793.2 | 2026-09-12 18:51:30 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 793.9 | 2026-09-12 18:51:30 | MSG | motor_test | starting motor test |
| 796.9 | 2026-09-12 18:51:33 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 797.3 | 2026-09-12 18:51:34 | MSG | motor_test | starting motor test |
| 797.3 | 2026-09-12 18:51:34 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 797.7 | 2026-09-12 18:51:34 | MSG | motor_test | starting motor test |
| 797.7 | 2026-09-12 18:51:34 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 798 | 2026-09-12 18:51:34 | MSG | motor_test | starting motor test |
| 798 | 2026-09-12 18:51:34 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 798.5 | 2026-09-12 18:51:35 | MSG | motor_test | starting motor test |
| 799.9 | 2026-09-12 18:51:36 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 800.2 | 2026-09-12 18:51:37 | MSG | motor_test | starting motor test |
| 800.2 | 2026-09-12 18:51:37 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 800.8 | 2026-09-12 18:51:37 | MSG | motor_test | starting motor test |
| 800.8 | 2026-09-12 18:51:37 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 801.2 | 2026-09-12 18:51:38 | MSG | motor_test | starting motor test |
| 801.2 | 2026-09-12 18:51:38 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 801.4 | 2026-09-12 18:51:38 | MSG | motor_test | starting motor test |
| 804.4 | 2026-09-12 18:51:41 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 804.9 | 2026-09-12 18:51:41 | MSG | motor_test | starting motor test |
| 804.9 | 2026-09-12 18:51:41 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 805.3 | 2026-09-12 18:51:42 | MSG | motor_test | starting motor test |
| 805.3 | 2026-09-12 18:51:42 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 805.7 | 2026-09-12 18:51:42 | MSG | motor_test | starting motor test |
| 805.7 | 2026-09-12 18:51:42 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #10 · BOOT 89 · `2026-09-12 18-59-08.bin` · 2026-09-12 18:59:07 · 55.9 s · 3S/10.92 V · beyan A · uçuş 0/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | ChibiOS: 6a85082c |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | Param space used: 875/5376 |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | RC Protocol: IBUS |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | RCOut: PWM:1-16 |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | New mission |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | New rally |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | New fence |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | Frame: QUAD/X |
| 36.4 | 2026-09-12 18:59:08 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 36.4 | 2026-09-12 18:59:08 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 36.4 | 2026-09-12 18:59:08 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 37.4 | 2026-09-12 18:59:09 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 37.4 | 2026-09-12 18:59:09 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 38.4 | 2026-09-12 18:59:10 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 38.4 | 2026-09-12 18:59:10 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 39.3 | 2026-09-12 18:59:11 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 39.3 | 2026-09-12 18:59:11 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 44.3 | 2026-09-12 18:59:16 | MSG | ekf | EKF3 IMU1 is using GPS |
| 44.7 | 2026-09-12 18:59:16 | MSG | ekf | EKF3 IMU0 is using GPS |
| 47.3 | 2026-09-12 18:59:19 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 47.3 | 2026-09-12 18:59:19 | EV | arm | ARMED(10) |
| 47.3 | 2026-09-12 18:59:19 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 49.3 | 2026-09-12 18:59:21 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 53.8 | 2026-09-12 18:59:25 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 55.4 | 2026-09-12 18:59:27 | EV | ev | AUTO_ARMED(15) |
| 58.3 | 2026-09-12 18:59:29 | EV | ev | NOT_LANDED(28) |
| 61 | 2026-09-12 18:59:32 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 61 | 2026-09-12 18:59:32 | EV | arm | DISARMED(11) |
| 61 | 2026-09-12 18:59:32 | EV | ev | LAND_COMPLETE(18) |
| 61 | 2026-09-12 18:59:32 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 61 | 2026-09-12 18:59:32 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 90.5 | 2026-09-12 19:00:02 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |

### #11 · BOOT 90 · `2026-09-12 19-13-58.bin` · 2026-09-12 19:13:58 · 316.3 s · 3S/10.76 V · beyan A · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | ChibiOS: 6a85082c |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | Param space used: 875/5376 |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | RC Protocol: None |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | RCOut: PWM:1-16 |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | New mission |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | New rally |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | New fence |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | Frame: QUAD/X |
| 220.8 | 2026-09-12 19:13:58 | MODE | kip | → STABILIZE (0), neden INITIALISED(26) |
| 220.8 | 2026-09-12 19:13:58 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 220.8 | 2026-09-12 19:13:58 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 396.8 | 2026-09-12 19:16:54 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 399.2 | 2026-09-12 19:16:56 | MSG | prearm | PreArm: RC not found |
| 486.6 | 2026-09-12 19:18:24 | MSG | arm_ret | Arm: Check mag field (xy diff:223>100) |
| 486.6 | 2026-09-12 19:18:24 | MSG | arm_ret | Arm: GPS glitching |
| 488.2 | 2026-09-12 19:18:25 | MSG | arm_ret | Arm: Check mag field (xy diff:223>100) |
| 488.2 | 2026-09-12 19:18:25 | MSG | arm_ret | Arm: GPS glitching |
| 492.9 | 2026-09-12 19:18:30 | MSG | arm_ret | Arm: Check mag field (xy diff:224>100) |
| 492.9 | 2026-09-12 19:18:30 | MSG | arm_ret | Arm: GPS glitching |
| 502.2 | 2026-09-12 19:18:39 | MSG | prearm | PreArm: Check mag field (xy diff:225>100) |
| 502.2 | 2026-09-12 19:18:39 | MSG | prearm | PreArm: GPS glitching |
| 520.6 | 2026-09-12 19:18:58 | MSG | arm_ret | Arm: Check mag field (xy diff:249>100) |
| 522.2 | 2026-09-12 19:18:59 | MSG | arm_ret | Arm: Check mag field (xy diff:249>100) |
| 523.4 | 2026-09-12 19:19:00 | MSG | arm_ret | Arm: Check mag field (xy diff:250>100) |
| 524.3 | 2026-09-12 19:19:01 | MSG | arm_ret | Arm: Check mag field (xy diff:247>100) |
| 525 | 2026-09-12 19:19:02 | MSG | arm_ret | Arm: Check mag field (xy diff:245>100) |
| 532.2 | 2026-09-12 19:19:09 | MSG | prearm | PreArm: Check mag field (xy diff:152>100) |
| 532.2 | 2026-09-12 19:19:09 | MSG | prearm | PreArm: EKF velocity variance |
| 532.6 | 2026-09-12 19:19:10 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 532.6 | 2026-09-12 19:19:10 | MSG | gps | GPS Glitch or Compass error |

### #12 · BOOT 91 · `2026-09-12 19-41-52.bin` · 2026-09-12 19:41:52 · 437.4 s · 3S/11.08 V · beyan A · uçuş 0/kısa 3

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | ChibiOS: 6a85082c |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | Param space used: 875/5376 |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | RC Protocol: IBUS |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | RCOut: PWM:1-16 |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | New mission |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | New rally |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | New fence |
| 37.2 | 2026-09-12 19:41:52 | MSG | banner | Frame: QUAD/X |
| 37.2 | 2026-09-12 19:41:52 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 37.2 | 2026-09-12 19:41:52 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 38.5 | 2026-09-12 19:41:53 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 38.5 | 2026-09-12 19:41:53 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 39.2 | 2026-09-12 19:41:54 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 39.9 | 2026-09-12 19:41:55 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 39.9 | 2026-09-12 19:41:55 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 61.3 | 2026-09-12 19:42:16 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 63.2 | 2026-09-12 19:42:18 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 63.3 | 2026-09-12 19:42:18 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 65.2 | 2026-09-12 19:42:20 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 65.2 | 2026-09-12 19:42:20 | EV | arm | DISARMED(11) |
| 65.2 | 2026-09-12 19:42:20 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 96.2 | 2026-09-12 19:42:51 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 96.2 | 2026-09-12 19:42:51 | EV | arm | ARMED(10) |
| 96.2 | 2026-09-12 19:42:51 | MSG | diger | Terrain: clamping offset 35 to 30 |
| 96.2 | 2026-09-12 19:42:51 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 98.2 | 2026-09-12 19:42:53 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 101.6 | 2026-09-12 19:42:56 | EV | ev | AUTO_ARMED(15) |
| 103.5 | 2026-09-12 19:42:58 | EV | ev | NOT_LANDED(28) |
| 103.9 | 2026-09-12 19:42:59 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 103.9 | 2026-09-12 19:42:59 | EV | arm | DISARMED(11) |
| 103.9 | 2026-09-12 19:42:59 | EV | ev | LAND_COMPLETE(18) |
| 103.9 | 2026-09-12 19:42:59 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 103.9 | 2026-09-12 19:42:59 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 106.3 | 2026-09-12 19:43:01 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 106.3 | 2026-09-12 19:43:01 | EV | arm | ARMED(10) |
| 106.3 | 2026-09-12 19:43:01 | MSG | diger | Terrain: clamping offset 35 to 30 |
| 106.3 | 2026-09-12 19:43:01 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 108.3 | 2026-09-12 19:43:03 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 114 | 2026-09-12 19:43:09 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 114 | 2026-09-12 19:43:09 | EV | arm | DISARMED(11) |
| 114 | 2026-09-12 19:43:09 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 126.6 | 2026-09-12 19:43:21 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 126.6 | 2026-09-12 19:43:21 | MSG | gps | GPS Glitch or Compass error |
| 128.1 | 2026-09-12 19:43:23 | MSG | prearm | PreArm: GPS glitching |
| 159.1 | 2026-09-12 19:43:54 | MSG | prearm | PreArm: GPS glitching |
| 173 | 2026-09-12 19:44:08 | MSG | arm_ret | Arm: GPS glitching |
| 174 | 2026-09-12 19:44:09 | ERR | gps | GPS(11) / temizlendi(0) |
| 174 | 2026-09-12 19:44:09 | MSG | gps | Glitch cleared |
| 178.7 | 2026-09-12 19:44:13 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 178.7 | 2026-09-12 19:44:13 | EV | arm | ARMED(10) |
| 178.7 | 2026-09-12 19:44:13 | MSG | diger | Terrain: clamping offset 35 to 30 |
| 178.7 | 2026-09-12 19:44:13 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 180.7 | 2026-09-12 19:44:15 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 182.7 | 2026-09-12 19:44:17 | EV | ev | AUTO_ARMED(15) |
| 187.4 | 2026-09-12 19:44:22 | EV | ev | NOT_LANDED(28) |
| 187.9 | 2026-09-12 19:44:23 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 187.9 | 2026-09-12 19:44:23 | EV | arm | DISARMED(11) |
| 187.9 | 2026-09-12 19:44:23 | EV | ev | LAND_COMPLETE(18) |
| 187.9 | 2026-09-12 19:44:23 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 187.9 | 2026-09-12 19:44:23 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 189.1 | 2026-09-12 19:44:24 | MSG | prearm | PreArm: Accels inconsistent |
| 199.2 | 2026-09-12 19:44:34 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 199.2 | 2026-09-12 19:44:34 | MSG | gps | GPS Glitch or Compass error |
| 201.1 | 2026-09-12 19:44:36 | MSG | prearm | PreArm: GPS glitching |
| 232.1 | 2026-09-12 19:45:07 | MSG | prearm | PreArm: GPS glitching |
| 262.1 | 2026-09-12 19:45:37 | MSG | prearm | PreArm: GPS glitching |
| 268.1 | 2026-09-12 19:45:43 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 268.1 | 2026-09-12 19:45:43 | MSG | ekf | EKF variance |
| 268.1 | 2026-09-12 19:45:43 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 269.8 | 2026-09-12 19:45:44 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 269.8 | 2026-09-12 19:45:44 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 272.9 | 2026-09-12 19:45:48 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 272.9 | 2026-09-12 19:45:48 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 274.7 | 2026-09-12 19:45:49 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 274.7 | 2026-09-12 19:45:49 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 293.1 | 2026-09-12 19:46:08 | MSG | prearm | PreArm: GPS glitching |
| 304.8 | 2026-09-12 19:46:19 | MSG | arm_ret | Arm: GPS glitching |
| 306.8 | 2026-09-12 19:46:21 | MSG | arm_ret | Arm: GPS glitching |
| 307.5 | 2026-09-12 19:46:22 | MSG | arm_ret | Arm: GPS glitching |
| 312.7 | 2026-09-12 19:46:27 | MSG | arm_ret | Arm: GPS glitching |
| 314.7 | 2026-09-12 19:46:29 | MSG | arm_ret | Arm: Check mag field (xy diff:125>100) |
| 314.7 | 2026-09-12 19:46:29 | MSG | arm_ret | Arm: GPS glitching |
| 316.1 | 2026-09-12 19:46:31 | MSG | arm_ret | Arm: GPS glitching |
| 319.7 | 2026-09-12 19:46:34 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 319.7 | 2026-09-12 19:46:34 | MSG | ekf | EKF variance |
| 319.7 | 2026-09-12 19:46:34 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 320.5 | 2026-09-12 19:46:35 | MSG | arm_ret | Arm: Need Position Estimate |
| 322.9 | 2026-09-12 19:46:38 | MSG | arm_ret | Arm: Need Position Estimate |
| 323.1 | 2026-09-12 19:46:38 | MSG | prearm | PreArm: Need Position Estimate |
| 323.3 | 2026-09-12 19:46:38 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 323.3 | 2026-09-12 19:46:38 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 324 | 2026-09-12 19:46:39 | MSG | arm_ret | Arm: GPS glitching |
| 327.2 | 2026-09-12 19:46:42 | MSG | arm_ret | Arm: GPS glitching |
| 328.2 | 2026-09-12 19:46:43 | MSG | arm_ret | Arm: GPS glitching |
| 334 | 2026-09-12 19:46:49 | ERR | gps | GPS(11) / temizlendi(0) |
| 334 | 2026-09-12 19:46:49 | MSG | gps | Glitch cleared |
| 336.4 | 2026-09-12 19:46:51 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 336.4 | 2026-09-12 19:46:51 | EV | arm | ARMED(10) |
| 336.4 | 2026-09-12 19:46:51 | MSG | diger | Terrain: clamping offset 36 to 30 |
| 336.4 | 2026-09-12 19:46:51 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 338.3 | 2026-09-12 19:46:53 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 338.3 | 2026-09-12 19:46:53 | EV | arm | DISARMED(11) |
| 338.6 | 2026-09-12 19:46:53 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 338.6 | 2026-09-12 19:46:53 | EV | arm | ARMED(10) |
| 338.6 | 2026-09-12 19:46:53 | MSG | diger | Terrain: clamping offset 36 to 30 |
| 338.6 | 2026-09-12 19:46:53 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 340.6 | 2026-09-12 19:46:55 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 342.6 | 2026-09-12 19:46:57 | EV | ev | AUTO_ARMED(15) |
| 362.2 | 2026-09-12 19:47:17 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 362.2 | 2026-09-12 19:47:17 | EV | arm | DISARMED(11) |
| 362.2 | 2026-09-12 19:47:17 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 415.2 | 2026-09-12 19:48:10 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 415.2 | 2026-09-12 19:48:10 | EV | arm | ARMED(10) |
| 415.2 | 2026-09-12 19:48:10 | MSG | diger | Terrain: clamping offset 37 to 30 |
| 415.2 | 2026-09-12 19:48:10 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 417.2 | 2026-09-12 19:48:12 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 425.1 | 2026-09-12 19:48:20 | ARM | arm | DISARM yöntem DISARMDELAY(17) forced=0 checks=0 |
| 425.1 | 2026-09-12 19:48:20 | EV | arm | DISARMED(11) |
| 425.1 | 2026-09-12 19:48:20 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 427.3 | 2026-09-12 19:48:22 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 427.3 | 2026-09-12 19:48:22 | EV | arm | ARMED(10) |
| 427.3 | 2026-09-12 19:48:22 | MSG | diger | Terrain: clamping offset 36 to 30 |
| 427.3 | 2026-09-12 19:48:22 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 429.3 | 2026-09-12 19:48:24 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 437.1 | 2026-09-12 19:48:32 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 437.1 | 2026-09-12 19:48:32 | EV | arm | DISARMED(11) |
| 437.1 | 2026-09-12 19:48:32 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 438.9 | 2026-09-12 19:48:34 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 438.9 | 2026-09-12 19:48:34 | EV | arm | ARMED(10) |
| 438.9 | 2026-09-12 19:48:34 | MSG | diger | Terrain: clamping offset 37 to 30 |
| 438.9 | 2026-09-12 19:48:34 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 440.9 | 2026-09-12 19:48:36 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 444.6 | 2026-09-12 19:48:39 | EV | ev | AUTO_ARMED(15) |
| 459.4 | 2026-09-12 19:48:54 | EV | ev | NOT_LANDED(28) |
| 459.8 | 2026-09-12 19:48:54 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 459.8 | 2026-09-12 19:48:54 | EV | arm | DISARMED(11) |
| 459.8 | 2026-09-12 19:48:54 | EV | ev | LAND_COMPLETE(18) |
| 459.8 | 2026-09-12 19:48:54 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 459.8 | 2026-09-12 19:48:55 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 471.4 | 2026-09-12 19:49:06 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 471.4 | 2026-09-12 19:49:06 | MSG | gps | GPS Glitch or Compass error |
| 473.1 | 2026-09-12 19:49:08 | MSG | prearm | PreArm: Check mag field (xy diff:138>100) |
| 473.1 | 2026-09-12 19:49:08 | MSG | prearm | PreArm: GPS glitching |

### #13 · BOOT 94 · `2026-09-12 20-51-26.bin` · 2026-09-12 20:51:26 · 1565.0 s · 3S/12 V · beyan A · uçuş 2/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | ChibiOS: 6a85082c |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | Param space used: 875/5376 |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | RC Protocol: IBUS |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | RCOut: PWM:1-16 |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | New mission |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | New rally |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | New fence |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | Frame: QUAD/X |
| 182.2 | 2026-09-12 20:51:26 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 182.2 | 2026-09-12 20:51:26 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 182.2 | 2026-09-12 20:51:26 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 190.6 | 2026-09-12 20:51:35 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 190.6 | 2026-09-12 20:51:35 | EV | arm | ARMED(10) |
| 190.6 | 2026-09-12 20:51:35 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 192.6 | 2026-09-12 20:51:37 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 194.8 | 2026-09-12 20:51:39 | EV | ev | AUTO_ARMED(15) |
| 195 | 2026-09-12 20:51:39 | EV | ev | NOT_LANDED(28) |
| 195.5 | 2026-09-12 20:51:39 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 196.3 | 2026-09-12 20:51:40 | EV | ev | LAND_COMPLETE(18) |
| 196.5 | 2026-09-12 20:51:40 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 196.6 | 2026-09-12 20:51:41 | EV | ev | AUTO_ARMED(15) |
| 198.8 | 2026-09-12 20:51:43 | EV | ev | NOT_LANDED(28) |
| 208.6 | 2026-09-12 20:51:53 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 212.1 | 2026-09-12 20:51:56 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 212.9 | 2026-09-12 20:51:57 | EV | ev | LAND_COMPLETE(18) |
| 213.4 | 2026-09-12 20:51:57 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 213.4 | 2026-09-12 20:51:57 | EV | arm | DISARMED(11) |
| 213.4 | 2026-09-12 20:51:57 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 292 | 2026-09-12 20:53:16 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 292 | 2026-09-12 20:53:16 | MSG | failsafe | GCS Failsafe |
| 308.7 | 2026-09-12 20:53:33 | MSG | prearm | PreArm: GCS failsafe on |
| 339.7 | 2026-09-12 20:54:04 | MSG | prearm | PreArm: GCS failsafe on |
| 370.7 | 2026-09-12 20:54:35 | MSG | prearm | PreArm: GCS failsafe on |
| 401.7 | 2026-09-12 20:55:06 | MSG | prearm | PreArm: GCS failsafe on |
| 432.7 | 2026-09-12 20:55:37 | MSG | prearm | PreArm: GCS failsafe on |
| 463.7 | 2026-09-12 20:56:08 | MSG | prearm | PreArm: GCS failsafe on |
| 494.7 | 2026-09-12 20:56:39 | MSG | prearm | PreArm: GCS failsafe on |
| 525.7 | 2026-09-12 20:57:10 | MSG | prearm | PreArm: GCS failsafe on |
| 556.7 | 2026-09-12 20:57:41 | MSG | prearm | PreArm: GCS failsafe on |
| 587.7 | 2026-09-12 20:58:12 | MSG | prearm | PreArm: GCS failsafe on |
| 618.7 | 2026-09-12 20:58:43 | MSG | prearm | PreArm: GCS failsafe on |
| 649.7 | 2026-09-12 20:59:14 | MSG | prearm | PreArm: GCS failsafe on |
| 680.7 | 2026-09-12 20:59:45 | MSG | prearm | PreArm: GCS failsafe on |
| 711.7 | 2026-09-12 21:00:16 | MSG | prearm | PreArm: GCS failsafe on |
| 742.7 | 2026-09-12 21:00:47 | MSG | prearm | PreArm: GCS failsafe on |
| 773.7 | 2026-09-12 21:01:18 | MSG | prearm | PreArm: GCS failsafe on |
| 804.7 | 2026-09-12 21:01:49 | MSG | prearm | PreArm: GCS failsafe on |
| 835.7 | 2026-09-12 21:02:20 | MSG | prearm | PreArm: GCS failsafe on |
| 866.7 | 2026-09-12 21:02:51 | MSG | prearm | PreArm: GCS failsafe on |
| 897.7 | 2026-09-12 21:03:22 | MSG | prearm | PreArm: GCS failsafe on |
| 928.7 | 2026-09-12 21:03:53 | MSG | prearm | PreArm: GCS failsafe on |
| 959.7 | 2026-09-12 21:04:24 | MSG | prearm | PreArm: GCS failsafe on |
| 990.7 | 2026-09-12 21:04:55 | MSG | prearm | PreArm: GCS failsafe on |
| 1021.7 | 2026-09-12 21:05:26 | MSG | prearm | PreArm: GCS failsafe on |
| 1052.7 | 2026-09-12 21:05:57 | MSG | prearm | PreArm: GCS failsafe on |
| 1083.7 | 2026-09-12 21:06:28 | MSG | prearm | PreArm: GCS failsafe on |
| 1114.7 | 2026-09-12 21:06:59 | MSG | prearm | PreArm: GCS failsafe on |
| 1145.7 | 2026-09-12 21:07:30 | MSG | prearm | PreArm: GCS failsafe on |
| 1176.7 | 2026-09-12 21:08:01 | MSG | prearm | PreArm: GCS failsafe on |
| 1199.4 | 2026-09-12 21:08:23 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1207.7 | 2026-09-12 21:08:32 | MSG | prearm | PreArm: GCS failsafe on |
| 1238.7 | 2026-09-12 21:09:03 | MSG | prearm | PreArm: GCS failsafe on |
| 1267.6 | 2026-09-12 21:09:32 | MSG | arm_ret | Arm: GCS failsafe on |
| 1269.3 | 2026-09-12 21:09:33 | MSG | arm_ret | Arm: GCS failsafe on |
| 1269.7 | 2026-09-12 21:09:34 | MSG | prearm | PreArm: GCS failsafe on |
| 1270.8 | 2026-09-12 21:09:35 | MSG | arm_ret | Arm: GCS failsafe on |
| 1272.3 | 2026-09-12 21:09:36 | MSG | arm_ret | Arm: GCS failsafe on |
| 1276.4 | 2026-09-12 21:09:40 | MSG | arm_ret | Arm: GCS failsafe on |
| 1285.9 | 2026-09-12 21:09:50 | MSG | failsafe | GCS Failsafe Cleared |
| 1285.9 | 2026-09-12 21:09:50 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 1287 | 2026-09-12 21:09:51 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 1287 | 2026-09-12 21:09:51 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 1287 | 2026-09-12 21:09:51 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | ChibiOS: 6a85082c |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | RCOut: PWM:1-16 |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 1288.7 | 2026-09-12 21:09:53 | MSG | banner | Frame: QUAD/X |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | ChibiOS: 6a85082c |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | RCOut: PWM:1-16 |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 1289.1 | 2026-09-12 21:09:53 | MSG | banner | Frame: QUAD/X |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | ChibiOS: 6a85082c |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | RCOut: PWM:1-16 |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 1289.8 | 2026-09-12 21:09:54 | MSG | banner | Frame: QUAD/X |
| 1298.1 | 2026-09-12 21:10:02 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 1298.1 | 2026-09-12 21:10:02 | EV | arm | ARMED(10) |
| 1298.1 | 2026-09-12 21:10:02 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1299.1 | 2026-09-12 21:10:03 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 1299.1 | 2026-09-12 21:10:03 | EV | arm | DISARMED(11) |
| 1299.9 | 2026-09-12 21:10:04 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 1299.9 | 2026-09-12 21:10:04 | EV | arm | ARMED(10) |
| 1299.9 | 2026-09-12 21:10:04 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1301.9 | 2026-09-12 21:10:06 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 1305.3 | 2026-09-12 21:10:09 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 1305.7 | 2026-09-12 21:10:10 | EV | ev | AUTO_ARMED(15) |
| 1309.6 | 2026-09-12 21:10:13 | EV | ev | NOT_LANDED(28) |
| 1316.4 | 2026-09-12 21:10:20 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 1319 | 2026-09-12 21:10:23 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 1319.8 | 2026-09-12 21:10:24 | EV | ev | LAND_COMPLETE(18) |
| 1320.3 | 2026-09-12 21:10:24 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 1320.3 | 2026-09-12 21:10:24 | EV | arm | DISARMED(11) |
| 1320.3 | 2026-09-12 21:10:24 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 1333.7 | 2026-09-12 21:10:38 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 1333.7 | 2026-09-12 21:10:38 | MSG | failsafe | GCS Failsafe |
| 1362.7 | 2026-09-12 21:11:07 | MSG | prearm | PreArm: GCS failsafe on |
| 1372.8 | 2026-09-12 21:11:17 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1393.7 | 2026-09-12 21:11:38 | MSG | prearm | PreArm: GCS failsafe on |
| 1424.7 | 2026-09-12 21:12:09 | MSG | prearm | PreArm: GCS failsafe on |
| 1455.7 | 2026-09-12 21:12:40 | MSG | prearm | PreArm: GCS failsafe on |
| 1486.7 | 2026-09-12 21:13:11 | MSG | prearm | PreArm: GCS failsafe on |
| 1517.7 | 2026-09-12 21:13:42 | MSG | prearm | PreArm: GCS failsafe on |
| 1548.7 | 2026-09-12 21:14:13 | MSG | prearm | PreArm: GCS failsafe on |
| 1579.7 | 2026-09-12 21:14:44 | MSG | prearm | PreArm: GCS failsafe on |
| 1595.4 | 2026-09-12 21:14:59 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 1610.7 | 2026-09-12 21:15:15 | MSG | prearm | PreArm: GCS failsafe on |
| 1641.7 | 2026-09-12 21:15:46 | MSG | prearm | PreArm: GCS failsafe on |
| 1672.7 | 2026-09-12 21:16:17 | MSG | prearm | PreArm: GCS failsafe on |
| 1703.7 | 2026-09-12 21:16:48 | MSG | prearm | PreArm: GCS failsafe on |
| 1720.3 | 2026-09-12 21:17:04 | MSG | arm_ret | Arm: GCS failsafe on |
| 1720.5 | 2026-09-12 21:17:04 | MSG | arm_ret | Arm: GCS failsafe on |
| 1729.2 | 2026-09-12 21:17:13 | MSG | arm_ret | Arm: GCS failsafe on |
| 1732.3 | 2026-09-12 21:17:16 | MSG | arm_ret | Arm: GCS failsafe on |
| 1734.7 | 2026-09-12 21:17:19 | MSG | prearm | PreArm: GCS failsafe on |

### #14 · BOOT 95 · `1980-01-12 20-17-44.bin` · 2026-09-12 21:17:38 · 708.0 s · 3S/11.36 V · beyan A · uçuş 2/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | ChibiOS: 6a85082c |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | Param space used: 875/5376 |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | RC Protocol: IBUS |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | RCOut: PWM:1-16 |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | New mission |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | New rally |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | New fence |
| 4.3 | 2026-09-12 21:17:38 | MSG | banner | Frame: QUAD/X |
| 4.3 | 2026-09-12 21:17:38 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 5.2 | 2026-09-12 21:17:39 | MSG | ekf | EKF3 IMU0 initialised |
| 5.2 | 2026-09-12 21:17:39 | MSG | ekf | EKF3 IMU1 initialised |
| 5.2 | 2026-09-12 21:17:39 | MSG | ekf | AHRS: EKF3 active |
| 6.6 | 2026-09-12 21:17:40 | MSG | ekf | EKF3 IMU0 tilt alignment complete |
| 6.6 | 2026-09-12 21:17:40 | MSG | ekf | EKF3 IMU1 tilt alignment complete |
| 6.7 | 2026-09-12 21:17:40 | MSG | ekf | EKF3 IMU0 MAG0 initial yaw alignment complete |
| 6.7 | 2026-09-12 21:17:40 | EV | ekf | EKF_YAW_RESET(62) |
| 6.7 | 2026-09-12 21:17:40 | MSG | ekf | EKF3 IMU1 MAG0 initial yaw alignment complete |
| 10.6 | 2026-09-12 21:17:44 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 15.4 | 2026-09-12 21:17:49 | MSG | arm_ret | Arm: Gyros inconsistent |
| 15.4 | 2026-09-12 21:17:49 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 15.4 | 2026-09-12 21:17:49 | MSG | arm_ret | Arm: Fence requires position |
| 16.7 | 2026-09-12 21:17:50 | MSG | arm_ret | Arm: Gyros inconsistent |
| 16.7 | 2026-09-12 21:17:50 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 16.7 | 2026-09-12 21:17:50 | MSG | arm_ret | Arm: Fence requires position |
| 20.9 | 2026-09-12 21:17:55 | MSG | ekf | EKF3 IMU0 origin set |
| 20.9 | 2026-09-12 21:17:55 | MSG | ekf | EKF3 IMU1 origin set |
| 20.9 | 2026-09-12 21:17:55 | EV | ev | SET_HOME(25) |
| 21 | 2026-09-12 21:17:55 | MSG | diger | Field Elevation Set: 97m |
| 23.9 | 2026-09-12 21:17:58 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 23.9 | 2026-09-12 21:17:58 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 23.9 | 2026-09-12 21:17:58 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 25.3 | 2026-09-12 21:17:59 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | ChibiOS: 6a85082c |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | RCOut: PWM:1-16 |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 25.5 | 2026-09-12 21:17:59 | MSG | banner | Frame: QUAD/X |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | ChibiOS: 6a85082c |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | RCOut: PWM:1-16 |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 25.7 | 2026-09-12 21:17:59 | MSG | banner | Frame: QUAD/X |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | ChibiOS: 6a85082c |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | RCOut: PWM:1-16 |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 26.2 | 2026-09-12 21:18:00 | MSG | banner | Frame: QUAD/X |
| 28.1 | 2026-09-12 21:18:02 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 28.1 | 2026-09-12 21:18:02 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 29.6 | 2026-09-12 21:18:03 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 29.6 | 2026-09-12 21:18:03 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 30.2 | 2026-09-12 21:18:04 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-12 21:18:04 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 35.4 | 2026-09-12 21:18:09 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 35.4 | 2026-09-12 21:18:09 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 36.7 | 2026-09-12 21:18:10 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 36.7 | 2026-09-12 21:18:10 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 40.6 | 2026-09-12 21:18:14 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 40.6 | 2026-09-12 21:18:14 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 42.1 | 2026-09-12 21:18:16 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 42.1 | 2026-09-12 21:18:16 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 42.3 | 2026-09-12 21:18:16 | MSG | ekf | EKF3 IMU0 is using GPS |
| 42.3 | 2026-09-12 21:18:16 | MSG | ekf | EKF3 IMU1 is using GPS |
| 46.6 | 2026-09-12 21:18:20 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 46.6 | 2026-09-12 21:18:20 | EV | arm | ARMED(10) |
| 46.6 | 2026-09-12 21:18:20 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 47.4 | 2026-09-12 21:18:21 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 47.4 | 2026-09-12 21:18:21 | EV | arm | DISARMED(11) |
| 54.1 | 2026-09-12 21:18:28 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 54.1 | 2026-09-12 21:18:28 | MSG | failsafe | GCS Failsafe |
| 60.2 | 2026-09-12 21:18:34 | MSG | prearm | PreArm: GCS failsafe on |
| 61.2 | 2026-09-12 21:18:35 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 61.7 | 2026-09-12 21:18:35 | MSG | arm_ret | Arm: GCS failsafe on |
| 64.2 | 2026-09-12 21:18:38 | MSG | arm_ret | Arm: GCS failsafe on |
| 70.7 | 2026-09-12 21:18:44 | MSG | failsafe | GCS Failsafe Cleared |
| 70.7 | 2026-09-12 21:18:44 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 71.8 | 2026-09-12 21:18:45 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 71.8 | 2026-09-12 21:18:45 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 71.8 | 2026-09-12 21:18:45 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | ChibiOS: 6a85082c |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | RCOut: PWM:1-16 |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 73.3 | 2026-09-12 21:18:47 | MSG | banner | Frame: QUAD/X |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | ChibiOS: 6a85082c |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | RCOut: PWM:1-16 |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 73.6 | 2026-09-12 21:18:47 | MSG | banner | Frame: QUAD/X |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | ChibiOS: 6a85082c |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | RCOut: PWM:1-16 |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 73.9 | 2026-09-12 21:18:48 | MSG | banner | Frame: QUAD/X |
| 443.2 | 2026-09-12 21:24:57 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 443.2 | 2026-09-12 21:24:57 | EV | arm | ARMED(10) |
| 443.2 | 2026-09-12 21:24:57 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 443.7 | 2026-09-12 21:24:57 | EV | ev | AUTO_ARMED(15) |
| 445.2 | 2026-09-12 21:24:59 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 446.2 | 2026-09-12 21:25:00 | EV | ev | NOT_LANDED(28) |
| 463.3 | 2026-09-12 21:25:17 | MODE | kip | → LAND (9), neden GCS_COMMAND(2) |
| 465.6 | 2026-09-12 21:25:19 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 466.4 | 2026-09-12 21:25:20 | EV | ev | LAND_COMPLETE(18) |
| 466.9 | 2026-09-12 21:25:21 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 466.9 | 2026-09-12 21:25:21 | EV | arm | DISARMED(11) |
| 466.9 | 2026-09-12 21:25:21 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 483 | 2026-09-12 21:25:37 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 483.7 | 2026-09-12 21:25:37 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 483.7 | 2026-09-12 21:25:37 | EV | arm | ARMED(10) |
| 483.7 | 2026-09-12 21:25:37 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 484.1 | 2026-09-12 21:25:38 | EV | ev | AUTO_ARMED(15) |
| 485.7 | 2026-09-12 21:25:39 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 486.4 | 2026-09-12 21:25:40 | EV | ev | NOT_LANDED(28) |
| 489.5 | 2026-09-12 21:25:43 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 489.5 | 2026-09-12 21:25:43 | EV | ekf | EKF_YAW_RESET(62) |
| 489.6 | 2026-09-12 21:25:43 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 505.9 | 2026-09-12 21:26:00 | MODE | kip | → LAND (9), neden GCS_COMMAND(2) |
| 513.7 | 2026-09-12 21:26:07 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 514.5 | 2026-09-12 21:26:08 | EV | ev | LAND_COMPLETE(18) |
| 515 | 2026-09-12 21:26:09 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 515 | 2026-09-12 21:26:09 | EV | arm | DISARMED(11) |
| 515 | 2026-09-12 21:26:09 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 580.1 | 2026-09-12 21:27:14 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 580.1 | 2026-09-12 21:27:14 | MSG | gps | GPS Glitch or Compass error |
| 580.2 | 2026-09-12 21:27:14 | MSG | prearm | PreArm: GPS glitching |
| 611.2 | 2026-09-12 21:27:45 | MSG | prearm | PreArm: Compasses inconsistent |
| 611.2 | 2026-09-12 21:27:45 | MSG | prearm | PreArm: GPS glitching |
| 642.2 | 2026-09-12 21:28:16 | MSG | prearm | PreArm: Compasses inconsistent |
| 642.2 | 2026-09-12 21:28:16 | MSG | prearm | PreArm: GPS glitching |
| 673.2 | 2026-09-12 21:28:47 | MSG | prearm | PreArm: Compasses inconsistent |
| 673.2 | 2026-09-12 21:28:47 | MSG | prearm | PreArm: GPS glitching |
| 704.2 | 2026-09-12 21:29:18 | MSG | prearm | PreArm: Compasses inconsistent |
| 704.2 | 2026-09-12 21:29:18 | MSG | prearm | PreArm: GPS glitching |

### #15 · BOOT 96 · `2026-09-12 23-47-27.bin` · 2026-09-12 23:47:27 · 1546.0 s · 4S/16.29 V · beyan B · uçuş 2/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | ChibiOS: 6a85082c |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | Param space used: 875/5376 |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | RC Protocol: IBUS |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | RCOut: PWM:1-16 |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | New mission |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | New rally |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | New fence |
| 14.4 | 2026-09-12 23:47:27 | MSG | banner | Frame: QUAD/X |
| 14.4 | 2026-09-12 23:47:27 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 14.4 | 2026-09-12 23:47:27 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 15.8 | 2026-09-12 23:47:28 | MSG | arm_ret | Arm: Accels inconsistent |
| 15.8 | 2026-09-12 23:47:28 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 15.8 | 2026-09-12 23:47:28 | MSG | arm_ret | Arm: Fence requires position |
| 22.8 | 2026-09-12 23:47:35 | MSG | ekf | EKF3 IMU1 origin set |
| 22.8 | 2026-09-12 23:47:35 | EV | ev | SET_HOME(25) |
| 22.8 | 2026-09-12 23:47:35 | MSG | ekf | EKF3 IMU0 origin set |
| 22.8 | 2026-09-12 23:47:35 | MSG | diger | Field Elevation Set: 115m |
| 27.4 | 2026-09-12 23:47:40 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.2 | 2026-09-12 23:47:43 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-12 23:47:43 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 71.2 | 2026-09-12 23:48:24 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 73.2 | 2026-09-12 23:48:26 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 75.2 | 2026-09-12 23:48:28 | EV | ev | AUTO_ARMED(15) |
| 75.3 | 2026-09-12 23:48:28 | EV | ev | NOT_LANDED(28) |
| 94.7 | 2026-09-12 23:48:47 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 94.7 | 2026-09-12 23:48:47 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 94.7 | 2026-09-12 23:48:47 | EV | arm | DISARMED(11) |
| 94.7 | 2026-09-12 23:48:47 | EV | ev | LAND_COMPLETE(18) |
| 94.7 | 2026-09-12 23:48:47 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 129.2 | 2026-09-12 23:49:22 | MSG | prearm | PreArm: Check mag field (xy diff:105>100) |
| 149.2 | 2026-09-12 23:49:42 | MSG | prearm | PreArm: Check mag field (xy diff:197>100) |
| 151.7 | 2026-09-12 23:49:44 | MSG | arm_ret | Arm: Check mag field (xy diff:203>100) |
| 153.1 | 2026-09-12 23:49:46 | MSG | arm_ret | Arm: Check mag field (xy diff:204>100) |
| 160.9 | 2026-09-12 23:49:53 | MSG | arm_ret | Arm: Check mag field (xy diff:215>100) |
| 169 | 2026-09-12 23:50:02 | MSG | arm_ret | Arm: Check mag field (xy diff:214>100) |
| 176.3 | 2026-09-12 23:50:09 | MSG | arm_ret | Arm: Check mag field (xy diff:212>100) |
| 180.2 | 2026-09-12 23:50:13 | MSG | prearm | PreArm: Check mag field (xy diff:208>100) |
| 180.2 | 2026-09-12 23:50:13 | MSG | prearm | PreArm: High GPS HDOP |
| 183.3 | 2026-09-12 23:50:16 | MSG | arm_ret | Arm: Check mag field (xy diff:209>100) |
| 185.4 | 2026-09-12 23:50:18 | MSG | arm_ret | Arm: Check mag field (xy diff:208>100) |
| 185.4 | 2026-09-12 23:50:18 | MSG | arm_ret | Arm: High GPS HDOP |
| 211.2 | 2026-09-12 23:50:44 | MSG | prearm | PreArm: Check mag field (xy diff:205>100) |
| 242.2 | 2026-09-12 23:51:15 | MSG | prearm | PreArm: Check mag field (xy diff:203>100) |
| 243.3 | 2026-09-12 23:51:16 | MSG | arm_ret | Arm: Check mag field (xy diff:206>100) |
| 273.2 | 2026-09-12 23:51:46 | MSG | prearm | PreArm: Check mag field (xy diff:206>100) |
| 289 | 2026-09-12 23:52:02 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 289 | 2026-09-12 23:52:02 | MSG | gps | GPS Glitch or Compass error |
| 304.2 | 2026-09-12 23:52:17 | MSG | prearm | PreArm: Check mag field (xy diff:206>100) |
| 304.2 | 2026-09-12 23:52:17 | MSG | prearm | PreArm: GPS glitching |
| 310.2 | 2026-09-12 23:52:23 | MSG | arm_ret | Arm: Check mag field (xy diff:208>100) |
| 310.2 | 2026-09-12 23:52:23 | MSG | arm_ret | Arm: GPS glitching |
| 331.8 | 2026-09-12 23:52:44 | ERR | gps | GPS(11) / temizlendi(0) |
| 331.8 | 2026-09-12 23:52:44 | MSG | gps | Glitch cleared |
| 335.2 | 2026-09-12 23:52:48 | MSG | prearm | PreArm: Check mag field (xy diff:208>100) |
| 364.8 | 2026-09-12 23:53:17 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 364.8 | 2026-09-12 23:53:17 | MSG | gps | GPS Glitch or Compass error |
| 366.2 | 2026-09-12 23:53:19 | MSG | prearm | PreArm: Check mag field (xy diff:208>100) |
| 366.2 | 2026-09-12 23:53:19 | MSG | prearm | PreArm: GPS glitching |
| 371.4 | 2026-09-12 23:53:24 | ERR | gps | GPS(11) / temizlendi(0) |
| 371.4 | 2026-09-12 23:53:24 | MSG | gps | Glitch cleared |
| 397.2 | 2026-09-12 23:53:50 | MSG | prearm | PreArm: Check mag field (xy diff:207>100) |
| 428.2 | 2026-09-12 23:54:21 | MSG | prearm | PreArm: Check mag field (xy diff:208>100) |
| 459.2 | 2026-09-12 23:54:52 | MSG | prearm | PreArm: Check mag field (xy diff:208>100) |
| 490.2 | 2026-09-12 23:55:23 | MSG | prearm | PreArm: Check mag field (xy diff:210>100) |
| 521.2 | 2026-09-12 23:55:54 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 552.2 | 2026-09-12 23:56:25 | MSG | prearm | PreArm: Check mag field (xy diff:211>100) |
| 583.2 | 2026-09-12 23:56:56 | MSG | prearm | PreArm: Check mag field (xy diff:210>100) |
| 614.2 | 2026-09-12 23:57:27 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 645.2 | 2026-09-12 23:57:58 | MSG | prearm | PreArm: Check mag field (xy diff:210>100) |
| 669 | 2026-09-12 23:58:22 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 669 | 2026-09-12 23:58:22 | MSG | gps | GPS Glitch or Compass error |
| 676.2 | 2026-09-12 23:58:29 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 676.2 | 2026-09-12 23:58:29 | MSG | prearm | PreArm: GPS glitching |
| 707.2 | 2026-09-12 23:59:00 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 707.2 | 2026-09-12 23:59:00 | MSG | prearm | PreArm: GPS glitching |
| 738.2 | 2026-09-12 23:59:31 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 738.2 | 2026-09-12 23:59:31 | MSG | prearm | PreArm: GPS glitching |
| 747.4 | 2026-09-12 23:59:40 | ERR | gps | GPS(11) / temizlendi(0) |
| 747.4 | 2026-09-12 23:59:40 | MSG | gps | Glitch cleared |
| 753.4 | 2026-09-12 23:59:46 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 753.4 | 2026-09-12 23:59:46 | MSG | gps | GPS Glitch or Compass error |
| 769.2 | 2026-09-13 00:00:02 | MSG | prearm | PreArm: Check mag field (xy diff:209>100) |
| 769.2 | 2026-09-13 00:00:02 | MSG | prearm | PreArm: GPS glitching |
| 787.6 | 2026-09-13 00:00:20 | MSG | arm_ret | Arm: GPS glitching |
| 800.2 | 2026-09-13 00:00:33 | MSG | prearm | PreArm: GPS glitching |
| 831.2 | 2026-09-13 00:01:04 | MSG | prearm | PreArm: GPS glitching |
| 862.2 | 2026-09-13 00:01:35 | MSG | prearm | PreArm: GPS glitching |
| 883.4 | 2026-09-13 00:01:56 | MSG | arm_ret | Arm: GPS glitching |
| 893.2 | 2026-09-13 00:02:06 | MSG | prearm | PreArm: GPS glitching |
| 924.2 | 2026-09-13 00:02:37 | MSG | prearm | PreArm: GPS glitching |
| 955.2 | 2026-09-13 00:03:08 | MSG | prearm | PreArm: GPS glitching |
| 986.2 | 2026-09-13 00:03:39 | MSG | prearm | PreArm: GPS glitching |
| 1017.2 | 2026-09-13 00:04:10 | MSG | prearm | PreArm: GPS glitching |
| 1048.2 | 2026-09-13 00:04:41 | MSG | prearm | PreArm: GPS glitching |
| 1079.2 | 2026-09-13 00:05:12 | MSG | prearm | PreArm: GPS glitching |
| 1110.2 | 2026-09-13 00:05:43 | MSG | prearm | PreArm: GPS glitching |
| 1113.2 | 2026-09-13 00:05:46 | ERR | gps | GPS(11) / temizlendi(0) |
| 1113.2 | 2026-09-13 00:05:46 | MSG | gps | Glitch cleared |
| 1123.7 | 2026-09-13 00:05:56 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 1123.7 | 2026-09-13 00:05:56 | EV | arm | ARMED(10) |
| 1123.7 | 2026-09-13 00:05:56 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1125.7 | 2026-09-13 00:05:58 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 1127.3 | 2026-09-13 00:06:00 | EV | ev | AUTO_ARMED(15) |
| 1127.5 | 2026-09-13 00:06:00 | EV | ev | NOT_LANDED(28) |
| 1132.1 | 2026-09-13 00:06:05 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) |
| 1132.1 | 2026-09-13 00:06:05 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) |
| 1132.1 | 2026-09-13 00:06:05 | MSG | failsafe | Radio Failsafe |
| 1132.1 | 2026-09-13 00:06:05 | MODE | failsafe | → LAND (9), neden RADIO_FAILSAFE(3) |
| 1137.5 | 2026-09-13 00:06:10 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 1138.3 | 2026-09-13 00:06:11 | EV | ev | LAND_COMPLETE(18) |
| 1138.8 | 2026-09-13 00:06:11 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 1138.8 | 2026-09-13 00:06:11 | EV | arm | DISARMED(11) |
| 1138.8 | 2026-09-13 00:06:11 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 1140 | 2026-09-13 00:06:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 1140 | 2026-09-13 00:06:13 | MSG | gps | GPS Glitch or Compass error |
| 1140.2 | 2026-09-13 00:06:13 | MSG | prearm | PreArm: GPS glitching |
| 1140.2 | 2026-09-13 00:06:13 | MSG | prearm | PreArm: Radio failsafe on |
| 1143.3 | 2026-09-13 00:06:16 | ERR | failsafe | FAILSAFE_RADIO(5) / temizlendi(0) |
| 1143.3 | 2026-09-13 00:06:16 | MSG | failsafe | Radio Failsafe Cleared |
| 1150.6 | 2026-09-13 00:06:23 | MSG | arm_ret | Arm: GPS glitching |
| 1154 | 2026-09-13 00:06:27 | MSG | arm_ret | Arm: GPS glitching |
| 1155.3 | 2026-09-13 00:06:28 | MSG | arm_ret | Arm: GPS glitching |
| 1159 | 2026-09-13 00:06:32 | MSG | arm_ret | Arm: GPS glitching |
| 1168.2 | 2026-09-13 00:06:41 | MSG | arm_ret | Arm: GPS glitching |
| 1170.2 | 2026-09-13 00:06:43 | MSG | arm_ret | Arm: GPS glitching |
| 1171.2 | 2026-09-13 00:06:44 | MSG | prearm | PreArm: GPS glitching |
| 1175.5 | 2026-09-13 00:06:48 | MSG | arm_ret | Arm: GPS glitching |
| 1183.7 | 2026-09-13 00:06:56 | MSG | arm_ret | Arm: GPS glitching |
| 1185.4 | 2026-09-13 00:06:58 | MSG | arm_ret | Arm: GPS glitching |
| 1187 | 2026-09-13 00:07:00 | MSG | arm_ret | Arm: GPS glitching |
| 1190.6 | 2026-09-13 00:07:03 | MSG | arm_ret | Arm: GPS glitching |
| 1199.1 | 2026-09-13 00:07:12 | MSG | arm_ret | Arm: GPS glitching |
| 1202.2 | 2026-09-13 00:07:15 | MSG | prearm | PreArm: GPS glitching |
| 1202.4 | 2026-09-13 00:07:15 | MSG | arm_ret | Arm: GPS glitching |
| 1204.3 | 2026-09-13 00:07:17 | MSG | arm_ret | Arm: GPS glitching |
| 1204.3 | 2026-09-13 00:07:17 | MSG | arm_ret | Arm: GPS glitching |
| 1207.7 | 2026-09-13 00:07:20 | MSG | arm_ret | Arm: GPS glitching |
| 1209.3 | 2026-09-13 00:07:22 | MSG | arm_ret | Arm: GPS glitching |
| 1209.3 | 2026-09-13 00:07:22 | MSG | arm_ret | Arm: GPS glitching |
| 1211 | 2026-09-13 00:07:24 | ERR | gps | GPS(11) / temizlendi(0) |
| 1211 | 2026-09-13 00:07:24 | MSG | gps | Glitch cleared |
| 1212.8 | 2026-09-13 00:07:25 | MSG | arm_ret | Arm: LAND mode not armable |
| 1217.8 | 2026-09-13 00:07:30 | MSG | arm_ret | Arm: LAND mode not armable |
| 1221.2 | 2026-09-13 00:07:34 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 1221.5 | 2026-09-13 00:07:34 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1223 | 2026-09-13 00:07:36 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 1223 | 2026-09-13 00:07:36 | EV | arm | ARMED(10) |
| 1223 | 2026-09-13 00:07:36 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 1225 | 2026-09-13 00:07:38 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 1226.3 | 2026-09-13 00:07:39 | EV | ev | AUTO_ARMED(15) |
| 1226.5 | 2026-09-13 00:07:39 | EV | ev | NOT_LANDED(28) |
| 1236.8 | 2026-09-13 00:07:49 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 1236.8 | 2026-09-13 00:07:49 | MSG | gps | GPS Glitch or Compass error |
| 1238.7 | 2026-09-13 00:07:51 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) |
| 1238.7 | 2026-09-13 00:07:51 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) |
| 1238.7 | 2026-09-13 00:07:51 | MSG | failsafe | Radio Failsafe |
| 1238.7 | 2026-09-13 00:07:51 | MODE | failsafe | → LAND (9), neden RADIO_FAILSAFE(3) |
| 1244.5 | 2026-09-13 00:07:57 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 1245.3 | 2026-09-13 00:07:58 | EV | ev | LAND_COMPLETE(18) |
| 1245.8 | 2026-09-13 00:07:58 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 1245.8 | 2026-09-13 00:07:58 | EV | arm | DISARMED(11) |
| 1245.8 | 2026-09-13 00:07:58 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 1250.2 | 2026-09-13 00:08:03 | MSG | prearm | PreArm: GPS glitching |
| 1250.2 | 2026-09-13 00:08:03 | MSG | prearm | PreArm: Radio failsafe on |
| 1281.2 | 2026-09-13 00:08:34 | MSG | prearm | PreArm: GPS glitching |
| 1281.2 | 2026-09-13 00:08:34 | MSG | prearm | PreArm: Radio failsafe on |
| 1312.2 | 2026-09-13 00:09:05 | MSG | prearm | PreArm: GPS glitching |
| 1312.2 | 2026-09-13 00:09:05 | MSG | prearm | PreArm: Radio failsafe on |
| 1343.2 | 2026-09-13 00:09:36 | MSG | prearm | PreArm: GPS glitching |
| 1343.2 | 2026-09-13 00:09:36 | MSG | prearm | PreArm: Radio failsafe on |
| 1374.2 | 2026-09-13 00:10:07 | MSG | prearm | PreArm: GPS glitching |
| 1374.2 | 2026-09-13 00:10:07 | MSG | prearm | PreArm: Radio failsafe on |
| 1396.2 | 2026-09-13 00:10:29 | ERR | failsafe | FAILSAFE_RADIO(5) / temizlendi(0) |
| 1396.2 | 2026-09-13 00:10:29 | MSG | failsafe | Radio Failsafe Cleared |
| 1397.6 | 2026-09-13 00:10:30 | MSG | arm_ret | Arm: GPS glitching |
| 1400 | 2026-09-13 00:10:33 | MSG | arm_ret | Arm: GPS glitching |
| 1401.6 | 2026-09-13 00:10:34 | MSG | arm_ret | Arm: GPS glitching |
| 1403.8 | 2026-09-13 00:10:36 | MSG | arm_ret | Arm: GPS glitching |
| 1405.2 | 2026-09-13 00:10:38 | MSG | prearm | PreArm: GPS glitching |
| 1406.5 | 2026-09-13 00:10:39 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) |
| 1406.5 | 2026-09-13 00:10:39 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) |
| 1406.5 | 2026-09-13 00:10:39 | MSG | failsafe | Radio Failsafe - Disarming |
| 1436.2 | 2026-09-13 00:11:09 | MSG | prearm | PreArm: GPS glitching |
| 1436.2 | 2026-09-13 00:11:09 | MSG | prearm | PreArm: Radio failsafe on |
| 1437.2 | 2026-09-13 00:11:10 | ERR | gps | GPS(11) / temizlendi(0) |
| 1437.2 | 2026-09-13 00:11:10 | MSG | gps | Glitch cleared |
| 1467.2 | 2026-09-13 00:11:40 | MSG | prearm | PreArm: Radio failsafe on |
| 1498.2 | 2026-09-13 00:12:11 | MSG | prearm | PreArm: Radio failsafe on |
| 1529.2 | 2026-09-13 00:12:42 | MSG | prearm | PreArm: Radio failsafe on |
| 1560.2 | 2026-09-13 00:13:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 1560.2 | 2026-09-13 00:13:13 | MSG | gps | GPS Glitch or Compass error |
| 1560.2 | 2026-09-13 00:13:13 | MSG | prearm | PreArm: GPS glitching |
| 1560.2 | 2026-09-13 00:13:13 | MSG | prearm | PreArm: Radio failsafe on |

### #16 · BOOT 115 · `2026-09-13 08-34-30.bin` · 2026-09-13 08:34:10 · 1379.0 s · 3S/12.09 V · beyan A · uçuş 1/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | ChibiOS: 6a85082c |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | Param space used: 899/5376 |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | RC Protocol: IBUS |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | RCOut: PWM:1-16 |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | New mission |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | New rally |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | New fence |
| 15.3 | 2026-09-13 08:34:11 | MSG | banner | Frame: QUAD/X |
| 15.3 | 2026-09-13 08:34:11 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 15.3 | 2026-09-13 08:34:11 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 18.6 | 2026-09-13 08:34:14 | MSG | arm_ret | Arm: Gyros inconsistent |
| 18.6 | 2026-09-13 08:34:14 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 18.6 | 2026-09-13 08:34:14 | MSG | arm_ret | Arm: Fence requires position |
| 20.4 | 2026-09-13 08:34:16 | MSG | arm_ret | Arm: Gyros inconsistent |
| 20.4 | 2026-09-13 08:34:16 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 20.4 | 2026-09-13 08:34:16 | MSG | arm_ret | Arm: Fence requires position |
| 23.9 | 2026-09-13 08:34:19 | MSG | arm_ret | Arm: Gyros inconsistent |
| 23.9 | 2026-09-13 08:34:19 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 23.9 | 2026-09-13 08:34:19 | MSG | arm_ret | Arm: Fence requires position |
| 27.3 | 2026-09-13 08:34:22 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.2 | 2026-09-13 08:34:25 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 30.2 | 2026-09-13 08:34:25 | MSG | prearm | PreArm: Fence requires position |
| 31 | 2026-09-13 08:34:26 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 31 | 2026-09-13 08:34:26 | MSG | arm_ret | Arm: Fence requires position |
| 32.4 | 2026-09-13 08:34:28 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 32.4 | 2026-09-13 08:34:28 | MSG | arm_ret | Arm: Fence requires position |
| 45.3 | 2026-09-13 08:34:41 | MSG | ekf | EKF3 IMU1 origin set |
| 45.3 | 2026-09-13 08:34:41 | EV | ev | SET_HOME(25) |
| 45.3 | 2026-09-13 08:34:41 | MSG | ekf | EKF3 IMU0 origin set |
| 45.3 | 2026-09-13 08:34:41 | MSG | ekf | EKF3 IMU1 is using GPS |
| 45.3 | 2026-09-13 08:34:41 | MSG | ekf | EKF3 IMU0 is using GPS |
| 45.4 | 2026-09-13 08:34:41 | MSG | diger | Field Elevation Set: 96m |
| 152.3 | 2026-09-13 08:36:27 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 154.3 | 2026-09-13 08:36:29 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 162.2 | 2026-09-13 08:36:37 | ARM | arm | DISARM yöntem DISARMDELAY(17) forced=0 checks=0 |
| 162.2 | 2026-09-13 08:36:37 | EV | arm | DISARMED(11) |
| 162.2 | 2026-09-13 08:36:37 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 165.9 | 2026-09-13 08:36:41 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 165.9 | 2026-09-13 08:36:41 | EV | arm | ARMED(10) |
| 165.9 | 2026-09-13 08:36:41 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 167.9 | 2026-09-13 08:36:43 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 169.5 | 2026-09-13 08:36:45 | EV | ev | AUTO_ARMED(15) |
| 173.2 | 2026-09-13 08:36:48 | EV | ev | NOT_LANDED(28) |
| 195.7 | 2026-09-13 08:37:11 | MSG | failsafe | Battery 1 is low 9.75V used 216 mAh |
| 195.7 | 2026-09-13 08:37:11 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) |
| 195.7 | 2026-09-13 08:37:11 | MSG | failsafe | Battery Failsafe |
| 195.7 | 2026-09-13 08:37:11 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) |
| 195.7 | 2026-09-13 08:37:11 | EV | ev | LAND_REPO_ACTIVE(73) |
| 205.9 | 2026-09-13 08:37:21 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 206.7 | 2026-09-13 08:37:22 | EV | ev | LAND_COMPLETE(18) |
| 207.2 | 2026-09-13 08:37:22 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 207.2 | 2026-09-13 08:37:22 | EV | arm | DISARMED(11) |
| 207.2 | 2026-09-13 08:37:22 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 209.2 | 2026-09-13 08:37:24 | MSG | prearm | PreArm: Battery failsafe |
| 216.2 | 2026-09-13 08:37:31 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 219.1 | 2026-09-13 08:37:34 | MSG | arm_ret | Arm: Battery failsafe |
| 220.6 | 2026-09-13 08:37:36 | MSG | arm_ret | Arm: Battery failsafe |
| 221.7 | 2026-09-13 08:37:37 | MSG | arm_ret | Arm: Battery failsafe |
| 230.2 | 2026-09-13 08:37:45 | MSG | arm_ret | Arm: Battery failsafe |
| 231.5 | 2026-09-13 08:37:47 | MSG | arm_ret | Arm: Battery failsafe |
| 232.3 | 2026-09-13 08:37:47 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 233.4 | 2026-09-13 08:37:49 | MSG | arm_ret | Arm: Battery failsafe |
| 234.6 | 2026-09-13 08:37:50 | MSG | arm_ret | Arm: Battery failsafe |
| 236.1 | 2026-09-13 08:37:51 | MSG | arm_ret | Arm: Battery failsafe |
| 239 | 2026-09-13 08:37:54 | MSG | arm_ret | Arm: Battery failsafe |
| 240.2 | 2026-09-13 08:37:55 | MSG | prearm | PreArm: Battery failsafe |
| 243.3 | 2026-09-13 08:37:58 | MSG | arm_ret | Arm: Battery failsafe |
| 244.8 | 2026-09-13 08:38:00 | MSG | arm_ret | Arm: Battery failsafe |
| 247.9 | 2026-09-13 08:38:03 | MSG | arm_ret | Arm: Battery failsafe |
| 248.8 | 2026-09-13 08:38:04 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 251.5 | 2026-09-13 08:38:07 | MSG | arm_ret | Arm: Battery failsafe |
| 271.2 | 2026-09-13 08:38:26 | MSG | prearm | PreArm: Battery failsafe |
| 302.2 | 2026-09-13 08:38:57 | MSG | prearm | PreArm: Battery failsafe |
| 333.2 | 2026-09-13 08:39:28 | MSG | prearm | PreArm: Battery failsafe |
| 364.2 | 2026-09-13 08:39:59 | MSG | prearm | PreArm: Battery failsafe |
| 371.2 | 2026-09-13 08:40:06 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 371.2 | 2026-09-13 08:40:06 | MSG | gps | GPS Glitch or Compass error |
| 395.2 | 2026-09-13 08:40:30 | MSG | prearm | PreArm: GPS glitching |
| 395.2 | 2026-09-13 08:40:30 | MSG | prearm | PreArm: Battery failsafe |
| 426.2 | 2026-09-13 08:41:01 | MSG | prearm | PreArm: GPS and AHRS differ by 25.0m |
| 426.2 | 2026-09-13 08:41:01 | MSG | prearm | PreArm: Battery failsafe |
| 457.2 | 2026-09-13 08:41:32 | MSG | prearm | PreArm: GPS glitching |
| 457.2 | 2026-09-13 08:41:32 | MSG | prearm | PreArm: Battery failsafe |
| 488.2 | 2026-09-13 08:42:03 | MSG | prearm | PreArm: GPS glitching |
| 488.2 | 2026-09-13 08:42:03 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 488.2 | 2026-09-13 08:42:03 | MSG | prearm | PreArm: Battery failsafe |
| 499 | 2026-09-13 08:42:14 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 499 | 2026-09-13 08:42:14 | MSG | ekf | EKF variance |
| 499 | 2026-09-13 08:42:14 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 500.4 | 2026-09-13 08:42:16 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 500.4 | 2026-09-13 08:42:16 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 519.2 | 2026-09-13 08:42:34 | MSG | prearm | PreArm: GPS and AHRS differ by 10.1m |
| 519.2 | 2026-09-13 08:42:34 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 519.2 | 2026-09-13 08:42:34 | MSG | prearm | PreArm: Battery failsafe |
| 550.2 | 2026-09-13 08:43:05 | MSG | prearm | PreArm: GPS and AHRS differ by 15.1m |
| 550.2 | 2026-09-13 08:43:05 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 550.2 | 2026-09-13 08:43:05 | MSG | prearm | PreArm: Battery failsafe |
| 550.2 | 2026-09-13 08:43:05 | MSG | prearm | PreArm: vehicle outside fence |
| 581.2 | 2026-09-13 08:43:36 | MSG | prearm | PreArm: GPS and AHRS differ by 34.9m |
| 581.2 | 2026-09-13 08:43:36 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 581.2 | 2026-09-13 08:43:36 | MSG | prearm | PreArm: Battery failsafe |
| 612.2 | 2026-09-13 08:44:07 | MSG | prearm | PreArm: GPS glitching |
| 612.2 | 2026-09-13 08:44:07 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 612.2 | 2026-09-13 08:44:07 | MSG | prearm | PreArm: Battery failsafe |
| 612.2 | 2026-09-13 08:44:07 | MSG | prearm | PreArm: vehicle outside fence |
| 620.6 | 2026-09-13 08:44:16 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 620.6 | 2026-09-13 08:44:16 | MSG | ekf | EKF variance |
| 620.6 | 2026-09-13 08:44:16 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 631.7 | 2026-09-13 08:44:27 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 631.7 | 2026-09-13 08:44:27 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 643.2 | 2026-09-13 08:44:38 | MSG | prearm | PreArm: GPS and AHRS differ by 12.0m |
| 643.2 | 2026-09-13 08:44:38 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 643.2 | 2026-09-13 08:44:38 | MSG | prearm | PreArm: Battery failsafe |
| 674.2 | 2026-09-13 08:45:09 | MSG | prearm | PreArm: GPS glitching |
| 674.2 | 2026-09-13 08:45:09 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 674.2 | 2026-09-13 08:45:09 | MSG | prearm | PreArm: Battery failsafe |
| 705.2 | 2026-09-13 08:45:40 | MSG | prearm | PreArm: GPS and AHRS differ by 12.7m |
| 705.2 | 2026-09-13 08:45:40 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 705.2 | 2026-09-13 08:45:40 | MSG | prearm | PreArm: Battery failsafe |
| 736.2 | 2026-09-13 08:46:11 | MSG | prearm | PreArm: GPS and AHRS differ by 28.0m |
| 736.2 | 2026-09-13 08:46:11 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 736.2 | 2026-09-13 08:46:11 | MSG | prearm | PreArm: Battery failsafe |
| 736.2 | 2026-09-13 08:46:11 | MSG | prearm | PreArm: vehicle outside fence |
| 767.2 | 2026-09-13 08:46:42 | MSG | prearm | PreArm: GPS and AHRS differ by 75.0m |
| 767.2 | 2026-09-13 08:46:42 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 767.2 | 2026-09-13 08:46:42 | MSG | prearm | PreArm: Battery failsafe |
| 767.2 | 2026-09-13 08:46:42 | MSG | prearm | PreArm: vehicle outside fence |
| 781.5 | 2026-09-13 08:46:57 | MSG | ekf | EKF3 lane switch 1 |
| 781.5 | 2026-09-13 08:46:57 | EV | ekf | EKF_YAW_RESET(62) |
| 781.6 | 2026-09-13 08:46:57 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 781.6 | 2026-09-13 08:46:57 | MSG | ekf | EKF variance |
| 781.6 | 2026-09-13 08:46:57 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 784.4 | 2026-09-13 08:47:00 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 784.4 | 2026-09-13 08:47:00 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 798.2 | 2026-09-13 08:47:13 | MSG | prearm | PreArm: GPS and AHRS differ by 16.2m |
| 798.2 | 2026-09-13 08:47:13 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 798.2 | 2026-09-13 08:47:13 | MSG | prearm | PreArm: Battery failsafe |
| 798.2 | 2026-09-13 08:47:13 | MSG | prearm | PreArm: vehicle outside fence |
| 829.2 | 2026-09-13 08:47:44 | MSG | prearm | PreArm: GPS and AHRS differ by 34.1m |
| 829.2 | 2026-09-13 08:47:44 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 829.2 | 2026-09-13 08:47:44 | MSG | prearm | PreArm: Battery failsafe |
| 829.2 | 2026-09-13 08:47:44 | MSG | prearm | PreArm: vehicle outside fence |
| 860.2 | 2026-09-13 08:48:15 | MSG | prearm | PreArm: GPS glitching |
| 860.2 | 2026-09-13 08:48:15 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 860.2 | 2026-09-13 08:48:15 | MSG | prearm | PreArm: Battery failsafe |
| 870 | 2026-09-13 08:48:25 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 870 | 2026-09-13 08:48:25 | MSG | ekf | EKF variance |
| 870 | 2026-09-13 08:48:25 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 877.1 | 2026-09-13 08:48:32 | MSG | ekf | EKF3 IMU0 stopped aiding |
| 877.1 | 2026-09-13 08:48:32 | MSG | ekf | EKF3 IMU1 stopped aiding |
| 877.1 | 2026-09-13 08:48:32 | ERR | gps | GPS(11) / temizlendi(0) |
| 877.1 | 2026-09-13 08:48:32 | MSG | gps | Glitch cleared |
| 891.2 | 2026-09-13 08:48:46 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 891.2 | 2026-09-13 08:48:46 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 891.2 | 2026-09-13 08:48:46 | MSG | prearm | PreArm: Battery failsafe |
| 891.2 | 2026-09-13 08:48:46 | MSG | prearm | PreArm: Fence requires position |
| 922.2 | 2026-09-13 08:49:17 | MSG | prearm | PreArm: Need Position Estimate |
| 922.2 | 2026-09-13 08:49:17 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 922.2 | 2026-09-13 08:49:17 | MSG | prearm | PreArm: Battery failsafe |
| 922.2 | 2026-09-13 08:49:17 | MSG | prearm | PreArm: vehicle outside fence |
| 953.2 | 2026-09-13 08:49:48 | MSG | prearm | PreArm: Need Position Estimate |
| 953.2 | 2026-09-13 08:49:48 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 953.2 | 2026-09-13 08:49:48 | MSG | prearm | PreArm: Battery failsafe |
| 984.2 | 2026-09-13 08:50:19 | MSG | prearm | PreArm: Need Position Estimate |
| 984.2 | 2026-09-13 08:50:19 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 984.2 | 2026-09-13 08:50:19 | MSG | prearm | PreArm: Battery failsafe |
| 984.2 | 2026-09-13 08:50:19 | MSG | prearm | PreArm: vehicle outside fence |
| 1015.2 | 2026-09-13 08:50:50 | MSG | prearm | PreArm: Need Position Estimate |
| 1015.2 | 2026-09-13 08:50:50 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1015.2 | 2026-09-13 08:50:50 | MSG | prearm | PreArm: Battery failsafe |
| 1029.7 | 2026-09-13 08:51:05 | MSG | arm_ret | Arm: Need Position Estimate |
| 1029.7 | 2026-09-13 08:51:05 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1029.7 | 2026-09-13 08:51:05 | MSG | arm_ret | Arm: Battery failsafe |
| 1033.8 | 2026-09-13 08:51:09 | MSG | arm_ret | Arm: Need Position Estimate |
| 1033.8 | 2026-09-13 08:51:09 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1033.8 | 2026-09-13 08:51:09 | MSG | arm_ret | Arm: Battery failsafe |
| 1035.5 | 2026-09-13 08:51:11 | MSG | arm_ret | Arm: Need Position Estimate |
| 1035.5 | 2026-09-13 08:51:11 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1035.5 | 2026-09-13 08:51:11 | MSG | arm_ret | Arm: Battery failsafe |
| 1046.2 | 2026-09-13 08:51:21 | MSG | prearm | PreArm: Need Position Estimate |
| 1046.2 | 2026-09-13 08:51:21 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1046.2 | 2026-09-13 08:51:21 | MSG | prearm | PreArm: Battery failsafe |
| 1077.2 | 2026-09-13 08:51:52 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1077.2 | 2026-09-13 08:51:52 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1077.2 | 2026-09-13 08:51:52 | MSG | prearm | PreArm: Battery failsafe |
| 1077.2 | 2026-09-13 08:51:52 | MSG | prearm | PreArm: Fence requires position |
| 1108.2 | 2026-09-13 08:52:23 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1108.2 | 2026-09-13 08:52:23 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1108.2 | 2026-09-13 08:52:23 | MSG | prearm | PreArm: Battery failsafe |
| 1108.2 | 2026-09-13 08:52:23 | MSG | prearm | PreArm: Fence requires position |
| 1139.2 | 2026-09-13 08:52:54 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1139.2 | 2026-09-13 08:52:54 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1139.2 | 2026-09-13 08:52:54 | MSG | prearm | PreArm: Battery failsafe |
| 1139.2 | 2026-09-13 08:52:54 | MSG | prearm | PreArm: Fence requires position |
| 1170.2 | 2026-09-13 08:53:25 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1170.2 | 2026-09-13 08:53:25 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1170.2 | 2026-09-13 08:53:25 | MSG | prearm | PreArm: Battery failsafe |
| 1170.2 | 2026-09-13 08:53:25 | MSG | prearm | PreArm: Fence requires position |
| 1201.2 | 2026-09-13 08:53:56 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1201.2 | 2026-09-13 08:53:56 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1201.2 | 2026-09-13 08:53:56 | MSG | prearm | PreArm: Battery failsafe |
| 1201.2 | 2026-09-13 08:53:56 | MSG | prearm | PreArm: Fence requires position |
| 1232.2 | 2026-09-13 08:54:27 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1232.2 | 2026-09-13 08:54:27 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1232.2 | 2026-09-13 08:54:27 | MSG | prearm | PreArm: Battery failsafe |
| 1232.2 | 2026-09-13 08:54:27 | MSG | prearm | PreArm: Fence requires position |
| 1263.2 | 2026-09-13 08:54:58 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1263.2 | 2026-09-13 08:54:58 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1263.2 | 2026-09-13 08:54:58 | MSG | prearm | PreArm: Battery failsafe |
| 1263.2 | 2026-09-13 08:54:58 | MSG | prearm | PreArm: Fence requires position |
| 1294.2 | 2026-09-13 08:55:29 | MSG | prearm | PreArm: GPS 1: Bad fix |
| 1294.2 | 2026-09-13 08:55:29 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1294.2 | 2026-09-13 08:55:29 | MSG | prearm | PreArm: Battery failsafe |
| 1294.2 | 2026-09-13 08:55:29 | MSG | prearm | PreArm: Fence requires position |
| 1309.9 | 2026-09-13 08:55:45 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 1309.9 | 2026-09-13 08:55:45 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1309.9 | 2026-09-13 08:55:45 | MSG | arm_ret | Arm: Battery failsafe |
| 1309.9 | 2026-09-13 08:55:45 | MSG | arm_ret | Arm: Fence requires position |
| 1314.2 | 2026-09-13 08:55:49 | MSG | arm_ret | Arm: Need Position Estimate |
| 1314.2 | 2026-09-13 08:55:49 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1314.2 | 2026-09-13 08:55:49 | MSG | arm_ret | Arm: Battery failsafe |
| 1316.2 | 2026-09-13 08:55:51 | MSG | arm_ret | Arm: Need Position Estimate |
| 1316.2 | 2026-09-13 08:55:51 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1316.2 | 2026-09-13 08:55:51 | MSG | arm_ret | Arm: Battery failsafe |
| 1322.9 | 2026-09-13 08:55:58 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 1323.9 | 2026-09-13 08:55:59 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 1325.2 | 2026-09-13 08:56:00 | MSG | prearm | PreArm: Need Position Estimate |
| 1325.2 | 2026-09-13 08:56:00 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1325.2 | 2026-09-13 08:56:00 | MSG | prearm | PreArm: Battery failsafe |
| 1325.2 | 2026-09-13 08:56:00 | MSG | prearm | PreArm: vehicle outside fence |
| 1326.4 | 2026-09-13 08:56:02 | MSG | arm_ret | Arm: GPS 1: Bad fix |
| 1326.4 | 2026-09-13 08:56:02 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 1326.4 | 2026-09-13 08:56:02 | MSG | arm_ret | Arm: Battery failsafe |
| 1326.4 | 2026-09-13 08:56:02 | MSG | arm_ret | Arm: Fence requires position |
| 1356.2 | 2026-09-13 08:56:31 | MSG | prearm | PreArm: Check mag field (xy diff:126>100) |
| 1356.2 | 2026-09-13 08:56:31 | MSG | prearm | PreArm: Need Position Estimate |
| 1356.2 | 2026-09-13 08:56:31 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1356.2 | 2026-09-13 08:56:31 | MSG | prearm | PreArm: Battery failsafe |
| 1373.9 | 2026-09-13 08:56:49 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) |
| 1373.9 | 2026-09-13 08:56:49 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) |
| 1373.9 | 2026-09-13 08:56:49 | MSG | failsafe | Radio Failsafe - Disarming |
| 1387.2 | 2026-09-13 08:57:02 | MSG | prearm | PreArm: Need Position Estimate |
| 1387.2 | 2026-09-13 08:57:02 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 1387.2 | 2026-09-13 08:57:02 | MSG | prearm | PreArm: Radio failsafe on |
| 1387.2 | 2026-09-13 08:57:02 | MSG | prearm | PreArm: Battery failsafe |
| 1391.5 | 2026-09-13 08:57:07 | MSG | ekf | EKF3 IMU1 is using GPS |
| 1391.7 | 2026-09-13 08:57:07 | MSG | ekf | EKF3 IMU0 is using GPS |
| 1391.7 | 2026-09-13 08:57:07 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 1391.7 | 2026-09-13 08:57:07 | MSG | gps | GPS Glitch or Compass error |
| 1392.6 | 2026-09-13 08:57:08 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 1392.6 | 2026-09-13 08:57:08 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |
| 1393.1 | 2026-09-13 08:57:08 | ERR | gps | GPS(11) / temizlendi(0) |
| 1393.1 | 2026-09-13 08:57:08 | MSG | gps | Glitch cleared |

### #17 · BOOT 116 · `2026-09-13 08-57-45.bin` · 2026-09-13 08:57:44 · 79.1 s · 3S/11.07 V · beyan A · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | ChibiOS: 6a85082c |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | Param space used: 907/5376 |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | RC Protocol: IBUS |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | RCOut: PWM:1-16 |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | New mission |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | New rally |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | New fence |
| 23.3 | 2026-09-13 08:57:44 | MSG | banner | Frame: QUAD/X |
| 23.3 | 2026-09-13 08:57:44 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 23.3 | 2026-09-13 08:57:44 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 24.2 | 2026-09-13 08:57:45 | MSG | arm_ret | Arm: Gyros inconsistent |
| 24.2 | 2026-09-13 08:57:45 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 24.2 | 2026-09-13 08:57:45 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3C8 |
| 24.2 | 2026-09-13 08:57:45 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 26.4 | 2026-09-13 08:57:47 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 27.1 | 2026-09-13 08:57:48 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 27.1 | 2026-09-13 08:57:48 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 27.1 | 2026-09-13 08:57:48 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 27.3 | 2026-09-13 08:57:48 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 28.5 | 2026-09-13 08:57:50 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 28.5 | 2026-09-13 08:57:50 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 28.5 | 2026-09-13 08:57:50 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 29.9 | 2026-09-13 08:57:51 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 29.9 | 2026-09-13 08:57:51 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 29.9 | 2026-09-13 08:57:51 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 30.2 | 2026-09-13 08:57:51 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-13 08:57:51 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 30.2 | 2026-09-13 08:57:51 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 36 | 2026-09-13 08:57:57 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 36 | 2026-09-13 08:57:57 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 36 | 2026-09-13 08:57:57 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 44.2 | 2026-09-13 08:58:05 | MSG | ekf | EKF3 IMU1 is using GPS |
| 44.2 | 2026-09-13 08:58:05 | MSG | ekf | EKF3 IMU0 is using GPS |
| 81.1 | 2026-09-13 08:58:42 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 92.2 | 2026-09-13 08:58:53 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 92.2 | 2026-09-13 08:58:53 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |

### #18 · BOOT 117 · `1980-01-06 07-59-23.bin` · 2026-09-13 08:59:21 · 406.5 s · 3S/11.05 V · beyan A · uçuş 0/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | ChibiOS: 6a85082c |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | Param space used: 907/5376 |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | RC Protocol: IBUS |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | RCOut: PWM:1-16 |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | New mission |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | New rally |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | New fence |
| 13.9 | 2026-09-13 08:59:21 | MSG | banner | Frame: QUAD/X |
| 13.9 | 2026-09-13 08:59:21 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 15.1 | 2026-09-13 08:59:23 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 22.7 | 2026-09-13 08:59:30 | MSG | arm_ret | Arm: Gyros inconsistent |
| 22.7 | 2026-09-13 08:59:30 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 22.7 | 2026-09-13 08:59:30 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 22.7 | 2026-09-13 08:59:30 | MSG | arm_ret | Arm: Fence requires position |
| 25.4 | 2026-09-13 08:59:33 | MSG | ekf | EKF3 IMU0 origin set |
| 25.4 | 2026-09-13 08:59:33 | MSG | ekf | EKF3 IMU1 origin set |
| 25.4 | 2026-09-13 08:59:33 | EV | ev | SET_HOME(25) |
| 25.4 | 2026-09-13 08:59:33 | MSG | diger | Field Elevation Set: 97m |
| 26.2 | 2026-09-13 08:59:34 | MSG | arm_ret | Arm: Gyros inconsistent |
| 26.2 | 2026-09-13 08:59:34 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 26.2 | 2026-09-13 08:59:34 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3C8 |
| 26.2 | 2026-09-13 08:59:34 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 29.9 | 2026-09-13 08:59:37 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.8 | 2026-09-13 08:59:38 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.8 | 2026-09-13 08:59:38 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 30.8 | 2026-09-13 08:59:38 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 36.4 | 2026-09-13 08:59:44 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 36.4 | 2026-09-13 08:59:44 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 36.4 | 2026-09-13 08:59:44 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 46.8 | 2026-09-13 08:59:54 | MSG | ekf | EKF3 IMU0 is using GPS |
| 46.8 | 2026-09-13 08:59:54 | MSG | ekf | EKF3 IMU1 is using GPS |
| 92.8 | 2026-09-13 09:00:40 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 185.8 | 2026-09-13 09:02:13 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 207.3 | 2026-09-13 09:02:35 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 214.3 | 2026-09-13 09:02:42 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 214.6 | 2026-09-13 09:02:42 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 215.3 | 2026-09-13 09:02:43 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 216.8 | 2026-09-13 09:02:44 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 330.9 | 2026-09-13 09:04:38 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 335.4 | 2026-09-13 09:04:43 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 340.4 | 2026-09-13 09:04:48 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 340.8 | 2026-09-13 09:04:48 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |

### #19 · BOOT 118 · `1980-01-06 08-07-20.bin` · 2026-09-13 09:07:18 · 424.0 s · 3S/10.99 V · beyan A · uçuş 1/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | ChibiOS: 6a85082c |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | Param space used: 907/5376 |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | RC Protocol: IBUS |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | RCOut: PWM:1-16 |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | New mission |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | New rally |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | New fence |
| 9.6 | 2026-09-13 09:07:18 | MSG | banner | Frame: QUAD/X |
| 9.6 | 2026-09-13 09:07:18 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 10.4 | 2026-09-13 09:07:19 | MSG | arm_ret | Arm: Accels inconsistent |
| 10.4 | 2026-09-13 09:07:19 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 10.4 | 2026-09-13 09:07:19 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 10.4 | 2026-09-13 09:07:19 | MSG | arm_ret | Arm: Fence requires position |
| 11.8 | 2026-09-13 09:07:20 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 12.5 | 2026-09-13 09:07:21 | MSG | arm_ret | Arm: Accels inconsistent |
| 12.5 | 2026-09-13 09:07:21 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 12.5 | 2026-09-13 09:07:21 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 12.5 | 2026-09-13 09:07:21 | MSG | arm_ret | Arm: Fence requires position |
| 21.9 | 2026-09-13 09:07:30 | MSG | ekf | EKF3 IMU1 origin set |
| 21.9 | 2026-09-13 09:07:30 | EV | ev | SET_HOME(25) |
| 22 | 2026-09-13 09:07:30 | MSG | diger | Field Elevation Set: 97m |
| 22.1 | 2026-09-13 09:07:31 | MSG | ekf | EKF3 IMU0 origin set |
| 26.6 | 2026-09-13 09:07:35 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 103.9 | 2026-09-13 09:08:52 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 142.1 | 2026-09-13 09:09:30 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 154.5 | 2026-09-13 09:09:43 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 216.5 | 2026-09-13 09:10:45 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 235.3 | 2026-09-13 09:11:04 | MSG | arm_ret | Arm: Battery 1 voltage failsafe critical >= low |
| 247.5 | 2026-09-13 09:11:16 | MSG | prearm | PreArm: Battery 1 voltage failsafe critical >= low |
| 281.6 | 2026-09-13 09:11:50 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 283.6 | 2026-09-13 09:11:52 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 291 | 2026-09-13 09:11:59 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 291 | 2026-09-13 09:11:59 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 291 | 2026-09-13 09:11:59 | EV | arm | DISARMED(11) |
| 291 | 2026-09-13 09:11:59 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 291.4 | 2026-09-13 09:12:00 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 292.6 | 2026-09-13 09:12:01 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 294 | 2026-09-13 09:12:02 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 297.4 | 2026-09-13 09:12:06 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 297.4 | 2026-09-13 09:12:06 | EV | arm | ARMED(10) |
| 297.4 | 2026-09-13 09:12:06 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 299.4 | 2026-09-13 09:12:08 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 300.6 | 2026-09-13 09:12:09 | EV | ev | AUTO_ARMED(15) |
| 304 | 2026-09-13 09:12:12 | EV | ev | NOT_LANDED(28) |
| 310.2 | 2026-09-13 09:12:19 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 310.2 | 2026-09-13 09:12:19 | EV | ekf | EKF_YAW_RESET(62) |
| 310.3 | 2026-09-13 09:12:19 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 319.7 | 2026-09-13 09:12:28 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 319.7 | 2026-09-13 09:12:28 | MSG | failsafe | GCS Failsafe - Continuing Pilot Control |
| 320.7 | 2026-09-13 09:12:29 | MSG | failsafe | GCS Failsafe Cleared |
| 320.7 | 2026-09-13 09:12:29 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 325.6 | 2026-09-13 09:12:34 | MSG | failsafe | Battery 1 is low 9.73V used 227 mAh |
| 325.6 | 2026-09-13 09:12:34 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) |
| 325.6 | 2026-09-13 09:12:34 | MSG | failsafe | Battery Failsafe |
| 325.6 | 2026-09-13 09:12:34 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) |
| 326.8 | 2026-09-13 09:12:35 | EV | ev | LAND_REPO_ACTIVE(73) |
| 340.6 | 2026-09-13 09:12:49 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 340.9 | 2026-09-13 09:12:49 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 340.9 | 2026-09-13 09:12:49 | EV | arm | DISARMED(11) |
| 340.9 | 2026-09-13 09:12:49 | EV | ev | LAND_COMPLETE(18) |
| 340.9 | 2026-09-13 09:12:49 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 345.5 | 2026-09-13 09:12:54 | MSG | prearm | PreArm: Battery failsafe |
| 376.5 | 2026-09-13 09:13:25 | MSG | prearm | PreArm: Battery failsafe |
| 401.6 | 2026-09-13 09:13:50 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 401.6 | 2026-09-13 09:13:50 | MSG | gps | GPS Glitch or Compass error |
| 407.5 | 2026-09-13 09:13:56 | MSG | prearm | PreArm: GPS glitching |
| 407.5 | 2026-09-13 09:13:56 | MSG | prearm | PreArm: Battery failsafe |

### #20 · BOOT 119 · `2026-09-13 09-26-58.bin` · 2026-09-13 09:26:58 · 665.0 s · 4S/16.69 V · beyan B · uçuş 0/kısa 6

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | ChibiOS: 6a85082c |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | Param space used: 907/5376 |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | RC Protocol: IBUS |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | RCOut: PWM:1-16 |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | New mission |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | New rally |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | New fence |
| 14.1 | 2026-09-13 09:26:58 | MSG | banner | Frame: QUAD/X |
| 14.1 | 2026-09-13 09:26:58 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 14.3 | 2026-09-13 09:26:58 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 15.1 | 2026-09-13 09:26:59 | MSG | arm_ret | Arm: Hardware safety switch |
| 15.1 | 2026-09-13 09:26:59 | MSG | arm_ret | Arm: Accels inconsistent |
| 15.1 | 2026-09-13 09:26:59 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 15.1 | 2026-09-13 09:26:59 | MSG | arm_ret | Arm: Fence requires position |
| 24 | 2026-09-13 09:27:08 | MSG | arm_ret | Arm: Gyros inconsistent |
| 24 | 2026-09-13 09:27:08 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 24 | 2026-09-13 09:27:08 | MSG | arm_ret | Arm: Fence requires position |
| 24.7 | 2026-09-13 09:27:09 | MSG | ekf | EKF3 IMU0 origin set |
| 24.7 | 2026-09-13 09:27:09 | EV | ev | SET_HOME(25) |
| 24.7 | 2026-09-13 09:27:09 | MSG | ekf | EKF3 IMU1 origin set |
| 24.8 | 2026-09-13 09:27:09 | MSG | diger | Field Elevation Set: 99m |
| 25.4 | 2026-09-13 09:27:09 | MSG | arm_ret | Arm: Gyros inconsistent |
| 25.4 | 2026-09-13 09:27:09 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 25.4 | 2026-09-13 09:27:09 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3C8 |
| 29.1 | 2026-09-13 09:27:13 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 31 | 2026-09-13 09:27:15 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 31 | 2026-09-13 09:27:15 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 51.2 | 2026-09-13 09:27:35 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 53.2 | 2026-09-13 09:27:37 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 53.3 | 2026-09-13 09:27:37 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 54.7 | 2026-09-13 09:27:38 | EV | ev | AUTO_ARMED(15) |
| 57.1 | 2026-09-13 09:27:41 | EV | ev | NOT_LANDED(28) |
| 60.3 | 2026-09-13 09:27:44 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 62.5 | 2026-09-13 09:27:46 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 62.5 | 2026-09-13 09:27:46 | EV | arm | DISARMED(11) |
| 62.5 | 2026-09-13 09:27:46 | EV | ev | LAND_COMPLETE(18) |
| 62.5 | 2026-09-13 09:27:46 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 62.5 | 2026-09-13 09:27:46 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 217.1 | 2026-09-13 09:30:21 | MSG | arm_ret | Arm: LAND mode not armable |
| 224.3 | 2026-09-13 09:30:28 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 225.5 | 2026-09-13 09:30:29 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 225.5 | 2026-09-13 09:30:29 | EV | arm | ARMED(10) |
| 225.5 | 2026-09-13 09:30:29 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 225.5 | 2026-09-13 09:30:29 | EV | ev | AUTO_ARMED(15) |
| 226.9 | 2026-09-13 09:30:31 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 226.9 | 2026-09-13 09:30:31 | EV | arm | DISARMED(11) |
| 234.3 | 2026-09-13 09:30:38 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 234.3 | 2026-09-13 09:30:38 | EV | arm | ARMED(10) |
| 234.3 | 2026-09-13 09:30:38 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 234.3 | 2026-09-13 09:30:38 | EV | ev | AUTO_ARMED(15) |
| 236.3 | 2026-09-13 09:30:40 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 239 | 2026-09-13 09:30:43 | EV | ev | NOT_LANDED(28) |
| 241 | 2026-09-13 09:30:45 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 242.8 | 2026-09-13 09:30:47 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 243.6 | 2026-09-13 09:30:47 | EV | ev | LAND_COMPLETE(18) |
| 243.9 | 2026-09-13 09:30:48 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 243.9 | 2026-09-13 09:30:48 | EV | arm | DISARMED(11) |
| 243.9 | 2026-09-13 09:30:48 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 341.1 | 2026-09-13 09:32:25 | MSG | arm_ret | Arm: LAND mode not armable |
| 346.2 | 2026-09-13 09:32:30 | MSG | arm_ret | Arm: LAND mode not armable |
| 347.6 | 2026-09-13 09:32:31 | MSG | arm_ret | Arm: LAND mode not armable |
| 351.8 | 2026-09-13 09:32:36 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 352.4 | 2026-09-13 09:32:36 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 352.4 | 2026-09-13 09:32:36 | EV | arm | ARMED(10) |
| 352.4 | 2026-09-13 09:32:36 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 352.4 | 2026-09-13 09:32:36 | EV | ev | AUTO_ARMED(15) |
| 354.4 | 2026-09-13 09:32:38 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 360.3 | 2026-09-13 09:32:44 | EV | ev | NOT_LANDED(28) |
| 361.6 | 2026-09-13 09:32:45 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 362.6 | 2026-09-13 09:32:46 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 362.6 | 2026-09-13 09:32:46 | EV | arm | DISARMED(11) |
| 362.6 | 2026-09-13 09:32:46 | EV | ev | LAND_COMPLETE(18) |
| 362.6 | 2026-09-13 09:32:46 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 362.6 | 2026-09-13 09:32:46 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 401.2 | 2026-09-13 09:33:25 | MSG | arm_ret | Arm: LAND mode not armable |
| 401.8 | 2026-09-13 09:33:26 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 403.7 | 2026-09-13 09:33:27 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 403.7 | 2026-09-13 09:33:27 | EV | arm | ARMED(10) |
| 403.7 | 2026-09-13 09:33:27 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 403.7 | 2026-09-13 09:33:27 | EV | ev | AUTO_ARMED(15) |
| 405.5 | 2026-09-13 09:33:29 | MSG | kip_red | Mode change to STABILIZE failed: throttle too high |
| 405.5 | 2026-09-13 09:33:29 | ERR | kip_red | FLIGHT_MODE(10) / kip STABILIZE reddedildi(0) |
| 405.7 | 2026-09-13 09:33:29 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 407.6 | 2026-09-13 09:33:31 | EV | ev | NOT_LANDED(28) |
| 409 | 2026-09-13 09:33:33 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 412.1 | 2026-09-13 09:33:36 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 412.2 | 2026-09-13 09:33:36 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 412.2 | 2026-09-13 09:33:36 | EV | arm | DISARMED(11) |
| 412.2 | 2026-09-13 09:33:36 | EV | ev | LAND_COMPLETE(18) |
| 412.2 | 2026-09-13 09:33:36 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 544.1 | 2026-09-13 09:35:48 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 545.6 | 2026-09-13 09:35:49 | MSG | arm_ret | Arm: Throttle too high |
| 549.5 | 2026-09-13 09:35:53 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 549.5 | 2026-09-13 09:35:53 | EV | arm | ARMED(10) |
| 549.5 | 2026-09-13 09:35:53 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 549.5 | 2026-09-13 09:35:53 | EV | ev | AUTO_ARMED(15) |
| 551.5 | 2026-09-13 09:35:55 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 553 | 2026-09-13 09:35:57 | EV | ev | AUTO_ARMED(15) |
| 553.2 | 2026-09-13 09:35:57 | EV | ev | NOT_LANDED(28) |
| 555.8 | 2026-09-13 09:36:00 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 556.7 | 2026-09-13 09:36:00 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 557.5 | 2026-09-13 09:36:01 | EV | ev | LAND_COMPLETE(18) |
| 561.1 | 2026-09-13 09:36:05 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 561.1 | 2026-09-13 09:36:05 | EV | arm | DISARMED(11) |
| 561.1 | 2026-09-13 09:36:05 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 575.1 | 2026-09-13 09:36:19 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 577.4 | 2026-09-13 09:36:21 | MSG | arm_ret | Arm: Throttle too high |
| 583.5 | 2026-09-13 09:36:27 | MSG | arm_ret | Arm: Yaw (RC4) is not neutral |
| 588.9 | 2026-09-13 09:36:33 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 588.9 | 2026-09-13 09:36:33 | EV | arm | ARMED(10) |
| 588.9 | 2026-09-13 09:36:33 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 590.9 | 2026-09-13 09:36:35 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 592.7 | 2026-09-13 09:36:36 | EV | ev | AUTO_ARMED(15) |
| 592.8 | 2026-09-13 09:36:37 | EV | ev | NOT_LANDED(28) |
| 595.9 | 2026-09-13 09:36:40 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 596.7 | 2026-09-13 09:36:40 | EV | ev | LAND_COMPLETE(18) |
| 596.8 | 2026-09-13 09:36:41 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 596.8 | 2026-09-13 09:36:41 | EV | arm | DISARMED(11) |
| 596.8 | 2026-09-13 09:36:41 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

### #21 · BOOT 120 · `2026-09-13 09-42-26.bin` · 2026-09-13 09:42:25 · 639.0 s · 3S/11.99 V · beyan A · uçuş 3/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | ChibiOS: 6a85082c |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | Param space used: 907/5376 |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | RC Protocol: IBUS |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | RCOut: PWM:1-16 |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | New mission |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | New rally |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | New fence |
| 11.6 | 2026-09-13 09:42:26 | MSG | banner | Frame: QUAD/X |
| 11.6 | 2026-09-13 09:42:26 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 11.6 | 2026-09-13 09:42:26 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 20.9 | 2026-09-13 09:42:35 | MSG | ekf | EKF3 IMU1 origin set |
| 20.9 | 2026-09-13 09:42:35 | EV | ev | SET_HOME(25) |
| 21 | 2026-09-13 09:42:35 | MSG | diger | Field Elevation Set: 112m |
| 21.1 | 2026-09-13 09:42:35 | MSG | ekf | EKF3 IMU0 origin set |
| 21.6 | 2026-09-13 09:42:36 | MSG | arm_ret | Arm: Gyros inconsistent |
| 21.6 | 2026-09-13 09:42:36 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 21.6 | 2026-09-13 09:42:36 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3E8 |
| 25.6 | 2026-09-13 09:42:40 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.5 | 2026-09-13 09:42:44 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.5 | 2026-09-13 09:42:44 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 47 | 2026-09-13 09:43:01 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 49 | 2026-09-13 09:43:03 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 49.9 | 2026-09-13 09:43:04 | EV | ev | AUTO_ARMED(15) |
| 54.1 | 2026-09-13 09:43:08 | EV | ev | NOT_LANDED(28) |
| 56 | 2026-09-13 09:43:10 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 56.8 | 2026-09-13 09:43:11 | EV | ev | LAND_COMPLETE(18) |
| 59.5 | 2026-09-13 09:43:13 | EV | ev | NOT_LANDED(28) |
| 72.6 | 2026-09-13 09:43:27 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 72.6 | 2026-09-13 09:43:27 | EV | ekf | EKF_YAW_RESET(62) |
| 72.9 | 2026-09-13 09:43:27 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 82.7 | 2026-09-13 09:43:37 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 90.9 | 2026-09-13 09:43:45 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 91.7 | 2026-09-13 09:43:46 | EV | ev | LAND_COMPLETE(18) |
| 92.2 | 2026-09-13 09:43:46 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 92.2 | 2026-09-13 09:43:46 | EV | arm | DISARMED(11) |
| 92.2 | 2026-09-13 09:43:46 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 174.1 | 2026-09-13 09:45:08 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 174.1 | 2026-09-13 09:45:08 | MSG | failsafe | GCS Failsafe |
| 179 | 2026-09-13 09:45:13 | MSG | failsafe | GCS Failsafe Cleared |
| 179 | 2026-09-13 09:45:13 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 179.9 | 2026-09-13 09:45:14 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 180.4 | 2026-09-13 09:45:14 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 180.4 | 2026-09-13 09:45:14 | EV | arm | ARMED(10) |
| 180.4 | 2026-09-13 09:45:14 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 180.4 | 2026-09-13 09:45:14 | EV | ev | AUTO_ARMED(15) |
| 182.4 | 2026-09-13 09:45:16 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 183 | 2026-09-13 09:45:17 | EV | ev | NOT_LANDED(28) |
| 186 | 2026-09-13 09:45:20 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 186 | 2026-09-13 09:45:20 | EV | ekf | EKF_YAW_RESET(62) |
| 186.1 | 2026-09-13 09:45:20 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 198 | 2026-09-13 09:45:32 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 198 | 2026-09-13 09:45:32 | MSG | failsafe | GCS Failsafe |
| 198 | 2026-09-13 09:45:32 | MODE | failsafe | → LAND (9), neden GCS_FAILSAFE(5) |
| 201 | 2026-09-13 09:45:35 | MSG | failsafe | GCS Failsafe Cleared |
| 201 | 2026-09-13 09:45:35 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 206 | 2026-09-13 09:45:40 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 206 | 2026-09-13 09:45:40 | MSG | failsafe | GCS Failsafe |
| 209.6 | 2026-09-13 09:45:44 | MSG | failsafe | GCS Failsafe Cleared |
| 209.6 | 2026-09-13 09:45:44 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 209.8 | 2026-09-13 09:45:44 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 210.6 | 2026-09-13 09:45:45 | EV | ev | LAND_COMPLETE(18) |
| 211.2 | 2026-09-13 09:45:45 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 211.2 | 2026-09-13 09:45:45 | EV | arm | DISARMED(11) |
| 211.2 | 2026-09-13 09:45:45 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 217.6 | 2026-09-13 09:45:52 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 217.6 | 2026-09-13 09:45:52 | MSG | failsafe | GCS Failsafe |
| 244.9 | 2026-09-13 09:46:19 | MSG | failsafe | GCS Failsafe Cleared |
| 244.9 | 2026-09-13 09:46:19 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 254.4 | 2026-09-13 09:46:28 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 259.4 | 2026-09-13 09:46:33 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 259.4 | 2026-09-13 09:46:33 | EV | arm | ARMED(10) |
| 259.4 | 2026-09-13 09:46:33 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 259.4 | 2026-09-13 09:46:33 | EV | ev | AUTO_ARMED(15) |
| 261.4 | 2026-09-13 09:46:35 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 264.2 | 2026-09-13 09:46:38 | EV | ev | NOT_LANDED(28) |
| 266.7 | 2026-09-13 09:46:41 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 266.7 | 2026-09-13 09:46:41 | EV | ekf | EKF_YAW_RESET(62) |
| 266.7 | 2026-09-13 09:46:41 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 288.4 | 2026-09-13 09:47:02 | MSG | failsafe | Battery 1 is low 9.85V used 696 mAh |
| 288.4 | 2026-09-13 09:47:02 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) |
| 288.4 | 2026-09-13 09:47:02 | MSG | failsafe | Battery Failsafe |
| 288.4 | 2026-09-13 09:47:02 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) |
| 303.7 | 2026-09-13 09:47:18 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 304.5 | 2026-09-13 09:47:18 | EV | ev | LAND_COMPLETE(18) |
| 305 | 2026-09-13 09:47:19 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 305 | 2026-09-13 09:47:19 | EV | arm | DISARMED(11) |
| 305 | 2026-09-13 09:47:19 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 306.5 | 2026-09-13 09:47:20 | MSG | prearm | PreArm: Battery failsafe |
| 310 | 2026-09-13 09:47:24 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 310 | 2026-09-13 09:47:24 | MSG | failsafe | GCS Failsafe |
| 337.5 | 2026-09-13 09:47:51 | MSG | prearm | PreArm: GCS failsafe on |
| 337.5 | 2026-09-13 09:47:51 | MSG | prearm | PreArm: Battery failsafe |
| 368.5 | 2026-09-13 09:48:22 | MSG | prearm | PreArm: GCS failsafe on |
| 368.5 | 2026-09-13 09:48:22 | MSG | prearm | PreArm: Battery failsafe |
| 399.5 | 2026-09-13 09:48:53 | MSG | prearm | PreArm: GCS failsafe on |
| 399.5 | 2026-09-13 09:48:53 | MSG | prearm | PreArm: Battery failsafe |
| 424.8 | 2026-09-13 09:49:19 | MSG | failsafe | GCS Failsafe Cleared |
| 424.8 | 2026-09-13 09:49:19 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 425.7 | 2026-09-13 09:49:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 425.7 | 2026-09-13 09:49:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 425.7 | 2026-09-13 09:49:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 427 | 2026-09-13 09:49:21 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 427 | 2026-09-13 09:49:21 | MSG | banner | ChibiOS: 6a85082c |
| 427 | 2026-09-13 09:49:21 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 427 | 2026-09-13 09:49:21 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 427 | 2026-09-13 09:49:21 | MSG | banner | RCOut: PWM:1-16 |
| 427 | 2026-09-13 09:49:21 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 427 | 2026-09-13 09:49:21 | MSG | banner | Frame: QUAD/X |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | ChibiOS: 6a85082c |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | RCOut: PWM:1-16 |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 427.4 | 2026-09-13 09:49:21 | MSG | banner | Frame: QUAD/X |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | ChibiOS: 6a85082c |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | RCOut: PWM:1-16 |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 427.6 | 2026-09-13 09:49:22 | MSG | banner | Frame: QUAD/X |
| 430.5 | 2026-09-13 09:49:24 | MSG | prearm | PreArm: Battery failsafe |
| 461.5 | 2026-09-13 09:49:55 | MSG | prearm | PreArm: Battery failsafe |
| 492.5 | 2026-09-13 09:50:26 | MSG | prearm | PreArm: Compass calibrated requires reboot |
| 492.5 | 2026-09-13 09:50:26 | MSG | prearm | PreArm: Battery failsafe |
| 497.8 | 2026-09-13 09:50:32 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 497.8 | 2026-09-13 09:50:32 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 497.8 | 2026-09-13 09:50:32 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 499 | 2026-09-13 09:50:33 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 499 | 2026-09-13 09:50:33 | MSG | banner | ChibiOS: 6a85082c |
| 499 | 2026-09-13 09:50:33 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 499 | 2026-09-13 09:50:33 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 499 | 2026-09-13 09:50:33 | MSG | banner | RCOut: PWM:1-16 |
| 499 | 2026-09-13 09:50:33 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 499 | 2026-09-13 09:50:33 | MSG | banner | Frame: QUAD/X |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | ChibiOS: 6a85082c |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | RCOut: PWM:1-16 |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 499.4 | 2026-09-13 09:50:33 | MSG | banner | Frame: QUAD/X |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | ChibiOS: 6a85082c |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | RCOut: PWM:1-16 |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 499.6 | 2026-09-13 09:50:34 | MSG | banner | Frame: QUAD/X |
| 523.5 | 2026-09-13 09:50:57 | MSG | prearm | PreArm: Compass calibration running |
| 523.5 | 2026-09-13 09:50:57 | MSG | prearm | PreArm: Battery failsafe |
| 550.1 | 2026-09-13 09:51:24 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 550.1 | 2026-09-13 09:51:24 | MSG | failsafe | GCS Failsafe |
| 550.4 | 2026-09-13 09:51:24 | MSG | failsafe | GCS Failsafe Cleared |
| 550.4 | 2026-09-13 09:51:24 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 554.5 | 2026-09-13 09:51:28 | MSG | prearm | PreArm: Compass calibration running |
| 554.5 | 2026-09-13 09:51:28 | MSG | prearm | PreArm: Battery failsafe |
| 565.9 | 2026-09-13 09:51:40 | MSG | compass | Mag(1) good orientation: 0 13.7 |
| 585.5 | 2026-09-13 09:51:59 | MSG | prearm | PreArm: Compass calibration running |
| 585.5 | 2026-09-13 09:51:59 | MSG | prearm | PreArm: Battery failsafe |
| 616.5 | 2026-09-13 09:52:30 | MSG | prearm | PreArm: Compass calibration running |
| 616.5 | 2026-09-13 09:52:30 | MSG | prearm | PreArm: Battery failsafe |
| 634.6 | 2026-09-13 09:52:49 | MSG | compass | Mag(0) good orientation: 6 18.8 |
| 647.5 | 2026-09-13 09:53:01 | MSG | prearm | PreArm: Compass calibrated requires reboot |
| 647.5 | 2026-09-13 09:53:01 | MSG | prearm | PreArm: Battery failsafe |

### #22 · BOOT 121 · `2026-09-13 09-53-45.bin` · 2026-09-13 09:53:44 · 149.0 s · 3S/11.3 V · beyan A · uçuş 1/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 38 | 2026-09-13 09:53:44 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 38 | 2026-09-13 09:53:44 | MSG | banner | ChibiOS: 6a85082c |
| 38 | 2026-09-13 09:53:44 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 38 | 2026-09-13 09:53:44 | MSG | banner | Param space used: 907/5376 |
| 38 | 2026-09-13 09:53:44 | MSG | banner | RC Protocol: IBUS |
| 38 | 2026-09-13 09:53:44 | MSG | banner | RCOut: PWM:1-16 |
| 38 | 2026-09-13 09:53:44 | MSG | banner | New mission |
| 38 | 2026-09-13 09:53:44 | MSG | banner | New rally |
| 38 | 2026-09-13 09:53:44 | MSG | banner | New fence |
| 38 | 2026-09-13 09:53:44 | MSG | banner | Frame: QUAD/X |
| 38 | 2026-09-13 09:53:44 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 39.2 | 2026-09-13 09:53:45 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 39.5 | 2026-09-13 09:53:45 | MSG | arm_ret | Arm: Accels inconsistent |
| 39.5 | 2026-09-13 09:53:45 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 39.5 | 2026-09-13 09:53:45 | MSG | arm_ret | Arm: Fence requires position |
| 41.1 | 2026-09-13 09:53:47 | MSG | arm_ret | Arm: Accels inconsistent |
| 41.1 | 2026-09-13 09:53:47 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 41.1 | 2026-09-13 09:53:47 | MSG | arm_ret | Arm: Fence requires position |
| 49.3 | 2026-09-13 09:53:55 | MSG | ekf | EKF3 IMU1 origin set |
| 49.3 | 2026-09-13 09:53:55 | EV | ev | SET_HOME(25) |
| 49.3 | 2026-09-13 09:53:55 | MSG | diger | Field Elevation Set: 100m |
| 49.5 | 2026-09-13 09:53:55 | MSG | ekf | EKF3 IMU0 origin set |
| 54 | 2026-09-13 09:54:00 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 81.4 | 2026-09-13 09:54:27 | MSG | failsafe | GCS Failsafe Cleared |
| 81.4 | 2026-09-13 09:54:27 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 86.5 | 2026-09-13 09:54:32 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 86.5 | 2026-09-13 09:54:32 | EV | arm | ARMED(10) |
| 86.5 | 2026-09-13 09:54:32 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 88.5 | 2026-09-13 09:54:34 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 89.7 | 2026-09-13 09:54:36 | EV | ev | AUTO_ARMED(15) |
| 94.3 | 2026-09-13 09:54:40 | EV | ev | NOT_LANDED(28) |
| 101.3 | 2026-09-13 09:54:47 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 101.3 | 2026-09-13 09:54:47 | EV | ekf | EKF_YAW_RESET(62) |
| 101.9 | 2026-09-13 09:54:48 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 108.9 | 2026-09-13 09:54:55 | MSG | failsafe | Battery 1 is low 9.78V used 133 mAh |
| 108.9 | 2026-09-13 09:54:55 | ERR | failsafe | FAILSAFE_BATT(6) / LOW(1) |
| 108.9 | 2026-09-13 09:54:55 | MSG | failsafe | Battery Failsafe |
| 108.9 | 2026-09-13 09:54:55 | MODE | failsafe | → LAND (9), neden BATTERY_FAILSAFE(4) |
| 108.9 | 2026-09-13 09:54:55 | EV | ev | LAND_REPO_ACTIVE(73) |
| 122.4 | 2026-09-13 09:55:08 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 123.2 | 2026-09-13 09:55:09 | EV | ev | LAND_COMPLETE(18) |
| 123.7 | 2026-09-13 09:55:10 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 123.7 | 2026-09-13 09:55:10 | EV | arm | DISARMED(11) |
| 123.7 | 2026-09-13 09:55:10 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 124.9 | 2026-09-13 09:55:11 | MSG | prearm | PreArm: Battery failsafe |
| 155.9 | 2026-09-13 09:55:42 | MSG | prearm | PreArm: Battery failsafe |
| 186.9 | 2026-09-13 09:56:13 | MSG | prearm | PreArm: Battery failsafe |

### #23 · BOOT 122 · `2026-09-13 09-59-30.bin` · 2026-09-13 09:59:29 · 1190.9 s · 3S/11.55 V · beyan A · uçuş 6/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | ChibiOS: 6a85082c |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | Param space used: 907/5376 |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | RC Protocol: IBUS |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | RCOut: PWM:1-16 |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | New mission |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | New rally |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | New fence |
| 17.6 | 2026-09-13 09:59:29 | MSG | banner | Frame: QUAD/X |
| 17.6 | 2026-09-13 09:59:29 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 17.6 | 2026-09-13 09:59:29 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 21.1 | 2026-09-13 09:59:33 | MSG | ekf | EKF3 IMU0 origin set |
| 21.1 | 2026-09-13 09:59:33 | MSG | ekf | EKF3 IMU1 origin set |
| 21.1 | 2026-09-13 09:59:33 | EV | ev | SET_HOME(25) |
| 21.2 | 2026-09-13 09:59:33 | MSG | diger | Field Elevation Set: 99m |
| 21.9 | 2026-09-13 09:59:34 | MSG | arm_ret | Arm: Gyros inconsistent |
| 21.9 | 2026-09-13 09:59:34 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 21.9 | 2026-09-13 09:59:34 | MSG | gps | GPS 1: u-blox solution rate configuration 0x3C8 |
| 23.7 | 2026-09-13 09:59:35 | MSG | arm_ret | Arm: Gyros inconsistent |
| 23.7 | 2026-09-13 09:59:35 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 23.7 | 2026-09-13 09:59:35 | MSG | gps | GPS 1: u-blox solution rate configuration 0x308 |
| 24.8 | 2026-09-13 09:59:37 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 24.8 | 2026-09-13 09:59:37 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 25.5 | 2026-09-13 09:59:37 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.5 | 2026-09-13 09:59:42 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.5 | 2026-09-13 09:59:42 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 48.1 | 2026-09-13 10:00:00 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 50.1 | 2026-09-13 10:00:02 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 51.6 | 2026-09-13 10:00:03 | EV | ev | AUTO_ARMED(15) |
| 51.8 | 2026-09-13 10:00:04 | EV | ev | NOT_LANDED(28) |
| 53 | 2026-09-13 10:00:05 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 53.4 | 2026-09-13 10:00:05 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 54.1 | 2026-09-13 10:00:06 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 59.5 | 2026-09-13 10:00:11 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 59.5 | 2026-09-13 10:00:11 | EV | ekf | EKF_YAW_RESET(62) |
| 59.6 | 2026-09-13 10:00:11 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 72.9 | 2026-09-13 10:00:25 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 82.5 | 2026-09-13 10:00:34 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 83.3 | 2026-09-13 10:00:35 | EV | ev | LAND_COMPLETE(18) |
| 83.8 | 2026-09-13 10:00:36 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 83.8 | 2026-09-13 10:00:36 | EV | arm | DISARMED(11) |
| 83.8 | 2026-09-13 10:00:36 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 222.2 | 2026-09-13 10:02:54 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 222.2 | 2026-09-13 10:02:54 | MSG | failsafe | GCS Failsafe |
| 229.9 | 2026-09-13 10:03:02 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 230.1 | 2026-09-13 10:03:02 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 232 | 2026-09-13 10:03:04 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 238.2 | 2026-09-13 10:03:10 | MSG | failsafe | GCS Failsafe Cleared |
| 238.2 | 2026-09-13 10:03:10 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 239.9 | 2026-09-13 10:03:12 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 240.5 | 2026-09-13 10:03:12 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 240.5 | 2026-09-13 10:03:12 | EV | arm | ARMED(10) |
| 240.5 | 2026-09-13 10:03:12 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 241.9 | 2026-09-13 10:03:14 | EV | ev | AUTO_ARMED(15) |
| 242.5 | 2026-09-13 10:03:14 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 243.6 | 2026-09-13 10:03:15 | EV | ev | NOT_LANDED(28) |
| 246 | 2026-09-13 10:03:18 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 246 | 2026-09-13 10:03:18 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 246 | 2026-09-13 10:03:18 | EV | ekf | EKF_YAW_RESET(62) |
| 280 | 2026-09-13 10:03:52 | MODE | kip | → LAND (9), neden GCS_COMMAND(2) |
| 280 | 2026-09-13 10:03:52 | EV | ev | LAND_REPO_ACTIVE(73) |
| 296.4 | 2026-09-13 10:04:08 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 297.2 | 2026-09-13 10:04:09 | EV | ev | LAND_COMPLETE(18) |
| 297.7 | 2026-09-13 10:04:10 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 297.7 | 2026-09-13 10:04:10 | EV | arm | DISARMED(11) |
| 297.7 | 2026-09-13 10:04:10 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 297.8 | 2026-09-13 10:04:10 | MSG | arm_ret | Arm: LAND mode not armable |
| 301.7 | 2026-09-13 10:04:14 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 301.7 | 2026-09-13 10:04:14 | MSG | failsafe | GCS Failsafe |
| 309.5 | 2026-09-13 10:04:21 | MSG | prearm | PreArm: GCS failsafe on |
| 340.5 | 2026-09-13 10:04:52 | MSG | prearm | PreArm: GCS failsafe on |
| 369.2 | 2026-09-13 10:05:21 | MSG | failsafe | GCS Failsafe Cleared |
| 369.2 | 2026-09-13 10:05:21 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 371 | 2026-09-13 10:05:23 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 371.2 | 2026-09-13 10:05:23 | ARM | arm | ARM yöntem MAVLINK(1) forced=0 checks=1 |
| 371.2 | 2026-09-13 10:05:23 | EV | arm | ARMED(10) |
| 371.2 | 2026-09-13 10:05:23 | MODE | kip | → GUIDED (4), neden GCS_COMMAND(2) |
| 371.2 | 2026-09-13 10:05:23 | EV | ev | AUTO_ARMED(15) |
| 373.2 | 2026-09-13 10:05:25 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 374.2 | 2026-09-13 10:05:26 | EV | ev | NOT_LANDED(28) |
| 406.4 | 2026-09-13 10:05:58 | MODE | kip | → LAND (9), neden GCS_COMMAND(2) |
| 406.4 | 2026-09-13 10:05:58 | EV | ev | LAND_REPO_ACTIVE(73) |
| 409.9 | 2026-09-13 10:06:02 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 410.7 | 2026-09-13 10:06:03 | EV | ev | LAND_COMPLETE(18) |
| 411.2 | 2026-09-13 10:06:03 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 411.2 | 2026-09-13 10:06:03 | EV | arm | DISARMED(11) |
| 411.2 | 2026-09-13 10:06:03 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 416.1 | 2026-09-13 10:06:08 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 416.1 | 2026-09-13 10:06:08 | MSG | failsafe | GCS Failsafe |
| 426.1 | 2026-09-13 10:06:18 | MSG | failsafe | GCS Failsafe Cleared |
| 426.1 | 2026-09-13 10:06:18 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 427.7 | 2026-09-13 10:06:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 427.7 | 2026-09-13 10:06:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 427.7 | 2026-09-13 10:06:20 | MSG | banner | GCS:Mission Planner 1.3.83 |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | ChibiOS: 6a85082c |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | RCOut: PWM:1-16 |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 428.9 | 2026-09-13 10:06:21 | MSG | banner | Frame: QUAD/X |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | ChibiOS: 6a85082c |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | RCOut: PWM:1-16 |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 429.3 | 2026-09-13 10:06:21 | MSG | banner | Frame: QUAD/X |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | ChibiOS: 6a85082c |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | IOMCU: 410 2003 411FC231 |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | RCOut: PWM:1-16 |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | IMU0: fast sampling enabled 2.0kHz |
| 429.7 | 2026-09-13 10:06:22 | MSG | banner | Frame: QUAD/X |
| 702.7 | 2026-09-13 10:10:55 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 705.7 | 2026-09-13 10:10:57 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 705.7 | 2026-09-13 10:10:57 | EV | arm | ARMED(10) |
| 705.7 | 2026-09-13 10:10:57 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 706.2 | 2026-09-13 10:10:58 | EV | ev | AUTO_ARMED(15) |
| 707.7 | 2026-09-13 10:11:00 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 709.5 | 2026-09-13 10:11:01 | EV | ev | AUTO_ARMED(15) |
| 709.8 | 2026-09-13 10:11:02 | EV | ev | NOT_LANDED(28) |
| 711.5 | 2026-09-13 10:11:03 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 712.3 | 2026-09-13 10:11:04 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 712.3 | 2026-09-13 10:11:04 | EV | ev | LAND_COMPLETE(18) |
| 712.4 | 2026-09-13 10:11:04 | EV | ev | AUTO_ARMED(15) |
| 714.6 | 2026-09-13 10:11:06 | EV | ev | NOT_LANDED(28) |
| 722.9 | 2026-09-13 10:11:15 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 722.9 | 2026-09-13 10:11:15 | EV | ekf | EKF_YAW_RESET(62) |
| 725.5 | 2026-09-13 10:11:17 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 750.6 | 2026-09-13 10:11:42 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 755.7 | 2026-09-13 10:11:47 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 756 | 2026-09-13 10:11:48 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 756 | 2026-09-13 10:11:48 | EV | arm | DISARMED(11) |
| 756 | 2026-09-13 10:11:48 | EV | ev | LAND_COMPLETE(18) |
| 756 | 2026-09-13 10:11:48 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 801.3 | 2026-09-13 10:12:33 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 802.3 | 2026-09-13 10:12:34 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 803.7 | 2026-09-13 10:12:36 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 823.9 | 2026-09-13 10:12:56 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 825.8 | 2026-09-13 10:12:58 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 825.8 | 2026-09-13 10:12:58 | EV | arm | ARMED(10) |
| 825.8 | 2026-09-13 10:12:58 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 825.8 | 2026-09-13 10:12:58 | EV | ev | AUTO_ARMED(15) |
| 827.8 | 2026-09-13 10:13:00 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 829.3 | 2026-09-13 10:13:01 | EV | ev | NOT_LANDED(28) |
| 839.3 | 2026-09-13 10:13:11 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 839.3 | 2026-09-13 10:13:11 | EV | ekf | EKF_YAW_RESET(62) |
| 840.1 | 2026-09-13 10:13:12 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 869 | 2026-09-13 10:13:41 | MSG | ekf | EKF3 lane switch 1 |
| 869 | 2026-09-13 10:13:41 | EV | ekf | EKF_YAW_RESET(62) |
| 869 | 2026-09-13 10:13:41 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 1(1) |
| 869 | 2026-09-13 10:13:41 | MSG | ekf | EKF primary changed:1 |
| 870.4 | 2026-09-13 10:13:42 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 872.1 | 2026-09-13 10:13:44 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 872.1 | 2026-09-13 10:13:44 | EV | arm | DISARMED(11) |
| 872.1 | 2026-09-13 10:13:44 | EV | ev | LAND_COMPLETE(18) |
| 872.1 | 2026-09-13 10:13:44 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 872.1 | 2026-09-13 10:13:44 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 872.1 | 2026-09-13 10:13:44 | ERR | ekf | EKF_PRIMARY(24) / birincil EKF cekirdegi -> 0(0) |
| 872.1 | 2026-09-13 10:13:44 | MSG | ekf | EKF primary changed:0 |
| 873.5 | 2026-09-13 10:13:45 | MSG | prearm | PreArm: Check mag field (xy diff:156>100) |
| 904.5 | 2026-09-13 10:14:16 | MSG | prearm | PreArm: Check mag field (xy diff:114>100) |
| 935.5 | 2026-09-13 10:14:47 | MSG | prearm | PreArm: Check mag field (xy diff:111>100) |
| 969.4 | 2026-09-13 10:15:21 | MSG | arm_ret | Arm: LAND mode not armable |
| 970.4 | 2026-09-13 10:15:22 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 978.5 | 2026-09-13 10:15:30 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 978.5 | 2026-09-13 10:15:30 | EV | arm | ARMED(10) |
| 978.5 | 2026-09-13 10:15:30 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 980.5 | 2026-09-13 10:15:32 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 981.6 | 2026-09-13 10:15:33 | EV | ev | AUTO_ARMED(15) |
| 985 | 2026-09-13 10:15:37 | EV | ev | NOT_LANDED(28) |
| 991.4 | 2026-09-13 10:15:43 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 991.4 | 2026-09-13 10:15:43 | EV | ekf | EKF_YAW_RESET(62) |
| 991.9 | 2026-09-13 10:15:44 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 997.5 | 2026-09-13 10:15:49 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 998 | 2026-09-13 10:15:50 | EV | ev | LAND_REPO_ACTIVE(73) |
| 1006.3 | 2026-09-13 10:15:58 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 1007.1 | 2026-09-13 10:15:59 | EV | ev | LAND_COMPLETE(18) |
| 1007.6 | 2026-09-13 10:15:59 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 1007.6 | 2026-09-13 10:15:59 | EV | arm | DISARMED(11) |
| 1007.6 | 2026-09-13 10:15:59 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 1010.2 | 2026-09-13 10:16:02 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 1089.4 | 2026-09-13 10:17:21 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 1089.4 | 2026-09-13 10:17:21 | MSG | failsafe | GCS Failsafe |
| 1090.5 | 2026-09-13 10:17:22 | MSG | prearm | PreArm: GCS failsafe on |
| 1121.5 | 2026-09-13 10:17:53 | MSG | prearm | PreArm: GCS failsafe on |
| 1152.5 | 2026-09-13 10:18:24 | MSG | prearm | PreArm: GCS failsafe on |
| 1183.5 | 2026-09-13 10:18:55 | MSG | prearm | PreArm: GCS failsafe on |
| 1193.5 | 2026-09-13 10:19:05 | MSG | prearm | PreArm: GCS failsafe on |
| 1198.5 | 2026-09-13 10:19:10 | MSG | prearm | PreArm: GCS failsafe on |
| 1200.9 | 2026-09-13 10:19:13 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 1200.9 | 2026-09-13 10:19:13 | MSG | gps | GPS Glitch or Compass error |
| 1203.5 | 2026-09-13 10:19:15 | MSG | prearm | PreArm: GCS failsafe on |
| 1203.5 | 2026-09-13 10:19:15 | MSG | prearm | PreArm: GPS glitching |

### #24 · BOOT 132 · `2026-09-14 19-43-06.bin` · 2026-09-14 19:43:06 · 160.9 s · 3S/12.44 V · beyan C · uçuş 2/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | ChibiOS: 6a85082c |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | Param space used: 907/5376 |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | RC Protocol: IBUS |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | RCOut: PWM:1-16 |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | New mission |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | New rally |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | New fence |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | Frame: QUAD/X |
| 55.4 | 2026-09-14 19:43:06 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 55.4 | 2026-09-14 19:43:06 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 55.4 | 2026-09-14 19:43:06 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 55.5 | 2026-09-14 19:43:06 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 55.5 | 2026-09-14 19:43:06 | MSG | arm_ret | Arm: Fence requires position |
| 56.4 | 2026-09-14 19:43:07 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 56.4 | 2026-09-14 19:43:07 | MSG | arm_ret | Arm: Fence requires position |
| 61.2 | 2026-09-14 19:43:11 | MSG | prearm | PreArm: AHRS: waiting for home |
| 61.2 | 2026-09-14 19:43:11 | MSG | prearm | PreArm: Fence requires position |
| 97.3 | 2026-09-14 19:43:47 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 99.3 | 2026-09-14 19:43:49 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 102.9 | 2026-09-14 19:43:53 | EV | ev | AUTO_ARMED(15) |
| 106 | 2026-09-14 19:43:56 | EV | ev | NOT_LANDED(28) |
| 131.8 | 2026-09-14 19:44:22 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 132.6 | 2026-09-14 19:44:23 | EV | ev | LAND_COMPLETE(18) |
| 132.8 | 2026-09-14 19:44:23 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 132.8 | 2026-09-14 19:44:23 | EV | arm | DISARMED(11) |
| 132.8 | 2026-09-14 19:44:23 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 148.3 | 2026-09-14 19:44:38 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 148.3 | 2026-09-14 19:44:38 | EV | arm | ARMED(10) |
| 148.3 | 2026-09-14 19:44:38 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 150.3 | 2026-09-14 19:44:40 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 152.3 | 2026-09-14 19:44:42 | EV | ev | AUTO_ARMED(15) |
| 154.9 | 2026-09-14 19:44:45 | EV | ev | NOT_LANDED(28) |
| 159 | 2026-09-14 19:44:49 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 159 | 2026-09-14 19:44:49 | EV | ekf | EKF_YAW_RESET(62) |
| 159.5 | 2026-09-14 19:44:50 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 184.4 | 2026-09-14 19:45:15 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 185.2 | 2026-09-14 19:45:15 | EV | ev | LAND_COMPLETE(18) |
| 185.3 | 2026-09-14 19:45:15 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 185.3 | 2026-09-14 19:45:15 | EV | arm | DISARMED(11) |
| 185.3 | 2026-09-14 19:45:15 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 197.7 | 2026-09-14 19:45:28 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 197.7 | 2026-09-14 19:45:28 | MSG | gps | GPS Glitch or Compass error |
| 199.2 | 2026-09-14 19:45:29 | MSG | prearm | PreArm: GPS glitching |
| 206.9 | 2026-09-14 19:45:37 | ERR | diger | RADIO(2) / LATE_FRAME (RC cercevesi gec)(2) |
| 206.9 | 2026-09-14 19:45:37 | ERR | failsafe | FAILSAFE_RADIO(5) / TETIKLENDI(1) |
| 206.9 | 2026-09-14 19:45:37 | MSG | failsafe | Radio Failsafe - Disarming |

### #25 · BOOT 134 · `2026-09-14 21-10-34.bin` · 2026-09-14 21:10:33 · 159.9 s · 3S/12.09 V · beyan C · uçuş 1/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | ChibiOS: 6a85082c |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | Param space used: 907/5376 |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | RC Protocol: IBUS |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | RCOut: PWM:1-16 |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | New mission |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | New rally |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | New fence |
| 25.4 | 2026-09-14 21:10:33 | MSG | banner | Frame: QUAD/X |
| 25.4 | 2026-09-14 21:10:33 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 25.4 | 2026-09-14 21:10:33 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 28.4 | 2026-09-14 21:10:36 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.2 | 2026-09-14 21:10:38 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-14 21:10:38 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 92.2 | 2026-09-14 21:11:40 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 93.5 | 2026-09-14 21:11:42 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 93.5 | 2026-09-14 21:11:42 | EV | arm | DISARMED(11) |
| 103.9 | 2026-09-14 21:11:52 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 103.9 | 2026-09-14 21:11:52 | EV | arm | ARMED(10) |
| 103.9 | 2026-09-14 21:11:52 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 105.4 | 2026-09-14 21:11:53 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 105.9 | 2026-09-14 21:11:54 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 107.4 | 2026-09-14 21:11:55 | EV | ev | AUTO_ARMED(15) |
| 108.8 | 2026-09-14 21:11:57 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 108.8 | 2026-09-14 21:11:57 | EV | arm | DISARMED(11) |
| 108.8 | 2026-09-14 21:11:57 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 115.8 | 2026-09-14 21:12:04 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 115.8 | 2026-09-14 21:12:04 | EV | arm | ARMED(10) |
| 115.8 | 2026-09-14 21:12:04 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 117.8 | 2026-09-14 21:12:06 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 118.3 | 2026-09-14 21:12:06 | EV | ev | AUTO_ARMED(15) |
| 120.8 | 2026-09-14 21:12:09 | EV | ev | NOT_LANDED(28) |
| 125.9 | 2026-09-14 21:12:14 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 125.9 | 2026-09-14 21:12:14 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 125.9 | 2026-09-14 21:12:14 | EV | ekf | EKF_YAW_RESET(62) |
| 142.4 | 2026-09-14 21:12:30 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 150.6 | 2026-09-14 21:12:39 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 151.4 | 2026-09-14 21:12:39 | EV | ev | LAND_COMPLETE(18) |
| 151.9 | 2026-09-14 21:12:40 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 151.9 | 2026-09-14 21:12:40 | EV | arm | DISARMED(11) |
| 151.9 | 2026-09-14 21:12:40 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 161.8 | 2026-09-14 21:12:50 | ERR | gps | GPS(11) / GPS_GLITCH(2) |
| 161.8 | 2026-09-14 21:12:50 | MSG | gps | GPS Glitch or Compass error |
| 163.2 | 2026-09-14 21:12:51 | MSG | prearm | PreArm: GPS glitching |
| 169.5 | 2026-09-14 21:12:58 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 178.7 | 2026-09-14 21:13:07 | ERR | ekf | EKFCHECK(16) / BAD_VARIANCE(2) |
| 178.7 | 2026-09-14 21:13:07 | MSG | ekf | EKF variance |
| 178.7 | 2026-09-14 21:13:07 | ERR | failsafe | FAILSAFE_EKFINAV(17) / TETIKLENDI(1) |
| 182.8 | 2026-09-14 21:13:11 | ERR | ekf | EKFCHECK(16) / temizlendi(0) |
| 182.8 | 2026-09-14 21:13:11 | ERR | failsafe | FAILSAFE_EKFINAV(17) / temizlendi(0) |

### #26 · BOOT 138 · `2026-09-15 11-14-33.bin` · 2026-09-15 11:14:32 · 204.7 s · 4S/16.29 V · beyan D · uçuş 1/kısa 0

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | ChibiOS: 6a85082c |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | Param space used: 907/5376 |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | RC Protocol: IBUS |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | RCOut: PWM:1-16 |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | New mission |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | New rally |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | New fence |
| 16.6 | 2026-09-15 11:14:32 | MSG | banner | Frame: QUAD/X |
| 16.6 | 2026-09-15 11:14:32 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 16.6 | 2026-09-15 11:14:32 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 17.6 | 2026-09-15 11:14:33 | MSG | arm_ret | Arm: Gyros inconsistent |
| 17.6 | 2026-09-15 11:14:33 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 17.6 | 2026-09-15 11:14:33 | MSG | arm_ret | Arm: Fence requires position |
| 19.4 | 2026-09-15 11:14:35 | MSG | arm_ret | Arm: Gyros inconsistent |
| 19.4 | 2026-09-15 11:14:35 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 19.4 | 2026-09-15 11:14:35 | MSG | arm_ret | Arm: Fence requires position |
| 23 | 2026-09-15 11:14:39 | MSG | ekf | EKF3 IMU1 origin set |
| 23 | 2026-09-15 11:14:39 | EV | ev | SET_HOME(25) |
| 23 | 2026-09-15 11:14:39 | MSG | ekf | EKF3 IMU0 origin set |
| 23.1 | 2026-09-15 11:14:39 | MSG | diger | Field Elevation Set: 90m |
| 27.6 | 2026-09-15 11:14:43 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 30.5 | 2026-09-15 11:14:46 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.5 | 2026-09-15 11:14:46 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 86.7 | 2026-09-15 11:15:43 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 88.7 | 2026-09-15 11:15:45 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 92.8 | 2026-09-15 11:15:49 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 95.5 | 2026-09-15 11:15:51 | EV | ev | AUTO_ARMED(15) |
| 101.7 | 2026-09-15 11:15:58 | EV | ev | NOT_LANDED(28) |
| 114.9 | 2026-09-15 11:16:11 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 114.9 | 2026-09-15 11:16:11 | EV | ekf | EKF_YAW_RESET(62) |
| 115.1 | 2026-09-15 11:16:11 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 135.1 | 2026-09-15 11:16:31 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 136.5 | 2026-09-15 11:16:32 | EV | ev | LAND_REPO_ACTIVE(73) |
| 145.4 | 2026-09-15 11:16:41 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 146.2 | 2026-09-15 11:16:42 | EV | ev | LAND_COMPLETE(18) |
| 146.7 | 2026-09-15 11:16:43 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 146.7 | 2026-09-15 11:16:43 | EV | arm | DISARMED(11) |
| 146.7 | 2026-09-15 11:16:43 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 153.2 | 2026-09-15 11:16:49 | MSG | arm_ret | Arm: LAND mode not armable |
| 154.6 | 2026-09-15 11:16:50 | MSG | arm_ret | Arm: LAND mode not armable |
| 162.6 | 2026-09-15 11:16:58 | MSG | arm_ret | Arm: High GPS HDOP |
| 164.2 | 2026-09-15 11:17:00 | MSG | arm_ret | Arm: High GPS HDOP |
| 165.5 | 2026-09-15 11:17:01 | MSG | prearm | PreArm: High GPS HDOP |
| 165.7 | 2026-09-15 11:17:02 | MSG | arm_ret | Arm: High GPS HDOP |
| 170.5 | 2026-09-15 11:17:06 | MSG | prearm | PreArm: High GPS HDOP |
| 172.2 | 2026-09-15 11:17:08 | MSG | arm_ret | Arm: High GPS HDOP |
| 178.5 | 2026-09-15 11:17:14 | MSG | arm_ret | Arm: High GPS HDOP |
| 183.2 | 2026-09-15 11:17:19 | MSG | arm_ret | Arm: LAND mode not armable |
| 184.7 | 2026-09-15 11:17:21 | MSG | arm_ret | Arm: High GPS HDOP |
| 185.5 | 2026-09-15 11:17:21 | MSG | prearm | PreArm: High GPS HDOP |
| 186.3 | 2026-09-15 11:17:22 | MSG | arm_ret | Arm: High GPS HDOP |
| 187.3 | 2026-09-15 11:17:23 | MSG | arm_ret | Arm: High GPS HDOP |
| 195.6 | 2026-09-15 11:17:31 | MSG | arm_ret | Arm: LAND mode not armable |
| 198.1 | 2026-09-15 11:17:34 | MSG | arm_ret | Arm: LAND mode not armable |
| 202.1 | 2026-09-15 11:17:38 | MSG | arm_ret | Arm: LAND mode not armable |
| 206.2 | 2026-09-15 11:17:42 | MSG | arm_ret | Arm: LAND mode not armable |
| 207.4 | 2026-09-15 11:17:43 | MSG | arm_ret | Arm: LAND mode not armable |
| 211.8 | 2026-09-15 11:17:48 | MSG | arm_ret | Arm: LAND mode not armable |
| 216.6 | 2026-09-15 11:17:52 | MSG | arm_ret | Arm: LAND mode not armable |

### #27 · BOOT 139 · `2026-09-15 11-18-16.bin` · 2026-09-15 11:18:16 · 202.0 s · 4S/16.12 V · beyan D · uçuş 2/kısa 1

| t s | saat | tür | sınıf | olay |
|---|---|---|---|---|
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | ArduCopter V4.5.7 (2a3dc4b7) |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | ChibiOS: 6a85082c |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | Pixhawk6C 00440022 35335114 38323631 |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | Param space used: 907/5376 |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | RC Protocol: IBUS |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | RCOut: PWM:1-16 |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | New mission |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | New rally |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | New fence |
| 14.4 | 2026-09-15 11:18:16 | MSG | banner | Frame: QUAD/X |
| 14.4 | 2026-09-15 11:18:16 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 14.4 | 2026-09-15 11:18:16 | MSG | gps | GPS 1: detected as u-blox at 230400 baud |
| 16.1 | 2026-09-15 11:18:18 | MSG | arm_ret | Arm: Gyros inconsistent |
| 16.1 | 2026-09-15 11:18:18 | MSG | arm_ret | Arm: AHRS: waiting for home |
| 16.1 | 2026-09-15 11:18:18 | MSG | arm_ret | Arm: Fence requires position |
| 20.7 | 2026-09-15 11:18:23 | MSG | ekf | EKF3 IMU1 origin set |
| 20.7 | 2026-09-15 11:18:23 | EV | ev | SET_HOME(25) |
| 20.7 | 2026-09-15 11:18:23 | MSG | diger | Field Elevation Set: 106m |
| 20.9 | 2026-09-15 11:18:23 | MSG | ekf | EKF3 IMU0 origin set |
| 22.8 | 2026-09-15 11:18:25 | MSG | arm_ret | Arm: Gyros inconsistent |
| 22.8 | 2026-09-15 11:18:25 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 22.8 | 2026-09-15 11:18:25 | MSG | gps | GPS 1: u-blox solution rate configuration 0x388 |
| 25.4 | 2026-09-15 11:18:27 | MSG | banner | u-blox 1 HW: 000A0000 SW: ROM SPG 5.10 (7b202e) |
| 25.5 | 2026-09-15 11:18:27 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 25.5 | 2026-09-15 11:18:27 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 27.5 | 2026-09-15 11:18:29 | MSG | arm_ret | Arm: GPS 1 still configuring this GPS |
| 27.5 | 2026-09-15 11:18:29 | MSG | gps | GPS 1: u-blox solution rate configuration 0x80208 |
| 30.2 | 2026-09-15 11:18:32 | MSG | prearm | PreArm: GPS 1 still configuring this GPS |
| 30.2 | 2026-09-15 11:18:32 | MSG | gps | GPS 1: u-blox solution rate configuration 0x208 |
| 42.5 | 2026-09-15 11:18:44 | MSG | ekf | EKF3 IMU0 is using GPS |
| 42.5 | 2026-09-15 11:18:44 | MSG | ekf | EKF3 IMU1 is using GPS |
| 49.9 | 2026-09-15 11:18:52 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 51.2 | 2026-09-15 11:18:53 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 51.2 | 2026-09-15 11:18:53 | EV | arm | ARMED(10) |
| 51.2 | 2026-09-15 11:18:53 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 51.3 | 2026-09-15 11:18:53 | EV | ev | AUTO_ARMED(15) |
| 53.2 | 2026-09-15 11:18:55 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 58.1 | 2026-09-15 11:19:00 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 58.1 | 2026-09-15 11:19:00 | EV | arm | DISARMED(11) |
| 58.1 | 2026-09-15 11:19:00 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 63.7 | 2026-09-15 11:19:06 | ERR | failsafe | FAILSAFE_GCS(8) / TETIKLENDI(1) |
| 63.7 | 2026-09-15 11:19:06 | MSG | failsafe | GCS Failsafe |
| 64.1 | 2026-09-15 11:19:06 | MSG | failsafe | GCS Failsafe Cleared |
| 64.1 | 2026-09-15 11:19:06 | ERR | failsafe | FAILSAFE_GCS(8) / temizlendi(0) |
| 64.1 | 2026-09-15 11:19:06 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 64.1 | 2026-09-15 11:19:06 | EV | arm | ARMED(10) |
| 64.1 | 2026-09-15 11:19:06 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 64.2 | 2026-09-15 11:19:06 | EV | ev | AUTO_ARMED(15) |
| 66.1 | 2026-09-15 11:19:08 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 68.4 | 2026-09-15 11:19:10 | EV | ev | NOT_LANDED(28) |
| 71 | 2026-09-15 11:19:13 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 71 | 2026-09-15 11:19:13 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 71 | 2026-09-15 11:19:13 | EV | ekf | EKF_YAW_RESET(62) |
| 86.7 | 2026-09-15 11:19:28 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 89.4 | 2026-09-15 11:19:31 | EV | ev | LAND_REPO_ACTIVE(73) |
| 95.8 | 2026-09-15 11:19:38 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 96.6 | 2026-09-15 11:19:38 | EV | ev | LAND_COMPLETE(18) |
| 97.1 | 2026-09-15 11:19:39 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 97.1 | 2026-09-15 11:19:39 | EV | arm | DISARMED(11) |
| 97.1 | 2026-09-15 11:19:39 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 116.7 | 2026-09-15 11:19:58 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 119.5 | 2026-09-15 11:20:01 | MSG | arm_ret | Arm: Throttle too high |
| 121.7 | 2026-09-15 11:20:04 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 121.7 | 2026-09-15 11:20:04 | EV | arm | ARMED(10) |
| 121.7 | 2026-09-15 11:20:04 | MODE | kip | → STABILIZE (0), neden RC_COMMAND(1) |
| 123.7 | 2026-09-15 11:20:06 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 124.7 | 2026-09-15 11:20:07 | EV | ev | AUTO_ARMED(15) |
| 124.9 | 2026-09-15 11:20:07 | EV | ev | NOT_LANDED(28) |
| 129.8 | 2026-09-15 11:20:12 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 130 | 2026-09-15 11:20:12 | ARM | arm | DISARM yöntem AUXSWITCH(2) forced=0 checks=0 |
| 130 | 2026-09-15 11:20:12 | EV | arm | DISARMED(11) |
| 130 | 2026-09-15 11:20:12 | EV | ev | LAND_COMPLETE(18) |
| 130 | 2026-09-15 11:20:12 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |
| 138.2 | 2026-09-15 11:20:20 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 138.9 | 2026-09-15 11:20:21 | ARM | arm | ARM yöntem AUXSWITCH(2) forced=0 checks=1 |
| 138.9 | 2026-09-15 11:20:21 | EV | arm | ARMED(10) |
| 138.9 | 2026-09-15 11:20:21 | MODE | kip | → LOITER (5), neden RC_COMMAND(1) |
| 140.9 | 2026-09-15 11:20:23 | EV | ev | MOTORS_INTERLOCK_ENABLED(57) |
| 142 | 2026-09-15 11:20:24 | EV | ev | AUTO_ARMED(15) |
| 146.3 | 2026-09-15 11:20:28 | EV | ev | NOT_LANDED(28) |
| 149.2 | 2026-09-15 11:20:31 | MSG | ekf | EKF3 IMU0 MAG0 in-flight yaw alignment complete |
| 149.2 | 2026-09-15 11:20:31 | EV | ekf | EKF_YAW_RESET(62) |
| 149.5 | 2026-09-15 11:20:31 | MSG | ekf | EKF3 IMU1 MAG0 in-flight yaw alignment complete |
| 167.5 | 2026-09-15 11:20:49 | MODE | kip | → LAND (9), neden RC_COMMAND(1) |
| 168.2 | 2026-09-15 11:20:50 | EV | ev | LAND_REPO_ACTIVE(73) |
| 176.6 | 2026-09-15 11:20:58 | EV | ev | LAND_COMPLETE_MAYBE(17) |
| 177.4 | 2026-09-15 11:20:59 | EV | ev | LAND_COMPLETE(18) |
| 177.9 | 2026-09-15 11:21:00 | ARM | arm | DISARM yöntem LANDED(13) forced=0 checks=0 |
| 177.9 | 2026-09-15 11:21:00 | EV | arm | DISARMED(11) |
| 177.9 | 2026-09-15 11:21:00 | EV | ev | MOTORS_INTERLOCK_DISABLED(56) |

## 6. Olay sınıfı × log matrisi

| # | log | arm | arm_ret | banner | compass | diger | ekf | ev | failsafe | gps | kip | kip_red | motor_test | prearm | thrust_loss |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `2026-09-12 16-45-10` | 0 | 3 | 11 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 0 |
| 2 | `1980-01-12 15-45-52` | 0 | 1 | 10 | 0 | 0 | 8 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 0 |
| 3 | `2026-09-12 16-50-10` | 6 | 15 | 11 | 0 | 1 | 11 | 13 | 0 | 2 | 5 | 0 | 0 | 6 | 2 |
| 4 | `2026-09-12 17-15-12` | 18 | 0 | 11 | 0 | 0 | 0 | 22 | 0 | 1 | 5 | 0 | 0 | 1 | 0 |
| 5 | `2026-09-12 17-31-18` | 12 | 2 | 11 | 0 | 0 | 2 | 11 | 0 | 3 | 4 | 0 | 0 | 0 | 0 |
| 6 | `2026-09-12 17-35-39` | 12 | 5 | 11 | 0 | 0 | 2 | 15 | 0 | 7 | 7 | 0 | 0 | 1 | 0 |
| 7 | `2026-09-12 17-42-38` | 4 | 11 | 11 | 0 | 1 | 4 | 7 | 0 | 6 | 5 | 0 | 0 | 1 | 0 |
| 8 | `2026-09-12 17-47-06` | 2 | 0 | 11 | 0 | 0 | 0 | 7 | 0 | 1 | 2 | 0 | 0 | 0 | 0 |
| 9 | `2026-09-12 18-48-07` | 0 | 0 | 11 | 0 | 0 | 0 | 31 | 0 | 1 | 1 | 0 | 29 | 3 | 0 |
| 10 | `2026-09-12 18-59-08` | 4 | 3 | 11 | 0 | 0 | 2 | 6 | 0 | 4 | 4 | 0 | 0 | 0 | 0 |
| 11 | `2026-09-12 19-13-58` | 0 | 11 | 11 | 0 | 0 | 0 | 1 | 0 | 3 | 1 | 0 | 0 | 5 | 0 |
| 12 | `2026-09-12 19-41-52` | 34 | 15 | 11 | 0 | 8 | 8 | 29 | 6 | 13 | 11 | 0 | 0 | 10 | 0 |
| 13 | `2026-09-12 20-51-26` | 12 | 9 | 35 | 0 | 0 | 0 | 16 | 6 | 1 | 11 | 0 | 0 | 45 | 0 |
| 14 | `1980-01-12 20-17-44` | 12 | 14 | 59 | 0 | 1 | 15 | 13 | 4 | 10 | 8 | 0 | 0 | 11 | 0 |
| 15 | `2026-09-12 23-47-27` | 10 | 40 | 11 | 0 | 4 | 2 | 19 | 12 | 28 | 6 | 0 | 0 | 63 | 0 |
| 16 | `2026-09-13 08-34-30` | 6 | 49 | 11 | 0 | 2 | 22 | 10 | 14 | 9 | 8 | 0 | 0 | 124 | 0 |
| 17 | `2026-09-13 08-57-45` | 0 | 13 | 11 | 0 | 0 | 2 | 0 | 0 | 7 | 2 | 0 | 0 | 3 | 0 |
| 18 | `1980-01-06 07-59-23` | 0 | 12 | 11 | 0 | 1 | 4 | 1 | 0 | 4 | 3 | 0 | 0 | 8 | 0 |
| 19 | `1980-01-06 08-07-20` | 6 | 11 | 11 | 0 | 1 | 5 | 10 | 8 | 3 | 7 | 0 | 0 | 7 | 0 |
| 20 | `2026-09-13 09-26-58` | 26 | 17 | 11 | 0 | 1 | 2 | 39 | 0 | 3 | 19 | 2 | 0 | 1 | 0 |
| 21 | `2026-09-13 09-42-26` | 10 | 2 | 59 | 2 | 1 | 11 | 22 | 29 | 3 | 7 | 0 | 0 | 22 | 0 |
| 22 | `2026-09-13 09-53-45` | 4 | 6 | 11 | 0 | 1 | 5 | 8 | 6 | 1 | 2 | 0 | 0 | 3 | 0 |
| 23 | `2026-09-13 09-59-30` | 22 | 7 | 35 | 0 | 1 | 23 | 47 | 14 | 7 | 27 | 0 | 0 | 14 | 0 |
| 24 | `2026-09-14 19-43-06` | 6 | 4 | 11 | 0 | 1 | 3 | 12 | 2 | 3 | 3 | 0 | 0 | 3 | 0 |
| 25 | `2026-09-14 21-10-34` | 10 | 0 | 11 | 0 | 0 | 6 | 9 | 2 | 4 | 7 | 0 | 0 | 2 | 0 |
| 26 | `2026-09-15 11-14-33` | 2 | 24 | 11 | 0 | 1 | 5 | 8 | 0 | 2 | 4 | 0 | 0 | 4 | 0 |
| 27 | `2026-09-15 11-18-16` | 16 | 8 | 11 | 0 | 1 | 10 | 24 | 4 | 5 | 10 | 0 | 0 | 1 | 0 |

## 7. Otomatik bulgular (sayılar yukarıdaki tablolardan)

- `1980-01-12 15-45-52.bin`: BOOTCNT 76; BOOTCNT-komşularıyla parametre farkı 0 / 1; hipotez konumu (65↔68) komşularıyla 20 / 20; hesaplanan saat 2026-09-12 16:45:45 (tutarlı=True).
- `1980-01-12 20-17-44.bin`: BOOTCNT 95; BOOTCNT-komşularıyla parametre farkı 0 / 1; hipotez konumu (65↔68) komşularıyla 20 / 20; hesaplanan saat 2026-09-12 21:17:38 (tutarlı=True).
- `1980-01-06 07-59-23.bin`: BOOTCNT 117; BOOTCNT-komşularıyla parametre farkı 0 / 1; hipotez konumu (65↔68) komşularıyla 17 / 18; hesaplanan saat 2026-09-13 08:59:21 (tutarlı=True).
- `1980-01-06 08-07-20.bin`: BOOTCNT 118; BOOTCNT-komşularıyla parametre farkı 1 / 3; hipotez konumu (65↔68) komşularıyla 17 / 18; hesaplanan saat 2026-09-13 09:07:18 (tutarlı=True).
- `MOT_THST_HOVER` segment sayısı 10: 0.35@#1 → 0.381312@#15 → 0.447916@#16 → 0.472593@#19 → 0.46451@#21 → 0.459637@#22 → 0.532559@#23 → 0.49768@#24 → 0.506167@#25 → 0.501742@#27
- `MOT_THST_HOVER` değişimleri: 14; log içi (öğrenme, DISARM kaydı) 14, loglar arası 0 → #15 LOG_ICI t=1138.8 0.35→0.349373 [OGRENME]; #15 LOG_ICI t=1245.8 0.349373→0.381312 [OGRENME]; #16 LOG_ICI t=207.2 0.381312→0.447916 [OGRENME]; #19 LOG_ICI t=340.9 0.447916→0.472593 [OGRENME]; #21 LOG_ICI t=211.2 0.472593→0.466202 [OGRENME]; #21 LOG_ICI t=305.0 0.466202→0.46451 [OGRENME]; #22 LOG_ICI t=123.7 0.46451→0.459637 [OGRENME]; #23 LOG_ICI t=83.8 0.459637→0.460352 [OGRENME]; #23 LOG_ICI t=756.0 0.460352→0.532062 [OGRENME]; #23 LOG_ICI t=872.1 0.532062→0.532559 [OGRENME]; #24 LOG_ICI t=132.8 0.532559→0.515692 [OGRENME]; #24 LOG_ICI t=185.3 0.515692→0.49768 [OGRENME]; #25 LOG_ICI t=151.9 0.49768→0.506167 [OGRENME]; #27 LOG_ICI t=177.9 0.506167→0.501742 [OGRENME]
- Olay sınıfları: arm=234, arm_ret=282, banner=440, compass=2, diger=26, ekf=152, ev=380, failsafe=107, gps=133, kip=171, kip_red=2, motor_test=29, prearm=340, thrust_loss=2
- Kullanıcı eliyle (KULLANICI+KALIBRASYON+RC_KAL) değişim: 37; parametre bazında: `BATT_VOLT_MULT`×9, `BATT_LOW_VOLT`×6, `BATT_CRT_VOLT`×2, `FS_GCS_ENABLE`×2, `BATT_ARM_VOLT`×2, `BATT_CAPACITY`×2, `COMPASS_OFS2_X`×1, `COMPASS_OFS2_Y`×1, `COMPASS_OFS2_Z`×1, `COMPASS_SCALE2`×1, `COMPASS_OFS_X`×1, `COMPASS_OFS_Y`×1, `COMPASS_OFS_Z`×1, `COMPASS_DIA_X`×1, `COMPASS_DIA_Y`×1, `COMPASS_DIA_Z`×1, `COMPASS_ODI_X`×1, `COMPASS_ODI_Y`×1, `COMPASS_ODI_Z`×1, `COMPASS_SCALE`×1
- Boşluk `2026-09-12 17-47-06` → `2026-09-12 18-48-07`: 5 logsuz açılış, görünmeyen RUNTIME 152 s, görünmeyen FLTTIME 0 s; bu aralıkta kullanıcı değişimi: YOK; MOT_THST_HOVER 0.35 → 0.35
- Boşluk `2026-09-12 23-47-27` → `2026-09-13 08-34-30`: 18 logsuz açılış, görünmeyen RUNTIME 11510 s, görünmeyen FLTTIME 0 s; bu aralıkta kullanıcı değişimi: `BATT_ARM_VOLT` 0→10.5; `BATT_CAPACITY` 3300→6000; MOT_THST_HOVER 0.381312 → 0.381312
- Boşluk `2026-09-13 09-59-30` → `2026-09-14 19-43-06`: 9 logsuz açılış, görünmeyen RUNTIME 25686 s, görünmeyen FLTTIME 0 s; bu aralıkta kullanıcı değişimi: `BATT_CAPACITY` 6000→8000; MOT_THST_HOVER 0.532559 → 0.532559
- Motor testi (`starting motor test`, MP Motor Test): `2026-09-12 18-48-07`×29
- thrust_loss: #3 `2026-09-12 16-50-10` t=383.2 s (2026-09-12 16:56:14) → THRUST_LOSS_CHECK/TETIKLENDI
- thrust_loss: #3 `2026-09-12 16-50-10` t=383.2 s (2026-09-12 16:56:14) → Potential Thrust Loss (3)
- Kritik olay sayıları: ERR EKFCHECK tetik=8, ERR EKF_PRIMARY tetik=2, ERR FAILSAFE_BATT tetik=4, ERR FAILSAFE_EKFINAV tetik=8, ERR FAILSAFE_GCS tetik=15, ERR FAILSAFE_RADIO tetik=5, ERR GPS tetik=18, ERR RADIO tetik=5, ERR THRUST_LOSS_CHECK tetik=1, MODE failsafe→LAND (BATTERY_FAILSAFE)=4, MODE failsafe→LAND (GCS_FAILSAFE)=1, MODE failsafe→LAND (RADIO_FAILSAFE)=2, MSG failsafe=44, MSG kip_red=1, MSG motor_test=29, MSG thrust_loss=1
- `1980-01-12 15-45-52.bin`: A*: kullanici beyaninda acikca yok; yerlesim (12-13 Eylul) + 3S hucre ile turetildi
