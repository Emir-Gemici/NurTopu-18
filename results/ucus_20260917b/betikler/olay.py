import pickle, math, sys
v = pickle.load(open(sys.argv[1],"rb"))
a, b = float(sys.argv[2]), float(sys.argv[3])
rows = []
for tip in sys.argv[4].split(","):
    for d in v.get(tip, []):
        if a <= d["t"] <= b:
            rows.append((d["t"], tip, d))
rows.sort(key=lambda r: r[0])
def fmt(tip, d):
    if tip == "RCOU": return f"M4(C9)={d['C9']} M2(C10)={d['C10']} M1(C11)={d['C11']} M3(C12)={d['C12']}"
    if tip == "IMU": return f"I{d['I']} Gx={math.degrees(d['GyrX']):7.1f} Gy={math.degrees(d['GyrY']):7.1f} Gz={math.degrees(d['GyrZ']):7.1f} Ax={d['AccX']:6.2f} Ay={d['AccY']:6.2f} Az={d['AccZ']:6.2f} EG={d['EG']} EA={d['EA']}"
    if tip == "RATE": return " ".join(f"{k}={d[k]:.3f}" for k in ("RDes","R","ROut","PDes","P","POut","YDes","Y","YOut","ADes","A","AOut"))
    if tip == "ATT": return " ".join(f"{k}={d[k]:.2f}" for k in ("DesRoll","Roll","DesPitch","Pitch","DesYaw","Yaw","ErrRP","ErrYaw"))
    if tip == "BAT": return f"V={d['Volt']:.2f} VR={d['VoltR']:.2f} A={d['Curr']:.1f} Res={d['Res']:.4f}"
    if tip == "MOTB": return " ".join(f"{k}={d[k]:.3f}" for k in ("LiftMax","BatVolt","ThLimit","ThrAvMx","ThrOut","FailFlags"))
    if tip == "CTUN": return " ".join(f"{k}={d[k]:.2f}" for k in ("ThI","ThO","ThH","DAlt","Alt","BAlt","DCRt","CRt"))
    if tip == "VIBE": return f"IMU{d['IMU']} X={d['VibeX']:.1f} Y={d['VibeY']:.1f} Z={d['VibeZ']:.1f} Clip={d['Clip']}"
    if tip == "XKF1": return f"C{d['C']} R={d['Roll']:.1f} P={d['Pitch']:.1f} Y={d['Yaw']:.1f} VN={d['VN']:.2f} VE={d['VE']:.2f} VD={d['VD']:.2f} PD={d['PD']:.2f} GX={d['GX']:.2f} GY={d['GY']:.2f} GZ={d['GZ']:.2f}"
    if tip == "MAG": return f"I{d['I']} {d['MagX']} {d['MagY']} {d['MagZ']} H={d['Health']}"
    if tip == "RCIN": return " ".join(f"C{i}={d['C%d'%i]}" for i in range(1,7))
    d2 = {k: (round(x,3) if isinstance(x,float) else x) for k,x in d.items() if k not in ("TimeUS","t")}
    return str(d2)
for t, tip, d in rows:
    print(f"{t:8.3f} {tip:5} {fmt(tip,d)}")
