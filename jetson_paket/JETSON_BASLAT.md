# JETSON AÇILIŞ — `jetson_baslat.sh` (Faz B · Görev C · 2026-09-02)

> **NEDEN:** şartname §6.2 thazırlık — Jetson **tek komutla** kalkar; hands-off sonrası ölen süreç **kendi kalkar** (`systemd Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`). CONTRACTS §7.4 (D-403): seri Pixhawk **tek sahipli** — portu yalnız çoğullayıcı (MAVProxy) açar; uçlar `udp:127.0.0.1:14550/14551/14552` ve `--sysid`/`--mav-sysid` pinleri belgede değil **kodda** (`jetson_baslat.sh` + `systemd/*.service`); `tests/test_faz_b_jetson_baslat.py` bunları CONTRACTS metniyle kilitler.

## Kullanım (Jetson; `~/navitas` kurulumu `JETSON_KILAVUZ.md` §2'ye göre yapılmış, `pip3 install MAVProxy` kurulu)

1. **ÖNCE `--kuru` İLE BAK — hiçbir şey başlatmaz:** `KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<derece> bash jetson_paket/jetson_baslat.sh --kuru`
   Çıktı: yazılacak `/etc/navitas.env`, birim başına **koşulacak komut**, paket denetimi (`[VAR]/[YOK]`), beyan denetimi (`[EKSIK]` varsa çıkış **3** — gerçek koşum durur).
2. **Kur ve kaldır (kalıcı; açılışta da kalkar):** `sudo -E KIP=udp YKS_IP=… IKA_IP=… FOV=… bash jetson_paket/jetson_baslat.sh` → `/etc/navitas.env` + `/etc/systemd/system/navitas-*.service`, `enable --now`; thazırlık süresini basar.
3. **Kapılı kaldırış (FAZ_B_GUN_PLANI §1):** `… --kapi` — yalnız çoğullayıcıyı kaldırır, üç uçta `scripts/mavlink_dogrula.py --sysid <SYSID>` koşar; **3/3 GEÇTİ** değilse tüketiciler başlatılmaz (fail-closed). `mavlink_dogrula.py` `~/navitas/scripts/` altında olmalı (paket **taşımıyor** — depodan kopyalanır).
4. **Durum:** `bash jetson_paket/jetson_baslat.sh --durum` — birim başına `is-active` + yeniden-başlatma sayısı; sayı **artıyorsa çökme döngüsü**: `journalctl -u navitas-<birim> -n 50`.
5. **SiK 433 MHz:** `KIP=sik` (YKS_IP/IKA_IP gerekmez; `SIK_SERI=/dev/ttyUSB0`) — `navitas-seri-hub` de kalkar, üç süreç `127.0.0.1:5100` üzerinden hub'a yazar; `/dev/ttyUSB0`'ı yalnız hub açar.
6. **systemd'siz prova:** `--dogrudan` (nohup + `results/jetson_log/<birim>.log`; **gözcü yok**, ölen süreç kalkmaz). **Durdur:** `sudo bash … --durdur`.
7. **Değişkenler** (ortamdan ezilir): `PIXHAWK_SERI=/dev/ttyACM0 PIXHAWK_BAUD=57600 SYSID=1 KIP=udp|sik SIK_SERI=/dev/ttyUSB0 SIK_BAUD=57600 FOV|ODAK SENARYO KAMERA UB_REFERANS KANIT_TIMEOUT=900 NAVITAS_KOK=/home/navitas/navitas`. `FOV`/`ODAK` ve (udp'de) `YKS_IP`/`IKA_IP` **beyan edilir** — varsayılanı yoktur.
8. YKS tarafı `yks_gui --iha <JETSON_IP>:5007` ile açılır (D-403 KRİTİK-1); İKA `saha_baslat.py ika --yks <YKS_IP>:5005`.

## Birimler (`systemd/`; hepsi `Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`, `EnvironmentFile=/etc/navitas.env`)

| birim | ne | MAVLink ucu (CONTRACTS §7.4) | kip |
|---|---|---|---|
| `navitas-cogullayici` | MAVProxy: `/dev/ttyACM0`'ın **tek sahibi**, `--out` ×3 | üretir: 14550/14551/14552 | udp+sik |
| `navitas-seri-hub` | SiK `/dev/ttyUSB0`'ın tek sahibi; `127.0.0.1:5100` → seri, seri → `--tuketici 127.0.0.1:5007` | — | **yalnız sik** |
| `navitas-rpi-inference` | `rpi_inference --camera` (algı + OPEN_ROUTE/NO_ROUTE + HEARTBEAT) | `udp:127.0.0.1:14550` `--mav-sysid` | udp+sik |
| `navitas-iha-inis-yayinci` | Pixhawk kanıtlı `IHA_LANDED` (`--kanit-timeout 900`) | `udp:127.0.0.1:14551` `--sysid` | udp+sik |
| `navitas-iha-komut-alici` | YKS PARAŞÜT/ARM → `COMMAND_LONG`, ACK yalnız ACCEPTED'de | `udp:127.0.0.1:14552` `--sysid` (yazar) | udp+sik |

Tüketiciler `After=`/`Wants=navitas-cogullayici.service` ile çoğullayıcıya bağlıdır; hiçbiri `/dev/tty*` açmaz (test kilidi).

## Kapatılan blokerler (2026-09-03, D-404) ve kalan uyarılar

- **Ekransız kip (kapatıldı):** `rpi_inference --camera` eskiden her karede koşulsuz
  `cv2.imshow` çağırır, ekransız Jetson'da ilk karede çöküp `Restart` döngüsüne
  girerdi. Birim artık `--ekransiz` ile koşar (pencere/`waitKey` yok; karar yolu
  bayt-eş aynı — `tests/test_faz_b_rpi_ekransiz.py`). `DISPLAY`/`XAUTHORITY`
  birimden kaldırıldı.
- **`comms/seri_hub.py` (kapatıldı):** CONTRACTS §7.5; CLI `--port --baud --bind
  --tuketici`; pakette `kod/seri_hub.py` (KOPYALAR). Hub gönderen tüketicileri
  **öğrenir**: `rpi_inference` ve `iha_inis_yayinci` hub'a yazdıkları için
  YKS ACK'leri onlara döner; yalnız dinleyen `iha_komut_alici` `--tuketici`
  ile statik verilir. `mavlink_dogrula.py` de pakettedir (`kod/` →
  `~/navitas/scripts/`, `--kapi` için).
- **SiK kipinde İKA hattı (AÇIK — cumartesi):** SiK genelde iki radyoyla
  **noktadan noktaya** (Jetson↔YKS) çalışır. `KIP=sik`'te betik bilerek yalnız
  `--yks-hedef 127.0.0.1:5100` / `--yks 127.0.0.1:5100` verir (tek hatta bir
  kez; test K2). İKA'ya OPEN_ROUTE/IHA_LANDED'ın **nasıl ulaşacağı** (İKA da SiK
  çok-noktalı mı, WiFi'da mı — o zaman `--ika-hedef <IKA_IP>:5006` ayrıca
  verilir) **topolojiyle karara bağlanır**; bugün varsayım yazılmadı.
- **Windows kopyası CRLF taşır** (`core.autocrlf=true`): betik ilk satırında CR görürse CR'siz kopyasıyla yeniden koşar; birim dosyaları kurulurken `tr -d '\r'` ile yazılır. `bash jetson_baslat.sh …` ile çağırın (`./jetson_baslat.sh` shebang'i CR yüzünden bozulabilir).
