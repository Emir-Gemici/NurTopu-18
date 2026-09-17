import sys,pickle,numpy as np
v=pickle.load(open(sys.argv[1],"rb"))
a,b,st=float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
def pen(tip,a,b,**kw): return [d for d in v[tip] if a<=d["t"]<=b and all(d.get(k)==x for k,x in kw.items())]
t=a
while t<b:
    e=t+st
    C=pen("CTUN",t,e); RC=pen("RCIN",t,e); R=pen("RCOU",t,e); A=pen("ATT",t,e); V0=pen("VIBE",t,e,IMU=0); B=pen("BAT",t,e); BA=pen("BARO",t,e,I=0)
    if C and RC and R:
        m=[np.mean([d[c] for d in R]) for c in ("C11","C10","C12","C9")]
        print(f"{t:6.1f} Alt {np.mean([d['Alt'] for d in C]):5.2f} BAlt {np.mean([d['BAlt'] for d in C]):5.2f} ThI {np.mean([d['ThI'] for d in C]):.2f} ThO {np.mean([d['ThO'] for d in C]):.3f} ThH {np.mean([d['ThH'] for d in C]):.3f} | C1 {np.mean([d['C1'] for d in RC]):4.0f} C2 {np.mean([d['C2'] for d in RC]):4.0f} C3 {np.mean([d['C3'] for d in RC]):4.0f} C4 {np.mean([d['C4'] for d in RC]):4.0f} C5 {RC[-1]['C5']} C6 {RC[-1]['C6']} | M {m[0]:4.0f} {m[1]:4.0f} {m[2]:4.0f} {m[3]:4.0f} | R {np.mean([d['Roll'] for d in A]):5.1f} P {np.mean([d['Pitch'] for d in A]):5.1f} Rmx {max(abs(d['Roll']) for d in A):5.1f} Pmx {max(abs(d['Pitch']) for d in A):5.1f} | VZ {np.mean([d['VibeZ'] for d in V0]) if V0 else float('nan'):4.1f} Clip {V0[-1]['Clip'] if V0 else '-'} | I {np.mean([d['Curr'] for d in B]):5.1f}")
    t=e
