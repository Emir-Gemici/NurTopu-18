#!/usr/bin/env python3
"""ArduPilot DataFlash (.bin) — kalkışta devrilme teşhisi (D-428).

NEDEN: 5 Eylül 2026'da iki kez aynı olay: arka kalktı, ön kalkmadı, öne devrildi.
Pervane eli, motor sırası/yönü, kart yönelimi, X gövde, ESC kalibrasyonu, CG ve
pitch girişi elle DOĞRULANDI (beyan). Beyan tükendi; log ölçümdür. Pixhawk her
döngüde motor komutlarını (RCOU), tutumu (ATT), pilot girişini (RCIN) ve TÜM
parametreleri (PARM) yazar — beyana gerek kalmaz.

NE ÜRETİR (her arm penceresi için):
  1. Kritik parametreler logdan (FRAME_TYPE, AHRS_ORIENTATION, AHRS_TRIM, RCn_REVERSED,
     RCn_TRIM, MOT_SPIN_*, MOT_PWM_*, INS_ACC*OFFS, COMPASS_OFS) — beyanla değil logla.
  2. 0,1 s çözünürlükte tablo: t · pitch/roll (gerçek ve istenen) · RCIN gaz/pitch ·
     RCOU C1..C4 · CTUN ThO.
  3. Hüküm yardımcısı: burun ilk kez -10°'yi geçtiği anda FC hangi motorlara ne
     komut veriyordu?
       - ön (C1,C3) MAX'a, arka (C2,C4) MIN'e çekilmiş  → FC düzeltiyor, ÖN İTKİ FİZİKSEL
         OLARAK YETMİYOR (motor/ESC/pervane/kol) ya da yer pivotu
       - dördü ~eşit                                   → FC düzeltmiyor: düz referansı /
         landed mantığı / gaz çok düşük
       - arka yukarı, ön aşağı                          → eksen/eşleme TERS (yönelim/mixer)
  4. VIBE, EV (arm/disarm/land), MODE, MSG satırları.

KULLANIM:
  python scripts/ucus_logu_devrilme.py results/ucus_loglari/20260905/*.bin
  (çıktı ekrana ve her .bin'in yanına <ad>_devrilme.txt)

Sınır: bu betik hüküm VERMEZ, hükmü mümkün kılan sayıları çıkarır. Yorum D-kaydına yazılır.
"""

import sys
from collections import defaultdict
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

try:
    from pymavlink import mavutil
except ImportError:
    print("pymavlink yok — depo venv'iyle koş: O:\\navitas-local-train\\venv\\Scripts\\python.exe")
    sys.exit(1)

KRITIK_PARM = [
    "FRAME_CLASS", "FRAME_TYPE", "AHRS_ORIENTATION", "AHRS_TRIM_X", "AHRS_TRIM_Y", "AHRS_TRIM_Z",
    "RC1_REVERSED", "RC2_REVERSED", "RC3_REVERSED", "RC4_REVERSED",
    "RC1_TRIM", "RC2_TRIM", "RC3_TRIM", "RC4_TRIM", "RC3_MIN", "RC3_MAX",
    "RC_PROTOCOLS", "MOT_PWM_TYPE", "MOT_PWM_MIN", "MOT_PWM_MAX",
    "MOT_SPIN_ARM", "MOT_SPIN_MIN", "MOT_SPIN_MAX", "MOT_THST_HOVER", "MOT_THST_EXPO",
    "ARMING_CHECK", "ARMING_RUDDER", "FS_THR_ENABLE", "FS_THR_VALUE",
    "INS_ACCOFFS_X", "INS_ACCOFFS_Y", "INS_ACCOFFS_Z", "INS_ACC2OFFS_X", "INS_ACC2OFFS_Y", "INS_ACC2OFFS_Z",
    "COMPASS_OFS_X", "COMPASS_OFS_Y", "COMPASS_OFS_Z", "COMPASS_ORIENT",
    "ATC_ANG_PIT_P", "ATC_RAT_PIT_P", "PILOT_THR_BHV",
]
EV_AD = {10: "ARMED", 11: "DISARMED", 15: "AUTO_ARMED", 18: "LAND_COMPLETE", 28: "NOT_LANDED",
         17: "LAND_COMPLETE_MAYBE", 62: "MOTORS_EMERGENCY_STOPPED", 63: "MOTORS_EMERGENCY_STOP_CLEARED",
         25: "SET_HOME", 51: "ARMED_HAS_FOLLOWERS"}


