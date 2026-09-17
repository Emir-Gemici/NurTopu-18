import pickle, math
v = pickle.load(open("tum.pkl","rb"))
print([ (round(t,3), d) for t,d in v["GPS"] if t>202.42])
# GPS bosluklari (>0.5 s) tum log boyunca
g=[t for t,d in v["GPS"]]
print("GPS >0.5 s bosluklar:", [(round(a,2),round(b,2)) for a,b in zip(g,g[1:]) if b-a>0.5])
# MAG I0 bayat S: log zamani - S > 0.15 s
st=[(round(t,2), round(t-d['S']/1e6,3)) for t,d in v["MAG"] if d['I']==0 and t-d['S']/1e6>0.15]
print("MAG0 bayat ilk/son:", st[:3], st[-3:], "adet", len(st))
# IMU hata sayaclari
print("IMU EG/EA max:", max(d['EG'] for t,d in v['IMU']), max(d['EA'] for t,d in v['IMU']), "GH/AH min", min(d['GH'] for t,d in v['IMU']), min(d['AH'] for t,d in v['IMU']))
# RCOU 203.0-204.1 ve BAT
for t,d in v["RCOU"]:
    if 202.95<=t<=204.2: print(f"  RCOU {t:.3f} M4 {d['C9']} M2 {d['C10']} M1 {d['C11']} M3 {d['C12']}")
