#!/usr/bin/env python3
"""
Navitas TEKNOFEST 2026 — Gerçekçi Dünya Üreteci (3 zon, sıralı/odaklı)

TEK 300×300 İHA-UB içinde SABİT sırayla 3 adet 50×50 HTAB (soldan sağa):
  kolay (-90,0) · orta (0,0) · zor (+90,0)   — her biri farklı zorluk + renk.
Kayıt SIRALI ilerler: önce kolay, sonra orta, sonra zor (her biri ayrı klip).
--focus <seviye> ile o anki seviyeye 90° dik bakılır; o zonun İHA SERPANTİN taraması +
İKA navigasyonu (açık yolu KIVRILARAK izler) animasyonlanır. Diğer zonlar statik bağlam.

ARENA DÜZENİ (--layout):
  clean : SADECE 3 net koridor (2 molozla TAM kapalı, 1 açık), aralar moloz duvarı. (vars.)
  field : tüm saha moloz dokulu; içinden 3 yol oyulmuş (daha 'afet sahası' hissi).

Kullanım:
  python3 scripts/world_generator.py --focus kolay --seed 42 --record \
      --layout clean --road 2 --output worlds/k.world
"""
import argparse
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import arena
from arena import (UB, UB_HALF, HTAB, HTAB_HALF, dist_to_path, dist_to_all_paths)

ZONE_ORDER = ["kolay", "orta", "zor"]
ZONE_POS = arena.ZONE_POS
# Seviye ayırt edici renk (zon sınır şeridi + İKA başlangıç halkası)
ZONE_COLOR = {"kolay": (0.10, 0.75, 0.20), "orta": (0.90, 0.70, 0.10), "zor": (0.85, 0.15, 0.15)}

DIFF = {
    "kolay": {"lane_w": 6.0, "debris_n": 130, "tikama_n": 2},
    "orta":  {"lane_w": 5.0, "debris_n": 170, "tikama_n": 3},
    "zor":   {"lane_w": 4.0, "debris_n": 210, "tikama_n": 3},
}

# ── Gerçekçi hızlar ───────────────────────────────────────────────────────────
IKA_SPEED   = 1.1     # m/s — gerçekçi diferansiyel rover seyir hızı (PDF: ≤10dk/HB)
IKA_Z       = arena.START_Z
PAD_SEC     = 4
# İHA faz hızları (m/s) — sabit kanat: stall üstü, arena ölçeğinde gerçekçi.
# (Şartname seyir 40-45 m/s HTAB'a İNTİKAL içindir; 50×50 arena üzerinde uygulanmaz.
#  Tarama 10 m/s → 50×50 serpantin ~20 s = şartname "20-30 s tarama" bandı.)
PHASE_SPEED = {"rampa": 6.0, "kalkis": 18.0, "tirmanis": 18.0,
               "tarama": 10.0, "donus": 10.0, "sokulma": 12.0, "parasut": 5.5}
SCAN_Z      = 30.0    # şartname: 30 m tarama irtifası


def make_zone(scenario, seed, road=None, harita_id=1):
    """Zon verisi — GERÇEKÇİ KIVRIMLI harita (arena.harita TEK KAYNAK).
    road: SADECE hata ayıklama (açık yolu elle zorla); normalde gizli seed kararı."""
    cx, cy = ZONE_POS[scenario]
    H = arena.harita(harita_id, scenario)
    if road not in (1, 2, 3):
        road = H["open"]
    wl = arena._downsample(H["paths"][road])          # İKA fallback rotası (~2 m)
    kb, hb = H["kb"], H["hb"]
    return {
        "cx": cx, "cy": cy, "scenario": scenario, "sfx": scenario,
        "harita": H, "harita_id": harita_id,
        "road": road, "lane_w": DIFF[scenario]["lane_w"],
        "color": ZONE_COLOR[scenario],
        "wp_local": wl, "wp_world": [(cx + x, cy + y) for (x, y) in wl],
        "start_world": (cx + kb[0], cy + kb[1]),
        "hb_world": (cx + hb[0], cy + hb[1]),
        "rng": random.Random(f"{seed}-{scenario}-{harita_id}"),
    }


TURN_STEP = math.radians(12)   # yay örnekleme adımı (~12° → akıcı dönüş)


