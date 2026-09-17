# ONARIM-10 — Jetson paket ağacı depoyla eşitlendi; servis yorumlayıcısı modül denetimi

**Durum:** KISMEN — paket senkronu ve yorumlayıcı kusuru KAPANDI · systemd birimlerinin Jetson'a **kurulması** ve sahada koşması BEKLİYOR (sudo + güvenlik kararı, ONARIM-07)
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 10

## 1. Paket senkronu (ölçüm)
Depodaki `codes/ comms/ scripts/ jetson_paket/ config/` altındaki 458 izlenen dosya (py/sh/json/service/yaml/txt/md/param) md5 ile Jetson `~/navitas` ile karşılaştırıldı:
- **442 aynı**, **7 farklı**, **9 Jetson'da yok**. `codes/` ve `comms/` farkı yok (ONARIM-03/04/08 dağıtımları).
- Farklı: `config/model_registry.json` (depoda yalnız ek `competition_v32` profili; üretim işaretçisi aynı), `jetson_paket/jetson_baslat.sh` (ONARIM-02/03), `jetson_paket/kod/inis_kaniti.py` (ONARIM-08), `jetson_paket/models/jetson_derleme_manifest.json` (yalnız belge metni), `scripts/fdr_pdf_uret.py`, `scripts/hover_kapisi.py` (ONARIM-01), `scripts/olcum/65_kabul_denetcisi.py` (ONARIM-11 dalı).
- Yok: `scripts/kamera_odak_olcer.py`, `scripts/tezgah/{kalibrasyon_satranc.py,tezgah_mavlink_koprusu.sh}`, `scripts/{fda_gorev_uret,fdr_mancinik_enerji_svg,fdr_yazilim_resmi,mesaj_boyutu_ve_veri_hizi,sunum_uret,t236_sitl_fda_provasi}.py`.
- 16 dosya dağıtıldı; üzerine yazılan 7'sinin eski hâli `~/navitas/.onarim_yedek_20260917/` altında.
- Doğrulama (Jetson): `load_model(None, kayit_zorunlu=True)` → **`navitas_seg_v36_best.pt · eslesti`**.

## 2. Kusur: `--kuru` yorumlayıcıyı yalnız `-x` ile sınıyordu
- Jetson'da varsayılan `PYTHON3=/usr/bin/python3` çalıştırılabilir ama `import ultralytics` → **ModuleNotFoundError**; `ultralytics/torch 2.11.0+cu130/pymavlink` yalnız `~/venv312`'de. `--kuru` yine de `[VAR] yorumlayici` ve **KURU SONUC: tamam** diyordu → `--kur` ile kurulan `navitas-rpi-inference` servisi ilk satırda çöküp `Restart=always` döngüsüne girerdi (hands-off ihlali).
- Düzeltme (`jetson_paket/jetson_baslat.sh`): `yorumlayici_modulleri_var()` — `$PYTHON3 -c "import ultralytics; import cv2; import numpy; import pymavlink"` (`PYTHON3_MODULLERI` ile ezilebilir). `--kuru`: `[VAR|YOK] modul <yorumlayıcı> import …` satırı, YOK → çıkış 3. `--kur/--kapi` (`dosya_denetle`): import edemiyorsa **HATA**, hiçbir şey kurulmaz.
- Jetson'da gerçek koşu:
  - `PYTHON3=/usr/bin/python3` → `[YOK] modul … ` · **KURU SONUC: eksik, çıkış 3**
  - `PYTHON3=/home/n4vitas/venv312/bin/python` → `[VAR] modul …` · **KURU SONUC: tamam, çıkış 0**; `navitas-rpi-inference` ExecStart `--gorev-kaydi …/results/jetson_log/gorev` içeriyor.
- **Saha komutu (bundan sonra):** `PYTHON3=/home/n4vitas/venv312/bin/python KIP=udp YKS_IP=<PC> IKA_IP=<İKA> FOV=<ölçülen> PIXHAWK_SERI=/dev/ttyTHS1 PIXHAWK_BAUD=57600 bash jetson_paket/jetson_baslat.sh --kuru`

## Testler
- `tests/test_faz_b_jetson_baslat.py` **44 OK** (K9 makine satırı ayrıştırıcısına `modul` türü: betikle aynı import sınaması bağımsız koşulur; K1 "kuru hiçbir shim'i çalıştırmaz" kuralına salt okunur `python3 -c import` istisnası).
- Mutasyon: `yorumlayici_modulleri_var` → her zaman `return 0` → **K9 FAIL**; geri alınca OK.

