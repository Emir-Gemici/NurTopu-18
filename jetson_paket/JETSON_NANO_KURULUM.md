# JETSON NANO 4GB — SIFIRDAN KURULUM (Faz B · Görev N · 2026-09-03)

> **NEDEN:** `SAHA_HAZIRLIK_PLANI_20260903.md` **§1.3** (Nano yığını — EN KRİTİK) ve **§1.5**
> (JetPack SD imajı). Kullanıcı beyanı (§0.2): kart **Jetson Nano 4GB**, JetPack **4.6.x**
> (Ubuntu 18.04, sistem Python **3.6**, sistem OpenCV 4.1 GStreamer'li), **cumartesi
> geliyor, kurulu DEĞİL**. Repo `codes/rpi_inference.py` → `from ultralytics import YOLO`
> (Python ≥ 3.8). Kamera **Raspberry Pi HQ (IMX477, CSI)**; görüntü yalnız GStreamer
> `nvarguscamerasrc` ile alınır (pip `opencv-python` wheel'i GStreamer'sızdır).
>
> ⚠ **`JETSON_KILAVUZ.md` Orin NX'e göre yazıldı ve DEĞİŞTİRİLMEDİ** (ölçüm kaydıdır).
> Bu belge onun §1–2'sini Nano için yeniden kurar; çelişen her yer **"Nano'da böyle DEĞİL"**
> etiketiyle işaretlidir. Etiket yoksa Orin kılavuzundaki satır Nano'da da geçerlidir.
>
> Her adımın **kapısı** vardır; kapı geçilmeden sonraki adıma geçilmez (fail-closed).
> Kapı çıktıları saha defterine **olduğu gibi** yapıştırılır — "çalıştı" yazılmaz, çıktı yazılır.
>
> Test kilidi: `tests/test_faz_b_nano_kurulum.py` (bu belge + `requirements_nano.txt` +
> `scripts/nano_tekerlek_indir.py --kuru`).

---

## 0. Orin NX kılavuzundan farklar — önce bunu oku

| konu | `JETSON_KILAVUZ.md` (Orin NX) | **Nano'da böyle DEĞİL** |
|---|---|---|
| Bellek | 16 GB | **4 GB** — swap 4 GB **şart** (§2.3); `yolo export`/INT8 bu kartta denenmez |
| Sistem Python | 3.8+ (JetPack 5) | **3.6** — `ultralytics` kurulmaz; **`~/venv38`** (Python 3.8 venv) kullanılır (§3) |
| torch | NVIDIA JetPack wheel'i (§3 *"pip install torch YAPMA"*) | NVIDIA wheel'i **Py3.6 içindir**, venv38'e giremez. **Garanti yol PyPI aarch64 CPU torch**; GPU yalnız topluluk wheel'i ile **denenir** (§4) |
| Paket kurulumu | §3 `pip3 install ultralytics …` (çevrimiçi, sistem python) | **çevrimdışı**: PC'de indirilen `wheels/` + `pip install --no-index` (§3) |
| TensorRT `.engine` (§4, T16) | Jetson'da derlenir | venv38'de `tensorrt` modülü **yok** (JetPack 4.6 bağı Py3.6). `.engine` **30 Eylül için ÖLÇÜLEMEDİ**; **PT/ONNX ile uçulur** (`FAZ_B_GUN_PLANI` §2 zaten izin veriyor) |
| Kamera | §6B DroidCam (HTTP) | CSI IMX477 → `jetson-io` overlay + `nvarguscamerasrc`; venv38 cv2'si bunu **açamaz** → **`kamera_koprusu.py`** (sistem python3 + sistem cv2) HTTP/MJPEG sunar, `rpi_inference --kaynak http://127.0.0.1:8080/video` (§6) |
| Güç modu | `nvpmodel -m 0` = MAXN (25 W) | `nvpmodel -m 0` = **MAXN 10 W** (4 çekirdek); 5 V/**≥ 4 A** besleme + **J48** jumper şart (plan §0.2 UBEC) |
| `jetson_baslat.sh` | `PYTHON3=/usr/bin/python3` | **`PYTHON3=/home/navitas/venv38/bin/python`** (navitas birimleri); kamera köprüsü birimi **sistem python3** ile (§7) |
| `mavproxy.py` | `pip3 install MAVProxy` → `~/.local/bin` | venv38'e kurulur; birim `PATH`'i `~/.local/bin` arar → **symlink** (§5.3) |
| FPS beklentisi | Orin: 0,9–2,6 FPS bandı rahat | **ÖLÇÜLMEDİ**. Kapı **0,61 FPS** (D-374/376, `FAZ_B_GUN_PLANI` §1) p50 **ve** p95 — **eşik gevşetilmez** (§8) |

🔴 **Dürüst risk:** üretim modeli v36 **YOLOv8m-seg** (27,2 M parametre, `JETSON_KILAVUZ` §4).
Plan §1.3'teki "~0,7–1 FPS" tahmini **yolov8n-seg** içindir; **m** modelin Nano CPU'da
512'de hızı **ölçülmedi** ve 0,61'in altında çıkabilir. Bu durumda kapı **düşer**, eşik
**gevşetilmez**; çözüm adayları (GPU wheel §4, `onnxruntime` ile ONNX §8) sırayla ölçülür,
karar mimara ve D-kaydına gider. Bu belge sonucu **tahmin etmez**.

---

## 1. PC'de (cuma, Nano gerekmez): JetPack SD imajı — plan §1.5

1. NVIDIA developer sayfası → **Jetson Nano Developer Kit** → *"Jetson Nano Developer Kit SD
   Card Image"*, JetPack **4.6.x (son 4.6)**. ⚠ **"Jetson Nano 2GB"** imajını **indirme** —
   kart 4 GB'lık Developer Kit. Sürüm numarası burada uydurulmaz; sayfada ne yazıyorsa o.
2. microSD **≥ 64 GB, UHS-I** (plan §1.11 alışverişte). **balenaEtcher** ile `.zip`'i
   doğrudan seç → *Flash* (Etcher zip'i kendisi açar).
3. **Kapı:** Etcher *"Flash Complete!"* + doğrulama (*Validating*) hatasız. Kart PC'de
   birden çok bölüm gösterir (Windows "biçimlendir?" diye sorar — **HAYIR**).
4. Belleğe ayrıca: `jetson_paket/` (tümü), **`wheels/`** (§3), `config/pixhawk/*` (plan §1.6–1.7).

---

## 2. Nano ilk açılış (cumartesi 14:30 — plan §2.5)

### 2.1 Güç ve ilk kurulum sihirbazı
- Besleme: **barrel jack 5 V/≥ 4 A** (UBEC) + **J48 jumper takılı**; micro-USB'den besleme
  MAXN'de **çöker/yeniden başlar** (Nano'ya özgü; Orin'de bu jumper yok).
- HDMI + klavye. Lisans → dil → klavye → saat dilimi → **kullanıcı adı `navitas`**
  (`jetson_baslat.sh` `SERVIS_KULLANICI` varsayılanı ve birimlerdeki `User=navitas` ile **aynı**;
  başka ad seçilirse birimler kalkmaz) → APP bölümü **azami** boyut → güç modu **MAXN**.
- Ağ: Ethernet ya da Wi-Fi dongle (Nano'da yerleşik Wi-Fi **yok**). İnternet **yalnız `apt`
  için** (§3.1); pip paketleri çevrimdışı gelir.

**Kapı 2.1:**
```bash
whoami                      # navitas
cat /etc/nv_tegra_release   # "# R32 (release), REVISION: 7.x" (JetPack 4.6.1+) ya da 6.x (4.6) — R35/R36 görürsen YANLIŞ imaj
python3 --version           # 3.6.x — beklenen; ultralytics BURAYA kurulmaz
python3 -c "import cv2; print(cv2.__version__, 'GStreamer' in cv2.getBuildInformation())"   # 4.1.x True
free -h                     # Mem 3.9G; Swap satırı §2.3'ten ÖNCE ~2G (zram)
```
Dört çıktı saha defterine.

### 2.2 Güç modu — *Orin'deki "MAXN" burada 10 W'tır*
```bash
sudo nvpmodel -m 0          # Nano: 0 = MAXN (10 W, 4 çekirdek) · 1 = 5 W (2 çekirdek) — 0 kalır
sudo jetson_clocks
sudo nvpmodel -q            # Kapı: "NV Power Mode: MAXN"
```
`jetson_clocks` yeniden başlatmada **kalıcı değildir**; `jetson_baslat.sh` bunu yapmaz — FPS
ölçümünden ve uçuştan önce **elle** koşulur (tutanak §9'a satır).

### 2.3 Swap 4 GB — *Nano 4GB için ŞART, Orin'de gerekmez*
`ultralytics` + torch yüklemesi tek başına ~1,5 GB RAM alır; zram 2 GB **yetmez**, OOM
`Restart=always` döngüsü üretir.
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h                     # Kapı: Swap toplamı ≥ 4G (+ zram)
```

### 2.4 Kamera overlay — `jetson-io` ile IMX477 (RPi HQ)
IMX477 desteği **JetPack 4.6 ile geldi**; listede yoksa imaj eski demektir (§1'e dön).
```bash
sudo /opt/nvidia/jetson-io/jetson-io.py
```
Menü: **Configure Jetson Nano CSI Connector → Configure for compatible hardware →
Camera IMX477** (tek kamera; "Dual" DEĞİL) → **Save pin changes → Save and reboot to
reconfigure pins**. Yeniden başlar.

**Kapı 2.4 (HDMI bağlıyken):**
```bash
ls /dev/video0                                              # var olmalı
gst-launch-1.0 nvarguscamerasrc sensor-id=0 ! nvoverlaysink  # ekranda CANLI görüntü; Ctrl+C
```
Ekransız kapı (tek kareyi dosyaya yaz, gözle bak):
```bash
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! \
  nvvidconv ! 'video/x-raw,format=I420' ! jpegenc ! filesink location=/home/navitas/imx477_ilk_kare.jpg
```
`imx477_ilk_kare.jpg` siyah/yeşil ise: şerit kablo yönü (mavi taraf konektör kilidine
bakar), kilit tam basılı mı, `jetson-io` seçimi kaydedildi mi (`sudo dmesg | grep -i imx477`).
🔴 **AYNA TESTİ** (`GUN1_KONTROL_LISTESI` §7, D-349): kadraja **sol** kenardan sokulan
nesne görüntüde **solda** olmalı — §6'da köprü üzerinden **tekrar** yapılır.

---

## 3. Python 3.8 venv + çevrimdışı tekerlekler — plan §1.3

### 3.1 Nano'da `python3.8` (bionic deposunda VAR — tek `apt` adımı)
```bash
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev
python3.8 --version                 # Kapı: Python 3.8.x
python3.8 -m venv /home/navitas/venv38
source /home/navitas/venv38/bin/activate
python -V                           # 3.8.x — bundan sonra "python" = venv38
```
`sudo apt install` internet ister; **cumartesi ağ yoksa** cuma PC'de `.deb` indirilir:
`apt-get download python3.8 python3.8-venv python3.8-dev python3.8-minimal libpython3.8
libpython3.8-dev libpython3.8-minimal libpython3.8-stdlib` (bionic, arm64) — bu liste
**doğrulanmadı**, ağlı kurulum esas yoldur.

### 3.2 PC'de tekerlekler — `scripts/nano_tekerlek_indir.py`
Paket listesinin **tek kaynağı** `jetson_paket/kod/requirements_nano.txt` (`requirements_rpi.txt`
üst kümesi + torch/torchvision/onnxruntime/MAVProxy/lxml/future + pip/setuptools/wheel).
⚠ **`opencv-python-headless` DEĞİL, `opencv-python`:** gerçek indirmede görüldü — `ultralytics`
`opencv-python>=4.6` ister, çözümleyici headless'i bu şarta **saymaz**; headless listelenirse
Nano'da **ikisi birden** kurulur ve aynı `cv2` paketini üst üste yazar. Nano masaüstü imajı
libGL taşır; `opencv-python` açılır. Bu cv2 GStreamer'sızdır (§6 köprü bu yüzden var).
```bash
# PC (depo venv'i) — önce kuru: hiçbir şey indirmez, komutları basar
O:\navitas-local-train\venv\Scripts\python.exe scripts\nano_tekerlek_indir.py --kuru
# gerçek indirme (wheels/ repoya GİRMEZ — .gitignore)
O:\navitas-local-train\venv\Scripts\python.exe scripts\nano_tekerlek_indir.py
# doğrudan belleğe:  ... --dest E:\wheels
```
Betiğin bayrakları (sabitler betikte, test kilitler): `pip download --only-binary=:all:
--python-version 3.8 --implementation cp --abi cp38 --platform manylinux2014_aarch64
--platform manylinux_2_17_aarch64 --platform manylinux_2_24_aarch64 --platform
manylinux_2_26_aarch64 --platform manylinux_2_27_aarch64`. **Neden bu liste:** Ubuntu 18.04
**glibc 2.27** — `manylinux_2_28_aarch64` wheel'leri Nano'da **açılmaz**; betik böyle bir dosya
görürse `YANLIS_PLATFORM` der ve çıkış **2** verir (fail-visible).

Her paket üç kademe dener: **WHEEL** (wheel + bağımlılıklar) → **WHEEL_BAGIMSIZ** (paketin
wheel'i var, bir bağımlılığının yok) → **KAYNAK** (sdist; Nano'da derlenir) → **BASARISIZ**.
Çıktılar: `wheels/INDIRME_RAPORU.txt`, `wheels/kaynak_paketler.txt`.

### 3.3 Gerçek indirme sonucu (PC, 3 Eylül 2026 — betik GERÇEKTEN koşuldu)

Komut: `O:\navitas-local-train\venv\Scripts\python.exe scripts\nano_tekerlek_indir.py`
(pip 26.1.2, PC x86_64 Windows, internet var). Ham çıktının son satırı:

```
OZET: {'WHEEL': 14, 'WHEEL_BAGIMSIZ': 0, 'KAYNAK': 0, 'BASARISIZ': 0} | 51 dosya | rapor ...\wheels\INDIRME_RAPORU.txt | kaynak listesi ...\wheels\kaynak_paketler.txt
EXIT=0
```

| paket (requirements_nano.txt) | durum | çözümlenen wheel |
|---|---|---|
| ultralytics | WHEEL (33 dosya) | `ultralytics-8.4.118-py3-none-any` + bağımlılıklar (aşağıda) |
| opencv-python | WHEEL (ultralytics ile geldi) | `opencv_python-4.8.1.78-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64` |
| numpy<2 | WHEEL | `numpy-1.24.4-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64` |
| pyserial | WHEEL | `pyserial-3.5-py2.py3-none-any` |
| pymavlink | **WHEEL** (3 dosya) | `pymavlink-2.4.49-cp38-cp38-manylinux2014_aarch64…` + `lxml-5.4.0` + `fastcrc-0.3.6` |
| torch | WHEEL (ultralytics ile geldi) | `torch-2.4.1-cp38-cp38-manylinux2014_aarch64` (**CPU**, ~90 MB) |
| torchvision | WHEEL | `torchvision-0.19.1-cp38-cp38-manylinux2014_aarch64` |
| onnxruntime | WHEEL (6 dosya) | `onnxruntime-1.19.2-cp38-cp38-manylinux_2_27_aarch64.manylinux_2_28_aarch64` + protobuf 5.29.6, flatbuffers, coloredlogs, humanfriendly |
| MAVProxy | WHEEL | `MAVProxy-1.8.70-py3-none-any` |
| lxml / future | WHEEL | `lxml-5.4.0` (pymavlink ile), `future-1.0.0-py3-none-any` |
| pip / setuptools / wheel | WHEEL | `pip-25.0.1`, `setuptools-75.3.4`, `wheel-0.45.1` (py3.8'in son sürümleri) |

ultralytics bağımlılıkları (hepsi cp38/abi3 aarch64 ya da saf Python): PyYAML 6.0.3, matplotlib 3.7.5,
pillow 10.4.0, polars 1.8.2 (`manylinux_2_24_aarch64`), psutil 7.2.2, scipy **yok** (8.4.x istemiyor),
requests 2.32.4, sympy 1.13.3, networkx 3.1, ultralytics-thop 2.1.6, nvidia-ml-py, fsspec, filelock,
jinja2, MarkupSafe, contourpy, kiwisolver, fonttools, cycler, pyparsing, python-dateutil, six,
typing_extensions, mpmath, packaging, certifi, charset_normalizer, idna, urllib3.

- **`kaynak_paketler.txt` BOŞ** — görev tanımındaki "pymavlink kaynaktan derlenir" varsayımı
  **yanlış çıktı**: 2.4.49 cp38/aarch64 wheel taşıyor. Nano'da derleme **gerekmez**; kademe
  (sdist'e düşme) betikte duruyor, ileride bir sürüm wheel'siz gelirse görünür olur.
- **Toplam 51 dosya, 246 MB** (`wheels/`, repoya girmez). Bellekte yer: ≥ 300 MB.
- **İlk koşumun bulgusu (düzeltildi):** listede `opencv-python-headless` varken ultralytics
  yine `opencv_python-4.8.1.78` çekti (şart `opencv-python>=4.6`) → Nano'da iki `cv2` üst
  üste yazılırdı. Liste `opencv-python`'a çevrildi, headless çıkarıldı.
- **Zararsız artık:** `pyreadline3-3.5.6` (humanfriendly'nin `sys_platform == "win32"`
  bağımlılığı; `pip download` işaretleyicileri PC'ye göre değerlendirir). Nano'da kurulmaz,
  dosya durabilir.
- Nano'da hedef: `python -c "import torch; print(torch.__version__)"` → `2.4.1` (CPU, `+cpu`
  eki yok — PyPI aarch64 yapısı). GPU için §4.

### 3.4 Nano'da kurulum (venv38 aktif, bellek `/media/navitas/<BELLEK>/wheels` → `~/wheels`)
```bash
cp -r /media/navitas/*/wheels /home/navitas/wheels
cd /home/navitas/wheels                                          # betik requirements_nano.txt'yi buraya da kopyalar
pip install --no-index --find-links . pip setuptools wheel      # önce araçlar (çevrimdışı)
pip install --no-index --find-links . -r requirements_nano.txt 2>&1 | tail -n 20
```
`kaynak_paketler.txt` **boşsa** (3 Eylül koşumunda boş — §3.3) derleme yoktur, kurulum
dakikalar sürer. Doluysa oradakiler bu komutta **derlenir** (Nano'da 5–15 dk; `python3.8-dev`
bu yüzden kuruldu); derleme düşerse çıktı deftere, **`--no-build-isolation` ile tekrar**
denenir (setuptools venv'de hazır).

**Kapı 3.4:**
```bash
python -c "import cv2, numpy, ultralytics, serial, pymavlink, torch, torchvision; print(cv2.__version__, numpy.__version__, ultralytics.__version__, torch.__version__)"
python -c "import onnxruntime; print(onnxruntime.__version__, onnxruntime.get_available_providers())"
mavproxy.py --version
```
Üçü de hatasız → geç. `ImportError` görülürse hangi paket → `INDIRME_RAPORU.txt`'de durumu
ne (WHEEL/KAYNAK/BASARISIZ) → deftere; **bu belge tahmin yazmaz.**

---

## 4. GPU seçeneği — isteğe bağlı, GARANTİ DEĞİL

JetPack 4.6 (CUDA 10.2) için **Python 3.8** torch wheel'i NVIDIA'da yoktur; topluluk deposu
**Qengineering/PyTorch-Jetson-Nano** (GitHub) Nano için derlenmiş cp38 wheel'leri ve
eşleşen torchvision'ı sunar. Cuma PC'de indirilir, belleğe konur; **denenir, olmazsa CPU**.
```bash
source /home/navitas/venv38/bin/activate
pip install --no-index --find-links /home/navitas/wheels /home/navitas/wheels/gpu/torch-*-cp38-*linux_aarch64.whl
pip install --no-index --find-links /home/navitas/wheels /home/navitas/wheels/gpu/torchvision-*-cp38-*linux_aarch64.whl
```
Kural: torch ve torchvision **aynı çiftten** (depodaki tabloya göre); CPU torch'un üstüne
kurulur (pip değiştirir). Kurulum düşerse: `pip install --no-index --find-links
/home/navitas/wheels torch torchvision` ile **CPU'ya geri dön**, deftere yaz.

**Kapı 4 (True/False İKİSİ DE KABUL — tutanağa yazılır):**
```bash
python -c "import torch, ultralytics, cv2; print(torch.__version__, torch.cuda.is_available())"
```
`True` → §8 FPS'i `--cihaz 0` ile; `False` → `--cihaz cpu`. **Eşik 0,61 FPS her iki durumda
aynıdır, gevşetilmez.** GPU'da `cudnn`/bellek hatası alınırsa CPU'ya dönülür — GPU **uçuş
şartı değildir**.

---

## 5. Paket kurulumu (`JETSON_KILAVUZ` §2 ile aynı yapı)

### 5.1 Kopyalar
```bash
mkdir -p ~/navitas/{codes,comms,scripts,models,data,config,results}
cd /media/navitas/*/jetson_paket
cp kod/rpi_inference.py kod/costmap_path_finder.py kod/karar_sozlesmesi.py kod/arac_maskesi.py ~/navitas/codes/
cp kod/model_registry.py kod/kamera_dogrula.py kod/karisim_arena.yaml ~/navitas/codes/
cp kod/kamera_koprusu.py ~/navitas/scripts/          # Görev K (§6) — jetson_baslat.sh SCRIPTS/ altında arar (D-407: codes/ yazılıydı, --kur HATA ile dururdu)
cp kod/protocol.py kod/link.py kod/iha_sender.py kod/inis_kaniti.py kod/iha_inis_yayinci.py kod/iha_komut_alici.py kod/seri_hub.py ~/navitas/comms/
cp kod/mavlink_dogrula.py kod/jetson_fps.py ~/navitas/scripts/
cp models/* ~/navitas/models/
cp config/model_registry.json ~/navitas/config/
cp -r test_goruntuleri ~/navitas/data/
cp -r kalibrasyon ~/navitas/
cp -r systemd jetson_baslat.sh JETSON_BASLAT.md ~/navitas/jetson_paket/ 2>/dev/null || (mkdir -p ~/navitas/jetson_paket && cp -r systemd jetson_baslat.sh JETSON_BASLAT.md ~/navitas/jetson_paket/)
```
*Nano'da böyle DEĞİL:* `JETSON_KILAVUZ` §2'de kalibrasyon/INT8 dosyaları derleme içindir;
burada **yalnız** taşınır, derleme yapılmaz (§0).

### 5.2 Kayıt defteri kapısı — `model_kayit_dogrula` (T103/D-177, fail-closed)
```bash
cd ~/navitas && /home/navitas/venv38/bin/python - <<'PY'
import sys; sys.path.insert(0, "codes")
from rpi_inference import model_kayit_dogrula
ok, detay = model_kayit_dogrula("models/navitas_seg_v36_best.pt")
print("UYUMLU" if ok else "RED", detay)
PY
```
**Kapı:** ilk kelime `UYUMLU`. `RED` + `kayit_defteri_yok` → `config/model_registry.json`
kopyalanmamış; `--kayit-dogrulamasiz` **sahada YASAK** (`JETSON_KILAVUZ` §2 kırmızı kutu).

### 5.3 MAVProxy'yi birimin `PATH`'ine tanıt
`navitas-cogullayici.service` → `/usr/bin/env mavproxy.py`, `PATH=/home/navitas/.local/bin:…`.
MAVProxy venv38'de; birim dosyasına dokunmadan:
```bash
mkdir -p /home/navitas/.local/bin
ln -sf /home/navitas/venv38/bin/mavproxy.py /home/navitas/.local/bin/mavproxy.py
/home/navitas/.local/bin/mavproxy.py --version        # Kapı: sürüm basar
```

### 5.4 `.engine` — *Nano'da böyle DEĞİL*
`JETSON_KILAVUZ` §4 (`yolo export … format=engine`) ve §4b **atlanır**: venv38'de `tensorrt`
yok, 4 GB'ta derleme OOM riski. Kayıt defterinde `.engine` türevi `DERLENINCE_YAZILIR`
kalır (= RED, doğru davranış). **30 Eylül tutanağına: `.engine` ÖLÇÜLEMEDİ — PT/ONNX ile
uçuldu.** ONNX türevi (`navitas_seg_v36_best_512_fp16.onnx`) defterde **sha'lı kayıtlıdır**;
`--model` ile seçilebilir (§8).

---

## 6. Kamera köprüsü (Görev K yazıyor) — CSI → HTTP/MJPEG

Neden: venv38'in `cv2`'si (pip wheel) GStreamer'sız → `nvarguscamerasrc` **açamaz**; sistem
python3 (3.6) + sistem cv2 (GStreamer'lı) açar ama `ultralytics` koşamaz. İki dünyayı
`kamera_koprusu.py` bağlar: sistem python3 ile kareyi alır, `http://127.0.0.1:8080/video`
(MJPEG) sunar; `rpi_inference --kaynak http://127.0.0.1:8080/video` bu akışı DroidCam
yolundan (T73 `--kaynak`, `JETSON_KILAVUZ` §6B) okur.
```bash
# terminal 1 — SİSTEM python3 (venv38 DEĞİL)
/usr/bin/python3 ~/navitas/scripts/kamera_koprusu.py          # bayraklar: Görev K belgesi
# terminal 2 — venv38
cd ~/navitas && /home/navitas/venv38/bin/python codes/kamera_dogrula.py \
  --kaynak "http://127.0.0.1:8080/video" --kare 120 --isinma 15 \
  --kaydet ~/navitas/results/kopru_ilk_kare.jpg
```
**Kapı 6:** `kamera_dogrula` son bloğu (`okunan kare`, `OLCULEN FPS`, `cozunurluk`) deftere;
`kopru_ilk_kare.jpg` gözle **gerçek** kamera; **AYNA TESTİ** tekrar (sol → sol). Yedek:
USB webcam `--kaynak 0` (plan §1.4/1.11) — köprüsüz, venv38 cv2 doğrudan açar.

---

## 7. `jetson_baslat.sh` — venv38 ile

`JETSON_BASLAT.md` sırası aynen: **`--kuru` → `--kapi` → birimler**. Tek fark ortam değişkeni:
```bash
cd ~/navitas
export PYTHON3=/home/navitas/venv38/bin/python          # navitas-* birimleri (rpi_inference, iha_*, seri_hub)
export KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<ölçülen derece>
export KAMERA=http://127.0.0.1:8080/video               # rpi_inference --kaynak (köprü, §6)
bash jetson_paket/jetson_baslat.sh --kuru               # Kapı: çıkış 0, [EKSIK] yok, [VAR] mavproxy.py (PATH), yorumlayıcı venv38
sudo -E bash jetson_paket/jetson_baslat.sh --kapi       # Kapı: mavlink_dogrula 3/3 GEÇTİ → tüketiciler kalkar
bash jetson_paket/jetson_baslat.sh --durum              # Kapı: her birim active, restart sayısı 0
```
Kamera köprüsü birimi (`navitas-kamera-koprusu`, Görev K) **sistem python3** ile koşar —
`PYTHON3` onu etkilemez; K belgesindeki değişken adıyla verilir. `sudo -E` şart: `PYTHON3`
`/etc/navitas.env`'e oradan yazılır. `--kuru` çıktısında `/usr/bin/python3` görülüyorsa
`export` yapılmamış demektir — birimler sistem Python'uyla kalkar ve `ultralytics` bulamaz.

---

## 8. FPS ölçümü, 10 dk ekransız koşum, `--durum`

### 8.1 FPS (`jetson_fps.py`, uçtan uca: kare oku → çıkarım → get_masks → costmap)
```bash
sudo nvpmodel -m 0 && sudo jetson_clocks                # §2.2 — her ölçümden önce
cd ~/navitas
/home/navitas/venv38/bin/python scripts/jetson_fps.py \
  --girdi data/test_goruntuleri/sentetik_arena \
  --pt models/navitas_seg_v36_best.pt \
  --onnx models/navitas_seg_v36_best_512_fp16.onnx \
  --engine models/YOK --imgsz 512 \
  --isinma 5 --tekrar 60 --conf 0.30 --cihaz cpu \
  --cikti results/nano_fps_$(date +%Y%m%d_%H%M%S)
```
`--cihaz 0` yalnız §4 kapısı `True` verdiyse. **Kapı 8.1:** `ozet.json` p50 **ve** p95 FPS
**≥ 0,61** (D-374/376; `GUN1_KONTROL_LISTESI` §5 — iki sayının kötümseri esas). Altında →
kapı **düşer, eşik gevşetilmez**; sırayla ölçülür ve deftere yazılır: (a) ONNX vakası
(`onnxruntime` CPU) aynı koşumda zaten ölçülür, (b) GPU wheel §4. Hâlâ altındaysa karar
**mimara** (D-kaydı) — bu belge çözünürlük/model değiştirmez.
Ayrı terminalde `sudo tegrastats --interval 1000 | tee ~/navitas/results/tegrastats_fps.log`.

### 8.2 10 dakika ekransız koşum (şartname üst sınırı)
§7 birimleri kalkık, HDMI **çıkarılmış**, kamera köprüsü açık:
```bash
date; sleep 600; date
bash jetson_paket/jetson_baslat.sh --durum              # Kapı: 5 birim active, restart sayısı 0
journalctl -u navitas-rpi-inference --since "-10 min" | grep -ci "OPEN_ROUTE\|NO_ROUTE"   # > 0
```
Restart sayısı **artıyorsa** çökme döngüsü: `journalctl -u navitas-<birim> -n 50` deftere;
OOM görülürse (`Killed process`) §2.3 swap'ı ve `free -h` kontrol.
İlk 1 dk ↔ son 1 dk FPS düşüşü > %15 → **TERMAL** bayrağı (`GUN1` §6).

---

## 9. Tutanak (saha defterine — hepsi doluysa Nano "kurulu" sayılır)

| # | kapı | çıktı (yapıştır) |
|---|---|---|
| 2.1 | `nv_tegra_release` R32 · `whoami` navitas · sistem cv2 GStreamer True | |
| 2.2 | `nvpmodel -q` MAXN · `jetson_clocks` koşuldu (saat) | |
| 2.3 | `free -h` Swap ≥ 4G | |
| 2.4 | IMX477 canlı görüntü / `imx477_ilk_kare.jpg` · ayna testi | |
| 3.1 | `python -V` 3.8.x (venv38) | |
| 3.4 | import satırı hatasız · `mavproxy.py --version` | |
| 4 | `torch.cuda.is_available()` → True / False (ikisi de kabul) | |
| 5.2 | `model_kayit_dogrula` UYUMLU | |
| 5.3 | `~/.local/bin/mavproxy.py --version` | |
| 6 | `kamera_dogrula` son bloğu · `kopru_ilk_kare.jpg` · ayna testi | |
| 7 | `--kuru` çıkış 0 · `--kapi` 3/3 · `--durum` restart 0 | |
| 8.1 | p50 / p95 FPS (PT, ONNX; cihaz) ≥ 0,61 — sayı, GEÇTİ/DÜŞTÜ | |
| 8.2 | 10 dk sonra `--durum` restart 0 · termal bayrağı | |
| — | `.engine`: **ÖLÇÜLEMEDİ** (PT/ONNX ile uçuş) | ✓ önceden yazıldı |
