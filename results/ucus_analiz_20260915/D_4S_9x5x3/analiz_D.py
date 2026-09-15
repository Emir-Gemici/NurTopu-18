# -*- coding: utf-8 -*-
"""Konfigurasyon D (4S + 9x5x3, 15 Eylul 2026 sabahi) derin analiz.
Ham .bin (pymavlink DFReader) + numpy; SciPy yok. Zaman ekseni: TimeUS/1e6 (mutlak, tum_loglar.json ile ayni).
"""
import json, os, sys, math, hashlib, collections, datetime
import numpy as np
from pymavlink import DFReader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "O:/navitas"
LOGLAR = ["results/ucus_20260915/2026-09-15 11-14-33.bin",
          "results/ucus_20260915/2026-09-15 11-18-16.bin"]
OUT = os.path.join(ROOT, "results/ucus_analiz_20260915/D_4S_9x5x3")
os.makedirs(OUT, exist_ok=True)

# Olcutler (gorev tanimi ile ayni)
THO_MOTORLU = 0.15
KISA_S = 5.0
ASKI_ALT_MIN = 1.0
ASKI_VZ = 0.5
ASKI_THO = (0.25, 0.75)
ASKI_EN_AZ = 10
RCOU_ESIK = 1050
HOVER_TC = 10.0          # AP_MOTORS_THST_HOVER_TC (s)
HOVER_MIN, HOVER_MAX = 0.125, 0.6875

# Renkler (dataviz varsayilan kategorik sira: mavi, turuncu, aqua, sari, magenta, yesil, mor, kirmizi)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURF = "#fcfcfb"; TXT = "#0b0b0b"; TXT2 = "#52514e"; GRID = "#e6e5e1"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": "#cfceca",
                     "axes.labelcolor": TXT, "xtick.color": TXT2, "ytick.color": TXT2, "text.color": TXT,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9, "legend.frameon": False, "lines.linewidth": 1.2})

EV_AD = {10: "ARMED", 11: "DISARMED", 15: "AUTO_ARMED", 17: "LAND_COMPLETE_MAYBE", 18: "LAND_COMPLETE",
         25: "SET_HOME", 28: "NOT_LANDED", 56: "MOTORS_INTERLOCK_DISABLED", 57: "MOTORS_INTERLOCK_ENABLED",
         60: "EKF_ALT_RESET", 62: "EKF_YAW_RESET", 73: "LAND_REPO_ACTIVE"}
MODE_AD = {0: "STAB", 1: "ACRO", 2: "ALTHOLD", 3: "AUTO", 4: "GUIDED", 5: "LOIT", 6: "RTL", 9: "LAND", 16: "POSHOLD", 21: "SMART_RTL"}
ERR_SUB = {8: "FS_GCS", 5: "FS_RADYO", 6: "FS_PIL", 12: "CRASH_CHECK", 16: "EKFCHECK", 17: "FS_EKFINAV", 24: "EKF_PRIMARY", 25: "THRUST_LOSS", 29: "FS_VIBE"}
ARM_YONTEM = {0: "RUDDER", 1: "MAVLINK", 2: "AUXSWITCH", 3: "MOTORTEST", 4: "SCRIPTING", 13: "LANDED", 8: "TERMINATION"}
MOTOR_FN = {33: "M1", 34: "M2", 35: "M3", 36: "M4"}


def r(x, n=3):
    if x is None: return None
    if isinstance(x, (float, np.floating)):
        if not np.isfinite(x): return None
        return round(float(x), n)
    return x


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def oku(fn):
    log = DFReader.DFReader_binary(fn)
    D = collections.defaultdict(list); parm = {}; parm_seri = collections.defaultdict(list); sayac = collections.Counter()
    while True:
        m = log.recv_msg()
        if m is None: break
        ty = m.get_type(); sayac[ty] += 1
        tu = getattr(m, "TimeUS", None)
        t = tu / 1e6 if tu is not None else None
        if ty == "CTUN": D["CTUN"].append((t, m.ThI, m.ThO, m.ThH, m.DAlt, m.Alt, m.BAlt, m.DCRt, m.CRt))
        elif ty == "BAT":
            if int(getattr(m, "Inst", 0)) == 0: D["BAT"].append((t, m.Volt, m.VoltR, m.Curr, m.CurrTot, m.EnrgTot, m.Res, m.RemPct))
        elif ty == "VIBE": D["VIBE"].append((t, m.IMU, m.VibeX, m.VibeY, m.VibeZ, m.Clip))
        elif ty == "RCOU": D["RCOU"].append((t,) + tuple(getattr(m, "C%d" % i) for i in range(1, 15)))
        elif ty == "RCIN": D["RCIN"].append((t,) + tuple(getattr(m, "C%d" % i) for i in range(1, 9)))
        elif ty == "ATT": D["ATT"].append((t, m.DesRoll, m.Roll, m.DesPitch, m.Pitch, m.DesYaw, m.Yaw, m.ErrRP, m.ErrYaw))
        elif ty == "RATE": D["RATE"].append((t, m.RDes, m.R, m.PDes, m.P, m.YDes, m.Y, m.ADes, m.A, m.AOut, m.ROut, m.POut, m.YOut))
        elif ty == "IMU": D["IMU"].append((t, m.I, m.GyrX, m.GyrY, m.GyrZ, m.AccX, m.AccY, m.AccZ))
        elif ty == "XKF4": D["XKF4"].append((t, m.C, m.SV, m.SP, m.SH, m.SM, m.SVT, m.errRP, m.FS, m.TS, m.SS, m.PI))
        elif ty == "XKF3": D["XKF3"].append((t, m.C, m.IVN, m.IVE, m.IVD, m.IPN, m.IPE, m.IPD, m.IMX, m.IMY, m.IMZ, m.IYAW))
        elif ty == "PSCD": D["PSCD"].append((t, m.TPD, m.PD, m.DVD, m.TVD, m.VD, m.DAD, m.TAD, m.AD))
        elif ty == "MOTB": D["MOTB"].append((t, m.LiftMax, m.BatVolt, m.ThLimit, m.ThrAvMx, m.ThrOut, m.FailFlags))
        elif ty == "GPS": D["GPS"].append((t, m.Status, m.NSats, m.HDop))
        elif ty == "POWR": D["POWR"].append((t, m.Vcc, m.VServo, m.Flags))
        elif ty == "DSF": D["DSF"].append((t, m.Dp))
        elif ty == "EV": D["EV"].append((t, int(m.Id)))
        elif ty == "ERR": D["ERR"].append((t, int(m.Subsys), int(m.ECode)))
        elif ty == "MODE": D["MODE"].append((t, int(m.Mode), int(m.Rsn)))
        elif ty == "ARM": D["ARM"].append((t, int(m.ArmState), int(m.Method), int(getattr(m, "Forced", 0))))
        elif ty == "MSG": D["MSG"].append((t, str(m.Message)))
        elif ty == "PARM":
            parm_seri[m.Name].append((t, float(m.Value)))
            if m.Name not in parm: parm[m.Name] = float(m.Value)
    A = {k: np.array(v, dtype=float) for k, v in D.items() if k not in ("MSG", "EV", "ERR", "MODE", "ARM")}
    for k in ("EV", "ERR", "MODE", "ARM"): A[k] = D[k]
    A["MSG"] = D["MSG"]; A["parm"] = parm; A["parm_seri"] = parm_seri; A["sayac"] = sayac
    return A


def pencereler(A):
    """ARM(1)->ARM(0) pencereleri; yoksa RCOU motor kanallari > esik."""
    p = []
    arm = A["ARM"]; ac = None
    for t, s, meth, forced in arm:
        if s == 1 and ac is None: ac = (t, meth)
        elif s == 0 and ac is not None:
            p.append({"t0": ac[0], "t1": t, "kaynak": "ARM", "arm_yontemi": ARM_YONTEM.get(ac[1], str(ac[1])), "disarm_yontemi": ARM_YONTEM.get(meth, str(meth))}); ac = None
    # RCOU tamamlayici
    rc = A["RCOU"]; mot = rc[:, 9:13].max(axis=1); t = rc[:, 0]
    on = mot > RCOU_ESIK
    seg = []; i = 0; n = len(t)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]: j += 1
            seg.append([t[i], t[j]]); i = j + 1
        else: i += 1
    bir = []
    for a, b in seg:
        if bir and a - bir[-1][1] < 2.0: bir[-1][1] = b
        else: bir.append([a, b])
    for a, b in bir:
        if b - a < 1.0: continue
        if any(a < q["t1"] + 0.5 and b > q["t0"] - 0.5 for q in p): continue
        # disarm ARM(0) kaydi varsa pencere sonunu ona cek
        dis = [tt for tt, s, _, _ in arm if s == 0 and b - 1.0 <= tt <= b + 1.0]
        p.append({"t0": a, "t1": dis[0] if dis else b, "kaynak": "RCOU", "arm_yontemi": None,
                  "disarm_yontemi": ARM_YONTEM.get(next((mm for tt, s, mm, _ in arm if s == 0 and abs(tt - (dis[0] if dis else b)) < 1.0), -1), None)})
    p.sort(key=lambda q: q["t0"])
    return p


def mode_at(A, t):
    m = None
    for tt, md, _ in A["MODE"]:
        if tt <= t: m = md
        else: break
    return m


