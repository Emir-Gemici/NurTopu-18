#!/usr/bin/env python3
"""
Navitas TEKNOFEST 2026 — Gazebo Dünya Dosyası Üretici

Kullanım:
  python3 generate_world.py --scenario kolay
  python3 generate_world.py --scenario orta
  python3 generate_world.py --scenario zor
  python3 generate_world.py --scenario rastgele

Üretilen dosya: worlds/navitas.world
Çalıştırmak için: gazebo worlds/navitas.world
"""

import argparse
import random
import os
import sys

# ── Alan parametreleri (metre) ──────────────────────────────────────────────
HTAB_HALF    = 25.0        # HTAB 50x50 → yarı kenar 25m
IKA_KB       = (-22.0, -22.0)   # İKA başlangıç (HTAB SW köşe)
HB_CENTER    = ( 18.0,  21.0)   # Hedef H merkezi (HTAB NE)
INIS_CENTER  = (  0.0, -80.0)   # İHA iniş bölgesi merkezi
INIS_HALF    = 15.0        # 30x30 → yarı kenar 15m
LAUNCH_POS   = (-80.0,  0.0, 3.0)  # Mancınık pozisyonu

# ── 3 Koridor tanımı ────────────────────────────────────────────────────────
# cx: merkez X, width: geçiş genişliği (m)
CORRIDORS = {
    "kolay": {"cx": -14.0, "width": 4.5, "label": "KOLAY"},
    "orta":  {"cx":   0.0, "width": 3.2, "label": "ORTA"},
    "zor":   {"cx": +14.0, "width": 2.2, "label": "ZOR"},
}

DEBRIS_SEED  = 42
DEBRIS_COUNT = 90          # HTAB içi moloz adedi

# ── Renk paletleri ──────────────────────────────────────────────────────────
def rgba(r, g, b, a=1.0):
    return f"{r:.3f} {g:.3f} {b:.3f} {a:.3f}"

C_GROUND     = rgba(0.45, 0.38, 0.28)   # Kuru toprak
C_HTAB       = rgba(0.38, 0.32, 0.22)   # HTAB zemini (koyu)
C_INIS       = rgba(0.10, 0.25, 0.75)   # İniş bölgesi (mavi)
C_HB         = rgba(0.85, 0.08, 0.08)   # Hedef H (kırmızı)
C_IKA_START  = rgba(0.90, 0.80, 0.10)   # İKA başlangıç (sarı)
C_DEBRIS     = rgba(0.55, 0.47, 0.35)   # Moloz
C_WALL       = rgba(0.50, 0.42, 0.32)   # Koridor yan duvarları
C_BARRIER    = rgba(0.70, 0.15, 0.10)   # Kapalı yol bariyeri (kırmızı-kahve)
C_LAUNCH     = rgba(0.20, 0.55, 0.20)   # Fırlatma noktası (yeşil)
C_BOUNDARY   = rgba(0.85, 0.65, 0.10)   # Uçuş sınırı (sarı)


# ── SDF öğe üreticiler ──────────────────────────────────────────────────────

def box_model(name, x, y, z, lx, ly, lz, color, yaw=0.0, static=True, cast_shadow=True):
    shadow = "true" if cast_shadow else "false"
    return f"""
  <model name="{name}">
    {"<static>true</static>" if static else ""}
    <pose>{x:.3f} {y:.3f} {z:.3f} 0 0 {yaw:.4f}</pose>
    <link name="link">
      <collision name="col">
        <geometry><box><size>{lx:.3f} {ly:.3f} {lz:.3f}</size></box></geometry>
      </collision>
      <visual name="vis">
        <cast_shadows>{shadow}</cast_shadows>
        <geometry><box><size>{lx:.3f} {ly:.3f} {lz:.3f}</size></box></geometry>
        <material>
          <ambient>{color}</ambient>
          <diffuse>{color}</diffuse>
          <specular>0.1 0.1 0.1 1</specular>
        </material>
      </visual>
    </link>
  </model>"""


def ground_overlay(name, cx, cy, sx, sy, color, z=0.005):
    """İnce renkli zemin döşemesi (görsel alan işaretleri)"""
    return box_model(name, cx, cy, z, sx, sy, 0.01, color, cast_shadow=False)


def text_label(name, x, y, z, text_label):
    """Yükseltilmiş ince silindir ile yön işareti (metin desteği yok, simge)"""
    return box_model(name, x, y, z, 0.5, 0.5, 0.5, rgba(1, 1, 1))


