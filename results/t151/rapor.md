# T151 · TEK KARAR YOLU — kanıt raporu (KARAR YOK; karar mimar vekilinindir)

Tarih: 2026-08-26 · Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`
Kapsam: **ana dizin, salt okuma**. Üretim kodu değiştirilmedi; yalnız `results/t151/` yazıldı.
GPU **kullanılmadı** (model çıkarımı koşulmadı — `karar_cevrilmesi` dışındaki ajanlar GPU kullanmaz).

Görev: `TASK_QUEUE.md` T151 · kanıt: `results/sartname_bosluk/rapor.md` R1 / K7.

---

## 0. Tek cümlelik durum

Sahada **yayına giden karar yalnız `analyze_path`ten** çıkar (`rpi_inference --camera` → K1 telsiz halkası);
`rota_bul` saha gününde yalnız **tanısal** araçlarda (`kamera_dogrula`, `jetson_fps`) ve PC'deki
**kuru koşuda** koşar. CONTRACTS §11.2 halka 7'nin sahibi olarak gösterdiği `rota_bul`, sahada
**hiçbir mesaj yayınlamaz**. Buna karşılık projenin **genel kapısı** (`test_rota_sentetik.py` 15/15,
yer gerçekli 3-koridorlu arena) yalnız `rota_bul`u sınar — yani **üretim yolu şartnamenin
§2.1 topolojisinde hiç kapıya sokulmamıştır**. Bu boşluğu bu görevde ölçtüm: aynı maskede
`rota_bul` 15/15 doğru `road` yayınlıyor, `analyze_path` **6/15** (rotanın geometrisi 15/15 doğru
koridorda, **yanlış olan yayınlanan numara**).

---

## 1. ÇAĞRI HARİTASI — hangi dosya hangi yolu çağırıyor, sahada hangisi koşuyor

### 1.1 `analyze_path` çağrı yerleri (üretim + yakın çevre)

| # | `dosya:satır` | Rol | Saha gününde koşar mı |
|---|---|---|---|
| 1 | `codes/rpi_inference.py:2141` (`run_camera`) | **ÜRETİM ALGI DÖNGÜSÜ** → `_karari_yayinla` → `comms/iha_sender.KararYayinci` (K1, CONTRACTS §6.5) | ✅ **EVET — yayına giden tek karar** |
| 2 | `codes/rpi_inference.py:2047` (`run_video`) | aynı zincirin video kipi; aynı yayıncıya bağlı | koşulursa evet |
| 3 | `codes/rpi_inference.py:1944` (`run_image`) | tek kare kipi | hayır (ölçüm) |
| 4 | `comms/yks_gui.py:1569` | YKS **yerel algı** paneli; ekranda "YEREL ALGI — telsiz DEĞİL" etiketli (D-121/D-122) | YKS'de evet, **yayın değil** |
| 5 | `simulation/scripts/iha_perceive.py:139` | Gazebo algı; §11.1/1 gereği **sahip değil** | hayır |
| 6 | `codes/test_accuracy.py:182` | doğruluk ölçümü (T8'de üretim fonksiyonuna bağlandı) | hayır |
| 7 | `scripts/olcum/61_rota_moloza_basma.py:99` | **model kabul kapısı K1–K4/K6**'nın rota üreticisi (`65_kabul_denetcisi.py:490` alt betiği) | hayır — ama **v36 terfisi buradan geçti** |
| 8 | `scripts/olcum/126_t138_gece_kumesi.py:104,108` | T152 "rota yol üstünde" kapısının ölçtüğü yol | hayır (ölçüm) |
| 9 | `scripts/olcum/` içinde 20+ betik daha (45,46,48,54,56,57,60,62,63,66,67,68,70,72,73,75,76,79,80,81,82,83,84,85,88,92, `s2_yonelim_olcum`) | ölçüm | hayır |

### 1.2 `rota_bul` / `koridor_adaylari` çağrı yerleri

| # | `dosya:satır` | Rol | Saha gününde koşar mı |
|---|---|---|---|
| 1 | `jetson_paket/kod/kamera_dogrula.py:36` (`zincir_durumu`) | **saha kamera doğrulama aracı** (`JETSON_KILAVUZ.md:586/599/621`) — yalnız `durum` basar | ✅ evet, **tanısal**; mesaj yayınlamaz |
| 2 | `scripts/jetson_fps.py:226` = `jetson_paket/kod/jetson_fps.py:226` | FPS ölçüm zinciri (`JETSON_KILAVUZ.md:409/439/462`), `plan=False` | ✅ evet, **tanısal** |
| 3 | `scripts/saha_kuru_kosu.py:709` (+ `:722` tanısal kırpık) | **CONTRACTS §11.4 kuru koşusu**, halka `rota` — çıktıda `dosya: codes/costmap_path_finder.py:729` | PC'de uçuş öncesi; sahada değil |
| 4 | `simulation/scripts/iha_haritala.py:324` | Gazebo mozaik → `rota.json` → `road` yayını; §11.1/1 gereği **sahip değil** | hayır |
| 5 | `codes/test_rota_sentetik.py:134,196` | **GENEL KAPI (15/15)** — CLAUDE.md madde 14 | hayır (kapı) |
| 6 | `codes/test_rota_guvenlik.py` | rota güvenlik kapısı | hayır (kapı) |
| 7 | `scripts/copy_paste_augmentation.py:882` | veri üretiminde rota kapısı (`plan=False`) | hayır |
| 8 | `scripts/v21_degerlendir_ve_paketle.py:71` | model değerlendirme; docstring'i **"üretim yolunun aynısı"** diyor — **YANLIŞ**, üretim `analyze_path` koşar | hayır |
| 9 | `codes/costmap_path_finder.py:1080` | `koridor_adaylari` — **yalnız `rota_bul` içinden** çağrılır | — |
| 10 | `codes/costmap_path_finder.py:1360` (`analyze_path_uyumlu`) | **hazır köprü: `rota_bul`u `analyze_path` dönüş şekline çevirir** | **çağıran YOK (0 çağrı yeri)** |

### 1.3 Saha günü zinciri — kanıt

`JETSON_KILAVUZ.md:638` ve `:647` (K1 · §6.5 saha görev komutu):

```bash
python3 ~/navitas/codes/rpi_inference.py --camera --kaynak "http://<IP>:4747/video" \
  --mavlink udpin:0.0.0.0:14550 --mav-sysid 1 --fov 78 \
  --yks-hedef <YKS_IP>:5005 --ika-hedef <IKA_IP>:5006
