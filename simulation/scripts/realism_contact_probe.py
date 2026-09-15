"""NEDEN: Statik mesh'in gerçekten temas ürettiğini pozitif/negatif kontrolde sınar."""

import argparse
import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from realism_scene import SIMULATION, child


def prepare(candidate, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    source = ET.parse(candidate).find("world")
    mesh = source.find("model[@name='real_rubble_kolay_concrete']")
    path = SIMULATION / mesh.findtext("link/collision/geometry/mesh/uri").removeprefix("file://")
    dae = ET.parse(path)
    namespace = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    vertices = np.fromstring(dae.find(".//c:float_array[@id='positions-array']", namespace).text, sep=" ").reshape(-1, 3, 3)
    edges = vertices[:, 1:] - vertices[:, :1]
    normals = np.cross(edges[:, 0], edges[:, 1])
    magnitude = np.linalg.norm(normals, axis=1)
    centers = vertices.mean(axis=1)
    eligible = (normals[:, 2] / magnitude > 0.995) & (magnitude > 0.4) & (centers[:, 2] > 0.8)
    indices = np.flatnonzero(eligible)
    if not len(indices):
        raise ValueError("Temas probu için yeterince düz üst yüz yok")
    selected = indices[np.argmax(centers[indices, 2])]
    target = centers[selected]
    expectations = {"rubble_surface_z": float(target[2]), "radius": 0.075,
                    "rubble_xy": target[:2].tolist(), "ground_z": 0.0}
    for mode in ("positive", "negative"):
        root = ET.Element("sdf", version="1.6")
        world = child(root, "world", name="realism_contact")
        physics = child(world, "physics", type="ode")
        child(physics, "max_step_size", "0.001")
        child(physics, "real_time_update_rate", "1000")
        child(world, "gravity", "0 0 -9.8")
        for name in ("real_surroundings", "real_ground_kolay", "real_rubble_kolay_concrete"):
            if mode == "negative" and name.startswith("real_rubble_"):
                continue
            model = copy.deepcopy(source.find(f"model[@name='{name}']"))
            for link in model.findall("link"):
                for visual in list(link.findall("visual")):
                    link.remove(visual)
            world.append(model)
        for name, position in (("probe_ground", (-90, -35, 1.5)),
                               ("probe_rubble", (target[0], target[1], target[2] + 1.5))):
            model = child(world, "model", name=name)
            child(model, "pose", " ".join(map(str, position)) + " 0 0 0")
            link = child(model, "link", name="body")
            inertial = child(link, "inertial")
            child(inertial, "mass", "1")
            inertia = child(inertial, "inertia")
            for axis in ("ixx", "iyy", "izz"):
                child(inertia, axis, 0.4 * expectations["radius"] ** 2)
            collision = child(link, "collision", name="ball")
            child(child(child(collision, "geometry"), "sphere"), "radius", expectations["radius"])
            joint = child(model, "joint", name="vertical_guide", type="prismatic")
            child(joint, "parent", "world")
            child(joint, "child", "body")
            axis = child(joint, "axis")
            child(axis, "xyz", "0 0 1")
            limit = child(axis, "limit")
            child(limit, "lower", "-100")
            child(limit, "upper", "100")
        ET.ElementTree(root).write(output / f"{mode}.world", encoding="utf-8", xml_declaration=True)
    (output / "expected.json").write_text(json.dumps(expectations, indent=2))
    print(json.dumps(expectations))


def check(output):
    output = Path(output)
    expected = json.loads((output / "expected.json").read_text())
    observations = {}
    for mode in ("positive", "negative"):
        observations[mode] = {}
        for name in ("probe_ground", "probe_rubble"):
            values = np.fromstring((output / f"{mode}_{name}.pose").read_text(), sep=" ")
            if len(values) != 6 or not np.isfinite(values).all():
                raise ValueError(f"Eksik/geçersiz gerçek Gazebo pozu: {mode}/{name}")
            observations[mode][name] = values.tolist()
    radius = expected["radius"]
    checks = {
        "ground_positive": abs(observations["positive"]["probe_ground"][2] - radius) < 0.025,
        "ground_negative": abs(observations["negative"]["probe_ground"][2] - radius) < 0.025,
        "rubble_support": abs(observations["positive"]["probe_rubble"][2] - expected["rubble_surface_z"] - radius) < 0.15,
        "mutation_without_rubble_falls": observations["negative"]["probe_rubble"][2] < 0.15,
    }
    result = {"checks": checks, "observed": observations, "expected": expected,
              "scope": "vertically guided contact probes on one face/ground, NOT vehicle/whole-scene physics validation"}
    (output / "contact_result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "check"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--candidate", type=Path)
    arguments = parser.parse_args()
    if arguments.mode == "prepare":
        if arguments.candidate is None:
            parser.error("prepare için --candidate gerekli")
        prepare(arguments.candidate, arguments.output)
    else:
        check(arguments.output)


if __name__ == "__main__":
    main()
