#!/usr/bin/env python3
"""
Navitas — GERÇEK AFET MOLOZU mesh kütüphanesi üreteci (prosedürel OBJ).

TEKNOFEST prompt (teknofest_gazebo_gercekci_moloz_prompt.txt) §4-8, §6 gereği:
molozlar artık RENKLİ KUTU değil, gerçek yıkılmış betonarme yapıdan çıkmış gibi
siluete sahip mesh'lerdir. Gerçekçilik önceliği: 1) siluet/geometri 2) yerleşim
3) ölçek 4) materyal 5) texture 6) ışık. Bu script (1)+(3)'ü sağlar.

Neden mesh (texture değil): Gazebo Classic 11 + llvmpipe bu projede foto-texture'ı
yüzeye bind EDEMİYOR (ölçüldü, AGENT_REPORTS/GAZEBO_GERCEKCILIK...), ama GEOMETRİ
ve GÖLGE render OLUYOR. Bu yüzden gerçekçilik geometriden gelir.

Üretilenler (deterministik seed → tekrarlanabilir):
  slab_*   : kırık beton döşeme — üstten düzensiz çokgen (dikdörtgen DEĞİL), kalın
  block_*  : düzensiz beton blok — deforme kutu, kırık köşeler
  column_* : kolon/kiriş — uzun, uçları kopuk
  wall_*   : duvar parçası — üst kenarı JAGGED (kırık), fiziksel hacimli
  brick_*  : tuğla/küçük moloz yığını — birkaç köşeli parça

Her mesh XY'de merkezlenir, min z = 0 (zemine oturur), metre ölçeğinde.
Çıktı: simulation/media/meshes/rubble/*.obj + rubble_manifest.json (tip + bbox).

Kullanım:
  .venv/bin/python simulation/scripts/generate_rubble_meshes.py
"""
import argparse
import json
import math
import random
from pathlib import Path

import numpy as np

SIM = Path(__file__).resolve().parents[1]
OUT_DIR = SIM / "media" / "meshes" / "rubble"
MANIFEST = OUT_DIR / "rubble_manifest.json"
SEED = 20260902


# ── OBJ yazıcı: üçgenler + dışa dönük yüz normalleri (flat shading, faceted beton) ──
def write_obj(path, verts, tris):
    V = np.asarray(verts, float)
    # zemine otur: min z = 0
    V[:, 2] -= V[:, 2].min()
    centroid = V.mean(axis=0)
    lines = ["# navitas prosedürel moloz mesh", "o rubble"]
    for x, y, z in V:
        lines.append(f"v {x:.5f} {y:.5f} {z:.5f}")
    nlines, flines = [], []
    ni = 0
    for a, b, c in tris:
        p0, p1, p2 = V[a], V[b], V[c]
        n = np.cross(p1 - p0, p2 - p0)
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            continue
        n /= ln
        fc = (p0 + p1 + p2) / 3.0
        if np.dot(n, fc - centroid) < 0:      # dışa dönük garantile
            n = -n
            a, b, c = a, c, b
        ni += 1
        nlines.append(f"vn {n[0]:.5f} {n[1]:.5f} {n[2]:.5f}")
        flines.append(f"f {a+1}//{ni} {b+1}//{ni} {c+1}//{ni}")
    lines += nlines + flines
    path.write_text("\n".join(lines) + "\n")
    bbox = (V.max(axis=0) - V.min(axis=0)).tolist()
    return {"verts": len(verts), "tris": len(flines), "bbox": [round(v, 4) for v in bbox]}