```

→ `run_camera` → `analyze_path` (`rpi_inference.py:2141`) → `_rota_kararini_esikle` (`:1720`)
→ `_karari_yayinla` (`:267`) → `KararYayinci.karar` (`comms/iha_sender.py:243`)
→ `send_open_route` / `send_no_route`. **`rota_bul` bu zincirde hiç yok.**

Yan bulgu (saha runbook boşluğu, T151'in konusu değil ama aynı zincirde):
`JETSON_KILAVUZ.md:300` `cp` listesinde **`kamera_dogrula.py` YOK**, ama `:586` onu
`~/navitas/codes/kamera_dogrula.py` diye çağırıyor. Saha kurulumunda dosya orada olmaz.

### 1.4 Ayna kontrolü

`diff -q` **boş** (fark yok): `codes/rpi_inference.py`, `codes/costmap_path_finder.py`,
`codes/karar_sozlesmesi.py` ↔ `jetson_paket/kod/` kopyaları; `scripts/jetson_fps.py` ↔
`jetson_paket/kod/jetson_fps.py`. `kamera_dogrula.py`'nin **kök kopyası yok** (yalnız pakette).

---

## 2. SÖZLEŞME FARKI — hangi kapı hangi yolda VAR / YOK

### 2.1 Çıktı sözleşmesi

| | `analyze_path` (`rpi_inference.py:1322`) | `rota_bul` (`costmap_path_finder.py:983`) |
|---|---|---|
| dönüş | demet: `(open_path, confidence, waypoints[, clean][, (sebep,detay)][, olcum])` | sözlük: `durum, yol_no, guven, waypoints_px, darbogaz_m, adaylar, en_iyi_aday, ihlaller, sure_ms, sebep[, uyari]` |
| `road` nereden | `olcum["darbogaz_serit"]` = rotanın **EN DAR** noktasının şeridi (`:1245`) | `kazanan["etiket"]` = **kapı ağırlık merkezinin** `serit_no`su (`:1160`) |
| KB/HB tohumu | **argüman YOK** — alt/üst bantları içerik kutusundan kendi kurar | `baslangic` / `hedef` **argüman** (`_tohum_maske`) |
| koridor envanteri | **YOK** (tek küresel A*, en büyük bağlı bileşen) | **VAR** — `koridor_adaylari` (`:368`), kapı başına ayrı geçilebilirlik |
| çekimserlik dili | §6.4 kanonik `(sebep, detay)` | `durum` metni (**§6.4 kümesinde değil**) |

### 2.2 Kapı matrisi (**en kritik kısım**)

| kapı | `analyze_path` | `rota_bul` | not |
|---|---|---|---|
| `ZEMIN_MASKESI_SUPHELI` zemin sağlamlık (T48/T134) | ✅ `:1524` | ✅ `:1067` | T134/D-267 ile **taşındı**; 400 vakada uyuşmazlık 0/400 |
| **K-A uç-bant teması** (§6.3, `UC_BANT_TEMAS_YOK`) | ✅ `:1581` | ⚠ **dolaylı** — `_bagli_mi` tohum bantlarıyla; kanonik sebep üretmez | aynı `0.08` bandı |
| C-uzayı (§5.3, `dist ≥ r_gerekli_px`) | ✅ `:1615-` | ✅ `:313` | analyze_path'e T43'te **taşındı** |
| A* tanık yol + plan bütçesi (`ROTA_PLAN_MAKS_HUCRE`) | ✅ `:1630-1680` | ✅ ROI + `plan_izgarasi` (`:1195-`) | ikisi de bütçeli |
| `KENAR_GUVENSIZ` (T24, ardışık wp görüş hattı) | ✅ `:1665` | ❌ | rota_bul yerine `rota_dogrula` kullanır |
| `rota_dogrula` K2/K3 ihlal denetimi + ankor ekleme | ❌ | ✅ `:1305-1330` (`DOGRULAMA_BASARISIZ`) | `ihlaller` alanı yalnız rota_bul'da |
| **`koridor_adaylari` — "3 güzergâhtan biri açık" kapısı (şartname §2.1)** | ❌ **YOK** | ✅ `n_kapi==1 → BELIRSIZ_TEK_KAPI`, `n_kapi!=3 → BELIRSIZ_COKLU` | R1'in çekirdek boşluğu |
| etiket çakışması fail-closed (T90/D-146) | ❌ | ✅ `:1150-1158` | iki geçilebilir kapı aynı şeridi gösterirse karar YOK |
| `KORIDOR_DEGIL` koridor genişlik tavanı (T65) | ✅ `:1703` | ❌ | açık arazi reddi yalnız analyze_path'te |
| **K-B güven eşiği** (`rota_guven_reddi`, §6.3) | ✅ `:1730` | ❌ | rota_bul'da yok; yalnız yayıncı/GUI'de |
| `OLCEK_YOK` (halka 5) | çağrı yerinde (`:1943/:2046/:2140`) | çağrı yerinde (`saha_kuru_kosu.py:690`); `iha_haritala` sabit `MPP` | ikisi de fonksiyon dışında |
| `HEDEF_YOK` / HB tohumu (T72) | ✅ `:1643` — **ama `goruntu=` geçen üretim çağrısı YOK** | ❌ (dış `hedef` argümanı var, üretimde besleyen yok) | R13 |
| beraberlik bandı ile deterministik seçim (D-112) | ✅ `:1241` | ❌ | |
| rota ekseni döndürme (S2 yönelim) | ✅ `:1396` | ❌ | |
| letterbox `icerik` kutusu | ✅ | ✅ (T135'ten beri; `icerik=None`'da **uyarı** basar `:1015`) | |
| **T152 "rota yol üstünde" kapısı** | ✅ ölçülüyor (`126`/`142`) | ❌ ölçülmedi | |
| **genel kapı `test_rota_sentetik` 15/15** | ❌ **hiç sınanmıyor** | ✅ | madde 14'ün kapısı yalnız rota_bul'u zorluyor |

**Özet:** iki yol **birbirinin alt kümesi değil**. Her birinde diğerinde **olmayan** en az üç
gerçek kapı var. "Tek yol ilan et" kararı, hangisi seçilirse seçilsin **kapı taşıma borcu** doğurur.

### 2.3 Ret sözlüğü uyuşmazlığı (yayın katmanını ilgilendirir)

`karar_sozlesmesi.ROTA_RET_SEBEPLERI` (`:106-118`) 11 koddan oluşur ve
`tests/test_rota_ret_nedenleri.py:71` bu kümeyi **kilitler**. `rota_bul`un ürettiği
`BELIRSIZ_TEK_KAPI · BELIRSIZ_COKLU · KAPALI_DAR · KAPALI_KOPUK · DOGRULAMA_BASARISIZ · KAPI_YOK`
kodlarının **hiçbiri bu kümede değil**. `KararYayinci._karari_gonder` (`iha_sender.py:273`)
`karar_reddi[0]`'ı doğrudan `NO_ROUTE.sebep` yapar. Yani üretimi `rota_bul`a çevirmek
**§6.4 sözlüğünü genişletmeyi veya bir eşleme katmanı yazmayı zorunlu kılar**;
aksi hâlde hakem ekranına sözleşme dışı sebep kodu gider.

---

## 3. ÖLÇÜM

### 3.1 YENİ ÖLÇÜM — aynı maske, iki yol, **yer gerçekli** 3 koridor (GPU yok, model koşulmadı)

Betik: `results/t151/iki_yol_kiyasi.py` · çıktı: `results/t151/iki_yol_kiyasi.json`
Küme: `simulation/scripts/arena.py` — 5 harita × 3 senaryo = **15 belirlenimci sahne**,
`codes/test_rota_sentetik.sahne_uret` ile **birebir aynı** rasterleştirme, `mpp=0,10`, tuval 500×500.
Aynı `{0: zemin, 1: engel}` sözlüğü **hem** `rota_bul(plan=True, baslangic, hedef)`'e **hem**
`analyze_path(icerik=None, engel_mask, mpp)`'e verildi. Yer gerçeği: `arena.harita()["open"]`.

```
har  senaryo gercek |  rota_bul              durum | analyze                    ret
  1    kolay      1 |         1               ACIK |       2                      -
  1     orta      2 |         2               ACIK |       2                      -
  1      zor      3 |         3               ACIK |       2                      -
  2    kolay      1 |         1               ACIK |       2                      -
  2     orta      1 |         1               ACIK |       2                      -
  2      zor      3 |         3               ACIK |       3                      -
  3    kolay      3 |         3               ACIK |       3                      -
  3     orta      2 |         2               ACIK |       2                      -
  3      zor      1 |         1               ACIK |       3                      -
  4    kolay      3 |         3               ACIK |       2                      -
  4     orta      3 |         3               ACIK |       3                      -
  4      zor      1 |         1               ACIK |       2                      -
  5    kolay      3 |         3               ACIK |       2                      -
  5     orta      3 |         3               ACIK |       3                      -
  5      zor      2 |         2               ACIK |       1                      -
