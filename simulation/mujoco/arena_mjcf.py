"""Arena MJCF üreteci — `simulation/scripts/arena.py` TEK KAYNAK, DETERMİNİSTİK.

Aynı (harita, senaryo, seed) → BAYT-EŞ XML (`uret`) ve bayt-eş HTAB zemin dokusu.
15 saha = 5 harita × 3 senaryo. HTAB merkezi DÜNYA ORİJİNİDİR (0, 0) — tek zon;
arena.py'nin HTAB-yerel çerçevesi burada dünya çerçevesine eşittir (CONTRACTS §3.2:
İKA yerel↔dünya yalnız öteleme; öteleme burada sıfır).

Yönerge geometrisi (şartname s.9, `data/arena_referans/KAYNAK.md`):
  İHA-UB 300×300 · HTAB 50×50 · İHA-İB 30×30 MAVİ · HB 2×2 m, üzerinde KIRMIZI H ·
  3 yol, 1 açık (gizli), 2'si bariyer + moloz tıkamasıyla kapalı.
world_generator.py'nin SDF'inden farklar (D-438 ölçülen kusurlar): iniş alanı 8×8 → 30×30,
H beyaz → kırmızı; yollar ve zemin düz renk kutu değil GERÇEK fotoğraf dokusu
(`dokular/KAYNAK.md`), yol yüzeyi HTAB dokusuna boyanır (spline birebir).

SINIR: fizik İHA uçuşu KİNEMATİKTİR (mocap gövde, aerodinamik yok) — `iha_ucus.py`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
SCRIPTS = BURASI.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(BURASI) not in sys.path:
    sys.path.insert(0, str(BURASI))

import arena                      # noqa: E402  (TEK KAYNAK harita geometrisi)
import araclar                    # noqa: E402
from world_generator import DIFF, SCAN_Z   # noqa: E402  (şerit genişliği, tarama irtifası)

DOKU_DIR = BURASI / "dokular"
URETILEN_DIR = DOKU_DIR / "uretilen"       # harita başına HTAB dokusu (git dışı)
MESH_DIR = araclar.MESH_DIR

# ── Yönerge ölçüleri ────────────────────────────────────────────────────────
IHA_IB_KENAR_M = 30.0                       # İHA-İB 30×30 MAVİ (şartname s.9)
IHA_IB_RGBA = (0.15, 0.35, 0.85, 1.0)
HB_KENAR_M = 2.0                            # HB 2×2 m
HB_PED_RGBA = (0.10, 0.20, 0.60, 1.0)       # küçük mavi ped
H_RGBA = (0.85, 0.08, 0.08, 1.0)            # KIRMIZI H
H_KALINLIK_M = 0.30
IHA_IB_MERKEZ_X = arena.HTAB_HALF + 2.0 + IHA_IB_KENAR_M / 2     # HTAB doğusu (x=+42)
MANCINIK_X = -26.0                          # İHA-FB: HTAB batısı
UB_DUVAR_H = 1.0
HTAB_DOKU_PX = 2048                         # 50 m / 2048 px ≈ 2,44 cm/px
HFOV_RAD = 1.3                              # models/iha/model.sdf scan_camera (iha_haritala.HFOV)
KAM_RES_VARSAYILAN = 1280
SEED_VARSAYILAN = 42
Z_IB, Z_KB, Z_PED, Z_H = 0.03, 0.04, 0.05, 0.07   # yassı işaretler katmanlı (z-fight yok)
LEVEL_RGBA = {"kolay": (0.10, 0.75, 0.20, 1), "orta": (0.90, 0.70, 0.10, 1),
              "zor": (0.85, 0.15, 0.15, 1)}
MOLOZ_MATERYALLER = ("moloz_a", "moloz_b", "moloz_a_koyu")


def _f(v: float, n: int = 3) -> str:
    s = f"{v:.{n}f}"
    return "0." + "0" * n if s == "-" + "0." + "0" * n else s


def _rgba(c) -> str:
    return " ".join(_f(v, 2) for v in c)


# ── HTAB zemin dokusu (toprak + boyanmış stabilize yol) ─────────────────────

def _kaynak_oku(ad: str) -> np.ndarray:
    import cv2
    im = cv2.imread(str(DOKU_DIR / f"{ad}.png"))
    if im is None:
        raise FileNotFoundError(f"doku kaynağı yok: {DOKU_DIR / ad}.png (dokular/uret_karolar.py)")
    return im


def _yama_dokusu(kaynak: np.ndarray, N: int, seed: str, yama_px: int = 512,
                 olcek: float = 1.0) -> np.ndarray:
    """Tekrarsız, DİKİŞSİZ (torus sarmalı) doku: kaynak bölgeden deterministik rastgele
    yamalar alınır, yükseltilmiş-kosinüs pencereyle bindirilerek birleştirilir.
    Ayna döşeme YOK → kaleydoskop deseni yok. `olcek` yamayı büyütür (m/px uyumu)."""
    import cv2
    rng = random.Random(seed)
    kh, kw = kaynak.shape[:2]
    k = max(16, int(round(yama_px / olcek)))       # kaynaktan alınan kenar
    k = min(k, kh, kw)
    w1 = 0.5 - 0.5 * np.cos(2 * np.pi * (np.arange(yama_px) + 0.5) / yama_px)
    pencere = (w1[:, None] * w1[None, :]).astype(np.float32)[..., None]
    top = np.zeros((N, N, 3), np.float32)
    agirlik = np.zeros((N, N, 1), np.float32)
    adim = yama_px // 2
    for gy in range(0, N, adim):
        for gx in range(0, N, adim):
            sx, sy = rng.randrange(0, kw - k + 1), rng.randrange(0, kh - k + 1)
            yama = kaynak[sy:sy + k, sx:sx + k]
            if k != yama_px:
                yama = cv2.resize(yama, (yama_px, yama_px), interpolation=cv2.INTER_AREA)
            if rng.random() < 0.5:
                yama = yama[:, ::-1]
            yama = np.rot90(yama, rng.randrange(4)).astype(np.float32) * pencere
            x0 = gx + rng.randrange(-adim // 4, adim // 4 + 1)
            y0 = gy + rng.randrange(-adim // 4, adim // 4 + 1)
            ys = (np.arange(yama_px) + y0) % N
            xs = (np.arange(yama_px) + x0) % N
            top[np.ix_(ys, xs)] += yama
            agirlik[np.ix_(ys, xs)] += pencere
    return (top / np.maximum(agirlik, 1e-6)).clip(0, 255).astype(np.uint8)


def ub_dokusu() -> np.ndarray:
    """İHA-UB zemini (HTAB dışı): 1024² dikişsiz toprak; MuJoCo tekrarlar."""
    return _yama_dokusu(_kaynak_oku("toprak_kaynak"), 1024, "navitas-ub-toprak", 512, 1.0)


def ub_doku_dosyasi(zorla: bool = False) -> Path:
    import cv2
    URETILEN_DIR.mkdir(parents=True, exist_ok=True)
    p = URETILEN_DIR / "ub_toprak.png"
    if zorla or not p.is_file():
        cv2.imwrite(str(p), ub_dokusu())
    return p


YOL_DOKULARI = ("stabilize", "asfalt")     # dokular/<ad>_kaynak.png (KAYNAK.md)
YOL_DOKUSU_VARSAYILAN = "stabilize"
# yama ölçeği: kaynaktan alınan kenar = 512/olcek px (asfalt kaynağı 300×90 → 90 px'e sığar)
YOL_DOKU_OLCEK = {"stabilize": 1.4, "asfalt": 5.0}


def htab_dokusu(H: dict, lane_w: float, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN) -> np.ndarray:
    """Kuzey-yukarı HTAB dokusu (satır 0 = +Y). Yol şeridi spline boyunca boyanır.
    Zemin = toprak yaması, yol = stabilize (vars.) ya da asfalt yaması; hepsi GERÇEK kare kırpması."""
    import cv2
    if yol_dokusu not in YOL_DOKULARI:
        raise ValueError(f"yol_dokusu {yol_dokusu!r} — {YOL_DOKULARI}")
    N = HTAB_DOKU_PX
    mpp = arena.HTAB / N
    tohum = f"navitas-htab-{H['id']}-{H['scenario']}"
    zemin = _yama_dokusu(_kaynak_oku("toprak_kaynak"), N, tohum + "-zemin", 512, 1.0)
    yol = _yama_dokusu(_kaynak_oku(f"{yol_dokusu}_kaynak"), N, tohum + "-yol", 512,
                       YOL_DOKU_OLCEK[yol_dokusu])
    maske = np.zeros((N, N), np.uint8)
    kal = max(2, int(round(lane_w / mpp)))
    for road in (1, 2, 3):
        pts = np.array([[(x + arena.HTAB_HALF) / mpp, (arena.HTAB_HALF - y) / mpp]
                        for (x, y) in H["paths"][road]], np.int32)
        cv2.polylines(maske, [pts], False, 255, thickness=kal, lineType=cv2.LINE_AA)
    a = cv2.GaussianBlur(maske, (0, 0), 3).astype(np.float32)[..., None] / 255.0
    out = zemin.astype(np.float32) * (1 - a) + yol.astype(np.float32) * a
    return out.clip(0, 255).astype(np.uint8)


def htab_doku_adi(harita_id: int, lv: str, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN) -> str:
    return f"htab_{harita_id}_{lv}_{yol_dokusu}.png"


def htab_doku_dosyasi(H: dict, lv: str, zorla: bool = False,
                      yol_dokusu: str = YOL_DOKUSU_VARSAYILAN) -> Path:
    import cv2
    URETILEN_DIR.mkdir(parents=True, exist_ok=True)
    p = URETILEN_DIR / htab_doku_adi(H["id"], lv, yol_dokusu)
    if zorla or not p.is_file():
        cv2.imwrite(str(p), htab_dokusu(H, DIFF[lv]["lane_w"], yol_dokusu))
    return p


# ── Moloz / bariyer yerleşimi (world_generator.make_zone_debris ile aynı kurallar) ──

def _moloz_boyut(rng: random.Random, buyuk: bool = False):
    k = rng.random()
    if k < 0.30:
        sx, sy, sz = rng.uniform(1.8, 3.6), rng.uniform(1.0, 2.2), rng.uniform(0.2, 0.4)
    elif k < 0.55:
        sx = sy = rng.uniform(0.9, 1.6); sz = rng.uniform(0.8, 1.6)
    elif k < 0.75:
        sx, sy, sz = rng.uniform(1.5, 3.0), rng.uniform(0.15, 0.3), rng.uniform(0.15, 0.4)
    else:
        sx = sy = rng.uniform(0.4, 0.8); sz = rng.uniform(0.3, 0.7)
    if buyuk:
        sx *= 1.4; sy *= 1.4; sz = max(sz, 1.0)
    return sx, sy, sz


def _moloz(rng, ad, x, y, buyuk=False):
    sx, sy, sz = _moloz_boyut(rng, buyuk)
    return {"ad": ad, "x": x, "y": y, "sx": sx, "sy": sy, "sz": sz,
            "yaw": rng.uniform(0, 3.14), "mat": rng.choice(MOLOZ_MATERYALLER)}


def yerlesim(H: dict, lv: str, seed: int, layout: str = "field") -> dict:
    """Deterministik yerleşim: {'bariyer': [...], 'tikama': [...], 'moloz': [...], 'chicane': [...]}."""
    rng = random.Random(f"navitas-mjcf-{H['id']}-{lv}-{seed}")
    lane_w = DIFF[lv]["lane_w"]
    clear = lane_w / 2.0 + 1.2
    kb, hb = H["kb"], H["hb"]
    acik = H["open"]
    out = {"bariyer": [], "tikama": [], "moloz": [], "chicane": []}

    tikama_n = DIFF[lv]["tikama_n"]
    for road in (1, 2, 3):
        if road == acik:
            continue
        path = H["paths"][road]
        bi = int(len(path) * 0.12)
        (bx, by), (nx2, ny2) = path[bi], path[bi + 1]
        byaw = math.atan2(ny2 - by, nx2 - bx) + math.pi / 2
        out["bariyer"].append({"road": road, "x": bx, "y": by, "yaw": byaw, "w": lane_w + 1.0})
        for k in range(tikama_n):
            t = 0.30 + 0.50 * (k / max(1, tikama_n - 1)) + rng.uniform(-0.05, 0.05)
            ti = max(1, min(len(path) - 2, int(len(path) * t)))
            (px, py), (qx, qy) = path[ti], path[ti + 1]
            tyaw = math.atan2(qy - py, qx - px)
            for j in range(max(6, int(lane_w * 1.6))):
                u = rng.uniform(-lane_w / 2 - 0.5, lane_w / 2 + 0.5)
                v = rng.uniform(-1.8, 1.8)
                ox = px + v * math.cos(tyaw) - u * math.sin(tyaw)
                oy = py + v * math.sin(tyaw) + u * math.cos(tyaw)
                out["tikama"].append(_moloz(rng, f"tikama_{road}_{k}_{j}", ox, oy, buyuk=True))

    n = DIFF[lv]["debris_n"]
    if layout == "clean":
        n //= 3
    placed = tries = 0
    while placed < n and tries < n * 15:
        tries += 1
        lx = rng.uniform(-arena.HTAB_HALF + 1, arena.HTAB_HALF - 1)
        ly = rng.uniform(-arena.HTAB_HALF + 1, arena.HTAB_HALF - 1)
        if arena.dist_to_all_paths(lx, ly, H) < clear:
            continue
        if math.hypot(lx - kb[0], ly - kb[1]) < 3.5:
            continue
        if math.hypot(lx - hb[0], ly - hb[1]) < 4.0:
            continue
        out["moloz"].append(_moloz(rng, f"moloz_{placed}", lx, ly))
        placed += 1

    op = H["paths"][acik]
    for wi, t in enumerate((0.25, 0.40, 0.55, 0.70, 0.85)):
        ti = min(len(op) - 2, int(len(op) * t))
        (px, py), (qx, qy) = op[ti], op[ti + 1]
        tyaw = math.atan2(qy - py, qx - px)
        side = 1.0 if wi % 2 == 0 else -1.0
        off = side * (clear + rng.uniform(0.4, 1.1))
        out["chicane"].append(_moloz(rng, f"chicane_{wi}", px - off * math.sin(tyaw),
                                     py + off * math.cos(tyaw), buyuk=True))
    return out


# ── MJCF metni ──────────────────────────────────────────────────────────────

def _kutu_geom(ad, x, y, z, sx, sy, sz, *, yaw=0.0, mat=None, rgba=None, ek=""):
    m = f' material="{mat}"' if mat else ""
    r = f' rgba="{_rgba(rgba)}"' if rgba else ""
    e = f' euler="0 0 {_f(math.degrees(yaw), 2)}"' if abs(yaw) > 1e-9 else ""
    return (f'    <geom name="{ad}" type="box" pos="{_f(x)} {_f(y)} {_f(z)}" '
            f'size="{_f(sx / 2)} {_f(sy / 2)} {_f(sz / 2)}"{e}{m}{r}{ek}/>')


def _moloz_geom(mz):
    return _kutu_geom(mz["ad"], mz["x"], mz["y"], mz["sz"] / 2, mz["sx"], mz["sy"], mz["sz"],
                      yaw=mz["yaw"], mat=mz["mat"])


def _h_harfi(hx, hy):
    k = H_KALINLIK_M
    s = HB_KENAR_M
    return "\n".join([
        _kutu_geom("hb_ped", hx, hy, Z_PED, s, s, 0.02, rgba=HB_PED_RGBA),
        _kutu_geom("hb_H_sol", hx - (s - k) / 2, hy, Z_H, k, s, 0.02, rgba=H_RGBA),
        _kutu_geom("hb_H_sag", hx + (s - k) / 2, hy, Z_H, k, s, 0.02, rgba=H_RGBA),
        _kutu_geom("hb_H_orta", hx, hy, Z_H, s - 2 * k, k, 0.02, rgba=H_RGBA),
    ])


def _kb_karesi(kx, ky, lv):
    """İKA-KB: 2,5 m beyaz kare çizgi (seviye rengi köşe işareti) — disk değil, yol/moloz dokusunu bozmaz."""
    a, t = 2.5, 0.12
    c = LEVEL_RGBA[lv]
    return "\n".join([
        _kutu_geom("kb_N", kx, ky + a / 2, Z_KB, a, t, 0.01, rgba=(1, 1, 1, 1)),
        _kutu_geom("kb_S", kx, ky - a / 2, Z_KB, a, t, 0.01, rgba=(1, 1, 1, 1)),
        _kutu_geom("kb_W", kx - a / 2, ky, Z_KB, t, a, 0.01, rgba=(1, 1, 1, 1)),
        _kutu_geom("kb_E", kx + a / 2, ky, Z_KB, t, a, 0.01, rgba=(1, 1, 1, 1)),
        _kutu_geom("kb_kose", kx - a / 2, ky - a / 2, Z_KB + 0.005, 0.4, 0.4, 0.01, rgba=c),
    ])


def _mancinik(x, y):
    return "\n".join([
        _kutu_geom("mancinik_taban", x, y, 0.075, 3.0, 0.6, 0.15, rgba=(0.45, 0.28, 0.10, 1)),
        f'    <geom name="mancinik_rampa" type="box" pos="{_f(x + 0.2)} {_f(y)} 0.500" '
        f'size="1.400 0.250 0.025" euler="0 -15 0" rgba="0.60 0.40 0.12 1"/>',
        f'    <geom name="mancinik_ayak_L" type="cylinder" pos="{_f(x - 1.3)} {_f(y + 0.25)} 0.400" '
        f'size="0.040 0.400" rgba="0.40 0.40 0.40 1"/>',
        f'    <geom name="mancinik_ayak_R" type="cylinder" pos="{_f(x - 1.3)} {_f(y - 0.25)} 0.400" '
        f'size="0.040 0.400" rgba="0.40 0.40 0.40 1"/>',
    ])


def _ub_duvarlari():
    h, half, t = UB_DUVAR_H, arena.UB_HALF, 0.6
    c = (0.45, 0.45, 0.50, 1)
    return "\n".join([
        _kutu_geom("ub_duvar_N", 0, half, h / 2, arena.UB, t, h, rgba=c),
        _kutu_geom("ub_duvar_S", 0, -half, h / 2, arena.UB, t, h, rgba=c),
        _kutu_geom("ub_duvar_W", -half, 0, h / 2, t, arena.UB, h, rgba=c),
        _kutu_geom("ub_duvar_E", half, 0, h / 2, t, arena.UB, h, rgba=c),
    ])


def ucus_baslangici(H: dict):
    """İHA'nın mancınıktaki başlangıç pozu (x, y, z, yaw) — iha_ucus profiliyle aynı."""
    return (MANCINIK_X, 0.0, 0.5, 0.0)


