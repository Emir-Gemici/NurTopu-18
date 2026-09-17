from c_ort import *
v=yukle(); p=P(v)
import re
for k in sorted(p):
    if re.match(r"(RC[1-6]_(REVERSED|MIN|MAX|TRIM|DZ)|ATC_|MOT_|INS_(ACC|GYR|POS|FAST|HNTCH|LOG)|BATT_(AMP|VOLT|CURR|MONITOR)|AHRS_ORIENT|LOIT_|PSC_|SERVO(9|10|11|12)_|FS_CRASH|CRASH|LOG_BIT|SCHED_LOOP|INS_RAW|GPS_POS|EK3_SRC|RNGFND1_TYPE|PILOT_)",k):
        print(k,p[k])
