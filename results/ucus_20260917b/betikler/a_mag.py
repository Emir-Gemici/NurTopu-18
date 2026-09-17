import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
mag = d["MAG"]
def f(x): return math.sqrt(x["MagX"]**2+x["MagY"]**2+x["MagZ"]**2)
# overall per-instance stats per arm window
wins = [(49.6,61.5),(66.0,80.2),(113.3,118.2),(120.5,124.3),(134.2,150.7),(181.7,204.0),(204.0,218.7)]
for I in (0,1):
    print("=== MAG I", I)
    for a,b in wins:
        xs=[f(x) for x in mag if x["I"]==I and a<=x["TimeUS"]/1e6<=b]
        if xs: print(f"  {a}-{b}: n={len(xs)} min={min(xs):.0f} max={max(xs):.0f} ort={sum(xs)/len(xs):.0f}")
    # offsets, health
    sub=[x for x in mag if x["I"]==I]
    print("  ofs ilk", {k:sub[0][k] for k in ("OfsX","OfsY","OfsZ","MOX","MOY","MOZ","Health","S")}, "son", {k:sub[-1][k] for k in ("OfsX","OfsY","OfsZ","MOX","MOY","MOZ","Health","S")})
    # health changes
    prev=None
    for x in sub:
        h=x["Health"]
        if h!=prev: print("   Health", h, "t=", x["TimeUS"]/1e6); prev=h
