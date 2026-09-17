import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def st(v):
    v=sorted(v); n=len(v)
    return f"n={n} min={v[0]} med={v[n//2]} max={v[-1]}" if n else "yok"
rc=[x for x in d["RCIN"] if 181.0<=x["TimeUS"]/1e6<=204.5]
for k in ["C1","C2","C3","C4","C5","C6","C7","C8","C9","C10","C11","C12","C13","C14"]:
    print(k, "181-202.37", st([x[k] for x in rc if x["TimeUS"]/1e6<=202.37]))
ts=[x["TimeUS"]/1e6 for x in d["RCIN"]]
dts=[(round(ts[i],3), round(ts[i+1]-ts[i],3)) for i in range(len(ts)-1)]
son=[dt for t,dt in dts if 181.7<=t<=204.0]
print("RCIN dt 181.7-204:", min(son), max(son))
print("RCIN tum log >0.15 s bosluklar:", [x for x in dts if x[1]>0.15])
# jumps >150 us in consecutive samples in last flight for C1..C6
for k in ["C1","C2","C3","C4","C5","C6"]:
    j=[(round(rc[i+1]["TimeUS"]/1e6,2), rc[i][k], rc[i+1][k]) for i in range(len(rc)-1) if abs(rc[i+1][k]-rc[i][k])>=100]
    print("sicrama>=100us", k, j[:30])
print("RCI2 fmt", L["fmt"].get("RCI2"))
r2=[x for x in d["RCI2"] if 181.0<=x["TimeUS"]/1e6<=219]
print("RCI2 Flags kume son ucus", sorted(set(x["Flags"] for x in r2)), "OMask", sorted(set(x["OMask"] for x in r2)), "C15", sorted(set(x["C15"] for x in r2)), "C16", sorted(set(x["C16"] for x in r2)))
print("RCI2 Flags kume tum", sorted(set(x["Flags"] for x in d["RCI2"])))
prev=None
for x in d["RCI2"]:
    if x["Flags"]!=prev: print(" RCI2 Flags degisim", round(x["TimeUS"]/1e6,3), x["Flags"]); prev=x["Flags"]
print("C3 gaz <= FS_THR_VALUE 975 ornek sayisi (tum):", sum(1 for x in d["RCIN"] if x["C3"]<=975))
io=d["IOMC"]
print("IOMC fmt", L["fmt"]["IOMC"])
for x in io:
    t=x["TimeUS"]/1e6
    if 175<=t<=219: print(round(t,2), {k:v for k,v in x.items() if k!="TimeUS"})
