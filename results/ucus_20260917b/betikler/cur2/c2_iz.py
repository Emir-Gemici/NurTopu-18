# Curutucu 2: 1 s kutularda iz (CTUN, RCOU, IMU gyro rms, RCIN)
import pickle, sys
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
P = pickle.load(open(S+sys.argv[1],"rb"))
t0, t1, adim = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
d = P["d"]
def T(r): return r["TimeUS"]/1e6
def arr(tip, keys, flt=None):
    rs = [r for r in d[tip] if (flt is None or all(r.get(k)==v for k,v in flt.items()))]
    t = np.array([T(r) for r in rs]); return t, {k: np.array([r[k] for r in rs], float) for k in keys}
tc, c = arr("CTUN", ["ThO","ThH","Alt","BAlt","DAlt","CRt"])
tr, rc = arr("RCOU", ["C9","C10","C11","C12"])
ti, im = arr("IMU", ["GyrX","GyrY","GyrZ","AccZ"], {"I":0})
tn, rn = arr("RCIN", ["C1","C2","C3","C4","C5","C6"])
tv, vb = arr("VIBE", ["VibeZ","Clip"], {"IMU":0})
ta, at = arr("ATT", ["Roll","Pitch","DesYaw","Yaw"])
tb, bt = arr("BAT", ["Volt","Curr"])
print("t    | ThO   ThH   Alt  BAlt  DAlt | M1   M2   M3   M4  CCW-CW | gxR  gyR  gz_ort | VibeZ Clip | C1-C4 min/max | R    P   yawerr | V  I")
t = t0
while t < t1:
    a, b = t, t+adim
    mc = (tc>=a)&(tc<b); mr=(tr>=a)&(tr<b); mi=(ti>=a)&(ti<b); mn=(tn>=a)&(tn<b); mv=(tv>=a)&(tv<b); ma=(ta>=a)&(ta<b); mb=(tb>=a)&(tb<b)
    if mc.sum()==0: t+=adim; continue
    M1,M2,M3,M4 = rc["C11"][mr],rc["C10"][mr],rc["C12"][mr],rc["C9"][mr]
    ye = ((at["DesYaw"][ma]-at["Yaw"][ma]+180)%360)-180
    sc = " ".join("%d-%d" % (rn[k][mn].min(), rn[k][mn].max()) for k in ["C1","C2","C3","C4"]) if mn.sum() else "-"
    print("%6.1f | %.3f %.3f %5.2f %5.2f %5.2f | %4.0f %4.0f %4.0f %4.0f %+5.0f | %5.1f %5.1f %6.1f | %5.1f %3.0f | %s | %5.1f %5.1f %5.1f | %.2f %.1f" % (
        a, c["ThO"][mc].mean(), c["ThH"][mc].mean(), c["Alt"][mc].mean(), c["BAlt"][mc].mean(), c["DAlt"][mc].mean(),
        M1.mean(), M2.mean(), M3.mean(), M4.mean(), (M1+M2-M3-M4).mean(),
        np.degrees(np.sqrt((im["GyrX"][mi]**2).mean())), np.degrees(np.sqrt((im["GyrY"][mi]**2).mean())), np.degrees(im["GyrZ"][mi].mean()),
        vb["VibeZ"][mv].mean(), vb["Clip"][mv].max(), sc, at["Roll"][ma].mean(), at["Pitch"][ma].mean(), ye.mean(), bt["Volt"][mb].mean(), bt["Curr"][mb].mean()))
    t += adim