def _arc(ax, ay, r, a0, a1, z0, z1, phase):
    """Dairesel dönüş yayı örnekle: merkez (ax,ay), a0→a1 rad (artış=CCW/sola,
    azalış=CW/sağa), irtifa z0→z1 lineer. Sabit kanat yerinde DÖNEMEZ — her yön
    değişimi bu yaylarla yapılır."""
    n = max(2, int(abs(a1 - a0) / TURN_STEP))
    return [(ax + r * math.cos(a0 + (a1 - a0) * (i / n)),
             ay + r * math.sin(a0 + (a1 - a0) * (i / n)),
             z0 + (z1 - z0) * (i / n), phase) for i in range(1, n + 1)]


def iha_flight(cx, cy):
    """Gerçekçi sabit-kanat İHA profili — (x, y, z, faz) yoğun örneklenmiş yol:
      mancınık fırlatma (doğuya) → düz tırmanış → SOLA tırmanışlı 180° raketrak dönüş
      → kuzey kenardan tarama girişi → 50×50 SERPANTİN (4 sütun, uçlarda YARIM DAİRE
      U-dönüşleri, arena kenarından hafif taşar — gerçek harita uçuşu gibi)
      → sağa çıkış dönüşüyle İHA-İB hattına → sokulma alçalması → PARAŞÜT açılır,
      süzülerek pede iner. Her nokta yol yönüne bakar (yaw), plugin roll/pitch ekler."""
    C = math.pi
    pts = [
        (cx - 26.0, cy, 0.5, "rampa"),            # mancınıkta (yer)
        (cx - 23.0, cy, 1.4, "kalkis"),           # fırlatma çıkışı (uçuş hızında)
        (cx - 6.0,  cy, 6.5, "kalkis"),           # düz tırmanış (doğuya, ~%15 gradyan)
        (cx + 20.0, cy, 14.0, "tirmanis"),
    ]
    # tırmanışlı 180° SOL raketrak dönüşü (R=12 — SIKI: görev süresi HTAB üzerinde
    # geçsin, saha dışı tur kısalsın; İHA-UB 300×300 sınırına zaten uzak)
    pts += _arc(cx + 20.0, cy + 12.0, 12.0, -C / 2, C / 2, 14.0, 22.0, "tirmanis")
    pts += [(cx - 10.0, cy + 27.0, 27.0, "tirmanis")]      # kuzey kenar boyunca batıya
    # çeyrek SOL dönüş → 1. sütuna güneye giriş (27→30 m)
    pts += _arc(cx - 10.0, cy + 19.0, 8.0, C / 2, C, 27.0, SCAN_Z, "tirmanis")

    cols = [-18.0, -6.0, 6.0, 18.0]
    ys = 20.0
    for i, lx in enumerate(cols):                  # SERPANTİN (30 m sabit)
        south = (i % 2 == 0)                       # çift sütun: kuzey→güney
        y_end = -ys if south else ys
        pts.append((cx + lx, cy + y_end, SCAN_Z, "tarama"))
        if i < len(cols) - 1:                      # uçta YARIM DAİRE U-dönüşü (R=6)
            mid = lx + 6.0
            if south:                              # güney uçta SOLA (CCW) dön
                pts += _arc(cx + mid, cy - ys, 6.0, C, 2 * C, SCAN_Z, SCAN_Z, "donus")
            else:                                  # kuzey uçta SAĞA (CW) dön
                pts += _arc(cx + mid, cy + ys, 6.0, C, 0.0, SCAN_Z, SCAN_Z, "donus")
    # tarama bitti (son sütun kuzey ucu) → SAĞ U-dönüş ile İHA-İB hattına (x=+32, güneye)
    pts += _arc(cx + 25.0, cy + ys, 7.0, C, 0.0, SCAN_Z, SCAN_Z, "donus")
    pts += [
        (cx + 32.0, cy + 13.0, 26.0, "sokulma"),  # güneye sokulma, alçalma
        (cx + 32.0, cy + 6.0,  21.0, "sokulma"),
        (cx + 32.0, cy + 4.5,  19.5, "parasut"),  # PARAŞÜT açılır (~20 m)
        (cx + 32.0, cy + 2.0,  12.0, "parasut"),  # süzülme (<7 m/s çöküş, şartname)
        (cx + 32.0, cy + 0.5,  4.5,  "parasut"),
        (cx + 32.0, cy,        0.35, "parasut"),  # İHA-İB pedine temas
    ]
    return pts


# ── Animasyon (kayıt, sadece odak zon) ────────────────────────────────────────

