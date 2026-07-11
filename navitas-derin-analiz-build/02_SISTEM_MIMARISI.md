# Sistem Mimarisi ve Veri Akışı

## Gerçek algı zinciri

```text
Kamera/resim/video
  -> en-boy oranı korunarak kare letterbox (sim: 1024)
  -> karanlık kontrolü (LAB L ortalaması)
  -> gerekirse raw ve gamma+CLAHE yarışması
  -> YOLOv8n-seg, conf tabanı 0.05
  -> istenen eşikte maskeleri filtrele; traversable yoksa 0.05 fallback
  -> aynı sınıftaki instance maskelerini OR ile birleştir
  -> morfolojik open/close
  -> en büyük bağlı traversable bileşeni
  -> üst %30 band centroid'i -> sol/orta/sağ
  -> distance transform -> sekiz banda kadar waypoint
```

`blocked` maskesi çizilir fakat nihai yol seçiminde kullanılmaz. Dolayısıyla model molozu iyi tespit etse bile bu bilgi seçim fonksiyonuna doğrudan girmez; tersine traversable yanlış pozitifi açık yol kararı üretebilir.

Kodun `confidence` değeri YOLO detection confidence değildir. Üst bant piksellerinin seçilen üçte-birde kalan oranıdır. Bu, geometrik karar netliği olarak adlandırılmalıdır.

Karanlık görüntüde raw ve normalize kopyadan “daha çok traversable piksel üreten” seçilir. Daha çok alanın daha doğru olduğu garanti değildir; bu seçim false-positive'i ödüllendirebilir. Karanlık test seti olmadan güvenli olduğu söylenemez.

## Haritalama

Gazebo tarama kareleri, kaydedilmiş pose ile yaklaşık yer ayak izine ölçeklenip 56 m'lik mozaik üzerine yapıştırılır. Kareler homografi/özellik eşleme yerine ideal kamera irtifası, HFOV ve yaw üzerinden yerleştirilir. Son gelen kare öncekinin üstüne yazar; seam blending, lens distortion düzeltmesi ve poz belirsizliği modeli yoktur. Bu simülasyonda yeterli olabilir, gerçek sahada kalibrasyon gerektirir.

Mozaik waypoint'lerinin yerel metreye çevrilmesi mevcut olsa da canlı tek-kare `generate_ika_map()` yalnız görsel koordinatlı bir görselleştirmedir; gerçek GNSS/world rota değildir.

## Haberleşme

OPEN_ROUTE şeması: sürüm, yol no/etiket, geometrik güven, referans XY, yerel waypoint'ler, seq ve epoch zamanıdır. Newline JSON hem UDP hem seri için kullanılır. İHA UDP'de hedef başına tekrar gönderir ve ACK toplar.

Sınırlar:

- Şema doğrulaması yok; alıcı `v`, tip, road aralığı, waypoint limitleri veya sayısal NaN kontrolü yapmaz.
- CRC/checksum/HMAC/şifreleme yok.
- Sequence var ama alıcı eski/tekrar mesajı reddetmez; replay/out-of-order koruması yok.
- FrameReader buffer'ı üst sınırsız büyüyebilir ve maksimum frame boyutu yoktur.
- Serial modunda adres olmadığı için ACK gönderilmez ve `wait_ack=False` seçilir; havadayken teslim doğrulaması yoktur.
- HEARTBEAT üreticisi ve test senaryosu vardır, ancak görev uygulamasında periyodik heartbeat döngüsü bütünleşmiş değildir.

## Navigasyon

Aktif sim navigasyonu gerçek A* occupancy-grid planlaması yapmaz. Haberleşmeden gelen `road` değeri alınır ve `arena.route_waypoints(road)` ile önceden bilinen geometrik yol takip edilir. OPEN_ROUTE içindeki waypoint/ref_xy alanları `ika_nav` tarafından kullanılmaz. GNSS/IMU/enkoder füzyonu da yoktur; pose, Gazebo `gz model -p` ground-truth konumundan okunur. Bu nedenle sim navigasyonu hareket kontrolü demosudur, saha konumlama ve yeniden-planlama kanıtı değildir.

## Simülasyon doğruluk sınıfları

- `mission_demo.py` ve `iha_detect_send.py`: açık yol doğrudan `arena.open_road()` ground-truth; algı testi değildir.
- `iha_perceive.py`: gerçek model, tek görüntü/video algısı.
- `iha_haritala.py`: sim kamera kareleri + pose mozaiği + gerçek model; en güçlü algı entegrasyon kanıtı.
- `hakem_log.py`: bazı log satırlarında A*, GNSS/IMU/encoder ve v1 mAP değerlerini fiili işlem olmuş gibi yazar; bu log metni kendi başına uygulama kanıtı değildir.
