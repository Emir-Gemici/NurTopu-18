# Dron + RPi5 Canlı Görüntü — Kurulum ve Saha Kılavuzu

Hocanın dronuna RPi5 + CSI kamera takılır; görüntü **internetsiz**, RPi'nin kendi
WiFi hotspot'u üzerinden laptopa canlı akar (ham 720p + model overlay).

> **Not:** RPi5'te WiFi **dahili** vardır (ayrı modül gerekmez). İnternet olmaması
> sorun değil — hotspot yerel bir ağdır, internete çıkmaz.

```
[dron]  RPi5 + CSI kamera ──(RPi'nin WiFi hotspot'u, internet YOK)── laptop
         rpi_yayin.py            udp 5599 (el sıkışma + kalp atışı)   pc_izleyici.py
                                 udp 5600 (ham H.264 720p)
                                 udp 5601 (AI overlay ~2-5fps)
                                 udp 5602 (telemetri JSON, 2 sn'de bir)
```

Dayanıklılık: izleyici 2 sn'de bir kalp atışı yollar; bağlantı koparsa RPi 8 sn
sonra yayını durdurur (boşa CPU/bant harcamaz), izleyici geri gelince otomatik
sürer. El sıkışma aynı zamanda saat eşitlemesi yapar → izleyici uçtan uca
gecikmeyi (ms) canlı gösterir. Ortak protokol tanımları `drone/ortak.py`'de.

---

## 0. GERÇEK KURULUM NOTLARI — Ubuntu 26.04'te yapıldı (2026-07-03, KANITLI)

> Bu bölüm sahada/tekrar kurarken şaşırmamak için **fiilen çalışan prosedürü** ve
> karşılaştığımız tuzakları özetler. Aşağıdaki 1-5. bölümler Raspberry Pi OS içindi;
> elimizdeki kartta **Ubuntu Server 26.04 LTS (arm64)** kuruluydu ve farklı adımlar gerekti.
> Sistem gerçek Pi 5 + Camera Module 3 (imx708) ile uçtan uca **çalışır durumda kanıtlandı.**

**Cihaz:** Raspberry Pi 5, Ubuntu 26.04, kullanıcı `navitas` / şifre `navitas2026`,
hostname `navitas`. Monitör/klavye yoktu → başsız (headless) kuruldu.

**Kurulum-için-internet (sahada değil, geliştirme masasında):** RPi ethernet ile laptopa
bağlandı; laptop (Fedora) NetworkManager "shared" ile interneti paylaştı → RPi 10.42.0.247.
Fedora'da gerekenler: `sysctl net.ipv4.ip_forward=1`, ethernet arayüzü firewalld `trusted`
zone'a, wifi zone'da `--add-masquerade`, ve `trusted→wifi` forward'a izin veren firewalld
**policy**. (Kampüs "Student" wifi'ı ICMP/ping engelliyordu ama HTTP/apt çalışıyordu — ping
ile test etme, yanıltır.)

**Tuzaklar ve çözümleri (Ubuntu 26.04 / Pi 5):**
1. **Saat:** Pi 5'te pilli RTC yok → her boot saat geçmişe düşer, apt "future-dated release"
   der. Çözüm: `sudo date -u -s "<doğru UTC>"` + `apt install fake-hwclock`. Her boot sonrası
   saati kontrol et (NTP kampüste kapalıydı).
2. **Kamera:** Ubuntu'nun `camera_auto_detect=1`'i imx708'i yakalamadı. Çözüm:
   `/boot/firmware/config.txt`'ye **`dtoverlay=imx708,cam0`** ekle + reboot → algılandı.
   Kullanıcıyı `video,render` gruplarına ekle (dmaHeap izni). Doğrula: `rpicam-hello --list-cameras`.
3. **Python paketleri:** venv `--system-site-packages` ŞART (picamera2 sistem paketi).
   `pip install ultralytics ncnn` torch'u (arm64) çeker. İKİ tuzak: (a) `/tmp` sadece 2GB
   tmpfs → torch açılırken taşar ("disk kotası"); çözüm `TMPDIR=~/piptmp` (gerçek disk).
   (b) Python 3.14 çok yeni ama torch 2.12 wheel'i var; kampüs wifi indirmeyi kesince
   `pip install --retries 20 --timeout 120`. (Not: gereksiz nvidia-cuda-* paketleri de
   iniyor, ARM'de kullanılmaz, `pip uninstall` ile yer açılabilir.)
4. **⚠️ picamera2 H264 encoder BOZUK (Ubuntu 26.04):** `from_ndarray() unexpected kwarg
   'width'` (picamera2↔PyAV uyumsuzluğu) → kamera döngüsünü kilitliyordu. Çözüm KODDA
   çözüldü: `rpi_yayin.py` ham yayını picamera2 encoder'ı yerine **ffmpeg libx264
   zerolatency**'e main kareleri besleyerek yapıyor (Pi 5'te donanım H264 yok zaten).
   Ek kurulum gerektirmez, sadece bilinmesi için.

