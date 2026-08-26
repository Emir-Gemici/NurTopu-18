# T153 — Katman 2 "ince beton şerit" çıkarıcısı (ON_KAYIT §13) · RAPOR

Tarih: 2026-08-26 · worktree `wf_2d1c9d5e-54f-1` (master 3bf66a6 üstüne) · yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`.
**Varsayılan DEĞİŞTİRİLMEDİ: `INCE_BETON_SERIT_ETKIN = False`.** Bu rapor yalnız sayıları ve "kural sağlandı/sağlanmadı"yı yazar; hüküm mimarındır.

## 0. Özet (bir bakışta)

| soru | sonuç |
|---|---|
| Dedektör kanalı buluyor mu? | Evet: 111 uzlaşı karesinin 25'inde ateşliyor; yazdığı piksellerin %66,5'i GT sınıf 1, %8,6'sı GT sınıf 0, %24,9'u etiketsiz (`dedektor_gt.json`). f157'de 6084 px, hepsi GT sınıf 1. |
| v35'te YANLIŞ GÜZERGÂH azaldı mı? | **15 → 14 (%6,7)**; kural ≥ %50 istiyordu → **SAĞLANMADI**. |
| Neden az? | Bindirmeler (`bindirme/`): modelin zemin blobu kanalın **kendisinden geniş** (kanal + oluk + banket). Dedektör beton şeridi çıkarınca rota şeridin yanındaki (GT sınıf 1 / etiketsiz) kalan zemine kayıyor; yalnız f158'de kalan şerit dar kalıp rota reddedildi (UC_BANT_TEMAS_YOK). |
| Meşru rota kaybı | v35: **1** (f158 — KAPALI'da TP ama rota kanal üstündeydi, "TP ve yol üstünde" sayımıyla 0) · v3: 0 · v6: 0 |
| Yeni FP | 0 / 0 / 0 |
| Sentetik K1–K6 birebir? | **Evet**, üç model (K0..K6 alanları + verdikt bayt-eş). Dedektör t66'da 284 dosyanın 5'inde ateşliyor (küçük parçalar), rota sonuçları değişmedi. |
| 67'de red ≤ 5? | 0 / 0 / 0 — ⚠ **yapısal olarak etkilenmez**: `109`'un `zemin_maskesi_reddi` yalnız zemin maskesine (mk[0]) bakar; dedektör yalnız engel katmanına (mk[1]) yazar. 67 karenin 17'sinde ateşliyor (otopark çizgileri), bunu 109 ölçmüyor. |
| **ON_KAYIT §13 benimseme kuralı** | v35: **SAĞLANMADI** (5 koşuldan 4'ü tutuyor, "yanlış ≥ %50 azalır" tutmuyor). v3/v6: azalma 0. → **KAPALI kalır.** |

## 1. Uygulama

- `codes/karar_sozlesmesi.py` — `ince_beton_serit_maskesi(bgr)` + `INCE_BETON_*` sabitleri (gerekçeli), `INCE_BETON_SERIT_ETKIN = False`, `INCE_BETON_SERIT_ORTAM_DEGISKENI = "NAVITAS_INCE_BETON_SERIT"`.
  Yöntem: LAB L ≥ 225 ∧ kroma ≤ 20 → 3 px açma (benek/zincir kırma) → 5 px kapama → bağlı bileşen: genişlik (2·max uzaklık dönüşümü) 3–14 px @512 (oran), uzunluk = alan/genişlik ≥ 40 px @512 ve ≥ 4·genişlik, halka kontrastı ≥ 30 L. Fail-closed: çözülemeyen girdide `None`, küçük girdide boş maske. Yalnız OpenCV/NumPy.
  ⚠ Top-hat (açma tabanlı) **kullanılmadı**: benekli kuru otta her 29 px pencerede koyu gölge olduğundan top-hat her yeri "parlak" gösterdi (keşif: L 170 piksellerde top-hat 100+); bu sürüm mutlak parlaklık + şekil + halka kontrastıdır.
  Sabitler f157/f196/f213 (3 kare) keşif ölçümüyle seçildi; **ölçüm sonrası oynatılmadı** (aşağıdaki §5 f196 sınırı dâhil).
- `codes/rpi_inference.py` — `get_masks(..., ince_beton_serit=None)`: öncelik parametre > ortam değişkeni ("1"/"0") > sabit. Etkinse `_ince_beton_seridi_ekle` masks[1]'e OR (T67 `_ince_bariyeri_ekle` ile aynı kalıp; `orig_img` yoksa sessizce atlanır). Açıkken bir kez stderr'e `T153: ince beton serit cikaricisi ACIK` yazar (log kanıtı).
- `jetson_paket/kod/{rpi_inference,karar_sozlesmesi}.py` — kopyalandı; `diff` boş (`AYNA_ES`).
- Not: worktree dalı başta f1c5931'deydi (master 3bf66a6'nın 40+ commit gerisinde); iş `git reset --hard master` ile güncel master üstüne alındı (yerel, pull/fetch yok).

## 2. Testler — `tests/test_t153_ince_beton_serit.py` (22 test)

```
> venv\Scripts\python.exe -m unittest discover -s tests -p "test_t153_ince_beton_serit.py"
Ran 22 tests in 0.483s
OK
```
Kapsam: dar şerit engel (4/6/8/12 px), geniş yol (30/60/120 px ve 40 px çapraz) engel DEĞİL, kablo (1 px çapraz, 2 px yatay) değil, kısa leke değil, kırmızı şerit (kroma) değil, kontrastsız şerit değil, aynı karede yol kalır + kanal engel, fail-closed, ölçek bağımsız oran (1024 tuval), `get_masks` kapalıyken bayt-eş, parametre/ortam önceliği, farklı çözünürlükte yeniden ölçek, **madde 15** (serbest alan yalnız küçülür, açıkken gerçekten küçülür), T67 ile birlikte çalışma, sabit kilitleri (varsayılan KAPALI, oranlar, en/boy T67 ile aynı, kroma üst < bariyer kroma alt).

### Mutasyon kanıtı — `mutasyon_kosumu.py` → `mutasyon.log`
```
MUTASYON YOK (kontrol)                      Ran 22  OK
MUTASYON: INCE_BETON_GENISLIK_UST_ORANI = 1.0 (ust sinir YOK)
  Ran 22  FAILED (failures=5)  DUSEN: test_AYNI_KAREDE_yol_KALIR_kanal_ENGEL, test_GENIS_ACIK_YOL_engel_SAYILMAZ (x2), test_GENIS_CAPRAZ_YOL_engel_SAYILMAZ, test_olcutler_ORAN...
