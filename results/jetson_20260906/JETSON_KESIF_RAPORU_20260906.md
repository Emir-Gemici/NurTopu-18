# NAVITAS — JETSON KEŞİF RAPORU · 6 Eylül 2026

> **7 Eylül 2026 — depoya taşıma notu (G0a, REVIEW_LOG D-431).** Bu belge 6 Eylül Jetson oturumunda
> yazıldı ve `GELISTIRICIYE_20260906` paketiyle geldi. Taşınırken: paketin **D-428** numarası master'daki
> D-428/429/430 ile çakıştığı için kayıt **D-431** oldu ve buradaki atıflar buna çevrildi; ham çıktılar
> `results/jetson_20260906/` altına kondu (yollar yeniden köklendi); denklik betiği
> `scripts/olcum/170_engine_karar_denkligi.py` (paketin 165 numarası `165_trt_pc_provasi.py` ile
> çakışıyordu). Aynı gün uygulanan kararlar: FP32 `navitas_seg_v36_best.engine` yer tutucu girdisi
> defterden çıkarıldı (K4), manifest ve KILAVUZ §4 export komutu `.pt`'den (K5), `test_t143` (K3).
> Ölçüm metni değiştirilmedi.

> Hazırlayan: Claude (Fable 5.1) · İsteyen: kullanıcı (n4vitas)
> Cihaz: `navitas-jetson` · Paket: `~/proje/NAVITAS_JETSON_20260906/navitas`
> Ölçümler 17:05–17:10 arasında bu kartta alındı. **ÖLÇÜLEMEDİ ≠ GEÇTİ.**
> Sayfa sürümü: https://claude.ai/code/artifact/43c0be67-d9e8-4a0b-bcc8-f85b80ea249d

---

## 0. Hüküm

Paket bir **Jetson Nano 4 GB (JetPack 4.6, Ubuntu 18.04, Python 3.6)** için
hazırlanmış; masadaki kart bir **Jetson Orin Nano Developer Kit 4 GB (JetPack 7.2.1,
Ubuntu 24.04, Python 3.12)**. Kurulum belgesi (`JETSON_NANO_KURULUM.md`) ve çevrimdışı
tekerlekler (`wheels/`, cp38) bu karta uymuyor. Buna karşılık kartta gerçek bir Ampere
GPU ve apt ile kurulabilir TensorRT var; Nano belgesindeki "engine derlenemedi, PT/ONNX
ile uçulur" riski burada ortadan kalkıyor.

Uçuş modeli **v36** pakette eksiksiz; `.pt` ve `.onnx` sha256'ları bu kartta hesaplandı
ve kayıt defteriyle eşleşti.

- **Tek gerçek engel RAM:** 3 459 MB'ın 2 705 MB'ı boştayken dolu (Firefox 430 MB,
  gnome-shell 399 MB), swap 0. YOLOv8m + torch + CUDA bağlamı bu hâliyle sığmaz.
- **Kamera ve Pixhawk bağlı değil.** O kapılar bugün ÖLÇÜLEMEDİ kalır.

---

## 1. Kartta ölçülen — donanım künyesi