# ── Zemin ve ışık ────────────────────────────────────────────────────────────

WORLD_HEADER = """<?xml version="1.0"?>
<sdf version="1.6">
<world name="navitas_teknofest_2026">

  <physics type="ode">
    <real_time_update_rate>1000</real_time_update_rate>
    <max_step_size>0.001</max_step_size>
  </physics>

  <scene>
    <ambient>0.6 0.6 0.6 1</ambient>
    <background>0.53 0.81 0.98 1</background>
    <shadows>true</shadows>
    <sky>
      <clouds><speed>12</speed></clouds>
    </sky>
  </scene>

  <include>
    <uri>model://sun</uri>
  </include>

  <!-- Zemin düzlemi -->
  <model name="ground_plane">
    <static>true</static>
    <link name="link">
      <collision name="col">
        <geometry><plane><normal>0 0 1</normal><size>500 500</size></plane></geometry>
      </collision>
      <visual name="vis">
        <geometry><plane><normal>0 0 1</normal><size>500 500</size></plane></geometry>
        <material>
          <ambient>0.45 0.38 0.28 1</ambient>
          <diffuse>0.45 0.38 0.28 1</diffuse>
        </material>
      </visual>
    </link>
  </model>

  <!-- Kamera başlangıç konumu (Gazebo GUI) -->
  <gui fullscreen="0">
    <camera name="user_camera">
      <pose>0 -80 60 0 0.8 1.5708</pose>
      <view_controller>orbit</view_controller>
    </camera>
  </gui>
"""

WORLD_FOOTER = """
</world>
</sdf>
"""


# ── Alan işaretleri ─────────────────────────────────────────────────────────

def make_zone_markers():
    parts = []

    # HTAB zemini (50x50, hafif koyu)
    parts.append(ground_overlay("htab_ground", 0, 0, 50, 50, C_HTAB, z=0.002))

    # İHA iniş bölgesi (30x30, mavi)
    parts.append(ground_overlay("inis_bolgesi",
        INIS_CENTER[0], INIS_CENTER[1], 30, 30, C_INIS))

    # Hedef H (2x2, kırmızı)
    parts.append(ground_overlay("hedef_H",
        HB_CENTER[0], HB_CENTER[1], 2.0, 2.0, C_HB, z=0.01))

    # "H" formu için 3 kutu (yatay çubuk + 2 dikey bacak)
    hx, hy = HB_CENTER
    parts.append(box_model("h_left",   hx-0.55, hy, 0.35, 0.3, 2.0, 0.7, C_HB))
    parts.append(box_model("h_right",  hx+0.55, hy, 0.35, 0.3, 2.0, 0.7, C_HB))
    parts.append(box_model("h_center", hx,      hy, 0.35, 0.8, 0.3, 0.7, C_HB))

    # İKA başlangıç bölgesi (1x1, sarı)
    parts.append(ground_overlay("ika_kb",
        IKA_KB[0], IKA_KB[1], 1.0, 1.0, C_IKA_START, z=0.01))

    # Fırlatma noktası işareti
    lx, ly, lz = LAUNCH_POS
    parts.append(ground_overlay("launch_marker", lx, ly, 3.0, 6.0, C_LAUNCH))
    parts.append(box_model("launch_post", lx, ly, 1.5, 0.3, 0.3, 3.0, C_LAUNCH))

    # İHA-UB sınır işaretçileri (300x300 köşe direkler)
    for sx, sy in [(-150,-150),(150,-150),(150,150),(-150,150)]:
        parts.append(box_model(f"ub_corner_{sx}_{sy}",
            sx, sy, 5.0, 1.0, 1.0, 10.0, C_BOUNDARY))

    # HTAB köşe işaretçileri (küçük direkler)
    for sx, sy in [(-25,-25),(25,-25),(25,25),(-25,25)]:
        parts.append(box_model(f"htab_corner_{sx}_{sy}",
            sx, sy, 1.0, 0.4, 0.4, 2.0, rgba(1,0.8,0)))

    return "\n".join(parts)


# ── Koridor yan duvarları ────────────────────────────────────────────────────

