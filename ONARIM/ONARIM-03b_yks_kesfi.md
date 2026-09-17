# ONARIM-03b — YKS keşfi: Jetson YKS'yi "Bluetooth mantığıyla" bulur (DHCP'ye dayanıklı)

**Durum:** KAPANDI (yazılım + **Jetson ↔ PC canlı**) · kullanıcının 3. maddesi (listede ONARIM-03 görev kaydıyla karışmasın diye `03b`)
**Tarih:** 17 Eylül 2026 · Kullanıcı: *"tarasın, bluetooth mantığı gibi doğrusu seçilsin"*

## Sorun (ölçüldü)
PC'nin IP'si bir günde iki kez değişti (10.21.8.112 → 10.21.8.156). Jetson'da `YKS_IP` sabit beyandı: telemetri eski adrese gidiyor, komut alıcı yeni adresten gelen komutu **reddediyordu** (`--izinli-kaynak YKS_IP:5005`).

## Çözüm
- **`comms/yks_kesif.py`** (yalnız standart kütüphane):
  - Eşleşme = kimlik + 32 bayt anahtar (dosya 0600) + 6 haneli **eşleşme kodu** (iki ekranda karşılaştırılır; anahtar pakette taşınmaz).
  - YKS `YKS_DUYURU` yayar (1 Hz, UDP 5010): kimlik, port, zaman, nonce, **HMAC-SHA256**.
  - `YksSecici`: yalnız eşleşen kimlik + doğru imza + tazelik (YKS saatine göre öğrenilen farktan ≤ 10 s; Jetson RTC'sine dayanmaz) + tekrar olmayan nonce **kabul**; YKS adresi = duyurunun **kaynak IP'si** + port. Başka kimlikler taramada görünür, seçilmez.
- **`scripts/yks_eslestir.py`**: `yeni` (YKS'de kimlik/anahtar/kod üret) · `tara` (ağdaki YKS'leri listele, eşleşeni "SECILEN" işaretle) · `esle` (kimlik+anahtar kaydet, kodu göster).
- **`yks_gui.py --eslesme DOSYA`**: dosya yoksa üretir; duyuruyu başlatır; hedefler **broadcast + `--iha` host'u doğrudan** (broadcast engelli ağlar için); günlüğe kimlik + EŞLEŞME KODU; kapanışta durur.
- **`seri_hub.py --lan-yks-eslesme DOSYA`** (`--lan-yks` yerine): 5010'da duyuruları dinler, adres değişince `lan_yks` güncellenir + günlük; eşleşme öncesi LAN'a gönderim yok (`lan_yks_yok` sayacı), LAN'dan gelen çerçeve kabul edilmez.
- **`jetson_baslat.sh`**: `KIP=ikili` + `YKS_ESLESME=/etc/navitas/yks_eslesme.json` → `YKS_IP` gerekmez; `--kuru` dosyayı `[VAR]/[YOK]` denetler.
- Yan düzeltme: SiK takılı değilken hub saniyede bir KIRMIZI "seri yeniden açma BAŞARISIZ" yazıyordu → ilk 3 + her 60. deneme (sayaç tam).
- Paket: `yks_kesif.py`, `yks_eslestir.py` KOPYALAR'a (24 → 26); kılavuz `cp` satırları.

## Testler
```
tests/test_onarim03_yks_kesif.py  Ran 10  OK
  K1 kabul + IP değişimi izlenir · K2 başka kimlik seçilmez / yanlış anahtar / port oynatma = İMZA_RED
  K3 tekrar oynatma TEKRAR_RED · 60 s eski duyuru BAYAT_RED, adresi ele geçiremez · K4 seçim tazeliği
  K5 dosya 0600, kod eşit, bozuk dosya ret · K6 gerçek soket yayıncı→dinleyici + `tara` CLI
  K7 hub: eşleşme öncesi LAN yok, sahte anahtarlı duyuru adres vermez, gerçek duyuru → heartbeat YKS'ye
  K7b hub CLI --lan-yks ile --lan-yks-eslesme birlikte verilemez · K8 jetson_baslat YKS_ESLESME · K9 YKS duyurusu (dosya üretimi, hedefler, bozuk dosya)
mutasyon: HMAC denetimi kapatıldı -> FAIL 2; geri alınca OK
test_onarim09_coklu_hat OK · test_faz_b_seri_hub OK · test_jetson_comms_paketi OK · test_kilavuz_kurulum_yordami OK · test_faz_b_jetson_baslat OK
```

## Canlı (17 Eyl 16:04–16:12, PC 10.21.8.156 Wi-Fi ↔ Jetson 10.21.8.7 Ethernet)
1. PC: `yks_eslestir.py yeni --dosya ~/.config/navitas/yks_eslesme.json --ad YKS-PC` → kimlik `YKS-PC-ff300926`, **kod 426812**. Dosya Jetson'a `/etc/navitas/yks_eslesme.json` (n4vitas, 0600) kopyalandı.
2. Jetson `saha_beyan.env`: `KIP=ikili`, `YKS_IP=` (boş), `YKS_ESLESME=/etc/navitas/yks_eslesme.json`, `SIK_SERI=/dev/ttyUSB0` (takılı değil) → `sudo jetson_baslat.sh`: 6 birim active, NRestarts 0.
3. PC duyuru + 5005 dinleme (25 s): hub günlüğü **`YKS KESFI: eslesen YKS YKS-PC-ff300926 adresi None -> 10.21.8.156:5005`**; PC'ye **ilk Jetson çerçevesi 0,2 s**'de, toplam **NO_ROUTE 83 + HEARTBEAT 25**, kaynak `10.21.8.7:5009` (hub LAN ucu). Broadcast + doğrudan hedef ikisi de gönderildi (52 duyuru, 0 hata).
4. Ters yön: PC → `10.21.8.7:5009` `CMD RTL` (Pixhawk Jetson'a bağlı değil — eyleyici yok) → komut alıcı günlüğü komutu aldı, saat ofsetini öğrendi, **"Pixhawk'tan henüz paket gelmedi; aktarım yapılmadı, ACK YOK"** (fail-closed doğru).

## Saha kullanımı
- YKS: `yks_gui.py --eslesme ~/.config/navitas/yks_eslesme.json --bind 0.0.0.0:5005 --iha 10.21.8.7:5009 --ika <ika>:5006 [--coklu --serial COMx]`
- Jetson: yeni YKS PC'si → PC'de `yks_eslestir.py yeni`, Jetson'da `yks_eslestir.py esle --kimlik … --anahtar … --dosya /etc/navitas/yks_eslesme.json` (kodlar aynı olmalı), `sudo systemctl restart navitas-seri-hub`.
- ⚠ Kalan: İKA tarafı hâlâ sabit `--ika HOST:PORT` (İKA kendi ağında; gerekirse aynı keşif İKA'ya da uygulanır). Ağ UDP 5010 broadcast'i engellerse `--iha` doğrudan hedefi yine çalışır (Jetson IP'si Ethernet'te sabit 10.21.8.7).

## Geniş karşılaştırma (ONARIM-09 sonrası ↔ bu iş, 82 test dosyası)
- Düzelen: `test_jetson_comms_paketi`, `test_yks_hakem_kanit_olaylari`.
- `test_faz_b_iha_komut_alici` bir koşuda FAIL (test_13 sahte Pixhawk COMMAND_ACK) — canlı UDP denemesiyle eşzamanlıydı; tek başına **3/3 OK** (zamanlama dalgalanması, kod değişmedi).
- `test_yks_mk15_hakem_ekrani` +1: CONTRACTS §6.8 **tam metni ön kayıtlı** (D-465); `HAT_DURUMU` satırı ön kayda da eklendi → yalnız önceden kırmızı `H2c` (etiket çakışması) kaldı.
