# SAHA RUNBOOK — kanonik saha yordamı (P4 · D-394 · 2026-09-02)

> **Bu dosya saha günü yordamının TEK güncel kaynağıdır.** Eski iki belge
> (`results/t123/saha_gunu_kontrol_listesi.md` — eski model sürümleriyle bayat;
> `results/saha_zinciri_20260826/saha_gunu.md` — 26 Ağustos dünyası, "Jetson
> 30 Eylül'de" varsayımı) TARİHSEL KAYITTIR, komut kopyalanmaz.
> Sürüm/komut satırları belge kapısıyla kilitlidir: `tests/test_p4_runbook.py`
> (model adı kayıt defterinden doğrulanır — çıplak sürüm sözü burada değil,
> `config/model_registry.json`'dadır).
>
> Takvim (plan v2): aviyonik+Jetson **5 Eylül**, kesin hazır **21 Eylül**,
> tek atış **30 Eylül**.

## 0. Sahaya çıkmadan (PC'de, her seferinde)

| ✓ | ne | komut | başarı ölçütü |
|---|---|---|---|
| ☐ | Genel kapı | `<venv> -B codes/test_rota_sentetik.py` | `15/15` (madde 14) |
| ☐ | Test paketi | `<venv> -B -m unittest discover -s tests -q` | `OK` |
| ☐ | Kuru koşu | `<venv> -B scripts/saha_kuru_kosu.py --cikti results/saha_kuru_kosu_<tarih>` | Kopuk halka yalnız **`motor`** (GercekSurucu arka ucu Faz B'de dolana dek — D-390). Yeni kopuk çıkarsa **regresyon**: sahaya çıkma |
| ☐ | Paket aynası | `<venv> scripts/jetson_paket_hazirla.py` | "hepsi senkron" |
| ☐ | Model pakette | `ls jetson_paket/models/` | Üretim modeli `navitas_seg_v36_best.pt` **ve** `navitas_seg_v36_best_512_fp16.onnx` |
| ☐ | H3 video (manuel, model yükler) | `<venv> drone/test_uctan_uca.py --hizli` | exit 0 — **genel kapıda DEĞİL** (bilerek: GPU işi, D-392) |

## 1. Açılış kartı (hazırlık ≤ 900 s — §6.2, her 30 s +1 puan)

İstasyon başına **TEK komut** (`scripts/saha_baslat.py` süreyi ölçüp yazar):

```bash
<venv> scripts/saha_baslat.py yks --fda --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080   # 21 Eylül YKS
<venv> scripts/saha_baslat.py ika --yks <YKS_IP>:5005     # İKA istasyonu
<venv> scripts/saha_baslat.py --komutlar                  # kartı yazdır
```

SiK (433 MHz) ile: `saha_baslat.py yks --fda --serial COM5 --baud 57600
--kamera-url http://<JETSON_IP>:8080`. Yarışma gününde yalnız `--fda` çıkarılır.
⚠ `--yks` İKA'da UDP'de fiilen **zorunludur** (CONTRACTS §6.6/K8: OPEN_ROUTE
IKA_GO'dan önce gelir; adres verilmezse hakem aktarım kanıtı hiç gitmez).

Kamera görüntüsü **SiK üzerinden taşınmaz**. `--kamera-url` Jetson ile YKS
arasındaki ayrı Wi-Fi/LAN köprüsüdür. Kamera ağı yoksa telemetri ve emniyet
komutları çalışmayı sürdürür; ekran eski kareyi canlıymış gibi tutmaz.

YKS her açılışta `results/prova/<tarih_saat_pid>/hakem_log.jsonl` altında
kalıcı, `flush+fsync` edilen bir kanıt oturumu açar. Başka yol istenirse
doğrudan GUI'ye `--hakem-log <yol>` verilir. Dosya açılamazsa YKS kanıtsız
başlamaz; koşarken yazma bozulursa kalkış/hakem onayı kapanır, ARM ve acil
komutlar erişilebilir kalır.

## 2. YKS operatör kartı

- Üst satırdaki **HAM GNSS** enlem/boylam, fix, uydu ve bağıl irtifayı canlı
  Pixhawk telemetrisinden gösterir. Bayat alan silinir. Ham koordinat, kalibre
  edilmiş arena dönüşümü olmadığı için semantik harita konumu **değildir**.
- **KAMERA** görünümü = Jetson RAW hakem görüntüsü. `CANLI` ve kare yaşı
  görünmeden görüntüyü güncel kabul etme; `KARE_BAYAT`, `KAYNAK_KAPALI` veya
  `BAĞLANAMADI` halinde fiziksel kamera/ağ giderilir.
- **A** = ARM/DISARM. Düğme yalnız taze Pixhawk `armed` heartbeat'i varken
  açılır. Komutun gönderilmiş olması durum kanıtı değildir: ekran ancak
  Pixhawk'ın kabul ACK'i **ve** yeni heartbeat aynı durumu gösterince ARM veya
  DISARM yazar. Uçuşta DISARM ayrıca iki adımlı teyit ister (T180).
- **FIRLATMA** yalnız ARM'dayken damga atar (yazılım kilidi, D-393).
- **PARAŞÜT (manuel −50)**: iki adımlı teyit; komut ACK gelene dek tekrarlar,
  ACK yoksa ekran KIRMIZI uyarır (D-393). Yalnız son çare — §6.4 sınırı.
- 🔴 **21 Eylül Adıyaman prova uçuşu `--fda` ile açılır** (CONTRACTS §6.7): çoklu
  rotorda paraşüt ve İKA **yoktur**. FDA kipinde ekran şunları değiştirir:
  bütçe tek **10 dk**, `FIRLATMA` düğmesi **KALKIŞ**, `PARAŞÜT` ve `İKA BAŞLAT`
  **kapalı** (basılsa bile komut gitmez), hakem 2/2 onayı **İKA kanıtı aramaz**
  — dayanak YKS'ye canlı aktarımdır. Yarışma günü kipi varsayılandır ve
  `--fda` verilmedikçe davranış değişmez.
- **R** = onay sıfırlama (tekrar fırlatma yordamının 1. adımı).
- İKA BAŞLAT: yalnız IHA_LANDED + hakem onayı sonrası açılır (§2.2.5 kilidi).

## 3. İHA / Jetson (5 Eylül'den itibaren)

> ⚠ **6 Eylül ölçümü (D-431):** kart **Jetson Orin Nano Developer Kit 4 GB / JetPack 7.2.1 /
> Ubuntu 24.04 / Python 3.12** — "Nano 4GB / JetPack 4.6" varsayımı geçersiz. Kurulum tutanağı
> `jetson_paket/JETSON_ORIN_NANO_KURULUM.md` (`JETSON_NANO_KURULUM.md` GEÇERSİZ bandıyla arşiv).
> Jetson'da aşağıdaki `python3` = `~/venv312/bin/python` (`source ~/venv312/bin/activate`);
> birimlerde `PYTHON3=/home/n4vitas/venv312/bin/python`, kullanıcı `n4vitas`, köprü `/usr/bin/python3`,
> paket kökü `~/navitas` (symlink). **Uçuş modeli `.pt`** (engine↔pt D-303 oransal denkliği 3/126
> DÜŞTÜ; engine yalnız açık `--model` ile). CSI kamera ve Pixhawk kapıları 6 Eylül'de **ÖLÇÜLEMEDİ**
> (donanım bağlı değildi); `jetson_baslat.sh --kuru` çıktısında `[YOK]` yalnız `/dev/ttyACM0`.

Cihaz kurulum ve `.engine` derleme: `jetson_paket/JETSON_KILAVUZ.md` +
`jetson_paket/GUN1_KONTROL_LISTESI.md` (Gün-1 kapıları: T16/T17 FPS ve
karar denkliği). İniş kanıtı yayıncısı (Jetson'da, uçuş öncesi hazır):

🔴 **Önce çoğullayıcı (CONTRACTS §7.4):** seri Pixhawk tek sahiplidir; üç
süreç aynı anda `/dev/ttyACM0` açamaz. Jetson'da mavlink-router (ya da
MAVProxy `--master /dev/ttyACM0 --out udp:127.0.0.1:14550 --out
udp:127.0.0.1:14551 --out udp:127.0.0.1:14552`) portu tek başına açar;
tüketiciler UDP uçlarından bağlanır. Doğrulama: `scripts/mavlink_dogrula.py
--mavlink udp:127.0.0.1:1455N --sysid 1` üç uçta da GEÇTİ.

```bash
python3 jetson_paket/kod/iha_inis_yayinci.py \
    --mavlink udp:127.0.0.1:14551 --sysid 1 --kanit-timeout 900 \
    --ika <IKA_IP>:5006 --yks <YKS_IP>:5005
python3 jetson_paket/kod/iha_komut_alici.py \
    --mavlink udp:127.0.0.1:14552 --sysid 1 --bind 0.0.0.0:5007 \
    --izinli-kaynak <YKS_IP>:5005
```

🔴 **`--izinli-kaynak` ZORUNLUDUR** (4 Eylül). Verilmezse süreç **hiç
kalkmaz** (argparse çıkış 2) ve blok **asimetrik** ölür: birinci satır
(`iha_inis_yayinci`) sorunsuz başlar, ikinci satır ölür. Sahada zincir
*yarı canlı* görünür — iniş kanıtı akar ama YKS'nin **ARM/DISARM/RTL/LAND/
PARAŞÜT** düğmeleri hiçbir zaman ACK almaz.

Değer, YKS'nin komutu gönderdiği sokettir: `<YKS_IP>:5005`. Kritik eyleyici
yalnız o kaynaktan komut kabul eder; başka bir adresten geleni **loglar ve
reddeder** (`CMD kaynagi RED: gelen=…, izinli=…`). `jetson_baslat.sh` bu
bayrağı kendisi verir — elle başlatan yazmalıdır.

🔴 **PİNİ AÇILIŞTA DOĞRULA — yanlışlığı YKS'de GÖRÜNMEZ.** `YKS_IP`
`navitas.env`'de **elle beyan edilir**. Dizüstünün o arayüzdeki gerçek adresi
farklıysa (DHCP değişimi, ikinci arayüz, VPN) alıcı **tüm** ARM/DISARM/RTL/
LAND/PARAŞÜT komutlarını reddeder — ve bunu **yalnız Jetson tarafında** loglar.
YKS ekranında hiçbir uyarı çıkmaz; operatör "ARM çalışmıyor" der, nedenini
bulamaz.

**Kapı — yer zinciri başlamadan önce, iki komut:**
```bash
# 1) YKS dizüstünde, Jetson ile aynı ağdaki arayüzün GERÇEK adresi:
ipconfig            # Windows  (ya da: ip -4 addr show  — Linux)
# 2) Jetson'da, pinin ne olduğu:
grep YKS_IP /etc/navitas.env
```
İkisi **eşit olmalı**. Değilse `navitas.env`'i düzelt ve
`sudo systemctl restart navitas-komut` koş.

🔴 **ÖNLEYİCİ ADIM — ethernet + yönlendirici kullanıyorsan bunu SAHA GÜNÜNDEN ÖNCE yap.** DHCP, YKS dizüstüne her açılışta farklı adres verebilir; o zaman pin sessizce yanlışlanır ve yukarıdaki kapı her seferinde düşer. İki yoldan biri:

1. **Yönlendiricide DHCP rezervasyonu** — dizüstünün MAC adresine sabit IP bağla.
2. **Adaptöre statik adres** — Windows: Ağ Bağlantıları → Ethernet → IPv4 →
   *Şu IP adresini kullan*. Jetson ile aynı alt ağda olsun.

⚠ Beyan değiştiğinde `--kur` **yeniden koşulur**; `restart` yeni argümanları canlı
sürece uygular (`enable --now` uygulamazdı, D-405).

**Saha teşhisi — "ARM'a basıyorum, hiçbir şey olmuyor":**
```bash
journalctl -u navitas-komut -n 30 --no-pager | grep -i "kaynagi RED"
```
Bu satır çıkıyorsa sorun pindir, araç değil. `gelen=` alanı YKS'nin
**gerçek** adresini gösterir; `navitas.env`'e onu yaz.

RAW kamera köprüsünü aynı kapalı saha LAN'ında açmak için Jetson başlangıç
ortamında `KAMERA=http://127.0.0.1:8080/video` ve
`KAMERA_KOPRU_BIND=0.0.0.0` açıkça beyan edilir. Varsayılan bind yalnız
loopback'tir; LAN'a kendiliğinden açılmaz. Güvenlik duvarında TCP/8080 yalnız
YKS IP'sinden kabul edilir. YKS `http://<JETSON_IP>:8080` kökünü kullanır;
istemci `/kare.jpg` ve `/durum` uçlarını kendi çözer.

- `iha_komut_alici` = YKS'nin PARAŞÜT/ARM/DISARM komutlarını Pixhawk'a aktarır
  ve **yalnız aktarım başarılıysa** ACK döner (D-393 dürüstlük sözleşmesi);
  YKS bu sürecin `--bind` adresini `--iha` olarak bilmeli.
- **SiK (433 MHz) kipi — CONTRACTS §7.5:** seri SiK portu da tek sahiplidir;
  üç süreç `--serial /dev/ttyUSB0` ile AÇILMAZ. `seri_hub` portu tek başına
  açar, süreçler UDP loopback üzerinden konuşur (kodları değişmez):
  ```bash
  # ONCE: systemctl stop navitas-seri-hub   (birim kuruluysa — iki hub ayni porta yazmasin)
  python3 jetson_paket/kod/seri_hub.py --port /dev/ttyUSB0 --bind 127.0.0.1:5100 \
      --tuketici 127.0.0.1:5007
  # rpi_inference    --yks-hedef 127.0.0.1:5100        (tek hatta bir kez: --ika-hedef hub'a VERILMEZ)
  # iha_inis_yayinci --yks 127.0.0.1:5100
  # iha_komut_alici  --bind 127.0.0.1:5007
  ```
  İKA'nın hattı (SiK çok-noktalı mı, WiFi `--ika-hedef <IKA_IP>:5006` mi)
  cumartesi topolojiyle karara bağlanır (CONTRACTS §7.5, D-405).
  Tek komut: `jetson_baslat.sh` (KIP=udp|sik) — `jetson_paket/JETSON_BASLAT.md`.

- `--sysid 1` = ArduPilot varsayılan sistem kimliği (D-389: pin beyana dayanır;
  araç farklı sysid'e ayarlandıysa buradaki değeri ona eşitle).
- `--kanit-timeout 900` = İHA görev süresi (§6.2); yayıncı iniş kanıtını bu
  pencere boyunca bekler ve tek geçici hata görevde vazgeçmez (D-389 A1+A2).
- 🔴 SiK üzerinden **`--serial` KULLANILMAZ** (4 Eylül düzeltmesi; bu satır önceki
  sürümde yukarıdaki SiK maddesiyle çelişiyordu). Seri portu `seri_hub` **tek
  başına** açar; süreçler UDP loopback'ten konuşur. `iha_komut_alici` artık
  `--serial`i **sert reddeder** (çıkış 2). Doğrusu yukarıdaki SiK bloğudur.

## 4. Tekrar fırlatma / reset (§6.2 — süre 15 dk'dan yer)

```bash
<venv> scripts/saha_baslat.py --reset     # yordamı yazdırır
```

Özet: YKS'de R + gerekirse yeniden ARM; İKA süreci ÖLDÜRÜLMEZ (güvenli
duruşta beklemeye devam eder); Jetson yeniden başlatılmaz; kronometre yeni
fırlatmada yeniden damgalanır. Hiçbir adımda araca fiziksel müdahale yok
(hands-off ihlali −100).

## 5. Prova ve kanıt

Her saha provası `simulation/PROVA_SENARYOSU.md` faz damgalarına göre koşulur;
video + hakem_log çıktısı `results/prova/<tarih>/` altına taşınır (UHDR §5.5
kanıtı). Sim koşusu saha kanıtı değildir (CONTRACTS 11.1) — gerçek prova
kayıtları esastır.

## 6. 21 Eylül kesin-hazır kapısı (gerçek donanım, masada + açık alanda)

Bu maddeler simülasyonla kapatılamaz; her biri tarihli ekran videosu ve
`hakem_log.jsonl`/servis günlüğüyle kanıtlanır. Bir madde düşerse uçuşa çıkılmaz.

| ✓ | fiziksel kapı | geçiş ölçütü |
|---|---|---|
| ☐ | Pixhawk bağlantısı | Üç MAVLink tüketicisi çoğullayıcı üzerinden aynı `sysid` aracını görür; seri portu yalnız router açar |
| ☐ | GNSS canlılığı | Açık alanda gerçek lat/lon, fix ve uydu görünür; anten kapatılınca/besleme kesilince alanlar tazelik süresi sonunda kaybolur |
| ☐ | Ölçek/irtifa | `relative_alt` uçuş boyunca kare kare değişir; telemetri kesilince `OLCEK_YOK` olur, son değer kullanılmaz |
| ☐ | ARM | YKS ARM komutu Pixhawk'ta gerçekten ARM eder; ACK tek başına ekran durumunu değiştirmez, ardından gelen armed heartbeat değiştirir |
| ☐ | DISARM | Yerde gerçekten DISARM olur; havada tek basış komut göndermez, ikinci teyit penceresi ölçülür |
| ☐ | Kamera canlılığı | RAW görüntü, kare sıra/yaşıyla en az 10 dk akar; lens önünde hareket ekrana gelir, donmuş kare canlı sayılmaz |
| ☐ | Kamera kopma/yakalama | Wi-Fi kapatılınca görünüm fail-closed uyarır; telemetri/ACK sürer; ağ dönünce süreç yeniden başlatılmadan görüntü gelir |
| ☐ | Ağ ayrımı | Video trafiği yalnız saha Wi-Fi/LAN TCP/8080'dedir; SiK hattında görüntü paketi yoktur |
| ☐ | E-stop/paraşüt | Yetkili, emniyetli masa düzeninde güçlü ACK ve red/timeout yolları ayrı ayrı gözlenir; kabul edilmeyen komut başarı yazmaz |
| ☐ | Kayıt | YKS ekranı, araç, GNSS, kamera kopma deneyi ve saat eşleşmesi tek prova klasöründe geri oynatılabilir |
