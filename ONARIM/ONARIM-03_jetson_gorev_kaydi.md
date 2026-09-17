# ONARIM-03 — Jetson görev kaydı: kare başına, fsync'li, güç kesilmesine dayanıklı

**Durum:** KAPANDI (yazılım + Jetson'da gerçek kamerayla koşuldu) · Pixhawk verisiyle (ölçekli karar) koşu **YAPILMADI** (Pixhawk hattı sessiz)
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 03

## Sorun (kanıt)
- Listedeki ilk tanım ("loglar `/tmp`'de") **eksikti**. İnceleme sonucu gerçek durum:
  - systemd kipinde servis çıktıları journald'a gidiyor; `--dogrudan` kipinde `$LOG_DIZIN/<birim>.log` (diske). `/tmp` yalnız 15 Eylül'de **elle** başlattığımız koşuda kullanıldı.
  - **Asıl boşluk:** `codes/rpi_inference.py` kamera döngüsünde kare başına **hiçbir kalıcı kayıt yok**. stdout yalnız açılış satırlarını basıyor (`results/jetson_20260915/jetson_tmp_loglari/navitas_canli_20260915/rpi_telem2c.log`). Karar kaydı yalnız **PC'deki YKS**'de (`hakem_log.jsonl`) vardı → Jetson'da maske, tespit, ölçek, çıkarım süresi hiç görülmüyordu. 15 Eylül'deki MASKE_YOK'un nedeni bu yüzden cihazda araştırılamadı.
  - journald ani kesilmede 5 dk'ya kadar kaybediyordu (Jetson oturumu 17 Eylül'de elle 5 s'ye indirdi; tekrarlanabilir değildi).

## Çözüm
1. **`rpi_inference --gorev-kaydi DIZIN`** (yalnız `--camera`): `DIZIN/<YYYYmmdd_HHMMSS>_<boot_id 8>_<pid>/gorev_kaydi.jsonl`. Yazıcı mevcut `comms/hakem_kaydi.HakemKaydi` → **her satır flush + fsync**, `monotonic_s`, oturum UUID.
   - `GOREV_BASLADI`: boot_id, pid, model adı, argv.
   - `KARE` (her kare): `kare`, `dusen_toplam`, `cikarim_ms`, `zemin_px`, `engel_px`, `maske_hw`, `olcek_kaynak`, `mpp`, `yol`, `guven`, `red`, `yayinlandi`.
   - `KAMERA_BITTI`: kamera özeti (okunan, düşen, fps ortalama/p95) · `OTURUM_BITTI`.
   - **Kayıt kararı etkilemez:** yazma hatası uçuşu durdurmaz → bir kez `UYARI`, kayıt kapanır. Dizin açılamazsa `UYARI` + kayıtsız devam.
2. **`jetson_baslat.sh`**: `RPI_EK_ARGS`'a her zaman `--gorev-kaydi $LOG_DIZIN/gorev` (diskte, `~/navitas/results/jetson_log/gorev`).
3. **`jetson_paket/saha_log_ayarlari.sh`** (yeni): 17 Eylül'de Jetson'a elle yapılan journald (`Storage=persistent · SyncIntervalSec=5s · RateLimitBurst=100000`) + fake-hwclock (10 dk) ayarlarını **drop-in** olarak tekrarlanabilir kurar; `--kuru` destekli; apt upgrade yapmaz.

## Değişen dosyalar
- `codes/rpi_inference.py` — `run_camera(..., gorev_kaydi=None)`, argparse `--gorev-kaydi`, doğrulama, `main` açma/kapatma; yardımcılar dosya sonunda (`_hakem_kaydi_modulu`, `_boot_id`, `gorev_kaydi_yolu`, `gorev_kaydi_ac`, `gorev_kaydi_kapat`, `_gorev_kare_alanlari`, `_gorev_kaydina_yaz`).
- `jetson_paket/jetson_baslat.sh` — `--gorev-kaydi` her zaman.
- `jetson_paket/saha_log_ayarlari.sh` — yeni.
- `tests/test_onarim03_gorev_kaydi.py` — yeni, 6 test.
- `tests/test_faz_b_jetson_baslat.py` — env beklentisi `RPI_EK_ARGS=--fov 90 --gorev-kaydi <LOG_DIZIN>/gorev`.
- Satır kayması atıfları: `tests/test_fdr_t244_ic_celiski.py`, `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` (2 yer), `FDR/ACIK_KALEMLER.md`: `rpi_inference.py:2562,2707` → `:2568,2719`.

## Kanıt
```
test_onarim03_gorev_kaydi   Ran 6  OK
test_faz_b_jetson_baslat    Ran 44 OK
test_faz_b_rpi_ekransiz OK · test_p5_histerezis OK · test_t201_kamera_yonu OK · test_seri_pixhawk_kilidi OK
test_fdr_t244_ic_celiski OK (atıf güncellemesinden sonra) · test_fdr_sarkan_atif_kapisi OK
test_isaretli_gosterici OK · test_saha_kosum_kagidi OK · test_faz_b_kamera_lan OK · test_faz_b_surum_dondurma OK · test_belge_kilidi OK
```
Mutasyon: `satir["yayinlandi"] = True` → `pass`: **FAIL** · yazma hatası yakalamasını daralt: **ERROR** · geri alınca OK.
Önceden kırmızı (bu işten bağımsız, HEAD temiz worktree'de de): `test_gece_akis_diyagramlari` 2 FAIL (FDR akış şeması düğüm satırları zaten bayattı) · `test_jetson_comms_paketi` 2 FAIL (paket kopyaları bayat).

### Jetson'da gerçek koşu (17 Eyl 11:26, IMX477 → köprü → v36 → kayıt)
Komut: `kamera_koprusu --kaynak nvargus --host 127.0.0.1` + `rpi_inference --camera --kaynak http://127.0.0.1:8080/video --mavlink udp:127.0.0.1:14550 --mav-sysid 1 --fov 63 --ekransiz --gorev-kaydi …` (Pixhawk hattı sessiz: `/dev/ttyTHS1` 3 s'de 2 bayt).
Ham kanıt: `results/onarim/onarim03_jetson_gorev_kaydi/` (41 satır JSONL + stdout).
- 37 kare, 0 düşen, `SIGINT` → `KAMERA_BITTI` + `OTURUM_BITTI` yazıldı.
- Çıkarım ~217–220 ms/kare (ilk kare 5,6 s ısınma), **fps ortalama 2,72 · p95 4,04** (`.pt`, TensorRT değil).
- 🔴 **ONARIM-04 için ilk ölçüm:** her karede `zemin_px = 0`, `engel_px ≈ 2 020 000` / 1920×1080 = 2 073 600 → model karenin **~%97,5'ini ENGEL** sınıfı işaretliyor, zemin hiç yok → `red = MASKE_YOK`. Kamera şu an bulanık/yakın sahne; bu tek başına kök neden değildir ama MASKE_YOK mekanizması artık **ölçülebilir**: "maske boş" değil, "her şey engel".

## Jetson'a dağıtım
- `~/navitas/codes/rpi_inference.py` güncellendi (md5 `4529255b…` = depo). Eski hâli `rpi_inference.py.onarim03-oncesi` (md5 `eae1f191…` = commit `230c8c8c`; Jetson T233'ten bir sürüm gerideydi).
- `~/navitas/jetson_paket/saha_log_ayarlari.sh` kopyalandı; **uygulanmadı** (aynı ayarlar Jetson'da zaten etkin: `SyncIntervalSec=5s`, `Storage=persistent`, `RateLimitBurst=100000`, `fake-hwclock-save.timer enabled`).

## Kalan risk
- Satır başına fsync ~3–5 Hz'de NVMe için önemsiz; TensorRT ile 15–20 Hz'de de ölçülmeli.
- Kayıt dizini büyümesi: 1 saatlik uçuş ≈ 15 000 satır ≈ 5 MB — sorun değil, temizlik yok.
- `iha_inis_yayinci` / `iha_komut_alici` kendi kalıcı kayıtlarını tutmuyor (stdout → journald 5 s). Gerekirse ayrı madde.
