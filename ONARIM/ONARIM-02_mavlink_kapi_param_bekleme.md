# ONARIM-02 — MAVLink kapısı parametre indirmesi bitmeden ölçmesin

**Durum:** KAPANDI (yazılım) · canlı Pixhawk'la `--kapi` koşusu **YAPILMADI** (İHA hasarlı; systemd birimleri Jetson'da hiç kurulmadı → ONARIM-10)
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 02

## Sorun (kanıt)
- `jetson_paket/jetson_baslat.sh` `kapi()`: çoğullayıcıyı (MAVProxy) yeniden başlatıp **sabit `sleep 3`** sonra üç uçta `mavlink_dogrula` koşuyordu.
- 15 Eylül tezgâh ölçümü (D-491 §3, `JETSON_DEVIR_20260915.md` §9): TELEM2 @57600'de MAVProxy açılışta **1025 parametre ~42 s** indiriyor; bu sürede konum 1,9–2,0 Hz / durum 0,5 Hz → **0/3**. İndirme bitince 3/3 (7,7 / 2,1 / 1,1 Hz).
- Sonuç: sahada `--kapi` sağlam bir hattı **yanlış DÜŞTÜ** ilan eder ve tüketiciler (model, iniş yayıncısı, komut alıcısı) başlatılmazdı.

## Çözüm
- İndirme bitişinin işareti: MAVProxy `Saved N parameters to <state-basedir>/mav.parm` yazar (kanıt: `results/jetson_20260915/jetson_tmp_loglari/navitas-mavproxy-telem2.log:25-26`). Birimde `--state-basedir ${LOG_DIZIN}/mavproxy` → dosya `$LOG_DIZIN/mavproxy/mav.parm`.
- Yeni `param_indirme_bekle()`: çoğullayıcı restart'ından **önce** alınan epoch'tan sonra yazılmış `mav.parm`'ı 1 s aralıkla bekler. Eski koşudan kalan dosya sayılmaz (mtime ≥ başlangıç).
- Tavan `PARAM_BEKLE_TAVAN_S` (varsayılan 90 s). Dolarsa `UYARI` basar ve **yine ölçer** — hükmü `mavlink_dogrula` verir (fail-closed korunur, bekleme kapıyı geçirmez).
- `sleep 3` kaldırıldı. Kapı ölçütleri/eşikleri **değişmedi**.

## Değişen dosyalar
- `jetson_paket/jetson_baslat.sh` — `param_indirme_bekle()` + `kapi()` içinde çağrı.
- `tests/test_faz_b_jetson_baslat.py` — sahte `systemctl` çoğullayıcı restart'ında `mav.parm` yazar (`FAKE_PARM_GECIKME`, `FAKE_PARM_YAZMA`); 2 yeni test:
  - `test_K10_kapi_param_indirmesi_bitmeden_OLCMEZ` — 4 s gecikmeli `mav.parm`; üç doğrulamanın başlangıcı da yazımdan sonra.
  - `test_K10_kapi_ESKI_mav_parm_sayilmaz_tavanda_UYARI_ve_yine_olcer` — 1 saat eski `mav.parm` sayılmaz, tavan 2 s → UYARI, 3 uç yine ölçülür.
  - Yan düzeltme: shim zaman damgası `EPOCHREALTIME` Türkçe yerelde virgüllü (`1789632863,92`) → `float()` hatası. Mevcut `test_K10_kapi_uc_uc_AYNI_ANDA…` testi bu makinede bu yüzden **ERROR** veriyordu; ayrıştırma virgül→nokta yapıldı.

## Kanıt (koşulan komutlar)
```
.venv/bin/python -m unittest discover -s tests -p test_faz_b_jetson_baslat.py
Ran 44 tests in 32.349s  OK
```
Mutasyon kontrolü (test gerçekten yakalıyor mu):
- `param_indirme_bekle "$bas"` → `sleep 3` geri konunca: **2 FAIL** (iki yeni test).
- `-ge "$bas"` → `-ge 0` (eski dosyayı kabul et): **1 FAIL** (`ESKI_mav_parm` testi).
- Geri alınınca OK.

İlgili testler: `test_faz_b_nano_kurulum` OK (8 skip) · `test_faz_b_kamera_lan` OK · `test_faz_b_pixhawk_sablon` OK · `test_faz_b_surum_dondurma` OK · `test_isaretli_gosterici` OK · `test_saha_kosum_kagidi` OK · `test_belge_kilidi` OK · `test_yks_sik_yordami` OK.
`test_jetson_comms_paketi` **2 FAIL — HEAD'de de aynı** (önceden var): paket kopyaları bayat `model_registry.json`, `rpi_inference.py` → **ONARIM-04 ile ilişkili olabilir** (Jetson hangi `rpi_inference` kopyasını koşuyor?).

## Jetson'a dağıtım
- `~/navitas/jetson_paket/jetson_baslat.sh` güncellendi (md5 `0f7dd459…` = depo). Eski hâli `jetson_baslat.sh.onarim02-oncesi` (md5 `8f30dd93…`). `bash -n` temiz.

## Kalan risk / sonraki
- Canlı doğrulama yok: Pixhawk bağlıyken `sudo -E bash jetson_baslat.sh --kapi` çıktısında `[PARAM] indirme bitti (~42 s)` ve 3/3 görülmeli.
- Hazırlık süresi: bekleme artık ~42 s'yi görünür kılıyor (şartname §6.2: her 30 s ≈ 1 puan). Kısaltmanın yolu `SERIAL2_BAUD 921600` (Pixhawk parametresi + `PIXHAWK_BAUD`) — **kullanıcı/Emir kararı**, dokunulmadı.
- `--dogrudan` kipi (systemd'siz) hâlâ çoğullayıcıdan sonra `sleep 3` ile tüketicileri başlatıyor; kapısı olmadığı için yanlış hüküm üretmiyor ama ilk ~40 s model düşük hızlı MAVLink görür. Gerekirse ONARIM-07/10'da ele alınır.
