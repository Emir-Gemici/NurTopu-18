#!/usr/bin/env python3
"""E) 15 Eylul 2026 12-40-55 logu — TAM GAZ dikey kalkis: ivme / tirmanma hizi / T-W alt siniri / pil sarkmasi.

Girdi : results/ucus_20260915/2026-09-15 12-40-55.bin
        4S pil + 9x5x3 pervane = KULLANICI BEYANI (logda yok). Kutle logda YOK -> mutlak itki hesaplanmaz.
Cikti : bu dizin — ozet.json + PNG'ler.

HER SAYI LOGDAN. Bagimlilik: pymavlink (DFReader), numpy, matplotlib. SciPy YOK (anayasa m.4).

Yontem ozeti
  t0        : ilk CTUN ornegi ThO >= 0,15 (motorlu esik, D-482 yontemi). Ayrica RCIN.C3 > 1500 ve RCOU.C9 > 1150 anlari yazilir.
  hiz       : XKF1.VD (birincil EKF cekirdegi, XKF4.PI) isareti ters cevrilmis (-VD = yukari +) ve CTUN.CRt/100 (cm/s -> m/s).
  esikler   : her v icin (a) ilk ornek >= v, (b) iki ornek arasi dogrusal ara deger ile kesisme ani.
  ivme      : np.gradient (3-nokta merkezi fark, gercek zaman damgalari) ham; + 3-ornek hareketli ortalama (hafif yumusatma).
  IMU       : IMU.AccZ (25 Hz/orn., INS_ACCEL_FILTER 20 Hz). Kalkis oncesi durgun pencere ortalamasi cikarilir (g + sapma).
              (1) basit: a_up = -(AccZ - AccZ_durgun)   (2) dondurulmus: ATT roll/pitch ile govde -> yer D ekseni.
              5-ornek (0,2 s) hareketli ortalama; ayrica ivme t0'dan itibaren integre edilip XKF1 hiziyla kiyaslanir.
  T/W       : 1 + a_maks/g, g = 9,80665. ALT SINIRDIR (gerekce ozet.json 'TW.neden_alt_sinir').
  pil       : t0..t0+3 s BAT.Volt ~ BAT.Curr, numpy.polyfit(deg=1): R_paket = -egim, V_ac = kesim. BAT.Res (AP tahmini) ile kiyas.
"""
from __future__ import annotations

import collections
import datetime as dt
import hashlib
import json
import math
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
LOG = os.path.join(KOK, "results", "ucus_20260915", "2026-09-15 12-40-55.bin")

G = 9.80665
THO_MOTORLU = 0.15
ESIKLER = [1.0, 2.0, 3.0, 4.0, 5.0]
HAREKET_ESIK = 0.10          # m/s — kalkis oncesi |VD| <= 0,03; 0,10 gurultu tabaninin 3 kati ustunde
ILK3S = 3.0
IMU_YUMUSATMA_N = 5          # 25 Hz -> 0,2 s
HUCRE = 4                    # kullanici beyani 4S; ilk gerilim 15,6 V ile tutarli (3,9 V/hucre)

# dataviz: sabit kategorik sira (blue, orange, aqua, yellow), acik yuzey
C_BLUE, C_ORANGE, C_AQUA, C_YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
C_VIOLET, C_RED = "#4a3aa7", "#e34948"
C_TEXT, C_TEXT2, C_GRID, C_SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": C_SURF, "axes.facecolor": C_SURF, "axes.edgecolor": C_GRID,
    "axes.labelcolor": C_TEXT2, "xtick.color": C_TEXT2, "ytick.color": C_TEXT2,
    "text.color": C_TEXT, "axes.grid": True, "grid.color": C_GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
    "legend.frameon": False, "lines.linewidth": 1.6,
})


