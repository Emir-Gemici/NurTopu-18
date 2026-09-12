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
import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import arena
from arena import (UB, UB_HALF, HTAB, HTAB_HALF, dist_to_path, dist_to_all_paths)
from scenario_profiles import load_profile

ZONE_ORDER = ["kolay", "orta", "zor"]
ZONE_POS = arena.ZONE_POS
# Seviye ayırt edici renk (zon sınır şeridi + İKA başlangıç halkası)
ZONE_COLOR = {"kolay": (0.10, 0.75, 0.20), "orta": (0.90, 0.70, 0.10), "zor": (0.85, 0.15, 0.15)}
ASPHALT_MATERIAL_URI = "file://media/materials/scripts/navitas_asphalt.material"
ASPHALT_MATERIAL_NAME = "Navitas/RealArenaAsphalt"
ASPHALT_RGB = (0.51, 0.56, 0.62)
ASPHALT_SPECULAR = 0.04

# ── ARAZI MODLARI (--terrain; kullanıcı 2026-09-02: SEÇİLEBİLİR olsun) ─────────
#   plain    : mevcut davranış — düz asfalt zemin, ızgarasız (VARSAYILAN, hiçbir şey bozulmaz).
#   textured : gerçek arena referansına (şartname s.9) benzer AÇIK KAHVE toprak zemin +
#              yüzey IZGARASI. Çarpışma DÜZ kalır → İKA nav & 15/15 kapısı ETKİLENMEZ.
#              Algı boşluğu içindir ([[gazebo-algi-boslugu-olculdu]]); P2'de ölçümle iyileştirilir.
#   relief   : heightmap KABARTMA (engebeli arazi). Çarpışmayı DEĞİŞTİRİR → yarışma öncesi
#              15/15 kapısı + İKA nav YENİDEN doğrulanmalı. Yalnız açıkça seçilince kurulur.
TERRAIN_MODES = ("plain", "textured", "relief")
TERRAIN_DEFAULT = "plain"
# Şartname s.9 referansı: açık kahve toprak/kum + koyu ölçüm ızgarası.
DIRT_RGB = (0.62, 0.52, 0.37)          # açık kahve toprak (traversable ipucu)
GRID_RGB = (0.30, 0.24, 0.17)          # koyu kahve ızgara çizgisi
GRID_SPACING_M = 5.0                    # ölçüm ızgarası hücre kenarı (referansa yakın)
GRID_LINE_W = 0.10                      # ızgara çizgi kalınlığı (m)
GRID_Z = 0.015                          # zon zemini (0.01) üstü, yol (0.04) altı → z-fight yok
# relief heightmap (media'ya bir kez üretilir; yoksa relief plain'e düşer + uyarı basar)
RELIEF_HEIGHTMAP_URI = "file://media/materials/textures/terrain_relief.png"
RELIEF_HEIGHTMAP_PATH = "media/materials/textures/terrain_relief.png"
RELIEF_SIZE_M = 400.0                   # yatay kaplama (ground_plane ile aynı ayak izi)
RELIEF_MAX_Z = 0.35                     # tepe-vadi toplam yükseklik (m) — rover tırmanabilir

# ── GERÇEK MOLOZ MESH KÜTÜPHANESİ (prompt §4-8: kutu DEĞİL, gerçek enkaz siluetleri) ──
RUBBLE_MESH_DIR = "media/meshes/rubble"
_RUBBLE_MANIFEST = (Path(__file__).resolve().parent.parent
                    / RUBBLE_MESH_DIR / "rubble_manifest.json")
_RUBBLE_LIB = None                       # {tip: [(ad, bbox), ...]}  (tembel yüklenir)

# Materyal paletleri (prompt §14: desatüre, aşırı doygun DEĞİL; turuncu-yeşil plaka YOK)
_CONCRETE = [(0.60, 0.60, 0.58), (0.68, 0.66, 0.62), (0.50, 0.50, 0.49),
             (0.72, 0.70, 0.66), (0.56, 0.55, 0.53), (0.45, 0.45, 0.44)]
_BRICK    = [(0.52, 0.34, 0.27), (0.46, 0.30, 0.24), (0.58, 0.40, 0.32), (0.49, 0.28, 0.21)]
_PLASTER  = [(0.80, 0.78, 0.72), (0.74, 0.71, 0.65), (0.83, 0.80, 0.74)]
_METAL    = [(0.34, 0.34, 0.36), (0.44, 0.35, 0.29), (0.40, 0.40, 0.42)]
_WOOD     = [(0.36, 0.27, 0.16), (0.30, 0.22, 0.14), (0.42, 0.32, 0.20)]


def _rubble_lib():
    global _RUBBLE_LIB
    if _RUBBLE_LIB is None:
        _RUBBLE_LIB = {}
        try:
            data = json.loads(_RUBBLE_MANIFEST.read_text())
            for m in data["meshes"]:
                _RUBBLE_LIB.setdefault(m["type"], []).append((m["name"], m["bbox"]))
        except (OSError, ValueError, KeyError):
            _RUBBLE_LIB = {}       # yoksa realism kutuya düşer (uyarı make_zone_debris'te)
    return _RUBBLE_LIB


def _rubble_mat(typ, rng):
    """Enkaz tipine göre desatüre beton/tuğla/sıva/ahşap/metal rengi + kirlilik jitteri."""
    if typ in ("slab", "column", "pile"):
        pal = _CONCRETE if rng.random() < 0.82 else _PLASTER
    elif typ == "block":
        pal = rng.choice([_CONCRETE, _CONCRETE, _PLASTER, _BRICK])
    elif typ == "wall":
        pal = rng.choice([_PLASTER, _PLASTER, _BRICK, _CONCRETE])
    elif typ == "beam":
        pal = rng.choice([_WOOD, _WOOD, _METAL])       # ahşap kiriş / metal profil
    elif typ == "crumble":
        pal = rng.choice([_CONCRETE, _CONCRETE, _BRICK])
    else:                                              # brick
        pal = _BRICK if rng.random() < 0.7 else _CONCRETE
    r, g, b = rng.choice(pal)
    j = rng.uniform(-0.05, 0.05)
    return tuple(max(0.05, min(0.92, c + j + rng.uniform(-0.02, 0.02))) for c in (r, g, b))
KB_OUTER_M = 1.0
KB_FRAME_M = 0.12
KB_HEIGHT_M = 0.04
PARACHUTE_GORE_COUNT = 16
PARACHUTE_LINE_RADIUS_M = 0.005
PARACHUTE_HIDDEN_Z = -60.0
PARACHUTE_PACKED_TIME_S = 0.25
PARACHUTE_INFLATION_TIME_S = 0.95
PARACHUTE_SWAY_PERIOD_S = 2.8
PARACHUTE_IHA_SWAY_M = 0.38
PARACHUTE_CANOPY_SWAY_M = 0.09
PARACHUTE_MESH_URIS = {
    "packed": "file://media/meshes/parachute_packed.obj",
    "partial": "file://media/meshes/parachute_partial.obj",
    "full": "file://media/meshes/parachute_full.obj",
}

