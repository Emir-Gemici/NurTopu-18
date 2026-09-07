import sys
from datetime import datetime, timedelta
from pymavlink import mavutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
m = mavutil.mavlink_connection(sys.argv[1])
pencereler = [(3833, 3850, "P19 20:56"), (4056, 4092, "P20 21:00"), (6077, 6090, "P26 21:33"), (6721, 6768, "P37 21:44")]
rc, att = [], []
t0 = None
while True:
    msg = m.recv_match(type=["RC_CHANNELS", "ATTITUDE"], blocking=False)
    if msg is None: break
    t = msg._timestamp
    if t0 is None: t0 = t
    if msg.get_type() == "RC_CHANNELS":
        rc.append((t - t0, msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw))
    else:
        import math
        att.append((t - t0, math.degrees(msg.roll), math.degrees(msg.pitch)))
def saat(s): return (datetime.fromtimestamp(t0) + timedelta(seconds=s)).strftime("%H:%M:%S")
for a, b, ad in pencereler:
    print(f"\n=== {ad}  (t {a}-{b})  roll=CH1 pitch=CH2 gaz=CH3 yaw=CH4 ===")
    ai = [x for x in att if a <= x[0] <= b]
    for t, c1, c2, c3, c4 in rc:
        if a <= t <= b:
            p = min(ai, key=lambda x: abs(x[0] - t)) if ai else (0, 0, 0)
            bayrak = "  <-- pitch kolu merkez dışı" if abs(c2 - 1500) > 60 else ""
            print(f"  {saat(t)} t={t:7.1f}  roll={c1} pitch={c2} gaz={c3} yaw={c4}   ölçülen roll {p[1]:6.1f}° pitch {p[2]:6.1f}°{bayrak}")
    if ai:
        print(f"  pitch min {min(x[2] for x in ai):.1f}°  max {max(x[2] for x in ai):.1f}°")
