# TERFİ RAPORU — üretim modeli **v35 → v36** (koşum `gece_v7a_v35taban`)

**Tarih:** 2026-08-26 · **Uygulayan:** başamele · **Karar:** KULLANICININ (D-133)
**Dayanak:** `REVIEW_LOG.md` D-293 · ön kayıt `results/gece_20260826/ON_KAYIT.md` §15
· çürütücü `results/gece_20260826/v7a_curut/` · yordam kalıbı D-256 (T130, v34→v35).

> 🔴 **KURAL DIŞI TERFİ.** Ön kayıtlı gerçek-kare eşiklerinden **ROTA ≥ 10** (ölçülen **8**)
> ve **MASKE_YOK ≤ 10** (ölçülen **16**) **GEÇİLMEDİ**. Kullanıcı 2026-08-26'da
> *"izin veriyorum kurala rağmen"* dedi ve düzeltilmiş tabloyu görüp *"tamam yap"* dedi.
> **Eşikler değiştirilmedi, gevşetilmedi**; `CONTRACTS.md` §12'ye İSTİSNA satırı yazıldı ve
> eşikler **sonraki terfileri bağlar**. Bu cümle registry `_surum_karari`, iki kılavuz ve
> CONTRACTS §12'de **aynen** durur — yumuşatılmadı.

---

## 0. SHA-256 — hepsi ÖLÇÜLDÜ (kopyalanmadı)

```
$ <venv> -c "hashlib.sha256(...)"
codes/runs/segment/gece_v7a_v35taban/weights/best.pt   1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911
models/navitas_seg_v36_best.pt                          1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911   54.788.636 bayt
jetson_paket/models/navitas_seg_v36_best.pt             1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911   54.788.636 bayt
models/navitas_seg_v36_best.onnx                        f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab   54.569.673 bayt
results/onnx_export_v36_20260826/navitas_seg_v36_best_512_fp16.onnx
                                                        f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab   54.569.673 bayt
jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx  f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab   54.569.673 bayt
```

Emirde verilen aday özeti (`1d1caca6…`) **bağımsız olarak yeniden ölçüldü ve tuttu**.
Üretim ağırlığı koşumun `best.pt`siyle **bayt-eş** — geçen terfilerde kırılan nokta budur.
Önceki üretim v35 (`e00f6b8e…`) ve v34 (`6730d777…`) **diskte duruyor, silinmedi**.

---

## 1. AĞIRLIK

```
$ cp codes/runs/segment/gece_v7a_v35taban/weights/best.pt models/navitas_seg_v36_best.pt
best.pt                        1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911
models/navitas_seg_v36_best.pt 1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911
bayt 54788636
```

---

## 2. `config/model_registry.json` — `profiles.competition`

| alan | eski (v35) | yeni (v36) |
|---|---|---|
| `model_id` | `navitas-seg-v35-512` | **`navitas-seg-v36-512`** |
| `path` | `models/navitas_seg_v35_best.pt` | **`models/navitas_seg_v36_best.pt`** |
| `sha256` | `e00f6b8e…` | **`1d1caca6…`** (ÖLÇÜLDÜ) |
| `imgsz` | 512 | 512 (DEĞİŞMEDİ) |
| `kabul_kumesi` | `…/sentetik_arena_kadraj_t66` | AYNI (ada geometrisi değişmedi) |
| `status` | competition | competition |

