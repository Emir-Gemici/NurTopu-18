# Bulgular ve Öncelikler

## Kritik

1. V2 modeli için doğrulanabilir validation metrikleri yok; v1 metrikleri v2 loglarına taşınmış.
2. Resmi test kodu varsayılan v1 modeli seçiyor ve mevcut görsel adları label'larla eşleşmiyor.
3. README'nin aktif dediği `best_ncnn_model` güncel v2 değil; yanlış deployment riski.
4. Bazı “uçtan uca” simülasyonlar model yerine ground-truth kullanıyor; test iddiası ayrıştırılmalı.
5. Kök şartname PDF'si yanlış yarışmaya ait.

## Yüksek

6. İKA navigasyonu OPEN_ROUTE waypoint'lerini tüketmiyor; arena'nın bilinen rotasını kullanıyor.
7. A*, GNSS/IMU/enkoder füzyonu ve gerçek MAVLink görev aktarımı belgede var, aktif uygulamada yok.
8. Haberleşmede CRC/auth/replay koruması yok; serial modda teslim ACK'i yok.
9. Blocked maskesi yol kararında kullanılmıyor.
10. V2 dataset provenance/hash ve eğitim çıktıları eksik; tekrar üretilebilirlik zayıf.
11. Açık metin cihaz/Wi-Fi/SSH parolaları dokümantasyonda bulunuyor.

## Orta

12. 512 merkezi crop, 1024 letterbox ve RPi/sim pipeline'ları farklı.
13. Karanlık normalizasyonda “en çok traversable” seçimi false-positive üretebilir.
14. Geometrik confidence model confidence gibi sunuluyor.
15. Test iki kez inference yapıyor; batch detection rate doğruluk değil.
16. Dataset YAML mutlak yol; requirements sürümleri sabit değil.
17. Notebook `hits[0]` ile yanlış checkpoint seçebilir.
18. FrameReader boyut limiti ve şema validasyonu yok.

## Önerilen sıra

P0: tek model manifesti (`model_id`, hash, dataset hash, git commit, Ultralytics sürümü), v2 val yeniden ölçümü, test görsel-label eşleşmesi, resmi model yolunu tekleştirme.  
P1: ortak inference modülü; PT/NCNN parity; blocked-aware yol skoru; waypoint'lerin İKA tarafından tüketimi; ground-truth'suz E2E.  
P2: haberleşme CRC+şema+replay/timeout; periyodik heartbeat; gerçek 433/915 saha benchmark'ı.  
P3: gerçek sensör füzyonu/A*, Jetson TensorRT, saha veri toplama ve calibration.
