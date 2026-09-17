# Curutucu 2: .bin -> pickle (bagimsiz cikarim)
import sys, pickle, collections
from pymavlink import mavutil
yol, cikti = sys.argv[1], sys.argv[2]
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
d = collections.defaultdict(list)
parm = {}
while True:
    x = m.recv_msg()
    if x is None: break
    t = x.get_type()
    if t in ("FMT","FMTU","UNIT","MULT","FILE"): continue
    if t == "PARM":
        parm[x.Name] = x.Value; continue
    r = x.to_dict()
    r.pop("mavpackettype", None)
    d[t].append(r)
pickle.dump({"d": dict(d), "parm": parm}, open(cikti, "wb"))
print({k: len(v) for k, v in d.items()})
print("parm", len(parm))
