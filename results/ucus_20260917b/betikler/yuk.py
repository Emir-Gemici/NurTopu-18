import pickle, math
v = pickle.load(open("tum.pkl","rb"))
def ort(tip, a, b, f, **flt):
    xs=[d[f] for t,d in v[tip] if a<=t<=b and all(d.get(k)==x for k,x in flt.items())]
    if not xs: return None
    m=sum(xs)/len(xs); s=math.sqrt(sum((x-m)**2 for x in xs)/len(xs))
    return f"ort {m:.2f} std {s:.2f} min {min(xs):.2f} max {max(xs):.2f} n {len(xs)}"
for (a,b,ad) in [(181.7,188.2,"yerde arm, kalkis oncesi"),(186.0,188.2,"kalkis oncesi son 2 s"),(197.0,202.37,"olay oncesi askida 5.4 s"),(201.4,202.37,"olay oncesi son 1 s"),(204.2,206.0,"carpma sonrasi yerde (disarm sonrasi)"),(206,218,"yerde 206-218")]:
    print(ad, a, b)
    print("  BARO0 Alt", ort("BARO",a,b,"Alt",I=0))
    print("  BARO1 Alt", ort("BARO",a,b,"Alt",I=1))
    print("  CTUN Alt", ort("CTUN",a,b,"Alt"))
    print("  CTUN BAlt", ort("CTUN",a,b,"BAlt"))
    print("  XKF1 C0 PD", ort("XKF1",a,b,"PD",C=0))
    print("  XKF1 C1 PD", ort("XKF1",a,b,"PD",C=1))
    print("  POS RelHomeAlt", ort("POS",a,b,"RelHomeAlt"))
    print("  GPS Alt", ort("GPS",a,b,"Alt",I=0))
g=[t for t,d in v["GPS"] if d['I']==0]
print("GPS I0 son mesaj", max(g), "toplam", len(g))
gg=[t for t in g if 188<=t<=202.42]; print("GPS maks bosluk 188-202.41", round(max(b-a for a,b in zip(gg,gg[1:])),3))
print("GPS 202.41 sonrasi mesaj sayisi", len([t for t in g if t>202.42]))
print("GPS instance'lar", set(d['I'] for t,d in v["GPS"]))
# BARO ham 202.3-203.2
for t,d in v["BARO"]:
    if 202.25<=t<=203.3 and d['I']==0: print(f"  BARO0 {t:.3f} Alt {d['Alt']:.2f} CRt {d['CRt']:.2f} H {d['Health']}")
