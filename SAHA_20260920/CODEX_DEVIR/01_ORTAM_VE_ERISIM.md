# 01 — Ortam, erişim ve Jetson'ın bugünkü hâli

## Bu makine (mimar oturumunun koştuğu yer)

**Linux**, Fedora 44, `/home/trs/projects/navitas-unified-20260822`, dal `master`.
⚠ `CLAUDE.md §13` Windows yorumlayıcısını söyler (`O:\navitas-local-train\venv\...`).
**Burası o makine değil.** Burada `python3` = **3.14.7**, sistem Python'u.

### 🔴 Bu makinede genel kapı KOŞAMAZ

```
numpy · opencv · pymavlink   → KURULU DEĞİL
pyserial 3.5                 → kuruldu (pip --user, 0,3 MB)
paramiko 5.0.0               → kuruldu (uygula.py icin)
tkinter                      → var
```

`codes/test_rota_sentetik.py` `cv2` + `numpy` ister. **Kapı kanıtı Windows makinesinden gelir.**
Kurmak istenirse Fedora deposunda hazır RPM var (`python3-numpy`, `python3-opencv`) — telefon
hotspot'uyla ~60–90 MB. **Kullanıcı onayı olmadan indirme.**

### Bu makine yedek YER İSTASYONU (D-519)

YKİ ve yönlendirici burada **koşar** (kanıt: `../kanit/yki_linux_20260920.png`).
Windows'tan tek fark seri port adı: `/dev/ttyUSB0` ↔ `COM7`.

```
cd /home/trs/projects/navitas-wt-bilgilendirme
python3 -B scripts/yer_yonlendirici.py --port /dev/ttyUSB0 --baud 57600 --tunel 127.0.0.1:14590
python3 -B comms/yks_gui.py --tunel 127.0.0.1:14590 --fda
```

## Git çalışma kopyaları

| Yol | Dal | Ne için |
|---|---|---|
| `/home/trs/projects/navitas-unified-20260822` | `master` | mimar oturumu, belgeler, `fda_gorev_uret.py` |
| `/home/trs/projects/navitas-wt-bilgilendirme` | `bilgilendirme-he` (324ce42b) | **saha yazılımı** — YKİ buradan açılır |
| `/home/trs/projects/navitas-tunel-olcum` | `tunel-saha-20260918` | eski ölçüm kopyası |

`master` `origin/master`'dan **1 ileri** (e4f4edc5 itilmemiş).
Bugünün işi **`SAHA_20260920/` commit edilmemiş** (`git status` → `?? SAHA_20260920/`).

## Jetson erişimi

### 🔴 Bugün öğrenilen: kablo yönü

Yurtta ethernet prizi yok, Jetson'da wifi yok. Çözüm **USB aygıt kipi** (`l4tbr0`):

```
LAPTOP (host) ──[A ucu]── kablo ──[C ucu]──► JETSON'ın TYPE-C portu
```

⚠ **A ucunu Jetson'a takmak işe yaramaz** — Jetson'ın Type-A portları *host*'tur, iki host
birbirine bağlanınca çekirdek **hiçbir şey görmez**. Bugün ~1 saat bu yüzden kaybedildi.
Doğru takıldığında:

```
Bus 003 Device 122: ID 0955:7020 NVIDIA Corp. L4T (Linux for Tegra) running on Tegra
enp0s20f0u6   192.168.55.100/24        Jetson: 192.168.55.1   (ping ~0,24 ms)
cdc_acm ttyACM0 de acilir — seri konsol yedek yol
```

### SSH — parolasız hazır

```
ssh jetson        # ~/.ssh/config icinde tanimli: 192.168.55.1, n4vitas, ~/.ssh/navitas_jetson
```

