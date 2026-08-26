# T155 — üretim yolunun yayınladığı ŞERİT NUMARASI düzeltildi (6/15 → 15/15)

**Tarih:** 2026-08-26 · **Ön kayıt:** `results/gece_20260826/ON_KAYIT.md` §17 (sonuç görülmeden)
**Karar kaydı:** `REVIEW_LOG.md` D-296 · **Sözleşme:** `CONTRACTS.md` §6.2
**GPU koşulmadı** (iki iş de sentetik/metin, görev şartı). **Model koşulmadı.**

---

## 1. Kusur ve mekanizması

Üretim yolu `road`'u `olcum["darbogaz_serit"]`ten yayınlıyordu — **rotanın en dar
noktasının**, yani **tek pikselin** şeridi. Yer gerçekli 15 arena sahnesinde **6/15** doğru.

🔴 **Mekanizma ölçüldü:** o tek piksel 15 sahnenin **13'ünde rotanın UCUNDA** ölçülüyor
(y=39 ya da y=460, tuval 500 px). KB/HB yakınında üç güzergâh **birleşir** — yani şerit
kimliğinin **tanımsız** olduğu yer. Kararı taşıyan piksel sayısı:

| sahne | rota piksel dağılımı (ş1/ş2/ş3) | yer gerçeği | yayınlanan | kararı veren |
|---|---|---|---|---|
| 1/kolay | 419 / 3 / 0 | 1 | **2** | 422'nin **3'ü** |
| 5/zor | 7 / 416 / 0 | 2 | **1** | 423'ün **7'si** |
| 3/zor | 427 / 189 / 7 | 1 | **3** | 623'ün **7'si** |

Rotanın **geometrisi** her sahnede doğru koridordaydı (D-295); yanlış olan yayınlanan sayıydı.

---

## 2. Düzeltme — TEK TANIM (anayasa madde 16)

`codes/karar_sozlesmesi.py`:

```python
def rota_serit_karari(rota_pikselleri, icerik_x0, icerik_w):
    """YAYINLANAN `road` — TEK TANIM. Şerit rotanın GÖVDESİNDEN okunur."""
```

Her rota pikseli `serit_no()` ile bir şeride sayılır; en çok piksel taşıyan şerit kazanır,
beraberlikte **deterministik** olarak küçük indis. Yayınlanan alan `olcum["serit_karari"]`.

**İki çağıran:**
- `rpi_inference._rota_serit_olcumu` → `open_path = olcum["serit_karari"]` (**yayın**)
- `costmap_path_finder.rota_bul` → `rota_serit`, `serit_uyumu` (**çapraz denetim**;
  o yolun otoritesi kapıdır, `yol_no` **değiştirilmedi**)

`darbogaz_serit` **silinmedi**: ölçüm sözlüğünde **tanı** alanı olarak duruyor, hakem
ekranında "(tanı)" etiketiyle görünüyor. Darboğaz **açıklığı** güvenin girdisi olmaya devam
ediyor (değişmedi).

---

## 3. Koşulan komutlar ve HAM çıktı

### 3.1 Önce/sonra ölçüm (aynı betik, iki kök)

```
> O:\navitas-local-train\venv\Scripts\python.exe results/t155/serit_kapisi.py \
      --kok O:/navitas --json results/t155/once_master.json
```
```
KOK: O:/navitas
har  senaryo gercek  yayin rota_bul   wp    ret  tani_darbogaz         seritler
  1    kolay      1      2        1    8      -              2      [419, 3, 0]
  1     orta      2      2        2    8      -              2      [0, 422, 0]
  1      zor      3      2        3   12      -              2   [12, 202, 427]
  2    kolay      1      2        1    8      -              2      [424, 7, 0]
  2     orta      1      2        1   10      -              2    [465, 166, 0]
  2      zor      3      3        3   10      -              3    [0, 210, 399]
  3    kolay      3      3        3    8      -              3      [0, 0, 440]
  3     orta      2      2        2   10      -              2      [0, 430, 0]
  3      zor      1      3        1   10      -              3    [427, 189, 7]
  4    kolay      3      2        3    8      -              2      [0, 4, 421]
  4     orta      3      3        3   13      -              3     [0, 28, 437]
  4      zor      1      2        1   12      -              2     [458, 23, 0]
  5    kolay      3      2        3    8      -              2    [0, 124, 381]
  5     orta      3      3        3    9      -              3      [0, 6, 463]
  5      zor      2      1        2    8      -              1      [7, 416, 0]
----------------------------------------------------------------------------------------
{"n": 15, "yayinlanan_dogru": 6, "rota_bul_dogru": 15}
```

