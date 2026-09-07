# NAVITAS — JETSON KURULUM SÜRECİ · 6 Eylül 2026 (17:05 → 19:30, TAMAMLANDI)

> **7 Eylül 2026 — depoya taşıma notu (G0a, REVIEW_LOG D-431).** Bu belge 6 Eylül Jetson oturumunda
> yazıldı ve `GELISTIRICIYE_20260906` paketiyle geldi. Taşınırken: paketin **D-428** numarası master'daki
> D-428/429/430 ile çakıştığı için kayıt **D-431** oldu ve buradaki atıflar buna çevrildi; ham çıktılar
> `results/jetson_20260906/` altına kondu (yollar yeniden köklendi); denklik betiği
> `scripts/olcum/170_engine_karar_denkligi.py` (paketin 165 numarası `165_trt_pc_provasi.py` ile
> çakışıyordu). Aynı gün uygulanan kararlar: FP32 `navitas_seg_v36_best.engine` yer tutucu girdisi
> defterden çıkarıldı (K4), manifest ve KILAVUZ §4 export komutu `.pt`'den (K5), `test_t143` (K3).
> Ölçüm metni değiştirilmedi.

> Bu dosya, oturumu takip edemeyen okuyucu için **olan biteni sırayla** anlatır.
> Ham çıktılar: `navitas/results/jetson_20260906/jetson_log_20260906/` ve `navitas/results/jetson_20260906/jetson_fps_20260906_orin_nano/`.
> Kurulum tutanağı (kapı kapı): `navitas/jetson_paket/JETSON_ORIN_NANO_KURULUM.md`.
> Keşif raporu: `JETSON_KESIF_RAPORU_20260906.md` · sayfa: https://claude.ai/code/artifact/43c0be67-d9e8-4a0b-bcc8-f85b80ea249d
>
> **Durum satırı en sonda (§9).** Kusur/karar kaydı: `navitas/REVIEW_LOG.md` **D-431**.

---

## 1. Ne bulundu (17:05–17:15)

- Kart **Jetson Nano değil, Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12, NVMe kök). Paket Nano/JetPack 4.6 için hazırlanmıştı; `wheels/` (cp38) ve `JETSON_NANO_KURULUM.md` bu kartta geçersiz.
- Uçuş modeli **v36** (`navitas_seg_v36_best.pt`, YOLOv8m-seg, 512, sınıf 0 zemin / 1 engel) pakette; sha256 kayıt defteriyle eşleşti.
- RAM 3,4 GiB, swap 0; masaüstü + Firefox 2,7 GB tutuyordu. Kamera ve Pixhawk bağlı değildi.
- Sudo parola istiyordu; kullanıcı parolayı verdi, root adımları betikle koşuldu.

## 2. Root kurulum (17:20–17:31) — `orin_nano_root_kurulum.sh`

`apt install nvidia-jetpack ...` (136 paket: CUDA 13.2, TensorRT 10.16.2, cuDNN, python3-pip/venv/opencv, gstreamer) ·
`/swapfile` 8 GB · `n4vitas` → dialout, video grupları · `nvpmodel -m 0` · `jetson_clocks`.
**Kapı:** nvcc 13.2 · tensorrt 10.16.2.10 · sistem cv2 4.6 GStreamer=True · swap 8,0 GiB · 10W. GEÇTİ.

## 3. Python ortamı (17:33–17:38) — `orin_nano_venv_kurulum.sh`

`~/venv312` (sistem paketlerini görür) · torch **2.11.0+cu130** + torchvision 0.25 (jetson-ai-lab `sbsa/cu130`) ·
ultralytics 8.4.142 · pymavlink 2.4.49 · MAVProxy · onnx/onnxslim · onnxruntime-gpu 1.29 · tqdm.
**Kapı:** `torch.cuda.is_available()` True (Orin) · GPU matmul, conv2d, sigmoid, interpolate, nms hepsi çalıştı ·
`import tensorrt` 10.16.2.10 · YOLO predict GPU 174–237 ms/kare, CPU 746–985 ms/kare. GEÇTİ.
Uyarı: torch tekerleği sm_87 için derlenmemiş (sm_80 SASS ile koşuyor); ölçümde hata üretmedi.

