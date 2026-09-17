from c_ort import *
import numpy as np, sys
pp=sys.argv[1]; a0,a1,st=float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
v=yukle(pp)
def wrap(x): return (x+180)%360-180
print("kutu        | M1   M2   M3   M4  | T    Rmix Pmix Ymix | Roll  Pitch YawErr | ROut  POut  YOut | C1ort C1min C1max C2ort C3ort C4ort | VN VE | Alt | VibeZ | n")
b=a0
while b<a1-1e-9:
    e=min(b+st,a1)
    R=pen(v,"RCOU",b,e)
    if not R: b=e; continue
    M=np.array([[d['C11'],d['C10'],d['C12'],d['C9']] for d in R],float)
    m=M.mean(0); T=m.mean(); Rm=(m[1]+m[2]-m[0]-m[3])/4; Pm=(m[0]+m[2]-m[1]-m[3])/4; Ym=(m[0]+m[1]-m[2]-m[3])/4
    A=pen(v,"ATT",b,e); Q=pen(v,"RATE",b,e); RC=pen(v,"RCIN",b,e); N=pen(v,"PSCN",b,e); E=pen(v,"PSCE",b,e); C=pen(v,"CTUN",b,e)
    VB=[d for d in pen(v,"VIBE",b,e) if d['IMU']==0]
    mo=lambda L,k: np.mean([d[k] for d in L]) if L else float('nan')
    print(f"{b:6.1f}-{e:6.1f} | {m[0]:4.0f} {m[1]:4.0f} {m[2]:4.0f} {m[3]:4.0f} | {T:4.0f} {Rm:4.0f} {Pm:4.0f} {Ym:4.0f} | {mo(A,'Roll'):5.2f} {mo(A,'Pitch'):5.2f} {np.mean([wrap(d['DesYaw']-d['Yaw']) for d in A]):5.1f} | {mo(Q,'ROut'):5.3f} {mo(Q,'POut'):5.3f} {mo(Q,'YOut'):5.3f} | {mo(RC,'C1'):5.0f} {min(d['C1'] for d in RC)} {max(d['C1'] for d in RC)} {mo(RC,'C2'):5.0f} {mo(RC,'C3'):5.0f} {mo(RC,'C4'):5.0f} | {mo(N,'VN'):5.2f} {mo(E,'VE'):5.2f} | {mo(C,'Alt'):4.2f} | {mo(VB,'VibeZ'):4.1f} | {len(R)}")
    b=e
