# ONARIM-09 — YKS ↔ Jetson: LAN + SiK AYNI ANDA (çok yönlü kontrol)

**Durum:** KAPANDI (yazılım, testli) · gerçek SiK telsiz çiftiyle koşu **YAPILMADI** (telsiz bağlı değil)
**Tarih:** 17 Eylül 2026 · **Liste:** madde 09 · Kullanıcı: *"ister ağdan ister koordinat telemetrisinden ister video telemetrisinden olsun, YKS programı güçlendirilsin, çok yönlü kontrol sağlasın; sadece gerçekten ihtiyacımız olanlar"*

## Sorun
- YKS **tek taşıyıcı** seçiyordu: `--serial` (SiK) **ya da** `--bind/--iha/--ika` (LAN); ikisi birlikte `ap.error`. Seçilen hat koparsa (Wi-Fi/DHCP değişimi, telsiz menzili) ekran sağırlaşıyor, komut İHA'ya ulaşmıyordu.
- Jetson tarafı da tek kip: `KIP=udp` ya da `KIP=sik`.

## Eklenen (yalnız gerekenler)
1. **`comms/link.py` `CokluLink`** — UDP + seri aynı anda; iki okuyucu iplik tek kuyruk. `recv` UDP'de adres, SiK'te `None` döner (mevcut seri kod yolları aynen çalışır). `send(peer)` yalnız UDP (ACK geldiği hatta döner), `send(None)` yalnız SiK, **`send_hepsi`** komutu iki hattan (biri bozuksa diğeri), `hat_yaslari()`.
2. **`yks_gui.py --coklu`** (`--serial` + `--iha` + `--ika` zorunlu): komutlar (`_ham_gonder`) iki hattan; ACK'ler geldiği hattan. Alt çubukta **"HATLAR: LAN x sn · SiK y sn"** (yeşil iki hat taze / sarı biri / kırmızı hiçbiri; 3 s eşik). Durum değişimi günlüğe + hakem kaydına **`HAT_DURUMU`** (CONTRACTS §6.8 tablosuna eklendi). `--coklu` verilmezse eski davranış ve hata mesajları **aynen**.
3. **`comms/seri_hub.py` LAN aynası** (`--lan-bind 0.0.0.0:5009 --lan-yks IP:5005`): Jetson süreçlerinin hub'a yazdığı her çerçeve seriye **ve** LAN'daki YKS'ye; LAN'dan **yalnız pinli YKS IP'sinden** gelen çerçeve tüketicilere fan-out (yabancı IP düşürülür, sayılır). **Seri kapalıyken LAN yolu yaşar**; `--lan-*` verilince seri port açılmazsa hub çıkmaz, LAN ile kalkar.
4. **`jetson_baslat.sh KIP=ikili`**: süreçler `sik`teki gibi yalnız hub'a (kodları değişmedi), hub `HUB_LAN_ARGS` ile LAN aynası; `YKS_IP` zorunlu; SiK yoksa UYARI (engel değil). `navitas-seri-hub.service` `$HUB_LAN_ARGS` alır (sik kipinde boş).
- **Tekrar güvenliği (yeni mekanizma gerekmedi):** komut alıcı `(oturum, seq, cmd)` ile eylemi bir kez uygular; YKS aynı seq'li heartbeat'i düşürür; OPEN_ROUTE tekrarı zaten tekrar gönderim gibi işlenir; seri çerçevesi adres kilidinden muaf (mevcut kural).
- Video: mevcut `--kamera-url` + ONARIM-06 işaretli yayın (LAN). SiK'e video girmez (değişmedi).

## Kanıt
```
tests/test_onarim09_coklu_hat.py  Ran 11  OK
  C1 CokluLink alım/yaş/yönlendirme/tek hat bozuk · C2 YKS komutu iki hattan, adres yoksa yalnız SiK
  C3 CLI eski retler aynen + --coklu kuralları · H1 hub seri+LAN, LAN→tüketici, yabancı IP düşer, seri kapalı LAN yaşar
  J1 KIP=ikili --kuru: hub --lan-bind 0.0.0.0:5009 --lan-yks, tüketiciler 127.0.0.1:5100, YKS_IP zorunlu
mutasyon M1 hub yabancı IP kontrolü kaldırıldı -> FAIL · M2 çoklu komut yalnız UDP -> ERROR · geri alınca OK
```
Geniş karşılaştırma (yks_gui/seri_hub/link/jetson_baslat/iha_komut_alici'ye dokunan 82 test dosyası, HEAD temiz worktree ↔ değişiklik):
- yeni kırmızı 2 → düzeltildi: `test_jetson_comms_paketi` (paket kopyaları `jetson_paket_hazirla.py` ile tazelendi) · `test_yks_hakem_kanit_olaylari` (`HAT_DURUMU` sabit+CONTRACTS+senaryo adımı 14) → **OK**
- farklı çıkan ama ortam kaynaklı: `test_saha_parametrik`, `test_yks_gui_uretim_hizasi` (tabanda kırmızı, yeni OK), `test_hakem_kunye_algi_hizasi` (atlama sayısı).
Sonrası: seri_hub, jetson_baslat (44), ika_go_gate, iha_komut_alici, belge_kilidi, saha_kosum_kagidi **OK**; genel kapı 15/15 · 15/15.

## Kullanım (saha)
- Jetson: `KIP=ikili YKS_IP=<PC> SIK_SERI=/dev/ttyUSB0 ...` (`saha_beyan.env`) → `sudo … jetson_baslat.sh`
- YKS: `yks_gui.py --coklu --serial <COMx|/dev/ttyUSBx> --bind 0.0.0.0:5005 --iha <jetson>:5009 --ika <ika>:5006`
- ⚠ `YKS_IP` sabit beyan hâlâ DHCP'ye kırılgan → ONARIM-03 (keşif) bunu kaldırır.
