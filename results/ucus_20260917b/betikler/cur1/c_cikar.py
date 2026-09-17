import sys, pickle
from collections import defaultdict
from pymavlink import mavutil
yol, cikti = sys.argv[1], sys.argv[2]
v = defaultdict(list)
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
while True:
    x = m.recv_match()
    if x is None: break
    tip = x.get_type()
    if tip in ("FMT","FMTU","UNIT","MULT","FILE","BAD_DATA"): continue
    d = x.to_dict(); d.pop("mavpackettype",None)
    ts = d.get("TimeUS")
    d["t"] = ts/1e6 if ts is not None else None
    v[tip].append(d)
with open(cikti, "wb") as f:
    pickle.dump(dict(v), f)
print({k: len(L) for k, L in sorted(v.items())})
