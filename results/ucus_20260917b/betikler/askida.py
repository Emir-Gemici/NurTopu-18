import sys, numpy as np
from ortak import *
def analiz(pkl, pencereler, sert=True):
    v = yukle(pkl)
    tR, R = dizi(v, "RCOU", ["C9","C10","C11","C12"])
    tI, I = dizi(v, "RCIN", ["C1","C2","C3","C4"])
    tA, A = dizi(v, "ATT", ["DesRoll","Roll","DesPitch","Pitch","DesYaw","Yaw"])
    tT, T = dizi(v, "RATE", ["ROut","POut","YOut","R","P","Y","RDes","PDes","YDes"])
    tB, B = dizi(v, "BAT", ["Volt","Curr"])
    tC, C = dizi(v, "CTUN", ["ThO","Alt","DAlt"])
    tV0, V0 = dizi(v, "VIBE", ["VibeX","VibeY","VibeZ","Clip"], lambda d: d["IMU"] == 0)
    tV1, V1 = dizi(v, "VIBE", ["VibeX","VibeY","VibeZ","Clip"], lambda d: d["IMU"] == 1)
    print(f"{'pencere':>16} {'n':>4} | {'M1':>5} {'M2':>5} {'M3':>5} {'M4':>5} | {'yayil':>5} {'CCW-CW':>6} {'Sag-Sol':>7} {'On-Arka':>7} | T: {'M1':>5} {'M2':>5} {'M3':>5} {'M4':>5} | {'ROut':>6} {'POut':>6} {'YOut':>6} | {'yawHt':>6} {'|RPht|':>6} | {'ThO':>5} {'A':>5} {'V':>5} | VibX0 VibY0 VibZ0 VibZmax Clip0 Clip1")
    for ad, a, b in pencereler:
        m = (tR >= a) & (tR <= b)
        tt = tR[m]
        M1, M2, M3, M4 = R["C11"][m], R["C10"][m], R["C12"][m], R["C9"][m]
        c1 = ornek(tI, I["C1"], tt); c2 = ornek(tI, I["C2"], tt); c3 = ornek(tI, I["C3"], tt); c4 = ornek(tI, I["C4"], tt)
        k = np.ones(len(tt), bool)
        if sert:
            k = (abs(c1-1500) <= 30) & (abs(c2-1502) <= 30) & (abs(c4-1500) <= 30) & (abs(c3-1500) < 100)
        k &= (np.minimum.reduce([M1,M2,M3,M4]) > 1100)
        if k.sum() == 0:
            print(f"{ad:>16} n=0"); continue
        M1, M2, M3, M4, tt = M1[k], M2[k], M3[k], M4[k], tt[k]
        mm = [M1.mean(), M2.mean(), M3.mean(), M4.mean()]
        Tm = [itki(M1).mean(), itki(M2).mean(), itki(M3).mean(), itki(M4).mean()]
        ro = ornek(tT, T["ROut"], tt); po = ornek(tT, T["POut"], tt); yo = ornek(tT, T["YOut"], tt)
        yh = yawfark(ornek(tA, A["DesYaw"], tt), ornek(tA, A["Yaw"], tt))
        rph = np.hypot(ornek(tA, A["DesRoll"], tt) - ornek(tA, A["Roll"], tt), ornek(tA, A["DesPitch"], tt) - ornek(tA, A["Pitch"], tt))
        th = ornek(tC, C["ThO"], tt); cur = ornek(tB, B["Curr"], tt); vol = ornek(tB, B["Volt"], tt)
        mv = (tV0 >= a) & (tV0 <= b); mv1 = (tV1 >= a) & (tV1 <= b)
        print(f"{ad:>16} {k.sum():4d} | {mm[0]:5.0f} {mm[1]:5.0f} {mm[2]:5.0f} {mm[3]:5.0f} | {max(mm)-min(mm):5.0f} {mm[0]+mm[1]-mm[2]-mm[3]:6.0f} {mm[0]+mm[3]-mm[1]-mm[2]:7.0f} {mm[0]+mm[2]-mm[1]-mm[3]:7.0f} | T: {Tm[0]:5.3f} {Tm[1]:5.3f} {Tm[2]:5.3f} {Tm[3]:5.3f} | {ro.mean():6.3f} {po.mean():6.3f} {yo.mean():6.3f} | {yh.mean():6.1f} {rph.mean():6.2f} | {th.mean():5.3f} {cur.mean():5.1f} {vol.mean():5.2f} | {V0['VibeX'][mv].mean():5.1f} {V0['VibeY'][mv].mean():5.1f} {V0['VibeZ'][mv].mean():5.1f} {V0['VibeZ'][mv].max():7.1f} {int(V0['Clip'][mv].min())}-{int(V0['Clip'][mv].max())} {int(V1['Clip'][mv1].min())}-{int(V1['Clip'][mv1].max())}")
if __name__ == "__main__":
    import json
    pkl = sys.argv[1]; sert = sys.argv[2] == "sert"
    pen = [(p.split(":")[0], float(p.split(":")[1]), float(p.split(":")[2])) for p in sys.argv[3:]]
    analiz(pkl, pen, sert)
