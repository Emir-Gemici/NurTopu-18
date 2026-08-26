#!/bin/sh
# K6 olcumu: 65_kabul_denetcisi v35 / v3 / v6 (ON_KAYIT §12). Worktree icinden kosulur.
PY=/o/navitas-local-train/venv/Scripts/python.exe
WT="O:/navitas/.claude/worktrees/wf_951a190e-bfe-1"
cd "$WT/scripts/olcum" || exit 1
export PYTHONIOENCODING=utf-8
run() {
  ad=$1; model=$2
  echo "=== $ad  $model  $(date)" > "$WT/results/k6/${ad}_65.log"
  "$PY" -B 65_kabul_denetcisi.py --model "$model" --ad "$ad" >> "$WT/results/k6/${ad}_65.log" 2>&1
  echo "exit=$? $(date)" >> "$WT/results/k6/${ad}_65.log"
}
run k6_v35 "O:/navitas/models/navitas_seg_v35_best.pt"
run k6_v3  "O:/navitas/codes/runs/segment/gece_v3_v35taban/weights/best.pt"
run k6_v6  "O:/navitas/codes/runs/segment/gece_v6_v35taban/weights/best.pt"
echo BITTI > "$WT/results/k6/BITTI"
