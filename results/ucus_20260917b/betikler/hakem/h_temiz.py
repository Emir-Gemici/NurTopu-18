from h_ortak import *
import numpy as np, math
from h_fft import analiz
v=yukle("ha.pkl"); P=parm(v)
tr={"C1":P["RC1_TRIM"],"C2":P["RC2_TRIM"],"C4":P["RC4_TRIM"]}
R=[d for d in v["RCIN"] if 617<=d["t"]<=647.8]
ok=[d["t"] for d in R if all(abs(d[c]-tr[c])<=30 for c in tr) and abs(d["C3"]-1500)<100]
# ardisik temiz bolumler
seg=[];s=None;p=None
for t in ok:
    if s is None: s=t
    elif t-p>0.15: seg.append((s,p)); s=t
    p=t
if s is not None: seg.append((s,p))
seg=[x for x in seg if x[1]-x[0]>=1.9]
print("00:20 temiz (cubuklar trim +-10, gaz olu bantta) bolumler >=1.9 s (+-30):", [(round(a,1),round(b,1)) for a,b in seg])
for a,b in seg:
    C=pen(v,"CTUN",a,b); B=pen(v,"BAT",a,b); VI=[d for d in pen(v,"VIBE",a,b) if d["IMU"]==0]
    print(f" {a:.1f}-{b:.1f} Alt {min(d['Alt'] for d in C):.2f}-{max(d['Alt'] for d in C):.2f} CRt ort {np.mean([d['CRt'] for d in C]):.0f} ThO {np.mean([d['ThO'] for d in C]):.3f} V {np.mean([d['Volt'] for d in B]):.2f} I {np.mean([d['Curr'] for d in B]):.1f} VZ {np.mean([d['VibeZ'] for d in VI]):.1f} VX {np.mean([d['VibeX'] for d in VI]):.1f} VY {np.mean([d['VibeY'] for d in VI]):.1f}")
    analiz("  00:20 temiz","ha.pkl",a,b)
w=yukle("hb.pkl")
for a,b in ((143.9,146.9),(196.4,198.4)):
    C=pen(w,"CTUN",a,b); B=pen(w,"BAT",a,b); VI=[d for d in pen(w,"VIBE",a,b) if d["IMU"]==0]
    print(f"02:50 {a}-{b} Alt {min(d['Alt'] for d in C):.2f}-{max(d['Alt'] for d in C):.2f} CRt ort {np.mean([d['CRt'] for d in C]):.0f} ThO {np.mean([d['ThO'] for d in C]):.3f} V {np.mean([d['Volt'] for d in B]):.2f} I {np.mean([d['Curr'] for d in B]):.1f} VZ {np.mean([d['VibeZ'] for d in VI]):.1f} VX {np.mean([d['VibeX'] for d in VI]):.1f} VY {np.mean([d['VibeY'] for d in VI]):.1f}")
