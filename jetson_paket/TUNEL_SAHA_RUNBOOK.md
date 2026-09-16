# TÜNEL SAHA RUNBOOK'U — MAVLink TUNNEL, tek RFD900A (CONTRACTS §7.6)

> **NEDEN:** kullanıcı kararı (16 Eylül 2026): tek RFD900A çifti Pixhawk **TELEM1**'de kalır,
> Jetson Pixhawk **TELEM2**'ye 3 telli UART ile bağlıdır, Mission Planner (MP) uçuşta açık kalır
> (acil LAND/RTL). NAVITAS çerçeveleri MAVLink2 `TUNNEL` ile taşınır. Ön kayıt:
> `results/tunel_20260916/ON_KAYIT.md`. **Bu belgedeki her ölçüm İNSAN görevidir; ölçülene dek
> sonuç ÖLÇÜLEMEDİ yazılır — benzetim (K4) GEÇTİ'si bunun yerine GEÇMEZ.**
>
> Komut yolları `tests/test_mavlink_tunel_sozlesme.py` ile kilitlidir (uçlar, portlar, dosyalar).

Uçlar (tek kaynak `comms/mavlink_tunel.py`):

| uç | adres | kim açar |
|---|---|---|
| hava tünel ucu | `127.0.0.1:14553` | Jetson `seri_hub --tunel` (MAVProxy `--out udp:127.0.0.1:14553` yazar) |
| yer tünel ucu | `127.0.0.1:14570` | PC `yks_gui --tunel` (MP aynası UDP Client yazar) |
| K8b yankı ucu | `127.0.0.1:5190` | Jetson `sik_rf_olc --rol yanki --tasiyici udp` (hub ek `--tuketici`) |
| hub UDP ucu | `127.0.0.1:5100` | Jetson `seri_hub --bind` (tüketiciler yazar) |

