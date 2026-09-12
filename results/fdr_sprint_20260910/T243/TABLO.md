# T243 — mesaj paket boyutu ve gerçek görev veri hızı (ÖLÇÜM)

> Bu dosya **üretilir** (`scripts/paket_boyutu_olc.py --kip tablo`); elle düzenlenmez. Her sayı `paket_boyutu.json` ya da `gorev_veri_hizi.json` dosyasından gelir.

- ölçüm: 2026-09-12T03:35:05 · Windows-11-10.0.26200-SP0 · Python 3.13.7
- ön kayıt: `results/fdr_sprint_20260910/T243/ON_KAYIT.md` · tohum 20260912
- taşıyıcı: UDP loopback 127.0.0.1 (ephemeral port). RF DEGILDIR: SiK 433 MHz hattinin veri hizi hala OLCULEMEDI.

## 1. Mesaj tipi başına çerçeve boyutu (N1)

`len(protocol.encode(msg))` — gerçek bayt. `t` ve `seq` genişliği sabitlendi (`t` = 1789000000.123, `seq` = 1000).

| `type` | asgari alanla (B) | örnek çerçeve (B) | örnek çerçevenin alanları |
|---|---:|---:|---|
| `OPEN_ROUTE` | 125 | 365 | `conf`, `label`, `ref_xy`, `road`, `seq`, `t`, `type`, `v`, `waypoints` |
| `NO_ROUTE` | 77 | 117 | `detay`, `sebep`, `seq`, `t`, `type`, `v` |
| `HEARTBEAT` | 70 | 273 | `alt`, `armed`, `bat`, `bat_yuzde`, `gps_fix`, `hiz`, `karar_yas`, `lat`, `lon`, `mod`, `node`, `pixhawk_canli`, `seq`, `t`, `type`, `uydu`, `v`, `x`, `y`, `yon` |
| `ACK` | 64 | 87 | `node`, `ref`, `ref_tip`, `t`, `type`, `v` |
| `CMD` | 80 | 124 | `cmd`, `hedef`, `oturum`, `seq`, `t`, `type`, `v` |
| `IHA_LANDED` | 71 | 71 | `node`, `seq`, `t`, `type`, `v` |

Örnek çerçeveler: `OPEN_ROUTE` üretim yolundan 21 waypoint'li rota; `HEARTBEAT` tam telemetri (15 alan); `CMD` `oturum` alanlı; `ACK` `ref_tip` alanlı. Her çerçeve `decode()` ile geri okunup yeniden çerçevelendiğinde bayt-eş çıktı: **true**.

## 2. `OPEN_ROUTE` — waypoint sayısına göre (N2)

| waypoint | üretim yolu (B) | en geniş / üst sınır (B) |
|---:|---:|---:|
| 1 | 139 | 151 |
| 2 | 150 | 167 |
| 3 | 160 | 183 |
| 4 | 171 | 199 |
| 5 | 181 | 215 |
| 6 | 193 | 231 |
| 7 | 204 | 247 |
| 8 | 216 | 263 |
| 9 | 227 | 279 |
| 10 | 239 | 295 |
| 11 | 250 | 311 |
| 12 | 262 | 327 |
| 13 | 273 | 343 |
| 14 | 285 | 359 |
| 15 | 296 | 375 |
| 16 | 308 | 391 |
| 17 | 319 | 407 |
| 18 | 331 | 423 |
| 19 | 342 | 439 |
| 20 | 354 | 455 |
| 64 (sözleşme tavanı) | 847 | 1159 |

