#!/usr/bin/env python3
"""E) 15 Eylul 2026 12-40-55 logu — TAM GAZ ucusu, derin inceleme (tek log).

Girdi : results/ucus_20260915/2026-09-15 12-40-55.bin  (kullanici: "12:41:20", 4S + 9x5x3 = D konfigu)
Kiyas : results/ucus_20260915/2026-09-15 11-18-16.bin  (D, ayni konfig, ayni sabah) — VIBE/RCOU gaz seviyesine gore
        results/ucus_20260915/2026-09-15 11-14-33.bin  (D, ek kiyas havuzu)
Cikti : bu dizin — ozet.json + PNG'ler

HER SAYI LOGDAN. Pil/pervane/kutle logda yok (kullanici beyani). Bagimlilik: pymavlink, numpy, matplotlib.
SciPy YOK. Askı ornekleme kurali: irtifa > 1 m, |vz| < 0,5 m/s, ThO 0,25-0,75. Kisa sicrama < 5 s motorlu.
"""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from pymavlink import DFReader  # noqa: E402

KOK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
LOG_E = os.path.join(KOK, "results", "ucus_20260915", "2026-09-15 12-40-55.bin")
LOG_D = [os.path.join(KOK, "results", "ucus_20260915", "2026-09-15 11-18-16.bin"),
         os.path.join(KOK, "results", "ucus_20260915", "2026-09-15 11-14-33.bin")]

THO_MOTORLU = 0.15
KISA_SICRAMA_S = 5.0
ASKI_ALT, ASKI_VZ, ASKI_THO = 1.0, 0.5, (0.25, 0.75)
ASKI_EN_AZ = 10
TAM_GAZ_THO = 0.80
RCOU_ESIK = 1050
MOTOR_FN = {33: "M1", 34: "M2", 35: "M3", 36: "M4"}
# ArduCopter FRAME_CLASS=1 (quad), FRAME_TYPE=1 (X): M1 on-sag CCW, M2 arka-sol CCW, M3 on-sol CW, M4 arka-sag CW
MOTOR_KONUM = {"M1": "on-sag CCW", "M2": "arka-sol CCW", "M3": "on-sol CW", "M4": "arka-sag CW"}
KV = 980  # SunnySky X2220 980KV — kullanici beyani, yalniz kaba HESAP
GAZ_BANTLARI = [(0.15, 0.25), (0.25, 0.50), (0.50, 0.75), (0.75, 0.90), (0.90, 1.001)]
YAPISAL_BANT = (2.0, 12.5)   # gorevde 2-15 Hz istendi; IMU 25 Hz -> 12,5 Hz'de kesilir
BANTLAR = {"0.3-2Hz": (0.3, 2.0), "2-6Hz": (2.0, 6.0), "6-12.5Hz": (6.0, 12.5)}


def r(x, n=3):
    if x is None:
        return None
    if isinstance(x, (float, np.floating)):
        if not np.isfinite(x):
            return None
        return round(float(x), n)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def oku(fn):
    log = DFReader.DFReader_binary(fn)
    D = collections.defaultdict(list); parm = {}; sayac = collections.Counter(); ver = None
    while True:
        m = log.recv_msg()
        if m is None:
            break
        ty = m.get_type(); sayac[ty] += 1
        tu = getattr(m, "TimeUS", None); t = tu / 1e6 if tu is not None else None
        if ty == "CTUN": D["CTUN"].append((t, m.ThI, m.ThO, m.ThH, m.DAlt, m.Alt, m.BAlt, m.DCRt, m.CRt))
        elif ty == "BAT":
            if int(getattr(m, "Inst", 0)) == 0: D["BAT"].append((t, m.Volt, m.VoltR, m.Curr, m.CurrTot, m.Res))
        elif ty == "VIBE": D["VIBE"].append((t, m.IMU, m.VibeX, m.VibeY, m.VibeZ, m.Clip))
        elif ty == "RCOU": D["RCOU"].append((t,) + tuple(getattr(m, "C%d" % i) for i in range(1, 15)))
        elif ty == "RCIN": D["RCIN"].append((t,) + tuple(getattr(m, "C%d" % i) for i in range(1, 9)))
        elif ty == "ATT": D["ATT"].append((t, m.DesRoll, m.Roll, m.DesPitch, m.Pitch, m.DesYaw, m.Yaw, m.ErrRP, m.ErrYaw))
        elif ty == "RATE": D["RATE"].append((t, m.RDes, m.R, m.ROut, m.PDes, m.P, m.POut, m.YDes, m.Y, m.YOut, m.ADes, m.A, m.AOut))
        elif ty == "IMU": D["IMU"].append((t, m.I, m.GyrX, m.GyrY, m.GyrZ, m.AccX, m.AccY, m.AccZ))
        elif ty == "XKF4": D["XKF4"].append((t, m.C, m.SV, m.SP, m.SH, m.SM, m.errRP))
        elif ty == "MOTB": D["MOTB"].append((t, m.LiftMax, m.BatVolt, m.ThLimit, m.ThrAvMx, m.ThrOut, m.FailFlags))
        elif ty == "PSCD": D["PSCD"].append((t, m.TPD, m.PD, m.DVD, m.TVD, m.VD, m.DAD, m.TAD, m.AD))
        elif ty == "POWR": D["POWR"].append((t, m.Vcc, m.VServo, m.Flags))
        elif ty == "DSF": D["DSF"].append((t, m.Dp))
        elif ty == "EV": D["EV"].append((t, int(m.Id)))
        elif ty == "ERR": D["ERR"].append((t, int(m.Subsys), int(m.ECode)))
        elif ty == "MODE": D["MODE"].append((t, int(m.Mode), int(m.Rsn)))
        elif ty == "ARM": D["ARM"].append((t, int(m.ArmState), int(m.Method)))
        elif ty == "MSG": D["MSG"].append((t, str(m.Message)))
        elif ty == "VER": ver = str(getattr(m, "FWS", ""))
        elif ty == "PARM":
            if m.Name not in parm: parm[m.Name] = float(m.Value)
    A = {k: np.array(v, dtype=float) for k, v in D.items() if k not in ("MSG", "EV", "ERR", "MODE", "ARM")}
    for k in ("EV", "ERR", "MODE", "ARM", "MSG"): A[k] = D[k]
    A["parm"] = parm; A["sayac"] = sayac; A["ver"] = ver
    return A


def motor_kanallari(parm):
    mk = {}
    for ch in range(1, 15):
        fn = parm.get("SERVO%d_FUNCTION" % ch)
        if fn is not None and int(fn) in MOTOR_FN and 9 <= ch <= 12:
            mk[MOTOR_FN[int(fn)]] = ch
    return mk


