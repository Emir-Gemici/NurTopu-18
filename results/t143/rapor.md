# T143 — kayıt defteri türevleri + kamera düşen-kare sayacı (D-284, T18 çürütücüsü)

Tarih: 2026-08-26 · worktree `wf_0c06347c-47a-2` (HEAD f1c5931) · yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`

## Değişen dosyalar
- `codes/karar_sozlesmesi.py` (+ ayna `jetson_paket/kod/`): `KAMERA_DUSEN_KARE_UST_SINIRI=30`, `KAMERA_DUSEN_KARE_BEKLEME_S=0.02`, `KAMERA_BITIS_*`, `MODEL_TUREV_SHA_YER_TUTUCU="DERLENINCE_YAZILIR"` — gerekçeli.
- `codes/model_registry.py`: `turev_dogrula`, `sha256_dogrulanmis_mi`, `resolve_model(turev=...)`, `turev_kaydet` + CLI `--turev-kaydet <dosya> [--kaynak-pt PT]` (paket aynasını bayt-eş yazar).
- `codes/rpi_inference.py` (+ ayna): `model_kayit_dogrula` ad uyuşmazlığında `_turev_kayit_dogrula`ya düşer; `kamera_kareleri` üreteci (sayaç + üst sınırlı yeniden deneme + log), `run_camera` özet döndürür ve `KAMERA BITIS:` satırı basar.
- `config/model_registry.json` (+ ayna): `competition.turevler` — 2 `.engine` yer tutucu (RED), 2 `.onnx` GERÇEK sha256 (CLI ile, `--kaynak-pt` .pt özeti kıyaslanarak yazıldı). `competition.path` ve `.pt` sha256 DEĞİŞMEDİ.
- `JETSON_KILAVUZ.md` (+ ayna): §4b `--turev-kaydet` yordamı. `--kayit-dogrulamasiz` komut satırı olarak YAZILMADI (test kilitler).
- `tests/test_t143_turev_ve_kamera.py`: 28 test.

## Gerçek dosya ölçümü (worktree defteriyle, kok=.)
```
True turev_eslesti O:/navitas/models/navitas_seg_v35_best.onnx
True turev_eslesti O:/navitas/jetson_paket/models/navitas_seg_v35_best_512_fp16.onnx
True eslesti O:/navitas/models/navitas_seg_v35_best.pt
False ESLESMIYOR O:/navitas/jetson_paket/models/navitas_seg_v27_best.pt
False TUREV SHA YER TUTUCU (dogrulanmamis) O:/navitas/models/navitas_seg_v35_best.engine
```
CLI çıktısı: `eski_sha256: DERLENINCE_YAZILIR -> yeni_sha256: 248ef808f8be20d7...` (iki onnx aynı özet, aynı dosya).

## Kapılar
- `codes/test_rota_sentetik.py` → `SONUC: 15/15 dogru`
- `unittest discover -s tests -q` → `Ran 793 tests … FAILED (failures=1, skipped=13)`; tek düşen `test_yks_gui_uretim_hizasi.test_kompozit_dizini_listeleniyor` (worktree'de `data/arena_kompozit` yok) — **stash ile baseline'da da aynı düşüyor** (ortam, kod değil). Worktree'de v35 `.pt` de yoktur; `models/` altına gitignore'lu kopya konarak `test_saha_parametrik` 20 OK, `test_imgsz_tek_kaynak` 9 OK, `test_model_registry` 4 OK doğrulandı.
- İkiz: `diff codes/{rpi_inference,karar_sozlesmesi}.py jetson_paket/kod/` ve `diff config/model_registry.json jetson_paket/config/` → boş.

## Mutasyon (TEST_SPECS §4.1)
1. `ozet["dusen_toplam"] = …` satırı `pass` yapıldı → `FAILED (failures=6, errors=2)` (sayaç testleri düştü). Geri alındı.
2. `_sha256_dogrulanmis_mi` → `return True` → `FAILED (failures=3)` (yer tutucu testleri düştü). Geri alındı.
3. `if gercek != kayit["sha256"]` → `if False` → `FAILED (failures=1)` (`test_sha_UYUSMAZSA_RED`). Geri alındı.
(İlk deneme: yer tutucuyu yalnız `len!=64` kıyasından çıkarmak testleri DÜŞÜRMEDİ — yer tutucu hex olmadığı için zaten reddediliyor; daha sert mutasyon 2 uygulandı.)

## ÖLÇÜLEMEDİ (cihaz yok)
Gerçek DroidCam/USB kamera ile düşen kare davranışı ve Jetson'da derlenmiş `.engine` yüklemesi — H3/Jetson günü.
