"""Dumen-arm penceresinin ayrintisi + CH6 anahtar cevirme zamanlari + gevsek denemeler + 'Arm:' metinleri."""
import sys
from datetime import datetime, timedelta
from pymavlink import mavutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
yol = sys.argv[1]
m = mavutil.mavlink_connection(yol)
rc, arm, txt, cmd = [], [], [], []
armed = None
t0 = None
while True:
    msg = m.recv_match(blocking=False)
    if msg is None:
        break
    t = getattr(msg, "_timestamp", 0.0)
    if t0 is None and t:
        t0 = t
    tp = msg.get_type()
    if tp == "RC_CHANNELS":
        rc.append((t - t0, msg.chan3_raw, msg.chan4_raw, msg.chan5_raw, msg.chan6_raw))
    elif tp == "HEARTBEAT" and msg.get_srcSystem() == 1 and msg.get_srcComponent() == 1:
        a = bool(msg.base_mode & 128)
        if a != armed:
            arm.append((t - t0, a)); armed = a
    elif tp == "STATUSTEXT":
        txt.append((t - t0, msg.text))
    elif tp == "COMMAND_LONG" and msg.command == 400:
        cmd.append(t - t0)

def saat(s):
    return (datetime.fromtimestamp(t0) + timedelta(seconds=s)).strftime("%H:%M:%S")

print(f"log başlangıcı {saat(0)}; RC_CHANNELS örnek aralığı ~{(rc[-1][0]-rc[0][0])/max(1,len(rc)-1):.2f} s")

print("\n1) DÜMEN-ARM PENCERESİ 6205–6240 s (CH3 gaz, CH4 yaw, CH6 anahtar):")
son = None
for t, c3, c4, c5, c6 in rc:
    if 6205 <= t <= 6240:
        if son is None or t - son >= 0.5:
            print(f"  {saat(t)}  t={t:7.1f}  gaz={c3}  yaw={c4}  ch5={c5}  ch6={c6}")
            son = t
for t, a in arm:
    if 6200 <= t <= 6245:
        print(f"  >>> {saat(t)} t={t:.1f} {'ARMED' if a else 'DISARMED'}")

print("\n2) 'Arm:' / 'Throttle' / 'Disarm' STATUSTEXT'leri (PreArm hariç):")
n = 0
for t, s in txt:
    if s.startswith("PreArm"):
        continue
    if any(w in s for w in ("Arm", "arm", "Throttle", "throttle", "Safety", "safety")):
        print(f"  {saat(t)}  t={t:7.1f}  {s}"); n += 1
if not n:
    print("  (yok)")

print("\n3) CH6 ANAHTARI ÇEVRİLME ANLARI ve ±3 s içinde arm geçişi var mı:")
onceki = None; k = 0
for t, c3, c4, c5, c6 in rc:
    if onceki is not None and c6 != onceki:
        yakin = [(round(tt, 1), 'ARM' if a else 'DIS') for tt, a in arm if abs(tt - t) <= 3]
        gcs = [round(tt, 1) for tt in cmd if abs(tt - t) <= 3]
        print(f"  {saat(t)}  t={t:7.1f}  ch6 {onceki}→{c6}  gaz={c3}  yaw={c4}  arm geçişi={yakin or 'YOK'}  gcs komutu={gcs or '-'}")
        k += 1
    onceki = c6
print(f"  toplam {k} çevirme")

print("\n4) CH5 (uçuş modu anahtarı) ÇEVRİLME sayısı:")
onceki = None; k = 0
for t, c3, c4, c5, c6 in rc:
    if onceki is not None and c5 != onceki:
        k += 1
    onceki = c5
print(f"  {k}")

print("\n5) GEVŞEK DÜMEN DENEMELERİ — yaw ≥1800 ama ya gaz >1100 ya da yaw <1947 (arm eşiği ~1947), ≥1,0 s:")
bas = None; ilk = None
for i, (t, c3, c4, c5, c6) in enumerate(rc):
    kosul = c4 >= 1800 and not (c3 <= 1100 and c4 >= 1947)
    if kosul and bas is None:
        bas = t; ilk = (c3, c4)
    if (not kosul or i == len(rc) - 1) and bas is not None:
        if t - bas >= 1.0:
            print(f"  {saat(bas)}  {bas:7.1f}–{t:7.1f} ({t-bas:.1f} s)  ilk örnek gaz={ilk[0]} yaw={ilk[1]}")
        bas = None
