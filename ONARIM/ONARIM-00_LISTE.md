# ONARIM-00 — 17 Eylül düşüşü sonrası yazılım eksikleri: ana liste

**Kod adı:** `ONARIM` · her madde ayrı dosya `ONARIM-NN_<konu>.md` (NN = aşağıdaki madde no).
**Başlangıç:** 17 Eylül 2026 · **Bağlam:** REVIEW_LOG D-493 (düşüş + Jetson kayıt incelemesi).
**Çalışma sırası (kullanıcı onayı):** 2 → 3 → 4 → 1 → kalanlar.

Durum etiketleri: `AÇIK` · `SÜRÜYOR` · `KAPANDI (kanıt: …)` · `BEKLİYOR (insan/karar)`.

| No | Sorun | Grup | Durum | Dosya |
|---|---|---|---|---|
| 01 | Hover kapısı tüm dosyanın tepesine bakıyor; **uçuşsuz log TAMAM alıyordu (fail-open)**; "motor çıkış farkı" tanımı ekiple eşleşmedi | A uçuş güvenliği | KISMEN (fail-open + hover dilimi KAPANDI, gerçek .bin; tanım BEKLİYOR — normal hover max−min 75–95 µs) | `ONARIM-01_hover_kapisi.md` |
| 02 | `jetson_baslat.sh --kapi` parametre indirmesi (~42 s @57600) bitmeden ölçüyor → yanlış DÜŞTÜ | A | KAPANDI (test 44 OK + mutasyon; canlı koşu yok) | `ONARIM-02_mavlink_kapi_param_bekleme.md` |
| 03 | Jetson'da kare başına kalıcı model/karar kaydı yok (stdout yalnız açılış); journald ayarı tekrarlanabilir değil | A | KAPANDI (6+44 test, mutasyon, Jetson'da gerçek kamera koşusu) | `ONARIM-03_jetson_gorev_kaydi.md` |
| 04 | Canlı kamerada her karar `MASKE_YOK` — ölçüldü: canlı hat suçsuz (A≡B); IMX477 keskinliği 1,5–2,3 = σ≈10 bulanıklık → model hep ENGEL | B algı | SÜRÜYOR (odak ayarı sonrası yeniden ölçüm) | `ONARIM-04_canli_maske_yok.md` |
| 05 | IMX477+6 mm odak ve FOV ölçülmedi (`--fov 63` BEYAN); sürücü yalnız 16:9 | B | KISMEN (odak ayarlandı: keskinlik 1,5 → ~350–550 NET; FOV ölçüm aracı hazır, 20–30 m ölçümü BEKLİYOR) | `ONARIM-10_jetson_paket_senkronu.md` §3 |
| 06 | İşaretli video yolu yarım: T227 `--isaretli-yayin` yoktu | B | KAPANDI (9 test + mutasyon; Jetson'da dosya kaynağıyla koşuldu, FPS etkisi −%1,3; canlı kamera/gösterici koşusu yok) | `ONARIM-06_isaretli_yayin.md` |
| 07 | Otomatik başlatma yok | C | KAPANDI (kullanıcı kararı A: systemd enabled; beyanlar /etc/navitas.env + jetson_paket/saha_beyan.env) | `ONARIM-10_jetson_paket_senkronu.md` §4 |
| 08 | Log saatleri Pixhawk'la hizalanmıyor (RTC pilsiz; fake-hwclock yalnız telafi); log adında boot id yok | C | KAPANDI (yazılım: pixhawk_ms eşlemesi + boot_id; RTC pili donanım) | `ONARIM-08_log_zaman_hizalama.md` |
| 09 | YKS→İHA komut hattı tek taşıyıcı; PC IP DHCP ile değişiyor | C | KAPANDI (çoklu hat: YKS --coklu LAN+SiK, hub LAN aynası, KIP=ikili; 11 test + mutasyon; gerçek SiK koşusu yok) — IP keşfi ONARIM-03 | `ONARIM-09_yks_coklu_hat.md` |
| 10 | Jetson servisleri hiç kurulmamıştı; venv bağımlılığı; gereksiz servisler | C | KAPANDI (/opt/navitas/python, 29 birim kapatıldı + geri alma kaydı, 5 servis enabled+active NRestarts=0; YKS_IP geçici — madde 3) | `ONARIM-10_jetson_paket_senkronu.md` §4 |
| 11 | Jetson dalı `jetson/tek-yol-20260912` master'a girmemiş; D-480…484 numara çakışması; Emir'in PC'sinde D-490/491/492 düşüş analizleri | D depo | KAPANDI (birleştirildi, D-477…484→D-495…502, T261→T265; yeni kırmızı yok) — Emir'in D-49x'leri gelince D-503+ | `ONARIM-11_jetson_dal_birlestirme.md` |
| 12 | Commitlenmemiş `world_generator.py`/`navitas_anim.cc` mujoco testini düşürüyordu | D | KAPANDI (kök neden paraşüt 5,5→3,0 m/s ölçüldü, beklenti 38,81; sim testlerinde yeni kırmızı yok) | `ONARIM-12_gazebo_commitlenmemis_dosyalar.md` |
| 13 | Telsiz frekansı: gövdede RFD900A (900 MHz), depo 433 MHz diyor | D | KARAR VAR (D-499: 433 MHz, RFD900A kullanılmayacak) — donanım değişimi insan işi | `ONARIM-11_jetson_dal_birlestirme.md` |

**Yazılım dışı (takip için):** gövde/motor/GPS kablosu değişimi · Jetson besleme hattı (açılışta brownout) · RTC pili (CR2032) · lens odak kontrolü.
| 14 | Uçuş logları (`results/ucus_20260912…20260917b/` 27 `.bin` + 4 `.tlog` + `DUSUS_ANALIZI.md`) yalnız Emir'in PC'sinde; D-492 kanıtı `.tlog` OneDrive'da tek kopya | D | BEKLİYOR (kullanıcı Emir'in PC'sinde) | — |
| 15 | Pixhawk düşüş sonrası durum: kart/firmware/TELEM2 ayarı sağlam, 1025 param yedeklendi; 🔴 pusulalar ~49° tutarsız ("Compasses inconsistent"), GPS iç mekânda fix yok | A | TESPİT TAMAM · kalibrasyon aracı hazır — drone toplanınca koşulacak (47,4° sürüyor); dış GPS testi BEKLİYOR | `ONARIM-15_pixhawk_durum_tespiti.md` |
| 16 | (kullanıcı maddesi 3) Jetson YKS'yi sabit IP yerine keşifle bulsun — "Bluetooth mantığı" | C | KAPANDI (imzalı duyuru + eşleşme kodu; hub adresi öğrenir; Jetson↔PC canlı: 0,2 s'de bulundu, 83+25 çerçeve; komut yolu doğrulandı) | `ONARIM-03b_yks_kesfi.md` |