Eğim: üretim yolunda **11,5 B/waypoint**, en geniş gösterimde **16,0 B/waypoint** (10 → 20 waypoint aralığından). `conf` alanının ondalık genişliği de boyutu değiştirir: 365 B (kısa) → 377 B (float32'den genişleyen ondalık).

## 3. `HEARTBEAT` telemetri alanlarının maliyeti (N3, N4)

asgari (`node` + ortak alanlar) **70 B** → tam telemetri **273 B** (15 alan).

| alan | marjinal maliyet (B) |
|---|---:|
| `pixhawk_canli` | 21 |
| `karar_yas` | 17 |
| `lat` | 17 |
| `lon` | 17 |
| `bat_yuzde` | 15 |
| `armed` | 13 |
| `mod` | 13 |
| `bat` | 12 |
| `gps_fix` | 12 |
| `yon` | 12 |
| `alt` | 11 |
| `hiz` | 11 |
| `x` | 11 |
| `y` | 11 |
| `uydu` | 10 |

## 4. `seq` ve `t` alanlarının bayt oynaması (N5)

| `seq` | tam telemetrili `HEARTBEAT` (B) |
|---:|---:|
| 1 | 270 |
| 10 | 271 |
| 100 | 272 |
| 1000 | 273 |
| 10000 | 274 |

Gerçek saat altında (200 örnek) aynı çerçeve **271–273 B** arasında oynar: `t` = `round(time.time(), 3)` ve ondalığın sondaki sıfırları JSON'da kısalır. Sabit saatteki değer 273 B'dir.

## 5. Gerçek görev karışımı — ölçülen veri hızı (N6–N9)

Pencere kadans başına 60 s. `saha` = SiK seri yolunun UDP ikizi (tek yayın ortamı, `wait_ack=False`); `udp` = dev/sim yolu (`ika` + `yks` akranları, `wait_ack=True`). Kadanslar: 1,353 Hz (Jetson Orin Nano `pt` p50'den ÖLÇÜLMÜŞ) ve 2,0 Hz (ölçülen kadans değil, **tavan senaryosu**).

| koşum | beslenen karar | **yayınlanan** karar | HEARTBEAT | İHA TX (B) | İHA TX (B/s) | İHA TX (pkt/s) | tepe TX (B/s) | İHA RX (B/s) | ortak ortam (B/s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `saha_jetson_olculmus` | 82 | 61 | 60 | 104807 | 1722,3 | 4,996 | 1728 | 0,0 | 2063,1 |
| `saha_tavan` | 120 | 61 | 60 | 105071 | 1726,6 | 4,996 | 1728 | 0,0 | 2071,0 |
| `udp_jetson_olculmus` | 82 | 50 | 60 | 123547 | 1995,5 | 5,976 | 2364 | 69,4 | 2134,3 |
| `udp_tavan` | 120 | 50 | 60 | 123580 | 2008,7 | 6,014 | 2364 | 69,9 | 2148,5 |

🔴 **Ölçümün asıl bulgusu — karar yayın tavanı ≈ 1 karar/s.** Beslenen karar sayısı kadansla artıyor ama **yayınlanan** karar sayısı artmıyor: `IhaSender._tekrarli_gonder` her kararı `repeat=4 × interval=0,25 s` = **1,0 s** boyunca tutar; `KararYayinci`'nin latest-wins yuvası fazlasını düşürür. `saha` koşumlarında 82 ve 120 besleme, ikisinde de 61 yayın verdi; `udp` koşumlarında 82 ve 120 besleme, ikisinde de 50 yayın verdi. Bu bir hat darboğazı değil, **gönderim tekrar tasarımının** sonucudur (D-383'te ölçülen ~3,3/s sınıfının aynı ailesi).

`udp` koşumunda YKS `OPEN_ROUTE`'a ACK üretmez (hakem 2/2'ye bağlıdır, `CONTRACTS.md` §6.6); bu yüzden her karar tekrar turunun tamamını koşar. YKS ucunun gördüğü çerçeveler: `ACK` 50 · `HEARTBEAT` 60 · `OPEN_ROUTE` 200.

## 6. Görev süresi boyunca toplam (N10) — EKSTRAPOLASYON

Yöntem: EKSTRAPOLASYON (olculen ortalama B/s x sure); 900 s'lik kosum YAPILMADI. Süreler şartname §6.2'den (İHA 900 s, İKA 600 s).

| koşum | İHA 900 s (B) | İKA 600 s (B) |
|---|---:|---:|
| `saha_jetson_olculmus` | 1550097 | 1033398 |
| `saha_tavan` | 1553961 | 1035974 |
| `udp_jetson_olculmus` | 1795978 | 1197318 |
| `udp_tavan` | 1807864 | 1205243 |

## 7. 57600 8N1 hat doluluğu (N11, N12) — HESAP

Ham bütçe 5760 B/s (57600 baud, 8N1 = 10 bit/bayt → 0,174 ms/bayt). Doluluk **hesaptır**, ölçüm değildir.

| koşum | tek yön (İHA TX) | paylaşımlı (ortak ortam) | ECC açıkken paylaşımlı |
|---|---:|---:|---:|
| `saha_jetson_olculmus` | %29,90 | %35,82 | %71,64 |
| `saha_tavan` | %29,98 | %35,95 | %71,91 |
| `udp_jetson_olculmus` | %34,64 | %37,05 | %74,11 |
| `udp_tavan` | %34,87 | %37,30 | %74,60 |

**ECC durumu: OLCULEMEDI.** Doluluk HESAPTIR (57600 8N1 = 10 bit/bayt -> 5760 B/s). SiK hava arayuzu TDM ile iki yon arasinda PAYLASILIR; hava hizi (Air Speed) ve ECC ayari OKUNMAMISTIR (results/atolye_20260912/SONUC_SABLONU.md A6 satiri bos). ECC acikken etkin hiz yariya iner — kaynak ATOLYE_TEST_GUNU_20260912.md A6 'HESAP + BENZER OLCUM - olcum degil' satiri; varsayim degil, ALINTIDIR.

## 8. Duyarlılık — rota sözleşme tavanına çıkarsa (HESAP)

| koşum | waypoint farkı (B) | `OPEN_ROUTE` çerçevesi | ortak ortam (B/s) | paylaşımlı | ECC açıkken |
|---|---:|---:|---:|---:|---:|
| `saha_tavan` | 482 | 244 | 4003,6 | %69,51 | %139,01 |
| `udp_tavan` | 482 | 200 | 3715,4 | %64,50 | %129,01 |

Rota sözleşme tavanındaki waypoint sayısına çıkarsa hat doluluğu yukarıdaki değerlere taşınır; ECC açık sütunu ham bütçeyi aşar. Bu bir ölçüm değil, ölçülen iki büyüklüğün (çerçeve boyutu farkı × çerçeve sayısı) çarpımıdır.

