# K6 — "rota yol üstünde" ölçütü, sentetik kabul zinciri (ON_KAYIT §12)

Tarih: 2026-08-26 · worktree `wf_951a190e-bfe-1` · eşik **sonuç görülmeden** yazıldı (§12: yanlış güzergâh oranı ≤ %5), sonuca göre değiştirilmedi.

## 1. Ne yapıldı

| parça | dosya | özet |
|---|---|---|
| tek tanım | `scripts/olcum/rota_yol_olcumu.py` (yeni) | 142'deki `uc_durum_maske`, `rota_yol_olc`, `yanlis_guzergah_mi`, `KAPI_B_EK2` buraya **taşındı** (gövdeler HEAD'deki 142 ile metin olarak birebir; yalnız fonksiyon içi `import numpy/cv2` satırları modül başına alındı — `scratchpad/karsilastir_142.py` çıktısı: 3 fonksiyon `True`, `KAPI_B_EK2 birebir: True`). |
| 142 | `scripts/olcum/142_gece_olcum.py` | Tanım kopyası silindi; adlar `rota_yol_olcumu`'dan bağlanır. `tests/test_t152_rota_yol_ustunde.py` 9/9 OK (aynı fonksiyonlar, aynı sabitler). |
| 61 | `scripts/olcum/61_rota_moloza_basma.py` | Kare başına `yol_payi`, `etiketsiz_payi`, `engel_wp`, `wp`, `yanlis_guzergah` alanları; JSON'a `yol_olculen`, `yanlis_guzergah`, `yanlis_kareler`, `kapi_rota_yol`; konsola "YANLIS GUZERGAH (K6)" satırı. |
| 65 | `scripts/olcum/65_kabul_denetcisi.py` | `ESIK["K6_yanlis_guzergah_maks"] = 0.05`; `k6_durumu()` üç durumlu (GECTI / DUSTU / OLCULEMEDI — girdi yok, eski 61 çıktısı, payda 0); `gecti["K6"]` VERDİKT `all()`'a dâhil; rapor satırı "K6 ROTA YOL USTUNDE <= %5"; JSON alanları `K6_yanlis_guzergah`, `K6_oran`, `K6_durum`, `K6_yanlis_kareler`. |
| test | `tests/test_k6_rota_yol_ustunde.py` (yeni, 15 test) | tek-tanım kanıtı, letterbox yerleşimi, sentetik küçük küme (iyi / engel wp / pay düşük), 61 JSON şekli → `k6_durumu`, üç durum, eşik sözlükten, kapı satırı + mutasyon. |

### Koordinat sistemi (kanıt)
`61`, rotayı `analyze_path(trav, icerik=..., ...)` ile **`sq` tuvalinde** üretir; `sq = _preprocess(img)[0]`, `codes/rpi_inference.py:1787-1796`:
```
yan = max(h, w); tuval = full((yan, yan, 3), 114); x0, y0 = (yan - w)//2, (yan - h)//2; tuval[y0:y0+h, x0:x0+w] = norm
```
61 bunu zaten kullanıyordu: waypoint'leri `iz = zeros((h, w))` tuvaline `cv2.line` ile çizip `icerik` ile kırpıp `(w0, h0)`'a götürüyordu. `uc_durum_maske(txt, h0, w0, yan=h)` yer gerçeğini **aynı `(x0, y0)`** yerleşimiyle `(yan, yan)` tuvale taşır (`assert uc.shape == (h, w)`). Kabul kümesi 640×640 → `x0 = y0 = 0`, birebir. Test `test_letterbox_yerlesimi_preprocess_ile_ayni` dikdörtgen karede dolgu bandının ETİKETSİZ kaldığını sınar.

Tanım (142 ile ortak): rota çizgisi = ardışık waypoint'ler, `cv2.polylines` 1 px, tuval koordinatı; `yol_payi = çizgi∩sınıf0 / çizgi`; `engel_wp` = sınıf 1 üstündeki (veya tuval dışı, fail-closed) waypoint sayısı; YANLIŞ GÜZERGÂH ⇔ `yol_payi < 0,90` ∨ `engel_wp > 0`. Payda = rota üretilen kare.

## 2. Kapılar

