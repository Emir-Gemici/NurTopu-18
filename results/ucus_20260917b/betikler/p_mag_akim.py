import pickle, math, bisect
import numpy as np
L = pickle.load(open("log.pkl","rb")); d = L["d"]
bat=d["BAT"]; bts=[x["TimeUS"] for x in bat]
def near(t):
    i=bisect.bisect_left(bts,t); c=[j for j in (i-1,i) if 0<=j<len(bat)]
    return bat[min(c,key=lambda j:abs(bts[j]-t))]
X=[];Y=[];Bv=[]
for x in d["MAG"]:
    t=x["TimeUS"]/1e6
    if x["I"]!=1 or not (181.7<=t<=202.37): continue
    b=near(x["TimeUS"]); 
    X.append(b["Curr"]); Y.append(math.sqrt(x["MagX"]**2+x["MagY"]**2+x["MagZ"]**2)); Bv.append((b["Curr"],x["MagX"],x["MagY"],x["MagZ"]))
X=np.array(X);Y=np.array(Y)
A=np.vstack([X,np.ones_like(X)]).T
k,c=np.linalg.lstsq(A,Y,rcond=None)[0]
r=np.corrcoef(X,Y)[0,1]
print(f"MAG1 |B| = {k:.2f}*Curr + {c:.1f}  (181.7-202.37, n={len(X)}, r={r:.3f}, Curr aralik {X.min():.1f}-{X.max():.1f} A)")
V=np.array(Bv)
A3=np.vstack([V[:,0],np.ones(len(V))]).T
for i,ax in enumerate(("X","Y","Z")):
    kk,cc=np.linalg.lstsq(A3,V[:,i+1],rcond=None)[0]; rr=np.corrcoef(V[:,0],V[:,i+1])[0,1]
    print(f"  Mag{ax} = {kk:.2f}*Curr + {cc:.1f} r={rr:.3f}")
# MAG0 external vs current
X0=[];Y0=[]
for x in d["MAG"]:
    t=x["TimeUS"]/1e6
    if x["I"]!=0 or not (181.7<=t<=202.37): continue
    b=near(x["TimeUS"]); X0.append(b["Curr"]); Y0.append(math.sqrt(x["MagX"]**2+x["MagY"]**2+x["MagZ"]**2))
X0=np.array(X0);Y0=np.array(Y0)
k0,c0=np.linalg.lstsq(np.vstack([X0,np.ones_like(X0)]).T,Y0,rcond=None)[0]
print(f"MAG0 |B| = {k0:.2f}*Curr + {c0:.1f} r={np.corrcoef(X0,Y0)[0,1]:.3f}")
# invert for impact window (rough)
for x in d["MAG"]:
    t=x["TimeUS"]/1e6
    if x["I"]==1 and 202.37<=t<=203.3:
        B=math.sqrt(x["MagX"]**2+x["MagY"]**2+x["MagZ"]**2); b=near(x["TimeUS"])
        print(f"  {t:.2f} |B1|={B:.0f} -> kaba akim tahmini {(B-c)/k:.0f} A | BAT Curr {b['Curr']:.1f} | V {b['Volt']:.2f} -> (16.2-V)/0.038 = {(16.2-b['Volt'])/0.038:.0f} A")