# Zorluk = SADECE çerçeve rengi değil, GERÇEK yoğunluk + rota karmaşıklığı farkı:
#   lane_w   : açık koridor genişliği (kolay geniş → zor dar)
#   debris_n : çökmüş yapı kümesi (pile omurgalı) sayısı — yoğunluk
#   micro_n  : küme-arası mikro kırıntı (crumble) yamaları — 'gerçek enkaz sahası' dokusu
#   tikama_n : kapalı rotada tıkama noktası sayısı
#   richness : küme başına parça zenginliği çarpanı (orta/küçük debris miktarı)
#   chicane  : açık yol kenarı viraj molozu sayısı
DIFF = {
    "kolay": {"lane_w": 6.0, "debris_n": 210, "micro_n": 220, "tikama_n": 2,
              "richness": 0.85, "chicane": 4},
    "orta":  {"lane_w": 5.0, "debris_n": 300, "micro_n": 360, "tikama_n": 3,
              "richness": 1.00, "chicane": 6},
    "zor":   {"lane_w": 4.2, "debris_n": 400, "micro_n": 520, "tikama_n": 4,
              "richness": 1.20, "chicane": 8},
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


def make_zone(scenario, seed, road=None, harita_id=1, profile=None,
              terrain=TERRAIN_DEFAULT):
    """Zon verisi — GERÇEKÇİ KIVRIMLI harita (arena.harita TEK KAYNAK).
    road: SADECE hata ayıklama (açık yolu elle zorla); normalde gizli seed kararı."""
    cx, cy = ZONE_POS[scenario]
    H = arena.harita(harita_id, scenario)
    if road not in (1, 2, 3):
        road = H["open"]
    wl = arena._downsample(H["paths"][road])          # İKA fallback rotası (~2 m)
    kb, hb = H["kb"], H["hb"]
    terrain_cfg = (profile or {}).get("terrain", {})   # profil moloz/şerit ayarları
    environment = (profile or {}).get("environment", {})
    return {
        "cx": cx, "cy": cy, "scenario": scenario, "sfx": scenario,
        "harita": H, "harita_id": harita_id,
        "road": road, "terrain": terrain,                 # arazi MODU (plain/textured/relief)
        "lane_w": DIFF[scenario]["lane_w"]
                  * float(terrain_cfg.get("lane_width_multiplier", 1.0)),
        "rubble_height_multiplier": float(terrain_cfg.get("rubble_height_multiplier", 1.0)),
        "chicane_count": int(terrain_cfg.get("chicane_count", DIFF[scenario]["chicane"])),
        "richness": DIFF[scenario]["richness"],   # zorluk zenginlik ölçeği (moloz)
        "ground_color": environment.get("ground_color", [0.34, 0.30, 0.25]),
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


def iha_flight(cx, cy, profile=None):
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
    scan_z = float((profile or {}).get("flight", {}).get("scan_altitude_m", SCAN_Z))
    pts += _arc(cx - 10.0, cy + 19.0, 8.0, C / 2, C, 27.0, scan_z, "tirmanis")

    cols = [-18.0, -6.0, 6.0, 18.0]
    ys = 20.0
    for i, lx in enumerate(cols):                  # SERPANTİN (30 m sabit)
        south = (i % 2 == 0)                       # çift sütun: kuzey→güney
        y_end = -ys if south else ys
        pts.append((cx + lx, cy + y_end, scan_z, "tarama"))
        if i < len(cols) - 1:                      # uçta YARIM DAİRE U-dönüşü (R=6)
            mid = lx + 6.0
            if south:                              # güney uçta SOLA (CCW) dön
                pts += _arc(cx + mid, cy - ys, 6.0, C, 2 * C, scan_z, scan_z, "donus")
            else:                                  # kuzey uçta SAĞA (CW) dön
                pts += _arc(cx + mid, cy + ys, 6.0, C, 0.0, scan_z, scan_z, "donus")
    # tarama bitti (son sütun kuzey ucu) → SAĞ U-dönüş ile İHA-İB hattına (x=+32, güneye)
    pts += _arc(cx + 25.0, cy + ys, 7.0, C, 0.0, scan_z, scan_z, "donus")
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


def _sample_timed(wps, t):
    """Zamanlı waypoint dizisini Python tarafında doğrusal örnekle."""
    if t <= wps[0][0]:
        return wps[0][1:]
    if t >= wps[-1][0]:
        return wps[-1][1:]
    for a, b in zip(wps, wps[1:]):
        if a[0] <= t <= b[0]:
            f = (t - a[0]) / max(b[0] - a[0], 1e-9)
            dyaw = (b[4] - a[4] + math.pi) % (2.0 * math.pi) - math.pi
            return (
                a[1] + (b[1] - a[1]) * f,
                a[2] + (b[2] - a[2]) * f,
                a[3] + (b[3] - a[3]) * f,
                a[4] + dyaw * f,
            )
    return wps[-1][1:]


def _sway_offset(t, deploy_t, land_t, amplitude):
    """Aynı fazlı sarkaç salınımı; açılışta büyür, inişte sıfıra sönümlenir."""
    if t <= deploy_t or land_t <= deploy_t:
        return 0.0
    progress = min(1.0, max(0.0, (t - deploy_t) / (land_t - deploy_t)))
    inflation_ramp = min(1.0, (t - deploy_t) / 0.55)
    # İlk salınım tam genliğe yaklaşır; son üçte hızla sönerek temasta sıfır olur.
    damping = 1.0 - progress ** 3
    phase = 2.0 * math.pi * (t - deploy_t) / PARACHUTE_SWAY_PERIOD_S
    return amplitude * inflation_ramp * damping * math.sin(phase)


def _sway_trajectory(base_wps, deploy_t, land_t, amplitude, step=0.20):
    """İrtifa ve ana zamanları koruyup paraşüt fazına yanal örnekler ekle."""
    times = {wp[0] for wp in base_wps}
    t = deploy_t + step
    while t < land_t:
        times.add(t)
        t += step
    out = []
    for tt in sorted(times):
        x, y, z, yaw = _sample_timed(base_wps, tt)
        offset = _sway_offset(tt, deploy_t, land_t, amplitude)
        x -= math.sin(yaw) * offset
        y += math.cos(yaw) * offset
        out.append((tt, x, y, z, yaw))
    return out


def make_anim_plugin(zone, profile=None):
    cx, cy = zone["cx"], zone["cy"]
    fp = iha_flight(cx, cy, profile)
    iha_base = _timed_flight(fp)
    land_t = iha_base[-1][0]
    # Tarama bitişi (sim sn): son 'tarama'/'donus' fazlı nokta — kayıt betiği bu anda
    # scan_done işareti bırakır, host'taki İHA-haritalama (iha_haritala.py) tetiklenir.
    scan_end_t = max(iha_base[i][0] for i, p in enumerate(fp)
                     if p[3] in ("tarama", "donus"))

    # Paraşüt: paket → kısmi → tam kanopi, toplam 0,95 s şişme. Aynı fazlı küçük
    # kanopi salınımı ve daha büyük İHA sarkaç hareketi inişe doğru sönümlenir.
    # Ana uçuş waypoint zamanları ve z değerleri değişmez; yalnız ara XY örnekleri eklenir.
    di = next(i for i, p in enumerate(fp) if p[3] == "parasut")
    t_dep = iha_base[di][0]
    iha = _sway_trajectory(
        iha_base, t_dep, land_t, PARACHUTE_IHA_SWAY_M
    )
    t_partial = t_dep + PARACHUTE_PACKED_TIME_S
    t_full = t_dep + PARACHUTE_INFLATION_TIME_S
    t_collapse = land_t + 0.35
    x_dep, y_dep, z_dep, yaw_dep = _sample_timed(iha_base, t_dep)

    def stage_pose(tt, z_offset, amplitude):
        x, y, z, yaw = _sample_timed(iha_base, min(tt, land_t))
        sway = _sway_offset(min(tt, land_t), t_dep, land_t, amplitude)
        return (tt, x - math.sin(yaw) * sway, y + math.cos(yaw) * sway,
                z + z_offset, yaw)

    hidden = (x_dep, y_dep, PARACHUTE_HIDDEN_Z, yaw_dep)
    packed = [
        (0.0, *hidden), (t_dep, *hidden),
        stage_pose(t_dep, 0.48, 0.03),
        stage_pose(t_partial, 0.48, 0.03),
    ]
    packed += [(t_partial, packed[-1][1], packed[-1][2], PARACHUTE_HIDDEN_Z,
                packed[-1][4]),
               (land_t + 8.0, packed[-1][1], packed[-1][2], PARACHUTE_HIDDEN_Z,
                packed[-1][4])]

    partial_start = stage_pose(t_partial, 1.85, 0.05)
    partial_end = stage_pose(t_full, 1.85, 0.05)
    ground_x, ground_y = fp[-1][0] + 1.10, fp[-1][1] + 0.55
    partial = [
        (0.0, *hidden), (t_partial, *hidden), partial_start, partial_end,
        (t_full, partial_end[1], partial_end[2], PARACHUTE_HIDDEN_Z, partial_end[4]),
        (t_collapse, ground_x, ground_y, PARACHUTE_HIDDEN_Z, 0.35),
        (t_collapse, ground_x, ground_y, 0.08, 0.35),
        (land_t + 8.0, ground_x, ground_y, 0.08, 0.35),
    ]

    full_visible = []
    full_times = {round(t_full, 6), round(land_t, 6)}
    t = t_full
    while t < land_t:
        full_times.add(round(t, 6))
        t += 0.20
    full_times.update(round(wp[0], 6) for wp in iha_base if t_full <= wp[0] <= land_t)
    for tt in sorted(full_times):
        full_visible.append(stage_pose(tt, 3.45, PARACHUTE_CANOPY_SWAY_M))
    full = [(0.0, *hidden), (t_full, *hidden)] + full_visible
    full_last = full_visible[-1]
    full += [
        (t_collapse, full_last[1], full_last[2], full_last[3], full_last[4]),
        (t_collapse, full_last[1], full_last[2], PARACHUTE_HIDDEN_Z, full_last[4]),
        (land_t + 8.0, full_last[1], full_last[2], PARACHUTE_HIDDEN_Z, full_last[4]),
    ]

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
              + block("parachute_packed", packed) + "\n"
              + block("parachute_partial", partial) + "\n"
              + block("parachute_full", full) + "\n"
              + block(f"ika_{zone['sfx']}", ika) + "\n    </plugin>")
    return plugin, duration, scan_end_t, land_t


# ── SDF yardımcıları ──────────────────────────────────────────────────────────

def _material(r, g, b, material_name=None, material_uri=ASPHALT_MATERIAL_URI):
    if material_name:
        return f"""<material>
            <specular>{ASPHALT_SPECULAR:.2f} {ASPHALT_SPECULAR:.2f} {ASPHALT_SPECULAR:.2f} 1</specular>
            <script>
              <uri>{material_uri}</uri>
              <name>{material_name}</name>
            </script>
          </material>"""
    return f"""<material>
            <ambient>{r:.2f} {g:.2f} {b:.2f} 1</ambient>
            <diffuse>{r:.2f} {g:.2f} {b:.2f} 1</diffuse>
            <specular>{ASPHALT_SPECULAR:.2f} {ASPHALT_SPECULAR:.2f} {ASPHALT_SPECULAR:.2f} 1</specular>
          </material>"""


def _box(name, px, py, pz, sx, sy, sz, r, g, b, yaw=0.0, static=True,
         material_name=None):
    st = "<static>true</static>" if static else ""
    return f"""
    <model name="{name}">
      {st}
      <pose>{px:.3f} {py:.3f} {pz:.3f} 0 0 {yaw:.3f}</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          {_material(r, g, b, material_name)}
        </visual>
      </link>
    </model>"""


def _visual_box(name, px, py, pz, sx, sy, sz, r, g, b, yaw=0.0,
                alpha=0.35, static=True):
    st = "<static>true</static>" if static else "<static>false</static>"
    transparency = max(0.0, min(1.0, 1.0 - float(alpha)))
    return f"""
    <model name="{name}">
      {st}
      <pose>{px:.3f} {py:.3f} {pz:.3f} 0 0 {yaw:.3f}</pose>
      <link name="link">
        <gravity>false</gravity>
        <kinematic>true</kinematic>
        <visual name="vis">
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <transparency>{transparency:.3f}</transparency>
          <material>
            <ambient>{r:.2f} {g:.2f} {b:.2f} {alpha:.2f}</ambient>
            <diffuse>{r:.2f} {g:.2f} {b:.2f} {alpha:.2f}</diffuse>
          </material>
        </visual>
      </link>
    </model>"""


def _flat(name, px, py, sx, sy, r, g, b, yaw=0.0, material_name=None):
    return _box(name, px, py, 0.01, sx, sy, 0.02, r, g, b, yaw,
                material_name=material_name)


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


def _ground_plane(profile=None, terrain=TERRAIN_DEFAULT):
    env = (profile or {}).get("environment", {})
    friction = float(env.get("ground_friction", 0.8))

    if terrain == "relief" and Path(RELIEF_HEIGHTMAP_PATH).exists():
        # Heightmap KABARTMA: yatayda RELIEF_SIZE_M, dikeyde RELIEF_MAX_Z. Görev
        # sahaları (3 HTAB) PNG'de DÜZ bırakıldığı için çarpışma orada değişmez.
        return f"""
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="collision">
        <geometry><heightmap>
          <uri>{RELIEF_HEIGHTMAP_URI}</uri>
          <size>{RELIEF_SIZE_M:.1f} {RELIEF_SIZE_M:.1f} {RELIEF_MAX_Z:.3f}</size>
          <pos>0 0 0</pos>
        </heightmap></geometry>
        <surface><friction><ode><mu>{friction:.3f}</mu><mu2>{friction:.3f}</mu2></ode></friction></surface>
      </collision>
      <visual name="visual"><cast_shadows>false</cast_shadows>
        <geometry><heightmap>
          <uri>{RELIEF_HEIGHTMAP_URI}</uri>
          <size>{RELIEF_SIZE_M:.1f} {RELIEF_SIZE_M:.1f} {RELIEF_MAX_Z:.3f}</size>
          <pos>0 0 0</pos>
        </heightmap></geometry>
        {_material(*DIRT_RGB)}
      </visual></link></model>"""

    if terrain == "relief":
        # PNG yoksa sessizce yanlış dünya kurmak yerine plain'e düş + uyar.
        print(f"[world_gen] UYARI: relief seçildi ama {RELIEF_HEIGHTMAP_PATH} yok → "
              "plain zemine düşülüyor (scripts/generate_terrain_heightmap.py ile üret).",
              file=sys.stderr)

    if terrain == "textured":
        # Gerçek arena referansı: açık kahve toprak (düz çarpışma korunur). Ogre
        # script yerine DÜZ renk → llvmpipe altında kesin render (algı ipucu).
        r, g, b = DIRT_RGB
        return f"""
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="collision"><geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        <surface><friction><ode><mu>{friction:.3f}</mu><mu2>{friction:.3f}</mu2></ode></friction></surface></collision>
      <visual name="visual"><cast_shadows>false</cast_shadows>
        <geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        {_material(r, g, b)}
      </visual></link></model>"""

    # plain (varsayılan): mevcut davranış — hiçbir şey değişmez.
    r, g, b = env.get("ground_color", ASPHALT_RGB)
    return f"""
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="collision"><geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        <surface><friction><ode><mu>{friction:.3f}</mu><mu2>{friction:.3f}</mu2></ode></friction></surface></collision>
      <visual name="visual"><cast_shadows>false</cast_shadows>
        <geometry><plane><normal>0 0 1</normal><size>400 400</size></plane></geometry>
        {_material(r, g, b, material_name=ASPHALT_MATERIAL_NAME)}
      </visual></link></model>"""


def _zone_grid(cx, cy, sfx):
    """textured modda HTAB üzerine şartname s.9'daki ölçüm IZGARASI (traversable
    ipucu). Zon zemini üstünde (GRID_Z), yol/işaret altında → z-fight yok."""
    gr, gg, gb = GRID_RGB
    n = int(HTAB / GRID_SPACING_M)          # 50/5 = 10 hücre → 11 çizgi/yön
    p = []
    for i in range(n + 1):
        off = -HTAB_HALF + i * GRID_SPACING_M
        # X'e paralel (yatay) çizgi
        p.append(_box(f"grid_{sfx}_h{i}", cx, cy + off, GRID_Z,
                      HTAB, GRID_LINE_W, 0.006, gr, gg, gb))
        # Y'ye paralel (dikey) çizgi
        p.append(_box(f"grid_{sfx}_v{i}", cx + off, cy, GRID_Z,
                      GRID_LINE_W, HTAB, 0.006, gr, gg, gb))
    return "\n".join(p)


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
    terrain = z.get("terrain", TERRAIN_DEFAULT)
    if terrain == "textured":
        # Açık kahve toprak + ölçüm ızgarası (şartname s.9). Çarpışma düz.
        dr, dg, db = DIRT_RGB
        p = [_flat(f"gd_{s}", cx, cy, HTAB, HTAB, dr, dg, db),
             _zone_grid(cx, cy, s)]
    else:
        gr, gg, gb = z.get("ground_color", ASPHALT_RGB)
        # Gercek arena referansi: adlandirilmis, gercek piksel dokulu asfalt.
        p = [_flat(f"gd_{s}", cx, cy, HTAB, HTAB, gr, gg, gb,
                   material_name=ASPHALT_MATERIAL_NAME)]
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
    textured = z.get("terrain", TERRAIN_DEFAULT) == "textured"
    # textured: koridor = molozsuz AÇILMIŞ toprak (referans s.9 gibi), asfalt bandı DEĞİL.
    col = (0.67, 0.58, 0.43) if textured else ASPHALT_RGB
    mat = None if textured else ASPHALT_MATERIAL_NAME
    p = []
    for road, path in z["harita"]["paths"].items():
        seg = arena._downsample(path, step=2.4)
        for i in range(len(seg) - 1):
            (x0, y0), (x1, y1) = seg[i], seg[i + 1]
            L = math.dist(seg[i], seg[i + 1]) + 0.9          # bindirme payı (boşluk kalmasın)
            yaw = math.atan2(y1 - y0, x1 - x0)
            p.append(_box(f"road_{s}_{road}_{i}", cx + (x0 + x1) / 2, cy + (y0 + y1) / 2,
                          Z_ROAD, L, z["lane_w"], 0.02, *col, yaw=yaw,
                          material_name=mat))
    return "\n".join(p)


def _rubble_color(rng):
    """Kirik beton/tugla/toz karisimi: egitim dagilimina yakin, tek ton degil."""
    palettes = (
        (0.48, 0.47, 0.44),  # eski beton
        (0.57, 0.55, 0.50),  # acik kirik yuzey
        (0.34, 0.33, 0.31),  # golgeli beton
        (0.61, 0.36, 0.25),  # tugla/kiremit parcasi
        (0.43, 0.30, 0.23),  # toprakli moloz
        (0.70, 0.66, 0.58),  # tozlu kenar
    )
    base = rng.choice(palettes)
    jitter = rng.uniform(-0.055, 0.055)
    return tuple(max(0.02, min(0.95, c + jitter + rng.uniform(-0.025, 0.025)))
                 for c in base)


def _rubble_piece_xml(index, ox, oy, pz, sx, sy, sz, r, g, b, yaw,
                      roll=0.0, pitch=0.0):
    return f"""
        <collision name="col_{index}">
          <pose>{ox:.3f} {oy:.3f} {pz:.3f} {roll:.3f} {pitch:.3f} {yaw:.3f}</pose>
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
        </collision>
        <visual name="vis_{index}">
          <pose>{ox:.3f} {oy:.3f} {pz:.3f} {roll:.3f} {pitch:.3f} {yaw:.3f}</pose>
          <cast_shadows>true</cast_shadows>
          <geometry><box><size>{sx:.3f} {sy:.3f} {sz:.3f}</size></box></geometry>
          <material>
            <ambient>{r:.2f} {g:.2f} {b:.2f} 1</ambient>
            <diffuse>{min(r*1.08, 1.0):.2f} {min(g*1.08, 1.0):.2f} {min(b*1.08, 1.0):.2f} 1</diffuse>
            <specular>0.05 0.05 0.045 1</specular>
          </material>
        </visual>"""


def _mesh_uri(nm):
    return f"file://{RUBBLE_MESH_DIR}/{nm}.obj"


def _rubble_piece_mesh(idx, nm, bbox, ox, oy, oz, yaw, roll, pitch, scale, rgb,
                       collide=True):
    """Bir enkaz parçası: gerçek mesh görseli + (isteğe bağlı) sadeleştirilmiş
    kutu collision (prompt §17: visual mesh ≠ ağır collision). Eğik parçada
    collision dik kutu olarak yaklaşıklanır (nav için yeterli)."""
    bx, by, bz = bbox[0] * scale, bbox[1] * scale, bbox[2] * scale
    r, g, b = rgb
    col = ""
    if collide:
        col = (f'<collision name="c{idx}"><pose>{ox:.3f} {oy:.3f} {bz/2:.3f} 0 0 '
               f'{yaw:.3f}</pose><geometry><box><size>{bx:.3f} {by:.3f} {bz:.3f}'
               f'</size></box></geometry></collision>')
    return f"""        {col}
        <visual name="v{idx}"><pose>{ox:.3f} {oy:.3f} {oz:.3f} {roll:.3f} {pitch:.3f} {yaw:.3f}</pose>
          <cast_shadows>true</cast_shadows>
          <geometry><mesh><uri>{_mesh_uri(nm)}</uri><scale>{scale:.3f} {scale:.3f} {scale:.3f}</scale></mesh></geometry>
          <material><ambient>{r:.3f} {g:.3f} {b:.3f} 1</ambient><diffuse>{r:.3f} {g:.3f} {b:.3f} 1</diffuse><specular>0.02 0.02 0.02 1</specular></material>
        </visual>"""


def _rebar_visual(idx, ox, oy, base_z, rng):
    """Betondan çıkan inşaat demiri: ince, eğik metal çubuk(lar) (prompt §5-C)."""
    out = []
    for j in range(rng.randint(1, 2)):
        L = rng.uniform(0.3, 0.85)
        rad = rng.uniform(0.006, 0.013)
        roll = rng.uniform(-0.55, 0.55)
        pitch = rng.uniform(-0.55, 0.55)
        px = ox + rng.uniform(-0.18, 0.18)
        py = oy + rng.uniform(-0.18, 0.18)
        pz = base_z + L * 0.42
        rr, gg, bb = rng.choice(_METAL)
        out.append(
            f'<visual name="rb{idx}_{j}"><pose>{px:.3f} {py:.3f} {pz:.3f} '
            f'{roll:.3f} {pitch:.3f} 0</pose><geometry><cylinder>'
            f'<radius>{rad:.4f}</radius><length>{L:.3f}</length></cylinder></geometry>'
            f'<material><ambient>{rr} {gg} {bb} 1</ambient><diffuse>{rr} {gg} {bb} 1'
            f'</diffuse><specular>0.15 0.15 0.15 1</specular></material></visual>')
    return "\n".join(out)


def _rubble_mesh_cluster(name, lx, ly, rng, big=False, height_multiplier=1.0,
                         richness=1.0):
    """GERÇEK enkaz kümesi (prompt §4/§8 katmanlı çöküş, YOĞUN).
      OMURGA : 1-3 'pile' (tek mesh'te 12-20 parça → yoğunluk, çizim çağrısı ucuz).
      ALT    : büyük kırık döşeme + (big) kolon/kiriş + duvar + ahşap/metal kiriş.
      ORTA   : bloklar (bazıları döşeme üstüne yığılı) + yarım duvar + tuğla yığını.
      ÜST/ÇEVRE: crumble kırıntı halesi + küçük parça + betondan çıkan rebar.
    richness: zorluk ölçeği (kolay<orta<zor) — parça sayısı ve pile adedini büyütür."""
    lib = _rubble_lib()
    hm = float(height_multiplier)
    parts = []
    state = {"idx": 0}
    base_yaw = rng.uniform(0, 2 * math.pi)
    spread = rng.uniform(1.1, 1.9) if big else rng.uniform(0.6, 1.15)

    def place(typ, scale, tiltmax, oz_extra=0.0, radial=0.6, collide=True):
        nm, bbox = rng.choice(lib[typ])
        rr = spread * radial * math.sqrt(rng.random())
        aa = rng.uniform(0, 2 * math.pi)
        ox, oy = rr * math.cos(aa), rr * math.sin(aa)
        yaw = base_yaw + rng.uniform(-math.pi, math.pi)
        roll = rng.uniform(-tiltmax, tiltmax)
        pitch = rng.uniform(-tiltmax, tiltmax)
        lift = 0.25 * (bbox[0] + bbox[1]) * scale * max(abs(math.sin(roll)),
                                                        abs(math.sin(pitch)))
        oz = oz_extra + 0.02 + lift
        rgb = _rubble_mat(typ, rng)
        parts.append(_rubble_piece_mesh(state["idx"], nm, bbox, ox, oy, oz,
                                        yaw, roll, pitch, scale, rgb, collide))
        state["idx"] += 1
        return bbox[2] * scale

    # ── OMURGA: yoğun yığın(lar) — merkezde üst üste binerek 'çöküş yığını' ──
    n_pile = (rng.randint(2, 3) if big else rng.randint(1, 2)) + (1 if richness > 1.05 else 0)
    for _ in range(n_pile):
        place("pile", rng.uniform(0.8, 1.15) * (1.0 + 0.12 * (richness - 1)),
              tiltmax=0.10, radial=0.55, collide=True)
    # ── ALT: büyük kırık döşeme + big ise kolon/kiriş/duvar/kiriş(ahşap-metal) ──
    slab_top = place("slab", rng.uniform(0.9, 1.3), tiltmax=0.14, radial=0.45)
    if big:
        place("column", rng.uniform(0.85, 1.2), tiltmax=0.18, radial=0.8)
        place("wall", rng.uniform(0.9, 1.25) * hm, tiltmax=0.10, radial=0.7)
        place("beam", rng.uniform(0.85, 1.15), tiltmax=0.20, radial=0.9, collide=False)
    # ── ORTA: bloklar (bazıları döşeme üstüne) + yarım duvar + tuğla ──
    n_mid = int(round((rng.randint(3, 5) if big else rng.randint(2, 3)) * richness))
    for _ in range(max(1, n_mid)):
        on_slab = rng.random() < 0.4
        place("block", rng.uniform(0.7, 1.15) * (hm if big else 1.0),
              tiltmax=0.28, oz_extra=slab_top * 0.8 if on_slab else 0.0, radial=0.8)
    if big and rng.random() < 0.55:
        place("wall", rng.uniform(0.7, 1.05) * hm, tiltmax=0.14, radial=0.95)
    if rng.random() < 0.5:
        place("beam", rng.uniform(0.7, 1.0), tiltmax=0.22, radial=1.0, collide=False)
    place("brick", rng.uniform(0.85, 1.25), tiltmax=0.24, radial=0.9)
    # ── ÜST/ÇEVRE: crumble kırıntı halesi + küçük parça + rebar ──
    n_small = int(round((rng.randint(2, 4) if big else rng.randint(1, 3)) * richness))
    for _ in range(max(1, n_small)):
        typ = rng.choice(["crumble", "crumble", "brick", "block"])
        place(typ, rng.uniform(0.6, 1.0), tiltmax=0.22, radial=1.25,
              collide=(typ == "block"))
    for _ in range(rng.randint(1, 2) if richness > 1.05 else rng.randint(0, 1)):
        place("crumble", rng.uniform(0.7, 1.1), tiltmax=0.2, radial=1.45, collide=False)
    if rng.random() < (0.55 if big else 0.28):
        parts.append(_rebar_visual(state["idx"], rng.uniform(-0.4, 0.4),
                                   rng.uniform(-0.4, 0.4), slab_top, rng))
        state["idx"] += 1

    body = "\n".join(parts)
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{lx:.3f} {ly:.3f} 0.000 0 0 0</pose>
      <link name="link">
{body}
      </link>
    </model>"""


def _rubble(name, lx, ly, rng, big=False, height_multiplier=1.0, realism=False,
            richness=1.0):
    if realism and _rubble_lib():
        return _rubble_mesh_cluster(name, lx, ly, rng, big=big,
                                    height_multiplier=height_multiplier,
                                    richness=richness)
    count = rng.randint(6, 10) if big else rng.randint(4, 7)
    spread = rng.uniform(1.0, 2.1) if big else rng.uniform(0.55, 1.35)
    base_yaw = rng.uniform(0, math.pi)
    parts = []
    for i in range(count):
        k = rng.random()
        if k < 0.30:
            sx, sy, sz = rng.uniform(1.4, 3.2), rng.uniform(0.65, 1.8), rng.uniform(0.16, 0.42)
        elif k < 0.58:
            sx, sy, sz = rng.uniform(0.45, 1.15), rng.uniform(0.35, 1.0), rng.uniform(0.35, 1.25)
        elif k < 0.78:
            sx, sy, sz = rng.uniform(1.0, 2.4), rng.uniform(0.12, 0.32), rng.uniform(0.12, 0.38)
        else:
            sx, sy, sz = rng.uniform(0.18, 0.52), rng.uniform(0.16, 0.48), rng.uniform(0.12, 0.35)
        if big:
            sx *= rng.uniform(1.10, 1.55)
            sy *= rng.uniform(1.05, 1.45)
            sz = max(sz * rng.uniform(1.10, 1.45), rng.uniform(0.55, 1.35))
        sz *= float(height_multiplier)
        radius = spread * math.sqrt(rng.random())
        angle = rng.uniform(0, 2 * math.pi)
        ox = radius * math.cos(angle)
        oy = radius * math.sin(angle)
        r, g, b = _rubble_color(rng)
        # Realizm modunda parçalar DEVRİK: küçük roll/pitch + biraz gömülü otur (kırık
        # beton yığını hissi). plain'de düz durur (baseline). Eğik parça zemine batmasın
        # diye merkez biraz yükseltilir.
        if realism:
            roll = rng.uniform(-0.28, 0.28)
            pitch = rng.uniform(-0.28, 0.28)
            tilt = (abs(sx) + abs(sy)) * 0.5 * max(abs(math.sin(roll)), abs(math.sin(pitch)))
            pz = sz / 2.0 + 0.4 * tilt
        else:
            roll = pitch = 0.0
            pz = sz / 2.0
        # Parca merkezleri zeminden baslar; farkli sz yukseklikleri tepeden golge/doku verir.
        parts.append(_rubble_piece_xml(i, ox, oy, pz, sx, sy, sz,
                                       r, g, b, base_yaw + rng.uniform(-1.4, 1.4),
                                       roll=roll, pitch=pitch))
    body = "\n".join(parts)
    return f"""
    <model name="{name}">
      <static>true</static>
      <pose>{lx:.3f} {ly:.3f} 0.000 0 0 0</pose>
      <link name="link">
{body}
      </link>
    </model>"""


def make_zone_debris(z, layout="field"):
    """GERÇEKÇİ enkaz sahası (kıvrımlı haritaya göre):
      · 2 KAPALI yol: rota ÜZERİNDE tikama_n noktada moloz TIKAMASI (yolu kesen küme)
        + yol girişine kırmızı-beyaz bariyer (yol yönüne dönük).
      · Saha geneli DAĞINIK moloz — 3 koridorun hiçbirine girmez (clearance),
        KB/HB/İHA işaretleri temiz kalır.
      · Açık yol kenarlarına chicane molozları (viraj hissi güçlenir).
    layout=field (vars.) tam yoğunluk; clean = dağınık moloz 1/3 (net sunum)."""
    rng = z["rng"]; cx, cy, s = z["cx"], z["cy"], z["sfx"]
    H = z["harita"]; lane_w = z["lane_w"]
    height_multiplier = z.get("rubble_height_multiplier", 1.0)
    realism = z.get("terrain", TERRAIN_DEFAULT) != "plain"   # textured/relief = mesh moloz
    # realism mesh kümeleri kütlesel (kompakt) → koridora yaklaşabilir (boş bant kalmasın),
    # ama açık rotayı kapatmayacak kadar clearance korunur (BFS ile doğrulandı).
    clear = (lane_w / 2.0 + 2.5) if realism else (lane_w / 2.0 + 1.2)
    richness = z.get("richness", 1.0)           # zorluk zenginlik ölçeği (küme yoğunluğu)
    lib_crumble = _rubble_lib().get("crumble", []) if realism else []
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
            # kümeyi yol EKSENİNE dik ser: tüm genişliği kapat + 2 sıra derinlik.
            # realism: mesh kümeleri GENİŞ → daha az küme yeter (kapama BFS ile doğrulanır).
            n_block = max(4, int(lane_w)) if realism else max(6, int(lane_w * 1.6))
            for j in range(n_block):
                u = rng.uniform(-lane_w / 2 - 0.5, lane_w / 2 + 0.5)   # yola dik eksen
                v = rng.uniform(-1.8, 1.8)                              # yol boyu eksen
                ox = px + v * math.cos(tyaw) - u * math.sin(tyaw)
                oy = py + v * math.sin(tyaw) + u * math.cos(tyaw)
                p.append(_rubble(f"blk_{s}_{road}_{k}_{j}", cx + ox, cy + oy, rng,
                                 big=True, height_multiplier=height_multiplier,
                                 realism=realism, richness=richness))

    # ── Saha geneli dağınık moloz ──
    # realism: SADECE açık rota temiz tutulur; kapalı rota alanları YOĞUN molozla
    # dolar (zaten kapalı → hem gerçekçi afet yoğunluğu hem kapama güçlenir).
    # plain: eski davranış (3 koridor da temiz).
    n = int(DIFF[z["scenario"]]["debris_n"] * float(z.get("debris_multiplier", 1.0)))
    if layout == "clean":
        n //= 3
    open_wps = H["paths"][z["road"]]

    def _outside_open(lx, ly, margin):
        """Açık rota + KB/HB temiz mi (realism'de sadece açık rota korunur)."""
        if realism:
            if dist_to_path(lx, ly, open_wps) < margin:
                return False
        elif dist_to_all_paths(lx, ly, H) < margin:
            return False
        if math.hypot(lx - kb[0], ly - kb[1]) < 3.0:
            return False
        if math.hypot(lx - hb[0], ly - hb[1]) < 3.5:
            return False
        return True

    placed = tries = 0
    while placed < n and tries < n * 15:
        tries += 1
        lx = rng.uniform(-HTAB_HALF + 1, HTAB_HALF - 1)
        ly = rng.uniform(-HTAB_HALF + 1, HTAB_HALF - 1)
        if not _outside_open(lx, ly, clear):
            continue
        p.append(_rubble(f"deb_{s}_{placed}", cx + lx, cy + ly, rng,
                         height_multiplier=height_multiplier, realism=realism,
                         richness=richness))
        placed += 1

    # ── MİKRO KIRINTI DAĞILIMI (realism) — küme-arası boşluğu 'gerçek enkaz sahası'
    #    dokusuyla doldurur: küçük crumble yamaları, açık koridora GİRMEZ (dar margin).
    #    Her yama tek mesh (5-9 parça) → yoğun görünüm, ucuz çizim. Collision YOK.
    if realism and lib_crumble:
        micro_n = int(DIFF[z["scenario"]].get("micro_n", 0)
                      * float(z.get("debris_multiplier", 1.0)))
        if layout == "clean":
            micro_n //= 3
        micro_clear = lane_w / 2.0 + 1.6         # mikro parça koridora daha çok yaklaşır
        placed = tries = 0
        while placed < micro_n and tries < micro_n * 12:
            tries += 1
            lx = rng.uniform(-HTAB_HALF + 0.5, HTAB_HALF - 0.5)
            ly = rng.uniform(-HTAB_HALF + 0.5, HTAB_HALF - 0.5)
            if not _outside_open(lx, ly, micro_clear):
                continue
            nm, bbox = rng.choice(lib_crumble)
            sc = rng.uniform(0.55, 1.05)
            yaw = rng.uniform(0, 2 * math.pi)
            rgb = _rubble_mat("crumble", rng)
            p.append(f"""
    <model name="mic_{s}_{placed}"><static>true</static>
      <pose>{cx + lx:.3f} {cy + ly:.3f} 0.010 0 0 {yaw:.3f}</pose>
      <link name="link">{_rubble_piece_mesh(0, nm, bbox, 0, 0, 0.01, 0, 0, 0, sc, rgb, collide=False)}
      </link></model>""")
            placed += 1

    # ── Chicane: açık yolun kenarına, sağlı sollu (kıvrımı vurgular) ──
    op = H["paths"][z["road"]]
    chicane_count = max(0, int(z.get("chicane_count", 5)))
    if chicane_count <= 1:
        fractions = [0.55] if chicane_count == 1 else []
    else:
        fractions = [0.18 + 0.64 * (i / (chicane_count - 1)) for i in range(chicane_count)]
    for wi, t in enumerate(fractions):
        ti = min(len(op) - 2, int(len(op) * t))
        (px, py), (qx, qy) = op[ti], op[ti + 1]
        tyaw = math.atan2(qy - py, qx - px)
        side = 1.0 if wi % 2 == 0 else -1.0
        off = side * (clear + rng.uniform(0.4, 1.1))
        ox = px - off * math.sin(tyaw)
        oy = py + off * math.cos(tyaw)
        # realism: chicane KÜÇÜK küme (big=False → 4 m kolon YOK, koridora taşmaz)
        p.append(_rubble(f"chic_{s}_{wi}", cx + ox, cy + oy, rng,
                         big=not realism, height_multiplier=height_multiplier,
                         realism=realism, richness=richness))
    return "\n".join(p)


def make_zone_markers(z):
    """1x1 çerçeve İKA-KB + 2x2 HB + kırmızı H — yol üstünde görünür kalır."""
    s = z["sfx"]; sx, sy = z["start_world"]; hx, hy = z["hb_world"]
    cr, cg, cb = z["color"]
    kb_edge_offset = (KB_OUTER_M - KB_FRAME_M) / 2.0
    kb_inner_span = KB_OUTER_M - 2.0 * KB_FRAME_M
    p = [_box(f"kb_{s}_N", sx, sy + kb_edge_offset, Z_PAD,
              KB_OUTER_M, KB_FRAME_M, KB_HEIGHT_M, cr, cg, cb),
         _box(f"kb_{s}_S", sx, sy - kb_edge_offset, Z_PAD,
              KB_OUTER_M, KB_FRAME_M, KB_HEIGHT_M, cr, cg, cb),
         _box(f"kb_{s}_W", sx - kb_edge_offset, sy, Z_PAD,
              KB_FRAME_M, kb_inner_span, KB_HEIGHT_M, cr, cg, cb),
         _box(f"kb_{s}_E", sx + kb_edge_offset, sy, Z_PAD,
              KB_FRAME_M, kb_inner_span, KB_HEIGHT_M, cr, cg, cb),
         _box(f"hbpad_{s}", hx, hy, Z_PAD, 2.0, 2.0, 0.04, 0.92, 0.92, 0.88),
         _box(f"H_{s}_l", hx-0.45, hy, Z_H, 0.22, 1.45, 0.08, 0.9, 0.02, 0.02),
         _box(f"H_{s}_r", hx+0.45, hy, Z_H, 0.22, 1.45, 0.08, 0.9, 0.02, 0.02),
         _box(f"H_{s}_b", hx, hy, Z_H, 1.10, 0.22, 0.08, 0.9, 0.02, 0.02)]
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
    # İHA-İB: HTAB'ın doğusunda küçük hedef ped. Eski 30x30 m mavi alan hem
    # ölçeği bozuyor hem de İHA'nın hassas inişini saklıyordu.
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return "\n".join([
        _flat("landing", cx + 32, cy, 9.0, 9.0, 0.08, 0.22, 0.65),
        _box("landing_border_n", cx + 32, cy + 4.7, 0.08, 9.8, 0.35, 0.08, 0.95, 0.95, 0.95),
        _box("landing_border_s", cx + 32, cy - 4.7, 0.08, 9.8, 0.35, 0.08, 0.95, 0.95, 0.95),
        _box("landing_border_w", cx + 27.3, cy, 0.08, 0.35, 9.0, 0.08, 0.95, 0.95, 0.95),
        _box("landing_border_e", cx + 36.7, cy, 0.08, 0.35, 9.0, 0.08, 0.95, 0.95, 0.95),
        _box("landing_cross_x", cx + 32, cy, 0.10, 6.0, 0.18, 0.08, 1.0, 0.95, 0.05),
        _box("landing_cross_y", cx + 32, cy, 0.10, 0.18, 6.0, 0.08, 1.0, 0.95, 0.05),
    ])


def make_judge_camp():
    """Hakem alanı: 3 HTAB'dan bağımsız, güvenli mesafede açık saha/cadır düzeni."""
    x, y = 0.0, -105.0
    parts = [
        _flat("judge_camp_floor", x, y, 28.0, 16.0, 0.24, 0.36, 0.30),
        _box("judge_tent_roof", x, y, 2.6, 18.0, 10.0, 0.35, 0.95, 0.95, 0.88),
        _box("judge_tent_pole_1", x - 8, y - 4, 1.2, 0.18, 0.18, 2.4, 0.85, 0.85, 0.80),
        _box("judge_tent_pole_2", x + 8, y - 4, 1.2, 0.18, 0.18, 2.4, 0.85, 0.85, 0.80),
        _box("judge_tent_pole_3", x - 8, y + 4, 1.2, 0.18, 0.18, 2.4, 0.85, 0.85, 0.80),
        _box("judge_tent_pole_4", x + 8, y + 4, 1.2, 0.18, 0.18, 2.4, 0.85, 0.85, 0.80),
        _box("judge_table", x, y, 0.45, 5.0, 1.4, 0.25, 0.28, 0.18, 0.12),
        _box("judge_monitor_1", x - 1.4, y + 0.25, 0.95, 1.0, 0.12, 0.65, 0.02, 0.02, 0.025),
        _box("judge_monitor_2", x + 1.4, y + 0.25, 0.95, 1.0, 0.12, 0.65, 0.02, 0.02, 0.025),
        _box("judge_chair_1", x - 3.0, y - 2.0, 0.35, 0.9, 0.9, 0.25, 0.16, 0.16, 0.16),
        _box("judge_chair_2", x, y - 2.0, 0.35, 0.9, 0.9, 0.25, 0.16, 0.16, 0.16),
        _box("judge_chair_3", x + 3.0, y - 2.0, 0.35, 0.9, 0.9, 0.25, 0.16, 0.16, 0.16),
        _box("judge_flag", x + 12.0, y + 5.0, 1.4, 0.12, 0.12, 2.8, 0.85, 0.85, 0.85),
        _box("judge_flag_panel", x + 12.0, y + 5.8, 2.3, 0.08, 1.4, 0.8, 0.90, 0.10, 0.10),
    ]
    return "\n".join(parts)


def make_view_footprints(focus_zone):
    """Kayıtta görünen dinamik görüş alanı yer izleri.

    Plugin bu modelleri her sim tick'inde İHA/İKA pozuna taşır. Gerçek sensörler
    zaten SDF içinde; bunlar hakem videosunda algı alanını görünür kılan overlay'dir.
    """
    s = focus_zone["sfx"]
    scan_side = 2.0 * SCAN_Z * math.tan(1.3 / 2.0)
    parts = [
        _visual_box("iha_view_footprint", 0, 0, 0.13, scan_side, scan_side, 0.035,
                    0.0, 0.85, 1.0, alpha=0.20, static=False),
        _visual_box(f"ika_view_{s}_center", 0, 0, 0.16, 13.0, 0.18, 0.04,
                    0.0, 1.0, 0.55, alpha=0.75, static=False),
        _visual_box(f"ika_view_{s}_left", 0, 0, 0.16, 13.0, 0.14, 0.04,
                    0.0, 1.0, 0.55, alpha=0.55, static=False),
        _visual_box(f"ika_view_{s}_right", 0, 0, 0.16, 13.0, 0.14, 0.04,
                    0.0, 1.0, 0.55, alpha=0.55, static=False),
    ]
    return "\n".join(parts)


def _path_len_xyz(points):
    return sum(math.dist(points[i][:3], points[i + 1][:3]) for i in range(len(points) - 1))


def _path_len_xy(points):
    return sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def _route_xy_text(points):
    return ";".join(f"{x:.2f},{y:.2f}" for x, y in points)


def make_iha_launch(focus_zone):
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return _flat("launch", cx - 26, cy, 6.0, 6.0, 0.7, 0.7, 0.15)


def make_catapult(focus_zone):
    # Mancınık: HTAB'ın batısında, İHA fırlatma noktasında (kare içinde, sınır içi)
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return _include("catapult_main", "catapult", cx - 26, cy, 0.08)


def make_aftershock_barrier(focus_zone):
    cx, cy = focus_zone["cx"], focus_zone["cy"]
    return f"""
    <model name="aftershock_barrier">
      <pose>{cx + 2.0:.3f} {cy + 7.0:.3f} 8.000 0 0 0.35</pose>
      <link name="link">
        <gravity>false</gravity>
        <kinematic>true</kinematic>
        <collision name="col"><geometry><box><size>9.000 0.900 1.300</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>9.000 0.900 1.300</size></box></geometry>
          <material><ambient>0.42 0.36 0.31 1</ambient><diffuse>0.42 0.36 0.31 1</diffuse></material>
        </visual>
      </link>
    </model>"""


def make_parachute():
    """İHA paraşütü — mesh kanopi, 16 gore-hizalı ip ve üç şişme durumu.

    OBJ yüzeyleri zero-thickness'tir; gerçek vent mesh'in merkezindeki açıklıktır.
    Animasyon eklentisi bu üç modeli paket → kısmi → tam sırasıyla görünür yapar.
    """
    variants = {
        "packed": {"attach_r": 0.22, "line_bottom_z": -0.34, "harness_r": 0.08},
        "partial": {"attach_r": 0.75, "line_bottom_z": -1.68, "harness_r": 0.14},
        "full": {"attach_r": 1.18, "line_bottom_z": -3.25, "harness_r": 0.17},
    }
    models = []
    for variant, dims in variants.items():
        visuals = f"""
        <visual name="canopy_mesh">
          <geometry><mesh><uri>{PARACHUTE_MESH_URIS[variant]}</uri><scale>1 1 1</scale></mesh></geometry>
          <cast_shadows>true</cast_shadows>
          <transparency>0.03</transparency>
        </visual>"""
        upper_r = dims["attach_r"]
        lower_r = dims["harness_r"]
        lower_z = dims["line_bottom_z"]
        for i in range(PARACHUTE_GORE_COUNT):
            theta = i * 2.0 * math.pi / PARACHUTE_GORE_COUNT
            cs, sn = math.cos(theta), math.sin(theta)
            upper = (upper_r * cs, upper_r * sn, 0.015)
            lower = (lower_r * cs, lower_r * sn, lower_z)
            dx, dy, dz = (upper[j] - lower[j] for j in range(3))
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            mid = tuple((upper[j] + lower[j]) * 0.5 for j in range(3))
            yaw = math.atan2(dy, dx)
            pitch = math.atan2(math.hypot(dx, dy), dz)
            visuals += f"""
        <visual name="line_{i:02d}">
          <pose>{mid[0]:.4f} {mid[1]:.4f} {mid[2]:.4f} 0 {pitch:.5f} {yaw:.5f}</pose>
          <geometry><cylinder><radius>{PARACHUTE_LINE_RADIUS_M:.3f}</radius><length>{length:.4f}</length></cylinder></geometry>
          <material><ambient>0.13 0.13 0.12 1</ambient><diffuse>0.20 0.20 0.18 1</diffuse><specular>0.02 0.02 0.02 1</specular></material>
          <cast_shadows>true</cast_shadows>
        </visual>"""
        harness_z = lower_z - 0.03
        visuals += f"""
        <visual name="harness">
          <pose>0 0 {harness_z:.3f} 0 0 0</pose>
          <geometry><box><size>0.52 0.32 0.10</size></box></geometry>
          <material><ambient>0.16 0.15 0.13 1</ambient><diffuse>0.23 0.22 0.19 1</diffuse></material>
          <cast_shadows>true</cast_shadows>
        </visual>"""
        models.append(f"""
    <model name="parachute_{variant}"><static>true</static>
      <pose>0 0 {PARACHUTE_HIDDEN_Z:.1f} 0 0 0</pose>
      <link name="link">{visuals}
      </link>
    </model>""")
    return "\n".join(models)


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
          <update_rate>12</update_rate>
        </sensor>
      </link>
    </model>"""


def _save_camera_model(name, path, px, py, pz, roll, pitch, yaw, fov=1.05,
                       width=1280, height=720, fps=6):
    return f"""
    <model name="{name}"><static>true</static>
      <pose>{px:.3f} {py:.3f} {pz:.3f} {roll:.4f} {pitch:.4f} {yaw:.4f}</pose>
      <link name="link">
        <sensor name="cam" type="camera">
          <camera>
            <horizontal_fov>{fov:.3f}</horizontal_fov>
            <image><width>{width}</width><height>{height}</height><format>R8G8B8</format></image>
            <clip><near>0.1</near><far>500</far></clip>
            <save enabled="true"><path>{path}</path></save>
          </camera>
          <always_on>1</always_on>
          <update_rate>{fps}</update_rate>
        </sensor>
      </link>
    </model>"""


def make_overview_cameras():
    """Ek kayıt kameraları: tüm alan tepeden + 4 çevre kamerası."""
    return "\n".join([
        _save_camera_model("rec_overview_cam", "/tmp/frames_overview",
                           0, 0, 210, 0, 1.5708, 1.5708, fov=1.35, fps=4),
        _save_camera_model("rec_side_north", "/tmp/frames_side_north",
                           0, 118, 78, 0, 0.95, -1.5708, fov=1.35),
        _save_camera_model("rec_side_south", "/tmp/frames_side_south",
                           0, -118, 78, 0, 0.95, 1.5708, fov=1.35),
        _save_camera_model("rec_side_east", "/tmp/frames_side_east",
                           142, 0, 58, 0, 0.72, 3.1416, fov=1.10),
        _save_camera_model("rec_side_west", "/tmp/frames_side_west",
                           -142, 0, 58, 0, 0.72, 0.0000, fov=1.10),
    ])


def make_lights(record=False, profile=None):
    sh = "true"
    env = (profile or {}).get("environment", {})
    sun_diffuse = env.get("sun_diffuse", [0.9, 0.9, 0.85, 1])
    sun_direction = env.get("sun_direction", [-0.4, 0.2, -0.9])
    return f"""
    <light name="sun" type="directional"><cast_shadows>{sh}</cast_shadows>
      <pose>0 0 120 0 -0 0</pose><diffuse>{sun_diffuse[0]} {sun_diffuse[1]} {sun_diffuse[2]} {sun_diffuse[3]}</diffuse><specular>0.1 0.1 0.1 1</specular>
      <attenuation><range>1200</range><constant>0.9</constant><linear>0.01</linear><quadratic>0.001</quadratic></attenuation>
      <direction>{sun_direction[0]} {sun_direction[1]} {sun_direction[2]}</direction></light>"""


# ── Tam dünya (odak zon: zemin + 3 yol + moloz + animasyon) ───────────────────

def build_world(seed, focus, record=False, road=None, layout="field", harita_id=None,
                profile_id=None, terrain=TERRAIN_DEFAULT):
    # road = SADECE hata ayıklama; normalde açık yol gizli (arena.harita seed'i).
    profile = load_profile(profile_id) if profile_id else None
    explicit_map = harita_id is not None
    if profile:
        seed = profile["seed"] if seed is None else seed
        focus = profile["active_zone"] if focus is None else focus
        layout = profile["terrain"]["layout"] if layout is None else layout
        if not explicit_map:
            harita_id = profile["map_ids"][focus]
    if harita_id is None:
        harita_id = 1
    if layout is None:
        layout = "field"

    zones = []
    for scenario in ZONE_ORDER:
        zone_map = profile["map_ids"][scenario] if profile and not explicit_map else harita_id
        z = make_zone(scenario, seed, road if scenario == focus else None,
                      zone_map, profile, terrain=terrain)
        if profile:
            z["debris_multiplier"] = profile["terrain"]["debris_multiplier"]
        zones.append(z)
    fz = next(z for z in zones if z["scenario"] == focus)

    parts = [make_lights(record, profile), _ground_plane(profile, terrain), make_ub(),
             make_judge_camp(), make_iha_landing(fz), make_iha_launch(fz),
             make_catapult(fz)]
    for z in zones:
        parts += [make_zone_ground(z), make_road_surfaces(z),
                  make_zone_debris(z, layout), make_zone_markers(z), make_zone_ika(z)]
    parts += [make_iha_vehicle(fz)]
    if profile and profile["mission"]["dynamic_obstacle"] == "aftershock_barrier":
        parts.append(make_aftershock_barrier(fz))
    if record:
        parts.append(make_parachute())             # İHA paraşütü (anim ile açılır)
        parts.append(make_view_footprints(fz))     # İHA/İKA görüş alanı overlay'i
        parts.append(make_rec_camera(fz))          # top-down kayıt kamerası (sensör)
        parts.append(make_overview_cameras())      # tüm UB + 4 çevre kamera kaydı
        plugin, _, _, _ = make_anim_plugin(fz, profile)
        parts.append(plugin)

    body = "\n".join(parts)
    gui = make_gui_camera(fz, record)
    env = (profile or load_profile())["environment"]
    fog = env["fog"]
    wind = env["wind"]
    # Realizm modlarında (textured/relief) ambient DÜŞÜR → yönlü güneş baskın olur,
    # gölge/derinlik artar (afet sahası hissi). plain baseline DOKUNULMAZ (seçilebilirlik).
    amb = list(env["ambient"])
    if terrain in ("textured", "relief"):
        amb = [round(c * 0.55, 3) for c in amb[:3]] + [amb[3] if len(amb) > 3 else 1.0]
    wind_xml = (
        f"<wind><linear_velocity>{wind[0]} {wind[1]} {wind[2]}</linear_velocity></wind>"
    )
    fog_xml = ""
    if fog["enabled"]:
        fog_xml = (
            f"<fog><type>{fog['type']}</type><color>{fog['color'][0]} {fog['color'][1]} "
            f"{fog['color'][2]} {fog['color'][3]}</color><start>{fog['start']}</start>"
            f"<end>{fog['end']}</end><density>{fog['density']}</density></fog>"
        )
    return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="navitas_arena">
{gui}
    <physics type="ode"><max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor><real_time_update_rate>1000</real_time_update_rate>
      <gravity>0 0 -9.8</gravity></physics>
    {wind_xml}
    <scene><ambient>{amb[0]} {amb[1]} {amb[2]} {amb[3]}</ambient><background>{env['background'][0]} {env['background'][1]} {env['background'][2]} {env['background'][3]}</background>
      <shadows>true</shadows>{fog_xml}</scene>
    <!-- Seed: {seed} | Profil: {(profile or {'id': 'baseline'})['id']} | Odak: {focus} | layout: {layout} | açık yol: {arena.ROAD_LABEL[fz['road']]} -->
{body}
  </world>
</sdf>
""", fz


def _atomic_write_text(path, text, encoding="utf-8"):
    """Write generated worlds without leaving a truncated target on failure."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=encoding,
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as tmp:
            tmp_name = tmp.name
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
        tmp_name = None
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass


def main():
    ap = argparse.ArgumentParser(description="Navitas 3-zon sıralı dünya üreticisi")
    ap.add_argument("--profile", default=None,
                    help="scenarios/<id>.json profilini kullan")
    ap.add_argument("--focus", choices=ZONE_ORDER, default=None,
                    help="bu kayıtta odaklanılacak seviye")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", default="worlds/navitas_arena.world")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--layout", choices=["clean", "field"], default=None,
                    help="field=gerçekçi moloz sahası (vars.), clean=seyrek/net sunum")
    ap.add_argument("--terrain", choices=list(TERRAIN_MODES), default=TERRAIN_DEFAULT,
                    help="plain=düz asfalt (vars.), textured=toprak+ızgara+devrik moloz+ışık "
                         "(çarpışma düz — ÖNERİLEN görsel), relief=heightmap kabartma "
                         "(DENEYSEL: görev sahası düz kalır ama çevre yüzeyi texture "
                         "gerektirdiğinden düzgün render olmaz — bkz Kol B)")
    ap.add_argument("--map", type=int, default=None,
                    help=f"gerçekçi harita no (1-{arena.HARITA_N}) — her biri farklı "
                         "kıvrım/KB/HB düzeni")
    ap.add_argument("--road", type=int, choices=[1, 2, 3], default=None,
                    help="SADECE HATA AYIKLAMA: açık yolu elle seç. Normal akışta dünya "
                         "her zaman ground-truth ile kurulur; model tespiti dünyaya GERİ "
                         "BESLENMEZ (tersine nedensellik yasak).")
    args = ap.parse_args()

    try:
        profile = load_profile(args.profile) if args.profile else None
    except ValueError as exc:
        # Bozuk profil bir traceback'e değil, okunur tek satır hataya düşer.
        ap.error(str(exc))
    seed = args.seed if args.seed is not None else (profile["seed"] if profile else 42)
    focus = args.focus if args.focus is not None else (profile["active_zone"] if profile else "kolay")
    layout = args.layout if args.layout is not None else (profile["terrain"]["layout"] if profile else "field")
    map_id = args.map
    world, fz = build_world(seed, focus, record=args.record, road=args.road,
                            layout=layout, harita_id=map_id, profile_id=args.profile,
                            terrain=args.terrain)
    out = Path(args.output)
    _atomic_write_text(out, world)
    print(f"[world_gen] PROFILE={args.profile or 'baseline'}")
    print(f"[world_gen] SEED={seed}")
    print(f"[world_gen] TERRAIN={args.terrain}")   # record_in_container parse eder
    print(f"[world_gen] Odak={focus} @({fz['cx']},{fz['cy']}) harita={fz['harita_id']} "
          f"layout={layout} açık yol={arena.ROAD_LABEL[fz['road']]} | yazıldı: {out}")
    print(f"[world_gen] OPEN_ROAD={arena.ROAD_LABEL[fz['road']]}")   # record_in_container parse eder
    # İHA-haritalama (iha_haritala.py) için makine-okur meta:
    print(f"[world_gen] HTAB_CENTER={fz['cx']},{fz['cy']}")
    print(f"[world_gen] MAP={fz['harita_id']}")
    if profile:
        print(f"[world_gen] SCAN_ALTITUDE_M={profile['flight']['scan_altitude_m']}")
    print(f"[world_gen] KB_XY={fz['start_world'][0]:.2f},{fz['start_world'][1]:.2f}")
    print(f"[world_gen] HB_XY={fz['hb_world'][0]:.2f},{fz['hb_world'][1]:.2f}")
    if args.record:
        _, dur, scan_end, land_t = make_anim_plugin(fz, profile)
        iha_len = _path_len_xyz(iha_flight(fz["cx"], fz["cy"], profile))
        ika_len = _path_len_xy(fz["wp_world"])
        print(f"[world_gen] SCAN_END_T={scan_end:.0f}")   # tarama bitiş sim sn (marker anı)
        print(f"[world_gen] LAND_T={land_t:.0f}")         # İHA iniş sim sn
        print(f"[world_gen] IHA_PATH_M={iha_len:.1f}")
        print(f"[world_gen] IKA_PATH_M={ika_len:.1f}")
        print(f"[world_gen] IKA_DRIVE_T={ika_len / IKA_SPEED:.1f}")
        print(f"[world_gen] ROUTE_ROAD={fz['road']}")
        print(f"[world_gen] ROUTE_XY={_route_xy_text(fz['wp_world'])}")
        print(f"[world_gen] RECORD_SECONDS={dur + PAD_SEC:.0f}")


if __name__ == "__main__":
    main()
