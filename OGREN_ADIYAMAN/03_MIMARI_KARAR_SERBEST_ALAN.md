# 03 · MİMARİ KARAR — "Serbest alan otoritedir, nesne katmanı yalnızca çıkarır" (3–4 Ağustos 2026)

> Kaynaklar: `RESEARCH_NOTES.md` (A/B/C değerlendirmesi, ölçümlerle) · `ARCHITECT_PLAN.md` §4–§6 (veri akışı, K-1…K-8 kararları)
> · `CONTRACTS.md` §2 (monotonluk sözleşmesi) · `codes/sinif_semasi.py` · `codes/costmap_path_finder.py:212-213`.
> Bu dosya projenin **en çok soru gelecek** kararını anlatır: neden çok-sınıflı nesne tespiti değil, serbest alan segmentasyonu.

---

## Seviye 1 — Bir cümle ve büyük resim

3 Ağustos 2026'da mimar üç yaklaşımı ölçümle karşılaştırdı ve **C — Hibrit, katı yapıyla** kararını verdi:

| katman | içerik | rolü |
|---|---|---|
| **1 — Otorite** | `0 = zemin` (sürülebilir alan) segmentasyonu | Zemin olmayan **her şey engeldir**. Bilinmeyen → engel. **Varsayılan güvenli.** |
| **2 — Emniyet ağı** | `1 = engel` (seg) + araç (DOTA OBB dedektörü) + ince bariyer dedektörü | Sınırlı kritik nesne kümesi. **Yalnız çıkarır, asla eklemez.** |
| **3 — Geometri** | `distanceTransform ≥ R_gerekli` → C-uzayı + açıklık ağırlıklı A* | Rota koridorun ortasından geçer, gövde sığar |

**Değişmez kural (invariant):**
```
serbest = zemin AND NOT engel                 ← çıkarma EN SON
serbest(Katman1 ∧ ¬Katman2) ⊆ serbest(Katman1)  ← hiçbir dedektör serbest alanı BÜYÜTEMEZ
```
Bu sayede yeni bir dedektör eklemek **monotonik olarak güvenlidir**: sistemi ancak daha güvenli yapar, asla daha az.
Anayasa madde 15 bunu değişmez kılar.

## Seviye 2 — Neden böyle: üç yaklaşım ve ölçümler

### 2.1 Üç aday
- **A — Çoklu nesne segmentasyonu:** engel, araç, moloz vb. her şeyi ayrı sınıf olarak etiketle ve tespit et.
- **B — Sadece serbest alan:** yalnız sürülebilir zemini eğit; zemin dışı **her şey** doğal engel; `distanceTransform` ile
  İKA genişliği + emniyet payı koridor filtresi.
- **C — Hibrit:** B + sınırlı kritik nesne maskesi (yalnız çıkarır).

### 2.2 Şartname A'yı yapısal olarak dışlıyor
§6: *"diğer iki güzergâh fiziksel engeller (bariyer, enkaz simülasyonu **vb.**) ile tamamen kapatılacaktır."*
**"vb." = sayılamaz küme.** Yarışma günü eğitimde olmayan bir engel çıkarsa:

| yaklaşım | bilinmeyen nesneye varsayılan | sonuç |
|---|---|---|
| A | "tespit edilmedi → boş → geçilebilir" | **fail-dangerous** — İKA içine sürer |
| B / C | "zemin değil → engel" | **fail-safe** — etrafından dolaşır |

Zemin etiketlemek **kapalı** bir problemdir: zemin zemindir, gerisi engel.

### 2.3 A çıktı katmanı olarak ÖLÇÜLDÜ: sistem davranışına etkisi sıfır
`blocked` sınıfının AP50'si 0,4329 → 0,5371 (+%24) yükseltildi; **verilen kararlar hiç değişmedi**. Sebep: `analyze_path`'in
altı çağrı yerinin tamamı yalnız `masks[0]` (zemin) geçiriyor; `blocked` sınıfının karar yoluna **nedensel bağı yok**.
(`RESEARCH_NOTES.md` §2.2, `BULGULAR_20260720.md` §11B.)

### 2.4 Ama A ön-eğitim yardımcı görevi olarak KAZANDIRDI
10 sınıflı RescueNet ön-eğitimi → 2 sınıfa fine-tune (v15): mAP düşük ama arenada moloza basma **%2,7**; ön-eğitimsiz v13
mAP lideri ama moloza basma **%37,7**. Çoklu sınıf **temsil öğrenmeye** yarıyor, çıktı kafasına değil (K-7).

