#!/usr/bin/env python3
"""
Navitas — relief (heightmap) arazi üreteci.

`world_generator.py --terrain relief` için gri tonlu bir heightmap PNG üretir.
Gazebo Classic 11 heightmap sözleşmesi: kare PNG, kenar = 2^n+1; 0(siyah)=en alçak,
255(beyaz)=en yüksek. Dünyada yükseklik = (v/255) * RELIEF_MAX_Z.

GÜVENLİK KURALI (kullanıcı 2026-09-02): 3 görev sahası (HTAB) + İHA-UB içi DÜMDÜZ
(v=0 → dünya z=0) bırakılır; kabartma yalnız UB DIŞI çevrede olur. Böylece İKA
çarpışması ve 15/15 kapısı ETKİLENMEZ; engebe sadece geniş çekim gerçekçiliğine katar.

Deterministik (sabit seed) → aynı harita her seferinde aynı.

Kullanım:
  .venv/bin/python simulation/scripts/generate_terrain_heightmap.py
  (çıktı: simulation/media/materials/textures/terrain_relief.png)
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import world_generator as W

SIM = Path(__file__).resolve().parents[1]
OUT = SIM / W.RELIEF_HEIGHTMAP_PATH
EDGE = 513                          # 2^9 + 1
FLAT_HALF_M = 152.0                 # merkez düz kare yarı-kenarı (UB 300 + pay)
SEED = 20260902


def _fbm(gx, gy, seed):
    """Birkaç sinüs oktavının toplamı — pürüzsüz, tohumla belirlenen tepe/vadi alanı."""
    rng = np.random.default_rng(seed)
    h = np.zeros_like(gx)
    amp, freq = 1.0, 1.0
    total = 0.0
    for _ in range(5):
        px, py = rng.uniform(0, 2 * math.pi, 2)
        h += amp * (np.sin(gx * freq + px) * np.cos(gy * freq * 0.9 + py))
        total += amp
        amp *= 0.5
        freq *= 2.03
    return h / total                # [-1, 1]


def build(edge=EDGE, size_m=None, seed=SEED):
    size_m = size_m if size_m is not None else W.RELIEF_SIZE_M
    # Piksel merkezlerinin dünya koordinatları (metre), [-size/2, +size/2].
    lin = np.linspace(-size_m / 2.0, size_m / 2.0, edge)
    wy, wx = np.meshgrid(lin, lin, indexing="ij")
    # Normalize (birkaç dalga arena çevresine yayılsın)
    gx, gy = wx / 40.0, wy / 40.0
    h = _fbm(gx, gy, seed)                       # [-1, 1]
    h = (h - h.min()) / (h.max() - h.min())      # [0, 1]

    # Merkezi (görev sahası + UB içi) düze indir: FLAT_HALF içinde 0, dışında
    # FLAT_HALF..FLAT_HALF+ramp arasında yumuşak geçişle kabartmaya aç.
    ramp = 28.0
    cheb = np.maximum(np.abs(wx), np.abs(wy))    # merkeze Chebyshev uzaklığı
    mask = np.clip((cheb - FLAT_HALF_M) / ramp, 0.0, 1.0)  # 0=düz, 1=tam kabartma
    mask = mask * mask * (3 - 2 * mask)          # smoothstep
    h = h * mask                                 # merkez tam 0 (dünya z=0)

    img = np.round(h * 255.0).astype(np.uint8)
    return img


def main():
    ap = argparse.ArgumentParser(description="Navitas relief heightmap üreteci")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--edge", type=int, default=EDGE)
    args = ap.parse_args()

    img = build(edge=args.edge, seed=args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cv2
        ok = cv2.imwrite(str(out), img)
        if not ok:
            raise RuntimeError("cv2.imwrite başarısız")
    except ImportError:
        from PIL import Image
        Image.fromarray(img, mode="L").save(out)

    flat = int((img == 0).sum())
    tot = img.size
    print(f"[heightmap] yazıldı: {out}")
    print(f"[heightmap] {args.edge}x{args.edge} · düz(merkez) piksel: {flat}/{tot} "
          f"(%{100*flat/tot:.1f}) · max yükseklik: {W.RELIEF_MAX_Z} m · "
          f"yatay: {W.RELIEF_SIZE_M} m · merkez düz kare: ±{FLAT_HALF_M} m")


if __name__ == "__main__":
    main()
