# Jetson'ın gerçek durumu — geçmiş kayıtlardan yeniden kurgulandı (20 Eyl 2026)

> Kullanıcı: *"jetson çalışıyor sadece toplu derli değil, geçmişe bakarak aslında ne durumda
> olduğunu öğrenebilirsin."*
> Bu belge **tahmin değil**: kaynağı `results/jetson_20260919/` altındaki ham dökümlerdir
> (`durum_once.txt` 19 Eyl 16:13, `durum_once_2.txt` 16:13:39, `ag_testi.json`,
> `tunel_dinleme_60s.json`) ve `BILGILENDIRME_HE/03`.
> Etiketler: **KESİN** (dökümde yazıyor) · **MUHTEMEL** (çıkarım) · **TEST EDİLMELİ**.

---

## 1. 🟢 En önemli bulgu: Jetson'a kablosuz/ethernetsiz girilebilir

```
enP8p1s0         UP     169.254.201.50/16   10.21.8.7/24
l4tbr0           DOWN   192.168.55.1/24
```

**KESİN.** `l4tbr0` = L4T USB aygıt-kipi köprüsü ve **Jetson'da kurulu**. `DOWN` olmasının
sebebi arıza değil, **o an USB kablosunun takılı olmamasıdır**.

**Sonuç:** Jetson'ın USB-C portuna bir **veri kablosu** takıp diğer ucu bir PC'ye sokmak
yeterlidir → Jetson `192.168.55.1` adresinde belirir. Sürücü, wifi taraması, parola, dongle
gerekmez. `ssh n4vitas@192.168.55.1`.

⚠ Şarj-only kablo iş görmez, **veri kablosu** olmalı. PC tarafında yeni bir ağ arayüzü
(`usb0` / `enp...u...`) çıkmalıdır; çıkmıyorsa kablo şarj kablosudur.

---

## 2. Servisler — hepsi systemd altında, `enabled`

**KESİN** (19 Eyl 16:13 dökümü):

| Servis | Durum (o an) | İş |
|---|---|---|
| `navitas-cogullayici` | active running | MAVProxy — **seri Pixhawk'ın tek sahibi** (CONTRACTS 7.4) |
| `navitas-seri-hub` | active running | UDP loopback dağıtıcı + tünel ucu |
| `navitas-iha-inis-yayinci` | active running | Pixhawk kanıtlı `IHA_LANDED` |
| `navitas-iha-komut-alici` | active running | YKS PARACHUTE/ARM → COMMAND_LONG |
| `navitas-kamera-koprusu` | active running | CSI kamera → MJPEG `127.0.0.1:8080` |
| `navitas-rpi-inference` | 🔴 **activating auto-restart** | üretim algı yolu — **o an ÇÖKME DÖNGÜSÜNDE** |

---

## 3. "Derli toplu değil"in kaynağı: üç ayrı Python — ama **kasıtlı ve kayıtlı**

**KESİN** (`/etc/navitas.env` dökümü):

| Python | Kim kullanıyor | Neden |
|---|---|---|
| `/opt/navitas/python/bin/python` | seri_hub, iniş yayıncısı, komut alıcı, rpi_inference | navitas üretim ortamı |
| `/home/n4vitas/venv312/bin/python` | MAVProxy | MAVProxy kendi venv'inde |
| `/usr/bin/python3` | kamera köprüsü (`KAMERA_PYTHON=/usr/bin/python3`) | `nvarguscamerasrc` / GStreamer bağları **yalnız sistem Python'unda** var |

