#!/usr/bin/env bash
# T214-A tur 3 koşumu — GPU işleri TEK süreç zincirinde SIRALI (ON_KAYIT §5.6, BSOD kuralı).
# Ham çıktı: kosum_tur3_log.txt (bu betik `bash kosum_tur3.sh 2>&1 | tee kosum_tur3_log.txt` ile koşulur).
#   (3) K3 üretim kare-bazlı boru hattı: 15 harita × tohum 42, iki besleme (kerteriz BİRİNCİL, ham TEŞHİS)
#   (4) K5: 15 harita × 3 tohum — gt (YER GERÇEĞİ) ve model (mozaik zinciri, imgsz 512 kayıt defterinden)
#   (4) uretim: yalnız (3)'te OPEN_ROUTE üreten haritalar × 3 tohum (kerteriz beslemesi)
set -euo pipefail
KOK="$(cd "$(dirname "$0")/../../../.." && pwd)"
PY="${PY:-O:/navitas-local-train/venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8
cd "$KOK"
echo "[tur3] başlangıç $(date '+%Y-%m-%d %H:%M:%S') kök=$KOK git=$(git rev-parse --short HEAD)"

"$PY" -B simulation/mujoco/sim_karar_toplayici.py --hepsi --seed 42 --res 1280 --besleme hepsi
echo "[tur3] K3 üretim bitti $(date '+%H:%M:%S')"

"$PY" -B simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak gt --res 1280 --tohumlar 42,43,44
echo "[tur3] gt bitti $(date '+%H:%M:%S')"

"$PY" -B simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak model --res 1280 --tohumlar 42,43,44
echo "[tur3] model bitti $(date '+%H:%M:%S')"

HARITALAR=$("$PY" -c "import json; o=json.load(open('results/fdr_sprint_20260910/H1/k3_uretim_boru/ozet_k3_uretim.json', encoding='utf-8')); print(','.join(str(h['harita']) + '_' + h['senaryo'] for h in o['beslemeler']['kerteriz']['haritalar'] if h['open_route_var']))")
echo "[tur3] uretim haritaları (K3 kerteriz, OPEN_ROUTE var): ${HARITALAR:-<yok>}"
if [ -n "$HARITALAR" ]; then
  "$PY" -B simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak uretim --res 1280 --tohumlar 42,43,44 \
      --haritalar "$HARITALAR"
fi
echo "[tur3] bitiş $(date '+%Y-%m-%d %H:%M:%S')"