def ma(x, n=5):
    if len(x) < n: return x
    k = np.ones(n) / n
    y = np.convolve(x, k, mode="same")
    # kenarlar: kismi ortalama
    for i in range(n // 2):
        y[i] = x[:i + n // 2 + 1].mean(); y[-1 - i] = x[-(i + n // 2 + 1):].mean()
    return y


def dilimler(t, mask, bosluk=0.25):
    """mask True olan orneklerin bitisik dilimleri [(t0,t1,n)]"""
    out = []; i = 0; n = len(t)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1] and t[j + 1] - t[j] <= bosluk: j += 1
            out.append((t[i], t[j], j - i + 1)); i = j + 1
        else: i += 1
    return out


def fft_tepeler(t, x, en_az_hz=0.3, k=5):
    if len(x) < 32: return None
    dt = np.median(np.diff(t)); fs = 1.0 / dt
    x = x - x.mean(); w = np.hanning(len(x)); X = np.fft.rfft(x * w); f = np.fft.rfftfreq(len(x), dt)
    amp = 2.0 * np.abs(X) / w.sum()
    m = f >= en_az_hz
    idx = [i for i in range(1, len(f) - 1) if m[i] and amp[i] >= amp[i - 1] and amp[i] >= amp[i + 1]]
    idx.sort(key=lambda i: -amp[i])
    return {"fs_hz": r(fs, 2), "nyquist_hz": r(fs / 2, 2), "n": int(len(x)), "sure_s": r(t[-1] - t[0], 2), "cozunurluk_hz": r(f[1], 3),
            "rms": r(float(np.sqrt(np.mean(x ** 2))), 3), "tepeler": [{"f_hz": r(f[i], 2), "genlik": r(amp[i], 3)} for i in idx[:k]],
            "_f": f, "_amp": amp}


def istat(x):
    x = np.asarray(x, float)
    if len(x) == 0: return None
    return {"n": int(len(x)), "ort": r(x.mean()), "p50": r(np.percentile(x, 50)), "p05": r(np.percentile(x, 5)), "p95": r(np.percentile(x, 95)), "maks": r(x.max()), "std": r(x.std())}


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def ucus_analiz(A, P, k, log_ad):
    t0, t1 = P["t0"], P["t1"]
    u = {"no": k, "arm_t": r(t0, 2), "disarm_t": r(t1, 2), "pencere_s": r(t1 - t0, 1), "pencere_kaynak": P["kaynak"],
         "arm_yontemi": P["arm_yontemi"], "disarm_yontemi": P["disarm_yontemi"], "notlar": []}
    ct = A["CTUN"]; cm = (ct[:, 0] >= t0) & (ct[:, 0] <= t1)
    c = ct[cm]; tc = c[:, 0]; ThO = c[:, 2]; ThH = c[:, 3]; Alt = c[:, 5]; CRt = c[:, 8]; DCRt = c[:, 7]
    taban = np.median(Alt[tc <= t0 + 1.0]) if np.any(tc <= t0 + 1.0) else Alt[0]
    alt = Alt - taban
    vz = ma(np.gradient(Alt, tc), 5)
    mot = ThO > THO_MOTORLU
    dtc = np.median(np.diff(tc)) if len(tc) > 1 else 0.1
    motorlu_s = float(mot.sum() * dtc)
    u["ctun_hz"] = r(1 / dtc, 1); u["alt_taban_m"] = r(taban, 2); u["alt_maks_m"] = r(alt.max(), 2)
    u["motorlu_s"] = r(motorlu_s, 1)
    u["motorlu_t"] = [r(tc[mot][0], 1), r(tc[mot][-1], 1)] if mot.any() else None
    if not mot.any(): u["tur"] = "arm_yalniz"
    elif motorlu_s < KISA_S: u["tur"] = "kisa_sicrama"
    else: u["tur"] = "ucus"
    u["kip_arm"] = MODE_AD.get(mode_at(A, t0 + 0.05), str(mode_at(A, t0 + 0.05)))
    u["kip_gecisleri"] = [{"t": r(tt, 1), "kip": MODE_AD.get(md, str(md))} for tt, md, _ in A["MODE"] if t0 - 0.5 <= tt <= t1 + 0.5]
    u["ThH_bas"] = r(ThH[0], 4); u["ThH_son"] = r(ThH[-1], 4)
    u["ThO_motorlu"] = istat(ThO[mot]) if mot.any() else None
    # --- aski ornekleri
    aski = (alt >= ASKI_ALT_MIN) & (np.abs(vz) < ASKI_VZ) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
    u["aski_n"] = int(aski.sum()); u["aski_s"] = r(aski.sum() * dtc, 1)
    # capraz: CTUN.CRt (cm/s) ile ayni tanim
    aski_crt = (alt >= ASKI_ALT_MIN) & (np.abs(CRt) < ASKI_VZ * 100) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
    u["aski_n_CRt_kaynakli"] = int(aski_crt.sum())
    ds = dilimler(tc, aski)
    u["aski"] = None
    if aski.sum() >= ASKI_EN_AZ:
        en = max(ds, key=lambda d: d[1] - d[0])
        u["aski"] = {"ThO": istat(ThO[aski]), "alt_ort_m": r(alt[aski].mean(), 2), "alt_std_m": r(alt[aski].std(), 2),
                     "dilim_n": len(ds), "en_uzun_dilim_t": [r(en[0], 1), r(en[1], 1)], "en_uzun_dilim_s": r(en[1] - en[0], 1),
                     "DCRt_sifir_orani": r(float(np.mean(DCRt[aski] == 0)), 3)}
        u["_aski_mask"] = aski; u["_en_uzun"] = en
    else:
        u["notlar"].append("aski orneklemi yetersiz (%d < %d)" % (aski.sum(), ASKI_EN_AZ))
    u["_tc"] = tc; u["_ThO"] = ThO; u["_alt"] = alt; u["_mot"] = mot; u["_vz"] = vz
    # --- pil
    b = A["BAT"]; bm = (b[:, 0] >= t0) & (b[:, 0] <= t1); bb = b[bm]
    onc = b[(b[:, 0] >= t0 - 5.0) & (b[:, 0] < t0)]
    bat = {"V_arm_oncesi_5s_ort": r(onc[:, 1].mean(), 2) if len(onc) else None, "I_arm_oncesi_5s_ort": r(onc[:, 3].mean(), 2) if len(onc) else None,
           "V_bas": r(bb[0, 1], 2), "V_son": r(bb[-1, 1], 2), "mAh_pencere": r(bb[-1, 4] - bb[0, 4], 0), "Wh_pencere": r(bb[-1, 5] - bb[0, 5], 2),
           "RemPct_son": r(bb[-1, 7], 1)}
    if mot.any():
        tm0, tm1 = tc[mot][0], tc[mot][-1]
        mm = (bb[:, 0] >= tm0) & (bb[:, 0] <= tm1); bmot = bb[mm]
        imin = np.argmin(bmot[:, 1])
        bat.update({"kapsam_motorlu": [r(tm0, 1), r(tm1, 1)], "V_min": r(bmot[imin, 1], 2), "V_min_t": r(bmot[imin, 0], 1),
                    "V_min_I": r(bmot[imin, 3], 1), "V_ort_motorlu": r(bmot[:, 1].mean(), 2),
                    "I_motorlu": istat(bmot[:, 3]), "mAh_motorlu": r(bmot[-1, 4] - bmot[0, 4], 0),
                    "sarkma_V": r(bb[0, 1] - bmot[imin, 1], 2), "sarkma_V_hucre": r((bb[0, 1] - bmot[imin, 1]) / 4, 3),
                    "toparlanma_V": r(bb[-1, 1] - bmot[imin, 1], 2)})
    if u["aski"] is not None:
        # BAT ornekleri aski CTUN zamanlarina en yakin (10 Hz ikisi de)
        ta = tc[aski]; ib = np.searchsorted(bb[:, 0], ta); ib = np.clip(ib, 0, len(bb) - 1); ba = bb[ib]
        V = ba[:, 1]; I = ba[:, 3]
        R_oz = None
        if len(onc) and (I.mean() - onc[:, 3].mean()) > 5:
            R_oz = (onc[:, 1].mean() - V.mean()) / (I.mean() - onc[:, 3].mean())
        sl = np.polyfit(V, ThO[aski], 1)[0] if V.std() > 0.05 else None
        bat["aski"] = {"V": istat(V), "V_hucre_ort": r(V.mean() / 4), "I": istat(I), "P_W": istat(V * I), "VoltR_ort": r(ba[:, 2].mean(), 2),
                       "BAT_Res_ort_ohm": r(ba[:, 6].mean(), 4), "R_ic_hesap_ohm": r(R_oz, 4), "R_ic_hesap_mohm_hucre": r(R_oz * 1000 / 4, 1) if R_oz else None,
                       "dThO_dV_egim": r(sl, 4), "mAh_per_s": r(I.mean() / 3.6, 2)}
    u["bat"] = bat
    # --- titresim
    v = A["VIBE"]; vm = (v[:, 0] >= t0) & (v[:, 0] <= t1); vv = v[vm]
    vibe = {"kapsam_pencere": {}, "clip": {}}
    for inst in (0, 1):
        x = vv[vv[:, 1] == inst]
        if not len(x): continue
        vibe["kapsam_pencere"]["IMU%d" % inst] = {ax: istat(x[:, 2 + i]) for i, ax in enumerate("XYZ")}
        cl = x[:, 5]; art = np.diff(cl); it = np.where(art > 0)[0]
        vibe["clip"]["IMU%d" % inst] = {"artis": int(cl[-1] - cl[0]), "zamanlar": [[r(x[i + 1, 0], 2), int(art[i])] for i in it][:20]}
    if mot.any():
        tm0, tm1 = tc[mot][0], tc[mot][-1]
        vibe["kapsam_motorlu"] = {}
        for inst in (0, 1):
            x = vv[(vv[:, 1] == inst) & (vv[:, 0] >= tm0) & (vv[:, 0] <= tm1)]
            if len(x): vibe["kapsam_motorlu"]["IMU%d" % inst] = {ax: istat(x[:, 2 + i]) for i, ax in enumerate("XYZ")}
        x = vv[(vv[:, 0] >= tm0) & (vv[:, 0] <= tm1)]
        vibe["kapsam_motorlu"]["IMU_birlesik"] = {ax: istat(x[:, 2 + i]) for i, ax in enumerate("XYZ")}
    if u["aski"] is not None:
        vibe["kapsam_aski"] = {}
        ta = tc[aski]
        for inst in (0, 1):
            x = vv[vv[:, 1] == inst]
            # VIBE 10 Hz/inst; aski CTUN zamanina +-0.06 s icinde olanlar
            sel = np.zeros(len(x), bool)
            j = np.searchsorted(x[:, 0], ta); j = np.clip(j, 0, len(x) - 1); sel[j] = True
            xs = x[sel]
            vibe["kapsam_aski"]["IMU%d" % inst] = {ax: istat(xs[:, 2 + i]) for i, ax in enumerate("XYZ")}
        xs = np.vstack([vv[vv[:, 1] == inst][np.clip(np.searchsorted(vv[vv[:, 1] == inst][:, 0], ta), 0, len(vv[vv[:, 1] == inst]) - 1)] for inst in (0, 1)])
        vibe["kapsam_aski"]["IMU_birlesik"] = {ax: istat(xs[:, 2 + i]) for i, ax in enumerate("XYZ")}
    u["vibe"] = vibe
    # --- IMU FFT (en uzun aski dilimi)
    u["imu_fft"] = None
    if u["aski"] is not None:
        a0, a1 = u["_en_uzun"][0], u["_en_uzun"][1]
        im = A["IMU"]; res = {"dilim_t": [r(a0, 1), r(a1, 1)]}
        for inst in (0, 1):
            x = im[(im[:, 1] == inst) & (im[:, 0] >= a0) & (im[:, 0] <= a1)]
            if len(x) < 32: continue
            res["IMU%d" % inst] = {}
            for ad, col in (("AccZ", 7), ("AccX", 5), ("AccY", 6), ("GyrX", 2), ("GyrY", 3), ("GyrZ", 4)):
                f = fft_tepeler(x[:, 0], x[:, col])
                if f: res["IMU%d" % inst][ad] = {kk: vv2 for kk, vv2 in f.items() if not kk.startswith("_")}
                if ad == "AccZ": u["_fft_%d" % inst] = (f["_f"], f["_amp"], f["fs_hz"])
        u["imu_fft"] = res
    # --- RCOU motor dengesi (SERVO9..12 = M4,M2,M1,M3)
    rc = A["RCOU"]; rm = (rc[:, 0] >= t0) & (rc[:, 0] <= t1); rr = rc[rm]
    mot_kanal = {}
    for ch in range(9, 13):
        fn = A["parm"].get("SERVO%d_FUNCTION" % ch)
        if fn in MOTOR_FN: mot_kanal[MOTOR_FN[fn]] = ch
    u["_mot_kanal"] = mot_kanal
    rcou = {"motor_kanallari": {m: "C%d" % ch for m, ch in sorted(mot_kanal.items())},
            "not": "SERVO9..12_FUNCTION = 36,34,33,35 -> C9=M4, C10=M2, C11=M1, C12=M3 (AUX1-4). C1..C4 (MAIN) = M2,M2,M1,M2 kopyalari; motor dengesi icin KULLANILMAZ."}
    if u["aski"] is not None or mot.any():
        if u["aski"] is not None:
            ta = tc[aski]; kap = "aski"
        else:
            ta = tc[mot]; kap = "motorlu"
        j = np.clip(np.searchsorted(rr[:, 0], ta), 0, len(rr) - 1); rs = rr[j]
        ort = {m: float(rs[:, ch].mean()) for m, ch in mot_kanal.items()}
        std = {m: float(rs[:, ch].std()) for m, ch in mot_kanal.items()}
        vals = ort
        rcou.update({"kapsam": kap, "n": int(len(rs)), "M_ort_pwm": {m: r(v, 0) for m, v in sorted(vals.items())},
                     "M_std_pwm": {m: r(v, 1) for m, v in sorted(std.items())},
                     "yayilim_pwm": r(max(vals.values()) - min(vals.values()), 0), "yayilim_pct_aralik": r((max(vals.values()) - min(vals.values())) / 10.0, 1),
                     "en_yuksek": max(vals, key=vals.get), "en_dusuk": min(vals, key=vals.get),
                     "ort_pwm_orani": r((np.mean(list(vals.values())) - 1000) / 1000.0, 3),
                     "cift_farklari_pwm": {"CCW(M1+M2)-CW(M3+M4)_yaw": r(vals["M1"] + vals["M2"] - vals["M3"] - vals["M4"], 0),
                                           "on(M1+M3)-arka(M2+M4)_pitch": r(vals["M1"] + vals["M3"] - vals["M2"] - vals["M4"], 0),
                                           "sag(M1+M4)-sol(M2+M3)_roll": r(vals["M1"] + vals["M4"] - vals["M2"] - vals["M3"], 0)},
                     "MAIN_C1_C4_ort_pwm_karsilastirma": [r(rs[:, ch].mean(), 0) for ch in range(1, 5)]})
        # ThO -> beklenen PWM (expo 0.65, spin 0.15..0.95)
        if u["aski"] is not None:
            th = float(ThO[aski].mean()); e = A["parm"].get("MOT_THST_EXPO", 0.65); smin = A["parm"].get("MOT_SPIN_MIN", 0.15); smax = A["parm"].get("MOT_SPIN_MAX", 0.95)
            ratio = ((e - 1) + math.sqrt((1 - e) ** 2 + 4 * e * th)) / (2 * e)
            rcou["ThO_aski_beklenen_pwm_hesap"] = r(1000 + 1000 * (smin + (smax - smin) * ratio), 0)
    u["rcou"] = rcou
    # --- tutum
    at = A["ATT"]; am = (at[:, 0] >= t0) & (at[:, 0] <= t1); aa = at[am]
    def att_stat(x):
        er = x[:, 2] - x[:, 1]; ep = x[:, 4] - x[:, 3]; ey = wrap(x[:, 6] - x[:, 5])
        return {"n": int(len(x)), "roll_rms_hata_deg": r(np.sqrt(np.mean(er ** 2)), 2), "pitch_rms_hata_deg": r(np.sqrt(np.mean(ep ** 2)), 2),
                "yaw_rms_hata_deg": r(np.sqrt(np.mean(ey ** 2)), 2), "roll_maks_abs_deg": r(np.abs(x[:, 2]).max(), 1), "pitch_maks_abs_deg": r(np.abs(x[:, 4]).max(), 1),
                "roll_ort_deg": r(x[:, 2].mean(), 2), "pitch_ort_deg": r(x[:, 4].mean(), 2), "ErrRP_ort": r(x[:, 7].mean(), 3), "ErrRP_maks": r(x[:, 7].max(), 3)}
    att = {}
    if mot.any():
        tm0, tm1 = tc[mot][0], tc[mot][-1]; att["motorlu"] = att_stat(aa[(aa[:, 0] >= tm0) & (aa[:, 0] <= tm1)])
    if u["aski"] is not None:
        ta = tc[aski]; j = np.clip(np.searchsorted(aa[:, 0], ta), 0, len(aa) - 1); att["aski"] = att_stat(aa[j])
        rt = A["RATE"]; rrt = rt[(rt[:, 0] >= t0) & (rt[:, 0] <= t1)]; j = np.clip(np.searchsorted(rrt[:, 0], ta), 0, len(rrt) - 1); rs = rrt[j]
        att["aski_hiz"] = {"roll_rate_rms_hata_dps": r(np.sqrt(np.mean((rs[:, 2] - rs[:, 1]) ** 2)), 2),
                           "pitch_rate_rms_hata_dps": r(np.sqrt(np.mean((rs[:, 4] - rs[:, 3]) ** 2)), 2),
                           "yaw_rate_rms_hata_dps": r(np.sqrt(np.mean((rs[:, 6] - rs[:, 5]) ** 2)), 2),
                           "YDes_ort_dps": r(rs[:, 5].mean(), 2), "YDes_p90_dps": r(np.percentile(rs[:, 5], 90), 1), "Y_abs_ort_dps": r(np.abs(rs[:, 6]).mean(), 2), "Y_p10_p90_dps": [r(np.percentile(rs[:, 6], 10), 1), r(np.percentile(rs[:, 6], 90), 1)],
                           "ROut_ort": r(rs[:, 10].mean(), 4), "POut_ort": r(rs[:, 11].mean(), 4), "YOut_ort": r(rs[:, 12].mean(), 4), "YOut_p90": r(np.percentile(rs[:, 12], 90), 3), "YOut_maks_abs": r(np.abs(rs[:, 12]).max(), 3),
                           "yaw_hata_maks_abs_deg": r(np.abs(wrap(aa[j][:, 6] - aa[j][:, 5])).max(), 1),
                           "RCIN_C4_yaw_cubugu": {"ort_us": r(A["RCIN"][(A["RCIN"][:, 0] >= ta[0]) & (A["RCIN"][:, 0] <= ta[-1]), 4].mean(), 0), "std_us": r(A["RCIN"][(A["RCIN"][:, 0] >= ta[0]) & (A["RCIN"][:, 0] <= ta[-1]), 4].std(), 1)},
                           "not": "RATE.R/P/Y deg/s; ROut/POut/YOut -1..1 karistirici cikisi (ortalama != 0 -> surekli tork dengesizligi)"}
        # aski diliminde irtifa egilimi (m/s) ve gaz cubugu
        a0, a1 = u["_en_uzun"][0], u["_en_uzun"][1]; sl_m = (tc >= a0) & (tc <= a1)
        u["aski"]["alt_egim_en_uzun_dilim_ms"] = r(np.polyfit(tc[sl_m], alt[sl_m], 1)[0], 3)
        ri = A["RCIN"]; rq = ri[(ri[:, 0] >= a0) & (ri[:, 0] <= a1)]
        rmin, rmax, rdz, tdz = A["parm"].get("RC3_MIN", 1000), A["parm"].get("RC3_MAX", 2000), A["parm"].get("RC3_DZ", 30), A["parm"].get("THR_DZ", 100)
        mid = 1000.0 * ((rmin + rmax) / 2.0 - (rmin + rdz)) / (rmax - (rmin + rdz))
        dz_pwm = [(rmin + rdz) + (mid - tdz) / 1000.0 * (rmax - (rmin + rdz)), (rmin + rdz) + (mid + tdz) / 1000.0 * (rmax - (rmin + rdz))]
        inDZ = (rq[:, 3] >= dz_pwm[0]) & (rq[:, 3] <= dz_pwm[1]); best = cur = 0
        for v_ in inDZ:
            cur = cur + 1 if v_ else 0; best = max(best, cur)
        u["aski"]["gaz_cubugu_RCIN_C3"] = {"ort_us": r(rq[:, 3].mean(), 0), "std_us": r(rq[:, 3].std(), 1), "p50_us": r(np.median(rq[:, 3]), 0),
                                           "olu_bolge_us_hesap": [r(dz_pwm[0], 0), r(dz_pwm[1], 0)], "olu_bolge_ici_orani": r(float(inDZ.mean()), 3), "en_uzun_olu_bolge_s": r(best * np.median(np.diff(rq[:, 0])), 1),
                                           "not": "olu bolge = RC3 mid(control_in) +- THR_DZ; RC3_MIN/MAX/DZ=%s/%s/%s THR_DZ=%s; ustunde kalan cubuk = surekli pozitif tirmanma istegi" % (rmin, rmax, rdz, tdz)}
    u["att"] = att
    # --- MOT_THST_HOVER ogrenme uygunlugu (Copter::update_throttle_hover kosullari)
    u["hover_ogrenme"] = None
    if u["tur"] == "ucus":
        ps = A["PSCD"]; pm = (ps[:, 0] >= t0) & (ps[:, 0] <= t1); pp = ps[pm]
        modes = np.array([mode_at(A, x) for x in tc])
        manual = np.isin(modes, [0, 1, 17])  # STAB, ACRO, DRIFT? (DRIFT=11 de haric)
        manual |= modes == 11
        # not landed: EV28 NOT_LANDED .. EV17 LAND_COMPLETE_MAYBE
        ev = [(tt, i) for tt, i in A["EV"] if t0 <= tt <= t1]
        nl = [tt for tt, i in ev if i == 28]; lc = [tt for tt, i in ev if i in (17, 18)]
        havada = np.zeros(len(tc), bool)
        if nl:
            a = nl[0]; bnd = min([x for x in lc if x > a], default=t1); havada = (tc >= a) & (tc <= bnd)
        if len(pp):
            j = np.clip(np.searchsorted(pp[:, 0], tc), 0, len(pp) - 1); DVD = pp[j, 3]; VD = pp[j, 5]   # PSCD m, m/s (AC_PosControl *0.01)
            dvd_ok = np.abs(DVD) * 100.0 < 1.1920929e-7   # is_zero(vel_desired.z cm/s) = fabsf < FLT_EPSILON
        else:
            dvd_ok = np.zeros(len(tc), bool); VD = np.zeros(len(tc))
        j = np.clip(np.searchsorted(aa[:, 0], tc), 0, len(aa) - 1)
        rp_ok = (np.abs(aa[j, 2]) < 5.0) & (np.abs(aa[j, 4]) < 5.0)
        vz_ok = np.abs(VD) < 0.60
        uygun = havada & (~manual) & dvd_ok & rp_ok & vz_ok & (ThO > 0)
        # simulasyon
        th = float(ThH[0]); alfa = dtc / (dtc + HOVER_TC)
        for i in range(len(tc)):
            if uygun[i]: th = min(max(th + alfa * (ThO[i] - th), HOVER_MIN), HOVER_MAX)
        # sadece DVD kosulu olmasa ne olurdu
        th2 = float(ThH[0]); uy2 = havada & (~manual) & rp_ok & vz_ok & (ThO > 0)
        for i in range(len(tc)):
            if uy2[i]: th2 = min(max(th2 + alfa * (ThO[i] - th2), HOVER_MIN), HOVER_MAX)
        hv = havada & (~manual)
        u["hover_ogrenme"] = {"havada_otomatik_gaz_s": r(hv.sum() * dtc, 1),
                              "kosul_oranlari_havada": {"is_zero(PSCD.DVD)": r(float(dvd_ok[hv].mean()), 3) if hv.any() else None,
                                                        "|VD|<0.6m/s": r(float(vz_ok[hv].mean()), 3) if hv.any() else None,
                                                        "|roll|,|pitch|<5deg": r(float(rp_ok[hv].mean()), 3) if hv.any() else None,
                                                        "hepsi": r(float(uygun[hv].mean()), 3) if hv.any() else None},
                              "uygun_s": r(uygun.sum() * dtc, 2),
                              "DVD_havada_abs_p50_ms": r(float(np.median(np.abs(DVD[hv]))), 4) if hv.any() else None,
                              "DVD_havada_abs_p90_ms": r(float(np.percentile(np.abs(DVD[hv]), 90)), 4) if hv.any() else None,
                              "DVD_havada_ort_ms_yukari_pozitif": r(float(-DVD[hv].mean()), 4) if hv.any() else None,
                              "en_uzun_uygun_dilim_s": r(max([d[1] - d[0] for d in dilimler(tc, uygun)] + [0.0]), 1),
                              "ThH_bas": r(ThH[0], 4), "ThH_son_log": r(ThH[-1], 4), "ThH_sim_kosullu": r(th, 4), "ThH_sim_DVD_kosulsuz": r(th2, 4), "ThH_gercek_degisim": r(ThH[-1] - ThH[0], 4),
                              "not": "Sim: alfa=dt/(dt+10 s) (AP_MOTORS_THST_HOVER_TC), uygun CTUN orneklerinde ThO'ya dogru; Copter::update_throttle_hover kosullari: armli, havada, manuel gaz kipi degil, is_zero(vel_desired.z) (PSCD.DVD m/s, FLT_EPSILON), |vz|<0.6 m/s (PSCD.VD), |roll|,|pitch|<5 deg. PSCD 10 Hz orneklendigi icin 100 Hz deki kisa sifir anlari kacabilir (kucuk gercek degisimi aciklar)"}
    # --- EKF
    xk = A["XKF4"]; xm = (xk[:, 0] >= t0) & (xk[:, 0] <= t1); xx = xk[xm]
    ekf = {"cekirdek": {}}
    for core in (0, 1):
        x = xx[xx[:, 1] == core]
        if not len(x): continue
        ekf["cekirdek"][str(core)] = {"n": int(len(x)), "SV_maks": r(x[:, 2].max(), 2), "SV_p95": r(np.percentile(x[:, 2], 95), 2), "SP_maks": r(x[:, 3].max(), 2), "SH_maks": r(x[:, 4].max(), 2),
                                      "SM_maks": r(x[:, 5].max(), 2), "SM_p95": r(np.percentile(x[:, 5], 95), 2), "errRP_maks": r(x[:, 7].max(), 3),
                                      "innov_>1_n": int(((x[:, 2] > 1) | (x[:, 3] > 1) | (x[:, 4] > 1) | (x[:, 5] > 1)).sum()),
                                      "FS_degerler": sorted(set(int(v_) for v_ in x[:, 8])), "TS_degerler": sorted(set(int(v_) for v_ in x[:, 9])), "SS_degerler": sorted(set(int(v_) for v_ in x[:, 10])),
                                      "not": "TS bit4(16)=airspeed timeout, hava hizi sensoru olmayan kopterde daima set; FS=0 normal"}
    pi = xx[:, 11]; ekf["lane_switch_n"] = int((np.diff(pi) != 0).sum()) if len(pi) > 1 else 0; ekf["primary_core"] = sorted(set(int(v) for v in pi)) if len(pi) else None
    x3 = A["XKF3"]; m3 = (x3[:, 0] >= t0) & (x3[:, 0] <= t1); y = x3[m3]
    if len(y):
        ekf["innovasyon_maks_abs"] = {"IVD_ms": r(np.abs(y[:, 4]).max(), 3), "IPD_m": r(np.abs(y[:, 7]).max(), 3), "IVN_ms": r(np.abs(y[:, 2]).max(), 3), "IVE_ms": r(np.abs(y[:, 3]).max(), 3),
                                      "IMX_mGauss": r(np.abs(y[:, 8]).max(), 1), "IMY_mGauss": r(np.abs(y[:, 9]).max(), 1), "IMZ_mGauss": r(np.abs(y[:, 10]).max(), 1), "IYAW_rad": r(np.abs(y[:, 11]).max(), 3)}
    g = A["GPS"]; gm = (g[:, 0] >= t0) & (g[:, 0] <= t1); gg = g[gm]
    if len(gg):
        hg = A["parm"].get("GPS_HDOP_GOOD", 140) / 100.0; kot = gg[gg[:, 3] > hg]
        ekf["gps"] = {"NSats_min": int(gg[:, 2].min()), "NSats_p50": r(np.median(gg[:, 2]), 0), "HDop_maks": r(gg[:, 3].max(), 2), "HDop_p50": r(np.median(gg[:, 3]), 2), "Status_min": int(gg[:, 1].min()),
                      "HDop_>%.2f_n" % hg: int(len(kot)), "HDop_>esik_t": [r(kot[0, 0], 1), r(kot[-1, 0], 1)] if len(kot) else None}
    ekf["yaw_reset_t"] = [r(tt, 1) for tt, i in A["EV"] if i == 62 and t0 <= tt <= t1]
    u["ekf"] = ekf
    mb = A["MOTB"]; mbm = (mb[:, 0] >= t0) & (mb[:, 0] <= t1); m_ = mb[mbm]
    if len(m_): u["motb"] = {"ThLimit_maks": r(m_[:, 3].max(), 3), "ThrAvMx_min": r(m_[:, 4].min(), 3), "LiftMax_ort": r(m_[:, 1].mean(), 3), "FailFlags_degerler": sorted(set(int(v_) for v_ in m_[:, 6])), "not": "FailFlags bit0=thrust_boost (itki kaybi telafisi), bit1=thrust_balanced; 2 = normal"}
    pw = A["POWR"]; pwm_ = pw[(pw[:, 0] >= t0) & (pw[:, 0] <= t1)]
    if len(pwm_): u["powr"] = {"Vcc_min": r(pwm_[:, 1].min(), 2), "Vcc_maks": r(pwm_[:, 1].max(), 2), "VServo_min": r(pwm_[:, 2].min(), 2), "Flags_degerler": sorted(set(int(v_) for v_ in pwm_[:, 3])), "not": "MAV_POWER_STATUS bitleri: 1 brick, 2 servo, 4 usb, 8/16 periph overcurrent, 128 changed"}
    # --- olaylar
    ol = []
    for tt, i in A["EV"]:
        if t0 - 0.5 <= tt <= t1 + 0.5: ol.append([r(tt, 2), "EV", EV_AD.get(i, "EV%d" % i)])
    for tt, s, e in A["ERR"]:
        if t0 - 0.5 <= tt <= t1 + 0.5: ol.append([r(tt, 2), "ERR", "%s=%d" % (ERR_SUB.get(s, "SUB%d" % s), e)])
    for tt, md, rsn in A["MODE"]:
        if t0 - 0.5 <= tt <= t1 + 0.5: ol.append([r(tt, 2), "MODE", MODE_AD.get(md, str(md))])
    for tt, s, me, fo in A["ARM"]:
        if t0 - 0.5 <= tt <= t1 + 0.5: ol.append([r(tt, 2), "ARM", "%s yontem=%s" % ("ARM" if s else "DISARM", ARM_YONTEM.get(me, me))])
    for tt, s in A["MSG"]:
        if t0 - 0.5 <= tt <= t1 + 0.5: ol.append([r(tt, 2), "MSG", s])
    ol.sort(key=lambda x: x[0]); u["olaylar"] = ol
    u["failsafe"] = [o for o in ol if ("FS_" in o[2] or "Failsafe" in o[2] or "CRASH" in o[2] or "Crash" in o[2])]
    return u


def temizle(o):
    if isinstance(o, dict): return {k: temizle(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, list): return [temizle(v) for v in o]
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.bool_): return bool(o)
    return o


# ---------------------------------------------------------------- ana
sonuc = {"meta": {"konfigurasyon": "D) 4S + 9x5x3 (9 inc, 5 pitch, 3 pal) - 15 Eylul 2026 sabahi; pil/pervane/kutle LOGDA YOK, kullanici beyani",
                  "uretim_zamani": datetime.datetime.now().isoformat(timespec="seconds"), "python": sys.version.split()[0], "numpy": np.__version__,
                  "zaman_ekseni": "TimeUS/1e6 mutlak (tum_loglar.json ile ayni)",
                  "olcutler": {"motorlu_ThO_esik": THO_MOTORLU, "kisa_sicrama_s": KISA_S, "aski": {"alt_min_m": ASKI_ALT_MIN, "vz_maks_ms": ASKI_VZ, "ThO": list(ASKI_THO), "en_az_ornek": ASKI_EN_AZ, "vz_kaynak": "CTUN.Alt turevi (np.gradient), 5 ornek hareketli ortalama"},
                               "alt_taban": "arm sonrasi ilk 1 s CTUN.Alt medyani", "rcou_arm_esik": RCOU_ESIK, "motor_kanallari": "SERVOn_FUNCTION 33..36 -> C9..C12"}},
         "loglar": []}
loglar_A = {}
for fn in LOGLAR:
    full = os.path.join(ROOT, fn)
    A = oku(full); loglar_A[fn] = A
    P = pencereler(A)
    L = {"dosya": fn, "sha256": sha256(full), "bayt": os.path.getsize(full), "yazilim": next((s for t, s in A["MSG"] if "ArduCopter" in s), None),
         "log_t_ilk": r(A["CTUN"][0, 0], 2), "log_t_son": r(A["CTUN"][-1, 0], 2), "log_suresi_s": r(A["CTUN"][-1, 0] - A["CTUN"][0, 0], 1),
         "hucre": {"n": 4, "V_ilk": r(A["BAT"][0, 1], 2), "V_ilk_hucre": r(A["BAT"][0, 1] / 4, 3), "dayanak": "V_ilk/4 = 3.2..4.3 V araligina 4 uyar (3S: >4.3 V/hucre olurdu)"},
         "kullanici_beyani": {"etiket": "D", "pil": "4S", "pervane": "9x5x3", "kaynak": "kullanici_beyani"},
         "mesaj_n": {k: int(A["sayac"].get(k, 0)) for k in ("CTUN", "BAT", "VIBE", "RCOU", "ATT", "RATE", "IMU", "XKF4", "PSCD", "MOTB", "EV", "ARM", "MODE", "ERR", "MSG", "PARM", "ESC", "RPM", "ISBH")},
         "DSF_dusurulen_toplam": int(A["DSF"][:, 1].sum()) if len(A["DSF"]) else None,
         "imu_hz": r(1.0 / np.median(np.diff(A["IMU"][A["IMU"][:, 1] == 0][:, 0])), 2),
         "parm": {k: A["parm"].get(k) for k in ("MOT_THST_HOVER", "MOT_HOVER_LEARN", "MOT_THST_EXPO", "MOT_SPIN_MIN", "MOT_SPIN_ARM", "MOT_SPIN_MAX", "MOT_BAT_VOLT_MAX", "MOT_BAT_VOLT_MIN", "BATT_CAPACITY", "BATT_LOW_VOLT", "BATT_CRT_VOLT",
                                                 "INS_HNTCH_ENABLE", "INS_GYRO_FILTER", "INS_ACCEL_FILTER", "INS_LOG_BAT_MASK", "LOG_BITMASK", "FS_GCS_ENABLE", "FS_OPTIONS", "FS_THR_ENABLE", "FS_CRASH_CHECK", "FS_VIBE_ENABLE", "FS_EKF_THRESH",
                                                 "PSC_ACCZ_P", "PSC_ACCZ_I", "PILOT_SPEED_UP", "PILOT_ACCEL_Z", "THR_DZ", "RC3_MIN", "RC3_MAX", "RC3_DZ", "GPS_HDOP_GOOD", "EK3_MAG_CAL", "RCMAP_THROTTLE", "RC6_OPTION", "EK3_SRC1_YAW", "SERVO9_FUNCTION", "SERVO10_FUNCTION", "SERVO11_FUNCTION", "SERVO12_FUNCTION",
                                                 "SERVO1_FUNCTION", "SERVO2_FUNCTION", "SERVO3_FUNCTION", "SERVO4_FUNCTION", "STAT_FLTTIME", "STAT_BOOTCNT")},
         "MOT_THST_HOVER_kayitlari": [[r(t, 2), r(v, 6)] for t, v in A["parm_seri"].get("MOT_THST_HOVER", [])],
         "STAT_FLTTIME_kayitlari": [[r(t, 1), v] for t, v in A["parm_seri"].get("STAT_FLTTIME", [])],
         "ucuslar": []}
    for k, p in enumerate(P, 1):
        u = ucus_analiz(A, p, k, fn); u["_A"] = A
        L["ucuslar"].append(u)
    if not any(s == 1 for _, s, _, _ in A["ARM"]):
        L["not"] = "ARM(ArmState=1)/EV10 kaydi YOK; DSF.Dp=%s (dusurulen mesaj yok). MODE(STAB) t=%.2f + 2 s sonra EV57 MOTORS_INTERLOCK_ENABLED (arming delay) -> arm ~t=%.2f; pencere RCOU C9-C12>%d'den turetildi. STAT_FLTTIME %s ile ucus suresi tutarli." % (
            L["DSF_dusurulen_toplam"], [t for t, m, _ in A["MODE"] if 60 < t < 100][0] if any(60 < t < 100 for t, m, _ in A["MODE"]) else -1,
            [t for t, i in A["EV"] if i == 57][0] - 2.0 if any(i == 57 for t, i in A["EV"]) else -1, RCOU_ESIK, L["STAT_FLTTIME_kayitlari"])
    L["ozet"] = {"ucus_n": sum(1 for u in L["ucuslar"] if u["tur"] == "ucus"), "kisa_sicrama_n": sum(1 for u in L["ucuslar"] if u["tur"] == "kisa_sicrama"),
                 "arm_yalniz_n": sum(1 for u in L["ucuslar"] if u["tur"] == "arm_yalniz"), "toplam_motorlu_s": r(sum(u["motorlu_s"] for u in L["ucuslar"]), 1),
                 "toplam_aski_s": r(sum(u["aski_s"] for u in L["ucuslar"]), 1)}
    sonuc["loglar"].append(L)

# ---------------------------------------------------------------- havuz (konfig D, yalniz 'ucus')
ucuslar = [(L, u) for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus"]
ThO_h = np.concatenate([u["_ThO"][u["_aski_mask"]] for _, u in ucuslar])
alt_h = np.concatenate([u["_alt"][u["_aski_mask"]] for _, u in ucuslar])
V_h = []; I_h = []; P_h = []; vibe_h = {0: [], 1: []}
for L, u in ucuslar:
    A = u["_A"]; tc = u["_tc"]; ta = tc[u["_aski_mask"]]
    b = A["BAT"]; j = np.clip(np.searchsorted(b[:, 0], ta), 0, len(b) - 1); V_h.append(b[j, 1]); I_h.append(b[j, 3]); P_h.append(b[j, 1] * b[j, 3])
    v = A["VIBE"]
    for inst in (0, 1):
        x = v[v[:, 1] == inst]; jj = np.clip(np.searchsorted(x[:, 0], ta), 0, len(x) - 1); vibe_h[inst].append(x[jj][:, 2:5])
V_h = np.concatenate(V_h); I_h = np.concatenate(I_h); P_h = np.concatenate(P_h)
vb = {inst: np.vstack(vibe_h[inst]) for inst in (0, 1)}; vb_all = np.vstack([vb[0], vb[1]])
sag = [u["bat"]["sarkma_V"] for _, u in ucuslar]
havuz = {"ucus_n": len(ucuslar), "kisa_sicrama_n": sum(1 for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "kisa_sicrama"),
         "arm_yalniz_n": sum(1 for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "arm_yalniz"),
         "aski_toplam_s": r(len(ThO_h) * 0.1, 1), "aski_n": int(len(ThO_h)),
         "aski_ThO": istat(ThO_h), "aski_alt_m": istat(alt_h),
         "aski_V": istat(V_h), "aski_V_hucre_ort": r(V_h.mean() / 4), "aski_I": istat(I_h), "aski_P_W": istat(P_h),
         "aski_mAh_per_s": r(I_h.mean() / 3.6, 2), "aski_mAh_per_dk": r(I_h.mean() / 3.6 * 60, 0),
         "gerilim_sarkmasi": {"ucus_basi_V": [u["bat"]["V_bas"] for _, u in ucuslar], "V_min": [u["bat"]["V_min"] for _, u in ucuslar],
                              "sarkma_V": sag, "sarkma_V_hucre": [r(s / 4) for s in sag], "sarkma_ort_V": r(np.mean(sag), 2), "sarkma_ort_V_hucre": r(np.mean(sag) / 4, 3),
                              "V_min_en_dusuk": min(u["bat"]["V_min"] for _, u in ucuslar), "V_min_en_dusuk_hucre": r(min(u["bat"]["V_min"] for _, u in ucuslar) / 4, 3),
                              "BATT_LOW_VOLT_param": sonuc["loglar"][0]["parm"]["BATT_LOW_VOLT"], "not": "BATT_LOW_VOLT=10.0 V ve CRT 9.0 V 3S degerleri; 4S'te (16 V) hic tetiklenmez -> 4S icin 14.0/13.2 V (3.5/3.3 V/hucre) gerekir"},
         "vibe_aski": {"IMU0": {ax: istat(vb[0][:, i]) for i, ax in enumerate("XYZ")}, "IMU1": {ax: istat(vb[1][:, i]) for i, ax in enumerate("XYZ")},
                       "birlesik": {ax: istat(vb_all[:, i]) for i, ax in enumerate("XYZ")}},
         "clip_toplam_ucus": int(sum(sum(c["artis"] for c in u["vibe"]["clip"].values()) for _, u in ucuslar)),
         "clip_toplam_kisa_sicrama": int(sum(sum(c["artis"] for c in u["vibe"]["clip"].values()) for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "kisa_sicrama")),
         "ucus_suresi_tahmini": {"durum": "HESAPLANMADI: 4S pil kapasitesi bilinmiyor (BATT_CAPACITY=8000 mAh parametresi 3S pilin degeridir, degistirilmemis)",
                                 "formul": "t_dk = 0.8 * C_mAh / (I_aski_A * 1000/60)", "I_aski_A": r(I_h.mean(), 1), "s_per_1000mAh_%80": r(0.8 * 1000 / (I_h.mean() / 3.6), 0),
                                 "kosullu_hesap_dk": {"C=%d mAh" % c: r(0.8 * c / (I_h.mean() * 1000 / 60), 1) for c in (4000, 5000, 6000, 8000)},
                                 "not": "kosullu satirlar HESAPtir, olcum degil; C kullanici beyaniyla doldurulunca gecerli"}}
sonuc["havuz_D"] = havuz

# MOT_THST_HOVER degerlendirmesi
thh = {"deger_log": [L["parm"]["MOT_THST_HOVER"] for L in sonuc["loglar"]],
       "kaynak": "14 Eylul 21-10-34 (konfig C, 3S+9x5x3) ucusu sonunda 0.498->0.506 ogrenildi (tum_loglar.json); 15 Eylul loglari 0.506 ile basliyor -> 4S'e AIT DEGIL, 3S+9x5x3'ten kalma",
       "aski_ThO_4S_ort": havuz["aski_ThO"]["ort"], "aski_ThO_4S_p50": havuz["aski_ThO"]["p50"],
       "fark": r(sonuc["loglar"][0]["parm"]["MOT_THST_HOVER"] - havuz["aski_ThO"]["ort"], 3),
       "fark_pct": r(100 * (sonuc["loglar"][0]["parm"]["MOT_THST_HOVER"] / havuz["aski_ThO"]["ort"] - 1), 1),
       "ogrenme": [{"log": L["dosya"].split("/")[-1], "ucus": u["no"], "aski_s": u["aski_s"], **u["hover_ogrenme"]} for L, u in ucuslar],
       "sonuc": None}
sonuc["MOT_THST_HOVER"] = thh

# ---------------------------------------------------------------- konfig karsilastirma (tum_loglar.json)
tl = json.load(open(os.path.join(ROOT, "results/ucus_analiz_20260915/tum_loglar.json"), encoding="utf-8"))
kk = {}
for l in tl["loglar"]:
    if l.get("kopya_of") or "KOPYA_OF" in l: continue
    et = (l.get("kullanici_beyani") or {}).get("etiket")
    if et not in ("A", "B", "C", "D"): continue
    d = kk.setdefault(et, {"ucus_n": 0, "kisa_n": 0, "aski_s": 0.0, "ThO_w": 0.0, "vZ_w": 0.0, "I_w": 0.0, "vZ_kisa": [], "ThH": [], "V_ilk": []})
    d["V_ilk"].append(l["hucre"]["V_ilk"])
    for u in l["ucuslar"]:
        if u["tur"] == "ucus" and u.get("aski"):
            s = u["aski_s"]; d["ucus_n"] += 1; d["aski_s"] += s; d["ThO_w"] += u["aski"]["ThO_p50"] * s; d["vZ_w"] += u["vibe"]["aski"]["Z"] * s
            if u["bat"].get("aski"): d["I_w"] += u["bat"]["aski"]["I_ort"] * s; d["V_w"] = d.get("V_w", 0.0) + u["bat"]["aski"]["V_ort"] * s; d["P_w"] = d.get("P_w", 0.0) + u["bat"]["aski"]["P_W"] * s
            d["ThH"].append(u["ThH_son"])
        elif u["tur"] == "kisa_sicrama":
            d["kisa_n"] += 1; d["vZ_kisa"].append(u["vibe"]["Z"]["p95"])
konf = {}
for et in "ABCD":
    d = kk.get(et)
    if not d: continue
    konf[et] = {"pil_pervane": tl["meta"]["konfig_beyani"][et]["pil"] + " + " + tl["meta"]["konfig_beyani"][et]["pervane"], "ucus_n": d["ucus_n"], "kisa_sicrama_n": d["kisa_n"], "aski_toplam_s": r(d["aski_s"], 1),
                "aski_ThO_p50_agirlikli": r(d["ThO_w"] / d["aski_s"], 3) if d["aski_s"] else None, "aski_VibeZ_ort_agirlikli": r(d["vZ_w"] / d["aski_s"], 1) if d["aski_s"] else None,
                "aski_I_ort_agirlikli": r(d["I_w"] / d["aski_s"], 1) if d["aski_s"] else None, "aski_V_ort_agirlikli": r(d.get("V_w", 0) / d["aski_s"], 2) if d["aski_s"] else None, "aski_P_W_agirlikli": r(d.get("P_w", 0) / d["aski_s"], 0) if d["aski_s"] else None, "kisa_sicrama_VibeZ_p95_ort": r(np.mean(d["vZ_kisa"]), 1) if d["vZ_kisa"] else None,
                "ThH_son_araligi": [min(d["ThH"]), max(d["ThH"])] if d["ThH"] else None, "V_ilk_araligi": [min(d["V_ilk"]), max(d["V_ilk"])]}
# D'yi bu analizin ham degerleriyle ez (tum_loglar ile capraz)
konf["D"]["bu_analiz"] = {"aski_ThO_p50": havuz["aski_ThO"]["p50"], "aski_ThO_ort": havuz["aski_ThO"]["ort"], "aski_VibeZ_ort_birlesik": havuz["vibe_aski"]["birlesik"]["Z"]["ort"], "aski_I_ort": havuz["aski_I"]["ort"]}
sonuc["konfig_karsilastirma"] = {"kaynak": "tum_loglar.json (askı_s agirlikli, yalniz tur=ucus; kisa sicramalar ayri sutunda)", "konfig": konf}

# ---------------------------------------------------------------- grafikler
graf = []
def shade(ax, L):
    for u in L["ucuslar"]:
        col = {"ucus": "#e8eef8", "kisa_sicrama": "#fbe6dc", "arm_yalniz": "#ececea"}[u["tur"]]
        ax.axvspan(u["arm_t"], u["disarm_t"], color=col, lw=0, zorder=0)

for L in sonuc["loglar"]:
    A = L["ucuslar"][0]["_A"]; tag = L["dosya"].split("/")[-1].replace(".bin", "").replace(" ", "_")
    tmin = min(u["arm_t"] for u in L["ucuslar"]) - 8; tmax = max(u["disarm_t"] for u in L["ucuslar"]) + 8
    ct = A["CTUN"]; b = A["BAT"]
    # 1) zaman: ThO / akim / gerilim / irtifa
    fig, ax = plt.subplots(4, 1, figsize=(11, 8.5), sharex=True)
    for a in ax: shade(a, L)
    ax[0].plot(ct[:, 0], ct[:, 2], color=C[0], label="CTUN.ThO")
    ax[0].plot(ct[:, 0], ct[:, 3], color=C[1], ls="--", label="CTUN.ThH (MOT_THST_HOVER)")
    for u in L["ucuslar"]:
        if u["aski"] is not None:
            ax[0].plot(u["_tc"][u["_aski_mask"]], u["_ThO"][u["_aski_mask"]], ".", color=C[2], ms=4, label="askı örneği" if u["no"] == min(x["no"] for x in L["ucuslar"] if x["aski"]) else None)
    ax[0].set_ylabel("gaz (0-1)"); ax[0].set_ylim(0, 0.8); ax[0].legend(loc="upper right", ncol=3)
    ax[1].plot(b[:, 0], b[:, 3], color=C[0]); ax[1].set_ylabel("BAT.Curr (A)")
    ax[2].plot(b[:, 0], b[:, 1], color=C[0]); ax[2].set_ylabel("BAT.Volt (V)")
    for u in L["ucuslar"]:
        if u["tur"] != "arm_yalniz": ax[2].annotate("min %.2f V" % u["bat"]["V_min"], (u["bat"]["V_min_t"], u["bat"]["V_min"]), textcoords="offset points", xytext=(4, -10), fontsize=8, color=TXT2)
    ax[3].plot(ct[:, 0], ct[:, 5] - (L["ucuslar"][0]["alt_taban_m"] or 0), color=C[0]); ax[3].set_ylabel("CTUN.Alt - taban (m)"); ax[3].set_xlabel("t (s, TimeUS)")
    ax[3].axhline(ASKI_ALT_MIN, color=TXT2, lw=0.8, ls=":")
    ax[0].set_xlim(tmin, tmax)
    ttl = "%s — %s: gaz / akım / gerilim / irtifa (mavi zemin: uçuş, turuncu: kısa sıçrama, gri: yalnız arm)" % (tag.replace("_", " "), "4S + 9x5x3 (kullanıcı beyanı)")
    fig.suptitle(ttl, fontsize=10); fig.tight_layout()
    p = os.path.join(OUT, "zaman_ThO_akim_gerilim_%s.png" % tag); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)
    # 2) VIBE
    v = A["VIBE"]
    fig, ax = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    for i, axn in enumerate("XYZ"):
        shade(ax[i], L)
        for inst in (0, 1):
            x = v[v[:, 1] == inst]; ax[i].plot(x[:, 0], x[:, 2 + i], color=C[inst], label="IMU%d" % inst, lw=1.0)
        ax[i].set_ylabel("Vibe%s (m/s²)" % axn)
        if i == 2: ax[i].axhline(30, color=C[7], lw=0.8, ls=":"); ax[i].text(tmin + 0.5, 30.5, "30 m/s² (ArduPilot 'yüksek' eşiği)", fontsize=7, color=TXT2)
    for u in L["ucuslar"]:
        for inst, cl in ((0, u["vibe"]["clip"].get("IMU0")), (1, u["vibe"]["clip"].get("IMU1"))):
            if cl:
                for tt, n in cl["zamanlar"]: ax[2].plot(tt, 58, "v", color=C[7], ms=6)
    ax[2].plot([], [], "v", color=C[7], label="clip artışı"); ax[2].legend(loc="upper right", ncol=3); ax[0].legend(loc="upper right", ncol=2)
    ax[2].set_xlabel("t (s, TimeUS)"); ax[0].set_xlim(tmin, tmax); ax[2].set_ylim(0, 62)
    fig.suptitle("%s — VIBE X/Y/Z (IMU0 mavi, IMU1 turuncu); ▼ = Clip sayacı artışı" % tag.replace("_", " "), fontsize=10); fig.tight_layout()
    p = os.path.join(OUT, "vibe_xyz_%s.png" % tag); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)
    # 3) RCOU motorlar
    rc = A["RCOU"]; mk = L["ucuslar"][0]["_mot_kanal"]
    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    shade(ax[0], L); shade(ax[1], L)
    for i, m in enumerate(("M1", "M2", "M3", "M4")):
        ax[0].plot(rc[:, 0], rc[:, mk[m]], color=C[i], label="%s (C%d)" % (m, mk[m]), lw=1.0)
    ax[0].set_ylabel("RCOU PWM (µs)"); ax[0].legend(loc="upper right", ncol=4); ax[0].set_ylim(950, 1900)
    for i, ch in enumerate((1, 2, 3, 4)):
        ax[1].plot(rc[:, 0], rc[:, ch], color=C[i], label="C%d (SERVO%d_FUNCTION=%d)" % (ch, ch, A["parm"]["SERVO%d_FUNCTION" % ch]), lw=1.0)
    ax[1].set_ylabel("MAIN C1-C4 PWM (µs)"); ax[1].legend(loc="upper right", ncol=4, fontsize=7); ax[1].set_ylim(950, 1900); ax[1].set_xlabel("t (s, TimeUS)")
    ax[0].set_xlim(tmin, tmax)
    fig.suptitle("%s — motor çıkışları: üst = gerçek motorlar (AUX C9-C12 → M1..M4), alt = MAIN C1-C4 (M2,M2,M1,M2 kopyaları; aracın analiz ettiği kanallar)" % tag.replace("_", " "), fontsize=9); fig.tight_layout()
    p = os.path.join(OUT, "rcou_motorlar_%s.png" % tag); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)

