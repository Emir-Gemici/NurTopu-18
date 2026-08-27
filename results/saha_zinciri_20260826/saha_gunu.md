# 30 EYLÜL SAHA GÜNÜ — KOMUT SIRASI, BAŞARI ÖLÇÜTÜ, DÜŞERSE NE YAPILACAK

> Üretildiği tarih: **2026-08-26** · kaynak: `JETSON_KILAVUZ.md` (bugünkü hâli),
> ölçülen kuru koşu `results/saha_zinciri_20260826/kosu_cpu/ozet.json`, CONTRACTS §6.5/§6.6/§7.1/§11.2.
>
> **Komutlar kılavuzdan AYNEN alınmıştır.** Kılavuzda karşılığı olmayan adım
> **EKSİK** diye işaretlidir ve uydurma komut yazılmamıştır. Bir adımın kaynağı
> kılavuz değil de modülün kendi `argparse`'ı ise bu **açıkça** belirtilmiştir
> (o satırlar bugün `--help` ile **koşularak** alındı, tahmin değildir).
>
> 🔴 **Jetson 30 Eylül'de ele geçiyor — cihaz-öncesi deneme penceresi YOK** (D-211 §5).
> Model ve paket o günden **ÖNCE** bitmiş olmalı; o gün yalnız `.engine` derlemesi kalır.
>
> 🔴 **`results/t123/saha_gunu_kontrol_listesi.md` BAYATTIR** — birincil olarak **v35**,
> yedek olarak v34 diyor. Üretim modeli **v36**'dır (D-294). O listeyi kullanacaksan
> her `v35` → `v36`, `v34` → `v35` okuyacaksın. Bu görevde düzeltilmedi (kapsam dışı).

---

## ADIM 0 · Sahaya çıkmadan (30 Eylül'den ÖNCE, PC'de)

| ✓ | ne | komut | başarı ölçütü | düşerse |
|---|---|---|---|---|
| ☐ | Genel kapı | `<venv> -B codes/test_rota_sentetik.py` | `SONUC: 15/15 dogru` | Sahaya çıkma. Anayasa madde 14. |
| ☐ | Test paketi | `<venv> -B -m unittest discover -s tests -q` | `OK` (2026-08-26: `Ran 1002 · OK (skipped=2)`) | Düşen testi çöz; **eşiği gevşetme.** |
| ☐ | Kuru koşu | `<venv> -B scripts/saha_kuru_kosu.py --cikti results/saha_kuru_kosu_<tarih>` | Kopuk halka listesi bugünküyle **aynı** (`hedef_konumu`, `rota`, `motor`) | Yeni kopuk halka çıkarsa **regresyon**; sahaya çıkmadan bak. |
| ☐ | Paket aynası | `diff codes/<x>.py jetson_paket/kod/<x>.py` (9 dosya + `config/model_registry.json`) | **diff boş** (2026-08-26: 10/10 aynı) | Aynayı `scripts/jetson_paket_hazirla.py` ile tazele. |
| ☐ | `.onnx` pakette | `ls jetson_paket/models/` | `navitas_seg_v36_best.pt` **ve** `navitas_seg_v36_best_512_fp16.onnx` (2026-08-26: **ikisi de VAR**; yedek v35 de var) | `.engine` PC'de derlenmez; **ONNX yoksa saha günü kurtaramazsın.** |

---

## ADIM 1 · Jetson elde — ilk 10 dakika  *(JETSON_KILAVUZ §1, AYNEN)*

```bash
# 1a — JetPack ve L4T surumu
cat /etc/nv_tegra_release
head -n1 /etc/nv_tegra_release

# 1b — TensorRT surumu  (T16 bu sayiya bagli)
dpkg -l | grep -i tensorrt
python3 -c "import tensorrt; print('TensorRT', tensorrt.__version__)"

# 1c — CUDA / cuDNN
nvcc --version 2>/dev/null || echo "nvcc PATH'te yok (normal olabilir)"
python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())"

# 1d — Ultralytics var mi
python3 -c "import ultralytics; print('ultralytics', ultralytics.__version__)"

# 1e — Donanim ve guc modu
sudo tegrastats --interval 1000 | head -3
sudo nvpmodel -q
jetson_release 2>/dev/null || true
```

