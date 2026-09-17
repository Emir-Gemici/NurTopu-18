from c_ort import *
import sys, numpy as np
v=yukle(); a,b=float(sys.argv[1]),float(sys.argv[2])
I=pen(v,"IMU",a,b)
print("IMU dt (I0):", sorted(set(np.round(np.diff([d['t'] for d in I if d['I']==0]),3)))[:10])
for d in I:
    g=[math.degrees(d[k]) for k in ("GyrX","GyrY","GyrZ")]; ac=[d[k] for k in ("AccX","AccY","AccZ")]
    print(f"IMU {d['t']:.3f} I{d['I']} G {g[0]:7.1f} {g[1]:7.1f} {g[2]:7.1f} A {ac[0]:6.2f} {ac[1]:6.2f} {ac[2]:6.2f} |a| {math.sqrt(sum(x*x for x in ac)):5.2f} EG {d.get('EG')} EA {d.get('EA')} GH {d.get('GH')} AH {d.get('AH')}")
for d in pen(v,"RATE",a,b): print(f"RATE {d['t']:.3f} RDes {d['RDes']:7.1f} R {d['R']:7.1f} ROut {d['ROut']:6.3f} PDes {d['PDes']:7.1f} P {d['P']:7.1f} POut {d['POut']:6.3f} YDes {d['YDes']:6.1f} Y {d['Y']:6.1f} YOut {d['YOut']:6.3f} ADes {d.get('ADes',0):.1f} A {d.get('A',0):.1f} AOut {d.get('AOut',0):.3f}")
for d in pen(v,"ATT",a,b): print(f"ATT {d['t']:.3f} DesR {d['DesRoll']:6.1f} R {d['Roll']:6.1f} DesP {d['DesPitch']:6.1f} P {d['Pitch']:6.1f} DesY {d['DesYaw']:6.1f} Y {d['Yaw']:6.1f}")
for d in pen(v,"RCOU",a,b):
    M1,M2,M3,M4=d['C11'],d['C10'],d['C12'],d['C9']; T=(M1+M2+M3+M4)/4
    R=(M2+M3-M1-M4)/4; Pp=(M1+M3-M2-M4)/4; Y=(M1+M2-M3-M4)/4
    print(f"RCOU {d['t']:.3f} M1 {M1} M2 {M2} M3 {M3} M4 {M4} | T {T:.0f} Rmix {R:.0f} Pmix {Pp:.0f} Ymix {Y:.0f}")
for d in pen(v,"MOTB",a,b): print("MOTB", round(d['t'],3), {k:round(x,3) for k,x in d.items() if k not in ('TimeUS','t')})
for d in pen(v,"CTRL",a,b): print("CTRL", round(d['t'],3), {k:round(x,3) for k,x in d.items() if k not in ('TimeUS','t')})
for d in pen(v,"BAT",a,b): print(f"BAT {d['t']:.3f} V {d['Volt']:.2f} VR {d['VoltR']:.2f} I {d['Curr']:.1f} Res {d.get('Res')}")
for d in pen(v,"VIBE",a,b): print(f"VIBE {d['t']:.3f} IMU{d['IMU']} {d['VibeX']:.1f} {d['VibeY']:.1f} {d['VibeZ']:.1f} Clip {d['Clip']}")
for d in pen(v,"CTUN",a,b): print(f"CTUN {d['t']:.3f} ThI {d['ThI']:.3f} ThO {d['ThO']:.3f} ThH {d['ThH']:.3f} DAlt {d['DAlt']:.2f} Alt {d['Alt']:.2f} BAlt {d['BAlt']:.2f} CRt {d['CRt']:.0f} DCRt {d['DCRt']:.0f}")
for d in pen(v,"BARO",a,b): print(f"BARO {d['t']:.3f} I{d['I']} Alt {d['Alt']:.2f} Press {d['Press']:.1f} CRt {d['CRt']:.2f}")
for d in pen(v,"RCIN",a,b): print(f"RCIN {d['t']:.3f} {d['C1']} {d['C2']} {d['C3']} {d['C4']} {d['C5']} {d['C6']}")
for d in pen(v,"MAG",a,b): print(f"MAG {d['t']:.3f} I{d['I']} H {d['Health']} S {d['S']/1e6:.3f} {d['MagX']:.0f} {d['MagY']:.0f} {d['MagZ']:.0f}")
for d in pen(v,"GPS",a-0.5,b+4.5): print(f"GPS {d['t']:.3f} St {d['Status']} NS {d['NSats']} Alt {d['Alt']:.2f} Spd {d['Spd']:.2f} VZ {d['VZ']:.2f}")
for d in pen(v,"POWR",a,b): print("POWR", round(d['t'],3), d['Vcc'], d['VServo'], d['Flags'], d.get('AccFlags'))
for d in pen(v,"PSCN",a,b): print("PSCN", round(d['t'],3), {k:round(x,2) for k,x in d.items() if k not in ('TimeUS','t')})
for d in pen(v,"PSCE",a,b): print("PSCE", round(d['t'],3), {k:round(x,2) for k,x in d.items() if k not in ('TimeUS','t')})
for d in pen(v,"PSCD",a,b): print("PSCD", round(d['t'],3), {k:round(x,2) for k,x in d.items() if k not in ('TimeUS','t')})
