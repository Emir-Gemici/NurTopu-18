#!/usr/bin/env python3
"""KONFIGURASYON C (3S + 9x5x3, 14 Eylul 2026 aksami) — derin log analizi.

Girdi : results/ucus_20260914/2026-09-14 19-43-06.bin (MP #68), 2026-09-14 21-10-34.bin (MP #69)
        + results/ucus_analiz_20260915/tum_loglar.json (arm pencereleri ve A/B/D karsilastirma tabani)
Cikti : results/ucus_analiz_20260915/C_3S_9x5x3/ozet.json + PNG grafikler

Her sayi LOGDAN hesaplanir. Pil/pervane/kutle logda yok -> "kullanici_beyani" etiketiyle.
Askı orneklemi: scripts/ucus_bin_analiz.py ile AYNI olcut (irtifa > 1 m, |vz| < 0,5 m/s, ThO 0,25-0,75).
Motor kanallari: SERVOn_FUNCTION'dan (33..36 = Motor1..4); bu aracta ESC'ler AUX1-4 = SERVO9-12
(donanim kunyesi, kullanici beyani). MAIN cikislarindaki C1-C8 ayni fonksiyonlarin AYNASIDIR
(C1/C2/C4/C5/C8 = Motor2, C3/C7 = Motor1, C6 = Motor4) — tum_loglar.json'daki "C1-C4" motor
dengesi bu yuzden yaniltici (bkz. ozet.json meta.uyari_rcou).

Bagimlilik: pymavlink DFReader, numpy, matplotlib. SciPy/scikit YOK.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[3]          # O:/navitas
sys.path.insert(0, str(KOK / "scripts"))
import ucus_bin_analiz as UBA  # noqa: E402  (aski_maskesi, dikey_hiz, en_uzun_kosu, imu_fft, esikler)

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

CIKTI = Path(__file__).resolve().parent
TUM_JSON = KOK / "results/ucus_analiz_20260915/tum_loglar.json"
LOGLAR = [KOK / "results/ucus_20260914/2026-09-14 19-43-06.bin",
          KOK / "results/ucus_20260914/2026-09-14 21-10-34.bin"]

# ----------------------------------------------------------------------------- sabitler (logdan / AP kaynagindan)
HOVER_TC_S = 10.0            # AP_MOTORS_THST_HOVER_TC (AP_MotorsMulticopter.h) — ogrenme zaman sabiti
PIL_MAH = 8000.0             # kullanici beyani (BATT_CAPACITY=8000 logda da var)
KULLANILABILIR = 0.80        # %80 kullanilabilir (gorev metni)
HUCRE_N = 3                  # ilk BAT geriliminden (12,44 / 12,09 V -> 3S); tum_loglar.json 'hucre'
YER_TEMASI_ALT_M = 0.30      # motorlu ama irtifa < 0,3 m: kalkis/inis yer temasi dilimi (askidan AYRI)
MOTOR_FN = {33: "M1", 34: "M2", 35: "M3", 36: "M4"}
# ArduCopter FRAME_TYPE=1 (X): M1 on-sag CCW, M2 arka-sol CCW, M3 on-sol CW, M4 arka-sag CW
MOTOR_KONUM = {"M1": "on-sag (CCW)", "M2": "arka-sol (CCW)", "M3": "on-sol (CW)", "M4": "arka-sag (CW)"}

# dataviz paleti (references/palette.md, acik yuzey)
RENK = {"mavi": "#2a78d6", "turuncu": "#eb6834", "aqua": "#1baf7a", "sari": "#eda100",
        "magenta": "#e87ba4", "yesil": "#008300", "mor": "#4a3aa7", "kirmizi": "#e34948"}
SERI = [RENK["mavi"], RENK["turuncu"], RENK["aqua"], RENK["sari"]]
YUZEY, IZGARA, MUREKKEP, IKINCIL, SOLUK = "#fcfcfb", "#e1e0d9", "#0b0b0b", "#52514e", "#898781"


# ----------------------------------------------------------------------------- okuma
def oku(yol: Path):
    from pymavlink import DFReader
    log = DFReader.DFReader_binary(str(yol))
    parm, parm_degisim = {}, []
    ev, arm, mode, err, msg = [], [], [], [], []
    ctun, bat, vibe, rcou, rcin, att, ekf, motb, gps, pm, rate = [], [], [], [], [], [], [], [], [], [], []
    imu = defaultdict(list)
    ver, sayac = None, defaultdict(int)
    while True:
        m = log.recv_msg()
        if m is None:
            break
        tp = m.get_type()
        sayac[tp] += 1
        tu = getattr(m, "TimeUS", None)
        t = tu / 1e6 if tu is not None else None
        if tp == "PARM":
            ad, v = m.Name, UBA._f32(m.Value)
            if ad in parm and parm[ad] != v and not ad.startswith("STAT_"):
                parm_degisim.append({"t": round(t, 1), "ad": ad, "eski": parm[ad], "yeni": v})
            parm[ad] = v
        elif tp == "EV":
            ev.append((t, int(m.Id)))
        elif tp == "ARM":
            arm.append((t, int(m.ArmState), int(getattr(m, "Method", -1))))
        elif tp == "MODE":
            mode.append((t, int(m.ModeNum), int(getattr(m, "Rsn", 0))))
        elif tp == "ERR":
            err.append((t, int(m.Subsys), int(m.ECode)))
        elif tp == "MSG":
            msg.append((t, str(m.Message)))
        elif tp == "CTUN":
            ctun.append((t, m.ThO, m.ThH, m.Alt, m.DAlt, m.DCRt, m.CRt, m.ThI))
        elif tp == "BAT":
            if int(getattr(m, "Inst", 0)) == 0:
                bat.append((t, m.Volt, m.Curr, m.CurrTot, getattr(m, "Res", float("nan")),
                            getattr(m, "RemPct", float("nan")), getattr(m, "VoltR", float("nan"))))
        elif tp == "VIBE":
            vibe.append((t, int(m.IMU), m.VibeX, m.VibeY, m.VibeZ, int(m.Clip)))
        elif tp == "RCOU":
            rcou.append([t] + [int(getattr(m, f"C{i}")) for i in range(1, 15)])
        elif tp == "RCIN":
            rcin.append((t, int(m.C1), int(m.C2), int(m.C3), int(m.C4)))
        elif tp == "ATT":
            att.append((t, m.DesRoll, m.Roll, m.DesPitch, m.Pitch, m.DesYaw, m.Yaw, m.ErrRP, m.ErrYaw))
        elif tp == "XKF4":
            ekf.append((t, int(m.C), m.SV, m.SP, m.SH, m.SM, m.errRP, int(m.PI), int(m.FS), int(m.TS), int(m.SS)))
        elif tp == "IMU":
            imu[int(m.I)].append((t, m.GyrX, m.GyrY, m.GyrZ, m.AccX, m.AccY, m.AccZ))
        elif tp == "MOTB":
            motb.append((t, m.LiftMax, m.BatVolt, m.ThLimit, m.ThrAvMx, m.ThrOut))
        elif tp == "RATE":
            rate.append((t, m.RDes, m.R, m.ROut, m.PDes, m.P, m.POut, m.YDes, m.Y, m.YOut))
        elif tp == "GPS":
            if int(getattr(m, "I", 0)) == 0:
                gps.append((t, int(m.Status), int(m.NSats), m.HDop))
        elif tp == "PM":
            pm.append((t, int(m.NLon), int(m.Load), int(getattr(m, "MaxT", 0))))
        elif tp == "VER":
            ver = str(getattr(m, "FWS", ""))
    A = lambda x, n: np.array(x, float).reshape(-1, n)  # noqa: E731
    return {"parm": parm, "parm_degisim": parm_degisim, "ev": ev, "arm": arm, "mode": mode, "err": err,
            "msg": msg, "ver": ver, "sayac": dict(sayac),
            "ctun": A(ctun, 8), "bat": A(bat, 7), "vibe": A(vibe, 6), "rcou": A(rcou, 15), "rcin": A(rcin, 5),
            "att": A(att, 9), "ekf": A(ekf, 11), "motb": A(motb, 6), "gps": A(gps, 4), "pm": A(pm, 4), "rate": A(rate, 10),
            "imu": {k: A(v, 7) for k, v in imu.items()}}


# ----------------------------------------------------------------------------- yardimcilar
def _r(x, n=3):
    if x is None:
        return None
    x = float(x)
    return round(x, n) if math.isfinite(x) else None


def _p(a, q):
    return _r(np.percentile(a, q)) if len(a) else None


def ist(a, n=3):
    a = np.asarray(a, float)
    if len(a) == 0:
        return None
    return {"n": int(len(a)), "ort": _r(a.mean(), n), "p50": _r(np.median(a), n), "p05": _p(a, 5),
            "p95": _p(a, 95), "min": _r(a.min(), n), "maks": _r(a.max(), n), "std": _r(a.std(), n)}


def dilim(arr, t0, t1):
    return arr[(arr[:, 0] >= t0) & (arr[:, 0] <= t1)]


def maske_tasi(t_kaynak, maske, t_hedef):
    """CTUN zamanindaki bool maskeyi baska mesaj zamanina en yakin ornekle tasir."""
    if len(t_kaynak) == 0:
        return np.zeros(len(t_hedef), bool)
    i = np.searchsorted(t_kaynak, t_hedef)
    i = np.clip(i, 0, len(t_kaynak) - 1)
    j = np.clip(i - 1, 0, len(t_kaynak) - 1)
    yakin = np.where(np.abs(t_kaynak[i] - t_hedef) <= np.abs(t_kaynak[j] - t_hedef), i, j)
    return maske[yakin] & (np.abs(t_kaynak[yakin] - t_hedef) < 0.15)


def motor_kanallari(parm):
    """SERVOn_FUNCTION -> {Mk: [servo no...]}; ESC'lerin AUX1-4 (SERVO9-12) uzerinde oldugu kullanici beyani."""
    fn = {}
    for n in range(1, 17):
        f = parm.get(f"SERVO{n}_FUNCTION")
        if f is not None and int(f) in MOTOR_FN:
            fn.setdefault(MOTOR_FN[int(f)], []).append(n)
    aux = {}
    for n in range(9, 13):
        f = parm.get(f"SERVO{n}_FUNCTION")
        if f is not None and int(f) in MOTOR_FN:
            aux[MOTOR_FN[int(f)]] = n
    return fn, aux


