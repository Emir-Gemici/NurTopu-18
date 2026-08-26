# T157 — T154 kapısının kalan delikleri (D-295 §4)

**Tarih:** 2026-08-26 · **Ön kayıt:** `results/gece_20260826/ON_KAYIT.md` §17
**Üretim modeli:** `v36` (kayıt defterinden çözüldü: `comms/yks_gui.py::ALGI_MODEL_DOSYA`
→ `navitas_seg_v36_best.pt`; `config/model_registry.json :: profiles.competition.imgsz = 512`)
**Yorumlayıcı:** `O:\navitas-local-train\venv\Scripts\python.exe` · GPU koşulmadı (iki iş de metin/sentetik)

---

## 0. Ön kaydın dediği

> **T157:** üç delik (imgsz, uzantısız yol, çıplak `vNN` başlık) için ayrı mutasyon;
> ayrıca kılavuz satır 15'teki bayat başlık ("v27 → v30", gövde v36) düzeltilir.
> Kapı: mutasyonda test DÜŞMELİ.

Beşi de kapatıldı. Üçü (a/b/c) için **ayrı mutasyon kanıtı** var; (d) ve (e) için de
mutasyon koşuldu (ön kayıt istemiyordu, yine de ölçüldü).

---

## 1. (c) — KARAR: başlık **BAYATTI**, tarihsel değil

`JETSON_KILAVUZ.md:15` şöyleydi:

```
## 0-T85. GÜNCELLEME 2026-08-15 — **asıl model v27 → v30** (çözünürlük 512, değişmedi)
```

aynı bölümün gövdesi (satır ~20) ise `navitas_seg_v36_best_512_fp16.onnx` diyordu.

**Karar: BAYAT — düzeltildi.** Gerekçe, belgenin KENDİ kuralından çıkıyor:

| bölüm | başlıkta ne yazıyor | tarihsel mi |
|---|---|---|
| `## 0-T76.` | `*(§0-T85 ile AŞILDI)*` | **evet** — aşıldığı başlıkta yazılı |
| `## 0-T58.` | `*(§0-T76 ile AŞILDI)*` | **evet** — aynı |
| `## 0-T85.` | (hiçbir aşılma etiketi yok) | **hayır** |

§0-T85 **CANLI** bölümdür: (1) `AŞILDI` etiketi taşımaz, (2) gövdesi "bugün derlenecek
ve koşulacak model" cümlesini taşır, (3) `§4. TensorRT engine derle` ona **"§0-T85
zinciri, güncel karar D-293"** diye atıf yapar. Yani bölüm okuyucuyu yönlendiren canlı
çapa; başlığı ise v30'da donmuştu — v30 en son **2026-08-15**'te üretimdi, arada
v34 → v35 → v36 geçti. **İki sürüm bayat.** Tarihsel bir kayıt olsaydı diğer ikisi gibi
`AŞILDI` etiketlenir ve istisna listesine öyle girerdi.

Düzeltme (her iki aynada birebir, `read_bytes`/`write_bytes`):

```
- ## 0-T85. GÜNCELLEME 2026-08-15 — **asıl model v27 → v30** (çözünürlük 512, değişmedi)
+ ## 0-T85. GÜNCELLEME 2026-08-15 — **asıl model v27 → v30** (çözünürlük 512, değişmedi) *(zincir SÜRDÜ — bugünün asıl modeli **v36**, D-293)*
```

Terfi kaydı (v27 → v30 ölçüm tablosu) **silinmedi** — bölüm hem kayıt hem canlı çapa
olmayı sürdürüyor, ama artık okuyucuya bugünün modelini de söylüyor.

🔴 **İstisna boş değil.** `BASLIK · SS0-T85 surum zinciri` kuralı `uretim_de_yazili: True`
taşır: başlık **üretim sürümünü de yazmak zorundadır**. v37 geldiğinde başlık
güncellenmezse kapı düşer. Mutasyon (c) tam bunu ölçüyor.

---

## 2. Değişen dosyalar

