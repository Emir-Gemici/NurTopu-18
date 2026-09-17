#!/usr/bin/env bash
# =============================================================================
# jetson_baslat.sh — Jetson'i TEK komutla kaldirir (Faz B · Gorev C · 2026-09-02)
#
# NEDEN
#   * Sartname §6.2 (thazirlik <= 900 s, her 30 s +1 puan): Jetson tek komutla
#     kalkmali. Hands-off: firlatmadan sonra bir surec olurse kimse dokunamaz —
#     surec KENDI kalkmali (systemd Restart=always, RestartSec=2,
#     StartLimitIntervalSec=0). FAZ_B_GUN_PLANI §3 ve §4b "surec gozcusu".
#   * CONTRACTS §7.4 (D-403): seri Pixhawk TEK SAHIPLIDIR. /dev/ttyACM0'i YALNIZ
#     cogullayici (MAVProxy) acar; tuketiciler kendi UDP ucundan konusur:
#         rpi_inference    --mavlink udp:127.0.0.1:14550  (okur)
#         iha_inis_yayinci --mavlink udp:127.0.0.1:14551  (okur)
#         iha_komut_alici  --mavlink udp:127.0.0.1:14552  (yazar, command_long)
#     Uclar ve --sysid/--mav-sysid pinleri BELGEDE degil BURADA ve
#     systemd/*.service icindedir; tests/test_faz_b_jetson_baslat.py bunlari
#     CONTRACTS.md §7.4 metniyle kilitler.
#   * KIP=sik (433 MHz): SiK seri portu da tek sahiplidir (D-403 §4b). Uc surec
#     /dev/ttyUSB0'i DOGRUDAN acmaz; navitas-seri-hub portu tek basina acar,
#     surecler UDP loopback 127.0.0.1:5100'e yazar, hub seri hattan geleni
#     --tuketici ucuna (iha_komut_alici --bind 127.0.0.1:5007) verir.
#   * D-405 (curutucu, 2026-09-02 "KURU vs GERCEK AYRISMASI"): --kur artik
#     enable + RESTART (degisen beyan canli surece uygulanir); --kapi uc ucu AYNI
#     ANDA kosar (CONTRACTS §7.4 "uc uc ayni anda acikken"); SERVIS_KULLANICI birim
#     dosyasina islenir (User=, ~/.local/bin); --kuru herhangi [YOK]'ta 3 ile durur.
#   * KAMERA=http://127.0.0.1:8080/video (SAHA_HAZIRLIK_PLANI_20260903 §1.4, Gorev K):
#     Jetson Nano'da RPi HQ (IMX477, CSI) yalniz GStreamer nvarguscamerasrc ile
#     okunur; o da yalniz SISTEM Python 3.6 + sistem OpenCV'de var. rpi_inference
#     (ultralytics, Python >= 3.8 venv = PYTHON3) kamerayi DOGRUDAN acamaz.
#     navitas-kamera-koprusu (scripts/kamera_koprusu.py, KAMERA_PYTHON=/usr/bin/python3)
#     kareyi MJPEG HTTP olarak sunar; rpi_inference --kaynak http://127.0.0.1:8080/video
#     ile okur (DroidCam kalibi). Loopback http disinda KAMERA (indeks, /dev/videoN,
#     DroidCam WiFi URL'si) kopruyu KALDIRMAZ.
#
# KULLANIM
#   bash jetson_baslat.sh --kuru        HICBIR SEY baslatmaz; kosacagi komutlari basar
#   sudo -E bash jetson_baslat.sh       systemd birimlerini kurar (enable + restart; acilista da kalkar)
#   sudo -E bash jetson_baslat.sh --kapi  kurar, YALNIZ cogullayiciyi kaldirir, 3 ucta AYNI ANDA
#                                       mavlink_dogrula kosar; 3/3 GECTI ise tuketicileri kaldirir
#   bash jetson_baslat.sh --dogrudan    systemd'siz: nohup + log (prova/ayiklama — GOZCU YOK)
#   sudo bash jetson_baslat.sh --durdur birimleri durdurur (disable --now), nohup pid'lerini oldurur
#   bash jetson_baslat.sh --durum       birim durumu + yeniden-baslatma sayisi (cokme dongusu GORUNUR)
#   Degiskenler ortamdan ezilir:   KIP=sik FOV=78 bash jetson_baslat.sh --kuru
#   CSI kamera (kopru):            KAMERA=http://127.0.0.1:8080/video FOV=78 ... --kuru
#   YKI canli kamera (ayri LAN):   KAMERA_KOPRU_BIND=0.0.0.0 ... --kuru
#     Video SiK'e GIRMEZ. 0.0.0.0 yalniz acik beyanla; TCP 8080 YKI IP'sine
#     guvenlik duvarinda sinirlanir. Varsayilan 127.0.0.1 (disariya KAPALI).
#   Isaretli gosterici (T228):      GOSTERICI_KIP=x11 ... --kuru   (x11|drm|rtsp|kapali; varsayilan kapali)
#     rpi_inference'a --isaretli-yayin $ISARETLI_YAYIN (T227, 127.0.0.1:8081) verir; gosterici
#     surecini bu betik KALDIRMAZ (x11 autostart / drm birimi / rtsp elle: gosterici/GOSTERICI_KURULUM.md).
#
# CIKIS KODLARI: 0 tamam · 1 hata (fail-closed, hicbir sey baslatilmadi) ·
#                3 --kuru'da beyan/paket/ana makine eksik (gercek kosum DURURDU)
# =============================================================================
# CRLF KORUMASI — ILK KOMUT OLMALI. Windows calisma agaci core.autocrlf=true ile
# CRLF'tir (olculdu: `git ls-files --eol` -> w/crlf); USB'ye kopyalanan betik CR
# tasir ve bash "$'\r': command not found" der. CR gorulurse betik CR'siz
# kopyasiyla yeniden calisir (bu satirin kendi CR'i satir sonu yorumunda kalir).
# NEDEN bash-ici algi (D-405, curutucu K8 bulgusu): MSYS grep CR'i GORMUYOR, bu
# yuzden `grep -q $'\r'` dali Windows'ta hic kosmadi (test bos gecti); `head -c`
# + bash kalibi Git Bash'te de tetiklenir, K8 dali gercekten kosturur.
# NAVITAS_CR_KOPYA gecici dosyanin YOLUNU tasir (1 degil): trap yalniz $0 o yolsa
# siler — ortamdan sizan NAVITAS_CR_KOPYA=1 asil betigi silemez.
case "$(head -c 4096 "$0" 2>/dev/null)" in *$'\r'*) _cr="$(mktemp)" && tr -d '\r' < "$0" > "$_cr" || { echo "HATA: CR'siz kopya olusturulamadi" >&2; exit 1; }; NAVITAS_PAKET_DIZIN="${NAVITAS_PAKET_DIZIN:-$(cd "$(dirname "$0")" && pwd)}" NAVITAS_CR_KOPYA="$_cr" exec bash "$_cr" "$@";; esac # CRLF
set -euo pipefail
CR_KOPYA=""
if [ -n "${NAVITAS_CR_KOPYA:-}" ] && [ "$NAVITAS_CR_KOPYA" = "$0" ]; then CR_KOPYA="$0"; trap 'rm -f "$0"' EXIT; fi

PAKET_DIZIN="${NAVITAS_PAKET_DIZIN:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
BIRIM_DIZIN="$PAKET_DIZIN/systemd"
BETIK_YOLU="$PAKET_DIZIN/jetson_baslat.sh"   # hata iletilerinde $0 DEGIL (CR kopyasinda $0 silinen gecici dosyadir)

