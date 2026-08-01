"""Safety-oriented conversion from segmentation masks to a traversable route."""

from __future__ import annotations

import cv2
import numpy as np


def analyze_safe_path(traversable, blocked=None, n_waypoints=8, clearance_ratio=0.018,
                      min_area_ratio=0.006, start_band_ratio=0.18):
    """Return ``(road, confidence, waypoints)`` after obstacle clearance.

    A route must be connected to the vehicle-side (bottom) band. Blocked pixels are
    dilated by a vehicle-clearance margin and subtracted after traversable cleanup,
    so closing cannot accidentally bridge a predicted obstacle.
    """
    trav = (np.asarray(traversable) > 0).astype(np.uint8)
    if trav.ndim != 2 or not trav.size:
        raise ValueError("traversable maskesi boş veya 2B değil")
    h, w = trav.shape
    if blocked is not None:
        obstacle = (np.asarray(blocked) > 0).astype(np.uint8)
        if obstacle.shape != trav.shape:
            raise ValueError("traversable/blocked maske boyutları eşleşmiyor")
    else:
        obstacle = np.zeros_like(trav)

    def odd(value, minimum=3):
        value = max(minimum, int(round(value)))
        return value if value % 2 else value + 1

    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                        (odd(w / 70), odd(h / 70)))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                         (odd(w / 35, 5), odd(h / 35, 5)))
    clean = cv2.morphologyEx(trav, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)

    clearance = odd(min(h, w) * clearance_ratio, 3)
    clearance_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                                  (clearance, clearance))
    blocked_margin = cv2.dilate(obstacle, clearance_kernel)
    clean[blocked_margin > 0] = 0
    clean = cv2.morphologyEx(clean, cv2.MORPH_OPEN, k_open)

    if int(clean.sum()) < h * w * min_area_ratio:
        return None, 0.0, []

    count, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    start_y = int(h * (1.0 - start_band_ratio))
    candidates = []
    for label in range(1, count):
        component = labels == label
        top = int(stats[label, cv2.CC_STAT_TOP])
        bottom = top + int(stats[label, cv2.CC_STAT_HEIGHT])
        reaches_target = top <= int(h * 0.45)
        spans_field = bottom - top >= int(h * 0.50)
        if component[start_y:, :].any() and reaches_target and spans_field:
            candidates.append((int(stats[label, cv2.CC_STAT_AREA]), label))
    if not candidates:
        return None, 0.0, []
    _, selected = max(candidates)
    clean = (labels == selected).astype(np.uint8)

    ys, xs = np.nonzero(clean)
    ymin, ymax = int(ys.min()), int(ys.max())
    top_band = ys <= ymin + 0.30 * (ymax - ymin + 1)
    bx = xs[top_band] if top_band.any() else xs
    cx = float(bx.mean())
    road = 1 if cx < w / 3 else (2 if cx < 2 * w / 3 else 3)
    lo, hi = (road - 1) * w / 3.0, road * w / 3.0
    direction_purity = float(((bx >= lo) & (bx < hi)).sum()) / max(1, bx.size)
    coverage = min(1.0, clean.sum() / max(1.0, h * w * 0.12))
    confidence = float(round(direction_purity * (0.55 + 0.45 * coverage), 3))

    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)
    waypoints = []
    for i in range(n_waypoints - 1, -1, -1):
        y0, y1 = i * h // n_waypoints, (i + 1) * h // n_waypoints
        band = dist[y0:y1, :]
        if band.size and band.max() > clearance / 2:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            waypoints.append((int(lx), int(y0 + ly)))
    if len(waypoints) < max(3, n_waypoints // 2):
        return None, 0.0, []
    return road, confidence, waypoints
