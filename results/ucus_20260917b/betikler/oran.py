import pickle
v = pickle.load(open("tum.pkl","rb"))
for k in ["IMU","RCIN","ATT","RATE","RCOU","CTUN","PSCN","XKF1","POS","GPS","BARO","VIBE","MAG"]:
    L = [t for t,d in v[k] if 190<=t<=202 and d.get("I",0)==0 and d.get("C",0)==0 and d.get("IMU",0)==0]
    dt = [b-a for a,b in zip(L,L[1:])]
    print(k, len(L), "ort dt", round(sum(dt)/len(dt),4) if dt else None, "min", round(min(dt),4) if dt else None, "max", round(max(dt),4) if dt else None)
