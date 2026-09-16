# SAHA RUNBOOK — MAVLink TUNNEL (yönlendirme)

Tünel saha runbook'unun **tek kanonik kopyası** pakettedir, Jetson'a paketle birlikte gider ve
komut satırları testle kilitlidir:

**`jetson_paket/TUNEL_SAHA_RUNBOOK.md`** (kilit: `tests/test_mavlink_tunel_sozlesme.py` S4)

İçerik haritası:

| § | konu |
|---|---|
| 1 | Pixhawk TELEM1/TELEM2 parametreleri — yalnız okuma |
| 2 | Jetson UART düğüm doğrulaması (`ls -l /dev/ttyTHS* /dev/ttyTCU*`, pin 8/10 geri döngü, `mavproxy.py --master=<düğüm> --baudrate 57600`) |
| 3 | Jetson ortam değişkenleri ve `KIP=tunel` kurulumu (`--kuru` / `--kapi`) |
| 4 | Windows yer kurulumu: Mission Planner COM + ayna (UDP Client 127.0.0.1:14570), `yks_gui --tunel` |
| 5 | Pixhawk reboot sonrası yordam |
| 6 | K8-0 ön kontrolleri (i)–(v) |
| 7 | K8a ham tünel — `sik_rf_olc` tünel kipi komutları |
| 8 | K8b üretim yolu + çok parçalı `--prob-dolgu 165/473` kayıtları; ÖLÇÜLEMEDİ satırları |
| 9 | K8 DÜŞTÜ sırası ve yedek plan |

İlk tezgâh testi sırası: §1 → §2 → §3 (`--kuru`, sonra `--kapi` 3/3) → §4 → §6 (i)–(v) → §7 (K8a) → §8 (K8b).

İkinci bir kopya bilerek YAZILMADI: iki kopya sahada birbirinden sessizce ayrışırdı.
