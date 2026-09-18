import sys
import numpy as np
from pymavlink import DFReader

LOGLAR = {
    "KAZA_4S_1045 (17 Eyl 02:50)": r"O:\navitas\results\ucus_20260917b\2026-09-17 02-50-38.bin",
    "3S_1045 (13 Eyl 08:57)": r"O:\navitas\results\ucus_20260913\2026-09-13 08-57-45.bin",
    "4S_1045 (13 Eyl 09:26, 'asiri titredi')": r"O:\navitas\results\ucus_20260913\2026-09-13 09-26-58.bin",
}
if len(sys.argv) > 1:
    LOGLAR = {a: a for a in sys.argv[1:]}
TIPLER = ["RATE", "IMU", "BAT", "CTUN", "RCOU", "PARM", "VIBE", "MODE"]


def oku(yol):
    r = DFReader.DFReader_binary(yol, zero_time_base=True)
    d = {t: [] for t in TIPLER}
    parm = {}
    while True:
        m = r.recv_match(type=TIPLER)
        if m is None:
            break
        t = m.get_type()
        if t == "PARM":
            parm[m.Name] = m.Value
            continue
        if t == "IMU" and getattr(m, "I", 0) != 0:
            continue
        if t == "BAT" and getattr(m, "Inst", 0) != 0:
            continue
        d[t].append(m.to_dict() | {"_t": m._timestamp})
    return d, parm


def dizi(kayitlar, alan):
    return np.array([k["_t"] for k in kayitlar]), np.array([k.get(alan, np.nan) for k in kayitlar], float)


def baskin_frekans(t, x, fmin=0.5, fmax=None):
    if len(t) < 32:
        return float("nan"), float("nan")
    dt = np.median(np.diff(t))
    if dt <= 0:
        return float("nan"), float("nan")
    fs = 1.0 / dt
    ti = np.arange(t[0], t[-1], dt)
    xi = np.interp(ti, t, x)
    xi = xi - xi.mean()
    w = np.hanning(len(xi))
    F = np.abs(np.fft.rfft(xi * w))
    f = np.fft.rfftfreq(len(xi), dt)
    fmax = fmax or fs / 2
    m = (f >= fmin) & (f <= fmax)
    if not m.any():
        return float("nan"), fs
    i = np.argmax(F[m])
    return float(f[m][i]), fs


for ad, yol in LOGLAR.items():
    print(f"\n==================== {ad}\n{yol}")
    try:
        d, parm = oku(yol)
    except Exception as e:
        print("OKUNAMADI:", e)
        continue
    tb, volt = dizi(d["BAT"], "Volt")
    _, akim = dizi(d["BAT"], "Curr")
    tc, alt = dizi(d["CTUN"], "Alt")
    _, tho = dizi(d["CTUN"], "ThO")
    print(f"BAT Volt min/medyan/max: {np.nanmin(volt):.2f} / {np.nanmedian(volt):.2f} / {np.nanmax(volt):.2f} V  -> "
          f"{'4S' if np.nanmax(volt) > 13.2 else '3S'}; akim maks {np.nanmax(akim):.1f} A")
    for p in ["ATC_RAT_RLL_P", "ATC_RAT_RLL_I", "ATC_RAT_RLL_D", "ATC_RAT_PIT_P", "ATC_RAT_PIT_I", "ATC_RAT_PIT_D",
              "ATC_ANG_RLL_P", "ATC_ANG_PIT_P", "MOT_BAT_VOLT_MAX", "MOT_BAT_VOLT_MIN", "MOT_THST_HOVER",
              "INS_GYRO_FILTER", "INS_HNTCH_ENABLE", "LOG_BITMASK"]:
        if p in parm:
            print(f"  {p} = {parm[p]:g}")
    havada = tc[(alt > 0.3) & (tho > 0.15)] if len(tc) else np.array([])
    if len(havada) == 0:
        print("HAVADA PENCERE BULUNAMADI (Alt>0.3 & ThO>0.15)")
        continue
    # havada kalinan bitisik bloklar
    bloklar = []
    bas = havada[0]
    onc = havada[0]
    for x in havada[1:]:
        if x - onc > 1.0:
            bloklar.append((bas, onc))
            bas = x
        onc = x
    bloklar.append((bas, onc))
    bloklar = [b for b in bloklar if b[1] - b[0] >= 1.5]
    print("havada bloklar (s):", ", ".join(f"{a:.1f}-{b:.1f}" for a, b in bloklar))
    tr, rdes = dizi(d["RATE"], "RDes")
    _, r = dizi(d["RATE"], "R")
    _, pdes = dizi(d["RATE"], "PDes")
    _, p = dizi(d["RATE"], "P")
    _, rout = dizi(d["RATE"], "ROut")
    _, pout = dizi(d["RATE"], "POut")
    ti, gx = dizi(d["IMU"], "GyrX")
    _, gy = dizi(d["IMU"], "GyrY")
    tv, vz = dizi(d["VIBE"], "VibeZ")
    fs_rate = 1 / np.median(np.diff(tr)) if len(tr) > 2 else float("nan")
    fs_imu = 1 / np.median(np.diff(ti)) if len(ti) > 2 else float("nan")
    print(f"ornekleme: RATE {fs_rate:.1f} Hz, IMU {fs_imu:.1f} Hz")
    for a, b in bloklar:
        # bloku 5 s pencerelere bol
        pencere = 5.0
        s = a
        while s < b - 0.5:
            e = min(s + pencere, b)
            mr = (tr >= s) & (tr < e)
            mi = (ti >= s) & (ti < e)
            mv = (tv >= s) & (tv < e)
            mb = (tb >= s) & (tb < e)
            if mr.sum() < 5:
                s = e
                continue
            er = r[mr] - rdes[mr]
            ep = p[mr] - pdes[mr]
            frx, _ = baskin_frekans(ti[mi], gx[mi], 0.5, 20)
            fry, _ = baskin_frekans(ti[mi], gy[mi], 0.5, 20)
            gxr = np.degrees(np.sqrt(np.mean((gx[mi] - gx[mi].mean()) ** 2))) if mi.sum() > 3 else float("nan")
            gyr = np.degrees(np.sqrt(np.mean((gy[mi] - gy[mi].mean()) ** 2))) if mi.sum() > 3 else float("nan")
            print(f"  {s:6.1f}-{e:6.1f}s  roll hata RMS {np.sqrt(np.mean(er**2)):6.1f} °/s  pitch hata RMS {np.sqrt(np.mean(ep**2)):6.1f} °/s  "
                  f"|ROut|max {np.nanmax(np.abs(rout[mr])):.2f} |POut|max {np.nanmax(np.abs(pout[mr])):.2f}  "
                  f"GyrX {gxr:5.1f}°/s@{frx:4.1f}Hz  GyrY {gyr:5.1f}°/s@{fry:4.1f}Hz  "
                  f"VibeZ {np.nanmean(vz[mv]) if mv.any() else float('nan'):5.1f}  V {np.nanmean(volt[mb]) if mb.any() else float('nan'):5.2f}")
            s = e
