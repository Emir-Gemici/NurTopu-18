#!/usr/bin/env bash
# Navitas TEKNOFEST 2026 — Konteynerli Simülasyon Video Kayıtçısı (HOST tarafı)
#
# Gazebo Classic 11'i Podman konteynerinde çalıştırır, sanal ekranda render eder,
# İHA + İKA görevini oynatır ve mp4 olarak kaydeder. Host'un masaüstüne dokunmaz.
#
# Kullanım:
#   ./record.sh                 → kolay, orta, zor (üçü de)
#   ./record.sh orta            → sadece orta
#   ./record.sh kolay zor       → seçili senaryolar
#
# Çıktı: simulation/recordings/navitas_<senaryo>.mp4
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"               # navitas/simulation
OUTDIR="$SIM/recordings"
IMAGE="navitas-gazebo:11"
mkdir -p "$OUTDIR"

# 1) İmaj yoksa derle
if ! podman image exists "$IMAGE"; then
    echo "[record] İmaj derleniyor: $IMAGE (ilk sefer ~2-4 dk, plugin derlemesi dahil)"
    podman build -t "$IMAGE" -f docker/Containerfile "$SIM"
fi

# 2) Senaryolar
SCENARIOS=("$@")
[ ${#SCENARIOS[@]} -eq 0 ] && SCENARIOS=(kolay orta zor)

# 3) Her senaryo için konteynerde kaydet
for sc in "${SCENARIOS[@]}"; do
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  KAYIT: $sc"
    echo "╚══════════════════════════════════════════╝"
    podman run --rm \
        -v "$SIM":/sim:Z \
        -v "$OUTDIR":/out:Z \
        --shm-size=1g \
        -e GAZEBO_GUI_CAM="${GAZEBO_GUI_CAM:-}" \
        "$IMAGE" \
        bash /sim/docker/record_in_container.sh "$sc" 42 "/out/navitas_${sc}.mp4"
done

echo ""
echo "════════════════════════════════════════════"
echo "  Tüm kayıtlar tamam → $OUTDIR"
ls -lh "$OUTDIR"/*.mp4 2>/dev/null || echo "  (mp4 bulunamadı)"
echo "════════════════════════════════════════════"
