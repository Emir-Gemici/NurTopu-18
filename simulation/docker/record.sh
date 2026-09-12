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
#   ./record.sh --terrain plain          → eski düz-kutu zemin (vars: textured = GERÇEK mesh moloz)
#     terrain: textured (vars, gerçek enkaz mesh'i) | plain (eski baseline) | relief (deneysel)
#
# Çıktı: simulation/recordings/rv<id>/  (navitas_tum_seviyeler.mp4 + hakem_log.txt) — her çalıştırma yeni rv<id>
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"               # navitas/simulation
REPO="$(dirname "$SIM")"            # navitas/  (comms/ burada)
OUTDIR="$SIM/recordings"
IMAGE="navitas-gazebo:11"
GAZEBO_RESOURCE_ROOT="/navitas_res" # Yalnız media bağlanır; /sim kayıt ve betikler için kalır.
mkdir -p "$OUTDIR"

# Argümanlar: seviye + --seed N + süre modu (1/0) + --layout + --map N (profil haritaları dahil)
SEED=42; SINGLE=""; LEVELS="kolay orta zor"; RT=0; LAYOUT=field; MAP=1; MAP_SET=0; PROFILE=""; REBUILD=0; TERRAIN=textured
while [ $# -gt 0 ]; do
    case "$1" in
        kolay|orta|zor) SINGLE="$1"; LEVELS="$1" ;;
        0|1) RT="$1" ;;                          # süre modu: 1=gerçekçi, 0=süresiz
        --realtime) RT="${2:-0}"; shift ;;
        --realtime=*) RT="${1#--realtime=}" ;;
        --seed) SEED="${2:-42}"; shift ;;
        --seed=*) SEED="${1#--seed=}" ;;
        --layout) LAYOUT="${2:-field}"; shift ;; # field=gerçekçi saha (vars.), clean=seyrek
        --layout=*) LAYOUT="${1#--layout=}" ;;
        --map) MAP="${2:-1}"; MAP_SET=1; shift ;; # gerçekçi/profil harita no
        --map=*) MAP="${1#--map=}"; MAP_SET=1 ;;
        --profile) PROFILE="${2:-}"; shift ;;    # scenario profile id (örn. cx_teknofest_official)
        --profile=*) PROFILE="${1#--profile=}" ;;
        --terrain) TERRAIN="${2:-plain}"; shift ;; # plain|textured|relief (zemin/arazi modu)
        --terrain=*) TERRAIN="${1#--terrain=}" ;;
        --rebuild) REBUILD=1 ;;
        *) echo "Bilinmeyen argüman: $1"; exit 1 ;;
    esac
    shift
done
case "$LAYOUT" in clean|field) ;; *) echo "Bilinmeyen layout: $LAYOUT (clean|field)"; exit 1 ;; esac
case "$TERRAIN" in plain|textured|relief) ;; *) echo "Bilinmeyen terrain: $TERRAIN (plain|textured|relief)"; exit 1 ;; esac
case "$MAP" in ''|*[!0-9]*) echo "Bilinmeyen harita: $MAP (pozitif tam sayı beklenir)"; exit 1 ;; esac
[ "$MAP" -gt 0 ] || { echo "Bilinmeyen harita: $MAP (pozitif tam sayı beklenir)"; exit 1; }

STAMP="$SIM/.gazebo-image-build.stamp"
if [ "$REBUILD" = "0" ] && [ ! -f "$STAMP" ]; then
    REBUILD=1
fi
if [ "$REBUILD" = "0" ] && [ -f "$STAMP" ]; then
    if find "$SIM/plugins" "$SIM/docker/Containerfile" -type f -newer "$STAMP" -print -quit | grep -q .; then
        REBUILD=1
    fi
fi

# İmaj yoksa veya plugin kaynakları yeniyse derle
if [ "$REBUILD" = "1" ] || ! podman image exists "$IMAGE"; then
    echo "[record] İmaj derleniyor: $IMAGE (ilk sefer ~2-4 dk)"
    podman build -t "$IMAGE" -f docker/Containerfile "$SIM"
    touch "$STAMP"
fi

# Sıradaki kayıt sürümü (rv1 yok say, en yüksek rvN → rvN+1)
LAST=$(ls -d "$OUTDIR"/rv[0-9]* 2>/dev/null | sed 's#.*/rv##' | sort -n | tail -1)
V=$(( ${LAST:-0} + 1 ))
VDIR="$OUTDIR/rv$V"; mkdir -p "$VDIR"

