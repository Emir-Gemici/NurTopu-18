import sys, pickle
from collections import defaultdict
from pymavlink import mavutil
yol = r"O:\navitas\results\ucus_20260917b\2026-09-17 02-50-38.bin"
v = defaultdict(list)
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
fmt = {}
while True:
    x = m.recv_match()
    if x is None: break
    tip = x.get_type()
    if tip in ("FMT","FMTU","PARM","UNIT","MULT","FILE"): continue
    ts = getattr(x, "TimeUS", None)
    if ts is None: continue
    t = ts/1e6
    d = x.to_dict(); d.pop("mavpackettype", None)
    v[tip].append((t, d))
pickle.dump(dict(v), open("tum.pkl","wb"))
print({k: len(L) for k, L in v.items()})