# ── Beyan degiskenleri (ortamdan ezilir) ─────────────────────────────────────
# Servis kullanicisi: birimlerdeki User=, MAVProxy'nin ~/.local/bin yolu, chown ve
# NAVITAS_KOK varsayilani buradan turer. NEDEN ${SUDO_USER:-${USER:-navitas}}
# (D-405, curutucu SERVIS_KULLANICI bulgusu): kilavuz kullanici adini zorlamaz;
# `sudo -E` altinda SUDO_USER, sudosuz (--kuru/--dogrudan) USER ayni kisiyi verir —
# --kuru ile --kur AYNI kullaniciyi hesaplar. Yanlis kullanici birimleri
# 217/USER ile sonsuz restart dongusune sokar; dosya_denetle `id -u` ile durur.
SERVIS_KULLANICI="${SERVIS_KULLANICI:-${SUDO_USER:-${USER:-navitas}}}"
PIXHAWK_SERI="${PIXHAWK_SERI:-/dev/ttyACM0}"   # Pixhawk USB/telem — YALNIZ cogullayici acar
PIXHAWK_BAUD="${PIXHAWK_BAUD:-57600}"
# Pixhawk SYSID_THISMAV. comms/iha_komut_alici.VARSAYILAN_HEDEF_SYSID ile AYNI (test
# kilitler). D-389: pin BEYANA dayanir — arac farkli sysid'deyse buradan ez.
SYSID="${SYSID:-1}"
YKS_IP="${YKS_IP:-}"         # KIP=udp'de ZORUNLU: hakem ekrani (karar + IHA_LANDED buraya)
IKA_IP="${IKA_IP:-}"         # KIP=udp'de ZORUNLU: IKA (rota + IHA_LANDED; sartname §2.2.5 kilidi)
KIP="${KIP:-udp}"            # udp | sik
SIK_SERI="${SIK_SERI:-/dev/ttyUSB0}"   # KIP=sik: YALNIZ navitas-seri-hub acar
SIK_BAUD="${SIK_BAUD:-57600}"
FOV="${FOV:-}"               # kamera YATAY gorus acisi (derece) — BEYAN edilir, tahmin edilmez
ODAK="${ODAK:-}"             # odak uzakligi (piksel); FOV ile birlikte verilmez (rpi_inference)
SENARYO="${SENARYO:-}"       # rpi_inference --senaryo (olcek kahini katman 2; bos = verilmez)
KAMERA="${KAMERA:-}"         # rpi_inference --kaynak (indeks, /dev/videoN, URL; bos = indeks 0)
                             # http://127.0.0.1:<port>/video -> navitas-kamera-koprusu KALKAR (asagida)
KAMERA_PYTHON="${KAMERA_PYTHON:-/usr/bin/python3}"   # kopru yorumlayicisi: SISTEM Python (GStreamer'li
                             # sistem OpenCV); PYTHON3 (venv) DEGIL — PYTHON3 ezilse de bu DEGISMEZ
KAMERA_KOPRU_BIND="${KAMERA_KOPRU_BIND:-127.0.0.1}" # YKI video LAN dinleme adresi; varsayilan KAPALI
KAMERA_KOPRU_ARGS="${KAMERA_KOPRU_ARGS:-}"   # kopru ek argumanlari (--fps 5, --kalite 70, --kaynak 0 ...);
                             # --host BURAYA YAZILMAZ; KAMERA_KOPRU_BIND tek sahibidir
UB_REFERANS="${UB_REFERANS:-}"   # LAT,LON — IHA-UB kose referansi (T162); bos = alan ihlali denetimi YOK
# iha_inis_yayinci --kanit-timeout: sartname §6.2 IHA gorev suresi
# (karar_sozlesmesi.SARTNAME_IHA_GOREV_SURESI_S = 15*60; SAHA_RUNBOOK §3). Test kilitler.
KANIT_TIMEOUT="${KANIT_TIMEOUT:-900}"
NAVITAS_KOK="${NAVITAS_KOK:-/home/$SERVIS_KULLANICI/navitas}"   # JETSON_KILAVUZ §2 kurulum koku (~/navitas)
PYTHON3="${PYTHON3:-/usr/bin/python3}"
ENV_DOSYA="${ENV_DOSYA:-/etc/navitas.env}"
SYSTEMD_DIZIN="${SYSTEMD_DIZIN:-/etc/systemd/system}"
LOG_DIZIN="${LOG_DIZIN:-$NAVITAS_KOK/results/jetson_log}"

# Birim dosyalarindaki sabit yollar/alanlar; ezildiyse kurulumda sed ile degistirilir
# (yerine_koy ve birimleri_kur AYNI ciftleri kullanir — --kuru ile kurulu birim ayrismaz).
KOK_VARSAYILAN="/home/navitas/navitas"
PYTHON3_VARSAYILAN="/usr/bin/python3"
ENV_DOSYA_VARSAYILAN="/etc/navitas.env"
KULLANICI_VARSAYILAN="navitas"
MAVPROXY_BIN_VARSAYILAN="/home/$KULLANICI_VARSAYILAN/.local/bin"
MAVPROXY_BIN="${MAVPROXY_BIN:-/home/$SERVIS_KULLANICI/.local/bin}"   # ONARIM-10: /opt/navitas/python/bin ile ezilir (venv bagimsizligi)

# ── CONTRACTS §7.4 uclari — TEK KAYNAK (burada + systemd/*.service) ───────────
MAV_UC_RPI="udp:127.0.0.1:14550"      # rpi_inference    --mavlink (okur)
MAV_UC_INIS="udp:127.0.0.1:14551"     # iha_inis_yayinci --mavlink (okur)
MAV_UC_KOMUT="udp:127.0.0.1:14552"    # iha_komut_alici  --mavlink (yazar)
MAV_UCLAR=("$MAV_UC_RPI" "$MAV_UC_INIS" "$MAV_UC_KOMUT")   # kapi bu ucun HEPSINI ister
# NAVITAS protokol uclari (SAHA_RUNBOOK §1/§3 · iha_komut_alici.VARSAYILAN_BIND)
YKS_PORT=5005
IKA_PORT=5006
KOMUT_PORT=5007
SERI_HUB_DINLE="127.0.0.1:5100"                 # KIP=sik: surecler buraya yazar
SERI_HUB_TUKETICI="127.0.0.1:${KOMUT_PORT}"     # hub seri hattan geleni buraya verir
HUB_LAN_PORT="${HUB_LAN_PORT:-5009}"
YKS_ESLESME="${YKS_ESLESME:-}"                   # ONARIM-03: eslesme dosyasi (KIP=ikili, YKS_IP yerine)             # ONARIM-09 KIP=ikili: YKS --iha <jetson>:5009
hub_kipi() { [ "$KIP" = sik ] || [ "$KIP" = ikili ]; }

hata() { echo "HATA: $*" >&2; exit 1; }

# ONARIM-10 (2026-09-17): `-x $PYTHON3` yetmiyordu. Jetson'da varsayilan /usr/bin/python3
# calistirilabilir ama ultralytics yalniz ~/venv312'de -> --kuru [VAR] diyordu, kurulan
# navitas-rpi-inference birimi ilk satirda ModuleNotFoundError ile Restart dongusune girerdi.
PYTHON3_MODULLERI="${PYTHON3_MODULLERI:-ultralytics cv2 numpy pymavlink}"
yorumlayici_modulleri_var() {
  local m kod=""
  for m in $PYTHON3_MODULLERI; do kod="${kod}import $m; "; done
  "$PYTHON3" -c "$kod" >/dev/null 2>&1
}

# MAVProxy pip ile kullanici dizinine kurulur (~/.local/bin); sudo altinda secure_path
# onu gormez. Birim dosyasi (Environment=PATH=...) ile AYNI arama yolu kullanilir.
MAVPROXY_PATH="$MAVPROXY_BIN:/usr/local/bin:/usr/bin:/bin"
mavproxy_var() { PATH="$MAVPROXY_PATH:$PATH" command -v mavproxy.py >/dev/null 2>&1; }

# Ayrı kamera LAN'ı yalnız IPv4 yerel/dinleme adresi kabul eder. Host adi DNS'e
# ve yanlis arayuze sessizce kayabilir; genel Internet adresi acik HTTP kamerayi
# disariya tasir. 0.0.0.0 acik bir opt-in'dir ve asagida KIRMIZI uyari uretir.
yerel_ipv4_var() {
  local ip="$1" a b c d fazla o
  IFS=. read -r a b c d fazla <<< "$ip"
  [ -z "${fazla:-}" ] && [ -n "$a" ] && [ -n "$b" ] && [ -n "$c" ] && [ -n "$d" ] || return 1
  [ "$ip" = "$a.$b.$c.$d" ] || return 1
  for o in "$a" "$b" "$c" "$d"; do
    case "$o" in ''|*[!0-9]*) return 1 ;; esac
    [ "$((10#$o))" -le 255 ] || return 1
  done
  case "$ip" in
    127.0.0.1|0.0.0.0|10.*|192.168.*|169.254.*) return 0 ;;
    172.*) [ "$((10#$b))" -ge 16 ] && [ "$((10#$b))" -le 31 ] ; return $? ;;
    *) return 1 ;;
  esac
}