def uret(harita_id: int = 1, lv: str = "kolay", seed: int = SEED_VARSAYILAN, *,
         asset_kok: Path | None = None, kam_res: int = KAM_RES_VARSAYILAN,
         layout: str = "field", yol_dokusu: str = YOL_DOKUSU_VARSAYILAN) -> str:
    """MJCF metni. `asset_kok=None` → göreli `mesh/`, `dokular/` (KANONİK, hash'lenir);
    verilirse mutlak dizinler (dosya başka yere yazılınca `from_xml_path` çözsün)."""
    if lv not in arena.SCENARIOS:
        raise ValueError(f"senaryo {lv!r} — {arena.SCENARIOS}")
    if yol_dokusu not in YOL_DOKULARI:
        raise ValueError(f"yol_dokusu {yol_dokusu!r} — {YOL_DOKULARI}")
    H = arena.harita(harita_id, lv)
    Y = yerlesim(H, lv, seed, layout)
    kb, hb = H["kb"], H["hb"]
    if asset_kok is None:
        meshdir, texdir = "mesh", "dokular"
    else:
        meshdir = (Path(asset_kok) / "mesh").as_posix()
        texdir = (Path(asset_kok) / "dokular").as_posix()
    doku_ad = "uretilen/" + htab_doku_adi(H["id"], lv, yol_dokusu)
    fx, fy, fz, _ = ucus_baslangici(H)

    geoms = [
        f'    <geom name="ub_zemin" type="plane" pos="0 0 0" size="{_f(arena.UB_HALF)} {_f(arena.UB_HALF)} 0.1" material="toprak"/>',
        f'    <geom name="htab_zemin" type="plane" pos="0 0 0.020" size="{_f(arena.HTAB_HALF)} {_f(arena.HTAB_HALF)} 0.1" material="htab"/>',
        _ub_duvarlari(),
        _kutu_geom("iha_ib", IHA_IB_MERKEZ_X, 0.0, Z_IB, IHA_IB_KENAR_M, IHA_IB_KENAR_M, 0.02,
                   rgba=IHA_IB_RGBA),
        _h_harfi(hb[0], hb[1]),
        _kb_karesi(kb[0], kb[1], lv),
        _mancinik(MANCINIK_X, 0.0),
    ]
    for b in Y["bariyer"]:
        geoms.append(_kutu_geom(f"bariyer_{b['road']}", b["x"], b["y"], 0.5, b["w"], 0.5, 1.0,
                                yaw=b["yaw"], mat="bariyer"))
        geoms.append(_kutu_geom(f"bariyer_{b['road']}_ust", b["x"], b["y"], 1.1, b["w"], 0.4, 0.2,
                                yaw=b["yaw"], rgba=(0.95, 0.95, 0.95, 1)))
    for grup in ("tikama", "moloz", "chicane"):
        geoms.extend(_moloz_geom(mz) for mz in Y[grup])

    kam = [
        f'    <camera name="ucuncu_sahis" pos="-42 -50 30" xyaxes="0.766 -0.643 0 0.232 0.276 0.933" fovy="55"/>',
        f'    <camera name="nadir_genel" pos="8 0 110" fovy="60"/>',
    ]
    ika_yaw = math.pi / 2          # kuzeye bakar (açık yolu ELE VERMEZ)

    return f"""<mujoco model="navitas_arena_{H['id']}_{lv}">
  <!-- NAVITAS MuJoCo arenası · harita {H['id']} · {lv} · seed {seed} · açık yol {arena.ROAD_LABEL[H['open']]} (GİZLİ: renk/şekil ele vermez) -->
  <!-- ÜRETEÇ: simulation/mujoco/arena_mjcf.py · TEK KAYNAK simulation/scripts/arena.py · deterministik -->
  <compiler angle="degree" meshdir="{meshdir}" texturedir="{texdir}"/>
  <option timestep="0.002" gravity="0 0 -9.81"/>
  <statistic extent="70" center="0 0 5"/>
  <visual>
    <global offwidth="{max(kam_res, 1280)}" offheight="{max(kam_res, 1280)}"/>
    <headlight ambient="0.30 0.30 0.30" diffuse="0.12 0.12 0.12" specular="0 0 0"/>
    <quality shadowsize="8192"/>
    <map znear="0.003" zfar="20" shadowscale="2.0" shadowclip="4"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.55 0.70 0.95" rgb2="0.85 0.90 1.00" width="128" height="128"/>
    <texture name="toprak" type="2d" file="uretilen/ub_toprak.png"/>
    <material name="toprak" texture="toprak" texrepeat="12 12" texuniform="false" reflectance="0"/>
    <texture name="htab" type="2d" file="{doku_ad}"/>
    <material name="htab" texture="htab" texrepeat="1 1" texuniform="false" reflectance="0"/>
    <texture name="moloz_a" type="cube" file="moloz_a.png"/>
    <material name="moloz_a" texture="moloz_a" rgba="0.85 0.84 0.82 1" reflectance="0"/>
    <material name="moloz_a_koyu" texture="moloz_a" rgba="0.70 0.68 0.66 1" reflectance="0"/>
    <texture name="moloz_b" type="cube" file="moloz_b.png"/>
    <material name="moloz_b" texture="moloz_b" rgba="0.72 0.70 0.68 1" reflectance="0"/>
    <texture name="bariyer" type="cube" file="bariyer.png"/>
    <material name="bariyer" texture="bariyer" reflectance="0"/>
{araclar.mesh_assetleri()}
  </asset>
  <worldbody>
    <light name="gunes" directional="true" pos="0 0 100" dir="-0.35 0.25 -0.90" diffuse="0.58 0.58 0.55" specular="0.05 0.05 0.05" castshadow="true"/>
{chr(10).join(geoms)}
{chr(10).join(kam)}
{araclar.iha_govdesi(fx, fy, fz, HFOV_RAD, kam_res)}
{araclar.parasut_govdesi()}
{araclar.ika_govdesi(kb[0], kb[1], ika_yaw)}
  </worldbody>
{araclar.ika_aktuatorleri()}
</mujoco>
"""


