#!/usr/bin/env python3
"""Mission Planner telemetri logu (.tlog) — kalkışta devrilme teşhisi (D-429).

NEDEN: DataFlash (.bin) indirilmediyse bile Mission Planner bağlıyken her oturumu
`logs\\<ARAÇ>\\1\\<tarih saat>.tlog` olarak KENDİSİ yazar. İçinde telemetri hızında
ATTITUDE (roll/pitch), SERVO_OUTPUT_RAW (çıkış PWM'leri, port 0 = MAIN 1–8, port 1 =
AUX 9–16), RC_CHANNELS (pilot girişi), HEARTBEAT (armed bayrağı), STATUSTEXT
(PreArm / Arming / Land) ve PARAM_VALUE (bağlanınca çekilen TÜM parametreler) vardır.
Bu, olay anına ait tek kanıttır; beyan değildir.

NE ÜRETİR (her arm penceresi için):
  1. Kritik parametreler tlog'daki PARAM_VALUE'dan (kart o an ne diyordu).
  2. 0,1 s tablo: t · pitch/roll · gaz/pitch girişi · AUX1..4 (servo9–12) · MAIN1..4.
  3. Burun ilk kez ≤ -10°'ye düştüğü anda ön/arka motor komutları — ESC'lerin AUX'ta
     olduğu ve SERVO9–12 = M4, M2, M1, M3 eşlemesi (6 Eylül dökümü) varsayılarak:
       AUX1 = M4 sağ arka · AUX2 = M2 sol arka · AUX3 = M1 sağ ön · AUX4 = M3 sol ön
     (eşleme tlog'daki SERVOn_FUNCTION'dan YENİDEN okunur; varsayım değil.)
  4. STATUSTEXT satırları (Arming, PreArm, Land, crash, EKF).

KULLANIM:
  python scripts/ucus_tlog_devrilme.py "C:/Users/<k>/Documents/Mission Planner/logs/QUADROTOR/1/<dosya>.tlog"
  (çıktı ekrana ve <dosya>_devrilme.txt)
"""

import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from pymavlink import mavutil  # noqa: E402

MOTOR_FN = {33: "M1", 34: "M2", 35: "M3", 36: "M4"}
KONUM = {"M1": "sağ ön CCW", "M2": "sol arka CCW", "M3": "sol ön CW", "M4": "sağ arka CW"}
KRITIK = ["FRAME_CLASS", "FRAME_TYPE", "AHRS_ORIENTATION", "AHRS_TRIM_X", "AHRS_TRIM_Y",
          "RC1_REVERSED", "RC2_REVERSED", "RC3_REVERSED", "RC4_REVERSED", "RC2_TRIM", "RC3_MIN", "RC3_MAX",
          "RC_SPEED", "MOT_PWM_TYPE", "MOT_PWM_MIN", "MOT_PWM_MAX", "MOT_SPIN_ARM", "MOT_SPIN_MIN",
          "MOT_THST_HOVER", "RC_PROTOCOLS", "ARMING_CHECK", "FS_THR_ENABLE", "FS_THR_VALUE",
          "FS_GCS_ENABLE", "BATT_FS_LOW_ACT", "INS_ACCOFFS_Z", "COMPASS_OFS_X", "COMPASS_OFS_Y", "COMPASS_OFS_Z"]


