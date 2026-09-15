# -*- coding: utf-8 -*-
"""
performans_modeli.py — Navitas uçuş performans zarfı (yazılımsal sınırlar YOK SAYILIR)

Konfigürasyonlar:
  * 4S 13 Ah + 9x5x3   (SunnySky X2220 980KV, Skywalker 60 A V2 ESC, PM06)
  * 3S  8 Ah + 1045    (aynı motor / ESC / PM06)

Bütün sayılar bu betikten üretilir:  tablolar.json + RAPOR.md + 3 grafik (PNG).
Yalnız numpy + matplotlib (SciPy YASAK). Parametreler dosyanın üstündedir.

Log ankrajları: results/ucus_analiz_20260915/{A_3S_1045,D_4S_9x5x3,E_1240_tam_gaz,
E_1240_ivme,F_1311_aski_4S_13Ah}/ozet.json ve parametre_zaman_cizgisi.md (satır 219).
Koşum:  O:\\navitas-local-train\\venv\\Scripts\\python.exe performans_modeli.py
"""
from __future__ import annotations

import datetime
import json
import math
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):   # Windows konsolu cp1254: θ, ✓ gibi karakterler için
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BURASI = os.path.dirname(os.path.abspath(__file__))
ANALIZ_KOK = os.path.dirname(BURASI)  # results/ucus_analiz_20260915

# =====================================================================
#  PARAMETRELER  (her sayının kaynağı yanında; ÖLÇÜM / BEYAN / VARSAYIM)
# =====================================================================
G = 9.80665                   # m/s²
RHO = 1.15                    # kg/m³  — Adıyaman ~670 m (VARSAYIM, kullanıcı)
CDA0 = 0.08                   # m²     — 0° eğimde ön/üst alan (VARSAYIM, kullanıcı)
CDA_EGIM_K = 0.5              # CdA(θ) = CDA0·(1 + 0.5·sinθ)   (VARSAYIM, kullanıcı)
EGIMLER_DEG = [0, 30, 45, 58, 66, 90]

# ArduPilot motor parametreleri — parametre_zaman_cizgisi.md satır 219 (tüm loglarda sabit)
MOT_SPIN_MIN = 0.15
MOT_SPIN_MAX = 0.95
MOT_THST_EXPO = 0.65
MOT_PWM_MIN = 1000
MOT_PWM_MAX = 2000

KV_RPM_PER_V = 980.0          # SunnySky X2220 980KV — üretici beyanı (yüksüz), ÖLÇÜLMEDİ

# Güç elektroniği sınırları
ESC_SUREKLI_A_MOTOR = 60.0    # Skywalker 60 A V2 — ad plakası
ESC_TEPE_A_MOTOR = 80.0       # 10 s tepe — veri sayfası DOĞRULANMADI
PM06_SUREKLI_A = 60.0         # Holybro PM06 V2 — veri sayfası DOĞRULANMADI (bellekten)
PM06_TEPE_A = 120.0           # <60 s — veri sayfası DOĞRULANMADI (bellekten)
MOTOR_N = 4

# E_1240_ivme/ozet.json — tam gaz denemesinde ölçülen hızlar (sürükleme ihmalinin büyüklüğü için)
E_IVME_TEPE_HIZ_MS = 5.195        # XKF1 -VD tepe (t0+1,0 s)
E_IVME_TEPE_IVME_T_S = 0.5        # ham ivme tepesi anı (XKF1 ham_tepe_t_s)
E_IVME_HIZ_TEPE_IVME_ANINDA_MS = 2.2   # 2 m/s eşiği 0,477 s, 3 m/s eşiği 0,591 s → 0,5 s'de doğrusal ara değer
E_TAM_GAZ_V_ARM = 15.54           # E_1240_tam_gaz/ozet.json V_arm

KULLANILABILIR_PIL = 0.80     # %80
UST_HIZ_ORANI = 0.95          # "üst hıza süre" = %95·v_üst
V_60 = 60.0 / 3.6             # 16,67 m/s
V_100 = 100.0 / 3.6           # 27,78 m/s

DT = 0.002                    # s — RK4 adımı
T_MAKS_ENTEGRE = 600.0        # s

KONFIGLER = [
    dict(
        kimlik="4S_13Ah_9x5x3",
        ad="4S 13 Ah + 9x5x3",
        kutle_kg=3.0,             # VARSAYIM (kullanıcı): kütle ölçülmedi
        kapasite_Ah=13.0,
        hucre=4,
        R_paket_ohm=0.0304,       # ÖLÇÜM: F logu kalkış geçişi polyfit, r² 0,995 (F ozet.json "ic_direnc.a_kalkis_gecisi")
        pervane="9x5x3 (3 pal)",
        pitch_m=5.0 * 0.0254,
        aski=dict(ThO=0.36, V_yuk=14.0, I_A=37.3, sure_s=64,
                  kaynak="F_1311_aski_4S_13Ah/ozet.json: ThO_aski_ort 0,3591 / p50 0,3604; I p50; 62,9 s GUIDED askı (13-11-32 logu)"),
        aski_pwm_olculen_orani=0.583,   # F ozet.json "rcou.ort_pwm_orani" (askı) — çapraz kontrol
        tam_gaz=dict(TW=1.91, V_yuk=12.36, I_A=115.0, a_ms2=8.934, rcou_maks=1949,
                     kaynak="E_1240_ivme/ozet.json: TW_alt_sinir 1,91 (a 8,934 m/s²); E_1240_tam_gaz/ozet.json: I_maks 115 A, V_min 12,36 V, RCOU M4 maks 1949"),
        pil_senaryolari=[
            ("fazla dolu 4,25 V/hücre", 17.0),
            ("dolu 4,20 V/hücre", 16.8),
            ("F logu başı", 15.6),      # F ozet.json V_ilk_log 15,57
        ],
        ikinci_aski_kontrol=dict(ThO=0.327, V_yuk=14.72, I_A=35.5,
                                 kaynak="D_4S_9x5x3 (F ozet.json kıyas bloğu 'D': aski_ThO_ort 0,327, aski_V 14,719, aski_I_A 35,514)"),
    ),
    dict(
        kimlik="3S_8Ah_1045",
        ad="3S 8 Ah + 1045",
        kutle_kg=2.5,             # VARSAYIM (kullanıcı): paket farkı ~0,5 kg
        kapasite_Ah=8.0,
        hucre=3,
        R_paket_ohm=0.041,        # ÖLÇÜM: A ozet.json "R_uydurma_ohm_paket.ort" 0,0409 (n=18 uçuş)
        pervane="10x4.5 (1045, 2 pal)",
        pitch_m=4.5 * 0.0254,
        aski=dict(ThO=0.467, V_yuk=10.08, I_A=31.6, sure_s=311,
                  kaynak="A_3S_1045/ozet.json: havuz_ThO ort 0,466 (ThO_motorlu_ort 0,467), havuz_V ort 10,09, havuz_I_A ort 31,6, askida_toplam_s 312,2 (n=3122 örnek, 18 uçuş)"),
        aski_pwm_olculen_orani=None,    # havuz PWM oranı ozet.json'da yok (uçuş bazlı 0,49–0,62)
        tam_gaz=None,                   # 3S + 1045 TAM GAZ ÖLÇÜMÜ YOK → 4S sarkma çarpanı aktarılır
        pil_senaryolari=[
            ("fazla dolu 4,25 V/hücre", 12.75),
            ("dolu 4,20 V/hücre", 12.6),
            ("A uçuş başı ort", 11.5),
        ],
        ikinci_aski_kontrol=None,
    ),
]

# =====================================================================
#  MODEL 1 — Motor-pervane
# =====================================================================


def aktuator_orani(thr: float) -> float:
    """ArduPilot AP_Motors thrust_to_actuator (lift_max=1, pil telafisi kapalı):
    a = ((e-1) + sqrt((1-e)² + 4·e·thr)) / (2e).  MOT_THST_EXPO=e itki-PWM
    doğrusallaştırmasıdır: itkinin PWM ile yaklaşık karesel arttığını telafi etmek
    için ThO'ya ters (kök) eğri uygular, böylece ThO'nun yarısı ≈ yarı itki verir."""
    e = MOT_THST_EXPO
    return ((e - 1.0) + math.sqrt((1.0 - e) ** 2 + 4.0 * e * thr)) / (2.0 * e)


