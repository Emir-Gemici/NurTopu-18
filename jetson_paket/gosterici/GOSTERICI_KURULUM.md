# İŞARETLİ GÖSTERİCİ — KURULUM (T228 · D-443 · MK15 video hattı)

> **NEDEN:** Jetson'un **yayınlanmış karar** bindirmeli karesi (T227 `rpi_inference --isaretli-yayin
> 127.0.0.1:8081`) hakeme MK15 video hattıyla görsel kanıt olarak gider. Tasarım ve ön kayıt:
> `results/fdr_sprint_20260910/H9_MK15/TASARIM.md` §1–§5; boşluk araştırması `mk15-bosluk` (10 Eylül).
>
> **Video KARAR ÜRETMEZ.** Rota verisi ve hakem onayı SiK 433 MHz'te kalır (CONTRACTS §6.7 değişmez).
> Video koparsa uçuş geçersiz olmaz; veri koparsa olur (şartname §2.2.3, §6.2).
>
> **Kural: ÖLÇÜLEMEDİ ≠ GEÇTİ.** Bu belgedeki Jetson adımlarının **hiçbiri Jetson'da koşulmadı**
> (10 Eylül; Jetson geliştirici PC'sinde yok). PC'de ölçülen: boru dizgileri, durum mantığı,
> x11 penceresi (Windows), kuru koşum — `tests/test_isaretli_gosterici.py`,
> `results/fdr_sprint_20260910/H9_MK15/t228/`. T228-D (10 Eylül): x11 döngüsü (sahte cv2),
> DRM gözetmeni histerezisi + boru nabzı (sahte süreç, sahte `-v` çıktısı) —
> `results/fdr_sprint_20260910/H9_MK15/t228d/`.

## 0. Ne yapar

- **Girdi:** `http://127.0.0.1:8081` — `/kare.jpg`, `/video`, `/durum` (kamera köprüsüyle **aynı uçlar**;
  T227 sunucusu `kamera_koprusu`'nun HTTP sunucusunu yeniden kullanır).
- **Çıktı:** 1280×720 tuval, tam ekran → DisplayPort.
- **Ekran durumları** (asla eski kareyi taze gibi göstermez):

| durum | ne zaman | ekranda |
|---|---|---|
| CANLI | son **yeni** kare ≤ 2 s önce | işaretli kare + sağ altta küçük `CANLI 0.4 s` |
| BAYAT | son yeni kare > 2 s önce (ön kayıt eşiği) | kare **gri + karartılmış**, üstte amber `BAYAT — kare N s eski` bandı |
| GÖRÜNTÜ YOK | > 5 s (köprünün taze kare tavanı) **ya da** yayın erişilemiyor / HTTP 503 / JPEG çözülemedi | tam ekran **kırmızı** `GORUNTU YOK` + sebep; eski kare **çizilmez** |

- **Kipler:**

| kip | ne | durum |
|---|---|---|
| `x11` | **varsayılan, birincil** — X11 masaüstü + otomatik oturum + tam ekran pencere; gdm **kapanmaz** | §3 |
| `drm` | seçenek — `nvdrmvideosink`; gdm **durur**, masaüstü gider | §5 |
| `rtsp` | **yedek** — yazılım x264 1280×720 @ 5 fps, `rtsp://<jetson_ip>:8554/isaretli` | §6 |
| `--kuru` | seçilen kipin tam komutunu/ayarını yazar, hiçbir şey açmaz (çıkış 0) | her kip |

`kmssink` **kullanılmaz** (araştırma kararı).

## 1. Zincir (İHA tarafı)

```
Jetson Orin Nano DevKit ─ DisplayPort
   └─(DP→HDMI adaptör: pasif ya da aktif — NVIDIA resmî destekli)─ HDMI
        └─(HDMI → mini HDMI kablo; eldeki kablo)─ SIYI HDMI giriş dönüştürücü (giriş Mini HDMI, 12 V / 3 W, 192.168.144.25)
             └─(LAN&PWR)─ SIYI hava birimi ──RF 5,8 GHz── MK15 kumanda: SIYI FPV "Camera 1"
                  └─(kumanda HDMI — yalnız Enterprise, ekran aynası)─ USB HDMI yakalama kartı ─ YKS PC
                       └─ kamera_koprusu --kaynak <indeks> → yks_gui --kamera-url http://127.0.0.1:8080
```