| dosya | ne |
|---|---|
| `tests/test_uretim_modeli_hizasi.py` | (a) `--imgsz` kapısı · (b) uzantısız yol deseni · (c) başlık kapısı · (d) ağaç istisnası bölüme bağlandı |
| `tests/test_k0_iki_olcum_hatti.py` | (e) taban (v35) k109 sayısı ham JSON'a bağlandı |
| `JETSON_KILAVUZ.md` | (c) §0-T85 başlığı düzeltildi |
| `jetson_paket/JETSON_KILAVUZ.md` | (c) ayna — birebir aynı düzeltme |

Kod/config aynaları (`jetson_paket/kod`, `jetson_paket/config`) **dokunulmadı** —
bu işte üretim kodu ya da defter değişmedi. Kılavuz aynası ise **ikisi de** düzeltildi:
`diff JETSON_KILAVUZ.md jetson_paket/JETSON_KILAVUZ.md` çıktısında **`0-T85` geçmiyor**
(0 satır), yani başlık farkı YOK; diff'te duran 160 satır §0-A/G1–G4/kod ağacı gibi
**bilerek ayrı** olan paket bağlamıdır (kılavuzun kendi metni bunu yazıyor).

**CRLF hijyeni** (dört dosya da, `read_bytes`/`write_bytes` ile yazıldı):

```
JETSON_KILAVUZ.md:                    LF=821 CRLF=821 SAF_LF=0 BOM=False
jetson_paket/JETSON_KILAVUZ.md:       LF=924 CRLF=924 SAF_LF=0 BOM=False
tests/test_uretim_modeli_hizasi.py:   LF=952 CRLF=952 SAF_LF=0 BOM=False
tests/test_k0_iki_olcum_hatti.py:     LF=231 CRLF=231 SAF_LF=0 BOM=False
```

---

## 3. Deliklerin kapatılışı

### (a) `--imgsz` denetlenmiyordu

Kılavuzdaki kabuk komutları `\` ile satıra bölünüyor: model adı bir satırda, `--imgsz`
bir aşağıda. Satır satır bakan kapı ikisini **ilişkilendiremiyordu**. Yeni kapı:

1. `_mantiksal_komutlar()` devam satırlarını **birleştirir**;
2. beklenen boyut, komuttaki model dosya adının **kendi damgasından** çözülür
   (`navitas_seg_v36_best_512_fp16.onnx` → 512);
3. damga yoksa beklenen boyut **defterden** gelir (`competition.imgsz`, madde 16 —
   çıplak 512 yazılmadı);
4. çelişkili damga (aynı komutta hem 512 hem 640) kapıyı düşürür.

Ayrıca `test_URETIM_modelinin_damgasi_DEFTERDEKI_imgsz`: kılavuzun ürettiği
`..._512_fp16` damgası defterin `imgsz`inden **sapamaz**.

**Tek istisna** (`Karar kıyası` bloğu, 640): `for M in v21 v17 v20` döngüsü model adını
kabuk değişkeniyle kurar, damga yoktur ve blok üç ESKİ modeli kendi döneminin 640
boyutunda kıyaslar (§0-T76'ya kadar üretim 640'tı). **Boş istisna değil:** blokta
üretim sürümünün adı geçerse istisna DÜŞER.

Kapı boş değil kanıtı: her iki kılavuzda da hem `--imgsz` hem damgalı model adı taşıyan
**≥ 5** mantıksal komut sayılıyor (`test_IMGSZ_kapisi_BOS_DEGIL`).

### (b) Uzantısız model yolu kaçıyordu

`MODEL_DOSYA_DESENI` uzantı şart koşuyordu. Ölçüldü:

```
satir      :   --engine models/navitas_seg_v30_best_512_fp16 \
ESKI desen : [] <- KOR (kapi bos liste gorur, satiri hic denetlemez)
YENI desen : ['v30'] <- yakaliyor
```

Uzantı **isteğe bağlı** yapıldı. Kılavuzda hâlihazırda uzantısız `navitas_seg_` geçişi
YOK (`grep` ile bakıldı, iki aynada da 0 satır), yani desen genişlemesi mevcut hiçbir
satırı yeni bir istisnaya sokmadı. Ayrıca `test_UZANTISIZ_model_yolu_da_DENETLENIYOR`
dört biçimi de (`.pt`/`.onnx`/`.engine`/uzantısız) doğrudan sınıyor.

### (c) Çıplak `vNN` başlık metni

Yeni sınıf `KilavuzBaslikSurumuTests`: **her başlık satırındaki** çıplak `vNN` ya üretim
sürümüdür ya da **yazılı gerekçeli** bir istisnaya düşer. Kod çerçevesi (` ``` `) içindeki
`# ...` kabuk yorumları başlık sayılmaz (mevcut `_bolumlu_satirlar` mantığı yeniden
kullanıldı).

