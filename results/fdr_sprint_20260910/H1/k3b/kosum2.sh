#!/usr/bin/env bash
# T213-A K3-b tur 2 (son kod: yol_koridor_uv hızlandırıldı → v1 dokusu yeniden üretilir; v1/v2/v3 yeniden ölçülür).
# ⚠ 10 Eyl çürütücü düzeltmesi: hb2.5 TEŞHİS geçişi tur 1/2 koşumunda üretim geçişiyle AYNI --kok'a yazıyor ve
# detection.json'ları eziyordu; satır ayrı köke (--kok <v>_hb2.5 --tarama-kaynak <v>) düzeltildi. Kanıt kosum3.sh ile yeniden üretildi.
# GPU tek süreç, sıralı. taban tur 1'den (kosum.sh) geçerli (dokusu değişmedi).
cd "O:/navitas/.claude/worktrees/wf_e7381c6f-ab1-1" || exit 1
PY="O:/navitas-local-train/venv/Scripts/python.exe"
K="results/fdr_sprint_20260910/H1/k3b"
H15="1:kolay,1:orta,1:zor,2:kolay,2:orta,2:zor,3:kolay,3:orta,3:zor,4:kolay,4:orta,4:zor,5:kolay,5:orta,5:zor"
rm -f simulation/mujoco/dokular/uretilen/*_v1.png
for v in v1 v2 v3; do
  echo "=== $v uretim (hb 0) $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/$v" --cikti "$K/${v}_15harita.json" --yeniden-tara --teshis-imgsz 512 2>&1 | grep "^\[K3\]"
  echo "=== $v TESHIS hb2.5 $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/${v}_hb2.5" --tarama-kaynak "$K/$v" --cikti "$K/${v}_15harita_hb2.5.json" --hb-yaricap 2.5 2>&1 | grep "^\[K3\] ÖZET"
done
echo "=== v1 TESHIS mozaik nadir_yakin $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant v1 --kok "$K/v1_nadir" --cikti "$K/v1_15harita_nadir_yakin.json" --yeniden-tara --mozaik nadir_yakin 2>&1 | grep "^\[K3\] ÖZET"
echo "=== v1 asfalt (3 harita) $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor --varyant v1 --yol-dokusu asfalt --kok "$K/v1_asfalt" --cikti "$K/v1_asfalt_3harita.json" --yeniden-tara 2>&1 | grep "^\[K3\]"
echo "=== v1 zemin_toprak (3 harita) $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor --varyant v1 --zemin-dokusu zemin_toprak --kok "$K/v1_zemin_toprak" --cikti "$K/v1_zemin_toprak_3harita.json" --yeniden-tara 2>&1 | grep "^\[K3\]"
echo "=== BITTI $(date +%H:%M:%S)"
