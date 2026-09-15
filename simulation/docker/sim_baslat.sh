#!/usr/bin/env bash
# Navitas — verilen .world dosyasını GERÇEK Gazebo GUI penceresinde açar (host X11'e
# yönlendirilmiş gzserver+gzclient). canli_izle.sh ve harita_studyo.py bunu çağırır;
# tek başına da kullanılabilir.
#
# Kullanım: ./sim_baslat.sh <dunya.world MUTLAK yolu> [konteyner adı]
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"
IMAGE="${NAVITAS_GAZEBO_IMAGE:-navitas-gazebo:11}"

WORLD_ABS="${1:?kullanım: sim_baslat.sh <dunya.world mutlak yolu> [konteyner adı]}"
NAME="${2:-navitas-canli-$$}"
case "$WORLD_ABS" in
    "$SIM"/*) WORLD_REL="${WORLD_ABS#"$SIM"/}" ;;
    *) echo "[sim] HATA: dünya dosyası $SIM altında olmalı (mount edilen tek yer)"; exit 1 ;;
esac
[ -f "$WORLD_ABS" ] || { echo "[sim] HATA: dosya yok: $WORLD_ABS"; exit 1; }

if ! podman image exists "$IMAGE"; then
    echo "[sim] İmaj derleniyor: $IMAGE (ilk sefer ~2-4 dk)"
    podman build -t "$IMAGE" -f Containerfile "$SIM"
fi

if [ -z "${DISPLAY:-}" ]; then echo "[sim] HATA: host'ta DISPLAY yok (X11/XWayland gerekli)"; exit 1; fi
xhost "+SI:localuser:$(id -un)" >/dev/null 2>&1 || echo "[sim] uyarı: xhost ayarlanamadı"
cleanup() { xhost "-SI:localuser:$(id -un)" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "[sim] Gazebo GUI açılıyor: $WORLD_REL  (konteyner: $NAME)"
podman run --rm --name "$NAME" \
    -e DISPLAY="$DISPLAY" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
    -v "$SIM":/sim:z \
    --shm-size=1g \
    --net=host \
    --security-opt label=disable \
    "$IMAGE" \
    bash -c '
        set -e
        export GAZEBO_MODEL_PATH=/sim/models:$GAZEBO_MODEL_PATH
        cd /sim
        pkill -f gzclient 2>/dev/null || true
        pkill -f gzserver 2>/dev/null || true
        gzserver --pause "'"$WORLD_REL"'" &
        SPID=$!
        for i in $(seq 1 30); do
            timeout 5 gz topic -l 2>/dev/null | grep -q world_stats && break
            sleep 1
        done
        gzclient &
        CPID=$!
        sleep 1
        gz world -p 0 || true
        # gzclient (Qt4+OGRE, XWayland uzerinde yazilimsal render) nadiren acilista
        # SIGABRT ile cokuyor (upstream Gazebo11 kirilganligi) — kullanici pencereyi
        # henuz gormeden coktuyse (ilk 15sn) gzserveri ayakta tutup gzclienti yeniden
        # baslat; kullanicinin pencereyi kapatmasiyla cikan gec sonlanmalarda denenmez.
        RETRY=0
        while true; do
            START=$(date +%s)
            wait -n $SPID $CPID
            kill -0 $SPID 2>/dev/null || break
            kill -0 $CPID 2>/dev/null && break
            ELAPSED=$(( $(date +%s) - START ))
            if [ "$ELAPSED" -lt 15 ] && [ "$RETRY" -lt 3 ]; then
                RETRY=$((RETRY+1))
                echo "[sim] gzclient beklenmedik kapandi (${ELAPSED}sn), yeniden deneniyor ($RETRY/3)..."
                sleep 1
                gzclient &
                CPID=$!
                continue
            fi
            break
        done
        kill $SPID $CPID 2>/dev/null || true
        wait $SPID $CPID 2>/dev/null || true
    '
echo "[sim] kapandı: $NAME"
