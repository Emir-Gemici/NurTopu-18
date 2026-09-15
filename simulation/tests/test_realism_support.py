"""NEDEN: Destek yerleştirmesinin boşluk, iç içe geçme ve yatay rota kaydırmasını sınar."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from realism_assets import hollow_pipe
from realism_support import SupportGrid, connected_parts, ground_mesh
import arena


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.points = np.asarray(((0, 0, 2), (1, 0, 2), (1, 1, 2), (0, 1, 2),
                                  (0, 0, 3), (1, 0, 3), (1, 1, 3), (0, 1, 3)), float)
        self.faces = np.asarray(((0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
                                 (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
                                 (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)))

    def test_two_boxes_stack_without_intersection_or_xy_change(self):
        with patch("realism_support.terrain_height", side_effect=lambda world_x, world_y, center: np.full(np.broadcast(world_x, world_y).shape, 0.025)):
            grid = SupportGrid((0, 0), extent=4, step=0.1)
            bottom, first = grid.settle(self.points, self.faces)
            top, second = grid.settle(self.points, self.faces)
        self.assertAlmostEqual(bottom[:, 2].min(), 0.025)
        self.assertAlmostEqual(top[:, 2].min(), bottom[:, 2].max())
        self.assertAlmostEqual(first["sampled_min_gap_m"], 0)
        self.assertAlmostEqual(second["sampled_min_gap_m"], 0)
        np.testing.assert_array_equal(top[:, :2], self.points[:, :2])
        np.testing.assert_array_equal(self.points[:, 2], [2, 2, 2, 2, 3, 3, 3, 3])

    def test_compound_mesh_split_preserves_every_triangle(self):
        points = np.vstack((self.points, self.points + [2, 0, 0]))
        faces = np.vstack((self.faces, self.faces + len(self.points)))
        parts = connected_parts(points, faces)
        self.assertEqual(len(parts), 2)
        self.assertEqual(sum(len(part_faces) for _, part_faces in parts), len(faces))

    def test_support_rejects_out_of_grid_instead_of_clipping(self):
        grid = SupportGrid((0, 0), extent=4, step=0.1)
        with self.assertRaisesRegex(ValueError, "dışına"):
            grid.settle(self.points + [10, 0, 0], self.faces)

    def test_reposition_keeps_full_fragment_outside_protected_route(self):
        grid = SupportGrid((0, 0), step=0.1)
        path = [(0, -23), (0, 21)]
        clearance = grid.clearance([path], width=6)
        placed, delta = grid.choose_position(self.points, clearance, np.random.default_rng(7))
        self.assertGreater(np.linalg.norm(delta), 0)
        for point in placed:
            self.assertGreater(arena.dist_to_path(point[0], point[1], path), 3)
        np.testing.assert_array_equal(placed[:, 2], self.points[:, 2])

    def test_reposition_prefers_ground_over_artificial_tower(self):
        grid = SupportGrid((0, 0), step=0.1)
        indices = np.floor((self.points[:, :2] - grid.origin) / grid.step).astype(int)
        grid.height[indices[:, 1].min():indices[:, 1].max() + 1,
                    indices[:, 0].min():indices[:, 0].max() + 1] = 12
        placed, _ = grid.choose_position(self.points, grid.clearance([], width=6), np.random.default_rng(7))
        settled, _ = grid.settle(placed, self.faces)
        self.assertLess(settled[:, 2].max(), 2)

    def test_ground_has_real_bounded_height_variation(self):
        vertices, faces = ground_mesh((0, 0), divisions=40)
        self.assertGreater(float(np.ptp(vertices[:, 2])), 0.015)
        self.assertGreater(float(vertices[:, 2].min()), 0.009)
        self.assertLess(float(vertices[:, 2].max()), 0.041)
        normals = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                           vertices[faces[:, 2]] - vertices[faces[:, 0]])
        self.assertTrue(np.all(normals[:, 2] > 0))

    def test_pipe_is_closed_solid_with_open_bore(self):
        vertices, faces = hollow_pipe(([-1, -0.2, 0], [1, 0.2, 0.4]))
        radius = np.linalg.norm(vertices[:, 1:] - [0, 0.2], axis=1)
        self.assertGreater(radius.min(), 0.14)
        edges = {}
        for face in faces:
            for start, end in zip(face, np.roll(face, -1)):
                edge = tuple(sorted((int(start), int(end))))
                edges[edge] = edges.get(edge, 0) + 1
        self.assertTrue(all(count == 2 for count in edges.values()))
        triangles = vertices[faces]
        volume = np.sum(np.einsum("ij,ij->i", triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2]))) / 6
        self.assertGreater(volume, 0)


if __name__ == "__main__":
    unittest.main()
