# H1 · T213-B — OPEN_ROUTE → sim hakem → İKA MuJoCo fizik sürüşü (15 harita × 3 tohum)

Üreteç: `simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak {gt,model} --res 1280 --tohumlar 42,43,44` → bu klasördeki `<kaynak>_<harita>_<senaryo>_<tohum>.json` + `ozet_kosum.json`; bu README `simulation/mujoco/kosum_readme.py` ile **ölçümden** yazılır, elle düzenlenmez (kilit: bayt-eş). Özet tarihi: 2026-09-10 10:22.

Etiketler (ON_KAYIT §5.2): **YER GERÇEĞİ** = `arena.route_waypoints` (açık yolun merkez hattı, engel kaçınması YOK; 3,3 m segmentler `MAX_SEGMENT_M` 2,10'a bölünür — D-438 c) · **ÜRETİM MODELİ** = `iha_haritala` (v36, OBB kapalı, sim'e özel eğitim YOK). Sürüş her ikisinde AYNI: `ika_nav.navigate` + `MuJoCoSurucu`, 10 Hz kontrol, 2 ms fizik, SİM SAATİ.

## 1. Özet (`ozet_kosum.json`)

| kaynak | n | rota bulundu | rota doğru | OPEN_ROUTE ACK [ika,yks] | IKA_GO ACK | HB içinde | temas var | süre aşımı | **BAŞARI** | harita (3/3) | eşik |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gt (YER GERÇEĞİ) | 45 | 45 | 45 | 45 | 45 | 35 | 12 | 10 | **33/45 (0.733)** | 10/15 | ≥ 12/15 harita (× 3 tohum) — ON_KAYIT H1-K5; gevşetilmez |
| model (ÜRETİM MODELİ) | 45 | 0 | 0 | 45 | 0 | 0 | 0 | 0 | **0/45 (0.000)** | 0/15 | ≥ 12/15 harita (× 3 tohum) — ON_KAYIT H1-K5; gevşetilmez |

Başarı tanımı (K5): çıkış 0 ∧ rota bulundu ∧ HB 2×2 m karesi içinde ∧ temas 0 ∧ sürüş ≤ 600 s sim.

## 2. Sürüş süresi (sim saniye — SANAL, `data.time`; İHA kolu kinematik profil süresi)

| kaynak | başarılı koşumlar | tüm koşumlar | varış mesafesi (m) | duvar saati toplam (s) |
|---|---|---|---|---|
| gt | n=33 · min 64.1 · medyan 71.3 · ort 75.6 · maks 98.4 | n=45 · min 64.1 · medyan 82.8 · ort 193.1 · maks 600.1 | n=45 · min 0.1 · medyan 0.2 · ort 3.7 · maks 45.0 | 292.1 |
| model | — | — | n=45 · min 44.5 · medyan 45.2 · ort 45.0 · maks 45.8 | 641.2 |

Senaryo kırılımı:

| kaynak | senaryo | n | başarı | HB içinde | temas var |
|---|---|---|---|---|---|
| gt | kolay | 15 | 15 | 15 | 0 |
| gt | orta | 15 | 7 | 9 | 8 |
| gt | zor | 15 | 11 | 11 | 4 |
| model | kolay | 15 | 0 | 0 | 0 |
| model | orta | 15 | 0 | 0 | 0 |
| model | zor | 15 | 0 | 0 | 0 |

## 3. Teşhis — başarısızlık nedenleri (ölçülen alanlardan sayılır)

`rota_engel_aciklik_m`: rota polyline'ı ile en yakın engel geomunun (moloz/tıkama/chicane/bariyer) XY OBB açıklığı. İKA yarı genişliği 0.25 m (iz 0.4595 TAHMİN + teker). Açıklık < 0.25 → rota **inşaat gereği** çarpışmasız izlenemez (sürücü sıfır hatayla gitse bile). 0.25–0.50 → üretim planlayıcısının `TAKIP_HATA_M` payının altında (CONTRACTS §4 `R_GEREKLI_M` 1,10 açıklık garantisi GT merkez hattında YOKTUR).

