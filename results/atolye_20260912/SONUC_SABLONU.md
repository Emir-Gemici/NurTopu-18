# 12 Eylül 2026 atölye — SONUÇ TABLOSU (T232 · `ATOLYE_TEST_GUNU_20260912.md`)

> Ekip doldurur. **Değer ölçüm dosyasından** yazılır (ekrandan söylenen sayı değil); dosyalar bu klasörde (`results/atolye_20260912/`). Boş satır = ÖLÇÜLEMEDİ.
> Kabul karşılaştırmasını mimar yapar (FDR Bölüm 4 sonuç sütunu, T231) — bu tabloya kabul/ret yazılmaz. Kart parametresi dökümden farklı okunduysa "not" sütununa.

| test | ölçülecek | ölçülen değer | dosya | durum | saat · kim | not |
|---|---|---|---|---|---|---|
| A1 | kumanda kapalı CH3/CH5 PWM; kapatma → `Land` süresi (s) ×3; `Radio Failsafe` satırı var/yok | | `A1_kumanda.txt` · `A1_failsafe.mp4` · `A1_<saat>.bin` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A2 | kart `FS_GCS_ENABLE`; çekme → `GCS Failsafe` süresi (s); (a) gaz orta / (b) gaz dipte davranışı | | `A2_gcs.txt` · `A2_gcs.mp4` · `A2_<saat>.bin` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A3 | `V_ölç` (V); yazım → `Battery 1 is low` süresi (s); mod; geri alınan `BATT_LOW_VOLT` | | `A3_pil.txt` · `A3_geri_alma.png` · `A3_<saat>.bin` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A4 | `RC6_OPTION` kararı (153/31); 3 denemede motor durdu (x/3) | | `A4_rc6.txt` · `A4_anahtar.mp4` · `A4_<saat>.bin` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A5 | kesme → YKS `(BAĞLANTI KAYBI!)` süresi (s) ×3; İKA `GÜVENLİ DURMA` süresi (s) ×3 | | `A5_hakem_log.jsonl` · `A5_iha.txt` · `A5_ika.txt` · `A5_kesme.mp4` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A6 | RTT p50/p95 (ms), kayıp (%), veri hızı (B/s) — IKA_GO ve PARAŞÜT kadansı; SiK Air Speed/ECC | | `A6_sik_ikago.json` · `A6_sik_parasut.json` · `A6_sik_ayar.txt` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A7 | ulaşılan mesafe (m); o mesafede RTT p95 (ms), kayıp (%); MK15 video CANLI/BAYAT | | `A7_sik_<mesafe>m.json` · `A7_konum_<m>.png` · `A7_mk15_<mesafe>m.png` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A8 | hat (TELEM2/USB); HEARTBEAT, GLOBAL_POSITION_INT, EXTENDED_SYS_STATE hızı (Hz); çıkış kodu | | `A8_mavlink.json` · `A8_mavlink.txt` · `A8_ekran.jpg` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A9 | p (px); d, s (m); FOV_yatay (°) | | `A9_fov.txt` · `A9_kare.jpg` · `A9_kamera.txt` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A10 | kare gecikmesi p50/p95 (ms); FPS; düşen kare | | `A10_canli_fps.txt` · `A10_ekran.jpg` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A11 | 5 gecikme ölçümü (ms), p50/maks; kumanda HDMI var/yok; Link Status bant/güç | | `A11_gecikme.txt` · `A11_gecikme.mp4` · `A11_foto_*.jpg` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A12 | öğrenilen `MOT_THST_HOVER`; VIBE X/Y/Z maks (m/s²); hover akımı (A); pil V | | `A12_hover.bin` · `A12_akim.json` · `A12_hover_devrilme.txt` · `A12_hover.mp4` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| A13 | %30 ve %50'de pens (A) / PM06 (A) / fark (%); pens çözünürlüğü | | `A13_akim.txt` · `A13_akim.mp4` · `A13_akim.json` | [ ] ÖLÇÜLDÜ [ ] ÖLÇÜLEMEDİ — neden: | | |
| 00/99 | parametre dökümü önce/sonra; `Compare Params` farkı | | `00_param_once.param` · `99_param_sonra.param` · `99_param_fark.png` | [ ] ALINDI [ ] ALINAMADI | | |
