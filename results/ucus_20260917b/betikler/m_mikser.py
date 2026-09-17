import pickle, bisect
L = pickle.load(open("log.pkl","rb")); d = L["d"]
e=0.65
def thr(p):
    r=(p-1150)/800.0
    r=max(0.0,min(1.0,r))
    return e*r*r+(1-e)*r
rate=d["RATE"]; rts=[x["TimeUS"] for x in rate]
mot=d["MOTB"]; mts=[x["TimeUS"] for x in mot]
def near(xs,ts,t):
    i=bisect.bisect_left(ts,t); c=[j for j in (i-1,i) if 0<=j<len(xs)]
    return xs[min(c,key=lambda j:abs(ts[j]-t))]
def st(v):
    v=sorted(v); n=len(v); return f"n={n} min={v[0]:.3f} med={v[n//2]:.3f} max={v[-1]:.3f}"
for ad,a,b in [("L2 140.9-147.5",140.9,147.5),("SON 188.4-195",188.4,195),("SON 195-202.37",195,202.37)]:
    rows=[]
    for o in d["RCOU"]:
        t=o["TimeUS"]/1e6
        if not a<=t<=b: continue
        t1,t2,t3,t4=thr(o["C11"]),thr(o["C10"]),thr(o["C12"]),thr(o["C9"])
        yaw=(t1+t2-t3-t4)/2; roll=(t2+t3-t1-t4)/2; pitch=(t1+t3-t2-t4)/2; avg=(t1+t2+t3+t4)/4
        R=near(rate,rts,o["TimeUS"]); M=near(mot,mts,o["TimeUS"])
        rows.append((yaw,R["YOut"],roll,R["ROut"],pitch,R["POut"],avg,M["ThrOut"],min(t1,t2,t3,t4)))
    print("==",ad)
    print(" uygulanan yaw (itki uzayi)",st([r[0] for r in rows])," YOut",st([r[1] for r in rows]))
    print(" yaw_uygulanan/YOut (YOut>0.1)",st([r[0]/r[1] for r in rows if r[1]>0.1]) if any(r[1]>0.1 for r in rows) else "YOut>0.1 yok")
    print(" uygulanan roll",st([r[2] for r in rows])," ROut",st([r[3] for r in rows]))
    print(" uygulanan pitch",st([r[4] for r in rows])," POut",st([r[5] for r in rows]))
    print(" ort itki",st([r[6] for r in rows])," ThrOut",st([r[7] for r in rows]))
    print(" en dusuk motor itkisi",st([r[8] for r in rows]))
