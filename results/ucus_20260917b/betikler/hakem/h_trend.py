from h_ortak import *
import math, sys
import numpy as np
dosya=sys.argv[1]; t0,t1,adim=float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
v=yukle(dosya)
def T(p): a=max(0.0,(p-1150)/800.0); return 0.35*a+0.65*a*a
def ort(L): return float(np.mean(L)) if L else float('nan')
def wrap(x): return (x+180)%360-180
print(" kutu      | M1   M2   M3   M4  | CCW-CW yayil | Tccw-cw Tsum TsumV2 | YawErr YOut |ROut| |POut| | Roll  Pitch | VZ  VY | V     I    W   ThO | C1dev C4 | n")
b=t0
while b<t1-1e-9:
    e=min(b+adim,t1)
    R=pen(v,"RCOU",b,e); A=pen(v,"ATT",b,e); Q=pen(v,"RATE",b,e); B=pen(v,"BAT",b,e); VI=pen(v,"VIBE",b,e,None); C=pen(v,"CTUN",b,e); RC=pen(v,"RCIN",b,e)
    VI=[d for d in VI if d["IMU"]==0]
    if not R: b=e; continue
    m=[ort([d[c] for d in R]) for c in ("C11","C10","C12","C9")]
    ts=[ [T(d[c]) for c in ("C11","C10","C12","C9")] for d in R]
    tccw=ort([x[0]+x[1]-x[2]-x[3] for x in ts]); tsum=ort([sum(x) for x in ts])
    V=ort([d["Volt"] for d in B]); I=ort([d["Curr"] for d in B])
    # TsumV2: komut itkisi * (V/15)^2 -> fiziksel itki vekili
    tv=ort([sum(x) for x in ts])*(V/15.0)**2
    ye=ort([wrap(d["DesYaw"]-d["Yaw"]) for d in A])
    print(f"{b:6.1f}-{e:6.1f} | {m[0]:4.0f} {m[1]:4.0f} {m[2]:4.0f} {m[3]:4.0f} | {m[0]+m[1]-m[2]-m[3]:5.0f} {max(m)-min(m):4.0f} | {tccw:6.3f} {tsum:5.3f} {tv:5.3f} | {ye:5.1f} {ort([d['YOut'] for d in Q]):5.3f} {ort([abs(d['ROut']) for d in Q]):5.3f} {ort([abs(d['POut']) for d in Q]):5.3f} | {ort([d['Roll'] for d in A]):5.2f} {ort([d['Pitch'] for d in A]):5.2f} | {ort([d['VibeZ'] for d in VI]):4.1f} {ort([d['VibeY'] for d in VI]):4.1f} | {V:5.2f} {I:5.1f} {V*I:4.0f} {ort([d['ThO'] for d in C]):5.3f} | {ort([abs(d['C1']-1500) for d in RC]):4.0f} {ort([d['C4'] for d in RC]):4.0f} | {len(R)}")
    b=e