------------------------------------------------------------------------------------------
 "n_sahne": 15,
 "analyze_path_rotasi_ACIK_guzergahta": 15,
 "rota_bul_rotasi_ACIK_guzergahta": 15,
 "rota_bul_karar_verdi": 15,      "rota_bul_dogru": 15,      "rota_bul_yanlis_guzergah": 0,
 "analyze_path_karar_verdi": 15,  "analyze_path_dogru": 6,   "analyze_path_yanlis_guzergah": 9,
 "ikisi_de_karar_verdi": 15,      "ikisi_karar_verdiginde_uyusan": 6,
 "rota_bul_durum_dagilimi": {"ACIK": 15},
 "analyze_path_ret_dagilimi": {"-": 15},
 "zemin_kaplama_min": 0.2986, "zemin_kaplama_max": 0.4262   (tavan 0,55 — kapı ateşlemedi)
```

🔴 **BULGUNUN ŞEKLİ — abartılmamalı, küçültülmemeli.** İki yolun **rota GEOMETRİSİ 15/15
aynı ve doğru koridorun üstünde** (yer gerçeği güzergâh ekseninin ±2 m bandında waypoint payı;
açık güzergâh için pay 1,0 · diğer ikisi ≤ 0,32). Yani **"analyze_path İKA'yı kapalı koridora
sürüyor" diye bir bulgu YOKTUR.** Ayrışan şey **yayınlanan `road` numarasıdır** — ve
`road` CONTRACTS §6.2/D-166 gereği **puanlanan cevaptır** (şartname §5.3.2 yanlış güzergâh = 0 puan).

**Mekanizma ölçüldü.** `analyze_path` `road`u rotanın **en dar noktasının** şeridinden okur
(`darbogaz_serit`). Arena topolojisinde üç güzergâh KB/HB yakınında birleştiği için rota,
komşu şeride birkaç piksel taşar ve darboğaz **o taşmaya** düşer:

| harita/senaryo | yer gerçeği | yayınlanan | şerit piksel dağılımı | yayınlanan şeridin rota payı |
|---|---:|---:|---|---:|
| 1 kolay | 1 | **2** | [419, 3, 0] | **%0,71** |
| 4 kolay | 3 | **2** | [0, 4, 421] | %0,94 |
| 3 zor | 1 | **3** | [427, 189, 7] | %1,12 |
| 2 kolay | 1 | **2** | [424, 7, 0] | %1,62 |
| 5 zor | 2 | **1** | [7, 416, 0] | %1,65 |
| 4 zor | 1 | **2** | [458, 23, 0] | %4,78 |
| 5 kolay | 3 | **2** | [0, 124, 381] | %24,6 |
| 2 orta | 1 | **2** | [465, 166, 0] | %26,3 |
| 1 zor | 3 | **2** | [12, 202, 427] | %31,5 |

**9 yanlış etiketin 5'inde yayınlanan şerit rotanın %2'sinden azını taşıyor.**

🔴 **Ve aynı çıktıda zaten hesaplanan `baskin_serit` bu kümede 15/15 doğru** — ama
`rpi_inference.py:1245-1250` onu **yayınlamıyor** (CONTRACTS §6.2 bunu açıkça yazar).

**Bu, CONTRACTS §6.2 ile çelişmez — kümesi farklıdır.** §6.2'nin `darbogaz 198/209 · baskin 196/209`
sayısı `sentetik_arena_kadraj_t66` (kadraj alınmış kareler) kümesindendir ve orada iki istatistik
258 karenin yalnız 5'inde (%1,9) ayrışır (D-145 §3). Sebebi ölçülü: o kümede kareler kırpıktır,
260 karenin **226'sında üç kapı görünmez** (D-145). Burada ölçülen küme ise **tam HTAB görüşüdür**
— şartname §2.1'in üç-güzergâhlı topolojisi. §6.2 zaten "sıralama bu kümede **karara bağlanamaz**"
diyor; bu ölçüm o cümlenin gerekçesini güçlendirir, hükmünü değiştirmez. **Ben de karar vermiyorum.**

⚠ **SINIRLAR (rapor edilir, gizlenmez):**
1. Maske **KUSURSUZDUR** — bu bir ALGI değil MANTIK ölçümüdür. Gerçek karelerde ayrışma oranı bu değildir.
2. `rota_bul` KB/HB tohumunu **argüman olarak** aldı, `analyze_path` alamaz (argümanı yok). Bu eşitsizlik
   ölçümün kusuru değil, **ölçülen sözleşme farkının kendisidir** — ama "rota_bul daha iyi" diye
   okunamaz: rota_bul sahada o tohumları **nereden alacağını bilmiyor** (halka 6 SAHİPSİZ).
3. n = 15. Küçük küme; oranlar değil **mekanizma** kanıttır.
4. Waypoint→güzergâh eşlemesinde ±2 m bant toleransı kullanıldı (T152'nin `yol_payi` fikri);
   arena yol genişliğinden türetilmedi, ölçümün kendi toleransıdır.

### 3.2 Repoda ZATEN kayıtlı kanıt (aynı kare üzerinde iki yol)

| kayıt | küme | ne diyor |
|---|---|---|
| **D-145** (`REVIEW_LOG.md:10470`) | `sentetik_arena_kadraj_t66`, n=260, σ=2/255, tohum 7 | Tek koşuda **aynı maske** hem `analyze_path` hem `rota_bul`a verildi. Üretim çevrilen **8/260**, envanter `yol_no` çevrilen **10/260** (envanter **daha kararsız**), `durum==ACIK` yalnız **34/260** — 226 karede `n_kapi != 3` → BELİRSİZ. Ön kayıt kuralı (B) ve (D) **birden** ateşledi → "seçimi envantere bağla" önerisi **ölçümle reddedildi**. |
| **D-145 §2** | 470 aday kapı | İki etiketleme otoritesi: `etiket != serit_no` **104/470 (%22,1)**. Canlı kusur **1/34**. → T90/D-146 ile kapatıldı (etiket artık `serit_no`dan). |
| **D-147** (`:10793`) | aynı küme | Envanterin **en kararsız** parçası bant seçimi: **41/260 (%15,8)**, `yol_no` kararsızlığının ~4 katı. `T90 öncesi = sonrası` → baştan beri orada. |
| **D-122** (`:8454`) | n=260 | `analyze_path` kararının gürültü altında çevrilmesi **9/260 (%3,46)** — bu **TABAN**, tavan değil. T79'un dayanağı. |
| **`results/saha_kuru_kosu_20260826_001414/ozet.json`** | 1 gerçek kare (`data/raw_frames/…11_44_03/frame_000000`) | halka `rota` **DÜŞTÜ** · `durum=BELIRSIZ_TEK_KAPI` · `yol_no=null` · `rota_yayinlanabilir=false` · `mpp=0,0338`. Yani **kuru koşu `rota_bul`u ölçüyor ve düşürüyor**, oysa saha komutu `analyze_path` koşuyor. Halka satırındaki `dosya` alanı hâlâ `codes/costmap_path_finder.py:729` (rota_bul bugün `:983`). |
| **CONTRACTS §11.2 halka 7** | — | Sahip: `costmap_path_finder.py:729 (rota_bul)`, durum KUSURLU/D-25. **Satır numarası bayat, sahip beyanı sahayla çelişiyor.** |

### 3.3 ÖLÇÜLEMEDİ (tahmin edilmedi)

1. **Gerçek karelerde iki yolun aynı kare üzerindeki kıyası.** Repoda böyle bir kayıt **yok**;
   ne `results/` altında ne D-kayıtlarında gerçek-kare `analyze_path ↔ rota_bul` tablosu var.
   D-145 sentetik kadraj kümesindedir ve D-145 "DOĞRULANAMADI #4" bunu zaten yazar:
   *"Gerçek arena karelerinde envanterin ne yapacağı ÖLÇÜLMEDİ."*
2. **`rota_bul`un v36 üretim modeliyle gerçek karelerde çekimserlik oranı.** Elimizde tek nokta var:
   kuru koşunun 1 karesi (`BELIRSIZ_TEK_KAPI`). n=1 oran değildir.
3. **Yayınlanan `road`un hakem puanına gerçek etkisi** — D-145 "DOĞRULANAMADI #5"ten beri açık.
4. **A\* maliyet beraberliği** (T79'un kalan tek mekanizması) — `astar()` toplam maliyeti döndürmüyor.
5. **SiK telsiz üzerinde** yayın — CONTRACTS §11.2 halka 8'de zaten "ÖLÇÜLMEDİ".

### 3.4 Bu ölçümler NASIL yapılır (GPU'lu gece için reçete)

**Ö1 · Gerçek-kare iki-yol kıyası (asıl eksik ölçüm).**
- Betik: `scripts/olcum/126_t138_gece_kumesi.py` kalıbı (D-139 sözleşmesi: **kare başına model YALNIZ BİR KEZ**
  koşar, çıkan aynı `mk` + `icerik` **hem** `analyze_path`e **hem** `rota_bul`a verilir).
- Küme: CONTRACTS §12 DOĞRULAMA kümesi + `dataset/dji_kirsal_0038_bolum_v3` etiketli test bölümü
  (T152'nin `--etiket-dizin` kapısı buradan çalışıyor) + `data/arena_referans/sartname_s9_arena.png`.
- Eşit koşullar: aynı model (`model_registry.resolve_model`), aynı `conf=0,30`, aynı `imgsz`,
  aynı `icerik`, aynı `mpp` (kâhin çıktısı), `plan=True` her ikisinde.
- Yazılacak alanlar: `ap_yol · ap_red · ap_baskin_serit · rb_durum · rb_yol_no · rb_n_kapi`
  ve **T152 `rota_yol_olc`** ikisi için ayrı ayrı (`yol_payi`, `engel_wp`).
- Ön kayıt kapısı **sonuç görülmeden** yazılmalı; en az: *"`rota_bul` çekimserliği ≥ %X ise
  üretime aday değildir"* ve *"iki yolun `yol_payi` farkı ≤ 1 kare ise geometri denk sayılır"*.

**Ö2 · `road` istatistiği yeniden seçimi.** `scripts/olcum/92_t96_road_istatistigi.py` **tam arena
görüşünde** (kadraj alınmamış) yeniden koşulur; A=`darbogaz_serit`, B=`baskin_serit`, C=`cikis_serit`
aynı çıktıdan türetilir. Bu görevde ölçülen 6/15 vs 15/15, kadraj kümesindeki 198 vs 196 ile
**aynı tabloda** raporlanır. Karar mimarındır; §6.2 metni ancak ondan sonra değişir.

**Ö3 · Mutasyon kanıtı.** Bu görevde üretim kodu değişmediği için mutasyon borcu yok. Ö1/Ö2
betikleri yazılırsa kök satır bozulup testin düşmesi ve bayt-eş geri alınması gerekir.

---

## 4. ÖNERİ — mimara üç seçenek (karar VERİLMEDİ)

### Seçenek A — **`analyze_path` tek üretim yolu ilan edilir**, `rota_bul` tanısal olur

Taşınması gereken kapılar (bugün yalnız `rota_bul`da):
1. **`koridor_adaylari` 3-güzergâh kapısı** (şartname §2.1) — ya taşınır ya **açıkça
   "üretim tek koridor görür, üçü ayırt etmez" diye CONTRACTS'a yazılır**.
2. `rota_dogrula` K2/K3 ihlal denetimi + `ihlaller` alanı.
3. `road` istatistiği kararı (Ö2) — 6/15 ölçümü **bu seçeneğin bedelidir**, kapatılmadan A seçilirse
   şartname §5.3.2 riski taşınır.

- **30 Eylül maliyeti:** düşük — kod zaten sahada koşan yol; K1 telsiz halkası, T152 kapısı,
  model kabul kapıları (K1–K6), `_rota_kararini_esikle` hep buna bağlı. Değişiklik = **ekleme**.
- **Risk:** yanlış `road` yayını riski **ölçülmüş ve kapatılmamış** olarak kalır (6/15).
- **Ölçüm borcu:** Ö1 + Ö2.

### Seçenek B — **`rota_bul` tek üretim yolu ilan edilir** (CONTRACTS §11.2'nin bugünkü iddiası)

Taşınması gereken kapılar (bugün yalnız `analyze_path`te): `KENAR_GUVENSIZ`, `KORIDOR_DEGIL`,
**K-B güven eşiği**, `HEDEF_YOK`/HB, beraberlik bandı, rota ekseni, ve **§6.4 kanonik ret sözlüğü**
(rota_bul'un `durum` kelimeleri `ROTA_RET_SEBEPLERI`de yok — `test_rota_ret_nedenleri.py:71` kilitli).
Ayrıca **halka 6 (HB tohumu) SAHİPSİZ** olduğu için `baslangic`/`hedef` argümanlarını besleyecek
kaynak yok — rota_bul'un en büyük avantajı sahada **beslenemiyor**.

- **30 Eylül maliyeti:** **YÜKSEK.** K1 telsiz halkası, `_rota_kararini_esikle`, T152 kapısı,
  model kabul kapıları ve YKS hakem ekranı `analyze_path`in dönüş şekline bağlı.
  Köprü hazır (`analyze_path_uyumlu:1341`) ama **`return_reason`/`return_olcum` desteklemiyor** —
  yani ret sebebi ve `olcum` (hakem kanıt satırı) kaybolur.
- **Ölçülmüş engel:** çekimserlik. D-145: `ACIK` **34/260**; kuru koşuda gerçek karede
  `BELIRSIZ_TEK_KAPI`. Kadrajlı/gerçek görüntüde 3 kapı çoğunlukla görünmüyor → **NO_ROUTE fabrikası**.
  Şartname çekimserliği puan kaybı sayar, ama görev tamamen yayınsız kalırsa §6.4 "veri akışı
  sağlanamadı" riski doğar.
- **Bu seçenek Ö1 ölçülmeden seçilirse kanıtsızdır.**

### Seçenek C — **roller ayrılır: üretim `analyze_path`, tanısal/kapı `rota_bul`** (mevcut fiilî durum, ama **beyan edilerek**)

- CONTRACTS §11.2 halka 7 sahibi `rpi_inference.analyze_path` olarak **düzeltilir**; `rota_bul`
  "kapı ve tanı yolu" olarak ayrı satıra yazılır.
- `scripts/saha_kuru_kosu.py` halka `rota` **iki satır** üretir: `rota_uretim` (`analyze_path`,
  yayınlanabilirlik ölçütü) ve `rota_tani` (`rota_bul`, mevcut davranış). Bugün kuru koşu
  **sahada koşmayan yolu** ölçüp "rota DÜŞTÜ" diyor — bu, sahaya yanlış hazırlık sinyali veriyor.
- `codes/test_rota_sentetik.py` genel kapısına `analyze_path` kolu **eklenir** (rota_bul kolu aynen
  kalır, 15/15 bozulmaz): üretim yolu **ilk kez** şartname §2.1 topolojisinde zorlanmış olur.
  Bugünkü ölçüm o kapının eşiğinin **6/15 ile başlayacağını** söylüyor — eşik ön kayıtla konur.
- `analyze_path_uyumlu` ya **silinir** ya "yalnız tanı" diye işaretlenir (0 çağrı yeri, bakırlık).
- **30 Eylül maliyeti:** en düşük; davranış değişmez, **beyan** ve **kapı** değişir.
- **Risk:** 6/15 `road` bulgusu kapanmaz — ama artık **görünür** ve ön kayıtlı bir kapıya bağlanır.

### CONTRACTS §11.2 düzeltme metni — TASLAK (Seçenek C için; A ve B'de sahip hücresi değişir)

```markdown
| 7 | Rota üretimi | maskeler + `mpp` (+ `hb_xy`) | `road`, `waypoints`, `(sebep, detay)` | `codes/rpi_inference.py:1322` (`analyze_path`) — `run_camera`/`run_video` ve `yks_gui` bu yolu çağırır; yayın `comms/iha_sender.KararYayinci` (§6.5) | **KUSURLU** · D-25 · T151 |
| 7b | Rota kapısı / tanı | maskeler + `mpp` + KB/HB tohumu | `durum`, `yol_no`, `adaylar`, `ihlaller` | `codes/costmap_path_finder.py:983` (`rota_bul`) — genel kapı `codes/test_rota_sentetik.py`, saha tanı `jetson_paket/kod/kamera_dogrula.py:36`, FPS `scripts/jetson_fps.py:226` | **ÜRETİM DEĞİL** · T151 |
```

Metne eklenecek bağlayıcı cümle:

> **Saha gününde telsize yazan tek karar yolu halka 7'dir.** Halka 7b sahada yalnız tanı üretir;
> hiçbir `OPEN_ROUTE`/`NO_ROUTE` mesajı 7b'den doğmaz. İki yolun **kapı kümeleri farklıdır**
> (T151 §2.2); birinde olup diğerinde olmayan bir kapı, o yol üretime alınmadan **taşınmak zorundadır**.
> `scripts/saha_kuru_kosu.py` halka `rota`yı **7 üzerinden** ölçer; 7b ölçümü ayrı satırdır.

---

## 5. Koşulan komutlar ve gerçek çıktılar

```
$ O:/navitas-local-train/venv/Scripts/python.exe -B results/t151/iki_yol_kiyasi.py
  -> (tablo ve özet §3.1'de aynen)
  -> yazildi: O:\navitas\results\t151\iki_yol_kiyasi.json

$ O:/navitas-local-train/venv/Scripts/python.exe -B codes/test_rota_sentetik.py
  SONUC: 15/15 dogru
  [OK] TUM DETERMINISTIK SAHNELER GECTI

$ diff -q codes/rpi_inference.py jetson_paket/kod/rpi_inference.py            -> (fark yok)
$ diff -q codes/costmap_path_finder.py jetson_paket/kod/costmap_path_finder.py -> (fark yok)
$ diff -q codes/karar_sozlesmesi.py jetson_paket/kod/karar_sozlesmesi.py       -> (fark yok)
$ diff -q scripts/jetson_fps.py jetson_paket/kod/jetson_fps.py                 -> (fark yok)
```

Üretim kodu **değişmedi** → mutasyon borcu yok, `unittest discover` koşulmadı (kod değiştiren
ajan kapısıdır; bu görev salt okumadır).
