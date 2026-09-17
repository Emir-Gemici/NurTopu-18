import numpy as np, math
from ortak import *
b = yukle("b.pkl")
tA, A = dizi(b, "ATT", ["DesYaw","Yaw"])
tT, T = dizi(b, "RATE", ["YOut","Y","YDes"])
tR, R = dizi(b, "RCOU", ["C9","C10","C11","C12"])
tI, I = dizi(b, "IMU", ["GyrZ"], lambda d: d["I"] == 0)
tV, V = dizi(b, "VIBE", ["VibeX","VibeY","VibeZ"], lambda d: d["IMU"] == 0)
tN, N = dizi(b, "RCIN", ["C1","C4"])
for p, q in ((188.8, 190.6), (193.6, 195.8)):
    print(f"--- {p}-{q}")
    for t, (m4, m2, m1, m3) in zip(tR, zip(R["C9"], R["C10"], R["C11"], R["C12"])):
        if p <= t <= q:
            gz = I["GyrZ"][(tI > t - 0.1) & (tI <= t)]
            print(f"{t:7.2f} M1..M4 {m1:.0f} {m2:.0f} {m3:.0f} {m4:.0f} CCW-CW {m1+m2-m3-m4:+5.0f} | YOut {ornek(tT,T['YOut'],t):+.3f} Y {ornek(tT,T['Y'],t):+6.1f} YDes {ornek(tT,T['YDes'],t):+6.1f} yawHt {yawfark(ornek(tA,A['DesYaw'],t), ornek(tA,A['Yaw'],t)):+5.1f} | GyrZ(son0.1s) {np.round(np.degrees(gz),0)} | VibY {ornek(tV,V['VibeY'],t):.1f} VibZ {ornek(tV,V['VibeZ'],t):.1f} | C1 {ornek(tN,N['C1'],t):.0f} C4 {ornek(tN,N['C4'],t):.0f}")
