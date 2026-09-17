import pickle
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def m(v): return sum(v)/len(v) if v else float('nan')
print("bin | YOut | yawerr | ROut | ThrOut | P=V*I W | V | I | M1 M2 M3 M4 PWM | RCIN C1 C2 C3 C4 | VibeZ0")
t=188.4
while t<202.4:
    a,b=t,min(t+1.0,202.37)
    R=[x for x in d["RATE"] if a<=x["TimeUS"]/1e6<b]; A=[x for x in d["ATT"] if a<=x["TimeUS"]/1e6<b]
    M=[x for x in d["MOTB"] if a<=x["TimeUS"]/1e6<b]; B=[x for x in d["BAT"] if a<=x["TimeUS"]/1e6<b]
    O=[x for x in d["RCOU"] if a<=x["TimeUS"]/1e6<b]; C=[x for x in d["RCIN"] if a<=x["TimeUS"]/1e6<b]
    V=[x for x in d["VIBE"] if a<=x["TimeUS"]/1e6<b and x["IMU"]==0]
    ye=[((x["DesYaw"]-x["Yaw"]+540)%360-180) for x in A]
    print(f"{a:6.1f}-{b:6.2f} | {m([x['YOut'] for x in R]):.3f} | {m(ye):5.1f} | {m([x['ROut'] for x in R]):.3f} | {m([x['ThrOut'] for x in M]):.3f} | {m([x['Volt']*x['Curr'] for x in B]):5.0f} | {m([x['Volt'] for x in B]):.2f} | {m([x['Curr'] for x in B]):4.1f} | {m([x['C11'] for x in O]):.0f} {m([x['C10'] for x in O]):.0f} {m([x['C12'] for x in O]):.0f} {m([x['C9'] for x in O]):.0f} | {m([x['C1'] for x in C]):.0f} {m([x['C2'] for x in C]):.0f} {m([x['C3'] for x in C]):.0f} {m([x['C4'] for x in C]):.0f} | {m([x['VibeZ'] for x in V]):.1f}")
    t+=1.0
