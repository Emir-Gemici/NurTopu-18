import pickle, bisect
import numpy as np
L = pickle.load(open("log.pkl","rb")); d = L["d"]
e=0.65
def t_of(p):
    r=max(0,min(1,(p-1150)/800)); return e*r*r+(1-e)*r
bat=d["BAT"]; bts=[x["TimeUS"] for x in bat]
def nb(t):
    i=bisect.bisect_left(bts,t); c=[j for j in (i-1,i) if 0<=j<len(bat)]; return bat[min(c,key=lambda j:abs(bts[j]-t))]
rows=[]
for o in d["RCOU"]:
    t=o["TimeUS"]/1e6
    if 181.6<=t<=203.3:
        b=nb(o["TimeUS"]); pw=[o["C11"],o["C10"],o["C12"],o["C9"]]
        A=sum(t_of(p)**1.5 for p in pw)
        B=(b["Volt"]**2)*sum(((p-1000)/1000.0)**3 for p in pw)
        A_noM1=sum(t_of(p)**1.5 for p in pw[1:]); B_noM1=(b["Volt"]**2)*sum(((p-1000)/1000.0)**3 for p in pw[1:])
        rows.append((t,b["Curr"],A,B,A_noM1,B_noM1,pw,b["Volt"]))
fit=[r for r in rows if 188.4<=r[0]<=202.37]
I=np.array([r[1] for r in fit])
for idx,ad in ((2,"A: I=k*sum(thrust^1.5)"),(3,"B: I=k*V^2*sum(esc^3)")):
    X=np.array([r[idx] for r in fit])
    k=float(np.dot(X,I)/np.dot(X,X))
    res=I-k*X
    print(f"{ad}: k={k:.2f}  hover artik: ort|hata|={np.mean(np.abs(res)):.2f} A, maks|hata|={np.max(np.abs(res)):.2f} A, ort I={I.mean():.1f} A (n={len(fit)})")
    for r in rows:
        if 202.2<=r[0]<=203.3:
            print(f"   {r[0]:.2f} olculen {r[1]:6.1f} A | model(4 motor) {k*r[idx]:6.1f} | model(M1 sifir) {k*r[idx+2]:6.1f} | PWM M1..M4 {r[6]} V={r[7]:.2f}")