def _timed(pts, t0, speed, z=None, yaw=False):
    seg = [math.dist(pts[i][:2], pts[i+1][:2]) for i in range(len(pts)-1)]

    def Y(i):
        j = min(i, len(pts)-2)
        return math.atan2(pts[j+1][1]-pts[j][1], pts[j+1][0]-pts[j][0])

    def Z(p):
        return z if z is not None else (p[2] if len(p) > 2 else 0.0)

    out = [(t0, pts[0][0], pts[0][1], Z(pts[0]), Y(0) if yaw else 0.0)]
    t = t0
    for i in range(len(pts)-1):
        t += seg[i] / speed
        out.append((t, pts[i+1][0], pts[i+1][1], Z(pts[i+1]), Y(i+1) if yaw else 0.0))
    return out


def _timed_flight(fp, t0=0.0):
    """(x,y,z,faz) yolu → (t,x,y,z,yaw) waypoint'leri.
    - yaw: her noktada YOL YÖNÜ (atan2) — uçak gittiği yöne bakar, yan kaymaz.
    - hız: faz hedefleri komşu-ortalamayla yumuşatılır → ani hız sıçraması yok
      (mancınık çıkışı hariç: fırlatma doğası gereği anidir)."""
    v = [PHASE_SPEED.get(p[3], 14.0) for p in fp]
    for _ in range(3):                              # ivme yumuşatma (3 geçiş)
        v = [v[0]] + [(v[i-1] + v[i] + v[i+1]) / 3.0
                      for i in range(1, len(v) - 1)] + [v[-1]]
    out, t = [], t0
    for i, p in enumerate(fp):
        j = min(i, len(fp) - 2)
        yaw = math.atan2(fp[j+1][1] - fp[j][1], fp[j+1][0] - fp[j][0])
        if i > 0:
            t += math.dist(fp[i-1][:3], p[:3]) / max((v[i-1] + v[i]) / 2.0, 0.1)
        out.append((t, p[0], p[1], p[2], yaw))
    return out


def make_anim_plugin(zone):
    cx, cy = zone["cx"], zone["cy"]
    fp = iha_flight(cx, cy)
    iha = _timed_flight(fp)
    land_t = iha[-1][0]
    # Tarama bitişi (sim sn): son 'tarama'/'donus' fazlı nokta — kayıt betiği bu anda
    # scan_done işareti bırakır, host'taki İHA-haritalama (iha_haritala.py) tetiklenir.
    scan_end_t = max(iha[i][0] for i, p in enumerate(fp) if p[3] in ("tarama", "donus"))

    # Paraşüt: 'parasut' fazına dek gizli (yer altı), açılınca İHA'nın ÜSTÜNDE
    # belirip 0.6 s'de kanopi yüksekliğine çıkar (açılma), inişte İHA ile süzülür,
    # yere oturup KALIR (kaybolmaz).
    di = next(i for i, p in enumerate(fp) if p[3] == "parasut")
    t_dep = iha[di][0]
    para = [(0.0, fp[di][0], fp[di][1], -60, 0.0),
            (t_dep - 0.05, fp[di][0], fp[di][1], -60, 0.0),
            (t_dep + 0.05, fp[di][0], fp[di][1], fp[di][2] + 0.8, 0.0)]
    for i in range(di + 1, len(fp)):
        zc = 0.6 if i == len(fp) - 1 else fp[i][2] + 3.5   # iniş: yere oturur
        para.append((iha[i][0], fp[i][0], fp[i][1], zc, 0.0))
    para.append((land_t + 8.0, fp[-1][0], fp[-1][1], 0.6, 0.0))  # sonrası KALIR

    # İKA: İHA YERE TEMAS + 1.5s sonra başlar (şartname §2.2.5). Plugin FİZİK kuvvet
    # kontrolüyle (IKA_SPEED) sürer; wps yalnız x,y hedef + başlangıç zamanı içindir.
    ika_start = land_t + 1.5
    ika = _timed(zone["wp_world"], ika_start, IKA_SPEED, z=IKA_Z, yaw=True)
    ww = zone["wp_world"]
    path_len = sum(math.dist(ww[i], ww[i+1]) for i in range(len(ww)-1))
    ika_drive = path_len / IKA_SPEED
    # +45: İKA rota-fallback bekleme payı (plugin ROUTE_WAIT). Normal koşuda görev
    # erken biter → kayıt betiği plugin'in "durum=BITTI" sinyaliyle erken keser.
    duration = max(land_t + 8.0, ika_start + ika_drive + 10) + 45

    def block(name, wps):
        lines = "\n".join(
            f"        <waypoint>{tt:.2f} {x:.3f} {y:.3f} {z:.3f} {yw:.4f}</waypoint>"
            for (tt, x, y, z, yw) in wps)
        return f'      <model name="{name}">\n{lines}\n      </model>'

    plugin = ('    <plugin name="navitas_anim" filename="libnavitas_anim.so">\n'
              + block("iha", iha) + "\n"
              + block("parachute", para) + "\n"
              + block(f"ika_{zone['sfx']}", ika) + "\n    </plugin>")
    return plugin, duration, scan_end_t, land_t


