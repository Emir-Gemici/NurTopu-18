import sys, numpy as np
from ortak import *
v = yukle(sys.argv[1]); a0, b0, adim = float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
tR, R = dizi(v, "RCOU", ["C9","C10","C11","C12"])
tI, I = dizi(v, "RCIN", ["C1","C2","C3","C4","C5"])
tA, A = dizi(v, "ATT", ["DesRoll","Roll","DesPitch","Pitch","DesYaw","Yaw"])
tT, T = dizi(v, "RATE", ["ROut","POut","YOut","Y","YDes"])
tB, B = dizi(v, "BAT", ["Volt","Curr"])
tC, C = dizi(v, "CTUN", ["ThO","Alt","DAlt","BAlt"])
tV0, V0 = dizi(v, "VIBE", ["VibeX","VibeY","VibeZ","Clip"], lambda d: d["IMU"] == 0)
tV1, V1 = dizi(v, "VIBE", ["VibeX","VibeY","VibeZ","Clip"], lambda d: d["IMU"] == 1)
tM, M = dizi(v, "MOTB", ["FailFlags","ThrAvMx","ThLimit"])
print("  bas-son  | n  M1   M2   M3   M4  | yay CCW-CW Sag-Sol On-Ark | ROut  POut  YOut | yawHt YDes | C1dev C2dev C4dev C3 | Alt  ThO   A    V   | VX0  VY0  VZ0  VZ1  Clip0 Clip1 | FailF")
t = a0
while t < b0 - 1e-9:
    u = min(t + adim, b0)
    m = (tR >= t) & (tR < u)
    if m.sum() == 0: t = u; continue
    M1, M2, M3, M4 = R["C11"][m].mean(), R["C10"][m].mean(), R["C12"][m].mean(), R["C9"][m].mean()
    mt = (tT >= t) & (tT < u); ma = (tA >= t) & (tA < u); mi = (tI >= t) & (tI < u); mc = (tC >= t) & (tC < u); mb = (tB >= t) & (tB < u)
    mv = (tV0 >= t) & (tV0 < u); mv1 = (tV1 >= t) & (tV1 < u); mm = (tM >= t) & (tM < u)
    yh = yawfark(A["DesYaw"][ma], A["Yaw"][ma]).mean()
    ff = sorted(set(M["FailFlags"][mm].astype(int).tolist()))
    print(f"{t:5.1f}-{u:5.1f} | {m.sum():2d} {M1:4.0f} {M2:4.0f} {M3:4.0f} {M4:4.0f} | {max(M1,M2,M3,M4)-min(M1,M2,M3,M4):3.0f} {M1+M2-M3-M4:6.0f} {M1+M4-M2-M3:7.0f} {M1+M3-M2-M4:6.0f} | {T['ROut'][mt].mean():5.2f} {T['POut'][mt].mean():5.2f} {T['YOut'][mt].mean():5.2f} | {yh:5.1f} {T['YDes'][mt].mean():5.0f} | {np.abs(I['C1'][mi]-1500).max():5.0f} {np.abs(I['C2'][mi]-1502).max():5.0f} {np.abs(I['C4'][mi]-1500).max():5.0f} {I['C3'][mi].mean():4.0f} | {C['Alt'][mc].mean():4.2f} {C['ThO'][mc].mean():4.2f} {B['Curr'][mb].mean():5.1f} {B['Volt'][mb].mean():5.2f} | {V0['VibeX'][mv].mean():4.1f} {V0['VibeY'][mv].mean():4.1f} {V0['VibeZ'][mv].mean():4.1f} {V1['VibeZ'][mv1].mean():4.1f} {int(V0['Clip'][mv].max()):5d} {int(V1['Clip'][mv1].max()):5d} | {ff}")
    t = u