- Anahtar: `~/.ssh/navitas_jetson` (ed25519), Jetson'a yetkilendirildi.
- Parola **dosyada**: `~/.ssh/.nav_s` (chmod 600). **Belgeye yazma, ekrana basma.**
- Kullanıcı `n4vitas` (repo belgelerindeki `navitas` yanlıştır).
- **`sudo` parola ister** (`sudo -S`, parolayı stdin'den ver). Servis yeniden başlatmak için
  sudo GEREKMEZ: `kill $(systemctl show -p MainPID --value navitas-rpi-inference)`.
- RTC pili yok → NTP gelene kadar saat yanlış olabilir.

## Jetson'ın bugünkü hâli

### ⚠ Şu an KAPALI (kullanıcı, 20 Eyl akşamı)

Kapanma **yapılanları kaybetmez**: dosyalar diske yazıldı, servisler `enabled`.
Açılışta otomatik gelir. Açıldığında `00_OKU_BENI` → `02_GOREVLER` sırası izlenir.

### Bugün kurulan (uygula.py, denetim zinciri eksiksiz işledi)

```
yedek       rpi_inference 6fe5819b  ·  karar_sozlesmesi 3bc18e5d   (.yedek_20260919b)
.yeni       sha + ast uzakta dogrulandi
mv          rpi_inference → 6a03cd4f   (telemetri kapisi c9ee27f0)
            karar_sozlesmesi → 45646ab9
servis      yeni MainPID 4732 · active · NRestarts=0 · traceback YOK
korundu     IKA_IZ_GENISLIGI_M = 0.4595  (OLCULDU, D-472)
```

Kayıt: `/home/trs/projects/navitas-wt-bilgilendirme/results/jetson_20260919/kurulum2/kurulum_20260920_174444.json`

**Geri alma** (gerekirse):
```
cd ~/navitas/codes
mv rpi_inference.py.yedek_20260919b rpi_inference.py
mv karar_sozlesmesi.py.yedek_20260919b karar_sozlesmesi.py
kill $(systemctl show -p MainPID --value navitas-rpi-inference)
```

### Servisler (altı, hepsi `enabled`, bugün `NRestarts=0`)

`navitas-cogullayici` (MAVProxy, Pixhawk'ın tek sahibi) · `navitas-seri-hub` ·
`navitas-rpi-inference` · `navitas-kamera-koprusu` · `navitas-iha-inis-yayinci` ·
`navitas-iha-komut-alici`

### Kamera — bugün ÇALIŞTI

```
/dev/video0 var · i2c bus 9 adres 0x1a: UU (surucu bagladi)
kaynak_acik true · fps 10.02 · dusen_kare 0 · acma_denemesi 1
rpi_inference 799 kare okudu, 0 dusurdu, 0 yeniden acma
```
Kök neden **mekanikti**: CSI/FFC konnektörünün ZIF mandalı kırık (kamera modülü tarafında).
Kullanıcı bantla sabitledi, **güç döngüsünden sonra** geldi. ⚠ CSI **sıcak takılmaz**.

🔴 **Ama görüntü ODAKSIZ** — indirilen kare düz gri, köşelerde macenta.
`../kanit/kare_20260920.jpg`. Lens odağı **açık iş**, bkz. `02_GOREVLER.md` T-C.

⚠ Konnektör **bantla** duruyor. Uçuş titreşiminde açılabilir. Gerginlik azaltma şart.

### Üç ayrı Python — kasıtlı, "temizleme"

`/opt/navitas/python` (servisler) · `~/venv312` (MAVProxy) · `/usr/bin/python3` (kamera köprüsü;
`nvarguscamerasrc` bağları yalnız sistem Python'unda). Üçü de `/etc/navitas.env`'de tanımlı.
**Birleştirmeye çalışmak kamerayı öldürür.**

### Bilinen tuzak
MAVProxy komut satırında `--streamrate` **iki kez** geçiyor (birim dosyasında 8,
`COGULLAYICI_EK_ARGS`'tan -1). Son yazan kazanır → şu an -1, istenen bu.
`COGULLAYICI_EK_ARGS` sırası değişirse **sessizce** 8'e döner. Uçuş sonrası tek yere alınmalı.