# ── SDF yardımcıları ──────────────────────────────────────────────────────────

def _box(name, px, py, pz, sx, sy, sz, r, g, b, yaw=0.0, static=True):
    st = "<static>true</static>" if static else ""
    return f"""
    <model name="{name}">
      {st}
      <pose>{px:.3f} {py:.3f} {pz:.3f} 0 0 {yaw:.3f}</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material><ambient>{r:.2f} {g:.2f} {b:.2f} 1</ambient><diffuse>{r:.2f} {g:.2f} {b:.2f} 1</diffuse></material>
        </visual>
      </link>
    </model>"""


def _flat(name, px, py, sx, sy, r, g, b, yaw=0.0):
    return _box(name, px, py, 0.01, sx, sy, 0.02, r, g, b, yaw)


def _cyl(name, px, py, pz, radius, length, r, g, b):
    return f"""
    <model name="{name}">
      <static>true</static><pose>{px:.3f} {py:.3f} {pz:.3f} 0 0 0</pose>
      <link name="link"><visual name="vis">
        <geometry><cylinder><radius>{radius}</radius><length>{length}</length></cylinder></geometry>
        <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
      </visual></link>
    </model>"""


def _include(name, model_name, px, py, pz, yaw=0.0):
    return f"""
    <include><uri>model://{model_name}</uri><name>{name}</name>
      <pose>{px:.3f} {py:.3f} {pz:.3f} 0 0 {yaw:.3f}</pose></include>"""


def _ground_plane():
    return """
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="collision"><geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        <surface><friction><ode><mu>0.8</mu><mu2>0.8</mu2></ode></friction></surface></collision>
      <visual name="visual"><cast_shadows>false</cast_shadows>
        <geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        <material><script><uri>file://media/materials/scripts/gazebo.material</uri><name>Gazebo/Grey</name></script></material>
      </visual></link></model>"""


def make_ub():
    WH = 1.5; c = (0.45, 0.45, 0.5); p = []
    p.append(_box("ub_N", 0,  UB_HALF, WH/2, UB, 0.6, WH, *c))
    p.append(_box("ub_S", 0, -UB_HALF, WH/2, UB, 0.6, WH, *c))
    p.append(_box("ub_W", -UB_HALF, 0, WH/2, 0.6, UB, WH, *c))
    p.append(_box("ub_E",  UB_HALF, 0, WH/2, 0.6, UB, WH, *c))
    return "\n".join(p)


def make_zone_ground(z):
    cx, cy, s = z["cx"], z["cy"], z["sfx"]
    cr, cg, cb = z["color"]
    # Kahve moloz zemini (içi)
    p = [_flat(f"gd_{s}", cx, cy, HTAB, HTAB, 0.34, 0.30, 0.25)]
    # Seviye rengi SINIR ÇERÇEVESİ (4 şerit — ayırt edici, içi kahve kalır)
    t = 1.6
    p.append(_box(f"brd_{s}_N", cx, cy + HTAB_HALF + t/2, 0.04, HTAB + 2*t, t, 0.08, cr, cg, cb))
    p.append(_box(f"brd_{s}_S", cx, cy - HTAB_HALF - t/2, 0.04, HTAB + 2*t, t, 0.08, cr, cg, cb))
    p.append(_box(f"brd_{s}_W", cx - HTAB_HALF - t/2, cy, 0.04, t, HTAB, 0.08, cr, cg, cb))
    p.append(_box(f"brd_{s}_E", cx + HTAB_HALF + t/2, cy, 0.04, t, HTAB, 0.08, cr, cg, cb))
    return "\n".join(p)


# Zemin katman yükseklikleri (z-fight/örtme önlemek için katmanlı):
#   zon zemini 0.01 < yol 0.04 < başlangıç halkası/HB pad 0.07 < H harfleri 0.10
Z_ROAD = 0.04
Z_PAD  = 0.07
Z_H    = 0.10


