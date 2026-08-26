# T156 — Genel kapıya (madde 14) ÜRETİM YOLU kolu

**Tarih:** 2026-08-26 · **Ön kayıt:** `results/gece_20260826/ON_KAYIT.md` §18-B (bağlayıcı, sonuca göre değiştirilmedi)
**Karar kaydı:** `REVIEW_LOG.md` D-297 · **Sözleşme:** `CONTRACTS.md` §11.2-EK → "Genel kapının kapsamı"
**Yorumlayıcı:** `O:\navitas-local-train\venv\Scripts\python.exe` · **GPU KULLANILMADI** (sahneler sentetik, model koşmuyor)

---

## 1. Neden — kapı üretimi hiç görmüyordu

`CONTRACTS §11.2-EK` (D-295) üretim yolunun **`rpi_inference.analyze_path`** olduğunu beyan etti:
`run_camera` → K1 telsiz halkası → `iha_sender.KararYayinci`. Anayasa madde 14'ün genel kapısı
(`codes/test_rota_sentetik.py`, 15/15) ise yalnız **`costmap_path_finder.rota_bul`**u zorluyordu.

Delik **varsayım değil ölçümdür**: T155'te (D-296) üretim yolu 15 yer gerçekli arena sahnesinin
**9'unda yanlış şerit numarası yayınlarken** genel kapı **15/15 yeşil** yanıyordu. Şartname §2.1
topolojisi (üç güzergâhtan biri açık) üretim yolunda **hiç kapıya sokulmamıştı**.

## 2. Yapılan — ikinci kol, aynı 15 belirlenimci sahne

Sahneler `simulation/scripts/arena.py` → `test_rota_sentetik.sahne_uret` ile üretilir (5 harita ×
3 senaryo, kusursuz maske). Yer gerçeği `H["open"]` **üretecin kendi tohumundan** gelir ve karar
yoluna **hiç verilmez** — bağımsız kâhin.

| kol | çağrılan | şart | kaynak |
|---|---|---|---|
| **KOL 1** (tanısal) | `costmap_path_finder.rota_bul` | **15/15 tam puan** — değişmedi | anayasa madde 14 |
| **KOL 2** (**ÜRETİM**) | `rpi_inference.analyze_path` | (a) rota **üretiliyor** (ret yok, karar var, ≥ 2 waypoint) **ve** (b) **yayınlanan** `road` yer gerçeğine eşit — her ikisi **≥ 14/15** | ÖN KAYIT §18-B |

- Çağrı T151/T155 ile **birebir aynı** (`results/t155/serit_kapisi.py`): `analyze_path(zemin,
  icerik=None, engel_mask=engel, mpp=MPP, return_reason=True, return_olcum=True)`.
- Eşik **tek yerde** tanımlıdır: `test_rota_sentetik.URETIM_KAPI_ESIGI = 14` (madde 16, çıplak sayı yok).
- Çıkış kodu **tek yerden** döner: `kapi_karari()` ve **iki kola da** bağlıdır.

### Çıktı sözleşmesi korundu
`SONUC: 15/15 dogru` satırı ve `[OK] TUM DETERMINISTIK SAHNELER GECTI` cümlesi **KOL 1'in çıktısı
olarak aynen** duruyor. `grep` ile tarandı: bu metni okuyan bir betik/CI **bulunamadı**
(`codes/test_rota_sentetik.py:162` dışında `SONUC:` üreten dosyalar ilgisiz), ama sözleşme yine de
korundu ve `tests/test_t156_...::test_KOL1_cikti_sozlesmesi_BOZULMADI` ile **kilitlendi**.

## 3. ÖLÇÜM — taban (ön kayıt §18-B'nin istediği)

Ham çıktı: `results/t156/ham_kapi_gecti.txt`

