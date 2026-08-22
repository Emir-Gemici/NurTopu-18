#!/usr/bin/env bash
# T140 — DONMA MI HAT MI? Ince taneli ornekleme ile AYIRIR.
#
# AYIRT EDICI FIKIR:
#   HAT sinirliysa  -> her araliktaki hiz BIRBIRINE YAKIN (dar dagilim).
#   DONMA varsa     -> araliklarin bir kismi ~0, bir kismi YUKSEK (iki tepeli).
# Yani ortalama hiz ikisinde de ayni cikabilir; AYIRAN sey DAGILIMDIR.
#
# 🔴 Uzak bayta bakilir, loga DEGIL (D-267). OLCULEMEDI != 0 (D-180).
set -u
KOK="O:/navitas"
UZAK="drive:navitas_yedek"
ARALIK="${2:-20}"      # saniye
SURE="${3:-360}"       # toplam olcum suresi (sn)
CIKTI="$KOK/results/yedek_hiz_tanisi.jsonl"

RCLONE="$(command -v rclone || true)"
[ -z "$RCLONE" ] && RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
[ -z "$RCLONE" ] && { echo "rclone yok" >&2; exit 2; }

kademe="${1:-}"
if [ -z "$kademe" ]; then
  kademe="$(grep -o 'KADEME: [a-zA-Z0-9_/-]*' "$KOK/results/yedek_drive_log.txt" | tail -1 | cut -d' ' -f2)"
fi
hedef="$UZAK"; [ -n "$kademe" ] && hedef="$UZAK/$kademe"
echo "kademe: ${kademe:-TUM} · aralik ${ARALIK}sn · sure ${SURE}sn"

olc () { "$RCLONE" size "$hedef" --json 2>/dev/null | grep -o '"bytes":[0-9]*' | cut -d: -f2; }

onceki=""; onceki_t=0; n=0; sifir=0
bas=$(date +%s)
printf '' > "$CIKTI"
while [ $(( $(date +%s) - bas )) -lt "$SURE" ]; do
  t=$(date +%s); b="$(olc)"
  if [ -z "$b" ]; then
    echo "  $(date +%H:%M:%S)  OLCULEMEDI -> atlandi"
    sleep "$ARALIK"; continue
  fi
  if [ -n "$onceki" ]; then
    dt=$(( t - onceki_t )); db=$(( b - onceki ))
    [ "$dt" -le 0 ] && dt=1
    kbs=$(( db / dt / 1024 ))
    n=$((n+1)); [ "$kbs" -lt 20 ] && sifir=$((sifir+1))
    printf '{"t":"%s","bayt":%s,"dt":%s,"db":%s,"KBs":%s}\n' \
      "$(date +%H:%M:%S)" "$b" "$dt" "$db" "$kbs" >> "$CIKTI"
    printf '  %s  %8d KB/s  (%+d bayt / %ds)\n' "$(date +%H:%M:%S)" "$kbs" "$db" "$dt"
  fi
  onceki="$b"; onceki_t="$t"
  sleep "$ARALIK"
done
echo ""
echo "ornek: $n · ~sifir (<20 KB/s) olan: $sifir"
[ "$n" -gt 0 ] && echo "sifir orani: $(( sifir * 100 / n ))%"
echo "ham: $CIKTI"
