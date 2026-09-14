#!/usr/bin/env python3
"""Navitas Gazebo başlatıcısı. İHA hızı her durumda 18.65 m/s'tir."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "worlds" / "navitas_arena.world"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", nargs="?", default="kolay", choices=["kolay", "orta", "zor", "rastgele"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()

    generator = ROOT / "scripts" / "world_generator_1865.py"
    cmd = [sys.executable, str(generator), "--difficulty", args.scenario,
           "--seed", str(args.seed), "--output", str(WORLD)]
    subprocess.run(cmd, cwd=ROOT, check=True)

    print("[navitas] İHA uçuş hızı: 18.65 m/s")
    gazebo_cmd = ["gzserver", str(WORLD)] if args.headless else ["gazebo", str(WORLD)]
    return subprocess.call(gazebo_cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
