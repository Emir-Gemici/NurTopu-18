import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
a,b,adim = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
def near(tp, t, filt=None):
    best=None; bd=9
    for x in d[tp]:
        if filt and not filt(x): continue
        dt=abs(x["TimeUS"]/1e6-t)
        if dt<bd: bd=dt; best=x
    return best
t=a
print("t | DesYaw Yaw err | YDes Y YOut | Alt DAlt BAlt CRt ThO | M1 M2 M3 M4 | Volt Curr | Vcc VServo | XKF1 VN VE VD | MAG0 MAG1 |B|")
import bisect
idx={tp:[x["TimeUS"]/1e6 for x in d[tp]] for tp in ("ATT","RATE","CTUN","RCOU","BAT","POWR","XKF1","MAG")}
def g(tp,t,f=None):
    xs=d[tp]; ts=idx[tp]; i=bisect.bisect_left(ts,t)
    cand=[j for j in range(max(0,i-4),min(len(xs),i+4)) if (f is None or f(xs[j]))]
    j=min(cand,key=lambda j:abs(ts[j]-t)); return xs[j]
while t<=b:
    A=g("ATT",t); R=g("RATE",t); C=g("CTUN",t); O=g("RCOU",t); B=g("BAT",t); P=g("POWR",t); K=g("XKF1",t,lambda x:x["C"]==0)
    M0=g("MAG",t,lambda x:x["I"]==0); M1=g("MAG",t,lambda x:x["I"]==1)
    e=(A["DesYaw"]-A["Yaw"]+540)%360-180
    bm=lambda x: math.sqrt(x["MagX"]**2+x["MagY"]**2+x["MagZ"]**2)
    print(f"{t:6.1f} | {A['DesYaw']:6.1f} {A['Yaw']:6.1f} {e:5.1f} | {R['YDes']:5.1f} {R['Y']:5.1f} {R['YOut']:5.2f} | {C['Alt']:5.2f} {C['DAlt']:5.2f} {C['BAlt']:5.2f} {C['CRt']:5.2f} {C['ThO']:4.2f} | {O['C11']} {O['C10']} {O['C12']} {O['C9']} | {B['Volt']:5.2f} {B['Curr']:5.1f} | {P['Vcc']:4.2f} {P['VServo']:4.2f} | {K['VN']:5.2f} {K['VE']:5.2f} {K['VD']:5.2f} | {bm(M0):4.0f} {bm(M1):4.0f}")
    t+=adim