def make_road_surfaces(z):
    """3 KIVRIMLI yolun zemin şeridi — spline, kısa dikdörtgen segmentlerle izlenir
    (her segment yol yönüne DÖNÜK). HEPSİ AYNI asfalt rengi: hangi yolun açık olduğu
    renkten DEĞİL, sadece moloz tıkamasından anlaşılır (şartname: açık yol GİZLİ).
    Zon zemininin (0.01) ÜSTÜNDE (Z_ROAD) → z-fighting yok."""
    cx, cy, s = z["cx"], z["cy"], z["sfx"]
    col = (0.20, 0.20, 0.22)
    p = []
    for road, path in z["harita"]["paths"].items():
        seg = arena._downsample(path, step=2.4)
        for i in range(len(seg) - 1):
            (x0, y0), (x1, y1) = seg[i], seg[i + 1]
            L = math.dist(seg[i], seg[i + 1]) + 0.9          # bindirme payı (boşluk kalmasın)
            yaw = math.atan2(y1 - y0, x1 - x0)
            p.append(_box(f"road_{s}_{road}_{i}", cx + (x0 + x1) / 2, cy + (y0 + y1) / 2,
                          Z_ROAD, L, z["lane_w"], 0.02, *col, yaw=yaw))
    return "\n".join(p)


def _rubble_color(rng):
    if rng.random() < 0.35:
        s = rng.uniform(0.45, 0.55); return (s, s*0.7, s*0.5)
    g = rng.uniform(0.4, 0.62); return (g, g, g*0.98)


def _rubble(name, lx, ly, rng, big=False):
    k = rng.random()
    if k < 0.30:
        sx, sy, sz = rng.uniform(1.8, 3.6), rng.uniform(1.0, 2.2), rng.uniform(0.2, 0.4)
    elif k < 0.55:
        sx = sy = rng.uniform(0.9, 1.6); sz = rng.uniform(0.8, 1.6)
    elif k < 0.75:
        sx, sy, sz = rng.uniform(1.5, 3.0), rng.uniform(0.15, 0.3), rng.uniform(0.15, 0.4)
    else:
        sx = sy = rng.uniform(0.4, 0.8); sz = rng.uniform(0.3, 0.7)
    if big:
        sx *= 1.4; sy *= 1.4; sz = max(sz, 1.0)
    r, g, b = _rubble_color(rng)
    return _box(name, lx, ly, sz/2.0, sx, sy, sz, r, g, b, yaw=rng.uniform(0, 3.14))