Sonuç dosyaları: `results/tunel_<YYYYMMDD>/` (PC'de; Jetson çıktıları `scp` ile aynı dizine).

---

## 1. Pixhawk parametreleri — yalnız OKU (değiştirme yok)

`Config` → `Full Parameter List` → `Refresh Params`; değerleri `results/tunel_<tarih>/K8_0.txt`'ye yaz:

- `SERIAL1_PROTOCOL=2`, `SERIAL2_PROTOCOL=2`, `SERIAL1_BAUD=57`, `SERIAL2_BAUD=57`
- `SERIAL1_OPTIONS` ve `SERIAL2_OPTIONS` bit10 = 0 (MAVLink yönlendirmesi açık)
- `BRD_SER2_RTSCTS=0` (3 tel), `BRD_SER1_RTSCTS` (kayıt; 14.09 dökümünde 2)
- `SYSID_THISMAV=1`, `SYSID_MYGCS=255`
- `SR2_POSITION ≥ 8`, `SR2_EXTRA3` (kayıt) — tünel kipinde akış otoritesi SR2'dir
- `SR1_*` değerlerinin hepsi (TELEM1 bant bütçesi için kayıt; HESAP ≈ %75 doluluk)

## 2. Jetson — UART düğümü doğrulaması (kurulumdan ÖNCE)

`/dev/ttyTHS1` varsayılanı **DOĞRULANMADI** (depodaki tek eşleme Nano bağlamındadır).

```bash
ls -l /dev/ttyTHS* /dev/ttyTCU*
# seri konsol o portta KAPALI mı:
systemctl status nvgetty 2>/dev/null | head -n 3; cat /proc/cmdline | tr ' ' '\n' | grep -i console
# pin 8/10 geri döngü (Pixhawk kablosu SÖKÜLÜ, 8 ile 10 köprülü): yazılan geri okunmalı
python3 -c "import serial,time; s=serial.Serial('/dev/ttyTHS1',57600,timeout=1); s.write(b'NAVITAS'); time.sleep(0.2); print(s.read(7))"
# kablo takılı: HEARTBEAT görülmeli (sonra Ctrl+C)
mavproxy.py --master=/dev/ttyTHS1 --baudrate 57600
```

Yanlış düğüm `[ -e ]` denetiminden geçer ama `--kapi` 3/3'te düşer — bu fail-closed'dır; yine de
bu ölçüm önce gelir. Düğüm farklıysa `PIXHAWK_SERI=<düğüm>` ile ez.

## 3. Jetson — kurulum (KIP=tunel)

```bash
cp kod/mavlink_tunel.py ~/navitas/comms/ && cp kod/sik_rf_olc.py ~/navitas/scripts/   # JETSON_KILAVUZ §2
KIP=tunel FOV=<derece> bash jetson_paket/jetson_baslat.sh --kuru       # [DOGRULA] listesini oku
sudo -E KIP=tunel FOV=<derece> bash jetson_paket/jetson_baslat.sh --kapi
ps -ef | grep [m]avproxy    # komutta '--out udp:127.0.0.1:14553 --streamrate -1' SONDA olmalı
```

Env: `KIP=tunel`, `PIXHAWK_SERI=/dev/ttyTHS1`, `PIXHAWK_BAUD=57600` (başka baud REDDEDİLİR),
`COGULLAYICI_EK_ARGS=--out udp:127.0.0.1:14553 --streamrate -1`,
`HUB_TASIYICI_ARGS=--tunel 127.0.0.1:14553 --tunel-kimlik hava`.

## 4. Windows yer kurulumu

1. RFD900A yer modülü USB → `COMx`. **COM'un tek sahibi Mission Planner'dır** (başka süreç açmaz).
2. MP 1.3.83 → `COMx` @ 57600 → **Connect**; İHA HEARTBEAT, parametreler, harita gelmeli.
3. MP aynası: Flight Data ekranında **Ctrl+F** → `Mavlink` (SerialOutput - Mavlink) → tür
   **UDP Client**, host `127.0.0.1`, port `14570`, **Write access** işaretli → Connect.
   ⚠ Menü yolu yalnız MP exe dizgelerinden çıkarıldı — **[DOGRULA]**; ekran fotoğrafı `K8_0_ayna.png`.
4. PowerShell (depo kökü):

```powershell
$PY = "<venv>\Scripts\python.exe"
& $PY -B comms\yks_gui.py --tunel 127.0.0.1:14570
```

`--ika/--iha` tünel kipinde **verilmez** (reddedilir). Ekran alt çubuğu:
`Taşıyıcı: MAVLink TUNNEL (Pixhawk TELEM1 → RFD900A)`. Günlükte `TÜNEL SAYAÇ ARTIŞI` KIRMIZI
satırları kayıp/tavan/akran değişimini gösterir.

## 5. Pixhawk reboot sonrası yordam (pil değişimi)

1. MAVProxy'ye ve hub'a **dokunma** (systemd birimleri açık kalır).
2. MP yeniden bağlanır; İHA HEARTBEAT ≤ 5 s.
3. Hub'ın tünel akranı ≤ 1 s içinde araç HEARTBEAT'iyle doğrulanır (`journalctl -u navitas-seri-hub -n 20`:
   `akran DEGISTI` yalnız MAVProxy yeniden başladıysa beklenir).
4. `iha_inis_yayinci` akış isteğini ≤ 10 s içinde yeniler; SR2 reboot'ta parametreden yüklenir.
5. `sudo -E KIP=tunel FOV=<derece> bash jetson_paket/jetson_baslat.sh --kapi` yeniden koş (3/3).
6. Reboot boyunca düşen çerçeveler hub sayaç satırında (`tunel sayac … kimlik_boslugu=`) görünür.

---

## 6. K8-0 ön kontrolleri (hepsi K8a'dan ÖNCE; sonuçlar `results/tunel_<tarih>/K8_0.txt`)

Herhangi biri düşerse **B seçeneği (MP aynası) RED** edilir ve yedek plana (§9) geçilir.

**(i) MP aynasının datagram sınırı** — `yks_gui` KAPALI; 60 s koş, sonra Ctrl+C:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol yanki --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --json --cikti results\tunel_<tarih>\K8_0_i_ayna.json
```

JSON `tunel_sayac`: `mavlink_paket / alinan_datagram ≈ 1` ve `cozum_hatasi = 0` ise sınır paket
başınadır → yer ayrıştırma kipi `datagram`'a geçişi D-kaydıyla önerilir (kod değişikliği ayrı iş).

**(ii) Yer→hava ilk sınama** — kısa K8a (§7 düzeneği) `--n 20`; hava JSON'unda
`tunel_sayac.bozuk_parca = 0` ve `tutarsiz_parca = 0`.

**(iii) 10 dk ıslatma** — üretim trafiği açık (§3 kurulu, `yks_gui` açık); başta ve sonda:
yer `yks_gui` günlüğü, hava `journalctl -u navitas-seri-hub | grep "tunel sayac" | tail -n 1`
(`gonderilen_parca`, `bozuk_parca`, `tutarsiz_parca`, `zaman_asimi_dusen`, `kimlik_boslugu`).
MP'de `Ctrl+F` → link istatistikleri: paket kaybı ve bozuk paket (MP kendi paketleriyle araya
girerse CRC hatası orada görünür).

**(iv)** `yks_gui` kapatılınca MP 60 s bağlı kalır; yeniden açılınca İHA HEARTBEAT ≤ 5 s.

**(v)** MP kapatılıp açılınca ayna ayarı kalıyor mu? Kalmıyorsa §4 adım 3 **zorunlu** işaretlenir.

---

## 7. K8a — ham tünel (ON_KAYIT K8 lafzı)

Jetson (hub durdurulur; cogullayıcı açık):

```bash
sudo systemctl stop navitas-seri-hub
python3 ~/navitas/scripts/sik_rf_olc.py --rol yanki --tasiyici tunel --tunel-bind 127.0.0.1:14553 --tunel-kimlik hava
```

PC:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 200 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8a_tunel_rtt.json
```

Bitince Jetson'da Ctrl+C, `sudo systemctl start navitas-seri-hub`.

## 8. K8b — üretim yolu (hub + üretim süreçleri açık)

Cogullayıcı açıldıktan **en az 60 s sonra** (parametre indirmesi, HESAP ≈ 6–7 s × pay). Jetson:

```bash
sudo systemctl stop navitas-seri-hub     # cogullayici, rpi_inference, iha_inis_yayinci, iha_komut_alici CALISIR kalir
python3 ~/navitas/comms/seri_hub.py --tunel 127.0.0.1:14553 --tunel-kimlik hava --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007 --tuketici 127.0.0.1:5190
# ikinci terminal:
python3 ~/navitas/scripts/sik_rf_olc.py --rol yanki --tasiyici udp --bind 127.0.0.1:5190
```

Güvenlik: prob `command('RF_PROBE','ika',…)` `iha_komut_alici`'de `hedef != node` ile ACK'siz yok
sayılır; MAVLink komutu **üretilmez**. PC:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 200 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8b_uretim_rtt.json
```

Aynı düzenekte **çok parçalı kayıt** (kapı DIŞI ama ZORUNLU; JSON `kapi_disi: true`):

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 100 --aralik 0.25 --prob-dolgu 165 --json --cikti results\tunel_<tarih>\K8_cok_parca_165.json
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 100 --aralik 0.25 --prob-dolgu 473 --json --cikti results\tunel_<tarih>\K8_cok_parca_473.json
```

K8b sırasında `journalctl -u navitas-rpi-inference` içinde `OLCEK_YOK` **olmamalı**
(`--streamrate -1` ile SR2 akışının kanıtı) ve `--kapi` 3/3. Bitince manuel hub Ctrl+C,
`sudo systemctl start navitas-seri-hub`.

**K8 GEÇTİ = K8a p95 < 0,20 s VE K8b p95 < 0,20 s** (ON_KAYIT eşiğinin sıkılaştırılması).
Ölçülmeyen her satır `ÖLÇÜLEMEDİ — neden: … · saat: … · kim: …` yazılır:

- `[ ] K8-0 (i)  [ ] (ii)  [ ] (iii)  [ ] (iv)  [ ] (v)` — ÖLÇÜLEMEDİ — neden: ……
- `[ ] K8a p95 = …… ms` — ÖLÇÜLEMEDİ — neden: ……
- `[ ] K8b p95 = …… ms` — ÖLÇÜLEMEDİ — neden: ……
- `[ ] çok parçalı 165 B p95 = …… ms · 473 B p95 = …… ms` — ÖLÇÜLEMEDİ — neden: ……

## 9. K8 DÜŞTÜ sırası (ön kayıtlı; eşik değişmez, her adım yeni ölçüm + yeni D-kaydı)

1. **Sayaç teşhisi:** `tunel_sayac` (`kimlik_boslugu`, `zaman_asimi_dusen`), MAVProxy `link`
   istatistiği (TELEM2 bayt/s), MP link istatistiği.
2. **Çerçeve boyu denetimi:** CMD/ACK'in tek parçaya sığıp sığmadığı raporlanır; protokol
   değişikliği ayrı görevdir.
3. **Kullanıcı kararları:** `SERIAL2_BAUD` yükseltme, `SR1_*` oran azaltma, RFD Air Speed.
4. **Geri dönüş:** `KIP=sik` yolu korunur (udp/sik kilitleri K6); ikinci telsiz çifti gerekir (açık soru).

**Yedek plan (MP aynası K8-0'da düşerse):** yerde MAVProxy
(`mavproxy.py --master=COMx --baudrate 57600 --source-system 255 --source-component 240 --cmd="set heartbeat 0" --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14570`),
MP `UDP 14550`'ye bağlanır. ⚠ Bu planda MP'nin araç bağlantısı MAVProxy'ye **bağımlıdır**. Yarış
PC'sine kurulum sahadan önce İNSAN görevi olarak yapılır ve bir kez ölçülür (kullanıcı kararı).
