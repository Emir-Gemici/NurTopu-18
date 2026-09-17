import pickle, math
L = pickle.load(open("log.pkl","rb")); d = L["d"]
def st(v):
    v=sorted(v); n=len(v)
    return f"n={n} min={v[0]:.1f} med={v[n//2]:.1f} max={v[-1]:.1f}" if n else "yok"
W=[("L1 75.6-79.9",75.6,79.9),("L2 140.9-147.5",140.9,147.5),("SON 188.4-195",188.4,195),("SON 195-202.37",195,202.37)]
for ad,a,b in W:
    for I in (0,1):
        v=[x for x in d["VIBE"] if a<=x["TimeUS"]/1e6<=b and x["IMU"]==I]
        print(ad,"IMU",I,"VX",st([x["VibeX"] for x in v]),"VY",st([x["VibeY"] for x in v]),"VZ",st([x["VibeZ"] for x in v]),"Clip",v[0]["Clip"] if v else None,"->",v[-1]["Clip"] if v else None)
for I in (0,1):
    prev=None
    for x in d["VIBE"]:
        if x["IMU"]!=I: continue
        if x["Clip"]!=prev: print(" VIBE IMU",I,"Clip degisim t=",round(x["TimeUS"]/1e6,3),"Clip",x["Clip"]); prev=x["Clip"]
# yaw integration check 188.4 -> 202.37
import bisect
at=[x for x in d["ATT"] if 188.4<=x["TimeUS"]/1e6<=202.37]
r=[x for x in d["RATE"] if 188.4<=x["TimeUS"]/1e6<=202.37]
im=[x for x in d["IMU"] if 188.4<=x["TimeUS"]/1e6<=202.37 and x["I"]==0]
s=0
for i in range(len(r)-1): s+=r[i]["Y"]*(r[i+1]["TimeUS"]-r[i]["TimeUS"])/1e6
s2=0
for i in range(len(im)-1): s2+=math.degrees(im[i]["GyrZ"])*(im[i+1]["TimeUS"]-im[i]["TimeUS"])/1e6
dy=(at[-1]["Yaw"]-at[0]["Yaw"]+540)%360-180
print("ATT yaw degisim", round(at[0]["Yaw"],2), "->", round(at[-1]["Yaw"],2), "=", round(dy,2), "| RATE.Y integrali", round(s,2), "| IMU0 GyrZ integrali (govde, 25Hz)", round(s2,2))
