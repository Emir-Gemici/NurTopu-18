#!/usr/bin/env python3
"""KONFIGURASYON A (3S + 10x4,5 pervane; kullanici beyani) — derin ucus analizi.

Girdi : results/ucus_analiz_20260915/tum_loglar.json (ortak arac T276; pencereler ve etiketler
        oradan alinir) + ham .bin dosyalari (pymavlink DFReader; SciPy YOK — anayasa m.4).
Cikti : results/ucus_analiz_20260915/A_3S_1045/ozet.json + PNG grafikler (matplotlib Agg).

Her sayi LOGDAN hesaplanir. Pil (3S 8000 mAh), pervane (1045) ve kutle LOGDA YOK — kullanici beyani.
Kisa sicramalar (< 5 s motorlu) askidan AYRI sayilir; askı orneklemi ortak aracla aynidir:
irtifa > 1 m, |dikey hiz| < 0,5 m/s (CTUN.Alt turevi), 0,25 <= ThO <= 0,75.

MOTOR HARITASI (PARM SERVOn_FUNCTION, her A logunda ayni): motorlar AUX1-4 = SERVO9..12 ->
RCOU.C9 = Motor4, C10 = Motor2, C11 = Motor1, C12 = Motor3. Ana cikislar C1,C2,C4 = Motor2 kopyasi,
C3 = Motor1 kopyasi; ortak aracin "C1-C4 dengesi" bu yuzden M3/M4'u hic gormez (bulgu).
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "scripts"))
import ucus_bin_analiz as UBA  # noqa: E402  (ortak arac: aski maskesi, FFT, esikler)

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

CIKTI_DIZIN = KOK / "results/ucus_analiz_20260915/A_3S_1045"
TUM_JSON = KOK / "results/ucus_analiz_20260915/tum_loglar.json"
ETIKET = "A"
HUCRE_N = 3
PIL_MAH_BEYAN = 8000.0          # kullanici beyani (3S)
KULLANILABILIR_ORAN = 0.80
MOTOR_KANAL = {"M1": "C11", "M2": "C10", "M3": "C12", "M4": "C9"}   # SERVO9..12_FUNCTION = 36,34,33,35
MOTOR_KONUM = {"M1": "on-sag CCW", "M2": "arka-sol CCW", "M3": "on-sol CW", "M4": "arka-sag CW"}  # QUAD X
MANUEL_GAZ_KIPLERI = {0, 1, 11}  # STAB, ACRO, DRIFT: hover ogrenmesi yapilmaz (Copter::update_throttle_hover)
OGRENME_TC_S = 10.0              # AP_MOTORS_THST_HOVER_TC
OGRENME_TILT_DEG = 5.0           # |roll|,|pitch| < 500 cdeg
OGRENME_VZ_CMS = 60.0            # |climb rate| < 60 cm/s
DVD_SIFIR_ESIK_MS = 1.19e-9      # is_zero(vel_desired.z cm/s) = FLT_EPSILON -> PSCD.DVD (m/s) esigi; OLCULDU: ThH yalniz |DVD|<=1,1e-9'da degisti

# dataviz palet (referans): kategorik sira sabit
RENK = {"mavi": "#2a78d6", "turuncu": "#eb6834", "aqua": "#1baf7a", "sari": "#eda100", "magenta": "#e87ba4",
        "yesil": "#008300", "mor": "#4a3aa7", "kirmizi": "#e34948", "kritik": "#d03b3b", "gri": "#898781",
        "izgara": "#e1e0d9", "metin": "#0b0b0b", "ikincil": "#52514e", "yuzey": "#fcfcfb"}
KONFIG_RENK = {"A": RENK["mavi"], "B": RENK["turuncu"], "C": RENK["aqua"], "D": RENK["sari"], None: RENK["gri"]}


def _r(x, n=3):
    if x is None:
        return None
    x = float(x)
    return round(x, n) if math.isfinite(x) else None


def _p(a, q):
    return float(np.percentile(a, q)) if len(a) else None


def _temiz(o):
    return UBA._temiz(o)


# ----------------------------------------------------------------------------- okuma (genis)
def oku_genis(yol: Path):
    """Tek gecis: CTUN, BAT, VIBE, RCOU(C1..C14), RCIN(C3), ATT, RATE, IMU(0), XKF4, MOTB, PSCD, PARM, MODE, EV, ERR, MSG."""
    from pymavlink import DFReader
    log = DFReader.DFReader_binary(str(yol))
    d = defaultdict(list)
    parm, parm_ilk, parm_degisim = {}, {}, []
    while True:
        m = log.recv_msg()
        if m is None:
            break
        tip = m.get_type()
        tu = getattr(m, "TimeUS", None)
        t = tu / 1e6 if tu is not None else None
        if tip == "CTUN":
            d["ctun"].append((t, m.ThO, m.ThH, m.Alt, getattr(m, "CRt", 0.0), getattr(m, "DCRt", 0.0), getattr(m, "ThI", 0.0)))
        elif tip == "BAT":
            if int(getattr(m, "Inst", 0)) == 0:
                d["bat"].append((t, m.Volt, m.Curr, getattr(m, "CurrTot", 0.0), getattr(m, "VoltR", m.Volt), getattr(m, "Res", 0.0)))
        elif tip == "VIBE":
            d["vibe"].append((t, int(getattr(m, "IMU", 0)), m.VibeX, m.VibeY, m.VibeZ, int(getattr(m, "Clip", 0))))
        elif tip == "RCOU":
            d["rcou"].append((t,) + tuple(int(getattr(m, f"C{i}", 0)) for i in range(1, 15)))
        elif tip == "RCIN":
            d["rcin"].append((t, int(getattr(m, "C3", 0)), int(getattr(m, "C1", 0)), int(getattr(m, "C2", 0)), int(getattr(m, "C4", 0))))
        elif tip == "ATT":
            d["att"].append((t, m.Roll, m.Pitch, getattr(m, "DesRoll", 0.0), getattr(m, "DesPitch", 0.0), m.Yaw, getattr(m, "DesYaw", 0.0)))
        elif tip == "RATE":
            d["rate"].append((t, m.RDes, m.R, m.PDes, m.P, m.YDes, m.Y))
        elif tip == "IMU":
            if int(getattr(m, "I", 0)) == 0:
                d["imu0"].append((t, m.AccX, m.AccY, m.AccZ, m.GyrX, m.GyrY, m.GyrZ))
        elif tip == "XKF4":
            d["xkf4"].append((t, int(getattr(m, "C", 0)), m.SV, m.SP, m.SH, m.SM, getattr(m, "errRP", 0.0)))
        elif tip == "MOTB":
            d["motb"].append((t, getattr(m, "ThrOut", 0.0), getattr(m, "ThrAvMx", 0.0), getattr(m, "LiftMax", 1.0), int(getattr(m, "FailFlags", 0))))
        elif tip == "PSCD":
            d["pscd"].append((t, m.DVD, m.VD, m.TVD))
        elif tip == "PARM":
            ad, v = m.Name, UBA._f32(m.Value)
            if ad in parm and parm[ad] != v and not ad.startswith("STAT_"):
                parm_degisim.append({"t": _r(t, 1), "ad": ad, "eski": parm[ad], "yeni": v})
            elif ad not in parm:
                parm_ilk[ad] = v
            parm[ad] = v
        elif tip == "MODE":
            d["mode"].append((t, int(getattr(m, "ModeNum", getattr(m, "Mode", -1))), int(getattr(m, "Rsn", 0))))
        elif tip == "EV":
            d["ev"].append((t, int(m.Id)))
        elif tip == "ERR":
            d["err"].append((t, int(m.Subsys), int(m.ECode)))
        elif tip == "MSG":
            d["msg"].append((t, str(m.Message)))
    out = {k: np.array(v, float) for k, v in d.items() if k not in ("msg", "mode", "ev", "err")}
    out["msg"] = d["msg"]; out["mode"] = d["mode"]; out["ev"] = d["ev"]; out["err"] = d["err"]
    out["parm"] = parm; out["parm_ilk"] = parm_ilk; out["parm_degisim"] = parm_degisim
    return out


def parm_anda(ham, ad, t):
    """Parametrenin t anindaki degeri: ilk PARM dokumu + t'ye kadar kaydedilmis degisimler."""
    v = ham["parm_ilk"].get(ad, ham["parm"].get(ad))
    for x in ham["parm_degisim"]:
        if x["ad"] == ad and x["t"] is not None and x["t"] <= t:
            v = x["yeni"]
    return v


def _dilim(a, t0, t1):
    if a is None or len(a) == 0:
        return a[:0] if a is not None else np.zeros((0, 2))
    m = (a[:, 0] >= t0) & (a[:, 0] <= t1)
    return a[m]


def _en_yakin(a_t, t, tol=0.2):
    """a_t sirali zaman dizisinde t'ye en yakin indeks (tol icinde), yoksa -1."""
    if len(a_t) == 0:
        return np.full(len(t), -1)
    idx = np.clip(np.searchsorted(a_t, t), 0, len(a_t) - 1)
    idx2 = np.clip(idx - 1, 0, len(a_t) - 1)
    sec = np.where(np.abs(a_t[idx2] - t) < np.abs(a_t[idx] - t), idx2, idx)
    return np.where(np.abs(a_t[sec] - t) <= tol, sec, -1)


def kip_dizisi(mode, t):
    """her t icin gecerli kip numarasi (son MODE mesaji)."""
    if not mode:
        return np.full(len(t), -1)
    mt = np.array([m[0] for m in mode]); mn = np.array([m[1] for m in mode])
    idx = np.searchsorted(mt, t, side="right") - 1
    return np.where(idx >= 0, mn[np.clip(idx, 0, len(mn) - 1)], -1)


