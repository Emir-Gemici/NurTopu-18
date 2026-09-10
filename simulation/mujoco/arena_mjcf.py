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

RENDER VARYANTLARI (T213-A · K3-b · ON_KAYIT §5.2 — üretim modeli v36 DEĞİŞMEDEN;
VARSAYILAN = v1, karar `VARYANT_VARSAYILAN` yorumunda; RAPOR: results/fdr_sprint_20260910/H1/k3b/RAPOR_K3B.md):
  taban : T212 hâli (`--varyant taban` ile bayt-eş). Yol = `stabilize_kaynak` yaması 5,8× büyütülmüş, şerit
          genişliği DIFF lane_w (4–6 m; üç yol birleşince 15–20 m bant); zemin =
          `toprak_kaynak` 2,3× büyütülmüş — ve o kırpma eğitimde YOL (traversable) etiketli.
  v1    : GERÇEK ÖLÇEKLİ dokular (kaynak m/px SRT irtifasından, `KAYNAK_MPP`): yol şeridi
          `YOL_GENISLIK_M` (4,0 m) gerçek yol kırpması spline boyunca (s,d) haritasıyla
          döşenir, kenarda banket + toprak geçişi; zemin eğitimde ARKA PLAN olan
          sürülmüş toprak (`zemin_surulmus_kaynak`). Yalnız doku dosyası değişir.
  v2    : v1 + alçak güneş (yönlü ışık, castshadow, ortam ışığı düşük → gölge/kontrast).
  v3    : v2 + moloz kutuları yerine düzensiz yığın mesh'leri (ikosfer türevi, trimesh; SciPy yok).
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


def ub_doku_dosyasi(zorla: bool = False, varyant: str = "taban",
                    zemin_dokusu: str = "zemin_surulmus") -> Path:
    import cv2
    URETILEN_DIR.mkdir(parents=True, exist_ok=True)
    p = URETILEN_DIR / ub_doku_adi(varyant, zemin_dokusu)
    if zorla or not p.is_file():
        cv2.imwrite(str(p), ub_dokusu() if varyant == "taban" else ub_dokusu_v1(zemin_dokusu))
    return p


YOL_DOKULARI = ("stabilize", "asfalt")     # dokular/<ad>_kaynak.png (KAYNAK.md)
YOL_DOKUSU_VARSAYILAN = "stabilize"
# yama ölçeği: kaynaktan alınan kenar = 512/olcek px (asfalt kaynağı 300×90 → 90 px'e sığar)
YOL_DOKU_OLCEK = {"stabilize": 1.4, "asfalt": 5.0}


# ── T213-A varyantları ───────────────────────────────────────────────────────
VARYANTLAR = ("taban", "v1", "v2", "v3")
# KARAR (T213-A, 10 Eyl, ölçüm k3b/ozet_k3b.json): 15 haritada üretim semantiğiyle taban 0/15,
# v1 3/15 (3/3 doğru), v2 0/15, v3 0/15 → ON_KAYIT §5.2 kuralı gereği v1 yeni VARSAYILAN.
# taban XML'i `varyant="taban"` ile bayt-eş üretilmeye devam eder (test kilidi: T212 sha).
VARYANT_VARSAYILAN = "v1"
# Kaynak kare ölçekleri (m/px). DJI 0037 SRT rel_alt: kare 3 → 16,3 m, kare 18 → 17,5 m
# (dokular/KAYNAK.md §GSD); yatay FOV 69,7° (DJI 82,1° diyagonal, 4:3), 3840 px:
#   mpp = 2·h·tan(34,85°)/3840 → 16,3 m: 0,00591 · 17,5 m: 0,00634
# Çapraz kontrol: yol_serit_kaynak 678 px × 0,00591 = 4,0 m (kırsal stabilize yol genişliği).
KAYNAK_HFOV_RAD = math.radians(69.7)
KAYNAK_GENISLIK_PX = 3840


def kaynak_mpp(rel_alt_m: float) -> float:
    return 2.0 * rel_alt_m * math.tan(KAYNAK_HFOV_RAD / 2.0) / KAYNAK_GENISLIK_PX