### 2.5 Saf B'nin ölümcül zaafı: yanlış-pozitif zemin
Model molozu "zemin" sanarsa İKA molozun içine sürer. Ölçüldü: v13 %37,7, v16 %31,6 moloza basma (v16'da etiketsiz moloz
yüzünden 11× kötüleşme). Saf B'de ikinci savunma hattı yok; C'de Katman 2 var: segmentasyon molozu kaçırsa bile araç
dedektörü/bariyer dedektörü onu serbest alandan çıkarır.

### 2.6 Katman 2'nin kâhini COCO değil DOTA OBB
Aynı hava fotoğrafında COCO `yolov8m-seg.pt` **2 araç**, DOTA `yolov8m-obb.pt` **93 araç**. COCO eşiğini 0,35 → 0,02 indirmek
18 karede yine sıfır kesişim verdi: eşik sorunu değil, **domain uyumsuzluğu** (COCO yer seviyesi; şartname 30 m nadir görüş).
Bu bulgu S1 kusurunu açtı: veri üreteci COCO ile araç maskeliyordu, araçların ~%98'i **"zemin"** olarak etiketleniyordu.

### 2.7 Performans bu kararı belirlemiyor
İlk PC ölçümünde (RTX 5080, v20) darboğaz costmap'ti (51 ms), ağ değil (26 ms). Sonra düzeltildi (costmap 8,9 ms). Sınıf
sayısının çıkarım maliyeti ölçülmedi ve ölçüm gürültüsünün altında beklenir. **Sonuç: A/B/C seçimi güvenlikle gerekçelendirilir,
hızla değil.** (Jetson'daki gerçek darboğaz 6 Eylül'de ölçüldü: `get_masks` + costmap CPU'da ~520 ms, toplamın %82'si — bkz. 10.)

### 2.8 OpenCV kısıtı (anayasa madde 4)
SciPy / scikit-image / sklearn / networkx **yasak**; `costmap_path_finder.py` yalnız `heapq`, `cv2`, `numpy`, `logging`.
Medial-axis yerine **açıklık ağırlıklı A\***: `maliyet = 1.0 + LAMBDA_ACIKLIK · u^US_ACIKLIK` (3.0, 2.0). Bilinçli ikame.

## Seviye 3 — Ayrıntı: veri akışı, sabitler, karar kayıtları

### 3.1 Uçtan uca veri akışı (`ARCHITECT_PLAN.md` §4, bugünkü adlarla)

```
İHA (Jetson, havada)
  kamera karesi
    → rpi_inference._preprocess()      LETTERBOX (kırpma yok) + ışık normalizasyonu → tuval + içerik dikdörtgeni
    → YOLOv8-seg (imgsz 512, v36)       → maskeler {0: zemin, 1: engel}
    → get_masks() + _maskeleri_icerige_kirp()  dolgu bölgesi sıfırlanır; ince bariyer dedektörü ENGELE ekler
    → ölçek: mpp = 2·h·tan(FOV/2)/W   canlı irtifa (MAVLink GLOBAL_POSITION_INT.relative_alt, tazelik ≤ 0,5 s)
    → analyze_path()  [ÜRETİM]         serbest = zemin AND NOT engel; C-uzayı (dist ≥ r_gerekli_px);
                                        en büyük bağlı bileşen; K-A uç-bant teması; A* tanık yol; şerit kararı
    → ret kapıları                       OLCEK_YOK · ZEMIN_MASKESI_SUPHELI · MASKE_YOK · UC_BANT_TEMAS_YOK · DUSUK_GUVEN · KORIDOR_DEGIL …
    → comms/iha_sender.KararYayinci     her karede OPEN_ROUTE(road, conf, waypoints) YA DA NO_ROUTE(sebep, detay)
          │ UDP (WiFi/sim) / SiK 433 MHz (seri hub)
   ┌──────┴──────────┐
 YKS (yks_gui)       İKA (ika_receiver → ika_nav)
 hakem ekranı,       üçlü kilit: OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO
 2 aşamalı onay,     → navigate (waypoint takibi) → sürücü arayüzü (gerçek arka uç YOK)
 IKA_GO, kanıt kaydı
```

Tanısal ikinci yol: `costmap_path_finder.rota_bul` (koridor envanteri, `ACIK | KAPALI_DAR | KAPALI_KOPUK | BELIRSIZ_*`). Genel
kapı **iki kolu** birden koşar (KOL 1 `rota_bul` 15/15, KOL 2 `analyze_path` ≥ 14/15) — T156, `CONTRACTS.md` §11.2-EK.

