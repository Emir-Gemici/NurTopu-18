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
