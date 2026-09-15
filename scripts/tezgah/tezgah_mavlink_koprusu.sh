#!/usr/bin/env bash
# Tezgah MAVLink koprusu: Pixhawk USB -> PC -> ag -> Jetson cogullayici.
# YALNIZ TEZGAH: ucusta Jetson-Pixhawk fiziksel hatti gerekir. Jetson tarafi uretimle ayni uclari uretir.
set -uo pipefail

JETSON="${JETSON:-n4vitas@10.21.8.7}"
JETSON_IP="${JETSON#*@}"
PIX="${PIX:-/dev/serial/by-id/usb-Holybro_Pixhawk6C_220044001451333531363238-if00}"
UZAK_PORT="${UZAK_PORT:-14555}"
YEREL_PORT="${YEREL_PORT:-14556}"
PC_LOG="${PC_LOG:-/tmp/navitas_tezgah_socat.log}"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=8 "$JETSON")

pc_baslat() {
  [ -r "$PIX" ] && [ -w "$PIX" ] || { echo "HATA: $PIX okunamiyor/yazilamiyor (dialout izni?)"; return 1; }
  pgrep -f "socat.*${PIX##*/}" >/dev/null && { echo "PC koprusu zaten calisiyor"; return 0; }
  nohup socat -d -d "OPEN:${PIX},rawer" "UDP-DATAGRAM:${JETSON_IP}:${UZAK_PORT},bind=:${YEREL_PORT}" >"$PC_LOG" 2>&1 &
  sleep 1
  pgrep -f "socat.*${PIX##*/}" >/dev/null && echo "PC koprusu BASLADI (log: $PC_LOG)" || { echo "PC koprusu BASLAMADI:"; tail -5 "$PC_LOG"; return 1; }
}

jetson_baslat() {
  "${SSH[@]}" "bash -s" <<UZAK
pgrep -f "mavproxy.py --master=udpin:0.0.0.0:${UZAK_PORT}" >/dev/null && { echo "Jetson cogullayici zaten calisiyor"; exit 0; }
nohup ~/venv312/bin/mavproxy.py --master=udpin:0.0.0.0:${UZAK_PORT} --streamrate 8 \
  --out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551 --out udp:127.0.0.1:14552 \
  --daemon --non-interactive --state-basedir /tmp/navitas-mavproxy-tezgah >/tmp/navitas-mavproxy-tezgah.log 2>&1 &
sleep 3
pgrep -f "mavproxy.py --master=udpin:0.0.0.0:${UZAK_PORT}" >/dev/null && echo "Jetson cogullayici BASLADI" || { echo "Jetson cogullayici BASLAMADI:"; tail -8 /tmp/navitas-mavproxy-tezgah.log; exit 1; }
UZAK
}

dogrula() {
  "${SSH[@]}" "bash -s" <<'UZAK'
d=~/navitas/scripts/mavlink_dogrula.py; [ -f "$d" ] || d=~/proje/github/navitas_github/scripts/mavlink_dogrula.py
k=/tmp/navitas_tezgah_kapi; rm -rf "$k"; mkdir -p "$k"
for p in 14550 14551 14552; do
  ( ~/venv312/bin/python "$d" --mavlink "udpin:127.0.0.1:$p" --sysid 1 --sure 10 >"$k/$p.log" 2>&1; echo $? >"$k/$p.rc" ) &
done
wait
g=0; for p in 14550 14551 14552; do rc=$(cat "$k/$p.rc" 2>/dev/null || echo yok); echo "--- uc $p: cikis=$rc"; tail -4 "$k/$p.log"; [ "$rc" = 0 ] && g=$((g+1)); done
echo "SONUC: $g/3 GECTI (log: $k)"
UZAK
}

durdur() {
  pkill -f "socat.*${PIX##*/}" 2>/dev/null && echo "PC koprusu durduruldu" || echo "PC koprusu calismiyordu"
  "${SSH[@]}" "pkill -f 'mavproxy.py --master=udpin:0.0.0.0:${UZAK_PORT}' && echo 'Jetson cogullayici durduruldu' || echo 'Jetson cogullayici calismiyordu'"
}

case "${1:-}" in
  baslat) pc_baslat && jetson_baslat ;;
  dogrula) dogrula ;;
  durdur) durdur ;;
  *) echo "kullanim: $0 baslat|dogrula|durdur"; exit 1 ;;
esac