**Hüküm:** dağınık *görünüyor* ama üçü de `/etc/navitas.env` içinde tanımlı. Bu bir kaza değil,
belgelenmiş bir düzen. **Birleştirmeye çalışmak zarar verir** (kamera sistem Python'suz açılmaz).

---

## 4. `/etc/navitas.env` — sahada geçerli yapılandırma (KESİN)

```
NAVITAS_KOK=/home/n4vitas/navitas      KIP=tunel        SYSID=1
PIXHAWK_SERI=/dev/ttyTHS1  57600       SIK_SERI=/dev/ttyUSB0  57600
COGULLAYICI_EK_ARGS=--out udp:127.0.0.1:14553 --streamrate -1
HUB_TASIYICI_ARGS=--tunel 127.0.0.1:14553 --tunel-kimlik hava
RPI_EK_ARGS=--fov 54 --kaynak http://127.0.0.1:8080/video --gorev-kaydi .../gorev
KAMERA_KOPRU_BIND=127.0.0.1  PORT=8080     GOSTERICI_KIP=kapali
```

- **FOV 54 zaten ayarlı** (Halil'in ölçümü 53–54° ile uyumlu).
- Kamera köprüsü **yalnız `127.0.0.1`'e bağlanıyor** → dışarıdan erişilemez, bu yüzden
  `ag_testi.json`'da 8080 "bağlantı reddedildi" verdi. **Arıza değil, tasarım.**
  Dışarıdan bakmak için SSH port yönlendirme şart (`ssh_yonlendir.py`).

### 🟡 Gizli tuzak: MAVProxy komut satırında ÇELİŞEN iki bayrak

```
mavproxy.py ... --streamrate 8 ... --out udp:...:14553 --streamrate -1
```

`--streamrate` **iki kez** geçiyor: birim dosyasında 8, `COGULLAYICI_EK_ARGS`'tan gelen -1.
argparse'ta **sonuncusu kazanır** → fiilen `-1`. Şu an istenen davranış bu, ama satır
kırılgandır: `COGULLAYICI_EK_ARGS` sırası değişirse akış hızı sessizce 8'e döner.
**TEST EDİLMELİ / düzeltilmeli** (uçuş sonrası): tek bir yerde tanımlansın.

---

## 5. 19 Eyl 16:13'te ne bozuktu — ve bugün ne değişti

**KESİN (o an):**
- `rpi_inference` **restart counter 32**. Her turda: `model: navitas_seg_v36_best.pt ·
  kayıt doğrulaması: eşleşti` → sonra `Kamera acilamadi (kaynak='http://127.0.0.1:8080/video')` → çıkış.
- Kamera köprüsü: `No cameras available`, **deneme 1130**, `/dev/video*` **yok**.
  Yani kamera o an fiziksel olarak yoktu (kablo ters pin — `BILGILENDIRME_HE/03`).

**Bugün (MUHTEMEL, doğrulanmalı):** iki düzeltme sonrası bu tablo değişmiş olmalı —
kamera kablosu onarıldı **ve** `67467c4f` kuruldu (kamera yoksa servis artık çıkmıyor,
bekleyip yeniden açıyor). Yani `rpi_inference` **ayakta kalıyor** olmalı.
**TEST EDİLMELİ:** ilk SSH'de `systemctl is-active navitas-rpi-inference` + restart counter.

---

## 6. 🔴 Şartname açığı — dökümde açıkça yazıyor

Her `rpi_inference` açılışında bu satır basılıyor (**KESİN**):

> `UYARI: --ub-referans verilmedi ya da canli telemetri yok — HEARTBEAT'e x,y EKLENMEZ;`
> `YKS ALAN IHLALI denetimi YAPILAMAZ (sartname SS6.2/SS6.4).`

**Anlamı:** YKS, İHA'nın alan sınırını ihlal edip etmediğini **denetleyemiyor**.
Bu, kod hatası değil **eksik parametre** (`--ub-referans`) ve şartnamenin iki maddesine dokunuyor.
`RPI_EK_ARGS` içinde `--ub-referans` **yok**. Bu bulgu uygunluk tablosuna eklendi.

---

## 7. Telsiz/tünel akışı — 60 saniyelik ölçüm (KESİN)

`tunel_dinleme_60s.json`: 60 s'de **58 heartbeat** (sysid 1, ~1 Hz) ve **tek bir TUNNEL çerçevesi**.

**Yorum (MUHTEMEL):** taşıyıcı sağlıklı çalışıyordu; TUNNEL'in neredeyse hiç akmaması
`rpi_inference`'ın çökme döngüsünde olmasındandır — karar üretilmiyordu, gönderilecek şey yoktu.
Kamera onarıldıktan sonra bu sayının **çok yükselmesi beklenir**; yükselmiyorsa algı yolu hâlâ ölüdür.

---

## 8. Küçük ama kayda değer

- **`sudo parolasız: HAYIR`** → uzaktan `reboot`/systemd değişikliği yapılamaz. Servisi yeniden
  başlatmak için sudo gerekmiyor: `kill $(systemctl show -p MainPID --value navitas-rpi-inference)`
  (birimler `Restart=always`, `User=n4vitas`).
- **`seri_hub` öğrenilen tüketici tavanı (32) aşıldı** — her test betiği yeni bir efemer port
  açtığı için tablo doldu ve en eskisi düşürüldü. Uzun ömürlü tüketiciler statik `--tuketici`
  ile verilmeli. Yeni onay test aracımız **sabit port (5193)** kullanıyor, bu sorunu üretmiyor.
- **Model kayıt doğrulaması `eşleşti`** — `navitas_seg_v36_best.pt` beklenen sürüm.
- **RTC pili yok** → NTP gelene kadar saat yanlış; açılış anı zaman damgalarına güvenilmez.
- PreArm (kapalı alan, beklenen): `RC not found`, `Hardware safety switch`,
  `Compasses inconsistent`, `GPS 1: Bad fix`, `Fence requires position`.

---

## 9. İlk SSH açıldığında koşulacak sıra (hazır)

```bash
systemctl is-active navitas-rpi-inference navitas-kamera-koprusu navitas-seri-hub navitas-cogullayici
systemctl show -p NRestarts --value navitas-rpi-inference      # cokme dongusu var mi
journalctl -u navitas-rpi-inference --since '-2min' -o cat | tail -30
ls /dev/video*                                                  # kamera fiziksel olarak var mi
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/kare.jpg
sha256sum ~/navitas/codes/rpi_inference.py ~/navitas/codes/karar_sozlesmesi.py
ls -la ~/kara_kutu/ | tail -5
```

Beklenen: dört servis `active`, `NRestarts` artmıyor, `/dev/video0` var, `kare.jpg` **200**,
sha'lar `6fe5819b` / `3bc18e5d` (tutmuyorsa `uygula.py` **koşulmaz**, elle incelenir).
