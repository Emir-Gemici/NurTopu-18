"""6 Eylul tlog'larinda kumandadan arm sorusu: kanal araliklari, dumen-arm denemeleri, arm kaynagi, STATUSTEXT."""
import sys
from pathlib import Path
from pymavlink import mavutil

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for yol in sys.argv[1:]:
    print("=" * 90)
    print(Path(yol).name)
    m = mavutil.mavlink_connection(yol)
    kanal = {k: [None, None, set()] for k in range(1, 9)}
    rc_zaman = []          # (t, ch3, ch4, ch5, ch6)
    armed_gecis = []       # (t, armed)
    armed = None
    komutlar = []          # (t, src, cmd, p1)
    metin = []
    t0 = None
    while True:
        msg = m.recv_match(blocking=False)
        if msg is None:
            break
        tp = msg.get_type()
        t = getattr(msg, "_timestamp", 0.0)
        if t0 is None and t:
            t0 = t
        if tp == "RC_CHANNELS":
            vals = [getattr(msg, f"chan{k}_raw") for k in range(1, 9)]
            for k, v in enumerate(vals, 1):
                mn, mx, s = kanal[k]
                kanal[k][0] = v if mn is None else min(mn, v)
                kanal[k][1] = v if mx is None else max(mx, v)
                if len(s) < 40:
                    s.add(v)
            rc_zaman.append((t - t0, vals[2], vals[3], vals[4], vals[5]))
        elif tp == "HEARTBEAT" and msg.get_srcSystem() == 1 and msg.get_srcComponent() == 1:
            a = bool(msg.base_mode & 128)
            if a != armed:
                armed_gecis.append((t - t0, a))
                armed = a
        elif tp == "COMMAND_LONG" and msg.command == 400:
            komutlar.append((t - t0, msg.get_srcSystem(), msg.get_srcComponent(), msg.param1, msg.param2))
        elif tp == "STATUSTEXT":
            s = msg.text
            if any(w in s.lower() for w in ("arm", "throttle", "safety", "rudder", "rc ")):
                metin.append((t - t0, s))

    print("\nKANAL ARALIKLARI (RC_CHANNELS, ham PWM):")
    for k in range(1, 9):
        mn, mx, s = kanal[k]
        farkli = sorted(s)
        print(f"  CH{k}: min {mn} max {mx}  farklı değer sayısı {'≥40' if len(s) >= 40 else len(s)}  {farkli if len(s) <= 6 else ''}")

    print("\nARM DURUM GEÇİŞLERİ (HEARTBEAT sys1):")
    for t, a in armed_gecis:
        print(f"  t={t:8.1f}s  {'ARMED' if a else 'DISARMED'}")

    print("\nYER İSTASYONUNDAN ARM/DISARM KOMUTLARI (COMMAND_LONG 400):")
    for t, ss, sc, p1, p2 in komutlar:
        print(f"  t={t:8.1f}s  kaynak sys{ss}/comp{sc}  param1={p1:.0f} ({'ARM' if p1 else 'DISARM'})  force={p2:.0f}")
    if not komutlar:
        print("  (yok)")

    # dumen-arm denemesi: gaz <=1100 ve yaw >=1900 kesintisiz >=1.0 s
    print("\nDÜMENLE ARM DENEMESİ PENCERELERİ (CH3≤1100 ∧ CH4≥1900, ≥1,0 s):")
    bas = None
    bulundu = 0
    for i, (t, c3, c4, c5, c6) in enumerate(rc_zaman):
        kosul = c3 <= 1100 and c4 >= 1900
        if kosul and bas is None:
            bas = t
        if (not kosul or i == len(rc_zaman) - 1) and bas is not None:
            son = t
            if son - bas >= 1.0:
                bulundu += 1
                durum = [a for tt, a in armed_gecis if tt <= son + 3]
                print(f"  {bas:8.1f}–{son:6.1f}s ({son - bas:.1f} s)  → arm geçişi ±3 s içinde: "
                      f"{[ (round(tt,1), 'ARM' if a else 'DIS') for tt, a in armed_gecis if bas - 1 <= tt <= son + 3] or 'YOK'}")
            bas = None
    if not bulundu:
        print("  (hiç yok)")
    # yaw sola disarm denemesi
    print("\nDÜMENLE DISARM DENEMESİ (CH3≤1100 ∧ CH4≤1100, ≥1,0 s):")
    bas = None; bulundu = 0
    for i, (t, c3, c4, c5, c6) in enumerate(rc_zaman):
        kosul = c3 <= 1100 and c4 <= 1100
        if kosul and bas is None:
            bas = t
        if (not kosul or i == len(rc_zaman) - 1) and bas is not None:
            if t - bas >= 1.0:
                bulundu += 1
                print(f"  {bas:8.1f}–{t:6.1f}s ({t - bas:.1f} s)  → geçiş: {[ (round(tt,1), 'ARM' if a else 'DIS') for tt, a in armed_gecis if bas - 1 <= tt <= t + 3] or 'YOK'}")
            bas = None
    if not bulundu:
        print("  (hiç yok)")

    print("\nSTATUSTEXT (arm/throttle/safety/rudder/rc):")
    for t, s in metin[:40]:
        print(f"  t={t:8.1f}s  {s}")
    if not metin:
        print("  (yok)")
