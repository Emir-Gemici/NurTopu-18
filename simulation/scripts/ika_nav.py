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
from pathlib import Path

# arena (waypoint kaynağı) + comms (açık yolu İHA'dan al)
sys.path.insert(0, str(Path(__file__).parent))            # scripts/
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
import arena
from arena import route_waypoints, open_road, ROAD_LABEL

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


def navigate(wps, label="rota", verbose=True):
    if len(wps) < 2:
        raise ValueError("navigasyon için en az iki waypoint gerekli")
    dt = 1.0 / CTRL_HZ

    # Heading'i konum geçmişinden tahmin edeceğiz
    prev_x = prev_y = None
    current_yaw = math.atan2(
        wps[1][1] - wps[0][1],
        wps[1][0] - wps[0][0]
    )  # başlangıç tahmini: ilk hedefe doğru

    print(f"\n[ika_nav] {label} | {len(wps)-1} segment")
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


def navigate_road(road, scenario="kolay", harita_id=1, origin=None, verbose=True):
    """İHA'dan gelen açık yol (1/2/3) → arena rotası ile navigate."""
    origin = arena.ZONE_POS[scenario] if origin is None else origin
    local_wps = route_waypoints(road, scenario, harita_id)
    world_wps = [arena.to_world(point, origin) for point in local_wps]
    return navigate(world_wps,
                    f"Açık yol: {ROAD_LABEL[road].upper()} ({road})", verbose)


def navigate_scenario(scenario, harita_id=1, verbose=True):
    return navigate_road(open_road(scenario, harita_id), scenario, harita_id,
                         verbose=verbose)


def wait_open_route_from_comms(bind="0.0.0.0:5006", timeout=60):
    """İHA'nın doğrulanmış OPEN_ROUTE mesajını bekle ve tamamını döndür."""
    from link import UDPLink
    from ika_receiver import IkaReceiver
    h, p = bind.split(":")
    rx = IkaReceiver(UDPLink(bind=(h, int(p)))).start()
    print(f"[ika_nav] comms dinleniyor ({bind}) — İHA açık yolu gönderecek...")
    t0 = time.time()
    while rx.latest is None and time.time() - t0 < timeout:
        time.sleep(0.2)
    rx.stop()
    rx.link.close()
    if rx.latest is None:
        return None
    route = rx.latest
    road = route["road"]
    print(f"[ika_nav] ✓ İHA'dan açık yol ALINDI: {ROAD_LABEL[road].upper()} ({road}) "
          f"conf={route.get('conf')} wp={len(route.get('waypoints') or [])}")
    return route


def navigate_route_message(route, fallback_scenario="kolay", harita_id=1, verbose=True):
    """Use transmitted coordinates; arena geometry is only a compatibility fallback."""
    local_wps = route.get("waypoints") or []
    ref = route.get("ref_xy")
    if local_wps and ref:
        world_wps = [(float(ref[0]) + float(point[0]),
                      float(ref[1]) + float(point[1])) for point in local_wps]
        return navigate(world_wps, f"İHA rota seq={route['seq']}", verbose)
    return navigate_road(route["road"], fallback_scenario, harita_id, verbose=verbose)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="İKA navigasyon (arena + comms)")
    ap.add_argument("mode", nargs="?", default="kolay",
                    help="senaryo: kolay|orta|zor  ·  veya 'comms' (İHA'dan bekle)")
    ap.add_argument("--road", type=int, choices=[1, 2, 3], help="açık yolu doğrudan ver")
    ap.add_argument("--bind", default="0.0.0.0:5006", help="comms modu dinleme adresi")
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--map", type=int, choices=range(1, arena.HARITA_N + 1), default=1)
    args = ap.parse_args()

    if args.road:
        navigate_road(args.road, args.mode if args.mode in arena.SCENARIOS else "kolay", args.map)
    elif args.mode == "comms":
        route = wait_open_route_from_comms(args.bind, args.timeout)
        if route is None:
            print("[ika_nav] ✗ açık yol gelmedi (timeout) — İKA hareket etmez")
            sys.exit(1)
        navigate_route_message(route, "kolay", args.map)
    elif args.mode in ("kolay", "orta", "zor"):
        navigate_scenario(args.mode, args.map)
    else:
        print("Kullanım: ika_nav.py [kolay|orta|zor|comms] [--road N]")
        sys.exit(1)