def make_zone_debris(z, layout="field"):
    """GERÇEKÇİ enkaz sahası (kıvrımlı haritaya göre):
      · 2 KAPALI yol: rota ÜZERİNDE tikama_n noktada moloz TIKAMASI (yolu kesen küme)
        + yol girişine kırmızı-beyaz bariyer (yol yönüne dönük).
      · Saha geneli DAĞINIK moloz — 3 koridorun hiçbirine girmez (clearance),
        KB/HB/İHA işaretleri temiz kalır.
      · Açık yol kenarlarına chicane molozları (viraj hissi güçlenir).
    layout=field (vars.) tam yoğunluk; clean = dağınık moloz 1/3 (net sunum)."""
    rng = z["rng"]; cx, cy, s = z["cx"], z["cy"], z["sfx"]
    H = z["harita"]; lane_w = z["lane_w"]; clear = lane_w / 2.0 + 1.2
    kb, hb = H["kb"], H["hb"]
    p = []

    # ── 2 KAPALI yol: giriş bariyeri + rota üzerinde tıkama kümeleri ──
    tikama_n = DIFF[z["scenario"]]["tikama_n"]
    for road in (1, 2, 3):
        if road == z["road"]:
            continue
        path = H["paths"][road]
        bi = int(len(path) * 0.12)                       # giriş bariyeri (~%12 noktası)
        (bx, by), (nx2, ny2) = path[bi], path[bi + 1]
        byaw = math.atan2(ny2 - by, nx2 - bx) + math.pi / 2   # yola DİK dursun
        p.append(_box(f"bar_{s}_{road}",  cx + bx, cy + by, 0.5, lane_w + 1.0, 0.5, 1.0,
                      0.85, 0.1, 0.1, yaw=byaw))
        p.append(_box(f"bar_{s}_{road}b", cx + bx, cy + by, 1.0, lane_w + 1.0, 0.4, 0.3,
                      0.95, 0.95, 0.95, yaw=byaw))
        for k in range(tikama_n):                        # yolu KESEN moloz kümeleri
            t = 0.30 + 0.50 * (k / max(1, tikama_n - 1)) + rng.uniform(-0.05, 0.05)
            ti = max(1, min(len(path) - 2, int(len(path) * t)))
            (px, py), (qx, qy) = path[ti], path[ti + 1]
            tyaw = math.atan2(qy - py, qx - px)
            # kümeyi yol EKSENİNE dik ser: tüm genişliği kapat + 2 sıra derinlik
            for j in range(max(6, int(lane_w * 1.6))):
                u = rng.uniform(-lane_w / 2 - 0.5, lane_w / 2 + 0.5)   # yola dik eksen
                v = rng.uniform(-1.8, 1.8)                              # yol boyu eksen
                ox = px + v * math.cos(tyaw) - u * math.sin(tyaw)
                oy = py + v * math.sin(tyaw) + u * math.cos(tyaw)
                p.append(_rubble(f"blk_{s}_{road}_{k}_{j}", cx + ox, cy + oy, rng, big=True))

    # ── Saha geneli dağınık moloz (koridorlara ve işaret alanlarına GİRMEZ) ──
    n = DIFF[z["scenario"]]["debris_n"]
    if layout == "clean":
        n //= 3
    placed = tries = 0
    while placed < n and tries < n * 15:
        tries += 1
        lx = rng.uniform(-HTAB_HALF + 1, HTAB_HALF - 1)
        ly = rng.uniform(-HTAB_HALF + 1, HTAB_HALF - 1)
        if dist_to_all_paths(lx, ly, H) < clear:
            continue                                     # koridor içine moloz koyma
        if math.hypot(lx - kb[0], ly - kb[1]) < 3.5:     # KB temiz
            continue
        if math.hypot(lx - hb[0], ly - hb[1]) < 4.0:     # HB temiz
            continue
        p.append(_rubble(f"deb_{s}_{placed}", cx + lx, cy + ly, rng))
        placed += 1

    # ── Chicane: açık yolun kenarına, sağlı sollu (kıvrımı vurgular) ──
    op = H["paths"][z["road"]]
    for wi, t in enumerate((0.25, 0.40, 0.55, 0.70, 0.85)):
        ti = min(len(op) - 2, int(len(op) * t))
        (px, py), (qx, qy) = op[ti], op[ti + 1]
        tyaw = math.atan2(qy - py, qx - px)
        side = 1.0 if wi % 2 == 0 else -1.0
        off = side * (clear + rng.uniform(0.4, 1.1))
        ox = px - off * math.sin(tyaw)
        oy = py + off * math.cos(tyaw)
        p.append(_rubble(f"chic_{s}_{wi}", cx + ox, cy + oy, rng, big=True))
    return "\n".join(p)


def make_zone_markers(z):
    """Başlangıç halkası + HB pad + H — yol zemininin (Z_ROAD) ÜSTÜNDE (görünür kalsın)."""
    s = z["sfx"]; sx, sy = z["start_world"]; hx, hy = z["hb_world"]
    cr, cg, cb = z["color"]
    p = [_cyl(f"kb_{s}", sx, sy, Z_PAD, 1.8, 0.06, cr, cg, cb),     # başlangıç = seviye rengi
         _box(f"hbpad_{s}", hx, hy, Z_PAD, 4.0, 4.0, 0.04, 0.1, 0.2, 0.6),
         _box(f"H_{s}_l", hx-1.0, hy, Z_H, 0.4, 2.4, 0.1, 1, 1, 1),
         _box(f"H_{s}_r", hx+1.0, hy, Z_H, 0.4, 2.4, 0.1, 1, 1, 1),
         _box(f"H_{s}_b", hx, hy, Z_H, 2.0, 0.4, 0.1, 1, 1, 1)]
    return "\n".join(p)


def make_zone_ika(z):
    sx, sy = z["start_world"]
    # Burnu rotanın İLK segmentine dönük başlat (dümdüz kuzeye bakmasın —
    # KB→HB hizasız, ilk hareket zaten kıvrıma girer)
    (x0, y0), (x1, y1) = z["wp_local"][0], z["wp_local"][1]
    yaw = math.atan2(y1 - y0, x1 - x0)
    return _include(f"ika_{z['sfx']}", "ika", sx, sy, arena.START_Z, yaw=yaw)


def make_iha_vehicle(focus_zone):
    fx, fy, fz, _ = iha_flight(focus_zone["cx"], focus_zone["cy"])[0]
    return _include("iha", "iha", fx, fy, fz + 0.2)


