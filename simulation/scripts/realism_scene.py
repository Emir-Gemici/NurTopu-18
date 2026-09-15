"""NEDEN: Kilitli/eski üreteci değiştirmeden ayrı, UV dokulu Gazebo aday sürümü üretir."""

import argparse
import copy
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

import arena
import world_generator
from realism_assets import MATERIALS, hollow_pipe, load_obj, texture, transform, transform_vertices, write_collada, write_material
from realism_support import SupportGrid, connected_parts, ground_mesh, terrain_height


SIMULATION = Path(__file__).resolve().parents[1]
RUBBLE_PREFIXES = ("deb_", "blk_", "chic_", "mic_", "micro_")


def child(parent, tag, text=None, **attributes):
    element = ET.SubElement(parent, tag, attributes)
    if text is not None:
        element.text = str(text)
    return element


def resource(path):
    return "file://" + str(Path(path).resolve().relative_to(SIMULATION))


def material_node(visual, directory, name):
    material = child(visual, "material")
    script = child(material, "script")
    child(script, "uri", resource(directory / f"{name}.material"))
    child(script, "uri", resource(directory))
    child(script, "name", "NavitasRealism/" + name)


def surface(collision, material):
    values = MATERIALS[material]
    node = child(collision, "surface")
    ode = child(child(node, "friction"), "ode")
    child(ode, "mu", values["mu"])
    child(ode, "mu2", values["mu"])
    child(child(node, "bounce"), "restitution_coefficient", values["restitution"])


def mesh_model(name, mesh_path, assets, material, pose="0 0 0 0 0 0", collidable=True):
    model = ET.Element("model", name=name)
    child(model, "static", "true")
    child(model, "pose", pose)
    link = child(model, "link", name="surface")
    visual = child(link, "visual", name="surface")
    geometry = child(visual, "geometry")
    child(child(geometry, "mesh"), "uri", resource(mesh_path))
    material_node(visual, assets, material)
    if collidable:
        collision = child(link, "collision", name="surface")
        collision.append(copy.deepcopy(geometry))
        surface(collision, material.split("_")[0])
    return model


def count(world):
    return {"models": len(world.findall("model")), "visuals": len(world.findall(".//visual")),
            "collisions": len(world.findall(".//collision"))}


def make_ground(world, assets, seed, profile):
    for model in list(world.findall("model")):
        name = model.get("name", "")
        if name == "ground_plane" or name.startswith(("gd_", "road_", "grid_")):
            world.remove(model)
    for index, scenario in enumerate(arena.SCENARIOS):
        zone = world_generator.make_zone(scenario, seed, harita_id=profile["map_ids"][scenario],
                                         profile=profile, terrain="textured")
        material = "asphalt_" + scenario
        image = texture(seed + index, "asphalt", size=2048, paths=zone["harita"]["paths"], extent=arena.HTAB)
        cv2.imwrite(str(assets / f"{material}.png"), image)
        write_material(assets / f"{material}.material", "NavitasRealism/" + material, f"{material}.png")
        points, faces = ground_mesh((zone["cx"], zone["cy"]))
        path = assets / f"{material}.dae"
        write_collada(path, points, faces, ground_extent=arena.HTAB)
        model = mesh_model("real_ground_" + scenario, path, assets, material,
                           f"{zone['cx']} {zone['cy']} 0 0 0 0")
        world.append(model)
    extent = arena.UB * 1.4
    points = [(-extent / 2, -extent / 2, 0), (extent / 2, -extent / 2, 0),
              (extent / 2, extent / 2, 0), (-extent / 2, extent / 2, 0)]
    path = assets / "soil_ground.dae"
    write_collada(path, points, [(0, 1, 2), (0, 2, 3)], ground_extent=extent)
    world.append(mesh_model("real_surroundings", path, assets, "soil"))


