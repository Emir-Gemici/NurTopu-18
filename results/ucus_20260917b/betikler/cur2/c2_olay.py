# Curutucu 2: olay penceresi ham degerler
import pickle, math, sys
P = pickle.load(open(r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/c2_b.pkl","rb"))
d, parm = P["d"], P["parm"]
t0, t1 = float(sys.argv[1]), float(sys.argv[2])
def T(r): return r["TimeUS"]/1e6
def win(tip):
    return [r for r in d.get(tip, []) if t0 <= T(r) <= t1]
print("== PARAM")
for k in ["SERVO%d_FUNCTION"%i for i in range(1,17)] + ["MOT_PWM_MIN","MOT_PWM_MAX","MOT_SPIN_MIN","MOT_SPIN_MAX","MOT_SLEW_UP_TIME","MOT_SLEW_DN_TIME","ATC_RAT_RLL_P","ATC_RAT_RLL_I","ATC_RAT_RLL_D","ATC_RAT_PIT_P","ATC_RAT_PIT_I","ATC_RAT_PIT_D","ATC_RAT_YAW_P","ATC_RAT_YAW_I","ATC_RAT_YAW_IMAX","INS_HNTCH_ENABLE","BATT_AMP_PERVLT","BATT_AMP_OFFSET","BATT_VOLT_MULT","BATT_MONITOR","MOT_THST_HOVER","FS_CRASH_CHECK","INS_POS1_X","INS_POS1_Y","INS_POS1_Z","AHRS_ORIENTATION","MOT_BAT_VOLT_MAX","INS_GYRO_FILTER","INS_ACCEL_FILTER","INS_LOG_BAT_MASK","LOG_DISARMED"]:
    print(k, parm.get(k))
print("== IMU")
for r in win("IMU"):
    a = math.sqrt(r["AccX"]**2+r["AccY"]**2+r["AccZ"]**2)
    print("%.3f I%d GyrX %7.1f GyrY %7.1f GyrZ %7.1f AccX %6.2f AccY %6.2f AccZ %6.2f |a| %6.2f" % (T(r), r["I"], math.degrees(r["GyrX"]), math.degrees(r["GyrY"]), math.degrees(r["GyrZ"]), r["AccX"], r["AccY"], r["AccZ"], a))
print("== RCOU (C9=?,C10,C11,C12)")
for r in win("RCOU"):
    M4,M2,M1,M3 = r["C9"],r["C10"],r["C11"],r["C12"]
    print("%.3f M1(C11) %d M2(C10) %d M3(C12) %d M4(C9) %d  CCW-CW %+d  C1..C8 %s" % (T(r), M1,M2,M3,M4,(M1+M2)-(M3+M4), [r["C%d"%i] for i in range(1,9)]))
print("== BAT")
for r in win("BAT"):
    print("%.3f %s" % (T(r), {k: r.get(k) for k in ["Inst","Volt","VoltR","Curr","CurrTot","Res"]}))
print("== ATT")
for r in win("ATT"):
    print("%.3f DesR %.1f R %.1f DesP %.1f P %.1f DesY %.1f Y %.1f" % (T(r), r["DesRoll"], r["Roll"], r["DesPitch"], r["Pitch"], r["DesYaw"], r["Yaw"]))
print("== VIBE")
for r in win("VIBE"):
    print("%.3f %s" % (T(r), {k: r.get(k) for k in ["IMU","VibeX","VibeY","VibeZ","Clip"]}))
print("== MAG")
for r in win("MAG"):
    print("%.3f %s" % (T(r), {k: r.get(k) for k in ["I","MagX","MagY","MagZ","Health","S"]}))
print("== GPS")
for r in [r for r in d["GPS"] if t0-1 <= T(r) <= t1+5]:
    print("%.3f %s" % (T(r), {k: r.get(k) for k in ["I","Status","NSats","HDop","Alt","Spd"]}))
print("== RCIN")
for r in win("RCIN"):
    print("%.3f %s" % (T(r), [r["C%d"%i] for i in range(1,9)]))
print("== CTUN")
for r in win("CTUN"):
    print("%.3f ThI %.3f ThO %.3f ThH %.3f DAlt %.2f Alt %.2f BAlt %.2f CRt %.0f" % (T(r), r["ThI"], r["ThO"], r["ThH"], r["DAlt"], r["Alt"], r["BAlt"], r["CRt"]))
print("== RATE")
for r in win("RATE"):
    print("%.3f %s" % (T(r), {k: round(r[k],3) for k in ["RDes","R","ROut","PDes","P","POut","YDes","Y","YOut"]}))
print("== POWR")
for r in win("POWR"):
    print("%.3f %s" % (T(r), {k: r.get(k) for k in ["Vcc","VServo","Flags","AccFlags","Safety"]}))
for tip in ["EV","ERR","MODE","ARM","MSG"]:
    for r in win(tip):
        print("%.3f %s %s" % (T(r), tip, {k:v for k,v in r.items() if k!="TimeUS"}))