def r(x, n=3):
    if x is None:
        return None
    if isinstance(x, (float, np.floating)):
        return None if not np.isfinite(x) else round(float(x), n)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def sha256(fn):
    h = hashlib.sha256()
    with open(fn, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def oku(fn):
    log = DFReader.DFReader_binary(fn)
    D = collections.defaultdict(list)
    parm = {}
    while True:
        m = log.recv_msg()
        if m is None:
            break
        ty = m.get_type()
        if ty == "PARM":
            d = m.to_dict()
            parm[d["Name"]] = d["Value"]
        elif ty in ("CTUN", "XKF1", "XKF4", "BAT", "RCOU", "RCIN", "ATT", "IMU", "MODE", "EV", "ARM",
                    "VER", "GPS", "VIBE", "MSG", "MOTB", "XKF3"):
            D[ty].append(m.to_dict())
    return D, parm


def kolon(lst, ad, sec=None):
    return np.array([d[ad] for d in lst if (sec is None or sec(d))], dtype=float)


def kesisme(t, v, esik, t_bas, t_son):
    """Ilk ornek >= esik (t_bas..t_son icinde) ve dogrusal ara degerle kesisme ani."""
    idx = np.where((t >= t_bas) & (t <= t_son) & (v >= esik))[0]
    if len(idx) == 0:
        return None, None
    i = int(idx[0])
    t_ornek = float(t[i])
    if i == 0 or v[i - 1] >= esik or v[i] == v[i - 1]:
        return t_ornek, t_ornek
    t_ara = float(t[i - 1] + (esik - v[i - 1]) / (v[i] - v[i - 1]) * (t[i] - t[i - 1]))
    return t_ornek, t_ara


def hareketli_ort(x, n):
    if n <= 1:
        return x.copy()
    k = np.ones(n) / n
    y = np.convolve(x, k, mode="same")
    h = n // 2
    for i in range(h):          # kenarlarda daralan pencere
        y[i] = x[: i + h + 1].mean()
        y[-1 - i] = x[-(i + h + 1):].mean()
    return y


def main():
    D, parm = oku(LOG)
    ver = D["VER"][0]["FWS"] if D["VER"] else None
    print("log:", LOG, "| fw:", ver)

    # ------------------------------------------------------------------ zaman serileri
    ct = D["CTUN"]
    t_ct = kolon(ct, "TimeUS") / 1e6
    tho = kolon(ct, "ThO"); thi = kolon(ct, "ThI"); alt = kolon(ct, "Alt"); crt = kolon(ct, "CRt") / 100.0
    thh = kolon(ct, "ThH")

    # birincil EKF cekirdegi (XKF4.PI)
    pi_sayac = collections.Counter(int(d["PI"]) for d in D["XKF4"])
    birincil = pi_sayac.most_common(1)[0][0]
    xk = [d for d in D["XKF1"] if int(d["C"]) == birincil]
    xk_dig = [d for d in D["XKF1"] if int(d["C"]) != birincil]
    t_xk = kolon(xk, "TimeUS") / 1e6
    vz = -kolon(xk, "VD")                      # yukari +
    pd_ = kolon(xk, "PD")
    vn = kolon(xk, "VN"); ve = kolon(xk, "VE")
    t_xk2 = kolon(xk_dig, "TimeUS") / 1e6 if xk_dig else None
    vz2 = -kolon(xk_dig, "VD") if xk_dig else None

    bat = D["BAT"]
    t_b = kolon(bat, "TimeUS") / 1e6; V = kolon(bat, "Volt"); I = kolon(bat, "Curr"); Res = kolon(bat, "Res")
    rc = D["RCOU"]
    t_rc = kolon(rc, "TimeUS") / 1e6
    mot = {f"C{k}": kolon(rc, f"C{k}") for k in (9, 10, 11, 12)}
    rcin = D["RCIN"]
    t_ri = kolon(rcin, "TimeUS") / 1e6; ri3 = kolon(rcin, "C3")
    att = D["ATT"]
    t_att = kolon(att, "TimeUS") / 1e6; roll = kolon(att, "Roll"); pitch = kolon(att, "Pitch")

    # ------------------------------------------------------------------ t0 ve olaylar
    i0 = int(np.where(tho >= THO_MOTORLU)[0][0])
    t0 = float(t_ct[i0])
    t_rcin = float(t_ri[np.where(ri3 > 1500)[0][0]])
    t_rcou = float(t_rc[np.where(mot["C9"] > 1150)[0][0]])
    tam = np.where(tho >= 0.99)[0]
    t_tam_bas, t_tam_son = float(t_ct[tam[0]]), float(t_ct[tam[-1]])
    tam_gaz_suresi = t_tam_son - t_tam_bas + 0.1   # 10 Hz ornek kapsami
    mod_ad = {0: "STABILIZE", 9: "LAND"}
    modlar = [{"t": r(d["TimeUS"] / 1e6 - t0), "t_mutlak": r(d["TimeUS"] / 1e6), "mod": mod_ad.get(int(d["Mode"]), str(d["Mode"])),
               "rsn": int(d["Rsn"])} for d in D["MODE"]]
    ev_ad = {10: "ARMED", 11: "DISARMED", 15: "AUTO_ARMED", 17: "LAND_COMPLETE_MAYBE", 18: "LAND_COMPLETE", 28: "NOT_LANDED",
             56: "MOTORS_INTERLOCK_DISABLED", 57: "MOTORS_INTERLOCK_ENABLED", 62: "EKF_YAW_RESET"}
    olaylar = [{"t": r(d["TimeUS"] / 1e6 - t0), "id": int(d["Id"]), "ad": ev_ad.get(int(d["Id"]), "?")} for d in D["EV"]]
    t_disarm = next((d["TimeUS"] / 1e6 for d in D["EV"] if int(d["Id"]) == 11), None)
    motorlu = np.where(tho >= THO_MOTORLU)[0]
    motorlu_sure = float(len(motorlu) * 0.1)

    # ------------------------------------------------------------------ hiz esikleri
    pen = (t_xk >= t0) & (t_xk <= t0 + 2.0)
    i_tepe_x = int(np.where(pen)[0][np.argmax(vz[pen])])
    tepe_x, t_tepe_x = float(vz[i_tepe_x]), float(t_xk[i_tepe_x])
    penc = (t_ct >= t0) & (t_ct <= t0 + 2.0)
    i_tepe_c = int(np.where(penc)[0][np.argmax(crt[penc])])
    tepe_c, t_tepe_c = float(crt[i_tepe_c]), float(t_ct[i_tepe_c])

    def esik_tablosu(t, v, t_tepe):
        out = {}
        for e in [HAREKET_ESIK] + ESIKLER:
            to, ta = kesisme(t, v, e, t0, t_tepe + 0.05)
            out[f"{e:g}"] = {"ilk_ornek_s": r(None if to is None else to - t0, 2),
                             "ara_deger_s": r(None if ta is None else ta - t0, 3)}
        return out
    esik_x = esik_tablosu(t_xk, vz, t_tepe_x)
    esik_c = esik_tablosu(t_ct, crt, t_tepe_c)
    j = np.array([int(np.argmin(np.abs(t_xk - tt))) for tt in t_ct])
    fark = crt - vz[j]
    kalk = (t_ct >= t0) & (t_ct <= t0 + 2.0)
    kaynak_farki = {"tanim": "CTUN.CRt/100 - (-XKF1.VD birincil), en yakin zaman damgasi eslesmesi, t0..t0+2 s",
                    "maks_mutlak_ms": r(float(np.abs(fark[kalk]).max())), "ort_ms": r(float(fark[kalk].mean())),
                    "zaman_damgasi_farki_maks_ms": r(float(np.abs(t_xk[j] - t_ct).max() * 1000), 1),
                    "esik_sure_farki_s": {k: r(None if (esik_c[k]["ara_deger_s"] is None or esik_x[k]["ara_deger_s"] is None)
                                                else esik_c[k]["ara_deger_s"] - esik_x[k]["ara_deger_s"], 3) for k in esik_x}}
    cekirdek_farki = None
    if vz2 is not None:
        j2 = np.array([int(np.argmin(np.abs(t_xk2 - tt))) for tt in t_xk])
        cekirdek_farki = {"birincil_cekirdek": birincil, "diger_cekirdek_tepe_ms": r(float(vz2[(t_xk2 >= t0) & (t_xk2 <= t0 + 2)].max())),
                          "maks_mutlak_fark_ms": r(float(np.abs(vz[pen] - vz2[j2][pen]).max()))}

    # ------------------------------------------------------------------ irtifa
    taban = float(np.median(alt[(t_ct >= t0 - 1.0) & (t_ct <= t0)]))
    alt_rel = alt - taban
    i_alt_maks = int(np.argmax(alt_rel))
    irtifa = {"taban_m_CTUN_Alt": r(taban), "maks_m": r(float(alt_rel[i_alt_maks]), 2), "maks_t_s": r(float(t_ct[i_alt_maks] - t0), 2),
              "esikler": {}}
    for h in (1.0, 2.0, 3.0, 5.0):
        to, ta = kesisme(t_ct, alt_rel, h, t0, t_ct[i_alt_maks])
        irtifa["esikler"][f"{h:g}m"] = {"ilk_ornek_s": r(None if to is None else to - t0, 2), "ara_deger_s": r(None if ta is None else ta - t0, 3)}
    to, ta = kesisme(t_ct, alt_rel, 0.05, t0, t_ct[i_alt_maks])
    irtifa["ilk_hareket_0p05m_s"] = r(None if to is None else to - t0, 2)
    pd_taban = float(np.median(pd_[(t_xk >= t0 - 1.0) & (t_xk <= t0)]))
    irtifa["XKF1_PD_maks_m"] = r(float((-(pd_ - pd_taban)).max()), 2)
    irtifa["BARO_BAlt_not"] = "CTUN.BAlt kalkista pervane akisi ile 0,9..1,8 m arasi sicrar (t0+0,2..+0,6 s); irtifa icin kullanilmadi"

    # ------------------------------------------------------------------ ivme (EKF turevleri)
    a_x = np.gradient(vz, t_xk)                     # 3-nokta merkezi fark
    a_x_y = hareketli_ort(a_x, 3)
    a_c = np.gradient(crt, t_ct)
    a_c_y = hareketli_ort(a_c, 3)
    pen_a = (t_xk >= t0) & (t_xk <= t0 + 1.5)
    ia = int(np.where(pen_a)[0][np.argmax(a_x[pen_a])]); iay = int(np.where(pen_a)[0][np.argmax(a_x_y[pen_a])])
    pen_ac = (t_ct >= t0) & (t_ct <= t0 + 1.5)
    ic = int(np.where(pen_ac)[0][np.argmax(a_c[pen_ac])]); icy = int(np.where(pen_ac)[0][np.argmax(a_c_y[pen_ac])])
    i_har = int(np.where((t_xk >= t0) & (vz >= HAREKET_ESIK))[0][0])
    a_ort = float((vz[i_tepe_x] - vz[i_har]) / (t_xk[i_tepe_x] - t_xk[i_har]))
    ivme = {
        "yontem": "np.gradient(v, t) = 3-nokta merkezi fark (10 Hz, dt=0,1 s -> etkin pencere 0,2 s); 'yumusak' = ustune 3-ornek hareketli ortalama",
        "XKF1": {"ham_tepe_ms2": r(float(a_x[ia])), "ham_tepe_t_s": r(float(t_xk[ia] - t0), 2),
                 "yumusak_tepe_ms2": r(float(a_x_y[iay])), "yumusak_tepe_t_s": r(float(t_xk[iay] - t0), 2)},
        "CTUN_CRt": {"ham_tepe_ms2": r(float(a_c[ic])), "ham_tepe_t_s": r(float(t_ct[ic] - t0), 2),
                     "yumusak_tepe_ms2": r(float(a_c_y[icy])), "yumusak_tepe_t_s": r(float(t_ct[icy] - t0), 2)},
        "ortalama_hareket_basi_tepe_ms2": r(a_ort), "ortalama_pencere_s": [r(float(t_xk[i_har] - t0), 2), r(float(t_xk[i_tepe_x] - t0), 2)],
        "ham_ornekler_t0dan_ms2": [[r(float(t_xk[k] - t0), 2), r(float(a_x[k]), 2)] for k in range(i0 - 1, i0 + 14) if 0 <= k < len(a_x)],
    }

    # ------------------------------------------------------------------ ivme (IMU ham)
    imu = {}
    imu_ser = {}
    for inst in sorted(set(int(d["I"]) for d in D["IMU"])):
        L = [d for d in D["IMU"] if int(d["I"]) == inst]
        t_i = kolon(L, "TimeUS") / 1e6
        ax, ay, az = kolon(L, "AccX"), kolon(L, "AccY"), kolon(L, "AccZ")
        fs = 1.0 / float(np.median(np.diff(t_i)))
        durgun = (t_i >= t0 - 3.0) & (t_i <= t0 - 0.5)
        az_d = float(az[durgun].mean()); az_sd = float(az[durgun].std())
        a_basit = -(az - az_d)
        rr = np.radians(np.interp(t_i, t_att, roll)); pp = np.radians(np.interp(t_i, t_att, pitch))
        fD = -ax * np.sin(pp) + ay * np.sin(rr) * np.cos(pp) + az * np.cos(rr) * np.cos(pp)
        fD_d = float(fD[durgun].mean())
        a_don = -(fD - fD_d)
        a_basit_y = hareketli_ort(a_basit, IMU_YUMUSATMA_N); a_don_y = hareketli_ort(a_don, IMU_YUMUSATMA_N)
        p = (t_i >= t0) & (t_i <= t0 + 1.5)

        def tepe(a):
            k = int(np.where(p)[0][np.argmax(a[p])])
            return r(float(a[k])), r(float(t_i[k] - t0), 2)
        m = t_i >= t0 - 0.1
        ti, ai = t_i[m], a_don[m]
        v_int = np.concatenate([[0.0], np.cumsum(0.5 * (ai[1:] + ai[:-1]) * np.diff(ti))])
        pi_ = (ti >= t0) & (ti <= t0 + 2.0)
        kv = int(np.where(pi_)[0][np.argmax(v_int[pi_])])
        tilt_maks = float(np.degrees(np.arccos(np.clip(np.cos(rr[p]) * np.cos(pp[p]), -1, 1))).max())
        imu[f"IMU{inst}"] = {
            "ornekleme_hz": r(fs, 1), "durgun_AccZ_ort_ms2": r(az_d), "durgun_AccZ_std_ms2": r(az_sd),
            "durgun_pencere_s": [-3.0, -0.5],
            "basit_ham_tepe_ms2": tepe(a_basit)[0], "basit_yumusak_tepe_ms2": tepe(a_basit_y)[0], "basit_yumusak_tepe_t_s": tepe(a_basit_y)[1],
            "dondurulmus_ham_tepe_ms2": tepe(a_don)[0], "dondurulmus_yumusak_tepe_ms2": tepe(a_don_y)[0], "dondurulmus_yumusak_tepe_t_s": tepe(a_don_y)[1],
            "tilt_maks_deg_t0_1p5s": r(tilt_maks, 1),
            "integre_hiz_tepe_ms": r(float(v_int[kv])), "integre_hiz_tepe_t_s": r(float(ti[kv] - t0), 2),
            "integre_hiz_XKF1_tepe_farki_ms": r(float(v_int[kv]) - tepe_x),
        }
        imu_ser[inst] = (t_i, a_don, a_don_y, ti, v_int)
    imu_not = ("IMU 25 Hz/orn. kaydi, INS_ACCEL_FILTER 20 Hz -> Nyquist 12,5 Hz altinda; titresim katlanir (alias). "
               "Dikey ivme < 2 Hz oldugu icin 0,2 s ortalama ile karsilastirilabilir. Yerde durgun pencere ortalamasi cikarildigi icin "
               "g ve ivmeolcer sapmasi birlikte gider; olcek hatasi kalir.")

    # ------------------------------------------------------------------ T/W
    a_maks = float(a_x[ia])
    tw = {
        "formul": "T/W >= 1 + a_maks/g, g = 9,80665",
        "a_maks_kullanilan_ms2": r(a_maks), "kaynak": "XKF1 -VD, 3-nokta merkezi fark, ham",
        "TW_alt_sinir": r(1 + a_maks / G, 2),
        "TW_alt_sinir_yumusak": r(1 + float(a_x_y[iay]) / G, 2),
        "TW_alt_sinir_IMU_dondurulmus_yumusak": {k: r(1 + v["dondurulmus_yumusak_tepe_ms2"] / G, 2) for k, v in imu.items()},
        "TW_alt_sinir_ortalama_ivme": r(1 + a_ort / G, 2),
        "neden_alt_sinir": [
            "Hava direnci ve pervane ic akisindaki kayiplar ihmal edildi: gercek itki m(g+a)+D, D>0 -> T/W gercek >= 1+a/g.",
            "10 Hz EKF hizi ve 0,2 s merkezi fark tepeyi yayar; anlik tepe ivme olculenden kucuk olamaz (IMU ham 0,2 s ortalama ile kiyas ozet.json'da).",
            "Motorlar SPIN_MAX=0,95 ile 1950 us'de kesildi (RCOU C9 1949 doygun); ESC tam araligi (2000) kullanilmadi.",
            "Pil 14,60 -> 12,36 V'a coktu (3,09 V/hucre); tam gerilimde itki daha yuksek olurdu. MOT_BAT_VOLT_MAX/MIN=0 -> gerilim telafisi kapali.",
            "Tam gaz yalniz 0,8 s tutuldu; hiz tepesi pilotun gazi birakmasiyla sinirlandi (kararli tirmanma hizina ulasilmadi).",
        ],
        "kutle_notu": "Kutle logda yok -> Newton cinsinden itki verilmez. T/W kutleden bagimsizdir.",
    }

    # ------------------------------------------------------------------ pil
    pb = (t_b >= t0) & (t_b <= t0 + ILK3S)
    Vb, Ib, Rb = V[pb], I[pb], Res[pb]
    egim, kesim = np.polyfit(Ib, Vb, 1)
    tahmin = np.polyval([egim, kesim], Ib)
    ss_res = float(((Vb - tahmin) ** 2).sum()); ss_tot = float(((Vb - Vb.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    V0 = float(V[(t_b >= t0 - 3.0) & (t_b <= t0)].mean())
    I0 = float(I[(t_b >= t0 - 3.0) & (t_b <= t0)].mean())
    iI = int(np.where(pb)[0][np.argmax(Ib)])
    i_vmin = int(np.where(pb)[0][np.argmin(Vb)])
    pt = (t_b >= t_tam_bas) & (t_b <= t_tam_son)
    pil = {
        "pencere_s": [0, ILK3S], "hucre_beyan": HUCRE,
        "V0_kalkis_oncesi_ort": r(V0), "V0_hucre": r(V0 / HUCRE),
        "I_maks_A": r(float(I[iI]), 1), "I_maks_t_s": r(float(t_b[iI] - t0), 2), "V_at_Imaks": r(float(V[iI])),
        "V_min": r(float(V[i_vmin])), "V_min_t_s": r(float(t_b[i_vmin] - t0), 2), "V_min_hucre": r(float(V[i_vmin]) / HUCRE),
        "sarkma_V": r(V0 - float(V[i_vmin])), "sarkma_hucre_V": r((V0 - float(V[i_vmin])) / HUCRE),
        "polyfit_V_I": {"egim_ohm": r(float(egim), 4), "R_paket_mohm": r(-float(egim) * 1000, 1), "R_hucre_mohm": r(-float(egim) * 1000 / HUCRE, 1),
                        "V_acik_devre_kesim": r(float(kesim)), "R2": r(r2), "n": int(pb.sum())},
        "tepe_nokta_R_paket_mohm": r((V0 - float(V[i_vmin])) / (float(I[iI]) - I0) * 1000, 1),
        "BAT_Res_AP_tahmini_ohm": {"ort": r(float(Rb.mean()), 4), "maks": r(float(Rb.max()), 4), "son": r(float(Rb[-1]), 4)},
        "mAh_ilk3s": r(float((getattr(np, "trapezoid", None) or np.trapz)(Ib, t_b[pb])) / 3.6, 1),
        "guc_tepe_W": r(float((V * I)[pb].max()), 0),
        "tam_gaz_penceresi": {"V_ort": r(float(V[pt].mean())), "I_ort_A": r(float(I[pt].mean()), 1), "sure_s": r(tam_gaz_suresi, 1)},
        "sensor": {"BATT_MONITOR": parm.get("BATT_MONITOR"), "BATT_AMP_PERVLT": r(parm.get("BATT_AMP_PERVLT"), 2), "BATT_VOLT_MULT": r(parm.get("BATT_VOLT_MULT"), 3),
                   "not": "akim/gerilim olcegi PARM'daki carpanlarla; sensor kalibrasyonu logdan dogrulanamaz"},
        "BATT_esikleri": {"BATT_LOW_VOLT": parm.get("BATT_LOW_VOLT"), "BATT_CRT_VOLT": parm.get("BATT_CRT_VOLT"), "BATT_CAPACITY": parm.get("BATT_CAPACITY"),
                          "not": "3S degerleri (10/9 V) 4S'de anlamsiz; kalkista 12,36 V'a inis (3,09 V/hucre) LOW esigini bile tetiklemedi"},
    }

    # ------------------------------------------------------------------ motor / MOT_*
    pwm_min, pwm_max = parm["MOT_PWM_MIN"], parm["MOT_PWM_MAX"]
    spin_max, spin_min, expo = parm["MOT_SPIN_MAX"], parm["MOT_SPIN_MIN"], parm["MOT_THST_EXPO"]
    pwm_tavan = pwm_min + spin_max * (pwm_max - pwm_min)
    pm = (t_rc >= t0) & (t_rc <= t0 + 2.0)
    motorlar = {}
    for k, v in mot.items():
        im = int(np.where(pm)[0][np.argmax(v[pm])])
        doygun = int(((v[pm] >= pwm_tavan - 1)).sum())
        ilk = np.where(pm & (v >= pwm_tavan - 1))[0]
        motorlar[k] = {"tepe_us": int(v[im]), "tepe_t_s": r(float(t_rc[im] - t0), 2), "doygun_ornek_10Hz": doygun,
                       "ilk_doygun_t_s": r(float(t_rc[ilk[0]] - t0), 2) if len(ilk) else None}
    pt1 = (t_rc >= t_tam_bas + 0.35) & (t_rc <= t_tam_son + 0.05)
    yay = [int(max(mot[k][i] for k in mot) - min(mot[k][i] for k in mot)) for i in np.where(pt1)[0]]
    motor = {
        "cikislar": "SERVO9-12 = M1..M4 (RCOU C9..C12); FRAME QUAD/X: M1 on-sag CCW, M2 arka-sol CCW, M3 on-sol CW, M4 arka-sag CW",
        "MOT_PWM_MIN": pwm_min, "MOT_PWM_MAX": pwm_max, "MOT_SPIN_MIN": r(spin_min), "MOT_SPIN_ARM": r(parm.get("MOT_SPIN_ARM")),
        "MOT_SPIN_MAX": r(spin_max), "MOT_THST_EXPO": r(expo), "MOT_THST_HOVER": r(parm.get("MOT_THST_HOVER")),
        "MOT_BAT_VOLT_MAX": parm.get("MOT_BAT_VOLT_MAX"), "MOT_BAT_VOLT_MIN": parm.get("MOT_BAT_VOLT_MIN"),
        "pwm_tavan_hesap_us": r(pwm_tavan, 0), "motorlar": motorlar,
        "tam_gaz_motorlar_arasi_yayilim_us": {"maks": max(yay) if yay else None, "ort": r(float(np.mean(yay)), 0) if yay else None},
        "ThO_1p0_suresi_s": r(tam_gaz_suresi, 1), "ThO_1p0_bas_s": r(t_tam_bas - t0, 2), "ThO_1p0_son_s": r(t_tam_son - t0, 2),
        "etki": [
            "ThO=1,0 -> itki egrisi girisi 1 -> aktuator = SPIN_MAX = 0,95 -> PWM 1950 (gozlenen 1949). EXPO tam gazda etkisizdir; yalniz ara gaz bolgesini (0<ThO<1) egriler.",
            "SPIN_MAX 0,95: ESC araliginin ustteki %5'i hic kullanilmadi; T/W alt siniri 1950 us'e aittir, 2000 us'e degil. 2000'deki itki logdan bilinemez.",
            "MOT_THST_EXPO 0,65 (varsayilan): ThO ile PWM esleme dogrusal degildir; sadece ara gaz bolgesinde gaz-itki dogrusalligini etkiler.",
            "Motorlar arasi yayilim tam gazda ~40-70 us: M1 (C9) doygunken M2/M4 daha dusuk -> tutum denetleyici roll/pitch'i M2/M4'u kisarak tutar; ortak itki tavani M1 ile sinirlanir.",
            "MOT_BAT_VOLT_MAX/MIN = 0: gerilim telafisi kapali; pil coktukce ayni PWM'de itki duser (12,36 V'da tam gaz itkisi 15,6 V'takinden dusuk).",
        ],
    }

    # ------------------------------------------------------------------ yazilim hiz sinirlari
    p = lambda k: parm.get(k)  # noqa: E731
    pilot_dn = p("PILOT_SPEED_DN") if p("PILOT_SPEED_DN") not in (None, 0.0) else p("PILOT_SPEED_UP")
    angle_max_deg = p("ANGLE_MAX") / 100.0
    hiz_sinirlari = {
        "PARM": {k: p(k) for k in ("PILOT_SPEED_UP", "PILOT_SPEED_DN", "PILOT_ACCEL_Z", "WPNAV_SPEED", "WPNAV_SPEED_UP", "WPNAV_SPEED_DN",
                                   "WPNAV_ACCEL", "WPNAV_ACCEL_Z", "LOIT_SPEED", "LOIT_ACC_MAX", "LOIT_BRK_ACCEL", "ANGLE_MAX", "LAND_SPEED",
                                   "LAND_SPEED_HIGH", "LAND_ALT_LOW", "PSC_JERK_XY", "PSC_JERK_Z", "WPNAV_JERK")},
        "firmware": ver,
        "tablo": [
            {"kip": "AUTO / GUIDED (WPNAV)", "yatay_maks_ms": p("WPNAV_SPEED") / 100, "tirmanma_maks_ms": p("WPNAV_SPEED_UP") / 100,
             "inis_maks_ms": p("WPNAV_SPEED_DN") / 100, "yatay_ivme_ms2": p("WPNAV_ACCEL") / 100, "dikey_ivme_ms2": p("WPNAV_ACCEL_Z") / 100,
             "kaynak": "WPNAV_SPEED / WPNAV_SPEED_UP / WPNAV_SPEED_DN / WPNAV_ACCEL / WPNAV_ACCEL_Z (DO_CHANGE_SPEED / guided hiz komutu ile degistirilebilir)"},
            {"kip": "LOITER / POSHOLD (pilot)", "yatay_maks_ms": p("LOIT_SPEED") / 100, "tirmanma_maks_ms": p("PILOT_SPEED_UP") / 100,
             "inis_maks_ms": pilot_dn / 100, "yatay_ivme_ms2": p("LOIT_ACC_MAX") / 100, "dikey_ivme_ms2": p("PILOT_ACCEL_Z") / 100,
             "kaynak": "LOIT_SPEED / PILOT_SPEED_UP / PILOT_SPEED_DN(=0 -> PILOT_SPEED_UP) / LOIT_ACC_MAX / PILOT_ACCEL_Z"},
            {"kip": "ALT_HOLD (pilot)", "yatay_maks_ms": None, "tirmanma_maks_ms": p("PILOT_SPEED_UP") / 100, "inis_maks_ms": pilot_dn / 100,
             "yatay_ivme_ms2": None, "dikey_ivme_ms2": p("PILOT_ACCEL_Z") / 100,
             "kaynak": "PILOT_SPEED_UP / PILOT_SPEED_DN; yatay: egim ANGLE_MAX ile sinirli, hiz siniri yok"},
            {"kip": "LAND", "yatay_maks_ms": None, "tirmanma_maks_ms": 0.0, "inis_maks_ms": p("LAND_SPEED") / 100,
             "yatay_ivme_ms2": None, "dikey_ivme_ms2": None,
             "kaynak": "LAND_SPEED (son LAND_ALT_LOW=10 m altinda); LAND_SPEED_HIGH=0 -> ustte WPNAV_SPEED_DN"},
            {"kip": "STABILIZE (bu ucus)", "yatay_maks_ms": None, "tirmanma_maks_ms": None, "inis_maks_ms": None,
             "yatay_ivme_ms2": r(G * math.tan(math.radians(angle_max_deg)), 2), "dikey_ivme_ms2": None,
             "kaynak": "yazilim hiz siniri YOK; yalniz ANGLE_MAX=30 deg egim siniri -> yatay ivme <= g*tan(30) = 5,66 m/s2 (surtunme ihmal)"},
        ],
        "ANGLE_MAX_deg": angle_max_deg,
        "yorum": ("Gorev kiplerinde (GUIDED/AUTO/LOITER) ulasilabilecek hizlar bu sinirlarla kisitlidir: tirmanma 2,5 m/s (WPNAV_SPEED_UP=PILOT_SPEED_UP=250), "
                  "inis 1,5 m/s (WPNAV) / 2,5 m/s (pilot), yatay 3,0 m/s (AUTO/GUIDED, WPNAV_SPEED=300) ve 12,5 m/s (LOITER pilot, LOIT_SPEED=1250). "
                  "Bu ucusta STABILIZE'da olculen tirmanma tepesi gorev kiplerinin izin verdigi 2,5 m/s'nin ustundedir: govde yetenegi yazilim sinirinin ustundedir."),
    }

    # ------------------------------------------------------------------ yatay hiz
    gps_spd = kolon(D["GPS"], "Spd"); t_gps = kolon(D["GPS"], "TimeUS") / 1e6
    vh = np.hypot(vn, ve)
    ig = int(np.argmax(gps_spd)); ih = int(np.argmax(vh))
    yatay = {"GPS_Spd_maks_ms": r(float(gps_spd[ig]), 2), "GPS_Spd_maks_t_s": r(float(t_gps[ig] - t0), 1),
             "XKF1_VN_VE_maks_ms": r(float(vh[ih]), 2), "XKF1_maks_t_s": r(float(t_xk[ih] - t0), 1),
             "OLCULMEDI": "Yatay ust hiz TEST EDILMEDI: ucus dikey kalkis + LAND; yatay hareket istemsiz kayma (< 2,3 m/s). "
                          "ANGLE_MAX=30 deg ile ulasilabilir yatay hiz surtunme bilinmeden hesaplanamaz."}

    gaz_profili = [[r(float(t_ct[k] - t0), 1), r(float(thi[k]), 2), r(float(tho[k]), 2)] for k in range(i0 - 2, min(i0 + 40, len(t_ct)))]

    # ------------------------------------------------------------------ ozet
    ozet = {
        "surum": "1.0", "uretim": dt.datetime.now().isoformat(timespec="seconds"),
        "log": os.path.relpath(LOG, KOK).replace("\\", "/"), "sha256": sha256(LOG), "firmware": ver,
        "kullanici_beyani": {"pil": "4S", "pervane": "9x5x3", "kutle": "BILINMIYOR (logda yok)"},
        "log_araligi_s": [r(float(t_ct[0])), r(float(t_ct[-1]))],
        "t0": {"tanim": "ilk CTUN ornegi ThO >= 0,15", "t_mutlak_s": r(t0, 2),
               "RCIN_C3_gt_1500_s": r(t_rcin - t0, 2), "RCOU_C9_gt_1150_s": r(t_rcou - t0, 2),
               "not": "RCIN C3 1002 -> 1081 (-0,20 s) -> 1798 (-0,10 s) -> 2000 (0,00 s): pilot gazi ~0,2 s icinde tavana itti"},
        "kipler": modlar, "olaylar": olaylar, "motorlu_sure_s": r(motorlu_sure, 1),
        "disarm_t_s": r(None if t_disarm is None else t_disarm - t0, 2),
        "EKF": {"birincil_cekirdek": birincil, "cekirdek_farki": cekirdek_farki,
                "yaw_reset_t_s": next((o["t"] for o in olaylar if o["id"] == 62), None),
                "not": "EKF3 'in-flight yaw alignment' t0+1,14 s'de: VN/VE'de sicrama olabilir; VD/PD etkilenmez (dikey durum yaw'dan bagimsiz)"},
        "tirmanma_hizi": {
            "XKF1_negVD": {"tepe_ms": r(tepe_x), "tepe_t_s": r(t_tepe_x - t0, 2), "esik_sureleri_s": esik_x},
            "CTUN_CRt": {"tepe_ms": r(tepe_c), "tepe_t_s": r(t_tepe_c - t0, 2), "esik_sureleri_s": esik_c},
            "kaynak_farki": kaynak_farki,
            "hareket_esigi_ms": HAREKET_ESIK,
            "not": "CTUN.CRt, AP_InertialNav.get_velocity_z_up_cms() = EKF birincil cekirdek dikey hizi; XKF1.VD ile ayni kaynak, farkli zaman damgasi ve cm/s yuvarlama",
        },
        "irtifa": irtifa, "ivme": ivme, "IMU": imu, "IMU_not": imu_not, "TW": tw, "pil": pil, "motor": motor,
        "yazilim_hiz_sinirlari": hiz_sinirlari, "yatay_hiz": yatay, "gaz_profili_t_ThI_ThO": gaz_profili,
    }

    mo = {"t0": 130.34, "ilk_hareket_s": 0.30, "esik_ilk_ornek_s": {"1": 0.40, "2": 0.50, "3": 0.60, "4": 0.80, "5": 0.90},
          "tepe_ms": 5.19, "tepe_t_s": 1.00, "tepe_ivme_ms2": 8.93, "TW": 1.91, "alt_2m_s": 1.0, "alt_5m_s": 3.6, "alt_maks_m": 8.0, "alt_maks_t_s": 5.0,
          "I_maks_A": 115, "V_min": 12.36, "yatay_maks_ms": 2.2}
    ozet["mimar_on_hesabi_kiyas"] = {
        "mimar": mo,
        "bu_analiz": {"t0": r(t0, 2), "ilk_hareket_0p10ms_ilk_ornek_s": esik_x["0.1"]["ilk_ornek_s"],
                      "esik_ilk_ornek_s": {k: esik_x[k]["ilk_ornek_s"] for k in ("1", "2", "3", "4", "5")},
                      "tepe_ms": r(tepe_x), "tepe_t_s": r(t_tepe_x - t0, 2), "tepe_ivme_ms2": r(a_maks), "TW": tw["TW_alt_sinir"],
                      "alt_2m_s": irtifa["esikler"]["2m"]["ilk_ornek_s"], "alt_5m_s": irtifa["esikler"]["5m"]["ilk_ornek_s"],
                      "alt_maks_m": irtifa["maks_m"], "alt_maks_t_s": irtifa["maks_t_s"], "I_maks_A": pil["I_maks_A"], "V_min": pil["V_min"],
                      "yatay_maks_ms": yatay["GPS_Spd_maks_ms"]},
    }

    # ================================================================== GRAFIKLER
    x0, x1 = -1.0, (t_disarm - t0 + 0.5) if t_disarm else 12.5
    fig, axs = plt.subplots(6, 1, figsize=(11, 14), sharex=True, gridspec_kw={"hspace": 0.12})
    a = axs[0]
    a.plot(t_xk - t0, vz, color=C_BLUE, label="XKF1 −VD (birincil çekirdek)")
    a.plot(t_ct - t0, crt, color=C_ORANGE, ls="--", label="CTUN.CRt / 100")
    a.axhline(0, color=C_TEXT2, lw=0.6)
    a.annotate(f"tepe {tepe_x:.2f} m/s @ +{t_tepe_x - t0:.2f} s", (t_tepe_x - t0, tepe_x), xytext=(8, 4), textcoords="offset points", fontsize=8)
    a.set_ylabel("tırmanma hızı (m/s)"); a.legend(loc="upper right", ncol=2)
    a = axs[1]
    a.plot(t_ct - t0, alt_rel, color=C_BLUE)
    a.annotate(f"maks {alt_rel[i_alt_maks]:.2f} m @ +{t_ct[i_alt_maks] - t0:.1f} s", (t_ct[i_alt_maks] - t0, alt_rel[i_alt_maks]), xytext=(8, -12), textcoords="offset points", fontsize=8)
    a.set_ylabel("irtifa CTUN.Alt − taban (m)")
    a = axs[2]
    a.plot(t_ct - t0, tho, color=C_BLUE, label="ThO (çıkış)")
    a.plot(t_ct - t0, thi, color=C_ORANGE, ls="--", label="ThI (pilot)")
    a.axhline(float(thh[i0]), color=C_TEXT2, lw=0.6, ls=":"); a.text(x1, float(thh[i0]), f" ThH {thh[i0]:.2f}", fontsize=7, va="center", color=C_TEXT2)
    a.set_ylabel("gaz (0–1)"); a.set_ylim(-0.05, 1.08); a.legend(loc="upper right", ncol=2)
    a = axs[3]
    a.plot(t_b - t0, I, color=C_BLUE)
    a.annotate(f"maks {I[iI]:.1f} A @ +{t_b[iI] - t0:.2f} s", (t_b[iI] - t0, I[iI]), xytext=(8, 0), textcoords="offset points", fontsize=8)
    a.set_ylabel("BAT akım (A)")
    a = axs[4]
    a.plot(t_b - t0, V, color=C_BLUE)
    a.annotate(f"min {V[i_vmin]:.2f} V ({V[i_vmin] / HUCRE:.2f} V/hücre) @ +{t_b[i_vmin] - t0:.2f} s", (t_b[i_vmin] - t0, V[i_vmin]), xytext=(8, -4), textcoords="offset points", fontsize=8)
    a.set_ylabel("BAT gerilim (V)")
    a = axs[5]
    renk = {"C9": C_BLUE, "C10": C_ORANGE, "C11": C_AQUA, "C12": C_YELLOW}
    ad = {"C9": "C9 M1", "C10": "C10 M2", "C11": "C11 M3", "C12": "C12 M4"}
    for k in ("C9", "C10", "C11", "C12"):
        a.plot(t_rc - t0, mot[k], color=renk[k], label=ad[k], lw=1.3)
    a.axhline(pwm_tavan, color=C_TEXT2, lw=0.6, ls=":"); a.text(x1, pwm_tavan, f" SPIN_MAX {pwm_tavan:.0f}", fontsize=7, va="center", color=C_TEXT2)
    sira = sorted(motorlar, key=lambda k: -motorlar[k]["tepe_us"])
    a.text(t_tam_son - t0 + 0.15, 1935, "tepe (µs): " + ", ".join(f"{ad[k]} {motorlar[k]['tepe_us']}" for k in sira),
           fontsize=7, color=C_TEXT2, va="top")
    a.set_ylabel("RCOU C9–C12 (µs)"); a.legend(loc="lower right", ncol=4); a.set_xlabel("t − t0 (s)   [t0 = ilk ThO ≥ 0,15 = %.2f s]" % t0)
    for m_ in modlar:
        if m_["mod"] == "LAND":
            for ax_ in axs:
                ax_.axvline(m_["t"], color=C_VIOLET, lw=0.8, ls="--")
            axs[1].text(m_["t"] + 0.05, 7.5, "LAND (RC) +%.1f s" % m_["t"], color=C_VIOLET, fontsize=8, va="top")
    for ax_ in axs:
        ax_.axvspan(t_tam_bas - t0 - 0.05, t_tam_son - t0 + 0.05, color=C_ORANGE, alpha=0.07, lw=0)
    axs[2].text(t_tam_son - t0 + 0.1, 1.0, "ThO=1,0 (%.1f s)" % tam_gaz_suresi, color=C_ORANGE, fontsize=7, va="center")
    axs[0].set_xlim(x0, x1)
    fig.subplots_adjust(top=0.965, bottom=0.04)
    fig.suptitle("15 Eyl 2026 12-40-55 — STABILIZE tam gaz dikey kalkış (4S + 9x5x3, kullanıcı beyanı)", y=0.985, fontsize=11)
    f1 = os.path.join(OUT, "zaman_serisi_t0_2026-09-15_12-40-55.png")
    fig.savefig(f1, dpi=130, bbox_inches="tight"); plt.close(fig)

    # --- 2) hiz-zaman esikleri
    fig, a = plt.subplots(figsize=(10, 5.5))
    a.plot(t_xk - t0, vz, color=C_BLUE, marker="o", ms=3.5, label="XKF1 −VD (10 Hz)")
    a.plot(t_ct - t0, crt, color=C_ORANGE, ls="--", marker="s", ms=2.5, label="CTUN.CRt / 100 (10 Hz)")
    for e in ESIKLER:
        a.axhline(e, color=C_GRID, lw=0.8)
        ta = esik_x[f"{e:g}"]["ara_deger_s"]; to = esik_x[f"{e:g}"]["ilk_ornek_s"]
        if ta is not None:
            a.plot([ta], [e], marker="|", ms=14, color=C_BLUE, mew=1.5)
            a.annotate(f"{e:.0f} m/s: +{ta:.2f} s (ara) / +{to:.1f} s (örnek)", (ta, e), xytext=(6, -11), textcoords="offset points", fontsize=8, color=C_TEXT)
    a.axvline(0, color=C_TEXT2, lw=0.8); a.text(0.02, 5.9, "t0 (ThO≥0,15)", fontsize=8, color=C_TEXT2)
    ha = esik_x["0.1"]["ilk_ornek_s"]
    a.axvline(ha, color=C_AQUA, lw=0.8, ls=":"); a.text(ha + 0.02, 5.6, f"ilk hareket (v≥0,1) +{ha:.1f} s", fontsize=8, color=C_TEXT2)
    a.axvspan(t_tam_bas - t0 - 0.05, t_tam_son - t0 + 0.05, color=C_ORANGE, alpha=0.07, lw=0); a.text(t_tam_bas - t0, -0.45, "ThO = 1,0", color=C_ORANGE, fontsize=8)
    a.annotate(f"tepe {tepe_x:.2f} m/s @ +{t_tepe_x - t0:.2f} s", (t_tepe_x - t0, tepe_x), xytext=(10, 6), textcoords="offset points", fontsize=8)
    a.set_xlim(-0.5, 2.5); a.set_ylim(-0.6, 6.2); a.set_xlabel("t − t0 (s)"); a.set_ylabel("tırmanma hızı (m/s)")
    a.legend(loc="lower right"); a.set_title("0→1..5 m/s eşik süreleri — tam gaz dikey kalkış (12-40-55)")
    f2 = os.path.join(OUT, "hiz_zaman_esikler_2026-09-15_12-40-55.png")
    fig.savefig(f2, dpi=130, bbox_inches="tight"); plt.close(fig)

    # --- 3) ivme kiyasi + IMU integrasyonu
    fig, axs = plt.subplots(2, 1, figsize=(10, 8), sharex=True, gridspec_kw={"hspace": 0.1})
    a = axs[0]
    a.plot(t_xk - t0, a_x, color=C_BLUE, marker="o", ms=3, label="XKF1 −VD merkezi fark (ham)")
    a.plot(t_xk - t0, a_x_y, color=C_BLUE, ls=":", label="XKF1 3-örnek yumuşak")
    a.plot(t_ct - t0, a_c, color=C_ORANGE, ls="--", label="CTUN.CRt merkezi fark (ham)")
    for inst, (t_i, ad_, ady, ti, v_int) in imu_ser.items():
        a.plot(t_i - t0, ady, color=C_AQUA if inst == 0 else C_YELLOW, lw=1.2, label=f"IMU{inst} döndürülmüş, 0,2 s ort.")
    a.annotate(f"tepe {a_maks:.2f} m/s² @ +{t_xk[ia] - t0:.2f} s → T/W ≥ {1 + a_maks / G:.2f}", (t_xk[ia] - t0, a_maks), xytext=(10, 4), textcoords="offset points", fontsize=8)
    a.axhline(0, color=C_TEXT2, lw=0.6); a.set_ylabel("dikey ivme (m/s², yukarı +)"); a.legend(loc="upper right", fontsize=8)
    a.set_title("Dikey ivme: EKF türevi ve IMU ham (yerçekimi + durgun sapma çıkarılmış)")
    a = axs[1]
    a.plot(t_xk - t0, vz, color=C_BLUE, marker="o", ms=3, label="XKF1 −VD")
    for inst, (t_i, ad_, ady, ti, v_int) in imu_ser.items():
        a.plot(ti - t0, v_int, color=C_AQUA if inst == 0 else C_YELLOW, lw=1.2, label=f"∫IMU{inst} ivme dt (t0'dan)")
    a.set_xlim(-0.5, 2.5); a.set_ylabel("hız (m/s)"); a.set_xlabel("t − t0 (s)"); a.legend(loc="upper right", fontsize=8)
    f3 = os.path.join(OUT, "ivme_EKF_vs_IMU_2026-09-15_12-40-55.png")
    fig.savefig(f3, dpi=130, bbox_inches="tight"); plt.close(fig)

    # --- 4) pil V-I
    fig, a = plt.subplots(figsize=(8, 5.5))
    sc = a.scatter(Ib, Vb, c=(t_b[pb] - t0), cmap="Blues", s=26, edgecolor=C_SURF, lw=0.5, vmin=0, vmax=3)
    xx = np.linspace(0, Ib.max() * 1.05, 50)
    a.plot(xx, np.polyval([egim, kesim], xx), color=C_ORANGE, label=f"polyfit: V = {kesim:.2f} − {-egim * 1000:.1f} mΩ · I   (R² {r2:.3f})")
    cb = fig.colorbar(sc, ax=a, pad=0.02); cb.set_label("t − t0 (s)")
    a.annotate(f"{I[iI]:.0f} A, {V[iI]:.2f} V", (I[iI], V[iI]), xytext=(-70, -14), textcoords="offset points", fontsize=8)
    a.set_xlabel("BAT akım (A)"); a.set_ylabel("BAT paket gerilimi (V)"); a.legend(loc="upper right", fontsize=8)
    a.set_title(f"Pil sarkması t0..t0+3 s — R_paket {-egim * 1000:.1f} mΩ ({-egim * 1000 / HUCRE:.1f} mΩ/hücre), BAT.Res(AP) son {Rb[-1] * 1000:.1f} mΩ")
    f4 = os.path.join(OUT, "pil_V_I_polyfit_2026-09-15_12-40-55.png")
    fig.savefig(f4, dpi=130, bbox_inches="tight"); plt.close(fig)

    ozet["grafikler"] = [os.path.relpath(f, KOK).replace("\\", "/") for f in (f1, f2, f3, f4)]
    yol = os.path.join(OUT, "ozet.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(ozet, f, ensure_ascii=False, indent=1)
    print("yazildi:", yol)
    print(json.dumps({k: ozet[k] for k in ("t0", "tirmanma_hizi", "irtifa", "ivme", "IMU", "TW", "pil", "motor", "yatay_hiz", "EKF", "mimar_on_hesabi_kiyas")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
