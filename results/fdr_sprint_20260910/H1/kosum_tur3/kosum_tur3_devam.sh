#!/usr/bin/env bash
# T214-A tur 3 DEVAM (10 Eyl öğleden sonra). İlk koşu (`kosum_tur3.sh`, 12:39–12:59; ham çıktı
# `kosum_tur3_log.txt`) uretim kolunda 6/15 koşumda KESİLDİ (kullanım kredisi). Bu betik, GPU işleri
# TEK süreç zincirinde SIRALI (ON_KAYIT §5.6):
#   (3') K3 üretim boru hattı YENİDEN — aynı taramalar (`--yeniden-tara` YOK), TEŞHİS alanları eklendi;
#        ilk koşunun karar izi önce yazılır, sonra karşılaştırılır (k3_uretim_boru/iki_kosu_karsilastirma.json)
#   (4') uretim: (3')'te OPEN_ROUTE üreten haritalar × 3 tohum — 15 koşumun HEPSİ (tek kod sürümü);
#        ilk koşunun 6 JSON'u `kesilen_kosu/` altında korunur (üzerine yazılmadan önce kopyalanır)
# gt ve model kolları YENİDEN KOŞULMAZ: sürüş/rota kod yolları değişmedi (yalnız özet ve tel-tipi
# alanları; eski JSON'lar hakem alanlarından çözülür — `gorev_kosumu.tel_tipi`).
# Koşum: bash kosum_tur3_devam.sh 2>&1 | tee kosum_tur3_devam_log.txt
set -euo pipefail
KOK="$(cd "$(dirname "$0")/../../../.." && pwd)"
PY="${PY:-O:/navitas-local-train/venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8
cd "$KOK"
K3="results/fdr_sprint_20260910/H1/k3_uretim_boru"
KT="results/fdr_sprint_20260910/H1/kosum_tur3"
echo "[devam] başlangıç $(date '+%Y-%m-%d %H:%M:%S') kök=$KOK git=$(git rev-parse --short HEAD) (+ çalışma ağacı değişiklikleri)"

if [ ! -f "$K3/kosu1_karar_izi.json" ]; then
  "$PY" -B "$K3/karar_izi.py" yaz kosu1_karar_izi.json
  cp "$K3/ozet_k3_uretim.json" "$K3/kosu1_ozet_k3_uretim.json"
fi
mkdir -p "$KT/kesilen_kosu"
for f in "$KT"/uretim_*_*_*.json; do
  [ -e "$KT/kesilen_kosu/$(basename "$f")" ] || cp "$f" "$KT/kesilen_kosu/"
done
echo "[devam] ilk koşu kopyaları: $(ls "$KT/kesilen_kosu" | wc -l) uretim JSON"

"$PY" -B simulation/mujoco/sim_karar_toplayici.py --hepsi --seed 42 --res 1280 --besleme hepsi
echo "[devam] K3 üretim (yeniden) bitti $(date '+%H:%M:%S')"
"$PY" -B "$K3/karar_izi.py" karsilastir kosu1_karar_izi.json

HARITALAR=$("$PY" -c "import json; o=json.load(open('$K3/ozet_k3_uretim.json', encoding='utf-8')); print(','.join(str(h['harita']) + '_' + h['senaryo'] for h in o['beslemeler']['kerteriz']['haritalar'] if h['open_route_var']))")
echo "[devam] uretim haritaları (K3 kerteriz, OPEN_ROUTE var): ${HARITALAR:-<yok>}"
if [ -n "$HARITALAR" ]; then
  "$PY" -B simulation/mujoco/gorev_kosumu.py --hepsi --rota-kaynak uretim --res 1280 --tohumlar 42,43,44 \
      --haritalar "$HARITALAR"
fi
echo "[devam] bitiş $(date '+%Y-%m-%d %H:%M:%S')"
