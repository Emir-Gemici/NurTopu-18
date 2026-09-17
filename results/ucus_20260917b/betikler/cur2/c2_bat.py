# Curutucu 2: BAT + RCOU + CTUN, akim/gerilim iliskisi
import pickle, sys
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
P = pickle.load(open(S+sys.argv[1],"rb")); d = P["d"]
t0, t1 = float(sys.argv[2]), float(sys.argv[3])
def T(r): return r["TimeUS"]/1e6
bat = [r for r in d["BAT"] if t0<=T(r)<=t1]
rc = [r for r in d["RCOU"] if t0-0.2<=T(r)<=t1+0.2]
ct = [r for r in d["CTUN"] if t0-0.2<=T(r)<=t1+0.2]
def near(rs,t): return min(rs, key=lambda r: abs(T(r)-t))
for b in bat:
    t=T(b); r=near(rc,t); c=near(ct,t)
    V0 = 16.16
    print("%.3f V %.2f I %.1f VoltR %.2f Res %.4f | (VoltR-V)/Res %.0f | M1 %d M2 %d M3 %d M4 %d | ThO %.3f" % (t, b["Volt"], b["Curr"], b["VoltR"], b["Res"], (b["VoltR"]-b["Volt"])/b["Res"] if b["Res"]>0 else -1, r["C11"], r["C10"], r["C12"], r["C9"], c["ThO"]))
