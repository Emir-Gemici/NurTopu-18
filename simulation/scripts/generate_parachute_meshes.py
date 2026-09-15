#!/usr/bin/env python3
"""NEDEN: İHA paraşütü kanopilerini tekrarlanabilir, ince kumaş yüzeyleri olarak üretir.

Yalnız NumPy ve Python standart kütüphanesini kullanır. Her OBJ, açık bir tepe
vent'ine, 16 gore paneline ve etekte hafif içe kıvrılan eksenel bir profile
sahiptir. Gore sınırındaki dar geometrik çöküntü, dikişi ek kutular olmadan
ışık-gölge ile görünür kılar.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


GORE_COUNT = 16
SEGMENTS_PER_GORE = 4
RADIAL_RINGS = 18
MATERIAL_FILE = "parachute_ripstop.mtl"


@dataclass(frozen=True)
class CanopySpec:
    name: str
    radius_m: float
    height_m: float
    vent_radius_m: float
    skirt_angle_rad: float
    crease_depth_m: float


SPECS = (
    CanopySpec("packed", 0.24, 0.30, 0.035, 1.72, 0.006),
    CanopySpec("partial", 0.76, 0.48, 0.080, 1.72, 0.014),
    CanopySpec("full", 1.20, 0.88, 0.140, 1.72, 0.026),
)


def _surface(spec: CanopySpec) -> np.ndarray:
    """Dışa doğru yuvarlanan, etekte içeri dönen ve vent'i açık kalan yüzey."""
    angular_count = GORE_COUNT * SEGMENTS_PER_GORE
    phi0 = math.asin(spec.vent_radius_m / spec.radius_m)
    phi = np.linspace(phi0, spec.skirt_angle_rad, RADIAL_RINGS)
    theta = np.linspace(0.0, 2.0 * math.pi, angular_count, endpoint=False)

    pp, tt = np.meshgrid(phi, theta, indexing="ij")
    radial = spec.radius_m * np.sin(pp)
    skirt_cos = math.cos(spec.skirt_angle_rad)
    height = spec.height_m * (np.cos(pp) - skirt_cos) / (1.0 - skirt_cos)

    # Yalnız gore sınırında tepe yapan dar ağırlık: geometri ışığı kırar ve dikiş
    # çizgisini görünür yapar. Vent ve etekte sıfıra yaklaşarak profili bozmaz.
    boundary = ((1.0 + np.cos(GORE_COUNT * tt)) * 0.5) ** 6
    along_panel = np.sin(
        math.pi * (pp - phi0) / (spec.skirt_angle_rad - phi0)
    )
    crease = boundary * along_panel
    radial -= 0.45 * spec.crease_depth_m * crease
    height -= spec.crease_depth_m * crease

    x = radial * np.cos(tt)
    y = radial * np.sin(tt)
    return np.stack((x, y, height), axis=-1)


def _obj_text(spec: CanopySpec) -> tuple[str, int]:
    vertices = _surface(spec)
    rings, angular_count, _ = vertices.shape
    lines = [
        f"# Navitas parachute canopy: {spec.name}",
        f"# gores={GORE_COUNT} vent_radius_m={spec.vent_radius_m:.3f}",
        f"mtllib {MATERIAL_FILE}",
        f"o parachute_{spec.name}",
    ]
    for x, y, z in vertices.reshape((-1, 3)):
        lines.append(f"v {x:.7f} {y:.7f} {z:.7f}")

    lines.extend(("s 1", "g canopy"))
    current_material = None
    triangle_count = 0
    for ring in range(rings - 1):
        for sector in range(angular_count):
            gore = sector // SEGMENTS_PER_GORE
            material = "ripstop_orange" if gore % 2 == 0 else "ripstop_ivory"
            if material != current_material:
                lines.append(f"usemtl {material}")
                current_material = material
            nxt = (sector + 1) % angular_count
            a = ring * angular_count + sector + 1
            b = ring * angular_count + nxt + 1
            c = (ring + 1) * angular_count + sector + 1
            d = (ring + 1) * angular_count + nxt + 1
            # Üst/dış yüz normali için saat yönünün tersine sarım.
            lines.append(f"f {a} {c} {b}")
            lines.append(f"f {b} {c} {d}")
            triangle_count += 2
    lines.append("")
    return "\n".join(lines), triangle_count


def _material_text() -> str:
    return """# Soluk kurtarma paraşütü ripstop naylonu; düşük parlaklık, yüksek matlık.
newmtl ripstop_orange
Ka 0.30 0.14 0.07
Kd 0.76 0.34 0.15
Ks 0.045 0.045 0.040
Ns 7.0
d 0.97
illum 2

newmtl ripstop_ivory
Ka 0.32 0.31 0.27
Kd 0.84 0.82 0.72
Ks 0.040 0.040 0.035
Ns 6.0
d 0.97
illum 2
"""


def generate(output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / MATERIAL_FILE).write_text(_material_text(), encoding="utf-8")
    counts = {}
    for spec in SPECS:
        text, triangle_count = _obj_text(spec)
        path = output_dir / f"parachute_{spec.name}.obj"
        path.write_text(text, encoding="ascii")
        counts[spec.name] = triangle_count
    return counts


def main() -> int:
    default_dir = Path(__file__).resolve().parents[1] / "media" / "meshes"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=default_dir)
    args = parser.parse_args()
    for name, triangles in generate(args.output_dir).items():
        print(f"parachute_{name}.obj: {triangles} triangles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
