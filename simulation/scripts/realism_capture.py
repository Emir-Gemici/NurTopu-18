"""NEDEN: Aynı kameralarda gerçek Gazebo öncesi/sonrası çekimi; eski videoya düşmez."""

import argparse
import copy
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import world_generator


SIMULATION = Path(__file__).resolve().parents[1]
CAMERAS = {
    "oblique": (-126, -36, 24, 0, 0.42, 0.785398),
    "top": (-90, 0, 66, 0, math.pi / 2, math.pi / 2),
    "detail": (-112, -26, 6.5, 0, 0.20, 0.94),
}


def prepare(source, output, label):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = ET.parse(source).getroot()
    world = root.find("world")
    for include in list(world.findall("include")):
        uri = include.findtext("uri", "")
        if not uri.startswith("model://"):
            raise ValueError(f"Yerel olmayan model: {uri}")
        model_source = SIMULATION / "models" / uri.removeprefix("model://") / "model.sdf"
        model = copy.deepcopy(ET.parse(model_source).getroot().find("model"))
        model.set("name", include.findtext("name", model.get("name")))
        pose = include.find("pose")
        if pose is not None:
            old_pose = model.find("pose")
            if old_pose is not None:
                model.remove(old_pose)
            model.append(copy.deepcopy(pose))
        world.remove(include)
        world.append(model)
    removed_sensors = 0
    for parent in list(root.iter()):
        for node in list(parent):
            if node.tag in ("sensor", "plugin"):
                removed_sensors += node.tag == "sensor"
                parent.remove(node)
    for model in world.findall("model"):
        static = model.find("static")
        if static is None:
            static = ET.SubElement(model, "static")
        static.text = "true"
    physics = world.find("physics")
    gravity = physics.find("gravity")
    if gravity is not None:
        physics.remove(gravity)
        world.append(gravity)
    for name, pose in CAMERAS.items():
        camera = ET.fromstring(world_generator._save_camera_model(
            "audit_" + name, "/evidence/" + name, *pose, fov=1.10, width=1280, height=960))
        camera.find("link/sensor/update_rate").text = "0.5"
        world.append(camera)
    ET.ElementTree(root).write(output / "capture.world", encoding="utf-8", xml_declaration=True)
    (output / "capture.json").write_text(json.dumps({
        "source": str(source.resolve()), "label": label, "cameras": CAMERAS,
        "mode": "STATIC VISUAL AUDIT, not a mission/sensor/physics validation",
        "removed_operational_sensors": removed_sensors,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--label", required=True)
    arguments = parser.parse_args()
    prepare(arguments.source, arguments.output, arguments.label)


if __name__ == "__main__":
    main()