def sarkma_ic_direnc(bat_w, tho_maske):
    """V = V0 - R*I en kucuk kareler (motorlu ornekler). -> (R_ohm, V0, r2, n)"""
    V, I = bat_w[tho_maske, 1], bat_w[tho_maske, 2]
    if len(V) < 20 or I.std() < 1.0:
        return None
    A = np.vstack([np.ones_like(I), -I]).T
    (v0, R), res, *_ = np.linalg.lstsq(A, V, rcond=None)
    ss_tot = float(((V - V.mean()) ** 2).sum())
    r2 = 1.0 - float(res[0]) / ss_tot if len(res) and ss_tot > 0 else None
    return {"R_paket_mohm": _r(R * 1000, 1), "R_hucre_mohm": _r(R * 1000 / HUCRE_N, 1),
            "V0_V": _r(v0, 2), "r2": _r(r2, 3), "n": int(len(V)),
            "yontem": "BAT.Volt = V0 - R*BAT.Curr, motorlu ornekler, numpy lstsq"}


def ogrenme_analizi(c_w, rcin_w, aski, parm):
    """CTUN.ThH degisimi = ogrenme aktif. TC tahmini ve gaz cubugu olu-bant orani."""
    t, tho, thh = c_w[:, 0], c_w[:, 1], c_w[:, 2]
    d = np.diff(thh)
    aktif = np.abs(d) > 1e-6
    dt = np.diff(t)
    aktif_s = float(dt[aktif].sum())
    # TC tahmini: dThH ≈ (ThO - ThH) * dt / TC  (dt=0,1 s icin 10 x 0,01 s adim ≈ ayni)
    tc = None
    if aktif.sum() >= 10:
        gap = (tho[:-1] - thh[:-1])[aktif]
        ok = np.abs(gap) > 0.005
        if ok.sum() >= 10:
            tc_dizi = gap[ok] * dt[aktif][ok] / d[aktif][ok]
            tc = _r(np.median(tc_dizi), 1)
    dz = parm.get("THR_DZ", 100.0)
    olu_bant = None
    if len(rcin_w):
        m = maske_tasi(t, aski, rcin_w[:, 0])
        if m.sum():
            olu_bant = _r(np.mean(np.abs(rcin_w[m, 3] - 1500) <= dz), 3)
    dcrt0 = _r(np.mean(c_w[aski, 5] == 0), 3) if aski.sum() else None
    return {"ThH_bas": _r(thh[0], 4), "ThH_son": _r(thh[-1], 4), "degisim": _r(thh[-1] - thh[0], 4),
            "ogrenme_aktif_s": _r(aktif_s, 1), "ogrenme_aktif_ornek_n": int(aktif.sum()),
            "TC_tahmin_s": tc, "TC_AP_kaynak_s": HOVER_TC_S,
            "aski_RC3_olu_bant_orani": olu_bant, "aski_DCRt_sifir_orani": dcrt0,
            "not": "AP Copter::update_throttle_hover: yalniz pos_control hedef dikey hiz = 0 (gaz cubugu olu-bantta), "
                   "|vz|<0,6 m/s, |roll|,|pitch|<5 deg iken ogrenir; ThH sabit kaldigi orneklerde ogrenme kapali"}


