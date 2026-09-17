import numpy as np
from ortak import *
b = yukle("b.pkl"); a = yukle("a.pkl")
def ort_T(v, t0, t1):
    L = [d for d in v["RCOU"] if t0 <= d["t"] < t1]
    T = np.array([[itki(d["C11"]), itki(d["C10"]), itki(d["C12"]), itki(d["C9"])] for d in L])  # M1 M2 M3 M4
    return T.mean(0), len(L)
def ayris(T):
    M1, M2, M3, M4 = T
    return dict(kolektif=(M1+M2+M3+M4)/4, roll_sol_fazla=(-M1+M2+M3-M4), pitch_on_fazla=(M1-M2+M3-M4), yaw_ccw_fazla=(M1+M2-M3-M4))
for ad, v, t0, t1 in [("a F3 637-643", a, 637, 643), ("b W5 141-148", b, 141, 148), ("b W6 188.5-190", b, 188.5, 190.0), ("b W6 201.4-202.37", b, 201.4, 202.37)]:
    T, n = ort_T(v, t0, t1)
    d = ayris(T)
    print(f"{ad:22s} n={n:3d} T(M1..M4)={np.round(T,3)} " + " ".join(f"{k}={x:+.3f}" for k, x in d.items()))
T5, _ = ort_T(b, 141, 148); T6, _ = ort_T(b, 201.4, 202.37)
d5 = ayris(T5); d6 = ayris(T6)
print("FARK (W6 son - W5), itki birimi, toplam olcek:", {k: round(d6[k]-d5[k], 3) for k in d5})
print("Tek-motor-zayif modeli beklenen isaret (roll_sol, pitch_on, yaw_ccw) = delta*(rho,pi,psi):")
for m, (rho, pi, psi) in {"M1 sag-on CCW": (-1, 1, 1), "M2 sol-arka CCW": (1, -1, 1), "M3 sol-on CW": (1, 1, -1), "M4 sag-arka CW": (-1, -1, -1)}.items():
    print(f"  {m}: zayif -> ({rho:+d},{pi:+d},{psi:+d}) ; guclu -> ({-rho:+d},{-pi:+d},{-psi:+d}) ; |uc bilesen esit| ")
# 202.37 an: tek motor kaybi beklenen AccZ
d = [x for x in b["RCOU"] if abs(x["t"] - 202.37) < 0.005][0]
T = np.array([itki(d["C11"]), itki(d["C10"]), itki(d["C12"]), itki(d["C9"])])
imu = [x for x in b["IMU"] if 201.9 <= x["t"] <= 202.371]
az0 = np.mean([x["AccZ"] for x in imu if x["I"] == 0]); az1 = np.mean([x["AccZ"] for x in imu if x["I"] == 1])
print(f"202.37 T(M1..M4)={np.round(T,3)} toplam={T.sum():.3f}; AccZ ort 201.9-202.37 IMU0={az0:.2f} IMU1={az1:.2f}")
for i, m in enumerate(["M1","M2","M3","M4"]):
    kalan = 1 - T[i] / T.sum()
    print(f"  {m} tamamen kaybolursa: itki orani {kalan:.2f} -> AccZ beklenen {az0*kalan:.2f} m/s2")
print("  gozlenen 202.41: IMU0 -3.75, IMU1 -4.05 -> oran", round(-3.75/az0, 2), round(-4.05/az1, 2))
# akim modeli: askida I = n*I1*(T/Th)^1.5
L = [x for x in b["RCOU"] if 201.4 <= x["t"] < 202.37]
Tm = np.array([[itki(x["C11"]), itki(x["C10"]), itki(x["C12"]), itki(x["C9"])] for x in L])
B = [x for x in b["BAT"] if 201.4 <= x["t"] < 202.37]
Iort = np.mean([x["Curr"] for x in B])
S = np.mean(np.sum(Tm ** 1.5, axis=1))
k = Iort / S
print(f"akim modeli: I = k*sum(T^1.5), k={k:.1f} A (201.4-202.37 ort akim {Iort:.1f} A)")
for tt in (202.47, 202.57, 202.67, 202.77, 202.87):
    r = [x for x in b["RCOU"] if abs(x["t"] - tt) < 0.005][0]
    bt = [x for x in b["BAT"] if abs(x["t"] - tt) < 0.005][0]
    T = np.array([itki(r["C11"]), itki(r["C10"]), itki(r["C12"]), itki(r["C9"])])
    saglam = k * np.sum(T ** 1.5); m1yok = k * np.sum(T[1:] ** 1.5) + 1.2
    tahmin = (16.16 - bt["Volt"]) / 0.0377
    print(f"  t={tt}: PWM M1..M4={r['C11']},{r['C10']},{r['C12']},{r['C9']} -> saglam {saglam:5.1f} A | M1 pervanesiz {m1yok:5.1f} A | olculen {bt['Curr']:5.1f} A (120,0 = 36,36*3,3 tavan) | V={bt['Volt']:.2f} -> (16,16-V)/0,0377 = {tahmin:5.0f} A")
print("Ayni model log a 648.30-648.80 (temas sonrasi havada) kontrol:")
L = [x for x in a["RCOU"] if 640 <= x["t"] < 643]
Tm = np.array([[itki(x["C11"]), itki(x["C10"]), itki(x["C12"]), itki(x["C9"])] for x in L])
Ia = np.mean([x["Curr"] for x in a["BAT"] if 640 <= x["t"] < 643]); ka = Ia / np.mean(np.sum(Tm ** 1.5, axis=1))
print(f"  k_a={ka:.1f}")
for r in [x for x in a["RCOU"] if 648.25 <= x["t"] <= 648.85]:
    bt = min(a["BAT"], key=lambda x: abs(x["t"] - r["t"]))
    T = np.array([itki(r["C11"]), itki(r["C10"]), itki(r["C12"]), itki(r["C9"])])
    print(f"  t={r['t']:.3f} model {ka*np.sum(T**1.5):5.1f} A olculen {bt['Curr']:5.1f} A V={bt['Volt']:.2f}")
