#!/usr/bin/env bash
# Container içi dinamik smoke: artçı engel görev sırasında açık koridora taşınır.
set -euo pipefail

SIM_ROOT="${SIM_ROOT:-/sim}"
cd "$SIM_ROOT"
export DISPLAY=:99
export GAZEBO_MODEL_PATH="$SIM_ROOT/models"
export GAZEBO_PLUGIN_PATH="${GAZEBO_PLUGIN_PATH:-/opt/navitas/lib}"

WORLD=/tmp/navitas_aftershock.world
rm -f /tmp/navitas_simtime /tmp/navitas_route /tmp/navitas_ika_trigger
rm -rf /tmp/frames /tmp/iha_scan
mkdir -p /tmp/frames /tmp/iha_scan
python3 scripts/world_generator.py --profile cx_aftershock_dynamic --record --output "$WORLD" >/tmp/aftershock_gen.log

# Açık rotayı ve YKS tetik olayını ver: test yalnız görsel pozu değil,
# dinamik kirişin İKA'yı fiziksel olarak durdurduğunu da kanıtlasın.
python3 -c "import sys;sys.path.insert(0,'scripts');import arena;from scenario_profiles import load_profile
p=load_profile('cx_aftershock_dynamic'); level=p['active_zone']; H=arena.harita(p['map_ids'][level],level); cx,cy=arena.ZONE_POS[level]
print('\\n'.join(f'{cx+x:.4f} {cy+y:.4f}' for x,y in arena._downsample(H['paths'][H['open']])))" \
  > /tmp/navitas_route
touch /tmp/navitas_ika_trigger

Xvfb :99 -screen 0 1280x720x24 -nolisten tcp >/tmp/aftershock_xvfb.log 2>&1 &
XVFB_PID=$!
gzserver --pause "$WORLD" >/tmp/aftershock_gzserver.log 2>&1 &
GZ_PID=$!
cleanup() { kill "$GZ_PID" "$XVFB_PID" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 90); do
  timeout 5 gz topic -l 2>/dev/null | grep -q world_stats && break
  kill -0 "$GZ_PID" 2>/dev/null || { cat /tmp/aftershock_gzserver.log; exit 1; }
  sleep 1
done
timeout 5 gz topic -l 2>/dev/null | grep -q world_stats
gz world -p 0 >/dev/null 2>&1 || true

wait_sim_time() {
  local target="$1" wall=0 now=0
  while [ "$wall" -lt 180 ]; do
    now=$(head -n1 /tmp/navitas_simtime 2>/dev/null || echo 0)
    [ "${now:-0}" -ge "$target" ] 2>/dev/null && return 0
    kill -0 "$GZ_PID" 2>/dev/null || { cat /tmp/aftershock_gzserver.log; return 1; }
    sleep 1; wall=$((wall + 1))
  done
  return 1
}

model_z() {
  grep '^aftershock_barrier ' /tmp/navitas_simtime | tail -n1 \
    | sed -n 's/.* z=\([^ ]*\).*/\1/p'
}

wait_sim_time 40
Z_BEFORE=$(model_z)
wait_sim_time 47
Z_AFTER=$(model_z)
python3 -c "zb=float('$Z_BEFORE'); za=float('$Z_AFTER'); print(f'AFTERSHOCK_Z_BEFORE={zb:.3f} AFTER={za:.3f}'); assert zb > 7 and 0.4 <= za <= 0.9"
wait_terminal() {
  local wall=0 line=""
  while [ "$wall" -lt 300 ]; do
    line=$(grep '^ika_' /tmp/navitas_simtime 2>/dev/null | tail -n1 || true)
    case "$line" in
      *durum=TIKANDI*|*durum=BITTI*) printf '%s\n' "$line"; return 0 ;;
    esac
    kill -0 "$GZ_PID" 2>/dev/null || { cat /tmp/aftershock_gzserver.log; return 1; }
    sleep 1; wall=$((wall + 1))
  done
  echo "terminal durum zaman aşımı: $line" >&2
  return 1
}
FINAL_IKA=$(wait_terminal)
printf '%s\n' "$FINAL_IKA" | grep -q 'durum=TIKANDI'
echo "AFTERSHOCK_COLLISION_TIKANDI_OK"
echo "AFTERSHOCK_SMOKE_OK"
