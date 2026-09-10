# T213-A · K3-b — Üretim modeli v36 render mozaikte yolu neden görmüyor? Teşhis + render varyantları

> **Kural:** ÖLÇÜLEMEDİ ≠ GEÇTİ. Eşik (H1-K3 doğru etiket ≥ 12/15) **değişmedi**. Üretim modeli v36
> (`sha 1d1caca6…`, kayıtla eş) **değişmedi**; sim'e özel eğitim/ince ayar **yok**. Bu belge
> ölçümden yazıldı; sayılar `k3b/*.json` (ölçüm) ve `simulation/mujoco/k3b_ozet.py` (tablo) kaynaklıdır.
> Koşum betikleri: `k3b/kosum.sh` (tur 1) ve `k3b/kosum2.sh` (tur 2, son kod), ham çıktılar `k3b/kosum_log.txt`,
> `k3b/kosum2_log.txt`. Tarih: 10 Eylül 2026 (10:3x–10:5x). Harita başına mozaik/algı JPG'leri git dışıdır
> (`kosum2.sh` içerik-eş yeniden üretir: GPU render, kareler ~%50 bayt-eş, mozaik maks 8 seviye / %0,3 piksel fark; hüküm ve sayılar aynı — çürütücü ölçümü 10 Eyl); `detection.json`/`poses.csv`/`meta.txt`/`tarama_ozeti.json` ve `ornekler/` depodadır.

## 0. Sonucun özeti (ayrıntı §3)

- **Teşhis tahmini (mimar): "model bandı yol değil boş zemin sayıyor" — DOĞRULANDI, ama tek neden değil.**
  Üç kanıtlı neden bulundu: (1) doku ölçeği/kaynak seçimi (taban zemini eğitimde *yol* etiketli bir
  kırpma, yol şeridi 5,8× büyütülmüş açık gri bant), (2) **T212 mozaik yer kaydı kusuru** — düz tarama
  bacaklarında İHA 26,2° yatık uçuyordu, nadir 14,8 m kayıyor; kare süzgeci roll'a bakmadığı için
  mozaik ±15 m kaymış/kesilmiş kuruluyordu (yer gerçeği şeritleriyle örtüşmüyordu), (3) rota
  zincirinin **HB pedi** semantiği: ped (2×2 m, kırmızı H) zemin sınıfı değil → tek piksel HB tohumu
  C-uzayında hiç geçilebilir olmuyor, her koridor "geçilemez".
- (2) düzeltildi (`iha_ucus.UcusProfili`: tarama segmentinde roll = 0; nöbetçi test).
- **10 Eyl ek (§7):** çürütücü düzeltmeleri (teşhis geçişi üretim kanıtını eziyordu → ayrı kök; kanıt kendini etiketler) ve **D-441 arena yerleşim kusuru** (engeller açık yol hattına sokuluyordu) düzeltildi; yeni yerleşimle v1 **7/15** (7/7 doğru) — K3 yine DÜŞTÜ (eşik 12/15). T212 sha kilidi yenilendi (T213-B armature + D-441). Bu düzeltme
  **taban dâhil tüm varyantları** etkiler; taban 15 haritada **yeniden ölçüldü** (T212 kaydı 0/15 dokunulmadı).
- Varyant sonuçları (üretim semantiği, HB tohumu tek piksel): tablo §4. TEŞHİS sütunları (HB tohumu
  2,5 m; imgsz 512) karar zincirini değiştirmez, mimara öneri gerekçesidir.

## 1. Teşhis — sınıf şeması, piksel oranları

**Sınıf sözleşmesi** (`codes/sinif_semasi.py`, CONTRACTS §1): eğitim sınıfı `0 = traversable`,
`1 = blocked`; costmap katmanları `KATMAN_ZEMIN=0` (geçilebilir), `KATMAN_MOLOZ=1`, `KATMAN_ARAC=10`
(sim'de kapalı). **"traversable" = YOL YÜZEYİ**dir (`dataset/VERI_KAYNAKLARI.md` §3.1: RescueNet
`road-clear` → 0), genel "yürünebilir zemin" değil. Eğitim kareleri (`dataset/dji_kirsal`, 101 kare,
etiket alanı ort. %35,7 traversable / %13 engel; bakıldı: kare 3, 18, 170; RescueNet 10778; otopark;
sentetik arena) yolu **3–6 m genişlikte, kenarlı** (banket/ot/toprak geçişi, tekerlek izi, gölge)
gösteriyor; sürülmüş tarla / ot / çalı **etiketsiz arka plan**.

