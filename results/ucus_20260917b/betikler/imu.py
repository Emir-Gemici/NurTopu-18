import pickle, math, sys
v = pickle.load(open("tum.pkl","rb"))
a,b = float(sys.argv[1]), float(sys.argv[2])
rows = {}
for t,d in v["IMU"]:
    if a<=t<=b:
        rows.setdefault(d["I"], []).append((t,d))
for I in sorted(rows):
    print("IMU", I)
    for t,d in rows[I]:
        gx,gy,gz = (math.degrees(d[k]) for k in ("GyrX","GyrY","GyrZ"))
        ax,ay,az = d["AccX"],d["AccY"],d["AccZ"]
        print(f"  {t:.3f} gx {gx:7.1f} gy {gy:7.1f} gz {gz:7.1f} | ax {ax:6.1f} ay {ay:6.1f} az {az:6.1f} |a| {math.sqrt(ax*ax+ay*ay+az*az):5.1f} axy {math.hypot(ax,ay):5.1f} EG {d['EG']} EA {d['EA']} GH {d['GH']} AH {d['AH']}")