# 4) FFT askida (3 ucus) + yer/rolanti taban
fig, ax = plt.subplots(len(ucuslar) + 1, 1, figsize=(10, 2.4 * (len(ucuslar) + 1)), sharex=True)
for i, (L, u) in enumerate(ucuslar):
    for inst in (0, 1):
        if "_fft_%d" % inst in u:
            f, amp, fs = u["_fft_%d" % inst]; ax[i].plot(f, amp, color=C[inst], lw=1.0, label="IMU%d AccZ" % inst)
    ax[i].set_title("%s uçuş %d — askı dilimi %s (%.1f s), IMU %.1f Hz → Nyquist %.1f Hz" % (L["dosya"].split("/")[-1], u["no"], u["imu_fft"]["dilim_t"], u["imu_fft"]["IMU0"]["AccZ"]["sure_s"], u["imu_fft"]["IMU0"]["AccZ"]["fs_hz"], u["imu_fft"]["IMU0"]["AccZ"]["nyquist_hz"]), fontsize=8)
    ax[i].set_ylabel("genlik (m/s²)"); ax[i].legend(loc="upper right")
    for tp in u["imu_fft"]["IMU0"]["AccZ"]["tepeler"][:3]:
        ax[i].annotate("%.1f Hz" % tp["f_hz"], (tp["f_hz"], tp["genlik"]), textcoords="offset points", xytext=(3, 3), fontsize=7, color=TXT2)
