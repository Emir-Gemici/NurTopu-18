# JETSON AÇILIŞ — `jetson_baslat.sh` (Faz B · Görev C · 2026-09-02)

> **NEDEN:** şartname §6.2 thazırlık — Jetson **tek komutla** kalkar; hands-off sonrası ölen süreç **kendi kalkar** (`systemd Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`). CONTRACTS §7.4 (D-403): seri Pixhawk **tek sahipli** — portu yalnız çoğullayıcı (MAVProxy) açar; uçlar `udp:127.0.0.1:14550/14551/14552` ve `--sysid`/`--mav-sysid` pinleri belgede değil **kodda** (`jetson_baslat.sh` + `systemd/*.service`); `tests/test_faz_b_jetson_baslat.py` bunları CONTRACTS metniyle kilitler.

## Kullanım (Jetson; `~/navitas` kurulumu `JETSON_KILAVUZ.md` §2'ye göre yapılmış, `pip3 install MAVProxy` kurulu)

> ⚠ **Orin Nano (6 Eylül ölçümü, D-431):** kurulum `JETSON_ORIN_NANO_KURULUM.md` §1–2 ile yapıldı (JetPack 7.2.1, Python 3.12). `--kuru` ölçüldü: tüm dosya ve yorumlayıcılar `[VAR]`, `[YOK]` yalnız `/dev/ttyACM0` (Pixhawk bağlı değildi) → çıkış 3, beklenen; `--kapi` **ÖLÇÜLEMEDİ**. Birimler için `PYTHON3=/home/n4vitas/venv312/bin/python` (kullanıcı `n4vitas`; `SUDO_USER`'dan türer), MAVProxy venv312'de ve `~/.local/bin/mavproxy.py` symlink; köprü `/usr/bin/python3` (sistem cv2 4.6, GStreamer'lı); paket kökü `~/navitas` symlink.

1. **ÖNCE `--kuru` İLE BAK — hiçbir şey başlatmaz:** `KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<derece> bash jetson_paket/jetson_baslat.sh --kuru`
   Çıktı: yazılacak `/etc/navitas.env`, birim başına **koşulacak komut**, paket denetimi (`[VAR]/[YOK]`), **ana makine denetimi** (kullanıcı, yorumlayıcı, seri cihaz, kurulu `.py` — salt okunur), beyan denetimi. **Herhangi bir `[YOK]` ya da `[EKSIK]` varsa `KURU SONUC: eksik` + çıkış 3** — gerçek koşum tam o yerde dururdu (D-405: kuru rapor yalan söylemez). Bir değer boşluk/glob/kaçış içeriyorsa `[UYARI]` basar (systemd ve bash onu böler).
2. **Kur ve kaldır (kalıcı; açılışta da kalkar):** `sudo -E KIP=udp YKS_IP=… IKA_IP=… FOV=… bash jetson_paket/jetson_baslat.sh` → `/etc/navitas.env` + `/etc/systemd/system/navitas-*.service`, `daemon-reload`, `enable` + **`restart`**; thazırlık süresini basar. **Beyan değişince aynı komutu yeniden koş** — `restart` yeni argümanları canlı sürece uygular (`enable --now` uygulamazdı, D-405).
3. **Kapılı kaldırış (FAZ_B_GUN_PLANI §1):** `… --kapi` — yalnız çoğullayıcıyı kaldırır, üç uçta **aynı anda** `scripts/mavlink_dogrula.py --sysid <SYSID>` koşar (CONTRACTS §7.4 "üç uç aynı anda açıkken"; uç başına log/rc: `results/jetson_log/kapi/<port>.log|.rc`); **3/3 GEÇTİ** değilse tüketiciler başlatılmaz (fail-closed). `mavlink_dogrula.py` `~/navitas/scripts/` altında olmalı (paket **taşımıyor** — depodan kopyalanır).
4. **Durum:** `bash jetson_paket/jetson_baslat.sh --durum` — birim başına `is-active` + yeniden-başlatma sayısı; sayı **artıyorsa çökme döngüsü**: `journalctl -u navitas-<birim> -n 50`.
5. **~~SiK 433 MHz~~ RFD900A 915–928 MHz:** `KIP=sik` (YKS_IP/IKA_IP gerekmez; `SIK_SERI=/dev/ttyUSB0`) — `navitas-seri-hub` de kalkar, üç süreç `127.0.0.1:5100` üzerinden hub'a yazar; `/dev/ttyUSB0`'ı yalnız hub açar.
6. **systemd'siz prova:** `--dogrudan` (nohup + `results/jetson_log/<birim>.log`; **gözcü yok**, ölen süreç kalkmaz). **Durdur:** `sudo bash … --durdur`.
7. **Değişkenler** (ortamdan ezilir): `PIXHAWK_SERI=/dev/ttyACM0 PIXHAWK_BAUD=57600 SYSID=1 KIP=udp|sik SIK_SERI=/dev/ttyUSB0 SIK_BAUD=57600 FOV|ODAK SENARYO KAMERA UB_REFERANS KANIT_TIMEOUT=900 SERVIS_KULLANICI=${SUDO_USER:-${USER:-navitas}} NAVITAS_KOK=/home/$SERVIS_KULLANICI/navitas PYTHON3=/usr/bin/python3 ENV_DOSYA=/etc/navitas.env`. `FOV`/`ODAK` ve (udp'de) `YKS_IP`/`IKA_IP` **beyan edilir** — varsayılanı yoktur. **`SERVIS_KULLANICI`** birimlere `User=` ve `~/.local/bin` (MAVProxy yolu) olarak işlenir; `sudo -E` altında `SUDO_USER` (giriş yapan kullanıcı) alınır, `--kuru`/`--dogrudan` sudosuz `USER` ile aynı kişiyi hesaplar. Kullanıcı yoksa `--kuru` `[YOK] kullanici`, `--kur` `HATA` ile durur (yanlış `User=` systemd 217/USER sonsuz restart döngüsüdür, D-405).
8. YKS tarafı `yks_gui --iha <JETSON_IP>:5007` ile açılır (D-403 KRİTİK-1); İKA `saha_baslat.py ika --yks <YKS_IP>:5005`.
9. **İşaretli gösterici (T228 · D-443 MK15 video hattı — karar üretmez):** `GOSTERICI_KIP=x11|drm|rtsp|kapali` (varsayılan **`kapali`**: davranış değişmez) ve `ISARETLI_YAYIN=127.0.0.1:8081` (yalnız loopback; LAN'a açılmaz). `kapali` dışında `rpi_inference`'a `--isaretli-yayin $ISARETLI_YAYIN` (T227) verilir; ikisi de `/etc/navitas.env`'e yazılır. Betik gösterici sürecini **kaldırmaz** (x11: masaüstü autostart `.desktop`; drm: elle etkinleştirilen birim, gdm durur; rtsp: yedek, elle). `--kuru` gösterici bölümünde komutu ve `[VAR]/[YOK]` denetimini basar; paketteki/kurulu `rpi_inference` bayrağı tanımıyorsa (T227 yok) `[YOK]` + çıkış 3, `--kur` `HATA` ile durur (argparse çıkış 2 → `Restart` çökme döngüsü önlenir). Kurulum: `gosterici/GOSTERICI_KURULUM.md`.

## KIP=tunel — MAVLink TUNNEL, tek RFD900A (CONTRACTS §7.6 · `results/tunel_20260916/ON_KAYIT.md`)

> **NEDEN:** kullanıcı kararı (16 Eylül): tek RFD900A çifti Pixhawk **TELEM1**'de kalır, Jetson Pixhawk **TELEM2**'ye 3 telli UART ile bağlıdır, Mission Planner uçuşta kullanılabilir kalır. Pixhawk ham NAVITAS baytlarını yönlendirmez; hub NAVITAS çerçevelerini MAVLink2 `TUNNEL` (id 385) parçalarına böler. Saha adımları: `TUNEL_SAHA_RUNBOOK.md`.

1. **Kuru:** `KIP=tunel FOV=<derece> bash jetson_paket/jetson_baslat.sh --kuru`. `PIXHAWK_SERI` varsayılanı **`/dev/ttyTHS1`** (TELEM2 UART — **DOĞRULANMADI**; runbook `ls -l /dev/ttyTHS* /dev/ttyTCU*` + pin 8/10 geri döngü ile ölçer), `PIXHAWK_BAUD` **57600 olmak zorunda** (`SERIAL2_BAUD=57`). Fail-closed (çıkış 1): `PIXHAWK_SERI=/dev/ttyACM*` ya da `PIXHAWK_BAUD≠57600`.
2. **Env anahtarları:** `COGULLAYICI_EK_ARGS=--out udp:127.0.0.1:14553 --streamrate -1` ve `HUB_TASIYICI_ARGS=--tunel 127.0.0.1:14553 --tunel-kimlik hava` (udp/sik'te ilki boş, ikincisi sik'te `--port <SIK_SERI> --baud <SIK_BAUD>`). Birimlerde **tırnaksız, süslü parantezsiz** `$VAR` (systemd boşluktan böler; `${VAR}` tek argüman olurdu — test kilidi).
3. **Neden `--streamrate -1`:** TELEM2 57600 bit/s = 5760 B/s. Birimdeki `--streamrate 8` (D-406 B) MAVProxy'nin `REQUEST_DATA_STREAM(ALL, 8)` isteğiyle SR2 oranlarını ezerdi; 06 Eyl tlog'unda SR1 oranlarıyla 1943 B/s ölçüldü, 8 Hz'e ölçekli **HESAP ≈ 6858 B/s > 5760** → hat doyar. MAVProxy 1.8.74'te `-1` hiç istek göndermez (`mavproxy.py:1045`), optparse **son** değeri alır: etkin değer `-1`. Akış otoritesi **SR2** (`SR2_POSITION=8`, `EXTRA3=2`; `14.09.2026.param`) ve `iha_inis_yayinci`'nin `SET_MESSAGE_INTERVAL` istekleridir. `--kapi` (mavlink_dogrula akışları kendisi istediği için) tek başına SR2 kanıtı **değildir**; kanıt `--kapi` koşmuyorken 14550'de ayrı dinleyiciyle sayılan `GLOBAL_POSITION_INT` Hz'idir (`TUNEL_SAHA_RUNBOOK.md` §8). `rpi_inference` günlüğünde `OLCEK_YOK` olmaması yalnız yardımcı gözlemdir (ölçek araç maskesinden de gelebilir).
4. **`[DOGRULA]` listesi** (`--kuru` basar, `[VAR]/[YOK]` sayımına girmez): `SERIAL1/2_PROTOCOL=2`, `SERIAL1/2_BAUD=57`, `SERIAL1/2_OPTIONS` bit10=0 · `BRD_SER2_RTSCTS=0`, `SYSID_THISMAV=$SYSID`, `SYSID_MYGCS=255` · `SR2_POSITION ≥ 8` · `/dev/ttyTHS*` düğümü, geri döngü, seri konsol kapalı · MAVProxy sürümünde `rate != -1` koşulu · `mavfwd` açık (`set mavfwd 0` yok) · 3 tel.
5. **Paket/kurulum:** `kod/mavlink_tunel.py` → `~/navitas/comms/`, `kod/sik_rf_olc.py` → `~/navitas/scripts/` (`JETSON_KILAVUZ.md` §2). `--kur` `mavlink_tunel.py` yoksa **durur** (hub import eder; yoksa `Restart` döngüsü).
6. **Pixhawk reboot (pil değişimi):** MAVProxy'ye ve hub'a **kendiliğinden dokunulmaz** (reboot onları yeniden başlatmayı gerektirmez). SR* reboot'ta parametreden yüklenir; `iha_inis_yayinci` akış isteğini ≤10 s içinde yeniler; hub'ın tünel akranı ≤1 s içinde araç HEARTBEAT'iyle doğrulanır; reboot boyunca düşen çerçeveler `kimlik_boslugu`/`zaman_asimi_dusen` sayaçlarında görünür. Sonra `--kapi` yeniden koşulur — ⚠ `--kapi` çoğullayıcıyı **ve** hub'ı yeniden başlatır: ardından `akran DEGISTI`/`akran ogrenildi` ve yerde `kimlik_sicramasi` **beklenir**; MAVProxy parametre indirmesi (HESAP ≈ 6–7 s) yüzünden tünel gecikmesi `--kapi`'den en az 60 s sonra ölçülür (`TUNEL_SAHA_RUNBOOK.md` §5).
7. **`sik` ile farklar:** hub seri port açmaz (`--port`/`/dev/tty` **yok**, `--tunel` var); çoğullayıcıya 4. `--out` (14553) ve son `--streamrate -1` eklenir; `PIXHAWK_SERI` TELEM2 UART'tır; tüketici argümanları (`127.0.0.1:5100`) **aynı**. udp/sik `--kuru` çıktısı eskisiyle birebir aynıdır (yalnız boş `$COGULLAYICI_EK_ARGS`'ın bıraktığı satır sonu boşluğu; kamera köprüsü satırındaki boş `$KAMERA_KOPRU_ARGS` ile aynı).
8. **Açık riskler (HESAP, ölçüm değil):** TELEM1 TX ≈ SR1 1943 B/s + tünel ≈ 2,4 KB/s ≈ 5760 B/s'nin %75'i — en dar boğaz; taklitte (K4) TX tamponu 256 B varsayımında 4 parçalı çerçeveler **düştü**, 1024 B'da geçti (tampon boyu ArduPilot'ta doğrulanamadı). Hüküm **K8a/K8b** gerçek donanım ölçümündedir; ölçülene dek **ÖLÇÜLEMEDİ**.

## Birimler (`systemd/`; hepsi `Restart=always`, `RestartSec=2`, `StartLimitIntervalSec=0`, `EnvironmentFile=/etc/navitas.env`)

| birim | ne | MAVLink ucu (CONTRACTS §7.4) | kip |
|---|---|---|---|
| `navitas-cogullayici` | MAVProxy: `/dev/ttyACM0`'ın **tek sahibi**, `--out` ×3 | üretir: 14550/14551/14552 | udp+sik |
| `navitas-seri-hub` | SiK `/dev/ttyUSB0`'ın tek sahibi (sik) **ya da** MAVLink TUNNEL ucu `--tunel 127.0.0.1:14553` (tunel); `127.0.0.1:5100` → hat, hat → `--tuketici 127.0.0.1:5007` | — | **sik + tunel** |
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