### 3.2 Geometri sabitleri (`codes/costmap_path_finder.py`, tek kaynak; `CONTRACTS.md` §4)

| sabit | değer | anlam |
|---|---|---|
| `IKA_GENISLIK_M` | 0,70 | İKA gövde genişliği |
| `MASKE_HATA_M` | 0,25 | segmentasyon sınır belirsizliği |
| `TAKIP_HATA_M` | 0,50 | sürüş takip hatası |
| **`R_GEREKLI_M`** | **1,10** | 0,70/2 + 0,25 + 0,50 — geçilebilirlik yarıçapı |
| `ALGI_PAYI_M` | 0,25 | engel genişletme payı |
| `AC_M` / `KAPAT_M` | 0,30 / 0,40 | zemin morfolojisi |
| `LAMBDA_ACIKLIK` / `US_ACIKLIK` | 3,0 / 2,0 | A* açıklık cezası |
| `WP_ARALIK_M` / `MAKS_WP` | 2,0 / 64 | waypoint aralığı / azami sayı |

Geçilebilirlik testi: `gecilebilir = dt_px >= r_gerekli_px`, `r_gerekli_px = R_GEREKLI_M / mpp`. Rota doğrulaması **C-uzayında**
(dt üzerinden), ham maskede asla. Çıkarmadan sonra serbest alanı büyüten işlemler (`dilate`, `MORPH_CLOSE`, `bitwise_or`,
`np.maximum`) **yasak**; bağlı bileşen alan filtresi silme işlemidir, serbest.

### 3.3 Sınıf id sözleşmesi — bir kez canlı kusur oldu (S2, D-35)
İki ad alanı ayrıldı, tek otorite `codes/sinif_semasi.py`:
```
EĞİTİM SINIFLARI      ZEMIN=0   ENGEL=1   HEDEF=2       (model çıktısı / YOLO etiketi)
COSTMAP KATMANLARI    KATMAN_ZEMIN=0  KATMAN_MOLOZ=1  KATMAN_ARAC=10   (çalışma anı; araç DOTA OBB'den)
COSTMAP_ENGEL_KATMANLARI = (KATMAN_MOLOZ, KATMAN_ARAC)
```
Eski kusur: `iha_haritala.py` `2 = araç` derken üreteç `2 = hedef` diyordu → 3 sınıflı model bu yola verilseydi **H brandası
engel sayılır, İKA hedefe hiç ulaşamaz, P_görev = 0**. Araç katmanı 10'dan başlar (eğitim uzayı 0..9 ile çarpışmasın);
modül import anında `dogrula()` koşar, çakışma varsa yüklenmez. Kapı `codes/test_sinif_semasi.py` 8/8, pozitif kontrol dâhil.

### 3.4 Karar kayıtları (`ARCHITECT_PLAN.md` §6) — jüri "neden X değil?" derse
- **K-1 ROS2 kurulmayacak.** JSON/UDP + SiK hattı güçlendirildi; 58 gün içinde ROS2 sahada çalışan hattı riske atar, puan getirmez.
- **K-2 Sınıf-id sözleşmesi tek yerde** (yukarıda).
- **K-3 Model seçimi RescueNet mAP'ine göre YAPILMAZ**; mAP arena sıralamasını tersine çeviriyor. Ölçüt hiyerarşisi: 1) karar
  doğruluğu, 2) moloza basma, 3) mAP reddedildi, 4) gürültü tabanı sd ≈ 0,03 → 0,04'ten küçük fark gürültü.
- **K-4 Ölçüm yolu üretim yolundan ayrışmaz** (aynı `analyze_path`); ayrışırsa "ölçüm geçersizliği".
- **K-6 Kritik nesne kâhini DOTA OBB.**
- **K-7 Çoklu sınıf yalnız ön-eğitim yardımcı görevi.**
- **K-8 FPS hedefi 3, asgari 1** (kullanıcı, 18 Ağustos); ve model sevk edilmeden **iki kapı**: arena başarımı + gerçek nadir
  karede zemin çıkarabilme (`data/raw_frames`, ≥ %5 zemin). Arena şampiyonu v17 gerçek nadir karede 10/67 kullanılabilirdi
  (körlük); bu "katastrofik unutma" bulgusu bağlayıcı kural doğurdu.

