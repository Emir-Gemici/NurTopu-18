# T154 — Kılavuz hizalama kapısının kör noktası kapatıldı

**Tarih:** 2026-08-26 · **Kaynak kusur:** `REVIEW_LOG.md` **D-294 §4** · **Kuyruk:** `TASK_QUEUE.md` T154
**Worktree:** `O:\navitas\.claude\worktrees\wf_c2f3b81b-a6e-2` (branch `worktree-wf_c2f3b81b-a6e-2`)

---

## 0. Önce bir düzeltme: worktree BAYAT açılmıştı

Worktree `f1c5931` (T132, 2026-08-21) üzerinden açılmıştı — yani **v36 terfisinden önceki**
ağaç. Defterde `navitas-seg-v35-512` yazıyordu ve görevin dayandığı D-294/T154 hiç yoktu.

```
$ git log --oneline -1                       -> f1c5931 T132 UYGULANDI: K0 tabani...
$ git merge-base --is-ancestor f1c5931 master -> f1c5931 IS ancestor of master
$ git log --oneline master..HEAD              -> (bos)
$ git merge --ff-only master
$ git log --oneline -1                       -> 2b8c069 ON_KAYIT §16: v36 sonrasi dort is...
$ grep '"model_id"' config/model_registry.json | head -1
6:   "model_id": "navitas-seg-v36-512",
```

Yerel fast-forward; `pull`/`fetch`/`stash` **kullanılmadı**, dal ayrık commit taşımıyordu.

---

## 1. Kör nokta GERÇEKTEN ölçüldü (kapı boş değildi, KÖRDÜ)

Eski kapı (`KilavuzHizasiTests`, 4 test) yalnız `ASIL` ve `format=engine` içeren satırlara
bakıyordu. `--saveEngine=` satırına eski sürüm enjekte edildi ve **eski kapı yeşil yandı**:

```
mutant: --saveEngine=navitas_seg_v30_best_512_fp16.engine
$ <venv> -m unittest -v test_uretim_modeli_hizasi.KilavuzHizasiTests
test_ASIL_satiri_URETIM_surumunu_gosteriyor ... ok
test_FPS_komutu_URETIM_conf_esigini_kullaniyor ... ok
test_IKI_kilavuz_da_ASIL_satiri_TASIYOR ... ok
test_derleme_komutu_URETIM_surumunu_kullaniyor ... ok
Ran 4 tests in 0.004s
OK
geri alindi: sha256 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449
```

D-294 §4'ün iddiası **doğrulandı**: sahadaki insanın yapıştıracağı komut iki sürüm bayat
olabilirdi ve hiçbir kapı ses çıkarmazdı.

---

## 2. Yeni kapı — `KilavuzKomutSatirlariTests` (7 test)

`tests/test_uretim_modeli_hizasi.py`. Kural **tersine çevrildi**: kılavuzda model
ağırlığı/türevi adı ya da sürümlü bir çıktı yolu geçen **HER satır** üretim sürümünü
taşımak zorundadır; eski sürüm adı yalnız **açıkça ve gerekçesiyle** tanımlı bir istisnaya
düşerse meşrudur (fail-closed).

Denetlenen iki aile:

| aile | desen | örnek |
|---|---|---|
| ağırlık/türev adı | `navitas_seg_(v\d+)[\w]*\.(pt\|onnx\|engine)` | `--saveEngine=`, `--engine`, `--model`, `model=`, `--pt`, `--onnx`, `--turev-kaydet`, `--kaynak-pt`, tablo hücreleri, ağaç satırları |
| sürümlü çıktı yolu | `--cikti` sonrasında `_(v\d+)` | `--cikti results/jetson_fps_v36_$(date ...)` |