def hazirla(harita_id: int, lv: str, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN) -> dict:
    """Varlıkları (mesh + HTAB dokusu + UB dokusu) üret; yolları döndür."""
    H = arena.harita(harita_id, lv)
    meshler = araclar.mesh_uret()
    doku = htab_doku_dosyasi(H, lv, yol_dokusu=yol_dokusu)
    ub = ub_doku_dosyasi()
    return {"mesh": meshler, "htab_doku": doku, "ub_doku": ub}


def yaz(harita_id: int, lv: str, yol: Path, seed: int = SEED_VARSAYILAN, **kw) -> Path:
    """MJCF'yi dosyaya yaz (varlıklar hazırlanır; paket dışına yazılıyorsa mutlak dizin)."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    hazirla(harita_id, lv, kw.get("yol_dokusu", YOL_DOKUSU_VARSAYILAN))
    kok = None if yol.resolve().parent == BURASI else BURASI
    yol.write_text(uret(harita_id, lv, seed, asset_kok=kok, **kw), encoding="utf-8")
    return yol


def yukle(harita_id: int, lv: str, seed: int = SEED_VARSAYILAN, **kw):
    """mujoco.MjModel — dosya yazmadan (mutlak varlık dizinleriyle)."""
    import mujoco
    hazirla(harita_id, lv, kw.get("yol_dokusu", YOL_DOKUSU_VARSAYILAN))
    return mujoco.MjModel.from_xml_string(uret(harita_id, lv, seed, asset_kok=BURASI, **kw))


def kanonik_sha256(harita_id: int, lv: str, seed: int = SEED_VARSAYILAN) -> str:
    return hashlib.sha256(uret(harita_id, lv, seed).encode("utf-8")).hexdigest()


# ── Yönerge kontrolü (yüklenmiş modelde) ────────────────────────────────────

def _geom(m, ad):
    import mujoco
    gid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, ad)
    return None if gid < 0 else gid


def yonerge_kontrol(m, harita_id: int, lv: str) -> dict:
    """Her madde: {'ok': bool, 'deger': ...}. Test ve kanıt JSON'u bunu kullanır."""
    import mujoco
    H = arena.harita(harita_id, lv)
    out = {}

    g = _geom(m, "iha_ib")
    if g is None:
        out["iha_ib_30x30_mavi"] = {"ok": False, "deger": "geom yok"}
    else:
        sz = m.geom_size[g]; c = m.geom_rgba[g]
        out["iha_ib_30x30_mavi"] = {
            "ok": bool(abs(sz[0] * 2 - IHA_IB_KENAR_M) < 1e-6 and abs(sz[1] * 2 - IHA_IB_KENAR_M) < 1e-6
                       and c[2] > 0.6 and c[0] < 0.35 and c[1] < 0.5),
            "deger": {"kenar_m": [float(sz[0] * 2), float(sz[1] * 2)], "rgba": [float(v) for v in c]}}

    hids = [_geom(m, n) for n in ("hb_H_sol", "hb_H_sag", "hb_H_orta")]
    if any(i is None for i in hids):
        out["hb_kirmizi_H_2x2"] = {"ok": False, "deger": "H geomları eksik"}
    else:
        kirmizi = all(m.geom_rgba[i][0] > 0.7 and m.geom_rgba[i][1] < 0.25 and m.geom_rgba[i][2] < 0.25
                      for i in hids)
        sol, sag = hids[0], hids[1]
        genislik = (m.geom_pos[sag][0] + m.geom_size[sag][0]) - (m.geom_pos[sol][0] - m.geom_size[sol][0])
        yukseklik = m.geom_size[sol][1] * 2
        ped = _geom(m, "hb_ped")
        out["hb_kirmizi_H_2x2"] = {
            "ok": bool(kirmizi and abs(genislik - HB_KENAR_M) < 1e-6 and abs(yukseklik - HB_KENAR_M) < 1e-6
                       and ped is not None),
            "deger": {"kirmizi": bool(kirmizi), "genislik_m": float(genislik), "yukseklik_m": float(yukseklik)}}

    bariyerli = [r for r in (1, 2, 3) if _geom(m, f"bariyer_{r}") is not None]
    out["acik_yol_tek_bariyersiz"] = {
        "ok": bool(len(bariyerli) == 2 and H["open"] not in bariyerli),
        "deger": {"bariyerli_yollar": bariyerli, "acik": H["open"]}}

    adlar = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]
    n_moloz = sum(a.startswith("moloz_") for a in adlar)
    n_tikama = sum(a.startswith("tikama_") for a in adlar)
    out["moloz_dagilmis"] = {"ok": bool(n_moloz >= 40 and n_tikama >= 12),
                             "deger": {"moloz": n_moloz, "tikama": n_tikama,
                                       "chicane": sum(a.startswith("chicane_") for a in adlar)}}

    ika = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "ika")
    kutle = float(m.body_subtreemass[ika]) if ika >= 0 else None
    n_teker = sum(1 for j in araclar.IKA_EKLEMLER
                  if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, j) >= 0)
    out["ika_ddr_fizik"] = {"ok": bool(ika >= 0 and kutle is not None
                                       and abs(kutle - araclar.IKA_KUTLE_KG) < 0.05
                                       and n_teker == 4 and m.nu == 4),
                            "deger": {"kutle_kg": kutle, "teker_eklemi": n_teker, "aktuator": int(m.nu)}}

    kam = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "scan_camera")
    iha = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "iha")
    fovy = float(m.cam_fovy[kam]) if kam >= 0 else None
    out["iha_mocap_scan_camera"] = {
        "ok": bool(kam >= 0 and iha >= 0 and m.body_mocapid[iha] >= 0
                   and fovy is not None and abs(fovy - math.degrees(HFOV_RAD)) < 1e-3),
        "deger": {"fovy_derece": fovy, "hfov_rad": HFOV_RAD}}

    hz = _geom(m, "htab_zemin")
    out["htab_50x50_dokulu"] = {"ok": bool(hz is not None and abs(m.geom_size[hz][0] * 2 - arena.HTAB) < 1e-6
                                           and m.geom_matid[hz] >= 0),
                                "deger": {"kenar_m": float(m.geom_size[hz][0] * 2) if hz is not None else None}}
    mancinik = _geom(m, "mancinik_rampa")
    out["mancinik_iha_fb"] = {"ok": bool(mancinik is not None and m.geom_pos[mancinik][0] < -arena.HTAB_HALF),
                              "deger": {"x": float(m.geom_pos[mancinik][0]) if mancinik is not None else None}}
    return out


