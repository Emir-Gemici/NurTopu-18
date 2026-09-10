#!/usr/bin/env bash
# T213-A K3-b: 4 varyant × 15 harita, üretim semantiği (hb 0) + TEŞHİS (hb 2,5 m; imgsz 512). GPU tek süreç, sıralı.
cd "O:/navitas/.claude/worktrees/wf_e7381c6f-ab1-1" || exit 1
PY="O:/navitas-local-train/venv/Scripts/python.exe"
K="results/fdr_sprint_20260910/H1/k3b"
H15="1:kolay,1:orta,1:zor,2:kolay,2:orta,2:zor,3:kolay,3:orta,3:zor,4:kolay,4:orta,4:zor,5:kolay,5:orta,5:zor"
for v in taban v1 v2 v3; do
  echo "=== $v uretim (hb 0) $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/$v" --cikti "$K/${v}_15harita.json" --yeniden-tara --teshis-imgsz 512 2>&1 | grep "^\[K3\]"
  echo "=== $v TESHIS hb2.5 $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/$v" --cikti "$K/${v}_15harita_hb2.5.json" --hb-yaricap 2.5 2>&1 | grep "^\[K3\] ÖZET"
done
echo "=== v1 asfalt (3 harita) $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor --varyant v1 --yol-dokusu asfalt --kok "$K/v1_asfalt" --cikti "$K/v1_asfalt_3harita.json" --yeniden-tara 2>&1 | grep "^\[K3\]"
echo "=== BITTI $(date +%H:%M:%S)"
