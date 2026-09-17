import pickle, math, sys
L = pickle.load(open("log.pkl","rb")); d = L["d"]
a,b = float(sys.argv[1]), float(sys.argv[2])
g=d["GPS"]
prev=None
for x in g:
    t=x["TimeUS"]/1e6
    if a<=t<=b:
        dt = (t-prev) if prev else 0
        print(f"{t:.3f} dt={dt:.3f} St{x['Status']} GMS{x['GMS']} NS{x['NSats']} HDop{x['HDop']:.2f} Spd{x['Spd']:.2f} VZ{x['VZ']:.2f} Alt{x['Alt']:.2f} U{x['U']}")
    prev=t