def batch_rubble(world, assets, supported=False, zones=None, seed=260822):
    batches = defaultdict(lambda: {"vertices": [], "triangles": []})
    manifest = []
    cache = {}
    fragments = []
    for model in list(world.findall("model")):
        if not model.get("name", "").startswith(RUBBLE_PREFIXES):
            continue
        if model.findtext("static") != "true":
            raise ValueError("Dinamik moloz statik birleştirmeye verilemez")
        model_matrix = transform(model.findtext("pose"))
        consumed = 0
        for link in model.findall("link"):
            link_matrix = model_matrix @ transform(link.findtext("pose"))
            for visual in list(link.findall("visual")):
                mesh = visual.find("geometry/mesh")
                if mesh is None:
                    continue
                uri = mesh.findtext("uri", "")
                if not uri.startswith("file://media/meshes/rubble/"):
                    continue
                source = SIMULATION / uri.removeprefix("file://")
                if source not in cache:
                    points, faces = load_obj(source)
                    cache[source] = {"mesh": (points, faces), "parts": connected_parts(points, faces),
                                     "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
                points, faces = cache[source]["mesh"]
                scale = np.fromstring(mesh.findtext("scale", "1 1 1"), sep=" ")
                if len(scale) != 3 or np.any(scale <= 0):
                    raise ValueError("Pozitif üç eksenli mesh ölçeği gerekli")
                matrix = link_matrix @ transform(visual.findtext("pose"))
                family = source.stem.split("_")[0]
                material = "brick" if family == "brick" else "timber" if family == "beam" else "concrete"
                parts = cache[source]["parts"] if supported else [(points, faces)]
                shape_override = None
                if family == "beam":
                    rgb = np.fromstring(visual.findtext("material/diffuse", "0.3 0.2 0.1 1"), sep=" ")[:3]
                    palettes = {"timber": world_generator._WOOD, "steel": world_generator._METAL}
                    material = min(palettes, key=lambda name: min(np.linalg.norm(rgb - color) for color in palettes[name]))
                    if supported and material == "steel":
                        parts = [hollow_pipe((points.min(axis=0), points.max(axis=0)))]
                        shape_override = "hollow_pipe_within_source_bounds"
                scenario = next((value for value in arena.SCENARIOS if value in model.get("name")), "extra")
                for component, (part_points, part_faces) in enumerate(parts):
                    transformed = transform_vertices(part_points * scale, matrix)
                    information = {"model": model.get("name"), "visual": visual.get("name"),
                                   "component": component, "family": "pipe" if shape_override else family,
                                   "material": material, "shape_override": shape_override,
                                   "source_mesh": str(source.relative_to(SIMULATION)),
                                   "source_sha256": cache[source]["sha256"],
                                   "source_world_transform": matrix.round(7).tolist(), "scale": scale.tolist(),
                                   "collision": "static triangle mesh, identical to visual",
                                   "dynamic_mass_inertia": "not applicable: static environment",
                                   "friction": MATERIALS[material], "expected": "blocked geometry"}
                    fragments.append((scenario, material, transformed, part_faces, information))
                link.remove(visual)
                collision = link.find(f"collision[@name='c{visual.get('name', '')[1:]}']")
                if collision is not None:
                    link.remove(collision)
                consumed += 1
        if consumed and not model.findall(".//visual"):
            world.remove(model)
    if not fragments:
        raise ValueError("Kaynak dünyada yeni moloz mesh'leri yok; eski kayıt yerine güncel üreteci kullanın")
    grids = {scenario: SupportGrid(center) for scenario, center in arena.ZONE_POS.items()} if supported else {}
    clearances = {}
    rng = np.random.default_rng(seed)
    if supported and zones:
        for scenario, zone in zones.items():
            paths = zone["harita"]["paths"]
            clearances[(scenario, "background")] = grids[scenario].clearance(paths.values(), zone["lane_w"])
            clearances[(scenario, "blocker")] = grids[scenario].clearance([paths[zone["road"]]], zone["lane_w"])
    anchors = defaultdict(list)
    if supported:
        fragments.sort(key=lambda fragment: float(fragment[2][:, 2].min()))
    for scenario, material, points, faces, information in fragments:
        original_center = points.mean(axis=0)
        horizontal_shift = [0.0, 0.0]
        if supported:
            if zones:
                kind = "blocker" if information["model"].startswith("blk_") else "background"
                points, horizontal_shift = grids[scenario].choose_position(points, clearances[(scenario, kind)], rng)
            points, information["support"] = grids[scenario].settle(points, faces)
            information["support"]["horizontal_shift_m"] = horizontal_shift
        else:
            information["support"] = {"status": "source_placement", "vertical_shift_m": 0}
        information["bounds_min"] = points.min(axis=0).round(6).tolist()
        information["bounds_max"] = points.max(axis=0).round(6).tolist()
        anchors[information["model"]].append((original_center, points.mean(axis=0)))
        batch = batches[(scenario, material)]
        offset = len(batch["vertices"])
        batch["vertices"].extend(points.tolist())
        batch["triangles"].extend((faces + offset).tolist())
        manifest.append(information)
    if supported:
        for model in world.findall("model"):
            candidates = anchors.get(model.get("name"))
            if not candidates:
                continue
            for link in model.findall("link"):
                matrix = transform(model.findtext("pose")) @ transform(link.findtext("pose"))
                for visual in link.findall("visual"):
                    pose = visual.find("pose")
                    if pose is None:
                        continue
                    values = np.fromstring(pose.text, sep=" ")
                    world_position = transform_vertices(values[None, :3], matrix)[0]
                    original, positioned = min(candidates, key=lambda pair: np.linalg.norm(pair[0] - world_position))
                    values[:3] += matrix[:3, :3].T @ (positioned - original)
                    pose.text = " ".join(f"{value:.7f}" for value in values)
    for (scenario, material), batch in sorted(batches.items()):
        path = assets / f"rubble_{scenario}_{material}.dae"
        write_collada(path, batch["vertices"], batch["triangles"], uv_scale=1.4)
        world.append(mesh_model(f"real_rubble_{scenario}_{material}", path, assets, material))
    return manifest


def place_barriers(world, zones):
    placements = []
    for scenario, zone in zones.items():
        geometry = zone["harita"]
        open_path = geometry["paths"][zone["road"]]
        for road, path in geometry["paths"].items():
            if road == zone["road"]:
                continue
            models = [world.find(f"model[@name='bar_{scenario}_{road}{suffix}']") for suffix in ("", "b")]
            if any(model is None for model in models):
                raise ValueError(f"Kapalı yol bariyeri eksik: {scenario}/{road}")
            sizes = [np.fromstring(model.findtext("link/collision/geometry/box/size"), sep=" ") for model in models]
            radius = max(float(np.linalg.norm(size[:2])) / 2 for size in sizes)
            selected = None
            for index in range(int(len(path) * 0.12), int(len(path) * 0.8)):
                position = np.asarray(path[index])
                if arena.dist_to_path(*position, open_path) < zone["lane_w"] / 2 + radius + 0.2:
                    continue
                if np.any(np.abs(position) + radius > arena.HTAB_HALF):
                    continue
                direction = np.asarray(path[index + 1]) - position
                selected = position, math.atan2(direction[1], direction[0]) + math.pi / 2
                break
            if selected is None:
                raise ValueError(f"Bariyer açık yolu kesmeden yerleşemiyor: {scenario}/{road}")
            position, yaw = selected
            world_position = position + np.asarray(arena.ZONE_POS[scenario])
            height = float(terrain_height(*world_position, arena.ZONE_POS[scenario]))
            for model in models:
                pose = model.find("pose")
                previous = np.fromstring(pose.text, sep=" ")
                updated = [*world_position, previous[2] + height, 0, 0, yaw]
                pose.text = " ".join(f"{value:.7f}" for value in updated)
                placements.append({"model": model.get("name"), "source_pose": previous.tolist(),
                                   "pose": updated, "reason": "closed-road barrier outside full open corridor"})
    return placements


def appearance(world, assets):
    scene = world.find("scene")
    scene.find("ambient").text = "0.40 0.43 0.48 1"
    scene.find("background").text = "0.68 0.76 0.84 1"
    sun = world.find("light[@name='sun']")
    sun.find("diffuse").text = "0.83 0.80 0.74 1"
    sun.find("direction").text = "-0.45 0.35 -0.82"
    physics = world.find("physics")
    gravity = physics.find("gravity")
    if gravity is not None:
        physics.remove(gravity)
        world.append(gravity)
    for model in list(world.findall("model")):
        name = model.get("name", "")
        if name.startswith(("iha_view_", "ika_view_")):
            world.remove(model)
        if name.startswith("brd_"):
            for color in model.findall(".//material/ambient") + model.findall(".//material/diffuse"):
                color.text = "0.55 0.51 0.39 1"
        if name.startswith("bar_"):
            for visual in model.findall(".//visual"):
                old_material = visual.find("material")
                if old_material is not None:
                    visual.remove(old_material)
                material_node(visual, assets, "concrete")
    gui = world.find("gui/camera/pose")
    if gui is not None:
        gui.text = "-124 -32 22 0 0.42 0.76"


def build(output, seed=260822, supported=True):
    output = Path(output).resolve()
    output.relative_to(SIMULATION)
    output.mkdir(parents=True, exist_ok=False)
    assets = output / "assets"
    assets.mkdir()
    source_text, _ = world_generator.build_world(seed, "kolay", record=False,
                                                     profile_id="cx_teknofest_official", terrain="textured")
    (output / "before.world").write_text(source_text)
    root = ET.fromstring(source_text)
    world = root.find("world")
    before = count(world)
    profile = world_generator.load_profile("cx_teknofest_official")
    for index, material in enumerate(MATERIALS):
        cv2.imwrite(str(assets / f"{material}.png"), texture(seed + 100 + index, material))
        write_material(assets / f"{material}.material", "NavitasRealism/" + material,
                       f"{material}.png", metallic=material == "steel")
    make_ground(world, assets, seed, profile)
    zones = {scenario: world_generator.make_zone(scenario, seed, harita_id=profile["map_ids"][scenario],
                                                 profile=profile, terrain="textured") for scenario in arena.SCENARIOS}
    objects = batch_rubble(world, assets, supported=supported, zones=zones, seed=seed)
    barriers = place_barriers(world, zones)
    appearance(world, assets)
    ET.indent(root)
    ET.ElementTree(root).write(output / "candidate.world", encoding="utf-8", xml_declaration=True)
    sources = [Path(world_generator.__file__), Path(arena.__file__), Path(__file__),
               SIMULATION / "scripts/realism_assets.py", SIMULATION / "scripts/realism_support.py",
               SIMULATION / "scenarios/cx_teknofest_official.json"]
    manifest = {"schema": 1, "seed": seed, "profile": "realism_candidate_not_competition_approved",
                "before": before, "after": count(world), "objects": objects, "barriers": barriers,
                "source_world_sha256": hashlib.sha256(source_text.encode()).hexdigest(),
                "sources": {str(path.relative_to(SIMULATION)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                "material_parameters": "engineering defaults, NOT measured on real robot/surface",
                "limits": ["No flight/tyre calibration or mission-success claim",
                           "Static rubble triangle contacts; no collapse dynamics",
                           "Support uses a 6 cm vertical sampling grid; rigid-body equilibrium and subgrid contacts are not proven",
                           "New ground contact and visual distribution require perception/route revalidation",
                           "Three training zones preserved; not a certified replica of the competition arena"],
                "assets": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(assets.iterdir())}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    summary = {"output": str(output), "before": before, "after": count(world), "rubble_pieces": len(objects),
               "supported": supported, "highest_rubble_m": max(item["bounds_max"][2] for item in objects)}
    print(json.dumps(summary, ensure_ascii=False))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=260822)
    parser.add_argument("--retain-placement", action="store_true", help="Destek yerleştirmesini atla; kaynak pozlarını koru")
    arguments = parser.parse_args()
    build(arguments.output, arguments.seed, supported=not arguments.retain_placement)


if __name__ == "__main__":
    main()
