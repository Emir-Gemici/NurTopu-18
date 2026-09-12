# T235-B/D kapı çıktıları (ham)

| dosya | ne |
|---|---|
| `genel_kapi.txt` | `codes/test_rota_sentetik.py` — CLAUDE.md madde 14 genel kapısı |
| `tam_suit.txt` | `-m unittest discover -s tests -p "test_*.py"` — çalışma ağacının tamamı |

## Tam suit: 21 düşen test ORTAM KAYNAKLIDIR (bu işin değişikliği değil)

`Ran 2671 tests` · `FAILED (failures=10, errors=11, skipped=34)`. Düşenlerin hepsi şu 7
modülde: `test_imgsz_tek_kaynak` (2), `test_model_registry` (1), `test_saha_parametrik` (7),
`test_t123_gecis_provasi` (4), `test_t202_jetson_paket_butunlugu` (1),
`test_t38_kuru_kosu_fiksturu` (5), `test_yks_gui_uretim_hizasi` (1).

Kanıt — üç bağımsız gözlem:

1. **Bu işin diff'i o modüllerin hiçbirine dokunmuyor.** `git diff --name-only master...HEAD`
   yalnız `codes/karar_sozlesmesi.py` (dosya SONUNA ekleme; master'da dosya 2260 satır, tek
   hunk `@@ -2260,0 +2261,249 @@` → mevcut hiçbir satır kaymadı), jetson aynası,
   `simulation/mujoco/t235_etiket_tezgahi.py`, `tests/test_t235_alan_etiketi.py` ve
   `results/.../t235/` altını listeler.
2. **Aynı 7 modül ANA AĞAÇTA (`O:\navitas`, master) GEÇİYOR:** `test_imgsz_tek_kaynak OK`,
   `test_model_registry OK`, `test_saha_parametrik OK (20 test)`, `test_t123_gecis_provasi OK`,
   `test_t202_jetson_paket_butunlugu OK`, `test_t38_kuru_kosu_fiksturu OK (11 test)`,
   `test_yks_gui_uretim_hizasi OK`.
3. **Kök neden git-ignore'lu model varlıkları:** `.gitignore:41` = `models/*.pt`, yani model
   ağırlıkları depoya girmiyor ve çalışma ağacına kopyalanmıyor.
   - `test_model_registry`: `ModelRegistryError: model artefaktı yok: ...`
   - `test_t202_jetson_paket_butunlugu`: eksik liste
     `['models/navitas_seg_v17_best.pt', 'models/navitas_seg_v17_best_640_fp16.onnx', ...]`

⚠ Bu bir **"GEÇTİ"** beyanı değildir: tam suit bu çalışma ağacında KIRMIZIDIR ve öyle
kaydedilmiştir. İddia yalnız şudur: kırmızılığın nedeni ölçüldü ve bu işin değişikliği değil.
Birleştirmeden sonra tam suit ana ağaçta yeniden koşulmalıdır.

## `test_olcum_ayna_senkronu` — 2 atlama da ortam kaynaklı

Çalışma ağacında canlı ölçüm dizini yolu `O:\navitas\.claude\worktrees\navitas-local-train`
olarak çözülüyor (yok) → `skipTest`. `NAVITAS_OLCUM_KOK=O:/navitas-local-train` ile
koşulduğunda kapı düşüyor; ölçüldü: ortak 77 betiğin **59'u bayt farklı, CRLF
normalleştirmesinden sonra 0'ı farklı** — yani fark `core.autocrlf=true` ile yapılan
worktree checkout'unun satır sonlarıdır, içerik aynıdır. Ana ağaçta (LF) aynı kapı
`Ran 6 tests ... OK` (atlama yok) veriyor.
