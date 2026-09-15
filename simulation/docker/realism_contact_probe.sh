#!/usr/bin/env bash
set -euo pipefail

export GAZEBO_MODEL_DATABASE_URI=
export GAZEBO_RESOURCE_PATH=/sim:/usr/share/gazebo-11
export GAZEBO_MODEL_PATH=/sim/models
export GAZEBO_MASTER_URI=http://127.0.0.1:11441
export GAZEBO_IP=127.0.0.1
server_pid=""
trap 'if [[ -n "$server_pid" ]]; then kill "$server_pid" 2>/dev/null || true; fi' EXIT

for mode in positive negative; do
    gzserver --verbose --pause "/evidence/$mode.world" >"/evidence/${mode}_server.log" 2>&1 &
    server_pid=$!
    ready=0
    for attempt in $(seq 1 40); do
        if timeout 3 gz model -m probe_ground -p >"/evidence/${mode}_initial.pose" 2>/dev/null; then
            if [[ -s "/evidence/${mode}_initial.pose" ]]; then ready=1; break; fi
        fi
        sleep 1
    done
    [[ "$ready" -eq 1 ]] || { echo "CONTACT_START_TIMEOUT $mode"; exit 1; }
    gz world -m 3000
    sleep 10
    for model in probe_ground probe_rubble; do
        timeout 10 gz model -m "$model" -p >"/evidence/${mode}_${model}.pose"
    done
    kill "$server_pid"
    wait "$server_pid" || true
    server_pid=""
    sleep 2
done
echo "CONTACT_POSES_RECORDED positive_and_negative"
