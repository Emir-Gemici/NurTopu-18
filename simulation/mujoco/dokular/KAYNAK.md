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
| `yol_serit_kaynak.png` (678×620) | DJI 0037 kare 3 (yukarıdaki) | döndür (766,826; 49,51°) → 483,927,1161,1547 | **V1 yol şeridi**: stabilize/çakıl yol, ekseni DİKEY, 4,0 m enine × 3,7 m boyuna (T213-A) |
| `banket_kaynak.png` (220×450) | DJI 0037 kare 3 | aynı döndürme → 1165,1150,1385,1600 | **V1 banket**: yolun hemen sağındaki kuru ot şeridi, iç kenar = yol kenarı, 1,3×2,7 m |
| `zemin_toprak_kaynak.png` (600×700) | DJI 0037 kare 3 | 0,0,600,700 | sıkıştırılmış toprak/kum — ⚠ eğitim etiketinde **traversable**; `--zemin-dokusu zemin_toprak` (karşılaştırma) |
| `zemin_surulmus_kaynak.png` (1800×700) | `dji_20260822170832_0037_d__frame_000018_000000660.jpg` | 1500,0,3300,700 | **V1 zemin (varsayılan)**: sürülmüş kahverengi toprak, eğitim etiketinde **arka plan** (yol değil); 11,4×4,4 m |
| `asfalt_yol_kaynak.png` (80×290) | otopark karesi (yukarıdaki) | 570,285,860,365 → 90° döndürülmüş | **V1 `--yol-dokusu asfalt`** şeridi; ölçek TAHMİN ≈10 cm/px |

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

## §GSD — kaynak ölçekleri (T213-A, 10 Eylül; `arena_mjcf.KAYNAK_MPP`)

DJI 0037 SRT (`dji/DJI_20260822170832_0037_D.SRT`, `rel_alt`): kare 3 (90 ms) **16,3 m**, kare 18
(660 ms) **17,5 m**, kare 170 (6630 ms) **29,7 m**. Yatay FOV varsayımı **69,7°** (DJI Fly serisi
82,1° diyagonal, 4:3 sensör; çapraz kontrol: yol şeridi 678 px × 0,591 cm/px = 4,0 m — kırsal
stabilize yol genişliği). `mpp = 2·h·tan(34,85°)/3840`:

| kaynak | irtifa | m/px |
|---|---|---|
| kare 3 (yol şeridi, banket, zemin_toprak) | 16,3 m | 0,00591 |
| kare 18 (zemin_surulmus) | 17,5 m | 0,00634 |
| kare 170 (toprak_kaynak — taban) | 29,7 m | 0,01083 |
| otopark (asfalt) | ? | ≈0,10 (TAHMİN, araç boyu) |

**Taban (T212) dokusunun ölçek kusuru (ölçüldü):** HTAB dokusu 2048 px / 50 m = 2,44 cm/px.
`_yama_dokusu(..., 512, olcek)` kaynaktan 512/olcek px alıp 512 px'e döşer → zemin
(`toprak_kaynak`, olcek 1,0): 512 px × 1,08 cm = 5,5 m gerçek alan 12,5 m'ye → **2,26×
büyütme**; yol (`stabilize_kaynak`, olcek 1,4): 366 px × 0,59 cm = 2,2 m → 12,5 m → **5,8×
büyütme**. Yani taban mozaikte çakıl/tekerlek izi gerçekten 2–6 kat iri görünür. Ayrıca
`toprak_kaynak` kırpması (kare 170, x 2900–3800) eğitim etiketinde **YOL (traversable)**
bölgesidir — taban zemini modelin "yol" öğrendiği yüzeydir, yol şeridi ise 5,8× büyütülmüş
açık gri banttır. V1 bunları düzeltir: yama = 128 px (3,1 m) ↔ kaynaktan 128/olcek px
(olcek = kaynak_mpp/2,44 cm ≈ 0,24–0,26 → ~490–530 px), INTER_AREA ile küçültülür.

Zemin seçimi gerekçesi: şartname s.9 "toprak/kum". Kare 3'ün sıkıştırılmış toprağı eğitimde
traversable etiketli (üç yol + zemin hepsi "yol" olurdu → tek kapı); kare 18'in sürülmüş
toprağı arka plan etiketli. Gerçek arenada zemin ile yol yüzeyi AYNI olabilir (fotoğrafta
öyle) — o durumda üç güzergâh molozla ayrılır; sim bu abstraksiyonu (ayrı yol dokusu)
T212'den devralır ve RAPOR_K3B §sınırlar'da yazılıdır.
