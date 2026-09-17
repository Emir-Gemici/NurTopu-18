import numpy as np, math
from ortak import *
def seg(v, a, b, I=0):
    L = [d for d in v["IMU"] if d["I"] == I and a <= d["t"] <= b]
    t = np.array([d["t"] for d in L]); gx = np.degrees([d["GyrX"] for d in L]); gy = np.degrees([d["GyrY"] for d in L]); gz = np.degrees([d["GyrZ"] for d in L])
    return t, gx, gy, gz
def ist(ad, v, a, b):
    t, gx, gy, gz = seg(v, a, b)
    dt = np.diff(t); ok = (dt > 0.03) & (dt < 0.05)
    ax = np.abs(np.diff(gx))[ok] / dt[ok]; ay = np.abs(np.diff(gy))[ok] / dt[ok]; az = np.abs(np.diff(gz))[ok] / dt[ok]
    print(f"{ad:28s} n={ok.sum():4d} |aX| p50={np.percentile(ax,50):6.0f} p95={np.percentile(ax,95):6.0f} p99={np.percentile(ax,99):6.0f} max={ax.max():6.0f} | |aY| p50={np.percentile(ay,50):6.0f} p95={np.percentile(ay,95):6.0f} max={ay.max():6.0f} | |aZ| p95={np.percentile(az,95):5.0f} max={az.max():5.0f}  (deg/s^2)")
a = yukle("a.pkl"); b = yukle("b.pkl")
ist("a F3 havada 622-648.2", a, 622.0, 648.2)
ist("a F3 temas->yer 648.28-648.80", a, 648.28, 648.80)
ist("b W5 havada 141-148", b, 141.0, 148.0)
ist("b W6 havada 188.5-202.33", b, 188.5, 202.33)
ist("b olay 202.33-202.53", b, 202.33, 202.53)
ist("b yuvarlanma 202.53-202.90", b, 202.53, 202.90)
# ayrinti: b olay ardişik farklar her iki IMU
for I in (0, 1):
    t, gx, gy, gz = seg(b, 202.20, 202.95, I)
    print(f"IMU{I}", " ".join(f"{t[i+1]:.2f}:dX={ (gx[i+1]-gx[i])/(t[i+1]-t[i]):+.0f},dY={(gy[i+1]-gy[i])/(t[i+1]-t[i]):+.0f},dZ={(gz[i+1]-gz[i])/(t[i+1]-t[i]):+.0f}" for i in range(len(t)-1)))
