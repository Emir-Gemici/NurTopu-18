import pickle, math
v = pickle.load(open("tum.pkl","rb"))
def qmul(a,b):
    w1,x1,y1,z1=a; w2,x2,y2,z2=b
    return (w1*w2-x1*x2-y1*y2-z1*z2, w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2)
def euler2q(r,p,y):
    cr,sr=math.cos(r/2),math.sin(r/2); cp,sp=math.cos(p/2),math.sin(p/2); cy,sy=math.cos(y/2),math.sin(y/2)
    return (cr*cp*cy+sr*sp*sy, sr*cp*cy-cr*sp*sy, cr*sp*cy+sr*cp*sy, cr*cp*sy-sr*sp*cy)
a=[d for t,d in v["ATT"] if t<=202.371][-1]
q=euler2q(math.radians(a['Roll']),math.radians(a['Pitch']),math.radians(a['Yaw']))
L=[(t,d) for t,d in v["IMU"] if d['I']==0 and 202.36<=t<=203.0]
prev=L[0][0]
for t,d in L[1:]:
    dt=t-prev; prev=t
    w=(d['GyrX'],d['GyrY'],d['GyrZ']); n=math.sqrt(sum(x*x for x in w))
    if n>0:
        h=n*dt/2; s=math.sin(h)/n
        q=qmul(q,(math.cos(h),w[0]*s,w[1]*s,w[2]*s))
    w0,x,y,z=q
    # body z ekseninin dunya z ile acisi (egim)
    bz_z = 1-2*(x*x+y*y)
    tilt=math.degrees(math.acos(max(-1,min(1,bz_z))))
    att=[dd for tt,dd in v["ATT"] if tt<=t+0.001][-1]
    print(f"{t:.3f} egim(jiro entegre) {tilt:6.1f} deg | ATT R {att['Roll']:.1f} P {att['Pitch']:.1f}")