| kaynak | temas ∧ geçilemez (< yarı gen.) | temas ∧ takip bandı | temas ∧ açıklık ≥ 0,50 (sürücü adayı) | kod 3 (izin yok) | kod 2 (NO_ROUTE) | kod 4 temassız |
|---|---|---|---|---|---|---|
| gt | 10 | 2 | 0 | 0 | 0 | 0 |
| model | 0 | 0 | 0 | 0 | 45 | 0 |

## 4. Koşum tablosu (her satır bir JSON)

| kaynak | harita | senaryo | tohum | rota | doğru | wp | açıklık m (geom) | çıkış | HB | varış m | temas | sürüş sim-s | başarı | sonuç/neden |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gt | 1 | kolay | 42 | ✓ | ✓ | 41 | 2.706 (chicane_1) | 0 | ✓ | 0.21 | 0 | 64.3 | **✓** | BAŞARI |
| gt | 1 | kolay | 43 | ✓ | ✓ | 41 | 2.843 (moloz_51) | 0 | ✓ | 0.21 | 0 | 64.3 | **✓** | BAŞARI |
| gt | 1 | kolay | 44 | ✓ | ✓ | 41 | 2.945 (moloz_118) | 0 | ✓ | 0.21 | 0 | 64.3 | **✓** | BAŞARI |
| gt | 1 | orta | 42 | ✓ | ✓ | 46 | 0.000 (chicane_3) | 4 | ✗ | 11.61 | 5 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 1 | orta | 43 | ✓ | ✓ | 46 | 0.000 (tikama_1_2_7) | 4 | ✗ | 15.05 | 469 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 1 | orta | 44 | ✓ | ✓ | 46 | 0.000 (tikama_1_2_4) | 4 | ✗ | 14.80 | 5203 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 1 | zor | 42 | ✓ | ✓ | 61 | 0.596 (tikama_2_2_2) | 0 | ✓ | 0.18 | 0 | 95.6 | **✓** | BAŞARI |
| gt | 1 | zor | 43 | ✓ | ✓ | 61 | 0.003 (tikama_2_2_2) | 4 | ✗ | 6.60 | 10923 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.003 < 0.22) |
| gt | 1 | zor | 44 | ✓ | ✓ | 61 | 0.000 (tikama_2_2_0) | 4 | ✗ | 44.97 | 3217 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 2 | kolay | 42 | ✓ | ✓ | 43 | 2.157 (chicane_1) | 0 | ✓ | 0.17 | 0 | 67.9 | **✓** | BAŞARI |
| gt | 2 | kolay | 43 | ✓ | ✓ | 43 | 1.061 (chicane_1) | 0 | ✓ | 0.17 | 0 | 67.9 | **✓** | BAŞARI |
| gt | 2 | kolay | 44 | ✓ | ✓ | 43 | 2.059 (chicane_1) | 0 | ✓ | 0.17 | 0 | 67.9 | **✓** | BAŞARI |
| gt | 2 | orta | 42 | ✓ | ✓ | 63 | 0.301 (tikama_2_2_6) | 0 | ✓ | 0.18 | 1 | 98.5 | ✗ | temas · açıklık takip bandında (0.301 < 0.50) |
| gt | 2 | orta | 43 | ✓ | ✓ | 63 | 0.309 (tikama_2_2_2) | 0 | ✓ | 0.17 | 1 | 98.5 | ✗ | temas · açıklık takip bandında (0.309 < 0.50) |
| gt | 2 | orta | 44 | ✓ | ✓ | 63 | 1.088 (bariyer_2) | 0 | ✓ | 0.22 | 0 | 98.4 | **✓** | BAŞARI |
| gt | 2 | zor | 42 | ✓ | ✓ | 61 | 1.460 (bariyer_2) | 0 | ✓ | 0.20 | 0 | 92.1 | **✓** | BAŞARI |
| gt | 2 | zor | 43 | ✓ | ✓ | 61 | 1.460 (bariyer_2) | 0 | ✓ | 0.20 | 0 | 92.1 | **✓** | BAŞARI |
| gt | 2 | zor | 44 | ✓ | ✓ | 61 | 1.016 (chicane_0) | 0 | ✓ | 0.20 | 0 | 92.1 | **✓** | BAŞARI |
| gt | 3 | kolay | 42 | ✓ | ✓ | 44 | 2.810 (chicane_0) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 3 | kolay | 43 | ✓ | ✓ | 44 | 3.336 (chicane_1) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 3 | kolay | 44 | ✓ | ✓ | 44 | 2.763 (chicane_4) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 3 | orta | 42 | ✓ | ✓ | 44 | 0.000 (tikama_1_2_0) | 4 | ✗ | 14.84 | 17 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 3 | orta | 43 | ✓ | ✓ | 44 | 0.000 (tikama_1_2_0) | 4 | ✗ | 15.71 | 11312 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 3 | orta | 44 | ✓ | ✓ | 44 | 0.000 (tikama_1_2_5) | 4 | ✗ | 15.26 | 18 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 3 | zor | 42 | ✓ | ✓ | 58 | 0.000 (tikama_2_2_1) | 4 | ✗ | 10.22 | 8 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 3 | zor | 43 | ✓ | ✓ | 58 | 0.573 (tikama_2_2_0) | 0 | ✓ | 0.16 | 0 | 90.3 | **✓** | BAŞARI |
| gt | 3 | zor | 44 | ✓ | ✓ | 58 | 0.000 (tikama_2_2_1) | 4 | ✗ | 10.24 | 6 | 600.1 | ✗ | temas · rota inşaat gereği geçilemez (açıklık 0.000 < 0.22) |
| gt | 4 | kolay | 42 | ✓ | ✓ | 43 | 0.844 (bariyer_2) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 4 | kolay | 43 | ✓ | ✓ | 43 | 0.844 (bariyer_2) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 4 | kolay | 44 | ✓ | ✓ | 43 | 0.844 (bariyer_2) | 0 | ✓ | 0.14 | 0 | 67.2 | **✓** | BAŞARI |
| gt | 4 | orta | 42 | ✓ | ✓ | 51 | 0.243 (chicane_3) | 0 | ✓ | 0.12 | 0 | 84.2 | **✓** | BAŞARI |
| gt | 4 | orta | 43 | ✓ | ✓ | 51 | 0.312 (chicane_2) | 0 | ✓ | 0.12 | 0 | 84.2 | **✓** | BAŞARI |
| gt | 4 | orta | 44 | ✓ | ✓ | 51 | 0.563 (chicane_2) | 0 | ✓ | 0.12 | 0 | 84.2 | **✓** | BAŞARI |
| gt | 4 | zor | 42 | ✓ | ✓ | 47 | 1.396 (moloz_53) | 0 | ✓ | 0.15 | 0 | 75.2 | **✓** | BAŞARI |
| gt | 4 | zor | 43 | ✓ | ✓ | 47 | 1.602 (bariyer_2) | 0 | ✓ | 0.15 | 0 | 75.2 | **✓** | BAŞARI |
| gt | 4 | zor | 44 | ✓ | ✓ | 47 | 1.511 (chicane_1) | 0 | ✓ | 0.15 | 0 | 75.2 | **✓** | BAŞARI |
| gt | 5 | kolay | 42 | ✓ | ✓ | 53 | 1.619 (tikama_2_1_7) | 0 | ✓ | 0.22 | 0 | 82.8 | **✓** | BAŞARI |
| gt | 5 | kolay | 43 | ✓ | ✓ | 53 | 0.526 (tikama_2_1_8) | 0 | ✓ | 0.22 | 0 | 82.8 | **✓** | BAŞARI |
| gt | 5 | kolay | 44 | ✓ | ✓ | 53 | 1.465 (tikama_2_1_5) | 0 | ✓ | 0.22 | 0 | 82.8 | **✓** | BAŞARI |
| gt | 5 | orta | 42 | ✓ | ✓ | 44 | 1.494 (chicane_4) | 0 | ✓ | 0.18 | 0 | 71.3 | **✓** | BAŞARI |
| gt | 5 | orta | 43 | ✓ | ✓ | 44 | 1.839 (chicane_0) | 0 | ✓ | 0.18 | 0 | 71.3 | **✓** | BAŞARI |
| gt | 5 | orta | 44 | ✓ | ✓ | 44 | 1.704 (chicane_0) | 0 | ✓ | 0.18 | 0 | 71.3 | **✓** | BAŞARI |
| gt | 5 | zor | 42 | ✓ | ✓ | 44 | 1.758 (chicane_2) | 0 | ✓ | 0.23 | 0 | 64.1 | **✓** | BAŞARI |
| gt | 5 | zor | 43 | ✓ | ✓ | 44 | 1.497 (moloz_176) | 0 | ✓ | 0.23 | 0 | 64.1 | **✓** | BAŞARI |
| gt | 5 | zor | 44 | ✓ | ✓ | 44 | 1.928 (chicane_0) | 0 | ✓ | 0.23 | 0 | 64.1 | **✓** | BAŞARI |
| model | 1 | kolay | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.24 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | kolay | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.24 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | kolay | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.24 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | orta | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.49 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | orta | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.49 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | orta | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.49 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | zor | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.17 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | zor | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.17 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 1 | zor | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.17 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | kolay | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.16 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | kolay | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.16 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | kolay | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.16 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | orta | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.71 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | orta | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.71 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | orta | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.71 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | zor | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.53 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | zor | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.53 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 2 | zor | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.53 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | kolay | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.31 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | kolay | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.31 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | kolay | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.31 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | orta | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | orta | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | orta | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | zor | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | zor | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 3 | zor | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.77 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | kolay | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.27 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | kolay | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.27 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | kolay | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.27 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | orta | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.65 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | orta | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.65 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | orta | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.65 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | zor | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.22 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | zor | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.22 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 4 | zor | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 45.22 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | kolay | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.66 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | kolay | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.66 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | kolay | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.66 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | orta | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.78 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | orta | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.78 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | orta | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.78 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | zor | 42 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.55 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | zor | 43 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.55 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |
| model | 5 | zor | 44 | ✗ | ✗ | 0 | — | 2 | ✗ | 44.55 | 0 | — | ✗ | NO_ROUTE (model karar vermedi) |

