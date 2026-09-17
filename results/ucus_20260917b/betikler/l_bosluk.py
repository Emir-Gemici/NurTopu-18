import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
for tp,filt in [("IMU",lambda x:x["I"]==0),("IMU",lambda x:x["I"]==1),("ATT",None),("RATE",None),("RCOU",None),("MOTB",None),("CTUN",None),("BARO",None),("BAT",None),("POWR",None),("XKF1",lambda x:x["C"]==0),("XKF4",lambda x:x["C"]==0),("MAG",lambda x:x["I"]==1),("VIBE",lambda x:x["IMU"]==0),("RCIN",None),("PSCN",None),("GPS",None)]:
    ts=[x["TimeUS"]/1e6 for x in d[tp] if (filt is None or filt(x))]
    def mx(a,b):
        s=[t for t in ts if a<=t<=b]
        if len(s)<2: return None
        dt=[(s[i+1]-s[i], s[i]) for i in range(len(s)-1)]
        m=max(dt); mn=min(dt)
        return f"n={len(s)} dtmin={mn[0]*1000:.0f}ms dtmax={m[0]*1000:.0f}ms @{m[1]:.3f}"
    print(f"{tp:5s} 188.4-202.3: {mx(188.4,202.3)} | 202.3-204.2: {mx(202.3,204.2)}")
print("DSF fmt", L["fmt"]["DSF"])
for x in d["DSF"]:
    t=x["TimeUS"]/1e6
    if 180<=t<=219: print(" DSF", round(t,2), {k:v for k,v in x.items() if k!="TimeUS"})
print("PM fmt", L["fmt"]["PM"])
for x in d["PM"]:
    print(" PM", round(x["TimeUS"]/1e6,2), {k:v for k,v in x.items() if k!="TimeUS"})
# global seq check: any big TimeUS jump in all messages in 202-204.2
seq=[s for s in L["seq"] if s[2] is not None and 201.0e6<=s[2]<=204.2e6]
seq_sorted=sorted(s[2] for s in seq)
gaps=[(seq_sorted[i+1]-seq_sorted[i])/1e3 for i in range(len(seq_sorted)-1)]
print("tum mesajlar 201-204.2 ardisik TimeUS en buyuk bosluk ms:", max(gaps))
# out-of-order timestamps in file order
oo=0; last=0
for s in seq:
    if s[2]<last-50000: oo+=1
    last=max(last,s[2])
print("dosya sirasinda 50ms'den buyuk geri giden TimeUS sayisi:", oo)