**BAŞARI ÖLÇÜTÜ:** `tensorrt.__version__` bir sayı basar · `torch … cuda True` ·
`nvpmodel -q` **MAXN** gösterir.
**DÜŞERSE:** `cuda False` ise `.engine` derlenmez → **ADIM 3 atlanır, `.pt`/`.onnx`
ile devam edilir** (yavaş ama görev yapar). Güç modu MAXN değilse kılavuz §1'deki
güç bloğunu koş — yoksa **FPS ölçümü yalan söyler.**

---

## ADIM 2 · Paketi Jetson'a taşı  *(§2, AYNEN)*

```bash
mkdir -p ~/navitas/{codes,comms,scripts,models,data,config}
cp kod/rpi_inference.py kod/costmap_path_finder.py kod/karar_sozlesmesi.py kod/arac_maskesi.py ~/navitas/codes/
cp kod/protocol.py kod/link.py kod/iha_sender.py kod/inis_kaniti.py kod/iha_inis_yayinci.py ~/navitas/comms/
cp kod/jetson_fps.py ~/navitas/scripts/
cp models/* ~/navitas/models/
cp config/model_registry.json ~/navitas/config/
```

```bash
python3 -c "import cv2, numpy, ultralytics; print('hepsi var')"
```

**BAŞARI ÖLÇÜTÜ:** `hepsi var` basılır.
**DÜŞERSE:** `pyserial` eksikse SiK yolu ölür ama UDP çalışır — telsiz kararını
ADIM 7'de UDP'ye çevir. `ultralytics` eksikse görev yapılamaz.

⚠ **EKSİK (kılavuzda YOK):** `kamera_dogrula.py` kopyalama satırı bu blokta **yok**,
ama §6B onu `~/navitas/codes/kamera_dogrula.py`'den çağırıyor. Kopyalamayı elle ekle,
yoksa ADIM 5 `No such file` verir.

---

## ADIM 3 · TensorRT engine derle  *(§4, AYNEN — v36)*

```bash
cd ~/navitas/models
yolo export model=navitas_seg_v36_best_512_fp16.onnx format=engine imgsz=512 half=True
```

**BAŞARI ÖLÇÜTÜ (T16 kapısı):** `.engine` dosyası oluştu **ve** tek kare çıkarım hatasız:
```bash
yolo predict task=segment model=navitas_seg_v36_best_512_fp16.engine \
  source=~/navitas/data/test_goruntuleri/sentetik_arena --imgsz 512
```
5–15 dakika sürebilir; **kesme.**

**DÜŞERSE — `trtexec` yedeği (§4, AYNEN):**
```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=navitas_seg_v36_best_512_fp16.onnx \
  --saveEngine=navitas_seg_v36_best_512_fp16.engine \
  --fp16 --workspace=4096
```
İkisi de düşerse **`.pt` ile göreve çık** — engine hız içindir, karar doğruluğu için değil.

---

## ADIM 4 · Derlenen `.engine`'i kayıt defterine TANIT  *(§4b, AYNEN)*

🔴 **ATLANIRSA YÜKLEME DÜŞER** (T143 · D-284): kayıtsız türev fail-closed **RED**.

```bash
cd ~/navitas
python3 codes/model_registry.py --turev-kaydet models/navitas_seg_v36_best_512_fp16.engine \
  --kaynak-pt models/navitas_seg_v36_best.pt
```

**BAŞARI ÖLÇÜTÜ:** komut sha256 yazar ve `DERLENINCE_YAZILIR` yer tutucusu **kalkar**;
sonraki `load_model` uyarısız geçer.
**DÜŞERSE:** `--kaynak-pt` uyuşmazlığı = **yanlış soydan derlenmiş engine** — engine'i sil,
ADIM 3'ü doğru `.onnx` ile tekrarla. **Defteri ELLE düzenleme.**
⚠ Değişen defter PC'ye geri taşınır (`tests/test_jetson_paket_defteri` aynayı kilitler).

