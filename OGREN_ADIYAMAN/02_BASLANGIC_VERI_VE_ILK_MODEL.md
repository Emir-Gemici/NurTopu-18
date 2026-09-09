# 02 · BAŞLANGIÇ — veri, YOLOv8-seg ve ilk hat (Mayıs–Temmuz 2026)

> Kaynaklar: `README.md` (ilk dönem belgesi; Orin NX/RPi/NCNN varsayımlarını taşır, bugün kısmen bayat) · `dataset/VERI_KAYNAKLARI.md` (yetkili veri
> belgesi, 28 Ağu) · `codes/train_seg.py`, `train_seg_v3.py` · `scripts/olcum/40_surum_degerlendirme.py` · `git log` (ilk commit 6 Mayıs 2026 "start project")
> · `navitas-teknofest/references/ddr_requirements.md` (DDR 15 Temmuz) · kod düzeyi ayrıntı `ozet/F_model_veri_egitim.md`.
> Bu dosya ML bilmeyen okuyucu için **kavramları sıfırdan** kurar; sonraki dosyalar bunlara dayanır.

---

## Seviye 1 — Bir cümle ve büyük resim

Proje 6 Mayıs 2026'da başladı. İlk üç ayın işi **"drone karesinde sürülebilir zemini boyayan" bir model** eğitmekti: RescueNet (afet
sonrası drone verisi) üzerinde YOLOv8-seg, iki sınıf (`traversable`, `blocked`), 512 piksel giriş; ilk hedef Raspberry Pi 5'te NCNN
ile ≥ 10 FPS idi. Temmuz ortasında DDR teslim edildi (15 Tem), model v3–v5c dönemi kapandı, Temmuz sonunda **sentetik arena** ve
ilk gerçek drone çekimi (30 Tem, otopark) geldi. Ağustos'ta mimar düzeni kurulunca (03) her şey ölçülüp yeniden değerlendirildi:
bu dönemin "başarılı" sanılan modeli (v17) gerçek karede **kör** çıktı.

## Seviye 2 — Kavramlar ve ilk hat

### 2.1 Segmentasyon nedir, neden "tespit" değil
- **Nesne tespiti** kutu çizer ("burada bir araba var"). **Semantik/örnek segmentasyonu** her pikseli sınıfa boyar ("bu pikseller zemin").
  Bizim sorumuz "hangi koridordan İKA geçebilir": kutu yetmez, **zeminin şekli** gerekir → segmentasyon.
- **YOLOv8-seg** (Ultralytics): tek geçişte kutu + piksel maskesi üreten hızlı bir sinir ağı. Boyutlar n (nano) < s < m < l. Maske
  "prototipleri" sınıflar arasında paylaşılır; sınıf sayısı çıkarım maliyetini pek değiştirmez.
- Çıktı: `results[i].masks.data` → her tespit için (h×w) olasılık haritası; `> 0,5` eşiği ile ikili maske; sınıf başına `np.maximum` ile
  birleştirilir (`rpi_inference.get_masks`).

### 2.2 Eğitim kavramları (kısa sözlük)
- **Epoch**: tüm eğitim kümesinin bir kez geçilmesi. **Batch**: bir adımda işlenen görüntü sayısı. **imgsz**: girdi kenarı (512).
- **Augmentasyon**: veriyi çeşitlendirmek için döndürme (`degrees`), çevirme (`flipud/fliplr`), renk (`hsv_*`), mozaik, **copy-paste**
  (bir görüntüden nesne kesip diğerine yapıştırma). Bu projede copy-paste **kendi veri üretecinin** adı da oldu (aşağıda).
- **Fine-tune**: hazır ağırlıktan devam etmek (v15: 10 sınıflı ön-eğitim → 2 sınıfa).
- **mAP50**: tespit/maske doğruluğu özeti (0–1). Bu projede model seçiminde **reddedildi** (03 §2.5): arena sıralamasını tersine çeviriyor.
- **IoU**: iki maskenin kesişim/birleşim oranı. **Kaplama**: maskenin karedeki payı. **Sızıntı**: doğrulama görüntüsünün eğitimde de olması
  (sayıyı şişirir; D-26, D-233, D-376 bu projede üç kez yakalandı).
- **Ön-eğitim (pretraining)**: COCO ya da 10 sınıflı RescueNet gibi geniş görevle öğrenilmiş ağırlıktan başlamak; v15'in arena kazancı buradan.

