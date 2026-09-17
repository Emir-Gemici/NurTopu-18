import pickle, math
v = pickle.load(open("tum.pkl","rb"))
for I in (0,1):
    L=[(t,d) for t,d in v["VIBE"] if d['IMU']==I]
    prev=None
    for t,d in L:
        if d['Clip']!=prev and t<202.4: print(f"IMU{I} {t:.2f} Clip {d['Clip']}"); prev=d['Clip']
    for a,b,ad in [(181.7,188.2,"yerde arm"),(189.0,202.37,"askida")]:
        z=[d['VibeZ'] for t,d in L if a<=t<=b]; x=[d['VibeX'] for t,d in L if a<=t<=b]; y=[d['VibeY'] for t,d in L if a<=t<=b]
        print(f"IMU{I} {ad} VibeX ort {sum(x)/len(x):.1f} maks {max(x):.1f} | VibeY ort {sum(y)/len(y):.1f} maks {max(y):.1f} | VibeZ ort {sum(z)/len(z):.1f} min {min(z):.1f} maks {max(z):.1f}")
# CTUN ThO vs ThH son 5 s
c=[d for t,d in v["CTUN"] if 197<=t<=202.37]
print("ThO ort", round(sum(d['ThO'] for d in c)/len(c),3), "ThH ort", round(sum(d['ThH'] for d in c)/len(c),3))
# gecmis ucus: 134-150 askida VibeZ
for a,b in [(141,147),(76,79.9),(55,61)]:
    z=[d['VibeZ'] for t,d in v["VIBE"] if a<=t<=b and d['IMU']==0]
    r=[d for t,d in v["RCOU"] if a<=t<=b]
    sp=[max(d['C9'],d['C10'],d['C11'],d['C12'])-min(d['C9'],d['C10'],d['C11'],d['C12']) for d in r]
    print(f"pencere {a}-{b} IMU0 VibeZ ort {sum(z)/len(z):.1f} maks {max(z):.1f} | motor yayilimi ort {sum(sp)/len(sp):.0f} us")
r=[d for t,d in v["RCOU"] if 197<=t<=202.37]
sp=[max(d['C9'],d['C10'],d['C11'],d['C12'])-min(d['C9'],d['C10'],d['C11'],d['C12']) for d in r]
print("197-202.37 motor yayilimi ort", round(sum(sp)/len(sp)), "M4 ort", round(sum(d['C9'] for d in r)/len(r)), "M2", round(sum(d['C10'] for d in r)/len(r)), "M1", round(sum(d['C11'] for d in r)/len(r)), "M3", round(sum(d['C12'] for d in r)/len(r)))
