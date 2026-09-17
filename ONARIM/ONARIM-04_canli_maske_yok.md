# ONARIM-04 — Canlı kamerada her karar MASKE_YOK

**Durum:** SÜRÜYOR — kök neden adayı **ölçüldü** (lens odağı); odak ayarı sonrası aynı sahnede yeniden ölçüm bekleniyor.
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 04 · **Ham kanıt:** `results/onarim/onarim04_maske_yok/`

## Sorun
15 Eylül'de IMX219 ve IMX477 ile canlı kameradan gelen kararların **tamamı** `MASKE_YOK` (ofis, ekranda yol dahil; D-491 §5). Aynı model `--image` ile kayıtlı karelerde maske üretiyordu. 17 Eylül ONARIM-03 görev kaydı ilk kez cihazda ölçtü: 37/37 karede `zemin_px = 0`, `engel_px ≈ %97,5`.

## Ayırt edici deneyler (Jetson, v36 `.pt`, 17 Eylül)
| Deney | Ne | Sonuç |
|---|---|---|
| **A** doğrudan | 36 DJI + 15 WhatsApp karesi, `run_camera` ile **aynı** `_preprocess → predict → get_masks → _maskeleri_icerige_kirp` (`onarim04_a.py`) | DJI **32/36** karede zemin, ort. zemin %20,2 · engel %7,7 · WhatsApp **15/15**, zemin %25,5 |
| **B** canlı hat | Aynı 36 DJI karesi → MJPG avi → `kamera_koprusu --kaynak dosya --fps 2` → `rpi_inference --camera --gorev-kaydi` (73 kare) | **65/73** karede zemin, ort. zemin %20,3 · engel %7,4 → **A ile aynı**. Red dağılımı: HEDEF_YOK 46 · OLCEK_YOK 9 · UC_BANT_TEMAS_YOK 8 · MASKE_YOK 8 · GORUS_HATTI_KOPUK 2 |
| **C** bulanıklık | DJI karelerine Gauss σ ∈ {0,2,5,10,20,40} (`onarim04_c.py`) | zemin>0 kare: σ0 **32/36** · σ2 23 · σ5 5 · σ10 **0** (engel %96,1) · σ20 0 · σ40 0 |
| **C** gerçek IMX477 | 17 Eyl 10:58 karesi, 15 Eyl `imx477_hd_auto` | zemin **%0**, engel **%89,4 / %99,4** |
| **D** keskinlik | Laplace varyansı, uzun kenar 640 px (`onarim04_d.py`) | DJI medyan: σ0 3369 · σ1 582 · σ2 67 · σ3 16 · σ5 3,7 · σ10 1,9 — WhatsApp: σ0 1373 · σ2 66 · σ3 20 · σ10 2,2 — **IMX477 17 Eyl: 1,5 · 15 Eyl hd_auto: 2,3** (σ≈10 bölgesi) · IMX219 kareleri 129 / 177 |

## Sonuç (KESİN olan / MUHTEMEL olan)
- **KESİN:** Köprü + MJPEG + `--camera` hattı maskeyi bozmuyor (A ≡ B).
- **KESİN:** Model ağır bulanıklıkta zemini kaybedip kareyi ENGEL sayıyor; canlı imzanın aynısı (zemin 0, engel ~%96–97).
- **KESİN:** Canlı IMX477 karelerinin keskinliği σ≈10 bulanıklık düzeyinde.
- **MUHTEMEL (test edilecek):** IMX477 + 6 mm lensteki MASKE_YOK'un kök nedeni **odak dışı lens** (CS/C adaptör arka odak ya da halka). Katkı: ofis sahnesinde yol yok. 15 Eylül IMX219 kareleri (keskinlik 129/177) keskin olduğu halde MASKE_YOK verdi → orada neden sahne (hava görüntüsü değil) olabilir; **ayrıca ölçülmedi**.
- Güvenlik yönü: bulanık kare → ENGEL → NO_ROUTE = **fail-closed** (İKA yanlış yöne gitmez, ama hiç rota da çıkmaz).

## Yapılanlar (yazılım)
- `codes/kare_keskinligi.py` — `kare_keskinligi()` + bantlar NET ≥100 · ŞÜPHELİ 20–100 · BULANIK <20 (**ön kayıt**, deney D'den). Karar yolunu etkilemez.
- `rpi_inference` görev kaydı `KARE` satırına `keskinlik` alanı (ONARIM-03 kaydı). `run_camera` satır sayısı değişmedi (atıflar sabit).
- `scripts/kamera_odak_olcer.py` — köprünün `/kare.jpg` ucundan ya da dosyadan canlı keskinlik; çıkış 0 NET / 1 değil / 2 ölçülemedi.
- `scripts/tezgah/odak_onizleme.py` — Jetson monitöründe CSI önizleme + büyük keskinlik/EN İYİ göstergesi (tezgâh aracı). 17 Eyl 11:52'de Jetson `DISPLAY=:1`'de başlatıldı; kullanıcı lensi uzaktan vida ile sabitliyor.
- `tests/test_onarim04_keskinlik.py` — 7 test.

## Kanıt (testler)
```
test_onarim04_keskinlik OK (7) · test_onarim03_gorev_kaydi OK · test_faz_b_rpi_ekransiz OK
test_rpi_canli_olcek OK · test_fdr_t244_ic_celiski OK · test_p5_histerezis OK
```

## Kalan
1. Odak ayarı sonrası: `odak_onizleme` EN İYİ değeri + aynı sahnede `rpi_inference --gorev-kaydi` → `zemin_px`, `keskinlik` karşılaştırması. NET bandında hâlâ zemin 0 ise neden sahne/model (ofis ≠ hava görüntüsü) → uzak dış sahne ya da ekranda DJI karesi ile test.
2. Öneri (mimar kararı, **uygulanmadı**): keskinlik BULANIK iken ayrı bir red nedeni (`KAMERA_BULANIK`) YKS'ye taşınsın mı? Şu an NO_ROUTE nedeni `MASKE_YOK` görünüyor ve operatörü yanlış yöne (model/zemin) bakmaya itiyor. CONTRACTS §6 red kodu değişikliği gerektirir.
3. Öneri: saha öncesi kontrol listesine `kamera_odak_olcer --sure 10` → NET şartı.
