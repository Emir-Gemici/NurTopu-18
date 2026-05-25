#!/usr/bin/env python3
"""
Navitas — İKA Otonom Navigasyon
Waypoint'ler arasında gezinir, DiffDrivePlugin'i gz topic ile kullanır.

Kullanım:
  python3 scripts/ika_nav.py [kolay|orta|zor]
"""

import subprocess
import math
import time
import re
import sys

# ── Waypoint haritası ─────────────────────────────────────────────────────────
WAYPOINTS = {
    "kolay": [
        (-23.0, -23.0),
        (-23.0, -10.0),
        (-15.0,   0.0),
        ( -5.0,  10.0),
        (  5.0,  15.0),
        ( 15.0,  20.0),
        ( 23.0,  23.0),
    ],
    "orta": [
        (-23.0, -23.0),
        (-20.0,  -8.0),
        ( -8.0,   2.0),
        (  5.0,   8.0),
        ( 15.0,  18.0),
        ( 23.0,  23.0),
    ],
    "zor": [
        (-23.0, -23.0),
        (-18.0, -15.0),
        ( -5.0,  -5.0),
        (  5.0,   5.0),
        ( 18.0,  20.0),
        ( 23.0,  23.0),
    ],
}

# ── Kontrol parametreleri ─────────────────────────────────────────────────────
MAX_SPEED   = 2.0   # m/s
TURN_GAIN   = 1.8   # dönüş orantı katsayısı
WP_RADIUS   = 1.5   # m — bu mesafeye gelince sonraki waypoint'e geç
CTRL_HZ     = 10    # Hz


def get_pose(model="ika"):
    """
    gz model -m ika -p çıktısını parse et.
    Döner: (x, y, z, yaw) veya (None, None, None, None)
    """
    try:
        r = subprocess.run(
            ["gz", "model", "-m", model, "-p"],
            capture_output=True, text=True, timeout=2
        )
        text = r.stdout + r.stderr

        # Format A: "position: (-23.0, -23.0, 0.12)"
        m = re.search(
            r'position[:\s(]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)',
            text
        )
        if m:
            x, y, z = float(m.group(1)), float(m.group(2)), float(m.group(3))
            # Quaternion → yaw
            q = re.search(
                r'orientation[:\s(]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)',
                text
            )
            if q:
                vals = [float(q.group(i)) for i in range(1, 5)]
                # Gazebo çıktısı genellikle (w, x, y, z) veya (x, y, z, w)
                # İkisini de deneriz; en büyük W olana göre:
                if abs(vals[0]) >= abs(vals[3]):  # (w, x, y, z)
                    qw, qx, qy, qz = vals
                else:                              # (x, y, z, w)
                    qx, qy, qz, qw = vals
                yaw = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
            else:
                # Son sayı yaw olabilir
                nums = re.findall(r'[+-]?\d+\.?\d*', text)
                yaw = float(nums[5]) if len(nums) >= 6 else 0.0
            return x, y, z, yaw

        # Format B: sadece sayılar → x y z roll pitch yaw
        nums = re.findall(r'[+-]?\d+\.?\d*', text)
        if len(nums) >= 6:
            return float(nums[0]), float(nums[1]), float(nums[2]), float(nums[5])

    except Exception as e:
        print(f"[ika_nav] Pose hatası: {e}")
    return None, None, None, None


def send_vel(right_spd, left_spd, topic="~/ika/vel_cmd"):
    """
    DiffDrivePlugin native mesaj: position.x = sağ tekerlek, position.y = sol tekerlek
    """
    msg = f"position {{ x: {right_spd:.3f} y: {left_spd:.3f} z: 0 }}"
    subprocess.run(
        ["gz", "topic", "-p", topic, "-m", msg],
        capture_output=True, timeout=1
    )


def wrap(a):
    while a >  math.pi: a -= 2 * math.pi
    while a < -math.pi: a += 2 * math.pi
    return a


def steer(heading_err, base=MAX_SPEED):
    """
    Heading hatası → (sağ_tekerlek, sol_tekerlek).
    err > 0 → sola dön: sağ tekerlek hızlı
    err < 0 → sağa dön: sol tekerlek hızlı
    """
    delta = TURN_GAIN * heading_err
    delta = max(-base, min(base, delta))
    r = max(-base, min(base, base + delta))
    l = max(-base, min(base, base - delta))
    return r, l


def navigate(scenario="kolay", verbose=True):
    wps = WAYPOINTS.get(scenario, WAYPOINTS["kolay"])
    dt = 1.0 / CTRL_HZ

    # Heading'i konum geçmişinden tahmin edeceğiz
    prev_x = prev_y = None
    current_yaw = math.atan2(
        wps[1][1] - wps[0][1],
        wps[1][0] - wps[0][0]
    )  # başlangıç tahmini: ilk hedefe doğru

    print(f"\n[ika_nav] Senaryo: {scenario} | {len(wps)-1} segment")
    print(f"[ika_nav] Başlangıç: {wps[0]} → Hedef: {wps[-1]}")

    for idx, (wx, wy) in enumerate(wps[1:], 1):
        print(f"\n[ika_nav] ── Waypoint {idx}/{len(wps)-1}: ({wx:.1f}, {wy:.1f})")

        at_wp = False
        while not at_wp:
            cx, cy, cz, gz_yaw = get_pose("ika")

            if cx is None:
                print("[ika_nav]   Konum alınamadı, bekleniyor...")
                time.sleep(0.5)
                continue

            # Yaw güncelleme: hareket vektöründen
            if prev_x is not None:
                ddx, ddy = cx - prev_x, cy - prev_y
                moved = math.hypot(ddx, ddy)
                if moved > 0.03:                # gürültüden kaçın
                    current_yaw = math.atan2(ddy, ddx)
            prev_x, prev_y = cx, cy

            dx, dy = wx - cx, wy - cy
            dist   = math.hypot(dx, dy)

            if dist < WP_RADIUS:
                send_vel(0, 0)
                print(f"[ika_nav]   ✓ Ulaşıldı (kalan: {dist:.2f}m)")
                at_wp = True
                time.sleep(0.3)
                continue

            desired = math.atan2(dy, dx)
            err     = wrap(desired - current_yaw)

            r, l = steer(err)
            send_vel(r, l)

            if verbose:
                print(f"[ika_nav]   pos=({cx:.1f},{cy:.1f}) "
                      f"dist={dist:.1f}m err={math.degrees(err):.0f}° "
                      f"wheel=({r:.1f},{l:.1f})")

            time.sleep(dt)

    send_vel(0, 0)
    print("\n[ika_nav] ══ HEDEF BÖLGEYE (HB) ULAŞILDI! ══")
    return True


if __name__ == "__main__":
    sc = sys.argv[1] if len(sys.argv) > 1 else "kolay"
    if sc not in WAYPOINTS:
        print(f"Bilinmeyen senaryo: {sc}  →  kolay|orta|zor")
        sys.exit(1)
    navigate(sc)
