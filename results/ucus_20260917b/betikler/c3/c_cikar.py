import sys, pickle
from collections import defaultdict
from pymavlink import mavutil
yol, cikti = sys.argv[1], sys.argv[2]
tipler = ["RCIN","ATT","CTUN","RCOU","BAT","VIBE","IMU","RATE","EV","ARM","MODE","MSG","PARM","GPS","BARO","POS","XKF1","MOTB","PSCN","PSCE","PSCD"]
v = defaultdict(list)
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
while True:
    x = m.recv_match(type=tipler)
    if x is None: break
    d = x.to_dict(); tip = d.pop("mavpackettype")
    ts = d.get("TimeUS")
    d["t"] = ts/1e6 if ts is not None else None
    v[tip].append(d)
with open(cikti, "wb") as f:
    pickle.dump(dict(v), f)
print({k: len(L) for k, L in v.items()})