### 3.5 Bu kararın açtığı görevler (S1–S8) ve akıbeti
S1 üreteçte kâhin COCO→DOTA (tıkayıcı; kapandı) · S2 sınıf-id sözleşmesi (kapandı 5 Ağu) · S3 monotonluk invariantı testi
(kapandı) · S4 iki ıraksak karar yolu → T151/T155/T156 ile "analyze_path üretim, rota_bul tanısal" beyanı ve genel kapı iki kol ·
S5 `imgsz` sabitlenmesi (v17 640→960'ta IoU 0,861→0,034; bugün registry `imgsz=512`, T163 kilidi) · S6 hedef sınıfı tohum
olarak bağlı değil (**hâlâ açık**, HB dedektörü ayrı yol) · S7 ölçüm betikleri makine-okunur çıktı (kapandı) · S8 FDA profili
20×20 m üretece (T14/T15).

---

## Jüriye 30 saniyede

> "Nesne tespit etmek yerine sürülebilir zemini segmentliyoruz, çünkü şartname engelleri 'vb.' ile tanımlıyor: sayılamaz bir
> küme. Bilinmeyen bir engel çıktığında nesne tespiti onu 'boş, geçilebilir' sayar; bizde zemin olmayan her şey engeldir.
> Üstüne sınırlı bir emniyet katmanı var: araç ve bariyer dedektörleri yalnız çıkarır, asla serbest alan eklemez. Bu
> monotonluk kuralı kodda ve testte kilitli. Bu kararı hızla değil ölçülmüş güvenlikle verdik: mAP lideri model arenada
> molozun yüzde 38'ine basıyordu."

## Kendini sına

1. "vb." kelimesi neden A yaklaşımını dışlıyor?
2. Monotonluk kuralını formülle yaz. Hangi OpenCV işlemleri çıkarmadan sonra yasak?
3. `blocked` AP50'yi %24 artırınca sistem kararı neden değişmedi?
4. v13 ile v17'yi mAP ve moloza basma açısından karşılaştır. Ders ne?
5. `R_GEREKLI_M` nasıl hesaplanır, hangi üç bileşenden?
6. Neden COCO değil DOTA OBB?
7. `KATMAN_ARAC` neden 10?
8. Medial-axis kullanılamadığı için ne yapıldı?
9. "Kör bir model %0 moloza basar" cümlesi ne anlatır?
10. Üretim karar yolu hangisi, tanısal hangisi? Genel kapı kaç kol?

<details><summary>Cevaplar</summary>

1. Etiketlenebilir kapalı bir küme değil; eğitimde olmayan engel "tespit edilmedi → geçilebilir" olur (fail-dangerous). 2. `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)`; `cv2.dilate`, `MORPH_CLOSE/DILATE`, `bitwise_or`, `np.maximum`. 3. `analyze_path` çağrılarının hepsi yalnız `masks[0]` (zemin) kullanır; engel sınıfının karar yoluna nedensel bağı yok. 4. v13 mAP 0,679 (en yüksek) ama moloza basma %37,7 (en kötü); v17 mAP 0,636 (en düşük) ama %0 ve arena IoU 0,861. mAP arena sıralamasını tersine çevirir; model seçimi mAP'e dayandırılmaz. 5. 0,70/2 + 0,25 + 0,50 = 1,10 m: yarım gövde + maske hatası + takip hatası. 6. COCO yer seviyesi; 30 m nadir görüşte 93 araca karşı 2 buldu; eşik indirmek çözmedi (domain uyumsuzluğu). 7. Eğitim sınıf uzayı 0..9 ile çakışmasın; 3 sınıflı model gelse bile HEDEF (2) engel katmanına denk gelmez. 8. Açıklık ağırlıklı A*: maliyet = 1 + 3·u² ile koridor ortasından geçiş. 9. Sıfır bedava bir sıfırdır; hiç çıktı üretmeyen model (v9) başarı değil körlüktür; K0 körlük kapısı bunun için var. 10. Üretim `rpi_inference.analyze_path`, tanısal `costmap_path_finder.rota_bul`; genel kapı iki kol (15/15 ve ≥14/15).
</details>

## Kaynaklar
`RESEARCH_NOTES.md` (tamamı) · `ARCHITECT_PLAN.md` §4–§9 · `CONTRACTS.md` §1–§4, §10, §11.2-EK · `codes/sinif_semasi.py` ·
`codes/costmap_path_finder.py` · `codes/test_sinif_semasi.py` · `REVIEW_LOG.md` D-12, D-18, D-35.
