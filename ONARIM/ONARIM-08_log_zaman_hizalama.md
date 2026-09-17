# ONARIM-08 — Jetson kaydını Pixhawk loguyla saatten bağımsız hizalama

**Durum:** KAPANDI (yazılım) · canlı Pixhawk'la kayıt **alınmadı** (Pixhawk hattı sessiz) · RTC pili donanım işi olarak açık
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 08

## Sorun (kanıt)
- Jetson'da RTC pil desteği yok: `nvvrs-pseq-rtc` her güç döngüsünde 1970'e dönüyor; ağsız açılışta saat 28 Temmuz 2026 (`results/jetson_20260917/LOG-DURUMU.md` §5). fake-hwclock yalnız "son kayıttan ≤10 dk eski" telafi verir.
- Emir'in envanteri (`LOG_ENVANTERI_20260917.md` §2): Pixhawk `.bin` dosya adı `1980-01-09 23-09-53.bin` → GPS zamanı yokken dosya adı da güvenilmez; olay saati log içinden çıkarılmış.
- Sonuç: Jetson kaydı ile Pixhawk `.bin`'i **duvar saatiyle** hizalamak iki taraftan da kırılgan.

## Çözüm — ortak saat Pixhawk'ın boot sayacı
- Pixhawk `GLOBAL_POSITION_INT.time_boot_ms` ile DataFlash `TimeUS` **aynı saattir** (autopilot boot'tan beri).
- `comms/inis_kaniti.zaman_eslemesi(okuyucu)` (yeni, modül fonksiyonu): `BagilIrtifaOkuyucu`nun son **kabul ettiği** konum paketinin `(time_boot_ms, yerel monotonic geliş)` çifti. Yabancı sysid / sıra dışı paket eşlemeyi değiştirmez (okuyucunun kendi kabul kuralı). Tazelik filtresi yok: yalnız kayıt içindir, karar yolu kullanmaz.
  - **Neden sınıf metodu değil:** FDR akış şemaları (`FDR/sekiller/akis_c.svg`, `ACIK_KALEMLER_HAM.md`) `inis_kaniti.py`'nin 925–1065. satırlarına atıf yapıyor; sınıf gövdesine ekleme hepsini kaydırırdı. Fonksiyon dosya **sonuna** eklendi, mevcut satırlar değişmedi.
- Görev kaydı `KARE` satırına: `pixhawk_ms`, `pixhawk_gelis_mono` (kaydın `monotonic_s` ile aynı saat), `irtifa_m`, `armed`, `mod` (taze snapshot'ta yoksa `None` — bayat değer yazılmaz). `boot_id` zaten `GOREV_BASLADI`'da (ONARIM-03).
- **Hizalama formülü:** bir `KARE` satırı için Pixhawk zamanı ≈ `pixhawk_ms + (monotonic_s − pixhawk_gelis_mono) × 1000` ms → `.bin`'de `TimeUS / 1000` ile aynı eksen. Hata payı: MAVLink gecikmesi (TELEM2 57600'de onlarca ms) + çoğullayıcı.

## Değişen dosyalar
- `comms/inis_kaniti.py` (+17 satır, sonda) · `jetson_paket/kod/inis_kaniti.py` (kanonik kopya, birebir)
- `codes/rpi_inference.py` — `_gorev_telemetri_alanlari()`; `run_camera` çağrı satırı aynı satır sayısında
- `tests/test_onarim08_zaman_eslemesi.py` — 6 test

## Kanıt
```
test_onarim08_zaman_eslemesi OK (6) · test_onarim03_gorev_kaydi OK · test_onarim04_keskinlik OK
test_inis_kaniti OK · test_rpi_canli_olcek OK · test_faz_b_rpi_ekransiz OK · test_p1_canli_mavlink OK
test_yki_gnss_telemetri OK · test_yki_ucus_telemetrisi OK · test_t162_alan_ihlali OK
test_fdr_t244_ic_celiski OK · test_seri_pixhawk_kilidi OK
test_jetson_comms_paketi FAILED (2) — önceden de 2 (model_registry.json, rpi_inference.py kopyaları bayat), yeni kırmızı yok
```
Mutasyon: `zaman_eslemesi` her zaman `None` → **3 FAIL**; geri alınca OK.

## Jetson'a dağıtım
`~/navitas/codes/rpi_inference.py` (md5 `ffdf2c7d…`), `~/navitas/comms/inis_kaniti.py` (`b8aeb71a…`), `~/navitas/codes/kare_keskinligi.py` (`adf951dd…`) = depo. `inis_kaniti.py`'nin önceki hâli depo HEAD'iyle aynıydı (md5 `6cdcd7b3…`), ayrı yedek alınmadı — `git show ad9cb52e:comms/inis_kaniti.py` ile geri gelir.

## Kalan
- Pixhawk bağlıyken kısa koşu: `KARE` satırlarında `pixhawk_ms` artmalı, `armed/mod` dolmalı.
- Donanım: CR2032 RTC pili (kesin çözüm; takım kararı).
- İsteğe bağlı: `.bin` ↔ `gorev_kaydi.jsonl` birleştiren hizalama betiği (hover_kapisi gibi pymavlink ile) — Emir'in logları gelince.