# taban: 11-18-16 pencere 1 (yalniz arm, rolanti)
Lb = sonuc["loglar"][1]; ub = next(u for u in Lb["ucuslar"] if u["tur"] == "arm_yalniz"); Ab = ub["_A"]; im = Ab["IMU"]
taban_fft = {}
for inst in (0, 1):
    x = im[(im[:, 1] == inst) & (im[:, 0] >= ub["arm_t"] + 2.5) & (im[:, 0] <= ub["disarm_t"])]
    f = fft_tepeler(x[:, 0], x[:, 7])
    if f:
        ax[-1].plot(f["_f"], f["_amp"], color=C[inst], lw=1.0, label="IMU%d AccZ" % inst); taban_fft["IMU%d" % inst] = {k: v for k, v in f.items() if not k.startswith("_")}
ax[-1].set_title("taban: %s pencere %d — yerde, armlı rölanti (motor ~1100 µs), %.1f s" % (Lb["dosya"].split("/")[-1], ub["no"], ub["disarm_t"] - ub["arm_t"] - 2.5), fontsize=8)
ax[-1].set_ylabel("genlik (m/s²)"); ax[-1].set_xlabel("frekans (Hz)"); ax[-1].legend(loc="upper right"); ax[-1].set_xlim(0, 12.6)
fig.suptitle("IMU AccZ genlik spektrumu (Hann, ortalama çıkarılmış) — 25 Hz örnekleme: pervane temel frekansı (>100 Hz) ÇÖZÜLEMEZ, katlanır", fontsize=9); fig.tight_layout()
p = os.path.join(OUT, "fft_aski_AccZ.png"); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)
sonuc["fft_taban_rolanti"] = {"pencere": [ub["arm_t"], ub["disarm_t"]], **taban_fft}