---

## ADIM 5 · Kamera akışı  *(§6B, AYNEN)*

WiFi yolu (tercih edilen):
```bash
ping -c 3 <TELEFON_IP>

python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --kare 120 --isinma 15 \
  --kaydet ~/navitas/results/droidcam_ilk_kare.jpg
```
USB yolu (WiFi olmazsa):
```bash
sudo apt install -y android-tools-adb        # yoksa
adb devices                                   # telefonda "izin ver" cikar
adb forward tcp:4747 tcp:4747

python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://127.0.0.1:4747/video" \
  --kare 120 --kaydet ~/navitas/results/droidcam_ilk_kare.jpg
```

**BAŞARI ÖLÇÜTÜ:** son blokta `okunan kare : 120 (dusen: 0)` **ve**
`droidcam_ilk_kare.jpg`'ye **gözle bakınca** gerçek kamera görüntüsü (siyah/donmuş değil).
Sürücünün bildirdiği FPS yalan söyleyebilir; betik ölçüleni ayrı basar — **ölçüleni oku.**
**DÜŞERSE:** WiFi → USB'ye geç. İkisi de olmazsa görev kamerasız kalır; **rota üretilemez.**

Algı zinciriyle canlı test (§6B, AYNEN):
```bash
python3 ~/navitas/codes/kamera_dogrula.py \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --zincir --model ~/navitas/models/navitas_seg_v36_best_512_fp16.engine \
  --imgsz 512 --kare 60
```
⚠ **Bu adımın çıktısı bir BAŞARIM İDDİASI DEĞİLDİR** (kılavuz §6B): telefon kamerası
ne drone irtifasına ne eğitim dağılımına benzer. `rota_durumlari` dağılımını
**olduğu gibi kaydet**, karar verme.

---

## ADIM 6 · İniş sinyali yayıncısı (IHA_LANDED)

🔴 **EKSİK — `JETSON_KILAVUZ.md`'de bu sürecin ÇALIŞTIRMA KOMUTU YOK.**
Kılavuz yalnız `cp … iha_inis_yayinci.py …` satırını taşıyor (`:301`); servis ya da
runbook satırı **hiç yok**. Bu, `results/sartname_bosluk/rapor.md` R10'un kapanmayan
yarısıdır. **Uçuş günü bunu kimse başlatmazsa İKA sürüş latch'i HİÇ açılmaz** ve
şartname §2.2.5 görevi başarısız olur.

Aşağıdaki arayüz **kılavuzdan değil**, modülün kendi `argparse`'ından bugün
`--help` **koşularak** alınmıştır (uydurma değil, ama kılavuz yordamı yerine geçmez):

```
iha_inis_yayinci.py --mavlink MAVLINK --kanit-timeout KANIT_TIMEOUT
                    [--serial SERIAL] [--baud BAUD] [--ika IKA] [--yks YKS]
                    [--heartbeat-sure HEARTBEAT_SURE] [--heartbeat-aralik HEARTBEAT_ARALIK]
```
- `--heartbeat-sure` varsayılanı **600 s** = şartname §6.2 İKA görev süresi
  (`IHA_INIS_HEARTBEAT_SURESI_S`, `codes/karar_sozlesmesi.py:1548`) — K6, T148.
- `--heartbeat-aralik` varsayılan 0,5 s; `ika_receiver` `hb_timeout`'undan **küçük olmalı**.

