# B — NAVITAS Haberleşme Katmanı (`comms/`) Öğretici Özeti

> Kaynak: `comms/*.py` (14 dosya), `CONTRACTS.md` §6–§7, `scripts/mavlink_dogrula.py`,
> `scripts/sahte_pixhawk.py`, `scripts/sik_rf_olc.py`, `config/pixhawk/README.md`.
> Her sayı/port/mesaj adı için `dosya:satır` verilmiştir. Kesin olmayan yerler
> **DOĞRULANAMADI** ile işaretlidir. Hedef okur: Python bilen, MAVLink/UDP bilmeyen takım üyesi.

---

## 1. Topoloji — kim, kime, ne gönderiyor

### 1.1 Cihazlar ve bağlantılar

| Cihaz | Rol | Üzerinde koşan comms süreçleri |
|---|---|---|
| **Jetson (İHA)** | Algı + telsiz halkası + Pixhawk köprüsü | `rpi_inference` içindeki `KararYayinci` (`iha_sender.py:301`), `iha_inis_yayinci.py`, `iha_komut_alici.py`, SiK kipinde `seri_hub.py`, kamera köprüsü `scripts/kamera_koprusu.py` (HTTP :8080, `kamera_koprusu.py:71`) |
| **Pixhawk 6C** (ArduCopter 4.5.7, `config/pixhawk/README.md:34`) | Uçuş kontrolcüsü | Jetson'a seri (`/dev/ttyACM0`, `iha_komut_alici.py:30`) — portu **yalnız çoğullayıcı** (mavlink-router / MAVProxy) açar, süreçler `udp:127.0.0.1:1455N` uçlarından konuşur (`CONTRACTS.md:1094-1119`) |
| **YKS PC** (dizüstü, hakem ekranı) | Hakem onayı, kritik komutlar, kanıt kaydı | `yks_gui.py` (Tk), `hakem_kaydi.py`, `komut_tekrar.py`, `kamera_istemci.py` |
| **İKA (RPi5)** | Kara aracı | `ika_receiver.py` (`ika_receiver.py:4-11`) |
| **SiK telsiz 433 MHz** | Saha taşıyıcısı (şeffaf seri köprü) | `/dev/ttyUSB0` @ 57600 baud (`link.py:80`; `comms/README.md:57-58`) |

### 1.2 Portlar (koddaki varsayılanlar)

| Port | Kim dinler | Kaynak |
|---|---|---|
| UDP **5005** | YKS (`yks_gui --bind 0.0.0.0:5005`) | `yks_gui.py:4343` |
| UDP **5006** | İKA (`ika_receiver --bind 0.0.0.0:5006`) | `ika_receiver.py:326` |
| UDP **5007** | İHA komut alıcısı (`iha_komut_alici --bind 0.0.0.0:5007`) | `iha_komut_alici.py:92` |
| UDP **5100** (loopback) | SiK hub'ın UDP ucu (`seri_hub --bind 127.0.0.1:5100`) | `seri_hub.py:100` |
| UDP 14550 / 14551 / 14552 (loopback) | MAVLink çoğullayıcı uçları: `rpi_inference` okur / `iha_inis_yayinci` okur / `iha_komut_alici` yazar | `CONTRACTS.md:1108-1112`; `iha_inis_yayinci.py:20`; `seri_hub.py:28` |
| HTTP **8080** | Jetson kamera köprüsü (`/kare.jpg`, `/durum`) | `kamera_koprusu.py:71`; `kamera_istemci.py:35-36` |
| Seri `/dev/ttyACM0` | Pixhawk (tek sahipli, yalnız çoğullayıcı) | `iha_komut_alici.py:28-33` |
| Seri `/dev/ttyUSB0` | SiK telsiz (tek sahipli, SiK kipinde yalnız hub) | `seri_hub.py:2-9` |

⚠ Tutarsızlık notu: `iha_komut_alici.py:42,44,851` örneklerinde `udp:127.0.0.1:14560` yazar; `CONTRACTS.md:1112` ve `seri_hub.py:28` ise **14552** der. Gerçek servis dosyasındaki değer bu okumada **DOĞRULANAMADI**.

### 1.3 ASCII şema

```
                 ┌──────────────────── JETSON (İHA) ────────────────────┐
                 │  rpi_inference ──► KararYayinci (iha_sender.py)      │
                 │        │ OPEN_ROUTE / NO_ROUTE / HEARTBEAT            │
                 │  iha_inis_yayinci ──► IHA_LANDED (Pixhawk kanıtlı)   │
                 │  iha_komut_alici  ◄── CMD(ARM/DISARM/RTL/LAND/PARACHUTE)
                 │        │ COMMAND_LONG ▼    ▲ COMMAND_ACK              │
                 │  MAVLink çoğullayıcı (udp:14550/14551/14552)          │
                 │        │ /dev/ttyACM0 (TEK SAHİP)                     │
                 │     PIXHAWK 6C  (HEARTBEAT, GLOBAL_POSITION_INT,      │
                 │                  EXTENDED_SYS_STATE, GPS_RAW_INT…)    │
                 │  kamera_koprusu :8080 (/kare.jpg, /durum)  [ayrı LAN] │
                 └───────┬───────────────────────────────┬──────────────┘
      UDP kipi (WiFi)    │            SiK kipi            │
   doğrudan 5005/5006 ◄──┘   seri_hub 127.0.0.1:5100 ◄────┘
                              │ /dev/ttyUSB0 (TEK SAHİP)
                              ▼  SiK 433 MHz şeffaf seri
   ┌──────── YKS PC ────────┐          ┌──────── İKA (RPi5) ────────┐
   │ yks_gui  :5005 (UDP)   │          │ ika_receiver :5006 (UDP)   │
   │  ACK(OPEN_ROUTE) ──► İHA│          │  ACK(OPEN_ROUTE) ──► İHA   │
   │  CMD(IKA_GO) ──► İKA   │          │       kopya ──► YKS (K8)   │
   │  CMD(ARM…) ──► İHA:5007│          │  latch: IKA_GO ∧ IHA_LANDED│
   │  kamera_istemci ◄─ :8080│         └────────────────────────────┘
   │  hakem_log.jsonl (fsync)│
   └────────────────────────┘
```

