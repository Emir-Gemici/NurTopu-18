import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
a,b = float(sys.argv[1]), float(sys.argv[2])
tips = sys.argv[3].split(",")
rows=[]
for tp in tips:
    for x in d.get(tp,[]):
        t=x["TimeUS"]/1e6
        if a<=t<=b:
            y={k:v for k,v in x.items() if k!="TimeUS"}
            if tp=="IMU":
                y={k:(round(math.degrees(v)) if k.startswith("Gyr") else (round(v,1) if isinstance(v,float) else v)) for k,v in y.items() if k in ("I","GyrX","GyrY","GyrZ","AccX","AccY","AccZ","EG","EA","T","GH","AH")}
            else:
                y={k:(round(v,3) if isinstance(v,float) else v) for k,v in y.items()}
            rows.append((t,tp,y))
rows.sort(key=lambda r:(r[0],r[1]))
for t,tp,y in rows: print(f"{t:.3f} {tp} {y}")
