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

---

# İKİNCİ MİRAS KIRMIZI — D-373 ileri işaret (`REVIEW_LOG.md`) · **BU DAL DÜZELTEMEZ**

## 6. Olgu

Belgeler bittikten sonra master bir kez daha ilerledi (`dd7cd12a`,
"D-468 T240 KABUL ve master'da…") ve `git merge master` onu bu dala getirdi.
Commit'in deltası **yalnız iki dosyadır**: `REVIEW_LOG.md` (+12 satır) ve
`TASK_QUEUE.md` (+4/-1). D-468 kaydı, D-465'i çürüten/düzelten bir kayıttır;
`tests/test_d373_defter_geri_isaret.py` her çürütülen kaydın başlığının altında
**ileri işaret** ister. D-465'in altında o işaret yok.

## 7. Ölçüm — kırmızı MASTER'DA

Ayrı detached worktree `dd7cd12a`'ya açıldı (bu dalın tek satırı yok):

```
AssertionError: Lists differ: [] != [('D-465', 'D-468')]
Ran 6 tests · FAILED (failures=2)
```

Ham çıktı: `master_d373_kirmizi.txt`.
`git diff master HEAD -- REVIEW_LOG.md TASK_QUEUE.md` → **BOŞ**: bu dal iki
dosyaya da dokunmadı.

## 8. Neden DÜZELTİLMEDİ

Bu dalın görev kuralı açıktır: **`REVIEW_LOG` / `TASK_QUEUE` / `CLAUDE` /
`AGENTS` / `HANDOFF` dosyalarına DOKUNULMAZ.** Düzeltme tam olarak
`REVIEW_LOG.md`de D-465 başlığının altına bir ileri işaret satırı eklemektir;
o satırı bu amele yazamaz. **Kayıt burada bırakılıyor, sessizce geçilmiyor.**

Gereken (kaydın sahibine): `REVIEW_LOG.md`de `D-465` başlığının hemen altına
D-468'e ileri işaret satırı — biçimi `tests/test_d373_defter_geri_isaret.py`
belirler.

## 9. YALITIM ÖLÇÜMÜ — kırmızılığın TAMAMI o iki dosyadan geliyor

`yalitim_suiti.py`: `REVIEW_LOG.md` ve `TASK_QUEUE.md` geçici olarak
`46ffb503` sürümüne çevrilir (yani master'ın `dd7cd12a` deltası kaldırılır),
tam süit koşulur, sonra iki dosya da **sha256 doğrulanarak bayt-eş** geri
yazılır. Ürün ve test kaynağına DOKUNULMAZ.

| Ağaç | Tam süit | Genel kapı | Kanıt |
|---|---|---|---|
| SON ağaç (master `dd7cd12a` dâhil) | `Ran 2816 · FAILED (failures=2)` — ikisi de D-373 | GECTI 15/15 | `results/push_kapisi/20260912_072913` |
| SON ağaç, **yalnız `REVIEW_LOG.md`** geri alınmış (ara ölçüm) | `Ran 2816 · FAILED (failures=1)` — `test_defter_butunlugu`: `defterde bulunmayan kuyruk atiflari: [468]` (TASK_QUEUE hâlâ D-468'i anıyor) | GECTI 15/15 | `results/push_kapisi/20260912_074003` |
| SON ağaç, **`dd7cd12a` deltasının TAMAMI** geri alınmış | **`Ran 2816 · OK (skipped=19)`** | **GECTI — kol1 15/15 · kol2 şerit 15/15** | `results/push_kapisi/20260912_074950` |

İkinci satır ayrıca ara ölçümün neden yetmediğini gösterir: iki dosya **birbirine
bağlıdır**, yalnız birini geri almak defter/kuyruk atıf kapısını düşürür.

**Sonuç:** bu dalın kendi içeriği (ürün + test + kanıt) **tam süitte yeşildir**;
son ağaçtaki iki düşüşün ikisi de master'ın `dd7cd12a` içeriğindendir ve bu
amelenin dokunması yasak olan dosyadadır.

## 10. KAPANDI — master kendi kusurunu düzeltti (`7f396ad6`)

Yalıtım ölçümü kaydedildikten kısa süre sonra master bir kez daha ilerledi:
`7f396ad6 D-465 e D-468 ileri isareti (defter geri isaret kapisi)` — yani
§8'de "gereken" diye yazılan satırı kaydın sahibi koydu. `git merge master`
ile alındı ve kapı bu dalda da yeşile döndü:

```
$ python -X utf8 -B -m unittest discover -s tests -p "test_d373_defter_geri_isaret.py"
Ran 6 tests · OK
```

⚠ §9'daki yalıtım ölçümü **silinmiyor**: o ölçüm, kırmızılığın kaynağını
bu dal değil master olduğunu gösteren kanıttır ve kayıtta öyle durmalıdır.
Bugünkü kapanış onu geçersiz kılmaz, tamamlar.
