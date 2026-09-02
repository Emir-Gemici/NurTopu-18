# Donanım-öncesi prova — 3 Eylül 2026 (D-404)

> Aviyonik/Jetson gelmeden (5 Eylül) yazılım tarafında **ek iş kalmasın** diye
> koşulan kuru provalar. Hepsi PC'de, donanımsız; **hiçbiri saha kanıtı
> değildir** — yalnız "ilk koşum kör olmayacak" kanıtıdır (FAZ_B §5).
> Her dosyanın son satırı gerçek çıkış kodudur (`exit=N`).

| dosya | komut | beklenen | ölçülen |
|---|---|---|---|
| `jetson_baslat_kuru_udp.txt` | `KIP=udp YKS_IP=192.168.1.10 IKA_IP=192.168.1.20 FOV=78 bash jetson_paket/jetson_baslat.sh --kuru` | exit 0; 14550/14551/14552 uçları, `--mav-sysid`/`--sysid`, `--ekransiz`; `/dev/tty` ile hiçbir tüketici yok | **exit 0** |
| `jetson_baslat_kuru_sik.txt` | `KIP=sik FOV=78 bash jetson_paket/jetson_baslat.sh --kuru` | exit 0; `navitas-seri-hub` satırı `--port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007`; tüketiciler `127.0.0.1:5100`'e; `[VAR] seri_hub.py` | **exit 0** |
| `jetson_baslat_kuru_udp_EKSIK_beyan.txt` | `KIP=udp FOV=78 … --kuru` (YKS_IP/IKA_IP verilmedi) | **fail-closed**: `[EKSIK] YKS_IP`, `[EKSIK] IKA_IP`, exit 3 | **exit 3** |
| `saha_baslat_komutlar.txt` | `scripts/saha_baslat.py --komutlar` | YKS satırında `--iha <JETSON_IP>:5007` (D-403 KRİTİK-1) | **exit 0** |
| `surum_dondur_dogrula.txt` | `scripts/surum_dondur.py --dogrula` | künye yok → "DONDURULMADI", exit **3** (mühür ~18 Eylül, kullanıcı kararı) | **exit 3** |
| `seri_hub_help.txt` | `comms/seri_hub.py --help` | CLI `--port --baud --bind --tuketici --log-aralik` | **exit 0** |

Notlar:
- `[YOK] mavproxy.py (PATH)` PC'de beklenir; Jetson'da `pip3 install MAVProxy`
  (`JETSON_BASLAT.md`). Kuru koşu bunu **gizlemez**, raporlar.
- SiK kipinde betik yalnız YKS hedefini verir (tek hatta bir kez); İKA'nın
  hangi hatta olduğu cumartesi topolojiyle karara bağlanır (FAZ_B §4b).
- systemd kurulum / `--kapi` / `--dogrudan` kipleri Windows'ta koşulamaz;
  Jetson'daki ilk koşum bunların ilk kanıtı olacak (test K5 kuru çıktısının
  birim `ExecStart` satırlarıyla aynı olduğunu kilitler).
