# Curutucu 2: istatistik ve karsilastirmalar
import pickle, math
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
B = pickle.load(open(S+"c2_b.pkl","rb")); A = pickle.load(open(S+"c2_a.pkl","rb"))
def T(r): return r["TimeUS"]/1e6
def win(P, tip, t0, t1, **flt):
    out = []
    for r in P["d"].get(tip, []):
        if t0 <= T(r) <= t1 and all(r.get(k)==v for k,v in flt.items()):
            out.append(r)
    return out
def col(rs, k): return np.array([r[k] for r in rs], float)

print("== param farklari (A=00:20, B=02:50)")
ka = set(A["parm"]); kb = set(B["parm"])
fark = [(k, A["parm"].get(k), B["parm"].get(k)) for k in sorted(ka|kb) if A["parm"].get(k) != B["parm"].get(k)]
print(len(fark))
for f in fark: print("  ", f)

def askı(P, ad, t0, t1):
    c = win(P,"CTUN",t0,t1); b = win(P,"BAT",t0,t1); r = win(P,"RATE",t0,t1); rc = win(P,"RCOU",t0,t1); ri = win(P,"RCIN",t0,t1)
    print("--", ad, t0, t1, "nCTUN", len(c))
    print("   ThO ort %.3f  ThH %.4f  Alt %.2f..%.2f" % (col(c,"ThO").mean(), col(c,"ThH").mean(), col(c,"Alt").min(), col(c,"Alt").max()))
    print("   BAT V %.2f I %.1f" % (col(b,"Volt").mean(), col(b,"Curr").mean()))
    for i in (0,1):
        v = win(P,"VIBE",t0,t1,IMU=i)
        print("   VIBE%d X %.1f Y %.1f Z %.1f Clip %d..%d" % (i, col(v,"VibeX").mean(), col(v,"VibeY").mean(), col(v,"VibeZ").mean(), col(v,"Clip").min(), col(v,"Clip").max()))
        im = win(P,"IMU",t0,t1,I=i)
        gx = np.degrees(col(im,"GyrX")); gy = np.degrees(col(im,"GyrY")); gz = np.degrees(col(im,"GyrZ"))
        tt = col(im,"TimeUS")/1e6
        dt = np.diff(tt)
        print("   IMU%d n %d dt_med %.4f  GyrX rms %.1f (std %.1f, ort %.2f)  GyrY rms %.1f (std %.1f)  GyrZ ort %.2f std %.1f" % (i, len(im), np.median(dt), np.sqrt((gx**2).mean()), gx.std(), gx.mean(), np.sqrt((gy**2).mean()), gy.std(), gz.mean(), gz.std()))
        if i == 0 and len(gx) > 16:
            x = gx - gx.mean(); n = len(x); w = np.hanning(n)
            F = np.abs(np.fft.rfft(x*w)); f = np.fft.rfftfreq(n, np.median(dt))
            j = np.argmax(F[1:])+1
            amp = 2*F[j]/w.sum()
            print("   IMU0 GyrX FFT tepe %.2f Hz genlik %.1f deg/s" % (f[j], amp))
    er = col(r,"RDes")-col(r,"R"); ep = col(r,"PDes")-col(r,"P")
    print("   RATE hata rms roll %.1f pitch %.1f  |ROut| ort %.3f |POut| %.3f  R rms %.1f  RDes rms %.1f" % (np.sqrt((er**2).mean()), np.sqrt((ep**2).mean()), np.abs(col(r,"ROut")).mean(), np.abs(col(r,"POut")).mean(), np.sqrt((col(r,"R")**2).mean()), np.sqrt((col(r,"RDes")**2).mean())))
    M1,M2,M3,M4 = col(rc,"C11"),col(rc,"C10"),col(rc,"C12"),col(rc,"C9")
    print("   RCOU ort M1 %.0f M2 %.0f M3 %.0f M4 %.0f  CCW-CW ort %+.0f  yayilim(ort) %.0f  anlik yayilim ort %.0f" % (M1.mean(),M2.mean(),M3.mean(),M4.mean(), (M1+M2-M3-M4).mean(), max(M1.mean(),M2.mean(),M3.mean(),M4.mean())-min(M1.mean(),M2.mean(),M3.mean(),M4.mean()), (np.max([M1,M2,M3,M4],0)-np.min([M1,M2,M3,M4],0)).mean()))
    print("   RCIN C1 %d..%d C2 %d..%d C3 %d..%d C4 %d..%d C5 %s" % (col(ri,"C1").min(),col(ri,"C1").max(),col(ri,"C2").min(),col(ri,"C2").max(),col(ri,"C3").min(),col(ri,"C3").max(),col(ri,"C4").min(),col(ri,"C4").max(), sorted(set(col(ri,"C5")))))
    mo = win(P,"MODE",0,t1)
    print("   son mod", mo[-1] if mo else None)

askı(B, "02:50 W5", 143.9, 146.9)
askı(A, "00:20 temiz", 639.1, 642.5)
askı(B, "02:50 son ucus 196.4-198.4", 196.4, 198.4)
askı(B, "02:50 son ucus 201.4-202.37", 201.4, 202.37)
