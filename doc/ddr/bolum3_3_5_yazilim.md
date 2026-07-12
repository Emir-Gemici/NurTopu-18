# Bölüm 3.3.5 — Yazılım Mimarisi ve Görüntü İşleme

> Şablon isterleri: (a) Yazılım Altyapısı — dil/kütüphane/OS + seçim sebepleri,
> (b) Görüntü İşleme Algoritması — AI/ML çalışma prensibi + veri seti hazırlığı +
> eğitim süreci + başarı oranları + BLOK ŞEMA, (c) Haberleşme Protokolü — İHA↔İKA
> mimari + veri bütünlüğü/güvenliği. Aşağıdaki metin Word şablonuna doğrudan
> yapıştırılabilir; [GÖRSEL: ...] işaretli yerlere doc/ddr/gorseller/ altındaki
> şemalar eklenecek.

---

## Yazılım Altyapısı

Sistemin yazılım altyapısı; geliştirme hızı, gömülü platform desteği ve gerçek
zamanlılık gereksinimleri gözetilerek üç katmanda yapılandırılmıştır.

**Programlama dilleri:**

| Dil | Kullanım alanı | Seçim gerekçesi |
|---|---|---|
| Python 3 | İHA görüntü işleme, İKA navigasyon, haberleşme, test/otomasyon | Ultralytics/OpenCV ekosistemiyle doğrudan entegrasyon; Jetson ve RPi 5 üzerinde birinci sınıf destek; hızlı iterasyon ve okunabilirlik (takım içinde bakım ve devir kolaylığı) |
| C++17 | Simülasyon eklentileri (Gazebo world/sensor plugin), performans kritik döngüler | Fizik motoru güncelleme döngüsünde (1 kHz) çalışma zorunluluğu; Gazebo API'sinin native dili |
| Bash | Kayıt/test otomasyonu, konteyner orkestrasyonu | Tekrarlanabilir test koşuları; CI benzeri otomasyon |

**Kütüphaneler ve araçlar:**

| Kütüphane/Araç | Rol | Seçim gerekçesi |
|---|---|---|
| Ultralytics YOLOv8 | Semantik segmentasyon (açık yol tespiti) | Tek geçişte gerçek zamanlı segmentasyon; nano varyantı (3,4M parametre) gömülü cihaza sığar; NCNN/TensorRT dışa aktarım desteği |
| OpenCV | Görüntü ön işleme, ortomozaik, morfoloji, distance transform | Endüstri standardı; ARM üzerinde optimize |
| NumPy | Maske/koordinat hesapları | Vektörel hesap performansı |
| NCNN | RPi 5 üzerinde model çıkarımı | ARM'de PyTorch'a göre belirgin hız; 12,6 MB model |
| picamera2 + GStreamer | İKA/İHA kamera erişimi ve H.264 video akışı | RPi kamera yığınının resmî yolu; düşük gecikmeli donanım kodlama |
| Gazebo Classic 11 + Podman | Görev simülasyonu (SITL yaklaşımı) | Fizik doğrulama; konteynerle her makinede aynı ortam |
| systemd | Araç üstü servis yönetimi | Güç kesintisi/yeniden başlatmada otonom toparlanma (watchdog + otomatik yeniden başlatma) |

**İşletim sistemleri:**

| Platform | OS | Gerekçe |
|---|---|---|
| İKA (Raspberry Pi 5) | Ubuntu Server 26.04 LTS | LTS destek süresi; picamera2/NCNN uyumu; systemd servisleri **gerçek donanımda doğrulandı** (kamera yayını servisi, kendiliğinden toparlanma) |
| İHA (Jetson Orin NX) | NVIDIA JetPack (L4T) | CUDA/TensorRT hızlandırması; YOLOv8 için üretici destekli yol |
| Yer istasyonu / geliştirme | Linux | Aynı araç zinciri; simülasyon ve saha yazılımı tek repo |

---

## Görüntü İşleme Algoritması

### Çalışma prensibi

Açık yol tespiti, **YOLOv8n-seg** semantik segmentasyon modeli üzerine kurulu
çok aşamalı bir boru hattıyla yapılır [GÖRSEL: gorseller/blok_goruntu_isleme.png]:

1. **Girdi standardizasyonu:** Ham hava görüntüsü, en-boy oranı korunarak
   1024×1024 kareye "letterbox" edilir. Böylece sonuç, kamera çözünürlüğünden
   bağımsızdır (aynı sahne 614²'den 3344 piksele kadar test edilmiş, karar
   değişmemiştir).