# 5) kisa sicrama yakinlastirma
for L in sonuc["loglar"]:
    for u in L["ucuslar"]:
        if u["tur"] != "kisa_sicrama": continue
        A = u["_A"]; t0, t1 = u["arm_t"] - 2, u["disarm_t"] + 2; tag = L["dosya"].split("/")[-1].replace(".bin", "").replace(" ", "_")
        ct = A["CTUN"]; cm = (ct[:, 0] >= t0) & (ct[:, 0] <= t1); v = A["VIBE"]; rc = A["RCOU"]; at = A["ATT"]
        fig, ax = plt.subplots(5, 1, figsize=(10, 9), sharex=True)
        ax[0].plot(ct[cm, 0], ct[cm, 2], color=C[0], label="ThO"); ax[0].axhline(THO_MOTORLU, color=TXT2, ls=":", lw=0.8); ax[0].set_ylabel("ThO"); ax[0].legend(loc="upper right")
        ax[1].plot(ct[cm, 0], ct[cm, 5] - u["alt_taban_m"], color=C[0], label="CTUN.Alt-taban"); ax[1].plot(ct[cm, 0], ct[cm, 6] - np.median(ct[cm, 6][:10]), color=C[1], label="BAlt-taban", lw=0.9); ax[1].set_ylabel("irtifa (m)"); ax[1].legend(loc="upper right")
        for inst in (0, 1):
            x = v[(v[:, 1] == inst) & (v[:, 0] >= t0) & (v[:, 0] <= t1)]; ax[2].plot(x[:, 0], x[:, 4], color=C[inst], label="VibeZ IMU%d" % inst)
            ax[3].step(x[:, 0], x[:, 5] - x[0, 5], color=C[inst], where="post", label="Clip artışı IMU%d" % inst)
        ax[2].set_ylabel("VibeZ (m/s²)"); ax[2].legend(loc="upper right"); ax[3].set_ylabel("clip (adet)"); ax[3].legend(loc="upper right")
        mk = u["_mot_kanal"]; rm = (rc[:, 0] >= t0) & (rc[:, 0] <= t1)
        for i, m in enumerate(("M1", "M2", "M3", "M4")): ax[4].plot(rc[rm, 0], rc[rm, mk[m]], color=C[i], label=m, lw=1.0)
        ax[4].set_ylabel("RCOU (µs)"); ax[4].legend(loc="upper right", ncol=4); ax[4].set_xlabel("t (s, TimeUS)")
        for tt, ty, s in u["olaylar"]:
            if ty in ("EV", "MODE"):
                ax[0].axvline(tt, color=TXT2, lw=0.6, ls="--"); ax[0].text(tt, 0.72, s, fontsize=6, rotation=90, va="top", color=TXT2)
        ax[0].set_ylim(0, 0.8)
        fig.suptitle("%s pencere %d — KISA SIÇRAMA (STAB, motorlu %.1f s): yer teması / VIBE / clip zamanlaması" % (tag.replace("_", " "), u["no"], u["motorlu_s"]), fontsize=9); fig.tight_layout()
        p = os.path.join(OUT, "kisa_sicrama_%s_p%d.png" % (tag, u["no"])); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)

