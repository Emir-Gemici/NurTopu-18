#!/usr/bin/env python3
"""
Navitas TEKNOFEST 2026 — Gelişmiş Dünya Üreteci
Kullanım:
  python3 scripts/world_generator.py --difficulty kolay  --seed 42  --output worlds/navitas_arena.world
  python3 scripts/world_generator.py --difficulty orta   --open-path
  python3 scripts/world_generator.py --difficulty rastgele
"""

import argparse
import math
import random
import sys
from pathlib import Path

# ── Koordinat sabitleri (şartname V2) ─────────────────────────────────────────
IHA_FB   = (-105.0,   0.0, 1.5)   # İHA Fırlatma Bölgesi (batı)
IHA_IB   = ( 85.0,    0.0, 0.0)   # İHA İniş Bölgesi (doğu)
IKA_KB   = (-23.0,  -23.0, 0.0)   # İKA Kalkış Bölgesi (güneybatı)
HB       = ( 23.0,   23.0, 0.0)   # Hedef Bölge (kuzeydoğu)
ARENA_CX =  0.0
ARENA_CY =  0.0

# ── Koridor parametreleri ──────────────────────────────────────────────────────
CORRIDORS = {
    "kolay":    {"cx": -18.0, "width": 5.0, "wall_h": 2.0, "color": "0.2 0.7 0.2 1"},
    "orta":     {"cx":   0.0, "width": 3.5, "wall_h": 2.5, "color": "0.8 0.6 0.0 1"},
    "zor":      {"cx":  18.0, "width": 2.2, "wall_h": 3.0, "color": "0.8 0.1 0.1 1"},
}

# İKA rotası: İKA-KB → HB arasında kıvrımlı waypoint'ler
IKA_WAYPOINTS = {
    "kolay": [
        IKA_KB[:2],
        (-23.0, -10.0),
        (-15.0,   0.0),
        ( -5.0,  10.0),
        (  5.0,  15.0),
        ( 15.0,  20.0),
        HB[:2],
    ],
    "orta": [
        IKA_KB[:2],
        (-20.0,  -8.0),
        ( -8.0,   2.0),
        (  5.0,   8.0),
        ( 15.0,  18.0),
        HB[:2],
    ],
    "zor": [
        IKA_KB[:2],
        (-18.0, -15.0),
        ( -5.0,  -5.0),
        (  5.0,   5.0),
        ( 18.0,  20.0),
        HB[:2],
    ],
}


# ── SDF yardımcıları ──────────────────────────────────────────────────────────

def _box(name, px, py, pz, sx, sy, sz, r, g, b, static=True):
    static_tag = "<static>true</static>" if static else ""
    return f"""
    <model name="{name}">
      {static_tag}
      <pose>{px} {py} {pz} 0 0 0</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{sx} {sy} {sz}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
          <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
        </visual>
      </link>
    </model>"""


