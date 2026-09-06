# JETSON ORIN NANO 4GB (JetPack 7.2.1) — KURULUM VE GÜN-1 TUTANAĞI · 6 Eylül 2026

> **7 Eylül 2026 — depoya taşıma notu (G0a, REVIEW_LOG D-431).** Bu belge 6 Eylül Jetson oturumunda
> yazıldı ve `GELISTIRICIYE_20260906` paketiyle geldi. Taşınırken: paketin **D-431** numarası master'daki
> D-431/429/430 ile çakıştığı için kayıt **D-431** oldu ve buradaki atıflar buna çevrildi; ham çıktılar
> `results/jetson_20260906/` altına kondu (yollar yeniden köklendi); denklik betiği
> `scripts/olcum/170_engine_karar_denkligi.py` (paketin 165 numarası `165_trt_pc_provasi.py` ile
> çakışıyordu). Aynı gün uygulanan kararlar: FP32 `navitas_seg_v36_best.engine` yer tutucu girdisi
> defterden çıkarıldı (K4), manifest ve KILAVUZ §4 export komutu `.pt`'den (K5), `test_t143` (K3).
> Ölçüm metni değiştirilmedi.

> **NEDEN:** `OKU_BENI.md` ve `JETSON_NANO_KURULUM.md` kartı **Jetson Nano 4 GB (JetPack 4.6,
> Ubuntu 18.04, Python 3.6)** varsaydı. 6 Eylül'de kart açılıp **ölçüldü**: bu bir
> **Jetson Orin Nano Developer Kit 4 GB (p3768 taşıyıcı + p3767-0004 modül), L4T R39.2.1 =
> JetPack 7.2.1, Ubuntu 24.04, Python 3.12, kök NVMe**. Nano belgesinin venv38, cp38
> `wheels/`, eMMC flash, Python 3.6 köprü kısıtları bu kartta **GEÇERSİZDİR**. Orin NX
> kılavuzu (`JETSON_KILAVUZ.md`) bu karta daha yakındır; farklar aşağıda.
>
> Bu belge **ölçümle** yazıldı. Her kapının ham çıktısı `results/jetson_20260906/jetson_log_20260906/` ve
> `results/jetson_20260906/jetson_fps_20260906_orin_nano/` altındadır. **ÖLÇÜLEMEDİ ≠ GEÇTİ.**
>
> ⚠ **Repodaki donanım künyesi düzeltilmelidir:** `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2,
> `JETSON_NANO_KURULUM.md` §0/§1, `FAZ_B_GUN_PLANI.md` §0, `OKU_BENI.md` §0 ve
> `tests/test_faz_b_nano_kurulum.py` kilidi "Nano 4GB eMMC" beyanını taşır. Bu PC
> tarafında mimarın işidir (D-kaydı: aşağıda §9).

---

## 0. Kartta ölçülen künye

```
$ cat /etc/nv_tegra_release
# R39 (release), REVISION: 2.1, GCID: 46758480, BOARD: generic, EABI: aarch64, DATE: Fri Aug  7 05:54:22 AM UTC 2026
$ cat /proc/device-tree/model            -> NVIDIA Jetson Orin Nano Developer Kit
$ cat /proc/device-tree/compatible       -> nvidia,p3768-0000+p3767-0004 nvidia,p3767-0004 nvidia,tegra234
$ lsb_release -d                         -> Ubuntu 24.04.4 LTS
$ python3 --version                      -> Python 3.12.3
$ nvidia-smi | head -3                   -> Driver 595.78, CUDA 13.2
$ df -h /                                -> /dev/nvme0n1p1 233G (21G dolu)
$ free -m                                -> Mem 3459 (bosta 2705 kullanimda), Swap 0   [kurulum oncesi]
$ nvpmodel -q                            -> NV Power Mode: 10W   (kipler: 0=10W 1=7W_AI 2=7W_CPU)
$ ls /dev/video* /dev/ttyACM*            -> YOK (kamera ve Pixhawk bagli degil)
$ whoami                                 -> n4vitas   (paket `navitas` varsayar; jetson_baslat.sh SUDO_USER'dan turetir)
```

| konu | `JETSON_NANO_KURULUM.md` | **Orin Nano'da böyle** |
|---|---|---|
| Sistem imajı | eMMC'ye SDK Manager ile JetPack 4.6 | **Zaten kurulu**: JetPack 7.2.1, NVMe kök. Flash yok. |
| Python | 3.6 → `~/venv38` + cp38 `wheels/` | **3.12** → `~/venv312` (`--system-site-packages`), paketler **çevrimiçi** pip. `wheels/` kullanılmaz. |
| torch | PyPI CPU cp38 | `https://pypi.jetson-ai-lab.io/sbsa/cu130` → **torch 2.11.0+cu130**, CUDA **çalışıyor** (uyarı: tekerlek sm_87 için derlenmemiş, sm_80 SASS ile koşuyor; conv/sigmoid/nms/interp/predict ölçüldü, hatasız) |
| TensorRT | "derlenemedi" | **apt `nvidia-jetpack`** → TensorRT 10.16.2 + `python3-libnvinfer`; `.engine` **derlendi** (§4) |
| Kamera köprüsü | sistem Python 3.6 + cv2 4.1 | sistem **Python 3.12 + `python3-opencv` 4.6 (GStreamer'lı)** — aynı ayrım, aynı betik; dosya kaynağıyla **ölçüldü** (§6) |
| Güç | 5 V/4 A + J48 | DevKit barrel jack; **J48 yok** |
| Swap | 4 GB şart | **8 GB** açıldı (`/swapfile`, NVMe) |
| `nvpmodel -m 0` | MAXN 10 W (4 çekirdek) | 10W (6 çekirdek + GPU) — azami kip bu |
| MAVProxy | venv38 + symlink | `~/venv312/bin/mavproxy.py` → `~/.local/bin/mavproxy.py` symlink (birim PATH'i orayı arar) |
| Paket kökü | `~/navitas` | `~/navitas` → `~/proje/NAVITAS_JETSON_20260906/navitas` **symlink** |

---

## 1. Root kurulum — `orin_nano_root_kurulum.sh` (paket kökünde, `sudo bash`)

`apt-get install nvidia-jetpack python3-pip python3-venv python3-dev python3-opencv python3-numpy
gstreamer1.0-tools gstreamer1.0-plugins-good git` (136 paket) · `/swapfile` 8G + fstab ·
`usermod -aG dialout,video` · `nvpmodel -m 0` · `jetson_clocks`.

**Kapı 1 (ölçüldü, `orin_nano_root_kurulum.log`):**
```
-- nvcc:      Build cuda_13.2.r13.2/compiler.37953736_0
-- tensorrt:  python3-libnvinfer 10.16.2.10-1+cuda13.2 · tensorrt 10.16.2.10-1+cuda13.2
-- python3:   Python 3.12.3 · pip 24.0
-- cv2:       4.6.0 True        (sistem cv2, GStreamer VAR)
-- swap:      Swap: 8.0Gi
-- nvpmodel:  NV Power Mode: 10W
```
⚠ dialout/video grup üyeliği **yeniden oturum açınca** etkin olur.

## 2. Kullanıcı alanı — `orin_nano_venv_kurulum.sh` (root istemez)

`python3 -m venv --system-site-packages ~/venv312` · torch 2.11.0+cu130 + torchvision 0.25.0
(jetson-ai-lab sbsa/cu130) · `ultralytics numpy<2 pyserial pymavlink MAVProxy lxml future onnx onnxslim` ·
`onnxruntime-gpu` (PyPI 1.29.0 — CUDA sağlayıcısı bu kartta **çalışmıyor**, §5).

**Kapı 2 (ölçüldü, `orin_nano_venv_kurulum.log`):**
```
python 3.12.3 · numpy 1.26.4 · cv2 4.11.0 (venv, pip) GStreamer True
torch 2.11.0+cu130 | cuda True | Orin · gpu matmul True
tensorrt 10.16.2.10 · ultralytics 8.4.142 · pymavlink 2.4.49
onnxruntime 1.29.0 ['CUDAExecutionProvider', 'CPUExecutionProvider']
```
Etkinleştir: `source ~/venv312/bin/activate` — birimlerde `PYTHON3=/home/n4vitas/venv312/bin/python`.

## 3. Genel kapı + kayıt defteri (madde 14, T73)

```
$ python -B codes/test_rota_sentetik.py
GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15
$ model_kayit_dogrula(...)
GECTI  models/navitas_seg_v36_best.pt                          -> eslesti
GECTI  jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx  -> turev_eslesti
RED    jetson_paket/models/navitas_seg_v35_best.pt             -> ESLESMIYOR   (dogru davranis)
```

## 4. TensorRT `.engine` — T16 / T109 (Gün-1 §3)

`yolo export` **ONNX'ten engine üretmez** (manifestteki `jetson_komutlari` satırı PC'de sınanmamıştı);
`.pt`'den üretildi, paket dışı bir kopya dizininde:

```
$ yolo export model=navitas_seg_v36_best.pt format=engine imgsz=512 half=True device=0 batch=1 workspace=2
TensorRT: input "images" (1,3,512,512) FLOAT · output0 (1,38,5376) · output1 (1,32,128,128)
Export complete (530.2s)   -> navitas_seg_v36_best.engine  57 283 989 bayt
```
Dosya `jetson_paket/models/navitas_seg_v36_best_512_fp16.engine` (+ `models/` aynası) olarak kondu ve deftere yazıldı:
```
$ python codes/model_registry.py --turev-kaydet jetson_paket/models/navitas_seg_v36_best_512_fp16.engine --kaynak-pt models/navitas_seg_v36_best.pt
{"turev": "navitas_seg_v36_best_512_fp16.engine", "eski_sha256": "DERLENINCE_YAZILIR",
 "yeni_sha256": "bb9bd8685a98a91947332c5b19b43f6c5631fb9c8ebcf611a9f75f6c05950300", "profil": "competition"}
ayna AYNI (jetson_paket/config/model_registry.json)
GECTI  jetson_paket/models/navitas_seg_v36_best_512_fp16.engine -> turev_eslesti
```
⚠ Defterdeki **`navitas_seg_v36_best.engine`** girdisi hâlâ yer tutucudur (FP32 engine derlenmedi, gerekmiyor).
Mühürden önce (FAZ_B_GUN_PLANI §3) bu girdi **defterden çıkarılmalı** ya da derlenmeli — mimar kararı.
⚠ Engine **bu karta özeldir** (Orin sm_87, TensorRT 10.16); başka Jetson'da geçersizdir.

## 5. FPS — T17 (Gün-1 §5) · eşik **0,61 FPS p50 ve p95** (D-374/376)

`scripts/jetson_fps.py --cihaz 0` · girdi `data/raw_frames` · 120 örnek · mpp=None · `jetson_clocks` açık.
Ham: `results/jetson_20260906/jetson_fps_20260906_orin_nano/{ozet.json,rapor.md,tegrastats.log}`.

| model | okuma | çıkarım p50/p95 | maske p50/p95 | katman A p50/p95 | **toplam p50/p95 ms** | **FPS p50 / p95** | kapı |
|---|---:|---:|---:|---:|---:|---:|---|
| PyTorch .pt (GPU) | 14 | 188 / 303 | 312 / 421 | 210 / 329 | **739 / 942** | **1,35 / 1,06** | GEÇTİ |
| TensorRT FP16 .engine | 8 | 87 / 106 | 311 / 418 | 208 / 329 | **635 / 751** | **1,58 / 1,33** | GEÇTİ |
| ONNX (onnxruntime-gpu) | — | — | — | — | — | — | **HATA** |

- ONNX kolu: `cudaErrorNoKernelImageForDevice` — PyPI `onnxruntime-gpu` 1.29 CUDA sağlayıcısı sm_87 için derlenmemiş. ONNX yedek yoldur; uçuş `.engine` ya da `.pt` ile. CPU `onnxruntime` ile ölçülmedi.
- 🔴 **Darboğaz model değil:** çıkarım engine'de 87 ms; `get_masks` (~311 ms) + costmap Katman A (~208 ms) toplamın **%82'si** ve CPU'da koşuyor. Engine, toplamda yalnız 104 ms kazandırıyor. Kapı geçiyor; daha yüksek FPS istenirse iş **kod tarafında** (mimar, dondurma sonrası).
- Rota durumları iki kolda **aynı** (mpp=None): BELIRSIZ_COKLU 101 · ACIK 2 · KAPALI_DAR 17.
- Termal (3,5 dk): gpu 54,2 → 55,8 °C, RAM tepe 3238/3459 MB (+swap).

**10 dk sürekli koşum (Gün-1 §6, `results/jetson_20260906/jetson_fps_20260906_orin_nano_10dk/`, 900 örnek/model):**

| model | süre | toplam p50/p95 ms | ilk 1 dk FPS | son 1 dk FPS | değişim | termal |
|---|---:|---:|---:|---:|---:|---|
| PyTorch .pt | 11,4 dk | 770 / 922 | 1,277 | 1,310 | +2,6 % | OK (< %15) |
| TensorRT FP16 | 9,5 dk | 649 / 765 | 1,534 | 1,527 | −0,4 % | OK (< %15) |

gpu 54,2–56,3 °C · cpu ≤ 57,5 °C · VDD_IN 7,7–9,4 W · RAM tepe 3179 MB · throttle satırı 0. Rota durumları iki kolda aynı (770/13/117).

## 6. Kamera — H3 / Gün-1 §7

CSI'da kamera yok: `nvarguscamerasrc` → `No cameras available` (beklenen). Köprü **dosya kaynağıyla** sınandı:
```
$ /usr/bin/python3 scripts/kamera_koprusu.py --kaynak "WhatsApp Video 2026-07-30 at 11.44.03.mp4" --port 8081 --fps 5
/durum  -> {"kaynak_acik": true, "kare_sayaci": 23, "fps": 4.99, "boyut": [1024, 576], ...}
/kare.jpg -> HTTP 200, 107 004 bayt
```
IMX477 takılınca: `sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → reboot → `ls /dev/video0` →
`gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! fakesink` → **AYNA TESTİ** (D-349). **ÖLÇÜLEMEDİ.**

## 7. `jetson_baslat.sh --kuru` (D-404)

```
PATH=$HOME/.local/bin:$PATH KIP=udp YKS_IP=<YKS> IKA_IP=<IKA> FOV=<derece> KAMERA=http://127.0.0.1:8080/video \
  NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python bash jetson_paket/jetson_baslat.sh --kuru
[VAR] mavproxy.py · kamera_koprusu.py · rpi_inference.py · iha_inis_yayinci.py · iha_komut_alici.py
[VAR] kullanici n4vitas · yorumlayici ~/venv312/bin/python · kopru yorumlayicisi /usr/bin/python3
[YOK] Pixhawk seri /dev/ttyACM0            <- kablo takili degil (KIP=sik'te ayrica /dev/ttyUSB0)
KURU SONUC: eksik ([YOK]: 1) — cikis 3
```
Pixhawk takılınca `[YOK]` kalkar; sonra `sudo -E ... jetson_baslat.sh --kapi` (3 uçta `mavlink_dogrula`). **ÖLÇÜLEMEDİ.**

## 8. Karar denkliği engine ↔ pt (Gün-1 §4, D-375 yöntemi) ve tam süit

Betik: `scripts/olcum/170_engine_karar_denkligi.py` (164 ile aynı halka; kol B = `.engine`).
S = `data/arena_kompozit_v2` (126 kare, GT'li — **T66 kabul kümesi değil**, o O:/ diskinde), R = dji_20260822 ≥ 30 m katmanı (633 kare).
⚠ Sapma (kayıtlı): 4K R kareleri üzerinde costmap CPU'da kare başına dakikalar sürdü (46 dk'da ~16 kare); koşum
durduruldu (`engine_karar_denkligi_4K_yarim.log`) ve R kareleri **1280 genişliğe küçültülerek** (`--r-genislik 1280`,
köprünün üretimde verdiği genişlik; mpp yeni genişlikten türetilir) yeniden koşuldu. S kareleri değişmedi.

**Sonuç (`engine_karar_denkligi.json`, 18:55–19:04):**

| kapı | ölçülen | eşik | hüküm |
|---|---|---|---|
| F1 — S'te FP32 doğruyken engine yanlış şerit | **0** kare | 0 tolerans | **GEÇTİ** |
| F2 — R ≥ 30 m katmanı karar uyuşması | **0,9953** (630/633) | ≥ 0,98 | **GEÇTİ** |
| D-303 oransal — S uyuşmazlık | **3/126** (%2,38) | ≤ 5/260 (%1,92) | **DÜŞTÜ** |
| F3 (bilgi) | None→şerit 1 · şerit→None 2 · şerit→şerit 3 | — | — |
| bit-eş maske oranı | S %0 · R %3,3 | — | — |

Uyuşmazlık kareleri: S'te 3 karede **pt de yanlıştı** (GT 3/1/1; pt 2/3/None; engine 1/2/2) — F1 bu yüzden 0.
R'de 3 kare: pt 3→engine 1; pt 1→engine None (GORUS_HATTI_KOPUK) ×2. S'te iki kolun GT doğruluğu eşit: **52/126**
(bu, modelin bu kompozit kümedeki başarımıdır, denklik sorunu değil).

**Hüküm (FAZ_B_GUN_PLANI §2 11:15 kuralı):** D-303 oransal eşiği aşıldı → **engine ÜRETİME ALINMAZ, uçuş `.pt` ile**
(FPS kapısını `.pt` de geçiyor: p95 1,06). Defterin `path`'i zaten `.pt`; engine yalnız açık `--model` ile yüklenir.
⚠ Bu S kümesi T66 kabul kümesi değildir; D-303 eşiği o küme için yazıldı. Nihai karar mimarındır (PC'de T66 ile tekrar).

Tam süit: `python -B -m unittest discover -s tests -q` → `results/jetson_20260906/jetson_log_20260906/unittest_tam_suit.log`.

## 9. Mimara giden kalemler (D-kaydı için)

1. Donanım künyesi Nano değil **Orin Nano 4GB / JetPack 7.2.1** — yukarıdaki belgeler ve `test_faz_b_nano_kurulum.py` düzeltilmeli.
2. `jetson_derleme_manifest.json` `jetson_komutlari` ONNX'ten engine diyor; ultralytics bunu desteklemiyor — `.pt`'den derlenir.
3. Defterde `navitas_seg_v36_best.engine` yer tutucu kaldı; mühürden önce karar.
4. FPS darboğazı CPU post-process (maske + costmap ≈ 520 ms); model hızlandırma FPS'i artırmaz.
5. `onnxruntime-gpu` PyPI tekerleği sm_87'de çalışmıyor; ONNX yedek yolu bu kartta CPU'da kalır (ölçülmedi).
6. `wheels/` (246 MB, cp38) bu kartta anlamsız; paketten çıkarılabilir (madde 18: kullanıcı kararı).