def olu_bant_kosu_analizi(c_w, rcin_w, motorlu, parm):
    """Ogrenme-aktif orneklerin, gaz cubugunun olu-banda GIRMESINDEN bu yana gecen sureyle iliskisi.
    AP: pos_control hedef dikey hiz TAM SIFIR olmali; cubuk ortalandiktan sonra istenen hiz ustel soner
    (KPa = PSC_JERK_Z/PILOT_ACCEL_Z), FLT_EPSILON altina ~10 s'de iner — ogrenme ancak ondan sonra baslar."""
    t, tho, thh = c_w[:, 0], c_w[:, 1], c_w[:, 2]
    aktif = np.zeros(len(t), bool); aktif[1:] = np.abs(np.diff(thh)) > 1e-6
    if len(rcin_w) == 0:
        return None
    dz = parm.get("THR_DZ", 100.0)
    rct = rcin_w[:, 0]; olu = np.abs(rcin_w[:, 3] - 1500) <= dz
    disari_t = rct[~olu]
    kosu = np.empty(len(t))
    for i, ti in enumerate(t):
        k = np.searchsorted(disari_t, ti) - 1
        kosu[i] = ti - disari_t[k] if k >= 0 else ti - t[0]
    # motorlu donemdeki ≥3 s olu-bant kosulari
    mt = t[motorlu]
    kosular = []
    if len(mt):
        s = None
        for i in range(len(rct)):
            if olu[i] and s is None:
                s = rct[i]
            if (not olu[i] or i == len(rct) - 1) and s is not None:
                e = rct[i]
                if e > mt[0] and s < mt[-1]:
                    s2, e2 = max(s, mt[0]), min(e, mt[-1])
                    if e2 - s2 >= 3.0:
                        m = (t >= s2) & (t <= e2); ak = aktif[m]
                        kosular.append({"t": [_r(s2, 1), _r(e2, 1)], "sure_s": _r(e2 - s2, 1), "ogrenme_aktif_s": _r(ak.sum() * 0.1, 1),
                                        "ilk_aktif_gecikme_s": _r(t[m][ak][0] - s2, 1) if ak.any() else None})
                s = None
    esikler = {}
    for es in (2, 5, 8, 10):
        m = motorlu & (kosu >= es)
        esikler[f"kosu>={es}s"] = {"ornek_s": _r(m.sum() * 0.1, 1), "aktif_orani": _r(np.mean(aktif[m]), 2) if m.sum() else None}
    return {"aktif_orneklerde_olu_bant_kosu_suresi_s": {"min": _r(kosu[aktif].min(), 1), "p50": _r(np.median(kosu[aktif]), 1),
                                                       "maks": _r(kosu[aktif].max(), 1)} if aktif.any() else None,
            "kosu_esigi_vs_aktif_orani": esikler, "olu_bant_kosulari_>=3s": kosular,
            "PSC_JERK_Z": parm.get("PSC_JERK_Z"), "PILOT_ACCEL_Z": parm.get("PILOT_ACCEL_Z"),
            "yorum": "aktif ornekler yalniz ≥~10 s kesintisiz olu-bant kosusundan sonra basliyor (olculdu); cubuga her dokunus sayaci sifirlar"}


def gerekli_aski_suresi(thh, tho, tol=0.01):
    """Ilk-derece ogrenme: gap * exp(-t/TC) < tol -> t."""
    gap = abs(tho - thh)
    if gap <= tol:
        return 0.0
    return _r(HOVER_TC_S * math.log(gap / tol), 1)


