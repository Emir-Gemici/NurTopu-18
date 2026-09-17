# Curutucu 2: askı karsilastirmasi yere yukseklik (AGL) eslesmeli
import pickle
import numpy as np
S = r"C:/Users/yunus/AppData/Local/Temp/claude/O--navitas/3e104177-9b44-4ec7-a18f-1f32ed2c3f72/scratchpad/wf_0250/cur2/"
def ozet(fn, zemin_penc, penc, ad):
    d = pickle.load(open(S+fn,"rb"))["d"]; T = lambda r: r["TimeUS"]/1e6
    W = lambda tip,a,b,**f: [r for r in d[tip] if a<=T(r)<=b and all(r.get(k)==v for k,v in f.items())]
    z = np.mean([r["Alt"] for r in W("CTUN",*zemin_penc)])
    c = W("CTUN",*penc); b = W("BAT",*penc); v = W("VIBE",*penc,IMU=0); im = W("IMU",*penc,I=0); rc = W("RCOU",*penc)
    alt = np.array([r["Alt"] for r in c]); crt = np.array([r["CRt"] for r in c])
    gx = np.degrees([r["GyrX"] for r in im]); gy = np.degrees([r["GyrY"] for r in im])
    pwm = np.mean([[r["C9"],r["C10"],r["C11"],r["C12"]] for r in rc])
    print("%-28s zemin Alt %.2f | AGL %.2f..%.2f | CRt %+.0f..%+.0f cm/s | ThO %.3f | PWM ort %.0f | V %.2f I %.1f | VibeX/Y/Z %.1f/%.1f/%.1f | GyrX std %.1f GyrY std %.1f | n_imu %d" % (
        ad, z, alt.min()-z, alt.max()-z, crt.min(), crt.max(), np.mean([r["ThO"] for r in c]), pwm,
        np.mean([r["Volt"] for r in b]), np.mean([r["Curr"] for r in b]),
        np.mean([r["VibeX"] for r in v]), np.mean([r["VibeY"] for r in v]), np.mean([r["VibeZ"] for r in v]), gx.std(), gy.std(), len(gx)))
ozet("c2_a.pkl", (612.0,619.0), (639.1,642.5), "00:20 sentez askisi")
ozet("c2_b.pkl", (134.0,139.0), (143.9,146.9), "02:50 W5 sentez askisi")
ozet("c2_a.pkl", (612.0,619.0), (622.3,623.9), "00:20 yere yakin (kalkis)")
ozet("c2_b.pkl", (134.0,139.0), (141.2,142.8), "02:50 W5 yere yakin (kalkis)")
ozet("c2_b.pkl", (181.7,187.5), (188.9,190.5), "02:50 son ucus yere yakin")
ozet("c2_b.pkl", (181.7,187.5), (190.5,194.3), "02:50 son ucus 190.5-194.3")