| konu | bilgi | kaynak |
|---|---|---|
| Orin Nano DevKit görüntü çıkışı | yalnız **DisplayPort**; pasif ve aktif DP→HDMI adaptör resmî destekli | docs.nvidia.com — Orin Nano DevKit "hardware layout" |
| HDMI giriş dönüştürücü | giriş **Mini HDMI**, **12 V / 3 W**, varsayılan IP **192.168.144.25**, `rtsp://192.168.144.25:8554/main.264` (H.264 — kodek çelişkili, bkz. Kodlayıcı satırı); IP, SD karttaki **`setip.txt`** ile değişir | SIYI dönüştürücü kılavuzu v1.1 |
| Dönüştürücü beslemesi | 12 V büyük olasılıkla hava biriminin **LAN&PWR** kablosundaki 12V pininden — **DOĞRULANACAK**; yedek: Jetson'un 12,2 V dönüştürücüsü (akım kapasitesi **BEYAN GEREKLİ**, D-443 ek) | araştırma; kullanıcı |
| Hava birimi | **MK15 Air Unit** (100 g, 1 LAN&PWR, 16,8–75,6 V) **ya da HM30 Air Unit** (74 g, 2 LAN&PWR, 12,6–25,2 V) — hangisi olduğu etiketten okunur. 🔴 **RİSK:** MK15 Air Unit ise 4S yük altında alt sınırın altına iner (6 Eylül tlog 9,35–11,28 V okundu, D-440) | SIYI; D-440 |
| Kumanda HDMI | yalnız **Enterprise** sürümde; ekranın aynası (ham akış değil) | MK15 kılavuzu v1.9 |
| SIYI FPV | OSD kapatılabilir; Camera 1 tam ekran | SIYI FPV |
| Frekans | FCC MK15TX 5745–5825 MHz, iletilen 68,1 mW ≈ **214 mW e.i.r.p.** (5 dBi) > BTK muafiyeti **25 mW e.i.r.p.** — 🔴 **RİSK AÇIK** (Link Status'tan okunur, DDK'ya sorulur) | FCC; BTK |
| Kodlayıcı | Orin Nano'da **NVENC yok**; x264 30 fps ultrafast çekirdek başı %19–38. Dönüştürücünün canlı kodeki **H.264/H.265 çelişkili** (TASARIM §5; SIYI dönüştürücü kılavuzu V1.1) — §4 adım 5'te VLC'de okunur (**DOĞRULANACAK**) | NVIDIA Jetson Linux R39.2; SIYI dönüştürücü kılavuzu V1.1 |
| Kamera | JetPack 7.2.1 + IMX477: stok sürücüyle başarı raporu yok; Arducam beta 39.2.0'a bağlı — **12 Eylül ilk test**; yedek USB UVC kamera | araştırma |

## 2. IP planı (SIYI alt ağı 192.168.144.0/24)

| adres | cihaz | not |
|---|---|---|
| .11 | hava birimi | sabit, değişmez |
| .12 | yer birimi (kumanda) | sabit |
| .20 | kumanda Android | sabit |
| .25 | HDMI giriş dönüştürücü | varsayılan; `setip.txt` ile değişir |
| .30 | Jetson (**yalnız RTSP yedeğinde**) | öneri — gösterici **.11/.12/.20/.25'i reddeder** (çıkış 2) |

IP ayarları sahada birlikte yapılır (D-443 ek, cevap 6). x11/drm kiplerinde Jetson'un SIYI ağına
bağlanması **gerekmez** (görüntü DP kablosundan gider).

## 3. X11 kipi (birincil — gdm KAPANMAZ)

1. **Dosya:** JETSON_KILAVUZ §2 kurulum bloğu `cp kod/isaretli_gosterici.py ~/navitas/scripts/` yapar.
   `kamera_koprusu.py` **aynı dizinde** olmalı (gösterici HTTP sabitlerini ondan alır).