### 2.3 Sınıflar
| id | ad | anlam |
|---|---|---|
| 0 | `traversable` / zemin | sürülebilir zemin — **otorite** |
| 1 | `blocked` / engel | moloz, bariyer, enkaz; sonradan bina/ağaç/su/araç da buraya eşlendi (T54) |
| 2 | `hedef` | 2×2 m kırmızı H — yalnız etiket üretecinin ad alanında; üretim modeli `nc: 2` |
Tek otorite `codes/sinif_semasi.py`; costmap katmanları 10'dan başlar (03 §3.3).

### 2.4 Veri kaynakları — ne, ne kadar, ne işe yaradı (`dataset/VERI_KAYNAKLARI.md`)
| kaynak | boyut | rol | v36'da? |
|---|---|---|---|
| **RescueNet** roads (HF `asolodin/rescuenet-roads`) | 2 365 train / 294 val / 305 test | ana gerçek afet verisi; `road-clear`→0, `road-blocked`→1 | ✅ (T54 "zemin değil → engel" eşlemesiyle 3 502 train) |
| RescueNet 11 sınıf | `nc: 10` | yardımcı görev **ön-eğitimi** (v15) ve engel eşlemesi (engel poligonu 850 → 22 356, 26×) | ✅ |
| FloodNet | 798 / 257 | yalnız v2 | ❌ (iki dönüştürücü farklı yol indeksi: 4 mü 5 mi, DOĞRULANAMADI) |
| Semantic Drone, Dubai Aerial | — | indirici yazıldı, **hiç kullanılmadı** | ❌ |
| Roboflow | — | yalnız test görselleri | ❌ |
| **Sentetik arena** (kendi üreteç `51_sentetik_arena.py`) | ~2 700 train | şartname geometrisi (50×50 m, 3 koridor, biri açık, HB 2×2 m); etiket piksel-kusursuz; "etiketsiz moloz yok" kuralı | ✅ |
| **copy_paste_gercek → t127** | 67 gerçek kare → 344 train | 30 Tem otopark karelerine sentetik moloz; v17 körlüğünü açan bileşen | ✅ |
| **DJI 22 Ağu** (gündüz, kırsal) | 486 etiketli kare ×5 | v36'nın gerçek bileşeni; **kör** etiket (56 amele + 7 denetçi); üç durumlu maske | ✅ |
| **0038 DOĞRULAMA** | 29 test + 82 val | eğitime **girmez**; iki kör geçişin uzlaşısı | test |
| DJI 20 Ağu gece | 569 kare | eğitime girmedi (medyan parlaklık 19) | ❌ |
| Şartname figürü | 1 kare | YZ ürünü; K0/K8 kapılarında | test |
| T66 kabul kümesi | 260 sentetik kadraj | K0–K7 kapıları (PC'de, depoda yok) | test |
Etiket kalite kapısı U1/U2 (etiketleyiciler arası IoU ≥ 0,75 / referansa ≥ 0,70): ölçülen **0,910 / 0,899** → geçti; etiketleme kapasitesi
5,1 kare/saat (19,9 değil; D-279).

### 2.5 İlk hat (Mayıs–Temmuz): ne varsayılıyordu
`README.md`: Orin NX + geniş açı kamera, İKA RPi 5 + Pi kamera + A* + PID, YKS dizüstü; model YOLOv8**n**-seg, NCNN export, RPi'de ≥ 10 FPS;
`rpi_inference.py` merkez kare crop → 512 → maske → distance transform centerline → "üst %40'ta hangi üçte birde daha çok zemin" →
`open_path` 1/2/3 → 8 waypoint; JSON payload `{open_path, confidence, waypoints, timestamp}`; Gazebo simülasyonu (kolay/orta/zor dünyalar,
`score.py`); Gemini üretimi 12 test görseli; haberleşme "MAVLink over UDP, 433 MHz SiK, ≤ 200 ms, 300 m".
Bugün bunların çoğu değişti: crop → **letterbox pad** (crop 1024×576'da genişliğin %56'sını atıyordu), "üst %40 üçte bir" → rota gövdesi
şerit kararı, NCNN → PyTorch GPU, RPi → Jetson, 10 FPS hedefi → 3 FPS hedef / 1 FPS asgari, JSON payload → `OPEN_ROUTE/NO_ROUTE` protokolü.

### 2.6 DDR (15 Temmuz) — Halil'in alanı
`ddr_requirements.md`: Halil = görüntü işleme, uçuş yazılımı, sistem mimarisi. DDR'de aviyonik/yazılım gereksinimleri REQ-35…40
(mimari, BOM, kablaj, güç, batarya, **güzergâh tespit akış şeması**); DDR BOM'u final aracı içindi (Orin NX, Arducam IMX477, M10,
Crossfire, X2216 ×2 motor, 4S 14–15 Ah, Opale 2,5 m² paraşüt; toplam 2 293 g). FDR bu BOM'un FDA aracıyla farkını açıkça yazar.