# 6) konfig karsilastirma
ets = [e for e in "ABCD" if e in konf]
fig, ax = plt.subplots(1, 3, figsize=(11, 3.6))
KISA = {"A": "3S+1045", "B": "4S+1045", "C": "3S+9x5x3", "D": "4S+9x5x3"}
lab = ["%s\n%s" % (e, KISA[e]) for e in ets]
for i, (key, yl, ttl) in enumerate((("aski_ThO_p50_agirlikli", "ThO askı p50", "askı gazı (askı-süresi ağırlıklı p50)"), ("aski_VibeZ_ort_agirlikli", "VibeZ ort (m/s²)", "askıda VibeZ ortalaması"), ("aski_I_ort_agirlikli", "akım (A)", "askı akımı"))):
    vals = [konf[e][key] for e in ets]
    for j, e in enumerate(ets):
        vv = vals[j]
        if vv is None:
            ax[i].bar(j, 0, color="none"); ax[i].text(j, 0.02, "askı yok\n(yalnız sıçrama)", ha="center", va="bottom", fontsize=7, color=TXT2)
        else:
            ax[i].bar(j, vv, color=C[j], width=0.6); ax[i].text(j, vv, ("%.3f" if key.startswith("aski_ThO") else "%.1f") % vv, ha="center", va="bottom", fontsize=8)
    ax[i].set_xticks(range(len(ets))); ax[i].set_xticklabels(lab, fontsize=7); ax[i].set_ylabel(yl); ax[i].set_title(ttl, fontsize=9); ax[i].grid(axis="x", visible=False)
fig.suptitle("Konfigürasyon karşılaştırması (tum_loglar.json, yalnız tur=uçuş; askı_s: %s)" % ", ".join("%s=%s s" % (e, konf[e]["aski_toplam_s"]) for e in ets), fontsize=9); fig.tight_layout()
p = os.path.join(OUT, "konfig_karsilastirma.png"); fig.savefig(p, dpi=140); plt.close(fig); graf.append(p)

