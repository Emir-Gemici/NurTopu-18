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
#
# KULLANIM
#   bash jetson_baslat.sh --kuru        HICBIR SEY baslatmaz; kosacagi komutlari basar
#   sudo -E bash jetson_baslat.sh       systemd birimlerini kurar (enable --now; acilista da kalkar)
#   sudo -E bash jetson_baslat.sh --kapi  kurar, YALNIZ cogullayiciyi kaldirir, 3 ucta
#                                       mavlink_dogrula kosar; 3/3 GECTI ise tuketicileri kaldirir
#   bash jetson_baslat.sh --dogrudan    systemd'siz: nohup + log (prova/ayiklama — GOZCU YOK)
#   sudo bash jetson_baslat.sh --durdur birimleri durdurur (disable --now), nohup pid'lerini oldurur
#   bash jetson_baslat.sh --durum       birim durumu + yeniden-baslatma sayisi (cokme dongusu GORUNUR)
#   Degiskenler ortamdan ezilir:   KIP=sik FOV=78 bash jetson_baslat.sh --kuru
#
# CIKIS KODLARI: 0 tamam · 1 hata (fail-closed, hicbir sey baslatilmadi) ·
#                3 --kuru'da beyan eksik (gercek kosum DURURDU)
# =============================================================================
# CRLF KORUMASI — ILK KOMUT OLMALI. Windows calisma agaci core.autocrlf=true ile
# CRLF'tir (olculdu: `git ls-files --eol` -> w/crlf); USB'ye kopyalanan betik CR
# tasir ve bash "$'\r': command not found" der. CR gorulurse betik CR'siz
# kopyasiyla yeniden calisir (bu satirin kendi CR'i satir sonu yorumunda kalir).
if grep -q $'\r' "$0" 2>/dev/null; then _cr="$(mktemp)"; tr -d '\r' < "$0" > "$_cr"; NAVITAS_PAKET_DIZIN="${NAVITAS_PAKET_DIZIN:-$(cd "$(dirname "$0")" && pwd)}" NAVITAS_CR_KOPYA=1 exec bash "$_cr" "$@"; fi # CRLF
set -euo pipefail
if [ "${NAVITAS_CR_KOPYA:-}" = 1 ]; then trap 'rm -f "$0"' EXIT; fi

PAKET_DIZIN="${NAVITAS_PAKET_DIZIN:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
BIRIM_DIZIN="$PAKET_DIZIN/systemd"

# ── Beyan degiskenleri (ortamdan ezilir) ─────────────────────────────────────
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
UB_REFERANS="${UB_REFERANS:-}"   # LAT,LON — IHA-UB kose referansi (T162); bos = alan ihlali denetimi YOK
# iha_inis_yayinci --kanit-timeout: sartname §6.2 IHA gorev suresi
# (karar_sozlesmesi.SARTNAME_IHA_GOREV_SURESI_S = 15*60; SAHA_RUNBOOK §3). Test kilitler.
KANIT_TIMEOUT="${KANIT_TIMEOUT:-900}"
NAVITAS_KOK="${NAVITAS_KOK:-/home/navitas/navitas}"   # JETSON_KILAVUZ §2 kurulum koku
PYTHON3="${PYTHON3:-/usr/bin/python3}"
ENV_DOSYA="${ENV_DOSYA:-/etc/navitas.env}"
SYSTEMD_DIZIN="${SYSTEMD_DIZIN:-/etc/systemd/system}"
LOG_DIZIN="${LOG_DIZIN:-$NAVITAS_KOK/results/jetson_log}"
SERVIS_KULLANICI="${SERVIS_KULLANICI:-navitas}"

# Birim dosyalarindaki sabit yollar; NAVITAS_KOK/PYTHON3 ezildiyse kurulumda degistirilir.
KOK_VARSAYILAN="/home/navitas/navitas"
PYTHON3_VARSAYILAN="/usr/bin/python3"

# ── CONTRACTS §7.4 uclari — TEK KAYNAK (burada + systemd/*.service) ───────────
MAV_UC_RPI="udp:127.0.0.1:14550"      # rpi_inference    --mavlink (okur)
MAV_UC_INIS="udp:127.0.0.1:14551"     # iha_inis_yayinci --mavlink (okur)
MAV_UC_KOMUT="udp:127.0.0.1:14552"    # iha_komut_alici  --mavlink (yazar)
# NAVITAS protokol uclari (SAHA_RUNBOOK §1/§3 · iha_komut_alici.VARSAYILAN_BIND)
YKS_PORT=5005
IKA_PORT=5006
KOMUT_PORT=5007
SERI_HUB_DINLE="127.0.0.1:5100"                 # KIP=sik: surecler buraya yazar
SERI_HUB_TUKETICI="127.0.0.1:${KOMUT_PORT}"     # hub seri hattan geleni buraya verir