- `codes/test_rota_sentetik.py` → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI`
- `tests/test_k6_rota_yol_ustunde.py` → `Ran 15 tests ... OK`
- 65'e bağlı mevcut testler (grep -l 65_kabul tests/): `test_k0_gorunurlugu`, `test_k5_ucuncu_durum`, `test_t125_denetci_olculemedi`, `test_t126_k5_zemini`, `test_t132_taban_gorunurlugu` → hepsi `OK`; `test_t152_rota_yol_ustunde` → `Ran 9 tests OK`
- `unittest discover -s tests -q` (worktree) → `Ran 940 tests in 72.299s · FAILED (failures=4, errors=11, skipped=16)` — 15 düşüş **ortam**: `models/*.pt` ve `jetson_paket/models` worktree'de yok (`Manifest navitas_seg_v35_best.pt diyor ama agirlik diskte YOK`), `dataset/gercek_kompozit` untracked. Düşen modüller: `test_imgsz_tek_kaynak` (2), `test_model_registry` (1), `test_saha_parametrik` (7), `test_t123_gecis_provasi` (4), `test_yks_gui_uretim_hizasi` (1). Hiçbiri 61/65/142/rota_yol'a dokunmaz. Ham log: `results/k6/unittest_tam.log`.

## 3. Mutasyon kanıtı (`scratchpad/mutasyon_k6.py`)
```
ONCE sha256 ec85993059053be065edde4ce855327b9dad8cded24f97e5460305737c0c9a0b
kaldirilan satir: gecti["K6"] = k6 == "GECTI"             # OLCULEMEDI de bloklar (T105 kalibi)
MUTANT exit 1
AssertionError: Regex didn't match: 'gecti\\["K6"\\]\\s*=\\s*k6\\s*==\\s*"GECTI"' not found in ...
Ran 15 tests in 0.012s
FAILED (failures=1)
GERI sha256 ec85993059053be065edde4ce855327b9dad8cded24f97e5460305737c0c9a0b bayt-es: True
GERI exit 0 |  OK
```
Ek: test yazılırken ilk beklenti (32/40 = 0,8) yanlıştı — `cv2.fillPoly` poligon kenar sütununu dâhil eder (33/40 = 0,825); beklenti düzeltildi, tanım DEĞİŞMEDİ.

## 4. ÖLÇÜM — 65 v35 / v3 / v6 (`results/k6/k6_*_65.log`, `scripts/olcum/results/t63/k6_*_kabul*.json`)

| model | K0 figür | K1 | K2 | K3 | K4 | K5 | **K6 yanlış güzergâh** | K6 oran | VERDİKT |
|---|---|---|---|---|---|---|---|---|---|
| v35 (`models/navitas_seg_v35_best.pt`) | %9,03 (oran 1,00) | 256/260 | 18/256 | 0/256 | 1/256 | 0/173 | **5/256** | **%1,95 GECTI** | URETIME ALINIR |
| v3 (`gece_v3_v35taban`) | %1,95 (oran 0,22) | 253/260 | 14/253 | 0/253 | 1/253 | 0/169 | **1/253** | **%0,40 GECTI** | URETIME ALINIR |
| v6 (`gece_v6_v35taban`) | %4,88 (oran 0,54) | 257/260 | 16/257 | 0/257 | 0/257 | 0/173 | **3/257** | **%1,17 GECTI** | URETIME ALINIR |

**K0–K5 önceki koşumlarla birebir:** v35 ↔ `t63/t130_v35_dogrulama_kabul_verdikt.json` (256/260 · 18/256 · 0 · 1/256 · K5 0/173 · figür 0,0903); v3 ↔ `gece_v3_v35taban_kabul_verdikt.json` (253/260 · 14/253 · 0 · 1/253 · K5 0/169 · figür 0,0195); v6 ↔ `gece_v6_v35taban_kabul_verdikt.json` (257/260 · 16/257 · 0 · 0/257 · K5 0/173 · figür 0,0488). K6 eklenmesi K0–K5'i değiştirmedi (D-286/287'deki "sentetik kabul geçer" sonucu korunur).

Yanlış güzergâh kareleri:
- v35: `sa_000114` (engel_wp 1, yol_payi 0,987) · `sa_000125` (1, 0,937) · `sa_000128` (1, 0,952) · `sa_000227` (1, 0,954) · **`sa_000176` (engel_wp 0, yol_payi 0,00, etiketsiz 1,00)** — etiket dosyası var (sınıf 0 poligonu dar bir şerit), rota tamamen etiketsiz zemin üzerinde; basma 0.
- v3: `sa_000076` (engel_wp 0, yol_payi 0,083, etiketsiz 0,90).
- v6: `sa_000020` (0, yol_payi 0,898 — eşiğin 2/1000 altında) · `sa_000021` (1, 0,980) · `sa_000125` (1, 0,943).
- yol_payi ortalaması: v35 0,9949 · v3 0,9960 · v6 0,9987; medyan 1,0 (üçü de).

**Yorum (kapı değil):** Sentetik kümede K6 üç modelde de rahat geçiyor (≤ %2). Gerçek karelerde (T152, D-289) v35'in 6 rotasından 5'i yol üstünde DEĞİLDİ — sentetik kabulün gerçek sahayı temsil etmediği bir kez daha ölçüldü; sentetik K6'nın geçmesi gerçek kapıyı (b-ek2, yanlış güzergâh = 0) **ikame etmez**. Sentetik yanlışların 4/5'i (v35) tek bir waypoint'in engel etiketinin kenarına düşmesidir (yol_payi ≥ 0,93).

## 5. Açık sorular
1. `sa_000176` (v35) ve `sa_000076` (v3): rota etiketsiz zemin üzerinde — üretecin sınıf 0 poligonunun kadrajdaki yolu tam kapsayıp kapsamadığı (etiket tavanı) bakılmalı; K6 tanımı gereği yanlış sayıldı, değiştirilmedi.
2. Worktree'de 15 ortam düşüşü; ana dizinde birleştirme sonrası `unittest discover` yeniden koşulmalı.
3. 61 JSON'u eski çıktılarla uyumsuz değil (alanlar eklendi); 65, eski 61 JSON'u okursa K6 = OLCULEMEDI (bloklar) — beklenen davranış, test edildi.