Bölüm bağlamı **başlık YOLUNDAN** çözülür (`## 6C.` + `### G4 · …`), kod çitleri
(` ``` `) içindeki `# 1a — JetPack…` gibi kabuk yorumları başlık sayılmaz.

### İstisna listesi (hepsi gerekçeli, hepsi CANLI olmak zorunda)

| istisna | koşul | izinli sürüm | gerekçe (özet) |
|---|---|---|---|
| `SS0-T76 (ASILDI)` | başlıkta `0-T76` **ve** `AŞILDI` | v27 | başlıkta açıkça "§0-T85 ile AŞILDI" yazar; ölçüm kaydıdır, koşulacak komut değil |
| `SS0-T58 (ASILDI)` | başlıkta `0-T58` **ve** `AŞILDI` | v24 | aynı gerekçe (§0-T76 ile aşıldı) |
| `Domain kontrolu (B1 tekrari)` | başlıkta `Domain kontrolü` | v17 | bloğun **amacı** B1'i (v17 kör) Jetson'da tekrarlamaktır; üretim modeliyle koşulursa ölçülmek istenen şey ölçülemez |
| `SS6C birincil->yedek gecis yordami` | başlıkta `6C.` **ve** `YEDEK` | **defterden**: `competition._yedek_surumler` | "yedek" bağlamı sürüm adını meşru kılan tek yerdir; ama izinli küme elle tutulmaz — defterde yedek olarak **kayıtlı olmayan** sürüm kılavuza yazılamaz |
| `Paket agac listesi (etiketli)` | ağaç satırı + `←` işareti | — | §2 ağacı komut değildir; ama eski sürümlü her ağaç satırı `YEDEK / eski asıl / referans / kıyas` etiketi taşımak **zorundadır** ve `← ASIL` satırı üretim sürümüne bağlıdır |

Listeyi kilitleyen iki test: `test_ISTISNA_kurallarinin_HEPSI_CANLI` (ölü istisna
birikemez — kılavuz değişince istisna da kalkar) ve `test_her_ISTISNAYA_gerekce_yazili`
(≥ 80 karakter gerekçe zorunlu). Ayrıca `test_KOR_NOKTA_satir_tipleri_GERCEKTEN_denetleniyor`
kapının **boşalmasını** engeller: üç satır tipinin her biri en az bir kez denetime girmeli.

---

## 3. 🔴 YENİ BULGU — kapı ilk koşuda gerçek bir bayat satır yakaladı

Kapı yazılır yazılmaz, hiçbir mutasyon yapılmadan, **iki kılavuzda da** düştü:

```
AssertionError: Lists differ: [] != [(623, '--zincir --model ~/navitas/models/[39 chars]17')]   (kök)
AssertionError: Lists differ: [] != [(726, '--zincir --model ~/navitas/models/[39 chars]17')]   (paket)
```

`§6B DroidCam → Algı zinciriyle canlı test` bloğu:

```bash
--zincir --model ~/navitas/models/navitas_seg_v17_best_640.engine \
--imgsz 640 --kare 60
```

**v17 en son 13 Ağustos'ta asıldı — yani bu satır ALTI sürüm bayattı** (v17 → v20/v21 →
v24 → v27 → v30 → v35 → v36) ve D-294'te sayılan `--saveEngine=`/`--engine`/`--cikti`
satırlarından **bile eski**ydi. Kimse görmemişti çünkü satır ne `ASIL` ne `format=engine`
içeriyor.

Düzeltildi (iki kılavuzda birebir): model `navitas_seg_v36_best_512_fp16.engine`,
`--imgsz 512`. Altındaki "Beklenti" paragrafı da **dürüstleştirildi**: eski metin
`MASKE_YOK ağırlıklı çıkar` diyordu, bu v17'ye ait B1 bulgusuydu; v36'nın DroidCam
görüntüsündeki davranışı **ÖLÇÜLMEDİ** ve öyle yazıldı. B1'i tekrar ölçmek isteyen için
§5 `Domain kontrolü` bloğunun bilerek v17'de durduğu not edildi.

---

## 4. MUTASYON KANITI — üç satır tipi, ayrı ayrı, TEK BAYT

Betik: `scratchpad/t154_mutasyon.py` (bayt düzeyinde; `write_text` CRLF'i bozup satır
numaralarını iki katına çıkardığı için tüm okuma/yazma `read_bytes`/`write_bytes`).

