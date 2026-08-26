# v7a çürütme — LENS 2: SAHA GÜVENLİĞİ (GPU YOK)

Tarih 2026-08-26 · Varsayım: "aday terfi ETMEMELİ" · Kod/veri/registry DEĞİŞMEDİ, git kullanılmadı.
Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`. Betik: `yeniden_olc.py` (bu dizin), log `yeniden_olc.log`, ham `yeniden_olc.json`, bindirmeler `bindirme/` (22 kare; üst-sol kare, üst-sağ uzlaşı, alt-sol v35, alt-sağ v7a; wp: beyaz=yol, sarı=etiketsiz, kırmızı=engel).

## 0. Ölçüm doğru mu — GPU'suz bağımsız yeniden üretim
Komut: `python results/gece_20260826/v7a_curut/guvenlik/yeniden_olc.py`
Girdi: 126 JSON'larındaki `olceksiz_wps` (3840 letterbox tuvali → 960×540: x/4, (y−840)/4) + `t152_uzlasi/*_uc.png` + `rota_yol_olcumu.rota_yol_olc` (aynı tanım).
```
etiket(v3 labels) vs uzlasi png farkli piksel payi: maks 0.013125 ort 0.0052 n 111
v7a test29: ROTA 8 YANLIS 0   engel_wp_toplam 0
v7a val82 : ROTA 30 YANLIS 7  [64,129,140,168,208,210,223] engel_wp_toplam 3
v35 test29: ROTA 6 YANLIS 5   [124,135,152,196,202] engel_wp_toplam 15
v35 val82 : ROTA 15 YANLIS 10 [130,153,156,157,158,159,201,203,208,230] engel_wp_toplam 64
```
→ D-293'ün 7/38 (v7a) ve 15/21 (v35) sayıları uzlaşı PNG'sinden bağımsız yolla **birebir** çıkıyor; dataset v3 etiketleri ile uzlaşı PNG'si ≤ %1,3 piksel farklı (INTER_NEAREST kenarı). **Ölçüm yanlış DEĞİL.**

## 1. Eksen eksen v7a vs v35 (kayıtlı JSON'lar)
| eksen | v35 | v7a | yön / hüküm |
|---|---|---|---|
| K0 figür zemin (kabul) | 0,0903 (oran 1,00) | 0,0266 (**oran 0,29**) | `65_kabul_denetcisi` D-186 kuralı: oran < 0,5 = **YETENEK uyarısı, fail-closed yön**; tehlikeli yön (> 2,0, daha ÇOK zemin) değil. Bloklamaz. |
| 109 figur_zemin_orani | 0,1508 | 0,0444 | aynı yön (az görüyor); figürde yer gerçeği yok (D-256 §4), kapı değil |
| K1 rota | 256/260 | 255/260 | eş |
| K2 moloza basma | 18/256 (%7,0) | 15/255 (%5,9) | v7a **daha iyi** |
| K3 ağır | 0/256 | 1/255 (%0,4) | v7a 1 kare kötü (tavan %3 altı) |
| K4 arena dışı | 1/256 (%0,4) | **4/255 (%1,6)** | v7a **4× kötü**, tavan %5 altı — KUSUR-1 |
| K6 yanlış güzergâh (sentetik) | 5/256 (%1,95) | 7/255 (%2,7) | v7a hafif kötü, tavan %5 altı |
| K5 bariyer kesişim | 0/173 | 0/172 | eş |
| çatı kaçağı ort/medyan | 0,043 / 0,021 | 0,023 / 0,012 | v7a **daha iyi** |
| 67 gerçek karede red | 0 | 0 | eş |
| kaplama67 içerik medyan | 0,508 (**D-240 bandı %47–52 İÇİNDE**) | **0,417 (bant ALTINDA)** | v7a gerçek otoparkta **eksik görüyor** (fail-closed); K0 raw_frames ort 0,289 → 0,234 — KUSUR-2 |
| val82 zemin geri çağırma (sizinti) | 0,083 | ÖLÇÜLMEDİ (v7a için sızıntı ölçümü koşulmadı; GPU gerek) | ÖLÇÜLEMEDİ |

**Belirgin kötü eksen var mı?** Tehlikeli yönde (daha çok zemin / engele basma) hiçbir eksende v7a v35'ten kötü değil: K2 ve çatı daha iyi. Kötüleşen üç kalem K3 (+1), K4 (+3), K6 (+2) — hepsi sentetik, tavan altı, n=255'te 1–3 kare. Kapasite yönünde (figür, kaplama67) v7a belirgin daha az görüyor — bu sahada "rota yok" demektir, "yanlış rota" değil.

## 2. Gerçek karede: v7a'nın 7 yanlışı vs v35'in 10 yanlışı (val82)
Kesişim yalnız **208**. v7a'nın 6 yanlışı **YENİ** (64, 129, 140, 168, 210, 223); v35'in 9 yanlışı v7a'da yok (153, 156, 157, 158, 159, 201, 203 → v7a ROTA yol payı 0,93–1,00; 130 → MASKE_YOK; 230 → UC_BANT). Test29'da v35'in 135/152/202 kanal rotaları v7a'da yol payı 0,98/1,00/1,00.
**Karakter farkı (asıl bulgu):** v35'in val82 yanlışlarının 8/10'unda rota çizgisinin engel payı 0,60–1,00 ve 4–8/8 waypoint **beton kanal üstünde** (engel_wp toplam 64); v7a'da engel_wp toplam **3** (208, 210, 223'te 1'er). v7a yanlışları çoğunlukla **etiketsiz** zemine düşüyor (0,11–1,00).

Gözle (bindirmeler):
- **64** (yol 0,67): rota çakıl yol üstünde; üst 3 wp yolun etiketsiz bırakılmış çakıl kenarında. Fiziksel tehlike görünmüyor; referans muhafazakâr.
- **129** (yol 0,00, etiketsiz 1,00): karede **belirgin çakıl yol var** (üst-sol panel), uzlaşı bu yolu etiketsiz bırakmış (A∧B uyuşmazlığı; tavan sebebi UC_BANT). Rota o yolun üstünde. **Referans eksiği**, model hatası değil.
- **140** (0,63): rota çakıl yolda; orta wp'ler etiketsiz yol kenarında. Tehlike görünmüyor.
- **168** (0,89 — eşik 0,90): son wp yol sonundaki etiketsiz toprağa taşıyor; sınır durumu.
- **208** (0,38, engel_wp 1): rota toprak yoldan başlayıp **beton kanalı KESEREK** etiketsiz dar asfalt şeride geçiyor. Gerçek risk (kanal geçişi). Aynı karede v35: 4 wp kanal üstünde, yol 0,00 — v35 daha kötü.
- **210** (0,57, engel_wp 1): rota **kanal üstünden başlıyor** (alt wp), yola çıkıyor, üstte etiketsize kayıyor. v35 burada rota üretmiyordu (UC_BANT) → **yeni risk**.
- **223** (0,00, etiketsiz 0,93, engel_wp 1): **yol YOK** — çorak tarla/yamaç; v7a çalılıktan başlayıp tarla boyunca 8 wp rota üretiyor. v35 MASKE_YOK (güvenli). **Yeni ve gerçek yanlış güzergâh** (şartname: 0 puan). v3 ve v6 de aynı karede FP (sizinti/rapor.md). — KUSUR-3

**Rota kaybı (fail-closed, kapasite):** v35'in doğru 3 rotası v7a'da yok — test 120 (yol 0,97 → MASKE_YOK), val 90 ve 136 (1,00 → MASKE_YOK). — KUSUR-4
Çapraz tablo (111 kare, v35→v7a): MASKE_YOK→ROTA 17, UC_BANT→ROTA 7, ROTA→MASKE_YOK 5, ROTA→UC_BANT 2, ROTA→ROTA 14.

## 3. FP 3/111
- **test29 218**: tavan UC_BANT_TEMAS_YOK (etiketli yol uç bantlara değmiyor), ama uzlaşıda yol VAR ve v7a rotası yol payı 0,95 ile onun üstünde. **Gerçek FP değil** — tavan boru hattı artefaktı.
- **val82 129**: yol görünür, uzlaşı etiketsiz; rota yolun üstünde. **Referans eksiği**, FP değil.
- **val82 223**: yol yok, rota var. **Gerçek FP** = gerçek yanlış güzergâh (1/111).
→ Gerekçedeki "FP 3/111" sayısı doğru ama yorumu iki yönlü: 2'si referans/tavan kaynaklı, 1'i gerçek.

## 4. Arena figürü
Kayıtlı ölçüm: `109` → figur_zemin_orani 0,0444, figur_engel_orani 0,1487 (v35 0,1508 / 0,2209). ON_KAYIT §4(c)'deki "arena figüründe yol var/yok" (rota) v7a için **ÖLÇÜLEMEDİ** — kayıt yok, GPU koşulmadı. Figürde yer gerçeği olmadığından bu sayı yön bilgisi verir (az zemin), tehlike bilgisi vermez.

## 5. Hüküm — "v7a sahada v35'ten daha tehlikeli olabilir mi?"
**HAYIR (bu kanıt kümesinde).** Kanıt: (i) tehlikeli yönlü hiçbir kabul ekseninde v7a v35'ten kötü değil (K2/çatı daha iyi; K3/K4/K6 farkları 1–3 kare, tavan altı); (ii) gerçek karede engel üstünde waypoint 64+15 → 3; v35'in "rota kanal üstünde" kalıbı (10 karede) v7a'da yok; (iii) v7a'nın yeni yanlışlarının 4'ü (64/129/140/168) referans-kenarı, 2'si kanal teması (208 v35'te daha kötü; 210 yeni), 1'i gerçek "yolsuz tarlada rota" (223).
**Ama** v7a **sıfır risk değil**: 223 tipi (yol olmayan sahnede rota) v35'te görülmeyen **yeni bir hata sınıfıdır** ve 210'da kanaldan başlayan rota yenidir. Bunlar 111 karede 2 kare; v35'in aynı kümede 15 kanal rotası var. Sahada operatör sözleşmesi ("rota yol dışındaysa durdur") yoksa 223 tipi hata 0 puan üretir — v35 için aynı kural kanal rotasında zaten geçerliydi.

## 6. Kısıtlar
- Tek uçuş (0038), aynı gün/kamera; 111 kare; arena değil (D-292 sınırı).
- v7a için sızıntı/geri çağırma piksel ölçümü ve arena figüründe rota ölçümü yok (GPU) — ÖLÇÜLEMEDİ.
- "engel_wp" yalnız waypoint pikselini sayar; iki wp arasındaki çizgi kanalı kesse de wp sayılmaz (208'de engel payı 0,18 bunu yakalıyor, sayaç 1).
- Uzlaşı A∧B muhafazakâr: "etiketsiz" ≠ "tehlikeli" (129 örneği); ama 223'te etiketsiz = tarla, gerçekten yol yok.