def olcumler(harita_id: int, lv: str, seed: int = SEED_VARSAYILAN) -> dict:
    """Kanıt JSON'u: sha256, süreler, geom sayıları, yönerge kontrolü."""
    import mujoco
    t0 = time.perf_counter()
    xml = uret(harita_id, lv, seed)
    t_uret = time.perf_counter() - t0
    t0 = time.perf_counter()
    m = yukle(harita_id, lv, seed)
    t_yukle = time.perf_counter() - t0
    H = arena.harita(harita_id, lv)
    doku = htab_doku_dosyasi(H, lv)
    return {
        "harita": harita_id, "senaryo": lv, "seed": seed,
        "acik_yol": H["open"], "acik_yol_etiket": arena.ROAD_LABEL[H["open"]],
        "kb_xy": [round(H["kb"][0], 3), round(H["kb"][1], 3)],
        "hb_xy": [round(H["hb"][0], 3), round(H["hb"][1], 3)],
        "htab_merkez_dunya": [0.0, 0.0],
        "iha_ib_merkez": [IHA_IB_MERKEZ_X, 0.0], "iha_ib_kenar_m": IHA_IB_KENAR_M,
        "mancinik_xy": [MANCINIK_X, 0.0],
        "mjcf_kanonik_sha256": hashlib.sha256(xml.encode("utf-8")).hexdigest(),
        "mjcf_bayt": len(xml.encode("utf-8")),
        "htab_doku_sha256": hashlib.sha256(doku.read_bytes()).hexdigest(),
        "mjcf_uretim_ms": round(t_uret * 1000, 1),
        "mjcf_yukleme_ms": round(t_yukle * 1000, 1),
        "ngeom": int(m.ngeom), "nbody": int(m.nbody), "ncam": int(m.ncam), "nu": int(m.nu),
        "yonerge": yonerge_kontrol(m, harita_id, lv),
        "sinir": "İHA uçuşu KİNEMATİK (mocap); aerodinamik yok. Modeller basitleştirilmiş (D-438 ek).",
    }