Ek: `~/navitas` → paket köküne symlink; `~/.local/bin/mavproxy.py` → venv'e symlink (systemd birimi PATH'i).

## 4. Yazılım kapıları (17:38–17:46)

| kapı | sonuç |
|---|---|
| Genel kapı `codes/test_rota_sentetik.py` (madde 14) | **GEÇTİ** — kol1 15/15 · kol2 şerit 15/15 |
| Kayıt defteri `model_kayit_dogrula` | v36 .pt `eslesti` · v36 .onnx `turev_eslesti` · v35 **RED** (doğru) |
| `jetson_baslat.sh --kuru` (udp) | tüm dosyalar `[VAR]`, kullanıcı/yorumlayıcı `[VAR]`; tek `[YOK]`: Pixhawk `/dev/ttyACM0` (bağlı değil) → çıkış 3 |
| `jetson_baslat.sh --kuru` (sik) | + `[YOK]` `/dev/ttyUSB0` (SiK bağlı değil) |
| Kamera köprüsü (sistem python3 + cv2 4.6, dosya kaynağı) | `/durum` kaynak_acik=true, 5 fps, 1024×576 · `/kare.jpg` HTTP 200 (107 KB). CSI: `No cameras available` (kamera yok) |

## 5. TensorRT engine (17:43–17:52) — T16/T109

`yolo export model=navitas_seg_v36_best.pt format=engine imgsz=512 half=True device=0` → 530 s → 57 MB engine.
(Manifestteki "ONNX'ten export" komutu ultralytics'te çalışmaz; `.pt`'den derlendi.)
Dosya: `jetson_paket/models/navitas_seg_v36_best_512_fp16.engine` (+ `models/` aynası).
Defter: `model_registry.py --turev-kaydet` → sha `bb9bd868…0300` yazıldı, paket aynası aynı. `model_kayit_dogrula` → `turev_eslesti`. GEÇTİ.
Manifest `jetson_derleme_manifest.json` `paket_icerigi`'ne engine eklendi (test_uretim_modeli_hizasi bunu istiyordu).

## 6. FPS (17:53–17:57) — T17, eşik 0,61 FPS p50 **ve** p95

| model | çıkarım p50/p95 ms | maske | costmap A | **toplam p50/p95 ms** | **FPS p50 / p95** | kapı |
|---|---:|---:|---:|---:|---:|---|
| PyTorch GPU | 188 / 303 | 312 | 210 | 739 / 942 | **1,35 / 1,06** | GEÇTİ |
| TensorRT FP16 | 87 / 106 | 311 | 208 | 635 / 751 | **1,58 / 1,33** | GEÇTİ |
| ONNX (onnxruntime-gpu) | — | — | — | — | — | HATA: CUDA sağlayıcısı sm_87 çekirdeği yok |

🔴 Darboğaz model değil: `get_masks` + costmap CPU'da ~520 ms, toplamın %82'si. Engine toplamda 104 ms kazandırıyor.
Rota durumları iki kolda aynı: BELIRSIZ_COKLU 101 · ACIK 2 · KAPALI_DAR 17. gpu 54→56 °C.

## 7. Tam test paketi (17:58–18:06)