| kalem | ölçülen |
|---|---|
| Kart | NVIDIA Jetson Orin Nano Developer Kit — taşıyıcı p3768, modül **p3767-0004 (4 GB)** |
| SoC | tegra234 · 6× Cortex-A78 · Ampere GPU · sürücü 595.78, CUDA 13.2 arayüzü |
| L4T / JetPack | **R39.2.1** (2026-08-06) · JetPack **7.2.1** · kernel 6.8.12-tegra |
| İşletim sistemi | Ubuntu **24.04.4** · sistem Python **3.12.3** |
| Depolama | Kök **NVMe** 233 GB, 21 GB dolu · microSD yok, eMMC yok |
| Bellek | 3 459 MB · boşta 2 705 MB kullanımda · **swap 0** |
| Güç kipi | 0 = **10W** (azami) · 1 = 7W_AI · 2 = 7W_CPU |
| Ağ | Ethernet `enP8p1s0` 10.21.8.7/24 · internet var · NVIDIA `r39.2` apt deposu tanımlı |
| Kurulu DEĞİL | cuda-toolkit, tensorrt, cudnn, pip, torch, cv2, ultralytics |
| Kurulabilir (apt) | `nvidia-jetpack 7.2.1-b49` · `cuda-toolkit 13.2.2` · `tensorrt 10.16.2` · `python3-libnvinfer` · `python3-opencv 4.6` · `python3-pip` · `python3-venv` |
| Kamera | `/dev/video*` yok · `nvarguscamerasrc` eklentisi ve `jetson-io` mevcut |
| Seri | `/dev/ttyACM*`, `/dev/ttyUSB*` yok · `ttyTHS1`, `ttyTHS2` (40-pin UART) var |
| Kullanıcı | `n4vitas` (paket `navitas` varsayar; `jetson_baslat.sh` `SUDO_USER`'dan türetir) |
| Ek | Docker 29.1.3 kurulu · varsayılan hedef `graphical.target` |

Kapı komutları ve ham çıktı:

```
$ cat /etc/nv_tegra_release
# R39 (release), REVISION: 2.1, GCID: 46758480, BOARD: generic, EABI: aarch64, DATE: Fri Aug  7 05:54:22 AM UTC 2026
$ cat /proc/device-tree/model
NVIDIA Jetson Orin Nano Developer Kit
$ cat /proc/device-tree/compatible
nvidia,p3768-0000+p3767-0004 nvidia,p3767-0004 nvidia,tegra234
$ lsb_release -d
Description:	Ubuntu 24.04.4 LTS
$ python3 --version
Python 3.12.3
$ free -m
               total        used        free      shared  buff/cache   available
Mem:            3459        2705          88          30         832         753
Swap:              0           0           0
$ nvpmodel -q
NV Power Mode: 10W
$ df -h /
/dev/nvme0n1p1  233G   21G  200G  10% /
```

---

## 2. Paket varsayımı ↔ kart

`OKU_BENI.md` kurulum için `JETSON_NANO_KURULUM.md`'yi işaret ediyor; o belge 3 Eylül
tarihli "Nano üretim modülü, eMMC, üçüncü parti taşıyıcı, microSD yok" beyanına dayanıyor.

| konu | paket varsayımı | kartta ölçülen | sonuç |
|---|---|---|---|
| Modül | Jetson Nano 4 GB (Tegra X1, eMMC) | Orin Nano 4 GB (tegra234, NVMe kök) | 🔴 UYMUYOR |
| JetPack / Ubuntu | 4.6.x / 18.04 | 7.2.1 / 24.04 | 🔴 UYMUYOR |
| Python | Sistem 3.6 → ayrı `venv38` | Sistem 3.12; ultralytics doğrudan kurulur | ⚠ PLAN DEĞİŞİR |
| `wheels/` (51 adet cp38) | Çevrimdışı pip | cp38 tekerlekleri 3.12'de kurulmaz | 🔴 KULLANILAMAZ |
| TensorRT `.engine` | "Bu kartta derlenemedi" | TensorRT 10.16 apt ile geliyor; derleme mümkün | ✅ KAZANIM |
| Güç kipi | MAXN 10 W, 4 çekirdek | 10W azami, 6 çekirdek + GPU | ✅ UYUMLU |
| Swap 4 GB şart | Evet | Evet; şu an sıfır | ⚠ YAPILACAK |
| Kamera köprüsü | Sistem Py3.6 + sistem cv2 (GStreamer) → MJPEG | Aynı ayrım geçerli: sistem `python3-opencv` GStreamer'lı, pip cv2 değil | ✅ TASARIM KORUNUR |
| `JETSON_KILAVUZ.md` (Orin NX) | "Nano'da geçersiz" | Bu karta Nano belgesinden daha yakın (16 GB → 4 GB farkı hariç) | ⚠ ESAS ALINIR |
| Paket kökü | `~/navitas` | `~/proje/NAVITAS_JETSON_20260906/navitas` | ⚠ `NAVITAS_KOK` verilir |
| İnternet | Yok sayıldı | Var; NVIDIA deposu erişilebilir | ✅ KAZANIM |

⚠ `tests/test_faz_b_nano_kurulum.py` yanlış donanım beyanını kilitliyor. Künye repoda
düzeltilmeden o test yeni belgeyle çelişir; bu PC tarafında mimara giden bir D-kaydıdır.

---

## 3. Uçuş modeli — v36, doğrulandı ve pakette

| | |
|---|---|
| Profil | `competition` (`config/model_registry.json`, `default_profile`) |
| Model id | `navitas-seg-v36-512` |
| Dosya | `models/navitas_seg_v36_best.pt` |
| Mimari | YOLOv8m-seg, 27,2 M parametre, çıkarım **512** |
| Sınıflar | `0` traversable (sürülebilir zemin) · `1` blocked (engel) |
| ONNX türevi | `navitas_seg_v36_best_512_fp16.onnx` (opset 17, fp16, statik 512) |
| Yedekler | v35 (arena K3/K4/K6'da daha iyi, gerçek karede beton kanaldan geçiriyor) · v34 (ikinci yedek) |

Bu kartta hesaplanan sha256:

```
ESLESTI  models/navitas_seg_v36_best.pt
         1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911
ESLESTI  jetson_paket/models/navitas_seg_v36_best.pt        (ayni ozet)
ESLESTI  models/navitas_seg_v36_best.onnx
         f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab
ESLESTI  jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx (ayni ozet)
AYNI     config/model_registry.json == jetson_paket/config/model_registry.json
YER TUTUCU  navitas_seg_v36_best.engine / _512_fp16.engine -> DERLENINCE_YAZILIR
            (Jetson'da derlenip `codes/model_registry.py --turev-kaydet` ile yazilir)
```

Modeli değerlendirirken bilinmesi gerekenler:

- **Kural dışı terfi (D-293).** Gerçek karede ROTA 8 ölçüldü, eşik ≥ 10; MASKE_YOK 16
  ölçüldü, eşik ≤ 10. Kullanıcı kararıyla üretime alındı; eşikler değişmedi.
- **Arena ölçümlerinin tamamı sentetik.** Gerçek arena karesi yok; tek gerçek doğrulama
  kümesi kırsal DJI uçuşu 0038 (29 + 82 kare).
- **Eğitim.** Taban v35, 17 epoch, en iyi epoch 2, val mAP50-95(M) 0,155.
- **FPS kapısı.** Uçtan uca **0,61 FPS**, p50 ve p95 ayrı (D-374/376; türetilmiş
  `gerekli_fps_R` 0,41). Hiçbir Jetson'da henüz ölçülmedi.
- **Diğer ağırlıklar uçuş modeli değil.** Kökteki `yolov8*.pt`, `yolo26n.pt` pretrained
  taban; `models/best_ncnn_model` Mayıs tarihli eski yolov8n-seg.

---

## 4. Proje — Jetson zincirde ne yapıyor

**Görev.** 50×50 m moloz arenasında üç güzergâhtan açık olanı ≥ 30 m irtifadan bulmak.
Kamera → v36 segmentasyonu → costmap → A* → `OPEN_ROUTE` / `NO_ROUTE` + waypoint'ler,
UDP ya da 433 MHz SiK ile YKS'ye ve İKA'ya (`CONTRACTS.md` §6.5).

**Jetson'daki süreçler** (`jetson_paket/jetson_baslat.sh`, systemd `Restart=always`):

| birim | ne | MAVLink ucu |
|---|---|---|
| `navitas-cogullayici` | MAVProxy, `/dev/ttyACM0`'ın tek sahibi | üretir 14550/14551/14552 |
| `navitas-rpi-inference` | kamera → v36 → karar yayını + HEARTBEAT | `udp:127.0.0.1:14550` |
| `navitas-iha-inis-yayinci` | Pixhawk kanıtlı `IHA_LANDED` | `udp:127.0.0.1:14551` |
| `navitas-iha-komut-alici` | YKS ARM/PARAŞÜT → `COMMAND_LONG` | `udp:127.0.0.1:14552` |
| `navitas-kamera-koprusu` | CSI nvargus (sistem python) → MJPEG :8080 | — |
| `navitas-seri-hub` | yalnız `KIP=sik`: SiK portunun tek sahibi | — |

**Takvim.** FDR teslimi + Adıyaman provası **21 Eylül 2026**; resmî drone görev test
uçuşu **30 Eylül–3 Ekim 2026** (quadcopter, 20×20 m, ≥ 30 m, ≤ 10 dk, tek atış);
yarışma Ağustos–Eylül 2027 (sabit kanat + mancınık + paraşüt + İKA).

**Site ↔ depo.** navitas.website depodan geride: "Orin NX, 915 MHz" yazıyor; depo
433 MHz SiK ve FDA için quadcopter kullanıyor. Ekip bölümü boş.

---

## 5. Sıradaki adımlar — kapı sırasıyla

| # | adım | kapı | durum |
|---|---|---|---|
| 1 | Root betiği `orin_nano_root_kurulum.sh`: `nvidia-jetpack`, pip/venv, `python3-opencv`; 8 GB swap; dialout/video grupları; `nvpmodel -m 0` | `nvcc`, `dpkg -l tensorrt`, `free -h` swap ≥ 8G | koşuyor |
| 2 | Python 3.12 venv (sistem paketlerini görür): NVIDIA JetPack 7 torch, ultralytics, pymavlink, MAVProxy, onnxruntime | `torch.cuda.is_available()` True · `import tensorrt` | bekliyor |
| 3 | Kayıt defteri kapısı: `rpi_inference.model_kayit_dogrula` v36 için True | `--kayit-dogrulamasiz` YOK | bekliyor |
| 4 | FP16 engine: `yolo export … format=engine imgsz=512 half=True`; `model_registry.py --turev-kaydet` | dosya var + tek kare çıkarım + defter "eslesti" | bekliyor |
| 5 | FPS: `jetson_fps.py` (.pt/.onnx/.engine), p50 ve p95; 10 dk sürekli + tegrastats | ≥ 0,61 FPS her ikisinde; düşerse eşik gevşetilmez | bekliyor |
| 6 | Kamera: IMX477 `jetson-io` overlay, `nvarguscamerasrc` tek kare, ayna testi, köprü | kare var + ayna doğru | ÖLÇÜLEMEDİ (kamera bağlı değil) |
| 7 | Pixhawk: `jetson_baslat.sh --kuru` → `--kapi`, 3 uçta `mavlink_dogrula` | 3/3 GEÇTİ | ÖLÇÜLEMEDİ (Pixhawk bağlı değil) |

---

## 6. Bu rapor için okunanlar

`OKU_BENI.md` · `CLAUDE.md` · `CONTRACTS.md` (§1, §6.5, §7.4) · `config/model_registry.json` ·
`jetson_paket/JETSON_NANO_KURULUM.md` · `JETSON_KILAVUZ.md` · `jetson_paket/{jetson_baslat.sh,
systemd/*, GUN1_KONTROL_LISTESI.md, JETSON_BASLAT.md, models/jetson_derleme_manifest.json,
kod/requirements_nano.txt, kod/kamera_koprusu.py}` · `codes/rpi_inference.py` ·
`codes/model_registry.py` · `scripts/jetson_fps.py` · `results/b4_fps/p_ve_kosu_20260901.json` ·
`FAZ_B_GUN_PLANI.md` · `SAHA_RUNBOOK.md` · `SAHA_HAZIRLIK_PLANI_20260903.md` · `DEVAM.md` ·
`HANDOFF.md` · `KARAR_PAKETI_20260901.md` · `ARCHITECT_PLAN.md` §1/§9 ·
`navitas-derin-analiz-build/00_YONETICI_OZETI.md` · navitas.website

---

## 7. EK — 19:30 güncellemesi: kurulum yapıldı, kapılar koşuldu

| kapı | ölçülen | hüküm |
|---|---|---|
| Root kurulum (JetPack 7.2.1: CUDA 13.2, TensorRT 10.16; 8 GB swap) | nvcc 13.2 · tensorrt 10.16.2 · swap 8,0 GiB | GEÇTİ |
| `~/venv312`: torch 2.11+cu130, ultralytics 8.4.142 | CUDA True, GPU çıkarım 174–237 ms/kare | GEÇTİ |
| Genel kapı madde 14 | 15/15 · şerit 15/15 | GEÇTİ |
| Kayıt defteri | v36 pt/onnx/engine eşleşti, v35 RED | GEÇTİ |
| TensorRT FP16 engine + defter kaydı | 530 s, 57 MB, sha `bb9bd868…0300` | GEÇTİ |
| FPS uçtan uca ≥ 0,61 (p50 ve p95) | pt 1,35 / 1,06 · engine 1,58 / 1,33 | GEÇTİ |
| 10 dk sürekli koşum | ilk↔son dk pt +2,6 %, engine −0,4 %; gpu ≤ 56,3 °C | GEÇTİ |
| Karar denkliği engine↔pt | F1 0 zarar · F2 0,995 · D-303 oransal 3/126 DÜŞTÜ | engine üretime alınmaz, uçuş `.pt` |
| ONNX (onnxruntime-gpu) | sm_87 çekirdeği yok | HATA (yedek yol) |
| Kamera IMX477 · Pixhawk çoğullayıcı | donanım bağlı değil | ÖLÇÜLEMEDİ |
| Tam süit | 2121 test; kalan sorunlar ortam/PC işi | bkz. D-431 |

Ayrıntı: `JETSON_KURULUM_SURECI_20260906.md` (süreç), `navitas/jetson_paket/JETSON_ORIN_NANO_KURULUM.md` (tutanak), `navitas/REVIEW_LOG.md` **D-431**.
