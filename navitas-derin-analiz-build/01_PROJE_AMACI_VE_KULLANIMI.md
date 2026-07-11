# Proje Amacı, Kullanımı ve Teknolojiler

## Amaç ve görev akışı

Tasarlanan görev: sabit kanatlı İHA'nın mancınıkla fırlatılması, HTAB üzerindeki üç güzergâhı görüntülemesi, iki kapalı güzergâh arasındaki açık güzergâhı belirlemesi, bu bilgiyi havadayken YKS/İKA'ya iletmesi, paraşütle inmesi ve İKA'nın hedef bölgeye otonom ilerlemesidir.

Kodda öngörülen kullanım katmanları:

1. Dataset scriptleri RescueNet/FloodNet verisini YOLO segmentasyon formatına çevirir.
2. `codes/train_seg.py`, YOLOv8n-seg modelini eğitir ve NCNN export eder.
3. `simulation/scripts/iha_perceive.py` gerçek resim/video üzerinde modeli çalıştırır.
4. `iha_haritala.py`, Gazebo tarama karelerini 1024×1024 kuzey-yukarı mozaikte birleştirir ve modelden rota çıkarır.
5. `comms/` OPEN_ROUTE mesajını UDP veya transparan seri üzerinden gönderir.
6. `ika_nav.py`, simülasyonda seçilen yolun arena waypoint'lerini diferansiyel sürüş komutlarına dönüştürür.
7. `drone/` Raspberry Pi kamera görüntüsünü ham H.264 ve AI-overlay UDP akışlarıyla laptopa taşır.

## Teknoloji envanteri ve gerçek kullanım düzeyi

| Teknoloji | Projedeki gerçek rol | Durum |
|---|---|---|
| Python 3 | Eğitim, inference, dataset, sim orkestrasyonu, haberleşme | Aktif |
| Ultralytics 8.4.x | YOLOv8-seg eğitim/export/inference | Aktif |
| PyTorch | `.pt` model runtime ve eğitim altyapısı | Aktif |
| NCNN | ARM/RPi için 512×512 export | Aktif artefakt mevcut |
| OpenCV/NumPy | Maske, CLAHE, morfoloji, waypoint, video | Aktif |
| Gazebo Classic (`gz`) | Dünya, kamera, araç hareketi, kayıt | Aktif; modern Gazebo/ROS2 değil |
| C++/CMake | Gazebo animasyon ve tarama kamera plugin'leri | Aktif |
| UDP + JSON | OPEN_ROUTE/ACK ve canlı video/telemetri prototipi | Aktif |
| Transparan seri/SiK | Saha taşıyıcısı hedefi | Kod mevcut; menzil kanıtı yok |
| Raspberry Pi 5/Picamera2/ffmpeg | Kamera + AI canlı yayın | Gerçek donanım denemesi belgeli |
| Jetson Orin NX/TensorRT | İHA hedef deployment'ı | Plan; artefakt ve benchmark yok |
| MAVLink/PX4/Pixhawk | Uçuş kontrolü/telemetri hedefi | Belgede var; görev verisi kodu MAVLink değil |
| ROS | README/dizin anlatımında geçiyor | Aktif Python akışında belirgin değil |
| A* | Referans dokümanda örnek algoritma | Aktif navigasyonda gerçek A* bulunmuyor |
| GNSS+IMU+enkoder füzyonu | İKA konumlama hedefi | Plan; aktif füzyon kodu yok |
| Docker/Podman container | Gazebo kayıt ortamı | Containerfile ve scriptler mevcut |
| Google Colab | V2 GPU eğitimi | Notebook mevcut, outputs temizlenmiş |
| RescueNet/FloodNet | Segmentasyon eğitimi | Dönüştürücüler mevcut; ham dataset repoda yok |

## Kurulum ve kullanım sorunları

- Global Python 3.14 ortamında paketler görünmezken repo içindeki `.venv` içinde Ultralytics 8.4.76, Torch 2.12.1, OpenCV 4.13, NumPy 2.5 ve NCNN kuruludur. Dokümanlar hangi Python'ın kullanılacağını net zorlamıyor.
- `codes/requirements_rpi.txt` yalnız üç satırdır ve sürümler sabitlenmemiştir; tekrar üretilebilir kurulum sağlamaz.
- Dataset YAML'ı `/home/trs/trs/github/navitas/dataset` mutlak yoluna bağlıdır.
- README eski merkezi-crop/512 pipeline'ını anlatırken güncel sim algısı letterbox/1024 kullanır; RPi canlı akışı 512 kullanır.
- RPi kurulum dokümanında sabit kullanıcı, IP ve açık metin Wi-Fi/SSH parolası bulunmaktadır. Bunlar yayınlanabilir depo için güvenlik borcudur.
