"""NEDEN: Enkaz parçalarını örneklenmiş destek yüzeyine deterministik olarak oturtur."""

from collections import defaultdict

import cv2
import numpy as np

import arena


GROUND_Z = 0.025
SUPPORT_STEP_M = 0.06


def terrain_height(world_x, world_y, center):
    local_x = np.asarray(world_x) - center[0]
    local_y = np.asarray(world_y) - center[1]
    inside = (np.abs(local_x) <= arena.HTAB_HALF) & (np.abs(local_y) <= arena.HTAB_HALF)
    taper = np.maximum(0, 1 - (local_x / arena.HTAB_HALF) ** 4)
    taper *= np.maximum(0, 1 - (local_y / arena.HTAB_HALF) ** 4)
    drainage = 0.012 * np.sin(local_x * 0.13) * np.cos(local_y * 0.11)
    wear = 0.003 * np.sin(local_x * 0.71 + local_y * 0.23)
    return np.where(inside, GROUND_Z + taper * (drainage + wear), 0.0)


def ground_mesh(center, divisions=100):
    coordinates = np.linspace(-arena.HTAB_HALF, arena.HTAB_HALF, divisions + 1)
    local_x, local_y = np.meshgrid(coordinates, coordinates)
    heights = terrain_height(local_x + center[0], local_y + center[1], center)
    vertices = np.column_stack((local_x.ravel(), local_y.ravel(), heights.ravel()))
    triangles = []
    stride = divisions + 1
    for row in range(divisions):
        for column in range(divisions):
            first = row * stride + column
            triangles.extend(((first, first + 1, first + stride + 1),
                              (first, first + stride + 1, first + stride)))
    return vertices, np.asarray(triangles, dtype=int)


def connected_parts(vertices, triangles):
    parents = np.arange(len(vertices))

    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for triangle in triangles:
        first = root(int(triangle[0]))
        for index in triangle[1:]:
            parents[root(int(index))] = first
    groups = defaultdict(list)
    for triangle in triangles:
        groups[root(int(triangle[0]))].append(triangle)
    result = []
    for faces in groups.values():
        indices, remapped = np.unique(np.asarray(faces), return_inverse=True)
        result.append((vertices[indices], remapped.reshape(-1, 3)))
    return result


