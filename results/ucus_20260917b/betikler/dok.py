import sys, pickle
from collections import defaultdict
from pymavlink import mavutil
yol = sys.argv[1]
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
d = defaultdict(list); fmt = {}
seq = []
i = 0
while True:
    x = m.recv_match()
    if x is None: break
    tip = x.get_type()
    if tip == "FMT":
        fmt[x.Name] = (x.Columns, x.Format)
        continue
    if tip in ("FMTU","UNIT","MULT","FILE"): continue
    dd = x.to_dict(); dd.pop("mavpackettype", None)
    d[tip].append(dd)
    ts = dd.get("TimeUS")
    seq.append((i, tip, ts))
    i += 1
pickle.dump({"d": dict(d), "fmt": fmt, "seq": seq}, open("log.pkl", "wb"))
print({k: len(v) for k, v in d.items()})
for k in ["POWR","MCU","BAT","MAG","XKF4","XKF3","GPS","RATE","MOTB","IOMC","RCIN","ERR","VIBE","IMU","XKFS","XKF1","CTRL","DSF","STAK","PM","MAV","RCI2"]:
    print(k, fmt.get(k))