Kural: SiK hattında hedef YKS'dir; `--ika-hedef` hub'a **verilmez** (İKA ACK'i seriden gelmediği için 8 tekrar boşa gidiyordu, ölçüldü D-405; `CONTRACTS.md:1146-1150`). İKA'nın hattı topolojiyle karara bağlanacak — **DOĞRULANAMADI** (bu okumada karar yok).

---

## 2. `protocol.py` ve `link.py`

### 2.1 Çerçeveleme ve sürüm

- Her mesaj **tek satır JSON + `\n`** (`protocol.py:216-219`, `encode`). Sürüm alanı `"v": 1` (`PROTOCOL_VERSION`, `protocol.py:23`). `decode` satırı `json.loads` eder (`:222-224`).
- `FrameReader` byte akışından newline çerçeveleri ayıklar; bozuk JSON'u (ValueError/UnicodeDecodeError/**RecursionError**) sessizce atar (`:249-270`). RecursionError'ın yutulması D-405'tendir: `[[[[...` gibi derin iç içe tek satır hub sürecini öldürüyordu (`:262-270`).
- Tampon tavanı **64 KiB** (`CERCEVE_TAMPON_TAVANI`, `:231`); newline'sız birikim tavanı aşarsa atılır ve `atilan_bayt` sayılır (`:271-275`). NEDEN: SiK gürültüsü newline üretmeden akarsa 15 dk'lık uçuşta tampon sessizce büyüyordu (`:227-230`).
- MAVLink'teki "sysid" kavramının NAVITAS karşılığı **`node`** alanıdır (`"iha"`, `"ika"`, `"yks"`); `seq` sayaçları **düğüm/süreç başınadır** (`itertools.count(1)`, `:36`), bu yüzden seq çakışması olabilir → `ref_tip` (aşağıda).

### 2.2 Mesaj tipleri

| Tip | Üretici → Alıcı | Alanlar | Kaynak |
|---|---|---|---|
| `OPEN_ROUTE` | İHA → YKS, İKA | `road` (1=sol,2=orta,3=sag; `ROAD_LABEL` `:24`), `label`, `conf` (0..1, yuvarlanmaz `:62-64`), `ref_xy` ([x,y] m, 2 ondalık), `waypoints` (ref'e göre yerel [[x,y]…]), `seq`, `t` | `protocol.py:41-70` |
| `NO_ROUTE` | İHA → YKS, İKA | `sebep` (zorunlu), `detay` (isteğe bağlı), `seq`, `t`. NEDEN ayrı tip: sessizlik ile güvenli ret ayırt edilemezdi | `:73-90` |
| `HEARTBEAT` | herkes | `node`, `seq`, `t` + isteğe bağlı telemetri: `x,y,alt,hiz,yon,bat,bat_yuzde,uydu,karar_yas,lat,lon,gps_fix,armed,mod,pixhawk_canli` (`HEARTBEAT_TELEMETRI_ALANLARI` `:103-110`). `None` alan **yazılmaz** (fail-closed, `:119-120`); sözleşme dışı alan `ValueError` (`:122-124`) | `:113-125` |
| `ACK` | YKS / İKA / İHA → gönderen | `ref` (onaylanan seq), `node`, `t`; isteğe bağlı `ref_tip` (onaylanan tip), `ref_cmd`, `sonuc` (`"ACCEPTED"`, `ACK_SONUC_KABUL` `:26`) | `:128-147` |
| `CMD` | YKS → İHA/İKA | `cmd` (`IKA_GO`, `ARM`, `DISARM`, `RTL`, `LAND`, `PARACHUTE`), `hedef`, `seq`, `t`, isteğe bağlı `oturum` (16–64 karakter `[A-Za-z0-9_-]`, `:31-34`, `oturum_dogrula` `:174-181`) | `:184-195` |
| `IHA_LANDED` | İHA → YKS, İKA | `node:"iha"`, `seq`, `t`. Operatör düğmesi değildir; latch'i yalnız bu açar | `:198-211` |

`kritik_komut_ack_gecerli_mi(mesaj, ref_seq, ref_cmd, node="iha")` (`:150-171`): ARM/DISARM/PARACHUTE/RTL/LAND için ACK ancak `ref==seq ∧ node=="iha" ∧ ref_tip=="CMD" ∧ ref_cmd==cmd ∧ sonuc=="ACCEPTED"` ise geçerlidir; bool/int tuzakları reddedilir. Eski "zayıf" ACK teslim tekrarını durdurabilir ama aracın fiziksel durumuna kanıt olamaz (`:153-156`).

### 2.3 `link.py` — taşıyıcılar

- **`UDPLink(bind, peer, timeout=0.3, reuse=True)`** (`link.py:14-40`). `reuse=False` → `SO_REUSEADDR` yok, Windows'ta `SO_EXCLUSIVEADDRUSE`; ikinci süreç aynı porta bağlanamaz (OSError → görünür çıkış). NEDEN (D-405): `SO_REUSEADDR` ile ikinci süreç sessizce bağlanıp datagramları ilk sokete kaptırıyordu (`:20-28`). Tek sahipli uçlar: hub (`seri_hub.py:573-574`) ve YKS (`yks_gui.py:393-395`).
- `recv()` `socket.timeout`, `ConnectionResetError`, `ConnectionRefusedError`'ı `(None, None)` olarak yutar (`:51-67`). NEDEN: Windows'ta dinlemeyen akrana gönderim sonraki `recvfrom`'da WinError 10054 üretiyor; YKS dinleyici thread'i ölüyor, `iha_sender` çöküyordu (REVIEW_LOG D-06).
- **`SerialLink(port="/dev/ttyUSB0", baud=57600, timeout=0.3, exclusive=True)`** (`:73-101`). `serial_for_url` kullanır (loop://, socket://, spy:// ile testlenebilsin; D-388). `exclusive=True` POSIX'te flock → ikinci süreç "Could not exclusively lock port" (D-405).
- `SerialLink.recv()` D-403 düzeltmesi (`:106-120`): eskiden `read(256)` 256 bayt veya 0,3 s bekliyordu → ~70 baytlık ACK için her bekleme zaman aşımına yuvarlanıyor, ACK turu p50 **622,6 ms** çıkıyordu (paraşüt tekrar aralığı 0,20 s'nin 3 katı). Şimdi: ilk bayta kadar bekle, sonra `in_waiting` kadar boşalt → aynı köprüde 0,8 ms.
- `make_link(kind)` fabrika (`:126-132`).

---

## 3. Akışlar adım adım

### 3(a) İHA rota sonucunu YKS'ye ve İKA'ya nasıl yollar — `iha_sender.py`

1. **Üretim yolu** `rpi_inference` → `KararYayinci.karar(open_path, conf, waypoints_px, mpp, karar_reddi)` (`iha_sender.py:371-383`). Her çağrı `_son_karar_monotonik` damgasını tazeler (NO_ROUTE de karardır; `karar_yas` heartbeat'e bundan gider, A2/D-381).
2. Karar **latest-wins tek yuvaya** yazılır; ayrı `iha-karar` thread'i alır (`:395-414`), kamera döngüsü ACK beklemez (`CONTRACTS.md:993`).
3. `_karari_gonder` (`:416-449`): ret sebebi varsa `NO_ROUTE(sebep)`; `open_path is None` ise `NO_ROUTE(KARAR_YOK)`; piksel rota `piksel_rotayi_yerele_cevir` ile yerel metreye çevrilir (`:271-298`: `x=(px−px₀)·mpp`, `y=(py₀−py)·mpp`, ilk nokta [0,0], kenar `MAX_SEGMENT_M`=2,10 m'yi aşarsa bölünür); çevrim düşerse `NO_ROUTE(OLCEK_YOK|ROTA_GEOMETRI)`.
4. `IhaSender.send_open_route` (`:219-238`): **güven kapısı burada** (`rota_guven_reddi(conf)`, eşik `ROTA_GUVEN_ESIGI=0.20`, `karar_sozlesmesi.py:22`) — eşik altı OPEN_ROUTE **NO_ROUTE'a döner**; İKA/broadcast akranı varsa `rota_geometrisini_dogrula` (`:62-75`: 2..64 waypoint, ilk nokta [0,0] ±0,15 m, yarıçap ≤ 60 m, segment ≤ 2,10 m).
5. `_tekrarli_gonder` (`:171-217`): mesaj her akrana gönderilir, `repeat=8` × `interval=0.25 s` ACK beklenir; ACK `_ack_dugumu` ile doğrulanır (`:127-159`: `v`, `type=="ACK"`, `ref==seq`, `node ∈ peers`, `ref_tip` varsa tiple eşit, **UDP'de kaynak adresi yapılandırılmış akranla aynı** `_adres_ayni_mi` `:104-125`). Tüm ACK'ler gelince pencere erken terk edilir (D-383: eskiden 0,3 s soket zaman aşımı bekleniyor, "telsiz_ack ~308 ms" sayısı o sabitin ölçümüydü; `:204-214`).
6. **Heartbeat** ayrı `iha-heartbeat` thread'i, `IHA_HEARTBEAT_ARALIK_S=1.0 s` (`karar_sozlesmesi.py:145`) < `IkaReceiver.hb_timeout=3.0 s` (`ika_receiver.py:27`). Alan toplama kendi try'ında (T171/D-320: eksik öznitelik AttributeError'ı sessiz heartbeat kaybına yol açıyordu, `:454-461`). `karar_yas` yalnız karar üretildiyse yazılır (`:493-506`).
7. Seri kipte `peers={"broadcast": None}`, `wait_ack=False` (`:519-522`, `:582-584`); ACK adres taşımadığı için `_ack_dugumu` `adres is None` durumunda kabul eder (`:157-158`).

**İKA tarafı** (`ika_receiver.py`): `OPEN_ROUTE` → `latest` güncellenir, ACK gönderene + `yks_addr`'a kopya (`_rota_ack` `:175-195`, K8); `NO_ROUTE` → `last_no_route` (latest **ezilmez**, `:247-260`); `IHA_LANDED` → `iha_landed` latch + ACK(`ref_tip="IHA_LANDED"`) (`:266-274`); `CMD IKA_GO` → `ika_go` latch (ilk alımda `ika_go_monotonic` sabitlenir, mükerrer alım yalnız ACK'lanır `:275-292`). Sürüş izni `ika_go ∧ iha_landed` (`:127-138`); `run_if_route_valid` link canlı ∧ izin ∧ rota ∧ NO_ROUTE yok ise eylemi kilit altında koşar (`:80-100`). 3 s mesaj yoksa `link_lost` (`:294-306`); rota önbelleği silinmez.

**YKS tarafı**: bkz. §4 (iki aşamalı hakem onayı; ACK yalnız 2/2'de).

### 3(b) YKS'den paraşüt/ARM komutu Pixhawk'a nasıl gider — `iha_komut_alici.py`

1. YKS `_komut_mesaji("PARACHUTE","iha")` → `command(cmd, "iha", oturum=<uuid4 hex>)` (`yks_gui.py:3115-3125`, oturum `:703`). `AckliTekrar` aynı seq ile `PARASUT_TEKRAR_ARALIGI_S=0.20 s × 40` (`karar_sozlesmesi.py:2102-2103`), ARM/RTL/LAND `0.25 s × 20` (`:2088-2089`) tekrarlar.
2. Hedef adres `--iha HOST:5007` ile **pinlenir**; heartbeat'ten öğrenilen adres `rpi_inference`'ın efemer portudur, komut alıcısı değil (D-403 KRİTİK-1, `yks_gui.py:731-737`, `:4346-4350`). UDP kipinde `--iha` zorunlu (`:4406-4408`).
3. `IhaKomutAlici.isle(mesaj, adr)` (`iha_komut_alici.py:630-779`) sırasıyla:
   - `type=="CMD"` ve `hedef==node` değilse yok say (`:632-635`);
   - `--izinli-kaynak HOST:PORT` pin'iyle kaynak eşleşmezse `kaynak_red` (`:636-646`; saha için **zorunlu** `:888-890`; SiK'te kaynak `127.0.0.1:5100` = hub);
   - `cmd ∉ {PARACHUTE, ARM, DISARM, RTL, LAND}` → aktarım yok, ACK yok (`:84-90`, `:658-662`);
   - **saat kapısı** (K-1/K-B, §6'da ayrıntı): `yas = (simdi − t) − ofset` tavan içinde değilse `zaman_red` (`:668-703`); tavan = YKS tekrar penceresi (ARM 5 s, PARAŞÜT 8 s; `KOMUT_YAS_TAVANI_S` `:120-126`);
   - `oturum` varsa `(oturum, seq, cmd)` anahtarı: daha önce ACCEPTED ise eyleyici **yeniden çalıştırılmaz**, ACK yinelenir; daha önce başarısızsa gecikmiş eylem RED (`:705-725`);
   - MAVLink bağlantısı yoksa ya da pymavlink `udp:` sunucu kipi akranı henüz görmediyse (`mav_hedefi_biliniyor_mu` `:251-269`) → "aktarılmadı, ACK YOK" (`:741-751`). NEDEN: pymavlink 2.4.49 `mavudp.write` akran yokken sessizce hiçbir şey göndermez (`:35-39`). Bu teşebbüsler anahtarı **zehirlemez** (K-2, `:726-740`);
   - `_aktar` → `command_long_send(sys=1, comp=1, MAV_CMD, confirmation=0, param1, 0×6)` (`:510-521`); tablo `:238-248`: PARACHUTE→`MAV_CMD_DO_PARACHUTE, PARACHUTE_RELEASE`; ARM/DISARM→`MAV_CMD_COMPONENT_ARM_DISARM, param1=1/0`; RTL→`MAV_CMD_NAV_RETURN_TO_LAUNCH`; LAND→`MAV_CMD_NAV_LAND`;
   - `_komut_ack_bekle` (`:544-608`): `MAVLINK_KOMUT_ACK_TAVANI_S=0.5 s` (`karar_sozlesmesi.py:2112`) içinde `COMMAND_ACK` bekler; `command` eşleşmeli, `srcSystem == target_system` olmalı (D-403), `srcComponent ∈ {0, MAV_COMP_ID_AUTOPILOT1, target_component}` (K-3, `:523-542`; ölçüldü: `--target-component 3` ile her ACK "yabancı" sayılıp uçtan uca düşüyordu), `result == MAV_RESULT_ACCEPTED`;
   - anahtar burada terminal olur (`:768-769`): ACCEPTED/REJECTED/gelmedi — aynı (oturum,seq,cmd) bir daha çalıştırılmaz;
   - yalnız ACCEPTED ise `_ack_gonder` → `ack(seq, "iha", "CMD", ref_cmd=cmd, sonuc="ACCEPTED")` (`:610-628`).
4. **"ACK = aldım VE Pixhawk KABUL ETTİ"** (docstring `:9-18`, D-393 dürüstlük sözleşmesi + D-403 ÖNEMLİ-3). Ret/zaman aşımı/istisna → ACK yok, KIRMIZI log; YKS tekrarlamaya devam eder, ekranda "ACK YOK" görünür.
5. **Idempotentlik bilerek yok** (`:20-26`, D-403 KRİTİK-2): eski `(cmd, seq)` hafızası, YKS her açılışta seq'i 1'den başlattığı için yeniden açılan YKS'nin PARACHUTE'unu "mükerrer" sayıp MAVLink'e hiç göndermeden ACK'lıyordu — yeşil "İHA ALDI", paraşüt kapalı. Oturumlu anahtar bunu çözer (oturum her YKS sürecinde yeni uuid).
6. YKS'de kabul: `_ack_isle` `kritik_komut_ack_gecerli_mi` ile güçlü ACK arar (`yks_gui.py:2014-2067`). ARM için ek şart: taze Pixhawk HEARTBEAT'te `armed` alanı beklenen değerde (`_arm_bekleyeni_tamamla` `:3223-3238`; tazelik `ARM_DURUM_TAZELIK_S`=2,5 s, `karar_sozlesmesi.py:2212-2215`). RTL/LAND için ACK sonrası `mod` alanı komutla eşleşmeli (`_acil_bekleyeni_tamamla` `:3328-3355`). Paraşüt için ACK yalnız "komut kabul" — mekanik açılma sensörü yok (`:2042-2046`).

### 3(c) İniş kanıtı — `iha_inis_yayinci.py` / `inis_kaniti.py`

1. `yerde_mi(mav, ardisik=3, tavan_m=1.0, beklenen_sysid)` (`inis_kaniti.py:925-934`) bağlantıyı süreç içi sahiplenir (`_mav_sahiplen` `:41-60`) ve `_yerde_mi_sahipli`'yi koşar (`:937-1065`):
   - `mav.inis_kaniti_deadline_monotonic` zorunlu (yoksa fail-closed False, `:978-983`);
   - tek `recv_match(type=[EXTENDED_SYS_STATE, GLOBAL_POSITION_INT])` akışı; `EXTENDED_SYS_STATE.landed_state == MAV_LANDED_STATE_ON_GROUND` sonra gelen **ilk** `GLOBAL_POSITION_INT.relative_alt/1000 < 1,0 m` bir örnek sayılır; **3 ardışık temiz çift** gerekir;
   - ON_GROUND dışı meşru durum terminal değil, ilerlemeyi sıfırlar (D-389 A2, `:1030-1037`); yabancı sysid **atlanır** (D-389 B1, `:1017-1022`); beklenen kaynaktan bozuk alan terminaldir (`:1027-1029`, `:1050-1052`);
   - `relative_alt` home'a göre bağıl irtifadır, yerden yükseklik değil — bu yüzden yalnız makullük kapısıdır; birincil kanıt `landed_state` (`:1-8`).
2. `iha_inis_yayinci.main` (`:467-561`): `--mavlink udp:127.0.0.1:14551` (seri cihaz verilirse exit 2, `:475-476`); `AkisIstekcisi.iste()` (`:200-251`) `MAV_CMD_SET_MESSAGE_INTERVAL` ile EXTENDED_SYS_STATE, GLOBAL_POSITION_INT, GPS_RAW_INT ister (aralık = 1e6/(asgari_hz×2) µs; `MAVLINK_DURUM_ASGARI_HZ=1`, `MAVLINK_KONUM_ASGARI_HZ=4`, çarpan 2 → `karar_sozlesmesi.py:2201-2246`). NEDEN (T207/D-406 A): ArduCopter EXTENDED_SYS_STATE'i hiçbir `SR*` akışında vermez, istek bağlantıya özeldir ve Pixhawk reboot'unda (pil değişimi) silinir (`iha_inis_yayinci.py:6-14`; `config/pixhawk/README.md:154-164`). `AkisGozcusu` (`:315-358`) `recv_match` beklemesini 0,5 s dilimlere böler; 5 s sessizlikte (`MAVLINK_AKIS_SESSIZLIK_TAVANI_S`) KIRMIZI `"EXTENDED_SYS_STATE gelmiyor — akis yeniden isteniyor"` (`:66`) + anında yeniden istek; her 10 s periyodik yenileme.
3. Kanıt gelince `iha_inisini_yayinla` (`:361-419`): `IhaSender.send_iha_landed` (8×0,25 s ACK'li), ardından `IHA_INIS_HEARTBEAT_SURESI_S` (= İKA görev süresi 600 s) boyunca 0,5 s'de bir heartbeat (K6; alıcıdaki `link_lost` yalnız heartbeat gerçekten kesilince oluşur). Çıkış kodları: 3 = kanıt yok, 4 = taşıyıcı açılamadı, 5 = ACK eksik (`:540, 548, 559`).
4. `BagilIrtifaOkuyucu` (`inis_kaniti.py:382-922`) aynı dosyada: `rpi_inference` için taze `relative_alt` + telemetri snapshot'ı (`lat/lon/alt/hiz/yon`, `gps_fix/uydu`, `bat/bat_yuzde`, `armed/mod/pixhawk_canli`; `:811-902`). Yabancı sysid/component paketleri cache'e dokunmaz (`:565-580`); `time_boot_ms` sıra/reboot ayrımı `_uzak_sira_karari` (`:350-379`); bayat alan sözlükte hiç yer almaz.

### 3(d) `seri_hub.py` — neden var

Olgu (`seri_hub.py:2-7`; `CONTRACTS.md:1121-1128`): SiK kipinde Jetson'daki üç üretim süreci (`rpi_inference --telsiz-seri`, `iha_inis_yayinci --serial`, `iha_komut_alici --serial`) aynı `/dev/ttyUSB0`'ı ister; seri port tek sahiplidir — ikinci süreç ya açamaz ya ilkinin bayt akışını çalar, iki taraf sessizce kör olur. Pixhawk tarafında aynı olgu §7.4'te ölçüldü (`CONTRACTS.md:1094-1103`).

Çözüm: hub portu tek başına açar, NAVITAS çerçevelerini UDP loopback üzerinden çoğullar — "MAVLink router'ın NAVITAS protokolü için karşılığı" (`:9-12`). Tüketicilerin kodu değişmez, yalnız hedef adresleri `127.0.0.1:5100`'e çevrilir.

- UDP→seri: datagram olduğu gibi seriye yazılır, gönderen "öğrenilen" kümeye eklenir (`_udp_turu` `:330-373`); newline'sız datagrama newline eklenir (D-405 Q1, `:353-366`).
- seri→UDP: kalıcı `FrameReader` ile tam çerçeve toplanır, `encode(decode(...))` ile tek satır yapılıp statik `--tuketici` ∪ öğrenilenler adreslerine fan-out (`_cerceveleri_isle` `:400-431`, `_fanout` `:380-398`). Datagram = tam olarak bir çerçeve (D-403 KÜÇÜK-4: `iha_komut_alici.poll` UDP'de datagram başına taze FrameReader kullanır, `iha_komut_alici.py:805-811`).
- `iha_komut_alici` hiç göndermeden dinlediği için **statik** `--tuketici 127.0.0.1:5007` verilir (`:29-31`). Öğrenilen küme tavanı 32 (`OGRENILEN_TAVANI` `:135`), aşılınca en az tazelenen düşer + KIRMIZI log; uzun ömürlü tüketici statik verilir.
- Zamanlama: seri okuma zaman aşımı **20 ms** (`:116`; D-403 dersi: 0,3 s tek iplikli hub'da UDP→seri yönünü her turda 300 ms bekletirdi), UDP 1 ms (`:120`), tur tavanları 64/128 (`:123-124`).
- Dayanıklılık: seri arızasında seri kapatılır, 1 s'de bir yeniden açma (`:107`), UDP tarafı yaşar, arızadaki UDP çerçeveleri **düşürülür ve sayılır — kuyruklanmaz** (bayat rota hat dönünce yayınlanmasın; `:33-38`); UDP okuma hatası (WinError 10040) hub'ı öldürmez (`:334-345`); datagram tavanı 65535 B (`:141`); SIGTERM → `durdur()` (systemd stop'ta son sayaç logu düşsün, `:495-515`).
- Tek sahiplik: UDP ucu `reuse=False` (ikinci hub exit 3, `:570-579`), seri `exclusive=True` (exit 4, `:580-588`).

Topoloji (`:24-28`; `CONTRACTS.md:1142-1146`): `seri_hub --port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007` · `rpi_inference --yks-hedef 127.0.0.1:5100` · `iha_inis_yayinci --yks 127.0.0.1:5100` · `iha_komut_alici --bind 0.0.0.0:5007 --izinli-kaynak 127.0.0.1:5100 --mavlink udp:127.0.0.1:1455N`. `iha_komut_alici --serial` CLI'da **reddedilir** (`iha_komut_alici.py:891-894`).

### 3(e) Yardımcı modüller

- **`kamera_istemci.py`** — YKS'nin Jetson `/kare.jpg` + `/durum` uçlarını okuyan arka-plan istemcisi. Video **SiK üzerinden taşınmaz**, ayrı LAN'dır (`:1-19`). 5 Hz kare (`:40`), 1 Hz durum (`:42`), istek zaman aşımı 1 s (`:44`), kare tazelik 2 s (`:47`), durum tazelik 3 s (`:50`), JPEG tavanı 5 MiB (`:52`). Yalnız `http` şeması, kullanıcı/parola/sorgu yasak, `0.0.0.0` hedef olamaz (`:66-96`). Aynı `X-Kare-Sira`/CRC32 tekrar gelirse tazelik yenilenmez — donmuş görüntü canlı sayılmaz (`:315-335`). `snapshot()` durumları: `CANLI`, `CANLI_SAGLIK_BILINMIYOR`, `KAYNAK_KAPALI`, `KARE_BAYAT`, `BAGLANAMADI` (`:55-59`, `:217-281`); bayat/kapalı durumda `jpeg=None`.
- **`hakem_kaydi.py`** — UTF-8 JSONL, her satırda `flush`+`fsync` (`:90-94`); ortak alanlar `v=1, ts (ISO ms), monotonic_s, oturum (uuid), olay` (`:78-84`); varsayılan yol `results/prova/<YYYYMMDD_HHMMSS>_<pid>/hakem_log.jsonl` (`:21-32`); `OTURUM_BASLADI`/`OTURUM_BITTI` (`:54`, `:112`); kapanış tek kritik bölge (`:104-120`). NEDEN: "Ekrandaki kayan metin uçuş sonrası kanıt değildir" (`:3`).
- **`komut_tekrar.py`** — `AckliTekrar(gonder, aralik_s, ust_sinir)`: `BOS→BEKLIYOR→ONAYLANDI|VAZGECILDI` (`:6-11`); `tik()` aralık dolduysa **aynı seq** ile tekrar (`:57-74`); `ack_geldi` `ref==seq` ve `ref_tip` varsa tip eşleşmesi (`:76-94`). NEDEN: IKA_GO tek paketti, tek kayıp görevi geri dönülmez bitiriyordu (D-02, K4). YKS'de dört örnek: `ika_go_tekrar`, `parasut_tekrar`, `arm_tekrar`, `acil_tekrar` (`yks_gui.py:748-774`).
- **`yks_monitor.py`** — **EMEKLİ** (P8/D-392): OPEN_ROUTE'a "HAKEM ONAYI ✓ (otomatik)" basıp ACK'i kendisi döner; sahada iki aşamalı onayı deler. `--legacy-bilerek` olmadan exit 2 (`:1-15`, `:34-39`).
- **`test_comms.py`** — loopback: İHA→İKA+YKS OPEN_ROUTE + ACK, heartbeat kesilince `link_lost`, NO_ROUTE ACK'i ve `latest` korunumu (`:73-128`). Portlar efemer (T209/D-427: sabit 5005/5006 saha PC'sinde YKS açıkken WinError 10013 veriyordu, `:34-44`).
- **`scripts/sahte_pixhawk.py`** — gerçek MAVLink çerçevesi/CRC ile HEARTBEAT 1 Hz, GLOBAL_POSITION_INT 5 Hz, EXTENDED_SYS_STATE 2 Hz basar (`:31-33`); sysid 1, component 1 (`:37-41`; component 0 olsaydı `inis_kaniti` süzgeci reddediyordu, 3 Eylül ölçümü `:225-233`); senaryolar `ucus/inis/yerde/yabanci(sysid 99)/donuk-saat` (`:51`); COMMAND_LONG'a `kabul/ret/sessiz` cevabı (`:198-218`).
- **`scripts/mavlink_dogrula.py`** — ön-uçuş kapısı: beklenen sysid'den HEARTBEAT (15 s tavan, `:57`), `SET_MESSAGE_INTERVAL` isteği (en iyi çaba, ACK 1 s), 10 s ölçüm penceresinde Hz = sayı/süre; HEARTBEAT ≥ 0,5, GLOBAL_POSITION_INT ≥ 4, EXTENDED_SYS_STATE ≥ 1 Hz değilse exit 1 (`:256-313`, `:370-373`, `:491`).
- **`scripts/sik_rf_olc.py`** — iki SiK ile `CMD(RF_PROBE)`→`ACK` RTT ölçer; p95 < `IKA_GO_TEKRAR_ARALIGI_S`(0,25) ve < `PARASUT_TEKRAR_ARALIGI_S`(0,20) → UYUMLU (0), aşıyorsa UYARI (1), hiç ACK yok/port açılamadı → OLCULEMEDI (2) (`:24-31`, `:246-251`). NEDEN: RTT tekrar aralığını aşarsa ACK yoldayken komut yeniden gider, hat boğulur (`:9-14`).

---

## 4. `yks_gui.py` — hakem ekranı

### 4.1 Ne gösterir
Docstring (`:1-25`): gerçek protokol trafiğini dinler (OPEN_ROUTE/NO_ROUTE/IHA_LANDED/HEARTBEAT/ACK), 50×50 m HTAB haritasında rotayı çizer, düğüm canlılığını (heartbeat yaşı) gösterir, hakem onayı **düğmeyle** verilir → ACK ancak o zaman döner. Paneller (`_arayuz_kur` `:854-1182`): saha haritası / canlı algı (üretim modeliyle gerçek çıkarım) / RAW kamera görünümleri; "AÇIK YOL TESPİTİ" kutusu (telsiz vs. yerel algı **karıştırma yasağı**, T81 `:1193-1246`); hakem onayı; rota analizi; düğüm durumu + Pixhawk modu + ham GNSS; mesaj günlüğü; kronometreler (İHA 15:00, İKA 10:00, hazırlık 15:00 — `karar_sozlesmesi`'nden, `:671-673`); görev düğmeleri: ALAN GİRİŞİ / TAKIM HAZIR / MÜDAHALE(−100) / ARM / FIRLATMA / İHA İNDİ / PARAŞÜT(−50) / İKA BAŞLAT / HB TEMAS / ACİL RTL / ACİL LAND (`:1127-1155`). Ana döngü `_tik` 120 ms (`:1503`); ağ dinleyici ayrı thread (`_dinle` `:1436-1460`), UDP'de datagram başına taze FrameReader.

### 4.2 `--fda` kipi (CONTRACTS §6.7, D-407)
Şartname §5.3.2 "Drone ile Görev Test Uçuşu": çoklu rotor, 20×20 m alan, ≥30 m, **İKA yok, paraşüt yok, mancınık yok**, kalkış→iniş ≤ 10 dk. `fda_kipini_uygula` (`:3607-3629`): `IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S` (600 s); FIRLATMA etiketi "KALKIŞ ZAMANI / KRONOMETRE"; PARAŞÜT ve İKA düğmeleri kapalı. Kilitler düğmede değil eylemde: `parasut()` link'e hiçbir şey yazmaz (`:3636-3639`), `ika_baslat()` IKA_GO göndermez (`:3490-3493`), `onayla()` 2/2'de İKA ACK kanıtı **aramaz** — dayanak "YKS'de canlı görüldü + hakem onayı" (`:1885-1895`, `:1914-1916`). Ölçülen tıkanma: yarışma kipinde 2/2 `ika_aktarim_kaniti_var()` ister; FDA'da İKA olmadığından onay hiç tamamlanmıyor, İHA'ya ACK gitmiyordu (`CONTRACTS.md:414-418`).

### 4.3 Hakem ekranı gereksinimleri (şartname §2.2.3 / §6.2, koddaki karşılıkları)
- **İki aşamalı onay** `onayla` (`:1842-1939`): 1/2 "tespit doğrulandı" → 2/2 "İKA'ya aktarıldı" ancak İKA'dan `ACK(ref=rota.seq, ref_tip∈{None,"OPEN_ROUTE"})` görüldüyse (`ika_rota_ack`, `:2080-2100`); ACK `ref_tip` ile yazılır (`:1900-1905`), `HAKEM_ONAYI_2` kaydı ACK link'e yazıldıktan sonra düşer (`:1920-1926`).
- Fail-closed ret sebepleri: `ANKOR_YOK` (rota şeride yerleştirilemedi, `:1860-1864`), `BAYAT_TESPIT` (`:1868-1873`), `IKA_ACK_KANITI_YOK` (`:1889-1895`).
- **Tazelik** `_tespiti_yaslandir` (`:3778-3905`): yaş = min(son OPEN_ROUTE yaşı, son İHA heartbeat yaşı) > `YKS_TESPIT_TAZELIK_S`=5 s → BAYAT; ek olarak `karar_yas` (A2/D-381): alan geldiyse etkin yaş = değer + geçen süre; alan **hiç gelmediyse taze sayılmaz** ("bilinmiyor"). Bayatlık simetriktir (T176): tazelik dönünce düğme kendiliğinden açılır. Onaylanmış tespit sonradan bayat işaretlenmez (D-321).
- Güven eşiği altı OPEN_ROUTE: ACK **üretilmez**, `ROTA_REDDEDILDI` kaydı (`:1787-1822`). NO_ROUTE ve IHA_LANDED: ACK **otomatik** (`:1630-1634`, `:1669-1673`) — bunlar rota onayı değil teslim kanıtıdır.
- Aktarım havadayken bitmeli (§2.2.3): İKA ACK kanıtı anında `_iha_havada_mi` damgası (`:2085-2096`); iniş kanıtı İKA ACK'inden önce gelirse KIRMIZI ihlal riski (`:1687-1693`).
- **Kanıt kaydı** (CONTRACTS §6.8): 16 olay `KANIT_OLAYLARI` (`:127-144`); `KAMERA_KANIT`/`TELEMETRI_KANIT` kenar olayı + 30 s tekrar (`:151`, `_kanit_durumu_yaz` `:4129-4157`); her `_logla` satırı `UI_OLAYI` olarak diske düşer (`:4164`). Kayıt dosyası açılamazsa kurucu yükseltir (`:823-828`).
- **Oturum künyesi** `yki_oturum_kunyesi` (`:440-474`): kip, dinleme, hedefler, kamera, model id/dosya/imgsz/sha256, repo commit, çalışma ağacı durumu (TEMİZ/KİRLİ), `yks_gui.py`'nin kendi SHA-256'sı, başlatma argümanları → `YKS_ARAYUZ_HAZIR` satırına.

### 4.4 Güvenlik kilitleri
- **Tek sahip UDP portu**: `yks_udp_linki_ac` `reuse=False` (`:393-395`, `:4425-4430`).
- **Protokol zarfı kilidi** (`protokol_kilidi`, demo dışı): `v != 1` veya tip string değilse ret (`:1522-1530`); heartbeat seq geri/tekrar ise ret (`_heartbeat_sirasi_gecerli` `:1505-1519`).
- **Kaynak kilidi** `mesaj_kaynagi_dogrula` (`:632-663`): İHA verisi (OPEN_ROUTE/NO_ROUTE/IHA_LANDED/HEARTBEAT iha) Jetson IP'sinden; İHA ACK'i tam `--iha` ucundan; İKA verisi tam `--ika` ucundan; seri taşıyıcıda adres doğrulanamaz. Heartbeat pinlenen adresi ezemez (`_dugum_adresini_ogren` `:3080-3083`).
- **Telemetri doğrulama** `heartbeat_telemetrisi_dogrula` (`:494-569`): bool/NaN/Inf/bant dışı alan alan alan elenir; lat/lon ve x/y çiftleri birlikte düşer; `mod` ≤ 32 ASCII karakter (`:173`). Her heartbeat snapshot'tır — eski değer saklanmaz (`:1726-1741`).
- **Kritik komut teyidi**: ARM/DISARM/RTL/LAND iki tık, `DISARM_TEYIT_SURESI_S`=4 s (`karar_sozlesmesi.py:2092`; `_kritik_teyit_al` `:3157-3184`); paraşüt 3 s "EMİN MİSİN?" (`:3641-3651`). Modal yok (demo akışını kilitler).
- **ARM gerçeği**: `armed` yalnız Pixhawk HEARTBEAT'inden (`arm_telemetri_degeri` `:483-491`); `_arm_durumu_taze_mi` 2,5 s (`:3140-3145`); FIRLATMA yalnız taze HEARTBEAT ile ARM doğrulanmışsa (`firlatma` `:3449-3457`, P9b/D-393).
- **Saat kilidi (D-422, İHA tarafı)**: bkz. §6. YKS tarafı kronometreleri `time.monotonic` ile ölçer (`:3458-3461`); tüm tazelik damgaları monotonik (D-384).
- **Model soyu**: hakem ekranı model adını `config/model_registry.json` etkin profilinden okur (`_uretim_modeli_adi` `:279-296`); yüklerken `resolve_model(verify=True)` SHA-256 + `imgsz` uyumu (`_dogrulanmis_algi_modeli_yukle` `:299-328`); uyuşmazsa hiç yüklenmez. Kabul kümesi kökü de profilden (`_kabul_kumesi_koku` `:354-378`).
- **Kanıt kaydı kilidi**: yazma hatası → `kanit_kaydi_hatasi` kalıcı; yalnız FIRLATMA ve ONAY kapanır, ARM/DISARM/RTL/LAND açık kalır (`:153-167`, `:4029-4116`).
- **§2.2.5 kilidi** `ika_baslat` (`:3487-3525`): `iha_landed_seq` yoksa ve hakem onayı yoksa IKA_GO gönderilmez; `IKA_GO` `0,25 s × 20` tekrar; VAZGECILDI'de kronometre sıfırlanır, düğme yeniden açılır (`:3527-3544`).

---

## 5. MAVLink — bu projede kullanıldığı kadarıyla

MAVLink, Pixhawk'ın konuştuğu ikili paket protokolüdür; Python'da `pymavlink.mavutil.mavlink_connection(adres)` ile açılır (`inis_kaniti.py:73-81`). Her paket **sysid** (araç kimliği; ArduPilot `SYSID_THISMAV` varsayılanı **1**, `iha_komut_alici.py:105-107`; `config/pixhawk/README.md:20`) ve **compid** (bileşen; otopilot `MAV_COMP_ID_AUTOPILOT1`=1) taşır — bu proje yabancı sysid'nin paketlerini kanıt saymaz. **HEARTBEAT** aracın ~1 Hz canlılık mesajıdır; `base_mode & MAV_MODE_FLAG_SAFETY_ARMED` biti ARM durumunu, `mode_string_v10` uçuş modunu verir (`inis_kaniti.py:273-288`, `:339-347`). **GLOBAL_POSITION_INT** konum/`relative_alt` (mm)/hız, **EXTENDED_SYS_STATE** `landed_state`, **GPS_RAW_INT** fix/uydu, **SYS_STATUS** pil. **COMMAND_LONG** genel komut zarfıdır (`target_system, target_component, command, confirmation, param1..7`); Pixhawk buna **COMMAND_ACK**(`command, result`) döner; `MAV_RESULT_ACCEPTED` kabul demektir — bu projede YKS'ye ACK dönmenin tek koşulu budur. Akış hızları `MAV_CMD_SET_MESSAGE_INTERVAL` (param1 = mesaj id, param2 = aralık µs) ile istenir. Seri Pixhawk portu tek sahipli olduğundan Jetson'da bir çoğullayıcı (MAVProxy `--out udp:127.0.0.1:1455N`, `--streamrate 8` D-406 B, `config/pixhawk/README.md:165-170`) portu açar ve her tüketici kendi UDP ucundan konuşur. `FS_GCS_ENABLE=1` "Jetson-bağlantı failsafe"i olarak kalır (D-406 C, `README.md:143-148`).

---

## 6. Güvenlik / dayanıklılık kararları ve kusur kayıtları (NEDEN'ler kodun kendi ifadesiyle)

| Karar | Kusur kaydı | Kodun NEDEN'i (özet/alıntı) | Yer |
|---|---|---|---|
| ACK yalnız Pixhawk `COMMAND_ACK ACCEPTED` | D-393, D-403 ÖNEMLİ-3 | "pymavlink'in her tasiyicisi write() hatasini YUTAR … 'istisnasiz gonderildi' kanit degildir … Tek durust olcut COMMAND_ACK(command == mav_cmd, result == ACCEPTED)" | `iha_komut_alici.py:546-551` |
| İHA'da `(cmd, seq)` idempotentliği **yok** | D-403 KRİTİK-2 | "YKS her acilista seq'i 1'den baslattigi icin yeniden acilan YKS'nin PARACHUTE'u 'mukerrer' sayilip MAVLink'e HIC gitmeden ACK'laniyordu — yesil 'IHA ALDI', parasut kapali" | `:20-26` |
| Oturumlu tekrar anahtarı `(oturum, seq, cmd)` | K-2 | "MAVLink'e HİÇ ULAŞMAMIŞ teşebbüs … terminal DEĞİLDİR … Anahtarı aktarımdan ÖNCE False yazmak … ARM/DISARM/RTL/LAND/PARACHUTE bir daha asla geçemezdi" | `:726-740` |
| `--iha` ile komut alıcısı adresi pinlenir | D-403 KRİTİK-1 | "iha adresi yalnız heartbeat/OPEN_ROUTE kaynağından öğreniliyordu — o adres rpi_inference'ın EFEMER portudur … PARACHUTE komutu sahada alıcıya HİÇ ulaşmazdı" | `yks_gui.py:731-737` |
| `udp:` sunucu kipinde akran görülmeden gönderim yok | D-403 | "pymavlink `mavudp.write` … kume bossa HICBIR SEY gondermez ve socket hatasini yutar" | `iha_komut_alici.py:251-269` |
| COMMAND_ACK yetkili bileşen kümesi | K-3 (3 Eylül ölçümü) | "sahte Pixhawk gerçek ArduPilot gibi component=1'den ACK basar, alıcı `--target-component 3` ile açılınca HER ACK 'yabancı' sayıldı ve PARACHUTE/ARM/DISARM/RTL/LAND uçtan uca DÜŞTÜ" | `:584-604` |
| **Saat kilidi K-A/K-1**: mutlak sapma filtresi kaldırıldı, iki kademeli kanıt eşiği (bant içi 2 örnek, bant dışı 6 destekleyen) | **D-422** | "Öyleyken ÖLÜMCÜLDÜ: ofset bilinmezken `ham` iki saatin FARKI'dır; sapma bu tavanı aşınca öğrenmek için gereken örneğin TA KENDİSİ eleniyordu -> ofset ASLA öğrenilemiyor -> ARM/DISARM/RTL/LAND/PARACHUTE KALICI olarak reddediliyordu. ÖLÇÜLDÜ (2 saat sapma, ARM merdiveni 20/20): MAVLink'e giden 0" | `:161-191`; `REVIEW_LOG.md:29432+` |
| **K-B** yerel saat adımı monotonik/duvar farkından ölçülür, pencere kaydırılır | D-422 §2 KARAR-2 | "ÖLÇÜLDÜ (ofset -600 s öğrenildi, saat +600 s ileri adımlandı): ARM yeniden geçene kadar 60,00 s ÖLÜ pencere, 241 komut reddi" · reddedilen alternatif (trafikten adım çıkarma): "bayat damgalı yeni bir `seq` 10. ısrarda kapıdan GEÇTİ ve MAVLink'e ULAŞTI" | `:193-226`, `:420-445` |
| **K-C** aday ofset küresel `min` değil, küçükten büyüğe taranır | 2026-09-04 çürütme | "Küresel `min`'e tek adayla bağlanmak bu kapıyı TEK PAKETLE kilitliyordu … 60,75 s ÖLÜ" | `:382-400` |
| Ofset bilinirken reddedilen çerçeve örneklenmez | 3–4 Eylül ölçümü | "ısrarlı ileri/bayat damgalı bir kaynak, kendi reddedilen örnekleriyle ofseti kendi üzerine çeker" | `:685-696` |
| Tek sahipli seri Pixhawk — kod kilidi | D-403, FDR §4b #23 | "Kural CONTRACTS §7.4'te yaziliydi ama YALNIZ `iha_komut_alici`da KODLUYDU; diger iki surec 'yordamla' korunuyordu — yani korunmuyordu" | `inis_kaniti.py:84-100` |
| SiK hub | D-404, D-405 | Üç süreç aynı `/dev/ttyUSB0`; `SO_REUSEADDR`'siz UDP, `exclusive=True` seri, RecursionError yutma, 65535 B datagram, newline ekleme, SIGTERM | `seri_hub.py:2-68` |
| `SerialLink.recv` ilk bayt + `in_waiting` | D-403 | "ACK turu p50 622,6 ms … parasut tekrar araligi 0,20 s'nin UC KATI … Simdi 0,8 ms" | `link.py:106-120` |
| ACK eşlemesinde `ref_tip` | D-405 Q4 / T206 | "OPEN_ROUTE seq=7 bekleyen gonderici, IHA_LANDED seq=7 icin uretilmis IKA ACK'ini de 'aktarildi' sayiyordu" | `iha_sender.py:193-200` |
| ACK penceresinden erken çıkış | D-383 | "'telsiz_ack ~308 ms' sayisi ACK gecikmesi degil o sabitin olcumuydu (gercek loopback RTT 0,06 ms)" | `:204-214` |
| Heartbeat alan toplama kendi try'ında | T171 / D-320 | "eksik bir oznitelik (AttributeError) … dongu sonsuza kadar donuyor, TELSIZ SESSIZCE SUSUYORDU" | `:454-461` |
| `karar_yas` heartbeat'te | A2 / D-381, D-374 | "gercek ucusta algi 45-51 s'lik sahne bagintili araliklarda HIC karar uretemiyor — o aralikta hat CANLI gorunur, algi OLUDUR" | `protocol.py:93-102` |
| Tüm tazelik damgaları monotonik | D-384, D-383 | "duvar saati (NTP/elle duzeltme) geri atlarsa BAYAT tespit TAZE gorunuyordu" | `yks_gui.py:1553-1557`, `:3807-3810` |
| EXTENDED_SYS_STATE periyodik isteği | T207 / D-406 A | "istek bağlantıya özeldir ve Pixhawk yeniden başlayınca (pil değişimi) silinir … reboot sonrası kanıt SESSİZCE ölür" | `iha_inis_yayinci.py:6-14` |
| Yabancı sysid kanıt değildir, atlanır | D-389 B1 | "Eski davranis (gecersiz kil) ucuncu bir tarafa bizi kor etme yetkisi veriyordu (D-387: erisilebilirlik 0/193)" | `inis_kaniti.py:567-572` |
| ON_GROUND dışı durum terminal değil | D-389 A2 | alçalma sırasında başlatılan doğrulama gerçek temastan sonra kanıt üretebilsin | `:1030-1037` |
| IKA_GO ACK'lı tekrar | D-02 / K4, K8 | "tek paket kaybı görevi geri dönülmez bitirir" | `komut_tekrar.py:1-3`; `CONTRACTS.md:352-355` |
| K8 aktarım kanıtı, `--yks` fiilen zorunlu | dalga 2 çürütücüsü | "OPEN_ROUTE IKA_GO'dan önce gelir, yani YKS adresi öğrenilmeden rota ACK'ı üretilir; --yks yoksa kopya HİÇ gitmez" | `CONTRACTS.md:378-383`; `ika_receiver.py:32-37` |
| FDA kipi | D-407 | "hakem onayı 2/2 adımı `ika_aktarim_kaniti_var()` ister … FDA'da İKA olmadığı için bu kanıt hiç gelmez → onay tamamlanamaz" | `CONTRACTS.md:414-418` |
| Kanıt kaydı kilidi fail-closed + fail-visible | 2026-09-03 ölçümü | "KIRMIZI afiş ekranda kalıyor, düğmeler çalışıyordu — ekran ile gerçek AYRIŞIYORDU" | `yks_gui.py:153-167`, `:4029-4042` |
| `yks_monitor` emekli | D-392 | otomatik hakem onayı kapıyı deler | `yks_monitor.py:1-15` |
| Test portları efemer | T209 / D-427 | sabit 5005/5006 saha PC'sinde WinError 10013 | `test_comms.py:34-44` |
| UDPLink `ConnectionResetError` yutma | D-06 | YKS dinleyici thread'i tek ölü akranla kalıcı ölüyordu | `link.py:52-63` |
| Çerçeve tampon tavanı 64 KiB | P2 / D-388 | "1 MiB çöp → 1 MiB tampon" | `protocol.py:227-231` |

---

## 7. On muhtemel jüri sorusu ve kodla desteklenen kısa cevap

1. **"Paraşüt komutunun gerçekten uçağa ulaştığını nereden biliyorsunuz?"** — YKS "İHA ALDI" demeden önce `kritik_komut_ack_gecerli_mi` ile `ref/node/ref_tip/ref_cmd/sonuc=ACCEPTED` beş alanı birden ister (`protocol.py:150-171`); İHA bu ACK'i yalnız Pixhawk'ın `COMMAND_ACK(result=MAV_RESULT_ACCEPTED)`'i 0,5 s içinde gelirse üretir (`iha_komut_alici.py:544-608`, `:770-779`). Ret/zaman aşımı ekranda kırmızı "ACK YOK" olur. Mekanik açılma için ayrı sensör yok — ekran bunu açıkça yazar (`yks_gui.py:2042-2046`).
2. **"Telsiz bir paketi düşürürse ne olur?"** — Tüm kritik mesajlar ACK gelene dek aynı seq ile tekrarlanır: OPEN_ROUTE/NO_ROUTE/IHA_LANDED 8×0,25 s (`iha_sender.py:171`), IKA_GO/ARM 0,25 s×20, PARACHUTE 0,20 s×40 (`karar_sozlesmesi.py:2081-2103`). Alıcı mükerrer alımı idempotent işler (`ika_receiver.py:289-290`; İHA'da oturum anahtarı `iha_komut_alici.py:716-721`). SiK RTT'nin bu aralıkların altında olduğu `scripts/sik_rf_olc.py` ile ölçülür.
3. **"Hakem bayat bir tespiti onaylayabilir mi?"** — Hayır. `_tespiti_yaslandir` 5 s tazelik (`YKS_TESPIT_TAZELIK_S`) + `karar_yas` ile onay düğmesini kapatır; `onayla()` düğme kapalıyken çağrılsa bile `BAYAT_TESPIT` ile reddeder ve kayda yazar (`yks_gui.py:1868-1873`, `:3778-3905`).
4. **"İKA, İHA inmeden hareket edebilir mi?"** — Hayır: İKA'da sürüş izni `ika_go ∧ iha_landed` latch'i (`ika_receiver.py:127-138`); `IHA_LANDED` yalnız Pixhawk `EXTENDED_SYS_STATE=ON_GROUND` + `relative_alt<1 m` 3 ardışık çift ile üretilir (`inis_kaniti.py:937-1065`); YKS'de `ika_baslat` da `iha_landed_seq` olmadan IKA_GO göndermez (`yks_gui.py:3497-3501`). Operatör düğmesi latch kuramaz (`protocol.py:201-203`).
5. **"Aktarımın İHA havadayken tamamlandığını nasıl kanıtlıyorsunuz?"** — İKA'nın OPEN_ROUTE ACK kopyası YKS'ye gelir (K8, `ika_receiver.py:175-195`); YKS o anda `_iha_havada_mi` (taze heartbeat ∧ iniş kanıtı yok) damgasını `IKA_AKTARIM_KANITI` satırına yazar (`yks_gui.py:2085-2096`); iniş kanıtı ACK'ten önce gelirse kırmızı ihlal riski loglanır (`:1687-1693`). Kayıt `hakem_log.jsonl`'de fsync'lidir.
6. **"Jetson'ın saati yanlışsa (RTC yok) komutlar reddedilir mi?"** — Eskiden evet (D-422: 2 saat sapmada ARM 0/20). Şimdi alıcı, YKS damgası ile kendi saati arasındaki ofseti NTP minimum-filtresi mantığıyla öğrenir (bant içi 2, bant dışı 6 destekleyen örnek), yaşı ofsete göre ölçer; yerel saat adımı monotonik/duvar farkından yakalanıp pencere kaydırılır (`iha_komut_alici.py:132-226`, `:361-491`). Bedeli: sapma varken merdivenin ilk 2 basamağı reddedilir, 3.'de geçer (`:152-154`).
7. **"İki süreç aynı seri portu açarsa?"** — Açamaz: Pixhawk için `--mavlink /dev/tty*` üç süreçte de exit 2 ile reddedilir (`inis_kaniti.py:136-143`); SiK için yalnız `seri_hub` `exclusive=True` ile açar, ikinci süreç flock'a takılır (`link.py:88-100`); hub'ın UDP ucu `SO_REUSEADDR`'siz (exit 3), YKS portu da öyle (`yks_gui.py:393-395`).
8. **"Sahte/başka bir kaynaktan gelen komut veya ACK'i nasıl eliyorsunuz?"** — İHA komut alıcısı `--izinli-kaynak` tam UDP pinini zorunlu tutar (`iha_komut_alici.py:636-646`, `:888-890`); YKS `mesaj_kaynagi_dogrula` ile İHA verisini Jetson IP'sine, ACK'leri tam uçlara bağlar (`yks_gui.py:632-663`); `IhaSender` ACK'i yapılandırılmış akran adresinden ister (`iha_sender.py:104-125`); MAVLink tarafında COMMAND_ACK'in sysid/component'i denetlenir (`iha_komut_alici.py:572-604`); iniş kanıtında yabancı sysid atlanır (`inis_kaniti.py:1017-1022`).
9. **"Ekranda gördüğünüz ARM durumu komutu gönderdiğiniz için mi yeşil?"** — Hayır. `armed` yalnız Pixhawk HEARTBEAT'inden gelir (`protocol.py:106-109`; `inis_kaniti.py:273-288`); YKS "ARM DOĞRULANDI" için güçlü ACK **ve** 2,5 s içinde beklenen `armed` değerini taşıyan taze heartbeat ister (`yks_gui.py:3223-3238`); FIRLATMA ancak bundan sonra açılır (`:3449-3457`).
10. **"Kanıt kaydınız uçuş sonrası neden güvenilir?"** — `HakemKaydi` her satırda `flush`+`fsync` yapar, oturum uuid'si ve monotonik damga taşır (`hakem_kaydi.py:78-94`); olay kümesi CONTRACTS §6.8 tablosuyla üç yönlü testle kilitlidir (`yks_gui.py:121-144`); `YKS_ARAYUZ_HAZIR` satırı model SHA-256'sı, repo commit'i, çalışma ağacı durumu ve `yks_gui.py`'nin kendi özetini içerir (`:440-474`); kayıt yazılamıyorsa FIRLATMA/ONAY kapanır, ARM/acil açık kalır (`:153-167`).

---

### Doğrulanamayan / dikkat noktaları
- `iha_komut_alici` örnek ucu 14560 vs. sözleşme 14552 (`iha_komut_alici.py:42`, `CONTRACTS.md:1112`) — servis dosyasındaki gerçek değer **DOĞRULANAMADI**.
- İKA'nın saha hattı (SiK çok-noktalı mı, WiFi mi) — `CONTRACTS.md:1150-1152` "topolojiyle karara bağlanır" der; karar **DOĞRULANAMADI**.
- `comms/README.md:68` eski "915 MHz" notu; güncel tasarım 433 MHz.
- `sahte_pixhawk` `MAV_TYPE_FIXED_WING` basar (`:164`); FDA testi ArduCopter ile yapılır — yalnız çerçeve/sözleşme katmanını kapatır (`:9-11`).
