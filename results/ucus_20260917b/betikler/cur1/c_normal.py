from c_ort import *
import numpy as np
v=yukle()
a,b=193.0,202.37
for I in (0,1):
    L=[d for d in pen(v,"IMU",a,b) if d['I']==I]
    t=np.array([d['t'] for d in L]); gx=np.degrees([d['GyrX'] for d in L]); gy=np.degrees([d['GyrY'] for d in L]); gz=np.degrees([d['GyrZ'] for d in L])
    am=np.array([math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2) for d in L])
    dgx=np.diff(gx); dgy=np.diff(gy)
    print(f"IMU{I} {a}-{b} n {len(L)} GyrX min/max {gx.min():.1f}/{gx.max():.1f} GyrY {gy.min():.1f}/{gy.max():.1f} GyrZ {gz.min():.1f}/{gz.max():.1f} | 40ms dGyrX min/max {dgx.min():.1f}/{dgx.max():.1f} dGyrY {dgy.min():.1f}/{dgy.max():.1f} | |a| min/max {am.min():.2f}/{am.max():.2f}")
    # olay adimi
    L2=[d for d in pen(v,"IMU",202.36,202.50) if d['I']==I]
    g=[(round(d['t'],2),round(math.degrees(d['GyrX']),1),round(math.degrees(d['GyrY']),1),round(math.degrees(d['GyrZ']),1)) for d in L2]
    print("   olay:", g, "dGyrX", [round(g[i+1][1]-g[i][1],1) for i in range(len(g)-1)], "dGyrY", [round(g[i+1][2]-g[i][2],1) for i in range(len(g)-1)], "dGyrZ", [round(g[i+1][3]-g[i][3],1) for i in range(len(g)-1)])
Q=pen(v,"RATE",a,b); ro=np.array([d['ROut'] for d in Q]); po=np.array([d['POut'] for d in Q])
print(f"RATE {a}-{b} ROut min/max {ro.min():.3f}/{ro.max():.3f} (>=0.299 olan: {(ro>=0.299).sum()} / {len(ro)}) POut {po.min():.3f}/{po.max():.3f}")
R=pen(v,"RCOU",a,b); m4=[d['C9'] for d in R]; print("M4 min", min(m4), "M4<=1210 sayisi", sum(1 for x in m4 if x<=1210), "/", len(m4))
# sonraki takla sirasinda GyrX ornekten ornege sicrama (titresim ortusmesi olcusu)
for I in (0,1):
    L=[d for d in pen(v,"IMU",202.53,202.93) if d['I']==I]
    gx=np.degrees([d['GyrX'] for d in L]); gy=np.degrees([d['GyrY'] for d in L])
    print(f"IMU{I} 202.53-202.93 |dGyrX| max {np.abs(np.diff(gx)).max():.1f} |dGyrY| max {np.abs(np.diff(gy)).max():.1f}")