def analiz(yol: Path):
    out = []
    P = out.append
    log = mavutil.mavlink_connection(str(yol))
    parm, txt, att, rc, srv0, srv1, hb = {}, [], [], [], [], [], []
    t0 = None
    while True:
        m = log.recv_match(blocking=False)
        if m is None:
            break
        ts = getattr(m, "_timestamp", 0.0)
        if t0 is None:
            t0 = ts
        t = ts - t0
        tip = m.get_type()
        if tip == "PARAM_VALUE":
            parm[m.param_id.strip("\x00")] = m.param_value
        elif tip == "STATUSTEXT":
            txt.append((t, m.text.strip("\x00")))
        elif tip == "ATTITUDE":
            att.append((t, m.roll * 57.2958, m.pitch * 57.2958))
        elif tip == "RC_CHANNELS":
            rc.append((t, m.chan1_raw, m.chan2_raw, m.chan3_raw, m.chan4_raw))
        elif tip == "SERVO_OUTPUT_RAW":
            # MAVLink2: tek mesajda servo1..16 (9-16 uzanti alani), port=0. MAVLink1: port 1
            # ayri mesaj. Ikisini de destekle: 9-16 doluysa AUX olarak srv1'e yaz.
            vals = [getattr(m, f"servo{i}_raw", 0) for i in range(1, 9)]
            ext = [getattr(m, f"servo{i}_raw", 0) for i in range(9, 17)]
            if getattr(m, "port", 0) == 1:
                srv1.append((t, vals))
            else:
                srv0.append((t, vals))
                if any(ext):
                    srv1.append((t, ext))
        elif tip == "HEARTBEAT" and m.get_srcSystem() == 1 and m.type != 6:
            hb.append((t, bool(m.base_mode & 128), m.custom_mode))

    P(f"# {yol.name}")
    P(f"kayit: ATTITUDE {len(att)} · RC_CHANNELS {len(rc)} · SERVO port0 {len(srv0)} · port1 {len(srv1)} · HEARTBEAT {len(hb)} · PARAM {len(parm)} · STATUSTEXT {len(txt)}")
    if not att or not (srv0 or srv1):
        P("ATTITUDE ya da SERVO_OUTPUT_RAW yok — bu tlog olay anini kapsamiyor olabilir (OLCULEMEDI).")
        return "\n".join(out)

    P("\n## 1. Kritik parametreler (tlog PARAM_VALUE — kart o an ne diyordu)")
    for k in KRITIK:
        if k in parm:
            P(f"  {k:16s} = {parm[k]:g}")
    esleme = {}
    for i in range(1, 17):
        fn = int(parm.get(f"SERVO{i}_FUNCTION", -1))
        if fn in MOTOR_FN:
            esleme[i] = MOTOR_FN[fn]
    if esleme:
        P("  Motor cikis eslemesi (SERVOn_FUNCTION): " + ", ".join(f"S{i}={esleme[i]}" for i in sorted(esleme)))
        cift = {}
        for i, mo in esleme.items():
            cift.setdefault(mo, []).append(i)
        for mo, ports in cift.items():
            if len(ports) > 1:
                P(f"  ⚠ {mo} ({KONUM[mo]}) {len(ports)} cikista birden: {ports} — bos cikislar zararsiz, DOLU cikis varsa ayni komutu alir")
    else:
        P("  (SERVOn_FUNCTION tlog'da yok — eslemeyi dokumden al)")

    P("\n## 2. STATUSTEXT")
    for t, s in txt:
        P(f"  t={t:8.1f}  {s}")

    # arm pencereleri
    pw, acik = [], None
    for t, armed, _ in hb:
        if armed and acik is None:
            acik = t
        elif not armed and acik is not None:
            pw.append((acik, t)); acik = None
    if acik is not None:
        pw.append((acik, hb[-1][0]))
    P(f"\n## 3. Arm pencereleri (HEARTBEAT armed): {len(pw)}")

    def son(seri, t, idx):
        while idx + 1 < len(seri) and seri[idx + 1][0] <= t:
            idx += 1
        return (seri[idx] if seri and seri[idx][0] <= t else None), idx

    aux_motor = {i - 8: esleme.get(i) for i in range(9, 13)}  # AUX1..4
    ia = ir = i0 = i1 = 0
    for k, (ta, tb) in enumerate(pw, 1):
        P(f"\n### Pencere {k}: {ta:.1f} → {tb:.1f} s (sure {tb - ta:.1f} s)")
        P("   t    pitch   roll | gaz  pitIn | AUX1   AUX2   AUX3   AUX4  | MAIN1  MAIN2  MAIN3  MAIN4")
        P("                      |            | " + "  ".join(f"{(aux_motor.get(i) or '?'):>5s}" for i in range(1, 5)))
        ilk = None
        t = max(0.0, ta - 1.0)
        while t <= tb + 0.5:
            a, ia = son(att, t, ia)
            r, ir = son(rc, t, ir)
            s0, i0 = son(srv0, t, i0)
            s1, i1 = son(srv1, t, i1)
            if a:
                _, roll, pitch = a
                gaz, pin = (r[3], r[2]) if r else (0, 0)
                v1 = s1[1] if s1 else [0] * 8
                v0 = s0[1] if s0 else [0] * 8
                P(f"  {t - ta:5.1f} {pitch:6.1f} {roll:6.1f} | {gaz:4d} {pin:6d} | {v1[0]:5d}  {v1[1]:5d}  {v1[2]:5d}  {v1[3]:5d}  | {v0[0]:5d}  {v0[1]:5d}  {v0[2]:5d}  {v0[3]:5d}")
                if ilk is None and pitch <= -10.0 and t >= ta:
                    ilk = (t - ta, pitch, v1[:4], gaz)
            t += 0.1
        if ilk:
            dt, pitch, v, gaz = ilk
            on = [v[i - 1] for i in range(1, 5) if aux_motor.get(i) in ("M1", "M3")]
            arka = [v[i - 1] for i in range(1, 5) if aux_motor.get(i) in ("M2", "M4")]
            P(f"\n  BURUN ILK KEZ ≤ -10°: t+{dt:.1f} s, pitch {pitch:.1f}°, gaz {gaz}")
            if on and arka:
                o, ar = sum(on) / len(on), sum(arka) / len(arka)
                P(f"     on ort {o:.0f} (M1/M3) · arka ort {ar:.0f} (M2/M4)")
                if o - ar > 150:
                    P("     → FC ONU KALDIRIYOR: on itki fiziksel olarak yetmiyor (motor/ESC/pervane/kol) ya da on ayak pivotu")
                elif ar - o > 150:
                    P("     → FC ARKAYI KALDIRIYOR — burun asagiyken TERS: eslesme/yonelim")
                else:
                    P("     → dordu ~esit: FC duzeltmiyor (duz referansi / landed / gaz dusuk)")
        else:
            P("\n  Bu pencerede pitch -10°'yi gecmedi.")
    return "\n".join(out)


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 1
    kod = 0
    for a in argv[1:]:
        y = Path(a)
        if not y.is_file():
            print(f"YOK: {y}"); kod = 1; continue
        r = analiz(y)
        print(r)
        o = y.with_name(y.stem + "_devrilme.txt")
        o.write_text(r, encoding="utf-8")
        print(f"\n→ yazildi: {o}\n")
    return kod


if __name__ == "__main__":
    sys.exit(main(sys.argv))