def u_eff(thr: float) -> float:
    """PWM aralığındaki gerçek oran: SPIN_MIN + (SPIN_MAX - SPIN_MIN)·a(ThO)."""
    return MOT_SPIN_MIN + (MOT_SPIN_MAX - MOT_SPIN_MIN) * aktuator_orani(thr)


def pwm_us(thr: float) -> float:
    return MOT_PWM_MIN + u_eff(thr) * (MOT_PWM_MAX - MOT_PWM_MIN)


def cda(theta_deg: float) -> float:
    return CDA0 * (1.0 + CDA_EGIM_K * math.sin(math.radians(theta_deg)))


def kalibre(kf: dict, s_TG_aktarim: float | None = None) -> dict:
    """Askı noktasından k_T, k_P; tam gaz noktasından RPM sarkma çarpanı s_TG.
    RPM_KV = KV·V_yük·u_eff (yüksüz KV modeli).  T = k_T·RPM², P_el = k_P·RPM³.
    Tam gazda RPM_TG = s_TG·KV·V_yük·SPIN_MAX  (s_TG: yük altı sarkma, 4S ölçümünden)."""
    m = kf["kutle_kg"]
    W = m * G
    a = kf["aski"]
    ue_h = u_eff(a["ThO"])
    rpm_h = KV_RPM_PER_V * a["V_yuk"] * ue_h
    k_T = W / rpm_h ** 2
    P_h = a["V_yuk"] * a["I_A"]
    k_P = P_h / rpm_h ** 3
    kal = dict(
        W_N=W,
        u_eff_aski_model=ue_h,
        pwm_aski_model_us=pwm_us(a["ThO"]),
        pwm_aski_expo_suz_us=MOT_PWM_MIN + (MOT_SPIN_MIN + (MOT_SPIN_MAX - MOT_SPIN_MIN) * a["ThO"]) * (MOT_PWM_MAX - MOT_PWM_MIN),
        pwm_aski_olculen_us=(None if kf["aski_pwm_olculen_orani"] is None
                             else MOT_PWM_MIN + kf["aski_pwm_olculen_orani"] * (MOT_PWM_MAX - MOT_PWM_MIN)),
        rpm_aski_KV=rpm_h,
        k_T_N_per_rpm2=k_T,
        k_P_W_per_rpm3=k_P,
        P_aski_W=P_h,
        T_motor_aski_N=W / MOTOR_N,
        P_motor_aski_W=P_h / MOTOR_N,
    )
    tg = kf.get("tam_gaz")
    if tg:
        rpm_tg_kv = KV_RPM_PER_V * tg["V_yuk"] * MOT_SPIN_MAX
        TW_kv = k_T * rpm_tg_kv ** 2 / W
        s_TG = math.sqrt(tg["TW"] / TW_kv)
        P_tg_model = k_P * (s_TG * rpm_tg_kv) ** 3
        # expo'suz u_eff ile ne olurdu (neden expo gerektiğinin kanıtı)
        ue_h_exposuz = MOT_SPIN_MIN + (MOT_SPIN_MAX - MOT_SPIN_MIN) * a["ThO"]
        TW_exposuz = (tg["V_yuk"] * MOT_SPIN_MAX / (a["V_yuk"] * ue_h_exposuz)) ** 2
        kal.update(
            s_TG=s_TG,
            s_TG_kaynak="ÖLÇÜM (bu konfigin tam gaz noktası)",
            c_T=s_TG ** 2,
            TW_tam_gaz_KV_modeli=TW_kv,
            TW_tam_gaz_olculen=tg["TW"],
            TW_tam_gaz_expo_suz_model=TW_exposuz,
            P_tam_gaz_model_W=P_tg_model,
            P_tam_gaz_olculen_W=tg["V_yuk"] * tg["I_A"],
            P_tam_gaz_sapma_pct=100.0 * (P_tg_model / (tg["V_yuk"] * tg["I_A"]) - 1.0),
            I_tam_gaz_model_A=P_tg_model / tg["V_yuk"],
            I_tam_gaz_olculen_A=tg["I_A"],
            rpm_tam_gaz_model=s_TG * rpm_tg_kv,
            T_motor_tam_gaz_N=tg["TW"] * W / MOTOR_N,
        )
    else:
        s_TG = s_TG_aktarim
        kal.update(s_TG=s_TG, s_TG_kaynak="4S ölçümünden AKTARILDI (aynı motor/ESC varsayımı)", c_T=s_TG ** 2)
    ik = kf.get("ikinci_aski_kontrol")
    if ik:
        ue2 = u_eff(ik["ThO"])
        rpm2 = KV_RPM_PER_V * ik["V_yuk"] * ue2
        kal["ikinci_aski_kontrol"] = dict(
            kaynak=ik["kaynak"],
            TW_model=k_T * rpm2 ** 2 / W,
            I_model_A=k_P * rpm2 ** 3 / ik["V_yuk"],
            I_olculen_A=ik["I_A"],
        )
    return kal


def rpm_tam_gaz(kal: dict, V_yuk: float) -> float:
    return kal["s_TG"] * KV_RPM_PER_V * V_yuk * MOT_SPIN_MAX


def T_maks(kal: dict, V_yuk: float) -> float:
    return kal["k_T_N_per_rpm2"] * rpm_tam_gaz(kal, V_yuk) ** 2


def P_tam_gaz(kal: dict, V_yuk: float) -> float:
    return kal["k_P_W_per_rpm3"] * rpm_tam_gaz(kal, V_yuk) ** 3


def P_itki(kal: dict, T: float) -> float:
    """P_el = k_P·(T/k_T)^1.5  (T ∝ RPM², P ∝ RPM³ → P ∝ T^1.5)."""
    return kal["k_P_W_per_rpm3"] * (T / kal["k_T_N_per_rpm2"]) ** 1.5


# =====================================================================
#  MODEL 2 — Pil (V_yük = V_açık − I·R_paket), kapalı döngü
# =====================================================================


def tam_gaz_cozum(kal: dict, kf: dict, V_acik: float) -> dict:
    """Tam gazda I = P(V)/V = c·V² ve V = V_açık − R·I birlikte çözülür (sönümlü iterasyon
    + kapalı form kontrolü)."""
    R = kf["R_paket_ohm"]
    c = kal["k_P_W_per_rpm3"] * (kal["s_TG"] * KV_RPM_PER_V * MOT_SPIN_MAX) ** 3
    V = V_acik
    n = 0
    for n in range(1, 100000):
        V_yeni = 0.5 * V + 0.5 * (V_acik - R * c * V * V)
        if abs(V_yeni - V) < 1e-10:
            V = V_yeni
            break
        V = V_yeni
    V_kapali = (-1.0 + math.sqrt(1.0 + 4.0 * R * c * V_acik)) / (2.0 * R * c)
    I = c * V * V
    Tm = T_maks(kal, V)
    return dict(V_yuk=V, V_yuk_kapali_form=V_kapali, iterasyon=n, I_A=I, P_W=I * V,
                T_max_N=Tm, TW=Tm / kal["W_N"], rpm=rpm_tam_gaz(kal, V),
                I_motor_A=I / MOTOR_N)


def sabit_itki_cozum(kal: dict, kf: dict, V_acik: float, T: float) -> dict:
    """Sabit itki T için P = P_itki(T); V = V_açık − R·P/V → V² − V_açık·V + R·P = 0.
    Yüksek gerilim kökü (kararlı dal). Diskriminant < 0 ise paket bu gücü veremez."""
    R = kf["R_paket_ohm"]
    P = P_itki(kal, T)
    disc = V_acik ** 2 - 4.0 * R * P
    if disc < 0:
        return dict(cozum=False, P_W=P, V_yuk=None, I_A=None, I_motor_A=None)
    V = 0.5 * (V_acik + math.sqrt(disc))
    Vi = V_acik
    n = 0
    for n in range(1, 100000):
        Vn = 0.5 * Vi + 0.5 * (V_acik - R * P / Vi)
        if abs(Vn - Vi) < 1e-10:
            Vi = Vn
            break
        Vi = Vn
    return dict(cozum=True, P_W=P, V_yuk=V, V_yuk_iter=Vi, iterasyon=n, I_A=P / V,
                I_motor_A=P / V / MOTOR_N)


# =====================================================================
#  MODEL 3 — Eğim dinamiği; zaman entegrasyonu (RK4) + kapalı form
# =====================================================================