2. **Otomatik oturum (GDM, Xorg):** `/etc/gdm3/custom.conf`

   ```ini
   [daemon]
   AutomaticLoginEnable=true
   AutomaticLogin=n4vitas
   WaylandEnable=false
   ```

   Oturum türü: `echo $XDG_SESSION_TYPE` → `x11` olmalı (**DOĞRULANACAK**).
3. **Ekran koruyucu / kilit / bildirim kapalı** (gösterici ayrıca `xset s off`, `s noblank`, `-dpms` dener):

   ```bash
   gsettings set org.gnome.desktop.session idle-delay 0
   gsettings set org.gnome.desktop.screensaver lock-enabled false
   gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
   gsettings set org.gnome.desktop.notifications show-banners false
   ```

4. **Autostart:** `mkdir -p ~/.config/autostart && cp gosterici/navitas-isaretli-gosterici.desktop ~/.config/autostart/`
   — Exec, `/etc/navitas.env`'deki `ISARETLI_YAYIN`'ı okur (yoksa `127.0.0.1:8081`), **sistem Python'uyla**
   koşar, çökerse 2 s sonra yeniden başlatır; çıkış 0 (q/ESC, SIGTERM) ve 2 (ortam hatası) olunca durur.
   Log: `~/navitas/results/jetson_log/isaretli_gosterici.log`.
5. **Yayını aç:** `GOSTERICI_KIP=x11 KIP=… FOV=… bash jetson_paket/jetson_baslat.sh --kuru` →
   `rpi_inference … --isaretli-yayin 127.0.0.1:8081` ve `## gosterici` bölümü (`[VAR]/[YOK]`).
   T227 birleşmeden `[YOK] … rpi_inference --isaretli-yayin (T227)` + çıkış 3; `--kur` **durur**
   (tanımsız bayrak argparse çıkış 2 → `Restart=always` çökme döngüsü olurdu).
6. **İmleç:** `sudo apt install unclutter` (isteğe bağlı — fare yoksa imleç ekranda kalabilir).
7. **Elle deneme (ssh):** `DISPLAY=:0 /usr/bin/python3 ~/navitas/scripts/isaretli_gosterici.py --kip x11 --sure 10`
   (`--tuval-kaydi <dizin>` durum değişimlerinde tuvali JPEG yazar).

## 4. Doğrulama sırası (12 Eylül atölye — İNSAN; hepsi şu an ÖLÇÜLEMEDİ)

| # | adım | beklenen | sonuç |
|---|---|---|---|
| 1 | `--kuru` (x11, drm, rtsp) | çıkış 0; komutlar basılır | ÖLÇÜLECEK |
| 2 | Jetson DP → HDMI monitör, yayın kapalı | tam ekran kırmızı `GORUNTU YOK` + "yayin erisilemiyor" | ÖLÇÜLECEK |
| 3 | `GOSTERICI_KIP=x11` + T227 yayını | CANLI, bindirme okunur | ÖLÇÜLECEK |
| 4 | `rpi_inference` durdurulur | ≤ 2 s içinde BAYAT, ≤ 5 s içinde GÖRÜNTÜ YOK; yeniden başlayınca CANLI | ÖLÇÜLECEK |
| 5 | monitör yerine dönüştürücü | VLC `rtsp://192.168.144.25:8554/main.264` görüntü | ÖLÇÜLECEK |
| 6 | MK15 kumanda Camera 1 | aynı ekran, OSD kapalı | ÖLÇÜLECEK |
| 7 | camdan cama gecikme (TASARIM §3.4, eşik ≤ 1,0 s) | 5 ölçüm, p50/maks | ÖLÇÜLECEK |
| 8 | Argus FPS: kamera + gösterici birlikte (drm kipinde ayrıca) | FPS düşmez | ÖLÇÜLECEK |
| 9 | DRM nabız biçimi + zamanlaması: §5 `--nabiz-sina` komutu (DRM kipinden ÖNCE) | çıkış 0, `NABIZ_SINA: ESLESTI — … 20 nabiz …; ZAMANINDA` | ÖLÇÜLECEK |

