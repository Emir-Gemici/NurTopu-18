import pickle, sys
v = pickle.load(open("tum.pkl","rb"))
a,b = float(sys.argv[1]), float(sys.argv[2])
ev = []
for k in ["RCIN","ATT","RATE","RCOU","CTUN","PSCN","PSCE","PSCD","MOTB","MODE","EV","ERR","ARM","MSG","BAT","VIBE"]:
    for t,d in v[k]:
        if a<=t<=b and d.get("IMU",0)==0: ev.append((t,k,d))
ev.sort(key=lambda r:r[0])
def fm(k,d):
    if k=="RCIN": return f"C1 {d['C1']} C2 {d['C2']} C3 {d['C3']} C4 {d['C4']} C5 {d['C5']} C6 {d['C6']}"
    if k=="ATT": return f"DR {d['DesRoll']:.1f} R {d['Roll']:.1f} DP {d['DesPitch']:.1f} P {d['Pitch']:.1f} DY {d['DesYaw']:.1f} Y {d['Yaw']:.1f}"
    if k=="RATE": return f"RDes {d['RDes']:.1f} R {d['R']:.1f} ROut {d['ROut']:.3f} | PDes {d['PDes']:.1f} P {d['P']:.1f} POut {d['POut']:.3f} | YDes {d['YDes']:.1f} Y {d['Y']:.1f} YOut {d['YOut']:.3f} | A {d['A']:.2f} AOut {d['AOut']:.3f}"
    if k=="RCOU": return f"M4 {d['C9']} M2 {d['C10']} M1 {d['C11']} M3 {d['C12']}"
    if k=="CTUN": return f"ThI {d['ThI']:.3f} ThO {d['ThO']:.3f} ThH {d['ThH']:.3f} DAlt {d['DAlt']:.2f} Alt {d['Alt']:.2f} BAlt {d['BAlt']:.2f} DCRt {d['DCRt']} CRt {d['CRt']}"
    if k in ("PSCN","PSCE","PSCD"): return " ".join(f"{kk} {vv:.2f}" for kk,vv in d.items() if kk!="TimeUS")
    if k=="MOTB": return f"LiftMax {d['LiftMax']:.2f} ThLimit {d['ThLimit']:.2f} ThrAvMx {d['ThrAvMx']:.3f} ThrOut {d['ThrOut']:.3f} FF {d['FailFlags']}"
    if k=="BAT": return f"V {d['Volt']:.2f} A {d['Curr']:.1f}"
    if k=="VIBE": return f"VX {d['VibeX']:.1f} VY {d['VibeY']:.1f} VZ {d['VibeZ']:.1f} Clip {d['Clip']}"
    return str({kk:vv for kk,vv in d.items() if kk!="TimeUS"})
for t,k,d in ev:
    print(f"{t:.3f} {k:5s} {fm(k,d)}")