`unittest discover -s tests` → **Ran 2121 · failures 5 · errors 30 · skipped 8**. Sınıflandırma:
- **26 ortam**: `O:/navitas-local-train/venv/Scripts/python.exe` (Windows venv, 17 test), `O:/…/sentetik_arena_kadraj_t66` kabul kümesi (5), `navitas-local-train/ayarlar.py` yok (2), `.gitignore`/`.git` yok (1), `/tmp` izin (1).
- **3 `tqdm` eksik** → kuruldu, üçü de OK.
- **1 manifest** → engine manifeste eklendi, `test_uretim_modeli_hizasi` 37/37 OK.
- **1 beklenen**: `test_t143…engine_YER_TUTUCU` defterde engine sha'sının yer tutucu olmasını **istiyor**; engine derlendiği için artık gerçek sha var. Test PC'de güncellenmeli (mimar).
- **2 Python 3.12**: `test_faz_b_protocol_dayaniklilik` ön koşulu (RecursionError yerine JSONDecodeError), `test_k6…ayni_modulu` (`is` kimliği).
- **1 kuru koşu testi** (`test_faz_b_jetson_baslat K9`): gerçek makinede her şey `[VAR]` olduğu için sahte eksik üretemedi.
- **1 zamanlama**: `test_yks_kamera_istemci` ("2 not greater than 2"), yeniden koşuda da düştü.
Yeniden koşulan 11 dosya: 9 OK, 2 yukarıdaki bilinen (t143, yks_kamera).

## 8. Karar denkliği engine ↔ pt (18:00 → 19:04)