## 5. DRM kipi (seçenek — gdm DURUR, masaüstü gider)

Önkoşul ve borular: `/usr/bin/python3 ~/navitas/scripts/isaretli_gosterici.py --kip drm --kuru` basar:

```bash
sudo systemctl stop gdm
sudo loginctl terminate-seat seat0
sudo modprobe nvidia-drm modeset=1
gst-launch-1.0 -v -e 'souphttpsrc location=http://127.0.0.1:8081/video is-live=true do-timestamp=true ! multipartdemux ! jpegdec ! identity name=nabiz silent=false ! nvvidconv ! video/x-raw(memory:NVMM),width=1280,height=720 ! nvdrmvideosink set_mode=1 sync=false'
```

~~10 Eylül (T228): `gst-launch-1.0 -e 'souphttpsrc location=http://127.0.0.1:8081/video is-live=true do-timestamp=true ! multipartdemux ! jpegdec ! nvvidconv ! video/x-raw(memory:NVMM),width=1280,height=720 ! nvdrmvideosink set_mode=1 sync=false'`~~ → **10 Eylül (T228-D):** `-v` + `identity name=nabiz silent=false` eklendi (boru ilerlemesi izlenir).

Birim (**varsayılan KAPALI**; `jetson_baslat.sh` kurmaz):

```bash
sed -e "s#/home/navitas/navitas#$HOME/navitas#g" -e "s#^User=navitas\$#User=$USER#" \
    gosterici/navitas-isaretli-gosterici-drm.service > /tmp/navitas-isaretli-gosterici-drm.service
sudo cp /tmp/navitas-isaretli-gosterici-drm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start navitas-isaretli-gosterici-drm     # önce dene; kalıcı için: enable
```

- `${KAMERA_PYTHON}` ve `${ISARETLI_YAYIN}` `/etc/navitas.env`'den gelir → `jetson_baslat.sh --kur` bu
  sürümle en az bir kez koşulmuş olmalı.
- 🔴 **Argus uyarısı:** `nvidia-drm` yüklenip `nvdrmvideosink` **çalışmazsa** Argus (`nvarguscamerasrc`)
  **~3 fps'e düşer**. DRM ya sürekli çalışır ya hiç açılmaz; kamera FPS'i DRM açıkken ölçülür.
- JetPack 7.2'de `nvidia-drm` varsayılan denylist'te (`nv-load-display-modules` servisi) — açık
  `modprobe`'un yükleyip yüklemediği **DOĞRULANACAK**.