hata() { echo "HATA: $*" >&2; exit 1; }

# MAVProxy pip ile kullanici dizinine kurulur (~/.local/bin); sudo altinda secure_path
# onu gormez. Birim dosyasi (Environment=PATH=...) ile AYNI arama yolu kullanilir.
MAVPROXY_PATH="/home/$SERVIS_KULLANICI/.local/bin:/usr/local/bin:/usr/bin:/bin"
mavproxy_var() { PATH="$MAVPROXY_PATH:$PATH" command -v mavproxy.py >/dev/null 2>&1; }

# ── KIP'e gore tuketici argumanlari — birimler bunlari $..._ARGS olarak okur ───
RPI_EK_ARGS=""
if [ -n "$FOV" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --fov $FOV"; fi
if [ -n "$ODAK" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --odak $ODAK"; fi
if [ -n "$SENARYO" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --senaryo $SENARYO"; fi
if [ -n "$KAMERA" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --kaynak $KAMERA"; fi
if [ -n "$UB_REFERANS" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --ub-referans $UB_REFERANS"; fi
RPI_EK_ARGS="${RPI_EK_ARGS# }"
case "$KIP" in
  udp)
    RPI_TELSIZ_ARGS="--yks-hedef ${YKS_IP}:${YKS_PORT} --ika-hedef ${IKA_IP}:${IKA_PORT}"
    INIS_TELSIZ_ARGS="--yks ${YKS_IP}:${YKS_PORT} --ika ${IKA_IP}:${IKA_PORT}"
    KOMUT_TELSIZ_ARGS="--bind 0.0.0.0:${KOMUT_PORT}"
    ;;
  sik)
    # Tek hat: her cerceve hub'a BIR kez yazilir (--telsiz-seri gibi); YKS ve IKA
    # ayni 433 MHz yayinini dinler. Seri hattan gelen ACK/CMD hub'in --tuketici
    # ucuna duser (hub tasarimi, D-403 §4b).
    RPI_TELSIZ_ARGS="--yks-hedef ${SERI_HUB_DINLE}"
    INIS_TELSIZ_ARGS="--yks ${SERI_HUB_DINLE}"
    KOMUT_TELSIZ_ARGS="--bind ${SERI_HUB_TUKETICI}"
    ;;
  *) hata "KIP='$KIP' taninmiyor (udp | sik)" ;;
esac

# /etc/navitas.env'e yazilan ve ExecStart'ta yerine konan anahtarlar
ENV_ANAHTARLAR=(NAVITAS_KOK PYTHON3 LOG_DIZIN KIP PIXHAWK_SERI PIXHAWK_BAUD SYSID
                SIK_SERI SIK_BAUD KANIT_TIMEOUT RPI_EK_ARGS RPI_TELSIZ_ARGS
                INIS_TELSIZ_ARGS KOMUT_TELSIZ_ARGS)

env_icerik() {
  local k
  for k in "${ENV_ANAHTARLAR[@]}"; do printf '%s=%s\n' "$k" "${!k}"; done
}

yerine_koy() {  # $1: metin -> ${ANAHTAR} ve $ANAHTAR yerine deger (systemd ile ayni anlam)
  local m="$1" k v
  for k in "${ENV_ANAHTARLAR[@]}"; do
    v="${!k}"
    m="${m//"\${$k}"/"$v"}"
    m="${m//"\$$k"/"$v"}"
  done
  m="${m//"$KOK_VARSAYILAN"/"$NAVITAS_KOK"}"
  m="${m//"$PYTHON3_VARSAYILAN"/"$PYTHON3"}"
  printf '%s\n' "$m"
}

# ── Birimler ──────────────────────────────────────────────────────────────────
birimler() {  # KIP'e gore, BASLATMA sirasinda
  echo navitas-cogullayici
  if [ "$KIP" = sik ]; then echo navitas-seri-hub; fi
  echo navitas-rpi-inference
  echo navitas-iha-inis-yayinci
  echo navitas-iha-komut-alici
}
TUKETICILER="navitas-rpi-inference navitas-iha-inis-yayinci navitas-iha-komut-alici"
# DURDURMA sirasi: once tuketiciler, sonra hub, en son cogullayici
TUM_BIRIMLER="$TUKETICILER navitas-seri-hub navitas-cogullayici"

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
  for uc in "$MAV_UC_RPI" "$MAV_UC_INIS" "$MAV_UC_KOMUT"; do
    case " $k " in *" --out $uc "*) ;; *) hata "navitas-cogullayici: '--out $uc' yok (CONTRACTS §7.4)" ;; esac
  done
  case " $k " in *" --master=$PIXHAWK_SERI "*) ;; *) hata "navitas-cogullayici: --master=$PIXHAWK_SERI yok" ;; esac
  tuketici_denetle navitas-rpi-inference "$MAV_UC_RPI" "--mav-sysid $SYSID"
  tuketici_denetle navitas-iha-inis-yayinci "$MAV_UC_INIS" "--sysid $SYSID"
  tuketici_denetle navitas-iha-komut-alici "$MAV_UC_KOMUT" "--sysid $SYSID"
  if [ "$KIP" = sik ]; then
    k="$(exec_start navitas-seri-hub)"
    case " $k " in *" --serial $SIK_SERI "*) ;; *) hata "navitas-seri-hub: '--serial $SIK_SERI' yok" ;; esac
    case " $k " in *" --bind $SERI_HUB_DINLE "*) ;; *) hata "navitas-seri-hub: '--bind $SERI_HUB_DINLE' yok" ;; esac
    case " $k " in *" --tuketici $SERI_HUB_TUKETICI "*) ;; *) hata "navitas-seri-hub: '--tuketici $SERI_HUB_TUKETICI' yok" ;; esac
  fi
}

