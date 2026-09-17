import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def win(tp,a,b): return [x for x in d[tp] if a<=x["TimeUS"]/1e6<=b]
def st(v):
    if not v: return "yok"
    v=sorted(v); n=len(v)
    return f"n={n} min={v[0]:.3f} med={v[n//2]:.3f} max={v[-1]:.3f} ort={sum(v)/n:.3f}"
W=[("L1 66.0-80.2 (NL 75.53)",75.6,79.9),("L2 134.2-150.7 (NL 140.87, LAND 147.6)",140.9,147.5),("SON 188.3-202.37",188.4,202.37),("SON erken 188.4-195",188.4,195.0),("SON gec 195-202.37",195.0,202.37)]
for ad,a,b in W:
    print("=====",ad)
    r=win("RATE",a,b); m=win("MOTB",a,b); o=win("RCOU",a,b); at=win("ATT",a,b); c=win("CTUN",a,b)
    print(" YDes",st([x["YDes"] for x in r])); print(" Y",st([x["Y"] for x in r])); print(" YOut",st([x["YOut"] for x in r]))
    print(" |YDes-Y|",st([abs(x["YDes"]-x["Y"]) for x in r]))
    print(" ROut",st([x["ROut"] for x in r])); print(" POut",st([x["POut"] for x in r]))
    print(" |RDes-R|",st([abs(x["RDes"]-x["R"]) for x in r])); print(" |PDes-P|",st([abs(x["PDes"]-x["P"]) for x in r]))
    def ye(x):
        e=(x["DesYaw"]-x["Yaw"]+540)%360-180; return e
    print(" yaw hata (Des-Gercek) deg",st([ye(x) for x in at]))
    print(" MOTB ThrOut",st([x["ThrOut"] for x in m])," ThrAvMx",st([x["ThrAvMx"] for x in m]))
    print(" MOTB FailFlags kume",sorted(set(x["FailFlags"] for x in m))," LiftMax",sorted(set(round(x["LiftMax"],3) for x in m))," ThLimit",sorted(set(round(x["ThLimit"],3) for x in m)), " BatVolt", st([x["BatVolt"] for x in m]))
    for k,ad2 in (("C11","M1 on-sag CCW"),("C10","M2 arka-sol CCW"),("C12","M3 on-sol CW"),("C9","M4 arka-sag CW")):
        print(f" {k} {ad2}",st([x[k] for x in o]))
    Y=[(x["C11"]+x["C10"]-x["C12"]-x["C9"])/4 for x in o]
    R=[(x["C10"]+x["C12"]-x["C11"]-x["C9"])/4 for x in o]
    P=[(x["C11"]+x["C12"]-x["C10"]-x["C9"])/4 for x in o]
    print(" PWM ayrisimi Y=(M1+M2-M3-M4)/4",st(Y)); print(" R=(M2+M3-M1-M4)/4 (sol-sag)",st(R)); print(" P=(M1+M3-M2-M4)/4 (on-arka)",st(P))
    print(" spread max-min",st([max(x["C9"],x["C10"],x["C11"],x["C12"])-min(x["C9"],x["C10"],x["C11"],x["C12"]) for x in o]))
    print(" min motor<=1160 orani", sum(1 for x in o if min(x["C9"],x["C10"],x["C11"],x["C12"])<=1160)/max(1,len(o)), " max motor>=1940 orani", sum(1 for x in o if max(x["C9"],x["C10"],x["C11"],x["C12"])>=1940)/max(1,len(o)))
    cr=win("CTRL",a,b)
    print(" CTRL RMSYaw",st([x["RMSYaw"] for x in cr])," RMSRollP",st([x["RMSRollP"] for x in cr]))
