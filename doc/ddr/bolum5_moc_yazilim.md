# Bölüm 5 — Gereksinim İzlenebilirliği (YAZILIM İSTERLERİ satırları)

> Şablon isteri: MoC (Means of Compliance) metodolojisi — her ister için
> doğrulama yöntemi (Analiz / Test / Muayene / Demonstrasyon), durum ve kanıt.
> Aşağıdaki tablo YAZILIM/ALGI/HABERLEŞME isterlerini kapsar; mekanik/aviyonik
> isterlerini ilgili birimler aynı formatta ekleyecek. ⚠️ REQ numaraları takımın
> şartname özetinden (navitas-teknofest/references) eşlendi; resmî gereksinim
> setiyle SON KONTROL yapılmalı. "REQ-__" kalan 4 satır resmî listeden doldurulacak.
> Rapora ayrıca karşılanan/süren/karşılanmayan dağılımı pasta grafiği eklenmeli
> (şablon açıkça istiyor).

| REQ | Gereksinim (özet) | MoC | Doğrulama faaliyeti | Durum | Kanıt |
|---|---|---|---|---|---|
| REQ-19/20 | Tam otonom görev icrası (insan müdahalesi yalnız İKA başlatma) | Demonstrasyon | Simülasyon uçtan uca görev koşusu; saha provası planlı | Sürüyor (sim tamam, saha bekliyor) | Sim görev videosu + hakem logu |
| REQ-13 | Açık yol tespiti < 60 s | Test | Tarama sonrası tespit süresi ölçümü | Sürüyor | Sim: tarama ~25 s + çıkarım saniyeler; Jetson ölçümü planlı |
| REQ-13/15 | Güzergah tespiti toplam < 5 dk | Test | Görev kronometresi (fırlatma→aktarım) | Karşılandı (sim) | Sim süre raporu (~2–3 dk) |
| REQ-15 | Veri aktarım doğruluğu > %95 | Test | seq/ACK sayımıyla paket başarı ölçümü | Sürüyor | UDP+433 MHz testleri tamam; 915 MHz saha ölçümü planlı |
| REQ-__ | Haberleşme menzili 300 m, gecikme < 100 ms | Test | Saha menzil testi | Planlandı | Test programı Bölüm 4 |
| REQ-22/23/24 | Telemetri ≤ 200 ms güncelleme ile YKS'ye | Test + Muayene | Telemetri akış hızı logu | Sürüyor | Sim telemetri 1 Hz + canlı yayın testi; saha doğrulaması planlı |
| REQ-19 | İKA'nın İHA verisiyle otonom navigasyonu (görü haritası olmadan koordinatla) | Demonstrasyon | Referans-noktalı rota aktarımı + takip | Karşılandı (sim) | Referans-noktalı OPEN_ROUTE aktarımı UDP üzerinde doğrulandı; İKA'nın rotayı sürüşü (sim) |
| REQ-4 | İKA'nın HB'ye ≤ 10 dk ulaşması | Test | Görev kronometresi | Karşılandı (sim ~1–2 dk) | Sim süre raporu |
| REQ-__ | İKA İHA inişinden önce hareket etmemeli | Muayene + Demonstrasyon | Yazılım kilidi (iniş teyidi + manuel başlat) | Karşılandı | Kod muayenesi + sim davranışı |
| Takım hedefi (REQ-13'ü destekler) | Segmentasyon başarımı (takım hedefi mAP50 ≥ 0,60) | Test | Val seti metrik ölçümü | Sürüyor (v1 karşıladı; v2 hedefin hemen altında) | v1: 0,619; v2: 0,595 (eğitim kaydı) — v3 iyileştirme planlı |
| REQ-__ | Arıza emniyet: bağlantı kaybında güvenli durma | Test | HEARTBEAT kesme simülasyonu | Sürüyor | Protokol + bağlantı-kaybı failsafe birim testleri tamam; araç üstü tatbikat planlı |
| REQ-__ | Araç üstü yazılımın kesinti sonrası kendiliğinden toparlanması | Demonstrasyon | Güç/kablo kesme tatbikatı | Karşılandı (İKA işlemcisi) | RPi 5 systemd servisi gerçek donanım testi |

**Özet dağılım (yazılım isterleri):** Karşılandı: 5 · Doğrulama sürüyor: 6 ·
Planlandı: 1 (dağılım aşağıdaki grafikte verilmiştir).

**Metodoloji cümlesi (rapora):** Doğrulama yaklaşımı MoC metodolojisini esas alır;
her ister Analiz/Test/Muayene/Demonstrasyon yöntemlerinden en az biriyle
eşlenmiş, kanıtlar sürümlenmiş depo çıktılarıyla (test logları, videolar,
metrik raporları) ilişkilendirilmiştir. Henüz karşılanmayan isterler için
planlanan doğrulama faaliyeti ve dönem Bölüm 4 test programında verilmiştir.
