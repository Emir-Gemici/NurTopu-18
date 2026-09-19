# 03 — Jetson: durum, bekleyen kurulum, kapanmalar

Kanıtlar: defter D-509, D-510, D-512 (+devamı), D-513, D-516 ek 3–5. Dosyalar: `results/jetson_20260919/`.

## Erişim

- SSH kullanıcısı **`n4vitas`**. Repo belgelerindeki `navitas` yanlıştır.
- Okul ağında IP `10.21.8.7`. DHCP olduğu için değişebilir. Doğrudan kabloda link-local adres `169.254.201.50`.
- Parola ekipte. **Repoda yok.** Betikler parolayı `NAVITAS_SIFRE` ortam değişkeninden okur.
  PowerShell'de `$env:NAVITAS_SIFRE="..."`, Git Bash'te `export NAVITAS_SIFRE=...` ile verilir.
- Kod `~/navitas` altında. **Git deposu değil**, kopya paket. Hangi dosyanın hangi daldan geldiğini
  `results/jetson_20260919/jetson_manifest.py` sha256 ile çıkarır. Çıktısı `manifest_<zaman>.json/.md`.
- Uzaktan `sudo reboot` bu oturumda izinli değildi. Yeniden başlatma elle, güç döngüsüyle yapıldı.
- RTC pili yok. NTP gelene kadar saat yanlış olabilir; açılış anı zaman damgalarına güvenmeyin.

## Servisler

Hepsi systemd altında, `User=n4vitas`, `Restart=always`. Ortak ayar `/etc/navitas.env` dosyasında, `KIP=tunel`.

`navitas-seri-hub` · `navitas-rpi-inference` · `navitas-kamera-koprusu` · `navitas-cogullayici` ·
`navitas-iha-inis-yayinci` · `navitas-iha-komut-alici` · (`navitas-isaretli-gosterici-drm`)

- Bir servisi yeniden başlatmak için sudo gerekmez: `kill $(systemctl show -p MainPID --value navitas-rpi-inference)`.
  systemd servisi 2 s içinde yeniden açar.
- MAVProxy `--out udp:127.0.0.1:14553 --streamrate -1` ile çalışır. seri_hub `--tunel ... --tunel-kimlik hava` ile çalışır.

## Jetson'da şu an kurulu olan (son bilinen, 19 Eyl ~19:45)

| Dosya | sha (ilk 8) | Kaynak |
|---|---|---|
| `codes/rpi_inference.py` | `6fe5819b` | dal `kamera-dayanikli-20260919`, commit 67467c4f: kamera beklemesi |
| `codes/karar_sozlesmesi.py` | `3bc18e5d` | Jetson'ın kendi dosyası + kamera sabitleri eki |
| `comms/mavlink_tunel.py`, `sik_rf_olc.py` | tünel dalı | 18 Eyl kurulumu |
| `kamera_koprusu.py` | origin/master | |

- 🔴 **Jetson'daki `karar_sozlesmesi.py` origin/master ile aynı değil.** `IKA_IZ_GENISLIGI_M` Jetson'da **0.4595**; bu değer ölçüldü (D-472).
  origin/master'da hâlâ **0.39**; bu eski tahmin ve bayat.
  Bu dosya Jetson'a **asla olduğu gibi kopyalanmaz**. Yalnız yeni sabit blokları dosyanın sonuna eklenir.
  Halil tarafı origin/master'daki 0.39'u düzeltmeli.
- Yedekler: `~/navitas/codes/rpi_inference.py.yedek_20260919` ve `karar_sozlesmesi.py.yedek_20260919`. Bunlar kamera düzeltmesi öncesi hâldir.

### Kamera düzeltmesi (kurulu, canlı kabul GEÇTİ)

Kamera açılamazsa ya da 30 kare üst üste düşerse servis artık çıkmıyor. Yakalayıcıyı bırakıp 1, 2, 5 s bekleyerek yeniden açıyor.
Günlükte `[KAMERA_BEKLIYOR]` ve `[KAMERA_GERI_GELDI]` satırları görünür.
Canlı testte kamera köprüsü `kill -9` ile öldürüldü. rpi_inference aynı PID'le devam etti ve kamera 1,1 s'de geri geldi.
Eski davranış `--kamera-bekleme-yok` seçeneğiyle geri alınabilir.

## BEKLEYEN KURULUM — telemetri kapısı (c9ee27f0) 🟡

**Ne yapar.** Jetson heartbeat'e saçma telemetri koymaz. 19 Eyl'de YKİ'ye 0/0 konum (4 500 km öte) ve 890 m irtifa gitmişti. Kurallar:

- `gps_fix` alanı hiç yoksa ve konum makulse (0/0 değil) lat/lon **gider**. Bugünkü heartbeat'lerin çoğunda gps_fix yok; aksi hâlde konum hiç gitmezdi.
- `gps_fix` < 3 ise ya da bozuksa lat/lon düşer.
- 0/0 konum düşer.
- İrtifa yalnız −50 ile 200 m arasındaysa gider.
- Hız 40 m/s üstündeyse ya da NaN/inf ise düşer.
- Bastırılan alanlar günlüğe `[TELEMETRI]` satırı olarak, en fazla 30 s'de bir yazılır.

