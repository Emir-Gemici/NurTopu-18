#!/usr/bin/env python3
"""Generate all six selectable Gazebo worlds plus a reproducibility manifest."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scenario_profiles import available_profiles, load_profile
from world_generator import build_world


def main():
    ap = argparse.ArgumentParser(description="Navitas altı-senaryo Gazebo paketi")
    ap.add_argument("--output-dir", default="/tmp/navitas-gazebo-six-scenarios")
    ap.add_argument("--no-animation", action="store_true",
                    help="İHA/İKA plugin ve kayıt kamerası olmadan yalnız statik dünyalar")
    args = ap.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "arena_m": [300, 300], "htab_m": [50, 50],
                "htab_count": 3, "profiles": []}
    for profile_id in available_profiles():
        profile = load_profile(profile_id)
        world, zone = build_world(profile["seed"], profile["active_zone"],
                                  record=not args.no_animation, profile_id=profile_id)
        path = outdir / f"{profile_id}.world"
        path.write_text(world, encoding="utf-8")
        manifest["profiles"].append({
            "id": profile_id,
            "author": profile["author"],
            "title_tr": profile["title_tr"],
            "active_zone": profile["active_zone"],
            "seed": profile["seed"],
            "map_ids": profile["map_ids"],
            "active_open_road": zone["road"],
            "world": path.name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "acceptance": profile["acceptance"],
        })
        print(f"{profile_id}: {path} ({path.stat().st_size / 1024 / 1024:.2f} MiB)")
    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