def make_iha_landing(focus_zone):
    # İHA-İB: HTAB'ın doğusunda mavi iniş bölgesi (paraşütle iniş, kare içinde)
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return _flat("landing", cx + 32, cy, 8.0, 8.0, 0.1, 0.25, 0.7)


def make_catapult(focus_zone):
    # Mancınık: HTAB'ın batısında, İHA fırlatma noktasında (kare içinde, sınır içi)
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return _include("catapult_main", "catapult", cx - 26, cy, 0.08)


def make_parachute():
    """İHA paraşütü — KUBBE kanopi (istiflenmiş silindir → kubbe görünümü) + ipler + harness.
    anim plugin 'parachute' modelini alçalmada İHA üstünde açar, iniş sonrası yere oturur."""
    dome = ""
    # istiflenmiş silindirlerle kubbe (turuncu/beyaz dilimler)
    layers = [(2.10, 0.00, 0.95, 0.45, 0.05), (1.70, 0.22, 1.0, 0.55, 0.08),
              (1.25, 0.42, 0.95, 0.95, 0.95), (0.75, 0.58, 1.0, 0.55, 0.08),
              (0.32, 0.70, 0.95, 0.45, 0.05)]
    for i, (rad, zz, r, g, b) in enumerate(layers):
        dome += f"""
        <visual name="dome{i}"><pose>0 0 {zz:.2f} 0 0 0</pose>
          <geometry><cylinder><radius>{rad:.2f}</radius><length>0.16</length></cylinder></geometry>
          <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
        </visual>"""
    # askı ipleri (4 eğik ince silindir) — kanopi kenarından harness'a
    lines = ""
    for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
        lines += f"""
        <visual name="line{i}"><pose>{sx*0.9:.2f} {sy*0.9:.2f} -1.5 {sy*0.5:.3f} {sx*0.5:.3f} 0</pose>
          <geometry><cylinder><radius>0.02</radius><length>3.0</length></cylinder></geometry>
          <material><ambient>0.1 0.1 0.1 1</ambient><diffuse>0.15 0.15 0.15 1</diffuse></material>
        </visual>"""
    harness = """
        <visual name="harness"><pose>0 0 -3.0 0 0 0</pose>
          <geometry><box><size>0.3 0.3 0.2</size></box></geometry>
          <material><ambient>0.2 0.2 0.2 1</ambient><diffuse>0.25 0.25 0.25 1</diffuse></material>
        </visual>"""
    return f"""
    <model name="parachute"><static>true</static>
      <pose>0 0 -60 0 0 0</pose>
      <link name="link">{dome}{lines}{harness}
      </link>
    </model>"""


def make_gui_camera(focus_zone, record=False):
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    if record:
        default = f"{cx} {cy} 58 0 1.5708 1.5708"      # 90° dik, odak zonu doldur
    else:
        default = f"{cx-34} {cy-34} 30 0 0.55 0.785"
    pose = os.environ.get("GAZEBO_GUI_CAM") or default
    fs = "1" if record else "0"
    return f'\n    <gui fullscreen="{fs}">\n      <camera name="user_camera"><pose>{pose}</pose></camera>\n    </gui>'


def make_rec_camera(z):
    """Kayıt için TOP-DOWN kamera SENSÖRÜ (deterministik — gzclient GUI kamerası racy).
    Kareleri /tmp/frames'e kaydeder; record_in_container ffmpeg ile videoya çevirir."""
    cx, cy = z["cx"], z["cy"]
    return f"""
    <model name="rec_cam"><static>true</static>
      <pose>{cx:.3f} {cy:.3f} 72 0 1.5708 1.5708</pose>
      <link name="link">
        <sensor name="cam" type="camera">
          <camera>
            <horizontal_fov>1.25</horizontal_fov>
            <image><width>1280</width><height>720</height><format>R8G8B8</format></image>
            <clip><near>0.1</near><far>200</far></clip>
            <save enabled="true"><path>/tmp/frames</path></save>
          </camera>
          <always_on>1</always_on>
          <update_rate>30</update_rate>
        </sensor>
      </link>
    </model>"""


def make_lights(record=False):
    sh = "false" if record else "true"
    return f"""
    <light name="sun" type="directional"><cast_shadows>{sh}</cast_shadows>
      <pose>0 0 120 0 -0 0</pose><diffuse>0.9 0.9 0.85 1</diffuse><specular>0.1 0.1 0.1 1</specular>
      <attenuation><range>1200</range><constant>0.9</constant><linear>0.01</linear><quadratic>0.001</quadratic></attenuation>
      <direction>-0.4 0.2 -0.9</direction></light>"""


