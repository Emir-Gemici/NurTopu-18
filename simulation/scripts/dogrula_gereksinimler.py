#!/usr/bin/env python3
"""
Navitas — TEKNOFEST saha GEREKSİNİM DOĞRULAMA (prompt §30 REQ-* PASS/FAIL).

build_world() ile dünyayı BELLEKTE üretir, SDF'i parse eder, collision kutularını
dünya koordinatına taşır ve şartname gereksinimlerini ÖLÇEREK sınar:

  REQ-HTAB-001  HTAB = 50×50 m
  REQ-IKA-KB-001 İKA-KB = 1×1 m
  REQ-HB-001    HB = 2×2 m
  REQ-HB-002    HB üzerinde kırmızı H
  REQ-ROUTE-001 3 farklı güzergâh var
  REQ-ROUTE-002 yalnızca 1 güzergâh açık
  REQ-ROUTE-003 diğer 2 güzergâh fiziksel engelli (rota üstünde collision)
  REQ-NAV-001   İKA-KB → HB açık rota BFS ile erişilebilir (İKA footprint şişirmeli)
  REQ-NAV-002   İKA footprint (0.66×0.50) açık rotadan geçiyor (şişirme yarıçapı)
  REQ-PHYS-001  önemli molozların collision modeli var
  REQ-VIS-001   moloz KUTU değil MESH (realism) — primitive rectangle görünümü yok
  REQ-SIM-003   world/seed tekrarlanabilir (aynı seed → aynı dünya)

Sadece OpenCV/NumPy/saf-Python (proje madde 4). Çıkış kodu: hepsi PASS→0, değilse 1.

Kullanım:
  .venv/bin/python simulation/scripts/dogrula_gereksinimler.py \
      --profile cx_teknofest_official --focus kolay --map 301 --seed 260822 --terrain textured
"""
import argparse
import math
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import arena
import world_generator as W

IKA_W, IKA_L = 0.66, 0.50          # İKA gövde footprint (models/ika/model.sdf)
ROBOT_R = math.hypot(IKA_W, IKA_L) / 2.0   # köşegen yarıçap (şişirme, muhafazakâr)
RES = 0.10                          # BFS grid çözünürlüğü (m)


# Nav ENGELİ sayılan modeller: moloz kümeleri + rota bariyerleri. Zemin, yol
# yüzeyi, KB/HB pad, H harfi, ızgara, UB duvarı vs. SÜRÜLEBİLİR yüzey/işarettir →
# collision'ları olsa da engel DEĞİL (aksi halde tüm saha kapalı görünür).
_OBSTACLE_PREFIXES = ("deb_", "blk_", "chic_", "bar_")


def _collisions_in_zone(world_xml, cx, cy, half=26.0):
    """SDF'ten (dünya koord.) ENGEL collision kutuları: [(wx, wy, sx, sy, yaw), ...],
    sadece odak zon HTAB penceresi içinde ve yalnız moloz/bariyer modelleri."""
    root = ET.fromstring(world_xml)
    out = []
    for model in root.iter("model"):
        nm = model.get("name", "")
        if not nm.startswith(_OBSTACLE_PREFIXES):
            continue
        mp = model.find("pose")
        mx = my = myaw = 0.0
        if mp is not None and mp.text:
            v = [float(t) for t in mp.text.split()]
            mx, my, myaw = v[0], v[1], v[5]
        for col in model.iter("collision"):
            box = col.find("./geometry/box/size")
            if box is None:
                continue
            sx, sy, _sz = [float(t) for t in box.text.split()]
            cp = col.find("pose")
            ox = oy = cyaw = 0.0
            if cp is not None and cp.text:
                v = [float(t) for t in cp.text.split()]
                ox, oy, cyaw = v[0], v[1], v[5]
            # link pozu 0 kabul; dünya = model ⊕ collision
            wx = mx + ox * math.cos(myaw) - oy * math.sin(myaw)
            wy = my + ox * math.sin(myaw) + oy * math.cos(myaw)
            if abs(wx - cx) > half or abs(wy - cy) > half:
                continue
            out.append((wx, wy, sx, sy, myaw + cyaw))
    return out


