#!/usr/bin/env bash
# =============================================================================
# saha_servis_sadelestir.sh — Jetson'da gorevle ilgisiz servisleri KAPATIR (ONARIM-10, madde 4)
#
# NEDEN (2026-09-17, kullanici onayi): Orin Nano 4 GB'ta masaustu + arka plan servisleri
# 1,7 GB RAM tutuyordu; otomatik apt guncelleme zamanlayicilari "apt upgrade yasak" kuralina
# aykiri calisiyordu. Silme YOK: yalniz `disable --now` (kullanici birimi icin `mask`).
# Onceki durumlar /var/lib/navitas/servis_onceki_durum_<zaman>.txt'ye yazilir; geri alma:
#   sudo bash saha_servis_sadelestir.sh --geri-al /var/lib/navitas/servis_onceki_durum_<zaman>.txt
#
# DOKUNULMAYANLAR (bilincli): gdm (monitor/gosterici), ssh, NetworkManager, systemd-networkd,
# nvargus-daemon ve tum nv*/nvidia* birimleri, fake-hwclock, snapd (firefox), cron, rsyslog,
# journald, timesyncd, udisks2, user@1000, ag-portal-giris.timer (kullanici birimi, kampus agi).
# isc-dhcp-server/dnsmasq: arayuz tanimlari bos, acilista FAILED; USB device-mode dhcpd'yi
# kendi betiginden dogrudan calistirir (/opt/nvidia/l4t-usb-device-mode) -> kapatmak zararsiz.
#
# KULLANIM: bash saha_servis_sadelestir.sh --kuru | sudo bash saha_servis_sadelestir.sh
# =============================================================================
set -uo pipefail

SERVISLER=(
  docker.service docker.socket containerd.service
  ModemManager.service bluetooth.service avahi-daemon.service avahi-daemon.socket
  kerneloops.service apport.service fwupd.service gnome-remote-desktop.service
  openvpn.service sssd.service ubiquity.service
  cloud-init-local.service cloud-init.service cloud-config.service cloud-final.service
  isc-dhcp-server.service isc-dhcp-server6.service dnsmasq.service
)
ZAMANLAYICILAR=(
  apt-daily.timer apt-daily-upgrade.timer update-notifier-download.timer
  update-notifier-motd.timer motd-news.timer ua-timer.timer apport-autoreport.timer
  fwupd-refresh.timer
)
KULLANICI="${SERVIS_KULLANICI:-n4vitas}"
KULLANICI_BIRIMLERI=(tracker-miner-fs-3.service)

kip="${1:-uygula}"
if [ "$kip" = "--kuru" ]; then
  for b in "${SERVISLER[@]}" "${ZAMANLAYICILAR[@]}"; do
    printf '%-40s enabled=%-10s active=%s\n' "$b" "$(systemctl is-enabled "$b" 2>/dev/null)" "$(systemctl is-active "$b" 2>/dev/null)"
  done
  echo "kullanici ($KULLANICI): ${KULLANICI_BIRIMLERI[*]} -> mask"
  exit 0
fi
[ "$(id -u)" = 0 ] || { echo "HATA: root gerekir"; exit 1; }

if [ "$kip" = "--geri-al" ]; then
  dosya="${2:?durum dosyasi}"
  while read -r b durum; do
    case "$durum" in enabled|static|indirect) systemctl enable "$b" >/dev/null 2>&1 && echo "[ACILDI] $b" ;; esac
  done < "$dosya"
  sudo -u "$KULLANICI" XDG_RUNTIME_DIR="/run/user/$(id -u "$KULLANICI")" systemctl --user unmask "${KULLANICI_BIRIMLERI[@]}" 2>/dev/null
  echo "geri alindi (yeniden baslatinca etkin)"
  exit 0
fi

mkdir -p /var/lib/navitas
kayit="/var/lib/navitas/servis_onceki_durum_$(date +%Y%m%d_%H%M%S).txt"
for b in "${SERVISLER[@]}" "${ZAMANLAYICILAR[@]}"; do
  echo "$b $(systemctl is-enabled "$b" 2>/dev/null || true)" >> "$kayit"
done
for b in "${SERVISLER[@]}" "${ZAMANLAYICILAR[@]}"; do
  if systemctl cat "$b" >/dev/null 2>&1; then
    systemctl disable --now "$b" >/dev/null 2>&1 && echo "[KAPATILDI] $b" || echo "[UYARI] $b kapatilamadi"
  else
    echo "[YOK] $b"
  fi
done
sudo -u "$KULLANICI" XDG_RUNTIME_DIR="/run/user/$(id -u "$KULLANICI")" systemctl --user stop "${KULLANICI_BIRIMLERI[@]}" 2>/dev/null
sudo -u "$KULLANICI" XDG_RUNTIME_DIR="/run/user/$(id -u "$KULLANICI")" systemctl --user mask "${KULLANICI_BIRIMLERI[@]}" 2>/dev/null \
  && echo "[MASKELENDI] kullanici ${KULLANICI_BIRIMLERI[*]}"
echo "onceki durum: $kayit"
