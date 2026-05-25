#!/usr/bin/env bash
# Navitas TEKNOFEST 2026 — Simülasyon Başlatıcı (uyumluluk sarmalayıcı)
# Yeni başlatıcı: ./launch/navitas.launch
#
# Kullanım:
#   ./launch.sh               → kolay senaryo
#   ./launch.sh orta          → orta senaryo
#   ./launch.sh zor           → zor senaryo
#   ./launch.sh rastgele      → rastgele senaryo
#   ./launch.sh zor --seed 5  → sabit seed

set -e
cd "$(dirname "$0")"

exec bash launch/navitas.launch "$@"