**`turevler`** — v36'nın dördü; `.engine`'ler yer tutucu (`DERLENINCE_YAZILIR` = RED, fail-closed),
iki `.onnx` **gerçek özetle** (adım 4'teki `--turev-kaydet` çıktısı). v35 türev girdileri
profilden **çıkarıldı** ve sebebi `_turevler_v35_notu` alanına yazıldı: kaynak artık v36
olduğu için `turev_dogrula` onları **YETİM** sayıp RED dönerdi; defterde durmaları yalnız
yanıltıcı olurdu. **v35 dosyaları diskte ve saha paketinde duruyor.**

**`metrics`** — K0–K6 tek kabul koşumundan (`scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json`):

| ölçüt | eşik | v35 | **v36** | yön |
|---|---|---|---|---|
| K0 körlük (figür zemin) | körlük yok | %9,03 | **%2,66** | yetenek ↓ (tehlike değil) |
| K1 rota üretimi | ≥ 230 | 256/260 | **255/260** | −1 kare |
| K2 moloza basma | ≤ %15 | %7,03 (18/256) | **%5,88 (15/255)** | ✅ iyileşti |
| K3 ağır basma | ≤ %3 | %0,00 (0/256) | **%0,39 (1/255)** | 🔴 maliyet |
| K4 arena dışı | ≤ %5 | %0,39 (1/256) | **%1,57 (4/255)** | 🔴 maliyet |
| K5 bariyer kesişimi | = 0 px | 0/173 · 0 px | **0/172 · 0 px** | aynı |
| K6 rota yol üstünde | ≤ %5 | 5/256 | **7/255 (%2,75)** | 🔴 maliyet, kapı içinde |

`109` çıktısı (`results/gece_20260826/gece_v7a_olcum.json` → `k109`): çatı kaçağı **0,023**
(medyan 0,0119), kaplama67 içerik **0,4171** / tuval **0,2346**, figür zemin **0,0444**,
67 gerçek karede zemin maskesi reddi **0**.

**GERÇEK-KARE KAPISI** (CONTRACTS §12) `metrics.gercek_kare_kapisi` altına yazıldı:

| küme | ROTA | MASKE_YOK | TP | FP | YANLIŞ GÜZERGÂH |
|---|---:|---:|---:|---:|---:|
| test29 · **v36** | **8** (eşik ≥ 10 ✗) | **16** (eşik ≤ 10 ✗) | 7 | 1 (✔) | **0** (✔) |
| test29 · v35 tabanı | 6 | 16 | 5 | 1 | 5 |
| val82 · **v36** | 30 | 35 | 28 | 2 | 7 |
| val82 · v35 tabanı | 15 | — | 15 | 0 | 10 |

`k0_korluk.figur_zemin_orani` listesine **v36 satırı EKLENDİ**
(`deger 0.0266`, `donem_tutarli true`, kaynak = 65'in `kaplama()` fonksiyonu, gece_v7a kabul
koşumu). **Mevcut 8 satırın hiçbiri silinmedi** (`test_t132_taban_gorunurlugu` bunu kilitler).

**`karar_cevrilmesi` alanı `OLCULMEDI` yazıldı.** v35'in 9/260 değeri **taşınmadı** —
D-256 §3'ün kuralı bayat sayı taşımayı yasaklar. v36'nın bu eksende nerede durduğu
**bilinmiyor**; ölçülmeden "iyi" ya da "kötü" denmedi.

`_surum_karari` ve `_kapsam` emirdeki metinle yazıldı; `_kapsam`, DOĞRULAMA kümesinin
(0038, CONTRACTS §12) varlığını **ve** arena benzeri saha kanıtının **hâlâ olmadığını**
(T111/D-198 açık) birlikte söyler.

---

## 3. AYNA — `jetson_paket/config/model_registry.json`

```
$ diff config/model_registry.json jetson_paket/config/model_registry.json
(çıktı YOK — bayt-eş)
```

---

## 4. ONNX (fp16 · opset 17 · imgsz 512)

```
$ <venv> scripts/export_tensorrt.py --model models/navitas_seg_v36_best.pt \
    --imgsz 512 --cikti results/onnx_export_v36_20260826
ONNX uretiliyor: navitas_seg_v36_best.pt -> imgsz=512, FP16
ONNX: starting export with onnx 1.22.0 opset 17...
ONNX: export success 1.3s, saved as 'models\navitas_seg_v36_best.onnx' (52.0 MB)
  -> O:\navitas\results\onnx_export_v36_20260826\navitas_seg_v36_best_512_fp16.onnx
ONEMLI: .engine bu PC'de uretilmedi.
```

`onnx` paketi venv'de zaten kuruluydu (1.22.0) — pip adımına gerek kalmadı.
Çıkan dosya `jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx` ve
`models/navitas_seg_v36_best.onnx` olarak kopyalandı; **üçü de bayt-eş** (§0).

```
$ <venv> codes/model_registry.py --turev-kaydet models/navitas_seg_v36_best.onnx \
    --kaynak-pt models/navitas_seg_v36_best.pt
{"turev":"navitas_seg_v36_best.onnx","eski_sha256":"DERLENINCE_YAZILIR",
 "yeni_sha256":"f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab", ...}

$ <venv> codes/model_registry.py --turev-kaydet jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx \
    --kaynak-pt models/navitas_seg_v36_best.pt
{"turev":"navitas_seg_v36_best_512_fp16.onnx","eski_sha256":"DERLENINCE_YAZILIR",
 "yeni_sha256":"f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab", ...}
```

CLI dosya **YOLU** alır (adı profilde kayıtlı olmak zorunda), `--kaynak-pt` zorunludur ve
paket aynasını kendisi bayt-eş yazar (`codes/model_registry.py:turev_kaydet`).

---

## 5. Saha paketi künyesi — `jetson_paket/models/jetson_derleme_manifest.json`

Değişen alanlar: `pc_modeli`, `asil_model`, `asil_model_pt`, `onnxler`, `jetson_komutlari`,
`paket_yenilenme`; **`paket_icerigi`ne iki satır EKLENDİ** (sha ölçülerek), v35 ve öncesinin
satırları **kaldı**:

```
navitas_seg_v35_best.pt             54803804  e00f6b8e25dd65604755c3cead7840aeb0f9a0ff74fee45e8f5fe9dbf1dd438b
navitas_seg_v35_best_512_fp16.onnx  54569669  248ef808f8be20d700d089e33c727dcb9e336832ce87304352cd859b463c37d3
navitas_seg_v36_best.pt             54788636  1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911
navitas_seg_v36_best_512_fp16.onnx  54569673  f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab
```

Paket **ağırlık taşıyor** (v35 nasılsa öyle): `jetson_paket/models/` altına v36 `.pt` ve
512 fp16 `.onnx` kopyalandı. Betik, diskteki `.pt`/`.onnx` kümesinin künye listesiyle
**birebir** olduğunu yazmadan önce doğruladı (`test_uretim_modeli_hizasi` kalıbı).
Yeni `_t_terfi_v36` alanı kural dışı terfiyi ve v35'in yedek rolünü yazar.

---

## 6. Kılavuzlar ×2, testler, CONTRACTS

**`JETSON_KILAVUZ.md` (kök) + `jetson_paket/JETSON_KILAVUZ.md` — aynı 17 değişiklik:**
başlıkta `ASIL MODEL: v36`; **kural dışı terfi satırı** (ölçülen 8/16, geçilen FP 1 ve
YANLIŞ 0, "eşikler değiştirilmedi"); yedek satırı **v35** (v34 ikinci yedek);
`§0-T85` gövdesi, `§3` `jetson_fps` varsayılan tablosu, paket ağacı (v36 ASIL + v35 YEDEK
satırları), `§4` `yolo export … format=engine`, `yolo predict`, `--turev-kaydet` örneği,
`trtexec` yedeği, `§5` FPS komutu ve `--cikti`, `§6` INT8 komutu → hepsi **v36**.
**§6C** birincil→yedek yordamında `<YEDEK>` = **v35**: G1 metni, G2 doğrulama betiğindeki
dosya adları, G6 kısa koşum komutu.

⚠ **Emrin dışında düzeltilen bayatlık (kayda geçiyor):** §4 `trtexec --saveEngine=`, §5
`--engine` ve `--cikti` satırları **v30** diyordu — v30 en son 2026-08-15'te üretimdi.
Operatör bu satırları kopyalasa engine'i **yanlış adla** kaydeder ve FPS ölçümünü var
olmayan dosyayla ister. Aynı dosyada, aynı hizalama işinde olduğu için düzeltildi;
`test_uretim_modeli_hizasi` bu satırları **denetlemiyordu** (yalnız `ASIL` ve
`format=engine` satırlarına bakıyor) — kapının kör noktasıdır, ayrıca kayda geçti.

**Testler:**

| dosya | ne yapıldı | neden |
|---|---|---|
| `tests/test_model_registry.py` | v35 → **v36** (test adı, docstring, üç assert) | sürüm bump'ı terfinin **bilinçli** adımı; defterden türetilse test totolojik olurdu |
| `tests/test_t143_turev_ve_kamera.py` | `URETIM_PT` / `URETIM_SHA` / `ENGINE_ADI` ve türev ad kümesi v36 | aynı gerekçe; v35 türevleri profilden çıktığı için ad kümesi de değişti |
| `tests/test_gercek_arena_kapisi.py` | `ARENA_KAPLAMA` 0.1508 → **0.0444** (kenar 0.0000, değişmedi) | **DÜŞTÜ, sonra ölçüldü** — aşağıda |
| `tests/test_t132_taban_gorunurlugu.py` | `BEKLENEN_SURUMLER`/`DONEM_TUTARLI` += v36; üretim kimliği v36; karşı-olgusal filtresi | **DÜŞTÜ** — aşağıda |
| `tests/test_t123_gecis_provasi.py` | mutasyon testi yedek adlarını artık **yordamdan türetiyor** | **DÜŞTÜ** — aşağıda |
| `test_hakem_kunye_algi_hizasi` · `test_saha_parametrik` · `test_jetson_paket_defteri` · `test_imgsz_tek_kaynak` · `test_uretim_modeli_hizasi` | **ELLE DEĞİŞTİRİLMEDİ** | sürümü defterden türetiyorlar; hizanın gerçek kanıtı bunların kendiliğinden geçmesidir |

### 6.1 DÜŞEN TESTLER — önce **neden** düştüğü, sonra düzeltme

İlk `discover` koşumu: **2 FAIL + 1 ERROR**.

1. **`test_gercek_arena_kapisi` · `test_OLCULEN_degerler_SABITLERLE_tutarli` yolu.**
   Sabitler v35 ile ölçülmüştü (0.1508). **Bu düşüş kusur değil, kapının işidir** —
   dosyanın kendi yorumu bunu yazıyordu: *"Model değişince test yine 'bayat sabit' diye
   DÜŞECEK — bu bilinçli."* Yeni değer **uydurulmadı, ölçüldü**: testin zincirinin
   birebir aynısı (`_preprocess` → `predict(imgsz=INFER_SIZE, conf=0.30)` →
   `_maskeleri_icerige_kirp` → `zemin_kaplamasi`/`zemin_kenar_dayanmasi`), ağırlık
   **defterden çözülerek**:
   ```
   defterden cozulen: O:\navitas\models\navitas_seg_v36_best.pt navitas-seg-v36-512
   ARENA_KAPLAMA = 0.04439787550304883
   ARENA_KENAR   = 0.0
   zemin_maskesi_reddi: None
   ```
   Aynı sayı bağımsız olarak `109` koşumunda da var: `k109.figur_zemin_orani = 0.0444`.
   İki `skipTest` gerekçesi güncellendi (ikisi de v24 dönemi kilidi; v36'da da atlanıyor).
   ⚠ Bu figürde **yer gerçeği YOKTUR**: 0,1508 → 0,0444 düşüşü "daha doğru" değil
   **"daha az zemin"** demektir.

2. **`test_gercek_arena_kapisi` · `test_MODEL_kayit_defterinden_geliyor_CIVILI_DEGIL`.**
   Benim yazdığım açıklama yorumu `navitas_seg_v36_best.pt` **literalini** içeriyordu;
   D-266 kilidi dosyada hiçbir sürüm ağırlığı adı olmamasını şart koşuyor. Yorum
   sürüm adı geçmeyecek şekilde yeniden yazıldı — **kilit gevşetilmedi**, kilide uyuldu.

3. **`test_t132_taban_gorunurlugu` · `test_gercek_defterle_satir_URETIM_surumunu_yaziyor`.**
   Üretim kimliği artık v36; `v35` bekleyen assert v36'ya çevrildi. Ayrıca
   `BEKLENEN_SURUMLER`/`DONEM_TUTARLI` kümelerine v36 eklendi (kümeden **eksiltme** yok —
   kilitlenen şey "geçmiş silinmez"dir). Karşı-olgusal test (`…v34_gunu_16x_gorunurdu`)
   soyağacından v35'i çıkarıyordu; artık **v35 ve v36'yı** çıkarıyor — aksi hâlde
   "o gün" senaryosu kendi geleceğini de sayardı ve iddia sulanırdı.

4. **`test_t123_gecis_provasi` · `test_MUTASYON_kunyedeki_sha_bozulursa_UYUSMAZ_der` (ERROR).**
   `FileNotFoundError: …\jetson_paket\models\navitas_seg_v35_best.pt`. Sebep: mutasyon
   testi yedek adlarını **`navitas_seg_v34_best` olarak çivilemişti**; kılavuzdaki G2
   yordamı v35'i aramaya başlayınca geçici pakete v34 kopyalanıyor, G2 v35 arıyordu.
   Düzeltme: adlar artık **G2 bloğundan türetiliyor** (`re.findall`) — aynı dosyadaki
   diğer test zaten bu deseni kullanıyordu ve dosyanın docstring'i elle listenin
   bayatlamasını (D-146/157/159/163) uyarıyordu. Böylece sonraki terfide bu test
   **elle dokunulmadan** doğru yedeği sınar.

**`CONTRACTS.md` §12** sonuna İSTİSNA bloğu eklendi — ölçülen sayılar, karar dayanağı ve
*"eşikler DEĞİŞMEDİ, sonraki terfileri bağlar"* cümlesi ile.

---

## 7. DOĞRULAMA — hepsi terfiden **SONRA**, defterin gösterdiği yoldan

### 7.1 `resolve_model()`
```
RESOLVE: O:\navitas\models\navitas_seg_v36_best.pt
model_id: navitas-seg-v36-512 imgsz: 512 status: competition
```
`resolve_model(verify=True)` sha256'yı **gerçekten** doğrular; yani defterdeki özet
diskteki ağırlığın özetidir.

### 7.2 Kabul zinciri — yolu ELLE vermeden, defterden çözülen ağırlıkla
```
$ <venv> scripts/olcum/65_kabul_denetcisi.py --model O:/navitas/models/navitas_seg_v36_best.pt \
    --ad t_v36_dogrulama

KABUL DENETIMI · t_v36_dogrulama
  kabul kumesi: O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66
                parmak izi n=547 · sha256:604c037f78...
  K0 KORLUK YOK        GECTI  figur zemin %2.66 (uretim tabani %2.66 = v36'in degeri · oran 1.00)
                       raw bos 0/67 · cp bos 0/393
     SOYAGACI: v27 %7.84 · v30 %7.96 · v34 %0.49 · v35 %9.03 · v36 %2.66
     TABAN, soyagaci medyanindan (%7.84) 2.9x uzakta   <- SAYI, KURAL DEGIL
  K1 ROTA >= 230       GECTI       255/260
  K2 BASMA <= %15      GECTI       15/255   (taban %9,2)
  K3 AGIR  <= %3       GECTI       1/255   (taban %0)
  K4 ARENA DISI <= %5  GECTI       4/255
  K6 ROTA YOL USTUNDE <= %5  GECTI  yanlis guzergah 7/255
  K5 BARIYER = 0 px    GECTI       kesen 0/172 kare · toplam 0 px
  VERDIKT: URETIME ALINIR
json -> scripts/olcum/results/t63/t_v36_dogrulama_kabul_verdikt.json
```
**K0–K6 `gece_v7a` koşumuyla BİREBİR** (255/260 · 15/255 · 1/255 · 4/255 · 7/255 · 0 px ·
figür %2,66). Kabul kümesi parmak izi de aynı (`n=547`, `604c037f…`) — yani ölçüm aynı
dağılımda tekrarlandı.

> ⚠ **D-256 §4 kalıbıyla not:** K0 oranı artık **1,00** ve "DİKKAT" satırı basılmıyor —
> çünkü taban kaydı **v36'nın kendi değeri** oldu. Terfiden **önce** taban v35 (%9,03) idi
> ve oran **0,294** görünüyordu (yetenek yönü; "daha çok zemin" tehlike uyarısı değil).
> Terfi, kendisini uyaran referansı **yine kaydırdı**; tarihsel değer registry'deki
> `k0_korluk.not` alanında ve yukarıdaki soyağacı satırında **yazılı** kaldı.

### 7.3 Genel kapı ve tam süit
```
$ <venv> codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

$ <venv> -m unittest discover -s tests -q
Ran 962 tests in 72.250s
OK (skipped=2)
```
İki `skipped`: `test_gercek_arena_kapisi`'nin v24-dönemi kilitleri (kenar dayanma tavanın
altında; eski 0.55 tavanı bile aşılmıyor) — gerekçe metinleri v36 ölçümüyle güncellendi.

### 7.4 Ayna ve hiza
```
$ <venv> scripts/olcum_ayna.py --uygula --repodan
cift: 77 · AYRISAN: 0   (hepsi senkron)
0 cift hizalandi (repodan).

$ diff codes/*.py jetson_paket/kod/*.py        -> AYRIŞAN YOK
$ diff config/model_registry.json jetson_paket/config/model_registry.json -> BOŞ
```

---

## 8. Commit

Tek commit; `.pt` / `.onnx` dosyaları `.gitignore` kapsamında olduğu için **eklenmedi**
(`git check-ignore -v` ile doğrulandı: `.gitignore:41,130,132,133,148`).

Commit'e giren 11 izlenen dosya:
`CONTRACTS.md` · `JETSON_KILAVUZ.md` · `jetson_paket/JETSON_KILAVUZ.md` ·
`config/model_registry.json` · `jetson_paket/config/model_registry.json` ·
`jetson_paket/models/jetson_derleme_manifest.json` · `tests/test_model_registry.py` ·
`tests/test_t143_turev_ve_kamera.py` · `tests/test_gercek_arena_kapisi.py` ·
`tests/test_t132_taban_gorunurlugu.py` · `tests/test_t123_gecis_provasi.py`
(+ bu rapor).

---

## 9. AÇIK KALANLAR (kapatılmadı, kayda geçiyor)

1. **Ön kayıtlı ROTA ≥ 10 / MASKE_YOK ≤ 10 eşikleri v7a'da GEÇİLMEDİ (8/16).** Terfi
   kullanıcı kararıdır; eşikler yerinde durur ve sonraki terfileri bağlar.
2. **val82'de FP 0 → 2.** Çürütücünün KUSUR-3'ü: kare 223'te **yol olmayan** çorak
   tarlada 8 waypoint'lik rota üretiliyor; v35 orada MASKE_YOK (güvenli) idi. Bu
   **yeni ve gerçek** bir yanlış güzergâh riskidir.
3. **`karar_cevrilmesi` v36 için ölçülmedi.** v34 terfisinde bu eksen KAPIYDI (≤ 8/260);
   bugünkü zincirde kapı değil. Ölçülmediği için hüküm yok.
4. **Arena benzeri saha kanıtı YOK.** 0038 kırsal bir yol çekimidir; kırmızı H, moloz,
   bariyer içermez. T111/D-198 açık ve insan görevidir (DJI arena çekimi).
5. **`.engine` türevleri yer tutucu.** Jetson'da derlendikten sonra `--turev-kaydet`
   ile yazılacak; o güne kadar TensorRT yolu **fail-closed RED**.
6. **`test_uretim_modeli_hizasi` kör noktası** (§6'daki v30 bayatlığı): kılavuzdaki
   `--saveEngine` / `--engine` / `--cikti` satırları hiçbir kapı tarafından
   denetlenmiyor. Ayrı bir tur gerektirir.
