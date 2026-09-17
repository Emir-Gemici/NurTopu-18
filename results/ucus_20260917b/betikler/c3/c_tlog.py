import sys, datetime
from collections import Counter
from pymavlink import mavutil
m=mavutil.mavlink_connection(sys.argv[1], dialect="ardupilotmega")
say=Counter(); ilk=None; son=None; arm_prev=None
servo_max=[0]*8; cur_max=0
while True:
    x=m.recv_match()
    if x is None: break
    t=getattr(x,'_timestamp',None)
    if t:
        if ilk is None: ilk=t
        son=t
    tp=x.get_type(); say[tp]+=1
    ts=datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S') if t else '-'
    if tp in ('COMMAND_LONG','COMMAND_ACK','PARAM_SET','STATUSTEXT','SET_MODE','COMMAND_INT','MAG_CAL_REPORT','MAG_CAL_PROGRESS'):
        if tp=='MAG_CAL_PROGRESS' and say[tp]>3: continue
        print(ts, tp, x.to_dict())
    if tp=='HEARTBEAT' and x.get_srcComponent()==1 and x.type!=6:
        a=bool(x.base_mode & 128)
        if a!=arm_prev: print(ts,'HEARTBEAT armed=',a,'custom_mode',x.custom_mode); arm_prev=a
    if tp=='SERVO_OUTPUT_RAW':
        for i in range(8):
            servo_max[i]=max(servo_max[i], getattr(x,'servo%d_raw'%(i+1)))
    if tp=='SYS_STATUS': cur_max=max(cur_max,x.current_battery)
print('sure', datetime.datetime.fromtimestamp(ilk), datetime.datetime.fromtimestamp(son))
print('servo_max', servo_max, 'akim max cA', cur_max)
print(dict(say.most_common(40)))
