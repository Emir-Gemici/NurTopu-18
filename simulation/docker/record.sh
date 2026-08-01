#!/usr/bin/env bash
# Navitas TEKNOFEST 2026 — Konteynerli Simülasyon Video Kayıtçısı (HOST tarafı)
#
# Gazebo Classic 11'i Podman konteynerinde çalıştırır, sanal ekranda render eder,
# İHA + İKA görevini oynatır, mp4 kaydeder + hakem/model logu tutar. Host'a dokunmaz.
#
# Kullanım:
#   ./record.sh             → 3 seviye SIRAYLA (kolay→orta→zor) TEK videoda
#   ./record.sh orta        → SADECE o seviye
#   ./record.sh zor --seed 7
#   ./record.sh orta 1 --layout field   → moloz sahası düzeni (vars: clean = 3 net koridor)
#
# Çıktı: simulation/recordings/v<id>/  (navitas.mp4 + hakem_log.txt) — her çalıştırma yeni v<id>
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"               # navitas/simulation
REPO="$(dirname "$SIM")"            # navitas/  (comms/ burada)
OUTDIR="$SIM/recordings"
IMAGE="${NAVITAS_GAZEBO_IMAGE:-navitas-gazebo:11-six-scenarios}"
mkdir -p "$OUTDIR"

# Argümanlar: seviye + --seed N + süre modu (1/0) + --layout + --map 1..5 (gerçekçi harita)
SEED=""; SINGLE=""; LEVELS="kolay orta zor"; RT=0; LAYOUT=""; MAP=""; PROFILE=baseline
while [ $# -gt 0 ]; do
    case "$1" in
        kolay|orta|zor) SINGLE="$1"; LEVELS="$1" ;;
        0|1) RT="$1" ;;                          # süre modu: 1=gerçekçi, 0=süresiz
        --realtime) RT="${2:-0}"; shift ;;
        --realtime=*) RT="${1#--realtime=}" ;;
        --seed) SEED="${2:-}"; shift ;;
        --seed=*) SEED="${1#--seed=}" ;;
        --layout) LAYOUT="${2:-field}"; shift ;; # field=gerçekçi saha (vars.), clean=seyrek
        --layout=*) LAYOUT="${1#--layout=}" ;;
        --map) MAP="${2:-1}"; shift ;;           # gerçekçi harita no (1-5)
        --map=*) MAP="${1#--map=}" ;;
        --profile) PROFILE="${2:-baseline}"; shift ;;
        --profile=*) PROFILE="${1#--profile=}" ;;
        *) echo "Bilinmeyen argüman: $1"; exit 1 ;;
    esac
    shift
done
case "$LAYOUT" in ""|clean|field) ;; *) echo "Bilinmeyen layout: $LAYOUT (clean|field)"; exit 1 ;; esac
if [ -n "$MAP" ] && ! [[ "$MAP" =~ ^[1-9][0-9]*$ ]]; then echo "--map pozitif tam sayı olmalı"; exit 1; fi
PROFILE_TO_VALIDATE="$PROFILE" SIM_SCRIPTS="$SIM/scripts" python3 -c 'import os,sys;sys.path.insert(0,os.environ["SIM_SCRIPTS"]);from scenario_profiles import load_profile;load_profile(os.environ["PROFILE_TO_VALIDATE"])' \
    || { echo "Bilinmeyen/geçersiz profil: $PROFILE"; exit 1; }
if [ -z "$SEED" ]; then
    SEED=$(PROFILE_TO_VALIDATE="$PROFILE" SIM_SCRIPTS="$SIM/scripts" python3 -c 'import os,sys;sys.path.insert(0,os.environ["SIM_SCRIPTS"]);from scenario_profiles import load_profile;print(load_profile(os.environ["PROFILE_TO_VALIDATE"])["seed"])')
fi

# İmaj yoksa derle
if ! podman image exists "$IMAGE"; then
    echo "[record] İmaj derleniyor: $IMAGE (ilk sefer ~2-4 dk)"
    podman build -t "$IMAGE" -f docker/Containerfile "$SIM"
fi

# Sıradaki versiyon (v1 yok say, en yüksek vN → vN+1)
LAST=$(ls -d "$OUTDIR"/v[0-9]* 2>/dev/null | sed 's#.*/v##' | sort -n | tail -1)
V=$(( ${LAST:-0} + 1 ))
VDIR="$OUTDIR/v$V"; mkdir -p "$VDIR"

if [ -n "$SINGLE" ]; then OUTNAME="navitas_${SINGLE}.mp4"; else OUTNAME="navitas.mp4"; fi

# İHA-HARİTALAMA İZLEYİCİSİ (DÜRÜST ZİNCİR) — host .venv'de ARKA PLANDA çalışır:
# konteyner İHA tarama karelerini + poz logunu v$V/iha_scan_<seviye>/'ye canlı senkronlar;
# tarama bitince (SCAN_DONE) izleyici ORTOMOZAİK kurar, GERÇEK modeli (best.pt) sim
# taramasında koşar, İKA rotasını route.txt'ye yazar; konteyner rotayı İKA'ya verir.
# Model yanılırsa İKA yanlış yola gider — sonuç DÜRÜSTTÜR (eski akıştaki gibi dünya
# modelin kararına göre KURULMAZ). .venv yoksa İKA ground-truth fallback ile sürer
# (plugin loglar; model başarısı sayılmaz).
VENV="$REPO/.venv/bin/python"
WATCHER_PID=""
if [ -x "$VENV" ]; then
    echo "[record] İHA-haritalama izleyicisi başlatıldı (host .venv, arka plan)"
    "$VENV" "$SIM/scripts/iha_haritala.py" --watch "$VDIR" --levels "$LEVELS" \
        > "$VDIR/iha_haritala.log" 2>&1 &
    WATCHER_PID=$!
else
    echo "[record] (.venv yok — model koşamaz; İKA ground-truth FALLBACK ile sürecek)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  KAYIT → v$V   profil: $PROFILE   seviye: $LEVELS   seed=$SEED   süre modu: $RT"
echo "╚══════════════════════════════════════════╝"
# /sim (simulation) + /comms (haberleşme) mount; recordings /sim içinde (:z paylaşımlı).
podman run --rm \
    -v "$SIM":/sim:z \
    -v "$REPO/comms":/comms:z \
    --shm-size=1g \
    -e GAZEBO_GUI_CAM="${GAZEBO_GUI_CAM:-}" \
    -e NAVITAS_MAP="$MAP" \
    -e NAVITAS_PROFILE="$PROFILE" \
    "$IMAGE" \
    bash /sim/docker/record_in_container.sh "$SEED" "/sim/recordings/v$V/$OUTNAME" "$LEVELS" "$RT" "$LAYOUT"

# izleyiciyi kapat (normalde seviyeler bitince kendisi çıkar)
if [ -n "$WATCHER_PID" ]; then
    wait_s=0
    while kill -0 "$WATCHER_PID" 2>/dev/null && [ "$wait_s" -lt 60 ]; do
        sleep 2; wait_s=$(( wait_s + 2 ))
    done
    kill "$WATCHER_PID" 2>/dev/null || true
fi

echo ""
echo "════════════════════════════════════════════"
echo "  Kayıt tamam → $VDIR/"
ls -lh "$VDIR"/ 2>/dev/null
echo "════════════════════════════════════════════"
