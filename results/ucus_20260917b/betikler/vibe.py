import pickle, math
v = pickle.load(open("tum.pkl","rb"))
print("VIBE 201.8-203.3")
for t,d in v["VIBE"]:
    if 201.8<=t<=203.3: print(f"  {t:.3f} IMU{d['IMU']} VX {d['VibeX']:.1f} VY {d['VibeY']:.1f} VZ {d['VibeZ']:.1f} Clip {d['Clip']}")
print("BAT 202.0-204.3")
for t,d in v["BAT"]:
    if 202.0<=t<=204.3: print(f"  {t:.3f} V {d['Volt']:.2f} A {d['Curr']:.1f}")
print("MAG 202.2-203.3")
for t,d in v["MAG"]:
    if 202.2<=t<=203.3: print(f"  {t:.3f} I{d['I']} X {d['MagX']} Y {d['MagY']} Z {d['MagZ']} H {d['Health']} S {d['S']}")