sonuc["grafikler"] = [x.replace("\\", "/") for x in graf]
# ---------------------------------------------------------------- bulgular (sayilar yukaridaki hesaplardan)
H = havuz; L1, L2 = sonuc["loglar"]; u1 = L1["ucuslar"][0]; u2, u3, u4 = L2["ucuslar"][1], L2["ucuslar"][2], L2["ucuslar"][3]
thh["sonuc"] = ("MOT_THST_HOVER=%.3f bu konfigurasyona AIT DEGIL: 14 Eylul 21-10-34 (3S+9x5x3) sonunda ogrenilmis deger; 4S aski gazi p50=%.3f (n=%d, %.1f s), fark %+.1f%%. "
                "Ogrenme 3 ucusta da engellendi: Copter::update_throttle_hover 'is_zero(vel_desired.z)' kosulu saglanmadi (PSCD.DVD |p50| %.2f/%.2f/%.2f m/s); "
                "neden gaz cubugu: 11-14-33 ucusunda RCIN.C3 ort %d us (olu bolge ustu %d us), olu bolge ici %%%.0f -> surekli +%.2f m/s tirmanma istegi (irtifa egimi %.3f m/s); "
                "11-18-16 ucus 2/4: olu bolge ici %%%.0f/%%%.0f ama en uzun sabit dilim %.1f/%.1f s. Ucus 4'te 0.3 s uygun dilim -> gercek degisim %+.4f (sim %+.4f). "
                "DVD kosulu olmasaydi sim ~%.3f'e inerdi.") % (
    L1["parm"]["MOT_THST_HOVER"], H["aski_ThO"]["p50"], H["aski_n"], H["aski_toplam_s"], thh["fark_pct"],
    u1["hover_ogrenme"]["DVD_havada_abs_p50_ms"], u2["hover_ogrenme"]["DVD_havada_abs_p50_ms"], u4["hover_ogrenme"]["DVD_havada_abs_p50_ms"],
    u1["aski"]["gaz_cubugu_RCIN_C3"]["ort_us"], u1["aski"]["gaz_cubugu_RCIN_C3"]["olu_bolge_us_hesap"][1], 100 * u1["aski"]["gaz_cubugu_RCIN_C3"]["olu_bolge_ici_orani"],
    u1["hover_ogrenme"]["DVD_havada_abs_p50_ms"], u1["aski"]["alt_egim_en_uzun_dilim_ms"],
    100 * u2["aski"]["gaz_cubugu_RCIN_C3"]["olu_bolge_ici_orani"], 100 * u4["aski"]["gaz_cubugu_RCIN_C3"]["olu_bolge_ici_orani"],
    u2["aski"]["gaz_cubugu_RCIN_C3"]["en_uzun_olu_bolge_s"], u4["aski"]["gaz_cubugu_RCIN_C3"]["en_uzun_olu_bolge_s"],
    u4["hover_ogrenme"]["ThH_gercek_degisim"], u4["hover_ogrenme"]["ThH_sim_kosullu"] - u4["hover_ogrenme"]["ThH_bas"], u1["hover_ogrenme"]["ThH_sim_DVD_kosulsuz"])
