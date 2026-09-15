#!/usr/bin/env bash
set -euo pipefail

simulation="$(cd "$(dirname "$0")/.." && pwd)"
world="$(realpath "${1:-$simulation/realism_runs/current/candidate.world}")"
case "$world" in
    "$simulation"/realism_runs/*/candidate.world) ;;
    *) echo "HATA: yalnız realism_runs altındaki aday dünya açılır" >&2; exit 1 ;;
esac
[[ -f "$world" ]] || { echo "HATA: dünya yok" >&2; exit 1; }
[[ -n "${DISPLAY:-}" ]] || { echo "HATA: DISPLAY yok" >&2; exit 1; }
image="${NAVITAS_GAZEBO_IMAGE:-navitas-gazebo:11}"
podman image exists "$image"
xhost "+SI:localuser:$(id -un)" >/dev/null
trap 'xhost "-SI:localuser:$(id -un)" >/dev/null 2>&1 || true' EXIT
echo "Gerçekçilik adayı: tam görev/fizik kalibrasyonu onaylı değildir."
podman run --rm --name "navitas-realism-gui-$$" --network=host \
    --security-opt label=disable --shm-size=1g \
    -e DISPLAY -e QT_X11_NO_MITSHM=1 -e GAZEBO_MODEL_DATABASE_URI= \
    -e GAZEBO_MODEL_PATH=/sim/models \
    -e GAZEBO_RESOURCE_PATH=/sim:/usr/share/gazebo-11 \
    -e GAZEBO_MASTER_URI=http://127.0.0.1:11440 -e GAZEBO_IP=127.0.0.1 \
    -v /tmp/.X11-unix:/tmp/.X11-unix:ro -v "$simulation":/sim:ro \
    "$image" gazebo --verbose --pause "/sim/${world#"$simulation"/}"
