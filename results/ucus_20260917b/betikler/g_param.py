import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
p={}
for x in d["PARM"]:
    p[x["Name"]]=x["Value"]
keys=[k for k in sorted(p) if k.startswith(("COMPASS_","EK3_SRC","EK3_MAG","EK3_YAW","EK3_PRIMARY","EK3_IMU_MASK","EK3_AFFINITY","MOT_","ATC_RAT_YAW","ATC_ANG_YAW","ATC_ACCEL_Y","ATC_SLEW_YAW","ATC_THR_MIX","GPS_TYPE","GPS_AUTO","GPS1_","GPS_DRV","BRD_","FS_","RC_OPTIONS","RC_PROTOCOLS","BATT_MONITOR","BATT_CURR","BATT_AMP","BATT_VOLT","BATT_SERIAL","LOG_","SCHED_LOOP","INS_GYRO_FILTER","INS_ACCEL_FILTER","SERIAL3","SERIAL4","CAN_","NTF_","FRAME","PILOT_Y","ATC_INPUT","EK3_CHECK","FS_EKF","ARMING_CHECK","INS_USE","AHRS_EKF"))]
for k in keys: print(k, round(p[k],5))
# param changes during log
from collections import defaultdict
h=defaultdict(list)
for x in d["PARM"]:
    h[x["Name"]].append((round(x["TimeUS"]/1e6,2), x["Value"]))
ch={k:v for k,v in h.items() if len(set(val for _,val in v))>1}
print("LOG ICINDE DEGISEN PARAMETRELER:", ch)
