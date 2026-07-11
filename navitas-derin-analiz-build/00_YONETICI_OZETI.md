# Yönetici Özeti

Navitas, afet sonrası 50×50 m görev alanında İHA görüntüsünden üç güzergâhtan açık olanı bulup İKA'ya iletmeyi amaçlayan, YOLOv8-seg tabanlı bir TEKNOFEST İleri Otonom Sistemler projesidir. Depoda eğitim/dataset araçları, PyTorch ve NCNN model artefaktları, gerçek kamera/video algısı, Gazebo Classic simülasyonu, UDP/seri haberleşme prototipi, Raspberry Pi canlı yayın sistemi ve DDR belgeleri bulunuyor.

Projenin en olgun kısmı görüntü işleme prototipidir. Güncel v2 PyTorch modeli ve onunla ilişkili NCNN export'u mevcut; gerçek görüntü/video üzerinde üretilmiş algı çıktıları da var. Buna karşılık metrik, model kimliği ve sistem seviyesi başarı iddiaları aynı güven düzeyinde değil. V2 eğitim notebook'u kayıtlı çıktı taşımıyor; dolayısıyla v2'nin mAP/precision/recall değerleri depodan tekrar doğrulanamıyor. DDR ve simülasyon loglarında kullanılan `mAP50=0.619` değeri v1 RescueNet modeline aittir, v2'ye değil.

En kritik teknik gerçek şudur: sistemin nihai “sol/orta/sağ” kararı YOLO'nun doğrudan sınıf çıktısı değildir. YOLO yalnız `traversable` ve `blocked` maskeleri üretir. Kod daha sonra traversable maskesini morfolojik olarak temizler, en büyük bağlı bileşeni seçer, koridorun üst bandının centroid'ini üç bölgeden birine atar ve distance transform ile waypoint üretir. Bu yüzden model mAP'i ile görev başarısı farklı ölçümlerdir.

Depoda üç farklı NCNN ağırlığı vardır. `models/navitas_seg_v2_ncnn_model` güncel v2'dir. `models/rescuenet_seg_v1_ncnn_model` v1'dir. README'nin “aktif” dediği `models/best_ncnn_model` ise ikisinden farklı bir ağırlıktır ve güncel v2 değildir. Varsayılan doğruluk testi de v1'i seçmektedir. Yanlış modelle test/deployment riski yüksektir.

Mevcut açık-yol doğruluk testi çalışır bir ölçüm setine bağlı değildir: test görselleri `1.png...12.png` biçimindeyken label JSON'ları `P001`, `E001`, `H001`, `TA01` gibi kimlikler bekler. Test tüm görselleri atlar. Ayrıca test kodu aynı görsellerde iki kez inference yapar ve “confidence” olarak YOLO confidence'ını değil seçilen koridorun piksel yoğunluğunu raporlar.

Gerçek video sonuçları modelin alan uyumu konusunda uyarıcıdır. 10.447 karelik bir videoda karelerin %85,5'inde yol bulunamamış; başka bir 9.532 karelik videoda “tespit yok” %33,0 ve sol/orta/sağ kararları geniş biçimde dağılmıştır. Etiketli ground truth bulunmadığı için bunlar doğruluk değildir; ancak karar kararlılığı ve domain shift riskini gösterir.

Simülasyonun iki ayrı doğruluk seviyesi vardır. `iha_perceive` ve `iha_haritala` gerçek modeli çalıştırır. Fakat `mission_demo` ve `iha_detect_send` açık yolu doğrudan `arena.open_road()` ground-truth'undan alır. Bu akışlar algı doğrulaması değil haberleşme/navigasyon demosudur. DDR'deki “zincirin bütünü yalnız kamera/model çıktısıyla uçtan uca doğrulandı” ifadesi ancak belirli v15 haritalama akışı için kısmen desteklenir; tüm demo ve kayıtlar için genellenemez.

Haberleşme katmanında newline-delimited JSON, artan sequence, ACK, tekrar gönderim ve timeout bulunmaktadır. Fakat mesajlarda CRC/checksum, kimlik doğrulama, şifreleme veya replay koruması yoktur. Saha seri modunda ACK bekleme özellikle kapatılmıştır. HEARTBEAT mesaj tipi ve birim testi vardır; düzenli heartbeat gönderen üretim döngüsü görev haberleşmesinde görünmemektedir. “Veri bütünlüğü ve güvenliği” iddiası bu haliyle sınırlıdır.

README/DDR ile kod arasında başka önemli ayrımlar vardır: A* anlatımı referans belgede bulunurken aktif İKA navigasyonu önceden üretilmiş arena waypoint'lerini takip eder; GNSS+IMU+enkoder füzyonu plan olarak belgelenmiştir fakat aktif kodda yoktur; görev verisi MAVLink değil özel JSON protokolüdür; geliştirme telsizi 433 MHz, bazı raporlarda şartname gereği 915 MHz yazılmıştır; Jetson/TensorRT desteği hedeftir, depoda TensorRT artefaktı yoktur.

Kökteki `2026_TEKNOFEST_TYDA_SARTNAME_Ucuncu_Senaryo_TR_2_NoDue.pdf` dosyasının adı bu projeye uygun görünse de içeriği “Yapay Zekâ Dil Modelleri/Ajanları” yarışmasına aittir. Navitas'ın resmi İleri Otonom Sistemler görev şartnamesi değildir ve gereksinim kaynağı olarak kullanılmamalıdır.

Genel hüküm: proje güçlü bir Ar-Ge prototipi ve etkileyici bir entegrasyon iskeletidir; ancak yarışma kanıt paketi henüz üretim/kalifikasyon seviyesinde değildir. Öncelik yeni özellik değil, doğru model kimliği, bağımsız etiketli test seti, v2 validation metriklerinin yeniden üretilmesi, `.pt`–NCNN parity testi ve ground-truth kullanmayan tek bir resmi uçtan uca test koşusudur.