class SupportGrid:
    def __init__(self, center, extent=None, step=SUPPORT_STEP_M):
        if not np.isfinite(step) or step <= 0:
            raise ValueError("Destek örnekleme aralığı pozitif olmalı")
        self.center = center
        self.step = step
        self.extent = arena.HTAB + 16 if extent is None else extent
        self.origin = np.asarray(center, dtype=float) - self.extent / 2
        self.side = int(np.ceil(self.extent / step))
        positions = (np.arange(self.side) + 0.5) * step
        world_x, world_y = np.meshgrid(positions + self.origin[0], positions + self.origin[1])
        self.height = terrain_height(world_x, world_y, center)

    def clearance(self, paths, width):
        allowed = np.zeros((self.side, self.side), np.uint8)
        lower = np.ceil((np.asarray(self.center) - arena.HTAB_HALF - self.origin) / self.step).astype(int)
        upper = np.floor((np.asarray(self.center) + arena.HTAB_HALF - self.origin) / self.step).astype(int)
        allowed[lower[1]:upper[1], lower[0]:upper[0]] = 1
        for path in paths:
            points = np.round((np.asarray(path) + self.center - self.origin) / self.step - 0.5).astype(np.int32)
            cv2.polylines(allowed, [points], False, 0, int(np.ceil(width / self.step)) + 2)
        return cv2.distanceTransform(allowed, cv2.DIST_L2, cv2.DIST_MASK_PRECISE) * self.step

    def choose_position(self, vertices, clearance, rng):
        center = (vertices[:, :2].min(axis=0) + vertices[:, :2].max(axis=0)) / 2
        radius = float(np.linalg.norm(vertices[:, :2] - center, axis=1).max())
        angles = np.arange(16) * (2 * np.pi / 16) + rng.uniform(0, 2 * np.pi)
        directions = np.column_stack((np.cos(angles), np.sin(angles)))
        candidates = np.concatenate([center[None], *[center + distance * directions for distance in (1, 2, 3.5, 5, 7, 10, 14)],
                                     rng.uniform(-arena.HTAB_HALF, arena.HTAB_HALF, (64, 2)) + self.center])
        indices = np.floor((candidates - self.origin) / self.step).astype(int)
        inside = (indices >= 0).all(axis=1) & (indices < self.side).all(axis=1)
        candidates, indices = candidates[inside], indices[inside]
        safe = clearance[indices[:, 1], indices[:, 0]] >= radius + 2 * self.step
        candidates, indices = candidates[safe], indices[safe]
        if not len(candidates):
            eligible = np.argwhere(clearance >= radius + 2 * self.step)
            if not len(eligible):
                raise ValueError(f"Parça korunmuş geçitlere sığmıyor; yarıçap={radius:.3f} m")
            stride = max(1, len(eligible) // 128)
            indices = eligible[::stride, ::-1]
            candidates = self.origin + (indices + 0.5) * self.step
        offsets = np.vstack((np.zeros((1, 2)), directions[::2] * radius * 0.8))
        samples = np.floor((candidates[:, None, :] + offsets - self.origin) / self.step).astype(int)
        sampled_heights = self.height[samples[:, :, 1], samples[:, :, 0]].max(axis=1)
        distances = np.linalg.norm(candidates - center, axis=1)
        shortlist = np.argsort(sampled_heights + 0.045 * distances)[:6]
        best_index, best_score = None, np.inf
        for index in shortlist:
            padding = int(np.ceil(radius / self.step))
            column, row = indices[index]
            height = float(self.height[row - padding:row + padding + 1,
                                       column - padding:column + padding + 1].max())
            score = height + 0.045 * distances[index]
            if score < best_score:
                best_index, best_score = int(index), score
        delta = candidates[best_index] - center
        result = vertices.copy()
        result[:, :2] += delta
        return result, delta.tolist()

    def settle(self, vertices, triangles):
        vertices = np.asarray(vertices, dtype=float).copy()
        lower_index = np.floor((vertices[:, :2].min(axis=0) - self.origin) / self.step).astype(int)
        upper_index = np.floor((vertices[:, :2].max(axis=0) - self.origin) / self.step).astype(int) + 1
        if np.any(lower_index < 0) or np.any(upper_index > self.side):
            raise ValueError("Moloz destek ızgarasının dışına çıktı")
        world_x, world_y = np.meshgrid(
            self.origin[0] + (np.arange(lower_index[0], upper_index[0]) + 0.5) * self.step,
            self.origin[1] + (np.arange(lower_index[1], upper_index[1]) + 0.5) * self.step,
        )
        lower = np.full(world_x.shape, np.inf)
        upper = np.full(world_x.shape, -np.inf)
        for triangle in vertices[triangles]:
            first, second, third = triangle
            denominator = ((second[1] - third[1]) * (first[0] - third[0])
                           + (third[0] - second[0]) * (first[1] - third[1]))
            if abs(denominator) < 1e-12:
                continue
            weight_first = ((second[1] - third[1]) * (world_x - third[0])
                            + (third[0] - second[0]) * (world_y - third[1])) / denominator
            weight_second = ((third[1] - first[1]) * (world_x - third[0])
                             + (first[0] - third[0]) * (world_y - third[1])) / denominator
            weight_third = 1 - weight_first - weight_second
            inside = (weight_first >= -1e-8) & (weight_second >= -1e-8) & (weight_third >= -1e-8)
            height = weight_first * first[2] + weight_second * second[2] + weight_third * third[2]
            lower[inside] = np.minimum(lower[inside], height[inside])
            upper[inside] = np.maximum(upper[inside], height[inside])
        valid = np.isfinite(lower)
        previous = self.height[lower_index[1]:upper_index[1], lower_index[0]:upper_index[0]]
        minimum_ground_shift = float(np.max(
            terrain_height(vertices[:, 0], vertices[:, 1], self.center) - vertices[:, 2]))
        if valid.any():
            shift = max(float(np.max(previous[valid] - lower[valid])), minimum_ground_shift)
            gap = float(np.min(lower[valid] + shift - previous[valid]))
            previous[valid] = np.maximum(previous[valid], upper[valid] + shift)
            status = "sampled_surface_contact" if gap < self.step else "vertex_ground_contact"
        else:
            shift = minimum_ground_shift
            gap = None
            status = "subgrid_fragment_ground_contact"
        vertices[:, 2] += shift
        return vertices, {"vertical_shift_m": round(shift, 7), "support_step_m": self.step,
                          "sampled_min_gap_m": None if gap is None else round(gap, 7),
                          "status": status}
