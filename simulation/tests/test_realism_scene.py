"""NEDEN: Yeni sürümde UV, geometri ve kaynak koruma hatalarını gerçekten yakalar."""

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from realism_assets import load_obj, texture, transform, transform_vertices, write_collada
from realism_scene import batch_rubble, build, mesh_model, place_barriers
from realism_capture import prepare
import arena
import world_generator


class RealismTests(unittest.TestCase):
    def test_texture_determinism_and_seed_variation(self):
        first = texture(19, "asphalt", size=128)
        np.testing.assert_array_equal(first, texture(19, "asphalt", size=128))
        self.assertFalse(np.array_equal(first, texture(20, "asphalt", size=128)))
        self.assertGreater(float(first.std()), 5)

    def test_every_route_receives_same_surface_treatment(self):
        routes = {1: [(-16, -20), (-16, 20)], 2: [(0, -20), (0, 20)], 3: [(16, -20), (16, 20)]}
        plain = texture(19, "asphalt", size=256).astype(float)
        routed = texture(19, "asphalt", size=256, paths=routes).astype(float)
        for column in (46, 128, 209):
            self.assertGreater(float((plain - routed)[80:160, column - 2:column + 2].mean()), 3)

    def test_rigid_transform_preserves_full_mesh_pose(self):
        matrix = transform("4 5 6 0 0 1.5707963267948966")
        points = transform_vertices([[1, 0, 0], [0, 2, 0]], matrix)
        np.testing.assert_allclose(points, [[4, 6, 6], [2, 5, 6]], atol=1e-10)

    def test_bad_pose_rejected(self):
        with self.assertRaises(ValueError):
            transform("0 0 nan 0 0 0")

    def test_collada_contains_uv_normals_and_metre_scale(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.dae"
            write_collada(path, [[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[0, 1, 2]])
            root = ET.parse(path)
            namespace = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
            self.assertEqual(root.find("c:asset/c:unit", namespace).get("meter"), "1")
            self.assertIsNotNone(root.find(".//c:input[@semantic='TEXCOORD']", namespace))
            self.assertIsNotNone(root.find(".//c:input[@semantic='NORMAL']", namespace))

    def test_degenerate_triangle_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_collada(Path(directory) / "bad.dae", [[0, 0, 0]] * 3, [[0, 1, 2]])

    def test_static_mesh_collision_identical_to_visual(self):
        simulation = SCRIPTS.parent
        model = mesh_model("test", simulation / "media/test.dae", simulation / "media", "concrete")
        visual = model.find("link/visual/geometry")
        collision = model.find("link/collision/geometry")
        self.assertEqual(ET.tostring(visual), ET.tostring(collision))
        self.assertEqual(model.findtext("static"), "true")
        self.assertGreater(float(model.findtext("link/collision/surface/friction/ode/mu")), 0)

    def test_old_box_world_rejected_instead_of_false_upgrade(self):
        world = ET.fromstring('<world><model name="deb_kolay_0"><static>true</static><link name="link"/></model></world>')
        with self.assertRaisesRegex(ValueError, "yeni moloz"):
            batch_rubble(world, SCRIPTS.parent / "media")

    def test_real_mesh_has_valid_faces(self):
        points, faces = load_obj(SCRIPTS.parent / "media/meshes/rubble/slab_0.obj")
        self.assertGreater(len(faces), 8)
        self.assertGreater(float(np.ptp(points[:, 2])), 0)

    def test_micro_mesh_batched_with_pose_and_no_old_box(self):
        world = ET.fromstring('''<world><model name="mic_kolay_0"><static>true</static>
            <pose>4 5 6 0 0 0</pose><link name="link">
            <collision name="c0"><geometry><box><size>1 1 1</size></box></geometry></collision>
            <visual name="v0"><pose>0 0 1 0 0 1.5707963267948966</pose>
            <geometry><mesh><uri>file://media/meshes/rubble/slab_0.obj</uri>
            <scale>2 2 2</scale></mesh></geometry></visual></link></model></world>''')
        points, _ = load_obj(SCRIPTS.parent / "media/meshes/rubble/slab_0.obj")
        with patch("realism_scene.write_collada") as writer:
            manifest = batch_rubble(world, SCRIPTS.parent / "media")
        actual = np.asarray(writer.call_args.args[1])
        expected = np.column_stack((-2 * points[:, 1] + 4, 2 * points[:, 0] + 5, 2 * points[:, 2] + 7))
        np.testing.assert_allclose(actual, expected, atol=1e-10)
        self.assertEqual(len(manifest), 1)
        self.assertIsNone(world.find("model[@name='mic_kolay_0']"))
        self.assertEqual(len(world.findall(".//collision")), 1)
        self.assertIsNone(world.find(".//collision/geometry/box"))

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "saved"
            existing.mkdir()
            sentinel = existing / "keep.txt"
            sentinel.write_text("original")
            with patch("realism_scene.SIMULATION", Path(directory)):
                with self.assertRaises(FileExistsError):
                    build(existing)
            self.assertEqual(sentinel.read_text(), "original")

    def test_capture_rejects_stale_frames_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileExistsError):
                prepare("not-read.world", directory, "test")

    def test_inherited_barriers_cannot_narrow_open_route(self):
        profile = world_generator.load_profile("cx_teknofest_official")
        zones = {scenario: world_generator.make_zone(scenario, 260822,
                 harita_id=profile["map_ids"][scenario], profile=profile, terrain="textured")
                 for scenario in arena.SCENARIOS}
        world = ET.Element("world")
        for scenario, zone in zones.items():
            for road in zone["harita"]["paths"]:
                if road != zone["road"]:
                    for suffix in ("", "b"):
                        model = ET.fromstring(f'''<model name="bar_{scenario}_{road}{suffix}">
                            <pose>0 0 0.5 0 0 0</pose><link><collision><geometry><box>
                            <size>{zone['lane_w'] + 1} 0.5 1</size>
                            </box></geometry></collision></link></model>''')
                        world.append(model)
        placements = place_barriers(world, zones)
        self.assertEqual(len(placements), 12)
        for model in world.findall("model"):
            scenario = model.get("name").split("_")[1]
            zone = zones[scenario]
            pose = np.fromstring(model.findtext("pose"), sep=" ")
            local = pose[:2] - arena.ZONE_POS[scenario]
            radius = np.hypot(zone["lane_w"] + 1, 0.5) / 2
            distance = arena.dist_to_path(*local, zone["harita"]["paths"][zone["road"]])
            self.assertGreaterEqual(distance, zone["lane_w"] / 2 + radius + 0.2 - 1e-6)


if __name__ == "__main__":
    unittest.main()
