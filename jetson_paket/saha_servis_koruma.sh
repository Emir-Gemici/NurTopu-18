#!/usr/bin/env bash
# =============================================================================
# saha_servis_koruma.sh — otomatik baslayan NAVITAS servislerinin sistemi COKERTMEMESI icin
# systemd drop-in korumalari (ONARIM-10, kullanici: "oto baslatma sistemin cokmesine neden olmasin")
#
# OLCUM (17 Eyl 2026 15:08, Orin Nano 4 GB, systemd 255): rpi-inference 1,28 GB · kamera-koprusu
# 212 MB (~0,75 cekirdek JPEG) · cogullayici 56 MB · inis-yayinci 24 MB · komut-alici 24 MB;
# kullanilabilir bellek ~480 MB, swap 6,9 GB, systemd-oomd kapali.
#
# KORUMALAR (birim dosyalarina DOKUNMAZ; /etc/systemd/system/<birim>.d/navitas-koruma.conf):
#   * MemoryHigh/MemoryMax: servis tavani asarsa YALNIZ o servis yavaslar/olur, sistem degil.
#   * OOMScoreAdjust=500: bellek biterse cekirdek once NAVITAS sureclerini secer; ssh -900.
#   * Nice/CPUWeight: algi ve kopru dusuk oncelik -> ssh ve masaustu yanit verir.
#   * RestartSteps/RestartMaxDelaySec: cokme dongusu 2 s'den 60 s'ye kademeli yavaslar
#     (StartLimitIntervalSec=0 korunur: servis ASLA vazgecilmez, hands-off).
#   * kamera-koprusu nvargus-daemon'dan SONRA baslar.
#
# KULLANIM: bash saha_servis_koruma.sh --kuru | sudo bash saha_servis_koruma.sh | sudo bash saha_servis_koruma.sh --kaldir
# =============================================================================
set -euo pipefail
DIZIN="${SYSTEMD_DIZIN:-/etc/systemd/system}"
AD="navitas-koruma.conf"

ortak() {  # $1 MemoryHigh  $2 MemoryMax  $3 Nice  $4 CPUWeight
  cat <<EOF
[Service]
MemoryAccounting=yes
MemoryHigh=$1
MemoryMax=$2
OOMScoreAdjust=500
Nice=$3
CPUWeight=$4
RestartSec=2
RestartSteps=6
RestartMaxDelaySec=60
EOF
}

declare -A ICERIK
ICERIK[navitas-rpi-inference.service]="$(ortak 1800M 2200M 5 60)"
ICERIK[navitas-kamera-koprusu.service]="$(ortak 400M 600M 5 60)
[Unit]
After=nvargus-daemon.service
Wants=nvargus-daemon.service"
ICERIK[navitas-cogullayici.service]="$(ortak 200M 300M 0 100)"
ICERIK[navitas-iha-inis-yayinci.service]="$(ortak 150M 250M 0 100)"
ICERIK[navitas-iha-komut-alici.service]="$(ortak 150M 250M 0 100)"
ICERIK[navitas-seri-hub.service]="$(ortak 150M 250M 0 100)"
SSH_ICERIK="[Service]
OOMScoreAdjust=-900"

case "${1:-uygula}" in
  --kuru)
    for b in "${!ICERIK[@]}"; do echo "## $DIZIN/$b.d/$AD"; echo "${ICERIK[$b]}"; done
    echo "## $DIZIN/ssh.service.d/$AD"; echo "$SSH_ICERIK"
    exit 0 ;;
  --kaldir)
    [ "$(id -u)" = 0 ] || { echo "HATA: root gerekir"; exit 1; }
    rm -f "$DIZIN"/navitas-*.service.d/"$AD" "$DIZIN/ssh.service.d/$AD"
    systemctl daemon-reload; echo "korumalar kaldirildi (servisleri yeniden baslat)"; exit 0 ;;
  uygula) ;;
  *) echo "HATA: bilinmeyen secenek $1"; exit 1 ;;
esac
[ "$(id -u)" = 0 ] || { echo "HATA: root gerekir"; exit 1; }
for b in "${!ICERIK[@]}"; do
  mkdir -p "$DIZIN/$b.d"
  printf '%s\n' "${ICERIK[$b]}" > "$DIZIN/$b.d/$AD"
  echo "[YAZILDI] $DIZIN/$b.d/$AD"
done
mkdir -p "$DIZIN/ssh.service.d"
printf '%s\n' "$SSH_ICERIK" > "$DIZIN/ssh.service.d/$AD"
systemctl daemon-reload
for b in "${!ICERIK[@]}"; do
  if systemctl is-enabled "$b" >/dev/null 2>&1; then
    printf '%-36s MemoryMax=%s OOMScoreAdjust=%s RestartMaxDelayUSec=%s\n' "$b" \
      "$(systemctl show -p MemoryMax --value "$b")" "$(systemctl show -p OOMScoreAdjust --value "$b")" \
      "$(systemctl show -p RestartMaxDelayUSec --value "$b")"
  fi
done
echo "ssh OOMScoreAdjust=$(systemctl show -p OOMScoreAdjust --value ssh.service) (calisan ssh surecine yeniden baslatinca uygulanir)"