# ----------------------------------------------------------------------------- ucus analizi
def ucus_analiz(ham, u, L):
    """u: ortak aractaki ucus kaydi (pencere/tur). Derin olcumler + grafik verisi."""
    t0, t1 = u["arm_t"], u["disarm_t"]
    tm0, tm1 = u.get("motorlu_t") or [None, None]
    span = (tm0, tm1) if tm0 is not None else (t0, t1)
    c = _dilim(ham["ctun"], t0, t1)
    r = {"no": u["no"], "tur": u["tur"], "arm_t": t0, "disarm_t": t1, "motorlu_s": u.get("motorlu_s"),
         "kip_arm": u.get("kip_arm"), "kip_gecisleri": u.get("kip_gecisleri"), "failsafe": u.get("failsafe"),
         "inis": u.get("inis"), "pencere_kaynak": u.get("pencere_kaynak"), "notlar": list(u.get("notlar") or [])}
    if len(c) == 0:
        r["notlar"].append("CTUN yok"); return r
    ct, tho, thh, alt, crt = c[:, 0], c[:, 1], c[:, 2], c[:, 3], c[:, 4]
    taban = u.get("alt_taban_m") or float(np.median(alt[ct <= t0 + UBA.ALT_TABAN_S])) if (ct <= t0 + 1).any() else alt[0]
    alt_rel = alt - taban
    am = UBA.aski_maskesi(ct, alt_rel, tho)
    mot = tho > UBA.MOTORLU_THO_ESIK
    dt_med = float(np.median(np.diff(ct))) if len(ct) > 1 else 0.1
    r["alt_maks_m"] = _r(alt_rel.max(), 2)
    r["ThO_maks"] = _r(tho.max())
    r["ThO_motorlu_ort"] = _r(tho[mot].mean()) if mot.any() else None
    r["aski_n"] = int(am.sum()); r["aski_s"] = _r(am.sum() * dt_med, 1)
    # --- ThH (MOT_THST_HOVER canli degeri) izi
    thh_d = np.diff(thh)
    r["ThH"] = {"bas": _r(thh[0], 4), "son": _r(thh[-1], 4), "min": _r(thh.min(), 4), "maks": _r(thh.max(), 4),
                "degisen_ornek_n": int((np.abs(thh_d) > 1e-6).sum()), "ctun_n": int(len(ct))}
    # ogrenme kosullari (Copter::update_throttle_hover): kip manuel gaz degil, |vz|<60 cm/s, |roll|,|pitch|<5 deg,
    # pos_control vel_desired.z == 0 (PSCD.DVD), armli & yerde degil (NOT_LANDED sonrasi kabul: motorlu maske)
    kip = kip_dizisi(ham["mode"], ct)
    at = ham.get("att"); at_i = _en_yakin(at[:, 0], ct) if at is not None and len(at) else np.full(len(ct), -1)
    tilt_ok = np.zeros(len(ct), bool)
    if (at_i >= 0).any():
        tilt_ok[at_i >= 0] = (np.abs(at[at_i[at_i >= 0], 1]) < OGRENME_TILT_DEG) & (np.abs(at[at_i[at_i >= 0], 2]) < OGRENME_TILT_DEG)
    ps = ham.get("pscd"); ps_i = _en_yakin(ps[:, 0], ct, 0.15) if ps is not None and len(ps) else np.full(len(ct), -1)
    dvd0 = np.zeros(len(ct), bool); dvd_var = (ps_i >= 0)
    if dvd_var.any():
        # is_zero(vel_desired.z [cm/s]) : |v| < FLT_EPSILON (1,19e-7 cm/s) -> PSCD.DVD [m/s] < 1,19e-9
        dvd0[dvd_var] = np.abs(ps[ps_i[dvd_var], 1]) < DVD_SIFIR_ESIK_MS
    kip_ok = ~np.isin(kip, list(MANUEL_GAZ_KIPLERI))
    vz_ok = np.abs(crt) < OGRENME_VZ_CMS
    ogr = mot & kip_ok & vz_ok & tilt_ok & dvd0
    r["ogrenme"] = {"motorlu_n": int(mot.sum()), "kip_uygun_n": int((mot & kip_ok).sum()), "vz_uygun_n": int((mot & kip_ok & vz_ok).sum()),
                    "tilt_uygun_n": int((mot & kip_ok & vz_ok & tilt_ok).sum()), "PSCD_var": bool(dvd_var.any()),
                    "DVD_sifir_n": int((mot & kip_ok & dvd0).sum()), "tum_kosul_n": int(ogr.sum()), "tum_kosul_s": _r(ogr.sum() * dt_med, 1),
                    "aski_ve_kosul_n": int((am & ogr).sum())}
    # ogrenme benzetimi: ThH_sim += dt/(dt+TC) * (ThO - ThH_sim), kosul saglanan orneklerde (10 Hz CTUN; gercek 100 Hz)
    sim = float(thh[0]); dt_s = dt_med
    for k in range(len(ct)):
        if ogr[k]:
            sim += (dt_s / (dt_s + OGRENME_TC_S)) * (float(tho[k]) - sim)
    r["ogrenme"]["ThH_benzetim_son"] = _r(sim, 4)
    r["ogrenme"]["ThH_gercek_son"] = _r(thh[-1], 4)
    r["ogrenme"]["not"] = ("benzetim CTUN 10 Hz uzerinden (gercek 100 Hz); kosul: kip manuel-gaz degil, |CRt|<60 cm/s, "
                          "|roll|,|pitch|<5 deg, PSCD.DVD==0")
    # --- aski istatistigi
    if am.sum() >= UBA.ASKI_EN_AZ_ORNEK:
        r["aski"] = {"ThO_ort": _r(tho[am].mean()), "ThO_p50": _r(np.median(tho[am])), "ThO_p05": _r(_p(tho[am], 5)),
                     "ThO_p95": _r(_p(tho[am], 95)), "ThO_std": _r(tho[am].std()), "alt_ort_m": _r(alt_rel[am].mean(), 2),
                     "alt_min_m": _r(alt_rel[am].min(), 2), "alt_maks_m": _r(alt_rel[am].max(), 2)}
        kosu = UBA.en_uzun_kosu(am)
        r["aski"]["en_uzun_dilim_t"] = [_r(ct[kosu[0]], 1), _r(ct[kosu[1]], 1)]
        r["aski"]["en_uzun_dilim_s"] = _r(ct[kosu[1]] - ct[kosu[0]], 1)
        kips = kip[am]
        r["aski"]["kip_dagilimi"] = {UBA.MODE_AD.get(int(k), str(k)): int((kips == k).sum()) for k in sorted(set(kips.astype(int)))}
    else:
        r["aski"] = None
    aski_t = ct[am]
    # --- BAT
    b = _dilim(ham["bat"], t0, t1)
    if len(b):
        bt, v, i, ctot, vr, res = b.T
        sm = (bt >= span[0]) & (bt <= span[1])
        i_s, v_s, vr_s, res_s = (i[sm], v[sm], vr[sm], res[sm]) if sm.any() else (i, v, vr, res)
        imin = int(np.argmin(v))
        bat = {"V_bas": _r(v[0], 2), "V_bas_hucre": _r(v[0] / HUCRE_N, 3), "V_min": _r(v.min(), 2), "V_min_hucre": _r(v.min() / HUCRE_N, 3),
               "V_min_t": _r(bt[imin], 1), "I_Vmin_aninda": _r(i[imin], 1), "V_son": _r(v[-1], 2),
               "V_ort_motorlu": _r(v_s.mean(), 2), "VoltR_min": _r(vr.min(), 2),
               "sarkma_V": _r(v[0] - v.min(), 2), "sarkma_hucre_V": _r((v[0] - v.min()) / HUCRE_N, 3),
               "I_ort": _r(i_s.mean(), 1), "I_p95": _r(_p(i_s, 95), 1), "I_maks": _r(i_s.max(), 1),
               "mAh_pencere": _r(ctot[-1] - ctot[0], 0), "Res_FC_medyan_ohm": _r(np.median(res_s[res_s > 0]), 4) if (res_s > 0).any() else None}
        # ic direnc: motorlu orneklerde V = V0 - R*I dogrusal uydurma (numpy polyfit)
        if sm.sum() >= 20 and (i_s.max() - i_s.min()) > 5:
            egim, kesim = np.polyfit(i_s, v_s, 1)
            bat["R_uydurma_ohm"] = _r(-egim, 4); bat["V0_uydurma"] = _r(kesim, 2)
            bat["R_uydurma_n"] = int(sm.sum()); bat["R_uydurma_I_aralik"] = [_r(i_s.min(), 1), _r(i_s.max(), 1)]
        if len(aski_t):
            va, ia, vra = np.interp(aski_t, bt, v), np.interp(aski_t, bt, i), np.interp(aski_t, bt, vr)
            bat["aski"] = {"V_ort": _r(va.mean(), 2), "V_hucre_ort": _r(va.mean() / HUCRE_N, 3), "V_min": _r(va.min(), 2),
                           "VoltR_ort": _r(vra.mean(), 2), "I_ort": _r(ia.mean(), 1), "I_p50": _r(np.median(ia), 1),
                           "I_p95": _r(_p(ia, 95), 1), "P_W_ort": _r((va * ia).mean(), 1), "P_W_p50": _r(np.median(va * ia), 1),
                           "sarkma_hucre_V_askida": _r((v[0] - va.mean()) / HUCRE_N, 3),
                           "Wh_per_dk_HESAP": _r((va * ia).mean() / 60.0, 2)}
        # pil failsafe aninda gecerli esik (PARM ilk dokum + kayitli degisimler) ve V<esik ilk ani
        for f in (u.get("failsafe") or []):
            if f["tip"] == "MODE" and "PIL_FS" in f["aciklama"]:
                esik = parm_anda(ham, "BATT_LOW_VOLT", f["t"]); crt = parm_anda(ham, "BATT_CRT_VOLT", f["t"])
                alt10 = bt[v < 10.0]; alt_e = bt[v < esik] if esik else bt[:0]
                bat["pil_fs"] = {"t": f["t"], "BATT_LOW_VOLT_o_anda": esik, "BATT_CRT_VOLT_o_anda": crt, "BATT_LOW_TIMER": ham["parm"].get("BATT_LOW_TIMER"),
                                 "V_fs_aninda": _r(np.interp(f["t"], bt, v), 2), "V_ilk_10V_alti_t": _r(alt10[0], 1) if len(alt10) else None,
                                 "V_ilk_esik_alti_t": _r(alt_e[0], 1) if len(alt_e) else None,
                                 "msg": [s for t_, s in ham["msg"] if abs(t_ - f["t"]) < 0.5 and "Battery" in s]}
                break
        r["bat"] = bat
    else:
        r["bat"] = None
    # --- VIBE (IMU 0 ve 1 ayri; motorlu ve aski)
    vb = _dilim(ham["vibe"], t0, t1)
    vibe = {}
    if len(vb):
        for inst in sorted(set(vb[:, 1].astype(int))):
            s = vb[vb[:, 1] == inst]
            sm = (s[:, 0] >= span[0]) & (s[:, 0] <= span[1])
            g = {"clip_artisi": int(s[-1, 5] - s[0, 5])}
            if sm.any():
                for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
                    x = s[sm, kol]
                    g[f"{ad}_motorlu"] = {"ort": _r(x.mean(), 1), "p95": _r(_p(x, 95), 1), "maks": _r(x.max(), 1)}
            if len(aski_t):
                ai = _en_yakin(s[:, 0], aski_t, 0.11); ai = ai[ai >= 0]
                if len(ai):
                    for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
                        x = s[ai, kol]
                        g[f"{ad}_aski"] = {"ort": _r(x.mean(), 1), "p95": _r(_p(x, 95), 1), "maks": _r(x.max(), 1)}
            g["pencere_maks"] = {ad: _r(s[:, kol].max(), 1) for ad, kol in (("X", 2), ("Y", 3), ("Z", 4))}
            vibe[f"IMU{inst}"] = g
        vibe["clip_toplam"] = int(sum(v["clip_artisi"] for k, v in vibe.items() if k.startswith("IMU")))
    r["vibe"] = vibe or None
    # --- RCOU motorlar (C9..C12) — aski (yoksa motorlu)
    rc = ham["rcou"]
    if len(rc):
        if len(aski_t):
            idx = _en_yakin(rc[:, 0], aski_t, 0.2); idx = idx[idx >= 0]; kapsam = "aski"
        else:
            idx = np.where((rc[:, 0] >= span[0]) & (rc[:, 0] <= span[1]))[0]; kapsam = "motorlu" if tm0 is not None else "pencere"
        if len(idx):
            pmin, pmaks = ham["parm"].get("MOT_PWM_MIN", 1000.0), ham["parm"].get("MOT_PWM_MAX", 2000.0)
            ar = max(pmaks - pmin, 1.0)
            mot_pwm = {m: float(rc[idx, int(k[1:])].mean()) for m, k in MOTOR_KANAL.items()}
            mot_std = {m: float(rc[idx, int(k[1:])].std()) for m, k in MOTOR_KANAL.items()}
            on, arka = (mot_pwm["M1"] + mot_pwm["M3"]) / 2, (mot_pwm["M2"] + mot_pwm["M4"]) / 2
            sag, sol = (mot_pwm["M1"] + mot_pwm["M4"]) / 2, (mot_pwm["M2"] + mot_pwm["M3"]) / 2
            ccw, cw = (mot_pwm["M1"] + mot_pwm["M2"]) / 2, (mot_pwm["M3"] + mot_pwm["M4"]) / 2
            r["rcou"] = {"kapsam": kapsam, "n": int(len(idx)), "kanal": MOTOR_KANAL,
                         "M1_M4_ort": {m: round(x) for m, x in mot_pwm.items()}, "M1_M4_std": {m: round(x, 1) for m, x in mot_std.items()},
                         "yayilim_pwm": round(max(mot_pwm.values()) - min(mot_pwm.values())),
                         "yayilim_pct_aralik": _r((max(mot_pwm.values()) - min(mot_pwm.values())) / ar * 100, 1),
                         "en_yuksek": max(mot_pwm, key=mot_pwm.get), "en_dusuk": min(mot_pwm, key=mot_pwm.get),
                         "on_eksi_arka_pwm": round(on - arka), "sag_eksi_sol_pwm": round(sag - sol), "ccw_eksi_cw_pwm": round(ccw - cw),
                         "ort_pwm_orani": _r((np.mean(list(mot_pwm.values())) - pmin) / ar),
                         "C1_C4_ortak_arac": [round(float(rc[idx, j].mean())) for j in (1, 2, 3, 4)]}
        else:
            r["rcou"] = None
    # --- ATT / RATE (aski ve motorlu)
    at = ham.get("att")
    if at is not None and len(at):
        sm = (at[:, 0] >= span[0]) & (at[:, 0] <= span[1])
        if sm.any():
            rr, pp, dr, dp = at[sm, 1], at[sm, 2], at[sm, 3], at[sm, 4]
            r["att"] = {"motorlu": {"roll_rms_hata_deg": _r(np.sqrt(np.mean((rr - dr) ** 2)), 2), "pitch_rms_hata_deg": _r(np.sqrt(np.mean((pp - dp) ** 2)), 2),
                                    "roll_maks_abs_deg": _r(np.abs(rr).max(), 1), "pitch_maks_abs_deg": _r(np.abs(pp).max(), 1),
                                    "roll_ort_deg": _r(rr.mean(), 2), "pitch_ort_deg": _r(pp.mean(), 2), "n": int(sm.sum())}}
            if len(aski_t):
                ai = _en_yakin(at[:, 0], aski_t, 0.11); ai = ai[ai >= 0]
                if len(ai):
                    ra, pa = at[ai, 1] - at[ai, 3], at[ai, 2] - at[ai, 4]
                    r["att"]["aski"] = {"roll_rms_hata_deg": _r(np.sqrt(np.mean(ra ** 2)), 2), "pitch_rms_hata_deg": _r(np.sqrt(np.mean(pa ** 2)), 2),
                                        "roll_ort_deg": _r(at[ai, 1].mean(), 2), "pitch_ort_deg": _r(at[ai, 2].mean(), 2),
                                        "desroll_ort_deg": _r(at[ai, 3].mean(), 2), "despitch_ort_deg": _r(at[ai, 4].mean(), 2), "n": int(len(ai))}
    ra = ham.get("rate")
    if ra is not None and len(ra) and len(aski_t):
        ai = _en_yakin(ra[:, 0], aski_t, 0.11); ai = ai[ai >= 0]
        if len(ai):
            r["rate_aski"] = {"roll_rms_hata_dps": _r(np.sqrt(np.mean((ra[ai, 1] - ra[ai, 2]) ** 2)), 2),
                              "pitch_rms_hata_dps": _r(np.sqrt(np.mean((ra[ai, 3] - ra[ai, 4]) ** 2)), 2),
                              "yaw_rms_hata_dps": _r(np.sqrt(np.mean((ra[ai, 5] - ra[ai, 6]) ** 2)), 2),
                              "yaw_rate_ort_dps": _r(ra[ai, 6].mean(), 2), "yaw_des_rate_ort_dps": _r(ra[ai, 5].mean(), 2), "n": int(len(ai))}
    if at is not None and len(at) and len(aski_t):
        ai = _en_yakin(at[:, 0], aski_t, 0.11); ai = ai[ai >= 0]
        if len(ai) > 1:
            yaw_err = (at[ai, 5] - at[ai, 6] + 180.0) % 360.0 - 180.0
            r.setdefault("att", {})["aski_yaw"] = {"yaw_hata_rms_deg": _r(np.sqrt(np.mean(yaw_err ** 2)), 2), "yaw_hata_ort_deg": _r(yaw_err.mean(), 2)}
    # --- EKF
    ek = _dilim(ham["xkf4"], t0, t1) if "xkf4" in ham else np.zeros((0, 7))
    e = {"cekirdek": {}}
    for cc in sorted(set(ek[:, 1].astype(int))) if len(ek) else []:
        s = ek[ek[:, 1] == cc]
        e["cekirdek"][str(cc)] = {"SV_maks": _r(s[:, 2].max(), 2), "SP_maks": _r(s[:, 3].max(), 2), "SH_maks": _r(s[:, 4].max(), 2),
                                  "SM_maks": _r(s[:, 5].max(), 2), "errRP_maks": _r(s[:, 6].max(), 3),
                                  "innov_dusen_n": int(((s[:, 2:6] > UBA.EKF_INNOV_ESIK).any(axis=1)).sum()), "n": int(len(s))}
    e["lane_switch"] = (u.get("ekf") or {}).get("lane_switch") or []
    e["err"] = (u.get("ekf") or {}).get("err") or []
    e["yaw_reset_n"] = sum(1 for x in e["err"] if x.get("aciklama") == "EKF_YAW_RESET")
    r["ekf"] = e
    # --- MOTB
    mb = _dilim(ham["motb"], span[0], span[1]) if "motb" in ham else np.zeros((0, 5))
    if len(mb):
        r["motb"] = {"ThrAvMx_ort": _r(mb[:, 2].mean()), "ThrAvMx_min": _r(mb[:, 2].min()), "LiftMax_ort": _r(mb[:, 3].mean()),
                     "ThrOut_maks": _r(mb[:, 1].max()), "FailFlags_sifirdisi_n": int((mb[:, 4] != 0).sum()), "n": int(len(mb))}
    # --- RCIN gaz cubugu askida (LOIT/GUID'de istenen tirmanma hizi -> ogrenme kosulu)
    ri = ham.get("rcin")
    if ri is not None and len(ri) and len(aski_t):
        ai = _en_yakin(ri[:, 0], aski_t, 0.11); ai = ai[ai >= 0]
        if len(ai):
            r["rcin_aski"] = {"gaz_pwm_ort": round(float(ri[ai, 1].mean())), "gaz_pwm_p05": round(_p(ri[ai, 1], 5)), "gaz_pwm_p95": round(_p(ri[ai, 1], 95)),
                              "gaz_olu_bant_disi_orani": _r(float(np.mean(np.abs(ri[ai, 1] - 1500) > ham["parm"].get("THR_DZ", 100))), 2)}
    # --- IMU FFT (25 Hz IMU; Nyquist 12,5 Hz — pervane frekansi COZULEMEZ)
    r["imu_fft"] = None
    im = ham.get("imu0")
    if im is not None and len(im) and r.get("aski"):
        ta, tb = r["aski"]["en_uzun_dilim_t"]
        s = _dilim(im, ta, tb)
        if len(s) >= UBA.FFT_EN_AZ_ORNEK:
            fz = UBA.imu_fft(s[:, 0], s[:, 3]); fx = UBA.imu_fft(s[:, 0], s[:, 1]); fy = UBA.imu_fft(s[:, 0], s[:, 2])
            gz = UBA.imu_fft(s[:, 0], np.degrees(s[:, 6]))
            if fz:
                r["imu_fft"] = {"dilim_t": [ta, tb], "fs_hz": fz["fs_hz"], "nyquist_hz": fz["nyquist_hz"], "n": fz["n"],
                                "AccZ": {"rms_ms2": fz["rms_ms2"], "tepeler": fz["tepeler"]},
                                "AccX": {"rms_ms2": fx["rms_ms2"], "tepeler": fx["tepeler"][:3]} if fx else None,
                                "AccY": {"rms_ms2": fy["rms_ms2"], "tepeler": fy["tepeler"][:3]} if fy else None,
                                "GyrZ_dps": {"rms": gz["rms_ms2"], "tepeler": gz["tepeler"][:3]} if gz else None,
                                "not": "IMU mesaji 25 Hz (LOG_BITMASK IMU_RAW yok, INS_LOG_BAT_MASK=0): Nyquist 12,5 Hz; pervane temel "
                                       "frekansi (~100-160 Hz) ve harmonikleri COZULEMEZ, INS_ACCEL_FILTER=20 Hz sonrasi ornek. "
                                       "Tepeler govde/kontrol bandidir; 10-12,5 Hz tepeler katlanma (alias) olabilir."}
                # grafik icin spektrum sakla
                n = len(s); w = np.hanning(n); dt = float(np.median(np.diff(s[:, 0])))
                X = np.fft.rfft((s[:, 3] - s[:, 3].mean()) * w); f = np.fft.rfftfreq(n, dt)
                r["_spektrum"] = (f, 2.0 * np.abs(X) / w.sum())
    # --- grafik verisi (ham diziler)
    r["_g"] = {"ct": ct, "tho": tho, "thh": thh, "alt_rel": alt_rel, "am": am, "bat": b, "vibe": vb, "rcou": rc[(rc[:, 0] >= t0) & (rc[:, 0] <= t1)] if len(rc) else rc}
    return r


