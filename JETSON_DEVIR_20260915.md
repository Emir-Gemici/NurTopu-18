# JETSON DEVİR · 15 Eylül 2026 — PC mimarından Jetson'daki ajana

> **Kim yazdı:** PC tarafındaki mimar oturumu (Claude 1), kullanıcının isteğiyle.
> **Kime:** Jetson Orin Nano üzerinde açılacak ajan (hangi model olursa olsun).
> **Bugünün tek hedefi:** **modelin (algı + karar yazılımı) Jetson'da gerçekten çalışması**, ardından Pixhawk bağlantısı.
> **Kural:** `CLAUDE.md` anayasası bu oturum için de bağlayıcıdır. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Her iddia
> **KESİN** (doküman/çıktı), **MUHTEMEL** (çıkarım) ya da **TEST EDİLMELİ** diye ayrılır. Kullanıcının
> beyanı da sistem çıktısıyla doğrulanır. Kullanıcı Türkçe, kısa ve öz iletişim ister.

---

## 0. Başarı ne demek (katman katman — biri geçilmeden sonrakine atlanmaz)

| # | katman | geçti sayılması için |
|---|---|---|
| L1 | Ortam | `~/venv312` açılıyor, `torch.cuda.is_available()` **True** |
| L2 | Model | `model_kayit_dogrula` v36 `.pt` için **eşleşti** |
| L3 | Tezgâh çıkarımı | `rpi_inference --image` kayıtlı karelerde çöküşsüz koşuyor, **her kareye karar** üretiyor (`OPEN_ROUTE` ya da sebepli `NO_ROUTE`) |
| L4 | Güncel kod | paket depo ile senkron (`jetson_paket_hazirla.py` → "hepsi senkron"), L2–L3 **tekrar** geçti |
| L5 | Kamera | canlı kareden karar üretiliyor |
| L6 | Pixhawk | HEARTBEAT sysid 1 + telemetri; `jetson_baslat.sh --kapi` **3/3 GEÇTİ** |
| L7 | Tam zincir | birimler ayakta, birkaç dakika kopmadan, loglarda gerçek irtifa → ölçek |

**Önerilen sıra:** L1 → L2 → L3 **mevcut paketle** (hızlı kanıt) → L4 (güncelle) → L2–L3 tekrar → L5 → L6 → L7.
Gerekçe: paket 248 commit geride; önce "model bu kartta koşuyor mu" sorusunu mevcut hâliyle cevapla, sonra güncelle.
Güncelleme bir şeyi bozarsa neyin bozduğu böylece ayrılabilir.

---

## 1. Donanım

| | değer | etiket |
|---|---|---|
| Görev bilgisayarı | Jetson **Orin Nano 4 GB** modül (p3767-0004), **Seeed reComputer J401 V1.0** taşıyıcı kart (NVIDIA devkit DEĞİL) | KESİN (kart üstü yazı, 13 Eyl fotoğraf) |
| Yazılım | JetPack 7.2.1 (L4T R39.2.1), Ubuntu 24.04, Python 3.12 | KESİN (9 Eyl kaydı) |
| Güç girişi | **9–19 V**, 5.5×2.5 mm jak, 5 A max | KESİN (kart yazısı + Seeed datasheet s.3) |
| Uçuş kontrolcüsü | **Holybro Pixhawk 6C**, **ArduCopter V4.5.7** | KESİN |
| Pixhawk dolu portlar | POWER1, GPS1, TELEM1 (SiK), PPM/SBUS RC, FMU PWM OUT | KESİN (kullanıcı beyanı + fotoğraf) |
| Pixhawk boş portlar | **TELEM2**, USB | KESİN |
| WiFi | RTL8822CE M.2 E-key takıldı, **anten YOK** → ağ için Ethernet | KESİN |
| Kamera | Raspberry Pi HQ (IMX477, CSI) — **bugün takılı mı bilinmiyor** | TEST EDİLMELİ |

### 1.1 Jetson ↔ Pixhawk kablosu (TELEM2 → 40-pin UART)

**Seeed J401 datasheet (s.15, s.17) — KESİN:**
- 40-pin **J10**: pin 1 = 3.3V · **pin 2, 4 = 5V** · **pin 6 = GND** · **pin 8 = UART1_TXD** · **pin 10 = UART1_RXD**.
- Tek sıra **J15** ("Button Header"): pin 3/4 = **UART2 (DEBUG)**; ayrıca reset (7–8), recovery (9–10), auto-power (5–6). **Pixhawk buraya BAĞLANMAZ.**
- Kart alt yüzü baskısı: tek numaralı pinler kart kenarı sırasında, çift numaralılar iç sırada.

**Pixhawk 6C TELEM2** (Holybro dokümanı — KESİN): JST-GH 6 pin, 3.3 V mantık: 1 VCC 5V · 2 TX · 3 RX · 4 CTS · 5 RTS · 6 GND.
ArduPilot: **SERIAL2 = TELEM2**.

**Yapılan kablo** (kullanıcı, 15 Eyl): JST telleri kırmızı solda sıralandı, 3 ayrı dişi jumper'a eklendi:

| JST (Pixhawk) | jumper | Jetson J10 pini |
|---|---|---|
| pin 6 GND | **mor** | **pin 6** GND |
| pin 3 RX | **mavi** | **pin 8** TXD |
| pin 2 TX | **yeşil** | **pin 10** RXD |
| pin 1 kırmızı (5V), 4, 5 | — | **bağlanmaz, izole** |

⚠ Renk ↔ pin eşlemesi **MUHTEMEL** (ek yerleri görülmedi). **Güç vermeden önce bip testi** yapılmış olmalı:
JST pin 6 → mor, pin 3 → mavi, pin 2 → yeşil; kırmızı hiçbir jumper'a bip vermez. Mavi/yeşil ters = zarar yok, iletişim yok.

Jetson'da yerleri: üst yüz, pin 1–2 ucundan (USB-C tarafı) **iç sıra**: 1. pin 2 (5V, boş) · 2. pin 4 (5V, boş) ·
3. **pin 6 mor** · 4. **pin 8 mavi** · 5. **pin 10 yeşil**.

**Pixhawk tarafı ayar** — 6 Eylül parametre dökümü (`config/pixhawk/arducopter_fda_20260906.param`):
`SERIAL2_PROTOCOL,2` (MAVLink2) · `SERIAL2_BAUD,57` (57600) · `BRD_SER2_RTSCTS,0` (3 telliye uygun). **KESİN o gün için;
sonrası TEST EDİLMELİ** → bağlanınca salt okuma: MAVProxy'de `param show SERIAL2*`. **Parametre değiştirme.**

**Linux cihazı:** 40-pin UART1 → `/dev/ttyTHS1` (Seeed/NVIDIA forum) — **TEST EDİLMELİ**. Seri konsol Orin'de
büyük ihtimalle `ttyTCU0`'da (J15 debug) → `nvgetty` kapatma adımı **gerekmeyebilir**; yalnız HEARTBEAT gelmezse bak.

**Yedek yol:** Pixhawk USB-C ↔ Jetson USB-A → `/dev/ttyACM0` (betiğin varsayılanı).

---

## 2. Jetson'ın bilinen son hâli — 9 Eylül 2026 (`JETSON_OTURUM_DURUMU_20260909.md`)

⚠ 9 Eylül'den sonra Jetson'da ne yapıldığı **depoda kayıtlı değil** (15 Eyl kontrolü: uzak depodaki son 7 commit
yalnız Gazebo). Aşağıdakiler **o günün** gerçeği; bugün L1–L2'de yeniden doğrula.

| | 9 Eylül |
|---|---|
| Kullanıcı | `n4vitas` (dialout + video grupları) |
| Paket kökü | `~/proje/NAVITAS_JETSON_20260906/navitas` (`~/navitas` symlink) — **git deposu DEĞİL** |
| Depo klonu | `~/proje/github/navitas_github` — blob'suz sparse klon, `181c310` |
| Python | `~/venv312` (`--system-site-packages`): torch 2.11.0+cu130, ultralytics 8.4.142, tensorrt 10.16.2, pymavlink 2.4.49 |
| MAVProxy | `~/.local/bin/mavproxy.py` → venv |
| Engine | `jetson_paket/models/navitas_seg_v36_best_512_fp16.engine` — **üretimde KULLANILMAZ** (D-303 karar denkliği 3/126 DÜŞTÜ → uçuş **`.pt` GPU**) |
| Güç kipi | `nvpmodel` 10W (FPS ölçümünde `-m 0` + `jetson_clocks`) |
| Geçen kapılar | genel kapı 15/15 · 15/15 · defter v36 `.pt` eşleşti · FPS pt p50/p95 1,35/1,06 (eşik 0,61) · 10 dk sürekli |
| **Hiç koşmayanlar** | **kamera** (IMX477 takılı değildi) · **Pixhawk** (bağlı değildi) · `--kapi` · systemd kipleri (`--kur`/`--dogrudan`) · `rpi_inference --camera` |

---

## 3. Depo gerçekleri (15 Eyl, PC'de ölçüldü)

- **Uzak depo:** `https://github.com/navitas26/navitas.git`. Jetson klonunun uzak adresi 9 Eyl'de `yazilim-takimi/navitas` diye
  yazılmış → `git remote -v` ile **TEST EDİLMELİ**.
- **Paket geride:** `181c310..HEAD` = **248 commit**. Jetson'ı ilgilendiren **32 dosya** değişti, özellikle:
  `jetson_paket/jetson_baslat.sh` (+95) · `jetson_paket/kod/kamera_koprusu.py` (+224) · `jetson_paket/kod/karar_sozlesmesi.py` (+263) ·
  `jetson_paket/kod/isaretli_gosterici.py` (yeni, 1378) · `mavlink_dogrula.py` · `protocol.py` · `iha_sender.py` ·
  `costmap_path_finder.py` · `config/model_registry.json` · `jetson_paket/gosterici/` (yeni).
- **Etkin model DEĞİŞMEDİ — KESİN:** `config/model_registry.json` → `default_profile = competition` →
  `models/navitas_seg_v36_best.pt`, imgsz **512**, sha `1d1caca6f6da19ea…`. Ağırlığı yeniden indirmek / engine derlemek **gerekmez**.
  Registry'deki değişiklik: `kabul_kumesi*` yolları `O:/…` → `data/kabul/…` (depo köküne göre) + `competition_v32` profili eklendi.
- **Paket aynası:** `scripts/jetson_paket_hazirla.py` → kanonik `codes/comms/scripts`'ten `jetson_paket/`'i yeniler, "hepsi senkron" basar
  (`SAHA_RUNBOOK.md:21`). Paket → `~/navitas` aktarımı 9 Eyl'de paket dizinindeki `GERI_AKTARIM.md` yordamıyla yapıldı.
- **Birim şablonu** `jetson_paket/systemd/navitas-rpi-inference.service` `/home/navitas/navitas` ve `/usr/bin/python3` yazar;
  **bu kusur değil**: `jetson_baslat.sh:111-114, 274` kurulumda `NAVITAS_KOK` / `PYTHON3` ile değiştirir — KESİN (kod).
  Bu kartta **`PYTHON3=/home/n4vitas/venv312/bin/python` verilmeli** (`JETSON_BASLAT.md:7`); sistem python3'te torch yok.
- **Tek-yazar kilidi (CONTRACTS §7.4, D-403) — KESİN:** seri Pixhawk'ı **yalnız çoğullayıcı** açar
  (`navitas-cogullayici`: `mavproxy.py --master=${PIXHAWK_SERI} --baudrate ${PIXHAWK_BAUD} --streamrate 8 --out udp:127.0.0.1:14550/14551/14552`).
  `rpi_inference --mavlink` **UDP ucu** alır; `/dev/tty*` verilirse argparse çıkış 2 ile reddeder (`--seri-pixhawk-bilerek` hariç — kullanma).

---

