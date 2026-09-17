# ONARIM-00 — 17 Eylül düşüşü sonrası yazılım eksikleri: ana liste

**Kod adı:** `ONARIM` · her madde ayrı dosya `ONARIM-NN_<konu>.md` (NN = aşağıdaki madde no).
**Başlangıç:** 17 Eylül 2026 · **Bağlam:** REVIEW_LOG D-493 (düşüş + Jetson kayıt incelemesi).
**Çalışma sırası (kullanıcı onayı):** 2 → 3 → 4 → 1 → kalanlar.

Durum etiketleri: `AÇIK` · `SÜRÜYOR` · `KAPANDI (kanıt: …)` · `BEKLİYOR (insan/karar)`.

| No | Sorun | Grup | Durum | Dosya |
|---|---|---|---|---|
| 01 | Hover kapısı tüm dosyanın tepesine bakıyor (kalkış/iniş geçicileri) + "motor çıkış farkı" tanımı ekibin yöntemiyle eşleşmedi | A uçuş güvenliği | BEKLİYOR (Emir'in log/yöntemi) | — |
| 02 | `jetson_baslat.sh --kapi` parametre indirmesi (~42 s @57600) bitmeden ölçüyor → yanlış DÜŞTÜ | A | KAPANDI (test 44 OK + mutasyon; canlı koşu yok) | `ONARIM-02_mavlink_kapi_param_bekleme.md` |
| 03 | Jetson'da kare başına kalıcı model/karar kaydı yok (stdout yalnız açılış); journald ayarı tekrarlanabilir değil | A | KAPANDI (6+44 test, mutasyon, Jetson'da gerçek kamera koşusu) | `ONARIM-03_jetson_gorev_kaydi.md` |
| 04 | Canlı kamerada her karar `MASKE_YOK` (kayıtlı resimde maske var) — ONARIM-03 ölçümü: zemin 0 px, **engel ~%97,5** | B algı | SÜRÜYOR | — |
| 05 | IMX477+6 mm odak ve FOV ölçülmedi (`--fov 63` BEYAN); sürücü yalnız 16:9 | B | BEKLİYOR (kamera uzağa) | — |
| 06 | İşaretli video yolu yarım: `jetson_baslat.sh` yayını loopback'te tutuyor, T227 bayrağı yok | B | AÇIK | — |
| 07 | Otomatik başlatma yok; FOV/YKS_IP/IKA_IP her seferinde elle | C saha | AÇIK (güvenlik kararı) | — |
| 08 | Log saatleri Pixhawk'la hizalanmıyor (RTC pilsiz; fake-hwclock yalnız telafi); log adında boot id yok | C | AÇIK | — |
| 09 | YKS→İHA komut hattı: 5007 dinleyen yok; PC IP DHCP ile değişiyor | C | AÇIK | — |
| 10 | İKA ve systemd birimleri sahada hiç koşmadı | C | AÇIK | — |
| 11 | Jetson dalı `jetson/tek-yol-20260912` master'a girmemiş; D-480…484 numara çakışması; **Emir'in PC'sinde D-490/491/492 düşüş analizleri** (master'da aynı numaralar Gazebo/Jetson) — `LOG_ENVANTERI_20260917.md` | D depo | AÇIK | — |
| 12 | Commitlenmemiş `world_generator.py`/`navitas_anim.cc` mujoco testini düşürüyor | D | BEKLİYOR (sahibi oturum) | — |
| 13 | Telsiz frekansı: gövdede RFD900A (900 MHz), depo 433 MHz diyor | D | BEKLİYOR (ölçüm) | — |

**Yazılım dışı (takip için):** gövde/motor/GPS kablosu değişimi · Jetson besleme hattı (açılışta brownout) · RTC pili (CR2032) · lens odak kontrolü.
| 14 | Uçuş logları (`results/ucus_20260912…20260917b/` 27 `.bin` + 4 `.tlog` + `DUSUS_ANALIZI.md`) yalnız Emir'in PC'sinde; D-492 kanıtı `.tlog` OneDrive'da tek kopya | D | BEKLİYOR (kullanıcı Emir'in PC'sinde) | — |
