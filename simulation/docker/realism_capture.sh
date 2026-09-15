#!/usr/bin/env bash
set -euo pipefail

export DISPLAY=:96
export GAZEBO_MODEL_DATABASE_URI=
export GAZEBO_RESOURCE_PATH="/sim:/usr/share/gazebo-11"
export GAZEBO_MODEL_PATH="/sim/models"
export GAZEBO_MASTER_URI="http://127.0.0.1:11439"
export GAZEBO_IP=127.0.0.1
export QT_X11_NO_MITSHM=1
export OMP_NUM_THREADS=4

Xvfb :96 -screen 0 1280x960x24 -nolisten tcp >/evidence/xvfb.log 2>&1 &
display_pid=$!
server_pid=""
cleanup() {
    if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; fi
    kill "$display_pid" 2>/dev/null || true
}
trap cleanup EXIT
sleep 2
gzserver --verbose /evidence/capture.world >/evidence/gzserver.log 2>&1 &
server_pid=$!
for elapsed in $(seq 1 240); do
    if ! kill -0 "$server_pid" 2>/dev/null; then
        echo "RENDER_FAILED: gzserver exited"
        tail -20 /evidence/gzserver.log
        exit 1
    fi
    ready=0
    for camera in oblique top detail; do
        frame_count=$(find "/evidence/$camera" -maxdepth 1 -name '*.jpg' 2>/dev/null | wc -l) || frame_count=0
        if [[ "$frame_count" -ge 2 ]]; then
            ready=$((ready + 1))
        fi
    done
    if [[ "$ready" -eq 3 ]]; then
        sleep 3
        echo "RENDER_OK cameras=3 minimum_frames_per_camera=2 ready_poll_seconds=$elapsed"
        exit 0
    fi
    sleep 1
done
echo "RENDER_TIMEOUT: fresh frames missing"
tail -20 /evidence/gzserver.log
exit 1
