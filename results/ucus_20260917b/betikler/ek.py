import numpy as np, math
from ortak import *
a = yukle("a.pkl"); b = yukle("b.pkl")
for ad, v in (("a", a), ("b", b)):
    print(ad, "MOTB FailFlags benzersiz:", sorted(set(int(d["FailFlags"]) for d in v["MOTB"])), "ThLimit min:", round(min(d["ThLimit"] for d in v["MOTB"]),3), "LiftMax min:", round(min(d["LiftMax"] for d in v["MOTB"]),3))
# W6 egim/hiz trendi
tA, A = dizi(b, "ATT", ["Roll","Pitch","DesRoll","DesPitch"])
tX, X = dizi(b, "XKF1", ["VN","VE","PN","PE","PD"], lambda d: d["C"] == 0)
print("b W5/W6 egim ve hiz (1 s):")
for t0 in list(range(141, 148)) + list(range(188, 202)):
    m = (tA >= t0) & (tA < t0 + 1); mx = (tX >= t0) & (tX < t0 + 1)
    print(f"  {t0}-{t0+1}: Roll {A['Roll'][m].mean():+5.2f} Pitch {A['Pitch'][m].mean():+5.2f} | yatay hiz {np.hypot(X['VN'][mx], X['VE'][mx]).mean():.2f} m/s VN {X['VN'][mx].mean():+.2f} VE {X['VE'][mx].mean():+.2f} PD {X['PD'][mx].mean():+.2f}")
m = (tX >= 202.0) & (tX <= 202.45)
print("XKF1 202.0-202.45:", [(round(t,2), round(vn,2), round(ve,2), round(pd,2)) for t, vn, ve, pd in zip(tX[m], X['VN'][m], X['VE'][m], X['PD'][m])])
m = (tX >= 184) & (tX < 188)
print("XKF1 PD yerde 184-188 ort:", round(X['PD'][m].mean(), 2), " 201.4-202.37 ort:", round(X['PD'][(tX >= 201.4) & (tX < 202.37)].mean(), 2))
tC, C = dizi(b, "CTUN", ["Alt","BAlt"])
for p, q in ((184, 188), (201.4, 202.37)):
    mm = (tC >= p) & (tC < q); print(f"CTUN {p}-{q}: Alt {C['Alt'][mm].mean():.2f} BAlt {C['BAlt'][mm].mean():.2f}")
tC2, C2 = dizi(a, "CTUN", ["Alt","BAlt"])
for p, q in ((617, 621), (637, 643)):
    mm = (tC2 >= p) & (tC2 < q); print(f"a CTUN {p}-{q}: Alt {C2['Alt'][mm].mean():.2f} BAlt {C2['BAlt'][mm].mean():.2f}")
# sert inis 79.47
for ad, v, p, q in (("b 79.0-79.8", b, 79.0, 79.8), ("b 202.30-202.55", b, 202.30, 202.55), ("b 202.88-203.10", b, 202.88, 203.10), ("a 648.2-648.35", a, 648.2, 648.35), ("a 648.8-648.95", a, 648.8, 648.95)):
    L = [d for d in v["IMU"] if p <= d["t"] <= q]
    r = max(L, key=lambda d: math.sqrt(d["AccX"]**2 + d["AccY"]**2 + d["AccZ"]**2))
    print(f"{ad}: |a|max={math.sqrt(r['AccX']**2+r['AccY']**2+r['AccZ']**2):.1f} m/s2 @ {r['t']:.3f} I{r['I']}")
