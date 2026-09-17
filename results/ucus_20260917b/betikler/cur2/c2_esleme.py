# Curutucu 2: motor eslemesini fiziksel olarak dogrula
# (1) firmware karisimi: motor sapmasi ~ ROut/POut/YOut
# (2) fiziksel: sonraki acisal ivme ~ motor farki; 24 permutasyon
import pickle, math, itertools, sys
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
d = pickle.load(open(S+"c2_b.pkl","rb"))["d"]
def T(r): return r["TimeUS"]/1e6
pencereler = [(141.5,147.9),(188.7,202.30)]
rc = [r for r in d["RCOU"] if any(a<=T(r)<=b for a,b in pencereler)]
ra = {round(T(r),2): r for r in d["RATE"]}
im = [r for r in d["IMU"] if r["I"]==0]
ti = np.array([T(r) for r in im]); gx = np.array([r["GyrX"] for r in im]); gy = np.array([r["GyrY"] for r in im]); gz = np.array([r["GyrZ"] for r in im])
Cn = ["C9","C10","C11","C12"]
X = np.array([[r[c] for c in Cn] for r in rc], float)
tr = np.array([T(r) for r in rc])
# (1) firmware karisimi
rate = [min(d["RATE"], key=lambda q: abs(T(q)-t)) for t in tr]
U = np.array([[q["ROut"], q["POut"], q["YOut"], 1.0] for q in rate])
dev = X - X.mean(1, keepdims=True)
print("(1) motor sapmasi = a*ROut + b*POut + c*YOut  (Quad-X beklenen: M1 -,+,+  M2 +,-,+  M3 +,+,-  M4 -,-,-)")
for j,c in enumerate(Cn):
    coef,*_ = np.linalg.lstsq(U, dev[:,j], rcond=None)
    print("   %s  ROut %+7.0f  POut %+7.0f  YOut %+7.0f" % (c, coef[0], coef[1], coef[2]))
# (2) fiziksel: t -> [t, t+0.08] ivme
def ivme(g, t):
    i0 = np.searchsorted(ti, t); i1 = i0 + 2
    if i1 >= len(ti): return np.nan
    return (g[i1]-g[i0])/(ti[i1]-ti[i0])
ar = np.array([ivme(gx,t) for t in tr]); ap = np.array([ivme(gy,t) for t in tr]); ay = np.array([ivme(gz,t) for t in tr])
def skor(perm):
    # perm: C9..C12 -> motor numarasi (1..4)
    M = {perm[k]: X[:,k] for k in range(4)}
    ur = (M[2]+M[3]-M[1]-M[4])/4; up = (M[1]+M[3]-M[2]-M[4])/4; uy = (M[1]+M[2]-M[3]-M[4])/4
    f = lambda a,b: np.corrcoef(a-a.mean(), b-b.mean())[0,1]
    return f(ur,ar), f(up,ap), f(uy,ay)
sonuc = []
for perm in itertools.permutations([1,2,3,4]):
    s = skor(perm); sonuc.append((sum(s), perm, s))
sonuc.sort(reverse=True)
print("(2) n=%d; C9..C12 -> motor; korelasyon (roll, pitch, yaw) ivme~komut" % len(tr))
for tot, perm, s in sonuc[:6]:
    print("   %s  toplam %+.3f  roll %+.3f pitch %+.3f yaw %+.3f" % (perm, tot, *s))
print("   ...")
for tot, perm, s in sonuc[-2:]:
    print("   %s  toplam %+.3f  roll %+.3f pitch %+.3f yaw %+.3f" % (perm, tot, *s))