def ma(x, n=5):
    if len(x) < n:
        return x
    y = np.convolve(x, np.ones(n) / n, mode="same")
    for i in range(n // 2):
        y[i] = x[:i + n // 2 + 1].mean(); y[-1 - i] = x[-(i + n // 2 + 1):].mean()
    return y


def dilimler(t, mask, bosluk=0.25):
    out = []; i = 0; n = len(t)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1] and t[j + 1] - t[j] <= bosluk: j += 1
            out.append((t[i], t[j], j - i + 1)); i = j + 1
        else:
            i += 1
    return out


def istat(x):
    x = np.asarray(x, float)
    if len(x) == 0:
        return None
    return {"n": int(len(x)), "ort": r(x.mean()), "p50": r(np.percentile(x, 50)), "p05": r(np.percentile(x, 5)),
            "p95": r(np.percentile(x, 95)), "maks": r(x.max()), "min": r(x.min()), "std": r(x.std())}


def fft_spektrum(t, x, en_az_hz=0.3, k=6, arama=None):
    """Hann pencereli genlik spektrumu; tepeler (yerel maksimum) genlige gore. arama=(f0,f1) yalniz o bantta tepe."""
    if len(x) < 32:
        return None
    dtm = np.median(np.diff(t)); fs = 1.0 / dtm
    x = np.asarray(x, float); x = x - x.mean(); w = np.hanning(len(x))
    X = np.fft.rfft(x * w); f = np.fft.rfftfreq(len(x), dtm); amp = 2.0 * np.abs(X) / w.sum()
    f0, f1 = (en_az_hz, fs / 2) if arama is None else arama
    m = (f >= f0) & (f <= f1)
    idx = [i for i in range(1, len(f) - 1) if m[i] and amp[i] >= amp[i - 1] and amp[i] >= amp[i + 1]]
    idx.sort(key=lambda i: -amp[i])
    # bant RMS: dikdortgen pencereli FFT ile bant sinirli sinyal
    Xr = np.fft.rfft(x); bant_rms = {}
    for ad, (b0, b1) in BANTLAR.items():
        Y = np.where((f >= b0) & (f <= b1), Xr, 0); y = np.fft.irfft(Y, n=len(x)); bant_rms[ad] = r(float(np.sqrt(np.mean(y ** 2))))
    return {"fs_hz": r(fs, 2), "nyquist_hz": r(fs / 2, 2), "n": int(len(x)), "sure_s": r(t[-1] - t[0], 2),
            "cozunurluk_hz": r(f[1], 3), "rms": r(float(np.sqrt(np.mean(x ** 2)))), "tepe_arama_hz": [r(f0, 2), r(f1, 2)],
            "tepeler": [{"f_hz": r(f[i], 2), "genlik": r(amp[i], 4)} for i in idx[:k]], "bant_rms": bant_rms,
            "_f": f, "_amp": amp}


def sifir_gecis_hz(t, x):
    """isaret degisim sayisindan kaba salinim frekansi (ortalama cikarilmis)."""
    x = np.asarray(x, float) - np.mean(x)
    s = np.sign(x); s[s == 0] = 1
    n = int(np.sum(s[1:] != s[:-1]))
    T = t[-1] - t[0]
    return r(n / (2.0 * T), 2) if T > 0 else None


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def kes(arr, t0, t1):
    return arr[(arr[:, 0] >= t0) & (arr[:, 0] <= t1)]


def hizala(t_hedef, t_kaynak, x_kaynak):
    j = np.clip(np.searchsorted(t_kaynak, t_hedef), 0, len(t_kaynak) - 1)
    return x_kaynak[j]


def hizala_yakin(t_hedef, t_kaynak, x_kaynak):
    """en yakin zamanli ornek (RATE ayni dongude RCOU'dan ~100 ms SONRA yaziliyor: sonraki-ornek hizalamasi
    korelasyonu bozar — OLCULDU: lag0 korr -0,22, ayni-dongu korr +0,98)."""
    j = np.clip(np.searchsorted(t_kaynak, t_hedef), 1, len(t_kaynak) - 1)
    onceki = np.abs(t_kaynak[j - 1] - t_hedef) <= np.abs(t_kaynak[j] - t_hedef)
    return x_kaynak[np.where(onceki, j - 1, j)]


def hucre(V):
    aday = [n for n in range(1, 13) if 3.2 <= V / n <= 4.3]
    if not aday:
        return None, []
    n = min(aday, key=lambda k: abs(V / k - 3.8))
    return n, aday


def pencereler(A, mk):
    p = []; arm = A["ARM"]; ac = None
    for t, s, meth in arm:
        if s == 1 and ac is None: ac = (t, meth)
        elif s == 0 and ac is not None:
            p.append({"t0": ac[0], "t1": t, "kaynak": "ARM", "disarm_yontemi": int(meth)}); ac = None
    rc = A["RCOU"]; ch = sorted(mk.values()); mot = rc[:, ch].max(axis=1); t = rc[:, 0]
    seg = dilimler(t, mot > RCOU_ESIK, bosluk=2.0)
    for a, b, n in seg:
        if b - a < 1.0: continue
        if any(a < q["t1"] + 0.5 and b > q["t0"] - 0.5 for q in p): continue
        dis = [(tt, mm) for tt, s, mm in arm if s == 0 and b - 1.0 <= tt <= b + 1.0]
        p.append({"t0": a, "t1": dis[0][0] if dis else b, "kaynak": "RCOU", "disarm_yontemi": int(dis[0][1]) if dis else None})
    p.sort(key=lambda q: q["t0"])
    return p


def vibe_istat(A, t0, t1, mask_fn=None):
    """mask_fn(t) -> bool dizisi (CTUN zamanina gore). IMU0/IMU1 ayri."""
    v = kes(A["VIBE"], t0, t1); out = {}
    for inst in (0, 1):
        vi = v[v[:, 1] == inst]
        if len(vi) == 0: continue
        if mask_fn is not None:
            vi = vi[mask_fn(vi[:, 0])]
        if len(vi) == 0:
            out["IMU%d" % inst] = None; continue
        out["IMU%d" % inst] = {"X": istat(vi[:, 2]), "Y": istat(vi[:, 3]), "Z": istat(vi[:, 4]),
                               "clip_artis": int(vi[-1, 5] - vi[0, 5]) if len(vi) > 1 else 0}
    return out


def rcou_istat(A, mk, tsec):
    rc = A["RCOU"]; rt = rc[:, 0]
    m = tsec(rt); rr = rc[m]
    if len(rr) == 0:
        return None
    pmin, pmax = A["parm"].get("MOT_PWM_MIN", 1000), A["parm"].get("MOT_PWM_MAX", 2000)
    spin_max = A["parm"].get("MOT_SPIN_MAX", 0.95); ust = pmin + spin_max * (pmax - pmin)
    M = {mm: rr[:, ch] for mm, ch in mk.items()}
    ort = {mm: r(x.mean(), 1) for mm, x in M.items()}
    o = {"n": int(len(rr)), "M_ort_pwm": ort, "M_std_pwm": {mm: r(x.std(), 1) for mm, x in M.items()},
         "M_maks_pwm": {mm: r(x.max(), 0) for mm, x in M.items()}, "M_min_pwm": {mm: r(x.min(), 0) for mm, x in M.items()},
         "yayilim_pwm": r(max(ort.values()) - min(ort.values()), 1),
         "en_yuksek": max(ort, key=ort.get), "en_dusuk": min(ort, key=ort.get),
         "ust_sinir_pwm": r(ust, 0), "ust_sinirda_oran": {mm: r(float(np.mean(x >= ust - 1)), 3) for mm, x in M.items()},
         "cift_farklari_pwm": {"CCW(M1+M2)-CW(M3+M4)_yaw": r((ort["M1"] + ort["M2"]) - (ort["M3"] + ort["M4"]), 1),
                               "on(M1+M3)-arka(M2+M4)_pitch": r((ort["M1"] + ort["M3"]) - (ort["M2"] + ort["M4"]), 1),
                               "sag(M1+M4)-sol(M2+M3)_roll": r((ort["M1"] + ort["M4"]) - (ort["M2"] + ort["M3"]), 1)}}
    # anlik yayilim (ayni anda motorlar arasi maks-min) — gevsek kol tek motorda surekli sapma verir
    anlik = np.stack([M["M1"], M["M2"], M["M3"], M["M4"]], axis=1)
    o["anlik_yayilim_pwm"] = istat(anlik.max(axis=1) - anlik.min(axis=1))
    # her motorun ortalamadan sapmasi (zamanla): ortalama ve std
    sap = anlik - anlik.mean(axis=1, keepdims=True)
    o["motor_sapma_ort_pwm"] = {mm: r(sap[:, i].mean(), 1) for i, mm in enumerate(("M1", "M2", "M3", "M4"))}
    o["motor_sapma_std_pwm"] = {mm: r(sap[:, i].std(), 1) for i, mm in enumerate(("M1", "M2", "M3", "M4"))}
    return o


def att_rate_istat(A, tsec, fft=True):
    at = A["ATT"]; m = tsec(at[:, 0]); a = at[m]
    o = {}
    if len(a) >= 3:
        er = a[:, 2] - a[:, 1]; ep = a[:, 4] - a[:, 3]; ey = wrap(a[:, 6] - a[:, 5])
        o["att"] = {"n": int(len(a)), "hz": r(1 / np.median(np.diff(a[:, 0])), 1),
                    "roll_rms_hata_deg": r(np.sqrt(np.mean(er ** 2)), 2), "pitch_rms_hata_deg": r(np.sqrt(np.mean(ep ** 2)), 2),
                    "yaw_rms_hata_deg": r(np.sqrt(np.mean(ey ** 2)), 2),
                    "roll_hata_maks_abs_deg": r(np.abs(er).max(), 2), "pitch_hata_maks_abs_deg": r(np.abs(ep).max(), 2),
                    "roll_maks_abs_deg": r(np.abs(a[:, 2]).max(), 1), "pitch_maks_abs_deg": r(np.abs(a[:, 4]).max(), 1),
                    "roll_ort_deg": r(a[:, 2].mean(), 2), "pitch_ort_deg": r(a[:, 4].mean(), 2),
                    "DesRoll_maks_abs_deg": r(np.abs(a[:, 1]).max(), 1), "DesPitch_maks_abs_deg": r(np.abs(a[:, 3]).max(), 1),
                    "ErrRP_ort": r(a[:, 7].mean(), 3), "ErrRP_maks": r(a[:, 7].max(), 3),
                    "roll_hata_sifir_gecis_hz": sifir_gecis_hz(a[:, 0], er), "pitch_hata_sifir_gecis_hz": sifir_gecis_hz(a[:, 0], ep)}
        if fft:
            for ad, e in (("roll_hata", er), ("pitch_hata", ep)):
                f = fft_spektrum(a[:, 0], e)
                if f:
                    o["att"][ad + "_fft"] = {k: v for k, v in f.items() if not k.startswith("_")}
                    o["_fft_" + ad] = f
    rt = A["RATE"]; m = tsec(rt[:, 0]); q = rt[m]
    if len(q) >= 3:
        er = q[:, 2] - q[:, 1]; ep = q[:, 5] - q[:, 4]; ey = q[:, 8] - q[:, 7]
        o["rate"] = {"n": int(len(q)), "hz": r(1 / np.median(np.diff(q[:, 0])), 1),
                     "roll_rate_rms_hata_dps": r(np.sqrt(np.mean(er ** 2)), 2), "pitch_rate_rms_hata_dps": r(np.sqrt(np.mean(ep ** 2)), 2),
                     "yaw_rate_rms_hata_dps": r(np.sqrt(np.mean(ey ** 2)), 2),
                     "R_maks_abs_dps": r(np.abs(q[:, 2]).max(), 1), "P_maks_abs_dps": r(np.abs(q[:, 5]).max(), 1), "Y_maks_abs_dps": r(np.abs(q[:, 8]).max(), 1),
                     "RDes_maks_abs_dps": r(np.abs(q[:, 1]).max(), 1), "PDes_maks_abs_dps": r(np.abs(q[:, 4]).max(), 1),
                     "ROut": istat(q[:, 3]), "POut": istat(q[:, 6]), "YOut": istat(q[:, 9]),
                     "ROut_abs_p90": r(np.percentile(np.abs(q[:, 3]), 90), 3), "POut_abs_p90": r(np.percentile(np.abs(q[:, 6]), 90), 3),
                     "YOut_abs_p90": r(np.percentile(np.abs(q[:, 9]), 90), 3),
                     "doyma_orani_abs_out_ge_0_5": {"R": r(float(np.mean(np.abs(q[:, 3]) >= 0.5)), 3), "P": r(float(np.mean(np.abs(q[:, 6]) >= 0.5)), 3),
                                                  "Y": r(float(np.mean(np.abs(q[:, 9]) >= 0.5)), 3)},
                     "AOut": istat(q[:, 12]), "A_dikey_ivme_ms2": istat(q[:, 11]), "ADes_ms2": istat(q[:, 10]),
                     "roll_rate_hata_sifir_gecis_hz": sifir_gecis_hz(q[:, 0], er), "pitch_rate_hata_sifir_gecis_hz": sifir_gecis_hz(q[:, 0], ep),
                     "not": "RATE.R/P/Y deg/s; ROut/POut/YOut -1..1 karistirici cikisi. PID bilesenleri (PIDR/PIDP) LOG_BITMASK bit12 kapali oldugundan YOK — P/I/D/FF ayri ayri cikarilamaz."}
        if fft:
            for ad, e in (("roll_rate_hata", er), ("pitch_rate_hata", ep), ("ROut", q[:, 3]), ("POut", q[:, 6])):
                f = fft_spektrum(q[:, 0], e)
                if f:
                    o["rate"][ad + "_fft"] = {k: v for k, v in f.items() if not k.startswith("_")}
                    o["_fft_" + ad] = f
    return o


def imu_fft_dilim(A, t0, t1, etiket):
    """IMU0 ve IMU1: AccX/AccY/AccZ, GyrX/GyrY/GyrZ spektrumlari ve yapisal bant (2-12,5 Hz) tepeleri."""
    out = {"etiket": etiket, "dilim_t": [r(t0, 2), r(t1, 2)], "sure_s": r(t1 - t0, 2)}
    im = kes(A["IMU"], t0, t1)
    for inst in (0, 1):
        x = im[im[:, 1] == inst]
        if len(x) < 32:
            out["IMU%d" % inst] = None; continue
        d = {"n": int(len(x)), "fs_hz": r(1 / np.median(np.diff(x[:, 0])), 2)}
        for ad, col, birim in (("AccZ", 7, "m/s2"), ("AccX", 5, "m/s2"), ("AccY", 6, "m/s2"),
                               ("GyrX", 2, "rad/s"), ("GyrY", 3, "rad/s"), ("GyrZ", 4, "rad/s")):
            f = fft_spektrum(x[:, 0], x[:, col])
            fy = fft_spektrum(x[:, 0], x[:, col], arama=YAPISAL_BANT, k=4)
            d[ad] = {k: v for k, v in f.items() if not k.startswith("_")}
            d[ad]["birim"] = birim
            d[ad]["yapisal_2_12.5Hz_tepeler"] = fy["tepeler"] if fy else None
            d[ad]["_f"] = f["_f"]; d[ad]["_amp"] = f["_amp"]
            if ad.startswith("Gyr"):
                d[ad]["rms_dps"] = r(float(np.degrees(np.sqrt(np.mean((x[:, col] - x[:, col].mean()) ** 2)))), 2)
                d[ad]["pp_dps"] = r(float(np.degrees(x[:, col].max() - x[:, col].min())), 1)
        out["IMU%d" % inst] = d
    return out


def kayan_bant_rms(x, fs, W, adim, bantlar):
    """x: IMU dizisi (t, I, GyrX, GyrY, GyrZ, AccX, AccY, AccZ); W ornek pencere, adim ornek; bantlar [(sutun,(f0,f1))]"""
    out = []
    for i in range(0, len(x) - W, adim):
        seg = x[i:i + W]; row = [seg[W // 2, 0]]
        for col, (b0, b1) in bantlar:
            sig = seg[:, col] - seg[:, col].mean(); X = np.fft.rfft(sig); f = np.fft.rfftfreq(len(sig), 1 / fs)
            y = np.fft.irfft(np.where((f >= b0) & (f <= b1), X, 0), n=len(sig)); row.append(float(np.sqrt(np.mean(y ** 2))))
        out.append(row)
    return np.array(out)


KB_BANTLAR = [(2, (4, 12.5)), (3, (4, 12.5)), (2, (2, 4)), (3, (2, 4)), (7, (4, 12.5))]


def kb_ozet(k):
    if len(k) == 0: return None
    return {"n_pencere": int(len(k)), "GyrX_4-12.5Hz_dps": istat(k[:, 1]), "GyrY_4-12.5Hz_dps": istat(k[:, 2]), "GyrX_2-4Hz_dps": istat(k[:, 3]), "GyrY_2-4Hz_dps": istat(k[:, 4]),
            "AccZ_4-12.5Hz_ms2": istat(k[:, 5]), "GyrX_4-12.5_tepe_t": r(k[np.argmax(k[:, 1]), 0], 1), "GyrY_4-12.5_tepe_t": r(k[np.argmax(k[:, 2]), 0], 1)}


def temizle(o):
    if isinstance(o, dict):
        return {str(k): temizle(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [temizle(v) for v in o]
    if isinstance(o, np.ndarray):
        return [temizle(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return r(float(o), 4)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# ============================================================================ E logu
A = oku(LOG_E); P = A["parm"]; mk = motor_kanallari(P)
assert mk == {"M4": 9, "M2": 10, "M1": 11, "M3": 12}, mk
bat = A["BAT"]; ct = A["CTUN"]
n_h, aday_h = hucre(bat[0, 1])
pen = pencereler(A, mk)
assert len(pen) == 1, pen
W = pen[0]; t0, t1 = W["t0"], W["t1"]

L = {"dosya": os.path.relpath(LOG_E, KOK).replace("\\", "/"), "sha256": sha256(LOG_E), "bayt": os.path.getsize(LOG_E),
     "yazilim": A["ver"], "log_t_ilk": r(ct[0, 0], 2), "log_t_son": r(ct[-1, 0], 2), "log_suresi_s": r(ct[-1, 0] - ct[0, 0], 1),
     "kullanici_beyani": {"etiket": "E (= D konfigu)", "pil": "4S", "pervane": "9x5x3", "saat": "kullanici: 12:41:20; dosya adi 12-40-55",
                          "gozlem": "tam gaz yapmama ragmen titresim olmadi ve gayet hizliydi; kollarda sallanti var, mekanik bir problem saniyorum",
                          "kaynak": "kullanici_beyani (pil/pervane LOGDA YOK)"},
     "hucre": {"n": n_h, "V_ilk": r(bat[0, 1], 2), "V_ilk_hucre": r(bat[0, 1] / n_h, 3), "adaylar": aday_h,
               "dayanak": "ilk BAT.Volt / n, 3,2-4,3 V/hucre araligina uyan n; 3S olsaydi %.2f V/hucre (> 4,3) olurdu" % (bat[0, 1] / 3)},
     "mesaj_n": {k: int(A["sayac"].get(k, 0)) for k in ("CTUN", "BAT", "VIBE", "RCOU", "RCIN", "ATT", "RATE", "IMU", "ACC", "GYR", "PIDR", "PIDP", "XKF4", "MOTB", "PSCD", "EV", "ARM", "MODE", "ERR", "MSG", "PARM", "ESC", "RPM", "DSF")},
     "DSF_dusurulen_toplam": int(A["DSF"][:, 1].max()) if len(A.get("DSF", [])) else 0,
     "imu_hz": r(1 / np.median(np.diff(A["IMU"][A["IMU"][:, 1] == 0][:, 0])), 2),
     "parm": {k: P.get(k) for k in ("MOT_THST_HOVER", "MOT_THST_EXPO", "MOT_SPIN_MIN", "MOT_SPIN_ARM", "MOT_SPIN_MAX", "MOT_PWM_MIN", "MOT_PWM_MAX",
                                    "MOT_YAW_HEADROOM", "MOT_BAT_VOLT_MAX", "MOT_BAT_VOLT_MIN", "BATT_CAPACITY", "BATT_LOW_VOLT", "BATT_CRT_VOLT",
                                    "INS_HNTCH_ENABLE", "INS_GYRO_FILTER", "INS_ACCEL_FILTER", "INS_LOG_BAT_MASK", "LOG_BITMASK", "FFT_ENABLE",
                                    "ATC_RAT_RLL_P", "ATC_RAT_RLL_I", "ATC_RAT_RLL_D", "ATC_RAT_RLL_FF", "ATC_RAT_RLL_FLTD", "ATC_RAT_RLL_FLTT", "ATC_RAT_RLL_IMAX",
                                    "ATC_RAT_PIT_P", "ATC_RAT_PIT_I", "ATC_RAT_PIT_D", "ATC_RAT_PIT_FF", "ATC_RAT_PIT_FLTD", "ATC_RAT_PIT_FLTT",
                                    "ATC_RAT_YAW_P", "ATC_RAT_YAW_I", "ATC_RAT_YAW_D", "ATC_ANG_RLL_P", "ATC_ANG_PIT_P", "ATC_ANG_YAW_P",
                                    "ATC_ACCEL_R_MAX", "ATC_ACCEL_P_MAX", "ATC_INPUT_TC", "ATC_THR_MIX_MAX", "ATC_THR_MIX_MAN",
                                    "PILOT_SPEED_UP", "PILOT_ACCEL_Z", "PSC_ACCZ_P", "PSC_ACCZ_I", "FRAME_CLASS", "FRAME_TYPE", "MOT_SPOOL_TIME", "MOT_SLEWUP_TIME", "MOT_SLEWDN_TIME",
                                    "SERVO9_FUNCTION", "SERVO10_FUNCTION", "SERVO11_FUNCTION", "SERVO12_FUNCTION", "STAT_FLTTIME", "STAT_BOOTCNT", "SCHED_LOOP_RATE")},
     "motor_kanallari": {m: "C%d" % c for m, c in sorted(mk.items())}, "motor_konum": MOTOR_KONUM,
     "arm_pencereleri": [{"t0": r(q["t0"], 2), "t1": r(q["t1"], 2), "sure_s": r(q["t1"] - q["t0"], 1), "kaynak": q["kaynak"], "disarm_yontemi": q["disarm_yontemi"]} for q in pen],
     "olaylar": sorted([(r(t, 2), "EV", int(i)) for t, i in A["EV"]] + [(r(t, 2), "MODE", "%d rsn=%d" % (m, rs)) for t, m, rs in A["MODE"]]
                       + [(r(t, 2), "ARM", "state=%d meth=%d" % (s, m)) for t, s, m in A["ARM"]] + [(r(t, 2), "MSG", s) for t, s in A["MSG"]]
                       + [(r(t, 2), "ERR", "sub=%d code=%d" % (s, c)) for t, s, c in A["ERR"]], key=lambda z: z[0])}

# ---------------------------------------------------------------- ucus profili
c = kes(ct, t0, t1); tc = c[:, 0]; ThI = c[:, 1]; ThO = c[:, 2]; ThH = c[:, 3]; Alt = c[:, 5]; DCRt = c[:, 7]; CRt = c[:, 8]
taban = np.median(Alt[tc <= t0 + 1.0]) if np.any(tc <= t0 + 1.0) else Alt[0]
alt = Alt - taban; vz = ma(np.gradient(Alt, tc), 5)
mot = ThO > THO_MOTORLU; dtc = np.median(np.diff(tc)); motorlu_s = float(mot.sum() * dtc)
aski = (alt > ASKI_ALT) & (np.abs(vz) < ASKI_VZ) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
orta = mot & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
tam = ThO > TAM_GAZ_THO
rc = kes(A["RCOU"], t0, t1); pmin, pmax = P["MOT_PWM_MIN"], P["MOT_PWM_MAX"]; ust = pmin + P["MOT_SPIN_MAX"] * (pmax - pmin)
rc_mot = rc[:, [mk["M1"], mk["M2"], mk["M3"], mk["M4"]]]
rcou_tam_t = rc[:, 0][rc_mot.max(axis=1) >= ust - 1]   # herhangi bir motor ust sinirda
rcin = kes(A["RCIN"], t0, t1)

U = {"no": 1, "arm_t": r(t0, 2), "disarm_t": r(t1, 2), "pencere_s": r(t1 - t0, 1), "pencere_kaynak": W["kaynak"],
     "ctun_hz": r(1 / dtc, 1), "alt_taban_m": r(taban, 2), "alt_maks_m": r(alt.max(), 2), "alt_maks_t": r(tc[np.argmax(alt)], 2),
     "motorlu_s": r(motorlu_s, 1), "motorlu_t": [r(tc[mot][0], 2), r(tc[mot][-1], 2)] if mot.any() else None,
     "tur": "ucus" if motorlu_s >= KISA_SICRAMA_S else ("kisa_sicrama" if motorlu_s > 0 else "arm_yalniz"),
     "ThH": {"bas": r(ThH[0], 3), "son": r(ThH[-1], 3), "MOT_THST_HOVER_parm": r(P["MOT_THST_HOVER"], 3)},
     "gaz_profili": {"ThO_motorlu": istat(ThO[mot]), "ThI_motorlu": istat(ThI[mot]),
                     "ThO_ust_0.8_s": r(float(np.sum(ThO > 0.8) * dtc), 1), "ThO_ust_0.9_s": r(float(np.sum(ThO > 0.9) * dtc), 1),
                     "ThO_eq_1.0_s": r(float(np.sum(ThO >= 0.999) * dtc), 1),
                     "ThO_bant_sureleri_s": {"%.2f-%.2f" % (a, min(b, 1.0)): r(float(np.sum((ThO >= a) & (ThO < b)) * dtc), 1) for a, b in GAZ_BANTLARI},
                     "RCIN_C3_gaz_cubugu_us": istat(rcin[:, 3]) if len(rcin) else None,
                     "RCIN_C3_ust_1900_s": r(float(np.sum(rcin[:, 3] >= 1900) * np.median(np.diff(rcin[:, 0]))), 1) if len(rcin) else None,
                     "CRt_tirmanma_maks_ms": r(CRt.max() / 100, 2), "CRt_tirmanma_maks_t": r(tc[np.argmax(CRt)], 2),
                     "CRt_inis_min_ms": r(CRt.min() / 100, 2), "vz_turev_maks_ms": r(vz.max(), 2), "vz_turev_min_ms": r(vz.min(), 2)},
     "aski": {"n": int(aski.sum()), "s": r(float(aski.sum() * dtc), 1), "istatistik": None,
              "not": "aski orneklemi %d < %d — ASKI YOK; bu ucusta askida VIBE/RCOU/ATT istatistigi hesaplanamaz. 'orta_gaz' (ThO 0,25-0,75, motorlu) bandi ayrica verildi ama ASKI DEGILDIR (tirmanis/inis icerir)." % (aski.sum(), ASKI_EN_AZ)},
     "orta_gaz": {"n": int(orta.sum()), "s": r(float(orta.sum() * dtc), 1)}}

# ---- tam gaz pencereleri (CTUN.ThO > 0,8; RCOU ust sinir ayrica)
tg = []
for a, b, n in dilimler(tc, tam):
    m = (tc >= a) & (tc <= b); bb = kes(bat, a - 0.05, b + 0.05); rr = kes(rc, a - 0.05, b + 0.05)
    mb = kes(A["MOTB"], a, b)
    tg.append({"t0": r(a, 2), "t1": r(b, 2), "sure_s": r(b - a + dtc, 2), "n": int(n),
               "alt_bas_m": r(alt[m][0], 2), "alt_son_m": r(alt[m][-1], 2), "alt_kazanc_m": r(alt[m][-1] - alt[m][0], 2),
               "CRt_maks_ms": r(CRt[m].max() / 100, 2), "CRt_ort_ms": r(CRt[m].mean() / 100, 2), "vz_turev_maks_ms": r(vz[m].max(), 2),
               "ThO_ort": r(ThO[m].mean(), 3), "ThO_maks": r(ThO[m].max(), 3), "ThI_ort": r(ThI[m].mean(), 3),
               "I_maks_A": r(bb[:, 3].max(), 1) if len(bb) else None, "I_ort_A": r(bb[:, 3].mean(), 1) if len(bb) else None,
               "V_min": r(bb[:, 1].min(), 2) if len(bb) else None, "V_ort": r(bb[:, 1].mean(), 2) if len(bb) else None,
               "P_maks_W": r((bb[:, 1] * bb[:, 3]).max(), 0) if len(bb) else None,
               "rcou_M_ort": {mm: r(rr[:, ch].mean(), 0) for mm, ch in mk.items()} if len(rr) else None,
               "rcou_M_maks": {mm: r(rr[:, ch].max(), 0) for mm, ch in mk.items()} if len(rr) else None,
               "rcou_ust_sinir_orani": {mm: r(float(np.mean(rr[:, ch] >= ust - 1)), 2) for mm, ch in mk.items()} if len(rr) else None,
               "MOTB": {"ThLimit_maks": r(mb[:, 3].max(), 3), "ThrAvMx_min": r(mb[:, 4].min(), 3), "LiftMax_min": r(mb[:, 1].min(), 3),
                        "FailFlags_maks": int(mb[:, 6].max())} if len(mb) else None})
U["tam_gaz_pencereleri"] = tg
U["yuksek_gaz_pencereleri(ThO>0.5)"] = [{"t0": r(a, 2), "t1": r(b, 2), "sure_s": r(b - a + dtc, 2), "ThO_ort": r(ThO[(tc >= a) & (tc <= b)].mean(), 3), "ThO_maks": r(ThO[(tc >= a) & (tc <= b)].max(), 3),
                                        "alt_m": [r(alt[(tc >= a) & (tc <= b)][0], 2), r(alt[(tc >= a) & (tc <= b)][-1], 2)], "I_maks_A": r(kes(bat, a, b)[:, 3].max(), 1) if len(kes(bat, a, b)) else None,
                                        "RCIN_C3_maks_us": r(kes(rcin, a, b)[:, 3].max(), 0) if len(kes(rcin, a, b)) else None} for a, b, n in dilimler(tc, ThO > 0.5)]
U["tam_gaz_toplam_s"] = r(sum(x["sure_s"] for x in tg), 1)
U["rcou_ust_sinir"] = {"ust_pwm": r(ust, 0), "herhangi_motor_ust_sinirda_n": int(len(rcou_tam_t)),
                       "herhangi_motor_ust_sinirda_s": r(len(rcou_tam_t) * np.median(np.diff(rc[:, 0])), 1),
                       "t_araligi": [r(rcou_tam_t.min(), 2), r(rcou_tam_t.max(), 2)] if len(rcou_tam_t) else None,
                       "hepsi_ust_sinirda_n": int(np.sum(rc_mot.min(axis=1) >= ust - 1))}

# ---- pil
bb = kes(bat, t0, t1); bm = bb[hizala(bb[:, 0], tc, mot.astype(float)) > 0.5]
U["bat"] = {"V_arm": r(bb[0, 1], 2), "V_son": r(bb[-1, 1], 2), "V_min": r(bb[:, 1].min(), 2), "V_min_t": r(bb[np.argmin(bb[:, 1]), 0], 2),
            "V_min_I": r(bb[np.argmin(bb[:, 1]), 3], 1), "V_min_hucre": r(bb[:, 1].min() / n_h, 3), "V_ort_motorlu": r(bm[:, 1].mean(), 2) if len(bm) else None,
            "I_motorlu": istat(bm[:, 3]) if len(bm) else None, "I_maks_A": r(bb[:, 3].max(), 1), "I_maks_t": r(bb[np.argmax(bb[:, 3]), 0], 2),
            "P_maks_W": r((bb[:, 1] * bb[:, 3]).max(), 0), "mAh_pencere": r((bb[-1, 4] - bb[0, 4]), 0),
            "VoltR_ort": r(bb[:, 2].mean(), 2), "BAT_Res_ort_ohm": r(bb[:, 5].mean(), 4),
            "sarkma_V": r(bb[0, 1] - bb[:, 1].min(), 2), "sarkma_V_hucre": r((bb[0, 1] - bb[:, 1].min()) / n_h, 3),
            "BATT_LOW_VOLT_parm": P.get("BATT_LOW_VOLT"), "BATT_CRT_VOLT_parm": P.get("BATT_CRT_VOLT"),
            "not": "BATT_LOW/CRT 10/9 V = 3S esikleri; 4S'te V_min %.2f V (%.2f V/hucre) esigin ustunde kaldi, failsafe tetiklenmedi (ERR yok)" % (bb[:, 1].min(), bb[:, 1].min() / n_h)}
mb = kes(A["MOTB"], t0, t1)
U["motb"] = {"LiftMax": istat(mb[:, 1]), "ThLimit": istat(mb[:, 3]), "ThrAvMx": istat(mb[:, 4]), "ThrOut": istat(mb[:, 5]),
             "FailFlags_degerler": {str(int(v)): int(np.sum(mb[:, 6] == v)) for v in np.unique(mb[:, 6])},
             "FailFlags_not": "AP_MotorsMulticopter Log_Write: bit0 = thrust_boost, bit1 = thrust_balanced -> 2 = dengeli, boost yok (OLAGAN); 0/1 gorulseydi motor doymasi/itki kaybi telafisi olurdu"}


# ---- VIBE: genel(pencere), motorlu, aski(yok), tam gaz, gaz bantlari
def ctun_mask(mask):
    return lambda tt: hizala(tt, tc, mask.astype(float)) > 0.5


U["vibe"] = {"kapsam_pencere": vibe_istat(A, t0, t1), "kapsam_motorlu": vibe_istat(A, t0, t1, ctun_mask(mot)),
             "kapsam_aski": None if aski.sum() < ASKI_EN_AZ else vibe_istat(A, t0, t1, ctun_mask(aski)),
             "kapsam_tam_gaz(ThO>0.8)": vibe_istat(A, t0, t1, ctun_mask(tam)),
             "kapsam_orta_gaz(0.25-0.75, aski DEGIL)": vibe_istat(A, t0, t1, ctun_mask(orta)),
             "gaz_bantlari": {}, "clip_toplam": {}}
for a, b in GAZ_BANTLARI:
    mm = (ThO >= a) & (ThO < b)
    U["vibe"]["gaz_bantlari"]["%.2f-%.2f" % (a, min(b, 1.0))] = vibe_istat(A, t0, t1, ctun_mask(mm)) if mm.sum() >= 3 else None
v = kes(A["VIBE"], t0, t1)
for inst in (0, 1):
    vi = v[v[:, 1] == inst]
    U["vibe"]["clip_toplam"]["IMU%d" % inst] = int(vi[-1, 5] - vi[0, 5]) if len(vi) > 1 else 0
# VIBE tepe zamanlari
vi0 = v[v[:, 1] == 0]
U["vibe"]["Z_tepe"] = {"t": r(vi0[np.argmax(vi0[:, 4]), 0], 2), "deger": r(vi0[:, 4].max(), 1),
                       "ThO_o_anda": r(float(hizala(np.array([vi0[np.argmax(vi0[:, 4]), 0]]), tc, ThO)[0]), 3),
                       "alt_o_anda_m": r(float(hizala(np.array([vi0[np.argmax(vi0[:, 4]), 0]]), tc, alt)[0]), 2)}

# ---- RCOU motor dengesi
U["rcou"] = {"motor_kanallari": L["motor_kanallari"], "not": "GERCEK motor kanallari AUX C9-C12; MAIN C1-C4 kopyadir (SERVO1..4_FUNCTION=34,34,33,34).",
             "motorlu": rcou_istat(A, mk, ctun_mask(mot)), "tam_gaz(ThO>0.8)": rcou_istat(A, mk, ctun_mask(tam)),
             "orta_gaz(0.25-0.75)": rcou_istat(A, mk, ctun_mask(orta)),
             "gaz_bantlari": {"%.2f-%.2f" % (a, min(b, 1.0)): rcou_istat(A, mk, ctun_mask((ThO >= a) & (ThO < b))) for a, b in GAZ_BANTLARI}}
# motor komutu ile ROut/POut iliskisi: karistirici tutarliligi (X: roll -> sag(M1,M4) eksi, sol(M2,M3) arti)
rt = kes(A["RATE"], t0, t1)
rc_m = rc[hizala(rc[:, 0], tc, mot.astype(float)) > 0.5]
if len(rc_m) > 10:
    RO = hizala_yakin(rc_m[:, 0], rt[:, 0], rt[:, 3]); PO = hizala_yakin(rc_m[:, 0], rt[:, 0], rt[:, 6]); YO = hizala_yakin(rc_m[:, 0], rt[:, 0], rt[:, 9])
    RO1 = hizala(rc_m[:, 0], rt[:, 0], rt[:, 3])
    Mm = {mm: rc_m[:, ch] for mm, ch in mk.items()}
    roll_fark = (Mm["M2"] + Mm["M3"]) - (Mm["M1"] + Mm["M4"])   # sol - sag  (pozitif ROut -> saga yatma -> sol motorlar artar)
    pitch_fark = (Mm["M1"] + Mm["M3"]) - (Mm["M2"] + Mm["M4"])  # on - arka (pozitif POut -> burun yukari -> on motorlar artar)
    yaw_fark = (Mm["M1"] + Mm["M2"]) - (Mm["M3"] + Mm["M4"])    # CCW - CW
    def korr(a, b):
        if a.std() == 0 or b.std() == 0: return None
        return r(float(np.corrcoef(a, b)[0, 1]), 3)
    U["rcou"]["karistirici_tutarlilik_motorlu"] = {"korr(ROut, sol-sag_pwm)": korr(RO, roll_fark), "korr(POut, on-arka_pwm)": korr(PO, pitch_fark),
                                                   "korr(YOut, CCW-CW_pwm)": korr(YO, yaw_fark),
                                                   "korr(ROut, sol-sag_pwm)_sonraki_ornek_hizalama": korr(RO1, roll_fark),
                                                   "RATE_t_eksi_RCOU_t_ms_medyan": r(float(np.median(rt[np.clip(np.searchsorted(rt[:, 0], rc_m[:, 0]), 0, len(rt) - 1), 0] - rc_m[:, 0]) * 1000), 1),
                                                   "not": "|korr| ~1 beklenir (karistirici dogru). RATE ayni dongude RCOU'dan ~100 ms sonra yazilir; en yakin ornek hizalamasi kullanildi (sonraki-ornek hizalamasi -0,2 verir, ARTEFAKT)"}

# ---- ATT / RATE
U["tutum"] = {"motorlu": att_rate_istat(A, ctun_mask(mot)), "tam_gaz(ThO>0.8)": att_rate_istat(A, ctun_mask(tam), fft=False),
              "orta_gaz(0.25-0.75)": att_rate_istat(A, ctun_mask(orta), fft=False),
              "pencere": att_rate_istat(A, lambda tt: (tt >= t0) & (tt <= t1), fft=False)}
# ---- RCIN cubuklari (pilot girisi mi salinim mi?)
if len(rcin):
    rm = rcin[hizala(rcin[:, 0], tc, mot.astype(float)) > 0.5]
    U["rcin_motorlu"] = {"C1_roll": istat(rm[:, 1]), "C2_pitch": istat(rm[:, 2]), "C3_gaz": istat(rm[:, 3]), "C4_yaw": istat(rm[:, 4]),
                         "not": "pilot cubuklari; DesRoll/DesPitch bunlardan turetilir (STAB), salinim pilot kaynakli mi diye bakilir"}
# ---- EKF
x4 = kes(A["XKF4"], t0, t1)
U["ekf"] = {"XKF4": {str(int(cc)): {"SV_maks": r(x4[x4[:, 1] == cc][:, 2].max(), 2), "SP_maks": r(x4[x4[:, 1] == cc][:, 3].max(), 2),
                                     "SH_maks": r(x4[x4[:, 1] == cc][:, 4].max(), 2), "SM_maks": r(x4[x4[:, 1] == cc][:, 5].max(), 2),
                                     "errRP_maks": r(x4[x4[:, 1] == cc][:, 6].max(), 3)} for cc in np.unique(x4[:, 1])},
            "ERR": [(r(t, 2), s, c) for t, s, c in A["ERR"]]}
# ---- PSCD (dikey konum kontrol) tam gazda
ps = kes(A["PSCD"], t0, t1)
U["pscd"] = {"n": int(len(ps)), "DVD_desired_vel_down_min_ms": r(ps[:, 3].min() / 100 if ps[:, 3].min() < -50 else ps[:, 3].min(), 2) if len(ps) else None,
             "VD_vel_down_min": r(ps[:, 5].min(), 2) if len(ps) else None,
             "not": "STAB kipinde PSCD yalniz LAND'de anlamli; birim cm/s ya da m/s surume gore — yalniz varlik kaydi"}

# ---- IMU FFT dilimleri: tam gaz (en uzun), motorlu tum, orta gaz en uzun, yer rolanti (arm'li, ThO<0.15, kalkis oncesi), arm oncesi
dil = {}
tg_dil = sorted([(b - a, a, b) for a, b, n in dilimler(tc, tam)], reverse=True)
if tg_dil:
    dil["tam_gaz"] = (tg_dil[0][1], tg_dil[0][2])
dil["motorlu"] = (tc[mot][0], tc[mot][-1])
if tg_dil:
    dil["tam_gaz_ve_tirmanis"] = (tg_dil[0][1], tc[np.argmax(alt)])   # tam gaz baslangici -> irtifa tepesi (tam gaz + momentumla tirmanis)
# LAND kipinde yavas inis: alt>1 m, ThO 0,25-0,75, |vz|<1 m/s (ASKI DEGIL; en sakin dilim — cubuklar ortada mi RCIN ile bakilir)
t_land = next((t for t, m, _ in A["MODE"] if m == 9), None)
if t_land is not None:
    li = (tc >= t_land) & (alt > ASKI_ALT) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1]) & (np.abs(vz) < 1.0)
    ld = sorted([(b - a, a, b) for a, b, n in dilimler(tc, li)], reverse=True)
    if ld and ld[0][0] >= 1.0:
        dil["yavas_inis_LAND"] = (ld[0][1], ld[0][2])
og = sorted([(b - a, a, b) for a, b, n in dilimler(tc, orta)], reverse=True)
if og:
    dil["orta_gaz_en_uzun"] = (og[0][1], og[0][2])
# kalkis oncesi rolanti: arm'dan motorlu baslangicina kadar (motorlar donuyor, yerde)
if tc[mot][0] - t0 > 1.3:
    dil["yer_rolanti_armli"] = (t0, tc[mot][0] - 0.1)
# arm oncesi (motor kapali) — sensor tabani
if t0 - ct[0, 0] > 1.5:
    dil["arm_oncesi_motor_kapali"] = (ct[0, 0], t0 - 0.1)
# inis sonrasi yerde armli (motorlu bitti -> disarm)
if t1 - tc[mot][-1] > 1.3:
    dil["inis_sonrasi_yerde"] = (tc[mot][-1] + 0.1, t1)
U["imu_fft"] = {k: imu_fft_dilim(A, a, b, k) for k, (a, b) in dil.items()}
U["dilimler_t"] = {k: [r(a, 2), r(b, 2)] for k, (a, b) in dil.items()}
if "yavas_inis_LAND" in dil:
    la, lb = dil["yavas_inis_LAND"]; lm = (tc >= la) & (tc <= lb)
    rl = kes(rcin, la, lb); rtl = kes(rt, la, lb)
    U["yavas_inis_LAND"] = {"t": [r(la, 2), r(lb, 2)], "sure_s": r(lb - la, 2), "n_ctun": int(lm.sum()), "ThO_ort": r(ThO[lm].mean(), 3), "vz_ort_ms": r(vz[lm].mean(), 2),
                            "CRt_ort_ms": r(CRt[lm].mean() / 100, 2), "alt_m": [r(alt[lm][0], 2), r(alt[lm][-1], 2)],
                            "rcin_us": {"C1_roll": istat(rl[:, 1]), "C2_pitch": istat(rl[:, 2]), "C4_yaw": istat(rl[:, 4])} if len(rl) else None,
                            "rate_out": {"ROut": istat(rtl[:, 3]), "POut": istat(rtl[:, 6]), "YOut": istat(rtl[:, 9])} if len(rtl) else None,
                            "rcou": rcou_istat(A, mk, ctun_mask(lm)), "vibe": vibe_istat(A, t0, t1, ctun_mask(lm)), "tutum": att_rate_istat(A, ctun_mask(lm), fft=False),
                            "not": "ASKI DEGIL (inis, ~0,5 m/s); ama gaz cubugu sabit ve roll/yaw cubuklari ortada -> statik motor dengesi icin E'deki EN sakin dilim. D askisiyla kiyas icin."}
# kayan pencere (1 s, adim 0,2 s) gyro/ivme bant RMS — yuksek frekans icerigi ZAMANDA nerede?
im0 = A["IMU"][A["IMU"][:, 1] == 0]; fs0 = 1 / np.median(np.diff(im0[:, 0]))
KB = kayan_bant_rms(im0, fs0, 25, 5, KB_BANTLAR); KB[:, 1:5] = np.degrees(KB[:, 1:5])
kb_m = (KB[:, 0] >= tc[mot][0]) & (KB[:, 0] <= tc[mot][-1])
U["kayan_bant_rms"] = {"yontem": "IMU0, 1 s (25 ornek) pencere, 0,2 s adim; dikdortgen FFT bant sinirlama; deg/s", "motorlu": kb_ozet(KB[kb_m])}
for k, (a, b) in dil.items():
    U["kayan_bant_rms"][k] = kb_ozet(KB[(KB[:, 0] >= a) & (KB[:, 0] <= b)])
esik = 3 * np.percentile(KB[kb_m, 1], 50)
yuksek = KB[kb_m & (KB[:, 1] > esik)]
U["kayan_bant_rms"]["GyrX_4-12.5_yuksek_anlar"] = {"esik_dps(3x motorlu p50)": r(esik, 2),
                                                   "dilimler": [[r(a, 1), r(b, 1)] for a, b, n in dilimler(yuksek[:, 0], np.ones(len(yuksek), bool), bosluk=0.45)] if len(yuksek) else []}

# pervane temel frekansi kaba hesabi
Vtg = tg[0]["V_ort"] if tg else U["bat"]["V_ort_motorlu"]
duty_tg = (tg[0]["rcou_M_ort"]["M1"] - pmin) / (pmax - pmin) if tg else None
U["pervane_frekans_hesap"] = {"yontem": "KV*V*duty/60 (yuksuz motor hizi; yuk altinda %20-35 daha dusuk) — OLCUM DEGIL, HESAP",
                              "KV": KV, "tam_gaz_V_ort": Vtg, "tam_gaz_duty_M1": r(duty_tg, 3),
                              "tam_gaz_f_temel_hz_yuksuz": r(KV * Vtg * duty_tg / 60, 0) if duty_tg else None,
                              "tam_gaz_f_temel_hz_yuklu_~0.7": r(0.7 * KV * Vtg * duty_tg / 60, 0) if duty_tg else None,
                              "pal_gecis_hz_3pal_yuklu": r(3 * 0.7 * KV * Vtg * duty_tg / 60, 0) if duty_tg else None,
                              "IMU_nyquist_hz": r(L["imu_hz"] / 2, 2),
                              "sonuc": "pervane temel frekansi (~100+ Hz) IMU 25 Hz kaydinda COZULEMEZ; 2-12,5 Hz'de gorulen tepeler govde/yapisal veya KATLANMIS (alias) icerik olabilir — ayirt edilemez. Kesin olcum icin INS_LOG_BAT_MASK=1 (+ INS_LOG_BAT_OPT=0 on-filtre) gerekir."}

# ============================================================================ D kiyas (gaz seviyesine gore)
def d_gaz_bantlari(fn):
    B = oku(fn); mkB = motor_kanallari(B["parm"]); penB = pencereler(B, mkB)
    ctB = B["CTUN"]; out = {"dosya": os.path.relpath(fn, KOK).replace("\\", "/"), "pencere_n": len(penB), "bantlar": {}, "ThO_maks": None, "ucuslar": []}
    tho_all = []
    for q in penB:
        cB = kes(ctB, q["t0"], q["t1"]); tB = cB[:, 0]; ThOB = cB[:, 2]; AltB = cB[:, 5]
        tabanB = np.median(AltB[tB <= q["t0"] + 1.0]) if np.any(tB <= q["t0"] + 1.0) else AltB[0]
        altB = AltB - tabanB; vzB = ma(np.gradient(AltB, tB), 5); motB = ThOB > THO_MOTORLU
        askiB = (altB > ASKI_ALT) & (np.abs(vzB) < ASKI_VZ) & (ThOB >= ASKI_THO[0]) & (ThOB <= ASKI_THO[1])
        dtB = np.median(np.diff(tB)) if len(tB) > 1 else 0.1
        out["ucuslar"].append({"t0": r(q["t0"], 1), "t1": r(q["t1"], 1), "motorlu_s": r(float(motB.sum() * dtB), 1), "aski_s": r(float(askiB.sum() * dtB), 1),
                               "ThO_maks": r(ThOB.max(), 3), "ThO_p95_motorlu": r(np.percentile(ThOB[motB], 95), 3) if motB.any() else None,
                               "alt_maks_m": r(altB.max(), 2)})
        tho_all.append(ThOB[motB])
        for a, b in GAZ_BANTLARI:
            mm = (ThOB >= a) & (ThOB < b)
            if mm.sum() < 3: continue
            key = "%.2f-%.2f" % (a, min(b, 1.0))
            vs = vibe_istat(B, q["t0"], q["t1"], lambda tt, tB=tB, mm=mm: hizala(tt, tB, mm.astype(float)) > 0.5)
            rs = rcou_istat(B, mkB, lambda tt, tB=tB, mm=mm: hizala(tt, tB, mm.astype(float)) > 0.5)
            ent = out["bantlar"].setdefault(key, {"vibe": [], "rcou": [], "n_ctun": 0})
            ent["vibe"].append(vs); ent["rcou"].append(rs); ent["n_ctun"] += int(mm.sum())
        # aski IMU FFT referansi (en uzun aski dilimi)
        if askiB.sum() >= ASKI_EN_AZ:
            sB = sorted([(b - a, a, b) for a, b, n in dilimler(tB, askiB)], reverse=True)
            if sB and sB[0][0] >= 2.0:
                out.setdefault("aski_imu_fft", []).append(imu_fft_dilim(B, sB[0][1], sB[0][2], "D aski en uzun dilim"))
                imB = B["IMU"][B["IMU"][:, 1] == 0]; fsB = 1 / np.median(np.diff(imB[:, 0]))
                KBB = kayan_bant_rms(imB[(imB[:, 0] >= sB[0][1]) & (imB[:, 0] <= sB[0][2])], fsB, 25, 5, KB_BANTLAR)
                if len(KBB):
                    KBB[:, 1:5] = np.degrees(KBB[:, 1:5])
                    out.setdefault("aski_kayan_bant_rms", []).append({"dilim_t": [r(sB[0][1], 1), r(sB[0][2], 1)], **kb_ozet(KBB)})
        # aski
        if askiB.sum() >= ASKI_EN_AZ:
            ent = out.setdefault("aski", {"vibe": [], "rcou": [], "att": [], "n_ctun": 0})
            ent["vibe"].append(vibe_istat(B, q["t0"], q["t1"], lambda tt, tB=tB, mm=askiB: hizala(tt, tB, mm.astype(float)) > 0.5))
            ent["rcou"].append(rcou_istat(B, mkB, lambda tt, tB=tB, mm=askiB: hizala(tt, tB, mm.astype(float)) > 0.5))
            ent["att"].append(att_rate_istat(B, lambda tt, tB=tB, mm=askiB: hizala(tt, tB, mm.astype(float)) > 0.5, fft=False))
            ent["n_ctun"] += int(askiB.sum())
    out["ThO_maks"] = r(max(x.max() for x in tho_all if len(x)), 3) if any(len(x) for x in tho_all) else None
    out["ThO_p99_motorlu"] = r(np.percentile(np.concatenate(tho_all), 99), 3) if any(len(x) for x in tho_all) else None
    # bant birlestirme: n agirlikli ortalama (vibe ort), p95 ve maks'in maks'i
    birles = {}
    for key, ent in out["bantlar"].items():
        d = {"n_ctun": ent["n_ctun"]}
        for inst in ("IMU0", "IMU1"):
            vs = [x[inst] for x in ent["vibe"] if x and x.get(inst)]
            if not vs: continue
            d[inst] = {}
            for ax in ("X", "Y", "Z"):
                n = sum(x[ax]["n"] for x in vs)
                d[inst][ax] = {"n": n, "ort": r(sum(x[ax]["ort"] * x[ax]["n"] for x in vs) / n), "p95_maks": r(max(x[ax]["p95"] for x in vs)), "maks": r(max(x[ax]["maks"] for x in vs))}
        rs = [x for x in ent["rcou"] if x]
        if rs:
            n = sum(x["n"] for x in rs)
            d["rcou"] = {"n": n, "M_ort_pwm": {mm: r(sum(x["M_ort_pwm"][mm] * x["n"] for x in rs) / n, 1) for mm in ("M1", "M2", "M3", "M4")},
                         "anlik_yayilim_ort": r(sum(x["anlik_yayilim_pwm"]["ort"] * x["n"] for x in rs) / n, 1),
                         "motor_sapma_ort_pwm": {mm: r(sum(x["motor_sapma_ort_pwm"][mm] * x["n"] for x in rs) / n, 1) for mm in ("M1", "M2", "M3", "M4")}}
            d["rcou"]["cift_farklari_pwm"] = {"CCW(M1+M2)-CW(M3+M4)_yaw": r((d["rcou"]["M_ort_pwm"]["M1"] + d["rcou"]["M_ort_pwm"]["M2"]) - (d["rcou"]["M_ort_pwm"]["M3"] + d["rcou"]["M_ort_pwm"]["M4"]), 1),
                                              "on(M1+M3)-arka(M2+M4)_pitch": r((d["rcou"]["M_ort_pwm"]["M1"] + d["rcou"]["M_ort_pwm"]["M3"]) - (d["rcou"]["M_ort_pwm"]["M2"] + d["rcou"]["M_ort_pwm"]["M4"]), 1),
                                              "sag(M1+M4)-sol(M2+M3)_roll": r((d["rcou"]["M_ort_pwm"]["M1"] + d["rcou"]["M_ort_pwm"]["M4"]) - (d["rcou"]["M_ort_pwm"]["M2"] + d["rcou"]["M_ort_pwm"]["M3"]), 1)}
        birles[key] = d
    out["bantlar_birlesik"] = birles
    if "aski" in out:
        ent = out["aski"]; d = {"n_ctun": ent["n_ctun"]}
        for inst in ("IMU0", "IMU1"):
            vs = [x[inst] for x in ent["vibe"] if x and x.get(inst)]
            if vs:
                d[inst] = {}
                for ax in ("X", "Y", "Z"):
                    n = sum(x[ax]["n"] for x in vs)
                    d[inst][ax] = {"n": n, "ort": r(sum(x[ax]["ort"] * x[ax]["n"] for x in vs) / n), "p95_maks": r(max(x[ax]["p95"] for x in vs)), "maks": r(max(x[ax]["maks"] for x in vs))}
        rs = [x for x in ent["rcou"] if x]
        if rs:
            n = sum(x["n"] for x in rs)
            d["rcou"] = {"n": n, "M_ort_pwm": {mm: r(sum(x["M_ort_pwm"][mm] * x["n"] for x in rs) / n, 1) for mm in ("M1", "M2", "M3", "M4")},
                         "anlik_yayilim_ort": r(sum(x["anlik_yayilim_pwm"]["ort"] * x["n"] for x in rs) / n, 1),
                         "motor_sapma_ort_pwm": {mm: r(sum(x["motor_sapma_ort_pwm"][mm] * x["n"] for x in rs) / n, 1) for mm in ("M1", "M2", "M3", "M4")},
                         "ucus_basina_cift_farklari_pwm": [x["cift_farklari_pwm"] for x in rs], "ucus_basina_n": [x["n"] for x in rs]}
        ats = [x["att"] for x in ent["att"] if x and x.get("att")]
        if ats:
            d["att"] = {"roll_rms_hata_deg": [x["roll_rms_hata_deg"] for x in ats], "pitch_rms_hata_deg": [x["pitch_rms_hata_deg"] for x in ats],
                        "roll_hata_sifir_gecis_hz": [x["roll_hata_sifir_gecis_hz"] for x in ats], "pitch_hata_sifir_gecis_hz": [x["pitch_hata_sifir_gecis_hz"] for x in ats]}
        rts = [x["rate"] for x in ent["att"] if x and x.get("rate")]
        if rts:
            d["rate"] = {"roll_rate_rms_hata_dps": [x["roll_rate_rms_hata_dps"] for x in rts], "pitch_rate_rms_hata_dps": [x["pitch_rate_rms_hata_dps"] for x in rts],
                         "ROut_std": [x["ROut"]["std"] for x in rts], "POut_std": [x["POut"]["std"] for x in rts], "YOut_ort": [x["YOut"]["ort"] for x in rts]}
        out["aski_birlesik"] = d
        del out["aski"]
    del out["bantlar"]
    return out, B


D_KIYAS = {}; D_RAW = {}
for fn in LOG_D:
    o, B = d_gaz_bantlari(fn); D_KIYAS[os.path.basename(fn)] = o; D_RAW[os.path.basename(fn)] = B

# E bant ozeti aynı bicimde (kiyas tablosu)
E_bant = {}
for key, vs in U["vibe"]["gaz_bantlari"].items():
    if not vs: continue
    d = {"n_ctun": int(np.sum((ThO >= float(key.split("-")[0])) & (ThO < (float(key.split("-")[1]) if float(key.split("-")[1]) < 1.0 else 1.001))))}
    for inst in ("IMU0", "IMU1"):
        if vs.get(inst):
            d[inst] = {ax: {"n": vs[inst][ax]["n"], "ort": vs[inst][ax]["ort"], "p95": vs[inst][ax]["p95"], "maks": vs[inst][ax]["maks"]} for ax in ("X", "Y", "Z")}
    rs = U["rcou"]["gaz_bantlari"].get(key)
    if rs:
        d["rcou"] = {"n": rs["n"], "M_ort_pwm": rs["M_ort_pwm"], "anlik_yayilim_ort": rs["anlik_yayilim_pwm"]["ort"], "motor_sapma_ort_pwm": rs["motor_sapma_ort_pwm"], "cift_farklari_pwm": rs["cift_farklari_pwm"]}
    E_bant[key] = d

KIYAS = {"yontem": "CTUN.ThO bantlarina gore VIBE (IMU0/IMU1 X/Y/Z ort, p95, maks) ve RCOU M1-M4 ortalamasi; D loglari ayni kural ve ayni koddan; D'nin tam gaz bandi yoksa o bantta kiyas YOK",
         "E_12-40-55": E_bant, "D": D_KIYAS}

# ============================================================================ GRAFIKLER
plt.rcParams.update({"font.size": 8, "axes.grid": True, "grid.alpha": 0.3})
C = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]
graf = []
tag = "2026-09-15_12-40-55"


def golge(ax):
    for x in tg:
        ax.axvspan(x["t0"], x["t1"], color="#d62728", alpha=0.12, lw=0)
    ax.axvline(t0, color="k", ls=":", lw=0.8); ax.axvline(t1, color="k", ls=":", lw=0.8)


# 1) zaman: gaz / irtifa / pil
fig, ax = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
ax[0].plot(ct[:, 0], ct[:, 2], color=C[0], label="CTUN.ThO"); ax[0].plot(ct[:, 0], ct[:, 1], color=C[3], lw=0.8, label="CTUN.ThI (pilot)")
ax[0].plot(ct[:, 0], ct[:, 3], color=C[2], lw=0.8, ls="--", label="CTUN.ThH")
if len(A["RCIN"]): ax[0].plot(A["RCIN"][:, 0], (A["RCIN"][:, 3] - 1000) / 1000, color="gray", lw=0.7, ls=":", label="RCIN.C3 (us-1000)/1000")
ax[0].axhline(TAM_GAZ_THO, color="r", lw=0.6, ls="--"); ax[0].set_ylabel("gaz 0-1"); ax[0].legend(loc="upper left", ncol=4); golge(ax[0])
ax[1].plot(ct[:, 0], ct[:, 5] - taban, color=C[0], label="CTUN.Alt - taban (m)"); ax[1].plot(ct[:, 0], ct[:, 8] / 100, color=C[1], lw=0.8, label="CTUN.CRt (m/s)")
ax[1].set_ylabel("m, m/s"); ax[1].legend(loc="upper left"); golge(ax[1])
ax[2].plot(bat[:, 0], bat[:, 1], color=C[0], label="BAT.Volt"); ax[2].plot(bat[:, 0], bat[:, 2], color=C[2], lw=0.7, ls="--", label="BAT.VoltR (dirence gore)")
ax[2].axhline(P["BATT_LOW_VOLT"], color="r", lw=0.6, ls=":", label="BATT_LOW_VOLT=%.0f" % P["BATT_LOW_VOLT"]); ax[2].set_ylabel("V"); ax[2].legend(loc="lower left"); golge(ax[2])
ax[3].plot(bat[:, 0], bat[:, 3], color=C[1], label="BAT.Curr (A)"); ax[3].plot(bat[:, 0], bat[:, 1] * bat[:, 3] / 10, color=C[4], lw=0.8, label="P/10 (W)")
ax[3].set_ylabel("A, W/10"); ax[3].set_xlabel("TimeUS/1e6 (s)"); ax[3].legend(loc="upper left"); golge(ax[3])
fig.suptitle("%s — 4S(logdan %.1f V) + 9x5x3 (beyan) — tam gaz pencereleri kirmizi; pencere %.1f-%.1f s, motorlu %.1f s, alt maks %.2f m" % (tag, bat[0, 1], t0, t1, motorlu_s, alt.max()), fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "zaman_ThO_alt_akim_gerilim_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 2) VIBE
fig, ax = plt.subplots(4, 1, figsize=(12, 9), sharex=True)
for i, (ad, col) in enumerate((("VibeX", 2), ("VibeY", 3), ("VibeZ", 4))):
    for inst in (0, 1):
        vi = A["VIBE"][A["VIBE"][:, 1] == inst]
        ax[i].plot(vi[:, 0], vi[:, col], color=C[inst], lw=0.9, label="IMU%d %s" % (inst, ad))
    ax[i].axhline(30, color="r", lw=0.6, ls="--", label="30 (AP esik)"); ax[i].set_ylabel("m/s2"); ax[i].legend(loc="upper left", ncol=3); golge(ax[i])
ax[3].plot(ct[:, 0], ct[:, 2], color=C[0], label="CTUN.ThO"); ax[3].plot(ct[:, 0], (ct[:, 5] - taban) / 10, color=C[2], lw=0.8, label="Alt/10 (m)")
for inst in (0, 1):
    vi = A["VIBE"][A["VIBE"][:, 1] == inst]; ax[3].plot(vi[:, 0], vi[:, 5] / max(1, vi[:, 5].max()), color=C[inst], lw=0.6, ls=":", label="IMU%d Clip (norm, maks=%d)" % (inst, vi[:, 5].max()))
ax[3].legend(loc="upper left", ncol=4); ax[3].set_xlabel("s"); golge(ax[3])
fig.suptitle("%s — VIBE X/Y/Z (IMU0/IMU1); clip toplam IMU0=%d IMU1=%d" % (tag, U["vibe"]["clip_toplam"]["IMU0"], U["vibe"]["clip_toplam"]["IMU1"]), fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "vibe_xyz_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 3) RCOU motorlar + RATE out + RCIN
fig, ax = plt.subplots(4, 1, figsize=(12, 11), sharex=True)
for i, mm in enumerate(("M1", "M2", "M3", "M4")):
    ax[0].plot(A["RCOU"][:, 0], A["RCOU"][:, mk[mm]], color=C[i], lw=0.9, label="%s C%d (%s)" % (mm, mk[mm], MOTOR_KONUM[mm]))
ax[0].axhline(ust, color="r", lw=0.6, ls="--", label="MOT_SPIN_MAX ust=%d" % ust); ax[0].set_ylabel("PWM us"); ax[0].legend(loc="upper left", ncol=3); golge(ax[0])
rcm = A["RCOU"][:, [mk["M1"], mk["M2"], mk["M3"], mk["M4"]]]
for i, mm in enumerate(("M1", "M2", "M3", "M4")):
    ax[1].plot(A["RCOU"][:, 0], rcm[:, i] - rcm.mean(axis=1), color=C[i], lw=0.9, label="%s - ort4" % mm)
ax[1].set_ylabel("sapma us"); ax[1].legend(loc="upper left", ncol=4); golge(ax[1])
ax[2].plot(A["RATE"][:, 0], A["RATE"][:, 3], color=C[0], lw=0.9, label="RATE.ROut"); ax[2].plot(A["RATE"][:, 0], A["RATE"][:, 6], color=C[1], lw=0.9, label="RATE.POut")
ax[2].plot(A["RATE"][:, 0], A["RATE"][:, 9], color=C[2], lw=0.9, label="RATE.YOut"); ax[2].plot(A["RATE"][:, 0], A["RATE"][:, 12], color=C[3], lw=0.7, ls="--", label="RATE.AOut")
ax[2].set_ylabel("-1..1"); ax[2].legend(loc="upper left", ncol=4); golge(ax[2])
if len(A["RCIN"]):
    for i, (ad, col) in enumerate((("C1 roll", 1), ("C2 pitch", 2), ("C3 gaz", 3), ("C4 yaw", 4))):
        ax[3].plot(A["RCIN"][:, 0], A["RCIN"][:, col], color=C[i], lw=0.9, label="RCIN." + ad)
ax[3].set_ylabel("us"); ax[3].set_xlabel("s"); ax[3].legend(loc="upper left", ncol=4); golge(ax[3])
fig.suptitle("%s — motor cikislari (AUX C9-C12 -> M1..M4), motor-ortalama sapmasi, karistirici cikislari, pilot cubuklari" % tag, fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "rcou_motorlar_rate_rcin_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 4) tutum izleme
at = A["ATT"]; rt_all = A["RATE"]
fig, ax = plt.subplots(4, 1, figsize=(12, 11), sharex=True)
ax[0].plot(at[:, 0], at[:, 1], color=C[1], lw=0.8, ls="--", label="DesRoll"); ax[0].plot(at[:, 0], at[:, 2], color=C[0], lw=0.9, label="Roll"); ax[0].set_ylabel("deg"); ax[0].legend(loc="upper left", ncol=2); golge(ax[0])
ax[1].plot(at[:, 0], at[:, 3], color=C[1], lw=0.8, ls="--", label="DesPitch"); ax[1].plot(at[:, 0], at[:, 4], color=C[0], lw=0.9, label="Pitch"); ax[1].set_ylabel("deg"); ax[1].legend(loc="upper left", ncol=2); golge(ax[1])
ax[2].plot(rt_all[:, 0], rt_all[:, 1], color=C[1], lw=0.8, ls="--", label="RDes"); ax[2].plot(rt_all[:, 0], rt_all[:, 2], color=C[0], lw=0.9, label="R (deg/s)")
ax[2].plot(rt_all[:, 0], rt_all[:, 4], color=C[3], lw=0.8, ls="--", label="PDes"); ax[2].plot(rt_all[:, 0], rt_all[:, 5], color=C[2], lw=0.9, label="P (deg/s)"); ax[2].set_ylabel("deg/s"); ax[2].legend(loc="upper left", ncol=4); golge(ax[2])
im0 = A["IMU"][A["IMU"][:, 1] == 0]
ax[3].plot(im0[:, 0], np.degrees(im0[:, 2]), color=C[0], lw=0.8, label="IMU0 GyrX (deg/s)"); ax[3].plot(im0[:, 0], np.degrees(im0[:, 3]), color=C[1], lw=0.8, label="IMU0 GyrY")
ax[3].plot(im0[:, 0], im0[:, 7], color=C[2], lw=0.7, ls=":", label="IMU0 AccZ (m/s2)"); ax[3].set_ylabel("deg/s, m/s2"); ax[3].set_xlabel("s"); ax[3].legend(loc="upper left", ncol=3); golge(ax[3])
tm = U["tutum"]["motorlu"]
fig.suptitle("%s — tutum izleme (ATT 10 Hz, RATE 10 Hz, IMU 25 Hz); motorlu roll/pitch RMS hata %.2f/%.2f deg, rate RMS %.1f/%.1f deg/s" % (
    tag, tm["att"]["roll_rms_hata_deg"], tm["att"]["pitch_rms_hata_deg"], tm["rate"]["roll_rate_rms_hata_dps"], tm["rate"]["pitch_rate_rms_hata_dps"]), fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "tutum_izleme_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 5) IMU FFT: dilimlere gore AccZ / GyrX / GyrY
dil_sira = [k for k in ("arm_oncesi_motor_kapali", "yer_rolanti_armli", "tam_gaz_ve_tirmanis", "orta_gaz_en_uzun", "yavas_inis_LAND", "motorlu", "inis_sonrasi_yerde") if k in U["imu_fft"]]
fig, ax = plt.subplots(3, 1, figsize=(12, 10))
for i, ad in enumerate(("AccZ", "GyrX", "GyrY")):
    for j, k in enumerate(dil_sira):
        d = U["imu_fft"][k].get("IMU0")
        if not d: continue
        f, amp = d[ad]["_f"], d[ad]["_amp"]
        y = np.degrees(amp) if ad.startswith("Gyr") else amp
        ax[i].plot(f, y, color=C[j % len(C)], lw=1.0, label="%s (%.1f s, n=%d)" % (k, U["imu_fft"][k]["sure_s"], d["n"]))
    ax[i].axvspan(YAPISAL_BANT[0], YAPISAL_BANT[1], color="orange", alpha=0.08, lw=0)
    ax[i].set_ylabel("%s genlik (%s)" % (ad, "deg/s" if ad.startswith("Gyr") else "m/s2")); ax[i].legend(loc="upper right", fontsize=7); ax[i].set_xlim(0, L["imu_hz"] / 2)
ax[2].set_xlabel("Hz (IMU0, %.1f Hz -> Nyquist %.2f Hz; turuncu = 2-12,5 Hz yapisal bant)" % (L["imu_hz"], L["imu_hz"] / 2))
fig.suptitle("%s — IMU0 FFT (Hann) dilimlere gore; pervane temel frekansi (~%s Hz hesap) COZULEMEZ" % (tag, U["pervane_frekans_hesap"]["tam_gaz_f_temel_hz_yuklu_~0.7"]), fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "fft_imu_dilimler_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 6) ATT/RATE hata FFT
fig, ax = plt.subplots(2, 1, figsize=(12, 7))
for ad, col in (("roll_hata", C[0]), ("pitch_hata", C[1])):
    f = tm.get("_fft_" + ad)
    if f: ax[0].plot(f["_f"], f["_amp"], color=col, lw=1.0, label="ATT %s (RMS %.2f deg)" % (ad, f["rms"]))
ax[0].set_ylabel("deg"); ax[0].legend(); ax[0].set_title("ATT Roll-DesRoll / Pitch-DesPitch FFT (10 Hz -> Nyquist 5 Hz), motorlu dilim")
for ad, col in (("roll_rate_hata", C[0]), ("pitch_rate_hata", C[1]), ("ROut", C[2]), ("POut", C[3])):
    f = tm.get("_fft_" + ad)
    if f: ax[1].plot(f["_f"], f["_amp"], color=col, lw=1.0, label="RATE %s (RMS %.3g)" % (ad, f["rms"]))
ax[1].set_ylabel("deg/s | -1..1"); ax[1].set_xlabel("Hz"); ax[1].legend(); ax[1].set_title("RATE hata ve karistirici cikisi FFT (10 Hz)")
fig.tight_layout(); p = os.path.join(OUT, "fft_tutum_hata_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 7) VIBE vs ThO: E ile D
fig, ax = plt.subplots(1, 3, figsize=(14, 4.5))
def tho_at(B, tt):
    cB = B["CTUN"]; return hizala(tt, cB[:, 0], cB[:, 2])
for i, (ad, col) in enumerate((("X", 2), ("Y", 3), ("Z", 4))):
    vi = A["VIBE"][A["VIBE"][:, 1] == 0]; vi = vi[(vi[:, 0] >= t0) & (vi[:, 0] <= t1)]
    ax[i].scatter(tho_at(A, vi[:, 0]), vi[:, col], s=6, color=C[1], alpha=0.6, label="E 12-40-55 (tam gaz)")
    for j, (nm, B) in enumerate(D_RAW.items()):
        vb = B["VIBE"][B["VIBE"][:, 1] == 0]
        ax[i].scatter(tho_at(B, vb[:, 0]), vb[:, col], s=4, color=[C[0], C[2]][j], alpha=0.35, label="D %s" % nm.replace(".bin", ""))
    ax[i].set_xlabel("CTUN.ThO"); ax[i].set_ylabel("Vibe%s IMU0 (m/s2)" % ad); ax[i].set_xlim(0, 1.02); ax[i].axvline(TAM_GAZ_THO, color="r", lw=0.6, ls="--")
    if i == 0: ax[i].legend(fontsize=7)
fig.suptitle("VIBE (IMU0) gaz seviyesine gore — E (12-40-55) vs D (11-18-16, 11-14-33), ayni 4S + 9x5x3 beyani", fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "vibe_vs_ThO_E_vs_D.png"); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 8) RCOU motor sapmasi gaz seviyesine gore, E vs D (M1..M4 - ort4)
fig, ax = plt.subplots(1, 4, figsize=(15, 4), sharey=True)
for i, mm in enumerate(("M1", "M2", "M3", "M4")):
    rE = kes(A["RCOU"], t0, t1); rEm = rE[:, [mk["M1"], mk["M2"], mk["M3"], mk["M4"]]]; thE = tho_at(A, rE[:, 0]); mmask = thE > THO_MOTORLU
    ax[i].scatter(thE[mmask], (rEm[:, i] - rEm.mean(axis=1))[mmask], s=6, color=C[1], alpha=0.6, label="E")
    for j, (nm, B) in enumerate(D_RAW.items()):
        mkB = motor_kanallari(B["parm"]); rB = B["RCOU"]; rBm = rB[:, [mkB["M1"], mkB["M2"], mkB["M3"], mkB["M4"]]]; thB = tho_at(B, rB[:, 0]); mb_ = thB > THO_MOTORLU
        ax[i].scatter(thB[mb_], (rBm[:, i] - rBm.mean(axis=1))[mb_], s=3, color=[C[0], C[2]][j], alpha=0.3, label="D %s" % nm[11:19])
    ax[i].set_title("%s (%s) - ort4" % (mm, MOTOR_KONUM[mm])); ax[i].set_xlabel("CTUN.ThO"); ax[i].axhline(0, color="k", lw=0.5)
    if i == 0: ax[i].set_ylabel("PWM sapma (us)"); ax[i].legend(fontsize=7)
fig.suptitle("Motor komutu sapmasi (motor - 4 motor ortalamasi) gaz seviyesine gore — E vs D; surekli tek yonlu sapma = o kolda itki/hiza farki", fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "rcou_sapma_vs_ThO_E_vs_D.png"); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# 9) kayan pencere gyro bant RMS zamanda + cubuklar
fig, ax = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
ax[0].plot(KB[:, 0], KB[:, 1], color=C[0], label="GyrX 4-12.5 Hz"); ax[0].plot(KB[:, 0], KB[:, 2], color=C[1], label="GyrY 4-12.5 Hz")
ax[0].plot(KB[:, 0], KB[:, 3], color=C[0], ls="--", lw=0.8, label="GyrX 2-4 Hz"); ax[0].plot(KB[:, 0], KB[:, 4], color=C[1], ls="--", lw=0.8, label="GyrY 2-4 Hz")
DK = D_KIYAS["2026-09-15 11-18-16.bin"].get("aski_kayan_bant_rms")
if DK:
    ax[0].axhline(DK[0]["GyrX_4-12.5Hz_dps"]["p95"], color=C[0], ls=":", lw=0.8, label="D aski GyrX 4-12.5 p95 = %.1f" % DK[0]["GyrX_4-12.5Hz_dps"]["p95"])
    ax[0].axhline(DK[0]["GyrY_4-12.5Hz_dps"]["p95"], color=C[1], ls=":", lw=0.8, label="D aski GyrY 4-12.5 p95 = %.1f" % DK[0]["GyrY_4-12.5Hz_dps"]["p95"])
ax[0].set_ylabel("bant RMS (deg/s)"); ax[0].legend(loc="upper left", ncol=3, fontsize=7); golge(ax[0])
ax[1].plot(KB[:, 0], KB[:, 5], color=C[2], label="AccZ 4-12.5 Hz (m/s2)"); ax[1].plot(ct[:, 0], ct[:, 2] * 2, color=C[0], lw=0.8, ls="--", label="CTUN.ThO x2")
ax[1].set_ylabel("m/s2"); ax[1].legend(loc="upper left", ncol=2, fontsize=7); golge(ax[1])
if len(A["RCIN"]):
    for i, (ad, col) in enumerate((("C1 roll", 1), ("C2 pitch", 2), ("C4 yaw", 4))):
        ax[2].plot(A["RCIN"][:, 0], A["RCIN"][:, col], color=C[i], lw=0.9, label="RCIN." + ad)
ax[2].set_ylim(1000, 2080)
for tt, m, _ in A["MODE"]:
    ax[2].axvline(tt, color="k", lw=0.8, ls="--"); ax[2].text(tt + 0.05, 1980, {0: "STAB", 9: "LAND"}.get(m, str(m)), fontsize=7)
for tt, i in A["EV"]:
    if i in (17, 18, 28): ax[2].axvline(tt, color="gray", lw=0.6, ls=":"); ax[2].text(tt, 1050, {17: "LAND?", 18: "LANDED", 28: "NOT_LANDED"}[i], fontsize=6, rotation=90)
ax[2].set_ylabel("us"); ax[2].set_xlabel("s"); ax[2].legend(loc="upper left", ncol=3, fontsize=7); golge(ax[2]); ax[2].set_xlim(t0 - 2, t1 + 1)
fig.suptitle("%s — 1 s kayan pencere gyro bant RMS (IMU0): yuksek frekans icerigi cubuk hareketleri / kip degisimi / yer temasiyla cakisiyor mu?" % tag, fontsize=9)
fig.tight_layout(); p = os.path.join(OUT, "kayan_bant_rms_gyro_%s.png" % tag); fig.savefig(p, dpi=130); plt.close(fig); graf.append(p)

# ============================================================================ SONUC
L["ucuslar"] = [U]
sonuc = {"meta": {"konfigurasyon": "E) 15 Eylul 12-40-55 — TAM GAZ denemesi; 4S (logdan) + 9x5x3 (kullanici beyani) = D konfigu",
                  "uretim_zamani": dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "python": sys.version.split()[0], "numpy": np.__version__,
                  "arac": os.path.relpath(os.path.abspath(__file__), KOK).replace("\\", "/"), "zaman_ekseni": "TimeUS/1e6 mutlak",
                  "olcutler": {"motorlu_ThO_esik": THO_MOTORLU, "kisa_sicrama_s": KISA_SICRAMA_S, "aski": {"alt_min_m": ASKI_ALT, "vz_maks_ms": ASKI_VZ, "ThO": list(ASKI_THO), "en_az_ornek": ASKI_EN_AZ},
                               "tam_gaz": "CTUN.ThO > %.2f bitisik dilimler (bosluk <= 0,25 s); ayrica RCOU herhangi motor >= MOT_SPIN_MAX ust siniri" % TAM_GAZ_THO,
                               "gaz_bantlari_ThO": ["%.2f-%.2f" % (a, min(b, 1.0)) for a, b in GAZ_BANTLARI], "yapisal_bant_hz": list(YAPISAL_BANT),
                               "rcou_arm_esik": RCOU_ESIK, "motor_kanallari": "SERVO9..12_FUNCTION 36,34,33,35 -> C9=M4,C10=M2,C11=M1,C12=M3",
                               "fft": "Hann pencereli rfft, genlik = 2|X|/sum(w); bant RMS dikdortgen FFT bant sinirlama"}},
         "log": L, "kiyas_D": KIYAS, "grafikler": [os.path.relpath(g, KOK).replace("\\", "/") for g in graf]}

# ---------------------------------------------------------------- bulgular (sayilara bagli metin)
tg0 = tg[0] if tg else None
vt = U["vibe"]["kapsam_tam_gaz(ThO>0.8)"]["IMU0"]; vm = U["vibe"]["kapsam_motorlu"]["IMU0"]; vo = U["vibe"]["kapsam_orta_gaz(0.25-0.75, aski DEGIL)"]["IMU0"]
DA = D_KIYAS["2026-09-15 11-18-16.bin"].get("aski_birlesik", {})
Dv = DA.get("IMU0", {})
fftT = U["imu_fft"].get("tam_gaz", {}).get("IMU0"); fftM = U["imu_fft"]["motorlu"]["IMU0"]; fftR = U["imu_fft"].get("yer_rolanti_armli", {}).get("IMU0") if "yer_rolanti_armli" in U["imu_fft"] else None
fftO = U["imu_fft"].get("orta_gaz_en_uzun", {}).get("IMU0") if "orta_gaz_en_uzun" in U["imu_fft"] else None
rm_ = U["rcou"]["motorlu"]; rtg = U["rcou"].get("tam_gaz(ThO>0.8)"); rog = U["rcou"]["orta_gaz(0.25-0.75)"]
tmr = tm["rate"]; tma = tm["att"]


def tepe_str(d, ad, k=3):
    if not d or not d.get(ad): return "yok"
    tp = d[ad]["yapisal_2_12.5Hz_tepeler"] or []
    g = (lambda x: np.degrees(x)) if ad.startswith("Gyr") else (lambda x: x)
    return ", ".join("%.1f Hz (%.2f)" % (x["f_hz"], g(x["genlik"])) for x in tp[:k]) or "tepe yok"


bul = []
bul.append("LOG: %s, sha %s, %.1f s (t=%.1f-%.1f), ArduCopter %s; TEK arm penceresi %.1f-%.1f s (%.1f s; kaynak %s — ARM(1)/EV10 kaydi yok, EV57 interlock t=%.1f), STAB'da kalkis, t=%.1f LAND(RC) ile inis, disarm LANDED. Motorlu %.1f s (%s), alt maks %.2f m (t=%.1f)." % (
    L["dosya"], L["sha256"][:12], L["log_suresi_s"], L["log_t_ilk"], L["log_t_son"], L["yazilim"], t0, t1, t1 - t0, W["kaynak"],
    next((t for t, i in A["EV"] if i == 57), float("nan")), next((t for t, m, _ in A["MODE"] if m == 9), float("nan")), motorlu_s, U["tur"], alt.max(), U["alt_maks_t"]))
bul.append("HUCRE: ilk BAT.Volt %.2f V -> %dS (%.3f V/hucre; 3S olsaydi %.2f V/hucre olurdu). BATT_LOW/CRT_VOLT = %.0f/%.0f V hala 3S degeri; V_min %.2f V (%.3f V/hucre, t=%.1f, I=%.1f A) esigin ustunde kaldi, pil failsafe yok. Tam gazda sarkma %.2f V (%.3f V/hucre), VoltR ort %.2f V, BAT.Res ort %.4f ohm." % (
    bat[0, 1], n_h, bat[0, 1] / n_h, bat[0, 1] / 3, P["BATT_LOW_VOLT"], P["BATT_CRT_VOLT"], U["bat"]["V_min"], U["bat"]["V_min_hucre"], U["bat"]["V_min_t"], U["bat"]["V_min_I"], U["bat"]["sarkma_V"], U["bat"]["sarkma_V_hucre"], U["bat"]["VoltR_ort"], U["bat"]["BAT_Res_ort_ohm"]))
if tg0:
    bul.append("TAM GAZ (CTUN.ThO > 0,8): %d pencere, toplam %.1f s; en uzunu t=%.2f-%.2f (%.2f s), ThO ort %.3f maks %.3f, ThI (pilot) ort %.3f; irtifa %.2f -> %.2f m (kazanc %.2f m), CRt maks %.2f m/s (ort %.2f), Alt turevi maks %.2f m/s; akim tepe %.1f A (ort %.1f A), V_min %.2f V, guc tepe %.0f W; RCOU M1-M4 ort %s, maks %s, ust sinir (%d us) orani %s; MOTB ThLimit maks %s, ThrAvMx min %s, FailFlags %s. Kalan pencereler: %s." % (
        len(tg), U["tam_gaz_toplam_s"], tg0["t0"], tg0["t1"], tg0["sure_s"], tg0["ThO_ort"], tg0["ThO_maks"], tg0["ThI_ort"], tg0["alt_bas_m"], tg0["alt_son_m"], tg0["alt_kazanc_m"], tg0["CRt_maks_ms"], tg0["CRt_ort_ms"], tg0["vz_turev_maks_ms"],
        tg0["I_maks_A"], tg0["I_ort_A"], tg0["V_min"], tg0["P_maks_W"], tg0["rcou_M_ort"], tg0["rcou_M_maks"], ust, tg0["rcou_ust_sinir_orani"],
        tg0["MOTB"]["ThLimit_maks"] if tg0["MOTB"] else None, tg0["MOTB"]["ThrAvMx_min"] if tg0["MOTB"] else None, tg0["MOTB"]["FailFlags_maks"] if tg0["MOTB"] else None,
        "; ".join("t=%.1f-%.1f %.1f s alt %.1f->%.1f m I_maks %.0f A" % (x["t0"], x["t1"], x["sure_s"], x["alt_bas_m"], x["alt_son_m"], x["I_maks_A"] or 0) for x in tg[1:]) or "yok"))
else:
    bul.append("TAM GAZ: CTUN.ThO > 0,8 hic OLMADI (ThO maks %.3f)." % ThO.max())
bul.append("GAZ PROFILI (motorlu): ThO ort %.3f p50 %.3f p95 %.3f maks %.3f; ThO>0,9 suresi %.1f s, ThO=1,0 suresi %.1f s; RCIN.C3 gaz cubugu maks %d us, >=1900 us suresi %.1f s. Bant sureleri: %s. RCOU: herhangi bir motor ust sinirda %.1f s (%d ornek), 4 motor birden ust sinirda %d ornek." % (
    U["gaz_profili"]["ThO_motorlu"]["ort"], U["gaz_profili"]["ThO_motorlu"]["p50"], U["gaz_profili"]["ThO_motorlu"]["p95"], U["gaz_profili"]["ThO_motorlu"]["maks"],
    U["gaz_profili"]["ThO_ust_0.9_s"], U["gaz_profili"]["ThO_eq_1.0_s"], U["gaz_profili"]["RCIN_C3_gaz_cubugu_us"]["maks"] if U["gaz_profili"]["RCIN_C3_gaz_cubugu_us"] else -1, U["gaz_profili"]["RCIN_C3_ust_1900_s"] or 0,
    U["gaz_profili"]["ThO_bant_sureleri_s"], U["rcou_ust_sinir"]["herhangi_motor_ust_sinirda_s"], U["rcou_ust_sinir"]["herhangi_motor_ust_sinirda_n"], U["rcou_ust_sinir"]["hepsi_ust_sinirda_n"]))
bul.append("ASKI: aski orneklemi %d ornek (%.1f s) < %d -> bu ucusta ASKI YOK; askida istatistik HESAPLANAMAZ (kullanici 'tam gaz' dedi, log da bunu dogruluyor: alt 0 -> %.1f m tirmanis + LAND). Kiyas icin 'orta gaz' (ThO 0,25-0,75, %d ornek %.1f s) bandi verildi ama tirmanis/inis icerir, aski DEGILDIR." % (
    aski.sum(), aski.sum() * dtc, ASKI_EN_AZ, alt.max(), orta.sum(), orta.sum() * dtc))
bul.append("VIBE (IMU0, m/s2) — motorlu: X %.1f/%.1f/%.1f, Y %.1f/%.1f/%.1f, Z %.1f/%.1f/%.1f (ort/p95/maks); TAM GAZ (ThO>0,8, n=%d): X %.1f/%.1f/%.1f, Y %.1f/%.1f/%.1f, Z %.1f/%.1f/%.1f; orta gaz (0,25-0,75, n=%d): Z %.1f/%.1f/%.1f. Clip artisi IMU0 %d, IMU1 %d. Z tepesi %.1f (t=%.1f, ThO %.3f, alt %.1f m). AP esigi 30 asilmadi." % (
    vm["X"]["ort"], vm["X"]["p95"], vm["X"]["maks"], vm["Y"]["ort"], vm["Y"]["p95"], vm["Y"]["maks"], vm["Z"]["ort"], vm["Z"]["p95"], vm["Z"]["maks"],
    vt["Z"]["n"] if vt else 0, vt["X"]["ort"], vt["X"]["p95"], vt["X"]["maks"], vt["Y"]["ort"], vt["Y"]["p95"], vt["Y"]["maks"], vt["Z"]["ort"], vt["Z"]["p95"], vt["Z"]["maks"],
    vo["Z"]["n"] if vo else 0, vo["Z"]["ort"] if vo else -1, vo["Z"]["p95"] if vo else -1, vo["Z"]["maks"] if vo else -1,
    U["vibe"]["clip_toplam"]["IMU0"], U["vibe"]["clip_toplam"]["IMU1"], U["vibe"]["Z_tepe"]["deger"], U["vibe"]["Z_tepe"]["t"], U["vibe"]["Z_tepe"]["ThO_o_anda"], U["vibe"]["Z_tepe"]["alt_o_anda_m"]))
D1 = D_KIYAS["2026-09-15 11-18-16.bin"]
kb = []
for key in ("0.25-0.50", "0.50-0.75", "0.75-0.90", "0.90-1.00"):
    e = E_bant.get(key, {}).get("IMU0"); d = D1["bantlar_birlesik"].get(key, {}).get("IMU0")
    kb.append("%s: E Z %s | D %s" % (key, "%.1f/%.1f/%.1f (n=%d)" % (e["Z"]["ort"], e["Z"]["p95"], e["Z"]["maks"], e["Z"]["n"]) if e else "yok",
                                     "%.1f/%.1f/%.1f (n=%d)" % (d["Z"]["ort"], d["Z"]["p95_maks"], d["Z"]["maks"], d["Z"]["n"]) if d else "YOK (D bu gaza cikmadi)"))
bul.append("D KIYASI (11-18-16, ayni sabah, ayni 4S+9x5x3 beyani; D ThO maks %.3f, p99 %.3f — D'de tam gaz bandi YOK, kiyas yalniz ortusen bantlarda): VibeZ IMU0 ort/p95/maks gaz bandina gore -> %s. D aski (n=%d): X %.1f Y %.1f Z %.1f ort, Z p95 %.1f maks %.1f. E'de VIBE gazla artiyor mu: bantlar %s." % (
    D1["ThO_maks"], D1["ThO_p99_motorlu"], " || ".join(kb), Dv.get("Z", {}).get("n", 0), Dv.get("X", {}).get("ort", -1), Dv.get("Y", {}).get("ort", -1), Dv.get("Z", {}).get("ort", -1), Dv.get("Z", {}).get("p95_maks", -1), Dv.get("Z", {}).get("maks", -1),
    {k: (v["IMU0"]["Z"]["ort"] if v and v.get("IMU0") else None) for k, v in E_bant.items()}))
bul.append("IMU FFT (IMU0, %.1f Hz -> Nyquist %.2f Hz; 2-12,5 Hz yapisal bant tepeleri f (genlik)): TAM GAZ %s s: AccZ %s | GyrX %s | GyrY %s. MOTORLU %.1f s: AccZ %s | GyrX %s | GyrY %s. ORTA GAZ %s: AccZ %s | GyrX %s | GyrY %s. YER ROLANTI %s: AccZ %s | GyrX %s. Bant RMS GyrX (0,3-2 / 2-6 / 6-12,5 Hz, rad/s): tam gaz %s, motorlu %s, rolanti %s; AccZ: tam gaz %s, motorlu %s, rolanti %s. Pervane temel frekansi HESAP (~%s Hz yuksuz, ~%s Hz yuklu, olcum degil) Nyquist'in cok ustunde -> COZULEMEZ; 2-12,5 Hz tepeleri govde/yapisal VEYA alias olabilir (ayirt edilemez)." % (
    L["imu_hz"], L["imu_hz"] / 2, U["imu_fft"]["tam_gaz"]["sure_s"] if "tam_gaz" in U["imu_fft"] else "-", tepe_str(fftT, "AccZ"), tepe_str(fftT, "GyrX"), tepe_str(fftT, "GyrY"),
    U["imu_fft"]["motorlu"]["sure_s"], tepe_str(fftM, "AccZ"), tepe_str(fftM, "GyrX"), tepe_str(fftM, "GyrY"),
    U["imu_fft"]["orta_gaz_en_uzun"]["sure_s"] if fftO else "-", tepe_str(fftO, "AccZ"), tepe_str(fftO, "GyrX"), tepe_str(fftO, "GyrY"),
    U["imu_fft"]["yer_rolanti_armli"]["sure_s"] if fftR else "-", tepe_str(fftR, "AccZ"), tepe_str(fftR, "GyrX"),
    fftT["GyrX"]["bant_rms"] if fftT else None, fftM["GyrX"]["bant_rms"], fftR["GyrX"]["bant_rms"] if fftR else None,
    fftT["AccZ"]["bant_rms"] if fftT else None, fftM["AccZ"]["bant_rms"], fftR["AccZ"]["bant_rms"] if fftR else None,
    U["pervane_frekans_hesap"]["tam_gaz_f_temel_hz_yuksuz"], U["pervane_frekans_hesap"]["tam_gaz_f_temel_hz_yuklu_~0.7"]))
bul.append("TUTUM (motorlu, ATT 10 Hz): roll RMS hata %.2f deg (maks |hata| %.2f), pitch %.2f deg (maks %.2f); Roll maks |%.1f| Pitch maks |%.1f| deg; DesRoll/DesPitch maks |%.1f|/|%.1f| (pilot komutu); hata sifir-gecis frekansi roll %.2f Hz, pitch %.2f Hz; hata FFT tepeleri roll %s, pitch %s (Nyquist 5 Hz). TAM GAZDA: roll/pitch RMS %.2f/%.2f deg. RATE (10 Hz): roll/pitch/yaw rate RMS hata %.1f/%.1f/%.1f deg/s, R/P maks |%.0f|/|%.0f| deg/s; ROut/POut/YOut ort %+.3f/%+.3f/%+.3f, std %.3f/%.3f/%.3f, |out|p90 %.3f/%.3f/%.3f, |out|>=0,5 orani R %.3f P %.3f Y %.3f; AOut ort %.3f maks %.3f. PID P/I/D/FF ayri bilesenleri LOGDA YOK (PIDR/PIDP kapali)." % (
    tma["roll_rms_hata_deg"], tma["roll_hata_maks_abs_deg"], tma["pitch_rms_hata_deg"], tma["pitch_hata_maks_abs_deg"], tma["roll_maks_abs_deg"], tma["pitch_maks_abs_deg"], tma["DesRoll_maks_abs_deg"], tma["DesPitch_maks_abs_deg"],
    tma["roll_hata_sifir_gecis_hz"], tma["pitch_hata_sifir_gecis_hz"], ", ".join("%.1f Hz (%.2f)" % (x["f_hz"], x["genlik"]) for x in tma["roll_hata_fft"]["tepeler"][:3]), ", ".join("%.1f Hz (%.2f)" % (x["f_hz"], x["genlik"]) for x in tma["pitch_hata_fft"]["tepeler"][:3]),
    U["tutum"]["tam_gaz(ThO>0.8)"]["att"]["roll_rms_hata_deg"] if U["tutum"]["tam_gaz(ThO>0.8)"].get("att") else -1, U["tutum"]["tam_gaz(ThO>0.8)"]["att"]["pitch_rms_hata_deg"] if U["tutum"]["tam_gaz(ThO>0.8)"].get("att") else -1,
    tmr["roll_rate_rms_hata_dps"], tmr["pitch_rate_rms_hata_dps"], tmr["yaw_rate_rms_hata_dps"], tmr["R_maks_abs_dps"], tmr["P_maks_abs_dps"],
    tmr["ROut"]["ort"], tmr["POut"]["ort"], tmr["YOut"]["ort"], tmr["ROut"]["std"], tmr["POut"]["std"], tmr["YOut"]["std"], tmr["ROut_abs_p90"], tmr["POut_abs_p90"], tmr["YOut_abs_p90"],
    tmr["doyma_orani_abs_out_ge_0_5"]["R"], tmr["doyma_orani_abs_out_ge_0_5"]["P"], tmr["doyma_orani_abs_out_ge_0_5"]["Y"], tmr["AOut"]["ort"], tmr["AOut"]["maks"]))
bul.append("RCOU MOTOR DENGESI (C9-C12 -> M1 on-sag CCW, M2 arka-sol CCW, M3 on-sol CW, M4 arka-sag CW; motorlu n=%d): ort %s, yayilim %.0f us, en yuksek %s en dusuk %s; motor-ort4 sapmasi %s (std %s); anlik yayilim ort %.0f p95 %.0f maks %.0f us; ciftler yaw CCW-CW %+.0f, pitch on-arka %+.0f, roll sag-sol %+.0f us. ORTA GAZ (n=%d): ort %s, sapma %s, ciftler %s. TAM GAZ (n=%d): ort %s, ust sinir orani %s, sapma %s. Karistirici tutarliligi korr: %s. D 11-18-16 askida (n=%d) sapma %s, ciftler %s." % (
    rm_["n"], rm_["M_ort_pwm"], rm_["yayilim_pwm"], rm_["en_yuksek"], rm_["en_dusuk"], rm_["motor_sapma_ort_pwm"], rm_["motor_sapma_std_pwm"], rm_["anlik_yayilim_pwm"]["ort"], rm_["anlik_yayilim_pwm"]["p95"], rm_["anlik_yayilim_pwm"]["maks"],
    rm_["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"], rm_["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"], rm_["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"],
    rog["n"] if rog else 0, rog["M_ort_pwm"] if rog else None, rog["motor_sapma_ort_pwm"] if rog else None, rog["cift_farklari_pwm"] if rog else None,
    rtg["n"] if rtg else 0, rtg["M_ort_pwm"] if rtg else None, rtg["ust_sinirda_oran"] if rtg else None, rtg["motor_sapma_ort_pwm"] if rtg else None,
    U["rcou"].get("karistirici_tutarlilik_motorlu"), DA.get("rcou", {}).get("n", 0), DA.get("rcou", {}).get("motor_sapma_ort_pwm"), D1["bantlar_birlesik"].get("0.50-0.75", {}).get("rcou", {}).get("cift_farklari_pwm")))
bul.append("EKF: XKF4 %s; ERR %s; EV62 EKF_YAW_RESET t=%.1f (in-flight yaw alignment, kalkis sonrasi olagan). DSF dusurulen %d." % (
    U["ekf"]["XKF4"], U["ekf"]["ERR"], next((t for t, i in A["EV"] if i == 62), float("nan")), L["DSF_dusurulen_toplam"]))
# --- ek bulgular: yavas inis dilimi, kayan bant RMS, D aski gyro referansi, tam gaz+tirmanis FFT
YL = U.get("yavas_inis_LAND")
if YL:
    yr = YL["rcou"]; ya = YL["tutum"].get("att", {}); yv = YL["vibe"]["IMU0"]
    bul.append("EN SAKIN DILIM (LAND yavas inis, t=%.1f-%.1f, %.1f s, ThO ort %.3f, vz ort %.2f m/s, alt %.1f->%.1f m; ASKI DEGIL): cubuklar C1 %.0f+-%.1f C2 %.0f+-%.1f C4 %.0f+-%.1f us (ortada); ROut/POut/YOut ort %+.3f/%+.3f/%+.3f; RCOU M1-M4 ort %s, sapma %s, ciftler yaw CCW-CW %+.0f, pitch on-arka %+.0f, roll sag-sol %+.0f us; VibeZ %.1f/%.1f (ort/p95); roll/pitch RMS hata %.2f/%.2f deg." % (
        YL["t"][0], YL["t"][1], YL["sure_s"], YL["ThO_ort"], YL["vz_ort_ms"], YL["alt_m"][0], YL["alt_m"][1],
        YL["rcin_us"]["C1_roll"]["ort"], YL["rcin_us"]["C1_roll"]["std"], YL["rcin_us"]["C2_pitch"]["ort"], YL["rcin_us"]["C2_pitch"]["std"], YL["rcin_us"]["C4_yaw"]["ort"], YL["rcin_us"]["C4_yaw"]["std"],
        YL["rate_out"]["ROut"]["ort"], YL["rate_out"]["POut"]["ort"], YL["rate_out"]["YOut"]["ort"], yr["M_ort_pwm"], yr["motor_sapma_ort_pwm"],
        yr["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"], yr["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"], yr["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"],
        yv["Z"]["ort"], yv["Z"]["p95"], ya.get("roll_rms_hata_deg", -1), ya.get("pitch_rms_hata_deg", -1)))
DKF = D_KIYAS["2026-09-15 11-18-16.bin"].get("aski_imu_fft", [])
DKB = D_KIYAS["2026-09-15 11-18-16.bin"].get("aski_kayan_bant_rms", [])
if DKF:
    d0 = DKF[0]["IMU0"]
    bul.append("D ASKI GYRO REFERANSI (11-18-16, en uzun aski dilimi t=%.1f-%.1f, %.1f s): 2-12,5 Hz tepeleri GyrX %s | GyrY %s | AccZ %s; bant RMS GyrX %s (rad/s), AccZ %s. -> E'nin orta gaz diliminde gorulen ~6 Hz GyrX tepesi (%s) D askisinda da AYNI frekansta var (%s): E'ye ozgu DEGIL; gaz seviyesinden bagimsiz sabit frekans, pervane katlanmasi (alias) olsaydi devirle kayardi -> govde/kontrol dongusu kaynakli olmasi daha olasi, ama 25 Hz kayitla KESIN DEGIL." % (
        DKF[0]["dilim_t"][0], DKF[0]["dilim_t"][1], DKF[0]["sure_s"], tepe_str(d0, "GyrX"), tepe_str(d0, "GyrY"), tepe_str(d0, "AccZ"), d0["GyrX"]["bant_rms"], d0["AccZ"]["bant_rms"],
        tepe_str(fftO, "GyrX", 1) if fftO else "yok", tepe_str(d0, "GyrX", 1)))
KBm = U["kayan_bant_rms"]["motorlu"]; KBy = U["kayan_bant_rms"]["GyrX_4-12.5_yuksek_anlar"]
bul.append("KAYAN PENCERE (1 s) GYRO BANT RMS 4-12,5 Hz (IMU0, deg/s) — motorlu: GyrX p50 %.1f p95 %.1f maks %.1f (t=%.1f), GyrY p50 %.1f p95 %.1f maks %.1f (t=%.1f); D aski referansi: GyrX p50 %.1f p95 %.1f, GyrY p50 %.1f p95 %.1f. Yuksek anlar (GyrX > %.1f): %s. Tam gaz vurusu (%.1f-%.1f): GyrX %.1f-%.1f, GyrY %.1f-%.1f -> yuksek frekans icerigi GAZLA DEGIL manevralarla (RCIN yaw/roll hareketi t=132.4-133.6, LAND frenleme 137.4-138.4) ve yer temasiyla (140.0-140.8, LAND_COMPLETE_MAYBE %.1f) cakisiyor." % (
    KBm["GyrX_4-12.5Hz_dps"]["p50"], KBm["GyrX_4-12.5Hz_dps"]["p95"], KBm["GyrX_4-12.5Hz_dps"]["maks"], KBm["GyrX_4-12.5_tepe_t"], KBm["GyrY_4-12.5Hz_dps"]["p50"], KBm["GyrY_4-12.5Hz_dps"]["p95"], KBm["GyrY_4-12.5Hz_dps"]["maks"], KBm["GyrY_4-12.5_tepe_t"],
    DKB[0]["GyrX_4-12.5Hz_dps"]["p50"] if DKB else -1, DKB[0]["GyrX_4-12.5Hz_dps"]["p95"] if DKB else -1, DKB[0]["GyrY_4-12.5Hz_dps"]["p50"] if DKB else -1, DKB[0]["GyrY_4-12.5Hz_dps"]["p95"] if DKB else -1,
    KBy["esik_dps(3x motorlu p50)"], KBy["dilimler"],
    dil["tam_gaz"][0] if "tam_gaz" in dil else -1, dil["tam_gaz"][1] if "tam_gaz" in dil else -1,
    U["kayan_bant_rms"]["tam_gaz"]["GyrX_4-12.5Hz_dps"]["min"] if U["kayan_bant_rms"].get("tam_gaz") else -1, U["kayan_bant_rms"]["tam_gaz"]["GyrX_4-12.5Hz_dps"]["maks"] if U["kayan_bant_rms"].get("tam_gaz") else -1,
    U["kayan_bant_rms"]["tam_gaz"]["GyrY_4-12.5Hz_dps"]["min"] if U["kayan_bant_rms"].get("tam_gaz") else -1, U["kayan_bant_rms"]["tam_gaz"]["GyrY_4-12.5Hz_dps"]["maks"] if U["kayan_bant_rms"].get("tam_gaz") else -1,
    next((t for t, i in A["EV"] if i == 17), float("nan"))))
fTT = U["imu_fft"].get("tam_gaz_ve_tirmanis", {}).get("IMU0")
if fTT:
    bul.append("TAM GAZ + TIRMANIS DILIMI FFT (t=%.1f-%.1f, %.1f s, n=%d; tam gaz tek basina %d ornek < 32 oldugu icin FFT yapilamadi): AccZ tepeleri %s | GyrX %s | GyrY %s; bant RMS GyrX %s, AccZ %s." % (
        U["imu_fft"]["tam_gaz_ve_tirmanis"]["dilim_t"][0], U["imu_fft"]["tam_gaz_ve_tirmanis"]["dilim_t"][1], U["imu_fft"]["tam_gaz_ve_tirmanis"]["sure_s"], fTT["n"],
        int(len(kes(A["IMU"][A["IMU"][:, 1] == 0], dil["tam_gaz"][0], dil["tam_gaz"][1]))) if "tam_gaz" in dil else 0,
        tepe_str(fTT, "AccZ"), tepe_str(fTT, "GyrX"), tepe_str(fTT, "GyrY"), fTT["GyrX"]["bant_rms"], fTT["AccZ"]["bant_rms"]))
kt = U["rcou"].get("karistirici_tutarlilik_motorlu", {})
bul.append("KARISTIRICI TUTARLILIGI (RATE ayni-dongu ornegiyle hizalanmis; RATE.t - RCOU.t = %s ms): korr(ROut, sol-sag) %s, korr(POut, on-arka) %s, korr(YOut, CCW-CW) %s -> motor komutlari kontrolcu cikisini birebir izliyor; hicbir motorun komutu 'bagimsiz' sapmiyor (gevsek kol motor KOMUTUNDA degil, KOMUTA VERILEN TEPKIDE gorunurdu — o da RATE hata/tutum hatasi olarak: roll/pitch RMS hata E motorlu %.2f/%.2f deg vs D aski %.2f/%.2f deg, E manevrali ucus). NOT: sonraki-ornek hizalamasiyla korr %s cikar — bu ARTEFAKTTIR, kullanilmadi." % (
    kt.get("RATE_t_eksi_RCOU_t_ms_medyan"), kt.get("korr(ROut, sol-sag_pwm)"), kt.get("korr(POut, on-arka_pwm)"), kt.get("korr(YOut, CCW-CW_pwm)"),
    tma["roll_rms_hata_deg"], tma["pitch_rms_hata_deg"], DA.get("att", {}).get("roll_rms_hata_deg", [-1])[0], DA.get("att", {}).get("pitch_rms_hata_deg", [-1])[0], kt.get("korr(ROut, sol-sag_pwm)_sonraki_ornek_hizalama")))

# --- mekanik hipotez degerlendirmesi (yapisal)
Dcf = DA.get("rcou", {}).get("ucus_basina_cift_farklari_pwm", [])
sonuc["mekanik_hipotez"] = {
    "kullanici_gozlemi": L["kullanici_beyani"]["gozlem"],
    "kanit_lehinde": [
        "Statik motor komutu dengesizligi D ve E'de AYNI YONDE: sag motorlar (M1+M4) sol'dan yuksek (D aski ucus basina sag-sol %s us; E motorlu %+.0f, E LAND yavas inis %+.0f us) ve arka motorlar on'den yuksek (D on-arka %s; E %+.0f / LAND %+.0f). -> agirlik merkezi sag-arkada VEYA sag/arka motor-pervane itkisi zayif; M4 (arka-sag) bu yuzden en yuksek komutlu motor ve tam gazda ILK doyan motor (1949 us'de %.0f%% sure) — diger 3 motor 7-55 us altta kaldi." % (
            [x["sag(M1+M4)-sol(M2+M3)_roll"] for x in Dcf], rm_["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"], YL["rcou"]["cift_farklari_pwm"]["sag(M1+M4)-sol(M2+M3)_roll"] if YL else float("nan"),
            [x["on(M1+M3)-arka(M2+M4)_pitch"] for x in Dcf], rm_["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"], YL["rcou"]["cift_farklari_pwm"]["on(M1+M3)-arka(M2+M4)_pitch"] if YL else float("nan"),
            100 * (rtg["ust_sinirda_oran"]["M4"] if rtg else 0)),
        "Tam gaz vurusunda cubuk ortada (RCIN C1 1499) iken govde +5,0 deg saga yatti (Roll 130.5-131.0: 1.6->5.0 deg, DesRoll 0), ROut -0,09'a kadar sol torku istendi -> sag taraf itki/sol taraf itkiden dusuk (ayni komutta) — sag-arka kol/motor/pervane suphesi. (ALTERNATIFLER: agirlik merkezi kaymasi; spool-up rampasinda (MOT_SPOOL_TIME, 1300->1949 us 0,4 s) ESC/motor kalkis tepkisi farki — logdan ayirt edilemez.)",
        "Yaw statik dengesizligi D'de tutarli +CCW (ucus basina CCW-CW %s us, YOut ort +0,025..+0,086) iken E'nin sakin diliminde %+.0f us / YOut %+.3f (cubuk ortada) -> 11:18 ile 12:40 arasinda yaw tork dengesi DEGISMIS gorunuyor; motor egikligi (gevsek kol donmesi) bunu yapabilir. Zayif kanit: E dilimi %.1f s, inis halinde." % (
            [x["CCW(M1+M2)-CW(M3+M4)_yaw"] for x in Dcf], YL["rcou"]["cift_farklari_pwm"]["CCW(M1+M2)-CW(M3+M4)_yaw"] if YL else float("nan"), YL["rate_out"]["YOut"]["ort"] if YL else float("nan"), YL["sure_s"] if YL else 0),
    ],
    "kanit_aleyhinde": [
        "VIBE (AP'nin 5 Hz+ ivme gurultu olcusu) E'de D ile AYNI: ThO 0,25-0,50 bandinda VibeZ %.1f vs D %.1f; tam gazda (0,9-1,0) %.1f, yani gaz artinca vibe ARTMADI; clip 0. Pervane/balans kaynakli genis bant titresim icin kanit YOK (kullanicinin 'titresim olmadi' gozlemiyle uyumlu)." % (
            E_bant.get("0.25-0.50", {}).get("IMU0", {}).get("Z", {}).get("ort", -1), D1["bantlar_birlesik"].get("0.25-0.50", {}).get("IMU0", {}).get("Z", {}).get("ort", -1), E_bant.get("0.90-1.00", {}).get("IMU0", {}).get("Z", {}).get("ort", -1)),
        "2-12,5 Hz gyro icerigi E'de D askisindan yuksek DEGIL (motorlu bant RMS GyrX 2-6 Hz %.3f vs D %.3f rad/s; 6-12,5 Hz %.3f vs %.3f) ve zamanda yuksek frekans icerigi cubuk hareketleri / LAND frenleme / yer temasiyla cakisiyor, gazla degil. Surekli (kendiliginden) dusuk frekansli salinim yok: roll/pitch hata FFT'si 0,4-1,4 Hz'de (pilot manevra bandi), sifir gecis %.2f/%.2f Hz." % (
            fftM["GyrX"]["bant_rms"]["2-6Hz"], DKF[0]["IMU0"]["GyrX"]["bant_rms"]["2-6Hz"] if DKF else -1, fftM["GyrX"]["bant_rms"]["6-12.5Hz"], DKF[0]["IMU0"]["GyrX"]["bant_rms"]["6-12.5Hz"] if DKF else -1, tma["roll_hata_sifir_gecis_hz"], tma["pitch_hata_sifir_gecis_hz"]),
        "Motor komutlari kontrolcu cikisini korr %s/%s/%s ile izliyor; RATE/ATT doyma yok (|out|>=0,5 orani 0), MOTB thrust_balanced hep 1 (FailFlags=2), ERR yok, EKF innovasyon testleri < 0,35. Kontrolcu 'kaybetmis' degil." % (kt.get("korr(ROut, sol-sag_pwm)"), kt.get("korr(POut, on-arka_pwm)"), kt.get("korr(YOut, CCW-CW_pwm)")),
    ],
    "olculemeyen": [
        "Kol egilme/gevseklik modlari tipik 15-40 Hz -> IMU 25 Hz (Nyquist 12,5 Hz) kayitla GORULEMEZ; ATT/RATE 10 Hz (Nyquist 5 Hz). Pervane temel frekansi (~%s Hz hesap) da cozulemez. 'Kollarda sallanti' gorsel gozlemini log ne dogrular ne curutur." % U["pervane_frekans_hesap"]["tam_gaz_f_temel_hz_yuklu_~0.7"],
        "Askida ornek yok (2 ornek); statik denge icin en sakin dilim %.1f s'lik LAND inisi." % (YL["sure_s"] if YL else 0),
        "PIDR/PIDP yok (LOG_BITMASK bit12 kapali): P/I/D/FF bilesenleri ve I-terim birikimi (surekli tork dengesizliginin en net gostergesi) cikarilamaz.",
    ],
    "hukum": "BELIRSIZ, agirlik: (1) pervane/balans titresimi YOK (VIBE=D, gazla artmiyor); (2) PID/ATC salinimi YOK (kendiliginden salinim yok, doyma yok); (3) sag-arka (M4) yonunde tutarli statik itki/agirlik dengesizligi VAR (D ve E) ve M4 tam gazda tek doyan motor — bu 'gevsek/egik kol' ile UYUMLU ama 'agirlik merkezi kaymasi' ile de uyumlu, log ayirt edemez; (4) yaw dengesinin D->E degisimi motor egikligi degisimine isaret edebilir (zayif). Onerilen yer testi (uçuş DEĞİL): kollari elle burarak gevseklik; motor eksen dikligi (M4 basta); 4 pervanenin ayni olup olmadigi; agirlik merkezi. Kesin olcum icin INS_LOG_BAT_MASK=1 (+ LOG_BITMASK bit12 PID) ile 20 s aski logu.",
}
sonuc["bulgular"] = bul
sonuc["kullanici_gozlemi"] = L["kullanici_beyani"]["gozlem"]

with open(os.path.join(OUT, "ozet.json"), "w", encoding="utf-8") as f:
    json.dump(temizle(sonuc), f, ensure_ascii=False, indent=1)
print("OK ozet.json +", len(graf), "grafik ->", OUT)
for b in bul:
    print("-", b)
