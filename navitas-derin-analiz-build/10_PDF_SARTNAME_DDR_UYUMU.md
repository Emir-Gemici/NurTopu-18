# PDF, Şartname ve DDR Uyumu

## İncelenen PDF'ler

1. `2026_TEKNOFEST_TYDA_SARTNAME_Ucuncu_Senaryo_TR_2_NoDue.pdf`, 19 sayfa: içeriği Yapay Zekâ Dil Modelleri/Ajanları yarışmasıdır; vLLM, multimodal video ve ajan araçları ister. Navitas İleri Otonom Sistemler gereksinim kaynağı değildir.
2. `doc/DDR_Sablon_TR_BhrGu.pdf`, 17 sayfa: doğru İleri Otonom Sistemler DDR şablonu. Yazılım altyapısı, AI/ML prensibi, dataset/eğitim/başarı, haberleşme bütünlüğü, test ve MoC izlenebilirliği ister.
3. `doc/ddr/word/Navitas_DDR_Yazilim_v4.pdf`, 20 sayfa: takımın yazılım DDR taslağı.
4. `doc/...ÖDR_Şablonu...pdf`, 8 sayfa: takımın kavramsal/ön tasarım içeriği; bazı sayısal değerler hedef olmasına rağmen başarı gibi işaretlenmiştir.

## DDR uyum değerlendirmesi

Güçlü taraflar: mimari açıklama, teknoloji gerekçesi, dataset sınıfları, v1 metrik tablosu, hata senaryoları, test planı ve MoC tablosu mevcut. Şablonun yazılım başlıklarına biçimsel uyum iyi.

Kanıt açığı bulunan ifadeler:

- “Zincirin bütünü dürüst uçtan uca doğrulandı”: yalnız belirli haritalama akışında kısmi kanıt; demo scriptleri ground-truth kullanıyor.
- “GNSS+IMU+enkoder füzyonu/A*”: aktif kodda yok; sim pose ve arena waypoint'i kullanılıyor.
- “CRC/checksum”: protokol kodunda yok.
- “MAVLink görev verisi”: görev verisi özel newline JSON; MAVLink uçuş telemetrisi için plan.
- “915 MHz”: kod/donanım belgeleri 433 MHz test düzeneği söylüyor; 915 MHz saha testi yok.
- “>%98 aktarım doğruluğu, 300 m, <100 ms”: hedef; saha kanıtı yok.
- “27,6 FPS”: referans/skill belgesinde platform tanımı çelişkili; ham benchmark artefaktı yok.
- “v2 başarı oranı”: yok; verilen 0.619 v1'e ait.
- “Tam otonom”: uçuş kontrolü, paraşüt, saha sensör füzyonu ve gerçek İKA entegrasyonu tamamlanmış kod/kanıtla desteklenmiyor.

DDR'de hedef, plan, simülasyon sonucu ve gerçek donanım sonucu ayrı sütunlarda gösterilmeli; gelecek zamanlı kabiliyetler “karşılandı” yapılmamalıdır.
