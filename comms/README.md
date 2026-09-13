# Navitas — Haberleşme (comms) Modülü

İHA'nın tespit ettiği **açık yol** bilgisini YKS'ye ve İKA'ya ileten haberleşme katmanı.
Şartname §2.2.3'e uygun: aktarım İHA havadayken yapılır, YKS'de hakem onaylar, İKA gelen
veriyle hareket eder.

> **10 Eylül 2026 (T216):** bayat satırlar ~~üstü çizili~~ bırakıldı, güncel hâli altına yazıldı.
> Yorumlayıcı her yerde `O:\navitas-local-train\venv\Scripts\python.exe` (`python`/`python3`
> komutu Windows'ta Store saplamasıdır, sessizce hiçbir şey yapmaz — CLAUDE.md m.13).

## Mimari

```
İHA (Jetson Orin Nano)          YKS (Laptop / hakem)        İKA (RPi5 — sim'de)
──────────────────────          ────────────────────        ───────────────────
rpi_inference → KararYayinci    yks_gui.py (hakem ekranı,   ika_receiver.py
  (iha_sender.py)  ─OPEN_ROUTE─►  2 aşamalı onay, kanıt   ─►  latest → ika_nav
iha_inis_yayinci ─IHA_LANDED──►  kaydı hakem_kaydi.py)        (IKA_GO + IHA_LANDED
iha_komut_alici  ◄──CMD/ACK────  komut_tekrar.py (ACK'lı       kilidi, ACK'lar)
seri_hub.py (SiK tek sahip)      tekrar)                    ▲
        └──────────────┬─────────────┴──────────────────────┘
                       │
        Taşıyıcı: ~~SiK Radio V3 433 MHz~~ RFD900A 915–928 MHz (transparan seri)   [saha]
                  ya da UDP                                  [dev/sim/LAN]
```

~~`detect_open_path() → road` · `yks_monitor.py` (canlı izle+onay)~~ — *yks_monitor emekli (D-392), üretim YKS `yks_gui.py`; İHA üretim yolu `codes/rpi_inference.py run_camera → KararYayinci` (CONTRACTS §6.5).*

- **Taşıyıcıdan bağımsız**: aynı kod hem UDP (geliştirme/sim/LAN) hem SiK telsiz (saha) ile çalışır.
- **Çerçeveleme**: newline (`\n`) ile ayrılmış JSON satırları — UDP datagram ve seri akış için güvenli;
  tampon tavanı `CERCEVE_TAMPON_TAVANI` (64 KiB, D-388 S5).
- **Dayanıklılık**: ACK gelene dek tekrar gönderim (RF paket kaybına karşı); `ref_tip` ile ACK bağlama (CONTRACTS §6.6).
- **Mesaj tipi adları tek yerde** (T208): `protocol.MESAJ_OPEN_ROUTE`, `MESAJ_NO_ROUTE`, `MESAJ_HEARTBEAT`,
  `MESAJ_ACK`, `MESAJ_CMD`, `MESAJ_IHA_LANDED` (`MESAJ_TIPLERI`). Alıcılar çıplak `"OPEN_ROUTE"` yazmaz (madde 16).

## Dosyalar

| Dosya | Görev |
|-------|-------|
| `protocol.py` | Mesaj şeması (OPEN_ROUTE / NO_ROUTE / HEARTBEAT / ACK / CMD / IHA_LANDED) + mesaj tipi sabitleri + encode/decode + `FrameReader` |
| `link.py` | Taşıyıcılar: `UDPLink` (dev/sim/LAN), `SerialLink` (SiK telsiz, `serial_for_url`; `exclusive` tek sahiplik) |
| `iha_sender.py` | İHA → açık yol / NO_ROUTE / IHA_LANDED gönderir, ACK toplar; `KararYayinci` (üretim algı yolunun yayın halkası) |
| `ika_receiver.py` | İKA → alır, ACK döner (`ref_tip` ile; kopyası `--yks`'e), `latest` rotayı dışa açar; IKA_GO + IHA_LANDED sürüş kilidi |
| `komut_tekrar.py` | YKS → `IKA_GO` / `PARACHUTE` / `ARM` ACK'lı, aynı-seq, üst sınırlı tekrar durum makinesi (Tk'dan bağımsız; CONTRACTS §6.6) |
| `yks_gui.py` | **YKS hakem ekranı (üretim)** — canlı rota, iki aşamalı onay, ARM kilidi, kronometreler, `--fda` kipi (CONTRACTS §6.7) |
| `hakem_kaydi.py` | YKS kalıcı kanıt kaydı (JSONL, `flush`+`fsync`; olay kümesi CONTRACTS §6.8) |
| `iha_komut_alici.py` | Jetson: YKS `CMD` (PARACHUTE/ARM/DISARM/RTL/LAND) → Pixhawk `COMMAND_LONG`; ACK yalnız `COMMAND_ACK(ACCEPTED)` sonrası |
| `iha_inis_yayinci.py` · `inis_kaniti.py` | Jetson: Pixhawk iniş kanıtı (ON_GROUND ardışık 3 + düşük bağıl irtifa) → `IHA_LANDED` ACK'lı yayın |
| `seri_hub.py` | Jetson: SiK seri hattının **tek sahibi**; üç üretim sürecini UDP↔seri çoğullar (CONTRACTS §7.5) |
| `kamera_istemci.py` | YKS: Jetson `kamera_koprusu` uçlarından canlı kare (SiK hattını yüklemeden, ayrı LAN) |
| ~~`yks_monitor.py`~~ | ~~YKS → hakem monitörü, canlı izler + onaylar~~ — **EMEKLİ (D-392):** OPEN_ROUTE'a otomatik onay basar; sahada yasak, yalnız `--legacy-bilerek` ile koşar |
| `test_comms.py` | Loopback testi (İHA→İKA/YKS + ACK + NO_ROUTE + failsafe); ephemeral port (T209) |

## Hızlı deneme (dev / UDP)

~~`python3 comms/yks_monitor.py --bind 0.0.0.0:5005`~~ — emekli (yukarıda).

```bash
# Terminal 1 — YKS hakem ekranı (üretim GUI; --demo sahte İHA/İKA üretir)
O:\navitas-local-train\venv\Scripts\python.exe -B comms/yks_gui.py --bind 0.0.0.0:5005 --ika 127.0.0.1:5006

# Terminal 2 — İKA (alıcı). --yks ZORUNLU sayılır: OPEN_ROUTE ACK kopyası hakem
# ekranına gider; verilmezse YKS'de "İKA'ya aktarıldı" 2. onayı HİÇ açılmaz (K8)
O:\navitas-local-train\venv\Scripts\python.exe -B comms/ika_receiver.py --bind 0.0.0.0:5006 --yks 127.0.0.1:5005

# Terminal 3 — İHA (açık yol = orta gönder)
O:\navitas-local-train\venv\Scripts\python.exe -B comms/iha_sender.py --road 2 --conf 0.91 \
    --ika 127.0.0.1:5006 --yks 127.0.0.1:5005
```

Otomatik test:
```bash
~~python3 comms/test_comms.py~~
O:\navitas-local-train\venv\Scripts\python.exe -B comms/test_comms.py      # "✓ TEST GEÇTİ" beklenir (çıkış 0)
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_p8_sim_katmani.py"
```
Port sayıları (5005 YKS · 5006 İKA · 5007 İHA komut alıcı) yalnız `CONTRACTS.md` ve üretim argparse
varsayılanlarına aittir; testler ve demolar ephemeral port kullanır (T209 / D-427; `mission_demo.py` 10 Eylül).

## Saha (~~SiK Radio 433 MHz~~ RFD900A 915–928 MHz)

Telsiz şeffaf seri köprüdür; UDP yerine `--serial` ver. Jetson'da seri hat **tek sahiplidir**:
üç üretim süreci `seri_hub.py` üzerinden çoğullanır (CONTRACTS §7.5; doğrudan `--serial` yalnız tek süreçli deneme içindir).
```bash
# İHA tarafı (Jetson) — üretimde hub: comms/seri_hub.py --port /dev/ttyUSB0 --tuketici ...
O:\navitas-local-train\venv\Scripts\python.exe -B comms/iha_sender.py --road 2 --conf 0.91 --serial /dev/ttyUSB0
# İKA tarafı (RPi) — seri hatta --yks GEREKMEZ: OPEN_ROUTE/NO_ROUTE ACK'ı
# ortam yayını olarak tek hatta yazılır, YKS aynı paketi duyar (CONTRACTS §6.6)
O:\navitas-local-train\venv\Scripts\python.exe -B comms/ika_receiver.py --serial /dev/ttyUSB0
```
> Gereksinim: `pip install pyserial` (venv'de kurulu, 3.5). SiK air-rate ile 57600 baud tipiktir; telsiz firmware/baud
> **doğrulanmadı** (FDR §3.3.4.3.4).
> ~~Not: README'de eski "915 MHz" geçse de güncel tasarım **433 MHz (BTK uyumlu)**.~~ — *10 Eylül: 915 MHz metni kalmadı; tasarım 433 MHz.*

### RF / hat ölçümü — `scripts/sik_rf_olc.py` (RTT p50/p95, kayıp, **veri hızı**)

Aynı `protocol` çerçeveleriyle CMD→ACK turu; `veri_hizi` alanı gönderilen/alınan bayt ve paket, bayt/s, bit/s, paket/s
(prob kadansındaki **fiilî** akış; kapasite değil). Verdikt fail-closed: UYUMLU 0 / UYARI 1 / ÖLÇÜLEMEDİ 2.
```bash
# Gerçek SiK çifti (ekip taktığında — RF satırlarını kapatan komut budur)
... -B scripts/sik_rf_olc.py --rol yanki --port COM7
... -B scripts/sik_rf_olc.py --rol olc --port COM8 --n 200 --json --cikti results/<tarih>/sik_rtt.json
# Yazılım düzenekleri (10 Eylül ölçüldü: results/fdr_sprint_20260910/H2/)
... -B scripts/sik_rf_olc.py --rol yanki --tasiyici udp --bind 127.0.0.1:0     # portu stderr'e yazar
... -B scripts/sik_rf_olc.py --rol olc --tasiyici udp --peer 127.0.0.1:<port> --n 200 --json
```
Kilit: `tests/test_faz_b_sik_rf_olc.py` (TCP-seri köprüsü + UDP loopback, 300 ms enjekte gecikme, sayaç mutasyonu).

## Mesaj formatı (OPEN_ROUTE)

```json
{"v":1,"type":"OPEN_ROUTE","road":2,"label":"orta","conf":0.91,"ref_xy":[-20.0,-24.5],"waypoints":[[0.0,0.0],[0.3,1.8]],"seq":1,"t":1750000000.0}
```
`road`: 1=sol, 2=orta, 3=sag (şartname yön kuralı). `ref_xy` + yerel `waypoints` (ilk nokta `[0,0]`, segment ≤ 2,10 m) —
CONTRACTS §6.2/§3. Diğer tipler ve alanlar: CONTRACTS §6 tablosu, FDR §3.3.4.3.1.

## İKA navigasyonuna bağlama

```python
from comms.link import UDPLink           # saha: SerialLink
from comms.ika_receiver import IkaReceiver

rx = IkaReceiver(UDPLink(bind=("0.0.0.0", 5006)), yks_peer=("<YKS_IP>", 5005)).start()
# ... ana döngüde:
route = rx.latest                        # None ya da {"road":2,...}
if route and rx.wait_surus_izni(timeout=0.0):   # IKA_GO + IHA_LANDED kilidi (CONTRACTS §7)
    hedef_yol = route["road"]            # A* / path planning bunu kullanır
```
