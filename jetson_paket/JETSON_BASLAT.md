# JETSON AÇILIŞ — `jetson_baslat.sh` (Faz B · Görev C · 2026-09-02)

> **NEDEN:** şartname §6.2 thazırlık — Jetson **tek komutla** kalkar; hands-off sonrası ölen süreç **kendi kalkar** (`systemd Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`). CONTRACTS §7.4 (D-403): seri Pixhawk **tek sahipli** — portu yalnız çoğullayıcı (MAVProxy) açar; uçlar `udp:127.0.0.1:14550/14551/14552` ve `--sysid`/`--mav-sysid` pinleri belgede değil **kodda** (`jetson_baslat.sh` + `systemd/*.service`); `tests/test_faz_b_jetson_baslat.py` bunları CONTRACTS metniyle kilitler.

## Kullanım (Jetson; `~/navitas` kurulumu `JETSON_KILAVUZ.md` §2'ye göre yapılmış, `pip3 install MAVProxy` kurulu)

> ⚠ **Orin Nano (6 Eylül ölçümü, D-431):** kurulum `JETSON_ORIN_NANO_KURULUM.md` §1–2 ile yapıldı (JetPack 7.2.1, Python 3.12). `--kuru` ölçüldü: tüm dosya ve yorumlayıcılar `[VAR]`, `[YOK]` yalnız `/dev/ttyACM0` (Pixhawk bağlı değildi) → çıkış 3, beklenen; `--kapi` **ÖLÇÜLEMEDİ**. Birimler için `PYTHON3=/home/n4vitas/venv312/bin/python` (kullanıcı `n4vitas`; `SUDO_USER`'dan türer), MAVProxy venv312'de ve `~/.local/bin/mavproxy.py` symlink; köprü `/usr/bin/python3` (sistem cv2 4.6, GStreamer'lı); paket kökü `~/navitas` symlink.

1. **ÖNCE `--kuru` İLE BAK — hiçbir şey başlatmaz:** `KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<derece> bash jetson_paket/jetson_baslat.sh --kuru`
   Çıktı: yazılacak `/etc/navitas.env`, birim başına **koşulacak komut**, paket denetimi (`[VAR]/[YOK]`), **ana makine denetimi** (kullanıcı, yorumlayıcı, seri cihaz, kurulu `.py` — salt okunur), beyan denetimi. **Herhangi bir `[YOK]` ya da `[EKSIK]` varsa `KURU SONUC: eksik` + çıkış 3** — gerçek koşum tam o yerde dururdu (D-405: kuru rapor yalan söylemez). Bir değer boşluk/glob/kaçış içeriyorsa `[UYARI]` basar (systemd ve bash onu böler).
2. **Kur ve kaldır (kalıcı; açılışta da kalkar):** `sudo -E KIP=udp YKS_IP=… IKA_IP=… FOV=… bash jetson_paket/jetson_baslat.sh` → `/etc/navitas.env` + `/etc/systemd/system/navitas-*.service`, `daemon-reload`, `enable` + **`restart`**; thazırlık süresini basar. **Beyan değişince aynı komutu yeniden koş** — `restart` yeni argümanları canlı sürece uygular (`enable --now` uygulamazdı, D-405).
3. **Kapılı kaldırış (FAZ_B_GUN_PLANI §1):** `… --kapi` — yalnız çoğullayıcıyı kaldırır, üç uçta **aynı anda** `scripts/mavlink_dogrula.py --sysid <SYSID>` koşar (CONTRACTS §7.4 "üç uç aynı anda açıkken"; uç başına log/rc: `results/jetson_log/kapi/<port>.log|.rc`); **3/3 GEÇTİ** değilse tüketiciler başlatılmaz (fail-closed). `mavlink_dogrula.py` `~/navitas/scripts/` altında olmalı (paket **taşımıyor** — depodan kopyalanır).
4. **Durum:** `bash jetson_paket/jetson_baslat.sh --durum` — birim başına `is-active` + yeniden-başlatma sayısı; sayı **artıyorsa çökme döngüsü**: `journalctl -u navitas-<birim> -n 50`.
5. **SiK 433 MHz:** `KIP=sik` (YKS_IP/IKA_IP gerekmez; `SIK_SERI=/dev/ttyUSB0`) — `navitas-seri-hub` de kalkar, üç süreç `127.0.0.1:5100` üzerinden hub'a yazar; `/dev/ttyUSB0`'ı yalnız hub açar.
6. **systemd'siz prova:** `--dogrudan` (nohup + `results/jetson_log/<birim>.log`; **gözcü yok**, ölen süreç kalkmaz). **Durdur:** `sudo bash … --durdur`.
7. **Değişkenler** (ortamdan ezilir): `PIXHAWK_SERI=/dev/ttyACM0 PIXHAWK_BAUD=57600 SYSID=1 KIP=udp|sik SIK_SERI=/dev/ttyUSB0 SIK_BAUD=57600 FOV|ODAK SENARYO KAMERA UB_REFERANS KANIT_TIMEOUT=900 SERVIS_KULLANICI=${SUDO_USER:-${USER:-navitas}} NAVITAS_KOK=/home/$SERVIS_KULLANICI/navitas PYTHON3=/usr/bin/python3 ENV_DOSYA=/etc/navitas.env`. `FOV`/`ODAK` ve (udp'de) `YKS_IP`/`IKA_IP` **beyan edilir** — varsayılanı yoktur. **`SERVIS_KULLANICI`** birimlere `User=` ve `~/.local/bin` (MAVProxy yolu) olarak işlenir; `sudo -E` altında `SUDO_USER` (giriş yapan kullanıcı) alınır, `--kuru`/`--dogrudan` sudosuz `USER` ile aynı kişiyi hesaplar. Kullanıcı yoksa `--kuru` `[YOK] kullanici`, `--kur` `HATA` ile durur (yanlış `User=` systemd 217/USER sonsuz restart döngüsüdür, D-405).
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
- **Windows kopyası CRLF taşır** (`core.autocrlf=true`): betik ilk satırında CR görürse (bash-içi `head -c` algısı, D-405 — Git Bash'te de tetiklenir) CR'siz kopyasıyla yeniden koşar ve `--kuru` başlığına `(CR'siz kopya: …)` basar; birim dosyaları kurulurken `tr -d '\r'` ile yazılır. `bash jetson_baslat.sh …` ile çağırın (`./jetson_baslat.sh` shebang'i CR yüzünden bozulabilir).
- **Kurulum/kapı yolları testte** (`tests/test_faz_b_jetson_baslat.py` K10, D-405): sahte `systemctl`/`sudo`/`id`/`python3`/`mavproxy.py` shim'leriyle `--kur`, `--kapi` (3/3 ve 2/3), `--dogrudan`, `--durdur` Git Bash'te gerçekten koşulur; `restart` çağrısı, CR'siz/sed'lenmiş birim dosyaları, üç ucun **aynı anda** koşması ve 2/3'te tüketicilerin başlatılmaması kilitlidir.
