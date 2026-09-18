# 18 Eylül 2026 21:17 — gece askı testi log analizi (ilk uçuşlar, yeniden kurulmuş gövde)

**Log:** `2026-09-18 21-17-21.bin` (520 s; ayrıca 21:15/21:16 üç kısa arm-öncesi kayıt). Araç tool özeti: `analiz_2117.json`.
**Pil: 3S** (başlangıç 12,28 V; parametreler 3S'e göre: ARM 12,0 / LOW 11,2 / CRT 10,2, VOLTSRC 1; `BATT_CAPACITY` 13000 3S paket için yanlış). ⚠ 3S'te Jetson buck regülatörü 12,2 V veremez (D-494 öncesi ölçüm): **YKİ bu uçuşlarda hiçbir telemetri almadı** (`results/prova/20260918_191533_41668` 21:10 sonrası 0 olay) → yazılım zinciri uçuşta çalışmadı (ÇIKARIM: Jetson kapalı/yeniden başlıyor). Jetson'a bu sırada erişilemedi (Ethernet çekili).

| Pencere | Süre | Ne |
|---|---|---|
| W1 48–61 s | 7 s | Loiter kısa sıçrama, LAND anahtarı, CH6 disarm |
| **W2 113–152 s** | **30 s havada** | Loiter, 0,7–0,8 m; 147,8 LAND; kendiliğinden disarm. 120,8 s EKF yaw reset (EV 62) |
| W3 169–256 s | 88 s | Armlı rölanti (1097 µs), kalkış yok |
| **W4 416–441 s** | **12 s havada** | Loiter 0,7 m; LAND; disarm |
| sonrası | — | `PreArm: Battery 1 below minimum arming voltage` (dinlenme 11,9 V < ARM 12,0 = 4,0 V/hücre; 3S için 11,4 uygun) |

**U1 kabul ölçütleri (yol haritası Faz 8 / D-484), W2 havada:**

| Ölçüt | Eşik | W2 | W4 | Sonuç |
|---|---|---|---|---|
| VibeZ p95 | ≤ 16 | 6,5 | 6,0 | GEÇTİ (clip 0) |
| Tutum hatası RMS roll/pitch | ≤ 1,5° | 1,27 / 0,55 | 1,67 / 1,58 | W2 GEÇTİ, W4 sınırda DÜŞTÜ |
| Hız hatası RMS roll/pitch | ≤ 10 °/s | 11,2 / 4,1 | 13,9 / 10,1 | DÜŞTÜ (hafif) |
| Motor yayılımı | ≤ 40 µs | **105** | **120** | DÜŞTÜ |
| CCW−CW = (M1+M2)−(M3+M4) | ≤ 60 µs | **+112** | **+145** | DÜŞTÜ |
| Askı gazı ThO p50 | 0,32–0,40 (9x5x3/4S bandı) | 0,33 (3S+1045) | 0,33 | bilgi |
| Pil | ham V_min ≥ 14,0 (4S) | 3S: 10,48 V @ 39 A; VoltR 12,08 | 10,36 | 3S ölçütü yok; sarkma 0,6 V/hücre yüksek |
| GPS | ≥ 12 uydu, HDop < 1 | 21–26, 0,75 | 19–24, 0,81 | GEÇTİ |
| Salınım (IMU0 FFT 2–12 Hz) | tepe yok | roll **6,9 Hz 2,1 °/s** | roll 7,9 Hz 2,6 °/s | küçük genlik; 17 Eyl kazasında 12–45 °/s idi |

**Yorum:** Uçuş kontrol edilebilir ve titreşim temiz. Açık sorunlar: (1) **motor dengesizliği sürüyor** — CCW çift (M1, M2; en yüksek M2 arka-sol) CW çiftten +85…+164 µs fazla çalışıyor, uçuş içinde dalgalanıyor (17 Eyl'de +16→+520 tırmanıştı; şimdi büyümüyor ama eşiğin 2 katı) → arka kollar/motor eksen dikliği/pervane eşleşmesi kontrolü (T279). (2) Roll ekseninde 7–8 Hz küçük salınım; `MOT_BAT_VOLT_MAX/MIN 16,8/13,2` 4S değerleri 3S'te (10,5–12 V) kazancı ~%27 artırıyor (HESAP) — 4S'e geçince kendiliğinden düzelir; 4S'te yeniden ölçülmeli. (3) EKF yaw reset (W2 içinde) → pusula/GPS başlık uyuşmazlığı; sabah dışarıda Jetson açıkken pusula kalibrasyonu (yalnız harici pusula kullanılıyor: DEV_ID2 658953, OFS2 31/−6/72). (4) 3S ile **Jetson uçmaz**; yarın 4S şart; 4S parametreleri geri yazılmalı (BATT LOW/CRT/ARM 14,0/13,2/14,4).
**Yazılım doğrulaması bu uçuşta YOK** (YKİ'ye veri gelmedi).