**Denetim.** Mimar 5 durum ölçtü. 6 test dosyası koştu: 27 / 17 / 19 / 20 / 11 / 19 test, hepsi OK. Genel kapı 15/15.
Bundan önceki sürüm (76f3261) reddedilmişti: fix alanı olmayan konumu da düşürüyordu ve yarınki koordinat testini bozacaktı.

**Dosyalar** `results/jetson_20260919/kurulum2/` altında:

- `rpi_inference.py` (sha `6a03cd4f`) = c9ee27f0.
- `karar_sozlesmesi_jetson_yeni2.py` (sha `45646ab9`) = Jetson'daki 3bc18e5d + yalnız TELEMETRI eki (2746 bayt). 0.4595 korunuyor.

**Kurulum (Jetson açık, ağda; drone disarm):**

```
$env:NAVITAS_SIFRE="<parola>"
O:\navitas-local-train\venv\Scripts\python.exe results\jetson_20260919\jetson_manifest.py 10.21.8.7
O:\navitas-local-train\venv\Scripts\python.exe results\jetson_20260919\kurulum2\uygula.py 10.21.8.7
```

`uygula.py` sırasıyla şunları yapar:

1. Jetson'daki sha'lar beklenen değerler değilse (6fe5819b / 3bc18e5d) **hiçbir şey yazmadan durur**.
2. Yedek alır (`.yedek_20260919b`). Var olan yedeğin üstüne yazmaz.
3. Dosyaları `.yeni` adıyla yükler. Jetson'da sha ve sözdizimi (ast) kontrol eder.
4. `mv` ile yerine koyar.
5. rpi_inference'ı yeniden başlatır.
6. 20 s sonra günlüğü okur. `kurulum_<zaman>.json` kaydı bırakır.

⚠ `uygula.py` henüz Jetson'a karşı **koşulmadı**. Jetson kapandığı için yazıldı ama denenmedi. Çıktıyı okuyun.
Kurulum sonrası kontrol: günlükte Traceback olmamalı, kamera açık olmalı, YKİ'de İHA TAZE görünmeli.

**Geri alma:**

```
cd ~/navitas/codes
mv rpi_inference.py.yedek_20260919b rpi_inference.py
mv karar_sozlesmesi.py.yedek_20260919b karar_sozlesmesi.py
kill $(systemctl show -p MainPID --value navitas-rpi-inference)
```

## Kendiliğinden kapanmalar (D-512) ⚠

- 18:10:47 ve 18:21:38'de Jetson ani kapandı. Günlükte kapanış mesajı yok.
  Çekirdek panic, OOM ve düşük gerilim olayı da yok. Sıcaklık 53 °C, fan dönüyor.
  Bu bir **güç kesintisi imzası**; yazılım çökmesi değil.
- İki kapanma da drone'un elle çevrildiği ya da yaklaşıldığı dakikalara denk geliyor. Konnektör ya da kablo teması şüphesi var.
  Bu bir zaman çakışması, kanıt değil.
- Dokunulmadığında 52 dk kesintisiz çalıştı. Kara kutuda VDD_IN hep 5064 mV, alarm 0.
- Modülün INA3221 ölçümü (5,06 V) modül rayıdır. Taşıyıcı kartın DC girişini ve regülatör çıkışını yazılım **göremez**.
- 18 Eyl'de 3S pil ve 12,2 V buck ile aynı sınıf olay yaşandı. **3S pille Jetson uçmaz.**
- **İNSAN işi:**
  - Jetson'ı besleyen pili, regülatör çıkışını ve fişi model çalışırken multimetreyle ölç.
  - Ayırıcı test: Jetson'ı 10 dk duvar adaptöründen besle. Kesinti olmazsa sorun güç yolundadır.
  - SSH'den izlerken 1 dk kablo oynatma testi yap.
- Uçuşta bir Jetson kesintisi 1–2 dk rotasız kalmak demektir. Görev bütçesi 10 dk.
  Telsizden de görülür: YKİ "kimlik SICRAMASI" yazar, karar seq'i küçük sayıya döner.

## Kara kutu

- `~/kara_kutu/kara_kutu.py` 0,5 s'de bir satır yazar ve her satırı fsync eder.
  İçerik: VDD_IN gerilimi, akım, güç, INA3221 alarmları, CPU/GPU sıcaklığı ve yükü, bellek, fan.
- Çıktı `~/kara_kutu/kutu_<zaman>_<acilis>.csv`. `crontab @reboot` ile her açılışta başlar.
- Kaynak kopyası repoda: `results/jetson_20260919/kara_kutu/`.
- Beklenmedik kapanmadan sonra bir önceki açılışın CSV'sinin **son satırlarına** bakın.

## Bilinen kök neden: gps_fix neden sık eksik (uçuş sonrası)

- `GPS_RAW_INT` mesajını yalnız `iha_inis_yayinci` istiyor: 8 Hz, 10 s'de bir tazeleniyor. Pixhawk'ta `SR2_EXT_STAT` 0.
- `telemetri_snapshot` gps_fix için 0,5 s tazelik penceresi kullanıyor (`inis_kaniti.py:868-877`). Bu yüzden heartbeat'lerin çoğunda gps_fix yok.
- Öneri: GPS alanlarına 2,5 s tazelik tanımak. `inis_kaniti` ortak modül olduğu için **uçuş sonrasına** bırakıldı. Onay gerekiyor.