KAYNAK_MPP = {
    "yol_serit_kaynak": kaynak_mpp(16.3),
    "banket_kaynak": kaynak_mpp(16.3),
    "zemin_toprak_kaynak": kaynak_mpp(16.3),
    "zemin_surulmus_kaynak": kaynak_mpp(17.5),
    "asfalt_yol_kaynak": 0.10,            # TAHMİN (araç boyu ~4,4 m ≈ 45 px), KAYNAK.md
}
YOL_GENISLIK_M = 4.0                      # V1 görsel yol şeridi (3,5–4 m; DIFF lane_w değil)
BANKET_M = 0.9                            # yol kenarı banketi (toprak/ot geçişi)
YOL_KENAR_YUMUSAK_M = 0.20                # yol→banket geçişi
BANKET_DIS_YUMUSAK_M = 0.45               # banket→zemin geçişi
YAMA_PX_V1 = 128                          # gerçek ölçekli zemin yaması (2048 dokuda 3,1 m)
YOL_SERIT_KAYNAGI = {"stabilize": "yol_serit_kaynak", "asfalt": "asfalt_yol_kaynak"}
ZEMIN_DOKULARI = ("zemin_surulmus", "zemin_toprak")
ZEMIN_DOKUSU_VARSAYILAN = "zemin_surulmus"
# Işık: (güneş yönü, güneş diffuse, headlight ambient, headlight diffuse)
ISIK = {
    "taban": ("-0.35 0.25 -0.90", "0.58 0.58 0.55", "0.30 0.30 0.30", "0.12 0.12 0.12"),
    # v2: güneş yüksekliği ≈ 40° (dir z = −0.64), gölge uzunluğu ≈ 1,2 × yükseklik; ambient düşük
    "v2": ("-0.62 0.45 -0.64", "0.85 0.83 0.78", "0.18 0.18 0.19", "0.04 0.04 0.04"),
}
ISIK["v1"] = ISIK["taban"]
ISIK["v3"] = ISIK["v2"]


