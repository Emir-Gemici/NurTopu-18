#!/usr/bin/env python3
"""Competition geometry and deterministic-generation contract tests."""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock


SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))

import arena
import iha_haritala
import iha_perceive
import scenario_profiles
import world_generator


def _resolve_gazebo_file_uri(uri, resource_roots):
    prefix = "file://"
    if not uri.startswith(prefix):
        raise AssertionError(f"not a file URI: {uri}")
    rel = uri[len(prefix):]
    if rel.startswith("/"):
        candidate = Path(rel)
        return candidate if candidate.is_file() else None
    for root in resource_roots:
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return None


class ScenarioContractTest(unittest.TestCase):
    def profile_ids(self):
        return ["baseline"] + scenario_profiles.available_profiles()

    def test_profiles_validate(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            self.assertEqual(set(profile["map_ids"]), set(arena.SCENARIOS))

    def test_three_distinct_50m_htab_inside_300m_ub(self):
        boxes = []
        for name, (cx, cy) in world_generator.ZONE_POS.items():
            box = (cx - 25.0, cy - 25.0, cx + 25.0, cy + 25.0)
            boxes.append((name, box))
            self.assertGreaterEqual(box[0], -arena.UB_HALF)
            self.assertGreaterEqual(box[1], -arena.UB_HALF)
            self.assertLessEqual(box[2], arena.UB_HALF)
            self.assertLessEqual(box[3], arena.UB_HALF)
        for i, (_, a) in enumerate(boxes):
            for _, b in boxes[i + 1:]:
                overlap_x = min(a[2], b[2]) - max(a[0], b[0])
                overlap_y = min(a[3], b[3]) - max(a[1], b[1])
                self.assertFalse(overlap_x > 0 and overlap_y > 0)

    def test_every_zone_has_three_routes_one_open_and_two_blocked(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            for level in arena.SCENARIOS:
                H = arena.harita(profile["map_ids"][level], level)
                self.assertEqual(set(H["paths"]), {1, 2, 3})
                self.assertIn(H["open"], (1, 2, 3))
                self.assertGreaterEqual(min(arena._kivrim(H["paths"][r]) for r in (1, 2, 3)),
                                        arena.MIN_KIVRIM)

    def test_generated_world_contains_all_zones_and_official_markers(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            world, _ = world_generator.build_world(profile["seed"], profile["active_zone"],
                                                    record=True, profile_id=profile_id)
            self.assertNotIn("nan", world.lower())
            root = ET.fromstring(world)
            model_names = [m.attrib["name"] for m in root.findall("./world/model")]
            include_names = [n.text for n in root.findall("./world/include/name")]
            names = model_names + include_names
            self.assertEqual(len(names), len(set(names)), f"yinelenen model adı: {profile_id}")
            for level in arena.SCENARIOS:
                self.assertIn(f"gd_{level}", model_names)
                self.assertTrue(any(n.startswith(f"kb_{level}_") for n in model_names))
                self.assertIn(f"hbpad_{level}", model_names)
                for road in (1, 2, 3):
                    self.assertTrue(any(n.startswith(f"road_{level}_{road}_") for n in model_names))
            self.assertIn("judge_camp_floor", model_names)
            self.assertIn("iha_view_footprint", model_names)
            self.assertIn(f"ika_view_{profile['active_zone']}_center", model_names)
            self.assertIn("<size>9.000 9.000 0.020</size>", world)
            self.assertIn("<size>2.000 2.000 0.040</size>", world)

    def test_kb_markers_are_1m_outlines_with_clear_centers(self):
        profile = scenario_profiles.load_profile("cx_teknofest_official")
        world, _ = world_generator.build_world(profile["seed"], profile["active_zone"],
                                                record=True, profile_id=profile["id"])
        root = ET.fromstring(world)
        all_models = root.findall("./world/model")

        for level in arena.SCENARIOS:
            H = arena.harita(profile["map_ids"][level], level)
            zone_x, zone_y = world_generator.ZONE_POS[level]
            kb_x = zone_x + H["kb"][0]
            kb_y = zone_y + H["kb"][1]
            prefix = f"kb_{level}_"
            markers = [m for m in all_models if m.attrib["name"].startswith(prefix)]

            self.assertEqual(
                {m.attrib["name"] for m in markers},
                {f"{prefix}{side}" for side in ("N", "S", "W", "E")},
            )
            self.assertIsNone(root.find(f"./world/model[@name='kb_{level}']"))

            bounds = []
            sizes = []
            for marker in markers:
                pose = [float(v) for v in marker.findtext("./pose").split()]
                visual_size = [float(v) for v in marker.findtext(
                    "./link/visual/geometry/box/size").split()]
                collision_size = [float(v) for v in marker.findtext(
                    "./link/collision/geometry/box/size").split()]
                self.assertEqual(visual_size, collision_size)
                self.assertEqual(pose[3:], [0.0, 0.0, 0.0])

                x0 = pose[0] - visual_size[0] / 2.0
                x1 = pose[0] + visual_size[0] / 2.0
                y0 = pose[1] - visual_size[1] / 2.0
                y1 = pose[1] + visual_size[1] / 2.0
                bounds.append((x0, x1, y0, y1))
                sizes.append(tuple(visual_size))
                self.assertFalse(x0 <= kb_x <= x1 and y0 <= kb_y <= y1,
                                 f"KB merkezi görsel şeritte kaldı: {marker.attrib['name']}")

            self.assertEqual(sorted(sizes), sorted([
                (1.0, 0.12, 0.04), (1.0, 0.12, 0.04),
                (0.12, 0.76, 0.04), (0.12, 0.76, 0.04),
            ]))
            outer_x0 = min(b[0] for b in bounds)
            outer_x1 = max(b[1] for b in bounds)
            outer_y0 = min(b[2] for b in bounds)
            outer_y1 = max(b[3] for b in bounds)
            self.assertAlmostEqual(outer_x1 - outer_x0, 1.0, places=6)
            self.assertAlmostEqual(outer_y1 - outer_y0, 1.0, places=6)
            self.assertAlmostEqual((outer_x0 + outer_x1) / 2.0, kb_x, delta=0.001)
            self.assertAlmostEqual((outer_y0 + outer_y1) / 2.0, kb_y, delta=0.001)

    def test_profile_environment_and_terrain_controls_reach_sdf(self):
        profile = scenario_profiles.load_profile("cc_night_fog")
        world, _ = world_generator.build_world(profile["seed"], profile["active_zone"],
                                                record=True, profile_id=profile["id"])
        root = ET.fromstring(world)
        self.assertEqual(root.findtext("./world/wind/linear_velocity"), "0.5 0.2 0.0")
        self.assertEqual(root.findtext("./world/model[@name='ground_plane']"
                                       "/link/collision/surface/friction/ode/mu"), "0.750")
        ground_material = root.find("./world/model[@name='ground_plane']/link/visual/material")
        self.assertIsNotNone(ground_material)
        self.assertIsNotNone(ground_material.find("./script"))
        self.assertIsNone(ground_material.find("./ambient"))
        self.assertIsNone(ground_material.find("./diffuse"))
        fallback = ET.fromstring(
            world_generator._material(*profile["environment"]["ground_color"])
        )
        self.assertEqual(fallback.findtext("./ambient"), "0.15 0.14 0.13 1")

        level = profile["active_zone"]
        chicanes = [m for m in root.findall("./world/model")
                    if m.attrib["name"].startswith(f"chic_{level}_")]
        chicane_groups = {
            m.attrib["name"]
            for m in chicanes
        }
        self.assertEqual(len(chicane_groups), profile["terrain"]["chicane_count"])

        size = chicanes[0].findtext("./link/visual/geometry/box/size")
        self.assertIsNotNone(size)
        rubble_h = float(size.split()[2])
        self.assertGreaterEqual(rubble_h, profile["terrain"]["rubble_height_multiplier"])

    def test_rubble_is_multi_piece_with_visual_variance(self):
        profile = scenario_profiles.load_profile("cx_teknofest_official")
        world, _ = world_generator.build_world(profile["seed"], "kolay",
                                               record=True, profile_id=profile["id"])
        root = ET.fromstring(world)
        rubble = [m for m in root.findall("./world/model")
                  if re.match(r"(blk|deb|chic)_", m.attrib["name"])]
        groups = {}
        colors = set()
        heights = []
        for model in rubble:
            name = model.attrib["name"]
            self.assertNotRegex(name, r"_p\d+$")
            self.assertEqual(model.findtext("./static"), "true")
            visuals = model.findall("./link/visual")
            collisions = model.findall("./link/collision")
            self.assertEqual(len(visuals), len(collisions))
            groups[name] = len(visuals)
            for visual in visuals:
                self.assertRegex(visual.attrib["name"], r"^vis_\d+$")
                size = visual.findtext("./geometry/box/size")
                ambient = visual.findtext("./material/ambient")
                self.assertIsNotNone(size)
                self.assertIsNotNone(ambient)
                heights.append(round(float(size.split()[2]), 3))
                colors.add(tuple(float(v) for v in ambient.split()[:3]))

        expected_clusters = 0
        for level in arena.SCENARIOS:
            H = arena.harita(profile["map_ids"][level], level)
            lane_w = world_generator.DIFF[level]["lane_w"]
            blocked_roads = 2
            blockers = blocked_roads * world_generator.DIFF[level]["tikama_n"] \
                * max(6, int(lane_w * 1.6))
            expected_clusters += blockers + world_generator.DIFF[level]["debris_n"] \
                + profile["terrain"]["chicane_count"]
            self.assertIn(H["open"], (1, 2, 3))

        self.assertEqual(len(groups), expected_clusters)
        self.assertGreaterEqual(min(groups.values()), 4)
        self.assertGreaterEqual(max(groups.values()), 6)
        self.assertLessEqual(max(groups.values()), 10)
        self.assertGreaterEqual(len(colors), 24)
        self.assertGreater(max(heights) - min(heights), 0.8)

    def test_official_ground_uses_named_real_arena_asphalt(self):
        profile = scenario_profiles.load_profile("cx_teknofest_official")
        world, _ = world_generator.build_world(profile["seed"], "kolay",
                                               record=True, profile_id=profile["id"])
        root = ET.fromstring(world)
        for name in ("ground_plane", "gd_kolay", "gd_orta", "gd_zor", "road_kolay_1_0"):
            model = root.find(f"./world/model[@name='{name}']")
            self.assertIsNotNone(model, name)
            material = model.find("./link/visual/material")
            self.assertIsNotNone(material, name)
            script = material.find("./script")
            self.assertIsNotNone(script, name)
            self.assertEqual(script.findtext("./uri"), world_generator.ASPHALT_MATERIAL_URI)
            self.assertEqual(script.findtext("./name"), world_generator.ASPHALT_MATERIAL_NAME)
            self.assertIsNone(material.find("./ambient"), name)
            self.assertIsNone(material.find("./diffuse"), name)
            self.assertEqual(material.findtext("./specular"), "0.04 0.04 0.04 1")

        self.assertEqual(profile["environment"]["ground_color"],
                         list(world_generator.ASPHALT_RGB))
        self.assertEqual(world_generator.ASPHALT_MATERIAL_URI,
                         "file://media/materials/scripts/navitas_asphalt.material")
        host_record_script = (SIM / "docker/record.sh").read_text(encoding="utf-8")
        container_record_script = (
            SIM / "docker/record_in_container.sh"
        ).read_text(encoding="utf-8")
        resource_root_match = re.search(
            r'^GAZEBO_RESOURCE_ROOT="([^"\n]+)"',
            host_record_script,
            re.MULTILINE,
        )
        self.assertIsNotNone(resource_root_match)
        container_resource_root = Path(resource_root_match.group(1))
        self.assertTrue(container_resource_root.is_absolute())
        self.assertNotEqual(container_resource_root, Path("/sim"))
        self.assertEqual(
            (host_record_script + container_record_script).count("/navitas_res"),
            1,
        )
        self.assertIn(
            '-v "$SIM/media":"$GAZEBO_RESOURCE_ROOT/media":z',
            host_record_script,
        )
        self.assertIn(
            '-e NAVITAS_GAZEBO_RESOURCE_ROOT="$GAZEBO_RESOURCE_ROOT"',
            host_record_script,
        )
        self.assertIn(
            'GAZEBO_RESOURCE_ROOT="${NAVITAS_GAZEBO_RESOURCE_ROOT:',
            container_record_script,
        )
        self.assertIn(
            'export GAZEBO_RESOURCE_PATH="$GAZEBO_RESOURCE_ROOT${GAZEBO_RESOURCE_PATH:+:$GAZEBO_RESOURCE_PATH}"',
            container_record_script,
        )
        # Konteynerde <kök>/media, host'taki gerçek simulation/media dizinidir.
        self.assertEqual(container_resource_root / "media", Path("/navitas_res/media"))
        self.assertTrue((SIM / "media").is_dir())
        resource_roots = [SIM]
        material_path = _resolve_gazebo_file_uri(
            world_generator.ASPHALT_MATERIAL_URI,
            resource_roots,
        )
        self.assertIsNotNone(material_path)
        texture_dir = SIM / "media/materials/textures"
        material_text = material_path.read_text(encoding="utf-8")
        # SÖZLEŞME, sihirli sayı DEĞİL. Materyalin ambient/diffuse kazançları
        # render zeminini ölçülmüş saha hedefine (BGR [154,130,109]) yaklaştırmak
        # için KALİBRE edilir; sayılar yeniden ölçüldükçe değişir. Testin
        # koruduğu şey kalibrasyonun BOZULMAMASI gereken yapısal özellikleridir:
        # adlandırılmış materyal, taşınabilir düz dosya adlı doku, ambient==diffuse
        # (tek kazanç vektörü, ışıklandırmadan bağımsız aynı renk) ve pozitif,
        # aşırı-parlatmayan (<=1) kanal kazançları.
        self.assertIn(f"material {world_generator.ASPHALT_MATERIAL_NAME}",
                      material_text)

        def _rgb_kazanc(anahtar):
            eslesme = re.search(
                rf"^\s*{anahtar}\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\b",
                material_text,
                re.MULTILINE,
            )
            self.assertIsNotNone(eslesme, anahtar)
            return tuple(float(v) for v in eslesme.groups())

        ambient = _rgb_kazanc("ambient")
        diffuse = _rgb_kazanc("diffuse")
        # ambient ile diffuse AYNI kazanç vektörü olmalı: farklılarsa zemin rengi
        # sahnedeki ışık miktarına göre kayar ve kalibrasyon anlamını yitirir.
        self.assertEqual(ambient, diffuse)
        for kanal, deger in zip("RGB", ambient):
            self.assertGreater(deger, 0.0, kanal)
            self.assertLessEqual(deger, 1.0, kanal)

        olcek = re.search(r"^\s*scale\s+([\d.]+)\s+([\d.]+)\s*$",
                          material_text, re.MULTILINE)
        self.assertIsNotNone(olcek)
        for deger in olcek.groups():
            self.assertGreater(float(deger), 0.0)

        texture_ref = re.search(r"^\s*texture\s+(\S+)\s*$", material_text, re.MULTILINE)
        self.assertIsNotNone(texture_ref)
        # Doku adı DÜZ dosya adı olmalı: göreli/mutlak yol yazılırsa Ogre'nin
        # kayıtlı textures dizininde bulunamaz (konteynerde sessizce beyaz zemin).
        self.assertEqual(Path(texture_ref.group(1)).name, texture_ref.group(1))
        registered_texture_dirs = [root / "media/materials/textures"
                                   for root in resource_roots]
        resolved_texture = next(
            (directory / texture_ref.group(1)
             for directory in registered_texture_dirs
             if (directory / texture_ref.group(1)).is_file()),
            None,
        )
        self.assertIsNotNone(resolved_texture)
        self.assertEqual(resolved_texture.parent.resolve(), texture_dir.resolve())

        fallback = ET.fromstring(
            world_generator._material(*world_generator.ASPHALT_RGB)
        )
        self.assertEqual(fallback.findtext("./ambient"), "0.51 0.56 0.62 1")
        self.assertEqual(fallback.findtext("./diffuse"), "0.51 0.56 0.62 1")
        self.assertEqual(fallback.findtext("./specular"), "0.04 0.04 0.04 1")
        self.assertIsNone(fallback.find("./script"))

        # Yesil sinir bandi T4'te olculmeden kaldirilmadi; ayri katman oldugu kilitlenir.
        border = root.find("./world/model[@name='brd_kolay_N']")
        self.assertIsNotNone(border)
        self.assertEqual(border.findtext("./link/visual/material/ambient"),
                         "0.10 0.75 0.20 1")

    def test_parachute_uses_vented_mesh_and_realistic_suspension_lines(self):
        profile = scenario_profiles.load_profile("cx_teknofest_official")
        world, zone = world_generator.build_world(
            profile["seed"], "kolay", record=True, profile_id=profile["id"]
        )
        root = ET.fromstring(world)
        resource_roots = [SIM]

        for variant in ("packed", "partial", "full"):
            name = f"parachute_{variant}"
            model = root.find(f"./world/model[@name='{name}']")
            self.assertIsNotNone(model, name)
            canopy = model.find("./link/visual[@name='canopy_mesh']")
            self.assertIsNotNone(canopy, name)
            self.assertEqual(canopy.findtext("./cast_shadows"), "true")
            self.assertIsNone(canopy.find("./geometry/cylinder"), name)
            uri = canopy.findtext("./geometry/mesh/uri")
            self.assertEqual(uri, world_generator.PARACHUTE_MESH_URIS[variant])
            self.assertIsNotNone(_resolve_gazebo_file_uri(uri, resource_roots), uri)

            line_visuals = [
                visual for visual in model.findall("./link/visual")
                if visual.attrib["name"].startswith("line_")
            ]
            self.assertEqual(len(line_visuals), world_generator.PARACHUTE_GORE_COUNT)
            self.assertEqual(
                {float(v.findtext("./geometry/cylinder/radius")) for v in line_visuals},
                {world_generator.PARACHUTE_LINE_RADIUS_M},
            )

        full_path = _resolve_gazebo_file_uri(
            world_generator.PARACHUTE_MESH_URIS["full"], resource_roots
        )
        obj_lines = full_path.read_text(encoding="ascii").splitlines()
        vertices = [
            tuple(float(value) for value in line.split()[1:])
            for line in obj_lines if line.startswith("v ")
        ]
        triangles = [line for line in obj_lines if line.startswith("f ")]
        radial = [math.hypot(x, y) for x, y, _ in vertices]
        self.assertGreaterEqual(2.0 * max(radial), 2.2)
        self.assertLessEqual(2.0 * max(radial), 2.6)
        self.assertGreater(min(radial), 0.10)  # merkez verteksi yok: vent gerçekten açık
        self.assertEqual(len(triangles), 2176)
        self.assertIn("usemtl ripstop_orange", obj_lines)
        self.assertIn("usemtl ripstop_ivory", obj_lines)

        plugin = root.find("./world/plugin[@name='navitas_anim']")
        self.assertIsNotNone(plugin)
        plugin_names = {m.attrib["name"] for m in plugin.findall("./model")}
        self.assertTrue(
            {"parachute_packed", "parachute_partial", "parachute_full"}
            <= plugin_names
        )
        packed_wps = plugin.findall("./model[@name='parachute_packed']/waypoint")
        full_wps = plugin.findall("./model[@name='parachute_full']/waypoint")
        packed_first_visible = min(
            float(w.text.split()[0]) for w in packed_wps
            if float(w.text.split()[3]) > -10.0
        )
        full_first_visible = min(
            float(w.text.split()[0]) for w in full_wps
            if float(w.text.split()[3]) > -10.0
        )
        self.assertAlmostEqual(
            full_first_visible - packed_first_visible,
            world_generator.PARACHUTE_INFLATION_TIME_S,
            delta=0.011,
        )
        self.assertGreaterEqual(full_first_visible - packed_first_visible, 0.8)
        self.assertLessEqual(full_first_visible - packed_first_visible, 1.2)

        fp = world_generator.iha_flight(zone["cx"], zone["cy"], profile)
        base = world_generator._timed_flight(fp)
        deploy_i = next(i for i, point in enumerate(fp) if point[3] == "parasut")
        deploy_t, land_t = base[deploy_i][0], base[-1][0]
        iha_sway = world_generator._sway_trajectory(
            base, deploy_t, land_t, world_generator.PARACHUTE_IHA_SWAY_M
        )
        offsets = []
        for tt, x, y, z, _ in iha_sway:
            bx, by, bz, _ = world_generator._sample_timed(base, tt)
            offsets.append(math.hypot(x - bx, y - by))
            self.assertAlmostEqual(z, bz, places=9)
        self.assertGreater(max(offsets), 0.25)
        self.assertLessEqual(max(offsets), world_generator.PARACHUTE_IHA_SWAY_M)
        self.assertAlmostEqual(offsets[-1], 0.0, places=9)

    def test_arena_texture_is_exact_mirrored_c_crop(self):
        import cv2
        import numpy as np

        source = cv2.imread(str(
            SIM.parent / "data/arena_kompozit/images/train/"
            "whatsapp_video_2026_07_30_at_11_44_03_frame_000000_000000000_cp_00.jpg"
        ))
        texture_path = SIM / "media/materials/textures/asphalt_arena.png"
        texture = cv2.imread(str(texture_path))
        self.assertIsNotNone(source)
        self.assertIsNotNone(texture)
        self.assertEqual(texture.shape, (960, 960, 3))
        self.assertLessEqual(texture_path.stat().st_size, 1024 * 1024)

        crop = source[300:420, 600:720]
        mirrored_x = np.concatenate((crop, crop[:, ::-1]), axis=1)
        seamless_cell = np.concatenate((mirrored_x, mirrored_x[::-1, :]), axis=0)
        expected = np.tile(seamless_cell, (4, 4, 1))
        np.testing.assert_array_equal(texture, expected)

    def test_iha_perceive_default_is_registry_v32_with_sha(self):
        registry = json.loads((SIM.parent / "config/model_registry.json").read_text(
            encoding="utf-8"))
        profile = registry["profiles"]["competition_v32"]
        self.assertEqual(iha_perceive.DEFAULT_MODEL_PROFILE, "competition_v32")
        self.assertEqual(iha_perceive.DEFAULT_MODEL,
                         SIM.parent / "models/navitas_seg_v32_best.pt")
        self.assertEqual(profile["classes"], {"0": "traversable", "1": "blocked"})
        self.assertEqual(iha_perceive.DEFAULT_MODEL_PROVENANCE,
                         {"seg_model": str(iha_perceive.DEFAULT_MODEL.resolve()),
                          "seg_model_sha256": profile["sha256"]})
        self.assertEqual(registry["profiles"]["competition"]["sha256"],
                         "e00f6b8e25dd65604755c3cead7840aeb0f9a0ff74fee45e8f5fe9dbf1dd438b")

    def test_teknofest_official_profile_has_required_static_geometry(self):
        profile = scenario_profiles.load_profile("cx_teknofest_official")
        world, zone = world_generator.build_world(profile["seed"], profile["active_zone"],
                                                  record=True, profile_id=profile["id"])
        again, _ = world_generator.build_world(profile["seed"], profile["active_zone"],
                                               record=True, profile_id=profile["id"])
        self.assertEqual(world, again)
        root = ET.fromstring(world)
        model_names = {m.attrib["name"] for m in root.findall("./world/model")}
        include_names = {n.text for n in root.findall("./world/include/name")}
        self.assertIn("catapult_main", include_names)
        self.assertIn("landing", model_names)
        self.assertIn("landing_cross_x", model_names)
        self.assertIn("judge_camp_floor", model_names)
        self.assertIn("iha_view_footprint", model_names)
        self.assertIn("launch", model_names)
        self.assertIn("ub_N", model_names)
        self.assertIn("ub_S", model_names)
        self.assertIn("ub_W", model_names)
        self.assertIn("ub_E", model_names)
        self.assertIn("<size>300.000 0.600 1.500</size>", world)
        self.assertIn("<size>50.000 50.000 0.020</size>", world)
        self.assertIn("<size>9.000 9.000 0.020</size>", world)
        self.assertIn("<size>6.000 6.000 0.020</size>", world)
        self.assertIn("<size>2.000 2.000 0.040</size>", world)
        self.assertIn("<ambient>0.90 0.02 0.02 1</ambient>", world)
        self.assertEqual(zone["cx"], world_generator.ZONE_POS[profile["active_zone"]][0])
        for level in arena.SCENARIOS:
            H = arena.harita(profile["map_ids"][level], level)
            blocked = [road for road in (1, 2, 3) if road != H["open"]]
            self.assertEqual(len(blocked), 2)
            for road in blocked:
                self.assertIn(f"bar_{level}_{road}", model_names)
                self.assertTrue(
                    any(name.startswith(f"blk_{level}_{road}_") for name in model_names))

    def test_flight_stays_in_ub_and_lands_in_9m_pad(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            level = profile["active_zone"]
            cx, cy = world_generator.ZONE_POS[level]
            flight = world_generator.iha_flight(cx, cy, profile)
            for x, y, z, _ in flight:
                self.assertLessEqual(abs(x), arena.UB_HALF)
                self.assertLessEqual(abs(y), arena.UB_HALF)
                self.assertGreaterEqual(z, 0.0)
            lx, ly, _, _ = flight[-1]
            self.assertLessEqual(abs(lx - (cx + 32.0)), 4.5)
            self.assertLessEqual(abs(ly - cy), 4.5)

    def test_generation_is_deterministic(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            args = (profile["seed"], profile["active_zone"])
            one, _ = world_generator.build_world(*args, record=True, profile_id=profile_id)
            two, _ = world_generator.build_world(*args, record=True, profile_id=profile_id)
            self.assertEqual(one, two)

    def test_cli_uses_profile_seed_and_reports_actual_map(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "world.sdf"
                result = subprocess.run(
                    [sys.executable, str(SIM / "scripts" / "world_generator.py"),
                     "--profile", profile_id, "--output", str(out)],
                    check=True, text=True, capture_output=True)
                self.assertIn(f"SEED={profile['seed']}", result.stdout)
                self.assertIn(f"MAP={profile['map_ids'][profile['active_zone']]}", result.stdout)
                self.assertIn(
                    f"SCAN_ALTITUDE_M={profile['flight']['scan_altitude_m']}", result.stdout)

    def test_aftershock_barrier_is_dynamic_and_gravity_free(self):
        profile = scenario_profiles.load_profile("cx_aftershock_dynamic")
        world, _ = world_generator.build_world(profile["seed"], profile["active_zone"],
                                                record=True, profile_id=profile["id"])
        root = ET.fromstring(world)
        barrier = root.find("./world/model[@name='aftershock_barrier']")
        self.assertIsNotNone(barrier)
        self.assertIsNone(barrier.find("static"))
        self.assertEqual(barrier.findtext("./link/gravity"), "false")
        self.assertEqual(barrier.findtext("./link/kinematic"), "true")

    def test_explicit_map_override_is_effective(self):
        profile = scenario_profiles.load_profile("cx_glare_perspective")
        _, zone = world_generator.build_world(profile["seed"], profile["active_zone"],
                                              harita_id=999, profile_id=profile["id"])
        self.assertEqual(zone["harita_id"], 999)

    def test_unknown_profile_fields_fail_fast(self):
        with self.assertRaisesRegex(ValueError, "bilinmeyen alan"):
            scenario_profiles._reject_unknown(scenario_profiles.DEFAULT_PROFILE,
                                              {"environment": {"ambiant": [1, 1, 1, 1]}})

    def load_from_text(self, tmp, profile_id, text):
        """profile_id.json'ı geçici bir profil dizinine yazıp yükler."""
        (Path(tmp) / f"{profile_id}.json").write_text(text, encoding="utf-8")
        with mock.patch.object(scenario_profiles, "PROFILE_DIR", Path(tmp)):
            return scenario_profiles.load_profile(profile_id)

    def test_malformed_profile_json_raises_valueerror_with_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, r"bozuk\.json.*ayrıştırılamadı"):
                self.load_from_text(tmp, "bozuk", "{ not json")

    def test_non_object_profile_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "JSON nesnesi olmalı"):
                self.load_from_text(tmp, "liste", "[1, 2, 3]")

    def test_wrong_typed_fields_raise_valueerror_not_typeerror(self):
        bad_id = dict(scenario_profiles.DEFAULT_PROFILE, id=7)
        with self.assertRaisesRegex(ValueError, "profile id metin olmalı"):
            scenario_profiles.validate_profile(bad_id)
        cases = {
            "arazi": ({"id": "arazi", "terrain": {"debris_multiplier": "cok"}},
                      r"terrain\.debris_multiplier: sayı olmalı"),
            "gecikme": ({"id": "gecikme", "mission": {"route_delivery_delay_s": None}},
                        r"mission\.route_delivery_delay_s: sayı olmalı"),
            "irtifa": ({"id": "irtifa", "flight": {"scan_altitude_m": "30"}},
                       r"flight\.scan_altitude_m: sayı olmalı"),
            "kivrim": ({"id": "kivrim", "terrain": {"chicane_count": 2.5}},
                       "chicane_count 0..64"),
            "harita": ({"id": "harita", "map_ids": {"kolay": True, "orta": 2, "zor": 3}},
                       "map_ids pozitif tam sayı"),
            "surus": ({"id": "surus", "environment": {"ground_friction": True}},
                      r"environment\.ground_friction: sayı olmalı"),
        }
        for profile_id, (raw, pattern) in cases.items():
            with self.subTest(profile=profile_id), tempfile.TemporaryDirectory() as tmp:
                raw = dict(raw, id=raw.get("id", profile_id))
                with self.assertRaisesRegex(ValueError, pattern):
                    self.load_from_text(tmp, profile_id, json.dumps(raw))

    def test_cli_rejects_unknown_profile_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(SIM / "scripts" / "world_generator.py"),
             "--profile", "yok_boyle_bir_profil"],
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("bilinmeyen senaryo profili", result.stderr)

    def test_world_write_preserves_existing_file_if_replace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "existing.world"
            out.write_text("<sdf>old-valid-world</sdf>", encoding="utf-8")
            with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    world_generator._atomic_write_text(out, "<sdf>new-world</sdf>")
            self.assertEqual(out.read_text(encoding="utf-8"), "<sdf>old-valid-world</sdf>")
            self.assertEqual(list(Path(tmp).glob("*.tmp")), [])

    def test_mosaic_rotation_border_does_not_erase_existing_scan(self):
        import cv2
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            kare_dir = Path(tmp)
            red = np.zeros((20, 20, 3), dtype=np.uint8)
            red[:, :] = (0, 0, 255)
            green = np.zeros((20, 20, 3), dtype=np.uint8)
            green[:, :] = (0, 255, 0)
            cv2.imwrite(str(kare_dir / "scan_00000.jpg"), red,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 100])
            cv2.imwrite(str(kare_dir / "scan_00001.jpg"), green,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 100])

            patches = [
                mock.patch.object(iha_haritala, "MOZ_PX", 64),
                mock.patch.object(iha_haritala, "MOZ_M", 64.0),
                mock.patch.object(iha_haritala, "MPP", 1.0),
                mock.patch.object(iha_haritala, "SCAN_Z", 10.0),
                mock.patch.object(iha_haritala, "HFOV", 1.2),
                mock.patch.object(iha_haritala, "BG_GRI", 114),
                mock.patch.object(iha_haritala, "Z_TOL", 100.0),
                mock.patch.object(iha_haritala, "YAW_TOL", 10.0),
                mock.patch.object(iha_haritala, "HTAB_HALF_MARJ", 100.0),
            ]
            with patches[0], patches[1], patches[2], patches[3], patches[4], \
                 patches[5], patches[6], patches[7], patches[8]:
                mozaik, kullanilan = iha_haritala.mozaik_kur(
                    kare_dir,
                    {
                        0: (0.0, 0.0, 10.0, 0.0),
                        1: (0.0, 0.0, 10.0, math.pi / 2),
                    },
                    htab_cx=0.0,
                    htab_cy=0.0,
                    rot_isaret=0.5,
                )

            self.assertEqual(kullanilan, 2)
            pixel = mozaik[25, 25]
            self.assertGreater(pixel[2], 200)
            self.assertLess(pixel[0], 60)
            self.assertLess(pixel[1], 60)

    def test_iha_coordinate_fallback_publishes_ika_route(self):
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp:
            level_dir = Path(tmp)
            (level_dir / "kareler").mkdir()
            (level_dir / "poses.csv").write_text("0,0,0,0,30,1.5708\n", encoding="utf-8")
            route = [(-1.0, -2.0), (1.5, 0.0), (3.0, 4.0)]
            blank = np.zeros((8, 8, 3), dtype=np.uint8)
            masks = [np.ones((8, 8), dtype=np.uint8), np.zeros((8, 8), dtype=np.uint8)]
            # Kare başı oylamanın çıktısı: her hücre bol gözlemli ve zemin.
            oy = {
                "zemin_oy": np.full((8, 8), 20, dtype=np.int32),
                "engel_oy": np.zeros((8, 8), dtype=np.int32),
                "gozlem": np.full((8, 8), 20, dtype=np.int32),
                "cikarim_sn": 0.0,
                "kare_sayisi": 1,
            }
            plan = {
                "durum": "KAPALI", "sebep": "sentetik test", "yol_no": None,
                "guven": 0.0, "waypoints_px": [], "darbogaz_m": None, "ihlaller": [],
            }
            with mock.patch.object(iha_haritala, "oy_haritasi_kur",
                                   return_value=(blank, 1, oy)), \
                 mock.patch.object(iha_haritala, "_arac_maskesi",
                                   return_value=np.zeros((8, 8), dtype=np.uint8)), \
                 mock.patch.object(
                     iha_haritala, "costmap_katmanlari",
                     return_value={0: masks[0], 1: masks[1], 10: np.zeros((8, 8), dtype=np.uint8)}), \
                 mock.patch.object(iha_haritala, "rota_bul", return_value=plan), \
                 mock.patch.object(iha_haritala, "_overlay", return_value=blank):
                det = iha_haritala.haritala(
                    level_dir, model=None, htab_cx=0.0, htab_cy=0.0,
                    kb_xy=route[0], hb_xy=route[-1],
                    coord_route=route, coord_road=2, yedek_izin=True)

            self.assertEqual(det["rota_durum"], "KOORDINAT_YEDEK")
            self.assertEqual(det["rota_kaynak"], "iha_koordinat_yedegi")
            self.assertEqual((level_dir / "route.txt").read_text(encoding="utf-8"),
                             "-1.00 -2.00\n1.50 0.00\n3.00 4.00\n")
            rota_json = json.loads((level_dir / "rota.json").read_text(encoding="utf-8"))
            self.assertEqual(rota_json["kaynak"], "iha_koordinat_yedegi")
            self.assertEqual(rota_json["yol_no"], 2)


if __name__ == "__main__":
    unittest.main()
