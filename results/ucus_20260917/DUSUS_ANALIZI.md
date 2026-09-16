# 17 Eylül 2026 00:20 düşüşü — log analizi

**Log:** `1980-01-09 23-09-53.bin` (Mission Planner adı; GPS zamanı yok iken açılmış) — kopya bu klasörde.
Telemetri: `2026-09-17 00-19-32.tlog`. ArduCopter 4.5.7, Pixhawk 6C (S/N 00440022 …).
**Olay anı:** log t = 648,28 s = **17 Eyl 00:20:30 yerel** (GPS: 2026-09-16 21:20:30 UTC).
Ham çıkarımlar: `genel.txt` (olaylar + parametreler), `ucus3_pencere.txt` (0,1 s tablo),
`ucus3_carpma_ham.txt` (RATE/PSC/MOTB/IMU ham), `ucus3_iz.txt` (iz + çubuk istatistiği).

## 1. Logdaki uçuşlar

| # | arm → disarm (s) | olay |
|---|---|---|
| 1 | 46,2 → 138,4 | Loiter; 4 kısa iniş-kalkış; CH6 ile disarm |
| 2 | 596,0 → 605,9 | Kalkmadı; LAND anahtarı → yerde disarm |
| 3 | 617,2 → 649,6 | **Düşüş.** Loiter, ~1,5 m; 647,9 LAND anahtarı; 648,28 çarpma; 648,6 ters döndü; 649,4 CH6 disarm |

## 2. Son 4 saniye (uçuş 3)