```
> ... results/t155/serit_kapisi.py --kok <worktree> --json results/t155/sonra_t155.json
```
```
har  senaryo gercek  yayin rota_bul   wp    ret  tani_darbogaz         seritler
  1    kolay      1      1        1    8      -              2      [419, 3, 0]
  1     orta      2      2        2    8      -              2      [0, 422, 0]
  1      zor      3      3        3   12      -              2   [12, 202, 427]
  2    kolay      1      1        1    8      -              2      [424, 7, 0]
  2     orta      1      1        1   10      -              2    [465, 166, 0]
  2      zor      3      3        3   10      -              3    [0, 210, 399]
  3    kolay      3      3        3    8      -              3      [0, 0, 440]
  3     orta      2      2        2   10      -              2      [0, 430, 0]
  3      zor      1      1        1   10      -              3    [427, 189, 7]
  4    kolay      3      3        3    8      -              2      [0, 4, 421]
  4     orta      3      3        3   13      -              3     [0, 28, 437]
  4      zor      1      1        1   12      -              2     [458, 23, 0]
  5    kolay      3      3        3    8      -              2    [0, 124, 381]
  5     orta      3      3        3    9      -              3      [0, 6, 463]
  5      zor      2      2        2    8      -              1      [7, 416, 0]
----------------------------------------------------------------------------------------
{"n": 15, "yayinlanan_dogru": 15, "rota_bul_dogru": 15}
```

`wp`, `ret`, `tani_darbogaz` ve `seritler` sütunları **iki tabloda da aynıdır** — değişen
tek sütun `yayin`.

### 3.2 BOZULMAMA — bayt-eş kıyas (ön kayıt §17 ek şartı)

```
> O:\navitas-local-train\venv\Scripts\python.exe results/t155/bozulmama_kiyas.py \
      --once results/t155/once_master.json --sonra results/t155/sonra_t155.json
```
```
sahne              : 15
kiyaslanan waypoint: 142
degismez alanlar   : waypointler, ret, guven, tani_darbogaz_serit, tani_seritler, tani_darbogaz_xy, tani_darbogaz_px

BOZULAN ALAN       : 0

yayinlanan_road DEGISEN sahne: 9
       sahne gercek  once sonra  sonuc
     1/kolay      1     2     1  DUZELDI
       1/zor      3     2     3  DUZELDI
     2/kolay      1     2     1  DUZELDI
      2/orta      1     2     1  DUZELDI
       3/zor      1     3     1  DUZELDI
     4/kolay      3     2     3  DUZELDI
       4/zor      1     2     1  DUZELDI
     5/kolay      3     2     3  DUZELDI
       5/zor      2     1     2  DUZELDI

yayinlanan road dogrulugu: ONCE 6/15  SONRA 15/15
KAPI (>= 14/15)          : GECTI
BOZULMAMA                : GECTI (bayt-es)
```

**9 sahnenin 9'u da düzeldi, hiçbiri bozulmadı.**

### 3.3 Genel kapı

```
> O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI
```

### 3.4 Test paketi

```
> O:\navitas-local-train\venv\Scripts\python.exe -m unittest discover -s tests -q
Ran 989 tests in 71.814s
FAILED (failures=4, errors=11, skipped=16)
```