**BAŞARI ÖLÇÜTÜ:** Pixhawk `EXTENDED_SYS_STATE.landed_state == ON_GROUND` **ve**
`relative_alt < 1 m` ardışık 3 çift → `IHA_LANDED` ACK'li gider; iniş sonrası
heartbeat **sürer** (yoksa 3 s'de `link_lost`).
**DÜŞERSE:** MAVLink bağlantısı yoksa latch açılmaz — **manuel "İHA İNDİ" düğmesi
latch'i AÇMAZ** (`tests/test_iha_landed_gate.py:313`), bu bilerek böyledir.
Telemetri gelmiyorsa görev **fail-closed** durur; yazılımdan zorlanmaz.

**🔴 MİMARA AÇIK İŞ:** bu adımın komutu `JETSON_KILAVUZ.md`'ye yazılmalı.

---

## ADIM 7 · SAHA GÖREV KOMUTU — telsiz halkasıyla  *(§6.5 / K1, AYNEN)*

UDP (dev/LAN):
```bash
python3 ~/navitas/codes/rpi_inference.py --camera \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --mavlink udpin:0.0.0.0:14550 --mav-sysid 1 --fov 78 \
  --yks-hedef <YKS_IP>:5005 --ika-hedef <IKA_IP>:5006
```

SiK 433 MHz telsiz (saha, ACK beklenmez — tek hatta yayın):
```bash
python3 ~/navitas/codes/rpi_inference.py --camera \
  --kaynak "http://<TELEFON_IP>:4747/video" \
  --mavlink udpin:0.0.0.0:14550 --mav-sysid 1 --fov 78 \
  --telsiz-seri /dev/ttyUSB0 --telsiz-baud 57600
```

**BAŞARI ÖLÇÜTÜ:** başlangıçta
`telsiz halkasi: yks=… ika=… seri=… · heartbeat 1 s` satırını **gör**.
**DÜŞERSE:** çıkışta `UYARI: telsiz yayin hatalari` basılırsa **halka kopuktur** —
hedef vermezsen telsiz halkası **hiç kurulmaz** (eski davranış, sessiz).
⚠ **SiK üzerinde ölçüm HENÜZ YAPILMADI**; yalnız UDP loopback ölçüldü
(`tests/test_rpi_telsiz_yayin.py`). Saha günü SiK ilk kez gerçek koşacak —
**yedek plan UDP'dir.**

⚠ **`--mavlink` VERİLMEZSE her kare `OLCEK_YOK` → NO_ROUTE.** Ölçek halkası canlı
irtifaya bağlıdır (fail-closed, T43). Bu bir arıza değil, sözleşmedir.

### 🔴 ADIM 7b · İHA-UB REFERANS NOKTASI — şartname §6.2 "Alan İhlali" (T162 · D-307)

Yukarıdaki komutlara **`--ub-referans <LAT>,<LON>`** eklenmezse YKS **ALAN İHLALİ
denetimi YAPAMAZ**. Bu sessiz değildir; başlangıçta şu satır basılır:

```
UYARI: --ub-referans verilmedi ya da canli telemetri yok — HEARTBEAT'e x,y
EKLENMEZ; YKS ALAN IHLALI denetimi YAPILAMAZ (sartname SS6.2/SS6.4).
```

**Referans, İHA-UB'nin bir KÖŞESİDİR** (yerel çerçeve 0..300 m, x doğu / y kuzey).
Yanlış köşe girmek, **yanlış ihlal** demektir — bu yüzden:

1. Hakemden/krokiden İHA-UB'nin **güneybatı** köşesinin koordinatını al.
2. Telefonla ya da Pixhawk'tan **ondalık derece** olarak oku (`39.9251234,32.8661234`).
3. Komuta ekle:
   ```bash
   --ub-referans 39.9251234,32.8661234
   ```
4. **BAŞARI ÖLÇÜTÜ:** başlangıçta `IHA-UB referansi: <lat>,<lon> · kenar 300 m`
   satırını **gör**. YKS'de İHA hareket ettikçe mini genel-sahada iz belirmeli.
5. **DOĞRULAMA (kalkıştan önce, yerde):** İHA yerdeyken YKS'de görünen `x,y`
   kabaca **0..300 bandında** ve krokideki yerine benziyor olmalı. Değilse köşe
   yanlıştır — düzeltmeden uçma; yanlış referans **sahte alan ihlali** üretir.

⚠ Bu ölçüm **gerçek Pixhawk ile hiç sınanmadı** (D-307 §5). Sahada ilk kez
gerçek koşacak; şüphede kalırsan bayrağı **verme** — denetim kapalı kalır ama
yanlış ihlal de üretilmez.

---

## ADIM 8 · İKA tarafı  *(süre bayrakları — CONTRACTS §7.1 / K5 · T148)*

🔴 **EKSİK — `JETSON_KILAVUZ.md`'de `ika_nav` çalıştırma komutu YOK.**
Aşağısı modülün `argparse`'ından bugün `--help` **koşularak** alındı:

```
ika_nav.py [--bind BIND] [--bekleme-suresi BEKLEME_SURESI]
           [--surus-suresi SURUS_SURESI] [--yks YKS] [comms]
```
| bayrak | varsayılan | şartname dayanağı |
|---|---|---|
| `--bekleme-suresi` (eski `--timeout`) | **900 s** | §6.2 İHA görev süresi — rota + `IHA_LANDED` + `IKA_GO` beklemesi |
| `--surus-suresi` | **600 s** | §6.2 İKA görev süresi — izin geldikten sonra HB'ye ulaşma |
| `--yks` | yok | **K8**: `OPEN_ROUTE`/`NO_ROUTE` ACK kopyası hakem ekranına |

🔴 **`--yks` VERİLMEZSE**, YKS'de *"İKA'ya aktarıldı"* **2. hakem onayı HİÇ AÇILMAZ**
(şartname §2.2.3 üçüncü maddesi karşılanamaz). Bu, T147'nin kapattığı boşluktur —
bayrağı unutmak onu **geri açar**.

**BAŞARI ÖLÇÜTÜ:** YKS'de "İKA ALDI" satırı görünür ve 2. onay düğmesi **açılır**;
`IKA_GO` kaybolursa aynı `seq` ile **tekrar** gider (§6.6).
**DÜŞERSE:** `IKA_GO` ACK'i hiç gelmezse düğme **yeniden açılır** — tekrar bas.
Rota yoksa İKA **sürmez** ve sebep kaydedilir; **model değiştirilmez** (D-277 §3-4).

---

## ADIM 9 · FPS ölçümü *(§5, AYNEN — görev sonrası, acele değil)*

```bash
cd ~/navitas
python3 scripts/jetson_fps.py \
  --girdi test_goruntuleri/sentetik_arena \
  --pt models/navitas_seg_v36_best.pt \
  --onnx models/navitas_seg_v36_best_512_fp16.onnx \
  --engine models/navitas_seg_v36_best_512_fp16.engine \
  --imgsz 512 \
  --isinma 15 --tekrar 120 --conf 0.30 --cihaz 0 \
  --cikti results/jetson_fps_v36_$(date +%Y%m%d_%H%M%S)
```

**BAŞARI ÖLÇÜTÜ:** `exit=0`, `ozet.json` yazılır.
**PC referansı (RTX 5080):** `çıkarım 14,00 ms · maske 2,23 ms · costmap 8,89 ms ·
toplam 27,38 ms · 36,5 FPS`.
**DÜŞERSE:** ölçüm görevin ön koşulu değildir — **göreve engel olmaz**, kaydet ve geç.
⚠ **`--kayit-dogrulamasiz` SAHADA YASAK.**

---

## ADIM 10 · Birincil düşerse — YEDEK MODEL GEÇİŞİ *(§6C, G1–G8)*

🔴 **Karar İNSANINDIR** (D-133). Yordam yalnız mekaniktir. Önce **G2 bütünlük** koş:

```bash
cd ~/navitas
python3 - <<'PY'
import hashlib, json, pathlib
kok = pathlib.Path.home() / "navitas"
man = json.loads((kok / "models/jetson_derleme_manifest.json").read_text(encoding="utf-8"))
kunye = {x["dosya"]: x["sha256"] for x in man["paket_icerigi"]}
for ad in ("navitas_seg_v35_best.pt", "navitas_seg_v35_best_512_fp16.onnx"):   # v36 terfisi: yedek = v35
    yol = kok / "models" / ad
    beklenen = kunye.get(ad)
    ozet = hashlib.sha256(yol.read_bytes()).hexdigest()
    print(ad, "OK" if ozet == beklenen else f"UYUSMAZ ({ozet[:12]} != {str(beklenen)[:12]})")
PY
```

**BAŞARI ÖLÇÜTÜ:** her satır `OK`.
**DÜŞERSE:** `UYUSMAZ` görürsen **DUR** — bozuk yedekle koşmak, düşen birincille
koşmaktan **kötüdür**. Geçiş yapılmaz.

### Hangi arızada ne yapılır

| gördüğün | senaryo | ne yap |
|---|---|---|
| Ekran **rota çizmiyor**, `road` yayınlanmıyor | (b) göremiyor | 🔴 **MODEL DEĞİŞTİRİLMEZ.** İKA sürmez, sebep kaydedilir (D-277 §3-4). Yedek v35 bu eksende **daha kötü** olabilir; körlüğü başka modelle denemek çözüm değildir. |
| İKA **moloza basıyor** | (a) çok basıyor | §6C geçişi meşru → G3–G7 |
| Süreç **çöküyor / model yüklenmiyor** | (c) teknik | G2 → geçiş; herhangi bir doğrulanmış ağırlık |

⚠ **v36 karar kararlılığında v35'ten KÖTÜ ölçüldü** (D-295 §3) — fazlalığın tamamı
"rota VAR/YOK çevrilmesi", yani **gürültü altında rotanın kaybolması**. Yön fail-closed
ama saha elverişliliğini düşürür. Sahada (b) senaryosunu görme olasılığın v35'e göre
**daha yüksektir**; yukarıdaki kural o yüzden daha da bağlayıcıdır.

---

## SAHA GÜNÜ BİLİNEREK KABUL EDİLEN AÇIKLAR

Bunlar 30 Eylül'de **kapalı olmayacak**; şaşırma, yerinde çözmeye çalışma:

| # | açık | sonucu | kaynak |
|---|---|---|---|
| 1 | **Gerçek İKA motor sürücüsü yok** (T149) | `send_vel` yalnız `gz`; gerçek İKA yazılımdan sürülmez | kuru koşu `motor SAHİPSİZ` · R12 |
| 2 | **HB dedektörü üretime bağlı değil** (T150) | Rota hedefi **üst banttır**, HB koordinatı İKA'ya gitmez | kuru koşu `hedef_konumu SAHİPSİZ` · D-295 §2 (gerçek pedde %0) |
| 3 | **Üretim yolu `analyze_path` hiçbir kapıda yok** (T156) | 15/15 kapısı ve kuru koşu `rota_bul`u ölçüyor | CONTRACTS §11.2-EK · D-297 §1 |
| 4 | **SiK seri hattı hiç ölçülmedi** | Saha günü **ilk kez** gerçek koşacak | R20 · yedek: UDP |
| 5 | **T153 ince beton şerit çıkarıcı KAPALI** | Beton kanal/bordür zemin sayılabilir | ön kayıt §13 kuralı sağlanmadı · D-291 |
| 6 | **Uçuş kontrolcüsü repo dışı** | Otonom uçuş, geofence, otonom paraşüt | R2/R9/R17 · ÖLÇÜLEMEDİ |

---

## GETİRİLECEK KANITLAR *(§7, AYNEN)*

| # | ne | hangi adımdan |
|---|---|---|
| 1 | `/etc/nv_tegra_release` + TensorRT sürümü | ADIM 1 |
| 2 | `.engine` derleme çıktısı + T16 kapısı | ADIM 3 |
| 3 | `model_registry --turev-kaydet` çıktısı (sha256) | ADIM 4 |
| 4 | `kamera_dogrula.py` son bloğu + `droidcam_ilk_kare.jpg` | ADIM 5 |
| 5 | `telsiz halkasi: …` başlangıç satırı | ADIM 7 |
| 6 | YKS'de "İKA ALDI" + 2. onay ekran görüntüsü | ADIM 8 |
| 7 | `results/jetson_fps_v36_*/ozet.json` + `rapor.md` | ADIM 9 |
| 8 | Değişen `config/model_registry.json` (PC'ye geri) | ADIM 4 / ADIM 10 |
