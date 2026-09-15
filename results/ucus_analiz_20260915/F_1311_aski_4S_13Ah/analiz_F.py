# -*- coding: utf-8 -*-
"""Konfigurasyon F: 4S 13 000 mAh + 9x5x3, 15 Eylul 2026 13:11:32 logu - kodla GUIDED kalkis, ~1 dk aski, LAND.
Ham .bin (pymavlink DFReader) + numpy + matplotlib; SciPy YOK (anayasa m.4).
Her sayi logdan; pil/pervane/kutle/KV LOGDA YOK -> 'kullanici_beyani' / 'HESAP' etiketiyle yazilir.
Zaman ekseni: TimeUS/1e6 mutlak (tum_loglar.json ile ayni).
"""
import json, os, sys, math, hashlib, collections, datetime
import numpy as np
from pymavlink import DFReader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

ROOT = "O:/navitas"
LOG = "results/ucus_20260915/2026-09-15 13-11-32.bin"
OUT = os.path.join(ROOT, "results/ucus_analiz_20260915/F_1311_aski_4S_13Ah")
C_OZET = os.path.join(ROOT, "results/ucus_analiz_20260915/C_3S_9x5x3/ozet.json")
D_OZET = os.path.join(ROOT, "results/ucus_analiz_20260915/D_4S_9x5x3/ozet.json")
os.makedirs(OUT, exist_ok=True)

# ---- olcutler (C/D analizleriyle AYNI)
THO_MOTORLU = 0.15
KISA_S = 5.0
ASKI_ALT_MIN = 1.0
ASKI_VZ = 0.5
ASKI_THO = (0.25, 0.75)
ASKI_EN_AZ = 10
HUCRE_N = 4                      # ilk BAT gerilimi 15,57 V -> 3,89 V/hucre (3S olsa 5,19 V/hucre olurdu)
PIL_MAH_BEYAN = 13000.0          # kullanici beyani (logda yok)
KULLANILABILIR = 0.80
V_HUCRE_LOW, V_HUCRE_CRT = 3.5, 3.3   # gorevde istenen esikler (V/hucre)
V_HUCRE_ARM_ONERI = 3.6          # oneri: BATT_ARM_VOLT en az LOW'un ustunde olmali
VIBE_ESIK_IYI, VIBE_ESIK_KOTU = 30.0, 60.0   # ArduPilot VIBE kilavuzu (m/s2)
MOTOR_KV = 980                   # SunnySky X2220 980KV (kullanici beyani; scripts/ucus_bin_analiz.py ile ayni) - yalniz HESAP
PAL_N = 3                        # 9x5x3 -> 3 pal (kullanici beyani)

# dataviz varsayilan kategorik sira (D analiziyle ayni)
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURF = "#fcfcfb"; TXT = "#0b0b0b"; TXT2 = "#52514e"; GRID = "#e6e5e1"; ASKI_GOLGE = "#2a78d6"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": "#cfceca",
                     "axes.labelcolor": TXT, "xtick.color": TXT2, "ytick.color": TXT2, "text.color": TXT,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 9, "legend.frameon": False, "lines.linewidth": 1.2})

EV_AD = {10: "ARMED", 11: "DISARMED", 15: "AUTO_ARMED", 17: "LAND_COMPLETE_MAYBE", 18: "LAND_COMPLETE",
         19: "LOST_GPS", 25: "SET_HOME", 28: "NOT_LANDED", 54: "MOTORS_EMERGENCY_STOPPED",
         56: "MOTORS_INTERLOCK_DISABLED", 57: "MOTORS_INTERLOCK_ENABLED", 60: "EKF_ALT_RESET",
         61: "LAND_CANCELLED_BY_PILOT", 62: "EKF_YAW_RESET", 67: "GPS_PRIMARY_CHANGED", 73: "LAND_REPO_ACTIVE"}
MODE_AD = {0: "STAB", 1: "ACRO", 2: "ALTHOLD", 3: "AUTO", 4: "GUIDED", 5: "LOIT", 6: "RTL", 9: "LAND", 16: "POSHOLD", 21: "SMART_RTL"}
RSN_AD = {0: "BILINMIYOR", 1: "RC", 2: "GCS", 3: "RADYO_FS", 4: "PIL_FS", 5: "GCS_FS", 6: "EKF_FS", 19: "CRASH", 25: "FAILSAFE", 26: "INITIALISED", 31: "STARTUP"}
ERR_SUB = {2: "RADIO", 5: "FS_RADYO", 6: "FS_PIL", 8: "FS_GCS", 12: "CRASH_CHECK", 16: "EKFCHECK", 17: "FS_EKFINAV", 24: "EKF_PRIMARY", 25: "THRUST_LOSS", 29: "FS_VIBE"}
ARM_YONTEM = {0: "RUDDER", 1: "MAVLINK", 2: "AUXSWITCH", 3: "MOTORTEST", 4: "SCRIPTING", 13: "LANDED"}
MOTOR_FN = {33: "M1", 34: "M2", 35: "M3", 36: "M4"}


def r(x, n=3):
    if x is None: return None
    if isinstance(x, (float, np.floating, int, np.integer)):
        if isinstance(x, (float, np.floating)) and not np.isfinite(x): return None
        return round(float(x), n)
    return x


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def istat(x):
    x = np.asarray(x, float)
    if len(x) == 0: return None
    return {"n": int(len(x)), "ort": r(x.mean()), "p50": r(np.percentile(x, 50)), "p05": r(np.percentile(x, 5)),
            "p95": r(np.percentile(x, 95)), "min": r(x.min()), "maks": r(x.max()), "std": r(x.std())}


def ma(x, n=5):
    if len(x) < n: return x
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
        else: i += 1
    return out


