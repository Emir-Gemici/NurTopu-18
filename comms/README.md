# Navitas — Haberleşme (comms) Modülü

İHA'nın tespit ettiği **açık yol** bilgisini YKS'ye ve İKA'ya ileten haberleşme katmanı.
Şartname §2.2.3'e uygun: aktarım İHA havadayken yapılır, YKS'de hakem onaylar, İKA gelen
veriyle hareket eder.

## Mimari

```
İHA (Jetson)                    YKS (Laptop/hakem)          İKA (RPi5)
─────────────                   ──────────────────          ──────────
detect_open_path() → road       yks_monitor.py              ika_receiver.py
        │                          ▲   (canlı izle+onay)        │  latest → A* nav
        │   OPEN_ROUTE {road,conf} │                            ▲
        └──────────────┬───────────┴────────────────────────────┘
                       │
        Taşıyıcı: SiK Radio V3 433 MHz (transparan seri)   [saha]
                  ya da UDP                                  [dev/sim]
```

- **Taşıyıcıdan bağımsız**: aynı kod hem UDP (geliştirme/sim) hem SiK telsiz (saha) ile çalışır.
- **Çerçeveleme**: newline ('\n') ile ayrılmış JSON satırları — UDP datagram ve seri akış için güvenli.
- **Dayanıklılık**: ACK gelene dek tekrar gönderim (RF paket kaybına karşı).

## Dosyalar

| Dosya | Görev |
|-------|-------|
| `protocol.py` | Mesaj şeması (OPEN_ROUTE/HEARTBEAT/ACK) + encode/decode + FrameReader |
| `link.py` | Taşıyıcılar: `UDPLink` (dev/sim), `SerialLink` (SiK telsiz) |
| `iha_sender.py` | İHA → açık yolu gönderir, ACK toplar |
| `ika_receiver.py` | İKA → alır, ACK döner, `latest` rotayı dışa açar (nav kullanır) |
| `yks_monitor.py` | YKS → hakem monitörü, canlı izler + onaylar |
| `test_comms.py` | Loopback testi (İHA→İKA/YKS + ACK) |

## Hızlı deneme (dev / UDP, 3 terminal)

```bash
# Terminal 1 — YKS (hakem monitörü)
python3 comms/yks_monitor.py --bind 0.0.0.0:5005

# Terminal 2 — İKA (alıcı)
python3 comms/ika_receiver.py --bind 0.0.0.0:5006

# Terminal 3 — İHA (açık yol = orta gönder)
python3 comms/iha_sender.py --road 2 --conf 0.91 \
    --ika 127.0.0.1:5006 --yks 127.0.0.1:5005
```

Otomatik test:
```bash
python3 comms/test_comms.py      # ✓ TEST GEÇTİ beklenir
```

## Saha (SiK Radio 433 MHz)

Telsiz şeffaf seri köprüdür; UDP yerine `--serial` ver:
```bash
# İHA tarafı (Jetson)
python3 comms/iha_sender.py --road 2 --conf 0.91 --serial /dev/ttyUSB0
# İKA tarafı (RPi)
python3 comms/ika_receiver.py --serial /dev/ttyUSB0
```
> Gereksinim: `pip install pyserial`. SiK air-rate ile 57600 baud tipiktir.
> Not: README'de eski "915 MHz" geçse de güncel tasarım **433 MHz (BTK uyumlu)**.

## Mesaj formatı (OPEN_ROUTE)

```json
{"v":1,"type":"OPEN_ROUTE","road":2,"label":"orta","conf":0.91,"waypoints":[],"seq":1,"t":1750000000.0}
```
`road`: 1=sol, 2=orta, 3=sag (şartname yön kuralı).

## İKA navigasyonuna bağlama

```python
from comms.link import UDPLink           # saha: SerialLink
from comms.ika_receiver import IkaReceiver

rx = IkaReceiver(UDPLink(bind=("0.0.0.0", 5006))).start()
# ... ana döngüde:
route = rx.latest                        # None ya da {"road":2,...}
if route:
    hedef_yol = route["road"]            # A* / path planning bunu kullanır
```