def entegre(F, m: float, hedefler: list[float]) -> dict:
    """m·dv/dt = F(v), v(0)=0; her hedef hıza ulaşma süresi (ulaşılmazsa None)."""
    v = 0.0
    t = 0.0
    sonuc = {h: None for h in hedefler}
    kalan = [h for h in hedefler if h > 0]
    for h in hedefler:
        if h <= 0:
            sonuc[h] = 0.0
    while kalan and t < T_MAKS_ENTEGRE:
        k1 = F(v) / m
        k2 = F(v + 0.5 * DT * k1) / m
        k3 = F(v + 0.5 * DT * k2) / m
        k4 = F(v + DT * k3) / m
        v_yeni = v + DT / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        t += DT
        if v_yeni <= v:  # ivme yok/negatif → asimptot
            break
        for h in list(kalan):
            if v_yeni >= h:
                sonuc[h] = t - DT + DT * (h - v) / (v_yeni - v)
                kalan.remove(h)
        v = v_yeni
    return sonuc


def t_kapali(v: float, v_ust: float, a0: float) -> float | None:
    """t(v) = (v_üst/a0)·atanh(v/v_üst); v ≥ v_üst ise None."""
    if v_ust <= 0 or a0 <= 0 or v >= v_ust:
        return None
    return (v_ust / a0) * math.atanh(v / v_ust)


def satir_hesapla(kf: dict, kal: dict, sen_ad: str, V_acik: float, theta: float) -> dict:
    m = kf["kutle_kg"]
    W = kal["W_N"]
    tg = tam_gaz_cozum(kal, kf, V_acik)
    th = math.radians(theta)
    cda_t = cda(theta)
    aa = 0.5 * RHO * cda_t
    r = dict(theta_deg=theta, senaryo=sen_ad, V_acik=V_acik,
             T_max_N=tg["T_max_N"], TW_max=tg["TW"], I_TG_A=tg["I_A"], I_TG_motor_A=tg["I_motor_A"],
             V_yuk_TG=tg["V_yuk"], P_TG_W=tg["P_W"], rpm_TG=tg["rpm"], CdA_m2=cda_t)
    hedefler = None
    if theta == 0:
        # Dikey tırmanış: T(v) = T_max·(1 − v/v_pitch) − W − ½ρ·CdA·v²
        v_pitch = kf["pitch_m"] * tg["rpm"] / 60.0
        r["gerek_TW"] = 1.0
        r["tutar"] = tg["TW"] >= 1.0
        r["v_pitch"] = v_pitch
        r["rejim"] = "dikey tırmanış (tam gaz)"
        if r["tutar"]:
            F0 = tg["T_max_N"] - W
            a0 = F0 / m
            bb = tg["T_max_N"] / v_pitch
            cc = -F0
            v_ust = (-bb + math.sqrt(bb * bb - 4 * aa * cc)) / (2 * aa)
            v_pitch_only = v_pitch * (1.0 - W / tg["T_max_N"])
            v_drag_only = math.sqrt(2.0 * F0 / (RHO * cda_t))
            sinir = "pitch hızı" if v_pitch_only < v_drag_only else "sürükleme"
            r.update(a0=a0, v_ust=v_ust, v_ust_pitch_only=v_pitch_only, v_ust_drag_only=v_drag_only,
                     sinir_birincil=sinir, a_z=None)
            F = lambda v: tg["T_max_N"] * (1.0 - v / v_pitch) - W - aa * v * v  # noqa: E731
            hedefler = [UST_HIZ_ORANI * v_ust, V_60, V_100]
            sur = entegre(F, m, hedefler)
            r.update(t95=sur[hedefler[0]], t60=sur[V_60], t100=sur[V_100], t95_kapali=None,
                     zaman_yontemi="RK4 (itki hızla doğrusal azalır → kapalı form geçersiz)")
        else:
            r.update(a0=(tg["T_max_N"] - W) / m, v_ust=0.0, sinir_birincil="itki (askı yok)",
                     t95=None, t60=None, t100=None, t95_kapali=None, a_z=(tg["T_max_N"] - W) / m,
                     zaman_yontemi="—")
        r.update(I_ust_A=tg["I_A"], V_yuk_ust=tg["V_yuk"], I_ust_motor_A=tg["I_motor_A"],
                 ruzgar=None, ruzgar_notu="dikey eksen — yatay rüzgar tanımsız")
    else:
        gerek = float("inf") if theta == 90 else 1.0 / math.cos(th)
        r["gerek_TW"] = gerek
        r["tutar"] = (theta < 90) and (tg["TW"] >= gerek)
        if r["tutar"]:
            # Düz uçuş, T = W/cosθ sabit; yatay kuvvet W·tanθ − ½ρ·CdA·v²
            F0 = W * math.tan(th)
            a0 = G * math.tan(th)
            v_ust = math.sqrt(2.0 * F0 / (RHO * cda_t))
            sabit = sabit_itki_cozum(kal, kf, V_acik, W / math.cos(th))
            r.update(rejim="düz uçuş, irtifa sabit (T = W/cosθ)", a0=a0, v_ust=v_ust, a_z=0.0,
                     sinir_birincil="sürükleme",
                     t95=t_kapali(UST_HIZ_ORANI * v_ust, v_ust, a0),
                     t60=t_kapali(V_60, v_ust, a0), t100=t_kapali(V_100, v_ust, a0),
                     zaman_yontemi="kapalı form v(t)=v_üst·tanh(a0·t/v_üst); RK4 ile çapraz kontrol")
            F = lambda v: F0 - aa * v * v  # noqa: E731
            hedefler = [UST_HIZ_ORANI * v_ust, V_60, V_100]
            sur = entegre(F, m, hedefler)
            r["t95_rk4"] = sur[hedefler[0]]
            r["t60_rk4"] = sur[V_60]
            r["t100_rk4"] = sur[V_100]
            if sabit["cozum"]:
                r.update(I_ust_A=sabit["I_A"], V_yuk_ust=sabit["V_yuk"], I_ust_motor_A=sabit["I_motor_A"],
                         P_ust_W=sabit["P_W"])
            else:
                r.update(I_ust_A=None, V_yuk_ust=None, I_ust_motor_A=None, P_ust_W=sabit["P_W"],
                         sinir_birincil="pil (güç aktarımı)")
            r.update(ruzgar=v_ust, ruzgar_notu="v_üst = konum tutabileceği azami hava hızı")
        else:
            # İrtifa tutulamaz: tam gaz, eğim θ; yatay kuvvet T_max·sinθ, düşey (T_max·cosθ − W) < 0
            F0 = tg["T_max_N"] * math.sin(th)
            a0 = F0 / m
            a_z = (tg["T_max_N"] * math.cos(th) - W) / m
            v_ust = math.sqrt(2.0 * F0 / (RHO * cda_t))
            r.update(rejim="irtifa tutamaz — tam gaz, düşüşte (yalnız yatay bileşen)", a0=a0, v_ust=v_ust,
                     a_z=a_z, sinir_birincil="itki",
                     t95=t_kapali(UST_HIZ_ORANI * v_ust, v_ust, a0),
                     t60=t_kapali(V_60, v_ust, a0), t100=t_kapali(V_100, v_ust, a0),
                     zaman_yontemi="kapalı form (yatay bileşen; düşüş hızı ayrı, dalış sürüklemesi ihmal)",
                     I_ust_A=tg["I_A"], V_yuk_ust=tg["V_yuk"], I_ust_motor_A=tg["I_motor_A"],
                     ruzgar=None, ruzgar_notu="konum tutulamaz (irtifa kaybı)")
            F = lambda v: F0 - aa * v * v  # noqa: E731
            hedefler = [UST_HIZ_ORANI * v_ust, V_60, V_100]
            sur = entegre(F, m, hedefler)
            r["t95_rk4"] = sur[hedefler[0]]
    # --- Akım bayrakları ---
    bayrak = []
    if r["I_TG_motor_A"] > ESC_SUREKLI_A_MOTOR:
        bayrak.append("tam gaz > ESC %g A/motor" % ESC_SUREKLI_A_MOTOR)
    if r["I_TG_A"] > PM06_TEPE_A:
        bayrak.append("tam gaz > PM06 tepe %g A" % PM06_TEPE_A)
    if r.get("I_ust_A") is not None:
        if r["I_ust_A"] > PM06_SUREKLI_A:
            bayrak.append("v_üst'te > PM06 sürekli %g A" % PM06_SUREKLI_A)
        if r["I_ust_motor_A"] > ESC_SUREKLI_A_MOTOR:
            bayrak.append("v_üst'te > ESC %g A/motor" % ESC_SUREKLI_A_MOTOR)
    r["akim_bayraklari"] = bayrak
    r["sinir"] = r["sinir_birincil"] + (("; akım: " + "; ".join(bayrak)) if bayrak else "")
    # --- Enerji ---
    if r.get("I_ust_A"):
        r["mAh_1dk"] = r["I_ust_A"] * 1000.0 / 60.0
        r["sure80_dk"] = KULLANILABILIR_PIL * kf["kapasite_Ah"] / r["I_ust_A"] * 60.0
    else:
        r["mAh_1dk"] = None
        r["sure80_dk"] = None
    return r