def varyant_dogrula(varyant: str, zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> None:
    if varyant not in VARYANTLAR:
        raise ValueError(f"varyant {varyant!r} — {VARYANTLAR}")
    if zemin_dokusu not in ZEMIN_DOKULARI:
        raise ValueError(f"zemin_dokusu {zemin_dokusu!r} — {ZEMIN_DOKULARI}")


def _yumusak(x: np.ndarray, genislik: float) -> np.ndarray:
    """0→1 kosinüs rampası: x ≤ 0 → 0, x ≥ genislik → 1."""
    t = np.clip(x / max(genislik, 1e-9), 0.0, 1.0)
    return 0.5 - 0.5 * np.cos(np.pi * t)


YOL_UZATMA_M = 3.0      # V1: şerit KB/HB uçlarının ötesine bu kadar uzar (uç kapağı = C-uzayı sıfırı olmasın)


def yol_koridor_uv(path_xy, N: int, mpp: float, yaricap_m: float, parca: int = 32768,
                   uzatma_m: float = 0.0):
    """Spline koridorundaki doku pikselleri için (ys, xs, s_m, d_m):
    s = spline boyunca yay uzunluğu (m), d = imzalı dik uzaklık (m; en yakın parçaya).
    Doku çerçevesi: sütun = (x + HTAB/2)/mpp, satır = (HTAB/2 − y)/mpp (kuzey yukarı).
    `uzatma_m` > 0: yol her iki uçta teğet boyunca bu kadar uzatılır (KB/HB yolun ucunda
    olduğundan uzatılmazsa rota tohumunun C-uzayı açıklığı sıfırdır — ölçüldü, 10 Eyl)."""
    import cv2
    path_xy = list(path_xy)
    if uzatma_m > 0 and len(path_xy) >= 2:
        (x0, y0), (x1, y1) = path_xy[0], path_xy[1]
        L = math.hypot(x1 - x0, y1 - y0) or 1e-9
        path_xy.insert(0, (x0 - (x1 - x0) / L * uzatma_m, y0 - (y1 - y0) / L * uzatma_m))
        (xa, ya), (xb, yb) = path_xy[-2], path_xy[-1]
        L = math.hypot(xb - xa, yb - ya) or 1e-9
        path_xy.append((xb + (xb - xa) / L * uzatma_m, yb + (yb - ya) / L * uzatma_m))
    pts = np.array([[(x + arena.HTAB_HALF) / mpp, (arena.HTAB_HALF - y) / mpp] for (x, y) in path_xy],
                   np.float32)
    R = yaricap_m / mpp
    A, B = pts[:-1], pts[1:]
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-9)
    L = np.sqrt(L2)
    U = AB / L[:, None]
    cum = np.concatenate([[0.0], np.cumsum(L)]).astype(np.float32)
    # Parça başına yerel kutu (hız: her piksel yalnız yakın parçalarla karşılaştırılır; eski
    # "her piksel × her parça" biçimi 3 yolda ~9 s sürüyordu). En yakın parça = en küçük dist².
    d2_en = np.full((N, N), np.inf, np.float32)
    s_en = np.zeros((N, N), np.float32)
    d_en = np.zeros((N, N), np.float32)
    for j in range(len(A)):
        ax, ay = float(A[j, 0]), float(A[j, 1])
        bx, by = float(B[j, 0]), float(B[j, 1])
        x0 = max(0, int(math.floor(min(ax, bx) - R)) - 1); x1 = min(N, int(math.ceil(max(ax, bx) + R)) + 2)
        y0 = max(0, int(math.floor(min(ay, by) - R)) - 1); y1 = min(N, int(math.ceil(max(ay, by) + R)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        PX = (np.arange(x0, x1, dtype=np.float32) - ax)[None, :]
        PY = (np.arange(y0, y1, dtype=np.float32) - ay)[:, None]
        t = np.clip((PX * AB[j, 0] + PY * AB[j, 1]) / L2[j], 0.0, 1.0)
        dx = PX - t * AB[j, 0]
        dy = PY - t * AB[j, 1]
        dist2 = dx * dx + dy * dy
        pen = d2_en[y0:y1, x0:x1]
        iyi = dist2 < pen
        pen[iyi] = dist2[iyi]
        s_en[y0:y1, x0:x1][iyi] = (cum[j] + t * L[j])[iyi]
        d_en[y0:y1, x0:x1][iyi] = (U[j, 0] * dy - U[j, 1] * dx)[iyi]
    ys, xs = np.nonzero(d2_en <= R * R)
    s_out = s_en[ys, xs] * mpp
    d_out = d_en[ys, xs] * mpp
    # uç kesimi: yolun başlangıcının gerisinde / bitişinin ilerisinde kalan pikseller (yarı düzlem)
    # koridor dışı — aksi hâlde yol ucu yelpaze gibi açılır (d radyal, s sabit)
    px = xs.astype(np.float32); py = ys.astype(np.float32)
    bas = (px - A[0, 0]) * U[0, 0] + (py - A[0, 1]) * U[0, 1] < 0
    son = (px - B[-1, 0]) * U[-1, 0] + (py - B[-1, 1]) * U[-1, 1] > 0
    d_out[bas | son] = np.inf
    return ys, xs, s_out, d_out


def _olcekle(kaynak: np.ndarray, kaynak_mpp: float, hedef_mpp: float):
    """Kaynağı hedef m/px'e indirger (INTER_AREA; büyütme gerekiyorsa INTER_LINEAR). (görüntü, mpp)."""
    import cv2
    if hedef_mpp <= kaynak_mpp:
        f = kaynak_mpp / hedef_mpp
        interp = cv2.INTER_LINEAR
    else:
        f = kaynak_mpp / hedef_mpp
        interp = cv2.INTER_AREA
    h, w = kaynak.shape[:2]
    nw, nh = max(2, int(round(w * f))), max(2, int(round(h * f)))
    return cv2.resize(kaynak, (nw, nh), interpolation=interp), hedef_mpp


def _ayna_satir(v_px: np.ndarray, h: int) -> np.ndarray:
    """Boyuna eksende aynalı döşeme (period 2h): dikiş yok."""
    v = np.mod(v_px, 2 * h)
    return np.where(v >= h, 2 * h - 1 - v, v)


def htab_dokusu_v1(H: dict, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
                   zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> np.ndarray:
    """V1: gerçek ölçekli zemin + spline boyunca döşenmiş gerçek yol şeridi + banket.
    Üç yol için en yakın yol seçilir (kesişimde banket öteki yolun üstünü boyamaz)."""
    import cv2
    if yol_dokusu not in YOL_DOKULARI:
        raise ValueError(f"yol_dokusu {yol_dokusu!r} — {YOL_DOKULARI}")
    varyant_dogrula("v1", zemin_dokusu)
    N = HTAB_DOKU_PX
    mpp = arena.HTAB / N
    tohum = f"navitas-htab-v1-{H['id']}-{H['scenario']}-{zemin_dokusu}"
    z_ad = f"{zemin_dokusu}_kaynak"
    zemin = _yama_dokusu(_kaynak_oku(z_ad), N, tohum, YAMA_PX_V1, KAYNAK_MPP[z_ad] / mpp)
    yol_ad = YOL_SERIT_KAYNAGI[yol_dokusu]
    # kaynaklar önce DOKU ÖLÇEĞİNE (mpp) alan-ortalamasıyla indirgenir (remap'in çift-doğrusal
    # örneklemesi 4× küçültmede örtüşme/parıltı üretir); sonra (s,d) → piksel eşlemesi bu ölçekte
    yol_src, m_yol = _olcekle(_kaynak_oku(yol_ad), KAYNAK_MPP[yol_ad], mpp)
    banket_src, m_bnk = _olcekle(_kaynak_oku("banket_kaynak"), KAYNAK_MPP["banket_kaynak"], mpp)
    yh, yw = yol_src.shape[:2]
    bh, bw = banket_src.shape[:2]

    yaricap = YOL_GENISLIK_M / 2 + BANKET_M + BANKET_DIS_YUMUSAK_M
    d_en = np.full((N, N), np.inf, np.float32)
    s_en = np.zeros((N, N), np.float32)
    for road in (1, 2, 3):
        ys, xs, s, d = yol_koridor_uv(H["paths"][road], N, mpp, yaricap, uzatma_m=YOL_UZATMA_M)
        yakin = np.abs(d) < np.abs(d_en[ys, xs])
        d_en[ys[yakin], xs[yakin]] = d[yakin]
        s_en[ys[yakin], xs[yakin]] = s[yakin]
    kor = np.isfinite(d_en)
    ys, xs = np.nonzero(kor)
    d, s = d_en[ys, xs], s_en[ys, xs]

    # yol şeridi: enine d ∈ [−W/2, W/2] → kaynak sütunu; boyuna s → aynalı satır
    map_x = np.full((N, N), -1.0, np.float32)
    map_y = np.full((N, N), -1.0, np.float32)
    map_x[ys, xs] = np.clip((d / YOL_GENISLIK_M + 0.5) * (yw - 1), 0, yw - 1)
    map_y[ys, xs] = _ayna_satir(s / m_yol, yh)
    yol_img = cv2.remap(yol_src, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    # banket: |d| − W/2 → kaynak sütunu (iç kenar = yol kenarı)
    bmap_x = np.full((N, N), -1.0, np.float32)
    bmap_y = np.full((N, N), -1.0, np.float32)
    bmap_x[ys, xs] = np.clip((np.abs(d) - YOL_GENISLIK_M / 2) / m_bnk, 0, bw - 1)
    bmap_y[ys, xs] = _ayna_satir(s / m_bnk + 0.37 * bh, bh)
    bnk_img = cv2.remap(banket_src, bmap_x, bmap_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    a_yol = np.zeros((N, N), np.float32)
    a_bnk = np.zeros((N, N), np.float32)
    a_yol[ys, xs] = _yumusak(YOL_GENISLIK_M / 2 + YOL_KENAR_YUMUSAK_M / 2 - np.abs(d), YOL_KENAR_YUMUSAK_M)
    a_bnk[ys, xs] = _yumusak(YOL_GENISLIK_M / 2 + BANKET_M + BANKET_DIS_YUMUSAK_M - np.abs(d),
                             BANKET_DIS_YUMUSAK_M)
    out = zemin.astype(np.float32)
    out = out * (1 - a_bnk[..., None]) + bnk_img.astype(np.float32) * a_bnk[..., None]
    out = out * (1 - a_yol[..., None]) + yol_img.astype(np.float32) * a_yol[..., None]
    return out.clip(0, 255).astype(np.uint8)


def ub_dokusu_v1(zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> np.ndarray:
    """İHA-UB zemini (v1+): 1024² = 25 m karo (texrepeat 12 / 300 m), gerçek ölçek."""
    varyant_dogrula("v1", zemin_dokusu)
    z_ad = f"{zemin_dokusu}_kaynak"
    mpp = arena.UB / 12 / 1024
    return _yama_dokusu(_kaynak_oku(z_ad), 1024, f"navitas-ub-v1-{zemin_dokusu}", YAMA_PX_V1,
                        KAYNAK_MPP[z_ad] / mpp)


def ub_doku_adi(varyant: str = VARYANT_VARSAYILAN, zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> str:
    return "ub_toprak.png" if varyant == "taban" else f"ub_{zemin_dokusu}_v1.png"


def htab_dokusu(H: dict, lane_w: float, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
                varyant: str = VARYANT_VARSAYILAN,
                zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> np.ndarray:
    """Kuzey-yukarı HTAB dokusu (satır 0 = +Y). Yol şeridi spline boyunca boyanır.
    taban: zemin = toprak yaması, yol = stabilize (vars.) ya da asfalt yaması (lane_w kalınlık);
    v1/v2/v3: `htab_dokusu_v1` (gerçek ölçek, 4 m şerit + banket)."""
    import cv2
    varyant_dogrula(varyant, zemin_dokusu)
    if varyant != "taban":
        return htab_dokusu_v1(H, yol_dokusu, zemin_dokusu)
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


def htab_doku_adi(harita_id: int, lv: str, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
                  varyant: str = VARYANT_VARSAYILAN,
                  zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> str:
    if varyant == "taban":
        return f"htab_{harita_id}_{lv}_{yol_dokusu}.png"
    return f"htab_{harita_id}_{lv}_{yol_dokusu}_{zemin_dokusu}_v1.png"     # v2/v3 aynı dokuyu kullanır


def htab_doku_dosyasi(H: dict, lv: str, zorla: bool = False,
                      yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
                      varyant: str = VARYANT_VARSAYILAN,
                      zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> Path:
    import cv2
    URETILEN_DIR.mkdir(parents=True, exist_ok=True)
    p = URETILEN_DIR / htab_doku_adi(H["id"], lv, yol_dokusu, varyant, zemin_dokusu)
    if zorla or not p.is_file():
        cv2.imwrite(str(p), htab_dokusu(H, DIFF[lv]["lane_w"], yol_dokusu, varyant, zemin_dokusu))
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


# ── v3: düzensiz moloz yığını mesh'leri (trimesh konveks gövde) ─────────────
MOLOZ_MESH_N = 8            # farklı yığın şekli; her moloz birini seçer, <mesh scale> ile boyutlanır


def moloz_mesh_uret(zorla: bool = False) -> dict[str, Path]:
    """Birim kutuya ([-0,5, 0,5]³) normalize edilmiş 8 yığın: ikosfer (42 köşe) yarıçapları
    rastgele bozulur (yıldız-şekilli, köşeli), tabanı düz kesilir, üstü daraltılır.
    SciPy YOK (konveks gövde kullanılmaz). Deterministik (sabit tohum). `mesh/moloz_yigin_<k>.stl`."""
    import trimesh
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for k in range(MOLOZ_MESH_N):
        p = MESH_DIR / f"moloz_yigin_{k}.stl"
        if zorla or not p.is_file():
            rng = np.random.RandomState(7300 + k)
            m = trimesh.creation.icosphere(subdivisions=1, radius=0.5)
            v = np.array(m.vertices, dtype=np.float64)
            v *= (1.0 + rng.uniform(-0.30, 0.30, len(v)))[:, None]          # köşeli yüzey
            v[:, :2] *= (1.0 - 0.35 * np.clip(v[:, 2] + 0.5, 0, 1))[:, None]  # yukarı daralan
            v[:, 2] = np.maximum(v[:, 2], -0.35)                             # tabanı düz
            lo, hi = v.min(0), v.max(0)
            v = (v - (lo + hi) / 2) / (hi - lo)
            trimesh.Trimesh(vertices=v, faces=m.faces, process=False).export(str(p))
        out[f"moloz_yigin_{k}"] = p
    return out


def moloz_mesh_geomlari(Y: dict, seed: int) -> tuple[list[str], str]:
    """v3: yerleşimdeki her moloz için (kutu yerine) ölçekli mesh geom'u + mesh asset satırı.
    Ad, konum, yaw ve materyal yerleşimle AYNI (yalnız şekil değişir)."""
    rng = random.Random(f"navitas-moloz-mesh-{seed}")
    geoms, assetler = [], []
    for grup in ("tikama", "moloz", "chicane"):
        for mz in Y[grup]:
            k = rng.randrange(MOLOZ_MESH_N)
            mad = f"mz_{mz['ad']}"
            assetler.append(f'    <mesh name="{mad}" file="moloz_yigin_{k}.stl" '
                            f'scale="{_f(mz["sx"])} {_f(mz["sy"])} {_f(mz["sz"])}"/>')
            e = f' euler="0 0 {_f(math.degrees(mz["yaw"]), 2)}"'
            geoms.append(f'    <geom name="{mz["ad"]}" type="mesh" mesh="{mad}" '
                         f'pos="{_f(mz["x"])} {_f(mz["y"])} {_f(mz["sz"] / 2)}"{e} material="{mz["mat"]}"/>')
    return geoms, "\n" + "\n".join(assetler)


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
         layout: str = "field", yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
         varyant: str = VARYANT_VARSAYILAN, zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN) -> str:
    """MJCF metni. `asset_kok=None` → göreli `mesh/`, `dokular/` (KANONİK, hash'lenir);
    verilirse mutlak dizinler (dosya başka yere yazılınca `from_xml_path` çözsün).
    `varyant` (T213-A): taban | v1 (doku) | v2 (+ışık/gölge) | v3 (+moloz mesh)."""
    if lv not in arena.SCENARIOS:
        raise ValueError(f"senaryo {lv!r} — {arena.SCENARIOS}")
    if yol_dokusu not in YOL_DOKULARI:
        raise ValueError(f"yol_dokusu {yol_dokusu!r} — {YOL_DOKULARI}")
    varyant_dogrula(varyant, zemin_dokusu)
    H = arena.harita(harita_id, lv)
    Y = yerlesim(H, lv, seed, layout)
    kb, hb = H["kb"], H["hb"]
    if asset_kok is None:
        meshdir, texdir = "mesh", "dokular"
    else:
        meshdir = (Path(asset_kok) / "mesh").as_posix()
        texdir = (Path(asset_kok) / "dokular").as_posix()
    doku_ad = "uretilen/" + htab_doku_adi(H["id"], lv, yol_dokusu, varyant, zemin_dokusu)
    ub_ad = "uretilen/" + ub_doku_adi(varyant, zemin_dokusu)
    gunes_dir, gunes_diffuse, hl_ambient, hl_diffuse = ISIK[varyant]
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
    moloz_assetleri = ""
    if varyant == "v3":
        moloz_geomlari, moloz_assetleri = moloz_mesh_geomlari(Y, seed)
        geoms.extend(moloz_geomlari)
    else:
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
    <headlight ambient="{hl_ambient}" diffuse="{hl_diffuse}" specular="0 0 0"/>
    <quality shadowsize="8192"/>
    <map znear="0.003" zfar="20" shadowscale="2.0" shadowclip="4"/>
  </visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1="0.55 0.70 0.95" rgb2="0.85 0.90 1.00" width="128" height="128"/>
    <texture name="toprak" type="2d" file="{ub_ad}"/>
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
{araclar.mesh_assetleri()}{moloz_assetleri}
  </asset>
  <worldbody>
    <light name="gunes" directional="true" pos="0 0 100" dir="{gunes_dir}" diffuse="{gunes_diffuse}" specular="0.05 0.05 0.05" castshadow="true"/>
{chr(10).join(geoms)}
{chr(10).join(kam)}
{araclar.iha_govdesi(fx, fy, fz, HFOV_RAD, kam_res)}
{araclar.parasut_govdesi()}
{araclar.ika_govdesi(kb[0], kb[1], ika_yaw)}
  </worldbody>
{araclar.ika_aktuatorleri()}
</mujoco>
"""


def hazirla(harita_id: int, lv: str, yol_dokusu: str = YOL_DOKUSU_VARSAYILAN,
            varyant: str = VARYANT_VARSAYILAN, zemin_dokusu: str = ZEMIN_DOKUSU_VARSAYILAN,
            seed: int = SEED_VARSAYILAN) -> dict:
    """Varlıkları (mesh + HTAB dokusu + UB dokusu [+ v3 moloz mesh'leri]) üret; yolları döndür."""
    varyant_dogrula(varyant, zemin_dokusu)
    H = arena.harita(harita_id, lv)
    meshler = araclar.mesh_uret()
    doku = htab_doku_dosyasi(H, lv, yol_dokusu=yol_dokusu, varyant=varyant, zemin_dokusu=zemin_dokusu)
    ub = ub_doku_dosyasi(varyant=varyant, zemin_dokusu=zemin_dokusu)
    out = {"mesh": meshler, "htab_doku": doku, "ub_doku": ub}
    if varyant == "v3":
        out["moloz_mesh"] = moloz_mesh_uret()
    return out


def _hazirla_kw(kw: dict) -> dict:
    return {k: kw[k] for k in ("yol_dokusu", "varyant", "zemin_dokusu") if k in kw}


def yaz(harita_id: int, lv: str, yol: Path, seed: int = SEED_VARSAYILAN, **kw) -> Path:
    """MJCF'yi dosyaya yaz (varlıklar hazırlanır; paket dışına yazılıyorsa mutlak dizin)."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    hazirla(harita_id, lv, seed=seed, **_hazirla_kw(kw))
    kok = None if yol.resolve().parent == BURASI else BURASI
    yol.write_text(uret(harita_id, lv, seed, asset_kok=kok, **kw), encoding="utf-8")
    return yol


def yukle(harita_id: int, lv: str, seed: int = SEED_VARSAYILAN, **kw):
    """mujoco.MjModel — dosya yazmadan (mutlak varlık dizinleriyle)."""
    import mujoco
    hazirla(harita_id, lv, seed=seed, **_hazirla_kw(kw))
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


def olcumler(harita_id: int, lv: str, seed: int = SEED_VARSAYILAN,
             varyant: str = VARYANT_VARSAYILAN) -> dict:
    """Kanıt JSON'u: sha256, süreler, geom sayıları, yönerge kontrolü."""
    import mujoco
    t0 = time.perf_counter()
    xml = uret(harita_id, lv, seed, varyant=varyant)
    t_uret = time.perf_counter() - t0
    t0 = time.perf_counter()
    m = yukle(harita_id, lv, seed, varyant=varyant)
    t_yukle = time.perf_counter() - t0
    H = arena.harita(harita_id, lv)
    doku = htab_doku_dosyasi(H, lv, varyant=varyant)
    return {
        "harita": harita_id, "senaryo": lv, "seed": seed, "varyant": varyant,
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
    ap.add_argument("--varyant", default=VARYANT_VARSAYILAN, choices=VARYANTLAR,
                    help="T213-A render varyantı (taban | v1 doku | v2 +ışık | v3 +moloz mesh)")
    a = ap.parse_args()
    if a.hepsi:
        rows = [olcumler(h, lv, a.seed, a.varyant) for h in range(1, arena.HARITA_N + 1) for lv in arena.SCENARIOS]
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
        p = yaz(a.map, a.level, Path(a.out), a.seed, varyant=a.varyant)
        print(f"[arena_mjcf] yazıldı: {p}")
    print(json.dumps(olcumler(a.map, a.level, a.seed, a.varyant), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
