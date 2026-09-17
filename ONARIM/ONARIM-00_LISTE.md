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
| 06 | İşaretli video yolu yarım: `jetson_baslat.sh` yayını loopback'te tutuyor, T227 bayrağı yok | B | AÇIK | — |
| 07 | Otomatik başlatma yok; FOV/YKS_IP/IKA_IP her seferinde elle | C saha | AÇIK (güvenlik kararı) | — |
| 08 | Log saatleri Pixhawk'la hizalanmıyor (RTC pilsiz; fake-hwclock yalnız telafi); log adında boot id yok | C | KAPANDI (yazılım: pixhawk_ms eşlemesi + boot_id; RTC pili donanım) | `ONARIM-08_log_zaman_hizalama.md` |
| 09 | YKS→İHA komut hattı: 5007 dinleyen yok; PC IP DHCP ile değişiyor | C | AÇIK | — |
| 10 | İKA ve systemd birimleri sahada hiç koşmadı; Jetson paketi depodan geride; `--kuru` ultralytics'siz yorumlayıcıya TAMAM diyordu | C | KISMEN (paket eşitlendi, yorumlayıcı modül denetimi eklendi; birim kurulumu/saha koşusu BEKLİYOR) | `ONARIM-10_jetson_paket_senkronu.md` |
| 11 | Jetson dalı `jetson/tek-yol-20260912` master'a girmemiş; D-480…484 numara çakışması; Emir'in PC'sinde D-490/491/492 düşüş analizleri | D depo | KAPANDI (birleştirildi, D-477…484→D-495…502, T261→T265; yeni kırmızı yok) — Emir'in D-49x'leri gelince D-503+ | `ONARIM-11_jetson_dal_birlestirme.md` |
| 12 | Commitlenmemiş `world_generator.py`/`navitas_anim.cc` mujoco testini düşürüyor | D | BEKLİYOR (sahibi oturum) | — |
| 13 | Telsiz frekansı: gövdede RFD900A (900 MHz), depo 433 MHz diyor | D | KARAR VAR (D-499: 433 MHz, RFD900A kullanılmayacak) — donanım değişimi insan işi | `ONARIM-11_jetson_dal_birlestirme.md` |

**Yazılım dışı (takip için):** gövde/motor/GPS kablosu değişimi · Jetson besleme hattı (açılışta brownout) · RTC pili (CR2032) · lens odak kontrolü.
| 14 | Uçuş logları (`results/ucus_20260912…20260917b/` 27 `.bin` + 4 `.tlog` + `DUSUS_ANALIZI.md`) yalnız Emir'in PC'sinde; D-492 kanıtı `.tlog` OneDrive'da tek kopya | D | BEKLİYOR (kullanıcı Emir'in PC'sinde) | — |