def _cylinder_marker(name, px, py, pz, radius, length, r, g, b):
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{px} {py} {pz} 0 0 0</pose>
      <link name="link">
        <collision name="col"><geometry><cylinder><radius>{radius}</radius><length>{length}</length></cylinder></geometry></collision>
        <visual name="vis">
          <geometry><cylinder><radius>{radius}</radius><length>{length}</length></cylinder></geometry>
          <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
        </visual>
      </link>
    </model>"""


def _include_model(name, model_name, px, py, pz, yaw=0.0):
    return f"""
    <include>
      <uri>model://{model_name}</uri>
      <name>{name}</name>
      <pose>{px} {py} {pz} 0 0 {yaw}</pose>
    </include>"""


def _ground_plane():
    return """
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>300 300</size></plane></geometry>
          <surface><friction><ode><mu>0.8</mu><mu2>0.8</mu2></ode></friction></surface>
        </collision>
        <visual name="visual">
          <cast_shadows>false</cast_shadows>
          <geometry><plane><normal>0 0 1</normal><size>300 300</size></plane></geometry>
          <material>
            <script>
              <uri>file://media/materials/scripts/gazebo.material</uri>
              <name>Gazebo/Grey</name>
            </script>
          </material>
        </visual>
      </link>
    </model>"""


# ── Alan işaretçileri ─────────────────────────────────────────────────────────

def make_zone_markers():
    parts = []
    # İHA-FB işareti (kırmızı)
    parts.append(_cylinder_marker("iha_fb_marker",
        IHA_FB[0], IHA_FB[1], 0.05, 3.0, 0.1, 0.9, 0.1, 0.1))
    # İHA-İB işareti (sarı)
    parts.append(_cylinder_marker("iha_ib_marker",
        IHA_IB[0], IHA_IB[1], 0.05, 4.0, 0.1, 0.9, 0.8, 0.0))
    # İKA-KB işareti (yeşil)
    parts.append(_cylinder_marker("ika_kb_marker",
        IKA_KB[0], IKA_KB[1], 0.05, 2.5, 0.1, 0.1, 0.8, 0.1))
    # HB işareti (büyük sarı-yeşil)
    parts.append(_cylinder_marker("hb_marker",
        HB[0], HB[1], 0.05, 3.5, 0.1, 0.9, 0.7, 0.0))
    # HB "H" levhası
    parts.append(_box("hb_sign", HB[0], HB[1], 1.2, 0.5, 0.05, 2.0,
                       0.9, 0.9, 0.0))
    return "\n".join(parts)


# ── İKA yol bariyerleri (kıvrımlı rota) ──────────────────────────────────────

def make_ika_path_walls(scenario, rng):
    """İKA rotası boyunca kıvrımlı duvarlar üret."""
    waypoints = IKA_WAYPOINTS.get(scenario, IKA_WAYPOINTS["kolay"])
    corridor_w = CORRIDORS[scenario]["width"]
    wall_h = CORRIDORS[scenario]["wall_h"]
    cr, cg, cb, _ = CORRIDORS[scenario]["color"].split()
    cr, cg, cb = float(cr), float(cg), float(cb)

    parts = []
    seg_idx = 0
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i + 1]
        dx = x1 - x0
        dy = y1 - y0
        length = math.sqrt(dx * dx + dy * dy)
        yaw = math.atan2(dy, dx)
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0

        # Sol duvar
        lx = cx - (corridor_w / 2.0) * math.sin(yaw)
        ly = cy + (corridor_w / 2.0) * math.cos(yaw)
        parts.append(_box(f"ika_wall_L_{seg_idx}", lx, ly, wall_h / 2.0,
                          length, 0.2, wall_h, cr, cg, cb))
        # Sağ duvar
        rx = cx + (corridor_w / 2.0) * math.sin(yaw)
        ry = cy - (corridor_w / 2.0) * math.cos(yaw)
        # SDF'de yaw döndürmek için pose'u ayarla - yine de box kullanıyoruz,
        # eğimleri için ayrı model yazıyoruz
        wall_name_r = f"ika_wall_R_{seg_idx}"
        parts.append(f"""
    <model name="{wall_name_r}">
      <static>true</static>
      <pose>{rx} {ry} {wall_h/2.0} 0 0 {yaw}</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{length} 0.2 {wall_h}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{length} 0.2 {wall_h}</size></box></geometry>
          <material><ambient>{cr} {cg} {cb} 1</ambient><diffuse>{cr} {cg} {cb} 1</diffuse></material>
        </visual>
      </link>
    </model>""")
        wall_name_l = f"ika_wall_L2_{seg_idx}"
        parts.append(f"""
    <model name="{wall_name_l}">
      <static>true</static>
      <pose>{lx} {ly} {wall_h/2.0} 0 0 {yaw}</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{length} 0.2 {wall_h}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{length} 0.2 {wall_h}</size></box></geometry>
          <material><ambient>{cr} {cg} {cb} 1</ambient><diffuse>{cr} {cg} {cb} 1</diffuse></material>
        </visual>
      </link>
    </model>""")
        seg_idx += 1

    return "\n".join(parts)


# ── Koridor engelleri (rastgele debris) ───────────────────────────────────────

def make_debris(scenario, rng, open_path=False):
    if open_path:
        return ""
    waypoints = IKA_WAYPOINTS.get(scenario, IKA_WAYPOINTS["kolay"])
    corridor_w = CORRIDORS[scenario]["width"]
    counts = {"kolay": 3, "orta": 6, "zor": 10}
    count = counts.get(scenario, 3)

    parts = []
    for i in range(count):
        seg = rng.randint(1, len(waypoints) - 2)
        x0, y0 = waypoints[seg]
        x1, y1 = waypoints[seg + 1] if seg + 1 < len(waypoints) else waypoints[seg]
        t = rng.random()
        px = x0 + t * (x1 - x0)
        py = y0 + t * (y1 - y0)
        offset = rng.uniform(-(corridor_w * 0.3), corridor_w * 0.3)
        dx = x1 - x0
        dy = y1 - y0
        dist = math.sqrt(dx * dx + dy * dy) or 1.0
        px += offset * (-dy / dist)
        py += offset * (dx / dist)
        sz = rng.uniform(0.3, 0.7)
        parts.append(_box(f"debris_{i}", px, py, sz / 2.0, sz, sz, sz,
                          0.55, 0.27, 0.07))
    return "\n".join(parts)


# ── İHA iniş bölgesi (büyük flat alan) ───────────────────────────────────────

def make_iha_landing_zone():
    parts = []
    # İniş zemini (sarı şerit)
    parts.append(_box("landing_ground",
        IHA_IB[0], IHA_IB[1], 0.01, 12.0, 12.0, 0.02,
        0.9, 0.8, 0.0))
    # Köşe konileri
    for i, (ox, oy) in enumerate([(-5, -5), (-5, 5), (5, -5), (5, 5)]):
        parts.append(_cylinder_marker(f"landing_cone_{i}",
            IHA_IB[0] + ox, IHA_IB[1] + oy, 0.5, 0.15, 1.0,
            1.0, 0.2, 0.0))
    return "\n".join(parts)


# ── Rampa (İHA-FB yanı) ───────────────────────────────────────────────────────

def make_catapult():
    return _include_model("catapult_main", "catapult",
                          IHA_FB[0] + 4.0, IHA_FB[1], 0.08, yaw=0.0)


# ── Dış çevre duvarları ───────────────────────────────────────────────────────

def make_arena_boundary():
    parts = []
    W, H, WH = 220.0, 80.0, 3.0
    # Kuzey
    parts.append(_box("boundary_N",  0,  H/2, WH/2, W, 0.4, WH, 0.4, 0.4, 0.4))
    # Güney
    parts.append(_box("boundary_S",  0, -H/2, WH/2, W, 0.4, WH, 0.4, 0.4, 0.4))
    # Batı
    parts.append(_box("boundary_W", -W/2, 0,  WH/2, 0.4, H, WH, 0.4, 0.4, 0.4))
    # Doğu
    parts.append(_box("boundary_E",  W/2, 0,  WH/2, 0.4, H, WH, 0.4, 0.4, 0.4))
    return "\n".join(parts)


# ── Modelleri dahil et ────────────────────────────────────────────────────────

def make_vehicle_includes():
    iha_x, iha_y, iha_z = IHA_FB
    ika_x, ika_y, ika_z = IKA_KB
    parts = [
        _include_model("iha", "iha", iha_x, iha_y, iha_z + 0.2, yaw=0.0),
        _include_model("ika", "ika", ika_x, ika_y, ika_z + 0.12, yaw=0.0),
    ]
    return "\n".join(parts)


# ── Işık kaynakları ───────────────────────────────────────────────────────────

def make_lights():
    return """
    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 -0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.1 0.1 0.1 1</specular>
      <attenuation><range>1000</range><constant>0.9</constant><linear>0.01</linear><quadratic>0.001</quadratic></attenuation>
      <direction>-0.5 0.1 -0.9</direction>
    </light>"""


# ── Tam dünya SDF ─────────────────────────────────────────────────────────────

def build_world(scenario, seed, open_path):
    rng = random.Random(seed)

    parts = [
        make_lights(),
        _ground_plane(),
        make_arena_boundary(),
        make_zone_markers(),
        make_iha_landing_zone(),
        make_catapult(),
        make_ika_path_walls(scenario, rng),
        make_debris(scenario, rng, open_path),
        make_vehicle_includes(),
    ]

    body = "\n".join(parts)

    world_sdf = f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="navitas_arena">

    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
      <gravity>0 0 -9.8</gravity>
    </physics>

    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.7 0.7 0.7 1</background>
      <shadows>true</shadows>
    </scene>

    <!-- Senaryo: {scenario} | Seed: {seed} | Açık yol: {open_path} -->
{body}

  </world>
</sdf>
"""
    return world_sdf


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Navitas arena dünya üreticisi")
    parser.add_argument("--difficulty", "--scenario",
                        choices=["kolay", "orta", "zor", "rastgele"],
                        default="kolay",
                        help="Zorluk seviyesi (varsayılan: kolay)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Rastgele sayı seed (varsayılan: 42)")
    parser.add_argument("--output", default="worlds/navitas_arena.world",
                        help="Çıktı .world dosyası yolu")
    parser.add_argument("--open-path", action="store_true",
                        help="Engel koymadan açık yol (test modu)")
    args = parser.parse_args()

    scenario = args.difficulty
    if scenario == "rastgele":
        scenario = random.choice(["kolay", "orta", "zor"])
        print(f"[world_gen] Rastgele senaryo seçildi: {scenario}")

    print(f"[world_gen] Senaryo={scenario} | Seed={args.seed} | Açık yol={args.open_path}")
    world = build_world(scenario, args.seed, args.open_path)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(world, encoding="utf-8")
    print(f"[world_gen] Dünya yazıldı: {out_path}")
    print(f"[world_gen] İHA-FB: {IHA_FB} | İHA-İB: {IHA_IB}")
    print(f"[world_gen] İKA-KB: {IKA_KB} | HB: {HB}")


if __name__ == "__main__":
    main()
