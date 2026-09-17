import numpy as np
from ortak import *
a = yukle("a.pkl"); b = yukle("b.pkl")
def ort(v, p, q):
    L = [d for d in v["RCOU"] if p <= d["t"] < q]
    M = np.array([[d["C11"], d["C10"], d["C12"], d["C9"]] for d in L], float)
    return M.mean(0), len(L)
def pairs(M):
    M1, M2, M3, M4 = M
    return np.array([M1+M2-M3-M4, -M1+M2+M3-M4, M1-M2+M3-M4])  # yaw CCW fazla, roll sol fazla, pitch on fazla
for ad, (p1, q1), (p2, q2) in (("basamak1", (188.8, 189.4), (189.8, 190.6)), ("basamak2", (193.6, 194.5), (194.95, 195.8)), ("rampa", (195.0, 197.0), (201.4, 202.37))):
    A1, n1 = ort(b, p1, q1); A2, n2 = ort(b, p2, q2)
    d = pairs(A2) - pairs(A1)
    print(f"{ad}: once {p1}-{q1} (n={n1}) {np.round(A1)} sonra {p2}-{q2} (n={n2}) {np.round(A2)} | fark M1..M4 {np.round(A2-A1)} | yaw(CCW-CW) {d[0]:+.0f}  roll(sol-sag) {d[1]:+.0f}  pitch(on-arka) {d[2]:+.0f} us")
def vib(v, p, q, I=0):
    L = [d for d in v["VIBE"] if d["IMU"] == I and p <= d["t"] < q]
    return np.round([np.mean([d["VibeX"] for d in L]), np.mean([d["VibeY"] for d in L]), np.mean([d["VibeZ"] for d in L])], 2), len(L)
print("Yerde 1100 us rolanti VIBE (X,Y,Z) IMU0:")
for ad, v, p, q in (("a 599.2-601.9", a, 599.2, 601.9), ("b 116.2-117.9", b, 116.2, 117.9), ("b 123.2-124.1", b, 123.2, 124.1), ("b 137.2-138.9", b, 137.2, 138.9), ("b 184.6-185.4", b, 184.6, 185.4)):
    r = [d for d in v["RCOU"] if p <= d["t"] < q]
    print(f"  {ad}: RCOU aralik {min(min(d['C9'],d['C10'],d['C11'],d['C12']) for d in r)}-{max(max(d['C9'],d['C10'],d['C11'],d['C12']) for d in r)} VIBE {vib(v,p,q)}")
print("Askida VIBE (X,Y,Z) IMU0:")
for ad, v, p, q in (("a F3 622.5-647.8", a, 622.5, 647.8), ("a 637-643", a, 637, 643), ("b W5 141.5-148", b, 141.5, 148), ("b W6 188.5-202.37", b, 188.5, 202.37)):
    print(f"  {ad}: {vib(v,p,q)}")
