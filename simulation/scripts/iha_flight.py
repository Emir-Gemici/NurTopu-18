#!/usr/bin/env python3
"""
Navitas — İHA Uçuş Animasyonu
İHA statik model; bu script ~/model/modify topic'i aracılığıyla pose'unu
güncelleyerek uçuş simüle eder. ROS gerektirmez.

Uçuş planı:
  Fırlatma Bölgesi (-105, 0, 1.5) → tırmanış → seyir (z=20m) → alçalış → İniş Bölgesi (85, 0, 0)

Kullanım:
  python3 scripts/iha_flight.py [--fps 20] [--speed 1.0]
"""

import subprocess
import math
import time
import sys

# Uçuş waypoint'leri: (x, y, z, yaw_derece, faz_adı)
FLIGHT_PATH = [
    (-105.0,  0.0,  1.5,   0.0, "rampa"),
    ( -90.0,  0.0,  5.0,   0.0, "kalkış"),
    ( -60.0,  0.0, 15.0,   0.0, "tırmanış"),
    ( -20.0,  0.0, 20.0,   0.0, "seyir-başı"),
    (  30.0,  0.0, 20.0,   0.0, "seyir-sonu"),
    (  65.0,  0.0, 10.0,   0.0, "alçalış"),
    (  80.0,  0.0,  3.0,   0.0, "yaklaşma"),
    (  85.0,  0.0,  0.0,   0.0, "iniş"),
]

MODIFY_TOPIC = "~/model/modify"
IHA_NAME     = "iha"


def set_pose(x: float, y: float, z: float, yaw_rad: float = 0.0):
    """
    İHA'yı belirtilen konuma ışınla (~/model/modify).
    Quaternion = sadece Z ekseni dönüşü.
    """
    qz = math.sin(yaw_rad / 2.0)
    qw = math.cos(yaw_rad / 2.0)
    msg = (
        f"name: '{IHA_NAME}' "
        f"pose {{ "
        f"  position {{ x: {x:.3f} y: {y:.3f} z: {z:.3f} }} "
        f"  orientation {{ x: 0 y: 0 z: {qz:.4f} w: {qw:.4f} }} "
        f"}}"
    )
    subprocess.run(
        ["gz", "topic", "-p", MODIFY_TOPIC, "-m", msg],
        capture_output=True, timeout=1
    )


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_angle(a, b, t):
    diff = (b - a + math.pi) % (2 * math.pi) - math.pi
    return a + diff * t


def fly(fps: float = 20.0, speed_mult: float = 1.0, verbose: bool = True):
    """
    FLIGHT_PATH boyunca İHA'yı hareket ettir.
    speed_mult: 1.0 = gerçek zamanlı, 2.0 = 2x hızlı
    """
    dt = 1.0 / fps

    # Her segment arasındaki 3D mesafeye göre süreyi belirle
    # Yaklaşık gerçekçi hız: rampa→kalkış kısa, seyir hızlı
    SEGMENT_SPEEDS = {   # m/s, her faz için
        "rampa":     0.0,   # sadece başlangıç noktası
        "kalkış":   12.0,
        "tırmanış": 20.0,
        "seyir-başı": 25.0,
        "seyir-sonu": 25.0,
        "alçalış":  18.0,
        "yaklaşma": 12.0,
        "iniş":      0.0,
    }

    print("\n[iha_flight] ══ İHA UÇUŞU BAŞLIYOR ══")
    print(f"[iha_flight] Rota: {FLIGHT_PATH[0][4]} → {FLIGHT_PATH[-1][4]}")

    set_pose(*FLIGHT_PATH[0][:3], math.radians(FLIGHT_PATH[0][3]))
    time.sleep(1.0)

    for seg_i in range(len(FLIGHT_PATH) - 1):
        x0, y0, z0, yaw0_deg, faz0 = FLIGHT_PATH[seg_i]
        x1, y1, z1, yaw1_deg, faz1 = FLIGHT_PATH[seg_i + 1]

        seg_dist = math.sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2)
        seg_spd  = SEGMENT_SPEEDS.get(faz0, 20.0) * speed_mult
        if seg_spd < 0.1:
            seg_spd = 20.0  # varsayılan
        seg_dur  = seg_dist / seg_spd
        steps    = max(1, int(seg_dur * fps))

        yaw0 = math.radians(yaw0_deg)
        yaw1 = math.radians(yaw1_deg)

        # Yaw: hedefe bakan yön
        flight_yaw = math.atan2(y1 - y0, x1 - x0)

        print(f"[iha_flight] Segment {seg_i+1}: {faz0} → {faz1} "
              f"({seg_dist:.0f}m, {seg_dur:.1f}s, {steps} adım)")

        for step in range(steps + 1):
            t = step / steps
            cx = lerp(x0, x1, t)
            cy = lerp(y0, y1, t)
            cz = lerp(z0, z1, t)
            set_pose(cx, cy, cz, flight_yaw)
            if verbose and step % max(1, steps // 5) == 0:
                print(f"[iha_flight]   ({cx:.1f}, {cy:.1f}, {cz:.1f})")
            time.sleep(dt)

    # Son konuma kilitle
    x_f, y_f, z_f, yaw_f_deg, _ = FLIGHT_PATH[-1]
    set_pose(x_f, y_f, z_f, math.radians(yaw_f_deg))
    print(f"\n[iha_flight] ══ İHA İNİŞ YAPTI: ({x_f}, {y_f}) ══")
    return True


if __name__ == "__main__":
    fps   = 20.0
    speed = 1.0
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--fps"   and i+2 <= len(sys.argv[1:]): fps   = float(sys.argv[i+2])
        if arg == "--speed" and i+2 <= len(sys.argv[1:]): speed = float(sys.argv[i+2])
    fly(fps=fps, speed_mult=speed)