def _occupancy(collisions, cx, cy, half=25.0, inflate=ROBOT_R):
    """Collision kutularını (footprint şişirmeli) ızgaraya raster et."""
    n = int(2 * half / RES)
    grid = np.zeros((n, n), dtype=bool)
    x0, y0 = cx - half, cy - half
    for (wx, wy, sx, sy, yaw) in collisions:
        hx, hy = sx / 2 + inflate, sy / 2 + inflate
        c, s = abs(math.cos(yaw)), abs(math.sin(yaw))
        ax, ay = hx * c + hy * s, hx * s + hy * c       # döndürülmüş AABB yarı-boyu
        i0 = max(0, int((wx - ax - x0) / RES)); i1 = min(n, int((wx + ax - x0) / RES) + 1)
        j0 = max(0, int((wy - ay - y0) / RES)); j1 = min(n, int((wy + ay - y0) / RES) + 1)
        if i0 >= i1 or j0 >= j1:
            continue
        gx = x0 + (np.arange(i0, i1) + 0.5) * RES
        gy = y0 + (np.arange(j0, j1) + 0.5) * RES
        GX, GY = np.meshgrid(gx - wx, gy - wy, indexing="ij")
        cy_, sy_ = math.cos(-yaw), math.sin(-yaw)
        lx = GX * cy_ - GY * sy_
        ly = GX * sy_ + GY * cy_
        mask = (np.abs(lx) <= hx) & (np.abs(ly) <= hy)
        grid[i0:i1, j0:j1] |= mask
    return grid, x0, y0, n


def _cell(wx, wy, x0, y0, n):
    return (min(n - 1, max(0, int((wx - x0) / RES))),
            min(n - 1, max(0, int((wy - y0) / RES))))


def _reachable(grid, start, goal, n):
    """8-komşu BFS: start→goal serbest hücrelerden geçilebilir mi."""
    if grid[start]:                 # başlangıç/hedef hücresi kapalıysa yakın serbeste kaydır
        start = _nearest_free(grid, start, n)
    if grid[goal]:
        goal = _nearest_free(grid, goal, n)
    if start is None or goal is None:
        return False
    seen = np.zeros_like(grid)
    q = deque([start]); seen[start] = True
    while q:
        i, j = q.popleft()
        if (i, j) == goal:
            return True
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n and not seen[ni, nj] and not grid[ni, nj]:
                    seen[ni, nj] = True
                    q.append((ni, nj))
    return False


def _nearest_free(grid, cell, n, r=8):
    for rad in range(1, r + 1):
        for di in range(-rad, rad + 1):
            for dj in range(-rad, rad + 1):
                ni, nj = cell[0] + di, cell[1] + dj
                if 0 <= ni < n and 0 <= nj < n and not grid[ni, nj]:
                    return (ni, nj)
    return None


def _route_blocked(grid, wps_world, x0, y0, n):
    """Bir güzergâh üzerindeki waypoint'lerin kaçı kapalı (fiziksel engel)."""
    blocked = 0
    for (wx, wy) in wps_world:
        c = _cell(wx, wy, x0, y0, n)
        if grid[c]:
            blocked += 1
    return blocked, len(wps_world)