Üç istisna, üçü de bölüme bağlı ve gerekçeli:

| istisna | nerede | izinli | çapa |
|---|---|---|---|
| `BASLIK · asilmis GUNCELLEME kaydi` | başlıkta `GÜNCELLEME` **ve** `AŞILDI` | v21, v24, v27 | etiket kalkarsa istisna düşer |
| `BASLIK · SS0-T85 surum zinciri` | `0-T85` + `zincir SÜRDÜ` | v27, v30 | **başlık üretim sürümünü de yazmak zorunda** |
| `BASLIK · SS0 B1/B2 v17 bulgulari` | `0. ÖNCE OKU` | v17 | konusu v17'nin kendisi; çevrilirse başlık yalan söyler |

### (d) Ağaç istisnası bölüm bağlamına bağlı değildi

`_istisna_bul` içinde `agac` dalı `baslik_icerir` denetiminden **önce** dönüyordu, yani
kural belgenin tamamına uyuyordu. Sıra tersine çevrildi ve kurala
`baslik_icerir: ("2.", "Paketi Jetson'a taşı")` eklendi. Doğrudan sınandı: SS9 başlığı
altına konan `├── navitas_seg_v17_best.pt  ← yedek model` satırı artık istisnaya
DÜŞMÜYOR, SS2'deki meşru satır ise düşüyor.

### (e) `k109_v35 = 0.1508` çıplaktı

**Kaynağa bağlandı.** v36 bacağı zaten `results/gece_20260826/gece_v7a_olcum.json`
okuyordu; taban bacağı elle kopyalanmış bir sayıyı kıyaslıyordu.

Artık iki **ayrı** v35 koşumu okunur:
`results/gece_20260826/v35_ref2_olcum.json` (0,15084) ve
`results/t152/v35_t152_olcum.json` (0,15084). İkisi de git'te izleniyor.

Sürüm de testin metninden değil **ölçüm çıktısından** çözülüyor: JSON'ın `agirlik`
alanı (`models\navitas_seg_v35_best.pt`) → `v35`. Yani ne sayı ne sürüm çıplak.

Ek kapı (`test_TABAN_sayisi_CIPLAK_degil_HAM_JSONDAN`): k109 figür ölçümü şartname
figüründen türer, dolayısıyla **iki farklı koşumda aynı çıkmak zorundadır**; ayrışırsa
kapı düşer. Ayrıca taban kaynağının üretim sürümünü göstermediği doğrulanır.

---

## 4. MUTASYON KANITI (kök satırı boz → test DÜŞER → bayt-eş geri al)

Betik: `mutasyon.py <a|b|c|d|e> <uygula|geri>` — yedek SHA256 ile alınır, geri alma
bayt-eş doğrulanır. Ham çıktılar: `results/t157/mutasyon_{a,b,c,d,e}.log`.

### (a) `--imgsz 512` → `--imgsz 640` (§5 ASIL FPS bloğu, v36/512 modelleriyle)

```
YEDEK sha256 = 47f1969df17a37d494aeb5a5f8a4838ac5c4a591e4648d800b7762a5d89bbe57
MUTASYON uygulandi: JETSON_KILAVUZ.md
  - '  --imgsz 512 \\\r\n  --isinma 15 --tekrar 120'
  + '  --imgsz 640 \\\r\n  --isinma 15 --tekrar 120'
BOZUK  sha256 = d6a666a5aa3ca67f1ccb31b3f9787567b2836aa0060cad0afa129131799614da
```

```
FAIL: test_KOMUTTAKI_imgsz_MODEL_dosyasinin_boyutuyla_AYNI ... (satir=409, imgsz=640)
AssertionError: unexpectedly None : wf_a3528b62-8d1-2:409 komutu `imgsz 640` diyor,
beklenen 512 (komuttaki model dosya adinin cozunurluk damgasi); sahadaki kisi modeli
YANLIS cozunurlukte kosar ve olcum kiyaslanamaz hale gelir (T157/a)
Ran 37 tests in 0.052s
FAILED (failures=1, skipped=7)
```

