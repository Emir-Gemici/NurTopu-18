# 10 · JETSON VE ÜRETİM PAKETİ — kart, paket, tek komutla açılış, engine, FPS (6 ve 9 Eylül 2026)

> Kaynaklar: `jetson_paket/JETSON_ORIN_NANO_KURULUM.md` (kapı kapı tutanak) · `results/jetson_20260906/` (ham kanıt; `JETSON_KURULUM_SURECI_20260906.md`,
> `JETSON_KESIF_RAPORU_20260906.md`, `ORTAM_KUNYESI.txt`, FPS ve denklik JSON'ları) · `REVIEW_LOG.md` D-431 · `CONTRACTS.md` §7.4–§7.5 ·
> `jetson_paket/JETSON_BASLAT.md`, `jetson_baslat.sh`, `systemd/` · `scripts/jetson_fps.py` · `scripts/olcum/170_engine_karar_denkligi.py` ·
> `JETSON_OTURUM_DURUMU_20260909.md` (9 Eylül geri aktarım). Bu dosyanın yazarı 6 ve 9 Eylül Jetson oturumlarını kendisi yürüttü.

---

## Seviye 1 — Bir cümle ve büyük resim

Jetson, İHA'nın üstündeki **görev bilgisayarıdır**: kamerayı okur, modeli koşturur, kararı üretir ve telsize yazar; Pixhawk'tan
irtifa ve iniş kanıtı alır; YKS'den paraşüt/ARM komutlarını Pixhawk'a aktarır. Paket "Jetson **Nano** 4 GB / JetPack 4.6 / Python 3.6"
için hazırlanmıştı; **6 Eylül'de kutudan Jetson Orin Nano Developer Kit 4 GB / JetPack 7.2.1 / Ubuntu 24.04 / Python 3.12 çıktı**
(D-431). Kurulum bu karta göre yapıldı; genel kapı, defter, FPS ve 10 dakika sürekli koşum GEÇTİ; TensorRT engine derlendi ama
karar denkliği eşiğini geçemediği için **uçuş PyTorch `.pt` ile**. Kamera ve Pixhawk bağlı olmadığı için o kapılar **ÖLÇÜLEMEDİ**.

## Seviye 2 — Nasıl çalışır

### 2.1 Kartın kimliği (ölçüldü; `ORTAM_KUNYESI.txt`)
| kalem | değer |
|---|---|
| Kart | NVIDIA Jetson Orin Nano Developer Kit, modül p3767-0004 (4 GB), taşıyıcı p3768 |
| Yazılım | L4T R39.2.1 = JetPack **7.2.1** · Ubuntu 24.04.4 · Python 3.12.3 · CUDA 13.2 · TensorRT 10.16.2 |
| Depolama | NVMe kök 233 GB (microSD yok, eMMC yok) |
| Bellek | 3 459 MB RAM (masaüstü + Firefox ~2,7 GB tutuyordu) · swap 0 → **8 GB `/swapfile`** eklendi |
| Güç kipi | 0 = 10 W (azami), `jetson_clocks` |
| Python ortamı | `~/venv312` (sistem paketlerini görür): torch 2.11.0+cu130, torchvision 0.25, ultralytics 8.4.142, pymavlink 2.4.49, MAVProxy, onnxruntime-gpu 1.29 |
| Kamera / seri | `/dev/video*` yok (IMX477 takılı değil); `/dev/ttyACM*`, `/dev/ttyUSB*` yok (Pixhawk, SiK takılı değil); `ttyTHS1/2` 40-pin UART var |

DDR'de planlanan Orin **NX** 16 GB idi; 3 Eylül beyanı "Nano 4GB eMMC + üçüncü parti taşıyıcı" idi; gerçek kart Orin Nano DevKit.
Bu, "kutusu açılmamış donanım hakkında varsayım" örüntüsünün **dördüncü** tekrarıydı (D-413 microSD, D-424 PX4, D-426 künye, D-431
kart) ve kural doğurdu: **kutu açılır açılmaz ilk komut künyeyi ölçen komuttur** (`/proc/device-tree/model`), belge ondan sonra yazılır.

### 2.2 Paket: `jetson_paket/` ve ayna sözleşmesi
`scripts/jetson_paket_hazirla.py` depodaki kanonik dosyaları `jetson_paket/` altına **bayt-eş** kopyalar (KOPYALAR listesi, bugün 21
dosya: `kod/` altında `rpi_inference.py`, `karar_sozlesmesi.py`, `costmap_path_finder.py`, `model_registry.py`, `sinif_semasi.py`,
`protocol.py`, `link.py`, `iha_sender.py`, `iha_inis_yayinci.py`, `inis_kaniti.py`, `iha_komut_alici.py`, `seri_hub.py`, `kamera_koprusu.py`,
`mavlink_dogrula.py`, `jetson_fps.py`, `kamera_dogrula.py`; `config/model_registry.json`; `systemd/*.service`; `jetson_baslat.sh`;
belgeler). Nöbetçi: `tests/test_t202_jetson_paket_butunlugu.py`, `test_jetson_comms_paketi.py`. Modeller: `jetson_paket/models/`
(v36 `.pt`, `_512_fp16.onnx`, engine; eski sürümler yedek). Manifest `jetson_derleme_manifest.json` paket içeriğinin sha'larını taşır.

### 2.3 Tek komutla açılış: `jetson_baslat.sh` ve systemd (D-404, Faz B Görev C)
Altı systemd birimi (`Restart=always`, `RestartSec=2`): `navitas-cogullayici` (MAVLink çoğullayıcı: MAVProxy `--out udp:127.0.0.1:1455N`),
`navitas-kamera-koprusu` (sistem Python + OpenCV/GStreamer → MJPEG HTTP `:8080/video`, `/kare.jpg`, `/durum`), `navitas-rpi-inference`
(`--ekransiz`, `KAMERA=http://127.0.0.1:8080/video`), `navitas-iha-inis-yayinci`, `navitas-iha-komut-alici`, `navitas-seri-hub` (yalnız SiK kipi).
Kipler: `--kur` (birimleri yaz, enable, restart), `--kapi` (üç uçta `mavlink_dogrula` **aynı anda** GEÇTİ ister), `--kuru` (hiçbir şey
başlatmaz, `[VAR]/[YOK]` listesi; bir `[YOK]` → çıkış 3), `--durum`, `--dogrudan`. Ortam değişkenleri: `KIP=udp|sik`, `YKS_IP`, `IKA_IP`,
`FOV` (kamera yatay görüş açısı **beyan edilir, tahmin edilmez**), `KAMERA`, `NAVITAS_KOK`, `PYTHON3`, `PIXHAWK_SERI`.
Kuru koşu 6 ve 9 Eylül'de: 12 `[VAR]`, tek `[YOK]` `/dev/ttyACM0` (Pixhawk bağlı değil) → çıkış 3. Bu **beklenen** sonuçtur.

### 2.4 Neden çoğullayıcı ve hub? (`CONTRACTS.md` §7.4–7.5)
Seri port **tek sahiplidir**. Pixhawk'ı üç süreç istiyordu (irtifa okuyucu, iniş kanıtı, komut alıcı) → yalnız çoğullayıcı açar,
tüketiciler UDP 14550/14551/14552. SiK kipinde `/dev/ttyUSB0`'ı da üç NAVITAS süreci istiyordu → `comms/seri_hub.py` portu açar,
tüketiciler `127.0.0.1:5100`'e yazar, hub çerçeveleri tüm tüketicilere yayınlar (datagram = çerçeve). Hiçbir üretim süreci
`--mavlink /dev/tty*` ile doğrudan açılmaz (kod kilidi, `--seri-pixhawk-bilerek` ile aşılır).

### 2.5 Kamera köprüsü neden ayrı süreçte, sistem Python'unda?
JetPack'in OpenCV'si GStreamer'lı ve CSI (`nvarguscamerasrc`) okuyabiliyor; venv'deki `opencv-python` okuyamaz. Bu yüzden köprü
**sistem `/usr/bin/python3` + `python3-opencv 4.6`** ile koşar, `rpi_inference` `~/venv312`'de HTTP'den kare alır. 6 Eylül'de dosya
kaynağıyla GEÇTİ (`/durum kaynak_acik=true`, 5 fps, `/kare.jpg` HTTP 200); CSI `No cameras available` (kamera yok). IMX477 takılınca:
`sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → reboot → `gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! fakesink` → **ayna
testi** (D-349: kadraja SOL kenardan nesne sokulur, ekranda solda görünmeli).

### 2.6 Model dosyaları: `.pt`, ONNX, TensorRT engine
- `.pt` (PyTorch): üretim; defterde sha `1d1caca6…6911`. Jetson'da GPU (`torch.cuda.is_available()` True, "Orin").
- ONNX `_512_fp16.onnx` (sha `f4c9f5fe…`): PC'de üretildi; Jetson'da onnxruntime-gpu 1.29 (PyPI) sm_87 çekirdeği taşımıyor →
  `cudaErrorNoKernelImageForDevice`; ONNX yolu bu kartta CPU'da kalır (ölçülmedi). "ONNX ile uçulur" seçeneği bu kart için doğrulanmamış.
- Engine `navitas_seg_v36_best_512_fp16.engine` (57 283 989 B, sha `bb9bd868…0300`): **bu karta özel** (sm_87, TRT 10.16.2), depoya girmez
  (`.gitignore *.engine`), Jetson'da derlenir: `yolo export model=navitas_seg_v36_best.pt format=engine imgsz=512 half=True device=0
  batch=1 workspace=2` (530 s). Ultralytics ONNX'ten engine **üretmez**; eski manifestteki komut yanlıştı (K5, düzeltildi).
  Defter: `model_registry.py --turev-kaydet` → sha yazılır; `model_kayit_dogrula` → `turev_eslesti`. Model sürümü değişirse engine
  **yeniden derlenir** (soya bağlı; eski engine RED olur).

## Seviye 3 — Ölçümler

### 3.1 FPS kapısı T17 (`scripts/jetson_fps.py`, 120 örnek, mpp=None, `data/raw_frames`; eşik 0,61 FPS p50 **ve** p95)
| model | çıkarım p50/p95 | maske | costmap A | toplam p50/p95 | **FPS p50 / p95** | kapı |
|---|---:|---:|---:|---:|---:|---|
| PyTorch GPU | 188 / 303 ms | 312 | 210 | 739 / 942 ms | **1,35 / 1,06** | GEÇTİ |
| TensorRT FP16 | 87 / 106 ms | 311 | 208 | 635 / 751 ms | **1,58 / 1,33** | GEÇTİ |
| ONNX | — | — | — | — | — | HATA (sm_87) |

🔴 **Darboğaz model değil:** `get_masks` ~311 ms + costmap Katman A ~208 ms ≈ 520 ms, toplamın **%82'si**, CPU'da. Engine çıkarımı
100 ms hızlandırıyor ama toplamda 104 ms kazandırıyor. FPS artışı istenirse iş **post-process**te (K6, mimar; dondurma sonrası).
Eşik 0,61 nereden: `1/(5·p)`, `p` = karede geçerli rota yayınlama olasılığı; en kötü gerçek uçuş p=0,3261 → 0,613 (D-376 sızıntısız).

### 3.2 10 dakika sürekli koşum (GUN1 §6; 900 örnek/model)
pt 11,4 dk: p50/p95 770/922 ms, ilk↔son dk FPS +2,6 % · engine 9,5 dk: 649/765 ms, −0,4 % · gpu ≤ 56,3 °C, cpu ≤ 57,5 °C, VDD_IN ≤ 9,4 W,
RAM tepe 3179 MB, throttle 0 → **termal bayrak yok** (eşik: düşüş > %15).

### 3.3 Engine ↔ pt karar denkliği (D-375 yöntemi; `170_engine_karar_denkligi.py`)
S = `data/arena_kompozit_v2` (126 GT'li kare), R = DJI 20260822 ≥ 30 m katmanı (633 kare, 4K → 1280'e küçültülerek; 4K'da costmap
CPU'da dakikalar sürüyordu, 46 dk'da 16 kare).
| kapı | ölçülen | eşik | hüküm |
|---|---|---|---|
| F1 zarar yönü (pt doğru, engine yanlış şerit) | 0 | 0 | GEÇTİ |
| F2 uyuşma (R) | 0,9953 | ≥ 0,98 | GEÇTİ |
| D-303 oransal (S) | 3/126 = %2,38 | ≤ 5/260 = %1,92 | **DÜŞTÜ** |
3 uyuşmazlıkta pt de yanlıştı; iki kol S'te 52/126 eşit doğrulukta. Hüküm: **engine üretime alınmaz, uçuş `.pt` ile** (plan §2 kuralı).
⚠ S kümesi T66 kabul kümesi **değil**; nihai karar T66 ile (T66 hâlâ PC'de; K2 açık). Defterin `path`'i zaten `.pt`.

### 3.4 Tam süit Jetson'da
6 Eyl: Ran 2121 · F5 E30 S8 · 9 Eyl (geri aktarım sonrası): Ran 2204 · F4 E28 S20. Kırmızıların tamamı **ortam**: 18 `O:/…python.exe`
Windows yolu (`test_p4_runbook`, `test_p8_sim_katmani`), 5 kabul kümesi `O:/…t66` yolu (registry'de çıplak PC yolu), 2 kardeş depo
`ayarlar.py`, 1 `/` altına tmp, 1 pakette olmayan `dataset/test29_v3.yaml`, 1 `.git` yok, 2 Python 3.12 davranışı, 1 K9 kuru koşu
(gerçek makinede sahte eksik üretemiyor), 1 zamanlama. Liste: `results/jetson_20260906/K10_LISTE.md`. Kod hatası **yok**.

### 3.5 6–9 Eylül olay dizisi
6 Eyl 17:05 keşif (kart Orin çıktı) → 17:20 root kurulum (`orin_nano_root_kurulum.sh`: nvidia-jetpack 136 paket, swap, gruplar, güç) →
17:33 venv (`orin_nano_venv_kurulum.sh`) → 17:38 genel kapı 15/15, defter, `--kuru` → 17:43 engine (530 s) + defter → 17:53 FPS → 17:58
tam süit → 18:00–19:04 denklik (4K yarım, 1280 tekrar) → 19:06–19:27 10 dk koşum → 19:50 devir klasörü `GELISTIRICIYE_20260906` USB'ye.
7 Eyl gece PC: mimar D-431 ile master'a işledi (K3/K4/K5, K1 bantları, K10 listesi). 9 Eyl: depoya `gh` ile giriş, 114 dosya Jetson'a
geri aktarıldı, kapılar yeniden koşuldu, durum notu `JETSON_OTURUM_DURUMU_20260909.md` dal `jetson/oturum-20260909`.

### 3.6 Açık kalanlar (Jetson tarafı)
IMX477 CSI + ayna testi · Pixhawk `--kapi` (3 uçta `mavlink_dogrula`) · SiK `KIP=sik` · K2 T66 kümesiyle nihai engine kararı · Gün-1 §4
doğruluk kapısı (`test_goruntuleri` engine ↔ **PC v36 referans kararı** — referans dosyası hiç üretilmedi) · K10 süit yolları ·
`wheels/` (246 MB cp38) silme kararı Halil'in · `JETSON_KILAVUZ.md` başlığı hâlâ "Orin NX".

---

## Jüriye 30 saniyede

> "Görev bilgisayarı Jetson Orin Nano 4 GB. Üstünde PyTorch ile v36 modeli GPU'da koşuyor; uçtan uca kare hızı 1,35 FPS medyan,
> 1,06 FPS p95; gereken alt sınırımız 0,61. On dakikalık sürekli koşumda hız düşmedi, sıcaklık 56 derecenin altında kaldı.
> TensorRT engine'i derledik, daha hızlı, ama karar denkliği eşiğimizi geçemediği için üretime almadık: aynı görüntüde farklı
> şerit söyleme riskini hıza tercih etmeyiz. Darboğaz sinir ağı değil, maske ve costmap işlemleri; o yüzden model hızlandırmak
> FPS'i artırmaz. Kamera ve Pixhawk hattı kartta henüz ölçülmedi; bunu 'ölçülemedi' olarak yazıyoruz."

## Kendini sına

1. Kart ne sanılıyordu, ne çıktı; hangi kural doğdu?
2. Uçuş `.pt` ile mi engine ile mi, neden? Üç kapıyı ve sayıları söyle.
3. FPS eşiği 0,61 nereden türetildi?
4. Darboğaz nerede; engine toplamda ne kazandırıyor?
5. Neden kamera köprüsü sistem Python'unda, `rpi_inference` venv'de?
6. Seri port için çoğullayıcı ve hub neden gerekli? Portlar?
7. `jetson_baslat.sh --kuru` 6 ve 9 Eylül'de ne dedi; bu ne anlama geliyor?
8. Engine neden depoya girmez; model değişirse ne olur?
9. Jetson'da süitteki 32 kırmızı neden; kod hatası var mı?
10. Ayna testi nedir, ne zaman yapılır?

<details><summary>Cevaplar</summary>

1. Nano 4 GB / JetPack 4.6 / Py3.6 sanıldı; Orin Nano DevKit 4 GB / JetPack 7.2.1 / Py3.12 çıktı; "kutu açılınca ilk komut künyeyi ölçer, belge sonra yazılır". 2. `.pt`; F1 zarar 0 GEÇTİ, F2 uyuşma 0,9953 GEÇTİ, D-303 oransal 3/126 (%2,38) > %1,92 DÜŞTÜ → engine üretime alınmaz. 3. `1/(5·p)`: tazelik 5 s, en kötü gerçek uçuşta geçerli rota olasılığı 0,326 → 0,61. 4. `get_masks` + costmap CPU'da ~520 ms (%82); engine toplamda 104 ms. 5. CSI/GStreamer'lı OpenCV yalnız sistem paketinde; venv'deki torch/ultralytics Python 3.12'de. 6. Seri port tek sahipli; Pixhawk'ı üç süreç, SiK'i üç süreç istiyor; MAVLink UDP 14550/14551/14552, hub 5100/5007. 7. 12 [VAR], tek [YOK] `/dev/ttyACM0`, çıkış 3; Pixhawk bağlı değil, gerçek koşum başlamaz, beklenen. 8. Karta ve TRT sürümüne özel ikili (57 MB); yeni sürümde yeniden derlenir, defterde sha güncellenir, eski engine RED. 9. PC Windows yolları, PC'deki kabul kümesi, kardeş depo, git yok, Py3.12 farkı; kod hatası yok. 10. Kameranın soldaki nesneyi ekranda solda göstermesi (aynalama yok); IMX477 takılıp jetson-io ile açıldıktan sonra, uçuştan önce.
</details>

## Kaynaklar
`jetson_paket/JETSON_ORIN_NANO_KURULUM.md` · `results/jetson_20260906/` · `REVIEW_LOG.md` D-431 · `CONTRACTS.md` §7.4–7.5 · `jetson_paket/JETSON_BASLAT.md` ·
`jetson_paket/GUN1_KONTROL_LISTESI.md` · `JETSON_OTURUM_DURUMU_20260909.md` · `scripts/jetson_fps.py` · `scripts/olcum/170_engine_karar_denkligi.py`.
