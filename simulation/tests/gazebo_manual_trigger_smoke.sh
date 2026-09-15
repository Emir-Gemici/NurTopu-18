#!/usr/bin/env bash
# Container içi dinamik smoke: rota hazır olsa bile İKA manuel YKS tetik olayını bekler.
set -euo pipefail

PROFILE="${1:-cx_comms_latency}"
SIM_ROOT="${SIM_ROOT:-/sim}"
cd "$SIM_ROOT"

export DISPLAY=:99
export GAZEBO_MODEL_PATH="$SIM_ROOT/models"
export GAZEBO_PLUGIN_PATH="${GAZEBO_PLUGIN_PATH:-/opt/navitas/lib}"

WORLD=/tmp/navitas_manual_trigger.world
SERVER_LOG=/tmp/navitas_manual_trigger_gzserver.log
rm -f /tmp/navitas_route /tmp/navitas_ika_trigger /tmp/navitas_simtime "$SERVER_LOG"
rm -rf /tmp/frames /tmp/iha_scan
mkdir -p /tmp/frames /tmp/iha_scan

python3 scripts/world_generator.py --profile "$PROFILE" --record --output "$WORLD" >/tmp/manual_gen.log

# Aktif profilin gerçek açık rotasını dünya koordinatında test girdisi yap.
python3 -c "import sys;sys.path.insert(0,'scripts');import arena;from scenario_profiles import load_profile
p=load_profile('$PROFILE'); level=p['active_zone']; H=arena.harita(p['map_ids'][level],level); cx,cy=arena.ZONE_POS[level]
print('\\n'.join(f'{cx+x:.4f} {cy+y:.4f}' for x,y in arena._downsample(H['paths'][H['open']])))" \
  > /tmp/navitas_route

Xvfb :99 -screen 0 1280x720x24 -nolisten tcp >/tmp/manual_xvfb.log 2>&1 &
XVFB_PID=$!
gzserver --pause "$WORLD" >"$SERVER_LOG" 2>&1 &
GZ_PID=$!
cleanup() {
  kill "$GZ_PID" "$XVFB_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 90); do
  timeout 5 gz topic -l 2>/dev/null | grep -q world_stats && break
  kill -0 "$GZ_PID" 2>/dev/null || { cat "$SERVER_LOG"; exit 1; }
  sleep 1
done
timeout 5 gz topic -l 2>/dev/null | grep -q world_stats || { cat "$SERVER_LOG"; exit 1; }
gz world -p 0 >/dev/null 2>&1 || true

wait_sim_time() {
  local target="$1" wall=0 now=0
  while [ "$wall" -lt 180 ]; do
    now=$(head -n1 /tmp/navitas_simtime 2>/dev/null || echo 0)
    [ "${now:-0}" -ge "$target" ] 2>/dev/null && return 0
    kill -0 "$GZ_PID" 2>/dev/null || { cat "$SERVER_LOG"; return 1; }
    sleep 1
    wall=$((wall + 1))
  done
  echo "sim time timeout: hedef=$target son=${now:-0}" >&2
  return 1
}

wait_sim_time 40
BEFORE=$(grep '^ika_' /tmp/navitas_simtime | tail -n1)
printf '%s\n' "$BEFORE" | grep -q 'rota=model'
printf '%s\n' "$BEFORE" | grep -q 'tetik=bekliyor'
BX=$(printf '%s\n' "$BEFORE" | sed -n 's/.* x=\([^ ]*\).*/\1/p')
BY=$(printf '%s\n' "$BEFORE" | sed -n 's/.* y=\([^ ]*\).*/\1/p')

# YKS operatörünün iniş sonrası açık manuel görev olayı.
touch /tmp/navitas_ika_trigger
wait_sim_time 48
AFTER=$(grep '^ika_' /tmp/navitas_simtime | tail -n1)
printf '%s\n' "$AFTER" | grep -q 'tetik=hazir'
AX=$(printf '%s\n' "$AFTER" | sed -n 's/.* x=\([^ ]*\).*/\1/p')
AY=$(printf '%s\n' "$AFTER" | sed -n 's/.* y=\([^ ]*\).*/\1/p')

python3 -c "import math; d=math.hypot(float('$AX')-float('$BX'),float('$AY')-float('$BY')); print(f'MANUAL_TRIGGER_MOVE_M={d:.3f}'); assert d > 0.5"
echo "MANUAL_TRIGGER_SMOKE_OK"