```
GERI ALINDI: JETSON_KILAVUZ.md
BAYT-ES? True  sha256 = 47f1969df17a37d494aeb5a5f8a4838ac5c4a591e4648d800b7762a5d89bbe57
```

### (b) `--engine models/navitas_seg_v36_best_512_fp16.engine` → `--engine models/navitas_seg_v30_best_512_fp16` (uzantısız, eski sürüm)

```
MUTASYON uygulandi: JETSON_KILAVUZ.md
BOZUK  sha256 = 366ac0d2cd394b81e0d95bc1cdb5ff47420f957fd7c83ad8dfd2c558f3934453
```

```
FAIL: test_kor_noktanin_UC_satir_tipi_URETIM_surumunde ... (isaret='--engine', satir=413)
FAIL: test_model_dosyasi_gecen_satirlar_URETIM_surumunu_TASIYOR ...
Ran 37 tests in 0.050s
FAILED (failures=2, skipped=7)
```

Eski desenin bu satırda **kör** olduğu ayrıca ölçüldü (§3-b çıktısı).

```
GERI ALINDI: JETSON_KILAVUZ.md
BAYT-ES? True  sha256 = 47f1969df17a37d494aeb5a5f8a4838ac5c4a591e4648d800b7762a5d89bbe57
```

### (c) §0-T85 başlığından üretim sürümü silinir (yani düzeltme öncesi hâl)

```
MUTASYON uygulandi: JETSON_KILAVUZ.md
  - ' *(zincir SÜRDÜ — bugünün asıl modeli **v36**, D-293)*'
  + ''
BOZUK  sha256 = 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449
```

```
FAIL: test_BASLIKTAKI_ciplak_surum_URETIME_veya_ISTISNAYA_bagli ... (satir=15, surum='v27')
FAIL: test_BASLIKTAKI_ciplak_surum_URETIME_veya_ISTISNAYA_bagli ... (satir=15, surum='v30')
FAIL: test_CANLI_bolumun_basligi_URETIM_surumunu_de_YAZIYOR ...
Ran 37 tests in 0.050s
FAILED (failures=3, skipped=7)
```

```
GERI ALINDI: JETSON_KILAVUZ.md
BAYT-ES? True  sha256 = 47f1969df17a37d494aeb5a5f8a4838ac5c4a591e4648d800b7762a5d89bbe57
```

> 🔴 Bu mutasyon aynı zamanda **kapının ilk koşuda gerçek kusuru yakaladığının** kanıtı:
> düzeltme yapılmadan önce kapı tam bu üç testte, aynı satırda (15), iki aynada birden
> kırmızı yanmıştı (7 fail). Yani (c) uydurulmuş bir kusur değil, **ölçülmüş** bir kusurdu.

### (d) SS9'a etiketli ağaç satırı konur (bölüm dışına)

```
MUTASYON uygulandi: JETSON_KILAVUZ.md
815:├── navitas_seg_v17_best.pt              ← yedek model     (SS9 altinda)
FAIL: test_model_dosyasi_gecen_satirlar_URETIM_surumunu_TASIYOR ...
Ran 37 tests in 0.053s
FAILED (failures=1, skipped=7)
GERI ALINDI: BAYT-ES? True  sha256 = 47f1969df17a37d494aeb5a5f8a4838ac5c4a591e4648d800b7762a5d89bbe57
```

Düzeltme öncesi bu satır **hiçbir kapıya takılmıyordu** (etiketli olduğu için `agac`
istisnası belgenin her yerinde geçerliydi).

### (e) `v35_ref2_olcum.json` içindeki k109 sayısı bozulur

```
MUTASYON uygulandi: results/gece_20260826/v35_ref2_olcum.json
  - '"figur_zemin_orani": 0.15084'
  + '"figur_zemin_orani": 0.11'
BOZUK  sha256 = c96cfa4af30530ebebc1800eaa6a9d48dbd99420bf06f0052afbf80d85a18051
```

