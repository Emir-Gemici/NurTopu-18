import sys
from pymavlink import mavutil
m=mavutil.mavlink_connection(sys.argv[1], dialect="ardupilotmega")
a,b=float(sys.argv[2]),float(sys.argv[3])
O=[];R=[];A=[]
while True:
    x=m.recv_match(type=["RCOU","RATE","ATT"])
    if x is None: break
    t=x.TimeUS/1e6
    if t<a: continue
    if t>b: break
    if x.get_type()=="RCOU": O.append(x)
    elif x.get_type()=="RATE": R.append(x)
    else: A.append(x)
def med(v): v=sorted(v); return v[len(v)//2]
print("n RCOU",len(O))
print("M1 C11",med([x.C11 for x in O]),"M2 C10",med([x.C10 for x in O]),"M3 C12",med([x.C12 for x in O]),"M4 C9",med([x.C9 for x in O]))
print("CCW-CW toplam fark (M1+M2-M3-M4) medyan",med([x.C11+x.C10-x.C12-x.C9 for x in O]))
print("YOut medyan",round(med([x.YOut for x in R]),3),"min",round(min(x.YOut for x in R),3),"max",round(max(x.YOut for x in R),3))
print("yaw hata medyan",round(med([((x.DesYaw-x.Yaw+540)%360-180) for x in A]),2))