def theta_max_hesapla(kal: dict, kf: dict, V_acik: float) -> dict:
    tg = tam_gaz_cozum(kal, kf, V_acik)
    W = kal["W_N"]
    if tg["TW"] < 1.0:
        return dict(V_acik=V_acik, TW_max=tg["TW"], theta_max_deg=None, ruzgar_ms=None, I_A=tg["I_A"], V_yuk=tg["V_yuk"])
    thm = math.acos(1.0 / tg["TW"])
    ruz = math.sqrt(2.0 * W * math.tan(thm) / (RHO * cda(math.degrees(thm))))
    return dict(V_acik=V_acik, TW_max=tg["TW"], theta_max_deg=math.degrees(thm), ruzgar_ms=ruz,
                ruzgar_kmh=ruz * 3.6, I_A=tg["I_A"], I_motor_A=tg["I_motor_A"], V_yuk=tg["V_yuk"],
                notu="θ_max'ta gaz %100 — kontrol payı sıfır")


# =====================================================================
#  Biçimlendirme
# =====================================================================


def f(x, nd=1):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    x = round(float(x), nd) + 0.0   # -0,0 → 0,0
    return ("%.*f" % (nd, x)).replace(".", ",")


def f_sure(t, v_ust):
    if t is None:
        return "✗ (asimptot %s km/h)" % f(v_ust * 3.6, 0)
    return f(t, 1) + " s"


def f_tw(x):
    if x == float("inf"):
        return "∞"
    return f(x, 2)


def yuvarla(o, nd=4, anlamli=6):
    """JSON için yuvarlama: |x| ≥ 1e-2 → nd ondalık; küçük büyüklükler (k_T ~1e-7, k_P ~1e-9)
    → `anlamli` anlamlı basamak (aksi hâlde 0,0'a çöker)."""
    if isinstance(o, dict):
        return {k: yuvarla(v, nd, anlamli) for k, v in o.items()}
    if isinstance(o, list):
        return [yuvarla(v, nd, anlamli) for v in o]
    if isinstance(o, float):
        if math.isinf(o):
            return "inf"
        if math.isnan(o):
            return None
        if o == 0.0:
            return 0.0
        if abs(o) < 1e-2:
            return float("%.*e" % (anlamli - 1, o))
        return round(o, nd) + 0.0   # + 0.0: -0,0 → 0,0
    return o


SUTUNLAR = ("θ | pil V_açık | gereken T/W | T_max/W | irtifa | a0 m/s² | v_üst m/s (km/h) | %95 v_üst süre | "
            "0–60 km/h | 0–100 km/h | tam gaz A @ V_yük | v_üst'te A | azami rüzgar m/s | 1 dk mAh | %80 pil dk | sınırlayıcı")