`scripts/olcum/170_engine_karar_denkligi.py` — D-375 yöntemi, kol B = `.engine`.
S = `data/arena_kompozit_v2` (126 GT'li kare) · R = dji_20260822 ≥ 30 m katmanı (633 kare, 4K).
İlk koşum 4K karelerde CPU costmap yüzünden 46 dk'da ~16 kare ilerledi → durduruldu; R kareleri üretim koşuluna
(1280 genişlik) küçültülerek 18:55–19:04'te yeniden koşuldu.

| kapı | ölçülen | eşik | hüküm |
|---|---|---|---|
| F1 zarar yönü (S) | 0 kare | 0 | **GEÇTİ** |
| F2 uyuşma (R ≥ 30 m, 633 kare) | 0,9953 | ≥ 0,98 | **GEÇTİ** |
| D-303 oransal (S) | 3/126 = %2,38 | ≤ %1,92 | **DÜŞTÜ** |

3 S uyuşmazlığında pt de yanlıştı (zarar yok); iki kol S'te eşit doğrulukta (52/126). **Sonuç: engine üretime alınmaz,
uçuş `.pt` ile** (plan §2 kuralı). Nihai karar mimarın (T66 kabul kümesi PC'de).

## 8a. 10 dakika sürekli koşum (19:06–19:27) — GUN1 §6

| model | süre | toplam p50/p95 ms | ilk 1 dk FPS | son 1 dk FPS | değişim | termal |
|---|---:|---:|---:|---:|---:|---|
| PyTorch .pt | 11,4 dk | 770 / 922 | 1,28 | 1,31 | +2,6 % | OK |
| TensorRT FP16 | 9,5 dk | 649 / 765 | 1,53 | 1,53 | −0,4 % | OK |

gpu en çok 56,3 °C, cpu 57,5 °C, güç en çok 9,4 W, throttle yok. Sürekli koşumda FPS düşmüyor.

## 8b. Uyumluluk sorusu — "yazılım hem İHA'ya hem kendi drone'umuza uyar mı?"

**Evet, Jetson tarafı gövdeden bağımsızdır; gövdeye özgü olan Pixhawk yapılandırmasıdır.** Kanıt (kod taraması, `comms/`):
- Jetson yalnız standart MAVLink konuşur: `GLOBAL_POSITION_INT` (irtifa → mpp), `EXTENDED_SYS_STATE` (iniş kanıtı), `GPS_RAW_INT`, `HEARTBEAT`, `COMMAND_LONG` ile `DO_PARACHUTE` / `COMPONENT_ARM_DISARM` / `NAV_RETURN_TO_LAUNCH` / `NAV_LAND`. Kodda **MAV_TYPE, gövde tipi, uçuş kipi adı (GUIDED/AUTO vb.) denetimi YOK**. ArduCopter ve ArduPlane bu mesajların hepsini üretir/kabul eder.
- Tek pin `--sysid` (Pixhawk `SYSID_THISMAV`); her iki gövdede de 1 yapılırsa aynen çalışır.
- **Gövdeye özgü olanlar:** (1) Pixhawk parametre dosyası — `config/pixhawk/arducopter_fda.param` **ArduCopter 4.5.7** içindir, sabit kanat için ArduPlane parametre seti ayrıca yazılmalı; (2) görev dosyası `fda_gorev.waypoints` (copter kalkış); (3) paraşüt: ArduPlane `CHUTE_ENABLED=0` ise `DO_PARACHUTE`'u reddeder, kod bunu ACK yokluğundan görür ve kırmızı uyarır; (4) YKS `--fda` kipi (quad prova: paraşüt ve İKA kapalı, süre 10 dk) — CONTRACTS §6.7; (5) kamera yatay FOV her gövdede **ayrı beyan** edilir (`FOV=` ortam değişkeni), tahmin edilmez.
- **Ölçülmedi:** ArduPlane ile hiç sınanmadı (SITL de gerçek uçak da yok). "Uyumlu" hükmü kod okumasına dayanır; kapı, uçaktaki Pixhawk'a bağlanıp `jetson_baslat.sh --kapi` (3 uçta `mavlink_dogrula`) + iniş kanıtı provasıdır.

## 9. Durum satırı

| adım | durum |
|---|---|
| Root kurulum | GEÇTİ |
| venv + torch + ultralytics | GEÇTİ |
| Genel kapı 15/15 | GEÇTİ |
| Kayıt defteri | GEÇTİ |
| Engine derleme + kayıt | GEÇTİ |
| FPS ≥ 0,61 (p50 ve p95) | GEÇTİ (pt ve engine) |
| Karar denkliği engine↔pt | F1 GEÇTİ · F2 GEÇTİ · D-303 oransal DÜŞTÜ → uçuş `.pt` ile |
| 10 dk sürekli koşum (GUN1 §6) | GEÇTİ — düşüş yok, termal OK |
| Kamera (IMX477) | ÖLÇÜLEMEDİ — kamera bağlı değil |
| Pixhawk / çoğullayıcı | ÖLÇÜLEMEDİ — Pixhawk bağlı değil |
| Tam süit | 2121 test; kalan sorunlar ortam/PC işi (§7) |

## 10. Mimara / PC tarafına giden liste (D-431 §4)

1. Donanım künyesi 5 belgede + `test_faz_b_nano_kurulum.py` → Orin Nano 4GB / JetPack 7.2.1.
2. Engine üretime alınmadı (D-303 oransal düştü); T66 kabul kümesiyle PC'de yeniden karar.
3. `test_t143…engine_YER_TUTUCU` güncellenmeli (engine sha artık gerçek).
4. Defterde `navitas_seg_v36_best.engine` yer tutucu — mühürden önce karar.
5. FPS darboğazı CPU post-process (maske + costmap ≈ 520 ms); model hızlandırma FPS'i artırmaz.
6. `wheels/` (246 MB, cp38) bu kartta anlamsız; silme kararı kullanıcının.

## 11. Sahada Jetson'u kaldırma (kısa yol)

```bash
source ~/venv312/bin/activate
cd ~/navitas
# kuru bakış (hiçbir şey başlatmaz):
PATH=$HOME/.local/bin:$PATH KIP=udp YKS_IP=<YKS_IP> IKA_IP=<IKA_IP> FOV=<derece> \
  KAMERA=http://127.0.0.1:8080/video NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python \
  bash jetson_paket/jetson_baslat.sh --kuru
# Pixhawk takılıyken kur + kapılı kaldır:
sudo -E PATH=$HOME/.local/bin:$PATH KIP=udp YKS_IP=… IKA_IP=… FOV=… KAMERA=http://127.0.0.1:8080/video \
  NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python bash jetson_paket/jetson_baslat.sh --kapi
bash jetson_paket/jetson_baslat.sh --durum
```
Kamera IMX477 takılınca önce `sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → reboot → ayna testi.
