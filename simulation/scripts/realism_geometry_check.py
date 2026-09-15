"""NEDEN: Üretilmiş collision mesh'lerinden üç güzergâhın açıklığını bağımsız ölçer."""

import argparse
import itertools
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np

import arena
from realism_assets import transform, transform_vertices
from realism_scene import SIMULATION
from scenario_profiles import load_profile

sys.path.insert(0, str(SIMULATION.parent / "codes"))
from costmap_path_finder import R_GEREKLI_M


def collada_triangles(path):
    namespace = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    root = ET.parse(path)
    values = root.find(".//c:float_array[@id='positions-array']", namespace)
    if values is None:
        raise ValueError(f"Beklenmeyen mesh pozisyon düzeni: {path}")
    return np.fromstring(values.text, sep=" ").reshape(-1, 3, 3)


def check(candidate, output, mpp=0.1):
    if mpp <= 0 or not np.isfinite(mpp):
        raise ValueError("Pozitif metre/piksel gerekli")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    world = ET.parse(candidate).find("world")
    side = int(round(arena.HTAB / mpp))
    masks = {scenario: np.zeros((side, side), np.uint8) for scenario in arena.SCENARIOS}
    mesh_count = 0
    for model in world.findall("model"):
        name = model.get("name", "")
        if not name.startswith(("real_rubble_", "bar_")):
            continue
        scenario = next(value for value in arena.SCENARIOS if value in name)
        mask = masks[scenario]
        origin = np.asarray(arena.ZONE_POS[scenario]) - arena.HTAB_HALF
        for link in model.findall("link"):
            base = transform(model.findtext("pose")) @ transform(link.findtext("pose"))
            for collision in link.findall("collision"):
                matrix = base @ transform(collision.findtext("pose"))
                mesh_uri = collision.findtext("geometry/mesh/uri")
                box = collision.findtext("geometry/box/size")
                if mesh_uri:
                    triangles = collada_triangles(SIMULATION / mesh_uri.removeprefix("file://"))
                    vertices = transform_vertices(triangles.reshape(-1, 3), matrix).reshape(-1, 3, 3)
                    pixels = np.round((vertices[:, :, :2] - origin) / mpp).astype(np.int32)
                    for triangle in pixels:
                        cv2.fillConvexPoly(mask, triangle, 1)
                    mesh_count += 1
                elif box:
                    size = np.fromstring(box, sep=" ")
                    corners = np.asarray(list(itertools.product((-0.5, 0.5), repeat=3))) * size
                    vertices = transform_vertices(corners, matrix)
                    pixels = np.round((vertices[:, :2] - origin) / mpp).astype(np.int32)
                    cv2.fillConvexPoly(mask, cv2.convexHull(pixels), 1)
                else:
                    raise ValueError(f"İşlenmeyen collision: {name}/{collision.get('name')}")
    if mesh_count != len(arena.SCENARIOS) * 4:
        raise ValueError(f"Dört materyal × üç bölge bekleniyor; mesh={mesh_count}")
    profile = load_profile("cx_teknofest_official")
    results = []
    for scenario, mask in masks.items():
        distance = cv2.distanceTransform(1 - mask, cv2.DIST_L2, cv2.DIST_MASK_PRECISE) * mpp
        geometry = arena.harita(profile["map_ids"][scenario], scenario)
        for road, path in geometry["paths"].items():
            pixels = np.round((np.asarray(path) + arena.HTAB_HALF) / mpp).astype(np.int32)
            path_mask = np.zeros_like(mask)
            cv2.polylines(path_mask, [pixels], False, 1, 1)
            samples = distance[path_mask.astype(bool)]
            if not len(samples):
                raise ValueError("Güzergâh örneklenmedi")
            minimum = float(samples.min())
            results.append({"scenario": scenario, "road": road,
                            "expected_clear": road == geometry["open"],
                            "observed_clear": minimum >= R_GEREKLI_M,
                            "minimum_clearance_m": round(minimum, 4)})
        cv2.imwrite(str(output / f"{scenario}_collision_mask.png"), mask * 255)
    result = {"mpp": mpp, "required_radius_m": R_GEREKLI_M, "paths": results,
              "all_match": all(row["expected_clear"] == row["observed_clear"] for row in results),
              "scope": "static collision XY projection along registered routes; not perception or vehicle execution"}
    (output / "geometry_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if not result["all_match"]:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    check(arguments.candidate, arguments.output)


if __name__ == "__main__":
    main()