```
FAIL: test_TABAN_sayisi_CIPLAK_degil_HAM_JSONDAN
FAIL: test_TABAN_surumde_de_ayni_PAYDA_orani
Ran 8 tests in 0.043s
FAILED (failures=2)
GERI ALINDI: BAYT-ES? True  sha256 = b7a225a5636fc11b963895d114a865796c14715da8cb5e82e941db1ad3983328
```

Çıplak sabit dururken bu mutasyon testi **hiç etkilemezdi** — bağlantının gerçek
olduğunun kanıtı budur.

---

## 5. Kapılar

### Genel kapı — 15/15

```
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI
```
(`results/t157/kapi_15.log`)

### `unittest discover`

```
ONCE  (HEAD, degisiklik yok): Ran 976 tests in 65.081s — FAILED (failures=4, errors=11, skipped=16)
SONRA (T157 ile)            : Ran 988 tests in 69.071s — FAILED (failures=4, errors=11, skipped=16)
```

🔴 **Kırmızı kümesi ÖNCE/SONRA birebir aynı** — `diff` ile ölçüldü, çıkış 0:

```
diff once.txt sonra.txt ; diff_rc=0 (ONCE ve SONRA kirmizi kumesi BIREBIR AYNI)
```

**Bu 15 kırmızı T157'nin değil, WORKTREE'nin sonucudur.** Hepsinin gövdesi ya
"ağırlık diskte YOK" ya da eksik görüntü dizinidir:

```
7 × RuntimeError: Manifest `navitas_seg_v36_best.pt` diyor ama agirlik diskte YOK
      (bakilan: ...\wf_a3528b62-8d1-2\jetson_paket\models, ...\wf_a3528b62-8d1-2\models)
3 × FileNotFoundError: ...\jetson_paket\models\navitas_seg_v35_best.pt
2 × AssertionError (ayni RuntimeError metnini bekleyen kiyaslar)
1 × AssertionError: [] is not true : kompozit kume bos listelendi
1 × AssertionError: False is not true  (PAKET/models/<birincil>.exists())
```

Ağırlıklar (`*.pt`, `*.onnx`) ve `data/arena_kompozit` `.gitignore` ile depo dışındadır,
worktree'de yoktur. Master'da (ağırlıkların bulunduğu `O:\navitas`) beklenen 976 → 988
test, OK/2 skip. **Bu worktree'de master'ın "976 OK" tabanı DOĞRULANAMADI (ÖLÇÜLEMEDİ);
ölçülebilen şey ÖNCE/SONRA farkının SIFIR olmasıdır** ve ölçülen budur.

Ham çıktılar: `results/t157/unittest_discover_ONCE.log`, `results/t157/unittest_discover.log`.

### T157 kapıları (yalnız değişen modül)

```
Ran 37 tests in 0.047s
OK (skipped=7)
```
(`results/t157/t157_kapilar.log`; 7 skip = model ağırlıkları worktree'de yok)

`tests/test_k0_iki_olcum_hatti.py`: `Ran 8 tests — OK`.

---

## 6. Açık kalanlar

1. **Master'daki 976/988 OK tabanı bu worktree'de ölçülemedi** (ağırlıklar yok).
   Birleştirmeden sonra `O:\navitas`'ta `discover` bir kez koşulmalı.
2. **(e) kaynak seçimi bir KARAR taşıyor:** taban olarak `v35_ref2` + `t152/v35_t152`
   seçildi. k109 figür ölçümü figürden türediği için beş ayrı v35 koşumunun hepsi
   0,15084 veriyor (ölçüldü), yani seçim sayıyı değiştirmiyor — ama "hangi koşum
   TABAN'dır" sorusu hâlâ defterde yazılı değil; not alanı yalnız v36 bacağının
   JSON'ını (`gece_v7a_olcum.json`) anıyor. Defter notunun taban kaynağını da anması
   ayrı bir iş olarak açılabilir (bu işte deftere dokunulmadı).
3. **Başlık kapısı yalnız `vNN` biçimini görüyor.** "asıl model **v30**" yakalanır;
   "asıl model 512'lik son sürüm" gibi sürüm adı geçirmeyen bayat bir başlık
   yakalanmaz. Ölçülmedi, sınır olarak yazılıyor.
