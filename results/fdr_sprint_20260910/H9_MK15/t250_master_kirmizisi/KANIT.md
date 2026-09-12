# MASTER'DAN MİRAS ALINAN KIRMIZI — `tests/belge_kilidi.py` muafiyet işareti

**Bu kusur bu dalın işi DEĞİLDİR; master'da doğdu ve `git merge master` ile
bu dala geçti.** Kayıt, hem düzeltmenin gerekçesini hem de "bu dal kırmızıyı
kendi üretmedi" iddiasını ÖLÇÜMLE bırakmak içindir.

## 1. Olgu

`git merge master` (12 Eyl, ikinci birleşim) master'ın `46ffb503`
("T240 birlestirme … ortak belge kilidi tests/belge_kilidi.py") commit'ini
getirdi. O commit `tests/` altına **sıfır test toplayan** bir yardımcı modül
ekliyor (`tests/belge_kilidi.py`, 737 satır) ama T120 kuralının istediği
muafiyet işaretini koymamış.

`tests/test_t120_sahte_kapi_yasagi.py` kuralı: `tests/` altındaki her dosya ya
**≥1 test toplamalı** ya da modül docstring'inde satır başında
`KESIF MUAFIYETI: <gerekce>` **ve** `KOSUM: <komut>` taşımalıdır.

## 2. Ölçüm — kırmızı MASTER'da, bu dalın hiçbir değişikliği olmadan

Ayrı bir **detached worktree** `46ffb503`'e açıldı (bu dalın tek satırı bile
yok) ve aynı komut koşuldu:

```
$ python -X utf8 -B -m unittest discover -s tests -p "test_t120_sahte_kapi_yasagi.py"
AssertionError: Lists differ: ['belge_kilidi.py: SIFIR test topluyor ve muafiyet isareti YOK (sahte kapi)'] != []
Ran 15 tests · FAILED (failures=1)
```

Ham çıktı: `master_t120_kirmizi.txt`.

Aynı kırmızı bu dalın tam süitinde de göründü:
`results/push_kapisi/20260912_070314/tam_suit.txt` →
`Ran 2816 tests · FAILED (failures=1, skipped=19)`, tek düşüş bu.

`git diff master HEAD -- tests/belge_kilidi.py tests/test_t120_sahte_kapi_yasagi.py`
**BOŞ** — yani iki dosyaya da bu dal dokunmamıştı.

## 3. Düzeltme — EN DAR olan: eksik işaret konuldu, kural GEVŞETİLMEDİ

`tests/belge_kilidi.py` modül docstring'ine, `tests/depo_yollari.py`'nin
zaten kullandığı **aynı biçimde** iki satır eklendi:

- `KESIF MUAFIYETI:` — modülün test değil ORTAK yardımcı olduğu ve kendi
  kapısının `tests/test_belge_kilidi.py` olduğu, gerekçesiyle;
- `KOSUM:` — o kapının gerçekten koşan komutu, dosyanın kendi adıyla.

⚠ `test_t120`in ikinci kilidi (`KOSUM` satırı kendi dosyasını göstermeli)
ilk denemede DÜŞTÜ: docstring ham dizge DEĞİLDİR, `O:\navitas…` içindeki
`\n` kaçış dizisine dönüşüp satırı `O:`ye kırpıyordu. Ters bölüler
`depo_yollari.py`deki gibi **çiftlendi**. Bu, T120'nin ikinci kilidinin
gerçekten ölçtüğünün kanıtıdır (kilit boş değil).

**Kurala dokunulmadı:** `test_t120_sahte_kapi_yasagi.py` DEĞİŞMEDİ, eşik
gevşetilmedi, muafiyet listesi elle tutulan bir yere yazılmadı (kural zaten
docstring'den türetiyor).

## 4. Düzeltmeden sonra (bu dal)

| Kapı | Sonuç | Dosya |
|---|---|---|
| `test_t120_sahte_kapi_yasagi.py` | **Ran 15 · OK** | `dal_t120_yesil.txt` |
| `test_belge_kilidi.py` (modülün KENDİ kapısı, KOSUM satırının gösterdiği) | Ran 74 · OK | — |
| `belge_kilidi`yi içe alan 4 test modülü (`test_isaretli_gosterici` 63, `test_faz_b_arduplane_sablon` 45, `test_t235_alan_etiketi` 57, `test_yks_mk15_hakem_ekrani` 42) | hepsi OK | — |
| `scripts/belge_kilidi_denetle.py` | EXIT 0 | — |

## 5. Mimara not

Değişiklik başka bir ajanın (T240) dosyasındadır ve **yalnız docstring**
satırıdır; davranış değişmez. Burada kayda geçiriliyor ki denetim, bu iki
satırın bu dalın kapsamı dışından geldiğini ve neden zorunlu olduğunu
görebilsin. Master tek başına hâlâ bu commit'ten önce kırmızıdır; bu dal
birleşince düzelir.