# ── Kamera koprusu (Gorev K): KAMERA loopback http ise birim kalkar ─────────────
# Port URL'den alinir; yol kamera_koprusu.VIDEO_YOLU olmali (yanlis yol = fail-closed).
KAMERA_KOPRU_PORT_VARSAYILAN=8080     # scripts/kamera_koprusu.py VARSAYILAN_PORT (test kilitler)
KAMERA_KOPRU_YOL="/video"             # kamera_koprusu.VIDEO_YOLU (test kilitler)
KAMERA_KOPRU=0
KAMERA_KOPRU_PORT="$KAMERA_KOPRU_PORT_VARSAYILAN"
case "$KAMERA" in
  http://127.0.0.1:*|http://localhost:*)
    _k="${KAMERA#http://}"; _k="${_k#*:}"          # "<port>/<yol>"
    _port="${_k%%/*}"
    case "$_k" in */*) _yol="/${_k#*/}" ;; *) _yol="" ;; esac
    case "$_port" in ''|*[!0-9]*) hata "KAMERA='$KAMERA': port sayi degil" ;; esac
    [ "$_yol" = "$KAMERA_KOPRU_YOL" ] \
      || hata "KAMERA='$KAMERA': kopru akisi $KAMERA_KOPRU_YOL ile biter (ornek: http://127.0.0.1:${KAMERA_KOPRU_PORT_VARSAYILAN}${KAMERA_KOPRU_YOL})"
    KAMERA_KOPRU=1
    KAMERA_KOPRU_PORT="$_port"
    ;;
esac

# --host'un iki sahibi olamaz. Serbest bicimli ek argumandan almak, --kuru ile
# canli birimin hangi arayuze acildigini belirsizlestirirdi.
case "$KAMERA_KOPRU_ARGS" in
  *--host*) hata "KAMERA_KOPRU_ARGS --host tasiyamaz; KAMERA_KOPRU_BIND kullan" ;;
esac
yerel_ipv4_var "$KAMERA_KOPRU_BIND" \
  || hata "KAMERA_KOPRU_BIND='$KAMERA_KOPRU_BIND': yalniz yerel IPv4, 127.0.0.1 veya acik opt-in 0.0.0.0"
if [ "$KAMERA_KOPRU" = 1 ]; then
  if [ "$KAMERA_KOPRU_BIND" != 127.0.0.1 ]; then
    KAMERA_KOPRU_ARGS="--host $KAMERA_KOPRU_BIND${KAMERA_KOPRU_ARGS:+ $KAMERA_KOPRU_ARGS}"
  fi
elif [ "$KAMERA_KOPRU_BIND" != 127.0.0.1 ]; then
  hata "KAMERA_KOPRU_BIND yalniz KAMERA=http://127.0.0.1:<port>/video koprusu etkinken kullanilir"
fi

# ── Isaretli gosterici (T228 · D-443 · H9_MK15/TASARIM.md): MK15 video hatti, KARAR URETMEZ ──
# ISARETLI_YAYIN: rpi_inference --isaretli-yayin ucu (T227). Gosterici buradan /kare.jpg (x11/rtsp)
#   ya da /video (drm) okur. YALNIZ loopback: isaretli yayin LAN'a acilmaz — disari DP->HDMI
#   donusturucu ya da yedek RTSP ile gider.
# GOSTERICI_KIP: x11 | drm | rtsp | kapali. VARSAYILAN kapali = mevcut davranis DEGISMEZ
#   (rpi_inference'a --isaretli-yayin VERILMEZ). Bu betik gostericiyi KALDIRMAZ: x11 = masaustu
#   autostart (.desktop), drm = elle etkinlestirilen birim (gdm DURUR), rtsp = yedek, elle —
#   gosterici/GOSTERICI_KURULUM.md. --kuru komutu ve [VAR]/[YOK] denetimini basar; --kur/--dogrudan
#   kurulu rpi_inference bayragi tanimiyorsa (T227 yok) DURUR (argparse cikis 2 dongusu yerine).
ISARETLI_YAYIN_PORT_VARSAYILAN=8081   # scripts/isaretli_gosterici.py VARSAYILAN_KAYNAK (test kilitler)
GOSTERICI_BETIK="isaretli_gosterici.py"
ISARETLI_YAYIN="${ISARETLI_YAYIN:-127.0.0.1:$ISARETLI_YAYIN_PORT_VARSAYILAN}"
GOSTERICI_KIP="${GOSTERICI_KIP:-kapali}"
case "$GOSTERICI_KIP" in
  x11|drm|rtsp|kapali) ;;
  *) hata "GOSTERICI_KIP='$GOSTERICI_KIP' taninmiyor (x11 | drm | rtsp | kapali)" ;;
esac
case "$ISARETLI_YAYIN" in
  127.0.0.1:*) _iy_port="${ISARETLI_YAYIN#127.0.0.1:}" ;;
  *) hata "ISARETLI_YAYIN='$ISARETLI_YAYIN': yalniz 127.0.0.1:<port> (isaretli yayin LAN'a ACILMAZ; disari HDMI/RTSP ile)" ;;
esac
case "$_iy_port" in ''|*[!0-9]*) hata "ISARETLI_YAYIN='$ISARETLI_YAYIN': port sayi degil" ;; esac
[ "${#_iy_port}" -le 5 ] && [ "$((10#$_iy_port))" -ge 1 ] && [ "$((10#$_iy_port))" -le 65535 ] \
  || hata "ISARETLI_YAYIN='$ISARETLI_YAYIN': port 1-65535 olmali"
if [ "$KAMERA_KOPRU" = 1 ] && [ "$((10#$_iy_port))" -eq "$((10#$KAMERA_KOPRU_PORT))" ]; then
  hata "ISARETLI_YAYIN portu ($_iy_port) kamera koprusuyle AYNI — iki HTTP sunucusu ayni porta baglanamaz"
fi

