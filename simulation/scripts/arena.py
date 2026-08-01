"""
Navitas arena geometrisi — TEK KAYNAK (gerçekçi KIVRIMLI haritalar).

5 HARİTA × 3 senaryo = 15 deterministik saha. Tasarım ilkeleri (2026-07-07 redesign):
  · İKA-KB güneyde, HB kuzeyde ama HİZALI DEĞİL (|dx| ≥ 6 m) → İKA'nın önünde
    DÜMDÜZ açık koridor ASLA yok (v15'in en büyük hatası buydu).
  · 3 yol KB'den ayrılır, ayrı koridorlarda MEANDER (kıvrım) yaparak HB'de birleşir.
    Yollar Catmull-Rom spline ile yumuşatılır — gerçek enkaz arası geçit hissi.
  · Her periyotta 1 yol açık, 2'si moloz yığınıyla KAPALI; hangisi açık GİZLİ
    (harita+senaryo seed'inden türetilir, renk/şekil ele vermez).

Yapı (şartname):
  İHA-UB  : 300×300 m uçuş bölgesi (dışına çıkmak = eleme).
  HTAB    : UB içinde 50×50 m moloz sahası.
  İKA     : KB'den kalkar, İHA'nın gönderdiği koordinat haritasıyla açık yolu izler.

Tüm geometri HTAB-YERELdir (merkez = HTAB merkezi). Dünyaya yazarken world_generator
zon merkeziyle öteler.
"""
import math
import random
from functools import lru_cache

# ── Bölge boyutları ───────────────────────────────────────────────────────────
UB        = 300.0          # İHA-UB 300×300
UB_HALF   = UB / 2.0
HTAB      = 50.0           # HTAB 50×50
HTAB_HALF = HTAB / 2.0

SCENARIOS = ("kolay", "orta", "zor")
HARITA_N  = 5              # üretilen gerçekçi harita sayısı (--map 1..5)

ROAD_LABEL = {1: "sol", 2: "orta", 3: "sag"}
# Üç HTAB zonunun Gazebo dünya koordinatları. World üretimi ve navigasyon aynı
# kaynağı kullanır; yerel waypoint'in yanlış zona sürüklenmesi böylece engellenir.
ZONE_POS = {"kolay": (-90.0, 0.0), "orta": (0.0, 0.0), "zor": (90.0, 0.0)}

# Yol koridor omurgaları (yerel X) — meander bu eksen etrafında salınır
KORIDOR = {1: -16.0, 2: 0.0, 3: 16.0}
# Kıvrım genliği (zorluk arttıkça daha keskin/derin viraj)
WIND_AMP = {"kolay": 3.0, "orta": 4.5, "zor": 5.5}
# Komşu yolların merkez hatları arasında korunacak asgari boşluk
MIN_ARA = 8.0

ROAD_Y0 = -20.0            # yolların güney bandı
ROAD_Y1 =  20.0            # yolların kuzey bandı
KB_Y    = -23.0            # İKA başlangıç y
HB_Y    =  21.0            # HB y
START_Z = 0.21             # İKA başlangıç z (teker yarıçapı + aks)


# ── Spline yardımcıları ───────────────────────────────────────────────────────

def _catmull_rom(pts, step=1.2):
    """Kontrol noktalarından geçen Catmull-Rom spline'ı ~step aralıkla örnekle.
    (Uçlar için ilk/son nokta çoğaltılır — spline tüm noktalarından GEÇER.)"""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        seg = math.dist(p1, p2)
        n = max(2, int(seg / step))
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(tuple(pts[-1]))
    return out


def _downsample(path, step=2.0):
    """Yoğun polyline'ı ~step aralıklı waypoint listesine indir (İKA takibi için)."""
    out = [path[0]]
    for p in path[1:-1]:
        if math.dist(p, out[-1]) >= step:
            out.append(p)
    out.append(path[-1])
    return out


# ── HARİTA ÜRETİMİ (deterministik: harita no + senaryo) ───────────────────────

MIN_KIVRIM = 6.0   # her yolun KB→HB düz çizgisinden MAKS sapması en az bu olmalı (m)
                   # (≈0 = düz koridor — v15'in ana tasarım hatası; ASLA kabul edilmez)


def _kivrim(path):
    """Yolun, kendi başlangıç→bitiş düz çizgisinden MAKSİMUM sapması (m)."""
    a, b = path[0], path[-1]
    return max(_dist_point_seg(x, y, a[0], a[1], b[0], b[1]) for (x, y) in path)


