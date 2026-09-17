# Curutucu 2: GyrX spektrum tepeleri (IMU0, 25 Hz)
import pickle
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
def fft(fn, a, b, ad):
    d = pickle.load(open(S+fn,"rb"))["d"]; T = lambda r: r["TimeUS"]/1e6
    im = [r for r in d["IMU"] if r["I"]==0 and a<=T(r)<=b]
    for eks in ("GyrX","GyrY"):
        x = np.degrees([r[eks] for r in im]); x = x - x.mean(); n = len(x); w = np.hanning(n)
        F = 2*np.abs(np.fft.rfft(x*w))/w.sum(); f = np.fft.rfftfreq(n, 0.04)
        top = np.argsort(F[1:])[::-1][:3]+1
        print("%-30s %s n%d tepeler: %s  | 5-8 Hz bandi en yuksek %.1f" % (ad, eks, n, ", ".join("%.2f Hz %.1f" % (f[i], F[i]) for i in top), F[(f>=5)&(f<=8)].max()))
fft("c2_a.pkl", 639.1, 642.5, "00:20 1.6 m AGL")
fft("c2_a.pkl", 622.3, 623.9, "00:20 yere yakin")
fft("c2_b.pkl", 143.9, 146.9, "02:50 W5 0.45 m")
fft("c2_b.pkl", 141.2, 142.8, "02:50 W5 kalkis")
fft("c2_b.pkl", 190.5, 202.30, "02:50 son ucus")
