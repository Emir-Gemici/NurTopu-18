# T135 + T143 KALINTILARI — uygulama raporu (2026-08-26)

Kaynak: REVIEW_LOG D-268 §6 · results/t142/olcum.md §3/§5 · results/t143/rapor.md (çürütücü kusurları 1–3).
Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`. Worktree: `wf_46c3db35-640-4` (master 542b589 üstüne).

## A · T135

| # | yer | değişiklik |
|---|---|---|
| A1 | `jetson_paket/kod/kamera_dogrula.py` | Zincir modül düzeyinde `zincir_durumu(bgr, tahmin_maskeleri, *, rota_bul, preprocess, kirp)` oldu; `rota_bul(..., icerik=icerik)` **geçiriliyor** (`icerik` `_preprocess` üçüncü dönüşü). `codes/` altında ayna YOK (dosya yalnız pakette). |
| A2 | `codes/costmap_path_finder.py` (+ ayna) | `rota_bul` artık `_rota_bul_cekirdek` sarmalayıcısı. `letterbox_suphesi(maskeler, icerik)`: `icerik=None` + kare tuval + en az bir maske pikseli + üst+alt (ya da sol+sağ) bantların ikisi de tüm maskelerde boş → `cikti["uyari"]=ICERIK_YOK_LETTERBOX_SUPHESI`, `sebep`e not eklenir, `logger.warning`. **Karar değişmez** (durum/yol_no/guven/waypoints çekirdekle birebir — testle kilitli). |
| A2 | `codes/karar_sozlesmesi.py` (+ ayna) | `ICERIK_YOK_LETTERBOX_SUPHESI_NOTU`, `LETTERBOX_SUPHE_BANT_ORANI = 0.10` (gerekçe yorumda: 4:3 → 0,125, 16:9 → 0,219 boş bant). Ret sebebi DEĞİL (ROTA_RET_SEBEPLERI'ne eklenmedi) — yalnız not. |

Ölçüm (test içinde): 320x180 kare → tuval 320x320, içerik (0,70,320,180). Çöküş maskesi (içeriğin tamamı zemin), kırpılmış:
- `icerik=None`: kaplama = 0,5625 ≤ 0,67 → kapı SUSAR (kusur belgelendi: `test_icerik_gecirilmezse_kapi_OLU_kalirdi`).
- `icerik` geçirilince: durum = `ZEMIN_MASKESI_SUPHELI` (kapı ATEŞLER).

## B · T143 çürütücü kusurları

| # | değişiklik |
|---|---|
| B1 | `model_registry.turev_kaydet`: `kaynak_pt=None` → `ModelRegistryError("--kaynak-pt ZORUNLU: ...")`; CLI `--kaynak-pt` help "ZORUNLU". CLI'de ayrı bir ön kontrol yazılmıştı; mutasyonda **eşdeğer** çıktı (fonksiyon zaten RED veriyor, `_cli` 1 döner) → gereksiz kod kaldırıldı, tek kaynak fonksiyon. |
| B2 | `tests/test_t143_turev_ve_kamera.py::_SahteKamera`: çağrı tavanı `len(senaryo) + 10×ust_sinir`; aşılınca `RuntimeError`. M6 mutasyonu artık ASILMIYOR, DÜŞÜYOR (8 hata, aşağıda). |
| B3 | `resolve_model(..., calisan_imgsz=None)` → `turev_dogrula(..., calisan_imgsz=...)` iletiliyor. |

Test notu: üretim `.pt` worktree'de yok; `_GeciciKok.sha_vekili()` yalnız vekil `.pt` dosyası + vekil içerik için `MR._sha256`'yı `URETIM_SHA`'ya yamar, diğer tüm dosyalar gerçek özet (yanlış-kaynak testi bu yüzden hâlâ RED verir).

## Kapılar (gerçek çıktı)

```
codes/test_rota_sentetik.py            SONUC: 15/15 dogru  [OK] TUM DETERMINISTIK SAHNELER GECTI
unittest discover -s tests -q (TABAN, git stash -u)   Ran 855 tests  FAILED (failures=4, errors=11, skipped=16)
unittest discover -s tests -q (SONRA)                Ran 865 tests  FAILED (failures=4, errors=11, skipped=16)
düşen küme diff (taban vs sonra): BOŞ → aynı 15 ortam düşüşü (model/veri worktree'de yok:
  test_imgsz_tek_kaynak×2, test_model_registry×1, test_saha_parametrik×7, test_t123_gecis_provasi×4, test_yks_gui_uretim_hizasi×1)
tests/test_t135_kamera_dogrula_icerik.py   Ran 8 tests   OK
tests/test_t143_turev_ve_kamera.py         Ran 30 tests  OK   (önce 28; +2)
tests/test_t134_rota_bul_zemin_kapisi.py   Ran 12 tests  OK
ayna ikizliği (diff -q): costmap_path_finder / karar_sozlesmesi / rpi_inference → IKIZ (boş diff); test_paket_aynalari_ikiz ile de kilitli
```

## Mutasyon kanıtı (`scratchpad/mutasyon_t135_wt4.py`; her biri koştu, bayt-eş geri alındı)

```
== M-A1 kamera_dogrula: icerik=icerik KALDIRILDI
   FAIL: test_letterboxlu_16_9_karede_kapi_ATESLER · ERROR: test_zincir_kirpmayi_ve_icerigi_URETIMDEN_alir
   Ran 8  FAILED (failures=1, errors=1)   geri alindi bayt-es: True
== M-A2 costmap: letterbox_suphesi hep False (codes + ayna birlikte)
   FAIL: test_icerik_None_letterboxta_NOT_ve_uyari
   Ran 8  FAILED (failures=1)   geri alindi bayt-es: True  ayna bayt-es: True
== M-B1 model_registry: kaynak_pt None kontrolu KALDIRILDI
   ERROR: test_turev_kaydet_KAYNAK_PT_YOKSA_RED
   Ran 30 FAILED (errors=1)   geri alindi bayt-es: True
== M6 rpi_inference: `if ardisik >= ust_sinir` KALDIRILDI (T143 raporunda bu mutasyon ASILIYORDU)
   8 × RuntimeError: _SahteKamera: cagri tavani asildi (30/53/54/56/60/300/302) — kamera dongusu ust sinirda BITMIYOR
   Ran 30 FAILED (errors=8) — 0,9 s, asılmadı   geri alindi bayt-es: True  ayna bayt-es: True
== M-B3 model_registry: resolve_model calisan_imgsz ILETILMIYOR
   FAIL: test_resolve_model_turev_CALISAN_IMGSZ_iletir
   Ran 30 FAILED (failures=1)   geri alindi bayt-es: True
```

İlk M-A2 koşumunda yalnız ikiz testi düştü: test `sys.path`e paket dizinini `codes`'un önüne koyuyordu, üretim modülü aynadan yükleniyordu. Düzeltildi (`codes/` önde) ve mutasyon codes+ayna birlikte uygulanır oldu; sonuç yukarıda.

## ÖLÇÜLEMEDİ
- Gerçek kamera + gerçek model ile `kamera_dogrula --zincir` koşumu (worktree'de model yok, GPU işi yasak). Kapının ateşlediği sentetik çöküş maskesiyle gösterildi.
- CONTRACTS.md değişikliği: YOK (yeni mesaj tipi yok; `uyari` alanı `rota_bul` çıktısına eklenen isteğe bağlı bir anahtardır, sebep koduna eklenmedi).
