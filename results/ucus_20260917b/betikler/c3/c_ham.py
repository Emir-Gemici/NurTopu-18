import sys,pickle,math
v=pickle.load(open(sys.argv[1],"rb")); a,b=float(sys.argv[2]),float(sys.argv[3])
def pen(tip,**kw): return [d for d in v[tip] if a<=d["t"]<=b and all(d.get(k)==x for k,x in kw.items())]
ev=[]
for d in pen("IMU",I=0):
    ev.append((d["t"],f"IMU0 Gyr {math.degrees(d['GyrX']):7.1f} {math.degrees(d['GyrY']):7.1f} {math.degrees(d['GyrZ']):7.1f} Acc {d['AccX']:6.2f} {d['AccY']:6.2f} {d['AccZ']:6.2f} |a| {math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2):5.2f}"))
for d in pen("ATT"): ev.append((d["t"],f"ATT DR {d['DesRoll']:6.1f} R {d['Roll']:6.1f} DP {d['DesPitch']:6.1f} P {d['Pitch']:6.1f} DY {d['DesYaw']:6.1f} Y {d['Yaw']:6.1f}"))
for d in pen("RCOU"): ev.append((d["t"],f"RCOU M1 {d['C11']} M2 {d['C10']} M3 {d['C12']} M4 {d['C9']}"))
for d in pen("RCIN"): ev.append((d["t"],f"RCIN C1 {d['C1']} C2 {d['C2']} C3 {d['C3']} C4 {d['C4']} C5 {d['C5']} C6 {d['C6']}"))
for d in pen("VIBE"): ev.append((d["t"],f"VIBE{d['IMU']} {d['VibeX']:.1f}/{d['VibeY']:.1f}/{d['VibeZ']:.1f} Clip {d['Clip']}"))
for d in pen("CTUN"): ev.append((d["t"],f"CTUN ThI {d['ThI']:.3f} ThO {d['ThO']:.3f} Alt {d['Alt']:.2f} BAlt {d['BAlt']:.2f} CRt {d['CRt']}"))
for d in pen("RATE"): ev.append((d["t"],f"RATE RDes {d['RDes']:.1f} R {d['R']:.1f} ROut {d['ROut']:.3f} PDes {d['PDes']:.1f} P {d['P']:.1f} POut {d['POut']:.3f}"))
flt=sys.argv[4].split(",") if len(sys.argv)>4 else None
for t,s in sorted(ev):
    if flt and not any(s.startswith(f) for f in flt): continue
    print(f"{t:8.3f} {s}")
