#!/usr/bin/env bash
# Navitas TEKNOFEST 2026 — Gazebo başlatıcı
# İHA hızı tüm Gazebo uçuşunda sabit 18.65 m/s.

set -e
cd "$(dirname "$0")"

exec python3 scripts/run_gazebo_1865.py "$@"