if [ -n "$SINGLE" ]; then OUTNAME="navitas_${SINGLE}_seviyesi.mp4"; else OUTNAME="navitas_tum_seviyeler.mp4"; fi

# İHA-HARİTALAMA İZLEYİCİSİ (DÜRÜST ZİNCİR) — host .venv'de ARKA PLANDA çalışır:
# konteyner İHA tarama karelerini + poz logunu rv$V/iha_scan_<seviye>/'ye canlı senkronlar;
# tarama bitince (SCAN_DONE) izleyici ORTOMOZAİK kurar, GERÇEK modeli (best.pt) sim
# taramasında koşar, İKA rotasını route.txt'ye yazar; konteyner rotayı İKA'ya verir.
# Model yanılırsa İKA yanlış yola gider — sonuç DÜRÜSTTÜR (eski akıştaki gibi dünya
# modelin kararına göre KURULMAZ). .venv/model rotası yoksa İKA güvenli durur;
# SDF'deki ground-truth waypoint'lere düşülmez.
VENV="$REPO/.venv/bin/python"
WATCHER_PID=""
if [ -x "$VENV" ]; then
    echo "[record] İHA-haritalama izleyicisi başlatıldı (host .venv, arka plan)"
    "$VENV" "$SIM/scripts/iha_haritala.py" --watch "$VDIR" --levels "$LEVELS" \
        > "$VDIR/iha_haritala.log" 2>&1 &
    WATCHER_PID=$!
else
    echo "[record] (.venv yok — model koşamaz; İKA dinamik rota olmadan GÜVENLİ DURUR)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
if [ -n "$PROFILE" ] && [ "$MAP_SET" = "0" ]; then MAP_LABEL="profile"; else MAP_LABEL="$MAP"; fi
echo "║  KAYIT → rv$V   seviye: $LEVELS   seed=$SEED   süre modu: $RT   layout: $LAYOUT   arazi: $TERRAIN   harita: $MAP_LABEL   profil: ${PROFILE:-baseline}"
echo "╚══════════════════════════════════════════╝"
# /sim (simulation) + /comms (haberleşme) mount; recordings /sim içinde (:z paylaşımlı).
# Gazebo kaynak kökü ayrı ve küçüktür: yalnız simulation/media ağacını görür.
podman run --rm \
    -v "$SIM":/sim:z \
    -v "$SIM/media":"$GAZEBO_RESOURCE_ROOT/media":z \
    -v "$REPO/comms":/comms:z \
    --shm-size=1g \
    -e GAZEBO_GUI_CAM="${GAZEBO_GUI_CAM:-}" \
    -e NAVITAS_GAZEBO_RESOURCE_ROOT="$GAZEBO_RESOURCE_ROOT" \
    -e NAVITAS_MAP="$MAP" \
    -e NAVITAS_MAP_SET="$MAP_SET" \
    -e NAVITAS_PROFILE="$PROFILE" \
    -e NAVITAS_TERRAIN="$TERRAIN" \
    "$IMAGE" \
    bash /sim/docker/record_in_container.sh "$SEED" "/sim/recordings/rv$V/$OUTNAME" "$LEVELS" "$RT" "$LAYOUT"

# Konteyner minimal Python ortamında hakem_log üretimi başarısız kalırsa host
# .venv ile onar. Video kaydı konteynerde kalır; kanıt logu host'taki proje
# bağımlılıklarıyla doldurulur.
if [ -x "$VENV" ] && [ ! -s "$VDIR/hakem_log.txt" ]; then
    LOG_MAP=$(find "$VDIR" -path "$VDIR/iha_scan_*/meta.txt" -maxdepth 3 -type f \
        -exec sed -n 's/^MAP=//p' {} + 2>/dev/null | tail -1)
    case "$LOG_MAP" in ''|*[!0-9]*) LOG_MAP="$MAP" ;; esac
    if [ -n "$SINGLE" ]; then
        MPLCONFIGDIR="${TMPDIR:-/tmp}/mpl-navitas" "$VENV" "$SIM/scripts/hakem_log.py" \
            --level "$SINGLE" --map "$LOG_MAP" --detections "$VDIR/detections.json" \
            --realtime "$RT" --out "$VDIR/hakem_log.txt" >/dev/null 2>&1 || true
    else
        MPLCONFIGDIR="${TMPDIR:-/tmp}/mpl-navitas" "$VENV" "$SIM/scripts/hakem_log.py" \
            --all --map "$LOG_MAP" --detections "$VDIR/detections.json" \
            --realtime "$RT" --out "$VDIR/hakem_log.txt" >/dev/null 2>&1 || true
    fi
fi

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
