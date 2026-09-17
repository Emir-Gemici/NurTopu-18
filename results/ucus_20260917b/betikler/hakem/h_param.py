from h_ortak import *
import re
for ad in ("hb.pkl","ha.pkl"):
    v=yukle(ad); P=parm(v)
    print("==",ad)
    print("SERVOx_FUNCTION:", {k:P[k] for k in sorted([k for k in P if re.match(r"SERVO\d+_FUNCTION$",k)], key=lambda s:int(re.findall(r"\d+",s)[0]))})
    print("SERVOx_MIN/MAX 1-12:", [(i,P.get(f"SERVO{i}_MIN"),P.get(f"SERVO{i}_MAX")) for i in range(1,13)])
    for k in ["MOT_PWM_MIN","MOT_PWM_MAX","MOT_PWM_TYPE","MOT_SPIN_MIN","MOT_SPIN_MAX","MOT_THST_EXPO","MOT_THST_HOVER","MOT_SLEW_UP_TIME","MOT_SLEW_DN_TIME","MOT_BAT_VOLT_MAX","BRD_PWM_COUNT","SERVO_RATE","ATC_RAT_YAW_P","ATC_RAT_YAW_I","ATC_RAT_YAW_IMAX","ATC_RAT_YAW_FLTE","ATC_RAT_RLL_P","ATC_RAT_RLL_I","ATC_RAT_RLL_D","ATC_RAT_PIT_P","ATC_RAT_PIT_I","ATC_RAT_PIT_D","ATC_ANG_YAW_P","INS_GYRO_FILTER","INS_ACCEL_FILTER","INS_POS1_X","INS_POS1_Y","INS_POS1_Z","INS_HNTCH_ENABLE","BATT_AMP_PERVLT","BATT_AMP_OFFSET","FS_CRASH_CHECK","COMPASS_MOT_X","ANGLE_MAX","PILOT_Y_RATE","LOIT_SPEED","ATC_THR_MIX_MAN","ATC_THR_MIX_MAX","MOT_YAW_HEADROOM","SERVO_BLH_MASK","SERVO_DSHOT_ESC"]:
        print(k, P.get(k))
    # fark
d1=parm(yukle("ha.pkl")); d2=parm(yukle("hb.pkl"))
fark=[(k,d1.get(k),d2.get(k)) for k in sorted(set(d1)|set(d2)) if d1.get(k)!=d2.get(k)]
print("PARAM FARKI a->b n=",len(fark)); print(fark)
