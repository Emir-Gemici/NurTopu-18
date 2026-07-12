# Bölüm 5 — Gereksinim İzlenebilirliği (YAZILIM İSTERLERİ satırları)

> Şablon isteri: MoC (Means of Compliance) metodolojisi — her ister için
> doğrulama yöntemi (Analiz / Test / Muayene / Demonstrasyon), durum ve kanıt.
> Aşağıdaki tablo YAZILIM/ALGI/HABERLEŞME isterlerini kapsar; mekanik/aviyonik
> isterlerini ilgili birimler aynı formatta ekleyecek. ⚠️ Resmî şartname PDF'i
> (V2 — 12.07'de repoya eklendi) REQ numarası İÇERMEZ; REQ numaraları T3KYS'te
> paylaşılan ayrı gereksinim setinden gelir ve o liste repoda yok. Eski "REQ-__"
> satırları 12.07'de şartname madde referanslarıyla dolduruldu; resmî numaralı
> set temin edilince numaralar birebir eşlenmeli. "(ÖDR hedefi)" etiketli sayısal
> eşikler şartnamede geçmez — takımın kendi kabul kriterleridir.
> Rapora ayrıca karşılanan/süren/karşılanmayan dağılımı pasta grafiği eklenmeli
> (şablon açıkça istiyor).

| REQ | Gereksinim (özet) | MoC | Doğrulama faaliyeti | Durum | Kanıt |
|---|---|---|---|---|---|
| REQ-19/20 | Tam otonom görev icrası (insan müdahalesi yalnız İKA başlatma) | Demonstrasyon | Simülasyon uçtan uca görev koşusu; saha provası planlı | Sürüyor (sim tamam, saha bekliyor) | Sim görev videosu + hakem logu |
| REQ-13 | Açık yol tespiti < 60 s (ÖDR hedefi; şartname süre vermez) | Test | Tarama sonrası tespit süresi ölçümü | Sürüyor | Sim: tarama ~25 s + çıkarım saniyeler; Jetson ölçümü planlı |
| REQ-13/15 | Güzergah tespiti toplam < 5 dk (ÖDR hedefi) | Test | Görev kronometresi (fırlatma→aktarım) | Karşılandı (sim) | Sim süre raporu (~2–3 dk) |
| REQ-15 | Veri aktarım doğruluğu > %95 (ÖDR hedefi; şartname şartı: akış kesilir/hakem teyit edemezse uçuş geçersiz, §6.4) | Test | seq/ACK sayımıyla paket başarı ölçümü | Sürüyor | UDP+433 MHz testleri tamam; saha menzil ölçümü planlı |
| Şartname §2.2.3/§6.4 | Haberleşme menzili 300 m (İHA-UB 300×300 m boyutundan türetildi), gecikme < 100 ms (ÖDR hedefi) | Test | Saha menzil testi | Planlandı | Test programı Bölüm 4 |
| REQ-22/23/24 | Telemetri ≤ 200 ms güncelleme ile YKS'ye (ÖDR beyanı; şartname "gerçek zamanlı" der) | Test + Muayene | Telemetri akış hızı logu | Sürüyor | Sim telemetri 1 Hz + canlı yayın testi; saha doğrulaması planlı |
| REQ-19 | İKA'nın İHA verisiyle otonom navigasyonu (görü haritası olmadan koordinatla) | Demonstrasyon | Referans-noktalı rota aktarımı + takip | Karşılandı (sim) | Referans-noktalı OPEN_ROUTE aktarımı UDP üzerinde doğrulandı; İKA'nın rotayı sürüşü (sim) |
| REQ-4 | İKA'nın HB'ye ≤ 10 dk ulaşması | Test | Görev kronometresi | Karşılandı (sim ~1–2 dk) | Sim süre raporu |
| Şartname §2.2.5/§6.2 | İKA İHA inişinden önce hareket etmemeli ("İHA yere temas etmeden İKA hareket edemez") | Muayene + Demonstrasyon | Yazılım kilidi (iniş teyidi + manuel başlat) | Karşılandı | Kod muayenesi + sim davranışı |
| Takım hedefi (REQ-13'ü destekler) | Segmentasyon başarımı (takım hedefi mAP50 ≥ 0,60) | Test | Val seti metrik ölçümü | **Karşılandı (v3: 0,627)** | v3: 0,627 — traversable 0,852 / blocked 0,403 (12.07.2026, model SHA kayıtlı; results/v3_test_20260712); önceki: v1 0,619 / v2 0,595 (results/v2_val_20260711) |
| Türetilmiş ister (Şartname §6.4'ten) | Arıza emniyet: bağlantı kaybında güvenli durma | Test | HEARTBEAT kesme simülasyonu | Sürüyor | Protokol + bağlantı-kaybı failsafe birim testleri tamam; araç üstü tatbikat planlı |
| Türetilmiş ister (Şartname §6.2'den — hands-off sonrası müdahale cezalı, tekrar fırlatmada yalnız "yeniden başlatma" serbest) | Araç üstü yazılımın kesinti sonrası kendiliğinden toparlanması | Demonstrasyon | Güç/kablo kesme tatbikatı | Karşılandı (İKA işlemcisi) | RPi 5 systemd servisi gerçek donanım testi |

**Özet dağılım (yazılım isterleri):** Karşılandı: 6 · Doğrulama sürüyor: 5 ·
Planlandı: 1 (dağılım aşağıdaki grafikte verilmiştir; segmentasyon v3 sonucuyla
12.07'de "Karşılandı"ya geçti — pasta grafiği buna göre yenilenmeli).

**Metodoloji cümlesi (rapora):** Doğrulama yaklaşımı MoC metodolojisini esas alır;
her ister Analiz/Test/Muayene/Demonstrasyon yöntemlerinden en az biriyle
eşlenmiş, kanıtlar sürümlenmiş depo çıktılarıyla (test logları, videolar,
metrik raporları) ilişkilendirilmiştir. Henüz karşılanmayan isterler için
planlanan doğrulama faaliyeti ve dönem Bölüm 4 test programında verilmiştir.