# ── KIP'e gore tuketici argumanlari — birimler bunlari $..._ARGS olarak okur ───
RPI_EK_ARGS=""
if [ -n "$FOV" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --fov $FOV"; fi
if [ -n "$ODAK" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --odak $ODAK"; fi
if [ -n "$SENARYO" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --senaryo $SENARYO"; fi
if [ -n "$KAMERA" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --kaynak $KAMERA"; fi
if [ -n "$UB_REFERANS" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --ub-referans $UB_REFERANS"; fi
# ONARIM-03: kare basina karar kaydi HER ZAMAN acik (fsync'li JSONL, LOG_DIZIN diskte).
# 17 Eyl dususunde Jetson'da tek model kaydi yoktu; stdout yalniz acilis satirlarini basar.
RPI_EK_ARGS="$RPI_EK_ARGS --gorev-kaydi $LOG_DIZIN/gorev"
# T228: gosterici acikken isaretli yayin (T227) acilir; kapaliyken bayrak VERILMEZ (mevcut davranis)
if [ "$GOSTERICI_KIP" != kapali ]; then RPI_EK_ARGS="$RPI_EK_ARGS --isaretli-yayin $ISARETLI_YAYIN"; fi
RPI_EK_ARGS="${RPI_EK_ARGS# }"
case "$KIP" in
  udp)
    RPI_TELSIZ_ARGS="--yks-hedef ${YKS_IP}:${YKS_PORT} --ika-hedef ${IKA_IP}:${IKA_PORT}"
    INIS_TELSIZ_ARGS="--yks ${YKS_IP}:${YKS_PORT} --ika ${IKA_IP}:${IKA_PORT}"
    # Kritik eyleyici yalnız yapılandırılmış YKS soketinden komut kabul eder.
    # Kaynak port, YKS'nin dinleme/gönderme soketiyle aynıdır (5005).
    KOMUT_TELSIZ_ARGS="--bind 0.0.0.0:${KOMUT_PORT} --izinli-kaynak ${YKS_IP}:${YKS_PORT}"
    ;;
  sik)
    # Tek hat: her cerceve hub'a BIR kez yazilir (--telsiz-seri gibi); YKS ve IKA
    # ayni 433 MHz yayinini dinler. Seri hattan gelen ACK/CMD hub'in --tuketici
    # ucuna duser (hub tasarimi, D-403 §4b).
    RPI_TELSIZ_ARGS="--yks-hedef ${SERI_HUB_DINLE}"
    INIS_TELSIZ_ARGS="--yks ${SERI_HUB_DINLE}"
    # Seri-hub, SiK'ten çözdüğü çerçeveyi kendi sabit 5100 UDP ucundan yollar.
    KOMUT_TELSIZ_ARGS="--bind ${SERI_HUB_TUKETICI} --izinli-kaynak ${SERI_HUB_DINLE}"
    HUB_LAN_ARGS=""
    ;;
  ikili)
    # ONARIM-09 (17 Eyl 2026): SiK + LAN AYNI ANDA. Surecler sik kipindeki gibi YALNIZ
    # hub'a yazar (kodlari degismez); hub her cerceveyi seriye VE LAN'daki YKS'ye verir,
    # iki hattan gelen CMD/ACK'i ayni tuketici ucuna dusurur. Komut alici tekrari
    # (oturum, seq, cmd) ile bir kez uygular. Seri yoksa LAN yolu yine calisir.
    RPI_TELSIZ_ARGS="--yks-hedef ${SERI_HUB_DINLE}"
    INIS_TELSIZ_ARGS="--yks ${SERI_HUB_DINLE}"
    KOMUT_TELSIZ_ARGS="--bind ${SERI_HUB_TUKETICI} --izinli-kaynak ${SERI_HUB_DINLE}"
    # ONARIM-03: YKS_ESLESME verilirse YKS adresi imzali duyurudan OGRENILIR (DHCP'ye
    # dayanikli, "Bluetooth mantigi"); yoksa sabit YKS_IP beyanı.
    if [ -n "$YKS_ESLESME" ]; then
      HUB_LAN_ARGS="--lan-bind 0.0.0.0:${HUB_LAN_PORT} --lan-yks-eslesme ${YKS_ESLESME}"
    else
      HUB_LAN_ARGS="--lan-bind 0.0.0.0:${HUB_LAN_PORT} --lan-yks ${YKS_IP}:${YKS_PORT}"
    fi
    ;;
  *) hata "KIP='$KIP' taninmiyor (udp | sik | ikili)" ;;
esac
HUB_LAN_ARGS="${HUB_LAN_ARGS:-}"

# /etc/navitas.env'e yazilan ve ExecStart'ta yerine konan anahtarlar
ENV_ANAHTARLAR=(NAVITAS_KOK PYTHON3 LOG_DIZIN KIP PIXHAWK_SERI PIXHAWK_BAUD SYSID
                SIK_SERI SIK_BAUD KANIT_TIMEOUT RPI_EK_ARGS RPI_TELSIZ_ARGS
                INIS_TELSIZ_ARGS KOMUT_TELSIZ_ARGS HUB_LAN_ARGS YKS_ESLESME
                KAMERA_PYTHON KAMERA_KOPRU_BIND KAMERA_KOPRU_PORT KAMERA_KOPRU_ARGS
                GOSTERICI_KIP ISARETLI_YAYIN)   # T228: DRM gosterici birimi ${ISARETLI_YAYIN} okur
# Tek deger tasiyan beyanlar: bosluk/glob/kacis icerirse systemd ($VAR) ve bash (nohup $k)
# ikisi de BOLER/GENISLETIR — --kuru [UYARI] basar (D-405, curutucu --dogrudan glob bulgusu).
TEK_DEGER_ANAHTARLAR=(FOV ODAK SENARYO KAMERA UB_REFERANS YKS_IP IKA_IP SYSID KANIT_TIMEOUT
                      PIXHAWK_SERI PIXHAWK_BAUD SIK_SERI SIK_BAUD NAVITAS_KOK PYTHON3 LOG_DIZIN
                      SERVIS_KULLANICI KAMERA_PYTHON KAMERA_KOPRU_BIND KAMERA_KOPRU_PORT
                      GOSTERICI_KIP ISARETLI_YAYIN)

env_icerik() {
  local k
  for k in "${ENV_ANAHTARLAR[@]}"; do printf '%s=%s\n' "$k" "${!k}"; done
}

yerine_koy() {  # $1: metin -> ${ANAHTAR} ve $ANAHTAR yerine deger (systemd ile ayni anlam)
  local m="$1" k v
  # ONCE birim dosyasindaki sabit yollar (ezilmis kok/python), SONRA degiskenler:
  # ${KAMERA_PYTHON} sistem Python'udur; PYTHON3 venv'e ezildiginde onun degerine
  # DONUSMEMELI (kopru GStreamer icin sistem OpenCV ister). birimleri_kur'daki sed
  # de yalniz birim METNINE dokunur, env dosyasindaki degere degil — ayni anlam.
  m="${m//"$KOK_VARSAYILAN"/"$NAVITAS_KOK"}"
  m="${m//"$PYTHON3_VARSAYILAN"/"$PYTHON3"}"
  for k in "${ENV_ANAHTARLAR[@]}"; do
    v="${!k}"
    m="${m//"\${$k}"/"$v"}"
    m="${m//"\$$k"/"$v"}"
  done
  printf '%s\n' "$m"
}

# ── Birimler ──────────────────────────────────────────────────────────────────
birimler() {  # KIP/KAMERA'ya gore, BASLATMA sirasinda
  echo navitas-cogullayici
  if hub_kipi; then echo navitas-seri-hub; fi
  if [ "$KAMERA_KOPRU" = 1 ]; then echo navitas-kamera-koprusu; fi   # rpi_inference'tan ONCE
  echo navitas-rpi-inference
  echo navitas-iha-inis-yayinci
  echo navitas-iha-komut-alici
}
TUKETICILER="navitas-rpi-inference navitas-iha-inis-yayinci navitas-iha-komut-alici"
# DURDURMA sirasi: once tuketiciler, sonra kopru ve hub, en son cogullayici
TUM_BIRIMLER="$TUKETICILER navitas-kamera-koprusu navitas-seri-hub navitas-cogullayici"

birim_dosyasi() { echo "$BIRIM_DIZIN/$1.service"; }

exec_start_ham() {  # $1 birim -> ExecStart= satiri (degiskenli, CR'siz)
  local d s
  d="$(birim_dosyasi "$1")"
  [ -f "$d" ] || hata "birim dosyasi yok: $d"
  s="$(tr -d '\r' < "$d" | sed -n 's/^ExecStart=//p' | head -n 1)"
  [ -n "$s" ] || hata "$1: ExecStart satiri yok"
  printf '%s\n' "$s"
}
exec_start() { yerine_koy "$(exec_start_ham "$1")"; }

py_yolu() {  # $1 komut satiri -> ilk NAVITAS .py dosyasinin tam yolu (yoksa bos)
  local t
  set -f   # tirnaksiz $1 bosluktan bolunsun ama GLOB acilmasin (KAMERA='*'); hep $(...) icinde cagrilir
  for t in $1; do
    case "$t" in "$NAVITAS_KOK"/*.py) printf '%s\n' "$t"; return 0 ;; esac
  done
  return 0
}

# ── Denetimler (fail-closed) ─────────────────────────────────────────────────
tuketici_denetle() {  # $1 birim  $2 beklenen --mavlink ucu  $3 beklenen sysid pini
  local k
  k="$(exec_start "$1")"
  case " $k " in *" --mavlink $2 "*) ;; *) hata "$1: '--mavlink $2' yok (CONTRACTS §7.4)" ;; esac
  case " $k " in *" $3 "*) ;; *) hata "$1: '$3' pini yok" ;; esac
  case "$k" in *"/dev/tty"*) hata "$1: seri cihaz DOGRUDAN veriliyor — Pixhawk/SiK tek sahipli (CONTRACTS §7.4)" ;; esac
  case "$k" in *"--telsiz-seri"*|*"--serial"*) hata "$1: --serial/--telsiz-seri YASAK; KIP=sik hub uzerinden" ;; esac
}

sozlesme_denetle() {  # birim dosyalari CONTRACTS §7.4'ten sapmis mi? (elle bozulmus birimle kalkilmaz)
  local k uc
  k="$(exec_start navitas-cogullayici)"
  for uc in "${MAV_UCLAR[@]}"; do
    case " $k " in *" --out $uc "*) ;; *) hata "navitas-cogullayici: '--out $uc' yok (CONTRACTS §7.4)" ;; esac
  done
  case " $k " in *" --master=$PIXHAWK_SERI "*) ;; *) hata "navitas-cogullayici: --master=$PIXHAWK_SERI yok" ;; esac
  tuketici_denetle navitas-rpi-inference "$MAV_UC_RPI" "--mav-sysid $SYSID"
  tuketici_denetle navitas-iha-inis-yayinci "$MAV_UC_INIS" "--sysid $SYSID"
  tuketici_denetle navitas-iha-komut-alici "$MAV_UC_KOMUT" "--sysid $SYSID"
  if hub_kipi; then
    k="$(exec_start navitas-seri-hub)"
    case " $k " in *" --port $SIK_SERI "*) ;; *) hata "navitas-seri-hub: '--port $SIK_SERI' yok" ;; esac
    case " $k " in *" --bind $SERI_HUB_DINLE "*) ;; *) hata "navitas-seri-hub: '--bind $SERI_HUB_DINLE' yok" ;; esac
    case " $k " in *" --tuketici $SERI_HUB_TUKETICI "*) ;; *) hata "navitas-seri-hub: '--tuketici $SERI_HUB_TUKETICI' yok" ;; esac
    if [ "$KIP" = ikili ] && [ -n "$YKS_ESLESME" ]; then
      case " $k " in *" --lan-yks-eslesme $YKS_ESLESME "*) ;; *) hata "navitas-seri-hub: KIP=ikili '--lan-yks-eslesme $YKS_ESLESME' yok" ;; esac
    elif [ "$KIP" = ikili ]; then
      case " $k " in *" --lan-yks $YKS_IP:$YKS_PORT "*) ;; *) hata "navitas-seri-hub: KIP=ikili '--lan-yks $YKS_IP:$YKS_PORT' yok" ;; esac
    fi
  fi
  if [ "$KAMERA_KOPRU" = 1 ]; then   # Gorev K: kopru sistem Python'la, dogru portta; tuketici ayni URL'yi okur
    k="$(exec_start navitas-kamera-koprusu)"
    case " $k " in *" $KAMERA_PYTHON "*) ;; *) hata "navitas-kamera-koprusu: yorumlayici $KAMERA_PYTHON degil (SISTEM Python + GStreamer sart): $k" ;; esac
    case "$k" in *kamera_koprusu.py*) ;; *) hata "navitas-kamera-koprusu: ExecStart kamera_koprusu.py kosmuyor" ;; esac
    case " $k " in *" --port $KAMERA_KOPRU_PORT "*) ;; *) hata "navitas-kamera-koprusu: '--port $KAMERA_KOPRU_PORT' yok (KAMERA=$KAMERA)" ;; esac
    if [ "$KAMERA_KOPRU_BIND" = 127.0.0.1 ]; then
      case " $k " in *" --host "*) hata "navitas-kamera-koprusu: varsayilan loopback kipinde beklenmeyen --host: $k" ;; esac
    else
      case " $k " in *" --host $KAMERA_KOPRU_BIND "*) ;; *) hata "navitas-kamera-koprusu: '--host $KAMERA_KOPRU_BIND' yok" ;; esac
    fi
    k="$(exec_start navitas-rpi-inference)"
    case " $k " in *" --kaynak $KAMERA "*) ;; *) hata "navitas-rpi-inference: '--kaynak $KAMERA' yok — kopru kalkar ama tuketici okumaz" ;; esac
  fi
}

beyan_eksikleri() {  # stdout: her satir bir eksik
  if [ -z "$FOV" ] && [ -z "$ODAK" ]; then
    echo "FOV ya da ODAK (kamera geometrisi; rpi_inference --mavlink icin zorunlu — BEYAN edilir, tahmin edilmez)"
  fi
  if [ -n "$FOV" ] && [ -n "$ODAK" ]; then
    echo "FOV ve ODAK birlikte verilmez (rpi_inference: karsilikli dislar)"
  fi
  if [ "$KIP" = ikili ] && [ -z "$YKS_IP" ] && [ -z "$YKS_ESLESME" ]; then
    echo "YKS_IP ya da YKS_ESLESME (KIP=ikili: LAN aynasinin YKS'si; eslesme dosyasi DHCP'ye dayanikli)"
  fi
  if [ "$KIP" = udp ]; then
    if [ -z "$YKS_IP" ]; then echo "YKS_IP (KIP=udp: hakem ekrani hedefi, port $YKS_PORT)"; fi
    if [ -z "$IKA_IP" ]; then echo "IKA_IP (KIP=udp: IKA hedefi, port $IKA_PORT — rota + IHA_LANDED)"; fi
  fi
}

deger_uyarilari() {  # stdout: bosluk/glob/kacis iceren tek-deger beyanlar (bolunur/genisler)
  local k v
  for k in "${TEK_DEGER_ANAHTARLAR[@]}"; do
    v="${!k}"
    [ -n "$v" ] || continue
    case "$v" in *[[:space:]]*|*[\*\?\[]*|*[\\\"\']*)
      echo "[UYARI] $k='$v' bosluk/glob/kacis iceriyor — systemd (\$VAR) ve bash (nohup) bunu BOLER/GENISLETIR" ;;
    esac
  done
  if [ "$KAMERA_KOPRU" = 1 ] && [ "$KAMERA_KOPRU_BIND" != 127.0.0.1 ]; then
    echo "[UYARI] KAMERA LAN'A ACIK: bind=$KAMERA_KOPRU_BIND port=$KAMERA_KOPRU_PORT — video SiK'e GIRMEZ; TCP portunu yalniz YKI IP'sine ac"
  fi
}

beyan_denetle_veya_dur() {
  local e
  e="$(beyan_eksikleri)"
  if [ -n "$e" ]; then
    printf '%s\n' "$e" | sed 's/^/[EKSIK] /' >&2
    hata "beyan eksik — HICBIR SEY BASLATILMADI (once --kuru)"
  fi
}

# Kurulu kopyadaki NAVITAS .py dosyalari (ExecStart'tan turetilir; cogullayici haric)
kurulu_py_dosyalari() {
  local b k y
  for b in $(birimler); do
    [ "$b" != navitas-cogullayici ] || continue
    k="$(exec_start "$b")"
    y="$(py_yolu "$k")"
    [ -n "$y" ] || hata "$b: ExecStart'ta NAVITAS .py yok"
    printf '%s %s\n' "$b" "$y"
  done
}

# ── Isaretli gosterici (T228) denetimi ─────────────────────────────────────────
# T227 destegi METIN denetimi: rpi_inference argparse'i tirnakli '--isaretli-yayin' bayragini
# tanimliyor mu. Tanimlamiyorsa bayrak VERILEMEZ: argparse cikis 2 -> Restart=always cokme
# dongusu. NEDEN pipe'siz grep: `set -o pipefail` altinda `tr | grep -q` erken cikinca tr'nin
# SIGPIPE'i (141) bulunan eslesmeyi "yok" gosterirdi.
isaretli_destek_var() { [ -n "$1" ] && [ -f "$1" ] && grep -Eq "[\"']--isaretli-yayin[\"']" "$1"; }

gosterici_denetimi() {  # --kuru bolumu (stdout); kuru() buradaki [YOK] satirlarini sayar
  local komut kip_dosyasi rpi_kurulu
  if [ "$GOSTERICI_KIP" = kapali ]; then
    echo "## gosterici (T228): GOSTERICI_KIP=kapali — rpi_inference'a --isaretli-yayin VERILMEZ, gosterici kalkmaz (mevcut davranis)"
    return 0
  fi
  komut="$KAMERA_PYTHON $NAVITAS_KOK/scripts/$GOSTERICI_BETIK --kip $GOSTERICI_KIP --kaynak http://$ISARETLI_YAYIN"
  echo "## gosterici (T228 · GOSTERICI_KIP=$GOSTERICI_KIP) — KARAR URETMEZ; bu betik gostericiyi KALDIRMAZ"
  echo "isaretli yayin: rpi_inference --isaretli-yayin $ISARETLI_YAYIN (RPI_EK_ARGS; T227)"
  echo "komut: $komut"
  case "$GOSTERICI_KIP" in
    x11)
      echo "baslatan: X11 otomatik oturum + ~/.config/autostart/navitas-isaretli-gosterici.desktop (gosterici/GOSTERICI_KURULUM.md)"
      kip_dosyasi="gosterici/navitas-isaretli-gosterici.desktop" ;;
    drm)
      echo "baslatan: navitas-isaretli-gosterici-drm.service — ELLE etkinlestirilir, gdm DURUR (gosterici/GOSTERICI_KURULUM.md)"
      echo "[UYARI] nvidia-drm yuklenip gosterici CALISMAZSA Argus (nvarguscamerasrc) ~3 fps'e duser — DRM ya surekli calisir ya hic acilmaz"
      kip_dosyasi="gosterici/navitas-isaretli-gosterici-drm.service" ;;
    rtsp)
      echo "baslatan: elle (YEDEK): $komut --jetson-ip <JETSON_IP> -> rtsp://<JETSON_IP>:8554/isaretli (oneri 192.168.144.30; .11/.12/.20/.25 YASAK)"
      kip_dosyasi="gosterici/GOSTERICI_KURULUM.md" ;;
  esac
  if [ -f "$PAKET_DIZIN/kod/$GOSTERICI_BETIK" ]; then echo "[VAR] paket kod/$GOSTERICI_BETIK"
  else echo "[YOK] paket kod/$GOSTERICI_BETIK <- scripts/jetson_paket_hazirla.py KOPYALAR"; fi
  if [ -f "$PAKET_DIZIN/$kip_dosyasi" ]; then echo "[VAR] paket $kip_dosyasi"
  else echo "[YOK] paket $kip_dosyasi"; fi
  if isaretli_destek_var "$PAKET_DIZIN/kod/rpi_inference.py"; then echo "[VAR] paket rpi_inference --isaretli-yayin (T227)"
  else echo "[YOK] paket rpi_inference --isaretli-yayin (T227) <- bayrak tanimli degil: rpi_inference argparse ile COKER (cikis 2, Restart dongusu); T227 birlesene dek GOSTERICI_KIP=kapali"; fi
  if [ -f "$NAVITAS_KOK/scripts/$GOSTERICI_BETIK" ]; then echo "[VAR] kurulu $NAVITAS_KOK/scripts/$GOSTERICI_BETIK"
  else echo "[YOK] kurulu $NAVITAS_KOK/scripts/$GOSTERICI_BETIK <- JETSON_KILAVUZ §2 (cp kod/$GOSTERICI_BETIK ~/navitas/scripts/)"; fi
  rpi_kurulu="$(py_yolu "$(exec_start navitas-rpi-inference)")"
  if isaretli_destek_var "$rpi_kurulu"; then echo "[VAR] kurulu rpi_inference --isaretli-yayin (T227)"
  else echo "[YOK] kurulu rpi_inference --isaretli-yayin (T227) <- ${rpi_kurulu:-rpi_inference.py} bayragi tanimiyor"; fi
}

dosya_denetle() {  # kurulu kopyada kullanici, dosyalar ve cihazlar var mi? (kuru kipte CAGRILMAZ)
  local b y liste
  # NEDEN once kullanici (D-405): yanlis User= ile kurulan birimler 217/USER ile sonsuz
  # restart dongusune girer; burada durmak o donguden ucuzdur.
  id -u "$SERVIS_KULLANICI" >/dev/null 2>&1 \
    || hata "servis kullanicisi yok: $SERVIS_KULLANICI (SERVIS_KULLANICI ile ez; birimler User=$SERVIS_KULLANICI ile kosar)"
  [ -x "$PYTHON3" ] || hata "yorumlayici yok: $PYTHON3"
  yorumlayici_modulleri_var \
    || hata "$PYTHON3 '$PYTHON3_MODULLERI' import EDEMIYOR — servis cokme dongusune girerdi; PYTHON3 ile venv yorumlayicisini ver (ONARIM-10)"
  [ -e "$PIXHAWK_SERI" ] || hata "Pixhawk seri cihazi yok: $PIXHAWK_SERI (PIXHAWK_SERI ile ez)"
  if [ "$KIP" = sik ]; then [ -e "$SIK_SERI" ] || hata "SiK seri cihazi yok: $SIK_SERI (SIK_SERI ile ez)"; fi
  if [ "$KIP" = ikili ] && [ ! -e "$SIK_SERI" ]; then
    echo "UYARI: KIP=ikili ama SiK seri yok ($SIK_SERI) — hub LAN yoluyla kalkar, seriyi arka planda dener"
  fi
  if [ "$KAMERA_KOPRU" = 1 ]; then
    [ -x "$KAMERA_PYTHON" ] \
      || hata "kopru yorumlayicisi yok: $KAMERA_PYTHON (SISTEM Python; KAMERA_PYTHON ile ez)"
  fi
  mavproxy_var \
    || hata "mavproxy.py yok ($MAVPROXY_PATH; pip3 install MAVProxy) — cogullayicisiz MAVLink isi BASLAMAZ (CONTRACTS §7.4)"
  # once degiskene: fonksiyon icindeki hata() ana kabugu durdursun (proses ikamesinde durdurmazdi)
  liste="$(kurulu_py_dosyalari)"
  while read -r b y; do
    [ -f "$y" ] || hata "$b: $y yok (JETSON_KILAVUZ §2: cp kod/... $NAVITAS_KOK/{codes,comms,scripts}; seri_hub icin comms/seri_hub.py; kamera_koprusu icin scripts/kamera_koprusu.py)"
  done <<< "$liste"
  if [ "$GOSTERICI_KIP" != kapali ]; then
    # T228 (fail-closed): --isaretli-yayin'i tanimayan rpi_inference argparse ile olur (cikis 2) ve
    # Restart=always onu cokme dongusune sokar — birimleri kurmadan / baslatmadan DUR.
    y="$(py_yolu "$(exec_start navitas-rpi-inference)")"
    isaretli_destek_var "$y" \
      || hata "GOSTERICI_KIP=$GOSTERICI_KIP: kurulu ${y:-rpi_inference.py} --isaretli-yayin TANIMIYOR (T227 yok) — argparse cikis 2 + Restart dongusu olurdu; GOSTERICI_KIP=kapali ya da T227'li paket"
  fi
}

# ── --kuru ────────────────────────────────────────────────────────────────────
kuru() {
  local b y e u g liste cr_isaret="" yok=0 kod=0
  # K8 kilidi: CR korumasi dali kostuysa basligi isaretle (test bunu assert eder)
  if [ -n "$CR_KOPYA" ]; then cr_isaret=" · (CR'siz kopya: $CR_KOPYA)"; fi
  echo "# jetson_baslat.sh --kuru · KIP=$KIP · HICBIR SEY BASLATILMADI$cr_isaret"
  echo "## $ENV_DOSYA (yazilacak icerik)"
  env_icerik
  echo "## birimler (ExecStart, degiskenler yerine konmus — systemd ve --dogrudan AYNEN bunu kosar)"
  for b in $(birimler); do echo "$b.service: $(exec_start "$b")"; done
  sozlesme_denetle
  echo "## paket denetimi ($PAKET_DIZIN/kod)"
  for b in $(birimler); do
    if [ "$b" = navitas-cogullayici ]; then
      if mavproxy_var; then echo "[VAR] mavproxy.py (PATH)"
      else echo "[YOK] mavproxy.py (PATH) <- Jetson'da: pip3 install MAVProxy"; yok=$((yok + 1)); fi
      continue
    fi
    y="$(py_yolu "$(exec_start "$b")")"
    y="${y##*/}"
    if [ -f "$PAKET_DIZIN/kod/$y" ]; then echo "[VAR] $y"
    else echo "[YOK] $y <- UYARI: paket tasimiyor (scripts/jetson_paket_hazirla.py KOPYALAR)"; yok=$((yok + 1)); fi
  done
  # NEDEN (D-405, curutucu "--kuru [YOK] iken tamam" bulgusu): --kur dosya_denetle'de
  # duracaksa --kuru bunu SIMDI soyler — salt okunur, ucuz; kuru rapor yalan soylemez.
  echo "## ana makine denetimi (gercek kosumun dosya_denetle'de duracagi yerler; salt okunur)"
  if id -u "$SERVIS_KULLANICI" >/dev/null 2>&1; then echo "[VAR] kullanici $SERVIS_KULLANICI (birimlerde User=)"
  else echo "[YOK] kullanici $SERVIS_KULLANICI <- SERVIS_KULLANICI ile ez (JETSON_KILAVUZ §2 ~/navitas sahibi)"; yok=$((yok + 1)); fi
  if [ -x "$PYTHON3" ]; then echo "[VAR] yorumlayici $PYTHON3"
  else echo "[YOK] yorumlayici $PYTHON3 <- PYTHON3 ile ez"; yok=$((yok + 1)); fi
  if [ -x "$PYTHON3" ]; then
    if yorumlayici_modulleri_var; then echo "[VAR] modul $PYTHON3 import $PYTHON3_MODULLERI"
    else echo "[YOK] modul $PYTHON3 import $PYTHON3_MODULLERI <- bu yorumlayicida yok; Jetson'da PYTHON3=/home/$SERVIS_KULLANICI/venv312/bin/python ile ez (ONARIM-10)"; yok=$((yok + 1)); fi
  fi
  if [ "$KAMERA_KOPRU" = 1 ]; then
    if [ -x "$KAMERA_PYTHON" ]; then echo "[VAR] kopru yorumlayicisi $KAMERA_PYTHON"
    else echo "[YOK] kopru yorumlayicisi $KAMERA_PYTHON <- KAMERA_PYTHON ile ez (GStreamer'li sistem Python)"; yok=$((yok + 1)); fi
  fi
  if [ -e "$PIXHAWK_SERI" ]; then echo "[VAR] Pixhawk seri $PIXHAWK_SERI"
  else echo "[YOK] Pixhawk seri $PIXHAWK_SERI <- kablo takili mi? PIXHAWK_SERI ile ez"; yok=$((yok + 1)); fi
  if [ "$KIP" = sik ]; then
    if [ -e "$SIK_SERI" ]; then echo "[VAR] SiK seri $SIK_SERI"
    else echo "[YOK] SiK seri $SIK_SERI <- SIK_SERI ile ez"; yok=$((yok + 1)); fi
  elif [ "$KIP" = ikili ] && [ ! -e "$SIK_SERI" ]; then
    echo "UYARI: KIP=ikili SiK seri yok ($SIK_SERI) — yalniz LAN yolu calisir"
  fi
  if [ "$KIP" = ikili ] && [ -n "$YKS_ESLESME" ]; then
    if [ -r "$YKS_ESLESME" ]; then echo "[VAR] YKS eslesme $YKS_ESLESME"
    else echo "[YOK] YKS eslesme $YKS_ESLESME <- scripts/yks_eslestir.py esle ... (YKS'deki dosya)"; yok=$((yok + 1)); fi
  fi
  liste="$(kurulu_py_dosyalari)"
  while read -r b y; do
    if [ -f "$y" ]; then echo "[VAR] kurulu $y"
    else echo "[YOK] kurulu $y <- $b: JETSON_KILAVUZ §2 (cp kod/... $NAVITAS_KOK/{codes,comms,scripts})"; yok=$((yok + 1)); fi
  done <<< "$liste"
  # T228: gosterici bolumu (kapaliyken tek satir). [YOK] satirlari toplam eksige eklenir:
  # GOSTERICI_KIP acik ama T227 yoksa --kur dosya_denetle'de duracaktir — kuru bunu SIMDI soyler.
  g="$(gosterici_denetimi)"
  printf '%s\n' "$g"
  yok=$((yok + $(printf '%s\n' "$g" | grep -c '^\[YOK\]' || true)))
  echo "## beyan denetimi"
  u="$(deger_uyarilari)"
  if [ -n "$u" ]; then printf '%s\n' "$u"; fi
  e="$(beyan_eksikleri)"
  if [ -n "$e" ]; then
    printf '%s\n' "$e" | sed 's/^/[EKSIK] /'
  else
    echo "[TAM] beyanlar tam"
  fi
  if [ -n "$e" ] || [ "$yok" -gt 0 ]; then
    echo "KURU SONUC: eksik (beyan: $( [ -n "$e" ] && echo eksik || echo tam ) · [YOK]: $yok) — gercek kosum DURUR (cikis 3)"
    kod=3
  else
    echo "KURU SONUC: tamam — kurmak icin: sudo -E bash $BETIK_YOLU"
  fi
  return $kod
}

