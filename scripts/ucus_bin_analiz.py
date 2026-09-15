#!/usr/bin/env python3
"""ArduPilot DataFlash (.bin) — YENIDEN KULLANILABILIR ucus analiz araci (T276).

NEDEN: 12-15 Eylul 2026 ucus loglari (37 dosya, 27 benzersiz) mimarin gecici (scratch)
betigiyle tarandi (`results/ucus_analiz_20260915/tarama_ham.json`, D-482 denetim borcu).
Bu betik o mantigi URETIM koduna cevirir: her sayi LOGDAN hesaplanir, uydurma yoktur;
bilinmeyenler (kutle, gercek pervane, pil) `kullanici_beyani` alaninda ETIKETLENIR.

HER LOG ICIN:
  - sha256 (kopya tespiti: ayni sha → "KOPYA_OF", kopyalar analiz edilmez)
  - hucre sayisi (ilk BAT geriliminden; 3S ~11-12,6 V, 4S ~15-16,8 V)
  - PARM secimi (MOT_THST_HOVER, MOT_THST_EXPO, MOT_SPIN_MIN, BATT_*, INS_HNTCH_ENABLE,
    INS_GYRO/ACCEL_FILTER, ATC_RAT_*_P/I/D, ATC_ANG_*_P, MOT_PWM_MIN/MAX, FRAME_*) ve
    log icinde DEGISEN parametreler
  - arm pencereleri (EV ARMED/DISARMED; yoksa ARM; ARTI EV/ARM'la ortusmeyen RCOU > armli-rolanti
    esigi (~1050) araliklari — her boot'un ILK arm'inda ARMED olayi yazilmiyor, OLCULDU)
  - her pencere icin: motorlu sure (CTUN.ThO > 0,15), tur (ucus / kisa_sicrama < 5 s /
    arm_yalniz), irtifa maks (arm aninda CTUN.Alt tabani cikarilmis), ASKI orneklemi
    (irtifa > 1 m, |dikey hiz| < 0,5 m/s [CTUN.Alt turevi, 5 ornek ortalama], gaz 0,25-0,75)
    uzerinden ThO ort/p50, CTUN.ThH bas/son, BAT V bas/min/ort ve akim ort/p95/maks, mAh,
    aski gucu V*I, VIBE X/Y/Z ort/p95/maks + clip artisi, RCOU C1-C4 aski ortalamalari ve
    yayilimi, ATT roll/pitch RMS hatasi, EKF (XKF4/NKF4 innovasyon testleri, lane switch,
    ERR), MODE gecisleri (sebep kodu ile), failsafe olaylari
  - IMU ham (ACC/GYR hizli kayit yoksa IMU mesaji) varsa aski penceresinde Z ivme FFT'si:
    tepe frekans/genlik, ornekleme hizi ve Nyquist (25 Hz IMU kaydinda pervane temel
    frekansi COZULEMEZ — sayi verilmez, not dusulur)

KULLANIM:
  python scripts/ucus_bin_analiz.py [--cikti results/ucus_analiz_20260915/tum_loglar.json]
                                    [--beyan beyan.json] yol_veya_dizin ...
  Dizin verilirse icindeki *.bin dosyalari (ad sirali) alinir. Verilis SIRASI kopya
  esasini belirler: ayni sha'nin ilk goruleni esas, sonrakiler "KOPYA_OF".

SINIR: bu betik hukum VERMEZ; hukmu mumkun kilan sayilari cikarir. Yorum D-kaydina yazilir.
Bagimlilik: pymavlink (DFReader), numpy. SciPy/scikit YOK (anayasa m.4).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
SURUM = "1.0"

# ----------------------------------------------------------------------------- olcutler
MOTORLU_THO_ESIK = 0.15      # CTUN.ThO bu esigin ustunde ise "motorlu" ornek (D-482 yontemi)
KISA_SICRAMA_S = 5.0         # motorlu sure < 5 s -> kisa sicrama (askida-olcumlerle karistirilmaz)
ASKI_ALT_MIN_M = 1.0         # aski orneklemi: irtifa > 1 m
ASKI_VZ_MAKS_MS = 0.5        # aski orneklemi: |dikey hiz| < 0,5 m/s
ASKI_THO_MIN, ASKI_THO_MAKS = 0.25, 0.75
ASKI_EN_AZ_ORNEK = 10        # 10 Hz CTUN'da ≥ 1 s askı yoksa aski istatistigi yazilmaz
VZ_ORTALAMA_PENCERE = 5      # dikey hiz turevi 5 ornek (0,5 s @10 Hz) hareketli ortalama
ALT_TABAN_S = 1.0            # arm sonrasi ilk 1 s CTUN.Alt medyani = yer tabani
HUCRE_V_MIN, HUCRE_V_MAKS, HUCRE_V_HEDEF = 3.2, 4.3, 3.8   # V/hucre kabul araligi ve hedef
RCOU_ARM_ESIK = 1050         # armli-rolanti PWM = PWM_MIN + SPIN_ARM*aralik (=1100); disarm = 1000.
                             # Esik ikisinin ortasi; logdan PARM ile yeniden hesaplanir (rcou_arm_esigi)
FFT_EN_AZ_ORNEK = 64
EKF_INNOV_ESIK = 1.0         # XKF4 SV/SP/SH/SM > 1 -> innovasyon testi DUSTU
MOTOR_KV = 980               # SunnySky X2220 980KV (kullanici beyani) — yalniz kaba HESAP notu
DUSUK_AKIM_A = 8.0           # motorlu >= 5 s ama ort akim < 8 A: pervanesiz/yer testi suphesi (not)

# ----------------------------------------------------------------------------- eslemeler
# ArduCopter kip numaralari (Copter mode enum)
MODE_AD = {0: "STAB", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUID", 5: "LOIT", 6: "RTL",
           7: "CIRCLE", 9: "LAND", 11: "DRIFT", 13: "SPORT", 14: "FLIP", 15: "AUTOTUNE",
           16: "POSHOLD", 17: "BRAKE", 18: "THROW", 19: "AVOID_ADSB", 20: "GUID_NOGPS",
           21: "SMART_RTL", 22: "FLOWHOLD", 23: "FOLLOW", 24: "ZIGZAG", 25: "SYSTEMID",
           26: "AUTOROTATE", 27: "AUTO_RTL", 28: "TURTLE"}
# MODE.Rsn (AP ModeReason) — ilk tarama eslemesi + kalanlar
RSN_AD = {0: "BILINMIYOR", 1: "RC", 2: "GCS", 3: "RADYO_FS", 4: "PIL_FS", 5: "GCS_FS",
          6: "EKF_FS", 7: "GPS_GLITCH", 8: "GOREV_SONU", 9: "THR_LAND_ESCAPE", 10: "FENCE",
          11: "TERRAIN_FS", 12: "BRAKE_TIMEOUT", 13: "FLIP_TAMAM", 14: "AVOIDANCE",
          15: "AVOIDANCE_RECOVERY", 16: "THROW_TAMAM", 17: "TERMINATE", 18: "TOY_MODE",
          19: "CRASH", 25: "FAILSAFE", 26: "INITIALISED", 31: "STARTUP", 32: "SCRIPTING",
          33: "UNAVAILABLE", 41: "MISSION_CMD", 42: "FRSKY", 43: "FENCE_RETURN_PREV",
          48: "DEADRECKON_FS"}
# ERR.Subsys (LogErrorSubsystem)
ERR_SUBSYS_AD = {1: "MAIN", 2: "RADIO", 3: "COMPASS", 4: "OPTFLOW", 5: "FS_RADYO", 6: "FS_PIL",
                 7: "FS_GPS", 8: "FS_GCS", 9: "FS_FENCE", 10: "FLIGHT_MODE", 11: "GPS",
                 12: "CRASH_CHECK", 13: "FLIP", 14: "AUTOTUNE", 15: "PARACHUTE", 16: "EKFCHECK",
                 17: "FS_EKFINAV", 18: "BARO", 19: "CPU", 20: "FS_ADSB", 21: "TERRAIN",
                 22: "NAVIGATION", 23: "FS_TERRAIN", 24: "EKF_PRIMARY", 25: "THRUST_LOSS",
                 26: "FS_SENSORS", 27: "FS_LEAK", 28: "PITOT", 29: "FS_VIBE", 30: "INTERNAL",
                 31: "FS_DEADRECKON"}
ERR_FAILSAFE_SUBSYS = {5, 6, 7, 8, 9, 17, 20, 23, 26, 27, 29, 31}
RSN_FAILSAFE = {3, 4, 5, 6, 10, 19, 25, 48}
# EV.Id (LogEvent) — 62/63 EKF yaw/alt reset'tir (ucus_logu_devrilme.py'deki E-STOP etiketi yanlis)
EV_AD = {10: "ARMED", 11: "DISARMED", 15: "AUTO_ARMED", 17: "LAND_COMPLETE_MAYBE",
         18: "LAND_COMPLETE", 19: "LOST_GPS", 25: "SET_HOME", 28: "NOT_LANDED",
         54: "MOTORS_EMERGENCY_STOPPED", 55: "MOTORS_EMERGENCY_STOP_CLEARED",
         56: "MOTORS_INTERLOCK_DISABLED", 57: "MOTORS_INTERLOCK_ENABLED", 60: "EKF_ALT_RESET",
         61: "LAND_CANCELLED_BY_PILOT", 62: "EKF_YAW_RESET", 67: "GPS_PRIMARY_CHANGED",
         73: "LAND_REPO_ACTIVE"}
EV_ARMED, EV_DISARMED = 10, 11
# ARM.Method (AP_Arming::Method)
ARM_METHOD_AD = {0: "RUDDER", 1: "MAVLINK", 2: "AUXSWITCH", 3: "MOTORTEST", 4: "SCRIPTING",
                 5: "TERMINATION", 6: "CPUFAILSAFE", 7: "BATTERYFAILSAFE", 12: "CRASH",
                 13: "LANDED", 15: "FENCEBREACH", 16: "RADIOFAILSAFE", 17: "DISARMDELAY",
                 18: "GCSFAILSAFE", 24: "EKFFAILSAFE", 28: "AUTOLANDED", 32: "LANDING"}

PARM_LISTESI = ["MOT_THST_HOVER", "MOT_THST_EXPO", "MOT_SPIN_MIN", "MOT_SPIN_ARM", "MOT_SPIN_MAX",
                "MOT_PWM_MIN", "MOT_PWM_MAX", "MOT_HOVER_LEARN", "MOT_BAT_VOLT_MAX", "MOT_BAT_VOLT_MIN",
                "BATT_CAPACITY", "BATT_LOW_VOLT", "BATT_CRT_VOLT", "BATT_FS_LOW_ACT", "BATT_FS_CRT_ACT",
                "INS_HNTCH_ENABLE", "INS_HNTCH_FREQ", "INS_HNTCH_MODE", "INS_GYRO_FILTER",
                "INS_ACCEL_FILTER", "INS_LOG_BAT_MASK", "INS_LOG_BAT_OPT", "LOG_BITMASK",
                "FS_THR_ENABLE", "FS_GCS_ENABLE", "FS_EKF_ACTION", "FS_EKF_THRESH", "ARMING_CHECK",
                "PILOT_THR_BHV", "AHRS_EKF_TYPE"]
PARM_DESENLERI = [re.compile(r"^ATC_RAT_(RLL|PIT|YAW)_(P|I|D)$"), re.compile(r"^ATC_ANG_(RLL|PIT|YAW)_P$"),
                  re.compile(r"^FRAME_")]

# ----------------------------------------------------------------------------- beyan (kullanici)
# Pil ve pervane LOGDA YOK — kullanici beyani (15 Eylul 2026). Kaynak: gorev metni (T276 ORTAK).
KONFIG = {
    "A": {"pil": "3S", "pervane": "10x4.5 (1045)", "aciklama": "olagan konfigurasyon (12-13 Eylul)"},
    "B": {"pil": "4S", "pervane": "10x4.5 (1045)", "aciklama": "bir kez denendi, 'asiri titredi'"},
    "C": {"pil": "3S", "pervane": "9x5x3 (9 inc, 5 pitch, 3 pal)", "aciklama": "14 Eylul aksami"},
    "D": {"pil": "4S", "pervane": "9x5x3 (9 inc, 5 pitch, 3 pal)", "aciklama": "15 Eylul sabahi"},
}
BEYAN_ACIK = {  # log govde adi (kopya adlari dahil) → etiket; kullanicinin ACIKCA saydiklari
    "2026-09-13 09-26-58": "B", "62 13.09.2026 09-38-02": "B",
    "2026-09-12 18-48-07": "B", "2026-09-12 23-47-27": "B",
    "2026-09-14 19-43-06": "C", "68 14.09.2026 19-45-46": "C",
    "2026-09-14 21-10-34": "C", "69 14.09.2026 21-13-14": "C",
    "2026-09-15 11-14-33": "D", "2026-09-15 11-18-16": "D",
    "1980-01-06 08-07-20": "A", "1980-01-12 20-17-44": "A",
}
BEYAN_TARIH = {"2026-09-12": "A", "2026-09-13": "A", "2026-09-14": "C", "2026-09-15": "D"}
_AD_TARIH_ISO = re.compile(r"^(\d{4}-\d{2}-\d{2}) ")
_AD_TARIH_MP = re.compile(r"^(\d+) (\d{2})\.(\d{2})\.(\d{4}) ")


def beyan_etiketi(adlar, acik=None, tarih=None):
    """adlar: esas log govde adi + kopya govde adlari. Once acik liste, sonra (kopya adindan
    cikan) tarih kurali. Hicbiri yoksa etiket None — 'beyan yok' olarak yazilir."""
    acik = BEYAN_ACIK if acik is None else acik
    tarih = BEYAN_TARIH if tarih is None else tarih
    for ad in adlar:
        if ad in acik:
            return {"etiket": acik[ad], "kaynak": "kullanici_beyani", "dayanak": f"acik liste: {ad}",
                    **KONFIG.get(acik[ad], {})}
    for ad in adlar:
        m = _AD_TARIH_ISO.match(ad)
        gun = None
        if m:
            gun = m.group(1)
        else:
            m = _AD_TARIH_MP.match(ad)
            if m:
                gun = f"{m.group(4)}-{m.group(3)}-{m.group(2)}"
        if gun and gun in tarih:
            return {"etiket": tarih[gun], "kaynak": "kullanici_beyani",
                    "dayanak": f"tarih kurali {gun} (ad: {ad})", **KONFIG.get(tarih[gun], {})}
    return {"etiket": None, "kaynak": "kullanici_beyani", "dayanak": "kullanici listesinde yok",
            "pil": None, "pervane": None, "aciklama": "beyan yok"}


def mp_no(adlar):
    """Mission Planner numarali kopya adindan ('62 13.09.2026 ...') log numarasi."""
    for ad in adlar:
        m = _AD_TARIH_MP.match(ad)
        if m:
            return int(m.group(1))
    return None


# ----------------------------------------------------------------------------- yardimcilar
def sha256_dosya(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def kopya_grupla(yollar):
    """Verilis sirasiyla: ilk gorulen sha esas; sonrakiler kopya. → (esaslar, kopyalar, sha)"""
    sha = {y: sha256_dosya(y) for y in yollar}
    ilk, esaslar, kopyalar = {}, [], []
    for y in yollar:
        s = sha[y]
        if s in ilk:
            kopyalar.append((y, ilk[s]))
        else:
            ilk[s] = y
            esaslar.append(y)
    return esaslar, kopyalar, sha


def hucre_sayisi(v_ilk, v_min=HUCRE_V_MIN, v_maks=HUCRE_V_MAKS, hedef=HUCRE_V_HEDEF):
    """Ilk BAT geriliminden hucre sayisi. Aday n: v_min ≤ V/n ≤ v_maks; birden cok aday varsa
    hucre gerilimi hedefe (3,8 V) en yakin olan secilir. → (n | None, adaylar)"""
    if v_ilk is None or not math.isfinite(v_ilk) or v_ilk <= 0:
        return None, []
    adaylar = [n for n in range(1, 13) if v_min <= v_ilk / n <= v_maks]
    if not adaylar:
        return None, []
    return min(adaylar, key=lambda n: abs(v_ilk / n - hedef)), adaylar


RCOU_PENCERE_EN_AZ_S = 1.0   # RCOU'dan turetilen pencere en az bu kadar surmeli (parazit degil)
RCOU_BIRLESTIR_S = 2.0       # RCOU pencereleri arasindaki < 2 s bosluklar birlestirilir


def rcou_arm_esigi(parm):
    """Armli-rolanti (PWM_MIN + SPIN_ARM*aralik) ile disarm (PWM_MIN) arasinin ortasi; PARM yoksa 1050."""
    try:
        pmin, pmaks, spin = float(parm["MOT_PWM_MIN"]), float(parm["MOT_PWM_MAX"]), float(parm["MOT_SPIN_ARM"])
    except (KeyError, TypeError, ValueError):
        return float(RCOU_ARM_ESIK)
    if pmaks <= pmin or spin <= 0:
        return float(RCOU_ARM_ESIK)
    return pmin + 0.5 * spin * (pmaks - pmin)


def _rcou_pencereleri(rcou_t, rcou_maks, esik=RCOU_ARM_ESIK):
    """Herhangi bir motor PWM > esik olan araliklar (kisa bosluklar birlestirilmis)."""
    if rcou_t is None or len(rcou_t) == 0:
        return []
    m = np.asarray(rcou_maks, float) > esik
    p, basla = [], None
    for t, a in zip(np.asarray(rcou_t, float), m):
        if a and basla is None:
            basla = float(t)
        elif not a and basla is not None:
            p.append((basla, float(t))); basla = None
    if basla is not None:
        p.append((basla, float(rcou_t[-1])))
    birlesik = []
    for a, b in p:
        if birlesik and a - birlesik[-1][1] < RCOU_BIRLESTIR_S:
            birlesik[-1] = (birlesik[-1][0], b)
        else:
            birlesik.append((a, b))
    return [(a, b) for a, b in birlesik if b - a >= RCOU_PENCERE_EN_AZ_S]


def arm_pencereleri(ev, arm, rcou_t, rcou_maks, t_ilk, t_son, esik=RCOU_ARM_ESIK):
    """ARM→DISARM pencereleri → [(t0, t1, kaynak)], zaman sirali.
    1) EV ARMED(10)/DISARMED(11); EV yoksa ARM.ArmState 1/0.
    2) TAMAMLAYICI: RCOU > esik (armli rolanti ~1100 sayilir, disarm 1000 sayilmaz)
       araliklarindan, 1)'deki hicbir pencereyle ORTUSMEYENLER "RCOU" kaynagiyla eklenir.
       Neden (OLCULDU, 8 logda): her boot'un ILK arm'inda EV ARMED(10) ve ARM(1) kaydi YOK;
       yalniz EV57 (interlock), AUTO_ARMED(15), NOT_LANDED(28) ve RCOU 1000→1100 var.
       15 Eyl 11-14-33: 43,5 s motorlu ucus (35 A, LAND, LAND_COMPLETE) — yalniz EV'ye
       bakan ilk tarama bu ucusu ve 7 logdaki ilk ucusu KACIRDI.
    ev: [(t, id)], arm: [(t, state)], rcou_t/rcou_maks: dizi."""
    p, acik = [], None
    # log ARMLI baslamis mi? Kanit: ilk RCOU orneginde motor PWM > esik. (Yalniz DISARMED
    # olayina bakmak yaniltir: LAND'de yerde iken de DISARMED/ARM(LANDED) yazilabiliyor.)
    bas_armli = rcou_maks is not None and len(rcou_maks) > 0 and float(rcou_maks[0]) > esik
    for t, i in ev:
        if i == EV_ARMED and acik is None:
            acik = t
        elif i == EV_DISARMED:
            if acik is not None:
                p.append((acik, t, "EV")); acik = None
            elif not p and bas_armli:
                p.append((t_ilk, t, "EV"))
    if acik is not None:
        p.append((acik, t_son, "EV"))
    if not p:
        acik = None
        for t, s in arm:
            if s == 1 and acik is None:
                acik = t
            elif s == 0 and acik is not None:
                p.append((acik, t, "ARM")); acik = None
        if acik is not None:
            p.append((acik, t_son, "ARM"))
    for a, b in _rcou_pencereleri(rcou_t, rcou_maks, esik):
        if not any(a < t1 + 0.5 and b > t0 - 0.5 for t0, t1, _ in p):
            p.append((a, b, "RCOU"))
    p.sort(key=lambda x: x[0])
    return p


def _dt_dizisi(t):
    if len(t) < 2:
        return np.full(len(t), 0.1)
    d = np.diff(t)
    d = np.append(d, np.median(d))
    return np.clip(d, 0.0, 1.0)


def motorlu_sure(t, tho, esik=MOTORLU_THO_ESIK):
    """CTUN.ThO > esik orneklerinin toplam suresi. → (sure_s, t_ilk_motorlu, t_son_motorlu)"""
    t = np.asarray(t, float); tho = np.asarray(tho, float)
    if len(t) == 0:
        return 0.0, None, None
    m = tho > esik
    if not m.any():
        return 0.0, None, None
    return float(_dt_dizisi(t)[m].sum()), float(t[m][0]), float(t[m][-1])


def ucus_turu(motorlu_s):
    if motorlu_s <= 0.0:
        return "arm_yalniz"
    return "kisa_sicrama" if motorlu_s < KISA_SICRAMA_S else "ucus"


def dikey_hiz(t, alt, pencere=VZ_ORTALAMA_PENCERE):
    """CTUN.Alt turevi (m/s), `pencere` ornek hareketli ortalama."""
    t = np.asarray(t, float); alt = np.asarray(alt, float)
    if len(t) < 2:
        return np.zeros(len(t))
    d = np.diff(t)
    if np.any(d <= 0):
        vz = np.gradient(alt) / max(float(np.median(d[d > 0])) if np.any(d > 0) else 0.1, 1e-3)
    else:
        vz = np.gradient(alt, t)
    if pencere > 1 and len(vz) >= pencere:
        vz = np.convolve(vz, np.ones(pencere) / pencere, mode="same")
    return vz


def aski_maskesi(t, alt_rel, tho, alt_min=ASKI_ALT_MIN_M, vz_maks=ASKI_VZ_MAKS_MS,
                 tho_min=ASKI_THO_MIN, tho_maks=ASKI_THO_MAKS):
    alt_rel = np.asarray(alt_rel, float); tho = np.asarray(tho, float)
    vz = dikey_hiz(t, alt_rel)
    return (alt_rel > alt_min) & (np.abs(vz) < vz_maks) & (tho >= tho_min) & (tho <= tho_maks)


def en_uzun_kosu(maske):
    """Maskedeki en uzun ardisik True dilimi → (i0, i1_dahil) | None"""
    en, bas, i0 = None, None, None
    for i, v in enumerate(list(maske) + [False]):
        if v and bas is None:
            bas = i
        elif not v and bas is not None:
            if en is None or i - bas > en:
                en, i0 = i - bas, bas
            bas = None
    return None if en is None else (i0, i0 + en - 1)


def imu_fft(t, z, en_az=FFT_EN_AZ_ORNEK, tepe_n=5):
    """Z ivme FFT (numpy.fft, Hann pencere, genlik = 2|X|/sum(w)). → dict | None"""
    t = np.asarray(t, float); z = np.asarray(z, float)
    n = len(z)
    if n < en_az:
        return None
    d = np.diff(t)
    dt = float(np.median(d[d > 0])) if np.any(d > 0) else None
    if not dt:
        return None
    fs = 1.0 / dt
    w = np.hanning(n)
    x = (z - z.mean()) * w
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, dt)
    genlik = 2.0 * np.abs(X) / w.sum()
    genlik[0] = 0.0
    # yerel maksimumlar (0,5 Hz ustu), en buyuk tepe_n
    adaylar = [i for i in range(1, len(genlik) - 1)
               if f[i] >= 0.5 and genlik[i] >= genlik[i - 1] and genlik[i] >= genlik[i + 1]]
    adaylar.sort(key=lambda i: -genlik[i])
    tepeler = [{"f_hz": round(float(f[i]), 2), "genlik_ms2": round(float(genlik[i]), 3)}
               for i in adaylar[:tepe_n]]
    return {"n": int(n), "fs_hz": round(fs, 2), "nyquist_hz": round(fs / 2, 2),
            "cozunurluk_hz": round(fs / n, 3), "sure_s": round(n * dt, 2),
            "rms_ms2": round(float(np.sqrt(np.mean((z - z.mean()) ** 2))), 3), "tepeler": tepeler}


def _f32(v):
    """PARM degerleri float32'dir; 6 anlamli basamaga yuvarla (0.47259318828582764 -> 0.472593)."""
    return float(f"{float(v):.6g}")


