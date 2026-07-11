# Aviyonik & Yazılım — DDR Bölüm 3.3 Referansı

## Sistem Mimarisi (Diagrama göre — DDR B.3.3.1)
```
YKİ/YKS
├─ Görev izleme
├─ Hakem Onay Paneli
├─ Telemetri Görüntüleme
└─ Veri Kaydı
    ↕ 433 MHz SiK Radio V3 · MAVLink/UDP · 915→433 MHz BTK uyumlu

İHA (Sabit Kanatlı)
├─ Pixhawk 6X (Autopilot · PX4/APM)
├─ Jetson Orin NX (YOLOv8 · TensorRT)
├─ Holybro M10 GPS (GNSS · Konum)
├─ Geniş açı kamera (Rota tespiti verisi)
├─ Aspilsan A28 LiPo batarya
└─ SiK Radio V3 (433 MHz · BTK uyumlu)
    ↓ Güzergah verisi

İKA (Diferansiyel Sürüş)
├─ Raspberry Pi 5 (Ana bilgisayar)
├─ BTS7960B x2 (Motor sürücü)
├─ KGX38 x4 Motor (Enkoder entegre)
├─ MPU6050 IMU (EKF ham veri)
├─ GNSS Modülü (Konum füzyon)
└─ SiK Radio V3 (433 MHz · Kara)
```

## Güç Tüketim Tablosu (DDR REQ-38 için taslak)
| Bileşen | Voltaj (V) | Ortalama Akım (A) | Peak Akım (A) | Güç (W) |
|---------|-----------|-------------------|---------------|---------|
| Jetson Orin NX | 12 | 2.5 | 5.0 | 30/60 |
| Pixhawk 6C | 5 | 0.25 | 0.5 | 1.25 |
| Arducam IMX477 | 5 | 0.3 | 0.5 | 1.5 |
| Holybro M10 GPS | 5 | 0.1 | 0.2 | 0.5 |
| SiK Radio 433 | 5 | 0.1 | 0.5 | 0.5/2.5 |
| TBS Crossfire | 5 | 0.2 | 0.3 | 1.0 |
| 4x Servo (kanat) | 5 | 0.1×4 | 0.5×4 | 0.4/2.0 |
| Paraşüt Servo | 5 | 0.05 | 1.0 | 0.25/5.0 |
| Mauch PL-100 | - | 0.02 | 0.02 | - |
| Motor (SunnySky) | 14.8 | 15→30 (uçuş) | 40 | 222/592 |
| **Aviyonik toplam** | 5-12 | ~3.5 | ~8.0 | ~35 |
| **Motor toplam** | 14.8 | ~15 | 40 | ~222 |

> Not: Tüm değerler tahmini. DDR için datasheet değerleriyle doğrulanmalı.

## Batarya Hesabı (DDR REQ-39 için taslak)
```
Pil: 4S LiPo/Li-ion, 14.8V, ~14000 mAh
Görev süresi: 15 dk = 0.25 saat

Motor tüketimi:
  Tırmanış (2 dk, 30A): 30A × (2/60)h = 1.0 Ah
  Seyir (13 dk, 15A):   15A × (13/60)h = 3.25 Ah
  Motor toplam: ~4.25 Ah

Aviyonik tüketimi:
  3.5A (sistem) × 15V BEC verimi %85 = 4.1A eq.
  4.1A × 0.25h = ~1.0 Ah
  
Toplam tüketim: ~5.25 Ah
%20 güvenlik marjı: 6.3 Ah → 14000 mAh yeterli ✓

C-rating kontrolü:
  Peak akım: 40A (motor) + 8A (aviyonik BEC) = ~48A
  Gerekli C: 48A / 14Ah = 3.4C → 10C+ pil yeterli ✓
```

## Güzergah Tespit Algoritması (DDR REQ-40 için akış şeması içeriği)
```
[Kamera] → [Frame buffer] → [YOLOv8-seg nano NCNN]
    ↓
[Segmentasyon maskesi] → [Güven skoru filtresi (conf>0.40)]
    ↓
[Morfolojik işlem] → [Grid dönüşümü (50×50)]
    ↓
[Güzergah sınıflandırması: Kolay/Orta/Zor]
    ↓
[Haberleşme: MAVLink/UDP → YKİ + İKA]
    ↓
[Hakem onayı] → [Paraşüt komutu + İKA tetikle]
```

## Arıza Emniyet Senaryoları (DDR B.3.3.1)
| Senaryo | Tetik | Failsafe Aksiyonu |
|---------|-------|-------------------|
| İletişim kaybı (İHA↔YKS) | >3s heartbeat yok | RTH veya güvenli bölgede loiter |
| GPS kaybı | Fix yok | Barometer hold + RC override bekleme |
| Düşük batarya | <15% | RTH + otonom paraşüt |
| Görüntü işleme timeout | >30s sonuç yok | Manuel hakem onayı modu |
| İKA iletişim kaybı | >5s yok | Bekle + son güzergah ile devam |

## EMI/EMC Önlemleri (DDR B.3.3.3)
- ESC → Motor kabloları burulmuş (twisted pair) veya örgülü
- Telemetri anteni motor/ESC'den min 5cm uzakta
- Jetson + Pixhawk arası shielded kablo (USB → UART converter değil, doğrudan JST-GH)
- LiPo'dan Jetson'a ayrı regülatör hattı (ortak GND, ayrı rail)
- GPS modülü motor gürültüsünden uzak, üst yüzeyde

## Kablaj Hesabı Taslak (DDR REQ-37)
| Hat | Max Akım | AWG | Konnektör |
|-----|----------|-----|-----------|
| Ana güç (pil→PDB) | 40-50A | 12 AWG | XT90 |
| ESC → Motor | 30-40A | 14 AWG | Banana 3.5mm |
| BEC çıkışı (servo/aviyonik) | 5-8A | 20 AWG | JST-XH / XT30 |
| Jetson güç | 5A@12V | 20 AWG | DC barrel |
| Pixhawk power | 2A@5V | 24 AWG | JST-GH |
| Veri hatları | <0.5A | 26-28 AWG | JST-GH |
