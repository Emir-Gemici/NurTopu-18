# NAVITAS — DRONE BİTTİKTEN SONRA SAHA YOL HARİTASI

> **Hazırlanma:** 16 Eylül 2026 · **Kod sürümü:** `a81784c2` (MAVLink TUNNEL köprüsü dahil)
> **Hedefler:** 21 Eylül Adıyaman ekip provası → 30 Eylül–3 Ekim FDA görev test uçuşu
> **Düzen:** tek RFD900A çifti Pixhawk **TELEM1**'de; Jetson Pixhawk **TELEM2**'ye 3 telle bağlı;
> NAVITAS mesajları Pixhawk üzerinden **MAVLink TUNNEL** ile YKİ'ye gider; Mission Planner uçuş
> boyunca açık kalır. Video telemetri **yok**.
>
> Bu belgedeki her komut depodan (dosya:satır) doğrulanarak yazıldı. Tünel ölçümlerinin kanonik
> kaynağı `jetson_paket/TUNEL_SAHA_RUNBOOK.md`'dir; iki belge çelişirse **bana yaz**, tahminle
> ilerleme.

---

## İÇİNDEKİLER

- [0. Önce bunu oku](#0-önce-bunu-oku)
- [1. Zaman planı](#1-zaman-planı)
- [2. FAZ 0 — Drone bitmeden masada yapılacaklar](#2-faz-0--drone-bitmeden-masada-yapılacaklar)
- [3. FAZ 1 — Montaj sonrası mekanik ve elektrik kontrol](#3-faz-1--montaj-sonrası-mekanik-ve-elektrik-kontrol)
- [4. FAZ 2 — Pixhawk: parametre, kalibrasyon, motor ve failsafe testleri](#4-faz-2--pixhawk-parametre-kalibrasyon-motor-ve-failsafe-testleri)
- [5. FAZ 3 — Jetson ↔ Pixhawk TELEM2 bağlantısı](#5-faz-3--jetson--pixhawk-telem2-bağlantısı)
- [6. FAZ 4 — Jetson servislerinin kurulumu (KIP=tunel)](#6-faz-4--jetson-servislerinin-kurulumu-kiptunel)
- [7. FAZ 5 — YKİ (bu bilgisayar) kurulumu](#7-faz-5--yki-bu-bilgisayar-kurulumu)
- [8. FAZ 6 — Tünel ölçümü (K8) — uçuştan önce zorunlu](#8-faz-6--tünel-ölçümü-k8--uçuştan-önce-zorunlu)
- [9. FAZ 7 — Yerde tam zincir provası (pervanesiz)](#9-faz-7--yerde-tam-zincir-provası-pervanesiz)
- [10. FAZ 8 — Uçuş testleri (pervaneli, kademeli)](#10-faz-8--uçuş-testleri-pervaneli-kademeli)
- [11. FAZ 9 — Görev günü akışı](#11-faz-9--görev-günü-akışı)
- [12. Uçuşta acil durum prosedürü](#12-uçuşta-acil-durum-prosedürü)
- [13. Arıza giderme tabloları](#13-arıza-giderme-tabloları)
- [Ek A — Parametre tablosu](#ek-a--parametre-tablosu)
- [Ek B — Komut kopya kartı](#ek-b--komut-kopya-kartı)
- [Ek C — Her fazdan sonra bana gönderilecekler](#ek-c--her-fazdan-sonra-bana-gönderilecekler)

---

## 0. Önce bunu oku

### 0.1 Belge nasıl kullanılır

- Fazlar **sırayla** yapılır. Her fazın sonunda bir **KAPI** vardır; kapı geçmeden sonraki faza
  geçilmez. Tek istisna Faz 0: drone yapılırken paralel yapılabilir.
- Her adım şu düzende yazıldı: **Ne** → **Neden** → **Nasıl** (komut / menü yolu) →
  **Geçti sayılır** → **Olmazsa**.
- Sonuç üç değerden biridir: **GEÇTİ**, **DÜŞTÜ**, **ÖLÇÜLEMEDİ**. Yapılmayan ölçüm
  "geçti" yazılmaz, tahmini sayı yazılmaz.
- Her günün çıktıları bu bilgisayarda tek klasöre gider:
  `O:\navitas\results\saha_<YYYYMMDD>\` (tünel ölçümleri runbook gereği
  `results\tunel_<YYYYMMDD>\`). Dosya adları adımların yanında yazılı.
- Bir adım düşerse: §13'teki ilgili tabloya bak, çözemezsen **komut çıktısının tamamını** bana
  yapıştır.

### 0.2 Değişmez güvenlik kuralları

1. **Pervaneler yalnız Faz 8'de takılır.** Motor testleri, arm testleri, failsafe testleri ve
   yerde zincir provası **pervanesiz** yapılır.
2. Pil takılıyken hiç kimse drone'un üstüne eğilmez; arm edilecekse herkes en az 3 m geride.
3. Aynı anda **tek kişi** parametre yazar (Mission Planner'da). Diğerleri yalnız okur.
4. **CH6 anahtarı = DISARM** (`RC6_OPTION=153`): havada motorları keser, drone **düşer**.
   Yalnız yere çok yakınken ya da kontrolden tamamen çıkmışken kullanılır.
5. Jetson çökerse drone **uçmaya devam eder** (Pixhawk bağımsızdır). Acil iniş pilot
   kumandası ya da Mission Planner ile yapılır (§12).
6. Her uçuşun `.bin` logu uçuş bitince **USB ile** bilgisayara alınır (RFD üzerinden indirme
   çok yavaş).
7. **Faz 8'deki tam provalar başladıktan sonra kod değişmez.** Değişirse provalar baştan
   sayılır.

### 0.3 Sistem şeması

```
HAVA (drone)
  Kamera IMX477 ─CSI─► navitas-kamera-koprusu (127.0.0.1:8080/video)
                                  │
                                  ▼
  navitas-rpi-inference ── model v36 .pt, FOV, irtifa ──► rota kararı (OPEN_ROUTE / NO_ROUTE)
  navitas-iha-inis-yayinci ── iniş kanıtı ──► IHA_LANDED
  navitas-iha-komut-alici ◄── YKİ komutları (ARM, DISARM, LAND, RTL)
            │ (hepsi UDP 127.0.0.1:5100)
            ▼
  navitas-seri-hub (--tunel 127.0.0.1:14553)
            │
  navitas-cogullayici (MAVProxy) ── /dev/ttyTHS1 57600 ── Pixhawk TELEM2
     çıkışlar: 14550 (rpi_inference), 14551 (inis_yayinci), 14552 (komut_alici), 14553 (tünel)
                                                          │
                                                   Pixhawk 6C (ArduCopter 4.5.7)
                                                          │ TELEM1 57600
                                                       RFD900A (hava)
                                                          ┊ 915 MHz
YER (bu bilgisayar)                                    RFD900A (yer) ── USB ── COMx
  Mission Planner (COMx'in TEK sahibi) ── MAVLink ayna: UDP Client 127.0.0.1:14570
                                                          │
  yks_gui.py --tunel 127.0.0.1:14570 --fda  (hakem ekranı, ARM/LAND/RTL düğmeleri)
```

**Mesaj tipleri** (`comms/protocol.py:32-39`): `OPEN_ROUTE`, `NO_ROUTE`, `HEARTBEAT`, `ACK`,
`CMD`, `IHA_LANDED`. ARM, DISARM, RTL, LAND ve PARACHUTE ayrı mesaj değil, `CMD` mesajının
`cmd` alanıdır. FDA kipinde paraşüt ve İKA düğmeleri kapalıdır.

### 0.4 Roller (uçuş günü en az 3 kişi)

| Rol | Görevi | Elinde |
|---|---|---|
| **Pilot** | Kumanda; acil durumda mod anahtarıyla kontrolü alır | FS-i6 |
| **MP operatörü** | Pil, GPS, mod, mesajlar; acil LAND/RTL; parametre yazan tek kişi | Mission Planner |
| **YKİ operatörü** | `yks_gui`; ARM komutu, kalkış kronometresi, hakem onayı, iniş | `yks_gui` penceresi |
| **Jetson sorumlusu** | Uçuş öncesi SSH, servisler, `--kapi` | Ethernet kablosu + SSH |

Aynı kişi hem pilot hem YKİ operatörü **olamaz** (uçuş anında ikisi eşzamanlı).

### 0.5 Faz 2'den önce netleşmesi gereken kararlar

**KARAR 1 — Otonom kalkış nasıl başlayacak?**

Plan: hakem onayından sonra YKİ'den ARM, drone AUTO görevle kendisi kalkar
(`SAHA_HAZIRLIK_PLANI_20260903.md` §6). Pixhawk'taki son döküm (14.09) bunu **engelliyor**:

- `AUTO_OPTIONS=0` (`14.09.2026.param:92`). ArduPilot belgesine göre bit0 kapalıyken AUTO
  modunda arm **reddedilir**, bit1 kapalıyken AUTO kalkışı için gaz çubuğunun kaldırılması
  gerekir.
- `FLTMODE1..6 = Stabilize, Stabilize, Stabilize, Loiter, Stabilize, Land`
  (`14.09.2026.param:387-392`). Kumanda anahtarında AUTO **yok**.

| Seçenek | Nasıl | Artısı | Eksisi |
|---|---|---|---|
| **A (önerilen)** | `AUTO_OPTIONS=3`; görev MP'den yüklenir; MP'den mod **AUTO** yapılır; YKİ'den ARM → drone kendisi kalkar | Plana uygun, dokunmadan kalkış | Yerde pervanesiz, sonra alçak irtifada denenmesi şart (Faz 7.4 ve Faz 8 U2) |
| B | Pilot Loiter'da arm edip 3–5 m'ye kaldırır, sonra MP'den AUTO | Parametre değişmez | Kumandayla kalkış müdahale sayılabilir; YKİ'den ARM kullanılmaz |

**KARAR 2 — Telsiz koparsa ne olsun?** Bugünkü davranış: Jetson'daki MAVProxy TELEM2'den
saniyede bir yer istasyonu HEARTBEAT'i basar ve Pixhawk bunu yer istasyonu sayar
(`SYSID_MYGCS=255`). Bu yüzden **yalnız RFD koparsa GCS failsafe TETİKLENMEZ**; drone
göreve devam eder (`TUNEL_SAHA_RUNBOOK.md:34-37`). Öneri: böyle kalsın. Emniyet pilot
kumandası, çit (`FENCE`) ve pil failsafe'idir. Değiştirmek istersen bana yaz.

**KARAR 3 — `RC_SPEED`:** dökümde 490, ESC'nin (Skywalker 60A V2) kabul ettiği üst sınır 432 Hz
(`config/pixhawk/README.md:56-58`). 13–15 Eylül uçuşları 490 ile sorunsuz geçti. Öneri: 400
yapıp motor testini tekrarla. Karar sende.

---

## 1. Zaman planı

Süreler **HESAP**tır (her adımın tahmini süresi), ölçüm değildir.

| Ne zaman | Fazlar | Tahmini süre | Kapı |
|---|---|---|---|
| **Şimdi** (drone yapımdayken) | Faz 0 | 3–4 saat | Jetson kodu kurulu, kamera FOV ölçüldü, canlı FPS ≥ 0,61 |
| **Gün 1** (drone biter bitmez) | Faz 1 → Faz 2 → Faz 3 | 5–6 saat | Kalibrasyonlar tamam, failsafe'ler geçti, TELEM2 çift yönlü |
| **Gün 1 akşam** | Faz 4 → Faz 5 | 2 saat | `--kapi` 3/3, YKİ'de İHA yeşil |
| **Gün 2 sabah** | Faz 6 (K8) → Faz 7 | 4 saat | K8a ve K8b p95 < 0,20 s; YKİ'den ARM/DISARM/LAND çalışıyor |
| **Gün 2 öğleden sonra** | Faz 8 U1, U2 | 3 saat (şarj dahil) | Askı kabul testi geçti; AUTO kalkış/iniş ve YKİ'den LAND havada çalıştı |
| **Gün 3** | Faz 8 U3, U4 (×2–3) | tüm gün | 30 m'de rota YKİ'ye geldi; ≤ 10 dk tam prova |
| **20 Eylül** | Yolculuk; akşam kuru koşu (`--durum`, YKİ açılışı) | — | — |
| **21 Eylül** | Faz 9 | — | Görev |

**Pil kuralı:** iMAX B6 ile dolum ~3 saat (`SAHA_HAZIRLIK_PLANI_20260903.md` §4). Tek 4S 13 Ah
pille günde en fazla 2 uçuş planla.

---

## 2. FAZ 0 — Drone bitmeden masada yapılacaklar

**Amaç:** Drone bitince yalnız donanım işi kalsın. Jetson'u masada kendi adaptörüyle ya da drone
piliyle (pervanesiz) çalıştırabilirsin. Bilgisayar ile Jetson'u Ethernet kablosuyla bağla.

### 0.1 Bilgisayar kontrolü

**Ne:** Python ortamı ve genel kapı.
**Neden:** Sahada `python` komutu sessizce hiçbir şey yapmaz (Windows Store saplaması); yanlış
yorumlayıcı zaman kaybettirir.
**Nasıl** (PowerShell, `O:\navitas`):

```powershell
cd O:\navitas
$PY = "O:\navitas-local-train\venv\Scripts\python.exe"
& $PY -c "import serial, pymavlink; print('tamam')"
& $PY -B codes\test_rota_sentetik.py
mkdir results\saha_20260917
```

**Geçti sayılır:** `tamam` yazar; son satır `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`.
**Olmazsa:** çıktıyı bana gönder.

Mission Planner sürümünü de not et (Help → About); runbook 1.3.83 ile yazıldı.

### 0.2 Jetson kimliği

**Ne:** Kart, JetPack, Python ve kurulu ortamın 6 Eylül'de ölçülen düzenle aynı olduğunu doğrula.
**Neden:** Paket **Jetson Orin Nano Developer Kit 4 GB / JetPack 7.2.1 / Python 3.12 / `~/venv312`**
için yazıldı (`JETSON_ORIN_NANO_KURULUM.md:32-44`). Sen kartı "Nano NX" diye anıyorsun; kart ya da
kurulum farklıysa aşağıdaki komutların yolları değişir.
**Nasıl** (bilgisayardan `ssh <kullanici>@<jetson-ip>`, ya da Jetson'da terminal):

```bash
cat /proc/device-tree/model; echo
cat /etc/nv_tegra_release
python3 --version
ls -d ~/venv312 ~/navitas 2>&1
ls -l ~/.local/bin/mavproxy.py 2>&1; which mavproxy.py
groups
free -h
```

**Geçti sayılır:** model satırında `Orin Nano`; `R39`; Python 3.12; `~/venv312` var; `groups`
çıktısında `dialout` ve `video` var.
**Olmazsa:**

- Model/JetPack farklı → **DUR**, çıktıyı bana gönder. Paket yolları o karta göre düzeltilir.
- `~/venv312` yok → internet bağlıyken paketin kurulum betiklerini koş (Faz 0.3'ten sonra,
  `~/navitas_tunel/jetson_paket` içinde): `sudo bash orin_nano_root_kurulum.sh`, çıkış-giriş
  yap, sonra `bash orin_nano_venv_kurulum.sh`.
- `dialout` yok → `sudo usermod -aG dialout,video $USER`, sonra **oturumu kapatıp aç**
  (grup üyeliği ancak yeniden girişte etkinleşir).
- `mavproxy.py` yok ama `~/venv312/bin/mavproxy.py` var →
  `mkdir -p ~/.local/bin && ln -sf ~/venv312/bin/mavproxy.py ~/.local/bin/mavproxy.py`.

### 0.3 Paketi Jetson'a taşı ve kodu kur

**Ne:** `a81784c2` sürümünün Jetson kodunu `~/navitas` altına kur.
**Neden:** Tünel kipi için `comms/mavlink_tunel.py`, `seri_hub.py` ve `sik_rf_olc.py` gerekli.
Servisler kodu `~/navitas` altından çalıştırır.
**Nasıl:**

1. Bilgisayarda (PowerShell):

   ```powershell
   scp O:\teslim\navitas_tunel.tar <kullanici>@<jetson-ip>:~/
   scp O:\navitas\jetson_paket\models\navitas_seg_v36_best.pt <kullanici>@<jetson-ip>:~/
   ```

   Model dosyası pakette **yok** (depoda izlenmiyor), bu yüzden ayrıca gönderiliyor.

2. Jetson'da:

   ```bash
   cd ~ && tar -xf navitas_tunel.tar
   [ -d ~/navitas ] && cp -a ~/navitas ~/navitas_yedek_$(date +%Y%m%d_%H%M)
   mkdir -p ~/navitas/{codes,comms,scripts,models,config,results}
   cd ~/navitas_tunel/jetson_paket
   cp kod/rpi_inference.py kod/costmap_path_finder.py kod/karar_sozlesmesi.py kod/arac_maskesi.py kod/model_registry.py kod/kamera_dogrula.py kod/karisim_arena.yaml ~/navitas/codes/
   cp kod/protocol.py kod/link.py kod/iha_sender.py kod/inis_kaniti.py kod/iha_inis_yayinci.py kod/iha_komut_alici.py kod/seri_hub.py kod/mavlink_tunel.py ~/navitas/comms/
   cp kod/mavlink_dogrula.py kod/sik_rf_olc.py kod/kamera_koprusu.py kod/isaretli_gosterici.py kod/jetson_fps.py ~/navitas/scripts/
   cp config/model_registry.json ~/navitas/config/
   cp models/jetson_derleme_manifest.json ~/navitas/models/
   [ -f ~/navitas/models/navitas_seg_v36_best.pt ] || mv ~/navitas_seg_v36_best.pt ~/navitas/models/
   sha256sum ~/navitas/models/navitas_seg_v36_best.pt
   ```

**Geçti sayılır:** `sha256sum` çıktısı `1d1caca6` ile başlar, `cac46911` ile biter
(`jetson_paket/config/model_registry.json`).
**Olmazsa:** hash farklıysa model dosyası bozuk ya da farklı sürüm. `~/navitas_seg_v36_best.pt`
dosyasını `~/navitas/models/` altına kopyalayıp tekrar kontrol et.

### 0.4 Bağımlılık ve model kayıt kontrolü

**Ne:** Servislerin kullanacağı Python'da gerekli kütüphaneler var mı, model kayıt defteriyle
eşleşiyor mu?
**Neden:** Model yükleme **fail-closed**'dur. Kayıt defteri yoksa ya da ağırlık eşleşmezse
`rpi_inference` açılmaz (`codes/rpi_inference.py:577-583`, `JETSON_KILAVUZ.md:382-390`).
**Nasıl:**

```bash
~/venv312/bin/python -c "import cv2, numpy, ultralytics, serial, pymavlink; print('hepsi var')"
/usr/bin/python3 -c "import cv2; print('sistem cv2', cv2.__version__)"
cd ~/navitas && ~/venv312/bin/python - <<'PY'
import sys; sys.path.insert(0, "codes")
from rpi_inference import model_kayit_dogrula
ok, detay = model_kayit_dogrula("models/navitas_seg_v36_best.pt")
print("UYUMLU" if ok else "RED", detay)
PY
```

**Geçti sayılır:** `hepsi var`; sistem cv2 sürümü yazar; son komutun ilk kelimesi `UYUMLU`.
**Olmazsa:** `RED kayit_defteri_yok` → `~/navitas/config/model_registry.json` kopyalanmamış.
`--kayit-dogrulamasiz` bayrağı sahada **yasak**tır.

### 0.5 Kamera: görüntü, ayna testi, FOV ölçümü, canlı FPS

**Neden:** Rota kararındaki metre ölçeği `mpp = 2·h·tan(FOV/2)/W` ile hesaplanır
(`codes/karar_sozlesmesi.py:395-428`). FOV yanlışsa rota metreleri yanlış olur. FOV hiç
**ölçülmedi**; 55,3° yalnız lens hesabıdır (`ATOLYE_TEST_GUNU_20260912.md:144`). Kurulum
komutu (`jetson_baslat.sh`) FOV'u tahmin değil, **beyan** ister.

**a) CSI kamera görünüyor mu?**

```bash
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=1 ! fakesink
```

Hatasız bitmeli. `No cameras available` → §13-D.

**b) Kamera köprüsünü elle başlat** (terminal 1, açık kalsın):

```bash
/usr/bin/python3 ~/navitas/scripts/kamera_koprusu.py --port 8080 --fps 5
```

Terminal 2:

```bash
curl -s http://127.0.0.1:8080/durum; echo
~/venv312/bin/python ~/navitas/codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --kaydet ~/kamera_ilk_kare.jpg
```

**Geçti sayılır:** `/durum` içinde `"kaynak_acik": true`; `kamera_dogrula` sonunda
`OLCULEN FPS` ≥ 4, düşen kare ≤ %5, `cozunurluk 1280x720` (`SAHA_KOSUM_KAGIDI_20260910.md:19`).

**c) Ayna testi:** elini kadraja kameranın **solundan** sok, tekrar
`curl -s http://127.0.0.1:8080/kare.jpg -o ~/ayna.jpg` al. Bilgisayara çek
(`scp <kullanici>@<jetson-ip>:~/ayna.jpg results\saha_<tarih>\`) ve aç. El görüntüde de **solda**
olmalı. Sağdaysa §13-D. Kodda görüntü çevirme **yoktur** ve eklenmez
(`codes/rpi_inference.py:2344-2355`).

**d) FOV ölçümü (A9):**

1. Kamerayı düz bir yüzeye **dik** baktır. Drone'daki kamera aşağı baktığı için en kolayı:
   drone'u masaya koy, kamera yere baksın.
2. Lensten yüzeye mesafeyi şeritmetreyle ölç (`d`, metre). Örnek: 0,95 m.
3. Yüzeye iki bant işareti koy. Aralarındaki mesafe (`s`) yaklaşık `d/2` olsun ve ikisi de
   görüntünün **orta yarısında** kalsın. Örnek: 0,50 m.
4. Kare al: `curl -s http://127.0.0.1:8080/kare.jpg -o ~/fov.jpg`, sonra bilgisayara çek.
5. Paint'te aç. İmleci iki işaretin üstüne getir, alt çubuktaki **x** piksel değerlerini oku.
   Farkları `p`.
6. Bilgisayarda:

   ```powershell
   & $PY -B scripts\kamera_fov_hesapla.py --genislik-px 1280 --isaret-px <p> --isaret-m <s> --mesafe-m <d>
   ```

**Geçti sayılır:** çıktıdaki `FOV_yatay` **50–65°** arasında (`SAHA_KOSUM_KAGIDI_20260910.md:20`).
Değeri `results\saha_<tarih>\A9_fov.txt` dosyasına `d, s, p, FOV` olarak yaz. **Bu değer Faz 4'te
`FOV=` olarak kullanılır.**
**Olmazsa:** 50°'nin altında ya da 65°'nin üstündeyse ölçümü bir kez tekrarla (dik bakış,
mesafe). Yine dışındaysa bana gönder; sensör modu kırpıyor olabilir
(`ATOLYE_TEST_GUNU_20260912.md:144`).

**e) Canlı FPS (A10)** — köprü hâlâ açıkken:

```bash
~/venv312/bin/python ~/navitas/codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --zincir --model ~/navitas/models/navitas_seg_v36_best.pt --imgsz 512
```

**Geçti sayılır:** p50 **ve** p95 ≥ **0,61 FPS** (`ATOLYE_TEST_GUNU_20260912.md:164`).
6 Eylül ölçümü 1,35 / 1,06 FPS idi.
**Olmazsa:** `sudo nvpmodel -m 0 && sudo jetson_clocks`, tekrar ölç (§13-D).

**f) Köprüyü kapat:** terminal 1'de **Ctrl+C**. Açık kalırsa Faz 4'te 8080 portu çakışır.

**KAPI 0:** 0.1–0.5 hepsi GEÇTİ, FOV değeri yazılı.

---

## 3. FAZ 1 — Montaj sonrası mekanik ve elektrik kontrol

**Koşul:** pil **takılı değil**, pervane **takılı değil**. Her madde için fotoğraf çek
(`results\saha_<tarih>\foto\`).

| # | Ne | Neden | Nasıl | Geçti sayılır |
|---|---|---|---|---|
| 1.1 | **Kol ve motor bağlantıları** — önce **M4 (arka-sağ)**, sonra M1 (ön-sağ) | 15 Eylül loglarında sağ-arka yönde tutarlı statik itki dengesizliği görüldü (`results/ucus_analiz_20260915/RAPOR.md` §4; T279) | Kolu elle bur ve kaldır; vidaların tork işareti; motor mili gövde düzlemine dik mi | Boşluk yok, mil dik, vidalar sıkı |
| 1.2 | **Motor yatağı** | Hasarlı motor askıda doyuma girer (6 Eylül M1) | Her motoru elle çevir | Takılma ya da cızırtı yok |
| 1.3 | **Pervaneler** (takma, yalnız kontrol) | 4S + 9x5x3 seçildi (D-484) | 4 adet 9x5x3: 2 CW + 2 CCW, çatlak yok, somunlar yanında | Tam takım |
| 1.4 | **Pixhawk montajı** | `AHRS_ORIENTATION=0`: ok **ileri** bakmalı | Ok yönü, sönümleyici ped, vidalar, kablo gerginliği | Ok ileri, kart oynamıyor |
| 1.5 | **GPS direği** | Pusula GPS modülünde | Direk sağlam, ok ileri; yerini değiştirdiysen Faz 2'de pusula kalibrasyonu **şart** | Sağlam |
| 1.6 | **TELEM2 kablosu** | Yanlış pin Jetson'u ya da portu yakar | Aşağıdaki tablo; multimetrede süreklilik | Tablo birebir, **5 V boşta** |
| 1.7 | **Diğer kablolar** | 5 Eylül'de RC kablosu yanlış porttaydı | RFD → **TELEM1**; PM06 → **POWER1**; RC alıcısı `i-BUS SERVO` → Pixhawk `PPM/SBUS RC`; ESC sinyalleri **AUX1=M4, AUX2=M2, AUX3=M1, AUX4=M3** | Hepsi doğru portta |
| 1.8 | **ESC BEC kırmızı telleri** | 4 BEC paralel rayda olmamalı (D-428 §5f) | ESC servo fişlerinin kırmızı tellerine bak | En fazla bir ESC'nin kırmızı teli rayda |
| 1.9 | **Jetson güç hattı** | Jetson drone pilinden 12,2 V regülatörle besleniyor | Kutup yönü; regülatör çıkış kablosu sağlam; lehimler izoleli | Ters kutup yok, açık iletken yok |
| 1.10 | **Kamera** | Şerit kablo gevşekse görüntü kesilir | Şerit kilidi kapalı; lens temiz; aşağı bakıyor; odak halkası sabit | Sağlam |
| 1.11 | **Anten yerleşimi** | RFD menzili ve GPS | RFD antenleri dikey, pilin ve karbonun arkasında değil; Jetson ve USB3 kabloları GPS'ten mümkün olduğunca uzakta | — |
| 1.12 | **Serbest kablo** | Pervane alanına giren kablo koparır | Tüm kablolar bağlı, pervane dairesinin dışında | Hiçbiri pervane alanında değil |
| 1.13 | **Kütle (T280)** | Performans hesabı ölçülmemiş kütleye dayanıyor | Pil takılı, pervaneler takılı halde tart | Değer `results\saha_<tarih>\kutle.txt` dosyasına yazıldı |
| 1.14 | **Ağırlık merkezi** | Önde CG + yavaş gaz 6 Eylül devrilmesinin adaylarından | Pil takılıyken iki çapraz kol ucundan parmakla kaldır | Gövde yatay ya da çok hafif eğik |

**TELEM2 bağlantısı** (`SAHA_KOSUM_KAGIDI_20260910.md:11`):

| Pixhawk TELEM2 | Jetson 40 pin |
|---|---|
| pin 1 (5 V, kırmızı) | **BAĞLANMAZ** |
| pin 2 (TX) | pin 10 (UART RX) |
| pin 3 (RX) | pin 8 (UART TX) |
| pin 6 (GND) | pin 6 (GND) |

**KAPI 1:** 1.1–1.14 tamam, fotoğraflar klasörde.

---

## 4. FAZ 2 — Pixhawk: parametre, kalibrasyon, motor ve failsafe testleri

**Koşul:** **pervanesiz**. Parametre ve kalibrasyon için Pixhawk'a **USB kablosuyla** bağlan
(hızlı). Motor ve failsafe testleri için pil takılı olacak.

### 2.1 Firmware kontrolü

**Nasıl:** MP → COM (USB) → Connect → **Messages** sekmesi.
**Geçti sayılır:** `ArduCopter V4.5.7` görünür.
**Olmazsa:** farklı sürümse **DUR**. 4.5.7'ye sabitiz; 4.7 parametre dosyasının anlamını bozar
(`config/pixhawk/README.md` §0). Yükleme yalnız **Load custom firmware** ile yapılır, quad ikonuna
tıklanmaz. Firmware yüklemek tüm parametreleri siler; bana yaz.

### 2.2 Mevcut parametreleri yedekle

**Nasıl:** Config → **Full Parameter List** → **Save to file** →
`results\saha_<tarih>\param_once_<SSDD>.param`.
**Neden:** Yanlış bir yazmada geri dönüş noktası.

### 2.3 4S parametre setini yaz

**Neden:** Pixhawk'ta hâlâ 3S değerleri var. `BATT_LOW_VOLT 10` / `BATT_CRT_VOLT 9`, 4S'te hücre
başına 2,5 / 2,25 V demektir, yani **pil failsafe'i fiilen kapalıdır**
(`results/ucus_analiz_20260915/RAPOR.md:166`).
**Nasıl:** Full Parameter List'te arama kutusuna adı yaz → değeri gir → hepsi bitince
**Write Params** → **Refresh Params** → her değeri tek tek kontrol et. Liste **Ek A**'dadır:

- Zorunlu: `BATT_CAPACITY 13000`, `BATT_LOW_VOLT 14.0`, `BATT_CRT_VOLT 13.2`,
  `BATT_FS_VOLTSRC 1`, `BATT_ARM_VOLT 14.4`
- Test uçuşları için: `LOG_BITMASK 180222`, `INS_LOG_BAT_MASK 1`
- KARAR 1 A seçildiyse: `AUTO_OPTIONS 3`
- KARAR 3 kabul edildiyse: `RC_SPEED 400`
- `MOT_THST_HOVER`: **önce oku**. 0,33–0,40 arasındaysa dokunma. 0,5 civarındaysa (3S değeri)
  `0.39` yaz (15 Eylül 4S askısında öğrenilen değer 0,3895).

Sonra Pixhawk'ı yeniden başlat (Config → Full Parameter List üstündeki **Reboot**, ya da USB çek-tak),
**Refresh Params**, değerler kaldı mı bak, **Save to file** →
`param_sonra_<SSDD>.param`.
**Geçti sayılır:** yeniden başlatmadan sonra tüm değerler yazdığın gibi.

### 2.4 Pil gerilimi doğrulaması

**Neden:** `BATT_VOLT_MULT` 15 Eylül'de 9 kez değiştirildi; failsafe eşikleri bu ölçüme bağlı.
**Nasıl:** Pili tak. Multimetreyle pil gerilimini ölç, MP HUD'daki gerilimle karşılaştır.
**Geçti sayılır:** fark ≤ 0,1 V (`config/pixhawk/README.md:137-139`).
**Olmazsa:** Setup → Optional Hardware → **Battery Monitor** → *Measured Battery Voltage*
kutusuna multimetre değerini yaz, Enter. Tekrar karşılaştır. Bunu **bir kez** yap, sonra dokunma.

### 2.5 Kalibrasyonlar

Montaj yenilendiği için dördü de yapılır.

| Adım | Menü | Nasıl | Geçti sayılır |
|---|---|---|---|
| **a. Akselerometre** | Setup → Mandatory Hardware → **Accel Calibration** → *Calibrate Accel* | MP'nin istediği 6 yönde drone'u sırayla koy, her birinde tuşa bas. Sonra düz zeminde *Calibrate Level* | `Calibration successful` |
| **b. Pusula** | Setup → Mandatory Hardware → **Compass** → *Onboard Mag Calibration* → **Start** | **Dışarıda**, metal ve araçlardan uzak. **Jetson açık ve pil takılı** (Jetson ve regülatör manyetik alan üretir). Drone'u her eksende tam tur çevir | Tüm pusulalar yeşil; ardından **reboot** |
| **c. Kumanda** | Setup → Mandatory Hardware → **Radio Calibration** | Tüm çubukları uçlara, tüm anahtarları her konuma getir → *Click when Done* | Her kanal ~1000–2000 aralığını kapsıyor |
| **d. Uçuş modları** | Setup → Mandatory Hardware → **Flight Modes** | CH5 anahtarının her konumunda yeşil satırı oku | Her konumun modu kayıtlı (döküm: Stabilize / Loiter / Land) |

**ESC kalibrasyonu** yalnız ESC ya da motor değiştiyse yapılır. 6 Eylül'de tutan sıra: POWER1
çıkarılır, yalnız USB, passthrough, sonra pil (`config/pixhawk/README.md` §2.1:104-110). O bölümü
okumadan başlama.

### 2.6 Motor sırası ve yön testi (pervanesiz, video çek)

**Neden:** Yanlış sıra ya da yön kalkışta anında devrilme demektir.
**Nasıl:** Pil takılı, **disarmed**. Setup → Optional Hardware → **Motor Test** → Throttle %10,
Duration 2 s. Her harfe ayrı bas. Motor tepesine küçük bir bant parçası yapıştır, dönüş yönünü
gör.

| Düğme | Motor | Konum | Yön |
|---|---|---|---|
| **A** | M1 | sağ-ön | CCW (saat yönünün tersi) |
| **B** | M4 | sağ-arka | CW |
| **C** | M2 | sol-arka | CCW |
| **D** | M3 | sol-ön | CW |

(`SAHA_KOSUM_KAGIDI_20260910.md:46`; üstten bakınca.) Ardından **Test all motors** %10:
dördü aynı anda başlamalı, aynı ses.
**Geçti sayılır:** 4/4 doğru konum ve yön; video `results\saha_<tarih>\motor_testi.mp4`.
**Olmazsa:** konum yanlış → `SERVO9..12_FUNCTION` değerlerine bak (36/34/33/35 olmalı) ya da
ESC sinyal fişleri yanlış AUX'ta. Yön yanlış → o motorun 3 faz kablosundan **ikisinin** yerini
değiştir. Biri geç başlıyorsa → ESC kalibrasyonu (§2.5 not).

### 2.7 PreArm temizliği

**Nasıl:** Dışarıda, pil takılı, GPS kilitlenene kadar bekle. MP **Messages**.
**Geçti sayılır:** `PreArm:` satırı yok; HUD'da GPS 3D fix, uydu ≥ 12, HDop < 1,0
(`RAPOR.md` §5.3 ön koşul).
**Olmazsa:** mesaja göre §13-A.

### 2.8 Failsafe testleri (pervanesiz)

| Test | Neden | Nasıl | Geçti sayılır |
|---|---|---|---|
| **A1 Kumanda failsafe** | Kumanda koparsa drone inmeli (`FS_THR_ENABLE=3` → LAND) | Stabilize'de arm et, gaz en altta → kumandayı **kapat** | ≤ 2 s içinde MP'de `Radio Failsafe` mesajı; mod LAND ya da disarm. Kumandayı aç, mod geri alınabiliyor |
| **A3 Pil failsafe** | 4S eşikleri gerçekten çalışıyor mu | `BATT_LOW_VOLT`'u geçici olarak **ölçülen gerilim + 0,5** yap → Write. Arm et (pervanesiz). ~10 s bekle (`BATT_LOW_TIMER=10`) | ≤ 12 s içinde `Battery 1 is low` + LAND/disarm. **Sonra `BATT_LOW_VOLT`'u 14.0'a geri yaz, Write, Refresh, ekran görüntüsü al** |
| **A4 CH6 disarm** | Son çare anahtarı | Arm et (pervanesiz) → CH6 anahtarı | Motorlar anında durur, `DISARMED`. 3 kez tekrarla, 3/3 |
| **Çit** | 50 m tavan, 60 m yarıçap | Full Parameter List: `FENCE_ENABLE 1`, `FENCE_ALT_MAX 50`, `FENCE_RADIUS 60`, `FENCE_ACTION 1` | Değerler doğru (14.09 dökümünde öyle) |

**A3'ün geri alınması zorunludur.** 12 Eylül'de eşikler geri alınmadan kalmıştı
(REVIEW_LOG D-473).

**KAPI 2:** 2.1–2.8 GEÇTİ; `param_sonra_*.param` klasörde; A3 geri alma ekran görüntüsü var.

---

## 5. FAZ 3 — Jetson ↔ Pixhawk TELEM2 bağlantısı

**Koşul:** pervanesiz, pil takılı, Jetson açık, Ethernet ile SSH bağlı.

### 3.1 Pixhawk parametrelerini oku (değiştirme)

**Nasıl:** MP → Full Parameter List. Değerleri `results\tunel_<tarih>\K8_0.txt` dosyasına yaz.

| Parametre | Olması gereken | 14.09 dökümü |
|---|---|---|
| `SERIAL1_PROTOCOL` / `SERIAL2_PROTOCOL` | 2 / 2 | 2 / 2 |
| `SERIAL1_BAUD` / `SERIAL2_BAUD` | 57 / 57 | 57 / 57 |
| `SERIAL1_OPTIONS` / `SERIAL2_OPTIONS` | bit10 = 0 | 0 / 0 |
| `BRD_SER2_RTSCTS` | 0 (3 tel) | 0 |
| `SYSID_THISMAV` / `SYSID_MYGCS` | 1 / 255 | 1 / 255 |
| `SR2_POSITION` | ≥ 8 | 8 |
| `FS_GCS_ENABLE` / `FS_GCS_TIMEOUT` | kayıt | 5 / 5 |

`SR1_*` değerlerinin hepsini de yaz (telsiz bant bütçesi için).
**Olmazsa:** farklı olan varsa **yazmadan önce** bana gönder.

### 3.2 İki yönlü bağlantı testi

**Neden:** Pixhawk → Jetson (telemetri) ve Jetson → Pixhawk (komut) iki ayrı teldir; biri kopuk
olabilir.
**Nasıl** (Jetson). Önce portu tutabilecek servisleri durdur:

```bash
sudo systemctl stop navitas-cogullayici navitas-seri-hub 2>/dev/null
ls -l /dev/ttyTHS* /dev/ttyTCU*
systemctl status nvgetty 2>/dev/null | head -n 3; cat /proc/cmdline | tr ' ' '\n' | grep -i console
```

Sonra bloğun **tamamını** tek seferde yapıştır:

```bash
~/venv312/bin/python - <<'EOF'
from pymavlink import mavutil
for dev in ("/dev/ttyTHS1", "/dev/ttyTHS0"):
    try:
        m = mavutil.mavlink_connection(dev, baud=57600, source_system=254)
    except Exception as e:
        print(dev, "ACILAMADI:", e); continue
    hb = m.recv_match(type="HEARTBEAT", blocking=True, timeout=6,
                      condition="HEARTBEAT.autopilot != 8")
    print(dev, "Pixhawk->Jetson:", ("VAR sysid=%d" % hb.get_srcSystem()) if hb else "YOK")
    if hb:
        m.mav.param_request_read_send(hb.get_srcSystem(), hb.get_srcComponent(), b"SYSID_THISMAV", -1)
        p = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=5)
        print(dev, "Jetson->Pixhawk:", ("VAR %s=%s" % (p.param_id, p.param_value)) if p else "YOK")
    m.close()
EOF
```

**Geçti sayılır:** bir portta iki satır da `VAR` (`Pixhawk->Jetson: VAR sysid=1` ve
`Jetson->Pixhawk: VAR SYSID_THISMAV=1.0`). Çıktıyı `results\tunel_<tarih>\03_telem2.txt`
dosyasına kaydet. **Hangi port çalıştıysa Faz 4'te `PIXHAWK_SERI` odur.**
**Olmazsa:**

| Belirti | Neden | Yapılacak |
|---|---|---|
| `Permission denied` | Kullanıcı `dialout` grubunda değil | Aynı bloğu `sudo ~/venv312/bin/python - <<'EOF'` ile koş; kalıcı çözüm Faz 0.2 |
| İki portta da `Pixhawk->Jetson: YOK` | Pixhawk TX → Jetson pin 10 teli, GND ya da parametre | Tel sürekliliği; `SERIAL2_PROTOCOL=2`, `SERIAL2_BAUD=57`; `nvgetty` o portu tutuyorsa `sudo systemctl stop nvgetty` |
| `Pixhawk->Jetson: VAR` ama `Jetson->Pixhawk: YOK` | Jetson pin 8 → Pixhawk pin 3 teli | Tel sürekliliği ve lehim |
| `ACILAMADI: No such file` | Port adı farklı | `ls -l /dev/ttyTHS*` çıktısını bana gönder |

**KAPI 3:** bir portta iki yön `VAR`.

---

## 6. FAZ 4 — Jetson servislerinin kurulumu (KIP=tunel)

### 4.1 Ortam değişkenleri ve kuru koşu

**Ne:** Servisleri kurmadan önce ne kurulacağını gör.
**Neden:** Runbook §3'teki komut `PYTHON3`, `NAVITAS_KOK` ve `KAMERA` değişkenlerini vermiyor.
Verilmezse servisler `/usr/bin/python3` ile kalkar ve `pymavlink`/`ultralytics` bulunamaz
(`jetson_paket/jetson_baslat.sh:120`, `JETSON_NANO_KURULUM.md:489-490`). Kamera köprüsü de hiç
kurulmaz (`jetson_baslat.sh:108,185-196`). Aşağıdaki komut **doğru biçimdir**.
**Nasıl:**

```bash
cd ~/navitas_tunel
export PATH=$HOME/.local/bin:$PATH
export KIP=tunel PIXHAWK_SERI=/dev/ttyTHS1 PIXHAWK_BAUD=57600 SYSID=1
export FOV=<Faz 0.5d'de ölçülen derece>
export KAMERA=http://127.0.0.1:8080/video
export NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python
bash jetson_paket/jetson_baslat.sh --kuru
```

Faz 3'te `ttyTHS0` çalıştıysa `PIXHAWK_SERI=/dev/ttyTHS0` yaz.

**Geçti sayılır:**

- Son satır `KURU SONUC: tamam`; çıkış kodu 0 (`echo $?` → 0).
- `[YOK]` ya da `[EKSIK]` satırı yok.
- ExecStart satırlarında **`/home/<kullanici>/venv312/bin/python`** görünür; kamera köprüsü
  satırında `/usr/bin/python3` olması **doğrudur**.
- `[DOGRULA]` listesi yazılır (sayılmaz; Faz 3'te yaptıkların).

**Olmazsa:** çıkış kodu 3 → `[YOK]` satırlarını oku, §13-C.

### 4.2 Kur ve kapıdan geçir

**Ne:** Servisleri kur, MAVProxy'yi başlat, üç MAVLink çıkışını doğrula, sonra tüketicileri başlat.
**Nasıl** (aynı terminalde, değişkenler hâlâ tanımlıyken):

```bash
sudo -E bash jetson_paket/jetson_baslat.sh --kapi
```

**Geçti sayılır:** üç satır `[GECTI] udp:127.0.0.1:14550`, `…:14551`, `…:14552`; ardından
tüketiciler başlatılır. Kapı her çıkışta şunlara bakar: 15 s içinde sysid 1 HEARTBEAT; 10 s
pencerede `GLOBAL_POSITION_INT` ≥ 4 Hz, `EXTENDED_SYS_STATE` ≥ 1 Hz, HEARTBEAT ≥ 0,5 Hz
(`scripts/mavlink_dogrula.py`, `codes/karar_sozlesmesi.py:2216-2222`).
**Olmazsa:** `kapi N/3 — tuketiciler BASLATILMADI` → §13-C.

### 4.3 Doğrulamalar

```bash
ps -ef | grep '[m]avproxy'
bash ~/navitas_tunel/jetson_paket/jetson_baslat.sh --durum
journalctl -u navitas-seri-hub -n 20 --no-pager
journalctl -u navitas-rpi-inference -n 30 --no-pager
journalctl -u navitas-iha-inis-yayinci -n 20 --no-pager
curl -s http://127.0.0.1:8080/durum; echo
```

**Geçti sayılır:**

- MAVProxy satırı `--out udp:127.0.0.1:14553 --streamrate -1` ile **bitiyor**.
- `--durum`: altı birim `active`, `NRestarts=0`. **2 dakika sonra tekrar koş: hâlâ 0.**
- seri-hub günlüğünde `akran ogrenildi`.
- rpi-inference günlüğünde model yüklendi; yerde `NO_ROUTE` / `OLCEK_YOK` görülmesi **normaldir**:
  yerde bağıl irtifa ≈ 0, ölçek hesaplanamaz.
- inis-yayinci günlüğünde yerdeyken `IHA_LANDED yayınlandı` görülmesi **normaldir** (Faz 9.2).
- `/durum` → `"kaynak_acik": true`.

### 4.4 Yeniden başlatma dayanıklılığı

**Nasıl:** `sudo reboot`. Açılınca 2 dakika bekle, `--durum`.
**Geçti sayılır:** tüm birimler kendiliğinden `active`.
**Not:** Pixhawk yeniden başladığında (pil değişimi) **`--kapi` yeniden koşulur** (Faz 7.5).

**KAPI 4:** `--kapi` 3/3; `--durum` 2 dk sonra 0 restart; reboot sonrası birimler ayakta.

---

## 7. FAZ 5 — YKİ (bu bilgisayar) kurulumu

### 5.1 Mission Planner'ı telsizle bağla

1. RFD900A yer modülünü USB'ye tak. Aygıt Yöneticisi → Bağlantı noktaları → `COMx` numarasını not et.
2. RFD LED'leri: yeşil **sabit** = iki modül eşleşti; yeşil **yanıp sönüyor** = eşleşme aranıyor.
3. MP sağ üst: `COMx`, **57600** → **Connect**.

**Geçti sayılır:** parametreler iner, HUD hareket eder, harita konumu gelir.
**COM portunun tek sahibi MP'dir.** Aynı portu başka program açmaz.

### 5.2 MAVLink aynası

**Ne:** MP, telsizden gelen tüm MAVLink paketlerini yerel bir UDP portuna kopyalar; `yks_gui` oradan
okur ve oradan yazar.
**Nasıl:** Flight Data ekranında **Ctrl+F** → **Mavlink** (MAVLink Mirror) düğmesi → tür
**UDP Client**, host `127.0.0.1`, port `14570`, **Write access** kutusu **işaretli** → Connect.
Pencerenin ekran görüntüsünü `results\tunel_<tarih>\K8_0_ayna.png` olarak kaydet.
**Not:** Menü yolu MP program dizgelerinden çıkarıldı, sahada **ilk kez** doğrulanacak
(`TUNEL_SAHA_RUNBOOK.md:82`). Düğme adı farklıysa ekranın fotoğrafını bana gönder.

### 5.3 YKİ'yi aç

```powershell
cd O:\navitas
$PY = "O:\navitas-local-train\venv\Scripts\python.exe"
& $PY -B comms\yks_gui.py --tunel 127.0.0.1:14570 --fda
```

`--ika`, `--iha` ve `--demo` bu kipte **verilmez**; verilirse program hata verip kapanır
(`comms/yks_gui.py:5120-5128`).

**Geçti sayılır:**

- Alt çubuk: `Taşıyıcı: MAVLink TUNNEL (Pixhawk TELEM1 → RFD900A)`.
- Sağdaki **BAĞLANTI / DÜĞÜM DURUMU**'nda İHA noktası birkaç saniyede **yeşil**: heartbeat < 3 s
  **ve** Pixhawk canlı.
- **HAM GNSS** satırında lat/lon ve uydu sayısı; değerler MP ile aynı.
- Mod satırı `STABILIZE … ⚠AUTO DIŞI` (yerde normal).
- Mesaj günlüğünde yerde `NO_ROUTE` (sebep `OLCEK_YOK`) ve `IHA_LANDED` görülür; ikisi de ACK'lenir.
- Kanıt kaydı `results\prova\<tarih_saat>_<pid>\hakem_log.jsonl` oluşur.

**Olmazsa:** §13-E.

**KAPI 5:** İHA yeşil, HAM GNSS MP ile aynı, günlükte `NO_ROUTE` ve `IHA_LANDED` görülüyor.

---

## 8. FAZ 6 — Tünel ölçümü (K8) — uçuştan önce zorunlu

**Neden:** Mission Planner telemetrisi ile NAVITAS mesajları **aynı 57600 baud telsizi** paylaşıyor.
YKİ komutlarının tekrar aralığı 0,20–0,25 s. Gidiş-dönüş gecikmesi bundan uzunsa komutlar üst
üste biner. Benzetim (K4) 30 noktalı rotada düştü; **gerçek hüküm bu ölçümdür**. Ölçülmeden
uçuş testine geçilmez.

**Ölçüm sırasında bu bilgisayarda ağır iş koşma:** test süiti, model eğitimi, tarayıcıda video.
Gecikmeyi bozar.

Jetson komutları runbook'tan farklı olarak `python3` yerine **`~/venv312/bin/python`** ile
yazıldı; sistem Python'unda `pymavlink` olmayabilir (Faz 4.1 nedeni).

### 6.1 K8-0 (i) — MP aynasının paket sınırları

`yks_gui` **kapalı**. İki kayıt, her biri **60 s**, sonra Ctrl+C:

```powershell
mkdir results\tunel_<tarih>
& $PY -B scripts\sik_rf_olc.py --rol yanki --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --tunel-ayristirma akis --json --cikti results\tunel_<tarih>\K8_0_i_ayna_akis.json
& $PY -B scripts\sik_rf_olc.py --rol yanki --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --tunel-ayristirma datagram --json --cikti results\tunel_<tarih>\K8_0_i_ayna_datagram.json
```

**Geçti sayılır** (hepsi birden, `TUNEL_SAHA_RUNBOOK.md:124-131`):

- İki JSON'da da `datagram_siniri.hizasiz = 0` ve `datagram_siniri.hizali ≥ 1`.
- İki JSON'da da `tunel_sayac.cozum_hatasi = 0`.
- `mavlink_paket / alinan_datagram` oranı iki dosyada ±%5 içinde eşit.

Bu ölçütü kendin hesaplama; JSON'ları bana gönder, birlikte bakalım.

### 6.2 K8a — ham tünel gecikmesi

**Jetson** (hub durur, MAVProxy çalışır):

```bash
sudo systemctl stop navitas-seri-hub
~/venv312/bin/python ~/navitas/scripts/sik_rf_olc.py --rol yanki --tasiyici tunel --tunel-bind 127.0.0.1:14553 --tunel-kimlik hava --json --cikti ~/K8a_hava_yanki.json
```

**Bilgisayar:** önce kısa deneme (K8-0 ii), sonra asıl ölçüm:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 20 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8_0_ii_kisa.json
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 200 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8a_tunel_rtt.json
```

Bitince Jetson'da **Ctrl+C** (hava JSON'u o an yazılır), sonra:

```bash
sudo systemctl start navitas-seri-hub
```

Bilgisayara çek: `scp <kullanici>@<jetson-ip>:~/K8a_hava_yanki.json results\tunel_<tarih>\`.

**Geçti sayılır:** `K8a_tunel_rtt.json` içinde `rtt_ms.p95 < 200`; hava JSON'unda
`tunel_sayac.bozuk_parca = 0` ve `tutarsiz_parca = 0`. Aracın çıkış kodu 0 = UYUMLU,
1 = UYARI, 2 = ÖLÇÜLEMEDİ (`scripts/sik_rf_olc.py:148`).

### 6.3 K8b — üretim yolu gecikmesi

**Ön koşul:** MAVProxy en az 60 s önce başlamış olmalı.
**Jetson, terminal 1** (hub'ı elle, ek yankı tüketicisiyle çalıştır):

```bash
sudo systemctl stop navitas-seri-hub
~/venv312/bin/python ~/navitas/comms/seri_hub.py --tunel 127.0.0.1:14553 --tunel-kimlik hava --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007 --tuketici 127.0.0.1:5190
```

**Jetson, terminal 2:**

```bash
~/venv312/bin/python ~/navitas/scripts/sik_rf_olc.py --rol yanki --tasiyici udp --bind 127.0.0.1:5190
```

**Bilgisayar:**

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 200 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8b_uretim_rtt.json
```

Ölçüm mesajı (`RF_PROBE`) komut alıcısı tarafından yok sayılır; Pixhawk'a komut gitmez
(`TUNEL_SAHA_RUNBOOK.md:186-187`).

**Geçti sayılır:** `rtt_ms.p95 < 200`.

### 6.4 Çok parçalı kayıtlar (kapı dışı ama **zorunlu**)

**Neden:** Uzun rota mesajı (30 nokta = 473 B) 4 parçaya bölünür. Benzetimde tam burada düştü.
Aynı düzenekle (terminal 1 ve 2 açık), bilgisayarda:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 100 --aralik 0.25 --prob-dolgu 165 --json --cikti results\tunel_<tarih>\K8_cok_parca_165.json
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 100 --aralik 0.25 --prob-dolgu 473 --json --cikti results\tunel_<tarih>\K8_cok_parca_473.json
```

**Hava → yer 473 B ACK:** Jetson terminal 2'yi Ctrl+C ile kapat, yerine:

```bash
~/venv312/bin/python ~/navitas/scripts/sik_rf_olc.py --rol yanki --tasiyici udp --bind 127.0.0.1:5190 --ack-dolgu 473 --json --cikti ~/K8_hava_yer_ack_473.json
```

Bilgisayarda:

```powershell
& $PY -B scripts\sik_rf_olc.py --rol olc --tasiyici tunel --tunel-bind 127.0.0.1:14570 --tunel-kimlik yer --n 100 --aralik 0.25 --json --cikti results\tunel_<tarih>\K8_hava_yer_ack_473.json
```

Bitince iki Jetson terminalini Ctrl+C ile kapat ve üretim düzenine dön:

```bash
sudo systemctl start navitas-seri-hub
bash ~/navitas_tunel/jetson_paket/jetson_baslat.sh --durum
```

Her kayıttan sonra hub sayaç satırını da al:
`journalctl -u navitas-seri-hub | grep "tunel sayac" | tail -n 1`.

### 6.5 K8-0 (iii)–(v) — dayanıklılık

| Test | Nasıl | Kaydet |
|---|---|---|
| **(iii) 10 dk sürekli** | Üretim düzeni, `yks_gui --tunel … --fda` açık, 10 dakika bekle | Başta ve sonda: hub `tunel sayac` satırı (`gonderilen_parca`, `bozuk_parca`, `tutarsiz_parca`, `zaman_asimi_dusen`, `kimlik_boslugu`); MP Ctrl+F bağlantı istatistikleri (kayıp, bozuk paket); YKİ günlüğündeki kırmızı `TÜNEL SAYAÇ ARTIŞI` satırları |
| **(iv) YKİ kapat/aç** | `yks_gui`'yi kapat, MP 60 s bağlı kalsın, YKİ'yi yeniden aç | ≤ 5 s içinde İHA yeşil mi |
| **(v) MP kapat/aç** | MP'yi kapatıp aç, yeniden bağlan | Ayna ayarı kalıcı mı? Kalıcı değilse her açılışta 5.2 **zorunlu** adımdır |

### 6.6 Hüküm

**K8 GEÇTİ = K8a p95 < 0,20 s VE K8b p95 < 0,20 s** (`TUNEL_SAHA_RUNBOOK.md:241`). Eşik
gevşetilmez. Tüm JSON'ları bana gönder; ben de `REVIEW_LOG`'a işleyeceğim.

**Düşerse** (runbook §9 sırası; her adım yeni ölçüm ister):

1. Sayaçlara bak: `kimlik_boslugu` ve `zaman_asimi_dusen` artıyor mu (kayıp), MP bozuk paket sayıyor mu.
2. MP'nin telsizden istediği akışları azalt: `SR1_EXTRA1`, `SR1_EXTRA2`, `SR1_RAW_SENS`,
   `SR1_EXT_STAT`, `SR1_RC_CHAN` (bugün 4/4/2/2/2). **Değiştirmeden önce bana yaz**; birlikte seçelim.
3. RFD Air Speed / `SERIAL2_BAUD` değişikliği — kullanıcı kararı.
4. Son çare: ikinci telsiz çifti (`KIP=sik`).

**KAPI 6:** K8 GEÇTİ; çok parçalı kayıtlar ve (iii)–(v) klasörde.

---

## 9. FAZ 7 — Yerde tam zincir provası (pervanesiz)

**Koşul:** **pervanesiz**, pil takılı, dışarıda (GPS), üretim düzeni (Faz 4 ve Faz 5), MP ve YKİ açık.
Her testi YKİ ekranından video çekerek yap: `results\saha_<tarih>\zincir_<test>.mp4`.

### 7.1 Telemetri doğruluğu

**Nasıl:** YKİ'deki HAM GNSS lat/lon, uydu sayısı, pil gerilimi ve mod değerlerini MP ile karşılaştır.
**Geçti sayılır:** aynı değerler; YKİ ≤ 1–2 s geride.

### 7.2 YKİ'den ARM / DISARM (3 tekrar)

**Neden:** "YKİ'den drone'u kontrol" hedefinin ilk kanıtı.
**Nasıl:**

1. MP'de mod **Stabilize**, gaz çubuğu en altta, `PreArm` mesajı yok.
2. YKİ'de **ARM (A)** düğmesine bas. Düğme `…? TEKRAR BAS` yazar. **4 s içinde tekrar bas.**
3. Motorlar rölantide döner (pervanesiz). YKİ düğmesi ancak Pixhawk ACK'i **ve** ardından gelen
   `armed` heartbeat'i gelince `DISARM (A)` olur.
4. **DISARM (A)**: iki basış. Motorlar durur.

**Geçti sayılır:** 3/3 ARM ve 3/3 DISARM; her birinde MP HUD aynı durumu gösterir. Jetson'da
`journalctl -u navitas-iha-komut-alici -n 30 --no-pager` çıktısında `[IHA_KOMUT]` satırları
görünür.
**Olmazsa:**

- Düğme **gri** → YKİ'ye taze `armed` bilgisi gelmiyor. Bu bilgi `rpi_inference` heartbeat'inde
  taşınır (`codes/rpi_inference.py:2656-2660`); servis çalışıyor mu kontrol et.
- `İHA ONAY VERMEDİ` → MP Messages'ta `PreArm`/`Arm` sebebini oku (§13-A). İlk basış saat farkı
  yüzünden reddedilebilir; ikinci kez dene (`results/faz_b_oncesi/CUMA_KONTROL_KARTI.md:94-103`).

### 7.3 YKİ'den ACİL LAND

**Nasıl:** YKİ'den ARM et (7.2) → **ACİL LAND** düğmesine 4 s içinde iki kez bas.
**Geçti sayılır:** Pixhawk modu LAND olur; yerde olduğu için kısa sürede disarm eder. YKİ uçuş
durumu satırı kırmızı `ACİL EMNİYET MODU (RTL/LAND)` gösterir.
**ACİL RTL yerde denenmez:** RTL, `RTL_ALT=35 m`'ye tırmanmaya çalışır. Havadaki denemesi
Faz 8 U2'dedir (isteğe bağlı).

### 7.4 KARAR 1 A seçildiyse: AUTO'da ARM ve kalkış başlangıcı

**Nasıl:**

1. MP **Plan** ekranında kısa bir deneme görevi hazırla: TAKEOFF 5 m → LOITER_TIME 20 s → LAND.
   **Write WPs**.
2. MP Flight Data → **Actions** sekmesi → mod listesinden **AUTO** → *Set Mode*.
3. YKİ'den ARM (iki basış).

**Geçti sayılır:** Pixhawk AUTO'da arm eder ve motor devri **rölantiden yükselmeye başlar**
(kalkış başladı). **O anda** YKİ'den DISARM (iki basış) ya da MP'den Disarm. Pervanesiz olduğu
için drone yerinden kalkmaz.
**Olmazsa:** `Arm: Mode not armable` → `AUTO_OPTIONS` yazılmamış. Arm ediyor ama devir
yükselmiyorsa → bit1 eksik (`AUTO_OPTIONS=3` olmalı) ya da görev yüklenmemiş.

### 7.5 Telsiz ve Jetson kopma davranışı

| Deneme | Nasıl | Beklenen |
|---|---|---|
| **RFD kopması** | Yer RFD USB'sini çek, 10 s bekle, tak | YKİ'de İHA noktası ~3 s'de **kırmızı** `(BAĞLANTI KAYBI!)`; MP bağlantı kaybı. Takınca MP yeniden bağlanır; ayna gerekiyorsa yeniden açılır; YKİ yeşile döner. **Pixhawk GCS failsafe'e GEÇMEZ** (Jetson heartbeat basıyor — KARAR 2) |
| **Jetson zinciri kopması** | Jetson'da `sudo systemctl stop navitas-cogullayici` → 10 s → `sudo -E bash ~/navitas_tunel/jetson_paket/jetson_baslat.sh --kapi` (değişkenler tanımlıyken) | YKİ İHA kırmızı; **MP bağlı kalır** (telsiz Pixhawk'ta). `--kapi` 3/3 sonrası YKİ yeşile döner |

### 7.6 Pil değişimi (Pixhawk yeniden başlaması) yordamı

**Neden:** Her pil değişimi Pixhawk'ı yeniden başlatır; akış istekleri silinir (D-406 A).
**Nasıl** (`TUNEL_SAHA_RUNBOOK.md` §5):

1. Pili çıkar, yenisini tak. Jetson servislerine **dokunma**.
2. MP ≤ 5 s içinde yeniden bağlanmalı.
3. `journalctl -u navitas-seri-hub -n 20 --no-pager`: araç heartbeat'iyle akran doğrulanmış olmalı.
4. `sudo -E bash ~/navitas_tunel/jetson_paket/jetson_baslat.sh --kapi` → **3/3**.
5. Gecikme ölçümü ya da uçuş için `--kapi`'den sonra **en az 60 s** bekle.

**Geçti sayılır:** 3/3, YKİ İHA yeşil, geçen toplam süre kayıtlı (görev günü planı için).
**Dikkat:** Jetson da aynı pilden beslendiği için pil değişiminde **Jetson da kapanır**. O durumda
Jetson açılışını (1–2 dk) bekle, sonra 4. adıma geç.

### 7.7 Rota zinciri (el ile yükseltme, isteğe bağlı ama önerilir)

**Neden:** Yerde irtifa ≈ 0 olduğu için rota hep `OLCEK_YOK` çıkar. Gerçek ölçekli rotayı uçmadan
görmenin tek yolu drone'u yükseltmek.
**Nasıl:** **Disarmed**, pervanesiz. Drone'u balkondan ya da merdivenden 3–5 m yükseklikte, kamerası
aşağıda, altında zemin görünecek şekilde tut.
**Geçti sayılır:** YKİ günlüğünde `OPEN_ROUTE` ya da `NO_ROUTE` sebep `KARAR_YOK` / `ROTA_GEOMETRI`
(yani `OLCEK_YOK` **değil**) görülür. Bir rota geldiyse **hakem onayı** akışını dene:
`1) TESPİTİ DOĞRULA` → `2) … ONAYLA → ACK`. FDA kipinde İKA kanıtı aranmaz.

### 7.8 GPS / pusula girişimi

**Nasıl:** Dışarıda, pil takılı. MP'de uydu sayısı ve HDop değerlerini not et. Jetson'un güç
fişini çek, 1 dakika bekle, tekrar not et. Jetson'u tak.
**Geçti sayılır:** Jetson açıkken uydu sayısı ve HDop, kapalıyken ölçülenle **belirgin fark
göstermiyor**. Eşik repoda tanımlı değil; iki değeri yaz, birlikte değerlendirelim.
**Olmazsa:** USB3 ya da Ethernet kablosunu GPS'ten uzaklaştır; gerekirse bakır bantla sar.

**KAPI 7:** 7.1–7.6 GEÇTİ (7.4 KARAR 1 A ise zorunlu); videolar klasörde.

---

## 10. FAZ 8 — Uçuş testleri (pervaneli, kademeli)

### 8.0 Her uçuştan önce kontrol listesi

| # | Kontrol | Geçti sayılır |
|---|---|---|
| 1 | Pil | ≥ 16,6 V (4,15 V/hücre), multimetre ile |
| 2 | Pervaneler | Doğru elli (CW/CCW), somunlar sıkı, çatlak yok |
| 3 | Kol ve vidalar | Elle burma testi; önce M4 |
| 4 | MP | `PreArm` yok; GPS 3D, uydu ≥ 12, HDop < 1,0; doğru mod |
| 5 | Jetson | `--durum` 0 restart; pil değiştiyse `--kapi` 3/3 + 60 s beklendi (7.6) |
| 6 | YKİ | İHA yeşil, HAM GNSS canlı |
| 7 | Log | `LOG_BITMASK 180222`, `INS_LOG_BAT_MASK 1` |
| 8 | Alan | İnsan yok; rüzgâr hafif; roller yerinde; pilot mod anahtarını biliyor |
| 9 | Jetson açık kalma testi | Uçuştan önce `uptime` değerini not et |

### 8.1 Her uçuştan sonra

1. Disarm → pili çıkarmadan önce Jetson'da `uptime` ve `--durum` al. `uptime` sıfırlandıysa Jetson
   uçuşta **kapanıp açılmış** demektir (güç düşmesi) → §13-G.
2. Hub sayacı: `journalctl -u navitas-seri-hub | grep "tunel sayac" | tail -n 1`.
3. Pixhawk'a USB bağla → MP → Flight Data → **DataFlash Logs** → *Download DataFlash Log Via
   Mavlink* → en son `.bin` → `results\saha_<tarih>\<uçuş>.bin`.
4. Analiz:

   ```powershell
   & $PY -B scripts\ucus_bin_analiz.py results\saha_<tarih>\<uçuş>.bin --cikti results\saha_<tarih>\<uçuş>_analiz.json
   ```

5. YKİ `hakem_log.jsonl` klasörünü not et.

### U1 — Kumandayla askı ve kabul testi

**Ne:** Loiter'da ~3 m, çubuklara **dokunmadan ≥ 30 s**, sonra LAND.
**Neden:** 4S + 9x5x3 + yeni montajın titreşim, tutum ve itki dengesi kabul ölçütlerini
sağladığının kanıtı. `MOT_THST_HOVER` bu sırada öğrenilir.
**Nasıl:** Pilot Loiter'da arm, yumuşak gazla (≥ 2 s rampa) 3 m, çubuklar ortada bekler, 30 s sonra
mod anahtarından Land.
**Geçti sayılır** (`results/ucus_analiz_20260915/RAPOR.md` §5.3):

| Ölçüt | Eşik |
|---|---|
| Askı gazı `CTUN.ThO` p50 | 0,32–0,40 |
| Titreşim VIBE p95 X, Y / Z | ≤ 8 / **≤ 16**; en yüksek < 30; clip artışı **0** |
| Tutum hatası roll/pitch RMS | ≤ 1,5° (yaw ≤ 6°) |
| Motor dengesi (RCOU C9–C12 askı ortalaması) | yayılım ≤ 40 µs; hiçbir motor ≥ 1900 µs |
| Pil | askı akımı 34–40 A; ham V_min ≥ 14,0 V |
| EKF | lane switch 0; ERR 0; failsafe 0 |

**Olmazsa:** hiçbir sonraki uçuş yapılmaz. Analiz JSON'unu bana gönder. Tek motor ≥ 1900 µs ya da
yayılım > 40 µs → önce M4 mekanik kontrolü (T279).
Yalnız askı gazı 0,40'ı aşıyor, diğer ölçütler geçiyorsa neden büyük olasılıkla kütle artışıdır: 15 Eylül
uçuşlarından bu yana ~0,35 kg eklendiyse askı gazı ~0,40'a çıkar (HESAP, `performans_modeli.py` motor modeli).
Bu durumda uçma kararı için analiz JSON'unu bana gönder; bandı kendin gevşetme.

### U2 — Kısa AUTO + havada YKİ komutu

**Ne:** KARAR 1'e göre kalkış → TAKEOFF **5 m** → LOITER_TIME 20 s → LOITER sırasında **YKİ'den ACİL LAND**.
**Neden:** Otonom kalkış ve YKİ'den havada komutun ilk gerçek kanıtı. Alçak irtifa, hata payı
yüksek.
**Nasıl:**

1. MP Plan: TAKEOFF 5 m, LOITER_TIME 20 s, LAND → **Write WPs**.
2. Pilot çubuklara dokunmaz ama **mod anahtarında eli hazır**. Kontrolü almak için anahtarı
   Loiter'a çeker.
3. KARAR 1 A: MP Actions → AUTO → YKİ'den ARM. KARAR 1 B: pilot Loiter'da kaldırır → MP'den AUTO.
4. Drone yerden kesilince (≥ 1 m) YKİ operatörü **KALKIŞ** düğmesine basar (Faz 9.2 kuralı).
5. LOITER sırasında YKİ **ACİL LAND**: 4 s içinde iki basış.

**Geçti sayılır:** otonom kalkış 5 m; YKİ LAND komutu ACK'lendi, mod LAND oldu, drone indi; YKİ
kırmızı `ACİL EMNİYET MODU`; iniş sonrası `IHA_LANDED` geldi ya da Faz 9.2'deki gecikme nedeni
görüldü; U1 ölçütleri bu logda da sağlanıyor.
**İsteğe bağlı:** YKİ **ACİL RTL** aynı düzenekle. Drone **35 m'ye tırmanır** (`RTL_ALT=3500`),
sonra eve döner ve iner. Çit tavanı 50 m.

### U3 — 30 m algı uçuşu

**Ne:** Gerçek görev yüksekliğinde rota üretimi ve hakem onayı.
**Nasıl:** Görev: TAKEOFF 32 m → alan üstünde 1–2 WP → LOITER_TIME 60 s → LAND. Alanın altında yol,
şerit ya da arena benzeri bir zemin olmalı. Kalkıştan 7–9 dk önce iniş yayıncısını yeniden başlat
(Faz 9.2). LOITER'ın 60 s'lik penceresinde YKİ operatörü gelen rotayı iki adımda onaylar.
**Geçti sayılır:**

- Drone **havadayken** YKİ günlüğünde en az bir `OPEN_ROUTE` (ya da `OLCEK_YOK` olmayan bir `NO_ROUTE`).
- Hakem onayı **inişten önce** tamamlandı (`hakem_log.jsonl`'de sırayla).
- İnişte `IHA_LANDED`.
- `GEÇERSİZLİK RİSKİ` satırı **yok**.

**Olmazsa:** YKİ'de sürekli `OLCEK_YOK` → irtifa akışı gelmiyor (§13-C `SR2_POSITION`). Rota hiç
gelmiyor → `journalctl -u navitas-rpi-inference --since "-10 min" --no-pager | tail -n 50` çıktısını
bana gönder.

### U4 — Tam prova (en az 2, hedef 3)

**Ne:** Görev günü akışının (Faz 9) birebir kopyası: kronometre, hands-off, gerçek görev
(TAKEOFF 32 m → 4 WP → LOITER_TIME 60 s → LAND), kalkıştan inişe **≤ 10 dk**.
**Geçti sayılır:** 0 müdahale, ≤ 10 dk, rota inişten önce onaylandı, `hakem_log` klasörü tam,
Jetson 0 restart.

**KAPI 8:** U1–U3 GEÇTİ ve en az 2 temiz U4.

---

## 11. FAZ 9 — Görev günü akışı

### 9.1 Zaman çizelgesi

| t | Kim | Ne | Kanıt |
|---|---|---|---|
| −90 dk | Kaptan, pilot | Alan keşfi. MP Plan: görev noktaları **gerçek koordinatlarla** (TAKEOFF 32 m, 4 WP, LOITER_TIME 60 s, LAND); çit kontrolü | Plan ekran görüntüsü |
| −60 dk | Jetson sorumlusu | Pil takılı, Jetson açık; `--durum` | Çıktı |
| −45 dk | Jetson sorumlusu | `--kapi` 3/3 (Faz 7.6) | Çıktı |
| −30 dk | MP operatörü, YKİ operatörü | MP COM + **ayna** → `yks_gui --tunel 127.0.0.1:14570 --fda` → İHA yeşil | Ekran |
| −15 dk | Pilot, aviyonik | Faz 8.0 kontrol listesi; pervaneler | Liste |
| −10 dk | MP operatörü | **Write WPs**; KARAR 1 A ise mod **AUTO** | MP |
| **−6 dk** | Jetson sorumlusu | **İniş yayıncısını yeniden başlat** (Faz 9.2; kalkış bundan 7–9 dk sonra olmalı): `sudo systemctl restart navitas-iha-inis-yayinci`; saati not et; Ethernet kablosunu çıkar | Saat notu |
| 0 | Kaptan | **"Takım Hazır"** → hands-off | Kronometre |
| +1 dk | Hakem → YKİ operatörü | Uçuşa uygunluk → YKİ'den **ARM** (iki basış) | YKİ |
| kalkış | YKİ operatörü | Drone yerden kesilince (≥ 1 m) **KALKIŞ** düğmesi | `hakem_log` |
| +2 → +5 | Otonom | Tırmanma, tarama; `OPEN_ROUTE` YKİ'ye gelir | YKİ günlüğü |
| LOITER (60 s) | Hakem, YKİ operatörü | `1) TESPİTİ DOĞRULA` → `2) … ONAYLA → ACK` — **inişten önce** | `hakem_log` |
| iniş | Otonom | LAND → `IHA_LANDED` → YKİ `İHA İNDİ` | YKİ |
| +10 dk içinde | Kaptan | Tutanak: süre, onay saati, log/video kopyası | `results\gorev_<tarih>\` |

**Sıra değişmez:** aktarım ve hakem onayı inişten **önce** gelir. Manuel müdahale = uçuş
başarısız (`SAHA_HAZIRLIK_PLANI_20260903.md:230`).

### 9.2 İniş bildirimi zamanlama kuralı (önemli)

**Sorun** (kod okumasından çıkarım; sahada ölçülmedi):

- `navitas-iha-inis-yayinci`, drone'un **önce havalandığını görmeyi şart koşmaz**. Başladığında
  drone yerdeyse ~2 s içinde `IHA_LANDED` yayınlar (`comms/iha_inis_yayinci.py:529-540`).
- Yayından sonra **600 s** heartbeat basar ve çıkar (`codes/karar_sozlesmesi.py:2084`). systemd
  onu 2 s sonra yeniden başlatır (`Restart=always`).
- Sonuç: yerdeyken **yaklaşık 10 dakikada bir** `IHA_LANDED` gelir.
- Uçuş tamamen bu 600 s'lik pencerenin **içine** düşerse, gerçek inişte **yeni `IHA_LANDED` gelmez**.
  Bir sonraki yeniden başlamayı (en çok ~10 dk) bekler.
- YKİ, kronometre başlamadan (KALKIŞ basılmadan) gelen `IHA_LANDED`'ı süre için yok sayar
  (`comms/yks_gui.py:4169-4172`).

**Kural:**

1. **KALKIŞ düğmesine drone yerden kesildikten sonra bas.** Böylece uçuş öncesi gelen bir
   `IHA_LANDED` kronometreyi durduramaz.
2. **İniş yayıncısını kalkıştan 7–9 dakika önce yeniden başlat**
   (`sudo systemctl restart navitas-iha-inis-yayinci`). Bir sonraki yeniden başlama kalkıştan
   1–3 dk sonraya, yani drone havadayken denk gelir. Yayıncı iniş kanıtını bekler ve gerçek
   inişte `IHA_LANDED` yayınlar. `--kapi` da bu servisi yeniden başlatır; son `--kapi`
   kalkıştan 7–9 dk önceyse ayrı yeniden başlatma gerekmez.
3. Kalkış 9,5 dakikadan fazla gecikirse: yeniden başlat ve 7 dk bekle.
4. Yedek: inişten sonra ~10 s içinde `IHA_LANDED` gelmezse YKİ operatörü **İHA İNDİ** düğmesine
   elle basar ve tutanağa "elle" diye yazar.

Kodda kalıcı düzeltme (yayıncının önce havalanmayı görmesi) **T284** olarak kuyruğa yazıldı.
Düzeltme gelirse bu kural sadeleşir.

---

## 12. Uçuşta acil durum prosedürü

Öncelik **yukarıdan aşağıya**. Her rol kendi satırını ezbere bilir.

| # | Durum | Kim | Ne yapar | Sonuç |
|---|---|---|---|---|
| 1 | Drone kararsız, sürükleniyor, beklenmedik hareket | **Pilot** | Mod anahtarını **Loiter**'a çeker ve kontrolü alır; gerekirse Land konumu | AUTO'dan çıkar (müdahale), drone kurtarılır |
| 2 | Pilot kontrol edemiyor ama drone havada dengeli | **MP operatörü** | Actions → mod **LAND** → Set Mode (ya da RTL) | Telsiz Pixhawk'ta olduğu için Jetson çökse de çalışır |
| 3 | MP erişilemiyor | **YKİ operatörü** | **ACİL LAND** (4 s içinde iki basış) | Jetson ve tünel çalışıyorsa |
| 4 | Kumanda koptu | Otomatik | `FS_THR_ENABLE=3` → LAND | Pilot kumandayı açınca mod anahtarıyla geri alır |
| 5 | Pil düştü | Otomatik | 14,0 V → LAND (`BATT_FS_LOW_ACT=1`); 13,2 V → LAND | — |
| 6 | Çit aşıldı (50 m tavan / 60 m yarıçap) | Otomatik | `FENCE_ACTION=1` → RTL ya da LAND | — |
| 7 | Drone yere çok yakın ve kontrolsüz (devrilme, yere sürtme) | **Pilot** | **CH6 DISARM** | Motorlar durur, drone **düşer** |

**Otomatik OLMAYANLAR:**

- **Yalnız RFD koparsa** drone göreve devam eder; GCS failsafe tetiklenmez (KARAR 2). Pilot izler.
- **Jetson çökerse** drone göreve devam eder; YKİ'ye rota ve heartbeat gelmez. Bu görev için
  aktarım başarısız sayılır ama uçuş emniyetlidir. MP operatörü görevi bitirtir ya da LAND verir.

---

## 13. Arıza giderme tabloları

### 13-A Pixhawk / Mission Planner / uçuş

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| MP bağlanmıyor (telsiz) | Yanlış COM ya da baud; RFD eşleşmedi | Aygıt Yöneticisi'nden COM; 57600; RFD yeşil LED sabit mi; iki modülün ayarları aynı mı (Net ID 73, Air Speed 128 — D-479) |
| `PreArm: Battery below minimum arming voltage` | Pil < 14,4 V (`BATT_ARM_VOLT`) | Pili şarj et. Eşiği düşürme |
| `PreArm: GPS …` / `Need 3D Fix` | İçeride ya da kilitlenmedi | Dışarıda 2–5 dk bekle; 7.8 girişim testi |
| `PreArm: Compass …` (not calibrated / inconsistent) | Montaj değişti; Jetson açıkken kalibre edilmedi | 2.5b'yi Jetson açık, dışarıda tekrarla |
| `PreArm: RC not calibrated` / `Throttle too high` | Kumanda kalibrasyonu ya da gaz çubuğu | 2.5c; gaz en altta |
| `PreArm: GCS failsafe on` | Telsiz az önce koptu | MP yeniden bağlansın, 5 s bekle |
| `Arm: Mode not armable` | AUTO'da arm; `AUTO_OPTIONS` bit0 kapalı | KARAR 1: `AUTO_OPTIONS=3` ya da başka modda arm |
| AUTO'da arm etti ama kalkmıyor | `AUTO_OPTIONS` bit1 kapalı, görev yok ya da ilk komut TAKEOFF değil | `AUTO_OPTIONS=3`; Plan → Read WPs ile görevi kontrol et |
| Arm'dan 10 s sonra kendiliğinden disarm | `DISARM_DELAY=10`, kalkış olmadı | Normal emniyet; kalkışı 10 s içinde başlat |
| Kalkışta devrilme eğilimi | Motor sırası/yönü, pervane eli, CG, ESC kalibrasyonu | **Gazı kes.** `SAHA_OLAY_SONRASI_MUAYENE.md` maddeleri; 2.6'yı video ile tekrarla |
| VIBE > 30 ya da clip artıyor | Pervane balansı, gevşek motor, Pixhawk sönümleyicisi | 1.1–1.4; pervaneyi değiştir |
| Loiter'da giderek büyüyen daireler çizerek sürükleniyor | Pusula girişimi | Pusula kalibrasyonu Jetson açıkken; GPS direğini uzaklaştır |
| Uçuşta erken pil failsafe | Zayıf ya da yarım dolu paket; `BATT_FS_VOLTSRC` 0 | Pil ≥ 16,6 V; `BATT_FS_VOLTSRC=1` mi kontrol et |
| MP gerilimi multimetreden farklı | `BATT_VOLT_MULT` | 2.4, bir kez |
| `.bin` indirme çok yavaş | RFD üzerinden iniyor | USB kablosuyla indir |

### 13-B TELEM2 / UART

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| `Permission denied` | `dialout` grubu | `sudo usermod -aG dialout,video $USER` → oturumu kapat/aç |
| Heartbeat yok (iki port) | TX teli, GND, parametre, seri konsol | Faz 3.2 tablosu; `SERIAL2_*`; `sudo systemctl stop nvgetty` |
| Tek yön çalışıyor | Bir tel kopuk ya da çapraz değil | Faz 1.6 tablosu; süreklilik |
| Anlamsız baytlar, heartbeat nadir | Baud uyuşmazlığı | `SERIAL2_BAUD=57`; `PIXHAWK_BAUD=57600` (tünelde başka baud reddedilir) |
| Port adı yok | Kart/JetPack farklı | `ls -l /dev/ttyTHS* /dev/ttyTCU*` çıktısını bana gönder |
| Servisler açıkken test komutu portu açamıyor | MAVProxy portu tutuyor | Önce `sudo systemctl stop navitas-cogullayici navitas-seri-hub` |

### 13-C Jetson servisleri

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| `--kuru` → `[YOK] mavproxy.py (PATH)` | MAVProxy venv'de ama `~/.local/bin`'de değil | `ln -sf ~/venv312/bin/mavproxy.py ~/.local/bin/mavproxy.py` |
| `--kuru` ExecStart'ta `/usr/bin/python3` (kamera köprüsü dışında) | `PYTHON3` değişkeni verilmedi | 4.1'deki `export` satırlarını aynı terminalde tekrar yaz |
| `HATA: … mavlink_tunel.py yok` | Kod kopyalanmadı | Faz 0.3 kopya komutları |
| `[YOK] kullanici …` / birim 217/USER döngüsü | Servis kullanıcısı yanlış | Komutu kendi kullanıcınla `sudo -E` ile koş (root oturumunda değil) |
| `--kapi` 0/3 | MAVProxy kalkmadı ya da port yanlış | `journalctl -u navitas-cogullayici -n 50 --no-pager`; Faz 3.2; `PIXHAWK_SERI` |
| `--kapi` 1/3 ya da 2/3 | Akış hızı sınırda (telsiz bandı, Pixhawk yeni açılmış) | 60 s bekle, tekrar koş; yine düşerse `results/jetson_log/kapi/*.log` dosyalarını bana gönder |
| `--kapi` `GLOBAL_POSITION_INT` düşük | `SR2_POSITION` < 8 | Parametreyi oku (Faz 3.1) |
| `--durum` restart sayısı artıyor | Bir servis çöküp kalkıyor | `journalctl -u navitas-<birim> -n 50 --no-pager` çıktısını bana gönder |
| Günlükte `Killed process` | Bellek yetmedi | `free -h`; swap var mı (8 GB olmalı) |
| `MODEL KAYIT DOGRULAMASI BASARISIZ` | Kayıt defteri yok ya da model farklı | Faz 0.3 hash; `config/model_registry.json` |
| rpi-inference `Jetson uretim manifesti bulunamadi` | Manifest kopyalanmadı | `cp ~/navitas_tunel/jetson_paket/models/jetson_derleme_manifest.json ~/navitas/models/` |
| YKİ'de sürekli `OLCEK_YOK` (havada) | İrtifa akışı yok ya da bayat (> 0,5 s) | `--kapi` 3/3 mü; Pixhawk yeniden başladıysa 7.6 |

### 13-D Kamera

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| `No cameras available` | CSI sensörü tanımlı değil ya da şerit kablo ters | `sudo /opt/nvidia/jetson-io/jetson-io.py` → CSI → IMX477 → kaydet → reboot; şerit kablo yönü ve kilidi; `sudo dmesg \| grep -i imx477` |
| Siyah ya da yeşil kare | Şerit kablo, sürücü | Şerit kablo; JetPack 7.2.1'de IMX477 stok sürücü riski var (`jetson_paket/gosterici/GOSTERICI_KURULUM.md:62`) — bana yaz |
| Köprü çıkış kodu 3 | 8080 portu dolu (elle açılan köprü kaldı) | `pkill -f kamera_koprusu.py`, sonra `--kapi` |
| `"kaynak_acik": false` | Kamera açılamadı | `journalctl -u navitas-kamera-koprusu -n 50 --no-pager` |
| FPS düşük | Güç modu | `sudo nvpmodel -m 0 && sudo jetson_clocks`; `sudo tegrastats --interval 1000` ile sıcaklık |
| Görüntü aynalı (ayna testi) | Kamera montajı | Kodda çevirme **eklenmez**; montajı/yönü bana gönder |
| FOV 50–65° dışında | Ölçüm hatası ya da sensör modu kırpıyor | Ölçümü tekrarla; yine dışındaysa değeri ve fotoğrafı bana gönder |

### 13-E Tünel / YKİ

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| MP yeşil, YKİ İHA kırmızı | Ayna kurulmadı ya da Write access yok | 5.2 (Ctrl+F); port 14570 |
| Ayna var, yine kırmızı | Jetson hub ya da MAVProxy `--out 14553` yok | 4.3 `ps` ve `journalctl -u navitas-seri-hub` |
| YKİ İHA sarı | Heartbeat var, Pixhawk verisi yok | `journalctl -u navitas-rpi-inference -n 30 --no-pager`; 14550 akışı |
| Kırmızı `TÜNEL SAYAÇ ARTIŞI` satırları | Parça kaybı, parça tavanı ya da akran değişti | Tek tük (Pixhawk/`--kapi` sonrası) normal; sürekliyse Faz 6.5 (iii) sayaçlarını bana gönder |
| YKİ açılmıyor: `--tunel ile --iha birlikte kullanılamaz` | Yanlış bayrak | Yalnız `--tunel 127.0.0.1:14570 --fda` |
| YKİ açılmıyor: kanıt kaydı hatası | `results\prova` yazılamıyor | Disk dolu mu; klasör izinleri |
| ARM düğmesi gri | Taze `armed` telemetrisi yok (> 2,5 s) | `rpi_inference` çalışıyor mu (7.2) |
| `İHA ONAY VERMEDİ` | Pixhawk reddetti ya da komut 5 s içinde ulaşmadı | MP Messages; Jetson `journalctl -u navitas-iha-komut-alici -n 30 --no-pager`; ikinci kez dene |
| MP parametre indirmesi çok yavaş / bağlantı kalitesi düşük | Telsiz bandı dolu | Faz 6.6 "Düşerse" |
| K8 p95 ≥ 0,20 s | Bant ya da telsiz ayarı | Faz 6.6 — eşik gevşetilmez |

### 13-F Telsiz (RFD900A)

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| Eşleşmiyor (yeşil LED yanıp sönüyor) | Farklı Net ID / Air Speed / frekans | İki modülü MP → Setup → Optional Hardware → **SiK Radio** → *Load Settings* ile oku; ayarlar aynı olmalı |
| Yakında çalışıyor, uzakta kopuyor | Anten yönü ya da engel; Air Speed 128 menzili ölçülmedi (T271) | Antenler dikey, karbon ve pil arkasında değil; menzil testi ayrı iş |

### 13-G Güç

| Belirti | Olası neden | Yapılacak |
|---|---|---|
| Uçuş sonrası Jetson `uptime` sıfırlandı | Tam gazda gerilim düşümü, regülatör akımı yetmiyor | **Sonraki uçuşa çıkılmaz.** Regülatör etiketini (akım değeri) ve bağlantı fotoğrafını bana gönder |
| Pixhawk uçuşta yeniden başladı (log kesik) | PM06 hattı, konnektör | Konnektörler; `SAHA_OLAY_SONRASI_MUAYENE.md` |
| Motorlardan biri ısınıyor | Yatak, pervane, ESC | U1 analizindeki motor dengesine bak; motoru değiştir |

---

## Ek A — Parametre tablosu

| Parametre | Şu an (14.09 dökümü) | Yazılacak | Neden | Kaynak |
|---|---|---|---|---|
| `BATT_CAPACITY` | 8000 | **13000** | 4S 13 Ah paket | RAPOR §5.2 |
| `BATT_LOW_VOLT` | 10 | **14.0** | 3,5 V/hücre; bugünkü değer 4S'te failsafe'i kapatıyor | RAPOR §5.2 |
| `BATT_CRT_VOLT` | 9 | **13.2** | 3,3 V/hücre | RAPOR §5.2 |
| `BATT_FS_VOLTSRC` | 0 | **1** | Sarkma telafili gerilim; yük altında yersiz failsafe'i önler | RAPOR §5.2 |
| `BATT_ARM_VOLT` | 9 | **14.4** | Yarı dolu pille kalkışı engeller | RAPOR §5.2 |
| `BATT_FS_LOW_ACT` / `BATT_FS_CRT_ACT` | 1 / 1 | değişmez | LAND | döküm |
| `MOT_THST_HOVER` | 0,5326 (3S) | 0,33–0,40 değilse **0.39** | 15 Eylül 4S askısında 0,3895 öğrenildi | RAPOR §5.2 |
| `MOT_HOVER_LEARN` | 2 | değişmez | Öğrenmeye devam | RAPOR §5.2 |
| `LOG_BITMASK` | 176126 | **180222** | PID logu (+4096) | RAPOR §5.2 |
| `INS_LOG_BAT_MASK` | 0 | **1** (test uçuşları) | Hızlı IMU logu; titreşim ve kol analizi | RAPOR §5.2 |
| `INS_HNTCH_ENABLE` | 0 | **değişmez** | Çentik filtresi için kanıt yok | RAPOR §5.2 |
| `ATC_*` (PID) | — | **değişmez** | Salınım kanıtı yok | RAPOR §5.2 |
| `AUTO_OPTIONS` | 0 | **3** (KARAR 1 A ise) | AUTO'da arm + gazsız kalkış | §0.5 |
| `RC_SPEED` | 490 | 400 (KARAR 3 kabul edilirse) | ESC üst sınırı 432 Hz | README:56-58 |
| `FS_THR_ENABLE` / `FS_THR_VALUE` | 3 / 975 | değişmez | Kumanda kopunca LAND | döküm |
| `FS_GCS_ENABLE` / `FS_GCS_TIMEOUT` | 5 / 5 | değişmez | LAND; tünel kipinde yalnız Jetson ve RFD birlikte koparsa tetiklenir | D-474, runbook:34-37 |
| `FENCE_*` | 1 / 3 / 50 / 60 / 1 | değişmez | Çit | döküm |
| `RTL_ALT` | 3500 | değişmez | RTL 35 m'ye çıkar | döküm |
| `SERIAL1/2_*`, `SR2_POSITION`, `SYSID_*` | Faz 3.1 | **okunur, yazılmaz** | Tünel düzeni | runbook §1 |

---

## Ek B — Komut kopya kartı

**Bilgisayar (PowerShell, `O:\navitas`):**

```powershell
$PY = "O:\navitas-local-train\venv\Scripts\python.exe"
& $PY -B comms\yks_gui.py --tunel 127.0.0.1:14570 --fda
& $PY -B scripts\ucus_bin_analiz.py <dosya.bin> --cikti <analiz.json>
& $PY -B scripts\kamera_fov_hesapla.py --genislik-px 1280 --isaret-px <p> --isaret-m <s> --mesafe-m <d>
```

**Jetson (her yeni terminalde önce değişkenler):**

```bash
cd ~/navitas_tunel
export PATH=$HOME/.local/bin:$PATH
export KIP=tunel PIXHAWK_SERI=/dev/ttyTHS1 PIXHAWK_BAUD=57600 SYSID=1
export FOV=<derece> KAMERA=http://127.0.0.1:8080/video
export NAVITAS_KOK=$HOME/navitas PYTHON3=$HOME/venv312/bin/python

bash jetson_paket/jetson_baslat.sh --kuru          # ne kurulacak
sudo -E bash jetson_paket/jetson_baslat.sh --kapi  # kur + 3/3 kapı + başlat (her pil değişiminde)
bash jetson_paket/jetson_baslat.sh --durum         # birimler ve restart sayısı
sudo bash jetson_paket/jetson_baslat.sh --durdur   # hepsini durdur (açılışta da başlamazlar)

journalctl -u navitas-<birim> -n 50 --no-pager     # birim: cogullayici, seri-hub, kamera-koprusu,
                                                   # rpi-inference, iha-inis-yayinci, iha-komut-alici
journalctl -u navitas-seri-hub | grep "tunel sayac" | tail -n 1
sudo systemctl restart navitas-iha-inis-yayinci    # görev günü, kalkıştan 7–9 dk önce (Faz 9.2)
uptime
```

---

## Ek C — Her fazdan sonra bana gönderilecekler

| Faz | Gönder |
|---|---|
| 0 | 0.2 çıktısı; hash; `UYUMLU` satırı; `A9_fov.txt`; A10 FPS satırları; ayna testi görüntüsü |
| 1 | Kütle; fotoğraflarda sorunlu görünen varsa o fotoğraf |
| 2 | `param_sonra_*.param`; motor testi sonucu (4/4); A1/A3/A4 sonuçları; A3 geri alma ekran görüntüsü |
| 3 | `03_telem2.txt` |
| 4 | `--kuru` son 30 satır; `--kapi` çıktısı; `--durum` (2 dk sonra) |
| 5 | YKİ ekran görüntüsü (İHA yeşil, alt çubuk) |
| 6 | `results\tunel_<tarih>\` klasöründeki tüm JSON'lar + hub sayaç satırları |
| 7 | 7.2–7.6 sonuçları; 7.6'nın süresi; 7.8'deki iki uydu/HDop değeri |
| 8 | Her uçuşun `_analiz.json`'u; `uptime` öncesi/sonrası; U3/U4 `hakem_log.jsonl` klasör adı |
