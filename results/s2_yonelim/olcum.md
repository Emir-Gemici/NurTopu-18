# S2 · YÖNELİM ÖLÇÜMÜ — K-A uç-bant kapısı rota eksenine göre

Ön kayıt: `results/gece_20260826/ON_KAYIT.md §5` (ölçümden önce yazıldı, bağlayıcı).
Betik: `scripts/olcum/s2_yonelim_olcum.py` · ham çıktı: `olcum.json`, `olcum.log`,
`kareler_kismi.jsonl` (kare başına kısmi kayıt). Model **v35**
(`O:\navitas\models\navitas_seg_v35_best.pt`), imgsz kayıt defterinden (512), conf 0,30,
çıkarım yolu `126_t138_gece_kumesi.py` ile aynı (`_preprocess → predict → get_masks →
_maskeleri_icerige_kirp`). Eksen ∈ {None, 0, 90}. Tarih 2026-08-26, süre A/B 4602 sn (kare
başına ~78 sn: 1920² tuvalde 12 `analyze_path`), C 24 sn.

## A) 0038 · 59 kare · v35 maskesi (üretim yolu)

| kip | None | 0° | 90° | tavan (0 ∪ 90) | yalnız 0 | yalnız 90 | None == 0 |
|---|---|---|---|---|---|---|---|
| ölçeksiz (üretim sebebi) | **11** | **11** | **0** | 11 | 11 | 0 | bayt-eş ✔ |
| ölçekli (mpp 0,01 bedava) | 1 | 1 | 0 | 1 | 1 | 0 | ✔ |

Sebep dağılımı, ölçeksiz: 0° → MASKE_YOK 35 · UC_BANT_TEMAS_YOK 13 · rota 11;
90° → MASKE_YOK 35 · UC_BANT_TEMAS_YOK 24.

**Bulgu (ön kayıtta öngörülmemişti, sayı olduğu gibi yazılır):** v35'in kendi maskesinde
90° **hiçbir kare kazandırmıyor**; 0°'de rota üreten 11 karenin hepsi 90°'de
UC_BANT_TEMAS_YOK'a düşüyor ve 0°'de UC_BANT olan 13 kare 90°'de de UC_BANT kalıyor.
Yani gerçek karede bugünkü darboğaz **yönelim değil model körlüğü**dür (MASKE_YOK 35/59;
kalan 13 UC_BANT karesinde maske iki eksende de bant kapatmıyor — parçalı/kısa).
D-281 §3'teki "döndürünce 14/18 geçiyor" gözlemi bu ölçümle **tekrar üretilemedi**
(o ölçümün girdisi/yöntemi farklı olabilir; ham çıktı burada, karşılaştırma mimara).

## B) Aynı 59 kare · ELLE etiket (YOLO poligon → letterbox maskesi, sınıf 0 zemin / 1 engel)

| kip | None | 0° | 90° | tavan (0 ∪ 90) | yalnız 0 | yalnız 90 | ikisi |
|---|---|---|---|---|---|---|---|
| ölçeksiz | **27** | **27** | **11** | **34** | 23 | **7** | 4 |
| ölçekli | 12 | 12 | 4 | 14 | 10 | 2 | 2 |

Yalnız 90°'de rota üreten 7 kare: frame_000104, 000107, 000197, 000200, 000207, 000217,
000218 (klibin sonu; yol kadrajı enine kesiyor). Etiket tavanı 0°'de 27 (D-281'de 28;
fark 1 kare — rasterizasyon/letterbox farkı olabilir, ham satır `olcum.json`).

**Yorum:** yönelim kazancı **etiket kalitesinde maskede** vardır (+7/59, tavan 27 → 34),
model maskesinde **yoktur** (11 → 11). S2 sorusunun cevabı: gerçek karede kazanç,
model kırsalı görmeye başladığında ortaya çıkar; bugün sıfırdır.

## C) Sentetik kabul kümesi `sentetik_arena_kadraj_t66` (n=260) · v35 · K1

`None` → **256** · `0` → **256** · karar/güven/waypoint/temiz maske **bayt-eş: True (0 fark)**.
Ön kayıt §5 "≥ 256 sabit kalmalı" → **GEÇTİ**. (0° yolu `_rota_ekseni_donusumu` üzerinden
geçtiği hâlde — birim dönüşüm INTER_NEAREST ile tam permütasyon — çıktı değişmiyor.)

## Madde 15 denetimi (ölçüm içinde)
Geri çevrilen waypoint'lerin **temiz maske dışında** kalanı: tüm kaynak/kip/eksenlerde
**0**. Ham (morfoloji öncesi) etiket maskesi dışında kalan: etiket/ölçeksiz 2, etiket/ölçekli 1
— **None ve 0'da da aynı 2/1** (çekirdeğin CLOSE adımı; döndürmeden bağımsız, önceden var).
90°'de 2/0. Döndürme yolu ham maske dışına **ek** waypoint üretmedi.

## Kapılar
- `codes/test_rota_sentetik.py` → **15/15**.
- `discover -s tests -q` (worktree) → Ran 772; **FAILED failures=3 errors=8** — **hepsi
  worktree ortamı** (`models/navitas_seg_v35_best.pt` ve `data/arena_kompozit` worktree'de
  yok). Kanıt: değişiklik `git stash` ile geri alınıp aynı komut koşuldu → aynı 11 kusur +
  yeni test dosyasının 7 import hatası; kusur kümesi farkı yalnız `test_rota_ekseni`.
  Ana depoda (`O:\navitas`) bu 11 test modeli bulur; oradaki taban 819 OK'dir.
- `tests/test_rota_ekseni.py` → 7 test OK; mutasyon (geri çevirme + fail-closed kapatıldı) →
  `FAILED (failures=2, errors=1)`; geri alındı → OK.

## Sonuç (ön kayıt §5'e göre)
1. Uygulama: `analyze_path(rota_ekseni_derece=None)` bayt-eş (A, C ve testlerle ölçüldü).
2. Gerçek karede "en iyi eksen" tavanı: **v35 11/59 (kazanç 0)**, etiket **34/59 (kazanç +7)**.
3. Sentetik arenada 0° ile kayıp **0** (256 = 256).
4. Üretime otomatik eksen seçimi **girmez**; kaynak önerisi `contracts_onerisi.md`.
