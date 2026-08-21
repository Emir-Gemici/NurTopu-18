# T131 · SÜRÜM-ÖTESİ KAYMA DEFTERİ

> Bu tablo bir **kapı değildir** ve eşik koymaz (T131 kısıtı).
> Amaç: taban taşıyan alanların terfiden terfiye nasıl hareket
> ettiğini **tek yerde görünür** kılmak (D-257 §4).

| tarih | model_id | imgsz | kabul_kumesi | kume parmak izi | kume dosya sayisi | K0 figur_zemin_orani | K0 figur (METINDEN) | K1 rota | K2 basma % | K3 agir % | K4 arena disi % | K5 bariyer px | karar cevrilmesi | gercek kare kaplama | gercek kare (ESKI ad) | cati kacagi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-01 | navitas-seg-v4-640 | 640 | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 2026-08-07 | navitas-seg-v4-640 | 640 | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| 2026-08-14 | navitas-seg-v27-512 | 512 | — | — | — | — | — | 255/260 | 7.1 | 0.0 | 0.4 | 0 | — | — | — | — |
| 2026-08-15 | navitas-seg-v27-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | — | — | 255/260 | 7.1 | 0.0 | 0.4 | 0 | — | — | — | — |
| 2026-08-15 | navitas-seg-v30-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | — | figur zemin %8,0 · raw 0/8 · cp 0/8 | 258/260 | 8.53 | 0.0 | 0.39 | 0 | 8/260 (%3,08) | — | 65/67 | — |
| 2026-08-19 | navitas-seg-v30-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | — | figur zemin %8,0 · raw 0/8 · cp 0/8 | 258/260 | 8.53 | 0.0 | 0.39 | 0 | 8/260 (%3,08) | — | 65/67 | — |
| 2026-08-19 | navitas-seg-v34-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | — | figur zemin %0,49 · raw bos 0/8 · cp bos 0/8 | 258/260 | 4.65 | 0.0 | 0.39 | 0 | 4/260 (%1,54) | 0.4551 | — | — |
| 2026-08-19 | navitas-seg-v34-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | 0.0049 | figur zemin %0,49 · raw bos 0/67 · cp bos 0/393 | 258/260 | 4.65 | 0.0 | 0.39 | 0 | 4/260 (%1,54) | 0.4551 | — | — |
| 2026-08-21 | navitas-seg-v35-512 | 512 | O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66 | — | — | 0.0903 | figur zemin %9.03 · raw bos 0/67 · cp bos 0/393 | 256/260 | 7.03 | 0.0 | 0.39 | 0 | 9/260 (%3,46) | 0.2855 | — | 0.0428 |

## K0 figür tabanı — TEK ALETLE bugün yeniden ölçüldü (119)

> Alet: `65_kabul_denetcisi.kaplama (ice aktarildi)` · CONF 0.3 · imgsz 512 · figür `data\arena_referans\sartname_s9_arena.png`
> Defterdeki değerler düz metne gömülüydü; bunlar **ölçümdür**.

| sürüm | figür zemin | not |
|---|---|---|
| v17 | 0.00% | ⚠ dönem-tutarlı değil (640 dönemi) |
| v20 | 0.00% | ⚠ dönem-tutarlı değil (640 dönemi) |
| v21 | 0.00% | ⚠ dönem-tutarlı değil (640 dönemi) |
| v24 | 34.64% | ⚠ dönem-tutarlı değil (640 dönemi) |
| v27 | 7.84% |  |
| v30 | 7.96% |  |
| v34 | 0.49% |  |
| v35 | 9.03% |  |

| terfi | taban | figür | oran | denetçinin bandı |
|---|---|---|---|---|
| v27 -> v30 | 7.84% | 7.96% | 1.02× | band içi — uyarı yok |
| v30 -> v34 | 7.96% | 0.49% | 0.06× | YETENEK (< 0,5 · daha az zemin) |
| v34 -> v35 | 0.49% | 9.03% | 18.29× | TEHLIKELI (> 2,0 · daha cok zemin) |

## Terfi geçişlerinde DEĞİŞEN alanlar

### navitas-seg-v4-640 -> navitas-seg-v27-512 · 2026-08-14 · `b4f8e402`
- **imgsz**: `640` → `512`
- **K1 rota**: `None` → `255/260`
- **K2 basma %**: `None` → `7.1`
- **K3 agir %**: `None` → `0.0`
- **K4 arena disi %**: `None` → `0.4`
- **K5 bariyer px**: `None` → `0`
- 🆕 **metrik alanı DOĞDU:** `_egitim`, `_kapsam`, `_kaynak`, `_mask_map50_notu`, `fitness_epoch200`, `k1_rota_uretimi`, `k2_moloza_basma_yuzde`, `k3_agir_basma_yuzde`, `k4_arena_disi_yuzde`, `k5_bariyer_kesisimi_px`
- ❌ **metrik alanı YOK OLDU:** `blocked_map50`

### navitas-seg-v27-512 -> navitas-seg-v30-512 · 2026-08-15 · `865f5910`
- **K0 figur (METINDEN)**: `None` → `figur zemin %8,0 · raw 0/8 · cp 0/8`
- **K1 rota**: `255/260` → `258/260`
- **K2 basma %**: `7.1` → `8.53`
- **K4 arena disi %**: `0.4` → `0.39`
- **karar cevrilmesi**: `None` → `8/260 (%3,08)`
- **gercek kare (ESKI ad)**: `None` → `65/67`
- 🆕 **metrik alanı DOĞDU:** `gercek_kare_gecen`, `k0_korluk`, `karar_cevrilmesi`

### navitas-seg-v30-512 -> navitas-seg-v34-512 · 2026-08-19 · `3cebce22`
- **K0 figur (METINDEN)**: `figur zemin %8,0 · raw 0/8 · cp 0/8` → `figur zemin %0,49 · raw bos 0/8 · cp bos 0/8`
- **K2 basma %**: `8.53` → `4.65`
- **karar cevrilmesi**: `8/260 (%3,08)` → `4/260 (%1,54)`
- **gercek kare kaplama**: `None` → `0.4551`
- **gercek kare (ESKI ad)**: `65/67` → `None`
- 🆕 **metrik alanı DOĞDU:** `_fitness_notu`, `gercek_kare_zemin_kaplamasi`
- ❌ **metrik alanı YOK OLDU:** `gercek_kare_gecen`, `mask_map50`

### navitas-seg-v34-512 -> navitas-seg-v35-512 · 2026-08-21 · `ee7508d7`
- **K0 figur_zemin_orani**: `0.0049` → `0.0903`
- **K0 figur (METINDEN)**: `figur zemin %0,49 · raw bos 0/67 · cp bos 0/393` → `figur zemin %9.03 · raw bos 0/67 · cp bos 0/393`
- **K1 rota**: `258/260` → `256/260`
- **K2 basma %**: `4.65` → `7.03`
- **karar cevrilmesi**: `4/260 (%1,54)` → `9/260 (%3,46)`
- **gercek kare kaplama**: `0.4551` → `0.2855`
- **cati kacagi**: `None` → `0.0428`
- 🆕 **metrik alanı DOĞDU:** `cati_kacagi`

