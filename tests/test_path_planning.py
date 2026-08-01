import unittest

try:
    import numpy as np
    from codes.path_planning import analyze_safe_path
except ImportError:  # minimal environments can still run protocol/simulation tests
    np = None


@unittest.skipIf(np is None, "numpy/opencv not installed")
class SafePathTests(unittest.TestCase):
    def lane(self, x0, x1):
        mask = np.zeros((120, 120), dtype=np.uint8)
        mask[:, x0:x1] = 1
        return mask

    def test_clear_routes_map_to_three_road_ids(self):
        for expected, bounds in enumerate(((8, 34), (47, 73), (86, 112)), 1):
            road, confidence, waypoints = analyze_safe_path(self.lane(*bounds))
            self.assertEqual(road, expected)
            self.assertGreater(confidence, 0.5)
            self.assertGreaterEqual(len(waypoints), 4)

    def test_blocked_barrier_fails_closed(self):
        traversable = self.lane(47, 73)
        blocked = np.zeros_like(traversable)
        blocked[54:66, 40:80] = 1
        self.assertEqual(analyze_safe_path(traversable, blocked), (None, 0.0, []))

    def test_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_safe_path(np.ones((10, 10)), np.ones((8, 8)))


if __name__ == "__main__":
    unittest.main()
