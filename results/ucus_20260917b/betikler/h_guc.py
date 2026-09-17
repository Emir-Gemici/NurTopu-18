import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def st(v):
    v=sorted(v); n=len(v)
    return f"n={n} min={v[0]:.3f} med={v[n//2]:.3f} max={v[-1]:.3f}" if n else "yok"
def win(tp,a,b,f=None): return [x for x in d[tp] if a<=x["TimeUS"]/1e6<=b and (f is None or f(x))]
W=[("tum",0,999),("SON arm yerde 181.7-188.3",181.7,188.3),("SON askida 188.4-202.37",188.4,202.37),("son 2 s 200.37-202.37",200.37,202.37),("carpma 202.38-204.0",202.38,204.0),("disarm sonrasi 204-219",204.0,219)]
for ad,a,b in W:
    print("==",ad)
    p=win("POWR",a,b); m=win("MCU",a,b); bt=win("BAT",a,b)
    print(" POWR Vcc",st([x["Vcc"] for x in p]),"| VServo",st([x["VServo"] for x in p]))
    print(" POWR Flags",sorted(set(x["Flags"] for x in p)),"AccFlags",sorted(set(x["AccFlags"] for x in p)),"Safety",sorted(set(x["Safety"] for x in p)))
    print(" MCU MTemp",st([x["MTemp"] for x in m]),"| MVolt",st([x["MVolt"] for x in m]),"| MVmin",st([x["MVmin"] for x in m]),"| MVmax",st([x["MVmax"] for x in m]))
    print(" BAT Volt",st([x["Volt"] for x in bt]),"| VoltR",st([x["VoltR"] for x in bt]),"| Curr",st([x["Curr"] for x in bt]),"| Res",st([x["Res"] for x in bt]))
    print(" BAT H/SH",sorted(set((x["H"],x["SH"]) for x in bt)))
# flag change times
prev=None
for x in d["POWR"]:
    k=(x["Flags"],x["AccFlags"],x["Safety"])
    if k!=prev: print("POWR degisim", round(x["TimeUS"]/1e6,3), k); prev=k
# BAT around impact
for x in win("BAT",201.9,204.2):
    print(f"{x['TimeUS']/1e6:.3f} BAT V{x['Volt']:.2f} VR{x['VoltR']:.2f} I{x['Curr']:.2f} CT{x['CurrTot']:.1f}")
for x in win("POWR",201.9,204.2):
    print(f"{x['TimeUS']/1e6:.3f} POWR Vcc{x['Vcc']:.3f} VS{x['VServo']:.3f} F{x['Flags']}")
for x in win("MCU",201.9,204.2):
    print(f"{x['TimeUS']/1e6:.3f} MCU T{x['MTemp']:.1f} V{x['MVolt']:.3f} min{x['MVmin']:.3f} max{x['MVmax']:.3f}")
print("AMP_PERVLT*3.3 =", 36.36*3.3)
print("Curr>=119.9 ornekleri", [round(x["TimeUS"]/1e6,2) for x in d["BAT"] if x["Curr"]>=119.9])