# ── systemd kurulumu ──────────────────────────────────────────────────────────
birimleri_kur() {  # env dosyasi + birim dosyalari + daemon-reload (baslatmaz)
  local b
  [ "$(id -u)" -eq 0 ] || hata "root gerekli: sudo -E bash $BETIK_YOLU ${1:-}"
  command -v systemctl >/dev/null 2>&1 || hata "systemctl yok — --dogrudan kullan"
  beyan_denetle_veya_dur
  sozlesme_denetle
  dosya_denetle
  mkdir -p "$LOG_DIZIN/mavproxy"
  chown -R "$SERVIS_KULLANICI": "$LOG_DIZIN" 2>/dev/null || true
  env_icerik > "$ENV_DOSYA"
  chmod 644 "$ENV_DOSYA"
  echo "[YAZILDI] $ENV_DOSYA"
  for b in $TUM_BIRIMLER; do
    # CR'siz kopyala (USB/Windows kopyasi CR tasiyabilir); ezilmis kok/python/env/kullanici
    # yollarini isle. NEDEN User= ve ~/.local/bin (D-405): birimde SABIT kalinca
    # SERVIS_KULLANICI ezilse de birim navitas kullanicisini arar (217/USER dongusu).
    tr -d '\r' < "$(birim_dosyasi "$b")" \
      | sed -e "s#$KOK_VARSAYILAN#$NAVITAS_KOK#g" \
            -e "s#$PYTHON3_VARSAYILAN#$PYTHON3#g" \
            -e "s#^EnvironmentFile=$ENV_DOSYA_VARSAYILAN\$#EnvironmentFile=$ENV_DOSYA#" \
            -e "s#^User=$KULLANICI_VARSAYILAN\$#User=$SERVIS_KULLANICI#" \
            -e "s#$MAVPROXY_BIN_VARSAYILAN#$MAVPROXY_BIN#g" \
      > "$SYSTEMD_DIZIN/$b.service"
    echo "[KURULDU] $SYSTEMD_DIZIN/$b.service"
  done
  systemctl daemon-reload
  if ! hub_kipi; then systemctl disable --now navitas-seri-hub.service >/dev/null 2>&1 || true; fi
  if [ "$KAMERA_KOPRU" != 1 ]; then systemctl disable --now navitas-kamera-koprusu.service >/dev/null 2>&1 || true; fi
}