# ----------------------------------------------------------------------------- pencere analizi
def pencere_analiz(ham, u, parm, fn_map, aux):
    t0, t1 = u["arm_t"], u["disarm_t"]
    c = dilim(ham["ctun"], t0, t1)
    ct, tho, thh, alt = c[:, 0], c[:, 1], c[:, 2], c[:, 3]
    taban = float(np.median(alt[ct <= t0 + UBA.ALT_TABAN_S])) if len(ct) else 0.0
    alt_rel = alt - taban
    motorlu = tho > UBA.MOTORLU_THO_ESIK
    motorlu_s = float(UBA._dt_dizisi(ct)[motorlu].sum())
    tur = UBA.ucus_turu(motorlu_s)
    aski = UBA.aski_maskesi(ct, alt_rel, tho)
    yer = motorlu & (alt_rel < YER_TEMASI_ALT_M)
    kosu = UBA.en_uzun_kosu(aski)
    dilim_t = [float(ct[kosu[0]]), float(ct[kosu[1]])] if kosu else None
    vz = UBA.dikey_hiz(ct, alt_rel)

    out = {"no": u["no"], "arm_t": t0, "disarm_t": t1, "pencere_s": _r(t1 - t0, 1), "tur": tur,
           "motorlu_s": _r(motorlu_s, 1), "alt_taban_m": _r(taban, 2), "alt_maks_m": _r(alt_rel.max(), 2) if len(alt_rel) else None,
           "aski_n": int(aski.sum()), "aski_s": _r(aski.sum() * 0.1, 1),
           "aski_en_uzun_dilim_t": dilim_t, "aski_en_uzun_dilim_s": _r(dilim_t[1] - dilim_t[0], 1) if dilim_t else None,
           "yer_temasi_n": int(yer.sum())}
    if tur != "ucus" or aski.sum() < UBA.ASKI_EN_AZ_ORNEK:
        out["not"] = "ucus degil ya da aski orneklemi yetersiz — aski istatistigi yok"
    # --- gaz
    out["gaz"] = {"ThO_aski": ist(tho[aski]) if aski.sum() else None,
                  "ThO_motorlu": ist(tho[motorlu]) if motorlu.sum() else None,
                  "ThO_yer_temasi": ist(tho[yer]) if yer.sum() else None,
                  "alt_aski_ort_m": _r(alt_rel[aski].mean(), 2) if aski.sum() else None,
                  "vz_aski_abs_ort_ms": _r(np.abs(vz[aski]).mean(), 2) if aski.sum() else None}
    out["ogrenme"] = ogrenme_analizi(c, dilim(ham["rcin"], t0, t1), aski, parm)
    out["ogrenme"]["olu_bant_kosu"] = olu_bant_kosu_analizi(c, dilim(ham["rcin"], t0 - 2.0, t1), motorlu, parm)
    if aski.sum():
        out["ogrenme"]["gap_ThO_aski_eksi_ThH_son"] = _r(tho[aski].mean() - thh[-1], 4)
        out["ogrenme"]["yakinsama_icin_gereken_aski_s_(tol_0.01)"] = gerekli_aski_suresi(thh[-1], tho[aski].mean())
        out["ogrenme"]["beklenen_ThH_son_tam_ogrenmeyle"] = _r(thh[0] + (tho[aski].mean() - thh[0]) * (1 - math.exp(-aski.sum() * 0.1 / HOVER_TC_S)), 4)
    # --- pil
    b = dilim(ham["bat"], t0 - 3.0, t1 + 6.0)
    bw = dilim(ham["bat"], t0, t1)
    bm_mot = maske_tasi(ct, motorlu, bw[:, 0]); bm_aski = maske_tasi(ct, aski, bw[:, 0])
    dinl = b[(b[:, 0] < t0)]
    topar = b[(b[:, 0] > t1 + 2.0)]
    V_dinl = float(np.median(dinl[:, 1])) if len(dinl) else float(bw[0, 1])
    V_min_i = int(np.argmin(bw[:, 1]))
    Wh = float(np.sum(bw[:-1, 1] * bw[:-1, 2] * np.diff(bw[:, 0])) / 3600.0)
    out["pil"] = {
        "hucre_n": HUCRE_N, "V_dinlenme_arm_oncesi": _r(V_dinl, 2), "V_bas_pencere": _r(bw[0, 1], 2),
        "V_min": _r(bw[V_min_i, 1], 2), "V_min_t": _r(bw[V_min_i, 0], 1), "I_V_min_aninda": _r(bw[V_min_i, 2], 1),
        "V_son_pencere": _r(bw[-1, 1], 2), "V_toparlanma_disarm_sonrasi": _r(np.median(topar[:, 1]), 2) if len(topar) else None,
        "hucre_V_dinlenme": _r(V_dinl / HUCRE_N, 3), "hucre_V_min": _r(bw[V_min_i, 1] / HUCRE_N, 3),
        "sarkma_V": _r(V_dinl - bw[V_min_i, 1], 2), "sarkma_hucre_V": _r((V_dinl - bw[V_min_i, 1]) / HUCRE_N, 3),
        "sarkma_yuzde": _r(100 * (V_dinl - bw[V_min_i, 1]) / V_dinl, 1),
        "sarkma_tanimi": "sarkma_V = arm ONCESI dinlenme medyani -> pencere min. A/B/D/E ile ayni tanim (pencere ilk BAT ornegi -> min) icin bkz. sarkma_V_pencere_basi; 2026-09-15 curutucu bulgusu",
        "sarkma_V_pencere_basi": _r(bw[0, 1] - bw[V_min_i, 1], 2), "sarkma_hucre_V_pencere_basi": _r((bw[0, 1] - bw[V_min_i, 1]) / HUCRE_N, 3),
        "V_min_BATT_LOW_VOLT_marji_V": _r(bw[V_min_i, 1] - parm.get("BATT_LOW_VOLT", 10.0), 2),
        "motorlu": {"V": ist(bw[bm_mot, 1], 2), "I": ist(bw[bm_mot, 2], 1)} if bm_mot.sum() else None,
        "aski": {"V": ist(bw[bm_aski, 1], 2), "I": ist(bw[bm_aski, 2], 1),
                 "P_W_ort": _r((bw[bm_aski, 1] * bw[bm_aski, 2]).mean(), 1),
                 "P_W_p95": _p(bw[bm_aski, 1] * bw[bm_aski, 2], 95)} if bm_aski.sum() else None,
        "mAh_pencere": _r(bw[-1, 3] - bw[0, 3], 0), "Wh_pencere": _r(Wh, 2),
        "BAT_Res_AP_tahmin_mohm_medyan_motorlu": _r(np.nanmedian(bw[bm_mot, 4]) * 1000, 1) if bm_mot.sum() else None,
        "ic_direnc_fit": sarkma_ic_direnc(bw, bm_mot),
        "BATT_AMP_PERVLT": parm.get("BATT_AMP_PERVLT"), "BATT_VOLT_MULT": parm.get("BATT_VOLT_MULT"),
    }
    if out["pil"]["aski"]:
        I = out["pil"]["aski"]["I"]["ort"]
        out["pil"]["ucus_suresi_tahmini"] = {
            "varsayim": f"{PIL_MAH:.0f} mAh 3S (kullanici beyani), %{KULLANILABILIR*100:.0f} kullanilabilir = {PIL_MAH*KULLANILABILIR:.0f} mAh, sabit aski akimi",
            "aski_dk": _r(PIL_MAH * KULLANILABILIR / I * 60 / 1000, 1),
            "not": "yalniz askida; manevra/ruzgar/kalkis-inis yok. Gerilim sarkmasi BATT_LOW_VOLT=10 V'u daha erken tetikleyebilir (bkz. V_min marji)"}
    # --- titresim
    v = dilim(ham["vibe"], t0, t1)
    vib = {"kapsam_notu": "VIBE = ucus denetleyicisinin tam hizli ivmeolcerden hesapladigi std (m/s2); 25 Hz IMU kaydindan bagimsiz"}
    for kap, mk in (("aski", aski), ("motorlu", motorlu), ("yer_temasi", yer)):
        vm = maske_tasi(ct, mk, v[:, 0])
        if vm.sum() == 0:
            vib[kap] = None
            continue
        d = {}
        for inst in (0, 1):
            vi = v[vm & (v[:, 1] == inst)]
            if len(vi):
                d[f"IMU{inst}"] = {"X": ist(vi[:, 2], 1), "Y": ist(vi[:, 3], 1), "Z": ist(vi[:, 4], 1),
                                   "clip_artisi": int(vi[-1, 5] - vi[0, 5])}
        vv = v[vm]
        d["birlesik"] = {"X": ist(vv[:, 2], 1), "Y": ist(vv[:, 3], 1), "Z": ist(vv[:, 4], 1)}
        vib[kap] = d
    # gaz-titresim iliskisi (askida): VibeZ ~ a + b*ThO
    vm = maske_tasi(ct, aski, v[:, 0])
    if vm.sum() >= 20:
        tho_v = np.interp(v[vm, 0], ct, tho)
        b1, b0 = np.polyfit(tho_v, v[vm, 4], 1)
        r = float(np.corrcoef(tho_v, v[vm, 4])[0, 1])
        vib["aski_VibeZ_vs_ThO"] = {"egim_ms2_per_ThO": _r(b1, 1), "korelasyon_r": _r(r, 2),
                                    "ThO_aralik": [_r(tho_v.min()), _r(tho_v.max())], "n": int(vm.sum())}
    out["vibe"] = vib
    # --- IMU FFT (25 Hz)
    fft = None
    if dilim_t:
        fft = {"dilim_t": dilim_t}
        for inst, arr in sorted(ham["imu"].items()):
            a = dilim(arr, dilim_t[0], dilim_t[1])
            fft[f"IMU{inst}"] = {}
            for ad, col in (("AccX", 4), ("AccY", 5), ("AccZ", 6), ("GyrX", 1), ("GyrY", 2), ("GyrZ", 3)):
                fft[f"IMU{inst}"][ad] = UBA.imu_fft(a[:, 0], a[:, col], tepe_n=4)
        fft["not"] = ("IMU 25 Hz (Nyquist 12,5 Hz): pervane temel/pal-gecis frekansi (>50 Hz) COZULEMEZ; "
                      "ESC/RPM mesaji yok. Tepeler govde/kontrol bandidir. INS_ACCEL_FILTER=20 Hz + decimation "
                      "yuksek frekansi zaten bastirir. Pervane bandi icin INS_LOG_BAT_MASK=1, INS_LOG_BAT_OPT=0/2 gerekir")
    out["imu_fft"] = fft
    # --- motor dengesi (gercek motor fonksiyonlari)
    r = dilim(ham["rcou"], t0, t1)
    rm = maske_tasi(ct, aski, r[:, 0]) if aski.sum() else np.zeros(len(r), bool)
    mot = {"kanal_eslemesi": {m: f"SERVO{aux[m]} (AUX{aux[m]-8}) -> RCOU.C{aux[m]}" for m in sorted(aux)},
           "kapsam": "aski" if rm.sum() else "pencere"}
    if rm.sum() == 0:
        rm = np.ones(len(r), bool)
    pwm = {}
    for m in sorted(aux):
        col = aux[m]
        pwm[m] = r[rm, col]
        mot[m] = {"konum": MOTOR_KONUM[m], **ist(r[rm, col], 0)}
    if len(pwm) == 4:
        M = np.vstack([pwm["M1"], pwm["M2"], pwm["M3"], pwm["M4"]])
        ortlar = M.mean(1)
        en_yuksek = np.argmax(M, 0)
        mot["yayilim_pwm"] = _r(ortlar.max() - ortlar.min(), 0)
        mot["yayilim_pct_aralik"] = _r((ortlar.max() - ortlar.min()) / 10.0, 1)
        mot["en_yuksek_ort"] = f"M{int(np.argmax(ortlar))+1}"
        mot["en_yuksek_olma_orani"] = {f"M{i+1}": _r(np.mean(en_yuksek == i), 2) for i in range(4)}
        # X karisim bilesenleri (PWM): sag-sol, on-arka, CCW-CW — TOPLAM olcegi (A/D/E/F ile ayni; onceki surum /2 idi, 2026-09-15 curutucu bulgusu)
        mot["karisim_bileseni_pwm"] = {
            "roll_sag_eksi_sol": _r(((pwm["M1"] + pwm["M4"]) - (pwm["M2"] + pwm["M3"])).mean(), 1),
            "pitch_on_eksi_arka": _r(((pwm["M1"] + pwm["M3"]) - (pwm["M2"] + pwm["M4"])).mean(), 1),
            "yaw_CCW_eksi_CW": _r(((pwm["M1"] + pwm["M2"]) - (pwm["M3"] + pwm["M4"])).mean(), 1),
            "olcek": "TOPLAM: (M1+M4)-(M2+M3), (M1+M3)-(M2+M4), (M1+M2)-(M3+M4) us — A/D/E/F ile ayni; motor basina ort fark = yarisi",
            "not": "pozitif = ilk grup daha yuksek PWM. FRAME_TYPE=1 X: M1 on-sag, M2 arka-sol, M3 on-sol, M4 arka-sag"}
        mot["doygunluk"] = {"maks_pwm_pencere": int(r[:, [aux[m] for m in sorted(aux)]].max()),
                            "MOT_SPIN_MAX_pwm": int(parm["MOT_PWM_MIN"] + parm["MOT_SPIN_MAX"] * (parm["MOT_PWM_MAX"] - parm["MOT_PWM_MIN"]))}
    mb = dilim(ham["motb"], t0, t1)
    if len(mb):
        mot["MOTB"] = {"ThLimit_min": _r(mb[:, 3].min(), 3), "LiftMax_min": _r(mb[:, 1].min(), 3),
                       "ThrAvMx_ort": _r(mb[:, 4].mean(), 3)}
    out["motor_dengesi"] = mot
    # --- tutum
    a = dilim(ham["att"], t0, t1)
    am = maske_tasi(ct, motorlu, a[:, 0]); aa = maske_tasi(ct, aski, a[:, 0])
    def att_ist(mk):
        if mk.sum() == 0:
            return None
        er, ep = a[mk, 2] - a[mk, 1], a[mk, 4] - a[mk, 3]
        ey = (a[mk, 6] - a[mk, 5] + 180) % 360 - 180
        i_r, i_p = int(np.argmax(np.abs(er))), int(np.argmax(np.abs(ep)))
        return {"n": int(mk.sum()),
                "roll_rms_hata_deg": _r(np.sqrt(np.mean(er ** 2)), 2), "pitch_rms_hata_deg": _r(np.sqrt(np.mean(ep ** 2)), 2),
                "yaw_rms_hata_deg": _r(np.sqrt(np.mean(ey ** 2)), 2),
                "roll_maks_hata_deg": _r(er[i_r], 1), "roll_maks_hata_t": _r(a[mk, 0][i_r], 1),
                "pitch_maks_hata_deg": _r(ep[i_p], 1), "pitch_maks_hata_t": _r(a[mk, 0][i_p], 1),
                "roll_ort_deg": _r(a[mk, 2].mean(), 2), "pitch_ort_deg": _r(a[mk, 4].mean(), 2),
                "roll_abs_maks_deg": _r(np.abs(a[mk, 2]).max(), 1), "pitch_abs_maks_deg": _r(np.abs(a[mk, 4]).max(), 1),
                "pitch_abs_maks_t": _r(a[mk, 0][int(np.argmax(np.abs(a[mk, 4])))], 1),
                "ErrRP_ort": _r(a[mk, 7].mean(), 3), "ErrRP_maks": _r(a[mk, 7].max(), 3)}
    out["tutum"] = {"motorlu": att_ist(am), "aski": att_ist(aa),
                    "not": "hata = ATT.Roll-DesRoll, Pitch-DesPitch (deg); ErrRP = AP tutum hata olcusu (0-1)"}
    # yaw: pilot komutu mu, bozucu mu?
    rw = dilim(ham["rate"], t0, t1)
    if len(rw) and am.sum():
        rm = maske_tasi(ct, motorlu, rw[:, 0])
        rc_w = dilim(ham["rcin"], t0, t1)
        rc4 = np.interp(rw[rm, 0], rc_w[:, 0], rc_w[:, 4]) if len(rc_w) else np.full(rm.sum(), 1500.0)
        dy = (np.diff(a[:, 5]) + 180) % 360 - 180; dyy = (np.diff(a[:, 6]) + 180) % 360 - 180
        ey = (a[am, 6] - a[am, 5] + 180) % 360 - 180
        out["tutum"]["yaw"] = {
            "kapsam": "motorlu", "RC4_yaw_cubugu_aktif_orani": _r(np.mean(np.abs(rc4 - 1500) > parm.get("RC4_DZ", 20)), 2),
            "DesYaw_toplam_degisim_deg": _r(np.abs(dy[am[1:]]).sum(), 0), "Yaw_toplam_degisim_deg": _r(np.abs(dyy[am[1:]]).sum(), 0),
            "RATE_YDes_rms_degs": _r(np.sqrt(np.mean(rw[rm, 7] ** 2)), 1), "RATE_Y_rms_degs": _r(np.sqrt(np.mean(rw[rm, 8] ** 2)), 1),
            "RATE_YOut_ort": _r(rw[rm, 9].mean(), 3), "RATE_YOut_p95_abs": _r(np.percentile(np.abs(rw[rm, 9]), 95), 3),
            "RATE_YOut_maks_abs": _r(np.abs(rw[rm, 9]).max(), 3),
            "yaw_hata_abs_gt10_orani": _r(np.mean(np.abs(ey) > 10), 2), "yaw_hata_min_deg": _r(ey.min(), 1), "yaw_hata_maks_deg": _r(ey.max(), 1),
            "MOT_YAW_HEADROOM": parm.get("MOT_YAW_HEADROOM"), "ATC_RAT_YAW_P": parm.get("ATC_RAT_YAW_P"), "ATC_RAT_YAW_I": parm.get("ATC_RAT_YAW_I")}
    # --- EKF
    e = dilim(ham["ekf"], t0, t1)
    ekf = {"tip": "XKF4", "innov_esik": UBA.EKF_INNOV_ESIK, "cekirdek": {}}
    for core in sorted(set(e[:, 1].astype(int))):
        ec = e[e[:, 1] == core]
        ekf["cekirdek"][str(core)] = {"n": int(len(ec)),
                                      "SV_maks": _r(ec[:, 2].max(), 2), "SP_maks": _r(ec[:, 3].max(), 2),
                                      "SH_maks": _r(ec[:, 4].max(), 2), "SM_maks": _r(ec[:, 5].max(), 2),
                                      "SV_ort": _r(ec[:, 2].mean(), 2), "SM_ort": _r(ec[:, 5].mean(), 2),
                                      "errRP_maks": _r(ec[:, 6].max(), 3),
                                      "innov_dusen_n": int(((ec[:, 2:6] > UBA.EKF_INNOV_ESIK).any(1)).sum())}
    pi = e[:, 7].astype(int)
    ekf["primary_core_degisim_n"] = int((np.diff(pi) != 0).sum()) if len(pi) > 1 else 0
    g = dilim(ham["gps"], t0, t1)
    if len(g):
        ekf["gps"] = {"Status_min": int(g[:, 1].min()), "NSats_min": int(g[:, 2].min()), "NSats_medyan": _r(np.median(g[:, 2]), 0),
                      "HDop_maks": _r(g[:, 3].max(), 2)}
    out["ekf"] = ekf
    # --- olaylar (pencere ici)
    ol = []
    for t, i in ham["ev"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ol.append([_r(t, 1), "EV", UBA.EV_AD.get(i, f"EV{i}")])
    for t, mn, rsn in ham["mode"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ol.append([_r(t, 1), "MODE", f"{UBA.MODE_AD.get(mn, mn)} <{UBA.RSN_AD.get(rsn, rsn)}>"])
    for t, s, c in ham["err"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ol.append([_r(t, 1), "ERR", f"{UBA.ERR_SUBSYS_AD.get(s, s)}={c}"])
    for t, m in ham["msg"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ol.append([_r(t, 1), "MSG", m])
    for t, st, me in ham["arm"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ol.append([_r(t, 1), "ARM", f"{'ARM' if st else 'DISARM'} {UBA.ARM_METHOD_AD.get(me, me)}"])
    ol.sort(key=lambda x: x[0])
    out["olaylar"] = ol
    out["failsafe_n"] = sum(1 for t, s, c in ham["err"] if t0 <= t <= t1 and s in UBA.ERR_FAILSAFE_SUBSYS and c != 0)
    out["_ic"] = {"ct": ct, "tho": tho, "thh": thh, "alt_rel": alt_rel, "aski": aski, "motorlu": motorlu, "dilim_t": dilim_t}
    return out


def log_analiz(yol, tum_kayit):
    ham = oku(yol)
    parm = ham["parm"]
    fn_map, aux = motor_kanallari(parm)
    ucuslar = [pencere_analiz(ham, u, parm, fn_map, aux) for u in tum_kayit["ucuslar"]]
    # pencere disi olaylar
    pencere = [(u["arm_t"], u["disarm_t"]) for u in tum_kayit["ucuslar"]]
    def disarida(t):
        return not any(a - 0.5 <= t <= b + 0.5 for a, b in pencere)
    dis = []
    for t, s, c in ham["err"]:
        if disarida(t):
            dis.append([_r(t, 1), "ERR", f"{UBA.ERR_SUBSYS_AD.get(s, s)}={c}"])
    for t, m in ham["msg"]:
        if disarida(t):
            dis.append([_r(t, 1), "MSG", m])
    for t, i in ham["ev"]:
        if disarida(t):
            dis.append([_r(t, 1), "EV", UBA.EV_AD.get(i, f"EV{i}")])
    dis.sort(key=lambda x: x[0])
    pm = ham["pm"]
    return {
        "dosya": str(yol.relative_to(KOK)).replace("\\", "/"), "mp_no": tum_kayit["mp_no"], "sha256": tum_kayit["sha256"],
        "yazilim": ham["ver"], "STAT_BOOTCNT": parm.get("STAT_BOOTCNT"), "STAT_FLTTIME_ilk_s": tum_kayit["sira"]["STAT_FLTTIME_ilk_s"],
        "hucre": tum_kayit["hucre"], "kullanici_beyani": tum_kayit["kullanici_beyani"],
        "MOT_THST_HOVER_son": parm.get("MOT_THST_HOVER"), "parm_degisim": ham["parm_degisim"],
        "servo_fonksiyon": {f"SERVO{n}": int(parm[f"SERVO{n}_FUNCTION"]) for n in range(1, 17) if f"SERVO{n}_FUNCTION" in parm},
        "motor_fonksiyon_kanallari": fn_map, "esc_kanallari_aux": {m: f"SERVO{n}" for m, n in aux.items()},
        "imu_kayit_hz": _r(1.0 / np.median(np.diff(ham["imu"][0][:, 0])), 1) if 0 in ham["imu"] else None,
        "cpu": {"PM_Load_maks_binde": int(pm[:, 2].max()) if len(pm) else None, "NLon_toplam": int(pm[:, 1].sum()) if len(pm) else None},
        "ucuslar": ucuslar, "pencere_disi_olaylar": dis, "_ham": ham,
    }


# ----------------------------------------------------------------------------- grafikler
def _stil(ax, baslik=None, ylab=None):
    ax.set_facecolor(YUZEY)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.grid(True, axis="y", color=IZGARA, linewidth=0.8)
    ax.tick_params(colors=SOLUK, labelsize=8)
    if baslik:
        ax.set_title(baslik, loc="left", fontsize=10, color=MUREKKEP)
    if ylab:
        ax.set_ylabel(ylab, color=IKINCIL, fontsize=9)


def _golge(ax, ucuslar):
    for u in ucuslar:
        ic = u["_ic"]
        ax.axvspan(u["arm_t"], u["disarm_t"], color="#f0efec", zorder=0)
        if ic["aski"].sum():
            t = ic["ct"][ic["aski"]]
            ax.axvspan(t.min(), t.max(), color="#cde2fb", alpha=0.6, zorder=0)


def ciz_zaman(L, plt):
    ham, uc = L["_ham"], L["ucuslar"]
    t0 = min(u["arm_t"] for u in uc) - 5; t1 = max(u["disarm_t"] for u in uc) + 5
    c, b = dilim(ham["ctun"], t0, t1), dilim(ham["bat"], t0, t1)
    fig, ax = plt.subplots(4, 1, figsize=(11, 9), sharex=True, facecolor=YUZEY)
    for a in ax: _golge(a, uc)
    ax[0].plot(c[:, 0], c[:, 1], color=SERI[0], lw=1.5, label="CTUN.ThO (cikis gazi)")
    ax[0].plot(c[:, 0], c[:, 2], color=SERI[1], lw=2, label="CTUN.ThH (ogrenilen aski gazi)")
    ax[0].axhline(UBA.MOTORLU_THO_ESIK, color=SOLUK, lw=0.8, ls="--")
    _stil(ax[0], f"MP #{L['mp_no']} {Path(L['dosya']).name} — gaz", "0-1"); ax[0].legend(fontsize=8, frameon=False, loc="center right"); ax[0].set_ylim(-0.02, 0.8)
    ax[1].plot(c[:, 0], c[:, 3] - c[0, 3], color=SERI[2], lw=1.5); _stil(ax[1], "CTUN.Alt (ilk ornege gore)", "m")
    ax[2].plot(b[:, 0], b[:, 2], color=SERI[1], lw=1.5); _stil(ax[2], "BAT.Curr", "A")
    ax[3].plot(b[:, 0], b[:, 1], color=SERI[0], lw=1.5); ax[3].axhline(ham["parm"].get("BATT_LOW_VOLT", 10), color=RENK["kirmizi"], lw=0.8, ls="--")
    _stil(ax[3], "BAT.Volt (kirmizi kesik: BATT_LOW_VOLT)", "V"); ax[3].set_xlabel("log zamani (s) — gri: arm penceresi, mavi: aski orneklemi", color=IKINCIL, fontsize=9)
    for u in uc:
        ax[0].annotate(f"ucus {u['no']} ({u['tur']})", (u["arm_t"], 0.72), fontsize=8, color=IKINCIL)
    fig.tight_layout(); p = CIKTI / f"zaman_ThO_akim_gerilim_mp{L['mp_no']}.png"; fig.savefig(p, dpi=140); plt.close(fig); return p.name


def ciz_vibe(L, plt):
    ham, uc = L["_ham"], L["ucuslar"]
    t0 = min(u["arm_t"] for u in uc) - 5; t1 = max(u["disarm_t"] for u in uc) + 5
    v = dilim(ham["vibe"], t0, t1)
    fig, ax = plt.subplots(3, 1, figsize=(11, 7.5), sharex=True, facecolor=YUZEY)
    for k, (ad, col) in enumerate((("VibeX", 2), ("VibeY", 3), ("VibeZ", 4))):
        _golge(ax[k], uc)
        for inst in (0, 1):
            vi = v[v[:, 1] == inst]
            ax[k].plot(vi[:, 0], vi[:, col], color=SERI[inst], lw=1.2, label=f"IMU{inst}")
        ax[k].axhline(30, color=RENK["kirmizi"], lw=0.8, ls="--")
        _stil(ax[k], f"VIBE.{ad} (kirmizi kesik: 30 m/s2 AP uyari esigi)", "m/s2")
    ax[0].legend(fontsize=8, frameon=False, loc="upper right")
    ax[2].set_xlabel("log zamani (s) — gri: arm penceresi, mavi: aski orneklemi", color=IKINCIL, fontsize=9)
    fig.suptitle(f"MP #{L['mp_no']} {Path(L['dosya']).name} — titresim", x=0.01, ha="left", fontsize=11, color=MUREKKEP)
    fig.tight_layout(); p = CIKTI / f"vibe_xyz_mp{L['mp_no']}.png"; fig.savefig(p, dpi=140); plt.close(fig); return p.name


def ciz_rcou(L, plt):
    ham, uc = L["_ham"], L["ucuslar"]
    aux = {m: int(s[5:]) for m, s in L["esc_kanallari_aux"].items()}
    t0 = min(u["arm_t"] for u in uc) - 5; t1 = max(u["disarm_t"] for u in uc) + 5
    r = dilim(ham["rcou"], t0, t1)
    fig, ax = plt.subplots(1, 1, figsize=(11, 4.8), facecolor=YUZEY)
    _golge(ax, uc)
    for k, m in enumerate(("M1", "M2", "M3", "M4")):
        ax.plot(r[:, 0], r[:, aux[m]], color=SERI[k], lw=1.2, label=f"{m} {MOTOR_KONUM[m]} = RCOU.C{aux[m]} (AUX{aux[m]-8})")
    _stil(ax, f"MP #{L['mp_no']} {Path(L['dosya']).name} — motor PWM (SERVOn_FUNCTION 33-36 ile eslendi)", "PWM (us)")
    ax.legend(fontsize=8, frameon=False, loc="lower right"); ax.set_xlabel("log zamani (s)", color=IKINCIL, fontsize=9)
    fig.tight_layout(); p = CIKTI / f"rcou_motorlar_mp{L['mp_no']}.png"; fig.savefig(p, dpi=140); plt.close(fig); return p.name


def ciz_fft(L, plt):
    ham = L["_ham"]; adlar = []
    for u in L["ucuslar"]:
        if not u.get("imu_fft"):
            continue
        d = u["imu_fft"]["dilim_t"]
        fig, ax = plt.subplots(2, 1, figsize=(10, 6.5), facecolor=YUZEY)
        for k, (ad, col) in enumerate((("AccZ", 6), ("GyrX", 1))):
            for inst in (0, 1):
                a = dilim(ham["imu"][inst], d[0], d[1])
                n = len(a); w = np.hanning(n); x = (a[:, col] - a[:, col].mean()) * w
                dt = float(np.median(np.diff(a[:, 0]))); f = np.fft.rfftfreq(n, dt); g = 2 * np.abs(np.fft.rfft(x)) / w.sum(); g[0] = 0
                ax[k].plot(f, g, color=SERI[inst], lw=1.2, label=f"IMU{inst}")
            _stil(ax[k], f"IMU.{ad} genlik spektrumu — aski dilimi {d[0]:.1f}-{d[1]:.1f} s (Hann, 25 Hz ornekleme, Nyquist 12,5 Hz)",
                  "m/s2" if ad.startswith("Acc") else "rad/s")
            ax[k].legend(fontsize=8, frameon=False)
        ax[1].set_xlabel("Hz — pervane bandi (>50 Hz) bu kayitta COZULEMEZ", color=IKINCIL, fontsize=9)
        fig.suptitle(f"MP #{L['mp_no']} ucus {u['no']}", x=0.01, ha="left", fontsize=11, color=MUREKKEP)
        fig.tight_layout(); p = CIKTI / f"fft_aski_mp{L['mp_no']}_ucus{u['no']}.png"; fig.savefig(p, dpi=140); plt.close(fig); adlar.append(p.name)
    return adlar


def ciz_karsilastirma(C_ucuslar, taban, plt):
    """C ucuslari (3 nokta) ve A/D tabani: aski ThO, akim, guc, VibeZ."""
    fig, ax = plt.subplots(1, 4, figsize=(13, 4), facecolor=YUZEY)
    olcum = [("ThO_aski", "aski gazi ThO"), ("I_aski", "aski akimi (A)"), ("P_aski", "aski gucu (W)"), ("VibeZ_aski", "VibeZ aski (m/s2)")]
    gruplar = [("A 3S+1045", taban["A"], SERI[0]), ("C 3S+9x5x3", C_ucuslar, SERI[1]), ("D 4S+9x5x3", taban["D"], SERI[2])]
    for k, (anahtar, baslik) in enumerate(olcum):
        for gi, (ad, satirlar, renk) in enumerate(gruplar):
            y = [s[anahtar] for s in satirlar if s.get(anahtar) is not None]
            x = np.full(len(y), gi) + np.linspace(-0.18, 0.18, len(y)) if len(y) > 1 else [gi]
            ax[k].scatter(x, y, s=36, color=renk, edgecolor=YUZEY, linewidth=1, zorder=3)
            if y:
                ax[k].hlines(np.median(y), gi - 0.3, gi + 0.3, color=renk, lw=2)
        ax[k].set_xticks(range(3)); ax[k].set_xticklabels([g[0] for g in gruplar], fontsize=8)
        _stil(ax[k], baslik)
    fig.suptitle("Askida olcumler, ucus basina bir nokta; cizgi = medyan (A/D: tum_loglar.json; C: bu analiz). "
                 "Pil/pervane/kutle = kullanici beyani", x=0.01, ha="left", fontsize=9, color=IKINCIL)
    fig.tight_layout(); p = CIKTI / "karsilastirma_A_C_D_aski.png"; fig.savefig(p, dpi=140); plt.close(fig); return p.name


# ----------------------------------------------------------------------------- ana
def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tum = json.loads(TUM_JSON.read_text(encoding="utf-8"))
    kayitlar = {l["dosya"]: l for l in tum["loglar"]}
    sonuc = []
    grafikler = []
    for yol in LOGLAR:
        rel = str(yol.relative_to(KOK)).replace("\\", "/")
        L = log_analiz(yol, kayitlar[rel])
        grafikler += [ciz_zaman(L, plt), ciz_vibe(L, plt), ciz_rcou(L, plt)] + ciz_fft(L, plt)
        sonuc.append(L)
        print(f"[ok] {rel}: {len(L['ucuslar'])} pencere")

    # --- konfigurasyon toplamlari (yalniz 'ucus' ve aski orneklemi olanlar)
    ucus_c = [u for L in sonuc for u in L["ucuslar"] if u["tur"] == "ucus" and u["gaz"]["ThO_aski"]]
    def agirlikli(anahtar_fn):
        w = np.array([u["aski_n"] for u in ucus_c], float); x = np.array([anahtar_fn(u) for u in ucus_c], float)
        return _r((w * x).sum() / w.sum())
    C_satir = [{"log": Path(L["dosya"]).name, "ucus": u["no"], "aski_s": u["aski_s"], "ThO_aski": u["gaz"]["ThO_aski"]["ort"],
                "ThO_p50": u["gaz"]["ThO_aski"]["p50"], "V_aski": u["pil"]["aski"]["V"]["ort"], "I_aski": u["pil"]["aski"]["I"]["ort"],
                "P_aski": u["pil"]["aski"]["P_W_ort"], "VibeZ_aski": u["vibe"]["aski"]["birlesik"]["Z"]["ort"],
                "VibeX_aski": u["vibe"]["aski"]["birlesik"]["X"]["ort"], "VibeY_aski": u["vibe"]["aski"]["birlesik"]["Y"]["ort"],
                "alt_aski_m": u["gaz"]["alt_aski_ort_m"], "ThH_bas": u["ogrenme"]["ThH_bas"], "ThH_son": u["ogrenme"]["ThH_son"]}
               for L, u in ((L, u) for L in sonuc for u in L["ucuslar"]) if u["tur"] == "ucus" and u["gaz"]["ThO_aski"]]
    # A/D tabani (tum_loglar.json)
    taban = {"A": [], "D": [], "B": []}
    for l in tum["loglar"]:
        if l.get("KOPYA_OF"):
            continue
        et = l["kullanici_beyani"]["etiket"]
        if et not in taban:
            continue
        for u in l.get("ucuslar", []):
            if u["tur"] == "ucus" and u.get("aski") and u.get("bat", {}).get("aski"):
                taban[et].append({"log": l["dosya"].split("/")[-1], "ucus": u["no"], "aski_s": u["aski_s"],
                                  "ThO_aski": u["aski"]["ThO_ort"], "V_aski": u["bat"]["aski"]["V_ort"], "I_aski": u["bat"]["aski"]["I_ort"],
                                  "P_aski": u["bat"]["aski"]["P_W"], "VibeZ_aski": u["vibe"]["aski"]["Z"], "VibeX_aski": u["vibe"]["aski"]["X"],
                                  "alt_aski_m": u["aski"]["alt_ort_m"]})
    grafikler.append(ciz_karsilastirma(C_satir, taban, plt))
    def taban_ozet(satirlar):
        if not satirlar:
            return None
        w = np.array([s["aski_s"] for s in satirlar], float)
        f = lambda k: _r((w * np.array([s[k] for s in satirlar], float)).sum() / w.sum(), 3)  # noqa: E731
        return {"ucus_n": len(satirlar), "aski_toplam_s": _r(w.sum(), 1), "ThO_aski_agirlikli": f("ThO_aski"),
                "V_aski_agirlikli": f("V_aski"), "I_aski_agirlikli": f("I_aski"), "P_aski_agirlikli_W": f("P_aski"),
                "VibeZ_aski_agirlikli": f("VibeZ_aski"), "VibeX_aski_agirlikli": f("VibeX_aski"),
                "VibeZ_aralik": [min(s["VibeZ_aski"] for s in satirlar), max(s["VibeZ_aski"] for s in satirlar)],
                "ThO_aralik": [min(s["ThO_aski"] for s in satirlar), max(s["ThO_aski"] for s in satirlar)],
                "P_aralik_W": [min(s["P_aski"] for s in satirlar), max(s["P_aski"] for s in satirlar)]}

    aski_toplam = sum(u["aski_s"] for u in ucus_c)
    I_ag = agirlikli(lambda u: u["pil"]["aski"]["I"]["ort"])
    konfig = {
        "etiket": "C", "pil": "3S (ilk BAT gerilimi 12,44 / 12,09 V -> 3 hucre; kapasite 8000 mAh = kullanici beyani + BATT_CAPACITY)",
        "pervane": "9x5x3 (kullanici beyani; logda yok)", "kutle": "BILINMIYOR (logda yok, beyan yok)",
        "ucus_n": len(ucus_c), "kisa_sicrama_n": sum(1 for L in sonuc for u in L["ucuslar"] if u["tur"] == "kisa_sicrama"),
        "arm_yalniz_n": sum(1 for L in sonuc for u in L["ucuslar"] if u["tur"] == "arm_yalniz"),
        "askida_toplam_s": _r(aski_toplam, 1), "motorlu_toplam_s": _r(sum(u["motorlu_s"] for L in sonuc for u in L["ucuslar"]), 1),
        "aski_ThO_agirlikli_ort": agirlikli(lambda u: u["gaz"]["ThO_aski"]["ort"]),
        "aski_ThO_ucus_basina": [u["gaz"]["ThO_aski"]["ort"] for u in ucus_c],
        "aski_ThO_p50_ucus_basina": [u["gaz"]["ThO_aski"]["p50"] for u in ucus_c],
        "aski_V_agirlikli": agirlikli(lambda u: u["pil"]["aski"]["V"]["ort"]),
        "aski_I_agirlikli_A": I_ag, "aski_I_ucus_basina_A": [u["pil"]["aski"]["I"]["ort"] for u in ucus_c],
        "aski_P_agirlikli_W": agirlikli(lambda u: u["pil"]["aski"]["P_W_ort"]),
        "aski_P_ucus_basina_W": [u["pil"]["aski"]["P_W_ort"] for u in ucus_c],
        "ucus_suresi_tahmini_dk_(6400_mAh/I_aski)": {"agirlikli": _r(6400 / I_ag * 60 / 1000, 1),
                                                     "ucus_basina": [_r(6400 / u["pil"]["aski"]["I"]["ort"] * 60 / 1000, 1) for u in ucus_c]},
        "MOT_THST_HOVER": {"13_Eylul_sonu": 0.532559, "mp68_ucus1_sonu": 0.515692, "mp68_ucus2_sonu": 0.49768, "mp69_ucus2_sonu": 0.506167,
                           "15_Eylul_mp_11-14-33_bas": kayitlar["results/ucus_20260915/2026-09-15 11-14-33.bin"]["parm"]["MOT_THST_HOVER"],
                           "kaynak": "PARM MOT_THST_HOVER degisim kayitlari (bu loglar + tum_loglar.json D kaydi)"},
        "vibe_aski_birlesik": {ek: ist(np.concatenate([np.array([u["vibe"]["aski"]["birlesik"][ek]["ort"]]) for u in ucus_c]), 1)
                               for ek in ("X", "Y", "Z")},
        "clip_toplam": sum(u["vibe"]["motorlu"][f"IMU{i}"]["clip_artisi"] for u in ucus_c for i in (0, 1) if u["vibe"]["motorlu"].get(f"IMU{i}")),
        "taban_A_3S_1045": taban_ozet(taban["A"]), "taban_D_4S_9x5x3": taban_ozet(taban["D"]),
        "taban_B_4S_1045": taban_ozet(taban["B"]) or "askida olcum yok (yalniz kisa sicramalar)",
    }
    meta = {
        "uretim_zamani": _dt.datetime.now().isoformat(timespec="seconds"), "betik": "results/ucus_analiz_20260915/C_3S_9x5x3/analiz_C.py",
        "girdi": [str(p.relative_to(KOK)).replace("\\", "/") for p in LOGLAR] + [str(TUM_JSON.relative_to(KOK)).replace("\\", "/")],
        "olcutler": tum["meta"]["olcutler"], "ek_olcutler": {"yer_temasi": f"motorlu ve irtifa < {YER_TEMASI_ALT_M} m (kalkis/inis dilimi; askidan ayri)",
                                                             "hover_TC_s": HOVER_TC_S, "pil_mAh": PIL_MAH, "kullanilabilir": KULLANILABILIR},
        "uyari_rcou": ("tum_loglar.json 'rcou.C1_C4_ort' bu aracta MOTOR DENGESI DEGILDIR: SERVO1/2/4/5/8_FUNCTION=34 (Motor2), "
                       "SERVO3/7=33 (Motor1), SERVO6=36 (Motor4); ESC'ler AUX1-4 = SERVO9-12 (36,34,33,35). C1=C2=C4 %100 ozdes "
                       "(olculdu). Bu analizde motorlar SERVOn_FUNCTION ile eslendi: M1=C11, M2=C10, M3=C12, M4=C9"),
        "beyan_notu": tum["meta"]["beyan_notu"],
    }
    ozet = {"meta": meta, "konfig_C": konfig, "C_ucus_satirlari": C_satir, "taban_satirlari": taban,
            "loglar": [{k: v for k, v in L.items() if k != "_ham"} for L in sonuc], "grafikler": grafikler}
    for L in ozet["loglar"]:
        for u in L["ucuslar"]:
            u.pop("_ic", None)
    (CIKTI / "ozet.json").write_text(json.dumps(UBA._temiz(ozet), ensure_ascii=False, indent=1), encoding="utf-8")
    print("[ok] ozet.json + grafikler:", grafikler)
    return 0


if __name__ == "__main__":
    sys.exit(main())
