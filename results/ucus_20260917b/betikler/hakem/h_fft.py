from h_ortak import *
import numpy as np, math
def analiz(ad,pp,a,b):
    v=yukle(pp)
    I=[d for d in pen(v,"IMU",a,b) if d["I"]==0]
    t=np.array([d["t"] for d in I]); 
    out=[ad,f"{a}-{b}",f"n={len(I)}"]
    for k in ("GyrX","GyrY","GyrZ"):
        x=np.array([d[k] for d in I]); x=x-x.mean()
        # duzgun ornekleme varsay (40 ms); hann
        w=np.hanning(len(x)); X=np.abs(np.fft.rfft(x*w))*2/np.sum(w); f=np.fft.rfftfreq(len(x),0.04)
        m=(f>=1.0)&(f<=12.4); i=np.argmax(X*m)
        rms=math.degrees(np.sqrt(np.mean(x**2)))
        # bant enerjisi 2-6 Hz
        P=np.abs(np.fft.rfft(x))**2; e26=P[(f>=2)&(f<=6)].sum()/P[f>0.2].sum()
        out.append(f"{k}: rms {rms:5.1f} deg/s, tepe {f[i]:4.2f} Hz {math.degrees(X[i]):5.1f} deg/s, 2-6Hz payi {e26:.2f}")
    R=pen(v,"RATE",a,b)
    out.append("RATE rms(RDes-R) %.1f rms(PDes-P) %.1f |ROut| %.3f |POut| %.3f"%(np.sqrt(np.mean([(d['RDes']-d['R'])**2 for d in R])),np.sqrt(np.mean([(d['PDes']-d['P'])**2 for d in R])),np.mean([abs(d['ROut']) for d in R]),np.mean([abs(d['POut']) for d in R])))
    print("\n  ".join(out))
#analiz("00:20 u3 aski","ha.pkl",624,643)
#analiz("02:50 W5","hb.pkl",141.5,147.5)
#analiz("02:50 W6a","hb.pkl",189.5,194.4)
#analiz("02:50 W6b (cubuk ortada)","hb.pkl",195,199.3)