| t (s) | Pilot girişi | Araç |
|---|---|---|
| 643,0–644,0 | Pitch **tam ileri** | 4,0 m/s'ye hızlandı, kalkış noktasından 9,5 m'ye gitti |
| 645,0–645,8 | Yaw **tam sol** | ~100–180 °/s dönüş; roll izleme hatası 10,5°'ye çıktı |
| 645,8–646,9 | Pitch ileri (C2 ≈ 1060–1210) | İstenen pitch −14°, gerçek −16…−21° |
| 647,0–647,7 | Yaw **tam sağ** | ~180 °/s dönüş |
| 647,8 | Mod anahtarı → **LAND** (647,93) | Hâlâ 1,3–1,4 m/s yatay hız ve ~170–180 °/s yaw dönüşü |
| 648,20 | Çubuklar ortada | Roll 2,4°, hız 1,3 m/s, yaw hızı 166 °/s — **kontrol normal** |
| **648,24** | — | İleri ivme +4,2 m/s² (ilk temas izi) |
| **648,28** | — | **Yaw hızı 154 → 4 °/s (40 ms'de durdu)**, yanal ivme **−15,8 m/s² (1,6 g)**, roll hızı 132 °/s |
| 648,32 | — | Yaw hızı **−99 °/s (ters yöne sekti)** |
| 648,30 | — | EKF yatay hızı 1,22 → 0,33 m/s; FC doğru yönde tam düzeltme veriyor (ROut −0,56; M1 1949 / M2 1150) |
| 648,4–648,6 | — | Çıkışlar doyumda, pitch 80°, roll 92° → 145° (ters döndü); akım 115 A tepe |
| 648,84 | — | Yere çarpma: |a| = 67 m/s² (6,9 g) |
| 649,16 | — | EKF şerit değişimi, GCS failsafe mesajı (çarpma sonrası) |
| 649,4–649,6 | CH6 → disarm | Motorlar durdu |

## 3. Teknik arıza var mı?

Çarpmadan **önce** bakılan her şey temiz:

| Kontrol | Bulgu | Hüküm |
|---|---|---|
| Hata/failsafe mesajı | ERR ya da failsafe yok (GCS failsafe ve EKF şerit değişimi **çarpmadan sonra**, 649,16) | Temiz |
| GPS / EKF | 19–21 uydu, HDop 0,62–0,76; XKF4 SV/SP/SH/SM ≤ 0,07 | Temiz |
| Titreşim | VibeZ 3–9, clip 0 | Temiz |
| Pil | Yükte 14,4–14,8 V, 40–55 A | Temiz |
| Motor doyumu | En yüksek ~1880 µs (tam yaw sırasında); 1949 tavanına çarpmadan önce ulaşılmadı | Temiz |
| Tutum izleme (çubuklar ortada) | Roll hatası ort. 0,57°, maks. 3,4° | İyi |
| Tutum izleme (tam yaw çubuğu) | Roll hatası ort. 2,0°, maks. **10,5°** | Zayıf ama kontrol korunuyor |
| Motor dengesi (çubuklar ortada, n = 125) | M1 1550, M2 1568, M3 1594, M4 1585; yayılım **44 µs**; CCW−CW **−61 µs** | Kabul sınırlarının (≤ 40 / ≤ 60) biraz üstünde |
| FC tepkisi çarpmada | Roll/pitch düzeltmesi doğru yönde ve tam | FC doğru çalıştı |

**Çarpma imzası:** 154 °/s'lik yaw dönüşünün 40 ms'de durması ve ters yöne sekmesi, 1,6 g yanal ivme ve yatay hızın
0,1 s'de 1,2 → 0,3 m/s'ye düşmesi **dış bir cisme temas** gösterir. Motor ya da pervane kaybı itkiyi düşürür ama
dönmekte olan gövdenin yaw dönüşünü 40 ms'de durduramaz ve 1,6 g yatay kuvvet üretemez.
ÇIKARIM: yanal ivme −Y (sola), roll hızı +X (sağ taraf aşağı) → temas büyük olasılıkla **sağ taraftan** (M1 ön-sağ ya
da M4 arka-sağ kol/pervane). Cismin ne olduğu logda yoktur.

## 4. Katkı değerlendirmesi

⚠ **Bu bölüm ölçüm değil, kanıta dayalı değerlendirmedir.** Log "kim ne kadar suçlu" diye bir sayı vermez;
yüzdeler aşağıdaki kanıtların ağırlıklandırmasıdır.

| Etken | Kanıt | Pay |
|---|---|---|
| **Pilot / operasyon** | ~1,5 m irtifada, kalkıştan 9 m uzakta, bir engelin yakınında tam çubuk pitch (4 m/s) ve iki yöne tam çubuk yaw (~180 °/s); yatay hareket ve dönüş durmadan LAND'e alındı; gece (00:20) | **~%80–85** |
| Araç ayarı: Loiter frenleme | `LOIT_BRK_DELAY=1` s, `LOIT_BRK_ACCEL=250` cm/s² (varsayılan) — çubuk bırakılınca araç 1 s daha süzülür; 4 m/s'den durma mesafesi metrelerce | ~%10 |
| Araç: yaw dengesizliği ve LAND geçişi | CCW−CW −61 µs, yayılım 44 µs → tam yaw sırasında roll hatası 10,5°; LAND'e geçişte gaz karışımı azaldı (MOTB ThrAvMx 0,42 → 0,30), tutum payı düştü | ~%5–10 |
| Teknik arıza (motor, ESC, pil, GPS, EKF, failsafe) | Çarpmadan önce hiçbir iz yok | **%0** |

**Hüküm:** Düşüşün doğrudan nedeni teknik arıza değil, **dış bir cisme çarpma**. Çarpmaya giden durum büyük ölçüde
pilotaj ve uçuş alanı seçiminden kaynaklanıyor. Araç ayarları (Loiter frenlemesi, hafif yaw dengesizliği) payı
büyütmüş ama tek başına düşüşe yol açacak durumda değil.
Cisim hareketliyse (insan, sallanan kablo ya da halat) pilot payı düşer — bu bilgi logda yok.

## 5. Sonraki uçuştan önce

1. `SAHA_OLAY_SONRASI_MUAYENE.md` maddeleri; **önce sağ taraf** (M1, M4): pervane, kol, motor yatağı, motor montajı.
   Ardından Pixhawk montajı ve GPS direği.
2. Pervanesiz motor testi ve video (yol haritası Faz 2.6); ardından ilk askı U1 kabul testi.
3. Eğitim uçuşları için öneri (geri alınabilir parametreler; karar pilotun):
   - `PILOT_Y_RATE` 202,5 → 90 °/s
   - `LOIT_SPEED` 1250 → 500 cm/s
   - `LOIT_BRK_DELAY` 1,0 → 0,3 s
   - `LOIT_BRK_ACCEL` 250 → 500 cm/s²
4. Uçuş alanı: engellerden ≥ 10–15 m uzak, irtifa ≥ 3 m, yeterli aydınlatma. Engel yakınında tam çubuk yaw yok.
