import pickle, math
v = pickle.load(open("tum.pkl","rb"))
print("GPS 201.5-206")
for t,d in v["GPS"]:
    if 201.5<=t<=206: print(f"  {t:.3f} I{d['I']} St {d['Status']} GMS {d['GMS']} NS {d['NSats']} HD {d['HDop']} Spd {d['Spd']:.2f} Alt {d['Alt']:.2f} U {d['U']}")
print("GPA 201.9-203.5")
for t,d in v["GPA"]:
    if 201.9<=t<=203.5: print(f"  {t:.3f}", {k:(round(x,3) if isinstance(x,float) else x) for k,x in d.items() if k!='TimeUS'})
print("MAG I0 son ornek S degeri ve sonraki ilk degisim:")
L=[(t,d) for t,d in v["MAG"] if d['I']==0 and 202.0<=t<=219]
prev=None
for t,d in L:
    if d['S']!=prev: print(f"  {t:.3f} S {d['S']} H {d['Health']} X {d['MagX']}"); prev=d['S']
print("MSG/ERR/EV 202-219:")
for k in ("MSG","ERR","EV","ARM","MODE"):
    for t,d in v[k]:
        if 202<=t<=219: print(f"  {t:.3f} {k} {d}")
print("POWR 202.2-203.4")
for t,d in v["POWR"]:
    if 202.2<=t<=203.4: print(f"  {t:.3f}", {k:(round(x,3) if isinstance(x,float) else x) for k,x in d.items() if k!='TimeUS'})
