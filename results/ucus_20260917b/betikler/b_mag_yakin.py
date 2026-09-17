import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
a,b = float(sys.argv[1]), float(sys.argv[2])
for x in d["MAG"]:
    t=x["TimeUS"]/1e6
    if a<=t<=b:
        print(f"{t:.3f} MAG I{x['I']} X{x['MagX']} Y{x['MagY']} Z{x['MagZ']} |B|={math.sqrt(x['MagX']**2+x['MagY']**2+x['MagZ']**2):.0f} H{x['Health']} S={x['S']/1e6:.3f}")
