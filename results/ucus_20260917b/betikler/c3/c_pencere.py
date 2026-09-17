import sys, pickle, math
import numpy as np
pp=sys.argv[1]
v=pickle.load(open(pp,"rb"))
P={d["Name"]:d["Value"] for d in v["PARM"]}
def pen(tip,a,b,**kw):
    return [d for d in v.get(tip,[]) if d["t"] is not None and a<=d["t"]<=b and all(d.get(k)==x for k,x in kw.items())]
def wrap(x): return (x+180)%360-180
print("ARM/EV/MODE:")
for tip in ("ARM","EV","MODE"):
    for d in v[tip]:
        if tip=="EV" and d["Id"] not in (10,11,15,17,18,28): continue
        print(f"  {d['t']:.3f} {tip} {({k:d[k] for k in d if k not in ('t','TimeUS')})}")
def seg_ozet(a,b,etiket):
    C=pen("CTUN",a,b); B=pen("BAT",a,b); A=pen("ATT",a,b); Q=pen("RATE",a,b); R=pen("RCOU",a,b); RC=pen("RCIN",a,b)
    V0=pen("VIBE",a,b,IMU=0); V1=pen("VIBE",a,b,IMU=1); I0=pen("IMU",a,b,I=0)
    if len(C)<5: print(etiket,"yetersiz"); return
    ms=[np.mean([d[c] for d in R]) for c in ("C11","C10","C12","C9")]
    tho=[d["ThO"] for d in C]
    rer=[d["DesRoll"]-d["Roll"] for d in A]; per=[d["DesPitch"]-d["Pitch"] for d in A]; yer=[wrap(d["DesYaw"]-d["Yaw"]) for d in A]
    gx=np.array([math.degrees(d["GyrX"]) for d in I0]); gy=np.array([math.degrees(d["GyrY"]) for d in I0])
    print(f"{etiket} {a:.2f}-{b:.2f} ({b-a:.1f} s) Alt {min(d['Alt'] for d in C):.2f}-{max(d['Alt'] for d in C):.2f} | ThO ort {np.mean(tho):.3f} p50 {np.median(tho):.3f} ThH {np.mean([d['ThH'] for d in C]):.3f} | V {np.mean([d['Volt'] for d in B]):.2f} I {np.mean([d['Curr'] for d in B]):.1f}")
    print(f"   VIBE0 ort X/Y/Z {np.mean([d['VibeX'] for d in V0]):.1f}/{np.mean([d['VibeY'] for d in V0]):.1f}/{np.mean([d['VibeZ'] for d in V0]):.1f} p95 {np.percentile([d['VibeX'] for d in V0],95):.1f}/{np.percentile([d['VibeY'] for d in V0],95):.1f}/{np.percentile([d['VibeZ'] for d in V0],95):.1f} maks Z {max(d['VibeZ'] for d in V0):.1f} | Clip0 {V0[0]['Clip']}->{V0[-1]['Clip']} Clip1 {V1[0]['Clip']}->{V1[-1]['Clip']}")
    print(f"   tutum hata RMS roll/pitch/yaw {np.sqrt(np.mean(np.square(rer))):.2f}/{np.sqrt(np.mean(np.square(per))):.2f}/{np.sqrt(np.mean(np.square(yer))):.1f} deg | roll std {np.std([d['Roll'] for d in A]):.2f} pitch std {np.std([d['Pitch'] for d in A]):.2f} | RATE hata RMS R/P {np.sqrt(np.mean([(d['RDes']-d['R'])**2 for d in Q])):.1f}/{np.sqrt(np.mean([(d['PDes']-d['P'])**2 for d in Q])):.1f} deg/s |ROut| p90 {np.percentile([abs(d['ROut']) for d in Q],90):.3f} |POut| p90 {np.percentile([abs(d['POut']) for d in Q],90):.3f}")
    print(f"   IMU0 Gyr RMS X/Y {np.sqrt(np.mean((gx-gx.mean())**2)):.1f}/{np.sqrt(np.mean((gy-gy.mean())**2)):.1f} deg/s (n {len(I0)}) | motor ort M1 {ms[0]:.0f} M2 {ms[1]:.0f} M3 {ms[2]:.0f} M4 {ms[3]:.0f} yayilim {max(ms)-min(ms):.0f} CCW-CW {ms[0]+ms[1]-ms[2]-ms[3]:+.0f} maks motor {max(max(d[c] for c in ('C9','C10','C11','C12')) for d in R)}")
    print(f"   RCIN C1 {min(d['C1'] for d in RC)}-{max(d['C1'] for d in RC)} C2 {min(d['C2'] for d in RC)}-{max(d['C2'] for d in RC)} C3 {min(d['C3'] for d in RC)}-{max(d['C3'] for d in RC)} C4 {min(d['C4'] for d in RC)}-{max(d['C4'] for d in RC)}")
def temiz(a,b,tol=30,minsure=1.9):
    RC=pen("RCIN",a,b)
    tr={"C1":P["RC1_TRIM"],"C2":P["RC2_TRIM"],"C4":P["RC4_TRIM"]}
    ok=[d["t"] for d in RC if all(abs(d[c]-tr[c])<=tol for c in tr) and abs(d["C3"]-1500)<100]
    seg=[];s=None;p=None
    for t in ok:
        if s is None: s=t
        elif t-p>0.15: seg.append((s,p)); s=t
        p=t
    if s is not None: seg.append((s,p))
    return [x for x in seg if x[1]-x[0]>=minsure]
if __name__=="__main__":
    for i in range(2,len(sys.argv),3):
        a,b,et=float(sys.argv[i]),float(sys.argv[i+1]),sys.argv[i+2]
        seg_ozet(a,b,et)
        for s in temiz(a,b): seg_ozet(s[0],s[1],"  temiz("+et+")")
