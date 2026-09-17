import sys, math, pickle
from pymavlink import mavutil
yol = r"O:\navitas\results\ucus_20260917b\2026-09-17 02-50-38.bin"
m = mavutil.mavlink_connection(yol, dialect="ardupilotmega")
P = {}
while True:
    x = m.recv_match(type=["PARM"])
    if x is None: break
    P[x.Name] = x.Value
for k in sorted(P):
    if any(k.startswith(p) for p in ("INS_ACCEL_FILTER","INS_GYRO_FILTER","FS_CRASH","THR_DZ","GPS_TYPE","GPS_AUTO","COMPASS_USE","COMPASS_EXTERN","COMPASS_ENABLE","COMPASS_TYPEMASK","LOIT_","ARMING_","DISARM","ATC_RAT_RLL_I","ATC_RAT_RLL_D","ATC_RAT_PIT_D","ATC_RAT_PIT_I","MOT_PWM","MOT_SPIN_MAX","MOT_THST_EXPO","BATT_AMP_OFFSET","BATT_MONITOR","RC5_","RC6_","RC1_DZ","RC2_DZ","RC4_DZ","LOG_BITMASK","SCHED_LOOP","INS_FAST","EK3_SRC1","EK3_MAG","AHRS_EKF")):
        print(k, P[k])
v = pickle.load(open("tum.pkl","rb"))
print("XKF4 C0 201.0-202.5:")
for t,d in v["XKF4"]:
    if 201.0<=t<=202.6 and d['C']==0: print(f"  {t:.3f} SV {d['SV']} SP {d['SP']} SH {d['SH']} SM {d['SM']} errRP {d['errRP']:.3f} FS {d['FS']} TS {d['TS']} SS {d['SS']} GPS {d['GPS']} PI {d['PI']}")
# yol uzunlugu
L=[(t,d) for t,d in v["PSCN"] if 188.3<=t<=202.38]; E=[(t,d) for t,d in v["PSCE"] if 188.3<=t<=202.38]
s=0; 
for (a,da),(b,db),(c,ea),(e,eb) in zip(L,L[1:],E,E[1:]):
    s+=math.hypot(db['PN']-da['PN'], eb['PE']-ea['PE'])
print("188.3-202.37 PSC konum yol uzunlugu m", round(s,2))
for w in [(192.37,202.38)]:
    L=[(t,d) for t,d in v["PSCN"] if w[0]<=t<=w[1]]; E=[(t,d) for t,d in v["PSCE"] if w[0]<=t<=w[1]]
    s=sum(math.hypot(db['PN']-da['PN'], eb['PE']-ea['PE']) for (a,da),(b,db),(c,ea),(e,eb) in zip(L,L[1:],E,E[1:]))
    pn=[d['PN'] for _,d in L]; pe=[d['PE'] for _,d in E]
    d0=[math.hypot(a+6.65,b+13.53) for a,b in zip(pn,pe)]
    print("son 10 s yol", round(s,2), "kalkis noktasina maks uzaklik", round(max(d0),2), "son", round(d0[-1],2))
# govde eksenli hiz 202.37 (yaw ~299.4)
for tt in (201.0, 201.5, 202.07, 202.37):
    n=[d for t,d in v["PSCN"] if t<=tt+0.001][-1]; e=[d for t,d in v["PSCE"] if t<=tt+0.001][-1]; a=[d for t,d in v["ATT"] if t<=tt+0.001][-1]
    y=math.radians(a['Yaw']); fwd = n['VN']*math.cos(y)+e['VE']*math.sin(y); rgt = -n['VN']*math.sin(y)+e['VE']*math.cos(y)
    print(f"t {tt} yaw {a['Yaw']:.1f} ileri {fwd:.2f} sag {rgt:.2f} m/s")
