import pickle
def pm(p):
    v = pickle.load(open(p,"rb")); d = {}
    for x in v["PARM"]: d[x["Name"]] = x["Value"]   # son deger
    return v, d
va, a = pm("a.pkl"); vb, b = pm("b.pkl")
print("param sayisi a,b:", len(a), len(b))
for k in sorted(set(a)|set(b)):
    if a.get(k) != b.get(k):
        print(f"FARK {k}: a={a.get(k)} b={b.get(k)}")
for k in ["MOT_THST_EXPO","MOT_SPIN_MIN","MOT_SPIN_MAX","MOT_PWM_MIN","MOT_PWM_MAX","MOT_YAW_HEADROOM","MOT_THST_HOVER","MOT_HOVER_LEARN","INS_POS1_X","INS_POS1_Y","INS_POS1_Z","INS_POS2_X","INS_POS2_Y","INS_ACCEL_FILTER","INS_GYRO_FILTER","ATC_RAT_YAW_IMAX","ATC_RAT_YAW_I","ATC_RAT_YAW_FLTE","ATC_ANG_YAW_P","MOT_OPTIONS","SERVO9_FUNCTION","SERVO10_FUNCTION","SERVO11_FUNCTION","SERVO12_FUNCTION","SERVO9_REVERSED","SERVO_BLH_MASK","SERVO_DSHOT_ESC","MOT_PWM_TYPE","BATT_AMP_PERVLT","BATT_AMP_OFFSET","ATC_THR_MIX_MAN","ATC_THR_MIX_MAX","INS_LOG_BAT_OPT","FRAME_TYPE","PSC_ACCZ_P"]:
    print(k, a.get(k), b.get(k))
for nm, v in (("a", va), ("b", vb)):
    print("=== olaylar", nm)
    rows = []
    for tip in ("EV","ARM","MODE","ERR"):
        for d in v.get(tip, []): rows.append((d["t"], tip, {k:x for k,x in d.items() if k not in ("TimeUS","t")}))
    for d in v.get("MSG", []): rows.append((d["t"], "MSG", d["Message"]))
    for r in sorted(rows, key=lambda r: r[0]): print(f"{r[0]:9.3f} {r[1]:4} {r[2]}")