## 3. Odak testi kayıtları (ONARIM-04/05 tezgâh)
`results/onarim/onarim05_odak_testi/` — Jetson `odak_onizleme` üç koşusu (12:07, 12:08, 12:17; 906 JSONL satırı, 66 kare). Kullanıcı lensi vida ile sabitledi: tam kare keskinlik **~350–430 NET** (ayar öncesi 1,5); son koşu en iyi **551,8**, orta kare en iyi 61,7. Önizleme 12:23'te `q` ile temiz kapandı. 20–30 m FOV/görüş ölçümü **henüz yapılmadı** (kayıtta `mesafe_beyan_m` yalnız 2 m denemesi).

## 4. Tam kurulum (17 Eylül 15:03–15:07, kullanıcı onayı: /opt sistem ortamı + servis sadeleştirme + otomatik başlatma A)
**a) Python ortamı venv'den bağımsız:** çalışan `~/venv312` (torch 2.11.0+cu130, ultralytics 8.4.142, cv2 4.11, pymavlink, serial) **`/opt/navitas/python`** altına kopyalandı, `root:root`, başkalarına yazma yok. `pip install torch` YAPILMADI. `bin/` altındaki 56 betiğin shebang'i `/home/n4vitas/venv312` → `/opt/navitas/python` (kalan 0). Doğrulama: `torch.cuda.is_available() True`, `mavproxy.py --help` OK. `~/venv312` silinmedi.
**b) Servis sadeleştirme:** `jetson_paket/saha_servis_sadelestir.sh` (`--kuru`, uygula, `--geri-al <dosya>`): 21 servis + 8 zamanlayıcı `disable --now`, kullanıcı `tracker-miner-fs-3` `mask`. Kapatılanlar: docker/containerd, ModemManager, bluetooth, avahi, kerneloops, apport, fwupd, gnome-remote-desktop, openvpn, sssd, ubiquity, cloud-init ×4, isc-dhcp-server ×2, dnsmasq; **apt-daily / apt-daily-upgrade** (otomatik güncelleme — "apt upgrade yasak" kuralıyla çelişiyordu), update-notifier ×2, motd-news, ua-timer, apport-autoreport, fwupd-refresh. Önceki durum: `/var/lib/navitas/servis_onceki_durum_20260917_150342.txt` (kopyası `results/onarim/`).
  ⚠ Düzeltme: DHCP sunucusu için "ağa IP dağıtabilir" demiştim — **yanlış**: `INTERFACESv4/6=""`, servisler zaten FAILED; USB device-mode `dhcpd`'yi kendi betiğinden doğrudan çalıştırır. Kapatmak zararsız, risk yoktu.
  Dokunulmayanlar: gdm, ssh, NetworkManager/networkd, nvargus + nv*/nvidia*, fake-hwclock, snapd, cron, journald, timesyncd, `ag-portal-giris.timer`.
**c) Kurulum:** `jetson_paket/saha_beyan.env` (PYTHON3=/opt/navitas/python/bin/python, MAVPROXY_BIN=/opt/navitas/python/bin, KIP=udp, **YKS_IP=10.21.8.156 GEÇİCİ** — PC DHCP adresi bugün iki kez değişti, ONARIM-03/09 keşif gelene dek; IKA_IP=127.0.0.1 yer tutucu; FOV=63 BEYAN; PIXHAWK_SERI=/dev/ttyTHS1; KAMERA köprü 0.0.0.0:8080). `jetson_baslat.sh`: `MAVPROXY_BIN` artık ortamdan ezilebilir. `sudo … jetson_baslat.sh` → `/etc/navitas.env` + 6 birim, 5'i **enabled + active** (açılışta otomatik başlar).
**d) 75 s sonra:** 5 birim `active`, `NRestarts=0`. rpi_inference: model v36 · kayıt eşleşti · görev kaydı açık · 82 kare, çıkarım ~214 ms, **keskinlik 475,5 (NET)**, iç mekân sahnesinde MASKE_YOK (engel ~%62; ONARIM-04'ün dış sahne ölçümü bekliyor). Köprü nvargus 1280×720 10 fps, 0 düşen. Çoğullayıcı: `Waiting for heartbeat from /dev/ttyTHS1` (Pixhawk Jetson'a bağlı değil — beklenen). Komut alıcı 0.0.0.0:5007 dinliyor, izinli kaynak 10.21.8.156:5005.
⚠ **Bellek:** kullanılabilir ~480 MB (3,4 GB'ın 2,97 GB'ı dolu; masaüstü + model + köprü); swap 6,9 GB boş. İzlenmeli; gerekirse masaüstü (gdm) sahada kapatılabilir — karar kullanıcının.