MUTASYON: uzunluk / en-boy suzgeci YOK
  Ran 22  FAILED (failures=3)  DUSEN: test_KISA_PARLAK_LEKE_engel_SAYILMAZ, test_en_boy_T67_ile_AYNI, test_olcutler_ORAN...
```
Genişlik üst sınırı kalkınca geniş açık yol engel oluyor ve test düşüyor (istenen mutasyon).

## 3. Kapılar

```
> venv\Scripts\python.exe codes\test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

> venv\Scripts\python.exe -m unittest discover -s tests -q        (unittest.log)
Ran 962 tests in 64.286s
FAILED (failures=4, errors=11, skipped=16)
```
15 düşüşün hepsi worktree ortamı (ağırlık/veri worktree'de yok), kod değil — her birinin son satırı:
- `test_imgsz_tek_kaynak` (2), `test_saha_parametrik` (8), `test_model_registry` (1): `Manifest navitas_seg_v35_best.pt diyor ama agirlik diskte YOK (bakilan: ...wf_2d1c9d5e-54f-1\jetson_paket\models, ...\models)` / `model artefaktı yok: ...\models\navitas_seg_v35_best.pt`
- `test_t123_gecis_provasi` (4): `No such file or directory: ...jetson_paket\models\navitas_seg_v34_best.pt` / yedek pakette yok
- `test_yks_gui_uretim_hizasi.test_kompozit_dizini_listeleniyor`: `kompozit kume bos listelendi` (data/arena_kompozit görüntüleri worktree'de yok)

## 4. Ölçüm (GPU SIRALI, tek YOLO süreci; `kosum/surucu.py`, loglar `log/`)

Yol: ana depodaki `scripts/olcum/142_gece_olcum.py` (→ 109 + 126 + tavan + b-ek2) ve `65_kabul_denetcisi.py`, **PYTHONPATH=`kosum/`** ile `sitecustomize.py` worktree `codes/`'unu önceden yükler (her log: `[T153 sitecustomize] rpi_inference=O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1\codes\rpi_inference.py NAVITAS_INCE_BETON_SERIT='1'`), `NAVITAS_INCE_BETON_SERIT=1/0` ile AÇIK/KAPALI. Ölçüm betikleri **üretim yolunu** (`_preprocess → predict(512, conf 0,30) → get_masks → _maskeleri_icerige_kirp → analyze_path`) kullanır; dedektör `get_masks` içinde çalışır.
KAPALI koşumları önceki koşumlarla birebir (v35 test29: ROTA 6 / yanlış 5 = `v35_ref3`; val82: ROTA 15 / yanlış 10 / TP 15 FP 0 FN 28 = `sizinti/val82_v35`; v3 val82 31/5/30/1; v6 val82 35/8/33/2).

Komut örneği (log başında tam hâli):
```
142_gece_olcum.py --agirlik O:\navitas\models\navitas_seg_v35_best.pt --ad t153_acik_v35_val82 --atla-kabul
  --test-dizin ...\dji_kirsal_0038_bolum_v3\images\val --etiket-dizin ...\labels\val
  --tavan ...\gece_20260826\sizinti\val82_etiket_tavani.json --cikti ...\results\t153\olcum
