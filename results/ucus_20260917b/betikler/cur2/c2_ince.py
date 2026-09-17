# Curutucu 2: 0.1 s ince tablo (RCOU zamanina hizali, en yakin ornek)
import pickle, sys, math
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
P = pickle.load(open(S+sys.argv[1],"rb")); d = P["d"]
t0, t1 = float(sys.argv[2]), float(sys.argv[3])
def T(r): return r["TimeUS"]/1e6
def near(tip, t, flt=None):
    best=None; bd=9
    for r in d[tip]:
        if flt and any(r.get(k)!=v for k,v in flt.items()): continue
        dd = abs(T(r)-t)
        if dd < bd: bd=dd; best=r
    return best
rows = [r for r in d["RCOU"] if t0<=T(r)<=t1]
print("t | M1 M2 M3 M4 CCW-CW | Alt CRt ThO | R P DesY Y yerr | RATE Ydes Y YOut | IMU0 gz ax ay az | VibeZ0 Clip0/1 | RCIN C1 C3 C4 C5 C6 | V I")
for r in rows:
    t = T(r)
    c = near("CTUN",t); a = near("ATT",t); ra = near("RATE",t); b = near("BAT",t); rn = near("RCIN",t)
    v0 = near("VIBE",t,{"IMU":0}); v1 = near("VIBE",t,{"IMU":1}); im = near("IMU",t,{"I":0})
    M1,M2,M3,M4 = r["C11"],r["C10"],r["C12"],r["C9"]
    ye = ((a["DesYaw"]-a["Yaw"]+180)%360)-180
    print("%.2f | %d %d %d %d %+d | %.2f %4.0f %.3f | %.1f %.1f %.1f %.1f %+.1f | %.1f %.1f %.3f | %.1f %.1f %.1f %.1f | %.1f %d/%d | %d %d %d %d %d | %.2f %.1f" % (
        t, M1,M2,M3,M4,M1+M2-M3-M4, c["Alt"], c["CRt"], c["ThO"], a["Roll"], a["Pitch"], a["DesYaw"], a["Yaw"], ye,
        ra["YDes"], ra["Y"], ra["YOut"], math.degrees(im["GyrZ"]), im["AccX"], im["AccY"], im["AccZ"], v0["VibeZ"], v0["Clip"], v1["Clip"],
        rn["C1"], rn["C3"], rn["C4"], rn["C5"], rn["C6"], b["Volt"], b["Curr"]))
