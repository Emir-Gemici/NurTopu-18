# Curutucu 2: kalan sayisal iddialar
import pickle, math
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
B = pickle.load(open(S+"c2_b.pkl","rb")); d = B["d"]; parm = B["parm"]
def T(r): return r["TimeUS"]/1e6
def W(tip,a,b,**f): return [r for r in d[tip] if a<=T(r)<=b and all(r.get(k)==v for k,v in f.items())]
print("== 79.2-79.8 IMU/VIBE/CTUN")
for r in W("IMU",79.25,79.65):
    print("%.3f I%d |a| %.2f AccZ %.2f GyrX %.1f" % (T(r), r["I"], math.sqrt(r["AccX"]**2+r["AccY"]**2+r["AccZ"]**2), r["AccZ"], math.degrees(r["GyrX"])))
for r in W("VIBE",79.2,79.8): print("%.3f VIBE%d Z %.1f Clip %d" % (T(r), r["IMU"], r["VibeZ"], r["Clip"]))
for r in W("CTUN",79.0,80.0): print("%.3f CTUN Alt %.2f ThO %.3f" % (T(r), r["Alt"], r["ThO"]))
print("== Clip degisimleri (tum log)")
for i in (0,1):
    v = [r for r in d["VIBE"] if r["IMU"]==i]; prev=None
    for r in v:
        if prev is not None and r["Clip"]!=prev: print("  IMU%d %.3f %d->%d" % (i, T(r), prev, r["Clip"]))
        prev = r["Clip"]
print("== Son ucus 188.3-202.37 araliklar")
a,b = 188.3, 202.37
rc = W("RCOU",188.4,202.37)
for k,n in [("C11","M1"),("C10","M2"),("C12","M3"),("C9","M4")]:
    x = np.array([r[k] for r in rc]); print("  %s min %d max %d" % (n, x.min(), x.max()))
rc2 = W("RCOU",188.4,202.30)
print("  188.4-202.30 M4 min", min(r["C9"] for r in rc2))
v = W("VIBE",a,b,IMU=0); z = np.array([r["VibeZ"] for r in v]); j = np.argmax(z); print("  VibeZ0 max %.2f @ %.3f" % (z[j], T(v[j])))
v1 = W("VIBE",a,b,IMU=1); z1 = np.array([r["VibeZ"] for r in v1]); j1 = np.argmax(z1); print("  VibeZ1 max %.2f @ %.3f" % (z1[j1], T(v1[j1])))
bt = W("BAT",188.4,202.37); print("  BAT V %.2f..%.2f I %.1f..%.1f" % (min(r["Volt"] for r in bt), max(r["Volt"] for r in bt), min(r["Curr"] for r in bt), max(r["Curr"] for r in bt)))
pw = W("POWR",188.4,202.37); print("  POWR Vcc %.3f..%.3f VServo %.3f..%.3f Flags %s AccFlags %s" % (min(r["Vcc"] for r in pw), max(r["Vcc"] for r in pw), min(r["VServo"] for r in pw), max(r["VServo"] for r in pw), sorted(set(r["Flags"] for r in pw)), sorted(set(r["AccFlags"] for r in pw))))
rn = W("RCIN",181.7,204.0); tt = np.array([T(r) for r in rn]); print("  RCIN dt max %.3f n %d" % (np.diff(tt).max(), len(tt)))
im = W("IMU",190.0,202.30,I=0); gz = np.degrees([r["GyrZ"] for r in im]); print("  IMU0 GyrZ 190-202.30 min %.1f mean %.2f std %.1f" % (gz.min(), gz.mean(), gz.std()))
at = W("ATT",190.0,202.37); print("  ATT Yaw 190.0 %.1f  202.37 %.1f  DesYaw %.1f..%.1f" % (at[0]["Yaw"], at[-1]["Yaw"], min(r["DesYaw"] for r in at), max(r["DesYaw"] for r in at)))
print("== 194.5-195.0 IMU GyrZ")
for r in W("IMU",194.5,195.0): print("  %.3f I%d GyrZ %.1f" % (T(r), r["I"], math.degrees(r["GyrZ"])))
print("== W5 1 s kutular (140.9 tabanli) CCW-CW")
for s in np.arange(140.9, 147.5, 1.0):
    rr = W("RCOU", s, s+1.0-1e-6)
    if rr: print("  %.1f %+.0f n%d" % (s, np.mean([r["C11"]+r["C10"]-r["C12"]-r["C9"] for r in rr]), len(rr)))
print("== ATC params")
for k in ["ATC_ANG_YAW_P","ATC_RAT_YAW_IMAX","ATC_RAT_RLL_IMAX","MOT_HOVER_LEARN","MOT_THST_EXPO","RC1_REVERSED","RC1_DZ","RC4_DZ","FS_CRASH_CHECK","MOT_YAW_HEADROOM","SERVO_BLH_MASK","SERVO_DSHOT_ESC","MOT_PWM_TYPE","BRD_IO_ENABLE","COMPASS_USE","COMPASS_USE2","COMPASS_DEV_ID","COMPASS_DEV_ID2","GPS_TYPE","GPS1_TYPE","INS_POS2_X","INS_POS3_X"]:
    print(" ", k, parm.get(k))
