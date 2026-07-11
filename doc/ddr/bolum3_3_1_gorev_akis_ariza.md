# Bölüm 3.3.1 — Görev Akış Şemaları + Arıza Emniyet Mantığı (YAZILIM TARAFI)

> Şablon isteri: İHA ve İKA için AYRI görev akış şemaları + arıza emniyet
> senaryolarının mantık şemaları. (Elektronik bağlantı/kablolama şemaları bu
> dosyada DEĞİL — o kısım aviyonik ekibinde.) Aşağıdaki akışlar
> [GÖRSEL: gorseller/akis_iha.png] ve [GÖRSEL: gorseller/akis_ika.png]
> şemalarının metin karşılığıdır; şemaları rapora koyup metni altına özet
> olarak yapıştırabilirsiniz.

---

## İHA Görev Akışı

1. **HAZIRLIK** — sistem açılışı, kamera/GNSS/telemetri öz-testleri, YKS bağlantı
   doğrulaması ("Takım Hazır" öncesi kontrol listesi).
2. **FIRLATMA** — mancınıkla atış (stall hızının ≥1,15 katı); otopilot tam otonom
   tırmanış moduna geçer. Görev kronometresi başlar (limit 15 dk).
3. **İNTİKAL + TARAMA İRTİFASI** — 30 m tarama irtifasına tırmanış, HTAB'a giriş.
4. **SERPANTİN TARAMA** — 50×50 m alan 4 paralel hatta taranır (~20–30 s);
   nadir kamera 1 Hz kare toplar, her kare çekim anındaki araç pozuyla eşlenir.
5. **HARİTALAMA + TESPİT** — kareler kuzey-yukarı ortomozaiğe birleştirilir;
   YOLOv8-seg açık yolu tespit eder (hedef < 60 s), koridor merkez hattından
   koordinat rotası üretilir.
6. **VERİ AKTARIMI (HAVADA)** — `OPEN_ROUTE` (açık yol + referans noktası +
   yerel waypoint'ler) İKA ve YKS'ye yayınlanır; her iki ACK alınana dek tekrar
   gönderilir; hakem YKS ekranında canlı doğrular.
7. **SOKULMA + PARAŞÜT** — İHA-İB üzerine alçalma; paraşüt barometre+GNSS
   tetikli otonom açılır (<7 m/s çöküş); iniş → görev kronometresi durur.

## İKA Görev Akışı

1. **BEKLEME** — İKA-KB'de enerjili bekleme; İHA inişi teyit edilmeden hareket
   YASAK (şartname). `OPEN_ROUTE` alındıysa rota önbelleğe alınır, ACK dönülür.
2. **BAŞLATMA** — İHA inişi + YKS operatöründen manuel başlat komutu (izinli tek
   insan girdisi). Kronometre başlar (limit 10 dk).
3. **ROTA OTURTMA** — alınan yerel waypoint'ler, İHA'nın yayınladığı referans
   noktasına ve aracın kendi konum tahminine (GNSS+IMU+enkoder füzyonu)
   oturtulur; A* ile ara engel kaçınma planı üretilir.
4. **OTONOM SÜRÜŞ** — diferansiyel sürüşle waypoint takibi; kamera+model yerel
   doğrulama (önü kapalıysa dur); telemetri (konum/hız/hedef wp) YKS'ye akar.
5. **HB TESPİTİ + DURMA** — hedef bölge yarıçapına girince görev BAŞARILI;
   araç durur, kronometre durur.

---

## Arıza Emniyet Senaryoları (mantık şemaları — yazılım katmanı)

| # | Senaryo | Tetik | Sistem tepkisi |
|---|---|---|---|
| A1 | İHA↔İKA/YKS bağlantı kaybı | HEARTBEAT zaman aşımı | İHA: aktarımı tekrar dener + yedek RF kanala geçer; İKA: hareket halindeyse GÜVENLİ DURMA, rota önbelleği korunur; bağlantı dönerse kaldığı wp'den devam |
| A2 | Model güvenilir rota üretemedi | Sağlamlık süzgeci: <3 geçerli waypoint | Rota İKA'ya GÖNDERİLMEZ; İHA taramayı bir kez yineler; YKS'ye "TESPİT YOK" durumu düşer (yanlış yönlendirme > gecikme tercihi) |
| A3 | İKA rotadan sapma / engel teması | Konum-rota hatası eşiği veya sıfır ilerleme (watchdog) | Motorlar durdurulur → geri manevra → yerel yeniden planlama (A*); N denemede ilerleme yoksa GÜVENLİ DURMA + YKS uyarısı |
| A4 | Görev süresi yaklaşımı | Kronometre eşiği (İHA 15 dk / İKA 10 dk) | İHA: taramayı keser, aktarım+iniş fazına geçer; İKA: en yakın güvenli noktada durur (limit aşımı görevden daha maliyetli) |
| A5 | İşlemci/servis çökmesi (araç üstü) | systemd watchdog | Servis otomatik yeniden başlar; durum dosyadan kurtarılır (rota önbelleği + son wp); **gerçek donanımda doğrulandı** (RPi 5 kamera servisi, kablo çıkarma testi dahil) |
| A6 | Paraşüt otonom tetik arızası | Otopilot irtifa/dikey hız koşulu sağlanamadı | Çift tetikleme: YKS'den manuel paraşüt komutu (şartname: −50 puan, görev geçerli kalır — kırıma tercih edilir) |

[GÖRSEL: gorseller/ariza_mantik.png — A1/A2/A3 karar ağaçları]