# ── Tam dünya (odak zon: zemin + 3 yol + moloz + animasyon) ───────────────────

def build_world(seed, focus, record=False, road=None, layout="field", harita_id=1):
    # road = SADECE hata ayıklama; normalde açık yol gizli (arena.harita seed'i).
    # Her klip SADECE odak zonu içerir (hafif dünya → 90° dik kamera güvenilir).
    fz = make_zone(focus, seed, road, harita_id)

    parts = [make_lights(record), _ground_plane(), make_ub(),
             make_iha_landing(fz), make_catapult(fz)]
    parts += [make_zone_ground(fz), make_road_surfaces(fz),
              make_zone_debris(fz, layout), make_zone_markers(fz)]
    parts += [make_iha_vehicle(fz), make_zone_ika(fz)]
    if record:
        parts.append(make_parachute())             # İHA paraşütü (anim ile açılır)
        parts.append(make_rec_camera(fz))          # top-down kayıt kamerası (sensör)
        plugin, _, _, _ = make_anim_plugin(fz)
        parts.append(plugin)

    body = "\n".join(parts)
    gui = make_gui_camera(fz, record)
    return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="navitas_arena">
{gui}
    <physics type="ode"><max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor><real_time_update_rate>1000</real_time_update_rate>
      <gravity>0 0 -9.8</gravity></physics>
    <scene><ambient>0.5 0.5 0.5 1</ambient><background>0.75 0.8 0.85 1</background>
      <shadows>{"false" if record else "true"}</shadows></scene>
    <!-- Seed: {seed} | Odak: {focus} | layout: {layout} | açık yol: {arena.ROAD_LABEL[fz['road']]} -->
{body}
  </world>
</sdf>
""", fz


def main():
    ap = argparse.ArgumentParser(description="Navitas 3-zon sıralı dünya üreticisi")
    ap.add_argument("--focus", choices=ZONE_ORDER, default="kolay",
                    help="bu kayıtta odaklanılacak seviye")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", default="worlds/navitas_arena.world")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--layout", choices=["clean", "field"], default="field",
                    help="field=gerçekçi moloz sahası (vars.), clean=seyrek/net sunum")
    ap.add_argument("--map", type=int, choices=range(1, arena.HARITA_N + 1), default=1,
                    help=f"gerçekçi harita no (1-{arena.HARITA_N}) — her biri farklı "
                         "kıvrım/KB/HB düzeni")
    ap.add_argument("--road", type=int, choices=[1, 2, 3], default=None,
                    help="SADECE HATA AYIKLAMA: açık yolu elle seç. Normal akışta dünya "
                         "her zaman ground-truth ile kurulur; model tespiti dünyaya GERİ "
                         "BESLENMEZ (tersine nedensellik yasak).")
    args = ap.parse_args()

    world, fz = build_world(args.seed, args.focus, record=args.record,
                            road=args.road, layout=args.layout, harita_id=args.map)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(world, encoding="utf-8")
    print(f"[world_gen] Odak={args.focus} @({fz['cx']},{fz['cy']}) harita={args.map} "
          f"layout={args.layout} açık yol={arena.ROAD_LABEL[fz['road']]} | yazıldı: {out}")
    print(f"[world_gen] OPEN_ROAD={arena.ROAD_LABEL[fz['road']]}")   # record_in_container parse eder
    # İHA-haritalama (iha_haritala.py) için makine-okur meta:
    print(f"[world_gen] HTAB_CENTER={fz['cx']},{fz['cy']}")
    print(f"[world_gen] MAP={args.map}")
    print(f"[world_gen] KB_XY={fz['start_world'][0]:.2f},{fz['start_world'][1]:.2f}")
    print(f"[world_gen] HB_XY={fz['hb_world'][0]:.2f},{fz['hb_world'][1]:.2f}")
    if args.record:
        _, dur, scan_end, land_t = make_anim_plugin(fz)
        print(f"[world_gen] SCAN_END_T={scan_end:.0f}")   # tarama bitiş sim sn (marker anı)
        print(f"[world_gen] LAND_T={land_t:.0f}")         # İHA iniş sim sn
        print(f"[world_gen] RECORD_SECONDS={dur + PAD_SEC:.0f}")


if __name__ == "__main__":
    main()