birim_listesi() { birimler | sed 's/$/.service/' | tr '\n' ' '; }

# NEDEN enable + restart, `enable --now` DEGIL (D-405, curutucu restart bulgusu):
# `start` aktif birimde no-op'tur — beyan (YKS_IP, FOV...) degisip --kur yeniden
# kosuldugunda env dosyasi yenilenir ama surec ESKI argumanlarla surerdi.
# restart daemon-reload'dan SONRA: yeni birim metni ve env dosyasi okunur.
etkinlestir_ve_yeniden_baslat() {  # $@: birim.service ...
  systemctl enable "$@"
  systemctl restart "$@"
}

kur_systemd() {
  birimleri_kur ""
  # shellcheck disable=SC2046
  etkinlestir_ve_yeniden_baslat $(birim_listesi)
  sleep 2
  durum
  echo "thazirlik (bu betik): ${SECONDS} s · loglar: journalctl -u navitas-<birim> -f"
}

# ONARIM-02 (2026-09-17): MAVProxy baglaninca once TUM parametreleri indirir; TELEM2 @57600'de
# 1025 parametre ~42 s surdu ve bu surede konum/durum akislari esigin altinda kaldi -> 0/3
# (JETSON_DEVIR_20260915.md §9, D-491 §3). Indirme bitince "Saved N parameters to
# <state-basedir>/mav.parm" yazilir (results/jetson_20260915/jetson_tmp_loglari/
# navitas-mavproxy-telem2.log:26). Kapi bu dosyanin cogullayici yeniden baslatildiktan SONRA
# yazilmasini bekler. Tavan asilirsa yine olcer: hukmu kapi verir (fail-closed), bekleme degil.
PARAM_BEKLE_TAVAN_S="${PARAM_BEKLE_TAVAN_S:-90}"
param_indirme_bekle() {  # $1: cogullayici restart'indan ONCEKI epoch saniye
  local bas="$1" parm="$LOG_DIZIN/mavproxy/mav.parm" gecen_s=0
  while [ "$gecen_s" -lt "$PARAM_BEKLE_TAVAN_S" ]; do
    if [ -f "$parm" ] && [ "$(stat -c %Y "$parm" 2>/dev/null || echo 0)" -ge "$bas" ]; then
      echo "[PARAM] indirme bitti (${gecen_s} s): $parm"
      return 0
    fi
    sleep 1
    gecen_s=$((gecen_s + 1))
  done
  echo "UYARI: ${PARAM_BEKLE_TAVAN_S} s icinde parametre indirmesi bitmedi ($parm yazilmadi) — kapi yine de olcer"
}

