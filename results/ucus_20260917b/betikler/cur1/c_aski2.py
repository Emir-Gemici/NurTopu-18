from c_ort import *
import numpy as np, sys
pp=sys.argv[1]; v=yukle(pp); W=2.0
# ucuslar: (NOT_LANDED t, bitis t)
ucuslar=[tuple(map(float,x.split(":"))) for x in sys.argv[2:]]
def agl_ref(t0):
    C=pen(v,"CTUN",t0-2.0,t0-0.05); return float(np.mean([d['Alt'] for d in C])) if C else float('nan')
for t0,t1 in ucuslar:
    ref=agl_ref(t0)
    print(f"== ucus NOT_LANDED {t0} -> {t1}  yer referansi Alt {ref:.2f}")
    a=t0+0.8
    while a+W<=t1:
        b=a+W
        RC=pen(v,"RCIN",a,b); C=pen(v,"CTUN",a,b)
        ok = RC and C and all(abs(d["C1"]-1500)<45 and abs(d["C2"]-1502)<45 and abs(d["C4"]-1500)<45 and 1400<=d['C3']<=1600 for d in RC)
        if ok:
            I=[d for d in pen(v,"IMU",a,b) if d['I']==0]
            gx=np.degrees([d['GyrX'] for d in I]); gy=np.degrees([d['GyrY'] for d in I])
            Q=pen(v,"RATE",a,b); B=pen(v,"BAT",a,b); VB=[d for d in pen(v,"VIBE",a,b) if d['IMU']==0]
            M=np.array([[d['C11'],d['C10'],d['C12'],d['C9']] for d in pen(v,"RCOU",a,b)],float)
            spread=np.mean(M.max(1)-M.min(1))
            print(f"{a:7.1f}-{b:7.1f} AGL {np.mean([d['Alt'] for d in C])-ref:5.2f} ThO {np.mean([d['ThO'] for d in C]):.3f} V {np.mean([d['Volt'] for d in B]):5.2f} I {np.mean([d['Curr'] for d in B]):5.1f} | gyrRMS X {np.std(gx):5.1f} Y {np.std(gy):5.1f} | rateErrRMS R {np.sqrt(np.mean([(d['RDes']-d['R'])**2 for d in Q])):5.1f} P {np.sqrt(np.mean([(d['PDes']-d['P'])**2 for d in Q])):5.1f} |ROut| {np.mean([abs(d['ROut']) for d in Q]):.3f} | VIBE {np.mean([d['VibeX'] for d in VB]):4.1f} {np.mean([d['VibeY'] for d in VB]):4.1f} {np.mean([d['VibeZ'] for d in VB]):4.1f} | anlikYayilim {spread:4.0f}")
        a+=0.5
