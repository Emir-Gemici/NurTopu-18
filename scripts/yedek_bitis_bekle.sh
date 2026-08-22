#!/usr/bin/env bash
# T140 — YEDEK BITISINI BEKLE. Bitince cikar; cagirana bildirim gider.
#
# NEDEN: kullanici "bitince haber ver" dedi. Surekli yoklamak yerine, yedek
# bitene kadar BLOKLAYAN tek bir is baslatilir; o is bittiginde ustabasi
# bildirim alir ve raporlar.
#
# BITIS OLCUTU IKI YONLU (biri yeterli degil):
#   a) gunlukte "TUM KADEMELER BITTI" satiri  -> betik kendini bitirdi
#   b) rclone + yedek betigi SURECI YOK       -> beklenmedik olum
# (b) de bildirilir; sessizce "bitti" denmez (D-267: cikis kodu KANIT DEGIL).
set -u
KOK="O:/navitas"
GUNLUK="$KOK/results/yedek_drive_log.txt"
ILERLEME="$KOK/results/yedek_ilerleme.jsonl"
ARALIK=600     # 10 dakikada bir ilerleme kaydi

RCLONE="$(command -v rclone || true)"
[ -z "$RCLONE" ] && RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"

uzak () { "$RCLONE" size drive:navitas_yedek --json 2>/dev/null | grep -o '"bytes":[0-9]*' | cut -d: -f2; }
surec_var () {
  powershell -NoProfile -ExecutionPolicy Bypass -File "$KOK/scripts/yedek_surec_yonet.ps1" -Kip durum 2>/dev/null \
    | tr -d '\r' | grep -c "rclone       : [1-9]"
}

bas=$(date +%s); bas_b="$(uzak)"; bas_b="${bas_b:-0}"
echo "[$(date +%H:%M:%S)] BEKLEYICI basladi · uzak $((bas_b / 1048576)) MB"
yok_sayaci=0
while true; do
  sleep "$ARALIK"
  b="$(uzak)"
  if [ -n "$b" ]; then
    gecen=$(( $(date +%s) - bas ))
    hiz=0; [ "$gecen" -gt 0 ] && hiz=$(( (b - bas_b) / gecen ))
    kademe="$(grep -o 'KADEME: [a-zA-Z0-9_/-]*' "$GUNLUK" 2>/dev/null | tail -1 | cut -d' ' -f2)"
    printf '{"t":"%s","uzak":%s,"kademe":"%s","ort_Bps":%s}\n' \
      "$(date +%H:%M:%S)" "$b" "${kademe:-?}" "$hiz" >> "$ILERLEME"
  fi
  if grep -q "TUM KADEMELER BITTI" "$GUNLUK" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] YEDEK BITTI (gunlukte 'TUM KADEMELER BITTI')"
    echo "son uzak: $(( ${b:-0} / 1048576 )) MB"
    exit 0
  fi
  if [ "$(surec_var)" = "0" ]; then
    yok_sayaci=$((yok_sayaci + 1))
    if [ "$yok_sayaci" -ge 3 ]; then
      echo "[$(date +%H:%M:%S)] 🔴 SUREC YOK ve gunlukte BITTI satiri YOK -> BEKLENMEDIK OLUM"
      echo "son uzak: $(( ${b:-0} / 1048576 )) MB · son kademe: $(grep -o 'KADEME: .*' "$GUNLUK" | tail -1)"
      exit 3
    fi
  else
    yok_sayaci=0
  fi
done