## Seviye 3 — Sürüm tarihçesi v1 → v20 (Temmuz) ve dersleri

| sürüm | tarih | ne | sonuç / ders |
|---|---|---|---|
| v1 | ≤ 11 Tem | RescueNet | mask mAP50 0,619; blocked 0,363 |
| v2 | 11 Tem | YOLOv8n, RescueNet + FloodNet, Colab 100 epoch; reçete `train_seg.py` (degrees 45, copy_paste 0,15, NCNN) | blocked **geriledi** 0,322; NCNN türevi bugün `legacy-fallback` |
| v3 | 12 Tem | YOLOv8s, degrees 15, copy_paste 0,30, 200 epoch, blocked oversampling | ara |
| v4 | 15 Tem | v3'ten ft, 640 | val'de en iyi; test split'i o güne dek hiç kullanılmamıştı (`11_capraz_dogrulama`) |
| **v5c** | 15 Tem | **YOLOv8m@640**, COCO'dan 200 epoch | mAP +0,043, blocked +0,076; gerçek karede 58/67 (arena görmemiş) |
| v6/v7 | 20 Tem | 1024 native | mAP artmadı, FPS düştü → RED |
| v9 mixup | 27 Tem | v5c + mixup | test mAP 0,6787 ama arenada **tam kör** ("sıfır bedava") |
| v12 | 27 Tem | warmup_bias_lr=0 | val +0,013, test −0,013: val'e aşırı uyum → RED |
| v13 | 27 Tem | box=10 | mAP **0,6794 (en yüksek)** · moloza basma **%37,7 (en kötü)** |
| **v15** | 28 Tem | 10 sınıf ön-eğitim → 2 sınıf | mAP 0,655 · moloza basma **%2,7** — kazanç arenada |
| v16 | 29 Tem | + sentetik arena v1 | %31,6 (etiketsiz moloz → 11× kötü) → üreteç düzeltildi |
| **v17** | 29 Tem | + sentetik arena v2 | arena IoU 0,077 → **0,861**, moloz %0; ama gerçek karede **10/67** (D-12/D-18 katastrofik unutma) |
| v18–v20 | 30 Tem | dar/kontrast/multi_scale | imgsz duyarlılığı (S5) düzelmedi |