# ── deforme kutu: 8 köşe rastgele kaydırılır → kırık blok/kolon ──
def _deformed_box(rng, sx, sy, sz, jitter=0.10, end_break=0.0):
    # KÜTLESEL blok: köşe kaydırması AZ (dikenli/sivri değil, köşeli-blok). Gerçek
    # kırık beton düz kırılma yüzeylerine sahiptir, keskin çıkıntılara değil.
    base = [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
    verts = []
    for (x, y, z) in base:
        jx = rng.uniform(-jitter, jitter)
        jy = rng.uniform(-jitter, jitter)
        jz = rng.uniform(-jitter * 0.6, jitter * 0.6)
        # uçları (|x|=1) daha çok kopar (kolon/kiriş kırık uç hissi)
        eb = end_break if abs(x) > 0.5 else 0.0
        jx += rng.uniform(-eb, eb)
        jz += rng.uniform(-eb, eb)
        verts.append(((x * 0.5 + jx) * sx, (y * 0.5 + jy) * sy, (z * 0.5 + jz + 0.5) * sz))
    # 6 yüz × 2 üçgen
    q = [(0, 1, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5, 1),
         (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    tris = []
    for f in q:
        if len(f) == 3:
            tris.append(f)
        else:
            a, b, c, d = f
            tris += [(a, b, c), (a, c, d)]
    return verts, tris


def slab(rng):
    """Kırık beton döşeme: üstten DÜZENSİZ çokgen (dikdörtgen değil), kalın."""
    ax = rng.uniform(0.7, 1.6)
    ay = rng.uniform(0.45, 1.15)
    th = rng.uniform(0.10, 0.32)
    n = rng.randint(6, 9)
    ring = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.08, 0.08)
        rx = ax * (0.88 + 0.24 * rng.random())      # yarıçap oynaması AZ → köşeli ama
        ry = ay * (0.88 + 0.24 * rng.random())      #   sivri/dikensiz düzensiz levha
        x, y = rx * math.cos(a), ry * math.sin(a)
        if rng.random() < 0.14:                     # hafif köşe kırığı (derin oyuk YOK)
            x *= 0.80
            y *= 0.80
        ring.append((x, y))
    verts = [(x, y, th) for (x, y) in ring]          # üst halka
    verts += [(x * rng.uniform(0.90, 1.0), y * rng.uniform(0.90, 1.0), 0.0)
              for (x, y) in ring]                    # alt halka (kırık taban)
    cx = sum(x for x, _ in ring) / n
    cy = sum(y for _, y in ring) / n
    ct, cb = 2 * n, 2 * n + 1
    verts += [(cx, cy, th), (cx, cy, 0.0)]           # üst/alt merkez
    tris = []
    for i in range(n):
        j = (i + 1) % n
        tris.append((ct, i, j))                       # üst kapak (merkezden yelpaze)
        tris.append((cb, n + j, n + i))               # alt kapak
        tris += [(i, n + i, n + j), (i, n + j, j)]    # yan
    return verts, tris


def block(rng):
    return _deformed_box(rng, rng.uniform(0.40, 0.95), rng.uniform(0.35, 0.85),
                         rng.uniform(0.30, 0.80), jitter=0.11)


def column(rng):
    L = rng.uniform(1.3, 3.0)
    t = rng.uniform(0.22, 0.5)
    t2 = rng.uniform(0.22, 0.5)
    return _deformed_box(rng, L, t, t2, jitter=0.08, end_break=0.10)


def wall(rng):
    """Duvar parçası: üst kenar JAGGED (kırık), fiziksel hacimli.
    Konveks trapez prizmalara böler → sağlam üçgenleme."""
    L = rng.uniform(1.1, 2.7)
    H = rng.uniform(0.6, 1.7)
    T = rng.uniform(0.14, 0.26)
    n = rng.randint(5, 9)
    xs = np.linspace(-L / 2, L / 2, n + 1)
    tops = [H * rng.uniform(0.62, 1.0) for _ in range(n + 1)]
    verts, tris = [], []
    for i in range(n):
        x0, x1 = xs[i], xs[i + 1]
        h0, h1 = tops[i], tops[i + 1]
        base = len(verts)
        # trapez prizma köşeleri: ön(y=-T/2) 0..3, arka(y=+T/2) 4..7
        verts += [(x0, -T / 2, 0), (x1, -T / 2, 0), (x1, -T / 2, h1), (x0, -T / 2, h0),
                  (x0, T / 2, 0), (x1, T / 2, 0), (x1, T / 2, h1), (x0, T / 2, h0)]
        q = [(0, 1, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        for f in q:
            f = tuple(base + k for k in f)
            if len(f) == 3:
                tris.append(f)
            else:
                a, b, c, d = f
                tris += [(a, b, c), (a, c, d)]
    return verts, tris


def brickpile(rng):
    """Tuğla/küçük moloz yığını: birkaç küçük köşeli parça bir mesh'te."""
    verts, tris = [], []
    m = rng.randint(3, 6)
    for _ in range(m):
        sx = rng.uniform(0.14, 0.34)
        sy = rng.uniform(0.10, 0.24)
        sz = rng.uniform(0.08, 0.20)
        bv, bt = _deformed_box(rng, sx, sy, sz, jitter=0.13)
        ox = rng.uniform(-0.32, 0.32)
        oy = rng.uniform(-0.28, 0.28)
        oz = rng.uniform(0.0, 0.16)
        base = len(verts)
        verts += [(x + ox, y + oy, z + oz) for (x, y, z) in bv]
        tris += [(a + base, b + base, c + base) for (a, b, c) in bt]
    return verts, tris


def _yawed_chunk(rng, sx, sy, sz, ox, oy, oz, jitter=0.12):
    """Tek deforme kutu parçası, z ekseninde döndürülmüş, (ox,oy,oz)'a taşınmış.
    (verts, tris) döner — yığın mesh'lerinde iç parça olarak kullanılır."""
    bv, bt = _deformed_box(rng, sx, sy, sz, jitter=jitter)
    cyaw = rng.uniform(0, 2 * math.pi)
    c, s = math.cos(cyaw), math.sin(cyaw)
    verts = [(x * c - y * s + ox, x * s + y * c + oy, z + oz) for (x, y, z) in bv]
    return verts, bt


def pile(rng):
    """YOĞUNLUK OMURGASI: tek mesh'te 12-20 karışık boy enkaz parçası, kubbe biçimli
    yığın (merkez daha yüksek). Bir çizim çağrısı = onlarca parça → yoğun + hızlı."""
    verts, tris = [], []
    m = rng.randint(12, 20)
    R = rng.uniform(1.0, 1.9)
    for _ in range(m):
        k = rng.random()
        if k < 0.50:      # küçük kırıntı
            sx, sy, sz = rng.uniform(0.14, 0.44), rng.uniform(0.11, 0.36), rng.uniform(0.10, 0.28)
        elif k < 0.85:    # orta parça
            sx, sy, sz = rng.uniform(0.4, 0.9), rng.uniform(0.28, 0.68), rng.uniform(0.18, 0.48)
        else:             # büyük levha parçası
            sx, sy, sz = rng.uniform(0.8, 1.5), rng.uniform(0.45, 1.0), rng.uniform(0.14, 0.4)
        rr = R * math.sqrt(rng.random())
        aa = rng.uniform(0, 2 * math.pi)
        ox, oy = rr * math.cos(aa), rr * math.sin(aa)
        oz = max(0.0, (1.0 - rr / R)) * rng.uniform(0.10, 0.55)   # kubbe: merkez yüksek
        base = len(verts)
        v, t = _yawed_chunk(rng, sx, sy, sz, ox, oy, oz)
        verts += v
        tris += [(a + base, b + base, c + base) for (a, b, c) in t]
    return verts, tris


def crumble(rng):
    """Küçük yoğun kırıntı yığını (5-9 ufak parça, tek mesh) — mikro dağılım için."""
    verts, tris = [], []
    m = rng.randint(5, 9)
    R = rng.uniform(0.35, 0.75)
    for _ in range(m):
        sx, sy, sz = rng.uniform(0.10, 0.30), rng.uniform(0.08, 0.24), rng.uniform(0.06, 0.20)
        rr = R * math.sqrt(rng.random())
        aa = rng.uniform(0, 2 * math.pi)
        ox, oy = rr * math.cos(aa), rr * math.sin(aa)
        base = len(verts)
        v, t = _yawed_chunk(rng, sx, sy, sz, ox, oy, rng.uniform(0, 0.08), jitter=0.14)
        verts += v
        tris += [(a + base, b + base, c + base) for (a, b, c) in t]
    return verts, tris


def beam(rng):
    """Uzun ince kiriş — ahşap kiriş / metal profil (malzeme ile ayrışır)."""
    L = rng.uniform(1.2, 3.2)
    t = rng.uniform(0.08, 0.20)
    t2 = rng.uniform(0.08, 0.22)
    return _deformed_box(rng, L, t, t2, jitter=0.07, end_break=0.08)


BUILDERS = {"slab": (slab, 6), "block": (block, 6), "column": (column, 4),
            "wall": (wall, 5), "brick": (brickpile, 5),
            "pile": (pile, 7), "crumble": (crumble, 6), "beam": (beam, 5)}


def main():
    ap = argparse.ArgumentParser(description="Navitas gerçek moloz mesh üreteci")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    manifest = {"meshes": []}
    for typ, (fn, count) in BUILDERS.items():
        for k in range(count):
            name = f"{typ}_{k}"
            verts, tris = fn(rng)
            info = write_obj(out / f"{name}.obj", verts, tris)
            manifest["meshes"].append({"name": name, "type": typ, **info})
    MANIFEST.write_text(json.dumps(manifest, indent=1))
    tv = sum(m["tris"] for m in manifest["meshes"])
    print(f"[rubble-mesh] {len(manifest['meshes'])} mesh yazıldı → {out}")
    print(f"[rubble-mesh] toplam üçgen: {tv} · manifest: {MANIFEST.name}")
    for m in manifest["meshes"]:
        print(f"    {m['name']:10} {m['type']:7} tris={m['tris']:3} "
              f"bbox={m['bbox']}")


if __name__ == "__main__":
    main()
