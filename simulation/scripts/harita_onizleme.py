"""5 gerçekçi haritanın kuşbakışı önizlemesi (matplotlib) → simulation/harita_onizleme/.

Gazebo koşmadan harita geometrisini gözle doğrulamak için: 3 kıvrımlı yol, kapalı
yollardaki tıkama noktaları, KB/HB konumları (hizasız!), saha molozunun dağılımı.
Kullanım:  python3 simulation/scripts/harita_onizleme.py [--senaryo orta]
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import arena
from world_generator import DIFF, make_zone

OUT = Path(__file__).resolve().parents[1] / "harita_onizleme"


def ciz(harita_id, scenario, ax):
    import matplotlib.patches as mp
    z = make_zone(scenario, seed=42, harita_id=harita_id)
    H, lane_w = z["harita"], z["lane_w"]
    rng = z["rng"]
    clear = lane_w / 2.0 + 1.2

    ax.add_patch(mp.Rectangle((-25, -25), 50, 50, fc="#8a7a63", ec="k", lw=1.5))

    # saha moloz örneklemi (world_gen ile aynı mantık — görsel doku)
    n = DIFF[scenario]["debris_n"]
    placed = tries = 0
    while placed < n and tries < n * 15:
        tries += 1
        lx = rng.uniform(-24, 24); ly = rng.uniform(-24, 24)
        if arena.dist_to_all_paths(lx, ly, H) < clear:
            continue
        if math.hypot(lx - H["kb"][0], ly - H["kb"][1]) < 3.5:
            continue
        if math.hypot(lx - H["hb"][0], ly - H["hb"][1]) < 4.0:
            continue
        ax.plot(lx, ly, "s", ms=2.5, color="#c9c3b8", mec="#6e6a60", mew=0.3)
        placed += 1

    # 3 yol — hepsi aynı asfalt; açık yol SADECE bu önizlemede kesikli yeşil
    for road in (1, 2, 3):
        xs = [p[0] for p in H["paths"][road]]
        ys = [p[1] for p in H["paths"][road]]
        ax.plot(xs, ys, "-", lw=lane_w * 1.9, color="#3a3a3e",
                solid_capstyle="round", zorder=3)
        if road == H["open"]:
            ax.plot(xs, ys, "--", lw=1.2, color="#4dff4d", zorder=5, alpha=0.9)

    # kapalı yollarda tıkamalar
    tik = DIFF[scenario]["tikama_n"]
    for road in (1, 2, 3):
        if road == H["open"]:
            continue
        path = H["paths"][road]
        for k in range(tik):
            t = 0.30 + 0.50 * (k / max(1, tik - 1))
            px, py = path[min(len(path) - 1, int(len(path) * t))]
            ax.plot(px, py, "X", ms=9, color="#b0552a", mec="k", zorder=6)
        bx, by = path[int(len(path) * 0.12)]
        ax.plot(bx, by, "s", ms=6, color="red", mec="w", zorder=6)

    kb, hb = H["kb"], H["hb"]
    ax.plot(*kb, "o", ms=10, color="#28c828", mec="k", zorder=7)
    ax.add_patch(mp.Rectangle((hb[0] - 1.6, hb[1] - 1.6), 3.2, 3.2,
                              fc="#2244cc", ec="w", lw=1.5, zorder=7))
    ax.text(hb[0], hb[1], "H", ha="center", va="center", color="w",
            fontsize=9, fontweight="bold", zorder=8)
    ax.annotate("KB", kb, textcoords="offset points", xytext=(8, -10), fontsize=8)

    ax.set_xlim(-27, 27); ax.set_ylim(-27, 27); ax.set_aspect("equal")
    ax.set_title(f"harita {harita_id} · {scenario} · açık={arena.ROAD_LABEL[H['open']]} "
                 f"· KB→HB dx={hb[0]-kb[0]:+.1f} m", fontsize=9)
    ax.tick_params(labelsize=6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--senaryo", default="orta", choices=arena.SCENARIOS)
    args = ap.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 5, figsize=(25, 5.4))
    for hid, ax in zip(range(1, arena.HARITA_N + 1), axes):
        ciz(hid, args.senaryo, ax)
    fig.suptitle(f"Navitas gerçekçi haritalar — senaryo: {args.senaryo} "
                 f"(yeşil kesikli = açık yol, X = tıkama, kırmızı = bariyer)", fontsize=12)
    fig.tight_layout()
    p = OUT / f"haritalar_{args.senaryo}.png"
    fig.savefig(p, dpi=110)
    print(f"önizleme → {p}")


if __name__ == "__main__":
    main()