def main():
    ap = argparse.ArgumentParser(description="NAVITAS arena MJCF üreteci (deterministik)")
    ap.add_argument("--map", type=int, default=1, choices=range(1, arena.HARITA_N + 1))
    ap.add_argument("--level", default="kolay", choices=arena.SCENARIOS)
    ap.add_argument("--seed", type=int, default=SEED_VARSAYILAN)
    ap.add_argument("--out", default=None, help="MJCF çıktı dosyası (vars.: yazma, ölçüm bas)")
    ap.add_argument("--hepsi", action="store_true", help="15 haritanın ölçümünü JSON olarak bas")
    ap.add_argument("--kanit-kok", default=None,
                    help="--hepsi ile: <kok>/harita_<h>_<lv>/arena_<h>_<lv>.json yaz + özet")
    a = ap.parse_args()
    if a.hepsi:
        rows = [olcumler(h, lv, a.seed) for h in range(1, arena.HARITA_N + 1) for lv in arena.SCENARIOS]
        if a.kanit_kok:
            kok = Path(a.kanit_kok)
            for r in rows:
                d = kok / f"harita_{r['harita']}_{r['senaryo']}"
                d.mkdir(parents=True, exist_ok=True)
                (d / f"arena_{r['harita']}_{r['senaryo']}.json").write_text(
                    json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
            ozet = {"harita_n": len(rows),
                    "yonerge_hepsi_ok": all(v["ok"] for r in rows for v in r["yonerge"].values()),
                    "mjcf_uretim_ms_ort": round(sum(r["mjcf_uretim_ms"] for r in rows) / len(rows), 1),
                    "mjcf_yukleme_ms_ort": round(sum(r["mjcf_yukleme_ms"] for r in rows) / len(rows), 1),
                    "ngeom_min_maks": [min(r["ngeom"] for r in rows), max(r["ngeom"] for r in rows)],
                    "sha256": {f"{r['harita']}_{r['senaryo']}": r["mjcf_kanonik_sha256"] for r in rows}}
            (kok / "arena_ozeti_15.json").write_text(json.dumps(ozet, ensure_ascii=False, indent=1),
                                                     encoding="utf-8")
            print(json.dumps(ozet, ensure_ascii=False, indent=1))
            return
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    if a.out:
        p = yaz(a.map, a.level, Path(a.out), a.seed)
        print(f"[arena_mjcf] yazıldı: {p}")
    print(json.dumps(olcumler(a.map, a.level, a.seed), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
