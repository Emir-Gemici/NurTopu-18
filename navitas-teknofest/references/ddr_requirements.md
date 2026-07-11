# DDR & Gereksinim Referansı

## Kritik Takvim
- **DDR Son Teslim: 15 Temmuz 2026** (21 gün kaldı — bugün 24 Haziran)
- DDR Sonuçları: 29 Temmuz 2026
- FDR: 21 Eylül 2026

## Takım Bilgileri
- Takım: Navitas Autonomous Systems
- ID: 997827 | Başvuru: 5329027
- Halil (Khalil Khattab Hamsho) — Görüntü işleme, Uçuş yazılımı, Sistem mimarisi

## DDR Puan Yapısı
| Bölüm | Konu | Puan |
|-------|------|------|
| 1 | Özet | 10 |
| 2 | Organizasyonel Yapı ve Proje Takvimi | 10 |
| 3 | Genel Sistem Spesifikasyonları | **60** |
| 4 | Test Faaliyetleri | 10 |
| 5 | Gereksinim İzlenebilirliği | 10 |

## DDR'ye Özgü Gereksinimler (REQ)
### Aviyonik / Yazılım (Halil'in Alanı)
- REQ-35: İHA ve İKA sistem mimarileri
- REQ-36: Aviyonik BOM listesi
- REQ-37: Kablaj ve konnektör hesapları
- REQ-38: Güç tüketim tabloları
- REQ-39: Batarya kapasite hesaplamaları
- REQ-40: Güzergah tespit algoritması akış şeması
- REQ-105: Yapısal malzeme dağılımı (DDR'de)

## Aviyonik BOM (Malzemeler Excel - Güncel)
| No | Bileşen | Model | Adet | Ağırlık(g) |
|----|---------|-------|------|------------|
| 1 | Autopilot | Pixhawk 6C | 1 | 59 |
| 2 | İşlemci | Jetson Orin NX + carrier + soğutucu | 1 | 180 |
| 3 | Kamera | Arducam IMX477 12MP | 1 | 50 |
| 4 | Pitot Tüpü | Pitot + silikon hortum | 1 | 10 |
| 5 | Airspeed | Holybro MS5525DSO | 1 | 20 |
| 6 | Telemetri (uçak) | Holybro SiK 433 MHz | 1 | 35 |
| 7 | GNSS | Holybro M10 GPS + Compass | 1 | 32 |
| 8 | RC Alıcı | TBS Crossfire Nano RX | 1 | 10 |
| 9 | Motor | SunnySky X2216 V3 1100KV | 2 | 138 |
| 10 | Servo (kanat/kuyruk) | EMAX ES08MA II | 4 | 48 |
| 11 | Pil | 4S 14000-15000 mAh Li-ion | 1 | 1000 |
| 12 | Paraşüt | Opale Rescue 2.5m² | 1 | 120 |
| 13 | Paraşüt Pod | Rescue Pod 2.5m² | 1 | 20 |
| 14 | Paraşüt Servo | EMAX ES08MA II | 1 | 60 |
| 15 | Paraşüt Mekanizması | Servo kontrollü kapak | 1 | 50 |
| 16 | Paraşüt Bağlantı | Nylon/Kevlar tether | 1 | 30 |
| 17 | ESC | Hobbywing FlyFun 40A V5 | 2 | 70 |
| 18 | Power Sensor | Mauch PL-100 | 1 | 22 |
| 19 | Pixhawk BEC | Mauch PL 4-6S BEC | 1 | 24 |
| 20 | Servo BEC | Matek BEC12S-PRO | 1 | 5 |
| 21 | Jetson Güç Reg | 12V 5A buck converter | 1 | 25 |
| 22 | PDB | Güç dağıtım kartı | 1 | 60 |
| 23 | Kablolama | XT60/XT90, JST-GH vb. | lot | 150 |
| 24 | Acil Kesme Şalterleri | Anahtarlı Stop + Röle | 1 | 30 |
| 26 | Telemetri (YKS) | Holybro SiK 433 MHz | 1 | 35 |
| 27 | Jetson SSD | NVMe M.2 250GB | 1 | 10 |
| **TOPLAM** | | | | **2293g** |

## Kritik Gereksinimler (Operasyonel)
- REQ-1: İKA ≤10 kg (yük hariç)
- REQ-3: İKA min 200g yük taşır
- REQ-5: İHA maks uçuş 15 dk
- REQ-6: Hazırlık ≤15 dk
- REQ-7: Sabit kanat zorunlu
- REQ-8: Mancınık fırlatma zorunlu
- REQ-9: Paraşüt iniş zorunlu
- REQ-13: HTAB'de güzergah tespiti
- REQ-15: Güzergah İKA'ya aktarılır
- REQ-16: Aktarım İHA inişinden önce
- REQ-19: İKA tam otonom
- REQ-20: İHA tam otonom (fırlatmadan inişe)
- REQ-25-31: Çift Acil Güç Kesme Anahtarı (İHA)
- REQ-32-34: Acil Güç Kesme Anahtarı (İKA)
- REQ-57: Modüler İHA tasarımı
- REQ-58: Mancınık ray geometrisi
- REQ-59: Çift kademeli emniyet
- REQ-137: T/W ≥ 0.20
- REQ-158: MTOW ≤ 25 kg
- REQ-185: Havada kalış ≥ 0.5 saat
- REQ-186: İniş dikey hız < 7 m/s
- REQ-188: Fırlatma sonrası ≥1.15 × V_stall

## DDR Gap Analizi — Ne Hazır, Ne Eksik
### ✅ ÖDR'den Taşınabilir / Hazır
- Özet (ÖDR'den güncellenecek)
- Organizasyon şeması
- Proje takvimi (güncelleme gerekli)
- Risk analizi (Bölüm 4'e uyarlanır)
- Sistem mimarisi diyagramı
- BOM listesi (Excel'den)
- Yazılım mimarisi özeti

### 🔴 DDR'de Yeni Gerekli (Kritik Eksikler)
**Uçuş Bilimleri (3.1)** — en ağır bölüm:
- Ağırlık & denge hesapları (CG koordinatları)
- Kısıt diyagramı (W/S, W/P)
- Kanat profili ve geometri (chord, span, AR)
- Gövde/kuyruk boyutlandırma
- Aerodinamik analiz (CFD veya yarı-ampirik)
- Kararlılık analizi (statik + dinamik)
- Uçuş zarfı (CS-VLA gust çizgileri)
- Performans hesapları (V_stall, V_max, endurance)
- Yük hesapları (limit ve nihai)

**Yapısal Analiz (3.2)**:
- FEM analizi (statik, burkulma, modal)
- Malzeme tablosu (mukavemet/ağırlık oranı)
- Mancınık enerji hesabı

**Aviyonik (3.3)** — Halil'in alanı:
- Detaylı güç tüketim tablosu (ortalama + peak current)
- Batarya hesabı (mAh, C-rating doğrulaması)
- Kablaj hesabı (AWG seçimi, XT60/90 doğrulaması)
- EMI/EMC önlemleri
- Arıza emniyet senaryoları (failsafe logic)
- Algoritma akış şeması (YOLOv8 → güzergah → İKA)

**Test Faaliyetleri (Bölüm 4)**:
- Yapılan testlerin görseli + sonucu
- Planlanan test takvimi
