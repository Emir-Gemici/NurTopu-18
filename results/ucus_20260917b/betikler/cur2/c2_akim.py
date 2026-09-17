# Curutucu 2: akim modeli I = k * sum(a_i^p) * (V/15)^q ; havadaki normal ornekler ile uydur, olaya uygula
import pickle
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
def veri(fn, pencereler):
    d = pickle.load(open(S+fn,"rb"))["d"]
    T = lambda r: r["TimeUS"]/1e6
    rc = d["RCOU"]; bt = d["BAT"]; tb = np.array([T(r) for r in bt])
    out = []
    for r in rc:
        t = T(r)
        if not any(a<=t<=b for a,b in pencereler): continue
        j = np.argmin(abs(tb-t)); b = bt[j]
        if abs(tb[j]-t) > 0.02: continue
        a = np.clip((np.array([r["C11"],r["C10"],r["C12"],r["C9"]],float)-1150)/800, 0, 1)
        out.append((t, a, b["Volt"], b["Curr"]))
    return out
egit = veri("c2_b.pkl", [(141.5,148.0),(188.7,202.30)]) + veri("c2_a.pkl", [(622.5,647.8)])
A = np.array([o[1] for o in egit]); V = np.array([o[2] for o in egit]); I = np.array([o[3] for o in egit])
print("egitim n", len(I), "a aralik %.2f..%.2f  I %.1f..%.1f" % (A.min(), A.max(), I.min(), I.max()))
best=None
for p in np.arange(1.0, 3.51, 0.1):
    for q in np.arange(0.0, 3.01, 0.25):
        x = (A**p).sum(1) * (V/15)**q
        k = (x@I)/(x@x); e = np.sqrt(((k*x-I)**2).mean())
        if best is None or e < best[0]: best = (e,p,q,k)
e,p,q,k = best
print("en iyi p %.1f q %.2f k %.1f rmse %.2f A" % (p,q,k,e))
def tahmin(o): return k*(o[1]**p).sum()*(o[2]/15)**q
print("-- kontrol: 00:20 dusus penceresi (648.2-649.7)")
for o in veri("c2_a.pkl", [(648.2,649.7)]):
    print("  %.3f a %s V %.2f olculen %.1f  model %.0f" % (o[0], np.round(o[1],2), o[2], o[3], tahmin(o)))
print("-- 02:50 olay (202.27-204.0)")
for o in veri("c2_b.pkl", [(202.27,204.0)]):
    print("  %.3f a %s V %.2f olculen %.1f  model %.0f" % (o[0], np.round(o[1],2), o[2], o[3], tahmin(o)))
