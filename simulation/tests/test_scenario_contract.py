#!/usr/bin/env python3
"""Competition geometry and deterministic-generation contract tests."""

import math
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))

import arena
import scenario_profiles
import world_generator


class ScenarioContractTest(unittest.TestCase):
    def profile_ids(self):
        return ["baseline"] + scenario_profiles.available_profiles()

    def test_profiles_validate(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            self.assertEqual(set(profile["map_ids"]), set(arena.SCENARIOS))

    def test_three_distinct_50m_htab_inside_300m_ub(self):
        boxes = []
        for name, (cx, cy) in arena.ZONE_POS.items():
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
                self.assertIn(f"kb_{level}", model_names)
                self.assertIn(f"hbpad_{level}", model_names)
                for road in (1, 2, 3):
                    self.assertTrue(any(n.startswith(f"road_{level}_{road}_") for n in model_names))
            self.assertIn("<size>30.000 30.000 0.020</size>", world)
            self.assertIn("<size>1.000 1.000 0.040</size>", world)
            self.assertIn("<size>2.000 2.000 0.040</size>", world)

    def test_flight_stays_in_ub_and_lands_in_30m_pad(self):
        for profile_id in self.profile_ids():
            profile = scenario_profiles.load_profile(profile_id)
            level = profile["active_zone"]
            cx, cy = arena.ZONE_POS[level]
            flight = world_generator.iha_flight(cx, cy, profile)
            for x, y, z, _ in flight:
                self.assertLessEqual(abs(x), arena.UB_HALF)
                self.assertLessEqual(abs(y), arena.UB_HALF)
                self.assertGreaterEqual(z, 0.0)
            lx, ly, _, _ = flight[-1]
            self.assertLessEqual(abs(lx - (cx + 38.0)), 15.0)
            self.assertLessEqual(abs(ly - cy), 15.0)

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


if __name__ == "__main__":
    unittest.main()