def make_corridor_walls():
    """3 koridorun yan duvarları — her zaman mevcuttur, geçişi tanımlar"""
    parts = []
    wall_h = 1.8   # Duvar yüksekliği
    wall_t = 0.35  # Duvar kalınlığı

    # HTAB'ı kuzey-güney yönünde kesen büyük dolgu duvarı
    # Koridor olmayan X bölgeleri moloz duvarlarla dolu
    # Sadece 3 koridor geçiş açıkları bırakılıyor

    # Sol dış duvar: x=-25'den kolay koridoru sol duvarına
    # Kolay: cx=-14, half=2.25 → sol duvar x=-16.25
    lx_kolay_l = CORRIDORS["kolay"]["cx"] - CORRIDORS["kolay"]["width"]/2 - wall_t/2
    lx_kolay_r = CORRIDORS["kolay"]["cx"] + CORRIDORS["kolay"]["width"]/2 + wall_t/2
    lx_orta_l  = CORRIDORS["orta"]["cx"]  - CORRIDORS["orta"]["width"]/2  - wall_t/2
    lx_orta_r  = CORRIDORS["orta"]["cx"]  + CORRIDORS["orta"]["width"]/2  + wall_t/2
    lx_zor_l   = CORRIDORS["zor"]["cx"]   - CORRIDORS["zor"]["width"]/2   - wall_t/2
    lx_zor_r   = CORRIDORS["zor"]["cx"]   + CORRIDORS["zor"]["width"]/2   + wall_t/2

    # Batı dolgu (x=-25 → kolay sol duvar)
    w_west = lx_kolay_l - (-HTAB_HALF)
    parts.append(box_model("wall_west_fill",
        (-HTAB_HALF + lx_kolay_l)/2, 0, wall_h/2,
        w_west, 50, wall_h, C_WALL))

    # Kolay-Orta arası dolgu
    w_km = lx_orta_l - lx_kolay_r
    parts.append(box_model("wall_kolay_orta",
        (lx_kolay_r + lx_orta_l)/2, 0, wall_h/2,
        w_km, 50, wall_h, C_WALL))

    # Orta-Zor arası dolgu
    w_oz = lx_zor_l - lx_orta_r
    parts.append(box_model("wall_orta_zor",
        (lx_orta_r + lx_zor_l)/2, 0, wall_h/2,
        w_oz, 50, wall_h, C_WALL))

    # Doğu dolgu (zor sağ duvar → x=+25)
    w_east = HTAB_HALF - lx_zor_r
    parts.append(box_model("wall_east_fill",
        (lx_zor_r + HTAB_HALF)/2, 0, wall_h/2,
        w_east, 50, wall_h, C_WALL))

    # HTAB çevre duvarları (ince, görsel sınır)
    parts.append(box_model("htab_north", 0,  HTAB_HALF, 0.75, 50, 0.3, 1.5, rgba(0.8,0.7,0.5)))
    parts.append(box_model("htab_south", 0, -HTAB_HALF, 0.75, 50, 0.3, 1.5, rgba(0.8,0.7,0.5)))
    parts.append(box_model("htab_east",  HTAB_HALF, 0, 0.75, 0.3, 50, 1.5, rgba(0.8,0.7,0.5)))
    parts.append(box_model("htab_west", -HTAB_HALF, 0, 0.75, 0.3, 50, 1.5, rgba(0.8,0.7,0.5)))

    return "\n".join(parts)


# ── Kapalı yol bariyerleri ──────────────────────────────────────────────────

def make_path_barriers(open_scenario):
    """Açık senaryo dışındaki 2 koridoru kapatan bariyer blokları"""
    parts = []
    for name, c in CORRIDORS.items():
        if name == open_scenario:
            continue  # Bu koridor açık, bariyer yok

        cx = c["cx"]
        w  = c["width"]
        # Kuzey yarıda bariyer (y=8'de büyük blok)
        parts.append(box_model(
            f"barrier_{name}_north",
            cx, 8.0, 1.2,
            w + 0.4, 2.0, 2.4,
            C_BARRIER
        ))
        # Güney yarıda ikinci bariyer (y=-8'de)
        parts.append(box_model(
            f"barrier_{name}_south",
            cx, -8.0, 1.2,
            w + 0.4, 2.0, 2.4,
            C_BARRIER
        ))
        # "KAPALI" işaretçi (üstte sarı şerit)
        parts.append(box_model(
            f"barrier_{name}_sign",
            cx, 0.0, 2.6,
            w + 0.4, 0.4, 0.4,
            rgba(0.95, 0.75, 0.05)
        ))

    return "\n".join(parts)


# ── Koridor içi moloz (her zaman mevcut, az miktarda) ──────────────────────