beyan_eksikleri() {  # stdout: her satir bir eksik
  if [ -z "$FOV" ] && [ -z "$ODAK" ]; then
    echo "FOV ya da ODAK (kamera geometrisi; rpi_inference --mavlink icin zorunlu — BEYAN edilir, tahmin edilmez)"
  fi
  if [ -n "$FOV" ] && [ -n "$ODAK" ]; then
    echo "FOV ve ODAK birlikte verilmez (rpi_inference: karsilikli dislar)"
  fi
  if [ "$KIP" = udp ]; then
    if [ -z "$YKS_IP" ]; then echo "YKS_IP (KIP=udp: hakem ekrani hedefi, port $YKS_PORT)"; fi
    if [ -z "$IKA_IP" ]; then echo "IKA_IP (KIP=udp: IKA hedefi, port $IKA_PORT — rota + IHA_LANDED)"; fi
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

dosya_denetle() {  # kurulu kopyada dosyalar ve cihazlar var mi? (kuru kipte CAGRILMAZ)
  local b k y
  [ -x "$PYTHON3" ] || hata "yorumlayici yok: $PYTHON3"
  [ -e "$PIXHAWK_SERI" ] || hata "Pixhawk seri cihazi yok: $PIXHAWK_SERI (PIXHAWK_SERI ile ez)"
  if [ "$KIP" = sik ]; then [ -e "$SIK_SERI" ] || hata "SiK seri cihazi yok: $SIK_SERI (SIK_SERI ile ez)"; fi
  for b in $(birimler); do
    k="$(exec_start "$b")"
    if [ "$b" = navitas-cogullayici ]; then
      mavproxy_var \
        || hata "mavproxy.py yok ($MAVPROXY_PATH; pip3 install MAVProxy) — cogullayicisiz MAVLink isi BASLAMAZ (CONTRACTS §7.4)"
      continue
    fi
    y="$(py_yolu "$k")"
    [ -n "$y" ] || hata "$b: ExecStart'ta NAVITAS .py yok"
    [ -f "$y" ] || hata "$b: $y yok (JETSON_KILAVUZ §2: cp kod/... $NAVITAS_KOK/{codes,comms}; seri_hub icin comms/seri_hub.py)"
  done
}

# ── --kuru ────────────────────────────────────────────────────────────────────
kuru() {
  local b k y e kod=0
  echo "# jetson_baslat.sh --kuru · KIP=$KIP · HICBIR SEY BASLATILMADI"
  echo "## $ENV_DOSYA (yazilacak icerik)"
  env_icerik
  echo "## birimler (ExecStart, degiskenler yerine konmus — systemd ve --dogrudan AYNEN bunu kosar)"
  for b in $(birimler); do echo "$b.service: $(exec_start "$b")"; done
  sozlesme_denetle
  echo "## paket denetimi ($PAKET_DIZIN/kod)"
  for b in $(birimler); do
    if [ "$b" = navitas-cogullayici ]; then
      if mavproxy_var; then echo "[VAR] mavproxy.py (PATH)"
      else echo "[YOK] mavproxy.py (PATH) <- Jetson'da: pip3 install MAVProxy"; fi
      continue
    fi
    y="$(py_yolu "$(exec_start "$b")")"
    y="${y##*/}"
    if [ -f "$PAKET_DIZIN/kod/$y" ]; then echo "[VAR] $y"
    else echo "[YOK] $y <- UYARI: paket tasimiyor (scripts/jetson_paket_hazirla.py KOPYALAR)"; fi
  done
  echo "## beyan denetimi"
  e="$(beyan_eksikleri)"
  if [ -n "$e" ]; then
    printf '%s\n' "$e" | sed 's/^/[EKSIK] /'
    echo "KURU SONUC: beyan eksik — gercek kosum DURUR (cikis 3)"
    kod=3
  else
    echo "[TAM] beyanlar tam"
    echo "KURU SONUC: tamam — kurmak icin: sudo -E bash $PAKET_DIZIN/jetson_baslat.sh"
  fi
  return $kod
}

# ── systemd kurulumu ──────────────────────────────────────────────────────────
birimleri_kur() {  # env dosyasi + birim dosyalari + daemon-reload (baslatmaz)
  local b
  [ "$(id -u)" -eq 0 ] || hata "root gerekli: sudo -E bash $0 ${1:-}"
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
    # CR'siz kopyala (USB/Windows kopyasi CR tasiyabilir); ezilmis kok/python yolunu isle
    tr -d '\r' < "$(birim_dosyasi "$b")" \
      | sed -e "s#$KOK_VARSAYILAN#$NAVITAS_KOK#g" -e "s#$PYTHON3_VARSAYILAN#$PYTHON3#g" \
      > "$SYSTEMD_DIZIN/$b.service"
    echo "[KURULDU] $SYSTEMD_DIZIN/$b.service"
  done
  systemctl daemon-reload
  if [ "$KIP" != sik ]; then systemctl disable --now navitas-seri-hub.service >/dev/null 2>&1 || true; fi
}

birim_listesi() { birimler | sed 's/$/.service/' | tr '\n' ' '; }

kur_systemd() {
  birimleri_kur ""
  # shellcheck disable=SC2046
  systemctl enable --now $(birim_listesi)
  sleep 2
  durum
  echo "thazirlik (bu betik): ${SECONDS} s · loglar: journalctl -u navitas-<birim> -f"
}

kapi() {  # FAZ_B_GUN_PLANI §1: cogullayici tek basina + 3 ucta mavlink_dogrula; 3/3 GECTI -> tuketiciler
  local b d uc gecen=0
  birimleri_kur "--kapi"
  d="$NAVITAS_KOK/scripts/mavlink_dogrula.py"
  [ -f "$d" ] || hata "$d yok — kapi araci kurulu degil; paket TASIMIYOR, depodan kopyala: scripts/mavlink_dogrula.py -> $NAVITAS_KOK/scripts/"
  # Onceki kurulumdan kalkmis tuketiciler 1455N uclarini tutar; kapi araci ayni ucu dinler.
  for b in $TUKETICILER; do systemctl stop "$b.service" >/dev/null 2>&1 || true; done
  systemctl enable --now navitas-cogullayici.service
  if [ "$KIP" = sik ]; then systemctl enable --now navitas-seri-hub.service; fi
  sleep 3
  for uc in "$MAV_UC_RPI" "$MAV_UC_INIS" "$MAV_UC_KOMUT"; do
    echo "## kapi: $uc"
    if sudo -u "$SERVIS_KULLANICI" "$PYTHON3" "$d" --mavlink "$uc" --sysid "$SYSID"; then
      echo "[GECTI] $uc"; gecen=$((gecen + 1))
    else
      echo "[DUSTU] $uc"
    fi
  done
  [ "$gecen" -eq 3 ] || hata "kapi $gecen/3 — tuketiciler BASLATILMADI (CONTRACTS §7.4: cogullayici dogrulanmadan MAVLink isi baslamaz)"
  # shellcheck disable=SC2086
  systemctl enable --now $(for b in $TUKETICILER; do printf '%s.service ' "$b"; done)
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
      # shellcheck disable=SC2086
      nohup $k > "$LOG_DIZIN/$b.log" 2>&1 &
      echo $! > "$LOG_DIZIN/$b.pid"     # nohup exec'ler: pid = surecin kendisi
    )
    case "$b" in navitas-cogullayici|navitas-seri-hub) sleep 3 ;; esac   # seri portu acsin
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
