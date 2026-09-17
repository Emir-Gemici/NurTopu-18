import sys, datetime, math
from pymavlink import mavutil
m=mavutil.mavlink_connection(sys.argv[1], dialect="ardupilotmega")
last=0
while True:
    x=m.recv_match(type=['ATTITUDE','VIBRATION','SYS_STATUS','SERVO_OUTPUT_RAW','HEARTBEAT'])
    if x is None: break
    t=x._timestamp; ts=datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S')
    tp=x.get_type()
    if tp=='ATTITUDE' and t-last>60:
        print(ts,'ATT roll %.1f pitch %.1f yaw %.1f'%(math.degrees(x.roll),math.degrees(x.pitch),math.degrees(x.yaw))); last=t
    if '00:45:2'<=ts<='00:45:59' and tp in ('VIBRATION','SYS_STATUS','SERVO_OUTPUT_RAW'):
        d=x.to_dict(); print(ts,tp,{k:d[k] for k in d if k in ('vibration_x','vibration_y','vibration_z','clipping_0','current_battery','voltage_battery','servo1_raw','servo9_raw','servo10_raw','servo11_raw','servo12_raw')})
