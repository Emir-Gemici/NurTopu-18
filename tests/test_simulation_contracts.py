import importlib
import math
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "simulation" / "scripts"
sys.path.insert(0, str(SCRIPTS))

arena = importlib.import_module("arena")
ika_nav = importlib.import_module("ika_nav")
navitas_sim = importlib.import_module("navitas_sim")


class ArenaContracts(unittest.TestCase):
    def test_all_15_maps_have_valid_distinct_safe_geometry(self):
        for scenario in arena.SCENARIOS:
            for map_id in range(1, arena.HARITA_N + 1):
                field = arena.harita(map_id, scenario)
                self.assertIn(field["open"], (1, 2, 3))
                self.assertGreaterEqual(abs(field["hb"][0] - field["kb"][0]), 6.0)
                for road in (1, 2, 3):
                    route = arena.route_waypoints(road, scenario, map_id)
                    self.assertGreater(len(route), 2)
                    self.assertTrue(all(math.isfinite(v) for p in route for v in p))

    def test_navigation_translates_local_route_to_selected_world_zone(self):
        captured = {}

        def fake_navigate(wps, label, verbose):
            captured["wps"] = wps
            return True

        with mock.patch.object(ika_nav, "navigate", side_effect=fake_navigate):
            self.assertTrue(ika_nav.navigate_road(2, "zor", harita_id=3, verbose=False))
        local = arena.route_waypoints(2, "zor", 3)
        origin = arena.ZONE_POS["zor"]
        self.assertEqual(captured["wps"][0], arena.to_world(local[0], origin))
        self.assertGreater(captured["wps"][0][0], 60.0)

    def test_transmitted_waypoints_take_precedence_over_arena_truth(self):
        route = {"road": 1, "seq": 9, "ref_xy": [90.0, -23.0],
                 "waypoints": [[0.0, 0.0], [2.0, 8.0], [-1.0, 20.0]]}
        with mock.patch.object(ika_nav, "navigate", return_value=True) as navigate:
            self.assertTrue(ika_nav.navigate_route_message(route, "zor", 5, verbose=False))
        self.assertEqual(navigate.call_args.args[0],
                         [(90.0, -23.0), (92.0, -15.0), (89.0, -3.0)])

    def test_worker_exception_returns_nonzero(self):
        argv = ["navitas_sim.py", "orta", "--ika-only", "--no-wait"]
        with (mock.patch.object(sys, "argv", argv),
              mock.patch.object(navitas_sim.time, "sleep"),
              mock.patch.object(navitas_sim, "check_topics", return_value=True),
              mock.patch.object(ika_nav, "navigate_scenario", side_effect=RuntimeError("boom"))):
            self.assertEqual(navitas_sim.main(), 1)


if __name__ == "__main__":
    unittest.main()
