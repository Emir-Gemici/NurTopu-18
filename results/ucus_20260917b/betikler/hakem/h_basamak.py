from h_ortak import *
import math, sys, numpy as np
v=yukle("hb.pkl")
def wrap(x): return (x+180)%360-180
for (a,b) in ((188.9,190.1),(193.9,195.3)):
    print("=== ",a,b)
    R={round(d["t"],1):d for d in pen(v,"RCOU",a,b)}
    for d in pen(v,"ATT",a,b):
        t=round(d["t"],1); r=R.get(t); c=[x for x in pen(v,"CTUN",d["t"]-0.01,d["t"]+0.01)]; q=[x for x in pen(v,"RATE",d["t"]-0.01,d["t"]+0.01)]
        vb=[x for x in pen(v,"VIBE",d["t"]-0.01,d["t"]+0.01) if x["IMU"]==0]; rc=[x for x in pen(v,"RCIN",d["t"]-0.06,d["t"]+0.04)]
        g=[math.degrees(x["GyrZ"]) for x in pen(v,"IMU",d["t"]-0.1,d["t"]) if x["I"]==0]
        s=f"{d['t']:.2f} yawErr {wrap(d['DesYaw']-d['Yaw']):5.1f} R {d['Roll']:5.1f} P {d['Pitch']:5.1f}"
        if r: s+=f" | M {r['C11']} {r['C10']} {r['C12']} {r['C9']} ccw-cw {r['C11']+r['C10']-r['C12']-r['C9']:4d}"
        if q: s+=f" | Y {q[0]['Y']:6.1f} YOut {q[0]['YOut']:.3f}"
        if c: s+=f" | Alt {c[0]['Alt']:.2f} ThO {c[0]['ThO']:.3f}"
        if vb: s+=f" | VZ {vb[0]['VibeZ']:.1f} Clip {vb[0]['Clip']}"
        if rc: s+=f" | C1 {rc[-1]['C1']} C3 {rc[-1]['C3']} C4 {rc[-1]['C4']}"
        if g: s+=f" | GyrZ {' '.join(f'{x:.0f}' for x in g)}"
        print(s)
# anlik yayilim ortalamasi
def anlik(pp,a,b):
    w=yukle(pp); R=pen(w,"RCOU",a,b)
    sp=[max(d[c] for c in ("C9","C10","C11","C12"))-min(d[c] for c in ("C9","C10","C11","C12")) for d in R]
    ms=[np.mean([d[c] for d in R]) for c in ("C11","C10","C12","C9")]
    return np.mean(sp), max(ms)-min(ms), len(R)
for ad,pp,a,b in (("00:20 u3",ha:="ha.pkl",628,643),("W5","hb.pkl",141,147.5),("W6a","hb.pkl",189.5,194.4),("W6son","hb.pkl",197,202.37)):
    x=anlik(pp,a,b); print(ad,a,b,"anlik yayilim ort %.0f | ortalamalar yayilimi %.0f | n %d"%x)