2. **Işık normalizasyonu:** Görüntü karanlıksa (ortalama parlaklık < eşik),
   gamma düzeltme + CLAHE uygulanmış kopya da modele verilir; daha fazla
   geçilebilir alan bulan sonuç kullanılır (gölge/loş ışık dayanıklılığı).
3. **Segmentasyon:** Model her pikseli `traversable` (geçilebilir zemin) /
   `blocked` (moloz) olarak maskeler. Güven eşiği 0,15; tespit çıkmazsa 0,05'e
   otomatik inilir (düşük kontrastta kademeli davranış).
4. **Gürültü ayıklama:** Morfolojik açma/kapama + **en büyük bağlı bileşen**
   filtresi — kopuk gürültü lekeleri yol kararını değiştiremez.
5. **Yol kararı:** Koridorun hedefe ulaşan üst bandındaki yatay ağırlık merkezi
   (centroid) sahanın üçte-birlerine oturtulur → SOL / ORTA / SAĞ.
6. **Rota üretimi:** Distance-transform ile koridorun **merkez hattı** çıkarılır,
   yatay bantlarda güneyden kuzeye waypoint örneklenir; piksel koordinatları,
   bilinen uçuş irtifası (30 m) ve kamera görüş açısından (1,3 rad) **metreye**
   çevrilir.
7. **Sağlamlık süzgeci:** Saha sınırı dışındaki, başlangıcın gerisindeki veya
   akışa ters düşen noktalar atılır; güvenilir rota kalmazsa veri İKA'ya
   **gönderilmez** (yanlış yönlendirme yerine güvenli durma).

Tarama uçuşunda İHA, 50×50 m alanı 30 m irtifadan serpantin desenle geçerken
1 Hz nadir kare toplar; kareler, çekim anındaki araç pozuyla birleştirilerek
kuzey-yukarı bir **ortomozaik saha haritası** oluşturulur ve model kararını bu
bütünleşik haritada verir [GÖRSEL: simülasyon çıktısı ortomozaik.jpg + algi.jpg].

### Veri seti hazırlığı

Temel veri kümesi **RescueNet**'tir (Michael Kasırgası sonrası sahada toplanmış gerçek İHA
görüntüleri; road-clear/road-blocked sınıfları `traversable`/`blocked`'a
eşlendi). Dağılım:

| Split | Görüntü | traversable örnek | blocked örnek |
|---|---|---|---|
| Eğitim | 2.365 | 2.327 | 660 |
| Doğrulama | 294 | 282 | 81 |
| Test | 305 | 308 | 85 |

Sınıf dengesizliği (blocked ~3,5× az) bilinen bir kısıttır; v2 eğitiminde
**FloodNet** eklenerek blocked çeşitliliği artırılmıştır. Görüntüler 30°–90°
hava açısını kapsar; İHA kamerası nadir (dik) bakışlı olduğundan dağılımla
uyumludur.

### Eğitim süreci

| Parametre | v1 (temel) | v2 (güncel) |
|---|---|---|
| Model | YOLOv8n-seg | YOLOv8n-seg |
| Veri | RescueNet | RescueNet (+FloodNet hedeflendi; fiilî katkı doğrulanamadı — bkz. not) |
| Epoch | 100 (early stop patience 20, en iyi: 85) | 100 (patience 40, cosine lr) |
| Görüntü boyutu | 512 | 512 (eğitim); çıkarımda 1024 letterbox |
| Optimizer / lr0 | AdamW / 0,001 | AdamW / 0,001 (lrf 0,005) |
| Donanım | CPU (16,6 sa) | Google Colab GPU |

### Başarı oranları

Doğrulama seti (v1, best.pt):

| Metrik | Değer | Hedef |
|---|---|---|
| Mask mAP50 (genel) | **0,619** | ≥ 0,60 — sağlandı |
| Mask mAP50 — traversable | **0,874** | görevin kritik sınıfı |
| Mask mAP50 — blocked | 0,363 | sınıf dengesizliği; iyileştirme planlı |
| Precision / Recall (mask) | 0,674 / 0,604 | — |

Doğrulama seti (v2 — sahaya konan model). Değerler 11.07.2026 BAĞIMSIZ
yeniden ölçümü (Colab, Ultralytics 8.4.92; model SHA-256 c7ce71a4…; 294
görüntülük RescueNet val — v1 ile AYNI set). Gömülü eğitim-sonu değerleriyle
üçüncü haneye kadar örtüştü; ham log/grafikler: `results/v2_val_20260711/`:

| Metrik | Değer | Hedef |
|---|---|---|
| Mask mAP50 (genel) | **0,595** | ≥ 0,60 — hedefin hemen altında (bkz. not) |
| Mask mAP50 — traversable | **0,868** | görevin kritik sınıfı (v1: 0,874 — pratikte eşit) |
| Mask mAP50 — blocked | 0,322 | zayıf nokta (v1: 0,363); v3 hedefi |
| Box mAP50 | 0,561 | — |
| Mask mAP50-95 | 0,344 | — |
| Precision / Recall (mask) | 0,722 / 0,516 | — |

Not: Aynı doğrulama setinde v1 hedefi karşılar (0,619), v2 hemen altında kalır
(0,595). Fark tümüyle blocked sınıfından gelir: kritik sınıf traversable'da iki
model pratikte eşittir (0,874 ↔ 0,868). Karışıklık matrisi blocked zayıflığını
netler: gerçek molozun yalnızca %28'i yakalanıyor, %12'si geçilebilir zemin
sanılıyor — iyileştirme önceliği budur. v3 planı: sınıf dengeleme + perspektif
augmentasyonu + FloodNet veri hattının sürümlenerek yeniden kurulması
(11.07 doğrulamasında FloodNet kaynağı görüntü vermedi; fiilî katkı teyide muhtaç).

Sistem seviyesi doğrulamalar: (i) ölçek bağımsızlık testi — aynı sahne
0,6×–3,3× çözünürlükte aynı karar; (ii) ışık dayanıklılığı — gamma 2,2 karartma
ve gölge gradyanında karar korunur; (iii) simülasyon uçtan uca — İHA'nın kendi
tarama mozaiğinde model, gizli açık yolu doğru tespit etmiştir (bkz. Bölüm 4).
Bilinen zayıflıklar ve plan: yüksek eğik açıda performans düşer → perspektif
augmentasyonlu yeniden eğitim; blocked mAP'i → sınıf dengeli fine-tune.

Çıkarım performansı: dizüstü CPU ~540 ms/kare (tam boru hattı); RPi 5 NCNN
hedefi imgsz 512'de 8–15 FPS [DOLDUR: RPi gerçek FPS ölçümü]; Jetson Orin NX
hedefi ≥15 FPS (TensorRT).

---

## Haberleşme Protokolü

İHA↔İKA↔YKS haberleşmesi, **taşıyıcıdan bağımsız** tek bir uygulama protokolü
üzerine kuruludur: newline (`\n`) ile çerçevelenmiş JSON satırları. Aynı mesajlar
geliştirme/simülasyonda UDP, sahada RF telsiz modülün transparan seri kanalı
üzerinden taşınır — üst katman kodu değişmez. [GÖRSEL: gorseller/blok_haberlesme.png]

**Mesaj tipleri:**

| Tip | Yön | İçerik |
|---|---|---|
| `OPEN_ROUTE` | İHA → İKA, YKS | Asıl görev verisi: açık yol no + etiket + güven + **referans noktası (x,y)** + waypoint listesi (referansa göre yerel koordinatlar) |
| `HEARTBEAT` | tüm düğümler | Bağlantı canlılığı (failsafe girdisi) |
| `ACK` | İKA/YKS → İHA | Alındı onayı (seq numarası ile) |

**Veri bütünlüğü ve güvenilirlik önlemleri:**
- Her mesajda **protokol sürümü, artan sıra numarası (seq) ve zaman damgası**;
  alıcı eksik/yinelenen mesajı ayırt eder.
- `OPEN_ROUTE`, her iki alıcıdan **ACK alınana dek tekrar gönderilir**
  (RF paket kaybına dayanıklılık; ÖDR'de beyan edilen >%95 aktarım doğruluğu hedefi).
- JSON çerçeveleme, seri akışta bozuk baytların tek satırı feda etmesini sağlar;
  satır bütünlüğü ayrıştırıcıda doğrulanır (hatalı satır atılır).
- HEARTBEAT kesilirse İKA **güvenli durma** moduna geçer (arıza emniyet, bkz.
  Bölüm 3.3.1 mantık şemaları).
- Rota verisi, İHA'nın yayınladığı **başlangıç referans noktasına göre yerel**
  koordinatlar içerir; İKA mutlak konum hatasından etkilenmeden rotayı kendi
  çerçevesine oturtur.

Uçuş kontrol telemetrisi (konum/tutum/batarya) için otopilot tarafında MAVLink
kullanılır; görev verisi yukarıdaki hafif JSON protokolüyle ayrıştırılmıştır
(tek RF kanalında iki akışın çakışmaması ve hakem ekranında insan-okur veri).
Saha telsizi **433 MHz** bandında SiK modüldür (şartname frekans bandı
belirtmez; 433 MHz, BTK kısa mesafe erişimli telsiz düzenlemesine uygundur ve
geliştirme testleri de aynı modüllerle yapılmıştır).