## 4. Yol haritası — her adım: komut · amaç · beklenen · dal

> Bir anda çok komut koşma. Çıktıyı oku, hata/uyarı/izin/port/sürücü satırlarına bak, sonra ilerle.
> Sonuç ve logları `~/navitas/results/jetson_log_20260915/` altına yaz.

### L1 — Ortam (salt okuma)
```bash
whoami; ls -la ~/navitas ~/venv312/bin/python; nvpmodel -q 2>/dev/null | tail -1
~/venv312/bin/python -c "import torch, ultralytics, cv2; print(torch.__version__, torch.cuda.is_available(), ultralytics.__version__, cv2.__version__)"
```
Beklenen: `n4vitas`, dosyalar var, `True`. **Dal:** `False` → CUDA/torch katmanı; **`pip install torch` YASAK** (JetPack'e özel teker).

### L2 — Model kayıt defteri
```bash
cd ~/navitas && ls -la models/navitas_seg_v36_best.pt config/model_registry.json
~/venv312/bin/python -c "import sys; sys.path.insert(0,'codes'); from rpi_inference import model_kayit_dogrula as m; print(m('models/navitas_seg_v36_best.pt'))"
```
Kalıp `jetson_paket/JETSON_NANO_KURULUM.md:428-429`'dan; bu karttaki yol **TEST EDİLMELİ** (`codes/` yerine `kod/` olabilir — `ls` ile bak).
Beklenen: `(True, …eslesti…)`. **Dal:** `kayit_defteri_yok` → `config/` eksik; sha uyuşmazlığı → yanlış ağırlık. **`--kayit-dogrulamasiz` KULLANMA** (fail-closed korumasını kapatır).

### L3 — Tezgâh çıkarımı (kamera ve Pixhawk YOK)
```bash
cd ~/navitas && ~/venv312/bin/python codes/rpi_inference.py --help | head -40
~/venv312/bin/python codes/rpi_inference.py --image test_goruntuleri/sentetik_arena
```
- `--image` klasör kabul eder (`codes/rpi_inference.py:2518`). `--ekransiz` bu kipte **etkisiz** (`:2539` yorumu) → masaüstü oturumunda koş.
- `--mpp` verilmezse ölçek yok → sebepli `NO_ROUTE` (`OLCEK_YOK`) **beklenen**; bu yine de modelin yüklendiğini ve karar yolunun koştuğunu kanıtlar.
- Rota görmek için `--mpp` **o kümenin bilinen ölçeğiyle** verilir — değeri **uydurma**, küme manifestinden bul.
- `test_goruntuleri/` **depoda YOK** (15 Eyl PC'de ölçüldü); 9 Eyl kaydına göre **Jetson paketinde** var → `ls` ile doğrula.
  Yoksa: `data/raw_frames` (FPS ölçümünün girdisi) ya da `drone_kareleri`.

Hızlı GPU sağlık kontrolü (9 Eyl'de ölçülen betik): `scripts/jetson_fps.py --help` → `JETSON_KILAVUZ.md` §T17 komutu.

### L4 — Güncelle (L3 geçtikten sonra)
```bash
cd ~/proje/github/navitas_github && git remote -v && git status -sb && git pull --ff-only
~/venv312/bin/python scripts/jetson_paket_hazirla.py     # beklenen: "hepsi senkron"
```
Sonra paket → `~/navitas` aktarımı: 9 Eyl yordamı (paket dizininde `GERI_AKTARIM.md`). ⚠ **Engine'e, venv'e, `results/`'a dokunma; hiçbir dosya silinmez.**
Aktarımdan sonra **L2 + L3 tekrar** ve genel kapı: `~/venv312/bin/python codes/test_rota_sentetik.py` → **15/15**.
Blob'suz klonda `git pull` blob indirir → **internet gerekir** (Ethernet).

### L5 — Kamera
- IMX477 takılıysa: `sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → reboot → `ls /dev/video0` →
  `gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! fakesink` (`jetson_paket/JETSON_ORIN_NANO_KURULUM.md:159-160`).
- Köprü sistem python'uyla koşar (`KAMERA_PYTHON=/usr/bin/python3`, GStreamer'lı cv2): `kamera_koprusu.py` → `http://127.0.0.1:8080/video`.
- Algı: `rpi_inference --camera --kaynak http://127.0.0.1:8080/video` (`--kaynak` indeks, `/dev/videoN`, dosya ya da URL alır).
- Takılı kamera yoksa **USB web kamerası** (`--kaynak 0`) L5'in yazılım yolunu sınar — ama bu **IMX477 ölçümü sayılmaz**.

### L6 — Pixhawk (**pervaneler çıkık**; ilk bağlantı pilsiz yapılabilir)
```bash
ls -l /dev/ttyTHS* /dev/ttyACM* 2>&1; systemctl is-active navitas-cogullayici ModemManager 2>&1
mavproxy.py --master=/dev/ttyTHS1 --baudrate 57600
```
Beklenen: HEARTBEAT, `Detected vehicle`, mod satırı. MAVProxy içinde **salt okuma**: `param show SERIAL2*`. Çık: `Ctrl+C`.
**Dal:** port yok → kablo/UART katmanı · izin reddi → `groups` · veri yok → TX/RX ters (mavi↔yeşil) → baud → `systemctl status nvgetty` · çoğullayıcı aynı portu tutuyorsa önce durdur.
⚠ **TELEM2 kablo bağlıyken pil TAKILACAKSA:** TELEM2 pin 1 (5V) izole olduğu için Jetson'a 5V gitmez; ortak referans yalnız GND.

### L7 — Tam zincir
```bash
cd ~/navitas && KIP=udp YKS_IP=<beyan> IKA_IP=<beyan> FOV=<beyan> PIXHAWK_SERI=/dev/ttyTHS1 \
  PYTHON3=/home/n4vitas/venv312/bin/python bash jetson_paket/jetson_baslat.sh --kuru
```
Beklenen: `[YOK]`/`[EKSIK]` yok. Sonra **aynı değişkenlerle** `--kapi` → **3/3 GEÇTİ** (fail-closed: 3/3 değilse tüketiciler kalkmaz).
`FOV`/`ODAK`, `YKS_IP`, `IKA_IP` **kullanıcıdan beyan alınır, tahmin edilmez** (`jetson_baslat.sh:360-368`).
Her Pixhawk reboot'undan (pil değişimi) sonra `--kapi` tekrar (`EXTENDED_SYS_STATE` isteği reboot'ta silinir — `config/pixhawk/README.md` §5.1).

---

## 5. Yasaklar

- **`sudo apt upgrade` / `dist-upgrade` YASAK** (JetPack, kernel, TensorRT kurulumu bozulur). `pip install torch` YASAK.
- Engine yeniden derlenmez (model v36 değişmedi). Uçuş `.pt` ile.
- **Pixhawk parametresi değiştirilmez.** Gerekirse: neden → mevcut değeri oku → eski değeri kaydet → sonra değiştir. TELEM1, RC, GPS, motor eşlemesine dokunma.
- Kullanıcının dosyası silinmez. REVIEW_LOG'a yalnız **eklenir**.
- Kod çekirdeğine değişiklik gerekiyorsa önce kullanıcıya/mimara sor (anayasa madde 7, 19: yazan onaylamaz).
- **Commit:** kullanıcı izni olmadan atılmaz; **yazar kimliğini kullanıcıya sor, tahmin etme**.
  **Hiçbir AI atfı yok** (`Co-Authored-By`, "Generated with", `Claude-Session`… hepsi yasak) — kullanıcının GitHub hesabı bu yüzden spam işareti yedi.

---

## 6. Kullanıcıdan alınacak beyanlar

1. Kamera bugün takılı mı, hangisi (IMX477 CSI / USB)?
2. Pixhawk yolu: **TELEM2 jumper** mı, USB mi? Bip testi yapıldı mı?
3. `FOV` (ya da `ODAK`), `YKS_IP`, `IKA_IP`, `KIP` (udp | sik).
4. Commit gerekirse git yazar kimliği.

## 7. PC tarafında 13–15 Eylül'de olanlar (bağlam)

- FDR'de bayat kod atfı düzeltildi: `rpi_inference.py:2539,2684` → `:2562,2707` (`FDR/BOLUM_3`, `FDR/ACIK_KALEMLER.md`,
  `tests/test_fdr_t244_ic_celiski.py`); FDR kapıları **77/77 OK**. PC'de **commit edilmedi**.
- PC'de genel kapı 13 Eyl **15/15 · 15/15**. PC tam süiti kırmızı (2877 test, F43/E21) → **ortam**: pyserial/trimesh/mujoco yok, ağırlık/veri `O:\`'da.
  Bu makine kanonik ortam değil (REVIEW_LOG'da kayıtlı); Jetson'ın süit sonucu ayrıca değerlendirilir.
- Sunum üreteci + nöbetçi test yazıldı (`scripts/sunum_uret.py`, `tests/test_sunum_kanit.py`, `results/sunum_20260913/`) — commit edilmedi.
- Kampüs portal oto-giriş script'i **bırakıldı** (kullanıcı kararı).
- J15 debug UART bulgusu ve kablo eşlemesi yukarıda (§1.1).

## 9. 🔴 CANLI DURUM — SSH ile ölçüldü (15 Eylül 2026, 17:06–17:20, PC → `n4vitas@10.21.8.7`)

> Jetson'daki ajan çalışmadığı için adımları mimar SSH üzerinden koştu. Aşağıdaki ölçümler **bu dosyanın §0, §2 ve §3'ündeki
> üç iddiayı YANLIŞLADI** — o bölümler PC deposuna ve 9 Eylül kaydına bakılarak yazılmıştı. Önceki metin silinmedi; doğrusu burada.

### 9.1 Yanlış çıkan iddialar
- ~~"9 Eylül'den sonra Jetson'da ne yapıldığı depoda kayıtlı değil"~~ → **YANLIŞ.** Jetson klonu `jetson/tek-yol-20260912` dalında
  (`abea98cb`, 13 Eyl), uzak `yazilim-takimi/navitas` (PC'ninki `navitas26/navitas` — **iki ayrı uzak**). Dalda 13 Eyl kayıtları var:
  `JETSON_KAMERA_PIXHAWK_20260913.md`, `results/jetson_20260913/`, REVIEW_LOG D-480…D-484. ⚠ Bu dalın D-484'ü PC'deki D-484 ile **aynı numara, farklı kayıt**.
- ~~"Paket 248 commit geride"~~ → **YANLIŞ.** O sayı 9 Eyl commit'ine (`181c310`) göreydi. Bugün paket (`~/navitas`) ile klon
  7 anahtar dosyada **bayt-eş**; PC master ile de 5'inde eş. Farklı olan yalnız `codes/rpi_inference.py` (Jetson'da **T233 yok** —
  ekransız kipte FPS ortalama/p95 raporu; **karar yolunu değiştirmez**, PC `df973d89`) ve `config/model_registry.json` (etkin `competition` sha'sı iki yanda aynı).
- ~~"Pixhawk hiç bağlanmadı / MAVLink kapısı koşulmadı"~~ → **YANLIŞ (kısmen).** 13 Eyl: Pixhawk **USB** (`/dev/serial/by-id/usb-Holybro_Pixhawk6C_…-if00`)
  `mavlink_dogrula` **180 s GEÇTİ**; geçici MAVProxy çoğullayıcıyla **üç UDP uçta aynı anda** 1/8/2 Hz, **GEÇTİ**. Koşulmayan: systemd `--kur`/`--kapi` ve gerçek üretim tüketicileri.

### 9.2 Bugün ölçülen katmanlar

| katman | sonuç | kanıt (komut → çıktı) |
|---|---|---|
| L1 ortam | **GEÇTİ** | `torch 2.11.0+cu130 cuda True` · ultralytics 8.4.142 · cv2 4.11.0 · disk 154 G boş · `n4vitas` dialout/video/i2c · güç kipi **10W** |
| L1b GPU çekirdekleri | **GEÇTİ** | torch "CC 8.7 desteklenmiyor" **uyarısı** veriyor ama `conv2d` (19,10 ms/iter), `matmul`, fp16 autocast `cuda:0`'da **çalıştı** → uyarı işlevsel değil |
| L2 model | **GEÇTİ** | `model_kayit_dogrula('models/navitas_seg_v36_best.pt')` → `True`, `durum: eslesti`, sha `1d1caca6…6911`, imgsz 512 |
| L3 tezgâh çıkarımı | **GEÇTİ (ölçeksiz kip)** | `codes/rpi_inference.py --image` 5 gerçek kare (`data/raw_frames/whatsapp_video_…`) → çıkış 0, 20 s; 5/5 karara **sebepli** `NO_ROUTE` (4× `OLCEK_YOK`, 1× `GORUS_HATTI_KOPUK`) — `--mpp` verilmedi, beklenen. Rotalı karar yolu Jetson'da 13 Eyl'de 260 kabul karesinde ölçülmüştü (D-482: engine ≡ pt, F1 0 · D-303 0/260 · F2 0,99526) |
| L4 güncelleme | **GEREKMİYOR (bugün)** | paket 13 Eyl dalıyla eş; tek eksik T233 raporlama |
| L5 kamera | 🔴 **DÜŞTÜ — fiziksel** | §9.3 |
| L6 Pixhawk | **ÖLÇÜLEMEDİ (bugün)** | `/dev/ttyACM*` yok (USB takılı değil); `/dev/ttyTHS1` var (`root:dialout`), `nvgetty` **inactive**. ⚠ `ModemManager` **active** — USB bağlanınca porta dokunabilir, izlenmeli |
| L7 tam zincir | **ÖLÇÜLEMEDİ** | `navitas-*` systemd birimi **kurulu değil**; çalışan süreç yok |

Tezgâh çıktı görselleri pakete (`codes/results/`) yazılmıştı; paket kirlenmesin diye **`/tmp/navitas_l3_20260915/cikti/`'ye taşındı** (log: `/tmp/navitas_l3_20260915/kosum.log`).

### 9.3 Kamera — kesin teşhis
- Modül: **Arducam UC-350 Rev.D = IMX219** (13 Eyl fotoğrafı; önceki IMX477 beyanı geçersiz). 160° lens bilgisi bu modüle aktarılmaz.
- Etkin boot (`/boot/extlinux/extlinux.conf`, `DEFAULT JetsonIO`): `OVERLAYS …camera-p3768-imx219-dual.dtbo` → **iki port birlikte** yoklanıyor.
- Çekirdek (bu boot): `imx219 9-0010 … i2c read probe (-121)` **ve** `imx219 10-0010 … (-121)` → **iki portta da sensör I2C'ye cevap vermiyor**; `/dev/video*` yok.
- **Sonuç:** dual overlay port seçimini devre dışı bıraktığı için sorun **port/overlay değil**; **fiziksel bağlantı** (şerit kablonun yönü, kilidi, teması, kablonun kendisi) ya da modül. -121 = I2C ACK yok.
- J401 datasheet (s.13–14, KESİN): **J12 = CSI0 / CAM0** (I2C mux 1. çıkış) · **J9 = CSI2 / CAM1** (mux 2. çıkış) · ikisi **2-lane 15 pin** (RPi tipi 15 pin şerit uyar).
  ⚠ 13 Eyl notu kart baskısında "J9/CAM0, J12/CAM1" okumuştu — datasheet'in tersi; dual overlay'de fark etmez, ama tek porta dönülürse **datasheet** esas alınır ve fotoğrafla teyit edilir.
- Alternatif kaynak: USB kamera **yok** (`lsusb`'de UVC arayüzü yok).

### 9.3b Kamera — kullanıcı taktıktan sonra (17:16–17:20) · L5 kısmen GEÇTİ
- Kullanıcı kamerayı Jetson **açıkken** taktı (CSI sıcak takma desteklemez — bir dahaki sefere kapalıyken). Açılış yoklaması yenilenmediği için
  sürücü `bind` ile yeniden yoklatıldı (`echo 9-0010 > /sys/bus/i2c/drivers/imx219/bind`, sudo): **`9-0010` bağlandı**, `/dev/video0` = `vi-output, imx219 9-0010`.
  `10-0010` hâlâ `-121` (o portta kamera yok). Çekirdek uyarısı: `tegra-nvcsi … Failed to create device link (0x180) with 9-0010` — kare alımını engellemedi.
- **Port adı:** kullanıcı kartın **"CAM0"** baskılı konnektörüne taktı; Linux `i2c-9` = `cam_i2cmux/i2c@1` (mux 2. çıkış) görüyor. Datasheet bu konnektöre **J9 / CAM1** diyor
  → kart baskısı ile datasheet adlandırması **ters** (13 Eyl notuyla uyumlu). `imx219-dual` overlay iki portu da yokladığı için **değişiklik gerekmiyor**.
  ⚠ Tek porta (A) indirilirse bu kamera **görülmez**. Yeniden başlatmada açılış yoklamasının kendiliğinden geçtiği **TEST EDİLMELİ**.
- `nvargus-daemon` yeniden başlatıldı (sudo) → `gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=10 … 1920x1080@30 … jpegenc` → **10 kare**
  (`/tmp/navitas_kamera_20260915/`). Kare **gözle doğrulandı**: gerçek sahne (tavan lambası + lens parlaması). Argus günlüğündeki `ImagerGUID 1 … Sensor could not be opened` boş CAM0 içindir.
- Köprü `scripts/kamera_koprusu.py --kaynak nvargus --port 8080`: `kaynak_acik true`, 50 kare, **~10 fps**, 1280×720, düşen 0, çökme yok; `/kare.jpg` HTTP 200 ve **gözle doğrulandı**.
  INT ile 5 s'de kapanmadı, TERM ile kapandı (çökme kaydı yok).
- 🔴 **Renk:** iki karede de **belirgin pembe/mor ton**. MUHTEMEL sebep: lenste IR-cut filtresi yok (NoIR) ya da ISP ayarı (`/var/nvidia/nvcam/settings/imx219.nito` genel dosya). Model normal RGB ile eğitildi → **uçuştan önce çözülmeli**; lens tipi kullanıcıdan TEST EDİLMELİ.
- `rpi_inference --camera` **çıkış 2**: `--camera icin --mavlink zorunludur` (ayrıca `--mav-sysid` ve `--fov`/`--odak` zorunlu, `codes/rpi_inference.py:2699-2717`). Canlı model testi MAVLink olmadan başlamaz — **tasarım gereği**.

### 9.3c Bugünkü tezgâh topolojisi (Pixhawk Jetson'a değil PC'ye bağlı)
- Kullanıcı durumu: Pixhawk **USB → PC** (`/dev/ttyACM0` = if00 MAVLink, `ttyACM1` = if02); Jetson **SSH → PC**; Pixhawk ↔ Jetson kablosu drone üstünde uzanmıyor.
- Karar: **Pixhawk MAVLink'i PC'den ağ ile Jetson'a taşınır**, Jetson tarafı üretim düzeniyle aynı kalır:
  `PC: socat /dev/ttyACM0 ⇄ UDP 10.21.8.7:14555` → `Jetson: mavproxy.py --master=udpin:0.0.0.0:14555 --out udp:127.0.0.1:14550/14551/14552` → tüketiciler değişmez.
  `rpi_inference` `udpin:`/`udp:` adresini kabul eder (`comms/inis_kaniti.py:107-120`). Bu **yalnız tezgâh** düzenidir; uçuşta Jetson–Pixhawk fiziksel hattı gerekir.
- PC hazırlığı (ölçüldü): `socat 1.8.1.1` var · `pyserial 3.5` depo `.venv`'ine kuruldu · MAVProxy PC'ye pip ile **kurulamadı** (300 s zaman aşımı, Py3.14) — gerek yok ·
  firewalld FedoraWorkstation bölgesi **1025–65535 UDP/TCP açık** · YKS `comms/yks_gui.py --help` Linux'ta **açıldı** (tkinter var).
- 🔴 PC engelleri (insan, sudo): `trs` **dialout grubunda değil** → `/dev/ttyACM0` `Permission denied` · PC'de `ModemManager` active (Pixhawk portunu yoklayabilir).
- Jetson: MAVProxy 1.8.74 var · 1455x/500x UDP portları boş · ufw inactive.
- Yer testinde irtifa ~0 m → canlı kararlar **sebepli NO_ROUTE** olacak (ölçek/asgari irtifa). Bu **doğru** davranıştır; zinciri kanıtlar, rota doğruluğunu kanıtlamaz.
- **18:05 — L6 (tezgâh düzeni) GEÇTİ.** Kullanıcı `sudo setfacl -m u:trs:rw /dev/ttyACM0 /dev/ttyACM1` koştu (geçici; USB çıkınca sıfırlanır).
  Köprü betiği `tezgah_mavlink_koprusu.sh baslat` (PC scratchpad): PC `socat OPEN:/dev/serial/by-id/usb-Holybro_Pixhawk6C_…-if00,rawer UDP-DATAGRAM:10.21.8.7:14555,bind=:14556`
  + Jetson `mavproxy.py --master=udpin:0.0.0.0:14555 --streamrate 8 --out udp:127.0.0.1:14550/14551/14552 --daemon` → `dogrula`: üç uçta **aynı anda**
  `mavlink_dogrula.py --mavlink udpin:127.0.0.1:<port> --sysid 1 --sure 10` → her uçta HEARTBEAT 10 (1,00 Hz ≥ 0,50) · GLOBAL_POSITION_INT 80 (8,00 ≥ 4,00) ·
  EXTENDED_SYS_STATE 20 (2,00 ≥ 1,00) · **VERDIKT GECTI, çıkış 0 · SONUÇ 3/3** (log `/tmp/navitas_tezgah_kapi/`). Süreçler **açık bırakıldı** (canlı model adımı için);
  durdurma: `tezgah_mavlink_koprusu.sh durdur`. Kapsam: üretim `--kapi` (systemd) değil, aynı uçlarla elle koşum.
- **18:08 — kamera köprüsü ağa açık:** Jetson `scripts/kamera_koprusu.py --kaynak nvargus --host 0.0.0.0 --port 8080` (log `/tmp/navitas_kopru_canli.log`);
  PC'den `curl http://10.21.8.7:8080/durum` → `kaynak_acik true`, 10 fps, düşen 0; `/kare.jpg` HTTP 200. Süreç **açık**.
- **18:09 — YKS bu PC'de AÇIK (L7'nin YKS yarısı):** `comms/yks_gui.py --bind 0.0.0.0:5005 --ika 127.0.0.1:5006 --iha 10.21.8.7:5007 --kamera-url http://10.21.8.7:8080 --gorunum kamera`.
  İlk iki deneme **fail-closed** reddetti: `UDP kipinde --ika HOST:PORT zorunlu`, sonra `--iha HOST:PORT zorunlu: ARM/DISARM/RTL/LAND efemer heartbeat portuna gönderilemez`.
  **Tezgâh ayarı (bilinçli):** İKA yok → `--ika 127.0.0.1:5006` (dinleyen yok, düşer). `--iha 10.21.8.7:5007` → Jetson'da 5007'yi **dinleyen süreç YOK** (`ss -ulpn` boş; `iha_komut_alici` **bilerek başlatılmadı**) → YKS'nin ARM/RTL/LAND/PARAŞÜT komutları Pixhawk'a **ulaşamaz**.
  YKS 5005'i dinliyor; `--otokaydet` ekran görüntüsü (1240×940) **gözle doğrulandı**: RAW Kamera panelinde Jetson görüntüsü canlı (`kare yaşı 0.10 sn`), İHA/İKA "sinyal yok", açık yol "BEKLENİYOR" — model henüz koşmadığı için **beklenen**.
- **~18:20 — kullanıcı isteğiyle tüm tezgâh süreçleri DURDURULDU:** PC `socat` + Jetson MAVProxy (`tezgah_mavlink_koprusu.sh durdur`), PC YKS, Jetson kamera köprüsü (INT'e 5 s'de kapanmadı, TERM ile kapandı).
  Jetson'da navitas/kamera/mavproxy süreci yok, 1455x ve 8080 serbest, `/var/crash`'te yeni kayıt yok. PC'deki `setfacl` izni USB çıkınca kendiliğinden kalkar.
- 🔴 **Lens karışıklığı (kullanıcı beyanı, 18:15):** IMX219 modülde şu an **Raspberry Pi HQ kameranın 6 mm lensi** takılı; kullanıcı lensleri değiştiriyor.
  Satın alma listesindeki kamera **Arducam IMX477 12,3 MP 160°**; Jetson'a takılı sensör **IMX219** (I2C `0x10`, `imx219` sürücüsüyle kare alındı — KESİN).
  **Hiçbir katalog FOV'u kullanılmaz.** Lens takıldıktan sonra FOV **duvar testiyle ölçülecek**: kamera duvara dik, lens–duvar D, köprünün 1280×720 karesinde görünen yatay genişlik W → `FOV_yatay = 2·atan(W/(2·D))`.
  (Hesap, ölçüm DEĞİL: 6 mm lens IMX219'da ~34°, IMX477'de ~55° yatay olurdu — sensör genişlikleri 3,68 / 6,287 mm; Jetson kip kırpması ayrıca değiştirir.)
- **18:25 — orijinal lens geri takıldı** (kullanıcı: "Jetson için aldığımız kameranın geldiği lens", HQ lens değil). Jetson yeniden başlamadı (uptime 1 sa 40 dk), `imx219 9-0010` bağlı.
  `gst-launch-1.0 nvarguscamerasrc … 1280x720 … num-buffers=30` → kare alındı, **gözle bakıldı**: odak dışı, yalnız tavan lambası → **FOV ve bükülme bu kareden okunamaz** (iddia edilmedi).
  **Mor ton bu lensle de var → tonun sebebi HQ lens DEĞİL**; modül tarafı (IR-cut yok / ISP) — TEST EDİLMELİ.
  Argus IMX219 kipleri (ölçüldü): 3280×2464@21 · 3280×1848@28 · 1920×1080@30 · 1640×1232@30 · **1280×720@60** (köprü bu kipi kullanır; tam sensörden kırpılmış olabilir → katalog FOV'u bu kipe birebir uymayabilir).
  Odak ve ölçüm için kamera köprüsü `--host 0.0.0.0 --port 8080` yeniden açıldı.
- **18:35 — FOV ÖLÇÜLDÜ (orijinal lens, köprü kipi 1280×720):** 2,00 m'de (lens→kâğıt, kullanıcı ölçümü) 7,6 cm kare kâğıt (kullanıcı: "8 cm'ye yakın");
  köprü karesinde OpenCV `minAreaRect` → **106,1 × 101,8 px** (~4° eğik). `FOV_yatay = 2·atan((S·1280/px)/(2·D))` →
  7,6 cm: 25,82° (106,1 px) · **26,32° (ort. 104 px)** · 26,87° (101,8 px); 8,0 cm: 27,13 · 27,66 · 28,23°. **Kullanılan değer: 26,3° (aralık 25,8–28,2°).**
  Sınırlar: tek nesne, piksel kenarı ±~%3, kâğıdın tam dik olduğu varsayımı; duvar + şerit metre ile tekrar ölçümü önerilir. Kare: PC scratchpad `fov_duvar_1.jpg`.
- 🔴 **KAPSAMA SORUNU (hesap, bu FOV ile):** 30 m'de yerde **14,0 × 7,9 m** (1,10 cm/px) · 32 m'de 15,0 × 8,4 m · 40 m'de 18,7 × 10,5 m.
  20×20 m FDA alanını 30 m'den tek karede **yatayda** görmek için FOV_yatay ≥ 36,9°, **16:9 dikeyde** de sığdırmak için ≥ 61,3° gerekir.
  `config/pixhawk/README.md` §5.4'teki *"Kamera 30–32 m'de 20×20 m alanı tek karede görür"* varsayımı **bu lens + 1280×720 kipiyle TUTMUYOR.**
  Seçenekler (karar mimar/ekip, ölçümle): daha geniş lens · tam sensör kipi (1640×1232 / 3280×2464) ile FOV'u yeniden ölçmek · görev irtifasını artırmak (şartname ≥ 30 m).
- **18:51–18:58 — CANLI ZİNCİR (L7 tezgâh) GEÇTİ:** kamera → Jetson model (GPU) → YKS (PC).
  - İlk koşum (`--yks-hedef 10.21.8.112:5005`): model GPU'da çalıştı (GR3D %95–99) ama YKS hakem kaydı `iha=YOK`, HEARTBEAT yaşı `null`.
    Teşhis (ölçüldü): Jetson'da `ip neigh 10.21.8.112 INCOMPLETE`, ping %100 kayıp, bağımsız UDP testi Jetson→PC:5099 **ulaşmadı**, modelin gönderim soketinde Send-Q birikti.
    ~~İlk yorum "kablolu↔kablosuz ARP izolasyonu"~~ → **YANLIŞTI.** **Kök neden (KESİN):** PC 17:47:28'de WiFi'ya yeniden bağlandı, DHCP **yeni adres** verdi
    (`dhcp4 (wlp0s20f3): new lease, address=10.21.8.156`; NetworkManager günlüğü). Model eski `.112`'ye gönderiyordu. PC'nin başlattığı akışlar (SSH/HTTP/MAVLink) `.156` ile çalıştığı için etkilenmedi.
  - Düzeltme: UDP testi Jetson→`10.21.8.156:5099` **ulaştı** → model `--yks-hedef 10.21.8.156:5005` ile yeniden başlatıldı → ARP `REACHABLE`.
    YKS hakem kaydı (`results/prova/20260915_185110_3752497/hakem_log.jsonl`): **`TELEMETRI_KANIT iha=TAZE`, yaş 0,0 s**; `ROTA_YOK` olayları akıyor, sebep **`MASKE_YOK`**
    ("Zemin maskesi 0 piksel") — kamera ofis içine bakıyor, **sebepli ret doğru davranış**; YKS her karara güvenli duruş ACK'i gönderiyor.
    YKS uyarısı "İHA MANUEL MODA GEÇTİ … §6.4": Pixhawk masada manuel modda — tezgâhta **beklenen**.
  - Kapsam: bu **zincirin** kanıtıdır (kamera, GPU çıkarım, MAVLink tüketimi, telsiz halkası, YKS kaydı). **Rota doğruluğunu kanıtlamaz** — yerde irtifa ~0, sahne arena değil.
  - 🔴 **Ağ kararlılığı:** PC adresi DHCP ile değişebiliyor (bir kez değişti). Saha/prova için YKS'ye **sabit IP / DHCP rezervasyonu** ya da ad çözümü gerekir; yoksa model kararları sessizce boşa gider.
  - ⚠ Jetson RAM ~3,1/3,46 GB, swap ~1,15 GB dolu (model + köprü + MAVProxy) — uzun koşumda izlenmeli. OOM yok.
- **19:25 — FOV kip testi (kullanıcı "şimdi yap"): 18:35'teki 26,3° KIRPILMIŞ açıymış; lens ~4,3 mm.**
  Model + köprü durduruldu, aynı sahnede (7,6 cm kâğıt, lensten 2,00 m) `gst-launch-1.0 nvarguscamerasrc` ile üç istek:
  - `3280x2464` (framerate verilmeden) → **ARGUS_ERROR "Frame Rate specified is greater than supported"** (kip 0 en çok 21 fps); `framerate=21/1` ile alındı → **Camera mode 0**.
  - `1640x1232` → **Camera mode 3**, Output 1640×1232 (tam sensör, 2×2 birleştirme).
  - `1280x720` → **Camera mode 2, Output Stream 1920×1080** → Argus 1920×1080 **merkez kırpımını** seçip 1280×720'ye küçültüyor. **Köprünün varsayılanı bu** (`--genislik` verilmezse 1280).
  Kâğıt (OpenCV `minAreaRect`, işaretli kırpıntılar **gözle doğrulandı**, kutu kâğıdın üstünde): 1640×1232 → **73,6 px** → **FOV_yatay 45,9°** · 1280×720 → 97,8 px → 27,9°.
  **Tutarlılık:** kip 2 birebir 1920 px kırpımsa beklenen 73,6×2×1280/1920 = **98,1 px**, ölçülen **97,8 px** (%0,3) → dar açının sebebi **kırpma**, lens değil (KESİN, iki bağımsız kareden).
  Lens odak (hesap, IMX219 aktif genişlik 3,674 mm): **~4,34 mm** (kâğıt 8 cm ise 4,12 mm; FOV 48,0°).
  Mevcut lens + **tam sensör** kipinde yerde görülen alan (hesap): 30 m **25,4 × 19,1 m** (kısa kenar 20 m'nin ALTINDA) · 32 m 27,1 × 20,4 m (payı yok) · 35 m 29,6 × 22,3 m · 40 m 33,9 × 25,4 m;
  20 m kısa kenar için ≥ 31,4 m, %25 payla ≥ 39,3 m. Alternatif lens, 30 m, tam sensör: 2,8 mm 39,4×29,6 · **3,04 mm 36,3×27,2** · 3,6 mm 30,6×23,0 · 4,0 mm 27,6×20,7 m.
  **Sonuç:** (a) köprü **tam sensör kipinde** koşmalı (`--genislik 1640 --yukseklik 1232`) ve `--fov 45.9` o kipe aittir; (b) FDA'yı 30–32 m'de payla görmek için **~3 mm lens** ya da mevcut lensle **≥ ~35–40 m** irtifa. Karar ekip/mimar.
  ⚠ 26,3° değeri artık **yalnız kırpılmış 1280×720 kipi** için geçerli; tam sensör kipiyle birlikte **kullanılmaz**.
  Üçüncü kontrol (3280×2464, yarım ölçekte arama): kâğıt 134×150 px (ort 142,0; beklenen 147,2, %3,5) → 47,4°; **ama konum 1640 karedekinden ~213 px yukarıda** → kamera kıpırdamış ya da başka nesne → **kanıt sayılmadı**. Raporlanan aralık: **FOV_yatay ~46–48°, lens ~4,1–4,3 mm**.
- **19:30 — canlı zincir TAM SENSÖR kipinde yeniden başlatıldı:** köprü `--genislik 1640 --yukseklik 1232` → log **Camera mode 3**, Output 1640×1232, 9,9–10 fps, düşen 0;
  model `--fov 45.9 --yks-hedef 10.21.8.156:5005`. Kararlı durum (30 s, 19:31:47–19:32:17): YKS **111 `ROTA_YOK` = 3,70 karar/s** (kırpık 1280×720 kipinde 4,72), sebep hep `MASKE_YOK`;
  `iha=TAZE` (yaş 0,2 s); Jetson model CPU %52, RSS 1,29 GB, GR3D örnekleri %2 / %99 / %67 (kare başına dalgalı), RAM ~3,1/3,46 GB.
  Açık gözlem: `seq` 290–429 (140 numara) iken 111 karar kaydı — önceki koşumdaki ~%20 fark aynen sürüyor; HEARTBEAT ile ortak sayaç mı, kayıp mı **ayrıştırılmadı**.
- **19:37 — PEMBE TON TESTİ: içerideki magentanın ana sebebi ISP beyaz dengesi (IR değil — iç mekân için).**
  Önce eldeki karelerde beyaz kâğıt (ölçüm): R/G 1,57–1,60 · B/G 1,36; duvar R/G ~1,62–1,73 · B/G ~1,57–1,65 → **yeşil kanal belirgin düşük**.
  `/var/nvidia/nvcam/settings/camera_overrides.isp` **yok** → modüle özel ISP ayarı yok, genel `imx219.nito` kullanılıyor. `v4l2-ctl` kurulu değil (ham Bayer testi yapılamadı).
  Test: model+köprü durduruldu, `nvarguscamerasrc wbmode=N` 1640×1232 → parlak-doymamış piksellerde:
  **wbmode 0 (off) R/G 1,31 B/G 1,34 · wbmode 1 (auto) R/G 1,30 B/G 1,34 (off ile birebir → AWB fiilen çalışmıyor)** · wbmode 3 (fluorescent) R/G 1,18 B/G 0,94 · wbmode 5 (daylight) R/G 1,24 B/G 0,62 (turuncuya kayar).
  Kareler **gözle bakıldı**: 0/1 magenta, 5 sıcak/turuncu ve "D" kâğıdı neredeyse beyaz. Hazır kipler tonu bu ölçüde değiştirdiğine göre iç mekândaki magenta **yazılımla düzeltilebilir** (MUHTEMEL, güçlü kanıt).
  ⚠ Sınırlar: kullanıcı kamerayı test arasında oynattı (kâğıt bulunamadı, sahneler kip başına aynı değil); ofis LED ışığında IR azdır → **dış mekânda IR-cut olup olmadığı AYRICA TEST EDİLMELİ** (TV kumandası IR LED'i canlı görüntüde / güneşte bitki rengi).
  Canlı zincir test sonrası geri açıldı: YKS son 30 s'de 118 `ROTA_YOK`, `iha=TAZE`.
- 🔴 **Kamera kimliği çelişkisi (kullanıcı GPT kaydı, 19:35):** satın alma kaydı **Waveshare/Arducam IMX477-160** (üretici: yatay ~117,6°, dikey ~85,6°, çapraz ~154,2°).
  Jetson'a takılı sensör **IMX219** (I2C 0x10, Argus kipleri 3280×2464/…/1280×720 — IMX477'nin kipleri farklıdır) — KESİN. IMX477-160 bu hat için (hesap):
  30 m'de ~99 × 56 m (pinhole yaklaşımı; balıkgözü bükülmesi yüzünden `mpp = 2h·tan(FOV/2)/W` formülü kenarlarda **geçersiz**), model girdisi 512 px'te 3 m yol ≈ 15 px → **önerilmez** (bükülme düzeltmesi + kalibrasyon olmadan).
- **19:45 — EKİP KARARI (Emir, WhatsApp, kullanıcı iletti):** *"Bizim aldığımız imx 477. Sana bir yerlerden bulup getirdiğimiz 219. 477'yi kullan. 6mm lens tak."*
  → **Uçuş kamerası IMX477 + 6 mm lens.** Bugün ölçülen IMX219 **ödünç** modüldür; 45,9° / 26,3° FOV değerleri ve renk bulguları **IMX477'ye aktarılmaz**, değişimden sonra yeniden ölçülür.
  Hesap (ölçüm DEĞİL; IMX477 aktif alan 6,287 × 4,712 mm, nominal 6 mm, bükülme yok sayıldı): FOV yatay ~55°, dikey ~43°; 30 m'de **4:3 tam sensör** ~31,4 × 23,6 m (20×20 FDA **payla sığar**),
  16:9 kipte ~31,4 × 17,7 m (kısa kenar 20 m'nin altında → 4:3 kip ya da ≥ ~34 m). ⚠ Lens yuvası uyumu (CS / M12) **TEST EDİLMELİ** — IMX477-160 ürünleri genelde M12 balıkgözü lensle gelir.
- **19:45 — Kullanıcı onayı:** *"yazılım ile görüntünün renkleriyle oynanarak çözülmesine onay veriyorum"* → renk düzeltmesi yazılımla yapılacak. IMX477 takıldıktan sonra renk yeniden ölçülüp gerekiyorsa uygulanacak
  (köprüde `nvarguscamerasrc` beyaz dengesi kipi bugün **verilemiyor**: `scripts/kamera_koprusu.py:165-173` `nvargus_boru`; üretim kodu değişikliği — anayasa madde 7/19 gereği yazan ≠ onaylayan).
- **~19:55 — IMX477'ye geçiş hazırlığı + Jetson KAPATILDI (kullanıcı "hazır"):**
  İlk deneme (19:48) Claude Code güvenlik sınıflandırıcısı zaman aşımına uğradığı için **hiç çalışmadı** (boot değişmemişti).
  İkinci deneme: `fdtoverlay -i /boot/dtb/kernel_tegra234-p3768-0000+p3767-0004-nv.dtb … tegra234-p3767-camera-p3768-imx477-dual.dtbo` → **BAŞARILI** (test DTB'de 18 `imx477` dizgisi; dtbo p3767-0004 uyumlu);
  yedek `/boot/extlinux/extlinux.conf.before-imx477-dual-20260915`; `diff` → **yalnız satır 37**: `OVERLAYS …imx219-dual.dtbo` → `OVERLAYS …imx477-dual.dtbo`.
  Model, kamera köprüsü, Jetson MAVProxy durduruldu; `systemctl poweroff`. **Geri dönüş:** yedeği `extlinux.conf` üstüne kopyala + reboot.
  Kullanıcı: IMX219 (lensiyle) çıkarılıyor, **"Raspberry Pi" yazan HQ kamera (IMX477, CS yuva) + 6 mm lens** takılacak; fotoğraf gönderecek.
  Telefon IR testi (IMX219, kullanıcı beyanı): Android telefonun IR vericisi canlı görüntüde **ışık verdi** → çıkarılan IMX219'da IR-cut yok/zayıf (MUHTEMEL; nitel test).
  Raspberry Pi dokümanına göre HQ Camera'nın yuvasında IR-cut filtresi bulunur → yeni kamerada aynı test **tekrarlanacak**.
- **20:15 — kamera kimliği fotoğrafla (kart yazıları):** Jetson'dan çıkarılan = **Arducam UC-350 Rev.D (IMX219)** + kendi lensi (~4,3 mm ölçüldü) — ödünç.
  Takılan = **"© Raspberry Pi 2018 HQ Camera V1.0" (IMX477)** + **"6mm IR · 3MP·HD · CCTV LENS"** (CS yuva; FAR/NEAR halkası, kilit vidası). Lenslere dokunulmadı.
- **20:27 — IMX477 AÇILIŞTA TANINDI (Jetson açıldı, `imx477-dual` overlay):** `imx477 9-001a: tegracam sensor driver:imx477_v2.0.6` · `subdev imx477 9-001a bound` ·
  `/dev/video0` = `vi-output, imx477 9-001a`. `10-001a` → `-121` (o portta kamera yok, beklenen). Aynı fiziksel konnektör, `i2c-9`.
- **20:30 — IMX477 kipleri ve renk (ölçüldü):** Argus bu sürücüde **yalnız iki kip** veriyor: **kip 0 = 3840×2160 @30** · **kip 1 = 1920×1080 @60** (ikisi de 16:9).
  Sensörün doğal 4:3 kipi (4056×3040) **yok**: `4032x3040` isteği → `Camera mode 0, Output Stream 3840×2160` → çıktı 4:3'e **uzatılmış** → **kullanılmaz**.
  Renk (parlak-doymamış pikseller): 1920×1080 `wbmode=1` **R/G 0,97 B/G 0,94** · `wbmode=0` aynı · kip 0 R/G 0,96 B/G 0,94 → **nötr; IMX219'daki magenta YOK** → yazılım renk düzeltmesi büyük olasılıkla **gereksiz**.
  Hesap (ölçüm DEĞİL; 1,55 µm piksel, 3840×2160 = 5,95 × 3,35 mm, nominal 6 mm): FOV yatay ~53°, dikey ~31°; 30 m'de ~29,8 × 16,7 m → **16:9 kırpma yüzünden 20×20 FDA'nın kısa kenarı SIĞMAZ**, ≥ ~36 m gerekir. Kâğıt testiyle ölçülecek.
  MAVLink köprüsü Jetson açılışından sonra yeniden başlatıldı → **3/3 GEÇTİ**.
- **20:35 — IMX477 odak + IR (kullanıcı beyanı):** köprü 1920×1080 (kip 1) `0.0.0.0:8080` açık; ilk kare **tamamen bulanıktı** (gözle) → kullanıcı lens odağını ayarladı, *"görüntü daha iyi"*.
  Telefon IR vericisi yoktu; **TV kumandası** canlı görüntüde **ışık vermedi** → IR-cut filtresi çalışıyor (MUHTEMEL; nitel test, HQ Camera yuvasındaki IR-cut ile tutarlı).
  Kullanıcı elle kâğıt/mesafe testinden emin değil → **satranç tahtası kalibrasyonu** (OpenCV `calibrateCamera`; odak uzunluğu px + bükülme, mesafe ölçümü gerektirmez) + üretici değeri araştırması.
- **20:45 — FOV araştırması + kalibrasyon aracı:**
  Satıcı sayfaları (SparkFun 16762, Adafruit 4563, Waveshare 6mm-wide-angle-lens-for-pi): Raspberry Pi 6 mm CS lens, HQ Camera'da **yatay ~63–65°** (F1.2, 3 MP, 1/2"). **Birincil kaynak DEĞİL.**
  Raspberry Pi'nin kendi `RP-008198-DS-1-cs-mount-lens-guide.pdf` belgesi indirildi, metni tarandı: yalnız montaj/diyafram/odak anlatıyor, **FOV değeri YOK**.
  Nominal 6 mm pinhole hesabı tam genişlikte ~55° → satıcı değeriyle fark, lensin geniş açı bükülmesine işaret edebilir (MUHTEMEL).
  RidgeRun IMX477 wiki'si **başka bir sürücü** (1920×1080@60 · 4032×3040@30) — bizim NVIDIA sürücüsünün ölçülen kipleriyle (3840×2160@30 · 1920×1080@60) uyuşmuyor; sensörün 16:9 binning kipi 2028×1128 → 1920×1080 yatayda ~%95 kırpım olabilir (MUHTEMEL).
  Kalibrasyon aracı: PC scratchpad `kalibrasyon_satranc.py` (OpenCV `findChessboardCorners`+`calibrateCamera`, 9×6 iç köşe, kareleri köprünün `/kare.jpg`'inden çeker, farklı pozları ayırır).
  **Sentetik öz-test GEÇTİ:** bilinen fx=1700 → bulunan **1700,23 (%0,01)**, rms 0,057 px, 15/40 poz. Tahta görüntüsü `satranc_9x6.png` (1320×960) PC ekranında açıldı.
- **22:19 — TELEM2 → Jetson 40-pin UART: DÜŞTÜ, hatta SIFIR bayt.** Kullanıcı jumper kablosunu bağladı (mor→6, mavi→8, yeşil→10 planı; **bip testi yapıldığı teyit edilmedi**), Pixhawk gücü PC USB'sinden.
  Jetson (açılış 22:18): `/dev/ttyTHS1` `root:dialout`, `n4vitas` dialout VAR · `console=ttyTCU0,115200` · `nvgetty`/`serial-getty@ttyTHS1` inactive · `fuser` boş.
  `mavlink_dogrula.py --mavlink /dev/ttyTHS1 --baud 57600 --sysid 1 --sure 10` → `HEARTBEAT zaman aşımı: 15 s içinde hiçbir kaynak konuşmadı` · **VERDIKT DÜŞTÜ, çıkış 1**.
  Ham dinleme (termios, salt okuma, 3 s): `ttyTHS1` ve `ttyTHS2`, 57600 / 115200 / 921600 → **hepsinde 0 bayt** (yanlış baud'da bile çöp bayt gelirdi → RX ucuna sinyal ULAŞMIYOR).
  Pixhawk tarafı (PC USB `ttyACM0`, pymavlink salt okuma): HEARTBEAT sysid 1 · **`SERIAL2_PROTOCOL 2` · `SERIAL2_BAUD 57` · `BRD_SER2_RTSCTS 0` · `SERIAL2_OPTIONS 0` · `SR2_POSITION 8` · `SR2_EXTRA3 2`** → TELEM2 yapılandırması **doğru**.
  **Sonuç (katman):** yazılım/izin/konsol/parametre temiz → sorun **fiziksel hat**: (1) TX/RX ters (en olası; Jetson RX, Pixhawk'ın boşta duran RX'ine bağlıysa tam olarak 0 bayt görülür), (2) jumper yanlış pin/sıra, (3) JST renk↔pin eşlemesi varsayımdan farklı, (4) 40-pin pinmux UART değil (düşük olasılık).
  Sıradaki ayırt edici adımlar: mavi↔yeşil yer değiştir → aynı ham dinleme; sonuç yoksa pin 8–10 **loopback** (Pixhawk'tan ayrık, tek jumper) ile Jetson UART'ını tek başına sına.
- **22:35 — KÖK NEDEN (fotoğraf, MUHTEMEL — iki bağımsız fotoğraf aynı sonucu veriyor):** jumper'lar **yanlış pinlerde**.
  Kenar görünümü fotoğrafındaki alt yüz baskısı sütunları okuttu (`1/2 · 3/4 · 5/6 · 7/8 · 9/10`; dış sıra tek, iç sıra çift). Ölçülen yerleşim: **yeşil (Pixhawk TX) → pin 2 = 5V · mavi (Pixhawk RX) → pin 4 = 5V · mor (GND) → pin 5 = I2C** — GND hiç bağlanmamış, TX/RX Jetson 5V rayına bağlı.
  Bu, ttyTHS1/THS2'deki 0 baytı açıklıyor. 🔴 TELEM2 3,3 V mantıktadır → **olası hasar TEST EDİLMELİ** (düzeltmeden sonra TELEM2 HEARTBEAT + Pixhawk USB'den `SERIAL2_*` ve arıza belirtileri).
  Kullanıcıya TELEM2 fişini hemen çekmesi söylendi. Doğru yerleşim (üst görünüm, sol sütun tek/sağ sütun çift, PWR LED ucundan): **mor 5→6 · mavi 4→8 · yeşil 2→10**, sol sütun ve ilk iki sıra boş. Kullanıcı "tamam" dedi; yeni fotoğraf bekleniyor.
- **22:45 — TELEM2 → Jetson DÜZELTİLDİ ve GEÇTİ.** Kullanıcı jumper'ları taşıdı; iki fotoğrafla doğrulandı (kenar görünümü: üçü **iç/çift sıra** sütun 3–5, ön sıra 5/7/9 açıkta; alt yüz baskısı 6=GND, 8, 10 → **mor 6 · mavi 8 · yeşil 10**; pin 2/4 boş). Bip: kırmızı hiçbir jumper'a bip vermiyor (kullanıcı beyanı).
  Jetson `/dev/ttyTHS1` @57600 ham dinleme **2394 bayt / 3 s** (0xFD 65 · 0xFE 4).
  `mavlink_dogrula.py --mavlink /dev/ttyTHS1 --baud 57600 --sysid 1 --sure 10` → HEARTBEAT sysid 1 compid 1 ArduPilot QUADROTOR (bekleme 0,16 s) · `SET_MESSAGE_INTERVAL` GLOBAL_POSITION_INT 8 Hz ve EXTENDED_SYS_STATE 2 Hz → **ACK ACCEPTED** ·
  10 s: HEARTBEAT 10 (1,00 Hz) · GLOBAL_POSITION_INT 80 (8,00 Hz) · EXTENDED_SYS_STATE 20 (2,00 Hz) · yabancı 0 · **VERDIKT GEÇTİ, çıkış 0**.
  **İki yön kanıtı:** ACK dönmesi Jetson TX → Pixhawk RX hattının da çalıştığını gösterir → 5V'a bağlı kalan TELEM2 TX/RX'te **işlevsel hasar gözlenmedi** (elektriksel/uzun süreli etki ÖLÇÜLMEDİ).
  Jetson `journalctl -k -b`: i2c/serial/over-current/undervolt satırı **yok**. PC USB: HEARTBEAT var, `SERIAL2_PROTOCOL 2 · BAUD 57 · RTSCTS 0` değişmemiş; `system_status=5` (MAV_STATE_CRITICAL), `SYS_STATUS` voltaj **0,00 V** → pilsiz tezgâh (MUHTEMEL pil failsafe), pil takılınca TEST EDİLMELİ.
- **22:50–23:00 — MAVProxy çoğullayıcı TELEM2 (`/dev/ttyTHS1` @57600) üzerinde: 3/3 GEÇTİ, ama AÇILIŞ PENCERESİ bulgusu.**
  (a) `mavproxy.py --master=/dev/ttyTHS1 --baudrate 57600 --streamrate 8 --out 127.0.0.1:1455{0,1,2}` başlatıldıktan **5 s sonra** üç uçta aynı anda `mavlink_dogrula --sure 10`:
  HEARTBEAT 0,90 Hz GEÇTİ · GLOBAL_POSITION_INT **1,90 Hz** DÜŞTÜ · EXTENDED_SYS_STATE **0,50 Hz** DÜŞTÜ → **0/3**. (İlk koşum SSH 124 zaman aşımıyla bitti: betikte `wait` arka plandaki MAVProxy'yi de bekliyordu — araç kusuru, düzeltildi.)
  (b) Hipotez "`--streamrate 8` 57600'ü doyuruyor" → `--streamrate -1` ile tekrar (6 s sonra): 2,00 / 0,50 Hz → **0/3 → hipotez ÇÜRÜDÜ.**
  (c) Hipotez "MAVProxy açılışta tüm parametreleri indiriyor, 57600 hat meşgul" → log: **`Received 1025 parameters` · `Saved 1025 parameters`**; indirme bittikten sonra aynı ölçüm:
  HEARTBEAT 11 (1,10 Hz) · GLOBAL_POSITION_INT 77 (**7,70 Hz**) · EXTENDED_SYS_STATE 21 (**2,10 Hz**) → **3/3 GEÇTİ** (log `/tmp/navitas_telem2_kapi3/`).
  🔴 **Üretim etkisi (kod okuması + bu ölçüm):** `jetson_baslat.sh --kapi` çoğullayıcıyı kaldırıp **`sleep 3`** sonra doğrular (`jetson_paket/jetson_baslat.sh:610`) → TELEM2 @57600'de parametre indirme sürerken **yanlış DÜŞTÜ** verir; tüketiciler de ilk onlarca saniye düşük hızlı telemetri görür; her Pixhawk yeniden başlatmasında tekrarlar.
  Seçenekler (mimar kararı, ölçümle): `SERIAL2_BAUD` 57→921 (Pixhawk parametresi; Jetson UART destekler) · kapının parametre indirme bitişini beklemesi · MAVProxy'nin parametre indirmemesi (yöntemi TEST EDİLMELİ).
  Açık: üretim birimindeki `--streamrate 8` indirme **sonrasında** TELEM2 @57600'de **ölçülmedi** (şu an çalışan MAVProxy `--streamrate -1`).
  **Ses:** kullanıcı "ses geldi", sonra "2 kere ses çıkardı" — iki MAVProxy başlatmasıyla eşzamanlı; kaynağı (Pixhawk/GPS buzzer) görülmedi. Gönderilen tek komut `SET_MESSAGE_INTERVAL`; ARM yok. MAVProxy log'u PreArm reddi: `RC not found` · `Hardware safety switch` · `GPS 1: Bad fix` · `Battery 1 below minimum arming voltage` · `Fence requires position`.
- **22:55–23:00 — CANLI ZİNCİR, KABLOLU PIXHAWK (TELEM2) İLE GEÇTİ, sonra kullanıcı isteğiyle durduruldu.**
  Model: kullanıcı *"v37 ve v36 var ama biz v36'yı kullanacağız"* → Jetson `models/`: v36 `.pt/.onnx/.engine` + v37 `.pt/.onnx` mevcut; kayıt defteri `competition → models/navitas_seg_v36_best.pt` imgsz 512; çalışma logu `kayit dogrulamasi: eslesti` → **v36 kurulu, gönderim gerekmedi**.
  FOV: kullanıcı *"model bu projede İHA'nınki ile aynı"* → proje beyanı `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:285` "FOV yaklaşık 55–63°" (`FDR/BOLUM_1_OZET.md:538`: lens beyanından **tahmin**) + satıcı 63–65° → **`--fov 63` (BEYAN, ÖLÇÜLMEDİ)**. Ölçüm yordamı hazır: `SAHA_KOSUM_KAGIDI_20260910.md` §2 + `scripts/kamera_fov_hesapla.py`.
  İlk deneme: köprü `kaynak_acik false`, 52 kare / 378 düşen, `INVALID_SETTINGS`; `nvargus-daemon` günlüğü **`PD_CRC_ERR: CRC error on packet payload`** + `CsimuxFrameError_Regular` + `Error 15 … sensor 0` → model `Kamera acilamadi`.
  Köprü durduruldu + `nvargus-daemon` yeniden başlatıldı → temiz çekim `num-buffers=300` 1920×1080@30 → **10,7 s, 0 CRC, 0 CsimuxFrameError** (kalan hatalar boş ikinci port `v4l2_sensor` init) → hat sağlam; geçici hatanın sebebi (köprü yeniden açma döngüsü mü, kablo teması mı) **ayrıştırılmadı**.
  Yeniden: köprü `kaynak_acik true` 10 fps · 412 kare / **0 düşen** · 1 istemci; model `--camera --kaynak http://127.0.0.1:8080/video --mavlink udp:127.0.0.1:14550 --mav-sysid 1 --fov 63 --yks-hedef 10.21.8.156:5005 --ekransiz`; MAVProxy `--master=/dev/ttyTHS1 57600 --streamrate -1`; GR3D %99, gpu 52,5 °C, RAM 2,8/3,46 GB.
  **YKS hakem kaydı (son 45 s):** `ROTA_YOK` **141 (3,13/s)** — `MASKE_YOK` 138 · `UC_BANT_TEMAS_YOK` 3 · `TELEMETRI_KANIT iha=TAZE` yaş 0,2 s · mod STABILIZE → **Pixhawk (kablo) → Jetson (IMX477 + v36 GPU) → YKS (PC) zinciri çalışıyor.** Rota doğruluğu kanıtlanmadı (yer, ofis sahnesi).
  23:00 kullanıcı *"durdur kamerayı, kablo bağlantısından emin olayım"* → model, köprü, MAVProxy durduruldu; CSI şerite dokunulacağı için **Jetson kapatıldı (23:00:08, ping kesildi)**.
- **23:05–23:12 — CSI kablo kontrolü sonrası TAM ZİNCİR TEKRAR GEÇTİ.** Kullanıcı şerit kabloyu çıkarıp multimetreyle ölçtü: **15/15 tel uçtan uca bip** (kopuk yok; komşu tel kısa devre testi yapılmadı); geri takıp Jetson'ı açtı.
  Açılış: `imx477 9-001a bound`, `/dev/video0` · temiz çekim 300 kare 10,8 s → **CRC 0 · CsimuxFrameError 0 · Error 15 0**.
  MAVProxy TELEM2 (`/dev/ttyTHS1` 57600, `--streamrate -1`): parametre indirme **1025 param ~42 s**; sonrasında üç uç aynı anda → HEARTBEAT 1,00 · GLOBAL_POSITION_INT 7,70 · EXTENDED_SYS_STATE 2,10 Hz → **3/3 GEÇTİ**.
  Köprü 1920×1080: 677 kare, **0 düşen**. Model v36 `--fov 63 --yks-hedef 10.21.8.156:5005` çalışıyor; RAM 2,8/3,46 GB, gpu 51 °C.
  **YKS (son 30 s):** `ROTA_YOK` **93 (3,10/s)**, sebep `MASKE_YOK` · `TELEMETRI_KANIT iha=TAZE` (yaş 0,9 s) · mod STABILIZE. Canlı çalışmada son 3 dk nvargus **CRC 0**.
  Önceki CRC hatasının sebebi ayrıştırılmadı (kablo temasının yeniden oturtulması ya da argus takılması); bu açılışta tekrar etmedi.
- **23:35–00:05 — laptop ekranından video testi + HDD model karşılaştırması.**
  Test: Jetson IMX477 kamerası, drone videosunu tam ekran oynatan laptop ekranına çevrildi. YKS (PC, yeni kayıt `results/prova/20260915_233210_3797176/`) kamera panelinde **net toprak yol + kaya** görüntüsü (kullanıcı fotoğrafı), karar kutusu yine
  **`ROTA YOK · MASKE_YOK — Zemin maskesi 0 piksel`** (seq 10361). Kullanıcı: *"diğer laptoptan olmadı, hiç yol görmedi, kısıtlı bir ortamdı"*.
  🔴 **Şüphe (TEST EDİLMELİ):** bugün canlı kameradan gelen kararların **tamamı** `MASKE_YOK` (IMX219 ofis 352/352, IMX477 ofis 93+141, ekrandaki yol dahil); oysa aynı model Jetson'da `--image` ile `data/raw_frames` karelerinde maske üretti
  (5 karede 1 `GORUS_HATTI_KOPUK` = maske var) ve 13 Eyl'de 260 kabul karesinde karar verdi (D-482). Ayırt edici deneyler: (a) köprünün `/kare.jpg` karesini (yol görünürken) `--image` ile işlemek; (b) bilinen iyi kareleri `kamera_koprusu --kaynak <dosya>` üzerinden `--camera` yoluna vermek.
  Alternatif açıklamalar (elenmedi): ekran fotoğraflama alan farkı (moiré, parlama, mavi ton), ölçek/irtifa ön kapısı, içerik kırpması.
  HDD: kullanıcının "modeller orada olmalı" dediği disk **PC'ye** takılıydı (`/dev/sda1` NTFS `BACKUP`, 698,6 G, USB); **salt okunur** bağlandı (`udisksctl mount -o ro`), kökte v36 `.pt/.onnx/.engine` + v37 `.pt/.onnx`.
  sha256 (ilk 16): v36 `.pt` **1d1caca6f6da19ea** · `.onnx` f4c9f5fe08883d1a · `.engine` bb9bd8685a98a919 · v37 `.pt` 6aeca0c125a2943d · `.onnx` 13db2094d2a3fdd4 → **Jetson'dakilerle 5/5 birebir aynı**; v36 `.pt` kayıt defteri `competition` sha'sıyla eşleşti → **gönderim gerekmedi**, disk ayrıldı.
  Jetson `/var/crash/_usr_bin_python3.12.1000.crash` 22:57 → köprü durdurma anı (13 Eyl'de kayıtlı kapanış SIGABRT'si ile tutarlı; ekranda Ubuntu "internal error" penceresi).
  Kullanıcı: *"yazılımsal olarak eklenecek birkaç fikir geldi aklıma"* — fikirler bekleniyor.
- **22:20 — mimari teyidi (kullanıcı):** *"drondaki Jetson işlemeyi yapacak ve bana aktaracak"* — Jetson (İHA) işler → PC (YKS) gösterir; ileride + İKA. Başka laptop'tan video ile tezgâh testi A (dosya + `--video --mpp`) / B (canlı yayın) seçimi ve video bilgileri bekleniyor.
- 🔴 18:03: Jetson'da ayrı bir Claude oturumu **açık** (kullanıcı ekran fotoğrafı). SSH ile yapılan kamera/MAVProxy işleriyle çakışmaması kullanıcıya bildirildi.
- FOV: bu IMX219 için **ÖLÇÜLEMEDİ / BEYAN YOK** (Jetson oturumu da teyit etti). `67,3°` yalnız K2 ölçüm betiğine verilen sabit, `160°` iptal edilen IMX477 beyanı — **ikisi de kullanılmaz**.

### 9.4 Bugün modelin CANLI çalışması için kalan (sırayla)
1. **İnsan — kamera fiziksel kontrol:** güç **kapalı**; şerit kablonun iki ucu: temas yüzü doğru yönde mi, kilit kapalı mı, kablo kırık mı. İki ucun fotoğrafı. Sonra aç → `journalctl -k -b | grep imx219` → `probe` hatası yoksa `/dev/video0`.
2. **İnsan — FOV beyanı:** IMX219 modülündeki lensin **yatay** görüş açısı (beyan/ölçüm). Yoksa canlı kipte ölçek türetilemez (`OLCEK_YOK`).
3. **Pixhawk:** 13 Eyl'de kanıtlı yol **USB** — TELEM2 jumper kablosu hazır olana kadar USB takılırsa L6 hemen yeniden koşulur.
4. Kamera açılınca: `kamera_koprusu.py --kaynak nvargus` → `rpi_inference --camera --kaynak http://127.0.0.1:8080/video --mavlink udp:127.0.0.1:14550 --mav-sysid 1 --fov <beyan> --ekransiz`.
5. Sonra `jetson_baslat.sh --kuru` → `--kapi` 3/3 (YKS_IP/IKA_IP beyanı).

## 8. Geri bildirim biçimi

Bitince (ya da tıkandığında) `results/jetson_log_20260915/DURUM.md` yaz: her katman için **GEÇTİ / DÜŞTÜ / ÖLÇÜLEMEDİ**,
koşulan komut, **gerçek çıktı** (kısaltmadan ilgili satırlar), log yolu, açık kalan ve sonraki adım. "Çalışıyor gibi" yazılmaz.

---

# 10. GECE KAPANIŞ RAPORU — 16 Eylül 2026, 00:35–01:00 (kullanıcı: *"tüm sistemi kapat, sabah devam edeceğiz"*)

> Bu bölüm günün **tek sayfalık özetidir**; ayrıntı ve ham çıktılar §9'dadır. Etiketler: KESİN (ölçüm/çıktı) · MUHTEMEL (çıkarım) · TEST EDİLMELİ.

## 10.1 Kapanış yordamı (sırayla, ani kapatma yok)

| # | işlem | sonuç |
|---|---|---|
| 1 | Jetson `/tmp` günlükleri PC'ye alındı (Jetson açılışta `/tmp`'yi temizler) | `results/jetson_20260915/jetson_tmp_loglari/` — 10 dosya, 116 KB |
| 2 | Jetson durum kaydı çıkarıldı | `results/jetson_20260915/jetson_durum_kapanis.txt` (65 satır) |
| 3 | Jetson süreçleri sırayla durduruldu: model `rpi_inference` (SIGINT) → `kamera_koprusu` → MAVProxy | 3/3 durdu, kalan süreç 0 |
| 4 | Jetson `sync` + `systemctl poweroff` | **00:35:24 kapandı** (ping kesildi) |
| 5 | PC YKS (pid 3797176) SIGTERM | kapandı, UDP 5005 serbest |
| 6 | PC `socat` köprüsü | çalışmıyordu (TELEM2'ye geçildiği için 22:45'ten beri kullanılmıyor) |
| 7 | HDD (`/dev/sda1` `BACKUP`) | 00:05'te `udisksctl unmount` ile ayrıldı |
| 8 | Pixhawk | **hâlâ PC USB'sinden güç alıyor** (pil yok) — PC kapanınca/USB çıkınca kapanır; kapatacak yazılım işlemi yok |

## 10.2 Üç cihaz (+ İKA, HDD) — kapanıştaki durum

| cihaz | kimlik | bağlantılar | kapanış durumu |
|---|---|---|---|
| **PC (YKS / kontrol merkezi)** | Fedora 44, `trs`, WiFi `TP-Link_2.4GHz_0041EC` | IP **DHCP ve bugün iki kez değişti**: 10.21.8.112 → (17:47) .156 → (gece) **.112** · Jetson'a SSH anahtarı (`~/.ssh/id_ed25519`) · Pixhawk USB `ttyACM0/1` (yalnız güç; `setfacl` izni geçici) | YKS kapalı · depo `.venv`'e `pyserial 3.5` eklendi · MAVProxy kurulamadı (Py3.14, gerek yok) · `ModemManager` active (Pixhawk portunu yoklayabilir) |
| **Jetson (İHA görev bilgisayarı)** | Orin Nano 4 GB (p3767-0004) + **Seeed reComputer J401**, JetPack 7.2.1, Ubuntu 24.04, `n4vitas`, IP **10.21.8.7** (Ethernet) | **TELEM2 ← Pixhawk** (40-pin **mor 6 GND · mavi 8 TXD · yeşil 10 RXD**, `/dev/ttyTHS1` 57600) · **IMX477 (RPi HQ Camera V1.0) + 6 mm CS lens** CSI (`imx477 9-001a`, kart baskısı "CAM0" = datasheet J9) · WiFi RTL8822CE takılı, **anten yok** | **KAPALI** · boot overlay `imx477-dual` (yedekler: `extlinux.conf.before-imx477-dual-20260915`, `.before-imx219-cam0-20260913`, `.before-cam0-20260913`, `.before-imx477-20260913`) · güç kipi 10W · `/var/crash` 22:57 python3.12 (köprü kapanışı) |
| **Pixhawk 6C (uçuş kontrolcüsü)** | ArduCopter 4.5.7, sysid 1, QUADROTOR | TELEM2 → Jetson · USB-C → PC (güç) · TELEM1 (SiK hattı; tezgâh fotoğrafında plakada **RFD900A** görüldü — D-481 kararıyla çelişki, TELEM1'e hangisi bağlı TEST EDİLMELİ) · GPS1 · RC | açık (USB gücü) · `SERIAL2_PROTOCOL 2 · SERIAL2_BAUD 57 · BRD_SER2_RTSCTS 0 · SR2_POSITION 8 · SR2_EXTRA3 2` (okundu, değiştirilmedi) · `system_status` CRITICAL + voltaj 0,00 V (pilsiz, MUHTEMEL pil failsafe) · PreArm reddi: RC yok, güvenlik anahtarı, GPS fix yok, pil düşük, fence · **hiçbir parametre değiştirilmedi, ARM komutu gönderilmedi** |
| **İKA (Raspberry Pi)** | — | bugün ağa bağlanmadı | **ÖLÇÜLEMEDİ** |
| **HDD `BACKUP`** | 698,6 G NTFS, PC USB | salt okunur incelendi | v36 `.pt/.onnx/.engine` + v37 `.pt/.onnx` sha256 **Jetson'la 5/5 aynı**; ayrıldı |

Çıkarılan/ödünç: **Arducam UC-350 Rev.D (IMX219)** + kendi lensi (~4,3 mm ölçüldü) — Jetson'dan çıkarıldı, kullanılmayacak (ekip kararı).

## 10.3 Bağlantı topolojisi

```
Bugün kanıtlanan (tezgâh, kablolu):
  Pixhawk 6C ──TELEM2 57600──► Jetson /dev/ttyTHS1 ──MAVProxy──► udp 127.0.0.1:14550/14551/14552
  IMX477+6mm ──CSI──► Jetson kamera_koprusu :8080 (1920×1080, 10 fps) ──► rpi_inference v36 (GPU)
  rpi_inference ──UDP OPEN_ROUTE/NO_ROUTE + HEARTBEAT──► PC YKS :5005   (PC ──HTTP :8080──► kamera paneli)
  Pixhawk ──USB──► PC (yalnız güç)

Hedef (henüz koşmadı):
  İHA Jetson ──(SiK 433 / ağ)──► YKS PC ◄──► İKA RPi ; systemd birimleri (jetson_baslat.sh --kur/--kapi)
```

## 10.4 Jetson depo / paket güncelliği (KESİN, `jetson_durum_kapanis.txt`)

| konum | durum |
|---|---|
| Paket `~/navitas` → `~/proje/NAVITAS_JETSON_20260906/navitas` | **git deposu değil**; 12 Eylül 13:54'te güncellenmiş dosyalar içerir |
| Klon `~/proje/github/navitas_github` | dal **`jetson/tek-yol-20260912`** @ `abea98cb` (13 Eyl), uzak **`yazilim-takimi/navitas`** |
| PC deposu | `master` @ `ab906f3a` (14 Eyl), uzak **`navitas26/navitas`** — **iki farklı uzak** |
| paket ↔ klon | 7 anahtar dosya bayt-eş |
| paket ↔ PC master | `codes/rpi_inference.py` **farklı** (Jetson'da T233 = ekransız kipte FPS ortalama/p95 raporu yok; karar yolu aynı) · `config/model_registry.json` farklı (etkin `competition` v36 sha **aynı**) · diğer 5 anahtar dosya eş |
| 🔴 D-numara çakışması | Jetson dalındaki **D-480…D-484** (Codex Jetson denetimi, telsiz bandı, K2 engine≡pt, W/3 ön kayıt, tek yol) ile PC master'daki **D-480…D-490** (İKA kütlesi, FDR dizgi, Gazebo) **aynı numara, farklı içerik** → birleştirmede yeniden numaralandırma gerekir |
| Modeller | v36 (`.pt` `1d1caca6…`, `.onnx`, `.engine`) + v37 (`.pt`, `.onnx`); etkin **v36** (kullanıcı kararı) |

## 10.5 Bugün ne kanıtlandı (katman tablosu)

| katman | sonuç | kanıt |
|---|---|---|
| Jetson ortam (torch cuda, ultralytics, cv2) | ✅ | §9.2 · CC 8.7 uyarısı işlevsel değil (conv2d cuda'da koştu) |
| Model v36 kayıt defteri | ✅ eşleşti | §9.2 |
| Tezgâh çıkarımı (`--image`) | ✅ sebepli kararlar | §9.2 |
| IMX477 kamera | ✅ 300 kare 0 CRC (kablo yeniden takıldıktan sonra) · renk nötr (R/G 0,97) | §9 23:05–23:12 |
| Pixhawk → Jetson TELEM2 | ✅ `mavlink_dogrula` GEÇTİ, iki yön (ACK ACCEPTED) | `jetson_tmp_loglari/` |
| MAVProxy çoğullayıcı 3 uç | ✅ **3/3** — yalnız **parametre indirmesi (1025 param, ~42 s) bittikten sonra** | `navitas_telem2_kapi3/4` |
| Tam zincir Pixhawk→Jetson→YKS | ✅ YKS 93 karar/30 s, `iha=TAZE` | `results/prova/20260915_233210_3797176/` |
| Rota doğruluğu | ❌ **ÖLÇÜLEMEDİ** (yerde, ofis/ekran sahnesi) | — |
| systemd `--kur/--kapi`, `iha_inis_yayinci`, `iha_komut_alici`, İKA | ❌ **KOŞULMADI** | — |

## 10.6 🔴 Açık kalanlar (öncelik sırası)

1. **Canlı kamerada her karede `MASKE_YOK`** — ekranda net yol varken bile (§9 00:05). Offline `--image`'da maske çıkıyor. TEST EDİLMELİ: (a) köprü karesini `--image` ile işle, (b) bilinen iyi kareleri `kamera_koprusu --kaynak <dosya>` üzerinden `--camera` yoluna ver. **Uçuşu doğrudan etkiler.**
2. **FOV ölçümü (IMX477 + 6 mm)** — kullanıcı: yarın. Şu an `--fov 63` = **BEYAN** (FDR B3:285 "55–63°" + satıcı 63–65°). Araçlar: `SAHA_KOSUM_KAGIDI_20260910.md` §2 + `scripts/kamera_fov_hesapla.py`, ya da `scripts/tezgah/kalibrasyon_satranc.py` (sentetik öz-test fx %0,01).
3. **TELEM2 hızı** — `SERIAL2_BAUD` 57600'ün tek gerekçesi betik varsayılanıyla eşleşme (`config/pixhawk/arducopter_fda.param:121-122`). Açılışta ~42 s parametre indirmesi → `jetson_baslat.sh --kapi` (`sleep 3`, `:610`) **yanlış DÜŞTÜ** verir. Seçenek: 921600 (Pixhawk param + `PIXHAWK_BAUD` + şablon + 3 test + D-kaydı) ya da kapının indirme bitişini beklemesi. **Karar bekliyor.** Üretim `--streamrate 8` TELEM2'de indirme sonrası ölçülmedi.
4. **Kapsama (hesap)** — IMX477 Jetson sürücüsünde yalnız 16:9 kipler (3840×2160@30, 1920×1080@60); 4:3 yok. 6 mm nominal → 30 m'de ~30×17 m → 20×20 FDA'nın kısa kenarı sığmaz (≥ ~36 m). FOV ölçülünce yeniden hesaplanacak.
5. **Jetson depo senkronu** — klon dalı `jetson/tek-yol-20260912` master'a girmemiş, iki uzak, D-480…484 numara çakışması, paket T233'ten geride.
6. **YKS adresi** — PC IP'si DHCP ile değişiyor; model `--yks-hedef` sabit IP ister. Sahada DHCP rezervasyonu/sabit IP.
7. **Üretim kurulumu** — systemd birimleri, `--kapi`, iniş yayıncısı, komut alıcısı, İKA hattı hiç koşmadı.
8. **Pixhawk** — pilsizken CRITICAL; RC failsafe (D-428) açık; TELEM1'de hangi telsizin bağlı olduğu (SiK 433 / RFD900A).
9. **CSI CRC olayı** — bir kez oluştu (22:56), kablo yeniden takıldıktan sonra tekrarlamadı; izlenecek.
10. **Jetson belleği** — model+köprü+MAVProxy ile RAM ~2,8/3,46 GB, swap ~1,2 GB.
11. **5V kazası** — jumper'lar bir süre pin 2/4 (5V) ve pin 5'e bağlı kaldı; TELEM2 işlevsel testte sağlam, uzun vadeli elektriksel etki ÖLÇÜLMEDİ.

## 10.7 Sabah başlangıç sırası (kanıtlanmış komutlar)

```bash
# 0) PC: IP'yi oku (YKS hedefi)          ip -4 -o addr show wlp0s20f3
# 1) Güç: Pixhawk USB → PC (güç), Jetson fişi. Pervaneler çıkık.
# 2) Jetson (SSH n4vitas@10.21.8.7):
nohup ~/venv312/bin/mavproxy.py --master=/dev/ttyTHS1 --baudrate 57600 --streamrate -1 \
  --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551 --out udp:127.0.0.1:14552 \
  --daemon --non-interactive --state-basedir /tmp/navitas-mavproxy-telem2 > /tmp/navitas-mavproxy-telem2.log 2>&1 &
#    "Received 1025 parameters" satırını BEKLE (~42 s), sonra üç uçta aynı anda:
#    ~/venv312/bin/python scripts/mavlink_dogrula.py --mavlink udpin:127.0.0.1:<1455N> --sysid 1 --sure 10   → 3/3
cd ~/navitas && nohup /usr/bin/python3 scripts/kamera_koprusu.py --kaynak nvargus --host 0.0.0.0 --port 8080 \
  --genislik 1920 --yukseklik 1080 > /tmp/navitas_kopru.log 2>&1 &
nohup ~/venv312/bin/python -u codes/rpi_inference.py --camera --kaynak http://127.0.0.1:8080/video \
  --mavlink udp:127.0.0.1:14550 --mav-sysid 1 --fov 63 --yks-hedef <PC_IP>:5005 --ekransiz > /tmp/navitas_model.log 2>&1 &
# 3) PC (depo kökü/comms):
../.venv/bin/python yks_gui.py --bind 0.0.0.0:5005 --ika 127.0.0.1:5006 --iha 10.21.8.7:5007 \
  --kamera-url http://10.21.8.7:8080 --kamera-etiket "Jetson IMX477 6mm" --gorunum kamera
# Durdurma sırası: model → köprü → MAVProxy (SIGINT, 8 s sonra SIGTERM); Jetson'da CSI'ya dokunmadan önce poweroff.
```

Dikkat: kamera köprüsü art arda yeniden açılırsa `nvargus-daemon` takılabilir (22:56 olayı) → köprüyü durdur, `sudo systemctl restart nvargus-daemon`, sonra aç. PC'de USB köprüsü gerekirse: `scripts/tezgah/tezgah_mavlink_koprusu.sh baslat|dogrula|durdur` (Pixhawk USB → UDP → Jetson).

## 10.8 Gece kapıları (PC, push öncesi)

| kapı | sonuç |
|---|---|
| Genel kapı `codes/test_rota_sentetik.py` (madde 14) | **GEÇTİ — kol1 15/15 · kol2 şerit 15/15** |
| FDR kapıları `tests/test_fdr*.py` | **77/77 OK** |
| Sunum nöbetçisi `tests/test_sunum_kanit.py` | **5 OK** (1 atlama: gerçek `icerik.json` yok) |
| Tam süit (PC, kanonik ortam DEĞİL — REVIEW_LOG'da kayıtlı) | *§10.9'da* |

## 10.9 Tam süit sonucu ve push kararı

- PC tam süit (16 Eylül 00:38, 444,8 s): **Ran 2877 · failures 47 · errors 9 · skipped 34**. 13 Eylül tabanı: F43 · E21 · S82 (PC kanonik ortam değil).
- Karşılaştırma (test adına göre): ortak kırmızı **38** (ortam: ağırlık/veri `O:\`, pyserial/trimesh, paket aynası…) · tabanda olup düzelen **14** · **yeni kırmızı 1**:
  `test_sim_mujoco_zincir.F_GorevKosumu.test_duman_60s_altinda_ve_metrik_semasi` → `sure_sim_iha_profil 38.81 != 36.98`. Tek başına deterministik (2,5 s) — zamanlama değil.
- **İzolasyon (KESİN):** HEAD `ab906f3a` temiz worktree → `ModuleNotFoundError: scenario_profiles` (modül **depoda yok**, yalnız PC'de izlenmeyen dosya → temiz klonda test açılamıyordu). HEAD + 120 izlenmeyen simülasyon dosyası → **OK**. Aynı ağaca başka oturumun commitlenmemiş `simulation/scripts/world_generator.py` + `simulation/plugins/navitas_anim.cc` değişiklikleri (D-488 hız / D-490 moloz) eklenince → **38.81 DÜŞTÜ**.
- **Karar:** kapıyı düşüren bu iki dosya **push EDİLMEDİ** (anayasa §5: kapı düşmüşken push yok); yerelde commitlenmemiş duruyor. Sahibi oturum test beklentisini (36,98) yeni hız sözleşmesine göre ön kayıtla güncelleyip bağımsız denetimle birleştirmeli. Geri kalan başka oturum işi (D-487…D-490 kayıtları, izlenmeyen simülasyon varlıkları/betikleri/testleri, Codex 15 Eyl raporu) ayrı commit olarak push edildi; derleme artığı `.gazebo-image-build.stamp`, `harita_gecmisi/` (22 Temmuz otomatik), `realism_runs/` çıktıları hariç.
- Push edilen durumun kapıları temiz worktree'de yeniden koşuldu: bkz. `REVIEW_LOG.md` D-491 §7.

## 10.10 Gizlilik

Jetson `sudo` parolası ve kampüs portal kimlik bilgileri **hiçbir depo dosyasına ve hafıza notuna yazılmadı**; kampüs portal betiği (kimlik dosyası okur) depoya **alınmadı** (yalnız PC scratchpad). Commit adaylarında gizli dizgi taraması temiz.
