"""
Navitas — gerçekçi görev süreleri (şartname limitleri).

İHA görev süresi (fırlatma→iniş)  ≤ 900 s (15 dk)
İKA görev süresi (hareket→H teması) ≤ 600 s (10 dk)
Hazırlık süresi                    ≤ 900 s (15 dk)

realtime modu (1): süreler gerçekçi, limit kontrolü + GEÇERLİ/GEÇERSİZ.
timeless modu (0): süre devre dışı (mevcut hızlı/süresiz sistem).
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import arena

IHA_LIMIT      = 900    # 15 dk
IKA_LIMIT      = 600    # 10 dk
HAZIRLIK_LIMIT = 900    # 15 dk

# Gerçekçi İHA görev süresi (mancınık→serpantin tarama→tespit→aktarım→paraşüt iniş) — s
# (şartname: 30m'den 50×50 tarama 20-30s, tespit <60s; toplam görev limiti 15dk içinde rahat)
IHA_SCAN = {"kolay": 150, "orta": 200, "zor": 250}
# İKA seyir hızı (m/s) — gerçekçi diferansiyel rover (PDF: 24V encoderli motor, ≤10dk/HB).
# PDF açık hız vermez; 10dk limiti + 12-15cm teker + dikkatli moloz nav'dan türetildi.
IKA_REAL_SPEED = 1.1
# Gerçekçi hazırlık süresi — s
HAZIRLIK = {"kolay": 540, "orta": 600, "zor": 660}


def path_len(road, level, harita_id=1):
    wps = arena.route_waypoints(road, level, harita_id)
    return sum(math.dist(wps[i], wps[i + 1]) for i in range(len(wps) - 1))


def realistic(level, road=None, harita_id=1):
    """Gerçekçi süreler (s) — şartname limitleri içinde."""
    if road not in (1, 2, 3):
        road = arena.open_road(level, harita_id)
    iha = IHA_SCAN.get(level, 180)
    ika = round(path_len(road, level, harita_id) / IKA_REAL_SPEED)
    ika = min(ika, IKA_LIMIT - 8)            # limit içinde tut
    haz = HAZIRLIK.get(level, 600)
    return {"iha": iha, "ika": ika, "hazirlik": haz}


def fmt(sec):
    sec = int(round(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


def status(t, limit):
    return "GEÇERLİ" if t <= limit else "GEÇERSİZ"