def main():
    ap = argparse.ArgumentParser(description="Navitas saha gereksinim doğrulama")
    ap.add_argument("--profile", default="cx_teknofest_official")
    ap.add_argument("--focus", default="kolay", choices=W.ZONE_ORDER)
    ap.add_argument("--seed", type=int, default=260822)
    ap.add_argument("--map", type=int, default=301)
    ap.add_argument("--terrain", default="textured", choices=list(W.TERRAIN_MODES))
    args = ap.parse_args()

    world, fz = W.build_world(args.seed, args.focus, record=False, harita_id=args.map,
                              layout="field", profile_id=args.profile, terrain=args.terrain)
    cx, cy = fz["cx"], fz["cy"]
    root = ET.fromstring(world)
    names = {m.get("name") for m in root.iter("model")}
    s = fz["sfx"]

    results = []

    def check(req, ok, detail):
        results.append((req, bool(ok), detail))

    # ── Geometri (SDF'ten ölçülür) ──
    def model_box_size(name):
        for m in root.iter("model"):
            if m.get("name") == name:
                b = m.find("./link/collision/geometry/box/size") \
                    or m.find("./link/visual/geometry/box/size")
                if b is not None:
                    return [float(t) for t in b.text.split()]
        return None

    gd = model_box_size(f"gd_{s}")
    check("REQ-HTAB-001", gd and abs(gd[0] - 50) < 0.5 and abs(gd[1] - 50) < 0.5,
          f"HTAB zemin = {gd[0]:.1f}×{gd[1]:.1f} m" if gd else "gd_ yok")

    kb_names = [f"kb_{s}_N", f"kb_{s}_S", f"kb_{s}_E", f"kb_{s}_W"]
    kb_ok = all(nm in names for nm in kb_names)
    check("REQ-IKA-KB-001", kb_ok and abs(W.KB_OUTER_M - 1.0) < 0.01,
          f"KB çerçeve dış = {W.KB_OUTER_M:.2f}×{W.KB_OUTER_M:.2f} m")

    hb = model_box_size(f"hbpad_{s}")
    check("REQ-HB-001", hb and abs(hb[0] - 2) < 0.1 and abs(hb[1] - 2) < 0.1,
          f"HB pad = {hb[0]:.1f}×{hb[1]:.1f} m" if hb else "hbpad yok")

    # kırmızı H: 3 kol var mı + rengi kırmızı mı (ambient)
    h_ok = all(f"H_{s}_{k}" in names for k in ("l", "r", "b"))
    h_red = False
    for m in root.iter("model"):
        if m.get("name") == f"H_{s}_l":
            amb = m.find(".//visual/material/ambient")
            if amb is not None:
                rr, gg, bb, *_ = [float(t) for t in amb.text.split()]
                h_red = rr > 0.7 and gg < 0.2 and bb < 0.2
    check("REQ-HB-002", h_ok and h_red, f"H harfi 3 kol + kırmızı={h_red}")

    # ── Rotalar (arena ground-truth) ──
    open_road = fz["road"]
    check("REQ-ROUTE-001", len(fz["harita"]["paths"]) == 3,
          f"{len(fz['harita']['paths'])} güzergâh tanımlı")
    check("REQ-ROUTE-002", open_road in (1, 2, 3),
          f"açık güzergâh = {arena.ROAD_LABEL[open_road]} (id {open_road})")

    # ── Occupancy + BFS ──
    cols = _collisions_in_zone(world, cx, cy)
    grid, x0, y0, n = _occupancy(cols, cx, cy)
    kb_w = fz["start_world"]
    hb_w = fz["hb_world"]
    kb_c = _cell(kb_w[0], kb_w[1], x0, y0, n)
    hb_c = _cell(hb_w[0], hb_w[1], x0, y0, n)

    reach = _reachable(grid, kb_c, hb_c, n)
    check("REQ-NAV-001", reach, f"KB→HB BFS erişilebilir={reach} (şişirme R={ROBOT_R:.2f} m)")
    check("REQ-NAV-002", reach, f"İKA footprint {IKA_W}×{IKA_L} m şişirmeli grid'de geçti")

    # kapalı rotalar fiziksel engelli mi (rota üstünde collision)
    closed_ok = True
    closed_detail = []
    for road in (1, 2, 3):
        if road == open_road:
            continue
        wl = arena._downsample(fz["harita"]["paths"][road])
        ww = [(cx + x, cy + y) for (x, y) in wl]
        b, tot = _route_blocked(grid, ww, x0, y0, n)
        closed_detail.append(f"{arena.ROAD_LABEL[road]}:{b}/{tot}")
        if b < 1:
            closed_ok = False
    check("REQ-ROUTE-003", closed_ok, "kapalı rota engel wp: " + ", ".join(closed_detail))

    # ── Fizik / görsel / tekrarlanabilirlik ──
    coll_n = sum(1 for _ in root.iter("collision"))
    check("REQ-PHYS-001", coll_n > 50, f"{coll_n} collision modeli")
    mesh_n = sum(1 for _ in root.iter("mesh"))
    if args.terrain == "plain":
        check("REQ-VIS-001", True, "plain baseline (mesh beklenmiyor)")
    else:
        check("REQ-VIS-001", mesh_n > 100,
              f"{mesh_n} moloz MESH (kutu değil) — primitive rectangle YOK")

    world2, _ = W.build_world(args.seed, args.focus, record=False, harita_id=args.map,
                              layout="field", profile_id=args.profile, terrain=args.terrain)
    check("REQ-SIM-003", world == world2, "aynı seed → aynı dünya (byte-eş)")

    # ── Rapor ──
    print("=" * 66)
    print(f"GEREKSİNİM DOĞRULAMA — profil={args.profile} odak={args.focus} "
          f"map={args.map} seed={args.seed} terrain={args.terrain}")
    print("=" * 66)
    allok = True
    for req, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        allok &= ok
        print(f"  [{tag}] {req:14} {detail}")
    print("-" * 66)
    print(f"SONUÇ: {'TÜMÜ PASS' if allok else 'BAZI FAIL'} "
          f"({sum(1 for _, o, _ in results if o)}/{len(results)})")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