kapi() {  # FAZ_B_GUN_PLANI §1: cogullayici tek basina + 3 ucta AYNI ANDA mavlink_dogrula; 3/3 GECTI -> tuketiciler
  local b d uc port rc kapi_dizin bas gecen=0 beklenen="${#MAV_UCLAR[@]}"
  birimleri_kur "--kapi"
  d="$NAVITAS_KOK/scripts/mavlink_dogrula.py"
  [ -f "$d" ] || hata "$d yok — kapi araci kurulu degil; paket TASIMIYOR, depodan kopyala: scripts/mavlink_dogrula.py -> $NAVITAS_KOK/scripts/"
  # Onceki kurulumdan kalkmis tuketiciler 1455N uclarini tutar; kapi araci ayni ucu dinler.
  for b in $TUKETICILER; do systemctl stop "$b.service" >/dev/null 2>&1 || true; done
  # restart: PIXHAWK_SERI/BAUD degismis olabilir (D-405)
  bas="$(date +%s)"
  etkinlestir_ve_yeniden_baslat navitas-cogullayici.service
  if hub_kipi; then etkinlestir_ve_yeniden_baslat navitas-seri-hub.service; fi
  if [ "$KAMERA_KOPRU" = 1 ]; then
    etkinlestir_ve_yeniden_baslat navitas-kamera-koprusu.service
  fi
  param_indirme_bekle "$bas"   # ONARIM-02: eski sabit `sleep 3` indirme bitmeden olcuyordu
  # NEDEN paralel (D-405, curutucu kapi bulgusu): CONTRACTS §7.4 / FAZ_B_GUN_PLANI §1
  # "uc uc AYNI ANDA acikken GECTI" der; sirali kosum bunu sinamaz ve thazirlik'e
  # +22..+52 s ekler (§6.2: 30 s = 1 puan). rc dosyalari: eski kosumdan kalan
  # dosya "gecti" sayilmasin diye ONCE silinir; rc yoksa DUSTU (fail-closed).
  kapi_dizin="$LOG_DIZIN/kapi"
  mkdir -p "$kapi_dizin"
  rm -f "$kapi_dizin"/*.rc "$kapi_dizin"/*.log
  for uc in "${MAV_UCLAR[@]}"; do
    port="${uc##*:}"
    (
      rc=0
      sudo -u "$SERVIS_KULLANICI" "$PYTHON3" "$d" --mavlink "$uc" --sysid "$SYSID" > "$kapi_dizin/$port.log" 2>&1 || rc=$?
      echo "$rc" > "$kapi_dizin/$port.rc"
    ) &
  done
  wait
  for uc in "${MAV_UCLAR[@]}"; do
    port="${uc##*:}"
    echo "## kapi: $uc (log: $kapi_dizin/$port.log)"
    cat "$kapi_dizin/$port.log" 2>/dev/null || true
    rc="$(cat "$kapi_dizin/$port.rc" 2>/dev/null || echo "rc-yok")"
    if [ "$rc" = 0 ]; then
      echo "[GECTI] $uc"; gecen=$((gecen + 1))
    else
      echo "[DUSTU] $uc (rc=$rc)"
    fi
  done
  [ "$gecen" -eq "$beklenen" ] || hata "kapi $gecen/$beklenen — tuketiciler BASLATILMADI (CONTRACTS §7.4: cogullayici dogrulanmadan MAVLink isi baslamaz)"
  # shellcheck disable=SC2046
  etkinlestir_ve_yeniden_baslat $(for b in $TUKETICILER; do printf '%s.service ' "$b"; done)
  sleep 2
  durum
  echo "thazirlik (bu betik, kapi dahil): ${SECONDS} s"
}

# ── systemd'siz (prova) ───────────────────────────────────────────────────────
dogrudan() {
  local b k
  beyan_denetle_veya_dur
  sozlesme_denetle
  dosya_denetle
  mkdir -p "$LOG_DIZIN/mavproxy"
  for b in $(birimler); do
    k="$(exec_start "$b")"
    echo "[BASLAT] $b: $k"
    (
      cd "$NAVITAS_KOK" || exit 1
      export PYTHONUNBUFFERED=1 PATH="$MAVPROXY_PATH:$PATH"
      # set -f (D-405): tirnaksiz $k bosluktan bolunmeli ama GLOB genislememeli —
      # KAMERA='*' cwd=NAVITAS_KOK'ta codes comms ... olarak aciliyordu (--kuru ile ayrisma)
      set -f
      # shellcheck disable=SC2086
      nohup $k > "$LOG_DIZIN/$b.log" 2>&1 &
      echo $! > "$LOG_DIZIN/$b.pid"     # nohup exec'ler: pid = surecin kendisi
    )
    case "$b" in navitas-cogullayici|navitas-seri-hub) sleep 3 ;; navitas-kamera-koprusu) sleep 1 ;; esac   # seri portu / HTTP ucunu acsin
  done
  echo "UYARI: --dogrudan kipinde GOZCU YOK — olen surec kendi kalkmaz (Restart=always yalniz systemd). Loglar: $LOG_DIZIN"
}

durdur() {
  local b
  if command -v systemctl >/dev/null 2>&1 && [ "$(id -u)" -eq 0 ]; then
    for b in $TUM_BIRIMLER; do
      if systemctl disable --now "$b.service" >/dev/null 2>&1; then echo "[DURDU] $b.service"; fi
    done
  fi
  for b in $TUM_BIRIMLER; do
    if [ -f "$LOG_DIZIN/$b.pid" ]; then
      if kill "$(cat "$LOG_DIZIN/$b.pid")" 2>/dev/null; then echo "[OLDURULDU] $b (nohup)"; fi
      rm -f "$LOG_DIZIN/$b.pid"
    fi
  done
}

durum() {
  local b a n
  if ! command -v systemctl >/dev/null 2>&1; then echo "systemctl yok (--dogrudan loglari: $LOG_DIZIN)"; return 0; fi
  for b in $(birimler); do
    a="$(systemctl is-active "$b.service" 2>/dev/null || true)"
    n="$(systemctl show -p NRestarts --value "$b.service" 2>/dev/null || echo '?')"
    echo "[${a:-yok}] $b.service  yeniden-baslatma=$n"
  done
  echo "(yeniden-baslatma sayisi ARTIYORSA surec cokme dongusunde: journalctl -u <birim> -n 50)"
}

yardim() { sed -n '/^# KULLANIM/,/^# CIKIS KODLARI/p' "$0" | sed 's/^# \{0,1\}//'; }

case "${1:-}" in
  --kuru)      kuru || exit $? ;;
  --kapi)      kapi ;;
  --dogrudan)  dogrudan ;;
  --durdur)    durdur ;;
  --durum)     durum ;;
  ""|--kur)    kur_systemd ;;
  -h|--help|--yardim) yardim ;;
  *) hata "bilinmeyen secenek: $1 (--kuru | --kapi | --dogrudan | --durdur | --durum | --kur)" ;;
esac
