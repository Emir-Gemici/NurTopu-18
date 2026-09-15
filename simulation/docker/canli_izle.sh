#!/usr/bin/env bash
# Navitas — CANLI İZLEME: gerçek Gazebo GUI penceresi (host ekranında) + YKS hakem paneli.
#
# record.sh'ten farkı: orada Xvfb (görünmez sanal ekran) + sadece gzserver ile mp4
# kaydı alınır (kanıt üretimi için deterministik). Burada gzclient GERÇEKTEN açılır ve
# X11 host ekranına yönlendirilir — sim'i CANLI, kendi gözünle izlersin.
#
# ⚠️ Dürüst uyarı: YKS paneli şu an --demo modunda (kendi iç İHA/İKA beslemesiyle) açılır,
# Gazebo penceresine GERÇEK comms/UDP ile bağlı DEĞİL (bu bağ [[gazebo-durum]] backlog'unda
# B.3: "rota.json'ın gerçek UDP comms ile aktarımı" maddesi — henüz yapılmadı). Yani iki ayrı
# pencere göreceksin: biri gerçek fizik sim'i, öbürü panel tanıtımı. Yan yana izlemek için iyi
# ama panel'deki rota GERÇEKTEN o an Gazebo'da olanı yansıtmıyor.
#
# Kullanım:
#   ./docker/canli_izle.sh                  → kolay, map 1, field layout
#   ./docker/canli_izle.sh orta --map 3
#   ./docker/canli_izle.sh zor --seed 7 --layout clean
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"
REPO="$(dirname "$SIM")"

LEVEL="kolay"; SEED=42; LAYOUT=field; MAP=1
while [ $# -gt 0 ]; do
    case "$1" in
        kolay|orta|zor) LEVEL="$1" ;;
        --seed) SEED="${2:-42}"; shift ;;
        --seed=*) SEED="${1#--seed=}" ;;
        --layout) LAYOUT="${2:-field}"; shift ;;
        --layout=*) LAYOUT="${1#--layout=}" ;;
        --map) MAP="${2:-1}"; shift ;;
        --map=*) MAP="${1#--map=}" ;;
        *) echo "Bilinmeyen argüman: $1"; exit 1 ;;
    esac
    shift
done

# ── Dünyayı üret (aynı üretici, --record: kinematik animasyon plugin'i ile pürüzsüz hareket) ──
WORLD_ABS="$SIM/worlds/canli_${LEVEL}.world"
echo "[canli] Dünya üretiliyor: $LEVEL / map $MAP / layout $LAYOUT / seed $SEED"
python3 "$SIM/scripts/world_generator.py" --focus "$LEVEL" --seed "$SEED" \
    --record --layout "$LAYOUT" --map "$MAP" --output "$WORLD_ABS"

# ── YKS hakem paneli — host .venv'de, ayrı pencere, arka planda ────────────
VENV="$REPO/.venv/bin/python"
GUI_PID=""
if [ -x "$VENV" ]; then
    echo "[canli] YKS hakem paneli açılıyor (--demo, ayrı pencere)..."
    "$VENV" "$REPO/comms/yks_gui.py" --demo &
    GUI_PID=$!
else
    echo "[canli] (.venv yok — YKS paneli atlanıyor, sadece Gazebo açılacak)"
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  CANLI Gazebo GUI → seviye: $LEVEL  map: $MAP  layout: $LAYOUT  seed: $SEED"
echo "║  Kapatmak için: bu terminalde Ctrl+C"
echo "╚══════════════════════════════════════════╝"

# ── Gerçek GUI: gzserver + gzclient, host X'ine yönlendirilmiş (ortak script) ──
"$SIM/docker/sim_baslat.sh" "$WORLD_ABS"

if [ -n "$GUI_PID" ]; then kill "$GUI_PID" 2>/dev/null || true; fi
echo "[canli] kapandı."