**Taban mozaikte modelin ne dediği** (T212 kaydı `on_olcum_K3_15harita.json`, 15 harita):
HTAB geçilebilir %0–15 (ort. ~%6), engel %12–45, kalan **~%70 etiketsiz**; açık yol şeridinde
geçilebilir 0–0,36 (11 haritada 0), yol dışı zeminde 0–0,14. Yani model bandı ne yol ne engel
sayıyor; zeminde ise (eğitimde yol etiketli `toprak_kaynak` kırpması) yer yer yeşil.
Yer kaydı kusuru (§2) nedeniyle bu oranlar zaten şeritle örtüşmeyen bir mozaikte ölçülmüştü.

**Yer kaydı düzeltilmiş taban (bu görev, `k3b/taban_15harita.json`):** 0/15 rota, 0/15 doğru;
HTAB geçilebilir 0–0,16, engel 0,17–0,46, açık yol şeridinde geçilebilir ort. 0,12
(9 haritada 0), yol dışı ort. 0,02. Durumlar: BELIRSIZ_TEK_KAPI / MASKE_YOK / KAPI_YOK / KAPALI_DAR.

## 2. Teşhis — ölçek (GSD), imgsz, yer kaydı

### 2.1 Doku ölçeği (kaynak: `dokular/KAYNAK.md §GSD`, SRT ile ölçüldü)
| kaynak | irtifa (SRT) | m/px | taban kullanımı | büyütme |
|---|---|---|---|---|
| `toprak_kaynak` (zemin) | 29,7 m | 1,08 cm | 512 px yama → 12,5 m | **2,3×** |
| `stabilize_kaynak` (yol) | 16,3 m | 0,59 cm | 366 px yama → 12,5 m | **5,8×** |

HTAB dokusu 2,44 cm/px; taban dokular içeriği 2–6 kat iri döşüyordu. Ek olarak `toprak_kaynak`
kırpması (kare 170, x 2900–3800) eğitim etiketinde **traversable** bölgesidir.

### 2.2 Model girişi GSD karşılaştırması
| yol | çerçeve | model girişi |
|---|---|---|
| Eğitim (DJI 3840 px → imgsz 512) | 0,59–1,08 cm/px | **4,4–8,1 cm/px** |
| Sim mozaik (`iha_haritala`: MOZ_M 56 / MOZ_PX 1024, `_infer(..., imgsz=MOZ_PX)`) | kare 3,56 cm/px (30 m, hfov 1,3 rad, 1280 px) | **5,47 cm/px @ imgsz 1024** |
| Gerçek görev (30 m, IMX477 + 6 mm: sensör 6,29 mm → hfov **55,4°**, 1280 px; FDR: FOV ÖLÇÜLMEDİ) | **2,46 cm/px** | 6,15 cm/px @ imgsz 512 (`rpi_inference`) |

Yani mozaik GSD'si eğitim/gerçek göreve yakın (5,5 ↔ 4,4–8,1); **ölçek şüphesi mozaikte değil,
dokunun içeriğindeydi** (§2.1). Not: mozaik yolu çıkarımı **imgsz 1024** ile koşuyor; üretim kaydı ve
CONTRACTS §8 **512** (v36 1280'de çöker, 960'ta 9/12). TEŞHİS olarak aynı mozaik 512'de de koşuldu
(tablo, "imgsz512" sütunu) — karar zinciri değişmedi. Sim kamerası hfov 74,5° (gerçek ~55°): ayak
izi 45,6 m ↔ 31,5 m; kare kenarlarında perspektif (kutu yan yüzleri) gerçekten daha güçlü.

