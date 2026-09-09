# Doku kaynakları — GERÇEK eğitim karelerinden

Üreteç: `uret_karolar.py` (tablo oradaki `KAYNAKLAR` sözlüğüyle birebir). Amaç: MuJoCo
arenasında zemin/yol/moloz yüzeyleri, üretim modelinin (v36) eğitimde gördüğü türden
GERÇEK fotoğraf dokusu taşısın (K3 ön-ölçümü render karede yol/moloz ayrımını ölçer).

| dosya | kaynak kare (eğitim kümesi) | piksel kutusu (x0,y0,x1,y1) | ne |
|---|---|---|---|
| `toprak_kaynak.png` (900×1800) | `dataset/dji_kirsal/images/train/dji_20260822170832_0037_d__frame_000170_000006630.jpg` | 2900,100,3800,1900 | kumlu toprak / stabilize zemin (tekerlek izli), nadir, DJI 0037 |
| `stabilize_kaynak.png` (500×900) | `dataset/dji_kirsal/images/train/dji_20260822170832_0037_d__frame_000003_000000090.jpg` | 60,250,560,1150 | gri çakıl/stabilize yol yüzeyi, nadir, DJI 0037 |
| `asfalt_kaynak.png` (300×90) | `data/raw_frames/whatsapp_video_2026_07_30_at_11_44_03/frame_000000_000000000.jpg` (depoda) | 700,240,1000,330 | asfalt otopark zemini, gerçek nadir drone karesi (`gercek_otopark` eğitim kaynağı) — yalnız **TEŞHİS** varyantı (`--yol-dokusu asfalt`) |
| `moloz_a.png` (1024², 2×2 aynalı) | `dataset/rescuenet_11sinif/images/train/12275.jpg` | 430,150,730,400 | yoğun kırık enkaz, gri-kahve |
| `moloz_b.png` (1024², 2×2 aynalı) | `dataset/rescuenet_11sinif/images/train/11237.jpg` | 10,370,310,670 | ahşap/beton kırık enkaz |
| `bariyer.png` (256²) | — | — | **PROSEDÜREL** kırmızı-beyaz şerit (fotoğraf değil) |

`dataset/` git dışıdır; kaynak kareler `O:/navitas/dataset/...` altında durur. DJI 0037/0039
**eğitim** kümesidir (`dataset/karisim_dji_kirsal.yaml`); 0038 bakır doğrulama kümesine
**dokunulmadı**. RescueNet kareleri `rescuenet_2sinif_engelli` eğitim kaynağının aslıdır.
`data/arena_referans/sartname_s9_arena.png` (tek gerçek arena karesi) **kullanılmadı**
(KAYNAK.md kuralı: doğrulama değeri korunur).

## Kullanım (arena_mjcf.py)

- HTAB zemini: `toprak_kaynak` bölgesinden deterministik rastgele 512 px yamalar,
  yükseltilmiş-kosinüs pencereyle torus-sarmalı bindirilir (`_yama_dokusu`) → 2048² doku,
  **ayna/kaleydoskop yok**. Yol şeridi `arena.harita` spline'ı boyunca `stabilize_kaynak`
  yamasıyla boyanır (şerit genişliği `world_generator.DIFF[lv]["lane_w"]`).
- İHA-UB zemini: aynı yöntemle 1024² dikişsiz karo (`uretilen/ub_toprak.png`), 12×12 tekrar.
- Moloz kutuları: `moloz_a` / `moloz_b` cube dokusu, materyal tonu ile 3 varyant.
- `uretilen/` git dışıdır; ilk çağrıda üretilir, aynı girdi → bayt-eş PNG.