**Üç ders (Ağustos'ta kurallaştı):** (1) mAP'e göre seçme (K-3); (2) model iki kapıdan geçer: arena + gerçek nadir karede zemin (K-8);
(3) sentetik veriyle yalnız başına eğitmek gerçek dokuyu unutturur → gerçek doku bileşeni (v21, 5 Ağu: 67/67).

**Eğitim reçeteleri (kanıtlı):** v2 CPU Ryzen 7 5700U, YOLOv8n, 150 epoch, batch 8, AdamW lr0 0,001; v21 v15 tabanı, 640, 60 epoch, 141 dk;
v27 640/200 epoch ~5,9 sa; v30 200 epoch 386 dk; **v36** v35 tabanı, RTX 5080 Laptop 16 GB, 8 611 train, val 73 gerçek DJI, 40 epoch/
patience 15 → **17 epoch, en iyi epoch 2, 0,65 saat**; `optimizer=auto` yüzünden lr0 sessizce 0,001667; **degrees 0, flipud 0, copy_paste 0**
(defterdeki "reçete t127 birebir" iddiası yanlıştı, D-324) → v36 döndürme görmedi, bariyeri 60–135°'de görmüyor. Tüm eğitimler PC'de
(`O:\navitas-local-train`, depo dışı); Jetson'da eğitim yok.

**Copy-paste üretecinin kritik kuralı:** zemin satırı tam kare dikdörtgen, engeller üstüne poligon → engel maskesine girmeyen her nesne
"zemin" etiketi alır. COCO kâhini araçların ~%98'ini zemin öğretiyordu (S1, DOTA'ya geçildi); çatı da zemin sayılıyordu (T121/T122 etiket
yaması; T127 temiz bölüm; D-233: eski val'in 55/55 karesi eğitimde de vardı, %100 sızıntı).

---

## Jüriye 30 saniyede

> "Modelimiz YOLOv8m segmentasyon; her pikseli sürülebilir zemin ya da engel diye boyar. Eğitim verisi dört kaynak: RescueNet afet
> drone verisi, şartname geometrisiyle ürettiğimiz sentetik arena, gerçek drone karelerine yapıştırılmış sentetik moloz ve kendi
> DJI çekimimizden kör etiketlenmiş kareler. Doğrulama kümesi eğitime hiç girmedi. Model seçiminde mAP'e bakmıyoruz: mAP lideri model
> arenada molozun yüzde 38'ine basıyordu. Yalnız sentetikle eğitince gerçek karede kör kaldığını ölçtük, bu yüzden gerçek doku ekledik."

## Kendini sına

1. Segmentasyon ile tespit farkı; neden segmentasyon?
2. Üretim modelinin sınıfları ve `nc` değeri? Sınıf 2 nerede yaşar?
3. RescueNet'in 11 sınıfı bugün nasıl kullanılıyor (iki yol)?
4. Sentetik arena üretecinin "etiketsiz moloz yok" kuralı neden kritik? (v16 ile anlat.)
5. v13 ve v15'i karşılaştır; ders?
6. v17'nin arena IoU'su ve gerçek karedeki durumu; adı ne?
7. 0038 kümesi nedir, neden eğitime girmez?
8. v36 kaç epoch, en iyi epoch, hangi donanım; reçetede ne eksikti ve bedeli ne?
9. Copy-paste üretecinde araçlar neden "zemin" oluyordu; çözüm?
10. İlk hat ile bugünkü hat arasındaki beş fark?

<details><summary>Cevaplar</summary>

1. Tespit kutu, segmentasyon piksel; koridor şekli gerektiği için segmentasyon. 2. 0 traversable, 1 blocked, nc=2; hedef (2) yalnız etiket üretecinin ad alanında. 3. 10 sınıflı ön-eğitim (v15 kazancı) ve T54 "zemin değil → engel" eşlemesi (bina/ağaç/su/araç → 1). 4. Etiketlenmemiş moloz "zemin" öğretilir; v16'da moloza basma %2,7 → %31,6 (11×). 5. v13 mAP en yüksek/moloza basma en kötü; v15 ön-eğitimli, %2,7; mAP arena sıralamasını tersine çevirir. 6. 0,861; 10/67 kullanılabilir; katastrofik unutma (D-12/D-18). 7. DJI 22 Ağustos 0038 uçuşu, 29 test + 82 val, iki kör etiketin uzlaşısı; bağımsız ölçüm için eğitime ve erken durdurmaya girmez (CONTRACTS §12). 8. 17 epoch, en iyi 2, RTX 5080 Laptop, 0,65 saat; degrees/flipud/copy_paste 0 → bariyeri 60–135°'de görmüyor. 9. COCO kâhini 93 araçtan 2'sini buluyordu, kalanlar tam-kare zemin dikdörtgeninin altında kalıyordu; DOTA OBB'ye geçildi (S1). 10. crop→letterbox pad, üçte-bir sayımı→rota gövdesi şeridi, NCNN/RPi→PyTorch/Jetson, 10 FPS→3/1 FPS, JSON payload→OPEN/NO_ROUTE protokolü (ayrıca YOLOv8n→m).
</details>

## Kaynaklar
`dataset/VERI_KAYNAKLARI.md` · `dataset/karisim_gece_v7a.yaml` · `results/gece_20260826/egitim_v7a.log` · `scripts/olcum/40_surum_degerlendirme.py` ·
`scripts/olcum/51_sentetik_arena.py` · `scripts/copy_paste_augmentation.py` · `CONTRACTS.md` §12 · `REVIEW_LOG.md` D-12, D-18, D-20, D-233, D-279, D-324.
