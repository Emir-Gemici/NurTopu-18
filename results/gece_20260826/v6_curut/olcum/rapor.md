# v6 ÇÜRÜTME — LENS 1: ÖLÇÜM YENİDEN ÜRETİMİ (2026-08-26)

Aday: `codes/runs/segment/gece_v6_v35taban/weights/best.pt`
sha256 best.pt = 480fd0461ee185c5de24935aa74e926b6ac1c7e5a65f0b9da669bba6f148efdf (last.pt farklı: f344768a…; v35 taban: e00f6b8e…)

## (1) Kayıtlı sayıların ham kaynaktan yeniden üretimi
- `scripts/olcum/results/t63/gece_v6_v35taban_kabul_verdikt.json`: verdikt True, gecti K0..K5 hepsi True, K1_rota "257/260", K2 16/257, K3 0/257, K4 0/257, K5 GECTI. Dosya mtime 05:19:18, best.pt 05:16:22 → ağırlıktan SONRA koşulmuş. `gece_v6_v35taban_olcum.json` kabul bloğu ile birebir.
- 109 (her iki olcum.json'da aynı): cati_kacak_ort 0,0391 · zemin_maskesi_reddi 0 → red67 ≤ 5 ✓, çatı ≤ 0,10 ✓.
- `gece_v6_ref2_test29.json` kare kare SAYDIM: 29 kare; olceksiz_sebep None=12, MASKE_YOK=8, UC_BANT_TEMAS_YOK=8, ZEMIN_MASKESI_SUPHELI=1 (toplam 29 ✓).
- `test29_etiket_tavani_v2.json`: 29 kayıt, rota True 15 / False 14; her test karesinin tavan kaydı var.
- Kendi sayımım: **TP 11 · FP 1 (frame_000218) · FN 4 (000100, 000116, 000124, 000202) · TN 13** — kayıtlı ile birebir.
- Test görüntüleri: `dji_kirsal_0038_bolum/images/test` ile `_v2/images/test` 29/29 aynı ad ve aynı sha256; `hazirlik.json` test listesi ile aynı küme → ROTA/MASKE_YOK eşiklerinin referans değişiminden etkilenmemesi iddiası doğru (v35_ref2 de 6/16 verdi).

## (2) 126'nın bağımsız yeniden koşumu
Komut: `venv python scripts/olcum/126_t138_gece_kumesi.py --kareler dataset/dji_kirsal_0038_bolum_v2/images/test --modeller O:/navitas/codes/runs/segment/gece_v6_v35taban/weights/best.pt --cikti results/gece_20260826/v6_curut/olcum --dosya v6_test29_curut.json`
Çıktı (`126_curut.log`): ROTA olceksiz 12 · olcek bedava 9 · sebep {None 12, MASKE_YOK 8, UC_BANT_TEMAS_YOK 8, ZEMIN_MASKESI_SUPHELI 1}. Kare kare alan alan (sebep, wp, yol) karşılaştırma: **0 fark** → deterministik. Tavan v2 ile TP 11, FP [frame_000218].

## (3) Kapı sabitleri
142 içindeki KAPI: verdikt True · K1_min 230 · red67_maks 5 · cati 0,10 · rota_test29_min 10 · maske_yok_test29_maks 10 — ON_KAYIT §4 ile aynı. FP ≤ 1 sabiti KAPI sözlüğünde DEĞİL, kodda `<= 1` olarak gömülü (§4 b-ek ile uyumlu ama `kapi_sabitleri` çıktısında görünmüyor).
Türetim: taban ROTA 6 → max(6+4, 1,5×6=9) = 10 ✓ · MASKE_YOK 16 → 2/3×16 = 10,67 → ≤ 10 (tam sayıya aşağı, sıkı yön) ✓. 65'in K1_rota_min de 230 ✓.

## (4) Reçete
args.yaml: model = models/navitas_seg_v35_best.pt (taban v35 ✓) · data karisim_gece_v6.yaml (sentetik_arena 5400 + copy_paste_t127 344 + dji_kirsal_x20 2020 + dalga2_x20 2160 = 209×20 ✓; rescuenet YOK ✓; val 0038 30 + dalga2 52 = 82 ✓) · epochs 10 · patience 5 · imgsz 512 · batch 12 · seed 0 · deterministic · lr0 0,001 · warmup 5 · workers 8 → §3/§9 ile uyuşuyor. results.csv: 6 epoch koştu (patience 5), val mAP50-95(M) epoch1 0,113 → sonra düşüyor; best epoch 1 ("v35+1 epoch").

## Kusurlar (hiçbiri tek başına ölçümü çürütmedi)
1. Hiçbir tek koşum `terfi_adayi: true` yazmadı: (a) 05:22 koşumundan (eski tavanla b DÜŞTÜ, FP 2), (b) 10:10 `--atla-kabul` koşumundan (a ÖLÇÜLMEDİ). "v6 (a)∧(b) geçti" hükmü iki JSON'un elle birleşimidir; aynı ağırlık (tek best.pt, mtime 05:16) ve (a) tavandan bağımsız olduğu için mantıken tutarlı, ama kayıtta bütün olarak yoktur.
2. FP=1 tavanın tam sınırında; ROTA 12 (eşik 10) 2 kare payla. frame_000205 v1 tavanında FP idi, v2 tavanında True oldu — geçiş referans genişlemesine bağlı.
3. FP ≤ 1 sabiti `KAPI` sözlüğünde yok (kodda gömülü).
4. best epoch 1, val mAP tekdüze düşüyor: model v35+1 epoch; kapı değil, §4(c) raporlanır.

SONUÇ: ölçüm yeniden üretildi, deterministik, sabitler ön kayıtla aynı → bu lensten ÇÜRÜTÜLEMEDİ.