def _p(a, q):
    return float(np.percentile(a, q)) if len(a) else None


def _r(x, n=3):
    if x is None:
        return None
    x = float(x)
    return round(x, n) if math.isfinite(x) else None


def _temiz(o):
    """JSON icin: numpy → python, NaN → None."""
    if isinstance(o, dict):
        return {str(k): _temiz(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_temiz(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o) if math.isfinite(float(o)) else None
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


# ----------------------------------------------------------------------------- okuma
def oku(yol: Path):
    """Tek gecis DFReader okumasi → ham dict (numpy dizileri + olay listeleri)."""
    from pymavlink import DFReader
    log = DFReader.DFReader_binary(str(yol))
    parm, parm_ilk, parm_degisim = {}, {}, []
    ev, arm, mode, err, msg = [], [], [], [], []
    ctun, bat, vibe, rcou, att, ekf = [], [], [], [], [], []
    imu, acc = defaultdict(list), defaultdict(list)
    ekf_tip, ver, sayac = None, None, defaultdict(int)
    t_ilk = t_son = None
    while True:
        m = log.recv_msg()
        if m is None:
            break
        tip = m.get_type()
        sayac[tip] += 1
        tu = getattr(m, "TimeUS", None)
        if tu is not None:
            t = tu / 1e6
            if t_ilk is None or t < t_ilk:
                t_ilk = t
            if t_son is None or t > t_son:
                t_son = t
        else:
            t = None
        if tip == "PARM":
            ad, v = m.Name, _f32(m.Value)
            if ad in parm and parm[ad] != v:
                if not ad.startswith("STAT_"):   # STAT_RUNTIME/FLTTIME sayaclari degisim degil
                    parm_degisim.append({"t": round(t, 1), "ad": ad, "eski": parm[ad], "yeni": v})
            elif ad not in parm:
                parm_ilk[ad] = v                 # ilk deger (STAT_* sayaclari icin: logun BASINDAKI)
            parm[ad] = v
        elif tip == "EV":
            ev.append((t, int(m.Id)))
        elif tip == "ARM":
            arm.append((t, int(m.ArmState), int(getattr(m, "Method", -1))))
        elif tip == "MODE":
            md = getattr(m, "Mode", None)
            mn = int(getattr(m, "ModeNum", md if isinstance(md, int) else -1))
            mode.append((t, mn, int(getattr(m, "Rsn", 0)), md if isinstance(md, str) else None))
        elif tip == "ERR":
            err.append((t, int(m.Subsys), int(m.ECode)))
        elif tip == "MSG":
            msg.append((t, str(m.Message)))
        elif tip == "CTUN":
            ctun.append((t, float(getattr(m, "ThO", 0.0)), float(getattr(m, "ThH", 0.0)),
                         float(getattr(m, "Alt", 0.0)), float(getattr(m, "ThI", 0.0)),
                         float(getattr(m, "CRt", 0.0))))
        elif tip == "BAT":
            if int(getattr(m, "Inst", 0)) == 0:
                bat.append((t, float(m.Volt), float(m.Curr), float(getattr(m, "CurrTot", 0.0))))
        elif tip == "VIBE":
            vibe.append((t, int(getattr(m, "IMU", 0)), float(m.VibeX), float(m.VibeY), float(m.VibeZ),
                         int(getattr(m, "Clip", 0))))
        elif tip == "RCOU":
            rcou.append((t, int(m.C1), int(m.C2), int(m.C3), int(m.C4)))
        elif tip == "ATT":
            att.append((t, float(m.Roll), float(m.Pitch), float(getattr(m, "DesRoll", 0.0)),
                        float(getattr(m, "DesPitch", 0.0))))
        elif tip in ("XKF4", "NKF4"):
            if ekf_tip is None:
                ekf_tip = tip
            if tip == ekf_tip:
                ekf.append((t, int(getattr(m, "C", 0)), float(m.SV), float(m.SP), float(m.SH),
                            float(m.SM), float(getattr(m, "errRP", 0.0))))
        elif tip == "IMU":
            imu[int(getattr(m, "I", 0))].append((t, float(m.AccX), float(m.AccY), float(m.AccZ)))
        elif tip == "ACC":
            acc[int(getattr(m, "I", 0))].append((t, float(m.AccX), float(m.AccY), float(m.AccZ)))
        elif tip == "VER":
            ver = str(getattr(m, "FWS", ""))

    return {
        "parm": parm, "parm_ilk": parm_ilk, "parm_degisim": parm_degisim, "ev": ev, "arm": arm, "mode": mode, "err": err,
        "msg": msg, "ver": ver, "sayac": dict(sayac), "t_ilk": t_ilk, "t_son": t_son,
        "ctun": np.array(ctun, float).reshape(-1, 6), "bat": np.array(bat, float).reshape(-1, 4),
        "vibe": np.array(vibe, float).reshape(-1, 6), "rcou": np.array(rcou, float).reshape(-1, 5),
        "att": np.array(att, float).reshape(-1, 5), "ekf": np.array(ekf, float).reshape(-1, 7),
        "ekf_tip": ekf_tip,
        "imu": {k: np.array(v, float).reshape(-1, 4) for k, v in imu.items()},
        "acc": {k: np.array(v, float).reshape(-1, 4) for k, v in acc.items()},
    }


def parm_sec(parm):
    secim = {k: parm[k] for k in PARM_LISTESI if k in parm}
    for k in sorted(parm):
        if any(d.match(k) for d in PARM_DESENLERI):
            secim[k] = parm[k]
    return secim


def _kip(mn, md_str=None):
    return md_str if md_str else MODE_AD.get(mn, f"KIP_{mn}")


def _rsn(r):
    return RSN_AD.get(r, f"RSN_{r}")


def _err_ad(subsys, ecode):
    ad = ERR_SUBSYS_AD.get(subsys, f"SUBSYS_{subsys}")
    if subsys == 10:
        return ad, f"kip {_kip(ecode)} reddedildi"
    if subsys == 12:
        return ad, {1: "CRASH", 2: "KONTROL_KAYBI"}.get(ecode, str(ecode))
    if subsys == 16:
        return ad, {2: "BAD_VARIANCE", 0: "temizlendi"}.get(ecode, str(ecode))
    if subsys == 11:
        return ad, {2: "GLITCH", 0: "temizlendi"}.get(ecode, str(ecode))
    if subsys == 24:
        return ad, f"birincil cekirdek -> {ecode}"
    return ad, {0: "temizlendi", 1: "TETIKLENDI"}.get(ecode, str(ecode))


# ----------------------------------------------------------------------------- pencere analizi
def pencere_analiz(ham, t0, t1, parm, k):
    """Bir arm penceresinin (t0..t1) tum olcumleri. Her sayi logdan; yoksa None + neden."""
    u = {"no": k, "arm_t": _r(t0, 1), "disarm_t": _r(t1, 1), "pencere_s": _r(t1 - t0, 1), "notlar": []}
    N = u["notlar"].append

    # arm/disarm yontemi
    for t, s, meth in ham["arm"]:
        if abs(t - t0) < 0.2 and s == 1:
            u["arm_yontemi"] = ARM_METHOD_AD.get(meth, f"METHOD_{meth}")
        if abs(t - t1) < 0.2 and s == 0:
            u["disarm_yontemi"] = ARM_METHOD_AD.get(meth, f"METHOD_{meth}")

    ctun = ham["ctun"]
    cm = (ctun[:, 0] >= t0) & (ctun[:, 0] <= t1) if len(ctun) else np.zeros(0, bool)
    if not cm.any():
        u.update({"motorlu_s": 0.0, "tur": "arm_yalniz", "ctun_n": 0})
        N("pencerede CTUN yok — motorlu sure/irtifa/aski OLCULEMEDI")
        c_t = np.zeros(0)
    else:
        c_t, tho, thh, alt = ctun[cm, 0], ctun[cm, 1], ctun[cm, 2], ctun[cm, 3]
        u["ctun_n"] = int(cm.sum())
        u["ctun_hz"] = _r(1.0 / float(np.median(np.diff(c_t))), 1) if len(c_t) > 2 else None
        ms, tm0, tm1 = motorlu_sure(c_t, tho)
        u["motorlu_s"] = _r(ms, 1)
        u["motorlu_t"] = [_r(tm0, 1), _r(tm1, 1)]
        u["tur"] = ucus_turu(ms)
        taban_m = c_t <= t0 + ALT_TABAN_S
        taban = float(np.median(alt[taban_m])) if taban_m.any() else float(alt[0])
        alt_rel = alt - taban
        u["alt_taban_m"] = _r(taban, 2)
        u["alt_maks_m"] = _r(alt_rel.max(), 2)
        u["alt_ham_maks_m"] = _r(alt.max(), 2)
        u["ThH_bas"] = _r(thh[0]); u["ThH_son"] = _r(thh[-1])
        mot = tho > MOTORLU_THO_ESIK
        u["ThO_motorlu_ort"] = _r(tho[mot].mean()) if mot.any() else None
        u["ThO_maks"] = _r(tho.max())
        am = aski_maskesi(c_t, alt_rel, tho)
        u["aski_n"] = int(am.sum())
        dt_med = float(np.median(np.diff(c_t))) if len(c_t) > 1 else 0.1
        u["aski_s"] = _r(am.sum() * dt_med, 1)
        if am.sum() >= ASKI_EN_AZ_ORNEK:
            u["aski"] = {"ThO_ort": _r(tho[am].mean()), "ThO_p50": _r(np.median(tho[am])),
                         "ThO_p05": _r(_p(tho[am], 5)), "ThO_p95": _r(_p(tho[am], 95)),
                         "alt_ort_m": _r(alt_rel[am].mean(), 2)}
            kosu = en_uzun_kosu(am)
            u["aski"]["en_uzun_dilim_t"] = [_r(c_t[kosu[0]], 1), _r(c_t[kosu[1]], 1)]
            u["aski"]["en_uzun_dilim_s"] = _r(c_t[kosu[1]] - c_t[kosu[0]], 1)
        else:
            u["aski"] = None
            N(f"aski orneklemi yetersiz ({int(am.sum())} < {ASKI_EN_AZ_ORNEK} ornek) — aski istatistigi yok")

    aski_t = c_t[aski_maskesi(c_t, ctun[cm, 3] - (u.get("alt_taban_m") or 0.0), ctun[cm, 1])] \
        if len(c_t) and u.get("aski") else np.zeros(0)
    tm0, tm1 = (u.get("motorlu_t") or [None, None])
    span = (tm0, tm1) if tm0 is not None else (t0, t1)

    # --- BAT
    bat = ham["bat"]
    bm = (bat[:, 0] >= t0) & (bat[:, 0] <= t1) if len(bat) else np.zeros(0, bool)
    if bm.any():
        b_t, v, i, ctot = bat[bm, 0], bat[bm, 1], bat[bm, 2], bat[bm, 3]
        sm = (b_t >= span[0]) & (b_t <= span[1])
        i_s = i[sm] if sm.any() else i
        u["bat"] = {"V_bas": _r(v[0], 2), "V_min": _r(v.min(), 2), "V_ort": _r(v.mean(), 2),
                    "V_son": _r(v[-1], 2), "V_min_t": _r(b_t[int(np.argmin(v))], 1),
                    "I_ort": _r(i_s.mean(), 1), "I_p95": _r(_p(i_s, 95), 1), "I_maks": _r(i_s.max(), 1),
                    "mAh": _r(ctot[-1] - ctot[0], 0),
                    "I_kapsam": "motorlu" if (tm0 is not None and sm.any()) else "pencere"}
        if len(aski_t):
            va, ia = np.interp(aski_t, b_t, v), np.interp(aski_t, b_t, i)
            u["bat"]["aski"] = {"V_ort": _r(va.mean(), 2), "I_ort": _r(ia.mean(), 1),
                                "I_p95": _r(_p(ia, 95), 1), "P_W": _r((va * ia).mean(), 1)}
    else:
        u["bat"] = None; N("pencerede BAT yok")

    # --- VIBE
    vb = ham["vibe"]
    vm = (vb[:, 0] >= span[0]) & (vb[:, 0] <= span[1]) if len(vb) else np.zeros(0, bool)
    if vm.any():
        d = {}
        for ad, kol in (("X", 2), ("Y", 3), ("Z", 4)):
            s = vb[vm, kol]
            d[ad] = {"ort": _r(s.mean(), 1), "p95": _r(_p(s, 95), 1), "maks": _r(s.max(), 1)}
        clip = {}
        wm = (vb[:, 0] >= t0) & (vb[:, 0] <= t1)
        for inst in sorted(set(vb[wm, 1].astype(int))):
            s = vb[wm & (vb[:, 1] == inst), 5]
            clip[str(inst)] = int(s[-1] - s[0]) if len(s) else 0
        d["clip_artisi"] = clip
        d["clip_toplam"] = int(sum(clip.values()))
        d["kapsam"] = "motorlu" if tm0 is not None else "pencere"
        # arm penceresinin TAMAMI (inis carpmasi gaz kesildikten sonra gelebilir; clip ile birlikte okunur)
        d["pencere_maks"] = {ad: _r(vb[wm, kol].max(), 1) for ad, kol in (("X", 2), ("Y", 3), ("Z", 4))}
        if len(aski_t):
            am_v = np.zeros(len(vb), bool)
            for j in range(len(aski_t)):
                lo, hi = np.searchsorted(vb[:, 0], aski_t[j] - 0.06), np.searchsorted(vb[:, 0], aski_t[j] + 0.06)
                am_v[lo:hi] = True
            if am_v.any():
                d["aski"] = {ad: _r(vb[am_v, kol].mean(), 1) for ad, kol in (("X", 2), ("Y", 3), ("Z", 4))}
        u["vibe"] = d
    else:
        u["vibe"] = None; N("pencerede VIBE yok")

    # --- RCOU (motor dengesi)
    rc = ham["rcou"]
    if len(rc):
        if len(aski_t):
            idx = np.clip(np.searchsorted(rc[:, 0], aski_t), 0, len(rc) - 1)
            idx = idx[np.abs(rc[idx, 0] - aski_t) <= 0.2]
            kapsam = "aski"
        else:
            sm = (rc[:, 0] >= span[0]) & (rc[:, 0] <= span[1])
            idx = np.where(sm)[0]; kapsam = "motorlu" if tm0 is not None else "pencere"
        if len(idx):
            ort = [float(rc[idx, j].mean()) for j in (1, 2, 3, 4)]
            std = [float(rc[idx, j].std()) for j in (1, 2, 3, 4)]
            pmin, pmaks = parm.get("MOT_PWM_MIN", 1000.0), parm.get("MOT_PWM_MAX", 2000.0)
            aralik = max(pmaks - pmin, 1.0)
            u["rcou"] = {"kapsam": kapsam, "n": int(len(idx)),
                         "C1_C4_ort": [round(x) for x in ort], "C1_C4_std": [round(x, 1) for x in std],
                         "yayilim_pwm": round(max(ort) - min(ort)),
                         "yayilim_pct": _r((max(ort) - min(ort)) / aralik * 100, 1),
                         "en_yuksek": "C%d" % (int(np.argmax(ort)) + 1), "en_dusuk": "C%d" % (int(np.argmin(ort)) + 1),
                         "ort_pwm_orani": _r((np.mean(ort) - pmin) / aralik)}
        else:
            u["rcou"] = None
    else:
        u["rcou"] = None; N("RCOU yok")

    # --- ATT
    at = ham["att"]
    if len(at):
        sm = (at[:, 0] >= span[0]) & (at[:, 0] <= span[1])
        if sm.any():
            r, p_, dr, dp = at[sm, 1], at[sm, 2], at[sm, 3], at[sm, 4]
            u["att"] = {"kapsam": "motorlu" if tm0 is not None else "pencere", "n": int(sm.sum()),
                        "roll_rms_hata_deg": _r(np.sqrt(np.mean((r - dr) ** 2)), 2),
                        "pitch_rms_hata_deg": _r(np.sqrt(np.mean((p_ - dp) ** 2)), 2),
                        "roll_maks_abs_deg": _r(np.abs(r).max(), 1), "pitch_maks_abs_deg": _r(np.abs(p_).max(), 1),
                        "roll_ort_deg": _r(r.mean(), 2), "pitch_ort_deg": _r(p_.mean(), 2)}
            if len(aski_t):
                idx = np.clip(np.searchsorted(at[:, 0], aski_t), 0, len(at) - 1)
                ra, pa = at[idx, 1] - at[idx, 3], at[idx, 2] - at[idx, 4]
                u["att"]["aski"] = {"roll_rms_hata_deg": _r(np.sqrt(np.mean(ra ** 2)), 2),
                                    "pitch_rms_hata_deg": _r(np.sqrt(np.mean(pa ** 2)), 2)}
        else:
            u["att"] = None
    else:
        u["att"] = None; N("ATT yok")

    # --- EKF
    ek = ham["ekf"]
    em = (ek[:, 0] >= t0) & (ek[:, 0] <= t1) if len(ek) else np.zeros(0, bool)
    e = {"tip": ham["ekf_tip"], "cekirdek": {}, "lane_switch": [], "err": []}
    if em.any():
        for c in sorted(set(ek[em, 1].astype(int))):
            s = ek[em & (ek[:, 1] == c)]
            e["cekirdek"][str(c)] = {"SV_maks": _r(s[:, 2].max(), 2), "SP_maks": _r(s[:, 3].max(), 2),
                                     "SH_maks": _r(s[:, 4].max(), 2), "SM_maks": _r(s[:, 5].max(), 2),
                                     "errRP_maks": _r(s[:, 6].max(), 3),
                                     "innov_dusen_n": int(((s[:, 2] > EKF_INNOV_ESIK) | (s[:, 3] > EKF_INNOV_ESIK) |
                                                           (s[:, 4] > EKF_INNOV_ESIK) | (s[:, 5] > EKF_INNOV_ESIK)).sum()),
                                     "n": int(len(s))}
    else:
        N("pencerede XKF4/NKF4 yok — EKF innovasyon testi OLCULEMEDI")
    for t, s in ham["msg"]:
        if t0 - 0.5 <= t <= t1 + 0.5 and re.search(r"lane switch|primary changed|EKF primary", s, re.I):
            e["lane_switch"].append({"t": _r(t, 1), "msg": s})
    for t, sub, code in ham["err"]:
        if t0 - 0.5 <= t <= t1 + 0.5 and sub in (16, 17, 24):
            ad, ac = _err_ad(sub, code)
            e["err"].append({"t": _r(t, 1), "subsys": ad, "kod": code, "aciklama": ac})
            if sub == 24:
                e["lane_switch"].append({"t": _r(t, 1), "msg": f"ERR EKF_PRIMARY -> {code}"})
    for t, i in ham["ev"]:
        if t0 <= t <= t1 and i in (60, 62):
            e["err"].append({"t": _r(t, 1), "subsys": "EV", "kod": i, "aciklama": EV_AD[i]})
    u["ekf"] = e

    # --- MODE / ERR / MSG / failsafe (pencere +-0,5 s)
    kip_arm = None
    for t, mn, rsn, md in ham["mode"]:
        if t <= t0 + 0.2:
            kip_arm = _kip(mn, md)
    u["kip_arm"] = kip_arm
    gec, fs, olay = [], [], []
    for t, mn, rsn, md in ham["mode"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            gec.append({"t": _r(t, 1), "kip": _kip(mn, md), "rsn": rsn, "rsn_ad": _rsn(rsn)})
            olay.append((t, "MOD", f"{_kip(mn, md)}<{_rsn(rsn)}"))
            if rsn in RSN_FAILSAFE:
                fs.append({"t": _r(t, 1), "tip": "MODE", "aciklama": f"{_kip(mn, md)} <- {_rsn(rsn)}"})
    for t, sub, code in ham["err"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            ad, ac = _err_ad(sub, code)
            olay.append((t, "ERR", f"{ad}={code} ({ac})"))
            if sub in ERR_FAILSAFE_SUBSYS:
                fs.append({"t": _r(t, 1), "tip": "ERR", "aciklama": f"{ad} {ac}"})
    for t, s in ham["msg"]:
        if t0 - 0.5 <= t <= t1 + 0.5:
            olay.append((t, "MSG", s))
            # "PreArm:/Arm:" satirlari arm KONTROLUdur, failsafe olayi degil (olaylar'da kalir)
            if re.search(r"failsafe|crash|thrust loss|potential thrust", s, re.I) \
                    and not re.match(r"^(PreArm|Arm):", s):
                fs.append({"t": _r(t, 1), "tip": "MSG", "aciklama": s})
    for t, i in ham["ev"]:
        if t0 <= t <= t1 and i not in (EV_ARMED, EV_DISARMED, 56, 57):
            olay.append((t, "EV", EV_AD.get(i, f"EV_{i}")))
    olay.sort(key=lambda x: x[0])
    u["kip_gecisleri"] = gec
    inis = [g for g in gec if g["kip"] in ("LAND", "RTL", "SMART_RTL") and g["t"] >= t0]
    u["inis"] = inis[-1] if inis else {"kip": None, "rsn_ad": "kip degismedi (disarm)"}
    fs.sort(key=lambda x: (x["t"] if x["t"] is not None else 0.0))
    u["failsafe"] = fs
    u["olaylar"] = [[_r(t, 1), tip, s] for t, tip, s in olay]

    # --- IMU FFT (aski en uzun dilimi; ACC hizli kayit varsa o, yoksa IMU)
    kaynak = "ACC" if ham["acc"] else ("IMU" if ham["imu"] else None)
    u["imu_fft"] = None
    if kaynak and u.get("aski"):
        inst = sorted(ham[kaynak.lower()])[0]
        s = ham[kaynak.lower()][inst]
        ta, tb = u["aski"]["en_uzun_dilim_t"]
        sm = (s[:, 0] >= ta) & (s[:, 0] <= tb)
        f = imu_fft(s[sm, 0], s[sm, 3]) if sm.any() else None
        if f:
            f.update({"kaynak": f"{kaynak} inst {inst}", "eksen": "AccZ", "dilim_t": [ta, tb]})
            # pervane temel frekansi: ESC/RPM mesaji YOK → yalniz kaba HESAP notu
            if u.get("rcou") and u["rcou"].get("ort_pwm_orani") is not None and u.get("bat") \
                    and u["bat"].get("aski"):
                f_perv = MOTOR_KV * u["bat"]["aski"]["V_ort"] * u["rcou"]["ort_pwm_orani"] / 60.0
                f["pervane_f_kaba_hesap_hz"] = _r(f_perv, 0)
                f["pervane_f_notu"] = ("ESC/RPM mesaji yok; KV x V_aski x PWM_orani / 60 KABA HESAP "
                                       "(pervane yuku ve ESC egrisi yok) — olcum degil")
            if f["nyquist_hz"] < 50:
                f["not"] = (f"ornekleme {f['fs_hz']} Hz -> Nyquist {f['nyquist_hz']} Hz: pervane temel "
                            "frekansi (>50 Hz) COZULEMEZ; tepeler govde/kontrol bandi. Hizli IMU icin "
                            "LOG_BITMASK IMU_FAST ya da INS_LOG_BAT_MASK gerekir")
            u["imu_fft"] = f
        elif sm.any():
            N(f"IMU FFT: dilimde {int(sm.sum())} < {FFT_EN_AZ_ORNEK} ornek")
    elif kaynak and not u.get("aski"):
        N("IMU FFT: aski dilimi yok")
    elif not kaynak:
        N("IMU/ACC mesaji yok — FFT yok")
    return u


# ----------------------------------------------------------------------------- log analizi
def _gorel(yol: Path) -> str:
    try:
        return yol.resolve().relative_to(KOK).as_posix()
    except ValueError:
        return yol.resolve().as_posix()


def log_analiz(yol: Path, kopya_adlari=(), sha=None, beyan_acik=None):
    ham = oku(yol)
    parm = ham["parm"]
    bat = ham["bat"]
    v_ilk = None
    if len(bat):
        gecerli = bat[bat[:, 1] > 1.0]
        v_ilk = float(gecerli[0, 1]) if len(gecerli) else None
    n, adaylar = hucre_sayisi(v_ilk)
    adlar = [yol.stem] + [Path(k).stem for k in kopya_adlari]
    beyan = beyan_etiketi(adlar, acik=beyan_acik)
    beyan["hucre_uyum"] = (None if (n is None or not beyan.get("pil"))
                           else (beyan["pil"] == f"{n}S"))
    rc = ham["rcou"]
    rc_esik = rcou_arm_esigi(parm)
    pw3 = arm_pencereleri(ham["ev"], [(t, s) for t, s, _ in ham["arm"]],
                          rc[:, 0] if len(rc) else None, rc[:, 1:5].max(axis=1) if len(rc) else None,
                          ham["t_ilk"] or 0.0, ham["t_son"] or 0.0, esik=rc_esik)
    pw = [(t0, t1) for t0, t1, _ in pw3]
    kaynak = "+".join(sorted(set(k for _, _, k in pw3))) or "YOK"
    ucuslar = []
    for k, (t0, t1, kay) in enumerate(pw3, 1):
        u = pencere_analiz(ham, t0, t1, parm, k)
        u["pencere_kaynak"] = kay
        if kay == "RCOU":
            ev57 = [t for t, i in ham["ev"] if i == 57 and t0 - 2.0 <= t <= t0 + 1.0]
            u["notlar"].append("ARMED olayi/ARM(1) kaydi yok — pencere RCOU > %.0f'den turetildi%s" % (
                rc_esik, ("; EV57 MOTORS_INTERLOCK_ENABLED t=%.1f arm kaniti" % ev57[0]) if ev57 else ""))
        b = u.get("bat") or {}
        if (u.get("motorlu_s") or 0) >= KISA_SICRAMA_S and b.get("I_ort") is not None and b["I_ort"] < DUSUK_AKIM_A:
            u["notlar"].append("motorlu %.1f s ama akim ort %.1f A < %d A: pervanesiz/yerde motor testi olabilir — "
                               "aski/itki olcumu olarak KULLANILMAZ" % (u["motorlu_s"], b["I_ort"], DUSUK_AKIM_A))
            u["dusuk_akim"] = True
        ucuslar.append(u)
    imu_var = bool(ham["imu"]) or bool(ham["acc"])
    imu_bilgi = {"var": imu_var, "acc_gyr_hizli": bool(ham["acc"]), "imu_mesaji": bool(ham["imu"]),
                 "instance_n": len(ham["acc"] or ham["imu"])}
    if imu_var:
        s = (ham["acc"] or ham["imu"])[sorted(ham["acc"] or ham["imu"])[0]]
        d = np.diff(s[:, 0])
        imu_bilgi["fs_hz"] = _r(1.0 / float(np.median(d[d > 0])), 1) if np.any(d > 0) else None
    # pencere disi olaylar (ERR + failsafe MSG)
    disi = []
    for t, sub, code in ham["err"]:
        if not any(t0 - 0.5 <= t <= t1 + 0.5 for t0, t1 in pw):
            ad, ac = _err_ad(sub, code); disi.append([_r(t, 1), "ERR", f"{ad}={code} ({ac})"])
    for t, s in ham["msg"]:
        if re.search(r"failsafe|crash|PreArm|EKF", s, re.I) and not any(t0 - 0.5 <= t <= t1 + 0.5 for t0, t1 in pw):
            disi.append([_r(t, 1), "MSG", s])
    disi.sort(key=lambda x: x[0])
    turler = [u["tur"] for u in ucuslar]
    return {
        "dosya": _gorel(yol), "sha256": sha or sha256_dosya(yol), "bayt": yol.stat().st_size,
        "MB": round(yol.stat().st_size / 1e6, 2), "kopyalar": [_gorel(Path(k)) for k in kopya_adlari],
        "mp_no": mp_no(adlar), "yazilim": ham["ver"], "log_suresi_s": _r((ham["t_son"] or 0) - (ham["t_ilk"] or 0), 1),
        "mesaj_n": {k: ham["sayac"].get(k, 0) for k in ("CTUN", "BAT", "VIBE", "RCOU", "ATT", "IMU", "ACC", "GYR",
                                                          "XKF4", "NKF4", "EV", "ARM", "MODE", "ERR", "MSG", "PARM",
                                                          "ESC", "RPM", "ISBH")},
        "hucre": {"n": n, "V_ilk": _r(v_ilk, 2), "adaylar": adaylar, "guven": "tek" if len(adaylar) == 1 else
                  ("coklu" if adaylar else "yok")},
        "kullanici_beyani": beyan,
        # GPS'siz (1980 tarihli) loglari SIRALAMAK icin: STAT_BOOTCNT ve STAT_RUNTIME (kumulatif s)
        # logun basindaki degerler — dosya adindaki tarihe bagimli olmayan mutlak sira.
        "sira": {"STAT_BOOTCNT": ham["parm_ilk"].get("STAT_BOOTCNT"),
                 "STAT_RUNTIME_ilk_s": ham["parm_ilk"].get("STAT_RUNTIME"),
                 "STAT_FLTTIME_ilk_s": ham["parm_ilk"].get("STAT_FLTTIME")},
        "parm": parm_sec(parm), "parm_degisim": ham["parm_degisim"],
        "imu": imu_bilgi,
        "arm_penceresi_kaynak": kaynak, "arm_pencere_n": len(pw), "rcou_arm_esigi": rc_esik,
        "ozet": {"ucus_n": turler.count("ucus"), "kisa_sicrama_n": turler.count("kisa_sicrama"),
                 "arm_yalniz_n": turler.count("arm_yalniz"),
                 "toplam_motorlu_s": _r(sum(u.get("motorlu_s") or 0 for u in ucuslar), 1),
                 "alt_maks_m": _r(max([u.get("alt_maks_m") or 0 for u in ucuslar] or [0]), 2),
                 "vibeZ_maks": _r(max([(u.get("vibe") or {}).get("Z", {}).get("maks") or 0 for u in ucuslar] or [0]), 1),
                 "vibeZ_pencere_maks": _r(max([(u.get("vibe") or {}).get("pencere_maks", {}).get("Z") or 0 for u in ucuslar] or [0]), 1),
                 "failsafe_n": sum(len(u.get("failsafe") or []) for u in ucuslar)},
        "ucuslar": ucuslar,
        "pencere_disi_olaylar": disi[:80],
    }


# ----------------------------------------------------------------------------- CLI
def _yollari_topla(argler):
    yollar = []
    for a in argler:
        p = Path(a)
        if p.is_dir():
            yollar.extend(sorted(p.glob("*.bin")) + sorted(p.glob("*.BIN")))
        elif p.is_file():
            yollar.append(p)
        else:
            print(f"YOK: {a}", file=sys.stderr)
    # ayni dosya iki kez verilmisse tekle
    gorulen, tek = set(), []
    for y in yollar:
        r = y.resolve()
        if r not in gorulen:
            gorulen.add(r); tek.append(y)
    return tek


def ozet_satiri(L):
    h = L["hucre"]; b = L["kullanici_beyani"]; o = L["ozet"]
    return (f"{L['dosya']:<52} sha {L['sha256'][:12]}  {h['n']}S {h['V_ilk']}V  beyan {b['etiket'] or '-'}"
            f"{'' if b['hucre_uyum'] in (True, None) else ' UYUMSUZ'}  pencere {L['arm_pencere_n']}"
            f" ucus {o['ucus_n']} kisa {o['kisa_sicrama_n']} armY {o['arm_yalniz_n']}"
            f"  motorlu {o['toplam_motorlu_s']} s  alt {o['alt_maks_m']} m  vibeZ {o['vibeZ_maks']}"
            f"  ThH {L['parm'].get('MOT_THST_HOVER')}  kopya {len(L['kopyalar'])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("yollar", nargs="*", help=".bin dosyalari ya da dizinler (verilis sirasi kopya esasini belirler)")
    ap.add_argument("--cikti", default=None, help="JSON cikti yolu (varsayilan: ekrana ozet)")
    ap.add_argument("--beyan", default=None, help="log govde adi → etiket JSON'u (BEYAN_ACIK'i ezer)")
    ap.add_argument("--sessiz", action="store_true")
    a = ap.parse_args(argv)
    if not a.yollar:
        ap.print_help(); return 1
    beyan_acik = None
    if a.beyan:
        beyan_acik = json.loads(Path(a.beyan).read_text(encoding="utf-8"))
    yollar = _yollari_topla(a.yollar)
    if not yollar:
        print("hic .bin bulunamadi", file=sys.stderr); return 1
    esaslar, kopyalar, sha = kopya_grupla(yollar)
    kopya_of = defaultdict(list)
    for k, e in kopyalar:
        kopya_of[e].append(k)
    loglar = []
    for y in esaslar:
        try:
            L = log_analiz(y, kopya_adlari=[str(k) for k in kopya_of[y]], sha=sha[y], beyan_acik=beyan_acik)
        except Exception as ex:  # tek bozuk log tum taramayi dusurmesin; hata kayda gecer
            L = {"dosya": _gorel(y), "sha256": sha[y], "HATA": f"{type(ex).__name__}: {ex}"}
        loglar.append(_temiz(L))
        if not a.sessiz:
            print(ozet_satiri(L) if "HATA" not in L else f"{L['dosya']}  HATA {L['HATA']}")
    cikti = {
        "meta": {
            "arac": "scripts/ucus_bin_analiz.py", "surum": SURUM,
            "uretim_zamani": _dt.datetime.now().isoformat(timespec="seconds"),
            "python": sys.version.split()[0], "pymavlink": _pymavlink_surum(), "numpy": np.__version__,
            "olcutler": {"motorlu_ThO_esik": MOTORLU_THO_ESIK, "kisa_sicrama_s": KISA_SICRAMA_S,
                         "aski": {"alt_min_m": ASKI_ALT_MIN_M, "vz_maks_ms": ASKI_VZ_MAKS_MS,
                                  "ThO": [ASKI_THO_MIN, ASKI_THO_MAKS], "en_az_ornek": ASKI_EN_AZ_ORNEK,
                                  "vz_kaynak": f"CTUN.Alt turevi, {VZ_ORTALAMA_PENCERE} ornek hareketli ortalama"},
                         "alt_taban": f"arm sonrasi ilk {ALT_TABAN_S} s CTUN.Alt medyani",
                         "hucre": {"V_hucre_aralik": [HUCRE_V_MIN, HUCRE_V_MAKS], "hedef": HUCRE_V_HEDEF},
                         "ekf_innov_esik": EKF_INNOV_ESIK, "dusuk_akim_A": DUSUK_AKIM_A,
                         "rcou_arm_esik": "PWM_MIN + 0.5*MOT_SPIN_ARM*(PWM_MAX-PWM_MIN) (PARM yoksa %d)" % RCOU_ARM_ESIK},
            "rsn_eslemesi": RSN_AD, "err_subsys": ERR_SUBSYS_AD, "konfig_beyani": KONFIG,
            "beyan_notu": "pil/pervane/kutle LOGDA YOK; 'kullanici_beyani' alani 15 Eylul 2026 kullanici beyanidir",
            "girdi": [_gorel(Path(p)) if Path(p).exists() else p for p in a.yollar],
            "dosya_n": len(yollar), "benzersiz_n": len(esaslar), "kopya_n": len(kopyalar),
        },
        "loglar": loglar,
        "kopyalar": [{"dosya": _gorel(k), "KOPYA_OF": _gorel(e), "sha256": sha[k]} for k, e in kopyalar],
    }
    if a.cikti:
        out = Path(a.cikti)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
        if not a.sessiz:
            print(f"-> yazildi: {out}  ({len(loglar)} benzersiz log, {len(kopyalar)} kopya)")
    return 0


def _pymavlink_surum():
    try:
        import pymavlink
        return getattr(pymavlink, "__version__", "?")
    except ImportError:
        return None


if __name__ == "__main__":
    sys.exit(main())
