import pickle, math
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def st(v):
    v=sorted(v); n=len(v); 
    import statistics
    return f"n={n} min={v[0]:.1f} p1={v[int(n*0.01)]:.1f} med={v[n//2]:.1f} p99={v[int(n*0.99)]:.1f} max={v[-1]:.1f} sd={statistics.pstdev(v):.1f}"
im=[x for x in d["IMU"] if 190.0<=x["TimeUS"]/1e6<=202.30 and x["I"]==0]
for k in ("GyrX","GyrY","GyrZ"):
    print("IMU0 190-202.30",k,"deg/s",st([math.degrees(x[k]) for x in im]))
for k in ("AccX","AccY","AccZ"):
    print("IMU0 190-202.30",k,"m/s2",st([x[k] for x in im]))
r=[x for x in d["RATE"] if 190.0<=x["TimeUS"]/1e6<=202.30]
print("RATE Y 190-202.30", st([x["Y"] for x in r]))
# samples with |GyrZ|>=20
print("IMU0 |GyrZ|>=15 ornekleri 188.4-202.45:", [(round(x["TimeUS"]/1e6,2), round(math.degrees(x["GyrZ"]))) for x in d["IMU"] if x["I"]==0 and 188.4<=x["TimeUS"]/1e6<=202.45 and abs(math.degrees(x["GyrZ"]))>=15])
print("IMU0 AccZ > -7 ornekleri 188.4-202.45:", [(round(x["TimeUS"]/1e6,2), round(x["AccZ"],1)) for x in d["IMU"] if x["I"]==0 and 188.4<=x["TimeUS"]/1e6<=202.45 and x["AccZ"]>-7])
print("IMU0 |GyrX| veya |GyrY| >=40 ornekleri 188.4-202.45:", [(round(x["TimeUS"]/1e6,2), round(math.degrees(x["GyrX"])), round(math.degrees(x["GyrY"]))) for x in d["IMU"] if x["I"]==0 and 188.4<=x["TimeUS"]/1e6<=202.45 and max(abs(math.degrees(x["GyrX"])),abs(math.degrees(x["GyrY"])))>=40])
# IMU health flags / error counts
print("IMU EG/EA/GH/AH kume 181-219:", sorted(set((x["I"],x["EG"],x["EA"],x["GH"],x["AH"]) for x in d["IMU"] if 181<=x["TimeUS"]/1e6<=219)))
print("IMU T sicaklik 181-219 I0:", st([x["T"] for x in d["IMU"] if x["I"]==0 and 181<=x["TimeUS"]/1e6<=219]))