```
BASLANGIC sha256(JETSON_KILAVUZ.md) = 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449
  bayt = 39874 · CRLF = 821

### TUR 0 — BOZULMAMIS kapi: cikis 0
    Ran 26 tests in 0.038s |  | OK (skipped=7)

### MUTASYON `--saveEngine=`  (yalniz 1 bayt farkli)
    - --saveEngine=navitas_seg_v36_best_512_fp16.engine \
    + --saveEngine=navitas_seg_v30_best_512_fp16.engine \
    kapi cikis kodu = 1  -> DUSTU (beklenen)
      AssertionError: unexpectedly None : wf_c2f3b81b-a6e-2:399 `--saveEngine=` satiri v30 diyor, uretim v36
      AssertionError: Lists differ: [] != [(399, '--saveEngine=navitas_seg_v30_best_512_fp16.engine \\', 'v30')]
    geri alindi -> sha256 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449 (BAYT-ES)

### MUTASYON `--engine`  (yalniz 1 bayt farkli)
    - --engine models/navitas_seg_v36_best_512_fp16.engine \
    + --engine models/navitas_seg_v35_best_512_fp16.engine \
    kapi cikis kodu = 1  -> DUSTU (beklenen)
      AssertionError: unexpectedly None : wf_c2f3b81b-a6e-2:413 `--engine` satiri v35 diyor, uretim v36
      AssertionError: Lists differ: [] != [(413, '--engine models/navitas_seg_v35_best_512_fp16.engine \\', 'v35')]
    geri alindi -> sha256 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449 (BAYT-ES)

### MUTASYON `--cikti`  (yalniz 1 bayt farkli)
    - --cikti results/jetson_fps_v36_$(date +%Y%m%d_%H%M%S)
    + --cikti results/jetson_fps_v30_$(date +%Y%m%d_%H%M%S)
    kapi cikis kodu = 1  -> DUSTU (beklenen)
      AssertionError: unexpectedly None : wf_c2f3b81b-a6e-2:416 `--cikti` satiri v30 diyor, uretim v36
      AssertionError: Lists differ: [] != [(416, '--cikti results/jetson_fps_v30_$(date +%Y%m%d_%H%M%S)', 'v30')]
    geri alindi -> sha256 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449 (BAYT-ES)

### SON — geri alinmis dosyayla kapi: cikis 0
    Ran 26 tests in 0.041s |  | OK (skipped=7)
SON sha256 = 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449  (baslangic 66aab63179071f3f4306d4847dc40a807ec9ab46f27454811c908497e46e5449)
```

⚠ `--engine` turunda enjekte edilen sürüm **v35**tir; v35 defterde `_yedek_surumler`
altında **kayıtlıdır** ve §6C'de yazılması meşrudur. Kapı yine de düştü — istisna
**bölüme bağlıdır**, sürüme değil. Yani "yedek adı geçebilir" kaçağı yok.

---

## 5. İkinci madde (D-294 §4) — `figur_zemin_orani`: aynı ad, iki ölçüm hattı

**Alan adı DEĞİŞTİRİLMEDİ** (görevin şartı; `65_kabul_denetcisi.py`,
`scripts/olcum/118_t131_kayma_defteri.py`, `tests/test_k0_gorunurlugu.py`,
`tests/test_t132_taban_gorunurlugu.py` bu adı okuyor — D-263 §5). Bunun yerine defterde
`metrics.k0_korluk._iki_olcum_hatti_notu` alanı açıldı ve `_surum_karari`'ndaki sayının
yanına hangi hat olduğu yazıldı.

| hat | alan | betik | payda | v35 | v36 |
|---|---|---|---|---|---|
| 65 (kabul zinciri) | `k0_korluk.figur_zemin_orani`, `olculen` | `scripts/olcum/65_kabul_denetcisi.py::kaplama()` → `(mk[0] > 0).mean()` | **LETTERBOX TUVAL** | 0,0903 | **0,0266** |
| k109 | `_surum_karari` metni ("figür zemin 0,15→0,04"), D-293/D-294 | `scripts/olcum/109_t122_kiyas.py` → `zemin_ve_mevcut_engel` → `alani_kirp` | **İÇERİK dikdörtgeni** | 0,1508 | **0,0444** |