- drm kipinde kareye BAYAT bandı **çizilmez** (boru `/video`'yu doğrudan gösterir). Gözetmen
  `/kare.jpg`'yi 1 s'de bir yoklar; kare 2 s'den uzun süre yeni değilse video borusunu durdurur ve
  kırmızı GÖRÜNTÜ YOK borusunu (`videotestsrc pattern=red ! textoverlay`) açar — `nvdrmvideosink`
  son kareyi ekranda bırakamaz.
- **Histerezis ve yeniden başlatma sıklığı (T228-D, 10 Eylül):** CANLI'dan (video borusundan) çıkış
  **ilk** bayat / hata / donmuş yoklamada, bekleme yok (güvenli taraf). Video borusuna dönüş
  **2 ardışık** taze yoklama **ve** son boru başlatmasından **≥ 3 s** ister — çırpınan yayın
  `nvdrmvideosink`'i sürekli yeniden açmaz (her açılış `set_mode=1` ile kip kurar). Kendiliğinden
  ölen video borusunun yerine GÖRÜNTÜ YOK borusu **hemen** açılır; ölen GÖRÜNTÜ YOK borusu ≥ 3 s
  aralıkla yeniden açılır. Açılışta kırmızı ekran ~3 s görünür (bu kurala göre beklenen).
- **Boru ilerlemesi — donmuş boru (T228-D):** video borusunda `identity name=nabiz silent=false`;
  `gst-launch-1.0 -v` her tamponda `…/GstIdentity:nabiz: last-message = chain … (nabiz:sink) … pts: …`
  biçiminde bir satır basar, gözetmen bunları okur. `/kare.jpg` taze olsa bile video borusu **> 3 s**
  tampon geçirmezse (açılışta ilk tampon için de 3 s pay) video borusu durur ve GÖRÜNTÜ YOK borusu
  açılır (sebep "video borusu ilerlemiyor"). `identity`, `jpegdec`'ten sonra sistem belleğindedir
  (NVMM caps'li `identity` **ÖLÇÜLEMEDİ**); boruda kuyruk yok → sink takılırsa nabız da durur.
- 🔴 **`-v` nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK** (PC'de GStreamer yok;
  ayrıştırıcı toleranslı: `nabiz` elemanı + önce `chain` kelimesi; `event` / `caps` satırları
  sayılmaz; `pts` isteğe bağlı). Sahada DRM kipinden **önce** (§4 adım 9):

  ```bash
  stdbuf -oL gst-launch-1.0 -v videotestsrc is-live=true num-buffers=20 ! video/x-raw,framerate=5/1 \
    ! identity name=nabiz silent=false ! fakesink \
    | /usr/bin/python3 ~/navitas/scripts/isaretli_gosterici.py --nabiz-sina
  ```

  Beklenen (~4 s): `NABIZ_SINA: ESLESTI — … 20 nabiz …; ZAMANINDA: varis yayilimi ≈3,8 s / pts
  yayilimi 3,80 s`, çıkış 0. **Çıkış 1** iki sebeple: `ESLESMEDI` (biçim farklı) ya da `TOPLU`
  (satırlar tamponlu, topluca geliyor → sağlıklı boru "donmuş" sayılır). İkisinde de DRM kipi video
  borusunu her ~3 s'de bir GÖRÜNTÜ YOK'a düşürür (fail-closed: eski kare gösterilmez ama canlı
  görüntü de gelmez) → **x11 kipinde kal**; ekrana basılan satırları bu belgeye yapıştır. DRM
  çalışırken gerçek satırlar journal'da `gst:` önekiyle görünür (ilk 40 satır).
- **Satır tamponu:** `drm_kos` video borusunu `stdbuf -oL` önekiyle koşar (coreutils `stdbuf`
  varsa; yoksa KIRMIZI uyarı, önek konmaz). Stdout boruya bağlıyken blok tampon nabız satırlarını
  topluca getirirdi; `gst-launch`'ın kendi `fflush`'ı **ÖLÇÜLEMEDİ**.
- **Geri alma:** `sudo systemctl disable --now navitas-isaretli-gosterici-drm; sudo modprobe -r nvidia_drm; sudo systemctl start gdm`
  (`modprobe -r` başarısızsa yeniden başlat).

## 6. RTSP kipi (YEDEK)

- **Ne zaman:** DP/dönüştürücü yolu çalışmazsa (TASARIM §1 "Yedek video yolu"). Jetson hava birimine
  doğrudan Ethernet'le bağlanır; hava biriminin LAN&PWR portu dönüştürücüdeyse **ethernet anahtarı** gerekir.
- **Bağımlılık:** `sudo apt install python3-gi gir1.2-gst-rtsp-server-1.0 gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly`
  (x264enc = plugins-ugly). **Sistem Python'u** ile koşulur (venv değil).
- **Jetson IP:** `192.168.144.30/24` (bağlantı adı ve komut sahada — **DOĞRULANACAK**).
- **Komut:** `/usr/bin/python3 ~/navitas/scripts/isaretli_gosterici.py --kip rtsp --jetson-ip 192.168.144.30`
  → `rtsp://192.168.144.30:8554/isaretli`; 1280×720 @ 5 fps, `x264enc tune=zerolatency speed-preset=ultrafast bitrate=2000 key-int-max=10`.
  Varsayılan boru `tuval` (gösterici ekranı appsrc ile — BAYAT/GÖRÜNTÜ YOK ekranları RTSP'ye de gider);
  `--rtsp-boru http` ham `/video`'yu souphttpsrc ile kodlar (bayat/yok ekranı yok).
- **Hava birimine adres:** üçüncü taraf IP kamera olarak RTSP adresi girilir — ekran/menü **DOĞRULANACAK**.
- **CPU:** PC ölçümü `results/fdr_sprint_20260910/H9_MK15/t228/x264_cpu_olcumu.txt`; Jetson'da **ÖLÇÜLEMEDİ**
  (NVIDIA R39.2: 30 fps ultrafast çekirdek başı %19–38 → 5 fps'te kabaca altıda biri — **BEKLENTİ, ölçüm değil**).

## 7. SIYI FPV (kumanda)

- **Camera 1** = dönüştürücü akışı (`rtsp://192.168.144.25:8554/main.264`).
- OSD **kapalı**, tam ekran, bildirimler sessiz — kumanda HDMI çıkışı ekranın aynasıdır; OSD ve
  bildirimler hakem ekranına da gider.

## 8. Sorun giderme

| belirti | olası neden | ne yap |
|---|---|---|
| DP'de siyah ekran / X "no screens found" | dönüştürücü EDID/HPD vermiyor (belgesiz) | `DISPLAY=:0 xrandr --query`; `grep -i edid /var/log/Xorg.0.log`; EDID yoksa `gosterici/xorg-1280x720-edid-yok.conf` (**TAHMİN** — önce yedekle) |
| kırmızı `GORUNTU YOK` "yayin erisilemiyor" | T227 yayını yok / `rpi_inference` çöktü / `GOSTERICI_KIP=kapali` | `curl -s http://127.0.0.1:8081/durum`; `journalctl -u navitas-rpi-inference -n 50` |
| kırmızı `GORUNTU YOK` "yayin HTTP 503" | kaynak açık değil / taze kare yok | `/durum` → `son_hata` |
| sürekli BAYAT | `rpi_inference` yavaş ya da takılı | `jetson_baslat.sh --durum`; FPS logu |
| gösterici hemen çıkıyor, log "DISPLAY yok" (çıkış 2) | grafik oturum yok / Wayland | otomatik oturum, `WaylandEnable=false`; ssh'ten `DISPLAY=:0` |
| "cv2 penceresi acilamadi" (çıkış 2) | venv Python'u (opencv-python-headless) | `/usr/bin/python3` + `python3-opencv` |
| drm kipinde sürekli kırmızı "video borusu ilerlemiyor" | `-v` nabız biçimi eşleşmiyor, satırlar tamponlu (`TOPLU`) ya da `/video` akmıyor | §5 `--nabiz-sina`; journal'da `gst:` satırları; x11 kipine dön |
| kamera ~3 fps | `nvidia-drm` yüklü, DRM gösterici çalışmıyor (Argus) | DRM birimini çalıştır ya da `sudo modprobe -r nvidia_drm` / yeniden başlat |
| monitörde var, MK15'te yok | dönüştürücü beslemesi / IP / Camera 1 ayarı | dönüştürücü LED'i; `ping 192.168.144.25`; VLC `rtsp://192.168.144.25:8554/main.264` |
| hava birimi kararıyor | 4S yük altında alt sınır (MK15 Air Unit 16,8 V) | etiketi oku; ayrı BEC; D-440 |

## 9. ÖLÇÜLEMEDİ / AÇIK (10 Eylül)

- x11/drm/rtsp kiplerinin **Jetson'da** koşumu; GNOME autostart'ın `sh -c` Exec ayrıştırması.
- DP→HDMI→dönüştürücü EDID/HPD davranışı; `set_mode=1` kip seçimi; xorg şablonu.
- Camdan cama gecikme (eşik ≤ 1,0 s); Jetson CPU yükü (gösterici + x264).
- Dönüştürücü 12 V besleme yolu; hava birimi modeli ve gerilim aralığı.
- IMX477'nin JetPack 7.2.1'de çalışması (12 Eylül ilk test; yedek USB UVC).
- 5,8 GHz güç / BTK 25 mW e.i.r.p. uyumu.
- `gst-launch-1.0 -v` nabız satırı biçimi (DRM gözetmeninin boru ilerlemesi denetimi) ve `identity`'nin boruya etkisi, `-v` satırlarının zamanında gelmesi / `stdbuf -oL` (T228-D).
- Dönüştürücünün canlı kodeki (H.264/H.265 çelişkili).