def ozet_tablo_md(k: dict) -> str:
    """Kompakt özet: her eğim için 'dolu' (2. senaryo) satırı + T_max/W aralığı (3 senaryo)."""
    dolu_ad = k["pil_senaryolari"][1][0]
    out = ["| θ | gereken T/W | T_max/W (3 senaryo) | irtifa (dolu) | a0 m/s² | v_üst m/s (km/h) | %95 süre | 0–60 | 0–100 | tam gaz A @ V_yük | v_üst'te A | rüzgar m/s | %80 pil dk | sınırlayıcı |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for theta in EGIMLER_DEG:
        rs = [r for r in k["satirlar"] if r["theta_deg"] == theta]
        r = [x for x in rs if x["senaryo"] == dolu_ad][0]
        tw_aralik = "–".join([f(min(x["TW_max"] for x in rs), 2), f(max(x["TW_max"] for x in rs), 2)])
        tut = "✓" if r["tutar"] else "✗ (a_z %s)" % f(r["a_z"], 2)
        v_txt = f(r["v_ust"], 1) + " (" + f(r["v_ust"] * 3.6, 0) + ")" + ("" if r["tutar"] or theta == 0 else " dalış")
        out.append("| %s° | %s | %s | %s | %s | %s | %s | %s | %s | %s @ %s V | %s | %s | %s | %s |" % (
            theta, f_tw(r["gerek_TW"]), tw_aralik, tut, f(r["a0"], 1), v_txt,
            f_sure(r["t95"], r["v_ust"]) if r["v_ust"] > 0 else "—", f_sure(r["t60"], r["v_ust"]), f_sure(r["t100"], r["v_ust"]),
            f(r["I_TG_A"], 0), f(r["V_yuk_TG"], 2), f(r["I_ust_A"], 0),
            f(r["ruzgar"], 1) if r["ruzgar"] is not None else "—", f(r["sure80_dk"], 1), r["sinir_birincil"]))
    return "\n".join(out)


def tablo_md(satirlar: list[dict]) -> str:
    bas = "| " + SUTUNLAR.replace(" | ", " | ") + " |"
    ayrac = "|" + "|".join(["---"] * (SUTUNLAR.count("|") + 1)) + "|"
    out = [bas, ayrac]
    for r in satirlar:
        tutar = "✓" if r["tutar"] else ("✗ düşüş a_z %s" % f(r["a_z"], 2) if r.get("a_z") is not None else "✗")
        v_txt = f(r["v_ust"], 1) + " (" + f(r["v_ust"] * 3.6, 0) + ")"
        if not r["tutar"] and r["theta_deg"] > 0:
            v_txt += " yalnız dalışta"
        ruz = f(r["ruzgar"], 1) if r["ruzgar"] is not None else "—"
        out.append("| %s° | %s V %s | %s | %s | %s | %s | %s | %s | %s | %s | %s @ %s V | %s | %s | %s | %s | %s |" % (
            r["theta_deg"], f(r["V_acik"], 2), r["senaryo"], f_tw(r["gerek_TW"]), f(r["TW_max"], 2), tutar,
            f(r["a0"], 2), v_txt, f_sure(r["t95"], r["v_ust"]) if r["v_ust"] > 0 else "—",
            f_sure(r["t60"], r["v_ust"]), f_sure(r["t100"], r["v_ust"]),
            f(r["I_TG_A"], 0), f(r["V_yuk_TG"], 2), f(r["I_ust_A"], 0), ruz,
            f(r["mAh_1dk"], 0), f(r["sure80_dk"], 1), r["sinir"]))
    return "\n".join(out)


# =====================================================================
#  Grafikler  (dataviz: kategorik renk = konfig, çizgi tipi = pil senaryosu)
# =====================================================================
RENK = {"4S_13Ah_9x5x3": "#2a78d6", "3S_8Ah_1045": "#eb6834"}
CIZGI = ["-", "--", ":"]
MURKKEP = "#52514e"
IZGARA = "#e1e0d9"
EKSEN = "#c3c2b7"


def grafik(sonuc: dict, anahtar: str, y_etiket: str, baslik: str, dosya: str, ref_cizgiler=None, ylim0=True):
    fig, ax = plt.subplots(figsize=(8.5, 5.2), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for k in sonuc["konfigler"]:
        kimlik = k["kimlik"]
        for si, sen in enumerate(k["pil_senaryolari"]):
            satirlar = [r for r in k["satirlar"] if r["senaryo"] == sen[0]]
            xs = [r["theta_deg"] for r in satirlar]
            ys = []
            for r in satirlar:
                v = r.get(anahtar)
                if anahtar == "t60" and v is None:
                    v = float("nan")
                ys.append(float("nan") if v is None else v)
            etiket = "%s — %s V" % (k["ad"], f(sen[1], 2))
            ax.plot(xs, ys, CIZGI[si], color=RENK[kimlik], lw=2, label=etiket, zorder=3)
            for r, y in zip(satirlar, ys):
                if math.isnan(y):
                    continue
                ax.plot([r["theta_deg"]], [y], "o", ms=6, mec=RENK[kimlik], mew=1.6,
                        mfc=(RENK[kimlik] if r["tutar"] else "#fcfcfb"), zorder=4)
    if ref_cizgiler:
        ymax_veri = max(ax.get_ylim())
        for yv, txt in ref_cizgiler:
            ax.axhline(yv, color="#898781", lw=1, ls="-.", zorder=2)
            # etiket sağa yaslı, çizginin ALTINDA (~%3 eksen payı): 70°–90° bandında
            # çizginin hemen altında veri yok (3S en düşük eğri ≥ 64 A, 4S ≥ 110 A)
            ax.text(90, yv - 0.03 * ymax_veri, txt, color="#898781", fontsize=8, va="top", ha="right",
                    bbox=dict(facecolor="#fcfcfb", edgecolor="none", pad=1.5), zorder=5)
    ax.set_xticks(EGIMLER_DEG)
    ax.set_xlabel("eğim θ (°)", color=MURKKEP)
    ax.set_ylabel(y_etiket, color=MURKKEP)
    ax.set_title(baslik, color="#0b0b0b", fontsize=11, loc="left")
    ax.grid(True, color=IZGARA, lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(EKSEN)
    ax.tick_params(colors=MURKKEP)
    if ylim0:
        ax.set_ylim(bottom=0)
    ax.legend(fontsize=8, frameon=True, facecolor="#fcfcfb", edgecolor="none", framealpha=0.95, loc="best")
    fig.text(0.01, 0.01, "dolu işaret: irtifa tutar · boş işaret: irtifa tutamaz (yalnız dalışta) · yazılımsal sınırlar yok sayıldı",
             fontsize=7, color="#898781")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(BURASI, dosya))
    plt.close(fig)


# =====================================================================
#  RAPOR
# =====================================================================


def rapor_yaz(sonuc: dict) -> str:
    L = []
    P = sonuc["parametreler"]
    L.append("# Performans zarfı — 4S 13 Ah + 9x5x3 ve 3S 8 Ah + 1045 (yazılımsal sınırlar yok sayıldı)")
    L.append("")
    L.append("Üretim: %s · betik: `results/ucus_analiz_20260915/performans_zarfi/performans_modeli.py` · "
             "numpy %s · tüm sayılar betik çıktısıdır (`tablolar.json`)." % (sonuc["meta"]["uretim_zamani"], np.__version__))
    L.append("")
    L.append("**Bu bir HESAPTIR, ölçüm değil.** Ölçülen yalnız kalibrasyon noktalarıdır (askı ve 4S tam gaz). "
             "Kütle, CdA, ρ ve KV ölçülmedi — parametre olarak alındı ve aşağıda yazılıdır. "
             "ANGLE_MAX 30°, LOIT_SPEED 12,5 m/s, WPNAV_SPEED 3 m/s **yok sayıldı** (kullanıcı: \"yazılımsal sınırlar kalksaydı\").")
    L.append("")
    # ---- Model ----
    L.append("## 1. Model (denklemler ve kaynakları)")
    L.append("")
    L.append("1. **Motor-pervane.** `u_eff = SPIN_MIN + (SPIN_MAX − SPIN_MIN)·a(ThO)`, `a(x) = ((e−1) + √((1−e)² + 4·e·x)) / (2e)`, e = MOT_THST_EXPO = %s "
             "(ArduPilot `AP_Motors::thrust_to_actuator`, lift_max = 1). **MOT_THST_EXPO ne yapar:** itkinin PWM ile yaklaşık karesel arttığını telafi etmek için "
             "kontrolcünün itki isteğine (ThO) ters/kök bir eğri uygular; böylece ThO'nun yarısı yaklaşık yarı itki verir. "
             "Expo'nun PWM yolunda olduğu ölçümle doğrulandı: F logu askıda ölçülen ortalama PWM %s µs; expo'lu model %s µs, expo'suz %s µs "
             "(expo'suz haritayla iki 4S ankrajı bağdaşmaz: tam gaz T/W öngörüsü %s olurdu, ölçülen %s)."
             % (f(MOT_THST_EXPO, 2), f(sonuc["kalibrasyon"]["4S_13Ah_9x5x3"]["pwm_aski_olculen_us"], 0),
                f(sonuc["kalibrasyon"]["4S_13Ah_9x5x3"]["pwm_aski_model_us"], 0),
                f(sonuc["kalibrasyon"]["4S_13Ah_9x5x3"]["pwm_aski_expo_suz_us"], 0),
                f(sonuc["kalibrasyon"]["4S_13Ah_9x5x3"]["TW_tam_gaz_expo_suz_model"], 2),
                f(sonuc["kalibrasyon"]["4S_13Ah_9x5x3"]["TW_tam_gaz_olculen"], 2)))
    L.append("   `RPM_KV = KV·V_yük·u_eff` (yüksüz KV modeli, KV = %s rpm/V üretici beyanı), `T = k_T·RPM²`, `P_el = k_P·RPM³`, `I = P_el/V_yük` (verim sabit). "
             "k_T = W/RPM_askı², k_P = P_askı/RPM_askı³ (askı noktası: T = W)." % f(KV_RPM_PER_V, 0))
    L.append("   **Tam gaz RPM sarkması:** `RPM_TG = s_TG·KV·V_yük·SPIN_MAX`. s_TG 4S tam gaz noktasından (T/W = 1,91 @ 12,36 V) kalibre edilir: "
             "yük altında RPM, yüksüz KV ekstrapolasyonunun altında kalır (motor I·R sarkması). 3S+1045 için tam gaz ölçümü YOK → aynı s_TG **aktarıldı** (aynı motor/ESC; belirsizlik notu §2 ve §6).")
    L.append("   Sonuç: `T_max(V_yük) = k_T·(s_TG·KV·V_yük·0,95)²`, `P(T) = k_P·(T/k_T)^1,5` (P ∝ T^1,5, momentum teorisi).")
    L.append("2. **Pil.** `V_yük = V_açık − I·R_paket` (4S %s mΩ, 3S %s mΩ; ölçüm). Tam gazda I = P(V_yük)/V_yük = c·V_yük² olduğundan V_yük ve I **kapalı döngü** çözülür "
             "(sönümlü sabit-nokta iterasyonu; ikinci derece kapalı formla doğrulandı). Sabit itkide V² − V_açık·V + R·P = 0, yüksek gerilim kökü; diskriminant < 0 ise paket gücü veremez."
             % (f(1000 * KONFIGLER[0]["R_paket_ohm"], 1), f(1000 * KONFIGLER[1]["R_paket_ohm"], 1)))
    L.append("3. **Eğim.** θ = 0: dikey tırmanış, `T(v) = T_max·(1 − v/v_pitch)`, `v_pitch = pitch·RPM_TG/60` (9x5x3: 5″ = 0,127 m; 1045: 4,5″ = 0,1143 m); "
             "`m·dv/dt = T(v) − W − ½ρ·CdA(0)·v²`, RK4 (dt = %s s). θ = 30–66°: irtifa sabit düz uçuş, gereken `T = W/cosθ`, yatay kuvvet `W·tanθ`, sürükleme `½ρ·v²·CdA(θ)`, "
             "`a0 = g·tanθ`, `v_üst = √(2·W·tanθ / (ρ·CdA(θ)))`, `v(t) = v_üst·tanh(a0·t/v_üst)`, `t(v) = (v_üst/a0)·atanh(v/v_üst)` (RK4 ile çapraz kontrol, azami sapma %s %%). "
             "T_max < W/cosθ ise **irtifa tutamaz**: tam gazla yatay kuvvet `T_max·sinθ`, düşey ivme `(T_max·cosθ − W)/m` < 0, v_üst \"yalnız dalışta\"; sürdürülebilir azami eğim `θ_max = acos(W/T_max)`. "
             "θ = 90: itki tamamen yatay, yatay ivme T_max/m, düşüş ivmesi g."
             % (f(DT, 3), f(sonuc["meta"]["kapali_form_vs_rk4_maks_sapma_pct"], 3)))
    L.append("   `CdA(θ) = %s·(1 + %s·sinθ)` m², ρ = %s kg/m³, g = %s m/s². \"Üst hıza süre\" = %%95·v_üst; 0–60 km/h = 16,67 m/s, 0–100 = 27,78 m/s; ulaşılmıyorsa ✗ (asimptot)."
             % (f(CDA0, 2), f(CDA_EGIM_K, 1), f(RHO, 2), f(G, 5)))
    L.append("4. **Akım.** v_üst'te (irtifa tutan satırlarda) T = W/cosθ → P(T) → I, V_yük ile birlikte çözülür; tam gaz akımı (ivmelenme başı) 2'deki kapalı döngüden. "
             "Kıyas: ESC %s A/motor sürekli (ad plakası; %s A tepe veri sayfası doğrulanmadı); PM06 %s A sürekli / %s A tepe (**veri sayfası doğrulanmadı**, bellekten). "
             "Ölçülen 115 A tepe PM06'dan geçti (E logu)." % (f(ESC_SUREKLI_A_MOTOR, 0), f(ESC_TEPE_A_MOTOR, 0), f(PM06_SUREKLI_A, 0), f(PM06_TEPE_A, 0)))
    L.append("5. **Rüzgar.** O eğimde konum tutabileceği azami rüzgar = v_üst (hava hızı). Ayrıca T_max ile θ_max ve ona karşılık rüzgar (gaz %100, kontrol payı sıfır).")
    L.append("6. **Enerji.** v_üst'te 1 dk: `I_üst·1000/60` mAh; %s pil ile kalan süre `%s·C / I_üst · 60` dk (C = beyan kapasite)." % ("%80", f(KULLANILABILIR_PIL, 2)))
    L.append("")
    L.append("İhmal edilenler: ileri uçuşta rotor gücünün değişimi (translational lift / profil gücü), dalışta düşey sürükleme, ESC/motor verim değişimi, pil sıcaklığı ve SoC'ye bağlı R.")
    L.append("")
    # ---- Kalibrasyon ----
    L.append("## 2. Kalibrasyon (ölçülen ankraj noktaları → model katsayıları)")
    L.append("")
    for k in sonuc["konfigler"]:
        kal = sonuc["kalibrasyon"][k["kimlik"]]
        kf = k["kf"]
        L.append("### %s" % k["ad"])
        L.append("")
        L.append("| büyüklük | değer | kaynak |")
        L.append("|---|---|---|")
        L.append("| kütle (VARSAYIM) | %s kg → W = %s N | kullanıcı parametresi; ölçülmedi |" % (f(kf["kutle_kg"], 2), f(kal["W_N"], 2)))
        L.append("| askı ankrajı | ThO %s, V_yük %s V, I %s A, P %s W (%s s) | %s |" % (
            f(kf["aski"]["ThO"], 3), f(kf["aski"]["V_yuk"], 2), f(kf["aski"]["I_A"], 1), f(kal["P_aski_W"], 0), kf["aski"]["sure_s"], kf["aski"]["kaynak"]))
        L.append("| u_eff(askı), PWM | %s → %s µs (expo'lu); ölçülen ort. PWM %s | model / F ozet.json `rcou.ort_pwm_orani` |" % (
            f(kal["u_eff_aski_model"], 3), f(kal["pwm_aski_model_us"], 0),
            (f(kal["pwm_aski_olculen_us"], 0) + " µs") if kal["pwm_aski_olculen_us"] else "havuz değeri yok"))
        L.append("| RPM_askı (KV modeli) | %s rpm | KV·V·u_eff |" % f(kal["rpm_aski_KV"], 0))
        L.append("| k_T | %.4e N/rpm² (motor başına askı itkisi %s N) | W/RPM_askı² |" % (kal["k_T_N_per_rpm2"], f(kal["T_motor_aski_N"], 2)))
        L.append("| k_P | %.4e W/rpm³ (motor başına askı gücü %s W) | P_askı/RPM_askı³ |" % (kal["k_P_W_per_rpm3"], f(kal["P_motor_aski_W"], 1)))
        if kf.get("tam_gaz"):
            tg = kf["tam_gaz"]
            L.append("| tam gaz ankrajı | T/W %s (a %s m/s², alt sınır: hava direnci ihmal), V_yük %s V, I %s A, RCOU maks %s | %s |" % (
                f(tg["TW"], 2), f(tg["a_ms2"], 2), f(tg["V_yuk"], 2), f(tg["I_A"], 0), tg["rcou_maks"], tg["kaynak"]))
            L.append("| T/W_TG yüksüz KV modeli (s_TG = 1) | %s | k_T·(KV·12,36·0,95)²/W — ölçülenden %s %% yüksek → sarkma gerekli |" % (
                f(kal["TW_tam_gaz_KV_modeli"], 2), f(100 * (kal["TW_tam_gaz_KV_modeli"] / kal["TW_tam_gaz_olculen"] - 1), 1)))
            L.append("| **s_TG** (RPM sarkma çarpanı) | **%s** (c_T = s² = %s; RPM_TG model %s rpm) | √(T/W_ölçülen / T/W_KV) — %s |" % (
                f(kal["s_TG"], 4), f(kal["c_T"], 3), f(kal["rpm_tam_gaz_model"], 0), kal["s_TG_kaynak"]))
            L.append("| çapraz kontrol: tam gaz güç | model %s W / %s A; ölçülen %s W / %s A (sapma %s %%) | P ∝ T^1,5 tutarlılığı |" % (
                f(kal["P_tam_gaz_model_W"], 0), f(kal["I_tam_gaz_model_A"], 1), f(kal["P_tam_gaz_olculen_W"], 0), f(kal["I_tam_gaz_olculen_A"], 0), f(kal["P_tam_gaz_sapma_pct"], 1)))
            L.append("| motor başına tam gaz itkisi | %s N (%s kgf) @ %s A/motor | T_max/4 |" % (
                f(kal["T_motor_tam_gaz_N"], 2), f(kal["T_motor_tam_gaz_N"] / G, 2), f(tg["I_A"] / MOTOR_N, 1)))
        else:
            L.append("| tam gaz ankrajı | **ÖLÇÜM YOK** | — |")
            L.append("| **s_TG** | **%s** (c_T = %s) | %s |" % (f(kal["s_TG"], 4), f(kal["c_T"], 3), kal["s_TG_kaynak"]))
            L.append("| belirsizlik | s_TG = 1 alınsaydı T_max/W (dolu pil) %s yerine %s olurdu; 3S'te tam gaz akımı 4S'ten düşük → sarkma daha az → gerçek değer bu iki sayı arasında |" % (
                f(kal["TW_dolu_sTG"], 2), f(kal["TW_dolu_sTG1"], 2)))
        if kal.get("ikinci_aski_kontrol"):
            ik = kal["ikinci_aski_kontrol"]
            L.append("| çapraz kontrol: D logu askısı | model T/W %s, I %s A; ölçülen I %s A | %s |" % (
                f(ik["TW_model"], 2), f(ik["I_model_A"], 1), f(ik["I_olculen_A"], 1), ik["kaynak"]))
        L.append("| R_paket | %s mΩ | %s |" % (f(1000 * kf["R_paket_ohm"], 1), "F ozet.json ic_direnc.a_kalkis_gecisi (r² 0,995)" if kf["hucre"] == 4 else "A ozet.json R_uydurma_ohm_paket.ort (n=18)"))
        L.append("| pil senaryoları V_açık | %s | kullanıcı |" % "; ".join("%s V (%s)" % (f(v, 2), a) for a, v in kf["pil_senaryolari"]))
        L.append("")
    # ---- Tablolar ----
    for k in sonuc["konfigler"]:
        kf = k["kf"]
        L.append("## %s. Tablo — %s" % (3 if k["kimlik"].startswith("4S") else 4, k["ad"]))
        L.append("")
        L.append("Satırlar: eğim θ × pil senaryosu. \"tam gaz A @ V_yük\": ivmelenme başı, kapalı döngü çözümü. \"v_üst'te A\": irtifa tutan satırlarda T = W/cosθ sabit hız akımı; "
                 "tutamayan satırlarda tam gaz akımı. 0° satırı dikey tırmanıştır (hızlar düşey).")
        L.append("")
        L.append(tablo_md(k["satirlar"]))
        L.append("")
        L.append("**Parametreler (%s):** kütle %s kg (VARSAYIM), W = %s N, CdA(θ) = %s·(1 + %s·sinθ) m², ρ = %s kg/m³, R_paket = %s mΩ, "
                 "pervane %s (pitch %s m), KV %s rpm/V, SPIN_MIN/MAX %s/%s, EXPO %s, kapasite %s Ah (%s kullanılabilir), "
                 "kalibrasyon: askı (ThO %s, %s V, %s A) → k_T %.3e N/rpm², k_P %.3e W/rpm³; s_TG %s (%s)." % (
                     k["ad"], f(kf["kutle_kg"], 2), f(sonuc["kalibrasyon"][k["kimlik"]]["W_N"], 2), f(CDA0, 2), f(CDA_EGIM_K, 1), f(RHO, 2),
                     f(1000 * kf["R_paket_ohm"], 1), kf["pervane"], f(kf["pitch_m"], 4), f(KV_RPM_PER_V, 0), f(MOT_SPIN_MIN, 2), f(MOT_SPIN_MAX, 2),
                     f(MOT_THST_EXPO, 2), f(kf["kapasite_Ah"], 0), "%80",
                     f(kf["aski"]["ThO"], 3), f(kf["aski"]["V_yuk"], 2), f(kf["aski"]["I_A"], 1),
                     sonuc["kalibrasyon"][k["kimlik"]]["k_T_N_per_rpm2"], sonuc["kalibrasyon"][k["kimlik"]]["k_P_W_per_rpm3"],
                     f(sonuc["kalibrasyon"][k["kimlik"]]["s_TG"], 4), sonuc["kalibrasyon"][k["kimlik"]]["s_TG_kaynak"]))
        L.append("")
        L.append("**Senaryo başına θ_max (T_max ile sürdürülebilir azami eğim) ve o eğimde rüzgar:**")
        L.append("")
        L.append("| V_açık | tam gaz V_yük / I | T_max/W | θ_max | rüzgar @ θ_max (m/s, km/h) | v_pitch (0°) |")
        L.append("|---|---|---|---|---|---|")
        for tm in k["theta_max"]:
            L.append("| %s V (%s) | %s V / %s A (%s A/motor) | %s | %s° | %s (%s) | %s m/s |" % (
                f(tm["V_acik"], 2), tm["senaryo"], f(tm["V_yuk"], 2), f(tm["I_A"], 0), f(tm.get("I_motor_A"), 1), f(tm["TW_max"], 2),
                f(tm["theta_max_deg"], 1), f(tm["ruzgar_ms"], 1), f(tm.get("ruzgar_kmh"), 0), f(tm["v_pitch"], 1)))
        L.append("")
        L.append("**Sınırlayıcı etken sütunu:** *sürükleme* = v_üst'ü CdA belirler (itki yeter); *itki* = T_max < W/cosθ, irtifa tutulamaz; "
                 "*pitch hızı* = dikey tırmanışta pervane pitch hızı sürüklemeden önce sınırlar; *pil (güç aktarımı)* = V_açık² < 4·R·P; "
                 "*akım* ekleri = ESC/PM06 sınırının aşıldığı yer (PM06 sınırları veri sayfasından doğrulanmadı).")
        L.append("")
    # ---- Grafikler ----
    L.append("## 5. Grafikler (iki konfig üst üste; çizgi tipi = pil senaryosu; boş işaret = irtifa tutamaz)")
    L.append("")
    for g in sonuc["grafikler"]:
        L.append("![%s](%s)" % (g["baslik"], g["dosya"]))
        L.append("")
    # ---- Uyarılar ----
    L.append("## 6. Uyarılar ve varsayımlar")
    L.append("")
    for u in sonuc["uyarilar"]:
        L.append("- " + u)
    L.append("")
    return "\n".join(L)


# =====================================================================
#  ANA
# =====================================================================


def main() -> dict:
    kalibrasyon = {}
    s_TG_4S = None
    konfig_sonuc = []
    maks_sapma = 0.0
    for kf in KONFIGLER:
        kal = kalibre(kf, s_TG_aktarim=s_TG_4S)
        if kf["tam_gaz"]:
            s_TG_4S = kal["s_TG"]
        else:
            # belirsizlik notu için s_TG = 1 ile dolu pil T_max/W
            dolu_V = kf["pil_senaryolari"][1][1]
            kal["TW_dolu_sTG"] = tam_gaz_cozum(kal, kf, dolu_V)["TW"]
            kal1 = dict(kal)
            kal1["s_TG"] = 1.0
            kal["TW_dolu_sTG1"] = tam_gaz_cozum(kal1, kf, dolu_V)["TW"]
        kalibrasyon[kf["kimlik"]] = kal
        satirlar = []
        for theta in EGIMLER_DEG:
            for sen_ad, V_acik in kf["pil_senaryolari"]:
                r = satir_hesapla(kf, kal, sen_ad, V_acik, theta)
                if r.get("t95_rk4") is not None and r.get("t95") is not None:
                    maks_sapma = max(maks_sapma, 100.0 * abs(r["t95_rk4"] / r["t95"] - 1.0))
                satirlar.append(r)
        theta_max = []
        for sen_ad, V_acik in kf["pil_senaryolari"]:
            tm = theta_max_hesapla(kal, kf, V_acik)
            tm["senaryo"] = sen_ad
            tm["v_pitch"] = kf["pitch_m"] * tam_gaz_cozum(kal, kf, V_acik)["rpm"] / 60.0
            theta_max.append(tm)
        konfig_sonuc.append(dict(kimlik=kf["kimlik"], ad=kf["ad"], kf=kf, pil_senaryolari=kf["pil_senaryolari"],
                                 satirlar=satirlar, theta_max=theta_max))

    uyarilar = [
        "Kütle ÖLÇÜLMEDİ: 4S 3,0 kg ve 3S 2,5 kg VARSAYIM. T/W ölçümü kütleden bağımsızdır; Newton cinsinden itki, ivme (a0 = g·(T/W−1) hariç), v_üst (√W ile) ve enerji kütleyle ölçeklenir.",
        "4S T/W = 1,91 hava direnci ihmal edilmiş ALT SINIRDIR (E_1240_ivme/ozet.json: ivme tepesi t0+%s s'de hız ≈ %s m/s → sürükleme ½ρ·CdA(0)·v² = %s N = W'nin %%%s'i; tepe hız %s m/s'de %s N = %%%s). "
        "Tablolar bu alt sınıra kalibre olduğundan itki türevli sayılar (T_max/W, θ_max, a0) da alt sınırdır." % (
            f(E_IVME_TEPE_IVME_T_S, 1), f(E_IVME_HIZ_TEPE_IVME_ANINDA_MS, 1),
            f(0.5 * RHO * CDA0 * E_IVME_HIZ_TEPE_IVME_ANINDA_MS ** 2, 2), f(100 * 0.5 * RHO * CDA0 * E_IVME_HIZ_TEPE_IVME_ANINDA_MS ** 2 / (KONFIGLER[0]["kutle_kg"] * G), 1),
            f(E_IVME_TEPE_HIZ_MS, 2), f(0.5 * RHO * CDA0 * E_IVME_TEPE_HIZ_MS ** 2, 2), f(100 * 0.5 * RHO * CDA0 * E_IVME_TEPE_HIZ_MS ** 2 / (KONFIGLER[0]["kutle_kg"] * G), 1)),
        "MODEL SAPMASI (görev tanımına göre): görev tanımı u_eff = SPIN_MIN + (SPIN_MAX − SPIN_MIN)·ThO (expo'suz) der; bu haritayla iki 4S ankrajı BAĞDAŞMAZ "
        "(askı ThO 0,36 → u_eff 0,438, tam gaz u_eff 0,95: T/W_TG = (12,36·0,95/(14,0·0,438))² = %s, ölçülen 1,91) ve F logunda ölçülen askı PWM'i (%s µs) expo'suz haritanın (%s µs) değil expo'lu haritanın (%s µs) yanındadır. "
        "Bu yüzden ArduPilot'un gerçek ThO→PWM eğrisi (MOT_THST_EXPO %s) kullanıldı ve tam gaz ankrajı bir RPM sarkma çarpanıyla (s_TG = %s) sağlandı. "
        "k_T ve k_P askı noktasından, s_TG tam gaz noktasından: iki ankraj da BİREBİR sağlanır; tam gaz gücü bağımsız çapraz kontroldür (model %s A, ölçülen 115 A)." % (
            f(kalibrasyon["4S_13Ah_9x5x3"]["TW_tam_gaz_expo_suz_model"], 2), f(kalibrasyon["4S_13Ah_9x5x3"]["pwm_aski_olculen_us"], 0),
            f(kalibrasyon["4S_13Ah_9x5x3"]["pwm_aski_expo_suz_us"], 0), f(kalibrasyon["4S_13Ah_9x5x3"]["pwm_aski_model_us"], 0),
            f(MOT_THST_EXPO, 2), f(s_TG_4S, 4), f(kalibrasyon["4S_13Ah_9x5x3"]["I_tam_gaz_model_A"], 1)),
        "3S + 1045 için TAM GAZ ÖLÇÜMÜ YOK: T_max, 4S'ten aktarılan RPM sarkma çarpanı s_TG = %s ile askı noktasından ekstrapolasyondur; s_TG = 1 üst sınırı §2'de verildi. 1045 2 pal ve 9x5x3 3 pal farklı pervanelerdir — k_T/k_P her biri kendi askısından, sarkma ortak varsayıldı." % f(s_TG_4S, 4),
        "Model RPM ∝ V_yük·u_eff (yüksüz KV) varsayar; sarkma tek çarpanla yalnız tam gazda düzeltildi. Kısmi gazda (v_üst'te akım) P ∝ T^1,5 zinciri kullanıldığından RPM haritası devreye girmez; tam gazda 4S için 12,36 V civarında doğru, uzak V_yük'te belirsiz.",
        "v_pitch modeli T(v) = T_max·(1 − v/v_pitch) doğrusal bir basitleştirmedir; gerçek pervanenin ileri hızda itki düşüşü ve tırmanışta güç değişimi ölçülmedi. Dikey tırmanış akımı tam gaz akımı olarak alındı (üst sınır).",
        "İrtifa tutamayan satırlarda (T_max < W/cosθ ve θ = 90°) 'v_üst' yalnız yatay bileşendir ve araç düşmektedir (a_z sütunda); pratikte anlamı 'o eğimde yatay asimptot', uçuş rejimi değil.",
        "PM06 sürekli/tepe akım sınırları (60/120 A) veri sayfasından DOĞRULANMADI; ESC 80 A tepe de doğrulanmadı. Yalnız 60 A/motor ad plakası kesindir. Ölçülen 115 A tepe PM06'dan geçti (E logu, 0,7 s).",
        "R_paket sabit alındı (4S %s mΩ F logu kalkış geçişinde 0–37 A aralığında uyduruldu, 115 A'ya ekstrapolasyon; 3S %s mΩ A havuzu 18 uçuş ortalaması, p05–p95 19,8–75,4 mΩ). "
        "E logunda V_arm %s V → 115 A'da model V_yük %s V, ölçülen 12,36 V (sapma %s %%)." % (
            f(1000 * KONFIGLER[0]["R_paket_ohm"], 1), f(1000 * KONFIGLER[1]["R_paket_ohm"], 1), f(E_TAM_GAZ_V_ARM, 2),
            f(E_TAM_GAZ_V_ARM - KONFIGLER[0]["tam_gaz"]["I_A"] * KONFIGLER[0]["R_paket_ohm"], 2),
            f(100 * ((E_TAM_GAZ_V_ARM - KONFIGLER[0]["tam_gaz"]["I_A"] * KONFIGLER[0]["R_paket_ohm"]) / KONFIGLER[0]["tam_gaz"]["V_yuk"] - 1), 1)),
        "İleri uçuşta rotor gücü (translational lift, profil gücü), dalış sürüklemesi, ESC/motor verim değişimi ve pil sıcaklığı ihmal edildi; 'v_üst'te akım' askı verimiyle hesaplanır.",
        "CdA = 0,08·(1 + 0,5·sinθ) m² ve ρ = 1,15 kg/m³ VARSAYIM; v_üst ∝ 1/√CdA — CdA %25 büyürse v_üst %11 düşer.",
        "Bütün yazılımsal sınırlar (ANGLE_MAX 30°, LOIT_SPEED 12,5 m/s, WPNAV_SPEED 3 m/s, PSC_* ivme sınırları) yok sayıldı; tablolar donanım zarfıdır, uçulabilir zarf değil.",
    ]

    sonuc = dict(
        meta=dict(uretim_zamani=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                  betik=os.path.relpath(os.path.abspath(__file__), os.path.dirname(os.path.dirname(ANALIZ_KOK))).replace("\\", "/"),
                  python=sys.version.split()[0], numpy=np.__version__, matplotlib=matplotlib.__version__,
                  kapali_form_vs_rk4_maks_sapma_pct=maks_sapma,
                  yazilimsal_sinirlar="YOK SAYILDI (ANGLE_MAX 30, LOIT_SPEED 12,5 m/s, WPNAV_SPEED 3 m/s)"),
        parametreler=dict(g=G, rho=RHO, CdA0=CDA0, CdA_egim_k=CDA_EGIM_K, egimler_deg=EGIMLER_DEG,
                          MOT_SPIN_MIN=MOT_SPIN_MIN, MOT_SPIN_MAX=MOT_SPIN_MAX, MOT_THST_EXPO=MOT_THST_EXPO,
                          KV_rpm_per_V=KV_RPM_PER_V, ESC_surekli_A_motor=ESC_SUREKLI_A_MOTOR, ESC_tepe_A_motor=ESC_TEPE_A_MOTOR,
                          PM06_surekli_A=PM06_SUREKLI_A, PM06_tepe_A=PM06_TEPE_A, PM06_notu="veri sayfası doğrulanmadı",
                          kullanilabilir_pil=KULLANILABILIR_PIL, ust_hiz_orani=UST_HIZ_ORANI, dt_s=DT,
                          konfigler=[{k: v for k, v in kf.items()} for kf in KONFIGLER]),
        kalibrasyon=kalibrasyon,
        konfigler=konfig_sonuc,
        uyarilar=uyarilar,
    )

    # Grafikler
    grafikler = [
        dict(anahtar="v_ust", y="v_üst (m/s)", baslik="Üst hız – eğim (irtifa tutamayan noktalar: yalnız dalışta)", dosya="grafik_v_ust_theta.png", ref=None),
        dict(anahtar="t60", y="0–60 km/h süresi (s)", baslik="0–60 km/h süresi – eğim (ulaşılmayan: boş)", dosya="grafik_t60_theta.png", ref=None),
        dict(anahtar="I_ust_A", y="v_üst'te toplam akım (A)", baslik="v_üst'te akım – eğim", dosya="grafik_akim_theta.png",
             ref=[(PM06_SUREKLI_A, "PM06 sürekli %g A (doğrulanmadı)" % PM06_SUREKLI_A), (MOTOR_N * ESC_SUREKLI_A_MOTOR, "4×ESC %g A" % ESC_SUREKLI_A_MOTOR)]),
    ]
    for g in grafikler:
        grafik(sonuc, g["anahtar"], g["y"], g["baslik"], g["dosya"], ref_cizgiler=g["ref"])
    sonuc["grafikler"] = [dict(baslik=g["baslik"], dosya=g["dosya"]) for g in grafikler]

    # JSON (kf ve satırlar yuvarlanmış)
    for k in sonuc["konfigler"]:
        k["ozet_md"] = ozet_tablo_md(k)
    json_cikti = dict(meta=sonuc["meta"], parametreler=sonuc["parametreler"], kalibrasyon=sonuc["kalibrasyon"],
                      konfigler=[dict(kimlik=k["kimlik"], ad=k["ad"], theta_max=k["theta_max"], ozet_md=k["ozet_md"],
                                      satirlar=[{kk: vv for kk, vv in r.items()} for r in k["satirlar"]]) for k in sonuc["konfigler"]],
                      grafikler=sonuc["grafikler"], uyarilar=uyarilar, sutunlar=SUTUNLAR)
    with open(os.path.join(BURASI, "tablolar.json"), "w", encoding="utf-8") as fh:
        json.dump(yuvarla(json_cikti), fh, ensure_ascii=False, indent=1)
    rapor = rapor_yaz(sonuc)
    with open(os.path.join(BURASI, "RAPOR.md"), "w", encoding="utf-8") as fh:
        fh.write(rapor)
    return sonuc


if __name__ == "__main__":
    s = main()
    for k in s["konfigler"]:
        kal = s["kalibrasyon"][k["kimlik"]]
        print("%s: k_T=%.4e k_P=%.4e s_TG=%.4f" % (k["ad"], kal["k_T_N_per_rpm2"], kal["k_P_W_per_rpm3"], kal["s_TG"]))
        for tm in k["theta_max"]:
            print("   V_acik %.2f -> V_yuk %.2f I %.0f A T/W %.2f theta_max %s ruzgar %s" % (
                tm["V_acik"], tm["V_yuk"], tm["I_A"], tm["TW_max"], f(tm["theta_max_deg"], 1), f(tm["ruzgar_ms"], 1)))
    print("kapali form vs RK4 maks sapma %%: %.6f" % s["meta"]["kapali_form_vs_rk4_maks_sapma_pct"])
    for k in s["konfigler"]:
        print("\n=== OZET %s (satir = 'dolu' senaryosu; T_max/W sutunu 3 senaryonun araligi) ===" % k["ad"])
        print(k["ozet_md"])
    print("yazildi: tablolar.json, RAPOR.md, 3 PNG ->", BURASI)
