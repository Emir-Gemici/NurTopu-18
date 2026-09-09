# NAVITAS `codes/` — Olgusal Modül Özeti (öğretici için)

> Kaynak: `/home/n4vitas/proje/navitas_tam/navitas/codes/` (2026-09-09 kopyası).
> Bütün satır numaraları bu kopyaya aittir. Her sayısal iddia `dosya:satır` ile verilir.
> Kodun docstring/yorumlarındaki **NEDEN** ve **D-###** (REVIEW_LOG kaydı) atıfları aynen aktarılmıştır.
> Emin olunamayan yerler **DOĞRULANAMADI** olarak işaretlidir.

---

## 0. Büyük resim: iki rota üreticisi, bir sözleşme

`codes/` altında **iki ayrı rota üretim yolu** vardır ve bunu bilmeden hiçbir şey anlaşılmaz:

| Yol | Fonksiyon | Ne için | Notu |
|---|---|---|---|
| **ÜRETİM** (Jetson/RPi'de sahada koşan) | `rpi_inference.analyze_path` (`rpi_inference.py:1352`) | kamera/video karesinden karar + telsize yayın | `test_rota_sentetik` "KOL 2" bunu sınar |
| **TANISAL** (costmap, 3-kapı mantığı) | `costmap_path_finder.rota_bul` (`costmap_path_finder.py:985`) | 3 güzergâhı kapı testiyle ayırt etme, A* + doğrulama | `test_rota_sentetik` "KOL 1" bunu sınar |

Her ikisi de eşiklerini, sebep kodlarını ve şerit numarası tanımını **tek kaynaktan**, `karar_sozlesmesi.py`'den okur (`karar_sozlesmesi.py:1-7`: *"Rota gecerlilik esikleri tum karar ve yayin yollarinda tek kaynaktan okunmazsa ayni guven degeri bir yerde OPEN_ROUTE, baska yerde NO_ROUTE uretebilir."*).

Projenin değişmez mimari ilkesi (CLAUDE.md madde 15, kodda defalarca anılır): **"Serbest alan OTORİTEDİR; nesne katmanı yalnız ÇIKARIR"** — serbest alanı büyüten hiçbir işlem eklenmez. Kod boyunca "madde 15" ibaresi bu ilkeye atıftır.

---

## 1. Modül modül: amaç, giriş/çıkış, ana fonksiyonlar, çağrı zinciri

### 1.1 `sinif_semasi.py` (106 satır) — sınıf kimlikleri sözleşmesi

**Amaç:** Eğitim sınıf id'leri ile costmap katman id'lerini **ayrı ad alanlarına** koymak ve çakışmamalarını import anında kanıtlamak.

**NEDEN (docstring `sinif_semasi.py:1-27`, aynen):** *"Sinif kimlikleri iki ayri ad alaninda yasiyor ve ikisi de sayi 2'yi kullaniyordu. Bu, olculmus ve KRITIK bir kusurdur (REVIEW_LOG D-17 oncesi S2, red team K3 pozitif kontrolu): `scripts/copy_paste_augmentation.py -> 2 = HEDEF`, `simulation/scripts/iha_haritala.py -> 2 = ARAC`. Uc sinifli (0,1,2) veriyle egitilmis bir model `iha_haritala` yoluna verilirse `engel_sinif_idler=(1, 2)` HEDEF'i engel sayar; IKA hedefe hicbir zaman ulasamaz ve gorev puani sifirlanir."*

Sabitler:
- `ZEMIN = 0`, `ENGEL = 1`, `HEDEF = 2` (`sinif_semasi.py:35-37`) — eğitim/model çıktısı ad alanı.
- `IKI_SINIF_ADLARI = {0: "traversable", 1: "blocked"}` (`:46`) — `data.yaml` için 2 sınıflı sözleşme.
- `ALGI_SINIF_IDLERI = (ZEMIN, ENGEL)` (`:50`) — `get_masks(..., sinif_idler=...)` bunu bekler.
- `KATMAN_ZEMIN = 0`, `KATMAN_MOLOZ = 1`, `KATMAN_ARAC = 10` (`:59-61`) — costmap ad alanı; **10'dan başlar** ki eğitim uzayı (0..9) ile çarpışmasın (`:56-58`).
- `COSTMAP_YOL_KATMANLARI = (KATMAN_ZEMIN,)` (`:64`), `COSTMAP_ENGEL_KATMANLARI = (KATMAN_MOLOZ, KATMAN_ARAC)` (`:68`).

Fonksiyonlar:
- `costmap_katmanlari(zemin, moloz, arac=None)` (`:71`) — `{0: zemin, 1: moloz, [10: arac]}` sözlüğü kurar; çağrı yerlerinin çıplak sayıyla sözlük kurmasını engeller. `arac=None` ise kanal **hiç eklenmez** (serbest alan yanlışlıkla büyümez, yalnızca ek çıkarma yapılmaz, `:75-77`).
- `dogrula()` (`:85`) — eğitim id kümesi ile costmap engel kümesinin (ENGEL hariç) kesişimi boş mu, HEDEF engel katmanında mı; değilse `AssertionError`. **Modül import edilirken çağrılır** (`:106`): *"Bu bir test degil, bir SOZLESME KAPISIDIR: birisi ileride KATMAN_ARAC'i 2 yaparsa import aninda patlar"* (`:88-89`).

Kural (`:27`): *"Bu modul disinda hicbir yerde ciplak sinif sayisi yazilmaz (CLAUDE.md madde 16)."*

⚠ Not: `rpi_inference.get_masks` varsayılanı `sinif_idler=(0, 1)` olarak **yazılıdır** (`rpi_inference.py:744`) — `sinif_semasi`'yi import etmez. Gerekçe `karar_sozlesmesi.py:978-983`'te: `sinif_semasi` Jetson saha paketinde YOKTUR, bu yüzden `BARIYER_ENGEL_SINIFI = 1` orada ayrıca tanımlanır ve eşitlik `tests/test_ince_bariyer.py` ile kilitlenir.

### 1.2 `model_registry.py` (252 satır) — kayıt defteri ve sha256 doğrulama

Ayrıntı §4'te.

### 1.3 `karar_sozlesmesi.py` (2246 satır) — tek-kaynak sabitler ve karar fonksiyonları

Ayrıntı §3'te. Büyük başlıklar: K-A/K-B eşikleri, ret sebep kodları, ölçek (mpp) sözleşmesi, zemin maskesi sağlamlık kapısı, Katman-2 klasik dedektörler (bariyer, beton şerit, HB), ölçek kâhini, beraberlik bandı/histerezis, `KararYumusatici`, şartname süre/alan sabitleri, MAVLink akış eşikleri.

### 1.4 `costmap_path_finder.py` (1408 satır) — serbest alan + koridor + A* + doğrulama

**Amaç (docstring `:1-19`):** Ekibin kendi çıktılarında rota park halindeki arabaların üstünden geçiyordu; kök neden mimari: `analyze_path` yalnız `masks[0]`'ı alıyor, engel sınıfı 4/5 çağrı yerinde hiç kullanılmıyordu; yalnız en büyük bağlı bileşen tutuluyordu (3 koridoru kıyaslamak imkânsız); waypoint'ler bant argmax'ıydı, süreklilik/açıklık denetimi yoktu.

**İki katman (`:21-36`):** KATMAN A (her karede) `serbest_alan()` + `koridor_adaylari()`; KATMAN B (~2 Hz) `astar()` + `yol_duzelt()` + `rota_dogrula()`. Ölçülen KATMAN A süreleri (`:28-29`): 384 px 12,6 ms · 640 px 32,6 ms · 1024 px 87,5 ms (sentetik); gerçek maske 640 px 24,5 ms · 1024 px 83,0 ms (D-162). *"~5 ms @384px" iddiası KALDIRILDI (T98 · D-169)* (`:25`).

**Kütüphane kısıtı (`:38-43`):** *"scipy YOK, scikit-image YOK, cv2.ximgproc YOK → medial_axis/skeletonize kullanilamaz. Yerine ACIKLIK AGIRLIKLI A* (heapq, stdlib)"*.

Fiziksel sabitler (`:74-110`):
| Sabit | Değer | Satır | Not |
|---|---|---|---|
| `IKA_GENISLIK_M` | 0.70 | :74 | sim SDF'ten; "TAHMIN: gercek arac olcusu FARKLI olabilir" |
| `MASKE_HATA_M` | 0.25 | :77 | proto-maske sınır belirsizliği |
| `TAKIP_HATA_M` | 0.50 | :79 | r_gerekli'nin en büyük tek terimi |
| `ALGI_PAYI_M` | 0.25 | :82 | yalnız ENGEL şişirilirken |
| `DOYUM_CARPANI_M` | 2.0 | :84 | A* ceza doyumu |
| `R_GEREKLI_M` | 0.35+0.25+0.50 = **1.10 m** | :87-88 | gerekli açıklık yarıçapı |
| `AC_M` / `KAPAT_M` | 0.30 / 0.40 | :93/:96 | KAPAT "en kucuk gercek engelden (~0.5 m) KUCUK olmak ZORUNDA" |
| `HEDEF_M_HUCRE` / `PLAN_M_HUCRE` | 0.15 / 0.45 | :101/:104 | costmap ve A* hücre boyu |
| `LAMBDA_ACIKLIK` / `US_ACIKLIK` | 3.0 / 2.0 | :106/:107 | en dar hücre 4× pahalı, karesel rampa — "AMPIRIK DEGIL" (`:1404-1405`) |
| `WP_ARALIK_M` / `MAKS_WP` | 2.0 / 64 | :109/:110 | |

Ana fonksiyonlar:
- `olcek_px(mpp, ...)` (`:120`) — metre sabitlerini piksele çevirir; `mpp=None` ise "ölçeksiz kip" (mpp=1.0 varsayılır; *"gorev ucusunda KULLANILMAZ"*, `:125-126`).
- `serbest_alan(maskeler, *, mpp, yol_sinif_idler=(0,), engel_sinif_idler=(1,), icerik)` (`:226`) — **sıralama kritik**: (1) ham engel birleşimi saklanır (`:253-256`); (2) engel `MORPH_CLOSE` + `dilate` ile `algi_payi_px` yarıçapında şişirilir (`:260-263`); (3) zemin `MORPH_OPEN`(ac_px) + `MORPH_CLOSE`(kapat_px) (`:270-272`); (4) `serbest = zemin AND NOT engel` **en son** (`:275`); (5) letterbox içerik kutusu dışı sıfırlanır — yalnız çıkarır (`:278-280`); (6) ada temizliği `connectedComponentsWithStats` alan filtresi, `min_ada_px` altı atılır (`:283-288`); (7) `dt_px = distanceTransform(serbest, DIST_L2, DIST_MASK_PRECISE)` (`:290`). Döner: `serbest, engel_ham, engel, zemin, dt_px, sekil, olcek, icerik`.
  NEDEN engel robot yarıçapı kadar şişirilmez (`:239-242`): *"dt_px >= r esigi, disk yaricapi r ile eroze etmeye MATEMATIKSEL OLARAK DENK ama TAM"*.
- `koridor_adaylari(dt_px, r_gerekli_px, baslangic, hedef, *, bant_oranlari=(0.30,0.40,0.50,0.60,0.70), bant_yukseklik_orani=0.06, icerik)` (`:370`) — `gecilebilir = dt_px >= r_gerekli_px` (`:409`); 5 yatay bantta `connectedComponentsWithStats` ile "kapı" sayar; en çok kapılı bant seçilir (`:431-450`); kapı kabul eşiği `genislik >= 2*r_gerekli_px` (`:429,:443`). Her kapı için yalnız o kapı açıkken `_bagli_mi` (`:361`, `connectedComponents`) ile başlangıç↔hedef bağlantısı test edilir (`:462-467`); darboğaz, `dt>=mid` eşiği üzerinde **6 iterasyonlu ikili arama** ile `[r, 4r]` aralığında bulunur (`:471-482`). Etiket **yalnız** `karar_sozlesmesi.serit_no()`'dan gelir (`:492-493`) — NEDEN (`:388-396`, T90 · D-145): iki otorite ölçüldü, 470 aday kapının 104'ü (%22,1) iki şemada farklı numara alıyordu.
- `_guven_hesapla(adaylar, r_gerekli_m, mpp)` (`:510`) — `guven = bolluk × ayirt`; `bolluk = clip((darbogaz_m − r_gerekli_m)/r_gerekli_m, 0, 1)`, `ayirt = clip((d1−d2)/d1, 0, 1)` (tek geçilebilir kapı varsa 1.0) (`:516-524`).
- `plan_izgarasi(dt_px, _, ds)` (`:530`) — **MIN-havuzlama** (`reshape(...).min`), muhafazakâr: hücre ancak içindeki tüm pikseller yeterliyse serbest (`:531-541`).
- `astar(gecilebilir_h, aciklik_m_h, hedef_h, baslangic_h, *, adim_m, r_gerekli_m, doyum_m, lam, us)` (`:559`) — 8 komşulu, çok-kaynaklı/çok-hedefli, `heapq` (`:598, :606, :632`). Maliyet: `adim_m × carpan × (1 + lam × u**us)`, `u = clip((doyum − açıklık)/(doyum − r_gerekli), 0, 1)` (`:576-580, :627`). Sezgisel: hedef maskesine `distanceTransform × adim_m` (`:582-584`). **Köşe kesme yasağı** (`:569-571, :624-626`): çapraz hamle ancak iki ortogonal komşu da serbestse — *"bir tekerlegi arabaya koyan hata sinifi tam budur"*.
- `_gorus_hatti(p1, p2, gecilebilir_tam)` (`:641`) — `cv2.line` LINE_8 ile segment pikselleri; hepsi serbest mi.
- `_bresenham_noktalari` (`:661`), `_maks_aralikla_bol` (`:683`) — waypoint aralığı azami `wp_aralik_px`; `maks_wp` yumuşak hedeftir, güvenlik için seyreltilmez (`:734-739`).
- `_polyline_asgari_aciklik` (`:743`) — rasterizasyon `_gorus_hatti` ile AYNI olmak zorunda; bağımsız denetim ölçtü: 200×200'de 4000 segmentin **621'i (%15,5)** farklı piksel kümesi üretiyordu (`:746-753`); erken çıkış olmadan 1860 düğümlü yolda 5,2 s (`:755-757`).
- `yol_duzelt(yol_px, gecilebilir_tam, *, wp_aralik_px, aci_esigi_derece=15.0, maks_wp, dt_px, kiris_bandi=BERABERLIK_BANDI)` (`:782`) — görüş-hattı string-pulling + açı/mesafe decimasyonu. `dt_px` verilirse **açıklık koruma**: kiriş, yerine geçtiği alt yoldan `(1 − 0.04)` oranından dar olamaz (`:791-792, :828-836`). NEDEN (D-154/156/157, `:794-807`): n=260'ta kayıp medyanı 4,00 px; 213/260 karede rota tek düz kirişe iniyordu; sabit eşik denendi kararlılığı bozdu (8→11/260), göreli eşik 8/260 (taban ile aynı). D-157 bulgusu (`:880-890`): aşama 2 korumayı siliyordu; artık düğüm düşürülmeden önce `onceki→sonraki` kirişi sınanır.
- `rota_dogrula(waypoints_px, engel_ham, dt_px_tam, r_gerekli_px, *, katı=False)` (`:898`) — **son güvenlik kapısı**: her waypoint (`:908-920`) ve tüm polyline (`cv2.polylines`, `:922-942`) HAM engele temas ve `dt < r_gerekli` için denetlenir; ihlal listesi döner, `katı=True` ise `RotaGuvenlikHatasi` (`:113`).
- `letterbox_suphesi` (`:955`), `rota_bul` (`:985`), `_rota_bul_cekirdek` (`:1008`) — §2/§3'te.
- `analyze_path_uyumlu` (`:1357`) — `rota_bul`u `analyze_path` dönüş şekline sarar (geriye uyum köprüsü).

Modül sonu **TAHMİNLER** (`:1394-1408`): TAKIP_HATA_M saf varsayım; IKA_GENISLIK_M SDF'ten; koridor genişlikleri şartnamede yok; LAMBDA/US ampirik değil; *"Jetson ~= 2x masaustu — 5 Agustos'ta olculecek"* (kodda ölçüm yok → **DOĞRULANAMADI**).

### 1.5 `rpi_inference.py` (2833 satır) — üretim çıkarım hattı

**Amaç:** Model yükleme (kayıt defteri doğrulamalı), kare ön-işleme, maske üretimi, Katman-2 dedektör ekleme, ölçek kâhini, `analyze_path` kararı, K-B eşikleme, histerezis, telsize yayın, görsel/harita çıktısı; `--fps/--image/--video/--camera` kipleri.

Önemli sabit ve fonksiyonlar:
- `MODEL_KAYIT_ZORUNLU = True` (`:162`); `INFER_SIZE_YEDEK = 512` (`:177`) yalnız defter okunamazsa; `INFER_SIZE = _baslangic_imgsz()` (`:206`) → `config/model_registry.json` profil `imgsz` (`_kayittan_imgsz`, `:185`). `cikarim_boyu()` (`:209`) defterden farklı istek gelirse stderr uyarısı.
- `CLASS_COLORS = {0: yeşil, 1: kırmızı}` (`:231`).
- `CanliOlcekSaglayici` (`:297`) — MAVLink bağıl irtifa okuyucusundan `kare_mpp(icerik_genisligi_px)` (`:358`) → `karar_sozlesmesi.mpp_irtifadan`. FOV ya da odaktan **tam biri** verilmeli (`:308-309`).
- `kare_olcek_kahini(mpp, canli_olcek, icerik, *, bgr, arac_modeli, senaryo, ...)` (`:453`) — katman 1 (telemetri/beyan) → katman 2 (arena, senaryo beyanla) → katman 3 (araç referansı, `arac_maskesi.arac_olcek_kenari`, `:423-450`).
- `_uretim_manifesti` (`:503`), `varsayilan_model_yolu` (`:535`) — model varsayılanı `jetson_derleme_manifest.json` → `asil_model_pt` (bu kopyada `"navitas_seg_v36_best.pt"`); çıplak ad yok (`:494-498`).
- `model_kayit_dogrula` (`:577`) ve `_turev_kayit_dogrula` (`:655`) — §4.
- `load_model` (`:701`) — uyumsuzlukta `RuntimeError` (fail-closed), `kayit_zorunlu=False` verilirse uyarı ile devam (`:720-735`); `YOLO(str(yol), task="segment")` (`:736`).
- `get_masks(results, h, w, min_conf=None, sinif_idler=(0,1), ince_beton_serit=None)` (`:744`) — §2.
- `_preprocess(img)` (`:1892`) — §2.
- `analyze_path` (`:1352`) → `_analyze_path_cekirdek` (`:1515`) veya `_analyze_path_yonelimli` (`:1426`, `rota_ekseni_derece` verilirse döndür→çekirdek→geri çevir; köşeler ENGEL kalır, geri çevrilen maske dönmemiş temizlikle kesiştirilir `:1455-1464`, dışarıda kalan waypoint → `KENAR_GUVENSIZ` `:1473-1482`).
- `_rota_kararini_esikle` (`:1779`) — K-B: `rota_guven_reddi` (`:1789`).
- `generate_ika_map` (`:1795`) — 512×512 tuvalde SOL/ORTA/SAG bölgeleri, waypoint'ler, HEDEF; çevrimdışı `--image` çıktısı.
- `DARK_L_MEAN = 80.0` (`:1865`), `is_dark` (`:1868`), `normalize_light` (`:1873`, gamma + CLAHE clipLimit 2.5, 8×8).
- `run_image` (`:1960`), `run_video` (`:2125`), `run_camera` (`:2298`), `kamera_kareleri` (`:2432`).
- CLI: `--conf` varsayılan **0.30** (`:2519`); `--camera` için `--mavlink` zorunlu ve statik `--mpp` reddedilir (`:2677-2680`); `--mavlink` için `--mav-sysid` ve `--fov|--odak` zorunlu (`:2689-2692`).
- Kontrollü durdurma: SIGTERM/SIGINT → bayrak (`_DURDURMA`, `:2070`); T204 (D-404 §8), `finally` ile `cap.release()`.
- Kamera düşen kare: `KAMERA_DUSEN_KARE_UST_SINIRI = 30` ardışık, bekleme `0.02 s` (`karar_sozlesmesi.py:362-363`), T143/D-284.
- `run_camera`'daki `cv2.flip(frame, 1)` **kaldırıldı** (D-349, `:2344-2355`): ölçüldü, açık yol 1/3 olan 16 karenin 15'i (%93,8) sol-sağ takas oluyordu. *"⚠ GERI KOYMAYIN."*

### 1.6 `arac_maskesi.py` (289 satır) — DOTA OBB araç kâhini (tek kaynak)

**NEDEN (`:1-18`):** COCO `yolov8m-seg.pt` aynı hava fotoğrafında **2** araç, DOTA `yolov8m-obb.pt` **93** araç buldu; COCO eşiği 0,35→0,02 indirildi, 18 karede sıfır kesişim — *"domain uyumsuzlugu"*. Sonuç: eğitim verisinde araçların ~%98'i ZEMİN öğretiliyordu (v16'yı moloza basmada %2,7→%31,6'ya çökerten hata sınıfı).

- `ARAC_SINIFLERI = {"small vehicle", "large vehicle"}` (`:28`) — **ad ile** eşleşir, id ile değil.
- `obb_arac_maskesi(bgr, arac_model, conf=0.25, imgsz=None)` (`:35`) — poligonları `cv2.fillPoly`; model None ise boş maske (serbest alanı büyütmez, `:43-44`).
- `MUKERRER_IOU = 0.5` (`:77`), `_mukerrerleri_ele` (`:87`) — sınıf-farkında NMS'in aynı aracı iki sınıfta sayması; ölçüldü drone 1137 kutuda 3 çift, kompozit 685'te 2 çift (%0,26).
- `arac_kisa_kenarlari` (`:110`) — OBB `xywhr` kısa kenarları (px).
- `ARAC_ASGARI_SAYI = 3` (`:184`) — T89/D-143: ≥3 araç bulunan kare: drone 20/20, kompozit 9/9, gemini 1/20, val 0/20, test 0/20 (`:172-176`). Yönelim saçılımı ayırıyordu ama "İLKESEL DEĞİL" diye kural yapılmadı (`:181-183`).
- `ARAC_OLCEK_IMGSZ = 640` (`:206`), `_olcek_cikarim_boyu` (`:209`) — kalibre edilen TAVAN, asla büyütme: `min(640, uzun kenar)`; ölçüldü doğal boyda mpp +%5,1, r_gerekli 0,75 px küçük = emniyetsiz yön (`:186-205`).
- `arac_olcek_kenari(bgr, model, conf, imgsz, asgari)` (`:233`) → `(medyan|None, sayı, sebep)` — ölçek katmanının **tek kaynağı**.
- `obb_modeli_mi` (`:262`), `coco_arac_maskesi` (`:277`, yalnız geriye uyum).

### 1.7 `test_rota_sentetik.py` (337 satır) — genel kapı 15/15

§7'de.

### 1.8 `test_rota_guvenlik.py` (565 satır) — gerçek görüntüde engelden kaçınma

**Amaç (`:1-20`):** Sentetik arenada araç yok; bu betik gerçek otopark drone görüntülerinde "rota arabaya değiyor mu" sorusunu ölçer. **İki kip:** (a) HAM: planlayıcıya yalnız navitas {0,1} maskeleri; (b) ENJEKTE: navitas {0,1} + araç kâhini maskesi engel olarak. Araç maskesi her iki kipte de yalnız **puanlamak** için hesaplanır (`:14-16`). (a) ihlal, (b) temiz → kusur ALGIDA; (b) de ihlal → kusur GEOMETRİDE.

- 3 koridor kapı mantığı burada **kullanılmaz** (`:22-26`); düşük seviye ilkeller doğrudan: `_rota_uret` (`:198`) = `serbest_alan` → `plan_izgarasi` → `astar` → `yol_duzelt` → `rota_dogrula`.
- Ölçek DOTA araç kısa ekseninden (`mpp_arac_maskesinden`, `costmap_path_finder.py:147`; 1,8 m binek) (`:290`).
- `bir_kare_isle` (`:274`) — letterbox 896 px (`:78, :430`), ihlal = rota-araç en küçük uzaklığı `< r_gerekli_px` (`:333-335`).
- `_ozet_cikis_kodu` (`:413`) — çıkış 0 yalnız `TAM_OLCUM` ve `ihlal_orani_ham > 0.10` ise (testin gücü olduğunu kanıtlar; `:522-523`). Geçme koşulu enjekte için "tam 0.0" (`:525`), çekimserlik `< 0.60` (`:528`).
- Varsayılan navitas modeli `models/navitas_seg_v20_best.pt` (`:425`) — üretim kaydındaki v36 **değil**.

### 1.9 `kamera_dogrula.py` (182 satır) — kamera/DroidCam doğrulama

**NEDEN (`:1-4`):** `rpi_inference.py` kamerayı `cv2.VideoCapture(0)` ile sabit açıyordu (bu kopyada `kamera_kaynagi_coz` ile artık parametrik, `rpi_inference.py:555`). Betik kaynağı parametrik alır, açılma süresi, sürücünün bildirdiği vs. **ölçülen** FPS/çözünürlük, kare düşme oranı (%5 uyarı, `:176`). `--zincir` ile gerçek algı zinciri: `zincir_durumu` (`:25`) = `_preprocess` → `get_masks` → `_maskeleri_icerige_kirp` → `rota_bul(..., icerik=icerik)["durum"]`. T135 notu (`:28-32`): `icerik` geçirilmezse 16:9 karede kaplama ≤ 0,5625, kenar ≤ 0,2815 — zemin kapısı hiç ateşlemez.

### 1.10 `train_seg.py` / `train_seg_v3.py` — eğitim reçeteleri

- `train_seg.py`: `yolov8n-seg.pt`, 150 epoch, `imgsz=512`, `batch=8`, `device="cpu"`, AdamW lr0 0.001, `degrees=45.0`, `flipud=0.5`, `copy_paste=0.15`, `patience=40` (`:26-27, :39-42, :48-49, :61-62, :78, :58`); sonra NCNN export (`:121`). Veri: RescueNet 2365 + FloodNet 798 = 3163 (`:5`).
- `train_seg_v3.py`: `yolov8s-seg.pt`, 200 epoch, `degrees=15.0`, `copy_paste=0.30`, `patience=60`, `cls_pw` ve `copy_paste_mode` parametreleri (`:36-37, :70, :87, :67, :97, :90`); gerekçeler `:6-21` (v2 blocked'ta 0,363→0,322 geriledi; n→s kapasite 3×). `per_class_report` (`:112`) sınıf bazlı mask mAP50; hedef ≥ 0,60 (`:178`).
- ⚠ Üretim modeli v36'nın gerçek reçetesi bu dosyalarda değil; `config/model_registry.json` `_egitim` notu: `139_gece_egitim.py`, taban v35, degrees 0, flipud 0, copy_paste 0, optimizer auto (lr0 sessizce 0,001667'ye ezildi), imgsz 512, 17 epoch, en iyi epoch 2. Bu betik `codes/` altında değil → **DOĞRULANAMADI** (yalnız kayıt notundan).

---

## 2. Uçtan uca boru hattı (üretim yolu, `run_camera`/`run_video`)

Adım adım, fonksiyon ve sabitlerle:

**A. Kare → letterbox tuval.** `_preprocess(img)` (`rpi_inference.py:1892`): önce `normalize_light` (yalnız LAB L ortalaması < 80 ise; `:1865, :1881`), sonra **kare PAD** (dolgu 114, `:1912`) — crop değil: *"1024x576 drone karesinde merkez crop genisligin %56'sini ATIYORDU → soldaki ve sagdaki guzergah yok oluyordu"* (`:1896-1900`). Model girişi `cv2.resize(tuval, (INFER_SIZE, INFER_SIZE))` (`:1915`, INFER_SIZE = defterden 512). Döner `(tuval, small, icerik=(x0,y0,w,h))`.

**B. Model çıkarımı.** `model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)` (`:2360` kamera, `:2210` video, `:1989` görsel); `conf` varsayılan 0.30 (`:2519`).

**C. Maske (`get_masks`, `:744`).** Her sınıf için `(h,w)` uint8: `r.masks.data[i]` → `cv2.resize` → `> 0.5` → `np.maximum` (`:769-772`). Sonra **KATMAN 2** engel ekleri: `_ince_bariyeri_ekle` (`:779`, `karar_sozlesmesi.ince_bariyer_maskesi`, `r.masks is None` dalında da çalışır `:776-778`); `_ince_beton_seridi_ekle` yalnız etkinse (`:785`; varsayılan **KAPALI**, `karar_sozlesmesi.py:1034`). Sonra `_maskeleri_icerige_kirp` (`:1919`) dolgu bölgesini sıfırlar.

**D. Ölçek (mpp).** `kare_olcek_kahini` (`:453`) → `{"mpp", "kaynak", "guven_carpani", "denenen"}`. Katman 1 telemetri (`mpp_irtifadan`, `karar_sozlesmesi.py:395`: FOV yolu `2·h·tan(FOV/2)/W`, odak yolu `h/f`; irtifa > 200 m fail-closed `:340, :420`; tazelik 0,50 s `:345`). Kâhin üretemezse `rota_olcek_reddi` (`:439`) → `OLCEK_YOK`. NEDEN (`:334-338`): `olcek_px(None)` sessizce `mpp=1.0` alıp `r_gerekli_px`'i 1,10 px yapıyordu — gerçek 12,7 px; gövde açıklığı ~11 kat küçülüyordu.

**E. Karar: `analyze_path(masks[0], icerik, engel_mask=masks.get(1), mpp, return_reason=True, olcek_kaynagi, goruntu=sq)`** (`:2376`). Çekirdek `_analyze_path_cekirdek` (`:1515`) sırayla:
1. `MASKE_YOK` — zemin 0 piksel (`:1535-1540`).
2. `ALAN_YETERSIZ` — içerik kutusu boş (`:1549-1555`).
3. **Zemin sağlamlık kapısı** `zemin_maskesi_reddi(trav, icerik)` (`:1562`; tanım `karar_sozlesmesi.py:712`) → `ZEMIN_MASKESI_SUPHELI`. HAM maske üzerinde ölçülür (`:1560-1561`).
4. Morfoloji: `MORPH_OPEN` çekirdek `max(3, w//60)` (`:1567`), `MORPH_CLOSE` çekirdek `kapama_cekirdegi_px(max(7, w//30), mpp)` (`:1573-1575`) — T188/D-326: kapama fiziksel tavan `KAPAMA_AZAMI_M = 0.25 m` ile sınırlı (`karar_sozlesmesi.py:1604-1626`); ölçüldü, duba sırası yalnız zemin deliği bırakınca kapama delikleri dolduruyor ve serit ACIK çıkıyordu (guven 1.00).
5. **Engel çıkarma en son** (`:1583-1591`): D-24, `MORPH_CLOSE` 7 px engelin %99'unu geri dolduruyordu.
6. `BILESEN_YOK` (`:1593-1599`); en büyük bağlı bileşen ana koridor (`:1603-1606`).
7. **K-A uç bant teması** (`:1615-1630`): aynı bileşen hem alt (başlangıç) hem üst (hedef) bandına yeterli genişlikte değmeli; bant yüksekliği `HEDEF_BANT_ORANI = 0.08` (`karar_sozlesmesi.py:13`), temas `≥ ceil(0.02 × icerik_w)` sütun (`:14, :290-297`) → `UC_BANT_TEMAS_YOK`.
8. Alan `≥ min_area_ratio(0.01) × icerik_w × icerik_h` (`:1633`, `:967`) → `ALAN_YETERSIZ`.
9. `dist = distanceTransform(clean, DIST_L2, 5)` (`:1648`); **C-uzayı** `gecilebilir = dist >= r_gerekli_px` (`:1664-1666`; `r_gerekli_px = R_GEREKLI_M/mpp`, `karar_sozlesmesi.py:495`); ölçek yoksa `gecilebilir = clean`, `olceksiz=True` (`:1668-1670`). Boşsa `GORUS_HATTI_KOPUK` (`:1672-1679`).
10. **HB hedefi** (`:1686-1702`): `goruntu` verildiğinde `hb_konumu(goruntu, mpp, sekil_esigi=HB_SEKIL_ESIGI if mpp else None)`; bulunamazsa `hedef_yok_reddi()` → `HEDEF_YOK` (T150/D-386 ile üretime bağlandı; ölçülen maliyet "SIFIR": şerit yayını 195/256 aynı, hedef 253/256 doğru pedde, `:2379-2385`).
11. **Tanık yol (witness)** `_bagli_koridor_yolu(gecilebilir, icerik, dist, min(k_open), hedef_tohumu)` (`:1704`; tanım `:1050`): `_bagli_mi` tam çözünürlükte bağlantı; sonra `_plan_adimlari` (`:993`) ile toplam hücre bütçesi `ROTA_PLAN_MAKS_HUCRE = 32_768` (`karar_sozlesmesi.py:27`) içinde adım(lar) seçilir; `plan_izgarasi` (MIN-havuz) → **`astar(..., r_gerekli_m=0.0, doyum_m=max(1, dt_plan.max()))`** (`:1105-1109`, `heapq` tabanlı `costmap_path_finder.astar`) → uç ankorları (`_tohum_hucresi_ankoru`, `:1036`) → `yol_duzelt(..., aci_esigi_derece=0.0, dt_px=dist)` (`:1133-1144`) → `_kenarlar_guvenli` (`:1156`). Başarısızsa `GORUS_HATTI_KOPUK` (`:1707-1711`).
12. `_rotayi_ornekle` (`:1712`, `:1167`): `n_waypoints` yalnız çıktı yoğunluğu; karara girmez (CONTRACTS SS6.4/5).
13. **Son kapı** `_kenarlar_guvenli(waypoints, gecilebilir, engel_mask)` (`:1715`; `:913`) → `KENAR_GUVENSIZ`.
14. **Şerit ve güven rotanın kendisinden** `_rota_serit_olcumu(kanonik_yol, dist, icerik)` (`:1730`; `:1211`): `serit_karari = rota_serit_karari(rota LINE_8 pikselleri)` (`karar_sozlesmesi.py:57`), `darbogaz_px` = rota üzerindeki en küçük dt.
15. **Koridor genişlik tavanı** `rota_koridor_genisligi_reddi(darbogaz_px, icerik_w)` (`:1757`; `karar_sozlesmesi.py:253`) → `KORIDOR_DEGIL` eğer darboğaz > `icerik_w/3 × 1.0` (`:232, :236, :242-250`).
16. `open_path = olcum["serit_karari"]` (`:1766`); `confidence = olcek_guveni_uygula(rota_darbogaz_guveni(darbogaz_px, icerik_w), olcek_kaynagi)` (`:1773-1774`): `rota_darbogaz_guveni = min(1, d / (icerik_w × 0.035))` (`karar_sozlesmesi.py:39, :101-116`) × kaynak çarpanı (1.00/0.70/0.86, `:1556-1560`).

**F. Öncelik ve eşikleme.** Yapısal ret ezilmez: `if olcek_reddi and karar_reddi is None: karar_reddi = olcek_reddi` (`:2390-2392`). Sonra `_rota_kararini_esikle` (`:2393`; `:1779`): `ROTA_GUVEN_ESIGI = 0.20` (`karar_sozlesmesi.py:22`) altı `DUSUK_GUVEN`.

**G. Yayın histerezisi.** `KararYumusatici().suz(open_path, karar_reddi)` (`:2399`; sınıf `karar_sozlesmesi.py:2125`, `KARAR_HISTEREZIS_KARE = 3` `:2122`): NO_ROUTE ve aynı şerit anında; farklı şerit 3 ardışık karede teyit ya da H5 tavanı (`esik−1` bastırma) sonrası.

**H. İKA'ya giden çıktı.** `_karari_yayinla(yayinci, open_path, path_conf, waypoints, kare_mpp, karar_reddi)` (`:2400`; `:285`) → `yayinci.karar(...)` (`:294`). Yayıncı `comms/iha_sender.yayinci_kur` (`:2758`) — **`codes/` dışında; içeriği bu özette DOĞRULANAMADI.** Kodda görünen sözleşme parçaları: her karede YA `OPEN_ROUTE` YA `NO_ROUTE`, sessizlik yok (`karar_sozlesmesi.py:132-138`, `KARAR_YOK_SEBEBI`); `ROTA_GEOMETRI` sebebi, piksel rota telsiz geometri sözleşmesine çevrilemezse (`:139-141`); `YAYIN_REF_XY = (0.0, 0.0)` — üretimde dünya çerçevesi yok, İKA saf öteleme (`:160-162`); heartbeat 1,0 s (`:145`), YKS tazelik 5,0 s (`:159`). Çevrimdışı `--image` kipinde ayrıca `generate_ika_map` (`:2047`) ve JSON payload `{"open_path","confidence","waypoints","timestamp"}` (`:2027-2032`).

---

## 3. `karar_sozlesmesi.py` — durumlar, ret nedenleri, şerit, güven kapıları, fail-closed

### 3.1 Rota durumları (`rota_bul`, tanısal yol)

`_rota_bul_cekirdek` (`costmap_path_finder.py:1012-1013`) `durum` alanı:
- `ACIK` (`:1165`) — kazanan geçilebilir kapı tek etiketli.
- `MASKE_YOK` / `KAPI_YOK` (`:1097-1100`, `koridor_adaylari` tanısından) — geçilebilir piksel yok / hiç kapı yok.
- `BELIRSIZ_TEK_KAPI` (`:1102-1106`) — 1 kapı, 3 güzergâh ayırt edilemedi.
- `KAPALI_DAR` / `KAPALI_KOPUK` (`:1111-1117`) — hiçbir kapı geçilebilir değil; alanlı bileşen varsa DAR, yoksa KOPUK. Ayrıca `ACIK` denip A* yol bulamazsa `KAPALI_DAR` "tutarsizlik" (`:1222-1226`).
- `BELIRSIZ_COKLU` (`:1119-1124`) — kapı sayısı ≠ 3; ve **T90 etiket çakışması** (`:1151-1160`): kazananın şerit numarasını başka bir geçilebilir kapı da taşıyorsa karar verilmez — NEDEN (`:1141-1145`): *"`road` YAYINLANAN ve PUANLANAN cevaptir... cekimserlik puan kaybettirir, YANLIS KARAR SIFIRLAR... Ayirt edilemeyen bir numarayi yayinlamak yazi-tura atmaktir."*
- `DOGRULAMA_BASARISIZ` (`:1273, :1281, :1330`) — ankor eklenemedi ya da `rota_dogrula` ihlal buldu; `waypoints_px = []`.
- Zemin kapısı `rota_bul`da da koşar (`:1058-1075`, T134/D-267): `durum = ZEMIN_MASKESI_SUPHELI` ya da `ALAN_YETERSIZ`.

### 3.2 Üretim yolu ret sebepleri (`ROTA_RET_SEBEPLERI`, `karar_sozlesmesi.py:164-176`)

`OLCEK_YOK`, `ZEMIN_MASKESI_SUPHELI`, `MASKE_YOK`, `BILESEN_YOK`, `UC_BANT_TEMAS_YOK`, `ALAN_YETERSIZ`, `GORUS_HATTI_KOPUK`, `KENAR_GUVENSIZ`, `DUSUK_GUVEN`, `KORIDOR_DEGIL` (T65/D-94), `HEDEF_YOK` (T72/D-105) (`:120-130`). Ayrıca yayın katmanı: `KARAR_YOK` (`:138`), `ROTA_GEOMETRI` (`:141`); GUI: `ALAN_IHLALI` (`:2004`), not (ret değil): `ASGARI_IRTIFA_ALTI` (`:462`).

### 3.3 Şerit numarası nasıl seçilir

- `serit_no(x, icerik_x0, icerik_w)` (`:42-54`): içerik kutusu genişliği üçe bölünür; `x < x0 + w/3 → 1`, `< x0 + 2w/3 → 2`, aksi `3`; `icerik_w <= 0 → 2`. Sınırlar **kare tuvalden değil letterbox İÇERİK kutusundan** (CONTRACTS SS8).
- `rota_serit_karari(rota_pikselleri, x0, w)` (`:57-98`): her rota pikseli bir şeride sayılır, **en çok piksel taşıyan şerit** kazanır; beraberlikte küçük indis (`:98`). NEDEN (T155 · D-296, `:63-79`): eski alan `darbogaz_serit` en dar **tek pikselin** şeridini yayınlıyordu ve 15 sahnenin 9'unda YANLIŞTI (6/15); o piksel 13/15 sahnede rotanın ucunda (güzergâhların birleştiği, şerit kimliğinin tanımsız olduğu yer). Örnek: harita 1 kolay 419/3/0 → yer gerçeği 1, darboğaz 2. Gövdeden karar 15/15.
- `rota_bul` tarafında etiket kapı merkezinden `serit_no` (`costmap_path_finder.py:492-493`); çapraz denetim `rota_serit_karari` ile (`:1343-1350`, `serit_uyumu`) — fail-closed DEĞİL, yalnız tanı.

### 3.4 Güven kapıları

- **K-A** (uç bant teması): `HEDEF_BANT_ORANI = 0.08`, `BANT_TEMAS_MIN_ORANI = 0.02` (`:12-14`). *"Guvenligin agirligi K-A'dadir"* (`:21`).
- **K-B** `ROTA_GUVEN_ESIGI = 0.20` (`:22`): 2026-08-10'da 0.50 → 0.20; gerçek 67 karede dağılım min 0,244 p50 0,307 max 0,352, std 0,030 — 0.50 %100 çekimserlik üretiyordu (D-37/D-38). *"K-B secici bir kapi DEGIL, taban koruyucusudur"*. `rota_guven_reddi` (`:300`): bool, NaN, sonsuz, [0,1] dışı → ret.
- Güven tanımı `ROTA_DARBOGAZ_TAM_ORANI = 0.035` (`:39`): rotanın en küçük dt / (icerik_w × 0.035), 1'e doyar. NEDEN (T32/D-41, `:29-38`): eski metrik tespit kötüleştikçe yükseliyor ve enjekte-kapı deneyinde 0,326/0,326/0,326 hiç değişmiyordu.
- **Zemin sağlamlık kapısı** (`:712-750`): `kaplama > ZEMIN_KAPLAMA_TAVANI (0.55, :583)` **VE** `kenar_dayanma > ZEMIN_KENAR_DAYANMA_TAVANI (0.40, :640)` → `ZEMIN_MASKESI_SUPHELI`. Kenar dayanma tek ayıran ölçüt (D-66 tablosu `:609-615`, mesru 0.000..0.339 vs çöküş 0.579..0.964). Kalibrasyon tarihi `:528-583` (0.55→0.67 T59, sonra v35 için 0.55 T142/D-286). *"🔴 ESIKLER MODELE BAGLIDIR... URETIM MODELI HER DEGISTIGINDE BU KALIBRASYON ZORUNLU ADIMDIR"* (`:572-574`). Geçersiz içerik kutusunda **kapı susmaz, reddeder** (`ALAN_YETERSIZ`, `:728-736`, D-71).
- **Koridor genişlik tavanı** (`:180-274`): darboğaz > bir şerit genişliği → `KORIDOR_DEGIL`. Ölçüm (`:214-222`): mesru 239 kare maks 0.280, kusurlu 10 karenin 5'i yakalanır, yanlış elenen 0/239. *"⚠ BU KISMI BIR COZUMDUR — gizlenmiyor"*.
- **Ölçek çapraz kontrolü** `OLCEK_CAPRAZ_BANDI = 0.25` (`:1490`), `olcek_capraz_kontrolu` (`:1493`): telemetri ve HB ölçeği bandı aşarsa `(None, "celiskili")` — ortalama alınmaz.
- **Beraberlik bandı** `BERABERLIK_BANDI = 0.04` (`:1900`, projenin ölçülmüş gürültü tabanı D-112), `beraber_adaylar` (`:1903`), `koridor_histerezisi` (`:1919`): önceki koridor artık geçilemezse **anında** bırakılır (`:1936-1937`).

### 3.5 "Fail-closed" mantığı — kodda nasıl görünür

Tekrarlayan kalıp: *ölçülemeyen ≠ geçti*. Örnekler:
- `mpp_irtifadan`: geçersiz/eksik/NaN/negatif/200 m üstü → `None`; *"'Tahmini olcek' DONMEZ"* (`:407-408`).
- `r_gerekli_piksel` None → *"kisit yok DEGIL, kisit UYGULANAMAZ"* (`:498-499`).
- `hb_konumu` (`:1358`): geçersiz `mpp`/`sekil_esigi` → None; şekil kapısı ölçeksiz açılmaz (`:1400-1405`, D-383); *"OLCULEMEDI != GECTI: puani uretilemeyen aday yarisamaz"* (`:1445`).
- `zemin_maskesi_reddi` bozuk kutuda reddeder (`:729-736`).
- `KararYumusatici.suz`: NO_ROUTE **asla** geciktirilmez/bastırılmaz (`:2159-2165`).
- `rota_koridor_genisligi_reddi`: ölçülemeyen darboğaz reddi tetiklemez — yalnız pozitif kanıt üzerine (`:256-259`); bu kapı bilinçli olarak "yalnız reddeder".
- İstisna: `asgari_irtifa_notu` (`:465`) **ret değil not** — kalkış/iniş karelerinde reddetmek zararlı olurdu (`:472-477`).

### 3.6 Katman-2 klasik dedektörler (yalnız ENGEL katmanına EKLER)

- `ince_bariyer_maskesi(bgr)` (`:894`): LAB a* > `BARIYER_KROMA_ESIGI = 25` (`:845`), uzun-ince (en/boy > 4.0, `:846`), T184'te açıdan bağımsız (12 açıda çizgi çekirdekleriyle kapama, `:959`). Ölçüm (`:906-910`): T184 öncesi 90°/270°'de **tamamen kör**. *"Kod yorumu bir OLCUM DEGIL, bir olcumun TARIHIDIR"* (`:770`): D-92'deki "model %0,0 görüyor" bayat; v36 aynı karede %99,9 ama 60°/120°/135°'de %0,0 (`:782-787`) çünkü v36 döndürme artırımı görmedi (`degrees: 0.0`, `:789-791`).
- `ince_beton_serit_maskesi` (`:1046`): L ≥ 225, kroma ≤ 20, genişlik 3–14 px @512, uzunluk ≥ 40 px @512 (`:1036-1043`); **varsayılan kapalı** (`:1034`), benimseme kuralı önceden yazılı (`:1029-1033`).
- `hb_maskesi` (`:1202`) / `hb_konumu` (`:1358`): kırmızı + KARE (en/boy 1/1.6..1.6, `:1155`) + fiziksel ölçek bandı `HB_OLCEK_BANDI = (0.883, 1.258)` (`:1168`, n=260 pedden türetildi) + şekil IoU `HB_SEKIL_ESIGI = 0.17656308851224103` (`:1267`; "TAM HASSASIYETLE yazilidir"). Bariyer ile tümleyen: bariyer dediği piksel HB olamaz (`:1187-1198`).

---

## 4. `model_registry.py` — kayıt defteri, sha256, türevler, profil, fail-closed

**Kayıt defteri:** `config/model_registry.json` (`model_registry.py:24`), Jetson aynası `jetson_paket/config/model_registry.json` (`:25`). Bu kopyadaki içerik: `schema_version 1`, `default_profile: "competition"`, `model_id: "navitas-seg-v36-512"`, `path: models/navitas_seg_v36_best.pt`, `backend: pytorch`, `imgsz: 512`, `sha256: 1d1caca6…6911`, `classes {0: traversable, 1: blocked}`, `turevler`: `navitas_seg_v36_best_512_fp16.engine` (tensorrt, sha256 gerçek `bb9bd868…`), `navitas_seg_v36_best.onnx` ve `…_512_fp16.onnx` (aynı sha256 `f4c9f5fe…`). ⚠ Bu çalışma kopyasında `models/` altında yalnız v2/v3/v4 `.pt` listelendi; v36 `.pt` dosyasının varlığı burada **DOĞRULANAMADI** (Jetson paketinde ayrı olabilir).

**Fonksiyonlar:**
- `load_registry(path)` (`:39`): JSON okunamaz ya da `schema_version != 1` / `profiles` dict değil → `ModelRegistryError`.
- `_sha256(path)` (`:50`): 1 MB bloklarla `hashlib.sha256`.
- `sha256_dogrulanmis_mi(ozet)` (`:58`): yer tutucu `"DERLENINCE_YAZILIR"` (`karar_sozlesmesi.py:378`), 64 hex değilse → False.
- `turev_dogrula(profil, dosya, *, calisan_imgsz, ozet_hesapla)` (`:71`) — sıralı RED durumları: `ESLESMIYOR` (kayıtsız ad, `:84`) · `TUREV KAYNAGI ESLESMIYOR` (`kaynak`/`kaynak_sha256` profilin `.pt`'siyle uyuşmuyor = yetim, `:92`) · `TUREV SHA YER TUTUCU` (`:95`) · `IMGSZ ESLESMIYOR` (`:100`) · `turev dosyasi yok` (`:107`) · `TUREV SHA ESLESMIYOR` (`:112`) · `turev_eslesti` (`:114`).
- `resolve_model(profile, *, registry_path, verify, turev, calisan_imgsz)` (`:118`): türev verilirse `turev_dogrula`, red ise `ModelRegistryError` (`:134-135`); `.pt` yolunda artefakt yok (`:142`), `imgsz <= 0` (`:144`), sha256 uyuşmazlığı (`:146-151`) → hata.
- `turev_kaydet(dosya, *, registry_path, profile, kaynak_pt, ayna_yollari)` (`:176`): `--kaynak-pt` ZORUNLU (`:188-191`); uzantı `.engine/.onnx` (`:31, :195`); türev adı profilde **zaten kayıtlı** olmalı — *"bu CLI yabanci dosyayi soya SOKMAZ"* (`:201-204`); kaynak `.pt` özeti profil sha256 ile birebir (`:208-211`); defter `indent=1` ile bayt-eş yazılır ve aynaya kopyalanır (`_defteri_yaz`, `:166`; `:219-220`).
- CLI `_cli` (`:225`): `--turev-kaydet DOSYA --kaynak-pt PT [--defter] [--profil] [--ayna-yok]`; hata → `RED: …`, çıkış 1.

**Üretimde kullanımı:** `rpi_inference.model_kayit_dogrula` (`:577`) aynı kuralları saha paketinde tekrar uygular (`model_registry` orada yok, `:657-658`): ad + `imgsz` kıyası; ad uymazsa `_turev_kayit_dogrula` (`:655`). `load_model` (`:701`) uyumsuzsa `RuntimeError` — *"Sahada hangi agirligin uctugunu bilmeden devam etmek yasaktir"* (`:730-731`); yalnız `--kayit-dogrulamasiz` ile uyarıya düşer (`:2510-2513`).

---

## 5. `sinif_semasi.py` / CONTRACTS bağı — neden çıplak sabit yasak

- CLAUDE.md madde 16: *"Sözleşmeler CONTRACTS.md'den okunur. Sınıf id, mesaj tipi ve koordinat çerçevesi için kodda çıplak sabit yazılmaz."* `CONTRACTS.md` bu özet için okunmadı → içerik **DOĞRULANAMADI**; kodda atıflar: SS2 (monotonluk), SS5 (ölçek), SS6.3 (K-A/K-B), SS6.4 (sebep kodları, hücre bütçesi), SS6.5 (yayın), SS8 (oranlar, çözünürlük bağımsızlığı), SS11 (halkalar), SS12 (doğrulama kümesi).
- Somut zararlar kodda yazılı: id 2 çakışması (`sinif_semasi.py:1-10`); `INFER_SIZE = 512` çıplak sabiti defterle hiç kıyaslanmıyordu (`rpi_inference.py:167-170`, D-116/5); GUI'de 300 m üç yerde çıplak (`karar_sozlesmesi.py:1999-2003`); kapama çekirdeği `w//30` metrik değildi (`:1577-1580`).
- Sınıf id'leri: eğitim `{0: traversable, 1: blocked}` (`sinif_semasi.py:46`; kayıt defteri `classes` ile aynı); costmap engel kanalları `(1, 10)` (`:68`); `serbest_alan` sözlük anahtarı varlığına bakar (`if c in maskeler`, `costmap_path_finder.py:255, :268`) — sayının değeri değil çakışmaması önemli (`sinif_semasi.py:19-20`).
- `test_sinif_semasi.py` (S2 kapısı): 3 sınıflı çıktı costmap'e verildiğinde HEDEF bölgesi serbest alanda 1 kalmalı (`:8-10`).

---

## 6. Kod kuralı: yalnız OpenCV/NumPy/heapq (SciPy yasak) — iz

- CLAUDE.md madde 4: *"sadece OpenCV, NumPy ve saf Python heapq kullan. SciPy / scikit-image YASAKTIR."*
- `grep -i "scipy|skimage|scikit|ximgproc" codes/*.py` → yalnız `costmap_path_finder.py:38-39` docstring'inde "scipy YOK, scikit-image YOK, cv2.ximgproc YOK" — **import yok**.
- `import heapq` `costmap_path_finder.py:51`; kullanım `:598, :606, :632` (A* açık listesi).
- `rpi_inference.py:39`: *"costmap_path_finder yalniz cv2/numpy/heapq kullanir, dairesel import yoktur."*
- `kamera_dogrula.py:12`: *"Yalniz OpenCV + NumPy kullanir (anayasa madde 4)."*
- `karar_sozlesmesi.py:2006-2009`: eşdikdörtgen izdüşüm `DUNYA_YARICAPI_M = 6_378_137.0` ile — *"SciPy / pyproj GEREKMEZ (anayasa madde 4)"*.
- Yerine konan teknikler: medial axis yerine açıklık ağırlıklı A* (`costmap_path_finder.py:38-43`); `cv2.erode` yerine `numpy reshape-min` havuzlama (çift boyutlu çekirdeğin çapası belirsiz, `:533-534`); Bresenham elde yazıldı ama güvenlik ölçümü `cv2.line` ile (`:746-753`).
- `ultralytics` (YOLO) yalnız model çıkarımı/eğitimi için (`requirements_rpi.txt`: ultralytics, opencv-python, numpy).

---

## 7. `test_rota_sentetik.py` "genel kapı 15/15" tam olarak neyi ölçüyor

**Sahne üretimi** (`sahne_uret`, `:83`): `simulation/scripts/arena.harita(id, senaryo)` → 3 yol poligonu + KB + HB + gizli `open`. 5 harita (`arena.HARITA_N = 5`, `arena.py:31`) × 3 senaryo (`SCENARIOS = ("kolay","orta","zor")`, `arena.py:30`) = **15 belirlenimci sahne** (`:4-6`). Şerit genişliği `lane_w` 6.0/5.0/4.0 m (`world_generator.py:36-38`). Rasterizasyon: `MPP = 0.10` m/px, 50 m → `N = 500` px tuval (`:51-53`). Zemin: yollar `cv2.polylines` kalınlık `lane_w/MPP` (`:90-93`). Engel: kapalı iki yolun %40'ına yola dik, `lane_w + 1.0` m genişlik, 1.5 m boy bariyer (`:100-127`); bozulma taraması için CRC tohumlu deterministik silme (`:96-99`). KB/HB 1.5 m disk (`:131-132`). Maskeler **kusursuzdur**: *"kusursuz maskede hata varsa bu MANTIK hatasidir, algi (model) hatasi degil"* (`:9-10`).

**KOL 1 — tanısal `rota_bul`** (`main`, `:251-279`): `rota_bul({0: zemin, 1: engel}, mpp=0.10, baslangic, hedef, plan=True)` (`:254`). Bir sahne "OK" sayılır ancak **hepsi** doğruysa (`:265-273`): `durum == "ACIK"`, ≥2 waypoint, `ihlaller` boş, en uzun adım ≤ `wp_aralik_px + 1` (20 px), ilk waypoint == KB ankoru, son waypoint == HB ankoru (`_tohum_merkezi`, `:75`), **ve** `yol_no == H["open"]`. Şart: **15/15** (`kapi_karari`, `:197`). Çıktı satırı `"SONUC: n/n dogru"` ve `"[OK] TUM DETERMINISTIK SAHNELER GECTI"` başka betikler okuduğu için aynen korunur (`:28-30`).

**KOL 2 — üretim `analyze_path`** (`uretim_yolu_kolu`, `:137`): aynı 15 sahne, `analyze_path(zemin, icerik=None, engel_mask=engel, mpp=MPP, return_reason=True, return_olcum=True)` (`:161-163`); başlangıç/hedef maskeleri **verilmez** — üretim yolu uç bantlarını maskeden türetir (`:158-160`). Ölçülen: `rota_var` (ret yok, yol var, ≥2 wp) ve `serit_ok` (`rota_var` ve yayınlanan `road == H["open"]`) (`:164, :174`). Eşik `URETIM_KAPI_ESIGI = 14` (`:59`; ON_KAYIT SS18-B, "SONUCA GORE DEGISTIRILMEZ", ölçülen taban 15/15). NEDEN (`:16-27`, T156): kapı 2026-08-26'ya kadar yalnız `rota_bul`u zorluyordu; üretim yolu 15 sahnenin 9'unda yanlış şerit yayınlarken kapı 15/15 yeşil yanıyordu (T155/D-296).

**Çıkış kodu** (`kapi_karari`, `:188-201`): `kol1_dogru == kol1_toplam` **VE** `uretim_rota >= 14` **VE** `uretim_serit >= 14` → 0; aksi 1. Ekran: `"GENEL KAPI (madde 14): GECTI/DUSTU — kol1 n/15 · kol2 serit n/15"` (`:294-295`).

**Ne ölçmez:** model doğruluğu, gerçek arena, araç engeli (`test_rota_guvenlik.py:3-4`). `--bozulma` (`:314-331`) bariyer piksellerini %100→%0 silerek kararın nerede döndüğünü ölçer: *"modelin bariyeri gormesi gereken GERCEK recall esigi budur — varsayim degil, olcum"*.

---

## 8. Muhtemel 10 jüri sorusu ve kodla desteklenen kısa cevaplar

1. **"Açık yolu nasıl seçiyorsunuz; model mi karar veriyor?"**
   Hayır. Model yalnız `traversable/blocked` maskesi verir (`get_masks`, `rpi_inference.py:744`). Karar, maskeden türetilen distance-transform üzerinde geometrik kapılarla verilir: K-A uç bant teması (`:1615`), C-uzayı `dist >= r_gerekli_px` (`:1666`), A* tanık yolu (`_bagli_koridor_yolu`, `:1050`), son kenar denetimi (`:1715`). Şerit numarası rotanın gövdesindeki piksel çoğunluğundan (`rota_serit_karari`, `karar_sozlesmesi.py:57`).

2. **"Emin değilseniz ne yapıyorsunuz?"**
   NO_ROUTE yayınlıyoruz, sessiz kalmıyoruz (`KARAR_YOK_SEBEBI`, `karar_sozlesmesi.py:132-138`). Gerekçe kodda: *"cekimserlik puan kaybettirir, YANLIS KARAR SIFIRLAR"* (`costmap_path_finder.py:1143-1144`). Ret sebepleri `ROTA_RET_SEBEPLERI` (`karar_sozlesmesi.py:164`).

3. **"İKA'nın sığacağını nereden biliyorsunuz?"**
   `R_GEREKLI_M = 0.35 + 0.25 + 0.50 = 1.10 m` (`costmap_path_finder.py:87-88`: yarı genişlik + maske hatası + takip hatası). `r_gerekli_px = 1.10 / mpp` (`karar_sozlesmesi.py:495`). Rota üzerindeki her piksel bu açıklığı sağlamalı; `rota_dogrula` (`costmap_path_finder.py:898`) HAM engel maskesine karşı yeniden denetler.

4. **"Ölçek (metre/piksel) yoksa?"**
   Rota üretilmez: `rota_olcek_reddi` → `OLCEK_YOK` (`karar_sozlesmesi.py:439-459`). Eskiden sessiz `mpp=1.0` varsayımı gövde açıklığını ~11 kat küçültüyordu (`:334-338`). Üç katmanlı kâhin (`olcek_kahini`, `:1683`): telemetri ×1.00, arena sınırı ×0.70, araç referansı ×0.86 (`:1556-1560`); kaynak karar nesnesine yazılır.

5. **"Model bariyeri görmezse?"**
   Katman-2 klasik dedektör engel katmanına **ekler** (`_ince_bariyeri_ekle`, `rpi_inference.py:831`; `ince_bariyer_maskesi`, `karar_sozlesmesi.py:894`). Serbest alan `zemin AND NOT engel` olduğu için yalnız küçülür (madde 15). Ölçüldü: v36 döndürülmüş karede 60°/120°/135°'de %0,0 görüyor (`:782-787`) — bu yüzden dedektör 12 açıda çalışır (`:959`).

6. **"Yanlış modelle uçma riski?"**
   `load_model` kayıt defteriyle ad + imgsz + (türevde) sha256 kıyaslar; uyumsuzlukta `RuntimeError` (`rpi_inference.py:701-735`). Türevler (`.engine/.onnx`) kaynak `.pt` sha256'sına bağlı; yer tutucu = RED (`model_registry.py:71-115`). Yalnız `--kayit-dogrulamasiz` bayrağıyla gevşer (`:2510`).

7. **"Sol/sağ karışır mı?"**
   Şerit sınırları letterbox içerik kutusundan (`serit_no`, `karar_sozlesmesi.py:42-54`). Kamera aynalaması D-349'da kaldırıldı: ölçüldü, 16 karenin 15'i (%93,8) takas oluyordu (`rpi_inference.py:2344-2355`). Letterbox crop değil pad: crop 1024×576'da genişliğin %56'sını atıyordu (`:1896-1900`).

8. **"Kararlar kareler arasında titrer mi?"**
   `KararYumusatici` (`karar_sozlesmesi.py:2125`): farklı şerit 3 ardışık karede teyit (`KARAR_HISTEREZIS_KARE = 3`, `:2122`); NO_ROUTE anında geçer (`:2159-2165`); H5 tavanı ile yayın bayatlamaz (`:2176-2177`). Ölçülen gürültü tabanı `BERABERLIK_BANDI = 0.04` (`:1900`).

9. **"Yazılımı nasıl test ediyorsunuz?"**
   Genel kapı `test_rota_sentetik.py`: 15 belirlenimci sahne, iki kol (`rota_bul` 15/15 zorunlu; `analyze_path` rota ≥14/15 ve şerit ≥14/15) (`:188-201`). Gerçek görüntüde araç kaçınma `test_rota_guvenlik.py` (ham/enjekte iki kip). Sınıf-id sözleşmesi `test_sinif_semasi.py`. `sinif_semasi.dogrula()` import anında koşar (`sinif_semasi.py:106`).

10. **"Neden SciPy/scikit-image kullanmadınız?"**
    Anayasa madde 4 ve Jetson paketinin sadeliği; kodda import yok (grep). Medial-axis yerine açıklık ağırlıklı A* (`costmap_path_finder.py:38-43`, `astar` `:559`, `heapq` `:51`); erozyon yerine `dt >= r` eşiği (`:239-242`); `reshape-min` havuzlama (`:531-541`).

---

## 9. Doğrulanamayan / dikkat gerektiren noktalar (özet)

- `comms/iha_sender`, `comms/inis_kaniti`, `CONTRACTS.md`, `simulation/scripts/arena.py` gövdesi bu özette okunmadı; yalnız `codes/` içindeki atıflar aktarıldı.
- Bu kopyada `models/navitas_seg_v36_best.pt` listede görünmedi; kayıt defteri onu bekliyor.
- Kod yorumlarındaki bazı ölçümler **tarihlidir** (kodun kendi uyarısı: `karar_sozlesmesi.py:766-770`); jüri önünde "ölçüldü" derken tarih/sürüm belirtilmeli.
- `costmap_path_finder.py:1394-1408` TAHMİNLER listesi (TAKIP_HATA_M, IKA_GENISLIK_M, LAMBDA/US, Jetson 2×) kodda "ölçülmemiş" olarak işaretlidir.
