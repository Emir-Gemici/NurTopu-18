import pickle, math
v = pickle.load(open("tum.pkl","rb"))
def sec(tip, a, b, **flt):
    return [(t,d) for t,d in v[tip] if a<=t<=b and all(d.get(k)==x for k,x in flt.items())]
# 1) jiroskop istatistik 192.4-202.3 IMU0 ve IMU1
for I in (0,1):
    L = sec("IMU", 192.4, 202.30, I=I)
    for ax in ("GyrX","GyrY","GyrZ"):
        xs = [math.degrees(d[ax]) for _,d in L]
        m = sum(xs)/len(xs); s = math.sqrt(sum((x-m)**2 for x in xs)/len(xs))
        print(f"IMU{I} {ax} n={len(xs)} ort {m:.1f} std {s:.1f} min {min(xs):.1f} max {max(xs):.1f}")
    for ax in ("AccX","AccY","AccZ"):
        xs = [d[ax] for _,d in L]
        m = sum(xs)/len(xs); s = math.sqrt(sum((x-m)**2 for x in xs)/len(xs))
        print(f"IMU{I} {ax} ort {m:.2f} std {s:.2f} min {min(xs):.2f} max {max(xs):.2f}")
    xs = [math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2) for _,d in L]
    print(f"IMU{I} |a| min {min(xs):.2f} max {max(xs):.2f}")
    xs = [math.hypot(d['AccX'],d['AccY']) for _,d in L]
    print(f"IMU{I} axy max {max(xs):.2f}")
# 2) gz'nin -12 den kucuk oldugu anlar tum son ucusta (188.3-202.3)
L = sec("IMU", 188.3, 202.40, I=0)
print("IMU0 |gz|>=12 anlari 188.3-202.4:", [(round(t,2), round(math.degrees(d['GyrZ']),1)) for t,d in L if abs(math.degrees(d['GyrZ']))>=12])
print("IMU0 gy<=-15 anlari 188.3-202.4:", [(round(t,2), round(math.degrees(d['GyrY']),1)) for t,d in L if math.degrees(d['GyrY'])<=-15])
print("IMU0 |gx|>=40 anlari 188.3-202.4:", [(round(t,2), round(math.degrees(d['GyrX']),1)) for t,d in L if abs(math.degrees(d['GyrX']))>=40])
print("IMU0 |a|<7 anlari 188.3-202.4:", [(round(t,2), round(math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2),1)) for t,d in L if math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2)<7])
# 3) RCIN 192.4-202.4
L = sec("RCIN", 192.4, 202.45)
for c in ("C1","C2","C3","C4","C5","C6"):
    xs=[d[c] for _,d in L]; print(f"RCIN {c} min {min(xs)} max {max(xs)}")
L = sec("RCIN", 188.3, 202.45)
for c in ("C1","C2","C3","C4"):
    xs=[d[c] for _,d in L]; print(f"RCIN 188.3- {c} min {min(xs)} max {max(xs)}")
# 4) ATT DesRoll/DesPitch 192.4-202.4
L = sec("ATT", 192.4, 202.40)
for c in ("DesRoll","Roll","DesPitch","Pitch"):
    xs=[d[c] for _,d in L]; print(f"ATT {c} min {min(xs):.1f} max {max(xs):.1f}")
# 5) hiz
L = sec("PSCN", 192.4, 202.40); E = sec("PSCE", 192.4, 202.40)
sp = [(t, math.hypot(dn['VN'], de['VE'])) for (t,dn),(_,de) in zip(L,E)]
print("yatay hiz max", max(sp, key=lambda r:r[1]))
# kalkis noktasi
for tt in (188.3, 192.4, 199.0, 202.37, 202.47, 202.97):
    n = [d for t,d in v["PSCN"] if t<=tt][-1]; e = [d for t,d in v["PSCE"] if t<=tt][-1]
    print("t", tt, "PN", round(n['PN'],2), "PE", round(e['PE'],2), "VN", round(n['VN'],2), "VE", round(e['VE'],2))
