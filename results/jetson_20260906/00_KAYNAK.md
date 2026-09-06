# results/jetson_20260906 — 6 Eylül 2026 Jetson Orin Nano oturumunun ham çıktıları

Kaynak: `GELISTIRICIYE_20260906/GELISTIRICIYE_20260906/` paketi (takım üyesinin Jetson'daki oturumu,
6 Eylül 17:05–19:30; 7 Eylül 01:47'de depoya açıldı, gece G0a işiyle master'a taşındı). Kayıt:
`REVIEW_LOG.md` **D-431** (pakette D-428 numarasıyla yazılmıştı; master'daki D-428/429/430 ile
çakıştığı için D-431). Dosyalar paketin `kanit/` ağacından **değiştirilmeden** kopyalandı; yalnız
iki anlatım belgesi (`JETSON_KESIF_RAPORU_20260906.md`, `JETSON_KURULUM_SURECI_20260906.md`)
başa bir taşıma notu aldı ve D-428 → D-431 / yol atıfları buna göre çevrildi.

| dosya / dizin | ne |
|---|---|
| `ORTAM_KUNYESI.txt` | kartta ölçülen künye: Orin Nano DevKit 4 GB, L4T R39.2.1 (JetPack 7.2.1), Ubuntu 24.04.4, Python 3.12.3, torch 2.11.0, tensorrt 10.16.2.10, ultralytics 8.4.142 |
| `orin_nano_root_kurulum.log`, `orin_nano_venv_kurulum.log` | `scripts/orin_nano_*.sh` koşum logları |
| `jetson_log_20260906/genel_kapi.log` | madde 14 genel kapı: GECTI 15/15 · şerit 15/15 |
| `jetson_log_20260906/engine_export.log`, `turev_kaydet.log`, `model_registry_ONCE.json` | T16 engine derleme (530 s, 57 283 989 B) + defter kaydı (sha `bb9bd868…0300`) + kayıt öncesi defter |
| `jetson_log_20260906/engine_karar_denkligi.{json,log}`, `engine_karar_denkligi_4K_yarim.log` | engine↔pt karar denkliği: F1 0 GEÇTİ · F2 0,99526 GEÇTİ · D-303 oransal 3/126 DÜŞTÜ (R 1280 genişliğe küçültülerek; ilk 4K koşumu yarım kaldı). Betik: `scripts/olcum/170_engine_karar_denkligi.py` |
| `jetson_log_20260906/jetson_baslat_kuru*.log`, `kamera_koprusu_dosya.log` | `--kuru` (Pixhawk yok → `[YOK] /dev/ttyACM0`), köprü dosya kaynağıyla |
| `jetson_log_20260906/unittest_tam_suit.log` | tam süit: Ran 2121 · F5 E30 S8 (sınıflandırma D-431 §3/§4) |
| `jetson_fps_20260906_orin_nano/` | T17 FPS 120 örnek: pt p50/p95 739/942 ms (1,35/1,06 FPS) · engine 635/751 ms (1,58/1,33 FPS) · eşik 0,61 · ONNX HATA (sm_87) |
| `jetson_fps_20260906_orin_nano_10dk/` | 10 dk sürekli, 900 örnek/model: pt 770/922 ms · engine 649/765 ms · termal bayrak yok |

⚠ Kamera (CSI) ve Pixhawk bağlı DEĞİLDİ: o kapılar ÖLÇÜLEMEDİ. ⚠ S kümesi `data/arena_kompozit_v2`,
T66 kabul kümesi DEĞİL — D-303 nihai kararı T66 ile verilir (D-431 K2).
