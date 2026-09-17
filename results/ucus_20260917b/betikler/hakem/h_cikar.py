import sys, pickle
from collections import defaultdict
from pymavlink import mavutil
yol, cikti = sys.argv[1], sys.argv[2]
tipler = ["RCIN","ATT","CTUN","RCOU","BAT","VIBE","IMU","RATE","MOTB","PSCN","PSCE","PSCD","EV","ERR","MODE","ARM","MSG","XKF1","POWR","MAG","GPS","PARM","CTRL","BARO"]
v = defaultdict(list)
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
while True:
    x = m.recv_match(type=tipler)
    if x is None: break
    d = x.to_dict(); tip = d.pop("mavpackettype")
    if tip == "PARM":
        v[tip].append(d); continue
    ts = d.get("TimeUS")
    if ts is None: continue
    d["t"] = ts/1e6
    v[tip].append(d)
with open(cikti, "wb") as f:
    pickle.dump(dict(v), f)
print({k: len(L) for k, L in v.items()})