**İkisi çelişmiyor; fark PAYDA — ve bu ÖLÇÜLDÜ (model yüklenmeden, yalnız OpenCV):**

```
$ <venv> -c "import cv2; img=cv2.imread(r'O:/navitas/data/arena_referans/sartname_s9_arena.png'); ..."
figur HxW = 634 1059  tuval yan = 1059
icerik/tuval orani = 0.598678
65/109 v36 orani  = 0.599099      (0,0266 / 0,0444)
65/109 v35 orani  = 0.598806      (0,0903 / 0,1508)
```

Ham kaynaklar: `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json` →
`olcum.K0.figur = 0.026580031226565586`; `results/gece_20260826/gece_v7a_olcum.json` →
`k109.figur_zemin_orani = 0.0444`.

Kilit: **`tests/test_k0_iki_olcum_hatti.py`** (7 test). Not "güzel bir cümle" olmaktan
çıkarılıp sayıya bağlandı: kapı figürün kendi geometrisinden içerik/tuval oranını yeniden
hesaplar ve iki hattın oranıyla karşılaştırır (delta 0,01).

### Mutasyon (defter)

```
BASLANGIC sha256(config/model_registry.json) = 49cdfef449c8b96b3c249b42eea46d1161e8be4f078609b187a5d98c8e2bea1c

### MUTASYON (a) 65 hattinin sayisi k109 sayisiyla DEGISTIRILDI (iki hat ayni sanildi)
    kapi cikis = 1 (DUSTU (beklenen))
      AssertionError: 0.5986779981114259 != 1.0 within 0.01 delta (0.40132200188857414 difference) :
        v36: 65 hatti 0.0444 / k109 hatti 0.0444 = 1.0000, oysa figurun icerik/tuval orani 0.598678.
      AssertionError: ... test_AYNA_defter_BAYT_ES ... jetson_paket defter aynasi kok defterden farkli
    geri alindi -> 49cdfef449c8b96b3c249b42eea46d1161e8be4f078609b187a5d98c8e2bea1c BAYT-ES

### MUTASYON (b) aciklayici NOT alani silindi (alan adi bozuldu)
    kapi cikis = 1 (DUSTU (beklenen))
      AssertionError: '_iki_olcum_hatti_notu' not found in {...}
      AssertionError: '65_kabul_denetcisi.py' not found in '' ... (7 alt-testin hepsi)
    geri alindi -> 49cdfef449c8b96b3c249b42eea46d1161e8be4f078609b187a5d98c8e2bea1c BAYT-ES

### SON geri alinmis kapi: 0 OK
```

Ayna (`jetson_paket/config/model_registry.json`) **bayt-eş** yazıldı ve kapı bunu da
kilitliyor (`test_AYNA_defter_BAYT_ES`):

```
ayna BAYT-ES: True  sha256 49cdfef449c8b96b3c249b42eea46d1161e8be4f078609b187a5d98c8e2bea1c
```

---

## 6. KAPILAR

```
$ <venv> codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

$ <venv> -m unittest discover -s tests -q
Ran 976 tests in 63.674s
FAILED (failures=4, errors=11, skipped=16)
```

**976 = 962 (ana dizin tabanı) + 14 yeni test** (7 `KilavuzKomutSatirlariTests` +
7 `test_k0_iki_olcum_hatti`).

🔴 **15 kırmızı, T154'ten DEĞİL — worktree'de model ağırlıkları ve `data/arena_kompozit`
yok** (`.gitignore:132`). Bu iddia tahmin değil, **ölçüldü**: ilgili beş modül önce
T154 değişiklikleriyle (A), sonra defterler `git checkout HEAD --` ile tabana döndürülüp
(B) koşuldu:

```
### A · SIMDIKI (T154 degisiklikleri ICINDE)
  A · test_saha_parametrik:        Ran 20 tests FAILED (failures=1, errors=6)
  A · test_t123_gecis_provasi:     Ran  6 tests FAILED (failures=1, errors=3)
  A · test_model_registry:         Ran  4 tests FAILED (errors=1)
  A · test_imgsz_tek_kaynak:       Ran  9 tests FAILED (failures=1, errors=1)
  A · test_yks_gui_uretim_hizasi:  Ran 54 tests FAILED (failures=1)
### B · TABAN (defter HEAD'e donduruldu)
  B · test_saha_parametrik:        Ran 20 tests FAILED (failures=1, errors=6)
  B · test_t123_gecis_provasi:     Ran  6 tests FAILED (failures=1, errors=3)
  B · test_model_registry:         Ran  4 tests FAILED (errors=1)
  B · test_imgsz_tek_kaynak:       Ran  9 tests FAILED (failures=1, errors=1)
  B · test_yks_gui_uretim_hizasi:  Ran 54 tests FAILED (failures=1)

A == B ? True (15 bulgu)
geri: model_registry.json 49cdfef449c8b96b3c249b42eea46d1161e8be4f078609b187a5d98c8e2bea1c
```

Kırmızı kümesi **birebir aynı**. Örnek hata metni de sebebi söylüyor:
`Manifest 'navitas_seg_v36_best.pt' diyor ama agirlik diskte YOK`.

⚠ **ÖLÇÜLEMEDİ:** ana dizindeki (`O:\navitas`) 962 OK / 2 skip sayısı bu worktree'den
doğrulanamaz — ağırlıklar orada. Birleştirme sonrası ana dizinde beklenen **976 OK /
2 skip**tir; ayrı bir koşumla teyit edilmelidir.

---

## 7. Değişen dosyalar

| dosya | ne |
|---|---|
| `tests/test_uretim_modeli_hizasi.py` | +`KilavuzKomutSatirlariTests` (7 test), istisna listesi, bölüm-yolu çözücü |
| `tests/test_k0_iki_olcum_hatti.py` | **YENİ** — iki ölçüm hattı kilidi (7 test) |
| `JETSON_KILAVUZ.md` | §6B canlı test satırı v17/640 → v36/512; "Beklenti" dürüstleştirildi (ÖLÇÜLMEDİ) |
| `jetson_paket/JETSON_KILAVUZ.md` | aynısı (kök kopyayla aynı blok) |
| `config/model_registry.json` | `k0_korluk._iki_olcum_hatti_notu` eklendi; `_surum_karari`'ndaki figür sayısına hat işareti |
| `jetson_paket/config/model_registry.json` | bayt-eş ayna |

`codes/` ve `comms/` altında **hiçbir şey değişmedi**, dolayısıyla `jetson_paket/kod`
aynalarında güncellenecek bir şey yok (`git status` yalnız yukarıdaki altı dosyayı
gösteriyor).

---

## 8. Açık kalanlar

1. **REVIEW_LOG D numarası verilmedi.** §3'teki yeni bulgu (v17 canlı-test satırı, altı
   sürüm bayat) `REVIEW_LOG.md`'ye **yazılmadı**: aynı gece §16'daki dört iş paralel
   worktree'lerde koşuyor ve D numarası çakışma riski var. Numarayı ve kaydı **mimar**
   vermeli; kanıt bu raporda tam.
2. **§6B canlı testin v36 ile davranışı ÖLÇÜLMEDİ.** Kılavuzdaki satır düzeltildi ama
   DroidCam görüntüsünde v36'nın ne ürettiği bilinmiyor (donanım gerekir). Kılavuzda
   böyle yazılı.
3. **Kapı hâlâ SATIR TABANLIDIR.** Kılavuzun düz metninde sürüm adı geçen cümleler
   (ör. "v17, v20, v21, v24, v27 ve v30 aynı mimaridir") denetlenmiyor — bunlar dosya
   adı taşımadığı için kalıba girmiyor. Bilinçli sınır: komut olmayan cümleye üretim
   sürümü dayatmak tarihsel kaydı bozardı.
4. **Ana dizin koşumu** (§6 sonundaki 976 OK / 2 skip beklentisi) teyit edilmeli.
