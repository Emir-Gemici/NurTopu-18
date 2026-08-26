# T152 · ON_KAYIT §11(2) — "rota YOL ÜSTÜNDE mi" kapısı (b-ek2) · rapor

Tarih: 2026-08-26 (ön kayıt §11 "sonuç görülmeden" yazıldı; bu betik ve ölçüm ondan sonra).
Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`. Çalışma: worktree `wf_5da987c3-099-1`
(master `d195073` üstüne). Modeller/veri `O:\navitas\…` salt okunur; çıktılar bu klasör.

⚠ **Referans notu:** Bu ölçüm **v2** referansıyladır (`dataset/dji_kirsal_0038_bolum_v2/labels/test`,
tek geçiş + tamamlama). §11'in **uzlaşı referansı (v3)** henüz yok; §11(3) yeniden ölçüm v3 gelince
koşulur. Aşağıdaki hükümler v3 ile **değişebilir** (özellikle frame_000196: D-288'e göre v2'de
asfalt = sınıf 1, mera = sınıf 0 — bkz. §4 v35 satırı).

## 1. Değişiklikler

| dosya | ne |
|---|---|
| `scripts/olcum/126_t138_gece_kumesi.py` | her kareye `olceksiz_wps` / `olcekli_wps`: `[[x,y],…]` tuval (letterbox) koordinatı, tam sayı. Mevcut alanlar/davranış aynı (§3 kıyas: 29/29 kare eski alanlarda **0 fark**). |
| `scripts/olcum/142_gece_olcum.py` | `--etiket-dizin <labels/test>` → (b-ek2). `KAPI_B_EK2 = {"yol_payi_min": 0.90, "engel_wp_maks": 0}` (ON_KAYIT §11(2) atfıyla). Fonksiyonlar: `uc_durum_maske` (143'teki yerleşimle tuvale rasterize, 0 etiketsiz/1 sınıf 0/2 sınıf 1, çakışmada engel), `rota_yol_olc` (1 px `cv2.polylines`, yol_payi / etiketsiz_payi / engel_payi / engel_wp — tuval dışı waypoint de engel sayılır, fail-closed), `yanlis_guzergah_mi` (yol_payi < 0,90 VEYA engel_wp > 0), `rota_yol_kapisi`. JSON: `kapi_sabitleri_b_ek2`, `rota_yol` (kare başına liste), `kapi_b["yanlis_guzergah==0"]`. `--cikti` (varsayılan değişmedi). `--etiket-dizin` verilmezse hiçbir yeni alan yazılmaz. |
| `tests/test_t152_rota_yol_ustunde.py` | 9 test (a–e + dosya tabanlı 3). 142 `spec_from_file_location` ile yüklenir. |

Tasarım notu: sabitler `KAPI` sözlüğüne **eklenmedi**, ayrı `KAPI_B_EK2` sözlüğünde tutuldu; çünkü `KAPI`
her koşumda JSON'a yazılıyor ve göreve göre `--etiket-dizin`siz çıktı bayt-eş kalmalıydı. `KAPI_B_EK2`
yalnız kapı koşunca JSON'a (`kapi_sabitleri_b_ek2`) yazılır.

## 2. Testler + mutasyon

```
> venv -m unittest discover -s tests -p "test_t152_rota_yol_ustunde.py" -v
test_eski_126_ciktisi_wps_yoksa_acik_hata ... ok
test_kapi_yalniz_rota_karelerini_sayar ... ok
test_uc_durum_maske_tuvale_yerlesir ... ok
test_a_yol_ustunde_rota_gecer ... ok
test_b_cimden_gecen_rota_pay_yarim_yanlis ... ok
test_c2_tuval_disi_waypoint_engel_sayilir ... ok
test_c_sinif1_ustunde_tek_waypoint_yanlis ... ok
test_d_esik_tam_sinir ... ok
test_e_mutasyon_yol_payi_kiyasi_kaldirilinca_b_gecer ... ok
Ran 9 tests in 2.184s
OK
```

Mutasyon (scratchpad `mutasyon.py`: 142'de `if olcum["yol_payi"] < kapi["yol_payi_min"]: return True`
satırı silindi, testler koşuldu, dosya bayt-eş geri kondu):
```
ONCE sha256: a8d4f4497157797444b2c7ebb7b74902e3a8df4236ec27653cc943f326a841fb
MUTANT: kapi satiri kaldirildi; kalan 'yol_payi_min' gecisleri: [41]
FAIL: test_b_cimden_gecen_rota_pay_yarim_yanlis   AssertionError: False is not true
FAIL: test_d_esik_tam_sinir                        AssertionError: False is not true
FAIL: test_e_mutasyon_yol_payi_kiyasi_kaldirilinca_b_gecer   AssertionError: False is not true
Ran 9 tests in 1.484s
FAILED (failures=3)
GERI ALINDI sha256: a8d4f4497157797444b2c7ebb7b74902e3a8df4236ec27653cc943f326a841fb bayt-es: True
GERI ALINDIKTAN SONRA: OK
```
Test (e) ayrıca test içinde `mock.patch.object` ile aynı mutantı kurup (b) örneğinin "yol üstünde"
çıktığını ve `assertTrue`'nun `AssertionError` attığını gösterir.

Genel kapı:
- `codes/test_rota_sentetik.py` → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI`
- `-m unittest discover -s tests -q` → `Ran 925 tests` · `FAILED (failures=4, errors=11, skipped=16)` — 15'i
  worktree ortamı (`unittest_discover.log`): `models/*.pt` ve `jetson_paket/models` worktree'de yok
  (test_imgsz_tek_kaynak ×2, test_model_registry ×1, test_saha_parametrik ×7, test_t123_gecis_provasi ×4),
  `data/arena_kompozit` boş (test_yks_gui_uretim_hizasi ×1). Hiçbiri değişen dosyaları içe almaz.

