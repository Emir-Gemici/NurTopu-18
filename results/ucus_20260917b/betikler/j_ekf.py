import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def st(v):
    v=sorted(v); n=len(v)
    return f"n={n} min={v[0]:.2f} med={v[n//2]:.2f} max={v[-1]:.2f}" if n else "yok"
W=[("SON askida 188.4-202.37",188.4,202.37),("son 1 s 201.37-202.37",201.37,202.37),("carpma 202.38-204.0",202.38,204.0),("L2 askida 140.9-147.5",140.9,147.5)]
for ad,a,b in W:
    print("==",ad)
    for C in (0,1):
        k4=[x for x in d["XKF4"] if a<=x["TimeUS"]/1e6<=b and x["C"]==C]
        k3=[x for x in d["XKF3"] if a<=x["TimeUS"]/1e6<=b and x["C"]==C]
        print(f" C{C} XKF4 SV",st([x["SV"] for x in k4]),"SP",st([x["SP"] for x in k4]),"SH",st([x["SH"] for x in k4]),"SM",st([x["SM"] for x in k4]),"SVT",st([x["SVT"] for x in k4]))
        print(f"    FS",sorted(set(x["FS"] for x in k4)),"TS",sorted(set(x["TS"] for x in k4)),"SS",sorted(set(x["SS"] for x in k4)),"GPS",sorted(set(x["GPS"] for x in k4)),"PI",sorted(set(x["PI"] for x in k4)), "errRP", st([x["errRP"] for x in k4]))
        print(f"    XKF3 IVN",st([x["IVN"] for x in k3]),"IVE",st([x["IVE"] for x in k3]),"IVD",st([x["IVD"] for x in k3]),"IPD",st([x["IPD"] for x in k3]))
        print(f"    XKF3 IMX",st([x["IMX"] for x in k3]),"IMY",st([x["IMY"] for x in k3]),"IMZ",st([x["IMZ"] for x in k3]),"IYAW",st([x["IYAW"] for x in k3]),"ErSc",st([x["ErSc"] for x in k3]))
        ks=[x for x in d["XKFS"] if a<=x["TimeUS"]/1e6<=b and x["C"]==C]
        print(f"    XKFS MI",sorted(set(x["MI"] for x in ks)),"BI",sorted(set(x["BI"] for x in ks)),"GI",sorted(set(x["GI"] for x in ks)),"AI",sorted(set(x["AI"] for x in ks)),"SS",sorted(set(x["SS"] for x in ks)))