### 2.3 🔴 Yer kaydı kusuru (T212, ölçüldü ve düzeltildi)
`iha_ucus.UcusProfili`: roll yumuşatması (`(roll[k-1]+roll[k])/2`, 2 geçiş) bir önceki dönüş yayının
35° yatışını sonraki **tek segmentlik düz tarama bacağına** sızdırıyordu → tüm bacakta **roll = ±26,2°**
(ölçüm: `durum(t)` t=8…28, kabul edilen 15 karenin hepsi). 30 m'de 26,2° → nadir **14,8 m** yana;
`kare_kabul`/`mozaik_kur` yalnız z ve yaw'a bakar (poses.csv'de roll yok) → kareler kabul edilip
±15 m kaymış yerleşiyordu. Kanıt: tek kare mozaikte İB batı kenarı 748. sütun (beklenen 1006);
render kareyi doğrudan ölçünce (yatışsız poz) İB kenarı beklenen satırda (447 ↔ 446 @640 px) —
yani kamera/ölçek doğru, poz yanlıştı. Düzeltme: tarama segmentinde roll = 0 (dönüşlerde 35° kalır).
Nöbetçi: `tests/test_sim_mujoco_arena.py::TaramaSozlesmesi::test_mozaik_yer_kaydi_ib_bati_kenari`
ve `test_tarama_bacaginda_yatis_sifir`. **T212'nin K2 "kapsama 1,00" kapısı bu kusuru görmüyordu**
(kapsama ayak izi hesabı roll'suz); K3 0/15 kısmen bu kusurdur. → REVIEW_LOG kaydı mimara (bu görev
REVIEW_LOG'a dokunmaz).

### 2.4 Rota zinciri: HB pedi ve yol uçları (ölçüldü)
- V1 mozaikte açık yol şeridi %97–99 geçilebilir olduğu hâlde `KAPALI_DAR`: `koridor_adaylari` 3
  kapıyı buluyor (kapı genişlikleri 91–130 px ≈ 5–7 m), ama **her aday "geçilemez"**. Neden: HB
  (2×2 m ped, kırmızı H) model için zemin değil; HB tohumu **tek piksel** (`iha_haritala` →
  `_tohum_maskesi(hb, yaricap_m=0)`) ve ped etrafında dt < R_GEREKLI (1,10 m) → A* hedefi C-uzayında
  yok. HB tohumu 1,5 m diskte bile C-uzayı pikseli 0; 2,5 m'de 47–51 px; 3,5 m'de ~2500 px.
- Yol uçları: şerit KB/HB'de bitiyordu → uçta dt = 0 (KB tohumu da C-uzayı dışı). V1'de şerit
  uçların 3 m ötesine uzatıldı (`YOL_UZATMA_M`), KB dt 41 px oldu.
- HB tohumu 2,5 m ile 1-kolay: rota **doğru kapıdan** bulunuyor (darboğaz 1,31 m) ama
  `DOGRULAMA_BASARISIZ: HB ankoru eklenemedi` — zincir fiziksel HB noktasını rotaya ankor olarak
  ister ve o nokta C-uzayında değil. Bu, **render değil karar zinciri** meselesidir (CONTRACTS §7.3
  "varış = brandaya TEMAS" ile HB merkezine ankor arasındaki fark). Karar mimarın; burada yalnız
  seçenek (`--hb-yaricap`, varsayılan 0 = üretim) ve ölçüm.

## 3. Varyantlar (arena_mjcf `--varyant`; karar sonrası varsayılan **v1**, `--varyant taban` bayt-eş T212)
| varyant | ne |
|---|---|
| taban | T212 hâli (XML bayt-eş; T212 sha ile test kilidi) |
| **v1** | gerçek ölçekli dokular: yol şeridi **4,0 m** gerçek stabilize yol kırpması spline boyunca (s,d) eşlemesiyle, banket 0,9 m + toprak geçişi, zemin sürülmüş toprak (eğitimde arka plan); şerit uçları +3 m; kaynak kareler INTER_AREA ile doku ölçeğine indirgenir; asfalt şeridi `--yol-dokusu asfalt` |
| **v2** | v1 + alçak güneş (yükseklik ≈ 40°, castshadow, ambient 0,30→0,18, diffuse 0,58→0,85) → belirgin gölge/kontrast |
| **v3** | v2 + moloz kutuları yerine düzensiz yığın mesh'leri (8 ikosfer-türevi şekil, trimesh, SciPy yok; `mesh/moloz_yigin_*.stl`) |

Görseller: `k3b/ornekler/` (varyant başına harita 1 kolay/orta/zor mozaik + algı), `k3b/<varyant>/harita_*/`.

## 4. Sonuçlar (15 harita; ölçüm `k3b/<varyant>_15harita*.json`; tablo `k3b_ozet.py` çıktısı)

| varyant | rota bulunan | doğru etiket | rota durumları | HTAB geçilebilir (ort) | HTAB engel (ort) | açık yol şeridinde geçilebilir (ort) | kapalı yol şeridinde geçilebilir (ort) | yol dışı geçilebilir (ort) | TEŞHİS imgsz512 rota/doğru | TEŞHİS HB tohumu 2,5 m rota/doğru |
|---|---|---|---|---|---|---|---|---|---|---|
| taban | 0/15 | 0/15 | BELIRSIZ_TEK_KAPI, KAPALI_DAR, KAPI_YOK, MASKE_YOK | 0.0506 | 0.2849 | 0.1242 | 0.0962 | 0.0246 | 0/0 | 0/0 (BELIRSIZ_TEK_KAPI, KAPALI_DAR, KAPI_YOK, MASKE_YOK) |
| v1 | 3/15 | 3/15 | ACIK, KAPALI_DAR | 0.3441 | 0.1314 | 0.9727 | 0.7138 | 0.1454 | 4/4 | 3/3 (ACIK, DOGRULAMA_BASARISIZ, KAPALI_DAR) |
| v2 | 0/15 | 0/15 | KAPALI_DAR | 0.335 | 0.238 | 0.9679 | 0.6855 | 0.1413 | 2/2 | 0/0 (DOGRULAMA_BASARISIZ, KAPALI_DAR) |
| v3 | 0/15 | 0/15 | KAPALI_DAR | 0.3645 | 0.163 | 0.9744 | 0.7575 | 0.1612 | 4/4 | 0/0 (DOGRULAMA_BASARISIZ, KAPALI_DAR) |
| v1 · yerleşim D-441 (açık yol koridoru engelsiz) | 7/15 | 7/15 | ACIK, BELIRSIZ_COKLU, KAPALI_DAR | 0.3448 | 0.1239 | 0.9877 | 0.7088 | 0.1459 | 6/6 | 7/7 (ACIK, BELIRSIZ_COKLU, DOGRULAMA_BASARISIZ, KAPALI_DAR) |
| ek: v1_asfalt_3harita.json | 0/3 | 0/3 | KAPALI_DAR | | | 0.9439 | | | | hb=0.0 mozaik=son_yazar |
| ek: v1_15harita_nadir_yakin.json | 0/15 | 0/15 | BELIRSIZ_COKLU, BELIRSIZ_TEK_KAPI, KAPALI_DAR | | | 0.9863 | | | | hb=0.0 mozaik=nadir_yakin |
| ek: v1_zemin_toprak_3harita.json | 0/3 | 0/3 | BELIRSIZ_TEK_KAPI, KAPALI_DAR | | | 0.9837 | | | | hb=0.0 mozaik=son_yazar |

Okuma notları (ham veri `k3b/<varyant>_15harita.json`, `haritalar[].teshis`):
- ⚠ **Düzeltme (10 Eyl, §7):** "düşüşlerin tamamı KAPALI_DAR ve nedeni HB pedi" hükmü kısmen yanlış — arena yerleşimi chicane/tıkama plakalarını açık yol hattına sokuyordu (D-441); yerleşim düzeltilince v1 7/15 (satır "v1 · yerleşim D-441"). Aşağıdaki notlar eski yerleşimin kaydıdır.
- **Algı düzeldi, karar zinciri düzelmedi.** v1/v2/v3'te açık yol şeridi %90–100 geçilebilir
  (taban: %12), açık yol şeridinde engel ≤ %8, yol dışı zemin %14–16 (kapalı yollar da yol dokusu
  olduğundan %70–80 yeşil — beklenen; kapanmayı tıkama molozu sağlar). Üç kapı 15/15 haritada
  bulunuyor (`koridor_adaylari` n_kapi=3); düşüşlerin tamamı **KAPALI_DAR** ("hiçbir koridor gerekli
  açıklıkta geçilebilir değil") ve nedeni §2.4'teki **HB pedi** (tek piksel hedef tohumu C-uzayı
  dışı): HB tohumu 2,5 m ile ACIK'a dönen haritalar `DOGRULAMA_BASARISIZ: HB ankoru eklenemedi`
  ile düşüyor — zincir fiziksel HB noktasını ankor ister.
- **v1'in 3 başarısı (4 kolay, 4 zor, 5 kolay; 3/3 doğru, darboğaz 1,56–2,03 m):** bu haritalarda
  model HB pedini de zemin saydı (ped etrafı yeşil), tohum C-uzayına düştü. Yani başarı/başarısızlık
  ayrımı **yol algısı değil pedin etiketi**. 12 düşüşte yanlış şerit yok (0 yanlış etiket).
- **v2 (gölge) ve v3 (moloz mesh) v1'den iyi değil:** gölge HTAB engel oranını 0,13→0,24'e çıkardı
  (gölgeli moloz çevresi daha geniş kırmızı), açık yol algısı aynı kaldı; v3'te engel 0,16 ve açık
  yol 0,97 (v1 ile eş) ama 3 başarılı haritada ped bu kez etiketsiz kaldı → 0/15. Ped etiketi
  modelin kararsız olduğu bir ayrıntıdır; varyantlar arası 0↔3 farkı bu kararsızlıktan.
- **imgsz 512 TEŞHİS (üretim kaydı çözünürlüğü):** v1 4/15, v2 2/15, v3 4/15, taban 0/15 — 1024'e
  yakın ama farklı haritalarda; karar zinciri MOZ_PX=1024 kullanmaya devam eder (değiştirilmedi).
- **Mozaik `nadir_yakin` (TEŞHİS):** açık yol algısı 0,986 (en yüksek), engel 0,04–0,20 (en düşük),
  ama 0/15 (KAPALI_DAR + 2 BELİRSİZ) — perspektif azalınca HB pedi hiç yeşil olmadı.
- **Asfalt şeridi (3 harita):** açık yol 0,94, 0/3 KAPALI_DAR (aynı ped nedeni). **Sıkıştırılmış
  toprak zemin (3 harita):** açık yol 0,98 ama yol dışı zemin 0,12–0,21 ve engel 0,24–0,33;
  1 zor'da BELIRSIZ_TEK_KAPI (zemin de yol sayılınca kapılar birleşiyor) → sürülmüş toprak kalır.
- **Tur 1 ↔ tur 2:** `yol_koridor_uv` hızlandırıldıktan sonra (11,2 → 2,3 s/doku) v1/v2/v3 yeniden
  koşuldu; sayılar birebir aynı çıktı (3/15, 0/15, 0/15; `kosum_log.txt` ↔ `kosum2_log.txt`).

## 5. Karar

**Karar kuralı (görev tanımı):** en iyi varyant taban çizgisinden (0/15) iyiyse yeni varsayılan.
Ölçüm: taban 0/15 · **v1 3/15 (3/3 doğru)** · v2 0/15 · v3 0/15 → **v1 yeni VARSAYILAN**
(`arena_mjcf.VARYANT_VARSAYILAN = "v1"`; `--varyant taban` T212 XML'iyle bayt-eş kalır, test kilidi
`Varyantlar.test_varsayilan_v1_ve_taban_t212_sha_es` T212 sha'sına bakar). Testler güncellendi
(`tests/test_sim_mujoco_arena.py`: Varyantlar 8 test, yer kaydı 2 test; toplam 33 OK).

**H1-K3 kapısı:** 3/15 < 12/15 → **DÜŞTÜ** (eşik değişmedi). Sonuç FDR'ye "üretim modeli, sim
mozaik: 3/15; algı düzeltilmiş, karar zinciri HB pedinde takılıyor" olarak yazılır; ON_KAYIT §5.2
uyarınca İKA sürüş ölçümü YER GERÇEĞİ rotasıyla ayrıca koşulur.

**Mimara öneriler (karar mimarın, burada uygulanmadı):**
1. **HB hedef semantiği** (`iha_haritala.haritala(hb_yaricap_m)`, CONTRACTS §7.3 "brandaya TEMAS"):
   tek piksel HB merkezi yerine ped yarıçapı + R_GEREKLI diski ve `_ankoru_ekle`'de HB ankorunun
   "temas mesafesi içinde" kabulü. Ölçüm: 2,5 m diskte bile ankor kuralı düşürüyor; kural değişmeden
   ped etiketi kararsız kaldığı sürece K3 ≤ 3–4/15.
2. **T212 yer kaydı kusuru** REVIEW_LOG'a D-kaydı (K2 "kapsama 1,00" kapısı roll'u görmüyordu;
   `poses.csv` sözleşmesine roll/pitch eklenmesi ya da `kare_kabul`'ün profil yatışına bakması).
3. `iha_haritala` çıkarım çözünürlüğü (1024) ↔ kayıt/CONTRACTS §8 (512) ayrışması: karar mimarın
   (512'de v1 4/15). `nadir_yakin` birleştirme algıyı iyileştiriyor (engel ↓), üretim varsayılanı
   değiştirilmedi.
4. Gerçek arena zemini ile yol yüzeyi aynıysa (şartname fotoğrafı) sim abstraksiyonu iyimserdir;
   FDR'de "sentetik, ayrı yol dokusu" etiketiyle yazılmalı (§6).

## 6. Sınırlar
- Sim abstraksiyonu T212'den devralındı: yol yüzeyi zeminden **ayrı** dokudur. Şartname fotoğrafında
  (`data/arena_referans`) zemin ile güzergâh yüzeyi aynı sıkıştırılmış topraktır; güzergâhı moloz
  ayırır. K3 sim ölçümü bu yüzden "yol dokusu + moloz" ayrımını ölçer, gerçek arenanın "yalnız moloz"
  ayrımını değil (sentetik etiketi FDR'de kalır).
- Asfalt şeridi kaynağı düşük çözünürlüklü (≈10 cm/px, TAHMİN) tek otopark karesi.
- DJI hfov 69,7° varsayım (çapraz kontrol: yol genişliği 4,0 m); kaynak ölçekleri ±%5 belirsiz.
- Gerçek kamera FOV'u ölçülmedi (FDR A19); 55,4° hesap değeri.

## 7. Çürütücü düzeltmeleri (10 Eyl, tur 3) ve D-441 arena yerleşim kusuru

### 7.1 Kanıt bütünlüğü (çürütücü bulguları)
- **hb2.5 TEŞHİS geçişi üretim kanıtının üstüne yazmıştı.** `kosum.sh`/`kosum2.sh` hb2.5 geçişini üretim
  geçişiyle **aynı `--kok`**'a koşturuyordu; `iha_haritala.haritala` her geçişte `detection.json`'ı yazdığından
  4 haritanın dosyası (v1 1 kolay, v1/v2/v3 5 orta: JSON `KAPALI_DAR` ↔ dosya `DOGRULAMA_BASARISIZ`) ve
  3 ACIK haritanın `rota.json`/`route.txt`'si teşhis geçişinden kalmıştı. Düzeltme: `on_olcum_k3 --tarama-kaynak`
  (tarama kaynak kökten okunur, çıktılar ayrı köke yazılır; aynı kök reddedilir) ve `iha_haritala.haritala(girdi_dir)`;
  teşhis kökleri `k3b/<varyant>_hb2.5/`. `detection.json` artık `hb_yaricap_m` ve `birlestirme` alanlarını taşır
  (kanıt kendini etiketler). `kosum3.sh` ile taban/v1/v2/v3 üretim (hb 0) `detection.json`'ları **mevcut taramadan**
  (`--yeniden-tara` yok) yeniden üretildi; hb2.5 geçişleri ayrı köke koşuldu. Kontrol (`kosum3_log.txt`):
  `taban/v1/v2/v3_15harita.json` ve `*_hb2.5.json` — 8 dosyada özet eş, harita başına alan farkı 0 (rota_durum, model_yol, darboğaz, wp_n, trav/moloz px, teşhis oranları, imgsz512); üretim `detection.json` ↔ JSON çelişkisi 0/60 (önce 4), hb0/son_yazar etiketli 60/60; hb2.5 kökleri etiketli ve tutarlı 60/60.
- **"bayt-eş yeniden üretir" → "içerik-eş"** (başlık notu ve `.gitignore`): GPU render kareleri ~%50 bayt-eş,
  mozaik maks 8 seviye / %0,3 piksel fark; hüküm ve sayılar aynı (çürütücü ölçümü 10 Eyl).
- **v1 darboğaz aralığı 1,62–2,03 → 1,56–2,03 m** (JSON: 1,564 / 1,616 / 2,028).
- `on_olcum_k3` `kapi` alanı harita sayısına göre yazılır ("H1-K3 15 harita (eşik ≥ 12/15)" / "ÖN-ÖLÇÜM n harita");
  15 harita JSON'larında eski "ÖN-ÖLÇÜM (3 harita…)" metni düzeldi.

### 7.2 D-441 — açık yol koridoruna sokulan engeller (T213-B ölçümü) ve düzeltme
**Kusur.** T213-B yer gerçeği sürüşünde 45 koşumun 12'sinde temas, 10'unda açık yolun **merkez hattı** bir engelle
kesişiyordu (açıklık < 0,22 m). `arena_mjcf.yerlesim` kapalı yol tıkamalarını (t 0,30–0,80, u ±(lane_w/2+0,5), v ±1,8)
ve 1,4× büyütülmüş chicane plakalarını yolların yakınlaştığı yerde (KB/HB ucu, meander) açık yolun hattına sokuyordu;
bariyer (lane_w+1 m, t=0,12) de KB yakınında 0,84 m'ye kadar giriyordu. Ölçüm (seed 42, 15 harita, açık yol merkez
hattı ↔ engel OBB en küçük açıklık, `gorev_kosumu.rota_engel_acikligi` ile):

| harita | ÖNCE min (geom) | bariyer | tıkama | moloz | chicane | SONRA min (geom) |
|---|---|---|---|---|---|---|
| 1 kolay | 2,748 (chicane_1) | 4,017 | 4,190 | 3,157 | 2,748 | 2,748 (chicane_1) |
| 1 orta | **0,000 (chicane_3)** | 0,864 | 4,119 | 2,549 | 0,000 | 1,816 (chicane_2) |
| 1 zor | **0,602 (tikama_2_2_2)** | 0,907 | 0,602 | 2,180 | 0,868 | 1,789 (bariyer_2) |
| 2 kolay | 2,177 (chicane_1) | 3,626 | 4,721 | 2,849 | 2,177 | 2,177 (chicane_1) |
| 2 orta | **0,300 (tikama_2_2_6)** | 1,092 | 0,300 | 2,583 | 2,373 | 2,048 (bariyer_2) |
| 2 zor | 1,466 (bariyer_2) | 1,466 | 3,507 | 1,664 | 2,254 | 1,466 (bariyer_2) |
| 3 kolay | 2,811 (chicane_0) | 5,128 | 10,293 | 3,086 | 2,811 | 2,811 (chicane_0) |
| 3 orta | **0,000 (tikama_1_2_0)** | 3,195 | 0,000 | 2,720 | 0,000 | 1,531 (chicane_3) |
| 3 zor | **0,000 (tikama_2_2_1)** | 4,800 | 0,000 | 1,656 | 1,095 | 1,656 (moloz_66) |
| 4 kolay | **0,840 (bariyer_2)** | 0,840 | 8,052 | 2,555 | 2,394 | 2,145 (bariyer_2) |
| 4 orta | **0,263 (chicane_3)** | 2,847 | 5,318 | 2,682 | 0,263 | 1,494 (chicane_1) |
| 4 zor | 1,378 (moloz_53) | 1,598 | 5,818 | 1,378 | 2,169 | 1,530 (chicane_1) |
| 5 kolay | 1,625 (tikama_2_1_7) | 4,269 | 1,625 | 2,461 | 2,689 | 1,625 (tikama_2_1_7) |
| 5 orta | 1,510 (chicane_4) | 4,193 | 9,306 | 2,162 | 1,510 | 1,510 (chicane_4) |
| 5 zor | 1,881 (chicane_2) | 5,321 | 7,023 | 2,053 | 1,881 | 1,881 (chicane_2) |

ÖNCE 5/15 haritada açıklık < 0,5 m (3'ünde 0,0 = hat engelin içinden geçiyor); SONRA 0/15, en küçük 1,466 (2 zor bariyer_2) m.

**Kural (`arena_mjcf.ACIK_YOL_PAY_M`).** Açık yol merkez hattından ± pay içinde hiçbir engel geom'u (OBB) olamaz;
pay = `IKA_GENISLIK_M/2 + R_GEREKLI_M` = 0,35 + 1,10 = **1,45 m** (CONTRACTS §4; `costmap_path_finder` tek kaynak,
çıplak sabit yok). Uygulama, rng dizisini koruyacak biçimde (ek çekiliş **yalnız ret hâlinde**):
- bariyer: pay sağlanan ilk t (0,12 → 0,40, adım 0,01; 15 haritada en geç t=0,17);
- tıkama parçası ve dağınık moloz: OBB açıklığı ≥ pay olana dek yeniden örnekleme (≤ 80 deneme; 45 yerleşimde
  **hiç parça atlanmadı**, tıkama sayıları değişmedi);
- chicane: yeniden örnekleme; her 10 denemede bant 0,5 m dışa, ikinci yarıda karşı yan. (İlk deneme "normal boyunca
  itme" idi; plaka yolun **başka bir parçasının** üstüne taşınıyordu — 2 kolay s43 chicane_1 segment (−16,6, −11,7)'den
  (−1,3, −23,5)'e; ölçüldü ve vazgeçildi.)
- v3 mesh'leri tasarım kutusunun içinde normalize ([−0,5, 0,5]³ × ölçek) → kutu payı sağlanınca mesh de sağlar
  (yüklenen modelde köşe kabuğuyla ölçüldü: 1 kolay 2,761 ↔ kutu 2,747; 3 orta 1,548 ↔ 1,533).

**Yönerge maddesi.** `yonerge_kontrol` → `acik_yol_koridoru_engelsiz` (yüklenen modelde her engel geomunun XY dışbükey
kabuğu ↔ açık yol hattı; kutu için OBB ile eş, mesh için köşe kabuğu); `arena_*.json` kanıtlarına yazılır.

**Testler** (`tests/test_sim_mujoco_arena.py::AcikYolKoridoru`, 6 test; süit 39/39):
15 haritada açıklık ≥ 0,5 m **ve** ≥ pay−5 mm; 45 yerleşimde (tohum 42/43/44, T213-B'nin koşumları) tasarım açıklığı
≥ pay ve atlanan parça yok; **mutasyon:** pay=0 → T212 yerleşimi bayt-eş geri gelir (3 orta `tikama_1_2_0` hattın
üstünde, açıklık 0,0) ve madde düşer; pay sözleşmeden; v3 mesh kabuğu ≥ kutu; yapay kutuda kabuk/OBB uzaklığı 0,30 m.

**T212 sha kilidi yenilendi** (`arena_ozeti_15.json` + `harita_*/arena_*.json`, `--varyant taban`). İki neden, ikisi de
ölçüldü: (a) **T213-B** (master) `araclar.py`'ye teker `armature="0.0100"` ekledi → XML'de 4 satır; T212 sha'sı bu
birleşmeyle zaten kırılmıştı (`pay=0` XML'i T212 XML'inden yalnız bu 4 satırla ayrılır: `PAY0_SHA_1_KOLAY`);
(b) D-441 yerleşim düzeltmesi. Determinizm kalır: aynı seed → bayt-eş (`Determinizm` testleri). T212'nin özgün
1_kolay sha'sı (`941c7b84…`) testte sabit olarak tutulur; kilit listesinin ondan **farklı** olması ayrıca denetlenir.
Eski v1/taban/v2/v3 taramaları (eski yerleşim) **silinmedi**; `tarama_ozeti.json`'da `mjcf_kanonik_sha256` alanı yok =
eski yerleşim; yeni taramalar sha + `acik_yol_pay_m` taşır.

### 7.3 Yeni yerleşimle K3 (v1 varsayılan, 15 harita, üretim semantiği) — `k3b/v1_15harita_yerlesim_d441.json`
**Sonuç: rota bulunan 7/15, doğru etiket 7/15** (eski yerleşim v1: 3/15). Durumlar: ACIK 7, BELIRSIZ_COKLU 1, KAPALI_DAR 7. ACIK haritalar: 1 orta, 2 orta, 3 orta, 4 kolay, 4 orta, 4 zor, 5 kolay — eski yerleşimin 3'ü korundu (4 kolay, 4 zor, 5 kolay), 4 harita 1 orta (KAPALI_DAR), 2 orta (KAPALI_DAR), 3 orta (KAPALI_DAR), 4 orta (KAPALI_DAR) ACIK'a döndü; 7/7 doğru, yanlış etiket 0. Darboğaz 1,77–2,131 m. Algı: açık yol şeridinde geçilebilir ort 0,9877, yol dışı 0,1459 (eski v1: 0,9727 / 0,1454 — aynı). TEŞHİS imgsz512: 6/6; HB tohumu 2,5 m: 7/7 (ACIK, BELIRSIZ_COKLU, DOGRULAMA_BASARISIZ, KAPALI_DAR).

**Okuma.** Tek değişen yerleşimdir (model v36, karar zinciri, dokular, HB tohumu aynı; tarama yeniden render). 4 haritanın KAPALI_DAR → ACIK dönmesi, §4'teki "düşüşlerin tamamı HB pedi" hükmünün bu haritalar için **yerleşim kusuruyla karışık** olduğunu gösterir: chicane/tıkama plakaları açık yol hattına 1,45 m'den yakın olunca C-uzayı (R_GEREKLI 1,10 m) o noktada kesiliyor, zincir KAPALI_DAR diyordu. Harita başına ayrım (ped etiketi mi, darboğaz mı) ölçülmedi → açık kalan. Kalan 8 düşüş KAPALI_DAR/BELIRSIZ_COKLU; hb2.5 teşhisinde DOGRULAMA_BASARISIZ sürüyor (HB ankoru, §2.4). **H1-K3: 7/15 < 12/15 → DÜŞTÜ** (eşik değişmedi). FDR'ye yazılacak sayı budur; 3/15 eski yerleşimin kaydıdır.

Eşik değişmedi (≥ 12/15). Karar zinciri (HB pedi tek piksel tohum, §2.4) ve model aynı. Yerleşim düzeltmesi
İKA sürüş halkası (T213-B, D-441) için yapıldı; rota zincirine etkisi **beklenenden büyük ölçüldü** (3/15 → 7/15):
açık yol hattına sokulan plakalar mozaikte de C-uzayını kesiyordu. T213-B'nin 45 GT koşumu eski yerleşimle
ölçüldü (README_T213B, D-441); yeni yerleşimle yeniden koşulması ayrı görevdir (bu görevin kapsamı dışında; mimara).
Eski taramalar/ölçümler (`k3b/v1/`, `v1_15harita.json`) silinmedi: eski yerleşimin kaydıdır.