@lru_cache(maxsize=32)
def harita(harita_id=1, scenario="kolay"):
    """Gerçekçi kıvrımlı saha üret → dict:
      kb        : İKA başlangıcı (yerel x,y) — güneyde
      hb        : Hedef Bölge (yerel x,y) — kuzeyde, KB ile HİZASIZ (|dx|≥6)
      open      : açık yol no (1/2/3) — GİZLİ (seed'den)
      paths     : {1,2,3: yoğun polyline [(x,y),...]} KB→HB kıvrımlı
      ctrl      : {road: kontrol noktaları} (moloz yerleşimi/debug için)

    KALİTE GARANTİSİ (deneme döngüsü): 3 yolun HER BİRİ en az MIN_KIVRIM sapmalı
    (düz koridor yasak) ve |KB→HB dx| ≥ 6 m. Kısıtı sağlamayan aday deterministik
    olarak atılıp bir sonraki alt-seed denenir → aynı (harita, senaryo) HEP aynı
    sahayı verir ama asla düz/hizalı saha veremez."""
    amp = WIND_AMP.get(scenario, 4.0)

    for deneme in range(64):
        rng = random.Random(f"navitas-harita-{harita_id}-{scenario}-{deneme}")

        # KB güney-ortada hafif rastgele; HB kuzeyde ve KB'DEN UZAK (dümdüz hat YOK)
        kbx = rng.uniform(-5.0, 5.0)
        while True:
            hbx = rng.uniform(-12.0, 12.0)
            if abs(hbx - kbx) >= 6.0:
                break
        kb, hb = (kbx, KB_Y), (hbx, HB_Y)

        # Meander kontrol y'leri (tüm yollar için ortak → ayrıklık kolay garanti edilir)
        ys = [-15.0, -8.0, -1.0, 6.0, 13.0]

        # Önce ORTA yolun salınımı, sonra sol/sağ ona çarpmayacak şekilde kırpılır
        mid = {y: KORIDOR[2] + rng.uniform(-amp, amp) for y in ys}
        ctrl, paths = {}, {}
        for road in (1, 2, 3):
            base = KORIDOR[road]
            pts = [kb, (kbx + (base - kbx) * 0.45, -19.5)]
            for y in ys:
                if road == 2:
                    x = mid[y]
                else:
                    x = base + rng.uniform(-amp, amp)
                    if road == 1:
                        x = min(x, mid[y] - MIN_ARA)     # soldaki, ortaya yaklaşmasın
                    else:
                        x = max(x, mid[y] + MIN_ARA)     # sağdaki de öyle
                    x = max(-HTAB_HALF + 3.0, min(HTAB_HALF - 3.0, x))
                pts.append((x, y))
            pts.append((hbx + (base - hbx) * 0.45, 17.5))
            pts.append(hb)
            ctrl[road] = pts
            paths[road] = _catmull_rom(pts)

        if min(_kivrim(paths[r]) for r in (1, 2, 3)) >= MIN_KIVRIM:
            return {"id": harita_id, "scenario": scenario, "kb": kb, "hb": hb,
                    "open": rng.choice((1, 2, 3)), "paths": paths, "ctrl": ctrl,
                    "deneme": deneme}

    raise RuntimeError(f"harita {harita_id}/{scenario}: 64 denemede kıvrım kısıtı "
                       f"sağlanamadı (MIN_KIVRIM={MIN_KIVRIM})")


# ── API (world_generator / hakem_log / mission_time bunları kullanır) ─────────

def open_road(scenario: str, harita_id=1) -> int:
    return harita(harita_id, scenario)["open"]


def route_waypoints(road: int, scenario="kolay", harita_id=1):
    """Yolun kıvrımlı merkez hattı, İKA takibine uygun ~2 m aralıklı (KB→HB)."""
    if road not in (1, 2, 3):
        raise ValueError(f"road 1-3 olmalı: {road}")
    return _downsample(harita(harita_id, scenario)["paths"][road])


def kb_yeri(scenario="kolay", harita_id=1):
    return harita(harita_id, scenario)["kb"]


def hb_yeri(scenario="kolay", harita_id=1):
    return harita(harita_id, scenario)["hb"]


# ── Koordinat referans çerçevesi (İKA görü modeli YOK → koordinatla nav) ──────
# İHA, başlangıç REFERANS noktası (KB, dünya xy) + rota noktalarını JSON ile
# yayınlar (iha_haritala → rota.json); İKA yerel farkları kendi konumuna ekler.

def to_world(local_xy, origin):
    """HTAB-yerel (x,y) → dünya (x,y). origin = HTAB merkezi (cx,cy)."""
    return (origin[0] + local_xy[0], origin[1] + local_xy[1])


def start_xyz(origin, scenario="kolay", harita_id=1):
    """İKA başlangıç referans noktası (dünya xyz)."""
    wx, wy = to_world(kb_yeri(scenario, harita_id), origin)
    return (wx, wy, START_Z)


def hb_xyz(origin, scenario="kolay", harita_id=1):
    """Hedef Bölge (dünya xyz)."""
    wx, wy = to_world(hb_yeri(scenario, harita_id), origin)
    return (wx, wy, START_Z)


# ── Yol-açıklık yardımcıları (moloz, koridorları kapatmasın) ──────────────────

def _dist_point_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_to_path(px, py, wps):
    """(px,py)'nin polyline'a en kısa mesafesi — moloz clearance kontrolü."""
    return min(_dist_point_seg(px, py, wps[i][0], wps[i][1],
                               wps[i + 1][0], wps[i + 1][1])
               for i in range(len(wps) - 1))


def dist_to_all_paths(px, py, H):
    """Noktanın 3 yolun HERHANGİ birine en kısa mesafesi."""
    return min(dist_to_path(px, py, H["paths"][r]) for r in (1, 2, 3))