65_kabul_denetcisi.py --model <ağırlık> --ad t153_acik_<model>
```

### 4.1 Tablo — K = KAPALI / A = AÇIK (`analiz.py` → `analiz.json`, `analiz.log`)

| model | bölüm | ROTA K/A | YANLIŞ K/A | yol üstünde K/A | TP K/A | FP K/A | FN K/A | MASKE_YOK K/A | meşru kayıp (yol üst.) | yeni FP | yanlış→yol | yanlış→yok | yol→yok | red67 K/A |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v35 | test29 | 6/6 | 5/5 | 1/1 | 5/5 | 1/1 | 7/7 | 16/16 | 0 (0) | 0 | 0 | 0 | 0 | 0/0 |
| v35 | val82 | 15/14 | 10/9 | 5/5 | 15/14 | 0/0 | 28/29 | 49/49 | 1 (0) | 0 | 0 | 1 | 0 | 0/0 |
| **v35** | **111** | 21/20 | **15/14** | 6/6 | 20/19 | 1/1 | 35/36 | 65/65 | **1 (0)** | **0** | 0 | 1 | 0 | – |
| v3 | test29 | 10/10 | 4/4 | 6/6 | 9/9 | 1/1 | 3/3 | 11/11 | 0 (0) | 0 | 0 | 0 | 0 | 0/0 |
| v3 | val82 | 31/31 | 5/5 | 26/26 | 30/30 | 1/1 | 13/13 | 30/30 | 0 (0) | 0 | 0 | 0 | 0 | 0/0 |
| **v3** | **111** | 41/41 | **9/9** | 32/32 | 39/39 | 2/2 | 16/16 | 41/41 | 0 (0) | 0 | 0 | 0 | 0 | – |
| v6 | test29 | 12/12 | 5/5 | 7/7 | 10/10 | 2/2 | 2/2 | 8/8 | 0 (0) | 0 | 0 | 0 | 0 | 0/0 |
| v6 | val82 | 35/35 | 8/8 | 27/27 | 33/33 | 2/2 | 10/10 | 20/20 | 0 (0) | 0 | 0 | 0 | 0 | 0/0 |
| **v6** | **111** | 47/47 | **13/13** | 34/34 | 43/43 | 4/4 | 12/12 | 28/28 | 0 (0) | 0 | 0 | 0 | 0 | – |

Tanımlar: meşru kayıp = KAPALI'da TP (model rota ∧ tavan rota) olup AÇIK'ta rota üretmeyen kare (ON_KAYIT §13 tanımı); parantez = aynı sayım "TP ∧ yol üstünde" ile. yeni FP = AÇIK'ta tavana göre FP olup KAPALI'da FP olmayan.
v35 val82 AÇIK ayrıntı: yanlış 9 = 130, 153, 156, 157, 159, 201, 203, 208, 230 (KAPALI listesinden 158 düştü: rota yok → UC_BANT_TEMAS_YOK). 157: engel_wp 8/8 → 6/8, 156: 1/8 → 2/8, 153: 8/8 → 7/8 (yanlış kaldı). Test29'da 196 (D-289'un karesi) AÇIK'ta hâlâ engel_wp 8/8: dedektör 196'da yalnız üst bordür parçasını (561 px) buluyor, rotanın üstündeki alt kanal segmentini bulmuyor (§5).

### 4.2 Sentetik kabul (65, AÇIK) — K1–K6 KAPALI referansla (`scripts/olcum/results/t63/k6_<model>_kabul_verdikt.json`) kıyas

| model | K1 | K2 | K3 | K4 | K6 | K5 kesen | K0 figür | verdikt | birebir |
|---|---|---|---|---|---|---|---|---|---|
| v35 AÇIK / ref | 256/260 = 256/260 | 18/256 = | 0/256 = | 1/256 = | 5/256 = (aynı 5 kare) | 0 = | 0,090305 = | True = | **EVET** |
| v3 AÇIK / ref | 253/260 = | = | = | = | 1/253 = | 0 = | 0,019514 = | True = | **EVET** |
| v6 AÇIK / ref | 257/260 = | = | = | = | 3/257 = | 0 = | 0,048786 = | True = | **EVET** |

Kanıt: `kabul/t153_acik_<model>_kabul_verdikt.json`, `log/t153_acik_<model>_65.log` (sitecustomize + "ACIK" satırı). 65'in çağırdığı 61 alt süreci ortamı miras alır (`subprocess.run` `env` vermez). Dedektör tek başına (CPU, `dedektor_sentetik_otopark.py`): t66 dizinindeki 284 dosyanın 5'inde ateşliyor (sa_000013 2054 px, sa_000121 385, sa_000192 582, sa_000226 1150; toplam 6588 px) — rota/K sonuçlarını değiştirmedi. Arena figüründe 0 px.

### 4.3 67 gerçek otopark karesi (109, 142 içinde her koşumda)
`zemin_maskesi_reddi` = 0 (AÇIK ve KAPALI, üç model); 109'un tüm sayıları (çatı kaçağı, kaplama67, figür oranı) AÇIK/KAPALI birebir. ⚠ Bu, dedektörün 67 karede sustuğu anlamına GELMEZ: tek başına 67 karenin 17'sinde ateşliyor (24 746 px; otopark çizgileri / kaldırım kenarı). 109 zemin maskesine bakar, engel katmanına yazılan piksel bu ölçüte girmez. Üretimde etkisi (`zemin AND NOT engel`) 109 ile ölçülmemiştir — açık soru.

### 4.4 Dedektör tek başına, uzlaşı referansına karşı (CPU, `dedektor_gt.py` → `dedektor_gt.json`)
111 kare: 25 karede ateşleme, toplam 89 539 px @960×540; GT sınıf 1 payı 0,665 · sınıf 0 payı 0,086 · etiketsiz 0,249. Sınıf 0 üstüne >100 px yazan 3 kare: f152 (2394 px — uzlaşı referansı bu karede beton kanalı **sınıf 0** etiketlemiş görünüyor, bindirme `v35_iyi_5_...152`), f156 (3422 px), f216. En çok px: f153 6399 (5504 GT1), f157 6084 (6084 GT1), f207 5821, f152 5168, f206 5163, f156 5132, f205 4813, f218 4536, f217 4399, f197 4270.

## 5. Bindirmeler — `bindirme/v35_{iyi,kotu}_<i>_<kare>.jpg` (alt: zemin YEŞİL, dedektör MOR, GT sınıf1 KIRMIZI kenar, rota KAPALI camgöbeği, rota AÇIK sarı)
- **iyi**: 158 (rota kanaldan düştü → rota yok), 153/157/208 (yanlış kaldı, engel_wp azaldı), 152 (dedektör kanalı örtüyor, rota yanında).
- **kötü** (meşru kayıp 158 + dedektörün en çok yazdığı TP kareler): 158, 153, 157, 152, 156.
- Gözlem (tüm kanal karelerinde aynı motif): mor şerit beton kanalın **parlak üst yüzeyini** örtüyor; yeşil zemin blobu ise kanal + koyu oluk + banketi kapsıyor. Çıkarma sonrası kalan yeşil şerit (GT sınıf 1 / etiketsiz) rotayı taşımaya yetiyor → yanlış güzergâh sürüyor. Yani sızıntının kaynağı "beton şerit" değil, "kanal koridoru boyunca geniş zemin blobu"; Katman 2 şerit çıkarıcısı bunu tek başına kapatamıyor.
- f196 sınırı: bordür L tepe 228–255 ama @512'de 1–2 px genişlikte, yanları ~220 → L ≥ 225 eşiğinde parçalanıp 3 px açmada siliniyor (keşif ölçümü, `debug196`). Eşik sonuca göre gevşetilmedi.

## 6. ON_KAYIT §13 benimseme kuralı — değerlendirme (hüküm DEĞİL, sayım)

| koşul | v35 | v3 | v6 |
|---|---|---|---|
| YANLIŞ GÜZERGÂH ≥ %50 azalır (111 kare) | 15→14, %6,7 → **sağlanmadı** | 9→9, %0 → sağlanmadı | 13→13, %0 → sağlanmadı |
| meşru rota kaybı ≤ 1 | 1 → sağlandı | 0 → sağlandı | 0 → sağlandı |
| yeni FP = 0 | 0 → sağlandı | 0 → sağlandı | 0 → sağlandı |
| sentetik K1–K6 birebir | sağlandı | sağlandı | sağlandı |
| 67'de red ≤ 5 | 0 → sağlandı (⚠ yapısal, §4.3) | sağlandı | sağlandı |
| **KURAL** | **SAĞLANMADI** | sağlanmadı | sağlanmadı |

→ Kurala göre dedektör **KAPALI kalır**; varsayılan değiştirilmedi. Eşikler oynatılmadı.

## 7. Dosyalar
- Kod: `codes/karar_sozlesmesi.py`, `codes/rpi_inference.py`, `jetson_paket/kod/*` (ayna), `tests/test_t153_ince_beton_serit.py`.
- Bu dizin: `rapor.md`, `analiz.json/.log`, `dedektor_gt.json/.log`, `dedektor_sentetik_otopark.json/.log`, `mutasyon.log`, `mutasyon_kosumu.py`, `unittest.log`, `olcum/` (142 + 126 JSON'ları, 12 koşum), `log/` (12 × 142 + 3 × 65 + sürücü), `kabul/` (65 verdikt kopyaları; asılları `O:\navitas\scripts\olcum\results\t63\t153_acik_*`), `bindirme/`, `kosum/` (sitecustomize, sürücü, analiz, bindirme, dedektör betikleri, bekle).

## 8. Açık sorular (mimara)
1. Kanal sızıntısı şerit değil koridor: modelin zemin blobu kanal+oluk+banketi kapsıyor. Katman 2'de "şerit + her iki yanında X px tampon" (dilate) denemesi ON_KAYIT'ta yok; yeni ön kayıt ister (madde 15 yine korunur, ama meşru rota kaybı riski artar — f157'de banket ile yol arası dar).
2. 109'un `zemin_maskesi_reddi` engel katmanını görmüyor; Katman 2 dedektörlerinin 67 karedeki gerçek etkisi (`zemin AND NOT engel` üzerinden red) ölçülmüyor — T67 için de geçerli.
3. Uzlaşı referansı f152'de beton kanalı sınıf 0 sayıyor (dedektör 2394 px "yol üstüne" yazmış görünüyor); f157/153'te sınıf 1. Etiket tutarlılığı.
4. f196 (D-289'un karesi) bordürü @512'de 1–2 px: 512 çıkarım tuvalinde bu yapı çözünürlük sınırında; dedektör 960/768 tuvalde koşturulmadı.
