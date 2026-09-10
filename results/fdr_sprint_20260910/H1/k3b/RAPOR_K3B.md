# T213-A · K3-b — Üretim modeli v36 render mozaikte yolu neden görmüyor? Teşhis + render varyantları

> **Kural:** ÖLÇÜLEMEDİ ≠ GEÇTİ. Eşik (H1-K3 doğru etiket ≥ 12/15) **değişmedi**. Üretim modeli v36
> (`sha 1d1caca6…`, kayıtla eş) **değişmedi**; sim'e özel eğitim/ince ayar **yok**. Bu belge
> ölçümden yazıldı; sayılar `k3b/*.json` (ölçüm) ve `simulation/mujoco/k3b_ozet.py` (tablo) kaynaklıdır.
> Koşum betikleri: `k3b/kosum.sh` (tur 1) ve `k3b/kosum2.sh` (tur 2, son kod), ham çıktılar `k3b/kosum_log.txt`,
> `k3b/kosum2_log.txt`. Tarih: 10 Eylül 2026 (10:3x–10:5x). Harita başına mozaik/algı JPG'leri git dışıdır
> (`kosum2.sh` bayt-eş yeniden üretir); `detection.json`/`poses.csv`/`meta.txt`/`tarama_ozeti.json` ve `ornekler/` depodadır.

## 0. Sonucun özeti (ayrıntı §3)

- **Teşhis tahmini (mimar): "model bandı yol değil boş zemin sayıyor" — DOĞRULANDI, ama tek neden değil.**
  Üç kanıtlı neden bulundu: (1) doku ölçeği/kaynak seçimi (taban zemini eğitimde *yol* etiketli bir
  kırpma, yol şeridi 5,8× büyütülmüş açık gri bant), (2) **T212 mozaik yer kaydı kusuru** — düz tarama
  bacaklarında İHA 26,2° yatık uçuyordu, nadir 14,8 m kayıyor; kare süzgeci roll'a bakmadığı için
  mozaik ±15 m kaymış/kesilmiş kuruluyordu (yer gerçeği şeritleriyle örtüşmüyordu), (3) rota
  zincirinin **HB pedi** semantiği: ped (2×2 m, kırmızı H) zemin sınıfı değil → tek piksel HB tohumu
  C-uzayında hiç geçilebilir olmuyor, her koridor "geçilemez".
- (2) düzeltildi (`iha_ucus.UcusProfili`: tarama segmentinde roll = 0; nöbetçi test). Bu düzeltme
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
| ek: v1_asfalt_3harita.json | 0/3 | 0/3 | KAPALI_DAR | | | 0.9439 | | | | hb=0.0 mozaik=son_yazar |
| ek: v1_15harita_nadir_yakin.json | 0/15 | 0/15 | BELIRSIZ_COKLU, BELIRSIZ_TEK_KAPI, KAPALI_DAR | | | 0.9863 | | | | hb=0.0 mozaik=nadir_yakin |
| ek: v1_zemin_toprak_3harita.json | 0/3 | 0/3 | BELIRSIZ_TEK_KAPI, KAPALI_DAR | | | 0.9837 | | | | hb=0.0 mozaik=son_yazar |

Okuma notları (ham veri `k3b/<varyant>_15harita.json`, `haritalar[].teshis`):
- **Algı düzeldi, karar zinciri düzelmedi.** v1/v2/v3'te açık yol şeridi %90–100 geçilebilir
  (taban: %12), açık yol şeridinde engel ≤ %8, yol dışı zemin %14–16 (kapalı yollar da yol dokusu
  olduğundan %70–80 yeşil — beklenen; kapanmayı tıkama molozu sağlar). Üç kapı 15/15 haritada
  bulunuyor (`koridor_adaylari` n_kapi=3); düşüşlerin tamamı **KAPALI_DAR** ("hiçbir koridor gerekli
  açıklıkta geçilebilir değil") ve nedeni §2.4'teki **HB pedi** (tek piksel hedef tohumu C-uzayı
  dışı): HB tohumu 2,5 m ile ACIK'a dönen haritalar `DOGRULAMA_BASARISIZ: HB ankoru eklenemedi`
  ile düşüyor — zincir fiziksel HB noktasını ankor ister.
- **v1'in 3 başarısı (4 kolay, 4 zor, 5 kolay; 3/3 doğru, darboğaz 1,62–2,03 m):** bu haritalarda
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
