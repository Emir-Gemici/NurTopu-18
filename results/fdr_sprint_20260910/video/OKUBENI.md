# H1-K7 · T214-B — MuJoCo görev icra simülasyonu videosu

> **SENTETİK** — MuJoCo simülasyonu; saha kanıtı değildir. Bu dosya `simulation/mujoco/sim_video.py` ile `video_ozeti.json`'ndan üretilir, elle düzenlenmez (nöbetçi `tests/test_sim_mujoco_video.py`). mp4 **git dışıdır** (`.gitignore`: `*.mp4`, `results/**/*.mp4`); yerel dosya aşağıdaki sha256 ile tanınır.

| alan | değer | eşik (ON_KAYIT H1-K7) | hüküm |
|---|---|---|---|
| dosya | `results/fdr_sprint_20260910/video/navitas_sim_gorev_20260910.mp4` | mp4 yazıldı | VAR |
| sha256 | `35ffc33e2f99c8335a7c4fe581cea257e294baea57f6f1edcd1fe1089139347d` | — | — |
| süre | 177.88 s (4447 kare) | ≥ 90 s | GEÇTİ |
| kare hızı | 25 FPS | ≥ 24 FPS | GEÇTİ |
| çözünürlük | 1280×720 (fourcc `h264`) | — | 1280×720 |
| boyut | 33.56 MB | < 60 MB (görev tanımı) | GEÇTİ |
| kameralar | IHA NADIR KAMERA (tarama, 30 m) · UCUNCU SAHIS (arena genel) · IKA TAKIP KAMERASI | üç kamera | GEÇTİ |
| HUD | sim saati · faz FIRLATMA/TARAMA/ROTA/AKTARIM/IKA_GO/SURUS/VARIS · rota kaynağı etiketi (YER GERCEGI / URETIM MODELI) · OPEN_ROUTE ACK [ika,yks] · IHA_LANDED · IKA_GO · IKA_GO ACK · İKA→HB mesafesi · temas · oynatma hızı · SENTETİK | HUD'lu | VAR |
| link | BEYAN GEREKLİ (insan — YouTube liste dışı / Drive; T222) | yönerge `Y-3.3.3-M03` linki ister | **AÇIK** |

## Koşumlar (her biri `gorev_kosumu.kos(..., kare_kaydet=True)`; üç kamera 25 Hz sim saati)

| # | koşum | rota kaynağı | başarı | sürüş sim-s | görev sim-s | varış m | temas | kosum_tur3 eşliği | seçim |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `kosum/model_1_kolay_44.json` | ÜRETİM MODELİ | ✓ | 63.4 | 100.58 | 0.273 | 0 | 11/11 alan eş | birincil |
| 2 | `kosum/model_3_orta_42.json` | ÜRETİM MODELİ | ✓ | 65.9 | 103.18 | 0.251 | 0 | FARK: sure_sim_ika=65.9↔65.8, varis_mesafesi_m=0.251↔0.261 | birincil |
| 3 | `kosum/model_5_zor_42.json` | ÜRETİM MODELİ | ✓ | 63.6 | 100.88 | 0.259 | 0 | 11/11 alan eş | birincil |

Eşlik alanları: `basari`, `rota_bulundu`, `rota_dogru`, `model_yol`, `model_guven`, `cikis_kodu`, `temas_sayisi`, `hb_icinde`, `wp_sayisi`, `sure_sim_ika`, `varis_mesafesi_m` — video koşumu aynı harita/seviye/tohumun `kosum_tur3` JSON'uyla karşılaştırılır. `rota.json` eşliği: model_1_kolay_44 eş · model_3_orta_42 FARKLI · model_5_zor_42 eş. Model koşumunda rota GPU render'lı mozaikten gelir (kareler koşumdan koşuma ~%50 bayt-eş, T213-A ölçümü); rota farklıysa sürüş farkı rotadandır — kaydedicinin kendisi aşağıdaki değişmezlik koşumuyla sınanır.

## Kaydedici fizik değişmezliği (ölçüm)