# ----------------------------------------------------------------------------- grafikler
def grafik_zaman(stem, ucuslar, olaylar_fs, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(5, 1, figsize=(13, 13), sharex=True, facecolor=RENK["yuzey"])
    for a in ax:
        a.set_facecolor(RENK["yuzey"]); a.grid(True, color=RENK["izgara"], lw=0.6); a.tick_params(colors=RENK["ikincil"], labelsize=8)
        for sp in a.spines.values():
            sp.set_color(RENK["izgara"])
    for u in ucuslar:
        g = u.get("_g")
        if not g:
            continue
        ct = g["ct"]; t0 = ct[0]
        ax[0].plot(ct, g["tho"], color=RENK["mavi"], lw=1.0, label="CTUN.ThO (gaz cikisi)" if u is ucuslar[0] else None)
        ax[0].plot(ct, g["thh"], color=RENK["turuncu"], lw=1.6, label="CTUN.ThH (MOT_THST_HOVER canli)" if u is ucuslar[0] else None)
        if g["am"].any():
            ax[0].fill_between(ct, 0, 1, where=g["am"], color=RENK["aqua"], alpha=0.18, transform=ax[0].get_xaxis_transform(),
                               label="aski orneklemi" if u is ucuslar[0] else None)
        ax[0].text(t0, 0.93, f"#{u['no']} {u['tur']}", fontsize=8, color=RENK["ikincil"], va="top")
        b = g["bat"]
        if len(b):
            ax[1].plot(b[:, 0], b[:, 2], color=RENK["mavi"], lw=1.0, label="BAT.Curr (A)" if u is ucuslar[0] else None)
            ax[2].plot(b[:, 0], b[:, 1], color=RENK["mavi"], lw=1.0, label="BAT.Volt (V)" if u is ucuslar[0] else None)
            ax[2].plot(b[:, 0], b[:, 4], color=RENK["turuncu"], lw=1.0, ls="--", label="BAT.VoltR (sarkma duzeltmeli)" if u is ucuslar[0] else None)
        vb = g["vibe"]; vb0 = vb[vb[:, 1] == 0] if len(vb) else vb
        if len(vb0):
            for ad, kol, rn in (("VibeX", 2, "mavi"), ("VibeY", 3, "turuncu"), ("VibeZ", 4, "aqua")):
                ax[3].plot(vb0[:, 0], vb0[:, kol], color=RENK[rn], lw=1.0, label=f"{ad} (IMU0, m/s²)" if u is ucuslar[0] else None)
        rc = g["rcou"]
        if len(rc):
            for m, k, rn in (("M1 on-sag CCW", "C11", "mavi"), ("M2 arka-sol CCW", "C10", "turuncu"), ("M3 on-sol CW", "C12", "aqua"), ("M4 arka-sag CW", "C9", "sari")):
                ax[4].plot(rc[:, 0], rc[:, int(k[1:])], color=RENK[rn], lw=1.0, label=f"{m} (RCOU.{k})" if u is ucuslar[0] else None)
    for t, ad in olaylar_fs:
        for a in ax:
            a.axvline(t, color=RENK["kritik"], lw=0.9, ls=":")
        ax[0].text(t, 0.05, ad, rotation=90, fontsize=7, color=RENK["kritik"], va="bottom", ha="right")
    ax[0].set_ylim(0, 1); ax[0].set_ylabel("gaz (0-1)"); ax[1].set_ylabel("akim (A)"); ax[2].set_ylabel("gerilim (V)")
    ax[3].set_ylabel("VIBE (m/s²)"); ax[4].set_ylabel("motor PWM (µs)"); ax[4].set_xlabel("log zamani (s)")
    for a in ax:
        a.legend(loc="upper right", fontsize=7, frameon=True, framealpha=0.85, facecolor=RENK["yuzey"], edgecolor=RENK["izgara"])
    ax[0].set_title(f"Konfig A (3S+1045, kullanici beyani) — {stem}: gaz/ThH, akim, gerilim, VIBE, motor PWM", fontsize=10, color=RENK["metin"])
    t_all = [u["_g"]["ct"] for u in ucuslar if u.get("_g") is not None and len(u["_g"]["ct"])]
    if t_all:
        ax[0].set_xlim(min(t[0] for t in t_all) - 5, max(t[-1] for t in t_all) + 5)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


def _stil(ax):
    ax.set_facecolor(RENK["yuzey"]); ax.grid(True, color=RENK["izgara"], lw=0.6); ax.tick_params(colors=RENK["ikincil"], labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(RENK["izgara"])


def grafik_ozet(ucuslar, yol):
    """kronolojik ucus sirasina gore: aski ThO (p05-p95), ThH sonu, aski akimi, aski gucu, VibeZ aski ort."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    U = [u for u in ucuslar if u.get("aski")]
    x = np.arange(len(U)); lab = [u["etiket_kisa"] for u in U]
    fig, ax = plt.subplots(4, 1, figsize=(13, 12), sharex=True, facecolor=RENK["yuzey"])
    for a in ax:
        _stil(a)
    tho = np.array([u["aski"]["ThO_p50"] for u in U]); lo = np.array([u["aski"]["ThO_p05"] for u in U]); hi = np.array([u["aski"]["ThO_p95"] for u in U])
    ax[0].errorbar(x, tho, yerr=[tho - lo, hi - tho], fmt="o", color=RENK["mavi"], ecolor=RENK["mavi"], capsize=3, ms=6, label="aski ThO p50 (p05-p95)")
    ax[0].plot(x, [u["ThH"]["son"] for u in U], "s", color=RENK["turuncu"], ms=6, label="ThH ucus sonu (MOT_THST_HOVER)")
    ax[0].plot(x, [u["ThH"]["bas"] for u in U], "s", mfc="none", color=RENK["turuncu"], ms=6, label="ThH ucus basi")
    ax[0].set_ylabel("gaz (0-1)"); ax[0].legend(fontsize=8, frameon=False, loc="upper left")
    ax[1].bar(x, [u["bat"]["aski"]["I_ort"] for u in U], color=RENK["mavi"], width=0.6, label="aski akimi ort (A)")
    ax[1].set_ylabel("akim (A)"); ax[1].legend(fontsize=8, frameon=False, loc="upper left")
    ax[2].bar(x, [u["bat"]["aski"]["P_W_ort"] for u in U], color=RENK["turuncu"], width=0.6, label="aski gucu V×I ort (W)")
    ax[2].set_ylabel("guc (W)"); ax[2].legend(fontsize=8, frameon=False, loc="upper left")
    vz = [((u.get("vibe") or {}).get("IMU0") or {}).get("Z_aski", {}).get("ort") or 0 for u in U]
    vx = [((u.get("vibe") or {}).get("IMU0") or {}).get("X_aski", {}).get("ort") or 0 for u in U]
    vy = [((u.get("vibe") or {}).get("IMU0") or {}).get("Y_aski", {}).get("ort") or 0 for u in U]
    ax[3].bar(x - 0.25, vx, width=0.24, color=RENK["mavi"], label="VibeX aski ort")
    ax[3].bar(x, vy, width=0.24, color=RENK["turuncu"], label="VibeY aski ort")
    ax[3].bar(x + 0.25, vz, width=0.24, color=RENK["aqua"], label="VibeZ aski ort")
    ax[3].axhline(30, color=RENK["kritik"], lw=0.8, ls=":"); ax[3].text(-0.4, 30.6, "30 m/s² (AP kilavuz esigi)", fontsize=7, color=RENK["kritik"], ha="left")
    ax[3].set_ylabel("VIBE (m/s²)"); ax[3].legend(fontsize=8, frameon=False, loc="upper left")
    ax[3].set_xticks(x); ax[3].set_xticklabels(lab, rotation=60, ha="right", fontsize=7)
    ax[0].set_title("Konfig A (3S+1045) — askidaki ucuslar, kronolojik (STAT_BOOTCNT sirasi)", fontsize=10)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


def grafik_thh(tum, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    L = [l for l in tum["loglar"] if "KOPYA_OF" not in l and "HATA" not in l and l["sira"].get("STAT_BOOTCNT") is not None]
    L.sort(key=lambda l: (l["sira"]["STAT_BOOTCNT"], l["sira"].get("STAT_RUNTIME_ilk_s") or 0))
    fig, ax = plt.subplots(figsize=(13, 5), facecolor=RENK["yuzey"]); _stil(ax)
    x = np.arange(len(L))
    gorulen = set()
    for k, l in enumerate(L):
        et = l["kullanici_beyani"]["etiket"]; pil = f"{l['hucre']['n']}S"
        lab = f"{et or 'beyan yok'} ({UBA.KONFIG.get(et, {}).get('pil', '?')} {UBA.KONFIG.get(et, {}).get('pervane', '')})" if et else "beyan yok"
        ax.plot(k, l["parm"]["MOT_THST_HOVER"], "o", color=KONFIG_RENK.get(et), ms=8, label=lab if lab not in gorulen else None)
        gorulen.add(lab)
        ax.text(k, l["parm"]["MOT_THST_HOVER"] + 0.008, f"{pil}\nucus {l['ozet']['ucus_n']}", fontsize=6.5, ha="center", color=RENK["ikincil"])
    ax.plot(x, [l["parm"]["MOT_THST_HOVER"] for l in L], "-", color=RENK["gri"], lw=0.8, zorder=0)
    ax.axhline(0.35, color=RENK["gri"], lw=0.8, ls="--"); ax.text(0, 0.352, "0,35 fabrika varsayilani", fontsize=7, color=RENK["ikincil"])
    ax.set_xticks(x); ax.set_xticklabels([f"{int(l['sira']['STAT_BOOTCNT'])} · {Path(l['dosya']).stem}" for l in L], rotation=70, ha="right", fontsize=7)
    ax.set_ylabel("MOT_THST_HOVER (log sonu PARM)"); ax.set_xlabel("STAT_BOOTCNT · log")
    ax.set_title("MOT_THST_HOVER gecmisi — 27 benzersiz log, BOOTCNT sirasi (renk = kullanici beyani konfig)", fontsize=10)
    ax.legend(fontsize=8, frameon=False, loc="upper left"); fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


def grafik_vibe(ucuslar, kisa, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.5), facecolor=RENK["yuzey"], sharey=True)
    havuz = {"ucus askida": defaultdict(list), "ucus motorlu": defaultdict(list), "kisa sicrama motorlu": defaultdict(list)}
    for u in ucuslar:
        g = u.get("_g")
        if not g or not len(g["vibe"]):
            continue
        vb = g["vibe"]; vb0 = vb[vb[:, 1] == 0]
        tm = u.get("_span")
        sm = (vb0[:, 0] >= tm[0]) & (vb0[:, 0] <= tm[1])
        for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
            havuz["ucus motorlu"][ad].extend(vb0[sm, kol].tolist())
        if g["am"].any():
            ai = _en_yakin(vb0[:, 0], g["ct"][g["am"]], 0.11); ai = ai[ai >= 0]
            for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
                havuz["ucus askida"][ad].extend(vb0[ai, kol].tolist())
    for u in kisa:
        g = u.get("_g")
        if not g or not len(g["vibe"]):
            continue
        vb = g["vibe"]; vb0 = vb[vb[:, 1] == 0]; tm = u.get("_span")
        sm = (vb0[:, 0] >= tm[0]) & (vb0[:, 0] <= tm[1])
        for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
            havuz["kisa sicrama motorlu"][ad].extend(vb0[sm, kol].tolist())
    for j, ad in enumerate(("X", "Y", "Z")):
        _stil(ax[j])
        veri = [np.array(havuz[k][ad]) for k in havuz]
        bp = ax[j].boxplot(veri, widths=0.5, patch_artist=True, showfliers=True, flierprops={"marker": ".", "ms": 3, "color": RENK["gri"]})
        for patch, rn in zip(bp["boxes"], ("mavi", "turuncu", "aqua")):
            patch.set_facecolor(RENK[rn]); patch.set_alpha(0.55); patch.set_edgecolor(RENK[rn])
        ax[j].set_xticks([1, 2, 3]); ax[j].set_xticklabels([f"{k}\n(n={len(havuz[k][ad])})" for k in havuz], fontsize=8)
        ax[j].axhline(30, color=RENK["kritik"], lw=0.8, ls=":")
        ax[j].set_title(f"Vibe{ad} (IMU0, m/s²)", fontsize=9)
    ax[0].set_ylabel("VIBE (m/s²)"); ax[0].text(0.55, 30.8, "30 m/s²", fontsize=7, color=RENK["kritik"])
    fig.suptitle("Konfig A — VIBE dagilimi: askida / ucus motorlu / kisa sicrama (yer temasi) AYRI", fontsize=10)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)
    return {k: {ad: {"n": len(v[ad]), "ort": _r(np.mean(v[ad]), 1) if v[ad] else None, "p50": _r(np.median(v[ad]), 1) if v[ad] else None,
                     "p95": _r(_p(np.array(v[ad]), 95), 1) if v[ad] else None, "maks": _r(np.max(v[ad]), 1) if v[ad] else None}
                for ad in ("X", "Y", "Z")} for k, v in havuz.items()}


def grafik_fft(ucuslar, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    U = [u for u in ucuslar if u.get("_spektrum") is not None]
    U.sort(key=lambda u: -(u["aski"]["en_uzun_dilim_s"] or 0)); U = U[:6]
    if not U:
        return []
    fig, ax = plt.subplots(2, 3, figsize=(13, 7), facecolor=RENK["yuzey"], sharex=True)
    ax = ax.ravel()
    for j, u in enumerate(U):
        _stil(ax[j]); f, g = u["_spektrum"]
        ax[j].plot(f, g, color=RENK["mavi"], lw=1.0)
        for tp in u["imu_fft"]["AccZ"]["tepeler"][:3]:
            ax[j].plot(tp["f_hz"], tp["genlik_ms2"], "o", color=RENK["turuncu"], ms=5)
            ax[j].text(tp["f_hz"], tp["genlik_ms2"], f" {tp['f_hz']} Hz", fontsize=7, color=RENK["ikincil"])
        ax[j].set_title(f"{u['etiket_kisa']} · aski {u['aski']['en_uzun_dilim_s']} s · ThO p50 {u['aski']['ThO_p50']}", fontsize=8)
        ax[j].set_xlim(0, u["imu_fft"]["nyquist_hz"])
    for j in range(len(U), 6):
        ax[j].axis("off")
    for j in (3, 4, 5):
        ax[j].set_xlabel("frekans (Hz)")
    ax[0].set_ylabel("AccZ genlik (m/s²)"); ax[3].set_ylabel("AccZ genlik (m/s²)")
    fig.suptitle("IMU0 AccZ FFT, en uzun aski dilimleri — IMU 25 Hz, Nyquist 12,5 Hz: pervane frekansi COZULEMEZ (govde/kontrol bandi)", fontsize=9)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)
    return [u["etiket_kisa"] for u in U]


def grafik_gerilim_akim(ucuslar, kisa, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 5), facecolor=RENK["yuzey"])
    for a in ax:
        _stil(a)
    grup = {"12 Eylul": RENK["mavi"], "13 Eylul erken": RENK["turuncu"], "13 Eylul gec (09-59-30 #4-6)": RENK["aqua"]}
    gor = set()
    for u in ucuslar:
        g = u.get("_g"); b = g["bat"] if g else None
        if b is None or not len(b):
            continue
        tm = u["_span"]; sm = (b[:, 0] >= tm[0]) & (b[:, 0] <= tm[1])
        rn = grup[u["grup"]]
        ax[0].plot(b[sm, 2], b[sm, 1], ".", color=rn, ms=3, alpha=0.5, label=u["grup"] if u["grup"] not in gor else None); gor.add(u["grup"])
    ax[0].set_xlabel("BAT.Curr (A)"); ax[0].set_ylabel("BAT.Volt (V)"); ax[0].set_title("ucuslar, motorlu ornekler: gerilim-akim (egim = ic direnc)", fontsize=9)
    ax[0].legend(fontsize=8, frameon=False)
    gor = set()
    for u in kisa:
        g = u.get("_g"); b = g["bat"] if g else None
        if b is None or not len(b):
            continue
        tm = u["_span"]; sm = (b[:, 0] >= tm[0]) & (b[:, 0] <= tm[1])
        ax[1].plot(b[sm, 2], b[sm, 1], ".", color=RENK["mor"], ms=3, alpha=0.5, label="kisa sicrama (motorlu)" if "k" not in gor else None); gor.add("k")
    ax[1].set_xlabel("BAT.Curr (A)"); ax[1].set_ylabel("BAT.Volt (V)"); ax[1].set_title("kisa sicramalar: 100+ A tepeler ve 6-8 V cokmeler (AYRI)", fontsize=9)
    ax[1].legend(fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


def grafik_motor(ucuslar, yol):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    U = [u for u in ucuslar if u.get("rcou") and u["rcou"]["kapsam"] == "aski"]
    if not U:
        return
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True, facecolor=RENK["yuzey"])
    for a in ax:
        _stil(a)
    x = np.arange(len(U))
    for j, (m, rn) in enumerate((("M1", "mavi"), ("M2", "turuncu"), ("M3", "aqua"), ("M4", "sari"))):
        ax[0].bar(x + (j - 1.5) * 0.2, [u["rcou"]["M1_M4_ort"][m] for u in U], width=0.19, color=RENK[rn], label=f"{m} {MOTOR_KONUM[m]} (RCOU.{MOTOR_KANAL[m]})")
    ax[0].set_ylim(min(min(u["rcou"]["M1_M4_ort"].values()) for u in U) - 40, max(max(u["rcou"]["M1_M4_ort"].values()) for u in U) + 40)
    ax[0].set_ylabel("aski ort PWM (µs)"); ax[0].legend(fontsize=8, frameon=False, ncol=2, loc="upper left")
    ax[1].plot(x, [u["rcou"]["on_eksi_arka_pwm"] for u in U], "o-", color=RENK["mavi"], label="on − arka (M1+M3 − M2−M4)/2")
    ax[1].plot(x, [u["rcou"]["sag_eksi_sol_pwm"] for u in U], "s-", color=RENK["turuncu"], label="sag − sol (M1+M4 − M2−M3)/2")
    ax[1].plot(x, [u["rcou"]["ccw_eksi_cw_pwm"] for u in U], "^-", color=RENK["aqua"], label="CCW − CW (M1+M2 − M3−M4)/2")
    ax[1].axhline(0, color=RENK["gri"], lw=0.8); ax[1].set_ylabel("PWM farki (µs)"); ax[1].legend(fontsize=8, frameon=False, loc="upper left")
    ax[1].set_xticks(x); ax[1].set_xticklabels([u["etiket_kisa"] for u in U], rotation=60, ha="right", fontsize=7)
    ax[0].set_title("Konfig A — motor dengesi askida (SERVO9-12 = M4,M2,M1,M3; ortak aracin C1-C4'u M2/M1 kopyasidir)", fontsize=10)
    fig.tight_layout(); fig.savefig(yol, dpi=120); plt.close(fig)


# ----------------------------------------------------------------------------- ana
def main():
    CIKTI_DIZIN.mkdir(parents=True, exist_ok=True)
    tum = json.loads(TUM_JSON.read_text(encoding="utf-8"))
    L_A = [l for l in tum["loglar"] if "KOPYA_OF" not in l and "HATA" not in l and
           (l["kullanici_beyani"]["etiket"] == ETIKET or (l["kullanici_beyani"]["etiket"] is None and l["hucre"]["n"] == HUCRE_N))]
    L_A.sort(key=lambda l: (l["sira"]["STAT_BOOTCNT"] or 0, l["sira"].get("STAT_RUNTIME_ilk_s") or 0))
    print(f"Konfig A log sayisi: {len(L_A)}")
    loglar_out, ucuslar, kisalar, arm_yalniz = [], [], [], []
    grafikler = []
    for l in L_A:
        yol = KOK / l["dosya"]
        boot = int(l["sira"]["STAT_BOOTCNT"]); stem = yol.stem
        beyan = dict(l["kullanici_beyani"])
        if beyan["etiket"] is None:
            beyan.update({"etiket": "A", "dayanak": f"STAT_BOOTCNT {boot} 12 Eylul loglari arasinda (75..95); 3S; ucus yok — A varsayildi (kullanici listesinde yok)",
                          "pil": "3S", "pervane": "10x4.5 (1045)", "hucre_uyum": True, "varsayim": True})
        kayit = {"dosya": l["dosya"], "sha256": l["sha256"][:16], "mp_no": l.get("mp_no"), "STAT_BOOTCNT": boot,
                 "STAT_RUNTIME_ilk_s": l["sira"].get("STAT_RUNTIME_ilk_s"), "log_suresi_s": l["log_suresi_s"], "hucre": l["hucre"],
                 "kullanici_beyani": beyan, "MOT_THST_HOVER_log_sonu": l["parm"]["MOT_THST_HOVER"], "MOT_HOVER_LEARN": l["parm"].get("MOT_HOVER_LEARN"),
                 "ozet_ortak_arac": l["ozet"], "parm_degisim": [x for x in l["parm_degisim"] if not x["ad"].startswith("BARO")]}
        if l["arm_pencere_n"] == 0:
            kayit["not"] = "arm penceresi yok — ucus/sicrama yok"
            loglar_out.append(kayit); print(f"  {stem}: pencere yok"); continue
        print(f"  {stem}: okunuyor ...", flush=True)
        ham = oku_genis(yol)
        p = ham["parm"]
        kayit["parm"] = {k: p.get(k) for k in ("MOT_THST_HOVER", "MOT_HOVER_LEARN", "MOT_THST_EXPO", "MOT_SPIN_MIN", "MOT_SPIN_ARM", "MOT_SPIN_MAX",
                                               "BATT_CAPACITY", "BATT_LOW_VOLT", "BATT_CRT_VOLT", "BATT_LOW_TIMER", "BATT_FS_VOLTSRC", "BATT_ARM_VOLT",
                                               "BATT_VOLT_MULT", "BATT_AMP_PERVLT", "BATT_AMP_OFFSET", "BATT_MONITOR", "INS_HNTCH_ENABLE",
                                               "INS_GYRO_FILTER", "INS_ACCEL_FILTER", "INS_LOG_BAT_MASK", "LOG_BITMASK", "FS_GCS_ENABLE",
                                               "FS_THR_ENABLE", "ATC_RAT_RLL_P", "ATC_RAT_RLL_D", "ATC_RAT_PIT_P", "ATC_RAT_PIT_D", "ATC_ANG_RLL_P",
                                               "THR_DZ", "PILOT_SPEED_UP", "FRAME_CLASS", "FRAME_TYPE")}
        kayit["servo_function"] = {f"SERVO{i}_FUNCTION": p.get(f"SERVO{i}_FUNCTION") for i in range(1, 17)}
        kayit["motor_haritasi_dogrulama"] = ({p.get(f"SERVO{i}_FUNCTION") for i in (9, 10, 11, 12)} == {33.0, 34.0, 35.0, 36.0})
        kayit["ucuslar"] = []
        fs_olay = []
        for u in l["ucuslar"]:
            r = ucus_analiz(ham, u, l)
            r["etiket_kisa"] = f"{stem[:10]} {stem[11:16]} #{u['no']}" if stem.startswith("2026") else f"{stem} #{u['no']}"
            r["log"] = l["dosya"]; r["STAT_BOOTCNT"] = boot
            r["_span"] = tuple(u.get("motorlu_t") or [u["arm_t"], u["disarm_t"]])
            if boot <= 95:
                r["grup"] = "12 Eylul"
            elif "09-59-30" in stem and u["no"] >= 4:
                r["grup"] = "13 Eylul gec (09-59-30 #4-6)"
            else:
                r["grup"] = "13 Eylul erken"
            for f in (u.get("failsafe") or []):
                if f["tip"] in ("MODE", "ERR"):
                    fs_olay.append((f["t"], f["aciklama"]))
            kayit["ucuslar"].append(r)
            (ucuslar if r["tur"] == "ucus" else kisalar if r["tur"] == "kisa_sicrama" else arm_yalniz).append(r)
        # zaman grafigi (ucus iceren loglar)
        if any(r["tur"] == "ucus" for r in kayit["ucuslar"]):
            png = CIKTI_DIZIN / f"zaman_{stem.replace(' ', '_')}.png"
            grafik_zaman(stem, [r for r in kayit["ucuslar"] if r["tur"] != "arm_yalniz"], sorted(set(fs_olay)), png)
            grafikler.append(str(png.relative_to(KOK)).replace("\\", "/"))
        loglar_out.append(kayit)

    # ------------------------------------------------------------------ toplulastirma
    def havuz(alan_fn, U):
        v = [alan_fn(u) for u in U]; v = [x for x in v if x is not None]
        return v

    aski_U = [u for u in ucuslar if u.get("aski")]
    # askı orneklerini havuzla (ThO)
    tho_havuz, I_havuz, P_havuz, V_havuz = [], [], [], []
    grup_havuz = defaultdict(lambda: {"tho": [], "I": [], "P": [], "V": [], "n_ucus": 0, "aski_s": 0.0})
    for u in aski_U:
        g = u["_g"]; am = g["am"]; ct = g["ct"]; b = g["bat"]
        tho_havuz.extend(g["tho"][am].tolist())
        if len(b):
            va, ia = np.interp(ct[am], b[:, 0], b[:, 1]), np.interp(ct[am], b[:, 0], b[:, 2])
            I_havuz.extend(ia.tolist()); P_havuz.extend((va * ia).tolist()); V_havuz.extend(va.tolist())
            gh = grup_havuz[u["grup"]]; gh["tho"].extend(g["tho"][am].tolist()); gh["I"].extend(ia.tolist()); gh["P"].extend((va * ia).tolist()); gh["V"].extend(va.tolist())
            gh["n_ucus"] += 1; gh["aski_s"] += u["aski_s"] or 0
    tho_h, I_h, P_h, V_h = map(np.array, (tho_havuz, I_havuz, P_havuz, V_havuz))

    def ist(a, n=3):
        return {"n": int(len(a)), "ort": _r(a.mean(), n), "p50": _r(np.median(a), n), "p05": _r(_p(a, 5), n), "p95": _r(_p(a, 95), n),
                "std": _r(a.std(), n)} if len(a) else None

    aski_toplam_s = float(sum(u["aski_s"] or 0 for u in aski_U))
    ucus_saat_kapasite = PIL_MAH_BEYAN * KULLANILABILIR_ORAN
    gruplar = {}
    for gad, gh in grup_havuz.items():
        I = np.array(gh["I"]); P = np.array(gh["P"]); T = np.array(gh["tho"]); V = np.array(gh["V"])
        gruplar[gad] = {"ucus_n": gh["n_ucus"], "aski_s": _r(gh["aski_s"], 1), "ThO": ist(T), "I_A": ist(I, 1), "P_W": ist(P, 1), "V": ist(V, 2),
                        "ucus_suresi_dk_HESAP": _r(ucus_saat_kapasite / I.mean() * 60 / 1000, 1) if len(I) else None}
    # failsafe ile biten ucuslar: arm -> PIL_FS suresi ve tuketilen mAh
    pil_fs = []
    for u in ucuslar:
        pf = (u.get("bat") or {}).get("pil_fs")
        if pf:
            b = u["_g"]["bat"]; t_fs = pf["t"]; sm = b[:, 0] <= t_fs
            pil_fs.append({"ucus": u["etiket_kisa"], "arm_t": u["arm_t"], "fs_t": t_fs, "armdan_fs_s": _r(t_fs - u["arm_t"], 1),
                           "motorludan_fs_s": _r(t_fs - u["_span"][0], 1), "mAh_fs_anina_kadar": _r(b[sm, 3][-1] - b[0, 3], 0) if sm.any() else None,
                           "V_bas": u["bat"]["V_bas"], "V_min_ucus": u["bat"]["V_min"], "VoltR_min_ucus": u["bat"]["VoltR_min"], **pf})
    # fiziksel durum degisimi kaniti: 09-59-30 #3 -> #4 (ayni log, ayni pil, 5 dk ara)
    def _bul(ad):
        return next((u for u in ucuslar if u["etiket_kisa"] == ad), None)
    u3, u4 = _bul("2026-09-13 09-59 #3"), _bul("2026-09-13 09-59 #4")
    degisim_kaniti = None
    if u3 and u4 and u3.get("aski") and u4.get("aski"):
        def _oz(u):
            return {"aski_ThO_p50": u["aski"]["ThO_p50"], "aski_I_A": u["bat"]["aski"]["I_ort"], "aski_P_W": u["bat"]["aski"]["P_W_ort"], "aski_V": u["bat"]["aski"]["V_ort"],
                    "ccw_eksi_cw_pwm": u["rcou"]["ccw_eksi_cw_pwm"], "M1_M4": u["rcou"]["M1_M4_ort"], "VibeZ_aski_ort": u["vibe"]["IMU0"]["Z_aski"]["ort"],
                    "VibeZ_aski_p95": u["vibe"]["IMU0"]["Z_aski"]["p95"], "yaw_rate_rms_dps": (u.get("rate_aski") or {}).get("yaw_rms_hata_dps"),
                    "arm_t": u["arm_t"], "disarm_t": u["disarm_t"]}
        degisim_kaniti = {"once_09-59_#3": _oz(u3), "sonra_09-59_#4": _oz(u4), "ara_s": _r(u4["arm_t"] - u3["disarm_t"], 0),
                          "not": "ayni log/pil; 5 dk arada aski akimi, gucu, CCW-CW motor farki ve VibeZ birlikte sicradi — fiziksel degisiklik (yuk/pervane/montaj) LOGDAN BELIRLENEMEZ, kullaniciya sorulacak"}
    # ThH sahiplik: A loglarindaki degisimler + B loguna bakis (tum_loglar.json)
    thh_gecmis = []
    for l in sorted([x for x in tum["loglar"] if "KOPYA_OF" not in x and "HATA" not in x], key=lambda x: (x["sira"]["STAT_BOOTCNT"] or 0)):
        thh_gecmis.append({"BOOTCNT": l["sira"]["STAT_BOOTCNT"], "log": Path(l["dosya"]).stem, "etiket": l["kullanici_beyani"]["etiket"], "hucre": l["hucre"]["n"],
                           "ThH_log_sonu": l["parm"]["MOT_THST_HOVER"], "ThH_degisim_logda": [(x["eski"], x["yeni"], x["t"]) for x in l["parm_degisim"] if x["ad"] == "MOT_THST_HOVER"],
                           "ucus_n": l["ozet"]["ucus_n"], "kisa_n": l["ozet"]["kisa_sicrama_n"]})
    # kisa sicrama toplulastirma
    kisa_oz = None
    if kisalar:
        kisa_oz = {"n": len(kisalar), "toplam_motorlu_s": _r(sum(u["motorlu_s"] or 0 for u in kisalar), 1),
                   "motorlu_s_aralik": [min(u["motorlu_s"] for u in kisalar), max(u["motorlu_s"] for u in kisalar)],
                   "alt_maks_m_aralik": [min(u["alt_maks_m"] for u in kisalar), max(u["alt_maks_m"] for u in kisalar)],
                   "I_maks_A": {"maks": max(u["bat"]["I_maks"] for u in kisalar if u.get("bat")), "medyan": _r(np.median([u["bat"]["I_maks"] for u in kisalar if u.get("bat")]), 1)},
                   "V_min_V": {"min": min(u["bat"]["V_min"] for u in kisalar if u.get("bat")), "medyan": _r(np.median([u["bat"]["V_min"] for u in kisalar if u.get("bat")]), 2)},
                   "V_min_hucre_min": _r(min(u["bat"]["V_min"] for u in kisalar if u.get("bat")) / HUCRE_N, 2),
                   "ThO_maks_medyan": _r(np.median([u["ThO_maks"] for u in kisalar]), 2),
                   "vibeZ_motorlu_maks_IMU0": max(((u.get("vibe") or {}).get("IMU0") or {}).get("Z_motorlu", {}).get("maks") or 0 for u in kisalar),
                   "clip_toplam": sum((u.get("vibe") or {}).get("clip_toplam") or 0 for u in kisalar),
                   "rcou_yayilim_pwm_medyan": _r(np.median([u["rcou"]["yayilim_pwm"] for u in kisalar if u.get("rcou")]), 0),
                   "rcou_en_yuksek_sayim": dict(zip(*np.unique([u["rcou"]["en_yuksek"] for u in kisalar if u.get("rcou")], return_counts=True))),
                   "att_roll_rms_medyan": _r(np.median([u["att"]["motorlu"]["roll_rms_hata_deg"] for u in kisalar if u.get("att")]), 1),
                   "not": "yer temasi/devrilme/gaz darbesi: aski olcumu DEGIL; VIBE ve akim tepeleri askidan ayri tutuldu"}
        kisa_oz["rcou_en_yuksek_sayim"] = {str(k): int(v) for k, v in kisa_oz["rcou_en_yuksek_sayim"].items()}
    # VIBE havuz + grafikler
    png_vibe = CIKTI_DIZIN / "vibe_dagilim.png"; vibe_havuz = grafik_vibe(ucuslar, kisalar, png_vibe); grafikler.append(str(png_vibe.relative_to(KOK)).replace("\\", "/"))
    png_oz = CIKTI_DIZIN / "ozet_aski_ucuslar.png"; grafik_ozet(ucuslar, png_oz); grafikler.append(str(png_oz.relative_to(KOK)).replace("\\", "/"))
    png_thh = CIKTI_DIZIN / "thh_gecmisi_tum_loglar.png"; grafik_thh(tum, png_thh); grafikler.append(str(png_thh.relative_to(KOK)).replace("\\", "/"))
    png_fft = CIKTI_DIZIN / "fft_aski_imu0.png"; fft_ucuslar = grafik_fft(ucuslar, png_fft); grafikler.append(str(png_fft.relative_to(KOK)).replace("\\", "/"))
    png_vi = CIKTI_DIZIN / "gerilim_akim.png"; grafik_gerilim_akim(ucuslar, kisalar, png_vi); grafikler.append(str(png_vi.relative_to(KOK)).replace("\\", "/"))
    png_mot = CIKTI_DIZIN / "motor_dengesi_aski.png"; grafik_motor(ucuslar, png_mot); grafikler.append(str(png_mot.relative_to(KOK)).replace("\\", "/"))

    # motor dengesi toplulastirma (aski)
    mot_U = [u for u in ucuslar if u.get("rcou") and u["rcou"]["kapsam"] == "aski"]
    motor_oz = None
    if mot_U:
        motor_oz = {"ucus_n": len(mot_U),
                    "M_ort_pwm": {m: round(float(np.mean([u["rcou"]["M1_M4_ort"][m] for u in mot_U]))) for m in MOTOR_KANAL},
                    "en_yuksek_sayim": {k: int(v) for k, v in zip(*np.unique([u["rcou"]["en_yuksek"] for u in mot_U], return_counts=True))},
                    "en_dusuk_sayim": {k: int(v) for k, v in zip(*np.unique([u["rcou"]["en_dusuk"] for u in mot_U], return_counts=True))},
                    "on_eksi_arka_pwm": ist(np.array([u["rcou"]["on_eksi_arka_pwm"] for u in mot_U]), 1),
                    "sag_eksi_sol_pwm": ist(np.array([u["rcou"]["sag_eksi_sol_pwm"] for u in mot_U]), 1),
                    "ccw_eksi_cw_pwm": ist(np.array([u["rcou"]["ccw_eksi_cw_pwm"] for u in mot_U]), 1),
                    "yayilim_pwm": ist(np.array([u["rcou"]["yayilim_pwm"] for u in mot_U]), 1),
                    "ucus_bazinda": [{"ucus": u["etiket_kisa"], "M1_M4": u["rcou"]["M1_M4_ort"], "ccw_eksi_cw": u["rcou"]["ccw_eksi_cw_pwm"],
                                      "on_eksi_arka": u["rcou"]["on_eksi_arka_pwm"], "sag_eksi_sol": u["rcou"]["sag_eksi_sol_pwm"],
                                      "yaw_rate_rms_dps": (u.get("rate_aski") or {}).get("yaw_rms_hata_dps"),
                                      "yaw_hata_rms_deg": ((u.get("att") or {}).get("aski_yaw") or {}).get("yaw_hata_rms_deg")} for u in mot_U],
                    "kanal": MOTOR_KANAL, "konum": MOTOR_KONUM,
                    "not": "CCW-CW > 0: FC, CCW motorlari (M1,M2) daha yuksek suruyor = govdeye CW moment uyguluyor; kaynak (montaj egikligi, pervane farki) LOGDAN BELIRLENEMEZ"}
    att_oz = {"aski_roll_rms_deg": ist(np.array([u["att"]["aski"]["roll_rms_hata_deg"] for u in ucuslar if u.get("att", {}).get("aski")]), 2),
              "aski_pitch_rms_deg": ist(np.array([u["att"]["aski"]["pitch_rms_hata_deg"] for u in ucuslar if u.get("att", {}).get("aski")]), 2),
              "motorlu_roll_rms_deg": ist(np.array([u["att"]["motorlu"]["roll_rms_hata_deg"] for u in ucuslar if u.get("att")]), 2),
              "motorlu_pitch_rms_deg": ist(np.array([u["att"]["motorlu"]["pitch_rms_hata_deg"] for u in ucuslar if u.get("att")]), 2),
              "rate_aski_roll_rms_dps": ist(np.array([u["rate_aski"]["roll_rms_hata_dps"] for u in ucuslar if u.get("rate_aski")]), 2),
              "rate_aski_pitch_rms_dps": ist(np.array([u["rate_aski"]["pitch_rms_hata_dps"] for u in ucuslar if u.get("rate_aski")]), 2)}
    ekf_oz = {"innov_dusen_ornek_toplam": sum(c["innov_dusen_n"] for u in ucuslar for c in u["ekf"]["cekirdek"].values()),
              "SV_maks": max((c["SV_maks"] for u in ucuslar for c in u["ekf"]["cekirdek"].values()), default=None),
              "SM_maks": max((c["SM_maks"] for u in ucuslar for c in u["ekf"]["cekirdek"].values()), default=None),
              "lane_switch_ucuslar": [u["etiket_kisa"] for u in ucuslar if u["ekf"]["lane_switch"]],
              "yaw_reset_toplam": sum(u["ekf"]["yaw_reset_n"] for u in ucuslar),
              "innov_dusen_ucuslar": [(u["etiket_kisa"], {k: c["innov_dusen_n"] for k, c in u["ekf"]["cekirdek"].items()}) for u in ucuslar if any(c["innov_dusen_n"] for c in u["ekf"]["cekirdek"].values())]}
    olay_oz = []
    for u in ucuslar + kisalar:
        for f in (u.get("failsafe") or []):
            olay_oz.append({"ucus": u["etiket_kisa"], "t": f["t"], "tip": f["tip"], "aciklama": f["aciklama"]})
        for ls in u["ekf"]["lane_switch"]:
            if "lane switch" in ls["msg"]:
                olay_oz.append({"ucus": u["etiket_kisa"], "t": ls["t"], "tip": "EKF", "aciklama": ls["msg"]})
    # ogrenme ozeti
    ogr_oz = [{"ucus": u["etiket_kisa"], "kip_arm": u["kip_arm"], "ThH_bas": u["ThH"]["bas"], "ThH_son": u["ThH"]["son"], "degisen_n": u["ThH"]["degisen_ornek_n"],
               "aski_ThO_p50": u["aski"]["ThO_p50"] if u.get("aski") else None, **{k: v for k, v in u["ogrenme"].items() if k != "not"}} for u in ucuslar]

    # ic direnc
    R_list = [u["bat"]["R_uydurma_ohm"] for u in ucuslar if u.get("bat") and u["bat"].get("R_uydurma_ohm")]
    Rfc = [u["bat"]["Res_FC_medyan_ohm"] for u in ucuslar if u.get("bat") and u["bat"].get("Res_FC_medyan_ohm")]
    sarkma = {"ucus_V_bas_ort": _r(np.mean([u["bat"]["V_bas"] for u in ucuslar]), 2), "ucus_V_min_ort": _r(np.mean([u["bat"]["V_min"] for u in ucuslar]), 2),
              "ucus_sarkma_hucre_V": ist(np.array([u["bat"]["sarkma_hucre_V"] for u in ucuslar]), 3),
              "aski_sarkma_hucre_V": ist(np.array([u["bat"]["aski"]["sarkma_hucre_V_askida"] for u in aski_U if u["bat"].get("aski")]), 3),
              "aski_V_hucre_ort": _r(V_h.mean() / HUCRE_N, 3) if len(V_h) else None,
              "R_uydurma_ohm_paket": ist(np.array(R_list), 4), "R_uydurma_ohm_hucre_HESAP": _r(np.mean(R_list) / HUCRE_N, 4) if R_list else None,
              "Res_FC_ohm": ist(np.array(Rfc), 4),
              "kisa_sicrama_V_min_hucre": kisa_oz["V_min_hucre_min"] if kisa_oz else None,
              "BATT_VOLT_MULT_degerleri": sorted({k["parm"]["BATT_VOLT_MULT"] for k in loglar_out if "parm" in k} | {x["yeni"] for k in loglar_out for x in k.get("parm_degisim", []) if x["ad"] == "BATT_VOLT_MULT"}),
              "not": "BATT_VOLT_MULT loglar arasinda 17,02-19,53 arasinda DEGISTIRILMIS (PM06 varsayilani 18,18): loglar arasi mutlak V/P karsilastirmasi ±%7 kalibrasyon belirsizligi tasir; ayni log icindeki sarkma (V_bas−V_min) bundan etkilenmez (orantili)"}

    ozet = {
        "meta": {"arac": "results/ucus_analiz_20260915/A_3S_1045/analiz_A.py", "ortak_arac": "scripts/ucus_bin_analiz.py (pencereler/etiketler)",
                 "uretim_zamani": _dt.datetime.now().isoformat(timespec="seconds"), "numpy": np.__version__,
                 "konfig": {"etiket": "A", "pil": "3S (kullanici beyani; hucre sayisi ilk BAT geriliminden dogrulandi)", "pervane": "10x4.5 (1045) 2 pal (kullanici beyani, LOGDA YOK)",
                            "motor": "SunnySky X2220 980KV (kullanici beyani)", "kutle": "BILINMIYOR (logda yok)", "pil_kapasitesi_mAh": PIL_MAH_BEYAN, "kullanilabilir_oran": KULLANILABILIR_ORAN},
                 "olcutler": tum["meta"]["olcutler"], "motor_haritasi": {"kanal": MOTOR_KANAL, "konum": MOTOR_KONUM,
                                                                          "kaynak": "PARM SERVO9..12_FUNCTION = 36,34,33,35 (Motor4,2,1,3); SERVO1,2,4=34 (M2 kopyasi), SERVO3=33 (M1 kopyasi)"},
                 "ogrenme_kosulu": "Copter::update_throttle_hover (4.5): armli, yerde degil, kip manuel-gaz degil (STAB/ACRO/DRIFT haric), pos_control vel_desired.z==0, |vz|<60 cm/s, |roll|,|pitch|<5 deg; TC 10 s"},
        "loglar_n": len(L_A), "log_listesi": [Path(l["dosya"]).stem for l in L_A],
        "sayim": {"ucus_n": len(ucuslar), "kisa_sicrama_n": len(kisalar), "arm_yalniz_n": len(arm_yalniz), "askili_ucus_n": len(aski_U),
                  "toplam_motorlu_s_ucus": _r(sum(u["motorlu_s"] or 0 for u in ucuslar), 1), "toplam_motorlu_s_kisa": _r(sum(u["motorlu_s"] or 0 for u in kisalar), 1),
                  "askida_toplam_s": _r(aski_toplam_s, 1), "en_uzun_aski_dilimi_s": max((u["aski"]["en_uzun_dilim_s"] for u in aski_U), default=None)},
        "aski_gazi": {"havuz_ThO": ist(tho_h), "gruplar": gruplar, "ucus_bazinda_ThO_p50": [(u["etiket_kisa"], u["aski"]["ThO_p50"], u["aski_s"], u["kip_arm"]) for u in aski_U]},
        "aski_akim_guc": {"havuz_I_A": ist(I_h, 1), "havuz_P_W": ist(P_h, 1), "havuz_V": ist(V_h, 2),
                          "ucus_suresi_dk_HESAP": {"kapasite_mAh_beyan": PIL_MAH_BEYAN, "kullanilabilir_mAh": ucus_saat_kapasite,
                                                   "havuz_I_ort_ile": _r(ucus_saat_kapasite / I_h.mean() * 60 / 1000, 1) if len(I_h) else None,
                                                   "havuz_I_p95_ile": _r(ucus_saat_kapasite / _p(I_h, 95) * 60 / 1000, 1) if len(I_h) else None,
                                                   "gruplar": {g: v["ucus_suresi_dk_HESAP"] for g, v in gruplar.items()},
                                                   "not": "kapasite/akim HESABI; pratikte BATT_LOW_VOLT failsafe sarkma nedeniyle cok daha erken tetiklendi (pil_failsafe_gozlemi)"},
                          "pil_failsafe_gozlemi": pil_fs},
        "gerilim_sarkmasi": sarkma,
        "MOT_THST_HOVER": {"A_loglarinda_deger_araligi": sorted({k["MOT_THST_HOVER_log_sonu"] for k in loglar_out}), "gecmis_tum_loglar_BOOTCNT_sirasi": thh_gecmis,
                           "ogrenme_ozet": {"ThH_degisen_ucus_n": sum(1 for u in ucuslar if u["ThH"]["degisen_ornek_n"]),
                                            "ogrenme_kosullu_toplam_s": _r(sum(u["ogrenme"]["tum_kosul_s"] or 0 for u in ucuslar), 1),
                                            "askida_toplam_s": _r(aski_toplam_s, 1),
                                            "12_Eylul_ogrenme_s": _r(sum(u["ogrenme"]["tum_kosul_s"] or 0 for u in ucuslar if u["grup"] == "12 Eylul"), 1),
                                            "13_Eylul_ogrenme_s": _r(sum(u["ogrenme"]["tum_kosul_s"] or 0 for u in ucuslar if u["grup"] != "12 Eylul"), 1),
                                            "rcin_gaz_olu_bant_disi_orani_askida": [(u["etiket_kisa"], u["kip_arm"], (u.get("rcin_aski") or {}).get("gaz_olu_bant_disi_orani"), u["ThH"]["degisen_ornek_n"]) for u in aski_U]},
                           "ogrenme_ucus_bazinda": ogr_oz},
        "durum_degisimi_kaniti_09-59-30": degisim_kaniti,
        "titresim": {"havuz_IMU0": vibe_havuz, "clip_toplam_ucus": sum((u.get("vibe") or {}).get("clip_toplam") or 0 for u in ucuslar),
                     "clip_toplam_kisa": sum((u.get("vibe") or {}).get("clip_toplam") or 0 for u in kisalar),
                     "clipli_ucuslar": [(u["etiket_kisa"], u["vibe"]["clip_toplam"], u["vibe"]["IMU0"]["pencere_maks"]) for u in ucuslar if (u.get("vibe") or {}).get("clip_toplam")],
                     "ucus_bazinda_aski_IMU0": [(u["etiket_kisa"], u["vibe"]["IMU0"].get("X_aski", {}).get("ort"), u["vibe"]["IMU0"].get("Y_aski", {}).get("ort"),
                                                u["vibe"]["IMU0"].get("Z_aski", {}).get("ort"), u["vibe"]["IMU0"].get("Z_aski", {}).get("p95")) for u in aski_U if u.get("vibe")],
                     "imu1_vs_imu0_aski_Z_ort": [(u["etiket_kisa"], u["vibe"]["IMU0"].get("Z_aski", {}).get("ort"), (u["vibe"].get("IMU1") or {}).get("Z_aski", {}).get("ort")) for u in aski_U if u.get("vibe")],
                     "fft": {"grafik_ucuslar": fft_ucuslar, "ucus_bazinda": [(u["etiket_kisa"], u["imu_fft"]["fs_hz"], u["imu_fft"]["AccZ"]["rms_ms2"], u["imu_fft"]["AccZ"]["tepeler"][:3]) for u in ucuslar if u.get("imu_fft")],
                             "not": "IMU 25 Hz → Nyquist 12,5 Hz; INS_ACCEL_FILTER 20 Hz; pervane temel frekansi cozulemez. 2 pal (1045) / 3 pal karsilastirmasi bu veriyle YAPILAMAZ; yalniz VIBE (ham ivme sapmasi) karsilastirilabilir"}},
        "motor_dengesi": motor_oz, "tutum": att_oz, "ekf": ekf_oz, "olaylar": olay_oz, "kisa_sicramalar": kisa_oz,
        "loglar": loglar_out, "grafikler": grafikler,
    }
    # ham diziler JSON'a girmez
    def _ayikla(o):
        if isinstance(o, dict):
            return {k: _ayikla(v) for k, v in o.items() if not k.startswith("_")}
        if isinstance(o, (list, tuple)):
            return [_ayikla(v) for v in o]
        return o
    out = CIKTI_DIZIN / "ozet.json"
    out.write_text(json.dumps(_temiz(_ayikla(ozet)), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {out}  ({out.stat().st_size / 1e3:.0f} KB); grafik {len(grafikler)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