```
------------------------------------------------------------------------------
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

==============================================================================
KOL 2 — URETIM YOLU (rpi_inference.analyze_path) · AYNI 15 SAHNE
==============================================================================
harita  senaryo  gercek   yayin  guven   wp              ret  darbogaz  sonuc
     1    kolay       1       1  0.822    8             None         2  OK
     1     orta       2       2  0.742    8             None         2  OK
     1      zor       3       3  0.662   12             None         2  OK
     2    kolay       1       1  0.742    8             None         2  OK
     2     orta       1       1  0.674   10             None         2  OK
     2      zor       3       3  0.662   10             None         3  OK
     3    kolay       3       3  0.662    8             None         3  OK
     3     orta       2       2  0.753   10             None         2  OK
     3      zor       1       1  0.719   10             None         3  OK
     4    kolay       3       3  0.685    8             None         2  OK
     4     orta       3       3  0.742   13             None         3  OK
     4      zor       1       1  0.742   12             None         2  OK
     5    kolay       3       3  0.731    8             None         2  OK
     5     orta       3       3  0.731    9             None         3  OK
     5      zor       2       2  0.674    8             None         1  OK
------------------------------------------------------------------------------
URETIM YOLU: rota uretimi 15/15 · yayinlanan serit 15/15 (esik >= 14/15, ON_KAYIT SS18-B)
[OK] URETIM YOLU KOLU GECTI
------------------------------------------------------------------------------
GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15
CIKIS_KODU=0
```

| ölçü | taban | eşik (ön kayıt §18-B) | sonuç |
|---|---|---|---|
| KOL 1 `rota_bul` | **15/15** | 15/15 | GEÇTİ |
| KOL 2 rota üretimi | **15/15** | ≥ 14/15 | GEÇTİ |
| KOL 2 yayınlanan şerit | **15/15** | ≥ 14/15 | GEÇTİ |

`darbogaz` sütunu **tanıdır, kapıya girmez** — T155 öncesi yayınlanan alan buydu ve tabloda
15 sahnenin 9'unda `gercek`ten farklı olduğu görülüyor.

## 4. MUTASYON KANITI — kapı vakum değil

**Mutasyon:** `codes/rpi_inference.py:1725`
`open_path = olcum["serit_karari"]` → `open_path = olcum["darbogaz_serit"]`

Ham çıktı: `results/t156/ham_kapi_mutant.txt`

```
URETIM YOLU: rota uretimi 15/15 · yayinlanan serit 6/15 (esik >= 14/15, ON_KAYIT SS18-B)
[FAIL] URETIM YOLU KOLU DUSTU — uretimde yayinlanan karar yer gercegiyle uyusmuyor
------------------------------------------------------------------------------
GENEL KAPI (madde 14): DUSTU — kol1 15/15 · kol2 serit 6/15
CIKIS_KODU=1
```

🔴 Bu çıktının kritik satırı **`kol1 15/15`**: mutasyonla üretim yolu bozulurken KOL 1 hâlâ
**tam puan** veriyor. T156 öncesi kapı bu bozulmayı **görmezdi** — delik artık kapıdadır.

Aynı mutasyonla `tests/test_t156_genel_kapi_uretim_kolu.py` de düştü (`FAILED (failures=2)`).

**Bayt-eş geri alma:**

```
$ sha256sum codes/rpi_inference.py            # mutasyondan ÖNCE
7f0afaaac605946494959c226dfb0bd474c5f409219874ae637fbd065fa3631d *codes/rpi_inference.py
$ sha256sum codes/rpi_inference.py            # geri aldıktan SONRA
7f0afaaac605946494959c226dfb0bd474c5f409219874ae637fbd065fa3631d *codes/rpi_inference.py
$ git diff --stat codes/rpi_inference.py      # (boş)
```

## 5. Kilit — `tests/test_t156_genel_kapi_uretim_kolu.py` (15 test)

1. **Değer** — kol ≥ eşik (rota üretimi + yayınlanan şerit), sahne sayısı `arena`nın kendi sayısı.
2. **Çıkış kodu sözleşmesi** — `kapi_karari()`: iki kol geçince 0; KOL 1 tek sahne düşünce 1;
   KOL 2 eşiğin altına inince 1; eşik sınırı (14 geçer / 13 düşer); **boş küme geçemez** (fail-closed).
3. **Uçtan uca** — kapı betiği **alt süreç** olarak koşulur: çıkış kodu 0, KOL 1 metni aynen var,
   KOL 2 geçti. `main()`den çağrı silinirse bu düşer.
4. **Mutasyon muhafızı** — `darbogaz_serit` yayınlansaydı kol **6/15** ile eşiğin altında kalırdı
   (ölçülüp assert edildi), ve iki alan 15 sahnenin bir kısmında gerçekten ayrışıyor.