def en_uzun_kosu(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0; best = max(best, cur)
    return best


def yakin(tref, t, x):
    """x(t) dizisinden tref zamanlarina en yakin ornekler (searchsorted)."""
    j = np.clip(np.searchsorted(t, tref), 0, len(t) - 1)
    return x[j]


def wrap(d):
    return (d + 180.0) % 360.0 - 180.0


def fft_tepeler(t, x, en_az_hz=0.3, k=6):
    if len(x) < 32: return None
    dt = np.median(np.diff(t)); fs = 1.0 / dt
    x = x - x.mean(); w = np.hanning(len(x)); X = np.fft.rfft(x * w); f = np.fft.rfftfreq(len(x), dt)
    amp = 2.0 * np.abs(X) / w.sum()
    m = f >= en_az_hz
    idx = [i for i in range(1, len(f) - 1) if m[i] and amp[i] >= amp[i - 1] and amp[i] >= amp[i + 1]]
    idx.sort(key=lambda i: -amp[i])
    band = (f >= 2.0) & (f <= 15.0)
    bidx = [i for i in idx if band[i]]
    return {"fs_hz": r(fs, 2), "nyquist_hz": r(fs / 2, 2), "n": int(len(x)), "sure_s": r(t[-1] - t[0], 2),
            "cozunurluk_hz": r(f[1], 3), "rms": r(float(np.sqrt(np.mean(x ** 2))), 3),
            "tepeler": [{"f_hz": r(f[i], 2), "genlik": r(amp[i], 3)} for i in idx[:k]],
            "band_2_15Hz_tepeler": [{"f_hz": r(f[i], 2), "genlik": r(amp[i], 3)} for i in bidx[:4]],
            "band_2_15Hz_rms": r(float(np.sqrt(np.sum(amp[band] ** 2) / 2)), 3),
            "_f": f, "_amp": amp}


# ============================================================================ oku
def oku(fn):
    log = DFReader.DFReader_binary(fn)
    D = collections.defaultdict(list); parm = {}; parm_seri = collections.defaultdict(list); sayac = collections.Counter()
    while True:
        m = log.recv_msg()
        if m is None: break
        ty = m.get_type(); sayac[ty] += 1
        tu = getattr(m, "TimeUS", None); t = tu / 1e6 if tu is not None else None
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
        elif ty == "PSCD": D["PSCD"].append((t, m.TPD, m.PD, m.DVD, m.TVD, m.VD, m.DAD, m.TAD, m.AD))
        elif ty == "POS": D["POS"].append((t, m.Alt, m.RelHomeAlt, m.RelOriginAlt))
        elif ty == "GPS": D["GPS"].append((t, m.Status, m.NSats, m.HDop))
        elif ty == "DSF": D["DSF"].append((t, m.Dp))
        elif ty == "PM": D["PM"].append((t, m.NLon, m.MaxT, m.Load))
        elif ty == "EV": D["EV"].append((t, int(m.Id)))
        elif ty == "ERR": D["ERR"].append((t, int(m.Subsys), int(m.ECode)))
        elif ty == "MODE": D["MODE"].append((t, int(m.Mode), int(m.Rsn)))
        elif ty == "ARM": D["ARM"].append((t, int(m.ArmState), int(m.Method), int(getattr(m, "Forced", 0))))
        elif ty == "MSG": D["MSG"].append((t, str(m.Message)))
        elif ty == "PARM":
            parm_seri[m.Name].append((t, float(m.Value)))
            if m.Name not in parm: parm[m.Name] = float(m.Value)
    A = {k: np.array(v, dtype=float) for k, v in D.items() if k not in ("MSG", "EV", "ERR", "MODE", "ARM")}
    for k in ("EV", "ERR", "MODE", "ARM", "MSG"): A[k] = D[k]
    A["parm"] = parm; A["parm_seri"] = parm_seri; A["sayac"] = sayac
    return A


def mode_at(A, t):
    m = None
    for tt, md, _ in A["MODE"]:
        if tt <= t: m = md
        else: break
    return m


# ============================================================================ ana
fn = os.path.join(ROOT, LOG)
A = oku(fn)
P = A["parm"]
ozet = {"meta": {}, "ucus": {}, "aski": {}, "pil": {}, "ucus_suresi": {}, "vibe": {}, "fft": {}, "rcou": {}, "tutum": {},
        "ekf_olaylar": {}, "failsafe": {}, "kiyas_C_D": {}, "grafikler": [], "bulgular": []}

# ---- meta
yazilim = next((s for _, s in A["MSG"] if s.startswith("ArduCopter")), None)
ozet["meta"] = {
    "konfigurasyon": "F) 4S 13 000 mAh + 9x5x3, kodla GUIDED kalkis -> ~1 dk aski -> LAND (15 Eylul 2026 13:11:32)",
    "uretim_zamani": datetime.datetime.now().isoformat(timespec="seconds"),
    "betik": "results/ucus_analiz_20260915/F_1311_aski_4S_13Ah/analiz_F.py",
    "python": sys.version.split()[0], "numpy": np.__version__,
    "log": {"dosya": LOG, "sha256": sha256(fn), "bayt": os.path.getsize(fn), "yazilim": yazilim,
            "STAT_BOOTCNT": P.get("STAT_BOOTCNT"), "STAT_FLTTIME_kayitlari": [[r(t, 1), v] for t, v in A["parm_seri"].get("STAT_FLTTIME", [])],
            "log_t_ilk": r(A["CTUN"][0, 0], 2), "log_t_son": r(A["CTUN"][-1, 0], 2)},
    "kullanici_beyani": {"pil": "4S 13 000 mAh", "pervane": "9x5x3 (9 inc, 5 pitch, 3 pal)", "gorev": "~3 m'de 1 dk aski, kodla GUIDED + LAND",
                         "kaynak": "kullanici beyani 15 Eylul 2026; pil/pervane/kutle/KV LOGDA YOK"},
    "olcutler": {"motorlu_ThO_esik": THO_MOTORLU, "aski": {"alt_min_m": ASKI_ALT_MIN, "vz_maks_ms": ASKI_VZ, "ThO": list(ASKI_THO), "en_az_ornek": ASKI_EN_AZ,
                 "vz_kaynak": "CTUN.Alt turevi (np.gradient), 5 ornek hareketli ortalama"},
                 "alt_taban": "arm sonrasi ilk 1 s CTUN.Alt medyani (CTUN.Alt EKF-orijinine goredir; POS.RelHomeAlt ile capraz kontrol edildi)",
                 "vibe_esikleri_ms2": [VIBE_ESIK_IYI, VIBE_ESIK_KOTU], "hucre_n_dayanak": "ilk BAT.Volt %.2f V / 4 = %.3f V/hucre (3S olsa %.2f V/hucre: imkansiz)" % (A["BAT"][0, 1], A["BAT"][0, 1] / 4, A["BAT"][0, 1] / 3)},
    "mesaj_n": {k: int(A["sayac"].get(k, 0)) for k in ("CTUN", "BAT", "VIBE", "RCOU", "ATT", "RATE", "IMU", "XKF4", "PSCD", "MOTB", "EV", "ARM", "MODE", "ERR", "MSG", "PARM", "ESC", "RPM", "ISBH", "DSF")},
    "DSF_dusurulen_toplam": int(A["DSF"][:, 1].sum()) if len(A.get("DSF", [])) else 0,
    "DSF_not": "DSF.Dp her saniye sabit 12 (bir mesaj tipi surekli yazilamiyor); CTUN/BAT/VIBE/RCOU 10 Hz, ATT/RATE 10 Hz, IMU 25 Hz arm penceresinde EKSIKSIZ (bosluk yok; tek 18,6 s bosluk 217,7-236,3 s arm ONCESI, disarm kayit durmasi)",
}
imu_t = A["IMU"][A["IMU"][:, 1] == 0, 0]
ozet["meta"]["imu_hz"] = r(1 / np.median(np.diff(imu_t)), 2)
ozet["meta"]["imu_not"] = "INS_LOG_BAT_MASK=0 -> hizli IMU (ISBH/ISBD) YOK; IMU mesaji %.1f Hz -> Nyquist %.2f Hz; ESC/RPM mesaji YOK -> pervane frekansi olculemez" % (ozet["meta"]["imu_hz"], ozet["meta"]["imu_hz"] / 2)

# ---- arm penceresi
arm = A["ARM"]; t0 = t1 = None
for t, s, meth, forced in arm:
    if s == 1 and t0 is None: t0 = (t, meth)
    elif s == 0 and t0 is not None and t1 is None: t1 = (t, meth)
assert t0 and t1, "ARM penceresi bulunamadi"
T0, T1 = t0[0], t1[0]
ct = A["CTUN"]; cm = (ct[:, 0] >= T0) & (ct[:, 0] <= T1); c = ct[cm]
tc = c[:, 0]; ThI = c[:, 1]; ThO = c[:, 2]; ThH = c[:, 3]; DAlt = c[:, 4]; Alt = c[:, 5]; DCRt = c[:, 7]; CRt = c[:, 8]
dtc = float(np.median(np.diff(tc)))
taban = float(np.median(Alt[tc <= T0 + 1.0])); alt = Alt - taban
vz = ma(np.gradient(Alt, tc), 5)
mot = ThO > THO_MOTORLU
pos = A["POS"]; pw = pos[(pos[:, 0] >= T0) & (pos[:, 0] <= T1)]
motorlu_s = float(mot.sum() * dtc); tm0, tm1 = tc[mot][0], tc[mot][-1]
ev_list = [(t, EV_AD.get(i, str(i))) for t, i in A["EV"]]
ozet["ucus"] = {
    "arm_t": r(T0, 2), "disarm_t": r(T1, 2), "pencere_s": r(T1 - T0, 1), "arm_yontemi": ARM_YONTEM.get(t0[1], str(t0[1])), "disarm_yontemi": ARM_YONTEM.get(t1[1], str(t1[1])),
    "kip_arm": MODE_AD.get(mode_at(A, T0 + 0.05)), "kip_gecisleri": [{"t": r(tt, 2), "kip": MODE_AD.get(md, str(md)), "sebep": RSN_AD.get(rs, str(rs))} for tt, md, rs in A["MODE"]],
    "olaylar_EV": [{"t": r(t, 2), "olay": ad} for t, ad in ev_list],
    "ctun_hz": r(1 / dtc, 1), "ctun_n_pencere": int(len(tc)),
    "alt_taban_m_CTUN_Alt": r(taban, 2), "alt_maks_m": r(alt.max(), 2), "alt_maks_m_POS_RelHomeAlt": r(pw[:, 2].max(), 2) if len(pw) else None,
    "DAlt_maks_m_taban_cikarilmis": r(DAlt.max() - taban, 2),
    "motorlu_s": r(motorlu_s, 1), "motorlu_t": [r(tm0, 1), r(tm1, 1)],
    "tur": "ucus" if motorlu_s >= KISA_S else ("kisa_sicrama" if mot.any() else "arm_yalniz"),
    "ThH_bas": r(ThH[0], 4), "ThH_son": r(ThH[-1], 4), "ThH_min": r(ThH.min(), 4), "ThH_maks": r(ThH.max(), 4),
    "MOT_THST_HOVER_PARM_kayitlari": [[r(t, 2), r(v, 6)] for t, v in A["parm_seri"].get("MOT_THST_HOVER", [])],
    "ThO_motorlu": istat(ThO[mot]),
}

# ---- aski orneklemi
aski = (alt >= ASKI_ALT_MIN) & (np.abs(vz) < ASKI_VZ) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
aski_crt = (alt >= ASKI_ALT_MIN) & (np.abs(CRt) < ASKI_VZ * 100) & (ThO >= ASKI_THO[0]) & (ThO <= ASKI_THO[1])
ds = dilimler(tc, aski); en = max(ds, key=lambda d: d[1] - d[0])
ta = tc[aski]
b = A["BAT"]; bb = b[(b[:, 0] >= T0 - 10.0) & (b[:, 0] <= T1 + 10.0)]
Va = yakin(ta, bb[:, 0], bb[:, 1]); Ia = yakin(ta, bb[:, 0], bb[:, 3]); VRa = yakin(ta, bb[:, 0], bb[:, 2]); Resa = yakin(ta, bb[:, 0], bb[:, 6])
Pa = Va * Ia
ozet["aski"] = {
    "n": int(aski.sum()), "sure_s": r(aski.sum() * dtc, 1), "n_CRt_kaynakli_capraz": int(aski_crt.sum()),
    "dilim_n": len(ds), "en_uzun_dilim_t": [r(en[0], 2), r(en[1], 2)], "en_uzun_dilim_s": r(en[1] - en[0], 1),
    "alt_m": istat(alt[aski]), "alt_egim_en_uzun_dilim_ms": r(np.polyfit(tc[(tc >= en[0]) & (tc <= en[1])], alt[(tc >= en[0]) & (tc <= en[1])], 1)[0], 3),
    "vz_abs_ort_ms": r(np.abs(vz[aski]).mean(), 3), "DCRt_sifir_orani": r(float(np.mean(DCRt[aski] == 0)), 3),
    "ThO": istat(ThO[aski]), "ThI": istat(ThI[aski]),
    "V": istat(Va), "V_hucre": {"ort": r(Va.mean() / HUCRE_N), "min": r(Va.min() / HUCRE_N), "maks": r(Va.max() / HUCRE_N), "bas": r(Va[0] / HUCRE_N), "son": r(Va[-1] / HUCRE_N)},
    "VoltR_dinlenme_tahmini_FC": istat(VRa),
    "I_A": istat(Ia), "P_W": istat(Pa), "P_W_ort_x_ort": r(Va.mean() * Ia.mean(), 1),
    "mAh_per_s": r(Ia.mean() / 3.6, 3), "mAh_per_dk": r(Ia.mean() / 3.6 * 60, 0),
    "MOT_THST_HOVER_vs_ThO": {"MOT_THST_HOVER": r(ThH[0], 4), "ThO_aski_ort": r(ThO[aski].mean(), 4), "ThO_aski_p50": r(np.percentile(ThO[aski], 50), 4),
                              "fark": r(ThH[0] - ThO[aski].mean(), 4), "fark_pct_ThO": r(100 * (ThH[0] - ThO[aski].mean()) / ThO[aski].mean(), 1)},
}
ozet["ucus"]["aski_s"] = ozet["aski"]["sure_s"]

# ---- hover ogrenme kosullari (Copter::update_throttle_hover) - neden ThH degismedi?
ps = A["PSCD"]; pp = ps[(ps[:, 0] >= T0) & (ps[:, 0] <= T1)]
aa_all = A["ATT"]; aa = aa_all[(aa_all[:, 0] >= T0) & (aa_all[:, 0] <= T1)]
if len(pp):
    DVD = yakin(tc, pp[:, 0], pp[:, 3]); VD = yakin(tc, pp[:, 0], pp[:, 5])
    dvd_ok = np.abs(DVD) * 100.0 < 1.1920929e-7
    rp = yakin(tc, aa[:, 0], aa[:, [2, 4]]); rp_ok = (np.abs(rp[:, 0]) < 5) & (np.abs(rp[:, 1]) < 5)
    vz_ok = np.abs(VD) < 0.6
    nl = [t for t, i in A["EV"] if i == 28 and T0 <= t <= T1]; lc = [t for t, i in A["EV"] if i in (17, 18) and T0 <= t <= T1]
    havada = (tc >= (nl[0] if nl else tm0)) & (tc <= (min([x for x in lc if x > (nl[0] if nl else tm0)], default=T1)))
    uygun = havada & dvd_ok & rp_ok & vz_ok & (ThO > 0)
    ozet["ucus"]["hover_ogrenme"] = {
        "MOT_HOVER_LEARN": P.get("MOT_HOVER_LEARN"), "havada_s_EV28_EV17": r(havada.sum() * dtc, 1),
        "kosul_oranlari_havada": {"is_zero(PSCD.DVD)": r(float(dvd_ok[havada].mean()), 3), "|VD|<0.6m/s": r(float(vz_ok[havada].mean()), 3),
                                  "|roll|,|pitch|<5deg": r(float(rp_ok[havada].mean()), 3), "hepsi": r(float(uygun[havada].mean()), 3)},
        "uygun_s": r(uygun.sum() * dtc, 1), "DVD_havada_abs_p50_ms": r(float(np.median(np.abs(DVD[havada]))), 4), "DVD_havada_abs_p90_ms": r(float(np.percentile(np.abs(DVD[havada]), 90)), 4),
        "DVD_askida_abs_p50_ms": r(float(np.median(np.abs(DVD[aski]))), 4), "DVD_askida_sifir_orani": r(float(dvd_ok[aski].mean()), 3),
        "ThH_degisim_log": r(ThH[-1] - ThH[0], 5),
        "not": "GUIDED kipinde pos_control hedef dikey hiz (PSCD.DVD) tam sifir olmadikca ogrenme calismaz (is_zero, FLT_EPSILON). PSCD 10 Hz orneklendigi icin 100 Hz'deki kisa sifir anlari kacabilir."}

# ---- pil: sarkma, ic direnc (numpy.polyfit dV/dI), tuketim
onc = b[(b[:, 0] >= T0 - 5.0) & (b[:, 0] < T0)]
ONC_NOT = "arm oncesi 5 s"
if len(onc) == 0:
    # kayit 217,7-236,3 s arasinda durdu (disarm); arm oncesi yuksuz referans = bosluktan onceki son 5 s (motor kapali, ~0,3 A)
    t_gap = ct[np.searchsorted(ct[:, 0], T0) - 1, 0]
    onc = b[(b[:, 0] >= t_gap - 5.0) & (b[:, 0] <= t_gap)]
    ONC_NOT = "kayit boslugu (217,7-236,3 s) oncesi son 5 s, motor kapali (arm oncesi 5 s'de BAT ornegi yok)"
bw = b[(b[:, 0] >= T0) & (b[:, 0] <= T1)]
bmot = bw[(bw[:, 0] >= tm0) & (bw[:, 0] <= tm1)]
imin = int(np.argmin(bmot[:, 1]))
V0 = float(b[0, 1])


def polyfit_R(I, V):
    if len(I) < 5 or I.std() < 1.0: return None
    p = np.polyfit(I, V, 1); rr = np.corrcoef(I, V)[0, 1]
    return {"n": int(len(I)), "I_aralik_A": [r(I.min(), 1), r(I.max(), 1)], "R_paket_ohm": r(-p[0], 4), "R_paket_mohm": r(-p[0] * 1000, 1),
            "R_hucre_mohm": r(-p[0] * 1000 / HUCRE_N, 1), "V_kesim_I0": r(p[1], 3), "r2": r(rr * rr, 3)}


# (a) kalkis gecisi: arm -> ilk aski ornegi (I ~0 -> ~37 A birkac saniyede; SoC degismez)
kal = b[(b[:, 0] >= T0 - 2.0) & (b[:, 0] <= ta[0])]
# (b) inis gecisi: LAND_COMPLETE_MAYBE (EV17) -> disarm + 3 s (I ~37 -> ~0)
ev17 = next((t for t, i in A["EV"] if i == 17 and T0 <= t <= T1 + 1), T1 - 1.5)
ini = b[(b[:, 0] >= ev17 - 0.5) & (b[:, 0] <= T1 + 3.0)]
# (c) tum pencere (+/-5 s) - SoC kaymasi karisir, yalniz kiyas icin
tum = b[(b[:, 0] >= T0 - 5.0) & (b[:, 0] <= T1 + 5.0)]
# (d) yalniz aski ornekleri (akim araligi dar -> zayif)
R_a = polyfit_R(kal[:, 3], kal[:, 1]); R_b = polyfit_R(ini[:, 3], ini[:, 1]); R_c = polyfit_R(tum[:, 3], tum[:, 1]); R_d = polyfit_R(Ia, Va)
R_e = (onc[:, 1].mean() - Va.mean()) / (Ia.mean() - onc[:, 3].mean()) if len(onc) else None
R_sec = R_a["R_paket_ohm"] if R_a else (R_b["R_paket_ohm"] if R_b else R_e)
ozet["pil"] = {
    "hucre_n": HUCRE_N, "V_ilk_log": r(V0, 2), "V_ilk_hucre": r(V0 / HUCRE_N, 3),
    "dolu_degil_notu": "ilk gerilim %.2f V = %.3f V/hucre; dolu LiPo 4,20 V/hucre (16,8 V) -> pil DOLU DEGILDI (yaklasik %.0f%% kalan, HESAP: 4,2-3,5 V araliginin dogrusal bolumu; olcum degil)" % (V0, V0 / HUCRE_N, 100 * (V0 / HUCRE_N - 3.5) / (4.2 - 3.5)),
    "V_arm_oncesi_5s_ort": r(onc[:, 1].mean(), 3), "I_arm_oncesi_5s_ort": r(onc[:, 3].mean(), 3), "arm_oncesi_referans": ONC_NOT, "arm_oncesi_t": [r(onc[0, 0], 2), r(onc[-1, 0], 2)],
    "V_bas_pencere": r(bw[0, 1], 3), "V_son_pencere": r(bw[-1, 1], 3),
    "V_min": r(bmot[imin, 1], 3), "V_min_hucre": r(bmot[imin, 1] / HUCRE_N, 3), "V_min_t": r(bmot[imin, 0], 2), "V_min_I": r(bmot[imin, 3], 1),
    "VoltR_min": r(bmot[:, 2].min(), 3), "VoltR_min_hucre": r(bmot[:, 2].min() / HUCRE_N, 3),
    "sarkma_V_ilk_askiya": r(V0 - Va.mean(), 3), "sarkma_V_ilk_min": r(V0 - bmot[imin, 1], 3), "sarkma_V_hucre_ilk_min": r((V0 - bmot[imin, 1]) / HUCRE_N, 3),
    "toparlanma_V_disarm_10s": r(b[(b[:, 0] >= T1) & (b[:, 0] <= T1 + 10)][-1, 1] - bmot[imin, 1], 3),
    "V_disarm_sonrasi_10s": r(b[(b[:, 0] >= T1) & (b[:, 0] <= T1 + 10)][-1, 1], 3),
    "I_motorlu": istat(bmot[:, 3]), "I_maks_t": r(bmot[int(np.argmax(bmot[:, 3])), 0], 2),
    "mAh_pencere": r(bw[-1, 4] - bw[0, 4], 1), "mAh_motorlu": r(bmot[-1, 4] - bmot[0, 4], 1), "Wh_pencere": r(bw[-1, 5] - bw[0, 5], 3),
    "mAh_log_toplam": r(b[-1, 4], 1), "RemPct_son_log_BATT_CAPACITY_8000": r(b[-1, 7], 0),
    "RemPct_13000_ile_HESAP": r(100 * (1 - b[-1, 4] / PIL_MAH_BEYAN), 1),
    "ic_direnc": {
        "yontem": "numpy.polyfit(I, V, 1) egimi = -R_paket; hucre = R_paket/4. (a) kalkis gecisi (arm-2 s -> ilk aski ornegi) ve (b) inis gecisi (EV17 -> disarm+3 s) SoC sabitken akim 0->37 A / 37->0 A tarar: TERCIH EDILEN. (c) tum pencere SoC kaymasiyla karisik. (d) yalniz aski: akim araligi dar. (e) D-yontemi: (V_arm_oncesi - V_aski)/(I_aski - I_arm_oncesi). (f) BAT.Res = FC'nin kendi tahmini (AP_BattMonitor)",
        "a_kalkis_gecisi": R_a, "b_inis_gecisi": R_b, "c_tum_pencere": R_c, "d_yalniz_aski": R_d,
        "e_arm_oncesi_vs_aski": {"R_paket_ohm": r(R_e, 4), "R_hucre_mohm": r(R_e * 1000 / HUCRE_N, 1)} if R_e else None,
        "f_BAT_Res_FC": {"aski_ort_ohm": r(Resa.mean(), 4), "aski_ort_mohm_hucre": r(Resa.mean() * 1000 / HUCRE_N, 1), "pencere_min_maks_ohm": [r(bw[:, 6].min(), 4), r(bw[:, 6].max(), 4)]},
        "secilen_R_paket_ohm": r(R_sec, 4), "secilen_kaynak": "a_kalkis_gecisi" if R_a else "b_inis_gecisi",
        "sarkma_HESAP_askida_V": r(R_sec * Ia.mean(), 3), "sarkma_olculen_ilk_askiya_V": r(V0 - Va.mean(), 3),
    },
    "BAT_Temp": "0 (sicaklik sensoru yok)",
}

# ---- ucus suresi tahmini
I_h = float(Ia.mean()); I_mot = float(bmot[:, 3].mean())
kul = PIL_MAH_BEYAN * KULLANILABILIR
# 3,5 V/hucre'ye kadar: askida V_yuklu vs CurrTot dogrusal uydurma -> 14,0 V'a ekstrapolasyon
mAh_a = yakin(ta, bb[:, 0], bb[:, 4])
V_low = V_HUCRE_LOW * HUCRE_N
sag = R_sec * I_h
# (i) tum aski uydurmasi - kalkis polarizasyon gecisini (ilk ~20 s'de 14,4 -> 14,0 V) icerir, SoC egimi DEGIL; yalniz kiyas icin
pf, pf_cov = np.polyfit(mAh_a, Va, 1, cov=True)          # V = pf[1] + pf[0]*mAh
egim_V_per_Ah = pf[0] * 1000.0; egim_se_V_per_Ah = math.sqrt(pf_cov[0, 0]) * 1000.0
# (ii) PLATO uydurmasi - askinin son 30 s'i (gecis bitmis, yuk sabit): SoC egimine en yakin, TERCIH EDILEN
PLATO_S = 30.0
plm = ta >= ta[-1] - PLATO_S
pfp, pfp_cov = np.polyfit(mAh_a[plm], Va[plm], 1, cov=True)
egim_plato_V_per_Ah = pfp[0] * 1000.0; egim_plato_se_V_per_Ah = math.sqrt(pfp_cov[0, 0]) * 1000.0


def ekstra(p, V_hedef):
    return (V_hedef - p[1]) / p[0] if p[0] < 0 else None


mAh_low_yuklu = ekstra(pf, V_low); mAh_low_dinlenme = ekstra(pf, V_low - sag)
mAh_low_yuklu_p = ekstra(pfp, V_low); mAh_low_dinlenme_p = ekstra(pfp, V_low - sag)
kal_yuklu = (mAh_low_yuklu - mAh_a[0]) if mAh_low_yuklu else None
kal_dinl = (mAh_low_dinlenme - mAh_a[0]) if mAh_low_dinlenme else None
kal_yuklu_p = (mAh_low_yuklu_p - mAh_a[-1]) if mAh_low_yuklu_p else None      # plato: aski SONUNDAN itibaren kalan
kal_dinl_p = (mAh_low_dinlenme_p - mAh_a[-1]) if mAh_low_dinlenme_p else None
# olculen: yuklu gerilim 14,0 V'in altina ILK inis
ilk_alt = bw[bw[:, 1] < V_low]
ilk_alt_t = float(ilk_alt[0, 0]) if len(ilk_alt) else None
ilk_alt_mAh = float(ilk_alt[0, 4] - mAh_a[0]) if len(ilk_alt) else None
# dinlenme gerilimi toparlanmasi (disarm sonrasi; polarizasyon dakikalarca surer -> alt sinir)
b_son = b[b[:, 0] >= T1]
V_dinl_son = float(b_son[-1, 1]); t_dinl_son = float(b_son[-1, 0] - T1)
egim_dinlenme_V_per_Ah = (V_dinl_son - V0) / ((b_son[-1, 4] - b[0, 4]) / 1000.0)   # log basi (yuksuz) -> log sonu (yuksuz, kismi toparlanma)
kal_dinl_ocv = (V_low - V_dinl_son) / egim_dinlenme_V_per_Ah * 1000.0 if egim_dinlenme_V_per_Ah < 0 else None
ozet["ucus_suresi"] = {
    "I_aski_A": r(I_h, 2), "I_motorlu_A": r(I_mot, 2), "P_aski_W": r(Pa.mean(), 1),
    "yontem_1": "t_dk = %.0f%% x %d mAh / (I_aski A x 1000/60)  [kullanici beyani kapasite; dolu pil varsayimi]" % (KULLANILABILIR * 100, PIL_MAH_BEYAN),
    "kullanilabilir_mAh": r(kul, 0), "tahmin_dk_aski_akimi": r(kul / (I_h * 1000 / 60), 1), "tahmin_dk_motorlu_ort_akim": r(kul / (I_mot * 1000 / 60), 1),
    "tahmin_dk_aski_p95_akim": r(kul / (np.percentile(Ia, 95) * 1000 / 60), 1),
    "tahmin_dk_%100_kapasite": r(PIL_MAH_BEYAN / (I_h * 1000 / 60), 1),
    "yontem_2_3.5V_hucre": {
        "aciklama": "askida yuklu gerilim V(CurrTot) dogrusal uydurma (numpy.polyfit), 14,0 V'a (3,5 V/hucre yuklu; LOW esigi ham gerilime bakar, BATT_FS_VOLTSRC=0) ve 14,0 - I_aski*R_paket'e (sarkma cikarilmis = dinlenme 3,5 V/hucre) ekstrapolasyon. Iki uydurma: (i) TUM aski - kalkis polarizasyon gecisini icerir (ilk ~20 s'de 14,4 -> 14,0 V), SoC egimi DEGIL, yalniz kiyas; (ii) PLATO - askinin son %.0f s'i (gecis bitmis, yuk sabit) = TERCIH. Ek: (iii) dinlenme gerilimi egimi = (V_log_sonu_yuksuz - V_log_basi_yuksuz)/mAh; disarm+%.0f s toparlanma tamamlanmamis -> pesimist ALT SINIR. Hepsi logdaki %.0f mAh (beyan kapasitenin %%%.1f'i) uzerinden EKSTRAPOLASYON = HESAP; LiPo egrisi dogrusal degildir (3,85-3,65 plato yavas, <3,6 diz hizli) -> gercek deger tam bosaltma testiyle olculmeli" % (PLATO_S, t_dinl_son, mAh_a[-1] - mAh_a[0], 100 * (mAh_a[-1] - mAh_a[0]) / PIL_MAH_BEYAN),
        "sarkma_I_R_V": r(sag, 3), "R_paket_ohm": r(R_sec, 4), "V_hedef_yuklu": V_low, "V_hedef_dinlenme_esdeger_yuklu": r(V_low - sag, 3),
        "olculen_yuklu_14.0V_ilk_inis": {"t": r(ilk_alt_t, 1), "aski_basindan_s": r(ilk_alt_t - ta[0], 1) if ilk_alt_t else None, "aski_basindan_mAh": r(ilk_alt_mAh, 0), "not": "OLCUM: bu ucusta yuklu gerilim 14,0 V'in altina indi"},
        "i_tum_aski_uydurma": {"n": int(len(mAh_a)), "mAh_aralik": [r(mAh_a[0], 0), r(mAh_a[-1], 0)], "V_aralik": [r(Va[0], 3), r(Va[-1], 3)], "egim_V_per_Ah": r(egim_V_per_Ah, 3), "egim_std_hata_V_per_Ah": r(egim_se_V_per_Ah, 3), "egim_mV_per_100mAh": r(egim_V_per_Ah / 10 * 1000, 1), "kesim_V": r(pf[1], 3), "r2": r(np.corrcoef(mAh_a, Va)[0, 1] ** 2, 3),
                               "yuklu_14.0V_kalan_mAh_aski_basindan": r(kal_yuklu, 0), "dinlenme_3.5V_kalan_mAh_aski_basindan": r(kal_dinl, 0), "dinlenme_3.5V_kalan_dk": r(kal_dinl / (I_h * 1000 / 60), 1) if kal_dinl else None,
                               "gecerlilik": "GECERSIZ/asiri pesimist: egim gecis kaynakli (bkz. plato)"},
        "ii_plato_uydurma_TERCIH": {"n": int(plm.sum()), "t_aralik": [r(ta[plm][0], 1), r(ta[plm][-1], 1)], "mAh_aralik": [r(mAh_a[plm][0], 0), r(mAh_a[plm][-1], 0)], "V_aralik_ort": r(Va[plm].mean(), 3), "egim_V_per_Ah": r(egim_plato_V_per_Ah, 3), "egim_std_hata_V_per_Ah": r(egim_plato_se_V_per_Ah, 3), "egim_mV_per_100mAh": r(egim_plato_V_per_Ah / 10 * 1000, 1), "kesim_V": r(pfp[1], 3), "r2": r(np.corrcoef(mAh_a[plm], Va[plm])[0, 1] ** 2, 3),
                                    "gecerlilik": "KOTU KOSULLU: r2 %.2f, egim %.1f +/- %.1f mV/100 mAh (std hata) -> egim sifirdan %s; ekstrapolasyon OLCUM DEGIL, yalniz buyukluk sirasi" % (np.corrcoef(mAh_a[plm], Va[plm])[0, 1] ** 2, egim_plato_V_per_Ah / 10 * 1000, egim_plato_se_V_per_Ah / 10 * 1000, "ayirt edilemiyor" if egim_plato_se_V_per_Ah >= abs(egim_plato_V_per_Ah) else "ayirt ediliyor"),
                                    "yuklu_14.0V": "aski sonunda zaten altinda (V_son %.3f V)" % Va[-1] if Va[-1] < V_low else r(kal_yuklu_p, 0),
                                    "dinlenme_3.5V_kalan_mAh_aski_sonundan": r(kal_dinl_p, 0), "dinlenme_3.5V_kalan_dk_aski_akimi": r(kal_dinl_p / (I_h * 1000 / 60), 1) if kal_dinl_p else None,
                                    "dinlenme_3.5V_toplam_mAh_log_basindan": r(mAh_low_dinlenme_p, 0), "toplam_dk_log_basindan_HESAP": r(mAh_low_dinlenme_p / (I_h * 1000 / 60), 1) if mAh_low_dinlenme_p else None},
        "iii_dinlenme_gerilimi_egimi": {"V_log_basi_yuksuz": r(V0, 3), "V_log_sonu_yuksuz": r(V_dinl_son, 3), "disarm_sonrasi_s": r(t_dinl_son, 1), "mAh": r(b_son[-1, 4] - b[0, 4], 0), "egim_V_per_Ah": r(egim_dinlenme_V_per_Ah, 3),
                                        "dinlenme_3.5V_kalan_mAh_log_sonundan_ALT_SINIR": r(kal_dinl_ocv, 0), "not": "toparlanma tamamlanmamis (VoltR ve Volt hala yukseliyor) -> egim abartili, kalan mAh ALT SINIR"},
        "not": "pil bu ucusa 3,89 V/hucre ile basladi (dolu degil); 'kalan' degerler BU pil durumundan itibarendir, dolu pilden degil. Uc yontem 13 000 mAh beyaniyla dogrudan karsilastirilamaz (beyan dolu pil icindir); beyan yalniz tam bosaltma testiyle dogrulanir",
    },
}

# ---- VIBE
v = A["VIBE"]; vw = v[(v[:, 0] >= T0) & (v[:, 0] <= T1)]
vibe = {"kapsam_pencere": {}, "kapsam_motorlu": {}, "kapsam_aski": {}, "clip": {}}
for inst in (0, 1):
    x = vw[vw[:, 1] == inst]
    vibe["kapsam_pencere"]["IMU%d" % inst] = {ax: istat(x[:, 2 + i]) for i, ax in enumerate("XYZ")}
    xm = x[(x[:, 0] >= tm0) & (x[:, 0] <= tm1)]
    vibe["kapsam_motorlu"]["IMU%d" % inst] = {ax: istat(xm[:, 2 + i]) for i, ax in enumerate("XYZ")}
    xs = x[np.clip(np.searchsorted(x[:, 0], ta), 0, len(x) - 1)]
    vibe["kapsam_aski"]["IMU%d" % inst] = {ax: istat(xs[:, 2 + i]) for i, ax in enumerate("XYZ")}
    cl = x[:, 5]; vibe["clip"]["IMU%d" % inst] = {"bas": int(cl[0]), "son": int(cl[-1]), "artis": int(cl[-1] - cl[0])}
xs_b = np.vstack([vw[vw[:, 1] == inst][np.clip(np.searchsorted(vw[vw[:, 1] == inst][:, 0], ta), 0, (vw[:, 1] == inst).sum() - 1)] for inst in (0, 1)])
vibe["kapsam_aski"]["IMU_birlesik"] = {ax: istat(xs_b[:, 2 + i]) for i, ax in enumerate("XYZ")}
xm_b = vw[(vw[:, 0] >= tm0) & (vw[:, 0] <= tm1)]
vibe["kapsam_motorlu"]["IMU_birlesik"] = {ax: istat(xm_b[:, 2 + i]) for i, ax in enumerate("XYZ")}
# kalkis / inis tepe
kalk = vw[(vw[:, 0] >= tm0) & (vw[:, 0] < ta[0])]; inis = vw[(vw[:, 0] > ta[-1]) & (vw[:, 0] <= T1)]
vibe["kalkis_dilimi_maks_XYZ"] = [r(kalk[:, 2 + i].max(), 1) for i in range(3)] if len(kalk) else None
vibe["inis_dilimi_maks_XYZ"] = [r(inis[:, 2 + i].max(), 1) for i in range(3)] if len(inis) else None
vibe["clip_toplam"] = sum(d["artis"] for d in vibe["clip"].values())
vibe["log_tamami_clip_son"] = [int(v[v[:, 1] == k][-1, 5]) for k in (0, 1)]
zb = vibe["kapsam_aski"]["IMU_birlesik"]
vibe["esik_kiyasi"] = {"esik_iyi_ms2": VIBE_ESIK_IYI, "esik_kotu_ms2": VIBE_ESIK_KOTU,
                       "aski_p95_XYZ": [zb["X"]["p95"], zb["Y"]["p95"], zb["Z"]["p95"]], "aski_maks_XYZ": [zb["X"]["maks"], zb["Y"]["maks"], zb["Z"]["maks"]],
                       "aski_p95_30_orani_Z": r(zb["Z"]["p95"] / VIBE_ESIK_IYI, 2), "motorlu_maks_Z": vibe["kapsam_motorlu"]["IMU_birlesik"]["Z"]["maks"],
                       "ornek_ustu_30_orani_aski": r(float(np.mean(xs_b[:, 2:5].max(axis=1) > VIBE_ESIK_IYI)), 4),
                       "ornek_ustu_30_orani_motorlu": r(float(np.mean(xm_b[:, 2:5].max(axis=1) > VIBE_ESIK_IYI)), 4),
                       "hukum": ("askida p95 ve maks 30 m/s2 esiginin ALTINDA" if zb["Z"]["maks"] < VIBE_ESIK_IYI else "askida maks 30 m/s2 esigini ASIYOR")}
ozet["vibe"] = vibe

# ---- FFT (IMU 25 Hz; en uzun aski dilimi + tabanlar)
im = A["IMU"]
fft = {"dilim_aski_t": [r(en[0], 2), r(en[1], 2)], "IMU_hz": ozet["meta"]["imu_hz"], "nyquist_hz": r(ozet["meta"]["imu_hz"] / 2, 2), "aski": {}, "taban_motor_kapali": {}, "taban_armli_rolanti": {}}
kanallar = (("AccZ", 7), ("AccX", 5), ("AccY", 6), ("GyrX", 2), ("GyrY", 3), ("GyrZ", 4))
fft_egriler = {}
for inst in (0, 1):
    x = im[(im[:, 1] == inst) & (im[:, 0] >= en[0]) & (im[:, 0] <= en[1])]
    fft["aski"]["IMU%d" % inst] = {}
    for ad, col in kanallar:
        f = fft_tepeler(x[:, 0], x[:, col])
        if f:
            fft["aski"]["IMU%d" % inst][ad] = {k: vv for k, vv in f.items() if not k.startswith("_")}
            fft_egriler[("aski", inst, ad)] = (f["_f"], f["_amp"])
    # taban 1: motor kapali, disarm, yerde (log basi 202-217 s: hareketsiz)
    xb = im[(im[:, 1] == inst) & (im[:, 0] >= 203.0) & (im[:, 0] <= 217.0)]
    fft["taban_motor_kapali"]["IMU%d" % inst] = {}
    for ad, col in (("AccZ", 7), ("GyrX", 2), ("GyrY", 3)):
        f = fft_tepeler(xb[:, 0], xb[:, col])
        if f:
            fft["taban_motor_kapali"]["IMU%d" % inst][ad] = {k: vv for k, vv in f.items() if not k.startswith("_")}
            fft_egriler[("kapali", inst, ad)] = (f["_f"], f["_amp"])
    # taban 2: armli rolanti (arm -> ilk motorlu ornek; motorlar spin_arm'da, yerde)
    xr = im[(im[:, 1] == inst) & (im[:, 0] >= T0) & (im[:, 0] < tm0)]
    fft["taban_armli_rolanti"]["IMU%d" % inst] = {"sure_s": r(tm0 - T0, 2)}
    if len(xr) >= 32:
        for ad, col in (("AccZ", 7), ("GyrX", 2), ("GyrY", 3)):
            f = fft_tepeler(xr[:, 0], xr[:, col])
            if f:
                fft["taban_armli_rolanti"]["IMU%d" % inst][ad] = {k: vv for k, vv in f.items() if not k.startswith("_")}
                fft_egriler[("rolanti", inst, ad)] = (f["_f"], f["_amp"])
    else:
        fft["taban_armli_rolanti"]["IMU%d" % inst]["not"] = "rolanti dilimi < 32 ornek, FFT yok"
# pervane temel frekansi (HESAP)
rc = A["RCOU"]; rw = rc[(rc[:, 0] >= T0) & (rc[:, 0] <= T1)]
mot_kanal = {MOTOR_FN[P.get("SERVO%d_FUNCTION" % ch)]: ch for ch in range(9, 13) if P.get("SERVO%d_FUNCTION" % ch) in MOTOR_FN}
rs = rw[np.clip(np.searchsorted(rw[:, 0], ta), 0, len(rw) - 1)]
pwm_ort = float(np.mean([rs[:, ch].mean() for ch in mot_kanal.values()]))
pwm_orani = (pwm_ort - P.get("MOT_PWM_MIN", 1000)) / (P.get("MOT_PWM_MAX", 2000) - P.get("MOT_PWM_MIN", 1000))
rpm_bos = MOTOR_KV * Va.mean() * pwm_orani
fft["pervane_temel_frekansi_HESAP"] = {
    "yontem": "RPM ~= KV x V_aski x PWM_orani (yuksuz motor ust siniri; yuklu pervane %10-20 dusuk doner). f_temel = RPM/60; pal gecis = 3 x f_temel (3 pal). KV kullanici beyani, ESC/RPM telemetrisi LOGDA YOK -> bu bir HESAP, olcum DEGIL",
    "KV_beyan": MOTOR_KV, "V_aski": r(Va.mean(), 2), "pwm_ort_M1_M4_us": r(pwm_ort, 0), "pwm_orani": r(pwm_orani, 3),
    "rpm_ust_sinir": r(rpm_bos, 0), "f_temel_hz_ust_sinir": r(rpm_bos / 60, 1), "f_temel_hz_%85": r(0.85 * rpm_bos / 60, 1),
    "f_pal_gecis_hz_ust_sinir": r(PAL_N * rpm_bos / 60, 1),
    "alias_25Hz_HESAP_hz": {"f_temel_ust": r(abs(rpm_bos / 60 - round(rpm_bos / 60 / 25) * 25), 1), "f_temel_%85": r(abs(0.85 * rpm_bos / 60 - round(0.85 * rpm_bos / 60 / 25) * 25), 1)},
    "alias_notu": "IMU 25 Hz ile kaydedildigi icin ~100-130 Hz pervane bileseni 0-12,5 Hz bandina KATLANIR (alias). INS_ACCEL/GYRO_FILTER=20 Hz 2 kutuplu LPF 120 Hz'i ~%3'e (~-31 dB) indirir ama sifirlamaz -> 2-12,5 Hz'de gorulen kucuk bir tepe kol esnekligi de, katlanmis pervane bileseni de olabilir; AYIRT EDILEMEZ. Kesin olcum icin INS_LOG_BAT_MASK=1 (hizli IMU, ISBH/ISBD) gerekir",
}
# 2-15 Hz band ozet: aski tepe vs tabanlar (IMU0 AccZ ve GyrX/Y)
bandoz = {}
for inst in (0, 1):
    for ad in ("AccZ", "GyrX", "GyrY"):
        a_ = fft["aski"]["IMU%d" % inst].get(ad); k_ = fft["taban_motor_kapali"]["IMU%d" % inst].get(ad); rl = fft["taban_armli_rolanti"]["IMU%d" % inst].get(ad)
        bandoz["IMU%d_%s" % (inst, ad)] = {"aski_2_15Hz_tepe": (a_["band_2_15Hz_tepeler"][:2] if a_ else None), "aski_2_15Hz_rms": a_["band_2_15Hz_rms"] if a_ else None,
                                           "kapali_2_15Hz_rms": k_["band_2_15Hz_rms"] if k_ else None, "rolanti_2_15Hz_rms": rl["band_2_15Hz_rms"] if rl else None,
                                           "aski_tum_rms": a_["rms"] if a_ else None, "kapali_tum_rms": k_["rms"] if k_ else None}
fft["band_2_15Hz_ozet"] = bandoz
ozet["fft"] = fft

# ---- RCOU
rcou = {"motor_kanallari_AUX": {m: "C%d" % ch for m, ch in sorted(mot_kanal.items())},
        "SERVO1_4_FUNCTION": [P.get("SERVO%d_FUNCTION" % i) for i in range(1, 5)],
        "not": "ESC'ler AUX1-4 = SERVO9-12 (36,34,33,35 -> C9=M4, C10=M2, C11=M1, C12=M3). C1..C4 (MAIN) fonksiyonlari 34,34,33,34 = M2,M2,M1,M2 (ayni motorun kopyalari; IOMCU cikisi, AUX ile ayni anda ort. 4 us farkli). Gorev C1-C4 istedi: ikisi de verildi; MOTOR DENGESI icin C9-C12 gecerlidir"}
kap = "aski"
ort9 = {m: float(rs[:, ch].mean()) for m, ch in mot_kanal.items()}; std9 = {m: float(rs[:, ch].std()) for m, ch in mot_kanal.items()}
rcou["C1_C4_aski"] = {"ort_us": [r(rs[:, ch].mean(), 0) for ch in range(1, 5)], "std_us": [r(rs[:, ch].std(), 1) for ch in range(1, 5)],
                      "yayilim_ort_us": r(max(rs[:, ch].mean() for ch in range(1, 5)) - min(rs[:, ch].mean() for ch in range(1, 5)), 0),
                      "min_us": [r(rs[:, ch].min(), 0) for ch in range(1, 5)], "maks_us": [r(rs[:, ch].max(), 0) for ch in range(1, 5)]}
rcou["C9_C12_motorlar_aski"] = {"n": int(len(rs)), "M_ort_us": {m: r(x, 0) for m, x in sorted(ort9.items())}, "M_std_us": {m: r(x, 1) for m, x in sorted(std9.items())},
                                "M_p05_p95_us": {m: [r(np.percentile(rs[:, ch], 5), 0), r(np.percentile(rs[:, ch], 95), 0)] for m, ch in sorted(mot_kanal.items())},
                                "yayilim_ort_us": r(max(ort9.values()) - min(ort9.values()), 0), "yayilim_pct_aralik": r((max(ort9.values()) - min(ort9.values())) / 10.0, 1),
                                "en_yuksek": max(ort9, key=ort9.get), "en_dusuk": min(ort9, key=ort9.get), "ort_pwm_orani": r(pwm_orani, 3),
                                "cift_farklari_us": {"CCW(M1+M2)-CW(M3+M4)_yaw": r(ort9["M1"] + ort9["M2"] - ort9["M3"] - ort9["M4"], 0),
                                                     "on(M1+M3)-arka(M2+M4)_pitch": r(ort9["M1"] + ort9["M3"] - ort9["M2"] - ort9["M4"], 0),
                                                     "sag(M1+M4)-sol(M2+M3)_roll": r(ort9["M1"] + ort9["M4"] - ort9["M2"] - ort9["M3"], 0)}}
th = float(ThO[aski].mean()); e_ = P.get("MOT_THST_EXPO", 0.65); smin = P.get("MOT_SPIN_MIN", 0.15); smax = P.get("MOT_SPIN_MAX", 0.95)
ratio = ((e_ - 1) + math.sqrt((1 - e_) ** 2 + 4 * e_ * th)) / (2 * e_)
rcou["ThO_aski_beklenen_pwm_HESAP"] = r(1000 + 1000 * (smin + (smax - smin) * ratio), 0)
rcou["motorlu_maks_us"] = {m: r(rw[(rw[:, 0] >= tm0) & (rw[:, 0] <= tm1), ch].max(), 0) for m, ch in sorted(mot_kanal.items())}
ozet["rcou"] = rcou

# ---- tutum
def att_stat(x):
    er = x[:, 2] - x[:, 1]; ep = x[:, 4] - x[:, 3]; ey = wrap(x[:, 6] - x[:, 5])
    return {"n": int(len(x)), "roll_rms_hata_deg": r(np.sqrt(np.mean(er ** 2)), 3), "pitch_rms_hata_deg": r(np.sqrt(np.mean(ep ** 2)), 3), "yaw_rms_hata_deg": r(np.sqrt(np.mean(ey ** 2)), 3),
            "roll_hata_maks_abs_deg": r(np.abs(er).max(), 2), "pitch_hata_maks_abs_deg": r(np.abs(ep).max(), 2),
            "roll_maks_abs_deg": r(np.abs(x[:, 2]).max(), 2), "pitch_maks_abs_deg": r(np.abs(x[:, 4]).max(), 2),
            "roll_ort_deg": r(x[:, 2].mean(), 3), "pitch_ort_deg": r(x[:, 4].mean(), 3), "DesRoll_ort_deg": r(x[:, 1].mean(), 3), "DesPitch_ort_deg": r(x[:, 3].mean(), 3),
            "ErrRP_ort": r(x[:, 7].mean(), 4), "ErrRP_maks": r(x[:, 7].max(), 4), "ErrYaw_maks": r(x[:, 8].max(), 4)}
am = aa[(aa[:, 0] >= tm0) & (aa[:, 0] <= tm1)]
tutum = {"motorlu": att_stat(am), "aski": att_stat(yakin(ta, aa[:, 0], aa))}
rt = A["RATE"]; rrt = rt[(rt[:, 0] >= T0) & (rt[:, 0] <= T1)]; rsr = yakin(ta, rrt[:, 0], rrt)
tutum["aski_hiz"] = {"roll_rate_rms_hata_dps": r(np.sqrt(np.mean((rsr[:, 2] - rsr[:, 1]) ** 2)), 2), "pitch_rate_rms_hata_dps": r(np.sqrt(np.mean((rsr[:, 4] - rsr[:, 3]) ** 2)), 2),
                     "yaw_rate_rms_hata_dps": r(np.sqrt(np.mean((rsr[:, 6] - rsr[:, 5]) ** 2)), 2),
                     "ROut_ort": r(rsr[:, 10].mean(), 4), "POut_ort": r(rsr[:, 11].mean(), 4), "YOut_ort": r(rsr[:, 12].mean(), 4), "YOut_maks_abs": r(np.abs(rsr[:, 12]).max(), 3),
                     "not": "ROut/POut/YOut -1..1 karistirici cikisi; ort != 0 -> surekli tork dengesizligi"}
# yaw salinimi: dilim bazinda hata + GyrZ baskin frekansi
aa_a = yakin(ta, aa[:, 0], aa); ey_a = wrap(aa_a[:, 6] - aa_a[:, 5])
yaw_dilim = []
for q0 in np.arange(math.floor(ta[0] / 10) * 10, ta[-1], 10.0):
    mq = (ta >= q0) & (ta < q0 + 10)
    if mq.sum() >= 20: yaw_dilim.append({"t": [r(q0, 0), r(q0 + 10, 0)], "rms_deg": r(np.sqrt(np.mean(ey_a[mq] ** 2)), 2), "maks_abs_deg": r(np.abs(ey_a[mq]).max(), 2)})
imz = im[(im[:, 1] == 0) & (im[:, 0] >= en[0]) & (im[:, 0] <= en[1])]
fz = fft_tepeler(imz[:, 0], imz[:, 4])
tutum["yaw"] = {"parm": {k: P.get(k) for k in ("ATC_ANG_YAW_P", "ATC_RAT_YAW_P", "ATC_RAT_YAW_I", "ATC_RAT_YAW_D", "ATC_RAT_YAW_IMAX", "ATC_RAT_YAW_FLTE", "ATC_RAT_YAW_FLTT", "ATC_ACCEL_Y_MAX", "ATC_SLEW_YAW", "MOT_YAW_HEADROOM", "ATC_RATE_Y_MAX")},
                "aski_hata_rms_deg": r(np.sqrt(np.mean(ey_a ** 2)), 2), "aski_hata_maks_abs_deg": r(np.abs(ey_a).max(), 2), "aski_hata_p95_abs_deg": r(np.percentile(np.abs(ey_a), 95), 2),
                "DesYaw_aski_ort_deg": r(aa_a[:, 5].mean(), 1), "DesYaw_aski_std_deg": r(aa_a[:, 5].std(), 2), "Yaw_aski_std_deg": r(aa_a[:, 6].std(), 2),
                "dilimler_10s": yaw_dilim,
                "GyrZ_FFT_IMU0_baskin": fz["tepeler"][:3] if fz else None, "GyrZ_rms_rad_s": fz["rms"] if fz else None,
                "YOut_ort": tutum["aski_hiz"]["YOut_ort"], "YOut_maks_abs": tutum["aski_hiz"]["YOut_maks_abs"], "YOut_p95_abs": r(np.percentile(np.abs(rsr[:, 12]), 95), 3),
                "yaw_rate_Y_p05_p95_dps": [r(np.percentile(rsr[:, 6], 5), 1), r(np.percentile(rsr[:, 6], 95), 1)],
                "EKF_yaw_reset_t": next((t for t, i in A["EV"] if i == 62), None),
                "not": "DesYaw ~sabit (GUIDED, yaw hedefi sabit); Yaw hedef etrafinda salinir -> kapali cevrim yaw salinimi. Kaynak (ayar mi, 3 pal pervanenin dusuk yaw otoritesi mi, ruzgar mi) bu logdan AYRISTIRILAMAZ; EKF yaw reset (in-flight alignment) yalniz baslangicta"}
ozet["tutum"] = tutum

# ---- EKF / ERR / MSG
xk = A["XKF4"]; xw = xk[(xk[:, 0] >= T0) & (xk[:, 0] <= T1)]
ekf = {"cekirdek": {}, "innov_esik": 1.0}
for core in (0, 1):
    x = xw[xw[:, 1] == core]
    if not len(x): continue
    ekf["cekirdek"][str(core)] = {"n": int(len(x)), "SV_maks": r(x[:, 2].max(), 3), "SP_maks": r(x[:, 3].max(), 3), "SH_maks": r(x[:, 4].max(), 3), "SM_maks": r(x[:, 5].max(), 3),
                                  "SVT_maks": r(x[:, 6].max(), 3), "errRP_maks": r(x[:, 7].max(), 4), "innov_>1_n": int(((x[:, 2] > 1) | (x[:, 3] > 1) | (x[:, 4] > 1) | (x[:, 5] > 1)).sum()),
                                  "PI_uniq": [int(z) for z in np.unique(x[:, 11])]}
ekf["lane_switch_n"] = int((np.diff(xw[xw[:, 1] == 0][:, 11]) != 0).sum()) if len(xw) else 0
gps = A["GPS"]; gw = gps[(gps[:, 0] >= T0) & (gps[:, 0] <= T1)]
ekf["gps"] = {"Status_uniq": [int(z) for z in np.unique(gw[:, 1])], "NSats_min_maks": [int(gw[:, 2].min()), int(gw[:, 2].max())], "HDop_min_maks": [r(gw[:, 3].min(), 2), r(gw[:, 3].max(), 2)]}
pm = A["PM"]; ekf["PM"] = {"NLon_toplam": int(pm[:, 1].sum()), "MaxT_us_maks": int(pm[:, 2].max()), "Load_binde_maks": int(pm[:, 3].max())}
ekf["ERR_tumu"] = [{"t": r(t, 2), "subsys": ERR_SUB.get(s, str(s)), "ecode": e, "ucus_icinde": bool(T0 <= t <= T1)} for t, s, e in A["ERR"]]
ekf["ERR_ucus_icinde_n"] = sum(1 for t, s, e in A["ERR"] if T0 <= t <= T1)
ekf["MSG_tumu"] = [{"t": r(t, 2), "mesaj": s} for t, s in A["MSG"]]
ekf["EV_ucus"] = [{"t": r(t, 2), "olay": ad} for t, ad in ev_list if T0 - 1 <= t <= T1 + 1]
ekf["MODE_ucus"] = ozet["ucus"]["kip_gecisleri"]
ekf["yorum"] = "ucus icinde ERR/failsafe YOK; GCS failsafe (ERR 8) arm ONCESI 210,1-233,7 s ve disarm SONRASI 315,1 s; radyo failsafe (ERR 5) disarm sonrasi 318,6 s (kumanda kapatildi). EKF innovasyon oranlari <<1, lane switch yok, GPS 3D fix"
ozet["ekf_olaylar"] = ekf

# ---- FAILSAFE UYUMU
fs_p = {k: P.get(k) for k in ("BATT_MONITOR", "BATT_CAPACITY", "BATT_LOW_VOLT", "BATT_CRT_VOLT", "BATT_ARM_VOLT", "BATT_ARM_MAH", "BATT_LOW_MAH", "BATT_CRT_MAH",
                              "BATT_FS_LOW_ACT", "BATT_FS_CRT_ACT", "BATT_LOW_TIMER", "BATT_FS_VOLTSRC", "BATT_VOLT_MULT", "BATT_AMP_PERVLT", "FS_OPTIONS")}
V_crt = V_HUCRE_CRT * HUCRE_N; V_arm_oneri = V_HUCRE_ARM_ONERI * HUCRE_N
Vw = bw[:, 1]; VRw = bw[:, 2]; tw = bw[:, 0]; dtb = float(np.median(np.diff(tw)))
alt_low = Vw < V_low; alt_low_R = VRw < V_low; alt_crt = Vw < V_crt
ozet["failsafe"] = {
    "logdaki_parametreler": fs_p,
    "hucre_basina_mevcut": {"LOW": r(fs_p["BATT_LOW_VOLT"] / HUCRE_N, 3), "CRT": r(fs_p["BATT_CRT_VOLT"] / HUCRE_N, 3), "ARM": r(fs_p["BATT_ARM_VOLT"] / HUCRE_N, 3)},
    "hukum": "UYGUN DEGIL: 10,0/9,0 V esikleri 4S'te 2,50/2,25 V/hucre demektir; LiPo 3,0 V/hucre altinda kalici hasar gorur -> failsafe HICBIR ZAMAN tetiklenmez, pil once biter. BATT_CAPACITY 8000 = 3S pilin degeri (13 000 beyan) -> RemPct ve mAh-tabanli esikler yanlis. BATT_ARM_VOLT 9,0 V = 2,25 V/hucre -> bos pille kalkisi engellemez",
    "oneri": {"BATT_LOW_VOLT": V_low, "BATT_CRT_VOLT": V_crt, "BATT_CAPACITY": PIL_MAH_BEYAN, "BATT_ARM_VOLT": V_arm_oneri,
              "BATT_ARM_VOLT_not": "oneri %.1f V (%.1f V/hucre): LOW'un ustunde olmali ki yarim pille kalkilmasin; 14,8 V (3,7 V/hucre) daha tutucu" % (V_arm_oneri, V_HUCRE_ARM_ONERI),
              "BATT_LOW_MAH_oneri_HESAP": r(PIL_MAH_BEYAN * 0.25, 0), "BATT_CRT_MAH_oneri_HESAP": r(PIL_MAH_BEYAN * 0.15, 0),
              "BATT_FS_LOW_ACT_mevcut": fs_p["BATT_FS_LOW_ACT"], "BATT_FS_CRT_ACT_mevcut": fs_p["BATT_FS_CRT_ACT"], "act_not": "1=Land (mevcut) 3 m aski icin uygun; RTL(2) gerekmez",
              "BATT_FS_VOLTSRC_not": "0=ham gerilim (mevcut). 1=sarkma-telafili (BAT.VoltR, R tahmini ile) yuk altinda yanlis tetiklemeyi azaltir; bu logda VoltR min %.2f V vs ham %.2f V" % (bmot[:, 2].min(), bmot[imin, 1])},
    "bu_logda_gerilim_vs_onerilen_esikler": {
        "V_min_ham": r(bmot[imin, 1], 3), "V_min_ham_hucre": r(bmot[imin, 1] / HUCRE_N, 3), "V_min_t": r(bmot[imin, 0], 2), "V_min_I_A": r(bmot[imin, 3], 1),
        "LOW_14.0V_marj_V": r(bmot[imin, 1] - V_low, 3), "CRT_13.2V_marj_V": r(bmot[imin, 1] - V_crt, 3),
        "ham_V_LOW_altinda_toplam_s": r(alt_low.sum() * dtb, 1), "ham_V_LOW_altinda_en_uzun_kosu_s": r(en_uzun_kosu(alt_low) * dtb, 1), "ham_V_LOW_altinda_ornek_orani_motorlu": r(float((bmot[:, 1] < V_low).mean()), 3),
        "ham_V_CRT_altinda_toplam_s": r(alt_crt.sum() * dtb, 1),
        "VoltR_LOW_altinda_toplam_s": r(alt_low_R.sum() * dtb, 1), "VoltR_min": r(bmot[:, 2].min(), 3),
        "BATT_LOW_TIMER_s": fs_p["BATT_LOW_TIMER"],
        "LOW_tetiklenir_miydi_ham": bool(en_uzun_kosu(alt_low) * dtb >= (fs_p["BATT_LOW_TIMER"] or 10)),
        "LOW_tetiklenir_miydi_VoltR": bool(en_uzun_kosu(alt_low_R) * dtb >= (fs_p["BATT_LOW_TIMER"] or 10)),
        "ARM_14.4V_ile_kalkis": "ilk gerilim %.2f V >= %.1f V -> arm IZIN verilirdi" % (V0, V_arm_oneri) if V0 >= V_arm_oneri else "ilk gerilim %.2f V < %.1f V -> arm REDDEDILIRDI" % (V0, V_arm_oneri),
        "mevcut_10V_esigine_marj_V": r(bmot[imin, 1] - fs_p["BATT_LOW_VOLT"], 2),
    },
}

# ---- KIYAS C / D
Cj = json.load(open(C_OZET, encoding="utf-8")); Dj = json.load(open(D_OZET, encoding="utf-8"))
kc = Cj["konfig_C"]; kd = Dj["havuz_D"]
vC = kc["vibe_aski_birlesik"]; vD = kd["vibe_aski"]["birlesik"]
d_kisa = next((u for L in Dj["loglar"] for u in L["ucuslar"] if u["tur"] == "kisa_sicrama"), None)
d_kisa_vibeZ_maks = max(v_["Z"]["maks"] for v_ in d_kisa["vibe"]["kapsam_pencere"].values()) if d_kisa else None
d_ucus_vibeZ = [(L["dosya"].split("/")[-1], u["no"], u["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["ort"], u["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["p95"], u["vibe"]["kapsam_aski"]["IMU_birlesik"]["Z"]["maks"]) for L in Dj["loglar"] for u in L["ucuslar"] if u["tur"] == "ucus"]
F_row = {"pil_pervane": "4S 13 Ah + 9x5x3 (GUIDED, kodla)", "ucus_n": 1, "aski_s": ozet["aski"]["sure_s"], "aski_ThO_ort": ozet["aski"]["ThO"]["ort"], "aski_ThO_p50": ozet["aski"]["ThO"]["p50"],
         "aski_V": ozet["aski"]["V"]["ort"], "aski_I_A": ozet["aski"]["I_A"]["ort"], "aski_P_W": ozet["aski"]["P_W"]["ort"],
         "vibe_aski_ort_XYZ": [zb["X"]["ort"], zb["Y"]["ort"], zb["Z"]["ort"]], "vibe_aski_p95_XYZ": [zb["X"]["p95"], zb["Y"]["p95"], zb["Z"]["p95"]], "vibe_aski_maks_XYZ": [zb["X"]["maks"], zb["Y"]["maks"], zb["Z"]["maks"]],
         "clip": vibe["clip_toplam"], "MOT_THST_HOVER": ozet["ucus"]["ThH_son"]}
C_row = {"pil_pervane": kc["pil"].split(" (")[0] + " + 9x5x3", "ucus_n": kc["ucus_n"], "aski_s": kc["askida_toplam_s"], "aski_ThO_ort": kc["aski_ThO_agirlikli_ort"], "aski_ThO_p50": Cj["konfig_C"]["aski_ThO_p50_ucus_basina"],
         "aski_V": kc["aski_V_agirlikli"], "aski_I_A": kc["aski_I_agirlikli_A"], "aski_P_W": kc["aski_P_agirlikli_W"],
         "vibe_aski_ort_XYZ": [vC["X"]["ort"], vC["Y"]["ort"], vC["Z"]["ort"]], "vibe_aski_p95_XYZ": [vC["X"]["p95"], vC["Y"]["p95"], vC["Z"]["p95"]], "vibe_aski_maks_XYZ": [vC["X"]["maks"], vC["Y"]["maks"], vC["Z"]["maks"]],
         "clip": kc["clip_toplam"], "MOT_THST_HOVER": kc["MOT_THST_HOVER"], "not": "vibe = 3 ucusun ucus-ortalamalarinin istatistigi (n=3), ornek bazli degil"}
D_row = {"pil_pervane": "4S + 9x5x3 (LOIT/STAB, kumanda)", "ucus_n": kd["ucus_n"], "aski_s": kd["aski_toplam_s"], "aski_ThO_ort": kd["aski_ThO"]["ort"], "aski_ThO_p50": kd["aski_ThO"]["p50"],
         "aski_V": kd["aski_V"]["ort"], "aski_I_A": kd["aski_I"]["ort"], "aski_P_W": kd["aski_P_W"]["ort"],
         "vibe_aski_ort_XYZ": [vD["X"]["ort"], vD["Y"]["ort"], vD["Z"]["ort"]], "vibe_aski_p95_XYZ": [vD["X"]["p95"], vD["Y"]["p95"], vD["Z"]["p95"]], "vibe_aski_maks_XYZ": [vD["X"]["maks"], vD["Y"]["maks"], vD["Z"]["maks"]],
         "clip_ucus": kd["clip_toplam_ucus"], "clip_kisa_sicrama": kd["clip_toplam_kisa_sicrama"], "kisa_sicrama_VibeZ_maks": d_kisa_vibeZ_maks,
         "ucus_bazinda_VibeZ_ort_p95_maks": d_ucus_vibeZ, "MOT_THST_HOVER": Dj["MOT_THST_HOVER"]["deger_log"][0]}
ozet["kiyas_C_D"] = {
    "kaynaklar": {"C": C_OZET.replace(ROOT + "/", ""), "D": D_OZET.replace(ROOT + "/", "")},
    "C": C_row, "D": D_row, "F_bu_log": F_row,
    "F_vs_D_ayni_konfig": {"ThO_ort_fark": r(F_row["aski_ThO_ort"] - D_row["aski_ThO_ort"], 3), "ThO_ort_fark_pct": r(100 * (F_row["aski_ThO_ort"] - D_row["aski_ThO_ort"]) / D_row["aski_ThO_ort"], 1),
                           "I_fark_A": r(F_row["aski_I_A"] - D_row["aski_I_A"], 2), "P_fark_W": r(F_row["aski_P_W"] - D_row["aski_P_W"], 1), "P_fark_pct": r(100 * (F_row["aski_P_W"] - D_row["aski_P_W"]) / D_row["aski_P_W"], 1),
                           "V_fark": r(F_row["aski_V"] - D_row["aski_V"], 3),
                           "VibeZ_ort_fark": r(zb["Z"]["ort"] - vD["Z"]["ort"], 2), "VibeZ_p95_fark": r(zb["Z"]["p95"] - vD["Z"]["p95"], 2), "VibeX_ort_fark": r(zb["X"]["ort"] - vD["X"]["ort"], 2),
                           "not": "D pili ayri (4S, kapasite bilinmiyor; D analizinde belirtildi), F pili 4S 13 Ah beyan -> kutle farki logda yok; ThO/guc farkinin kutle mi pil mi kaynakli oldugu AYRISTIRILAMAZ"},
    "F_vs_C": {"ThO_ort_fark_pct": r(100 * (F_row["aski_ThO_ort"] - C_row["aski_ThO_ort"]) / C_row["aski_ThO_ort"], 1), "P_fark_pct": r(100 * (F_row["aski_P_W"] - C_row["aski_P_W"]) / C_row["aski_P_W"], 1),
               "VibeZ_ort_fark": r(zb["Z"]["ort"] - vC["Z"]["ort"], 2)},
}

# ============================================================================ GRAFIKLER
def golge(ax):
    for a0, a1, _ in ds:
        ax.axvspan(a0, a1, color=ASKI_GOLGE, alpha=0.07, lw=0)

def kaydet(fig, ad):
    p = os.path.join(OUT, ad); fig.savefig(p, dpi=130, bbox_inches="tight"); plt.close(fig); ozet["grafikler"].append(ad); return p

x0, x1 = T0 - 8, T1 + 8
# 1) zaman: ThO/ThH + irtifa, akim, gerilim
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True)
ax[0].plot(tc, ThO, color=C[0], label="CTUN.ThO"); ax[0].plot(tc, ThH, color=C[1], ls="--", label="CTUN.ThH (MOT_THST_HOVER)")
ax[0].axhline(ThO[aski].mean(), color=C[0], lw=0.8, ls=":"); ax[0].set_ylabel("gaz (0-1)"); ax[0].legend(loc="center right"); golge(ax[0])
ax[0].set_title("F) 4S 13 Ah + 9x5x3 - %s: arm %.1f-%.1f s, aski %.1f s (golge), ThO aski ort %.3f, MOT_THST_HOVER %.3f" % (LOG.split("/")[-1], T0, T1, ozet["aski"]["sure_s"], ThO[aski].mean(), ThH[0]), fontsize=9)
ax[1].plot(tc, alt, color=C[2], label="CTUN.Alt - taban (m)"); ax[1].plot(tc, DAlt - taban, color=C[3], ls="--", label="CTUN.DAlt - taban (m)")
if len(pw): ax[1].plot(pw[:, 0], pw[:, 2], color=C[6], lw=0.8, label="POS.RelHomeAlt (m)")
ax[1].set_ylabel("irtifa (m)"); ax[1].legend(loc="upper right"); golge(ax[1])
ax[2].plot(bw[:, 0], bw[:, 3], color=C[1], label="BAT.Curr (A)"); ax[2].axhline(I_h, color=C[1], lw=0.8, ls=":"); ax[2].set_ylabel("akim (A)"); ax[2].legend(loc="upper right"); golge(ax[2])
ax[2].annotate("aski ort %.1f A" % I_h, (ta[0], I_h), textcoords="offset points", xytext=(4, 6), fontsize=8, color=TXT2)
bt = b[(b[:, 0] >= x0) & (b[:, 0] <= x1)]
ax[3].plot(bt[:, 0], bt[:, 1], color=C[0], label="BAT.Volt (ham)"); ax[3].plot(bt[:, 0], bt[:, 2], color=C[4], lw=0.9, label="BAT.VoltR (sarkma-telafili)")
ax[3].axhline(V_low, color=C[7], lw=0.9, ls="--"); ax[3].axhline(V_crt, color=C[7], lw=0.9, ls=":")
ax[3].text(x0 + 0.5, V_low + 0.05, "onerilen LOW 14,0 V (3,5 V/hucre)", fontsize=7.5, color=C[7]); ax[3].text(x0 + 0.5, V_crt + 0.05, "onerilen CRT 13,2 V (3,3 V/hucre)", fontsize=7.5, color=C[7])
ax[3].text(x0 + 0.5, 12.85, "logdaki BATT_LOW_VOLT 10 V / CRT 9 V grafik disinda (2,5 / 2,25 V/hucre)", fontsize=7.5, color=TXT2)
ax[3].set_ylim(12.75, 16.0); ax[3].set_ylabel("gerilim (V)"); ax[3].set_xlabel("TimeUS (s)"); ax[3].legend(loc="center right"); golge(ax[3])
for a in ax: a.set_xlim(x0, x1)
kaydet(fig, "zaman_ThO_akim_gerilim.png")

# 2) VIBE xyz + clip
fig, ax = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
vt = v[(v[:, 0] >= x0) & (v[:, 0] <= x1)]
for i, axn in enumerate("XYZ"):
    for inst, col in ((0, C[0]), (1, C[1])):
        x = vt[vt[:, 1] == inst]; ax[i].plot(x[:, 0], x[:, 2 + i], color=col, lw=1.0, label="IMU%d" % inst)
    ax[i].axhline(VIBE_ESIK_IYI, color=C[7], lw=0.8, ls="--"); ax[i].set_ylabel("Vibe%s (m/s2)" % axn); golge(ax[i]); ax[i].set_ylim(0, max(VIBE_ESIK_IYI + 5, vt[:, 2 + i].max() + 2))
    s_ = zb[axn]; ax[i].text(x0 + 0.5, VIBE_ESIK_IYI + 1, "esik 30 (iyi) - aski %s: ort %.1f p95 %.1f maks %.1f" % (axn, s_["ort"], s_["p95"], s_["maks"]), fontsize=7.5, color=TXT2)
ax[0].legend(loc="upper right"); ax[0].set_title("VIBE X/Y/Z - aski golgeli; clip toplam %d" % vibe["clip_toplam"], fontsize=9)
for inst, col in ((0, C[0]), (1, C[1])):
    x = vt[vt[:, 1] == inst]; ax[3].step(x[:, 0], x[:, 5], color=col, where="post", label="IMU%d Clip" % inst)
ax[3].set_ylabel("Clip (sayac)"); ax[3].set_xlabel("TimeUS (s)"); ax[3].legend(loc="upper right"); golge(ax[3])
for a in ax: a.set_xlim(x0, x1)
kaydet(fig, "vibe_xyz.png")

# 3) RCOU C9-C12 (motorlar) ve C1-C4
fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
rt_ = rc[(rc[:, 0] >= x0) & (rc[:, 0] <= x1)]
for k, (m, ch) in enumerate(sorted(mot_kanal.items())):
    ax[0].plot(rt_[:, 0], rt_[:, ch], color=C[k], lw=1.0, label="%s = C%d (aski ort %.0f us)" % (m, ch, ort9[m]))
ax[0].set_ylabel("PWM (us)"); ax[0].legend(loc="upper right", ncol=2); golge(ax[0])
ax[0].set_title("RCOU - ESC kanallari AUX1-4 (C9-C12): aski yayilimi %.0f us (%.1f%% aralik); beklenen PWM (ThO %.3f, expo %.2f) %.0f us" % (rcou["C9_C12_motorlar_aski"]["yayilim_ort_us"], rcou["C9_C12_motorlar_aski"]["yayilim_pct_aralik"], th, e_, rcou["ThO_aski_beklenen_pwm_HESAP"]), fontsize=9)
for k, ch in enumerate(range(1, 5)):
    ax[1].plot(rt_[:, 0], rt_[:, ch], color=C[k], lw=1.0, label="C%d (SERVO%d_FUNCTION=%d, aski ort %.0f us)" % (ch, ch, P.get("SERVO%d_FUNCTION" % ch), rs[:, ch].mean()))
ax[1].set_ylabel("PWM (us)"); ax[1].set_xlabel("TimeUS (s)"); ax[1].legend(loc="upper right", ncol=2); golge(ax[1])
ax[1].set_title("RCOU C1-C4 (MAIN) - fonksiyon M2,M2,M1,M2 kopyalari; motor dengesi icin KULLANILMAZ", fontsize=9)
for a in ax: a.set_xlim(x0, x1)
kaydet(fig, "rcou_C1_C4_ve_motorlar.png")

# 4) FFT: AccZ + GyrX/GyrY, IMU0 ve IMU1; aski vs tabanlar
fig, ax = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
for j, inst in enumerate((0, 1)):
    for i, ad in enumerate(("AccZ", "GyrX", "GyrY")):
        a = ax[i, j]
        for kap_, col, lab in (("aski", C[0], "aski %.1f s" % (en[1] - en[0])), ("rolanti", C[1], "armli rolanti (yerde)"), ("kapali", C[2], "motor kapali (yerde)")):
            e2 = fft_egriler.get((kap_, inst, ad))
            if e2: a.plot(e2[0], e2[1], color=col, lw=1.0, label=lab)
        a.axvspan(2, 12.5, color=C[3], alpha=0.06, lw=0)
        a.set_ylabel("%s genlik (%s)" % (ad, "m/s2" if ad.startswith("Acc") else "rad/s")); a.set_title("IMU%d %s" % (inst, ad), fontsize=9)
        f_ = fft["aski"]["IMU%d" % inst].get(ad)
        if f_ and f_["band_2_15Hz_tepeler"]:
            tp = f_["band_2_15Hz_tepeler"][0]; a.annotate("2-12,5 Hz tepe %.1f Hz" % tp["f_hz"], (tp["f_hz"], tp["genlik"]), textcoords="offset points", xytext=(6, 4), fontsize=7.5, color=TXT2)
        if i == 0 and j == 0: a.legend(loc="upper right")
ax[2, 0].set_xlabel("frekans (Hz)  [IMU 25 Hz -> Nyquist 12,5 Hz]"); ax[2, 1].set_xlabel("frekans (Hz)")
fig.suptitle("IMU FFT (Hanning, genlik spektrumu) - pervane temel frekansi (HESAP ~%.0f Hz ust sinir) COZULEMEZ, 0-12,5 Hz'e katlanir" % (rpm_bos / 60), fontsize=9)
kaydet(fig, "fft_aski_AccZ_gyro.png")

# 5) tutum: Roll/Pitch vs Des
fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
at_ = aa_all[(aa_all[:, 0] >= x0) & (aa_all[:, 0] <= x1)]
ax[0].plot(at_[:, 0], at_[:, 2], color=C[0], label="Roll"); ax[0].plot(at_[:, 0], at_[:, 1], color=C[0], ls="--", lw=0.9, label="DesRoll"); ax[0].set_ylabel("roll (deg)"); ax[0].legend(loc="upper right"); golge(ax[0])
ax[1].plot(at_[:, 0], at_[:, 4], color=C[1], label="Pitch"); ax[1].plot(at_[:, 0], at_[:, 3], color=C[1], ls="--", lw=0.9, label="DesPitch"); ax[1].set_ylabel("pitch (deg)"); ax[1].legend(loc="upper right"); golge(ax[1])
ax[2].plot(at_[:, 0], at_[:, 2] - at_[:, 1], color=C[0], label="Roll - DesRoll"); ax[2].plot(at_[:, 0], at_[:, 4] - at_[:, 3], color=C[1], label="Pitch - DesPitch"); ax[2].set_ylabel("hata (deg)"); ax[2].set_xlabel("TimeUS (s)"); ax[2].legend(loc="upper right"); golge(ax[2])
ax[0].set_title("ATT - askida RMS hata roll %.2f / pitch %.2f / yaw %.2f deg; maks |roll| %.1f |pitch| %.1f deg" % (tutum["aski"]["roll_rms_hata_deg"], tutum["aski"]["pitch_rms_hata_deg"], tutum["aski"]["yaw_rms_hata_deg"], tutum["aski"]["roll_maks_abs_deg"], tutum["aski"]["pitch_maks_abs_deg"]), fontsize=9)
for a in ax: a.set_xlim(x0, x1)
kaydet(fig, "att_roll_pitch_des_hata.png")

# 6) pil: V-I sacilimi + polyfit; V vs mAh + 14,0 V ekstrapolasyonu
fig, ax = plt.subplots(1, 2, figsize=(12, 4.8))
ax[0].scatter(tum[:, 3], tum[:, 1], s=6, color=TXT2, alpha=0.35, label="tum pencere (+/-5 s)")
ax[0].scatter(kal[:, 3], kal[:, 1], s=10, color=C[0], label="kalkis gecisi")
ax[0].scatter(ini[:, 3], ini[:, 1], s=10, color=C[1], label="inis gecisi")
ax[0].scatter(Ia, Va, s=6, color=C[2], alpha=0.5, label="aski")
Ig = np.linspace(0, tum[:, 3].max(), 50)
for R_, col, lab in ((R_a, C[0], "kalkis"), (R_b, C[1], "inis"), (R_c, TXT2, "tum")):
    if R_: ax[0].plot(Ig, R_["V_kesim_I0"] - R_["R_paket_ohm"] * Ig, color=col, lw=1.0, ls="--", label="polyfit %s: R=%.1f mOhm/hucre, r2=%.2f" % (lab, R_["R_hucre_mohm"], R_["r2"]))
ax[0].set_xlabel("BAT.Curr (A)"); ax[0].set_ylabel("BAT.Volt (V)"); ax[0].legend(fontsize=7.5, loc="lower left"); ax[0].set_title("Ic direnc: dV/dI dogrusal uydurma (numpy.polyfit)", fontsize=9)
ax[1].scatter(mAh_a, Va, s=6, color=C[2], alpha=0.5, label="aski: V_yuklu vs CurrTot")
ax[1].scatter(mAh_a[plm], Va[plm], s=6, color=C[0], alpha=0.8, label="plato (son %.0f s)" % PLATO_S)
xmax = max([x for x in (mAh_low_dinlenme_p, mAh_low_dinlenme, mAh_a[-1]) if x] + [mAh_a[-1]]) * 1.03
mg = np.linspace(mAh_a[0], xmax, 100)
ax[1].plot(mg, pf[1] + pf[0] * mg, color=C[2], ls=":", lw=1.0, label="(i) tum aski uydurma %.1f mV/100 mAh (gecis kaynakli, GECERSIZ)" % (egim_V_per_Ah / 10 * 1000))
ax[1].plot(mg, pfp[1] + pfp[0] * mg, color=C[0], ls="--", lw=1.2, label="(ii) plato uydurma %.1f mV/100 mAh (TERCIH)" % (egim_plato_V_per_Ah / 10 * 1000))
ax[1].axhline(V_low, color=C[7], lw=0.9, ls="--", label="14,0 V (3,5 V/hucre) yuklu")
ax[1].axhline(V_low - sag, color=C[7], lw=0.9, ls=":", label="14,0 - I*R = %.2f V (dinlenme 3,5 V/hucre)" % (V_low - sag))
if mAh_low_dinlenme_p: ax[1].axvline(mAh_low_dinlenme_p, color=C[0], lw=0.7, ls=":"); ax[1].annotate("%.0f mAh" % mAh_low_dinlenme_p, (mAh_low_dinlenme_p, V_low - sag), textcoords="offset points", xytext=(-40, 8), fontsize=7.5, color=TXT2)
if mAh_low_dinlenme: ax[1].axvline(mAh_low_dinlenme, color=C[2], lw=0.7, ls=":")
ax[1].set_xlabel("BAT.CurrTot (mAh, log basindan)"); ax[1].set_ylabel("BAT.Volt (V)"); ax[1].legend(fontsize=7, loc="upper right")
ax[1].set_ylim(12.5, 14.9); ax[1].set_xlim(0, xmax)
ax[1].set_title("3,5 V/hucre'ye ekstrapolasyon (HESAP; log %.0f mAh = beyan kapasitenin %%%.1f'i)" % (mAh_a[-1] - mAh_a[0], 100 * (mAh_a[-1] - mAh_a[0]) / PIL_MAH_BEYAN), fontsize=9)
kaydet(fig, "pil_ic_direnc_ve_ekstrapolasyon.png")

# 7) kiyas C / D / F: ThO, P, VibeZ (ayri eksenler, kucuk coklu)
fig, ax = plt.subplots(1, 4, figsize=(13, 3.8))
etiket = ["C\n3S\n9x5x3", "D\n4S\n9x5x3\n(kumanda)", "F\n4S 13Ah\n9x5x3\n(GUIDED)"]
seri = [("aski ThO ort", [C_row["aski_ThO_ort"], D_row["aski_ThO_ort"], F_row["aski_ThO_ort"]], "gaz (0-1)"),
        ("aski guc V*I (W)", [C_row["aski_P_W"], D_row["aski_P_W"], F_row["aski_P_W"]], "W"),
        ("aski akim (A)", [C_row["aski_I_A"], D_row["aski_I_A"], F_row["aski_I_A"]], "A"),
        ("aski VibeZ ort (m/s2)", [vC["Z"]["ort"], vD["Z"]["ort"], zb["Z"]["ort"]], "m/s2")]
for a, (bas, vals, yl) in zip(ax, seri):
    bars = a.bar(etiket, vals, color=[C[2], C[1], C[0]], width=0.6, zorder=3)
    for bb_, vv_ in zip(bars, vals): a.text(bb_.get_x() + bb_.get_width() / 2, vv_, "%.3g" % vv_, ha="center", va="bottom", fontsize=8, color=TXT)
    a.set_title(bas, fontsize=9); a.set_ylabel(yl); a.tick_params(axis="x", labelsize=7.5)
    a.set_ylim(0, max(vals) * 1.18)
ax[3].axhline(VIBE_ESIK_IYI, color=C[7], lw=0.8, ls="--"); ax[3].text(-0.4, VIBE_ESIK_IYI + 0.5, "esik 30", fontsize=7.5, color=C[7])
ax[3].set_ylim(0, max(VIBE_ESIK_IYI + 4, max(seri[3][1]) * 1.18))
fig.suptitle("Konfig kiyasi (askida): C n=3 ucus, D n=3 ucus (ayni pervane, baska 4S pil), F bu log", fontsize=9)
kaydet(fig, "kiyas_C_D_F.png")

# ============================================================================ BULGULAR
bul = []
u = ozet["ucus"]; a_ = ozet["aski"]; pl = ozet["pil"]; us = ozet["ucus_suresi"]; fsb = ozet["failsafe"]["bu_logda_gerilim_vs_onerilen_esikler"]
bul.append("UCUS: arm %.2f s (MAVLINK, GUIDED) -> LAND %.2f s (GCS) -> disarm %.2f s (LANDED); pencere %.1f s, motorlu %.1f s, aski %.1f s (n=%d, en uzun kesintisiz dilim %.1f s). Irtifa: CTUN.Alt tabani %.2f m (EKF orijini) cikarilinca aski ort %.2f m, maks %.2f m; POS.RelHomeAlt maks %.2f m -> ilk taramadaki '4,76 m' EKF-orijin gorelidir, yerden yukseklik ~3 m (kullanici beyani '~3 m' ile UYUMLU). Ucus icinde ERR/failsafe/EKF olayi YOK." % (
    T0, next((tt for tt, md, _ in A["MODE"] if md == 9), float("nan")), T1, u["pencere_s"], u["motorlu_s"], a_["sure_s"], a_["n"], a_["en_uzun_dilim_s"], taban, a_["alt_m"]["ort"], u["alt_maks_m"], u["alt_maks_m_POS_RelHomeAlt"]))
bul.append("ASKI (n=%d, %.1f s): ThO ort %.3f / p50 %.3f / p05 %.3f / p95 %.3f; V ort %.2f V (%.3f V/hucre; bas %.3f, min %.3f V/hucre); I ort %.1f A (p95 %.1f, maks %.1f); P=V*I ort %.0f W (p95 %.0f). Tuketim %.0f mAh/dk. MOT_THST_HOVER %.4f log boyunca SABIT (PARM 3 kayit ayni) ve aski ThO'dan %+.1f%% yuksek: ogrenme GUIDED'da calismadi (havada is_zero(PSCD.DVD) orani %.3f, uygun %.1f s)." % (
    a_["n"], a_["sure_s"], a_["ThO"]["ort"], a_["ThO"]["p50"], a_["ThO"]["p05"], a_["ThO"]["p95"], a_["V"]["ort"], a_["V_hucre"]["ort"], a_["V_hucre"]["bas"], a_["V_hucre"]["min"], a_["I_A"]["ort"], a_["I_A"]["p95"], a_["I_A"]["maks"], a_["P_W"]["ort"], a_["P_W"]["p95"], a_["mAh_per_dk"], ThH[0], a_["MOT_THST_HOVER_vs_ThO"]["fark_pct_ThO"],
    ozet["ucus"]["hover_ogrenme"]["kosul_oranlari_havada"]["is_zero(PSCD.DVD)"], ozet["ucus"]["hover_ogrenme"]["uygun_s"]))
bul.append("MOT_THST_HOVER kokeni: 11-18-16 logu 0,5017 ile bitti (BOOTCNT 139, FLTTIME 942 s); 12-40-55 (BOOTCNT 143, FLTTIME 1027 s) ve bu log (BOOTCNT 145, FLTTIME 1027->1095 s) 0,3895 ile basliyor -> 0,3895 klasorde OLMAYAN 140-142 acilislarindaki ~85 s ucusta ogrenilmis; bu logda degismedi.")
bul.append("PIL DOLU DEGILDI: ilk gerilim %.2f V = %.3f V/hucre (dolu 4,20). Sarkma: ilk -> aski ort %.2f V, ilk -> min %.2f V (%.3f V/hucre); V_min %.3f V (%.3f V/hucre) t=%.1f s @ %.1f A; VoltR (FC sarkma-telafili) min %.2f V; disarm+10 s toparlanma %+.2f V. Ic direnc (numpy.polyfit dV/dI): kalkis gecisi %s mOhm/hucre (r2 %s, I %s A), inis gecisi %s mOhm/hucre (r2 %s), tum pencere %s (SoC kaymasi karisik), arm-oncesi/aski yontemi %s, FC BAT.Res %s mOhm/hucre; HESAP sarkma I*R = %.2f V vs olculen %.2f V." % (
    V0, V0 / HUCRE_N, pl["sarkma_V_ilk_askiya"], pl["sarkma_V_ilk_min"], pl["sarkma_V_hucre_ilk_min"], pl["V_min"], pl["V_min_hucre"], pl["V_min_t"], pl["V_min_I"], pl["VoltR_min"], pl["toparlanma_V_disarm_10s"],
    R_a["R_hucre_mohm"] if R_a else None, R_a["r2"] if R_a else None, R_a["I_aralik_A"] if R_a else None, R_b["R_hucre_mohm"] if R_b else None, R_b["r2"] if R_b else None, R_c["R_hucre_mohm"] if R_c else None,
    pl["ic_direnc"]["e_arm_oncesi_vs_aski"]["R_hucre_mohm"] if pl["ic_direnc"]["e_arm_oncesi_vs_aski"] else None, pl["ic_direnc"]["f_BAT_Res_FC"]["aski_ort_mohm_hucre"], pl["ic_direnc"]["sarkma_HESAP_askida_V"], pl["ic_direnc"]["sarkma_olculen_ilk_askiya_V"]))
y2 = us["yontem_2_3.5V_hucre"]; yp = y2["ii_plato_uydurma_TERCIH"]; yi = y2["i_tum_aski_uydurma"]; yo = y2["iii_dinlenme_gerilimi_egimi"]
bul.append("UCUS SURESI (HESAP, kapasite kullanici beyani 13 000 mAh, DOLU pil varsayimi): %%80 kural -> %.0f mAh / %.1f A = %.1f dk (motorlu ort akim %.1f A ile %.1f dk; p95 %.1f A ile %.1f dk). 3,5 V/hucre yontemi (bu pil 3,89 V/hucre ile basladi): OLCUM - yuklu gerilim 14,0 V'in altina t=%.1f s'de, aski basindan %.0f s / %.0f mAh sonra indi. Ekstrapolasyon: (i) tum aski uydurmasi %.1f mV/100 mAh (r2 %.2f) kalkis polarizasyon gecisini icerdigi icin GECERSIZ (dinlenme 3,5 V'a %s mAh verir, asiri pesimist); (ii) PLATO (son %.0f s, %.0f-%.0f mAh) egimi %.1f +/- %.1f mV/100 mAh (r2 %.2f, egim gurultu icinde -> KOTU KOSULLU): sarkma I*R=%.2f V cikarilinca dinlenme 3,5 V/hucre'ye aski sonundan %s mAh = %s dk (log basindan toplam %s mAh = %s dk) - buyukluk sirasi, olcum degil; (iii) yuksuz gerilim egimi (%.2f -> %.2f V, %.0f mAh, disarm+%.0f s eksik toparlanma) alt sinir %s mAh. Hepsi %.0f mAh gozlemden (beyanin %%%.1f'i) ekstrapolasyon; LiPo egrisi dogrusal degil -> 63 s / 658 mAh aski 3,5 V'a kalan mAh'i BELIRLEYEMEZ (aralik 3,2 Ah alt sinir .. ~11 Ah kotu kosullu); 13 Ah beyani ancak tam bosaltma testiyle dogrulanir." % (
    us["kullanilabilir_mAh"], us["I_aski_A"], us["tahmin_dk_aski_akimi"], us["I_motorlu_A"], us["tahmin_dk_motorlu_ort_akim"], np.percentile(Ia, 95), us["tahmin_dk_aski_p95_akim"],
    y2["olculen_yuklu_14.0V_ilk_inis"]["t"], y2["olculen_yuklu_14.0V_ilk_inis"]["aski_basindan_s"], y2["olculen_yuklu_14.0V_ilk_inis"]["aski_basindan_mAh"],
    yi["egim_mV_per_100mAh"], yi["r2"], yi["dinlenme_3.5V_kalan_mAh_aski_basindan"], PLATO_S, yp["mAh_aralik"][0], yp["mAh_aralik"][1], yp["egim_mV_per_100mAh"], yp["egim_std_hata_V_per_Ah"] * 100, yp["r2"], sag, yp["dinlenme_3.5V_kalan_mAh_aski_sonundan"], yp["dinlenme_3.5V_kalan_dk_aski_akimi"], yp["dinlenme_3.5V_toplam_mAh_log_basindan"], yp["toplam_dk_log_basindan_HESAP"],
    yo["V_log_basi_yuksuz"], yo["V_log_sonu_yuksuz"], yo["mAh"], yo["disarm_sonrasi_s"], yo["dinlenme_3.5V_kalan_mAh_log_sonundan_ALT_SINIR"], mAh_a[-1] - mAh_a[0], 100 * (mAh_a[-1] - mAh_a[0]) / PIL_MAH_BEYAN))
bul.append("TITRESIM (askida, IMU0+IMU1 birlesik n=%d): X ort %.1f / p95 %.1f / maks %.1f; Y %.1f / %.1f / %.1f; Z %.1f / %.1f / %.1f m/s2; clip 0/0 (log tamaminda da 0). 30 m/s2 esigi: askida hicbir ornek asmiyor (%.1f%%), motorlu tumunde %.1f%%; Z p95 esigin %.0f%%'i. Kalkis dilimi maks XYZ %s, inis dilimi %s (motorlu maks Z %.1f) -> hepsi <30, <<60." % (
    zb["Z"]["n"], zb["X"]["ort"], zb["X"]["p95"], zb["X"]["maks"], zb["Y"]["ort"], zb["Y"]["p95"], zb["Y"]["maks"], zb["Z"]["ort"], zb["Z"]["p95"], zb["Z"]["maks"],
    100 * vibe["esik_kiyasi"]["ornek_ustu_30_orani_aski"], 100 * vibe["esik_kiyasi"]["ornek_ustu_30_orani_motorlu"], 100 * zb["Z"]["p95"] / VIBE_ESIK_IYI, vibe["kalkis_dilimi_maks_XYZ"], vibe["inis_dilimi_maks_XYZ"], vibe["esik_kiyasi"]["motorlu_maks_Z"]))
f0 = fft["aski"]["IMU0"]; f1 = fft["aski"]["IMU1"]; pv = fft["pervane_temel_frekansi_HESAP"]
bul.append("FFT (en uzun aski dilimi %.1f s, IMU %.1f Hz -> Nyquist %.2f Hz): AccZ IMU0 tepeler %s (rms %.3f m/s2; motor-kapali taban rms %.3f); IMU1 %s. 2-12,5 Hz bandinda AccZ IMU0 en buyuk tepe %s, GyrX %s, GyrY %s. Pervane temel frekansi HESAP (KV %d beyan x %.2f V x PWM orani %.3f): <=%.0f Hz (yuklu ~%.0f Hz), pal gecis <=%.0f Hz -> 25 Hz kayitla COZULEMEZ, %.1f/%.1f Hz'e katlanir (alias): 2-12,5 Hz'deki tepe kol esnekligi mi katlanmis pervane mi AYIRT EDILEMEZ; kesin sonuc icin INS_LOG_BAT_MASK=1 gerekli." % (
    en[1] - en[0], ozet["meta"]["imu_hz"], ozet["meta"]["imu_hz"] / 2, [(p_["f_hz"], p_["genlik"]) for p_ in f0["AccZ"]["tepeler"][:3]], f0["AccZ"]["rms"], fft["taban_motor_kapali"]["IMU0"]["AccZ"]["rms"],
    [(p_["f_hz"], p_["genlik"]) for p_ in f1["AccZ"]["tepeler"][:3]], f0["AccZ"]["band_2_15Hz_tepeler"][:1], f0["GyrX"]["band_2_15Hz_tepeler"][:1], f0["GyrY"]["band_2_15Hz_tepeler"][:1],
    MOTOR_KV, Va.mean(), pwm_orani, pv["f_temel_hz_ust_sinir"], pv["f_temel_hz_%85"], pv["f_pal_gecis_hz_ust_sinir"], pv["alias_25Hz_HESAP_hz"]["f_temel_ust"], pv["alias_25Hz_HESAP_hz"]["f_temel_%85"]))
r9 = rcou["C9_C12_motorlar_aski"]; r1 = rcou["C1_C4_aski"]
bul.append("RCOU askida: C1-C4 (MAIN, fonksiyon M2/M2/M1/M2 kopyalari) ort %s us, yayilim %.0f us. Gercek ESC kanallari C9-C12: %s us (std %s), yayilim %.0f us = %%%.1f aralik, en yuksek %s / en dusuk %s; cift farklari yaw(CCW-CW) %+.0f, pitch(on-arka) %+.0f, roll(sag-sol) %+.0f us; ThO %.3f icin beklenen PWM %.0f us (expo %.2f). Motorlu maks %s." % (
    r1["ort_us"], r1["yayilim_ort_us"], r9["M_ort_us"], r9["M_std_us"], r9["yayilim_ort_us"], r9["yayilim_pct_aralik"], r9["en_yuksek"], r9["en_dusuk"],
    r9["cift_farklari_us"]["CCW(M1+M2)-CW(M3+M4)_yaw"], r9["cift_farklari_us"]["on(M1+M3)-arka(M2+M4)_pitch"], r9["cift_farklari_us"]["sag(M1+M4)-sol(M2+M3)_roll"], th, rcou["ThO_aski_beklenen_pwm_HESAP"], e_, rcou["motorlu_maks_us"]))
ta_ = tutum["aski"]
bul.append("TUTUM askida: Roll-DesRoll RMS %.2f deg (maks |hata| %.2f), Pitch RMS %.2f (maks %.2f), Yaw RMS %.2f; |roll| maks %.1f, |pitch| maks %.1f deg; roll ort %+.2f pitch ort %+.2f (DesRoll %+.2f DesPitch %+.2f); ErrRP maks %.3f. Hiz halkasi RMS hata roll/pitch/yaw %.1f/%.1f/%.1f dps; ROut/POut/YOut ort %+.4f/%+.4f/%+.4f." % (
    ta_["roll_rms_hata_deg"], ta_["roll_hata_maks_abs_deg"], ta_["pitch_rms_hata_deg"], ta_["pitch_hata_maks_abs_deg"], ta_["yaw_rms_hata_deg"], ta_["roll_maks_abs_deg"], ta_["pitch_maks_abs_deg"], ta_["roll_ort_deg"], ta_["pitch_ort_deg"], ta_["DesRoll_ort_deg"], ta_["DesPitch_ort_deg"], ta_["ErrRP_maks"],
    tutum["aski_hiz"]["roll_rate_rms_hata_dps"], tutum["aski_hiz"]["pitch_rate_rms_hata_dps"], tutum["aski_hiz"]["yaw_rate_rms_hata_dps"], tutum["aski_hiz"]["ROut_ort"], tutum["aski_hiz"]["POut_ort"], tutum["aski_hiz"]["YOut_ort"]))
yw = tutum["yaw"]
bul.append("YAW SALINIMI (askida): DesYaw sabit (%.1f deg, std %.2f) ama Yaw-DesYaw RMS %.2f deg, p95 |hata| %.2f, maks %.2f deg; 10 s dilimlerde RMS %s; GyrZ FFT baskin %s (rms %.3f rad/s) -> ~%.1f Hz kapali cevrim yaw salinimi; yaw hizi p05/p95 %s dps, YOut maks |%.3f| p95 %.3f. Yaw ayarlari: %s. Kaynak (ayar / 3 pal pervanenin yaw otoritesi / ruzgar) bu logdan ayristirilamaz; roll/pitch RMS ~1 deg iken yaw 5 deg -> 21 Eylul oncesi bakilmali." % (
    yw["DesYaw_aski_ort_deg"], yw["DesYaw_aski_std_deg"], yw["aski_hata_rms_deg"], yw["aski_hata_p95_abs_deg"], yw["aski_hata_maks_abs_deg"], [(d_["t"][0], d_["rms_deg"]) for d_ in yw["dilimler_10s"]],
    [(p_["f_hz"], p_["genlik"]) for p_ in (yw["GyrZ_FFT_IMU0_baskin"] or [])[:2]], yw["GyrZ_rms_rad_s"] or 0, (yw["GyrZ_FFT_IMU0_baskin"] or [{"f_hz": 0}])[0]["f_hz"], yw["yaw_rate_Y_p05_p95_dps"], yw["YOut_maks_abs"], yw["YOut_p95_abs"], yw["parm"]))
ek0 = ekf["cekirdek"]["0"]
bul.append("EKF/OLAYLAR: XKF4 core0 SV/SP/SH/SM maks %.2f/%.2f/%.2f/%.2f (esik 1), innov>1 ornek %d, lane switch %d, GPS 3D fix %d-%d uydu HDOP %.2f-%.2f, PM NLon %d. ERR: ucus icinde 0; arm oncesi GCS failsafe (%.1f-%.1f s, arm oncesi PreArm engeli sonra temizlendi), disarm sonrasi GCS FS %.1f s ve radyo FS %.1f s ('Radio Failsafe - Disarming', zaten disarm). EV: ARMED 236,28, AUTO_ARMED, INTERLOCK_ENABLED, NOT_LANDED 239,15, EKF_YAW_RESET 241,98 (in-flight yaw alignment), LAND_COMPLETE_MAYBE 309,38, LAND_COMPLETE 310,18, DISARMED 310,68." % (
    ek0["SV_maks"], ek0["SP_maks"], ek0["SH_maks"], ek0["SM_maks"], ek0["innov_>1_n"], ekf["lane_switch_n"], ekf["gps"]["NSats_min_maks"][0], ekf["gps"]["NSats_min_maks"][1], ekf["gps"]["HDop_min_maks"][0], ekf["gps"]["HDop_min_maks"][1], ekf["PM"]["NLon_toplam"],
    A["ERR"][0][0], A["ERR"][1][0], A["ERR"][2][0], A["ERR"][4][0]))
bul.append("FAILSAFE UYUMU: logda BATT_LOW_VOLT %.1f / BATT_CRT_VOLT %.1f / BATT_ARM_VOLT %.1f V (= %.2f / %.2f / %.2f V/hucre @4S), BATT_CAPACITY %.0f (3S pil degeri), BATT_LOW_TIMER %.0f s, BATT_FS_VOLTSRC %.0f (ham), FS_LOW/CRT_ACT %.0f/%.0f (Land). UYGUN DEGIL: hucre 3,0 V altinda hasar gorur, esikler hicbir zaman tetiklenmez; RemPct %.0f%% (8000 ile) yerine 13 000 ile %.1f%% olurdu. ONERI: LOW 14,0 V, CRT 13,2 V, CAPACITY 13000, ARM_VOLT 14,4 V (3,6 V/hucre; 14,8 daha tutucu). BU LOGDA: V_min ham %.3f V (%.3f V/hucre) -> 14,0 V'a marj %+.2f V = ESIGIN ALTINA INDI: ham V<14,0 toplam %.1f s, en uzun kesintisiz %.1f s (LOW_TIMER 10 s) -> LOW failsafe %s; VoltR (sarkma-telafili) min %.2f V, <14,0 V %.1f s -> VOLTSRC=1 ile %s. 13,2 V'a marj %+.2f V. Yorum: 3,89 V/hucre ile (dolu degil) baslayan pil 37 A yukte 3,46 V/hucre'ye sarktigi icin 3,5 V/hucre HAM esigi bu ucusta LAND tetiklerdi; dolu pil (4,2 V) ile marj ~1,2 V daha genis. Esik secimi VOLTSRC ile birlikte dusunulmeli." % (
    fs_p["BATT_LOW_VOLT"], fs_p["BATT_CRT_VOLT"], fs_p["BATT_ARM_VOLT"], fs_p["BATT_LOW_VOLT"] / 4, fs_p["BATT_CRT_VOLT"] / 4, fs_p["BATT_ARM_VOLT"] / 4, fs_p["BATT_CAPACITY"], fs_p["BATT_LOW_TIMER"], fs_p["BATT_FS_VOLTSRC"], fs_p["BATT_FS_LOW_ACT"], fs_p["BATT_FS_CRT_ACT"],
    pl["RemPct_son_log_BATT_CAPACITY_8000"], pl["RemPct_13000_ile_HESAP"], fsb["V_min_ham"], fsb["V_min_ham_hucre"], fsb["LOW_14.0V_marj_V"], fsb["ham_V_LOW_altinda_toplam_s"], fsb["ham_V_LOW_altinda_en_uzun_kosu_s"],
    "TETIKLENIRDI (LAND)" if fsb["LOW_tetiklenir_miydi_ham"] else "tetiklenmezdi", fsb["VoltR_min"], fsb["VoltR_LOW_altinda_toplam_s"], "tetiklenirdi" if fsb["LOW_tetiklenir_miydi_VoltR"] else "tetiklenmezdi", fsb["CRT_13.2V_marj_V"]))
kk = ozet["kiyas_C_D"]
bul.append("KIYAS: aski ThO C %.3f / D %.3f / F %.3f; guc C %.0f / D %.0f / F %.0f W; akim C %.1f / D %.1f / F %.1f A; VibeZ ort C %.1f / D %.1f / F %.1f (p95 C %.1f / D %.1f / F %.1f). F vs D (ayni pervane, baska 4S pil; kutle logda yok): ThO %+.1f%%, guc %+.1f%%, VibeZ ort %+.1f, VibeX ort %+.1f. D'nin yuksek VIBE'i KISA SICRAMADAN: D ucuslarinda askida VibeZ ort/p95/maks %s (hepsi <30), clip 0; clip 19 ve VibeZ maks %.1f yalniz 11-18-16 pencere 3 kisa sicramasinda (yer carpmasi). Bu logda ayni konfigin %.1f s temiz askisi: VibeZ ort %.1f, maks %.1f, clip 0 -> D'nin aski titresimi de dusuktu; sicrama olayi konfige ait degil." % (
    kk["C"]["aski_ThO_ort"], kk["D"]["aski_ThO_ort"], kk["F_bu_log"]["aski_ThO_ort"], kk["C"]["aski_P_W"], kk["D"]["aski_P_W"], kk["F_bu_log"]["aski_P_W"], kk["C"]["aski_I_A"], kk["D"]["aski_I_A"], kk["F_bu_log"]["aski_I_A"],
    vC["Z"]["ort"], vD["Z"]["ort"], zb["Z"]["ort"], vC["Z"]["p95"], vD["Z"]["p95"], zb["Z"]["p95"], kk["F_vs_D_ayni_konfig"]["ThO_ort_fark_pct"], kk["F_vs_D_ayni_konfig"]["P_fark_pct"], kk["F_vs_D_ayni_konfig"]["VibeZ_ort_fark"], kk["F_vs_D_ayni_konfig"]["VibeX_ort_fark"],
    [(x[2], x[3], x[4]) for x in d_ucus_vibeZ], d_kisa_vibeZ_maks, a_["sure_s"], zb["Z"]["ort"], zb["Z"]["maks"]))
ozet["bulgular"] = bul
ozet["grafikler"] = [os.path.join(OUT, g).replace("\\", "/") for g in ozet["grafikler"]]

with open(os.path.join(OUT, "ozet.json"), "w", encoding="utf-8") as f:
    json.dump(ozet, f, ensure_ascii=False, indent=1)
print("OK", os.path.join(OUT, "ozet.json"))
for s in bul: print("-", s)
