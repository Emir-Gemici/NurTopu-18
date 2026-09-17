import pickle
v = pickle.load(open("tum.pkl","rb"))
for k in ["IMU","CTUN","BARO","PSCN","PSCE","PSCD","POS","GPS","RCIN","ATT","RATE","XKF1","XKF4","MOTB","CTRL","VIBE","AHR2","RCOU","BAT","MAG","XKF2","XKF3","XKFS"]:
    print(k, v[k][0])