sonuc["bulgular"] = [
    "GOREV ONCULU DUZELTMESI: '11-14-33 ucus yok' YANLIS. ilk tarama (tarama_ham.json) ucus_n=0 yazdi (ARM(1) kaydi olmadigi icin); ARM(1)/EV10 kaydi yok (DSF.Dp=0, mesaj dusmedi) ama MODE(STAB) t=86.67 + EV57 t=88.67 + RCOU C9-C12 1000->1100->1550 + STAT_FLTTIME 834->878 s (+44 s) -> %.1f s motorlu, %.1f s aski (en uzun kesintisiz aski dilimi %.1f s) iceren GERCEK ucus; D konfigurasyonunun EN UZUN askisi bu logda." % (u1["motorlu_s"], u1["aski_s"], u1["aski"]["en_uzun_dilim_s"]),
    "ASKI GAZI (4S+9x5x3, 3 ucus havuzu, n=%d ornek, %.1f s): ThO ort %.3f / p50 %.3f / p05 %.3f / p95 %.3f; ucus bazinda p50 %.3f / %.3f / %.3f. 3S+9x5x3 (C) p50 %.3f, 3S+1045 (A) p50 %.3f -> 4S ile ayni pervanede gaz %%%.0f dusuk." % (
        H["aski_n"], H["aski_toplam_s"], H["aski_ThO"]["ort"], H["aski_ThO"]["p50"], H["aski_ThO"]["p05"], H["aski_ThO"]["p95"], u1["aski"]["ThO"]["p50"], u2["aski"]["ThO"]["p50"], u4["aski"]["ThO"]["p50"],
        konf["C"]["aski_ThO_p50_agirlikli"], konf["A"]["aski_ThO_p50_agirlikli"], 100 * (1 - H["aski_ThO"]["p50"] / konf["C"]["aski_ThO_p50_agirlikli"])),
    thh["sonuc"],
    "ASKI AKIMI/GUCU: I ort %.1f A (p95 %.1f, maks %.1f), V ort %.2f V (%.3f V/hucre), P=V*I ort %.0f W (p95 %.0f). Ucus bazinda I %.1f/%.1f/%.1f A. Konfig C (3S+9x5x3): %.1f A, %.2f V, %.0f W; A (3S+1045): %.1f A, %.0f W. 4S'te akim C ile ayni (~%.0f A) ama gerilim %%%.0f yuksek -> guc +%%%.0f; kutle farki (4S pil) LOGDA YOK, kullanici beyani gerekir." % (
        H["aski_I"]["ort"], H["aski_I"]["p95"], H["aski_I"]["maks"], H["aski_V"]["ort"], H["aski_V_hucre_ort"], H["aski_P_W"]["ort"], H["aski_P_W"]["p95"],
        u1["bat"]["aski"]["I"]["ort"], u2["bat"]["aski"]["I"]["ort"], u4["bat"]["aski"]["I"]["ort"],
        konf["C"]["aski_I_ort_agirlikli"], konf["C"]["aski_V_ort_agirlikli"], konf["C"]["aski_P_W_agirlikli"], konf["A"]["aski_I_ort_agirlikli"], konf["A"]["aski_P_W_agirlikli"],
        H["aski_I"]["ort"], 100 * (H["aski_V"]["ort"] / konf["C"]["aski_V_ort_agirlikli"] - 1), 100 * (H["aski_P_W"]["ort"] / konf["C"]["aski_P_W_agirlikli"] - 1)),
    "GERILIM SARKMASI: ucus basi %.2f/%.2f/%.2f V -> motorlu min %.2f/%.2f/%.2f V; sarkma %.2f/%.2f/%.2f V (%.3f/%.3f/%.3f V/hucre), ort %.2f V = %.3f V/hucre; en dusuk %.2f V = %.3f V/hucre (@%.1f A). Ic direnc HESABI (V_arm_oncesi-V_aski)/(I_aski-I_arm_oncesi): %.1f/%.1f/%.1f mOhm/hucre; BAT.Res (FC tahmini) %.0f/%.0f/%.0f mOhm paket. Kalan gerilim (BAT.VoltR) askida %.2f/%.2f/%.2f V. BATT_LOW_VOLT=%.0f / CRT=%.0f V 3S degerleri -> 4S'te pil failsafe FIILEN KAPALI." % (
        u1["bat"]["V_bas"], u2["bat"]["V_bas"], u4["bat"]["V_bas"], u1["bat"]["V_min"], u2["bat"]["V_min"], u4["bat"]["V_min"],
        u1["bat"]["sarkma_V"], u2["bat"]["sarkma_V"], u4["bat"]["sarkma_V"], u1["bat"]["sarkma_V_hucre"], u2["bat"]["sarkma_V_hucre"], u4["bat"]["sarkma_V_hucre"],
        H["gerilim_sarkmasi"]["sarkma_ort_V"], H["gerilim_sarkmasi"]["sarkma_ort_V_hucre"], H["gerilim_sarkmasi"]["V_min_en_dusuk"], H["gerilim_sarkmasi"]["V_min_en_dusuk_hucre"], u4["bat"]["V_min_I"],
        u1["bat"]["aski"]["R_ic_hesap_mohm_hucre"], u2["bat"]["aski"]["R_ic_hesap_mohm_hucre"], u4["bat"]["aski"]["R_ic_hesap_mohm_hucre"],
        1000 * u1["bat"]["aski"]["BAT_Res_ort_ohm"], 1000 * u2["bat"]["aski"]["BAT_Res_ort_ohm"], 1000 * u4["bat"]["aski"]["BAT_Res_ort_ohm"],
        u1["bat"]["aski"]["VoltR_ort"], u2["bat"]["aski"]["VoltR_ort"], u4["bat"]["aski"]["VoltR_ort"], L1["parm"]["BATT_LOW_VOLT"], L1["parm"]["BATT_CRT_VOLT"]),
    "UCUS SURESI: HESAPLANMADI - 4S pil kapasitesi bilinmiyor (BATT_CAPACITY=8000 mAh parametresi 3S pilin degeri, degistirilmemis; BAT.RemPct bu yuzden anlamsiz). Tuketim hizi askida %.2f mAh/s = %.0f mAh/dk; kosullu HESAP t=0.8*C/I: C=4000 -> %.1f dk, 5000 -> %.1f dk, 6000 -> %.1f dk, 8000 -> %.1f dk. Iki logda toplam CurrTot %.0f mAh." % (
        H["aski_mAh_per_s"], H["aski_mAh_per_dk"], H["ucus_suresi_tahmini"]["kosullu_hesap_dk"]["C=4000 mAh"], H["ucus_suresi_tahmini"]["kosullu_hesap_dk"]["C=5000 mAh"], H["ucus_suresi_tahmini"]["kosullu_hesap_dk"]["C=6000 mAh"], H["ucus_suresi_tahmini"]["kosullu_hesap_dk"]["C=8000 mAh"],
        sum(u["bat"]["mAh_pencere"] for L in sonuc["loglar"] for u in L["ucuslar"])),
    "TITRESIM (askida, IMU0+IMU1 birlesik, n=%d): X ort %.1f / p95 %.1f / maks %.1f; Y %.1f / %.1f / %.1f; Z %.1f / %.1f / %.1f m/s2; clip 0 (3 ucusta). Ucus bazinda VibeZ ort %.1f -> %.1f -> %.1f (azalan). ArduPilot 30 m/s2 esiginin altinda. Konfig kiyasi (askida VibeZ ort): A 3S+1045 %.1f, C 3S+9x5x3 %.1f, D 4S+9x5x3 %.1f -> en dusuk; B 4S+1045 yalniz sicramalarda p95 %.1f ('asiri titredi' beyani ile uyumlu, ama sicrama=yer temasi karisik). 3 pal 9 inc + 4S: ayni pervane 3S'te (C) 17.9 iken 4S'te 11.9 -> dusuk PWM orani (0.55 vs ~0.65, expo 0.65 ile hesap) titresimi azaltmis gorunuyor; neden-sonuc icin hizli IMU logu gerekir." % (
        H["vibe_aski"]["birlesik"]["X"]["n"], H["vibe_aski"]["birlesik"]["X"]["ort"], H["vibe_aski"]["birlesik"]["X"]["p95"], H["vibe_aski"]["birlesik"]["X"]["maks"],
        H["vibe_aski"]["birlesik"]["Y"]["ort"], H["vibe_aski"]["birlesik"]["Y"]["p95"], H["vibe_aski"]["birlesik"]["Y"]["maks"],
        H["vibe_aski"]["birlesik"]["Z"]["ort"], H["vibe_aski"]["birlesik"]["Z"]["p95"], H["vibe_aski"]["birlesik"]["Z"]["maks"],
        u1["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["ort"], u2["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["ort"], u4["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["ort"],
        konf["A"]["aski_VibeZ_ort_agirlikli"], konf["C"]["aski_VibeZ_ort_agirlikli"], konf["D"]["aski_VibeZ_ort_agirlikli"], konf["B"]["kisa_sicrama_VibeZ_p95_ort"]),
    "KISA SICRAMA (11-18-16 pencere 3, STAB, motorlu %.1f s, alt maks %.2f m) ASKIDAN AYRI: VibeZ maks %.1f (IMU1) / %.1f (IMU0), clip IMU0 +%d, IMU1 +%d, HEPSI t=128.63'te: ThO 127.8'de 0.39 -> 128.0'da 0.07 (gaz kesildi), CRt -123 cm/s ile 0.36 m'den dusus, 128.6'da yer carpmasi (roll -2.2, pitch +2.7, M1 1150 / M2 1687 us). 127.4'te ikinci tepe (VibeZ 25, M2 1714/M1 1375) yerde spool sirasinda devrilme egilimi. -> Sert inis / yer temasi kaynakli; ucus titresimi degil. Bu pencere aski istatistiklerine dahil edilmedi." % (
        u3["motorlu_s"], u3["alt_maks_m"], u3["vibe"]["kapsam_pencere"]["IMU1"]["Z"]["maks"], u3["vibe"]["kapsam_pencere"]["IMU0"]["Z"]["maks"], u3["vibe"]["clip"]["IMU0"]["artis"], u3["vibe"]["clip"]["IMU1"]["artis"]),
    "FFT: IMU mesaji %.1f Hz (INS_LOG_BAT_MASK=0, hizli IMU yok) -> Nyquist %.1f Hz; pervane temel frekansi cozulemez (kaba hesap KV*V*PWM_orani/60 ~%.0f Hz, olcum degil; 3 pal gecis ~3x). Askida AccZ tepeleri: ucus1 0.4/8.5/6.6 Hz, ucus2 0.4/0.7/11.2 Hz, ucus4 0.5/10.7/1.0 Hz; rms %.2f/%.2f/%.2f m/s2 (yerde rolanti taban %.2f). 0.4-1 Hz = Loiter konum/tutum salinimi, 6-11 Hz bandi govde ya da katlanmis (alias) pervane icerigi - AYIRT EDILEMEZ. Kesin pervane spektrumu icin INS_LOG_BAT_MASK=1, INS_LOG_BAT_OPT=0 (on-filter) + INS_HNTCH icin FFT_ENABLE=1 onerilir." % (
        L1["imu_hz"], L1["imu_hz"] / 2, 980 * H["aski_V"]["ort"] * 0.55 / 60, u1["imu_fft"]["IMU0"]["AccZ"]["rms"], u2["imu_fft"]["IMU0"]["AccZ"]["rms"], u4["imu_fft"]["IMU0"]["AccZ"]["rms"], sonuc["fft_taban_rolanti"]["IMU0"]["rms"]),
    "MOTOR DENGESI (RCOU, GERCEK motor kanallari C9-C12: SERVO9..12_FUNCTION=36,34,33,35 -> M4,M2,M1,M3; askida ort us): ucus1 M1 %d M2 %d M3 %d M4 %d (yayilim %d), ucus2 %d/%d/%d/%d (%d), ucus4 %d/%d/%d/%d (%d). M1 (on-sag, CCW) hep en yuksek, M3 (on-sol, CW) hep en dusuk. CCW(M1+M2)-CW(M3+M4) = +%d/+%d/+%d us -> surekli yaw tork dengesizligi; RATE.YOut ort %+.3f/%+.3f/%+.3f (ucus4 p90 %.3f, maks %.3f); ucus4'te yaw cubugu ortada (RCIN.C4 ort %d us, std %.1f us) iken yaw hatasi %.1f dereceye ulasti, YDes p90 %.0f deg/s. Sag(M1+M4)-sol(M2+M3) %+d/%+d/%+d, on-arka %+d/%+d/%+d us. -> motor eksen/kol hizasi ve pervane esligi (4 adet ayni 9x5x3?) kontrol edilmeli; 6 Eylul 'M1 hasarli' notu ile birlikte degerlendirilmeli." % (
        u1["rcou"]["M_ort_pwm"]["M1"], u1["rcou"]["M_ort_pwm"]["M2"], u1["rcou"]["M_ort_pwm"]["M3"], u1["rcou"]["M_ort_pwm"]["M4"], u1["rcou"]["yayilim_pwm"],
        u2["rcou"]["M_ort_pwm"]["M1"], u2["rcou"]["M_ort_pwm"]["M2"], u2["rcou"]["M_ort_pwm"]["M3"], u2["rcou"]["M_ort_pwm"]["M4"], u2["rcou"]["yayilim_pwm"],
        u4["rcou"]["M_ort_pwm"]["M1"], u4["rcou"]["M_ort_pwm"]["M2"], u4["rcou"]["M_ort_pwm"]["M3"], u4["rcou"]["M_ort_pwm"]["M4"], u4["rcou"]["yayilim_pwm"],
        u1["rcou"]["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"], u2["rcou"]["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"], u4["rcou"]["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"],
        u1["att"]["aski_hiz"]["YOut_ort"], u2["att"]["aski_hiz"]["YOut_ort"], u4["att"]["aski_hiz"]["YOut_ort"], u4["att"]["aski_hiz"]["YOut_p90"], u4["att"]["aski_hiz"]["YOut_maks_abs"],
        u4["att"]["aski_hiz"]["RCIN_C4_yaw_cubugu"]["ort_us"], u4["att"]["aski_hiz"]["RCIN_C4_yaw_cubugu"]["std_us"], u4["att"]["aski_hiz"]["yaw_hata_maks_abs_deg"], u4["att"]["aski_hiz"]["YDes_p90_dps"],
        u1["rcou"]["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"], u2["rcou"]["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"], u4["rcou"]["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"],
        u1["rcou"]["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"], u2["rcou"]["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"], u4["rcou"]["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"]),
    "ARAC HATASI (scripts/ucus_bin_analiz.py satir 469): RCOU C1-C4 okunuyor; bu aracta SERVO1..4_FUNCTION = 34,34,33,34 (M2,M2,M1,M2 kopyalari), motorlar AUX C9-C12'de. tum_loglar.json'daki tum 'rcou' bloklari (C1=C2=C4 birebir ayni: %d/%d/%d/%d) motor dengesi olarak GECERSIZ; SERVOn_FUNCTION'dan kanal eslemesi yapilmali. Bu analiz C9-C12 kullandi." % tuple(u1["rcou"]["MAIN_C1_C4_ort_pwm_karsilastirma"]),
    "TUTUM IZLEME (askida RMS hata, ATT Des-gercek): roll %.2f/%.2f/%.2f deg, pitch %.2f/%.2f/%.2f deg (motorlu: roll %.2f/%.2f/%.2f, pitch %.2f/%.2f/%.2f); hiz halkasi roll %.1f/%.1f/%.1f, pitch %.1f/%.1f/%.1f deg/s RMS. Pitch maks |%.1f| deg (ucus1, Loiter fren/konum duzeltme). Ortalama pitch %.1f/%.1f/%.1f deg (hafif burun asagi egilim = ruzgar ya da CG). Yaw RMS %.1f/%.1f/%.1f deg (ucus2 pilot yaw komutlu, |Y| ort %.0f deg/s; ucus4 komutsuz)." % (
        u1["att"]["aski"]["roll_rms_hata_deg"], u2["att"]["aski"]["roll_rms_hata_deg"], u4["att"]["aski"]["roll_rms_hata_deg"], u1["att"]["aski"]["pitch_rms_hata_deg"], u2["att"]["aski"]["pitch_rms_hata_deg"], u4["att"]["aski"]["pitch_rms_hata_deg"],
        u1["att"]["motorlu"]["roll_rms_hata_deg"], u2["att"]["motorlu"]["roll_rms_hata_deg"], u4["att"]["motorlu"]["roll_rms_hata_deg"], u1["att"]["motorlu"]["pitch_rms_hata_deg"], u2["att"]["motorlu"]["pitch_rms_hata_deg"], u4["att"]["motorlu"]["pitch_rms_hata_deg"],
        u1["att"]["aski_hiz"]["roll_rate_rms_hata_dps"], u2["att"]["aski_hiz"]["roll_rate_rms_hata_dps"], u4["att"]["aski_hiz"]["roll_rate_rms_hata_dps"], u1["att"]["aski_hiz"]["pitch_rate_rms_hata_dps"], u2["att"]["aski_hiz"]["pitch_rate_rms_hata_dps"], u4["att"]["aski_hiz"]["pitch_rate_rms_hata_dps"],
        u1["att"]["motorlu"]["pitch_maks_abs_deg"], u1["att"]["aski"]["pitch_ort_deg"], u2["att"]["aski"]["pitch_ort_deg"], u4["att"]["aski"]["pitch_ort_deg"],
        u1["att"]["aski"]["yaw_rms_hata_deg"], u2["att"]["aski"]["yaw_rms_hata_deg"], u4["att"]["aski"]["yaw_rms_hata_deg"], u2["att"]["aski_hiz"]["Y_abs_ort_dps"]),
    "EKF SAGLIK: XKF4 (2 cekirdek) test oranlari maks SV %.2f SP %.2f SH %.2f SM %.2f (esik 1.0), innov>1 = 0, FS=0, lane switch 0 (PI hep 0), errRP maks %.3f. Her ucusta takeoff +%.0f s civari 'EKF3 in-flight yaw alignment complete' + EV62 EKF_YAW_RESET: EK3_MAG_CAL=3 (ilk tirmanista yaw sifirla) -> NORMAL, ariza degil; IYAW innov maks %.1f rad bu sifirlamanin izi. GPS: NSats %d-%d, HDop p50 %.2f; 11-14-33'te t=%.1f-%.1f (arm'dan takeoff+13 s'ye kadar) HDop > %.2f (maks %.2f) -> arm STAB'da (t=86.7), LOIT'e yerde kalkistan once gecildi (t=92.8, kalkis 101.4; kip degisimi HDop'a bakmaz, EKF konum saglikli: SP maks 0.04); inisten sonra 'PreArm: High GPS HDOP' mesajlari. XKF4.TS=48 (bit4 airspeed + bit5 drag timeout: ikisi de kullanilmayan fuzyon) kopterde sabit, ariza degil." % (
        max(c["SV_maks"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus" for c in u["ekf"]["cekirdek"].values()),
        max(c["SP_maks"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus" for c in u["ekf"]["cekirdek"].values()),
        max(c["SH_maks"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus" for c in u["ekf"]["cekirdek"].values()),
        max(c["SM_maks"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus" for c in u["ekf"]["cekirdek"].values()),
        max(c["errRP_maks"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus" for c in u["ekf"]["cekirdek"].values()),
        u1["ekf"]["yaw_reset_t"][0] - u1["motorlu_t"][0], max(u["ekf"]["innovasyon_maks_abs"]["IYAW_rad"] for L in sonuc["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus"),
        min(u["ekf"]["gps"]["NSats_min"] for L in sonuc["loglar"] for u in L["ucuslar"]), 15, u1["ekf"]["gps"]["HDop_p50"], u1["ekf"]["gps"]["HDop_>esik_t"][0], u1["ekf"]["gps"]["HDop_>esik_t"][1], 1.40, u1["ekf"]["gps"]["HDop_maks"]),
    "OLAYLAR: failsafe UCUSTA YOK. 11-18-16 t=63.75 GCS Failsafe (ERR FS_GCS=1) yerde/disarm halinde, 0.33 s sonra temizlendi (FS_GCS_ENABLE=5 Land; FS_OPTIONS=16 pilot kontrollu kiplerde GCS FS yoksayilir); crash check / thrust loss / EKF failsafe / vibe failsafe yok (MOTB FailFlags=2 normal, POWR Flags=1, Vcc %.2f-%.2f V). Inisler: 3 ucus RC ile LAND kipi (LAND_REPO_ACTIVE: pilot inis sirasinda konum duzeltti), LAND_COMPLETE + LANDED disarm. 11-18-16 t=105 'Arm: Throttle too high' (STAB arm denemesi, gaz yuksek), pencere 3 STAB ile armlandi -> sicrama. MOT_THST_HOVER 0.506 STAB'da cubuk ortasini 0.506 gaza esler (askinin 1.56 kati) -> STAB'da sert tirmanma riski." % (
        min(u["powr"]["Vcc_min"] for L in sonuc["loglar"] for u in L["ucuslar"]), max(u["powr"]["Vcc_maks"] for L in sonuc["loglar"] for u in L["ucuslar"])),
    "PARAMETRE UYUMSUZLUKLARI (4S'e gecis icin): BATT_LOW_VOLT 10.0 / BATT_CRT_VOLT 9.0 (3S) -> 4S icin 14.0 / 13.2 V; BATT_CAPACITY 8000 (3S pil) -> 4S kapasitesi girilmeli; MOT_THST_HOVER 0.506 (3S) -> 0.33 (olculen) ya da cubuk ortada >=30 s askida ogrenme; MOT_BAT_VOLT_MAX/MIN=0 (gerilim telafisi kapali: askida dThO/dV egimi %.2f/%.2f/%.2f 1/V, 1.5 V sarkma boyunca gaz ~%.3f artiyor). INS_HNTCH_ENABLE=0, INS_GYRO_FILTER=20 degismedi." % (
        u1["bat"]["aski"]["dThO_dV_egim"], u2["bat"]["aski"]["dThO_dV_egim"], u4["bat"]["aski"]["dThO_dV_egim"], -u1["bat"]["aski"]["dThO_dV_egim"] * 1.5),
]
out = temizle(sonuc)
with open(os.path.join(OUT, "ozet.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("YAZILDI", os.path.join(OUT, "ozet.json"))
print(json.dumps(out["havuz_D"], ensure_ascii=False, indent=1))
print(json.dumps(out["MOT_THST_HOVER"], ensure_ascii=False, indent=1))
print(json.dumps(out["konfig_karsilastirma"], ensure_ascii=False, indent=1))
