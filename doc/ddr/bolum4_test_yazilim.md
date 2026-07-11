# Bölüm 4 — Test Faaliyetleri (YAZILIM / ALGI / HABERLEŞME / SİMÜLASYON kısmı)

> Şablon isteri: her testin amacı + uygulanma yöntemi + başarı kriteri +
> gereksinim ilişkisi; YAPILMIŞ kabul testleri GÖRSELLERLE + sonuçlar;
> gelecek test programı. Mekanik/aviyonik testleri (motor itki, batarya,
> paraşüt açılma, mancınık) ekibin ilgili birimleri ekleyecek — buradaki tablo
> yazılım tarafının GERÇEKLEŞMİŞ testleridir.

## 4.x Gerçekleştirilen Yazılım/Algı/Haberleşme Testleri

| Test | Amaç | Yöntem | Başarı kriteri | Sonuç |
|---|---|---|---|---|
| Model doğrulama (val seti) | Segmentasyonun görev yeterliliği | Aynı 294 görüntülük doğrulama setinde standart mAP ölçümü; v2 için bağımsız yeniden ölçüm (11.07.2026, model SHA kayıtlı) | Mask mAP50 ≥ 0,60 | v1: 0,619 — hedef sağlandı; v2: 0,595 (traversable 0,868 / blocked 0,322) — v3 planlı; kanıt: results/v2_val_20260711 |
| Ölçek bağımsızlık | Kararın kamera çözünürlüğünden bağımsızlığı | Aynı sahne 0,6×–3,3× ölçeklerde işlendi | Tüm ölçeklerde aynı yol kararı | Başarılı (tek sapma: 410 px aşırı bulanık girdi — saha altı çözünürlük) |
| Işık dayanıklılığı | Gölge/loş ışıkta kararlılık | Gamma 2,2/3,0 karartma + gölge gradyanı sentetik varyantları | Karar değişmemeli | Başarılı — gamma 2,2 ve gölgede korunur; aşırı karanlık (gamma 3) sınır durumu — iyileştirme planlı |
| Haberleşme birim testi | Protokol çerçeveleme + ACK + tekrar gönderim + bağlantı-kaybı arıza emniyeti | UDP loopback üzerinde OPEN_ROUTE (referans noktası + yerel waypoint'ler) / HEARTBEAT / ACK alışverişi + bağlantı kesme-toparlanma senaryosu (test_comms) | Mesajlar bozulmadan iletilmeli; kesintide güvenli durma tetiklenmeli, dönüşte kaldığı noktadan devam | Başarılı — rota önbelleği kesintide korunuyor; 11.07.2026'da 3 ardışık koşuda geçti (test zamanlama marjı sağlamlaştırıldı) |
| Gerçek donanım canlı yayın | İKA işlemcisinde uçtan uca video + AI katmanı | RPi 5 + kamera, systemd servisi; kablolu ve kablosuz ağda paket kaybı ölçümü | Kesintisiz H.264 yayın + AI bindirme | Başarılı — kablolu %0 kayıp; kablosuz ~%17 (adaptif kalite modu eklendi); kamera kablosu çekme testinde servis kendini toparladı |
| Simülasyon uçtan uca görev | Tüm zincirin bütünleşik doğrulaması (SITL yaklaşımı) | Gazebo 11: mancınık→serpantin tarama→ortomozaik→model tespiti→rota aktarımı→İKA sürüşü→HB | Model GİZLİ açık yolu bulmalı, İKA HB'ye şartname süresinde ulaşmalı | Başarılı — model, İHA'nın kendi tarama mozaiğinde doğru yolu tespit etti; İKA rotayı izleyip HB'de durdu; süreler limit içinde |
| Fizik çarpışma testi | İKA'nın engelden GEÇEMEMESİ (gerçekçilik) | Simülasyonda sınırlı traksiyon kuvveti + katı moloz; duvara sürüş denemesi | Araç engel önünde durmalı, devrilmemeli | Başarılı — engel önünde durdu, gövde stabil |
| Gerçek dron video analizi | Boru hattının gerçek kamera görüntüsüyle mekanik doğrulaması | 2:15 dk gerçek uçuş videosu kare kare işlendi (~540 ms/kare) | Boru hattı çökmesiz, karar+rota üretimi çalışmalı | Başarılı — mekanik olarak çalıştı (içerik kapalı mekân olduğundan kararlar anlamlı değil — saha görüntüsü testi planlandı) |

## 4.y Test Metodolojisi Notu

Simülasyon testlerinde **dürüst zincir** ilkesi uygulanır: saha, modele
kapalı/gizli kurulur; algı yalnızca İHA'nın kendi kamera karelerinden çalışır;
İKA yalnızca İHA'nın ürettiği rotayı sürer. Model yanılırsa görev simülasyonda
da BAŞARISIZ sonuçlanır — böylece testler gerçek yarış riskini ölçer, maskelenmez.
Ayrıca 5 farklı gerçekçi saha düzeni (kıvrımlı 3'er yol, rastgele KB/HB
yerleşimi) üretilmiş olup her düzen otomatik geometri denetiminden geçirilir
(dümdüz koridor yasağı, yol ayrıklığı, başlangıç-hedef hizasızlığı).

## 4.z Gelecek Test Programı (yazılım)

| Test | Planlanan dönem | Başarı kriteri |
|---|---|---|
| Jetson Orin NX çıkarım FPS | Entegrasyon fazı | ≥15 FPS (TensorRT) |
| RPi 5 NCNN FPS ölçümü | Entegrasyon fazı | ≥10 FPS @512 |
| 915 MHz RF menzil + aktarım doğruluğu | Saha testleri | 300 m'de >%95 doğruluk, <100 ms gecikme |
| Gerçek saha (moloz benzeri) algı testi | Saha testleri | Açık yol doğru tespiti ≥%90 |
| Perspektif-augmentasyonlu model v3 eğitimi + regresyon | Entegrasyon fazı | Eğik açı senaryosunda karar kararlılığı |
| Tam görev provası (İHA+İKA+mancınık) | Faz 8–9 | 15 dk İHA + 10 dk İKA limitlerinde uçtan uca başarı |