## 5. Sınırlar (rapora yazılır)

- İHA uçuşu **kinematik** (mocap; aerodinamik yok); `sure_sim_iha_profil` = fırlatma→iniş profil süresi.
- Hakem onayı sim'de **otomatik** (`sim_hakem`, mesajlar `sim: true`, CONTRACTS §6.7.1) — **saha kanıtı sayılmaz**.
- İKA iz genişliği 0.4595 m **TAHMİN** (DDR'de yok, CONTRACTS §4.1); teker armature 0,01 kg·m² TAHMİN (fizik kararlılığı için, araclar.py); motor tork sınırı yok; modeller basitleştirilmiş (D-438 ek).
- `haritala` hesap süresi sim'de modellenmez (rota tarama biter bitmez yayınlanır); OBB araç maskesi kapalı.
- Yer işaretleri (İHA-İB, HB pedi/H, KB karesi) arena MJCF'inde 1–7 cm kalın **çarpışan** kutulardır; sürücü bunları yüklenen modelde çarpışmasız yapar (`isaretleri_carpismasiz_yap`) — MJCF/sha256 değişmez.
- `ika_nav.steer()` geri gitmez (teker hızı ≥ 0; pivot dönüş yok) — dokunulmadı, kayıt (CONTRACTS §4.1).
- `TURN_GAIN` 1,8: 1,3 m/s tabanda GT koşumlarında takip hatası ≤ 0,15 m ölçüldü (teşhis yörüngesi, 1 zor 43); değiştirilmedi.
- Temas koşumu **durdurmaz** (kayıt); başarı temas = 0 ister. Portlar yalnız ephemeral (127.0.0.1:0).

## 6. Kusur kayıtları (kanıtlı; REVIEW_LOG'a mimar taşır)

1. **Arena yerleşimi — GT merkez hattı engelle kesişiyor (T212 `arena_mjcf.yerlesim`).** Kapalı yol tıkamaları (`tikama_<yol>_<k>_<j>`, t = 0,30–0,80, u ∈ ±(lane_w/2+0,5), v ∈ ±1,8) yollar HB'ye yaklaşırken açık yolun hattına taşıyor; chicane'lar (`off ≥ clear+0,4`, ama 1,4× büyütülmüş 1,8–3,6 m yarı-boy plakalar, kıvrımlı hat) merkez hattı kesebiliyor. Ölçüm: yukarıdaki §3 tablosu ('temas ∧ geçilemez') ve §4 açıklık sütunu. Örnek (10 Eyl teşhis yörüngesi): `gt 1 zor 43` — `tikama_2_2_2` (yol 2 kapalı) açık yol 3 hattına 0,003 m; İKA 88,9 s'de takıldı, 600 s'e dek 6,6 m kala. Üretim planlayıcısı böyle rota ÜRETMEZ (R_GEREKLI 1,10 m); GT merkez hattı bu garantiyi taşımaz → **GT etiketli oran sürücü kusuru değil, rota inşaatının ölçümüdür**.
2. **`sim_hakem` sıra kusuru (düzeltildi, yeniden koşuldu).** İKA'nın OPEN_ROUTE ACK kopyası hakeme OPEN_ROUTE'tan ÖNCE gelince kanıt atılıyordu; İHA 'ika' ACK'ını gördüğü için İKA'ya tekrar göndermez → kopya bir daha gelmez → 2/2 asla, çıkış 3 (`gt 1 orta 44` ilk koşum: ack_listesi t=32,68 ACK, sonra ROTA_ALINDI). Erken kanıt seq ile saklanıp rota gelince eşleniyor (test E, mutasyonlu). İlk toplu koşumda 3/45 GT koşumu bu yüzden kod 3 verdi (`ilk_toplu_kosum_cikti.txt`: gt 1 orta 44, gt 2 zor 44, gt 5 orta 43); düzeltme sonrası yalnız bu üçü yeniden koşuldu (→ kod 4 temas/geçilemez, başarı, başarı), JSON'lar yenisidir. ⚠ **Üretim YKS'de aynı sıra:** `comms/yks_gui.py:2081` `if (self.rota and ref == self.rota['seq'] …)` — kopya rota'dan önce gelirse `ika_rota_ack`'a yazılmaz; İHA→YKS ilk datagramı kayıpsa tek yayınlı OPEN_ROUTE'ta 2/2 kilitlenir (sürekli yeniden yayında geçicidir). Mimar kararı: T216 alanı, burada DOKUNULMADI.
3. **Yer işaretleri çarpışan kutu** (arena MJCF, T213-A ile eş zamanlı düzenleniyor → MJCF'e dokunulmadı; sürücü modelde kapatıyor, `isaretler_carpismasiz` alanı JSON'da).

## 7. Komutlar

```
venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak gt    --res 1280 --tohumlar 42,43,44
venv python simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak model --res 1280 --tohumlar 42,43,44
venv python simulation/mujoco/gorev_kosumu.py --map 1 --level zor --seed 43 --rota-kaynak gt   # tek koşum
venv python simulation/mujoco/kosum_readme.py                                                  # bu README
venv python -B -m unittest discover -s tests -p test_sim_mujoco_zincir.py
```

Klasör: `<kaynak>_<h>_<lv>_<seed>.json` (metrik, git'te) · `<kaynak>_<h>_<lv>_<seed>/iha_scan/` (tarama kareleri/mozaik — **git dışı**, `--hepsi` ile bayt-eş yeniden üretilir; model koşumlarında `detection.json`/`rota.json` git'te).