**Kanıtlanan sonuç:** ham H.264 720p + AI overlay ("AÇIK YOL: SOL/ORTA/SAG güven + yeşil
maske") canlı aktı. Kablolu (ethernet) %0 kayıp; kablosuz (RPi hotspot NAVITAS) çalışıyor
ama ~%16-17 AI kare kaybı (bkz `--ai-kalite`; büyük çözüm: vektör-overlay, TODO). CPU ~70°C
(drona soğutucu/hava akışı iyi olur). İnternet tamamen kesikken de akış sürdü (kanıtlandı).

**Bilinen kararsızlık:** kullandığımız USB ethernet adaptörü ara ara düştü (masaüstü testinde
donmalar bundan). Dron gününde ethernet yok, wifi hotspot kullanılacağı için bu yaşanmaz.

---

## 1. Evde/okulda hazırlık (İNTERNETLİ ortamda, BİR KEZ)

Sahada internet yok; tüm kurulum önceden yapılır.

### 1.1 İşletim sistemi + paketler
- RPi OS **Bookworm 64-bit** (Raspberry Pi Imager ile; SSH'ı imager'da etkinleştir).
- Paketler:
  ```bash
  sudo apt update
  sudo apt install -y python3-picamera2 ffmpeg python3-opencv git
  ```
- Python ortamı (picamera2 sistem paketi olduğundan `--system-site-packages` ŞART):
  ```bash
  python3 -m venv --system-site-packages ~/navitas-venv
  source ~/navitas-venv/bin/activate
  pip install ultralytics ncnn
  ```

### 1.2 Proje dosyalarını RPi'ye gönderme

**Yöntem A — doğrudan laptoptan rsync (git/GitHub GEREKMEZ, önerilen):**
Laptopta, repo kökünde çalıştır (kullanıcı adı ve IP'yi kendine göre değiştir;
IP'yi bilmiyorsan bkz **3.5** — hotspot'taysa `10.42.1.1`, ethernet paylaşımında
bizde `10.42.0.247`):

```bash
cd ~/trs/github/navitas
rsync -avz --relative --exclude '__pycache__' \
    drone codes simulation/scripts/iha_perceive.py  navitas@10.42.1.1:navitas/
rsync -avz navitas_model/navitas_seg_v2_ncnn_model/  navitas@10.42.1.1:navitas/codes/best_ncnn_model/
```

İlk komut kodu dizin yapısını koruyarak `~/navitas/` altına kurar (drone/, codes/,
simulation/scripts/ — `rpi_yayin.py` bu yerleşimi bekler). İkincisi GÜNCEL v2 NCNN
modelini `codes/best_ncnn_model/` adına koyar (⚠️ v2'yi gönder; `models/best_ncnn_model`
ESKİ 2026-05 v1 modelidir). Kod değişince aynı komutları tekrar çalıştır — rsync
sadece farkları gönderir.

**Yöntem B — git clone (GitHub erişimi varsa):**
```bash
git clone <navitas repo> ~/navitas
cp -r ~/navitas/navitas_model/navitas_seg_v2_ncnn_model ~/navitas/codes/best_ncnn_model
```

### 1.3 Kamera modülünü RPi5'e bağlama (adım adım)

⚠️ **Kablo uyarısı:** RPi5'in kamera konektörü **22-pin küçük (0.5 mm)** tiptir.
Kamera modülleri genelde eski **15-pin geniş** kabloyla gelir — bu kablo RPi5'e
TAKILMAZ. Gereken: **"RPi 5 camera cable" (15-pin → 22-pin dönüştürücü şerit)**,
birkaç dolarlık standart parça. Elindeki kablonun iki ucuna bak: bir ucu dar
(22-pin, RPi5 tarafı) değilse bu kabloyu edinmen gerekir.

1. RPi'yi **kapat, güç kablosunu çek** (konektörler kırılgandır, elektrikliyken takma).
2. RPi5'te iki kamera konektörü vardır: Ethernet portunun yanında **CAM/DISP 0** ve
   **CAM/DISP 1** yazılı iki yassı yuva. İkisi de olur; **CAM1**'i kullan (karışıklık olmasın).
3. Yuvadaki **siyah/kahverengi mandalı tırnakla yukarı hafifçe kaldır** (tamamen çıkmaz,
   ~2 mm kalkar ve gevşer).
4. Şerit kabloyu tak: **metal (altın) temas uçları Ethernet portuna bakacak** şekilde,
   dibe kadar. Eğik girmesin — iki kenar aynı derinlikte olmalı.
5. Mandalı **aşağı bastırarak kilitle**. Kablodan nazikçe çek: çıkmıyorsa oturmuştur.
6. Aynısını kamera tarafında yap (kamera kartındaki mandal — temaslar kamera lensinin
   BAKTIĞI yöne göre modülüne göre değişir; kamera kitinin kablosu zaten takılı
   geldiyse hiç sökme, sadece RPi ucunu tak).
7. Gücü ver ve doğrula:
```bash
rpicam-hello --list-cameras     # kamera listede görünmeli (imx708 vb.)
rpicam-still -o /tmp/test.jpg   # kare çekebilmeli
```
Görünmüyorsa: mandal tam kilitli mi, kablo düz mü (kıvrım/çatlak?), temas yönü doğru mu
kontrol et; `sudo raspi-config`'te kamera ayarına bakmana Bookworm'da gerek yok
(otomatik algılanır).

### 1.4 Hotspot (kalıcı, açılışta otomatik)
```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid NAVITAS password navitas2026
sudo nmcli connection modify Hotspot connection.autoconnect yes \
    connection.autoconnect-priority 100
```
- RPi'nin adresi hotspot'ta **10.42.1.1** olur (bizde kanıtlı; NetworkManager
  ethernet paylaşımına 10.42.0.x'i verdiği için wifi hotspot'a 10.42.1.x düşer);
  laptop `NAVITAS` ağına bağlanınca DHCP alır.
- ⚠️ Hotspot açıkken RPi başka WiFi'a bağlanamaz → **internet gerektiren işleri
  bundan önce bitir.** Geri dönüş: `sudo nmcli connection down Hotspot`.

### 1.5 Yayının açılışta otomatik başlaması (önerilir — sahada ekran/SSH gerekmez)
```bash
sudo tee /etc/systemd/system/navitas-yayin.service > /dev/null <<'EOF'
[Unit]
Description=Navitas dron yayini
After=network-online.target

[Service]
User=pi
ExecStart=/home/pi/navitas-venv/bin/python3 /home/pi/navitas/drone/rpi_yayin.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable navitas-yayin
```
(`pi` yerine gerçek kullanıcı adını yaz. Kamera ters monteliyse `ExecStart` satırının
sonuna ` --dondur 180` ekle; montaj değişirse `sudo systemctl restart navitas-yayin`.)

### 1.6 Evde uçtan uca prova (SAHAYA GİTMEDEN MUTLAKA)
1. RPi'yi yeniden başlat (hotspot + servis otomatik kalkmalı).
2. Laptopta `NAVITAS` ağına bağlan (şifre: navitas2026).
3. `python3 drone/pc_izleyici.py` → iki pencere: **NAVITAS HAM** (720p) + **NAVITAS AI**
   (overlay + altta istatistik bandı: izleyici fps / uçtan uca gecikme / kayıp % /
   RPi fps / çıkarım ms / CPU sıcaklığı / karar / RTT).
4. Gecikmeye bak: elini kameraya salla, ham pencerede < ~0.5 sn olmalı;
   AI bandındaki `gecikme=` değeri çıkarım süresi + ağ toplamıdır.

### 1.7 Donanımsız test (protokolün tamamı, herhangi bir bilgisayarda)

```bash
# otomatik: 16 kontrol (el sıkışma, H.264, AI akışı, telemetri, kopma/yeniden bağlanma)
.venv/bin/python drone/test_uctan_uca.py

# elle: bir uçta sahte-kamera yayını, diğer uçta gerçek izleyici
.venv/bin/python drone/rpi_yayin.py --sim test_images/ai
.venv/bin/python drone/pc_izleyici.py --rpi-ip 127.0.0.1        # ayrı terminalde
```

`--sim KAYNAK` görsel klasörü / video / tek görsel alır; ham H.264 dahil aynı kod
yolu çalışır (kameranın yerini sahte kaynak alır). Kod değişikliğinden sonra
`test_uctan_uca.py` çalıştırmak yeterli.

---

## 2. Dron montajı (BANT/YAPIŞTIRMA — dron elektroniğine BAĞLANMAZ)

Sistem dronun elektroniğinden **tamamen bağımsız çalışır**: dron kendi kumandasıyla
uçar, RPi sadece "yük" olarak taşınır. Dronla hiçbir kablo bağlantısı gerekmez.

- **Sabitleme:** dronun **alt gövdesine** cırt bant (velcro) / kablo bağı / çift
  taraflı köpük bant. Köpük bant titreşimi de emer (görüntü titremesini azaltır).
  Uçuş öncesi sallayarak test et — düşen RPi hem kayıptır hem tehlike.
- **Kamera yönü:** **aşağı bakacak** (nadir; görev senaryosuyla aynı). Bant montajında
  modül ters/dönük kaldıysa sökmene gerek yok: `--dondur 180` parametresi görüntüyü
  yazılımda çevirir (ham + AI her iki yayına birden uygulanır).
- **Güç:** RPi5 5V ister (ideal 5A; 5V/3A ile de çalışır, throttle olabilir).
  En pratik çözüm: küçük bir **powerbank** (RPi'yle birlikte banta sar). Alternatif:
  dron bataryasından 5V BEC/UBEC (≥3A) — ama bu lehim/kablo işi gerektirir, powerbank
  varken gerek yok.
- **Ağırlık:** RPi+kamera+powerbank+bant ~200-400 g. ⚠️ Uçuş öncesi hocaya dronun
  taşıma kapasitesini sor; ağırlığı gövde merkezine yakın koy (denge bozulmasın).
- **Şerit kablo:** pervane akışından uzak, gövdeye bantla — rüzgârda titreyen kablo
  konektörden çıkabilir.
- **SD kart:** kaliteli/hızlı (A1/A2) olsun; sarsıntıda ucuz kartlar sorun çıkarır.

## 3. Çalıştırma komutları

### 3.0 İlk kez kuruyorsan sıralama şu (BİR KEZ yapılır)

```bash
ssh pi@<rpi-ip>                       # ev ağında IP'yi router'dan öğren (veya: ssh pi@raspberrypi.local)
# 1) paketler + venv        → README 1.1  (İNTERNET GEREKİR — hotspot'u AÇMADAN yap)
# 2) projeyi indir + model  → README 1.2  (git clone ... BİR KEZ; her seferinde değil)
# 3) kamera testi           → README 1.3
# 4) hotspot + servis       → README 1.4 + 1.5
```

Kurulumdan sonra RPi hotspot modundadır → adresi HEP `10.42.1.1` olur ve
(servis kurulduysa) yayın güç verilince KENDİLİĞİNDEN başlar; ssh + komut gerekmez.

### 3.1 En yaygın kullanım

```bash
# LAPTOP (NAVITAS WiFi'ına bağlandıktan sonra) — günlük tek komut bu:
.venv/bin/python drone/pc_izleyici.py                      # izle (AI penceresi; --ham = ayrıca ham pencere)
.venv/bin/python drone/pc_izleyici.py --kayit ucus1.mp4    # izle + kaydet

# RPi'de ELLE çalıştırmak gerekirse (servis yoksa/durdurduysan):
ssh navitas@10.42.1.1        # şifre: navitas2026 (ethernet'teyse IP için bkz 3.5)
source ~/navitas-venv/bin/activate
python3 ~/navitas/drone/rpi_yayin.py                # varsayılan: kamera + model, çevirme YOK
python3 ~/navitas/drone/rpi_yayin.py --dondur 180   # SADECE kamera ters yapıştırıldıysa
```

`--dondur` yazmazsan 0 kabul edilir = görüntüye dokunulmaz (düz montaj). Yani
çevirmeye ihtiyaç yoksa hiçbir şey eklemezsin; `--dondur 0` yazmak da aynı şey.

### 3.2 rpi_yayin.py — tüm parametreler (yaygından seyreğe)

| Parametre | Varsayılan | Ne yapar / ne zaman |
|---|---|---|
| *(parametresiz)* | — | Kamera + model, izleyici bekler. Normal kullanım. |
| `--dondur 180` | `0` (çevirme) | Kamera ters monteliyse görüntüyü çevirir (ham+AI). Düz montajda YAZMA. |
| `--ai-fps 3` | `0` (serbest) | Çıkarımı sınırlar → CPU/ısı düşer. Uzun uçuşta, RPi ısınıyorsa. |
| `--ai-kalite 40` | `55` | AI overlay JPEG kalitesi. Düşük = küçük kare = az UDP parçası = **wifi'da az kare kaybı**. Uzak/parazitli linkte 40-45'e düşür. |
| `--no-ai` | kapalı | Model hiç yüklenmez, sadece ham yayın. İlk kamera denemesi / model sorunuysa. |
| `--bitrate 2000000` | `4000000` | Ham H.264 bant genişliği (bps). Menzil sınırında görüntü bozuluyorsa düşür. |
| `--debug` | kapalı | Ayrıntılı log. Sorun ararken. |
| `--log-file X.log` | yok | Logları dosyaya da yazar. Uçuş kaydı/sonradan inceleme. |
| `--conf 0.15` | `0.15` | Model eşiği. Normalde DOKUNMA (0.05 fallback zaten var). |
| `--imgsz 512` | `512` | Model girdi boyutu. Büyütmek fps düşürür; normalde dokunma. |
| `--sim KAYNAK` | yok | Kamerasız test: görsel klasörü/video. Sadece geliştirme için. |

### 3.3 pc_izleyici.py — tüm parametreler (yaygından seyreğe)

| Parametre | Varsayılan | Ne yapar / ne zaman |
|---|---|---|
| *(parametresiz)* | — | 10.42.1.1'e (hotspot) bağlanır, TEK büyütülebilir AI penceresi açar. Normal kullanım. |
| `--kayit ucus1.mp4` | yok | AI yayınını (istatistik bandıyla) mp4 kaydeder. Uçuş arşivi. |
| `--rpi-ip 192.168.1.x` | `10.42.1.1` | RPi hotspot'ta DEĞİLSE (ethernet paylaşımı 10.42.0.x / ev ağı; bkz 3.5). |
| `--ham` | kapalı | AYRICA ham (overlaysiz) kamerayı ayrı ffplay penceresinde gösterir. |
| `--headless` | kapalı | Pencere yok, konsola istatistik. SSH'tan izleme. (DISPLAY yoksa otomatik.) |
| `--debug` / `--log-file` | kapalı/yok | Ayrıntılı log / dosyaya yaz. Sorun ararken. |

Her iki betikte `--help` bu listeyi gösterir.

### 3.4 Saha günü akışı

1. RPi'ye güç ver (dron yerde) → ~40 sn içinde hotspot + yayın servisi kalkar.
2. Laptop → `NAVITAS` WiFi → yukarıdaki izleyici komutu.
3. Görüntü iki pencerede de akıyorsa uçuşa hazır. `q` = çıkış; izleyici kapanıp
   yeniden açılabilir, yayın kaldığı yerden devam eder.
4. **Menzil:** açık alanda ~30-80 m beklenir (RPi dahili anten). Görüntü koparsa
   dron yaklaştırılınca kendiliğinden geri gelir (UDP, oturum tutmaz).

### 3.5 RPi'nin IP adresini bulma (SSH atacağım ama IP'yi bilmiyorum)

Mantık hep aynı: **(1)** hangi ağdaysan kendi IP'nden ağ aralığını çıkar,
**(2)** o aralığı tara, **(3)** çıkanlar arasından Pi'yi MAC adresi/hostname ile ayırt et.
Ama önce taramasız kısayollara bak — çoğu durumda gerek kalmaz:

**Kısayollar (önce bunları dene):**

| Durum | RPi'nin IP'si |
|---|---|
| RPi kendi hotspot'unu açmış (NAVITAS ağındasın) | **10.42.1.1** (sabit — hotspot'ta RPi ağın kapısıdır, tarama gerekmez) |
| RPi ethernet'le laptopa bağlı (paylaşımlı bağlantı) | 10.42.0.x — bizde **10.42.0.247** çıkıyordu; değiştiyse aşağıdaki taramayla bul |
| Aynı ağda mDNS çalışıyorsa | `ssh navitas@navitas.local` dene (hostname = navitas; her ağda çalışmaz, tutarsa tarama gerekmez) |
| Ev ağı (modeme ikisi de bağlı) | Modemin arayüzünden DHCP istemci listesine bak; ya da aşağıdaki tarama |

**Tarama yöntemi (adım adım):**

1. **Kendi ağını öğren** — laptopta:
   ```bash
   ip -4 addr show
   ```
   Aktif arayüzde `inet 192.168.1.34/24` gibi bir satır görürsün. `/24` şu demek:
   ilk üç blok ağı tanımlar → taranacak aralık `192.168.1.0/24`
   (yani 192.168.1.1–254 arası tüm adresler).

2. **Aralığı tara** — `nmap` ile (yoksa: `sudo dnf install nmap`):
   ```bash
   sudo nmap -sn 192.168.1.0/24
   ```
   `-sn` = "ping taraması": port karıştırmadan sadece "kim ayakta?" diye sorar.
   `sudo` ile çalıştırmak önemli — o zaman nmap MAC adreslerini ve üretici adını da
   gösterir; Pi şöyle görünür:
   ```
   Nmap scan report for 192.168.1.87
   MAC Address: 2C:CF:67:XX:XX:XX (Raspberry Pi Trading)
   ```
   Bizim Pi 5'in MAC'i **2c:cf:67** ile başlar — listede bunu ara.

3. **Ping engelliyse** (kampüs ağı ICMP'yi kesiyor, `-sn` boş dönebilir!) doğrudan
   SSH portunu tara:
   ```bash
   nmap -p 22 --open 192.168.1.0/24
   ```
   Bu, her adreste TCP 22'yi dener ve sadece SSH'ı açık olanları listeler —
   ping yasak olsa da çalışır. Çıkan adreslere `ssh navitas@<ip>` dener, karşılayan Pi'dir.

4. **Alternatif: ARP tablosu** — tarama sonrası (veya broadcast ping sonrası) işletim
   sistemi gördüğü cihazları ezberler:
   ```bash
   ip neigh
   ```
   Listede `2c:cf:67` MAC'li satırın IP'si Pi'dir. (Ethernet doğrudan bağlıysa çoğu
   zaman tek başına bu yeter, nmap'e bile gerek kalmaz.)

5. **Bağlan:**
   ```bash
   ssh navitas@<bulduğun-ip>       # şifre: navitas2026
   ```

> ⚠️ İki tuzak: (a) Laptop ile RPi **aynı ağda olmalı** — laptop ev wifi'ında, RPi
> NAVITAS hotspot'undaysa hiçbir tarama onu bulamaz. (b) Kampüs gibi "istemci
> izolasyonu" yapan ağlar cihazların birbirini görmesini tamamen engelleyebilir —
> o zaman çözüm tarama değil, RPi'yi ethernet'le ya da hotspot'la kendi ağına almaktır.

## 4. Sorun giderme

| Belirti | Muhtemel neden / çözüm |
|---|---|
| `hello: cevap yok` | Laptop NAVITAS ağında mı? RPi açık mı? `ping 10.42.1.1`. IP farklıysa bkz 3.5 |
| RPi'nin IP'sini bilmiyorum | bkz **3.5** — kısayollar + nmap taraması |
| HAM penceresi siyah | ffplay ilk kareyi bekliyor (birkaç sn); sürüyorsa RPi'de servisi kontrol: `journalctl -u navitas-yayin -f` |
| AI penceresi yok/donuk | Model yüklemesi ~15-30 sn sürer; `codes/best_ncnn_model` kopyalandı mı? |
| `picamera2 yok` hatası | venv `--system-site-packages` ile mi kuruldu? |
| Kamera açılmıyor | Başka süreç kamerayı tutuyor olabilir: `sudo systemctl stop navitas-yayin` deyip elle çalıştır |
| Görüntü çok gecikmeli | Laptop 2.4GHz'e bağlanmış olabilir; kalabalık ortamda 5GHz dene (`nmcli` ile hotspot band a) |

## 5. Bilinçli sınırlar

- AI overlay RPi5 CPU'da **~2-5 fps** (NCNN, 512px) — karar akışı için yeterli,
  video akıcılığı beklenmesin; ham yayin 30 fps'dir.
- WiFi menzili sınırlıdır; şartnamedeki 300 m/915MHz linki video taşımaz — bu kurulum
  **test/gösterim** içindir, yarışma haberleşme mimarisinin yerine geçmez.
- Kayıt yalnızca AI yayını için var (`--kayit`); ham 720p'yi de kaydetmek istersek
  izleyicide ffplay yerine `ffmpeg`'e geçeriz (izle + kaydet aynı anda).
- AI kararı `iha_perceive._infer` ile üretilir (letterbox + conf-fallback + karanlıkta
  ışık-normalize çift koşu) — sim/İHA algısıyla AYNI kanıtlanmış boru hattı.