```
$ <venv> -m unittest discover -s tests -p "test_t156_*.py" -q
Ran 15 tests in 5.597s
OK
```

## 6. Genel kapı ve süit (madde 14)

```
$ <venv> codes/test_rota_sentetik.py
SONUC: 15/15 dogru · [OK] TUM DETERMINISTIK SAHNELER GECTI
URETIM YOLU: rota uretimi 15/15 · yayinlanan serit 15/15
GENEL KAPI (madde 14): GECTI    → CIKIS_KODU=0     (3,7 s)

$ <venv> -m unittest discover -s tests -q
Ran 1017 tests in 79.394s
FAILED (failures=4, errors=11, skipped=16)      → 986 OK
```

15 kırmızının **hepsi T156'dan önce de vardı** ve worktree'de `models/` + `data/` bulunmamasından
gelir: `test_saha_parametrik` (7), `test_t123_gecis_provasi` (4), `test_imgsz_tek_kaynak` (2),
`test_model_registry` (1), `test_yks_gui_uretim_hizasi` (1). Yalıtılmış koşumla doğrulandı
(`test_saha_parametrik`, `test_t123_gecis_provasi` T156 dosyaları yokken de düşüyor) ve hiçbiri
`test_rota_sentetik`i import etmiyor. **Ana depodaki 988 OK / 2 skip tabanı bu worktree'de
ölçülemedi** — modeller ve veri worktree'de yok.

`jetson_paket` aynaları: `diff codes/rpi_inference.py jetson_paket/kod/rpi_inference.py` **boş**,
`diff codes/costmap_path_finder.py jetson_paket/kod/costmap_path_finder.py` **boş** — üretim kodu
değişmediği için ayna güncellemesi gerekmedi.

## 7. 🔴 YAN BULGU — worktree'de sessiz yanlış ölçüm (ayrı iş, kapanmadı)

Yeni test ilk **tam** `discover` koşumunda düştü; sebep testin kendisi değildi. `discover`
sırasında bir test modülü `scripts/olcum/ayarlar.py` zincirinden (`REPO = Path(r"O:\navitas")`)
**ANA deponun** `codes` dizinini `sys.path[0]`'a ekliyor. Ölçüldü:

```
MODUL: O:\navitas\codes\test_rota_sentetik.py
URETIM KOLU VAR MI: False
KAYNAK DOSYA: O:\navitas\codes\test_rota_sentetik.py
```

Yani worktree'de koşan tam süit, worktree'nin `codes/` dosyalarını değil **ANA deponunkini**
import ediyor. Bu, T156'nın yanında `test_t155_serit_numarasi.py`,
`test_t134_rota_bul_zemin_kapisi.py` ve `test_zemin_kaplama_kapisi.py`yi de kapsar: bir worktree
ajanı `codes/`de değişiklik yapıp süiti koştuğunda **değiştirdiği kodu ölçmemiş olabilir** —
düşmesi gereken bir kapı sessizce geçer.

**Bu turda yapılan:** yalnız T156 bağışık kılındı (kesin dosya yolundan `importlib` yüklemesi +
alt süreçle uçtan uca koşum + kaynağı doğrulayan test).
**Kapanmadı:** diğer üç dosya ve genel yordam; kök çözüm `ayarlar.py`'nin `REPO`'yu `__file__`den
türetmesidir ama bu **ana depo betiklerinin davranışını değiştirir**, bu görevin kapsamı değildi
ve **ölçülmedi**. **Mimarın kararını bekler.**

## 8. ⚠ SINIR (raporda aynen durur)

Sahneler **SENTETİKtir** ve maske **KUSURSUZdur**. Bu bir **MANTIK** kapısıdır, **ALGI** kapısı
değildir; gerçek karelerde oran **BU DEĞİLDİR**. Gerçek kare etkisi bu turda **ÖLÇÜLMEDİ** —
GPU yasağı yürürlükteydi (`results/pc_cokme_20260826/rapor.md`).

Ayrıca §11.2-EK'in **ikinci** boşluğu kapanmadı: `koridor_adaylari` üç-güzergâh kapısı ile
`rota_dogrula`nın K2/K3 ihlal denetimi **hâlâ yalnız `rota_bul`dadır**. T156 üretim yolunun
**kararını** kapıya soktu, ihlal denetimini üretim yoluna **taşımadı**.