def make_corridor_debris(rng):
    """Koridor içine rastgele küçük moloz parçaları (geçişi zorlaştırır)"""
    parts = []
    for name, c in CORRIDORS.items():
        cx, hw = c["cx"], c["width"] / 2 - 0.6
        debris_n = {"kolay": 6, "orta": 10, "zor": 16}[name]
        for i in range(debris_n):
            dx = rng.uniform(-hw, hw)
            dy = rng.uniform(-22, 22)
            # HB ve İKA-KB yakınına koyma
            if abs(dy - HB_CENTER[1]) < 4 or abs(dy - IKA_KB[1]) < 4:
                continue
            dw = rng.uniform(0.2, 0.5)
            dh = rng.uniform(0.1, 0.4)
            parts.append(box_model(
                f"cor_debris_{name}_{i}",
                cx + dx, dy, dh/2,
                dw, dw, dh, C_DEBRIS
            ))
    return "\n".join(parts)


# ── HTAB dışı büyük moloz (gürültü / realist görünüm) ──────────────────────

def make_outer_debris(rng):
    """HTAB çevresinde dağınık büyük moloz yığınları"""
    parts = []
    positions = [
        (-50, 30), (50, -20), (-40, -50), (60, 40),
        (-70, 10), (45, 60),  (-35, 70),  (70, -30),
    ]
    for i, (px, py) in enumerate(positions):
        s = rng.uniform(2.0, 6.0)
        h = rng.uniform(1.0, 3.5)
        yaw = rng.uniform(0, 3.14)
        parts.append(box_model(
            f"outer_debris_{i}",
            px, py, h/2,
            s, s*rng.uniform(0.6,1.4), h,
            C_DEBRIS, yaw=yaw
        ))
    return "\n".join(parts)


# ── Araç modelleri ──────────────────────────────────────────────────────────

def make_iha_model():
    """
    Sabit kanatlı İHA modeli — mancınık başlangıç pozisyonunda.
    Gerçek uçuş için ArduPilot SITL plugin'i buraya eklenir.
    Gövde + kanatlar + kuyruk + kamera silindiri.
    """
    lx, ly, lz = LAUNCH_POS  # (-80, 0, 3)
    C_GOVDE = rgba(0.15, 0.15, 0.20)   # Koyu gri gövde
    C_KANAT = rgba(0.25, 0.25, 0.30)   # Kanatlar
    C_KUYRUK= rgba(0.20, 0.20, 0.25)
    C_CAM   = rgba(0.10, 0.60, 0.90, 0.6)  # Kamera camı (mavi şeffaf)

    parts = []

    # Gövde (1.2m uzun, 0.15m çaplı)
    parts.append(box_model("iha_govde", lx, ly, lz,
        1.2, 0.15, 0.12, C_GOVDE, static=False))

    # Sol kanat
    parts.append(box_model("iha_kanat_sol", lx, ly - 0.85, lz + 0.02,
        0.3, 1.5, 0.04, C_KANAT, static=False))

    # Sağ kanat
    parts.append(box_model("iha_kanat_sag", lx, ly + 0.85, lz + 0.02,
        0.3, 1.5, 0.04, C_KANAT, static=False))

    # Kuyruk yatay
    parts.append(box_model("iha_kuyruk_yatay", lx - 0.55, ly, lz + 0.05,
        0.15, 0.6, 0.03, C_KUYRUK, static=False))

    # Kuyruk dikey
    parts.append(box_model("iha_kuyruk_dikey", lx - 0.55, ly, lz + 0.13,
        0.12, 0.03, 0.2, C_KUYRUK, static=False))

    # Kamera (gövde altında, aşağı bakan silindir)
    parts.append(box_model("iha_kamera", lx + 0.2, ly, lz - 0.09,
        0.12, 0.12, 0.08, C_CAM, static=False))

    # Fırlatma rampası (statik, mancınık temsili)
    C_RAMPA = rgba(0.35, 0.35, 0.35)
    parts.append(box_model("mancinik_rampa", lx, ly, lz - 1.0,
        1.4, 0.2, 2.0, C_RAMPA, static=True))
    parts.append(box_model("mancinik_taban", lx, ly, 0.15,
        2.0, 1.0, 0.3, C_RAMPA, static=True))

    return "\n".join(parts)


