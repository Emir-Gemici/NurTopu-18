#!/usr/bin/env bash
# =============================================================================
# saha_log_ayarlari.sh — Jetson'da log dayanikliligi + cevrimdisi saat (ONARIM-03)
#
# NEDEN (2026-09-17, results/jetson_20260917/LOG-DURUMU.md §5-§7):
#   * RTC pil destegi yok: nvvrs-pseq-rtc her guc dongusunde 1970'e doner; agsiz
#     acilista systemd saati 28 Temmuz 2026 tabanina (systemd ikilisinin mtime'i)
#     cekiyordu -> sahada tum log damgalari yanlis. fake-hwclock son bilinen saati
#     acilista ILERI alir (asla geri almaz), kapanista ve 10 dk'da bir diske yazar.
#   * journald varsayilani SyncIntervalSec=5min: ani guc kesilmesinde 5 dk'lik
#     servis ciktisi kaybolabilir -> 5 s. RateLimitBurst yukseltilir (cokus aninda
#     mesaj patlamasi "suppressed" olmasin). Storage=persistent acikca yazilir.
#   Bu ayarlar 17 Eylul'de Jetson'a ELLE uygulandi; bu betik yeniden kurulumda ayni
#   sonucu uretir. Paketin ana journald.conf'una dokunmaz: drop-in yazar.
#   ⚠ Kalici cozum donanimdir (CR2032 RTC pili). Gorev kaydi ayrica satir basina
#   fsync eder (rpi_inference --gorev-kaydi).
#
# KULLANIM
#   bash saha_log_ayarlari.sh --kuru   ne yapacagini basar, HICBIR SEY degistirmez
#   sudo bash saha_log_ayarlari.sh     uygular (tekrar kosmak guvenlidir)
#   ⚠ apt upgrade YAPMAZ (yasak); yalniz fake-hwclock kurulu degilse kurar.
# =============================================================================
set -euo pipefail

JOURNALD_DROPIN_DIZIN="${JOURNALD_DROPIN_DIZIN:-/etc/systemd/journald.conf.d}"
JOURNALD_DROPIN="$JOURNALD_DROPIN_DIZIN/navitas-saha.conf"
FHC_TIMER_DIZIN="${FHC_TIMER_DIZIN:-/etc/systemd/system/fake-hwclock-save.timer.d}"
FHC_TIMER_DROPIN="$FHC_TIMER_DIZIN/10dk-saha.conf"

JOURNALD_ICERIK='[Journal]
Storage=persistent
Compress=yes
SyncIntervalSec=5s
RateLimitIntervalSec=30s
RateLimitBurst=100000'

FHC_TIMER_ICERIK='[Timer]
OnCalendar=
OnCalendar=*:0/10'

kuru=0
case "${1:-}" in
  --kuru) kuru=1 ;;
  "") ;;
  *) echo "HATA: bilinmeyen secenek: $1 (--kuru)" >&2; exit 1 ;;
esac

if [ "$kuru" = 1 ]; then
  echo "[KURU] fake-hwclock kurulu degilse: apt-get install -y fake-hwclock"
  echo "[KURU] $JOURNALD_DROPIN yazilir:"; echo "$JOURNALD_ICERIK"
  echo "[KURU] $FHC_TIMER_DROPIN yazilir:"; echo "$FHC_TIMER_ICERIK"
  echo "[KURU] systemctl daemon-reload · restart systemd-journald · enable --now fake-hwclock-save.timer · fake-hwclock save"
  exit 0
fi

[ "$(id -u)" = 0 ] || { echo "HATA: root gerekir (sudo bash $0)" >&2; exit 1; }

if ! dpkg -s fake-hwclock >/dev/null 2>&1; then
  apt-get install -y fake-hwclock
fi
mkdir -p "$JOURNALD_DROPIN_DIZIN" "$FHC_TIMER_DIZIN"
printf '%s\n' "$JOURNALD_ICERIK" > "$JOURNALD_DROPIN"
printf '%s\n' "$FHC_TIMER_ICERIK" > "$FHC_TIMER_DROPIN"
systemctl daemon-reload
systemctl restart systemd-journald
systemctl enable --now fake-hwclock-save.timer >/dev/null 2>&1 || true
fake-hwclock save
echo "[TAMAM] journald: $(systemd-analyze cat-config systemd/journald.conf 2>/dev/null | grep -E '^SyncIntervalSec' | tail -1)"
echo "[TAMAM] fake-hwclock: $(cat /etc/fake-hwclock.data 2>/dev/null)"