## 3. Ölçüm — komutlar

```
venv scripts/olcum/142_gece_olcum.py --agirlik O:/navitas/codes/runs/segment/gece_v6_v35taban/weights/best.pt --ad v6_t152 --atla-kabul
     --test-dizin O:/navitas/dataset/dji_kirsal_0038_bolum_v2/images/test
     --tavan O:/navitas/results/gece_20260826/test29_etiket_tavani_v2.json
     --etiket-dizin O:/navitas/dataset/dji_kirsal_0038_bolum_v2/labels/test --cikti results/t152
venv scripts/olcum/142_gece_olcum.py --agirlik O:/navitas/models/navitas_seg_v35_best.pt --ad v35_t152 (aynı argümanlar)
```
(Adım 2'nin `data/raw_frames`'i için worktree'de geçici junction → `O:\navitas\data\raw_frames`; ölçüm sonrası kaldırıldı.)

Geriye uyumluluk (scratchpad `kiyas.py`, yeni 126 çıktısı vs önceki `*_ref2_test29.json`, yeni `*_wps` alanları
ve `sure_sn` hariç):
```
v6_t152 vs gece_v6_ref2 | kare farki: 0 / 29 | ozet ayni: True | eski JSON'da wps alani var mi: False
v35_t152 vs v35_ref2    | kare farki: 0 / 29 | ozet ayni: True | eski JSON'da wps alani var mi: False
```
(Eski JSON'da alan yok → 142 `rota_yol_kapisi` bunu açık `SystemExit` ile söyler; test var.)

## 4. Ölçüm — sonuç (v2 referansı)

### v6 (`olcum_v6_t152.log`, `v6_t152_olcum.json`)
```
[3] test29 rota 12 · maske_yok 8 · uc_bant 8   [3-ek] tavan 15 · TP 11 · FP 1 (000218) · FN 4
[3-ek2] rota_yol rota_kare 12 · yanlis_guzergah 5
  frame_000143: yol 0.62 etiketsiz 0.38 engel_wp 0/8 -> YANLIS GUZERGAH
  frame_000160: yol 0.75 etiketsiz 0.25 engel_wp 0/8 -> YANLIS GUZERGAH
  frame_000196: yol 0.21 etiketsiz 0.79 engel_wp 0/8 -> YANLIS GUZERGAH
  frame_000205: yol 0.32 etiketsiz 0.67 engel_wp 0/8 -> YANLIS GUZERGAH
  frame_000218: yol 0.49 etiketsiz 0.51 engel_wp 0/8 -> YANLIS GUZERGAH
  (diğer 7 rota karesi: yol 1.00, engel_wp 0)
HUKUM: rota>=10 GECTI · maske_yok<=10 GECTI · FP<=1 GECTI · yanlis_guzergah==0 DUSTU → (b) DUSTU · TERFI ADAYI False
```
**D-288'in üç karesi (196, 205, 218) "YANLIŞ GÜZERGÂH" çıktı**; pay değerleri D-288/güvenlik lensiyle
(0,21 · 0,32 · 0,49) **aynen** örtüşüyor (aynı yöntem: 1 px polylines ∩ sınıf 0). D-288'in "143 ve 160'da
%25–38 çime taşıyor" notu da 0,90 eşiğinin altında kaldığı için bu iki kare de düştü → v6'da 5/12.
Hiçbir v6 waypoint'i sınıf 1 üstünde değil; düşüşlerin tamamı etiketsiz (çim/tarla) üstünden geçen çizgi payından.

### v35 (`olcum_v35_t152.log`, `v35_t152_olcum.json`)
```
[3] test29 rota 6 · maske_yok 16 · uc_bant 7   [3-ek] tavan 15 · TP 6 · FP 0 · FN 9
[3-ek2] rota_kare 6 · yanlis_guzergah 4
  frame_000135: yol 0.88 etiketsiz 0.12 engel_wp 0/8 -> YANLIS GUZERGAH   (eşiğe 0,02 kala)
  frame_000152: yol 0.58 etiketsiz 0.42 engel_wp 0/8 -> YANLIS GUZERGAH
  frame_000196: yol 0.43 etiketsiz 0.20 engel_wp 3/8 -> YANLIS GUZERGAH   (çizgi %37 sınıf 1 üstünde)
  frame_000202: yol 0.12 etiketsiz 0.17 engel_wp 5/8 -> YANLIS GUZERGAH   (çizgi %71 sınıf 1 üstünde)
HUKUM: rota>=10 DUSTU · maske_yok<=10 DUSTU · FP<=1 GECTI · yanlis_guzergah==0 DUSTU
```
Dikkat — **v35'in 196'sı engel waypoint'iyle düşüyor**: D-288'e göre v2 referansında 196'da asfalt yol
sınıf 1, mera sınıf 0. v35 rotasının 3 waypoint'i "sınıf 1" (= muhtemelen asfalt) üstünde; yani v35 burada
büyük ihtimalle YOLU izlerken referans hatası yüzünden cezalanıyor; v6'nın çizgisi ise %79 etiketsiz (tarla)
üstünde (yol 0,21, engel 0,00) — kapı v6'yı doğru sebeple, v35'i muhtemelen yanlış sebeple düşürüyor. Bu, kapının değil **referansın** kusurudur ve tam olarak §11(1) uzlaşı geçişinin (v3) sebebidir.
Aynı uyarı 202 için de geçerli olabilir (ölçülmedi; gözle bakılmadı — bu rapor referansı düzeltmez, §11 "FP
karesine bakıp referans düzeltmek yapılmaz").

### Özet
| model | ROTA | MASKE_YOK | TP/FP/FN | yanlış güzergâh | (b) |
|---|---:|---:|---|---:|---|
| v35 | 6 | 16 | 6/0/9 | **4/6** | DÜŞTÜ |
| v6 | 12 | 8 | 11/1/4 | **5/12** (196, 205, 218 + 143, 160) | DÜŞTÜ (yalnız b-ek2) |

Kapı eklenmeden v6 (b)'yi geçiyordu (D-288); kapı ile **geçmiyor** — D-288'in gözle bulduğu üç yanlış
güzergâh artık ölçümle yakalanıyor. Eşik gevşetilmedi (0,90 / 0). v3 referansıyla §11(3) yeniden ölçüm beklemede.

## 5. Bayt-eşlik (142, `--etiket-dizin`siz)
`--ad v6_eskiyol` ile `--etiket-dizin`siz koşum (`olcum_v6_eskiyol.log`, `v6_eskiyol_olcum.json`) vs
önceki `gece_v6_ref2_olcum.json` (yalnız ad/saniye/yollar hariç; test29'da `json` yolu hariç):
```
anahtarlar ayni: True ['agirlik', 'ad', 'kapi_sabitleri', 'taban_v35', 'test_dizin', 'tavan', 'k109', 'test29', 'test29_tavan', 'kapi_a', 'kapi_b', 'a_gecti', 'b_gecti', 'terfi_adayi', 'saniye']
kapi_sabitleri         AYNI
taban_v35              AYNI
k109                   AYNI
test29                 AYNI
test29_tavan           AYNI
kapi_a                 AYNI
kapi_b                 AYNI
a_gecti                AYNI
b_gecti                AYNI
terfi_adayi            AYNI
```
Yeni anahtar yok (`kapi_sabitleri_b_ek2`, `rota_yol`, `kapi_b["yanlis_guzergah==0"]` yalnız `--etiket-dizin` ile).