⚠ **Bu 15 hata T155'ten DEĞİLDİR.** Aynı paket, değişikliklerim **geri alınmış**
worktree'de koşuldu ve **birebir aynı 15 hata** çıktı (`diff` boş). Hepsi worktree'de
**model/veri bulunmamasından** gelir (`v36_competition_model`, `manifest`, `sha`,
`kompozit dizini`); `models/` ve `data/arena_kompozit/images` yalnız `O:\navitas`'ta var.
Test sayısı 976 → **989** (T155'in 13 yeni testi).

---

## 4. MUTASYON KANITI

Kök satır bozuldu: `open_path = olcum["serit_karari"]` → `olcum["darbogaz_serit"]`

```
MUTASYON ONCESI sha256: 7f0afaaac605946494959c226dfb0bd474c5f409219874ae637fbd065fa3631d
KOK SATIR BOZULDU
> python -m unittest test_t155_serit_numarasi test_t119_yayinlanan_road_kapisi -q
Ran 17 tests in 3.398s
FAILED (failures=25)
```

Düşen assert'ler: `test_onceden_yanlis_dokuz_sahne_artik_dogru` (9 subtest),
`test_yayin_alani_serit_kararina_bagli` (9), `test_on_kayit_kapisi_15_sahnede_en_az_14`,
ve **T119'dan** `test_zikzak_yayinlanan_road_govde_serididir` (2),
`test_zikzak_ayrisan_sahnede_yayin_darbogaza_esitlenmez` (2),
`test_yayin_serit_karari_sozlesmesine_bagli` (2).

Bayt-eş geri alma:
```
GERI ALINDI sha256: 7f0afaaac605946494959c226dfb0bd474c5f409219874ae637fbd065fa3631d
BAYT-ES: True
> python -m unittest test_t155_serit_numarasi test_t119_yayinlanan_road_kapisi -q
Ran 17 tests in 3.276s
OK
```

⚠ Çıkış kodu kanıt sayılmadı — düşen test adları yukarıda.

---

## 5. Sentetik kabul K0–K6 neden koşulmadı, ETKİLENMEDİĞİ nasıl kanıtlandı

GPU yasak (görev şartı). Bunun yerine **okuma yolu** izlendi:

| soru | cevap |
|---|---|
| Hangi fonksiyonlar değişti? | `karar_sozlesmesi.rota_serit_karari` (**yeni**), `rpi_inference._rota_serit_olcumu` (alan eklendi, `seritler` **bayt-eş** aynı), `rpi_inference` yayın satırı, `rota_bul` sonu (**yalnız yeni tanı alanları**), `yks_gui` kanıt metni |
| `61_rota_moloza_basma` hangi alanı okuyor? | `basma_orani`, `arena_disi_orani`, `yol_payi`, `engel_wp`, `yanlis_guzergah` — **hepsi waypoint'lerden türer**. `kayit["serit"]` kaydedilir ama **hiçbir kapıya girmez** (K1–K6 hesabında kullanılmıyor) |
| K1–K6 bunlara bağlı mı? | **Hayır.** Waypoint'ler bayt-eş aynı (142/142, 0 fark) → K1–K6 girdileri değişmedi |
| T152 `rota_yol_olcumu`? | `rota_yol_olc(wps, uc)` — **yalnız waypoint** alır. Waypoint'ler değişmediği için **etkilenmez** |

Rota üretimine dokunulmadı: kod yolunda maske, morfoloji, A*, string-pulling, `rota_dogrula`
hiç değişmedi — değişen tek şey ölçüm sözlüğünden **hangi alanın yayınlandığı**.

---

## 6. 🔴 AÇIK SORU — MİMARIN KARARINI BEKLİYOR

`tests/test_t119_yayinlanan_road_kapisi.py` **eski sözleşmeyi assert ediyordu** ve bu
değişiklikle düştü. İncelendiğinde çelişkinin **gerçek** olduğu görüldü.

T119'un `_zikzak` sahnesinde alt/üst dikeyler şerit 3'te, **tek geçiş** şerit 1'deki dar
kapıdadır. İki tanım aynı ismi (`road`) taşıyan **iki farklı soruyu** yanıtlıyor:

| soru | cevap | doğru olan tanım |
|---|---|---|
| "hangi güzergâh **açık**" | 3 (gövde) | `serit_karari` |
| "**darboğaz** hangi şeritte" | 1 (kapı) | `darbogaz_serit` |

**Ajanın hükmü (ratifikasyona açık):** şartname §2.2.3'ün sorduğu soru **birincisidir**.
Arena üç koridoru **paraleldir** — açık rota gövdesiyle tek şeritte kalır; `_zikzak` gibi üç
şeride **dengeli** yayılan bir rota arena geometrisinde **oluşmaz**. Kanıt kalitesi de
asimetrik: arena kümesinin yer gerçeği **üreteçten gelir ve algoritmadan gizlidir**;
T119'un yer gerçeği ise sahne yazarının **beyanıdır** ve kendi kabulüyle yalnız dar
kapılarda (16/24 px) tutar — 48/64 px'te `darbogaz_serit` zaten 3 veriyor.

⚠ **HAKEMLİK DENENDİ, OLMADI.** Görev *"rota_bul'un doğru şerit kararını üretim yoluna
taşı"* diyordu. Ölçüldü: `rota_bul` bu sahne ailesinin **hiçbirinde karar vermiyor**:

```
T119 ZIKZAK — kapi_px 16/24/48/64 -> yol_no=None, durum=BELIRSIZ_TEK_KAPI (dördünde de)
T31 ENJEKTE-KAPI — kapi_serit 1/2/3 -> yol_no=None, durum=BELIRSIZ_COKLU (üçünde de)
```

Yani rota_bul bu çelişkide **hakemlik yapamaz**, ve mekanizmasını (koridor kapıları)
`analyze_path`e taşımak T119/T31 sahnelerini topluca `NO_ROUTE`'a çevirirdi — gerçek karede
ret oranını GPU'suz ölçemeyeceğim bir fail-closed regresyon. Bu yüzden taşınan şey
mekanizma değil **ilke** oldu: *şerit, rotanın ayırt edici olduğu yerden okunur, bir uç
değerden değil.*

**Yapılan:** T119 yeni sözleşmeye **nişanlandı**; mutasyon muhafızı **korundu** (§4'te
görüldüğü gibi yayın hattı eski alana çevrilince T119'dan 6 assert düşüyor). Çelişki hem
o dosyanın başlığında hem `CONTRACTS.md` §6.2'de **kayıtlı** bırakıldı. Bu bir kapı
**gevşetmesi değil**, kapının yeni sözleşmeye nişanlanmasıdır — **ama hükmü mimar
onaylamalıdır.** Onaylanmazsa geri alma tek satırdır (`open_path` + T119).

**Önerilen takip (ayrı ön kayıt ister, bu turda GİRMEDİ):** rota gerçekten üç şeride
dengeli yayıldığında tek etiket yayınlamak yerine **fail-closed** durmak — `rota_bul`un bu
sahnelerde zaten yaptığı şey ve projenin ilan ettiği politikayla (*"çekimserlik puan
kaybettirir, yanlış karar sıfırlar"*) tutarlı. Gerçek karede ret oranını değiştireceği için
**GPU'lu ölçüm olmadan bağlanmaz**.

---

## 7. ÖLÇÜLEMEDİ (dürüstlük kaydı)

- **T96'nın n=209 kadraj kümesi** yeniden ölçülemedi — maskeleri **model koşumu** ister,
  oturumda **GPU yasaktı**. D-167/D-168'in `darbogaz 198 · cikis 197 · baskin 196`
  sıralamasının yeni tanımla ne olacağı **ÖLÇÜLMEDİ**. Kapanan şey o sıralama değil,
  **yer gerçeği sağlam** arena geometrisinde hangi tanımın doğru olduğudur.
- **Gerçek kare etkisi ÖLÇÜLEMEDİ** (GPU yasak). §5'te etkilenmediği **okuma yoluyla**
  kanıtlandı, ama bu bir ölçüm değildir.
- Sahneler **sentetik**, maske **kusursuz**: bu bir **algı** ölçümü değil **mantık**
  ölçümüdür; gerçek karelerde oran **bu değildir**.

---

## 8. Değişen dosyalar

| dosya | değişiklik |
|---|---|
| `codes/karar_sozlesmesi.py` | `rota_serit_karari()` — **tek tanım** |
| `codes/rpi_inference.py` | `serit_karari` alanı + yayın satırı; `darbogaz_serit` tanı olarak korundu |
| `codes/costmap_path_finder.py` | `rota_bul` çapraz denetimi (`rota_serit`, `serit_uyumu`) |
| `comms/yks_gui.py` | kanıt satırı: yayınlanan şerit + "(tanı)" darboğaz; bayat metin düzeltildi |
| `jetson_paket/kod/{rpi_inference,costmap_path_finder,karar_sozlesmesi}.py` | ayna (**diff boş**) |
| `tests/test_t155_serit_numarasi.py` | **yeni** — 13 test (değer kapısı, mutasyon muhafızı, bozulmama, ortak fonksiyon) |
| `tests/test_t119_yayinlanan_road_kapisi.py` | yeni sözleşmeye nişanlandı, çelişki kayıtlı |
| `tests/test_rota_ret_nedenleri.py`, `tests/test_yks_gui_rota_engel.py` | sahte ölçüm sözlüğüne `serit_karari` eklendi (dosyaların kendi kuralı) |
| `CONTRACTS.md` §6.2 | yayınlanan istatistik + ölçülen sayılar; D-167/D-168 notu **kaldı** |
| `REVIEW_LOG.md` | D-296 |
| `results/t155/` | betikler, ham JSON'lar, bu rapor |
