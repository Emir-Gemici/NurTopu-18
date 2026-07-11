# Bölüm 1 — Özete eklenecek OTONOMİ / YAZILIM paragrafı

> Bölüm 1'in tamamı (İHA/İKA/mancınık konfigürasyon karşılaştırmaları,
> metrikli değerlendirme) takım genelinde yazılacak; aşağıdaki paragraf özetin
> "otonom sistem mimarisi" kısmına yapıştırılmak üzere hazırdır.

Sistemin otonomi omurgası, uçtan uca doğrulanabilir tek bir veri zinciri olarak
tasarlanmıştır: mancınıkla fırlatılan sabit kanatlı İHA, 30 m irtifadan 50×50 m
görev alanını serpantin desenle tarar; 1 Hz nadir kamera kareleri, çekim
anındaki araç pozuyla birleştirilerek kuzey referanslı bir ortomozaik saha
haritasına dönüştürülür. YOLOv8 tabanlı segmentasyon modeli (gerçek afet
görüntüleriyle eğitilmiş; v1 doğrulamasında geçilebilir zemin sınıfında 0,874 mAP50; v2 genel 0,595) açık
güzergâhı bu harita üzerinde tespit eder; koridor merkez hattından üretilen
rota, sağlamlık süzgecinden geçirilip başlangıç referans noktalı yerel
koordinatlar hâlinde, ACK'li ve tekrar-gönderimli hafif bir JSON protokolüyle
İHA havadayken İKA ve yer istasyonuna aktarılır. İKA, İHA yere indikten sonra
bu koordinat haritasını GNSS+IMU+enkoder füzyonuyla kendi çerçevesine oturtarak
hedef bölgeye tam otonom ilerler. Zincirin bütünü, fizik tabanlı Gazebo
simülasyonunda "dürüst test" ilkesiyle (gizli açık yol; algı yalnızca İHA'nın
kendi kamerasından; İKA yalnızca modelin ürettiği rotayı sürer) uçtan uca
doğrulanmış; haberleşme ve araç üstü yazılım dayanıklılığı gerçek donanımda
(Raspberry Pi 5 üzerinde kesinti-toparlanmalı canlı görüntü servisi) test
edilmiştir. Bu mimari, görev başarısını tek bir alt sisteme değil; algı,
haberleşme ve navigasyon katmanlarının her birinde ölçülebilir kabul
kriterlerine bağlamaktadır.
