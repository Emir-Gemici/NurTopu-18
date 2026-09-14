#!/usr/bin/env python3
"""Navitas Gazebo dünya üreticisi için sabit İHA hız sarmalayıcısı.

Ana world_generator modülünü kullanır ancak İHA'nın tüm waypoint zamanlamasını
tek hız kaynağına bağlar. Faz bazlı farklı hızlar devre dışıdır.
"""

import math
import random
import sys

import world_generator as wg
from iha_speed import IHA_FLIGHT_SPEED_MPS


# Eski faz tablosunu çalışma anında tamamen tek değere indir.
wg.IHA_FLIGHT_SPEED = IHA_FLIGHT_SPEED_MPS
wg.PHASE_SPEED = {
    "rampa": IHA_FLIGHT_SPEED_MPS,
    "kalkis": IHA_FLIGHT_SPEED_MPS,
    "tirmanis": IHA_FLIGHT_SPEED_MPS,
    "tarama": IHA_FLIGHT_SPEED_MPS,
    "donus": IHA_FLIGHT_SPEED_MPS,
    "sokulma": IHA_FLIGHT_SPEED_MPS,
    "parasut": IHA_FLIGHT_SPEED_MPS,
}


def _timed_flight_constant(fp, t0=0.0):
    """Tüm 3B İHA rota segmentlerini tam 18.65 m/s ile zamanla."""
    out = []
    t = t0
    for i, p in enumerate(fp):
        j = min(i, len(fp) - 2)
        yaw = math.atan2(fp[j + 1][1] - fp[j][1], fp[j + 1][0] - fp[j][0])
        if i > 0:
            t += math.dist(fp[i - 1][:3], p[:3]) / IHA_FLIGHT_SPEED_MPS
        out.append((t, p[0], p[1], p[2], yaw))
    return out


wg._timed_flight = _timed_flight_constant


def _normalize_legacy_args(argv):
    """Eski navitas.launch argümanlarını güncel world_generator CLI'ına çevir."""
    args = list(argv)
    out = []
    i = 0
    seed = 42
    requested_focus = None

    while i < len(args):
        arg = args[i]
        if arg == "--difficulty" and i + 1 < len(args):
            requested_focus = args[i + 1]
            i += 2
            continue
        if arg == "--open-path":
            # Eski başlatıcıdaki bu bayrağın güncel üreticide karşılığı yok.
            i += 1
            continue
        if arg == "--seed" and i + 1 < len(args):
            seed = int(args[i + 1])
            out.extend([arg, args[i + 1]])
            i += 2
            continue
        if arg.startswith("--seed="):
            seed = int(arg.split("=", 1)[1])
        out.append(arg)
        i += 1

    if requested_focus:
        if requested_focus == "rastgele":
            requested_focus = random.Random(seed).choice(wg.ZONE_ORDER)
        out.extend(["--focus", requested_focus])

    return out


if __name__ == "__main__":
    sys.argv[1:] = _normalize_legacy_args(sys.argv[1:])
    print(f"[world_gen] IHA_SPEED_MPS={IHA_FLIGHT_SPEED_MPS:.2f}")
    wg.main()