def _t(m):
    return getattr(m, "TimeUS", 0) / 1e6


def oku(yol: Path):
    log = mavutil.mavlink_connection(str(yol))
    parm, ev, mode, msg = {}, [], [], []
    att, rcou, rcin, ctun, vibe = [], [], [], [], []
    while True:
        m = log.recv_match(blocking=False)
        if m is None:
            break
        tip = m.get_type()
        if tip == "PARM":
            parm[m.Name] = m.Value
        elif tip == "EV":
            ev.append((_t(m), m.Id))
        elif tip == "MODE":
            mode.append((_t(m), getattr(m, "Mode", "?"), getattr(m, "ModeNum", "?")))
        elif tip == "MSG":
            msg.append((_t(m), m.Message))
        elif tip == "ATT":
            att.append((_t(m), m.Roll, m.Pitch, getattr(m, "DesRoll", 0.0), getattr(m, "DesPitch", 0.0)))
        elif tip == "RCOU":
            rcou.append((_t(m), m.C1, m.C2, m.C3, m.C4))
        elif tip == "RCIN":
            rcin.append((_t(m), m.C1, m.C2, m.C3, m.C4))
        elif tip == "CTUN":
            ctun.append((_t(m), getattr(m, "ThO", 0.0), getattr(m, "Alt", 0.0)))
        elif tip == "VIBE":
            vibe.append((_t(m), getattr(m, "VibeX", 0.0), getattr(m, "VibeY", 0.0), getattr(m, "VibeZ", 0.0)))
    return parm, ev, mode, msg, att, rcou, rcin, ctun, vibe


def _son_once(seri, t, idx):
    """seri[idx] zaman-sıralı; t'den önceki son kaydı döndür (idx ilerletilir)."""
    while idx + 1 < len(seri) and seri[idx + 1][0] <= t:
        idx += 1
    return seri[idx] if seri and seri[idx][0] <= t else None, idx


def pencereler(ev, att, rcou):
    """ARM→DISARM pencereleri; EV yoksa RCOU>1100 aralıklarından türet."""
    p, acik = [], None
    for t, i in ev:
        if i in (10, 15) and acik is None:
            acik = t
        elif i == 11 and acik is not None:
            p.append((acik, t)); acik = None
    if acik is not None:
        p.append((acik, rcou[-1][0] if rcou else att[-1][0] if att else acik))
    if not p and rcou:
        # EV yok: motor komutu 1100'ü aşan sürekli aralıklar
        basla = None
        for t, *c in rcou:
            if max(c) > 1100 and basla is None:
                basla = t
            elif max(c) <= 1100 and basla is not None:
                p.append((basla, t)); basla = None
        if basla is not None:
            p.append((basla, rcou[-1][0]))
    return p