def make_ika_model():
    """
    4 tekerlekli diferansiyel sürüş İKA modeli.
    İKA-KB (başlangıç noktası) üzerinde konumlandırılmış.
    Gerçek navigasyon için motor/encoder plugin eklenecek.
    """
    kx, ky = IKA_KB  # (-22, -22)
    kz = 0.18        # Tekerlek yarıçapı kadar yüksek

    C_GOVDE = rgba(0.10, 0.35, 0.15)   # Koyu yeşil gövde
    C_TEK   = rgba(0.12, 0.12, 0.12)   # Siyah tekerlek
    C_CAM   = rgba(0.10, 0.60, 0.90, 0.7)

    parts = []

    # Gövde (0.6m × 0.4m × 0.2m)
    parts.append(box_model("ika_govde", kx, ky, kz + 0.10,
        0.60, 0.40, 0.20, C_GOVDE, static=False))

    # 4 tekerlek (silindir yerine ince kutu kullanıyoruz)
    for wx, wy, label in [
        (kx + 0.20, ky - 0.22, "sol_on"),
        (kx + 0.20, ky + 0.22, "sag_on"),
        (kx - 0.20, ky - 0.22, "sol_arka"),
        (kx - 0.20, ky + 0.22, "sag_arka"),
    ]:
        parts.append(box_model(f"ika_tekerlek_{label}", wx, wy, kz,
            0.18, 0.08, 0.18, C_TEK, static=False))

    # Kamera (önde, öne bakan)
    parts.append(box_model("ika_kamera", kx + 0.32, ky, kz + 0.15,
        0.08, 0.10, 0.08, C_CAM, static=False))

    # GNSS anteni (üstte küçük kutu)
    parts.append(box_model("ika_gnss", kx, ky, kz + 0.22,
        0.06, 0.06, 0.06, rgba(0.9, 0.9, 0.9), static=False))

    return "\n".join(parts)


# ── Ana üretici ─────────────────────────────────────────────────────────────

def generate_world(scenario):
    rng = random.Random(DEBRIS_SEED)

    parts = [WORLD_HEADER]

    # 1. Alan işaretleri
    parts.append("  <!-- === ALAN İŞARETLERİ === -->")
    parts.append(make_zone_markers())

    # 2. Koridor yapısı (yan dolgu duvarları)
    parts.append("  <!-- === KORİDOR YAPISI === -->")
    parts.append(make_corridor_walls())

    # 3. Kapalı yol bariyerleri
    parts.append(f"  <!-- === KAPALI YOL BARİYERLERİ (açık: {scenario.upper()}) === -->")
    parts.append(make_path_barriers(scenario))

    # 4. Koridor içi küçük engeller
    parts.append("  <!-- === KORİDOR İÇİ KÜÇÜK ENGELLER === -->")
    parts.append(make_corridor_debris(rng))

    # 5. Dış moloz (görsel)
    parts.append("  <!-- === DIŞ MOLOZ (görsel) === -->")
    parts.append(make_outer_debris(rng))

    # 6. Araç modelleri
    parts.append("  <!-- === ARAÇLAR === -->")
    parts.append(make_iha_model())
    parts.append(make_ika_model())

    parts.append(WORLD_FOOTER)
    return "\n".join(parts)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Navitas TEKNOFEST 2026 Gazebo Dünya Üretici")
    parser.add_argument(
        "--scenario", "-s",
        choices=["kolay", "orta", "zor", "rastgele"],
        default="kolay",
        help="Açık güzergah senaryosu (default: kolay)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Çıktı dosyası (default: worlds/navitas.world)"
    )
    args = parser.parse_args()

    if args.scenario == "rastgele":
        scenario = random.choice(["kolay", "orta", "zor"])
        print(f"[Navitas] Rastgele seçilen senaryo: {scenario.upper()}")
    else:
        scenario = args.scenario

    out_dir = os.path.join(os.path.dirname(__file__), "worlds")
    os.makedirs(out_dir, exist_ok=True)

    out_path = args.output or os.path.join(out_dir, "navitas.world")

    world_sdf = generate_world(scenario)
    with open(out_path, "w") as f:
        f.write(world_sdf)

    print(f"[Navitas] Dünya dosyası oluşturuldu: {out_path}")
    zorluk = {"kolay": 1.0, "orta": 1.5, "zor": 2.0}[scenario]
    print(f"[Navitas] Açık güzergah: {scenario.upper()} (Zorluk: {zorluk}x)")
    print(f"\nGazebo'yu başlatmak için:")
    print(f"  gazebo {out_path}")
    print(f"\nVeya gzserver+gzclient ayrı:")
    print(f"  gzserver {out_path} &")
    print(f"  gzclient")

    return scenario

if __name__ == "__main__":
    main()