YER GERÇEĞİ koşumu `gt_1_kolay_42` (rota render'dan bağımsız) kareli koşuldu ve `results/fdr_sprint_20260910/H1/kosum_tur3/gt_1_kolay_42.json` ile 20 alanda karşılaştırıldı: **hepsi eş** (kare 2540; `kosum/degismezlik.json`).

**Ölçülen ve düzeltilen kusur (ilk video koşumu, `results/fdr_sprint_20260910/video/ilk_kosum_kare_bekle_sonu/`):** kare bekle sonunda çiziliyordu → mj_forward xpos'u tazeledi → denetleyici 2 ms taze poz okudu (olay zamanları eş); düzeltme: kare yalnız alt-adım öbeğinin başında (gorev_kosumu.surus_adimla). Alanlar [ilk video koşumu, kosum_tur3]:

| koşum | sürüş sim-s | varış m | takip maks m | IKA_GO ACK t |
|---|---|---|---|---|
| model_1_kolay_44 | 63.4 ↔ 63.4 | 0.286 ↔ 0.273 | 1.016 ↔ 1.012 | 37.27999999999964 ↔ 37.27999999999964 |
| model_3_orta_42 | 65.7 ↔ 65.8 | 0.256 ↔ 0.261 | 1.752 ↔ 1.751 | 37.27999999999964 ↔ 37.27999999999964 |
| model_5_zor_42 | 63.4 ↔ 63.6 | 0.263 ↔ 0.259 | 1.636 ↔ 1.626 | 37.27999999999964 ↔ 37.27999999999964 |

## Videodaki genel sayılar (giriş kartı; ölçüm JSON'larından)

- H1-K3 mozaik zinciri doğru etiket 6/15 · üretim kare-bazlı 1/15 (eşik 12/15, ikisi de DÜŞTÜ)
- H1-K5 YER GERÇEĞİ 45/45 (harita 15/15) · ÜRETİM MODELİ 9/45 (harita 0/15) · ÜRETİM BORU HATTI 0/15
- Kaynak: `results/fdr_sprint_20260910/H1/kosum_tur3/ozet_kosum.json`, `results/fdr_sprint_20260910/H1/k3_uretim_boru/ozet_k3_uretim.json`. Videodaki 3 koşum **başarılı** koşumlardır ve bu girişte açıkça yazılıdır; genel oranın yerine geçmez.

## Bölümler (video saniyesi)

| bölüm | başlangıç s | bitiş s | faz → video karesi |
|---|---|---|---|
| giris_karti | — | — | kart 8 s |
| model_1_kolay_44 | 8.0 | 61.36 | FIRLATMA 98 · TARAMA 302 · ROTA 100 · AKTARIM 130 · SURUS 529 · VARIS 75 |
| model_3_orta_42 | 61.36 | 116.0 | FIRLATMA 98 · TARAMA 302 · ROTA 100 · AKTARIM 130 · IKA_GO 12 · SURUS 549 · VARIS 75 |
| model_5_zor_42 | 116.0 | 169.88 | FIRLATMA 98 · TARAMA 302 · ROTA 100 · AKTARIM 130 · IKA_GO 12 · SURUS 530 · VARIS 75 |
| cikis_karti | — | — | kart 8 s |

Oynatma hızı (HUD'da her karede yazılı): FIRLATMA 2× · TARAMA 2× · AKTARIM 1× · IKA_GO 0.25× · SURUS 3× · ROTA kartı sim saatini dondurur (`iha_haritala` hesap süresi sim saatine eklenmez).

## Üretim komutu

```
O:/navitas-local-train/venv/Scripts/python.exe -B simulation/mujoco/sim_video.py --kos
O:/navitas-local-train/venv/Scripts/python.exe -B simulation/mujoco/sim_video.py --birlestir
```

Ana kopya: `cv2.VideoWriter` fourcc `mp4v` (FFMPEG) → `results/fdr_sprint_20260910/video/navitas_sim_gorev_20260910_cv2_mp4v.mp4` (124.58 MB, sha256 `268eac1b373d01fe93a0e731a77d889c637247c8ada2c1889b128e8aba5fad54`; git dışı).
Teslim dosyası H.264'e dönüştürüldü (libx264 CRF 23 · preset medium · yuv420p · 25 FPS): `ffmpeg -y -hide_banner -loglevel error -i results/fdr_sprint_20260910/video/navitas_sim_gorev_20260910_cv2_mp4v.mp4 -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -r 25 -movflags +faststart -an results/fdr_sprint_20260910/video/navitas_sim_gorev_20260910.mp4` — ffmpeg version 2026-02-02-git-7e9fe341df-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers. Neden (ölçüldü): bu cv2 derlemesinde mp4v bit hızı ayarlanamıyor (`OPENCV_FFMPEG_WRITER_OPTIONS` etkisiz, 5,82 MB / 10 s), ana kopya 60 MB sınırını aşıyor. Kareler ana kopyayla aynıdır; yalnız sıkıştırma değişir.
Özet tarihi: 2026-09-10 17:02.

## Sınırlar

- İHA uçuşu KİNEMATİK (mocap, aerodinamik yok); hakem onayı sim'de OTOMATİK (`sim=true`); İKA iz genişliği 0,39 m TAHMİN; modeller BASİTLEŞTİRİLMİŞ (sabit kanat mesh, DDR ölçülü İKA). GPU render kareleri koşumdan koşuma ~%50 bayt-eş (T213-A ölçümü) — video yeniden üretildiğinde sha256 değişir, sayılar değişmez.
- Link yoktur: yükleme İNSAN işidir (T222). Link gelene kadar `Y-3.3.3-M03` KISMEN.