def analiz(yol: Path):
    out = []
    P = out.append
    parm, ev, mode, msg, att, rcou, rcin, ctun, vibe = oku(yol)
    P(f"# {yol.name}")
    P(f"kayit: ATT {len(att)} · RCOU {len(rcou)} · RCIN {len(rcin)} · CTUN {len(ctun)} · EV {len(ev)} · PARM {len(parm)}")
    if not rcou:
        P("RCOU YOK — LOG_BITMASK'ta RCOUT kapali ya da log bos. Hukum verilemez (OLCULEMEDI).")
        return "\n".join(out)

    P("\n## 1. Kritik parametreler (LOGDAN — beyan degil)")
    for k in KRITIK_PARM:
        if k in parm:
            P(f"  {k:18s} = {parm[k]:g}")
    eksik = [k for k in KRITIK_PARM if k not in parm]
    if eksik:
        P(f"  (logda yok: {', '.join(eksik)})")

    P("\n## 2. Olaylar")
    for t, i in ev:
        P(f"  EV  t={t:8.2f}  {i:3d} {EV_AD.get(i, '')}")
    for t, ad, n in mode:
        P(f"  MODE t={t:8.2f}  {ad} ({n})")
    for t, s in msg:
        P(f"  MSG t={t:8.2f}  {s}")

    pw = pencereler(ev, att, rcou)
    P(f"\n## 3. Arm pencereleri: {len(pw)}")
    ia = ir = ii = ic = 0
    for k, (t0, t1) in enumerate(pw, 1):
        P(f"\n### Pencere {k}: {t0:.2f} → {t1:.2f} s  (sure {t1 - t0:.1f} s)")
        P("   t(s)  pitch  desP   roll  desR | gaz  pitchIn | C1(saO) C2(soA) C3(soO) C4(saA) | ThO")
        t = t0
        ilk_burun = None
        while t <= t1 + 0.05:
            a, ia = _son_once(att, t, ia)
            r, ir = _son_once(rcou, t, ir)
            i_, ii = _son_once(rcin, t, ii)
            c, ic = _son_once(ctun, t, ic)
            if a and r:
                _, roll, pitch, desr, desp = a
                _, c1, c2, c3, c4 = r
                gaz = i_[3] if i_ else 0
                pin = i_[2] if i_ else 0
                tho = c[1] if c else 0.0
                P(f"  {t - t0:5.1f} {pitch:6.1f} {desp:6.1f} {roll:6.1f} {desr:6.1f} | {gaz:4d} {pin:7d} | {c1:6d} {c2:7d} {c3:7d} {c4:7d} | {tho:5.2f}")
                if ilk_burun is None and pitch <= -10.0:
                    ilk_burun = (t - t0, pitch, c1, c2, c3, c4, gaz)
            t += 0.1
        if ilk_burun:
            dt, pitch, c1, c2, c3, c4, gaz = ilk_burun
            on, arka = (c1 + c3) / 2, (c2 + c4) / 2
            P(f"\n  BURUN ILK KEZ ≤ -10° : t+{dt:.1f} s, pitch {pitch:.1f}°, gaz {gaz}")
            P(f"     on  (C1 sag on, C3 sol on) ort = {on:.0f}   arka (C2 sol arka, C4 sag arka) ort = {arka:.0f}")
            if on - arka > 150:
                P("     → FC ONU KALDIRMAYA CALISIYOR (on >> arka). On itki fiziksel olarak yetmiyor ya da"
                  " on ayaklar yerde pivot: motor/ESC/pervane/kol/zemin ekseni.")
            elif arka - on > 150:
                P("     → FC ARKAYI KALDIRIYOR (arka >> on) — burun asagiyken bu TERS: eksen/eslesme/yonelim.")
            else:
                P("     → Dordu ~esit: FC duzeltmiyor — duz referansi, landed mantigi ya da gaz cok dusuk.")
        else:
            P("\n  Bu pencerede pitch -10°'yi gecmedi.")
        # pencere ozeti
        w = [x for x in rcou if t0 <= x[0] <= t1]
        if w:
            P("  RCOU max: C1 %d C2 %d C3 %d C4 %d · min: C1 %d C2 %d C3 %d C4 %d" % (
                max(x[1] for x in w), max(x[2] for x in w), max(x[3] for x in w), max(x[4] for x in w),
                min(x[1] for x in w), min(x[2] for x in w), min(x[3] for x in w), min(x[4] for x in w)))
        wa = [x for x in att if t0 <= x[0] <= t1]
        if wa:
            P("  ATT pitch min %.1f max %.1f · roll min %.1f max %.1f" % (
                min(x[2] for x in wa), max(x[2] for x in wa), min(x[1] for x in wa), max(x[1] for x in wa)))
        # yerde dururken tutum (arm oncesi 2 s)
        onc = [x for x in att if t0 - 2.0 <= x[0] < t0]
        if onc:
            P("  ARM ONCESI 2 s ort: pitch %.2f° roll %.2f° (ayaklar ustunde 'duz' referansi — |1°| olmali)" % (
                sum(x[2] for x in onc) / len(onc), sum(x[1] for x in onc) / len(onc)))
    if vibe:
        P("\n## 4. VIBE (max): X %.1f Y %.1f Z %.1f" % (max(v[1] for v in vibe), max(v[2] for v in vibe), max(v[3] for v in vibe)))
    return "\n".join(out)


def main(argv):
    yollar = [Path(a) for a in argv[1:]]
    if not yollar:
        print(__doc__); return 1
    kod = 0
    for y in yollar:
        if not y.is_file():
            print(f"YOK: {y}"); kod = 1; continue
        rapor = analiz(y)
        print(rapor)
        (y.with_name(y.stem + "_devrilme.txt")).write_text(rapor, encoding="utf-8")
        print(f"\n→ yazildi: {y.with_name(y.stem + '_devrilme.txt')}\n")
    return kod


if __name__ == "__main__":
    sys.exit(main(sys.argv))
